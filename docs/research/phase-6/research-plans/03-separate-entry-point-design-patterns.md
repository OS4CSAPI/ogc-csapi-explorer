# Research Plan 03: Separate Entry Point Design Patterns

> **Plan 3 of 8** | **Phase 6 — Upstream Acceptance Refactoring**

---

## Metadata

| Field                  | Value                                                                                           |
| ---------------------- | ----------------------------------------------------------------------------------------------- |
| **Status**             | Not Started                                                                                     |
| **Plan Type**          | External research (build/packaging mechanics)                                                   |
| **Date Created**       | 2026-02-23                                                                                      |
| **Last Updated**       | 2026-02-23                                                                                      |
| **Estimated Time**     | 2–3 hours                                                                                       |
| **Actual Time**        | —                                                                                               |
| **Depends On**         | Plan 01 (Upstream Build System and Entry Point Analysis)                                        |
| **Blocks**             | Plan 06 (Endpoint Decoupling Architecture), Plan 08 (File-Level Changelist and Commit Strategy) |
| **Strategy Reference** | [research-strategy.md § Plan 03](../research-strategy.md)                                       |

---

## 1. Research Objective

Produce a comprehensive guide to sub-path export patterns (`package/submodule`) across the JavaScript/TypeScript ecosystem, grounded in how proven libraries actually configure `package.json` `"exports"`, barrel files, TypeScript declarations, and bundler compatibility — then synthesize that knowledge into a concrete, recommended entry point configuration for `@camptocamp/ogc-client/csapi`. The deliverable is a tested `package.json` `"exports"` field, a barrel file design (if needed), consumer usage examples for every environment (browser, Node ESM, TypeScript), and documentation of how major bundlers resolve the sub-path.

This plan bridges the gap between Plan 01 (what the build system _can_ produce) and Plan 06 (what the architecture _should_ look like) by answering: **given our build system's capabilities, what is the proven, ecosystem-standard way to expose a sub-module entry point?**

---

## 2. Sequencing Rationale

### Why Plan 3?

Plan 03 depends on Plan 01 because the entry point configuration must be compatible with what the build system actually produces. Plan 01 answers "what does `dist/` look like?" — Plan 03 answers "given that `dist/` layout, how do we point `"./csapi"` at the right files using patterns that are proven across the ecosystem?"

This plan is external research, not internal analysis. We study how Angular, RxJS, AWS SDK v3, date-fns, and other libraries solve the same problem — sub-path exports where the sub-module depends on the core, shipped inside a single npm package. This is the "External-Knowledge-First Pattern" from the research philosophy: gather authoritative precedent before making our own design decisions.

Plan 02 (EDR pattern analysis) shows us what the _current_ integration looks like and why it fails at CSAPI's scale. Plan 03 shows us what _correct_ sub-path exports look like in the wider ecosystem. Together, they provide the foundation for Plan 06's design synthesis.

### Dependency Chain

- **Builds on:**
  - **Plan 01** (Build System and Entry Point Analysis): Provides the specific `dist/` layout, build system capabilities, candidate `"exports"` configurations, and whether a barrel file is needed. Plan 03 takes Plan 01's mechanical findings and validates/refines them against ecosystem best practices.
- **Feeds into:**
  - **Plan 06** (Endpoint Decoupling Architecture): Needs the final entry point configuration, barrel file structure, and consumer import paths to design the public API surface. Without this, Plan 06 can't determine what consumers actually type.
  - **Plan 08** (File-Level Changelist and Commit Strategy): Needs the exact `package.json` changes, any new barrel files, and any `tsconfig.json` adjustments to include in the changelist.

---

## 3. Boundary Conditions

### Non-Negotiable Constraints

1. **Separate entry point required (Constraint 2):** The sub-path MUST be `"./csapi"`, so consumers write `import { CSAPIQueryBuilder } from '@camptocamp/ogc-client/csapi'`. This is not a design option — jahow explicitly required it. No alternatives (e.g., `"./connected-systems"`, a separate npm package, or a deep path like `"./ogc-api/csapi"`) should be researched.
2. **No CSAPI in root exports (Constraint 1):** The `"."` entry point must not expose CSAPI code. Patterns where a single entry re-exports everything (like `lodash` vs `lodash-es/chunk`) are irrelevant — we need the sub-path pattern specifically.
3. **One-way dependency (Constraint 4):** Only research sub-path patterns where the sub-module depends on the core, never the reverse. Patterns involving plugin registration, bi-directional imports, or host-imports-plugin architectures are excluded.
4. **CI must pass (Constraint 5):** The chosen configuration must not break the existing build pipeline (`build:browser`, `build:node`, `build:worker`), TypeScript type checking, or tests.
5. **Existing tooling only:** The solution must work within the existing build stack (esbuild, Vite, `vite-plugin-dts`, TypeScript 5.x). No new build tools or migration to a monorepo structure.

