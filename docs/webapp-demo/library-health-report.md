# OGC Client CSAPI_2 — Library Health Report

**Date:** February 19, 2026  
**Repository:** [OS4CSAPI/ogc-client-CSAPI_2](https://github.com/OS4CSAPI/ogc-client-CSAPI_2)  
**Upstream:** [camptocamp/ogc-client](https://github.com/camptocamp/ogc-client) (forked from)  
**Library Version:** `@camptocamp/ogc-client` v1.3.1-dev  
**Purpose:** Assess production-readiness and upstream contribution viability of the CSAPI module.

---

## 1. Executive Summary

The CSAPI module is a **spec-complete, production-quality implementation** of both OGC Connected Systems API Part 1 (OGC 23-001) and Part 2 (OGC 23-002) for request/response patterns. It includes full SWE Common 3.0 and SensorML 3.0 parsers. The code is thoroughly tested (29 spec files, 200+ individual test cases, 1:1+ spec-to-source ratio), cleanly isolated from existing ogc-client modules, and documented with JSDoc referencing OGC spec sections.

The 3 test failures in the full suite are **pre-existing camptocamp issues** (WMS timeout, esbuild worker resolution, OGC API endpoint parsing) — zero CSAPI regressions.

---

## 2. Test Results

**Command:** `npx jest --config jest.config.cjs --forceExit`

| Metric | Result |
|--------|--------|
| **Total test suites** | 57 |
| **Passing** | 54 |
| **Failing** | 3 (pre-existing, non-CSAPI) |
| **CSAPI suites** | 29 / 29 PASS |

### Failing Suites (all pre-existing)

| Suite | Issue |
|-------|-------|
| `src/wms/endpoint.spec.ts` | Timeout (97s) — WMS GetCapabilities mock issue |
| `src/shared/http-utils.spec.ts` | esbuild worker resolution error |
| `src/ogc-api/endpoint.spec.ts` | 1 test failure in OGC API endpoint parsing |

### CSAPI Test Suites — All Passing

```
PASS src/ogc-api/csapi/url_builder.spec.ts
PASS src/ogc-api/csapi/helpers.spec.ts
PASS src/ogc-api/csapi/model.spec.ts
PASS src/ogc-api/csapi/command-routing.spec.ts
PASS src/ogc-api/csapi/formats/part2.spec.ts
PASS src/ogc-api/csapi/formats/geojson.spec.ts
PASS src/ogc-api/csapi/formats/response.spec.ts
PASS src/ogc-api/csapi/formats/classification.spec.ts
PASS src/ogc-api/csapi/formats/constants.spec.ts
PASS src/ogc-api/csapi/formats/schema-response.spec.ts
PASS src/ogc-api/csapi/formats/property.spec.ts
PASS src/ogc-api/csapi/formats/index.spec.ts
PASS src/ogc-api/csapi/formats/sensorml/parser.spec.ts
PASS src/ogc-api/csapi/formats/sensorml/physical-system.spec.ts
PASS src/ogc-api/csapi/formats/sensorml/simple-process.spec.ts
PASS src/ogc-api/csapi/formats/sensorml/aggregate-process.spec.ts
PASS src/ogc-api/csapi/formats/sensorml/types.spec.ts
PASS src/ogc-api/csapi/formats/sensorml/index.spec.ts
PASS src/ogc-api/csapi/formats/swecommon/parser.spec.ts
PASS src/ogc-api/csapi/formats/swecommon/components.spec.ts
PASS src/ogc-api/csapi/formats/swecommon/data-record.spec.ts
PASS src/ogc-api/csapi/formats/swecommon/data-array.spec.ts
PASS src/ogc-api/csapi/formats/swecommon/types.spec.ts
PASS src/ogc-api/csapi/formats/swecommon/index.spec.ts
PASS src/ogc-api/csapi/integration/discovery.spec.ts
PASS src/ogc-api/csapi/integration/navigation.spec.ts
PASS src/ogc-api/csapi/integration/observation.spec.ts
PASS src/ogc-api/csapi/integration/command.spec.ts
PASS src/ogc-api/csapi/integration/pipeline.spec.ts
```

---

## 3. Architecture

The CSAPI module lives at `src/ogc-api/csapi/` and follows a layered architecture:

| Layer | File(s) | Lines | Responsibility |
|-------|---------|-------|----------------|
| **URL Builder** | `url_builder.ts` | 2,329 | Query URL construction for all 9 CSAPI resource types |
| **Model** | `model.ts` | 676 | TypeScript interfaces for all resources, query options, schema responses |
| **Helpers** | `helpers.ts` | 229 | Temporal encoding, link scanning, parameter validation |
| **Command Routing** | `command-routing.ts` | ~170 | Fallback routing for servers rejecting top-level `/commands` |
| **Formats** | `formats/` (13+ files) | ~2,160 | Parsers for GeoJSON, Part 2, SensorML 3.0, SWE Common 3.0 |
| **Integration Tests** | `integration/` (5 specs) | — | Workflow-level tests: discovery, navigation, observation, command, pipeline |

**Design pattern:** `CSAPIQueryBuilder` is the main entry point — a URL builder that discovers available resources from OGC collection link relations, constructs spec-correct URLs, and validates parameters. It is intentionally **not** an HTTP client — it produces URLs that consumers call themselves. This matches the existing camptocamp/ogc-client architecture.

---

## 4. Module Completeness

### 4.1 URL Builder — 77+ Public Methods

The `CSAPIQueryBuilder` class provides full CRUD + nested resource navigation for all 9 CSAPI resource types:

| Resource | List | Get | Create | Update | Delete | Nested / Cross-refs |
|----------|:----:|:---:|:------:|:------:|:------:|---------------------|
| **Systems** | ✅ | ✅ | ✅ | ✅ | ✅ | History, Subsystems, DataStreams, ControlStreams, SamplingFeatures, Deployments, Procedures |
| **Deployments** | ✅ | ✅ | ✅ | ✅ | ✅ | History, Subdeployments, Systems |
| **Procedures** | ✅ | ✅ | ✅ | ✅ | ✅ | History, Systems, DataStreams |
| **Sampling Features** | ✅ | ✅ | ✅ | ✅ | ✅ | History, Systems, Observations |
| **Properties** | ✅ | ✅ | — | — | — | History, Systems, DataStreams, ControlStreams |
| **DataStreams** | ✅ | ✅ | ✅ | ✅ | ✅ | Schema, Observations, Systems, Procedures, History |
| **Observations** | ✅ | ✅ | ✅¹ | ✅ | ✅ | Datastream, SamplingFeature, System, History |
| **Control Streams** | ✅ | ✅ | ✅ | ✅ | ✅ | Schema, Commands, Feasibility |
| **Commands** | ✅ | ✅ | ✅ | ✅ | ✅ | Status, Result, Cancel, Batch create |

¹ Observations are created via their parent DataStream endpoint, per the OGC spec.  
Properties are correctly modeled as read-only (no CUD methods).

### 4.2 Format Parsers

| Parser | Functions | Coverage |
|--------|-----------|----------|
| `geojson.ts` (472 lines) | `isCSAPIFeature()`, `getCSAPIResourceType()`, `parseValidTime()`, `extractCSAPIFeature()` | SOSA, SSN, SensorML vocabulary namespaces |
| `part2.ts` (512 lines) | `parseDatastream()`, `parseObservation()`, `parseControlStream()`, `parseCommand()`, `parseCommandStatus()` | All 5 Part 2 resource types |
| `response.ts` (131 lines) | `parseCollectionResponse()` | FeatureCollection + Items envelopes |
| `classification.ts` (126 lines) | `inferResourceTypeFromPath()`, `classifyFeature()` | 52North featureType:null fallback |
| `schema-response.ts` (178 lines) | `parseDatastreamSchemaResponse()`, `parseControlStreamSchemaResponse()` | Both schema endpoints |
| `property.ts` (61 lines) | `parseProperty()` | DerivedProperty (non-GeoJSON Part 1 resource) |
| `constants.ts` (336 lines) | Media types, SOSA/SSN URIs, vocabulary namespaces, `getContentTypeForResource()` | Comprehensive constants registry |

### 4.3 Model — TypeScript Types

676 lines covering:
- **9 resource interfaces:** System, Deployment, Procedure, SamplingFeature, Property, Datastream, Observation, ControlStream, Command, CommandStatus
- **10 query option interfaces:** Base QueryOptions + type-specific options for each resource
- **Schema responses:** DatastreamSchemaResponse, ControlStreamSchemaResponse
- **Collection wrappers:** FeatureCollection\<T\>, ItemCollection\<T\>, plus 10 typed aliases
- **Enums/constants:** CSAPIResourceTypes (9-element), CommandStatusCodes (9 statuses), SystemTypeUris (5 SOSA URIs)
- **Utility types:** TimeInterval, ResourceLink, CsapiDateTimeParameter

### 4.4 SensorML 3.0 Parser

**928 lines of type definitions** modeling the full SensorML 3.0 hierarchy:
- `DescribedObject` → `AbstractProcess` → `SimpleProcess`, `AggregateProcess`
- `AbstractPhysicalProcess` → `PhysicalComponent`, `PhysicalSystem`
- Supporting: ContactInfo, ResponsibleParty, CapabilityList, CharacteristicList, I/O lists, Position, Pose, Events, Settings

**5 parser source files + helpers/errors:**
- `parseSensorML30()` — main entry with type discrimination
- Dedicated sub-parsers: SimpleProcess, AggregateProcess, PhysicalSystem
- 6 spec files with substantive tests

### 4.5 SWE Common 3.0 Parser

**735 lines of type definitions** covering the full SWE Common 3.0 data model:
- **6 scalar types:** SweBoolean, SweCount, SweQuantity, SweText, SweCategory, SweTime
- **4 range types:** SweCountRange, SweQuantityRange, SweTimeRange, SweCategoryRange
- **Aggregate types:** DataRecord, Vector, Matrix, DataChoice, DataArray, SweGeometry
- **4 encoding types:** TextEncoding, JSONEncoding, BinaryEncoding, XMLEncoding
- Constraints, NilValues, UnitOfMeasure

**~900-line parser** with 18+ exported functions covering all 16 component types, plus `validateAgainstSchema()`.

### 4.6 Helpers & Command Routing

- **helpers.ts** (229 lines): `formatDateTimeParameter()`, `scanCsapiLinks()` (3 link relation conventions), `encodeResourceId()`, parameter validators
- **command-routing.ts** (~170 lines): Workaround for OpenSensorHub rejecting top-level `/commands` with HTTP 400. Provides detection, per-server routing cache, and fallback URL construction through `/controlstreams/{csId}/commands`.

### 4.7 Integration Tests

5 workflow-level test suites using mocked `fetch`:

| Test | Purpose |
|------|---------|
| `discovery.spec.ts` (391 lines) | Full lifecycle: connect → conformance → collections → build URLs → retrieve → classify |
| `navigation.spec.ts` | Cross-resource navigation (system → datastreams → observations) |
| `observation.spec.ts` | Observation retrieval and parsing workflow |
| `command.spec.ts` | Command creation, status tracking, routing fallback |
| `pipeline.spec.ts` | End-to-end multi-step fetch/parse chains |

---

## 5. Code Quality Signals

### Test Quality — Real Tests, Not Stubs

All 29 spec files contain substantive assertions:
- `url_builder.spec.ts` (3,180 lines) — **larger than its source** (2,329 lines). Uses fixture factories, tests constructor behavior, URL construction for all resource types, error handling for invalid parameters.
- `sensorml/parser.spec.ts` (382 lines) — Tests type discrimination with minimal valid JSON fixtures for all 4 concrete process types
- `integration/discovery.spec.ts` (391 lines) — Full end-to-end discovery workflow with `globalThis.fetch = jest.fn()` mocking

### JSDoc / Documentation — Excellent

- Module-level `@module` JSDoc with `@see` links to OGC spec sections
- Class-level documentation with usage examples and migration guides
- Per-method JSDoc with `@param`, `@returns`, `@throws`, `@example`, `@see`
- Inline `@remarks` blocks noting server quirks (OSH streaming POST, uid strictness)
- The `url_builder.ts` class JSDoc alone is ~90 lines including full usage examples

### TypeScript Rigor — Zero `any` in Production

- All function signatures have explicit parameter and return types
- Discriminated unions for SWE Common components and SensorML processes
- `as const` assertions on all enum-like arrays for literal type inference
- Generic collection types: `FeatureCollection<T>`, `ItemCollection<T>`, `CollectionResponse<T>`
- The only `any` in the codebase are in spec files for deliberate edge-case testing

---

## 6. OGC Spec Coverage Analysis

### Part 1 — OGC 23-001 (Features)

| Requirement | Status |
|------------|--------|
| Systems (CRUD, GeoJSON, subsystems, history) | ✅ Complete |
| Deployments (CRUD, GeoJSON, subdeployments, history) | ✅ Complete |
| Procedures (CRUD, GeoJSON, history) | ✅ Complete |
| Sampling Features (CRUD, GeoJSON, history) | ✅ Complete |
| Properties (read-only) | ✅ Complete |
| Feature type recognition (SOSA/SSN/SensorML vocabularies) | ✅ Complete |
| Nested resource navigation | ✅ Complete |
| Version history endpoints | ✅ Complete (all 5 Part 1 resources) |

### Part 2 — OGC 23-002 (Dynamic Data)

| Requirement | Status |
|------------|--------|
| DataStreams (CRUD, nested via system) | ✅ Complete |
| Observations (list, get, update, delete, create via datastream) | ✅ Complete |
| Control Streams (CRUD, nested via system) | ✅ Complete |
| Commands (CRUD, nested via control stream, batch) | ✅ Complete |
| Command Status (get, update) | ✅ Complete |
| Command Result (get) | ✅ Complete |
| Command Cancel (post) | ✅ Complete |
| Command feasibility checking | ✅ Complete |
| Schema endpoints (datastream + control stream) | ✅ Complete |
| `resultTime: 'latest'` keyword | ✅ Complete |
| Cursor-based pagination | ✅ Complete |

### SWE Common 3.0

| Requirement | Status |
|------------|--------|
| All 6 scalar types | ✅ Complete |
| All 4 range types | ✅ Complete |
| Aggregate types (DataRecord, Vector, Matrix, DataChoice, DataArray, Geometry) | ✅ Complete |
| All 4 encoding types (Text, JSON, Binary, XML) | ✅ Complete |
| Constraints (AllowedValues, AllowedTokens, AllowedTimes) | ✅ Complete |
| Nil values | ✅ Complete |
| Schema validation | ✅ Complete |

### SensorML 3.0

| Requirement | Status |
|------------|--------|
| SimpleProcess | ✅ Complete |
| AggregateProcess (ComponentList, ConnectionList) | ✅ Complete |
| PhysicalComponent | ✅ Complete |
| PhysicalSystem | ✅ Complete |
| DescribedObject properties | ✅ Complete |
| Capabilities / Characteristics | ✅ Complete |
| Position (all variants including GeoJSON Point, Pose) | ✅ Complete |
| I/O (InputList, OutputList, ParameterList) | ✅ Complete |

---

## 7. Known Gaps

| Gap | Severity | Notes |
|-----|----------|-------|
| **No WebSocket / SSE streaming** | Medium | Part 2 supports real-time streaming of observations and commands. Only request/response patterns are implemented. |
| **No HTTP client layer** | Low (by design) | The library is a URL builder + parser. HTTP fetch is left to the consumer. Matches existing camptocamp/ogc-client architecture. |
| **No MQTT support** | Low | Optional in the spec. |
| **SWE Binary encoding decode** | Low | `BinaryEncoding` type is defined and parsed, but runtime binary data stream decoding is not implemented. |
| **No batch observation creation helper** | Low | Batch is implicit via `createObservation()` (same URL, array body). Only `createCommands()` has an explicit batch method. |

---

## 8. Upstream Contribution Viability

### Favorable Factors

1. **Clean isolation** — All CSAPI code is in `src/ogc-api/csapi/` with no modifications to existing WMS/WFS/WMTS/STAC modules
2. **Architectural consistency** — Follows the same URL-builder-not-HTTP-client pattern as the rest of ogc-client
3. **Zero test regressions** — All 54 passing suites in the original still pass; 3 failures are pre-existing
4. **camptocamp/ogc-client#118** — Open issue from the CSAPI co-chair (Sam Bolling) requesting Connected Systems support, with 11 comments and community interest
5. **Substantial standalone value** — The SWE Common 3.0 and SensorML 3.0 parsers are useful beyond CSAPI
6. **Issue tracker clean** — 0 open issues on ogc-client-CSAPI_2

### Steps Required for Upstream PR

1. Confirm maintainer receptiveness (issue #118 is open but no commitment)
2. Ensure the 3 pre-existing test failures are not worsened
3. Strip demo app files (demo/ directory is explorer-specific, not library code)
4. Potentially split into smaller PRs: (a) SWE Common parser, (b) SensorML parser, (c) CSAPI URL builder + model, (d) format parsers
5. Add CHANGELOG entries and update README with CSAPI documentation

### Recommendation

The library is **PR-ready from a code quality perspective**. The decision is strategic — whether camptocamp maintainers want to accept a large feature addition. Splitting into atomic PRs (SWE Common first, then SensorML, then CSAPI core) would reduce review burden and increase acceptance likelihood.

---

## 9. Source Inventory

### Total CSAPI Codebase

| Category | Files | Approximate Lines |
|----------|-------|-------------------|
| Core source (url_builder, model, helpers, command-routing) | 4 | ~3,400 |
| Format parsers (7 files) | 7 | ~2,160 |
| SensorML 3.0 (types, parsers, helpers, errors) | 8 | ~2,000+ |
| SWE Common 3.0 (types, parsers, helpers) | 7 | ~2,500+ |
| **Source subtotal** | **~27 files** | **~10,000+** |
| Spec files | 29 | ~12,000+ |
| Integration tests | 5 | ~1,500+ |
| **Total** | **~56 files** | **~23,000+** |

### Spec-to-Source Ratio

- **29 spec files / 27 source files = 1.07× file coverage**
- `url_builder.spec.ts` (3,180 lines) is **1.37× the size** of its source (2,329 lines)
- **200+ individual `it()` / `test()` blocks** across all CSAPI specs
