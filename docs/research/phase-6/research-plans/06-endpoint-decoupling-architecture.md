# Research Plan 06: Endpoint Decoupling Architecture (Design Synthesis)

> **Plan 6 of 8** | **Phase 6 — Upstream Acceptance Refactoring**

---

## Metadata

| Field                  | Value                                                     |
| ---------------------- | --------------------------------------------------------- |
| **Status**             | Not Started                                               |
| **Plan Type**          | Design synthesis                                          |
| **Date Created**       | 2026-02-23                                                |
| **Last Updated**       | 2026-02-23                                                |
| **Estimated Time**     | 3–4 hours                                                 |
| **Actual Time**        | —                                                         |
| **Depends On**         | 02, 03, 04, 05                                            |
| **Blocks**             | 08 (File-Level Changelist and Commit Strategy)            |
| **Strategy Reference** | [research-strategy.md § Plan 06](../research-strategy.md) |

---

## 1. Research Objective

Synthesize all prior research (Plans 02–05) into a concrete, implementation-ready architecture for decoupling CSAPI from `endpoint.ts`. Produce a complete design document that specifies: (a) the consumer API shape with exact TypeScript signatures, (b) the coupling level with before/after code for every affected integration point, (c) the data flow from `OgcApiEndpoint` to `CSAPIQueryBuilder` after decoupling, (d) the placement decision for every function and property currently straddling the module boundary (`hasConnectedSystems`, `csapiCollections`, `csapi()`, `extractRootResourceUrls`, `scanCsapiLinks`, `collection_id_to_csapi_builder_`), (e) the barrel file design for `./csapi`, (f) the test migration plan for the 6 CSAPI tests in `endpoint.spec.ts`, and (g) boundary condition verification (✓/✗) for every design choice.

This is the single most consequential plan in the research phase. Every architectural decision for the upstream refactoring is made here. Plans 01–05 gather evidence; Plan 06 makes decisions.

---

## 2. Sequencing Rationale

### Why Plan 6?

This is the critical synthesis plan. It cannot begin until Plans 02–05 are complete because each contributes essential input:

- **Plan 02 (EDR)** provides the proven precedent — EDR is already cleanly decoupled. Its `edr()` method on `endpoint.ts` (line 341) imports `EDRQueryBuilder` directly, but EDR is small (656 lines / 3 files) and was never flagged by jahow. Understanding _why_ EDR's pattern is acceptable at its scale but not at CSAPI's scale (11,767 lines / 27 files) is critical context for the coupling level decision.
- **Plan 03 (Entry Point)** provides the `package.json` `"exports"` configuration and barrel file mechanics. Plan 06 must design the barrel file _contents_ — Plan 03 tells us the barrel file _structure_ works.
- **Plan 04 (Industry API)** provides the consumer API pattern catalog. Plan 06 selects from that catalog based on our specific constraints and codebase realities.
- **Plan 05 (Decoupling Patterns)** provides the coupling level analysis and structural typing implications. Plan 06 selects the coupling level and resolves the `scanCsapiLinks` placement problem using Plan 05's analysis.

### Dependency Chain

- **Builds on:**
  - **Plan 02:** EDR decoupling pattern — the baseline. How does EDR's `endpoint.edr(collectionId)` work? EDR imports `OgcApiCollectionInfo` from `../model.js` and `CrsCode` from `../../shared/models.js`. The endpoint calls `new EDRQueryBuilder(collection)` with a parsed `OgcApiCollectionInfo`. CSAPI's pattern is similar but more complex: the endpoint calls `new CSAPIQueryBuilder(collectionDoc, resourceUrls)` with a raw document (not parsed) plus root-level resource URLs. Plan 02's findings tell us what EDR does right and what CSAPI must do differently.
  - **Plan 03:** Entry point configuration — the `"./csapi"` sub-path export in `package.json`, the barrel file structure (`src/ogc-api/csapi/index.ts`), TypeScript declaration generation for sub-paths. Plan 06 designs the barrel file contents; Plan 03 confirms the packaging mechanics work.
  - **Plan 04:** Industry API patterns — the recommended consumer API shape (constructor injection, factory function, static method, or standalone functions). Plan 06 maps the recommended pattern to our concrete codebase: what does the recommended pattern look like when applied to `CSAPIQueryBuilder` specifically?
  - **Plan 05:** Coupling level analysis — the recommended coupling level (concrete class, interface, data record, or parameters) plus the `import type` strategy, `scanCsapiLinks` placement analysis, and structural typing implications. Plan 06 takes Plan 05's ranked recommendation and applies it to every integration point in `endpoint.ts`.
- **Feeds into:**
  - **Plan 08:** File-Level Changelist and Commit Strategy — needs the complete architectural blueprint to produce the exact file-by-file changelist and commit sequence. Plan 08 cannot begin without Plan 06's decisions.

---

## 3. Boundary Conditions

### Non-Negotiable Constraints

1. **No CSAPI in root exports (Constraint 1):** The ~170 lines of CSAPI exports in `src/index.ts` (lines 45–252) must be removed and relocated to the `./csapi` barrel file. After refactoring, `git grep csapi src/index.ts` must return zero matches.
2. **Separate entry point (Constraint 2):** CSAPI must be importable via `@camptocamp/ogc-client/csapi`. The barrel file at `src/ogc-api/csapi/index.ts` must serve as the entry point. Plan 03's findings confirm the packaging mechanics.
3. **No outward imports (Constraint 3):** The two CSAPI imports in `endpoint.ts` must be eliminated:
   - Line 52: `import CSAPIQueryBuilder from './csapi/url_builder.js'` — **must go**
   - Line 53: `import { scanCsapiLinks } from './csapi/helpers.js'` — **must go**
     After refactoring, `git grep "from.*csapi" src/ogc-api/endpoint.ts` must return zero matches.
