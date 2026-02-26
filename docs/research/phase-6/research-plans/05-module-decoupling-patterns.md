# Research Plan 05: Module Decoupling Patterns in TypeScript (Architectural Patterns)

> **Plan 5 of 8** | **Phase 6 — Upstream Acceptance Refactoring**

---

## Metadata

| Field                  | Value                                                     |
| ---------------------- | --------------------------------------------------------- |
| **Status**             | Not Started                                               |
| **Plan Type**          | External research (architectural patterns)                |
| **Date Created**       | 2026-02-23                                                |
| **Last Updated**       | 2026-02-23                                                |
| **Estimated Time**     | 2–3 hours                                                 |
| **Actual Time**        | —                                                         |
| **Depends On**         | None                                                      |
| **Blocks**             | Plan 06 (Endpoint Decoupling Architecture)                |
| **Strategy Reference** | [research-strategy.md § Plan 05](../research-strategy.md) |

---

## 1. Research Objective

Produce a decision matrix of coupling levels — concrete class, explicit interface, data record, and individual parameters — with tradeoff analysis specific to our boundary conditions, plus TypeScript code examples for each level. This plan investigates adapter patterns, dependency inversion, module extraction techniques, and module boundary definition strategies as they apply within TypeScript's structural type system, to directly inform the CSAPI-from-endpoint decoupling architecture in Plan 06.

The key output is a **ranked recommendation** of coupling levels, answering: "Given that `CSAPIQueryBuilder` currently accepts `Pick<OgcApiCollectionInfo, 'id' | 'title' | 'links'>` and an optional `Map<string, string>`, and that TypeScript uses structural typing, what is the optimal abstraction level for the CSAPI module boundary?"

This plan focuses on the **internal architecture** (how the module boundary is structured, how types flow, how dependency inversion works in TypeScript), complementing Plan 04's focus on the **external consumer API** (what developers type).

---

## 2. Sequencing Rationale

### Why Plan 5?

Plan 06 (Endpoint Decoupling Architecture) must design the concrete module boundary between core `endpoint.ts` and `csapi/`. That design requires understanding two things: what API consumers should type (Plan 04) and how the internal boundary should be structured (this plan). Without studying how TypeScript's structural type system affects adapter patterns, we'd apply textbook dependency inversion from Java/C# — nominal typing patterns that don't translate directly to TypeScript.

This is particularly important because our codebase already uses structural typing in a critical way: `CSAPIQueryBuilder` accepts `Pick<OgcApiCollectionInfo, 'id' | 'title' | 'links'>`, not the full interface. This is an implicit adapter — TypeScript's structural typing means any object with those three properties satisfies the contract, without needing an explicit interface declaration. Understanding the implications of this existing pattern is essential before designing the decoupled architecture.

### Dependency Chain

- **Builds on:** Nothing directly — this is independent external research. However, the codebase analysis of current coupling points (the two CSAPI imports in `endpoint.ts`, the type dependencies in `csapi/model.ts`, and the `scanCsapiLinks` function) provides the real-world context for evaluating patterns.
- **Feeds into:**
  - **Plan 06** (Endpoint Decoupling Architecture): Needs the coupling level recommendation and type-sharing strategy. Must know whether to accept `OgcApiEndpoint` (concrete), an interface, or extracted data. Without this, Plan 06 would choose a coupling level without understanding the structural typing implications.
  - **Plan 08** (File-Level Changelist): Indirectly — the chosen coupling level determines which files need adapter layers, which types need extraction, and what the barrel file exports.

---

## 3. Boundary Conditions

### Non-Negotiable Constraints

1. **One-way dependency (Constraint 4):** All patterns studied must result in CSAPI importing from core, never the reverse. The adapter/facade/interface must be defined on the CSAPI side or in a shared types location — never in core referencing CSAPI. This is the strongest constraint: core must be completely unaware of CSAPI's existence.
2. **No outward imports (Constraint 3):** Nothing outside `src/ogc-api/csapi/` imports from the CSAPI module. Any adapter interface or facade that core needs to reference is excluded — the boundary must be invisible to core. The decoupling mechanism must work without core providing any explicit hook, slot, or interface for CSAPI.
3. **Core builds/tests independently (Constraints 1, 3, 4):** After decoupling, removing the entire `csapi/` directory must leave core fully functional with zero type errors, zero test failures, and zero import resolution errors. This is the litmus test for every proposed pattern.
4. **Separate entry point (Constraint 2):** The decoupled module is imported via `@camptocamp/ogc-client/csapi`, not from root. The internal architecture must support this separation — types used at the boundary must be importable from both sides without creating a barrel that re-exports CSAPI from root.

