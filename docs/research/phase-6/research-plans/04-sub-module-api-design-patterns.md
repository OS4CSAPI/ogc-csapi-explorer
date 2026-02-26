# Research Plan 04: TypeScript Sub-Module API Design Patterns (Industry Case Studies)

> **Plan 4 of 8** | **Phase 6 — Upstream Acceptance Refactoring**

---

## Metadata

| Field                  | Value                                                     |
| ---------------------- | --------------------------------------------------------- |
| **Status**             | Not Started                                               |
| **Plan Type**          | External research (industry case studies)                 |
| **Date Created**       | 2026-02-23                                                |
| **Last Updated**       | 2026-02-23                                                |
| **Estimated Time**     | 2–3 hours                                                 |
| **Actual Time**        | —                                                         |
| **Depends On**         | None                                                      |
| **Blocks**             | Plan 06 (Endpoint Decoupling Architecture)                |
| **Strategy Reference** | [research-strategy.md § Plan 04](../research-strategy.md) |

---

## 1. Research Objective

Produce a pattern catalog of consumer-facing API designs from 5+ proven TypeScript/JavaScript libraries where a sub-module depends on a core module, imported via a separate path, and the core has no knowledge of the sub-module's existence. For each library, document the exact consumer API shape (constructor injection, factory function, static method, standalone functions), what the sub-module accepts from the core (concrete class, interface, config object, primitives), how types are shared across the boundary, and how asynchronous data flows from core to sub-module. The deliverable is a ranked comparison of API patterns with a recommendation for which pattern best fits the CSAPI boundary conditions.

This plan answers the design question that Plan 06 needs most: **what should consumers actually type when they use CSAPI, and what precedent exists for each option?**

---

## 2. Sequencing Rationale

### Why Plan 4?

This is the "External-Knowledge-First" plan for consumer API design. Plan 06 (Endpoint Decoupling Architecture) must decide the consumer-facing API shape — `new CSAPIClient(endpoint)` vs `CSAPIClient.fromEndpoint(endpoint)` vs `createCSAPIClient({baseUrl, conformance})` vs standalone functions. Without studying how mature libraries solve the identical problem (sub-module accepts core instance, builds on it, never imports back), we'd design from instinct rather than evidence.

This plan has no dependencies and can run in parallel with Plans 01, 02, 05, and 07. However, its findings are critical input to Plan 06, which cannot begin design synthesis without knowing which API patterns are proven in the ecosystem. Plan 04 focuses on the **consumer API shape** (what developers type), while Plan 05 focuses on the **internal architecture** (how the module boundary is structured). Together they provide the full picture for Plan 06.

### Dependency Chain

- **Builds on:** Nothing — this is independent external research. However, familiarity with the CSAPI codebase (the `CSAPIQueryBuilder` constructor, the `csapi()` method on `OgcApiEndpoint`, and the data requirements) provides context for evaluating library patterns against our specific use case.
- **Feeds into:**
  - **Plan 06** (Endpoint Decoupling Architecture): Needs the pattern catalog and recommendation to decide the consumer API shape. Without this, Plan 06 would choose an API design without evidence.
  - **Plan 08** (File-Level Changelist and Commit Strategy): Indirectly — the consumer API shape from 06 (informed by 04) determines what code changes are needed in the barrel file and public API.

---

## 3. Boundary Conditions

### Non-Negotiable Constraints

1. **One-way dependency only (Constraint 4):** Only study patterns where the sub-module depends on the core, never the reverse. Every library case study must demonstrate that the core package can exist and function without the sub-module. This is the most restrictive constraint — it eliminates plugin architectures, mixin patterns, and any design where the host knows about the extension.
2. **Sub-module imported via separate path (Constraint 2):** Only study patterns where consumers import the sub-module from a distinct path (`@scope/package/submodule` or `@scope/submodule`). Cases where the sub-module is re-exported from the core's main entry point are irrelevant.
3. **Core has no knowledge of sub-module (Constraint 3):** The core module must not import, reference, or expose any sub-module code. Patterns where the core provides a "register plugin" API or a slot for the sub-module are excluded.

### Excluded From Scope

