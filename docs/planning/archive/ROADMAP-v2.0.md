# CSAPI Implementation Roadmap

**Last Updated:** February 5, 2026  
**Version:** 2.0 (Phase 2 Restructure - Incremental Testing)

---

## Executive Summary

This roadmap outlines the complete implementation plan for adding Connected Systems API (CSAPI) support to the Camptocamp OGC Client Library. The work is organized into four sequential phases spanning **60-88 hours of development time** (8-12 weeks calendar time).

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
- **Phase 2: QueryBuilder (20-28 hours)** - Complete URL building for all 70-80 CSAPI methods across 9 resource types (9 tasks, one per resource type)
- **Phase 3: Format Handling (16-28 hours)** - SensorML/SWE parsers + GeoJSON/Format Detector/Validator extensions (7 tasks)
- **Phase 4: Worker & Tests (12-16 hours)** - Worker extensions, integration tests, documentation completion (4 tasks)

**Total Scope:**

- **Implementation:** ~4,850-6,500 lines across 24 files
- **Tests:** ~4,400-6,300 lines across 17 test files
- **Total Code:** ~9,250-12,800 lines

**Key Dependencies:**

- Phase 1 → Phase 2 (types required for QueryBuilder)
- Phase 2 → Phase 3 (QueryBuilder required for format integration tests)
- Phases 1-3 → Phase 4 (complete implementation required for full testing)

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

2. **Create Helper Utilities** (~3-4 hours, Low complexity)

   - Create `src/ogc-api/csapi/helpers.ts` (~50-80 lines)
   - Implement `buildResourceUrl(resourceType, id?, subPath?, options?)` - core URL construction
   - Implement `buildQueryString(options?)` - parameter serialization with encoding
   - Implement URL encoding utilities, temporal parsing utilities, validation utilities
   - **Write JSDoc:** Document each utility function with parameter descriptions, examples
   - **Test:** Add helper tests (~100-150 lines for helpers)

3. **Create Stub QueryBuilder** (~2-3 hours, Low complexity)

   - Create `src/ogc-api/csapi/url_builder.ts` (stub with constructor + 1-2 methods)
   - Implement constructor with collection info parameter
   - Implement `extractAvailableResources()` helper for resource discovery
   - Create `availableResources` property (Set<string>)
   - Implement 1-2 simple methods (e.g., `getSystems()`, `getSystem(id)`) as proof of concept
   - Validate resource availability before URL construction
   - **Write JSDoc:** Document constructor, helper methods, and validation pattern
   - **Test:** Create `url_builder.spec.ts` with basic tests for constructor and resource validation (~100-150 lines)

4. **Integrate with OgcApiEndpoint** (~3-4 hours, Low complexity)
   - Modify `src/ogc-api/endpoint.ts` (+35 lines)
     - Add import for CSAPIQueryBuilder
     - Add cache field for QueryBuilder instances
     - Add `csapiCollections` getter (6 lines)
     - Add `hasConnectedSystems` getter (6 lines)
     - Add `csapi(collectionId)` factory method (17 lines)
   - Modify `src/ogc-api/shared/info.ts` (+12 lines)
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

**Goal:** Implement all 70-80 QueryBuilder methods for all 9 CSAPI resource types, with incremental testing after each resource type.

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
     - Test schema retrieval
     - Test observation creation
     - Test cursor-based pagination

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
     - Test result format handling

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

- ✅ All 70-80 QueryBuilder methods implemented (9 resource types)
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

**Goal:** Build format parsers for SensorML 3.0 and SWE Common 3.0, extend GeoJSON/Format Detector/Validator for CSAPI.

**Tasks:**

1. **GeoJSON Handler Extensions** (~2-3 hours, Medium complexity)

   - Extend existing GeoJSON parser in library
   - Add recognition for CSAPI `featureType` property (sosa:System, sosa:Deployment, etc.)
   - Extract CSAPI-specific properties (uniqueIdentifier, systemType, assetType, validTime, etc.)
   - Add validation for CSAPI GeoJSON requirements (uniqueIdentifier must be URI, systemType from SOSA vocabulary)
   - **Write JSDoc:** Document CSAPI property extraction, validation rules
   - **Test:** Add tests for CSAPI GeoJSON parsing (~150-300 lines tests)

