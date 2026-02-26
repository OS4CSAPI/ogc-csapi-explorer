# Phase 6 Research Strategy: Upstream Acceptance Refactoring

**Date:** 2026-02-23
**Context:** Maintainer feedback on PR #136 requires architectural changes before CSAPI can be accepted upstream
**Branch:** `phase-6`
**Related:** [Work Assessment and Strategy](../../planning/phase-6/work-assessment-and-strategy.md)

---

## Research Philosophy

**Research-First Approach:** Complete all research plans in order before implementing changes. Each plan builds understanding needed for subsequent plans. Do not write code until research is complete and synthesized into an implementation plan.

**Primary Constraint:** The maintainer's acceptance criteria are:

1. CSAPI must **not** be exported from the root `index.ts`
2. CSAPI must be importable via `@camptocamp/ogc-client/csapi`
3. Nothing outside `src/ogc-api/csapi/` should import from the CSAPI module
4. All existing CI checks must pass (Prettier, TypeScript, ESLint, tests)

**Success Criteria:** After completing this research, we can answer:

1. Exactly how does the upstream build system produce dist artifacts, and how do we add a second entry point?
2. How did EDR integrate with `endpoint.ts`, and why is that pattern unacceptable for CSAPI at this scale?
3. What is the correct factory/adapter pattern to let CSAPI consume `OgcApiEndpoint` without the endpoint importing CSAPI?
4. What Prettier/ESLint configuration rules apply, and what changes will they force on our code?
5. What is the exact file-level changelist needed, and what is the correct commit sequence for a clean rebase?

---

## Research Plans Overview

### Plan 01: Upstream Build System and Entry Point Analysis

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
- Are there existing examples of multi-entry-point packages using similar tooling?
- Does tree-shaking work automatically if we just add exports, or is the separate entry point strictly necessary?

**Sources:**

- `package.json` (scripts, exports, main, browser, types fields)
- `vite.node-config.js`, `vite.worker-config.js`
- `tsconfig.json` (paths, outDir, declaration settings)
- esbuild documentation for `--outdir` multi-file output
- `dist/` output structure (build locally and inspect)

**Deliverable:** Complete build pipeline analysis with a proven `package.json` `"exports"` configuration for `"./csapi"`

---

### Plan 02: EDR Integration Pattern Analysis

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

**Sources:**

- Node.js documentation on package exports
- TypeScript handbook on module resolution with `"exports"`
- Popular library examples (Angular, RxJS, date-fns, AWS SDK v3)
- Vite and webpack documentation on sub-path resolution
- esbuild documentation on external packages and entry points

**Deliverable:** Recommended entry point configuration with package.json changes, barrel file structure, and consumer usage examples

---

### Plan 04: Endpoint Decoupling Architecture

**Objective:** Design the factory/adapter pattern that lets the CSAPI module consume `OgcApiEndpoint` data without `endpoint.ts` importing CSAPI code.

**Why Fourth:** With build system knowledge (01), EDR analysis (02), and entry point patterns (03), we can now design the actual architecture for decoupling.

**Key Questions:**

- What data does `CSAPIQueryBuilder` actually need from the endpoint? (base URL, available resources, resource URLs, conformance classes)
- Which `OgcApiEndpoint` public properties provide that data today?
- Can a factory function (`CSAPIQueryBuilder.fromEndpoint(endpoint, collectionId)`) extract everything it needs from the endpoint's public API?
- Does `OgcApiEndpoint` need any new public methods/properties to support this, or is the existing API sufficient?
- How should `hasConnectedSystems` be exposed — as a standalone function in the CSAPI module that accepts an endpoint?
- How should `csapiCollections` be exposed — same pattern?
- What happens to the endpoint test fixtures and the 6 CSAPI tests in `endpoint.spec.ts`?
- Should the CSAPI module re-export `OgcApiEndpoint` types it depends on, or should consumers import from both paths?
- What's the right level of coupling — should CSAPI depend on `OgcApiEndpoint` as a class, or just on an interface/type describing the data shape?

**Sources:**

- `src/ogc-api/endpoint.ts` (current CSAPI integration: `csapi()`, `hasConnectedSystems`, `csapiCollections`)
- `src/ogc-api/csapi/url_builder.ts` (constructor parameters)
- `src/ogc-api/csapi/helpers.ts` (link scanning, resource discovery)
- `src/ogc-api/info.ts` (`checkHasConnectedSystems`)
- `src/ogc-api/endpoint.spec.ts` (CSAPI test block)
- Dependency inversion and adapter pattern references

**Deliverable:** Complete architecture design with class diagrams, data flow, factory function signatures, and before/after code comparison

---

### Plan 05: Prettier and ESLint Configuration Analysis

**Objective:** Understand the exact formatting and linting rules that our code must conform to, and identify any linting issues beyond just Prettier.

**Why Fifth:** Formatting is mechanical but we need to understand the rules before applying them, especially since we've never run ESLint against this codebase. There may be lint errors beyond formatting that affect our code.

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

### Plan 06: File-Level Changelist and Commit Strategy

**Objective:** Produce the exact list of file changes needed, organized into a clean commit sequence for the rebase.

**Why Sixth (Last):** This is the synthesis of all prior research into a concrete implementation plan. It requires knowing the build config (01), the EDR pattern (02), the entry point design (03), the decoupling architecture (04), and the formatting rules (05).

**Key Questions:**

- What is the complete list of files to create, modify, move, or delete?
- What is the correct ordering of commits? (Architecture first? Formatting first? Both together?)
- Should we squash the refactoring into the existing 13 commits or add new commits on top?
- How does this affect the rebase from `phase-6` → `clean-pr`?
- Do we need to update any test fixtures?
- Do we need to update the PR description?
- What is the verification checklist before pushing?

**Sources:**

- All prior research findings (Plans 01–05)
- Current file inventory on `clean-pr` branch
- The 13-commit structure of the existing PR
- Upstream CI pipeline (`qa.yml`)

**Deliverable:** Numbered file-level changelist with before/after paths, commit message drafts, and a rebase strategy

---

## Research Execution Order

| #   | Research Plan                              | Depends On | Est. Time |
| --- | ------------------------------------------ | ---------- | --------- |
| 01  | Build System and Entry Point Analysis      | —          | 2–3 hours |
| 02  | EDR Integration Pattern Analysis           | —          | 1–2 hours |
| 03  | Separate Entry Point Design Patterns       | 01         | 2–3 hours |
| 04  | Endpoint Decoupling Architecture           | 02, 03     | 3–4 hours |
| 05  | Prettier and ESLint Configuration Analysis | —          | 1–2 hours |
| 06  | File-Level Changelist and Commit Strategy  | 01–05      | 2–3 hours |

**Notes:**

- Plans 01, 02, and 05 have no dependencies and can be executed in parallel
- Plan 03 depends on 01 (build system knowledge needed first)
- Plan 04 depends on 02 and 03 (need EDR analysis + entry point patterns before designing architecture)
- Plan 06 is the synthesis — must be last
- Total estimated research time: **12–18 hours**
- This research phase can proceed immediately, without waiting for jahow's detailed review (research doesn't change code)
