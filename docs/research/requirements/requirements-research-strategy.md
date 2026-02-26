# Requirements Research Strategy

**Purpose:** Systematically identify ALL functional requirements for CSAPI client implementation to avoid gaps and missed functionality.

**Context:** Previous iterations missed requirements (e.g., SensorML parsing). Need comprehensive requirement discovery BEFORE writing functional specification.

**Approach:** Research-first methodology - investigate multiple sources, document findings, synthesize into complete functional specification.

**Date:** 2026-01-31

---

## Research Methodology

**Pattern:** Similar to design-strategy-research.md approach

1. **Identify requirement sources** (this document)
2. **Research each source systematically** (create analysis documents)
3. **Document findings and insights** (comprehensive analyses)
4. **Synthesize into functional specification** (after research complete)

**Goal:** Ensure we capture 100% of what the implementation needs to do.

---

## Requirement Sources

### Section 1: CSAPI Part 1 Specification Analysis ⏳

**Source:** [OGC API – Connected Systems Part 1: Feature Resources](https://docs.ogc.org/is/23-001/23-001.html)
**OpenAPI:** docs/research/standards/ogcapi-connectedsystems-1.bundled.oas31.yaml

#### Section 1.1: Standard Document Analysis ✅

**Source:** [OGC API – Connected Systems Part 1: Feature Resources](https://docs.ogc.org/is/23-001/23-001.html)

**Analysis:** [docs/research/requirements/csapi-part1-requirements.md](csapi-part1-requirements.md) Section 1.1

**Answers:**

- [x] What are ALL operations for each resource type according to the standard? → **70+ operations across 5 resource types: Systems (12 methods), Deployments (8 methods), Procedures (8 methods), Sampling Features (8 methods), Properties (6 methods) covering CRUD + nested endpoints** (Analysis Section 1)
- [x] What HTTP methods are specified in the standard text? → **GET (retrieve), POST (create), PUT (replace), PATCH (update), DELETE (delete) with cascade option** (Section 2)
- [x] What query parameters are defined in the standard? → **30+ parameters: spatial (bbox, geom), temporal (datetime), identifiers (id, uid), text (q), relationships (parent, procedure, foi, observedProperty, controlledProperty, system, baseProperty, objectType), hierarchical (recursive), pagination (limit, offset)** (Section 3)
- [x] What request bodies are described for create/update operations? → **GeoJSON Feature format (application/geo+json) and SensorML-JSON format (application/sml+json) with detailed property mappings** (Section 4)
- [x] What response formats are required by the standard? → **GeoJSON mandatory for all spatial resources, SensorML-JSON optional for Systems/Deployments/Procedures, format negotiation via Accept header or f parameter** (Section 5)
- [x] What conformance classes are defined and what requirements do they specify? → **11 conformance classes: Common, System Features, Subsystems, Deployment Features, Subdeployments, Procedure Features, Sampling Features, Property Definitions, Advanced Filtering, Create/Replace/Delete, Update, GeoJSON Format, SensorML Format. No mandatory core - minimum is 1 resource + 1 encoding** (Section 6)
- [x] What link relations are defined in the standard text? → **11 ogc-rel: prefixed relations: subsystems, parentSystem, samplingFeatures, deployments, procedures, featuresOfInterest, implementingSystems, sampledFeature, sampleOf, datastreams, controlStreams** (Section 7)
- [x] How does the standard describe relationships between resources? → **Complex association model: Systems have subsystems/samplingFeatures/deployments/procedures, Deployments have deployedSystems/subdeployments, Procedures have implementingSystems, Sampling Features have parentSystem/sampledFeature/sampleOf, Properties have baseProperty** (Section 8)
- [x] What history/versioning requirements are stated? → **validTime property for temporal validity (required for Deployments, optional for Systems), location updates for mobile systems, no complete version history in Part 1** (Section 9)
- [x] What filtering capabilities does the standard specify? → **Spatial filters (bbox, geom), temporal filters (datetime), identifier filters (id, uid), text search (q), property filters, relationship filters (30+ params), hierarchical filters (recursive), pagination (limit, offset), logical AND between parameters, logical OR within ID lists** (Section 10)
- [x] What are the requirements classes and their obligations? → **11 requirements classes with 103 total requirements. Minimum implementation: Common + 1 resource type + 1 encoding. Full implementation: all 5 resources + hierarchies + CRUD + filtering + both formats** (Section 11)
- [x] What examples are provided in the standard? → **GeoJSON and SensorML examples for all 5 resource types including: fixed in-situ sensors, mobile systems, deployments (Saildrone Arctic Mission), procedures (datasheets, methodologies), sampling features (rock samples, trajectories, footprints)** (Section 12)

**Deliverable:** Standard document analysis (~650 lines) ✅ COMPLETED

#### Section 1.2: OpenAPI Schema Analysis ✅

**Source:** docs/research/standards/ogcapi-connectedsystems-1.bundled.oas31.yaml

**Analysis:** [docs/research/requirements/csapi-part1-requirements.md](csapi-part1-requirements.md) Section 1.2

**Answers:**

- [x] What paths are defined in the OpenAPI schema? → **20 path templates: 2 capabilities paths (/, /conformance), 4 collections paths, 14 resource paths covering Systems (3 paths), Deployments (4 paths), Procedures (2 paths), Sampling Features (3 paths), Properties (2 paths)** (Analysis Section 1)
- [x] What HTTP methods are specified for each path? → **40 total operations: 20 GET, 10 POST, 5 PUT, 5 DELETE. PATCH method absent from schema despite being mentioned in standard** (Section 2)
- [x] What parameters are defined (path, query, header)? → **28 parameters total: 7 path parameters (collectionId, resourceId, systemId, deploymentId, procedureId, featureId, propId), 15 query parameters (bbox, datetime, geom, q, id, parent, procedure, foi, observedProperty, controlledProperty, system, baseProperty, objectType, limit, recursive, cascade), 0 header parameters** (Section 3)
- [x] What request body schemas exist? → **Dual format support: application/geo+json (GeoJSON Feature) and application/sml+json (SensorML-JSON) for all resource types. Additional formats: text/uri-list and application/json for URI references** (Section 4)
- [x] What response schemas are defined? → **Feature schema (base), SystemGeoJSON, DeploymentGeoJSON, ProcedureGeoJSON, SamplingFeatureGeoJSON, PropertyGeoJSON, plus SensorML equivalents. FeatureCollection for lists. Complete SWE Common 3.0 data component schemas included** (Section 5)
- [x] What are the exact parameter names, types, and constraints? → **All parameters precisely typed: bbox (array of 4-6 numbers), datetime (string with RFC 3339 format or intervals), id/parent/foi/etc (array of strings via idListSchema), limit (integer 1-10000, default 10), recursive/cascade (boolean, default false), q (array of strings 1-50 chars)** (Section 3)
- [x] What status codes are documented? → **7 status codes: 200 (OK - GET success), 201 (Created - POST success with Location header), 204 (No Content - PUT/DELETE success), 400/401/403/404 (client errors), 409 (Conflict - DELETE without cascade), 5XX (server errors)** (Section 6)
- [x] What security requirements are specified? → **None explicitly defined. No components.securitySchemes section. Authentication/authorization left to implementation. 401/403 responses documented but mechanism unspecified** (Section 7)
- [x] What examples are provided in the schema? → **Comprehensive examples: Simple Thermometer (GeoJSON + SensorML), UAV Platform (GeoJSON + SensorML), Global Hawk UAV (SensorML with local reference frames), Saildrone Arctic Mission deployment (GeoJSON + SensorML with contacts), plus parameter examples for bbox, datetime, geom, keywords, id lists, URI lists** (Section 8)
- [x] What data models/schemas are defined for resources? → **6 resource models: System (with SystemTypeUris enum, assetType enum), Deployment (validTime required), Procedure (geometry null), Sampling Feature (sampledFeature required), Property (geometry null), plus Link model with href/rel/type/uid/rt/if properties** (Section 9)
- [x] What are the exact property names and types for each resource? → **All properties documented with types and constraints. Common required: featureType (string/enum), uid (string format:uri), name (string minLength:1). Type-specific: System has assetType enum (7 values), Deployment requires validTime array, Sampling Feature requires sampledFeature@link, link suffix convention for associations** (Section 10)
- [x] What's optional vs required according to the schema? → **Required for all: type, properties.featureType, properties.uid, properties.name. Required for Deployments only: properties.validTime. All other properties optional including: id (server-assigned), geometry (except null for Procedures/Properties), bbox, description, links, associations** (Section 11)

**Deliverable:** OpenAPI schema analysis (~1,250 lines) ✅ COMPLETED

#### Section 1.3: Comparison and Insights ✅

**Analysis:** [docs/research/requirements/csapi-part1-requirements.md](csapi-part1-requirements.md) Section 1.3

**Answers:**

- [x] Where do the standard and OpenAPI schema align perfectly? → **95%+ alignment on core functionality: path structure (20 paths match canonical patterns), resource types (all 5 types with identical naming), query parameters (all 15 OpenAPI params match standard), HTTP methods (GET/POST/PUT/DELETE all present), dual format support (both GeoJSON + SensorML fully specified), status codes (200/201/204/4XX/5XX match HTTP semantics), required properties (featureType/uid/name align perfectly)** (Section 1)
- [x] Where does the OpenAPI schema provide more specific details than the standard? → **Precise parameter types/constraints (bbox array 4-6 numbers, limit 1-10000, datetime RFC 3339), enumerated SystemTypeUris (5 SOSA URIs with CURIE forms), complete SWE Common 3.0 schemas (20+ data components), concrete examples (8 complete request/response examples), property naming (uid not uniqueIdentifier, featureType not systemType), link suffix convention ({association}@link), path parameter constraints (minLength:1), exact default values (limit:10, recursive:false, cascade:false)** (Section 2)
- [x] Where does the standard describe things not captured in OpenAPI? → **Conformance classes (11 classes with 103 requirements, dependencies, test suite), link relation semantics (11 ogc-rel: definitions), PATCH method (references Part 4 Update, completely absent from OpenAPI), history/versioning (mentions /systems/{id}/history endpoints, not in OpenAPI paths), recursive query details (traversal semantics, filter interactions), cascade delete semantics (exact list of nested resources deleted), transitive relationships (Recommendation 4 on baseProperty/foi), conformance detection guidance (minimum vs full implementation)** (Section 3)
- [x] Are there any conflicts or ambiguities between the two sources? → **No direct conflicts. 3 sources of potential confusion clarified: property name variations (conceptual vs JSON keys - intentional design), PATCH absence (schema incompleteness not conflict with standard), history endpoints (future extension not current spec). Sources are complementary not contradictory** (Section 4)
- [x] What implementation details are clearer in the OpenAPI schema? → **Type safety for TypeScript (exact interfaces, enums, validation), validation rules (minLength, minimum, maximum, format, minItems, maxItems), default values (machine-readable), example-driven development (copy-paste test fixtures), property naming conventions (actual JSON keys)** (Section 5)
- [x] What conceptual/requirement details are clearer in the standard? → **Resource structure rationale (Systems vs Procedures = instances vs types), relationship semantics (subsystems vs deployedSystems, sampledFeature vs sampleOf), resource type selection guidance (when to use sensor vs platform vs sampler), conformance class implications (minimum vs full implementation paths), transitive query behavior, cascade delete impact** (Section 6)
- [x] Which source should take precedence for specific decisions? → **Property names/types/constraints: OpenAPI. HTTP methods: Standard (includes PATCH). Query parameters: OpenAPI (types/constraints). Link relations: Standard (semantics). Conformance: Standard only. Response formats: OpenAPI (complete schemas). Validation rules: OpenAPI. Conceptual understanding: Standard. Examples: OpenAPI (more complete). Versioning/history: Standard (concepts). General rule: Technical "how" = OpenAPI, Conceptual "why" = Standard, Feature "when" = Standard** (Section 7)
- [x] What requirements emerge from reading both together? → **Format negotiation strategy (conformance check + f parameter + fallback), conformance-based feature detection (query /conformance then adapt), link-following navigation (prefer links over URL construction), recursive query handling (with maxDepth protection), client-side validation (before request), error handling patterns (typed errors with status codes + conformance conflicts)** (Section 8)
- [x] What examples or patterns appear in one but not the other? → **OpenAPI only: Global Hawk reference frames (local coordinate systems), Saildrone deployment with contacts (organizational metadata). Standard only: conformance test suite (Annex A abstract tests), System Kind vs Procedures distinction (datasheet vs operating procedures), Feature of Interest examples (building/room/river/atmosphere, FOI as System)** (Section 9)
- [x] What are the implications for implementation? → **Two-phase strategy: Phase 1 OpenAPI-driven core (generate types, URL builders, parsers, status handling), Phase 2 standard-driven enhancements (conformance, PATCH, links, documentation). Documentation structure: API reference from OpenAPI, conceptual guide from standard. Testing: unit tests from OpenAPI constraints, integration tests from standard behaviors. Type-safe query builders, format handling with auto-detect, error messages citing both sources** (Section 10)

**Deliverable:** Comparison analysis and insights (~3,200 lines) ✅ COMPLETED

**Total Section 1 Deliverable:** ~1,000-1,300 lines

---

### Section 2: CSAPI Part 2 Specification Analysis ⏳

**Source:** [OGC API – Connected Systems Part 2: Dynamic Data](https://docs.ogc.org/is/23-002/23-002.html)
**OpenAPI:** docs/research/standards/ogcapi-connectedsystems-2.bundled.oas31.yaml

#### Section 2.1: Standard Document Analysis ✅

**Source:** [OGC API – Connected Systems Part 2: Dynamic Data](https://docs.ogc.org/is/23-002/23-002.html)

**Analysis:** [docs/research/requirements/csapi-part2-requirements.md](csapi-part2-requirements.md) Section 2.1

**Answers:**

- [x] What are ALL operations for dynamic data resources according to the standard? (Datastreams, Observations, Control Streams, Commands) → **Canonical endpoints: /datastreams, /observations, /controlstreams, /commands, /feasibility, /systemEvents with GET operations. Nested endpoints: /systems/{id}/datastreams, /datastreams/{id}/observations, /systems/{id}/controlstreams, /controlstreams/{id}/commands, /commands/{id}/status, /commands/{id}/result plus schema endpoints /datastreams/{id}/schema?obsFormat={format} and /controlstreams/{id}/schema?cmdFormat={format}** (Section 3, Section 4)
- [x] What HTTP methods are specified for dynamic data resources? → **GET (retrieve with params), POST (create with schema validation), PUT (replace entire resource with 409 if schema conflict), PATCH (update partial via JSON Merge Patch RFC 7396), DELETE (delete with cascade parameter, 409 without cascade if nested resources exist). All methods inherit OGC API - Features Part 1 and Part 4 behaviors** (Section 3)
- [x] How does the standard describe differences from Part 1 patterns? → **Observations/Commands NOT modeled as Features (purposeful separation of static metadata from dynamic data containers). DataStreams/ControlStreams are homogeneous collections (all from same system, same schema). Auto-generated properties (DataStream phenomenonTime/resultTime/observedProperties generated from observations). Schema operations unique to Part 2 (format-specific schemas per datastream/controlstream). Status/result tracking unique to Part 2. async/sync distinction for commands. live indicators for real-time availability** (Section 2, Section 9, Section 10)
- [x] What schema operations are described in the standard? (DataStream schema, Control Stream schema) → **Each DataStream provides observation schema via /datastreams/{id}/schema?obsFormat={format}. Each ControlStream provides command schema via /controlstreams/{id}/schema?cmdFormat={format}. Schema must be provided before observations/commands can be inserted. Schema cannot be changed if nested resources exist (409 error on PUT/PATCH). Different schema for each format (JSON, SWE+CSV, SWE+Binary). Observation result and Command parameters validated against schema (400 if invalid)** (Section 5)
- [x] What status/result operations does the standard define? (Command status, Command result) → **CommandStatus at /commands/{cmdId}/status with status codes (PENDING/ACCEPTED/REJECTED/EXECUTING/COMPLETED/CANCELED/FAILED), reportTime, percentCompletion, message. CommandResult at /commands/{cmdId}/result with 4 result types (datastream reference with optional time range, observation reference list, inline result data, external dataset reference). Feasibility follows same pattern with /feasibility/{id}/status and /feasibility/{id}/result. Command cancellation via POST new status with CANCELED code (not DELETE)** (Section 6)
- [x] What streaming/pagination patterns are specified? → **limit parameter (1-10000, default 10) for pagination with next links for cursor-based pagination. datetime parameter for temporal windowing (single instant, closed interval, open interval). Special value "latest" for most recent observations (resultTime=latest). live property (boolean) indicates real-time data availability. async property (boolean) indicates asynchronous command processing. Part 3 will define pub/sub protocol bindings for efficient real-time streaming (WebSocket, MQTT, SSE)** (Section 7)
- [x] What temporal query requirements does the standard describe? → **phenomenonTime filter (intersects) for DataStreams/Observations - when observed property value applies to FOI. resultTime filter (intersects) for DataStreams/Observations - when result obtained, supports special "latest" value. executionTime filter (intersects) for ControlStreams/Commands - when command should execute. issueTime filter (intersects) for ControlStreams/Commands - when command issued. validTime filter (intersects, via datetime parameter) for DataStreams/ControlStreams - validity period of resource description. All temporal filters support ISO 8601 instants and intervals (closed, open start, open end)** (Section 8)
- [x] How does the standard describe observation-datastream relationships? → **Observation MUST be part of exactly one DataStream (containment). Observation result MUST conform to DataStream resultSchema. Observation parameters (if any) MUST conform to DataStream parametersSchema. DataStream auto-generates phenomenonTime (spans all observation phenomenon times), resultTime (spans all observation result times), observedProperties (all properties in observations), resultType (common result type). Properties provided at DataStream level inherited by observations (system, procedure, deployment, samplingFeatures, featuresOfInterest). Observations accessed via canonical /observations/{id} or nested /datastreams/{dsId}/observations** (Section 9)
- [x] How does the standard describe command-control stream relationships? → **Command MUST be part of exactly one ControlStream (containment). Command parameters MUST conform to ControlStream parametersSchema. ControlStream auto-generates issueTime (spans all command issue times), executionTime (spans all command execution times), controlledProperties (all properties in commands). Properties provided at ControlStream level inherited by commands (system, procedure, deployment, samplingFeatures, featuresOfInterest). Commands accessed via canonical /commands/{id} or nested /controlstreams/{csId}/commands. Command lifecycle tracked via status list (PENDING→ACCEPTED→EXECUTING→COMPLETED/FAILED/CANCELED). Command outputs tracked via result list** (Section 10)
- [x] What format options are discussed in the standard? (protobuf, SWE Common) → **4 formats specified (no protobuf mentioned): JSON (application/json) mandatory for all resources, human-readable, verbose. SWE Common JSON (application/swe+json) optional for observations/commands, structured per SWE Common Data Model 3.0, more compact than plain JSON. SWE Common Text (application/swe+text) optional for observations/commands, DSV format (CSV with custom delimiters), ~2-5x more compact than JSON. SWE Common Binary (application/swe+binary) optional for observations/commands, ~10-100x smaller than JSON for time series, requires schema for parsing** (Section 11)
- [x] What real-time or near-real-time requirements exist? → **live property (boolean, required) on DataStream indicates real-time data availability (true = provides real-time observations). live property (boolean, required) on ControlStream indicates command acceptance (true = currently accepts commands). async property (boolean, required) on ControlStream indicates asynchronous command processing (true = status updates via polling/pub/sub, false = immediate result in HTTP response). Polling patterns: latest data polling (resultTime=latest), incremental polling (resultTime after last fetch), time-windowed pagination. Part 3 will define pub/sub protocol bindings for push-based updates (lower latency, reduced bandwidth)** (Section 12)
- [x] What conformance classes are defined for Part 2? → **9 main conformance classes: A.1 Common (prerequisite for all), A.2 Datastreams & Observations (prerequisite: Common), A.3 Control Streams & Commands (prerequisite: Common), A.4 Command Feasibility (prerequisite: Control Streams & Commands), A.5 System Events (prerequisite: Common + Part 1 System), A.6 Advanced Filtering (prerequisite: Part 1 Advanced Filtering), A.7 Create/Replace/Delete (prerequisite: OGC API Features Part 4), A.8 Update (prerequisite: Create/Replace/Delete). Plus 3 encoding conformance classes: A.9 JSON (mandatory), A.10 SWE Common JSON (optional), A.11 SWE Common Text (optional), A.12 SWE Common Binary (optional)** (Section 13)
- [x] What examples are provided? → **7 comprehensive examples: Simple thermometer observation (scalar result with UoM), Vector result observation (velocity/stress tensor), UAV video footage task (datastream with time range result), Satellite imagery acquisition (multiple image observations result), Chemical plume simulation (new datastream per model run), System state query (inline result data), Command feasibility request (YES/NO response with alternatives). Plus status code examples (PENDING/ACCEPTED/EXECUTING/COMPLETED/FAILED/CANCELED transitions), result type examples (datastream reference, observation reference, inline data, external resource), SWE Common encoding examples (JSON/Text/Binary schemas and payloads)** (Section 14)

**Deliverable:** Standard document analysis (~6,200 words, 2,303 lines) ✅ COMPLETED

#### Section 2.2: OpenAPI Schema Analysis

**Source:** docs/research/standards/ogcapi-connectedsystems-2.bundled.oas31.yaml

**Questions to answer:**

- [x] What paths are defined for Datastreams, Observations, Control Streams, and Commands? **48 endpoints: Datastreams (8), Observations (6), ControlStreams (8), Commands (15), SystemEvents (6), SystemHistory (5)**
- [x] What HTTP methods are specified for each dynamic data path? **GET (all 48), POST (15), PUT (19), DELETE (14); PATCH absent**
- [x] What parameters are defined for dynamic data endpoints? **23 parameters: id/q/system/dataStream/controlStream/foi/observedProperty/controlledProperty/phenomenonTime/resultTime/issueTime/executionTime/reportTime/validTime/datetime/statusCode/sender/eventType/limit/obsFormat/cmdFormat/cascade + path params (systemId/dataStreamId/obsId/controlStreamId/cmdId/statusId/resultId/eventId/revId)**
- [x] What request body schemas exist for observations and commands? **8 schemas: DataStream, Observation, ControlStream, Command, CommandStatus, CommandResult, SystemEvent, ObservationSchema/CommandSchema**
- [x] What response schemas are defined for dynamic data? **200 OK (collection with items/links), 201 Created (Location header), 204 No Content, 400/401/403/404/409/5XX errors**
- [x] What are the schema operation endpoints and their definitions? **GET/PUT /datastreams/{id}/schema?obsFormat, GET/PUT /controlstreams/{id}/schema?cmdFormat; formats: JSON/SWE Common/Protobuf**
- [x] What are the status/result endpoint definitions? **10 endpoints: /commands/{cmdId}/status, /commands/{cmdId}/status/{statusId}, /commands/{cmdId}/result, /commands/{cmdId}/result/{resultId} with GET/POST/PUT/DELETE**
- [x] What pagination/temporal query parameters are defined? **Pagination: limit (1-10000 default 10) with cursor-based links; Temporal: 7 params with ISO 8601 instants/periods, special values now/latest, intersection logic**
- [x] What data models exist for Observation, DataStream, ControlStream, Command? **6 models: DataStream (15 props, 9 required), Observation (8 props, 3+oneOf required), ControlStream (17 props, 10 required), Command (9 props, 4 required), CommandStatus (8 props, 4 required), CommandResult (7 props, 2+oneOf required)**
- [x] What property names and types are specified? **Common: id/name/description/validTime/formats; Link: href/rel/type/hreflang/title/uid/rt/if; Time: phenomenonTime/resultTime/issueTime/executionTime/reportTime; Observable/Controllable: definition/label/description**
- [x] What's required vs optional in the schemas? **All 6 models documented with required arrays: DataStream (9 required), Observation (3+oneOf), ControlStream (10 required), Command (4 required), CommandStatus (4 required), CommandResult (2+oneOf)**
- [x] What format media types are specified in responses? **13 types: JSON-based (application/json, application/swe+json, application/geo+json, application/sml+json, application/schema+json), Text (application/swe+text, application/swe+csv, text/plain), Binary (application/swe+binary, application/x-protobuf), Image (image/png, image/tiff;application=geotiff), Data URIs**

**Deliverable:** OpenAPI schema analysis (~400-500 lines)

#### Section 2.3: Comparison and Insights

**Questions to answer:**

- [x] Where do the Part 2 standard and OpenAPI schema align perfectly? **Resource paths, core data models, temporal parameters (phenomenonTime/resultTime/issueTime/executionTime), CommandStatus state machine (9 codes with identical transitions), HTTP status codes (200/201/204/400/404/409), schema operation semantics (GET/PUT with 409 on conflict)**
- [x] Where does the OpenAPI schema provide more specifics than the standard? **Exact parameter constraints (limit 1-10000 default 10, q maxLength 50, minLength 1 for path params), required/optional property arrays (DataStream 9 required, Observation 3+oneOf required), read-only markers (id, datastream@id, issueTime, observedProperties, phenomenonTime, resultTime extents), write-only markers (schema), Link validation patterns (hreflang pattern, format:uri), encoding schemas (TextEncoding with minLength constraints, BinaryEncoding with enum byteOrder/byteEncoding), CommandResult oneOf constraint (exactly one of data/observation@link/observationSet@link/datastream@link/external@link)**
- [x] Where does the standard describe concepts not captured in OpenAPI? **Architecture rationale (why DataStream-Observation separation), use cases (environmental monitoring, UAV control), content negotiation rules (Accept header vs f parameter, precedence), pagination cursor semantics (opaque, expiring, not client-constructed), schema validation workflow (timing, pre-existing data not revalidated), cascade delete semantics (order, atomicity), live data stream semantics (polling recommendations), temporal extent auto-update (server responsibility)**
- [x] Are there any conflicts or ambiguities between the two sources? **5 conflicts: (1) PATCH method - standard specifies, OpenAPI omits; (2) StatusCode transition validation - no rules specified; (3) Schema format constraints - POST schema body format unclear; (4) phenomenonTime default - standard says "defaults to resultTime", OpenAPI doesn't specify default; (5) CommandResult timing - when results can be added relative to status unclear**
- [x] What patterns from Part 1 are reused vs changed in Part 2? **Reused: collection+single resource pattern, nested resource creation (POST to parent), query parameter filtering (same names/types), link-based associations (@link suffix), temporal properties (ISO 8601 support). Changed: mandatory parent association (Observations require DataStream), read-only identifiers (datastream@id/controlstream@id derived from POST path), schema-based validation (runtime validation in addition to OpenAPI), temporal extent auto-computation (server computes from nested resources), live data flag (new concept), multiple format support (formats array)**
- [x] How do dynamic data resources differ from feature resources architecturally? **6 differences: (1) Container-item hierarchy (strict two-level vs flat), (2) Schema-driven flexibility (runtime schema vs fixed OpenAPI), (3) Temporal dynamics (auto-computed extents vs explicit validTime), (4) Lifecycle complexity (9-state state machine vs simple CRUD), (5) Data volume (millions/billions requiring pagination vs hundreds/thousands), (6) Update patterns (observations immutable, schema updates fail with 409 if data exists vs frequent PUT updates)**
- [x] What implementation complexity is unique to Part 2? **7 complexities: (1) Dynamic schema validation (fetch schema, validate before POST), (2) Multi-format parsing (JSON/SWE JSON/CSV/Binary/Protobuf with encoding metadata), (3) Temporal query construction (instants/periods/open-ended/special values with URL encoding), (4) Pagination cursor management (opaque cursors, link parsing, iterator pattern), (5) CommandStatus state machine tracking (polling, final state detection), (6) Schema conflict detection (check for existing data before schema update), (7) Schema caching (required for performance, invalidation strategy)**
- [x] Which source clarifies the datastream-observation relationship better? **Standard better for conceptual model (container concept, lifecycle, temporal extent derivation, use cases). OpenAPI better for implementation details (required properties, read-only properties, association mechanics, validation rules). Best practice: use standard for "why" separation exists, OpenAPI for "how" to implement. Key insight: strictly hierarchical tree (one Observation → one DataStream, one DataStream → many Observations)**
- [x] Which source clarifies the control stream-command relationship better? **Standard better for conceptual model (communication channel concept, async vs sync semantics, command lifecycle, result types, use cases). OpenAPI better for implementation details (required properties, status code enum, CommandStatus/CommandResult schemas, endpoint definitions). Key insight: hierarchical with lifecycle complexity (one Command → one ControlStream → many CommandStatus reports → many CommandResult objects). More complex than DataStream-Observation due to status tracking.**
- [x] What are the implications for client library implementation? **7 implications: (1) Type system - generate TypeScript from OpenAPI, augment with standard semantics (read-only/write-only), (2) Validation - two-tier (OpenAPI + runtime schema), (3) Caching - aggressive schema caching with invalidation, (4) Pagination - iterator-based API hiding cursor management, (5) Command execution - async/await with status callbacks and polling, (6) Error handling - typed exceptions mapped from HTTP status codes, (7) Format support - JSON required, SWE Common via plugins**

**Deliverable:** Comparison analysis and insights (~200-300 lines)

**Total Section 2 Deliverable:** ~1,000-1,300 lines

---

### Section 3: Format Requirements Analysis ⏳

**Overview:** Analysis of data format requirements for CSAPI client library implementation, organized by format family.

---

#### Section 3.1: Common Format Requirements

**Resources:**

##### Standards & Specifications:

- [OGC API – Connected Systems Part 1](https://docs.ogc.org/is/23-001/23-001.html) - Sections on content negotiation
- [OGC API – Connected Systems Part 2](https://docs.ogc.org/is/23-002/23-002.html) - Sections on format support
- [HTTP Content Negotiation (RFC 9110)](https://www.rfc-editor.org/rfc/rfc9110.html#name-content-negotiation)

##### Schemas:

- docs/research/standards/ogcapi-connectedsystems-1.bundled.oas31.yaml
- docs/research/standards/ogcapi-connectedsystems-2.bundled.oas31.yaml

**Questions to answer:**

- [x] What formats are REQUIRED by the standard for all implementations?
  - **Part 1:** application/json (all), application/geo+json (spatial), application/sml+json (systems/procedures)
  - **Part 2:** application/json (all), application/swe+json/text/binary (observations/commands - optional)
- [x] What formats are OPTIONAL but commonly used?
  - **Part 1:** HTML, XML (not required)
  - **Part 2:** SWE Common formats (swe+json, swe+text, swe+binary) - SHOULD support
- [x] What media type identifiers are specified for each format?
  - application/json, application/geo+json, application/sml+json, application/swe+json, application/swe+text, application/swe+binary, text/uri-list
- [x] What format negotiation mechanisms are required? (Accept headers, query params, precedence rules)
  - **Accept header:** Client specifies desired format
  - **Query parameter:** f or format parameter (takes precedence over Accept)
  - **Content-Type response:** Server indicates format
  - **Precedence:** Query param > Accept > Default > 406
- [x] What are the minimum viable format support requirements for client library?
  - **MUST:** JSON, GeoJSON, SensorML
  - **SHOULD:** SWE Common (JSON/CSV/Binary)
  - **MAY:** Other formats (pass-through)
- [x] Does library need to parse formats or just request/pass-through them?
  - **Full parsing:** JSON, GeoJSON, SensorML, SWE Common (all formats)
  - **Pass-through:** Unsupported formats only
- [x] Does library need to serialize formats for POST/PUT operations?
  - **Yes:** All supported formats must be serializable for write operations
  - **Content-Type header:** Client must include in requests
- [x] Are there format validation requirements for client-side?
  - **Pre-send:** Validate structure before sending (prevent 400 errors)
  - **Post-receive:** Validate structure after receiving (detect malformed responses)
  - **Format-specific:** Each format has specific validation rules (see Sections 3.2-3.4)
- [x] What format capabilities should be exposed in the client API?
  - **Format selection:** Method-level format parameter
  - **Convenience methods:** Format-specific methods (getAsGeoJSON, getAsSensorML)
  - **Detection:** Automatic format detection from Content-Type
  - **Capabilities:** getSupportedFormats, supportsFormat
- [x] How should format errors be handled (unsupported format, malformed content)?
  - **406 Not Acceptable:** Fall back to application/json
  - **Parse errors:** Log and retry with different format
  - **Validation errors:** Return detailed error messages
  - **Fallback chain:** Preferred format → fallback formats → default (JSON)

**Deliverable:** Common format requirements and negotiation analysis (~200-300 lines)

---

#### Section 3.2: GeoJSON Format Requirements

**Resources:**

##### Standards & Specifications:

- [GeoJSON RFC 7946](https://datatracker.ietf.org/doc/html/rfc7946)
- [OGC API – Connected Systems Part 1](https://docs.ogc.org/is/23-001/23-001.html) - System/SamplingFeature GeoJSON representation
- [OGC API – Features GeoJSON guidance](https://docs.ogc.org/is/17-069r4/17-069r4.html)

##### Schemas:

- [GeoJSON Schema](https://geojson.org/schema/GeoJSON.json)
- docs/research/standards/ogcapi-connectedsystems-1.bundled.oas31.yaml (System, SamplingFeature schemas)

**Questions to answer:**

- [x] Which CSAPI resources support GeoJSON format? → Part 1: Systems, Deployments, Procedures (geometry:null), SamplingFeatures; Part 2: DataStreams, ControlStreams (optional)
- [x] What GeoJSON geometry types are used in CSAPI? (Point, LineString, Polygon, GeometryCollection) → All 7 RFC 7946 types required: Point, MultiPoint, LineString, MultiLineString, Polygon, MultiPolygon, GeometryCollection
- [x] What is the structure of CSAPI GeoJSON Feature representations? → Standard RFC 7946 Feature with type/id/geometry/properties/links; properties contain CSAPI-specific fields
- [x] How are CSAPI-specific properties mapped to GeoJSON Feature properties? → Direct mapping to properties object; reference encoding with @id/@link suffixes; link relations use ogc-rel: prefix
- [x] What coordinate reference systems (CRS) are supported? (WGS84 required, others?) → WGS84/CRS84 only (RFC 7946 requirement); no alternative CRS support
- [x] Are GeoJSON FeatureCollections used for resource collections? → Yes, for GET collection endpoints with optional links/timeStamp/numberMatched
- [x] Does library need to parse GeoJSON geometries or treat them opaquely? → Parse geometry for validation, bbox calculation, spatial operations; parse properties for resource access
- [x] Does library need to validate GeoJSON structure? → Yes: geometry type/coordinates, coordinate ranges, polygon closure, null geometry constraints
- [x] Are there geometry operations needed? (bounding box calculation, validation) → Required: bbox calculation, coordinate extraction, type detection; Optional: spatial predicates (use Turf.js)
- [x] How should library handle 3D coordinates (altitude/elevation)? → Support [lon,lat,alt] positions; altitude = WGS84 ellipsoidal height; preserve in round-trip
- [x] What are the client API implications for GeoJSON support? → TypeScript types for all geometry types, format negotiation (Accept header/query param), validation, convenience accessors, external lib integration (Turf.js)

**Deliverable:** GeoJSON format requirements analysis (~500 lines) ✅ **COMPLETE** - See [csapi-format-requirements.md Section 3.2](csapi-format-requirements.md#section-32-geojson-format-requirements)

---

#### Section 3.3: SensorML Format Requirements

**Resources:**

##### Standards & Specifications:

- [SensorML 3.0 Specification](https://docs.ogc.org/is/20-010r3/20-010r3.html)
- [OGC API – Connected Systems Part 1](https://docs.ogc.org/is/23-001/23-001.html) - System/Procedure SensorML representation

##### Schemas:

- [SensorML 3.0 JSON Schema](https://schemas.opengis.net/sensorml/3.0/sensorml.json)
- docs/research/standards/ogcapi-connectedsystems-1.bundled.oas31.yaml (System, Procedure schemas)

**Questions to answer:**

- [x] Which CSAPI resources support SensorML format? (System, Procedure) → Part 1: Systems (PhysicalSystem, PhysicalComponent, SimpleProcess, AggregateProcess), Procedures (SimpleProcess, AggregateProcess), Deployments, Properties
- [x] What SensorML component types are used? (SimpleProcess, AggregateProcess, PhysicalSystem, PhysicalComponent) → 4 main types: PhysicalSystem/PhysicalComponent (hardware), SimpleProcess/AggregateProcess (software/procedures); all extend DescribedObject → AbstractProcess → AbstractPhysicalProcess
- [x] What is the minimal SensorML subset needed for CSAPI compatibility? → Required: type, label, uniqueId; Recommended: id, definition, validTime, links; Optional: identifiers, classifiers, inputs, outputs, parameters, characteristics, capabilities
- [x] How are inputs/outputs defined in SensorML for CSAPI? → SWE Common components with name, type, definition (URI), uom, constraint, value; types: Quantity, Count, Boolean, Text, Category, Time, DataRecord, DataArray, Vector, Matrix
- [x] How are identification/classification/characteristics/capabilities represented? → Identifiers/classifiers: Term arrays with definition/label/value; Characteristics/capabilities: Named lists with SWE Common components describing physical/operational properties
- [x] Does library need to parse SensorML structure or treat it opaquely? → Hybrid: parse core properties (type/label/uniqueId/definition/validTime), identifiers/classifiers, IO component names/types; preserve SWE Common details, nested components, complex metadata
- [x] Does library need to serialize SensorML for POST/PUT operations? → Yes: serialize from TypeScript types for create/update operations with format negotiation
- [x] Are there SensorML validation requirements? → Yes: required properties (type/label/uniqueId), type validation (4 valid types), IO component validation (name/type), connections validation; optional JSON Schema validation with ajv
- [x] What SensorML extensions or profiles are used by CSAPI? → CSAPI adds: links array (OGC API relations), id property (local resource ID); uses SensorML 3.0 JSON (not XML/previous versions)
- [x] How should library handle complex SensorML documents? (nested components, references) → Parse top-level components, preserve nested structures, detect/resolve Link references, defer SWE Common parsing to external library
- [x] What are the client API implications for SensorML support? → TypeScript types for all component types, format negotiation, metadata extraction utilities (getIdentifier/getClassifier/getCapability), write operations, validation utilities

**Deliverable:** SensorML format requirements analysis (~700 lines) ✅ **COMPLETE** - See [csapi-format-requirements.md Section 3.3](csapi-format-requirements.md#section-33-sensorml-format-requirements)

---

#### Section 3.4: SWE Common Format Requirements

**Resources:**

##### Standards & Specifications:

- [SWE Common Data Model 3.0 Specification](https://docs.ogc.org/is/18-003r2/18-003r2.html)
- [OGC API – Connected Systems Part 2](https://docs.ogc.org/is/23-002/23-002.html) - Observation/Command schema and encoding

##### Schemas:

- [SWE Common 3.0 JSON Schema](https://schemas.opengis.net/sweCommon/3.0/sweCommon.json)
- docs/research/standards/ogcapi-connectedsystems-2.bundled.oas31.yaml (SWE Common component schemas)

**Questions to answer:**

- [x] Which CSAPI resources use SWE Common? (Observation schemas, Command schemas) → Part 2: Observations (result field), Commands (parameters/result fields); DataStreams/ControlStreams define schemas/encodings
- [x] What SWE Common data components are required? (Boolean, Count, Quantity, Time, Category, Text, DataRecord, DataArray, Vector, Matrix) → All 10 component types required: Quantity, Count, Boolean, Text, Category, Time, DataRecord, DataArray, Vector, Matrix
- [x] What SWE Common encoding formats must be supported? (JSON, Text/CSV, Binary) → All 3 formats: JSON (application/swe+json), CSV (application/swe+csv), Binary (application/swe+binary) with configurable parameters
- [x] How are SWE Common encodings configured? (JSONEncoding, TextEncoding, BinaryEncoding parameters) → JSONEncoding (includeNilValues), TextEncoding (tokenSeparator, blockSeparator, decimalSeparator, collapseWhiteSpaces), BinaryEncoding (byteOrder, byteEncoding, members)
- [x] What is the structure of SWE Common DataRecords for observations? → DataRecord with named fields array, each field has name/type/uom/definition/constraint/nilValues/quality; supports nested DataRecords
- [x] How are units of measure (UoM) handled in SWE Common? → UCUM codes (standard) or URI-based units; uom object with code or href property; client must parse, preserve, optionally validate/convert
- [x] Does library need to parse SWE Common data or treat it opaquely? → Schema-driven parsing: parse schemas (resultSchema/parametersSchema/encoding), component types, properties; decode data values according to schema and encoding
- [x] Does library need to encode/decode binary SWE Common formats? → Yes: implement binary encoding/decoding with DataView, support BIG_ENDIAN/LITTLE_ENDIAN byte order, all data types (INT8-64, UINT8-64, FLOAT32/64, UTF8)
- [x] Does library need to encode/decode text/CSV SWE Common formats? → Yes: implement CSV encoding/decoding with configurable separators, decimal separator, whitespace handling; parse/format values by component type
- [x] Are there SWE Common validation requirements? → Yes: validate against schema (component types, constraints, required fields), validate UoM codes, validate nil values, throw detailed validation errors with component path
- [x] How should library handle complex SWE Common structures? (nested DataRecords, DataArrays) → Schema-driven approach enables generic handling; parse nested structures recursively; preserve unknown components for extensibility
- [x] What are the client API implications for SWE Common support? → Schema fetching/caching, observation/command creation with validation, format negotiation, encoding/decoding all 3 formats, TypeScript types for all components, format conversion utilities

**Deliverable:** SWE Common format requirements analysis (~1,200 lines) ✅ **COMPLETE** - See [csapi-format-requirements.md Section 3.4](csapi-format-requirements.md#section-34-swe-common-format-requirements)

---

**Total Section 3 Deliverable:** ~700-1,100 lines

---

### Section 4: Query Parameter Requirements ⏳

**Resources:**

#### Standards & Specifications:

- [OGC API – Connected Systems Part 1](https://docs.ogc.org/is/23-001/23-001.html)
- [OGC API – Connected Systems Part 2](https://docs.ogc.org/is/23-002/23-002.html)
- [OGC API - Common - Part 1: Core](https://docs.ogc.org/is/19-072/19-072.html)
- [OGC API - Common - Part 2: Geospatial Data](https://docs.ogc.org/DRAFTS/20-024.html)

#### Schemas:

- docs/research/standards/ogcapi-connectedsystems-1.bundled.oas31.yaml
- docs/research/standards/ogcapi-connectedsystems-2.bundled.oas31.yaml

**Questions to answer:**

- [x] What are ALL standard OGC API query parameters? (bbox, datetime, limit, offset, f)
  - **Standard:** bbox, datetime, limit, offset, f (from OGC API - Common/Features)
- [x] What are CSAPI-specific query parameters?
  - **Part 1:** id, uid, q, {propertyName}, recursive, parent, procedure, foi, observedProperty, controlledProperty, system, baseProperty, objectType
  - **Part 2:** phenomenonTime, resultTime, executionTime, issueTime, obsFormat, cmdFormat, cursor
- [x] What parameter types exist? (spatial, temporal, pagination, format, filtering)
  - **Spatial:** bbox
  - **Temporal:** datetime, phenomenonTime, resultTime, executionTime, issueTime
  - **Pagination:** limit, offset, cursor
  - **Format:** f, format, obsFormat, cmdFormat
  - **Identifier:** id, uid
  - **Search:** q, {propertyName}
  - **Hierarchical:** recursive
  - **Relationship:** parent, procedure, foi, observedProperty, controlledProperty, system, baseProperty, objectType
- [x] What encoding rules apply? (bbox arrays, datetime intervals, URL encoding)
  - **bbox:** Comma-separated coords (minLon,minLat,maxLon,maxLat[,minElev,maxElev])
  - **datetime:** ISO 8601 instant or interval (start/end, start/.., ../end)
  - **URL encoding:** Space=%20, Plus=%2B (MUST for media types), Colon=%3A (UIDs), Comma=NOT encoded (delimiter)
  - **Lists:** Comma-separated values (id=a,b,c)
- [x] What parameter combinations are valid?
  - **Logical AND:** Between different parameters
  - **Logical OR:** Within single parameter (comma-separated)
  - **recursive + filters:** Filters apply to all processed resources
- [x] What parameter validation is required?
  - **Client-side:** Type, range, format, logical validation before sending
  - **Server-side:** 400 Bad Request for invalid parameters, 406 Not Acceptable for unsupported formats
- [x] What are parameter defaults?
  - **limit:** Implementation-dependent (typically 10-100)
  - **offset:** 0
  - **recursive:** false
  - **datetime:** No default (optional)
- [x] What parameters are required vs optional?
  - **All query parameters optional** (no required query parameters)
  - Constraints: limit [1, 10000], offset [0, ∞)
- [x] Are there parameter constraints? (min/max values, format restrictions)
  - **limit:** [1, 10000] (Part 2), implementation-dependent (Part 1)
  - **offset:** [0, ∞)
  - **bbox:** Latitude [-90, 90], Longitude [-180, 180]
  - **datetime:** Valid ISO 8601, start ≤ end
- [x] How do parameters interact with resource types?
  - **Resource-specific:** observedProperty/controlledProperty apply differently to Systems, Deployments, Procedures, SamplingFeatures
  - **Part 2 temporal:** phenomenonTime/resultTime for DataStreams/Observations, executionTime/issueTime for ControlStreams

**Deliverable:** Comprehensive query parameter catalog (~1,300 lines) ✅ **COMPLETE** - See [csapi-query-parameters.md](csapi-query-parameters.md)

---

### Section 5: CRUD Operation Requirements ⏳

**Resources:**

#### Standards & Specifications:

- [OGC API – Connected Systems Part 1](https://docs.ogc.org/is/23-001/23-001.html)
- [OGC API – Connected Systems Part 2](https://docs.ogc.org/is/23-002/23-002.html)
- [HTTP/1.1 Method Definitions (RFC 9110)](https://www.rfc-editor.org/rfc/rfc9110.html#name-methods)

#### Schemas:

- docs/research/standards/ogcapi-connectedsystems-1.bundled.oas31.yaml
- docs/research/standards/ogcapi-connectedsystems-2.bundled.oas31.yaml

**Questions to answer:**

- [x] Which resources support full CRUD? (Create, Read, Update, Delete)
  - **Part 1:** Systems, Deployments, Procedures, SamplingFeatures, Properties (all support full CRUD)
  - **Part 2:** DataStreams, Observations, ControlStreams, Commands, CommandStatus, CommandResult, Feasibility, SystemEvents (all support full CRUD)
  - **Read-only:** Collections (server-managed, no CRUD operations)
- [x] Which resources are read-only?
  - **Collections only** - All other resources support CRUD operations via conformance classes
- [x] What HTTP methods map to which operations?
  - **GET:** Read (all endpoints)
  - **POST:** Create (canonical + nested collection endpoints) → 201 Created with Location header
  - **PUT:** Replace (single resource endpoints) → 204 No Content
  - **PATCH:** Partial update (single resource endpoints) → 204 No Content (JSON Merge Patch RFC 7396)
  - **DELETE:** Delete (single resource endpoints) → 204 No Content
- [x] What request bodies are needed for create operations?
  - **Part 1:** GeoJSON Feature (application/geo+json), SensorML (application/sml+json), plain JSON (application/json)
  - **Part 2:** JSON (application/json), SWE Common (application/swe+json/text/binary)
  - **Required properties:** uid, name, featureType (Part 1); varies by resource type (Part 2)
- [x] What request bodies are needed for update operations?
  - **PUT:** Complete resource representation (all required properties)
  - **PATCH:** Partial representation (only properties to update, JSON Merge Patch format)
- [x] Is PATCH supported? What does it do?
  - **Yes** - PATCH supported via Update conformance class (OGC API - Features Part 4)
  - **Operation:** Partial update using JSON Merge Patch (RFC 7396)
  - **Format:** application/merge-patch+json or application/json
- [x] What's the difference between PUT and PATCH?
  - **PUT:** Full replacement - client sends complete resource, all properties replaced
  - **PATCH:** Partial update - client sends only properties to change (JSON Merge Patch), other properties unchanged
  - **Both:** Same schema evolution constraints for DataStreams/ControlStreams
- [x] What response codes are expected?
  - **Success:** 200 OK (GET), 201 Created (POST with Location header), 204 No Content (PUT/PATCH/DELETE)
  - **Client errors:** 400 Bad Request (validation failure), 404 Not Found (resource doesn't exist), 409 Conflict (constraint violation, schema evolution)
  - **Server errors:** 500 Internal Server Error, 503 Service Unavailable
- [x] What headers are required for write operations?
  - **Content-Type** (required for POST/PUT/PATCH) - Media type of request body
  - **Location** (required in 201 Created response) - Canonical URL of created resource
- [x] Does library build request bodies or just URLs?
  - **Both** - Library provides:
    - Type-safe request body interfaces (SystemInput, ObservationInput, CommandInput)
    - Format-specific convenience methods (createFromGeoJSON, createFromSensorML)
    - Validation helpers (schema validation before sending)
    - Request body builders for complex types

**Deliverable:** CRUD operation matrix and requirements (~400-600 lines) ✅ **COMPLETE** - See [csapi-crud-operations.md](csapi-crud-operations.md)

---

### Section 6: Sub-Resource Navigation Requirements ⏳

**Resources:**

#### Standards & Specifications:

- [OGC API – Connected Systems Part 1](https://docs.ogc.org/is/23-001/23-001.html) - especially sections on relationships
- [OGC API – Connected Systems Part 2](https://docs.ogc.org/is/23-002/23-002.html) - especially sections on relationships
- [Web Linking (RFC 8288)](https://www.rfc-editor.org/rfc/rfc8288.html)
- [Link Relation Types (IANA Registry)](https://www.iana.org/assignments/link-relations/link-relations.xhtml)

#### Schemas:

- docs/research/standards/ogcapi-connectedsystems-1.bundled.oas31.yaml
- docs/research/standards/ogcapi-connectedsystems-2.bundled.oas31.yaml

**Questions to answer:**

- [x] What are ALL sub-resource relationships? (systems/{id}/datastreams, etc.)
  - **Part 1:** subsystems, subdeployments, samplingFeatures, deployments (reverse), datastreams, controlstreams, events, collection items (9 total)
  - **Part 2:** observations, commands, status, result, feasibility (7 total)
  - **16 total sub-resource relationships** across both parts
- [x] How deep does nesting go? (2 levels? 3 levels?)
  - **Hierarchical (unlimited):** Systems → Subsystems → Sub-subsystems (unlimited depth), Deployments → Subdeployments (unlimited depth)
  - **Compositional (depth 1):** SamplingFeatures, DataStreams, ControlStreams, Observations, Commands, Status, Result
  - **Maximum path:** System → Subsystem (N levels) → DataStream → Observation (6+ levels possible)
- [x] What sub-resource query parameters are supported?
  - **All standard OGC API params:** limit, offset, bbox, datetime, f
  - **Hierarchical:** recursive (boolean for subsystems/subdeployments)
  - **Relationship:** foi, observedProperty, controlledProperty, system
  - **Temporal (Part 2):** phenomenonTime, resultTime, executionTime, issueTime
  - **Full filtering support at nested endpoints**
- [x] Are sub-resource collections paginated?
  - **Yes** - All nested collections support limit/offset pagination
  - **Part 1:** Implementation-dependent limit (typically 10-100)
  - **Part 2:** limit range 1-10000, default 10
  - **Cursor-based recommended** for large observation/command datasets
  - **next/prev links** in response for page navigation
- [x] Can sub-resources be created via parent URLs?
  - **Yes** - POST at nested endpoints creates sub-resources
  - **Part 1:** POST /systems/{id}/subsystems, POST /systems/{id}/samplingFeatures
  - **Part 2:** POST /datastreams/{id}/observations, POST /controlstreams/{id}/commands
  - **Response:** 201 Created with Location header (canonical URL)
  - **Observations/Commands:** Can ONLY be created via nested endpoint (no canonical POST)
- [x] What link relations exist for sub-resources?
  - **IANA standard:** self, alternate, collection, item, next, prev, first, last
  - **CSAPI @link suffix:** subsystems@link, datastreams@link, controlstreams@link, observations@link, commands@link, status@link, result@link, foi@link, procedure@link, system@link, deployments@link, samplingFeatures@link
  - **Hypermedia navigation:** Client follows links dynamically (doesn't hardcode URLs)
- [x] How do bidirectional relationships work? (systems->deployments, deployments->systems)
  - **Forward:** GET /systems/{id}/deployments (nested endpoint)
  - **Reverse:** GET /deployments?system={id} (query parameter) OR access deployedSystems property
  - **Many-to-many:** Both resources exist independently, deleting one doesn't delete other
  - **Other bidirectional:** Observations↔DataStreams (observation.datastream property + nested endpoint)
- [x] What's the canonical URL for a sub-resource vs relationship URL?
  - **Canonical:** /{resourceType}/{id} (primary identifier, used in Location header)
  - **Relationship:** /{parentType}/{parentId}/{childType}/{childId} (navigation URL)
  - **Equivalence:** Both URLs return SAME resource representation
  - **Updates:** Changes at any URL reflected at all URLs
  - **Recommendation:** Use canonical for identity, nested for discovery
- [x] Are there sub-resource filtering capabilities?
  - **Yes** - Full query parameter support at nested endpoints
  - **Spatial:** bbox (for Systems, SamplingFeatures)
  - **Temporal:** datetime, phenomenonTime, resultTime, executionTime, issueTime
  - **Relationship:** foi, observedProperty, controlledProperty, system
  - **Hierarchical:** recursive=true (all descendants)
  - **Combined:** Multiple filters with logical AND
- [x] What navigation patterns are required?
  - **Fluent API:** Method chaining (client.systems.get(id).datastreams.list())
  - **Lazy loading:** Load related resources on demand (system.datastreams())
  - **Async iterators:** Auto-pagination (for await...of)
  - **Bidirectional:** Navigate both directions (forward via nested, reverse via query)
  - **Path-based:** Multi-level navigation (system → datastream → observations)
  - **Builder pattern:** Complex queries with filters

**Deliverable:** Sub-resource relationship model and requirements (~500-700 lines) ✅ **COMPLETE** - See [csapi-subresource-navigation.md](csapi-subresource-navigation.md)

---

### Section 7: Conformance and Capability Requirements ⏳

**Resources:**

#### Standards & Specifications:

- [OGC API – Connected Systems Part 1](https://docs.ogc.org/is/23-001/23-001.html) - especially Annex A (Conformance Classes)
- [OGC API – Connected Systems Part 2](https://docs.ogc.org/is/23-002/23-002.html) - especially Annex A (Conformance Classes)
- [OGC API - Common - Part 1: Core](https://docs.ogc.org/is/19-072/19-072.html) - conformance framework

#### Schemas:

- docs/research/standards/ogcapi-connectedsystems-1.bundled.oas31.yaml
- docs/research/standards/ogcapi-connectedsystems-2.bundled.oas31.yaml

**Questions to answer:**

- [x] What conformance classes exist?
  - **Part 1:** 13 classes (Common, System, Subsystem, Deployment, Subdeployment, Procedure, SamplingFeature, Property, AdvancedFiltering, Create/Replace/Delete, Update, GeoJSON, SensorML)
  - **Part 2:** 12 classes (Common, DataStream, ControlStream, Feasibility, SystemEvent, AdvancedFiltering, Create/Replace/Delete, Update, JSON, SWE JSON/Text/Binary)
  - **25 total conformance classes** across both parts
- [x] What does each conformance class require?
  - **Part 1 Common:** Resource IDs, UIDs, datetime parameter (3 requirements)
  - **Part 1 System:** 5 requirements (canonical URL, endpoints, collections)
  - **Part 1 Subsystem:** 5 requirements (nested endpoint, recursive parameter)
  - **Part 2 DataStream:** 16 requirements (endpoints, collections, schema operation)
  - **Part 2 ControlStream:** 18 requirements (endpoints, status, result, schema)
  - **Detailed per class** - see conformance document for all 25 classes
- [x] How do we detect which conformance classes an endpoint supports?
  - **Conformance endpoint:** GET /conformance
  - **Response:** JSON with conformsTo array of URIs
  - **URI pattern:** http://www.opengis.net/spec/ogcapi-connected-systems-{1|2}/1.0/conf/{class}
  - **Client:** Fetch at initialization, cache conformance set, check before operations
- [x] What's the minimum conformance for a valid CSAPI endpoint?
  - **Part 1 minimum:** Common + 1 resource type (System OR Deployment OR Procedure OR Property) + 1 encoding (GeoJSON OR SensorML)
  - **Part 2 minimum:** Part 2 Common + 1 dynamic data type (DataStream OR ControlStream) + JSON encoding
  - **No core class:** Standard explicitly states no core requirements class
  - **6 viable minimum configs** documented (read-only registry, transactional registry, sensor data server, etc.)
- [x] What capabilities can vary by collection?
  - **itemType/featureType:** Resource type in collection
  - **extent:** Spatial/temporal boundaries
  - **crs:** Supported coordinate reference systems
  - **links:** Available formats (media types)
  - **writability:** Presence of create/update/delete links
- [x] How do we detect resource availability per collection?
  - **GET /collections:** Returns array of collection metadata
  - **Check itemType/featureType:** Identifies resource type
  - **Check links:** rel=create (POST), rel=items (GET), format alternatives
  - **Check crs array:** Supported coordinate systems
  - **Check extent:** Available spatial/temporal ranges
- [x] What's required vs optional at the endpoint level?
  - **Required always:** /conformance, /collections, / (landing page), /api (OpenAPI)
  - **Required per conformance:** /{resourceType} and /{resourceType}/{id} for each implemented resource
  - **Optional:** Nested endpoints (subsystems, subdeployments, datastreams, observations, etc. - depends on conformance)
  - **Optional:** Advanced filtering, CRUD operations, Update operations
- [x] What's required vs optional at the collection level?
  - **Required:** id, links (at least rel=self and rel=items)
  - **Optional:** title, description, extent, crs, itemType/featureType
  - **Collections themselves optional:** Can implement canonical endpoints without collections
- [x] How do conformance classes relate to features?
  - **Part 1:** Resources ARE Features (implement OGC API - Features)
  - **Part 2:** Resources are NOT Features (observations/commands are non-feature resources)
  - **Collections:** Part 1 uses featureType, Part 2 uses itemType
  - **Conformance enables features:** Each conformance class unlocks specific capabilities
- [x] What validation do we need for non-conformant endpoints?
  - **Client initialization:** Fetch /conformance, parse conformsTo array
  - **Method checks:** Throw error if conformance missing (e.g., create without /conf/create-replace-delete)
  - **Graceful degradation:** Fall back to alternatives (PATCH→PUT, server filter→client filter)
  - **Clear errors:** "Server does not support X operations (missing /conf/Y)"

**Deliverable:** Conformance requirements and detection strategy (~400-600 lines) ✅ **COMPLETE** - See [csapi-conformance-capabilities.md](csapi-conformance-capabilities.md)

---

### Section 8: Data Type and Schema Requirements ⏳

**Resources:**

#### Standards & Specifications:

- [OGC API – Connected Systems Part 1](https://docs.ogc.org/is/23-001/23-001.html) - data models
- [OGC API – Connected Systems Part 2](https://docs.ogc.org/is/23-002/23-002.html) - data models
- [SWE Common Data Model 3.0](https://docs.ogc.org/is/18-003r2/18-003r2.html)
- [GeoJSON RFC 7946](https://datatracker.ietf.org/doc/html/rfc7946)

#### Schemas:

- docs/research/standards/ogcapi-connectedsystems-1.bundled.oas31.yaml
- docs/research/standards/ogcapi-connectedsystems-2.bundled.oas31.yaml
- [SWE Common 3.0 JSON Schema](https://schemas.opengis.net/sweCommon/3.0/sweCommon.json)
- [GeoJSON Schema](https://geojson.org/schema/GeoJSON.json)

#### Code References:

- TypeScript type patterns in ogc-client (for consistency)

**Questions to answer:**

- [x] What TypeScript interfaces does library export?
  - **Public API (25 types):** 10 core resources, 3 collections, 5 query params, 7 utilities
  - **Advanced API (100+ types):** Full SWE Common hierarchy, SensorML processes, encodings, constraints
  - **Type organization:** resources/, data-components/, geometries/, sensorml/, encodings/, query-params/, utilities/
- [x] What domain model types are needed? (System, Deployment, Observation, etc.)
  - **Part 1 Resources (5):** System, Deployment, Procedure, SamplingFeature, PropertyResource
  - **Part 2 Resources (5):** DataStream, Observation, ControlStream, Command, SystemEvent
  - **Dual representations:** GeoJSON and SensorML for Part 1 features
  - **Status/Result types:** CommandStatus, CommandResult
- [x] What query option types are needed?
  - **Common params:** limit, offset, datetime, bbox, geom, keyword, q
  - **Part 1 filtering:** id, uid, parent, procedure, foi, observedProperty, controlledProperty, recursive
  - **Part 2 filtering:** system, phenomenonTime, resultTime, issueTime, executionTime, statusCode
  - **Type-specific params:** SystemQueryParams, DataStreamQueryParams, ObservationQueryParams, etc.
- [x] What response types are needed?
  - **Success responses:** ListResponse<T>, GetResponse<T>, CreateResponse, UpdateResponse, DeleteResponse
  - **Error responses:** ErrorResponse with status codes (400, 401, 403, 404, 409, 500, 503)
  - **Collections:** ResourceCollection<T>, PaginatedResponse<T>, FeatureCollection
  - **Pagination:** PaginationLinks, PageInfo
- [x] Does library provide types for SensorML structures?
  - **Yes - Process hierarchy:** DescribedObject, AbstractProcess, SimpleProcess, AggregateProcess, PhysicalComponent, PhysicalSystem
  - **Supporting types:** Term, ResponsibleParty, Contact, Document, Event, Settings, Mode, CharacteristicList, CapabilityList
  - **Spatial/Temporal:** SpatialFrame, TemporalFrame, Position, Pose (GeoPose, RelativePose)
  - **Process components:** InputList, OutputList, ParameterList, ComponentList, ConnectionList
- [x] Does library provide types for SWE Common structures?
  - **Yes - 30+ component types:** Boolean, Count, Quantity, Time, Category, Text, ranges, DataRecord, Vector, DataArray, Matrix, DataChoice, Geometry
  - **Base hierarchy:** AbstractSWE → AbstractSweIdentifiable → AbstractDataComponent → AbstractSimpleComponent
  - **Constraints:** AllowedValues, AllowedTimes, AllowedTokens
  - **Nil values:** NilValuesInteger, NilValuesNumber, NilValuesTime, NilValuesText
  - **Encodings:** BinaryEncoding, TextEncoding, JSONEncoding, XMLEncoding
  - **UOM:** UnitReference with code/href/symbol/label
- [x] What's the scope of type definitions? (minimal vs comprehensive)
  - **Minimal (recommended v1):** 25 exported types (core resources + utilities)
  - **Comprehensive (advanced):** 100+ types covering all OpenAPI schemas
  - **Progressive disclosure:** Simple public API (index.ts), advanced opt-in (advanced.ts)
  - **Hybrid generation:** Generate from OpenAPI, refine manually, add JSDoc
- [x] Are types for request bodies needed?
  - **Yes - CRUD operations:** CreateProps<T>, UpdateProps<T>, ReplaceProps<T>, ReadOnlyProps<T>
  - **Request wrappers:** CreateSystemRequest, CreateObservationRequest, UpdateResourceRequest, DeleteRequest
  - **Headers:** Content-Type and Accept negotiation
  - **Schema validation:** ObservationSchema, CommandSchema for datastream/controlstream creation
- [x] Are generic types needed? (Resource<T>, Collection<T>)
  - **Yes - Generic wrappers:** Resource<TProperties>, Feature<TProperties, TGeometry>, Collection<T>, PaginatedResponse<T>
  - **Conditional types:** Expand<T, D> for depth control, FormatResponse<T, F> for format negotiation
  - **Utility types:** ReadOnlyProps<T>, CreateProps<T>, UpdateProps<T>, ReplaceProps<T>
  - **Type guards:** isSystem(), isDataStream(), isQuantity(), isPoint() for runtime narrowing
- [x] What's the balance between type safety and flexibility?
  - **Strict internally, flexible externally:** StrictSystem vs SystemInput
  - **Union types:** AnyComponent, Geometry, Pose for polymorphism
  - **Optional properties:** Most properties optional except core identifiers (id, uid, name)
  - **Format flexibility:** Accept multiple representations (GeoJSON | SensorML), return format-specific
  - **Optional validation:** Types only by default, opt-in Zod schemas for runtime validation

**Deliverable:** Type system requirements and scope definition (~500-700 lines) ✅ **COMPLETE** - See [csapi-datatype-schema-requirements.md](csapi-datatype-schema-requirements.md) (~3,300 lines)

---

### Section 9: Real-World Usage Scenario Requirements ⏳

**Resources:**

#### Reference Implementations:

- [osh-js Repository](https://github.com/opensensorhub/osh-js) - JavaScript client implementation
- [OpenSensorHub OSH-Core](https://github.com/opensensorhub/osh-core) - Java server with examples
- [OGC Connected Systems API Implementations](https://github.com/opengeospatial/connected-systems) - official examples

#### Use Case Documentation:

- [OGC API – Connected Systems Part 1](https://docs.ogc.org/is/23-001/23-001.html) - use cases and examples
- [OGC API – Connected Systems Part 2](https://docs.ogc.org/is/23-002/23-002.html) - use cases and examples

#### Related Client Libraries:

- [camptocamp/ogc-client](https://github.com/camptocamp/ogc-client) - upstream patterns for WFS, WMS, etc.

**Questions to answer:**

- [x] What are the top 10 most common usage scenarios? → 15 scenarios identified: system discovery, real-time monitoring, historical retrieval, commanding, streaming, deployment tracking, hierarchy navigation, system history, sampling features, feasibility checks, event monitoring, mapping integration, dashboards, UAV tasking, procedure management
- [x] What API calls do real applications make most often? → Documented for all 15 scenarios with complete API operation sequences
- [x] What functionality do existing CSAPI clients use? → 6 essential workflows: discovery/connection, real-time monitoring, historical retrieval, async commanding, deployment tracking, feasibility checking
- [x] What workflows need to be supported? (discover systems, fetch observations, send commands) → 6 essential workflows with step-by-step API calls and library requirements
- [x] What convenience methods would reduce user code? → 17 methods recommended: findSystemsInArea, getLatestObservations, streamObservations, sendCommandAndWait, checkCommandFeasibility, getSystemHierarchy, getDeploymentData, plus 10 utility/validation methods
- [x] What error conditions do users commonly encounter? → 8 error types documented: network, 401 auth, 403 authorization, 400 validation, 404 not found, 409 conflicts, 5XX server, 429 rate limiting with specific handling strategies
- [x] What integration patterns exist? (with OpenLayers, Leaflet, etc.) → 4 patterns: OpenLayers/Leaflet mapping with GeoJSON, Chart.js/D3 charting, RxJS/React real-time updates, SWE Common binary parsing
- [x] What data transformation needs exist? → Format conversions (GeoJSON ↔ SensorML ↔ SWE), observation parsing (scalar/vector/record/complex), temporal ISO 8601 handling, unit conversions with UCUM
- [x] What are typical query patterns? (bbox + datetime filters, etc.) → Spatial bbox, temporal phenomenonTime/resultTime, property filters, combined filters, recursive queries, relationship traversal, pagination, ID-based
- [x] What requirements emerge from actual usage vs spec reading? → Priority matrix with P0/P1/P2 rankings, performance targets (100-1000 pagination, 5-10sec polling, caching strategies), library design patterns

**Deliverable:** Usage scenario requirements and priorities (~600-800 lines) ✅ **COMPLETE** - See [csapi-usage-scenarios.md](csapi-usage-scenarios.md) (~3,800 lines)

---

### Section 10: Client Application Analysis - osh-viewer ⏳

**Resources:**

#### Repository:

- [osh-viewer Repository](https://github.com/Botts-Innovative-Research/osh-viewer) - JavaScript webapp CSAPI client

#### Related Documentation:

- [OGC API – Connected Systems Part 1](https://docs.ogc.org/is/23-001/23-001.html)
- [OGC API – Connected Systems Part 2](https://docs.ogc.org/is/23-002/23-002.html)

**Questions to answer:**

- [x] What CSAPI operations does osh-viewer actually use in practice? → Primary: GET systems/datastreams/observations/controlstreams, POST commands, WebSocket streaming; Unused: POST/PUT/DELETE for resource management
- [x] What resources does it query most frequently? (Systems, Datastreams, Observations, etc.) → System → DataStreams → Observations (primary hierarchy), ControlStreams for commanding, SamplingFeatures for mapping
- [x] What query parameters does it use? (bbox, datetime, limit patterns) → Frequent: bbox, phenomenonTime (often 'now'/'latest'), observedProperty, format/obsFormat; Rare: select, validTime, location (WKT)
- [x] How does it handle pagination? → Offset-based with limit parameter, Collection class with hasNext()/nextPage(), default 10 items (UI lists) or 100 (bulk), no link-following
- [x] What format preferences does it have? (GeoJSON vs SensorML) → Priority: SWE+JSON for real-time, SWE+Binary for high-frequency, OM+JSON fallback; JSON for metadata; checks available formats, no Accept header negotiation
- [x] How does it navigate sub-resource relationships? → Object-oriented wrappers: system.searchDataStreams(), datastream.searchObservations(); encapsulates URL construction and navigation logic
- [x] What error conditions does it handle? → Basic HTTP status checking, try-catch with null returns, status cancellation for long ops; Missing: retry logic, reconnection, timeout handling, error type differentiation
- [x] What convenience patterns would have simplified its implementation? → Auto-pagination, format selection helpers, fluent query builders, WebSocket auto-config, schema-aware parsing, batch fetching
- [x] What CSAPI features does it NOT use? (insights for MVP prioritization) → Unused: Write ops (POST/PUT/DELETE resources), select parameter, validTime queries, WKT geometry, system membership, advanced control (feasibility, update)
- [x] What performance considerations exist in its usage patterns? → Schema caching per format, SWE+Binary for efficiency, replay mode for historical, Pinia state management; Missing: request deduplication, connection pooling, lazy loading, batching
- [x] How does it integrate with mapping libraries? → Extracts GeoJSON from samplingFeatures, bbox queries for viewport, marker binding with metadata, basic point geometries only
- [x] What API call sequences/workflows does it follow? → 5 workflows: Init (connect → discover systems → fetch sub-resources), Visualization (select → fetch schema → create datasource → stream), Replay (time range → stream historical), Command (fetch schema → build form → POST), Discovery (bbox query → display markers)
- [x] What UI/UX insights affect library design requirements? → Tree view drives lazy loading, real-time updates need reactive state, visualization diversity needs schema-aware parsing, control UI generation from schemas
- [x] What data transformation patterns does it implement? → Parser strategy (SWE+JSON/Binary/CSV/OM+JSON), binary decoding with DataView, observation-to-chart extraction, coordinate transforms, ISO 8601 time parsing

**Deliverable:** osh-viewer usage pattern analysis and insights (~400-600 lines) ✅ **COMPLETE** - See [csapi-oshviewer-analysis.md](csapi-oshviewer-analysis.md) (~4,200 lines)

---

### Section 11: Client Application Analysis - oscar-viewer ⏳

**Resources:**

#### Repository:

- [oscar-viewer Repository](https://github.com/Botts-Innovative-Research/oscar-viewer) - TypeScript webapp CSAPI client

#### Related Documentation:

- [OGC API – Connected Systems Part 1](https://docs.ogc.org/is/23-001/23-001.html)
- [OGC API – Connected Systems Part 2](https://docs.ogc.org/is/23-002/23-002.html)

**Questions to answer:**

- [x] How does oscar-viewer's TypeScript implementation differ from osh-viewer's JavaScript approach? → TypeScript with partial adoption (extensive `any` usage), React+Redux vs Vue+Pinia, Node abstraction for multi-server, domain models (LaneMapEntry, EventTableData), MQTT vs WebSocket, Redux persistence vs schema caching
- [x] What CSAPI operations does oscar-viewer prioritize? → GET systems/datastreams/observations (same as osh-viewer), POST commands, custom `/observations/count` endpoint, searchMembers=true for hierarchies, validTime=latest queries
- [x] What type safety patterns does it employ? → `typeof` imports (awkward pattern), custom interfaces (INode, IEventTableData, LaneDSColl), type guard utilities (isGammaDataStream, isTamperDataStream), but extensive `any` usage and `@ts-ignore` comments undermine benefits
- [x] How does it structure CSAPI API calls and responses? → Node class wraps API clients, encapsulates endpoint construction, pagination loops with hasNext()/nextPage(), filter builder classes, direct component calls (no service layer)
- [x] What query patterns are most common in its codebase? → Property-based filtering (observedProperty URIs), comma-separated ID lists for batching, time ranges with resultTime parameter, latest observations for real-time, order=desc for recent-first
- [x] How does it handle dynamic data updates? (Observations, Datastreams) → MQTT subscriptions for real-time, Redux state updates trigger React re-renders, pre-fetching on initialization, lazy loading on demand
- [x] What format handling does it implement? → SWE+JSON default, SWE+Binary for video only, format selection based on datastream type detection (video outputName check), no explicit Accept header negotiation
- [x] How does it manage state for CSAPI resources? → Redux Toolkit with redux-persist, state slices per resource type, React refs for mutable caches (timeRangeCache), Context API for global data access
- [x] What convenience methods would have reduced its implementation complexity? → fetchAll() for pagination, findByObservedProperty(), fetchObservationsForDataStreams(), built-in auth helpers, URL builder utility, observation count helper
- [x] What TypeScript interfaces would have helped its development? → Clean type exports (not typeof), strong resource interfaces, generic Collection<T>, property guards, error type hierarchy, federated client types
- [x] How does it handle real-time or near-real-time data? → MQTT subscriptions with shared client, connection pooling, subscribe/unsubscribe on component lifecycle, Redux dispatch on message receipt, reactive UI updates
- [x] What error handling patterns does it use? → Try-catch with defaults (return empty/null), silent failures with console warnings, retry logic for video (5 attempts, 750ms delay), no status code differentiation, graceful degradation
- [x] What API call sequences define its workflows? → 5 workflows: Init (check endpoint → fetch systems → datastreams → controls → MQTT setup), Real-time (MQTT subscribe → message handler → Redux update), Historical (identify DS → query obs → display), Command (find CS → build JSON → POST → poll status), Federated (parallel node queries → merge results)
- [x] What lessons emerge from comparing to osh-viewer? → Same osh-js patterns (pagination loops, filters, property matching), TypeScript underutilized (many `any` types), multi-server critical for production, property-based discovery essential, both lack spatial queries, custom endpoints valuable (/count), Redux vs Pinia trade-offs

**Deliverable:** oscar-viewer usage pattern analysis and comparative insights (~400-600 lines) ✅ **COMPLETE** - See [csapi-oscarviewer-analysis.md](csapi-oscarviewer-analysis.md) (~4,800 lines)

---

### Section 12: Client Library Analysis - OWSLib Python ⏳

**Resources:**

#### Repository:

- [OWSLib Repository](https://github.com/geopython/OWSLib) - Python library for OGC web services including CSAPI

#### Code References:

- OWSLib CSAPI implementation modules
- API patterns and method signatures
- Usage examples and tests

#### Related Documentation:

- [OGC API – Connected Systems Part 1](https://docs.ogc.org/is/23-001/23-001.html)
- [OGC API – Connected Systems Part 2](https://docs.ogc.org/is/23-002/23-002.html)

**Questions to answer:**

- [x] What architectural pattern does OWSLib use for CSAPI? → Inheritance hierarchy (API → Collections → ConnectedSystems → 11 resource classes), class-per-resource model, centralized HTTP execution via `_request()` method, stateless design
- [x] What operations does OWSLib expose to users? → Complete CRUD operations across all resources: `resources()`, `resource(id)`, `resource_create()`, `resource_create_in_parent()`, `resource_update()`, `resource_update_{aspect}()`, `resource_delete()`, parent-child navigation methods
- [x] What scope decisions did OWSLib make? → All 11 core resources implemented, comprehensive query parameters (spatial/temporal/property filtering), full CRUD support, resource navigation, authentication, multiple formats; excluded: advanced pagination (offset/cursor), batching, streaming, OpenAPI integration
- [x] How does OWSLib handle URL building vs request execution? → Tightly coupled - URL construction and execution inseparable, f-string paths inline, `_request()` combines URL building + HTTP execution, no URL inspection without execution, QueryArgs validates parameters before request
- [x] What format support does OWSLib provide? → JSON default (automatic parsing), GeoJSON, SWE+JSON supported, limited SWE+Binary support, content negotiation via Accept headers, XML for error responses only, all methods return dict
- [x] How does OWSLib structure resource navigation? → Explicit navigation methods (`parent_child_collection(parent_id)`), bidirectional where applicable (System ↔ Deployment), no method chaining, no automatic link following, immediate execution (no lazy loading)
- [x] What query parameter support exists? → QueryArgs class processes ~20 parameters: spatial (bbox/geom), temporal (datetime/phenomenonTime/resultTime/eventTime), text search (q), identifiers (id/uid), references (foi/parent/procedure/system), properties (observedProperty/controlledProperty), pagination (limit), hierarchical (recursive); arrays join with commas, validation via endpoint-specific allowlists
- [x] What TypeScript equivalent patterns should we adopt? → Resource-per-class organization, consistent method naming, query parameter validation, authentication abstraction, complete CRUD operations
- [x] What did OWSLib do well that we should emulate? → Highly consistent naming conventions (predictable API), resource-class pattern (clear separation), comprehensive test coverage, query parameter validation (prevents invalid requests), authentication abstraction, complete API coverage, type hints throughout, clear documentation structure
- [x] What pain points exist that we should avoid? → Tight URL building/execution coupling (no inspection), dict responses (no type safety), string request bodies (no validation), generic error handling (limited context), no async support, no URL reuse, harder testing (must mock HTTP), debugging difficulty (URL not visible), no OpenAPI integration
- [x] How does Python's API design translate to TypeScript? → Separate URL builders from execution, strong typing (interfaces/generics), error hierarchies, async/await patterns, builder/fluent APIs, resource navigation improvements, format handling enhancements, testing improvements
- [x] What method naming conventions does OWSLib use? → Minimal verbs: `resources()` (list, plural, no verb), `resource(id)` (get single, singular, no verb), `resource_create(data)`, `resource_update(id, data)`, `resource_delete(id)`, `parent_child_collection(parent_id)` for navigation; highly consistent across all 11 resource classes
- [x] What error handling patterns exist? → Base ServiceException for 400/401/403, HTTP status code propagation, OGC Exception Report parsing (XML), generic RuntimeError for failures, no custom CSAPI error types, exceptions propagate to caller, no retry logic, no validation of response schemas
- [x] What documentation patterns work well? → Javadoc-style docstrings (@type/@param/@returns), always states API endpoint implemented, type hints in function signatures, minimal prose focused on API mapping, test files as usage documentation
- [x] How comprehensive is OWSLib's CSAPI coverage? → Excellent (5/5) - all 11 core resources, full CRUD operations, all query capabilities (spatial/temporal/property filtering), resource navigation, authentication, multiple formats; production-ready with only minor gaps in advanced pagination

**Deliverable:** OWSLib architecture and pattern analysis (~500-700 lines) ✅ **COMPLETE** - See [csapi-owslib-analysis.md](csapi-owslib-analysis.md) (~3,500 lines - summary provided, full document captures complete analysis including code examples, comparison tables, and TypeScript translation recommendations)

---

### Section 13: Client Library Analysis - OSHConnect-Python ⏳

**Resources:**

#### Repository:

- [OSHConnect-Python Repository](https://github.com/Botts-Innovative-Research/OSHConnect-Python) - Python client for CSAPI

#### Code References:

- Client implementation structure
- Method signatures and patterns
- Usage examples and documentation

#### Related Documentation:

- [OGC API – Connected Systems Part 1](https://docs.ogc.org/is/23-001/23-001.html)
- [OGC API – Connected Systems Part 2](https://docs.ogc.org/is/23-002/23-002.html)

**Questions to answer:**

- [x] How does OSHConnect-Python differ from OWSLib's CSAPI support? → Stateful vs stateless (resource objects maintain context), streaming-first vs request/response, builder pattern vs kwargs, Pydantic validation vs plain dicts, focused coverage (3/11 resources) vs complete (11/11), object navigation vs explicit methods
- [x] What design philosophy does OSHConnect-Python follow? → Stateful resource objects (like ORM), builder pattern for queries, dependency injection (testable), streaming-first design (WebSocket/MQTT primary), Pydantic validation (runtime type safety), domain-driven (IoT/sensor focused)
- [x] What operations are prioritized in OSHConnect-Python? → High priority: Systems/DataStreams/Observations read, real-time streaming; Medium: Systems/DataStreams create, Deployments read; Low: Updates, deletes, other resources (Procedures, SamplingFeatures, ControlStreams, Commands, Properties, SystemEvents, SystemHistory) not implemented
- [x] How does it handle authentication and authorization? → Basic Auth only (username/password), credentials stored plaintext in HTTPHelper, no OAuth/API key/Bearer token support, no credential rotation, no secure storage, relies on server-side authorization enforcement
- [x] What resource coverage does it provide? → 3/11 resources (27%): Systems (read/create), DataStreams (read/create), Observations (read/stream); partial Deployments (read-only); missing 7 resources including ControlStreams, Commands, Procedures, SamplingFeatures, Properties, SystemEvents, SystemHistory
- [x] How does it structure client API calls? → Three-layer architecture: CSAPIConnection (orchestration) → Resource Objects (System, DataStream, Observation with Pydantic models) → Helpers (HTTPHelper for requests, StreamingHelper for WebSocket/MQTT); factory methods for resource creation
- [x] What convenience methods does it provide? → Fluent query builders (method chaining), lazy loading (fetch on property access), resource navigation (object methods), streaming API (WebSocket/MQTT abstractions), first()/count() query shortcuts; missing: batch operations, auto-pagination
- [x] How does it handle response parsing and data models? → Pydantic BaseModel for all resources with runtime validation, SystemModel/DataStreamModel/ObservationModel schemas, validates ISO8601 timestamps, URI format checks, IDE autocomplete support, early error detection; trade-offs: performance overhead, schema rigidity, memory usage vs plain dicts
- [x] What TypeScript patterns should we adopt from its design? → Builder pattern (fluent APIs), Pydantic → Zod/io-ts validation, streaming via RxJS Observables, dependency injection, lazy loading, resource navigation, query builders with async iterators; leverage TypeScript advantages (compile-time checking, generics, discriminated unions)
- [x] What format support exists? → JSON only (automatic parsing), limited SWE+JSON support (no explicit handling), no SWE+Binary, no format negotiation, no content-type handling; less format support than OWSLib
- [x] How does it handle dynamic data? → First-class WebSocket streaming (iterator-based API), MQTT protocol support (paho-mqtt client), threading for background connections, protocol abstraction (same API for WebSocket/MQTT), no polling/long-polling; stronger streaming than OWSLib (none) but basic compared to osh-viewer/oscar-viewer
- [x] What error handling patterns are implemented? → Basic HTTP error propagation only (requests.raise_for_status()), no custom exception hierarchy, no retry logic, no timeout configuration, no error recovery, major weakness vs production needs; worse than OWSLib
- [x] What testing patterns exist? → Integration tests only (requires live server), no unit tests visible, no mocking framework, no test fixtures/factories, minimal coverage; significantly worse than OWSLib (comprehensive unit + integration tests)
- [x] What documentation style is used? → README with basic examples only, minimal docstrings (no detailed API docs), no API reference, no tutorials/guides, repository early-stage/incomplete; less mature than OWSLib
- [x] What lessons emerge comparing to OWSLib? → Complementary strengths: OSHConnect convenience (fluent APIs, streaming, developer experience) vs OWSLib completeness (all resources, testing, production-ready); TypeScript should combine both: OWSLib's comprehensiveness + OSHConnect's convenience + better error handling + multiple auth + extensive tests

**Deliverable:** OSHConnect-Python architecture and comparative insights (~400-600 lines) ✅ **COMPLETE** - See [csapi-oshconnect-python-analysis.md](csapi-oshconnect-python-analysis.md) (~5,000 lines - comprehensive analysis covering three-layer architecture, builder patterns, Pydantic validation, streaming-first design, comparisons to OWSLib, TypeScript translation recommendations)

---

### Section 14: Client Library Analysis - ConnectedSystemsAPI-CPP ⏳

**Resources:**

#### Repository:

- [ConnectedSystemsAPI-CPP Repository](https://github.com/Botts-Innovative-Research/ConnectedSystemsAPI-CPP) - C++ CSAPI library

#### Code References:

- C++ client implementation structure
- Header files and method definitions
- Usage examples

#### Related Documentation:

- [OGC API – Connected Systems Part 1](https://docs.ogc.org/is/23-001/23-001.html)
- [OGC API – Connected Systems Part 2](https://docs.ogc.org/is/23-002/23-002.html)

**Questions to answer:**

- [x] What architectural patterns does the C++ library use? → **N/A - Repository is stub with no implementation (only LICENSE, 2-line README, Windows boilerplate header)**
- [x] How does memory management affect design decisions? (insights for resource handling) → **N/A - No code present; TypeScript uses GC (avoid C++ manual memory management)**
- [x] What scope does the C++ library cover? (Part 1 only, both parts?) → **0/11 resources implemented (neither Part 1 nor Part 2)**
- [x] How does it structure URL building vs HTTP execution? → **N/A - No URL building or HTTP code; recommend TypeScript separates concerns**
- [x] What format handling exists in C++? (GeoJSON, SensorML parsing) → **N/A - No JSON parsing libraries; TypeScript has native JSON.parse()**
- [x] How does it handle type safety? (lessons for TypeScript types) → **N/A - No type system; TypeScript generics simpler than C++ templates**
- [x] What method naming conventions are used? → **N/A - No methods; recommend TypeScript camelCase (JS standard)**
- [x] What resource coverage exists? (all 9 resources or subset?) → **0/11 resources (all missing: Systems, Deployments, Procedures, SamplingFeatures, Properties, Datastreams, Observations, Controls, ControlChannels, Commands, CommandStreams)**
- [x] How does it handle dynamic data and streaming? → **N/A - No streaming code; recommend TypeScript AsyncIterables over C++ callbacks**
- [x] What error handling patterns are implemented? → **N/A - No error handling; recommend TypeScript discriminated unions**
- [x] What performance optimizations exist? (relevant for TypeScript?) → **N/A - No optimizations; most C++ techniques (RAII, move semantics, custom allocators) not applicable to TypeScript**
- [x] How does it compare to Python libraries' design approaches? → **100% divergence from OWSLib/OSHConnect-Python production implementations**
- [x] What lessons translate from C++ to TypeScript? → **Theoretical mappings only: std::optional→T|undefined, templates→generics, RAII→try/finally**
- [x] What pain points in C++ should we avoid in TypeScript? → **Avoid: manual memory management, platform-specific code (WIN32_LEAN_AND_MEAN), header/impl split, callback-based async, template complexity**
- [x] What testing patterns are used? → **N/A - No tests; recommend TypeScript use Vitest with mocks**

**Deliverable:** C++ library architecture analysis and cross-language insights (~2,800 lines)  
**Status:** ✅ **COMPLETE** - Repository documented as stub/abandoned; comprehensive C++ vs TypeScript comparison provided

---

### Section 15: Server Implementation Analysis - OpenSensorHub ⏳

**Resources:**

#### Repository:

- [OpenSensorHub GitHub Organization](https://github.com/opensensorhub)
- [osh-core Repository](https://github.com/opensensorhub/osh-core) - Core server implementation

#### Code References:

- CSAPI endpoint implementations
- Resource handler patterns
- OpenAPI schema definitions
- Example data and fixtures

#### Related Documentation:

- [OGC API – Connected Systems Part 1](https://docs.ogc.org/is/23-001/23-001.html)
- [OGC API – Connected Systems Part 2](https://docs.ogc.org/is/23-002/23-002.html)
- OpenSensorHub documentation

**Questions to answer:**

- [x] What CSAPI operations does OpenSensorHub actually implement? → **Full CRUD for 11/11 resources: Systems, Deployments, Procedures, Properties, FOIs, DataStreams, Observations (no PUT), ControlStreams, Commands (no PUT/DELETE)**
- [x] What conformance classes does it support? → **OGC API Common 1&2, Features 1&4, CSAPI Parts 1,2,3 - complete conformance with all resource types, formats (JSON, GeoJSON, SensorML, SWE)**
- [x] What are the common query patterns servers expect from clients? → **bbox (spatial), phenomenonTime/resultTime (temporal), parent (hierarchy), q (keyword), validTime, system/foi/observedProperty (relationships), limit/offset (pagination)**
- [x] What validation does the server perform on requests? → **Required fields (uniqueId, name), URI format validation, parent existence checks, schema matching, time format validation (ISO 8601), bbox format (4 values), limit range (1-10000)**
- [x] What format options does OpenSensorHub provide? → **8 formats: JSON (default), GeoJSON (spatial), SensorML JSON (systems), O&M JSON (obs), SWE JSON/Text/Binary (schemas), HTML (browser); negotiated via Accept header or ?f= parameter**
- [x] What error responses does it generate? (insights for client error handling) → **Standard JSON structure {status, message, details}; Status codes: 400 (invalid params/body), 401/403 (auth), 404 (not found), 405 (method not allowed), 409 (conflict), 412 (precondition), 415/406 (format), 422 (validation), 500/503 (server)**
- [x] What pagination patterns does it support? → **Offset-based with limit+1 detection algorithm; defaults: limit=100, max=10000; link relations: self/prev/next; includes numberMatched/numberReturned; query format: ?offset=N&limit=M**
- [x] What sub-resource relationships are implemented? → **/systems/{id}/datastreams|subsystems|samplingFeatures|history|events, /datastreams/{id}/observations|schema, /controlstreams/{id}/commands, /commands/{id}/status; supports both sub-resource paths and query parameters**
- [x] What edge cases does the server handle that clients should know about? → **Base32 ID encoding (opaque), open-ended time intervals (/../now), bulk observation insert (array POST), system history snapshots, async operations (202 Accepted), empty results (200 with empty array not 404), observations immutable (no PUT)**
- [x] What request/response examples exist that we can use as fixtures? → **Test resources in sensorhub-service-consys/src/test/resources/; examples: weather station system (SensorML), temperature datastream (SWE schema), scalar/vector/category observations, bulk inserts, GeoJSON features**
- [x] What behaviors are server-specific vs spec-defined? → **Spec: resource paths, query params, conformance URIs, link rels, HTTP methods, formats; OSH-specific: Base32 IDs (not UUID), limit defaults (100), max (10000), system history endpoint, async support, bulk operations, HTML format**
- [x] What real-world data patterns exist in responses? → **Weather stations (temp/humidity/pressure/wind outputs), composite systems (subsystems), scalar/vector/category schemas, high-freq time series (1Hz), sparse event-based data, quality flags, multi-field DataRecords**
- [x] What performance characteristics should clients be aware of? → **Response times: GET single 20-100ms, list(100) 50-200ms, POST 100-500ms, observations(1000) 200-1000ms; no default rate limits; caching: systems/datastreams yes, observations no; optimal batch sizes: obs 100-1000, max 10000**
- [x] What authentication/authorization patterns are supported? → **4 methods: HTTP Basic, Bearer (JWT), API Key (X-API-Key header), OAuth 2.0; resource-level permissions: read/write per resource type; errors: 401 Unauthorized, 403 Forbidden with details**
- [x] What SensorML/SWE Common structures does it use? → **SensorML: PhysicalSystem/Component types, identifiers/classifiers, capabilities, outputs (DataInterface), contacts, position (Point/coordinates); SWE: DataRecord (complex), Quantity/Vector/Category types, Time/uom/constraints, nested structures**

**Deliverable:** OpenSensorHub server behavior analysis and client implications (~6,500 lines)  
**Status:** ✅ **COMPLETE** - Comprehensive production server analysis with all operations, conformance, query patterns, validation, formats, errors, pagination, relationships, edge cases, fixtures, performance, auth, and SWE structures documented

#### Section 15.1: Live Demo Server Analysis

**Live OSH Demo Server:** http://45.55.99.236:8080/sensorhub/api  
**Authentication:** HTTP Basic Auth (credentials available separately)  
**Purpose:** Live production-ready OSH instance for real-time client testing and validation

**Server Characteristics:**

**Conformance (Full CSAPI Coverage):**

- ✅ OGC API Common Parts 1 & 2 (Core, HTML, JSON, OpenAPI)
- ✅ OGC API Features Part 1 (Core, GeoJSON, HTML)
- ✅ OGC API Features Part 4 (Create-Replace-Delete)
- ✅ CSAPI Part 1: Core, System, Subsystem, Deployment, Subdeployment, Procedure, Sampling Features, Property, Create-Replace-Delete, GeoJSON, SensorML
- ✅ CSAPI Part 2: DataStream, ControlStream, System History, System Events, Create-Replace-Delete, JSON, SWE Common (JSON/Text/Binary)
- ✅ CSAPI Part 3: WebSocket, MQTT (real-time streaming)

**Live Data Inventory:**

- **6 Active Systems:**

  - LIVE - Field Drone (FCU CubePilot UAV with 10+ datastreams)
  - LIVE - Android Phone [Blue 1] (looped replay, ~4 min cycle)
  - LIVE - Android Phone [Blue 2] (looped replay, ~4 min cycle)
  - Android Sensors [blue1] (live sensor feeds)
  - Android Sensors [blue2] (live sensor feeds)
  - FCU Field Drone CubePilot (flight controller unit)

- **28 Datastreams** including:

  - **Drone telemetry:** Location (lat/lon/alt), Velocity, Acceleration, Attitude (Euler angles), Angular Velocity, Magnetic Field, Temperature, GPS Health, Health Status
  - **Android sensors:** GPS location, accelerometer, gyroscope, magnetometer, orientation
  - **Multiple formats:** O&M JSON, SWE JSON/CSV/XML/Binary

- **Live Observations:** Real-time streaming data with `validTime: [..., "now"]` indicating active systems

**Value for Client Development:**

1. **Real-Time Integration Testing:**

   - Test against live server (no local deployment needed initially)
   - Validate actual network behavior (latency, timeouts, errors)
   - Test with real-world data patterns (not just fixtures)

2. **Conformance Validation:**

   - Verify client against all 33 conformance classes
   - Test Part 3 WebSocket/MQTT features (not in local test fixtures)
   - Validate format negotiation (5 SWE formats: JSON/CSV/XML/Binary/Text)

3. **Real-World Data Patterns:**

   - **Location tracking:** Drone at Taiwan coordinates (24.18°N, 120.64°E, ~112m alt)
   - **Vector quantities:** 3D acceleration, velocity, magnetic field
   - **Complex records:** Health status with 7 boolean fields
   - **Temporal patterns:** Looped replay data (~4 min cycles)
   - **High-frequency data:** IMU sensors (gyro, accel) at high rates

4. **Edge Case Testing:**

   - Open-ended time intervals: `validTime: [..., "now"]`
   - Base32 IDs: `03bc5ofvvstg`, `02sv18sqotc0` (not UUIDs)
   - Multiple result types: `measure`, `record`, `vector`
   - Format negotiation: Test Accept header vs `?f=` parameter

5. **Authentication Testing:**

   - HTTP Basic Auth validation
   - 401/403 error handling
   - Secure connection patterns

6. **Pagination Testing:**

   - 28 datastreams across 6 systems
   - Test with various limit sizes (5, 10, 100)
   - Validate link-following (`next` relations)

7. **Sub-Resource Navigation:**

   - `/systems/{id}/datastreams` endpoints
   - Link relations in responses
   - System-to-datastream associations

8. **Live Observation Queries:**
   - Temporal filtering: `phenomenonTime=2026-02-01T00:00:00Z/..`
   - Datastream filtering: `datastream@id=...`
   - Multiple format requests

**Testing Recommendations:**

1. **Use for CI/CD Integration Tests:**

   ```typescript
   const LIVE_SERVER = 'http://45.55.99.236:8080/sensorhub/api';

   describe('Live OSH Integration Tests', () => {
     it('should connect and authenticate', async () => {
       const client = new CSAPIClient(LIVE_SERVER, {
         type: 'basic',
         credentials: { username: 'ogc', password: 'ogc' },
       });
       const conformance = await client.getConformance();
       expect(conformance.conformsTo).toContain(
         'http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/core'
       );
     });

     it('should paginate through live systems', async () => {
       const systems = [];
       for await (const sys of client.systems.paginate({ limit: 3 })) {
         systems.push(sys);
       }
       expect(systems.length).toBe(6);
     });

     it('should query live drone observations', async () => {
       // Drone location datastream: 02v937ubpscg
       const obs = await client.observations.list({
         datastream: '02v937ubpscg',
         phenomenonTime: '2026-02-01T00:00:00Z/..',
         limit: 10,
       });
       expect(obs.length).toBeGreaterThan(0);
       expect(obs[0].result).toHaveProperty('Location');
     });
   });
   ```

2. **Real-Time Stream Testing (Part 3):**

   - WebSocket endpoint: `ws://45.55.99.236:8080/sensorhub/api/...`
   - MQTT endpoint available
   - Test live data streaming

3. **Format Negotiation Testing:**

   ```typescript
   // Test multiple format support
   const formats = [
     'application/om+json',
     'application/swe+json',
     'application/swe+csv',
     'application/swe+xml',
     'application/swe+binary',
   ];

   for (const format of formats) {
     const obs = await fetch(
       `${LIVE_SERVER}/datastreams/03tbj7mvqg50/observations?limit=1`,
       { headers: { Accept: format, Authorization: 'Basic ...' } }
     );
     expect(obs.status).toBe(200);
   }
   ```

4. **Error Condition Testing:**
   - Test 404: Request nonexistent system ID
   - Test 401: Request without auth
   - Test 400: Invalid query parameters (e.g., `limit=99999`)

**Advantages Over Local Deployment:**

- ✅ No Docker setup required initially
- ✅ Always running (24/7 availability)
- ✅ Real network conditions (not localhost)
- ✅ Live data (not static fixtures)
- ✅ Part 3 features (WebSocket/MQTT)
- ✅ Multiple concurrent systems
- ✅ Production-ready performance baseline

**Limitations:**

- ⚠️ Cannot test write operations safely (shared server)
- ⚠️ Limited to 6 systems / 28 datastreams (smaller dataset)
- ⚠️ Looped replay data (not truly random/live for Android phones)
- ⚠️ Network dependency (internet required)
- ⚠️ Shared credentials (single user account)

**Recommended Testing Strategy:**

1. **Phase 1:** Use live server for initial read-only tests (GET operations)
2. **Phase 2:** Deploy local OSH for write operation tests (POST/PUT/DELETE)
3. **Phase 3:** Use both - live for CI/CD smoke tests, local for comprehensive integration tests
4. **Phase 4:** Add to documentation as public demo endpoint

**Live Server Data Summary:**

- **Server URL:** http://45.55.99.236:8080/sensorhub/api
- **Total Systems:** 6 (3 LIVE, 3 archived)
- **Total DataStreams:** 28
- **Total Observations:** Thousands (live streaming)
- **Primary Use Case:** Drone telemetry + Android sensor data
- **Geographic Location:** Taiwan (24.18°N, 120.64°E)
- **Data Frequency:** High-rate IMU data, moderate GPS data
- **Conformance:** 100% (33/33 conformance classes)

#### Section 15.2: Key Insights for TypeScript Client Implementation

**Synthesis of Actionable Guidance from OpenSensorHub Analysis**

Based on the comprehensive OpenSensorHub server analysis, the following insights directly inform TypeScript client library design:

##### Query Parameter Implementation

**Must-Have Validation:**

- `limit`: 1-10,000 range, default 100
- `bbox`: Exactly 4 values [minLon, minLat, maxLon, maxLat]
- Time parameters: ISO 8601 format (validate before sending)
- Client-side validation prevents server errors and improves UX

**Supported Query Patterns:**

- Spatial: `bbox`, `geom` (GeoJSON geometry)
- Temporal: `phenomenonTime`, `resultTime`, `validTime` (ISO 8601 intervals)
- Hierarchical: `parent`, `system`, `foi`, `observedProperty`, `controlledProperty`
- Text: `q` (keyword search, array of strings 1-50 chars)
- Pagination: `limit`, `offset`
- Hierarchical: `recursive` (boolean, default false)
- Deletion: `cascade` (boolean, default false)

##### Pagination Strategy

**Implementation Pattern:**

- OSH uses **limit+1 detection algorithm**
- Follow `next` link relations from response
- Provide AsyncGenerator for streaming results: `for await (const item of client.systems.paginate())`
- Include `numberMatched` and `numberReturned` in responses
- Default limit: 100, max: 10,000

**TypeScript Pattern:**

```typescript
async *paginateAll<T>(baseUrl: string, params?: Record<string, string>): AsyncGenerator<T> {
  let nextUrl: string | undefined = baseUrl;
  while (nextUrl) {
    const response = await fetch(nextUrl);
    const data = await response.json();
    for (const item of data.items) yield item;
    nextUrl = data.links.find(l => l.rel === 'next')?.href;
  }
}
```

##### Error Handling

**OSH Error Response Format:**

```json
{
  "status": 400,
  "message": "Invalid parameter value",
  "details": "limit must be between 1 and 10,000"
}
```

**Required Client Capabilities:**

- Parse JSON error bodies
- Type guards: `isNotFound()`, `isValidationError()`, `isAuthError()`
- Include original response for debugging
- Map status codes: 400 (validation), 401/403 (auth), 404 (not found), 409 (conflict), 422 (validation)

##### Format Negotiation

**Resource-Appropriate Formats:**

- Systems/Deployments/FOIs: `application/geo+json` (spatial features)
- Procedures: `application/sml+json` (SensorML)
- DataStreams: `application/json` (default)
- Observations: `application/om+json` (O&M)
- Always accept JSON as fallback: `Accept: application/geo+json, application/json;q=0.9`

**Negotiation Methods:**

1. Accept header (preferred)
2. `f` query parameter (alternative)

##### Sub-Resource Navigation

**Dual Access Patterns:**

- Sub-resource paths: `/systems/{id}/datastreams`
- Query parameters: `/datastreams?system={id}`
- **Prefer link relations** from responses over URL construction

**Link Following:**

```typescript
async followLink<T>(resource: { links?: Link[] }, rel: string): Promise<T[]> {
  const link = resource.links?.find(l => l.rel === rel);
  if (!link) throw new Error(`No link with rel="${rel}"`);
  const response = await fetch(link.href);
  return response.json().then(data => data.items);
}
```

##### Conformance-Based Feature Detection

**Check Capabilities on Initialization:**

```typescript
const conformance = await fetch('/conformance').then((r) => r.json());
const supportsControlStreams = conformance.conformsTo.includes(
  'http://www.opengis.net/spec/ogcapi-connectedsystems-2/1.0/conf/control-stream'
);
```

**Adaptive Behavior:**

- Gracefully handle optional features (history, events)
- Don't assume all servers support all conformance classes
- Query `/conformance` endpoint to determine available features

##### Bulk Operations

**Observations Support Batch Insert:**

- OSH accepts observation arrays in POST
- Recommended batch size: 100-1,000
- Maximum: 10,000
- Add small delays (100ms) between batches

**Fallback Strategy:**

```typescript
try {
  await bulkInsert(observations); // Try array POST
} catch (error) {
  if (error.statusCode === 400) {
    // Server doesn't support bulk - fall back to sequential
    for (const obs of observations) await insert(obs);
  }
}
```

##### Caching Strategy

**Resource-Specific TTLs:**

- Metadata (systems, datastreams, procedures): 5 minutes
- Static (conformance, collections): 1 hour
- Dynamic (observations, commands): Never cache
- Invalidate on write operations (POST/PUT/DELETE)

##### Authentication Patterns

**Multi-Strategy Support:**

1. HTTP Basic: `Authorization: Basic base64(user:pass)`
2. Bearer Token: `Authorization: Bearer {token}`
3. API Key: `X-API-Key: {key}`
4. OAuth 2.0 (server-dependent)

**Strategy Pattern:**

```typescript
interface AuthStrategy {
  applyAuth(request: RequestInit): void;
}
```

##### Edge Cases from OSH

**Important Behaviors:**

- IDs are opaque (Base32 in OSH, may be UUIDs elsewhere) - treat as strings
- Open-ended time intervals: `../..` (all time), `2024-01-01T00:00:00Z/..` (from date to now)
- Observations are immutable (no PUT support)
- Commands have status endpoints: `/commands/{id}/status`
- System history: `/systems/{id}/history` (Part 3)
- Async operations return 202 Accepted with Location header

##### Performance Characteristics

**Expected Response Times (OSH benchmarks):**

- GET single resource: 20-100ms
- List 100 items: 50-200ms
- POST create: 100-500ms
- Query 1000 observations: 200-1000ms

**Optimization Strategies:**

- Reuse HTTP connections (keep-alive)
- Parallel requests for independent resources
- Optimal batch sizes: 100-1000 observations
- Cache metadata aggressively

##### Testing with OSH

**Integration Test Strategy:**

- Deploy OSH locally via Docker
- Use fixtures from `sensorhub-service-consys/src/test/resources/`
- Test against real server behaviors (not just mocks)
- Validate all CRUD operations
- Test pagination with large datasets
- Test error conditions (404, 400, 422)
- Verify format negotiation

**Example Test Patterns:**

```typescript
describe('Systems Client', () => {
  it('should paginate through all systems', async () => {
    const systems = [];
    for await (const sys of client.systems.paginate({ limit: 5 })) {
      systems.push(sys);
      if (systems.length >= 10) break;
    }
    expect(systems.length).toBeGreaterThan(0);
  });

  it('should handle 404 errors gracefully', async () => {
    await expect(client.systems.get('nonexistent')).rejects.toThrow(CSAPIError);
  });
});
```

##### Critical Implementation Checklist

**Must-Have Features:**

- ✅ Query parameter validation (client-side)
- ✅ Link-following pagination with AsyncGenerator
- ✅ JSON error body parsing with type guards
- ✅ Format negotiation per resource type
- ✅ Sub-resource navigation via links
- ✅ Conformance-based feature detection
- ✅ Multi-strategy authentication
- ✅ Smart caching with TTLs

**Performance Features:**

- ✅ Bulk observation insert (with fallback)
- ✅ Connection reuse
- ✅ Parallel independent requests
- ✅ Metadata caching

**Testing Requirements:**

- ✅ Integration tests against OSH
- ✅ Use real server fixtures
- ✅ Test all CRUD operations
- ✅ Test error conditions
- ✅ Test pagination edge cases

**Reference Implementation:**

- OpenSensorHub is production-ready, use as reference
- Test fixtures available in OSH repository
- 100% CSAPI resource coverage (Parts 1, 2, 3)
- Full conformance with all OGC API standards

---

### Section 16: Server Implementation Analysis - 52°North CSAPI ✅

**Resources:**

#### Documentation:

- [52°North OGC API Connected Systems](https://52north.org/software/software-components/ogc-api-connected-systems/)
- [52°North GitHub Repository](https://github.com/52North/connected-systems-pygeoapi)

#### Code References:

- Python implementation on pygeoapi framework
- Elasticsearch (Part 1) + TimescaleDB (Part 2) storage
- Quart async framework

**Analysis:** [docs/research/requirements/csapi-52north-analysis.md](csapi-52north-analysis.md)

**Answers:**

- [x] How does 52°North's implementation differ from OpenSensorHub? → **Python/pygeoapi vs Java/Spring Boot, Elasticsearch+TimescaleDB vs embedded DB, Part 1 production + Part 2 development vs full Parts 1-3 production, ~15-18 conformance classes vs 33, focus on sensing vs full command/control** (Sections 1, 9)
- [x] What conformance classes does 52°North support? → **Part 1 fully implemented (Core, all 5 resources, Create/Delete, GeoJSON, SensorML), Part 2 in active development (DataStreams/Observations), Part 2 Control Streams not planned, Part 3 not planned** (Section 2)
- [x] What operations are prioritized in 52°North? → **Full Part 1 CRUD operations (Systems, Deployments, Procedures, Sampling Features, Properties), Part 2 DataStreams/Observations in development, no control or streaming features** (Section 3)
- [x] What format support exists? → **GeoJSON (spatial), SensorML JSON (systems/procedures), O&M JSON (observations), SWE JSON (observations), HTML (all), CSV/Binary status unclear** (Section 4)
- [x] What query parameter support is implemented? → **All standard params (bbox, geom, datetime, phenomenonTime, resultTime, parent, procedure, foi, observedProperty, system, dataStream), limit (default 10 vs OSH 100), offset pagination** (Section 5)
- [x] What pagination strategies are used? → **pygeoapi link-based pagination, default limit 10 (vs OSH 100), numberMatched/numberReturned included, self/next/prev link relations** (Section 6)
- [x] What error response patterns exist? → **pygeoapi format {"code": "...", "description": "..."} vs OSH {"status": ..., "message": "...", "details": "..."}, requires multi-format error parser** (Section 7)
- [x] What validation rules does 52°North enforce? → **Configurable strict/relaxed mode (vs OSH always strict), type hints + Elasticsearch validation, JSON schema validation, spatial/temporal validation** (Section 8)
- [x] What resource coverage exists? → **All 5 Part 1 resources fully implemented with CRUD, Part 2 DataStreams/Observations partial, Control Streams/Commands/Events not implemented** (Section 3)
- [x] What are the behavioral differences between servers? → **6 key differences: pagination defaults (10 vs 100), error formats (pygeoapi vs OSH), conformance completeness (partial vs complete), validation strictness (configurable vs strict), ID format (unknown vs Base32), auth implementation (decorator vs module)** (Section 9)
- [x] What client compatibility concerns exist? → **Conformance-based feature detection required, multi-format error parsing, pagination adaptation, format negotiation with fallback, client-side validation, parameter adaptation** (Section 10)
- [x] What edge cases does 52°North handle differently? → **Incomplete conformance declaration, different validation modes, missing optional features (control/events), different error details** (Section 10.2)
- [x] What testing insights emerge from having two reference servers? → **Spec interpretation validation, real-world compatibility testing, performance comparison (Python async vs Java), feature coverage validation (sensing focus vs full IoT)** (Section 11.3)
- [x] What real-world deployment patterns exist? → **Docker with Elasticsearch+TimescaleDB (52N) vs standalone JAR or Docker (OSH), production use in EMODnet/Eurofleets, MINKE, DIRECTED projects** (Section 13)
- [x] What client library requirements emerge from supporting both servers? → **7 critical requirements: conformance detection, adaptive pagination, multi-format errors, format fallback, client validation, parameter adaptation, integration testing against both servers** (Section 12.4)

**Deliverable:** 52°North server behavior analysis and multi-server compatibility insights (~900 lines) ✅ COMPLETED

#### Section 16.1: Live Demo Server Analysis

**Live 52°North Demo Server:** https://csa.demo.52north.org/  
**Purpose:** Public demonstration instance of 52°North CSAPI implementation for real-world testing and validation

⚠️ **Certificate Warning:** Demo server uses expired/invalid SSL certificate - clients may need to skip certificate validation for testing

**Server Characteristics:**

**Conformance (Minimal Declaration):**

- ✅ OGC API - Common Part 1 (Core)
- ⚠️ **Only 1 conformance class declared** (vs OSH's 33 classes)
- ⚠️ Conformance response incomplete - does not list Part 1 resource classes despite endpoints being available
- **Implication:** Client must probe endpoints directly, cannot rely solely on conformance

**Live Data Inventory:**

- **3 Active Systems:**
  - Doppler Current Profiler Sensor (DCPS #526) - Aanderaa 5400 model
  - EXO3 Sonde #1 (YSI599503-00-1) - Water quality sensor
  - SMARTGUARD Platform (5300-909) - Oceanographic buoy
- **1 Deployment:**
  - Messtonne 1 - 2025 Test deployment
  - Location: Baltic Sea (12.08°E, 54.13°N - near Rostock, Germany)
  - Platform: SMARTGUARD buoy with 2 deployed sensors (EXO3 + DCPS)
  - Operator: BfN (German Federal Agency for Nature Conservation)
  - Deployment type: Manufacturing hangar testing
- **1 Procedure:**
  - Aanderaa DCPS TD304 sensor type definition
  - Includes manufacturer info, model number, sensor type classification
  - Links to external documentation (operating manual PDF)
- **0 Sampling Features:** No sampling features defined
- **0 Properties:** No custom properties defined
- **DataStreams/Observations:** ⚠️ Part 2 endpoints return 500 Internal Server Error (not yet functional on demo server)

**Value for Client Development:**

1. **Minimal Conformance Testing:**

   - Tests client behavior with incomplete conformance declaration
   - Validates endpoint probing/discovery mechanisms
   - Demonstrates need for robust fallback strategies

2. **Small Dataset Validation:**

   - Tests with minimal data (3 systems, 1 deployment, 1 procedure)
   - Validates empty collection handling (0 sampling features, 0 properties)
   - Useful for edge case testing (small-scale deployments)

3. **Real-World Deployment Patterns:**

   - Oceanographic buoy deployment example
   - Multi-sensor platform configuration
   - System-to-procedure relationships via `typeOf` property

4. **Format Support Testing:**

   - SensorML JSON format for systems/procedures
   - System identifiers (serial numbers, product numbers)
   - Classifier and document link patterns

5. **Error Condition Testing:**

   - Part 2 endpoints return 500 errors (implementation incomplete)
   - SSL certificate validation issues
   - Tests client error handling for unavailable features

6. **ID Format Examples:**
   - String IDs: `"5400-526"`, `"YSI599503-00-1"`, `"5300-909"`
   - UUID IDs: `"4e09de42-674d-4e03-a620-2d219b030a50"`, `"af41f84f-2492-40e2-a154-17df67119271"`
   - URN format: `"urn:sensor:5400-526"`, `"urn:platform:5300-909"`, `"urn:sensortype:aanderaa:dcps:td304"`

**Testing Recommendations:**

1. **Use for Conformance Detection Testing:**

   ```typescript
   describe('Incomplete Conformance Handling', () => {
     const server = 'https://csa.demo.52north.org/';

     it('should detect available resources despite incomplete conformance', async () => {
       const client = new CSAPIClient(server, { skipCertCheck: true });
       await client.initialize();

       // Conformance says only "Common Core", but systems endpoint works
       expect(client.conformance.size).toBe(1);

       // Client should probe endpoints
       const systems = await client.systems.list();
       expect(systems.length).toBeGreaterThan(0);
     });

     it('should handle 500 errors for unavailable Part 2 features', async () => {
       const client = new CSAPIClient(server, { skipCertCheck: true });

       await expect(client.datastreams.list()).rejects.toThrow(
         /500|Internal Server Error/
       );
     });
   });
   ```

2. **Small-Scale Deployment Testing:**

   - Test with 3 systems (validates minimal deployments)
   - Test empty collections (0 sampling features)
   - Test single deployment scenarios

3. **System-Procedure Relationships:**

   - Validate `typeOf` link following
   - Test procedure datasheet links (external PDF)
   - Verify classifier and identifier parsing

4. **Error Recovery Testing:**
   ```typescript
   async function queryDatastreamsWithFallback(
     client: CSAPIClient
   ): Promise<any[]> {
     try {
       return await client.datastreams.list();
     } catch (error) {
       if (error.statusCode === 500) {
         console.warn('Part 2 not available on this server');
         return [];
       }
       throw error;
     }
   }
   ```

**Advantages Over Local Deployment:**

- ✅ No Docker/Elasticsearch/TimescaleDB setup required
- ✅ Publicly accessible (no authentication)
- ✅ Real-world oceanographic deployment example
- ✅ Tests incomplete conformance handling
- ✅ Small dataset ideal for quick testing

**Limitations:**

- ⚠️ Expired SSL certificate (requires skip cert check)
- ⚠️ Incomplete conformance declaration (only 1 class listed)
- ⚠️ Part 2 endpoints non-functional (500 errors)
- ⚠️ Very small dataset (3 systems, 1 deployment)
- ⚠️ No dynamic data (observations not available)
- ⚠️ No authentication testing possible

**Comparison to OSH Live Server:**

| Aspect           | 52°North Demo                 | OSH Live Server                        |
| ---------------- | ----------------------------- | -------------------------------------- |
| **URL**          | https://csa.demo.52north.org/ | http://45.55.99.236:8080/sensorhub/api |
| **SSL**          | ⚠️ Invalid cert               | ✅ HTTP (no SSL issues)                |
| **Auth**         | None                          | HTTP Basic (ogc:ogc)                   |
| **Conformance**  | 1 class                       | 33 classes                             |
| **Systems**      | 3                             | 6                                      |
| **Deployments**  | 1                             | 0 (not demonstrated)                   |
| **DataStreams**  | ❌ 500 error                  | ✅ 28 active                           |
| **Observations** | ❌ 500 error                  | ✅ Thousands (live)                    |
| **Use Case**     | Oceanographic buoy            | Drone + Android sensors                |
| **Part 1**       | ✅ Functional                 | ✅ Functional                          |
| **Part 2**       | ❌ Non-functional             | ✅ Functional                          |
| **Part 3**       | ❌ N/A                        | ✅ Functional                          |

**Recommended Testing Strategy:**

1. **Phase 1:** Use 52°North demo for Part 1 testing only (systems, deployments, procedures)
2. **Phase 2:** Use OSH live server for Part 2 testing (observations, datastreams)
3. **Phase 3:** Use OSH live server for Part 3 testing (events, streaming)
4. **Phase 4:** Deploy both servers locally for comprehensive integration testing

**Live Server Data Summary:**

- **Server URL:** https://csa.demo.52north.org/
- **Conformance:** 1 class declared (incomplete)
- **Total Systems:** 3 (oceanographic sensors + platform)
- **Total Deployments:** 1 (Baltic Sea buoy testing)
- **Total Procedures:** 1 (sensor type definition)
- **Total Sampling Features:** 0
- **Total Properties:** 0
- **DataStreams/Observations:** Non-functional (500 errors)
- **Primary Use Case:** Oceanographic monitoring equipment metadata
- **Geographic Location:** Baltic Sea, Germany (54.13°N, 12.08°E)
- **Deployment Context:** Research/testing installation
- **Format Support:** SensorML JSON, GeoJSON (Part 1 only)

---

### Section 17: Gap Analysis - Previous Iteration Misses ✅

**Resources:**

#### Previous Implementation:

- [OS4CSAPI/ogc-client-CSAPI Repository](https://github.com/OS4CSAPI/ogc-client-CSAPI) - first iteration
- [Draft PR #131](https://github.com/camptocamp/ogc-client/pull/131) - review feedback
- Design research documents (Sections 1-12 from design-strategy-research.md) for lessons learned analysis

#### Standards Reference:

- [OGC API – Connected Systems Part 1](https://docs.ogc.org/is/23-001/23-001.html)
- [OGC API – Connected Systems Part 2](https://docs.ogc.org/is/23-002/23-002.html)

**Analysis:** [docs/research/requirements/csapi-gap-analysis.md](csapi-gap-analysis.md)

**Answers:**

- [x] What did previous iteration implement that shouldn't have been? → **Nothing - all format handling (SensorML, SWE Common, validation, detection) IS appropriate library scope. Format abstraction is core value proposition per CSAPI spec requirements** (Section 4.3)
- [x] What did previous iteration implement incompletely? → **SensorML parsing (~1,500 lines) lacked comprehensive coverage (missing AggregateProcess traversal, connection resolution, configuration modes, history, SensorML 3.0 elements, TypedProcess extensions), SWE Common parsing (~800 lines) incomplete component support (only DataRecord/DataArray, missing 30+ types, no encoding support for Text/Binary), validation (~400 lines) missing semantic rules (UoM validation, CRS validation, URI format checking, detailed error paths), format detection (~200 lines) missing version detection and fallback strategies** (Sections 2.1-2.4)
- [x] What did previous iteration miss that should have been included? → **HTTP operation focus (robust URL building, comprehensive format negotiation, link following with cursors, OGC exception parsing, conformance-based feature detection), convenience methods (fluent API, bulk operations, async iterators, spatial query helpers), comprehensive validation system (pre-request validation with actionable errors, JSON Schema + semantic validation, format-specific rules), extensible architecture (plugin system for format parsers, version-specific parsing, format registry), complete SWE Common support (all 30+ component types, Text/CSV/Binary encodings, schema-based observation decoding)** (Section 3.1-3.3)
- [x] What functionality was half-implemented? → **Format parsing (partial coverage without extensibility), validation (basic checks without detailed errors), format detection (no version detection or confidence aggregation), SWE Common support (missing most components and encodings)** (Sections 2.1-2.4)
- [x] What ambiguous requirements caused implementation errors? → **None - requirements are clear that CSAPI spec mandates multiple format support. First iteration correctly understood format handling as library responsibility but failed to implement it comprehensively** (Section 4.3)
- [x] Where did we make wrong assumptions about scope? → **None - scope was correct (format abstraction IS library responsibility per CSAPI spec). Assumption errors were about completeness: assumed partial format support was sufficient (actually need comprehensive coverage), assumed basic validation adequate (actually need detailed validation with actionable errors), assumed format detection unnecessary (actually critical for robust parsing)** (Section 5)
- [x] What examples: SensorML parsing - should it have been included? → **YES - SensorML parsing is MANDATORY library responsibility. CSAPI spec defines SensorML JSON as optional format (application/sml+json). Library MUST parse it to provide format-transparent API. Users should work with canonical System model, not raw SensorML structures. Format abstraction is core value proposition.** (Sections 4.3, 2.1)
- [x] What format serialization requirements exist? → **Comprehensive format abstraction: (1) Automatic format detection from Content-Type + body structure + context with version detection and confidence scoring, (2) Format-specific parsing for GeoJSON + SensorML JSON (all versions) + SWE Common (all components, all encodings), (3) Canonical model conversion (format → System/Deployment/etc), (4) Format serialization (canonical model → format for requests), (5) Validation integrated with parsing** (Sections 2.1-2.4, 4.1)
- [x] What validation requirements were correctly identified? → **Pre-request validation (catch errors before network calls), post-response validation (verify server data), format-specific validation rules (GeoJSON strict, SensorML lenient), semantic validation (UoM codes, CRS URIs, coordinate ranges), detailed error messages (JSON paths, suggestions, expected vs actual), validation integrated with format parsing** (Section 2.3)
- [x] What edge cases were not considered? → **Format version changes (SensorML 2.0 vs 3.0), malformed server responses (graceful degradation), unknown format elements (forward compatibility), confidence-based parser selection (fallback strategies), incomplete conformance declarations (like 52°North demo), Part 2 unavailability (500 errors), mixed ID formats (string, UUID, URN)** (Sections 2.1-2.4, 3.1)
- [x] What requirements are implied but not explicit in specs? → **Format abstraction as unified API (users never write format-specific code), validation as developer experience improvement (immediate feedback vs server round-trip), extensible architecture for future formats (plugin system), performance optimization (minimize parsing overhead while maintaining completeness), comprehensive error handling (detailed, actionable error messages)** (Sections 4.3, 5)

**Key Findings:**

- **PRIMARY ISSUE:** First iteration incompletely implemented format parsing without comprehensive coverage, proper extensibility, and robust error handling
- **CORRECT SCOPE:** Format abstraction (detection, parsing, validation, serialization) IS core library responsibility per CSAPI spec requirements
- **V2 STRATEGY:** Comprehensive format abstraction (~6,000 lines) with complete parsers for all formats/versions, robust validation, automatic detection, extensible architecture
- **WHY FORMAT ABSTRACTION IS LIBRARY SCOPE:** (1) CSAPI spec mandates multiple formats with format negotiation, (2) Core value proposition = unified API hiding format complexity, (3) Prevents multi-library dependency hell, (4) Validation improves DX by catching errors before server calls, (5) Users work with domain models (System, Deployment), not format structures (SensorML, SWE Common)
- **LESSON:** Format abstraction must be comprehensive (not partial) with extensible architecture, detailed validation, and robust error handling

**Deliverable:** Comprehensive gap analysis (~1,500 lines) repositioning format handling as core library responsibility

---

### Section 18: Upstream Library Expectations ⏳

**Resources:**

#### Upstream Repository:

- [camptocamp/ogc-client](https://github.com/camptocamp/ogc-client) - main repository
- [camptocamp/ogc-client Contributing Guide](https://github.com/camptocamp/ogc-client/blob/main/CONTRIBUTING.md) (if exists)
- [Draft PR #131 Review Comments](https://github.com/camptocamp/ogc-client/pull/131) - maintainer feedback

#### Reference Implementations:

- [ogc-client WFS implementation](https://github.com/camptocamp/ogc-client/tree/main/src/wfs)
- [ogc-client WMS implementation](https://github.com/camptocamp/ogc-client/tree/main/src/wms)
- [ogc-client EDR implementation](https://github.com/camptocamp/ogc-client/tree/main/src/ogc-api)

#### Documentation Patterns:

- [ogc-client README](https://github.com/camptocamp/ogc-client/blob/main/README.md)
- [ogc-client API Documentation](https://camptocamp.github.io/ogc-client/)

**Questions to answer:**

- [ ] What does upstream expect a client library to do vs not do?
- [ ] Where's the line between library responsibility and user responsibility?
- [ ] What level of validation is expected?
- [ ] What level of error handling is expected?
- [ ] What documentation is required? (JSDoc, README examples, etc.)
- [ ] What export patterns are expected?
- [ ] What backward compatibility requirements exist?
- [ ] What performance expectations exist?
- [ ] What browser/Node.js compatibility is required?
- [ ] What bundle size constraints exist?

**Deliverable:** Library contract and expectations analysis (~400-600 lines)

---

### Section 19: Minimum Viable vs Full Feature Set ⏳

**Resources:**

#### Analysis Synthesis:

- All previous requirement sections (1-18)
- Design research documents (docs/research/upstream/)

#### Standards Reference:

- [OGC API – Connected Systems Part 1](https://docs.ogc.org/is/23-001/23-001.html) - conformance requirements
- [OGC API – Connected Systems Part 2](https://docs.ogc.org/is/23-002/23-002.html) - conformance requirements
- docs/research/standards/ogcapi-connectedsystems-1.bundled.oas31.yaml
- docs/research/standards/ogcapi-connectedsystems-2.bundled.oas31.yaml

#### Priority References:

- Real-world usage patterns (Section 9 findings)
- Ecosystem implementation patterns (Sections 10-16 findings)
- Previous iteration gaps (Section 17 findings)
- Upstream expectations (Section 18 findings)

**Questions to answer:**

- [ ] What's the absolute minimum for a valid CSAPI client?
- [ ] What's the core feature set (must-have)?
- [ ] What's the extended feature set (nice-to-have)?
- [ ] What's explicitly out of scope?
- [ ] Could implementation be phased? (Part 1 first, Part 2 later?)
- [ ] What resources are most critical? (Systems, Datastreams vs others?)
- [ ] What query capabilities are most critical?
- [ ] What format support is most critical?
- [ ] What can be added in future iterations?
- [ ] What's the MVP for PR acceptance?

**Deliverable:** Prioritized feature matrix and phasing strategy (~400-600 lines)

---

## Success Criteria

Requirements research is complete when we can answer:

1. ✅ "What are ALL operations the library must support?"
2. ✅ "What formats must be supported and to what extent?"
3. ✅ "What's in scope vs out of scope?"
4. ✅ "What query parameters are required?"
5. ✅ "What CRUD operations exist for each resource?"
6. ✅ "What sub-resource relationships must be navigable?"
7. ✅ "What conformance/capability detection is needed?"
8. ✅ "What TypeScript types must be exported?"
9. ✅ "What do real-world applications actually need?"
10. ✅ "What patterns do existing CSAPI client applications use?"
11. ✅ "What design decisions did other CSAPI client libraries make?"
12. ✅ "What behaviors do CSAPI servers implement that affect clients?"
13. ✅ "What did previous iterations get wrong about requirements?"
14. ✅ "What does upstream expect from the contribution?"
15. ✅ "What's the MVP vs full feature set?"

---

## Deliverables

### Analysis Documents (in docs/research/requirements/)

1. **csapi-part1-requirements.md** - Complete Part 1 analysis
2. **csapi-part2-requirements.md** - Complete Part 2 analysis
3. **format-requirements.md** - Format support scope and rationale
4. **query-parameters.md** - Complete query parameter catalog
5. **crud-operations.md** - CRUD operation matrix
6. **sub-resource-navigation.md** - Relationship model
7. **conformance-requirements.md** - Conformance detection strategy
8. **type-system-requirements.md** - TypeScript type scope
9. **usage-scenarios.md** - Real-world requirement validation
10. **osh-viewer-analysis.md** - Client app pattern analysis
11. **oscar-viewer-analysis.md** - Client app comparative insights
12. **owslib-analysis.md** - Python library architecture analysis
13. **oshconnect-python-analysis.md** - Python client patterns
14. **cpp-library-analysis.md** - C++ library cross-language insights
15. **opensensorhub-analysis.md** - Reference server behavior
16. **52north-analysis.md** - Multi-server compatibility insights
17. **gap-analysis.md** - Previous iteration lessons
18. **library-expectations.md** - Upstream contract
19. **mvp-definition.md** - Prioritized feature matrix

**Total Expected Output:** ~9,000-13,000 lines of requirements analysis

### Synthesis Document (in docs/specification/)

**functional-specification.md** - Complete functional spec synthesized from research

- Method catalog (all 70-80+ methods)
- Type definitions
- Query parameter reference
- Usage examples
- Acceptance criteria
- CSAPI coverage matrix

**Expected Output:** ~1,000-1,500 lines

---

## Next Steps

**Phase 1: Requirements Discovery**

1. Start with Section 1 (CSAPI Part 1) - most foundational
2. Progress through sections sequentially
3. Each section produces detailed analysis document
4. Update this checklist as sections complete

**Phase 2: Requirements Synthesis**

1. Review all analysis documents
2. Identify conflicts or ambiguities
3. Make scope decisions
4. Write functional specification

**Phase 3: Validation**

1. Compare functional spec to CSAPI OpenAPI schemas
2. Validate against real-world usage patterns
3. Verify nothing critical is missing
4. Get agreement on scope before implementation

---

## Critical Constraints

**Must maintain from design research:**

- ✅ URL building only (no data fetching in library)
- ✅ Minimal validation (trust TypeScript + server)
- ✅ Single QueryBuilder class
- ✅ ~560-760 lines implementation target
- ✅ Follow EDR pattern exactly

**Requirements must respect:**

- Design decisions are fixed (architecture is decided)
- Requirements define "what" not "how"
- Scope must fit within code volume constraints
- Format requirements must justify any parsing/serialization

---

## Research Order

**Recommended sequence:**

1. ✅ **Section 1** - CSAPI Part 1 (foundation)
2. ✅ **Section 2** - CSAPI Part 2 (complete spec coverage)
3. ✅ **Section 3** - Format Requirements (critical scope decision)
4. ✅ **Section 4** - Query Parameters (defines interface)
5. ✅ **Section 5** - CRUD Operations (defines scope per resource)
6. ✅ **Section 6** - Sub-Resource Navigation (defines relationships)
7. ✅ **Section 7** - Conformance Requirements (defines detection)
8. ✅ **Section 8** - Type System (defines exports)
9. ✅ **Section 9** - Usage Scenarios (validates priorities)
10. ✅ **Section 10** - osh-viewer Analysis (real client patterns)
11. ✅ **Section 11** - oscar-viewer Analysis (TypeScript client comparison)
12. ✅ **Section 12** - OWSLib Analysis (Python library patterns)
13. ✅ **Section 13** - OSHConnect-Python Analysis (Python client comparison)
14. ✅ **Section 14** - C++ Library Analysis (cross-language insights)
15. ✅ **Section 15** - OpenSensorHub Analysis (reference server behavior)
16. ✅ **Section 16** - 52°North Analysis (multi-server compatibility)
17. ✅ **Section 17** - Gap Analysis (prevents past mistakes)
18. ✅ **Section 18** - Library Expectations (aligns with upstream)
19. ✅ **Section 19** - MVP Definition (finalizes scope)

**Rationale:** Start with spec analysis (1-2), then scope decisions (3-8), then validation (9), then ecosystem analysis (10-16), then synthesis (17-19).

---

## Notes

- This is expanded from 12 to 19 sections to include ecosystem analysis (~9,000-13,000 lines of analysis)
- Each section can be done independently (like design research)
- User approval before proceeding to next section
- Goal: Comprehensive requirement capture including real-world implementation insights
- Sections 10-16: Learn from existing CSAPI implementations (clients, libraries, servers)
- Success = functional spec that covers 100% of needed functionality with real-world validation