4. **One-way dependency (Constraint 4):** After refactoring, removing the entire `src/ogc-api/csapi/` directory must leave core fully functional — zero type errors, zero test failures, zero import resolution errors. This is the litmus test for every design choice.
5. **CI compliance:** Prettier, TypeScript typecheck, ESLint, browser tests, and Node.js tests must all pass.

### Implementation Scope Gate

> **Research broadly, implement minimally.**
>
> Plans 04 and 05 provide industry best practices and architectural theory to _inform_ design decisions. However, every design decision produced by this plan must pass the **minimum-change test:**
>
> **"Does this change directly serve jahow's two requirements (CSAPI out of root index.ts, non-CSAPI code stops importing CSAPI), or are we adding work he didn't request?"**
>
> If a design choice is informed by industry best practice but increases the implementation scope beyond what jahow requires, prefer the simpler approach that still satisfies all boundary conditions. Use the industry research to _validate_ that the simpler approach is sound — not to justify a more complex one.
>
> Specifically:
>
> - Do NOT introduce adapter interfaces, factory patterns, or data record types unless they are strictly necessary to satisfy the boundary conditions. If the existing code can be relocated without restructuring, that is preferred.
> - Do NOT refactor `CSAPIQueryBuilder`'s constructor signature unless the current signature violates a boundary condition.
> - Do NOT suggest changes to EDR or other upstream modules — that is not our scope.
> - If a design decision is a close call, document both options and flag it for jahow's input rather than over-engineering a solution.
>
> See: [Scope Alignment Review Notes](scope-alignment-review-notes.md)

### Excluded From Scope

- **Plugin registration, mixin injection, decorator patterns:** Excluded — these require core to reference the sub-module (violates constraints 3 and 4).
- **Shared barrel re-exports from root:** Excluded — violates constraint 1.
- **Runtime dependency injection containers:** Over-engineered for a library consumed as a package.
- **Build system mechanics (`package.json` `"exports"`, Vite config, esbuild config):** Covered in Plans 01 and 03. This plan assumes the build pipeline supports the `./csapi` sub-path.
- **Individual TypeScript structural typing theory:** Covered in Plan 05. This plan applies Plan 05's findings to concrete design decisions.
- **Industry case study cataloging:** Covered in Plan 04. This plan consumes Plan 04's recommendations.

### What Remains Open

These are the genuine design decisions this plan must resolve:

- **Consumer API shape:** What do developers type to use CSAPI after decoupling? The current `endpoint.csapi(collectionId)` method will be removed. What replaces it?
  - Option A: `new CSAPIQueryBuilder(collectionDoc, resourceUrls)` — constructor injection (consumers extract data themselves)
  - Option B: `CSAPIQueryBuilder.fromEndpoint(endpoint, collectionId)` — static factory on the builder
  - Option C: `createCSAPIBuilder(endpoint, collectionId)` — standalone factory function
  - Option D: `createCSAPIBuilder({collectionDoc, resourceUrls})` — factory accepting data record
- **Coupling level:** What does the CSAPI module accept from core?
  - The constructor currently takes `Pick<OgcApiCollectionInfo, 'id' | 'title' | 'links'>` + `Map<string, string>` — already Level 3 (data record with type import). Does this stay, or does the type import need to go?
- **`hasConnectedSystems` placement:** Currently a getter on `OgcApiEndpoint` (line 334). It calls `checkHasConnectedSystems()` from `info.ts`, which checks conformance URIs only — **no CSAPI imports**. Can it stay on the endpoint?
- **`csapiCollections` placement:** Currently a getter on `OgcApiEndpoint` (line 237). It calls `parseCollections()` from `info.ts`, which checks `collection.links` for `ogc-cs:*` patterns — **no CSAPI imports**. Can it stay on the endpoint?
- **`extractRootResourceUrls()` placement:** Currently a private method on `OgcApiEndpoint` (line 431). It calls `scanCsapiLinks(links)` — **the second constraint violation**. Must be resolved.
- **`scanCsapiLinks` placement:** Currently in `csapi/helpers.ts` (line 129). Used by both `endpoint.ts` (line 435) and `url_builder.ts` (via `extractAvailableResources`). This is the "shared utility" problem identified in Plan 05.
- **`collection_id_to_csapi_builder_` cache:** Currently a private `Map` on `OgcApiEndpoint` (line 70). If `csapi()` moves off the endpoint, where does the cache live?
- **`getCollectionDocument()` accessibility:** Currently a private method on `OgcApiEndpoint` (line 438). The `csapi()` method calls it to get the raw collection document with links intact (because `parseBaseCollectionInfo` strips links). If CSAPI is decoupled, does `getCollectionDocument` need to become public? Or does the consumer provide the document?
- **Test migration:** 6 CSAPI tests in `endpoint.spec.ts` (lines 2836–2888): `detects Connected Systems support`, `can list all CSAPI collections`, `can produce a CSAPI query builder`, `caches the CSAPI query builder`, `reports no Connected Systems support`, `throws an error when calling csapi()`. Which stay on endpoint (testing `hasConnectedSystems`, `csapiCollections`) and which move to CSAPI?

---

## 4. Research Questions

### Core Questions