- **Plugin registration architectures (e.g., Express middleware `.use()`):** The host module imports and registers the plugin, violating constraint 3 and 4. Not applicable even as inspiration.
- **Mixin/decorator/monkey-patching patterns:** CSAPI cannot add methods to `OgcApiEndpoint` at runtime. Violates constraints 3 and 4.
- **Shared barrel re-exports:** Patterns where the sub-module is re-exported from the core's root entry. Violates constraint 1.
- **Build system mechanics and `package.json` configuration:** Plan 03 covers how the sub-path export is technically configured. This plan focuses on API design, not packaging.
- **Internal module architecture (adapter patterns, dependency inversion, type extraction):** Plan 05 covers the internal structural patterns. This plan focuses on the external consumer-facing API.
- **CommonJS or dual-module patterns:** The `ogc-client` package is ESM-only (`"type": "module"`). CJS interop patterns are irrelevant.

### What Remains Open

- Whether the CSAPI consumer API should accept the `OgcApiEndpoint` class instance directly (tight coupling, simple API) or extracted data (loose coupling, more verbose API)
- Whether a factory function, a class constructor, a static method, or standalone functions is the best entry pattern
- Whether the API should be synchronous (accepting already-resolved data) or asynchronous (accepting the endpoint and resolving data internally)
- Whether there should be a single entry class (`CSAPIClient`) or multiple standalone functions (`getSystems(endpoint)`, `getDatastreams(endpoint)`)
- How to handle the specific data `CSAPIQueryBuilder` currently needs: collection document with links, root document resource URLs, conformance classes
- Whether the consumer API should mirror the current `endpoint.csapi(collectionId)` pattern (method on endpoint returning builder) or invert it (`new CSAPIClient(endpoint).forCollection(collectionId)`)

---

## 4. Research Questions

### Core Questions

1. What consumer API shapes do proven TypeScript libraries use when a sub-module depends on a core module instance, and what is the dominant pattern?
2. What does each sub-module accept from the core — a concrete class instance, an interface, a configuration object, or primitive values?
3. How do these libraries share types between core and sub-module without creating circular dependencies?
4. How do they handle asynchronous data that the core provides (e.g., data from HTTP requests that the sub-module needs)?
5. Which patterns best map to our specific constraints (one-way dependency, separate import path, core-blind-to-sub-module)?

### Detailed Questions

#### AWS SDK v3 Pattern (6 questions)

1. How does `@aws-sdk/lib-storage` (multipart upload) consume `@aws-sdk/client-s3`? Does it accept the `S3Client` instance, a configuration object, or individual parameters?
2. What is the consumer code for using `@aws-sdk/lib-storage`? Show the exact import statements and construction pattern.
3. Does `@aws-sdk/lib-storage` reference `S3Client` as a concrete class or through an interface/type? How is the dependency expressed in TypeScript?
4. Does `@aws-sdk/client-s3` know that `@aws-sdk/lib-storage` exists? (Expected: no — verify by checking if `client-s3` imports anything from `lib-storage`)
5. How does `@aws-sdk/lib-storage` handle the asynchronous flow? (S3 uploads require pre-configured client → the sub-module wraps multi-step upload logic around the client)
6. Are there other AWS SDK v3 sub-packages that demonstrate the same pattern? (e.g., `@aws-sdk/s3-request-presigner`, `@aws-sdk/abort-controller`)

#### Octokit Pattern (6 questions)

7. How does `@octokit/plugin-rest-endpoint-methods` compose with `@octokit/core`? What is the consumer API for adding the plugin?
8. Does Octokit use a plugin registration pattern (`.plugin()` method on core) or a wrapper pattern (sub-module wraps the core)? Which direction does the dependency flow?
9. Does Octokit's pattern satisfy our constraints? (Specifically: does `@octokit/core` import from the plugin, or does the plugin import from core only?)
10. What TypeScript type does the plugin accept — `Octokit` class, an `OctokitOptions` interface, or something else?
11. How does Octokit share types between core and plugins? Are shared types in a separate `@octokit/types` package?
12. Is the Octokit plugin pattern applicable to our use case, or does it violate constraint 3 (core references plugin)?

#### Angular CDK Pattern (5 questions)

