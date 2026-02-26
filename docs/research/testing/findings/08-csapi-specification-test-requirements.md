# CSAPI Specification Reference

> **⚠️ REVIEW NOTICE (Phase 2D, C1):** This document was originally titled "CSAPI Specification Test Requirements Matrix" and framed as a test plan with 334 requirement IDs (SYS-001, DEP-001, etc.) tracing specification SHALL/MUST statements to proposed test cases. Phase 2D review identified this as anti-patterns AP1 (Testing Response Content), AP3 (OGC Requirement Traceability), and AP4 (Asserting Data Shape) at SEVERE severity.
>
> **Problem:** SHALL/MUST statements in OGC specifications are **server requirements** — they define what a conformant server implementation must do. A client library does not "claim conformance" to API specifications; it consumes them. This document was testing server compliance, not client code behavior.
>
> **Reclassification:** This document has been reclassified from "test requirements" to **"specification reference."** The requirement IDs (SYS-001, etc.) should NOT be used as test case identifiers. The resource type matrices, endpoint catalogs, query parameter inventories, temporal format specifications, and conformance class hierarchies remain valuable as **implementation reference material** — they inform what the CSAPIQueryBuilder must handle, what URL patterns exist, and what response shapes to expect in fixtures.
>
> **For actual test plans**, tests should be organized around client code modules: CSAPIQueryBuilder methods, parser functions (parseSensorML, parseSWECommon), and conformance detection logic — not around specification requirement IDs. See [Phase 2D review](../review/phase-2d-csapi-specific-testing-category.md) for details.

**Research Plan:** [Research Plan 08: CSAPI Specification Test Requirements](../research-plans/08-csapi-specification-test-requirements.md)  
**Research Questions:** 72 questions about normative requirements from CSAPI Parts 1 & 2, conformance classes, requirements for all 9 resource types, query parameters and validation rules, error conditions, specification examples as fixtures, OpenAPI schema requirements, format validation rules, and requirement cataloging  
**Methodology:** 4-phase systematic extraction (Part 1 specification deep dive extracting conformance classes and normative statements → Part 2 specification deep dive for dynamic resources and temporal/spatial queries → OpenAPI analysis parsing schemas and endpoints → Synthesis creating unified specification reference with cross-references)  
**Research Time:** 2.5 hours (150 minutes) (February 5, 2026)

**Primary Source(s):**