1. What is the complete architecture for decoupling CSAPI from `endpoint.ts`, expressed as before/after code for every affected integration point?
2. What consumer API replaces `endpoint.csapi(collectionId)`, and how does it satisfy all four boundary conditions while maximizing developer ergonomics?
3. How does each property and method currently straddling the module boundary (`hasConnectedSystems`, `csapiCollections`, `csapi()`, `extractRootResourceUrls`, `scanCsapiLinks`, `collection_id_to_csapi_builder_`) resolve to one side of the boundary?
4. How do Plan 04's industry patterns and Plan 05's coupling analysis synthesize into a single concrete recommendation, and where do they conflict?
5. What is the complete barrel file design for `src/ogc-api/csapi/index.ts` — every exported symbol, organized by category?
6. What is the complete test migration plan — which tests stay, which move, what new tests are needed?

### Detailed Questions

#### Synthesis of Prior Findings (6 questions)

1. What consumer API pattern did Plan 04 recommend? What coupling level did Plan 05 recommend? Do they align, or is there a conflict that must be resolved?
2. How does Plan 02's EDR pattern inform the CSAPI design? EDR uses `endpoint.edr(collectionId)` with a direct import of `EDRQueryBuilder` — this is the pattern jahow rejected for CSAPI. What specifically makes EDR acceptable and CSAPI not? Is it scale (656 lines vs 11,767), or a difference in coupling depth?
3. What `package.json` `"exports"` configuration did Plan 03 recommend? Does the Plan 06 barrel file design fit within that configuration?
4. What `import type` strategy did Plan 05 recommend? Does applying it to CSAPI's existing `import type { OgcApiCollectionInfo } from '../model.js'` satisfy constraint 3, or does even a type-only import violate the spirit of the boundary?
5. What `scanCsapiLinks` placement did Plan 05 recommend? Does the recommendation hold when applied to the concrete data flow in `endpoint.ts` lines 431–436 (`extractRootResourceUrls` calls `scanCsapiLinks(links)`)?
6. Did any Plan 04 case study (AWS SDK v3, Octokit, Angular CDK, RxJS, zod) demonstrate a pattern where the core provides async data to the sub-module without importing it? How does that map to our `getCollectionDocument()` → `CSAPIQueryBuilder` pipeline?

#### Consumer API Design (8 questions)