13. How does `@angular/cdk/testing` relate to `@angular/core`? Does it import concrete classes (`TestBed`) or abstracted interfaces?
14. What is the consumer API for using `@angular/cdk/testing` — constructor injection, factory function, or standalone utilities?
15. Does `@angular/core` have any imports from `@angular/cdk`? (Expected: no — CDK depends on core, not reverse)
16. How does Angular CDK share types with Angular core — separate type packages, or direct imports from core's public API?
17. Does the CDK sub-path export pattern (`@angular/cdk/testing`) use a barrel file? What does it re-export?

#### Stateless Utility Libraries: RxJS, date-fns, lodash-es (5 questions)

18. How does `rxjs/operators` relate to `rxjs` core? Do operators accept `Observable` as a concrete class or through a generic interface?
19. What is the consumer API for using `rxjs/operators` — are they standalone functions that accept and return observables, or methods on the Observable class?
20. How does `date-fns` expose sub-path imports (`date-fns/format`, `date-fns/locale/en-US`)? Are these standalone functions with no shared state?
21. For `lodash-es` per-function imports (`lodash-es/chunk`), are there shared types that flow between the core package and individual functions?
22. How applicable are stateless utility patterns to our use case? CSAPI is **stateful** (needs endpoint data, conformance classes, collection links) — does the stateless function pattern still work if we extract the state into parameters?

#### Zod Ecosystem Pattern (4 questions)

23. How does `zod-to-json-schema` depend on `zod`? Does it accept a `z.ZodType` instance, a schema object, or something else?
24. Does `zod` know about `zod-to-json-schema`? (Expected: no — verify the dependency direction)
25. How does `zod-to-json-schema` reference zod's types — direct import from `zod`, or re-declaration of compatible types?
26. Is the zod ecosystem pattern (extension packages that accept core instances) applicable to our single-package sub-path scenario?

#### Additional Library Case Study (4 questions)

27. Identify at least one additional TypeScript library with a sub-module that depends on a core (candidates: `@trpc/server` + `@trpc/client`, `drizzle-orm` + `drizzle-orm/pg-core`, `effect` ecosystem, `@tanstack/react-query` + `@tanstack/query-core`, `msw` handlers). Document the consumer API.
28. What does the sub-module accept from the core — instance, interface, or primitives?
29. How are types shared?
30. Does the dependency flow match our constraints (one-way, separate import, core-blind)?

#### Cross-Cutting Synthesis (8 questions)

31. Across all libraries studied, what is the distribution of consumer API patterns? (Constructor injection, factory function, static method, standalone functions, wrapper class)
32. Is there a dominant pattern for stateful sub-modules (like CSAPI) that need data from the core instance? Is it different from stateless utility sub-modules?
33. What coupling level is most common: accepting the concrete core class, an interface/type, or extracted data primitives?
34. How do libraries handle the "async data from core" problem? (CSAPI needs collection links and conformance classes, which are resolved via HTTP requests on `OgcApiEndpoint`)
35. Do any studied libraries have an "adapter" layer between core and sub-module, or do they all accept the core object directly?
36. What error patterns are used when the sub-module receives an invalid or insufficient core object?
37. How do the library patterns compare in terms of discoverability (can consumers find the sub-module API via IDE autocompletion)?
38. Based on all evidence, what is the recommended consumer API pattern for CSAPI given our specific constraints?

**Total: 38 detailed questions**

---

## 5. Sources

### Primary Sources (In Workspace)

| Source                        | Path                                               | What to Extract                                                                                                                              |
| ----------------------------- | -------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| CSAPIQueryBuilder constructor | `src/ogc-api/csapi/url_builder.ts` (lines 106–174) | What data the builder needs: `Pick<OgcApiCollectionInfo, 'id' \| 'title' \| 'links'>` + optional `Map<string, string>` resource URLs         |
| Current `csapi()` method      | `src/ogc-api/endpoint.ts` (lines 385–413)          | How the endpoint currently provides data to the builder: `getCollectionDocument()`, `extractRootResourceUrls()`, `hasConnectedSystems` check |
| CSAPI model types             | `src/ogc-api/csapi/model.ts`                       | Types exported by CSAPI — what the consumer API must expose                                                                                  |
| Core model types              | `src/ogc-api/model.ts`                             | Shared types like `OgcApiCollectionInfo` that cross the module boundary                                                                      |
| Current root exports          | `src/index.ts`                                     | What CSAPI currently exports from root — the API surface that must move to `./csapi`                                                         |
| CSAPI helpers                 | `src/ogc-api/csapi/helpers.ts`                     | `scanCsapiLinks()` — the function `endpoint.ts` imports (must be eliminated or moved)                                                        |