### Excluded From Scope

- **Consumer API design (class shape, factory functions, method signatures):** Plan 04 (industry case studies) and Plan 06 (design synthesis) determine what the consumer API _looks like_. This plan only determines the _entry point mechanics_ — how the import resolves, not what it contains.
- **Module decoupling architecture:** How `endpoint.ts` is refactored to remove CSAPI imports is Plan 06. This plan assumes the CSAPI code will live under `src/ogc-api/csapi/` and asks how to expose it.
- **EDR integration analysis:** Plan 02 covers why the EDR pattern fails at CSAPI's scale. This plan focuses forward on the correct pattern, not backward on the old one.
- **Multi-package monorepo patterns (e.g., Lerna, Nx workspaces, pnpm workspaces):** Out of scope — we are not changing the package structure. CSAPI remains in the same npm package, exposed via a sub-path export.
- **CommonJS (`require`) support:** The package has `"type": "module"` and no CJS output. The `"exports"` configuration only needs `types`, `import`, `browser`, and `default` conditions. Do not research `"require"` condition patterns.

### What Remains Open

- Whether the `"./csapi"` export should point to a barrel file (`dist/ogc-api/csapi/index.js`) or directly to the main module file (e.g., `dist/ogc-api/csapi/url_builder.js`)
- Whether a CSAPI barrel file (`src/ogc-api/csapi/index.ts`) needs to be created, or whether the per-file esbuild output is sufficient
- Whether the `"./csapi"` export needs a separate `"browser"` condition pointing to a different file than `"import"`, or whether one ESM file serves both
- How TypeScript declarations should be structured — a single `csapi/index.d.ts` barrel, or per-file `.d.ts` with a `"types"` condition pointing to the barrel
- Whether consumers who import from both `@camptocamp/ogc-client` and `@camptocamp/ogc-client/csapi` encounter duplicate module instances or shared type conflicts
- Whether additional `"exports"` sub-paths beside `"./csapi"` are needed (e.g., `"./csapi/formats"` for advanced consumers) or whether a single flat entry suffices
- What `typesVersions` field (if any) is needed for older TypeScript versions that don't fully support `"exports"`

---

## 4. Research Questions

### Core Questions

1. How do proven TypeScript/JavaScript libraries implement sub-path exports within a single npm package, and what `package.json` `"exports"` patterns have they converged on?
2. What barrel file structure is standard for sub-path exports — a single index barrel, direct file pointers, or something else?
3. How should TypeScript declaration files be organized for sub-path exports so that consumers get correct autocompletion and type checking?
4. How do the major consumers' bundlers (Vite, webpack, esbuild, Rollup) and Node.js resolve sub-path exports, and are there compatibility pitfalls?
5. What happens when a consumer imports from both the root entry (`@camptocamp/ogc-client`) and the sub-path (`@camptocamp/ogc-client/csapi`) — are there duplicate module or duplicate type issues?

### Detailed Questions

#### Library Case Studies (8 questions)

1. How does Angular implement sub-path exports (e.g., `@angular/core/testing`, `@angular/cdk/testing`)? What does their `package.json` `"exports"` field look like? Do they use barrel files or direct file pointers?
2. How does RxJS implement `rxjs/operators` and `rxjs/ajax`? Is it a sub-path export in a single package or a separate package? What changed between RxJS 6 (path rewriting) and RxJS 7+ (native exports)?
3. How does AWS SDK v3 expose sub-library packages (e.g., `@aws-sdk/lib-storage` depending on `@aws-sdk/client-s3`)? Are these separate npm packages or sub-path exports within one package? What can we learn from their approach about the single-package vs. multi-package decision?
4. How does `date-fns` expose its sub-paths (e.g., `date-fns/format`, `date-fns/locale/en-US`)? Is it per-function barrel files or per-file exports?
5. How does `zod` structure its package — is it a single entry point, or does it use sub-path exports? Do ecosystem extensions (`zod-to-json-schema`) depend on the public entry or internal paths?
6. For each library studied, what conditions do they include in their `"exports"` field? (`types`, `import`, `require`, `browser`, `default`, `node`, `development`?) Which conditions are standard and which are edge cases?
7. Among the libraries studied, what is the typical number of sub-path exports? (1–2 for focused packages, dozens for utility libraries?) Where does our use case fall?
8. Do any of the studied libraries use `typesVersions` as a fallback for older TypeScript? If so, what does the configuration look like?

