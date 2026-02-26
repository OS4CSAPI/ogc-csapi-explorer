# CSAPI Implementation References

**Purpose:** Annotated bibliography of key resources for implementing OGC Connected Systems API (CSAPI) support in the Camptocamp OGC Client Library.

**Last Updated:** February 2, 2026

---

## Table of Contents

1. [OGC CSAPI Standards](#ogc-csapi-standards)
2. [Related OGC Standards](#related-ogc-standards)
3. [Foundational Semantic Standards](#foundational-semantic-standards)
4. [Data Encoding Standards](#data-encoding-standards)
5. [Code Repositories](#code-repositories)
6. [Vocabularies and Ontologies](#vocabularies-and-ontologies)
7. [Supporting Specifications](#supporting-specifications)
8. [Requirements Research](#requirements-research)
9. [Upstream Research](#upstream-research)

---

## OGC CSAPI Standards

### OGC API - Connected Systems - Part 1: Feature Resources

**URL:** https://docs.ogc.org/is/23-001/23-001.html  
**Document ID:** OGC 23-001  
**Status:** Approved Implementation Standard (2024)

Defines the core CSAPI resources representing physical and logical assets in observation and control systems: Systems, Deployments, Procedures, Sampling Features, and Properties. Specifies REST API patterns for discovery, CRUD operations, hierarchical relationships, and query parameters for these metadata resources. This is the foundation for understanding what sensors/actuators exist, where they're deployed, how they observe, and what they observe.

**Key Relevance:**

- Primary specification for Part 1 resource types and their properties
- Defines conformance classes we need to detect (`hasConnectedSystems`)
- Specifies query parameters: bbox, datetime, id, uid, q, recursive, parent, deployment, procedure, foi, observedProperty, controlledProperty
- Defines collection metadata structures for CSAPI resources
- Establishes GeoJSON and SensorML encoding requirements

---

### OGC API - Connected Systems - Part 1: OpenAPI Specification

**URL:** https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/standards/ogcapi-connectedsystems-1.bundled.oas31.yaml  
**Format:** OpenAPI 3.1 (YAML)  
**Status:** Bundled specification (all references resolved)

Machine-readable OpenAPI definition of the CSAPI Part 1 REST API. Describes all endpoints, query parameters, request/response schemas, and error codes for Systems, Deployments, Procedures, Sampling Features, and Properties resources.

**Key Relevance:**

- Definitive source for endpoint paths and HTTP methods
- Query parameter validation rules and constraints
- Response schema definitions for all Part 1 resources
- Error response formats and status codes
- Could enable runtime API validation or dynamic client generation
- Reference for implementing URL builder methods in CSAPIQueryBuilder

---

### OGC API - Connected Systems - Part 2: Dynamic Data

**URL:** https://docs.ogc.org/is/23-002/23-002.html  
**Document ID:** OGC 23-002  
**Status:** Approved Implementation Standard (2024)

Extends Part 1 with dynamic observation and control data resources: DataStreams, Observations, Control Streams, and Commands. Specifies schema-driven observation ingestion, temporal queries, cursor-based pagination for high-volume data, command submission, and status tracking. This enables reading sensor data and controlling actuators beyond just metadata discovery.

**Key Relevance:**

- Primary specification for Part 2 resource types and operations
- Defines temporal query parameters: phenomenonTime, resultTime, executionTime, issueTime
- Specifies both pagination modes: offset-based (Part 1) and cursor-based (Part 2)
- Establishes schema requirements for DataStreams and ControlStreams
- Defines bulk operations for observations and commands
- Specifies SWE Common 3.0 encoding requirements for observation results

---

### OGC API - Connected Systems - Part 2: OpenAPI Specification

**URL:** https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/standards/ogcapi-connectedsystems-2.bundled.oas31.yaml  
**Format:** OpenAPI 3.1 (YAML)  
**Status:** Bundled specification (all references resolved)

Machine-readable OpenAPI definition of the CSAPI Part 2 REST API. Describes all endpoints, query parameters, request/response schemas, and error codes for DataStreams, Observations, Control Streams, and Commands resources.

**Key Relevance:**

- Definitive source for endpoint paths and HTTP methods for dynamic data
- Temporal query parameter definitions with ISO 8601 interval formats
- Schema endpoint definitions for DataStreams and ControlStreams
- Observation result encoding specifications (JSON, Text, Binary)
- Command submission, status tracking, and result retrieval patterns
- Pagination parameter constraints (limit: 1-10000, cursor format)
- Reference for implementing URL builder methods for Part 2 resources

---

## Related OGC Standards

### OGC SensorML 3.0

**URL:** https://docs.ogc.org/is/23-000r1/23-000r1.html  
**Document ID:** OGC 23-000r1  
**Status:** Approved Implementation Standard (2024)  
**JSON Schema:** https://schemas.opengis.net/sensorml/3.0/

The latest Sensor Model Language standard providing rich XML-free JSON-native metadata for sensors, actuators, platforms, and processing chains. Complete rewrite from 2.x versions with modern JSON structure. Describes system capabilities, characteristics, components, connections, modes, and positions.

**Key Relevance:**

- Format we must parse for detailed System and Procedure descriptions
- Media type: `application/sml+json`
- Defines four concrete process types: SimpleProcess, AggregateProcess, PhysicalComponent, PhysicalSystem (plus abstract bases DescribedObject, AbstractProcess, AbstractPhysicalProcess)
- Integrates deeply with SWE Common 3.0 for capabilities, characteristics, parameters
- Supports recursive component hierarchies we need to parse
- Alternative to GeoJSON for Systems/Procedures when detailed technical metadata needed

---

### OGC SWE Common 3.0

**URL:** https://docs.ogc.org/is/23-011r1/23-011r1.html  
**Document ID:** OGC 23-011r1  
**Status:** Approved Implementation Standard (2024)  
**JSON Schema:** https://schemas.opengis.net/sweCommon/3.0/

Data component specification for structured observation and control data encoding. Defines schemas for measurement data (DataRecord, Quantity, DataArray, etc.) and three encoding formats: JSON (human-readable), Text/CSV (compact), Binary (efficient streaming). The "type system" for observation results and command parameters.

**Key Relevance:**

- Critical format for parsing observation results and command parameters
- Media types: `application/swe+json`, `application/swe+text`, `application/swe+binary`
- Defines all data component types we must support (12+ types including ranges, choices, geometry)
- Specifies schema validation rules for observations against DataStream schemas
- Binary encoding parsing is most complex: IEEE 754 floats, multi-byte integers, endianness
- Used in SensorML 3.0 for capabilities, characteristics, parameters (nested integration)

---

### OGC API - Common

**URL:** https://docs.ogc.org/is/19-072/19-072.html  
**Document ID:** OGC 19-072  
**Status:** Approved Implementation Standard

Foundation specification for all OGC API standards defining common patterns: landing page, conformance endpoint, collections endpoint, bbox/datetime parameters, pagination, error handling, and HATEOAS link patterns.

**Key Relevance:**

- Establishes patterns CSAPI extends (conformance checking, collections metadata)
- Defines standard query parameters we inherit: bbox, datetime, limit, offset, f
- Specifies link relation types and HATEOAS navigation patterns
- Conformance class detection pattern we follow for `hasConnectedSystems`
- Already implemented in camptocamp/ogc-client, we extend rather than rebuild

---

### OGC API - Features

**URL:** https://docs.ogc.org/is/17-069r4/17-069r4.html  
**Document ID:** OGC 17-069r4  
**Status:** Approved Implementation Standard

REST API for accessing geospatial features with GeoJSON encoding. CSAPI Part 1 resources are exposed as GeoJSON features with SOSA/SSN semantic properties.

**Key Relevance:**

- Part 1 resources use Features API patterns (items endpoint, GeoJSON encoding)
- Existing GeoJSON parser in library provides foundation we extend
- Query parameter patterns (bbox, datetime, limit, offset) inherited by CSAPI
- Feature collections pattern used for Systems, Deployments, Procedures, Sampling Features

---

## Foundational Semantic Standards

### SOSA/SSN (Semantic Sensor Network Ontology)

**W3C Recommendation:** https://www.w3.org/TR/vocab-ssn/  
**Namespace:** http://www.w3.org/ns/sosa/  
**Status:** W3C Recommendation (2017)

Semantic foundation for sensor and observation concepts. SOSA (Sensor, Observation, Sample, and Actuator) provides core classes and properties. SSN extends SOSA with additional concepts. CSAPI resources are instances of SOSA/SSN classes.

**Key Relevance:**

- Vocabulary for `systemType` property: `sosa:Sensor`, `sosa:Platform`, `sosa:Actuator`, `sosa:Sampler`
- Semantic model for resource relationships: system-deployment, system-procedure, observation-foi
- `featureType` property values reference SOSA classes
- Properties like `observedProperty`, `madeBySensor`, `hasFeatureOfInterest` from SOSA
- Validates our understanding of sensor observation patterns

---

### GeoJSON (RFC 7946)

**RFC:** https://tools.ietf.org/html/rfc7946  
**Status:** IETF Proposed Standard (2016)

JSON format for encoding geographic features with geometries and properties. Primary encoding for CSAPI Part 1 resources.

**Key Relevance:**

- All Part 1 resources encoded as GeoJSON features
- Library already has GeoJSON parser we extend with CSAPI-specific property extraction
- Geometry types for system locations, deployment footprints, sampling feature shapes
- Feature properties object contains CSAPI resource metadata
- Coordinate validation (WGS84, right-hand rule) we must enforce

---

## Data Encoding Standards

### ISO 8601 (Date and Time Format)

**ISO Standard:** https://www.iso.org/iso-8601-date-and-time-format.html  
**Wikipedia:** https://en.wikipedia.org/wiki/ISO_8601

International standard for date, time, and temporal interval representation. Used extensively in CSAPI for temporal queries and temporal properties.

**Key Relevance:**

- All temporal parameters use ISO 8601: datetime, phenomenonTime, resultTime, executionTime, issueTime
- Interval formats: instant, closed interval, open-start, open-end
- validTime property encoding for Systems, Deployments
- Temporal extent in collection metadata
- Must parse all interval types including open-ended (e.g., `2024-01-01/..`)

---

### UCUM (Unified Code for Units of Measure)

**Home:** http://unitsofmeasure.org/  
**Specification:** http://unitsofmeasure.org/ucum.html

Standard for representing units of measure in machine-readable format. Used in SWE Common for quantity units.

**Key Relevance:**

- Unit codes in SWE Common Quantity components: `Cel`, `m`, `Pa`, `%`, etc.
- Unit validation for observation results
- Unit conversion calculations when needed
- Scale factors and offsets in unit definitions
- Validates measurement data is physically meaningful

---

### IEEE 754 (Floating Point Arithmetic)

**Wikipedia:** https://en.wikipedia.org/wiki/IEEE_754

Standard for binary floating-point arithmetic. Used in SWE Common Binary encoding.

**Key Relevance:**

- Binary observation encoding uses IEEE 754 float32 and float64
- Must implement binary parsing with correct endianness (little-endian, big-endian)
- Precision considerations for measurement data
- Special values: NaN, Infinity for missing/invalid data
- Performance-critical for high-volume observation streaming

---

## Code Repositories

### camptocamp/ogc-client

**GitHub:** https://github.com/camptocamp/ogc-client  
**NPM:** https://www.npmjs.com/package/@camptocamp/ogc-client

The upstream library we're extending with CSAPI support. Provides unified OGC API access for Features, Tiles, Records, EDR, WMS, WFS, WMTS.

**Key Relevance:**

- Architecture patterns we must follow (OgcApiEndpoint, QueryBuilder classes)
- EDR implementation (PR #114) is our direct pattern: factory method, QueryBuilder, conformance detection
- Existing format handlers (GeoJSON, XML) we extend
- Web Worker infrastructure for background processing
- Testing patterns (Jest, fixtures) we replicate for CSAPI
- TypeDoc documentation style we match
- Integration requires ~48 lines across 2-3 files (endpoint.ts, info.ts, index.ts)

---

### OS4CSAPI/ogc-client-CSAPI_2

**GitHub:** https://github.com/OS4CSAPI/ogc-client-CSAPI_2

This repository - our development workspace for CSAPI implementation.

**Key Relevance:**

- Fork of camptocamp/ogc-client for CSAPI development
- Implementation guide and technical architecture in docs/planning/
- Will contain all new CSAPI code: CSAPIQueryBuilder, SensorML handler, SWE Common handler
- Test fixtures for CSAPI resources
- Integration point for upstream contribution

---

## Vocabularies and Ontologies

### QUDT (Quantities, Units, Dimensions and Data Types)

**Home:** http://www.qudt.org/  
**Vocabularies:** http://www.qudt.org/release2/qudt-catalog.html

Ontology for physical quantities, units, and dimensions. Common vocabulary for observed/controlled properties.

**Key Relevance:**

- Property definition URIs for observedProperty, controlledProperty
- Standard vocabulary alternative to CF Standard Names
- Quantity kinds (Temperature, Pressure, Velocity, etc.)
- Unit definitions with conversion factors
- Referenced in CSAPI examples and test servers

---

### CF Standard Names

**Home:** https://cfconventions.org/standard-names.html  
**Name Table:** https://cfconventions.org/Data/cf-standard-names/current/build/cf-standard-name-table.html

Standardized vocabulary for climate and forecast variables. Widely used in Earth observation communities.

**Key Relevance:**

- Alternative vocabulary for observedProperty in atmospheric/oceanic observations
- Standard names: `air_temperature`, `sea_surface_temperature`, etc.
- Canonical units and descriptions for each variable
- Common in meteorology, oceanography, climate science CSAPI deployments
- Many servers use CF names for property definitions

---

### EPSG Geodetic Parameter Dataset

**Home:** https://epsg.org/  
**Registry:** https://epsg.io/

Registry of coordinate reference systems, geodetic datums, and coordinate transformations.

**Key Relevance:**

- CRS codes for spatial data: EPSG:4326 (WGS84), EPSG:3857 (Web Mercator)
- Geometry validation requires CRS awareness
- Reference frames for Vector components in SWE Common
- Position definitions in SensorML
- Default CRS for CSAPI is WGS84 (EPSG:4326) per GeoJSON RFC 7946

---

## Supporting Specifications

### IANA Link Relations

**Registry:** https://www.iana.org/assignments/link-relations/link-relations.xhtml

Official registry of link relation types for HATEOAS navigation.

**Key Relevance:**

- Standard rel values: `self`, `alternate`, `collection`, `item`, `next`, `prev`
- CSAPI-specific relations: `system`, `deployment`, `procedure`, `datastream`, `observations`
- Link validation in GeoJSON features and collection metadata
- Navigation patterns between related resources

---

### JSON Schema

**Specification:** https://json-schema.org/  
**Latest Draft:** https://json-schema.org/draft/2020-12/json-schema-core.html

Standard for describing JSON document structure and validation rules.

**Key Relevance:**

- SensorML 3.0 and SWE Common 3.0 both have JSON Schemas for validation
- Schema validation in our parsers uses JSON Schema
- DataStream result schemas defined using JSON Schema subset
- ControlStream parameter schemas use similar patterns
- Type definitions inform our TypeScript interfaces

---

### OpenAPI Specification

**Home:** https://www.openapis.org/  
**Specification:** https://spec.openapis.org/oas/latest.html

Standard for describing REST APIs. OGC API standards provide OpenAPI definitions.

**Key Relevance:**

- CSAPI servers expose OpenAPI definitions at `/api` endpoint
- Describes available endpoints, query parameters, response schemas
- Could enable dynamic client generation or runtime validation
- Alternative to hard-coded URL patterns (future enhancement)
- Useful for testing against compliant servers

---

## Requirements Research

### Full Implementation Scope Definition

**URL:** https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/requirements/contribution-definition.md  
**Type:** Internal research document

Defines the complete implementation scope for CSAPI client library contribution to camptocamp/ogc-client, covering all resources (Part 1 + Part 2) and full format abstraction capabilities. Establishes that the implementation includes ALL CSAPI resources with comprehensive format parsing.

**Key Relevance:**

- Establishes complete vs partial implementation scope
- Defines feature completeness requirements
- Production-ready implementation goals
- Format abstraction layer requirements

---

### 52°North Server Implementation Analysis

**URL:** https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/requirements/csapi-52north-analysis.md  
**Type:** Internal research document  
**Live Demo Server:** https://csa.demo.52north.org/ (⚠️ expired SSL certificate, Part 2 non-functional)

Analyzes 52°North's Python-based CSAPI server implementation to understand multi-server compatibility requirements. Documents Python/pygeoapi architecture, partial conformance patterns, and differences from OpenSensorHub. Part 1 production-ready, Part 2 in active development.

**Key Relevance:**

- Multi-server compatibility requirements
- Server capability variation handling
- Pagination pattern differences between implementations
- Format support variations across servers
- Python/pygeoapi architecture patterns
- Adaptive behavior based on conformance detection

---

### Conformance and Capability Requirements

**URL:** https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/requirements/csapi-conformance-capabilities.md  
**Type:** Internal research document

Documents all conformance classes from CSAPI Part 1 and Part 2, detection mechanisms via /conformance endpoint, and capability discovery patterns. Defines minimum viable server configuration and graceful degradation strategies.

**Key Relevance:**

- Conformance class detection implementation
- hasConnectedSystems method requirements
- Runtime capability discovery
- Client adaptation to server capabilities

---

### C++ Client Analysis

**URL:** https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/requirements/csapi-cpp-analysis.md  
**Type:** Internal research document

Analysis of ConnectedSystemsAPI-CPP repository reveals it's an abandoned skeleton project with no meaningful implementation. Documents why this isn't a useful reference for design patterns.

**Key Relevance:**

- Negative example - what not to do
- Validates approach of studying Python clients instead
- Documents state of C++ CSAPI ecosystem (nonexistent)

---

### CRUD Operations Requirements

**URL:** https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/requirements/csapi-crud-operations.md  
**Type:** Internal research document

Documents all Create, Read, Update, Delete operations across CSAPI resources, HTTP method mappings, request/response requirements, and operation-specific constraints. Establishes which resources support full CRUD vs read-only.

**Key Relevance:**

- Complete CRUD operation matrix
- HTTP method to operation mapping
- Request body requirements for write operations
- Client API design for transactional operations

---

### Data Type and Schema Requirements

**URL:** https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/requirements/csapi-datatype-schema-requirements.md  
**Type:** Internal research document

Defines TypeScript type system requirements based on OpenAPI 3.1 schema analysis. Covers 100+ schema definitions including resource types, SWE Common data components, and supporting structures.

**Key Relevance:**

- 50+ TypeScript interfaces needed
- Hierarchical type system with inheritance
- Union types for polymorphic structures
- Generic types for collections and responses

---

### Common Format Requirements

**URL:** https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/requirements/csapi-format-requirements-3.1.md  
**Type:** Internal research document

Documents common format requirements and negotiation mechanisms applying across all CSAPI resources. Defines required vs optional formats, media type identifiers, and format negotiation strategies.

**Key Relevance:**

- Format negotiation implementation patterns
- Accept header vs query parameter strategies
- Minimum viable format support
- Parsing vs pass-through requirements

---

### Comprehensive Format Requirements

**URL:** https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/requirements/csapi-format-requirements.md  
**Type:** Internal research document

Comprehensive analysis of GeoJSON, SensorML, and SWE Common format requirements for CSAPI client library covering both Part 1 and Part 2 resources.

**Key Relevance:**

- Complete format parsing requirements
- GeoJSON CSAPI extensions
- SensorML 3.0 parsing needs
- SWE Common encoding handling (JSON/Text/Binary)

---

### Gap Analysis from Previous Iteration

**URL:** https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/requirements/csapi-gap-analysis.md  
**Type:** Internal research document

Identifies gaps, errors, and lessons from first implementation attempt. Documents incomplete format parsing that led to rejection and defines comprehensive format abstraction requirements for v2.

**Key Relevance:**

- Lessons from failed iteration
- Format abstraction importance
- Completeness requirements
- Error handling improvements needed

---

### OpenSensorHub Server Analysis

**URL:** https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/requirements/csapi-opensensorhub-analysis.md  
**Type:** Internal research document  
**Live Demo Server:** http://45.55.99.236:8080/sensorhub/api

Comprehensive analysis of OpenSensorHub's production-ready Java CSAPI server implementation. Documents full Part 1 + Part 2 + Part 3 coverage, rich format support, robust query engine, and provides extensive test fixtures. Includes access to live demo server with 6 active systems, 28 datastreams, and thousands of observations with real-time streaming.

**Key Relevance:**

- Primary server implementation to test against
- Complete conformance baseline
- Real-world format examples
- Query pattern validation
- Live demo server for real-time testing and validation
- Production-ready reference implementation

---

### oscar-viewer Client Application Analysis

**URL:** https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/requirements/csapi-oscarviewer-analysis.md  
**Type:** Internal research document

Analyzes oscar-viewer TypeScript React application for radiation detection monitoring. Documents production-grade patterns, TypeScript usage insights, and property-based discovery patterns.

**Key Relevance:**

- Real-world TypeScript CSAPI usage
- Multi-server federated query patterns
- Property-based datastream identification
- Real-time subscription patterns with Redux

---

### OSHConnect-Python Client Analysis (Detailed)

**URL:** https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/requirements/csapi-oshconnect-python-analysis.md  
**Type:** Internal research document

Detailed analysis of OSHConnect-Python's stateful, streaming-first approach with builder patterns and Pydantic models. Compares to OWSLib's stateless approach.

**Key Relevance:**

- Stateful vs stateless architecture decisions
- Builder pattern for query construction
- Real-time streaming (WebSocket/MQTT) integration
- Type safety with runtime validation

---

### OSHConnect-Python Client Analysis (Summary)

**URL:** https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/requirements/OSHConnect-Python-Analysis.md  
**Type:** Internal research document

Summary analysis of OSHConnect-Python demonstrating builder patterns, generic type system, Pydantic validation, and comprehensive CRUD operations for all CSAPI resources.

**Key Relevance:**

- Builder pattern reference implementation
- Request construction patterns
- Generic type system design
- Real-time streaming integration

---

### osh-viewer Client Application Analysis

**URL:** https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/requirements/csapi-oshviewer-analysis.md  
**Type:** Internal research document

Analyzes osh-viewer Vue.js web client to understand real-world CSAPI usage patterns. Documents read-heavy operations, System → Datastreams → Observations navigation, and format preferences.

**Key Relevance:**

- Common workflow patterns
- Offset-based pagination defaults
- Format selection strategy (SWE+JSON vs SWE+Binary)
- Object-oriented wrapper patterns

---

### OWSLib CSAPI Implementation Analysis

**URL:** https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/requirements/csapi-owslib-analysis.md  
**Type:** Internal research document

Analyzes OWSLib's mature Python CSAPI implementation with class-per-resource architecture, consistent CRUD operations, and complete coverage of all 11 resource types.

**Key Relevance:**

- Mature client library reference
- Class-per-resource architecture patterns
- Consistent naming conventions
- Comprehensive query parameter validation
- Authentication abstraction patterns

---

### CSAPI Part 1 Requirements

**URL:** https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/requirements/csapi-part1-requirements.md  
**Type:** Internal research document

Comprehensive analysis of OGC API – Connected Systems Part 1 standard extracting ALL requirements for TypeScript client implementation. Documents 5 resource types, 11 conformance classes, 70+ operations, and dual format support.

**Key Relevance:**

- Complete Part 1 specification analysis
- Systems, Deployments, Procedures, Sampling Features, Properties
- GeoJSON and SensorML format requirements
- 30+ query parameters for filtering
- Sub-resource navigation patterns

---

### CSAPI Part 2 Requirements

**URL:** https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/requirements/csapi-part2-requirements.md  
**Type:** Internal research document

Comprehensive analysis of OGC API – Connected Systems Part 2 standard for dynamic data. Documents DataStreams, Observations, Control Streams, Commands with schema operations, temporal queries, and pagination modes.

**Key Relevance:**

- Complete Part 2 specification analysis
- Schema-driven observation ingestion
- Temporal query parameters and intervals
- Cursor-based pagination for high-volume data
- Command submission and status tracking
- SWE Common encoding requirements

---

### Query Parameter Requirements

**URL:** https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/requirements/csapi-query-parameters.md  
**Type:** Internal research document

Catalogs ALL query parameters from CSAPI Part 1 and Part 2 with encoding rules, validation requirements, and parameter combination rules. Classifies parameters by type (spatial, temporal, pagination, format, relationship).

**Key Relevance:**

- Complete query parameter catalog
- Parameter encoding and validation rules
- Resource-specific applicability
- Parameter combination logic
- Client API query building interface

---

### Sub-Resource Navigation Requirements

**URL:** https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/requirements/csapi-subresource-navigation.md  
**Type:** Internal research document

Documents all nested navigation patterns including relationship endpoints, nesting depth, query parameter support on nested endpoints, and bidirectional relationship navigation.

**Key Relevance:**

- Nested endpoint URL construction
- Sub-resource relationship matrix
- Query parameter support on nested paths
- Canonical vs relationship URL patterns
- Link relation types for navigation

---

### Usage Scenarios and Priorities

**URL:** https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/requirements/csapi-usage-scenarios.md  
**Type:** Internal research document

Identifies 15 core real-world usage scenarios, 6 essential workflows, 8 common error patterns, and recommends 17 convenience methods to simplify client library usage.

**Key Relevance:**

- Prioritized usage scenarios
- Common workflow patterns
- Error handling requirements
- Convenience method design
- Performance recommendations

---

### Lessons Learned from Previous Iterations

**URL:** https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/requirements/lessons-learned-analysis.md  
**Type:** Internal research document

Documents what worked, what didn't, and what to improve from previous CSAPI implementation attempts. Identifies over-engineered vs under-engineered components and likely rejection points.

**Key Relevance:**

- Mistakes to avoid from previous attempts
- Over-engineering warnings
- Under-engineering gaps
- Maintenance and testing lessons
- PR review considerations

---

### Requirements Research Strategy

**URL:** https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/requirements/requirements-research-strategy.md  
**Type:** Internal research document

Defines systematic research-first methodology for identifying ALL functional requirements before writing specification. Lists requirement sources and research approach.

**Key Relevance:**

- Comprehensive requirement discovery methodology
- Research-before-implementation approach
- Requirement source identification
- Gap prevention strategy

---

### Upstream Library Expectations

**URL:** https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/requirements/upstream-expectations.md  
**Type:** Internal research document

Defines what camptocamp/ogc-client expects from CSAPI implementation based on patterns from WFS, WMS, WMTS, EDR implementations. Documents endpoint-oriented API expectations.

**Key Relevance:**

- Upstream integration requirements
- Established patterns to follow
- Quality standards and conventions
- Format abstraction alignment with existing parsers
- Web Worker support requirements

---

## Upstream Research

### Architecture Patterns Analysis

**URL:** https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/upstream/architecture-patterns-analysis.md  
**Type:** Internal research document

Documents the consistent architectural patterns used in camptocamp/ogc-client for adding new OGC API support. Analyzes endpoint extension patterns, collection capability determination, type organization, conformance checking, and shared utilities.

**Key Relevance:**

- Blueprint for how CSAPI should integrate with OgcApiEndpoint
- Pattern documentation for maintaining upstream consistency
- Guides architectural decisions for CSAPI implementation
- Reference for code organization and file structure

---

### Code Reuse vs Duplication Strategy

**URL:** https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/upstream/code-reuse-analysis.md  
**Type:** Internal research document

Defines when to reuse upstream utilities versus duplicate code for CSAPI implementation. Balances DRY principle against isolation and maintainability, with complete dependency mapping.

**Key Relevance:**

- Governs which shared utilities we import vs duplicate
- Minimizes coupling to upstream code for easier PR review
- Documents acceptable dependencies and isolation requirements
- Provides import guidelines for CSAPI development

---

### CSAPI Architecture Decisions

**URL:** https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/upstream/csapi-architecture-analysis.md  
**Type:** Internal research document

Documents architectural choices for implementing 9 CSAPI resource types within ogc-client patterns. Addresses Part 1 vs Part 2 architecture, sub-resource handling, shared vs unique implementations, and SWE Common/SensorML integration.

**Key Relevance:**

- Architectural decisions specific to CSAPI's complexity (9 resource types)
- Resource type organization strategy
- Part 1 (metadata) vs Part 2 (dynamic data) separation
- Foundation for CSAPIQueryBuilder design

---

### Error Handling Design Analysis

**URL:** https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/upstream/error-handling-analysis.md  
**Type:** Internal research document

Documents error handling patterns in ogc-client to guide CSAPI error strategy. Covers error classes, validation errors, missing resource errors, conformance errors, and distinguishes user errors from library errors.

**Key Relevance:**

- Error handling patterns to follow for consistency
- CSAPI-specific error scenarios (validation, schema mismatches)
- Error message design guidelines
- Integration with existing EndpointError patterns

---

### File Organization Strategy

**URL:** https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/upstream/file-organization-analysis.md  
**Type:** Internal research document

Documents file organization patterns in ogc-client to guide CSAPI implementation structure. Analyzes EDR file structure, test organization, fixture organization, export strategy, naming conventions, and import path patterns.

**Key Relevance:**

- Where to place CSAPIQueryBuilder, types, helpers, tests
- Fixture organization for 9 resource types
- Export strategy from src/ogc-api/csapi/index.ts
- Maintains repository organization consistency

---

### Format Negotiation Architecture

**URL:** https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/upstream/format-negotiation-analysis.md  
**Type:** Internal research document

Documents format negotiation patterns in ogc-client for handling multiple response formats. Covers Accept header strategy, query parameter format selection, link-based discovery, and format detection. Defines CSAPI format strategy for GeoJSON, SensorML, and SWE Common.

**Key Relevance:**

- How to implement format negotiation for CSAPI resources
- Media type handling: application/sml+json, application/swe+json, etc.
- Format detection and content type parsing
- Integration with format handlers

---

### Integration with Existing Code

**URL:** https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/upstream/integration-analysis.md  
**Type:** Internal research document

Documents the exact code changes required to integrate CSAPI into ogc-client. Analyzes EDR integration pattern and specifies precise modifications to endpoint.ts (~35 lines), info.ts (~7 lines), and index.ts (~6 lines).

**Key Relevance:**

- Line-by-line integration requirements
- Minimizing diff size for PR review
- Shared models and utilities reuse
- Implementation roadmap for core file modifications

---

### PR #114 (EDR Implementation) Analysis

**URL:** https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/upstream/pr114-analysis.md  
**Type:** Internal research document

Critical analysis of the merged EDR implementation PR (camptocamp/ogc-client#114). This is the direct blueprint for CSAPI implementation. Documents the factory method pattern, EDRQueryBuilder class structure, and integration approach.

**Key Relevance:**

- **PRIMARY REFERENCE** - Direct pattern to follow for CSAPI
- Confirms terminology: "QueryBuilder" not "navigator"
- Factory method signature and caching strategy
- File organization and test patterns
- Exact integration approach that upstream accepted

---

### QueryBuilder Pattern Analysis

**URL:** https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/upstream/querybuilder-pattern-analysis.md  
**Type:** Internal research document

Documents the QueryBuilder pattern used in ogc-client for API-specific query operations. Corrects terminology (was incorrectly called "navigator"), explains QueryBuilder lifecycle, state management, caching strategy, and resource availability checking.

**Key Relevance:**

- Core pattern for CSAPIQueryBuilder implementation
- State management and caching requirements
- Interface vs implementation separation
- Lifecycle from factory instantiation to URL building

---

### TypeScript Type System Design

**URL:** https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/upstream/typescript-types-analysis.md  
**Type:** Internal research document

Documents TypeScript type organization and design patterns used in ogc-client. Covers type hierarchy, query parameter type patterns, resource type modeling, shared vs specific parameters, type safety strategies, and type definition location.

**Key Relevance:**

- Type system design for CSAPI resources and query parameters
- Interface definition patterns for CSAPIQueryBuilder
- Parameter type organization (spatial, temporal, relationship, etc.)
- Type safety enforcement for query construction

---

### URL Building Architecture

**URL:** https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/upstream/url-building-analysis.md  
**Type:** Internal research document

Documents URL building patterns and practices used in ogc-client. Covers base URL strategy, query parameter assembly, URL encoding, parameter modeling, array parameters, base path construction, and resource path structure.

**Key Relevance:**

- URL construction patterns for CSAPIQueryBuilder methods
- Query parameter encoding for CSAPI-specific parameters
- Nested resource path building (e.g., /systems/{id}/subsystems)
- Array parameter handling (comma-separated IDs)

---

## Notes

### Document Maintenance

- Add new references as discovered during implementation
- Update URLs if specifications move
- Note specification version changes (CSAPI may evolve to 1.1, 2.0, etc.)
- Track implementation-specific resources (blog posts, tutorials, tools)

### Missing References

Resources we may need to add:

- Specific CSAPI server implementations as they become available
- TypeScript libraries for SWE Common/SensorML parsing (if any exist)
- Performance benchmarks for observation streaming
- Security considerations (OAuth2, API keys) for CSAPI endpoints
- Real-world CSAPI deployment case studies