- [CSAPI Part 1 Specification (23-001)](https://docs.ogc.org/is/23-001/23-001.html) and [OpenAPI](../../standards/ogcapi-connectedsystems-1.bundled.oas31.yaml)
- [CSAPI Part 2 Specification (23-002)](https://docs.ogc.org/is/23-002/23-002.html) and [OpenAPI](../../standards/ogcapi-connectedsystems-2.bundled.oas31.yaml)

**Supporting Resources:**

- Part 1 Requirements Analysis: [csapi-part1-requirements.md](../../requirements/csapi-part1-requirements.md) (4,300 lines)
- Part 2 Requirements Analysis: [csapi-part2-requirements.md](../../requirements/csapi-part2-requirements.md) (6,022 lines)
- Implementation Guide: [csapi-implementation-guide.md](../../../planning/csapi-implementation-guide.md) (cross-validation)
- Section 6: [Meaningful vs Trivial Definition](06-meaningful-vs-trivial-definition.md) (quality criteria for testability)
- Section 7: [End-to-End Testing Scope](07-end-to-end-testing-scope.md) (workflow context)

**Document Purpose:** Catalog all 250+ normative requirements (SHALL/MUST statements) from CSAPI Parts 1 & 2 specifications and OpenAPI definitions as an implementation reference covering 19 conformance classes, 9 resource types, query parameters, validation rules, error conditions, and format requirements. This document serves as background knowledge for developers implementing the CSAPIQueryBuilder, format parsers, and conformance detection — it is not a test plan.

---

## Executive Summary

This document provides a comprehensive specification reference extracted from CSAPI Parts 1 & 2 specifications and OpenAPI definitions. All normative requirements (SHALL/MUST statements) have been cataloged with specification cross-references. These are **server requirements** that inform what the client must handle, not test cases for client code. See review notice above for reclassification context.

### Key Findings

**Total Normative Requirements Identified:** 250+ testable requirements across Parts 1 & 2

**Conformance Classes:**

- **Part 1:** 11 conformance classes covering 5 resource types
- **Part 2:** 8 conformance classes covering 4 dynamic resource types
- **Total:** 19 conformance classes defining scope of testing

**Coverage Across 9 Resource Types:**

| Resource Type     | Part | Properties | Query Parameters | Operations | Priority     |
| ----------------- | ---- | ---------- | ---------------- | ---------- | ------------ |
| Systems           | 1    | 15+        | 20+              | 12         | **CRITICAL** |
| Deployments       | 1    | 12+        | 15+              | 12         | HIGH         |
| Procedures        | 1    | 10+        | 10+              | 10         | MEDIUM       |
| Sampling Features | 1    | 12+        | 12+              | 10         | HIGH         |
| Properties        | 1    | 8+         | 8+               | 8          | MEDIUM       |
| DataStreams       | 2    | 15+        | 25+              | 15         | **CRITICAL** |
| Observations      | 2    | 10+        | 20+              | 12         | **CRITICAL** |
| ControlStreams    | 2    | 12+        | 20+              | 12         | HIGH         |
| Commands          | 2    | 12+        | 15+              | 15         | HIGH         |

**Testing Priorities:**

- **CRITICAL (Must Have):** Systems, DataStreams, Observations - 3 resource types, ~120 requirements
- **HIGH (Should Have):** Deployments, Sampling Features, ControlStreams, Commands - 4 resource types, ~80 requirements
- **MEDIUM (Nice to Have):** Procedures, Properties - 2 resource types, ~50 requirements

**Format Validation Requirements:**

- **GeoJSON:** 30+ validation rules (RFC 7946 + CSAPI extensions)
- **SensorML 3.0:** 40+ validation rules (system types, components, configurations)
- **SWE Common 3.0:** 50+ validation rules (data records, arrays, quantities, encodings)

**Query Parameter Validation:**

- **Temporal:** phenomenonTime, resultTime, validTime, executionTime, issueTime (25+ rules)
- **Spatial:** bbox, geometry (10+ rules)
- **Filtering:** systemType, observedProperty, controlledProperty, parent, foi (30+ rules)
- **Pagination:** limit, offset, bbox-crs (10+ rules)

---

## 1. Conformance Classes Matrix

### Part 1 Conformance Classes (11 total)

| Conformance Class        | Identifier                   | Prerequisites                               | Requirements Count | Priority     | Testing Focus                                   |
| ------------------------ | ---------------------------- | ------------------------------------------- | ------------------ | ------------ | ----------------------------------------------- |
| **Common**               | `/conf/api-common`           | OGC API Features Core, OGC API Common Core  | 3                  | **CRITICAL** | Resource IDs, UIDs, datetime parameters         |
| **System Features**      | `/conf/system`               | Common                                      | 5                  | **CRITICAL** | Systems CRUD, canonical endpoints, collections  |
| **Subsystems**           | `/conf/subsystem`            | System Features                             | 5                  | HIGH         | Subsystem navigation, recursive queries         |
| **Deployment Features**  | `/conf/deployment`           | Common                                      | 5                  | HIGH         | Deployments CRUD, system associations           |
| **Subdeployments**       | `/conf/subdeployment`        | Deployment Features                         | 4                  | MEDIUM       | Subdeployment hierarchy, recursive queries      |
| **Procedure Features**   | `/conf/procedure`            | Common                                      | 5                  | MEDIUM       | Procedures CRUD, no location requirement        |
| **Sampling Features**    | `/conf/sf`                   | Common, System Features                     | 5                  | HIGH         | Sampling features CRUD, system associations     |
| **Property Definitions** | `/conf/property`             | Common                                      | 4                  | MEDIUM       | Property resources, non-feature operations      |
| **Advanced Filtering**   | `/conf/advanced-filtering`   | System, Deployment, Procedure, SF, Property | 25+                | HIGH         | Relationship filters, hierarchy queries         |
| **Create/Update/Delete** | `/conf/create-update-delete` | OGC API Features Part 4                     | 10+                | HIGH         | POST/PUT/PATCH/DELETE operations                |
| **GeoJSON Encoding**     | `/conf/geojson`              | System, Deployment, Procedure, SF           | 10+                | **CRITICAL** | GeoJSON serialization, RFC 7946 compliance      |
| **SensorML Encoding**    | `/conf/sensorml`             | System, Deployment, Procedure, SF           | 15+                | HIGH         | SensorML 3.0 serialization, system descriptions |

### Part 2 Conformance Classes (8 total)

| Conformance Class                  | Identifier                             | Prerequisites                | Requirements Count | Priority     | Testing Focus                                                          |
| ---------------------------------- | -------------------------------------- | ---------------------------- | ------------------ | ------------ | ---------------------------------------------------------------------- |
| **Common (Part 2)**                | `/conf/api-common` (Part 2)            | OGC API Features Part 1 Core | 2                  | **CRITICAL** | Non-feature resources, resource collections                            |
| **DataStreams & Observations**     | `/conf/datastream`                     | Part 2 Common                | 16                 | **CRITICAL** | DataStream/Observation CRUD, schema operations, nested endpoints       |
| **ControlStreams & Commands**      | `/conf/controlstream`                  | Part 2 Common                | 18                 | HIGH         | ControlStream/Command CRUD, status/result endpoints, schema operations |
| **Command Feasibility**            | `/conf/feasibility`                    | ControlStreams & Commands    | 5                  | MEDIUM       | Feasibility checks, status/result tracking                             |
| **System Events**                  | `/conf/system-event`                   | Part 2 Common, Part 1 System | 5                  | MEDIUM       | System event logging, event types                                      |
| **Advanced Filtering (Part 2)**    | `/conf/advanced-filtering` (Part 2)    | Part 1 Advanced Filtering    | 17                 | HIGH         | Temporal/spatial filters for observations/commands                     |
| **Create/Replace/Delete (Part 2)** | `/conf/create-replace-delete` (Part 2) | OGC API Features Part 4      | 10+                | HIGH         | POST/PUT/DELETE for dynamic resources                                  |
| **SWE Common Encoding**            | `/conf/swecommon`                      | DataStreams & Observations   | 20+                | **CRITICAL** | SWE Common JSON/Text/Binary serialization                              |

**Total:** 19 conformance classes, 180+ explicit requirements (additional implicit requirements from prerequisites)

---

## 2. Resource Type Requirements Matrix

> **⚠️ REVIEW NOTICE (M1):** The requirement matrices below (Sections 2.1-2.9)
> contain 250+ entries with "Requirement ID", "Test Type", and "Priority"
> columns that frame spec properties as individual test cases. **Do not use
> these as a test checklist.** The useful content here is:
>
> - **Endpoint patterns:** What URL shapes the CSAPIQueryBuilder must produce
> - **Query parameters:** What parameters each resource type accepts
> - **Associations:** What link relationships exist between resource types
> - **Required vs optional properties:** What the parser must handle
>
> The "Test Type" and "Priority" columns reflect spec validation priorities,
> not client test priorities. For client tests, the priority is: does the
> parser/QueryBuilder produce correct output for each resource type?

### 2.1 Systems Resource Requirements

**Conformance Class:** System Features (`/conf/system`)  
**Priority:** **CRITICAL** (Primary resource type, foundational for all workflows)

| Requirement ID            | Type        | Description                                                    | Test Type   | Priority     | Spec Reference   |
| ------------------------- | ----------- | -------------------------------------------------------------- | ----------- | ------------ | ---------------- |
| **Properties Validation** |
| SYS-001                   | Property    | `uniqueIdentifier` must be valid URI                           | Unit        | **CRITICAL** | Part 1, Req 2    |
| SYS-002                   | Property    | `name` required (non-empty string)                             | Unit        | **CRITICAL** | Part 1, §9.2     |
| SYS-003                   | Property    | `systemType` from controlled vocabulary (Table 6)              | Unit        | HIGH         | Part 1, Table 6  |
| SYS-004                   | Property    | `assetType` from enum (Table 7) if present                     | Unit        | MEDIUM       | Part 1, Table 7  |
| SYS-005                   | Property    | `validTime` valid ISO 8601 datetime if present                 | Unit        | MEDIUM       | Part 1, §9.2     |
| SYS-006                   | Property    | `location` required for mobile systems (Req 4)                 | Unit        | HIGH         | Part 1, Req 4    |
| SYS-007                   | Property    | `location` updates when system moves (Req 4)                   | Integration | HIGH         | Part 1, Req 4    |
| **Canonical Endpoints**   |
| SYS-010                   | Endpoint    | System accessible at `{api_root}/systems/{id}` (Req 5)         | Integration | **CRITICAL** | Part 1, Req 5    |
| SYS-011                   | Endpoint    | Server exposes `{api_root}/systems` (Req 7)                    | Integration | **CRITICAL** | Part 1, Req 7    |
| SYS-012                   | Collection  | At least one collection with `featureType=sosa:System` (Req 8) | Integration | **CRITICAL** | Part 1, Req 8    |
| **Operations**            |
| SYS-020                   | Operation   | GET systems list from canonical endpoint                       | Integration | **CRITICAL** | Part 1, §9.3     |
| SYS-021                   | Operation   | GET single system by ID                                        | Integration | **CRITICAL** | Part 1, §9.3     |
| SYS-022                   | Operation   | GET systems from collection with featureType filter            | Integration | HIGH         | Part 1, §9.3     |
| SYS-023                   | Operation   | POST create new system at canonical endpoint                   | Integration | HIGH         | Part 1, §9.4     |
| SYS-024                   | Operation   | PUT replace system (full replacement)                          | Integration | MEDIUM       | Part 1, §9.5     |
| SYS-025                   | Operation   | PATCH update system (partial update)                           | Integration | MEDIUM       | Part 1, §9.5     |
| SYS-026                   | Operation   | DELETE system                                                  | Integration | MEDIUM       | Part 1, §9.6     |
| SYS-027                   | Operation   | DELETE system with cascade=true                                | Integration | MEDIUM       | Part 1, §9.6     |
| **Query Parameters**      |
| SYS-030                   | Parameter   | `systemType` filter (URI or CURIE)                             | Unit        | HIGH         | Part 1, §9.3     |
| SYS-031                   | Parameter   | `assetType` filter (enum value)                                | Unit        | MEDIUM       | Part 1, §9.3     |
| SYS-032                   | Parameter   | `parent` filter (system ID)                                    | Unit        | HIGH         | Part 1, §9.3     |
| SYS-033                   | Parameter   | `procedure` filter (procedure ID)                              | Unit        | MEDIUM       | Part 1, §9.3     |
| SYS-034                   | Parameter   | `bbox` spatial filter (WGS84)                                  | Unit        | HIGH         | OGC API Common   |
| SYS-035                   | Parameter   | `datetime` temporal filter (validTime)                         | Unit        | MEDIUM       | Part 1, Req 3    |
| SYS-036                   | Parameter   | `limit` pagination (integer > 0)                               | Unit        | HIGH         | OGC API Features |
| SYS-037                   | Parameter   | `offset` pagination (integer >= 0)                             | Unit        | MEDIUM       | OGC API Features |
| SYS-038                   | Parameter   | `recursive` boolean for subsystems                             | Unit        | HIGH         | Part 1, Req 10   |
| **Associations**          |
| SYS-040                   | Association | `subsystems` array links to subsystems                         | Integration | HIGH         | Part 1, §9.2     |
| SYS-041                   | Association | `deployments` array links to deployments                       | Integration | MEDIUM       | Part 1, §9.2     |
| SYS-042                   | Association | `procedures` array links to procedures                         | Integration | MEDIUM       | Part 1, §9.2     |
| SYS-043                   | Association | `samplingFeatures` array links to sampling features            | Integration | HIGH         | Part 1, §9.2     |
| SYS-044                   | Association | `datastreams` array links to datastreams (Part 2)              | Integration | **CRITICAL** | Part 2, §8.2     |
| SYS-045                   | Association | `controlstreams` array links to control streams (Part 2)       | Integration | HIGH         | Part 2, §9.2     |
| **Error Conditions**      |
| SYS-050                   | Error       | 404 for non-existent system ID                                 | Unit        | MEDIUM       | Part 1, §5.5     |
| SYS-051                   | Error       | 400 for invalid query parameters                               | Unit        | MEDIUM       | Part 1, §5.4     |
| SYS-052                   | Error       | 406 for unsupported media type                                 | Unit        | MEDIUM       | Part 1, §5.6     |
| SYS-053                   | Error       | 409 for duplicate uniqueIdentifier                             | Unit        | MEDIUM       | Part 1, §5.8     |
| SYS-054                   | Error       | 422 for invalid property values                                | Unit        | MEDIUM       | Part 1, §5.9     |

**Subsystems Requirements (Conformance Class `/conf/subsystem`):**

| Requirement ID | Type      | Description                                                      | Test Type   | Priority | Spec Reference |
| -------------- | --------- | ---------------------------------------------------------------- | ----------- | -------- | -------------- |
| SUB-001        | Endpoint  | Subsystems at `{api_root}/systems/{parentId}/subsystems` (Req 9) | Integration | HIGH     | Part 1, Req 9  |
| SUB-002        | Parameter | `recursive=false` returns direct subsystems only (Req 11)        | Integration | HIGH     | Part 1, Req 11 |
| SUB-003        | Parameter | `recursive=true` returns all nested subsystems (Req 11)          | Integration | HIGH     | Part 1, Req 11 |
| SUB-004        | Behavior  | Recursive associations include parent resources (Req 13)         | Integration | HIGH     | Part 1, Req 13 |
| SUB-005        | Behavior  | Query parameters apply to all processed systems                  | Integration | MEDIUM   | Part 1, §10.3  |

**Total Systems Requirements:** 45+ testable requirements

---

### 2.2 Deployments Resource Requirements

**Conformance Class:** Deployment Features (`/conf/deployment`)  
**Priority:** HIGH (Important for temporal/spatial context)

| Requirement ID            | Type        | Description                                                         | Test Type   | Priority | Spec Reference   |
| ------------------------- | ----------- | ------------------------------------------------------------------- | ----------- | -------- | ---------------- |
| **Properties Validation** |
| DEP-001                   | Property    | `uniqueIdentifier` must be valid URI                                | Unit        | HIGH     | Part 1, Req 2    |
| DEP-002                   | Property    | `name` required (non-empty string)                                  | Unit        | HIGH     | Part 1, §11.2    |
| DEP-003                   | Property    | `validTime` valid ISO 8601 interval if present                      | Unit        | HIGH     | Part 1, §11.2    |
| DEP-004                   | Property    | `geometry` valid GeoJSON if present                                 | Unit        | MEDIUM   | Part 1, §11.2    |
| **Canonical Endpoints**   |
| DEP-010                   | Endpoint    | Deployment accessible at `{api_root}/deployments/{id}` (Req 14)     | Integration | HIGH     | Part 1, Req 14   |
| DEP-011                   | Endpoint    | Server exposes `{api_root}/deployments` (Req 16)                    | Integration | HIGH     | Part 1, Req 16   |
| DEP-012                   | Endpoint    | Nested endpoint `{api_root}/systems/{sysId}/deployments` (Req 17)   | Integration | HIGH     | Part 1, Req 17   |
| DEP-013                   | Collection  | At least one collection with `featureType=sosa:Deployment` (Req 18) | Integration | HIGH     | Part 1, Req 18   |
| **Operations**            |
| DEP-020                   | Operation   | GET deployments list from canonical endpoint                        | Integration | HIGH     | Part 1, §11.3    |
| DEP-021                   | Operation   | GET single deployment by ID                                         | Integration | HIGH     | Part 1, §11.3    |
| DEP-022                   | Operation   | GET deployments for specific system                                 | Integration | HIGH     | Part 1, §11.3    |
| DEP-023                   | Operation   | POST create new deployment                                          | Integration | MEDIUM   | Part 1, §11.4    |
| DEP-024                   | Operation   | PUT replace deployment                                              | Integration | MEDIUM   | Part 1, §11.5    |
| DEP-025                   | Operation   | PATCH update deployment                                             | Integration | MEDIUM   | Part 1, §11.5    |
| DEP-026                   | Operation   | DELETE deployment                                                   | Integration | MEDIUM   | Part 1, §11.6    |
| **Query Parameters**      |
| DEP-030                   | Parameter   | `system` filter (system ID)                                         | Unit        | HIGH     | Part 1, §11.3    |
| DEP-031                   | Parameter   | `procedure` filter (procedure ID)                                   | Unit        | MEDIUM   | Part 1, §11.3    |
| DEP-032                   | Parameter   | `bbox` spatial filter                                               | Unit        | HIGH     | OGC API Common   |
| DEP-033                   | Parameter   | `datetime` temporal filter (validTime)                              | Unit        | HIGH     | Part 1, Req 3    |
| DEP-034                   | Parameter   | `limit` pagination                                                  | Unit        | HIGH     | OGC API Features |
| DEP-035                   | Parameter   | `recursive` for subdeployments                                      | Unit        | MEDIUM   | Part 1, Req 20   |
| **Associations**          |
| DEP-040                   | Association | `deployedSystems` array links to systems                            | Integration | HIGH     | Part 1, §11.2    |
| DEP-041                   | Association | `subdeployments` array links to subdeployments                      | Integration | MEDIUM   | Part 1, §11.2    |
| **Error Conditions**      |
| DEP-050                   | Error       | 404 for non-existent deployment ID                                  | Unit        | MEDIUM   | Part 1, §5.5     |
| DEP-051                   | Error       | 400 for invalid query parameters                                    | Unit        | MEDIUM   | Part 1, §5.4     |

**Total Deployments Requirements:** 25+ testable requirements

---

### 2.3 Procedures Resource Requirements

**Conformance Class:** Procedure Features (`/conf/procedure`)  
**Priority:** MEDIUM (Support resource for system descriptions)

| Requirement ID            | Type       | Description                                                        | Test Type   | Priority | Spec Reference   |
| ------------------------- | ---------- | ------------------------------------------------------------------ | ----------- | -------- | ---------------- |
| **Properties Validation** |
| PROC-001                  | Property   | `uniqueIdentifier` must be valid URI                               | Unit        | MEDIUM   | Part 1, Req 2    |
| PROC-002                  | Property   | `name` required (non-empty string)                                 | Unit        | MEDIUM   | Part 1, §13.2    |
| PROC-003                  | Property   | `procedureType` from controlled vocabulary                         | Unit        | MEDIUM   | Part 1, §13.2    |
| PROC-004                  | Property   | `location` MUST NOT be present (Req 24)                            | Unit        | MEDIUM   | Part 1, Req 24   |
| **Canonical Endpoints**   |
| PROC-010                  | Endpoint   | Procedure accessible at `{api_root}/procedures/{id}` (Req 25)      | Integration | MEDIUM   | Part 1, Req 25   |
| PROC-011                  | Endpoint   | Server exposes `{api_root}/procedures` (Req 27)                    | Integration | MEDIUM   | Part 1, Req 27   |
| PROC-012                  | Collection | At least one collection with `featureType=sosa:Procedure` (Req 28) | Integration | MEDIUM   | Part 1, Req 28   |
| **Operations**            |
| PROC-020                  | Operation  | GET procedures list                                                | Integration | MEDIUM   | Part 1, §13.3    |
| PROC-021                  | Operation  | GET single procedure by ID                                         | Integration | MEDIUM   | Part 1, §13.3    |
| PROC-022                  | Operation  | POST create new procedure                                          | Integration | LOW      | Part 1, §13.4    |
| PROC-023                  | Operation  | PUT replace procedure                                              | Integration | LOW      | Part 1, §13.5    |
| PROC-024                  | Operation  | DELETE procedure                                                   | Integration | LOW      | Part 1, §13.6    |
| **Query Parameters**      |
| PROC-030                  | Parameter  | `procedureType` filter                                             | Unit        | MEDIUM   | Part 1, §13.3    |
| PROC-031                  | Parameter  | `limit` pagination                                                 | Unit        | MEDIUM   | OGC API Features |
| **Error Conditions**      |
| PROC-050                  | Error      | 404 for non-existent procedure ID                                  | Unit        | LOW      | Part 1, §5.5     |
| PROC-051                  | Error      | 422 if location property present                                   | Unit        | MEDIUM   | Part 1, Req 24   |

**Total Procedures Requirements:** 15+ testable requirements

---

### 2.4 Sampling Features Resource Requirements

**Conformance Class:** Sampling Features (`/conf/sf`)  
**Priority:** HIGH (Links systems to features of interest)

| Requirement ID            | Type        | Description                                                            | Test Type   | Priority | Spec Reference   |
| ------------------------- | ----------- | ---------------------------------------------------------------------- | ----------- | -------- | ---------------- |
| **Properties Validation** |
| SF-001                    | Property    | `uniqueIdentifier` must be valid URI                                   | Unit        | HIGH     | Part 1, Req 2    |
| SF-002                    | Property    | `name` required (non-empty string)                                     | Unit        | HIGH     | Part 1, §14.2    |
| SF-003                    | Property    | `sampledFeature` URI reference if present                              | Unit        | HIGH     | Part 1, §14.2    |
| SF-004                    | Property    | `geometry` valid GeoJSON                                               | Unit        | HIGH     | Part 1, §14.2    |
| **Canonical Endpoints**   |
| SF-010                    | Endpoint    | Sampling feature at `{api_root}/samplingFeatures/{id}` (Req 29)        | Integration | HIGH     | Part 1, Req 29   |
| SF-011                    | Endpoint    | Server exposes `{api_root}/samplingFeatures` (Req 31)                  | Integration | HIGH     | Part 1, Req 31   |
| SF-012                    | Endpoint    | Nested endpoint `{api_root}/systems/{sysId}/samplingFeatures` (Req 32) | Integration | HIGH     | Part 1, Req 32   |
| SF-013                    | Behavior    | System sampling features only for that system (Req 32)                 | Integration | HIGH     | Part 1, Req 32   |
| SF-014                    | Collection  | At least one collection with `featureType=sosa:Sample` (Req 33)        | Integration | HIGH     | Part 1, Req 33   |
| **Operations**            |
| SF-020                    | Operation   | GET sampling features list                                             | Integration | HIGH     | Part 1, §14.3    |
| SF-021                    | Operation   | GET single sampling feature by ID                                      | Integration | HIGH     | Part 1, §14.3    |
| SF-022                    | Operation   | GET sampling features for system                                       | Integration | HIGH     | Part 1, §14.3    |
| SF-023                    | Operation   | POST create sampling feature under system                              | Integration | MEDIUM   | Part 1, §14.4    |
| SF-024                    | Operation   | PUT replace sampling feature                                           | Integration | MEDIUM   | Part 1, §14.5    |
| SF-025                    | Operation   | DELETE sampling feature                                                | Integration | MEDIUM   | Part 1, §14.6    |
| **Query Parameters**      |
| SF-030                    | Parameter   | `system` filter (system ID)                                            | Unit        | HIGH     | Part 1, §14.3    |
| SF-031                    | Parameter   | `sampledFeature` filter (FOI URI)                                      | Unit        | HIGH     | Part 1, §14.3    |
| SF-032                    | Parameter   | `bbox` spatial filter                                                  | Unit        | HIGH     | OGC API Common   |
| SF-033                    | Parameter   | `limit` pagination                                                     | Unit        | HIGH     | OGC API Features |
| **Associations**          |
| SF-040                    | Association | `systems` array links to systems                                       | Integration | HIGH     | Part 1, §14.2    |
| **Error Conditions**      |
| SF-050                    | Error       | 404 for non-existent sampling feature ID                               | Unit        | MEDIUM   | Part 1, §5.5     |

**Total Sampling Features Requirements:** 20+ testable requirements

---

### 2.5 Properties Resource Requirements

**Conformance Class:** Property Definitions (`/conf/property`)  
**Priority:** MEDIUM (Support resource for property definitions)

| Requirement ID            | Type        | Description                                                    | Test Type   | Priority | Spec Reference   |
| ------------------------- | ----------- | -------------------------------------------------------------- | ----------- | -------- | ---------------- |
| **Properties Validation** |
| PROP-001                  | Property    | `uniqueIdentifier` must be valid URI                           | Unit        | MEDIUM   | Part 1, Req 2    |
| PROP-002                  | Property    | `name` required (non-empty string)                             | Unit        | MEDIUM   | Part 1, §15.2    |
| PROP-003                  | Property    | `definition` URI reference if present                          | Unit        | MEDIUM   | Part 1, §15.2    |
| **Canonical Endpoints**   |
| PROP-010                  | Endpoint    | Property at `{api_root}/properties/{id}` (Req 34)              | Integration | MEDIUM   | Part 1, Req 34   |
| PROP-011                  | Endpoint    | Server exposes `{api_root}/properties` (Req 36)                | Integration | MEDIUM   | Part 1, Req 36   |
| PROP-012                  | Collection  | At least one collection with `itemType=sosa:Property` (Req 37) | Integration | MEDIUM   | Part 1, Req 37   |
| PROP-013                  | Terminology | Use "resources/resource" not "features/feature" (Req 35)       | Unit        | LOW      | Part 1, Req 35   |
| **Operations**            |
| PROP-020                  | Operation   | GET properties list                                            | Integration | MEDIUM   | Part 1, §15.3    |
| PROP-021                  | Operation   | GET single property by ID                                      | Integration | MEDIUM   | Part 1, §15.3    |
| PROP-022                  | Operation   | POST create new property                                       | Integration | LOW      | Part 1, §15.4    |
| PROP-023                  | Operation   | PUT replace property                                           | Integration | LOW      | Part 1, §15.5    |
| PROP-024                  | Operation   | DELETE property                                                | Integration | LOW      | Part 1, §15.6    |
| **Query Parameters**      |
| PROP-030                  | Parameter   | `limit` pagination                                             | Unit        | MEDIUM   | OGC API Features |
| **Error Conditions**      |
| PROP-050                  | Error       | 404 for non-existent property ID                               | Unit        | LOW      | Part 1, §5.5     |

**Total Properties Requirements:** 15+ testable requirements

---

### 2.6 DataStreams Resource Requirements

**Conformance Class:** DataStreams & Observations (`/conf/datastream`)  
**Priority:** **CRITICAL** (Primary data access mechanism)

| Requirement ID                                   | Type        | Description                                                              | Test Type   | Priority     | Spec Reference   |
| ------------------------------------------------ | ----------- | ------------------------------------------------------------------------ | ----------- | ------------ | ---------------- |
| **Properties Validation**                        |
| DS-001                                           | Property    | `uniqueIdentifier` must be valid URI                                     | Unit        | **CRITICAL** | Part 2, Req 2    |
| DS-002                                           | Property    | `name` required (non-empty string)                                       | Unit        | **CRITICAL** | Part 2, §8.2     |
| DS-003                                           | Property    | `observedProperties` array of URIs required                              | Unit        | **CRITICAL** | Part 2, §8.2     |
| DS-004                                           | Property    | `phenomenonTimeRange` ISO 8601 interval if present                       | Unit        | HIGH         | Part 2, §8.2     |
| DS-005                                           | Property    | `resultTimeRange` ISO 8601 interval if present                           | Unit        | HIGH         | Part 2, §8.2     |
| DS-006                                           | Property    | `streamType` enum (status, observation)                                  | Unit        | HIGH         | Part 2, §8.2     |
| **Canonical Endpoints**                          |
| DS-010                                           | Endpoint    | DataStream at `{api_root}/datastreams/{id}` (Req 5)                      | Integration | **CRITICAL** | Part 2, Req 5    |
| DS-011                                           | Endpoint    | Server exposes `{api_root}/datastreams` (Req 7)                          | Integration | **CRITICAL** | Part 2, Req 7    |
| DS-012                                           | Endpoint    | Nested `{api_root}/systems/{sysId}/datastreams` (Req 8)                  | Integration | **CRITICAL** | Part 2, Req 8    |
| DS-013                                           | Endpoint    | Nested `{api_root}/deployments/{depId}/datastreams` (Req 9)              | Integration | HIGH         | Part 2, Req 9    |
| DS-014                                           | Collection  | At least one collection with `itemType=DataStream` (Req 10)              | Integration | **CRITICAL** | Part 2, Req 10   |
| **Schema Operations**                            |
| DS-020                                           | Operation   | GET schema `{api_root}/datastreams/{id}/schema?obsFormat={fmt}` (Req 11) | Integration | **CRITICAL** | Part 2, Req 11   |
| DS-021                                           | Format      | Schema supports `obsFormat=application/swe+json`                         | Unit        | **CRITICAL** | Part 2, §8.4     |
| DS-022                                           | Format      | Schema supports `obsFormat=application/om+json`                          | Unit        | HIGH         | Part 2, §8.4     |
| **Operations**                                   |
| DS-030                                           | Operation   | GET datastreams list                                                     | Integration | **CRITICAL** | Part 2, §8.3     |
| DS-031                                           | Operation   | GET single datastream by ID                                              | Integration | **CRITICAL** | Part 2, §8.3     |
| DS-032                                           | Operation   | GET datastreams for system                                               | Integration | **CRITICAL** | Part 2, §8.3     |
| DS-033                                           | Operation   | GET datastreams for deployment                                           | Integration | HIGH         | Part 2, §8.3     |
| DS-034                                           | Operation   | POST create new datastream                                               | Integration | HIGH         | Part 2, §8.4     |
| DS-035                                           | Operation   | PUT replace datastream                                                   | Integration | MEDIUM       | Part 2, §8.5     |
| DS-036                                           | Operation   | DELETE datastream                                                        | Integration | MEDIUM       | Part 2, §8.6     |
| **Query Parameters (Part 1 Common)**             |
| DS-040                                           | Parameter   | `system` filter (system ID)                                              | Unit        | **CRITICAL** | Part 2, §8.3     |
| DS-041                                           | Parameter   | `deployment` filter (deployment ID)                                      | Unit        | HIGH         | Part 2, §8.3     |
| DS-042                                           | Parameter   | `procedure` filter (procedure ID)                                        | Unit        | MEDIUM       | Part 2, §8.3     |
| DS-043                                           | Parameter   | `foi` filter (FOI URI)                                                   | Unit        | HIGH         | Part 2, §8.3     |
| DS-044                                           | Parameter   | `limit` pagination                                                       | Unit        | HIGH         | OGC API Features |
| **Query Parameters (Part 2 Advanced Filtering)** |
| DS-050                                           | Parameter   | `phenomenonTime` temporal filter (interval) (Req 45)                     | Unit        | **CRITICAL** | Part 2, Req 45   |
| DS-051                                           | Parameter   | `resultTime` temporal filter (interval) (Req 46)                         | Unit        | **CRITICAL** | Part 2, Req 46   |
| DS-052                                           | Parameter   | `observedProperty` filter (URI list) (Req 47)                            | Unit        | **CRITICAL** | Part 2, Req 47   |
| **Associations**                                 |
| DS-060                                           | Association | `system` links to producer system                                        | Integration | **CRITICAL** | Part 2, §8.2     |
| DS-061                                           | Association | `observations` array links to observations                               | Integration | **CRITICAL** | Part 2, §8.2     |
| DS-062                                           | Association | `procedure` links to procedure if present                                | Integration | MEDIUM       | Part 2, §8.2     |
| DS-063                                           | Association | `deployment` links to deployment if present                              | Integration | HIGH         | Part 2, §8.2     |
| DS-064                                           | Association | `samplingFeatures` array links to sampling features (Req 3)              | Integration | HIGH         | Part 2, Req 3    |
| DS-065                                           | Association | `featuresOfInterest` array links to FOIs (Req 4)                         | Integration | HIGH         | Part 2, Req 4    |
| **Error Conditions**                             |
| DS-070                                           | Error       | 404 for non-existent datastream ID                                       | Unit        | MEDIUM       | Part 2, §5.5     |
| DS-071                                           | Error       | 400 for invalid query parameters                                         | Unit        | MEDIUM       | Part 2, §5.4     |
| DS-072                                           | Error       | 400 for invalid phenomenonTime format                                    | Unit        | HIGH         | Part 2, Req 45   |
| DS-073                                           | Error       | 400 for invalid resultTime format                                        | Unit        | HIGH         | Part 2, Req 46   |

**Total DataStreams Requirements:** 40+ testable requirements

---

### 2.7 Observations Resource Requirements

**Conformance Class:** DataStreams & Observations (`/conf/datastream`)  
**Priority:** **CRITICAL** (Actual observation data)

| Requirement ID                                   | Type        | Description                                                  | Test Type   | Priority     | Spec Reference   |
| ------------------------------------------------ | ----------- | ------------------------------------------------------------ | ----------- | ------------ | ---------------- |
| **Properties Validation**                        |
| OBS-001                                          | Property    | `phenomenonTime` valid ISO 8601 datetime/interval            | Unit        | **CRITICAL** | Part 2, §8.2     |
| OBS-002                                          | Property    | `resultTime` valid ISO 8601 datetime                         | Unit        | **CRITICAL** | Part 2, §8.2     |
| OBS-003                                          | Property    | `result` matches datastream schema                           | Unit        | **CRITICAL** | Part 2, §8.2     |
| OBS-004                                          | Property    | `parameters` matches datastream parameter schema if present  | Unit        | MEDIUM       | Part 2, §8.2     |
| **Canonical Endpoints**                          |
| OBS-010                                          | Endpoint    | Observation at `{api_root}/observations/{id}` (Req 12)       | Integration | **CRITICAL** | Part 2, Req 12   |
| OBS-011                                          | Endpoint    | Server exposes `{api_root}/observations` (Req 14)            | Integration | **CRITICAL** | Part 2, Req 14   |
| OBS-012                                          | Endpoint    | Nested `{api_root}/datastreams/{dsId}/observations` (Req 15) | Integration | **CRITICAL** | Part 2, Req 15   |
| OBS-013                                          | Collection  | At least one collection with `itemType=Observation` (Req 16) | Integration | **CRITICAL** | Part 2, Req 16   |
| **Operations**                                   |
| OBS-020                                          | Operation   | GET observations list                                        | Integration | **CRITICAL** | Part 2, §8.3     |
| OBS-021                                          | Operation   | GET single observation by ID                                 | Integration | **CRITICAL** | Part 2, §8.3     |
| OBS-022                                          | Operation   | GET observations for datastream                              | Integration | **CRITICAL** | Part 2, §8.3     |
| OBS-023                                          | Operation   | POST create new observation                                  | Integration | HIGH         | Part 2, §8.4     |
| OBS-024                                          | Operation   | DELETE observation                                           | Integration | MEDIUM       | Part 2, §8.6     |
| **Query Parameters (Part 1 Common)**             |
| OBS-030                                          | Parameter   | `datastream` filter (datastream ID)                          | Unit        | **CRITICAL** | Part 2, §8.3     |
| OBS-031                                          | Parameter   | `limit` pagination                                           | Unit        | **CRITICAL** | OGC API Features |
| OBS-032                                          | Parameter   | `offset` pagination                                          | Unit        | HIGH         | OGC API Features |
| **Query Parameters (Part 2 Advanced Filtering)** |
| OBS-040                                          | Parameter   | `phenomenonTime` temporal filter (interval) (Req 48)         | Unit        | **CRITICAL** | Part 2, Req 48   |
| OBS-041                                          | Parameter   | `resultTime` temporal filter (interval/`latest`) (Req 49)    | Unit        | **CRITICAL** | Part 2, Req 49   |
| OBS-042                                          | Parameter   | `resultTime=latest` returns most recent (Req 50)             | Integration | **CRITICAL** | Part 2, Req 50   |
| OBS-043                                          | Parameter   | `foi` filter (FOI URI) (Req 51)                              | Unit        | HIGH         | Part 2, Req 51   |
| **Temporal Filter Formats**                      |
| OBS-050                                          | Format      | Instant: `2024-01-15T12:00:00Z`                              | Unit        | **CRITICAL** | Part 2, §8.3     |
| OBS-051                                          | Format      | Closed interval: `2024-01-01/2024-01-31`                     | Unit        | **CRITICAL** | Part 2, §8.3     |
| OBS-052                                          | Format      | Open start: `../2024-01-31`                                  | Unit        | HIGH         | Part 2, §8.3     |
| OBS-053                                          | Format      | Open end: `2024-01-01/..`                                    | Unit        | HIGH         | Part 2, §8.3     |
| OBS-054                                          | Format      | Duration: `2024-01-01/P1M`                                   | Unit        | MEDIUM       | Part 2, §8.3     |
| **Associations**                                 |
| OBS-060                                          | Association | `datastream` links to parent datastream                      | Integration | **CRITICAL** | Part 2, §8.2     |
| OBS-061                                          | Association | `samplingFeature` links to sampling feature if present       | Integration | HIGH         | Part 2, §8.2     |
| OBS-062                                          | Association | `procedure` links to procedure if present                    | Integration | MEDIUM       | Part 2, §8.2     |
| **Error Conditions**                             |
| OBS-070                                          | Error       | 404 for non-existent observation ID                          | Unit        | MEDIUM       | Part 2, §5.5     |
| OBS-071                                          | Error       | 400 for invalid phenomenonTime format                        | Unit        | HIGH         | Part 2, Req 48   |
| OBS-072                                          | Error       | 400 for invalid resultTime format                            | Unit        | HIGH         | Part 2, Req 49   |
| OBS-073                                          | Error       | 422 for result not matching schema                           | Unit        | HIGH         | Part 2, §8.2     |

**Total Observations Requirements:** 35+ testable requirements

---

### 2.8 ControlStreams Resource Requirements

**Conformance Class:** ControlStreams & Commands (`/conf/controlstream`)  
**Priority:** HIGH (Command and control functionality)

| Requirement ID                                   | Type        | Description                                                                 | Test Type   | Priority | Spec Reference   |
| ------------------------------------------------ | ----------- | --------------------------------------------------------------------------- | ----------- | -------- | ---------------- |
| **Properties Validation**                        |
| CS-001                                           | Property    | `uniqueIdentifier` must be valid URI                                        | Unit        | HIGH     | Part 2, Req 2    |
| CS-002                                           | Property    | `name` required (non-empty string)                                          | Unit        | HIGH     | Part 2, §9.2     |
| CS-003                                           | Property    | `controlledProperties` array of URIs required                               | Unit        | HIGH     | Part 2, §9.2     |
| CS-004                                           | Property    | `streamType` enum (self, external)                                          | Unit        | HIGH     | Part 2, §9.2     |
| **Canonical Endpoints**                          |
| CS-010                                           | Endpoint    | ControlStream at `{api_root}/controlstreams/{id}` (Req 19)                  | Integration | HIGH     | Part 2, Req 19   |
| CS-011                                           | Endpoint    | Server exposes `{api_root}/controlstreams` (Req 21)                         | Integration | HIGH     | Part 2, Req 21   |
| CS-012                                           | Endpoint    | Nested `{api_root}/systems/{sysId}/controlstreams` (Req 22)                 | Integration | HIGH     | Part 2, Req 22   |
| CS-013                                           | Endpoint    | Nested `{api_root}/deployments/{depId}/controlstreams` (Req 23)             | Integration | MEDIUM   | Part 2, Req 23   |
| CS-014                                           | Collection  | At least one collection with `itemType=ControlStream` (Req 24)              | Integration | HIGH     | Part 2, Req 24   |
| **Schema Operations**                            |
| CS-020                                           | Operation   | GET schema `{api_root}/controlstreams/{id}/schema?cmdFormat={fmt}` (Req 25) | Integration | HIGH     | Part 2, Req 25   |
| CS-021                                           | Format      | Schema supports `cmdFormat=application/swe+json`                            | Unit        | HIGH     | Part 2, §9.4     |
| **Operations**                                   |
| CS-030                                           | Operation   | GET control streams list                                                    | Integration | HIGH     | Part 2, §9.3     |
| CS-031                                           | Operation   | GET single control stream by ID                                             | Integration | HIGH     | Part 2, §9.3     |
| CS-032                                           | Operation   | GET control streams for system                                              | Integration | HIGH     | Part 2, §9.3     |
| CS-033                                           | Operation   | GET control streams for deployment                                          | Integration | MEDIUM   | Part 2, §9.3     |
| CS-034                                           | Operation   | POST create new control stream                                              | Integration | MEDIUM   | Part 2, §9.4     |
| CS-035                                           | Operation   | PUT replace control stream                                                  | Integration | LOW      | Part 2, §9.5     |
| CS-036                                           | Operation   | DELETE control stream                                                       | Integration | LOW      | Part 2, §9.6     |
| **Query Parameters (Part 1 Common)**             |
| CS-040                                           | Parameter   | `system` filter (system ID)                                                 | Unit        | HIGH     | Part 2, §9.3     |
| CS-041                                           | Parameter   | `deployment` filter (deployment ID)                                         | Unit        | MEDIUM   | Part 2, §9.3     |
| CS-042                                           | Parameter   | `procedure` filter (procedure ID)                                           | Unit        | LOW      | Part 2, §9.3     |
| CS-043                                           | Parameter   | `foi` filter (FOI URI)                                                      | Unit        | MEDIUM   | Part 2, §9.3     |
| CS-044                                           | Parameter   | `limit` pagination                                                          | Unit        | HIGH     | OGC API Features |
| **Query Parameters (Part 2 Advanced Filtering)** |
| CS-050                                           | Parameter   | `issueTime` temporal filter (interval) (Req 52)                             | Unit        | HIGH     | Part 2, Req 52   |
| CS-051                                           | Parameter   | `executionTime` temporal filter (interval) (Req 53)                         | Unit        | HIGH     | Part 2, Req 53   |
| CS-052                                           | Parameter   | `controlledProperty` filter (URI list) (Req 54)                             | Unit        | HIGH     | Part 2, Req 54   |
| **Associations**                                 |
| CS-060                                           | Association | `system` links to receiver system                                           | Integration | HIGH     | Part 2, §9.2     |
| CS-061                                           | Association | `commands` array links to commands                                          | Integration | HIGH     | Part 2, §9.2     |
| CS-062                                           | Association | `procedure` links to procedure if present                                   | Integration | LOW      | Part 2, §9.2     |
| CS-063                                           | Association | `deployment` links to deployment if present                                 | Integration | MEDIUM   | Part 2, §9.2     |
| CS-064                                           | Association | `samplingFeatures` array links to sampling features (Req 17)                | Integration | MEDIUM   | Part 2, Req 17   |
| CS-065                                           | Association | `featuresOfInterest` array links to FOIs (Req 18)                           | Integration | MEDIUM   | Part 2, Req 18   |
| **Error Conditions**                             |
| CS-070                                           | Error       | 404 for non-existent control stream ID                                      | Unit        | MEDIUM   | Part 2, §5.5     |
| CS-071                                           | Error       | 400 for invalid query parameters                                            | Unit        | MEDIUM   | Part 2, §5.4     |

**Total ControlStreams Requirements:** 35+ testable requirements

---

### 2.9 Commands Resource Requirements

**Conformance Class:** ControlStreams & Commands (`/conf/controlstream`)  
**Priority:** HIGH (Command execution and tracking)

| Requirement ID                                   | Type        | Description                                                 | Test Type   | Priority | Spec Reference   |
| ------------------------------------------------ | ----------- | ----------------------------------------------------------- | ----------- | -------- | ---------------- |
| **Properties Validation**                        |
| CMD-001                                          | Property    | `issueTime` valid ISO 8601 datetime                         | Unit        | HIGH     | Part 2, §9.2     |
| CMD-002                                          | Property    | `executionTime` valid ISO 8601 datetime                     | Unit        | HIGH     | Part 2, §9.2     |
| CMD-003                                          | Property    | `parameters` matches control stream schema                  | Unit        | HIGH     | Part 2, §9.2     |
| **Canonical Endpoints**                          |
| CMD-010                                          | Endpoint    | Command at `{api_root}/commands/{id}` (Req 26)              | Integration | HIGH     | Part 2, Req 26   |
| CMD-011                                          | Endpoint    | Server exposes `{api_root}/commands` (Req 28)               | Integration | HIGH     | Part 2, Req 28   |
| CMD-012                                          | Endpoint    | Nested `{api_root}/controlstreams/{csId}/commands` (Req 29) | Integration | HIGH     | Part 2, Req 29   |
| CMD-013                                          | Collection  | At least one collection with `itemType=Command` (Req 30)    | Integration | HIGH     | Part 2, Req 30   |
| **Status and Result Endpoints**                  |
| CMD-020                                          | Endpoint    | GET status `{api_root}/commands/{cmdId}/status` (Req 31)    | Integration | HIGH     | Part 2, Req 31   |
| CMD-021                                          | Endpoint    | POST status `{api_root}/commands/{cmdId}/status` (Req 32)   | Integration | HIGH     | Part 2, Req 32   |
| CMD-022                                          | Endpoint    | GET result `{api_root}/commands/{cmdId}/result` (Req 33)    | Integration | HIGH     | Part 2, Req 33   |
| CMD-023                                          | Endpoint    | POST result `{api_root}/commands/{cmdId}/result` (Req 34)   | Integration | HIGH     | Part 2, Req 34   |
| **Operations**                                   |
| CMD-030                                          | Operation   | GET commands list                                           | Integration | HIGH     | Part 2, §9.3     |
| CMD-031                                          | Operation   | GET single command by ID                                    | Integration | HIGH     | Part 2, §9.3     |
| CMD-032                                          | Operation   | GET commands for control stream                             | Integration | HIGH     | Part 2, §9.3     |
| CMD-033                                          | Operation   | POST create/submit new command                              | Integration | HIGH     | Part 2, §9.4     |
| CMD-034                                          | Operation   | DELETE command (cancel)                                     | Integration | HIGH     | Part 2, §9.6     |
| **Query Parameters (Part 1 Common)**             |
| CMD-040                                          | Parameter   | `controlstream` filter (control stream ID)                  | Unit        | HIGH     | Part 2, §9.3     |
| CMD-041                                          | Parameter   | `limit` pagination                                          | Unit        | HIGH     | OGC API Features |
| **Query Parameters (Part 2 Advanced Filtering)** |
| CMD-050                                          | Parameter   | `issueTime` temporal filter (interval) (Req 56)             | Unit        | HIGH     | Part 2, Req 56   |
| CMD-051                                          | Parameter   | `executionTime` temporal filter (interval) (Req 57)         | Unit        | HIGH     | Part 2, Req 57   |
| CMD-052                                          | Parameter   | `foi` filter (FOI URI) (Req 58)                             | Unit        | MEDIUM   | Part 2, Req 58   |
| **Status Code Values**                           |
| CMD-060                                          | Status      | `PENDING` - Command accepted, waiting                       | Unit        | HIGH     | Part 2, §9.2     |
| CMD-061                                          | Status      | `ACCEPTED` - Command being processed                        | Unit        | HIGH     | Part 2, §9.2     |
| CMD-062                                          | Status      | `EXECUTING` - Command currently executing                   | Unit        | HIGH     | Part 2, §9.2     |
| CMD-063                                          | Status      | `COMPLETED` - Command successfully completed                | Unit        | HIGH     | Part 2, §9.2     |
| CMD-064                                          | Status      | `FAILED` - Command failed                                   | Unit        | HIGH     | Part 2, §9.2     |
| CMD-065                                          | Status      | `CANCELED` - Command canceled                               | Unit        | HIGH     | Part 2, §9.2     |
| **Associations**                                 |
| CMD-070                                          | Association | `controlstream` links to parent control stream              | Integration | HIGH     | Part 2, §9.2     |
| CMD-071                                          | Association | `samplingFeature` links to sampling feature if present      | Integration | MEDIUM   | Part 2, §9.2     |
| CMD-072                                          | Association | `procedure` links to procedure if present                   | Integration | LOW      | Part 2, §9.2     |
| CMD-073                                          | Association | `status` array links to command status resources            | Integration | HIGH     | Part 2, §9.2     |
| CMD-074                                          | Association | `result` array links to command result resources            | Integration | HIGH     | Part 2, §9.2     |
| **Error Conditions**                             |
| CMD-080                                          | Error       | 404 for non-existent command ID                             | Unit        | MEDIUM   | Part 2, §5.5     |
| CMD-081                                          | Error       | 400 for invalid query parameters                            | Unit        | MEDIUM   | Part 2, §5.4     |
| CMD-082                                          | Error       | 422 for parameters not matching schema                      | Unit        | HIGH     | Part 2, §9.2     |

**Total Commands Requirements:** 40+ testable requirements

---

## 3. Query Parameter Requirements Matrix

### 3.1 Temporal Query Parameters

| Parameter          | Resource Types            | Format                                  | Required/Optional | Validation Rules                                               | Example                                     | Spec Reference         |
| ------------------ | ------------------------- | --------------------------------------- | ----------------- | -------------------------------------------------------------- | ------------------------------------------- | ---------------------- |
| **phenomenonTime** | DataStreams, Observations | ISO 8601 instant or interval            | Optional          | Valid instant or interval format, supports open intervals      | `2024-01-01/2024-01-31`                     | Part 2, Req 45, 48     |
| **resultTime**     | DataStreams, Observations | ISO 8601 instant, interval, or `latest` | Optional          | Valid instant/interval, special value `latest` for most recent | `2024-01-01T00:00:00Z` or `latest`          | Part 2, Req 46, 49, 50 |
| **validTime**      | Systems, Deployments      | ISO 8601 instant or interval            | Optional          | Valid instant or interval format per Part 1 Req 3              | `2024-01-01/..`                             | Part 1, Req 3          |
| **executionTime**  | ControlStreams, Commands  | ISO 8601 instant or interval            | Optional          | Valid instant or interval format                               | `2024-01-15T12:00:00Z/2024-01-15T13:00:00Z` | Part 2, Req 53, 57     |
| **issueTime**      | ControlStreams, Commands  | ISO 8601 instant or interval            | Optional          | Valid instant or interval format                               | `2024-01-01/2024-01-31`                     | Part 2, Req 52, 56     |
| **datetime**       | All (via OGC API Common)  | ISO 8601 instant or interval            | Optional          | Valid instant or interval format, applies to `validTime`       | `2024-01-01/2024-01-31`                     | OGC API Common         |

**Temporal Format Validation Rules:**

| Format Type     | Pattern                | Example                    | Test Type | Priority     |
| --------------- | ---------------------- | -------------------------- | --------- | ------------ |
| Instant         | `YYYY-MM-DDTHH:MM:SSZ` | `2024-01-15T12:00:00Z`     | Unit      | **CRITICAL** |
| Closed Interval | `instant/instant`      | `2024-01-01/2024-01-31`    | Unit      | **CRITICAL** |
| Open Start      | `../instant`           | `../2024-01-31`            | Unit      | HIGH         |
| Open End        | `instant/..`           | `2024-01-01/..`            | Unit      | HIGH         |
| Duration Start  | `instant/duration`     | `2024-01-01/P1M`           | Unit      | MEDIUM       |
| Duration End    | `duration/instant`     | `P1M/2024-01-31`           | Unit      | MEDIUM       |
| Special Value   | `latest`               | `latest` (resultTime only) | Unit      | **CRITICAL** |

### 3.2 Spatial Query Parameters

| Parameter    | Resource Types        | Format            | Required/Optional | Validation Rules                                             | Example                                      | Spec Reference   |
| ------------ | --------------------- | ----------------- | ----------------- | ------------------------------------------------------------ | -------------------------------------------- | ---------------- |
| **bbox**     | All spatial resources | WGS84 coordinates | Optional          | 4 or 6 values, minLon,minLat,maxLon,maxLat[,minElev,maxElev] | `-180,-90,180,90`                            | OGC API Common   |
| **geometry** | All spatial resources | WKT or GeoJSON    | Optional          | Valid WKT or GeoJSON geometry                                | `POLYGON((...))`                             | OGC API Features |
| **bbox-crs** | All spatial resources | CRS URI           | Optional          | Valid CRS URI, default WGS84                                 | `http://www.opengis.net/def/crs/EPSG/0/4326` | OGC API Features |

**Spatial Validation Rules:**

| Rule     | Description                                          | Test Type | Priority     |
| -------- | ---------------------------------------------------- | --------- | ------------ |
| BBOX-001 | bbox must have 4 or 6 numeric values                 | Unit      | **CRITICAL** |
| BBOX-002 | minLon < maxLon, minLat < maxLat                     | Unit      | **CRITICAL** |
| BBOX-003 | Coordinates within valid WGS84 range                 | Unit      | HIGH         |
| GEOM-001 | geometry must be valid WKT or GeoJSON                | Unit      | HIGH         |
| GEOM-002 | Geometry type supported (Point, LineString, Polygon) | Unit      | MEDIUM       |

### 3.3 Filtering Parameters

| Parameter              | Resource Types                                                  | Format       | Required/Optional | Validation Rules                                                            | Example                                                      | Spec Reference               |
| ---------------------- | --------------------------------------------------------------- | ------------ | ----------------- | --------------------------------------------------------------------------- | ------------------------------------------------------------ | ---------------------------- |
| **systemType**         | Systems                                                         | URI or CURIE | Optional          | Value from controlled vocabulary (Table 6)                                  | `sosa:Sensor`                                                | Part 1, Table 6              |
| **assetType**          | Systems                                                         | Enum         | Optional          | Value from enum (Table 7)                                                   | `Equipment`                                                  | Part 1, Table 7              |
| **observedProperty**   | DataStreams                                                     | URI list     | Optional          | Comma-separated valid URIs                                                  | `http://example.org/temperature,http://example.org/pressure` | Part 2, Req 47               |
| **controlledProperty** | ControlStreams                                                  | URI list     | Optional          | Comma-separated valid URIs                                                  | `http://example.org/valve-position`                          | Part 2, Req 54               |
| **foi**                | DataStreams, Observations, ControlStreams, Commands             | URI          | Optional          | Valid URI reference to feature of interest                                  | `http://example.org/features/building-1`                     | Part 2, Req 51, 58           |
| **parent**             | Systems, Deployments                                            | ID           | Optional          | Valid parent resource ID                                                    | `sys-123`                                                    | Part 1, Advanced Filtering   |
| **system**             | Deployments, SamplingFeatures, DataStreams, ControlStreams      | ID           | Optional          | Valid system ID                                                             | `sys-123`                                                    | Part 1/2, Advanced Filtering |
| **deployment**         | DataStreams, ControlStreams                                     | ID           | Optional          | Valid deployment ID                                                         | `dep-456`                                                    | Part 2, Advanced Filtering   |
| **procedure**          | Systems, Deployments, DataStreams, Observations, ControlStreams | ID           | Optional          | Valid procedure ID                                                          | `proc-789`                                                   | Part 1/2, Advanced Filtering |
| **datastream**         | Observations                                                    | ID           | Optional          | Valid datastream ID                                                         | `ds-101`                                                     | Part 2, Advanced Filtering   |
| **controlstream**      | Commands                                                        | ID           | Optional          | Valid control stream ID                                                     | `cs-202`                                                     | Part 2, Advanced Filtering   |
| **sampledFeature**     | SamplingFeatures                                                | URI          | Optional          | Valid FOI URI                                                               | `http://example.org/features/river-1`                        | Part 1, Advanced Filtering   |
| **statusCode**         | CommandStatus                                                   | Enum         | Optional          | Value from enum (PENDING, ACCEPTED, EXECUTING, COMPLETED, FAILED, CANCELED) | `COMPLETED`                                                  | Part 2, Req 59               |

### 3.4 Pagination Parameters

| Parameter  | Resource Types | Format  | Required/Optional | Validation Rules                      | Example | Spec Reference   |
| ---------- | -------------- | ------- | ----------------- | ------------------------------------- | ------- | ---------------- |
| **limit**  | All            | Integer | Optional          | Integer > 0, typically default 10-100 | `50`    | OGC API Features |
| **offset** | All            | Integer | Optional          | Integer >= 0                          | `100`   | OGC API Features |

### 3.5 Hierarchical Query Parameters

| Parameter     | Resource Types                                     | Format  | Required/Optional | Validation Rules                   | Example | Spec Reference     |
| ------------- | -------------------------------------------------- | ------- | ----------------- | ---------------------------------- | ------- | ------------------ |
| **recursive** | Systems (subsystems), Deployments (subdeployments) | Boolean | Optional          | `true` or `false`, default `false` | `true`  | Part 1, Req 10, 20 |

**Recursive Behavior Rules:**

| Rule    | Description                                               | Test Type   | Priority |
| ------- | --------------------------------------------------------- | ----------- | -------- |
| REC-001 | `recursive=false` or omitted returns direct children only | Integration | HIGH     |
| REC-002 | `recursive=true` returns all nested descendants           | Integration | HIGH     |
| REC-003 | Filters apply to all processed resources                  | Integration | HIGH     |
| REC-004 | Nested resource associations include parent resources     | Integration | MEDIUM   |

### 3.6 Format Negotiation Parameters

| Parameter     | Resource Types       | Format     | Required/Optional   | Validation Rules                          | Example                | Spec Reference |
| ------------- | -------------------- | ---------- | ------------------- | ----------------------------------------- | ---------------------- | -------------- |
| **obsFormat** | DataStream schema    | Media type | Required for schema | Valid media type for observation encoding | `application/swe+json` | Part 2, Req 11 |
| **cmdFormat** | ControlStream schema | Media type | Required for schema | Valid media type for command encoding     | `application/swe+json` | Part 2, Req 25 |

**Supported Format Values:**

| Format                | Media Type                 | Applies To             | Priority     |
| --------------------- | -------------------------- | ---------------------- | ------------ |
| SWE Common JSON       | `application/swe+json`     | Observations, Commands | **CRITICAL** |
| O&M JSON              | `application/om+json`      | Observations           | HIGH         |
| SWE Common Text (CSV) | `text/csv`                 | Observations           | MEDIUM       |
| SWE Common Binary     | `application/octet-stream` | Observations           | LOW          |

---

## 4. Error Condition Requirements Matrix

> **⚠️ REVIEW NOTICE (M1):** Error response shapes are useful reference for
> what the client should handle gracefully (404 → return null, 400 → throw
> with message, etc.), but testing that a server returns the exact error
> message pattern is a server concern. Client tests should verify: does the
> client code handle each HTTP status correctly?

| Error Condition            | HTTP Status | Error Detail Required          | Applies To               | Test Type | Spec Reference     |
| -------------------------- | ----------- | ------------------------------ | ------------------------ | --------- | ------------------ |
| **Client Errors (4xx)**    |
| Resource not found         | 404         | Resource type, ID              | All resources            | Unit      | Part 1/2, §5.5     |
| Invalid parameter format   | 400         | Parameter name, reason         | All queries              | Unit      | Part 1/2, §5.4     |
| Missing required parameter | 400         | Parameter name                 | Schema operations        | Unit      | Part 2, §8.4, §9.4 |
| Invalid parameter value    | 400         | Parameter name, allowed values | All queries              | Unit      | Part 1/2, §5.4     |
| Unsupported media type     | 406         | Supported types list           | All resources            | Unit      | Part 1/2, §5.6     |
| Conflict (duplicate UID)   | 409         | Conflicting resource UID       | Create operations        | Unit      | Part 1/2, §5.8     |
| Unprocessable entity       | 422         | Validation errors list         | Create/Update operations | Unit      | Part 1/2, §5.9     |
| Method not allowed         | 405         | Allowed methods list           | Read-only resources      | Unit      | Part 1/2, §5.7     |
| **Server Errors (5xx)**    |
| Internal server error      | 500         | Generic error message          | All operations           | Unit      | Part 1/2, §5.10    |
| Service unavailable        | 503         | Retry-After header             | All operations           | Unit      | Part 1/2, §5.11    |

**Detailed Error Scenarios:**

### 4.1 Parameter Validation Errors (400)

| Scenario                | Parameter                                                       | Error Message Pattern                                                     | Test Type | Priority |
| ----------------------- | --------------------------------------------------------------- | ------------------------------------------------------------------------- | --------- | -------- |
| Invalid temporal format | phenomenonTime, resultTime, validTime, executionTime, issueTime | "Invalid {param} format: {value}. Expected ISO 8601 instant or interval." | Unit      | HIGH     |
| Invalid bbox format     | bbox                                                            | "Invalid bbox format: {value}. Expected 4 or 6 numeric values."           | Unit      | HIGH     |
| Invalid bbox range      | bbox                                                            | "Invalid bbox coordinates: minLon={} must be < maxLon={}."                | Unit      | HIGH     |
| Invalid enum value      | systemType, assetType, statusCode                               | "Invalid {param} value: {value}. Allowed values: {list}."                 | Unit      | HIGH     |
| Invalid URI format      | observedProperty, controlledProperty, foi                       | "Invalid {param} URI: {value}. Expected valid URI reference."             | Unit      | MEDIUM   |
| Invalid boolean         | recursive                                                       | "Invalid recursive value: {value}. Expected 'true' or 'false'."           | Unit      | MEDIUM   |
| Invalid integer         | limit, offset                                                   | "Invalid {param} value: {value}. Expected positive integer."              | Unit      | HIGH     |
| Out of range            | limit                                                           | "Invalid limit value: {value}. Must be between 1 and {max}."              | Unit      | MEDIUM   |
| Negative value          | offset                                                          | "Invalid offset value: {value}. Must be >= 0."                            | Unit      | MEDIUM   |

### 4.2 Resource Not Found Errors (404)

| Resource Type    | URL Pattern              | Error Message Pattern                        | Test Type | Priority |
| ---------------- | ------------------------ | -------------------------------------------- | --------- | -------- |
| System           | `/systems/{id}`          | "System with ID '{id}' not found."           | Unit      | MEDIUM   |
| Deployment       | `/deployments/{id}`      | "Deployment with ID '{id}' not found."       | Unit      | MEDIUM   |
| Procedure        | `/procedures/{id}`       | "Procedure with ID '{id}' not found."        | Unit      | LOW      |
| Sampling Feature | `/samplingFeatures/{id}` | "Sampling feature with ID '{id}' not found." | Unit      | MEDIUM   |
| Property         | `/properties/{id}`       | "Property with ID '{id}' not found."         | Unit      | LOW      |
| DataStream       | `/datastreams/{id}`      | "DataStream with ID '{id}' not found."       | Unit      | MEDIUM   |
| Observation      | `/observations/{id}`     | "Observation with ID '{id}' not found."      | Unit      | MEDIUM   |
| ControlStream    | `/controlstreams/{id}`   | "ControlStream with ID '{id}' not found."    | Unit      | MEDIUM   |
| Command          | `/commands/{id}`         | "Command with ID '{id}' not found."          | Unit      | MEDIUM   |

### 4.3 Unprocessable Entity Errors (422)

| Scenario                   | Resource Type | Error Message Pattern                                                    | Test Type | Priority |
| -------------------------- | ------------- | ------------------------------------------------------------------------ | --------- | -------- |
| Missing required property  | All           | "Missing required property: {propertyName}."                             | Unit      | HIGH     |
| Invalid property type      | All           | "Invalid type for property '{name}': expected {expected}, got {actual}." | Unit      | HIGH     |
| Invalid URI format         | Systems, etc. | "Invalid URI format for uniqueIdentifier: {value}."                      | Unit      | HIGH     |
| Procedure with location    | Procedures    | "Procedures must not have a location property (Part 1, Req 24)."         | Unit      | MEDIUM   |
| Result schema mismatch     | Observations  | "Observation result does not match datastream schema."                   | Unit      | HIGH     |
| Parameters schema mismatch | Commands      | "Command parameters do not match control stream schema."                 | Unit      | HIGH     |

---

## 5. Format Validation Requirements

> **⚠️ REVIEW NOTICE (M1):** The validation rules below (VAL-GJ-_, VAL-SML-_,
> VAL-SWE-\*) define what constitutes valid server output. These are useful as
> reference for what properties and structures the parser should expect, but
> should not become individual validation test cases. Parser tests should
> verify: `parse(fixture) → typed output with correct properties extracted`.
> The rules inform fixture design (what variations to include), not test
> case design (what assertions to write).

### 5.1 GeoJSON Validation (RFC 7946 + CSAPI Extensions)

**Conformance Class:** GeoJSON Encoding (`/conf/geojson`)  
**Applies To:** Systems, Deployments, Procedures, Sampling Features

| Validation Rule      | Applies To        | Required/Optional                                          | Test Type | Priority     | Spec Reference  |
| -------------------- | ----------------- | ---------------------------------------------------------- | --------- | ------------ | --------------- |
| **RFC 7946 Core**    |
| VAL-GJ-001           | All               | Feature must be valid GeoJSON                              | Unit      | **CRITICAL** | RFC 7946        |
| VAL-GJ-002           | All               | Feature must have `type="Feature"`                         | Unit      | **CRITICAL** | RFC 7946, §3.2  |
| VAL-GJ-003           | All               | Feature must have `geometry` or `properties` (or both)     | Unit      | **CRITICAL** | RFC 7946, §3.2  |
| VAL-GJ-004           | All               | Geometry must be valid GeoJSON geometry type               | Unit      | HIGH         | RFC 7946, §3.1  |
| VAL-GJ-005           | All               | FeatureCollection must have `type="FeatureCollection"`     | Unit      | **CRITICAL** | RFC 7946, §3.3  |
| VAL-GJ-006           | All               | FeatureCollection must have `features` array               | Unit      | **CRITICAL** | RFC 7946, §3.3  |
| **CSAPI Extensions** |
| VAL-GJ-010           | All               | Feature `id` is local identifier (not UID)                 | Unit      | HIGH         | Part 1, Req 1   |
| VAL-GJ-011           | All               | `properties.uniqueIdentifier` must be valid URI            | Unit      | **CRITICAL** | Part 1, Req 2   |
| VAL-GJ-012           | All               | `properties.name` required (non-empty string)              | Unit      | **CRITICAL** | Part 1, §9-15   |
| VAL-GJ-013           | Systems           | `properties.featureType="sosa:System"`                     | Unit      | HIGH         | Part 1, Req 8   |
| VAL-GJ-014           | Deployments       | `properties.featureType="sosa:Deployment"`                 | Unit      | HIGH         | Part 1, Req 18  |
| VAL-GJ-015           | Procedures        | `properties.featureType="sosa:Procedure"`                  | Unit      | HIGH         | Part 1, Req 28  |
| VAL-GJ-016           | Sampling Features | `properties.featureType="sosa:Sample"`                     | Unit      | HIGH         | Part 1, Req 33  |
| VAL-GJ-017           | Procedures        | Feature must NOT have `geometry`                           | Unit      | MEDIUM       | Part 1, Req 24  |
| VAL-GJ-018           | Systems           | `properties.systemType` from controlled vocabulary         | Unit      | HIGH         | Part 1, Table 6 |
| VAL-GJ-019           | Systems           | `properties.assetType` from enum if present                | Unit      | MEDIUM       | Part 1, Table 7 |
| **Associations**     |
| VAL-GJ-020           | All               | Association arrays contain valid links                     | Unit      | MEDIUM       | Part 1/2        |
| VAL-GJ-021           | Systems           | `properties.subsystems` is array of System references      | Unit      | MEDIUM       | Part 1, §9.2    |
| VAL-GJ-022           | Systems           | `properties.datastreams` is array of DataStream references | Unit      | HIGH         | Part 2, §8.2    |

### 5.2 SensorML 3.0 Validation

**Conformance Class:** SensorML Encoding (`/conf/sensorml`)  
**Applies To:** Systems, Deployments, Procedures, Sampling Features

| Validation Rule                    | Applies To          | Required/Optional                                  | Test Type | Priority | Spec Reference     |
| ---------------------------------- | ------------------- | -------------------------------------------------- | --------- | -------- | ------------------ |
| **Core Structure**                 |
| VAL-SML-001                        | All                 | Root element valid SensorML type                   | Unit      | HIGH     | SensorML 3.0       |
| VAL-SML-002                        | Systems             | PhysicalSystem, AggregateProcess, or SimpleProcess | Unit      | HIGH     | SensorML 3.0, §7   |
| VAL-SML-003                        | Procedures          | PhysicalComponent or SimpleProcess                 | Unit      | MEDIUM   | SensorML 3.0, §7   |
| **Identification**                 |
| VAL-SML-010                        | Systems, Procedures | System must have `identification` section          | Unit      | HIGH     | SensorML 3.0, §7.2 |
| VAL-SML-011                        | Systems, Procedures | `uniqueID` identifier required                     | Unit      | HIGH     | SensorML 3.0, §7.2 |
| VAL-SML-012                        | Systems, Procedures | `uniqueID` must be valid URI                       | Unit      | HIGH     | Part 1, Req 2      |
| VAL-SML-013                        | Systems, Procedures | `shortName` or `longName` required                 | Unit      | HIGH     | SensorML 3.0, §7.2 |
| **Classification**                 |
| VAL-SML-020                        | Systems             | `classification` section for systemType            | Unit      | MEDIUM   | SensorML 3.0, §7.3 |
| VAL-SML-021                        | Systems             | systemType classifier from Table 6 vocabulary      | Unit      | MEDIUM   | Part 1, Table 6    |
| **Components (Aggregate Systems)** |
| VAL-SML-030                        | Systems (Aggregate) | `components` section references valid systems      | Unit      | MEDIUM   | SensorML 3.0, §8.3 |
| VAL-SML-031                        | Systems (Aggregate) | Component links valid (internal or external)       | Unit      | MEDIUM   | SensorML 3.0, §8.3 |
| **Capabilities**                   |
| VAL-SML-040                        | Systems             | `capabilities` section valid DataRecord            | Unit      | LOW      | SensorML 3.0, §7.5 |
| **Characteristics**                |
| VAL-SML-050                        | Systems             | `characteristics` section valid DataRecord         | Unit      | LOW      | SensorML 3.0, §7.6 |

### 5.3 SWE Common 3.0 Validation

**Conformance Class:** SWE Common Encoding (`/conf/swecommon`)  
**Applies To:** Observations, Commands (result and parameter schemas)

| Validation Rule                     | Applies To            | Required/Optional                                    | Test Type | Priority     | Spec Reference        |
| ----------------------------------- | --------------------- | ---------------------------------------------------- | --------- | ------------ | --------------------- |
| **DataRecord Structure**            |
| VAL-SWE-001                         | Schemas               | DataRecord must have `fields` array                  | Unit      | **CRITICAL** | SWE Common 3.0, §7.2  |
| VAL-SWE-002                         | Schemas               | Each field must have `name` and valid component      | Unit      | **CRITICAL** | SWE Common 3.0, §7.2  |
| VAL-SWE-003                         | Schemas               | Field names unique within DataRecord                 | Unit      | HIGH         | SWE Common 3.0, §7.2  |
| **Quantity (Numeric Values)**       |
| VAL-SWE-010                         | Numeric observations  | Quantity must have `uom` (unit of measure)           | Unit      | **CRITICAL** | SWE Common 3.0, §8.1  |
| VAL-SWE-011                         | Numeric observations  | `uom.code` valid UCUM code                           | Unit      | HIGH         | SWE Common 3.0, §8.1  |
| VAL-SWE-012                         | Numeric observations  | `value` is numeric                                   | Unit      | **CRITICAL** | SWE Common 3.0, §8.1  |
| **Text (String Values)**            |
| VAL-SWE-020                         | Text observations     | Text `value` is string                               | Unit      | **CRITICAL** | SWE Common 3.0, §8.2  |
| VAL-SWE-021                         | Text observations     | Text `constraint` valid if present                   | Unit      | MEDIUM       | SWE Common 3.0, §8.2  |
| **Boolean**                         |
| VAL-SWE-030                         | Boolean observations  | Boolean `value` is true/false                        | Unit      | HIGH         | SWE Common 3.0, §8.3  |
| **Category (Coded Values)**         |
| VAL-SWE-040                         | Category observations | Category has `codeSpace` reference                   | Unit      | HIGH         | SWE Common 3.0, §8.4  |
| VAL-SWE-041                         | Category observations | `value` from defined code space                      | Unit      | MEDIUM       | SWE Common 3.0, §8.4  |
| **Time**                            |
| VAL-SWE-050                         | Temporal observations | Time `value` valid ISO 8601                          | Unit      | **CRITICAL** | SWE Common 3.0, §8.5  |
| VAL-SWE-051                         | Temporal observations | Time `uom.code` valid temporal unit                  | Unit      | HIGH         | SWE Common 3.0, §8.5  |
| **DataArray (Multi-Value Results)** |
| VAL-SWE-060                         | Array observations    | DataArray has `elementType`                          | Unit      | **CRITICAL** | SWE Common 3.0, §9.1  |
| VAL-SWE-061                         | Array observations    | DataArray has `encoding`                             | Unit      | **CRITICAL** | SWE Common 3.0, §9.1  |
| VAL-SWE-062                         | Array observations    | DataArray `values` matches encoding and element type | Unit      | **CRITICAL** | SWE Common 3.0, §9.1  |
| **Encoding**                        |
| VAL-SWE-070                         | Encoded observations  | TextEncoding valid (tokenSeparator, blockSeparator)  | Unit      | HIGH         | SWE Common 3.0, §10.1 |
| VAL-SWE-071                         | Encoded observations  | BinaryEncoding valid (byteOrder, byteLength)         | Unit      | MEDIUM       | SWE Common 3.0, §10.2 |
| VAL-SWE-072                         | Encoded observations  | JSONEncoding valid                                   | Unit      | **CRITICAL** | SWE Common 3.0, §10.3 |

---

## 6. Specification Examples Fixture Inventory

**Purpose:** Catalog all specification examples that can be extracted as test fixtures

### 6.1 Part 1 Examples

| Spec Section    | Example Type | Resource Type      | Format                    | Usable as Fixture | Notes                                                                     |
| --------------- | ------------ | ------------------ | ------------------------- | ----------------- | ------------------------------------------------------------------------- |
| Part 1, §9.2    | Response     | System             | GeoJSON                   | ✅ Yes            | Complete weather station system with all properties                       |
| Part 1, §9.2    | Response     | System (Sensor)    | GeoJSON                   | ✅ Yes            | Temperature sensor with minimal properties                                |
| Part 1, §9.2    | Response     | System (Platform)  | GeoJSON                   | ✅ Yes            | UAV platform with subsystems                                              |
| Part 1, §10.2   | Response     | Subsystems         | GeoJSON FeatureCollection | ✅ Yes            | List of subsystems for platform                                           |
| Part 1, §11.2   | Response     | Deployment         | GeoJSON                   | ✅ Yes            | System deployment with validTime and geometry                             |
| Part 1, §11.2   | Response     | Deployment         | GeoJSON                   | ✅ Yes            | Multi-system deployment example                                           |
| Part 1, §13.2   | Response     | Procedure          | GeoJSON                   | ✅ Yes            | Measurement procedure (no geometry)                                       |
| Part 1, §14.2   | Response     | Sampling Feature   | GeoJSON                   | ✅ Yes            | Water sampling station                                                    |
| Part 1, §15.2   | Response     | Property           | JSON                      | ✅ Yes            | Observed property definition                                              |
| Part 1, Annex B | Response     | System             | SensorML JSON             | ✅ Yes            | Complete PhysicalSystem with identification, classification, capabilities |
| Part 1, Annex B | Response     | System (Aggregate) | SensorML JSON             | ✅ Yes            | AggregateProcess with components array                                    |

### 6.2 Part 2 Examples

| Spec Section    | Example Type | Resource Type     | Format                | Usable as Fixture | Notes                                                       |
| --------------- | ------------ | ----------------- | --------------------- | ----------------- | ----------------------------------------------------------- |
| Part 2, §8.2    | Response     | DataStream        | JSON                  | ✅ Yes            | Temperature datastream with schema reference                |
| Part 2, §8.2    | Response     | DataStream        | JSON                  | ✅ Yes            | Multi-property datastream (temperature, humidity, pressure) |
| Part 2, §8.3    | Response     | Observations      | SWE Common JSON       | ✅ Yes            | DataArray with 5 temperature observations                   |
| Part 2, §8.3    | Response     | Observations      | SWE Common JSON       | ✅ Yes            | Multi-property observations (3 fields)                      |
| Part 2, §8.3    | Response     | Observation       | SWE Common JSON       | ✅ Yes            | Single observation with DataRecord result                   |
| Part 2, §8.4    | Response     | DataStream Schema | SWE Common JSON       | ✅ Yes            | DataRecord schema for multi-property observations           |
| Part 2, §9.2    | Response     | ControlStream     | JSON                  | ✅ Yes            | Valve control stream                                        |
| Part 2, §9.2    | Response     | Command           | SWE Common JSON       | ✅ Yes            | Set valve position command                                  |
| Part 2, §9.2    | Response     | CommandStatus     | JSON                  | ✅ Yes            | Command status sequence (PENDING → EXECUTING → COMPLETED)   |
| Part 2, §9.2    | Response     | CommandResult     | SWE Common JSON       | ✅ Yes            | Command execution result                                    |
| Part 2, Annex B | Response     | Observations      | SWE Common Text (CSV) | ✅ Yes            | Time-series observations in CSV format                      |
| Part 2, Annex B | Response     | Observations      | SWE Common Binary     | ⚠️ Partial        | Binary-encoded observations (complex to parse)              |

**Total Spec Examples:** 25+ examples usable as fixtures

**Fixture Extraction Strategy:**

1. Copy examples verbatim from specification documents
2. Add provenance metadata (`_source`, `_spec_url`, `_section`)
3. Validate examples against JSON schemas
4. Organize by resource type and format
5. Create variations for edge cases not covered by spec examples

---

## 7. OpenAPI Schema Requirements

**Source:** Part 1 OpenAPI (6,442 lines), Part 2 OpenAPI (bundled)

### 7.1 Part 1 Schemas

| Schema Name                   | Purpose                         | Properties Count | Key Validation Rules                                                  | Notes                       |
| ----------------------------- | ------------------------------- | ---------------- | --------------------------------------------------------------------- | --------------------------- |
| **System**                    | System resource                 | 15+              | `uniqueIdentifier` URI, `systemType` vocab, `name` required           | Core schema for systems     |
| **SystemCollection**          | Collection of systems           | 3                | `features` array, `featureType=sosa:System`                           | GeoJSON FeatureCollection   |
| **Deployment**                | Deployment resource             | 12+              | `uniqueIdentifier` URI, `validTime` interval, `deployedSystems` array | Temporal/spatial deployment |
| **DeploymentCollection**      | Collection of deployments       | 3                | `features` array, `featureType=sosa:Deployment`                       | GeoJSON FeatureCollection   |
| **Procedure**                 | Procedure resource              | 10+              | `uniqueIdentifier` URI, `procedureType` vocab, NO `geometry`          | No location allowed         |
| **ProcedureCollection**       | Collection of procedures        | 3                | `features` array, `featureType=sosa:Procedure`                        | GeoJSON FeatureCollection   |
| **SamplingFeature**           | Sampling feature resource       | 12+              | `uniqueIdentifier` URI, `sampledFeature` URI, `geometry` required     | Links systems to FOIs       |
| **SamplingFeatureCollection** | Collection of sampling features | 3                | `features` array, `featureType=sosa:Sample`                           | GeoJSON FeatureCollection   |
| **Property**                  | Property definition resource    | 8+               | `uniqueIdentifier` URI, `definition` URI, `name` required             | Non-feature resource        |
| **PropertyCollection**        | Collection of properties        | 3                | `resources` array, `itemType=sosa:Property`                           | Non-feature collection      |

### 7.2 Part 2 Schemas

| Schema Name                 | Purpose                       | Properties Count | Key Validation Rules                                                        | Notes                  |
| --------------------------- | ----------------------------- | ---------------- | --------------------------------------------------------------------------- | ---------------------- |
| **DataStream**              | DataStream resource           | 15+              | `uniqueIdentifier` URI, `observedProperties` array, `system` link           | Observation container  |
| **DataStreamCollection**    | Collection of datastreams     | 3                | `resources` array, `itemType=DataStream`                                    | Non-feature collection |
| **Observation**             | Observation resource          | 10+              | `phenomenonTime` datetime, `resultTime` datetime, `result` matches schema   | Dynamic data           |
| **ObservationCollection**   | Collection of observations    | 3                | `resources` array, `itemType=Observation`                                   | Non-feature collection |
| **ControlStream**           | ControlStream resource        | 12+              | `uniqueIdentifier` URI, `controlledProperties` array, `system` link         | Command container      |
| **ControlStreamCollection** | Collection of control streams | 3                | `resources` array, `itemType=ControlStream`                                 | Non-feature collection |
| **Command**                 | Command resource              | 12+              | `issueTime` datetime, `executionTime` datetime, `parameters` matches schema | Command to system      |
| **CommandCollection**       | Collection of commands        | 3                | `resources` array, `itemType=Command`                                       | Non-feature collection |
| **CommandStatus**           | Command status resource       | 8+               | `reportTime` datetime, `statusCode` enum, `percentCompletion` 0-100         | Status tracking        |
| **CommandResult**           | Command result resource       | 8+               | `result` matches schema, `completionTime` datetime                          | Execution result       |
| **SWECommonDataRecord**     | SWE Common data schema        | Variable         | `fields` array, each field has `name` and component                         | Schema definition      |
| **SWECommonDataArray**      | SWE Common array schema       | Variable         | `elementType`, `encoding`, `values`                                         | Multi-value results    |

**Total OpenAPI Schemas:** 40+ schemas across Parts 1 & 2

---

## 8. Endpoint Requirements Matrix

### 8.1 Part 1 Canonical Endpoints

| Endpoint                                 | HTTP Methods            | Request Parameters                  | Response Format            | Error Responses | Spec Reference     |
| ---------------------------------------- | ----------------------- | ----------------------------------- | -------------------------- | --------------- | ------------------ |
| **Core API Endpoints**                   |
| `/`                                      | GET                     | None                                | JSON (landing page)        | 500             | OGC API Common     |
| `/conformance`                           | GET                     | None                                | JSON (conformance classes) | 500             | OGC API Common     |
| `/collections`                           | GET                     | bbox, datetime, limit               | JSON (collections list)    | 400, 500        | OGC API Features   |
| `/collections/{collectionId}`            | GET                     | None                                | JSON (collection info)     | 404, 500        | OGC API Features   |
| **Systems Endpoints**                    |
| `/systems`                               | GET, POST               | bbox, systemType, limit, recursive  | GeoJSON FeatureCollection  | 400, 500        | Part 1, §9.3-9.4   |
| `/systems/{id}`                          | GET, PUT, PATCH, DELETE | None                                | GeoJSON Feature            | 404, 422, 500   | Part 1, §9.3-9.6   |
| `/systems/{parentId}/subsystems`         | GET, POST               | limit, recursive                    | GeoJSON FeatureCollection  | 404, 400, 500   | Part 1, §10.3-10.4 |
| **Deployments Endpoints**                |
| `/deployments`                           | GET, POST               | bbox, datetime, system, limit       | GeoJSON FeatureCollection  | 400, 500        | Part 1, §11.3-11.4 |
| `/deployments/{id}`                      | GET, PUT, PATCH, DELETE | None                                | GeoJSON Feature            | 404, 422, 500   | Part 1, §11.3-11.6 |
| `/deployments/{parentId}/subdeployments` | GET, POST               | limit, recursive                    | GeoJSON FeatureCollection  | 404, 400, 500   | Part 1, §12.3-12.4 |
| `/systems/{sysId}/deployments`           | GET                     | limit                               | GeoJSON FeatureCollection  | 404, 400, 500   | Part 1, §11.3      |
| **Procedures Endpoints**                 |
| `/procedures`                            | GET, POST               | procedureType, limit                | GeoJSON FeatureCollection  | 400, 500        | Part 1, §13.3-13.4 |
| `/procedures/{id}`                       | GET, PUT, PATCH, DELETE | None                                | GeoJSON Feature            | 404, 422, 500   | Part 1, §13.3-13.6 |
| **Sampling Features Endpoints**          |
| `/samplingFeatures`                      | GET, POST               | bbox, system, sampledFeature, limit | GeoJSON FeatureCollection  | 400, 500        | Part 1, §14.3-14.4 |
| `/samplingFeatures/{id}`                 | GET, PUT, PATCH, DELETE | None                                | GeoJSON Feature            | 404, 422, 500   | Part 1, §14.3-14.6 |
| `/systems/{sysId}/samplingFeatures`      | GET, POST               | limit                               | GeoJSON FeatureCollection  | 404, 400, 500   | Part 1, §14.3-14.4 |
| **Properties Endpoints**                 |
| `/properties`                            | GET, POST               | limit                               | JSON ResourceCollection    | 400, 500        | Part 1, §15.3-15.4 |
| `/properties/{id}`                       | GET, PUT, PATCH, DELETE | None                                | JSON Resource              | 404, 422, 500   | Part 1, §15.3-15.6 |

### 8.2 Part 2 Canonical Endpoints

| Endpoint                              | HTTP Methods     | Request Parameters                                                      | Response Format             | Error Responses | Spec Reference   |
| ------------------------------------- | ---------------- | ----------------------------------------------------------------------- | --------------------------- | --------------- | ---------------- |
| **DataStreams Endpoints**             |
| `/datastreams`                        | GET, POST        | system, deployment, observedProperty, phenomenonTime, resultTime, limit | JSON ResourceCollection     | 400, 500        | Part 2, §8.3-8.4 |
| `/datastreams/{id}`                   | GET, PUT, DELETE | None                                                                    | JSON Resource               | 404, 422, 500   | Part 2, §8.3-8.6 |
| `/datastreams/{id}/schema`            | GET              | obsFormat (required)                                                    | SWE Common JSON             | 400, 404, 500   | Part 2, §8.4     |
| `/systems/{sysId}/datastreams`        | GET, POST        | limit, phenomenonTime, resultTime, observedProperty                     | JSON ResourceCollection     | 404, 400, 500   | Part 2, §8.3-8.4 |
| `/deployments/{depId}/datastreams`    | GET              | limit                                                                   | JSON ResourceCollection     | 404, 400, 500   | Part 2, §8.3     |
| **Observations Endpoints**            |
| `/observations`                       | GET, POST        | datastream, phenomenonTime, resultTime, foi, limit, offset              | JSON ResourceCollection     | 400, 500        | Part 2, §8.3-8.4 |
| `/observations/{id}`                  | GET, DELETE      | None                                                                    | JSON Resource               | 404, 500        | Part 2, §8.3-8.6 |
| `/datastreams/{dsId}/observations`    | GET, POST        | phenomenonTime, resultTime, foi, limit, offset                          | JSON ResourceCollection     | 404, 400, 500   | Part 2, §8.3-8.4 |
| **ControlStreams Endpoints**          |
| `/controlstreams`                     | GET, POST        | system, deployment, controlledProperty, issueTime, executionTime, limit | JSON ResourceCollection     | 400, 500        | Part 2, §9.3-9.4 |
| `/controlstreams/{id}`                | GET, PUT, DELETE | None                                                                    | JSON Resource               | 404, 422, 500   | Part 2, §9.3-9.6 |
| `/controlstreams/{id}/schema`         | GET              | cmdFormat (required)                                                    | SWE Common JSON             | 400, 404, 500   | Part 2, §9.4     |
| `/systems/{sysId}/controlstreams`     | GET, POST        | limit, issueTime, executionTime, controlledProperty                     | JSON ResourceCollection     | 404, 400, 500   | Part 2, §9.3-9.4 |
| `/deployments/{depId}/controlstreams` | GET              | limit                                                                   | JSON ResourceCollection     | 404, 400, 500   | Part 2, §9.3     |
| **Commands Endpoints**                |
| `/commands`                           | GET, POST        | controlstream, issueTime, executionTime, foi, limit                     | JSON ResourceCollection     | 400, 500        | Part 2, §9.3-9.4 |
| `/commands/{id}`                      | GET, DELETE      | None                                                                    | JSON Resource               | 404, 500        | Part 2, §9.3-9.6 |
| `/commands/{cmdId}/status`            | GET, POST        | None                                                                    | JSON CommandStatus or array | 404, 400, 500   | Part 2, §9.3-9.4 |
| `/commands/{cmdId}/result`            | GET, POST        | None                                                                    | JSON CommandResult or array | 404, 400, 500   | Part 2, §9.3-9.4 |
| `/controlstreams/{csId}/commands`     | GET, POST        | issueTime, executionTime, foi, limit                                    | JSON ResourceCollection     | 404, 400, 500   | Part 2, §9.3-9.4 |

**Total Endpoints:** 50+ endpoints across Parts 1 & 2

---

## 9. Test Type Mapping

> **⚠️ REVIEW NOTICE (Phase 2D, C1):** The mapping below is useful as general guidance for how different categories of client code should be tested, but the specific "Example Test" entries often describe server-validation tests (e.g., "Validate `uniqueIdentifier` is valid URI" tests server data correctness, not client behavior). When using this table, reinterpret examples as client-behavior tests: e.g., "Encode `phenomenonTime` interval to URL param" is a genuine client test; "Validate 404 error includes resource type" is not.

**Purpose:** Map each requirement category to appropriate test types (unit/integration/e2e)

| Requirement Category           | Test Type   | Example Test                                  | Priority     | Rationale                                         |
| ------------------------------ | ----------- | --------------------------------------------- | ------------ | ------------------------------------------------- |
| **Property Validation**        | Unit        | Validate `uniqueIdentifier` is valid URI      | **CRITICAL** | Isolated property rules, no external dependencies |
| **Query Parameter Encoding**   | Unit        | Encode `phenomenonTime` interval to URL param | HIGH         | Pure string serialization logic                   |
| **Query Parameter Validation** | Unit        | Reject invalid `bbox` format                  | HIGH         | Input validation, no HTTP calls                   |
| **Error Response Structure**   | Unit        | Validate 404 error includes resource type     | MEDIUM       | Expected error format, no integration             |
| **Format Serialization**       | Unit        | Serialize System to GeoJSON                   | HIGH         | Format conversion logic, no HTTP                  |
| **Format Parsing**             | Unit        | Parse SWE Common DataRecord to TypeScript     | **CRITICAL** | Format conversion logic, no HTTP                  |
| **Schema Validation**          | Unit        | Validate observation result matches schema    | **CRITICAL** | Schema matching logic                             |
| **Multi-Component Workflows**  | Integration | QueryBuilder + helpers create correct URL     | HIGH         | 2-3 components, mocked HTTP                       |
| **Resource Relationships**     | Integration | System → DataStreams navigation               | HIGH         | Multi-resource traversal, mocked HTTP             |
| **Caching Behavior**           | Integration | Same collection ID returns cached builder     | MEDIUM       | State management across calls                     |
| **Pagination**                 | Integration | Follow `next` link for additional results     | MEDIUM       | Multi-request workflow                            |
| **Complete User Workflows**    | E2E         | Discovery → Observation Query → Parse Results | **CRITICAL** | All components, realistic scenario                |
| **Error Recovery**             | E2E         | Handle 404 gracefully in multi-step workflow  | MEDIUM       | Error handling across workflow                    |
| **Format Detection**           | Integration | Detect format from URL or Accept header       | MEDIUM       | Multi-component (URL builder + format detector)   |

**Test Distribution Guidance:**

- **Unit Tests (55-60%):** Property validation, parameter encoding, format serialization/parsing, schema validation, error structure
- **Integration Tests (25-30%):** Multi-component workflows, resource relationships, caching, pagination, format detection
- **E2E Tests (10-15%):** Complete workflows (discovery, observation query, command submission, cross-resource navigation)

---

## 10. Requirement-to-Test Traceability Framework

> **⚠️ REVIEW NOTICE (Phase 2D, C1):** This section proposed mapping 334 specification requirement IDs (SYS-001, DS-050, etc.) directly to test cases. This is anti-pattern AP3 (OGC Requirement Traceability) — it organizes tests by specification structure rather than by client code modules. **Do not use this framework.** Tests should be organized around CSAPIQueryBuilder methods, parser functions, and conformance detection logic. The requirement IDs below are specification references, not test case identifiers.
>
> The "Conformance Claim Validation" concept in Section 11 is also a server concern — client libraries do not claim OGC conformance; servers do.

**Original Purpose:** Establish traceability from specification requirements to test implementation

### Traceability Matrix Structure (NOT RECOMMENDED — see notice above)

```markdown
| Requirement ID | Spec Reference | Description                        | Test File                    | Test Case(s)                                                                        | Status  |
| -------------- | -------------- | ---------------------------------- | ---------------------------- | ----------------------------------------------------------------------------------- | ------- |
| SYS-001        | Part 1, Req 2  | uniqueIdentifier must be valid URI | systems.spec.ts              | "should validate uniqueIdentifier is valid URI", "should reject invalid URI format" | Planned |
| SYS-010        | Part 1, Req 5  | System accessible at canonical URL | endpoint.integration.spec.ts | "should access system at canonical URL"                                             | Planned |
| DS-050         | Part 2, Req 45 | phenomenonTime temporal filter     | datastreams.spec.ts          | "should filter by phenomenonTime interval", "should handle open intervals"          | Planned |
```

**Status Values:**

- **Planned:** Requirement identified, test not yet implemented
- **Implemented:** Test code written
- **Passing:** Test implemented and passing
- **Failing:** Test implemented but failing (bug or incomplete implementation)
- **Blocked:** Test cannot be implemented until dependency resolved

### Coverage Reporting

For each conformance class, track:

- Total requirements count
- Requirements with tests (planned + implemented)
- Requirements fully covered (tests passing)
- Coverage percentage

**Example:**

```markdown
### Conformance Class: Systems (`/conf/system`)

**Total Requirements:** 45  
**Requirements with Tests:** 40 (89%)  
**Fully Covered (Passing):** 35 (78%)  
**Status:** ⚠️ 5 requirements without tests, 5 tests failing

**Missing Tests:**

- SYS-026: DELETE system with cascade
- SYS-027: DELETE system cascade behavior validation
- SYS-038: recursive parameter for subsystems (edge cases)
- SUB-004: Recursive associations include parent resources
- SUB-005: Query parameters apply recursively

**Failing Tests:**

- SYS-007: location updates when system moves (implementation bug)
- SYS-040: subsystems array validation (schema issue)
- ...
```

---

## 11. Conformance Claim Validation

> **⚠️ REVIEW NOTICE (Phase 2D, C1):** Conformance claim validation is a **server concern**, not a client library concern. OGC conformance classes define what a server implementation must support. A client library does not "claim conformance" — it detects what conformance classes a server supports and adapts its behavior accordingly (see Doc 22 for the correct client-oriented approach to conformance). The table below is retained as reference for understanding what servers may support, which informs the client's conformance detection logic.

**Original Purpose:** Map conformance classes to test requirements for claiming conformance

| Conformance Class                  | Required Tests                                                       | Test File(s)                                                            | Priority     | Status  |
| ---------------------------------- | -------------------------------------------------------------------- | ----------------------------------------------------------------------- | ------------ | ------- |
| **Part 1 Common**                  | Resource IDs, UIDs, datetime parameters                              | common.spec.ts, endpoint.integration.spec.ts                            | **CRITICAL** | Planned |
| **System Features**                | Systems CRUD, canonical endpoints, collections, property validation  | systems.spec.ts, endpoint.integration.spec.ts                           | **CRITICAL** | Planned |
| **Subsystems**                     | Subsystem navigation, recursive queries, association behavior        | subsystems.spec.ts, systems.integration.spec.ts                         | HIGH         | Planned |
| **Deployment Features**            | Deployments CRUD, system associations, temporal validity             | deployments.spec.ts, endpoint.integration.spec.ts                       | HIGH         | Planned |
| **Subdeployments**                 | Subdeployment hierarchy, recursive queries                           | subdeployments.spec.ts, deployments.integration.spec.ts                 | MEDIUM       | Planned |
| **Procedure Features**             | Procedures CRUD, no location validation                              | procedures.spec.ts, endpoint.integration.spec.ts                        | MEDIUM       | Planned |
| **Sampling Features**              | Sampling features CRUD, system associations, geometry validation     | samplingfeatures.spec.ts, endpoint.integration.spec.ts                  | HIGH         | Planned |
| **Property Definitions**           | Property resources, non-feature operations                           | properties.spec.ts, endpoint.integration.spec.ts                        | MEDIUM       | Planned |
| **Advanced Filtering (Part 1)**    | Relationship filters, hierarchy queries, all query parameters        | filtering.spec.ts, query-builder.spec.ts                                | HIGH         | Planned |
| **Create/Update/Delete**           | POST/PUT/PATCH/DELETE operations, error handling                     | crud.spec.ts, endpoint.integration.spec.ts                              | HIGH         | Planned |
| **GeoJSON Encoding**               | GeoJSON serialization/parsing, RFC 7946 compliance, CSAPI extensions | geojson.spec.ts, formats/geojson-validator.spec.ts                      | **CRITICAL** | Planned |
| **SensorML Encoding**              | SensorML 3.0 serialization/parsing, system descriptions              | sensorml.spec.ts, formats/sensorml-parser.spec.ts                       | HIGH         | Planned |
| **Part 2 Common**                  | Non-feature resources, resource collections                          | common-part2.spec.ts, endpoint.integration.spec.ts                      | **CRITICAL** | Planned |
| **DataStreams & Observations**     | DataStream/Observation CRUD, schema operations, temporal queries     | datastreams.spec.ts, observations.spec.ts, endpoint.integration.spec.ts | **CRITICAL** | Planned |
| **ControlStreams & Commands**      | ControlStream/Command CRUD, status/result tracking                   | controlstreams.spec.ts, commands.spec.ts, endpoint.integration.spec.ts  | HIGH         | Planned |
| **Command Feasibility**            | Feasibility checks, status/result tracking                           | feasibility.spec.ts, commands.integration.spec.ts                       | MEDIUM       | Planned |
| **System Events**                  | System event logging, event type validation                          | system-events.spec.ts, endpoint.integration.spec.ts                     | MEDIUM       | Planned |
| **Advanced Filtering (Part 2)**    | Temporal/spatial filters for observations/commands                   | filtering-part2.spec.ts, query-builder.spec.ts                          | HIGH         | Planned |
| **Create/Replace/Delete (Part 2)** | POST/PUT/DELETE for dynamic resources                                | crud-part2.spec.ts, endpoint.integration.spec.ts                        | HIGH         | Planned |
| **SWE Common Encoding**            | SWE Common JSON/Text/Binary serialization/parsing                    | swecommon.spec.ts, formats/swecommon-parser.spec.ts                     | **CRITICAL** | Planned |

**Original Conformance Validation Process (NOT RECOMMENDED — server concern, not client concern):**

1. For each conformance class, enumerate all normative requirements
2. For each requirement, create corresponding test case(s)
3. Implement tests using appropriate test type (unit/integration/e2e)
4. Verify all tests passing before claiming conformance
5. Document conformance claim with test evidence

**Client-oriented alternative:** Test that the client correctly _detects_ which conformance classes a server supports (via `/conformance` endpoint), and that it enables/disables methods accordingly. See Doc 22 (conformance-capability-testing) for the correct approach.

---

## 12. Testing Priorities

> **⚠️ REVIEW NOTICE (M1):** The priority tiers below and their test line
> estimates (~4,800 lines total) reflect a spec-coverage testing approach.
> Client test volume should be driven by actual parser/QueryBuilder code
> complexity, not by counting spec requirements. The resource type grouping
> and phase sequencing are useful for implementation planning; the line
> estimates are not.

### CRITICAL (Must Have) - Implementation Phase 3-4

**Conformance Classes:**

- Part 1 Common
- System Features
- GeoJSON Encoding
- Part 2 Common
- DataStreams & Observations
- SWE Common Encoding

**Resource Types:**

- Systems (45+ requirements)
- DataStreams (40+ requirements)
- Observations (35+ requirements)

**Query Parameters:**

- phenomenonTime, resultTime (temporal filtering)
- bbox (spatial filtering)
- systemType, observedProperty (entity filtering)
- limit, offset (pagination)

**Formats:**

- GeoJSON validation (30+ rules)
- SWE Common JSON parsing (50+ rules)

**Estimated Test Lines:** ~2,500 lines (60% unit, 30% integration, 10% e2e)

### HIGH (Should Have) - Implementation Phase 5-6

**Conformance Classes:**

- Subsystems
- Deployment Features
- Sampling Features
- Advanced Filtering (Part 1 & 2)
- ControlStreams & Commands
- Create/Update/Delete (Part 1 & 2)
- SensorML Encoding

**Resource Types:**

- Deployments (25+ requirements)
- Sampling Features (20+ requirements)
- ControlStreams (35+ requirements)
- Commands (40+ requirements)

**Query Parameters:**

- validTime, executionTime, issueTime (temporal filtering)
- parent, system, deployment, foi (relationship filtering)
- recursive (hierarchical queries)
- controlledProperty, statusCode (entity filtering)

**Formats:**

- SensorML 3.0 parsing (40+ rules)
- SWE Common Text (CSV) parsing (20+ rules)

**Estimated Test Lines:** ~1,500 lines (60% unit, 30% integration, 10% e2e)

### MEDIUM (Nice to Have) - Implementation Phase 7+

**Conformance Classes:**

- Subdeployments
- Procedure Features
- Property Definitions
- Command Feasibility
- System Events

**Resource Types:**

- Procedures (15+ requirements)
- Properties (15+ requirements)
- Subdeployments (10+ requirements)

**Query Parameters:**

- procedureType, type (entity filtering)
- Advanced parameter combinations

**Formats:**

- SWE Common Binary parsing (complex, low priority)

**Estimated Test Lines:** ~800 lines (60% unit, 30% integration, 10% e2e)

**Total Estimated Test Lines:** ~4,800 lines across all priorities

---

## 13. Gaps and Ambiguities

**Purpose:** Document specification areas requiring clarification or interpretation

### 13.1 Specification Ambiguities

| Issue ID | Area                    | Description                                                                                  | Resolution Strategy                                                | Priority |
| -------- | ----------------------- | -------------------------------------------------------------------------------------------- | ------------------------------------------------------------------ | -------- |
| GAP-001  | Temporal Filters        | Open intervals: Does `../2024-01-31` mean "all times up to 2024-01-31" or "unbounded start"? | Assume unbounded start (per ISO 8601), document assumption         | HIGH     |
| GAP-002  | Recursive Queries       | When `recursive=true`, do filters apply before or after recursion?                           | Assume filters apply to all processed resources, document          | MEDIUM   |
| GAP-003  | SensorML vs GeoJSON     | Can a System be available in BOTH GeoJSON and SensorML, or must choose one?                  | Assume both formats available via content negotiation, document    | HIGH     |
| GAP-004  | Observation Schema      | Must observation result EXACTLY match datastream schema, or can it be subset?                | Assume exact match required for validation, document               | HIGH     |
| GAP-005  | Command Cancellation    | DELETE command vs POST status with CANCELED - are they equivalent?                           | Assume DELETE is preferred, CANCELED status for tracking, document | MEDIUM   |
| GAP-006  | Subsystem Datastreams   | Do subsystem datastreams appear in parent system's datastreams list when recursive?          | Assume YES per Req 13, document behavior                           | MEDIUM   |
| GAP-007  | uniqueIdentifier Format | Must UID be UUID, or any valid URI? Spec says "preferably UUID" but not required             | Accept any valid URI, recommend UUID in documentation              | LOW      |

### 13.2 Missing Specification Examples

| Resource Type     | Missing Example                                                       | Impact | Mitigation                                                   |
| ----------------- | --------------------------------------------------------------------- | ------ | ------------------------------------------------------------ |
| Systems           | System with all optional properties populated                         | Medium | Create synthetic example based on schema                     |
| Deployments       | Multi-level subdeployment hierarchy (3+ levels)                       | Low    | Create synthetic example with 3-level nesting                |
| Observations      | Observations with all temporal format variations                      | High   | Create examples for instant, closed interval, open intervals |
| Commands          | Complete command lifecycle (submit → pending → executing → completed) | High   | Create synthetic examples for all status transitions         |
| Sampling Features | Sampling feature with complex geometry (Polygon, MultiPoint)          | Low    | Create synthetic examples with various geometry types        |
| DataStreams       | DataStream with multi-property schema (10+ observed properties)       | Medium | Create synthetic example with diverse property types         |

### 13.3 OpenAPI vs Specification Text Conflicts

| Conflict ID | Area                | OpenAPI Says                       | Spec Text Says                                      | Resolution                                                             |
| ----------- | ------------------- | ---------------------------------- | --------------------------------------------------- | ---------------------------------------------------------------------- | ------ |
| CONF-001    | System location     | Optional in schema                 | "MUST have location for mobile systems" (Req 4)     | Prioritize spec text: location required for mobile, optional for fixed | HIGH   |
| CONF-002    | Procedure geometry  | Not explicitly forbidden in schema | "Procedures MUST NOT have location" (Req 24)        | Prioritize spec text: reject if geometry present                       | MEDIUM |
| CONF-003    | resultTime format   | String type in schema              | "ISO 8601 instant or interval or 'latest'" (Req 49) | Prioritize spec text: validate format explicitly                       | HIGH   |
| CONF-004    | recursive parameter | Boolean type                       | "true or false, default false" (Req 10)             | No conflict, document default behavior                                 | LOW    |

**Resolution Strategy:**

1. **Specification text takes precedence** over OpenAPI when conflicts exist
2. Document all ambiguities and resolutions in test documentation
3. Flag conflicts for upstream clarification (contribute to spec improvement)
4. Create test cases for both interpretations where ambiguous
5. Clearly document assumptions in code comments

---

## 14. Cross-Validation with Implementation Guide

**Purpose:** Validate extracted requirements against Implementation Guide specifications

### Alignment Check

| Aspect                  | Implementation Guide                                                                                                                   | Specification Requirements                  | Status            | Notes                                                                  |
| ----------------------- | -------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------- | ----------------- | ---------------------------------------------------------------------- |
| **Resource Types**      | 9 resource types (Systems, Deployments, Procedures, SamplingFeatures, Properties, DataStreams, Observations, ControlStreams, Commands) | Same 9 resource types                       | ✅ Aligned        | Full coverage                                                          |
| **Query Parameters**    | 70+ parameters documented                                                                                                              | 80+ parameters extracted                    | ⚠️ Gap            | Implementation Guide missing some Part 2 advanced filtering parameters |
| **Temporal Filters**    | phenomenonTime, resultTime, validTime, executionTime, issueTime                                                                        | Same 5 temporal parameters                  | ✅ Aligned        | All formats covered                                                    |
| **Spatial Filters**     | bbox, geometry                                                                                                                         | Same spatial parameters                     | ✅ Aligned        | WGS84 default                                                          |
| **Formats**             | GeoJSON, SensorML JSON, SWE Common JSON/Text/Binary                                                                                    | Same 5 formats                              | ✅ Aligned        | All formats supported                                                  |
| **Operations**          | 70+ operations (CRUD + nested)                                                                                                         | 80+ operations extracted                    | ⚠️ Gap            | Implementation Guide missing some nested endpoints                     |
| **Error Handling**      | Generic error categories                                                                                                               | Detailed error conditions per resource      | ⚠️ Gap            | Need to add detailed error matrix to Implementation Guide              |
| **Conformance Classes** | 19 conformance classes listed                                                                                                          | 19 conformance classes extracted            | ✅ Aligned        | Full coverage                                                          |
| **Test Pyramid**        | 60% unit, 40% integration, 0% e2e                                                                                                      | 55-60% unit, 25-30% integration, 10-15% e2e | ⚠️ Minor Conflict | Specification testing includes e2e workflows                           |

### Identified Gaps in Implementation Guide

1. **Missing Advanced Filtering Parameters:**

   - Implementation Guide doesn't document all Part 2 advanced filtering parameters
   - **Action:** Update Implementation Guide with complete parameter list from Part 2, Conformance Class A.6

2. **Missing Nested Endpoints:**

   - `/datastreams/{dsId}/samplingFeatures` (optional, Part 2, Req 3)
   - `/datastreams/{dsId}/featuresOfInterest` (optional, Part 2, Req 4)
   - `/controlstreams/{csId}/samplingFeatures` (optional, Part 2, Req 17)
   - `/controlstreams/{csId}/featuresOfInterest` (optional, Part 2, Req 18)
   - **Action:** Add optional nested endpoints to Implementation Guide

3. **Missing Error Detail Requirements:**

   - Implementation Guide has generic error handling
   - Specification requires detailed error structures per resource type
   - **Action:** Add comprehensive error condition matrix to Implementation Guide

4. **Test Pyramid Discrepancy:**
   - Implementation Guide: 60/40/0 (unit/integration/e2e)
   - Specification Testing: 55-60/25-30/10-15 (includes workflow validation)
   - **Resolution:** Specification testing correctly identifies need for e2e workflow tests; update Implementation Guide

### Conflicts Requiring Resolution

| Conflict             | Implementation Guide      | Specification                               | Resolution                                                                        |
| -------------------- | ------------------------- | ------------------------------------------- | --------------------------------------------------------------------------------- |
| Test Distribution    | 60% unit, 40% integration | 55-60% unit, 25-30% integration, 10-15% e2e | Adopt specification distribution; e2e workflows validate specification compliance |
| Error Handling Scope | Generic error categories  | Detailed error per resource type            | Adopt specification detail; update Implementation Guide with error matrix         |

**Cross-Validation Actions:**

1. ✅ Align resource type coverage (already aligned)
2. ⚠️ Add missing parameters to Implementation Guide
3. ⚠️ Add optional nested endpoints to Implementation Guide
4. ⚠️ Add error condition matrix to Implementation Guide
5. ⚠️ Update test pyramid distribution in Implementation Guide
6. ✅ Validate conformance class coverage (already aligned)

---

## 15. Summary and Next Steps

### Research Summary

**Total Specification Requirements Cataloged:** 250+ normative requirements

**Coverage:**

- ✅ 19 conformance classes fully analyzed
- ✅ 9 resource types with comprehensive reference matrices
- ✅ 80+ query parameters documented with validation rules
- ✅ 100+ format validation rules extracted (GeoJSON, SensorML, SWE Common)
- ✅ 50+ endpoints mapped with operations and error responses
- ✅ 25+ specification examples inventoried as potential fixtures
- ✅ 40+ OpenAPI schemas analyzed
- ✅ Cross-validation with Implementation Guide complete

**Implementation Priorities (by resource type):**

- **CRITICAL:** Systems, DataStreams, Observations (3 resource types, ~120 spec requirements to support)
- **HIGH:** Deployments, Sampling Features, ControlStreams, Commands (4 resource types, ~80 spec requirements)
- **MEDIUM:** Procedures, Properties (2 resource types, ~50 spec requirements)

### How to Use This Document

This document is a **specification reference**, not a test plan. Use it to:

- Understand what URL patterns, query parameters, and response shapes the CSAPIQueryBuilder must handle
- Know what conformance classes exist so the client can detect and adapt to server capabilities
- Identify temporal format variations for parameter encoding tests
- Source fixture structures from specification examples (Section 6)
- Understand error response shapes the client should handle gracefully

**Do not** use the requirement IDs (SYS-001, etc.) as test case identifiers. Tests should be organized around client code: `csapi-query-builder.spec.ts`, `sensorml-parser.spec.ts`, `conformance-detection.spec.ts`, etc.

### Answers to All Research Questions

**Core Questions:**

1. **What are all normative requirements?** 250+ requirements extracted from Parts 1 & 2, documented in resource matrices
2. **What conformance classes exist?** 19 conformance classes (11 Part 1, 8 Part 2), all documented
3. **What are the requirements for 9 resource types?** Complete matrices created (Section 2)
4. **What query parameters, validation rules, error conditions?** Comprehensive matrices created (Sections 3-4)
5. **What specification examples as fixtures?** 25+ examples inventoried (Section 6)
6. **What endpoint patterns exist?** Complete endpoint matrix (Section 8)

**Detailed Questions (72 total):** All answered throughout sections 1-14

### Next Steps

**Using This Reference:**

1. Use resource matrices to inform CSAPIQueryBuilder method signatures and URL patterns
2. Extract specification examples as static test fixtures
3. Use query parameter inventory to inform parameter encoding unit tests
4. Use conformance class catalog to inform client conformance detection logic
5. Use endpoint matrix to validate QueryBuilder URL generation

**Documentation Updates:** 6. Add missing parameters to Implementation Guide 7. Add error condition matrix to Implementation Guide 8. Add optional nested endpoints to Implementation Guide

---

**Research Status:** COMPLETE ✅  
**All Success Criteria Met:** ✅  
**Reclassified:** From "test requirements" to "specification reference" (Phase 2D, C1)  
**Review notices added:** Phase 2D, M1 — sections 2, 4, 5, 9, 10, 11, 12 annotated to distinguish useful reference content from test-framing  
**Ready for Downstream Use:** As implementation reference for CSAPIQueryBuilder, format parsers, conformance detection
