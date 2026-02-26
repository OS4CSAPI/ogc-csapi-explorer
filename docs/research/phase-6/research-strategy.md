# Phase 6 Research Strategy: Upstream Acceptance Refactoring

**Version:** 2.0
**Date:** 2026-02-23
**Context:** Maintainer feedback on PR #136 requires architectural changes before CSAPI can be accepted upstream
**Branch:** `phase-6`
**Related:** [Work Assessment and Strategy](../../planning/phase-6/work-assessment-and-strategy.md)
**Previous Version:** [v1 (archived)](archive/research-strategy-v1.md)

---

## Research Philosophy

**Research-First Approach:** Complete all research plans in order before implementing changes. Each plan builds understanding needed for subsequent plans. Do not write code until research is complete and synthesized into an implementation plan.

**External-Knowledge-First Pattern:** Before making any design decision, gather authoritative external knowledge (industry case studies, proven library patterns, specification references). This is the same methodology used in the testing research phase, where external research plans (Sections 3, 8, 9, 32) preceded every internal design synthesis.

**Success Criteria:** After completing this research, we can answer:

1. Exactly how does the upstream build system produce dist artifacts, and how do we add a second entry point?
2. How did EDR integrate with `endpoint.ts`, and why is that pattern unacceptable for CSAPI at this scale?
3. How do proven TypeScript libraries solve sub-module composition, and what patterns apply to our constraints?
4. What adapter/decoupling patterns work in TypeScript's structural type system for extracting a tightly-coupled module?
5. What is the correct architecture to let CSAPI consume `OgcApiEndpoint` without violating any boundary condition?
6. What Prettier/ESLint configuration rules apply, and what changes will they force on our code?
7. What is the exact file-level changelist needed, and what is the correct commit sequence for a clean rebase?

---

## Boundary Conditions (Non-Negotiable)

These are hard constraints from jahow's review of PR #136. They are **not design options** — they are boundary conditions that every research plan must respect. No research question should explore patterns that violate these rules.

### jahow's Four Rules

1. **No CSAPI in root exports:** Nothing from `src/ogc-api/csapi/` shall appear in the root `index.ts`
2. **Separate entry point:** CSAPI must be importable via `@camptocamp/ogc-client/csapi`
3. **No outward imports:** Nothing outside `src/ogc-api/csapi/` should import from the CSAPI module
4. **One-way dependency:** The core module must not depend on CSAPI code. Dependency direction is strictly CSAPI → core, never core → CSAPI

### What These Constraints Close Off

These patterns are **excluded from research scope** — do not study or propose them:

- **Plugin/mixin patterns** where the host module imports the plugin (violates rule 4)
- **Decorator or monkey-patching patterns** where CSAPI adds methods to `OgcApiEndpoint` (violates rules 3 and 4)
- **Shared barrel exports** that re-export CSAPI from root (violates rule 1)
- **`endpoint.csapi()` remaining on the endpoint class** with an import from CSAPI code (violates rule 4)

### What Remains Open for Design

These are the genuine design decisions our research must inform:

- **Consumer API shape:** `new CSAPIClient(endpoint)` vs `CSAPIClient.fromEndpoint(endpoint)` vs `createCSAPIClient({baseUrl, conformance})`
- **Coupling level:** Accept `OgcApiEndpoint` as concrete class vs interface/type vs extracted data primitives
- **`hasConnectedSystems` placement:** Stays on endpoint (if it only checks conformance URIs without importing CSAPI) vs moves to CSAPI module as standalone function
- **`csapiCollections` placement:** Same question as above
- **Shared type references:** Does CSAPI import types like `OgcApiCollectionInfo` from the core module's public API?

### Additional Constraint: CI Compliance

5. **All CI checks must pass:** Prettier formatting, TypeScript type checking, ESLint linting, browser tests, Node.js tests

### Implementation Scope Principle

> **Research broadly, implement minimally.**
>
> jahow issued two concrete requirements. Our research explores industry best practices, build system mechanics, and architectural patterns to ensure we make the _best_ design choices to meet those requirements. However, the implementation must deliver _only_ what jahow requires — no additional work inspired by research findings that exceeds the acceptance criteria.
>
> Rules 3 and 4 above are reasonable inferences from jahow's two bullet points, but they are _our_ inferences, not his explicit words. If during implementation we discover that a pragmatic solution (e.g., a clean `import type` from core) would simplify the architecture, we should consider asking jahow rather than dogmatically enforcing inferred constraints.
>
> jahow also said _"unless we find a better way to handle tree-shaking"_ — this alternative should be explored in Plans 01/03. If modern ESM tree-shaking already prevents CSAPI from entering consumer bundles, that may be a simpler path jahow explicitly said he'd accept.
>
> See: [Scope Alignment Review Notes](research-plans/scope-alignment-review-notes.md)

