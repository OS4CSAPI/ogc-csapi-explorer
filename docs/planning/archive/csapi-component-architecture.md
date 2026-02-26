# CSAPI Client Library: What We're Building

**Purpose:** This document describes every component we need to implement CSAPI support in the Camptocamp OGC Client Library, explaining which components extend existing code versus which require building new code from scratch.

**Date:** February 2, 2026

---

## Main Component: Unified OGC API Access

The Camptocamp OGC Client Library uses the `OgcApiEndpoint` class as the main component for all OGC API standards. Developers use this same class to interact with CSAPI servers by pointing it at a CSAPI-compliant endpoint. The `OgcApiEndpoint` automatically detects CSAPI capabilities by checking the server's conformance classes and exposes the appropriate methods for working with sensors, observations, and control streams with COMPLETE query, filtering, and pagination support - NOT MVP Scope. This unified approach means developers don't need to learn different APIs for different OGC standards - they use the same patterns whether accessing Features, Tiles, Records, EDR, or CSAPI data with full access to all query parameters, all filtering capabilities (spatial, temporal, hierarchical, relationship-based, property-based, full-text), and both pagination modes (offset-based and cursor-based for high-volume data). The CSAPI implementation extends `OgcApiEndpoint` following the exact same pattern already established for EDR support, providing developers with comprehensive access to all CSAPI capabilities through a familiar, consistent interface.

---

## Service Discovery Components

### Conformance Reader: Extending Existing Capability Detection

The conformance reader is existing code in `OgcApiEndpoint` that checks which OGC API standards a server implements by reading its conformance document. For CSAPI support, we will extend this reader by adding new conformance class checks that detect CSAPI Part 1 (Systems, Deployments, Procedures, Sampling Features, Properties) and Part 2 (DataStreams, Observations, Control Streams, Commands) capabilities. This follows the exact pattern already used for EDR detection - adding a `hasConnectedSystems` method similar to the existing `hasEnvironmentalDataRetrieval` method. The extension integrates seamlessly into the upstream repository's architecture without breaking existing functionality for Features, Tiles, Records, or EDR. This approach aligns with the project goal of making CSAPI support feel like a natural part of the existing library rather than a bolt-on addition.

**CSAPI Conformance Classes to Detect:**

- Part 1 Core: `http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/req/core`
- Part 1 Systems: `http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/req/system`
- Part 1 Deployments: `http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/req/deployment`
- Part 1 Procedures: `http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/req/procedure`
- Part 1 Sampling Features: `http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/req/samplingFeature`
- Part 1 Properties: `http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/req/property`
- Part 2 DataStreams: `http://www.opengis.net/spec/ogcapi-connectedsystems-2/1.0/req/datastream`
- Part 2 Observations: `http://www.opengis.net/spec/ogcapi-connectedsystems-2/1.0/req/observation`
- Part 2 Control Streams: `http://www.opengis.net/spec/ogcapi-connectedsystems-2/1.0/req/controlstream`
- Part 2 Commands: `http://www.opengis.net/spec/ogcapi-connectedsystems-2/1.0/req/command`

**Recommended Development Workflow:**

1. Write method signature for new conformance detection methods
2. Add JSDoc comments with description, return types, examples
3. Implement the detection logic
4. Write tests verifying conformance class detection
5. Update as you go - don't defer documentation to later

**Implementation Type:** EXTENDING EXISTING CODE

---

### Collections Reader: Extending Metadata Parsing

The collections reader is existing code that fetches and parses the `/collections` endpoint to discover what data is available on a server. For CSAPI, we will extend this parser to recognize and extract CSAPI-specific metadata that indicates whether a collection contains Systems, DataStreams, Observations, or other CSAPI resources. This is primarily an extension of existing parsing logic rather than building something entirely new - we're adding new properties to the collection info objects and new filter methods like `csapiSystemCollections`, `csapiDataStreamCollections`, and `csapiObservationCollections` alongside the existing `featureCollections` and `edrCollections` getters. The extension reuses the upstream repository's established patterns for handling different resource types within the unified collections framework. This approach supports the project goal of providing developers a consistent experience across all OGC API standards through one endpoint class.

**CSAPI Collection Properties to Parse:**

- `featureType` property indicating resource type (e.g., `sosa:System`, `sosa:Deployment`, `sosa:ObservationCollection`)
- Links to CSAPI-specific operations (create, update, delete, schema endpoints for Part 2 resources)
- Temporal extent for observation collections
- Spatial extent for systems and deployment collections
- ALL available query parameters and COMPLETE filtering capabilities (spatial: bbox 2D/3D; temporal: datetime, phenomenonTime, resultTime, executionTime, issueTime with all ISO 8601 interval types; hierarchical: recursive; relationship: parent, system, deployment, procedure, foi, observedProperty, controlledProperty, baseProperty, objectType; common: id, uid, q, property filters; pagination: limit 1-10000, offset, cursor)
- Supported formats (GeoJSON, SensorML 3.0, SWE Common 3.0 JSON/Text/Binary)
- Pagination modes (offset-based and cursor-based for high-volume observations and commands)
- Schema information (DataStream/ControlStream schema availability)

**Recommended Development Workflow:**

1. Write method signature for new collection filter methods
2. Add JSDoc comments documenting parameters, return types, filter behavior
3. Implement the parsing and filtering logic
4. Write tests with sample collection metadata
5. Document as you code to maintain clarity on CSAPI-specific metadata

**Implementation Type:** EXTENDING EXISTING CODE

---

### OgcApiEndpoint Integration: Extending Main Endpoint Class

