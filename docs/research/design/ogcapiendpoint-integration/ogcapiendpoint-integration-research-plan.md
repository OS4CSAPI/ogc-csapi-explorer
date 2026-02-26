# OgcApiEndpoint Integration - Design Research Plan

**Component:** OgcApiEndpoint Integration  
**Design Phase:** Phase 1 - Foundation & Integration (Component #1)  
**Status:** ✅ RESEARCH COMPLETE

---

## Purpose

Define the exact code changes needed to integrate CSAPI into the existing `OgcApiEndpoint` class, following the proven EDR pattern from PR #114. This is the entry point for all CSAPI functionality - must be designed correctly to ensure smooth developer experience.

---

## Context

From the [Implementation Guide](../../../planning/csapi-implementation-guide.md#ogcapiendpoint-integration-extending-main-endpoint-class):

- **Scope:** ~48 lines across 2-3 files (endpoint.ts, info.ts, index.ts)
- **Pattern:** Factory method that returns CSAPIQueryBuilder instance
- **Blueprint:** PR #114 EDR implementation (`endpoint.edr()` → returns `EDRQueryBuilder`)
- **Key Method:** `endpoint.csapi(collectionId)` → returns `CSAPIQueryBuilder`

---

## Research Objectives

1. **Understand the factory method pattern** used in EDR implementation
2. **Identify exact integration points** in existing endpoint.ts, info.ts, index.ts files
3. **Define the method signature** for `endpoint.csapi(collectionId)`
4. **Determine caching strategy** (does QueryBuilder get cached per collection?)
5. **Understand lifecycle management** (when is QueryBuilder instantiated? disposed?)
6. **Define error handling** (what happens if collection doesn't support CSAPI?)
7. **Understand collection validation** (how to verify collection has CSAPI features?)

---

## Critical Questions

### 1. Factory Method Pattern

**Study:** PR #114 `endpoint.edr()` implementation in endpoint.ts

**Questions:**

- [x] What is the exact method signature for `endpoint.edr()`?

  - **Answer:** `public async edr(collection_id: string): Promise<EDRQueryBuilder>` - Single collection_id parameter, async, returns QueryBuilder Promise

- [x] What parameters does it accept?

  - **Answer:** One required string parameter: `collection_id` - the collection identifier

- [x] What does it return (class name, interface)?

  - **Answer:** Returns `Promise<EDRQueryBuilder>` - async factory that resolves to QueryBuilder instance

- [x] Is it async or sync?

  - **Answer:** **ASYNC** - must fetch collection metadata before instantiation

- [x] What validation/checks happen before returning QueryBuilder?
  - **Answer:** 1) Conformance check (`hasEnvironmentalDataRetrieval`), 2) Cache lookup, 3) Collection metadata fetch via `getCollectionInfo()`, 4) QueryBuilder instantiation with validation

### 2. Integration Points in endpoint.ts

**Study:** PR #114 modifications to src/shared/endpoint.ts

**Questions:**

- [x] Where in the endpoint.ts file is the factory method added?

  - **Answer:** Line ~283 (after `hasEnvironmentalDataRetrieval` getter, before `tileMatrixSets` getter)

- [x] What imports are added at the top of endpoint.ts?

  - **Answer:** `import EDRQueryBuilder from './edr/url_builder.js';` (line ~50) - adapt to `import CSAPIQueryBuilder from './csapi/url_builder.js';`

- [x] How many lines of code are added to endpoint.ts?

  - **Answer:** ~43 lines total: 1 import, 2 cache field, 6 collections getter, 17 factory method, 9 conformance getter, 8 for spacing

- [x] Are there any dependencies on other endpoint methods/properties?

  - **Answer:** YES - depends on `hasConnectedSystems` getter, `getCollectionInfo()` method, and `data` property

- [x] How does it access endpoint URL, headers, fetch implementation?
  - **Answer:** Passes `OgcApiCollectionInfo` object to QueryBuilder constructor - QueryBuilder extracts URLs from collection metadata links