2. **Format Detector Extensions** (~1-2 hours, Low complexity)

   - Extend existing format detector
   - Register 4 new media types: `application/sml+json`, `application/swe+json`, `application/swe+text`, `application/swe+binary`
   - Add routing logic to format handlers (SensorML → SensorML parser, SWE Common → SWE Common parser)
   - Add Content-Type header parsing, structure-based fallback detection
   - **Write JSDoc:** Document media type detection patterns
   - **Test:** Add format detection tests (~50-100 lines tests)

3. **Validator Extensions** (~3-4 hours, Medium complexity)

   - Extend existing validation framework
   - Add CSAPI Part 1 validation rules (required properties, URI formats, temporal validity, spatial constraints)
   - Add CSAPI Part 2 validation rules (schema conformance for Observations/Commands, result validation)
   - Add cross-reference validation (association links, hierarchical integrity, vocabulary references)
   - **Write JSDoc:** Document validation rules, error reporting patterns
   - **Test:** Add validation tests (~200-400 lines tests)

4. **SensorML Parser** (~5-10 hours, High complexity)

   - Create `src/ogc-api/csapi/formats/sensorml/` directory
   - Create `types.ts` (~800-1,200 lines)
     - Define PhysicalSystem, PhysicalComponent, SimpleProcess, AggregateProcess interfaces
     - Define CapabilityList, CharacteristicList, ComponentList, ConnectionList interfaces
     - Link to SWE Common types for capability/characteristic values
   - Create `parser.ts` (~600-800 lines)
     - Main SensorML 3.0 parser with recursive component parsing
     - Capability/characteristic parsing with SWE Common integration
     - Position/location parsing
   - Create sub-parsers (~550-700 lines total)
     - `simple-process.ts` (~150-200 lines)
     - `aggregate-process.ts` (~200-250 lines)
     - `physical-system.ts` (~200-250 lines)
   - Create `index.ts` (~50-100 lines) - barrel file exports
   - **Write JSDoc:** Document all SensorML types and parser functions with SensorML 3.0 spec references
   - **Test:** Add SensorML parser tests (~600-800 lines tests)

5. **SWE Common Parser** (~5-10 hours, High complexity)

   - Create `src/ogc-api/csapi/formats/swecommon/` directory
   - Create `types.ts` (~600-800 lines)
     - Define DataComponent union type and all component interfaces
     - Define DataRecord, DataArray, Quantity, Count, Text, Boolean, Time, etc.
     - Define Encoding interfaces (JSONEncoding, TextEncoding, BinaryEncoding)
   - Create `parser.ts` (~500-700 lines)
     - Main SWE Common 3.0 parser with component type discrimination
     - Encoding detection (JSON/Text/Binary)
     - Schema validation against DataComponent definitions
   - Create sub-parsers (~650-850 lines total)
     - `data-record.ts` (~150-200 lines)
     - `data-array.ts` (~200-250 lines)
     - `components.ts` (~300-400 lines) - all simple component types
   - Create `index.ts` (~50-100 lines) - barrel file exports
   - **Write JSDoc:** Document all SWE Common types and parser functions with SWE Common 3.0 spec references
   - **Test:** Add SWE Common parser tests (~800-1,000 lines tests)

6. **Format Constants** (~1-2 hours, Low complexity)

   - Create `src/ogc-api/csapi/formats/constants.ts` (~50-100 lines)
   - Define media type constants
   - Define resource type constants
   - Define vocabulary URI constants (SOSA, SSN, CF, QUDT)
   - **Write JSDoc:** Document constant values and usage
   - **Test:** Constants validated by format detector tests

