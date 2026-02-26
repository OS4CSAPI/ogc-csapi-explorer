# Collections Reader - Design Research Plan

**Component:** Collections Reader  
**Design Phase:** Phase 1 - Foundation & Integration (Component #3)  
**Status:** Research Planning

---

## Purpose

Define how to identify which collections contain CSAPI resources by parsing collection metadata from the `/collections` endpoint. This component determines which collections support Systems, DataStreams, Observations, or other CSAPI resource types, enabling developers to discover available CSAPI collections before constructing queries.

---

## Context

From the [Implementation Guide](../../../planning/csapi-implementation-guide.md#collections-reader-extending-metadata-parsing):

- **Scope:** ~15 lines total (filter function in info.ts + getter in endpoint.ts)
- **Pattern:** Add `parseCollections()` filtering logic and `csapiCollections` getter (similar to EDR pattern)
- **Purpose:** Filter collections metadata to identify those with CSAPI resource types (Systems, DataStreams, etc.)
- **Integration:** Used by developers to discover available CSAPI collections; called internally by `endpoint.csapi()` factory method

**CSAPI Collection Indicators:**

- `featureType` property with SOSA/SSN values (`sosa:System`, `sosa:Deployment`, `sosa:ObservationCollection`, etc.)
- Links to CSAPI-specific operations (systems, datastreams, observations endpoints)
- Schema information for DataStreams/ControlStreams
- Supported formats (GeoJSON, SensorML 3.0, SWE Common 3.0)

**Key Metadata Properties:**

```json
{
  "id": "sensors-collection",
  "title": "IoT Sensors",
  "featureType": "sosa:System",
  "links": [
    { "rel": "systems", "href": ".../collections/sensors-collection/systems" },
    {
      "rel": "datastreams",
      "href": ".../collections/sensors-collection/datastreams"
    }
  ]
}
```

---

## Research Objectives

1. **Understand existing collection parsing pattern** used for Features, Tiles, Records, EDR
2. **Identify collection metadata structure** (what fields exist, what indicates CSAPI support)
3. **Determine filtering strategy** (check featureType, check links, check both?)
4. **Understand parseCollections pattern** (how EDR filters collections by metadata)
5. **Define csapiCollections getter** (returns array of collection IDs with CSAPI support)
6. **Understand collection data access** (where collections data comes from, caching)
7. **Define error handling** (what if /collections fails, empty collections array)

---

## Critical Questions

### 1. Existing Collection Parsing Pattern

**Study:** How EDR, Features, Tiles, Records parse and filter collections

**Questions:**

- [x] What is the exact structure of collection metadata objects?

  - **Answer:** `OgcApiCollectionInfo` interface with properties: id, title, description, itemType, featureType, links, extent, crs, queryables, sortables, etc.

- [x] Where is collection metadata fetched from (`/collections` endpoint)?

  - **Answer:** Yes - fetched from standard OGC API `/collections` endpoint, returned as array in `collections` property

- [x] How is the collection data parsed (JSON structure)?

  - **Answer:** Via `parseCollections()` function in info.ts which maps over `doc.collections` array and extracts metadata flags

- [x] What TypeScript types represent collections?

  - **Answer:** `OgcApiCollectionInfo` (model.ts line 85) for individual collections, `OgcApiDocument` contains `collections?: OgcApiCollectionInfo[]`

- [x] Is collection data cached?
  - **Answer:** Yes - `this.data` property in endpoint.ts caches the Promise resolving to collections document

### 2. EDR Collection Filtering Pattern

**Study:** `parseCollections()` function and EDR filtering logic in info.ts

**Questions:**

- [x] Does a `parseCollections()` function exist in info.ts?

  - **Answer:** Yes - line 229 in info.ts, used by all collection getters (Features, Tiles, Records, EDR)

- [x] What is the exact function signature for collection parsing?

  - **Answer:** `export function parseCollections(doc: OgcApiDocument): Array<{name: string; hasRecords?: boolean; hasFeatures?: boolean; ...}>`

- [x] How does EDR identify collections with EDR support?

  - **Answer:** Checks for `collection.data_queries` property existence, sets `hasDataQueries: true` if present

- [x] What metadata properties does EDR check (data_queries, crs, extent)?

  - **Answer:** Checks `data_queries` property - existence indicates EDR support for that collection

- [x] Does it use `.filter()`, `.map()`, or other array methods?

  - **Answer:** Uses `.map()` to transform collections array into metadata objects with flags

- [x] What does the function return (collection IDs, collection objects, both)?
  - **Answer:** Returns array of objects with `name` (collection ID) and boolean flags (hasRecords, hasFeatures, hasDataQueries, etc.)

### 3. Collection Metadata Structure

**Study:** TypeScript types for collection objects in model.ts

**Questions:**

- [x] What is the TypeScript type for a collection object?

  - **Answer:** `OgcApiCollectionInfo` interface defined in model.ts line 85

- [x] What properties are available on collection objects?

  - **Answer:** id, title, description, links, itemType, itemFormats, crs, extent, queryables, sortables, data_queries, mapTileFormats, vectorTileFormats, and more

- [x] Is there a `featureType` property on collections?

  - **Answer:** Not in TypeScript type definition, but collections API can return it - CSAPI uses it for Part 1 Feature resources

- [x] Is there a `links` array property on collections?

  - **Answer:** Yes - `links: any` property exists on OgcApiCollectionInfo

- [x] What other CSAPI-relevant metadata might exist?

  - **Answer:** `itemType` (for Part 2 resources), `featureType` (for Part 1 Feature resources), `extent` (spatial/temporal)

- [x] Are there any optional vs required properties?
  - **Answer:** Most properties optional - only id, title, description, links required. itemType and featureType are optional.

### 4. CSAPI Detection Strategy

**Study:** How to identify collections with CSAPI resources

**Questions:**

- [x] Should we check `featureType` property for SOSA/SSN values?

  - **Answer:** Yes - Part 1 Feature resources use featureType (sosa:System, sosa:Deployment, sosa:Procedure, sosa:Sample)

- [x] Should we check `links` array for CSAPI-specific relations (systems, datastreams)?

  - **Answer:** No - checking itemType/featureType is sufficient and more reliable than link relations

- [x] What are valid `featureType` values for CSAPI collections?

  - **Answer:** `http://www.w3.org/ns/sosa/System`, `sosa:System`, `sosa:Deployment`, `sosa:Procedure`, `sosa:Sample`

- [x] Should detection require BOTH featureType AND links?

  - **Answer:** No - check featureType OR itemType. Links not required for detection.

- [x] What if collection has Systems but not DataStreams - still CSAPI?

  - **Answer:** Yes - any CSAPI resource type qualifies. Part 1 only, Part 2 only, or both are all valid.

- [x] Should we detect specific resource types (systems, datastreams separately)?
  - **Answer:** No - use single `hasConnectedSystems` flag for any CSAPI resource type. Simpler and matches existing patterns.

### 5. Collection Data Access

**Study:** Where collection metadata comes from in endpoint.ts

**Questions:**

- [x] What is `this.data` in endpoint.ts?

  - **Answer:** Private property that returns Promise<OgcApiDocument> containing collections metadata from `/collections` endpoint

- [x] Does `this.data` return a Promise?

  - **Answer:** Yes - returns `Promise<OgcApiDocument>` which resolves to collections document

- [x] What structure does `this.data` return (object with collections array)?

  - **Answer:** Returns `OgcApiDocument` with `collections?: OgcApiCollectionInfo[]` array property

- [x] How is collection data fetched (HTTP GET to /collections)?

  - **Answer:** Handled by OgcApiEndpoint infrastructure - HTTP GET request to `/collections` endpoint, cached in Promise

- [x] Is there error handling for failed collection fetches?
  - **Answer:** Yes - handled upstream by OgcApiEndpoint class. Getter receives rejected Promise if fetch fails.

### 6. Getter Implementation Pattern

**Study:** How `edrCollections`, `featureCollections` getters work in endpoint.ts

**Questions:**

- [x] What is the exact implementation of `edrCollections` getter?

  - **Answer:** `Promise.all([this.data, this.hasEnvironmentalDataRetrieval]).then(([data, hasEDR]) => hasEDR ? data : {collections: []}).then(parseCollections).then(filter).then(map)`

- [x] Does it use `Promise.all()` pattern?

  - **Answer:** Yes - combines `this.data` Promise with conformance check Promise using `Promise.all()`

- [x] Does it combine collection data with conformance check?

  - **Answer:** Yes - returns empty collections if conformance check fails: `hasEDR ? data : {collections: []}`

- [x] What does the getter return (Promise<string[]> of collection IDs)?

  - **Answer:** `Promise<string[]>` - array of collection ID strings (names)

- [x] How does it handle empty collections?

  - **Answer:** Returns empty array `[]` - parseCollections handles empty input gracefully

- [x] Does it call a parsing/filter function from info.ts?
  - **Answer:** Yes - calls `parseCollections()` from info.ts, then filters and maps results

### 7. Filter Function Design

**Study:** How to structure the collection filtering function

**Questions:**

- [x] Should the filter function be in info.ts or endpoint.ts?

  - **Answer:** Extend existing `parseCollections()` in info.ts - follows established pattern, no new function needed

- [x] Should it accept collections array as parameter?

  - **Answer:** No new function - extend `parseCollections()` which accepts `OgcApiDocument` parameter

- [x] Should it return collection objects or just IDs?

  - **Answer:** Returns objects with name + flags. Getter then filters and maps to extract just IDs.

- [x] Should it be named `parseCSAPICollections()` or similar?

  - **Answer:** No - extend existing `parseCollections()` function with additional logic

- [x] Is it exported for testing?
  - **Answer:** Yes - `parseCollections()` is already exported, can test CSAPI additions directly

### 8. Integration with Conformance Check

**Study:** How csapiCollections relates to hasConnectedSystems

**Questions:**

- [x] Should `csapiCollections` check `hasConnectedSystems` first?

  - **Answer:** Yes - use `Promise.all([this.data, this.hasConnectedSystems])` pattern, return empty if no conformance

- [x] What if `hasConnectedSystems` is false but collection has featureType?

  - **Answer:** Return empty array - conservative approach requires explicit conformance declaration

- [x] Should we return empty array if no CSAPI conformance?

  - **Answer:** Yes - `hasCSAPI ? data : {collections: []}` returns empty document to avoid processing

- [x] How does EDR pattern handle conformance + collections together?
  - **Answer:** Exactly same pattern - Promise.all combines conformance + data, returns empty collections if no conformance

### 9. Error Handling

**Study:** What happens if collection endpoint is unreachable

**Questions:**

- [x] Does the getter throw errors or return empty array?

  - **Answer:** Returns empty array for normal cases (no conformance, no collections). HTTP errors propagate as Promise rejection.

- [x] What happens if `/collections` returns 404?

  - **Answer:** Handled upstream - `this.data` Promise rejects, getter propagates rejection to caller

- [x] What happens if collection metadata is malformed?

  - **Answer:** Type guards check property types, skip malformed collections (undefined !== true in filter)

- [x] Is there a default/fallback behavior?
  - **Answer:** Default is empty array [] - conservative approach, require explicit CSAPI indicators

### 10. CSAPI-Specific Metadata

**Study:** Official CSAPI collection metadata from specs

**Questions:**

- [x] What are the EXACT `featureType` values for CSAPI resources?

  - **Answer:** Part 1: `sosa:System`, `sosa:Deployment`, `sosa:Procedure`, `sosa:Sample` (full URIs: `http://www.w3.org/ns/sosa/...`)

- [x] What link relation types indicate CSAPI endpoints (rel="systems")?

  - **Answer:** Not using links for detection - itemType/featureType properties are more reliable indicators

- [x] Are there version-specific indicators (Part 1 vs Part 2)?

  - **Answer:** Part 1 uses featureType (Feature resources) + itemType (Property). Part 2 uses itemType (DataStream, Observation, etc.)

- [x] What other metadata might indicate CSAPI support?

  - **Answer:** itemType values: `sosa:Property` (Part 1), `DataStream`, `Observation`, `ControlStream`, `Command`, `Feasibility`, `SystemEvent` (Part 2)

- [x] Should we check for all 9 resource types or just core types?
  - **Answer:** Check all types - any CSAPI resource type qualifies collection as CSAPI-enabled

---

## Research Tasks

### Task 1: Study EDR Collection Parsing

- [x] Find `parseCollections()` or similar function in info.ts
- [x] Document exact implementation line-by-line
- [x] Extract function signature
- [x] Understand collection filtering logic
- [x] Note any comments or documentation

### Task 2: Study Collection Getter Pattern

- [x] Read `edrCollections` getter in endpoint.ts
- [x] Understand how it calls the parsing function
- [x] Document the Promise pattern used
- [x] Identify where collection data comes from
- [x] Check how it integrates with conformance check

### Task 3: Study Collection Metadata Structure

- [x] Find collection type definitions in model.ts
- [x] Document all properties on collection objects
- [x] Identify CSAPI-relevant properties (featureType, links)
- [x] Check for optional vs required properties
- [x] Review any validation logic

### Task 4: Study Other Collection Getters

- [x] Find `featureCollections` getter (if exists)
- [x] Find `tileCollections` getter (if exists)
- [x] Compare patterns across all getters
- [x] Identify the canonical pattern to follow

### Task 5: Review CSAPI Specifications

- [x] Read Part 1 collection metadata section
- [x] Read Part 2 collection metadata section
- [x] Extract CSAPI-specific featureType values
- [x] Document link relation types for CSAPI resources
- [x] Check for version-specific metadata

### Task 6: Design Filter Strategy

- [x] Determine if checking featureType is sufficient
- [x] Decide if links array check is needed
- [x] Consider combinations (featureType AND/OR links)
- [x] Define the boolean logic expression
- [x] Plan for future extensibility

---

## Upstream Code to Study

### Primary Sources

- **src/ogc-api/info.ts**
  - Collection parsing functions (if they exist)
  - EDR-specific collection filtering logic
- **src/ogc-api/endpoint.ts**

  - Line ~280-300: `edrCollections` getter (if exists)
  - Line ~250-270: `featureCollections` getter (if exists)
  - `this.data` property (collections data source)

- **src/ogc-api/model.ts**
  - Collection type definition
  - Collection-related types and interfaces

### Secondary Sources

- **OGC API - Connected Systems Part 1 Spec**

  - Section on collection metadata
  - featureType property definition
  - Links array for CSAPI resources

- **OGC API - Connected Systems Part 2 Spec**

  - Section on collection metadata
  - DataStream/Observation collection properties

- **SOSA/SSN Ontology Spec**
  - `sosa:System`, `sosa:Deployment`, `sosa:ObservationCollection` definitions

### Reference Analysis

- **[pr114-analysis.md](../../upstream/pr114-analysis.md)** - Section on EDR collection filtering
- **[collection-metadata-analysis.md](../../requirements/csapi-collection-metadata.md)** - CSAPI collection structure

---

## Deliverables

### 1. Research Plan (This Document)

- [x] Define all research questions
- [x] Fill in answers as research progresses
- [x] Mark completed tasks
- [x] Document key findings inline

### 2. Analysis Report

**File:** `collections-reader-analysis.md` (to be created in this folder)

**Important:** The analysis report MUST include a reference to the [Development Standards](../../../planning/csapi-implementation-guide.md#development-standards) section from the implementation guide. All design decisions should follow these standards for code quality, documentation, and testing.

**Required Sections:**

1. **Executive Summary**

   - Collection filtering approach (featureType-based, links-based, or both)
   - Recommended detection strategy

2. **Filter Function Design**

   - Exact function signature
   - Implementation code (full function)
   - Filtering logic and criteria

3. **Collection Metadata Structure**

   - TypeScript type definitions
   - CSAPI-relevant properties (featureType, links)
   - How to identify CSAPI collections

4. **CSAPI Collection Indicators**

   - Complete list of valid `featureType` values
   - Link relation types for CSAPI resources
   - Which properties to check and why

5. **Getter Implementation**

   - How `csapiCollections` getter calls the filter function
   - Promise handling pattern
   - Integration with `hasConnectedSystems` conformance check

6. **Detection Logic**

   - Boolean expression for filtering
   - Why checking featureType vs links vs both
   - Future-proofing for additional resource types

7. **Error Handling**

   - What happens if collections endpoint fails
   - Default behavior for missing collections
   - Edge cases and fallbacks

8. **Integration Points**

   - Exact line in info.ts to add filter function
   - Exact line in endpoint.ts to add getter
   - Integration with factory method from Component 1

9. **Testing Approach**

   - How to test collection filtering
   - Mock collection metadata
   - Edge cases to test

10. **Implementation Checklist**
    - Step-by-step implementation guide
    - Validation steps
    - Integration verification

### 3. Code Artifacts

**Optional but recommended:**

- Draft filter function implementation
- Example collection metadata (fixtures)
- Test cases

---

## Success Criteria

This research is complete when:

- [x] All critical questions have answers
- [x] Analysis report is written and reviewed
- [x] Filter function implementation is fully specified
- [x] CSAPI collection indicators are documented
- [x] Detection logic is clearly defined
- [x] Integration with Component 2 is verified
- [x] Error scenarios are identified and handled
- [x] Testing strategy is defined

---

## Next Steps

1. **DO NOT START IMPLEMENTATION** - This is research only
2. Review this plan for completeness
3. Begin research with Task 1 (Study EDR collection parsing)
4. Fill in answers as research progresses
5. Create analysis report when research is complete
6. Mark component complete in [design-sequence.md](../design-sequence.md)
7. Move to Component #4 (CSAPIQueryBuilder)

---

## Notes

- This component is slightly more complex than Component 2 (~15 lines vs ~7 lines)
- Depends on Component 2 (uses `hasConnectedSystems` getter)
- Critical for enabling the factory method from Component 1
- Filter strategy (featureType vs links vs both) is the key decision
- Function will be called when developers query `csapiCollections` getter
- Must be efficient - no heavy processing, just array filtering

---

## Dependencies

**Depends On:**

- Component 2 (Conformance Reader) - Provides `hasConnectedSystems` getter to check CSAPI support

**Required By:**

- Component 1 (OgcApiEndpoint Integration) - Factory method may use `csapiCollections` to validate collection ID
- Component 4 (CSAPIQueryBuilder) - Developers use `csapiCollections` to discover available collections

**Integration Point:**

```typescript
// In endpoint.ts (from Component 1)
public async csapi(collection_id: string): Promise<CSAPIQueryBuilder> {
  if (!this.hasConnectedSystems) {  // ← Component 2 conformance check
    throw new EndpointError('Endpoint does not support Connected Systems API');
  }
  // Could also validate collection_id is in csapiCollections ← This component
  const collection = await this.getCollectionInfo(collection_id);
  const result = new CSAPIQueryBuilder(collection);
  return result;
}
```

**Developer Usage:**

```typescript
// Discover CSAPI collections
const csapiCollections = await endpoint.csapiCollections;
// ['sensors-collection', 'weather-stations', 'iot-devices']

// Then query specific collection
const csapi = await endpoint.csapi('sensors-collection');
```

---

## Key Design Decisions to Research

1. **Detection Strategy:** Check featureType only vs links only vs both?
2. **featureType Values:** Which SOSA/SSN values indicate CSAPI? All 9 types or just core?
3. **Link Relations:** Which link rel values indicate CSAPI endpoints?
4. **Part 1 vs Part 2:** How to distinguish or do we need to?
5. **Error Strategy:** Return empty array, throw error, or default assumption?
6. **Filtering Efficiency:** Filter once or multiple times? Cache results?

These decisions will be documented in the analysis report with rationale.
