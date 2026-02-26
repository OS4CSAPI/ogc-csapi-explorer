# Design Strategy Research

**Purpose:** Define the correct architectural approach for implementing CSAPI client support in ogc-client.

**Context:** Multiple previous iterations. Need to get design right BEFORE implementation to avoid wasted effort and PR rejection.

**Priority:** This research MUST be completed before writing any implementation code.

---

## Critical Question

**"What architecture will the maintainers accept and merge?"**

Everything else is secondary. This research answers that question definitively.

---

## ✅ CRITICAL TERMINOLOGY QUESTION (RESOLVED)

**Issue:** We've been using the term "navigator" throughout documentation and previous implementations (e.g., `CSAPINavigator`, `endpoint.csapi()` returns a "navigator"). However, this term may not be consistent with upstream terminology.

**RESOLUTION (from PR #114 analysis):**

The object returned by `endpoint.edr()` is called **`EDRQueryBuilder`** (not "navigator").

**Answers:**

- [x] What does PR #114 call the object returned by `endpoint.edr()`? → **`EDRQueryBuilder`**
- [x] Is "navigator" the correct upstream term? → **No, "QueryBuilder" is the pattern**
- [x] What's the actual class name in PR #114? → **`EDRQueryBuilder`**
- [x] What terminology should CSAPI use? → **`CSAPIQueryBuilder`**

**Confirmed Pattern:**

```typescript
// EDR implementation:
endpoint.edr() → returns EDRQueryBuilder

// CSAPI should follow:
endpoint.csapi() → returns CSAPIQueryBuilder
```

**Impact:**

- Previous "navigator" terminology was incorrect
- CSAPI implementation must use "QueryBuilder" pattern
- Minimal documentation updates needed (terminology wasn't widely used in committed docs yet)

**Source:** [docs/research/upstream/pr114-analysis.md](../upstream/pr114-analysis.md) Section 2

---

## ✅ CODE VOLUME CONCERN (RESOLVED)

**Issue:** Previous implementation was ~2x the size of entire upstream repo. This is a red flag for maintainers.

**RESOLUTION (from PR #114 analysis):**

**PR #114 Metrics:**

- **Total:** 2858 additions, 54 deletions
- **Implementation code:** ~750 lines (26%)
- **Test code:** ~2050 lines (72%)
- **Other:** ~58 lines (2%)
- **Files:** 18 total
- **Core modifications:** ~115 lines to existing files

**CSAPI Projection:**

- EDR has 5 query types, CSAPI has 9 resources
- Estimated **~3500 total lines** (~975 implementation, ~2450 tests, ~75 other)
- This is **~25% larger than EDR** (reasonable for 80% more resources)
- **NOT 2x the size of entire repo** - that was over-engineering in previous attempts

**Answers:**

- [x] How large is PR #114? → **2858 total lines, 750 implementation**
- [x] Typical size? → **~750 implementation per API family**
- [x] EDR resources vs CSAPI? → **5 query types vs 9 resources**
- [x] Code-per-resource ratio? → **~150 lines per resource for EDR**
- [x] Can we stay proportional? → **Yes, if we follow EDR patterns closely**

**Design Principle Confirmed:** Match PR #114's architecture exactly. Code volume will naturally align with upstream patterns.

**Source:** [docs/research/upstream/pr114-analysis.md](../upstream/pr114-analysis.md) Section 1

---

## Research Questions

### 1. ✅ PR #114 Architecture Deep Dive (COMPLETED)

**Source:** [PR #114 - EDR Implementation](https://github.com/camptocamp/ogc-client/pull/114)  
**Analysis:** [docs/research/upstream/pr114-analysis.md](../upstream/pr114-analysis.md)

**Answers:**

- [x] **PRIORITY: What is the object returned by endpoint.edr() actually called?** → **`EDRQueryBuilder`** (Analysis Section 2)
- [x] **PRIORITY: How many lines of code / files did PR #114 add?** → **2858 additions, 54 deletions, 18 files** (Section 1)
- [x] What files were added? → **18 files documented in complete structure** (Section 3.1)
- [x] Where were files placed? → **`src/ogc-api/edr/`** (Section 3.1)
- [x] What existing files were modified? → **endpoint.ts, info.ts, index.ts + 3 others, ~115 lines total** (Section 3.2)
- [x] How minimal were modifications to existing files? → **Very minimal: 6 files, ~115 lines to core** (Section 3.2)
- [x] What classes/interfaces were created? → **EDRQueryBuilder, 15+ TypeScript types** (Section 4)
- [x] How is the QueryBuilder pattern implemented? → **Fluent API with method chaining** (Section 5)
- [x] How is format negotiation handled? → **Accept header, format parameter, defaults to GeoJSON** (Section 6.2)
- [x] How are TypeScript types defined? → **Types in types.ts, detailed in Section 4** (Section 4)
- [x] How are query parameters modeled? → **Interfaces per query type + common params** (Section 5.1)
- [x] How is conformance checking done? → **info.ts conformance classes** (Section 6.4)
- [x] How are errors handled? → **HTTP errors, validation errors, network errors** (Section 6.5)
- [x] What's the separation of concerns between files? → **Clear separation documented** (Section 7)
- [x] How is caching implemented? → **Collection metadata cached** (Section 6.3)
- [x] What's exported from the module? → **EDRQueryBuilder + 3 types** (Section 8)

**Status:** Comprehensive 794-line analysis completed and documented.

---

### 2. ✅ Existing ogc-client Architecture Patterns (COMPLETED)

**Files studied:**

- `src/ogc-api/endpoint.ts` - Main endpoint class
- `src/ogc-api/info.ts` - Conformance and capability checking
- `src/index.ts` - Public API exports
- `src/ogc-api/edr/` - EDR implementation reference
- `src/shared/` - Shared utilities and models

**Analysis:** [docs/research/upstream/architecture-patterns-analysis.md](../upstream/architecture-patterns-analysis.md)

**Answers:**

- [x] What's the consistent pattern for adding new API support? → **5-step pattern: conformance check (info.ts) + capability getter (endpoint.ts) + collection filter + factory method + exports** (Analysis Section 2)
- [x] How do implementations extend OgcApiEndpoint? → **They DON'T - QueryBuilder pattern via composition, not inheritance** (Section 3)
- [x] How are collection-specific capabilities determined? → **Two-level: endpoint conformance + collection metadata via getCollectionInfo()** (Section 4)
- [x] How are shared types vs API-specific types organized? → **3-tier: shared/ → ogc-api/ → ogc-api/{api}/model.ts** (Section 5)
- [x] What's the pattern for adding methods to endpoint? → **Async factory methods with Map caching, conformance guards** (Section 6)
- [x] How is conformance class checking done consistently? → **Helper functions in info.ts checking conformance URIs** (Section 7)
- [x] What utilities exist that we should reuse? → **Link utils (getLinkUrl, fetchLink), url-utils (getChildPath), mime-type checking** (Section 8)
- [x] How are links handled? → **Follow links via link-utils, never construct URLs manually** (Section 9)
- [x] How is pagination handled across implementations? → **limit + offset query params via searchParams** (Section 10)
- [x] How are datetime/bbox parameters handled? → **Shared DateTimeParameter type, encoded to ISO 8601 ranges** (Section 11)

**Status:** Comprehensive 902-line architecture analysis completed. CSAPI implementation checklist documented in Section 12.

---

### 3. ✅ QueryBuilder Pattern Analysis (COMPLETED)

**Terminology confirmed: "QueryBuilder" (not "navigator")**

**Critical architectural decision: How does the QueryBuilder pattern work?**

**Analysis:** [docs/research/upstream/querybuilder-pattern-analysis.md](../upstream/querybuilder-pattern-analysis.md)

**Answers:**

- [x] **What is the correct terminology?** → **QueryBuilder (not "navigator" - that was invented term from previous attempt)** (Analysis Section 1)
- [x] What is a "QueryBuilder" in ogc-client context? → **Standalone class that encapsulates collection metadata and provides query methods** (Section 2)
- [x] What's the lifecycle of a QueryBuilder instance? → **4 phases: instantiation (via endpoint) → configuration (constructor) → usage (method calls) → reuse (caching)** (Section 3)
- [x] How is `endpoint.csapi(collectionId)` supposed to work? → **Check conformance → check cache → fetch collection info → instantiate QueryBuilder → cache → return** (Section 3.1)
- [x] What does a QueryBuilder expose? → **Public properties (capabilities, links) + query methods (build URL or execute query)** (Section 4)
- [x] How is per-collection state managed? → **Immutable state stored in QueryBuilder instance, set in constructor from OgcApiCollectionInfo** (Section 5)
- [x] How is caching implemented? → **Map<collection_id, QueryBuilder> in endpoint class, checked before instantiation** (Section 6)
- [x] What's the interface vs implementation separation? → **No formal interface - concrete class with public/private members** (Section 7)
- [x] How do QueryBuilders handle resource availability checking? → **Constructor validation + runtime checks + exposed capability properties** (Section 8)
- [x] How do QueryBuilders construct base URLs? → **From collection.links, never manual construction** (Section 9)
- [x] What's the pattern for URL builder methods? → **Validate capability → get URL from links → add params via searchParams → return string** (Section 10)

**Status:** Comprehensive 1135-line QueryBuilder analysis completed. CSAPI design documented in Section 11.

---

### 4. ✅ URL Building Architecture (COMPLETED)

**Core functionality: How should URL building be structured?**

**Analysis:** [docs/research/upstream/url-building-analysis.md](../upstream/url-building-analysis.md)

**Answers:**

- [x] Should there be a base URL builder class? → **No - native URL API + link relations are sufficient** (Analysis Section 2)
- [x] How are query parameters assembled? → **Via URL.searchParams.set() for each parameter** (Section 3)
- [x] How is URL encoding handled? → **Automatic via URL API - no manual encoding needed** (Section 4)
- [x] How are optional vs required parameters modeled? → **Required as direct params, optional in destructured options object** (Section 5)
- [x] How are array parameters handled? → **Join with comma: array.join(',')** (Section 6)
- [x] How is the base path constructed? → **From collection links via getLinkUrl(), never manual construction** (Section 7)
- [x] How are resource paths structured? → **Hypermedia structure, paths from links** (Section 8)
- [x] Should there be URL builder utilities? → **Reuse existing link-utils, add helpers only for common param handling** (Section 9)
- [x] How to avoid duplication across 9 resource types? → **Accept some duplication (EDR has ~70%), extract helpers for >80% duplication** (Section 10)
- [x] What's the pattern for sub-resource URLs? → **Path concatenation: {parentUrl}/{parentId}/{childResource}** (Section 11)

**Status:** Comprehensive 1323-line URL building analysis completed. CSAPI strategy with helper functions documented in Section 12.

---

### 5. ✅ TypeScript Type System Design (COMPLETED)

**Core functionality: How should types be structured for CSAPI?**

**Analysis:** [docs/research/upstream/typescript-types-analysis.md](../upstream/typescript-types-analysis.md)

**Answers:**

- [x] How should query parameter types be defined? → **Optional parameters interface pattern with all fields optional** (Analysis Section 3)
- [x] Should each resource have its own query interface? → **Base QueryOptions + extended interfaces for resource-specific params** (Section 3, Pattern 4)
- [x] How to model shared parameters (bbox, datetime, limit)? → **Reuse from shared/models.ts - already defined** (Section 5)
- [x] How to model resource-specific parameters? → **Extended interfaces: SystemQueryOptions extends QueryOptions** (Section 5)
- [x] How to ensure type safety for URL builders? → **Discriminated unions, const assertions, strict null checks, type guards** (Section 6)
- [x] How to model CSAPI resources themselves? → **GeoJSON-aligned interfaces with id, type, properties, geometry?, links** (Section 4)
- [x] How granular should types be? → **Fine granularity for core resources, medium for nested objects** (Section 7)
- [x] Where should type definitions live? → **Single src/ogc-api/csapi/model.ts file (~350-400 lines)** (Section 8)
- [x] How to handle format-specific types (GeoJSON vs SensorML)? → **Only type JSON/GeoJSON, leave XML as string/unknown** (Section 9)
- [x] How to model optional properties? → **Use ? operator, never | undefined | null** (Section 10)

**Status:** Comprehensive type system designed with 9 resource interfaces, query options, helper types (~350-400 lines total). Three-tier hierarchy (shared → ogc-api → csapi) documented in Section 11.

---

### 6. ✅ File Organization Strategy (COMPLETED)

**Core functionality: How should CSAPI files be organized?**

**Analysis:** [docs/research/upstream/file-organization-analysis.md](../upstream/file-organization-analysis.md)

**Answers:**

- [x] What files go in `src/ogc-api/csapi/`? → **5 core files: model.ts, url_builder.ts, helpers.ts, + 2 test files** (Analysis Section 10)
- [x] Should there be subdirectories? → **No - flat structure like EDR (5 files doesn't need subdirs)** (Section 10)
- [x] How to organize 9 resource types? → **All in single model.ts file (~350-400 lines)** (Section 10)
- [x] Should each resource be a separate file? → **No - consolidate all resources in model.ts** (Section 2)
- [x] Where do format utilities go? → **helpers.ts for shared utilities** (Section 2)
- [x] Where do validators/parsers go? → **helpers.ts or inline in url_builder.ts** (Section 2)
- [x] How to organize test files? → **Colocated: {filename}.spec.ts next to implementation** (Section 4)
- [x] Where do fixtures go? → **fixtures/ogc-api/csapi/ with collection + item samples** (Section 5, 10)
- [x] What gets exported publicly vs kept internal? → **Export resource types via src/index.ts, QueryBuilder accessed via factory** (Section 9, 10)

**Status:** Complete file organization design. 5 implementation files (model.ts, url_builder.ts, helpers.ts, 2 test files), flat structure, ~3150-3900 total lines. Integration requires ~40 lines in endpoint.ts + info.ts.

---

### 7. ✅ Integration with Existing Code (COMPLETED)

**Core functionality: How to integrate CSAPI into existing codebase?**

**Analysis:** [docs/research/upstream/integration-analysis.md](../upstream/integration-analysis.md)

**Answers:**

- [x] Exactly what changes to `endpoint.ts`? → **5 additions: import, cache field, collections getter, conformance getter, factory method (~35 lines)** (Analysis Section 3)
- [x] Exactly what changes to `info.ts`? → **1 function: checkHasConnectedSystems (~12 lines)** (Section 4)
- [x] Exactly what changes to `index.ts`? → **Export 9 resources + 3 option types + 2 helpers (~17 lines)** (Section 5)
- [x] What shared models can/should be reused? → **BoundingBox, DateTimeParameter, CrsCode, MimeType, Contact, Provider, OgcApiDocumentLink** (Section 6)
- [x] What shared utilities can be reused? → **15+ utilities: getLinkUrl, setQueryParams, getChildPath, EndpointError, etc.** (Section 7)
- [x] How to avoid touching unnecessary files? → **Only modify 3 files (endpoint.ts, info.ts, index.ts), all additive** (Section 8)
- [x] How to minimize diff size? → **Follow existing style, group changes, no refactoring (~65 lines total)** (Section 8)

**Status:** Complete integration strategy. 3 files modified with ~65 lines added (all additive). Follows EDR pattern exactly. Reuses 15+ utilities and 6+ shared types. Clean, reviewable diff.

---

### 8. ✅ Format Negotiation Architecture (COMPLETED)

**Core functionality: How should format selection work?**

**Analysis:** [docs/research/upstream/format-negotiation-analysis.md](../upstream/format-negotiation-analysis.md)

**Answers:**

- [x] Where does format negotiation logic live? → **Inline in url_builder.ts, no separate module** (Analysis Section 1)
- [x] How are Accept headers set? → **Not used - CSAPI uses query parameter instead** (Section 3)
- [x] How is Content-Type detected? → **Not validated - trust server compliance** (Section 6)
- [x] How are format-specific URLs built? → **Single URL, format via 'f' query parameter** (Section 4)
- [x] Should there be a format utility module? → **No - follow EDR inline pattern** (Section 1)
- [x] How to model format enum/constants? → **Optional export for convenience, use string type for flexibility** (Section 7, 8)
- [x] How do parsers/validators fit in? → **None - return URLs only, let users fetch** (Section 9)

**Status:** Simple format handling via 'f' query parameter. Optional format constants (~10 lines). No validation, no Accept headers, no parsers. Total ~13 lines following EDR pattern.

---

### 9. Error Handling Design ✅

**Questions to answer:**

- [x] What errors should the library throw? → **Only conformance check, collection not found, required links missing** (Section 9)
- [x] What errors should be left to user? → **Resource IDs, parameter values, formats - all server-validated** (Section 8)
- [x] How to handle invalid parameters? → **Trust TypeScript types, no runtime validation** (Section 3, 4)
- [x] How to handle non-CSAPI endpoints? → **Conformance check throws EndpointError** (Section 6)
- [x] How to handle missing resources? → **Collections validated, individual resources let server 404** (Section 5)
- [x] What's the error handling pattern upstream? → **EndpointError for API issues, Error for validation, let fetch propagate** (Section 3)
- [x] Should there be custom error classes? → **No - reuse EndpointError, plain Error** (Section 7)

**Status:** Minimal error handling - 1 explicit throw (conformance), 2-3 implicit (from utilities). Trust TypeScript types and server validation. Total ~3 lines. See [error-handling-analysis.md](../upstream/error-handling-analysis.md).

---

### 10. CSAPI-Specific Architectural Decisions

**Questions to answer:**

- [x] How to handle 9 different resource types cleanly? → **Single QueryBuilder with helper methods, ~70-80 methods** (Section 3, 6)
- [x] Should resources share base implementation? → **No inheritance - use private helpers like buildResourceUrl** (Section 6)
- [x] How to model Part 1 vs Part 2 resources? → **Single class, logical sections via comments** (Section 4)
- [x] How to handle sub-resources (systems/{id}/datastreams)? → **Path concatenation pattern, parent ID as parameter** (Section 5)
- [x] How to model observation/command schemas? → **URL building with format parameter, no parsing** (Section 8)
- [x] How to handle SWE Common data components? → **No parsing - return URLs only, user handles** (Section 8)
- [x] How to handle SensorML structures? → **No parsing - return URLs only, user handles** (Section 8)
- [x] Should there be resource-specific navigators? → **No - single QueryBuilder for all resources** (Section 3, 4)
- [x] How to check resource availability per collection? → **Expose availableResources property, no validation in methods** (Section 7)

**Status:** Clean single-class architecture. Total ~560-760 lines (~62-84 lines per resource). 5-6x more efficient than EDR per resource. No parsing, no inheritance, follow EDR pattern exactly. See [csapi-architecture-analysis.md](../upstream/csapi-architecture-analysis.md).

---

### 11. Code Reuse vs Duplication ✅

**Questions to answer:**

- [x] When to reuse upstream utilities vs duplicate? → **Reuse types, errors, OGC API utils; duplicate simple helpers (<15 lines)** (Section 4, 6)
- [x] What shared models exist for bbox, datetime, pagination? → **BoundingBox, DateTimeParameter in shared/models.ts - always import** (Section 2, 5)
- [x] Should we create abstraction base classes? → **No - duplicate CSAPI-specific logic instead** (Section 6)
- [x] When to copy-paste vs import? → **Import if >15 lines & stable; duplicate if CSAPI-specific or simple** (Section 7)
- [x] How much duplication is acceptable to maintain isolation? → **1-15 lines always duplicate, 16-30 consider, 31+ extract or import** (Section 4)

**Principle:** Prefer duplication over coupling (per governance constraints)

**Status:** Minimal coupling strategy - 7 imports (types, errors, OGC API utils), ~75 lines duplicated (query building, datetime, resource discovery). Total dependency ratio: ~1% imports, ~99% implementation. See [code-reuse-analysis.md](../upstream/code-reuse-analysis.md).

---

### 12. Lessons from Previous Iterations ✅

**From [ogc-client-CSAPI](https://github.com/OS4CSAPI/ogc-client-CSAPI):**

- [x] What architectural decisions worked well? → **URL building pattern, resource coverage, isolation in own directory** (Section 3)
- [x] What was over-engineered? → **Format parsing (~2000-4000 lines), validation, domain types, abstractions - saved ~3000-6000 lines** (Section 4)
- [x] What was under-engineered? → **Test quality (trivial tests), documentation, incremental planning** (Section 5)
- [x] What caused maintenance problems? → **Mixed concerns, tight coupling, unclear responsibilities** (Section 6)
- [x] What made testing difficult? → **Unclear scope (what to test), low quality standards, poor organization** (Section 7)
- [x] What would maintainers likely reject? → **Code volume (~2x), wrong patterns, poor tests, unclear justification** (Section 8)
- [x] What feedback did we get (if any)? → **"Too trivial" tests, code volume concerns, terminology errors** (Section 2)

**Action:** Review second iteration's architecture and identify improvements

**Status:** All concerns addressed. Research-first approach (12 analyses complete), right-sized code (~560-760 lines vs ~2x), correct terminology (QueryBuilder not navigator), minimal scope (URL only, no parsing), quality tests (meaningful with spec examples), clear justification (every decision documented), strong isolation (7 minimal imports). Expected outcome: successful PR merge. See [lessons-learned-analysis.md](../upstream/lessons-learned-analysis.md).

---

## Research Deliverables

### Phase 1: Pattern Discovery (Do these first)

1. **PR #114 Architecture Document** - Complete file-by-file breakdown
2. **Upstream Pattern Catalog** - Common patterns across WFS/STAC/EDR
3. **Navigator Pattern Specification** - Exact pattern to follow

### Phase 2: Design Decisions

4. **File Organization Plan** - Exact file structure for CSAPI
5. **Type System Design** - Complete TypeScript interface definitions
6. **Integration Point Specification** - Exact changes to endpoint.ts, info.ts, index.ts

### Phase 3: Implementation Blueprint

7. **Architecture Diagram** - Visual representation of module structure
8. **Class/Interface Reference** - What needs to be created
9. **Implementation Checklist** - Step-by-step build order

---

## Success Criteria

Research is complete when we can answer:

1. ✅ "What exact files do we need to create?"
2. ✅ "What exact changes do we make to existing files?"
3. ✅ "How do we structure the navigator class?"
4. ✅ "How do we organize 9 resource types?"
5. ✅ "What TypeScript interfaces do we need?"
6. ✅ "Does this match upstream patterns exactly?"

---

## Critical Constraints (From Governance)

**Must follow these when designing:**

- ✅ Additive only - minimize modifications to existing files
- ✅ No refactoring of upstream code
- ✅ Follow existing patterns exactly
- ✅ Isolated to `src/ogc-api/csapi/` directory
- ✅ Prefer duplication over shared abstractions
- ✅ Match PR #114 architectural style

---

## Next Steps

1. **START HERE:** Deep dive into PR #114 code structure
2. Document findings as we discover them
3. Create detailed architecture specification
4. Update FEATURE_SPEC.md Section 3 (Technical Design) with findings
5. Get your approval before writing any implementation code

---

## Investigation Priority Order

**Week 1: Foundation (CRITICAL)**

1. **FIRST:** Resolve terminology question - what is the correct term for the object returned by endpoint methods?
2. PR #114 complete file-by-file analysis
3. Existing endpoint.ts patterns
4. [CORRECT_TERM] pattern deep dive

**Week 2: Details** 4. URL building patterns 5. Type system design 6. File organization

**Week 3: Integration** 7. Integration points specification 8. Format negotiation architecture 9. Final architecture document

---

## Notes & Findings

_(Add research findings here as we investigate)_

### PR #114 Analysis

- [ ] TODO: Pull PR and analyze

### Upstream Patterns

- [ ] TODO: Study existing implementations

### Key Architectural Decisions

- [ ] TODO: Document decisions as they're made
