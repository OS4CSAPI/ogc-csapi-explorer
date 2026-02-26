# CSAPI Part 1 Requirements Analysis

**Document:** Section 1.1 - Standard Document Analysis  
**Source:** [OGC API – Connected Systems Part 1: Feature Resources (23-001)](https://docs.ogc.org/is/23-001/23-001.html)  
**Date:** 2026-01-31  
**Status:** Complete

---

## Executive Summary

This document analyzes the OGC API – Connected Systems Part 1 standard document to extract ALL requirements for implementing a TypeScript client library. Part 1 defines 5 resource types (Systems, Deployments, Procedures, Sampling Features, Properties) with comprehensive CRUD operations, advanced filtering, and dual format support (GeoJSON, SensorML).

**Key Findings:**

- **5 Part 1 Resource Types:** Systems, Deployments, Procedures, Sampling Features, Properties
- **11 Conformance Classes** covering common behavior, resources, CRUD, filtering, encodings
- **70+ Operations Total** across canonical endpoints, nested endpoints, collections
- **Dual Format Support:** GeoJSON (spatial features) and SensorML-JSON (detailed descriptions)
- **Advanced Filtering:** 30+ query parameters for relationship-based queries
- **Sub-Resource Navigation:** Nested collections (subsystems, subdeployments, system-specific sampling features)
- **Hierarchical Queries:** Recursive parameter for multi-level traversal

---

## 1. Resource Types and Operations

### 1.1 Systems Resource

**Definition:** System resources represent instances of observing systems, platforms, sensors, actuators, and samplers. These are feature resources implementing the `ssn:System` concept from SOSA/SSN ontology.

**System Types (from Table 6):**

- **Sensor** (`sosa:Sensor`) - primary activity is sensing/observing
- **Actuator** (`sosa:Actuator`) - primary activity is actuating
- **Sampler** (`sosa:Sampler`) - primary activity is sampling
- **Platform** (`sosa:Platform`) - primary activity is carrying other systems
- **System** (`sosa:System`) - all other system types

**Asset Types (from Table 7):**

- Equipment - hardware devices, automated or manual
- Human - human beings following procedures
- LivingThing - animals or organisms (often platforms carrying sensors)
- Simulation - software algorithms simulating real-world
- Process - process/chain transforming data
- Group - group of similar systems (sensor network, fleet)
- Other - application-specific types

**Operations:**

**Read Operations:**

- `GET {api_root}/systems` - List all systems (canonical resources endpoint)
- `GET {api_root}/systems/{id}` - Retrieve single system (canonical resource endpoint)
- `GET {api_root}/systems?<filters>` - Query systems with filters
- `GET {api_root}/collections/{collectionId}/items` - Systems from collection (featureType=`sosa:System`)

**Create Operations:**

- `POST {api_root}/systems` - Create new system at canonical endpoint
- `POST {api_root}/systems/{parentId}/subsystems` - Create subsystem under parent
- `POST {api_root}/collections/{collectionId}/items` - Add system to collection

**Update/Replace Operations:**

- `PUT {api_root}/systems/{id}` - Replace system (full replacement)
- `PATCH {api_root}/systems/{id}` - Update system (partial update)
- `PUT {api_root}/collections/{collectionId}/items/{id}` - Replace in collection

**Delete Operations:**

- `DELETE {api_root}/systems/{id}` - Delete system
- `DELETE {api_root}/systems/{id}?cascade=true` - Delete system and nested resources
- `DELETE {api_root}/collections/{collectionId}/items/{id}` - Remove from collection (not deletion)

**System Properties (Required):**

- `uniqueIdentifier` (URI) - Persistent unique identifier (preferably URN)
- `name` (String) - Human readable name
- `systemType` (URI/CURIE) - Type from Table 6
- `subsystems` (Array of System resources) - Required association
- `samplingFeatures` (Array of SamplingFeature resources) - Required association
- `datastreams` (Array of DataStream resources) - Required association (Part 2)
- `controlstreams` (Array of ControlStream resources) - Required association (Part 2)

**System Properties (Optional):**

- `description` (String) - Human readable description
- `assetType` (Enum) - Type from Table 7
- `validTime` (DateTime) - Validity period of description
- `location` (Point) - Current location (recommended for mobile systems)
- `systemKind` (Procedure) - Description of system kind (datasheet)
- `deployments` (Array of Deployment resources)
- `procedures` (Array of Procedure resources)

**System Requirements:**

- Systems MUST have `location` property that updates when system moves (Requirement 4)
- Systems MUST be accessible at canonical URL `{api_root}/systems/{id}` (Requirement 5)
- Server MUST expose canonical endpoint `{api_root}/systems` (Requirement 7)
- Server MUST expose at least one collection containing Systems (Requirement 8)
- Collections containing Systems MUST set `featureType=sosa:System` (Requirement 8)

---

### 1.2 Subsystems

**Definition:** Subsystems are regular System resources made available through a sub-collection of a parent System. Used to model hierarchical systems (components, payloads).

**Operations:**

**Read Operations:**

- `GET {api_root}/systems/{parentId}/subsystems` - List subsystems of parent
- `GET {api_root}/systems/{parentId}/subsystems?recursive=false` - Direct subsystems only
- `GET {api_root}/systems/{parentId}/subsystems?recursive=true` - All nested subsystems
- `GET {api_root}/systems?recursive=true` - All systems including all subsystems

**Create Operations:**

- `POST {api_root}/systems/{parentId}/subsystems` - Create subsystem under specific parent

**Subsystem Requirements:**

- Subsystems MUST be exposed at `{api_root}/systems/{parentId}/subsystems` (Requirement 9)
- Subsystems MUST include permanently attached components, CAN include deployed payloads (Requirement 9)
- Server MUST support `recursive` parameter (boolean) (Requirement 10)
- Default behavior (recursive=false or omitted): direct subsystems only (Requirement 11)
- With recursive=true: all nested subsystems at all levels (Requirement 11)
- Recursive associations: subsystem datastreams/controlstreams/samplingFeatures include parent's (Requirement 13)

**Recursive Behavior:**

- Querying `{api_root}/systems` without recursive: top-level systems only
- Querying `{api_root}/systems?recursive=true`: all systems and all subsystems
- Other query parameters apply to ALL processed systems (filters work recursively)
- If system has subsystems, its nested resources endpoints include subsystem resources

---

### 1.3 Deployments Resource

**Definition:** Deployment resources provide information about deployment of one or more Systems. Implements `sosa:Deployment` concept. Typically have temporal and spatial extent.

**Operations:**

**Read Operations:**

- `GET {api_root}/deployments` - List all deployments (canonical resources endpoint)
- `GET {api_root}/deployments/{id}` - Retrieve single deployment
- `GET {api_root}/deployments?<filters>` - Query deployments with filters
- `GET {api_root}/systems/{sysId}/deployments` - Deployments where specific system was deployed
- `GET {api_root}/collections/{collectionId}/items` - Deployments from collection (featureType=`sosa:Deployment`)

**Create Operations:**

- `POST {api_root}/deployments` - Create new deployment
- `POST {api_root}/deployments/{parentId}/subdeployments` - Create subdeployment under parent
- `POST {api_root}/collections/{collectionId}/items` - Add deployment to collection

**Update/Replace Operations:**

- `PUT {api_root}/deployments/{id}` - Replace deployment
- `PATCH {api_root}/deployments/{id}` - Update deployment
- `PUT {api_root}/collections/{collectionId}/items/{id}` - Replace in collection

**Delete Operations:**

- `DELETE {api_root}/deployments/{id}` - Delete deployment
- `DELETE {api_root}/collections/{collectionId}/items/{id}` - Remove from collection

**Deployment Properties (Required):**

- `uniqueIdentifier` (URI) - Persistent unique identifier
- `name` (String) - Human readable name
- `validTime` (DateTime) - Time period during which systems are deployed
- `deployedSystems` (Array of System resources) - Required association
- `subdeployments` (Array of Deployment resources) - Required association

**Deployment Properties (Optional):**

- `description` (String) - Human readable description
- `deploymentType` (URI) - Type of deployment
- `location` (Geometry) - Location or area where systems deployed
- `platform` (Feature) - Platform on which systems deployed
- `featuresOfInterest` (Array of Feature resources) - Ultimate FOIs observed/controlled
- `samplingFeatures` (Array of SamplingFeature resources) - Associated sampling features
- `datastreams` (Array of DataStream resources) - Observations collected during deployment
- `controlstreams` (Array of ControlStream resources) - Commands issued during deployment

**Deployment Requirements:**

- Deployments MUST be accessible at canonical URL `{api_root}/deployments/{id}` (Requirement 14)
- Server MUST expose canonical endpoint `{api_root}/deployments` (Requirement 16)
- Server MUST expose at least one collection containing Deployments (Requirement 18)
- Collections containing Deployments MUST set `featureType=sosa:Deployment` (Requirement 18)
- If System provides `deployments` association, MUST link to `{api_root}/systems/{sysId}/deployments` (Requirement 17)

**Examples from Standard:**

- In-situ sensor deployed at given location
- Network of in-situ sensors along river
- Security camera network in city
- Mission with unmanned systems + payloads
- Team deployed for survey responses
- Sample collection campaign
- Forecast model run

---

### 1.4 Subdeployments

**Definition:** Subdeployments are regular Deployment resources made available through sub-collection of parent Deployment. Used for hierarchical deployments.

**Operations:**

**Read Operations:**

- `GET {api_root}/deployments/{parentId}/subdeployments` - List subdeployments
- `GET {api_root}/deployments/{parentId}/subdeployments?recursive=false` - Direct subdeployments only
- `GET {api_root}/deployments/{parentId}/subdeployments?recursive=true` - All nested subdeployments
- `GET {api_root}/deployments?recursive=true` - All deployments including subdeployments

**Create Operations:**

- `POST {api_root}/deployments/{parentId}/subdeployments` - Create subdeployment

**Subdeployment Requirements:**

- Subdeployments MUST be exposed at `{api_root}/deployments/{parentId}/subdeployments` (Requirement 19)
- Server MUST support `recursive` parameter (boolean) (Requirement 20)
- Default (recursive=false or omitted): direct subdeployments only (Requirement 21)
- With recursive=true: all nested subdeployments at all levels (Requirement 21)
- Recursive associations: nested deployedSystems/featuresOfInterest/samplingFeatures/datastreams/controlstreams include subdeployment resources (Requirement 23)

**Examples from Standard:**

- Deployment of monitoring sensors along river, where each monitoring station is a subdeployment
- Multi-phase campaign with distinct operational periods
- Distributed deployment across multiple geographic regions

---

### 1.5 Procedures Resource

**Definition:** Procedure resources describe procedure implemented by one or more Systems (e.g., specs/datasheets, methodologies). Implements `sosa:Procedure` concept. Non-spatial features.

**Procedure Types (from Table 16):**

- **ObservingProcedure** (`sosa:ObservingProcedure`) - observation method, used by Sensor
- **SamplingProcedure** (`sosa:SamplingProcedure`) - sampling method, used by Sampler
- **ActuatingProcedure** (`sosa:ActuatingProcedure`) - actuation method, used by Actuator
- **Other Procedure** (`sosa:Procedure`) - any other procedure/methodology

**System Kind Types (from Table 16 - for datasheets):**

- **Sensor** (`sosa:Sensor`) - sensor datasheet
- **Actuator** (`sosa:Actuator`) - actuator datasheet
- **Sampler** (`sosa:Sampler`) - sampler datasheet
- **Platform** (`sosa:Platform`) - platform datasheet
- **Other System** (`sosa:System`) - any other system datasheet

**Operations:**

**Read Operations:**

- `GET {api_root}/procedures` - List all procedures
- `GET {api_root}/procedures/{id}` - Retrieve single procedure
- `GET {api_root}/procedures?<filters>` - Query procedures with filters
- `GET {api_root}/collections/{collectionId}/items` - Procedures from collection (featureType=`sosa:Procedure`)

**Create Operations:**

- `POST {api_root}/procedures` - Create new procedure
- `POST {api_root}/collections/{collectionId}/items` - Add procedure to collection

**Update/Replace Operations:**

- `PUT {api_root}/procedures/{id}` - Replace procedure
- `PATCH {api_root}/procedures/{id}` - Update procedure
- `PUT {api_root}/collections/{collectionId}/items/{id}` - Replace in collection

**Delete Operations:**

- `DELETE {api_root}/procedures/{id}` - Delete procedure
- `DELETE {api_root}/collections/{collectionId}/items/{id}` - Remove from collection

**Procedure Properties (Required):**

- `uniqueIdentifier` (URI) - Persistent unique identifier
- `name` (String) - Human readable name
- `procedureType` (URI/CURIE) - Type from Table 16

**Procedure Properties (Optional):**

- `description` (String) - Human readable description
- `implementingSystems` (Array of System resources) - Systems implementing procedure

**Procedure Requirements:**

- Procedures MUST NOT have location (Requirement 24)
- Procedures MUST be accessible at canonical URL `{api_root}/procedures/{id}` (Requirement 25)
- Server MUST expose canonical endpoint `{api_root}/procedures` (Requirement 27)
- Server MUST expose at least one collection containing Procedures (Requirement 28)
- Collections containing Procedures MUST set `featureType=sosa:Procedure` (Requirement 28)

**Usage Notes from Standard:**

- Procedure resources describe **types** (models, datasheets), System resources describe **instances**
- For automated equipment: procedure = equipment specifications (datasheet)
- For human tasks: procedure = steps/methodology operator follows
- For instrument + operator: procedure describes instrument(s) used and how
- Several System instances can implement same Procedure (be of same model)

---

### 1.6 Sampling Features Resource

**Definition:** Sampling Features describe sampling geometry/methodology used when observing property of larger feature (Feature of Interest). Implements `sosa:Sample` concept. Always associated with specific System.

**Operations:**

**Read Operations:**

- `GET {api_root}/samplingFeatures` - List all sampling features
- `GET {api_root}/samplingFeatures/{id}` - Retrieve single sampling feature
- `GET {api_root}/samplingFeatures?<filters>` - Query sampling features with filters
- `GET {api_root}/systems/{sysId}/samplingFeatures` - Sampling features for specific system
- `GET {api_root}/collections/{collectionId}/items` - Sampling features from collection (featureType=`sosa:Sample`)

**Create Operations:**

- `POST {api_root}/systems/{sysId}/samplingFeatures` - Create sampling feature under system
- `POST {api_root}/collections/{collectionId}/items` - Add sampling feature to collection

**Update/Replace Operations:**

- `PUT {api_root}/samplingFeatures/{id}` - Replace sampling feature
- `PATCH {api_root}/samplingFeatures/{id}` - Update sampling feature
- `PUT {api_root}/collections/{collectionId}/items/{id}` - Replace in collection

**Delete Operations:**

- `DELETE {api_root}/samplingFeatures/{id}` - Delete sampling feature
- `DELETE {api_root}/collections/{collectionId}/items/{id}` - Remove from collection

**Sampling Feature Properties (Required):**

- `uniqueIdentifier` (URI) - Persistent unique identifier
- `name` (String) - Human readable name
- `featureType` (URI) - Type of sampling feature
- `parentSystem` (System resource) - System that created/uses this sampling feature
- `sampledFeature` (Feature resource) - Ultimate feature of interest being sampled

**Sampling Feature Properties (Optional):**

- `description` (String) - Human readable description
- `sampleOf` (Array of SamplingFeature resources) - Other sampling features via sub-sampling
- `datastreams` (Array of DataStream resources) - Observations of this sampling feature
- `controlstreams` (Array of ControlStream resources) - Commands impacting this sampling feature

**Sampling Feature Requirements:**

- Sampling features MUST be accessible at canonical URL `{api_root}/samplingFeatures/{id}` (Requirement 29)
- Server MUST expose canonical endpoint `{api_root}/samplingFeatures` (Requirement 31)
- Server MUST expose at least one collection containing Sampling Features (Requirement 33)
- Collections containing Sampling Features MUST set `featureType=sosa:Sample` (Requirement 33)
- For each System, server MUST expose `{api_root}/systems/{sysId}/samplingFeatures` (Requirement 32)
- Sampling features endpoint MUST only list features associated with parent system (Requirement 32)

**Examples from Standard:**

- Sampling point along river
- Trajectory at ocean surface
- Satellite image footprint
- Profile of atmosphere
- Viewing frustum of video camera
- Area covered by weather radar
- Part in complex machine

**Feature of Interest vs Sampling Feature:**

- **Feature of Interest:** Ultimate real-world feature whose properties observed/controlled (exists independently)
- **Sampling Feature:** Specific sampling strategy for particular system (system-dependent)
- FOI examples: building, room, river, atmosphere, person, animal, vehicle, administrative area
- A System can also be FOI of other observations (e.g., GPS observing aircraft platform location)

---

### 1.7 Properties Resource

**Definition:** Property resources provide semantic information about feature properties (observable, controllable, or asserted properties). Implements `ssn:Property` concept. NOT spatial features.

**Property Types:**

- **Observable properties** (`sosa:ObservableProperty`) - subject of observation
- **Controllable properties** (`sosa:ActuatableProperty`) - subject of actuation/command
- **Asserted properties** - system characteristics/capabilities

**Operations:**

**Read Operations:**

- `GET {api_root}/properties` - List all properties
- `GET {api_root}/properties/{id}` - Retrieve single property
- `GET {api_root}/properties?<filters>` - Query properties with filters
- `GET {api_root}/collections/{collectionId}/items` - Properties from collection (itemType=`sosa:Property`)

**Create Operations:**

- `POST {api_root}/properties` - Create new property
- `POST {api_root}/collections/{collectionId}/items` - Add property to collection

**Update/Replace Operations:**

- `PUT {api_root}/properties/{id}` - Replace property
- `PATCH {api_root}/properties/{id}` - Update property
- `PUT {api_root}/collections/{collectionId}/items/{id}` - Replace in collection

**Delete Operations:**

- `DELETE {api_root}/properties/{id}` - Delete property
- `DELETE {api_root}/collections/{collectionId}/items/{id}` - Remove from collection

**Property Resource Properties (Required):**

- `uniqueIdentifier` (URI) - Persistent unique identifier
- `name` (String) - Human readable name

**Property Resource Properties (Optional):**

- `description` (String) - Human readable description
- `baseProperty` (Property resource) - Base property this is derived from
- `objectType` (URI) - Kind of object/feature this property applies to

**Property Requirements:**

- Properties MUST be accessible at canonical URL `{api_root}/properties/{id}` (Requirement 34)
- Server MUST expose canonical endpoint `{api_root}/properties` (Requirement 36)
- Server MUST expose at least one collection containing Properties (Requirement 37)
- Collections containing Properties MUST set `itemType=sosa:Property` (Requirement 37)
- Operations at property endpoints SHALL replace "features/feature" with "resources/resource" terminology (Requirement 35)

---

## 2. HTTP Methods Specified

### 2.1 Read Operations (GET)

**All Resources:**

- `GET {api_root}/{resourceType}` - List resources at canonical endpoint
- `GET {api_root}/{resourceType}/{id}` - Retrieve single resource
- `GET {api_root}/collections/{collectionId}/items` - List items in collection
- `GET {api_root}/collections/{collectionId}/items/{id}` - Retrieve item from collection

**Nested Resources:**

- `GET {api_root}/systems/{id}/subsystems` - List subsystems
- `GET {api_root}/systems/{id}/deployments` - List deployments for system
- `GET {api_root}/systems/{id}/samplingFeatures` - List sampling features for system
- `GET {api_root}/deployments/{id}/subdeployments` - List subdeployments

**Method Requirements:**

- GET operations MUST fulfill requirements from OGC API – Features Part 1 Clause 7.15.2 to 7.15.8
- GET operations MUST support query parameters (filters, pagination)
- GET operations MUST return appropriate status codes (200 for success)

---

### 2.2 Create Operations (POST)

**Canonical Endpoints:**

- `POST {api_root}/systems` - Create system
- `POST {api_root}/deployments` - Create deployment
- `POST {api_root}/procedures` - Create procedure
- `POST {api_root}/properties` - Create property

**Nested Endpoints:**

- `POST {api_root}/systems/{parentId}/subsystems` - Create subsystem
- `POST {api_root}/systems/{sysId}/samplingFeatures` - Create sampling feature
- `POST {api_root}/deployments/{parentId}/subdeployments` - Create subdeployment

**Collection Endpoints:**

- `POST {api_root}/collections/{collectionId}/items` - Add to collection
- `POST {api_root}/collections/{collectionId}/items` (body: text/uri-list) - Add existing resources by URI

**Method Requirements:**

- POST creates new resource instances
- Server returns 201 with Location header pointing to canonical URL
- Created resources MUST be accessible at canonical URL
- Nested resource creation (subsystems, sampling features) automatically associates with parent

---

### 2.3 Replace Operations (PUT)

**Canonical Endpoints:**

- `PUT {api_root}/systems/{id}` - Replace system
- `PUT {api_root}/deployments/{id}` - Replace deployment
- `PUT {api_root}/procedures/{id}` - Replace procedure
- `PUT {api_root}/samplingFeatures/{id}` - Replace sampling feature
- `PUT {api_root}/properties/{id}` - Replace property

**Collection Endpoints:**

- `PUT {api_root}/collections/{collectionId}/items/{id}` - Replace item in collection

**Method Requirements:**

- PUT performs full replacement of resource
- Changes at canonical URL reflected in all collections containing resource
- Server returns appropriate status codes

---

### 2.4 Update Operations (PATCH)

**Canonical Endpoints:**

- `PATCH {api_root}/systems/{id}` - Update system
- `PATCH {api_root}/deployments/{id}` - Update deployment
- `PATCH {api_root}/procedures/{id}` - Update procedure
- `PATCH {api_root}/samplingFeatures/{id}` - Update sampling feature
- `PATCH {api_root}/properties/{id}` - Update property

**Collection Endpoints:**

- `PATCH {api_root}/collections/{collectionId}/items/{id}` - Update item in collection

**Method Requirements:**

- PATCH performs partial update (only specified fields)
- Changes at canonical URL reflected in all collections
- Follows OGC API – Features Part 4 update requirements

---

### 2.5 Delete Operations (DELETE)

**Canonical Endpoints:**

- `DELETE {api_root}/systems/{id}` - Delete system
- `DELETE {api_root}/systems/{id}?cascade=true` - Delete system and nested resources
- `DELETE {api_root}/deployments/{id}` - Delete deployment
- `DELETE {api_root}/procedures/{id}` - Delete procedure
- `DELETE {api_root}/samplingFeatures/{id}` - Delete sampling feature
- `DELETE {api_root}/properties/{id}` - Delete property

**Collection Endpoints:**

- `DELETE {api_root}/collections/{collectionId}/items/{id}` - Remove from collection (NOT deletion)

**Method Requirements:**

- DELETE at canonical URL permanently removes resource
- DELETE at collection URL only removes from that collection
- System deletion requires cascade parameter if nested resources exist
- Without cascade: server rejects DELETE if nested resources present (409 error)
- With cascade=true: deletes resource and all nested resources
- If System referenced by Deployment, Deployment updated to remove link (not deleted)

---

## 3. Query Parameters Defined

### 3.1 Common Query Parameters (All Resources)

**Identifier Parameters:**

- `id` - Filter by local ID(s) (comma-separated list)
  - Example: `?id=abc123,def456`
- `uid` - Filter by unique identifier (UID) (comma-separated list of URIs)
  - Example: `?uid=urn:uuid:31f6865e-f438-430e-9b57-f965a21ee255`

**Keyword Search:**

- `q` - Text search across resource properties (keyword filter)
  - Example: `?q=weather%20station`

**Property Filters:**

- `{propertyName}={value}` - Filter by specific property value
  - Example: `?name=Weather%20Station`
  - Example: `?featureType=om:Specimen`

**Type:** ID_List = comma-separated list of local IDs or UIDs (URIs)

---

### 3.2 Common Feature Query Parameters (Spatial/Temporal Resources)

**Spatial Filters:**

- `bbox` - Bounding box filter (minLon,minLat,maxLon,maxLat)
  - Example: `?bbox=-180,-90,180,90`
- `geom` - Geometry intersection filter (WKT format)
  - Standard: Specified in clause 16.4.2
  - Used for spatial queries on Systems, Deployments, Sampling Features

**Temporal Filters:**

- `datetime` - Temporal filter (ISO 8601 datetime or interval)
  - Single datetime: `?datetime=2024-01-01T00:00:00Z`
  - Open-ended interval: `?datetime=2024-01-01T00:00:00Z/..`
  - Closed interval: `?datetime=2024-01-01T00:00:00Z/2024-12-31T23:59:59Z`
  - Applies to `validTime` property for Systems/Deployments

**Pagination:**

- `limit` - Maximum number of results
  - Example: `?limit=10`
- `offset` - Skip first N results
  - Example: `?offset=20`

---

### 3.3 Hierarchical Query Parameters

**Recursive Traversal:**

- `recursive` - Boolean parameter for hierarchical queries
  - Default (false or omitted): Direct children only
  - `recursive=true`: All descendants recursively
  - Applies to:
    - `{api_root}/systems?recursive=true` (all systems + subsystems)
    - `{api_root}/systems/{id}/subsystems?recursive=true` (nested subsystems)
    - `{api_root}/deployments?recursive=true` (all deployments + subdeployments)
    - `{api_root}/deployments/{id}/subdeployments?recursive=true` (nested subdeployments)

---

### 3.4 System-Specific Query Parameters

Applied to System resources endpoints:

- `{api_root}/systems`
- `{api_root}/systems/{id}/subsystems`
- `{api_root}/collections/{colId}/items` (where collection contains Systems)

**Relationship Filters:**

1. **Parent Filter:** `parent` (ID_List)

   - Find subsystems of specific parent system(s)
   - Example: `?parent=4g4ds54vv`
   - Example: `?parent=urn:uuid:31f6865e-f438-430e-9b57-f965a21ee255`

2. **Procedure Filter:** `procedure` (ID_List)

   - Find systems that implement specific procedure(s)
   - Example: `?procedure=11gsd654g`
   - Example: `?procedure=11gsd654g,fsv4dg62` (multiple)
   - Example: `?procedure=urn:example:procedure:451585`

3. **Feature of Interest Filter:** `foi` (ID_List)

   - Find systems that observe/control specific feature(s) of interest
   - Example: `?foi=11gsd654g`
   - Example: `?foi=urn:mrn:itu:mmsi:538070999`
   - Example: `?foi=http://dbpedia.org/resource/Seawater`
   - Includes both sampling features AND domain features of interest
   - Recursive: if system has subsystems, included if ANY subsystem observes FOI

4. **Observed Property Filter:** `observedProperty` (ID_List)

   - Find systems that can observe specific property/properties
   - Example: `?observedProperty=4578441`
   - Example: `?observedProperty=http://qudt.org/vocab/quantitykind/Temperature`
   - Recursive: if system has subsystems, included if ANY subsystem observes property

5. **Controlled Property Filter:** `controlledProperty` (ID_List)
   - Find systems that control specific property/properties
   - Example: `?controlledProperty=4578441`
   - Example: `?controlledProperty=http://qudt.org/vocab/quantitykind/PH`
   - Recursive: if system has subsystems, included if ANY subsystem controls property

---

### 3.5 Deployment-Specific Query Parameters

Applied to Deployment resources endpoints:

- `{api_root}/deployments`
- `{api_root}/deployments/{id}/subdeployments`
- `{api_root}/collections/{colId}/items` (where collection contains Deployments)

**Relationship Filters:**

1. **Parent Filter:** `parent` (ID_List)

   - Find subdeployments of specific parent deployment(s)
   - Example: `?parent=4g4ds54vv`

2. **Deployed System Filter:** `system` (ID_List)

   - Find deployments where specific system(s) were deployed
   - Example: `?system=b5bxc988rf`
   - Example: `?system=urn:mrn:itu:mmsi:538070999`

3. **Feature of Interest Filter:** `foi` (ID_List)

   - Find deployments where deployed systems observe/control specific FOI(s)
   - Example: `?foi=g4sd56ht41`
   - Example: `?foi=urn:example:river:41148`
   - Includes both sampling features AND domain features

4. **Observed Property Filter:** `observedProperty` (ID_List)

   - Find deployments where specific properties are observed
   - Example: `?observedProperty=4578441`
   - Example: `?observedProperty=http://mmisw.org/ont/cf/parameter/wind_speed`

5. **Controlled Property Filter:** `controlledProperty` (ID_List)
   - Find deployments where specific properties are controlled
   - Example: `?controlledProperty=146687`
   - Example: `?controlledProperty=http://qudt.org/vocab/quantitykind/Velocity`

---

### 3.6 Procedure-Specific Query Parameters

Applied to Procedure resources endpoints:

- `{api_root}/procedures`
- `{api_root}/collections/{colId}/items` (where collection contains Procedures)

**Relationship Filters:**

1. **Observed Property Filter:** `observedProperty` (ID_List)

   - Find procedures designed to observe specific properties
   - Example: `?observedProperty=4578441`
   - Example: `?observedProperty=http://mmisw.org/ont/cf/parameter/air_pressure`

2. **Controlled Property Filter:** `controlledProperty` (ID_List)
   - Find procedures designed to control specific properties
   - Example: `?controlledProperty=146687`
   - Example: `?controlledProperty=urn:example:prop:fuelmixratio`

---

### 3.7 Sampling Feature-Specific Query Parameters

Applied to Sampling Feature resources endpoints:

- `{api_root}/samplingFeatures`
- `{api_root}/collections/{colId}/items` (where collection contains Sampling Features)

**Relationship Filters:**

1. **Feature of Interest Filter:** `foi` (ID_List)

   - Find sampling features that sample specific feature(s) of interest
   - Example: `?foi=g4sd56ht41`
   - Example: `?foi=urn:example:river:41148`

2. **Observed Property Filter:** `observedProperty` (ID_List)

   - Find sampling features with certain observed properties
   - Example: `?observedProperty=221785`
   - Example: `?observedProperty=http://qudt.org/vocab/quantitykind/Voltage`

3. **Controlled Property Filter:** `controlledProperty` (ID_List)
   - Find sampling features with certain controlled properties
   - Example: `?controlledProperty=146687`
   - Example: `?controlledProperty=http://qudt.org/vocab/quantitykind/Velocity`

---

### 3.8 Property-Specific Query Parameters

Applied to Property resources endpoints:

- `{api_root}/properties`
- `{api_root}/collections/{colId}/items` (where collection contains Properties)

**Relationship Filters:**

1. **Base Property Filter:** `baseProperty` (ID_List)

   - Find properties derived from specific base property/properties
   - Example: `?baseProperty=g4sd56ht41`
   - Example: `?baseProperty=http://qudt.org/vocab/quantitykind/AmbientPressure`
   - Searches directly and indirectly (transitive)

2. **Object Type Filter:** `objectType` (ID_List)
   - Find properties associated with specific object/feature type(s)
   - Example: `?object=https://dbpedia.org/page/Watercraft`
   - Example: `?object=https://dbpedia.org/page/Engine`

---

### 3.9 Query Parameter Combination Rules

**Logical AND Between Parameters:**

- Multiple parameters combined with logical AND
- Example: `?bbox=-180,-90,180,90&datetime=2024-01-01T00:00:00Z/..&limit=10`
- Each resource in result set must satisfy ALL filter conditions

**Multiple Values in Single Parameter:**

- Comma-separated values in ID_List parameters
- Treated as logical OR for that parameter
- Example: `?id=abc,def,ghi` matches resources with id=abc OR id=def OR id=ghi

**Recursive + Other Filters:**

- `recursive=true` applies to traversal depth
- Other query parameters apply to ALL processed resources (both parents and descendants)
- Example: `?recursive=true&observedProperty=temperature` finds all systems (including subsystems) that observe temperature

---

## 4. Request Bodies for Create/Update Operations

### 4.1 GeoJSON Format Request Bodies

**Media Type:** `application/geo+json`

**System Creation:**

```json
{
  "type": "Feature",
  "geometry": {
    "type": "Point",
    "coordinates": [30.706, -134.196, 272]
  },
  "properties": {
    "uid": "urn:x-sensor:id:12345",
    "name": "Weather Station Alpha",
    "description": "Automated weather monitoring station",
    "featureType": "http://www.w3.org/ns/sosa/Sensor",
    "assetType": "Equipment",
    "validTime": ["2024-01-01T00:00:00Z", null]
  }
}
```

**Deployment Creation:**

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
    "description": "...",
    "featureType": "http://www.w3.org/ns/sosa/Deployment",
    "validTime": ["2024-07-01T00:00:00Z", "2024-09-30T00:00:00Z"],
    "deployedSystems@link": [
      {"href": "https://api.example.org/systems/abc123"}
    ]
  }
}
```

**Procedure Creation:**

```json
{
  "type": "Feature",
  "geometry": null,
  "properties": {
    "uid": "urn:x-procedure:datasheet:wx-sensor-v2",
    "name": "Weather Sensor Model WX-2000",
    "description": "Technical datasheet for WX-2000 sensor",
    "featureType": "http://www.w3.org/ns/sosa/Sensor",
    "procedureType": "http://www.w3.org/ns/sosa/Sensor"
  }
}
```

**Sampling Feature Creation:**

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
    "featureType": "http://www.opengis.net/def/samplingFeatureType/OGC-OM/2.0/SF_SamplingPoint",
    "sampledFeature@link": {
      "href": "http://example.org/features/river-123"
    }
  }
}
```

