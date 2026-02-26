# CSAPI Implementation Roadmap

**Last Updated:** February 15, 2026  
**Version:** 3.4 (Phase 3.1 Smoke Test Findings F40-F46 Integrated)

---

## Executive Summary

This roadmap outlines the complete implementation plan for adding Connected Systems API (CSAPI) support to the Camptocamp OGC Client Library. The work is organized into four sequential phases spanning **57-84 hours of development time** (8-11 weeks calendar time).

> **📋 FULL CONTEXT**
>
> This roadmap extracts the implementation phases from the complete [CSAPI Implementation Guide](csapi-implementation-guide.md), which contains:
>
> - 13 completed research plans with ⭐⭐⭐⭐⭐ confidence ratings
> - Complete architectural decisions and rationale
> - Detailed component specifications
> - Integration patterns and code examples
> - Development standards and best practices
>
> **Refer to the [Implementation Guide](csapi-implementation-guide.md) for complete architectural context and detailed component specifications.**

**Roadmap Overview:**

- **Phase 1: Core Structure (12-16 hours)** - Foundation: types, integration points, stub QueryBuilder, helper utilities (4 tasks)
- **Phase 2: QueryBuilder (20-28 hours)** - Complete URL building for all 80 CSAPI methods across 9 resource types (9 tasks)
- **Phase 3: Format Handling (16-28 hours)** - SensorML/SWE parsers + GeoJSON/Format Detector/Validator extensions (17 tasks with incremental testing)
- **Phase 4: Tests & Documentation (9-12 hours)** - Integration tests, unit test completion, documentation (3 tasks)

**Total Scope:**

- **Implementation:** ~4,800-6,450 lines across 24 files
- **Tests:** ~4,200-6,000 lines across 22 test files (phase-level range; authoritative per-file breakdown in [Doc 19](../research/testing/findings/19-test-organization-file-structure.md) yields 4,040-5,340)
- **Total Code:** ~9,000-12,450 lines

**Key Dependencies:**

- Phase 1 → Phase 2 (types required for QueryBuilder)
- Phase 2 → Phase 3 (QueryBuilder required for format integration tests)
- Phases 1-3 → Phase 4 (complete implementation required for full testing)

**Fixture Convention:** Test fixtures in `fixtures/csapi/sample-server/` following the URL-path-mirroring convention (directory structure matches API endpoint paths). Estimated ~80-100 fixture files. See Guide §9 for full fixture strategy.

**Scope Exclusions:** The following are explicitly OUT OF SCOPE for this contribution:

- Performance testing (no `expect(duration)` assertions — upstream has zero performance tests)
- Real-world server testing (all tests use local fixtures, never live servers — see AP2)
- Migration testing (no existing CSAPI users to migrate)
- Worker extensions (no upstream JSON API uses Web Workers — see ROADMAP v3.1)

**Success Factors:**

