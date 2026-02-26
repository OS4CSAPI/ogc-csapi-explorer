# CSAPI Implementation Guide for Camptocamp OGC Client Library

**Last Updated:** February 2, 2026

---

## Executive Summary

This implementation adds Connected Systems API (CSAPI) support to the Camptocamp OGC Client Library, enabling developers to interact with sensor networks, observation data, and system control through the same unified interface they already use for OGC API Features, Tiles, and Environmental Data Retrieval (EDR).

**What We're Building:**

- **9 components extending existing code** - Small, targeted enhancements to conformance checking, collection parsing, format detection, validation, and worker infrastructure (~50 lines of modifications total)
- **3 components building new code** - CSAPIQueryBuilder class for URL construction (~10k-14k lines), SensorML 3.0 parser, and SWE Common 3.0 parser

**Key Architectural Facts:**

- **Integration Footprint:** ~48 lines across 2-3 files (`endpoint.ts`, `info.ts`, `index.ts`)
- **QueryBuilder Pattern:** Single `CSAPIQueryBuilder` class accessed via `endpoint.csapi(collectionId)` (follows upstream EDR pattern from PR #114)
- **9 Resource Types:** Systems, Deployments, Procedures, Sampling Features, Properties, DataStreams, Observations, Control Streams, Commands - all as methods within one QueryBuilder class
- **Full CSAPI Support:** Complete Parts 1 & 2 implementation with all query parameters, filtering, pagination, and format support - NOT MVP scope

**Scope Clarification:** While architecturally elegant (3 new classes, 9 extensions), the CSAPIQueryBuilder represents ~70% of new code volume because it implements comprehensive URL construction for 60-70 unique URL patterns across all CSAPI resource types with full CRUD, query, filter, and pagination capabilities. See [Summary: Build vs Extend Breakdown](#summary-build-vs-extend-breakdown) for detailed component inventory.

**Estimated Effort:** 6-8 weeks for complete implementation with 80% test coverage

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Table of Contents](#table-of-contents)
3. [Purpose and Scope](#purpose-and-scope)
4. [Architecture Overview](#architecture-overview)
   - [Component Interaction Diagram](#component-interaction-diagram)
5. [Service Discovery Components](#service-discovery-components)
   - [Conformance Reader](#conformance-reader-extending-existing-capability-detection)
   - [Collections Reader](#collections-reader-extending-metadata-parsing)
   - [OgcApiEndpoint Integration](#ogcapiendpoint-integration-extending-main-endpoint-class)
6. [Query Builder Component](#query-builder-component)
   - [CSAPIQueryBuilder Overview](#csapiquerybuilder-building-new-query-construction-class)
   - [Systems Resource Methods](#systems-resource-methods)
   - [Deployments Resource Methods](#deployments-resource-methods)
   - [Procedures Resource Methods](#procedures-resource-methods)
   - [Sampling Features Resource Methods](#sampling-features-resource-methods)
   - [Properties Resource Methods](#properties-resource-methods)
   - [DataStreams Resource Methods](#datastreams-resource-methods)
   - [Observations Resource Methods](#observations-resource-methods)
   - [Control Streams Resource Methods](#control-streams-resource-methods)
   - [Commands Resource Methods](#commands-resource-methods)
   - [Query Parameters Reference](#complete-query-parameter-support)
7. [Format Handler Components](#format-handler-components)
   - [GeoJSON Handler](#geojson-handler-extending-existing-parser)
   - [SensorML Handler](#sensorml-handler-building-new-format-parser)
   - [SWE Common Handler](#swe-common-handler-building-new-format-parser)
   - [Format Detector](#format-detector-extending-existing-content-negotiation)
   - [Validator](#validator-extending-existing-validation-framework)
8. [Worker Components](#worker-components)
   - [Background Processing](#background-processing-extending-existing-web-worker-pattern)
9. [Testing Components](#testing-components)
   - [Test Coverage](#test-coverage-extending-existing-test-suite)
10. [Documentation Components](#documentation-components)
    - [API Documentation](#api-documentation-extending-existing-typedoc-documentation)
11. [Summary: Build vs Extend Breakdown](#summary-build-vs-extend-breakdown)
12. [Project Goals Alignment](#project-goals-alignment)
13. [Development Standards](#development-standards)

---

## Purpose and Scope

This document describes every component needed to implement CSAPI support in the Camptocamp OGC Client Library, explaining which components extend existing code versus which require building new code from scratch.

**What This Document Provides:**

- Complete component inventory for CSAPI implementation
- Clear identification of "extend" vs "build" work
- Integration points with existing library code
- Query parameter reference for all CSAPI resources
- Development workflow recommendations

**Scope Statement:**
This implementation provides **COMPLETE CSAPI Parts 1 & 2 support** including:

- ✅ All query parameters (spatial, temporal, hierarchical, relationship-based, property-based)
- ✅ Full filtering capabilities (bbox, datetime, recursive, parent, system, foi, observedProperty, etc.)
- ✅ Both pagination modes (offset-based and cursor-based)
- ✅ All three SWE Common encodings (JSON, Text/CSV, Binary)
- ✅ Complete schema validation
- ✅ All CRUD operations

**This is NOT an MVP** - this is a production-ready, specification-complete implementation suitable for enterprise use.

**References:**

- [OGC API - Connected Systems Part 1: Feature Resources](https://docs.ogc.org/is/23-001/23-001.html) - Standard defining Systems, Deployments, Procedures, Sampling Features, Properties
- [OGC API - Connected Systems Part 2: Dynamic Data](https://docs.ogc.org/is/23-002/23-002.html) - Standard defining DataStreams, Observations, Control Streams, Commands
- [Full Implementation Scope Definition](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/requirements/contribution-definition.md) - Complete vs partial implementation rationale
- [CSAPI Part 1 Requirements](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/requirements/csapi-part1-requirements.md) - Comprehensive Part 1 requirements analysis
- [CSAPI Part 2 Requirements](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/requirements/csapi-part2-requirements.md) - Comprehensive Part 2 requirements analysis
- [Upstream Library Expectations](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/requirements/upstream-expectations.md) - What camptocamp/ogc-client expects from implementations

---

## Architecture Overview

### Component Interaction Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                      OgcApiEndpoint (existing)                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Developer Entry Points:                                 │   │
│  │  • endpoint.features(collectionId)  → FeaturesAPI        │   │
│  │  • endpoint.edr(collectionId)      → EDRQueryBuilder    │   │
│  │  • endpoint.csapi(collectionId)    → CSAPIQueryBuilder  │◄──┼── New Factory Method (~35 lines)
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  Conformance: hasConnectedSystems ◄─── New Getter (~7 lines)   │
│  Collections: csapiCollections    ◄─── New Getter (~6 lines)   │
└─────────────────────────────────────────────────────────────────┘
                            │
                            │ returns instance
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│             CSAPIQueryBuilder (NEW - single class)              │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Part 1 Resource Methods (Systems, Deployments, etc.):   │   │
│  │  • getSystems(params)              → URL                 │   │
│  │  • getDeployments(params)          → URL                 │   │
│  │  • getProcedures(params)           → URL                 │   │
│  │  • getSamplingFeatures(params)     → URL                 │   │
│  │  • getProperties(params)           → URL                 │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Part 2 Resource Methods (Observations, Commands, etc.): │   │
│  │  • getDataStreams(params)          → URL                 │   │
│  │  • getObservations(params)         → URL                 │   │
│  │  • getControlStreams(params)       → URL                 │   │
│  │  • getCommands(params)             → URL                 │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  All methods support FULL query parameters:                     │
│  • Spatial: bbox (2D/3D)                                        │
│  • Temporal: datetime, phenomenonTime, resultTime, etc.         │
│  • Hierarchical: recursive                                      │
│  • Relationship: parent, system, deployment, foi, etc.          │
│  • Pagination: limit, offset, cursor                            │
└─────────────────────────────────────────────────────────────────┘
                            │
                            │ constructs URLs for
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Format Handlers (parsers)                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │  GeoJSON     │  │  SensorML    │  │  SWE Common          │  │
│  │  Handler     │  │  Handler     │  │  Handler             │  │
│  │  (extend)    │  │  (NEW)       │  │  (NEW)               │  │
│  │              │  │              │  │                      │  │
│  │ • Systems    │  │ • Physical   │  │ • JSON encoding      │  │
│  │ • Deployments│  │   System     │  │ • Text/CSV encoding  │  │
│  │ • Procedures │  │ • Physical   │  │ • Binary encoding    │  │
│  │ • Sampling   │  │   Component  │  │ • Schema validation  │  │
│  │   Features   │  │ • System     │  │ • All DataComponent  │  │
│  │              │  │   Config     │  │   types              │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
│                                                                  │
│  Format Detector (extend) ◄─── Recognizes CSAPI media types    │
│  Validator (extend)       ◄─── Validates CSAPI resources       │
└─────────────────────────────────────────────────────────────────┘
                            │
                            │ offloads heavy parsing to
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Web Worker (existing pattern)                │
│  • SensorML 3.0 parsing (complex hierarchies)                   │
│  • SWE Common Binary decoding (large datasets)                  │
│  • Observation result validation (1000s of observations)        │
│  • Spatial/temporal filtering (large collections)               │
│                                                                  │
│  Extends existing worker with new CSAPI message types           │
└─────────────────────────────────────────────────────────────────┘
```

**Key Architectural Principles:**

1. **Unified Access:** All CSAPI functionality through `OgcApiEndpoint.csapi()` factory method
2. **Single QueryBuilder:** One `CSAPIQueryBuilder` class with methods for all 9 resource types (not 9 separate classes)
3. **Format Abstraction:** Developers work with TypeScript objects, format handlers parse wire formats transparently
4. **Minimal Integration:** ~48 lines of modifications to existing files maintain upstream compatibility
5. **Worker Offloading:** Heavy parsing/validation operations run off main thread for UI responsiveness

**References:**

- [Architecture Patterns Analysis](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/upstream/architecture-patterns-analysis.md) - Consistent patterns used in ogc-client for adding new OGC API support
- [PR #114 (EDR Implementation) Analysis](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/upstream/pr114-analysis.md) - Direct blueprint for CSAPI implementation, factory method pattern
- [QueryBuilder Pattern Analysis](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/upstream/querybuilder-pattern-analysis.md) - Core pattern for CSAPIQueryBuilder implementation
- [Integration with Existing Code](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/upstream/integration-analysis.md) - Exact code changes required for integration
- [CSAPI Architecture Decisions](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/upstream/csapi-architecture-analysis.md) - Architectural choices for implementing 9 resource types
- [OGC API - Common](https://docs.ogc.org/is/19-072/19-072.html) - Foundation specification for all OGC API standards

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

**Implementation Type:** EXTENDING EXISTING CODE (~7 lines in `info.ts`)

**References:**

- [OGC API - Connected Systems Part 1](https://docs.ogc.org/is/23-001/23-001.html) - Conformance classes for Part 1 resources
- [OGC API - Connected Systems Part 1: OpenAPI Specification](../research/standards/ogcapi-connectedsystems-1.bundled.oas31.yaml) - Machine-readable API definition for Part 1
- [OGC API - Connected Systems Part 2](https://docs.ogc.org/is/23-002/23-002.html) - Conformance classes for Part 2 resources
- [OGC API - Connected Systems Part 2: OpenAPI Specification](../research/standards/ogcapi-connectedsystems-2.bundled.oas31.yaml) - Machine-readable API definition for Part 2
- [Conformance and Capability Requirements](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/requirements/csapi-conformance-capabilities.md) - All conformance classes and detection mechanisms
- [Integration with Existing Code](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/upstream/integration-analysis.md) - Exact code changes to info.ts

---

### Collections Reader: Extending Metadata Parsing

The collections reader is existing code that fetches and parses the `/collections` endpoint to discover what data is available on a server. For CSAPI, we will extend this parser to recognize and extract CSAPI-specific metadata that indicates whether a collection contains Systems, DataStreams, Observations, or other CSAPI resources. This is primarily an extension of existing parsing logic rather than building something entirely new - we're adding new properties to the collection info objects and new filter methods like `csapiSystemCollections`, `csapiDataStreamCollections`, and `csapiObservationCollections` alongside the existing `featureCollections` and `edrCollections` getters. The extension reuses the upstream repository's established patterns for handling different resource types within the unified collections framework. This approach supports the project goal of providing developers a consistent experience across all OGC API standards through one endpoint class.

**CSAPI Collection Properties to Parse:**

- `featureType` property indicating resource type (e.g., `sosa:System`, `sosa:Deployment`, `sosa:ObservationCollection`)
- Links to CSAPI-specific operations (create, update, delete, schema endpoints for Part 2 resources)
- Temporal extent for observation collections
- Spatial extent for systems and deployment collections
- Supported formats (GeoJSON, SensorML 3.0, SWE Common 3.0 JSON/Text/Binary)
- Pagination modes (offset-based and cursor-based for high-volume observations and commands)
- Schema information (DataStream/ControlStream schema availability)

**Implementation Type:** EXTENDING EXISTING CODE (~6 lines in `endpoint.ts`)

**References:**

- [SOSA/SSN Ontology](https://www.w3.org/TR/vocab-ssn/) - Semantic foundation for featureType values (sosa:System, sosa:Deployment, etc.)
- [OGC API - Features](https://docs.ogc.org/is/17-069r4/17-069r4.html) - Collections endpoint patterns CSAPI extends
- [Architecture Patterns Analysis](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/upstream/architecture-patterns-analysis.md) - Collection capability determination patterns

---

### OgcApiEndpoint Integration: Extending Main Endpoint Class

The OgcApiEndpoint integration adds the CSAPI factory method to the main `OgcApiEndpoint` class following the exact pattern established by EDR support (PR #114). This integration adds approximately 48 lines total across 2-3 files to expose CSAPI functionality through a single developer-facing method. Developers access all CSAPI capabilities through `endpoint.csapi(collectionId)` which returns a `CSAPIQueryBuilder` instance containing all URL-building methods for the 9 CSAPI resource types. The factory method includes conformance checking (`hasConnectedSystems`), collection metadata fetching, QueryBuilder instantiation, and caching for performance. This minimal integration approach maintains the library's architecture principle of composition over inheritance - no subclassing, just a factory method that returns a specialized query builder. The integration also includes adding the `csapiCollections` getter for filtering collections that support CSAPI resources, and a private cache field for QueryBuilder instances.

**Integration Points in OgcApiEndpoint:**

**1. Import Statement (1 line in `endpoint.ts`):**

```typescript
import CSAPIQueryBuilder from './csapi/url_builder.js';
```

**2. Cache Field (2 lines in `endpoint.ts`):**

```typescript
private collection_id_to_csapi_builder_: Map<string, CSAPIQueryBuilder> = new Map();
```

**3. Collections Getter (~6 lines in `endpoint.ts`):**

```typescript
get csapiCollections(): Promise<string[]> {
  return Promise.all([this.data, this.hasConnectedSystems])
    .then(([data, hasCSAPI]) => (hasCSAPI ? data : { collections: [] }))
    .then(parseCollections)
    .then((collections) => collections.map((collection) => collection.name));
}
```

**4. Conformance Getter (~7 lines in `info.ts`):**

```typescript
get hasConnectedSystems(): Promise<boolean> {
  return Promise.all([this.conformanceClasses]).then(checkHasConnectedSystems);
}
```

**5. Factory Method (~17 lines in `endpoint.ts`):**

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

**6. Export Additions (~6 lines in `index.ts`):**

```typescript
export { CSAPIQueryBuilder } from './ogc-api/csapi/url_builder.js';
export type {} from /* CSAPI types */ './ogc-api/csapi/types.js';
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

**Implementation Type:** EXTENDING EXISTING CODE (~48 lines total across 2-3 files)

**References:**

- [PR #114 (EDR Implementation) Analysis](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/upstream/pr114-analysis.md) - **PRIMARY REFERENCE** - Direct blueprint for factory method pattern
- [Integration with Existing Code](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/upstream/integration-analysis.md) - Line-by-line integration requirements for endpoint.ts, info.ts, index.ts
- [QueryBuilder Pattern Analysis](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/upstream/querybuilder-pattern-analysis.md) - Factory method lifecycle, caching strategy, state management
- [File Organization Strategy](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/upstream/file-organization-analysis.md) - Where to place integration code
- [camptocamp/ogc-client Repository](https://github.com/camptocamp/ogc-client) - Upstream repository to integrate with

---

## Query Builder Component

### CSAPIQueryBuilder: Building New Query Construction Class

> **📋 STRUCTURE NOTE**
>
> The following sections (Systems, Deployments, Procedures, Sampling Features, Properties, DataStreams, Observations, Control Streams, Commands) are **methods within this single CSAPIQueryBuilder class**, not separate components.
>
> This follows the upstream EDR pattern where `EDRQueryBuilder` contains methods like `getCubeUrl()`, `getCorridorUrl()`, etc. Similarly, `CSAPIQueryBuilder` contains methods like `getSystems()`, `getObservations()`, `getCommands()`, etc.
>
> Each subsection below describes a **method group** within the QueryBuilder class.

The CSAPIQueryBuilder is new code we need to build as a single comprehensive class containing URL-building methods for all 9 CSAPI resource types, following the pattern established by the existing `EDRQueryBuilder` class. This QueryBuilder class is instantiated by the `OgcApiEndpoint.csapi()` factory method and provides developers with all the methods needed to construct URLs for CSAPI operations: querying Systems with spatial/temporal filters, creating Observations in DataStreams, retrieving historical observations with temporal ranges, sending Commands to Control Streams, and accessing all other CSAPI resources. The class consolidates URL construction for approximately 60-70 unique URL patterns across Part 1 resources (Systems, Deployments, Procedures, Sampling Features, Properties) and Part 2 resources (DataStreams, Observations, Control Streams, Commands), including canonical endpoints, nested resource endpoints, schema endpoints, and special-purpose endpoints like command status/result tracking. This single-class design follows the upstream repository's architecture pattern where one QueryBuilder per API family handles all URL construction for that API, keeping the implementation focused and maintainable rather than splitting across multiple handler classes. The following sections detail the URL construction requirements for each of the 9 resource types as methods within this one CSAPIQueryBuilder class.

**URL Construction Requirements:**

- Canonical resource endpoints: `/systems`, `/deployments`, `/procedures`, `/samplingFeatures`, `/properties`, `/datastreams`, `/observations`, `/controlstreams`, `/commands`
- Nested resource endpoints: `/systems/{id}/subsystems`, `/systems/{id}/datastreams`, `/datastreams/{id}/observations`, `/controlstreams/{id}/commands`
- Schema endpoints: `/datastreams/{id}/schema`, `/controlstreams/{id}/schema`
- Bulk operations: POST with arrays of observations or commands
- Command status/result endpoints: `/commands/{id}/status`, `/commands/{id}/result`

**Implementation Type:** BUILDING NEW CODE (following EDRQueryBuilder pattern, ~10k-14k lines)

**References:**

- [OGC API - Connected Systems Part 1: OpenAPI Specification](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/standards/ogcapi-connectedsystems-1.bundled.oas31.yaml) - Machine-readable API definition for Part 1 endpoints
- [OGC API - Connected Systems Part 2: OpenAPI Specification](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/standards/ogcapi-connectedsystems-2.bundled.oas31.yaml) - Machine-readable API definition for Part 2 endpoints
- [QueryBuilder Pattern Analysis](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/upstream/querybuilder-pattern-analysis.md) - Core pattern for implementation
- [URL Building Architecture](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/upstream/url-building-analysis.md) - URL construction patterns and query parameter assembly
- [TypeScript Type System Design](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/upstream/typescript-types-analysis.md) - Type definitions for query parameters and interfaces
- [CSAPI Architecture Decisions](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/upstream/csapi-architecture-analysis.md) - Single-class design for 9 resource types

---

### Complete Query Parameter Support

> **📋 CENTRALIZED REFERENCE**
>
> This section documents ALL query parameters used across CSAPI resources. Individual resource method sections below reference this section rather than repeating parameter documentation.

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

**References:**

- [Query Parameter Requirements](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/requirements/csapi-query-parameters.md) - Complete catalog of all CSAPI query parameters
- [OGC API - Common](https://docs.ogc.org/is/19-072/19-072.html) - Standard OGC API parameters (bbox, datetime, limit, offset, f)
- [ISO 8601](https://www.iso.org/iso-8601-date-and-time-format.html) - Temporal parameter format specification
- [Sub-Resource Navigation Requirements](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/requirements/csapi-subresource-navigation.md) - Query parameters on nested endpoints
- [URL Building Architecture](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/upstream/url-building-analysis.md) - Parameter encoding and array handling

---

#### Systems Resource Methods

The CSAPIQueryBuilder includes Systems resource methods to manage CSAPI System resources, representing sensors, actuators, platforms, samplers, and other observing systems. These methods implement all CRUD operations (Create, Read, Update, Delete) for Systems at both canonical endpoints (`/systems`, `/systems/{id}`) and nested endpoints (`/systems/{parentId}/subsystems`). Systems are the core resource in CSAPI Part 1, serving as the entry point for discovering available sensors and their relationships to deployments, procedures, sampling features, and observation streams. The methods support hierarchical queries (recursive subsystem traversal), relationship filtering (query by deployment, procedure, or sampling feature), and both GeoJSON and SensorML format parsing. This functionality connects to the URL builder for query construction, the format handlers for parsing responses, and the validator for checking system constraints.

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

**Query Parameters:** See [Complete Query Parameter Support](#complete-query-parameter-support). Systems support: `bbox`, `datetime`, `recursive`, `parent`, `deployment`, `procedure`, `foi`, `id`, `uid`, `q`, property filters, `limit`, `offset`, `f`.

**References:**

- [OGC API - Connected Systems Part 1](https://docs.ogc.org/is/23-001/23-001.html): Normative specification for Systems resources and CRUD operations
- [OGC API - Connected Systems Part 1: OpenAPI Specification](../research/standards/ogcapi-connectedsystems-1.bundled.oas31.yaml): Systems endpoint definitions
- [csapi-part1-requirements.md](../research/requirements/csapi-part1-requirements.md): Detailed client implementation requirements for Systems resource methods
- [SOSA/SSN Ontology](https://www.w3.org/TR/vocab-ssn/): Semantic definitions for system types and relationships
- [RFC 7946 (GeoJSON)](https://tools.ietf.org/html/rfc7946): Format specification for encoding Systems as GeoJSON Features

---

#### Deployments Resource Methods

The CSAPIQueryBuilder includes Deployments resource methods to manage CSAPI Deployment resources, describing where and when systems are deployed in the field. These methods implement all CRUD operations for Deployments at canonical endpoints (`/deployments`, `/deployments/{id}`) and nested endpoints (`/deployments/{parentId}/subdeployments`). Deployments connect systems to geographic locations and temporal periods, enabling queries like "what sensors were active in this region during this time period." The methods support hierarchical subdeployment queries (recursive parameter), relationship filtering (query by system), and GeoJSON format parsing with deployment-specific metadata. Deployments have bidirectional associations with systems - a system can have multiple deployments over time, and a deployment can involve multiple systems.

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

**Query Parameters:** See [Complete Query Parameter Support](#complete-query-parameter-support). Deployments support: `bbox`, `datetime`, `recursive`, `system`, `parent`, `id`, `uid`, `q`, property filters, `limit`, `offset`, `f`.

**References:**

- [OGC API - Connected Systems Part 1](https://docs.ogc.org/is/23-001/23-001.html): Normative specification for Deployments resources
- [OGC API - Connected Systems Part 1: OpenAPI Specification](../research/standards/ogcapi-connectedsystems-1.bundled.oas31.yaml): Deployments endpoint definitions
- [csapi-part1-requirements.md](../research/requirements/csapi-part1-requirements.md): Client implementation requirements for Deployments including spatial/temporal queries
- [RFC 7946 (GeoJSON)](https://tools.ietf.org/html/rfc7946): Format for encoding Deployments with spatial extents

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

**Query Parameters:** See [Complete Query Parameter Support](#complete-query-parameter-support). Procedures support: `system`, `id`, `uid`, `q`, property filters, `limit`, `offset`, `f`.

**References:**

- [OGC API - Connected Systems Part 1](https://docs.ogc.org/is/23-001/23-001.html): Normative specification for Procedures resources and methodologies
- [OGC API - Connected Systems Part 1: OpenAPI Specification](../research/standards/ogcapi-connectedsystems-1.bundled.oas31.yaml): Procedures endpoint definitions
- [csapi-part1-requirements.md](../research/requirements/csapi-part1-requirements.md): Client requirements for Procedures including SensorML format support
- [OGC SensorML 3.0](https://docs.ogc.org/is/23-000/23-000.html): Format for detailed procedure descriptions

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

**Query Parameters:** See [Complete Query Parameter Support](#complete-query-parameter-support). Sampling Features support: `bbox`, `system`, `foi`, `relatedSamplingFeature`, `id`, `uid`, `q`, property filters, `limit`, `offset`, `f`.

**References:**

- [OGC API - Connected Systems Part 1](https://docs.ogc.org/is/23-001/23-001.html): Normative specification for Sampling Features resources
- [OGC API - Connected Systems Part 1: OpenAPI Specification](../research/standards/ogcapi-connectedsystems-1.bundled.oas31.yaml): Sampling Features endpoint definitions
- [csapi-part1-requirements.md](../research/requirements/csapi-part1-requirements.md): Client requirements for Sampling Features navigation
- [SOSA/SSN Ontology](https://www.w3.org/TR/vocab-ssn/): Semantic definitions for sampling feature types and relationships
- [RFC 7946 (GeoJSON)](https://tools.ietf.org/html/rfc7946): Format for encoding Sampling Features with geometries

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

**Query Parameters:** See [Complete Query Parameter Support](#complete-query-parameter-support). Properties support: `system`, `baseProperty`, `id`, `uid`, `q`, property filters, `limit`, `offset`, `f`.

**References:**

- [OGC API - Connected Systems Part 1](https://docs.ogc.org/is/23-001/23-001.html): Normative specification for Properties resources
- [OGC API - Connected Systems Part 1: OpenAPI Specification](../research/standards/ogcapi-connectedsystems-1.bundled.oas31.yaml): Properties endpoint definitions
- [csapi-part1-requirements.md](../research/requirements/csapi-part1-requirements.md): Client requirements for Properties navigation
- [SOSA/SSN Ontology](https://www.w3.org/TR/vocab-ssn/): Semantic definitions for observable and actuatable properties

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

**Query Parameters:** See [Complete Query Parameter Support](#complete-query-parameter-support). DataStreams support: `system`, `observedProperty`, `foi`, `samplingFeature`, `procedure`, `datetime`, `id`, `uid`, `q`, property filters, `limit`, `offset`, `f`.

**References:**

- [OGC API - Connected Systems Part 2](https://docs.ogc.org/is/23-002/23-002.html): Normative specification for DataStreams resources and schema operations
- [OGC API - Connected Systems Part 2: OpenAPI Specification](../research/standards/ogcapi-connectedsystems-2.bundled.oas31.yaml): DataStreams endpoint definitions
- [csapi-part2-requirements.md](../research/requirements/csapi-part2-requirements.md): Client implementation requirements for DataStreams including schema handling
- [OGC SWE Common 3.0](https://docs.ogc.org/is/24-014/24-014.html): Format for result schemas and data encoding
- [pr114-analysis.md](../research/upstream/pr114-analysis.md): Architectural patterns for DataStreams implementation

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

**Temporal Query Features:**

- **phenomenonTime filtering** (when observation was made - PRIMARY temporal filter):
  - Single instant: `phenomenonTime=2024-01-15T12:00:00Z`
  - Closed interval: `phenomenonTime=2024-01-01/2024-01-31`
  - Open start (before end): `phenomenonTime=../2024-01-31`
  - Open end (after start): `phenomenonTime=2024-01-01/..`
  - Multiple disjoint intervals: `phenomenonTime=2024-01-01/2024-01-15,2024-02-01/2024-02-15`
- **resultTime filtering**: When observation result became available (ISO 8601 intervals)
- **Temporal binning/aggregation**: Group observations by time period (hour, day, month)
- **Temporal resolution**: Filter by minimum time spacing between observations

**Pagination Support:**

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

**Query Parameters:** See [Complete Query Parameter Support](#complete-query-parameter-support). Observations support: `phenomenonTime`, `resultTime`, `foi`, `id`, `limit`, `offset`, `cursor`, `f`, `obsFormat`.

**References:**

- [OGC API - Connected Systems Part 2](https://docs.ogc.org/is/23-002/23-002.html): Normative specification for Observations resources and temporal queries
- [OGC API - Connected Systems Part 2: OpenAPI Specification](../research/standards/ogcapi-connectedsystems-2.bundled.oas31.yaml): Observations endpoint definitions
- [csapi-part2-requirements.md](../research/requirements/csapi-part2-requirements.md): Client requirements for Observations including pagination and bulk operations
- [OGC SWE Common 3.0](https://docs.ogc.org/is/24-014/24-014.html): Format for observation result encodings (JSON, Text, Binary)
- [pr114-analysis.md](../research/upstream/pr114-analysis.md): Performance patterns for high-volume observation handling

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

**Query Parameters:** See [Complete Query Parameter Support](#complete-query-parameter-support). Control Streams support: `system`, `controlledProperty`, `id`, `uid`, `q`, property filters, `limit`, `offset`, `f`.

**References:**

- [OGC API - Connected Systems Part 2](https://docs.ogc.org/is/23-002/23-002.html): Normative specification for ControlStreams resources
- [OGC API - Connected Systems Part 2: OpenAPI Specification](../research/standards/ogcapi-connectedsystems-2.bundled.oas31.yaml): ControlStreams endpoint definitions
- [csapi-part2-requirements.md](../research/requirements/csapi-part2-requirements.md): Client requirements for ControlStreams and actuation capabilities
- [OGC SWE Common 3.0](https://docs.ogc.org/is/24-014/24-014.html): Format for control parameter schemas
- [pr114-analysis.md](../research/upstream/pr114-analysis.md): Architectural patterns mirroring DataStreams for control

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

**Temporal Query Features:**

- **issueTime filtering** (when command was issued - PRIMARY temporal filter):
  - Single instant: `issueTime=2024-01-15T12:00:00Z`
  - Closed interval: `issueTime=2024-01-01/2024-01-31`
  - Open start: `issueTime=../2024-01-31`
  - Open end: `issueTime=2024-01-01/..`
- **executionTime filtering**: When command should be/was executed (ISO 8601 intervals)
- **Status filtering**: `status` parameter with multiple values (pending, accepted, executing, completed, failed, cancelled)
- **Relationship filtering**: `controlstream` parameter (commands for specific control stream)

**Pagination Support:**

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

**Query Parameters:** See [Complete Query Parameter Support](#complete-query-parameter-support). Commands support: `issueTime`, `executionTime`, `status`, `controlstream`, `id`, `limit`, `offset`, `cursor`, `f`, `cmdFormat`.

**References:**

- [OGC API - Connected Systems Part 2](https://docs.ogc.org/is/23-002/23-002.html): Normative specification for Commands resources and lifecycle management
- [OGC API - Connected Systems Part 2: OpenAPI Specification](../research/standards/ogcapi-connectedsystems-2.bundled.oas31.yaml): Commands endpoint definitions
- [csapi-part2-requirements.md](../research/requirements/csapi-part2-requirements.md): Client requirements for Commands including status tracking and feasibility
- [OGC SWE Common 3.0](https://docs.ogc.org/is/24-014/24-014.html): Format for command parameter encodings
- [pr114-analysis.md](../research/upstream/pr114-analysis.md): Patterns for command submission and status polling

---

## Format Handler Components

### GeoJSON Handler: Extending Existing Parser

The GeoJSON handler is existing code in the library that parses GeoJSON Feature and FeatureCollection documents, supporting all seven geometry types (Point, LineString, Polygon, MultiPoint, MultiLineString, MultiPolygon, GeometryCollection). For CSAPI, we will extend this handler with recognition and extraction of CSAPI-specific properties. The extension will recognize CSAPI-specific feature types through the `featureType` property and extract CSAPI resource properties from the feature `properties` object. CSAPI Part 1 resources (Systems, Deployments, Procedures, Sampling Features) are encoded as GeoJSON features with additional semantic properties like `systemType`, `assetType`, `uniqueIdentifier`, `validTime`, and association links to related resources. The extension will add type checking for these CSAPI properties and validation rules specific to each CSAPI feature type, while maintaining compatibility with generic GeoJSON handling for other OGC API standards.

**CSAPI-Specific GeoJSON Properties:**

- Systems: `systemType` (URI), `assetType` (enum), `uniqueIdentifier` (URI), `validTime` (period), association arrays (`subsystems`, `deployments`, `procedures`, `samplingFeatures`, `datastreams`, `controlstreams`)
- Deployments: `deployedSystems` (array), `validTime` (period), spatial/temporal extent
- Procedures: `procedureType` (URI), `methodKind` (URI), `attachedTo` (link to system)
- Sampling Features: `samplingFeatureType` (URI), `sampledFeature` (link), `relatedSamplingFeature` (links)
- All resources: `id`, `name`, `description`, `links` (HATEOAS navigation)

**Validation Requirements:**

- `uniqueIdentifier` must be valid URI (preferably URN format following RFC 8141)
- `systemType` must be from SOSA/SSN vocabulary (`sosa:Sensor`, `sosa:Platform`, `sosa:Actuator`, `sosa:Sampler`, etc.)
- `validTime` must be ISO 8601 temporal period or instant
- Association arrays must contain valid resource links (href + rel) or inline features
- Geometry must be valid per RFC 7946 (WGS84 coordinates, right-hand rule for polygons)

**Implementation Type:** EXTENDING EXISTING CODE

**References:**

- [RFC 7946 (GeoJSON)](https://tools.ietf.org/html/rfc7946): Normative specification for GeoJSON format
- [OGC API - Connected Systems Part 1](https://docs.ogc.org/is/23-001/23-001.html): CSAPI-specific GeoJSON property requirements
- [OGC API - Connected Systems Part 1: OpenAPI Specification](../research/standards/ogcapi-connectedsystems-1.bundled.oas31.yaml): GeoJSON schema definitions for Part 1 resources
- [SOSA/SSN Ontology](https://www.w3.org/TR/vocab-ssn/): Vocabulary for systemType and property URIs
- [RFC 8141 (URN Syntax)](https://tools.ietf.org/html/rfc8141): uniqueIdentifier format requirements

---

### SensorML Handler: Building New Format Parser

The SensorML handler is new code we need to build to parse [OGC SensorML 3.0](https://docs.ogc.org/is/23-000/23-000.html) format documents that describe sensor systems, components, and processes in detail. SensorML 3.0 is the latest version of the JSON-native format from the Sensor Web Enablement (SWE) standards family, published in 2024, that provides rich metadata about sensors, actuators, and processing chains. CSAPI servers return SensorML 3.0 documents when describing Systems or Procedures, providing detailed technical specifications beyond what GeoJSON can express. We will build a parser that handles SensorML 3.0 system models (System, PhysicalComponent, PhysicalSystem, SystemConfiguration), component descriptions, capability specifications, input/output specifications, configuration parameters, operational modes, component connections, and temporal validity periods. The parser must convert SensorML 3.0 JSON documents into TypeScript objects that the library can work with.

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

**Parsing Capabilities:**

- **Recursive component parsing**: Nested PhysicalSystems with full component hierarchy
- **SWE Common 3.0 DataComponent integration**: Complete parsing of all DataComponent types
- **Unit of measure parsing**: UCUM code support ([UCUM codes](http://unitsofmeasure.org/))
- **Reference resolution**: External link dereferencing for procedures, datasheets, feature definitions
- **Position/location parsing**: GeoJSON geometry plus orientation (quaternions, euler angles)
- **Mode and configuration state management**: Operational modes with state definitions and transitions
- **Connection graph traversal**: Component connection mapping (data flow, physical connections)
- **Vocabulary resolution**: Automatic fetching of vocabulary terms from code spaces (SOSA, SSN, CF, QUDT)

**References:**

- [OGC SensorML 3.0](https://docs.ogc.org/is/23-000/23-000.html): Normative specification for SensorML 3.0 format
- [OGC API - Connected Systems Part 1](https://docs.ogc.org/is/23-001/23-001.html): Requirements for SensorML encoding in CSAPI
- [OGC API - Connected Systems Part 1: OpenAPI Specification](../research/standards/ogcapi-connectedsystems-1.bundled.oas31.yaml): SensorML media type definitions
- [SensorML 3.0 JSON Schema](https://schemas.opengis.net/sensorML/3.0/): Official JSON schemas for validation
- [csapi-part1-requirements.md](../research/requirements/csapi-part1-requirements.md): Client requirements for SensorML parsing
- [UCUM Codes](http://unitsofmeasure.org/): Unit of measure code system

**Implementation Type:** BUILDING NEW CODE

---

### SWE Common Handler: Building New Format Parser

The SWE Common handler is new code we need to build to parse [OGC SWE Common 3.0](https://docs.ogc.org/is/24-014/24-014.html) format documents that define observation data schemas and encode actual observation results. SWE Common 3.0 is the latest version of the data encoding standard from the Sensor Web Enablement family, published in 2024, that describes structured measurement data with units, quality information, and constraints using a modernized JSON-native approach. CSAPI Part 2 uses SWE Common 3.0 extensively for DataStream schemas (defining what properties are observed and result structure) and Observation results (actual measurement values). We will build parsers for all three SWE Common 3.0 encodings: JSON (human-readable structured data), Text (CSV-style compact encoding), and Binary (efficient encoding for high-volume streaming). The handler must parse DataComponent schemas, extract values from encoded result formats, validate measurements against schemas, and convert between different encodings.

**SWE Common 3.0 Data Components to Parse:**

**Simple Components:**

- **Quantity**: Numeric measurement with unit of measure (temperature, pressure, voltage)
- **Count**: Integer count value (particle count, event count)
- **Boolean**: True/false indicator (on/off status, alarm state)
- **Text**: String value (station ID, observation notes)
- **Time**: ISO 8601 timestamp (observation time, event time)
- **Category**: Categorical value from controlled vocabulary (weather condition, quality flag)

**Range Components (new in 3.0):**

- **QuantityRange**: Range of numeric values with units (temperature range)
- **CategoryRange**: Range of categorical values (quality range indicators)
- **TimeRange**: Temporal interval (observation period, validity period)

**Complex Components:**

- **DataRecord**: Structured record containing multiple named fields (multi-property observation)
- **DataArray**: Array of measurements with variable or fixed element count (time series, profile, trajectory)
- **Vector**: Positional vector with coordinate reference system (3D location, velocity)
- **Matrix**: Matrix of values with specified dimensions (covariance matrix, transformation matrix)
- **DataChoice**: Choice between alternative structures (different measurement modes, conditional observations)
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

**Schema Validation Requirements:**

- **Result structure validation**: Matching result structure against DataStream schema
- **Range validation**: Values within allowed ranges
- **Unit validation**: UCUM code validation
- **Array validation**: Array dimensions match schema element count specifications
- **Quality validation**: Quality indicators follow schema
- **Temporal validation**: Timestamps follow ISO 8601 format
- **Categorical validation**: Categorical values from defined code space
- **Text validation**: Text patterns match defined constraints
- **Geometry validation**: GeometryData follows GeoJSON spec

**Advanced 3.0 Features Support:**

- **NilValues**: Representation of missing/invalid data with reason codes
- **Quality**: Associated quality indicators (accuracy, precision, confidence, flags)
- **Constraints**: AllowedValues (enumeration lists), AllowedIntervals (numeric ranges), AllowedTimes (temporal constraints), AllowedTokens (text patterns)
- **ReferenceFrames**: Temporal reference frame definitions (UTC, TAI, GPS time) and spatial reference frame definitions (EPSG codes)
- **CodeSpaces**: Controlled vocabulary support with vocabulary dereferencing
- **Encoding conversion**: Bidirectional conversion between JSON ↔ Text ↔ Binary
- **Streaming support**: Incremental parsing for large datasets
- **Performance optimization**: Binary encoding for high-volume data

**References:**

- [OGC SWE Common 3.0](https://docs.ogc.org/is/24-014/24-014.html): Normative specification for SWE Common data encodings
- [OGC API - Connected Systems Part 2](https://docs.ogc.org/is/23-002/23-002.html): Requirements for SWE Common in DataStreams/Observations
- [OGC API - Connected Systems Part 2: OpenAPI Specification](../research/standards/ogcapi-connectedsystems-2.bundled.oas31.yaml): SWE Common media type definitions
- [SWE Common 3.0 JSON Schema](https://schemas.opengis.net/sweCommon/3.0/): Official JSON schemas
- [csapi-part2-requirements.md](../research/requirements/csapi-part2-requirements.md): Client requirements for SWE Common parsing
- [pr114-analysis.md](../research/upstream/pr114-analysis.md): Implementation patterns for result parsing

**Implementation Type:** BUILDING NEW CODE

---

### Format Detector: Extending Existing Content Negotiation

The format detector is existing code that examines HTTP response headers (Content-Type) and document structure to determine what format a server returned. For CSAPI, we will extend this detector to recognize CSAPI media types. The extension will recognize new media types used by CSAPI servers: `application/sml+json` (SensorML-JSON encoding), `application/swe+json` (SWE Common JSON encoding), `application/swe+text` (SWE Common Text/CSV encoding), and `application/swe+binary` (SWE Common Binary encoding). The extension will add these media types to the library's format registry and route them to the appropriate new format handlers (SensorML handler, SWE Common handler). This follows the existing pattern where the detector checks Content-Type headers first, then falls back to document structure analysis if headers are missing or ambiguous.

**Media Type Recognition:**

- `application/sml+json` → Route to SensorML Handler
- `application/swe+json` → Route to SWE Common Handler (JSON encoding)
- `application/swe+text` → Route to SWE Common Handler (Text encoding)
- `application/swe+binary` → Route to SWE Common Handler (Binary encoding)
- `application/geo+json` with CSAPI `featureType` → Route to GeoJSON Handler with CSAPI extensions

**Detection Strategy:**

1. **Content-Type header parsing** (primary method): Full media type parsing with parameter extraction
2. **Accept header negotiation**: Server-driven content negotiation with quality factors
3. **Document structure analysis** (fallback): Root JSON property examination (SensorML: `type: PhysicalSystem`, SWE Common: `type: DataRecord`, CSAPI GeoJSON: `featureType` property)
4. **Format-specific identifiers**: SensorML process types, SWE Common component types, CSAPI resource types
5. **Binary format detection**: Magic numbers, byte order marks, structure signatures
6. **Charset detection**: BOM detection, heuristic analysis

**Implementation Type:** EXTENDING EXISTING CODE

**References:**

- [RFC 6838 (Media Type Specifications)](https://tools.ietf.org/html/rfc6838): Media type format and registration
- [OGC API - Connected Systems Part 1](https://docs.ogc.org/is/23-001/23-001.html): CSAPI media types for Part 1
- [OGC API - Connected Systems Part 1: OpenAPI Specification](../research/standards/ogcapi-connectedsystems-1.bundled.oas31.yaml): Part 1 media type definitions
- [OGC API - Connected Systems Part 2](https://docs.ogc.org/is/23-002/23-002.html): CSAPI media types for Part 2 (SWE formats)
- [OGC API - Connected Systems Part 2: OpenAPI Specification](../research/standards/ogcapi-connectedsystems-2.bundled.oas31.yaml): Part 2 media type definitions

---

### Validator: Extending Existing Validation Framework

The validator is existing code that checks whether parsed documents conform to format specifications and semantic constraints. For CSAPI, we will extend this validator with validation of CSAPI requirements. The extension will check CSAPI-specific requirements: required properties for each resource type, valid enumeration values, URI format validation, temporal validity constraints, spatial constraint validation, association integrity, and schema conformance for Part 2 resources (Observation results must match DataStream schema, Command parameters must match ControlStream schema). The extension will add CSAPI validation rules to the existing validation pipeline, reporting errors and warnings through the same error handling mechanism used for other formats.

**CSAPI Validation Rules:**

**Part 1 Resource Validation:**

- Systems: `uniqueIdentifier` (required URI), `systemType` (required, from SOSA vocabulary), `name` (required string)
- Deployments: `validTime` (required temporal period), spatial extent (required)
- Procedures: `procedureType` (required URI), attached system reference validation
- Sampling Features: `sampledFeature` (required reference), geometry (required)
- Properties: `definition` (required URI from vocabulary), `label` (required string)

**Part 2 Resource Validation:**

- DataStreams: schema validation (result schema must be valid SWE Common DataComponent), observed properties must reference existing Property resources
- Observations: result validation (must conform to DataStream schema), temporal validation (phenomenonTime required)
- Control Streams: schema validation (parameter schema must be valid SWE Common), system association (required)
- Commands: parameter validation (must conform to ControlStream schema), execution time validation

**Cross-Reference Validation:**

- **Association links**: All links must have valid href, valid rel, optional type
- **Resource references**: Referenced resources must exist or be valid external URIs
- **Hierarchical integrity**: Parent-child relationships are consistent, no circular references
- **Relationship consistency**: Bidirectional relationships are consistent
- **Vocabulary references**: All vocabulary URIs dereferenceable
- **Schema references**: DataStream/ControlStream schemas valid SWE Common
- **Spatial references**: CRS codes valid (EPSG codes or URIs), coordinates within valid ranges
- **Temporal references**: Reference frames valid, timezones valid, ISO 8601 compliance
- **Unit references**: UCUM codes valid
- **External references**: HTTP/HTTPS links reachable (optional validation)

**Validation Error Reporting:**

- **Error severity**: Error (invalid/unusable), Warning (questionable/suboptimal), Info (recommendations)
- **Error context**: JSON path to error location, line/column numbers, surrounding context
- **Error messages**: Clear description of problem, expected vs actual values, suggested fixes
- **Error codes**: Machine-readable error codes for programmatic handling
- **Batch validation**: All errors collected and reported together
- **Validation summaries**: Count of errors/warnings/info messages, validation pass/fail status

**Implementation Type:** EXTENDING EXISTING CODE

**References:**

- [OGC API - Connected Systems Part 1](https://docs.ogc.org/is/23-001/23-001.html): Validation requirements for Part 1 resources
- [OGC API - Connected Systems Part 1: OpenAPI Specification](../research/standards/ogcapi-connectedsystems-1.bundled.oas31.yaml): Part 1 schema definitions for validation
- [OGC API - Connected Systems Part 2](https://docs.ogc.org/is/23-002/23-002.html): Validation requirements for Part 2 resources
- [OGC API - Connected Systems Part 2: OpenAPI Specification](../research/standards/ogcapi-connectedsystems-2.bundled.oas31.yaml): Part 2 schema definitions for validation
- [csapi-part1-requirements.md](../research/requirements/csapi-part1-requirements.md): Required properties and constraints
- [csapi-part2-requirements.md](../research/requirements/csapi-part2-requirements.md): Schema conformance requirements
- [RFC 8141 (URN Syntax)](https://tools.ietf.org/html/rfc8141): URI validation rules

---

## Worker Components

### Background Processing: Extending Existing Web Worker Pattern

The background processing component extends the existing Web Worker infrastructure in the Camptocamp OGC Client Library (`src/worker/worker.ts`, `src/worker/utils.ts`, `src/worker/index.ts`) to move heavy parsing and validation work off the main thread, keeping browser UIs responsive. The upstream library currently uses this worker pattern to parse XML capabilities documents for WMS, WFS, and WMTS services, offloading computationally expensive XML parsing and processing to a Web Worker that runs in parallel and returns results asynchronously via message passing. The library provides a fallback mechanism for non-worker environments like Node.js or older browsers, where the same code runs synchronously on the main thread. For CSAPI, we will extend this proven worker pattern by adding new CSAPI-specific message types to handle: SensorML 3.0 parsing (complex hierarchical JSON document traversal), SWE Common 3.0 parsing (especially binary encoding decoding), large observation result set processing (thousands of observations with schema validation), bulk command validation, and schema validation operations.

**CSAPI Operations to Move to Worker:**

**Format Parsing (Heavy Operations):**

- **SensorML 3.0 parsing**: Complex hierarchical JSON document parsing with recursive PhysicalSystem component trees
- **SWE Common 3.0 parsing**: Binary encoding decoding (IEEE 754 float, multi-byte integers, byte order handling), Text/CSV parsing, JSON encoding with schema-driven validation
- **Large observation arrays**: Parsing thousands of observations with result validation against DataStream schemas
- **Large command arrays**: Bulk command parameter validation against ControlStream schemas
- **GeoJSON feature collections**: Large spatial datasets with CSAPI-specific property extraction

**Validation Operations (CPU-Intensive):**

- **Schema validation**: Complex SWE Common DataComponent schema validation with constraint checking
- **Observation result validation**: Validate observation results against DataStream result schemas
- **Command parameter validation**: Validate command parameters against ControlStream parameter schemas
- **Cross-reference validation**: Check resource association integrity across hierarchies

**Query Operations (Memory/CPU Intensive):**

- **Recursive hierarchy traversal**: Deep system/deployment trees with all descendants
- **Spatial filtering**: bbox intersection calculations across large feature collections
- **Temporal filtering**: phenomenonTime/resultTime interval matching across large observation sets

**Worker Message Types to Add:**

- `PARSE_SENSORML_3`: Input SensorML 3.0 JSON, output parsed System/PhysicalComponent/PhysicalSystem object
- `PARSE_SWE_RESULT`: Input SWE Common encoded result (JSON/Text/Binary) + schema, output validated parsed values
- `PARSE_SWE_BINARY`: Input Base64 binary block + schema, output decoded observation array
- `VALIDATE_OBSERVATIONS`: Input observation array + DataStream schema, output validation results
- `VALIDATE_COMMANDS`: Input command array + ControlStream schema, output validation results
- `PARSE_OBSERVATION_ARRAY`: Input large observation array, output parsed and validated observations
- `TRAVERSE_HIERARCHY`: Input system ID + recursive flag, output complete hierarchy tree
- `FILTER_SPATIAL`: Input feature collection + bbox, output filtered features
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

**Implementation Type:** EXTENDING EXISTING CODE (adding CSAPI message handlers to existing worker)

**References:**

- [pr114-analysis.md](../research/upstream/pr114-analysis.md): Worker patterns for EDR implementation
- [csapi-part2-requirements.md](../research/requirements/csapi-part2-requirements.md): Performance requirements for large observation datasets

---

## Testing Components

### Test Coverage: Extending Existing Test Suite

The test coverage component extends the existing Jest test suite to cover all CSAPI functionality. For CSAPI, we will add test suites for every new component: format parsers (SensorML, SWE Common), resource methods (Systems, DataStreams, Observations, Commands, etc.), query builders, validators, and integration tests. The library has established testing patterns including unit tests (isolated component tests), integration tests (multi-component interaction), and fixture-based tests (using example documents from the spec). The extension will add CSAPI test fixtures (GeoJSON features, SensorML documents, SWE Common results), mock CSAPI responses, and test utilities specific to CSAPI validation. Test coverage should match the existing library standard (>80% code coverage).

**CSAPI Test Suites to Create:**

**Format Parser Tests:**

- **GeoJSON CSAPI extensions**: All Part 1 resource types, all CSAPI-specific properties, all geometry types, validation rules
- **SensorML 3.0 parser**: All system models, all elements, recursive component parsing, SWE Common integration
- **SWE Common 3.0 parser**: All data components, all encodings (JSON, Text, Binary), constraint validation, quality indicators
- **Format detector**: All CSAPI media types, fallback detection, error handling
- **Validator**: All Part 1 validation rules, all Part 2 validation rules, cross-reference validation

**Resource Method Tests (All CRUD + All Query Parameters):**

- **Systems**: CRUD, subsystem hierarchy, all query parameters, pagination, format negotiation, error cases
- **Deployments**: CRUD, subdeployment hierarchy, all query parameters, pagination, error cases
- **Procedures**: CRUD, all query parameters, pagination, format negotiation, error cases
- **Sampling Features**: CRUD, all query parameters, pagination, error cases
- **Properties**: Read operations, all query parameters, pagination, error cases
- **DataStreams**: CRUD, schema operations, all query parameters, pagination, error cases
- **Observations**: CRUD, all temporal queries, both pagination modes, large result sets, bulk operations, all encodings, error cases
- **Control Streams**: CRUD, schema operations, all query parameters, pagination, error cases
- **Commands**: CRUD, status tracking, result retrieval, all temporal queries, both pagination modes, bulk operations, sync vs async, error cases

**Query Builder Tests:**

- **Canonical endpoints**: URL construction for all 9 resource types
- **Nested endpoints**: All nesting patterns
- **Query parameter encoding**: All spatial, temporal, relationship, common, hierarchical, pagination, format parameters
- **Combined filtering**: Multiple query parameters together, parameter precedence
- **Schema endpoints**: DataStream/ControlStream schema URLs
- **Status/result endpoints**: Command status/result URLs
- **Error cases**: Invalid parameters, malformed URLs

**Integration Tests (End-to-End Workflows):**

- **Discovery workflows**: Connect → check conformance → list collections → filter by type → retrieve resources
- **Observation workflows**: Discover systems → find datastreams → query observations → paginate → parse results
- **Command workflows**: Discover systems → find control streams → check feasibility → submit → track status → retrieve results
- **Cross-resource navigation**: System → deployments → procedures → sampling features → datastreams → observations
- **Format round-tripping**: Parse → validate → modify → serialize → parse (verify consistency)
- **Hierarchical queries**: Recursive traversal with large hierarchies
- **Error handling**: Server errors, validation errors, network errors, malformed responses

**Test Fixtures:**

- **Specification examples**: All example responses from CSAPI Parts 1 & 2 specifications
- **Edge cases**: Empty collections, minimal resources, malformed data, boundary conditions
- **Large datasets**: Paginated collections, large observation sets, complex hierarchies
- **All format variations**: GeoJSON (all Part 1 types), SensorML 3.0 (all system types), SWE Common 3.0 (all encodings)
- **Error responses**: All HTTP error codes, validation error types, malformed headers
- **Schema fixtures**: DataStream schema examples, ControlStream parameter schemas

**Test Coverage Targets:**

- **Code coverage**: >80% statement coverage, >80% branch coverage, 100% public API coverage
- **Resource coverage**: 100% of all CSAPI resource types, 100% of all query parameters, 100% of all format types
- **Error coverage**: All error conditions documented in CSAPI specification

**Implementation Type:** EXTENDING EXISTING CODE (adding CSAPI test suites to existing Jest framework)

**References:**

- [OGC API - Connected Systems Part 1](https://docs.ogc.org/is/23-001/23-001.html): Specification examples for test fixtures
- [OGC API - Connected Systems Part 1: OpenAPI Specification](../research/standards/ogcapi-connectedsystems-1.bundled.oas31.yaml): Part 1 endpoint testing specifications
- [OGC API - Connected Systems Part 2](https://docs.ogc.org/is/23-002/23-002.html): Part 2 examples for observation/command tests
- [OGC API - Connected Systems Part 2: OpenAPI Specification](../research/standards/ogcapi-connectedsystems-2.bundled.oas31.yaml): Part 2 endpoint testing specifications

---

## Documentation Components

### API Documentation: Extending Existing TypeDoc Documentation

The API documentation component extends the existing TypeDoc documentation to cover all CSAPI additions. For CSAPI, we will add documentation for all new TypeScript interfaces and types, all new methods on OgcApiEndpoint, usage examples for every resource type and query pattern, format handler documentation, and migration guides for users of other CSAPI clients. The library uses TypeDoc to generate API documentation from TypeScript source code comments, providing type-aware documentation with cross-references and examples. The extension will add JSDoc comments to all new code, following the existing documentation standards and style.

**Documentation to Add:**

- **Interface Documentation**: All CSAPI TypeScript interfaces (System, Deployment, DataStream, Observation, etc.)
- **Method Documentation**: All CSAPIQueryBuilder methods with parameter descriptions and examples
- **Usage Examples**: Common workflows (discovery, observation queries, command submission)
- **Format Documentation**: SensorML 3.0 and SWE Common 3.0 parsing examples
- **Migration Guides**: For users of other CSAPI client libraries
- **Query Parameter Reference**: Complete documentation of all query parameters
- **Error Handling**: Common error scenarios and how to handle them

**Implementation Type:** EXTENDING EXISTING CODE (adding CSAPI docs to existing TypeDoc setup)

**References:**

- [OGC API - Connected Systems Part 1](https://docs.ogc.org/is/23-001/23-001.html): Normative references for documentation
- [OGC API - Connected Systems Part 1: OpenAPI Specification](../research/standards/ogcapi-connectedsystems-1.bundled.oas31.yaml): API reference documentation source
- [OGC API - Connected Systems Part 2](https://docs.ogc.org/is/23-002/23-002.html): Part 2 specification references
- [OGC API - Connected Systems Part 2: OpenAPI Specification](../research/standards/ogcapi-connectedsystems-2.bundled.oas31.yaml): Part 2 API reference documentation source

---

## Summary: Build vs Extend Breakdown

### Components Extending Existing Code (9 components):

1. **Conformance Reader** - Add CSAPI conformance class checks (`hasConnectedSystems` getter, ~7 lines in `info.ts`)
2. **Collections Reader** - Parse CSAPI collection metadata (`csapiCollections` getter, ~6 lines in `endpoint.ts`)
3. **OgcApiEndpoint Integration** - Add `csapi(collectionId)` factory method (~48 lines total across 2-3 files)
4. **GeoJSON Handler** - Recognize CSAPI feature types and properties (extend existing GeoJSON parser)
5. **Format Detector** - Add SensorML 3.0 and SWE Common 3.0 media types (extend existing content negotiation)
6. **Validator** - Add CSAPI validation rules (extend existing validation framework)
7. **Background Processing** - Add CSAPI operations to Web Worker (extend existing worker with new message types)
8. **Test Coverage** - Add CSAPI test suites to Jest framework (extend existing test infrastructure)
9. **API Documentation** - Add CSAPI docs to TypeDoc (extend existing documentation)

### Components Building New Code (3 components):

1. **CSAPIQueryBuilder** - New query builder class with URL-building methods for all 9 CSAPI resource types (~10k-14k lines)
   - Systems methods (getSystems, createSystem, updateSystem, deleteSystem, getSubsystems, etc.)
   - Deployments methods (getDeployments, createDeployment, updateDeployment, deleteDeployment, etc.)
   - Procedures methods (getProcedures, createProcedure, updateProcedure, deleteProcedure, etc.)
   - Sampling Features methods (getSamplingFeatures, createSamplingFeature, etc.)
   - Properties methods (getProperties, getProperty - read-only)
   - DataStreams methods (getDataStreams, createDataStream, getDataStreamSchema, etc.)
   - Observations methods (getObservations, createObservations, bulkCreateObservations, etc.)
   - Control Streams methods (getControlStreams, createControlStream, getControlStreamSchema, etc.)
   - Commands methods (getCommands, createCommand, getCommandStatus, getCommandResult, cancelCommand, etc.)
   - FULL query parameter support across all methods
2. **SensorML Handler** - New format parser for SensorML 3.0 (all system models, recursive component parsing, SWE Common integration)
3. **SWE Common Handler** - New format parser for SWE Common 3.0 (JSON/Text/Binary encodings, all data component types, schema validation)

### Architectural Notes:

**QueryBuilder Pattern:** Following the upstream EDR pattern (PR #114), CSAPI uses a single QueryBuilder class accessed via a factory method on OgcApiEndpoint. Developers call `endpoint.csapi(collectionId)` to get a CSAPIQueryBuilder instance containing all 9 resource type methods. This maintains the library's architecture principle of composition over inheritance.

**Resource Methods within QueryBuilder:** The 9 resource sections documented above (Systems, Deployments, Procedures, Sampling Features, Properties, DataStreams, Observations, Control Streams, Commands) are all methods within the single CSAPIQueryBuilder class, not separate standalone components. This follows the same pattern as EDR where `EDRQueryBuilder` contains methods like `getCubeUrl()`, `getCorridorUrl()`, etc.

**Integration Footprint:** Total modifications to existing files: ~48 lines across 2-3 files (`endpoint.ts`: ~35 lines, `info.ts`: ~7 lines, `index.ts`: ~6 lines). This minimal footprint follows the proven EDR integration pattern.

**Scope Understanding:** While the summary lists "3 components building new code" (architecturally accurate), the CSAPIQueryBuilder component represents ~70% of the new code volume (~10,000-14,000 lines) because it implements URL construction for 9 distinct CSAPI resource types with approximately 60-70 unique URL patterns covering full CRUD operations, nested resource access, schema endpoints, and comprehensive query parameter support. The detailed sections above document the functional methods within this single CSAPIQueryBuilder class. This consolidated single-class architecture follows the upstream EDR pattern (one QueryBuilder per API family) but delivers functionally extensive capabilities across all CSAPI resources. Clients evaluating scope should understand that while architecturally elegant (3 new classes vs 12), the functional scope is substantial - implementing complete CSAPI Part 1 and Part 2 specifications with full query, filter, and pagination support across all resource types.

### Estimated Scope:

- **Extending existing code:** ~20% of effort (9 small extensions, ~50 total lines modified)
- **Building new code:** ~80% of effort (CSAPIQueryBuilder with ~60-70 URL patterns, 2 complex format parsers)
- **Total estimated lines of code:** ~15,000-20,000 lines
- **Total estimated time:** 6-8 weeks for complete implementation

---

## Project Goals Alignment

Every component described above aligns with these core project goals:

1. **Unified Developer Experience:** All CSAPI functionality accessed through existing `OgcApiEndpoint` class using the same patterns as Features, Tiles, and EDR
2. **Format Abstraction:** Developers work with TypeScript objects, not raw GeoJSON/SensorML/SWE Common
3. **Upstream Integration:** Extensions follow established patterns in the camptocamp/ogc-client repository
4. **Complete Spec Coverage:** All CSAPI Part 1 and Part 2 resources with full CRUD support
5. **Production Ready:** Comprehensive validation, error handling, testing, and documentation
6. **Performance Aware:** Web Worker support for heavy operations, efficient pagination, streaming support

---

## Development Standards

**Recommended Development Workflow:**

1. Write method signatures before implementation
2. Add comprehensive JSDoc comments with parameters, return types, examples
3. Implement functionality with inline documentation for complex logic
4. Write tests as you implement (not deferred to later)
5. Document edge cases and validation rules as discovered
6. Add usage examples to JSDoc for common scenarios
7. Update as you go - don't defer documentation

**Code Quality Standards:**

- TypeScript strict mode enabled
- 100% public API JSDoc coverage
- > 80% test coverage (statement and branch)
- Lint-clean code (ESLint configuration)
- No magic numbers or strings (use constants)
- Consistent error handling patterns
- Performance profiling for heavy operations

**Documentation Standards:**

- Clear, concise method descriptions
- Parameter descriptions with types and constraints
- Return type documentation
- Example code for common use cases
- Links to relevant CSAPI specification sections
- Error condition documentation
- Performance characteristics noted where relevant