#### Package.json Exports Configuration (8 questions)

9. What is the Node.js documentation's recommended structure for conditional sub-path exports in ESM-only packages? Specifically, what conditions are relevant when `"type": "module"` and there is no CJS output?
10. What is the correct ordering of conditions in `"exports"`? Does `"types"` always come first? Does `"browser"` come before or after `"import"`?
11. For our build system (esbuild per-file output in `dist/`), should `"./csapi"` point to `"./dist/ogc-api/csapi/index.js"` (barrel) or `"./dist/ogc-api/csapi/url_builder.js"` (main file)? What are the tradeoffs?
12. Should the `"browser"` and `"import"` conditions point to the same file (both use the per-file esbuild ESM output), or do they need separate targets?
13. Does the `"default"` condition need to point to the Vite SSR bundle (`dist-node.js`), or can it point to the per-file output? Does this depend on whether a CSAPI-specific Node build exists?
14. What is the minimum `"exports"` configuration that works — just `"types"` and `"import"`, or do we need all four conditions (`types`, `import`, `browser`, `default`)?
15. Can we use wildcard/glob sub-path patterns (e.g., `"./csapi/*"`) to expose individual CSAPI modules, or should we restrict to a single `"./csapi"` barrel? What do ecosystem best practices recommend?
16. Does adding `"./csapi"` to `"exports"` require any changes to the `"files"` field in `package.json`? (Currently `"files": ["dist/", "src/"]` — CSAPI dist files are already inside `dist/`.)

#### Barrel File Design (6 questions)

17. Does a CSAPI barrel file (`src/ogc-api/csapi/index.ts`) already exist, or does one need to be created? (Note: `formats/index.ts` exists as a sub-barrel, but is there a top-level CSAPI barrel?)
18. If a barrel file is needed, what should it export? Should it re-export everything from `url_builder.ts`, `model.ts`, `helpers.ts`, `command-routing.ts`, and `formats/index.ts`? Or should it be selective?
19. How do barrel file re-exports interact with tree-shaking? If a consumer imports only `CSAPIQueryBuilder` from `@camptocamp/ogc-client/csapi`, do the format parsers (SensorML, SWE Common) get included in their bundle?
20. Should there be separate barrel files for sub-categories (e.g., `@camptocamp/ogc-client/csapi/formats`) or should one flat barrel at `@camptocamp/ogc-client/csapi` export everything?
21. What is the naming convention for sub-path barrel files in the ecosystem? `index.ts`? A named file matching the package path?
22. How do barrel re-exports affect build output size and compile time? Are there known performance issues with large barrel files in TypeScript?

#### TypeScript Declaration Resolution (7 questions)

23. How does TypeScript resolve types for sub-path exports? Does it use the `"types"` condition in `"exports"`, the `"typesVersions"` field, or the automatic `.d.ts` file next to the `.js` file?
24. What `moduleResolution` setting does a consumer need for `"exports"` `"types"` conditions to work? Does `"node"` (classic) support it, or is `"node16"` / `"bundler"` required?
25. If our `tsconfig.json` uses `"moduleResolution": "node"`, does that affect how our own build generates declarations, or only how consumers resolve them?
26. Does `vite-plugin-dts` (configured with `include: ['./src/**/*']`) already generate a `dist/ogc-api/csapi/index.d.ts` if `src/ogc-api/csapi/index.ts` exists? Or does it only generate declarations for files reachable from the Vite entry point?
27. Do we need a `"typesVersions"` fallback for consumers using older TypeScript or `"moduleResolution": "node"`? What does the fallback look like?
28. If the CSAPI barrel re-exports types from the core module (e.g., `OgcApiCollectionInfo` from `ogc-api/model.ts`), do consumers see those types correctly through the `"./csapi"` entry point, or do they get "cannot find module" errors for transitive type references?
29. Do `.d.ts.map` files (declaration maps, enabled in our `tsconfig.json`) need special handling for sub-path exports?