### External Sources

| Source                   | URL/Reference                                                        | What to Extract                                                       |
| ------------------------ | -------------------------------------------------------------------- | --------------------------------------------------------------------- |
| AWS SDK v3 `lib-storage` | https://github.com/aws/aws-sdk-js-v3/tree/main/lib/lib-storage       | Consumer API, constructor signature, what it accepts from `client-s3` |
| AWS SDK v3 `client-s3`   | https://github.com/aws/aws-sdk-js-v3/tree/main/clients/client-s3     | Verify no imports from `lib-storage` — confirm one-way dependency     |
| Octokit core             | https://github.com/octokit/core.js                                   | Plugin architecture, `.plugin()` API, dependency direction            |
| Octokit REST plugin      | https://github.com/octokit/plugin-rest-endpoint-methods.js           | How it composes with core, consumer API, type dependencies            |
| Angular CDK testing      | https://github.com/angular/components/tree/main/src/cdk/testing      | Sub-path export, relationship to `@angular/core`, consumer API        |
| RxJS operators           | https://github.com/ReactiveX/rxjs/tree/master/src/internal/operators | How operators accept Observable, standalone function pattern          |
| date-fns sub-paths       | https://github.com/date-fns/date-fns                                 | Per-function export pattern, type sharing                             |
| zod-to-json-schema       | https://github.com/StefanTerdell/zod-to-json-schema                  | How it depends on zod, what types it accepts, consumer API            |
| zod core                 | https://github.com/colinhacks/zod                                    | Verify no imports from ecosystem packages                             |
| TanStack Query           | https://github.com/TanStack/query                                    | `@tanstack/query-core` + `@tanstack/react-query` sub-module pattern   |
| drizzle-orm              | https://github.com/drizzle-team/drizzle-orm                          | `drizzle-orm/pg-core` sub-path, consumer API, type dependencies       |

### Prior Research Findings

| Finding | Path | What to Use                                                                                                                                                    |
| ------- | ---- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| None    | —    | This is Plan 4 — no prior findings from Phase 6. The current CSAPIQueryBuilder constructor signature (from the codebase) provides the baseline for comparison. |

---

## 6. Research Methodology

### Phase 1: Deep Dive Case Studies (~60 minutes)

**Objective:** Document the consumer API, dependency direction, type sharing, and async handling for each of the 5+ selected libraries.

**Tasks:**

1. **AWS SDK v3:** Fetch `@aws-sdk/lib-storage` source — document the `Upload` class constructor, what it accepts from `S3Client`, how the consumer creates it, and verify that `client-s3` has no imports from `lib-storage`
2. **Octokit:** Fetch `@octokit/plugin-rest-endpoint-methods` — document the plugin function signature, how it composes with `Octokit.plugin()`, verify dependency direction, determine if the plugin pattern violates our constraints
3. **Angular CDK:** Fetch `@angular/cdk/testing` — document the consumer API, what it imports from `@angular/core`, verify no reverse dependencies
4. **RxJS operators:** Examine the operator function pattern — document how `map`, `filter`, etc. accept and return `Observable`, and whether this is a standalone function or method pattern
5. **zod ecosystem:** Fetch `zod-to-json-schema` — document how it accepts `z.ZodType`, verify `zod` core has no ecosystem knowledge
6. **Additional library:** Select one from TanStack Query, drizzle-orm, or tRPC — document the same dimensions (consumer API, dependency direction, type sharing, async handling)
7. For each library, fill in a structured record: Library | Consumer API Pattern | What it Accepts | Dependency Direction | Type Sharing Mechanism | Async Handling | Constraint Compliance (1–4)

**Output:** 6+ structured case study records

### Phase 2: Pattern Classification and Comparison (~30 minutes)

**Objective:** Classify the discovered patterns into categories and build a comparison matrix.

**Tasks:**