7. The current `endpoint.csapi(collectionId)` method performs 4 operations: (a) checks `hasConnectedSystems`, (b) checks cache, (c) calls `getCollectionDocument(collectionId)` to get raw doc, (d) calls `extractRootResourceUrls()` to get root links, then constructs `new CSAPIQueryBuilder(doc, urls)`. After decoupling, who performs each of these 4 operations — the consumer, a factory function in CSAPI, or some combination?
8. If the consumer must call `endpoint.getCollectionDocument(collectionId)` to get the raw document, that method is currently private (line 438). Must it become public? What are the implications of exposing it?
9. If the consumer must call `extractRootResourceUrls()`, that method is currently private (line 431) and calls `scanCsapiLinks`. Must it become public? Or should the consumer use `endpoint.root` (a public-via-getter property) and call `scanCsapiLinks` themselves?
10. What does the recommended consumer code look like end-to-end? Write the exact TypeScript code a developer would use to create a CSAPI builder after decoupling. Compare to the current code.
11. How does the recommended pattern handle caching? Currently `endpoint.csapi()` caches builders in `collection_id_to_csapi_builder_`. If `csapi()` is removed, is caching the consumer's responsibility? Or does a factory function in CSAPI handle it?
12. How does the recommended pattern handle the `hasConnectedSystems` guard? Currently `csapi()` checks `await this.hasConnectedSystems` and throws if false. After decoupling, who checks? The consumer? A factory function? Or is the guard removed (let the builder fail naturally if resources aren't available)?
13. For the recommended consumer API pattern, draft the exact function/class signature with JSDoc documentation. Include parameter types, return type, thrown errors, and usage example.
14. How does the recommended pattern affect the `app/examples/edr.ts` demo and any other consumer examples in the repo? Draft the before/after for each.

#### `hasConnectedSystems` and `csapiCollections` Placement (5 questions)

15. `hasConnectedSystems` (endpoint.ts line 334) calls `checkHasConnectedSystems()` from `info.ts` (line 112), which checks conformance URIs `ogcapi-connectedsystems-1/1.0/conf/core` and `ogcapi-connectedsystems-2/1.0/conf/dynamic-data`. Neither `checkHasConnectedSystems` nor `hasConnectedSystems` imports anything from `csapi/`. Does this mean `hasConnectedSystems` can stay on the endpoint without violating constraint 3 or 4? Write the explicit constraint verification.
16. `csapiCollections` (endpoint.ts line 237) calls `parseCollections()` from `info.ts` (line 248), which checks `collection.links.some(link => /^ogc-cs:.+$/.test(link.rel))` (info.ts line 300–303). Neither `parseCollections` nor `csapiCollections` imports from `csapi/`. Does `csapiCollections` satisfy all boundary conditions? Write the explicit constraint verification.
17. If both `hasConnectedSystems` and `csapiCollections` stay on the endpoint, how does a consumer discover the CSAPI module? The endpoint has these two properties, but no method that creates a builder. What is the discoverability story?
18. Should `hasConnectedSystems` and `csapiCollections` be _also_ available from the CSAPI module (as standalone functions that accept conformance classes or collection data), creating a dual-availability pattern? Or should they exist in exactly one place?
19. If Plan 04 recommends a pattern where the sub-module provides its own capability checks (e.g., `CSAPIClient.isSupported(endpoint)`), does that conflict with keeping `hasConnectedSystems` on the endpoint?

#### `scanCsapiLinks` and `extractRootResourceUrls` Resolution (6 questions)

20. `scanCsapiLinks` (helpers.ts line 129) has these dependencies: it imports `CSAPIResourceTypes` from `./model.js` (the constant array of 9 resource type strings) and `CSAPIResourceType` type from `./model.js`. It accepts `Array<{rel?: string, href?: string}>` — a structural type. It returns `Map<string, string>`. Analyze: is this function fundamentally CSAPI-specific (it knows the 9 resource type strings), or could a generic version work?
21. `endpoint.extractRootResourceUrls()` (line 431–436) does: `const rootDoc = await this.root; const links = rootDoc?.links; return scanCsapiLinks(links)`. This is 6 lines of code that delegates to `scanCsapiLinks`. What are the options for eliminating this constraint violation?

- Option A: Inline `scanCsapiLinks` logic into endpoint (duplicate the ~40 lines).
- Option B: Move `scanCsapiLinks` to `shared/` or core utils (but it uses `CSAPIResourceTypes`).
- Option C: Make `extractRootResourceUrls` generic — scan for _any_ link patterns, not CSAPI-specific ones.
- Option D: Remove `extractRootResourceUrls` from endpoint entirely — let the consumer (or CSAPI factory) scan the root document links.
- Option E: Move just the `CSAPIResourceTypes` constant to a shared location, then move `scanCsapiLinks` to shared utils.

22. For each option in Q21, verify against all four boundary conditions with explicit ✓/✗.
23. Which option has the lowest migration effort while satisfying all constraints?
24. If Option D is chosen (remove from endpoint), how does the CSAPI factory/constructor get the root document links? Does `endpoint.root` need to be public? (Currently `root` is a private getter on line 72.)
25. The `root` property returns `Promise<OgcApiDocument>`. If it becomes public, does exposing the raw root document to consumers create any API surface concerns? Is there precedent in the existing codebase (e.g., `conformanceClasses` is already a public getter returning parsed data)?

#### `getCollectionDocument` and Data Pipeline (5 questions)

26. `getCollectionDocument(collectionId)` (line 438) fetches the raw collection document with links intact. This is critical because `parseBaseCollectionInfo()` strips the `links` array (as noted in the code comment at line 397). Does this method need to become public for the recommended consumer API to work?
27. If `getCollectionDocument` becomes public, what is the TypeScript signature and return type? It currently returns `Promise<OgcApiDocument>`. Is this return type sufficient, or should it be narrowed to indicate the collection-specific shape?
28. The `csapi()` method uses `collectionDoc as unknown as OgcApiCollectionInfo` (line 408) — a type assertion that bridges the gap between the raw document (`OgcApiDocument`) and the typed interface. After decoupling, where does this assertion live? In the consumer code, in a factory function, or is it eliminated?
29. Should the CSAPI module provide a `prepareCollectionForCSAPI(rawDoc: OgcApiDocument): Pick<OgcApiCollectionInfo, 'id' | 'title' | 'links'>` function that extracts and validates the data the builder needs?
30. What is the complete data flow diagram from "consumer has an `OgcApiEndpoint` instance" to "consumer has a `CSAPIQueryBuilder`"? Draw the before and after, showing every function call, data transformation, and module boundary crossing.

#### Barrel File Design (5 questions)

31. The current `src/index.ts` exports ~170 lines of CSAPI symbols from 3 source locations: `csapi/url_builder.ts` (the builder class), `csapi/model.ts` (~50 type exports + 3 value exports), `csapi/formats/index.ts` (~30 value exports + ~100 type exports). Draft the exact barrel file (`src/ogc-api/csapi/index.ts`) that re-exports all these symbols. Should it mirror the current root exports exactly, or curate differently?
32. Should the barrel file also export CSAPI-internal utilities that are currently not in root exports? (e.g., `scanCsapiLinks`, `formatDateTimeParameter`, `encodeResourceId`, `validateLimit`, `validateBbox`, `isValidResourceType`, `assertValidResourceType`)
33. Should the barrel file export the factory/constructor functions introduced by the new consumer API?
34. How should the barrel file organize exports? By source module (model, formats, builder), by category (types, values, functions), or flat?
35. Does the barrel file create any circular dependency risks? The barrel re-exports from `url_builder.ts`, which imports from `model.ts`, `helpers.ts`, `../model.js`, and `../../shared/errors.js`. None of these import from the barrel. Verify there is no cycle.

#### Test Migration (5 questions)

36. The 6 CSAPI tests in `endpoint.spec.ts` (lines 2836–2888) are organized in two `describe` blocks: "nominal case" (4 tests) and "non-CSAPI endpoint" (2 tests). After decoupling, classify each test:
    - `detects Connected Systems support` — tests `hasConnectedSystems`. If it stays on endpoint, the test stays.
    - `can list all CSAPI collections` — tests `csapiCollections`. If it stays on endpoint, the test stays.
    - `can produce a CSAPI query builder` — tests `endpoint.csapi('iot-sensors')`. This method is being removed. The test must be migrated or rewritten.
    - `caches the CSAPI query builder` — tests `endpoint.csapi()` caching. Must be migrated or rewritten.
    - `reports no Connected Systems support` — tests `hasConnectedSystems` === false. Stays on endpoint.
    - `throws an error when calling csapi()` — tests `endpoint.csapi()` throwing. Must be migrated or rewritten.
      Draft the concrete migration plan for each test.
37. The CSAPI test fixtures are in `fixtures/ogc-api/csapi/`. Are there fixture files specifically for the `endpoint.spec.ts` CSAPI tests (e.g., `sample-data-hub`)? What happens to them after migration?
38. After test migration, what is the test coverage for the CSAPI module boundary? Are there new tests needed to verify: (a) the factory/constructor works with endpoint-provided data, (b) the factory/constructor works with manually-provided data (no endpoint), (c) error handling when data is insufficient?
39. Does the test migration change `jest.config.cjs` or test file patterns?
40. Draft the exact before/after for the `describe('OgcApiEndpoint with CSAPI')` block — what remains in `endpoint.spec.ts` and what moves to CSAPI's test suite.

#### Before/After Code Comparison (4 questions)

41. Draft the exact before/after for `src/ogc-api/endpoint.ts` — show every import removed, every method removed, every property removed, and any new public methods added.
42. Draft the exact before/after for `src/index.ts` — show every CSAPI export removed.
43. Draft the exact contents of the new `src/ogc-api/csapi/index.ts` barrel file.
44. If a factory function is introduced, draft the exact file it lives in (e.g., `src/ogc-api/csapi/factory.ts` or added to `url_builder.ts`) with complete TypeScript source.

**Total: 44 detailed questions**

---

## 5. Sources

### Primary Sources (In Workspace)

| Source                                        | Path                                               | What to Extract                                                                                                                                                               |
| --------------------------------------------- | -------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Endpoint CSAPI imports (violations)           | `src/ogc-api/endpoint.ts` (lines 52–53)            | The two imports that must be eliminated: `CSAPIQueryBuilder` and `scanCsapiLinks`                                                                                             |
| Endpoint class declaration and cache          | `src/ogc-api/endpoint.ts` (lines 57–70)            | Class fields: `collection_id_to_csapi_builder_: Map<string, CSAPIQueryBuilder>`, `root_`, `conformance_`, private getters                                                     |
| Endpoint `hasConnectedSystems`                | `src/ogc-api/endpoint.ts` (lines 320–338)          | Calls `checkHasConnectedSystems()` from `info.ts` — no CSAPI imports                                                                                                          |
| Endpoint `csapiCollections`                   | `src/ogc-api/endpoint.ts` (lines 218–244)          | Calls `parseCollections()` from `info.ts` — no CSAPI imports                                                                                                                  |
| Endpoint `csapi()` method                     | `src/ogc-api/endpoint.ts` (lines 385–413)          | 4-step data flow: hasConnectedSystems check → cache → getCollectionDocument → extractRootResourceUrls → new CSAPIQueryBuilder                                                 |
| Endpoint `extractRootResourceUrls()`          | `src/ogc-api/endpoint.ts` (lines 425–436)          | Calls `scanCsapiLinks(rootDoc.links)` — the second violation                                                                                                                  |
| Endpoint `getCollectionDocument()`            | `src/ogc-api/endpoint.ts` (lines 438–468)          | Private method returning raw OgcApiDocument with links intact                                                                                                                 |
| Endpoint EDR pattern (precedent)              | `src/ogc-api/endpoint.ts` (lines 341–354)          | `edr()` method: checks `hasEnvironmentalDataRetrieval`, gets `getCollectionInfo` (not raw doc), constructs `new EDRQueryBuilder(collection)` — a simpler data flow than CSAPI |
| CSAPIQueryBuilder constructor                 | `src/ogc-api/csapi/url_builder.ts` (lines 106–180) | Accepts `Pick<OgcApiCollectionInfo, 'id' \| 'title' \| 'links'>` + optional `Map<string, string>`. Already uses structural typing via `Pick<>`.                               |
| CSAPIQueryBuilder imports from core           | `src/ogc-api/csapi/url_builder.ts` (line 1)        | `import type { OgcApiCollectionInfo } from '../model.js'` — type-only import                                                                                                  |
| CSAPI model imports from core                 | `src/ogc-api/csapi/model.ts` (lines 1–2)           | `import type { BoundingBox, DateTimeParameter, CrsCode, MimeType } from '../../shared/models.js'` and `import type { OgcApiDocumentLink } from '../model.js'`                 |
| CSAPI helpers imports from core               | `src/ogc-api/csapi/helpers.ts` (line 3)            | `import type { BoundingBox } from '../../shared/models.js'`                                                                                                                   |
| `scanCsapiLinks` full implementation          | `src/ogc-api/csapi/helpers.ts` (lines 129–170)     | 40 lines, uses `CSAPIResourceTypes` constant, accepts structural `Array<{rel?, href?}>`, returns `Map<string, string>`                                                        |
| `checkHasConnectedSystems`                    | `src/ogc-api/info.ts` (lines 112–123)              | Checks conformance URIs only — zero CSAPI imports                                                                                                                             |
| `parseCollections` with `hasConnectedSystems` | `src/ogc-api/info.ts` (lines 248–309)              | Sets `hasConnectedSystems = true` when `link.rel` matches `/^ogc-cs:.+$/` — zero CSAPI imports, uses regex only                                                               |
| Root CSAPI exports                            | `src/index.ts` (lines 45–252)                      | ~170 lines of CSAPI exports from `csapi/url_builder.ts`, `csapi/model.ts`, `csapi/formats/index.ts`                                                                           |
| CSAPI tests in endpoint                       | `src/ogc-api/endpoint.spec.ts` (lines 2836–2888)   | 6 tests in 2 describe blocks: nominal (4 tests) + non-CSAPI (2 tests)                                                                                                         |
| EDR query builder imports                     | `src/ogc-api/edr/url_builder.ts` (lines 1–20)      | EDR imports `OgcApiCollectionInfo` from `../model.js` — same pattern as CSAPI                                                                                                 |
| CSAPI formats barrel                          | `src/ogc-api/csapi/formats/index.ts`               | What the formats sub-module exports — needed for barrel file design                                                                                                           |
| CSAPI directory structure                     | `src/ogc-api/csapi/`                               | 10 source files + `formats/` (8 files) + `integration/` (test files) + `formats/sensorml/` + `formats/swecommon/`                                                             |

### External Sources

| Source                                  | URL/Reference                                                                                     | What to Extract                                                                                                                           |
| --------------------------------------- | ------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| TypeScript Handbook — Structural Typing | https://www.typescriptlang.org/docs/handbook/type-compatibility.html                              | Applied context for the `Pick<OgcApiCollectionInfo, ...>` pattern — does structural compatibility allow the type import to be eliminated? |
| TypeScript Handbook — `import type`     | https://www.typescriptlang.org/docs/handbook/modules/reference.html#type-only-imports-and-exports | Whether `import type` creates any dependency that violates constraints                                                                    |
| Node.js subpath exports                 | https://nodejs.org/api/packages.html#subpath-exports                                              | Reference for barrel file → `"exports"` field mapping                                                                                     |
| ESLint `no-restricted-imports` rule     | https://eslint.org/docs/latest/rules/no-restricted-imports                                        | Enforcing module boundary via linting                                                                                                     |
| TypeScript Project References           | https://www.typescriptlang.org/docs/handbook/project-references.html                              | Enforcing module boundary at compile time                                                                                                 |
| Martin Fowler — Extract Module          | https://refactoring.guru/refactoring/catalog                                                      | Migration strategy patterns                                                                                                               |
| OGC API - Connected Systems Part 1      | https://docs.ogc.org/is/23-001/23-001.html                                                        | Conformance URIs used by `checkHasConnectedSystems`                                                                                       |
| OGC API - Connected Systems Part 2      | https://docs.ogc.org/is/23-002/23-002.html                                                        | Conformance URIs used by `checkHasConnectedSystems`                                                                                       |

### Prior Research Findings

| Finding          | Path                                                                        | What to Use                                                                                                                                             |
| ---------------- | --------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Plan 02 findings | `docs/research/phase-6/findings/02-edr-integration-pattern-analysis.md`     | EDR decoupling pattern as baseline: how `edr()` works, why it's acceptable at EDR's scale, what patterns carry over to CSAPI and what doesn't           |
| Plan 03 findings | `docs/research/phase-6/findings/03-separate-entry-point-design-patterns.md` | `package.json` `"exports"` configuration, barrel file mechanics, TypeScript declaration generation for sub-paths                                        |
| Plan 04 findings | `docs/research/phase-6/findings/04-sub-module-api-design-patterns.md`       | Recommended consumer API pattern, coupling level precedent from industry, async data handling patterns                                                  |
| Plan 05 findings | `docs/research/phase-6/findings/05-module-decoupling-patterns.md`           | Coupling level recommendation, `scanCsapiLinks` placement analysis, `import type` strategy, structural typing implications, module boundary enforcement |

---

## 6. Research Methodology

### Phase 1: Synthesize Prior Findings and Resolve Conflicts (~50 minutes)

**Objective:** Extract the concrete recommendations from Plans 02–05 and identify any conflicts that must be resolved before design can begin.

**Tasks:**

1. Extract Plan 02's EDR pattern summary — document the exact `edr()` data flow and compare point-by-point with `csapi()`: What does EDR do that CSAPI can reuse? Where does CSAPI diverge? (EDR uses `getCollectionInfo` which strips links; CSAPI uses `getCollectionDocument` which preserves links.)
2. Extract Plan 03's recommended `package.json` `"exports"` configuration — verify it supports the barrel file design needed for CSAPI's ~170 exported symbols.
3. Extract Plan 04's recommended consumer API pattern — document the exact pattern name, which industry libraries use it, and what it looks like in code.
4. Extract Plan 05's recommended coupling level — document which level (1–4) was selected, the `import type` strategy, and the `scanCsapiLinks` placement recommendation.
5. Cross-reference Plan 04 (consumer API) with Plan 05 (coupling level) — identify conflicts. For example: if Plan 04 recommends "constructor injection of core instance" but Plan 05 recommends "data record (no core import)", these conflict and must be reconciled.
6. Cross-reference Plan 02 (EDR pattern) with constraint 3 — EDR's `endpoint.edr()` imports `EDRQueryBuilder` directly. Why is this acceptable for EDR but not CSAPI? Document the reasoning (scale, jahow's explicit feedback, or both).