#### Bundler Compatibility and Runtime Resolution (6 questions)

30. How does Vite resolve sub-path exports when a consumer app uses `import { CSAPIQueryBuilder } from '@camptocamp/ogc-client/csapi'`? Does it use the `"browser"` condition, the `"import"` condition, or something else?
31. How does webpack 5 resolve the same import? Does it respect `package.json` `"exports"`, or does it fall back to file system resolution?
32. How does esbuild (as a consumer-side bundler) resolve sub-path exports? Are there known issues with `"exports"` support?
33. How does Rollup resolve sub-path exports? Does it need `@rollup/plugin-node-resolve` with specific configuration?
34. When a consumer imports from both `@camptocamp/ogc-client` and `@camptocamp/ogc-client/csapi`, do bundlers create two separate module instances, or do they deduplicate shared code? Is there a risk of `OgcApiEndpoint` being loaded twice?
35. Does Node.js (v20+, ESM mode) resolve `@camptocamp/ogc-client/csapi` correctly using the `"exports"` field? Are there edge cases with `--experimental-specifier-resolution` or import maps?

**Total: 35 detailed questions**

---

## 5. Sources

### Primary Sources (In Workspace)

| Source                 | Path                                 | What to Extract                                                                   |
| ---------------------- | ------------------------------------ | --------------------------------------------------------------------------------- |
| Package configuration  | `package.json`                       | Current `"exports"`, `"type"`, `"files"`, `"main"`, `"browser"`, `"types"` fields |
| TypeScript config      | `tsconfig.json`                      | `moduleResolution`, `declaration`, `outDir`, `declarationMap` settings            |
| CSAPI module directory | `src/ogc-api/csapi/`                 | File inventory, check for existing `index.ts` barrel file                         |
| CSAPI formats barrel   | `src/ogc-api/csapi/formats/index.ts` | Existing sub-barrel pattern to follow                                             |
| Root barrel file       | `src/index.ts`                       | Current CSAPI exports to understand what the sub-path barrel must replace         |
| Vite worker config     | `vite.worker-config.js`              | `vite-plugin-dts` `include` config (affects `.d.ts` generation)                   |
| Vite node config       | `vite.node-config.js`                | SSR entry point configuration                                                     |

### External Sources

| Source                                  | URL/Reference                                                                  | What to Extract                                                                            |
| --------------------------------------- | ------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------ |
| Node.js Packages documentation          | https://nodejs.org/api/packages.html#exports                                   | Sub-path exports syntax, conditional exports, pattern exports, condition ordering          |
| Node.js Package entry points            | https://nodejs.org/api/packages.html#package-entry-points                      | Resolution algorithm, `"types"` condition, dual-package hazard                             |
| TypeScript module resolution            | https://www.typescriptlang.org/docs/handbook/modules/reference.html            | How `"exports"` `"types"` condition is resolved; `moduleResolution` settings               |
| TypeScript `typesVersions`              | https://www.typescriptlang.org/docs/handbook/declaration-files/publishing.html | Fallback for older `moduleResolution` settings                                             |
| Angular `package.json`                  | https://github.com/angular/angular (search `@angular/core/package.json`)       | Sub-path exports pattern for `@angular/core/testing`                                       |
| RxJS `package.json`                     | https://github.com/ReactiveX/rxjs (search `package.json`)                      | Sub-path exports for `rxjs/operators`, `rxjs/ajax`                                         |
| AWS SDK v3 structure                    | https://github.com/aws/aws-sdk-js-v3                                           | Multi-package monorepo vs. sub-path approach                                               |
| date-fns `package.json`                 | https://github.com/date-fns/date-fns                                           | Per-function sub-path exports pattern                                                      |
| zod `package.json`                      | https://github.com/colinhacks/zod                                              | Single entry vs. sub-path decision                                                         |
| Vite dependency resolution              | https://vite.dev/guide/dep-pre-bundling.html                                   | How Vite resolves `"exports"` in dev vs. build mode                                        |
| webpack resolve.exports                 | https://webpack.js.org/configuration/resolve/#resolveexportsfields             | webpack 5 `"exports"` support                                                              |
| esbuild package resolution              | https://esbuild.github.io/api/#resolve-extensions                              | esbuild's `"exports"` handling                                                             |
| Rollup `@rollup/plugin-node-resolve`    | https://github.com/rollup/plugins/tree/master/packages/node-resolve            | Sub-path export resolution in Rollup                                                       |
| Andrew Branch: TypeScript exports guide | https://github.com/andrewbranch/example-subpath-exports-ts-compat              | Reference repo for TypeScript + `"exports"` compatibility patterns                         |
| `resolve.exports` library               | https://github.com/lukeed/resolve.exports                                      | Small library implementing `"exports"` resolution — useful for understanding the algorithm |