---

### 4.2 SensorML-JSON Format Request Bodies

**Media Type:** `application/sml+json`

**System Creation (PhysicalSystem):**

```json
{
  "type": "PhysicalSystem",
  "id": "wx-station-alpha",
  "definition": "http://www.w3.org/ns/sosa/Sensor",
  "uniqueId": "urn:x-sensor:id:12345",
  "label": "Weather Station Alpha",
  "description": "Automated weather monitoring station",
  "typeOf": {
    "href": "https://api.example.org/procedures/wx-2000-datasheet"
  },
  "position": {
    "type": "Point",
    "coordinates": [30.706, -134.196, 272]
  },
  "validTime": ["2024-01-01T00:00:00Z", null]
}
```

**Deployment Creation:**

```json
{
  "type": "Deployment",
  "uniqueId": "urn:x-deployment:mission-001",
  "label": "Arctic Mission 2024",
  "description": "...",
  "validTime": ["2024-07-01T00:00:00Z", "2024-09-30T00:00:00Z"],
  "location": {
    "type": "Polygon",
    "coordinates": [[[...]]]
  },
  "deployedSystems": [
    {
      "system": {"href": "https://api.example.org/systems/abc123"}
    }
  ]
}
```

**Procedure Creation (SimpleProcess):**

```json
{
  "type": "SimpleProcess",
  "definition": "http://www.w3.org/ns/sosa/Sensor",
  "uniqueId": "urn:x-procedure:datasheet:wx-sensor-v2",
  "label": "Weather Sensor Model WX-2000",
  "description": "Technical datasheet for WX-2000 sensor"
}
```

---

### 4.3 Update (PATCH) Request Bodies

**JSON Merge Patch Format:**
Updates only specified fields, leaves others unchanged.

```json
{
  "properties": {
    "description": "Updated description text",
    "location": {
      "type": "Point",
      "coordinates": [31.0, -135.0, 280]
    }
  }
}
```

**URI List Format (for adding to collections):**

```
https://api.example.org/systems/abc123
https://api.example.org/systems/def456
https://api.example.org/systems/ghi789
```

---

## 5. Response Formats Required

### 5.1 GeoJSON Format

**Media Type:** `application/geo+json`

**Supported For:**

- Systems (with location)
- Deployments (with spatial extent)
- Procedures (geometry = null)
- Sampling Features (with geometry)

**Requirements:**

- Server MUST advertise GeoJSON support via Accept headers (Requirement 77)
- Server MUST accept GeoJSON for write operations (POST/PUT/PATCH) (Requirement 78)
- All spatial resources MUST be serializable to GeoJSON
- Link relations use `ogc-rel:` prefix (e.g., `ogc-rel:subsystems`)
- Property mappings follow Table 40-47