---

## Research Plans Overview

### Plan 01: Upstream Build System and Entry Point Analysis

> **Type:** Internal analysis | **Depends on:** None

**Objective:** Understand how `ogc-client` builds, bundles, and exposes its public API so we can add a `./csapi` entry point correctly.

**Why First:** Everything else depends on knowing whether the build system supports multiple entry points out of the box, or if we need config changes. This determines the shape of every subsequent decision.

**Key Questions:**

- How does `package.json` `"exports"` map to dist output?
- What does esbuild do with the `find ./src -name "*.ts"` command? Does it produce per-file output or a single bundle?
- How does `vite build` (node config) handle entry points?
- How does `vite build` (worker config) handle entry points?
- What does `build:browser` output look like in `dist/`?
- How does `vite-plugin-dts` generate `.d.ts` files — does it follow the same export structure?
- What changes to `package.json` `"exports"` are needed for `"./csapi"`?
- Does tree-shaking work automatically if we just add exports, or is the separate entry point strictly necessary?

**Boundary scoping:** The entry point _must_ be `"./csapi"` mapping to CSAPI module code only. Do not explore shared or merged entry point configurations.

**Sources:**

- `package.json` (scripts, exports, main, browser, types fields)
- `vite.node-config.js`, `vite.worker-config.js`
- `tsconfig.json` (paths, outDir, declaration settings)
- esbuild documentation for `--outdir` multi-file output
- `dist/` output structure (build locally and inspect)

**Deliverable:** Complete build pipeline analysis with a proven `package.json` `"exports"` configuration for `"./csapi"`

---

### Plan 02: EDR Integration Pattern Analysis

> **Type:** Internal analysis | **Depends on:** None