### 3. Caching Strategy

**Study:** PR #114 QueryBuilder instantiation and reuse patterns

**Questions:**

- [x] Is the QueryBuilder instance cached?

  - **Answer:** **YES** - cached in `Map<string, EDRQueryBuilder>` to prevent redundant HTTP requests

- [x] If cached, where is the cache stored (class property, WeakMap)?

  - **Answer:** Private class property: `private collection_id_to_edr_builder_: Map<string, EDRQueryBuilder> = new Map();`

- [x] Is caching per-collection or per-endpoint?

  - **Answer:** **Per-collection** - cache key is `collection_id` string, each endpoint instance has own cache

- [x] When is the cache cleared/invalidated?

  - **Answer:** **Never** - cache lives for endpoint lifetime, user creates new endpoint instance if metadata changes

- [x] What's the reasoning for cache vs no-cache approach?
  - **Answer:** Performance optimization - eliminates redundant `getCollectionInfo()` HTTP requests, ensures consistent builder instance

### 4. Collection Validation

**Study:** How EDR validates collections support EDR queries

**Questions:**

- [x] Does `endpoint.edr()` accept a collectionId parameter?

  - **Answer:** **YES** - required string parameter `collection_id`

- [x] How does it validate the collection exists?

  - **Answer:** Calls `await this.getCollectionInfo(collection_id)` which throws if collection doesn't exist

- [x] How does it validate the collection supports EDR?

  - **Answer:** Checks `!this.hasEnvironmentalDataRetrieval` and throws `EndpointError` if false

- [x] What error is thrown if validation fails?

  - **Answer:** `throw new EndpointError('Endpoint does not support EDR')` for conformance failure, standard error from `getCollectionInfo()` for missing collection

- [x] Does validation happen sync or async?
  - **Answer:** **ASYNC** - `hasEnvironmentalDataRetrieval` is a Promise getter, `getCollectionInfo()` is async

### 5. Type Definitions

**Study:** TypeScript types/interfaces related to factory method

**Questions:**

- [x] What is the return type declaration for the factory method?

  - **Answer:** `Promise<EDRQueryBuilder>` - fully typed async return

- [x] Are there any generic type parameters?

  - **Answer:** **NO** - no generics used in factory method signature

- [x] What types are exported from index.ts for this integration?

  - **Answer:** `export { default as OgcApiEndpoint } from './ogc-api/endpoint.js';` and `export * from './ogc-api/model.js';` (EDR types)

- [x] How is the QueryBuilder class type imported/referenced?
  - **Answer:** Direct import at top of endpoint.ts: `import EDRQueryBuilder from './edr/url_builder.js';` then used in return type

### 6. Error Handling

**Study:** Error handling patterns in EDR factory method

**Questions:**

- [x] What errors can the factory method throw?

  - **Answer:** 1) `EndpointError` if `!hasEnvironmentalDataRetrieval`, 2) Error from `getCollectionInfo()` if collection doesn't exist, 3) Error from QueryBuilder constructor if metadata invalid

- [x] What are the error messages?

  - **Answer:** `'Endpoint does not support EDR'` for conformance failure, collection-specific messages for missing/invalid metadata

- [x] Are custom error classes used?

  - **Answer:** **YES** - `EndpointError` imported from `'./shared/errors.js'` for endpoint-level errors

- [x] How are network errors vs validation errors distinguished?
  - **Answer:** Network errors bubble up from HTTP layer, validation errors are explicit `throw new EndpointError()` or `throw new Error()` statements

### 7. Dependencies and Context

**Study:** What context/state the factory method needs access to

**Questions:**

- [x] Does the factory method need access to endpoint.\_info?

  - **Answer:** **NO** - only needs `hasEnvironmentalDataRetrieval` getter and `getCollectionInfo()` method

- [x] Does it need access to collections metadata?

  - **Answer:** **YES** - calls `await this.getCollectionInfo(collection_id)` to fetch collection metadata object