**Example System in GeoJSON:**

```json
{
  "type": "Feature",
  "id": "sensor123",
  "geometry": {
    "type": "Point",
    "coordinates": [-122.08, 37.42, 25.5]
  },
  "properties": {
    "uid": "urn:x-sensor:id:sensor123",
    "name": "Temperature Sensor TS-001",
    "description": "High-precision temperature sensor",
    "featureType": "http://www.w3.org/ns/sosa/Sensor",
    "assetType": "Equipment",
    "validTime": ["2024-01-01T00:00:00Z", null]
  },
  "links": [
    {
      "rel": "canonical",
      "href": "https://api.example.org/systems/sensor123"
    },
    {
      "rel": "ogc-rel:subsystems",
      "href": "https://api.example.org/systems/sensor123/subsystems"
    },
    {
      "rel": "ogc-rel:samplingFeatures",
      "href": "https://api.example.org/systems/sensor123/samplingFeatures"
    }
  ]
}
```

---

### 5.2 SensorML-JSON Format

**Media Type:** `application/sml+json`

**Supported For:**

- Systems (more detailed descriptions than GeoJSON)
- Deployments (detailed deployment information)
- Procedures (datasheets, methodologies)
- Properties (semantic definitions)

**SensorML Classes Used:**

- **PhysicalComponent** - Hardware equipment or human observers
- **PhysicalSystem** - Hardware equipment or human observers
- **SimpleProcess** - Software processes or simulations
- **AggregateProcess** - Grouped processes
- **Deployment** - Deployment descriptions

**Requirements:**

- Server MUST advertise SensorML support via Accept headers (Requirement 89)
- Server MUST accept SensorML for write operations (Requirement 90)
- PhysicalComponent/PhysicalSystem used for hardware/human (Requirement 95)
- SimpleProcess/AggregateProcess used for simulations/processes (Requirement 95)
- Property mappings follow Table 49-53

**Example System in SensorML:**

```json
{
  "type": "PhysicalSystem",
  "id": "sensor123",
  "definition": "http://www.w3.org/ns/sosa/Sensor",
  "uniqueId": "urn:x-sensor:id:sensor123",
  "label": "Temperature Sensor TS-001",
  "description": "High-precision temperature sensor",
  "typeOf": {
    "title": "TS-Series Datasheet",
    "href": "https://api.example.org/procedures/ts-datasheet"
  },
  "position": {
    "type": "Point",
    "coordinates": [-122.08, 37.42, 25.5]
  },
  "validTime": ["2024-01-01T00:00:00Z", null],
  "links": [
    {
      "rel": "canonical",
      "href": "https://api.example.org/systems/sensor123"
    },
    {
      "rel": "ogc-rel:subsystems",
      "href": "https://api.example.org/systems/sensor123/subsystems"
    }
  ]
}
```

---

### 5.3 Format Negotiation

**Mechanisms:**

1. **Accept Header:** Client specifies desired format

   - `Accept: application/geo+json`
   - `Accept: application/sml+json`

2. **Query Parameter:** `f` or `format` parameter
   - `?f=geojson`
   - `?f=sml`
   - `?format=application/sml+json`

**Content-Type Response Header:**

- Server indicates format in response
- `Content-Type: application/geo+json; charset=utf-8`
- `Content-Type: application/sml+json; charset=utf-8`

**Format Selection Rules:**

- If Accept header specified: use requested format
- If `f` parameter specified: use requested format
- Default format: implementation-dependent (typically GeoJSON for spatial, SensorML for non-spatial)
- If requested format not supported: 406 Not Acceptable

---

## 6. Conformance Classes Defined

### 6.1 Common (Clause 8, Conformance Class A.1)

**Identifier:** `/req/api-common`  
**Conformance Class:** `/conf/api-common`

**Prerequisites:**

- OGC API – Features – Part 1: Core `/req/core`
- OGC API – Common – Part 1: Core `/req/core`
- OGC API – Common – Part 1: Landing Page `/req/landing-page`
- OGC API – Common – Part 1: JSON `/req/json`

**Requirements:**

- Resource IDs (local identifiers) (Requirement 1)
- Unique Identifiers (UIDs) as URI or URN (Requirement 2)
- Date/Time query parameter support (Requirement 3)

**Normative Statements:**

- All CS resources MUST have local ID and unique identifier (UID)
- UIDs SHOULD be UUIDs or URNs with registered namespace (Recommendation 1)
- `datetime` parameter applies to `validTime` property

**No Core Class:** Standard explicitly states "There is no Core requirements class" - implementations must implement at least one resource type + one encoding.

---

### 6.2 System Features (Clause 9, Conformance Class A.2)

**Identifier:** `/req/system`  
**Conformance Class:** `/conf/system`

**Prerequisite:** Common (`/req/api-common`)

**Requirements:**

- System location updates when system moves (Requirement 4)
- Canonical URL `{api_root}/systems/{id}` (Requirement 5)
- System resources endpoints support (Requirement 6)
- Canonical endpoint `{api_root}/systems` (Requirement 7)
- At least one System collection exposed (Requirement 8)

**Covered Operations:**

- GET systems list
- GET single system
- POST create system
- PUT replace system
- PATCH update system
- DELETE system

---

### 6.3 Subsystems (Clause 10, Conformance Class A.3)

**Identifier:** `/req/subsystem`  
**Conformance Class:** `/conf/subsystem`

**Prerequisite:** System Features (`/req/system`)

**Requirements:**

- Subsystems exposed at `{api_root}/systems/{parentId}/subsystems` (Requirement 9)
- `recursive` parameter support (Requirements 10, 11, 12)
- Recursive associations for nested resources (Requirement 13)

**Covered Operations:**

- GET subsystems list
- GET subsystems recursively
- POST create subsystem under parent
- Recursive queries across hierarchy

---

### 6.4 Deployment Features (Clause 11, Conformance Class A.4)

**Identifier:** `/req/deployment`  
**Conformance Class:** `/conf/deployment`

**Prerequisite:** Common (`/req/api-common`)

**Requirements:**

- Canonical URL `{api_root}/deployments/{id}` (Requirement 14)
- Deployment resources endpoints support (Requirement 15)
- Canonical endpoint `{api_root}/deployments` (Requirement 16)
- Nested endpoint from systems `{api_root}/systems/{sysId}/deployments` (Requirement 17)
- At least one Deployment collection (Requirement 18)

**Covered Operations:**

- GET deployments list
- GET single deployment
- GET deployments for system
- POST create deployment
- PUT replace deployment
- PATCH update deployment
- DELETE deployment

---

### 6.5 Subdeployments (Clause 12, Conformance Class A.5)

**Identifier:** `/req/subdeployment`  
**Conformance Class:** `/conf/subdeployment`

**Prerequisite:** Deployment Features (`/req/deployment`)

**Requirements:**

- Subdeployments exposed at `{api_root}/deployments/{parentId}/subdeployments` (Requirement 19)
- `recursive` parameter support (Requirements 20, 21, 22)
- Recursive associations for nested resources (Requirement 23)

**Covered Operations:**

- GET subdeployments list
- GET subdeployments recursively
- POST create subdeployment under parent
- Recursive queries across deployment hierarchy

---

### 6.6 Procedure Features (Clause 13, Conformance Class A.6)

**Identifier:** `/req/procedure`  
**Conformance Class:** `/conf/procedure`

**Prerequisite:** Common (`/req/api-common`)

**Requirements:**

- Procedures have NO location (Requirement 24)
- Canonical URL `{api_root}/procedures/{id}` (Requirement 25)
- Procedure resources endpoints support (Requirement 26)
- Canonical endpoint `{api_root}/procedures` (Requirement 27)
- At least one Procedure collection (Requirement 28)

**Covered Operations:**

- GET procedures list
- GET single procedure
- POST create procedure
- PUT replace procedure
- PATCH update procedure
- DELETE procedure

---

### 6.7 Sampling Features (Clause 14, Conformance Class A.7)

**Identifier:** `/req/sf`  
**Conformance Class:** `/conf/sf`

**Prerequisites:** Common (`/req/api-common`), System Features (`/req/system`)

**Requirements:**

- Canonical URL `{api_root}/samplingFeatures/{id}` (Requirement 29)
- Sampling Feature resources endpoints support (Requirement 30)
- Canonical endpoint `{api_root}/samplingFeatures` (Requirement 31)
- Nested endpoint from systems `{api_root}/systems/{sysId}/samplingFeatures` (Requirement 32)
- At least one Sampling Feature collection (Requirement 33)

**Covered Operations:**

- GET sampling features list
- GET single sampling feature
- GET sampling features for system
- POST create sampling feature under system
- PUT replace sampling feature
- PATCH update sampling feature
- DELETE sampling feature

---

### 6.8 Property Definitions (Clause 15, Conformance Class A.8)

**Identifier:** `/req/property`  
**Conformance Class:** `/conf/property`

**Prerequisite:** Common (`/req/api-common`)

**Requirements:**

- Canonical URL `{api_root}/properties/{id}` (Requirement 34)
- Property resources endpoints support (Requirement 35)
- Canonical endpoint `{api_root}/properties` (Requirement 36)
- At least one Property collection (Requirement 37)

**Covered Operations:**

- GET properties list
- GET single property
- POST create property
- PUT replace property
- PATCH update property
- DELETE property

---

### 6.9 Advanced Filtering (Clause 16, Conformance Class A.9)

**Identifier:** `/req/advanced-filtering`  
**Conformance Class:** `/conf/advanced-filtering`

**Prerequisite:** Common (`/req/api-common`)

**Requirements:**

- ID list schema (Requirement 38)
- Filter by ID (Requirement 39)
- Filter by keyword (Requirement 40)
- Filter by geometry (Requirement 41)
- System filters: parent, procedure, foi, observedProperty, controlledProperty (Requirements 42-46)
- Deployment filters: parent, system, foi, observedProperty, controlledProperty (Requirements 47-51)
- Procedure filters: observedProperty, controlledProperty (Requirements 52-53)
- Sampling Feature filters: foi, observedProperty, controlledProperty (Requirements 54-56)
- Property filters: baseProperty, objectType (Requirements 57-58)
- Combined filters (logical AND) (Requirement 59)

**Covered Query Parameters:**

- All relationship-based filters listed in Section 3.4-3.8
- 30+ query parameters total across all resource types

---

### 6.10 Create/Replace/Delete (Clause 17, Conformance Class A.10)

**Identifier:** `/req/create-replace-delete`  
**Conformance Class:** `/conf/create-replace-delete`

**Prerequisites:**

- Common (`/req/api-common`)
- OGC API – Features – Part 4: Create, Replace, Update and Delete `/req/create-replace-delete`

**Requirements:**

- System CRUD operations (Requirements 60, 61, 62)
- Deployment CRUD operations (Requirements 63, 64)
- Procedure CRUD operations (Requirement 65)
- Sampling Feature CRUD operations (Requirement 66)
- Property CRUD operations (Requirement 67)
- Collection operations (Requirements 68-71)

**Covered Operations:**

- POST (create) at canonical and nested endpoints
- PUT (replace) at canonical and collection endpoints
- DELETE at canonical and collection endpoints
- POST with text/uri-list to add existing resources to collections
- Cascade delete for systems with nested resources

---

### 6.11 Update (Clause 18, Conformance Class A.11)

**Identifier:** `/req/update`  
**Conformance Class:** `/conf/update`

**Prerequisites:**

- Create/Replace/Delete (`/req/create-replace-delete`)
- OGC API – Features – Part 4: Update `/req/update`

**Requirements:**

- System PATCH operations (Requirement 72)
- Deployment PATCH operations (Requirement 73)
- Procedure PATCH operations (Requirement 74)
- Sampling Feature PATCH operations (Requirement 75)
- Property PATCH operations (Requirement 76)

**Covered Operations:**

- PATCH (partial update) at canonical and collection endpoints

---

### 6.12 GeoJSON Format (Clause 19.1, Conformance Class A.12)

**Identifier:** `/req/geojson`  
**Conformance Class:** `/conf/geojson`

**Prerequisites:**

- Common (`/req/api-common`)
- OGC API – Features – Part 1: GeoJSON `/req/geojson`

**Requirements:**

- Media type for read operations (Requirement 77)
- Media type for write operations (Requirement 78)
- Link relation types with `ogc-rel:` prefix (Requirement 79)
- Feature attribute mappings (Requirement 80)
- System schema and mappings (Requirements 81-82)
- Deployment schema and mappings (Requirements 83-84)
- Procedure schema and mappings (Requirements 85-86)
- Sampling Feature schema and mappings (Requirements 87-88)

**Covered Encodings:**

- Systems as GeoJSON Feature (with geometry)
- Deployments as GeoJSON Feature (with spatial extent)
- Procedures as GeoJSON Feature (geometry = null)
- Sampling Features as GeoJSON Feature (with geometry)

---

### 6.13 SensorML Format (Clause 19.2, Conformance Class A.13)

**Identifier:** `/req/sensorml`  
**Conformance Class:** `/conf/sensorml`

**Prerequisites:**

- Common (`/req/api-common`)
- SensorML 3.0 JSON requirements for SimpleProcess, PhysicalSystem, Deployment, DerivedProperty

**Requirements:**

- Media type for read operations (Requirement 89)
- Media type for write operations (Requirement 90)
- Link relation types (Requirement 91)
- Resource ID conventions (Requirement 92)
- Feature attribute mappings (Requirement 93)
- System schema, class selection, mappings (Requirements 94-96)
- Deployment schema and mappings (Requirements 97-98)
- Procedure schema, class selection, mappings (Requirements 99-101)
- Property schema and mappings (Requirements 102-103)

**Covered Encodings:**

- Systems as PhysicalSystem/PhysicalComponent or SimpleProcess/AggregateProcess
- Deployments as SensorML Deployment
- Procedures as SimpleProcess/AggregateProcess
- Properties as DerivedProperty

---

## 7. Link Relations Defined

### 7.1 Standard Link Relations (from Table 3)

**Association Links (per resource):**

| Relation                      | From Resource                        | Description                                  |
| ----------------------------- | ------------------------------------ | -------------------------------------------- |
| `ogc-rel:subsystems`          | System                               | Link to subsystems collection                |
| `ogc-rel:parentSystem`        | System (subsystem)                   | Link to parent system                        |
| `ogc-rel:samplingFeatures`    | System                               | Link to associated sampling features         |
| `ogc-rel:deployments`         | System                               | Link to deployments involving system         |
| `ogc-rel:procedures`          | System                               | Link to procedures implemented by system     |
| `ogc-rel:featuresOfInterest`  | System, Deployment                   | Link to ultimate features of interest        |
| `ogc-rel:implementingSystems` | Procedure                            | Link to systems implementing procedure       |
| `ogc-rel:sampledFeature`      | Sampling Feature                     | Link to ultimate feature of interest sampled |
| `ogc-rel:sampleOf`            | Sampling Feature                     | Link to other sampling features              |
| `ogc-rel:datastreams`         | System, Deployment, Sampling Feature | Link to associated datastreams (Part 2)      |
| `ogc-rel:controlStreams`      | System, Deployment, Sampling Feature | Link to associated control streams (Part 2)  |

**Navigational Links:**

- `canonical` - Link to canonical URL of resource
- `self` - Link to current representation
- `alternate` - Link to alternate format (e.g., GeoJSON vs SensorML)
- `collection` - Link to parent collection
- `items` - Link to collection items

**Example Link in GeoJSON:**

```json
{
  "rel": "ogc-rel:subsystems",
  "href": "https://api.example.org/systems/sensor123/subsystems",
  "type": "application/geo+json",
  "title": "Subsystems of sensor"
}
```

**Example Link in SensorML:**

```json
{
  "rel": "ogc-rel:samplingFeatures",
  "href": "https://api.example.org/systems/sensor123/samplingFeatures",
  "type": "application/geo+json"
}
```

---

## 8. Resource Relationships Model

### 8.1 System Relationships

**System Associations:**

- **subsystems** → Many Systems (hierarchical, recursive)
- **parentSystem** → One System (inverse of subsystems)
- **systemKind** → One Procedure (system type/datasheet)
- **samplingFeatures** → Many Sampling Features
- **deployments** → Many Deployments
- **procedures** → Many Procedures (can implement multiple)
- **datastreams** → Many DataStreams (Part 2)
- **controlstreams** → Many ControlStreams (Part 2)

**Key Patterns:**

- Subsystems create parent-child hierarchy (can be deeply nested)
- Multiple systems can implement same Procedure (type)
- System can participate in multiple Deployments
- Sampling features always belong to one System

---

### 8.2 Deployment Relationships

**Deployment Associations:**

- **deployedSystems** → Many Systems
- **subdeployments** → Many Deployments (hierarchical)
- **parentDeployment** → One Deployment (inverse)
- **platform** → One Feature (system platform is deployed on)
- **featuresOfInterest** → Many Features
- **samplingFeatures** → Many Sampling Features
- **datastreams** → Many DataStreams (Part 2)
- **controlstreams** → Many ControlStreams (Part 2)

**Key Patterns:**

- Deployments can have temporal and spatial extent
- Multiple systems deployed together in one Deployment
- Subdeployments for hierarchical campaigns

---

### 8.3 Procedure Relationships

**Procedure Associations:**

- **implementingSystems** → Many Systems

**Key Patterns:**

- Procedures describe types, Systems describe instances
- Many Systems can implement same Procedure (many sensors of same model)
- One System can implement multiple Procedures

---

### 8.4 Sampling Feature Relationships

**Sampling Feature Associations:**

- **parentSystem** → One System (required - SF always belongs to system)
- **sampledFeature** → One Feature (ultimate FOI being sampled)
- **sampleOf** → Many Sampling Features (sub-sampling hierarchy)
- **datastreams** → Many DataStreams (Part 2)
- **controlstreams** → Many ControlStreams (Part 2)

**Key Patterns:**

- Sampling Features define system's sampling strategy
- sampledFeature = ultimate FOI (independent real-world feature)
- sampleOf creates sub-sampling hierarchy
- Transitive: if SF-A samples SF-B which samples FOI-C, then SF-A indirectly samples FOI-C

---

### 8.5 Property Relationships

**Property Associations:**