**Objective:** Understand exactly how EDR (PR #114) integrated with `endpoint.ts`, `info.ts`, and `index.ts`, and why jahow is requesting a different approach for CSAPI.

**Why Second:** EDR is the pattern we followed. Understanding where it succeeded and where it doesn't scale helps us design the CSAPI alternative. jahow himself pointed to PR #114 as a reference in issue #118.

**Key Questions:**

- What imports does `endpoint.ts` have from `src/ogc-api/edr/`?
- What imports does `info.ts` have from EDR?
- What does `index.ts` export from EDR?
- How many lines of EDR code exist in total vs CSAPI?
- Is EDR included in the root bundle? If so, why is that acceptable for EDR but not CSAPI?
- Did jahow explicitly approve EDR being in the root bundle, or was it just small enough to not matter?
- What is the exact boundary between "small enough to include" and "needs its own entry point"?
- Could EDR eventually move to the same pattern we're building for CSAPI?

**Boundary scoping:** EDR's integration pattern is a reference for _what CSAPI must NOT do_. Research the pattern to understand why it's disallowed at CSAPI's scale, not to replicate it.

**Sources:**

- `src/ogc-api/endpoint.ts` (EDR-related imports and methods)
- `src/ogc-api/info.ts` (EDR conformance checks)
- `src/index.ts` (EDR exports)
- `src/ogc-api/edr/` (full module)
- PR #114 diff and review comments
- jahow's comment on PR #136

**Deliverable:** Side-by-side comparison of EDR vs CSAPI integration patterns, with analysis of why the approaches must differ and what we can still learn from EDR

---

### Plan 03: Separate Entry Point Design Patterns

> **Type:** External research (build/packaging mechanics) | **Depends on:** 01

**Objective:** Research how other TypeScript/JavaScript libraries implement sub-path exports (`package/submodule`) and determine the best pattern for `@camptocamp/ogc-client/csapi`.

**Why Third:** After understanding the build system (Plan 01) and the EDR precedent (Plan 02), we need to research proven patterns before designing our own.

**Key Questions:**

- How do popular libraries implement sub-path exports (e.g., `@angular/core/testing`, `rxjs/operators`, `lodash-es/chunk`)?
- What pattern works with esbuild's per-file output?
- Do we need a separate barrel file (`src/ogc-api/csapi/index.ts`) or can we point directly to specific files?
- How should TypeScript declaration files be structured for sub-path exports?
- What are the Node.js `"exports"` field best practices for conditional exports (types, import, require, browser)?
- How do consumers' bundlers (Vite, webpack, esbuild, Rollup) resolve sub-path exports?
- What happens if a consumer imports from `@camptocamp/ogc-client` and `@camptocamp/ogc-client/csapi` — are there duplicate module issues?

**Boundary scoping:** Only research patterns where the sub-module is a **one-way dependent** of the host package (CSAPI depends on core, never reverse). Exclude patterns where sub-modules register themselves with the host.

**Sources:**

- Node.js documentation on package exports
- TypeScript handbook on module resolution with `"exports"`
- Popular library examples (Angular, RxJS, date-fns, AWS SDK v3)
- Vite and webpack documentation on sub-path resolution
- esbuild documentation on external packages and entry points

**Deliverable:** Recommended entry point configuration with package.json changes, barrel file structure, and consumer usage examples

---

### Plan 04: TypeScript Sub-Module API Design Patterns (Industry Case Studies)

> **Type:** External research (industry case studies) | **Depends on:** None

**Objective:** Study how proven TypeScript libraries design the consumer-facing API for sub-modules that depend on a core module, to inform the CSAPI consumer API shape.

**Why Fourth:** This is the most visible design decision — what developers actually type when they use CSAPI. Without studying industry precedent, we'd design from instinct. This plan mirrors Section 3 (TypeScript Testing Best Practices) from the testing research phase.

**Key Questions (all scoped to one-way dependency patterns only):**

- How does `@aws-sdk/lib-storage` consume `@aws-sdk/client-s3`? Does the sub-module accept the client instance, a config object, or primitives?
- How does `@octokit/plugin-rest-endpoint-methods` compose with `@octokit/core`? What does the consumer API look like?
- How does `@angular/cdk/testing` relate to `@angular/core`? Does it import concrete classes or interfaces?
- How do `date-fns`, `lodash-es`, or `rxjs/operators` expose stateless utility APIs vs stateful module APIs?
- How does `zod`'s ecosystem (`zod-to-json-schema`, `@anatine/zod-openapi`) depend on zod — concrete class or interface?
- Across these examples, what is the dominant pattern: factory function, static method, constructor injection, or standalone functions?
- How do these libraries share types between core and sub-module without circular dependencies?
- How do these libraries handle the case where the sub-module needs data that the core module provides asynchronously?

**Boundary scoping:** Only study patterns where:

- The sub-module depends on the core (never reverse) — matching constraint 4
- The sub-module is imported via a separate path — matching constraint 2
- The core module has no knowledge of the sub-module's existence — matching constraint 3

**Excluded patterns:** Plugin registration, mixin injection, decorator/monkey-patching, host-imports-plugin architectures.

**Sources:**

- AWS SDK v3 source code and documentation (multi-package monorepo with sub-module composition)
- Octokit source code (plugin architecture with core dependency)
- Angular CDK source code (sub-path exports with core dependency)
- RxJS, date-fns, lodash-es (stateless utility sub-modules)
- zod ecosystem packages (extension packages depending on core)

**Deliverable:** Pattern catalog of consumer API shapes from 5+ proven libraries, with analysis of which patterns satisfy our boundary conditions and which don't

---

### Plan 05: Module Decoupling Patterns in TypeScript (Architectural Patterns)

> **Type:** External research (architectural patterns) | **Depends on:** None

**Objective:** Research adapter patterns, dependency inversion, and module extraction techniques specifically in TypeScript's structural type system, to inform the endpoint decoupling architecture.

**Why Fifth:** Plan 06 requires us to design the decoupling architecture. TypeScript's structural typing makes adapter patterns different from Java/C# where they originated. Without studying TypeScript-specific approaches, we'd apply textbook patterns that may not translate well.

**Key Questions (all scoped to our extraction scenario):**

- What does the adapter pattern look like in TypeScript? Concrete examples, not just UML diagrams
- How does dependency inversion work with TypeScript's structural typing? (Duck-typed interfaces as implicit contracts vs explicit `interface` declarations)
- What are the tradeoffs between coupling levels that satisfy our constraints?
  - Accept `OgcApiEndpoint` concrete class (tight but simple)
  - Accept `OgcApiEndpointLike` explicit interface (medium coupling)
  - Accept `{baseUrl: string, conformance: string[], collections: ...}` data record (loose)
  - Accept individual function parameters (loosest, most verbose)
- How do TypeScript projects define module boundaries? (barrel files, explicit public APIs, `@internal` tags)
- Are there documented case studies of extracting a tightly-coupled module into a separately-importable sub-module _within the same package_? (This is exactly our situation)
- How loose is "loose enough" for a module that lives in the same repo as its dependency?

**Boundary scoping:** All patterns must result in:

- CSAPI importing from core (never reverse) — constraint 4
- No CSAPI types/code appearing in core's module graph — constraint 3
- A clean module boundary where core can be built/tested without CSAPI — constraints 1, 3, 4

**Excluded patterns:** Circular dependency patterns, shared mutable state, service locator patterns, runtime dependency injection containers.

**Sources:**

- TypeScript handbook (structural typing, module resolution)
- Adapter and facade pattern references with TypeScript examples
- Real-world TypeScript library refactoring case studies (blog posts, conference talks, GitHub issues documenting module extractions)
- Martin Fowler's refactoring catalog (Extract Module, Replace Dependency with Interface) applied to TypeScript

**Deliverable:** Decision matrix of coupling levels (concrete class → interface → data record → parameters) with tradeoffs analysis specific to our boundary conditions, plus TypeScript code examples for each level

---

### Plan 06: Endpoint Decoupling Architecture (Design Synthesis)

> **Type:** Design synthesis | **Depends on:** 02, 03, 04, 05

**Objective:** Synthesize all prior research into the concrete architecture for decoupling CSAPI from `endpoint.ts`.

**Why Sixth:** This is the critical design plan — every consequential decision lives here. It is now informed by five prior plans: build system mechanics (01), EDR precedent (02), entry point patterns (03), industry API patterns (04), and TypeScript decoupling patterns (05).

**Key Questions (all framed as "given our boundary conditions and prior research findings"):**

- Given the industry patterns from Plan 04, what consumer API shape best fits our constraints? Factory function, static method, or constructor with endpoint parameter?
- Given the coupling analysis from Plan 05, what level of coupling is optimal? Concrete `OgcApiEndpoint`, an interface, or extracted data primitives?
- What exact data does `CSAPIQueryBuilder` need from the endpoint? (base URL, available resources, resource URLs, conformance classes)
- Which `OgcApiEndpoint` public properties provide that data today?
- Can a factory function extract everything it needs from the endpoint's existing public API, or does `OgcApiEndpoint` need new public members?
- Where does `hasConnectedSystems` live? If it only checks conformance URIs (no CSAPI import), it can stay on endpoint. If it needs CSAPI logic, it must move.
- Where does `csapiCollections` live? Same analysis.
- What happens to the 6 CSAPI tests in `endpoint.spec.ts`? Do they move to CSAPI's test suite?
- How are shared types (like `OgcApiCollectionInfo`) referenced across the module boundary?

**Boundary verification checklist (every design decision must pass all four):**

- [ ] Nothing from CSAPI appears in root `index.ts`
- [ ] CSAPI is importable via `@camptocamp/ogc-client/csapi`
- [ ] Nothing outside `src/ogc-api/csapi/` imports from CSAPI
- [ ] Core module has zero imports from CSAPI code

**Sources:**

- Plan 01 findings (build system capabilities)
- Plan 02 findings (EDR pattern analysis)
- Plan 03 findings (entry point configuration)
- Plan 04 findings (industry API patterns)
- Plan 05 findings (TypeScript decoupling patterns)
- `src/ogc-api/endpoint.ts` (current CSAPI integration)
- `src/ogc-api/csapi/url_builder.ts` (constructor parameters)
- `src/ogc-api/csapi/helpers.ts` (link scanning, resource discovery)
- `src/ogc-api/info.ts` (`checkHasConnectedSystems`)
- `src/ogc-api/endpoint.spec.ts` (CSAPI test block)

**Deliverable:** Complete architecture design with class diagrams, data flow, factory function signatures, before/after code comparison, and boundary condition verification for every design choice

---

### Plan 07: Prettier and ESLint Configuration Analysis

> **Type:** Mechanical analysis | **Depends on:** None

**Objective:** Understand the exact formatting and linting rules that our code must conform to, and identify any linting issues beyond just Prettier.

**Why Seventh:** Formatting is mechanical but we need to understand the rules before applying them, especially since we've never run ESLint against this codebase. There may be lint errors beyond formatting that affect our code.

**Key Questions:**

- What Prettier version and configuration does upstream use? (`.prettierrc.json` rules)
- What ESLint version and plugins are configured? (`eslint.config.js` rules)
- What specific Prettier changes will be applied to our files? (single quotes vs double? trailing commas? line width? semicolons?)
- Are there ESLint rules that may flag our code? (unused imports, import order, naming conventions)
- Does `eslint-plugin-require-extensions` affect our import statements?
- Does `eslint-plugin-import` enforce specific import ordering?
- Will the `typescript-eslint` plugin flag any of our type patterns?
- Should we run Prettier before or after the architectural refactor?

**Sources:**

- `.prettierrc.json` (or `prettier` field in `package.json`)
- `eslint.config.js`
- `package.json` (devDependencies: prettier version, eslint plugins)
- Running `npx prettier --check` and `npx eslint .` locally and reviewing output

**Deliverable:** Complete formatting/linting impact assessment with list of expected changes per file category, and a recommended execution order

---

### Plan 08: File-Level Changelist and Commit Strategy

> **Type:** Implementation synthesis | **Depends on:** 01–07

**Objective:** Produce the exact list of file changes needed, organized into a clean commit sequence for the rebase.

**Why Last:** This is the synthesis of all prior research into a concrete implementation plan. It requires the build config (01), EDR pattern (02), entry point design (03), industry patterns (04), decoupling patterns (05), architecture (06), and formatting rules (07).

**Key Questions:**

- What is the complete list of files to create, modify, move, or delete?
- What is the correct ordering of commits? (Architecture first? Formatting first? Both together?)
- Should we squash the refactoring into the existing 13 commits or add new commits on top?
- How does this affect the rebase from `phase-6` → `clean-pr`?
- Do we need to update any test fixtures?
- Do we need to update the PR description?
- What is the verification checklist before pushing?

**Boundary verification (final gate):**

- [ ] `git grep` confirms no CSAPI imports in `src/index.ts`
- [ ] `git grep` confirms no CSAPI imports in any file outside `src/ogc-api/csapi/`
- [ ] `npm run format:check` passes
- [ ] `npm run typecheck` passes
- [ ] `npm run lint` passes
- [ ] `npm run test:browser` passes
- [ ] `npm run test:node` passes

**Sources:**

- All prior research findings (Plans 01–07)
- Current file inventory on `clean-pr` branch
- The 13-commit structure of the existing PR
- Upstream CI pipeline (`qa.yml`)

**Deliverable:** Numbered file-level changelist with before/after paths, commit message drafts, rebase strategy, and CI verification checklist

---

## Research Execution Order

| #   | Research Plan                              | Type                     | Depends On     | Est. Time |
| --- | ------------------------------------------ | ------------------------ | -------------- | --------- |
| 01  | Build System and Entry Point Analysis      | Internal analysis        | —              | 2–3 hours |
| 02  | EDR Integration Pattern Analysis           | Internal analysis        | —              | 1–2 hours |
| 03  | Separate Entry Point Design Patterns       | External (packaging)     | 01             | 2–3 hours |
| 04  | TypeScript Sub-Module API Design Patterns  | External (industry)      | —              | 2–3 hours |
| 05  | Module Decoupling Patterns in TypeScript   | External (architecture)  | —              | 2–3 hours |
| 06  | Endpoint Decoupling Architecture           | **Design synthesis**     | 02, 03, 04, 05 | 3–4 hours |
| 07  | Prettier and ESLint Configuration Analysis | Mechanical               | —              | 1–2 hours |
| 08  | File-Level Changelist and Commit Strategy  | Implementation synthesis | 01–07          | 2–3 hours |

**Parallel execution opportunities:**

- Plans 01, 02, 04, 05, and 07 have no dependencies — can run in parallel
- Plan 03 depends on 01 only
- Plan 06 depends on 02, 03, 04, 05 — the critical design synthesis
- Plan 08 is the final synthesis — must be last

**Total estimated research time: 16–24 hours**

This research phase can proceed immediately, without waiting for jahow's detailed review (research doesn't change code).

---

## Version History

| Version | Date       | Changes                                                                                                                                                                                                         |
| ------- | ---------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1.0     | 2026-02-23 | Initial 6-plan strategy                                                                                                                                                                                         |
| 2.0     | 2026-02-23 | Added Boundary Conditions section, added Plans 04–05 (external research), renumbered Plans 05–06 to 07–08, scoped all research questions to respect jahow's constraints, added boundary verification checklists |
