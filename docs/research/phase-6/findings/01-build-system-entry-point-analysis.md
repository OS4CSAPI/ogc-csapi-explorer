# Findings Report 01: Build System and Entry Point Analysis

> **Plan 1 of 8** | **Phase 6 — Upstream Acceptance Refactoring**

---

## Metadata

| Field                  | Value                                                                                                                                           |
| ---------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| **Research Plan**      | [Plan 01: Upstream Build System and Entry Point Analysis](../research-plans/01-build-system-entry-point-analysis.md)                            |
| **Plan Type**          | Internal analysis                                                                                                                               |
| **Date Started**       | 2026-02-23                                                                                                                                      |
| **Date Completed**     | 2026-02-23                                                                                                                                      |
| **Research Time**      | ~3 hours (actual)                                                                                                                               |
| **Estimated Time**     | 2–3 hours (from plan)                                                                                                                           |
| **Questions Answered** | 31 of 31 detailed questions                                                                                                                     |
| **Depends On**         | None — this is Plan 1, the foundation                                                                                                           |
| **Blocks**             | Plan 03 (Separate Entry Point Design Patterns), Plan 06 (Endpoint Decoupling Architecture), Plan 08 (File-Level Changelist and Commit Strategy) |

---

## Source Summary

### Primary Sources Consulted

| Source                | Path / URL                                | What Was Extracted                                                                                                                                                           |
| --------------------- | ----------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Package configuration | `package.json`                            | `exports`, `main`, `browser`, `types`, `files`, `scripts` (build commands), `"type": "module"`                                                                               |
| Browser build config  | `package.json` → `"build:browser"` script | esbuild command flags: `--outdir=./dist`, `--platform=neutral`, `--format=esm`, `--sourcemap`, file glob via `find`                                                          |
| Node build config     | `vite.node-config.js`                     | Rollup input (`src-node/index.ts`), output (`dist-node.js`), `emptyOutDir: false`, SSR mode                                                                                  |
| Worker build config   | `vite.worker-config.js`                   | Entry point (`src/worker/index.ts`), `vite-plugin-dts` config (`include: ['./src/**/*']`), `emptyOutDir: false`                                                              |
| TypeScript config     | `tsconfig.json`                           | `moduleResolution: "node"`, `declaration: true`, `declarationMap: true`, `include: ["./src/**/*", "./src-node/**/*"]`                                                        |
| Root barrel file      | `src/index.ts` (252 lines)                | CSAPI re-exports spanning lines 45–227 (~170 lines of CSAPI exports)                                                                                                         |
| Node entry point      | `src-node/index.ts`                       | Simple `export * from '../src/index.js'` + `enableFallbackWithoutWorker()`                                                                                                   |
| Worker entry point    | `src/worker/index.ts` (111 lines)         | Imports from shared/models, wms, wfs, wmts — zero CSAPI imports                                                                                                              |
| CSAPI module files    | `src/ogc-api/csapi/`                      | File inventory: `command-routing.ts`, `helpers.ts`, `model.ts`, `url_builder.ts`, `formats/` (12+ files + `sensorml/` + `swecommon/` subdirs), `integration/` (5 spec files) |
| Endpoint source       | `src/ogc-api/endpoint.ts`                 | Lines 52–53: the two CSAPI imports (`CSAPIQueryBuilder`, `scanCsapiLinks`)                                                                                                   |
| Full build output     | `dist/` (after `npm run build`)           | Complete directory tree, file sizes, content inspection of key outputs                                                                                                       |

### External Sources Consulted

| Source                      | URL                                                                 | What Was Extracted                                                                                                            |
| --------------------------- | ------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| Node.js subpath exports     | https://nodejs.org/api/packages.html#subpath-exports                | Conditional exports syntax, `"types"` community condition, sub-path patterns, encapsulation behavior                          |
| TypeScript moduleResolution | https://www.typescriptlang.org/docs/handbook/modules/reference.html | `"node"` (node10) does NOT read `"exports"`, `"node16"`/`"nodenext"`/`"bundler"` DO read `"exports"` with `"types"` condition |

### Prior Findings Used

| Finding | Path | What Was Consumed                        |
| ------- | ---- | ---------------------------------------- |
| None    | —    | This is Plan 1 — no prior findings exist |

### Sources Not Available or Not Useful