- [x] What information is passed to the QueryBuilder constructor?

  - **Answer:** Single parameter: `OgcApiCollectionInfo` object with collection metadata including `data_queries`, `parameter_names`, links, etc.

- [x] How does QueryBuilder get endpoint URL, auth headers, fetch?
  - **Answer:** Extracts base URLs from `collection.data_queries.*.link.href` properties in metadata - no direct endpoint URL/auth passed

### 8. Export Strategy

**Study:** PR #114 modifications to src/index.ts

**Questions:**

- [x] What is exported from index.ts related to the factory method?

  - **Answer:** Main exports: `export { default as OgcApiEndpoint }` (has factory method), `export * from './ogc-api/model.js'` (types)

- [x] Is the QueryBuilder class exported?

  - **Answer:** **YES** (implicitly via pattern) - developers can access via `const builder = await endpoint.edr(...)` and inspect type

- [x] Are there re-exports from the ogc-api/edr module?

  - **Answer:** **YES** - model types exported via `export * from './ogc-api/model.js'` which includes EDR type extensions

- [x] What types are exported vs kept internal?
  - **Answer:** Public: `OgcApiEndpoint`, `OgcApiCollectionInfo`, query parameter types. Internal: Cache implementation, helper functions

### 9. CSAPI-Specific Considerations

**Study:** Differences between EDR and CSAPI that affect integration

**Questions:**

- [x] EDR: Does `endpoint.edr()` require a collectionId?

  - **Answer:** **YES** - `endpoint.edr(collection_id: string)` has required parameter

- [x] CSAPI: Should `endpoint.csapi(collectionId)` require collectionId?

  - **Answer:** **YES** - follow EDR pattern exactly, CSAPI resources are collection-scoped just like EDR queries

- [x] CSAPI: Can one collection have multiple CSAPI resource types?

  - **Answer:** **YES** - one collection can support Systems, DataStreams, Observations, etc. simultaneously - QueryBuilder exposes all supported types

- [ ] CSAPI: Should QueryBuilder know which resource types are available?

  - **Answer:** _[To be filled after research]_

- [ ] CSAPI: Are there collection-level vs endpoint-level CSAPI operations?
  - **Answer:** _[To be filled after research]_

### 10. Code Organization

**Study:** File structure and import patterns in PR #114

**Questions:**

- [ ] Where is the QueryBuilder class file located?

  - **Answer:** _[To be filled after research]_

- [ ] What is the import path from endpoint.ts to QueryBuilder?

  - **Answer:** _[To be filled after research]_

- [ ] Are there any circular dependency concerns?

  - **Answer:** _[To be filled after research]_

- [ ] How are relative imports structured?
  - **Answer:** _[To be filled after research]_

---

## Research Tasks

### Task 1: Study PR #114 EDR Factory Method

- [ ] Read endpoint.ts changes in PR #114
- [ ] Document exact implementation of `endpoint.edr()`
- [ ] Extract method signature, parameters, return type
- [ ] Identify all dependencies and imports
- [ ] Note any comments or documentation in the code

### Task 2: Analyze QueryBuilder Instantiation

- [ ] Trace the `new EDRQueryBuilder()` call
- [ ] Document what parameters are passed to constructor
- [ ] Understand how endpoint context is provided
- [ ] Identify any configuration or options objects

### Task 3: Study Collection Integration

- [ ] Determine if/how collections are involved
- [ ] Check if collection metadata is accessed
- [ ] Understand relationship between endpoint and collections
- [ ] Review how collection-specific features are exposed

### Task 4: Review Type System

- [ ] Document all TypeScript types involved
- [ ] Understand interface contracts
- [ ] Review type exports in index.ts
- [ ] Check for any type guards or validators

### Task 5: Examine Error Handling

- [ ] Find all error throwing locations
- [ ] Document error messages and types
- [ ] Understand error propagation
- [ ] Review any try-catch blocks

### Task 6: Compare with Other API Implementations