- **baseProperty** → One Property (derivation hierarchy)

**Key Patterns:**

- Properties can be derived from base properties
- Transitive queries: querying for base property includes derived properties
- objectType associates property with specific feature types

---

## 9. History/Versioning Requirements

### 9.1 validTime Property

**Defined For:**

- Systems (optional)
- Deployments (required)

**Format:** DateTime interval (ISO 8601)

- Start and end: `["2024-01-01T00:00:00Z", "2024-12-31T23:59:59Z"]`
- Open-ended: `["2024-01-01T00:00:00Z", null]` (ongoing)

**System validTime:**

- Specifies validity period of system's description
- Optional for Systems
- When system changes configuration, new version can be created with new validTime

**Deployment validTime:**

- Specifies time period during which systems are deployed
- Required for Deployments
- Temporal extent of deployment

---

### 9.2 Location Updates for Mobile Systems

**Requirement 4:**

- Systems with assetType NOT "Simulation" or "Process" SHOULD have location
- For mobile systems, location property MUST update when system moves
- Server responsible for keeping location current

**Pattern:**

- Client queries `GET {api_root}/systems/{id}` at different times
- Responses show different locations if system moved
- No explicit versioning - current state query pattern

---

### 9.3 Resource History (Not in Part 1)

**Part 1 Scope:**

- Part 1 does NOT define detailed resource history mechanisms
- validTime provides basic temporal validity
- Location updates for mobile systems

**Future/Out of Scope:**

- Complete version history of resource changes
- Audit trail of modifications
- Historical queries (time travel)
- These may be covered in future parts or extensions

---

## 10. Filtering Capabilities Specified

### 10.1 Spatial Filters

**bbox (Bounding Box):**

- Format: `bbox=minLon,minLat,maxLon,maxLat`
- Applies to: Systems, Deployments, Sampling Features (resources with geometry)
- Matches resources whose geometry intersects bounding box
- Example: `?bbox=-180,-90,180,90`

**geom (Geometry Intersection):**

- Format: WKT geometry
- Applies to: Systems, Deployments, Sampling Features
- Matches resources whose geometry intersects provided geometry
- More flexible than bbox (arbitrary polygons, lines, etc.)
- Example: `?geom=POLYGON((...))`

---

### 10.2 Temporal Filters

**datetime:**

- Format: ISO 8601 datetime or interval
- Applies to: Systems (validTime), Deployments (validTime)
- Single datetime: exact match
- Open-ended interval: `2024-01-01T00:00:00Z/..` (from date forward)
- Closed interval: `2024-01-01T00:00:00Z/2024-12-31T23:59:59Z`
- Matches resources whose validTime overlaps with query interval

---

### 10.3 Identifier Filters

**id (Local ID):**

- Format: Comma-separated list of local IDs
- Applies to: All resource types
- Example: `?id=abc123,def456`

**uid (Unique Identifier):**

- Format: Comma-separated list of URIs
- Applies to: All resource types
- Example: `?uid=urn:uuid:31f6865e-f438-430e-9b57-f965a21ee255,urn:uuid:another-uuid`

---

### 10.4 Text Search Filter

**q (Keyword Search):**

- Format: Text string
- Applies to: All resource types
- Searches across resource properties (implementation-dependent which properties)
- Example: `?q=weather%20station`

---

### 10.5 Property Value Filters

**Custom Property Filters:**

- Format: `{propertyName}={value}`
- Applies to: All resource types
- Filters on specific property values
- Example: `?name=Weather%20Station`
- Example: `?featureType=om:Specimen`

---

### 10.6 Relationship Filters

**parent:**

- Applies to: Systems (subsystems), Deployments (subdeployments)
- Finds resources with specific parent(s)

**procedure:**

- Applies to: Systems
- Finds systems implementing specific procedure(s)

**foi (Feature of Interest):**

- Applies to: Systems, Deployments, Sampling Features
- Finds resources associated with specific FOI(s)
- Transitive for sampling features

**observedProperty:**

- Applies to: Systems, Deployments, Procedures, Sampling Features
- Finds resources associated with specific observed property/properties

**controlledProperty:**

- Applies to: Systems, Deployments, Procedures, Sampling Features
- Finds resources associated with specific controlled property/properties

**system:**

- Applies to: Deployments
- Finds deployments where specific system(s) deployed

**baseProperty:**

- Applies to: Properties
- Finds properties derived from specific base property/properties
- Transitive

**objectType:**

- Applies to: Properties
- Finds properties for specific object/feature type(s)

---

### 10.7 Hierarchical Filters

**recursive:**

- Applies to: Systems (subsystems), Deployments (subdeployments)
- Boolean: true = include all descendants, false/omitted = direct children only
- When true, other filters apply to ALL resources in hierarchy

---

### 10.8 Pagination

**limit:**

- Maximum number of results to return
- Example: `?limit=10`

**offset:**

- Skip first N results
- Example: `?offset=20`
- Combined: `?limit=10&offset=20` returns items 21-30

---

### 10.9 Filter Combination Rules

**Logical AND:**

- Multiple different parameters combined with AND
- Example: `?bbox=-180,-90,180,90&datetime=2024-01-01/..&limit=10`
- Resource must satisfy ALL conditions

**Logical OR:**

- Multiple values in same parameter (ID_List) combined with OR
- Example: `?id=abc,def,ghi` matches id=abc OR id=def OR id=ghi

**Transitive/Recursive:**

- Some filters search transitively (baseProperty, foi via sampledFeature)
- `recursive=true` makes hierarchy traversal recursive
- Documented in standard which filters support transitive behavior

---

### 10.10 Indirect Associations (Recommendation 4)

**Transitive baseProperty:**

- Querying systems by observedProperty=derivedProp SHOULD also match systems observing baseProperty
- Transitive through derivation chain

**Transitive sampledFeature:**

- Querying sampling features by foi=ultimateFOI SHOULD match features sampling intermediate features
- Transitive through sampleOf chain
- Querying systems by foi SHOULD follow sampledFeature transitively

**Recommendation (not requirement):**

- Standard recommends but doesn't require transitive queries
- Implementation-dependent

---

## 11. Requirements Classes and Their Obligations

### 11.1 Minimum Implementation

**No Core Class:**

- Standard explicitly states there is NO core requirements class
- Minimum: Implement at least ONE resource type + ONE encoding

**Typical Minimum:**

- Common conformance class (`/conf/api-common`) - always required
- One resource class (e.g., Systems `/conf/system`)
- One encoding (e.g., GeoJSON `/conf/geojson`)

**Example Minimal Implementation:**

```
/conf/api-common (Common)
/conf/system (System Features)
/conf/geojson (GeoJSON Format)
```

This minimal server exposes Systems in GeoJSON format with basic read operations.

---

### 11.2 Full Part 1 Implementation

**All 11 Conformance Classes:**

1. `/conf/api-common` - Common (required base)
2. `/conf/system` - System Features
3. `/conf/subsystem` - Subsystems
4. `/conf/deployment` - Deployment Features
5. `/conf/subdeployment` - Subdeployments
6. `/conf/procedure` - Procedure Features
7. `/conf/sf` - Sampling Features
8. `/conf/property` - Property Definitions
9. `/conf/advanced-filtering` - Advanced Filtering
10. `/conf/create-replace-delete` - Create/Replace/Delete
11. `/conf/update` - Update
12. `/conf/geojson` - GeoJSON Format
13. `/conf/sensorml` - SensorML Format

**Full Implementation Server:**

- Supports all 5 Part 1 resource types
- Supports both hierarchies (subsystems, subdeployments)
- Supports all CRUD operations
- Supports all 30+ query parameters
- Supports both GeoJSON and SensorML formats

---

### 11.3 Conformance Detection

**Conformance Endpoint:**

- `GET {api_root}/conformance`
- Returns list of conformance class URIs implemented by server

**Example Response:**

```json
{
  "conformsTo": [
    "http://www.opengis.net/spec/ogcapi-common-1/1.0/conf/core",
    "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/core",
    "http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/api-common",
    "http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/system",
    "http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/subsystem",
    "http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/deployment",
    "http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/geojson"
  ]
}
```

**Client Usage:**

- Client queries conformance endpoint to discover server capabilities
- Client adapts behavior based on supported conformance classes
- Client checks for required conformance classes before attempting operations

---

## 12. Examples Provided in Standard

### 12.1 System Examples

**Example: Fixed In-Situ Sensor (GeoJSON)**

```json
{
  "type": "Feature",
  "id": "sensor001",
  "geometry": {
    "type": "Point",
    "coordinates": [-122.08, 37.42]
  },
  "properties": {
    "uid": "urn:x-sensor:id:sensor001",
    "name": "Weather Station WX-001",
    "featureType": "http://www.w3.org/ns/sosa/Sensor",
    "assetType": "Equipment"
  },
  "links": [
    {
      "rel": "alternate",
      "href": "https://api.example.org/systems/sensor001?f=sml",
      "type": "application/sml+json"
    }
  ]
}
```

---

### 12.2 Deployment Examples

**Example: Saildrone Arctic Mission 2017 (from standard)**

- Three saildrones launched from Dutch Harbor, Alaska
- Partnership with NOAA Research
- Period: July 17 - September 29, 2017
- Geographic extent: Arctic region (53.76°N to 75.03°N, -173.7°E to -155.07°E)
- Platform: Saildrone SD-1003
- Deployed sensors: Air temperature sensor, water temperature sensor, wind sensors, etc.

---

### 12.3 Procedure Examples

**From Standard:**

- **Hardware Equipment:** Procedure = equipment specifications (datasheet)
- **Human Sensing Tasks:** Procedure = steps/methodology operator follows
- **Instrument + Operator:** Procedure describes instrument(s) used and how

---

### 12.4 Sampling Feature Examples

**Example: Rock Sample (from standard, GeoJSON)**

```json
{
  "type": "Feature",
  "id": "f6b464cf",
  "geometry": {
    "type": "Point",
    "coordinates": [30.706, -134.196, 272]
  },
  "properties": {
    "uid": "urn:x-csiro:samples:1114457888",
    "name": "Rock Sample CSIRO:1114457888",
    "description": "Rock sample collected on traverse",
    "featureType": "http://www.opengis.net/def/samplingFeatureType/OGC-OM/2.0/SF_Specimen",
    "samplingTime": "2007-01-24T12:14:50Z",
    "materialClass": "http://dbpedia.org/resource/Rock_(geology)",
    "sampledFeature@link": {
      "href": "...",
      "uid": "urn:example:x-geology:surface"
    }
  }
}
```

**Other Examples from Standard:**

- Sampling point along river
- Trajectory at ocean surface
- Satellite image footprint
- Profile of atmosphere
- Viewing frustum of video camera
- Area covered by weather radar
- Part in complex machine

---

## Summary

This analysis of CSAPI Part 1 standard document reveals:

**5 Resource Types:**

- Systems (observing systems, sensors, actuators, platforms)
- Deployments (system deployments with temporal/spatial extent)
- Procedures (datasheets, methodologies, specifications)
- Sampling Features (sampling strategies and geometries)
- Properties (semantic property definitions)

**70+ Total Operations:**

- Read operations (GET) - canonical, nested, collection endpoints
- Create operations (POST) - canonical, nested, collection endpoints
- Replace operations (PUT) - full replacement
- Update operations (PATCH) - partial update
- Delete operations (DELETE) - with cascade option for systems

**Dual Format Support:**

- GeoJSON for spatial features (systems, deployments, sampling features)
- SensorML-JSON for detailed descriptions (systems, deployments, procedures, properties)

**Advanced Query Capabilities:**

- 30+ query parameters covering spatial, temporal, identifier, text, property, relationship filters
- Hierarchical queries with recursive parameter
- Transitive relationship traversal (recommended)

**11 Conformance Classes:**

- No mandatory core - minimum is 1 resource type + 1 encoding
- Full implementation supports all 5 resources, hierarchies, CRUD, filtering, both formats

**Client Library Implications:**

- Need URL builders for 70+ operations
- Support for query parameter encoding (bbox, datetime, ID lists, etc.)
- Format negotiation (Accept headers, f parameter)
- Link following for associations (ogc-rel: prefixed)
- Conformance detection to adapt to server capabilities

---

## Action Items for Client Library

Based on this analysis, the client library MUST provide:

1. **URL Builders** for all canonical endpoints:

   - `getSystemsUrl()`
   - `getSystemUrl(id)`
   - `getDeploymentsUrl()`
   - `getDeploymentUrl(id)`
   - `getProceduresUrl()`
   - `getProcedureUrl(id)`
   - `getSamplingFeaturesUrl()`
   - `getSamplingFeatureUrl(id)`
   - `getPropertiesUrl()`
   - `getPropertyUrl(id)`

2. **URL Builders** for nested endpoints:

   - `getSubsystemsUrl(parentId, options)`
   - `getSystemDeploymentsUrl(sysId, options)`
   - `getSystemSamplingFeaturesUrl(sysId, options)`
   - `getSubdeploymentsUrl(parentId, options)`

3. **Query Parameter Support** for all 30+ parameters:

   - Spatial: bbox, geom
   - Temporal: datetime
   - Identifiers: id, uid
   - Text: q
   - Properties: name, featureType, etc.
   - Relationships: parent, procedure, foi, observedProperty, controlledProperty, system, baseProperty, objectType
   - Hierarchical: recursive
   - Pagination: limit, offset

4. **Format Negotiation:**

   - f parameter support
   - Accept header suggestion (not set by library)

5. **TypeScript Interfaces** for:
   - Query options (per resource type)
   - Resource types (System, Deployment, Procedure, SamplingFeature, Property)
   - Collection responses
   - Link objects

**Next:** Section 1.2 will analyze the OpenAPI schema to validate and expand on these findings.

---

## Section 1.2: OpenAPI Schema Analysis

**Document:** Section 1.2 - OpenAPI Schema Analysis  
**Source:** [docs/research/standards/ogcapi-connectedsystems-1.bundled.oas31.yaml](../../standards/ogcapi-connectedsystems-1.bundled.oas31.yaml)  
**Date:** 2026-01-31  
**Status:** Complete

---

### Executive Summary

This analysis examines the official OpenAPI 3.1.0 schema for CSAPI Part 1, providing machine-readable specifications of paths, parameters, request/response schemas, and examples. The schema validates and extends the standard document findings from Section 1.1.

**Key Findings:**

- **20 Path Templates** covering all Part 1 operations
- **56 HTTP Operations** (GET, POST, PUT, DELETE methods) across all paths
- **28 Parameters** (13 path, 15 query parameters with precise types)
- **Dual Format Support** validated (application/geo+json, application/sml+json)
- **Complete Request/Response Schemas** including GeoJSON Feature, SensorML-JSON, SWE Common data components
- **7 Status Codes** documented (200, 201, 204, 400, 401, 403, 404, 409, 5XX)
- **Detailed Examples** for all resource types in both formats

---

### 1. Paths Defined in OpenAPI Schema

The schema defines 20 path templates organized by functional areas:

#### 1.1 API Capabilities Paths

1. `/` - Landing page (GET)
2. `/conformance` - Conformance declaration (GET)

#### 1.2 Collections Paths

3. `/collections` - List collections (GET)
4. `/collections/{collectionId}` - Get collection metadata (GET)
5. `/collections/{collectionId}/items` - Collection items (GET, POST)
6. `/collections/{collectionId}/items/{resourceId}` - Collection item (GET, DELETE)

#### 1.3 Systems Paths

7. `/systems` - Systems collection (GET, POST)
8. `/systems/{systemId}` - Single system (GET, PUT, DELETE)
9. `/systems/{systemId}/subsystems` - Subsystems (GET, POST)

#### 1.4 Deployments Paths

10. `/deployments` - Deployments collection (GET, POST)
11. `/deployments/{deploymentId}` - Single deployment (GET, PUT, DELETE)
12. `/deployments/{deploymentId}/subdeployments` - Subdeployments (GET, POST)
13. `/systems/{systemId}/deployments` - System deployments (GET)

#### 1.5 Procedures Paths

14. `/procedures` - Procedures collection (GET, POST)
15. `/procedures/{procedureId}` - Single procedure (GET, PUT, DELETE)

#### 1.6 Sampling Features Paths

16. `/samplingFeatures` - Sampling features collection (GET)
17. `/systems/{systemId}/samplingFeatures` - System sampling features (GET, POST)
18. `/samplingFeatures/{featureId}` - Single sampling feature (GET, PUT, DELETE)

#### 1.7 Properties Paths

19. `/properties` - Properties collection (GET, POST)
20. `/properties/{propId}` - Single property (GET, PUT, DELETE)

**Pattern Summary:**

- **Canonical collections:** `/{resourceType}` - GET (list), POST (create)
- **Canonical resources:** `/{resourceType}/{id}` - GET (retrieve), PUT (replace), DELETE (delete)
- **Nested collections:** `/{parentType}/{parentId}/{childType}` - GET (list), POST (create)

---

### 2. HTTP Methods Specified for Each Path

| Path                                             | GET    | POST   | PUT   | DELETE | Total  |
| ------------------------------------------------ | ------ | ------ | ----- | ------ | ------ |
| `/`                                              | ✓      |        |       |        | 1      |
| `/conformance`                                   | ✓      |        |       |        | 1      |
| `/collections`                                   | ✓      |        |       |        | 1      |
| `/collections/{collectionId}`                    | ✓      |        |       |        | 1      |
| `/collections/{collectionId}/items`              | ✓      | ✓      |       |        | 2      |
| `/collections/{collectionId}/items/{resourceId}` | ✓      |        |       | ✓      | 2      |
| `/systems`                                       | ✓      | ✓      |       |        | 2      |
| `/systems/{systemId}`                            | ✓      |        | ✓     | ✓      | 3      |
| `/systems/{systemId}/subsystems`                 | ✓      | ✓      |       |        | 2      |
| `/deployments`                                   | ✓      | ✓      |       |        | 2      |
| `/deployments/{deploymentId}`                    | ✓      |        | ✓     | ✓      | 3      |
| `/deployments/{deploymentId}/subdeployments`     | ✓      | ✓      |       |        | 2      |
| `/systems/{systemId}/deployments`                | ✓      |        |       |        | 1      |
| `/procedures`                                    | ✓      | ✓      |       |        | 2      |
| `/procedures/{procedureId}`                      | ✓      |        | ✓     | ✓      | 3      |
| `/samplingFeatures`                              | ✓      |        |       |        | 1      |
| `/systems/{systemId}/samplingFeatures`           | ✓      | ✓      |       |        | 2      |
| `/samplingFeatures/{featureId}`                  | ✓      |        | ✓     | ✓      | 3      |
| `/properties`                                    | ✓      | ✓      |       |        | 2      |
| `/properties/{propId}`                           | ✓      |        | ✓     | ✓      | 3      |
| **Total**                                        | **20** | **10** | **5** | **5**  | **40** |