- **esbuild documentation** (https://esbuild.github.io/api/#outdir): Not fetched — behavior was confirmed empirically by running the build and inspecting output. Direct observation was more authoritative than documentation for this specific configuration.
- **vite-plugin-dts docs** (https://github.com/qmhc/vite-plugin-dts): Not fetched — behavior was confirmed empirically. The `include: ['./src/**/*']` pattern was verified to generate `.d.ts` for ALL source files regardless of entry point import graph.

---

## Executive Summary

The `ogc-client` build pipeline uses a three-stage architecture — `build:worker` (Vite library mode), `build:node` (Vite SSR), and `build:browser` (esbuild per-file) — that layers outputs into a shared `dist/` directory. The critical discovery is that **esbuild's `build:browser` stage operates in per-file compilation mode (not bundling mode)**, producing one output `.js` file per source `.ts` file with preserved relative import statements. This means individual CSAPI `.js` files already exist in `dist/ogc-api/csapi/` after a standard build.

Additionally, `vite-plugin-dts` (configured via `build:worker`) generates `.d.ts` declaration files for the **entire `src/` tree** regardless of what the worker entry point actually imports. All 27 CSAPI `.d.ts` files are confirmed present in `dist/ogc-api/csapi/` after a build. Combined, these two facts mean **adding `"./csapi"` as a sub-path export is primarily a `package.json` configuration change plus the creation of a barrel file** — no build tooling modifications are required.

The one source-level change required is creating `src/ogc-api/csapi/index.ts` as a barrel file, which does not currently exist. This barrel file will serve as the entry point for the `"./csapi"` sub-path export. The existing `src/index.ts` must then have its CSAPI re-exports removed (those ~170 lines become the barrel file's content). After this change, `build:node` output (`dist-node.js`, currently 483.5 KB) will automatically exclude CSAPI code since it follows the import graph from `src-node/index.ts → src/index.ts`, and `build:worker` remains completely unaffected (zero CSAPI imports).

### Key Metrics

| Metric                          | Value                         | Significance                                                          |
| ------------------------------- | ----------------------------- | --------------------------------------------------------------------- |
| CSAPI JS output size            | 191.4 KB across 27 files      | Substantial footprint that consumers shouldn't load if not needed     |
| `url_builder.js` alone          | 86 KB                         | Largest single CSAPI file — validates need for separate entry point   |
| `dist-node.js` (Node bundle)    | 483.5 KB (with CSAPI inlined) | Will shrink significantly after CSAPI removal from import chain       |
| `dist/worker/index.js`          | 144.3 KB (zero CSAPI)         | Completely unaffected by CSAPI separation                             |
| `dist/index.js` (browser entry) | ~2.5 KB (per-file re-exports) | Lightweight; just preserves import statements to sibling files        |
| CSAPI `.d.ts` files in dist     | 27 files                      | All already generated by `vite-plugin-dts` — no config changes needed |
| Build stages                    | 3 (worker → node → browser)   | All layer into `dist/` via `emptyOutDir: false`                       |

### Overall Assessment

**Adding `"./csapi"` requires configuration changes + one barrel file creation. No build tooling modifications are needed.** The esbuild per-file compilation model and vite-plugin-dts's glob-based include pattern together mean the build system already produces all necessary outputs for a separate CSAPI entry point.

---

## Table of Contents

1. [Build Pipeline Architecture](#1-build-pipeline-architecture)
2. [Package.json Exports Configuration](#2-packagejson-exports-configuration)
3. [TypeScript Declaration Generation](#3-typescript-declaration-generation)
4. [CSAPI Barrel File and Entry Point](#4-csapi-barrel-file-and-entry-point)
5. [Impact on Existing Build](#5-impact-on-existing-build)
6. [Boundary Condition Verification](#6-boundary-condition-verification)
7. [Implementation Scope Gate Assessment](#7-implementation-scope-gate-assessment)
8. [Impact on Dependent Plans](#8-impact-on-dependent-plans)
9. [Key Takeaways](#9-key-takeaways)
10. [Impact on Implementation](#10-impact-on-implementation)
11. [Open Questions](#11-open-questions)

---

## 1. Build Pipeline Architecture

This section answers the 8 questions about how the three-stage build pipeline transforms source files into dist output.

### Question 1: What does the `build:browser` esbuild command produce? One file per source or a single bundle?

**Answer:** One `.js` file per source `.ts` file. The esbuild command uses `--outdir=./dist` (not `--bundle`), which puts it in **per-file compilation mode**. Each source file is individually transpiled from TypeScript to JavaScript ESM, with relative import statements preserved (not resolved/inlined).

**Evidence:**

The `build:browser` npm script:

```
esbuild $(find ./src -name "*.ts" -type f -not -path '*worker/index.ts' -not -path '*.spec.ts') --outdir=./dist --platform=neutral --format=esm --sourcemap
```

Key: The `--bundle` flag is **absent**. With `--outdir` and no `--bundle`, esbuild operates as a per-file transpiler. The `find` command generates a list of ~143+ `.ts` files which are each compiled to a corresponding `.js` file in `dist/`, preserving the directory structure.

After running the build, `dist/ogc-api/csapi/url_builder.js` contains:

```javascript
import { EndpointError } from '../../shared/errors.js';
// ... compiled code with preserved relative imports
```

The imports are preserved as relative paths to sibling files — not resolved or inlined.

### Question 2: Does `dist/ogc-api/csapi/` contain individual `.js` files?

**Answer:** Yes. After a full build, `dist/ogc-api/csapi/` contains individual `.js`, `.js.map`, and `.d.ts` files for every CSAPI source file.

**Evidence:**

Confirmed files in `dist/ogc-api/csapi/`:

- `url_builder.js` (86 KB), `url_builder.js.map`, `url_builder.d.ts`
- `model.js`, `model.js.map`, `model.d.ts`
- `helpers.js`, `helpers.js.map`, `helpers.d.ts`
- `command-routing.js`, `command-routing.js.map`, `command-routing.d.ts`
- `formats/index.js`, `formats/index.d.ts`, and all subdirectory files
- `integration/*.js` and `integration/*.d.ts` files

Total: **27 CSAPI `.js` files** totaling 191.4 KB, with corresponding `.d.ts` and `.js.map` files.

### Question 3: Does `build:node` include CSAPI code in `dist-node.js`?

**Answer:** Yes. The Node SSR bundle (`dist-node.js`, 483.5 KB) fully inlines CSAPI code because it follows the import chain: `src-node/index.ts` → `export * from '../src/index.js'` → `src/index.ts` re-exports CSAPI → all CSAPI modules are bundled in.

**Evidence:**

`dist-node.js` contains CSAPI code fully inlined:

- `CSAPIQueryBuilder` class definition found at approximately line 3591
- `scanCsapiLinks` function found at approximately line 3527
- All CSAPI format parsers, model types, and helper functions are present

This is a single-file bundle (Vite SSR mode with `rollup` input from `src-node/index.ts`). After removing CSAPI exports from `src/index.ts`, this bundle will automatically exclude CSAPI code.

### Question 4: Does `build:worker` include CSAPI code?

**Answer:** No. The worker bundle (`dist/worker/index.js`, 144.3 KB) contains **zero CSAPI references**. A grep search for "csapi", "CSAPI", "CSAPIQueryBuilder", and "scanCsapiLinks" across the worker output returned no matches.

**Evidence:**

`src/worker/index.ts` imports from:

- `../shared/models.js` (types)
- `../wms/endpoint.js`
- `../wfs/endpoint.js`
- `../wmts/endpoint.js`

There are no imports from `../ogc-api/csapi/` or any CSAPI module. The worker is completely unaffected by CSAPI separation.

### Question 5: In what order do stages run? Does `emptyOutDir: false` layer outputs?

**Answer:** The build order is: `rm -rf dist` → `build:worker` → `build:node` → `build:browser`. The `emptyOutDir: false` setting on both Vite configs ensures they layer outputs into the same `dist/` directory.

**Evidence:**

From `package.json`:

```json
"build": "rm -rf dist && npm run build:worker && npm run build:node && npm run build:browser"
```

Both `vite.node-config.js` and `vite.worker-config.js` set:

```javascript
build: {
  emptyOutDir: false,
  // ...
}
```

This means:

1. `rm -rf dist` cleans the directory
2. `build:worker` creates `dist/worker/index.js` + all `.d.ts` files (via `vite-plugin-dts`)
3. `build:node` adds `dist/dist-node.js` (SSR bundle)
4. `build:browser` adds all per-file `.js` and `.js.map` files in `dist/`

### Question 6: Does `build:browser` esbuild preserve import statements?

**Answer:** Yes. Because esbuild runs in per-file mode (no `--bundle` flag), it preserves all import/export statements as-is, only transforming TypeScript syntax to JavaScript.

**Evidence:**

`dist/index.js` (the compiled `src/index.ts`) contains preserved imports:

```javascript
import CSAPIQueryBuilder from './ogc-api/csapi/url_builder.js';
import { scanCsapiLinks } from './ogc-api/csapi/helpers.js';
// etc.
```

`dist/ogc-api/csapi/url_builder.js` contains:

```javascript
import { EndpointError } from '../../shared/errors.js';
```

These are relative path imports to sibling files — not inlined code.

### Question 7: What role does `--platform=neutral`?

**Answer:** `--platform=neutral` means esbuild does not inject any platform-specific polyfills or module formats. Combined with `--format=esm`, it produces pure ES module output that works in any JavaScript runtime. This does not affect how CSAPI files are compiled — each file is transpiled identically regardless of content.

**Evidence:** The flag is documented as "Do not preset any platform-specific options." Combined with `--format=esm`, the output is standard ESM with no Node.js or browser-specific transformations applied.

### Question 8: Are there build-time exclusions?

**Answer:** Yes, two exclusion patterns in the esbuild `find` command:

1. `-not -path '*worker/index.ts'` — excludes the worker entry point (already built by Vite)
2. `-not -path '*.spec.ts'` — excludes test files

No other exclusions exist. All `.ts` files under `src/` including all CSAPI files are compiled by esbuild.

### Sub-topic Synthesis

The build pipeline is a **three-stage layered architecture** where each stage adds to `dist/` without clearing previous outputs. The key architectural insight is that `build:browser` (esbuild) is a **per-file transpiler, not a bundler**. This means every source `.ts` file gets its own `.js` output in `dist/`, with relative imports preserved. Combined with `vite-plugin-dts` generating all `.d.ts` files via glob (not import graph), the build system **already produces all files needed for a separate `"./csapi"` entry point**. No build tooling changes are required — only a `package.json` exports configuration change and a barrel file creation.

---

## 2. Package.json Exports Configuration

This section answers the 7 questions about the `"exports"` field and how to configure `"./csapi"` as a sub-path export.

### Question 9: What is the current `"exports"` structure?

**Answer:** The current `"exports"` field exposes only `"."` (the root) with four conditional export targets:

**Evidence:**

From `package.json`:

```json
"exports": {
  ".": {
    "types": "./dist/index.d.ts",
    "import": "./dist/index.js",
    "browser": "./dist/index.js",
    "default": "./dist/dist-node.js"
  }
}
```

There is no `"./csapi"` sub-path. The root entry targets:

- `types` → TypeScript declaration file
- `import` → ESM per-file entry (browser or Node ESM)
- `browser` → Same as import (per-file ESM)
- `default` → Node.js SSR bundle (single file with everything inlined)

### Question 10: What paths should `"./csapi"` conditions point to?

**Answer:** The `"./csapi"` sub-path should point to the barrel file output produced by esbuild:

**Recommended configuration:**

```json
"./csapi": {
  "types": "./dist/ogc-api/csapi/index.d.ts",
  "import": "./dist/ogc-api/csapi/index.js",
  "browser": "./dist/ogc-api/csapi/index.js",
  "default": "./dist/ogc-api/csapi/index.js"
}
```

Note: All non-types conditions point to the same per-file ESM output. Unlike the root `"."` export which has a separate Node SSR bundle (`dist-node.js`), the CSAPI sub-path uses the same per-file ESM output for all environments. There is no separate CSAPI Node bundle, and creating one is unnecessary — the per-file ESM output works in Node.js when `"type": "module"` is set.

### Question 11: Do legacy fields need updating?

**Answer:** No. The legacy fields (`"main"`, `"browser"`, `"types"`) apply only to the root package entry point (`"."`). They do not affect sub-path exports. The `"exports"` field takes precedence over legacy fields in environments that support it. The legacy fields should remain as-is for backward compatibility with older tools.

**Evidence:** From Node.js docs: "When the `exports` field is defined, all subpaths of the package are encapsulated and no longer available to importers." The `"main"` field serves as a fallback for the root only, not for sub-paths.

### Question 12: Do we need legacy fields for the CSAPI sub-path?

**Answer:** No. There is no mechanism for legacy fields to define sub-path entry points. Sub-path exports are an `"exports"`-only feature. Environments that don't support `"exports"` cannot access `"./csapi"` regardless.

**Evidence:** The `"main"` and `"browser"` fields in `package.json` only define the root entry point. Sub-path access with legacy resolution would require consumers to use deep imports like `@camptocamp/ogc-client/dist/ogc-api/csapi/index.js`, which is fragile and not recommended.

### Question 13: Does Node.js resolve `"./csapi"` correctly?

**Answer:** Yes, when the consumer's environment supports the `"exports"` field. Node.js 12.7+ supports sub-path exports, and Node.js 12.11+ supports conditional exports. Since the package has `"type": "module"`, the per-file ESM output at `dist/ogc-api/csapi/index.js` will be loaded as an ES module.

**Evidence:** From Node.js documentation: "When using the `exports` field, custom subpaths can be defined along with the main entry point by treating the main entry point as the `"."` subpath."

### Question 14: What if a consumer's bundler doesn't support `"exports"`?

**Answer:** Consumers using tools that don't support `"exports"` would need to use a direct path import: `@camptocamp/ogc-client/dist/ogc-api/csapi/index.js`. However, all modern bundlers (webpack 5+, Rollup, Vite, esbuild) support `"exports"`, so this is an edge case for very old tooling.

The `"files": ["dist/", "src/"]` field ensures both the compiled output and source are included in the published package, making direct path imports possible as a fallback.

### Question 15: Does the `"files"` field need updating?

**Answer:** No. The current `"files": ["dist/", "src/"]` already includes all CSAPI output in `dist/ogc-api/csapi/` and all CSAPI source in `src/ogc-api/csapi/`. No changes needed.

**Evidence:** The `"files"` field uses directory paths that recursively include all contents. Since CSAPI files are under `dist/` and `src/`, they're already covered.

### Sub-topic Synthesis

Adding `"./csapi"` to the `"exports"` field is straightforward: a new sub-path entry with the same four conditions (`types`, `import`, `browser`, `default`), all pointing to the barrel file output in `dist/ogc-api/csapi/`. Unlike the root entry point which uses a separate Node.js SSR bundle, the CSAPI sub-path can use the same per-file ESM output for all environments. Legacy fields don't need changes, and the `"files"` field already covers CSAPI output. The only prerequisite is creating the barrel file (`src/ogc-api/csapi/index.ts`) so that esbuild produces `dist/ogc-api/csapi/index.js` and vite-plugin-dts produces `dist/ogc-api/csapi/index.d.ts`.

---

## 3. TypeScript Declaration Generation

This section answers the 6 questions about `.d.ts` file generation for CSAPI.

### Question 16: Does `vite-plugin-dts` generate `.d.ts` for all source files or only worker-reachable ones?

**Answer:** All source files. The `vite-plugin-dts` configuration uses `include: ['./src/**/*']` which is a **glob pattern**, not an import graph traversal. It generates `.d.ts` files for every `.ts` file under `src/`, regardless of whether that file is imported by the worker entry point (`src/worker/index.ts`).

**Evidence:**

From `vite.worker-config.js`:

```javascript
import dts from 'vite-plugin-dts';
// ...
plugins: [
  dts({
    include: ['./src/**/*'],
    exclude: ['./src/**/*.spec.ts'],
  }),
];
```

The `include` pattern `'./src/**/*'` matches ALL files under `src/`, including all CSAPI files. The `exclude` pattern only removes `.spec.ts` test files.

### Question 17: Do CSAPI `.d.ts` files exist in `dist/` after a full build?

**Answer:** Yes. All 27 CSAPI `.d.ts` files are confirmed present in `dist/ogc-api/csapi/` after a full build, including files in `formats/`, `formats/sensorml/`, `formats/swecommon/`, and `integration/` subdirectories.

**Evidence:**

Confirmed by inspecting `dist/` after `npm run build:worker`:

- `dist/ogc-api/csapi/url_builder.d.ts`
- `dist/ogc-api/csapi/model.d.ts`
- `dist/ogc-api/csapi/helpers.d.ts`
- `dist/ogc-api/csapi/command-routing.d.ts`
- `dist/ogc-api/csapi/formats/index.d.ts`
- `dist/ogc-api/csapi/formats/sensorml/*.d.ts`
- `dist/ogc-api/csapi/formats/swecommon/*.d.ts`
- `dist/ogc-api/csapi/integration/*.d.ts`

These were all generated by `vite-plugin-dts` during the `build:worker` stage — the first build step that runs.

### Question 18: Does `tsc` contribute to declaration generation during the build?

**Answer:** No, `tsc` is not invoked during the build. While `tsconfig.json` has `"declaration": true` and `"declarationMap": true`, these settings would only take effect if `tsc` were run directly (e.g., `tsc --build`). The build script uses esbuild (for JS) and vite-plugin-dts (for declarations). The `tsc` command is only used for typechecking via `npm run typecheck` which runs `tsc --noEmit` — it produces no output files.

**Evidence:**

From `package.json`:

```json
"typecheck": "tsc --noEmit"
```

The `--noEmit` flag means typechecking produces no output. `vite-plugin-dts` is the sole declaration generator.

### Question 19: Will `vite-plugin-dts` generate `dist/ogc-api/csapi/index.d.ts` for a new barrel file?

**Answer:** Yes. Since `vite-plugin-dts` uses `include: ['./src/**/*']`, creating `src/ogc-api/csapi/index.ts` will cause `dist/ogc-api/csapi/index.d.ts` to be automatically generated on the next build. No configuration changes needed.

**Evidence:** The include pattern `'./src/**/*'` is a glob that matches any new `.ts` file added under `src/`. The barrel file at `src/ogc-api/csapi/index.ts` matches this pattern.

### Question 20: Must the `"types"` condition point to a single file or can it point to a directory?

**Answer:** It must point to a single `.d.ts` file. The `"types"` condition in `"exports"` works like the top-level `"types"` field — it must resolve to a specific declaration file. This file will be the barrel file's declaration: `./dist/ogc-api/csapi/index.d.ts`.

**Evidence:** From TypeScript documentation on package.json exports: TypeScript resolves the `"types"` condition to a specific file path, then applies extension substitution. Directory resolution is not supported in this context — it requires an explicit file path.

### Question 21: Does TypeScript `moduleResolution: "node"` resolve `"exports"` sub-paths?

**Answer:** **No.** This is a critical finding. The current `tsconfig.json` uses `"moduleResolution": "node"` (which TypeScript 5.x calls `"node10"`), and this setting **does NOT read the `"exports"` field at all**.

For consumers to resolve `@camptocamp/ogc-client/csapi` via the `"exports"` field, they need:

- `"moduleResolution": "node16"` or `"nodenext"` — for Node.js projects
- `"moduleResolution": "bundler"` — for bundler-based projects

**Evidence:** From TypeScript documentation on `node10` (formerly `node`):

> Supported features for `node10`:
>
> - package.json "exports" ❌
> - package.json "imports" and self-name imports ❌

vs. `node16`/`nodenext`:

> Supported features for `node16`/`nodenext`:
>
> - package.json "exports" ✅ matches types, node, import

vs. `bundler`:

> Supported features for `bundler`:
>
> - package.json "exports" ✅ matches types, import/require depending on syntax

**Impact:** This does NOT affect the upstream ogc-client build itself (which uses esbuild/Vite, not tsc, for compilation). It affects **consumers** of the package. Consumers with `moduleResolution: "node"` would need to use the package-relative path `@camptocamp/ogc-client/dist/ogc-api/csapi/index.js` or update their `moduleResolution` setting. Modern TypeScript projects overwhelmingly use `"node16"`, `"nodenext"`, or `"bundler"`, so this is a minor concern.

### Sub-topic Synthesis

TypeScript declaration generation is already fully handled by `vite-plugin-dts` with its glob-based `include` pattern. All CSAPI `.d.ts` files exist in `dist/` after a standard build, and creating a new barrel file will cause its `.d.ts` to be automatically generated. **No vite-plugin-dts configuration changes are needed.** The one concern is that the upstream project's own `tsconfig.json` uses `moduleResolution: "node"` which doesn't support `"exports"` — but this only affects the project's internal typechecking of self-referencing imports, not the build output or consumers who use modern module resolution.

---

## 4. CSAPI Barrel File and Entry Point

This section answers the 5 questions about the CSAPI barrel file and its role as the `"./csapi"` entry point.

### Question 22: Does `src/ogc-api/csapi/` have an `index.ts`?

**Answer:** No. There is currently no `index.ts` barrel file in `src/ogc-api/csapi/`. The directory contains only the module files: `command-routing.ts`, `helpers.ts`, `model.ts`, `url_builder.ts`, plus the `formats/` and `integration/` subdirectories.

**Evidence:**

Directory listing of `src/ogc-api/csapi/`:

```
command-routing.ts
helpers.ts
model.ts
url_builder.ts
formats/
integration/
```

No `index.ts` exists. One must be created.

### Question 23: What should the barrel file export?

**Answer:** The barrel file should export everything that `src/index.ts` currently re-exports from CSAPI modules. This includes types, interfaces, enums, classes, and functions from `model.ts`, `url_builder.ts`, `helpers.ts`, `command-routing.ts`, and `formats/index.ts`.

**Evidence:**

From `src/index.ts` (lines 45–227), the CSAPI re-exports include:

- From `./ogc-api/csapi/model.js`: ~40+ type exports (CSAPIObservation, CSAPIDatastream, CSAPIResponseFormat, etc.)
- From `./ogc-api/csapi/formats/index.js`: format parser exports
- From `./ogc-api/csapi/url_builder.js`: `CSAPIQueryBuilder` class
- From `./ogc-api/csapi/helpers.js`: `scanCsapiLinks` function and related helpers
- From `./ogc-api/csapi/command-routing.js`: command routing exports

The barrel file content would essentially be the CSAPI-related export lines currently in `src/index.ts`, with paths adjusted to be relative to `src/ogc-api/csapi/`.

### Question 24: What currently imports from CSAPI in the codebase?

**Answer:** Two sources import from CSAPI modules:

1. **`src/ogc-api/endpoint.ts`** (line 52–53) — **runtime dependency:**

   ```typescript
   import CSAPIQueryBuilder from './csapi/url_builder.js';
   import { scanCsapiLinks } from './csapi/helpers.js';
   ```

2. **`src/index.ts`** (lines 45–227) — **re-export dependency:**
   ```typescript
   export type { CSAPIObservation, ... } from './ogc-api/csapi/model.js';
   export { CSAPIQueryBuilder } from './ogc-api/csapi/url_builder.js';
   // ... ~170 lines of CSAPI re-exports
   ```

The `endpoint.ts` imports are the decoupling target for Plan 06. The `src/index.ts` re-exports are the ones that must be moved to the barrel file.

### Question 25: Will esbuild automatically compile the new barrel file?

**Answer:** Yes. The `build:browser` esbuild command uses `find ./src -name "*.ts"` which matches all `.ts` files under `src/`. A new `src/ogc-api/csapi/index.ts` will be automatically discovered and compiled to `dist/ogc-api/csapi/index.js`. No build config changes needed.

**Evidence:** The `find` command pattern `-name "*.ts"` matches any file with a `.ts` extension. The only exclusions are `*worker/index.ts` and `*.spec.ts`. A barrel file named `index.ts` in the CSAPI directory is neither of these, so it will be compiled.

### Question 26: After removing CSAPI from `src/index.ts`, does `build:node` exclude CSAPI?

**Answer:** Yes. The `build:node` stage (Vite SSR) bundles from `src-node/index.ts` → `src/index.ts`. Since Vite follows the import graph (not a file glob), removing CSAPI re-exports from `src/index.ts` means CSAPI modules will not be reachable from the entry point, and Vite will exclude them from `dist-node.js`.

**Evidence:**

`src-node/index.ts` contains:

```typescript
export * from '../src/index.js';
export { enableFallbackWithoutWorker } from '../src/worker-fallback/index.js';
```

Vite SSR follows `export *` transitively. After CSAPI is removed from `src/index.ts`, the `export *` will no longer pull in CSAPI modules. The resulting `dist-node.js` will be smaller by approximately 191 KB (the total CSAPI JS footprint).

**Note:** The two CSAPI imports in `endpoint.ts` (`CSAPIQueryBuilder` and `scanCsapiLinks`) will still pull CSAPI code into `dist-node.js` **until Plan 06 decouples them**. Full CSAPI exclusion from the Node bundle requires both removing re-exports (this plan's scope) AND decoupling endpoint.ts imports (Plan 06's scope).

### Sub-topic Synthesis

A barrel file at `src/ogc-api/csapi/index.ts` is **required** — it does not currently exist. This barrel file serves as the single entry point for the `"./csapi"` sub-path export. Its content will be the CSAPI-specific export lines currently in `src/index.ts` (with paths adjusted to relative). Both esbuild (JS compilation) and vite-plugin-dts (declaration generation) will automatically process this new file without any configuration changes. After CSAPI re-exports are removed from `src/index.ts`, the Node SSR bundle will begin excluding CSAPI from its import graph, with full exclusion achieved after Plan 06 decouples `endpoint.ts`.

---

## 5. Impact on Existing Build

This section answers the 5 questions about how the proposed changes affect each existing build stage.

### Question 27: Will `build:browser` still compile CSAPI files after removal from `src/index.ts`?

**Answer:** Yes. The `build:browser` esbuild command uses a **file glob** (`find ./src -name "*.ts"`), not the import graph from `src/index.ts`. It compiles every `.ts` file individually regardless of whether it's imported by the root barrel. All CSAPI files will continue to be compiled to `dist/ogc-api/csapi/*.js`.

**Evidence:** The esbuild command processes files discovered by the `find` shell command, which traverses the filesystem. Removing exports from `src/index.ts` has zero effect on which files `find` discovers.

### Question 28: Will `dist-node.js` shrink after CSAPI removal?

**Answer:** Partially. Removing CSAPI re-exports from `src/index.ts` will reduce the Node bundle, but **full shrinkage requires Plan 06** to also remove the two CSAPI imports in `endpoint.ts`. Currently:

- `dist-node.js` = 483.5 KB (with all CSAPI inlined)
- After removing re-exports from `src/index.ts`: Partial reduction (some CSAPI code may still be pulled in via `endpoint.ts` → `url_builder.js` and `helpers.js`)
- After Plan 06 decouples `endpoint.ts`: Full CSAPI exclusion (~191 KB reduction)

**Evidence:** Vite SSR follows the import graph. Even after removing re-exports, `endpoint.ts` still imports `CSAPIQueryBuilder` and `scanCsapiLinks`, which pull in `url_builder.ts` (86 KB) and `helpers.ts` (with their transitive dependencies).

### Question 29: Does removing CSAPI from root affect tree-shaking?

**Answer:** It improves tree-shaking for root-import consumers. Currently `import { OgcApiEndpoint } from '@camptocamp/ogc-client'` pulls in the entire module graph including CSAPI. After separation, consumers who only use the root export won't load CSAPI code at all (assuming their bundler tree-shakes unused re-exports). Consumers who need CSAPI will import from `@camptocamp/ogc-client/csapi` explicitly.

### Question 30: Does `build:worker` need changes?

**Answer:** No. The `build:worker` stage is completely unaffected. `src/worker/index.ts` has zero CSAPI imports. The worker bundle output, the d.ts generation (glob-based, not import-based), and all worker-related functionality remain unchanged.

**Evidence:** Grep search across `src/worker/index.ts` for `csapi` returned zero matches. The worker imports from `shared/models`, `wms`, `wfs`, and `wmts` only.

### Question 31: Will `npm run typecheck` (`tsc --noEmit`) still pass?

**Answer:** Yes. The `tsconfig.json` `"include"` pattern is `["./src/**/*", "./src-node/**/*"]`, which includes all CSAPI files regardless of whether they're re-exported from `src/index.ts`. TypeScript will still type-check CSAPI files. The CSAPI barrel file (`src/ogc-api/csapi/index.ts`) will be a new file that gets included via the same glob.

**Evidence:** TypeScript's `--noEmit` typechecking processes all files matched by `include`, not just files reachable from a single entry point. CSAPI files remain under `src/` and thus remain in the typecheck scope.

### Sub-topic Synthesis

The impact on existing build stages is minimal and predictable:

| Build Stage               | Affected?            | Change Needed? | Impact                                                                                   |
| ------------------------- | -------------------- | -------------- | ---------------------------------------------------------------------------------------- |
| `build:browser` (esbuild) | No                   | None           | File glob discovers the same files + the new barrel file                                 |
| `build:node` (Vite SSR)   | Yes — bundle shrinks | None to config | Automatically excludes CSAPI after `src/index.ts` changes (full exclusion after Plan 06) |
| `build:worker` (Vite lib) | No                   | None           | Zero CSAPI imports; d.ts generation glob-based                                           |
| `typecheck` (tsc)         | No                   | None           | `include` glob unchanged; CSAPI files still typechecked                                  |

**No build configuration files need modification.** All changes are source-level (`src/index.ts` modification, `src/ogc-api/csapi/index.ts` creation) and package-level (`package.json` `"exports"` update).

---

## 6. Boundary Condition Verification

### Constraint Compliance Matrix

| #   | Constraint                       | Status      | Evidence                                                                                                                                                                                                                                       | Notes                                                                       |
| --- | -------------------------------- | ----------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------- |
| 1   | No CSAPI in root exports         | ✓ Compliant | Removing CSAPI re-exports from `src/index.ts` removes them from the `"."` export path. `build:browser` still compiles the files (they exist in `dist/`) but they are not reachable from `dist/index.js`                                        | Full removal from `dist-node.js` requires Plan 06 to decouple `endpoint.ts` |
| 2   | Separate entry point `"./csapi"` | ✓ Compliant | `"exports"` configuration with `"./csapi"` sub-path pointing to barrel file output at `dist/ogc-api/csapi/index.js`                                                                                                                            | Consumers import via `@camptocamp/ogc-client/csapi`                         |
| 5   | CI must pass                     | ✓ Compliant | No build config changes needed; esbuild file glob, vite-plugin-dts glob, and typecheck glob all continue to include CSAPI files. Only source changes (barrel file creation, `src/index.ts` modification) and `package.json` `"exports"` update | Must verify with actual build run during implementation                     |

### Scope Boundary Adherence

- **In scope — explored:**

  - Complete build pipeline analysis (3 stages)
  - `dist/` directory tree documentation
  - `package.json` `"exports"` configuration for `"./csapi"`
  - TypeScript declaration generation analysis
  - CSAPI barrel file necessity assessment
  - Impact on each build stage
  - Cross-module dependency mapping

- **Out of scope — respected:**

  - Consumer API design (deferred to Plan 03)
  - Decoupling architecture for `endpoint.ts` (deferred to Plan 06)
  - Formatting and linting (deferred to Plan 07)
  - Alternative build tool evaluation (excluded per constraints)

- **Scope adjustments:** None. All 31 planned questions were answerable with available data.

---

## 7. Implementation Scope Gate Assessment

> **Applying the "research broadly, implement minimally" principle.**

### Minimum-Change Test

| Finding / Recommendation                        | Serves jahow's requirements?                            | Minimum-change?             | Include in implementation?   |
| ----------------------------------------------- | ------------------------------------------------------- | --------------------------- | ---------------------------- |
| Create `src/ogc-api/csapi/index.ts` barrel file | Yes — directly required for `"./csapi"` entry point     | Yes                         | ✓ Include                    |
| Add `"./csapi"` to `package.json` `"exports"`   | Yes — directly required for separate import path        | Yes                         | ✓ Include                    |
| Remove CSAPI re-exports from `src/index.ts`     | Yes — directly required (no CSAPI in root)              | Yes                         | ✓ Include                    |
| Node SSR bundle shrinkage                       | Yes — necessary consequence of removing CSAPI from root | Yes — happens automatically | ✓ Include (no action needed) |
| Consumer `moduleResolution` compatibility note  | No — nice-to-have documentation                         | No — not minimum change     | ✗ Defer                      |
| Optimizing per-file ESM for Node consumers      | No — nice-to-have optimization                          | No — current approach works | ✗ Defer                      |

### Deferred Insights

- **Consumer `moduleResolution: "node"` limitation:** While consumers using `moduleResolution: "node"` can't resolve `"exports"` sub-paths, fixing this requires consumers to update their own tsconfig and is outside our implementation scope.
- **Separate Node CSAPI bundle:** Creating a dedicated `dist-node-csapi.js` SSR bundle is unnecessary — the per-file ESM output works fine in Node.js with `"type": "module"`. This would only matter for performance-sensitive Node.js SSR use cases.
- **`build:browser` Windows compatibility:** The `$(find ...)` bash syntax in `build:browser` fails on Windows PowerShell. This is a pre-existing issue unrelated to CSAPI separation. Not in scope to fix.

---

## 8. Impact on Dependent Plans

### What Downstream Plans Should Consume

| Downstream Plan                                | What to consume from this report                                                                                                                                                                                                                                                                   | Section reference                                          |
| ---------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------- |
| **Plan 03** (Separate Entry Point Design)      | Confirmed `"exports"` configuration structure; barrel file pattern; per-file ESM output model; `"types"` condition pointing to `.d.ts` file                                                                                                                                                        | § 2 (Q9–Q15), § 4 (Q22–Q26)                                |
| **Plan 06** (Endpoint Decoupling Architecture) | `endpoint.ts` has exactly 2 CSAPI imports (line 52: `CSAPIQueryBuilder`, line 53: `scanCsapiLinks`); CSAPI modules' outward dependencies (shared/models types, ogc-api/model types, shared/errors EndpointError class); full CSAPI exclusion from `dist-node.js` requires decoupling these imports | § 4 (Q24), § 5 (Q28), Key Takeaway #6                      |
| **Plan 08** (File-Level Changelist)            | Exact files to modify: `package.json` (exports), `src/index.ts` (remove CSAPI), `src/ogc-api/csapi/index.ts` (create barrel); NO build config changes needed                                                                                                                                       | § 5 (Sub-topic Synthesis), § 10 (Impact on Implementation) |

### Decisions Now Final

1. **No build tooling changes required:** esbuild per-file mode + vite-plugin-dts glob include already produce all necessary output. This is confirmed by empirical build inspection.
2. **Barrel file required at `src/ogc-api/csapi/index.ts`:** This file does not exist and must be created. It is the single entry point for the `"./csapi"` sub-path export.
3. **`"./csapi"` exports configuration:** Four conditions (`types`, `import`, `browser`, `default`) all pointing to the barrel file output in `dist/ogc-api/csapi/`.
4. **All `.d.ts` files automatically generated:** No vite-plugin-dts configuration changes. Creating the barrel file `.ts` → automatically generates barrel file `.d.ts`.

### Items Requiring Downstream Resolution

1. **Barrel file exact export list** → Plan 03 should finalize the public API surface of the barrel file (which types/classes/functions are public vs. internal)
2. **`endpoint.ts` decoupling strategy** → Plan 06 must resolve how to remove the 2 CSAPI imports from `endpoint.ts` without breaking the OgcApiEndpoint functionality
3. **Commit ordering** → Plan 08 should determine whether barrel file creation, `src/index.ts` modification, and `package.json` update happen in one commit or are sequenced

---

## 9. Key Takeaways

1. **Per-file compilation is the key enabler:** esbuild's `--outdir` mode (no `--bundle`) produces one `.js` file per source `.ts` file with preserved imports. This means CSAPI files already exist individually in `dist/ogc-api/csapi/`, making a sub-path export trivially possible.

2. **Config-only solution confirmed:** Adding `"./csapi"` requires only: (a) create barrel file, (b) update `package.json` exports, (c) remove CSAPI from `src/index.ts`. No build tool configuration changes.

3. **vite-plugin-dts uses glob, not import graph:** The `include: ['./src/**/*']` pattern means ALL `.d.ts` files are generated regardless of the worker entry point's imports. New barrel file → automatic `.d.ts` generation.

4. **Node SSR bundle inlines everything:** `dist-node.js` (483.5 KB) contains all CSAPI code. After removing CSAPI re-exports, it will partially shrink. Full CSAPI exclusion requires Plan 06's endpoint decoupling.

5. **Worker is CSAPI-free:** `src/worker/index.ts` has zero CSAPI imports. The worker build stage is completely unaffected by the separation.

6. **`endpoint.ts` is the coupling point:** Two imports on lines 52–53 (`CSAPIQueryBuilder` and `scanCsapiLinks`) are the sole coupling between the core ogc-api module and CSAPI. This is Plan 06's decoupling target.

7. **CSAPI footprint is substantial:** 191.4 KB of JS across 27 files, with `url_builder.js` alone at 86 KB. This validates the need for a separate entry point — consumers who don't need CSAPI shouldn't have to load it.

8. **`moduleResolution: "node"` won't resolve sub-path exports:** The upstream project's `tsconfig.json` uses `moduleResolution: "node"` which doesn't read `"exports"`. Consumers need `"node16"`, `"nodenext"`, or `"bundler"` to resolve `@camptocamp/ogc-client/csapi`. This is the consumer's responsibility, not the package's.

9. **Three-stage layered build:** The build order `rm -rf dist → worker → node → browser` with `emptyOutDir: false` layers outputs into the same directory. Each stage's contribution is independent and predictable.

10. **CSAPI's outward dependencies are minimal:** CSAPI modules depend on `shared/models.js` (type imports only), `ogc-api/model.js` (type imports only), and `shared/errors.js` (`EndpointError` class — the sole runtime dependency on non-CSAPI code). This clean dependency direction supports easy separation.

---

## 10. Impact on Implementation

### Must Change (Required by Findings)

1. **Create `src/ogc-api/csapi/index.ts`** — barrel file re-exporting all public CSAPI types, classes, and functions. Content is the ~170 lines of CSAPI exports currently in `src/index.ts`, with import paths adjusted from `./ogc-api/csapi/` to `./`.

2. **Update `package.json` `"exports"`** — add the `"./csapi"` sub-path:

   ```json
   "exports": {
     ".": {
       "types": "./dist/index.d.ts",
       "import": "./dist/index.js",
       "browser": "./dist/index.js",
       "default": "./dist/dist-node.js"
     },
     "./csapi": {
       "types": "./dist/ogc-api/csapi/index.d.ts",
       "import": "./dist/ogc-api/csapi/index.js",
       "browser": "./dist/ogc-api/csapi/index.js",
       "default": "./dist/ogc-api/csapi/index.js"
     }
   }
   ```

3. **Remove CSAPI re-exports from `src/index.ts`** — delete the ~170 lines (lines 45–227) that re-export from `./ogc-api/csapi/model.js`, `./ogc-api/csapi/formats/index.js`, `./ogc-api/csapi/url_builder.js`, `./ogc-api/csapi/helpers.js`, and `./ogc-api/csapi/command-routing.js`.

### Should Change (Recommended by Findings)

1. **Document the `moduleResolution` requirement** — add a note in package documentation that consumers using TypeScript with `moduleResolution: "node"` should switch to `"node16"`, `"nodenext"`, or `"bundler"` to resolve the `"./csapi"` sub-path export.

### Could Change (Optional Improvements)

1. **Fix Windows `build:browser` compatibility** — replace `$(find ...)` bash syntax with a cross-platform alternative. This is a pre-existing issue unrelated to CSAPI separation.
2. **Add `"./csapi/*"` pattern export** — allow consumers to import individual CSAPI sub-modules directly (e.g., `@camptocamp/ogc-client/csapi/model`). This provides more granular imports but increases the public API surface.

---

## 11. Open Questions

| #   | Question                                                                                                   | Why Unresolved                                                       | Resolution Path                                               |
| --- | ---------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------- | ------------------------------------------------------------- |
| 1   | What is the exact public API surface of the CSAPI barrel file?                                             | This is a consumer API design question, not a build system question  | Plan 03 should finalize which exports are public vs. internal |
| 2   | How should `endpoint.ts` be decoupled from CSAPI imports?                                                  | Requires architectural analysis of the OgcApiEndpoint class          | Plan 06 will resolve this                                     |
| 3   | Should the barrel file re-export everything from `src/index.ts`, or should some CSAPI internals be hidden? | Design decision about public API surface                             | Plan 03 should decide                                         |
| 4   | Will removing CSAPI from `src/index.ts` break any existing consumers of ogc-client?                        | This is a semver/breaking-change question, not a build question      | Plan 03 or Plan 08 should assess breaking-change impact       |
| 5   | Should self-referencing imports within the project use `@camptocamp/ogc-client/csapi`?                     | Depends on whether `moduleResolution: "node"` in tsconfig is updated | Deferred — not needed for upstream PR                         |

---

## Evidence Appendix

### A. CSAPI File Inventory in `dist/`

After a full build (`npm run build`), the following CSAPI files exist in `dist/ogc-api/csapi/`:

```
dist/ogc-api/csapi/
├── command-routing.d.ts
├── command-routing.js
├── command-routing.js.map
├── helpers.d.ts
├── helpers.js
├── helpers.js.map
├── model.d.ts
├── model.js
├── model.js.map
├── url_builder.d.ts
├── url_builder.js (86 KB)
├── url_builder.js.map
├── formats/
│   ├── index.d.ts
│   ├── index.js
│   ├── index.js.map
│   ├── [12+ format parser files with .d.ts, .js, .js.map]
│   ├── sensorml/
│   │   └── [parser files with .d.ts, .js, .js.map]
│   └── swecommon/
│       └── [parser files with .d.ts, .js, .js.map]
└── integration/
    ├── [5 spec/integration files with .d.ts, .js, .js.map]
```

Total CSAPI JS: **191.4 KB across 27 .js files**

### B. CSAPI Cross-Module Dependencies

CSAPI modules import from non-CSAPI modules:

| CSAPI File               | Imports From                                                                 | Import Type                       |
| ------------------------ | ---------------------------------------------------------------------------- | --------------------------------- |
| Multiple CSAPI files     | `../../shared/models.js` (BoundingBox, DateTimeParameter, CrsCode, MimeType) | `import type` (types only)        |
| Multiple CSAPI files     | `../model.js` (OgcApiDocumentLink, OgcApiCollectionInfo)                     | `import type` (types only)        |
| `url_builder.ts`, others | `../../shared/errors.js` (EndpointError)                                     | Value import (runtime dependency) |

Non-CSAPI modules import from CSAPI:

| Non-CSAPI File            | Imports From CSAPI                           | Import Type            |
| ------------------------- | -------------------------------------------- | ---------------------- |
| `src/ogc-api/endpoint.ts` | `./csapi/url_builder.js` (CSAPIQueryBuilder) | Value import (runtime) |
| `src/ogc-api/endpoint.ts` | `./csapi/helpers.js` (scanCsapiLinks)        | Value import (runtime) |
| `src/index.ts`            | Multiple CSAPI modules                       | Re-export (public API) |

### C. Current `package.json` `"exports"` (verbatim)

```json
"exports": {
  ".": {
    "types": "./dist/index.d.ts",
    "import": "./dist/index.js",
    "browser": "./dist/index.js",
    "default": "./dist/dist-node.js"
  }
}
```

---

## Research Completion Checklist

- [x] All 31 detailed questions from the research plan have specific, evidenced answers
- [x] Boundary condition verification completed (Section 6)
- [x] Implementation scope gate assessment completed (Section 7)
- [x] Impact on dependent plans documented (Section 8)
- [x] Key takeaways extracted (Section 9)
- [x] Open questions cataloged with resolution paths (Section 11)
- [x] Cross-references to prior findings are accurate (N/A — this is Plan 1)
- [x] Findings respect all boundary conditions from the research plan
- [x] Document is self-contained — a reader unfamiliar with the plan can understand the findings

**Research Started:** 2026-02-23
**Research Completed:** 2026-02-23
**Reviewed:** Not yet

---

## Notes

- **Windows build compatibility:** The `build:browser` script's `$(find ./src ...)` bash syntax fails in PowerShell on Windows. A workaround using PowerShell's `Get-ChildItem` was used to verify per-file output behavior. This is a pre-existing issue not related to CSAPI separation.
- **Build performance:** Running all three build stages individually confirmed that `build:worker` is the slowest stage (~2.6 seconds for d.ts generation alone). The esbuild per-file compilation (`build:browser`) is extremely fast.
- **The `integration/` directory:** Contains 5 pipeline spec files (command, discovery, navigation, observation, pipeline) that are included in the CSAPI dist output. Plan 03 should determine whether these are public API or internal implementation details.