### Excluded From Scope

- **Consumer API shape decisions (factory vs constructor vs static method):** Plan 04 covers what developers type. This plan covers the internal architecture that makes any consumer API work.
- **Package.json `"exports"` configuration:** Plan 03 covers the mechanical entry point setup. This plan focuses on the source-level module boundary design.
- **Plugin registration, mixin injection, decorator patterns:** Excluded per strategy boundary conditions. These require core to know about the sub-module (violates constraints 3 and 4).
- **Circular dependency patterns:** Not applicable — dependency direction is strictly one-way.
- **Shared mutable state patterns:** Not applicable — no global state flows between core and CSAPI.
- **Service locator / dependency injection containers:** Over-engineered for a library that's consumed as a package, not a framework. Also would require core to register services (violates constraint 4).
- **Runtime type checking or reflection:** TypeScript structural typing operates at compile time. Patterns requiring runtime type introspection are out of scope.
- **Build system or bundler configuration:** Plan 01 and Plan 03 cover build mechanics. This plan focuses on the source-level architecture.

### What Remains Open

- Whether CSAPI should accept `OgcApiEndpoint` as a concrete class parameter (tight coupling, simplest consumer API, but creates direct dependency on the class)
- Whether CSAPI should define its own interface (e.g., `OgcApiEndpointLike`) that `OgcApiEndpoint` satisfies structurally (medium coupling — TypeScript's duck typing means no explicit `implements` needed)
- Whether CSAPI should accept a data record like `{baseUrl: string, conformance: string[], collectionLinks: Array<{rel: string, href: string}>}` (loose coupling, most verbose, but zero type dependency on core)
- Whether CSAPI should accept individual primitive parameters (loosest coupling, most migration effort)
- Whether `Pick<>` utility types on core interfaces count as a form of interface dependency that violates the spirit of constraint 3 (currently: `Pick<OgcApiCollectionInfo, 'id' | 'title' | 'links'>` is used — is this acceptable?)
- Whether shared types like `OgcApiCollectionInfo` and `OgcApiDocumentLink` should be imported from core's public API as `import type` (type-only import, no runtime dependency) or re-declared in CSAPI
- How `EndpointError` should be handled — CSAPI currently imports it from `../../shared/errors.js`. Should it continue to do so, or declare its own error class?
- Where the `scanCsapiLinks` function belongs after decoupling — it's currently in `csapi/helpers.ts` but imported by `endpoint.ts` (the violation). Should it be duplicated, moved, or replaced by a generic link scanner in core?

---

## 4. Research Questions

### Core Questions

1. How does TypeScript's structural type system affect adapter and dependency inversion patterns compared to nominal type systems (Java, C#)?
2. What are the concrete coupling levels available when a TypeScript sub-module depends on a core module, and what are the tradeoffs of each?
3. How do TypeScript projects define and enforce module boundaries within a single package?
4. What is the recommended approach for extracting a tightly-coupled module into a separately-importable sub-module _within the same package_ in TypeScript?
5. How should shared types (interfaces used by both core and sub-module) be managed to maintain one-way dependency flow?
6. What is the role of `import type` in maintaining clean module boundaries, and what are its limitations?

### Detailed Questions

#### Structural Typing and Adapter Patterns (7 questions)

1. In TypeScript, when Module B accepts `Pick<ModuleA.Foo, 'x' | 'y'>`, does Module B have a compile-time dependency on Module A? What about after erasure — is there a runtime dependency?
2. If Module B defines its own interface `FooLike { x: string; y: number }` that is structurally compatible with Module A's `Foo`, can Module A instances be passed to Module B without any import? Does this eliminate the compile-time dependency?
3. What is the TypeScript-idiomatic way to define an adapter: (a) explicit interface in the sub-module, (b) `Pick<>` on the core type, (c) inline type literal in function signature, or (d) completely re-declared standalone type?
4. How does the adapter pattern differ in TypeScript vs. Java/C#? In Java, the adapter must explicitly implement an interface. In TypeScript, structural compatibility is sufficient — what are the practical implications for our use case?
5. Does TypeScript's structural typing make explicit adapter classes/interfaces unnecessary for our scenario? If `CSAPIQueryBuilder` only needs `{id: string, title: string, links: Array<{rel?: string, href?: string}>}`, any object matching that shape works — is an explicit interface still valuable?
6. What is the cost of abandoning `Pick<OgcApiCollectionInfo, 'id' | 'title' | 'links'>` (which imports `OgcApiCollectionInfo` from core) in favor of an inline structural type `{id: string, title: string, links: any}` (which imports nothing)? What do we lose in terms of type safety, refactoring safety, and documentation?
7. How do TypeScript projects handle the "interface drift" problem — where the sub-module's structural type was derived from the core type but the core type changes? Is there a recommended way to maintain alignment without a direct import?

#### Dependency Inversion in TypeScript (6 questions)

8. What does dependency inversion (DIP) look like in TypeScript without a DI container? Provide concrete examples of how a sub-module defines an abstraction that the core satisfies, without the core importing the sub-module's abstraction.
9. In nominal type systems, DIP requires the core to `implement SubModule.IFoo`. In TypeScript's structural type system, the core doesn't need to reference the sub-module at all — it just needs to have a compatible shape. How does this change the pattern? Is explicit DIP even necessary?
10. For our specific case: `endpoint.ts` currently imports `CSAPIQueryBuilder` and `scanCsapiLinks`. What does inverting this dependency look like? The endpoint currently _creates_ the builder — after inversion, who creates it?
11. Is there a standard TypeScript pattern for "the core provides data, the sub-module consumes it, and neither imports the other's code"? (Not dependency injection — more like "data handoff at the boundary")
12. How does the "Hollywood Principle" (don't call us, we'll call you) apply to our scenario? Currently the endpoint calls `new CSAPIQueryBuilder(...)`. After decoupling, should the consumer be responsible for getting endpoint data and passing it to CSAPI?
13. What are the tradeoffs between "sub-module accepts core instance" (sub-module calls core methods) vs. "sub-module accepts extracted data" (consumer extracts data, passes to sub-module)? Which produces a cleaner module boundary?

#### Coupling Level Analysis (8 questions)

14. **Level 1 — Concrete class:** If CSAPI accepts `OgcApiEndpoint` as a parameter, what are the coupling implications? The sub-module depends on the entire class, including all its methods, properties, and transitive dependencies. Is this acceptable for a module in the same package?
15. **Level 2 — Explicit interface:** If CSAPI defines `interface OgcApiEndpointLike { getCollectionDocument(id: string): Promise<OgcApiDocument>; conformanceClasses: Promise<string[]>; root: Promise<OgcApiDocument> }`, what are the coupling implications? The core class satisfies this structurally without any modification — but CSAPI still imports core types (`OgcApiDocument`).
16. **Level 3 — Data record:** If CSAPI accepts `{ collectionDoc: { id: string, title: string, links: Array<{rel?: string, href?: string}> }, rootLinks: Array<{rel?: string, href?: string}>, conformance: string[] }`, what are the coupling implications? Zero type imports from core — but the consumer must extract and assemble the data.
17. **Level 4 — Individual parameters:** If CSAPI accepts `(collectionId: string, collectionLinks: Array<{...}>, resourceUrls: Map<string, string>)`, what are the coupling implications? Most decoupled, but most verbose consumer API.
18. For each coupling level, what happens when `OgcApiEndpoint` adds, removes, or renames a property? How much does CSAPI need to change?
19. For each coupling level, how discoverable is the CSAPI API? Can IDE autocompletion lead a developer from the endpoint to CSAPI?
20. For each coupling level, how testable is CSAPI in isolation? Can CSAPI unit tests create the required input without instantiating `OgcApiEndpoint`?
21. What coupling level does our current codebase actually use? `CSAPIQueryBuilder` takes `Pick<OgcApiCollectionInfo, 'id' | 'title' | 'links'>` + `Map<string, string>` — is this Level 3 (data record) with a type import, or something between Level 2 and Level 3?

#### Module Boundary Definition (6 questions)

22. How do TypeScript libraries define module boundaries within a single package? Are barrel files (`index.ts`) the standard, or are there other patterns (explicit export lists, `@internal` JSDoc tags, `package.json` `"exports"`)?
23. What is the purpose of a barrel file in the context of a sub-path export? Does `src/ogc-api/csapi/index.ts` serve the same role as `src/index.ts` but for the `./csapi` entry point?
24. Should the CSAPI barrel file re-export everything, or should it curate a public API? (Currently `src/index.ts` re-exports ~170 lines of CSAPI symbols — should the `csapi/index.ts` barrel mirror this, expand it, or curate differently?)
25. How should internal-only CSAPI types (used within CSAPI but not exposed to consumers) be handled? Are private modules within `csapi/` sufficient, or should there be an explicit public/private distinction?
26. After decoupling, should CSAPI expose `scanCsapiLinks` as a public utility? It's currently used by both `endpoint.ts` and `url_builder.ts`. Options: (a) keep in CSAPI, duplicate in core, (b) move to shared utils, (c) inline the logic in endpoint's `extractRootResourceUrls`, (d) expose from CSAPI barrel and accept the outward import (violates constraint 3).
27. How do TypeScript projects handle the "shared utility" problem — a function needed by both an extracted module and the core? What is the recommended placement (core utils, shared package, duplicated, or re-implemented)?

#### Module Extraction Case Studies (5 questions)

28. Are there documented case studies of extracting a tightly-coupled TypeScript module into a separately-importable sub-module _within the same package_? (Not a separate npm package — a sub-path export.)
29. What migration patterns are recommended when extracting a module? (Strangler fig, branch-by-abstraction, feature flags, one-shot extraction)
30. How does one verify that the extraction is complete — that no residual coupling remains? (Import graphs, static analysis tools, manual grep, TypeScript project references)
31. What are common mistakes when extracting modules in TypeScript? (Forgetting type-only imports, leaving transitive dependencies, barrel file circular references, breaking tree-shaking)
32. How does tree-shaking interact with module boundaries? If CSAPI exports many symbols and a consumer only imports one, does the bundler eliminate the rest? Does the coupling level affect tree-shaking effectiveness?

#### `import type` and Type-Only Dependencies (5 questions)

33. Does `import type { OgcApiCollectionInfo } from '../model.js'` create a runtime dependency? Is it erased during compilation? Does it appear in the JavaScript output?
34. If CSAPI uses `import type` for all core types, does the CSAPI module have a runtime dependency on core? What about a build-time dependency?
35. Can `import type` be used to maintain type safety across the module boundary (catching drift when core types change) without creating a module dependency that violates constraint 3?
36. If CSAPI uses `import type { OgcApiCollectionInfo } from '@camptocamp/ogc-client'` (the package's public API, not a relative path), does this create a circular dependency? How do bundlers handle this?
37. What is the recommended `import type` strategy for a sub-module within the same package: import from relative paths (`../model.js`), from the package public API (`@camptocamp/ogc-client`), or re-declare types locally?

**Total: 37 detailed questions**

---

## 5. Sources

### Primary Sources (In Workspace)

| Source                                  | Path                                                                                                   | What to Extract                                                                                                                                                                    |
| --------------------------------------- | ------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| CSAPIQueryBuilder constructor           | `src/ogc-api/csapi/url_builder.ts` (lines 106–180)                                                     | Current coupling: `Pick<OgcApiCollectionInfo, 'id' \| 'title' \| 'links'>` + `Map<string, string>`. The existing structural typing pattern.                                        |
| CSAPI imports from core                 | `src/ogc-api/csapi/url_builder.ts` (line 1), `csapi/model.ts` (lines 1–2), `csapi/helpers.ts` (line 3) | Complete list of type imports from core: `OgcApiCollectionInfo`, `OgcApiDocumentLink`, `BoundingBox`, `DateTimeParameter`, `CrsCode`, `MimeType`, `EndpointError`                  |
| Endpoint CSAPI imports (the violations) | `src/ogc-api/endpoint.ts` (lines 52–53)                                                                | `import CSAPIQueryBuilder from './csapi/url_builder.js'` and `import { scanCsapiLinks } from './csapi/helpers.js'` — these two imports must be eliminated                          |
| Endpoint `csapi()` method               | `src/ogc-api/endpoint.ts` (lines 385–413)                                                              | Current data flow: `getCollectionDocument()` → `extractRootResourceUrls()` → `new CSAPIQueryBuilder(doc, urls)`. What data the endpoint currently provides.                        |
| Endpoint `extractRootResourceUrls()`    | `src/ogc-api/endpoint.ts` (lines 431–436)                                                              | Uses `scanCsapiLinks(rootDoc.links)` — the second constraint violation. Simple delegation that could be inlined or moved.                                                          |
| Core model types                        | `src/ogc-api/model.ts` (lines 85–155)                                                                  | `OgcApiCollectionInfo` (full interface, 30+ properties), `OgcApiDocumentLink` (4 properties), `OgcApiDocument` (generic document type)                                             |
| CSAPI model types                       | `src/ogc-api/csapi/model.ts`                                                                           | All types exported by CSAPI — what crosses the module boundary                                                                                                                     |
| `scanCsapiLinks` function               | `src/ogc-api/csapi/helpers.ts` (lines 129–170)                                                         | The shared utility problem: imported by both `endpoint.ts` and `url_builder.ts`. Accepts `Array<{rel?: string, href?: string}>` — already uses structural typing in its parameter. |
| `checkHasConnectedSystems`              | `src/ogc-api/info.ts` (lines 112–120)                                                                  | Confirms: no CSAPI imports. Uses only conformance URIs. Candidate to stay on endpoint.                                                                                             |
| Root exports (current)                  | `src/index.ts` (lines 45–252)                                                                          | ~170 lines of CSAPI re-exports that must move to the `./csapi` barrel                                                                                                              |
| EDR pattern (for comparison)            | `src/ogc-api/endpoint.ts` (line 51), `src/ogc-api/edr/url_builder.ts`                                  | How EDR decouples from endpoint — direct `import` from core, no reverse. Same structural pattern we need.                                                                          |

### External Sources

| Source                                     | URL/Reference                                                        | What to Extract                                                                            |
| ------------------------------------------ | -------------------------------------------------------------------- | ------------------------------------------------------------------------------------------ |
| TypeScript Handbook — Structural Typing    | https://www.typescriptlang.org/docs/handbook/type-compatibility.html | How structural compatibility works, implications for adapter patterns                      |
| TypeScript Handbook — Module Resolution    | https://www.typescriptlang.org/docs/handbook/modules/theory.html     | How `import type` works, module boundary semantics                                         |
| TypeScript Handbook — Utility Types        | https://www.typescriptlang.org/docs/handbook/utility-types.html      | `Pick<>`, `Partial<>`, `Required<>` — utility types as implicit adapters                   |
| Martin Fowler — Refactoring Catalog        | https://refactoring.guru/refactoring/catalog                         | Extract Module, Replace Dependency with Interface, Move Function — adapted to TypeScript   |
| Adapter Pattern in TypeScript              | https://refactoring.guru/design-patterns/adapter/typescript/example  | Classic adapter implementation, how to adapt for structural typing                         |
| Facade Pattern in TypeScript               | https://refactoring.guru/design-patterns/facade/typescript/example   | Simplifying complex module interfaces — relevant to the "data record" coupling level       |
| TypeScript Project References              | https://www.typescriptlang.org/docs/handbook/project-references.html | Enforcing module boundaries with separate `tsconfig` per module                            |
| Nx / Turborepo module boundary enforcement | https://nx.dev/concepts/module-boundaries                            | How monorepo tools enforce boundaries — applicable patterns for single-package sub-modules |
| `@internal` tag behavior in TypeScript     | https://www.typescriptlang.org/tsconfig/#stripInternal               | Hiding internal types from public API declarations                                         |
| Node.js subpath exports documentation      | https://nodejs.org/api/packages.html#subpath-exports                 | Canonical reference for `"exports"` field behavior — context for barrel file design        |

### Prior Research Findings

| Finding                           | Path                                                                    | What to Use                                                                                                      |
| --------------------------------- | ----------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| Plan 02 findings (when available) | `docs/research/phase-6/findings/02-edr-integration-pattern-analysis.md` | EDR decoupling pattern as baseline comparison — EDR is already cleanly decoupled                                 |
| Plan 04 findings (when available) | `docs/research/phase-6/findings/04-sub-module-api-design-patterns.md`   | Industry consumer API patterns — this plan complements Plan 04's external perspective with internal architecture |

---

## 6. Research Methodology

### Phase 1: TypeScript Structural Typing Deep Dive (~40 minutes)

**Objective:** Establish how TypeScript's structural type system changes classical adapter and dependency inversion patterns compared to nominal languages (Java, C#).

**Tasks:**

1. Review TypeScript handbook on structural typing — document how type compatibility works without explicit `implements` or `extends` declarations
2. Create concrete TypeScript examples demonstrating: (a) implicit structural compatibility (Module B accepts any object matching shape), (b) explicit interface adaptation (Module B defines `FooLike`), (c) `Pick<>` utility types as partial adapters, (d) inline type literals eliminating imports
3. Analyze `import type` erasure behavior — confirm that `import type { X } from 'module'` creates no runtime dependency, and document exactly what appears in the compiled JavaScript output
4. Compare TypeScript adapter patterns with Java/C# equivalents — document specific differences that affect our design (no need for `implements`, duck typing, structural assignability rules)
5. Document the "interface drift" problem: if CSAPI defines `{id: string, title: string, links: any}` independent of core's `OgcApiCollectionInfo`, what happens when core renames `title` to `name`? How can we detect this without a direct import?
6. Analyze TypeScript project references as a mechanism for enforcing module boundaries — determine if they're applicable to our single-`tsconfig` project or only for multi-project setups

**Output:** TypeScript structural typing reference document with code examples for each adaptation pattern, and a clear statement of how structural typing changes the adapter pattern for our use case

### Phase 2: Coupling Level Analysis (~50 minutes)

**Objective:** Analyze all four coupling levels (concrete class, explicit interface, data record, individual parameters) with tradeoffs specific to our boundary conditions and existing codebase.

**Tasks:**

1. **Level 1 — Concrete class:** Draft code example where CSAPI accepts `OgcApiEndpoint`. Analyze: (a) compile-time coupling (CSAPI imports the class), (b) runtime coupling (CSAPI calls endpoint methods), (c) testability (CSAPI tests must instantiate or mock `OgcApiEndpoint`), (d) constraint compliance (does the endpoint import CSAPI? — if CSAPI only receives endpoint as a parameter, core still doesn't import CSAPI ✓), (e) migration effort from current code
2. **Level 2 — Explicit interface:** Draft code example where CSAPI defines `interface CSAPIEndpoint { getCollectionDocument(id: string): Promise<...>; conformance: Promise<string[]>; root: Promise<...> }`. Analyze: (a) does `OgcApiEndpoint` satisfy this structurally? (b) does CSAPI still import core types for the return types (`OgcApiDocument`)? (c) testability (easy to create mock implementing the interface), (d) interface maintenance burden, (e) constraint compliance
3. **Level 3 — Data record:** Draft code example where CSAPI accepts `{ collectionDoc: { id: string, title: string, links: Array<{rel?: string, href?: string}> }, rootLinks: Array<{rel?: string, href?: string}> }`. Analyze: (a) zero type imports from core (full independence), (b) consumer burden (who assembles the record?), (c) loss of type safety (inline literals vs named types), (d) current state analysis (CSAPIQueryBuilder already uses this level via `Pick<>`)
4. **Level 4 — Individual parameters:** Draft code example where CSAPI builder takes `(collectionId: string, collectionLinks: Array<...>, resourceUrls: Map<string, string>)`. Analyze: (a) maximum decoupling, (b) verbose consumer API, (c) current state (already close to this — constructor takes two params)
5. For each level, verify against all four boundary conditions with explicit ✓/✗ markings
6. For each level, assess: refactoring safety, IDE discoverability, test ergonomics, migration effort, tree-shaking impact
7. Build comparison matrix with all dimensions

**Output:** 4 coded examples + comparison matrix across 10+ dimensions

### Phase 3: Module Boundary Patterns (~30 minutes)

**Objective:** Research how TypeScript projects define and enforce module boundaries within a single package, with focus on barrel files, `@internal` tags, and the "shared utility" problem.

**Tasks:**

1. Research barrel file patterns for sub-path exports — document the standard `index.ts` barrel file structure, what to export (all symbols vs curated public API), and how it relates to `package.json` `"exports"`
2. Analyze the `scanCsapiLinks` shared utility problem: (a) document all callers (endpoint.ts line 435, url_builder.ts via `extractAvailableResources`), (b) document all options (duplicate, move to shared, inline, expose from CSAPI barrel), (c) recommend placement based on the function's actual dependencies (it only uses `CSAPIResourceTypes` from `./model.js`)
3. Research `@internal` tag and `stripInternal` tsconfig option — can we mark CSAPI-internal types that shouldn't appear in the public `.d.ts` files?
4. Research how TypeScript projects verify module boundary integrity: import graphs, ESLint rules (e.g., `eslint-plugin-import`), `package.json` `"exports"`, Nx boundary tags
5. Document the recommended barrel file structure for `src/ogc-api/csapi/index.ts` — what it should export (CSAPIQueryBuilder, model types, format utilities) and what it should NOT export (internal helpers, private types)

**Output:** Module boundary pattern catalog with specific recommendation for CSAPI barrel file design and `scanCsapiLinks` placement

### Phase 4: Module Extraction Patterns (~20 minutes)

**Objective:** Research documented strategies for extracting a tightly-coupled module into a separately-importable sub-module within the same TypeScript package.

**Tasks:**

1. Search for case studies of TypeScript module extraction within a single package (blog posts, conference talks, GitHub issues/PRs documenting module splits)
2. Document migration strategies applicable to our scenario: (a) one-shot extraction (change all files in one commit), (b) strangler fig (gradual replacement), (c) branch-by-abstraction (introduce interface, then swap implementation)
3. Determine if intermediate steps are needed — can we go directly from "endpoint imports CSAPI" to "endpoint has zero CSAPI imports", or do we need an adapter layer in between?
4. Document verification techniques: (a) `git grep` for residual imports, (b) TypeScript compilation without CSAPI in tsconfig, (c) dependency graph visualization, (d) ESLint import boundary rules
5. Identify common extraction mistakes: circular barrel imports, forgetting `import type`, transitive dependencies via re-exports, breaking tree-shaking with barrel files

**Output:** Extraction pattern recommendations with verification checklist

### Phase 5: Synthesis and Documentation (~30 minutes)

**Objective:** Consolidate all phase outputs into the deliverable document.

**Tasks:**

1. Synthesize findings from Phases 1–4 into the findings report structure
2. Produce the final coupling level recommendation with complete rationale
3. Verify all 37 research questions are answered with specific, evidenced answers
4. Validate every finding against all four boundary conditions
5. Produce the `scanCsapiLinks` placement recommendation with justification
6. Produce the `import type` strategy recommendation
7. Cross-reference with Plan 04 (consumer API shape) and Plan 06 (what it needs from this plan)
8. Write the deliverable document

**Output:** Completed findings report at `docs/research/phase-6/findings/05-module-decoupling-patterns.md`

---

## 7. Success Criteria

This research is complete when:

- [ ] All 37 detailed research questions have specific, evidenced answers
- [ ] Findings respect all boundary conditions listed in Section 3
- [ ] All four coupling levels are documented with concrete TypeScript code examples
- [ ] Each coupling level has explicit ✓/✗ verification against all four boundary conditions
- [ ] A comparison matrix is produced covering: constraint compliance, type safety, refactoring safety, IDE discoverability, testability, consumer ergonomics, migration effort, tree-shaking impact
- [ ] The role of TypeScript structural typing in the adapter pattern is clearly documented with examples showing how it differs from nominal typing approaches
- [ ] `import type` behavior is documented with a specific recommendation for the CSAPI module boundary
- [ ] The `scanCsapiLinks` shared utility problem is analyzed with a specific placement recommendation
- [ ] The barrel file structure for `src/ogc-api/csapi/index.ts` is recommended
- [ ] Module extraction verification techniques are documented (how to confirm no residual coupling)
- [ ] A clear coupling level recommendation is made, citing structural typing properties and constraint compliance
- [ ] Deliverable document is complete and follows the findings report template
- [ ] Findings are cross-referenced with Plans 04 and 06

---

## 8. Deliverable

**Title:** Module Decoupling Patterns in TypeScript: Coupling Level Analysis and Recommended Architecture for CSAPI Extraction

**Location:** `docs/research/phase-6/findings/05-module-decoupling-patterns.md`

**Required Sections:** (per findings report template)

1. Executive Summary — the recommended coupling level, the key structural typing insight, and the `scanCsapiLinks` resolution
2. TypeScript Structural Typing Analysis — how it changes adapter/DIP patterns vs nominal typing, with code examples
3. Coupling Level Case Studies — 4 levels, each with code example, constraint verification, and multi-dimensional tradeoff analysis
4. Coupling Level Comparison Matrix — tabular comparison across all dimensions
5. Module Boundary Patterns — barrel file design, `@internal` tags, boundary enforcement
6. `scanCsapiLinks` Placement Analysis — options, recommendation, justification
7. `import type` Strategy — when to use type-only imports, recommended pattern for CSAPI
8. Module Extraction Patterns — migration strategies, verification techniques
9. Recommendation — the selected coupling level with full rationale
10. Impact on Implementation — what Plan 06 should consume, what decisions are made vs. deferred
11. Open Questions — anything unresolved that feeds into Plan 06

---

## 9. Risks and Mitigation

| Risk                                                                                                                                                                           | Impact                                                                             | Mitigation                                                                                                                                                                                                |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| TypeScript structural typing may make all coupling levels practically equivalent for our small boundary surface                                                                | Decision matrix may not clearly differentiate levels                               | Focus on second-order tradeoffs: testability, refactoring safety, migration effort. Even if structural typing makes them compile-time equivalent, the developer experience differs.                       |
| `Pick<OgcApiCollectionInfo, 'id' \| 'title' \| 'links'>` creates a compile-time dependency on `OgcApiCollectionInfo` even though the runtime shape is structurally independent | May need to eliminate `Pick<>` in favor of inline types to achieve full decoupling | Determine if `import type` + `Pick<>` is acceptable (no runtime dependency) or if the compile-time dependency violates the spirit of constraint 3. Provide both options.                                  |
| The `scanCsapiLinks` shared utility has no clean placement — it uses CSAPI-specific constants (`CSAPIResourceTypes`) but is needed by core's `extractRootResourceUrls`         | May require code duplication, which is a maintenance risk                          | Analyze all four placement options with honest tradeoffs. Prefer the option that keeps CSAPI self-contained even if it means core loses some convenience.                                                 |
| Module extraction case studies may be sparse — most documented examples involve separate npm packages, not sub-path exports within a single package                            | Limited external evidence for our exact scenario                                   | Extrapolate from multi-package extraction patterns. Our scenario is simpler (same repo, same build, same tsconfig) — patterns that work across packages certainly work within one.                        |
| Recommended coupling level from this plan may conflict with Plan 04's recommended consumer API pattern                                                                         | Plans 05 and 06 may need to reconcile different recommendations                    | This plan produces a coupling level recommendation; Plan 04 produces a consumer API recommendation. Plan 06 is explicitly designed to synthesize both. Flag any obvious conflicts for Plan 06 to resolve. |
| `EndpointError` import from `../../shared/errors.js` may be considered an outward import that violates constraint 3                                                            | Unclear whether `shared/` counts as "core" for constraint purposes                 | Research whether `shared/` is considered part of the core module boundary or a shared utility layer. If shared, the import is fine. If core, CSAPI may need its own error class.                          |

---

## 10. Research Status Checklist

- [ ] Phase 1: TypeScript Structural Typing Deep Dive — Not Started
- [ ] Phase 2: Coupling Level Analysis — Not Started
- [ ] Phase 3: Module Boundary Patterns — Not Started
- [ ] Phase 4: Module Extraction Patterns — Not Started
- [ ] Phase 5: Synthesis and Documentation — Not Started
- [ ] Deliverable document created
- [ ] Cross-references updated in Plans 04 and 06

**Start Date:** —
**Completion Date:** —
**Actual Time:** —