1. Classify each library's consumer API into one of: (a) Constructor injection (sub-module class takes core instance), (b) Factory function (standalone function returns configured sub-module), (c) Static method on sub-module class, (d) Wrapper class (sub-module wraps core entirely), (e) Standalone utility functions (no class, each function takes core data), (f) Plugin registration (core registers sub-module — expected: excluded)
2. Build comparison matrix with columns: Library | Pattern Type | Coupling Level (concrete/interface/data/params) | Async? | Constraint Fit (✓/✗ for each of constraints 1–4)
3. Identify which patterns satisfy ALL four constraints — these are the viable candidates for CSAPI
4. Rank the viable patterns by: developer ergonomics, discoverability, TypeScript autocompletion quality, and precedent frequency

**Output:** Classified comparison matrix with ranked viable patterns

### Phase 3: Application to CSAPI Use Case (~30 minutes)

**Objective:** Map each viable pattern to the specific CSAPI scenario and evaluate fit.

**Tasks:**

1. For each viable pattern, draft a concrete CSAPI consumer code example showing what the developer would type:
   - Constructor injection: `new CSAPIClient(endpoint)` or `new CSAPIClient(collectionDoc, resourceUrls)`
   - Factory function: `createCSAPIClient(endpoint)` or `createCSAPIClient({baseUrl, conformance, collectionLinks})`
   - Static method: `CSAPIClient.fromEndpoint(endpoint)` or `CSAPIClient.fromCollection(collectionDoc)`
   - Standalone functions: `getSystems(endpoint, collectionId, options)` or `getSystems(collectionDoc, options)`
2. Evaluate each against the async data problem: `CSAPIQueryBuilder` currently needs data that `OgcApiEndpoint` resolves asynchronously (collection document, root resource URLs, conformance). How does each pattern handle this?
3. Evaluate each against the "what data does CSAPI actually need" question: The constructor currently takes `Pick<OgcApiCollectionInfo, 'id' | 'title' | 'links'>` + `Map<string, string>`. How much of `OgcApiEndpoint` does CSAPI actually need?
4. Evaluate discoverability: if a consumer has `OgcApiEndpoint`, can their IDE lead them to the CSAPI API? (Constructor injection with endpoint param is more discoverable than standalone functions with extracted data)
5. Evaluate migration effort: which pattern requires the least change from the current `endpoint.csapi(collectionId)` API? Which requires the most?

**Output:** CSAPI-specific code examples for each viable pattern with evaluation across 5 dimensions

### Phase 4: Type Sharing Analysis (~20 minutes)

**Objective:** Determine how types flow across the core → sub-module boundary in each pattern, and what that means for CSAPI.

**Tasks:**

1. For each studied library, document how shared types are referenced: (a) direct import from core's public API, (b) re-declaration of compatible types, (c) shared type package, (d) structural typing (no explicit shared type)
2. Map to CSAPI: which core types does CSAPI currently import? (`OgcApiCollectionInfo` from `model.ts`, `EndpointError` from `shared/errors.ts`, various from `shared/models.ts`)
3. Determine if CSAPI can import these types from the core's public API (`@camptocamp/ogc-client`) at the type level only (i.e., `import type { OgcApiCollectionInfo } from '@camptocamp/ogc-client'`), or if it needs to use relative internal imports
4. Identify any type-sharing pitfalls: circular type references, type duplication, or types that are internal to core but needed by CSAPI
5. Document the recommended type-sharing approach based on ecosystem evidence

**Output:** Type sharing recommendation with concrete import patterns

### Phase 5: Synthesis and Documentation (~20 minutes)

**Objective:** Consolidate all phase outputs into the deliverable document.

**Tasks:**

1. Synthesize findings from Phases 1–4 into the findings report structure
2. Verify all 38 research questions are answered
3. Validate findings against boundary conditions (Constraints 1–4)
4. Produce the final recommendation with rationale
5. Write the deliverable document
6. Cross-reference with Plan 06 (what it needs: recommended pattern, type sharing approach) and Plan 05 (related internal architecture patterns)

**Output:** Completed findings report at `docs/research/phase-6/findings/04-sub-module-api-design-patterns.md`

---

## 7. Success Criteria

This research is complete when:

- [ ] All 38 detailed research questions have specific, evidenced answers
- [ ] Findings respect all boundary conditions listed in Section 3
- [ ] At least 5 library case studies are documented with structured records
- [ ] Each case study includes: consumer API pattern, what it accepts, dependency direction, type sharing mechanism, async handling, constraint compliance
- [ ] Patterns are classified into named categories (constructor injection, factory function, etc.)
- [ ] A comparison matrix is produced ranking patterns by constraint compliance, ergonomics, and frequency
- [ ] At least 3 CSAPI-specific consumer code examples are drafted (one per viable pattern)
- [ ] The async data flow problem is analyzed for each viable pattern (CSAPI needs data from HTTP requests that endpoint resolves)
- [ ] Type sharing across the core ↔ sub-module boundary is analyzed with a specific recommendation
- [ ] A clear recommendation is made for the CSAPI consumer API pattern, with rationale referencing the case studies
- [ ] Deliverable document is complete and follows the findings report template
- [ ] Findings are cross-referenced with Plans 05 and 06

---

## 8. Deliverable

**Title:** Sub-Module API Design Patterns: Industry Case Studies and Recommended Consumer API for CSAPI

**Location:** `docs/research/phase-6/findings/04-sub-module-api-design-patterns.md`

**Required Sections:** (per findings report template)

1. Executive Summary — the dominant pattern, the recommended API shape, and key evidence
2. Library Case Studies — 6+ structured records with full analysis
3. Pattern Classification Matrix — comparison table with constraint compliance
4. CSAPI Consumer API Candidates — concrete code examples for each viable pattern
5. Async Data Flow Analysis — how each pattern handles the endpoint → builder data pipeline
6. Type Sharing Analysis — how types cross the module boundary, recommended approach
7. Recommendation — the selected pattern with full rationale citing case study evidence
8. Key Takeaways — numbered list of critical findings
9. Impact on Implementation — what Plan 06 should consume, what decisions are made vs. deferred
10. Open Questions — anything unresolved that feeds into Plan 06

---

## 9. Risks and Mitigation

| Risk                                                                                                                                                                                    | Impact                                                                 | Mitigation                                                                                                                                                                                    |
| --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Most studied libraries use multi-package monorepos, not single-package sub-path exports                                                                                                 | Patterns may not directly apply to our single-package scenario         | Distinguish between patterns that require package boundaries (multi-repo) and patterns that work with sub-path exports (single package). Focus on the API shape, not the packaging mechanics. |
| Octokit's plugin pattern may require core to know about plugins (`.plugin()` registration)                                                                                              | Pattern may violate constraint 3 and need to be excluded               | Verify dependency direction before adopting; if Octokit violates constraints, document it as an anti-pattern for our use case                                                                 |
| No studied library may exactly match our "async data from core → sync builder" scenario                                                                                                 | The recommended pattern may be a hybrid not seen in any single library | Propose a composite pattern that combines the best elements, with explicit rationale for each design choice                                                                                   |
| The "right" pattern may be subjective — different team members may prefer different API shapes                                                                                          | Recommendation may be contested in PR review                           | Provide multiple viable options with objective tradeoff analysis, not just one recommendation. Let Plan 06 make the final decision with full evidence.                                        |
| CSAPI currently uses `Pick<OgcApiCollectionInfo, 'id' \| 'title' \| 'links'>` — if the recommendation changes the constructor to accept the full endpoint, migration effort may be high | Significant refactoring of `CSAPIQueryBuilder`                         | Document migration effort for each pattern; if the constructor already accepts a narrow type, prefer patterns that preserve this narrow coupling                                              |
| Some libraries may have changed their API patterns between major versions                                                                                                               | Outdated case study                                                    | Verify the current version of each library; note the version studied                                                                                                                          |

---

## 10. Research Status Checklist

- [ ] Phase 1: Deep Dive Case Studies — Not Started
- [ ] Phase 2: Pattern Classification and Comparison — Not Started
- [ ] Phase 3: Application to CSAPI Use Case — Not Started
- [ ] Phase 4: Type Sharing Analysis — Not Started
- [ ] Phase 5: Synthesis and Documentation — Not Started
- [ ] Deliverable document created
- [ ] Cross-references updated in Plans 05 and 06

**Start Date:** —
**Completion Date:** —
**Actual Time:** —
