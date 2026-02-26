# Component Design Sequence

This document defines the optimal order for designing each CSAPI component to minimize rework and ensure each component builds on knowledge from previous ones.

## Design Checklist

### Phase 1: Foundation & Integration

Components that establish how CSAPI is accessed and what capabilities are available.

- [x] **1. OgcApiEndpoint Integration** (`ogcapiendpoint-integration/`)

  - ✅ **RESEARCH COMPLETE**
  - Entry point for everything; defines how CSAPI is accessed
  - Establishes the `endpoint.csapi(collectionId)` factory method pattern
  - Analysis: Factory method, caching, type system all documented
  - Implementation: ~65 lines across 3 files (endpoint.ts, info.ts, index.ts)
  - Dependencies: None

- [x] **2. Conformance Reader** (`conformance-reader/`)

  - ✅ **RESEARCH COMPLETE**
  - Determines if a service supports CSAPI
  - Adds `checkHasConnectedSystems()` function in info.ts
  - Adds `hasConnectedSystems` getter to endpoint.ts
  - Analysis: Function signature, detection logic (Part 1 OR Part 2), testing strategy documented
  - Implementation: ~7 lines total (simplest component in design)
  - Dependencies: None

- [x] **3. Collections Reader** (`collections-reader/`)
  - ✅ **RESEARCH COMPLETE**
  - Identifies which collections have CSAPI features
  - Extends `parseCollections()` function in info.ts
  - Adds `csapiCollections` getter to endpoint.ts
  - Analysis: Detection strategy (featureType + itemType checks), filter logic, testing strategy documented
  - Implementation: ~15 lines total (extend function + add getter)
  - Dependencies: Conformance Reader (uses `hasConnectedSystems` getter)

### Phase 2: Core Functionality

The main component that defines all URL patterns, methods, and query parameters.

- [ ] **4. CSAPIQueryBuilder** (`csapiquerybuilder/`)
  - **The heart of the implementation (70% of code)**
  - Defines all URL patterns for 9 resource types
  - Defines all query parameters and filtering logic
  - Dependencies: OgcApiEndpoint Integration (needs factory method pattern)
  - Informs: All handlers (defines what data structures to parse), Validator (defines what to validate)

### Phase 3: Data Parsing

Components that parse and convert various CSAPI formats into TypeScript objects.

- [ ] **5. GeoJSON Handler** (`geojson-handler/`)

  - Simplest format, handles Part 1 resources
  - Extends existing GeoJSON parser with CSAPI-specific properties
  - Dependencies: CSAPIQueryBuilder (knows what resource types exist)

- [ ] **6. SensorML Handler** (`sensorml-handler/`)

  - Complex format for System/Procedure details
  - New parser for SensorML 3.0 documents
  - Dependencies: CSAPIQueryBuilder (knows what endpoints return SensorML)

- [ ] **7. SWE Common Handler** (`swe-common-handler/`)
  - Most complex format with JSON/Text/Binary encodings
  - New parser for SWE Common 3.0 data components
  - Dependencies: CSAPIQueryBuilder (knows DataStream/Observation structure), SensorML Handler (SWE Common used in SensorML)

### Phase 4: Supporting Infrastructure

Components that detect formats and validate data structures.

- [ ] **8. Format Detector** (`format-detector/`)

  - Now that we know all formats, design detection/routing
  - Adds SensorML 3.0 and SWE Common 3.0 media types
  - Dependencies: All Handlers (needs to know all format types)

- [ ] **9. Validator** (`validator/`)
  - Now that we know all data structures, design validation rules
  - Extends existing validation framework with CSAPI rules
  - Dependencies: All Handlers (needs to know all data structures), CSAPIQueryBuilder (knows all constraints)

### Phase 5: Optimization & Quality

Components for performance, testing, and documentation.

- [ ] **10. Background Processing** (`background-processing/`)

  - Now that we know what's computationally expensive, design worker offloading
  - Extends existing Web Worker with CSAPI message types
  - Dependencies: All Handlers (knows what operations are expensive)

- [ ] **11. Test Coverage** (`test-coverage/`)

  - Now that all APIs are designed, plan comprehensive testing
  - Extends existing Jest framework with CSAPI test suites
  - Dependencies: All components (needs to test everything)

- [ ] **12. API Documentation** (`api-documentation/`)
  - Final step: document everything
  - Extends existing TypeDoc with CSAPI documentation
  - Dependencies: All components (documents entire API surface)

---

## Design Workflow

For each component:

1. **Research Phase**

   - Study upstream patterns (especially PR #114 EDR implementation)
   - Review CSAPI specifications (Part 1, Part 2, OpenAPI specs)
   - Analyze requirements documents in `docs/research/requirements/`
   - Document findings in component's design folder

2. **Design Phase**

   - Create detailed design document with:
     - Interface/class signatures
     - Method signatures with parameters
     - Data structures (TypeScript types/interfaces)
     - Integration points with existing code
     - Error handling approach
   - Review against implementation guide

3. **Validation Phase**

   - Confirm design aligns with upstream patterns
   - Verify completeness against CSAPI specs
   - Check for consistency with previous component designs
   - Update this checklist when complete

4. **Move to Next Component**
   - Mark component as complete (check the box)
   - Use learnings to inform next component design

---

## Key Principle

**This order minimizes rework** - each component builds on concrete knowledge from previous ones rather than making assumptions that might need revision later.

Example: Don't design validation rules before knowing what data structures exist. Don't design worker offloading before knowing what operations are expensive.
