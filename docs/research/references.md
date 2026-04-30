# CSAPI Implementation References

**Purpose:** Annotated bibliography of key resources for implementing OGC Connected Systems API (CSAPI) support in the Camptocamp OGC Client Library.

**Last Updated:** March 6, 2026

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
10. [Design Research](#design-research)
11. [Testing Research](#testing-research)
12. [Planning Documents](#planning-documents)
13. [Governance Documents](#governance-documents)
14. [Implementation Records](#implementation-records)
15. [Testing Documentation](#testing-documentation)
16. [Upstream PR Preparation](#upstream-pr-preparation)
17. [Demo Application](#demo-application)
18. [Live Infrastructure](#live-infrastructure)

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

## Design Research

### Component Design Sequence

**URL:** https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/design/design-sequence.md  
**Type:** Internal research document

Defines the order in which CSAPI components should be designed and implemented. Establishes dependency chains between format handlers, query builder, and integration layer.

**Key Relevance:**

- Implementation ordering to avoid circular dependencies
- Component dependency chain documentation
- Risk mitigation through sequenced design

---

### Design Strategy Research

**URL:** https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/strategy/design-strategy-research.md  
**Type:** Internal research document

High-level design strategy for the CSAPI implementation, covering architectural trade-offs, integration approach, and format abstraction layer design.

**Key Relevance:**

- Strategic design decisions for the overall CSAPI module
- Format abstraction layer architecture
- Integration approach with upstream library

---

### CSAPIQueryBuilder Architecture Decisions

**URL:** https://github.com/OS4CSAPI/ogc-client-CSAPI_2/tree/main/docs/research/design/csapiquerybuilder/architecture-decision/  
**Type:** Internal research document series (22 research plans + findings + results)

Comprehensive architecture decision series for CSAPIQueryBuilder design. Includes analysis of PR #114 EDR pattern, QueryBuilder pattern, architecture patterns, OWS patterns, OSHConnect detailed analysis, and scope analysis for Part 1 and Part 2. Produced decision records for validation approach and multi-class architecture lessons learned.

**Key Documents:**

- `01-pr114-edr-pattern.md` — EDR implementation blueprint analysis
- `02-querybuilder-pattern.md` — QueryBuilder pattern deep dive
- `03-csapi-architecture-decisions.md` — Core architecture choices
- `04-architecture-patterns.md` — Pattern comparison analysis
- `05-owslib-pattern.md` — OWSLib reference implementation study
- `06-oshconnect-detailed.md` — OSHConnect-Python detailed analysis
- `07-oshconnect-summary.md` — OSHConnect condensed findings
- `08-oscar-viewer.md` through `22-part2-openapi.md` — Extended research series
- `findings/` — Research findings for each plan
- `results/DECISION-part3-validation.md` — Validation architecture decision
- `results/LESSONS-LEARNED-multi-class-failure.md` — Multi-class architecture failure analysis

**Key Relevance:**

- Definitive architecture decisions for CSAPIQueryBuilder
- Pattern evaluation and selection rationale
- Scope boundaries for Part 1 and Part 2
- Lessons learned from abandoned multi-class approach

---

### Collections Reader Research

**URL:** https://github.com/OS4CSAPI/ogc-client-CSAPI_2/tree/main/docs/research/design/collections-reader/  
**Type:** Internal research documents

Research into how the upstream library's collections reader works and how CSAPI resources integrate with the existing collection discovery infrastructure.

**Key Documents:**

- `collections-reader-research-plan.md` — Research plan
- `collections-reader-analysis.md` — Analysis findings

**Key Relevance:**

- Understanding collection discovery for CSAPI resource types
- Integration with existing OgcApiEndpoint collection metadata

---

### OGCAPIEndpoint Integration Research

**URL:** https://github.com/OS4CSAPI/ogc-client-CSAPI_2/tree/main/docs/research/design/ogcapiendpoint-integration/  
**Type:** Internal research documents

Research into how the CSAPI module integrates with the existing OgcApiEndpoint class, covering factory method patterns, conformance detection, and capability discovery.

**Key Documents:**

- `ogcapiendpoint-integration-research-plan.md` — Research plan
- `ogcapiendpoint-integration-analysis.md` — Analysis findings

**Key Relevance:**

- Factory method integration pattern
- Conformance detection for `hasConnectedSystems`
- Minimal-touch integration with upstream endpoint class

---

## Testing Research

### Testing Strategy Research

**URL:** https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/testing/testing-strategy-research.md  
**Type:** Internal research document

Comprehensive testing strategy for the CSAPI implementation covering unit tests, integration tests, fixture sourcing, and coverage targets. Supersedes earlier testing research versions.

**Key Relevance:**

- Overall testing approach and quality gates
- Fixture strategy for 9 resource types
- Coverage targets and metrics
- Test organization and naming conventions

---

### Testing Research Plans (20 Plans)

**URL:** https://github.com/OS4CSAPI/ogc-client-CSAPI_2/tree/main/docs/research/testing/research-plans/  
**Type:** Internal research document series

Systematic 20-plan research series covering all testing dimensions for the CSAPI implementation.

**Key Documents:**

- `01-pr114-blueprint-analysis.md` — EDR test blueprint as reference
- `02-upstream-test-consistency.md` — Maintaining upstream test patterns
- `03-typescript-testing-standards.md` — TypeScript-specific testing requirements
- `04-implementation-guide-testing-requirements.md` — Testing requirements from implementation guide
- `05-roadmap-testing-integration.md` — Roadmap-aligned testing milestones
- `06-meaningful-vs-trivial-definition.md` — Defining meaningful test coverage
- `07-end-to-end-testing-scope.md` — E2E testing boundaries
- `08-csapi-specification-test-requirements.md` — Spec-driven test requirements
- `09-sensorml-testing-requirements.md` — SensorML parser testing
- `10-swe-common-testing-requirements.md` — SWE Common parser testing
- `11-geojson-csapi-testing-requirements.md` — GeoJSON CSAPI extension testing
- `12-querybuilder-testing-strategy.md` — QueryBuilder method testing
- `13-resource-method-testing-patterns.md` — Resource method test patterns
- `14-integration-test-workflow-design.md` — Integration test workflows
- `15-fixture-sourcing-organization.md` — Fixture sourcing and organization
- `16-worker-extensions-testing.md` — Web Worker extension testing
- `17-coverage-targets-metrics.md` — Coverage targets and metrics
- `18-error-condition-testing.md` — Error condition coverage
- `19-test-organization-file-structure.md` — Test file structure
- `20-test-to-code-ratio-validation.md` — Test-to-code ratio validation

**Key Relevance:**

- Comprehensive testing framework for all CSAPI components
- Spec-driven test requirement extraction
- Coverage target definitions and validation criteria

---

### Testing Research Findings

**URL:** https://github.com/OS4CSAPI/ogc-client-CSAPI_2/tree/main/docs/research/testing/findings/  
**Type:** Internal research document series

Findings documents produced from executing the 20 testing research plans. Each findings document summarizes discoveries and actionable recommendations.

**Key Documents:**

- `01-edr-test-blueprint.md` through `09-sensorml-testing-requirements.md`
- Corresponding to research plans 01-09

**Key Relevance:**

- Actionable test requirements extracted from research
- Pattern documentation for test implementation

---

### Testing Strategy Review Phases

**URL:** https://github.com/OS4CSAPI/ogc-client-CSAPI_2/tree/main/docs/research/testing/review/  
**Type:** Internal research document series

Multi-phase review of testing strategy covering foundation validation, fixtures, testing patterns, standards quality, CSAPI-specific testing, advanced scenarios, and integration workflows.

**Key Documents:**

- `phase-0-lessons-from-failed-attempt.md` — Lessons from failed testing approach
- `phase-1-foundation-validation.md` — Foundation validation review
- `phase-2a-fixtures-category.md` — Fixture review
- `phase-2b-testing-patterns-category.md` — Testing patterns review
- `phase-2c-standards-quality-category.md` — Standards quality review
- `phase-2d-csapi-specific-testing-category.md` — CSAPI-specific testing review
- `phase-2e-advanced-scenarios-category.md` — Advanced scenarios review
- `phase-2f-integration-workflow-category.md` — Integration workflow review
- `notes-parser-testing-vs-spec-validation.md` — Parser testing vs spec validation analysis
- `notes-why-models-default-to-server-validation.md` — Server validation default rationale

**Key Relevance:**

- Quality gates for testing strategy completeness
- Lessons from iterative strategy refinement
- Parser testing philosophy decisions

---

## Planning Documents

### CSAPI Implementation Roadmap (Top-Level)

**URL:** https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/planning/ROADMAP.md  
**Type:** Internal planning document

Master roadmap for the entire CSAPI implementation spanning all phases. Defines phase progression from initial architecture through upstream contribution.

**Key Relevance:**

- Overall project timeline and phase definitions
- Phase dependency chain
- Milestone tracking across all phases

---

### CSAPI Implementation Guide (Top-Level)

**URL:** https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/planning/csapi-implementation-guide.md  
**Type:** Internal planning document

Comprehensive implementation guide for CSAPI support in the Camptocamp OGC Client Library. Covers architecture, component design, format handlers, testing requirements, and integration approach.

**Key Relevance:**

- Definitive architecture reference for the CSAPI module
- Component specifications and interfaces
- Format handler design requirements
- Integration requirements with upstream library

---

### Contribution Goal and Definition (Top-Level)

**URL:** https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/planning/contribution-goal-and-definition.md  
**Type:** Internal planning document

Defines what constitutes a complete, contribution-ready CSAPI implementation. Establishes acceptance criteria for the upstream PR.

**Key Relevance:**

- PR acceptance criteria definition
- Contribution completeness requirements
- Quality bar for upstream submission

---

### Phase 5: Parser Completion — Roadmap

**URL:** https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/planning/phase-5/P5-ROADMAP.md  
**Type:** Internal planning document

Phase 5 roadmap for completing all remaining parser implementations including parseProperty, parseDatastream, parseObservation, parseControlStream, parseCommand, and schema response parsers.

**Key Relevance:**

- Parser completion task sequencing
- Sub-phase definitions (5.1 through 5.4)
- Phase 5 completion criteria

---

### Phase 5: Parser Completion — Implementation Guide

**URL:** https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/planning/phase-5/P5-parser-completion-implementation-guide.md  
**Type:** Internal planning document

Detailed implementation guide for Phase 5 parser completion. Specifies parser signatures, field mappings, test requirements, and integration wiring for all remaining parsers.

**Key Relevance:**

- Parser function signatures and contracts
- Field mapping specifications from server response to parsed types
- Test fixture requirements per parser
- Integration wiring into CSAPIQueryBuilder

---

### Phase 5: Parser Completion — Contribution Goal and Definition

**URL:** https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/planning/phase-5/P5-contribution-goal-and-definition.md  
**Type:** Internal planning document

Phase 5 specific contribution definition establishing what "parser completion" means and the quality requirements for each parser.

**Key Relevance:**

- Parser completeness definition
- Per-parser acceptance criteria
- Coverage requirements for Phase 5

---

### Phase 5: Parser Completion — Task Package

**URL:** https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/planning/phase-5/parser-completion-task-package.md  
**Type:** Internal planning document

Consolidated task package for Phase 5 parser completion work. Bundles all parser tasks with dependencies, estimates, and verification criteria.

**Key Relevance:**

- Task-level breakdown of parser work
- Dependency ordering between parsers
- Verification checklist per task

---

### Phase 6: Upstream Acceptance Refactoring — Roadmap

**URL:** https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/planning/phase-6/P6-ROADMAP.md  
**Type:** Internal planning document

Phase 6 roadmap for refactoring the implementation to meet upstream acceptance requirements. Covers architectural decoupling, code quality normalization, and PR preparation.

**Key Relevance:**

- Upstream acceptance requirements mapped to refactoring tasks
- Architectural decoupling specifications
- Code quality normalization checklist
- PR submission timeline

---

### Phase 6: Upstream Acceptance Refactoring — Implementation Guide

**URL:** https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/planning/phase-6/P6-implementation-guide.md  
**Type:** Internal planning document

Detailed implementation guide for Phase 6 refactoring. Specifies the exact changes required to satisfy jahow's architectural requirements: CSAPI removal from root index.ts, isolation enforcement, sub-path exports, and code quality alignment.

**Key Relevance:**

- Exact refactoring specifications for upstream acceptance
- jahow's architectural requirements mapped to code changes
- Sub-path export configuration
- Prettier/ESLint/TypeScript normalization scope

---

### Phase 6: Upstream Acceptance Refactoring — Contribution Goal and Definition

**URL:** https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/planning/phase-6/P6-contribution-goal-and-definition.md  
**Type:** Internal planning document

Phase 6 specific contribution definition establishing what "upstream acceptance ready" means and the quality requirements for the final PR.

**Key Relevance:**

- PR acceptance readiness definition
- jahow's requirements traceability
- Final quality gate criteria

---

### Phase 6: Work Assessment and Strategy

**URL:** https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/planning/phase-6/work-assessment-and-strategy.md  
**Type:** Internal planning document

Initial assessment of Phase 6 work scope and strategic approach. Evaluates the remaining effort to achieve upstream acceptance.

**Key Relevance:**

- Effort estimation for Phase 6
- Risk assessment for upstream acceptance
- Strategic approach to refactoring

---

## Governance Documents

### AI Collaboration Agreement

**URL:** https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/governance/AI_Collaboration_Agreement.md  
**Type:** Internal governance document

Establishes the terms and expectations for AI-assisted development in this project. Defines roles, responsibilities, quality standards, and collaboration protocols.

**Key Relevance:**

- Foundational governance for AI-assisted development
- Quality standards and review requirements
- Collaboration workflow definitions
- Accountability framework

---

### AI Operational Constraints

**URL:** https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/governance/AI_OPERATIONAL_CONSTRAINTS.md  
**Type:** Internal governance document

Defines operational boundaries and constraints for AI agents working on this project. Specifies prohibited actions, required verifications, and safety rails.

**Key Relevance:**

- Operational safety boundaries for AI agents
- Required verification steps before destructive actions
- Prohibited modification scopes
- Mandatory confirmation requirements

---

### Known Server Quirks, Bugs, and Limitations

**URL:** https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/governance/known-server-quirks.md  
**Type:** Internal governance document

Catalog of known server-side issues, non-compliant behaviors, and workarounds for CSAPI test servers (OpenSensorHub, 52°North). Documents how the client library handles server quirks.

**Key Relevance:**

- Server compatibility workarounds
- Known non-compliant server behaviors
- Adaptive client behavior documentation
- Test fixture accuracy notes

---

### Phase 2 Implementation Lessons Learned

**URL:** https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/governance/phase-2-lessons-learned.md  
**Type:** Internal governance document

Lessons learned from Phase 2 implementation covering testing strategy effectiveness, code review findings, iterative development patterns, and fixture management.

**Key Relevance:**

- Testing strategy refinement insights
- Code review process improvements
- Implementation velocity lessons
- Fixture management best practices

---

### Phase 3 Implementation Lessons Learned

**URL:** https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/governance/phase-3-lessons-learned.md  
**Type:** Internal governance document

Lessons learned from Phase 3 implementation covering complex format handler development, SWE Common encoding challenges, and smoke test methodology refinements.

**Key Relevance:**

- Format handler development insights
- SWE Common complexity management
- Live server smoke test methodology
- Iterative quality assurance patterns

---

### Code Review Prompt Templates

**URLs:**

- **Base:** https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/governance/code-review-prompt-template.md
- **Phase 3:** https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/governance/code-review-prompt-template-phase-3.md
- **Phase 5:** https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/governance/code-review-prompt-template-phase-5.md
- **Phase 6:** https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/governance/code-review-prompt-template-phase-6.md

**Type:** Internal governance templates

Prompt templates for conducting systematic code reviews at each implementation phase. Each template specifies review scope, quality criteria, and acceptance gates appropriate to the phase's objectives.

**Key Relevance:**

- Reproducible code review process
- Phase-specific quality criteria
- Systematic defect detection methodology
- Quality gate enforcement

---

### Smoke Test Prompt Templates

**URLs:**

- **Base:** https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/governance/smoke-test-prompt-template.md
- **Phase 3:** https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/governance/smoke-test-prompt-template-phase-3.md
- **Phase 4:** https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/governance/smoke-test-prompt-template-phase-4.md
- **Phase 5:** https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/governance/smoke-test-prompt-template-phase-5.md
- **Phase 6:** https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/governance/smoke-test-prompt-template-phase-6.md

**Type:** Internal governance templates

Prompt templates for conducting live server smoke tests against OpenSensorHub and 52°North CSAPI servers. Phase 6 template covers architecture verification testing rather than live server testing.

**Key Relevance:**

- Live server validation methodology
- Reproducible smoke test process
- Phase-specific test scope definitions
- Architecture verification (Phase 6)

---

### Issue Creation Prompt Templates

**URLs:**

- **Base:** https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/governance/issue-creation-prompt-template.md
- **Phase 4:** https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/governance/issue-creation-prompt-template-phase-4.md
- **Phase 5:** https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/governance/issue-creation-prompt-template-phase-5.md
- **Phase 6:** https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/governance/issue-creation-prompt-template-phase-6.md
- **Code Review:** https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/governance/issue-creation-prompt-template-code-review.md

**Type:** Internal governance templates

Prompt templates for creating well-structured GitHub issues from findings at each phase. The code review template (Template C) adds ownership verification for distinguishing CSAPI-owned vs upstream-owned findings.

**Key Relevance:**

- Consistent issue creation process
- Ownership verification workflow
- Phase-specific categorization and labeling
- Severity assessment framework (P1-P4)

---

## Implementation Records

### Phase Assessments and Overviews

**URLs:**

- `docs/implementation/phase-0-baseline-assessment.md` — Phase 0 baseline assessment
- `docs/implementation/phase-1-overview.md` — Phase 1 implementation overview
- `docs/implementation/phase-1-completion-assessment.md` — Phase 1 completion assessment
- `docs/implementation/phase-1-fix-report.md` — Phase 1 fix report
- `docs/implementation/phase-2-overview.md` — Phase 2 implementation overview
- `docs/implementation/phase-2.1-overview.md` — Phase 2.1 implementation overview
- `docs/implementation/phase-2.2-overview.md` — Phase 2.2 implementation overview
- `docs/implementation/phase-2.3-overview.md` — Phase 2.3 implementation overview

**Type:** Internal implementation records

Phase-level assessment and overview documents tracking implementation progress, completion criteria, and quality metrics at each milestone.

**Key Relevance:**

- Implementation progress tracking
- Phase completion verification
- Quality metrics and defect tracking
- Decision rationale documentation

---

### Code Review Reports

**URLs:**

- `docs/implementation/phase-1-code-review.md` — Phase 1
- `docs/implementation/phase-2.2-code-review.md` — Phase 2.2
- `docs/implementation/phase-2.3-code-review.md` — Phase 2.3
- `docs/implementation/phase-2.4-code-review.md` — Phase 2.4
- `docs/implementation/phase-2.5-code-review.md` — Phase 2.5
- `docs/implementation/phase-2.6-code-review.md` — Phase 2.6
- `docs/implementation/phase-2.7-code-review.md` — Phase 2.7
- `docs/implementation/phase-2.8-code-review.md` — Phase 2.8
- `docs/implementation/phase-2.9-code-review.md` — Phase 2.9
- `docs/implementation/phase-3.1-code-review.md` through `phase-3.17-code-review.md` — Phase 3 (17 sub-phases)
- `docs/implementation/phase-3.8-code-review.md` — Phase 3.8
- `docs/implementation/phase-3.9-code-review.md` — Phase 3.9
- `docs/implementation/phase-5.1-code-review.md` — Phase 5.1
- `docs/implementation/phase-5.2-code-review.md` — Phase 5.2
- `docs/implementation/phase-5.3-code-review.md` — Phase 5.3
- `docs/implementation/phase-5.4-code-review.md` — Phase 5.4

**Type:** Internal implementation records (40+ reports)

Systematic code review reports for each implementation sub-phase. Each report documents findings, defects, fixes applied, and quality assessment.

**Key Relevance:**

- Cumulative defect history and resolution
- Quality trend tracking across phases
- Code review methodology evolution
- Finding categorization (critical, major, minor, cosmetic)

---

### Live Server Smoke Test Reports

**URLs:**

- `docs/implementation/live-server-smoke-test-52north.md` — 52°North initial test
- `docs/implementation/live-server-smoke-test-post-phase-2.1.md` through `post-phase-2.9.md` — Phase 2 series (9 reports)
- `docs/implementation/live-server-smoke-test-post-phase-3.1.md` through `post-phase-3.16.md` — Phase 3 series (10 reports)
- `docs/implementation/live-server-smoke-test-post-phase-4.1.md` — Phase 4 report
- `docs/implementation/live-server-smoke-test-post-phase-5.1.md` through `post-phase-5.5.md` — Phase 5 series (4 reports)
- `docs/implementation/live-server-smoke-test-post-phase-6.1.md` — Phase 6 report
- `docs/implementation/live-server-retest-post-issues-34-35.md` — Post-fix retest

**Type:** Internal implementation records (25+ reports)

Live server validation reports against OpenSensorHub (http://45.55.99.236:8080/sensorhub/api) and 52°North (https://csa.demo.52north.org/) CSAPI servers. Documents real-world interoperability testing results.

**Key Relevance:**

- Real-world server compatibility validation
- Format parsing verification against live data
- Server quirk discovery and documentation
- Regression detection across implementation phases

---

### Findings Analyses and Design Notes

**URLs:**

- `docs/implementation/p5-findings-coverage-analysis.md` — Phase 5 findings coverage analysis
- `docs/implementation/p4-findings-code-vs-docs-reassessment.md` — Phase 4 findings reassessment
- `docs/implementation/p4-crud-findings-scope-assessment.md` — Phase 4 CRUD findings scope
- `docs/implementation/outstanding-findings-status-report.md` — Outstanding findings status
- `docs/implementation/deferred-findings-final-disposition.md` — Deferred findings final disposition
- `docs/implementation/cross-server-interoperability-analysis.md` — Cross-server interoperability
- `docs/implementation/d1-d3-d4-fix-recommendations.md` — Design finding fix recommendations
- `docs/implementation/f70-design-findings-investigation.md` — F70 design findings investigation
- `docs/implementation/f57-content-negotiation-correction.md` — F57 content negotiation correction
- `docs/implementation/design-notes-validation-extraction-decoupling.md` — Validation/extraction decoupling
- `docs/implementation/note-crud-smoke-test-readiness.md` — CRUD smoke test readiness
- `docs/implementation/note-F71-osh-accept-header-noncompliance.md` — OSH Accept header noncompliance
- `docs/implementation/phase-3-smoke-test-rationale.md` — Phase 3 smoke test rationale

**Type:** Internal implementation records

Targeted analyses of specific findings, design decisions, and issue investigations produced during implementation.

**Key Relevance:**

- Finding triage and disposition decisions
- Design trade-off documentation
- Server noncompliance workarounds
- Scope boundary decisions for deferred work

---

### Final Project Code Review

**URL:** https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/implementation/final-project-code-review.md  
**Type:** Internal implementation record

End-to-end code review of the complete CSAPI implementation prior to upstream submission. Covers all components, test coverage, documentation completeness, and PR readiness.

**Key Relevance:**

- Final quality assessment before upstream submission
- Comprehensive component review
- PR readiness verification
- Outstanding issue identification

---

## Testing Documentation

### Test Fixtures Guide

**URL:** https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/testing/fixtures-guide.md  
**Type:** Internal testing document

Guide for CSAPI test fixture sourcing, organization, and maintenance. Covers fixture naming conventions, directory structure, live server fixture capture process, and fixture validation.

**Key Relevance:**

- Test fixture creation and management process
- Fixture naming and organization conventions
- Live server data capture methodology
- Fixture validation requirements

---

### Demo App Findings (Issues #5–#110)

**URL:** https://github.com/OS4CSAPI/ogc-client-CSAPI_2/tree/main/docs/testing/demo-app-findings/  
**Type:** Internal testing document series (25+ findings)

Findings discovered during CSAPI Explorer demo app development and live server integration testing. Each document maps to a GitHub issue and documents the problem, impact, and recommended fix.

**Key Documents:**

- `issue-5-nested-create-methods.md` — Nested create method design
- `issue-6-content-type-helper.md` — Content type helper utility
- `issue-11-generic-crud-methods.md` — Generic CRUD method design
- `issue-12-constructor-parameter-narrowing.md` — Constructor parameter types
- `issue-13-type-guard-functions-for-union-narrowing.md` — Type guard utilities
- `issue-14-resource-discovery-non-standard-links.md` — Non-standard link handling
- `issue-15-parse-location-header.md` — Location header parsing
- `issue-100-assert-resource-available.md` through `issue-110-link-resolution-utilities.md` — Phase 4/5 findings

**Key Relevance:**

- Real-world integration testing findings
- API design improvement recommendations
- Type safety gap identification
- Live server compatibility issues

---

## Upstream PR Preparation

### PR Strategy Discussion

**URL:** https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/upstream-pr-preparation/01-strategy-discussion.md  
**Type:** Internal planning document

Strategy discussion for preparing the upstream PR to camptocamp/ogc-client. Covers PR presentation, commit history approach, review facilitation, and maintainer communication.

**Key Relevance:**

- PR presentation strategy
- Commit history clean-up approach
- Maintainer communication plan
- Review facilitation techniques

---

### Rebase Plan — Clean PR

**URL:** https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/upstream-pr-preparation/02-rebase-plan.md  
**Type:** Internal planning document

Detailed plan for rebasing the development history into a clean, reviewable commit sequence for the upstream PR. Defines the 16-commit structure ultimately used in PR #136.

**Key Relevance:**

- Commit sequence design for PR reviewability
- Interactive rebase strategy
- Commit message standards
- History clean-up methodology

---

### Lessons Learned: CI Formatting Check Failure

**URL:** https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/upstream-pr-preparation/03-lessons-learned-ci-formatting.md  
**Type:** Internal governance document

Documents the CI formatting check failure encountered on PR #136 and the resolution. Prettier formatting differences between local and CI environments.

**Key Relevance:**

- CI pipeline compatibility requirements
- Prettier formatting alignment with upstream
- Pre-push validation checklist

---

### Upstream PR #136

**URL:** https://github.com/camptocamp/ogc-client/pull/136  
**Type:** External upstream PR

The actual pull request submitted to camptocamp/ogc-client adding Connected Systems API (CSAPI) support. 86 files changed, ~32,000 lines added, 16 commits, currently in draft status.

**Key Relevance:**

- The upstream contribution this entire project produces
- jahow's review feedback (architectural decoupling requirements)
- CI verification on Ubuntu
- Commit history and PR description as delivered

---

## Demo Application

### CSAPI Demo Webapp — Assessment & Recommendations

**URL:** https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/webapp-demo/demo-app-assessment.md  
**Type:** Internal documentation

Assessment of the CSAPI Explorer Vue.js demo application in the `app/` directory. Evaluates the demo app's coverage of CSAPI features, API surface exercise, and suitability for integration testing.

**Key Relevance:**

- Demo app capability assessment
- CSAPI feature coverage evaluation
- Integration testing utility analysis

---

### CSAPI Explorer — Session Handoff & Context Briefing

**URL:** https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/webapp-demo/session-handoff.md  
**Type:** Internal documentation

Session handoff document for continuing CSAPI Explorer demo app development. Provides context briefing on app architecture, current state, and next steps.

**Key Relevance:**

- Demo app architecture documentation
- Development continuation context
- Current state and remaining work

---

## Live Infrastructure

### OpenSensorHub Demo Server

**URL:** http://45.55.99.236:8080/sensorhub/api  
**Status:** Active (as of March 2026)  
**Operator:** OpenSensorHub project

Production-ready Java-based CSAPI server with full Part 1 + Part 2 + Part 3 support. Hosts 6 active systems, 28 datastreams, thousands of observations with real-time streaming capabilities.

**Key Relevance:**

- Primary test server for live validation
- Complete conformance implementation
- Real-time streaming test target
- Rich format support (GeoJSON, SensorML, SWE Common JSON/Text/Binary)
- Test fixture source for all resource types

---

### 52°North Demo Server

**URL:** https://csa.demo.52north.org/  
**Status:** Degraded — SSL certificate expired, Part 2 non-functional (as of March 2026)  
**Operator:** 52°North GmbH

Python/pygeoapi-based CSAPI server with Part 1 support. Part 2 in active development but not yet functional on the public demo instance.

**Key Relevance:**

- Multi-server compatibility testing (different implementation stack)
- Partial conformance testing (Part 1 only)
- Server quirk documentation (pagination differences, format variations)
- Validates adaptive client behavior when server capabilities vary

---

### OS4CSAPI Fork (Clean PR Source)

**URL:** https://github.com/OS4CSAPI/ogc-client  
**Branch:** `clean-pr` (tip: `6e759a6`)  
**Status:** Active — GitHub Actions CI verified passing (Run #22428856030)

Fork of camptocamp/ogc-client used as the source for PR #136. Contains the clean 16-commit history ready for upstream review.

**Key Relevance:**

- Source repository for upstream PR #136
- CI verification on Ubuntu (GitHub Actions)
- Clean commit history for review

---

### connected-systems-go Demo Server (Go / PostGIS)

**URL:** https://129-80-248-53.sslip.io/csapi-go (representative deployment, as of April 2026)  
**Repository:** https://github.com/OS4CSAPI/connected-systems-go  
**Status:** Active — early/in-development; multiple known conformance gaps tracked in that repo's issues  
**Operator:** OS4CSAPI

Go-based CSAPI server backed by PostGIS. Surfaced post–Phase 6 during the [`ogc-csapi-explorer`](https://github.com/OS4CSAPI/ogc-csapi-explorer) demo-app effort and the OSHConnect-Python publisher fleet migration. Default page size differs materially from OpenSensorHub (Go default is small — typically 10 — vs. OSH's 100), and several spec-required behaviors are not yet implemented or are partially implemented.

**Key Relevance:**

- Third independent implementation in our test corpus, beyond OpenSensorHub (Java) and 52°North (Python). Critical for surfacing single-server-corpus blind spots — both [#166](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/166) (Part 2 `@link` fallback) and [#167](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/167) (pagination-contract documentation) were identified by exercising this server.
- Emits Part 2 cross-references using the `@link` form (object) where OSH emits the `@id` form (scalar). Both are spec-legal per OGC 23-002 §16.1; the existence of two encodings in the wild is the motivation for [#166](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/166).
- Default `limit` of 10 (vs. OSH's 100) makes pagination correctness materially more important; documented in [#167](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/167).
- Several open conformance issues against the server are tracked at [`OS4CSAPI/connected-systems-go`](https://github.com/OS4CSAPI/connected-systems-go/issues) — see the "Known Server Conformance Gaps" subsection below for the catalog as it bears on our client.

---

### Known Server Conformance Gaps

This subsection records empirically-observed deviations from the OGC API — Connected Systems specifications that we have encountered while testing our client against live servers. It is **not** a comprehensive conformance audit; it is a working log of behaviors that have shaped client-side decisions (or that explicitly did **not** result in client-side changes, with rationale).

**Purpose:** Future contributors investigating "why doesn't my query work as the spec says?" should consult this catalog before assuming the bug is in our library. Issues in our repo (e.g. [#168](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/168)) have been incorrectly framed as library bugs in the past; this catalog is the institutional memory that keeps that from recurring.

#### Gap 1 — `connected-systems-go`: Temporal query parameters silently ignored

**Server:** `connected-systems-go` (all builds as of April 2026).  
**Tracked at:** [`OS4CSAPI/connected-systems-go#11`](https://github.com/OS4CSAPI/connected-systems-go/issues/11)  
**Surfaced by:** [`OS4CSAPI/ogc-client-CSAPI_2#168`](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/168) (originally filed as a client-side library bug; closed `wontfix` after empirical re-test reattributed the failure to the server).

**Spec citation:** OGC 23-002r0 §13.3.2 `/req/advanced-filtering/obs-by-resulttime`, statement D — _"the parameter SHALL also support the special value `latest`. When this special value is used, only observations with the latest result time SHALL be included in the result set."_ Plus the broader OGC 23-002 temporal-parameter family (`datetime`, `phenomenonTime`, `resultTime`, `issueTime`, `executionTime`).

**Empirical behavior (probed 2026-04-17, recorded against `https://129-80-248-53.sslip.io/csapi-go`):**

| Request                                                 | Observed response                                                                 | Implication                                                     |
| ------------------------------------------------------- | --------------------------------------------------------------------------------- | --------------------------------------------------------------- |
| `?resultTime=latest`                                    | 200 OK, server's default page (10 items, unfiltered)                              | `latest` keyword silently discarded                             |
| `?resultTime=latest&limit=1`                            | 200 OK, 1 item — happens to be the newest because Go's default sort is descending | "Works" by accident; the parameter still has no semantic effect |
| `?resultTime=frobnicate`                                | 200 OK, 10 items (default page, unfiltered)                                       | Invalid values silently accepted; no validation                 |
| `?resultTime=` (empty)                                  | 200 OK, 10 items from today (default page, unfiltered)                            | Empty values silently accepted                                  |
| `?resultTime=2026-01-01T00:00:00Z/2026-01-02T00:00:00Z` | Behavior consistent with above — interval form also appears unfiltered            | Whole temporal-parameter family appears non-functional          |

**Scope of the gap on the server:** Probably broader than `resultTime=latest`. The probe pattern (silent acceptance of invalid values, default page returned regardless) is consistent with all five temporal keys (`datetime`, `phenomenonTime`, `resultTime`, `issueTime`, `executionTime`) being non-functional on this server. Not all five have been individually probed; the assumption that the gap covers the family is informed by the uniform behavior across the values that _have_ been probed.

**Client-side disposition:** No change. Our client correctly serializes every temporal parameter and `latest` keyword per spec ([`src/ogc-api/csapi/helpers.ts:26-28`](src/ogc-api/csapi/helpers.ts#L26-L28), [`src/ogc-api/csapi/url_builder.ts:351-358`](src/ogc-api/csapi/url_builder.ts#L351-L358)). The library does the right thing; the server discards it silently. Adding a server-specific compatibility shim was considered ([#168](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/168) Option A) and rejected — see that issue's status banner for full reasoning. Summary of the rejection: shimming one keyword of one parameter of five is selective and unprincipled; the deprecation path (remove once Go ships the fix) means we'd be adding a method we already plan to remove; consumer-side ergonomic problems belong in consumer repos. A consumer-side helper for the [`ogc-csapi-explorer`](https://github.com/OS4CSAPI/ogc-csapi-explorer) `MapViewPage.vue` use case is tracked separately.

**Defensive guidance for consumers of our library:** If you target a server that may belong to this class, do not assume `resultTime=latest` (or any temporal filter) has narrowed the result set. Verify temporal-filter behavior empirically against your target server before relying on it. The server is required by spec to honor these parameters; relying on them is correct in principle, but defensive coding (`limit=1` + sort-aware fallback) is a reasonable belt-and-suspenders strategy when targeting servers in this class.

#### Gap 2 — `connected-systems-go`: `?uid=` filter silently ignored on list endpoints

**Server:** `connected-systems-go` (all builds as of April 2026).  
**Tracked at:** [`OS4CSAPI/connected-systems-go#5`](https://github.com/OS4CSAPI/connected-systems-go/issues/5)  
**Surfaced by:** [OSHConnect-Python publisher fleet migration](https://github.com/OS4CSAPI/OSHConnect-Python/issues/4) — `find_by_uid` returned `None` for resources that existed; root-caused to the server returning the unfiltered default page when `?uid=` was supplied.

**Spec citation:** OGC 23-001 — Common query parameters; servers expose `uid` as a queryable filter on resource list endpoints.

**Empirical behavior:** Server returns its default unfiltered page regardless of `?uid=` value. Workaround on the consumer side: client-side filter loop with `&limit=1000` to paper over the missing server-side filter. Documented as fragile in the consumer-side bug ([`OSHConnect-Python#4`](https://github.com/OS4CSAPI/OSHConnect-Python/issues/4)) — `limit=1000` is a magic number that breaks at scale.

**Client-side disposition:** No change. Filter-honoring is a server obligation; clients construct correct URLs (which we do).

**Cross-cutting interaction:** When this gap and Gap 1 above co-occur on the same server (as they currently do on `connected-systems-go`), client-side correctness depends on (a) following `next` HATEOAS links per spec, and (b) not relying on temporal filters to narrow result sets. Both are spec-required of conformant clients regardless of server quirks; both are documented as consumer obligations in the JSDoc work tracked by [#167](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/167).

#### Gap 3 — `connected-systems-go`: Default page size of 10 (small relative to OSH)

**Server:** `connected-systems-go`.  
**Tracked at:** Behavior, not defect — fully spec-legal per OGC 23-001 §7.6 (default page size is server-defined). Surfaced as a _client documentation_ issue at [#167](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/167).

**Empirical behavior:** Default `limit` is 10 (vs. OSH's 100). Spec-legal but enough smaller than OSH that consumers who never tested against this server class can experience silent first-page-only behavior in production.

**Client-side disposition:** Documentation-only fix (Phase 8 finding 167). JSDoc on every public list method explicitly documents the pagination contract (the server picks the default; consumers must follow `next` HATEOAS links to retrieve subsequent pages). No behavior change.

#### Gap 4 — `52°North`: Part 2 endpoints non-functional + expired SSL

**Server:** 52°North demo (as of March–April 2026).  
**Tracked at:** Out-of-repo — 52°North project's own tracker.

**Empirical behavior:** Public demo SSL certificate expired (CONNECT fails); separately, Part 2 endpoints are not yet functional on the public instance per their own roadmap. We have not been able to probe Part 2 conformance against this server.

**Client-side disposition:** No change possible — server unreachable. Recorded here so future contributors don't waste cycles re-discovering the same wall.

#### Pattern observed across gaps

Three of the four cataloged gaps come from one server (`connected-systems-go`) and were surfaced post–Phase 6 by stress-testing the client against a wider implementation corpus. The pattern is: **each gap was at first reflexively framed as a client-side bug, then re-attributed to the server after empirical re-test.** This is the pattern the catalog exists to break — before filing a "library doesn't honor X" issue against this repo, probe the server's behavior independently and confirm the failure is on the client side.

**Empirical-probe template** for future contributors investigating an apparent client bug:

1. Build the URL with our library (manually verify it matches the spec).
2. `curl -v` (or browser DevTools) the same URL directly against the server.
3. Compare what came back to what the spec mandates.
4. If server response disagrees with spec → file in the _server's_ repo, record here, leave the client alone.
5. If client URL disagrees with spec → file against the client.

Skipping step 2 has cost us cycles in #166, #167, and #168. The catalog above exists so that cost doesn't repeat.

---

## Research Findings Not Adopted

This subsection records research investigations that surfaced real, useful operational knowledge but **did not result in a library change** — typically because the proposed change was too opinionated, too consumer-specific, or architecturally premature. Capturing the knowledge here keeps the operational insight without committing the library to maintaining a heuristic API surface.

### Finding 1 — Observation `result` geographic-coordinate naming-convention diversity

**Surfaced by:** [`OS4CSAPI/ogc-client-CSAPI_2#169`](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/169) (closed `wontfix` 2026-04-29 after Phase 8 triage).
**Origin context:** Live integration testing of the [`ogc-csapi-explorer`](https://github.com/OS4CSAPI/ogc-csapi-explorer) demo app's `MapViewPage.vue` against the [OSHConnect-Python](https://github.com/OS4CSAPI/OSHConnect-Python) 10-publisher fleet (ISS SGP4, OpenSky ADS-B, USGS Earthquake, NWS Surface Obs, NDBC Buoy, CO-OPS Tide, UAS Localizer, etc.) and OSH SensorHub.

**The empirical observation worth preserving:**

CSAPI publishers in our test corpus encode geographic position inside observation `result` payloads using at least **six distinct field-name conventions**, none of which are mandated or even mentioned by OGC 23-002:

| #   | Convention              | Example fields                                 | Observed publishers                                  |
| --- | ----------------------- | ---------------------------------------------- | ---------------------------------------------------- |
| 1   | Direct, lowercase short | `lat`, `lon`, `alt`                            | NWS Surface Obs, NDBC Buoy, CO-OPS Tide              |
| 2   | Nested, capitalized     | `Location.lat`, `Location.lon`, `Location.alt` | UAS Localizer                                        |
| 3   | Nested, lowercase       | `location.lat`, `location.lon`, `location.alt` | (variant of #2 in some publishers)                   |
| 4   | Full-word, lowercase    | `latitude`, `longitude`, `altitude`            | OpenSky ADS-B, USGS Earthquake                       |
| 5   | Full-word, title-case   | `Latitude`, `Longitude`, `Altitude`            | (observed in some triangulated-position datastreams) |
| 6   | Suffixed with unit hint | `lat_deg`, `lon_deg`, `alt_km`                 | ISS Position (SGP4)                                  |

**Unit ambiguity across the convention set:** Convention 6 's `alt_km` is **kilometers**, while the unsuffixed `altitude` from OpenSky may be meters _or_ feet (varies by publisher), and `Location.alt` from the UAS localizer is unspecified. There is no convention by which a consumer can recover units from the field name alone in the general case.

**Why we did not ship a library-level extraction helper:**

A heuristic extractor (the original Option A in [#169](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/169)) was rejected on five grounds — the issue's status banner has the full reasoning. Headlines:

1. **Unit ambiguity is a silent data-loss footgun.** Returning a single `alt: number` field while the source units span km, m, and ft (and unspecified) silently corrupts altitude semantics. Fixing this requires an `altUnit` field, which defeats the convenience pitch.
2. **Heuristic false positives are unbounded.** A datastream with calibration parameters coincidentally named `lat`/`lon` would silently match. There is no spec-grounded way to assert "this `lat` field carries WGS 84 latitude in degrees."
3. **The architecturally correct answer is SWE Common, not field-name matching.** OGC 23-002 references SWE Common for result schemas; SWE Common defines `Vector` types with a proper `referenceFrame` (CRS) and per-component `uom`. A schema-aware extractor reading the datastream's `resultEncoding` / `resultStructure` is the right path. Heuristic field-name matching encodes our 10-publisher fleet as a library opinion.
4. **Maintenance trap.** Six conventions today; a seventh, eighth, ninth tomorrow as new publishers join. Each addition is a minor version bump downstream consumers must adopt to see the new convention. The Explorer's local 30-line function can be edited in place; an exported library function cannot.
5. **Sampling-feature ambiguity.** For most publishers, geographic positioning belongs on `SamplingFeature` or `System.position`, not embedded in `result`. The publishers that embed coordinates in result do so because _the position itself is the observation_ (ISS, localizer) — but that is a narrow class. A library helper that normalizes this away discourages publishers from making the architectural choice consciously.

**The right future path (deferred):**

A SWE Common–aware result-vector extractor that consumes the datastream's `resultStructure` to identify components by `definition` URI (e.g. matching SWE Common's standard latitude/longitude definitions) and applies the per-component `uom` to return values with explicit units. This is large enough that it should not block on the heuristic version; it is tracked at [`OS4CSAPI/ogc-client-CSAPI_2#171`](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/171) (deferred until upstream PR #136 lands and library scope is broadened).

**Defensive guidance for consumers (until the SWE Common path lands):**

- Implement a small consumer-local extractor matched to your specific publisher fleet. Six conventions is a lot if you're targeting "any CSAPI server in the world"; it is small and stable if you're targeting a known set of publishers.
- Always pair coordinate values with a known unit assumption documented in the consumer (do not ship a "best-effort" unit guess).
- For multi-publisher map views, prefer extracting position from `SamplingFeature` or `System.position` where available — those _are_ standardized by OGC 23-002.

**Cross-references:**

- [`OS4CSAPI/ogc-client-CSAPI_2#169`](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/169) — research issue, closed `wontfix` (status banner has full triage reasoning).
- [`OS4CSAPI/ogc-client-CSAPI_2#171`](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/171) — deferred follow-up: SWE Common–aware extraction (the architecturally correct future path).
- [`OS4CSAPI/ogc-csapi-explorer`](https://github.com/OS4CSAPI/ogc-csapi-explorer) — `MapViewPage.vue` 30-line `extractLatLonFromResult()` continues to be the right place for this logic until the SWE Common path is available; an Explorer-side TODO has been filed.

---

## Notes

### Document Maintenance

- Add new references as discovered during implementation
- Update URLs if specifications move
- Note specification version changes (CSAPI may evolve to 1.1, 2.0, etc.)
- Track implementation-specific resources (blog posts, tutorials, tools)

### Potential Future References

Resources to consider adding as they become relevant:

- TypeScript libraries for SWE Common/SensorML parsing (if any emerge)
- Performance benchmarks for observation streaming
- Security considerations (OAuth2, API keys) for CSAPI endpoints
- Real-world CSAPI deployment case studies
- Additional CSAPI server implementations beyond OpenSensorHub and 52°North
- OGC Testbed reports involving Connected Systems API
