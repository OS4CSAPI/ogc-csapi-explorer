# CSAPI Implementation Guide for Camptocamp OGC Client Library

**Last Updated:** February 5, 2026  
**Version:** 6.0 (Complete Self-Contained Guide)

---

## Executive Summary

This implementation adds Connected Systems API (CSAPI) support to the Camptocamp OGC Client Library, enabling developers to interact with sensor networks, observation data, and system control through the same unified interface they already use for OGC API Features, Tiles, and Environmental Data Retrieval (EDR).

> **📊 RESEARCH FOUNDATION**
>
> This implementation guide is built on **13 completed research plans** (Plans 01-04, 10-16) with **⭐⭐⭐⭐⭐ confidence ratings (98-100%)** for all architectural and implementation decisions. Every design choice documented here has been validated through systematic analysis of:
>
> - Upstream library patterns (100% consistency with existing code)
> - CSAPI specification requirements (complete Parts 1 & 2 coverage)
> - Real-world usage scenarios (validated workflows)
> - Performance characteristics (proven patterns)
> - Integration patterns (EDR as exact template)
> - Type system design (three-tier hierarchy)
> - File organization (flat structure + formats/)
> - Lessons learned from two previous failed attempts
>
> **See:** [Architecture Decision Documents](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/tree/main/docs/research/design/csapiquerybuilder/architecture-decision/results) for complete research foundation.

**What We're Building:**

- **9 components extending existing code** - Small, targeted enhancements to conformance checking, collection parsing, format detection, validation, and worker infrastructure (~50 lines of modifications total)
- **3 components building new code** - CSAPIQueryBuilder class for URL construction, SensorML 3.0 parser, and SWE Common 3.0 parser

**Key Architectural Facts:**

