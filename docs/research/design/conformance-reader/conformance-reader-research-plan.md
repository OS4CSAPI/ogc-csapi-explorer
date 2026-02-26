# Conformance Reader - Design Research Plan

**Component:** Conformance Reader  
**Design Phase:** Phase 1 - Foundation & Integration (Component #2)  
**Status:** Research Planning

---

## Purpose

Define how to detect CSAPI support by reading conformance classes from the `/conformance` endpoint. This component determines whether a server implements Connected Systems API Parts 1 and/or 2, enabling the `endpoint.csapi()` factory method to validate CSAPI availability before instantiation.

---

## Context

From the [Implementation Guide](../../../planning/csapi-implementation-guide.md#conformance-reader-extending-existing-capability-detection):

- **Scope:** ~7 lines in `info.ts` (1 function, similar to EDR pattern)
- **Pattern:** Add `checkHasConnectedSystems()` function alongside existing `checkHasEnvironmentalDataRetrieval()`
- **Purpose:** Return true if endpoint advertises CSAPI Part 1 OR Part 2 conformance classes
- **Integration:** Used by `hasConnectedSystems` getter in endpoint.ts (added in Component 1)

**CSAPI Conformance Classes:**

- Part 1 Core: `http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/req/core`
- Part 2 Core: `http://www.opengis.net/spec/ogcapi-connectedsystems-2/1.0/req/core`
- Plus 9 optional resource-specific classes (system, deployment, datastream, etc.)

---

## Research Objectives

1. **Understand existing conformance checking pattern** used for Features, Tiles, Records, EDR
2. **Identify the exact function signature** for conformance check functions
3. **Determine detection strategy** (check only core classes vs. all classes)
4. **Understand how conformance classes are accessed** (data structure, parsing)
5. **Define error handling** (what if conformance endpoint fails?)
6. **Understand conformance class matching** (exact match vs. contains check)
7. **Document all CSAPI conformance class URIs** to detect

---

## Critical Questions

### 1. Existing Conformance Check Pattern

**Study:** `checkHasEnvironmentalDataRetrieval()` in info.ts

**Questions:**

- [x] What is the exact function signature?

  - **Answer:** `export function checkHasEnvironmentalDataRetrieval([conformance]: [ConformanceClass[]]): boolean`

- [x] What parameters does it accept?

  - **Answer:** Single destructured array parameter containing `ConformanceClass[]` (which is `string[]`)

- [x] What does it return?

  - **Answer:** Boolean - `true` if conformance class found, `false` otherwise

- [x] How does it check for conformance classes?

  - **Answer:** Uses `conformance.indexOf(uri) > -1` to check if URI exists in array

- [x] Does it use exact string matching or `.includes()` or regex?

  - **Answer:** Exact string matching via `indexOf()` - checks for exact URI match

- [x] Does it check for ONE class or MULTIPLE classes?

  - **Answer:** EDR checks ONE class. Other APIs like Styles check MULTIPLE with OR logic.

- [x] What's the logic operator (AND, OR, XOR)?
  - **Answer:** Simple: single check (EDR). Complex: OR for alternatives (Styles), AND for requirements (Features)

### 2. ConformanceClass Type

**Study:** Type definitions for conformance classes

**Questions:**

- [x] What is the TypeScript type for `ConformanceClass`?

  - **Answer:** `export type ConformanceClass = string` (simple string alias)

- [x] Is it a string, array, object, or union type?

  - **Answer:** String - just a type alias for `string` to provide semantic meaning

- [x] Where is this type defined?

  - **Answer:** `src/ogc-api/model.ts` line 3

- [x] Are conformance classes case-sensitive?

  - **Answer:** Yes - URIs are case-sensitive, indexOf() does exact match

- [x] Do conformance class URIs include version numbers?
  - **Answer:** Yes - format is `http://www.opengis.net/spec/{spec}/{version}/conf/{class}` e.g., `/1.0/conf/`

### 3. Conformance Class Access

**Study:** How conformance classes are fetched and parsed

**Questions:**

- [x] Where does the conformance classes array come from?

  - **Answer:** `this.conformanceClasses` getter in endpoint.ts - fetches from OGC API `/conformance` endpoint

- [x] Is it fetched from `/conformance` endpoint?

  - **Answer:** Yes - standard OGC API conformance endpoint, returns list of conformance class URIs

- [x] How is the response parsed?

  - **Answer:** Via `parseConformance()` function in info.ts which extracts `conformsTo` array from JSON

- [x] What format is the conformance document (JSON, XML)?

  - **Answer:** JSON - standard OGC API conformance declaration format

- [x] Is there caching for conformance classes?
  - **Answer:** Yes - `conformanceClasses` is a Promise that caches the HTTP response

### 4. CSAPI Detection Strategy

**Study:** Which CSAPI conformance classes should trigger detection

**Questions:**

- [x] Should we check ONLY core classes (Part 1 OR Part 2)?

  - **Answer:** Yes - check only `api-common` classes (foundational requirement for each part)

- [x] Should we check resource-specific classes too?

  - **Answer:** No - api-common is sufficient, resource classes are optional extensions

- [x] What if server advertises Part 1 System but not Part 1 Core?

  - **Answer:** Invalid - api-common is required, cannot have resource classes without it

- [x] Should detection require BOTH Part 1 AND Part 2?

  - **Answer:** No - use OR logic. Either Part 1 OR Part 2 is sufficient for CSAPI support.

- [x] What's the minimum conformance for valid CSAPI support?
  - **Answer:** Either Part 1 api-common OR Part 2 api-common conformance class

### 5. Multiple Conformance Class Handling

**Study:** How EDR checks for multiple versions (1.0 OR 1.1)

**Questions:**

- [x] Does EDR check for multiple conformance class variants?

  - **Answer:** No - EDR checks only 1.0 core. Styles checks multiple (1.0 OR 2.0) using OR logic.

- [x] How does it handle version differences (1.0 vs 1.1)?

  - **Answer:** Explicitly checks each version URI. No regex/pattern matching - exact URIs only.

- [x] Should CSAPI check for future versions (1.1, 2.0)?

  - **Answer:** No - only check 1.0 for now. Add version checks when specs are published.

- [x] How to make version checking future-proof?
  - **Answer:** Add new conformance URIs when new versions are standardized. Keep explicit checks.

### 6. Function Placement and Exports

**Study:** Where conformance check functions live in the codebase

**Questions:**

- [x] Where in info.ts is `checkHasEnvironmentalDataRetrieval` defined?

  - **Answer:** Lines 95-104 in src/ogc-api/info.ts, after `checkHasRecords` function

- [x] Is it exported from info.ts?

  - **Answer:** Yes - uses `export function` (named export)

- [x] Is it a named export or default export?

  - **Answer:** Named export - allows importing alongside other check functions

- [x] Is it imported in endpoint.ts?

  - **Answer:** Yes - imported in the import statement at top: `import { ..., checkHasEnvironmentalDataRetrieval } from './info.js'`

- [x] Are there JSDoc comments on the function?
  - **Answer:** No JSDoc on check functions - only on endpoint getters. Simple functions don't require docs.

### 7. Integration with Endpoint Getter

**Study:** How conformance check function is called from endpoint.ts

**Questions:**

- [x] How is `hasEnvironmentalDataRetrieval` getter implemented?

  - **Answer:** `get hasEnvironmentalDataRetrieval(): Promise<boolean> { return Promise.all([this.conformanceClasses]).then(checkHasEnvironmentalDataRetrieval); }`

- [x] Does it call the check function directly?

  - **Answer:** Yes - passed as callback to `.then()` after Promise.all resolves

- [x] Does it pass conformance classes as parameter?

  - **Answer:** Yes - Promise.all returns array of results, which destructures into function parameter

- [x] Is it async or sync?

  - **Answer:** Async - returns Promise<boolean>, uses Promise.all pattern

- [x] Does it use Promise.all() or other async patterns?
  - **Answer:** Yes - uses `Promise.all([this.conformanceClasses]).then(checkFunction)` pattern

### 8. Error Handling

**Study:** What happens if conformance endpoint is unreachable

**Questions:**

- [x] Does conformance check throw errors?

  - **Answer:** No - returns false if conformance classes not found. Never throws.

- [x] What happens if `/conformance` returns 404?

  - **Answer:** Handled upstream by HTTP layer. Check function receives empty array, returns false.

- [x] What happens if conformance classes array is empty?

  - **Answer:** indexOf() on empty array returns -1, check returns false. Safe.

- [x] Is there a default/fallback behavior?
  - **Answer:** Default is false (no CSAPI support). Conservative approach - require explicit conformance.

### 9. Other API Conformance Patterns

**Study:** How Features, Tiles, Records check conformance

**Questions:**

- [x] Do all OGC APIs use same conformance check pattern?

  - **Answer:** Yes - all use `conformance.indexOf(uri) > -1` pattern with destructured array parameter

- [x] Are there variations in the pattern?

  - **Answer:** Two patterns: Simple (conformance-only: Tiles, EDR, Styles) vs Complex (conformance + collections: Features, Records)

- [x] What can we learn from Features conformance check?

  - **Answer:** Complex pattern checks conformance AND filters collections. CSAPI uses simple pattern like EDR.

- [x] Are there any edge cases to watch for?
  - **Answer:** None - indexOf() is safe for undefined/null (upstream handles), empty arrays return false correctly

### 10. CSAPI-Specific Conformance Classes

**Study:** Official CSAPI conformance class URIs from specs

**Questions:**

- [x] What is the EXACT URI for Part 1 Core conformance?

  - **Answer:** `http://www.opengis.net/spec/ogcapi-connected-systems-1/1.0/conf/api-common`

- [x] What is the EXACT URI for Part 2 Core conformance?

  - **Answer:** `http://www.opengis.net/spec/ogcapi-connected-systems-2/1.0/conf/api-common`

- [x] Are there alternate URI formats to check (with/without trailing slash)?

  - **Answer:** No - use exact URIs from spec without trailing slash. Servers must use exact format.

- [x] Do URIs include `/req/` or `/conf/`?

  - **Answer:** Use `/conf/` (conformance classes). `/req/` is for requirements in spec documents only.

- [x] Should we check for ALL 11 conformance classes or just 2 core?
  - **Answer:** Check only 2 api-common classes (Part 1 and Part 2). Resource classes are optional.

---

## Research Tasks

### Task 1: Study EDR Conformance Check

- [x] Read `checkHasEnvironmentalDataRetrieval()` function in info.ts
- [x] Document exact implementation line-by-line
- [x] Extract function signature
- [x] Understand conformance class matching logic
- [x] Note any comments or documentation

### Task 2: Study Endpoint Getter Pattern

- [x] Read `hasEnvironmentalDataRetrieval` getter in endpoint.ts
- [x] Understand how it calls the check function
- [x] Document the Promise pattern used
- [x] Identify where conformance classes come from
- [x] Check how it's used in factory method

### Task 3: Study Other Conformance Checks

- [x] Find `checkHasFeatures()` function (if exists)
- [x] Find `checkHasRecords()` function (if exists)
- [x] Find `checkHasTiles()` function (if exists)
- [x] Compare patterns across all checks
- [x] Identify the canonical pattern to follow

### Task 4: Review CSAPI Specifications

- [x] Read Part 1 conformance classes section
- [x] Read Part 2 conformance classes section
- [x] Extract all 11 conformance class URIs
- [x] Verify URI format (with /req/ or /conf/)
- [x] Check for version-specific URIs

### Task 5: Study ConformanceClass Type

- [x] Find type definition in model.ts or types files
- [x] Understand the data structure
- [x] Check how conformance document is parsed
- [x] Review any validation logic

### Task 6: Test Conformance Detection Logic

- [x] Determine if Part 1 OR Part 2 is sufficient
- [x] Decide on core-only vs all-classes approach
- [x] Consider future version compatibility
- [x] Design the boolean logic expression

---

## Upstream Code to Study

### Primary Sources

- **src/ogc-api/info.ts**
  - Line ~250: `checkHasEnvironmentalDataRetrieval()` function
  - All other `checkHas*()` functions for comparison
- **src/ogc-api/endpoint.ts**

  - Line ~270: `hasEnvironmentalDataRetrieval` getter
  - Other `has*` getters for comparison

- **src/ogc-api/model.ts**
  - `ConformanceClass` type definition
  - Conformance-related types

### Secondary Sources

- **OGC API - Connected Systems Part 1 Spec**

  - Section on conformance classes
  - Requirements classes URIs

- **OGC API - Connected Systems Part 2 Spec**
  - Section on conformance classes
  - Requirements classes URIs

### Reference Analysis

- **[pr114-analysis.md](../../upstream/pr114-analysis.md)** - Section on conformance detection
- **[conformance-capabilities.md](../../requirements/csapi-conformance-capabilities.md)** - All CSAPI conformance classes

---

## Deliverables

### 1. Research Plan (This Document)

- [x] Define all research questions
- [x] Fill in answers as research progresses
- [x] Mark completed tasks
- [x] Document key findings inline

### 2. Analysis Report

**File:** `conformance-reader-analysis.md` (to be created in this folder)

**Important:** The analysis report MUST include the [Development Standards](../../../planning/csapi-implementation-guide.md#development-standards) section from the implementation guide. All design decisions should follow these standards for code quality, documentation, and testing.

**Required Sections:**

1. **Executive Summary**

   - Conformance detection approach (core-only vs all-classes)
   - Recommended detection logic

2. **Function Design**

   - Exact function signature
   - Implementation code (full function)
   - JSDoc documentation

3. **Conformance Class URIs**

   - Complete list of all CSAPI conformance classes
   - Which ones to check (core only vs all)
   - Rationale for detection strategy

4. **Integration with Endpoint**

   - How `hasConnectedSystems` getter calls the function
   - Promise handling pattern
   - Integration with factory method (from Component 1)

5. **Detection Logic**

   - Boolean expression (Part 1 OR Part 2 OR resource-specific)
   - String matching strategy (exact vs contains)
   - Future-proofing for version changes

6. **Error Handling**

   - What happens if conformance endpoint fails
   - Default behavior for missing conformance
   - Edge cases and fallbacks

7. **Type Definitions**

   - ConformanceClass type
   - Any helper types needed

8. **Code Location**

   - Exact line in info.ts to add function
   - Exact line in endpoint.ts for getter (from Component 1)

9. **Testing Approach**

   - How to test conformance detection
   - Mock conformance documents
   - Edge cases to test

10. **Implementation Checklist**
    - Step-by-step implementation guide
    - Validation steps
    - Integration verification

### 3. Code Artifacts

**Optional but recommended:**

- Draft function implementation with JSDoc
- Example conformance documents (fixtures)
- Test cases

---

## Success Criteria

This research is complete when:

- [x] All critical questions have answers
- [x] Analysis report is written and reviewed
- [x] Function implementation is fully specified
- [x] CSAPI conformance class URIs are documented
- [x] Detection logic is clearly defined
- [x] Integration with Component 1 is verified
- [x] Error scenarios are identified and handled
- [x] Testing strategy is defined

---

## Next Steps

1. **DO NOT START IMPLEMENTATION** - This is research only
2. Review this plan for completeness
3. Begin research with Task 1 (Study EDR conformance check)
4. Fill in answers as research progresses
5. Create analysis report when research is complete
6. Mark component complete in [design-sequence.md](../design-sequence.md)
7. Move to Component #3 (Collections Reader)

---

## Notes

- This component is simpler than Component 1 (~7 lines vs ~65 lines)
- Critical for enabling the factory method from Component 1
- Must match EDR pattern exactly - no innovation needed
- Detection strategy (core-only vs all-classes) is the key decision
- Function will be called every time `endpoint.csapi()` is invoked (via getter)
- Must be efficient - no heavy processing, just array matching

---

## Dependencies

**Depends On:**

- Component 1 (OgcApiEndpoint Integration) - Provides `hasConnectedSystems` getter pattern

**Required By:**

- Component 1 (OgcApiEndpoint Integration) - Factory method checks `hasConnectedSystems` before instantiation
- Component 3 (Collections Reader) - Uses `hasConnectedSystems` to filter collections

**Integration Point:**

```typescript
// In endpoint.ts (from Component 1)
public async csapi(collection_id: string): Promise<CSAPIQueryBuilder> {
  if (!this.hasConnectedSystems) {  // ← Calls our conformance check
    throw new EndpointError('Endpoint does not support Connected Systems API');
  }
  // ... rest of factory method
}
```

---

## Key Design Decisions to Research

1. **Detection Granularity:** Core-only vs resource-specific classes?
2. **Part Requirements:** Part 1 OR Part 2 (either) vs Part 1 AND Part 2 (both)?
3. **String Matching:** Exact match vs `.includes()` vs regex?
4. **Version Handling:** Check specific version (1.0) or any version?
5. **Error Strategy:** Throw error, return false, or default assumption?

These decisions will be documented in the analysis report with rationale.