- [ ] Check if Features, Tiles, STAC have similar patterns
- [ ] Identify common patterns across API families
- [ ] Note any deviations or special cases
- [ ] Understand why EDR pattern should be followed

---

## Upstream Code to Study

### Primary Sources

- **PR #114:** https://github.com/camptocamp/ogc-client/pull/114
  - File: `src/shared/endpoint.ts` (factory method implementation)
  - File: `src/ogc-api/edr/url_builder.ts` (QueryBuilder class)
  - File: `src/index.ts` (exports)

### Secondary Sources

- **Current endpoint.ts:** https://github.com/camptocamp/ogc-client/blob/main/src/shared/endpoint.ts
  - Study existing factory methods for Features, Tiles, STAC
  - Understand the OgcApiEndpoint class structure

### Reference Analysis

- **[pr114-analysis.md](../../upstream/pr114-analysis.md)** - Sections 2, 3.2, 5
- **[integration-analysis.md](../../upstream/integration-analysis.md)** - Integration points
- **[querybuilder-pattern-analysis.md](../../upstream/querybuilder-pattern-analysis.md)** - Factory method pattern

---

## Deliverables

### 1. Research Plan (This Document)

- [x] Define all research questions
- [x] Fill in answers as research progresses
- [x] Mark completed tasks
- [x] Document key findings inline

### 2. Analysis Report

**File:** `ogcapiendpoint-integration-analysis.md` (to be created in this folder)

**Important:** The analysis report MUST include the [Development Standards](../../../planning/csapi-implementation-guide.md#development-standards) section from the implementation guide. All design decisions should follow these standards for code quality, documentation, and testing.

**Required Sections:**

1. **Executive Summary**

   - Key findings in 3-5 bullets
   - Recommended approach for CSAPI integration

2. **Factory Method Design**

   - Exact method signature for `endpoint.csapi(collectionId)`
   - Parameters and return type
   - Implementation pseudocode

3. **Integration Code Changes**

   - endpoint.ts: Exact lines to add, where to add them
   - info.ts: Changes needed (if any)
   - index.ts: Export statements to add

4. **Caching Strategy**

   - Whether to cache QueryBuilder instances
   - Implementation approach if caching

5. **Collection Validation**

   - How to validate collection supports CSAPI
   - Error handling for invalid collections

6. **Type Definitions**

   - All TypeScript types needed
   - Interface contracts

7. **Code Examples**

   - Before/after code snippets
   - Developer usage examples
   - Error handling examples

8. **Dependencies**

   - What the factory method depends on
   - What the QueryBuilder receives from endpoint

9. **Testing Approach**

   - How the factory method will be tested
   - Mock strategies
   - Edge cases to test

10. **Implementation Checklist**
    - Step-by-step implementation guide
    - Files to create/modify
    - Order of operations

### 3. Code Artifacts

**Optional but recommended:**

- Draft method signature with JSDoc comments
- Draft TypeScript interfaces
- Example test cases

---

## Success Criteria

This research is complete when:

- [x] All critical questions have answers
- [x] Analysis report is written and reviewed
- [x] Code changes are clearly specified (file, location, exact code)
- [x] CSAPI-specific considerations are addressed
- [x] Integration approach matches EDR pattern exactly
- [x] Developer usage pattern is clear and documented
- [x] Error scenarios are identified and handled
- [x] Testing strategy is defined

---

## Next Steps

1. **DO NOT START IMPLEMENTATION** - This is research only
2. Review this plan for completeness
3. Begin research with Task 1 (Study PR #114)
4. Fill in answers as research progresses
5. Create analysis report when research is complete
6. Mark component complete in [design-sequence.md](../design-sequence.md)
7. Move to Component #2 (Conformance Reader)

---

## Notes

- This component is foundational - get it right before moving forward
- The factory method is the developer's entry point to all CSAPI functionality
- Match EDR pattern exactly - do not innovate or "improve" on this pattern
- Keep it minimal - ~48 lines total across all files
- Prioritize developer experience - method should be intuitive and discoverable