- **Integration Footprint:** 64 lines across 3 files (`endpoint.ts`: 35 lines, `info.ts`: 12 lines, `index.ts`: 17 lines)
- **QueryBuilder Pattern:** Single `CSAPIQueryBuilder` class accessed via `endpoint.csapi(collectionId)` (follows upstream EDR pattern from PR #114)
- **9 Resource Types:** Systems, Deployments, Procedures, Sampling Features, Properties, DataStreams, Observations, Control Streams, Commands - all as methods within one QueryBuilder class
- **Resource Validation:** All ~70-80 methods validate resource availability and fail-fast with clear error messages (user mandate)
- **Type System:** Complete TypeScript types for all resources (1,750-2,400 lines) with three-tier hierarchy
- **Full CSAPI Support:** Complete Parts 1 & 2 implementation with all query parameters, filtering, pagination, and format support - NOT MVP scope

**Scope Clarification:** While architecturally elegant (3 new classes, 9 extensions), the CSAPIQueryBuilder represents ~70% of new code volume because it implements comprehensive URL construction for 60-70 unique URL patterns across all CSAPI resource types with full CRUD, query, filter, and pagination capabilities. See [Summary: Build vs Extend Breakdown](#summary-build-vs-extend-breakdown) for detailed component inventory.

**Estimated Code Volume:** ~4,614-6,094 lines implementation + ~4,500-6,000 lines tests = **~9,114-12,094 lines total**

**Estimated Effort:** 40-60 hours development time (6-8 weeks calendar time with testing)

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Table of Contents](#table-of-contents)
3. [Purpose and Scope](#purpose-and-scope)
4. [Architecture Overview](#architecture-overview)
   - [Component Interaction Diagram](#component-interaction-diagram)
   - [Research Foundation](#research-foundation)
5. [Service Discovery Components](#service-discovery-components)
   - [Conformance Reader](#conformance-reader-extending-existing-capability-detection)
   - [Collections Reader](#collections-reader-extending-metadata-parsing)
   - [OgcApiEndpoint Integration](#ogcapiendpoint-integration-extending-main-endpoint-class)
6. [Query Builder Component](#query-builder-component)
   - [CSAPIQueryBuilder Overview](#csapiquerybuilder-building-new-query-construction-class)
   - [Resource Validation Strategy](#resource-validation-strategy)
   - [Helper Methods](#helper-methods)
   - [Architecture Validation](#architecture-validation-query-parameters-and-code-reuse)
   - [Navigation Patterns](#navigation-patterns-fluent-api-design)
   - [File Structure](#file-structure-and-organization)
   - [Type System Architecture](#type-system-architecture)
   - [Import Conventions](#import-conventions)
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
   - [Why Full Format Handling](#why-full-format-handling-for-csapi)
   - [Format Type System](#format-type-system)
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
11. [Developer Experience](#developer-experience)
    - [API Surface](#api-surface)
    - [Type-Safe Usage](#type-safe-usage)
    - [Format Parser Integration](#format-parser-integration)
    - [Error Handling Patterns](#error-handling-patterns)
12. [Real-World Usage Scenarios](#real-world-usage-scenarios)
    - [Scenario 1: Real-Time Temperature Monitoring](#scenario-1-real-time-temperature-monitoring)
    - [Scenario 2: Remote System Control and Tasking](#scenario-2-remote-system-control-and-tasking)
    - [Scenario 3: Historical Data Analysis](#scenario-3-historical-data-analysis)
    - [Scenario 4: System Deployment Tracking](#scenario-4-system-deployment-tracking)
    - [Scenario 5: Dashboard Data Aggregation](#scenario-5-dashboard-data-aggregation)
    - [Scenario Complexity Analysis](#scenario-complexity-analysis)
13. [Implementation Roadmap](#implementation-roadmap)
    - [Phase 1: Core Structure](#phase-1-core-structure-low-complexity)
    - [Phase 2: QueryBuilder](#phase-2-querybuilder-medium-complexity)
    - [Phase 3: Format Parsers](#phase-3-format-parsers-high-complexity)
    - [Phase 4: Tests](#phase-4-tests-medium-high-complexity)
14. [Code Volume Summary](#code-volume-summary)
15. [Summary: Build vs Extend Breakdown](#summary-build-vs-extend-breakdown)
16. [Project Goals Alignment](#project-goals-alignment)
17. [Development Standards](#development-standards)

---

## Purpose and Scope

This document describes every component needed to implement CSAPI support in the Camptocamp OGC Client Library, explaining which components extend existing code versus which require building new code from scratch. **This is a complete implementation manual with actionable roadmap.**

**What This Document Provides:**

- Complete component inventory for CSAPI implementation
- Clear identification of "extend" vs "build" work
- Integration points with existing library code
- Exact integration code (copy-pasteable)
- Complete type system architecture
- Query parameter reference for all CSAPI resources
- Step-by-step implementation roadmap
- Developer experience patterns
- Research-validated architectural decisions

**Scope Statement:**
This implementation provides **COMPLETE CSAPI Parts 1 & 2 support** including:

- ✅ All query parameters (spatial, temporal, hierarchical, relationship-based, property-based)
- ✅ Full filtering capabilities (bbox, datetime, recursive, parent, system, foi, observedProperty, etc.)
- ✅ Both pagination modes (offset-based and cursor-based)
- ✅ All three SWE Common encodings (JSON, Text/CSV, Binary)
- ✅ Complete schema validation
- ✅ All CRUD operations
- ✅ Resource validation (fail-fast with clear error messages)
- ✅ Full TypeScript type system (1,750-2,400 lines)

**This is NOT an MVP** - this is a production-ready, specification-complete implementation suitable for enterprise use.

**References:**

- [OGC API - Connected Systems Part 1: Feature Resources](https://docs.ogc.org/is/23-001/23-001.html) - Standard defining Systems, Deployments, Procedures, Sampling Features, Properties
- [OGC API - Connected Systems Part 2: Dynamic Data](https://docs.ogc.org/is/23-002/23-002.html) - Standard defining DataStreams, Observations, Control Streams, Commands
- [Full Implementation Scope Definition](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/requirements/contribution-definition.md) - Complete vs partial implementation rationale
- [CSAPI Part 1 Requirements](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/requirements/csapi-part1-requirements.md) - Comprehensive Part 1 requirements analysis
- [CSAPI Part 2 Requirements](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/requirements/csapi-part2-requirements.md) - Comprehensive Part 2 requirements analysis
- [Upstream Library Expectations](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/requirements/upstream-expectations.md) - What camptocamp/ogc-client expects from implementations
- [Architecture Decision - Part 1: Structure](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/design/csapiquerybuilder/architecture-decision/results/DECISION-part1-structure.md) - Structural design decisions
- [Architecture Decision - Part 2: Implementation](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/design/csapiquerybuilder/architecture-decision/results/DECISION-part2-implementation.md) - Implementation details
- [Architecture Decision - Part 3: Validation](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/design/csapiquerybuilder/architecture-decision/results/DECISION-part3-validation.md) - Architecture validation through usage scenarios

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
│  │  • endpoint.csapi(collectionId)    → CSAPIQueryBuilder  │◄──┼── New Factory Method (17 lines)
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  Conformance: hasConnectedSystems ◄─── New Getter (6 lines)    │
│  Collections: csapiCollections    ◄─── New Getter (6 lines)    │
└─────────────────────────────────────────────────────────────────┘
                            │
                            │ returns instance
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│             CSAPIQueryBuilder (NEW - single class)              │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Resource Validation (all 70-80 methods):                 │   │
│  │  • availableResources property (Set<string>)             │   │
│  │  • Validate before building URL                          │   │
│  │  • Fail-fast with clear error messages                   │   │
│  └──────────────────────────────────────────────────────────┘   │
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
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Helper Methods (private, 2-3 methods):                   │   │
│  │  • buildResourceUrl()     - Core URL construction        │   │
│  │  • buildQueryString()     - Parameter serialization      │   │
│  │  • extractAvailableResources() - Resource discovery      │   │
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
3. **Resource Validation:** All methods validate resource availability before building URLs (fail-fast with clear errors)
4. **Helper Methods:** Private helper methods for code reuse (no inheritance)
5. **Format Abstraction:** Developers work with TypeScript objects, format handlers parse wire formats transparently
6. **Minimal Integration:** 64 lines of modifications to existing files maintain upstream compatibility
7. **Worker Offloading:** Heavy parsing/validation operations run off main thread for UI responsiveness
8. **Three-Tier Type System:** Shared → OGC API → CSAPI types for maximum reuse

---

### Research Foundation

This implementation is built on extensive research with 98-100% confidence levels:

**Completed Research Plans (13 of 22):**

| Plan | Title                    | Confidence | Key Finding                              |
| ---- | ------------------------ | ---------- | ---------------------------------------- |
| 01   | PR#114 EDR Pattern       | ⭐⭐⭐⭐⭐ | Factory method template, caching pattern |
| 02   | QueryBuilder Pattern     | ⭐⭐⭐⭐⭐ | Single builder class per API             |
| 03   | CSAPI Architecture       | ⭐⭐⭐⭐⭐ | 9 resources, format handling required    |
| 04   | Architecture Patterns    | ⭐⭐⭐⭐⭐ | 100% use helper methods, 0% inheritance  |
| 10   | Upstream Expectations    | ⭐⭐⭐⭐⭐ | Minimal validation, trust server         |
| 11   | Integration Requirements | ⭐⭐⭐⭐⭐ | EDR pattern exactly (64 lines)           |
| 12   | File Organization        | ⭐⭐⭐⭐⭐ | Flat structure + formats/ subfolder      |
| 13   | TypeScript Types         | ⭐⭐⭐⭐⭐ | Three-tier hierarchy, single model.ts    |
| 14   | Usage Scenarios          | ⭐⭐⭐⭐⭐ | 100% multi-resource workflows            |
| 15   | Query Parameters         | ⭐⭐⭐⭐⭐ | 47% shared, type-based clustering        |
| 16   | Subresource Navigation   | ⭐⭐⭐⭐⭐ | 100% cross-boundary navigation           |

**Key Decisions Validated:**

- **Single Class:** 100% of upstream APIs use single builder (not multi-class)
- **Helper Methods:** 100% use private helpers, 0% use inheritance
- **Format Handling:** CSAPI-specific complexity requires full parsing
- **Resource Validation:** User mandate for better developer experience
- **Integration Pattern:** Copy EDR exactly (64 lines total)
- **File Structure:** Flat + formats/ subfolder (21 files)
- **Type System:** Three-tier hierarchy with 1,750-2,400 lines

**References:**

- [Architecture Decision - Part 1](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/design/csapiquerybuilder/architecture-decision/results/DECISION-part1-structure.md) - Structural design with confidence ratings
- [Architecture Decision - Part 2](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/design/csapiquerybuilder/architecture-decision/results/DECISION-part2-implementation.md) - Implementation details
- [Architecture Decision - Part 3](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/design/csapiquerybuilder/architecture-decision/results/DECISION-part3-validation.md) - Usage scenario validation
- [Lessons Learned](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/design/csapiquerybuilder/architecture-decision/results/LESSONS-LEARNED-multi-class-failure.md) - Why previous multi-class attempts failed

**References (Architecture Patterns):**

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

**Implementation Type:** EXTENDING EXISTING CODE (~12 lines in `info.ts`)

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

The OgcApiEndpoint integration adds the CSAPI factory method to the main `OgcApiEndpoint` class following the exact pattern established by EDR support (PR #114). This integration adds **64 lines total** across 3 files to expose CSAPI functionality through a single developer-facing method. Developers access all CSAPI capabilities through `endpoint.csapi(collectionId)` which returns a `CSAPIQueryBuilder` instance containing all URL-building methods for the 9 CSAPI resource types. The factory method includes conformance checking (`hasConnectedSystems`), collection metadata fetching, QueryBuilder instantiation, and caching for performance. This minimal integration approach maintains the library's architecture principle of composition over inheritance - no subclassing, just a factory method that returns a specialized query builder. The integration also includes adding the `csapiCollections` getter for filtering collections that support CSAPI resources, and a private cache field for QueryBuilder instances.

**Integration Points in OgcApiEndpoint:**

#### endpoint.ts Changes (+35 lines)

```typescript
// 1. Import (1 line)
import CSAPIQueryBuilder from './csapi/url_builder.js';

// 2. Cache field (2 lines)
private collection_id_to_csapi_builder_: Map<string, CSAPIQueryBuilder> =
  new Map();

// 3. Collections getter (6 lines)
get csapiCollections(): Promise<string[]> {
  return Promise.all([this.data, this.hasConnectedSystems])
    .then(([data, hasCSAPI]) => (hasCSAPI ? data : { collections: [] }))
    .then(parseCollections)
    .then((collections) => collections.map((collection) => collection.name));
}

// 4. Conformance getter (6 lines)
get hasConnectedSystems(): Promise<boolean> {
  return Promise.all([this.conformanceClasses]).then(
    checkHasConnectedSystems
  );
}

// 5. Factory method (17 lines)
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

// 6. Import update (3 lines)
import {
  checkHasConnectedSystems,  // Add this line
  // ... existing imports
} from './shared/info.js';
```

#### info.ts Changes (+12 lines)

```typescript
export function checkHasConnectedSystems([conformance]: [ConformanceClass[]]) {
  return (
    conformance.indexOf(
      'http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/core'
    ) > -1 ||
    conformance.indexOf(
      'http://www.opengis.net/spec/ogcapi-connectedsystems-2/1.0/conf/dynamic-data'
    ) > -1
  );
}
```

#### index.ts Changes (+17 lines)

```typescript
// Export QueryBuilder class
export { default as CSAPIQueryBuilder } from './ogc-api/csapi/url_builder.js';

// Export types
export type {
  System,
  Deployment,
  SamplingFeature,
  Procedure,
  Property,
  Datastream,
  Observation,
  Control,
  ControlStream,
  Command,
  QueryOptions,
  SystemQueryOptions,
  ObservationQueryOptions,
} from './ogc-api/csapi/model.js';
```

**Total Integration Code:** 64 lines (35 + 12 + 17)

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

**Implementation Type:** EXTENDING EXISTING CODE (64 lines total across 3 files)

**References:**

- [PR #114 (EDR Implementation) Analysis](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/upstream/pr114-analysis.md) - **PRIMARY REFERENCE** - Direct blueprint for factory method pattern
- [Architecture Decision - Part 2: Integration](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/design/csapiquerybuilder/architecture-decision/results/DECISION-part2-implementation.md#decision-1-integration-pattern) - Complete integration code with line-by-line breakdown
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

**Implementation Type:** BUILDING NEW CODE (following EDRQueryBuilder pattern)

**Code Volume:**

- url_builder.ts: ~700-800 lines
- model.ts: ~350-400 lines (GeoJSON types)
- helpers.ts: ~50-80 lines
- formats/: ~3,450-4,750 lines
- **Total: ~4,550-6,030 lines**

**References:**

- [OGC API - Connected Systems Part 1: OpenAPI Specification](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/standards/ogcapi-connectedsystems-1.bundled.oas31.yaml) - Machine-readable API definition for Part 1 endpoints
- [OGC API - Connected Systems Part 2: OpenAPI Specification](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/standards/ogcapi-connectedsystems-2.bundled.oas31.yaml) - Machine-readable API definition for Part 2 endpoints
- [QueryBuilder Pattern Analysis](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/upstream/querybuilder-pattern-analysis.md) - Core pattern for implementation
- [URL Building Architecture](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/upstream/url-building-analysis.md) - URL construction patterns and query parameter assembly
- [TypeScript Type System Design](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/upstream/typescript-types-analysis.md) - Type definitions for query parameters and interfaces
- [CSAPI Architecture Decisions](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/upstream/csapi-architecture-analysis.md) - Single-class design for 9 resource types
- [Architecture Decision - Part 1](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/design/csapiquerybuilder/architecture-decision/results/DECISION-part1-structure.md) - Complete structural design with confidence ratings
- [Architecture Decision - Part 2](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/design/csapiquerybuilder/architecture-decision/results/DECISION-part2-implementation.md) - Implementation details with exact code patterns

---

### Resource Validation Strategy

**User Mandate: All methods must validate resource availability before building URLs.**

This decision differs from the upstream EDR pattern (which has no validation) but significantly improves developer experience for CSAPI's 9 resource types.

**Implementation Pattern:**

```typescript
export default class CSAPIQueryBuilder {
  // Public property for users to check available resources
  public readonly availableResources: Set<string>;

  constructor(private collection_: OgcApiCollectionInfo) {
    this.availableResources = this.extractAvailableResources();
  }

  // Validate in ALL 70-80 methods before building URLs
  async getSystems(options?: QueryOptions): Promise<string> {
    if (!this.availableResources.has('systems')) {
      throw new EndpointError(
        `Collection '${this.collection_.id}' does not support 'systems' resource. ` +
          `Available resources: ${Array.from(this.availableResources).join(
            ', '
          )}`
      );
    }
    return this.buildResourceUrl('systems', undefined, undefined, options);
  }

  async getDeployments(options?: QueryOptions): Promise<string> {
    if (!this.availableResources.has('deployments')) {
      throw new EndpointError(
        `Collection '${this.collection_.id}' does not support 'deployments' resource. ` +
          `Available resources: ${Array.from(this.availableResources).join(
            ', '
          )}`
      );
    }
    return this.buildResourceUrl('deployments', undefined, undefined, options);
  }

  // ... validation in all 70-80 methods (~2 lines per method = ~140-160 lines total)
}
```

**Developer Experience:**

```typescript
const builder = await endpoint.csapi('sensors');

// No manual checking needed - method validates automatically
try {
  const url = await builder.getSystems();
  const response = await fetch(url);
  const systems = await response.json();
} catch (error) {
  // Clear error message immediately identifies the problem
  console.error(error.message);
  // "Collection 'sensors' does not support 'systems' resource. Available resources: deployments, datastreams"
}
```

**Why Validate (User Mandate):**

1. **Better Developer Experience:** Fail-fast with clear, actionable error messages
2. **Debugging Efficiency:** Users know immediately if resource is unavailable (not a network/server issue)
3. **Standard Practice:** Most client libraries validate before operations
4. **Small Code Cost:** ~140-160 lines total (~2 lines per method) for significant UX improvement
5. **Type Safety Extension:** TypeScript types + runtime validation = complete safety

**Trade-offs Accepted:**

- Deviates from EDR pattern - **Acceptable:** CSAPI has 9 resources (more complexity than EDR's 1)
- Additional code - **Acceptable:** ~140-160 lines is <2% of total implementation
- Validation overhead - **Negligible:** Set lookup is O(1), happens once per method call

**Code Volume:** ~140-160 lines across all methods

**Confidence:** ⭐⭐⭐⭐⭐ (5/5) - User mandate, clear UX benefit

**References:**

- [Architecture Decision - Part 1: Resource Validation](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/design/csapiquerybuilder/architecture-decision/results/DECISION-part1-structure.md#decision-4-resource-validation-user-mandate) - Complete rationale and implementation pattern

---

### Helper Methods

**Pattern: Private helper methods for code reuse (not inheritance).**

Research shows 100% of upstream APIs use helper methods, 0% use inheritance.

**Helper Methods to Implement:**

```typescript
export default class CSAPIQueryBuilder {
  // ========================================
  // PRIVATE HELPERS (2-3 methods)
  // ========================================

  /**
   * Core URL construction helper
   * Handles canonical and nested resource endpoints
   * @param resourceType - Resource type (systems, deployments, etc.)
   * @param id - Optional resource ID
   * @param subPath - Optional sub-path (subsystems, datastreams, etc.)
   * @param options - Query parameters
   * @returns Constructed URL
   */
  private buildResourceUrl(
    resourceType: string,
    id?: string,
    subPath?: string,
    options?: QueryOptions
  ): string {
    let url = `${this.baseUrl}/${resourceType}`;
    if (id) url += `/${id}`;
    if (subPath) url += `/${subPath}`;
    return url + this.buildQueryString(options);
  }

  /**
   * Query parameter serialization helper
   * Handles encoding, arrays, special characters
   * @param options - Query parameter object
   * @returns Query string (with leading ?)
   */
  private buildQueryString(options?: QueryOptions): string {
    if (!options) return '';
    const params = new URLSearchParams();

    for (const [key, value] of Object.entries(options)) {
      if (value !== undefined && value !== null) {
        if (Array.isArray(value)) {
          // Handle array parameters (e.g., id=sys1,sys2,sys3)
          params.append(key, value.join(','));
        } else {
          params.append(key, String(value));
        }
      }
    }

    const queryString = params.toString();
    return queryString ? `?${queryString}` : '';
  }

  /**
   * Resource discovery helper
   * Extracts available resources from collection links
   * @returns Set of available resource types
   */
  private extractAvailableResources(): Set<string> {
    const resources = new Set<string>();

    // Parse collection links to find CSAPI resources
    for (const link of this.collection_.links) {
      const match = link.rel?.match(/^ogc-cs:(.+)$/);
      if (match) {
        resources.add(match[1]); // e.g., 'systems', 'datastreams'
      }
    }

    return resources;
  }

  // ========================================
  // PUBLIC METHODS (70-80 methods)
  // ========================================

  // All public methods use the helpers above for code reuse
}
```

**Code Reuse Benefits:**

- `buildResourceUrl()` used by ~70-80 methods → ~60% code reduction
- `buildQueryString()` used by all parameterized methods → ~85% reuse
- `extractAvailableResources()` called once in constructor

**Why Helper Methods (Not Inheritance):**

1. **Upstream Consistency:** 100% of existing APIs use helpers
2. **Visibility:** All methods visible in one class
3. **Simplicity:** No abstract base classes, no inheritance chains
4. **Maintainability:** Easy to understand and navigate

**Code Volume:** ~50-80 lines (3 helper methods)

**Confidence:** ⭐⭐⭐⭐⭐ (5/5) - Zero inheritance precedent in codebase

**References:**

- [Architecture Decision - Part 1: Helper Methods](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/design/csapiquerybuilder/architecture-decision/results/DECISION-part1-structure.md#decision-2-helper-methods-not-inheritance) - Complete analysis of helper methods vs inheritance
- [Architecture Patterns Analysis](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/upstream/architecture-patterns-analysis.md) - 0% inheritance usage in upstream

---

### Architecture Validation: Query Parameters and Code Reuse

**Research validates single-class architecture through parameter complexity analysis.**

This section quantifies why helper methods in a single class provide massive code reuse compared to alternative multi-class designs.

#### Parameter Distribution Analysis

**From Research Plan 15 (Query Parameters):**

- **30+ total parameters** across all CSAPI resources
- **47% shared parameters** (14 parameters used by multiple resources)
- **53% resource-specific parameters** (16 parameters, but cluster by TYPE not by resource)
- **Key finding:** Parameters cluster by TYPE (spatial, temporal, relationship), not by resource boundary

**Parameter clusters:**

| Cluster Type     | Parameters                                                     | Used By                                            | Validation Logic                       |
| ---------------- | -------------------------------------------------------------- | -------------------------------------------------- | -------------------------------------- |
| **Universal**    | limit, offset, f, id, uid, q                                   | 9 resources                                        | Same across all                        |
| **Spatial**      | bbox                                                           | Systems, Deployments, Procedures, SamplingFeatures | Same across all 4                      |
| **Temporal**     | datetime, phenomenonTime, resultTime, executionTime, issueTime | 5+ resources                                       | Same logic, different applicability    |
| **Relationship** | parent, procedure, foi, observedProperty, system, etc.         | Varies by resource                                 | Same encoding, different applicability |
| **Format**       | obsFormat, cmdFormat                                           | Schema endpoints                                   | Same logic                             |
| **Hierarchical** | recursive                                                      | Systems, Deployments                               | Same logic                             |
| **Pagination**   | cursor                                                         | Observations, Commands                             | Same logic                             |

#### Code Reuse Metrics: Single-Class Architecture

```typescript
export default class CSAPIQueryBuilder {
  // ========================================
  // SHARED PARAMETER HELPERS (150-200 lines)
  // ========================================

  private buildQueryString(options?: QueryOptions): string {
    if (!options) return '';

    const params = new URLSearchParams();

    // Universal parameters (used by ALL 9 resources)
    if (options.bbox) params.set('bbox', this.encodeBBox(options.bbox));
    if (options.datetime)
      params.set('datetime', this.encodeDateTime(options.datetime));
    if (options.limit) params.set('limit', String(options.limit));
    if (options.offset) params.set('offset', String(options.offset));
    if (options.f) params.set('f', encodeURIComponent(options.f));

    // CSAPI common parameters
    if (options.id) params.set('id', this.encodeArray(options.id));
    if (options.uid) params.set('uid', this.encodeArray(options.uid));
    if (options.q) params.set('q', encodeURIComponent(options.q));

    // Relationship parameters (resource-specific applicability, shared logic)
    if (options.observedProperty) {
      params.set(
        'observedProperty',
        this.encodeArray(options.observedProperty)
      );
    }
    if (options.foi) params.set('foi', this.encodeArray(options.foi));

    // Temporal parameters (resource-specific applicability, shared logic)
    if (options.phenomenonTime) {
      params.set('phenomenonTime', this.encodeDateTime(options.phenomenonTime));
    }
    if (options.resultTime) {
      params.set('resultTime', this.encodeResultTime(options.resultTime));
    }

    return params.toString() ? `?${params.toString()}` : '';
  }

  // Type-based encoding helpers (shared across resources)
  private encodeBBox(bbox: BBoxFilter): string {
    this.validateBBox(bbox); // ✅ Same validation for 4 resources
    return [bbox.minLon, bbox.minLat, bbox.maxLon, bbox.maxLat].join(',');
  }

  private encodeDateTime(datetime: DateTimeFilter): string {
    this.validateDateTime(datetime); // ✅ Same validation for 5+ resources
    if (datetime.start && datetime.end) {
      return `${datetime.start.toISOString()}/${datetime.end.toISOString()}`;
    }
    return datetime.start.toISOString();
  }

  private encodeArray(values: string | string[]): string {
    return Array.isArray(values) ? values.join(',') : values;
  }

  private validateBBox(bbox: BBoxFilter): void {
    if (bbox.minLon >= bbox.maxLon || bbox.minLat >= bbox.maxLat) {
      throw new Error('Invalid bbox: min values must be less than max values');
    }
  }

  private validateDateTime(datetime: DateTimeFilter): void {
    if (datetime.start && datetime.end && datetime.start >= datetime.end) {
      throw new Error('Invalid datetime: start must be before end');
    }
  }

  // ========================================
  // PUBLIC METHODS (70-80 methods)
  // All methods use shared helpers above
  // ========================================

  async getSystems(options?: SystemQueryOptions): Promise<string> {
    if (!this.availableResources.has('systems')) {
      throw new EndpointError(`Collection does not support 'systems' resource`);
    }
    return `${this.baseUrl}/systems` + this.buildQueryString(options);
    // ✅ Uses shared helpers (bbox, datetime, limit, offset, etc.)
  }

  async getDataStreams(options?: DatastreamQueryOptions): Promise<string> {
    if (!this.availableResources.has('datastreams')) {
      throw new EndpointError(
        `Collection does not support 'datastreams' resource`
      );
    }
    return `${this.baseUrl}/datastreams` + this.buildQueryString(options);
    // ✅ Uses same shared helpers
  }

  async getObservations(options?: ObservationQueryOptions): Promise<string> {
    if (!this.availableResources.has('observations')) {
      throw new EndpointError(
        `Collection does not support 'observations' resource`
      );
    }
    return `${this.baseUrl}/observations` + this.buildQueryString(options);
    // ✅ Uses same shared helpers
  }

  // ... 67 more methods, all using same helpers
}
```

**Code Metrics - Single-Class:**

- Parameter helpers: **150-200 lines** (ONE implementation)
- Methods using helpers: **70-80 methods**
- Reuse efficiency: **85%** (helpers used by 60+ methods)
- Code duplication: **0 lines**
- Maintenance locations: **1 file** (all parameter logic in one place)

#### Alternative: Multi-Class Code Duplication

**Hypothetical multi-class approach would require:**

```typescript
// ❌ SystemsBuilder class
class SystemsBuilder {
  private buildQueryString(options?: SystemQueryOptions): string {
    // ... duplicate 150-200 lines of parameter handling
  }
  private encodeBBox(bbox: BBoxFilter): string {
    /* duplicate 10-15 lines */
  }
  private encodeDateTime(datetime: DateTimeFilter): string {
    /* duplicate 10-15 lines */
  }
  private validateBBox(bbox: BBoxFilter): void {
    /* duplicate 5-10 lines */
  }
  // ... 8+ more duplicate helper methods
}

// ❌ DatastreamsBuilder class
class DatastreamsBuilder {
  private buildQueryString(options?: DatastreamQueryOptions): string {
    // ... duplicate same 150-200 lines again
  }
  private encodeDateTime(datetime: DateTimeFilter): string {
    /* duplicate again */
  }
  private validateDateTime(datetime: DateTimeFilter): void {
    /* duplicate again */
  }
  // ... 6+ more duplicate helper methods
}

// ❌ ObservationsBuilder class ... duplicate again
// ❌ 6 more builder classes ... duplicate 6 more times
```

**Code Metrics - Multi-Class:**

- Parameter helpers: **150-200 lines × 9 classes = 1,350-1,800 lines** of duplication
- Reuse efficiency: **0%** (each class implements own helpers)
- Code duplication: **1,200-1,600 lines** (726% overhead)
- Maintenance locations: **9 files** (bug fixes in up to 9 places)

**Maintenance Penalty:**

- Bug fix in `encodeBBox()` → Must fix in 4 classes (Systems, Deployments, Procedures, SamplingFeatures)
- Bug fix in `encodeDateTime()` → Must fix in 5+ classes (all temporal resources)
- Bug fix in `validatePagination()` → Must fix in 9 classes (all resources)
- **Result:** 4-9x maintenance overhead for every parameter-related change

#### Why Single-Class Architecture Wins

**Quantitative Benefits:**

1. **✅ 726% less code** - 150-200 lines vs 1,350-1,800 lines
2. **✅ 85% reuse efficiency** - Helpers used by 60+ methods
3. **✅ 89% fewer maintenance locations** - 1 file vs 9 files for bug fixes
4. **✅ Type-based validation clustering** - bbox validation same for all 4 spatial resources
5. **✅ Consistent behavior guaranteed** - Same encoding/validation logic across all resources

**Qualitative Benefits:**

1. **✅ Single source of truth** - One implementation for each parameter type
2. **✅ Easy testing** - Test each parameter handler once, applies to all methods
3. **✅ No divergence risk** - Cannot have inconsistent parameter handling between resources
4. **✅ Clear organization** - All parameter logic visible in one location
5. **✅ Upstream consistency** - Matches EDR pattern (helper methods in single class)

**Why Alternative Fails:**

1. **❌ Massive duplication** - 1,200-1,600 wasted lines
2. **❌ Maintenance nightmare** - Bug fixes propagate to 9 classes
3. **❌ Inconsistency risk** - Each class could diverge in behavior
4. **❌ Testing overhead** - Must test parameter handling 9 times
5. **❌ No architectural benefit** - Resource boundaries don't align with parameter types

**Confidence:** ⭐⭐⭐⭐⭐ (5/5) - Parameter complexity provides quantitative proof AGAINST class separation

**References:**

- [Architecture Decision - Part 3: Query Parameter Validation](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/design/csapiquerybuilder/architecture-decision/results/DECISION-part3-validation.md#decision-2-query-parameter-validation) - Complete parameter analysis with distribution tables
- [Research Plan 15](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/design/csapiquerybuilder/research-plan-15-query-parameters.md) - Original query parameter research

---

### Navigation Patterns: Fluent API Design

**Research validates single-class enables seamless multi-hop navigation across resource boundaries.**

This section demonstrates how the single-class architecture enables fluent method chaining for complex navigation patterns that span multiple resource types.

#### Navigation Pattern Requirements

**From Research Plan 16 (Subresource Navigation):**

- **16 navigation patterns** identified across all resources
- **100% cross resource boundaries** - Not a single pattern stays within one resource type
- **Maximum depth: 6+ levels** - System → Subsystem → ... → DataStream → Observation
- **Industry standard:** Fluent APIs used by AWS SDK, Google Cloud Client, Stripe API

**Navigation pattern examples:**

```
System navigates to:
  → Subsystems (hierarchical, unlimited depth)
  → Deployments (associative relationship)
  → SamplingFeatures (compositional relationship)
  → DataStreams (compositional, crosses Part 1 → Part 2 boundary)
  → ControlStreams (compositional, crosses Part 1 → Part 2 boundary)
  → SystemEvents (compositional relationship)

DataStream navigates to:
  → Observations (compositional relationship)
  → Schema (metadata endpoint)

ControlStream navigates to:
  → Commands (compositional relationship)
  → Feasibility (validation endpoint)

Command navigates to:
  → Status (state tracking)
  → Result (output data)

Deployment navigates to:
  → Subdeployments (hierarchical, unlimited depth)
  → Systems (reverse associative relationship)
```

**Key finding:** Every navigation pattern requires traversing resource type boundaries. Multi-hop paths are common (3-6 resource types in single workflow).

#### Seamless Navigation with Single-Class

**Implementation:**

```typescript
export default class CSAPIQueryBuilder {
  private baseUrl: string;
  private parentContext: ParentContext | null = null;

  // ========================================
  // FLUENT NAVIGATION API
  // All methods return same class type
  // ========================================

  // System navigation
  system(systemId: string): CSAPIQueryBuilder {
    const builder = this.clone();
    builder.parentContext = { type: 'system', id: systemId };
    return builder; // ✅ Returns CSAPIQueryBuilder
  }

  // Hierarchical navigation (unlimited depth)
  subsystem(subsystemId: string): CSAPIQueryBuilder {
    if (this.parentContext?.type !== 'system') {
      throw new Error('subsystem() requires system context');
    }
    const builder = this.clone();
    builder.parentContext = { type: 'system', id: subsystemId };
    return builder; // ✅ Returns CSAPIQueryBuilder (same type)
  }

  // Cross-boundary navigation (Part 1 → Part 2)
  datastream(datastreamId: string): CSAPIQueryBuilder {
    if (this.parentContext?.type !== 'system') {
      throw new Error('datastream() requires system context');
    }
    const builder = this.clone();
    builder.parentContext = { type: 'datastream', id: datastreamId };
    return builder; // ✅ Returns CSAPIQueryBuilder (same type)
  }

  // Terminal methods (return data)
  async getObservations(options?: ObservationQueryOptions): Promise<string> {
    if (this.parentContext?.type !== 'datastream') {
      throw new Error('getObservations() requires datastream context');
    }
    return (
      `${this.baseUrl}/datastreams/${this.parentContext.id}/observations` +
      this.buildQueryString(options)
    );
  }
}
```

**Usage - 6-Level Deep Navigation:**

```typescript
// Example: Navigate from system through nested subsystems to observations
const client = await endpoint.csapi('sensor-network');

const observations = await client
  .system('wx-station-001') // ✅ Returns CSAPIQueryBuilder
  .subsystem('temperature-module') // ✅ Returns CSAPIQueryBuilder
  .subsystem('sensor-array') // ✅ Returns CSAPIQueryBuilder
  .subsystem('sensor-001') // ✅ Returns CSAPIQueryBuilder
  .datastream('temp-ds-123') // ✅ Returns CSAPIQueryBuilder
  .getObservations({ limit: 100 }); // ✅ Returns Promise<string>

// ✅ Type-safe throughout entire chain
// ✅ No class switching or type changes
// ✅ IDE autocomplete works at every level
// ✅ Single fluent expression
```

**Code Metrics - Single-Class:**

- Navigation code: **500-600 lines** in 1 file
- Circular dependencies: **0**
- Method chain breaks: **0**
- Type safety: **Full** (preserved through entire chain)
- IDE support: **Complete** (autocomplete at every level)

#### Real-World Usage Pattern Examples

**Example 1: Recursive System Discovery**

```typescript
// Discover all temperature sensors in hierarchical system
const client = await endpoint.csapi('weather-network');

async function discoverTempSensors(systemId: string): Promise<Datastream[]> {
  const system = client.system(systemId);

  // Get temperature datastreams for this system
  const datastreams = await system.getDatastreams({
    observedProperty: 'temperature',
  });

  // Recursively check subsystems
  const subsystems = await system.getSubsystems();
  const nestedStreams = await Promise.all(
    subsystems.map((sub) => discoverTempSensors(sub.id))
  );

  return [...datastreams, ...nestedStreams.flat()];
}

// ✅ Seamless navigation between systems and datastreams
// ✅ No builder switching required
// ✅ Type-safe at all levels
```

**Example 2: Command Execution Tracking**

```typescript
// Execute command and track status to completion
const client = await endpoint.csapi('uav-fleet');

const uavSystem = client.system('uav-007');
const controlStream = uavSystem.controlstream('flight-control');

// Issue command
const commandUrl = await controlStream.createCommand({
  parameters: { altitude: 500, speed: 15 },
});
const commandResponse = await fetch(commandUrl, { method: 'POST' });
const command = await commandResponse.json();

// Track status (poll until complete)
const statusUrl = await client.command(command.id).getStatus();
while (true) {
  const statusResponse = await fetch(statusUrl);
  const status = await statusResponse.json();

  if (status.state === 'completed') {
    // Get result datastream
    const resultUrl = await client.command(command.id).getResult();
    break;
  }
  await new Promise((resolve) => setTimeout(resolve, 1000));
}

// ✅ Seamless navigation: System → ControlStream → Command → Status → Result
// ✅ All on same client object
// ✅ No type casting or builder switching
```

**Example 3: Multi-Hop Deployment Analysis**

```typescript
// Analyze all observations across deployment network
const client = await endpoint.csapi('ocean-buoys');

const deployment = client.deployment('atlantic-array-2024');

// Get all systems in deployment
const systems = await deployment.getSystems();

// For each system, get datastreams and observations
for (const system of systems) {
  const datastreams = await client
    .system(system.id)
    .getDatastreams({ observedProperty: 'salinity' });

  for (const ds of datastreams) {
    const observations = await client.datastream(ds.id).getObservations({
      phenomenonTime: '2024-01-01/2024-01-31',
      limit: 1000,
    });

    analyzeSalinity(system.name, observations);
  }
}

// ✅ Seamless navigation: Deployment → System → Datastream → Observation
// ✅ No builder switching across Part 1/Part 2 boundary
// ✅ Natural workflow expression
```

#### Why Fluent API Requires Single-Class

**TypeScript Type Requirements:**

```typescript
// ✅ Single-class: All methods return same type
class CSAPIQueryBuilder {
  system(id: string): CSAPIQueryBuilder { ... }      // Same type
  subsystem(id: string): CSAPIQueryBuilder { ... }   // Same type
  datastream(id: string): CSAPIQueryBuilder { ... }  // Same type
  // ✅ Enables: client.system('id').datastream('id').getObservations()
}

// ❌ Multi-class: Methods return different types
class SystemsBuilder {
  subsystem(id: string): SystemsBuilder { ... }        // OK (same type)
  datastream(id: string): DatastreamsBuilder { ... }   // ❌ Type change!
}
class DatastreamsBuilder {
  observations(): ObservationsBuilder { ... }          // ❌ Another type change!
}
// ❌ Breaks: client.system('id').datastream('id').observations()
//            ^^^^^^^^^^^^^^^^^^  ^^^^^^^^^^^^^^^^^^^  ^^^^^^^^^^^^^
//            SystemsBuilder      DatastreamsBuilder   ObservationsBuilder
//                                ↑ TypeScript error here
```

**Problems with Multi-Class Navigation:**

1. **❌ Type changes break fluent chains** - Every resource boundary requires new variable
2. **❌ IDE autocomplete breaks** - Type changes confuse IntelliSense
3. **❌ Cannot write single expression** - Must use intermediate variables
4. **❌ Circular dependencies** - All 9 classes must reference each other
5. **❌ Verbose code** - 3-4x more lines for same workflow

**Confidence:** ⭐⭐⭐⭐⭐ (5/5) - Navigation patterns provide STRONGEST evidence for single-class

**References:**

- [Architecture Decision - Part 3: Navigation Pattern Validation](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/design/csapiquerybuilder/architecture-decision/results/DECISION-part3-validation.md#decision-3-navigation-pattern-validation) - Complete navigation analysis with code examples
- [Research Plan 16](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/design/csapiquerybuilder/research-plan-16-subresource-navigation.md) - Original navigation pattern research
- [Industry Fluent API Patterns](https://aws.amazon.com/sdk-for-javascript/) - AWS SDK v3 fluent API design

---

### Systems Resource Methods

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

### Deployments Resource Methods

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

### Procedures Resource Methods

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

### Sampling Features Resource Methods

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

### Properties Resource Methods

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

### DataStreams Resource Methods

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

### Observations Resource Methods

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

### Control Streams Resource Methods

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

### Commands Resource Methods

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

### File Structure and Organization

**Research-Validated Structure:**

```
src/ogc-api/csapi/
├── url_builder.ts              (~700-800 lines) - CSAPIQueryBuilder class
│   ├── Constructor & validation (~50-100 lines)
│   ├── Helper methods (~50-80 lines)
│   │   ├── buildResourceUrl() - Core URL construction
│   │   ├── buildQueryString() - Parameter serialization
│   │   └── extractAvailableResources() - Resource discovery
│   ├── Part 1 methods (~400-500 lines, 42 methods)
│   │   ├── Systems (12 methods)
│   │   ├── Deployments (8 methods)
│   │   ├── Procedures (8 methods)
│   │   ├── Sampling Features (8 methods)
│   │   └── Properties (6 methods)
│   ├── Part 2 methods (~400-500 lines, 38 methods)
│   │   ├── DataStreams (11 methods)
│   │   ├── Observations (9 methods)
│   │   ├── Control Streams (8 methods)
│   │   └── Commands (10 methods)
│   └── Resource validation (~140-160 lines, ~2 lines/method)
│
├── model.ts                    (~350-400 lines) - GeoJSON types
│   ├── Resource type enum (12 lines)
│   ├── Query options (~40 lines)
│   │   ├── QueryOptions (base)
│   │   ├── SystemQueryOptions (extended)
│   │   └── ObservationQueryOptions (extended)
│   ├── Helper types (~40 lines)
│   │   ├── TimeInterval
│   │   ├── ResourceLink
│   │   ├── HistoryEvent
│   │   └── Characteristic
│   ├── Resource interfaces (~225 lines)
│   │   ├── System (~25 lines)
│   │   ├── Deployment (~25 lines)
│   │   ├── SamplingFeature (~25 lines)
│   │   ├── Procedure (~25 lines)
│   │   ├── Property (~25 lines)
│   │   ├── Datastream (~25 lines)
│   │   ├── Observation (~25 lines)
│   │   ├── Control (~25 lines)
│   │   ├── ControlStream (~25 lines)
│   │   └── Command (~25 lines)
│   └── Collection types (~35 lines)
│
├── helpers.ts                  (~50-80 lines) - Utility functions
│   ├── URL encoding helpers
│   ├── Temporal parsing utilities
│   └── Validation utilities
│
├── formats/                    (~3,450-4,750 lines) - Format parsers
│   ├── index.ts                (~50-100 lines) - Format exports
│   │   └── Barrel file for all parsers
│   │
│   ├── geojson.ts              (~50-100 lines) - GeoJSON utilities
│   │   └── CSAPI property extraction
│   │
│   ├── constants.ts            (~50-100 lines) - Media types, namespaces
│   │   ├── Media type constants
│   │   ├── Resource type constants
│   │   └── Vocabulary URI constants
│   │
│   ├── sensorml/               (~1,600-2,200 lines)
│   │   ├── index.ts            (~50-100 lines) - SensorML exports
│   │   │
│   │   ├── types.ts            (~800-1,200 lines) - TypeScript interfaces
│   │   │   ├── PhysicalSystem interface
│   │   │   ├── PhysicalComponent interface
│   │   │   ├── SimpleProcess/AggregateProcess interfaces
│   │   │   ├── Capability/Characteristic interfaces
│   │   │   ├── Component/Connection/Mode interfaces
│   │   │   └── 30+ supporting interfaces
│   │   │
│   │   ├── parser.ts           (~600-800 lines) - Main parser
│   │   │   ├── Main SensorML 3.0 parser
│   │   │   ├── Recursive component parsing
│   │   │   ├── Capability/characteristic parsing
│   │   │   └── Position/location parsing
│   │   │
│   │   ├── simple-process.ts   (~150-200 lines) - SimpleProcess parser
│   │   ├── aggregate-process.ts(~200-250 lines) - AggregateProcess parser
│   │   └── physical-system.ts  (~200-250 lines) - PhysicalSystem parser
│   │
│   └── swecommon/              (~1,600-2,250 lines)
│       ├── index.ts            (~50-100 lines) - SWE exports
│       │
│       ├── types.ts            (~600-800 lines) - TypeScript interfaces
│       │   ├── DataComponent union type
│       │   ├── DataRecord interface
│       │   ├── DataArray interface
│       │   ├── Quantity/Count/Text/Boolean interfaces
│       │   ├── Encoding interfaces (JSON/Text/Binary)
│       │   └── 20+ supporting interfaces
│       │
│       ├── parser.ts           (~500-700 lines) - Main parser
│       │   ├── Main SWE Common 3.0 parser
│       │   ├── Component type discrimination
│       │   ├── Encoding detection
│       │   └── Schema validation
│       │
│       ├── data-record.ts      (~150-200 lines) - DataRecord parser
│       ├── data-array.ts       (~200-250 lines) - DataArray parser
│       └── components.ts       (~300-400 lines) - Component parsers
│
├── model.spec.ts               (~200-300 lines) - Type tests
└── url_builder.spec.ts         (~800-1,000 lines) - QueryBuilder tests
```

**Total:** 21 files, ~5,100-6,730 lines

**File Purposes:**

**Core files (3):**

- `model.ts` - All TypeScript type definitions (GeoJSON-based resources)
- `url_builder.ts` - CSAPIQueryBuilder class with all 70-80 methods
- `helpers.ts` - Pure utility functions (URL building, validation, etc.)

**Format files (15):**

- `formats/index.ts` - Barrel file for parser exports
- `formats/geojson.ts` - GeoJSON parsing utilities (reuse geojson package)
- `formats/constants.ts` - Media type constants, namespace URIs
- `formats/sensorml/` - SensorML 3.0 parser (6 files)
- `formats/swecommon/` - SWE Common 3.0 parser (6 files)

**Test files (2):**

- `model.spec.ts` - Type validation tests
- `url_builder.spec.ts` - QueryBuilder method tests

**Format test files** - Located in test/ directory (not colocated due to subfolder depth)

**Why This Structure:**

1. **Flat Core:** url_builder.ts, model.ts, helpers.ts at same level (easy to find)
2. **Separate Formats:** formats/ subfolder isolates complex parsing logic
3. **Tree-Shaking Friendly:** Users can exclude formats/ if not needed
4. **Clear Imports:** `import { CSAPIQueryBuilder } from './csapi/url_builder'` vs `import { parseSensorML } from './csapi/formats/sensorml'`
5. **Maintainable:** Format changes isolated from QueryBuilder

**Why flat structure:**

1. ✅ **100% convention compliance** - Matches all upstream APIs
2. ✅ **Easy navigation** - No hunting through subdirectories
3. ✅ **Clear organization** - Purpose obvious from filename
4. ✅ **Colocated tests** - Test files next to implementation
5. ✅ **No barrel files** - Direct imports (except formats/index.ts)

**Why formats/ subfolder:**

1. ✅ **Size justification** - 3,450+ lines needs organization
2. ✅ **Separation of concerns** - URL building vs format parsing
3. ✅ **Tree-shaking** - Users can exclude parsers
4. ✅ **Maintainability** - Format changes isolated
5. ✅ **Import clarity** - `import { parseSensorML } from 'formats'`

**Code Volume Breakdown:**

| Component          | Lines           | Percentage |
| ------------------ | --------------- | ---------- |
| url_builder.ts     | 700-800         | 13-15%     |
| model.ts           | 350-400         | 6-8%       |
| helpers.ts         | 50-80           | 1%         |
| formats/sensorml/  | 1,600-2,200     | 30-35%     |
| formats/swecommon/ | 1,600-2,250     | 30-36%     |
| formats/ (other)   | 200-400         | 4-6%       |
| **TOTAL**          | **4,500-5,130** | **100%**   |

**Confidence:** ⭐⭐⭐⭐⭐ (5/5) - Research Plan 12 validated structure

**References:**

- [Architecture Decision - Part 2: File Organization](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/design/csapiquerybuilder/architecture-decision/results/DECISION-part2-implementation.md#decision-2-file-organization) - Complete file structure analysis
- [File Organization Strategy](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/upstream/file-organization-analysis.md) - Upstream file organization patterns

---

### Type System Architecture

**Research-Validated Three-Tier Hierarchy:**

The type system is organized in three tiers for maximum reuse and clarity:

1. **Tier 1: Shared Primitives** (from `../../shared/models.ts`)
2. **Tier 2: OGC API Common** (from `../model.ts`)
3. **Tier 3: CSAPI-Specific** (defined in `model.ts`)

#### model.ts Structure (~350-400 lines)

```typescript
// ========================================
// TIER 1: SHARED PRIMITIVES (import from ../../shared/models.ts)
// ========================================
import {
  BoundingBox, // Spatial primitive
  DateTimeParameter, // Temporal primitive
  CrsCode, // Coordinate reference system
  MimeType, // Format type
  Contact, // Metadata primitive
} from '../../shared/models.js';

// ========================================
// TIER 2: OGC API COMMON (import from ../model.ts)
// ========================================
import {
  OgcApiCollectionInfo, // Collection metadata
  OgcApiDocumentLink, // HATEOAS links
  ConformanceClass, // Conformance checking
} from '../model.ts';

// Import GeoJSON types from geojson package
import type { Geometry, Point } from 'geojson';

// ========================================
// TIER 3: CSAPI-SPECIFIC TYPES (define in this file)
// ========================================

// 1. Resource Type Enum (12 lines)
export const CSAPIResourceTypes = [
  'systems',
  'deployments',
  'samplingFeatures',
  'procedures',
  'properties',
  'datastreams',
  'observations',
  'controlStreams',
  'commands',
] as const;

export type CSAPIResourceType = (typeof CSAPIResourceTypes)[number];

// 2. Query Options (~40 lines)
export interface QueryOptions {
  limit?: number;
  offset?: number;
  bbox?: BoundingBox;
  datetime?: DateTimeParameter;
  f?: 'json' | 'geojson' | 'sml' | 'swe';
  crs?: CrsCode;
}

export interface SystemQueryOptions extends QueryOptions {
  propertyId?: string;
  procedureId?: string;
  recursive?: boolean;
  parent?: string;
}

export interface ObservationQueryOptions extends QueryOptions {
  datastreamId?: string;
  resultTime?: DateTimeParameter;
  phenomenonTime?: DateTimeParameter;
  cursor?: string;
}

// 3. Helper Types (~40 lines)
export interface TimeInterval {
  start: Date;
  end?: Date;
}

export type ResourceLink = OgcApiDocumentLink & {
  rel: 'self' | 'collection' | 'item' | 'alternate' | 'describedby';
};

export interface HistoryEvent {
  timestamp: Date;
  description: string;
  user?: string;
}

export interface Characteristic {
  name: string;
  value: string | number | boolean;
  unit?: string;
}

// 4. Resource Interfaces (~225 lines - ~25 lines each)
export interface System {
  id: string;
  type: 'System';
  properties: {
    name: string;
    description?: string;
    uid?: string;
    keywords?: string[];
    classification?: string[];
    validTime?: TimeInterval;
    contacts?: Contact[];
    capabilities?: Characteristic[];
    characteristics?: Characteristic[];
  };
  geometry?: Geometry;
  links: ResourceLink[];
}

export interface Deployment {
  id: string;
  type: 'Deployment';
  properties: {
    name: string;
    description?: string;
    deploymentTime: TimeInterval;
    platformId?: string;
    systemIds?: string[];
  };
  geometry?: Point;
  links: ResourceLink[];
}

export interface SamplingFeature {
  id: string;
  type: 'SamplingFeature';
  properties: {
    name: string;
    description?: string;
    featureType: string;
    sampledFeatureId?: string;
  };
  geometry?: Geometry;
  links: ResourceLink[];
}

export interface Procedure {
  id: string;
  type: 'Procedure';
  properties: {
    name: string;
    description?: string;
    procedureType: string;
  };
  links: ResourceLink[];
}

export interface Property {
  id: string;
  type: 'Property';
  properties: {
    name: string;
    description?: string;
    definition?: string;
    propertyType: string;
  };
  links: ResourceLink[];
}

export interface Datastream {
  id: string;
  type: 'Datastream';
  properties: {
    name: string;
    description?: string;
    systemId: string;
    deploymentId?: string;
    observedPropertyId: string;
    phenomenonTime?: TimeInterval;
    resultTime?: TimeInterval;
    unitOfMeasurement?: {
      name: string;
      symbol: string;
      definition?: string;
    };
  };
  links: ResourceLink[];
}

export interface Observation {
  id: string;
  type: 'Observation';
  properties: {
    phenomenonTime: Date;
    resultTime: Date;
    datastreamId: string;
    result: any; // Type depends on observed property
    resultQuality?: string[];
  };
  geometry?: Point;
  links: ResourceLink[];
}

export interface Control {
  id: string;
  type: 'Control';
  properties: {
    name: string;
    description?: string;
    controlType: string;
    parameters?: Record<string, any>;
  };
  links: ResourceLink[];
}

export interface ControlStream {
  id: string;
  type: 'ControlStream';
  properties: {
    name: string;
    description?: string;
    systemId: string;
    controlId: string;
  };
  links: ResourceLink[];
}

export interface Command {
  id: string;
  type: 'Command';
  properties: {
    issueTime: Date;
    executionTime?: Date;
    controlStreamId: string;
    parameters: Record<string, any>;
    status: 'pending' | 'accepted' | 'executing' | 'completed' | 'failed';
    result?: any;
  };
  links: ResourceLink[];
}

// 5. Collection Types (~35 lines)
export interface Collection<T> {
  type: 'FeatureCollection';
  features: T[];
  links: ResourceLink[];
  numberMatched?: number;
  numberReturned: number;
  timeStamp: Date;
}

export type SystemCollection = Collection<System>;
export type DeploymentCollection = Collection<Deployment>;
export type SamplingFeatureCollection = Collection<SamplingFeature>;
export type ProcedureCollection = Collection<Procedure>;
export type PropertyCollection = Collection<Property>;
export type DatastreamCollection = Collection<Datastream>;
export type ObservationCollection = Collection<Observation>;
export type ControlCollection = Collection<Control>;
export type ControlStreamCollection = Collection<ControlStream>;
export type CommandCollection = Collection<Command>;
```

**Total:** ~357 lines in model.ts

#### Why This Structure:

**Three-Tier Benefits:**

1. ✅ **Clear dependencies** - One-way imports (lower → higher)
2. ✅ **Code reuse** - Shared types prevent duplication
3. ✅ **Namespace clarity** - Types organized by scope
4. ✅ **Maintainability** - Changes isolated to appropriate tier

**Why single model.ts for GeoJSON:**

1. ✅ **Convention compliance** - EDR uses single model.ts
2. ✅ **Import simplicity** - One import for all resource types
3. ✅ **IntelliSense efficiency** - Full autocomplete from one source
4. ✅ **Logical grouping** - All GeoJSON resources together
5. ✅ **Size appropriate** - 350-400 lines is manageable

**Confidence:** ⭐⭐⭐⭐⭐ (5/5) - Research Plan 13 validated structure

**References:**

- [Architecture Decision - Part 2: Type System](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/design/csapiquerybuilder/architecture-decision/results/DECISION-part2-implementation.md#decision-3-typescript-type-system) - Complete type system with all interfaces
- [TypeScript Type System Design](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/upstream/typescript-types-analysis.md) - Three-tier hierarchy analysis

---

### Import Conventions

**Research-validated import patterns ensuring consistency with upstream:**

#### Core Imports (from main package)

```typescript
// Main classes
import { OgcApiEndpoint, CSAPIQueryBuilder } from '@camptocamp/ogc-client';

// GeoJSON types (CSAPI resources)
import type {
  System,
  Deployment,
  Datastream,
  Observation,
  SystemCollection,
  ObservationCollection,
} from '@camptocamp/ogc-client';

// Query options
import type {
  QueryOptions,
  SystemQueryOptions,
  ObservationQueryOptions,
} from '@camptocamp/ogc-client';
```

#### Format Imports (from formats/ subfolder)

```typescript
// SensorML parsers and types
import { parseSensorML30 } from '@camptocamp/ogc-client/csapi/formats/sensorml';
import type {
  PhysicalSystem,
  PhysicalComponent,
  Capability,
} from '@camptocamp/ogc-client/csapi/formats/sensorml';

// SWE Common parsers and types
import {
  parseSWEDataRecord,
  parseSWEDataArray,
} from '@camptocamp/ogc-client/csapi/formats/swecommon';
import type {
  DataRecord,
  DataArray,
  Quantity,
  DataEncoding,
} from '@camptocamp/ogc-client/csapi/formats/swecommon';

// Or barrel import (if using formats/index.ts)
import {
  parseSensorML30,
  parseSWEDataRecord,
} from '@camptocamp/ogc-client/csapi/formats';
```

#### Internal Imports (within implementation)

```typescript
// Three-tier hierarchy imports in model.ts
import {
  BoundingBox,
  DateTimeParameter,
  Contact,
} from '../../shared/models.js';
import { OgcApiCollectionInfo, OgcApiDocumentLink } from '../model.js';
import type { Geometry, Point } from 'geojson';

// Relative imports with .js extension (TypeScript convention)
import CSAPIQueryBuilder from './csapi/url_builder.js';
import { parseSensorML30 } from './csapi/formats/sensorml/parser.js';
```

#### Import Pattern Rules

1. **Use .js extension** - TypeScript requires .js for relative imports
2. **Relative imports only** - No absolute paths within library
3. **Three-tier hierarchy** - Import from lower tiers only
4. **Type-only imports** - Use `import type` for interfaces/types
5. **Named exports** - Prefer named exports for utilities
6. **Default export** - Only for main QueryBuilder class
7. **Barrel files** - Only for formats/ subfolder (tree-shaking)

**Why These Patterns:**

1. ✅ **100% Upstream Consistency** - Matches existing API patterns
2. ✅ **TypeScript Resolution** - .js extension required for ES modules
3. ✅ **Tree-Shaking** - Format imports are separate, excludable
4. ✅ **Clear Dependencies** - Three-tier hierarchy prevents circular imports
5. ✅ **Type Safety** - Type-only imports don't generate runtime code

**Confidence:** ⭐⭐⭐⭐⭐ (5/5) - 100% convention compliance

**References:**

- [Architecture Decision - Part 2: Import Patterns](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/design/csapiquerybuilder/architecture-decision/results/DECISION-part2-implementation.md#decision-5-user-experience-patterns) - Complete import pattern documentation

---

_[Continue with existing resource methods sections from v2.0 - Systems, Deployments, Procedures, Sampling Features, Properties, DataStreams, Observations, Control Streams, Commands, Query Parameters - these sections remain unchanged as they are already comprehensive]_

---

## Format Handler Components

### Why Full Format Handling for CSAPI

**This section explains why CSAPI requires full format parsing, unlike other OGC APIs (WFS, EDR, STAC) that only build URLs.**

**Research Evolution:**

- **Original Research (Plan 03):** Recommended URL-only (following upstream pattern)
- **User Mandate (2026-02-04):** Full format handling REQUIRED

**Why CSAPI is Different:**

1. **CSAPI-Specific Complexity:** SensorML 3.0 and SWE Common 3.0 are CORE to CSAPI functionality (not optional formats like WMS GetFeatureInfo XML or WFS DescribeFeatureType)

   - **Systems/Procedures:** Encoded in SensorML 3.0 (no simpler alternative)
   - **Observation Results:** Encoded in SWE Common 3.0 (binary/text/JSON - no alternatives)
   - **DataStream Schemas:** SWE Common DataComponents (complex type system)

2. **User Experience:** Manual parsing creates significant friction

   - Developers would need to implement 1,600+ lines of SensorML parser themselves
   - Developers would need to implement 1,600+ lines of SWE Common parser themselves
   - No mature TypeScript libraries exist for SensorML 3.0 / SWE Common 3.0
   - CSAPI adoption severely limited without format support

3. **Type Safety:** TypeScript interfaces provide strong typing

   - Parsed objects have full IntelliSense support
   - Compiler catches type errors
   - Better developer experience than raw JSON

4. **Ecosystem Gap:** No mature TypeScript libraries for these formats

   - SensorML 3.0: Published 2024, no existing TypeScript parsers
   - SWE Common 3.0: Published 2024, no existing TypeScript parsers
   - Library fills critical ecosystem gap

5. **Differentiation:** Complete CSAPI client library vs simple URL builder
   - Goal: Production-ready, enterprise-grade implementation
   - Not just a URL builder, but a complete CSAPI solution
   - Competitive advantage over minimal implementations

**Code Volume Impact:**

- URL-only implementation: ~1,100-1,280 lines
- Full format parsing: +3,450-4,750 lines (formats/)
- **Total: ~4,550-6,030 lines** (formats are 76-79% of implementation)

**Separation of Concerns:**

- CSAPIQueryBuilder = URL building ONLY
- Format parsers = Separate imports in formats/ subfolder
- Users choose when to parse (tree-shaking friendly)

**Usage Pattern:**

```typescript
import { CSAPIQueryBuilder } from '@camptocamp/ogc-client';
import { parseSensorML30 } from '@camptocamp/ogc-client/csapi/formats';

const builder = await endpoint.csapi('sensors');
const smlUrl = await builder.getSystem('sys-123', { f: 'sml' });
const response = await fetch(smlUrl);
const system = parseSensorML30(await response.text());
```

**Confidence:** ⭐⭐⭐⭐⭐ (5/5) - User mandate, clear ecosystem gap

**References:**

- [Architecture Decision - Part 1: Full Format Handling](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/design/csapiquerybuilder/architecture-decision/results/DECISION-part1-structure.md#decision-3-full-format-handling) - Complete rationale with research evolution

---

### Format Type System

**Complete TypeScript type definitions for SensorML 3.0 and SWE Common 3.0.**

This section details the format-specific types that enable full IntelliSense and type safety when working with parsed CSAPI formats.

#### SensorML 3.0 Types (~800-1,200 lines)

**Key Interfaces:**

```typescript
// formats/sensorml/types.ts
// Based on OGC 23-001: https://docs.ogc.org/is/23-001/23-001.html

import type { SWEDataComponent } from '../swecommon/types.js';

// Process base types
export type SensorMLProcess =
  | PhysicalSystem
  | PhysicalComponent
  | SimpleProcess
  | AggregateProcess;

export interface PhysicalSystem {
  type: 'PhysicalSystem';
  id: string;
  description?: string;
  identifier?: string;
  classification?: Classification[];
  validTime?: TimeInterval;
  capabilities?: CapabilityList[];
  characteristics?: CharacteristicList[];
  contacts?: Contact[];
  documentation?: Documentation[];
  history?: Event[];
  components?: ComponentList[]; // Nested systems
  connections?: ConnectionList[]; // Component connections
  modes?: ModeList[]; // Operating modes
  position?: Position; // Location/orientation
}

export interface PhysicalComponent {
  type: 'PhysicalComponent';
  id: string;
  description?: string;
  identifier?: string;
  classification?: Classification[];
  validTime?: TimeInterval;
  capabilities?: CapabilityList[];
  characteristics?: CharacteristicList[];
  position?: Position;
}

// Capability/Characteristic structures
export interface CapabilityList {
  name: string;
  label?: string;
  capabilities: Capability[];
}

export interface Capability {
  name: string;
  label?: string;
  description?: string;
  definition?: string;
  value: SWEDataComponent; // Links to SWE Common types
}

export interface CharacteristicList {
  name: string;
  label?: string;
  characteristics: Characteristic[];
}

export interface Characteristic {
  name: string;
  label?: string;
  description?: string;
  definition?: string;
  value: SWEDataComponent; // Links to SWE Common types
}

// Component structures
export interface ComponentList {
  name: string;
  label?: string;
  components: Component[];
}

export interface Component {
  name: string;
  label?: string;
  href?: string; // Reference to external component
  role?: string;
  process?: SensorMLProcess; // Inline component definition
}

// ... 30+ more interfaces for complete SensorML schema
// (Classification, TimeInterval, Contact, Documentation, Event,
//  ConnectionList, ModeList, Position, InputList, OutputList,
//  ParameterList, ProcessMethod, etc.)
```

**Why These Types Matter:**

1. **IntelliSense:** Full autocomplete for nested SensorML structures
2. **Type Safety:** Compiler catches errors when accessing properties
3. **Documentation:** Interface comments serve as inline documentation
4. **Validation:** Types guide parser implementation
5. **Integration:** SWE Common types integrated via `SWEDataComponent`

#### SWE Common 3.0 Types (~600-800 lines)

**Key Interfaces:**

```typescript
// formats/swecommon/types.ts
// Based on OGC 23-002: https://docs.ogc.org/is/23-002/23-002.html

// Data component base types
export type SWEDataComponent =
  | DataRecord
  | DataArray
  | Vector
  | DataChoice
  | Quantity
  | Count
  | Boolean
  | Text
  | Category
  | Time
  | QuantityRange
  | CountRange
  | TimeRange
  | CategoryRange;

export interface DataRecord {
  type: 'DataRecord';
  id?: string;
  label?: string;
  description?: string;
  definition?: string;
  fields: DataField[];
}

export interface DataField {
  name: string;
  label?: string;
  component: SWEDataComponent; // Recursive structure
}

export interface DataArray {
  type: 'DataArray';
  id?: string;
  label?: string;
  description?: string;
  definition?: string;
  elementType: SWEDataComponent;
  elementCount?: Count | QuantityRange;
  values?: EncodedValues;
  encoding?: DataEncoding;
}

export interface Quantity {
  type: 'Quantity';
  id?: string;
  label?: string;
  description?: string;
  definition?: string;
  uom: UnitOfMeasure; // Unit of measure
  constraint?: AllowedValues; // Value constraints
  quality?: Quality[]; // Quality indicators
  nilValues?: NilValues[]; // Missing data representation
  value?: number;
}

// Unit of measure
export interface UnitOfMeasure {
  code?: string; // UCUM code (e.g., "m/s", "degC")
  href?: string; // URI to unit definition
}

// Encoding types
export type DataEncoding = JSONEncoding | TextEncoding | BinaryEncoding;

export interface TextEncoding {
  type: 'TextEncoding';
  tokenSeparator: string; // e.g., ","
  blockSeparator: string; // e.g., "\n"
  decimalSeparator?: string; // e.g., "."
  collapseWhiteSpaces?: boolean;
}

export interface BinaryEncoding {
  type: 'BinaryEncoding';
  byteOrder: 'bigEndian' | 'littleEndian';
  byteEncoding: 'base64' | 'raw';
  byteLength?: number;
  members: BinaryMember[];
}

export interface BinaryMember {
  name: string;
  dataType: 'int' | 'float' | 'double' | 'string' | 'boolean';
  byteLength?: number;
}

// ... 20+ more interfaces for complete SWE Common schema
// (Vector, DataChoice, Category, Time, QuantityRange, CountRange,
//  TimeRange, CategoryRange, AllowedValues, AllowedTokens, Quality,
//  NilValues, EncodedValues, etc.)
```

**Why These Types Matter:**

1. **Schema Validation:** DataRecord/DataArray define observation structure
2. **Encoding Support:** Types for JSON/Text/Binary encodings
3. **Unit Safety:** Type-safe unit of measure handling
4. **Quality Indicators:** Built-in quality/constraint types
5. **Parser Guidance:** Types drive parser implementation

#### Type Organization Summary

| Location                     | Lines           | Purpose                      |
| ---------------------------- | --------------- | ---------------------------- |
| `model.ts`                   | 350-400         | GeoJSON-based resource types |
| `formats/sensorml/types.ts`  | 800-1,200       | SensorML 3.0 interfaces      |
| `formats/swecommon/types.ts` | 600-800         | SWE Common 3.0 interfaces    |
| **TOTAL**                    | **1,750-2,400** | **Complete type system**     |

**Why Format-Specific Type Files:**

1. ✅ **User mandate** - Full typing required for all formats
2. ✅ **Professional standard** - AWS, Google, Stripe all type everything
3. ✅ **Developer experience** - IntelliSense for SensorML/SWE objects
4. ✅ **Size justification** - 1,400-2,000 lines warrants separate files
5. ✅ **Tree-shaking** - Users can exclude if not needed
6. ✅ **Maintainability** - Format types isolated from core types

**Integration Pattern:**

```typescript
// SensorML Capability uses SWE Common DataComponent
export interface Capability {
  name: string;
  value: SWEDataComponent; // Type from swecommon/types.ts
}

// This integration provides seamless type flow from
// SensorML → SWE Common → JavaScript values
```

**Confidence:** ⭐⭐⭐⭐⭐ (5/5) - User mandate + industry standard

**References:**

- [Architecture Decision - Part 2: Type System](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/design/csapiquerybuilder/architecture-decision/results/DECISION-part2-implementation.md#decision-3-typescript-type-system) - Complete type definitions with all interfaces
- [OGC SensorML 3.0](https://docs.ogc.org/is/23-000/23-000.html) - Official SensorML specification
- [OGC SWE Common 3.0](https://docs.ogc.org/is/24-014/24-014.html) - Official SWE Common specification

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

## Developer Experience

This section demonstrates the complete developer experience when using the CSAPI implementation, from initial connection through complex workflows.

### API Surface

**Single Entry Point Pattern:**

```typescript
import { OgcApiEndpoint, CSAPIQueryBuilder } from '@camptocamp/ogc-client';

// 1. Connect to endpoint
const endpoint = await OgcApiEndpoint.fromUrl('https://api.example.com/csapi');

// 2. Check conformance
const hasCSAPI = await endpoint.hasConnectedSystems; // true/false

// 3. List available collections
const collections = await endpoint.csapiCollections; // ['sensors', 'stations', ...]

// 4. Get builder for collection
const builder: CSAPIQueryBuilder = await endpoint.csapi('sensors');

// 5. Check available resources (automatic validation)
console.log(builder.availableResources);
// Set { 'systems', 'deployments', 'datastreams', 'observations' }

// 6. Use builder methods (with automatic validation)
try {
  const systemsUrl = await builder.getSystems({ limit: 10 });
  const systemUrl = await builder.getSystem('sensor-123');
  const historyUrl = await builder.getSystemHistory('sensor-123', {
    datetime: { start: new Date('2024-01-01'), end: new Date('2024-12-31') },
  });
} catch (error) {
  // Fail-fast with clear error if resource unavailable
  console.error(error.message);
}
```

---

### Type-Safe Usage

**GeoJSON Resource Types with Full IntelliSense:**

```typescript
import type {
  System,
  SystemCollection,
  Deployment,
  Datastream
} from '@camptocamp/ogc-client';

// Fetch and parse GeoJSON
const systemsUrl = await builder.getSystems({ limit: 10, bbox: [...] });
const response = await fetch(systemsUrl);
const systems: SystemCollection = await response.json();

// Type-safe property access with full IntelliSense
systems.features.forEach((system: System) => {
  // ✅ TypeScript knows all properties
  console.log(system.id);                      // string
  console.log(system.type);                    // 'System'
  console.log(system.properties.name);         // string
  console.log(system.properties.description);  // string | undefined
  console.log(system.properties.validTime);    // TimeInterval | undefined
  console.log(system.geometry?.coordinates);   // number[] | undefined
  console.log(system.links);                   // ResourceLink[]

  // ✅ TypeScript catches errors at compile time
  // console.log(system.properties.invalid);   // ❌ Compile error

  // ✅ Safe navigation with optional chaining
  const startTime = system.properties.validTime?.start;
  const longitude = system.geometry?.coordinates?.[0];
});

// Multi-resource workflows with type safety
const deployment: Deployment = await fetchDeployment(deploymentId);
const datastream: Datastream = await fetchDatastream(deployment.properties.systemIds[0]);
console.log(datastream.properties.observedPropertyId); // ✅ Full type safety
```

---

### Format Parser Integration

**SensorML 3.0 with Type Safety:**

```typescript
import { parseSensorML30 } from '@camptocamp/ogc-client/csapi/formats/sensorml';
import type {
  PhysicalSystem,
  Capability,
} from '@camptocamp/ogc-client/csapi/formats/sensorml';

// Fetch SensorML 3.0 format
const smlUrl = await builder.getSystem('sensor-123', { f: 'sml' });
const smlResponse = await fetch(smlUrl);
const smlJson = await smlResponse.json();
const system: PhysicalSystem = parseSensorML30(smlJson);

// Type-safe SensorML access with full IntelliSense
console.log(system.type); // 'PhysicalSystem'
console.log(system.description); // string | undefined
console.log(system.classification); // Classification[] | undefined
console.log(system.capabilities); // CapabilityList[] | undefined
console.log(system.components); // ComponentList[] | undefined

// Navigate nested structures safely
system.capabilities?.forEach((capList) => {
  capList.capabilities.forEach((cap: Capability) => {
    console.log(cap.name); // string
    console.log(cap.definition); // string | undefined
    console.log(cap.value.type); // 'Quantity' | 'Count' | ...

    // ✅ TypeScript narrows types based on discriminator
    if (cap.value.type === 'Quantity') {
      console.log(cap.value.uom.code); // UCUM code (e.g., "m/s")
      console.log(cap.value.value); // number | undefined
    }
  });
});

// Access nested components (recursive structure)
system.components?.forEach((compList) => {
  compList.components.forEach((comp) => {
    if (comp.process?.type === 'PhysicalSystem') {
      // ✅ Recursive type safety for nested systems
      console.log(comp.process.components); // ComponentList[] | undefined
    }
  });
});
```

**SWE Common 3.0 with Type Safety:**

```typescript
import { parseSWEDataRecord } from '@camptocamp/ogc-client/csapi/formats/swecommon';
import type {
  DataRecord,
  Quantity,
  DataArray,
} from '@camptocamp/ogc-client/csapi/formats/swecommon';

// Fetch SWE Common schema
const schemaUrl = await builder.getDatastreamSchema('ds-456');
const schemaResponse = await fetch(schemaUrl);
const schemaJson = await schemaResponse.json();
const schema: DataRecord = parseSWEDataRecord(schemaJson);

// Type-safe SWE Common access
schema.fields.forEach((field) => {
  console.log(field.name); // string
  console.log(field.component.type); // 'Quantity' | 'Count' | ...

  // ✅ Type narrowing based on discriminator
  if (field.component.type === 'Quantity') {
    const quantity = field.component as Quantity;
    console.log(quantity.uom.code); // UCUM code
    console.log(quantity.constraint); // AllowedValues | undefined
    console.log(quantity.quality); // Quality[] | undefined
  }

  if (field.component.type === 'DataArray') {
    const array = field.component as DataArray;
    console.log(array.elementType.type); // Element type
    console.log(array.encoding?.type); // 'JSON' | 'Text' | 'Binary'
  }
});

// Parse observation results using schema
const obsUrl = await builder.getObservations('ds-456', {
  phenomenonTime: '2024-01-01/2024-01-31',
  limit: 100,
});
const obsResponse = await fetch(obsUrl);
const observations = await obsResponse.json();

observations.features.forEach((obs) => {
  // Result structure validated against schema
  const result = obs.properties.result;
  // ✅ Access with type safety based on schema
});
```

---

### Error Handling Patterns

**Resource Validation Errors:**

```typescript
import { OgcApiEndpoint, EndpointError } from '@camptocamp/ogc-client';

const endpoint = await OgcApiEndpoint.fromUrl('https://api.example.com');
const builder = await endpoint.csapi('weather-stations');

// Automatic resource validation before URL building
try {
  const url = await builder.getSystems();
  // If 'systems' not available, exception thrown before network call
} catch (error) {
  if (error instanceof EndpointError) {
    // Clear, actionable error message
    console.error(error.message);
    // "Collection 'weather-stations' does not support 'systems' resource.
    //  Available resources: datastreams, observations"

    // Programmatic access to available resources
    console.log(builder.availableResources);
    // Set { 'datastreams', 'observations' }
  }
}
```

**Network Errors:**

```typescript
try {
  const url = await builder.getObservations('ds-123', {
    phenomenonTime: '2024-01-01/2024-01-31',
  });
  const response = await fetch(url);

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
  }

  const observations = await response.json();
} catch (error) {
  console.error('Failed to fetch observations:', error.message);
}
```

**Format Parsing Errors:**

```typescript
import {
  parseSensorML30,
  SensorMLParseError,
} from '@camptocamp/ogc-client/csapi/formats/sensorml';

try {
  const smlUrl = await builder.getSystem('sys-123', { f: 'sml' });
  const response = await fetch(smlUrl);
  const smlJson = await response.json();
  const system = parseSensorML30(smlJson);
} catch (error) {
  if (error instanceof SensorMLParseError) {
    console.error('Invalid SensorML document:', error.message);
    console.error('At path:', error.path);
  }
}
```

**Best Practices:**

1. ✅ **Check conformance first:** `endpoint.hasConnectedSystems`
2. ✅ **Check available resources:** `builder.availableResources`
3. ✅ **Let validation fail-fast:** Don't manually check before calling methods
4. ✅ **Handle specific error types:** `EndpointError`, `SensorMLParseError`, etc.
5. ✅ **Use TypeScript:** Catch type errors at compile time
6. ✅ **Log clear errors:** Include context (collection ID, resource type)

---

## Real-World Usage Scenarios

**Research-validated scenarios showing how CSAPI will actually be used in production applications.**

This section demonstrates complete workflows that developers will implement using the CSAPI client library. These scenarios are derived from Research Plan 14 (Usage Scenarios) which analyzed 15 real-world use cases and found that **100% require multi-resource workflows**. The scenarios validate the single-class architecture by showing that every practical use case requires seamless navigation across multiple resource types.

### Scenario 1: Real-Time Temperature Monitoring

**Priority:** P0 (Critical)  
**Resources Used:** Systems, DataStreams, Observations (3 resource types)  
**Complexity:** Medium

**Use Case:**  
A weather monitoring application needs to discover all temperature sensors in a region and display real-time temperature readings on a dashboard. The application must handle hierarchical system structures where sensors may be nested within stations.

**Implementation:**

```typescript
import { OgcApiEndpoint } from '@camptocamp/ogc-client';

async function monitorTemperatures(
  endpointUrl: string,
  bbox: [number, number, number, number]
): Promise<void> {
  // 1. Connect to CSAPI endpoint
  const endpoint = await OgcApiEndpoint.fromUrl(endpointUrl);
  if (!(await endpoint.hasConnectedSystems)) {
    throw new Error('Endpoint does not support Connected Systems API');
  }

  // 2. Get CSAPI client
  const client = await endpoint.csapi('weather-sensors');

  // 3. Discover all temperature-capable systems in region
  const systemsUrl = await client.getSystems({
    bbox: bbox,
    observedProperty: 'temperature',
    limit: 50,
  });
  const systemsResponse = await fetch(systemsUrl);
  const systems = await systemsResponse.json();

  console.log(`Found ${systems.features.length} temperature sensors`);

  // 4. For each system, get temperature datastreams and latest observations
  for (const system of systems.features) {
    // Get system's temperature datastreams
    const dsUrl = await client.getSystemDataStreams(system.id, {
      observedProperty: 'temperature',
    });
    const dsResponse = await fetch(dsUrl);
    const datastreams = await dsResponse.json();

    // For each datastream, get latest observation
    for (const ds of datastreams.features) {
      const obsUrl = await client.getDataStreamObservations(ds.id, {
        resultTime: 'latest',
        limit: 1,
      });
      const obsResponse = await fetch(obsUrl);
      const observations = await obsResponse.json();

      if (observations.features.length > 0) {
        const obs = observations.features[0];
        console.log(
          `${system.properties.name} - ${ds.properties.name}: ` +
            `${obs.properties.result} ${ds.properties.unitOfMeasurement.symbol}`
        );

        // Update dashboard UI
        updateDashboard(
          system.id,
          obs.properties.result,
          obs.properties.phenomenonTime
        );
      }
    }
  }
}

// Usage
monitorTemperatures('https://api.weather.com/csapi', [-122, 37, -121, 38]);
```

**Why Single-Class Works:**

- ✅ All methods on same `client` object - no builder switching
- ✅ Natural workflow: Systems → DataStreams → Observations
- ✅ Type-safe throughout (no casting needed)
- ✅ Clear method names (`getSystemDataStreams`, `getDataStreamObservations`)

**Alternative Multi-Class Would Require:**

- ❌ Switch from `SystemsBuilder` → `DatastreamsBuilder` → `ObservationsBuilder`
- ❌ Unclear how to navigate between builders
- ❌ Must filter datastreams by `system` parameter (inefficient)
- ❌ Context lost at each builder boundary

**Scenario Metrics:**

- Resources accessed: 3 (Systems, DataStreams, Observations)
- API calls: 1 + N + M (1 systems, N datastreams, M observations)
- Lines of code: ~45 lines
- Builder switches (multi-class): 2 per system (vs 0 in single-class)

---

### Scenario 2: Remote System Control and Tasking

**Priority:** P0 (Critical)  
**Resources Used:** Systems, ControlStreams, Commands, Status (4 resource types)  
**Complexity:** High

**Use Case:**  
A UAV fleet management system needs to send flight commands to specific UAVs, track command execution status, and retrieve resulting observation data. This requires navigating from System identification through command issuance to result retrieval.

**Implementation:**

```typescript
import { OgcApiEndpoint } from '@camptocamp/ogc-client';

async function taskUAV(
  endpointUrl: string,
  uavId: string,
  missionParams: {
    altitude: number;
    speed: number;
    waypoints: [number, number][];
  }
): Promise<void> {
  const endpoint = await OgcApiEndpoint.fromUrl(endpointUrl);
  const client = await endpoint.csapi('uav-fleet');

  // 1. Verify UAV system exists and supports commands
  const systemUrl = await client.getSystem(uavId);
  const systemResponse = await fetch(systemUrl);
  const uav = await systemResponse.json();
  console.log(`Tasking ${uav.properties.name}...`);

  // 2. Get flight control stream for UAV
  const controlStreamsUrl = await client.getSystemControlStreams(uavId, {
    controlledProperty: 'flight-control',
  });
  const csResponse = await fetch(controlStreamsUrl);
  const controlStreams = await csResponse.json();

  if (controlStreams.features.length === 0) {
    throw new Error(`UAV ${uavId} does not support flight control`);
  }

  const controlStream = controlStreams.features[0];

  // 3. Check command feasibility before issuing
  const feasibilityUrl = await client.checkCommandFeasibility(
    controlStream.id,
    {
      parameters: missionParams,
    }
  );
  const feasibilityResponse = await fetch(feasibilityUrl, { method: 'POST' });
  const feasibility = await feasibilityResponse.json();

  if (!feasibility.feasible) {
    throw new Error(`Mission not feasible: ${feasibility.reason}`);
  }

  // 4. Issue flight command
  const commandUrl = await client.createCommand(controlStream.id, {
    parameters: missionParams,
  });
  const commandResponse = await fetch(commandUrl, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ parameters: missionParams }),
  });
  const command = await commandResponse.json();

  console.log(`Command ${command.id} issued, tracking status...`);

  // 5. Poll command status until completion
  let status;
  let attempts = 0;
  const maxAttempts = 60; // 5 minutes

  while (attempts < maxAttempts) {
    const statusUrl = await client.getCommandStatus(command.id);
    const statusResponse = await fetch(statusUrl);
    status = await statusResponse.json();

    console.log(`Status: ${status.state} (attempt ${attempts + 1})`);

    if (status.state === 'completed') {
      console.log('Mission completed successfully');
      break;
    } else if (status.state === 'failed') {
      throw new Error(`Mission failed: ${status.errorMessage}`);
    }

    await new Promise((resolve) => setTimeout(resolve, 5000)); // Poll every 5s
    attempts++;
  }

  // 6. Retrieve command result (telemetry datastream)
  if (status.state === 'completed' && status.resultDatastream) {
    const resultUrl = await client.getCommandResult(command.id);
    const resultResponse = await fetch(resultUrl);
    const telemetry = await resultResponse.json();

    console.log(
      `Telemetry collected: ${telemetry.features.length} observations`
    );
    processTelemetry(telemetry);
  }
}

// Usage
taskUAV('https://api.uav-fleet.com/csapi', 'uav-007', {
  altitude: 500,
  speed: 15,
  waypoints: [
    [-122.5, 37.7],
    [-122.4, 37.8],
    [-122.5, 37.9],
  ],
});
```

**Why Single-Class Works:**

- ✅ Seamless navigation: System → ControlStream → Command → Status → Result
- ✅ All on same `client` object throughout workflow
- ✅ Clear progression through command lifecycle
- ✅ No type casting or builder management

**Alternative Multi-Class Would Require:**

- ❌ Navigate: `SystemsBuilder` → `ControlStreamsBuilder` → `CommandsBuilder` → `StatusBuilder` → `ResultBuilder`
- ❌ 4 builder switches in single workflow
- ❌ Circular dependencies between all 5 builder classes
- ❌ Context management complexity (carry IDs between builders)

**Scenario Metrics:**

- Resources accessed: 4 (Systems, ControlStreams, Commands, Status/Result)
- API calls: 6+ (1 system, 1 control stream, 1 feasibility, 1 command, N status, 1 result)
- Lines of code: ~75 lines
- Builder switches (multi-class): 4 (vs 0 in single-class)

---

### Scenario 3: Historical Data Analysis

**Priority:** P0 (Critical)  
**Resources Used:** Systems, DataStreams, Observations (3 resource types)  
**Complexity:** Medium

**Use Case:**  
A climate researcher needs to analyze historical temperature data from multiple sensors over a 1-year period, aggregating observations for statistical analysis and trend detection.

**Implementation:**

```typescript
import { OgcApiEndpoint } from '@camptocamp/ogc-client';

async function analyzeHistoricalTemperatures(
  endpointUrl: string,
  region: [number, number, number, number],
  startDate: string,
  endDate: string
): Promise<void> {
  const endpoint = await OgcApiEndpoint.fromUrl(endpointUrl);
  const client = await endpoint.csapi('climate-stations');

  // 1. Find all temperature sensors in region
  const systemsUrl = await client.getSystems({
    bbox: region,
    observedProperty: 'temperature',
  });
  const systemsResponse = await fetch(systemsUrl);
  const systems = await systemsResponse.json();

  console.log(`Analyzing ${systems.features.length} climate stations...`);

  const allObservations: Observation[] = [];

  // 2. For each system, get temperature datastreams
  for (const system of systems.features) {
    const dsUrl = await client.getSystemDataStreams(system.id, {
      observedProperty: 'temperature',
    });
    const dsResponse = await fetch(dsUrl);
    const datastreams = await dsResponse.json();

    // 3. For each datastream, get historical observations
    for (const ds of datastreams.features) {
      // Use cursor-based pagination for large datasets
      let cursor = null;
      let hasMore = true;

      while (hasMore) {
        const obsUrl = await client.getDataStreamObservations(ds.id, {
          phenomenonTime: `${startDate}/${endDate}`,
          limit: 1000,
          cursor: cursor,
        });
        const obsResponse = await fetch(obsUrl);
        const observations = await obsResponse.json();

        allObservations.push(...observations.features);
        console.log(
          `Retrieved ${observations.features.length} observations from ${system.properties.name}`
        );

        // Check for more data
        const nextLink = observations.links.find((l) => l.rel === 'next');
        if (nextLink) {
          const url = new URL(nextLink.href);
          cursor = url.searchParams.get('cursor');
        } else {
          hasMore = false;
        }
      }
    }
  }

  // 4. Perform statistical analysis
  const temperatures = allObservations.map((obs) => obs.properties.result);
  const stats = {
    count: temperatures.length,
    mean: temperatures.reduce((a, b) => a + b, 0) / temperatures.length,
    min: Math.min(...temperatures),
    max: Math.max(...temperatures),
    std: calculateStdDev(temperatures),
  };

  console.log(`Analysis complete: ${stats.count} observations`);
  console.log(
    `Temperature range: ${stats.min}°C to ${
      stats.max
    }°C (mean: ${stats.mean.toFixed(2)}°C)`
  );

  return stats;
}

// Usage
analyzeHistoricalTemperatures(
  'https://api.climate-data.gov/csapi',
  [-125, 35, -115, 45], // Western US
  '2023-01-01',
  '2023-12-31'
);
```

**Why Single-Class Works:**

- ✅ Natural pagination workflow with cursor support
- ✅ Consistent method names across resources
- ✅ Clear parent-child relationships (system → datastream → observations)
- ✅ Type-safe aggregation across multiple sources

**Alternative Multi-Class Would Require:**

- ❌ Manage 3 builder types simultaneously
- ❌ Unclear pagination API across builder boundaries
- ❌ Context management for cursor state

**Scenario Metrics:**

- Resources accessed: 3 (Systems, DataStreams, Observations)
- API calls: 1 + N + M×P (1 systems, N datastreams, M datastreams × P pages)
- Dataset size: Potentially millions of observations
- Lines of code: ~60 lines
- Builder switches (multi-class): 2 per system (vs 0 in single-class)

---

### Scenario 4: System Deployment Tracking

**Priority:** P1 (Important)  
**Resources Used:** Deployments, Systems, SamplingFeatures, DataStreams (4-5 resource types)  
**Complexity:** Medium-High

**Use Case:**  
An ocean buoy network operator needs to track the deployment of new sensor packages, verify system connectivity, and begin data collection across the deployment network.

**Implementation:**

```typescript
import { OgcApiEndpoint } from '@camptocamp/ogc-client';

async function trackDeploymentNetwork(
  endpointUrl: string,
  deploymentId: string
): Promise<void> {
  const endpoint = await OgcApiEndpoint.fromUrl(endpointUrl);
  const client = await endpoint.csapi('ocean-sensors');

  // 1. Get deployment information
  const deploymentUrl = await client.getDeployment(deploymentId);
  const deploymentResponse = await fetch(deploymentUrl);
  const deployment = await deploymentResponse.json();

  console.log(`Tracking deployment: ${deployment.properties.name}`);
  console.log(`Deployed: ${deployment.properties.deploymentTime.start}`);

  // 2. Get all systems in deployment
  const systemsUrl = await client.getDeploymentSystems(deploymentId);
  const systemsResponse = await fetch(systemsUrl);
  const systems = await systemsResponse.json();

  console.log(`Deployment contains ${systems.features.length} systems`);

  const deploymentStatus = {
    totalSystems: systems.features.length,
    activeDatastreams: 0,
    samplingFeatures: new Set(),
    recentObservations: 0,
  };

  // 3. For each system, verify data collection
  for (const system of systems.features) {
    // Get system's sampling features (e.g., buoy locations)
    const sfUrl = await client.getSystemSamplingFeatures(system.id);
    const sfResponse = await fetch(sfUrl);
    const samplingFeatures = await sfResponse.json();

    samplingFeatures.features.forEach((sf) => {
      deploymentStatus.samplingFeatures.add(sf.id);
    });

    // Get system's datastreams
    const dsUrl = await client.getSystemDataStreams(system.id);
    const dsResponse = await fetch(dsUrl);
    const datastreams = await dsResponse.json();

    deploymentStatus.activeDatastreams += datastreams.features.length;

    // Check recent observations (last 24 hours)
    for (const ds of datastreams.features) {
      const yesterday = new Date(
        Date.now() - 24 * 60 * 60 * 1000
      ).toISOString();
      const obsUrl = await client.getDataStreamObservations(ds.id, {
        phenomenonTime: `${yesterday}/..`,
        limit: 1,
      });
      const obsResponse = await fetch(obsUrl);
      const observations = await obsResponse.json();

      if (observations.features.length > 0) {
        deploymentStatus.recentObservations++;
        console.log(
          `✓ ${system.properties.name} - ${ds.properties.name}: Active`
        );
      } else {
        console.log(
          `✗ ${system.properties.name} - ${ds.properties.name}: No recent data`
        );
      }
    }
  }

  // 4. Generate deployment health report
  console.log('\n=== Deployment Health Report ===');
  console.log(`Total Systems: ${deploymentStatus.totalSystems}`);
  console.log(`Sampling Features: ${deploymentStatus.samplingFeatures.size}`);
  console.log(`Active Datastreams: ${deploymentStatus.activeDatastreams}`);
  console.log(
    `Reporting (24h): ${deploymentStatus.recentObservations}/${deploymentStatus.activeDatastreams}`
  );

  const healthPercentage =
    (deploymentStatus.recentObservations / deploymentStatus.activeDatastreams) *
    100;
  console.log(`Network Health: ${healthPercentage.toFixed(1)}%`);
}

// Usage
trackDeploymentNetwork(
  'https://api.ocean-data.org/csapi',
  'atlantic-array-2024'
);
```

**Why Single-Class Works:**

- ✅ Complex navigation: Deployment → Systems → SamplingFeatures/DataStreams → Observations
- ✅ All relationships accessible from single client object
- ✅ No ambiguity about how to access related resources
- ✅ Type-safe across 5 resource types

**Alternative Multi-Class Would Require:**

- ❌ Navigate through 5 different builder classes
- ❌ Manage relationships across builder boundaries
- ❌ Unclear how to get from Deployment to Systems to DataStreams

**Scenario Metrics:**

- Resources accessed: 5 (Deployments, Systems, SamplingFeatures, DataStreams, Observations)
- API calls: 1 + 1 + N×(2 + M) (deployment, systems, N systems × (SF + DS), M datastreams)
- Complexity: High (multi-resource health check)
- Lines of code: ~80 lines
- Builder switches (multi-class): 4 per system (vs 0 in single-class)

---

### Scenario 5: Dashboard Data Aggregation

**Priority:** P0 (Critical)  
**Resources Used:** Systems, DataStreams, Observations (3 resource types, scaled)  
**Complexity:** High (performance-critical)

**Use Case:**  
A smart city dashboard needs to display real-time data from hundreds of sensors across multiple systems (weather, traffic, air quality, noise). The application must efficiently aggregate data from 50+ datastreams with minimal API calls.

**Implementation:**

```typescript
import { OgcApiEndpoint } from '@camptocamp/ogc-client';

async function buildCityDashboard(
  endpointUrl: string,
  cityBounds: [number, number, number, number]
): Promise<DashboardData> {
  const endpoint = await OgcApiEndpoint.fromUrl(endpointUrl);
  const client = await endpoint.csapi('smart-city-sensors');

  const dashboard: DashboardData = {
    weather: [],
    traffic: [],
    airQuality: [],
    noise: [],
  };

  // 1. Discover all systems in city bounds
  const systemsUrl = await client.getSystems({
    bbox: cityBounds,
    limit: 100,
  });
  const systemsResponse = await fetch(systemsUrl);
  const systems = await systemsResponse.json();

  console.log(`Processing ${systems.features.length} sensor systems...`);

  // 2. Build category-to-property mapping
  const propertyCategories = {
    weather: ['temperature', 'humidity', 'pressure', 'windSpeed'],
    traffic: ['vehicleCount', 'averageSpeed', 'congestionLevel'],
    airQuality: ['pm25', 'pm10', 'no2', 'co', 'o3'],
    noise: ['soundLevel', 'noiseFrequency'],
  };

  // 3. For each system, get categorized datastreams and latest observations
  const promises = systems.features.map(async (system) => {
    const dsUrl = await client.getSystemDataStreams(system.id);
    const dsResponse = await fetch(dsUrl);
    const datastreams = await dsResponse.json();

    // Group datastreams by category
    for (const ds of datastreams.features) {
      const property = ds.properties.observedPropertyId;

      // Determine category
      let category = null;
      for (const [cat, props] of Object.entries(propertyCategories)) {
        if (props.some((p) => property.includes(p))) {
          category = cat;
          break;
        }
      }

      if (!category) continue;

      // Get latest observation for this datastream
      const obsUrl = await client.getDataStreamObservations(ds.id, {
        resultTime: 'latest',
        limit: 1,
      });
      const obsResponse = await fetch(obsUrl);
      const observations = await obsResponse.json();

      if (observations.features.length > 0) {
        const obs = observations.features[0];
        dashboard[category].push({
          systemName: system.properties.name,
          datastreamName: ds.properties.name,
          value: obs.properties.result,
          unit: ds.properties.unitOfMeasurement?.symbol,
          timestamp: obs.properties.phenomenonTime,
          location: system.geometry?.coordinates,
        });
      }
    }
  });

  // 4. Execute all requests in parallel for performance
  await Promise.all(promises);

  // 5. Calculate aggregates per category
  const aggregates = {
    weather: calculateAggregates(dashboard.weather),
    traffic: calculateAggregates(dashboard.traffic),
    airQuality: calculateAggregates(dashboard.airQuality),
    noise: calculateAggregates(dashboard.noise),
  };

  console.log('\n=== City Dashboard Summary ===');
  console.log(`Weather sensors: ${dashboard.weather.length}`);
  console.log(`Traffic sensors: ${dashboard.traffic.length}`);
  console.log(`Air quality sensors: ${dashboard.airQuality.length}`);
  console.log(`Noise sensors: ${dashboard.noise.length}`);
  console.log(
    `\nAvg temperature: ${aggregates.weather.temperature?.mean.toFixed(1)}°C`
  );
  console.log(
    `Avg traffic speed: ${aggregates.traffic.averageSpeed?.mean.toFixed(
      1
    )} km/h`
  );
  console.log(
    `Avg PM2.5: ${aggregates.airQuality.pm25?.mean.toFixed(1)} μg/m³`
  );

  return { dashboard, aggregates };
}

// Usage
buildCityDashboard(
  'https://api.smartcity.gov/csapi',
  [-122.5, 37.7, -122.3, 37.9]
);
```

**Why Single-Class Works:**

- ✅ Parallel processing with same client object
- ✅ Consistent API across all sensor types
- ✅ Type-safe aggregation across heterogeneous data
- ✅ Clear performance characteristics

**Alternative Multi-Class Would Require:**

- ❌ Manage multiple builder instances simultaneously
- ❌ Coordinate parallel requests across builder boundaries
- ❌ Complex type casting for aggregation

**Scenario Metrics:**

- Resources accessed: 3 (Systems, DataStreams, Observations)
- API calls: 1 + N×2 (1 systems, N systems × (datastreams + observations))
- Scale: 100+ systems, 200+ datastreams, 200+ observations
- Performance: Parallel execution critical
- Lines of code: ~100 lines
- Builder switches (multi-class): 2 per system × 100 = 200 (vs 0 in single-class)

---

### Scenario Complexity Analysis

**Evidence Summary from 5 Representative Scenarios:**

| Scenario               | Priority | Resources | API Calls   | Complexity  | Builder Switches (Multi-Class) |
| ---------------------- | -------- | --------- | ----------- | ----------- | ------------------------------ |
| Temperature Monitoring | P0       | 3         | 1 + N + M   | Medium      | 2 per system                   |
| UAV Command & Control  | P0       | 4         | 6+          | High        | 4 per workflow                 |
| Historical Analysis    | P0       | 3         | 1 + N + M×P | Medium      | 2 per system                   |
| Deployment Tracking    | P1       | 5         | Complex     | Medium-High | 4 per system                   |
| Dashboard Aggregation  | P0       | 3         | 1 + N×2     | High        | 200+ total                     |

**Key Findings:**

1. **100% Multi-Resource Workflows** - All 5 scenarios require accessing multiple resource types
2. **Average 3.4 Resources Per Scenario** - Range from 3 to 5 resource types
3. **Navigation Complexity** - Every scenario navigates across resource boundaries multiple times
4. **Single-Class Advantage** - Zero builder switches vs 4-200 in multi-class alternative
5. **Performance Critical** - Parallel execution and consistent API essential for scalability

**Validation Verdict:**

✅ **Single-class architecture naturally supports all real-world scenarios**  
✅ **Multi-resource workflows are the norm, not the exception**  
✅ **Seamless navigation across resource boundaries is essential**  
✅ **Alternative multi-class design would fragment every workflow**

**Confidence:** ⭐⭐⭐⭐⭐ (5/5) - Real-world scenarios provide conclusive evidence for single-class architecture

**References:**

- [Architecture Decision - Part 3: Usage Scenario Validation](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/design/csapiquerybuilder/architecture-decision/results/DECISION-part3-validation.md#decision-1-usage-scenario-validation) - Complete analysis of all 15 scenarios
- [Research Plan 14](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/design/csapiquerybuilder/research-plan-14-usage-scenarios.md) - Original usage scenario research with P0/P1/P2 prioritization

---

## Implementation Roadmap

This section provides a complete, actionable roadmap for implementing CSAPI support in the correct order with complexity ratings and time estimates.

### Phase 1: Core Structure (LOW COMPLEXITY)

**Estimated Time:** 4-6 hours  
**Prerequisites:** None  
**Goal:** Set up basic structure and integration

**Tasks:**

- [ ] **Create model.ts** (~350-400 lines, 2-3 hours)
  - [ ] Define CSAPIResourceTypes enum (12 lines)
  - [ ] Define QueryOptions interfaces (40 lines)
  - [ ] Define helper types (TimeInterval, ResourceLink, etc.) (40 lines)
  - [ ] Define all 9 resource interfaces (225 lines)
  - [ ] Define collection types (35 lines)
  - [ ] Import from three tiers (shared, ogc-api, geojson)
- [ ] **Create helpers.ts** (~50-80 lines, 1 hour)
  - [ ] Implement URL encoding helpers
  - [ ] Implement temporal parsing utilities
  - [ ] Implement validation utilities
- [ ] **Add integration code to endpoint.ts** (+35 lines, 1 hour)
  - [ ] Import CSAPIQueryBuilder (1 line)
  - [ ] Add cache field (2 lines)
  - [ ] Add csapiCollections getter (6 lines)
  - [ ] Add hasConnectedSystems getter (6 lines)
  - [ ] Add csapi() factory method (17 lines)
  - [ ] Update import statement (3 lines)
- [ ] **Add conformance check to info.ts** (+12 lines, 30 minutes)
  - [ ] Implement checkHasConnectedSystems function
  - [ ] Check both Part 1 and Part 2 conformance classes
- [ ] **Add exports to index.ts** (+17 lines, 30 minutes)
  - [ ] Export CSAPIQueryBuilder class
  - [ ] Export all type interfaces

**Validation:**

- [ ] TypeScript compiles without errors
- [ ] All imports resolve correctly
- [ ] Factory method instantiates builder
- [ ] Conformance checking works with test fixture

---

### Phase 2: QueryBuilder (MEDIUM COMPLEXITY)

**Estimated Time:** 12-16 hours  
**Prerequisites:** Phase 1 complete  
**Goal:** Implement all URL-building methods with validation

**Tasks:**

- [ ] **Create url_builder.ts skeleton** (~100 lines, 1 hour)
  - [ ] Class structure with constructor
  - [ ] Private fields (collection, baseUrl)
  - [ ] Public field (availableResources)
- [ ] **Implement helper methods** (~50-80 lines, 2 hours)
  - [ ] buildResourceUrl() - Core URL construction (30-40 lines)
  - [ ] buildQueryString() - Parameter serialization (20-30 lines)
  - [ ] extractAvailableResources() - Resource discovery (10-15 lines)
- [ ] **Implement Part 1 methods** (~400-500 lines, 5-6 hours)
  - [ ] Systems methods (12 methods, ~120 lines)
    - [ ] getSystems, getSystem, createSystem, updateSystem, deleteSystem
    - [ ] getSubsystems, createSubsystem, getSystemHistory
    - [ ] getSystemDatastreams, getSystemSamplingFeatures
    - [ ] getSystemProcedures, getSystemDeployments
  - [ ] Deployments methods (8 methods, ~80 lines)
  - [ ] Procedures methods (8 methods, ~80 lines)
  - [ ] Sampling Features methods (8 methods, ~80 lines)
  - [ ] Properties methods (6 methods, ~60 lines)
- [ ] **Implement Part 2 methods** (~400-500 lines, 5-6 hours)
  - [ ] Datastreams methods (11 methods, ~110 lines)
  - [ ] Observations methods (9 methods, ~90 lines)
  - [ ] Control Streams methods (8 methods, ~80 lines)
  - [ ] Commands methods (10 methods, ~100 lines)
    - [ ] getCommands, getCommand, createCommand
    - [ ] getCommandStatus, getCommandResult
    - [ ] cancelCommand, pauseCommand, resumeCommand
    - [ ] checkFeasibility, bulkCreateCommands

**Validation:**

- [ ] All methods build correct URLs
- [ ] Query parameters serialized correctly
- [ ] Resource validation throws correct errors
- [ ] Nested endpoint URLs correct
- [ ] Schema/status endpoint URLs correct

---

### Phase 3: Format Parsers (HIGH COMPLEXITY)

**Estimated Time:** 20-30 hours  
**Prerequisites:** Phase 2 complete  
**Goal:** Implement all format parsers with full type support

**Tasks:**

- [ ] **Create formats/ infrastructure** (~150-300 lines, 2-3 hours)
  - [ ] Create formats/constants.ts (~50-100 lines)
    - [ ] Media type constants
    - [ ] Namespace URI constants
    - [ ] Vocabulary constants
  - [ ] Create formats/geojson.ts (~50-100 lines)
    - [ ] GeoJSON parsing utilities
    - [ ] CSAPI property extraction
  - [ ] Create formats/index.ts (~50-100 lines)
    - [ ] Barrel file for all parsers
    - [ ] Re-export types
- [ ] **Implement SensorML parsers** (~1,600-2,200 lines, 10-12 hours)
  - [ ] Create formats/sensorml/types.ts (~800-1,200 lines, 4-5 hours)
    - [ ] PhysicalSystem interface
    - [ ] PhysicalComponent interface
    - [ ] SimpleProcess/AggregateProcess interfaces
    - [ ] Capability/Characteristic interfaces
    - [ ] Component/Connection/Mode interfaces
    - [ ] 30+ supporting interfaces
  - [ ] Create formats/sensorml/parser.ts (~600-800 lines, 4-5 hours)
    - [ ] Main parser function
    - [ ] Recursive component parsing
    - [ ] Capability/characteristic parsing
    - [ ] Position/location parsing
  - [ ] Create formats/sensorml/simple-process.ts (~150-200 lines, 1 hour)
  - [ ] Create formats/sensorml/aggregate-process.ts (~200-250 lines, 1 hour)
  - [ ] Create formats/sensorml/physical-system.ts (~200-250 lines, 1 hour)
  - [ ] Create formats/sensorml/index.ts (~50-100 lines, 30 minutes)
- [ ] **Implement SWE Common parsers** (~1,600-2,250 lines, 10-12 hours)
  - [ ] Create formats/swecommon/types.ts (~600-800 lines, 3-4 hours)
    - [ ] DataComponent union type
    - [ ] DataRecord interface
    - [ ] DataArray interface
    - [ ] Quantity/Count/Text/Boolean interfaces
    - [ ] Encoding interfaces (JSON/Text/Binary)
    - [ ] 20+ supporting interfaces
  - [ ] Create formats/swecommon/parser.ts (~500-700 lines, 3-4 hours)
    - [ ] Main parser function
    - [ ] Component type discrimination
    - [ ] Encoding detection
    - [ ] Schema validation
  - [ ] Create formats/swecommon/data-record.ts (~150-200 lines, 1 hour)
  - [ ] Create formats/swecommon/data-array.ts (~200-250 lines, 1-2 hours)
  - [ ] Create formats/swecommon/components.ts (~300-400 lines, 2-3 hours)
  - [ ] Create formats/swecommon/index.ts (~50-100 lines, 30 minutes)

**Validation:**

- [ ] All SensorML examples parse correctly
- [ ] All SWE Common examples parse correctly
- [ ] Type discrimination works correctly
- [ ] Recursive structures parsed correctly
- [ ] Invalid documents throw clear errors
- [ ] Binary encoding decodes correctly

---

### Phase 4: Tests (MEDIUM-HIGH COMPLEXITY)

**Estimated Time:** 15-20 hours  
**Prerequisites:** Phases 1-3 complete  
**Goal:** Achieve >80% code coverage with comprehensive tests

**Tasks:**

- [ ] **Create model.spec.ts** (~200-300 lines, 2-3 hours)
  - [ ] Test all type definitions
  - [ ] Test query option interfaces
  - [ ] Test resource interfaces
  - [ ] Test collection types
- [ ] **Create url_builder.spec.ts** (~800-1,000 lines, 6-8 hours)
  - [ ] Test constructor and initialization
  - [ ] Test resource discovery
  - [ ] Test all Part 1 methods (40 methods × ~15 lines)
  - [ ] Test all Part 2 methods (38 methods × ~15 lines)
  - [ ] Test query parameter encoding
  - [ ] Test nested endpoint URLs
  - [ ] Test schema/status endpoints
  - [ ] Test error cases
  - [ ] Test resource validation
- [ ] **Create format parser tests** (~3,500-4,700 lines, 10-12 hours)
  - [ ] Test SensorML parser (~1,500-2,000 lines)
    - [ ] Test all system models
    - [ ] Test recursive component parsing
    - [ ] Test capability/characteristic parsing
    - [ ] Test invalid documents
    - [ ] Test edge cases
  - [ ] Test SWE Common parser (~1,500-2,000 lines)
    - [ ] Test all data component types
    - [ ] Test all encodings (JSON/Text/Binary)
    - [ ] Test constraint validation
    - [ ] Test invalid documents
    - [ ] Test edge cases
  - [ ] Test GeoJSON utilities (~300-400 lines)
  - [ ] Test format detector (~200-300 lines)

**Validation:**

- [ ] Code coverage >80%
- [ ] All tests pass
- [ ] Edge cases covered
- [ ] Error handling tested
- [ ] Integration tests pass

---

### Summary

**Total Estimated Time:** 51-72 hours (6-9 weeks calendar time)

| Phase                   | Complexity  | Time            | Lines             | Dependencies   |
| ----------------------- | ----------- | --------------- | ----------------- | -------------- |
| Phase 1: Core Structure | LOW         | 4-6 hours       | ~500-600          | None           |
| Phase 2: QueryBuilder   | MEDIUM      | 12-16 hours     | ~900-1,180        | Phase 1        |
| Phase 3: Format Parsers | HIGH        | 20-30 hours     | ~3,450-4,750      | Phase 2        |
| Phase 4: Tests          | MEDIUM-HIGH | 15-20 hours     | ~4,500-6,000      | Phases 1-3     |
| **TOTAL**               | **MIXED**   | **51-72 hours** | **~9,350-12,530** | **Sequential** |

**Complexity Distribution:**

- **Low Complexity:** 10 files (~600-800 lines, 4-6 hours)
- **Medium Complexity:** 4 files (~1,700-2,180 lines, 27-36 hours)
- **High Complexity:** 10 files (~7,050-9,550 lines, 20-30 hours)

**Recommended Implementation Order:**

1. ✅ **Phase 1 first** - Establishes foundation
2. ✅ **Phase 2 second** - Core functionality
3. ✅ **Phase 3 third** - Format support (can be parallelized if team > 1)
4. ✅ **Phase 4 last** - Validates everything

**Risk Mitigation:**

- Start with low complexity (Phase 1) to validate approach
- Implement core URL building (Phase 2) before complex parsers
- Test incrementally during each phase
- Use spec examples as test fixtures throughout

**Confidence:** ⭐⭐⭐⭐ (4/5) - Estimates based on similar upstream implementations (EDR, WFS)

**References:**

- [Architecture Decision - Part 2: Implementation Roadmap](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/design/csapiquerybuilder/architecture-decision/results/DECISION-part2-implementation.md#implementation-readiness) - Complete implementation checklist

---

## Code Volume Summary

**Research-Validated Estimates (from Architecture Decision Documents):**

### Implementation Files

| Category                  | Files  | Lines           | Complexity | Status                 |
| ------------------------- | ------ | --------------- | ---------- | ---------------------- |
| **Core Implementation**   | **3**  | **1,100-1,280** | **Medium** | **Structure complete** |
| url_builder.ts            | 1      | 700-800         | Medium     | 70-80 methods          |
| model.ts                  | 1      | 350-400         | Low        | Type definitions       |
| helpers.ts                | 1      | 50-80           | Low        | Utilities              |
| **Format Implementation** | **18** | **3,450-4,750** | **High**   | **Structure complete** |
| SensorML types            | 1      | 800-1,200       | Medium     | Interface definitions  |
| SensorML parsers          | 5      | 800-1,000       | High       | Recursive parsing      |
| SWE Common types          | 1      | 600-800         | Medium     | Interface definitions  |
| SWE Common parsers        | 5      | 1,000-1,250     | High       | Encoding support       |
| GeoJSON utilities         | 1      | 50-100          | Low        | Extensions             |
| Constants                 | 1      | 50-100          | Low        | Media types            |
| Index files               | 3      | 150-300         | Low        | Exports                |
| **Integration**           | **3**  | **64**          | **Low**    | **Pattern decided**    |
| endpoint.ts changes       | 1      | 35              | Low        | Factory method         |
| info.ts changes           | 1      | 12              | Low        | Conformance            |
| index.ts changes          | 1      | 17              | Low        | Exports                |
| **TOTAL IMPLEMENTATION**  | **24** | **4,614-6,094** | **Mixed**  | **Ready**              |

### Test Files

| Category        | Files  | Lines           | Complexity | Status            |
| --------------- | ------ | --------------- | ---------- | ----------------- |
| Core tests      | 2      | 1,000-1,300     | Medium     | Patterns complete |
| Format tests    | 15     | 3,500-4,700     | High       | Patterns complete |
| **TOTAL TESTS** | **17** | **4,500-6,000** | **High**   | **Ready**         |

### Grand Total

**Implementation:** 24 files, ~4,614-6,094 lines  
**Tests:** 17 files, ~4,500-6,000 lines  
**TOTAL:** 41 files, ~9,114-12,094 lines

**Comparison to Original Estimates:**

| Estimate             | Original (v2.0)      | Research-Validated (v3.0) | Difference |
| -------------------- | -------------------- | ------------------------- | ---------- |
| QueryBuilder         | ~10,000-14,000 lines | ~700-800 lines            | -93%       |
| Total Implementation | ~15,000-20,000 lines | ~4,614-6,094 lines        | -69%       |
| Total with Tests     | ~21,000-27,900 lines | ~9,114-12,094 lines       | -56%       |

**Why More Accurate:**

1. ✅ **Research-based** - Plans 11-13 analyzed exact requirements
2. ✅ **Component-level** - Counted each file individually
3. ✅ **Upstream comparison** - Compared to EDR/WFS implementations
4. ✅ **Format-separated** - Correctly attributed 76% to format parsers
5. ✅ **Helper methods** - Accounted for code reuse (~60-85%)

**Key Insights:**

1. **Format Parsers Dominate:** 76-78% of implementation is format parsing (justifies "why full format handling" section)
2. **Minimal Integration:** Only 64 lines modify existing files (upstream-friendly)
3. **Resource Validation:** ~140-160 lines (~3% of total) for significant UX improvement
4. **Test Coverage:** >80% coverage with ~4,500-6,000 lines of tests
5. **Complexity Distribution:** 10 low, 4 medium, 10 high complexity files

**Confidence:** ⭐⭐⭐⭐⭐ (5/5) - Based on 13 research plans

**References:**

- [Architecture Decision - Part 1: Code Volume Summary](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/design/csapiquerybuilder/architecture-decision/results/DECISION-part1-structure.md#code-volume-summary) - Detailed breakdown with component-level estimates
- [Architecture Decision - Part 2: Implementation Complexity](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/design/csapiquerybuilder/architecture-decision/results/DECISION-part2-implementation.md#decision-4-implementation-complexity-metrics) - Complexity analysis by component

---

## Summary: Build vs Extend Breakdown

### Components Extending Existing Code (9 components):

1. **Conformance Reader** - Add CSAPI conformance class checks (`hasConnectedSystems` getter, ~12 lines in `info.ts`)
2. **Collections Reader** - Parse CSAPI collection metadata (`csapiCollections` getter, ~6 lines in `endpoint.ts`)
3. **OgcApiEndpoint Integration** - Add `csapi(collectionId)` factory method (64 lines total: endpoint.ts 35 + info.ts 12 + index.ts 17)
4. **GeoJSON Handler** - Recognize CSAPI feature types and properties (extend existing GeoJSON parser)
5. **Format Detector** - Add SensorML 3.0 and SWE Common 3.0 media types (extend existing content negotiation)
6. **Validator** - Add CSAPI validation rules (extend existing validation framework)
7. **Background Processing** - Add CSAPI operations to Web Worker (extend existing worker with new message types)
8. **Test Coverage** - Add CSAPI test suites to Jest framework (extend existing test infrastructure, ~4,500-6,000 lines)
9. **API Documentation** - Add CSAPI docs to TypeDoc (extend existing documentation)

### Components Building New Code (3 components):

1. **CSAPIQueryBuilder** - New query builder class (~1,100-1,280 lines)

   - url_builder.ts: ~700-800 lines (includes validation)
   - model.ts: ~350-400 lines (GeoJSON types)
   - helpers.ts: ~50-80 lines (utilities)
   - **70-80 public methods** for all 9 CSAPI resource types
   - **Resource validation** in all methods (fail-fast with clear errors)
   - **3 helper methods** for code reuse (not inheritance)
   - **60-70 unique URL patterns** (CRUD, nested, schema, status endpoints)
   - **Three-tier type system** with 1,750-2,400 total lines

2. **SensorML Handler** - New format parser for SensorML 3.0 (~1,600-2,200 lines)

   - types.ts: ~800-1,200 lines (interfaces)
   - parser.ts: ~600-800 lines (main parser)
   - Sub-parsers: ~550-700 lines (simple-process, aggregate-process, physical-system)
   - Index file: ~50-100 lines
   - All system models, recursive component parsing, SWE Common integration

3. **SWE Common Handler** - New format parser for SWE Common 3.0 (~1,600-2,250 lines)
   - types.ts: ~600-800 lines (interfaces)
   - parser.ts: ~500-700 lines (main parser)
   - Sub-parsers: ~650-850 lines (data-record, data-array, components)
   - Index file: ~50-100 lines
   - JSON/Text/Binary encodings, all data component types, schema validation

### Architectural Notes:

**QueryBuilder Pattern:** Following the upstream EDR pattern (PR #114), CSAPI uses a single QueryBuilder class accessed via a factory method on OgcApiEndpoint. Developers call `endpoint.csapi(collectionId)` to get a CSAPIQueryBuilder instance containing all 9 resource type methods. This maintains the library's architecture principle of composition over inheritance.

**Resource Methods within QueryBuilder:** The 9 resource sections documented above (Systems, Deployments, Procedures, Sampling Features, Properties, DataStreams, Observations, Control Streams, Commands) are all methods within the single CSAPIQueryBuilder class, not separate standalone components. This follows the same pattern as EDR where `EDRQueryBuilder` contains methods like `getCubeUrl()`, `getCorridorUrl()`, etc.

**Integration Footprint:** Total modifications to existing files: 64 lines across 3 files (`endpoint.ts`: 35 lines, `info.ts`: 12 lines, `index.ts`: 17 lines). This minimal footprint follows the proven EDR integration pattern exactly.

**Resource Validation:** All 70-80 methods validate resource availability before building URLs (~140-160 lines total, ~2 lines per method). This user-mandated feature provides fail-fast behavior with clear error messages, improving developer experience for CSAPI's 9 resource types.

**Helper Methods:** 2-3 private helper methods provide code reuse without inheritance, following 100% of upstream patterns. No abstract base classes, no inheritance chains.

**File Organization:** Flat core (url_builder.ts, model.ts, helpers.ts) + formats/ subfolder (sensorml/, swecommon/, geojson.ts, constants.ts, 3 index files) for tree-shaking and maintainability. Total: 21 implementation files.

**Type System:** Three-tier hierarchy (Shared → OGC API → CSAPI) with 1,750-2,400 total lines:

- model.ts: ~350-400 lines (GeoJSON resources)
- formats/sensorml/types.ts: ~800-1,200 lines (SensorML interfaces)
- formats/swecommon/types.ts: ~600-800 lines (SWE Common interfaces)

**Scope Understanding:** While the summary lists "3 components building new code" (architecturally accurate), the implementation totals ~4,614-6,094 lines:

- QueryBuilder core: ~1,100-1,280 lines (21%)
- Format parsers: ~3,450-4,750 lines (76-78%)
- Integration: 64 lines (1%)

The format parsers represent ~76-78% of new code because CSAPI requires full parsing of SensorML 3.0 and SWE Common 3.0 (unlike other OGC APIs that only build URLs). This consolidated single-class architecture follows the upstream EDR pattern (one QueryBuilder per API family) but delivers functionally extensive capabilities across all CSAPI resources. Clients evaluating scope should understand that while architecturally elegant (3 new classes), the functional scope is substantial - implementing complete CSAPI Part 1 and Part 2 specifications with full query, filter, and pagination support across all resource types.

### Estimated Scope:

- **Extending existing code:** ~20% of effort (9 small extensions, 64 total lines modified in existing files + ~4,500-6,000 test lines)
- **Building new code:** ~80% of effort (QueryBuilder: ~1,100-1,280 lines + Format parsers: ~3,450-4,750 lines)
- **Total estimated lines of code:** ~9,114-12,094 lines (implementation + tests)
- **Total estimated time:** 51-72 hours development (6-9 weeks calendar time with testing)
- **Complexity:** 10 low, 4 medium, 10 high complexity files

**Confidence:** ⭐⭐⭐⭐⭐ (5/5) - All estimates validated through 13 research plans

**References:**

- [Architecture Decision - Part 1: Code Volume](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/design/csapiquerybuilder/architecture-decision/results/DECISION-part1-structure.md#code-volume-summary) - Component-level breakdown
- [Architecture Decision - Part 2: Implementation Complexity](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/design/csapiquerybuilder/architecture-decision/results/DECISION-part2-implementation.md#decision-4-implementation-complexity-metrics) - Detailed complexity analysis

---

## Project Goals Alignment

Every component described above aligns with these core project goals:

1. **Unified Developer Experience:** All CSAPI functionality accessed through existing `OgcApiEndpoint` class using the same patterns as Features, Tiles, and EDR
2. **Format Abstraction:** Developers work with TypeScript objects, not raw GeoJSON/SensorML/SWE Common
3. **Upstream Integration:** Extensions follow established patterns in the camptocamp/ogc-client repository (100% consistency validated through research)
4. **Complete Spec Coverage:** All CSAPI Part 1 and Part 2 resources with full CRUD support
5. **Production Ready:** Comprehensive validation, error handling, testing (>80% coverage), and documentation
6. **Performance Aware:** Web Worker support for heavy operations, efficient pagination, streaming support
7. **Developer Experience:** Resource validation (fail-fast with clear errors), type safety, helper methods for code reuse
8. **Type Safety:** Complete TypeScript type system (1,750-2,400 lines) with three-tier hierarchy and full IntelliSense
9. **Implementation Readiness:** Complete roadmap with phases, tasks, time estimates, and complexity ratings

---

## Development Standards

**Recommended Development Workflow:**

1. Follow the [Implementation Roadmap](#implementation-roadmap) phase by phase
2. Write method signatures before implementation
3. Add comprehensive JSDoc comments with parameters, return types, examples
4. Implement functionality with inline documentation for complex logic
5. Write tests as you implement (not deferred to later)
6. Document edge cases and validation rules as discovered
7. Add usage examples to JSDoc for common scenarios
8. Validate against spec examples throughout
9. Update documentation as you go - don't defer

**Code Quality Standards:**

- TypeScript strict mode enabled
- 100% public API JSDoc coverage
- > 80% test coverage (statement and branch)
- Lint-clean code (ESLint configuration)
- No magic numbers or strings (use constants)
- Consistent error handling patterns
- Performance profiling for heavy operations
- Follow three-tier type hierarchy
- Use helper methods for code reuse (no inheritance)

**Documentation Standards:**

- Clear, concise method descriptions
- Parameter descriptions with types and constraints
- Return type documentation
- Example code for common use cases
- Links to relevant CSAPI specification sections
- Error condition documentation
- Performance characteristics noted where relevant
- Type system documentation with IntelliSense examples

**Research-Validated Standards:**

- All architectural decisions backed by research (⭐⭐⭐⭐⭐ confidence)
- Follow upstream patterns (100% consistency)
- Helper methods for code reuse (0% inheritance)
- Resource validation in all methods (~2 lines per method)
- Flat file structure + formats/ subfolder
- Three-tier type system (shared → ogc-api → csapi)
- Complete integration code (64 lines exact)
- Comprehensive test coverage (>80%)

---

## Version History

**Document Version:** 6.0 (Complete Self-Contained Guide)  
**Date:** February 5, 2026  
**Research Foundation:** 14 completed research plans with ⭐⭐⭐⭐⭐ confidence (98-100%)  
**Status:** ✅ **ARCHITECTURE VALIDATED** with real-world scenarios and quantitative evidence

**Version 6.0 Restoration (February 5, 2026):**

- Restored 17 detailed implementation sections removed in v2.0
- All resource method sections restored (Systems, Deployments, Procedures, Sampling Features, Properties, DataStreams, Observations, Control Streams, Commands)
- All format handler sections restored (GeoJSON Handler, SensorML Handler, SWE Common Handler, Format Detector, Validator)
- All infrastructure sections restored (Background Processing, Test Coverage, API Documentation)
- Document now complete and self-contained with no archive dependencies
- Total additions: ~900 lines of detailed implementation guidance
- See [Phase 1 Reconnaissance Report](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/planning/archive/phase1-reconnaissance-report.md) for restoration methodology

**Previous Versions:**

- [v5.0 (archived)](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/planning/archive/csapi-implementation-guide-v5.md) - Architecture-validated with real-world scenarios (pre-restoration)
- [v4.0 (archived)](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/planning/archive/csapi-implementation-guide-v4.md) - Hybrid file structure diagram
- [v3.0 (archived)](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/planning/archive/csapi-implementation-guide-v3.md) - Implementation details and roadmap
- [v2.0 (archived)](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/planning/archive/csapi-implementation-guide-v2.md) - Research-validated structure (sections consolidated)
- [v1.0 (archived)](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/planning/archive/csapi-implementation-guide-v1.md) - Original architecture with all detailed sections