**Output:** Conflict resolution document with concrete recommendation for consumer API + coupling level + `scanCsapiLinks` placement. Every conflict is resolved with rationale.

### Phase 2: Design the Consumer API (~50 minutes)

**Objective:** Produce the exact consumer API with TypeScript signatures, before/after code, and data flow diagrams.

**Tasks:**

1. Draft the recommended consumer API function/class with complete TypeScript signature, JSDoc, parameter types, return type, and usage example.
2. Draft the before/after consumer code comparison:
   - **Before:** `const builder = await endpoint.csapi('weather-stations');`
   - **After:** [the new recommended pattern]
3. Design the data pipeline: how does a consumer get from `OgcApiEndpoint` to `CSAPIQueryBuilder`? Step by step, function by function. Document every function call, what data crosses the module boundary, and in which direction.
4. Design the async flow: currently `csapi()` is async because it awaits `hasConnectedSystems`, `getCollectionDocument`, and `extractRootResourceUrls`. The new API must handle these awaits somewhere. Where?
5. Design the caching strategy: currently `collection_id_to_csapi_builder_` is a private Map on the endpoint. Does caching move to CSAPI (factory function caches), to the consumer (manual caching), or is it eliminated?
6. Design the `hasConnectedSystems` guard: currently `csapi()` throws `EndpointError` if `hasConnectedSystems` is false. Does the new API replicate this guard, or leave it to the consumer?
7. Design the error handling: what errors can the new API throw? `EndpointError`? A new CSAPI-specific error? Standard TypeScript errors?
8. Verify the complete consumer API against all four boundary conditions with explicit ✓/✗.