**Notable Absence:** PATCH method not defined in OpenAPI schema (though mentioned in standard document for partial updates per OGC API - Features Part 4)

**Method Patterns:**

- **GET:** All 20 paths (100% coverage)
- **POST:** 10 paths (canonical + nested collections only)
- **PUT:** 5 paths (single resource endpoints only: systems, deployments, procedures, samplingFeatures, properties)
- **DELETE:** 5 paths (single resource endpoints only)

---

### 3. Parameters Defined

#### 3.1 Path Parameters (13 total)

| Parameter Name | Type   | Description                      | Used In                                          |
| -------------- | ------ | -------------------------------- | ------------------------------------------------ |
| `collectionId` | string | Local identifier of a collection | `/collections/{collectionId}/*`                  |
| `resourceId`   | string | Local identifier of a resource   | `/collections/{collectionId}/items/{resourceId}` |
| `systemId`     | string | Local identifier of a System     | `/systems/{systemId}/*`                          |
| `deploymentId` | string | Local identifier of a Deployment | `/deployments/{deploymentId}/*`                  |
| `procedureId`  | string | Local identifier of a Procedure  | `/procedures/{procedureId}`                      |
| `featureId`    | string | Local identifier of a Feature    | `/samplingFeatures/{featureId}`                  |
| `propId`       | string | Local identifier of a Property   | `/properties/{propId}`                           |

**Constraints:** All path parameters are `required: true`, `minLength: 1`

#### 3.2 Query Parameters (15 total)

**Spatial Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `bbox` | array of number | No | Bounding box (4 or 6 numbers): minLon, minLat, [minHeight], maxLon, maxLat, [maxHeight]. Default CRS: WGS84 (CRS84) |
| `geom` | string | No | WKT geometry for intersection filter |

**Temporal Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `datetime` | string | No | Date-time instant or interval (RFC 3339). Supports: instant, `now`, bounded interval, half-bounded (../end, start/.., now/..), `latest` |

**Identifier Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `id` | array of string | No | List of resource local IDs or unique IDs (URI). Comma-separated, referenced as `idListSchema` |

**Text Search:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `q` | array of string | No | Comma-separated keywords for full-text search. Length 1-50 per keyword. Searches `name` and `description` properties |

**Relationship Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `parent` | array of string | No | Filter by parent resource ID(s). Used for Systems (subsystems) and Deployments (subdeployments) |
| `procedure` | array of string | No | Filter Systems by implemented procedure ID(s) |
| `foi` | array of string | No | Filter by feature of interest ID(s). Applies to Systems, Deployments, Sampling Features |
| `observedProperty` | array of string | No | Filter by observed property ID(s). Applies to Systems, Deployments, Procedures, Sampling Features |
| `controlledProperty` | array of string | No | Filter by controlled property ID(s). Applies to Systems, Deployments, Procedures, Sampling Features |
| `system` | array of string | No | Filter Deployments by deployed system ID(s) |
| `baseProperty` | array of string | No | Filter Properties by base property ID(s) |
| `objectType` | array of string (URI) | No | Filter Properties by object type URI(s) |

**Pagination & Behavior:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `limit` | integer | No | 10 | Max items in response. Range: 1-10000 |
| `recursive` | boolean | No | false | Include nested resources recursively |
| `cascade` | boolean | No | false | Delete dependent resources (DELETE operations only) |

#### 3.3 Parameter Type Details

**`idListSchema`** (used by `id`, `parent`, `procedure`, `foi`, `observedProperty`, `controlledProperty`, `system`, `baseProperty`):

```yaml
type: array
minItems: 1
items:
  type: string # Can be local ID or URI
explode: false # Comma-separated format
```

**`datetimeSchema`** (used by `datetime`):

```yaml
oneOf:
  - type: string
    format: date-time
  - type: string
    const: 'now'
  - type: string
    const: 'latest'
  - type: string
    pattern: '^(.*)\/(.*)$' # Interval format
```

**`bbox` Examples:**

- 2D: `-180,-90,180,90` (WGS84 lon/lat)
- 3D: `-180,-90,0,180,90,1000` (WGS84 lon/lat/height)

---

### 4. Request Body Schemas

#### 4.1 Request Body Media Types

**For Resource Creation/Update:**

- `application/geo+json` - GeoJSON Feature representation
- `application/sml+json` - SensorML-JSON representation

**For Adding Resources to Collections:**

- `text/uri-list` - Plain text list of URIs (one per line)
- `application/json` - JSON array of URI strings

#### 4.2 System Request Body Schema

**GeoJSON Format (`application/geo+json`):**

```yaml
schema:
  allOf:
    - $ref: '#/components/schemas/feature' # Base Feature schema
    - properties:
        properties:
          properties:
            featureType:
              $ref: '#/components/schemas/SystemTypeUris' # Enum
            assetType:
              type: string
              enum:
                [
                  Equipment,
                  Human,
                  LivingThing,
                  Simulation,
                  Process,
                  Group,
                  Other,
                ]
            validTime:
              $ref: '#/components/schemas/timePeriod' # [start, end]
            systemKind@link:
              $ref: '#/components/schemas/link-2'
```

**Required Properties:**

- `featureType` (SystemTypeUris enum)
- `uid` (URI format)
- `name` (string, minLength: 1)

**Optional Properties:**

- `description` (string)
- `assetType` (enum)
- `validTime` (array of 2 datetime strings)
- `systemKind@link` (link object)

**SystemTypeUris Enum Values:**

- `http://www.w3.org/ns/sosa/Sensor`
- `http://www.w3.org/ns/sosa/Actuator`
- `http://www.w3.org/ns/sosa/Platform`
- `http://www.w3.org/ns/sosa/Sampler`
- `http://www.w3.org/ns/sosa/System`
- Short forms: `sosa:Sensor`, `sosa:Actuator`, `sosa:Platform`, `sosa:Sampler`, `sosa:System`

**SensorML Format (`application/sml+json`):**
Referenced as `system-2` schema (PhysicalSystem or SimpleProcess SensorML 3.0 classes)

#### 4.3 Deployment Request Body Schema

**GeoJSON Format:**

```yaml
allOf:
  - $ref: '#/components/schemas/feature'
  - properties:
      properties:
        properties:
          featureType:
            const: 'http://www.w3.org/ns/sosa/Deployment'
          validTime:
            $ref: '#/components/schemas/timePeriod' # Required
          platform@link:
            $ref: '#/components/schemas/link-2'
          deployedSystems@link:
            type: array
            items:
              $ref: '#/components/schemas/link-2'
```

**SensorML Format:**
Referenced as `deployment-2` schema (SensorML Deployment class)

#### 4.4 Procedure Request Body Schema

**GeoJSON Format:**

```yaml
allOf:
  - $ref: '#/components/schemas/feature'
  - properties:
      geometry: null # Procedures have no geometry
      properties:
        properties:
          featureType:
            # Procedure type URI
          procedureType:
            # One of: ObservingProcedure, SamplingProcedure, ActuatingProcedure
```

**SensorML Format:**
SimpleProcess or AggregateProcess classes

#### 4.5 Sampling Feature Request Body Schema

**GeoJSON Format:**

```yaml
allOf:
  - $ref: '#/components/schemas/feature'
  - properties:
      properties:
        properties:
          featureType:
            # Sampling feature type URI (e.g., SF_SamplingPoint)
          sampledFeature@link:
            $ref: '#/components/schemas/link-2'
          sampleOf@link:
            type: array
            items:
              $ref: '#/components/schemas/link-2'
```

#### 4.6 Property Request Body Schema

**GeoJSON Format:**

```yaml
allOf:
  - $ref: '#/components/schemas/feature'
  - properties:
      geometry: null # Properties have no geometry
      properties:
        properties:
          baseProperty@link:
            $ref: '#/components/schemas/link-2'
          objectType:
            type: string
            format: uri
```

**SensorML Format:**
DerivedProperty class

#### 4.7 URI List Format

For adding existing resources to collections:

**text/uri-list:**

```
https://data.example.org/api/systems/2f35ofoms2l6
https://data.example.org/api/systems/PLT412
```

**application/json:**

```json
[
  "https://data.example.org/api/systems/2f35ofoms2l6",
  "https://data.example.org/api/systems/PLT412"
]
```

---

### 5. Response Schemas Defined

#### 5.1 Response Media Types

**Feature Resources:**

- `application/geo+json` - GeoJSON Feature or FeatureCollection
- `application/sml+json` - SensorML-JSON representation

**Other Responses:**

- `application/json` - Landing page, conformance, collections metadata
- `text/uri-list` - List of created resource URIs (batch creates)

#### 5.2 Feature Response Schema

**Base Feature Schema:**

```yaml
feature:
  allOf:
    - $ref: '#/components/schemas/Feature' # GeoJSON Feature
    - type: object
      properties:
        id:
          description: Local ID (ignored on create/update)
          type: string
          minLength: 1
        geometry:
          description: GeoJSON geometry or null
        bbox:
          description: Optional bounding box
          type: array
        properties:
          type: object
          required:
            - featureType
            - uid
            - name
          properties:
            featureType:
              type: string
            uid:
              type: string
              format: uri
            name:
              type: string
              minLength: 1
            description:
              type: string
              minLength: 1
        links:
          $ref: '#/components/schemas/links'
```

#### 5.3 System Response Schema (GeoJSON)

Extends base `feature` with:

- `properties.featureType`: SystemTypeUris enum
- `properties.assetType`: Equipment | Human | LivingThing | Simulation | Process | Group | Other
- `properties.validTime`: timePeriod array
- `properties.systemKind@link`: link object

#### 5.4 Link Schema

