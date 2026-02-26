# Research Plan 01: Upstream Build System and Entry Point Analysis

> **Plan 1 of 8** | **Phase 6 — Upstream Acceptance Refactoring**

---

## Metadata

| Field                  | Value                                                                                               |
| ---------------------- | --------------------------------------------------------------------------------------------------- |
| **Status**             | Not Started                                                                                         |
| **Plan Type**          | Internal analysis                                                                                   |
| **Date Created**       | 2026-02-23                                                                                          |
| **Last Updated**       | 2026-02-23                                                                                          |
| **Estimated Time**     | 2–3 hours                                                                                           |
| **Actual Time**        | —                                                                                                   |
| **Depends On**         | None                                                                                                |
| **Blocks**             | Plan 03 (Separate Entry Point Design Patterns), Plan 08 (File-Level Changelist and Commit Strategy) |
| **Strategy Reference** | [research-strategy.md § Plan 01](../research-strategy.md)                                           |

---

## 1. Research Objective

Produce a complete build pipeline analysis of `ogc-client` that documents exactly how source files are compiled, bundled, and exposed as the package's public API — across all three build stages (`build:browser`, `build:node`, `build:worker`) and the TypeScript declaration generation. The primary output is a proven, tested `package.json` `"exports"` configuration that adds `"./csapi"` as a second entry point, along with the specific build configuration changes (if any) required to support it.

This plan answers the foundational question: **can we add `"./csapi"` with config changes alone, or do we need to modify the build tooling itself?**

---

## 2. Sequencing Rationale

### Why Plan 1?

This is the foundation for every subsequent plan. The build system determines what is physically possible for entry point configuration. Plans 03 (entry point design patterns) and 06 (decoupling architecture) both need to know whether the build system produces per-file output (where adding an export is trivial) or single-bundle output (where a second entry point requires a second build pipeline). If we design an architecture without knowing this, we risk proposing a structure the build system can't produce.

Additionally, this plan reveals whether there are hidden constraints — for example, if `vite-plugin-dts` only generates declarations for files reachable from a single root, adding a second entry point may require changes to the DTS plugin configuration. These constraints shape every downstream decision.

### Dependency Chain

- **Builds on:** Nothing — this is Plan 1, the foundation for all other research.
- **Feeds into:**
  - **Plan 03** (Separate Entry Point Design Patterns): Needs to know what `package.json` `"exports"` configurations the build system can actually produce.
  - **Plan 06** (Endpoint Decoupling Architecture): Needs to know if CSAPI files are already individually compiled (esbuild per-file) or bundled into a single output (Vite).
  - **Plan 08** (File-Level Changelist and Commit Strategy): Needs the exact build config changes to include in the changelist.

---

## 3. Boundary Conditions

### Non-Negotiable Constraints

1. **Separate entry point required (Constraint 2):** The entry point MUST be `"./csapi"` mapping to CSAPI module code only. This is not a design option — jahow explicitly requires `@camptocamp/ogc-client/csapi` as the import path.
2. **No CSAPI in root exports (Constraint 1):** The root `"."` export must NOT include any CSAPI code in its module graph. The `build:browser` esbuild command currently processes `find ./src -name "*.ts"` which includes CSAPI files — we need to determine if this means they're in the root bundle or just individually compiled.
3. **CI must pass (Constraint 5):** Any build config changes must not break existing builds. The `build` script, `typecheck`, and all tests must continue to work.

### Excluded From Scope

- **Consumer API design:** How developers import and use CSAPI is Plan 03 and Plan 06's territory. This plan only covers what the build system _can_ produce, not what the API _should_ look like.
- **Decoupling architecture:** How `endpoint.ts` and CSAPI code are separated is Plan 06. This plan treats the current file structure as-is and asks what the build system does with it.
- **Formatting and linting:** Plan 07 covers Prettier/ESLint. Build output formatting is irrelevant here.
- **Alternative build tools or migration:** We are not evaluating whether to replace esbuild, Vite, or any tooling. We work within the existing build system.

### What Remains Open