- Write JSDoc documentation as you code (don't defer)
- **Write tests immediately after each subtask** (not batched at end of phase)
- Validate against spec examples throughout
- Review coverage after each subtask (aim for >80%)

---

## Implementation Roadmap

**Complete Roadmap: ALL Work Required for Full CSAPI Implementation**

This roadmap breaks down the complete CSAPI implementation into four phases, ordered by complexity and dependencies. The phases include ALL components documented in the [CSAPI Implementation Guide](csapi-implementation-guide.md): core structure, query builder with all methods, format parsers with all extensions, and comprehensive testing.

### Phase 1: Core Structure (Low Complexity)

**Estimated Time:** 12-16 hours (1.5-2 weeks calendar time)

**Goal:** Establish foundational types, conformance checking, and integration points.

**Tasks:**

1. **Create Type System** (~4-5 hours, Low complexity)

   - Create `src/ogc-api/csapi/model.ts` (~350-400 lines)
   - Define all Part 1 resource interfaces (System, Deployment, Procedure, SamplingFeature, Property)
   - Define all Part 2 resource interfaces (Datastream, Observation, ControlStream, Command)
   - Define query options interfaces (QueryOptions, SystemQueryOptions, ObservationQueryOptions, etc.)
   - Follow three-tier hierarchy: import from `../../shared/models.ts` and `../model.ts`
   - Import GeoJSON types from `geojson` package
   - **Write JSDoc:** Document all interfaces with property descriptions, required vs optional fields, examples
   - **Test:** Create `model.spec.ts` for type validation tests (~200-300 lines)
   - **Note:** This task estimates 4-5 hours including tests. Write types incrementally — aim for a mid-task test checkpoint around the 2.5-3 hour mark (e.g., after Part 1 interfaces, before Part 2 interfaces).

2. **Create Helper Utilities** (~2-3 hours, Low complexity)

   - Create `src/ogc-api/csapi/helpers.ts` (~50-80 lines)
   - Implement URL encoding utilities (properly encode special characters in query parameter values)
   - Implement temporal encoding utility (ISO 8601 formatting for CSAPI temporal parameters — similar to EDR's `DateTimeParameterToEDRString`)
   - Implement resource type validation utility (is string a valid `CSAPIResourceType`?)
   - Implement parameter validation utilities (e.g., `limit` must be positive integer)
   - **Note:** `buildResourceUrl()` and `buildQueryString()` are **private methods inside the QueryBuilder class** (see Guide §6 "Helper Methods"), not standalone helpers. They require `this.baseUrl` and are tested indirectly through public API method tests. This file contains only standalone pure functions.
   - **Write JSDoc:** Document each utility function with parameter descriptions, examples
   - **Test:** Add helper tests (~80-120 lines for helpers)

3. **Create Stub QueryBuilder** (~3-4 hours, Low complexity)

   - Create `src/ogc-api/csapi/url_builder.ts` (stub with constructor + 1-2 methods)
   - Implement constructor with collection info parameter
   - Implement `extractAvailableResources()` private helper for resource discovery
   - Create `availableResources` property (Set<string>)
   - Implement private `buildResourceUrl(resourceType, id?, subPath?, options?)` — core URL construction using `this.baseUrl`
   - Implement private `buildQueryString(options?)` — parameter serialization with encoding
   - Implement 1-2 simple public methods (e.g., `getSystems()`, `getSystem(id)`) as proof of concept using the private helpers
   - Validate resource availability before URL construction
   - **Note:** `buildResourceUrl()`, `buildQueryString()`, and `extractAvailableResources()` are private methods tested indirectly through public API method tests (see Guide §6 "Helper Methods" testing note).
   - **Write JSDoc:** Document constructor, public methods, and validation pattern. Private helpers get internal JSDoc only.
   - **Test:** Create `url_builder.spec.ts` with basic tests for constructor, resource validation, and the 1-2 public methods (~100-150 lines)

4. **Integrate with OgcApiEndpoint** (~3-4 hours, Low complexity)
   - Modify `src/ogc-api/endpoint.ts` (+35 lines)
     - Add import for CSAPIQueryBuilder
     - Add cache field for QueryBuilder instances
     - Add `csapiCollections` getter (6 lines)
     - Add `hasConnectedSystems` getter (6 lines)
     - Add `csapi(collectionId)` factory method (17 lines)
   - Modify `src/ogc-api/info.ts` (+12 lines)
     - Add `checkHasConnectedSystems()` function
     - Check for CSAPI Part 1 Core and Part 2 Dynamic Data conformance classes
   - Modify `src/ogc-api/index.ts` (+17 lines)
     - Export `CSAPIQueryBuilder` class
     - Export all CSAPI types (System, Deployment, DataStream, Observation, etc.)
     - Export query options types
   - **Write JSDoc:** Document factory method, getters, conformance function with usage examples
   - **Test:** Add integration tests for endpoint conformance checking (~100-150 lines)

**Phase 1 Deliverables:**

- ✅ Complete type system (all interfaces)
- ✅ OgcApiEndpoint integration (64 lines)
- ✅ Stub QueryBuilder with resource validation
- ✅ Helper utilities for URL/query building
- ✅ Basic test coverage (~400-550 lines tests)
- ✅ All JSDoc documentation for Phase 1 code

**Dependencies:** None (foundational work)

---

### Phase 2: QueryBuilder Methods (Medium Complexity)

**Estimated Time:** 20-28 hours (3-4 weeks calendar time)

**Goal:** Implement all 80 QueryBuilder methods for all 9 CSAPI resource types, with incremental testing after each resource type.

**Complete Query Parameter Support:** All collection query methods support `sortBy` and `sortOrder` parameters for server-side result ordering, in addition to pagination (`limit`, `offset`/cursor), temporal (`datetime`, `phenomenonTime`, `resultTime`), and spatial (`bbox`) parameters. See Guide §6 for full parameter documentation.

**Task Structure:** Each task implements methods for one resource type, then writes tests immediately before moving to the next resource type.

**Tasks:**

1. **Systems Methods** (~2-2.5 hours implementation + ~0.5 hour testing, Medium complexity)

   - **Implement 12 Systems methods in `url_builder.ts`:**
     - `getSystems(options?)` - Collection query with pagination
     - `getSystem(id, options?)` - Single system by ID
     - `createSystem(body)` - POST new system
     - `updateSystem(id, body)` - PUT/PATCH system
     - `deleteSystem(id)` - DELETE system
     - `getSystemHistory(id, options?)` - Temporal history
     - `getSystemSubsystems(id, options?)` - Hierarchical navigation
     - `getSystemDataStreams(id, options?)` - Part 2 link
     - `getSystemControlStreams(id, options?)` - Part 2 link
     - `getSystemSamplingFeatures(id, options?)` - Association link
     - `getSystemDeployments(id, options?)` - Association link
     - `getSystemProcedures(id, options?)` - Association link
   - All methods validate resource availability (~2 lines per method)
   - All methods use helper functions for code reuse
   - **Write JSDoc:** Document each method with parameters, return types, query parameter descriptions, examples
   - **Test immediately:** Add Systems method tests to `url_builder.spec.ts` (~40-50 lines tests)
     - Test getSystems with pagination, filtering, bbox
     - Test getSystem with specific ID
     - Test CRUD operations (create/update/delete)
     - Test navigation methods (subsystems, datastreams, associations)
     - Test resource validation (unavailable resource throws error)
     - Test query parameter encoding

2. **Deployments Methods** (~1.5-2 hours implementation + ~0.5 hour testing, Medium complexity)

   - **Implement 8 Deployments methods in `url_builder.ts`:**
     - `getDeployments(options?)` - Collection query
     - `getDeployment(id, options?)` - Single deployment
     - `createDeployment(body)` - POST new deployment
     - `updateDeployment(id, body)` - PUT/PATCH deployment
     - `deleteDeployment(id)` - DELETE deployment
     - `getDeploymentSubdeployments(id, options?)` - Hierarchical navigation
     - `getDeploymentSystems(id, options?)` - Associated systems
     - `getDeploymentHistory(id, options?)` - Temporal history
   - Validate resource availability, use helpers
   - **Write JSDoc:** Document methods with parameters, examples
   - **Test immediately:** Add Deployments tests (~30-40 lines tests)
     - Test collection and individual retrieval
     - Test CRUD operations
     - Test subdeployments navigation
     - Test temporal validity filtering

3. **Procedures Methods** (~1.5-2 hours implementation + ~0.5 hour testing, Medium complexity)

   - **Implement 8 Procedures methods in `url_builder.ts`:**
     - `getProcedures(options?)` - Collection query
     - `getProcedure(id, options?)` - Single procedure
     - `createProcedure(body)` - POST new procedure
     - `updateProcedure(id, body)` - PUT/PATCH procedure
     - `deleteProcedure(id)` - DELETE procedure
     - `getProcedureSystems(id, options?)` - Systems using procedure
     - `getProcedureDataStreams(id, options?)` - DataStreams using procedure
     - `getProcedureHistory(id, options?)` - Temporal history
   - Validate resource availability, use helpers
   - **Write JSDoc:** Document methods with parameters, examples
   - **Test immediately:** Add Procedures tests (~30-40 lines tests)
     - Test collection and retrieval
     - Test CRUD operations
     - Test system and datastream associations

4. **Sampling Features Methods** (~1.5-2 hours implementation + ~0.5 hour testing, Medium complexity)

   - **Implement 8 Sampling Features methods in `url_builder.ts`:**
     - `getSamplingFeatures(options?)` - Collection query with spatial filtering
     - `getSamplingFeature(id, options?)` - Single sampling feature
     - `createSamplingFeature(body)` - POST new feature
     - `updateSamplingFeature(id, body)` - PUT/PATCH feature
     - `deleteSamplingFeature(id)` - DELETE feature
     - `getSamplingFeatureSystems(id, options?)` - Systems at feature
     - `getSamplingFeatureObservations(id, options?)` - Observations at feature
     - `getSamplingFeatureHistory(id, options?)` - Temporal history
   - Validate resource availability, use helpers
   - **Write JSDoc:** Document methods with spatial query parameters, examples
   - **Test immediately:** Add Sampling Features tests (~30-40 lines tests)
     - Test spatial filtering (bbox, geometry)
     - Test observation retrieval
     - Test system associations

5. **Properties Methods** (~1-1.5 hours implementation + ~0.5 hour testing, Medium complexity)

   - **Implement 6 Properties methods in `url_builder.ts`:**
     - `getProperties(options?)` - Collection query
     - `getProperty(id, options?)` - Single property
     - `getPropertySystems(id, options?)` - Systems observing property
     - `getPropertyDataStreams(id, options?)` - DataStreams for property
     - `getPropertyControlStreams(id, options?)` - Control streams for property
     - `getPropertyHistory(id, options?)` - Temporal history
   - Validate resource availability, use helpers
   - **Write JSDoc:** Document methods with parameters, examples
   - **Test immediately:** Add Properties tests (~25-30 lines tests)
     - Test property retrieval
     - Test system/datastream/controlstream associations

6. **DataStreams Methods** (~2-2.5 hours implementation + ~0.5 hour testing, Medium-High complexity)

   - **Implement 11 DataStreams methods in `url_builder.ts`:**
     - `getDataStreams(options?)` - Collection query with phenomenonTime filtering
     - `getDataStream(id, options?)` - Single datastream
     - `createDataStream(body)` - POST new datastream
     - `updateDataStream(id, body)` - PUT/PATCH datastream
     - `deleteDataStream(id)` - DELETE datastream
     - `getDataStreamSchema(id)` - SWE Common schema
     - `getDataStreamObservations(id, options?)` - Observations in stream
     - `createObservation(datastreamId, body)` - POST observation
     - `getDataStreamSystems(id, options?)` - Systems producing stream
     - `getDataStreamProcedures(id, options?)` - Procedures for stream
     - `getDataStreamHistory(id, options?)` - Temporal history
   - Validate resource availability, use helpers
   - Support complete temporal query parameters (phenomenonTime, resultTime)
   - **Write JSDoc:** Document methods with temporal patterns, schema retrieval, examples
   - **Test immediately:** Add DataStreams tests (~45-55 lines tests)
     - Test temporal filtering (phenomenonTime, resultTime)
     - Test schema retrieval (obsFormat parameter)
     - Test observation creation
     - Test cursor-based pagination on getDataStreamObservations

7. **Observations Methods** (~1.5-2 hours implementation + ~0.5 hour testing, Medium-High complexity)

   - **Implement 9 Observations methods in `url_builder.ts`:**
     - `getObservations(options?)` - Collection query with phenomenonTime
     - `getObservation(id, options?)` - Single observation
     - `createObservations(datastreamId, body)` - POST bulk observations
     - `updateObservation(id, body)` - PUT/PATCH observation
     - `deleteObservation(id)` - DELETE observation
     - `getObservationDataStream(id)` - Parent datastream
     - `getObservationSamplingFeature(id, options?)` - Sampling feature
     - `getObservationSystem(id, options?)` - Observing system
     - `getObservationHistory(id, options?)` - Temporal history
   - Validate resource availability, use helpers
   - Support temporal and spatial filtering
   - **Write JSDoc:** Document methods with bulk creation patterns, temporal queries, examples
   - **Test immediately:** Add Observations tests (~35-45 lines tests)
     - Test temporal filtering
     - Test bulk creation
     - Test navigation to datastream/feature/system
     - Test obsFormat query parameter encoding (e.g., `obsFormat: 'application/swe+json'` → correct URL parameter)

8. **Control Streams Methods** (~1.5-2 hours implementation + ~0.5 hour testing, Medium-High complexity)

   - **Implement 8 Control Streams methods in `url_builder.ts`:**
     - `getControlStreams(options?)` - Collection query
     - `getControlStream(id, options?)` - Single control stream
     - `createControlStream(body)` - POST new control stream
     - `updateControlStream(id, body)` - PUT/PATCH control stream
     - `deleteControlStream(id)` - DELETE control stream
     - `getControlStreamSchema(id)` - SWE Common parameter schema
     - `getControlStreamCommands(id, options?)` - Commands in stream
     - `checkCommandFeasibility(controlStreamId, body)` - POST feasibility check
   - Validate resource availability, use helpers
   - **Write JSDoc:** Document methods with schema retrieval, feasibility checking, examples
   - **Test immediately:** Add Control Streams tests (~30-40 lines tests)
     - Test schema retrieval
     - Test feasibility checking
     - Test command listing

9. **Commands Methods** (~1.5-2 hours implementation + ~0.5 hour testing, Medium-High complexity)
   - **Implement 10 Commands methods in `url_builder.ts`:**
     - `getCommands(options?)` - Collection query with issueTime/executionTime
     - `getCommand(id, options?)` - Single command
     - `createCommand(controlStreamId, body)` - POST single command
     - `createCommands(controlStreamId, body)` - POST bulk commands
     - `updateCommand(id, body)` - PUT/PATCH command
     - `deleteCommand(id)` - DELETE command
     - `getCommandStatus(id)` - Status resource
     - `updateCommandStatus(id, body)` - Update status
     - `getCommandResult(id)` - Result resource
     - `cancelCommand(id)` - POST cancel operation
   - Validate resource availability, use helpers
   - Support temporal filtering on issueTime and executionTime
   - **Write JSDoc:** Document methods with command lifecycle patterns, status tracking, examples
   - **Test immediately:** Add Commands tests (~40-50 lines tests)
     - Test temporal filtering (issueTime, executionTime)
     - Test bulk command creation
     - Test status updates and retrieval
     - Test result retrieval
     - Test cancel operation

**Phase 2 Deliverables:**

- ✅ All 80 QueryBuilder methods implemented (9 resource types)
- ✅ Complete query parameter support (spatial, temporal, pagination)
- ✅ Resource validation in all methods (~2 lines per method)
- ✅ Comprehensive test coverage (~800-1,000 lines tests)
- ✅ All JSDoc documentation for QueryBuilder methods
- ✅ Each resource type tested immediately after implementation

**Dependencies:** Phase 1 (types, helpers, stub QueryBuilder, integration)

**Why This Structure:**

- **Early bug detection** - Helper function issues discovered with Systems, not Commands
- **Architecture validation** - Patterns validated incrementally, not all at end
- **Natural checkpoints** - Each resource type is a commit-able unit
- **Fresh context** - Tests written while method details are fresh
- **Prevents test debt** - Never more than 12 methods without tests
- **Matches Phase 1 pattern** - Test after each task

---

### Phase 3: Format Handling (High Complexity)

**Estimated Time:** 16-28 hours (2-4 weeks calendar time)

**Goal:** Build format parsers for SensorML 3.0 and SWE Common 3.0, extend GeoJSON/Format Detector/Validator for CSAPI, with incremental testing and correct dependency ordering.

**Task Structure:** SWE Common types created first (needed by SensorML), then each parser component tested immediately after implementation.

**Tasks:**

1. **GeoJSON Handler Extensions** (~2-3 hours, Medium complexity)

   - Create `formats/geojson.ts` (~50-100 lines) extending existing GeoJSON parser
   - Add recognition for CSAPI `featureType` property (sosa:System, sosa:Deployment, etc.)
   - Extract CSAPI-specific properties (uid, featureType, assetType, validTime, @link associations, etc.)
   - Add validation for CSAPI GeoJSON requirements (uid must be URI, featureType from spec-defined type URIs)
   - **Write JSDoc:** Document CSAPI property extraction, validation rules
   - **Test immediately:** Add tests for CSAPI GeoJSON parsing (~150-300 lines tests)
     - Test featureType recognition
     - Test property extraction
     - Test validator correctly rejects invalid GeoJSON input (e.g., missing uid, invalid featureType)
   - > **📋 Smoke Test Notes (Phase 2.9 — F34, F38, F39):**
     >
     > - **F34 (Issue #47):** Commands require fallback routing — top-level `/commands` returns 400 on OSH. The response handler built in this phase must implement dual-path resolution: try top-level first, fall back to nested `/controlstreams/{csId}/commands` path on 400. See Issue #47 for full design.
     > - **F38:** Command status responses use `command@id` cross-reference and `executionTime` as a 2-element array (time range). Add `command@id` to the `@id` cross-reference registry alongside `system@id`, `datastream@id`, `controlstream@id`, `foi@id`.
     > - **F39:** Commands use the same `{ items: [...], links: [...] }` envelope as all other resources — no special-casing needed. A single `parseCollectionResponse()` function can handle all 9 resource types.
   - > **📋 Smoke Test Notes (Phase 3.1 — F40, F43):**
     >
     > - **F40 (Issue #49):** OSH SamplingFeatures use `http://www.opengis.net/sensorml/2.0#Feature` — a non-SOSA vocabulary. Extend handler vocabulary sets to recognize SensorML namespace. See Issue #49 for full design.
     > - **F43:** 52North `/procedures` endpoint returns `featureType: "sosa:Sensor"` (a System-type URI). The handler's System > Procedure classification priority correctly handles this, but the endpoint context and featureType disagree. Future response parser may use endpoint context as a tiebreaker.
   - > **📋 Smoke Test Notes (Phase 3.2 — F49) — Design Decision:**
     >
     > - **F49 (Issue #52):** `extractCSAPIFeature()` uses `validateCSAPIFeature()` as a hard gate — any validation error blocks extraction entirely. This conflicts with upstream ogc-client patterns (tolerant extraction) and Postel's Law. **Design decision: remove all feature-level validators from scope.** The mature upstream handlers (WMS, WFS, WMTS, TMS) have zero validation; the STAC handler has inline required-field checks but no formal validation framework. No handler has separate `validate*()` functions or `ValidationError` types. Extraction succeeds for any recognized feature. See `docs/implementation/design-notes-validation-extraction-decoupling.md`.

2. **Format Detector Extensions** (~1-2 hours, Low complexity)

   - Extend existing format detector
   - Register 5 new media types: `application/sml+json`, `application/swe+json`, `application/swe+text`, `application/swe+csv`, `application/swe+binary`
   - Add routing logic to format handlers (SensorML → SensorML parser, SWE Common → SWE Common parser)
   - Add Content-Type header parsing, structure-based fallback detection
   - **Write JSDoc:** Document media type detection patterns
   - **Test immediately:** Add format detection tests (~50-100 lines tests)
     - Test media type registration
     - Test routing logic
     - Test fallback detection
   - > **📋 Smoke Test Notes (Phase 3.1 — F41, F45, F46):**
     >
     > - **F41 (Issue #50):** 52North systems return `featureType: null` in GeoJSON but `definition: "sosa:Sensor"` in SensorML. The response parser / format detector must implement endpoint-context fallback classification when `getCSAPIResourceType()` returns null. See Issue #50 for design options.
     > - **F45:** Response envelope varies by server AND format — OSH always uses `{ items: [...] }`, 52North GeoJSON uses `{ type: "FeatureCollection", features: [...] }`, 52North SensorML uses `{ items: [...] }`. The format detector / response parser must handle both envelope types.
     > - **F46:** OSH ignores `Accept: application/sml+json` and returns GeoJSON anyway. SensorML parser testing will be limited to 52North only.

3. **~~Validator Extensions~~ — REMOVED FROM SCOPE** (Issue #52)

   > **🚫 OUT OF SCOPE** — Feature-level validators have been **removed from the CSAPI contribution scope**. Analysis of the upstream codebase found that while the STAC handler has inline required-field checks (~20 ad-hoc `if/throw` patterns), **no handler has a formal validation framework** — no separate `validate*()` functions, no `ValidationError` types, no structured error arrays. The mature handlers (WMS, WFS, WMTS, TMS) have zero validation. The upstream philosophy follows Postel's Law: client libraries accept what servers return and make it accessible. Adding ~500 lines of formal validators + tests for a feature with no upstream consumer would be scope creep. See `docs/implementation/design-notes-validation-extraction-decoupling.md` for full rationale.
   >
   > **Smoke test findings F35, F36, F37** (error handling for cancel, `id` filter, result-less commands) remain valid and belong to the response handler / error handling layer (Phase 4 Integration Tests), not to a validation framework.

4. **SWE Common Types** (~2-3 hours, Medium complexity)

   - Create `src/ogc-api/csapi/formats/swecommon/` directory
   - Create `types.ts` (~600-800 lines)
     - Define DataComponent union type and all component interfaces
     - Define DataRecord, DataArray, Quantity, Count, Text, Boolean, Time, etc.
     - Define Encoding interfaces (JSONEncoding, TextEncoding, BinaryEncoding)
     - Define Constraint interfaces (AllowedValues, AllowedTimes, etc.)
   - **Write JSDoc:** Document all SWE Common types with SWE Common 3.0 spec references
   - **Test immediately:** Add type compilation tests (~50-100 lines tests)
     - Test type definitions compile without errors
     - Test union types discriminate correctly
     - Test interface constraints

5. **SensorML Types** (~2-3 hours, Medium complexity)

   - Create `src/ogc-api/csapi/formats/sensorml/` directory
   - Create `types.ts` (~800-1,200 lines)
     - Define PhysicalSystem, PhysicalComponent, SimpleProcess, AggregateProcess interfaces
     - Define CapabilityList, CharacteristicList, ComponentList, ConnectionList interfaces
     - **Link to SWE Common types** from Task 4 for capability/characteristic values
   - **Write JSDoc:** Document all SensorML types with SensorML 3.0 spec references
   - **Test immediately:** Add type compilation tests (~50-100 lines tests)
     - Test type definitions compile without errors
     - Test SWE Common type integration works
     - Test interface constraints
   - **Note:** The 800-1,200 lines are passive type definitions (interfaces only, no behavioral code). The 800 LOC testing cadence threshold applies to behavioral/implementation code, not type-only files. Type compilation tests verify correctness without requiring the same volume as behavioral code tests.

6. **SensorML Simple Process Parser** (~2-3 hours, Medium-High complexity)

   - Create `formats/sensorml/simple-process.ts` (~150-200 lines)
   - Implement parser for SimpleProcess descriptors
   - Handle inputs, outputs, parameters, method descriptions
   - **Write JSDoc:** Document parser function with examples
   - **Test immediately:** Add Simple Process parser tests (~100-150 lines tests)
     - Test parsing with spec example fixtures
     - Test invalid document handling
     - Test edge cases

7. **SensorML Aggregate Process Parser** (~2-3 hours, Medium-High complexity)

   - Create `formats/sensorml/aggregate-process.ts` (~200-250 lines)
   - Implement parser for AggregateProcess descriptors
   - Handle component connections, internal processes
   - **Write JSDoc:** Document parser function with examples
   - **Test immediately:** Add Aggregate Process parser tests (~150-200 lines tests)
     - Test parsing with spec example fixtures
     - Test connection handling
     - Test nested component parsing

8. **SensorML Physical Process Parsers** (~2-3 hours, Medium-High complexity)

   - Create `formats/sensorml/physical-system.ts` (~200-250 lines)
   - Implement parsers for PhysicalSystem and PhysicalComponent descriptors
   - Handle position, components (PhysicalSystem), method (PhysicalComponent), capabilities, characteristics
   - **Write JSDoc:** Document parser functions with examples
   - **Test immediately:** Add physical process parser tests (~150-200 lines tests)
     - Test parsing with spec example fixtures
     - Test position/location parsing
     - Test component hierarchy parsing (PhysicalSystem)
     - Test method parsing (PhysicalComponent)

9. **SensorML Main Parser** (~2-3 hours, High complexity)

   - Create `formats/sensorml/parser.ts` (~600-800 lines)
   - Main SensorML 3.0 parser with recursive component parsing
   - Capability/characteristic parsing with SWE Common integration
   - Type discrimination (SimpleProcess vs AggregateProcess vs PhysicalComponent vs PhysicalSystem)
   - Delegate to sub-parsers from Tasks 6-8
   - **Write JSDoc:** Document main parser with workflow examples
   - **Test immediately:** Add main parser tests (~150-200 lines tests)
     - Test type discrimination
     - Test recursive parsing
     - Test capability/characteristic integration with SWE Common
     - Test error handling

10. **SensorML Index** (~0.5-1 hour, Low complexity)

    - Create `formats/sensorml/index.ts` (~50-100 lines)
    - Barrel file exporting all SensorML parsers and types
    - Tree-shaking friendly exports
    - **Write JSDoc:** Document exports and usage patterns
    - **Test immediately:** Verify exports work (~20-30 lines tests)

11. **SWE Common Simple Components Parser** (~2-3 hours, Medium-High complexity)

    - Create `formats/swecommon/components.ts` (~300-400 lines)
    - Implement parsers for all simple component types (Quantity, Count, Text, Boolean, Time, Category) and range types (QuantityRange, CountRange, TimeRange, CategoryRange)
    - Handle UOM, constraints, code spaces
    - **Write JSDoc:** Document each component parser with examples
    - **Test immediately:** Add component parser tests (~200-300 lines tests)
      - Test each component type with fixtures
      - Test constraint validation
      - Test UOM handling

12. **SWE Common DataRecord Parser** (~2-3 hours, Medium-High complexity)

    - Create `formats/swecommon/data-record.ts` (~150-200 lines)
    - Implement parser for DataRecord structures
    - Handle field definitions, nested records
    - **Write JSDoc:** Document parser function with examples
    - **Test immediately:** Add DataRecord parser tests (~100-150 lines tests)
      - Test flat records
      - Test nested records
      - Test field ordering

13. **SWE Common DataArray Parser** (~2-3 hours, Medium-High complexity)

    - Create `formats/swecommon/data-array.ts` (~200-250 lines)
    - Implement parser for DataArray structures
    - Handle element types, encoding, values
    - Support JSON/Text/Binary encodings
    - **Write JSDoc:** Document parser function with encoding examples
    - **Test immediately:** Add DataArray parser tests (~150-200 lines tests)
      - Test JSON encoding
      - Test Text encoding
      - Test Binary encoding
      - Test element count validation

14. **SWE Common Main Parser** (~2-3 hours, High complexity)

    - Create `formats/swecommon/parser.ts` (~500-700 lines)
    - Main SWE Common 3.0 parser with component type discrimination
    - Encoding detection (JSON/Text/Binary)
    - Schema validation against DataComponent definitions
    - Delegate to sub-parsers from Tasks 11-13
    - **Write JSDoc:** Document main parser with workflow examples
    - **Test immediately:** Add main parser tests (~200-300 lines tests)
      - Test type discrimination
      - Test encoding detection
      - Test schema validation
      - Test error handling
    - > **📋 Smoke Test Note (Phase 2.8/2.9 — F33):**
      >
      > - **F33:** ControlStream schemas use `commandFormat` + `parametersSchema` where DataStream schemas use `observationFormat` + `resultSchema`. The SWE Common parser must handle both schema response variants. Both use the same SWE Common DataRecord structure internally.

15. **SWE Common Index** (~0.5-1 hour, Low complexity)

    - Create `formats/swecommon/index.ts` (~50-100 lines)
    - Barrel file exporting all SWE Common parsers and types
    - Tree-shaking friendly exports
    - **Write JSDoc:** Document exports and usage patterns
    - **Test immediately:** Verify exports work (~20-30 lines tests)

16. **Format Constants** (~1-2 hours, Low complexity)

    - Create `src/ogc-api/csapi/formats/constants.ts` (~50-100 lines)
    - Define media type constants
    - Define resource type constants
    - Define vocabulary URI constants (SOSA, SSN, CF, QUDT)
    - **Write JSDoc:** Document constant values and usage
    - **Test:** Constants validated by format detector tests (no separate test file needed)

17. **Format Index** (~1-2 hours, Low complexity)
    - Create `src/ogc-api/csapi/formats/index.ts` (~50-100 lines)
    - Barrel file exporting all parsers, types, and constants
    - Tree-shaking friendly exports
    - **Write JSDoc:** Document format imports and usage patterns
    - **Test immediately:** Add integration tests (~50-100 lines tests)
      - Test all exports are accessible
      - Test tree-shaking works correctly
      - Test import paths resolve

**Phase 3 Deliverables:**

- ✅ GeoJSON CSAPI extensions (~150-300 lines)
- ✅ Format Detector extensions (~50-100 lines)
- 🚫 ~~Validator extensions~~ — **Removed from scope** (Issue #52, no upstream precedent)
- ✅ SWE Common types (~600-800 lines) - **Created first for SensorML dependency**
- ✅ SensorML types (~800-1,200 lines) - Links to SWE Common types
- ✅ SensorML parsers complete (~1,150-1,450 lines across 4 files)
- ✅ SWE Common parsers complete (~1,150-1,550 lines across 4 files)
- ✅ Format constants and indices (~150-300 lines)
- ✅ Comprehensive format tests (~2,400-3,500 lines tests)
- ✅ All JSDoc documentation for format handlers
- ✅ Each component tested immediately after implementation

**Dependencies:** Phase 1 (type system), Phase 2 (QueryBuilder for integration tests)

**Why This Structure:**

- **Dependency fix** - SWE Common types (Task 4) created before SensorML types (Task 5) that depend on them
- **Early validation** - Each parser component tested immediately, not after 5-10 hours
- **Incremental progress** - 17 tasks with ~1-3 hour intervals instead of 2 massive 5-10 hour blocks
- **Natural checkpoints** - Each parser type (Simple Process, Aggregate Process, Physical System, etc.) is commit-able
- **Fresh context** - Tests written while parser logic is fresh
- **Prevents test debt** - Max 800 lines without tests, not 2,900 lines
- **Matches Phases 1 & 2 pattern** - Test after each task

---

### Phase 4: Tests and Documentation (Medium Complexity)

**Estimated Time:** 9-12 hours (1-1.5 weeks calendar time)

**Goal:** Add comprehensive tests and complete documentation.

> **📋 Scope Note:** Worker extensions (9 CSAPI message types) were evaluated and **removed from scope**. Analysis found that no upstream JSON-based API (EDR, STAC, TMS, OGC API) uses the Web Worker infrastructure — only XML-based APIs (WMS, WFS, WMTS) offload parsing to workers because XML DOM traversal is CPU-intensive. CSAPI operations use `response.json()` which is fast and does not benefit from worker offloading. All CSAPI parsing runs on the main thread, consistent with the EDR pattern. Worker offloading could be revisited as a future optimization if profiling demonstrates a need.

**Tasks:**

1. **Integration Tests** (~4-6 hours, Medium complexity)

   - Create end-to-end workflow tests (~900-1,150 lines across 4 files)
   - Discovery workflow: connect → check conformance → list collections → retrieve resources
   - Observation workflow: systems → datastreams → observations → pagination → parsing
   - Command workflow: systems → control streams → feasibility → submit → status → result
   - Cross-resource navigation: system → deployments → procedures → sampling features → datastreams → observations
   - Hierarchical queries: recursive traversal with large hierarchies
   - Error handling: server errors, network errors, malformed responses
   - **Write JSDoc:** Document test scenarios and expected behavior
   - **Test:** All integration tests (~900-1,150 lines)
   - > **📋 Smoke Test Notes (Phase 2.9 — F34-F39, cumulative server limitation matrix):**
     >
     > - **F34 (Issue #47):** Command workflow integration tests must cover the fallback routing path (top-level 400 → nested path). Test both: servers that support top-level `/commands` and servers that only support nested paths.
     > - **F35/F37:** Include negative-path integration tests: cancel returns 400 (optional endpoint), result returns 404 (result-less command type). Both should be handled gracefully, not throw.
     > - **Cumulative server limitation matrix for error-handling tests (15 known):** F6-F9 (Systems/SamplingFeatures nested), F16-F18 (DataStreams nested), F21-F24 (Observations nested), F28 (feasibility), F34 (top-level commands), F35 (cancel). All return 400 — validate the response handler returns `{ items: [], supported: false }` or equivalent for each.

2. **Unit Tests Completion** (~3-4 hours, Medium complexity)

   - Complete coverage for all QueryBuilder methods (~200-300 additional lines)
   - Complete coverage for all helper functions (~100-150 lines)
   - Edge case tests: empty collections, minimal resources, boundary conditions
   - Error case tests: invalid parameters, malformed URLs, resource validation failures
   - Pagination tests: offset-based and cursor-based
   - Query parameter tests: all spatial, temporal, relationship, hierarchical parameters
   - **Write JSDoc:** Document test cases and coverage goals
   - **Test:** All unit tests (~300-450 lines)

3. **API Documentation** (~2-3 hours, Low complexity)
   - Extend TypeDoc configuration for CSAPI types
   - Verify all JSDoc comments complete and accurate
   - Add usage examples to main classes (OgcApiEndpoint, CSAPIQueryBuilder)
   - Add format parser examples (parseSensorML30, parseSWEDataRecord)
   - Add migration guide for users of other CSAPI clients
   - Add error handling examples
   - **Write JSDoc:** Complete documentation review and examples
   - **Test:** Documentation build validation

**Phase 4 Deliverables:**

- ✅ Complete integration tests (~900-1,150 lines tests)
- ✅ Complete unit test coverage (~300-450 lines tests)
- ✅ API documentation complete with examples
- ✅ >80% total test coverage achieved (~4,800-6,650 lines total tests)
- ✅ All JSDoc documentation complete and verified

**Dependencies:** Phase 1-3 (complete implementation for testing)

---

### Roadmap Summary

| Phase       | Time          | Complexity | Deliverables                                                          | Lines Added                           |
| ----------- | ------------- | ---------- | --------------------------------------------------------------------- | ------------------------------------- |
| **Phase 1** | 12-16 hrs     | Low        | Types, integration, stub builder, helpers (4 tasks)                   | ~500-600 + ~400-550 tests             |
| **Phase 2** | 20-28 hrs     | Medium     | Complete QueryBuilder - 9 resource types (9 tasks)                    | ~700-800 + ~800-1,000 tests           |
| **Phase 3** | 13-24 hrs     | High       | Format parsers + extensions (16 tasks; validators removed from scope) | ~3,400-4,650 + ~2,200-3,100 tests     |
| **Phase 4** | 9-12 hrs      | Medium     | Tests and documentation (3 tasks)                                     | ~1,200-1,600 tests                    |
| **TOTAL**   | **54-80 hrs** | **Mixed**  | **Complete CSAPI implementation (32 tasks; validators removed)**      | **~4,600-6,050 + ~4,600-6,250 tests** |

**Total Development Time:** 57-84 hours (average: 71 hours)  
**Calendar Time:** 8-11 weeks (assuming 6-8 hours/week development pace)  
**Total Code:** ~9,600-13,100 lines (implementation + tests)

**Key Success Factors:**

- ✅ Write JSDoc documentation AS YOU CODE (don't defer)
- ✅ Write method signatures before implementation (design first)
- ✅ **Write tests IMMEDIATELY after each subtask** (see Testing Cadence in Development Standards below)
- ✅ Validate against spec examples throughout
- ✅ Use helper methods for code reuse (prevents duplication)
- ✅ Follow three-tier type hierarchy (prevents circular dependencies)
- ✅ Test edge cases and errors as discovered (don't batch)
- ✅ Document edge cases in JSDoc immediately
- ✅ Review coverage after each subtask (aim for >80%)
- ✅ **Respect dependencies** (SWE Common types before SensorML types)
- ✅ Update this roadmap if estimates change

**Confidence:** ⭐⭐⭐⭐⭐ (5/5) - Based on 13 research plans and component-level estimates

---

## Development Standards

**Recommended Development Workflow:**

1. Write method signatures before implementation
2. Add comprehensive JSDoc comments with parameters, return types, examples
3. Implement functionality with inline documentation for complex logic
4. **Write tests immediately after completing each subtask (not batched)**
5. Document edge cases and validation rules as discovered
6. Add usage examples to JSDoc for common scenarios
7. Validate against spec examples throughout
8. Update documentation as you go - don't defer

**Testing Cadence:**

- **Maximum 2-3 hours between test checkpoints** (33 checkpoints across 33 tasks)
- **Maximum ~800 lines of behavioral code without tests** (type-only files exempt; see Task 3.5 note)
- Write tests while method details are fresh — never batch tests at end of phase
- Aim for >80% coverage after each subtask

**Testing Conventions:**

- **HTTP Mocking:** Use `globalThis.fetch = vi.fn()` (Vitest) or `jest.fn()` for all HTTP mocking. Never use `nock`, `msw`, or other external mocking libraries. See Guide §9 for code examples.
- **Meaningful vs Trivial Tests:** Every test should verify a meaningful behavior — not just that code runs without throwing. Test that URL parameters are correctly encoded, that input validators reject invalid input, that parsers extract the right properties. See [Doc 06](../research/testing/findings/06-meaningful-vs-trivial-testing.md) for the full standard.
- **Anti-Pattern Catalog (AP1-AP5):** Avoid these testing anti-patterns documented in Guide §16 and [Phase 0 review](../research/testing/review/phase-0-scope-assessment.md):

| Anti-Pattern                    | Rule                                                | Example Violation                             |
| ------------------------------- | --------------------------------------------------- | --------------------------------------------- |
| AP1: Testing Response Content   | Don't assert fixture data values as "correct"       | `expect(system.name).toBe('Weather Station')` |
| AP2: Live Server Dependencies   | Never call real servers in tests                    | `fetch('https://api.example.com/...')`        |
| AP3: Server Conformance Testing | Don't test OGC requirement IDs                      | `it('meets /req/core/root-success')`          |
| AP4: Asserting Data Shape       | Don't assert fixture structure as specification     | `expect(response).toHaveProperty('links')`    |
| AP5: Graceful Skipping          | Don't skip tests conditionally by server capability | `if (!hasCSAPI) return`                       |

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

**Document:** CSAPI Implementation Roadmap (Standalone)  
**Version:** 3.6 (Feature-Level Validators Removed from Scope)  
**Date:** February 15, 2026  
**Status:** ✅ **IMPLEMENTATION READY** - Roadmap complete with incremental testing, correct dependencies, and validator scope decision

**Version 3.6 - Feature-Level Validators Removed from Scope (February 15, 2026):**

- **Phase 3 Task 3 (Validator Extensions) removed from scope** — no upstream precedent for a formal validation framework (STAC has inline checks, but WMS/WFS/WMTS/TMS have zero; no handler has `validate*()` functions or `ValidationError` types)
- Updated Phase 3 Task 1 smoke test note (F49): decision changed from "decouple" to "remove entirely"
- Updated Phase 3 deliverables, summary table, and total estimates
- Removed format round-tripping and validation error tests from Phase 4 Integration Tests
- Task count reduced from 33 to 32; time estimate reduced by ~3-4 hours
- Issue #52 updated to reflect full validator removal
- Design notes document updated: `docs/implementation/design-notes-validation-extraction-decoupling.md`
- Version bumped to 3.6

**Version 3.5 - Phase 3.2 Smoke Test Finding F49 — Validation/Extraction Decoupling (February 15, 2026):**

- Added smoke test note to Phase 3 Task 1 (GeoJSON Handler): F49 validation-as-gate blocks extraction of recognized features (Issue #52)
- Added design decision reminder to Phase 3 Task 3 (Validator Extensions): validation is opt-in diagnostics, never an extraction gate
- Design notes document: `docs/implementation/design-notes-validation-extraction-decoupling.md`
- Created Issue #52: Decouple validation from extraction in `extractCSAPIFeature`
- Version bumped to 3.5

**Version 3.4 - Phase 3.1 Smoke Test Findings F40-F46 Integrated (February 15, 2026):**

- Added smoke test notes to Phase 3 Task 1 (GeoJSON Handler): F40 non-SOSA vocabulary (Issue #49), F43 procedure misclassification
- Added smoke test notes to Phase 3 Task 2 (Format Detector): F41 null featureType fallback (Issue #50), F45 envelope variation, F46 OSH ignores SensorML Accept header
- Created Issue #49 for F40 (Critical): Extend GeoJSON handler vocabulary for SensorML SamplingFeature
- Created Issue #50 for F41 (Critical): Deferred to response parser — endpoint-context fallback for null featureType
- Version bumped to 3.4

**Version 3.3 - Smoke Test Findings F34-F39 Integrated (February 14, 2026):**

- Added smoke test notes to Phase 3 Task 1 (GeoJSON Handler): F34 fallback routing, F38 `command@id` cross-reference, F39 `items` envelope confirmation
- Added smoke test notes to Phase 3 Task 3 (Validator): F35 cancel limitation, F36 `id` filter quirk, F37 result-less commands
- Added smoke test note to Phase 3 Task 14 (SWE Common Main Parser): F33 schema duality (`commandFormat`/`parametersSchema` vs `observationFormat`/`resultSchema`)
- Added smoke test notes to Phase 4 Task 1 (Integration Tests): F34 fallback routing tests, F35/F37 negative-path tests, cumulative 15-entry server limitation matrix
- Created Issue #47 for F34 (Critical): Phase 3 fallback routing for Commands
- Version bumped to 3.3

**Version 3.2 - A2 Alignment — Estimates & Test Ranges Reconciled (February 5, 2026):**

- All 80 method references aligned (previously "70-80")
- Test line range annotated with Doc 19 authoritative per-file breakdown (4,040-5,340)
- Phase 3 task count corrected to 17 tasks (from 15)
- sortBy/sortOrder added to Phase 2 Task 2.7 Observations
- Task 1.1 note: factory method returns new class, not OgcApiEndpoint subclass
- Task 3.1/3.3/3.5 wording, scope, and spec references refined
- Scope Exclusions section added (performance, real-world, migration testing)
- Development Standards expanded with AP catalog, globalThis.fetch, testing cadence
- Resolves all 19 actionable A2 audit findings

**Version 3.1 - Worker Extensions Removed from Scope (February 5, 2026):**

- Removed Phase 4 Task 4.1 (Worker Extensions — 9 CSAPI message types, ~3-4 hours)
- **Rationale:** No upstream JSON-based API (EDR, STAC, TMS, OGC API) uses the Web Worker infrastructure. Only XML-based APIs (WMS, WFS, WMTS) offload parsing to workers. CSAPI is JSON-based following the EDR pattern — `response.json()` does not benefit from worker offloading. All 9 proposed message types had zero upstream precedent.
- Phase 4 reduced from 4 tasks (12-16 hrs) to 3 tasks (9-12 hrs)
- Total tasks reduced from 34 to 33
- Phase 4 renamed from "Worker Extensions and Tests" to "Tests and Documentation"
- Binary SWE parsing remains in scope at parser level (Phase 3 Task 3.13); only worker offloading is removed

**Version 3.0 - Phase 3 Restructure (February 5, 2026):**

- Restructured Phase 3 from 7 tasks (2 massive 5-10 hour tasks) into **17 granular subtasks**
- Each subtask now implements one component, then tests immediately (implement → test → commit)
- **Fixed critical dependency**: SWE Common types (Task 4) now created **before** SensorML types (Task 5) that depend on them
- Prevents test debt: max 800 lines without tests (Task 5 or 9), not 2,900 lines
- Creates natural checkpoints every 1-3 hours instead of 5-10 hour blocks
- Aligns with Development Standards and Phases 1 & 2: test immediately after each subtask
- Total time unchanged (16-28 hours), but distributed across 17 checkpoints
- Task count increased from 24 to 34 total tasks (more granular tracking)

**Previous Versions:**

- [v2.0 (archived)](archive/ROADMAP-v2.0.md) - Phase 2 restructured, Phase 3 had testing debt issue
- [v1.0 (archived)](archive/ROADMAP-v1.0.md) - Original standalone roadmap with monolithic phases

**Roadmap Source:**
This roadmap is based on the Implementation Roadmap section from the complete [CSAPI Implementation Guide](csapi-implementation-guide.md), which contains:

- 13 completed research plans with ⭐⭐⭐⭐⭐ confidence (98-100%)
- Complete architectural decisions and component specifications
- Detailed implementation guidance for all 24 files
- Development standards and integration patterns

**Implementation Guide Version History:**
For the complete version history of the architectural research and implementation planning, see the [CSAPI Implementation Guide](csapi-implementation-guide.md) version history section.