### Prior Research Findings

| Finding          | Path                                                                     | What to Use                                                                                                                                 |
| ---------------- | ------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------- |
| Plan 01 findings | `docs/research/phase-6/findings/01-build-system-entry-point-analysis.md` | The `dist/` directory layout, candidate `"exports"` configs, `vite-plugin-dts` behavior, whether a barrel file is needed at the build level |

---

## 6. Research Methodology

### Phase 1: Library Case Study Survey (~45 minutes)

**Objective:** Collect and document the `package.json` `"exports"` configurations, barrel file structures, and declaration strategies from 5+ established libraries that use sub-path exports.

**Tasks:**

1. Fetch Angular's `@angular/core` `package.json` — document the `"exports"` field, specifically how `"./testing"` is configured (conditions, file paths, barrel structure)
2. Fetch RxJS `package.json` — document how `rxjs/operators`, `rxjs/ajax`, and other sub-paths are configured; note whether these are sub-path exports or path-mapped separate packages
3. Fetch date-fns `package.json` — document the per-function sub-path pattern (`date-fns/format`, `date-fns/locale/*`); note whether wild-card exports are used
4. Fetch zod `package.json` — check whether zod uses sub-path exports at all or is single-entry; note how the ecosystem (`zod-to-json-schema`) depends on it
5. Fetch at least 1 additional TypeScript library with a sub-path export in a single package (candidates: `msw`, `@trpc/server`, `effect`, `drizzle-orm`, `@tanstack/react-query`)
6. For each library, record: (a) `"exports"` field structure, (b) conditions used, (c) condition ordering, (d) barrel file or direct file pointer, (e) `"typesVersions"` presence, (f) `"type"` field value, (g) whether separate CJS and ESM outputs exist
7. Synthesize into a comparison table with columns: Library | Sub-path Example | Conditions Used | Barrel or Direct | typesVersions | Notes

**Output:** Comparison table of 5+ library sub-path export patterns

### Phase 2: Node.js and TypeScript Specification Research (~30 minutes)

**Objective:** Document the authoritative specification for how Node.js resolves `"exports"` and how TypeScript resolves types from `"exports"`, including edge cases and gotchas.

**Tasks:**

1. Read Node.js `"exports"` documentation — document the resolution algorithm step by step for sub-path exports with conditions
2. Document the correct ordering of conditions in `"exports"` — does `"types"` always come first? Is `"browser"` before or after `"import"`?
3. Read TypeScript's `moduleResolution` documentation — determine which settings (`"node"`, `"node16"`, `"bundler"`, `"nodenext"`) support the `"types"` condition in `"exports"`
4. Document the `"typesVersions"` fallback mechanism — when is it needed, what does a minimal config look like?
5. Research the "dual package hazard" — can a consumer who imports both `@camptocamp/ogc-client` and `@camptocamp/ogc-client/csapi` get two instances of shared types?
6. Determine what `moduleResolution` setting `ogc-client` consumers are likely using — Angular apps use `"bundler"`, Node.js scripts use `"node16"` or `"nodenext"`, older setups use `"node"`

**Output:** Specification-grounded resolution guide covering Node.js, TypeScript, and the dual-package hazard

### Phase 3: Bundler Compatibility Analysis (~30 minutes)

**Objective:** Verify that the sub-path export pattern works correctly across all major consumer bundlers (Vite, webpack, esbuild, Rollup) and bare Node.js.

**Tasks:**