- Whether the `build:browser` esbuild per-file output already provides individually-importable CSAPI files in `dist/`, or whether additional configuration is needed
- Whether `vite-plugin-dts` (in `build:worker`) already generates `.d.ts` files for CSAPI or needs a second pass
- Whether `build:node` (Vite SSR, single entry from `src-node/index.ts`) needs a second entry point for CSAPI, or whether Node consumers use the same per-file output as browser consumers
- What the exact `"exports"` field configuration should look like (conditional exports: `types`, `import`, `browser`, `default`)
- Whether a CSAPI barrel file (`src/ogc-api/csapi/index.ts`) is needed as a build entry point, or whether we can point directly to individual files

---

## 4. Research Questions

### Core Questions

1. How does the three-stage build pipeline (`build:browser` → `build:node` → `build:worker`) transform source files into dist output, and what does each stage contribute?
2. Does the `build:browser` esbuild per-file compilation already produce individually-importable CSAPI files in `dist/ogc-api/csapi/`, or are they bundled into a single output?
3. What `package.json` `"exports"` configuration is needed to expose `"./csapi"` alongside `"."` for all consumer environments (browser, Node ESM, TypeScript types)?
4. Does the TypeScript declaration generation (`vite-plugin-dts` and/or `tsc`) already produce `.d.ts` files for CSAPI, or does it need configuration changes?
5. Can the `"./csapi"` entry point be added with configuration changes only (package.json + possibly vite configs), or are source-level changes required (e.g., creating a barrel file)?

### Detailed Questions

#### Build Pipeline Architecture (8 questions)

1. What does the `build:browser` esbuild command (`esbuild $(find ./src -name "*.ts" -type f -not -path '*worker/index.ts' -not -path '*.spec.ts') --outdir=./dist --platform=neutral --format=esm --sourcemap`) actually produce? Is it one file per source file, or a single bundle?
2. What is the directory structure of `dist/` after `build:browser` completes? Specifically, do `dist/ogc-api/csapi/url_builder.js`, `dist/ogc-api/csapi/model.js`, `dist/ogc-api/csapi/helpers.js`, etc. exist as individual files?
3. What does `build:node` (`vite build --config vite.node-config.js`) produce? The config shows `input: 'src-node/index.ts'` and `output: { entryFileNames: 'dist-node.js' }` — does this single-file bundle include CSAPI code via the re-export chain `src-node/index.ts → src/index.ts → src/ogc-api/csapi/*`?
4. What does `build:worker` (`vite build --config vite.worker-config.js`) produce? The config shows `entry: 'src/worker/index.ts'` — does the worker bundle include CSAPI code?
5. In what order do the three build stages run, and does `emptyOutDir: false` on Vite configs mean they layer outputs into the same `dist/` directory?
6. Does the `build:browser` esbuild step resolve and inline imports, or does it preserve import statements pointing to sibling files in `dist/`?
7. What role does the `--platform=neutral` flag play? Does it affect how CSAPI files are compiled?
8. Are there any build-time exclusions (e.g., `.spec.ts` files are excluded from esbuild — are there others)?

#### Package.json Exports Configuration (7 questions)

9. What is the current `"exports"` field structure, and what does each condition (`types`, `import`, `browser`, `default`) resolve to?
10. If we add `"./csapi": { ... }` to `"exports"`, what paths should `types`, `import`, `browser`, and `default` point to?
11. Does the existing `"main": "./dist/dist-node.js"` and `"browser": "./dist/index.js"` need to be updated, or do the `"exports"` conditions take precedence?
12. Do we need legacy fields (`"main"`, `"browser"`, `"types"`) for the CSAPI sub-path, or is `"exports"` sufficient for all supported environments?
13. Does Node.js resolve `"./csapi"` correctly when `"type": "module"` is set and the `"exports"` field is present?
14. What happens if a consumer's bundler doesn't support the `"exports"` field — do we need a fallback?
15. Does the `"files": ["dist/", "src/"]` field in package.json already include CSAPI dist output, or does it need updating?

#### TypeScript Declaration Generation (6 questions)