7. **Format Index** (~1-2 hours, Low complexity)
   - Create `src/ogc-api/csapi/formats/index.ts` (~50-100 lines)
   - Barrel file exporting all parsers
   - Tree-shaking friendly exports
   - **Write JSDoc:** Document format imports and usage patterns
   - **Test:** Integration tests verify exports

**Phase 3 Deliverables:**

- ✅ GeoJSON CSAPI extensions (~150-300 lines)
- ✅ Format Detector extensions (~50-100 lines)
- ✅ Validator extensions (~200-400 lines)
- ✅ SensorML parser complete (~1,600-2,200 lines)
- ✅ SWE Common parser complete (~1,600-2,250 lines)
- ✅ Format constants and index (~100-200 lines)
- ✅ Comprehensive format tests (~2,400-3,500 lines tests)
- ✅ All JSDoc documentation for format handlers

**Dependencies:** Phase 1 (type system), Phase 2 (QueryBuilder for integration tests)

---

### Phase 4: Worker Extensions and Tests (Medium-High Complexity)

**Estimated Time:** 12-16 hours (1.5-2 weeks calendar time)

**Goal:** Extend Web Worker for CSAPI operations, add comprehensive tests, complete documentation.

**Tasks:**

1. **Worker Extensions** (~3-4 hours, Medium complexity)

   - Extend existing Web Worker in `src/worker/`
   - Add 9 new CSAPI message types:
     - `PARSE_SENSORML_3` - SensorML 3.0 parsing
     - `PARSE_SWE_RESULT` - SWE Common result parsing (JSON/Text/Binary)
     - `PARSE_SWE_BINARY` - Binary decoding
     - `VALIDATE_OBSERVATIONS` - Observation schema validation
     - `VALIDATE_COMMANDS` - Command parameter validation
     - `PARSE_OBSERVATION_ARRAY` - Large observation arrays
     - `TRAVERSE_HIERARCHY` - Recursive system traversal
     - `FILTER_SPATIAL` - Bbox filtering
     - `FILTER_TEMPORAL` - Temporal filtering
   - Integrate SensorML and SWE Common parsers
   - Add fallback for non-worker environments
   - **Write JSDoc:** Document message types, payload structures, performance characteristics
   - **Test:** Add worker tests (~200-300 lines tests)

2. **Integration Tests** (~4-6 hours, Medium complexity)

   - Create end-to-end workflow tests (~500-800 lines)
   - Discovery workflow: connect → check conformance → list collections → retrieve resources
   - Observation workflow: systems → datastreams → observations → pagination → parsing
   - Command workflow: systems → control streams → feasibility → submit → status → result
   - Cross-resource navigation: system → deployments → procedures → sampling features → datastreams → observations
   - Format round-tripping: parse → validate → modify → serialize → parse
   - Hierarchical queries: recursive traversal with large hierarchies
   - Error handling: server errors, validation errors, network errors, malformed responses
   - **Write JSDoc:** Document test scenarios and expected behavior
   - **Test:** All integration tests (~500-800 lines)

3. **Unit Tests Completion** (~3-4 hours, Medium complexity)

   - Complete coverage for all QueryBuilder methods (~200-300 additional lines)
   - Complete coverage for all helper functions (~100-150 lines)
   - Edge case tests: empty collections, minimal resources, boundary conditions
   - Error case tests: invalid parameters, malformed URLs, resource validation failures
   - Pagination tests: offset-based and cursor-based
   - Query parameter tests: all spatial, temporal, relationship, hierarchical parameters
   - **Write JSDoc:** Document test cases and coverage goals
   - **Test:** All unit tests (~300-450 lines)

4. **API Documentation** (~2-3 hours, Low complexity)
   - Extend TypeDoc configuration for CSAPI types
   - Verify all JSDoc comments complete and accurate
   - Add usage examples to main classes (OgcApiEndpoint, CSAPIQueryBuilder)
   - Add format parser examples (parseSensorML30, parseSWEDataRecord)
   - Add migration guide for users of other CSAPI clients
   - Add error handling examples
   - **Write JSDoc:** Complete documentation review and examples
   - **Test:** Documentation build validation

**Phase 4 Deliverables:**