1. Research how Vite resolves sub-path exports — does it use `"browser"` condition in dev mode? Does it pre-bundle sub-path imports differently?
2. Research how webpack 5 resolves sub-path exports — does `resolve.exports` support all conditions? Any known bugs?
3. Research how esbuild (consumer-side) resolves sub-path exports — does it respect `"browser"` vs `"import"` conditions?
4. Research how Rollup resolves sub-path exports — does `@rollup/plugin-node-resolve` need `"exportConditions"` configuration?
5. Test scenario: consumer imports from both `@camptocamp/ogc-client` and `@camptocamp/ogc-client/csapi` — research whether bundlers deduplicate or create separate instances of shared internal modules
6. Document any known compatibility issues or required consumer-side configuration for each bundler

**Output:** Bundler compatibility matrix (Vite, webpack 5, esbuild, Rollup, Node.js ≥ 20) with pass/fail/caveats for each

### Phase 4: Barrel File and Declaration Design (~25 minutes)

**Objective:** Determine the optimal barrel file structure and TypeScript declaration organization for the CSAPI sub-path export, informed by Plan 01 findings and the library survey.

**Tasks:**

1. Review Plan 01 findings — what does the `dist/` layout look like for CSAPI files? Does `vite-plugin-dts` already generate `.d.ts` for them?
2. Check whether `src/ogc-api/csapi/index.ts` already exists as a barrel file, or needs to be created
3. Design the barrel file contents — determine what should be re-exported (CSAPIQueryBuilder, types, format parsers, helpers?) based on what `index.ts` currently exports from CSAPI
4. Evaluate tree-shaking implications — if the barrel re-exports everything, do unused CSAPI modules get eliminated? Research how esbuild and Vite handle barrel file tree-shaking
5. Decide between single flat barrel (`./csapi`) vs. multi-level sub-paths (`./csapi`, `./csapi/formats`) — what do the library case studies recommend for a module with ~170 lines of current root exports?
6. Determine the `.d.ts` pointing strategy — should `"types"` in `"exports"` point to `dist/ogc-api/csapi/index.d.ts`, or to a distinct `.d.ts` barrel?

**Output:** Barrel file design specification with exact file contents and declaration pointing strategy

### Phase 5: Configuration Synthesis (~20 minutes)

**Objective:** Combine all prior phase outputs into a concrete, validated `package.json` `"exports"` configuration with supporting file changes.

**Tasks:**

1. Draft the complete `"exports"` field with both `"."` and `"./csapi"` entries, using the correct conditions and paths
2. Validate the draft against: (a) the library case study patterns, (b) Node.js spec requirements, (c) TypeScript resolution rules, (d) bundler compatibility findings
3. Draft consumer usage examples for each scenario: TypeScript browser app (Vite), TypeScript Node.js script, webpack app, tree-shaking verification
4. Determine whether `"typesVersions"` is needed as a fallback and draft if so
5. Identify any `tsconfig.json` changes needed (e.g., adding `"paths"` for internal resolution, or adjusting declaration output)
6. List all file changes needed: `package.json`, barrel file creation, `tsconfig.json`, any vite config changes

**Output:** Complete configuration spec ready for implementation

### Phase 6: Synthesis and Documentation (~20 minutes)

**Objective:** Consolidate all phase outputs into the deliverable document.

**Tasks:**

1. Synthesize findings from Phases 1–5 into the findings report structure
2. Verify all 35 research questions are answered
3. Validate findings against boundary conditions (Constraints 1, 2, 4, 5)
4. Write the deliverable document
5. Cross-reference with Plan 06 (what it needs from this plan) and Plan 08 (file changes)

**Output:** Completed findings report at `docs/research/phase-6/findings/03-separate-entry-point-design-patterns.md`

---

## 7. Success Criteria

This research is complete when:

- [ ] All 35 detailed research questions have specific, evidenced answers
- [ ] Findings respect all boundary conditions listed in Section 3
- [ ] At least 5 library case studies are documented with their `"exports"` configurations
- [ ] A comparison table of library patterns is produced
- [ ] The Node.js resolution algorithm for sub-path exports is documented step by step
- [ ] TypeScript declaration resolution is documented for `"exports"` with `"types"` condition, including which `moduleResolution` settings support it
- [ ] Bundler compatibility matrix is produced for Vite, webpack 5, esbuild, Rollup, and Node.js ≥ 20
- [ ] A concrete `"exports"` configuration for `"./csapi"` is drafted with all necessary conditions
- [ ] Barrel file design is specified (contents, tree-shaking implications, single vs. multi-level)
- [ ] Consumer usage examples are documented for at least 3 scenarios (Vite app, Node.js script, webpack app)
- [ ] The dual-import scenario (root + sub-path) is analyzed for duplicate module risk
- [ ] Deliverable document is complete and follows the findings report template
- [ ] Findings are cross-referenced with Plans 01, 06, and 08