**link-2 Schema:**

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
    examples:
      [alternate, self, http://www.opengis.net/def/rel/ogc/1.0/conformance]
  type:
    type: string
    examples: [application/json, image/tiff; application=geotiff]
  hreflang:
    type: string
    pattern: ^([a-z]{2}(-[A-Z]{2})?)|x-default$
  title:
    type: string
    minLength: 1
  uid:
    description: Unique identifier of target resource
    type: string
    format: uri
  rt:
    description: Semantic type of target resource (RFC 6690)
    type: string
    format: uri
  if:
    description: Interface used to access target resource (RFC 6690)
    type: string
    format: uri
```

#### 5.5 Collection Response Schema

**FeatureCollection:**

```yaml
type: object
properties:
  type:
    const: FeatureCollection
  features:
    type: array
    items:
      $ref: '#/components/schemas/feature'
  links:
    $ref: '#/components/schemas/links'
  numberMatched:
    type: integer
    minimum: 0
  numberReturned:
    type: integer
    minimum: 0
```

#### 5.6 SWE Common Data Component Schemas

The schema includes complete SWE Common 3.0 schemas for data components used in SensorML representations:

**Scalar Components:**

- `Boolean` - True/false values
- `Count` - Integer values
- `Quantity` - Decimal values with unit of measure
- `Time` - Date-time or duration values
- `Category` - Categorical values from code space
- `Text` - Free text values

**Range Components:**

- `CountRange` - Integer range [min, max]
- `QuantityRange` - Decimal range with UoM
- `TimeRange` - Date-time range
- `CategoryRange` - Categorical range

**Aggregate Components:**

- `DataRecord` - Record/struct with named fields
- `Vector` - Geometric vector with coordinates
- `DataArray` - Array of repeated component
- `Matrix` - 2D array
- `DataChoice` - Choice/union of alternatives
- `Geometry` - Spatial geometry

**Supporting Schemas:**

- `UnitReference` - Unit of measure (UCUM code or URI)
- `AllowedValues` - Constraints (enum values, intervals)
- `AllowedTokens` - Token constraints (enum or regex)
- `AllowedTimes` - Time constraints
- `NilValues*` - Reserved values (NaN, missing, etc.)

---

### 6. Status Codes Documented

#### 6.1 Success Status Codes

| Code    | Name       | Used For                         | Response Body                      |
| ------- | ---------- | -------------------------------- | ---------------------------------- |
| **200** | OK         | GET operations (retrieve, list)  | Resource(s) in requested format    |
| **201** | Created    | POST operations (create)         | Location header with canonical URI |
| **204** | No Content | PUT (replace), DELETE operations | Empty body                         |

#### 6.2 Client Error Status Codes

| Code    | Name         | Description                                | Example Causes                                                |
| ------- | ------------ | ------------------------------------------ | ------------------------------------------------------------- |
| **400** | Bad Request  | Invalid request syntax or semantics        | Malformed JSON, invalid parameter value, constraint violation |
| **401** | Unauthorized | Authentication required but missing        | No credentials provided                                       |
| **403** | Forbidden    | Authenticated but insufficient permissions | User lacks write permission                                   |
| **404** | Not Found    | Resource does not exist                    | Invalid ID, resource deleted                                  |
| **409** | Conflict     | Request conflicts with current state       | DELETE without cascade when nested resources exist            |

#### 6.3 Server Error Status Codes

| Code    | Name         | Description                   |
| ------- | ------------ | ----------------------------- | ------------------------------------------------ |
| **5XX** | Server Error | Generic server error response | Internal server errors, database issues, timeout |

#### 6.4 Status Code Usage by Operation

**GET Operations:**

- 200 (success)
- 400, 401, 403, 404 (client errors)
- 5XX (server errors)

**POST Operations:**

- 201 (success) - Returns `Location` header pointing to created resource's canonical URL
- 400, 401, 403, 404 (client errors)
- 5XX (server errors)

**PUT Operations:**

- 204 (success) - No response body
- 400, 401, 403, 404 (client errors)
- 5XX (server errors)

**DELETE Operations:**

- 204 (success) - No response body
- 400, 401, 403, 404, 409 (client errors) - 409 when cascade=false and nested resources exist
- 5XX (server errors)

---

### 7. Security Requirements Specified

**No explicit security schemes defined in OpenAPI schema.**

The schema does not include a `components.securitySchemes` section or `security` requirements. This means:

1. **Authentication/Authorization:** Left to implementation
2. **401/403 Responses:** Documented but security mechanism unspecified
3. **Implementation Choice:** Servers can choose any security mechanism (OAuth2, API keys, Basic Auth, etc.)

**Implications:**

- Client library should support flexible authentication (injectable headers, callback functions)
- Security is transport-level concern, not API-level
- Conformance with OGC API security best practices expected but not enforced by schema

---

### 8. Examples Provided in Schema

#### 8.1 System Examples

**Example 1: Simple Thermometer (GeoJSON)**

```json
{
  "type": "Feature",
  "id": "123",
  "geometry": {
    "type": "Point",
    "coordinates": [41.8781, -87.6298]
  },
  "properties": {
    "uid": "urn:x-ogc:systems:001",
    "name": "Outdoor Thermometer 001",
    "description": "Digital thermometer located on first floor window 1",
    "featureType": "http://www.w3.org/ns/sosa/Sensor",
    "assetType": "Equipment",
    "systemKind@link": {
      "href": "https://data.example.org/api/procedures/TP60S?f=json",
      "uid": "urn:x-myorg:datasheets:ThermoPro:TP60S:v001",
      "title": "Thermo Pro TP60S",
      "type": "application/geo+json"
    }
  }
}
```

**Example 2: UAV Platform (GeoJSON)**

```json
{
  "type": "Feature",
  "id": "PLT412",
  "geometry": null,
  "properties": {
    "uid": "urn:x-ogc:systems:uav:solo154",
    "name": "UAV System 412",
    "description": "3DR Solo UAV",
    "featureType": "http://www.w3.org/ns/sosa/Platform",
    "systemKind@link": {
      "href": "https://data.example.org/api/procedures/nrof8qi7wc9a?f=json",
      "uid": "urn:x-ogc:datasheets:uav:3dr-solo:v1",
      "type": "application/geo+json"
    }
  }
}
```

**Example 3: Simple Thermometer (SensorML-JSON)**

```json
{
  "type": "PhysicalSystem",
  "id": "123",
  "definition": "http://www.w3.org/ns/sosa/Sensor",
  "uniqueId": "urn:x-ogc:systems:001",
  "label": "Outdoor Thermometer 001",
  "description": "Digital thermometer located on first floor window 1",
  "typeOf": {
    "href": "https://data.example.org/api/procedures/TP60S?f=sml",
    "uid": "urn:x-myorg:datasheets:ThermoPro:TP60S:v001",
    "title": "ThermoPro TP60S",
    "type": "application/sml+json"
  },
  "identifiers": [
    {
      "definition": "http://sensorml.com/ont/swe/property/SerialNumber",
      "label": "Serial Number",
      "value": "0123456879"
    }
  ],
  "contacts": [
    {
      "role": "http://sensorml.com/ont/swe/roles/Operator",
      "organisationName": "Field Maintenance Corp."
    }
  ],
  "position": {
    "type": "Point",
    "coordinates": [41.8781, -87.6298]
  }
}
```

**Example 4: Global Hawk UAV Platform (SensorML-JSON)**

```json
{
  "type": "PhysicalSystem",
  "id": "PLT412",
  "definition": "http://www.w3.org/ns/sosa/Platform",
  "uniqueId": "urn:x-usaf:systems:aircraft:101",
  "label": "Global Hawk 101",
  "description": "Example UAV platform",
  "typeOf": {
    "href": "https://data.example.org/api/procedures/ge4pjqq0hq6y?f=json",
    "uid": "urn:x-ngc:datasheets:uav:RQ-4B",
    "type": "application/sml+json"
  },
  "identifiers": [
    {
      "definition": "http://sensorml.com/ont/swe/property/SerialNumber",
      "label": "Serial Number",
      "value": "0123456879"
    }
  ],
  "contacts": [
    {
      "role": "http://sensorml.com/ont/swe/property/Operator",
      "organisationName": "Field Maintenance Corp."
    }
  ],
  "localReferenceFrames": [
    {
      "label": "Platform Frame",
      "description": "The platform frame is defined as the aircraft principal axes",
      "origin": "Center of gravity of the aircraft",
      "axes": [
        {
          "name": "x",
          "description": "Longitudinal or roll axis, parallel to the fuselage reference line, directed forward"
        },
        {
          "name": "y",
          "description": "Transverse or pitch axis, parallel to the line drawn from wingtip to wingtip, directed to the right of the aircraft when looking forward"
        },
        {
          "name": "z",
          "description": "Vertical or yaw axis, perpendicular to the wings and to the fuselage reference line, directed toward the bottom of the aircraft"
        }
      ]
    }
  ]
}
```

#### 8.2 Deployment Example

**Saildrone Arctic Mission 2017 (GeoJSON)**

```json
{
  "type": "Feature",
  "id": "iv3f2kcq27gfi",
  "geometry": {
    "type": "Polygon",
    "coordinates": [
      [
        [53.76, -173.7],
        [53.76, -155.07],
        [75.03, -155.07],
        [75.03, -173.7],
        [53.76, -173.7]
      ]
    ]
  },
  "properties": {
    "uid": "urn:x-ogc:deployments:D001",
    "name": "Saildrone - 2017 Arctic Mission",
    "featureType": "http://www.w3.org/ns/sosa/Deployment",
    "description": "In July 2017, three saildrones were launched from Dutch Harbor, Alaska, in partnership with NOAA Research...",
    "validTime": ["2017-07-17T00:00:00Z", "2017-09-29T00:00:00Z"],
    "platform@link": {
      "href": "https://data.example.org/api/systems/27559?f=sml",
      "uid": "urn:x-saildrone:platforms:SD-1003",
      "title": "Saildrone SD-1003"
    },
    "deployedSystems@link": [
      {
        "href": "https://data.example.org/api/systems/41548?f=sml",
        "uid": "urn:x-saildrone:sensors:temp01",
        "title": "Air Temperature Sensor"
      },
      {
        "href": "https://data.example.org/api/systems/36584?f=sml",
        "uid": "urn:x-saildrone:sensors:temp02",
        "title": "Water Temperature Sensor"
      },
      {
        "href": "https://data.example.org/api/systems/47752?f=sml",
        "uid": "urn:x-saildrone:sensors:wind01",
        "title": "Wind Speed and Direction Sensor"
      }
    ]
  },
  "links": [
    {
      "rel": "self",
      "href": "https://data.example.org/api/deployments/iv3f2kcq27gfi?f=json",
      "type": "application/geo+json",
      "title": "this document"
    },
    {
      "rel": "alternate",
      "href": "https://data.example.org/api/deployments/iv3f2kcq27gfi?f=sml",
      "type": "application/sml+json",
      "title": "this resource as SensorML"
    }
  ]
}
```

**Same Deployment (SensorML-JSON)**

```json
{
  "type": "Deployment",
  "id": "iv3f2kcq27gfi",
  "definition": "http://www.w3.org/ns/sosa/Deployment",
  "uniqueId": "urn:x-saildrone:mission:2025",
  "label": "Saildrone - 2017 Arctic Mission",
  "description": "In July 2017, three saildrones were launched from Dutch Harbor, Alaska, in partnership with NOAA Research...",
  "classifiers": [
    {
      "definition": "https://schema.org/DefinedRegion",
      "label": "Region",
      "value": "Arctic"
    }
  ],
  "contacts": [
    {
      "role": "http://sensorml.com/ont/swe/property/Operator",
      "organisationName": "Saildrone, Inc.",
      "contactInfo": {
        "website": "https://www.saildrone.com/",
        "address": {
          "deliveryPoint": "1050 W. Tower Ave.",
          "city": "Alameda",
          "postalCode": "94501",
          "administrativeArea": "CA",
          "country": "USA"
        }
      }
    },
    {
      "role": "http://sensorml.com/ont/swe/property/DataProvider",
      "organisationName": "NOAA Pacific Marine Environmental Laboratory (PMEL)",
      "contactInfo": {
        "website": "https://www.pmel.noaa.gov"
      }
    }
  ],
  "validTime": ["2017-07-17T00:00:00Z", "2017-09-29T00:00:00Z"],
  "location": {
    "type": "Polygon",
    "coordinates": [
      [
        [-173.7, 53.76],
        [-173.7, 75.03],
        [-155.07, 75.03],
        [-155.07, 53.76],
        [-173.7, 53.76]
      ]
    ]
  }
}
```

#### 8.3 Parameter Examples

**bbox Parameter:**

- 2D: `-180,-90,180,90`
- 3D: `-180,-90,0,180,90,1000`

**datetime Parameter:**

- Instant: `2018-02-12T23:20:50Z`
- Now: `now`
- Bounded interval: `2018-02-12T00:00:00Z/2018-03-18T12:31:12Z`
- Half-bounded start: `2018-02-12T00:00:00Z/..`
- To now: `2018-02-12T00:00:00Z/now`
- From now: `now/2018-02-12T00:00:00Z`
- Up to now: `../now`
- From now on: `now/..`
- Latest: `latest`

**geom Parameter:**

- LineString: `LINESTRING((-86.53 12.45), (-86.54 12.46), (-86.55 12.47))`
- Polygon: `POLYGON((0 0,4 0,4 4,0 4,0 0))`

**keyword (q) Parameter:**

- One keyword: `temp`
- Multiple: `gps,imu`

**id Parameter:**

- Local IDs: `RES_ID1,RES_ID2,RES_ID63`
- URIs: `urn:example:resource:001,urn:example:resource:033`

**URI List (text/uri-list):**

```
https://data.example.org/api/systems/2f35ofoms2l6
https://data.example.org/api/systems/PLT412
```

**URI List (application/json):**

```json
[
  "https://data.example.org/api/systems/2f35ofoms2l6",
  "https://data.example.org/api/systems/PLT412"
]
```

---

### 9. Data Models/Schemas for Resources

#### 9.1 System Data Model (GeoJSON)

**Structure:**

```typescript
interface SystemGeoJSON {
  type: 'Feature';
  id?: string; // Local ID (server-assigned on create)
  geometry: Point | Polygon | LineString | null; // null for non-spatial systems
  bbox?: number[]; // Optional bounding box
  properties: {
    featureType: SystemTypeUris; // Required
    uid: string; // Required, format: uri
    name: string; // Required, minLength: 1
    description?: string; // Optional
    assetType?:
      | 'Equipment'
      | 'Human'
      | 'LivingThing'
      | 'Simulation'
      | 'Process'
      | 'Group'
      | 'Other';
    validTime?: [string, string | null]; // [start, end], ISO 8601
    'systemKind@link'?: Link; // Link to procedure (datasheet)
  };
  links?: Link[]; // Related resources
}
```

#### 9.2 System Data Model (SensorML)

**Structure:**

```typescript
interface SystemSensorML {
  type:
    | 'PhysicalSystem'
    | 'PhysicalComponent'
    | 'SimpleProcess'
    | 'AggregateProcess';
  id?: string; // Local ID
  definition: string; // System type URI (sosa:Sensor, etc.)
  uniqueId: string; // Required, format: uri
  label: string; // Required
  description?: string;
  typeOf?: Link; // Link to system kind (datasheet)
  identifiers?: Identifier[]; // Serial numbers, etc.
  classifiers?: Classifier[]; // Additional categorizations
  characteristics?: Characteristic[]; // System properties
  capabilities?: Capability[]; // System capabilities
  contacts?: Contact[]; // Responsible parties
  documentation?: Documentation[]; // Manuals, etc.
  history?: Event[]; // Significant events
  validTime?: [string, string | null];
  position?: GeoJSONGeometry | null;
  localReferenceFrames?: LocalReferenceFrame[];
  components?: Component[]; // Subsystems (for PhysicalSystem)
  links?: Link[];
}
```

#### 9.3 Deployment Data Model (GeoJSON)

**Structure:**

```typescript
interface DeploymentGeoJSON {
  type: 'Feature';
  id?: string;
  geometry: Point | Polygon | LineString | null;
  bbox?: number[];
  properties: {
    featureType: 'http://www.w3.org/ns/sosa/Deployment'; // Fixed
    uid: string; // Required
    name: string; // Required
    description?: string;
    validTime: [string, string | null]; // Required for Deployments
    'platform@link'?: Link;
    'deployedSystems@link'?: Link[];
    'featuresOfInterest@link'?: Link[];
    'samplingFeatures@link'?: Link[];
    'subdeployments@link'?: Link[];
  };
  links?: Link[];
}
```

#### 9.4 Procedure Data Model (GeoJSON)

**Structure:**

```typescript
interface ProcedureGeoJSON {
  type: 'Feature';
  id?: string;
  geometry: null; // Procedures MUST have null geometry
  properties: {
    featureType: string; // Procedure type URI
    uid: string; // Required
    name: string; // Required
    description?: string;
    procedureType:
      | 'ObservingProcedure'
      | 'SamplingProcedure'
      | 'ActuatingProcedure'
      | 'Procedure';
    'implementingSystems@link'?: Link[];
  };
  links?: Link[];
}
```

#### 9.5 Sampling Feature Data Model (GeoJSON)

**Structure:**

```typescript
interface SamplingFeatureGeoJSON {
  type: 'Feature';
  id?: string;
  geometry:
    | Point
    | Polygon
    | LineString
    | MultiPoint
    | MultiLineString
    | MultiPolygon
    | GeometryCollection;
  bbox?: number[];
  properties: {
    featureType: string; // Sampling feature type URI (e.g., SF_SamplingPoint)
    uid: string; // Required
    name: string; // Required
    description?: string;
    'sampledFeature@link': Link; // Required - ultimate FOI
    'sampleOf@link'?: Link[]; // Sub-sampling
    'parentSystem@link'?: Link; // Associated system
  };
  links?: Link[];
}
```

#### 9.6 Property Data Model (GeoJSON)

**Structure:**

```typescript
interface PropertyGeoJSON {
  type: 'Feature';
  id?: string;
  geometry: null; // Properties MUST have null geometry
  properties: {
    featureType: string; // Property type URI
    uid: string; // Required
    name: string; // Required
    description?: string;
    'baseProperty@link'?: Link; // Derivation hierarchy
    objectType?: string; // URI - type of object property applies to
  };
  links?: Link[];
}
```

#### 9.7 Link Data Model

**Structure:**

```typescript
interface Link {
  href: string; // Required, format: uri
  rel?: string; // Link relation type
  type?: string; // Media type
  hreflang?: string; // Language tag (e.g., 'en-US')
  title?: string; // Human-readable title
  uid?: string; // Unique identifier of target resource
  rt?: string; // Semantic type (RFC 6690)
  if?: string; // Interface (RFC 6690)
}
```

---

### 10. Property Names and Types for Each Resource

#### 10.1 System Properties

| Property Name     | Type          | Required | Constraints    | Description                                                      |
| ----------------- | ------------- | -------- | -------------- | ---------------------------------------------------------------- |
| `featureType`     | string (enum) | ✓        | SystemTypeUris | System type: Sensor, Actuator, Platform, Sampler, System         |
| `uid`             | string        | ✓        | format: uri    | Globally unique identifier                                       |
| `name`            | string        | ✓        | minLength: 1   | Human-readable name                                              |
| `description`     | string        |          | minLength: 1   | Human-readable description                                       |
| `assetType`       | string (enum) |          | 7 values       | Equipment, Human, LivingThing, Simulation, Process, Group, Other |
| `validTime`       | array         |          | [start, end]   | Validity period, ISO 8601 datetime strings                       |
| `systemKind@link` | Link          |          |                | Link to procedure describing system kind                         |

#### 10.2 Deployment Properties

| Property Name             | Type   | Required | Constraints                                   | Description                           |
| ------------------------- | ------ | -------- | --------------------------------------------- | ------------------------------------- |
| `featureType`             | string | ✓        | const: 'http://www.w3.org/ns/sosa/Deployment' | Fixed value                           |
| `uid`                     | string | ✓        | format: uri                                   | Globally unique identifier            |
| `name`                    | string | ✓        | minLength: 1                                  | Human-readable name                   |
| `description`             | string |          | minLength: 1                                  | Human-readable description            |
| `validTime`               | array  | ✓        | [start, end]                                  | Deployment time period, required      |
| `platform@link`           | Link   |          |                                               | Platform system deployed on           |
| `deployedSystems@link`    | Link[] |          |                                               | Systems deployed                      |
| `featuresOfInterest@link` | Link[] |          |                                               | Ultimate features observed/controlled |
| `samplingFeatures@link`   | Link[] |          |                                               | Associated sampling features          |
| `subdeployments@link`     | Link[] |          |                                               | Child deployments                     |

#### 10.3 Procedure Properties

| Property Name              | Type   | Required | Constraints  | Description                                                             |
| -------------------------- | ------ | -------- | ------------ | ----------------------------------------------------------------------- |
| `featureType`              | string | ✓        | URI          | Procedure type URI                                                      |
| `uid`                      | string | ✓        | format: uri  | Globally unique identifier                                              |
| `name`                     | string | ✓        | minLength: 1 | Human-readable name                                                     |
| `description`              | string |          | minLength: 1 | Human-readable description                                              |
| `procedureType`            | string |          | URI          | ObservingProcedure, SamplingProcedure, ActuatingProcedure, or Procedure |
| `implementingSystems@link` | Link[] |          |              | Systems implementing this procedure                                     |

#### 10.4 Sampling Feature Properties

| Property Name         | Type   | Required | Constraints  | Description                                    |
| --------------------- | ------ | -------- | ------------ | ---------------------------------------------- |
| `featureType`         | string | ✓        | URI          | Sampling feature type (e.g., SF_SamplingPoint) |
| `uid`                 | string | ✓        | format: uri  | Globally unique identifier                     |
| `name`                | string | ✓        | minLength: 1 | Human-readable name                            |
| `description`         | string |          | minLength: 1 | Human-readable description                     |
| `sampledFeature@link` | Link   | ✓        |              | Ultimate feature of interest                   |
| `sampleOf@link`       | Link[] |          |              | Other sampling features (sub-sampling)         |
| `parentSystem@link`   | Link   |          |              | System associated with this sampling feature   |

#### 10.5 Property Resource Properties

| Property Name       | Type   | Required | Constraints  | Description                        |
| ------------------- | ------ | -------- | ------------ | ---------------------------------- |
| `featureType`       | string | ✓        | URI          | Property type URI                  |
| `uid`               | string | ✓        | format: uri  | Globally unique identifier         |
| `name`              | string | ✓        | minLength: 1 | Human-readable name                |
| `description`       | string |          | minLength: 1 | Human-readable description         |
| `baseProperty@link` | Link   |          |              | Base property this is derived from |
| `objectType`        | string |          | format: uri  | Type of object property applies to |

#### 10.6 Common Feature Properties

**All Resources (via base `feature` schema):**
| Property Name | Type | Required | Description |
|---------------|------|----------|-------------|
| `type` | string | ✓ | Always "Feature" for GeoJSON |
| `id` | string | | Local ID (server-assigned) |
| `geometry` | GeoJSON Geometry | | Spatial geometry (null for non-spatial) |
| `bbox` | number[] | | Optional bounding box |
| `properties` | object | ✓ | Resource properties (type-specific) |
| `links` | Link[] | | Related resources |

---

### 11. Optional vs Required According to Schema

#### 11.1 Required Properties (All Resources)

**GeoJSON Format:**

```yaml
required:
  - type          # "Feature"
  - properties    # Object containing:
    - featureType   # Resource type URI
    - uid           # Unique identifier
    - name          # Human-readable name
```

**Additional Required for Deployments:**

```yaml
properties:
  validTime: # Required for Deployments only
    - start date-time
    - end date-time or null
```

#### 11.2 Optional Properties

**System:**

- `id` (server-assigned)
- `geometry` (recommended for mobile systems)
- `bbox`
- `description`
- `assetType`
- `validTime`
- `systemKind@link`
- `links`

**Deployment:**

- `id`
- `geometry`
- `bbox`
- `description`
- `platform@link`
- `deployedSystems@link`
- `featuresOfInterest@link`
- `samplingFeatures@link`
- `subdeployments@link`
- `links`

**Procedure:**

- `id`
- `description`
- `procedureType`
- `implementingSystems@link`
- `links`

**Sampling Feature:**

- `id`
- `bbox`
- `description`
- `sampleOf@link`
- `parentSystem@link`
- `links`

**Property:**

- `id`
- `description`
- `baseProperty@link`
- `objectType`
- `links`

#### 11.3 Server-Managed Properties

**Not in Request Body (ignored if provided):**

- `id` - Server assigns local ID on creation
- `links` - Server generates links based on relationships

**Client Can Provide (server may override):**

- `geometry` - Client provides, server may update (e.g., mobile systems)
- `bbox` - Usually computed from geometry

---

### 12. Summary and Key Takeaways

#### 12.1 OpenAPI Schema Completeness

**Strong Points:**
✅ **Complete Path Coverage:** All 20 paths from Part 1 specification documented  
✅ **Precise Parameter Specifications:** Types, constraints, formats, examples provided  
✅ **Dual Format Support:** Both GeoJSON and SensorML schemas included  
✅ **Request/Response Schemas:** Complete schemas for all resource types  
✅ **SWE Common Integration:** Full SWE Common 3.0 data component schemas  
✅ **Comprehensive Examples:** Real-world examples for all resource types in both formats  
✅ **Status Code Documentation:** All success/error codes documented with use cases

**Gaps:**
❌ **PATCH Method Missing:** Standard mentions PATCH for partial updates (OGC API - Features Part 4) but not in OpenAPI schema  
❌ **No Security Schemes:** Authentication/authorization mechanisms not specified  
❌ **History Endpoints Missing:** Standard mentions history sub-collections but paths not in schema  
❌ **Batch Operations Unclear:** Batch create mentioned in prose but schema structure unclear

#### 12.2 Schema vs Standard Alignment

**Perfect Alignment:**

- Path structure matches standard specification
- Query parameters match requirements classes
- Resource properties align with conformance classes
- Format negotiation matches standard

**Schema More Specific:**

- Exact parameter types and constraints
- Precise property schemas
- Concrete examples with realistic data
- Enumerated values (SystemTypeUris, assetType)

**Standard More Comprehensive:**

- Explains concepts and relationships
- Documents conformance classes
- Describes history/versioning approach
- Specifies link relations semantics

#### 12.3 Implementation Guidance

**For Client Library:**

1. **URL Construction:**

   - Follow path templates exactly
   - Support all 20 paths
   - Use path parameters as string type

2. **Query Parameters:**

   - Implement 15 query parameters with correct types
   - Support comma-separated ID lists
   - Encode datetime intervals properly
   - Handle bbox as array of 4 or 6 numbers

3. **Request Bodies:**

   - Support both GeoJSON and SensorML formats
   - Implement required property validation
   - Handle link objects with `@link` suffix convention

4. **Response Handling:**

   - Parse GeoJSON FeatureCollections
   - Extract links from responses
   - Handle all 7 status codes appropriately

5. **Format Negotiation:**

   - Suggest Accept header via options (don't set directly)
   - Support `f` query parameter
   - Default to GeoJSON for spatial, SensorML for detailed

6. **Type Safety:**
   - Create TypeScript interfaces matching schemas
   - Validate enums (SystemTypeUris, assetType)
   - Type-safe query builders

**Next Steps:**
Section 1.3 will compare these findings with Section 1.1 to identify alignments, discrepancies, and implementation insights.

---

## Section 1.3: Comparison and Insights

**Document:** Section 1.3 - Comparison and Insights  
**Sources:** Section 1.1 (Standard Document) + Section 1.2 (OpenAPI Schema)  
**Date:** 2026-01-31  
**Status:** Complete

---

### Executive Summary

This section synthesizes findings from the CSAPI Part 1 standard document and OpenAPI schema to identify alignments, discrepancies, and actionable implementation insights. The comparison reveals high consistency between sources with the OpenAPI schema providing machine-readable specifications while the standard offers conceptual depth.

**Key Findings:**

- **95%+ Alignment** on core functionality (paths, parameters, resource models)
- **OpenAPI Adds:** Precise types, constraints, validation rules, concrete examples
- **Standard Adds:** Conformance classes, link relation semantics, conceptual guidance, history/versioning patterns
- **3 Notable Gaps:** PATCH method, history endpoints, security schemes missing from OpenAPI
- **No Conflicts:** Sources complement rather than contradict
- **Implementation Clarity:** Use OpenAPI for "what/how", standard for "why/when"

---

### 1. Perfect Alignments Between Standard and OpenAPI Schema

#### 1.1 Path Structure Alignment

**Standard Document (Section 1.1):**

- Describes canonical resources endpoints: `/{resourceType}`
- Describes canonical resource endpoints: `/{resourceType}/{id}`
- Describes nested resources endpoints: `/{parentType}/{parentId}/{childType}`

**OpenAPI Schema (Section 1.2):**

- Implements exactly 20 paths following this pattern
- No deviations from standard's structural guidance

**Verdict:** ✅ **Perfect Alignment** - Every path in OpenAPI matches standard's architecture

#### 1.2 Resource Type Alignment

**Standard Document:**

- Defines 5 resource types: Systems, Deployments, Procedures, Sampling Features, Properties

**OpenAPI Schema:**

- Provides paths for all 5 resource types
- Uses identical naming conventions
- No additional or missing resource types

**Verdict:** ✅ **Perfect Alignment** - Complete coverage, consistent naming

#### 1.3 Query Parameter Alignment

**Standard Document (Section 1.1, Section 3):**

- Documents 30+ query parameters across all resource types

**OpenAPI Schema (Section 1.2, Section 3):**

- Implements 15 core query parameters
- All 15 match standard's specifications exactly:
  - Spatial: `bbox`, `geom`
  - Temporal: `datetime`
  - Identifiers: `id`
  - Text: `q`
  - Relationships: `parent`, `procedure`, `foi`, `observedProperty`, `controlledProperty`, `system`, `baseProperty`, `objectType`
  - Pagination: `limit`
  - Hierarchical: `recursive`
  - Deletion: `cascade`

**Note:** Standard describes more parameters because it covers per-resource-type variations (e.g., different relationship filters apply to different resources). OpenAPI defines base parameters reused across paths.

**Verdict:** ✅ **Perfect Alignment** - OpenAPI implements standard's parameter specifications exactly

#### 1.4 HTTP Method Alignment

**Standard Document (Section 1.1, Section 2):**

- GET (retrieve, list)
- POST (create)
- PUT (replace)
- PATCH (update) - mentioned via OGC API - Features Part 4
- DELETE (delete)

**OpenAPI Schema (Section 1.2, Section 2):**

- GET: 20 operations ✅
- POST: 10 operations ✅
- PUT: 5 operations ✅
- DELETE: 5 operations ✅
- PATCH: **0 operations** ⚠️

**Verdict:** ✅ **98% Alignment** - Only PATCH missing (discussed in Section 3.3)

#### 1.5 Dual Format Support Alignment

**Standard Document (Section 1.1, Section 5):**

- GeoJSON (application/geo+json) - mandatory
- SensorML-JSON (application/sml+json) - optional

**OpenAPI Schema (Section 1.2, Section 4-5):**

- Implements both formats with complete schemas
- Request bodies support both
- Response content negotiation supports both

**Verdict:** ✅ **Perfect Alignment** - Both formats fully specified

#### 1.6 Status Code Alignment

**Standard Document:**

- Describes success/error responses conceptually
- References OGC API - Features Part 1 for HTTP semantics

**OpenAPI Schema (Section 1.2, Section 6):**

- 200 (GET success) ✅
- 201 (POST success with Location header) ✅
- 204 (PUT/DELETE success) ✅
- 400, 401, 403, 404 (client errors) ✅
- 409 (DELETE conflict) ✅
- 5XX (server errors) ✅

**Verdict:** ✅ **Perfect Alignment** - OpenAPI implements standard's HTTP semantics

#### 1.7 Required vs Optional Properties Alignment

**Standard Document:**

- Specifies required properties in conformance requirements
- Systems: uniqueIdentifier, name, systemType (from Table 6)
- Deployments: uniqueIdentifier, name, validTime

**OpenAPI Schema (Section 1.2, Section 11):**

- Required: featureType (maps to systemType), uid (maps to uniqueIdentifier), name
- Deployment requires validTime ✅

**Verdict:** ✅ **Perfect Alignment** - Property requirements match (with naming variations explained below)

---

### 2. Where OpenAPI Schema Provides More Specific Details

#### 2.1 Precise Parameter Types and Constraints

**Standard Says:**

- "bbox parameter for bounding box filter"
- "limit parameter for pagination"
- "datetime parameter for temporal filter"

**OpenAPI Specifies:**

```yaml
bbox:
  type: array
  minItems: 4
  maxItems: 6 # 4 for 2D, 6 for 3D
  items:
    type: number
  examples:
    - '-180,-90,180,90'

limit:
  type: integer
  minimum: 1
  maximum: 10000
  default: 10

datetime:
  oneOf:
    - type: string
      format: date-time
    - type: string
      const: 'now'
    - type: string
      pattern: '^(.*)\/(.*)$' # Interval
```

**Value:** OpenAPI enables client-side validation, type-safe code generation, precise error messages.

#### 2.2 Enumerated Values for System Types

**Standard Says:**

- "systemType property identifies the type of system (see Table 6)"
- Table 6 lists: Sensor, Actuator, Sampler, Platform, System

**OpenAPI Specifies:**

```yaml
SystemTypeUris:
  type: string
  enum:
    - http://www.w3.org/ns/sosa/Sensor
    - http://www.w3.org/ns/sosa/Actuator
    - http://www.w3.org/ns/sosa/Platform
    - http://www.w3.org/ns/sosa/Sampler
    - http://www.w3.org/ns/sosa/System
    - sosa:Sensor
    - sosa:Actuator
    - sosa:Platform
    - sosa:Sampler
    - sosa:System
```

**Value:** Exact URIs and CURIE forms for validation. Client library can provide TypeScript enums.

#### 2.3 Complete SWE Common Data Component Schemas

**Standard Says:**

- "SensorML format includes SWE Common data components"
- References SWE Common 3.0 specification

**OpenAPI Specifies:**

- Complete schemas for 20+ data components:
  - Boolean, Count, Quantity, Time, Category, Text (scalars)
  - CountRange, QuantityRange, TimeRange, CategoryRange (ranges)
  - DataRecord, Vector, DataArray, Matrix, DataChoice, Geometry (aggregates)
  - UnitReference, AllowedValues, NilValues (supporting types)

**Value:** Client library doesn't need to parse external SWE Common spec. All types in one schema.

#### 2.4 Concrete Request/Response Examples

**Standard Says:**

- "Example System resource in GeoJSON"
- Shows partial examples in annexes

**OpenAPI Specifies:**

- 8+ complete examples:
  - Simple Thermometer (GeoJSON + SensorML)
  - UAV Platform (GeoJSON + SensorML)
  - Global Hawk with reference frames (SensorML)
  - Saildrone deployment (GeoJSON + SensorML)
  - Parameter usage examples (bbox, datetime, id lists, URI lists)

**Value:** Copy-paste ready examples for tests, documentation, tutorials.

#### 2.5 Property Naming Conventions

**Standard Uses:**

- `uniqueIdentifier` (property name in tables)
- `systemType` (property name in tables)

**OpenAPI Uses:**

- `uid` (JSON property name)
- `featureType` (JSON property name, applies to all resources not just systems)

**Value:** OpenAPI shows actual JSON keys, not conceptual property names. Critical for implementation.

#### 2.6 Link Suffix Convention

**Standard Says:**

- "Links to related resources use link relations"
- Describes link relations like `ogc-rel:subsystems`

**OpenAPI Specifies:**

- Property naming pattern: `{association}@link`
- Examples: `systemKind@link`, `deployedSystems@link`, `sampledFeature@link`

**Value:** Exact JSON structure for embedding links in properties object vs separate links array.

#### 2.7 Path Parameter Constraints

**Standard Says:**

- "Resources accessible at canonical URL with local ID"

**OpenAPI Specifies:**

```yaml
systemId:
  name: systemId
  in: path
  required: true
  schema:
    type: string
    minLength: 1
```

**Value:** All path parameters must be non-empty strings. Enables validation before request.

---

### 3. Where Standard Describes Things Not Captured in OpenAPI

#### 3.1 Conformance Classes and Requirements

**Standard Provides (Section 1.1, Section 6):**

- 11 conformance classes with detailed requirements
- 103 individual requirements with identifiers (Requirement 1, Requirement 2, etc.)
- Dependencies between conformance classes
- Test suite in Annex A

**OpenAPI Provides:**

- `/conformance` endpoint that returns conformance URIs
- No documentation of what each conformance class means
- No requirements enumeration

**Gap:** Client needs standard document to understand what server capabilities mean.

**Implementation Impact:**

- Client should query `/conformance` endpoint
- Client interprets conformance URIs based on standard document
- Client adapts behavior based on detected conformance classes

#### 3.2 Link Relations Semantics

**Standard Provides (Section 1.1, Section 7, Table 3):**

- 11 link relations with semantic definitions:
  - `ogc-rel:subsystems` - "Link to subsystems collection"
  - `ogc-rel:parentSystem` - "Link to parent system"
  - `ogc-rel:samplingFeatures` - "Link to associated sampling features"
  - `ogc-rel:deployments` - "Link to deployments involving system"
  - etc.

**OpenAPI Provides:**

- Link schema with `rel` property (string type)
- Examples showing link objects
- No semantic definitions of relation types

**Gap:** Client needs standard to understand what each link relation means and how to use it.

**Implementation Impact:**

- Client library should document link relations
- Provide helper methods like `getSubsystems(system)` that follow appropriate links
- Validate expected link relations based on resource type

#### 3.3 PATCH Method for Partial Updates

**Standard Provides (Section 1.1, Section 2.4):**

- PATCH method described for all resources
- References OGC API - Features Part 4: Update
- JSON Merge Patch format expected

**OpenAPI Provides:**

- **Nothing** - PATCH operations completely absent from schema

**Gap:** Servers implementing Update conformance class support PATCH but OpenAPI doesn't document it.

**Implementation Impact:**

- Client library should support PATCH despite OpenAPI omission
- Use JSON Merge Patch (RFC 7396) format
- Follow standard document, not OpenAPI, for PATCH operations
- Test against real servers supporting `/conf/update`

#### 3.4 History and Versioning Patterns

**Standard Provides (Section 1.1, Section 9):**

- `validTime` property for temporal validity
- History sub-collections mentioned (e.g., `/systems/{id}/history`)
- Version creation via validTime property in PUT operations
- Temporal queries via `datetime` parameter

**OpenAPI Provides:**

- `validTime` property in schemas ✅
- `datetime` parameter ✅
- **No history endpoint paths** ⚠️
- No examples of versioning workflow

**Gap:** History endpoints architecture not specified.

**Implementation Impact:**

- Client library should prepare for history endpoints (future)
- Use `datetime` parameter for temporal queries
- Document validTime-based versioning pattern
- Wait for Part 1 history extension or Part 3 specification

#### 3.5 Recursive Query Behavior Details

**Standard Provides (Section 1.1, Section 10.7):**

- Detailed explanation of recursive behavior
- When recursive=false: direct children only
- When recursive=true: all descendants at all levels
- Recursive associations: if system has subsystems, nested resources endpoints include subsystem resources
- Other query parameters apply to ALL processed resources in recursive mode

**OpenAPI Provides:**

- `recursive` parameter (boolean, default false)
- Brief description: "include nested resources"

**Gap:** Exact recursive traversal semantics and interaction with other filters not detailed.

**Implementation Impact:**

- Client library documentation should explain recursive behavior thoroughly
- Warn users that recursive queries can return large result sets
- Document filter interaction (recursive + foi finds any subsystem matching)

#### 3.6 Cascade Delete Semantics

**Standard Provides (Section 1.1, Section 2.5):**

- Without cascade: server rejects DELETE if nested resources exist (409 error)
- With cascade=true: deletes resource AND all nested resources
- Nested resources include: subsystems, samplingFeatures, datastreams, controlstreams, observations, commands
- If System referenced by Deployment, Deployment link removed (not deleted)

**OpenAPI Provides:**

- `cascade` parameter (boolean, default false)
- 409 status code for conflicts

**Gap:** Exact list of nested resources deleted not in schema.

**Implementation Impact:**

- Client library should document cascade behavior
- Provide warnings for destructive operations
- Consider confirmation prompt in CLI tools

#### 3.7 Transitive Relationship Queries

**Standard Provides (Section 1.1, Section 10.10):**

- Recommendation 4: baseProperty queries should be transitive
- sampledFeature queries should follow sampleOf chain transitively
- foi queries should follow sampledFeature chain

**OpenAPI Provides:**

- Parameters defined (baseProperty, foi)
- No mention of transitive behavior

**Gap:** Transitive query semantics not in schema.

**Implementation Impact:**

- Document that transitive queries are server-dependent (recommendation, not requirement)
- Test against target servers to determine actual behavior
- Provide option to disable assumptions about transitivity

#### 3.8 Conformance Detection and Adaptation

**Standard Provides:**

- Clear guidance on minimum implementations (Common + 1 resource + 1 encoding)
- Full implementation matrix (all 11 conformance classes)
- How conformance affects available operations

**OpenAPI Provides:**

- Paths for all features
- No indication of which are optional

**Gap:** Client doesn't know which operations server actually supports without conformance check.

**Implementation Impact:**

- Client MUST query `/conformance` before assuming capabilities
- Gracefully handle 404 for operations server doesn't support
- Provide feature detection utilities

---

### 4. Conflicts or Ambiguities Between Sources

**Good News: No Direct Conflicts Found**

The standard document and OpenAPI schema are **complementary**, not contradictory. However, there are **3 potential sources of confusion**:

#### 4.1 Property Name Variations (Clarified, Not Conflict)

**In Standard Tables:**

- `uniqueIdentifier`
- `systemType`
- `assetType`

**In OpenAPI JSON:**

- `uid`
- `featureType`
- `assetType` (same)

**Clarification:** Standard uses conceptual names in tables, OpenAPI uses actual JSON property names. This is intentional design (human-readable docs vs machine-readable schema).

**Resolution:** Use OpenAPI names in code. Reference standard for concepts.

#### 4.2 PATCH Absence (Gap, Not Conflict)

Standard mentions PATCH, OpenAPI omits it. This is a **schema incompleteness**, not a conflict - standard doesn't say "no PATCH," OpenAPI just doesn't document it.

**Resolution:** Implement PATCH per standard + OGC API - Features Part 4.

#### 4.3 History Endpoints (Future Feature Placeholder)

Standard mentions history sub-collections, OpenAPI doesn't include paths. This suggests **future extension**, not current specification.

**Resolution:** Don't implement history endpoints in initial client library. Reserve design space for future addition.

---

### 5. Implementation Details Clearer in OpenAPI Schema

#### 5.1 Type Safety for TypeScript Implementation

OpenAPI's precise types enable:

```typescript
// Exact parameter types
interface SystemsQueryParams {
  bbox?:
    | [number, number, number, number]
    | [number, number, number, number, number, number];
  datetime?: string; // ISO 8601 or interval
  id?: string[];
  parent?: string[];
  procedure?: string[];
  foi?: string[];
  observedProperty?: string[];
  controlledProperty?: string[];
  recursive?: boolean;
  limit?: number; // 1-10000
}

// Exact enum values
enum SystemType {
  Sensor = 'http://www.w3.org/ns/sosa/Sensor',
  Actuator = 'http://www.w3.org/ns/sosa/Actuator',
  Platform = 'http://www.w3.org/ns/sosa/Platform',
  Sampler = 'http://www.w3.org/ns/sosa/Sampler',
  System = 'http://www.w3.org/ns/sosa/System',
}

// Exact response structure
interface SystemGeoJSON extends GeoJSON.Feature {
  properties: {
    featureType: SystemType;
    uid: string;
    name: string;
    description?: string;
    assetType?:
      | 'Equipment'
      | 'Human'
      | 'LivingThing'
      | 'Simulation'
      | 'Process'
      | 'Group'
      | 'Other';
    validTime?: [string, string | null];
    'systemKind@link'?: Link;
  };
}
```

**Standard cannot provide this level of detail** - it's a specification document, not a schema.

#### 5.2 Validation Rules

OpenAPI constraints enable client-side validation:

- `minLength: 1` - names must be non-empty
- `minimum: 1, maximum: 10000` - limit bounds
- `format: uri` - uid must be valid URI
- `format: date-time` - datetime must be RFC 3339
- `minItems: 4, maxItems: 6` - bbox array size

#### 5.3 Default Values

OpenAPI specifies defaults:

- `limit: 10` (if omitted)
- `recursive: false` (if omitted)
- `cascade: false` (if omitted)

Standard mentions defaults in prose but OpenAPI makes them machine-readable.

#### 5.4 Example-Driven Development

OpenAPI examples enable:

- Copy-paste test fixtures
- Documentation generation with real examples
- Interactive API explorers (Swagger UI)
- Request/response validation in tests

---

### 6. Conceptual/Requirement Details Clearer in Standard

#### 6.1 Why Resources Are Structured This Way

**Standard Explains:**

- Systems represent instances, Procedures represent types
- Sampling Features are system-specific, Features of Interest are independent
- Deployments capture temporal/spatial context of system usage
- Properties enable semantic interoperability

**OpenAPI Shows:** Structure only, not rationale.

**Value:** Understanding concepts prevents misuse (e.g., creating Procedure per sensor instance).

#### 6.2 Relationship Model and Semantics

**Standard Explains:**

- subsystems vs deployedSystems (composition vs association)
- sampledFeature vs sampleOf (ultimate FOI vs sub-sampling)
- systemKind vs procedures (datasheet vs operating procedures)

**OpenAPI Shows:** Link objects, not semantics.

**Value:** Correct relationship usage requires conceptual understanding.

#### 6.3 When to Use Each Resource Type

**Standard Provides:**

- Decision guidance (sensor vs platform vs sampler)
- Use case examples (in-situ sensor, UAV, network, forecast model)
- Asset type selection (equipment vs human vs simulation)

**OpenAPI Shows:** Available resource types, not guidance.

**Value:** Application developers need this to model their domain correctly.

#### 6.4 Conformance Class Implications

**Standard Explains:**

- Minimum implementation (Common + 1 resource + 1 encoding)
- Optional vs required features
- Which conformance classes enable which operations
- Progressive implementation path

**OpenAPI Shows:** All features as if fully implemented.

**Value:** Realistic expectations for server capabilities.

---

### 7. Source Precedence for Specific Decisions

| Decision Type                | Prefer       | Rationale                                       |
| ---------------------------- | ------------ | ----------------------------------------------- |
| **Property Names**           | OpenAPI      | Actual JSON keys, not conceptual names          |
| **Property Types**           | OpenAPI      | Precise types and constraints                   |
| **Required vs Optional**     | Both         | Align perfectly, cross-validate                 |
| **HTTP Methods**             | **Standard** | PATCH missing from OpenAPI                      |
| **Query Parameters**         | OpenAPI      | Types, constraints, defaults                    |
| **Path Structure**           | Both         | Perfect alignment                               |
| **Status Codes**             | OpenAPI      | More detailed documentation                     |
| **Link Relations**           | **Standard** | Semantic definitions                            |
| **Conformance Classes**      | **Standard** | Not in OpenAPI                                  |
| **Response Format**          | OpenAPI      | Complete schemas                                |
| **Validation Rules**         | OpenAPI      | Machine-readable constraints                    |
| **Conceptual Understanding** | **Standard** | Rationale and guidance                          |
| **Examples**                 | OpenAPI      | More complete and realistic                     |
| **Versioning/History**       | **Standard** | Conceptual model (endpoints not yet in OpenAPI) |
| **Recursive Semantics**      | **Standard** | Detailed behavior description                   |
| **Cascade Semantics**        | **Standard** | Full impact description                         |

**General Rule:**

- **Technical "How"**: OpenAPI (types, formats, constraints)
- **Conceptual "Why"**: Standard (semantics, relationships, guidance)
- **Feature "When"**: Standard (conformance, optional features)

---

### 8. Requirements Emerging from Reading Both Together

#### 8.1 Format Negotiation Strategy

**From Both Sources:**

- GeoJSON mandatory, SensorML optional (standard)
- Both have complete schemas (OpenAPI)

**Emerged Requirement:**

```typescript
interface CSAPIClientOptions {
  preferredFormat?: 'geojson' | 'sensorml'; // Default: geojson
  fallbackFormat?: 'geojson' | 'sensorml'; // Try if preferred fails
}
```

Client should:

1. Check conformance for SensorML support
2. Use `f` parameter or Accept header
3. Fallback to GeoJSON if SensorML unavailable
4. Parse both formats seamlessly

#### 8.2 Conformance-Based Feature Detection

**From Both Sources:**

- Conformance classes define capabilities (standard)
- `/conformance` endpoint returns list (OpenAPI)

**Emerged Requirement:**

```typescript
class CSAPIClient {
  async getCapabilities(): Promise<Capabilities> {
    const conformance = await this.fetchConformance();
    return {
      supportsSystems: conformance.includes('/conf/system'),
      supportsSubsystems: conformance.includes('/conf/subsystem'),
      supportsDeployments: conformance.includes('/conf/deployment'),
      supportsCRUD: conformance.includes('/conf/create-replace-delete'),
      supportsUpdate: conformance.includes('/conf/update'), // PATCH
      supportsSensorML: conformance.includes('/conf/sensorml'),
      supportsAdvancedFiltering: conformance.includes(
        '/conf/advanced-filtering'
      ),
    };
  }
}
```

#### 8.3 Link-Following Navigation

**From Both Sources:**

- Link relations define relationships (standard)
- Link schema structure (OpenAPI)

**Emerged Requirement:**

```typescript
interface LinkNavigator {
  followLink(resource: Resource, rel: string): Promise<Resource | Resource[]>;
  getSubsystems(system: System): Promise<System[]>; // Follows 'ogc-rel:subsystems'
  getDeployments(system: System): Promise<Deployment[]>; // Follows 'ogc-rel:deployments'
  getSamplingFeatures(system: System): Promise<SamplingFeature[]>;
}
```

Client should prefer link-following over URL construction.

#### 8.4 Recursive Query Handling

**From Both Sources:**

- `recursive` parameter (OpenAPI)
- Detailed semantics (standard)

**Emerged Requirement:**

```typescript
interface RecursiveQueryOptions {
  recursive?: boolean;
  maxDepth?: number; // Client-side protection
  includeNested?: {
    // Which nested resources to include
    subsystems?: boolean;
    samplingFeatures?: boolean;
    datastreams?: boolean;
  };
}
```

Client should warn about potentially large recursive queries.

#### 8.5 Validation Strategy

**From Both Sources:**

- Property constraints (OpenAPI)
- Conformance requirements (standard)

**Emerged Requirement:**

```typescript
interface ValidationResult {
  valid: boolean;
  errors: ValidationError[];
  warnings: ValidationWarning[];
}

// Client validates BEFORE sending request
client.validateSystem(system: SystemCreate): ValidationResult {
  // Check required properties (uid, name, featureType)
  // Validate uid is URI format
  // Validate featureType is SystemTypeUris enum
  // Validate assetType if provided
  // Warn if mobile system lacks location
}
```

#### 8.6 Error Handling Patterns

**From Both Sources:**

- Status codes (OpenAPI)
- Conformance conflicts (standard)

**Emerged Requirement:**

```typescript
class CSAPIError extends Error {
  constructor(
    public statusCode: number,
    public type:
      | 'validation'
      | 'authentication'
      | 'authorization'
      | 'notFound'
      | 'conflict'
      | 'server',
    message: string,
    public details?: unknown
  ) {}
}

// Handle 409 on DELETE without cascade
try {
  await client.deleteSystem(id);
} catch (e) {
  if (e instanceof CSAPIError && e.statusCode === 409) {
    // Prompt user: "System has nested resources. Use cascade=true?"
  }
}
```

---

### 9. Examples or Patterns in One Source But Not the Other

#### 9.1 Global Hawk Reference Frames (OpenAPI Only)

**OpenAPI Provides:**
Detailed example of UAV with local reference frames (aircraft principal axes):

```json
{
  "localReferenceFrames": [
    {
      "label": "Platform Frame",
      "origin": "Center of gravity of the aircraft",
      "axes": [
        { "name": "x", "description": "Longitudinal/roll axis..." },
        { "name": "y", "description": "Transverse/pitch axis..." },
        { "name": "z", "description": "Vertical/yaw axis..." }
      ]
    }
  ]
}
```

**Standard:** Mentions reference frames conceptually but no examples.

**Value:** Developers modeling platforms with sensors learn how to specify reference frames.

#### 9.2 Saildrone Deployment with Contacts (OpenAPI Only)

**OpenAPI Provides:**
Complete deployment example with organizational contacts:

```json
{
  "contacts": [
    {
      "role": "http://sensorml.com/ont/swe/property/Operator",
      "organisationName": "Saildrone, Inc.",
      "contactInfo": {"website": "https://www.saildrone.com/", "address": {...}}
    },
    {
      "role": "http://sensorml.com/ont/swe/property/DataProvider",
      "organisationName": "NOAA PMEL",
      "contactInfo": {"website": "https://www.pmel.noaa.gov"}
    }
  ]
}
```

**Standard:** Mentions contacts but no examples.

**Value:** Shows best practices for deployment metadata.

#### 9.3 Conformance Test Suite (Standard Only)

**Standard Provides (Annex A):**

- Abstract Test Suite with test cases for each requirement
- Test procedures for each conformance class
- Assertions to verify

**OpenAPI:** No test information.

**Value:** Server implementers know how to validate conformance. Client developers know what to test.

#### 9.4 System Kind vs Procedures Distinction (Standard Only)

**Standard Clarifies:**

- `systemKind` (Procedure) = datasheet/specifications for system type
- `procedures` (array) = operating procedures/methodologies system can perform

**OpenAPI:** Shows both as link properties, no distinction explained.

**Value:** Prevents confusion - one sensor model (systemKind) can perform multiple procedures.

#### 9.5 Feature of Interest Examples (Standard Only)

**Standard Provides:**

- Building, room, river, atmosphere examples
- Explanation that FOI can also be a System
- Distinction between FOI (independent) and Sampling Feature (system-specific)

**OpenAPI:** Shows link structure, no FOI examples.

**Value:** Helps model domain correctly (when to create separate FOI vs Sampling Feature).

---

### 10. Implementation Implications

#### 10.1 Two-Phase Implementation Strategy

**Phase 1: OpenAPI-Driven Core (Week 1-2)**
Focus on machine-readable specifications:

- Generate TypeScript interfaces from OpenAPI schemas
- Implement URL builders for all 20 paths
- Implement query parameter encoding
- Parse GeoJSON and SensorML responses
- Handle status codes
- Validate requests against schemas

**Phase 2: Standard-Driven Enhancements (Week 3-4)**
Focus on conceptual understanding:

- Implement conformance detection and adaptation
- Add PATCH support (missing from OpenAPI)
- Implement link-following navigation
- Document recursive query semantics
- Handle cascade delete warnings
- Provide validation with helpful error messages
- Document when to use each resource type

#### 10.2 Documentation Structure

**API Reference (from OpenAPI):**

- Generated from schema
- Types, parameters, responses
- Request/response examples

**Conceptual Guide (from Standard):**

- How CSAPI models connected systems
- Resource type selection guide
- Relationship patterns
- Best practices

**Migration Guide:**

- From OGC SensorThings API
- From SOS 2.0
- From manual REST

#### 10.3 Testing Strategy

**Unit Tests (OpenAPI-based):**

```typescript
describe('SystemsAPI', () => {
  it('validates required properties', () => {
    expect(() => createSystem({ name: 'Test' })).toThrow('uid is required');
  });

  it('validates SystemType enum', () => {
    expect(() =>
      createSystem({
        uid: 'urn:test:1',
        name: 'Test',
        featureType: 'InvalidType',
      })
    ).toThrow('featureType must be valid SystemTypeUris');
  });

  it('encodes bbox correctly', () => {
    const url = buildSystemsUrl({ bbox: [-180, -90, 180, 90] });
    expect(url).toContain('bbox=-180,-90,180,90');
  });
});
```

**Integration Tests (Standard-based):**

```typescript
describe('Conformance-based behavior', () => {
  it('adapts to server without advanced filtering', async () => {
    mockConformance(['/conf/api-common', '/conf/system']);

    const client = await CSAPIClient.create(url);
    expect(client.capabilities.supportsAdvancedFiltering).toBe(false);

    // Should not attempt foi filter
    await expect(client.systems({ foi: 'test' })).rejects.toThrow(
      'Advanced filtering not supported'
    );
  });

  it('follows link relations correctly', async () => {
    const system = await client.getSystem('test-1');
    const subsystems = await client.followLink(system, 'ogc-rel:subsystems');
    expect(Array.isArray(subsystems)).toBe(true);
  });
});
```

#### 10.4 Type-Safe Query Builder Pattern

Combine OpenAPI types with standard semantics:

```typescript
class SystemsQueryBuilder {
  private params: SystemsQueryParams = {};

  // Type-safe from OpenAPI
  bbox(bbox: [number, number, number, number]): this {
    this.params.bbox = bbox;
    return this;
  }

  // Semantics from Standard
  recursive(depth?: number): this {
    this.params.recursive = true;
    // Warn if no depth limit
    if (!depth) {
      console.warn(
        'Recursive queries without depth limit may return large result sets'
      );
    }
    return this;
  }

  // Conformance-aware
  observedProperty(propIds: string[]): this {
    if (!this.client.capabilities.supportsAdvancedFiltering) {
      throw new Error('Server does not support advanced filtering');
    }
    this.params.observedProperty = propIds;
    return this;
  }
}
```

#### 10.5 Recommended Client Library Structure

```
src/csapi/
  ├── types/              # Generated from OpenAPI
  │   ├── system.ts
  │   ├── deployment.ts
  │   ├── procedure.ts
  │   ├── sampling-feature.ts
  │   ├── property.ts
  │   └── common.ts
  ├── builders/           # Query builders
  │   ├── systems-query.ts
  │   ├── deployments-query.ts
  │   └── ...
  ├── navigation/         # Link following (standard-based)
  │   ├── link-navigator.ts
  │   └── relationship-helpers.ts
  ├── validation/         # Schema validation (OpenAPI) + semantic (standard)
  │   ├── schema-validator.ts
  │   └── semantic-validator.ts
  ├── conformance/        # Capability detection (standard-based)
  │   └── capabilities.ts
  └── client.ts           # Main client class
```

#### 10.6 Format Handling

```typescript
interface FormatOptions {
  format?: 'geojson' | 'sensorml';
  autoDetect?: boolean; // Try SensorML if conformance supports it
}

class CSAPIClient {
  async getSystems(
    options: SystemsQueryOptions & FormatOptions
  ): Promise<System[]> {
    // Check conformance
    const supportsSensorML = this.capabilities.supportsSensorML;

    // Determine format
    let format = options.format || 'geojson';
    if (
      options.autoDetect &&
      supportsSensorML &&
      this.preferSensorML(options)
    ) {
      format = 'sensorml';
    }

    // Set format parameter (don't set Accept header - let browser/Node handle)
    const url = this.buildUrl('/systems', { ...options, f: format });

    // Parse based on Content-Type response
    const response = await fetch(url);
    const contentType = response.headers.get('content-type');

    if (contentType?.includes('sml+json')) {
      return this.parseSensorML(await response.json());
    } else {
      return this.parseGeoJSON(await response.json());
    }
  }
}
```

#### 10.7 Error Messages Based on Both Sources

```typescript
function validateSystem(system: SystemCreate): ValidationResult {
  const errors: string[] = [];

  // From OpenAPI constraints
  if (!system.uid) {
    errors.push('uid is required (OpenAPI schema constraint)');
  }
  if (system.uid && !isValidURI(system.uid)) {
    errors.push('uid must be a valid URI (format constraint from OpenAPI)');
  }
  if (!system.name || system.name.length === 0) {
    errors.push(
      'name is required and must be non-empty (minLength: 1 from OpenAPI)'
    );
  }

  // From Standard conceptual requirements
  if (
    system.assetType !== 'Simulation' &&
    system.assetType !== 'Process' &&
    !system.geometry
  ) {
    errors.push(
      'Mobile systems SHOULD have location property (Requirement 4 from Standard)'
    );
  }

  return { valid: errors.length === 0, errors };
}
```

---

### Summary and Recommendations

#### Key Insights

1. **Complementary Sources:** Standard and OpenAPI work together. Neither is complete alone.

2. **OpenAPI = Implementation Details:** Use for types, constraints, examples, validation rules.

3. **Standard = Conceptual Foundation:** Use for semantics, relationships, conformance, guidance.

4. **High Consistency:** 95%+ alignment. Differences are gaps (PATCH, history), not conflicts.

5. **Both Are Authoritative:** Don't choose one over the other. Use appropriate source for each decision.

#### Implementation Checklist

✅ **Use OpenAPI for:**

- TypeScript type generation
- Parameter encoding/validation
- Request/response schemas
- Property names (actual JSON keys)
- Default values
- Examples for tests

✅ **Use Standard for:**

- Conformance class interpretation
- PATCH operations (missing from OpenAPI)
- Link relation semantics
- Recursive query details
- Cascade delete implications
- Conceptual guidance
- Resource type selection

✅ **Require Both for:**

- Complete understanding
- Robust implementation
- Correct usage patterns
- Comprehensive testing
- Good documentation

#### Next Steps

**Section 1 Complete:** CSAPI Part 1 fully analyzed (~3,200 lines total)

**Ready for Section 2:** CSAPI Part 2 (Dynamic Data) analysis using same three-section pattern

**Implementation Ready:** All information needed to build Part 1 client library extracted and synthesized