**Output:** Complete consumer API design with TypeScript source, data flow diagram, and boundary verification.

### Phase 3: Resolve Module Boundary Integration Points (~50 minutes)

**Objective:** Make a placement decision for every function, property, and type currently straddling the core ↔ CSAPI boundary.

**Tasks:**

1. **`hasConnectedSystems`:** Verify import graph (endpoint → info.ts → no CSAPI). Write explicit ✓/✗ for each constraint. Decision: stays on endpoint? Also available from CSAPI?
2. **`csapiCollections`:** Same analysis as #1. Verify `parseCollections` in `info.ts` uses only `link.rel` regex, no CSAPI constant imports. Decision: stays on endpoint?
3. **`scanCsapiLinks`:** Apply Plan 05's recommendation. Evaluate all 5 options from Q21 against constraints. Select the option. Draft the before/after code for `endpoint.ts` and `csapi/helpers.ts`.
4. **`extractRootResourceUrls`:** Directly dependent on `scanCsapiLinks`. Once `scanCsapiLinks` is resolved, this resolves automatically. Draft the before/after.
5. **`getCollectionDocument`:** Determine if it must become public. If so, draft the public API (signature, JSDoc, return type). If not, document how the consumer gets the raw collection document.
6. **`collection_id_to_csapi_builder_` cache:** Determine where caching lives. Draft the before/after for the endpoint class.
7. **`csapi()` method:** This is being removed. Draft the exact deletion — the ~30 lines (385–413) plus the JSDoc block (~20 lines).
8. **Shared types:** List every type that crosses the boundary. For each, document: current import path, proposed import strategy (`import type` from core, re-declare, or use `Pick<>`), and constraint verification.
   - `OgcApiCollectionInfo` (used by `url_builder.ts` via `Pick<>`)
   - `OgcApiDocumentLink` (used by `model.ts`)
   - `BoundingBox`, `DateTimeParameter`, `CrsCode`, `MimeType` (used by `model.ts`)
   - `EndpointError` (used by `url_builder.ts` and `helpers.ts`)
   - `BoundingBox` (used by `helpers.ts`)