---

## 8. Deliverable

**Title:** Separate Entry Point Design Patterns: Ecosystem Patterns and Recommended Configuration for `@camptocamp/ogc-client/csapi`

**Location:** `docs/research/phase-6/findings/03-separate-entry-point-design-patterns.md`

**Required Sections:** (per findings report template)

1. Executive Summary — key findings about ecosystem convergence on sub-path export patterns and the recommended configuration
2. Library Case Study Survey — comparison table and detailed notes for each library studied
3. Node.js and TypeScript Resolution — authoritative spec behavior, condition ordering, `"typesVersions"` guidance
4. Bundler Compatibility Matrix — pass/fail/caveats for each major bundler and Node.js
5. Barrel File Design — recommended structure, contents, tree-shaking analysis
6. Recommended `"exports"` Configuration — exact `package.json` changes with inline commentary
7. Consumer Usage Examples — import statements and expected resolution for TypeScript browser, Node.js, and bundler consumers
8. Dual-Import Analysis — risk assessment for consumers importing both root and sub-path
9. Key Takeaways — numbered list of critical findings
10. Impact on Implementation — exact file changes for Plan 08, inputs for Plan 06
11. Open Questions — anything unresolved that feeds into later plans

---

## 9. Risks and Mitigation

| Risk                                                                                                                  | Impact                                                                                     | Mitigation                                                                                                                                                                           |
| --------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Libraries studied may use monorepo multi-package structure rather than sub-path exports within a single package       | Case studies may not be directly applicable to our single-package sub-path scenario        | Distinguish clearly between multi-package patterns (AWS SDK v3) and single-package sub-path patterns (date-fns, Angular CDK); focus on the latter for direct applicability           |
| TypeScript `moduleResolution: "node"` (our current setting) may not resolve `"exports"` `"types"` conditions          | Consumers or our own type checking may fail                                                | Research `"typesVersions"` as a fallback; determine if we need to recommend `"node16"` or `"bundler"` to consumers; check if our own `tsconfig.json` needs updating                  |
| Tree-shaking may not eliminate unused CSAPI format parsers when imported through a barrel file                        | Consumers who only want `CSAPIQueryBuilder` pull in SensorML, SWE Common, etc.             | Research barrel file tree-shaking behavior in esbuild and Vite specifically; consider whether selective barrel exports or side-effects annotation (`"sideEffects": false`) is needed |
| The `"browser"` condition may conflict with `"import"` in some bundlers, causing wrong file resolution                | Consumer app loads Node-specific or browser-specific code incorrectly                      | Research exact condition priority in each bundler; align our condition set with ecosystem consensus from the library survey                                                          |
| Plan 01 findings may not be available when Plan 03 executes (parallel execution allowed for Plans 01, 02, 04, 05, 07) | Barrel file design and `"exports"` paths can't be finalized without knowing `dist/` layout | Draft conditional recommendations ("if per-file output exists at `dist/ogc-api/csapi/`, then X; otherwise Y") and finalize when Plan 01 completes                                    |
| Dual-import scenario creates two module instances of shared code (OgcApiEndpoint loaded twice)                        | Runtime errors, type mismatches, doubled bundle size                                       | Research how bundlers deduplicate within a single package; worst case, document the limitation and warn consumers                                                                    |

---

## 10. Research Status Checklist

- [ ] Phase 1: Library Case Study Survey — Not Started
- [ ] Phase 2: Node.js and TypeScript Specification Research — Not Started
- [ ] Phase 3: Bundler Compatibility Analysis — Not Started
- [ ] Phase 4: Barrel File and Declaration Design — Not Started
- [ ] Phase 5: Configuration Synthesis — Not Started
- [ ] Phase 6: Synthesis and Documentation — Not Started
- [ ] Deliverable document created
- [ ] Cross-references updated in Plans 06 and 08

**Start Date:** —
**Completion Date:** —
**Actual Time:** —