- ✅ Worker extensions with 9 CSAPI message types (~50 lines)
- ✅ Complete integration tests (~500-800 lines tests)
- ✅ Complete unit test coverage (~300-450 lines tests)
- ✅ API documentation complete with examples
- ✅ >80% total test coverage achieved (~4,500-6,000 lines total tests)
- ✅ All JSDoc documentation complete and verified

**Dependencies:** Phase 1-3 (complete implementation for testing)

---

### Roadmap Summary

| Phase       | Time          | Complexity  | Deliverables                                        | Lines Added                           |
| ----------- | ------------- | ----------- | --------------------------------------------------- | ------------------------------------- |
| **Phase 1** | 12-16 hrs     | Low         | Types, integration, stub builder, helpers (4 tasks) | ~500-600 + ~400-550 tests             |
| **Phase 2** | 20-28 hrs     | Medium      | Complete QueryBuilder - 9 resource types (9 tasks)  | ~700-800 + ~800-1,000 tests           |
| **Phase 3** | 16-28 hrs     | High        | Format parsers + extensions (7 tasks)               | ~3,600-5,050 + ~2,400-3,500 tests     |
| **Phase 4** | 12-16 hrs     | Medium-High | Worker, tests, documentation (4 tasks)              | ~50 + ~800-1,250 tests                |
| **TOTAL**   | **60-88 hrs** | **Mixed**   | **Complete CSAPI implementation (24 tasks)**        | **~4,850-6,500 + ~4,400-6,300 tests** |

**Total Development Time:** 60-88 hours (average: 74 hours)  
**Calendar Time:** 8-12 weeks (assuming 6-8 hours/week development pace)  
**Total Code:** ~9,250-12,800 lines (implementation + tests)

**Key Success Factors:**

- ✅ Write JSDoc documentation AS YOU CODE (don't defer)
- ✅ Write method signatures before implementation (design first)
- ✅ **Write tests IMMEDIATELY after each subtask** (Phase 2: test each resource type before moving to next)
- ✅ Validate against spec examples throughout
- ✅ Use helper methods for code reuse (prevents duplication)
- ✅ Follow three-tier type hierarchy (prevents circular dependencies)
- ✅ Test edge cases and errors as discovered (don't batch)
- ✅ Document edge cases in JSDoc immediately
- ✅ Review coverage after each subtask (aim for >80%)
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
**Version:** 2.0 (Phase 2 Restructure - Incremental Testing)  
**Date:** February 5, 2026  
**Status:** ✅ **IMPLEMENTATION READY** - Roadmap complete with incremental testing strategy

**Version 2.0 - Phase 2 Restructure (February 5, 2026):**

- Restructured Phase 2 from 2 large tasks into **9 granular subtasks** (one per resource type)
- Each subtask now includes immediate test writing (implement → test → commit)
- Prevents test debt accumulation (max 12 methods without tests, not 70)
- Validates architecture incrementally (helper functions tested with Systems, not Commands)
- Creates natural checkpoints for commits and rollbacks
- Aligns with Development Standards: "Write tests as you implement (not deferred to later)"
- Aligns with Phase 1 pattern: test after each task
- Total time unchanged (20-28 hours), but better distributed across 9 checkpoints
- Phase 1 task order corrected: Types → Helpers → QueryBuilder → Integration

**Previous Versions:**

- [v1.0 (archived)](archive/ROADMAP-v1.0.md) - Original standalone roadmap with 2-task Phase 2 structure

**Roadmap Source:**
This roadmap is based on the Implementation Roadmap section from the complete [CSAPI Implementation Guide](csapi-implementation-guide.md), which contains:

- 13 completed research plans with ⭐⭐⭐⭐⭐ confidence (98-100%)
- Complete architectural decisions and component specifications
- Detailed implementation guidance for all 24 files
- Development standards and integration patterns

**Implementation Guide Version History:**
For the complete version history of the architectural research and implementation planning, see the [CSAPI Implementation Guide](csapi-implementation-guide.md) version history section.