9. Document the complete import graph after refactoring — draw every module and every dependency direction. Verify no arrows point from core to CSAPI.

**Output:** Complete boundary resolution table with before/after code for every integration point.

### Phase 4: Design Barrel File and Export Surface (~30 minutes)

**Objective:** Draft the exact `src/ogc-api/csapi/index.ts` barrel file and verify it covers all symbols currently exported from root.

**Tasks:**

1. Inventory all CSAPI symbols currently exported from `src/index.ts` — categorize by source file and export kind (value, type, class)
2. Draft the barrel file contents — every `export` and `export type` statement, organized by category
3. Determine if additional symbols should be exported (factory function, `scanCsapiLinks`, helper utilities) that aren't in root today
4. Verify no circular dependencies: trace every import chain from the barrel file through all re-exported modules
5. Verify the barrel file works with Plan 03's `package.json` `"exports"` configuration

**Output:** Complete barrel file source code draft.

### Phase 5: Test Migration and Verification Plan (~30 minutes)

**Objective:** Draft the complete test migration plan and post-refactoring verification checklist.

**Tasks:**

1. Classify each of the 6 CSAPI tests in `endpoint.spec.ts` — stays, moves, or rewrites
2. For tests that move: draft the destination file, the before/after test code, and any fixture changes
3. For tests that stay: document why they don't violate constraints (they test endpoint behavior, not CSAPI internals)
4. Draft new tests needed for the CSAPI module boundary: factory function tests, data validation tests, error handling tests
5. Draft the post-refactoring verification checklist:
   - `git grep "from.*csapi" src/ogc-api/endpoint.ts` → 0 matches
   - `git grep "csapi" src/index.ts` → 0 matches
   - `npm run typecheck` → passes
   - `npm run test:browser` → passes
   - `npm run test:node` → passes
   - `npm run format:check` → passes
   - `npm run lint` → passes
   - Removing `src/ogc-api/csapi/` → core still compiles (the litmus test)

**Output:** Complete test migration plan with before/after code and verification checklist.

### Phase 6: Synthesis and Final Documentation (~40 minutes)

**Objective:** Consolidate all phase outputs into the deliverable architectural document.

**Tasks:**

1. Synthesize findings from Phases 1–5 into the findings report structure
2. Verify all 44 research questions are answered with specific, evidenced answers
3. Validate every design decision against all four boundary conditions — explicit ✓/✗ for each
4. Produce the class diagram showing the before/after module relationship
5. Produce the data flow diagram showing the before/after consumer pipeline
6. Write the deliverable document
7. Cross-reference with Plan 08 (what Plan 08 needs: file list, commit sequence, before/after diffs)
8. Verify the design is implementable — no unresolved decisions that would block Plan 08

**Output:** Completed architectural findings report at `docs/research/phase-6/findings/06-endpoint-decoupling-architecture.md`

---

## 7. Success Criteria

This research is complete when:

- [ ] All 44 detailed research questions have specific, evidenced answers
- [ ] Findings respect all boundary conditions listed in Section 3
- [ ] Prior findings from Plans 02–05 are synthesized with explicit conflict resolution where recommendations diverge
- [ ] Consumer API is _fully specified_ — exact TypeScript function/class signature, JSDoc, parameter types, return type, usage example, before/after comparison
- [ ] Every integration point currently straddling the module boundary has a concrete placement decision with before/after code
- [ ] `scanCsapiLinks` placement is resolved with a selected option and before/after code
- [ ] `hasConnectedSystems` and `csapiCollections` placement is resolved with explicit constraint verification (✓/✗ for each)
- [ ] `getCollectionDocument` visibility decision is made and documented
- [ ] Complete barrel file (`src/ogc-api/csapi/index.ts`) is drafted with every exported symbol
- [ ] Data flow diagram (before/after) is produced showing the complete pipeline from `OgcApiEndpoint` to `CSAPIQueryBuilder`
- [ ] All 6 CSAPI tests in `endpoint.spec.ts` are classified (stays/moves/rewrites) with migration plan
- [ ] Post-refactoring verification checklist is complete
- [ ] The "litmus test" is explicitly verified: removing `src/ogc-api/csapi/` leaves core functional
- [ ] Deliverable document is complete and follows the findings report template
- [ ] **Implementation scope gate applied:** Every design decision passes the minimum-change test — no changes beyond what jahow's requirements demand
- [ ] Findings are cross-referenced with Plan 08 and provide everything Plan 08 needs to produce the changelist