16. The `vite-plugin-dts` plugin in `vite.worker-config.js` is configured with `include: ['./src/**/*']` — does this generate `.d.ts` files for all source files including CSAPI, or only files reachable from the worker entry point?
17. After a full build, do `dist/ogc-api/csapi/url_builder.d.ts`, `dist/ogc-api/csapi/model.d.ts`, etc. exist?
18. Does `tsconfig.json` with `"declaration": true` and `"declarationMap": true` contribute to declaration generation during the build, or is `vite-plugin-dts` the sole declaration generator?
19. If CSAPI needs its own barrel file (`src/ogc-api/csapi/index.ts`), does `vite-plugin-dts` automatically generate `dist/ogc-api/csapi/index.d.ts`?
20. Does the `"exports"` field's `"types"` condition for `"./csapi"` need to point to a single `.d.ts` file, or can it point to a directory?
21. Does TypeScript's `moduleResolution: "node"` (in tsconfig) correctly resolve `@camptocamp/ogc-client/csapi` when `"exports"` includes `"./csapi"` with a `"types"` condition?

#### CSAPI Barrel File and Entry Point (5 questions)

22. Does `src/ogc-api/csapi/` currently have an `index.ts` barrel file, or would one need to be created?
23. If a barrel file is needed, what should it export? (All public types and classes from `url_builder.ts`, `model.ts`, `helpers.ts`, `command-routing.ts`?)
24. What currently imports from `src/ogc-api/csapi/` in the codebase? (To understand what the barrel file's public API needs to cover)
25. If we create `src/ogc-api/csapi/index.ts`, does the `build:browser` esbuild command automatically pick it up (since it processes `find ./src -name "*.ts"`)?
26. For the `build:node` stage, does `src-node/index.ts` re-export from `src/index.ts` which re-exports CSAPI? If so, after we remove CSAPI from `src/index.ts`, does `build:node` output naturally exclude CSAPI?

#### Impact on Existing Build (5 questions)

27. After removing CSAPI exports from `src/index.ts`, will the `build:browser` esbuild command still compile CSAPI `.ts` files (since it uses `find ./src -name "*.ts"`, not the import graph from `src/index.ts`)?
28. Will the `build:node` Vite SSR bundle (`dist-node.js`) shrink after CSAPI is removed from the import chain? Is there a measurable size difference?
29. Does removing CSAPI from `src/index.ts` affect tree-shaking for consumers who use bundlers? (They would import from `@camptocamp/ogc-client/csapi` separately)
30. Does the `build:worker` stage need any changes for the CSAPI separation, or is it completely unaffected (since `src/worker/index.ts` likely doesn't import CSAPI)?
31. Will `npm run typecheck` (`tsc --noEmit`) still pass after the changes, given that CSAPI files remain in `"include": ["./src/**/*"]` in tsconfig?

**Total: 31 detailed questions**

---

## 5. Sources

### Primary Sources (In Workspace)

| Source                | Path                               | What to Extract                                                                                              |
| --------------------- | ---------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| Package configuration | `package.json`                     | `exports`, `main`, `browser`, `types`, `files`, `scripts` (build commands), dependency versions              |
| Browser build config  | (inline in `package.json` scripts) | esbuild command flags: `--outdir`, `--platform`, `--format`, file glob pattern                               |
| Node build config     | `vite.node-config.js`              | Rollup input, output config, `emptyOutDir`, SSR settings                                                     |
| Worker build config   | `vite.worker-config.js`            | Entry point, `vite-plugin-dts` config (`include`, `exclude`), lib settings                                   |
| TypeScript config     | `tsconfig.json`                    | `outDir`, `declaration`, `declarationMap`, `include` patterns                                                |
| Root barrel file      | `src/index.ts`                     | Current CSAPI exports (lines ~46–80) — what needs to be removed                                              |
| Node entry point      | `src-node/index.ts`                | Re-export pattern from `src/index.ts`                                                                        |
| CSAPI module files    | `src/ogc-api/csapi/`               | File inventory: `url_builder.ts`, `model.ts`, `helpers.ts`, `command-routing.ts`, `formats/`, `integration/` |
| Worker entry point    | `src/worker/index.ts`              | Whether it imports CSAPI code                                                                                |

### External Sources

| Source                      | URL/Reference                                                       | What to Extract                                                                    |
| --------------------------- | ------------------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| esbuild documentation       | https://esbuild.github.io/api/#outdir                               | Per-file output behavior, `--outdir` vs `--bundle`, `--platform=neutral` semantics |
| Node.js package exports     | https://nodejs.org/api/packages.html#exports                        | Conditional exports syntax, sub-path exports, `"types"` condition                  |
| Vite library mode docs      | https://vite.dev/guide/build.html#library-mode                      | How `build.lib.entry` works, multiple entry points                                 |
| vite-plugin-dts docs        | https://github.com/qmhc/vite-plugin-dts                             | `include`/`exclude` behavior, how declarations are generated                       |
| TypeScript moduleResolution | https://www.typescriptlang.org/docs/handbook/modules/reference.html | How `"exports"` with `"types"` condition is resolved by TypeScript                 |

### Prior Research Findings

| Finding | Path | What to Use                              |
| ------- | ---- | ---------------------------------------- |
| None    | —    | This is Plan 1 — no prior findings exist |

---

## 6. Research Methodology

### Phase 1: Build Output Inspection (~45 minutes)

**Objective:** Run the full build locally and inspect the resulting `dist/` directory to understand exactly what each build stage produces.

**Tasks:**

1. Run `npm run build` (full build: `build:worker` → `build:node` → `build:browser`)
2. List the complete `dist/` directory tree and document every file and directory
3. Identify which files come from which build stage by running each stage individually:
   - `rm -rf dist && npm run build:worker` → list `dist/`
   - Continue with `npm run build:node` (no clean) → list `dist/` to see additions
   - Continue with `npm run build:browser` (no clean) → list `dist/` to see additions
4. Inspect `dist/ogc-api/csapi/` specifically — do individual `.js` files exist? Do `.d.ts` files exist? What about `.js.map` source maps?
5. Inspect `dist/dist-node.js` — does it contain CSAPI code inlined, or does it import from sibling files?
6. Inspect `dist/index.js` if it exists — what does the browser entry point look like?
7. Check file sizes to understand the CSAPI footprint in each output

**Output:** Complete `dist/` directory tree with annotations showing which build stage produced each file, plus the content structure of key output files.

### Phase 2: Build Configuration Analysis (~30 minutes)

**Objective:** Read and document every build configuration file, understanding each option's effect.

**Tasks:**

1. Analyze the `build:browser` esbuild command flag by flag — what does each flag do and how does it affect CSAPI files?
2. Analyze `vite.node-config.js` — trace the SSR build from `src-node/index.ts` through to `dist-node.js`
3. Analyze `vite.worker-config.js` — document the `vite-plugin-dts` configuration and its `include` pattern
4. Analyze `tsconfig.json` — document how `declaration`, `declarationMap`, and `include` affect `.d.ts` generation
5. Document the relationship between the three configs — what shared assumptions do they make about the `dist/` layout?

**Output:** Annotated configuration analysis showing exactly how each build stage transforms source files to dist output.

### Phase 3: Exports Configuration Research (~30 minutes)

**Objective:** Determine the correct `package.json` `"exports"` configuration for adding `"./csapi"`.

**Tasks:**

1. Read Node.js documentation on sub-path exports with conditional exports
2. Read TypeScript documentation on how `"types"` condition in `"exports"` works with `moduleResolution`
3. Study how esbuild's per-file output maps to sub-path exports (do we point to individual files or a barrel?)
4. Draft candidate `"exports"` configurations for `"./csapi"`
5. Determine whether a CSAPI barrel file (`src/ogc-api/csapi/index.ts`) is necessary or optional
6. Determine whether legacy fields (`"main"`, `"browser"`, `"types"`) need updates for the sub-path

**Output:** 2–3 candidate `"exports"` configurations with pros/cons for each.

### Phase 4: Impact Analysis and Validation (~30 minutes)

**Objective:** Verify that the proposed changes don't break existing builds or consumer patterns.

**Tasks:**

1. Simulate removing CSAPI from `src/index.ts` — would the build still compile CSAPI files? (Answer: yes, esbuild uses file glob, not import graph)
2. Check whether `npm run typecheck` would still pass with CSAPI files present but not exported from root
3. Determine if `build:node` output (`dist-node.js`) would automatically exclude CSAPI after it's removed from the import chain
4. Determine if `build:worker` is affected at all by CSAPI separation
5. Document the complete list of build config files that need changes vs. those that don't

**Output:** Impact assessment matrix showing each build stage, whether it's affected, and what changes (if any) are needed.

### Phase 5: Synthesis and Documentation (~15 minutes)

**Objective:** Consolidate all phase outputs into the deliverable document.

**Tasks:**

1. Synthesize findings from Phases 1–4
2. Verify all 31 research questions are answered
3. Validate findings against boundary conditions (Constraints 1, 2, 5)
4. Write deliverable document
5. Cross-reference with Plans 03, 06, 08 to note what information they'll need from this plan

**Output:** Completed findings report at `docs/research/phase-6/findings/01-build-system-entry-point-analysis.md`

---

## 7. Success Criteria

This research is complete when:

- [ ] All 31 detailed research questions have specific, evidenced answers
- [ ] Findings respect all boundary conditions listed in Section 3
- [ ] The complete `dist/` directory tree is documented (full build output)
- [ ] Each build stage's contribution to `dist/` is individually identified
- [ ] The role of `vite-plugin-dts` in generating CSAPI `.d.ts` files is confirmed or refuted
- [ ] At least one proven `"exports"` configuration for `"./csapi"` is documented with all four conditions (`types`, `import`, `browser`, `default`)
- [ ] The question "config changes only, or source changes too?" is definitively answered
- [ ] Impact on each existing build stage is documented (affected/unaffected + what changes)
- [ ] Deliverable document is complete and follows the findings report template
- [ ] Findings are cross-referenced with Plans 03, 06, and 08

---

## 8. Deliverable

**Title:** Build System and Entry Point Analysis: How to Add `"./csapi"` to ogc-client

**Location:** `docs/research/phase-6/findings/01-build-system-entry-point-analysis.md`

**Required Sections:** (per findings report template)

1. Executive Summary — key findings about what the build system produces and whether config-only changes suffice
2. Build Pipeline Architecture — what each of the three stages does, with `dist/` directory tree
3. Package.json Exports Configuration — the recommended `"exports"` structure with `"./csapi"`
4. TypeScript Declaration Generation — how `.d.ts` files are produced and what changes are needed
5. CSAPI Barrel File Analysis — whether `src/ogc-api/csapi/index.ts` is needed and what it should contain
6. Impact on Existing Build — stage-by-stage impact assessment
7. Key Takeaways — numbered list of critical findings
8. Impact on Implementation — specific config changes needed and what Plans 03, 06, 08 should consume
9. Open Questions — anything unresolved that feeds into later plans

---

## 9. Risks and Mitigation

| Risk                                                                                      | Impact                                                                  | Mitigation                                                                                                                                          |
| ----------------------------------------------------------------------------------------- | ----------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| esbuild per-file output doesn't preserve directory structure for CSAPI files              | `"./csapi"` can't point to correct dist paths                           | Run the build and inspect `dist/` before designing the exports config (Phase 1 task)                                                                |
| `vite-plugin-dts` only generates declarations for files reachable from worker entry point | No `.d.ts` files for CSAPI in `dist/`                                   | Check `dist/` for CSAPI `.d.ts` files; if missing, research `vite-plugin-dts` `include` config or alternative DTS generation                        |
| `build:node` SSR bundle inlines all code, making CSAPI inseparable for Node consumers     | Node consumers can't import CSAPI separately from the core              | Determine if Node consumers should use the per-file esbuild output instead of the SSR bundle; may need a different `"import"` target in `"exports"` |
| TypeScript `moduleResolution: "node"` doesn't resolve `"exports"` sub-paths               | Consumers get type errors when importing `@camptocamp/ogc-client/csapi` | Research TypeScript 5.x `"exports"` support; may need `moduleResolution: "bundler"` or `"node16"` recommendation in docs                            |
| Removing CSAPI from `src/index.ts` breaks the `build:node` output in unexpected ways      | Build fails or produces incorrect output                                | Test the removal locally before documenting; validate with `npm run build && npm run typecheck`                                                     |

---

## 10. Research Status Checklist

- [ ] Phase 1: Build Output Inspection — Not Started
- [ ] Phase 2: Build Configuration Analysis — Not Started
- [ ] Phase 3: Exports Configuration Research — Not Started
- [ ] Phase 4: Impact Analysis and Validation — Not Started
- [ ] Phase 5: Synthesis and Documentation — Not Started
- [ ] Deliverable document created
- [ ] Cross-references updated in Plans 03, 06, 08

**Start Date:** —
**Completion Date:** —
**Actual Time:** —