The OgcApiEndpoint integration adds the CSAPI factory method to the main `OgcApiEndpoint` class following the exact pattern established by EDR support (PR #114). This integration adds approximately 35 lines to `src/ogc-api/endpoint.ts` to expose CSAPI functionality through a single developer-facing method. Developers access all CSAPI capabilities through `endpoint.csapi(collectionId)` which returns a `CSAPIQueryBuilder` instance containing all URL-building methods for the 9 CSAPI resource types. The factory method includes conformance checking (`hasConnectedSystems`), collection metadata fetching, QueryBuilder instantiation, and caching for performance. This minimal integration approach maintains the library's architecture principle of composition over inheritance - no subclassing, just a factory method that returns a specialized query builder. The integration also includes adding the `csapiCollections` getter for filtering collections that support CSAPI resources, and a private cache field for QueryBuilder instances.

**Integration Points in OgcApiEndpoint:**

**1. Import Statement (1 line):**

```typescript
import CSAPIQueryBuilder from './csapi/url_builder.js';
```

**2. Cache Field (2 lines):**

```typescript
private collection_id_to_csapi_builder_: Map<string, CSAPIQueryBuilder> = new Map();
```

**3. Collections Getter (~6 lines):**

```typescript
get csapiCollections(): Promise<string[]> {
  return Promise.all([this.data, this.hasConnectedSystems])
    .then(([data, hasCSAPI]) => (hasCSAPI ? data : { collections: [] }))
    .then(parseCollections)
    .then((collections) => collections.map((collection) => collection.name));
}
```

**4. Conformance Getter (~6 lines):**

```typescript
get hasConnectedSystems(): Promise<boolean> {
  return Promise.all([this.conformanceClasses]).then(checkHasConnectedSystems);
}
```

**5. Factory Method (~17 lines):**

```typescript
public async csapi(collection_id: string): Promise<CSAPIQueryBuilder> {
  if (!this.hasConnectedSystems) {
    throw new EndpointError('Endpoint does not support Connected Systems API');
  }
  const cache = this.collection_id_to_csapi_builder_;
  if (cache.has(collection_id)) {
    return cache.get(collection_id);
  }
  const collection = await this.getCollectionInfo(collection_id);
  const result = new CSAPIQueryBuilder(collection);
  cache.set(collection_id, result);
  return result;
}
```

**Developer Usage Pattern:**

```typescript
import { OgcApiEndpoint } from '@camptocamp/ogc-client';

const endpoint = new OgcApiEndpoint('https://server.com/api');
await endpoint.isReady();

// Check if endpoint supports CSAPI
if (await endpoint.hasConnectedSystems) {
  // Get CSAPI query builder for a collection
  const csapi = await endpoint.csapi('sensors-collection');

  // Use builder methods to construct URLs for all 9 resource types
  const systemsUrl = csapi.getSystems({ bbox: [...], recursive: true });
  const observationsUrl = csapi.getObservations(datastreamId, { phenomenonTime: '2024-01-01/..' });
}
```

**Recommended Development Workflow:**

1. Write method signatures for factory method and getters
2. Add comprehensive JSDoc documenting conformance checking, caching, and usage pattern
3. Implement integration following EDR pattern exactly
4. Write tests verifying conformance detection, factory method, caching behavior
5. Document the ~35 line diff to endpoint.ts as you implement

**Implementation Type:** EXTENDING EXISTING CODE

---

### CSAPIQueryBuilder: Building New Query Construction Class

The CSAPIQueryBuilder is new code we need to build as a single comprehensive class containing URL-building methods for all 9 CSAPI resource types, following the pattern established by the existing `EDRQueryBuilder` class. This QueryBuilder class is instantiated by the `OgcApiEndpoint.csapi()` factory method and provides developers with all the methods needed to construct URLs for CSAPI operations: querying Systems with spatial/temporal filters, creating Observations in DataStreams, retrieving historical observations with temporal ranges, sending Commands to Control Streams, and accessing all other CSAPI resources. The class consolidates URL construction for approximately 60-70 unique URL patterns across Part 1 resources (Systems, Deployments, Procedures, Sampling Features, Properties) and Part 2 resources (DataStreams, Observations, Control Streams, Commands), including canonical endpoints, nested resource endpoints, schema endpoints, and special-purpose endpoints like command status/result tracking. This single-class design follows the upstream repository's architecture pattern where one QueryBuilder per API family handles all URL construction for that API, keeping the implementation focused and maintainable rather than splitting across multiple handler classes. The following sections detail the URL construction requirements for each of the 9 resource types as methods within this one CSAPIQueryBuilder class.

**URL Construction Requirements:**

- Canonical resource endpoints: `/systems`, `/deployments`, `/procedures`, `/samplingFeatures`, `/properties`, `/datastreams`, `/observations`, `/controlstreams`, `/commands`
- Nested resource endpoints: `/systems/{id}/subsystems`, `/systems/{id}/datastreams`, `/datastreams/{id}/observations`, `/controlstreams/{id}/commands`
- Schema endpoints: `/datastreams/{id}/schema`, `/controlstreams/{id}/schema`
- Bulk operations: POST with arrays of observations or commands
- Command status/result endpoints: `/commands/{id}/status`, `/commands/{id}/result`

**Complete Query Parameter Support:**

This URL builder implements FULL query parameter support for CSAPI Parts 1 and 2, including all standard OGC API parameters and all CSAPI-specific extensions. This is NOT an MVP - we support the complete filtering and pagination capabilities defined in the CSAPI specifications.

**Standard OGC API Parameters:**

- `bbox`: Spatial bounding box filter (2D and 3D) for Systems, Deployments, Sampling Features
- `datetime`: Temporal filter using ISO 8601 intervals for validTime filtering
- `limit`: Maximum results per page (1 to 10,000 for Part 2)
- `offset`: Skip N results for pagination
- `f`: Format negotiation (json, geojson, sml+json, swe+json, swe+text)

**CSAPI Common Parameters (Part 1):**

- `id`: Filter by resource ID (multiple IDs supported as comma-separated list)
- `uid`: Filter by unique identifier (URN-based filtering)
- `q`: Full-text search across resource properties
- `{propertyName}`: Filter by any resource property (e.g., `name=Weather%20Station`, `systemType=sosa:Sensor`)

**CSAPI Hierarchical Parameters:**

- `recursive`: Boolean flag for hierarchical queries (subsystems, subdeployments)
  - `recursive=false`: Direct children only (default)
  - `recursive=true`: All descendants at all nesting levels

**CSAPI Relationship Parameters (Part 1):**

- `parent`: Filter by parent system/deployment ID
- `procedure`: Filter resources by associated procedure
- `foi`: Filter by feature of interest
- `observedProperty`: Filter by observed property URI
- `controlledProperty`: Filter by controlled property URI
- `system`: Filter resources by associated system
- `baseProperty`: Filter properties by base property (hierarchy)
- `objectType`: Filter by resource type

**CSAPI Temporal Parameters (Part 2):**

- `phenomenonTime`: When observation was made (ISO 8601 interval, primary temporal filter for observations)
- `resultTime`: When observation result became available
- `executionTime`: When command should be/was executed
- `issueTime`: When command was issued

**Pagination Modes:**

- **Offset-based** (Part 1): `limit` + `offset` for predictable page navigation
- **Cursor-based** (Part 2): `limit` + `cursor` for efficient large dataset streaming
- **Temporal windowing** (Part 2): `phenomenonTime` intervals for time-series data

**Advanced Filtering Capabilities:**

- **Multiple ID filtering**: `id=sys1,sys2,sys3` (OR logic)
- **Property-based filtering**: Any resource property can be used as query parameter
- **Combined filters**: All parameters can be combined (AND logic between different parameter types)
- **Nested endpoint filtering**: All query parameters work on nested endpoints (e.g., `/systems/{id}/subsystems?bbox=...&recursive=true`)

**Format Negotiation:**

- Query parameter: `f=json|geojson|sml+json|swe+json|swe+text|html`
- HTTP Accept header: `application/json`, `application/geo+json`, `application/sml+json`, `application/swe+json`, `application/swe+text`
- Format-specific parameters for Part 2: `obsFormat` (observation encoding), `cmdFormat` (command encoding)

**Recommended Development Workflow:**

1. Write method signatures for each URL construction method (buildSystemsURL, etc.)
2. Add comprehensive JSDoc with all parameters, examples of constructed URLs
3. Implement URL construction and parameter encoding
4. Write tests for each endpoint and parameter combination
5. Document edge cases and parameter validation rules as you discover them

**Implementation Type:** BUILDING NEW CODE (following EDRQueryBuilder pattern)

---

#### Systems Resource Methods

The CSAPIQueryBuilder includes Systems resource methods to manage CSAPI System resources, representing sensors, actuators, platforms, samplers, and other observing systems. These methods implement all CRUD operations (Create, Read, Update, Delete) for Systems at both canonical endpoints (`/systems`, `/systems/{id}`) and nested endpoints (`/systems/{parentId}/subsystems`). Systems are the core resource in CSAPI Part 1, serving as the entry point for discovering available sensors and their relationships to deployments, procedures, sampling features, and observation streams. The methods support hierarchical queries (recursive subsystem traversal), relationship filtering (query by deployment, procedure, or sampling feature), spatial filtering (bbox), temporal filtering (validTime), and both GeoJSON and SensorML format parsing. This functionality connects to the URL builder for query construction, the format handlers for parsing responses, and the validator for checking system constraints. It represents significant functionality with complex relationship management and hierarchical navigation.

**Operations to Implement:**

**Read Operations:**

- List all systems: `GET /systems`
- Get single system: `GET /systems/{id}`
- Query systems: `GET /systems?bbox=...&parent=...&recursive=true`
- List subsystems: `GET /systems/{parentId}/subsystems`
- Recursive subsystem query: `GET /systems/{parentId}/subsystems?recursive=true`
- Systems by deployment: `GET /systems?deployment={deploymentId}`
- Systems by procedure: `GET /systems?procedure={procedureId}`
- Systems in collection: `GET /collections/{collectionId}/items?featureType=sosa:System`

**Create Operations:**

- Create system: `POST /systems` with GeoJSON or SensorML body
- Create subsystem: `POST /systems/{parentId}/subsystems` with body
- Add to collection: `POST /collections/{collectionId}/items` with system feature

**Update Operations:**

- Replace system: `PUT /systems/{id}` with full document
- Partial update: `PATCH /systems/{id}` with partial document (JSON Patch or Merge Patch)

**Delete Operations:**

- Delete system: `DELETE /systems/{id}`
- Cascade delete: `DELETE /systems/{id}?cascade=true` (deletes subsystems, datastreams, etc.)

**System Relationship Management:**

- Parse and expose subsystem hierarchy
- Navigate system-deployment associations (bidirectional)
- Navigate system-procedure associations
- Navigate system-sampling feature associations
- Navigate system-datastream associations (Part 2)
- Navigate system-controlstream associations (Part 2)

**Complete Query and Filtering Support:**

These methods implement FULL query parameter support - NOT MVP scope. All filtering and pagination capabilities from the CSAPI specification are supported.

- **Spatial filtering**: `bbox` parameter (2D and 3D bounding boxes)
- **Temporal filtering**: `datetime` parameter for validTime filtering (ISO 8601 intervals: instant, closed interval, open start, open end)
- **Hierarchy traversal**: `recursive` parameter (true = all descendants, false = direct children only)
- **Relationship filtering**: `parent`, `deployment`, `procedure`, `foi` parameters for association-based queries
- **ID filtering**: `id` parameter (supports comma-separated list for multiple IDs)
- **UID filtering**: `uid` parameter (URN-based unique identifier filtering)
- **Full-text search**: `q` parameter for searching across all text properties
- **Property-based filtering**: Any system property can be used as query parameter (e.g., `systemType=sosa:Sensor`, `name=Weather*`)
- **Pagination**: `limit` (1 to server maximum) and `offset` (non-negative integer) for predictable page navigation
- **Format negotiation**: `f` parameter and Accept headers for GeoJSON vs SensorML-JSON format selection
- **Combined filtering**: All query parameters work together with AND logic

**Recommended Development Workflow:**

1. Write method signatures for all CRUD and query methods
2. Add comprehensive JSDoc with parameter descriptions, return types, examples
3. Implement each method with inline documentation for complex logic
4. Write tests for each operation as you implement (CRUD, queries, navigation)
5. Document query parameter combinations and behavior
6. Add JSDoc examples for common workflows (create system, query hierarchy)

---

#### Deployments Resource Methods

The CSAPIQueryBuilder includes Deployments resource methods to manage CSAPI Deployment resources, describing where and when systems are deployed in the field. These methods implement all CRUD operations for Deployments at canonical endpoints (`/deployments`, `/deployments/{id}`) and nested endpoints (`/deployments/{parentId}/subdeployments`). Deployments connect systems to geographic locations and temporal periods, enabling queries like "what sensors were active in this region during this time period." The methods support hierarchical subdeployment queries (recursive parameter), relationship filtering (query by system), spatial filtering (bbox for deployment footprint), temporal filtering (validTime for deployment period), and GeoJSON format parsing with deployment-specific metadata. Deployments have bidirectional associations with systems - a system can have multiple deployments over time, and a deployment can involve multiple systems. This functionality manages these many-to-many relationships and provides navigation methods for traversing them.

**Operations to Implement:**

**Read Operations:**

- List all deployments: `GET /deployments`
- Get single deployment: `GET /deployments/{id}`
- Query deployments: `GET /deployments?bbox=...&system=...&datetime=...`
- List subdeployments: `GET /deployments/{parentId}/subdeployments`
- Recursive subdeployment query: `GET /deployments/{parentId}/subdeployments?recursive=true`
- Deployments by system: `GET /deployments?system={systemId}`
- Deployments in collection: `GET /collections/{collectionId}/items?featureType=sosa:Deployment`

**Create Operations:**

- Create deployment: `POST /deployments` with GeoJSON body
- Create subdeployment: `POST /deployments/{parentId}/subdeployments`
- Add to collection: `POST /collections/{collectionId}/items`

**Update Operations:**

- Replace deployment: `PUT /deployments/{id}`
- Partial update: `PATCH /deployments/{id}`

**Delete Operations:**

- Delete deployment: `DELETE /deployments/{id}`
- Cascade delete: `DELETE /deployments/{id}?cascade=true`

**Deployment Relationship Management:**

- Parse and expose subdeployment hierarchy
- Navigate deployment-system associations (many-to-many)
- Extract spatial extent (deployment footprint)
- Extract temporal extent (deployment period)
- Validate validTime periods

**Complete Query and Filtering Support:**

These methods implement FULL query parameter support - NOT MVP scope.

- **Spatial filtering**: `bbox` parameter (2D and 3D for deployment footprint/volume)
- **Temporal filtering**: `datetime` parameter for deployment validTime period filtering
- **Hierarchy traversal**: `recursive` parameter for nested subdeployments
- **Relationship filtering**: `system` parameter (deployments for specific systems), `parent` parameter
- **ID filtering**: `id` parameter (multiple IDs supported)
- **UID filtering**: `uid` parameter
- **Full-text search**: `q` parameter
- **Property-based filtering**: Any deployment property as query parameter
- **Pagination**: `limit` and `offset`
- **Format**: GeoJSON only (deployments always have spatial geometry)
- **Combined filtering**: All parameters work together

**Recommended Development Workflow:**

1. Write method signatures for CRUD and spatial/temporal query methods
2. Add JSDoc with parameter descriptions, spatial/temporal filter examples
3. Implement each operation with documentation for extent handling
4. Write tests for spatial queries, temporal queries, hierarchy
5. Document bbox and datetime parameter formats as you implement
6. Add JSDoc examples for deployment tracking workflows

---

#### Procedures Resource Methods

The CSAPIQueryBuilder includes Procedures resource methods to manage CSAPI Procedure resources, describing the methodologies, algorithms, or processes used to generate observations or control systems. These methods implement all CRUD operations for Procedures at canonical endpoints (`/procedures`, `/procedures/{id}`). Procedures can represent sensor measurement methodologies, data processing algorithms, calibration procedures, quality control processes, or sampling protocols. The methods parse both GeoJSON features (for simple procedure metadata) and SensorML process models (for detailed technical descriptions), support relationship filtering (procedures used by specific systems), and provide access to procedure documentation and parameters. Procedures are referenced by Systems (via `systemKind` or `procedure` properties) and DataStreams (via `procedure` property), connecting the "how" of data collection to the "what" (systems) and "where" (observation streams).

**Operations to Implement:**

**Read Operations:**

- List all procedures: `GET /procedures`
- Get single procedure: `GET /procedures/{id}`
- Query procedures: `GET /procedures?system=...&q=...`
- Procedures by system: `GET /procedures?system={systemId}`
- Procedures in collection: `GET /collections/{collectionId}/items?featureType=sosa:Procedure`

**Create Operations:**

- Create procedure: `POST /procedures` with GeoJSON or SensorML body
- Add to collection: `POST /collections/{collectionId}/items`

**Update Operations:**

- Replace procedure: `PUT /procedures/{id}`
- Partial update: `PATCH /procedures/{id}`

**Delete Operations:**

- Delete procedure: `DELETE /procedures/{id}`

**Procedure Properties to Parse:**

- `procedureType`: URI indicating type (sensor, algorithm, protocol)
- `methodKind`: URI from controlled vocabulary
- `attachedTo`: Link to system that uses this procedure
- `inputs`: Input parameters/requirements (from SensorML)
- `outputs`: Output specifications (from SensorML)
- `parameters`: Configuration parameters (from SensorML)
- `documentation`: Links to manuals, specifications

**Procedure Relationship Management:**

- Systems using this procedure (reverse lookup)
- DataStreams using this procedure (Part 2 cross-reference)
- Parse SensorML method descriptions
- Extract parameter definitions

**Complete Query and Filtering Support:**

These methods implement FULL query parameter support - NOT MVP scope.

- **Relationship filtering**: `system` parameter (procedures used by specific systems)
- **Full-text search**: `q` parameter for searching procedure names, descriptions, methodology details
- **ID filtering**: `id` parameter (multiple procedure IDs)
- **UID filtering**: `uid` parameter
- **Property-based filtering**: Any procedure property (e.g., `procedureType=sosa:SensingProcedure`, `methodKind=observation`)
- **Pagination**: `limit` and `offset` for paging through procedure catalogs
- **Format negotiation**: `f` parameter and Accept headers for GeoJSON vs SensorML-JSON format selection
- **Combined filtering**: All parameters work together

**Recommended Development Workflow:**

1. Write method signatures for read operations and query methods
2. Add JSDoc documenting SensorML integration, system associations
3. Implement read and query logic with format negotiation
4. Write tests for GeoJSON and SensorML parsing
5. Document procedure type filtering and relationship queries
6. Add JSDoc examples showing procedure discovery workflows

---

#### Sampling Features Resource Methods

The CSAPIQueryBuilder includes Sampling Features resource methods to manage CSAPI Sampling Feature resources, representing the features being observed or sampled by systems. These methods implement all CRUD operations for Sampling Features at canonical endpoints (`/samplingFeatures`, `/samplingFeatures/{id}`) and nested endpoints (`/systems/{systemId}/samplingFeatures` for system-specific sampling features). Sampling Features answer "what is being observed?" - they can be physical locations (weather station site), spatial regions (forest plot), physical samples (water sample, core sample), or abstract features (administrative boundary). The methods support spatial queries (bbox for sampling location), relationship queries (sampling features for specific systems or sampled features), hierarchical relationships (related sampling features), and GeoJSON format parsing with sampling feature metadata. Sampling Features connect systems to the ultimate features of interest through the sampling relationship chain.

**Operations to Implement:**

**Read Operations:**

- List all sampling features: `GET /samplingFeatures`
- Get single sampling feature: `GET /samplingFeatures/{id}`
- Query sampling features: `GET /samplingFeatures?bbox=...&foi=...&system=...`
- System-specific sampling features: `GET /systems/{systemId}/samplingFeatures`
- Sampling features by feature of interest: `GET /samplingFeatures?foi={featureId}`
- Sampling features in collection: `GET /collections/{collectionId}/items?featureType=sosa:SamplingFeature`

**Create Operations:**

- Create sampling feature: `POST /samplingFeatures` with GeoJSON body
- Create under system: `POST /systems/{systemId}/samplingFeatures`
- Add to collection: `POST /collections/{collectionId}/items`

**Update Operations:**

- Replace sampling feature: `PUT /samplingFeatures/{id}`
- Partial update: `PATCH /samplingFeatures/{id}`

**Delete Operations:**

- Delete sampling feature: `DELETE /samplingFeatures/{id}`

**Sampling Feature Properties to Parse:**

- `samplingFeatureType`: URI indicating type (point, specimen, transect)
- `sampledFeature`: Link to ultimate feature of interest
- `relatedSamplingFeature`: Links to related sampling features
- `hostedProcedure`: Procedures performed at this location
- `shape`: Geometry (point, line, polygon) of sampling location
- `samplingMethod`: How sample was collected

**Sampling Feature Relationship Management:**

- Systems using this sampling feature
- Ultimate feature of interest (sampled feature)
- Related sampling features (hierarchical relationships)
- Observations at this sampling feature (Part 2)

**Complete Query and Filtering Support:**

These methods implement FULL query parameter support - NOT MVP scope.

- **Spatial filtering**: `bbox` parameter (2D and 3D for sampling location/volume)
- **Relationship filtering**: `system` (sampling features for specific systems), `foi` (by feature of interest), `relatedSamplingFeature` (related features)
- **ID filtering**: `id` parameter (multiple sampling feature IDs)
- **UID filtering**: `uid` parameter
- **Full-text search**: `q` parameter across all text properties
- **Property-based filtering**: Any sampling feature property (e.g., `samplingFeatureType=SF_SamplingPoint`, `samplingMethod=grab`)
- **Pagination**: `limit` and `offset`
- **Format**: GeoJSON (sampling features always have spatial geometry)
- **Combined filtering**: All parameters work together

**Recommended Development Workflow:**

1. Write method signatures for CRUD and spatial query methods
2. Add JSDoc with geometry types, relationship parameters, examples
3. Implement operations with spatial filter handling
4. Write tests for different geometry types and spatial queries
5. Document sampling feature relationships as you implement
6. Add JSDoc examples for feature-of-interest workflows

---

#### Properties Resource Methods

The CSAPIQueryBuilder includes Properties resource methods to manage CSAPI Property resources, defining the observable or controllable properties that systems can measure or actuate. These methods implement read-only operations (GET only, no CRUD) for Properties at canonical endpoints (`/properties`, `/properties/{id}`). Properties represent physical quantities (temperature, pressure, humidity), chemical properties (pH, dissolved oxygen), biological parameters (species count), or control parameters (valve position, power state). The methods parse property definitions from controlled vocabularies (like QUDT or CF Standard Names), support relationship queries (properties observed by specific systems or datastreams), and provide access to property metadata (definition URIs, units, descriptions). Properties serve as the vocabulary for DataStreams (what is being measured) and ControlStreams (what can be controlled), connecting abstract concepts to concrete measurement streams.

**Operations to Implement:**

**Read Operations:**

- List all properties: `GET /properties`
- Get single property: `GET /properties/{id}`
- Query properties: `GET /properties?q=temperature&system=...`
- Properties by system: `GET /properties?system={systemId}` (properties this system can observe)
- Properties in collection: `GET /collections/{collectionId}/items?featureType=sosa:ObservableProperty`

**Property Metadata to Parse:**

- `definition`: URI from controlled vocabulary (QUDT, CF, etc.)
- `label`: Human-readable name
- `description`: Detailed explanation
- `baseProperty`: Parent property in hierarchy
- `subProperties`: Child properties
- `units`: Standard units of measure

**Property Relationship Management:**

- Systems capable of observing this property
- DataStreams observing this property (Part 2)
- ControlStreams controlling this property (Part 2)
- Property hierarchies (baseProperty/subProperty relationships)

**Complete Query and Filtering Support:**

These methods implement FULL query parameter support - NOT MVP scope.

- **Full-text search**: `q` parameter for searching property labels, descriptions, definitions
- **Relationship filtering**: `system` (properties observable by specific systems), `baseProperty` (child properties of a base property)
- **ID filtering**: `id` parameter (multiple property IDs)
- **UID filtering**: `uid` parameter (definition URIs)
- **Property-based filtering**: Any property metadata field (e.g., `label=Temperature`, `units=Cel`)
- **Pagination**: `limit` and `offset` for paging through property vocabularies
- **Format**: JSON only (properties don't have spatial geometry)
- **Combined filtering**: All parameters work together

**Recommended Development Workflow:**

1. Write method signatures for read and vocabulary navigation methods
2. Add JSDoc documenting vocabulary integration, hierarchy navigation
3. Implement read operations with baseProperty relationship handling
4. Write tests for observable/controllable property filtering
5. Document vocabulary URI dereferencing as you implement
6. Add JSDoc examples for property discovery workflows

---

#### DataStreams Resource Methods

The CSAPIQueryBuilder includes DataStreams resource methods to manage CSAPI DataStream resources, representing collections of observations from the same system with shared schemas. These methods implement all CRUD operations for DataStreams at canonical endpoints (`/datastreams`, `/datastreams/{id}`) and nested endpoints (`/systems/{systemId}/datastreams` for system-specific streams). DataStreams define the structure and metadata for observation data: what properties are being observed, what system is observing them, what sampling features or features of interest are involved, what schema the results follow, and what output format is used. The methods parse SWE Common result schemas (DataComponent definitions), validate that observations conform to these schemas, support relationship queries (datastreams for specific systems, procedures, or features of interest), and provide access to schema endpoints (`/datastreams/{id}/schema`). DataStreams are the bridge between Part 1 metadata (systems, procedures, sampling features) and Part 2 dynamic data (observations).

**Operations to Implement:**

**Read Operations:**

- List all datastreams: `GET /datastreams`
- Get single datastream: `GET /datastreams/{id}`
- Query datastreams: `GET /datastreams?system=...&observedProperty=...&foi=...`
- System-specific datastreams: `GET /systems/{systemId}/datastreams`
- Get result schema: `GET /datastreams/{id}/schema`
- DataStreams in collection: `GET /collections/{collectionId}/items`

**Create Operations:**

- Create datastream: `POST /datastreams` with JSON body including result schema
- Create under system: `POST /systems/{systemId}/datastreams`

**Update Operations:**

- Replace datastream: `PUT /datastreams/{id}` (caution: schema changes affect existing observations)
- Partial update: `PATCH /datastreams/{id}` (limited schema updates allowed)

**Delete Operations:**

- Delete datastream: `DELETE /datastreams/{id}`
- Cascade delete: `DELETE /datastreams/{id}?cascade=true` (deletes all observations)

**DataStream Properties to Parse:**

- `name`: Human-readable name
- `description`: Detailed description
- `system`: Link to producing system (required)
- `observedProperties`: Array of property URIs being measured
- `resultSchema`: SWE Common DataComponent defining observation structure
- `resultFormat`: Output encoding (JSON, Text, Binary)
- `phenomenonTimeRange`: Temporal extent of observations
- `procedure`: Link to observation methodology
- `samplingFeatures`: Links to sampling features
- `featuresOfInterest`: Links to ultimate features of interest
- `liveFeed`: Boolean indicating real-time availability
- `archiveDuration`: How long observations are retained

**DataStream Relationship Management:**

- System producing this datastream (required association)
- Properties being observed (required association)
- Observations in this datastream (Part 2, see Observations methods)
- Procedure used (optional association)
- Sampling features (optional association)
- Features of interest (optional association)

**Schema Operations:**

- Parse SWE Common result schema
- Validate observation results against schema
- Provide schema introspection for clients
- Support schema evolution (versioning)

**Complete Query and Filtering Support:**

These methods implement FULL query parameter support - NOT MVP scope.

- **Relationship filtering**: `system`, `observedProperty`, `foi`, `samplingFeature`, `procedure` parameters for association-based discovery
- **Temporal filtering**: `datetime` parameter for filtering by phenomenonTimeRange (datastream validity period)
- **ID filtering**: `id` parameter (multiple datastream IDs)
- **UID filtering**: `uid` parameter
- **Full-text search**: `q` parameter across datastream names and descriptions
- **Property-based filtering**: Any datastream property (e.g., `liveFeed=true`, `resultFormat=JSON`)
- **Pagination**: `limit` and `offset` for paging through large datastream catalogs
- **Format**: JSON (datastream metadata and SWE Common schemas in JSON)
- **Combined filtering**: All parameters work together to narrow discovery

**Recommended Development Workflow:**

1. Write method signatures for CRUD, schema operations, observation navigation
2. Add comprehensive JSDoc with schema handling examples, validation rules
3. Implement each operation with schema integration documentation
4. Write tests for schema retrieval, validation, observations
5. Document SWE Common schema interpretation as you implement
6. Add JSDoc examples for datastream creation and observation workflows

---

#### Observations Resource Methods

The CSAPIQueryBuilder includes Observations resource methods to manage CSAPI Observation resources, representing actual measurement data from systems. These methods implement CRUD operations for Observations at canonical endpoints (`/observations`, `/observations/{id}`) and nested endpoints (`/datastreams/{datastreamId}/observations` for stream-specific observations). Observations are the dynamic data in CSAPI - they change frequently, come in high volumes, and require efficient pagination and temporal queries. The methods parse SWE Common result encodings (JSON, Text/CSV, Binary), validate results against DataStream schemas, support temporal range queries (phenomenonTime, resultTime), implement cursor-based pagination for large result sets, and handle bulk observation creation (POST with arrays of observations). Observations connect to DataStreams for schema and metadata, making them schema-driven rather than free-form. This is one of the most performance-critical components due to high data volumes.

**Operations to Implement:**

**Read Operations:**

- List all observations: `GET /observations?phenomenonTime=...&limit=...`
- Get single observation: `GET /observations/{id}`
- Stream-specific observations: `GET /datastreams/{id}/observations?phenomenonTime=2024-01-01/2024-01-31`
- Query by result time: `GET /observations?resultTime=2024-01-01/..`
- Query by feature of interest: `GET /observations?foi={featureId}`
- Pagination: `GET /observations?cursor={nextCursor}&limit=1000`

**Create Operations:**

- Create single observation: `POST /datastreams/{id}/observations` with observation body
- Bulk create: `POST /datastreams/{id}/observations` with array of observations
- Stream ingestion: POST to `/datastreams/{id}/observations` with streaming payload

**Update Operations:**

- Replace observation: `PUT /observations/{id}` (rare, usually observations are immutable)
- Partial update: `PATCH /observations/{id}` (for quality flags, validation status)

**Delete Operations:**

- Delete observation: `DELETE /observations/{id}` (rare, usually retained)

**Observation Properties to Parse:**

- `phenomenonTime`: When the observation was made (required, ISO 8601)
- `resultTime`: When the result became available (optional, defaults to phenomenonTime)
- `result`: Observation result structured per DataStream schema (required)
- `resultQuality`: Quality indicators (accuracy, precision, flags)
- `parameters`: Additional metadata (sensor settings, environmental conditions)
- `featureOfInterest`: Link to observed feature (optional if provided by DataStream)

**Observation Result Parsing:**

- Parse SWE Common JSON encoding: structured JSON with units
- Parse SWE Common Text encoding: CSV-style compact format
- Parse SWE Common Binary encoding: efficient binary format
- Validate against DataStream result schema
- Extract individual property values
- Extract units of measure
- Extract quality information

**Complete Temporal Query Features:**

These methods implement FULL temporal filtering - NOT MVP scope. All temporal query patterns from CSAPI Part 2 are supported.

- **phenomenonTime filtering** (when observation was made - PRIMARY temporal filter):
  - Single instant: `phenomenonTime=2024-01-15T12:00:00Z`
  - Closed interval: `phenomenonTime=2024-01-01/2024-01-31`
  - Open start (before end): `phenomenonTime=../2024-01-31`
  - Open end (after start): `phenomenonTime=2024-01-01/..`
  - Multiple disjoint intervals: `phenomenonTime=2024-01-01/2024-01-15,2024-02-01/2024-02-15`
- **resultTime filtering**: When observation result became available (ISO 8601 intervals)
- **Temporal binning/aggregation**: Group observations by time period (hour, day, month)
- **Temporal resolution**: Filter by minimum time spacing between observations

**Complete Pagination Support:**

Both offset-based and cursor-based pagination fully implemented - NOT MVP scope.

- **Offset-based pagination** (Part 1 style): `limit` + `offset` for predictable page numbers
- **Cursor-based pagination** (Part 2 optimized): `limit` + `cursor` for efficient streaming of large time series
  - Cursor tokens encode position in result set
  - Stable across result set changes
  - Required for datasets > 100K observations
- **Limit parameter**: 1 to 10,000 (CSAPI Part 2 maximum)
- **Next/prev links**: Link headers for navigation
- **Stable sorting**: By phenomenonTime ascending, then by ID for deterministic ordering

**Performance Considerations:**

- Efficient parsing of large observation arrays
- Streaming support for bulk ingestion
- Incremental parsing of CSV/Text format
- Memory-efficient handling of large result sets
- Caching of DataStream schemas

**Recommended Development Workflow:**

1. Write method signatures for CRUD, query, bulk operations, pagination
2. Add detailed JSDoc with temporal filter examples, pagination modes, encoding formats
3. Implement operations with inline documentation for complex temporal queries
4. Write tests for each encoding format, pagination mode, temporal filter
5. Document performance considerations for large datasets
6. Add JSDoc examples for time-series queries, bulk ingestion

---

#### Control Streams Resource Methods

The CSAPIQueryBuilder includes Control Streams resource methods to manage CSAPI ControlStream resources, representing command interfaces for controlling actuators and systems. These methods implement all CRUD operations for Control Streams at canonical endpoints (`/controlstreams`, `/controlstreams/{id}`) and nested endpoints (`/systems/{systemId}/controlstreams` for system-specific control channels). Control Streams define what can be controlled on a system: the control schema (parameters structure using SWE Common), valid parameter ranges and constraints, execution modes (synchronous vs asynchronous), and feasibility checking capabilities. The methods parse SWE Common parameter schemas, validate commands against these schemas, support relationship queries (controlstreams for specific systems or controlled properties), and provide access to schema endpoints (`/controlstreams/{id}/schema`). Control Streams mirror DataStreams architecturally but for control/actuation rather than observation/sensing. This functionality is essential for bidirectional system interaction beyond just reading sensor data.

**Operations to Implement:**

**Read Operations:**

- List all control streams: `GET /controlstreams`
- Get single control stream: `GET /controlstreams/{id}`
- Query control streams: `GET /controlstreams?system=...&controlledProperty=...`
- System-specific control streams: `GET /systems/{systemId}/controlstreams`
- Get parameter schema: `GET /controlstreams/{id}/schema`
- Control streams in collection: `GET /collections/{collectionId}/items`

**Create Operations:**

- Create control stream: `POST /controlstreams` with JSON body including parameter schema
- Create under system: `POST /systems/{systemId}/controlstreams`

**Update Operations:**

- Replace control stream: `PUT /controlstreams/{id}`
- Partial update: `PATCH /controlstreams/{id}`

**Delete Operations:**

- Delete control stream: `DELETE /controlstreams/{id}`
- Cascade delete: `DELETE /controlstreams/{id}?cascade=true` (deletes all commands)

**Control Stream Properties to Parse:**

- `name`: Human-readable name
- `description`: Detailed description
- `system`: Link to controlled system (required)
- `controlledProperties`: Array of property URIs being controlled
- `parameterSchema`: SWE Common DataComponent defining command structure
- `parameterFormat`: Input encoding (JSON, Text, Binary)
- `executionMode`: Synchronous or asynchronous
- `supportsExecutionControl`: Can cancel/pause/resume
- `supportsFeasibility`: Can check feasibility before execution

**Control Stream Relationship Management:**

- System being controlled (required association)
- Properties being controlled (required association)
- Commands sent through this stream (see Commands methods)
- Valid parameter ranges and constraints

**Schema Operations:**

- Parse SWE Common parameter schema
- Validate command parameters against schema
- Provide schema introspection for clients
- Support schema evolution

**Complete Query and Filtering Support:**

These methods implement FULL query parameter support - NOT MVP scope.

- **Relationship filtering**: `system` (control streams for specific systems), `controlledProperty` (by controlled property URI)
- **ID filtering**: `id` parameter (multiple control stream IDs)
- **UID filtering**: `uid` parameter
- **Full-text search**: `q` parameter across names and descriptions
- **Property-based filtering**: Any control stream property (e.g., `executionMode=asynchronous`, `supportsFeasibility=true`)
- **Pagination**: `limit` and `offset`
- **Format**: JSON (control stream metadata and SWE Common parameter schemas in JSON)
- **Combined filtering**: All parameters work together

**Recommended Development Workflow:**

1. Write method signatures for CRUD, schema operations, command navigation
2. Add JSDoc with parameter schema examples, validation rules
3. Implement operations with schema integration documentation
4. Write tests for schema retrieval, command parameter validation
5. Document controllable property associations as you implement
6. Add JSDoc examples for control stream setup and command workflows

---

#### Commands Resource Methods

The CSAPIQueryBuilder includes Commands resource methods to manage CSAPI Command resources, representing instructions sent to systems for actuation or control. These methods implement CRUD operations for Commands at canonical endpoints (`/commands`, `/commands/{id}`) and nested endpoints (`/controlstreams/{controlstreamId}/commands` for stream-specific commands). Commands are the control equivalent of Observations - they flow to systems rather than from systems. The methods parse SWE Common parameter encodings, validate parameters against ControlStream schemas, support temporal queries (issueTime, executionTime), implement command status tracking (`/commands/{id}/status`), handle command results (`/commands/{id}/result`), and support bulk command submission. Commands can be synchronous (immediate execution with result) or asynchronous (queued execution with status polling). This functionality enables closed-loop control and system tasking capabilities.

**Operations to Implement:**

**Read Operations:**

- List all commands: `GET /commands?issueTime=...&limit=...`
- Get single command: `GET /commands/{id}`
- Stream-specific commands: `GET /controlstreams/{id}/commands?issueTime=2024-01-01/..`
- Query by execution time: `GET /commands?executionTime=2024-01-01/..`
- Query by status: `GET /commands?status=pending,executing`
- Get command status: `GET /commands/{id}/status`
- Get command result: `GET /commands/{id}/result`

**Create Operations:**

- Create single command: `POST /controlstreams/{id}/commands` with command body
- Bulk create: `POST /controlstreams/{id}/commands` with array of commands
- Check feasibility: `POST /controlstreams/{id}/feasibility` with parameters

**Update Operations:**

- Update command status: `PATCH /commands/{id}/status` (for system-generated status updates)
- Update command result: `PUT /commands/{id}/result` (when execution completes)
- Cancel command: `POST /commands/{id}/cancel`

**Delete Operations:**

- Delete command: `DELETE /commands/{id}` (if not yet executed)

**Command Properties to Parse:**

- `issueTime`: When command was issued (ISO 8601)
- `executionTime`: When to execute (optional, immediate if omitted)
- `parameters`: Command parameters per ControlStream schema
- `priority`: Execution priority (integer)
- `sender`: Entity that issued command
- `receiver`: Target system/component

**Command Status Properties:**

- `status`: Current state (pending, accepted, executing, completed, failed, cancelled)
- `percentCompletion`: Progress indicator (0-100)
- `statusMessage`: Human-readable status
- `updateTime`: Last status update timestamp

**Command Result Properties:**

- `result`: Execution result per ControlStream schema
- `completionTime`: When execution finished
- `resultQuality`: Quality indicators for result

**Complete Temporal Query Features:**

These methods implement FULL temporal filtering - NOT MVP scope. All temporal query patterns from CSAPI Part 2 are supported.

- **issueTime filtering** (when command was issued - PRIMARY temporal filter):
  - Single instant: `issueTime=2024-01-15T12:00:00Z`
  - Closed interval: `issueTime=2024-01-01/2024-01-31`
  - Open start: `issueTime=../2024-01-31`
  - Open end: `issueTime=2024-01-01/..`
- **executionTime filtering**: When command should be/was executed (ISO 8601 intervals)
- **Status filtering**: `status` parameter with multiple values (pending, accepted, executing, completed, failed, cancelled)
- **Relationship filtering**: `controlstream` parameter (commands for specific control stream)

**Complete Pagination Support:**

Both offset-based and cursor-based pagination fully implemented - NOT MVP scope.

- **Offset-based pagination**: `limit` + `offset` for predictable page numbers
- **Cursor-based pagination**: `limit` + `cursor` for efficient streaming of command histories
- **Limit parameter**: 1 to 10,000 (CSAPI Part 2 maximum)
- **Next/prev links**: Link headers for navigation
- **Stable sorting**: By issueTime ascending, then by ID

**Command Lifecycle Management:**

- Submit command (validate parameters)
- Track status (poll for updates)
- Retrieve result (when completed)
- Cancel command (if supported)
- Check feasibility (before submission)

**Synchronous vs Asynchronous Execution:**

- Synchronous: POST returns 200 with immediate result
- Asynchronous: POST returns 201 with status URL, client polls for completion

**Recommended Development Workflow:**

1. Write method signatures for CRUD, execution, status tracking, result retrieval
2. Add comprehensive JSDoc with status state machine, async patterns, examples
3. Implement operations with detailed status tracking documentation
4. Write tests for sync/async execution, status polling, error handling
5. Document temporal filters for command history as you implement
6. Add JSDoc examples for command submission, status tracking, result retrieval workflows

---

## Format Handler Components

### GeoJSON Handler: Extending Existing Parser

The GeoJSON handler is existing code in the library that parses GeoJSON Feature and FeatureCollection documents, supporting all seven geometry types (Point, LineString, Polygon, MultiPoint, MultiLineString, MultiPolygon, GeometryCollection). For CSAPI, we will extend this handler with COMPLETE recognition and extraction of ALL CSAPI-specific properties - NOT MVP Scope. The extension will recognize CSAPI-specific feature types through the `featureType` property and extract all CSAPI resource properties from the feature `properties` object. CSAPI Part 1 resources (Systems, Deployments, Procedures, Sampling Features) are encoded as GeoJSON features with additional semantic properties like `systemType`, `assetType`, `uniqueIdentifier`, `validTime`, and association links to related resources. The extension will add comprehensive type checking for all these CSAPI properties and complete validation rules specific to each CSAPI feature type, while maintaining compatibility with generic GeoJSON handling for other OGC API standards. This approach leverages the existing GeoJSON infrastructure while adding CSAPI-aware semantics on top.

**COMPLETE CSAPI-Specific GeoJSON Properties - NOT MVP Scope:**

- Systems: `systemType` (URI), `assetType` (enum), `uniqueIdentifier` (URI), `validTime` (period), association arrays (`subsystems`, `deployments`, `procedures`, `samplingFeatures`, `datastreams`, `controlstreams`)
- Deployments: `deployedSystems` (array), `validTime` (period), spatial/temporal extent
- Procedures: `procedureType` (URI), `methodKind` (URI), `attachedTo` (link to system)
- Sampling Features: `samplingFeatureType` (URI), `sampledFeature` (link), `relatedSamplingFeature` (links)
- All resources: `id`, `name`, `description`, `links` (HATEOAS navigation)

**COMPLETE Validation Requirements - NOT MVP Scope:**

- `uniqueIdentifier` must be valid URI (preferably URN format following RFC 8141)
- `systemType` must be from SOSA/SSN vocabulary (`sosa:Sensor`, `sosa:Platform`, `sosa:Actuator`, `sosa:Sampler`, etc.) with URI validation
- `validTime` must be ISO 8601 temporal period or instant with full interval support (start/end, start/duration, open-ended)
- Association arrays must contain valid resource links (href + rel) or inline features (embedded GeoJSON) with referential integrity checking
- Geometry must be valid per RFC 7946 (WGS84 coordinates, right-hand rule for polygons, coordinate array structure)
- All required properties present for each resource type (id, name, links minimum for all types)
- All enumeration values from allowed lists (assetType, procedureType, samplingFeatureType)
- All URIs properly formatted and dereferenceable where applicable
- Spatial extent validation (bbox must be valid WGS84 bounds)
- Temporal extent validation (all ISO 8601 formats with timezone handling)
- Link relation validation (IANA relations + CSAPI-specific relations)
- Property data type validation (strings, numbers, booleans, arrays, objects match schema)

**Recommended Development Workflow:**

1. Write method signatures for CSAPI property extraction methods
2. Add JSDoc documenting which CSAPI properties are handled, validation rules
3. Implement parsing logic for each resource type
4. Write tests with sample CSAPI GeoJSON features
5. Document CSAPI-specific validation rules as you implement them

**Implementation Type:** EXTENDING EXISTING CODE

---

### SensorML Handler: Building New Format Parser

The SensorML handler is new code we need to build to parse [OGC SensorML 3.0](https://docs.ogc.org/is/23-000r1/23-000r1.html) format documents that describe sensor systems, components, and processes in detail with COMPLETE support for ALL SensorML 3.0 elements - NOT MVP Scope. SensorML 3.0 is the latest version of the JSON-native format from the Sensor Web Enablement (SWE) standards family, published in 2024, that provides rich metadata about sensors, actuators, and processing chains with significant improvements over the previous XML-based 2.x versions. CSAPI servers return SensorML 3.0 documents when describing Systems or Procedures, providing detailed technical specifications beyond what GeoJSON can express. We will build a comprehensive parser that handles all SensorML 3.0 system models (System, PhysicalComponent, PhysicalSystem, SystemConfiguration), all component descriptions, all feature of interest definitions, all capability/characteristic/constraint specifications, all input/output specifications, all configuration parameters, all operational modes, all component connections, and temporal validity periods. The parser must convert SensorML 3.0 JSON documents into TypeScript objects that the library can work with, following the same architecture patterns as the existing GeoJSON and other format handlers. This new component represents one of the most complex format handling tasks in the project due to SensorML's hierarchical structure, extensive vocabulary, and deep integration with [SWE Common 3.0](https://docs.ogc.org/is/23-011r1/23-011r1.html) data components.

**SensorML 3.0 Document Types to Parse:**

- **System**: Abstract system description with common properties (identification, classification, characteristics, capabilities, contacts)
- **PhysicalComponent**: Single physical sensor or actuator with detailed specifications, position, and operating characteristics
- **PhysicalSystem**: Composite system made of multiple components with spatial/functional connections and aggregation properties
- **SystemConfiguration**: Reusable configuration profiles with parameter settings and mode definitions

**SensorML 3.0 Elements to Extract:**

- **Identification**: `uid` (unique identifier), `label`, `description`, `identifiers` (array of alternate identifiers)
- **Classification**: `classifiers` array with type definitions, intended applications, sensor taxonomies
- **ValidTime**: Temporal period when description is valid (ISO 8601 period)
- **SecurityConstraints**: Access restrictions, usage limitations, classification levels
- **Characteristics**: Observable properties, measurement ranges, resolution, accuracy, sensitivity (using SWE Common 3.0 DataRecord)
- **Capabilities**: Operating conditions, survival ranges, response times, power requirements (using SWE Common 3.0 DataRecord)
- **Constraints**: Physical or operational constraints limiting system use
- **Contacts**: Responsible parties, manufacturers, operators with roles and contact information
- **Documentation**: Links to user manuals, datasheets, specifications, images, videos
- **FeaturesOfInterest**: What the system observes or controls (links to feature definitions)
- **Inputs**: Data interfaces, observable properties, control inputs (using SWE Common 3.0 DataComponent definitions)
- **Outputs**: Data outputs, actuated properties, status indicators (using SWE Common 3.0 DataComponent definitions)
- **Parameters**: Configuration settings, calibration parameters, operational modes (using SWE Common 3.0 DataComponent definitions)
- **Modes**: Operating modes with associated configurations and state transitions
- **Components** (PhysicalSystem only): Array of component systems with roles and connections
- **Connections** (PhysicalSystem only): Data flow and physical connections between components
- **Position**: Location and orientation using GeoJSON Point or more complex positioning models

**COMPLETE Parsing Capabilities - NOT MVP Scope:**

- **Recursive component parsing**: Unlimited depth traversal for nested PhysicalSystems with full component hierarchy preservation
- **SWE Common 3.0 DataComponent integration**: Complete parsing of all DataComponent types used in characteristics, capabilities, parameters, inputs, outputs (DataRecord, DataArray, Quantity, Count, Boolean, Text, Time, Category, Vector, Matrix, all range types, DataChoice, GeometryData)
- **Unit of measure parsing**: Full UCUM code support ([UCUM codes](http://unitsofmeasure.org/)) with unit validation, scale factors, offsets
- **Reference resolution**: External link dereferencing for procedures, datasheets, feature definitions, documentation, images, videos with HTTP/HTTPS fetching and caching
- **Position/location parsing**: Complete GeoJSON geometry support plus orientation (quaternions, euler angles, direction cosines), reference frames (EPSG codes, custom frames), dynamic positioning (velocity, acceleration)
- **Mode and configuration state management**: All operational modes with state definitions, transitions, associated configurations, parameter value sets
- **Connection graph traversal**: Complete component connection mapping (data flow, physical connections, control connections) with port matching and graph analysis
- **Vocabulary resolution**: Automatic fetching and caching of vocabulary terms from code spaces (SOSA, SSN, CF, QUDT)
- **Schema validation**: Full validation against SensorML 3.0 JSON Schema with detailed error reporting
- **Temporal validity**: Complete ISO 8601 temporal period parsing with timezone handling
- **Security constraints**: Classification level parsing, access restrictions, usage limitations
- **Contact information**: All contact types with vCard formatting
- **Documentation links**: Media type detection, thumbnail generation, content previewing

**References:**

- [OGC SensorML 3.0 Standard](https://docs.ogc.org/is/23-000r1/23-000r1.html) (OGC 23-000r1)
- [SensorML 3.0 JSON Schema](https://schemas.opengis.net/sensorml/3.0/)
- [OGC Connected Systems API Part 1 - SensorML Encoding](https://docs.ogc.org/is/23-001/23-001.html#sensorml-encoding)

**Recommended Development Workflow:**

1. Write TypeScript interfaces for SensorML types (PhysicalSystem, PhysicalComponent, etc.)
2. Add comprehensive JSDoc to each interface documenting all properties and relationships
3. Implement parser methods with JSDoc showing examples of input/output
4. Write tests for each SensorML element type as you implement parsing
5. Document complex parsing logic (recursion, SWE Common integration) inline
6. Add usage examples to JSDoc for common scenarios (parsing system with components)

**Implementation Type:** BUILDING NEW CODE

---

### SWE Common Handler: Building New Format Parser

The SWE Common handler is new code we need to build to parse [OGC SWE Common 3.0](https://docs.ogc.org/is/23-011r1/23-011r1.html) format documents that define observation data schemas and encode actual observation results with COMPLETE support for ALL data components and ALL three encodings - NOT MVP Scope. SWE Common 3.0 is the latest version of the data encoding standard from the Sensor Web Enablement family, published in 2024, that describes structured measurement data with units, quality information, and constraints using a modernized JSON-native approach. CSAPI Part 2 uses SWE Common 3.0 extensively for DataStream schemas (defining what properties are observed and result structure) and Observation results (actual measurement values). We will build comprehensive parsers for all three SWE Common 3.0 encodings: JSON (human-readable structured data), Text (CSV-style compact encoding with configurable delimiters), and Binary (efficient encoding for high-volume streaming with multiple data types and byte orders). The handler must parse all DataComponent schemas (Quantity, Count, Boolean, Text, Time, Category, CategoryRange, QuantityRange, TimeRange, DataRecord, DataArray, Vector, Matrix, DataChoice, GeometryData), extract values from all encoded result formats, validate all measurements against schemas including quality indicators and constraints, and convert between all different encodings bidirectionally. This is the second most complex format handling component after SensorML due to the variety of encoding formats, the need for schema-driven validation, and the performance requirements for high-volume streaming data.

**SWE Common 3.0 Data Components to Parse:**

**Simple Components:**

- **Quantity**: Numeric measurement with unit of measure and optional constraints (temperature, pressure, voltage)
- **Count**: Integer count value with optional constraints (particle count, event count)
- **Boolean**: True/false indicator (on/off status, alarm state)
- **Text**: String value with optional pattern constraints (station ID, observation notes)
- **Time**: ISO 8601 timestamp with optional temporal reference frame (observation time, event time)
- **Category**: Categorical value from controlled vocabulary with code space (weather condition, quality flag)

**Range Components (new in 3.0):**

- **QuantityRange**: Range of numeric values with units (temperature range, acceptable operating range)
- **CategoryRange**: Range of categorical values (quality range indicators)
- **TimeRange**: Temporal interval (observation period, validity period)

**Complex Components:**

- **DataRecord**: Structured record containing multiple named fields (multi-property observation)
- **DataArray**: Array of measurements with variable or fixed element count (time series, profile, trajectory)
- **Vector**: Positional vector with coordinate reference system (3D location, velocity, acceleration)
- **Matrix**: Matrix of values with specified dimensions (covariance matrix, transformation matrix)
- **DataChoice**: Choice between alternative structures with selection criteria (different measurement modes, conditional observations)
- **GeometryData**: Geometric data encoded using GeoJSON geometry types (spatial observations, coverage areas)

**SWE Common 3.0 Encodings to Support:**

**JSON Encoding** (human-readable):

```json
{
  "temperature": { "uom": { "code": "Cel" }, "value": 23.5 },
  "humidity": { "uom": { "code": "%" }, "value": 65.2 }
}
```

**Text Encoding** (CSV-style compact):

```
23.5,65.2
24.1,63.8
```

**Binary Encoding** (efficient streaming):

- IEEE 754 floating point (32-bit, 64-bit)
- Integer encodings (signed/unsigned, 8/16/32/64-bit)
- Base64 encoded blocks
- Block compression support
- Little-endian and big-endian byte order support

**COMPLETE Schema Validation Requirements - NOT MVP Scope:**

- **Result structure validation**: Complete matching of result structure against DataStream schema (all DataComponent definitions, nested structures, choice discriminators)
- **Range validation**: All values within allowed ranges (AllowedValues enumeration lists, AllowedIntervals numeric/temporal ranges, AllowedTimes temporal constraints, AllowedTokens text patterns with regex)
- **Unit validation**: Complete UCUM code validation ([UCUM codes](http://unitsofmeasure.org/)) with unit conversion support, scale factors, offsets
- **Array validation**: Array dimensions match schema element count specifications (fixed or variable size), homogeneous element types, nested array support
- **Quality validation**: All quality indicators follow schema (nilValues with reason codes, quality DataRecord with multiple quality measures, uncertainty values)
- **Temporal validation**: All timestamps follow ISO 8601 format with optional reference frame (UTC, TAI, GPS time), timezone handling, leap second support
- **Categorical validation**: All categorical values from defined code space with vocabulary dereferencing, code validation
- **Text validation**: All text patterns match defined constraints (regex patterns, length limits, character sets)
- **Geometry validation**: GeometryData follows GeoJSON spec (coordinate structure, geometry types, CRS handling)
- **Matrix validation**: Matrix dimensions match schema (rows × columns), data type consistency, numeric precision
- **Vector validation**: Vector components match coordinate reference system, dimension count, axis order
- **Choice validation**: DataChoice discriminator present, selected option matches discriminator, option structure validation

**COMPLETE Advanced 3.0 Features Support - NOT MVP Scope:**

- **NilValues**: Complete representation of missing/invalid data with all reason codes (inapplicable, missing, template, unknown, withheld, BelowDetectionRange, AboveDetectionRange), reason text, custom codes
- **Quality**: All associated quality indicators (accuracy measures, precision values, confidence intervals, data quality flags, quality DataRecord with multiple quality dimensions)
- **Constraints**: Complete support for AllowedValues (enumeration lists, code lists), AllowedIntervals (numeric ranges, temporal ranges, open/closed bounds), AllowedTimes (temporal constraints, ISO 8601 intervals), AllowedTokens (text patterns, regex validation, character sets)
- **ReferenceFrames**: Complete temporal reference frame definitions (UTC, TAI, GPS time, custom frames) and spatial reference frame definitions (EPSG codes, WKT, custom CRS, axis order handling)
- **CodeSpaces**: Complete controlled vocabulary support with vocabulary dereferencing (HTTP/HTTPS fetching), caching, code validation, hierarchical code lists
- **Encoding conversion**: Bidirectional conversion between all three encodings (JSON ↔ Text ↔ Binary) with schema preservation
- **Streaming support**: Incremental parsing for large datasets, memory-efficient processing, chunked encoding/decoding
- **Performance optimization**: Binary encoding for high-volume data, text encoding for human readability, compression support (gzip, deflate)
- **Type coercion**: Automatic type conversion with precision preservation (integer to float, timestamp to ISO string, etc.)

**References:**

- [OGC SWE Common 3.0 Standard](https://docs.ogc.org/is/23-011r1/23-011r1.html) (OGC 23-011r1)
- [SWE Common 3.0 JSON Schema](https://schemas.opengis.net/sweCommon/3.0/)
- [OGC Connected Systems API Part 2 - SWE Common Encoding](https://docs.ogc.org/is/23-002/23-002.html#swe-common-encoding)

**Recommended Development Workflow:**

1. Write TypeScript interfaces for each DataComponent type (Quantity, DataRecord, etc.)
2. Add detailed JSDoc with encoding examples (JSON/Text/Binary)
3. Implement parser for each encoding format with comprehensive documentation
4. Write tests for each component type and encoding as you implement
5. Document schema validation rules, constraint handling inline
6. Add JSDoc examples showing encoding conversion workflows
7. Document performance considerations for binary encoding

**Implementation Type:** BUILDING NEW CODE

---

### Format Detector: Extending Existing Content Negotiation

The format detector is existing code that examines HTTP response headers (Content-Type) and document structure to determine what format a server returned. For CSAPI, we will extend this detector with COMPLETE recognition of ALL CSAPI media types with comprehensive fallback detection - NOT MVP Scope. The extension will recognize all new media types used by CSAPI servers: `application/sml+json` (SensorML-JSON encoding), `application/swe+json` (SWE Common JSON encoding), `application/swe+text` (SWE Common Text/CSV encoding), and `application/swe+binary` (SWE Common Binary encoding). The extension will add these media types to the library's format registry and route them to the appropriate new format handlers (SensorML handler, SWE Common handler) with complete parameter parsing (charset, boundary, encoding parameters). This follows the existing pattern where the detector checks Content-Type headers first, then falls back to comprehensive document structure analysis if headers are missing or ambiguous. The extension maintains the library's existing format abstraction architecture where developers work with parsed TypeScript objects regardless of the wire format.

**COMPLETE Media Type Recognition - NOT MVP Scope:**

- `application/sml+json` → Route to SensorML Handler (with charset detection)
- `application/swe+json` → Route to SWE Common Handler (JSON encoding, charset detection)
- `application/swe+text` → Route to SWE Common Handler (Text encoding, delimiter detection, charset handling)
- `application/swe+binary` → Route to SWE Common Handler (Binary encoding, byte order detection, data type detection)
- `application/geo+json` with CSAPI `featureType` → Route to GeoJSON Handler with CSAPI extensions (all Part 1 resource types)
- All media type parameters: charset (UTF-8, UTF-16, ISO-8859-1, etc.), version, encoding, boundary for multipart

**COMPLETE Detection Strategy - NOT MVP Scope:**

1. **Content-Type header parsing** (primary method): Full media type parsing with parameter extraction, quality factor handling (q values), wildcard matching, charset detection
2. **Accept header negotiation**: Server-driven content negotiation with quality factors, format preference ordering, fallback format selection
3. **Document structure analysis** (fallback for missing headers): Root JSON property examination (SensorML: `type: PhysicalSystem`, SWE Common: `type: DataRecord`, CSAPI GeoJSON: `featureType` property), schema pattern matching, namespace detection
4. **Format-specific identifiers**: SensorML (all process types: PhysicalSystem, PhysicalComponent, System, SystemConfiguration), SWE Common (all component types: DataRecord, DataArray, Quantity, Vector, Matrix, etc.), CSAPI GeoJSON (all resource types: System, Deployment, Procedure, SamplingFeature)
5. **Schema validation**: Validate against format JSON schemas with detailed error reporting, ambiguous format resolution through validation
6. **Binary format detection**: Magic numbers, byte order marks (BOM), structure signatures, data type patterns
7. **Text encoding detection**: Delimiter patterns (comma, tab, pipe, custom), quote character detection, escape sequence recognition, line ending detection (CRLF, LF, CR)
8. **Charset detection**: BOM detection (UTF-8, UTF-16 LE/BE, UTF-32 LE/BE), heuristic analysis for common encodings, encoding validation
9. **Error handling**: Graceful degradation for unknown formats, detailed error messages for malformed content, format suggestion for common mistakes

**Recommended Development Workflow:**

1. Write method signatures for CSAPI media type detection
2. Add JSDoc documenting each media type, detection strategy, fallback behavior
3. Implement detection logic with inline comments for complex heuristics
4. Write tests for each media type and edge cases (missing headers, ambiguous content)
5. Document media type routing decisions as you implement them

**Implementation Type:** EXTENDING EXISTING CODE

---

### Validator: Extending Existing Validation Framework

The validator is existing code that checks whether parsed documents conform to format specifications and semantic constraints. For CSAPI, we will extend this validator with COMPLETE validation of ALL CSAPI requirements across all resource types - NOT MVP Scope. The extension will check all CSAPI-specific requirements: all required properties for each resource type, all valid enumeration values (systemType, assetType, procedureType, samplingFeatureType, all Part 2 resource types), complete URI format validation (uniqueIdentifier must be URN, all vocabulary URIs must be valid), all temporal validity constraints (validTime periods with ISO 8601 compliance, timezone handling), all spatial constraint validation (geometry must be WGS84, coordinate validation, bbox validation), complete association integrity (linked resources must exist or be valid references, referential integrity across all relationship types), and comprehensive schema conformance for Part 2 resources (Observation results must match DataStream schema with all constraints, Command parameters must match ControlStream schema with all validation rules). The extension will add comprehensive CSAPI validation rules to the existing validation pipeline, reporting detailed errors and warnings through the same error handling mechanism used for other formats with enhanced context information. This maintains consistency in how the library reports validation failures across all OGC API standards while providing CSAPI-specific validation detail.

**COMPLETE CSAPI Validation Rules - NOT MVP Scope:**

**Part 1 Resource Validation:**

- Systems: `uniqueIdentifier` (required URI), `systemType` (required, from SOSA vocabulary), `name` (required string), `location` (required for mobile systems)
- Deployments: `validTime` (required temporal period), spatial extent (required)
- Procedures: `procedureType` (required URI), attached system reference validation
- Sampling Features: `sampledFeature` (required reference), geometry (required)
- Properties: `definition` (required URI from vocabulary), `label` (required string)

**Part 2 Resource Validation:**

- DataStreams: schema validation (result schema must be valid SWE Common DataComponent), observed properties must reference existing Property resources, system association (required)
- Observations: result validation (must conform to DataStream schema), temporal validation (phenomenonTime required), result time validation
- Control Streams: schema validation (parameter schema must be valid SWE Common), system association (required)
- Commands: parameter validation (must conform to ControlStream schema), execution time validation

**COMPLETE Cross-Reference Validation - NOT MVP Scope:**

- **Association links**: All links must have valid href (absolute or relative URI), valid rel (IANA or CSAPI relation type), optional type (media type), optional title
- **Resource references**: Referenced resources must exist in collection or be valid external URIs with optional dereferencing and existence checking
- **Hierarchical integrity**: Parent-child relationships are consistent (system subsystems, deployment subdeployments), no circular references, depth limits respected
- **Relationship consistency**: Bidirectional relationships are consistent (system ↔ deployment, system ↔ datastream, datastream ↔ observation), orphaned resources detected
- **Vocabulary references**: All vocabulary URIs dereferenceable (observedProperty, controlledProperty, systemType, procedureType), vocabulary terms exist in vocabulary
- **Schema references**: DataStream schema valid SWE Common DataComponent, ControlStream schema valid SWE Common DataComponent, schemas dereferenceable if external
- **Spatial references**: CRS codes valid (EPSG codes or URIs), geometry coordinates within valid ranges (latitude -90 to 90, longitude -180 to 180)
- **Temporal references**: Reference frames valid (UTC, TAI, GPS time), timezones valid (IANA timezone database), ISO 8601 compliance
- **Unit references**: UCUM codes valid, custom units properly defined with conversion factors
- **External references**: HTTP/HTTPS links reachable (optional validation), media types match content, documentation links valid

**Validation Error Reporting:**

- **Error severity**: Error (invalid/unusable), Warning (questionable/suboptimal), Info (recommendations)
- **Error context**: JSON path to error location, line/column numbers, surrounding context
- **Error messages**: Clear description of problem, expected vs actual values, suggested fixes
- **Error codes**: Machine-readable error codes for programmatic handling
- **Batch validation**: All errors collected and reported together, not failing on first error
- **Validation summaries**: Count of errors/warnings/info messages, validation pass/fail status, performance metrics
- Subsystem references must create valid hierarchies (no circular references)
- Deployment-system associations must be bidirectional
- DataStream-system associations must be valid
- Observation-DataStream associations must be valid

**Recommended Development Workflow:**

1. Write method signatures for each validation rule category
2. Add JSDoc documenting what is validated, error codes returned, examples
3. Implement validation logic with clear error messages
4. Write tests with valid and invalid data for each rule
5. Document complex validation rules (cross-references, schema conformance) inline
6. Add JSDoc examples showing how to handle validation errors

**Implementation Type:** EXTENDING EXISTING CODE

---

## Worker Components

### Background Processing: Extending Existing Web Worker Pattern

The background processing component extends the existing Web Worker infrastructure in the Camptocamp OGC Client Library (`src/worker/worker.ts`, `src/worker/utils.ts`, `src/worker/index.ts`) to move heavy parsing and validation work off the main thread, keeping browser UIs responsive. The upstream library currently uses this worker pattern to parse XML capabilities documents for WMS, WFS, and WMTS services, offloading computationally expensive XML parsing and processing to a Web Worker that runs in parallel and returns results asynchronously via message passing (`sendTaskRequest()` and `addTaskHandler()` utilities). The library provides a fallback mechanism (`enableFallbackWithoutWorker()`) for non-worker environments like Node.js or older browsers, where the same code runs synchronously on the main thread. For CSAPI, we will extend this proven worker pattern by adding new CSAPI-specific message types to handle: SensorML 3.0 parsing (complex hierarchical JSON document traversal with recursive PhysicalSystem component trees), SWE Common 3.0 parsing (especially binary encoding decoding with IEEE 754 floats and multi-byte integers), large observation result set processing (thousands of observations with schema validation), bulk command validation, and comprehensive schema validation operations. The extension will integrate the new CSAPI format parsers (SensorML Handler, SWE Common Handler) into the worker context following the same architecture patterns already established for WMS/WFS/WMTS capabilities parsing. This maintains the library's performance characteristics when dealing with large CSAPI datasets or complex format parsing operations.

**COMPLETE CSAPI Operations to Move to Worker - NOT MVP Scope:**

This worker extension implements FULL offloading of computationally expensive CSAPI operations to maintain UI responsiveness.

**Format Parsing (Heavy Operations):**

- **SensorML 3.0 parsing**: Complex hierarchical JSON document parsing with recursive PhysicalSystem component trees, deep nesting, SWE Common DataComponent integration
- **SWE Common 3.0 parsing**: Binary encoding decoding (IEEE 754 float, multi-byte integers, byte order handling), Text/CSV parsing, JSON encoding with schema-driven validation
- **Large observation arrays**: Parsing thousands of observations with result validation against DataStream schemas (range checks, unit validation, quality indicators)
- **Large command arrays**: Bulk command parameter validation against ControlStream schemas and encoding for transmission
- **GeoJSON feature collections**: Large spatial datasets with CSAPI-specific property extraction (Systems, Deployments, Procedures, Sampling Features)

**Validation Operations (CPU-Intensive):**

- **Schema validation**: Complex SWE Common DataComponent schema validation with constraint checking
- **Observation result validation**: Validate observation results against DataStream result schemas (range checks, unit validation, quality indicators)
- **Command parameter validation**: Validate command parameters against ControlStream parameter schemas
- **Cross-reference validation**: Check resource association integrity across hierarchies

**Query Operations (Memory/CPU Intensive):**

- **Recursive hierarchy traversal**: Deep system/deployment trees with all descendants (potentially hundreds/thousands of nodes)
- **Spatial filtering**: bbox intersection calculations across large feature collections
- **Temporal filtering**: phenomenonTime/resultTime interval matching across large observation sets

**Worker Message Types to Add:**

- `PARSE_SENSORML_3`: Input SensorML 3.0 JSON, output parsed System/PhysicalComponent/PhysicalSystem object
- `PARSE_SWE_RESULT`: Input SWE Common encoded result (JSON/Text/Binary) + schema, output validated parsed values
- `PARSE_SWE_BINARY`: Input Base64 binary block + schema, output decoded observation array
- `VALIDATE_OBSERVATIONS`: Input observation array + DataStream schema, output validation results with errors/warnings
- `VALIDATE_COMMANDS`: Input command array + ControlStream schema, output validation results
- `PARSE_OBSERVATION_ARRAY`: Input large observation array (1000s of obs), output parsed and validated observations
- `TRAVERSE_HIERARCHY`: Input system ID + recursive flag, output complete hierarchy tree with all relationships
- `FILTER_SPATIAL`: Input feature collection + bbox, output filtered features (spatial intersection)
- `FILTER_TEMPORAL`: Input observation array + temporal interval, output filtered observations

**Performance Benefits:**

- Prevent main thread blocking during large data operations
- Enable responsive UIs during heavy parsing
- Parallel processing of multiple requests
- Better utilization of multi-core CPUs

**Fallback for Non-Worker Environments:**

- Provide synchronous fallback implementation
- Maintain same API surface
- Graceful degradation in environments without Web Worker support

**Recommended Development Workflow:**

1. Write message handler signatures for each CSAPI worker operation
2. Add JSDoc documenting message format, performance benefits, error handling
3. Implement worker handlers with fallback logic
4. Write tests for worker operations and fallback scenarios
5. Document performance characteristics as you measure them
6. Add JSDoc examples showing when operations run in workers

**Implementation Type:** EXTENDING EXISTING CODE (adding CSAPI message handlers to existing worker)

---

## Testing Components

### Test Coverage: Extending Existing Test Suite

The test coverage component extends the existing Jest test suite to cover all CSAPI functionality. For CSAPI, we will add test suites for every new component: format parsers (SensorML, SWE Common), resource handlers (Systems, DataStreams, Observations, Commands, etc.), query builders, validators, and integration tests. The library has established testing patterns including unit tests (isolated component tests), integration tests (multi-component interaction), and fixture-based tests (using example documents from the spec). The extension will add CSAPI test fixtures (GeoJSON features, SensorML documents, SWE Common results), mock CSAPI responses, and test utilities specific to CSAPI validation. Test coverage should match the existing library standard (>80% code coverage).

**COMPLETE CSAPI Test Suites to Create - NOT MVP Scope:**

This testing extension implements COMPREHENSIVE test coverage for all CSAPI functionality to match the existing library standard (>80% code coverage).

**Format Parser Tests (Complete Coverage):**

- **GeoJSON CSAPI extensions**: All Part 1 resource types (Systems, Deployments, Procedures, Sampling Features), all CSAPI-specific properties, all geometry types, validation rules
- **SensorML 3.0 parser**: All system models (System, PhysicalComponent, PhysicalSystem, SystemConfiguration), all elements (identification, classification, characteristics, capabilities, constraints, contacts, FeaturesOfInterest, modes, components, connections), recursive component parsing, SWE Common integration
- **SWE Common 3.0 parser**: All data components (Quantity, Count, Boolean, Text, Time, Category, QuantityRange, CategoryRange, TimeRange, DataRecord, DataArray, Vector, Matrix, DataChoice, GeometryData), all encodings (JSON, Text, Binary with endianness), constraint validation, quality indicators, nil values
- **Format detector**: All CSAPI media types (application/sml+json, application/swe+json, application/swe+text, application/swe+binary), fallback detection, error handling
- **Validator**: All Part 1 validation rules (required properties, enumeration values, URI formats, temporal constraints, spatial constraints, association integrity), all Part 2 validation rules (schema conformance, result validation, parameter validation), cross-reference validation

**Resource Handler Tests (All CRUD Operations + All Query Parameters):**

- **Systems**: Create/read/update/delete, subsystem hierarchy (recursive queries), all query parameters (bbox, datetime, parent, deployment, procedure, foi, id, uid, q, property filters, recursive), pagination (limit, offset), format negotiation (GeoJSON vs SensorML), error cases
- **Deployments**: CRUD, subdeployment hierarchy, all query parameters (bbox, datetime, system, parent, id, uid, q, property filters, recursive), pagination, format (GeoJSON only), error cases
- **Procedures**: CRUD, all query parameters (system, id, uid, q, property filters), pagination, format negotiation (GeoJSON vs SensorML), error cases
- **Sampling Features**: CRUD, all query parameters (bbox, system, foi, relatedSamplingFeature, id, uid, q, property filters), pagination, format (GeoJSON), error cases
- **Properties**: Read operations, all query parameters (system, baseProperty, id, uid, q, property filters), pagination, format (JSON), error cases
- **DataStreams**: CRUD, schema operations, all query parameters (system, observedProperty, foi, samplingFeature, procedure, datetime, id, uid, q, property filters), pagination, error cases
- **Observations**: CRUD, all temporal queries (phenomenonTime with all interval types, resultTime, temporal binning), all query parameters (foi, id), both pagination modes (offset-based, cursor-based), large result sets (1000s-10000s of observations), bulk operations, all encodings (JSON, Text, Binary), error cases
- **Control Streams**: CRUD, schema operations, all query parameters (system, controlledProperty, id, uid, q, property filters), pagination, error cases
- **Commands**: CRUD, status tracking, result retrieval, all temporal queries (issueTime, executionTime with all interval types), status filtering, both pagination modes, bulk operations, synchronous vs asynchronous execution, error cases

**Query Builder Tests (All Query Parameters + All Combinations):**

- **Canonical endpoints**: URL construction for all 9 resource types
- **Nested endpoints**: All nesting patterns (systems/subsystems, systems/datastreams, datastreams/observations, controlstreams/commands)
- **Query parameter encoding**: All spatial parameters (bbox 2D/3D, coordinate validation), all temporal parameters (datetime, phenomenonTime, resultTime, executionTime, issueTime with all interval formats), all relationship parameters (parent, system, deployment, procedure, foi, observedProperty, controlledProperty, baseProperty), all common parameters (id with multiple values, uid, q, property filters), hierarchical parameters (recursive), pagination (limit, offset, cursor), format negotiation (f parameter, Accept headers)
- **Combined filtering**: Multiple query parameters together (AND logic), parameter precedence, edge cases
- **Schema endpoints**: DataStream schema URL, ControlStream schema URL
- **Status/result endpoints**: Command status URL, command result URL
- **Error cases**: Invalid parameter values, malformed URLs, unsupported combinations

**Integration Tests (End-to-End Workflows):**

- **Discovery workflows**: Connect to server → check conformance → list collections → filter by resource type → retrieve resources
- **Observation workflows**: Discover systems → find datastreams → query observations with temporal filters → paginate results → parse SWE Common results
- **Command workflows**: Discover systems → find control streams → check feasibility → submit commands → track status → retrieve results
- **Cross-resource navigation**: System → deployments → procedures → sampling features → datastreams → observations (following all relationship links)
- **Format round-tripping**: Parse GeoJSON → validate → modify → serialize → parse again (verify consistency)
- **Hierarchical queries**: Recursive system traversal with large hierarchies, recursive deployment traversal
- **Error handling**: Server errors (4xx, 5xx), validation errors (schema mismatches, invalid data), network errors (timeouts, connection failures), malformed responses

**Test Fixtures to Create (Complete Coverage):**

- **Specification examples**: All example responses from CSAPI Parts 1 & 2 specification documents
- **Edge cases**: Empty collections, minimal resources, malformed data (for error handling tests), boundary conditions (max limits, extreme coordinates, edge temporal values)
- **Large datasets**: Paginated collections (100s of items), large observation sets (1000s-10000s of results for pagination testing), complex hierarchies (deep system/deployment nesting)
- **All format variations**: GeoJSON (all Part 1 resource types with all property combinations), SensorML 3.0 (all system types, all components, all encodings), SWE Common 3.0 (all data components, all three encodings: JSON/Text/Binary with various data types)
- **Error responses**: All HTTP error codes (400, 404, 409, 500, etc.), all validation error types, malformed content-type headers
- **Schema fixtures**: All DataStream schema examples (various observable types, all SWE Common component types), all ControlStream parameter schemas (all controllable property types)

**Test Coverage Targets:**

- **Code coverage**: >80% statement coverage for all new code, >80% branch coverage for all new code, 100% coverage for all public API methods
- **Resource coverage**: 100% of all CSAPI resource types, 100% of all query parameters, 100% of all format types (GeoJSON, SensorML 3.0, SWE Common 3.0 all encodings)
- **Error coverage**: All error conditions documented in CSAPI specification

**Implementation Type:** EXTENDING EXISTING CODE (adding CSAPI test suites to existing Jest framework)

---

## Documentation Components

### API Documentation: Extending Existing TypeDoc Documentation

The API documentation component extends the existing TypeDoc documentation to cover all CSAPI additions with COMPLETE coverage - NOT MVP Scope. For CSAPI, we will add comprehensive documentation for all new TypeScript interfaces and types, all new methods on OgcApiEndpoint, extensive usage examples for every resource type and query pattern, complete format handler documentation, and detailed migration guides for users of other CSAPI clients. The library uses TypeDoc to generate API documentation from TypeScript source code comments, providing type-aware documentation with cross-references and examples. The extension will add comprehensive JSDoc comments to all new code, following the existing documentation standards and style. This ensures CSAPI features are discoverable and understandable for library users.

**Implementation Type:** EXTENDING EXISTING CODE (adding CSAPI docs to existing TypeDoc setup)

---

## Summary: Build vs Extend Breakdown

### Components Extending Existing Code (9 components):

1. **Conformance Reader** - Add CSAPI conformance class checks (`hasConnectedSystems` getter, ~7 lines in info.ts)
2. **Collections Reader** - Parse CSAPI collection metadata with FULL query/filter/pagination support (`csapiCollections` getter, ~6 lines in endpoint.ts)
3. **OgcApiEndpoint Integration** - Add `csapi(collectionId)` factory method to main endpoint class (~35 lines in endpoint.ts following EDR pattern)
4. **GeoJSON Handler** - Recognize CSAPI feature types and properties (extend existing GeoJSON parser)
5. **Format Detector** - Add SensorML 3.0 and SWE Common 3.0 media types (extend existing content negotiation)
6. **Validator** - Add CSAPI validation rules (COMPLETE validation for all formats, extend existing validation framework)
7. **Background Processing** - Add CSAPI operations to Web Worker (extend existing worker with new message types)
8. **Test Coverage** - Add CSAPI test suites to Jest framework (fixture-based testing, extend existing test infrastructure)
9. **API Documentation** - Add CSAPI docs to TypeDoc (JSDoc comments written as code is developed, extend existing documentation)

### Components Building New Code (3 components):

1. **CSAPIQueryBuilder** - New query builder class with URL-building methods for all 9 CSAPI resource types (following EDRQueryBuilder pattern from PR #114)
   - Systems methods (getSystems, createSystem, updateSystem, deleteSystem, getSubsystems, getSystemHistory, etc.)
   - Deployments methods (getDeployments, createDeployment, updateDeployment, deleteDeployment, getSubdeployments, etc.)
   - Procedures methods (getProcedures, createProcedure, updateProcedure, deleteProcedure, etc.)
   - Sampling Features methods (getSamplingFeatures, createSamplingFeature, updateSamplingFeature, deleteSamplingFeature, etc.)
   - Properties methods (getProperties, getProperty - read-only)
   - DataStreams methods (getDataStreams, createDataStream, updateDataStream, deleteDataStream, getDataStreamSchema, etc.)
   - Observations methods (getObservations, createObservations, bulkCreateObservations, etc.)
   - Control Streams methods (getControlStreams, createControlStream, updateControlStream, deleteControlStream, getControlStreamSchema, etc.)
   - Commands methods (getCommands, createCommand, getCommandStatus, getCommandResult, cancelCommand, etc.)
   - FULL query parameter support across all methods (spatial, temporal, hierarchical, relationship, property filtering, pagination)
2. **SensorML Handler** - New format parser for SensorML 3.0 (COMPLETE support: JSON-native format, all system models, recursive component parsing, SWE Common integration)
3. **SWE Common Handler** - New format parser for SWE Common 3.0 (COMPLETE support: JSON/Text/Binary encodings, all data component types, schema validation, bidirectional conversion)

### Architectural Notes:

**QueryBuilder Pattern:** Following the upstream EDR pattern (PR #114), CSAPI uses a single QueryBuilder class accessed via a factory method on OgcApiEndpoint. Developers call `endpoint.csapi(collectionId)` to get a CSAPIQueryBuilder instance containing all 9 resource type methods. This maintains the library's architecture principle of composition over inheritance.

**Resource Methods within QueryBuilder:** The 9 resource sections documented above (Systems, Deployments, Procedures, Sampling Features, Properties, DataStreams, Observations, Control Streams, Commands) are all methods within the single CSAPIQueryBuilder class, not separate standalone components. This follows the same pattern as EDR where `EDRQueryBuilder` contains methods like `getCubeUrl()`, `getCorridorUrl()`, etc.

**Integration Footprint:** Total modifications to existing files: ~48 lines across 2 files (endpoint.ts: ~35 lines, info.ts: ~7 lines, index.ts: ~6 lines for exports). This minimal footprint follows the proven EDR integration pattern.

**Scope Understanding:** While the summary lists "3 components building new code" (architecturally accurate), the CSAPIQueryBuilder component represents ~70% of the new code volume (~10,000-14,000 lines of code) because it implements URL construction for 9 distinct CSAPI resource types with approximately 60-70 unique URL patterns covering full CRUD operations, nested resource access, schema endpoints, and comprehensive query parameter support. The detailed sections above document the functional methods within this single CSAPIQueryBuilder class. This consolidated single-class architecture follows the upstream EDR pattern (one QueryBuilder per API family) but delivers functionally extensive capabilities across all CSAPI resources. Clients evaluating scope should understand that while architecturally elegant (3 new classes vs 12), the functional scope is substantial - implementing complete CSAPI Part 1 and Part 2 specifications with full query, filter, and pagination support across all resource types.

### Estimated Scope:

- **Extending existing code:** ~20% of effort (9 small extensions following established patterns, ~50 total lines modified)
- **Building new code:** ~80% of effort (CSAPIQueryBuilder with ~60-70 URL patterns, 2 complex format parsers)
- **Total estimated lines of code:** ~15,000-20,000 lines (reduced from initial estimate due to single QueryBuilder class vs 9 separate handlers)
- **Total estimated time:** 6-8 weeks for complete FULL implementation (NOT MVP)

---

## Project Goals Alignment

Every component described above aligns with these core project goals:

1. **Unified Developer Experience:** All CSAPI functionality accessed through existing `OgcApiEndpoint` class using the same patterns as Features, Tiles, and EDR
2. **Format Abstraction:** Developers work with TypeScript objects, not raw GeoJSON/SensorML/SWE Common
3. **Upstream Integration:** Extensions follow established patterns in the camptocamp/ogc-client repository
4. **Complete Spec Coverage:** All CSAPI Part 1 and Part 2 resources with full CRUD support
5. **Production Ready:** Comprehensive validation, error handling, testing, and documentation
6. **Performance Aware:** Web Worker support for heavy operations, efficient pagination, streaming support