---

## 8. Deliverable

**Title:** Endpoint Decoupling Architecture: Complete Design Blueprint for CSAPI Extraction

**Location:** `docs/research/phase-6/findings/06-endpoint-decoupling-architecture.md`

**Required Sections:**

1. Executive Summary — the selected architecture in one paragraph: consumer API shape, coupling level, module boundary design, and key decisions
2. Prior Findings Synthesis — what Plans 02–05 recommended, where they aligned, where they conflicted, and how conflicts were resolved
3. Consumer API Design — exact TypeScript signatures, JSDoc, before/after consumer code, data flow diagram, async handling, caching, error handling
4. Integration Point Resolution Table — for each function/property/type straddling the boundary: current location, decision (stays/moves/removed/refactored), before/after code, constraint verification (✓/✗ × 4)
5. `scanCsapiLinks` Resolution — selected option, before/after code, constraint verification
6. Shared Type Import Strategy — for each type crossing the boundary: import path, strategy (`import type`, re-declare, `Pick<>`), constraint verification
7. Barrel File Design — complete `src/ogc-api/csapi/index.ts` source code draft
8. Test Migration Plan — each test classified (stays/moves/rewrites) with before/after code
9. Post-Refactoring Verification Checklist — every verification command and expected result
10. Class Diagram — before/after module relationship diagram
11. Data Flow Diagram — before/after consumer pipeline
12. Boundary Condition Verification Summary — master ✓/✗ table across all design decisions × all 4 constraints
13. Impact on Plan 08 — what Plan 08 consumes from this document, what decisions are final, what (if anything) remains deferred
14. Open Questions — anything unresolved (ideally: nothing)

---

## 9. Risks and Mitigation

| Risk                                                                                                                                                                               | Impact                                                                            | Mitigation                                                                                                                                                                                                                                                                                                                                            |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Plan 04 recommends constructor injection (sub-module accepts core instance) but Plan 05 recommends data record coupling (zero core imports) — these are fundamentally incompatible | Must choose one, sacrificing the other's benefits                                 | Phase 1 explicitly cross-references both recommendations. If they conflict, this plan resolves by evaluating both against boundary conditions + migration effort + developer ergonomics. The option that satisfies all 4 constraints wins; if both satisfy, the lower-migration-effort option wins.                                                   |
| `getCollectionDocument` may need to become public, expanding the `OgcApiEndpoint` API surface                                                                                      | jahow may object to new public methods on the endpoint class                      | Evaluate whether the factory function can use existing public getters instead. `endpoint.root` is private; `endpoint.conformanceClasses` is public. If a new public method is unavoidable, minimize its surface (return a narrow type, not the full raw document).                                                                                    |
| The `scanCsapiLinks` resolution may require code duplication, which is a maintenance risk                                                                                          | If duplicated, changes to link scanning conventions must be applied in two places | Assess all 5 options honestly. If duplication is selected, document a linting rule or code comment that flags the twin as needing synchronized updates.                                                                                                                                                                                               |
| `hasConnectedSystems` and `csapiCollections` may be controversial to keep on the endpoint — jahow may consider them "CSAPI in core"                                                | Could be rejected in PR review                                                    | Prepare the explicit import graph analysis showing these properties have zero CSAPI imports. `checkHasConnectedSystems` uses conformance URI strings only; `parseCollections` uses `link.rel` regex only. Neither imports from `csapi/`. If jahow still objects, the fallback plan (move to CSAPI module as standalone functions) is designed in Q18. |
| The 6 CSAPI tests use a `sample-data-hub` fixture that may have CSAPI-specific content                                                                                             | Fixture files may need to be duplicated or restructured                           | Inventory the fixture files used by the CSAPI tests. Determine if they can be shared or must move with the tests.                                                                                                                                                                                                                                     |
| The barrel file with ~170 re-exports may affect tree-shaking                                                                                                                       | Consumers importing one CSAPI symbol may pull in the entire module                | Plan 05's findings on tree-shaking inform this. If the barrel file hurts tree-shaking, consider per-file deep imports as an alternative (e.g., `@camptocamp/ogc-client/csapi/url_builder`).                                                                                                                                                           |
| The architecture may look clean on paper but fail TypeScript compilation due to subtle circular references or module resolution issues                                             | Wasted implementation time                                                        | Phase 6 includes a barrel file circular dependency verification task. Plan 08 should include a "build and verify" step before committing.                                                                                                                                                                                                             |

---

## 10. Research Status Checklist

- [ ] Phase 1: Synthesize Prior Findings and Resolve Conflicts — Not Started
- [ ] Phase 2: Design the Consumer API — Not Started
- [ ] Phase 3: Resolve Module Boundary Integration Points — Not Started
- [ ] Phase 4: Design Barrel File and Export Surface — Not Started
- [ ] Phase 5: Test Migration and Verification Plan — Not Started
- [ ] Phase 6: Synthesis and Final Documentation — Not Started
- [ ] Deliverable document created
- [ ] Cross-references updated in Plan 08

**Start Date:** —
**Completion Date:** —
**Actual Time:** —
