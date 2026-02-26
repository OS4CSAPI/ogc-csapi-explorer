# Phase 6: Upstream Acceptance Refactoring — Implementation Guide

**Version:** 1.0
**Date:** February 24, 2026
**Status:** Ready for Execution
**Scope:** Module boundary refactoring only — zero CSAPI business logic changes

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Architecture Context](#2-architecture-context)
3. [Design Principles](#3-design-principles)
4. [Commit 14 — Formatting and ESLint](#4-commit-14--formatting-and-eslint)
   - 4.1 [Prettier Scope](#41-prettier-scope)
   - 4.2 [ESLint Scope](#42-eslint-scope)
   - 4.3 [Execution Sequence](#43-execution-sequence)
   - 4.4 [Commit Message](#44-commit-message)
5. [Commit 15 — Architecture Refactoring](#5-commit-15--architecture-refactoring)
   - 5.1 [Files Created](#51-files-created)
   - 5.2 [Files Modified](#52-files-modified)
   - 5.3 [Files NOT Changed](#53-files-not-changed)
   - 5.4 [Commit Message](#54-commit-message)
6. [New File Specifications](#6-new-file-specifications)
   - 6.1 [Barrel File: `csapi/index.ts`](#61-barrel-file-csapiindexts)
   - 6.2 [Factory Function: `csapi/factory.ts`](#62-factory-function-csapifactoryts)
   - 6.3 [Factory Tests: `csapi/factory.spec.ts`](#63-factory-tests-csapifactoryspects)
7. [Modified File Specifications](#7-modified-file-specifications)
   - 7.1 [`src/ogc-api/endpoint.ts`](#71-srcogc-apiendpointts)
   - 7.2 [`src/index.ts`](#72-srcindexts)
   - 7.3 [`src/ogc-api/endpoint.spec.ts`](#73-srcogc-apiendpointspects)
   - 7.4 [`package.json`](#74-packagejson)
8. [Consumer API Migration](#8-consumer-api-migration)
9. [Verification Plan](#9-verification-plan)
   - 9.1 [Boundary Verification](#91-boundary-verification)
   - 9.2 [CI Verification](#92-ci-verification)
   - 9.3 [Litmus Test](#93-litmus-test)
   - 9.4 [Diff Review](#94-diff-review)
10. [Git Command Runbook](#10-git-command-runbook)
    - 10.1 [Phase 0: Preparation](#101-phase-0-preparation)
    - 10.2 [Phase 1: Commit 14](#102-phase-1-commit-14)
    - 10.3 [Phase 2: Commit 15](#103-phase-2-commit-15)
    - 10.4 [Phase 3: Verification and Push](#104-phase-3-verification-and-push)
11. [Branching Strategy and Rebase Path](#11-branching-strategy-and-rebase-path)
12. [Risk Register](#12-risk-register)
13. [Scope Boundaries](#13-scope-boundaries)
14. [Research Foundation](#14-research-foundation)

---

## 1. Executive Summary

This guide covers the implementation of **Phase 6: Upstream Acceptance Refactoring** — decoupling the CSAPI module from the core ogc-client library to satisfy upstream maintainer jahow's two acceptance requirements from [PR #136](https://github.com/camptocamp/ogc-client/pull/136):

1. **CSAPI symbols must not appear in the root `index.ts` file.** Consumers import CSAPI via `@camptocamp/ogc-client/csapi`.
2. **Nothing outside `csapi/` may import from the CSAPI module.** One-way dependency: CSAPI depends on core, never the reverse.

**Estimated volume:** ~280 lines of new code (barrel file + factory + factory tests), ~275 lines removed (endpoint method + root exports + migrated tests), ~3,023 lines of automated Prettier formatting changes.

**What this guide does NOT cover:** CSAPI business logic, URL builder methods, format parsers, model types, SensorML/SWE Common parsers, integration tests, or any work outside the module boundary refactoring. The CSAPI implementation is complete from Phases 1–5 (1,282 tests, 29 suites, 0 tsc errors). Phase 6 changes zero CSAPI behavior.

**Relationship to prior guides:** The [CSAPI Implementation Guide](../csapi-implementation-guide.md) (v7.0, 4,715 lines) covers the full CSAPI contribution across all phases. The [P5 Parser Completion Implementation Guide](../phase-5/P5-parser-completion-implementation-guide.md) (1,009 lines) covers the Phase 5 parser work. This guide is a narrowly scoped supplement covering only the Phase 6 module boundary refactoring.

> **Research Foundation**
>
> This implementation guide is built on **8 completed research plans** (285 questions answered, ~8,000 lines of findings). Every design choice is traced to systematic research against upstream patterns, ecosystem benchmarks, and jahow's explicit requirements. Zero open questions remain.
>
> **See:** [`docs/research/phase-6/findings/`](../../research/phase-6/findings/) for the complete research foundation.

---

## 2. Architecture Context

### Before Phase 6 (Current State)

```
┌─────────────────────────────────────────────────────────────────┐
│                 src/index.ts (252 lines)                        │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  Lines 1–44:  WFS, WMS, WMTS, shared, OGC API exports  │    │
│  │  Lines 45–227: ❌ 183 lines of CSAPI re-exports        │    │
│  │  Lines 228–252: TMS, STAC, cache, worker exports       │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│             src/ogc-api/endpoint.ts (896 lines)                 │
│                                                                  │
│  Line 52: ❌ import CSAPIQueryBuilder from './csapi/...'        │
│  Line 53: ❌ import { scanCsapiLinks } from './csapi/...'      │
│  Line 71: ❌ private csapi_builder_ cache Map                   │
│  ~L363:   ❌ csapi() method (~49 lines)                        │
│  ~L424:   ❌ extractRootResourceUrls() (~14 lines)             │
│                                                                  │
│  L340:    ✅ hasConnectedSystems (zero csapi imports)           │
│  L352:    ✅ csapiCollections (zero csapi imports)              │
└─────────────────────────────────────────────────────────────────┘
```

**Problem:** CSAPI is entangled with core. A consumer importing `@camptocamp/ogc-client` gets all CSAPI code in their bundle. `endpoint.ts` has 2 imports from `csapi/`. `index.ts` has 183 lines of CSAPI re-exports.

### After Phase 6 (Target State)

```
┌─────────────────────────────────────────────────────────────────┐
│                 src/index.ts (~69 lines)                        │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  Lines 1–44:  WFS, WMS, WMTS, shared, OGC API exports  │    │
│  │               ✅ Zero CSAPI references                   │    │
│  │  Lines 45+:   TMS, STAC, cache, worker exports          │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│             src/ogc-api/endpoint.ts (~833 lines)                │
│                                                                  │
│  ✅ Zero imports from csapi/                                    │
│  ✅ hasConnectedSystems getter (unchanged)                     │
│  ✅ csapiCollections getter (unchanged)                        │
│  ✅ root → public (1-word change)                               │
│  ✅ getCollectionDocument → public (1-word change)              │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│         src/ogc-api/csapi/index.ts (NEW — ~190 lines)          │
│              ↕ import/export ↕                                   │
│         src/ogc-api/csapi/factory.ts (NEW — ~55 lines)         │
│              ↓ import type ↓                                     │
│         ../endpoint.ts (type-only, erased at compile)           │
│                                                                  │
│  Consumer: import { createCSAPIBuilder }                        │
│            from '@camptocamp/ogc-client/csapi'                  │
└─────────────────────────────────────────────────────────────────┘

package.json "exports": {
  ".":       → dist/index.js (core — zero CSAPI)
  "./csapi": → dist/ogc-api/csapi/index.js (CSAPI module)
}
```

**Result:** Complete isolation. Consumers who use only core ogc-client get zero CSAPI code. Consumers who need CSAPI import it explicitly via a separate sub-path.

### Key Architectural Decisions

| Decision                                                  | Rationale                                                                                                                                      | Research Source            |
| --------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------- |
| Separate sub-path export (`"./csapi"`)                    | Ecosystem standard — 6/6 surveyed libraries use conditional sub-path exports                                                                   | Plan 01, Plan 03           |
| Barrel file at `csapi/index.ts`                           | Universal pattern (6/6 libraries). Single source of truth for CSAPI public API                                                                 | Plan 01, Plan 03           |
| Factory function `createCSAPIBuilder()`                   | Replaces `endpoint.csapi()`. Constructor injection is 4/7 dominant pattern for stateful sub-modules                                            | Plan 04, Plan 06           |
| `hasConnectedSystems`/`csapiCollections` stay on endpoint | Zero CSAPI imports — use `info.ts` functions with conformance URI strings. Identical to EDR's `hasEnvironmentalDataRetrieval`/`edrCollections` | Plan 02                    |
| Level 3.5 coupling (`Pick<>` + `import type`)             | Constructor already uses `Pick<OgcApiCollectionInfo, ...>`. `import type` is erased at compile time. Zero runtime coupling                     | Plan 05                    |
| `scanCsapiLinks` stays in CSAPI                           | Problem self-resolves when endpoint stops calling it. Factory calls it directly. Minimum-change                                                | Plan 05 → Plan 06 override |
| `root`/`getCollectionDocument` made public                | Factory needs access. Both already called by multiple endpoint features internally. 1-word change each                                         | Plan 06                    |
| Format First commit strategy                              | 3,023-insertion Prettier diff MUST be separated from logic changes. Upstream has 5+ formatting-only commit precedents                          | Plan 07                    |
| `"sideEffects": false`                                    | 5/6 surveyed libraries declare this. Enables tree-shaking through barrel files                                                                 | Plan 03                    |
| Append commits (not amend/squash)                         | Safest path, best reviewability, zero rebase conflict risk                                                                                     | Plan 08                    |

---

## 3. Design Principles

### 3.1 Minimum Change

Every file operation must pass the scope gate: **"Does this serve jahow's two requirements or CI compliance?"** If neither, defer. This principle held through the entire 8-plan research arc — no generalized utilities, no plugin systems, no enforcement tooling made the cut.

### 3.2 Zero Business Logic Changes

Phase 6 touches the **integration boundary only**. The URL builder, format parsers, model types, helpers, command routing, SensorML/SWE Common parsers — all remain byte-identical (except Prettier whitespace in Commit 14). Any test that fails after Phase 6 represents a regression, not an intentional change.

### 3.3 Format First

Separate the mechanical formatting diff from the logical architecture diff. A reviewer can skip Commit 14 entirely and focus on Commit 15 — the actual refactoring.

### 3.4 Append, Don't Amend

Adding 2 commits on top of the existing 13 is safer than rewriting history. The "integrate then decouple" narrative is acceptable for a draft PR. If jahow requests squashing, `git rebase -i` is trivial from the appended state.

### 3.5 Comply with Upstream Code Style

All new files must be Prettier-compliant from inception:

- Single quotes, semicolons, 80-char `printWidth`, 2-space indent
- Trailing commas ES5-style (objects/arrays, NOT function params)
- `.js` extensions on all local imports/re-exports
- `import type` for type-only imports
- LF line endings

---

## 4. Commit 14 — Formatting and ESLint

**Purpose:** Mechanical cleanup only. Zero logic changes. Required to pass upstream CI gates `format:check` and `lint`.

### 4.1 Prettier Scope

51 files total, broken into 3 categories:

**CSAPI source files (20 of 27):**

| File | Path (relative to `src/ogc-api/csapi/`) |
| ---- | --------------------------------------- |
| 1    | `command-routing.ts`                    |
| 2    | `helpers.ts`                            |
| 3    | `model.ts`                              |
| 4    | `url_builder.ts`                        |
| 5    | `formats/geojson.ts`                    |
| 6    | `formats/index.ts`                      |
| 7    | `formats/part2.ts`                      |
| 8    | `formats/property.ts`                   |
| 9    | `formats/response.ts`                   |
| 10   | `formats/sensorml/_helpers.ts`          |
| 11   | `formats/sensorml/aggregate-process.ts` |
| 12   | `formats/sensorml/parser.ts`            |
| 13   | `formats/sensorml/physical-system.ts`   |
| 14   | `formats/swecommon/_helpers.ts`         |
| 15   | `formats/swecommon/components.ts`       |
| 16   | `formats/swecommon/data-array.ts`       |
| 17   | `formats/swecommon/data-record.ts`      |
| 18   | `formats/swecommon/index.ts`            |
| 19   | `formats/swecommon/parser.ts`           |
| 20   | `formats/swecommon/types.ts`            |

**CSAPI test files (26 of 29):** All test files except `formats/index.spec.ts`, `sensorml/index.spec.ts`, and `swecommon/index.spec.ts` (those 3 already pass Prettier).

**CSAPI fixture JSON files (4):**

| File                                                                  |
| --------------------------------------------------------------------- |
| `fixtures/ogc-api/csapi/sample-data-hub.json`                         |
| `fixtures/ogc-api/csapi/sample-data-hub/collections.json`             |
| `fixtures/ogc-api/csapi/sample-data-hub/conformance.json`             |
| `fixtures/ogc-api/csapi/sample-data-hub/collections/iot-sensors.json` |

**Core file (1):** `src/ogc-api/endpoint.ts` — 8-line formatting diff only.

**Volume note:** `url_builder.spec.ts` alone accounts for ~55% of the total formatting diff (2,221 of 4,059 changed lines) due to inline link object expansion at 80-char `printWidth`.

### 4.2 ESLint Scope

99 errors total — **all `@typescript-eslint/no-unused-vars`** across 15 files.

**Source files (5 files, 9 errors):**

| File                                    | Errors |
| --------------------------------------- | ------ |
| `url_builder.ts`                        | 1      |
| `formats/sensorml/aggregate-process.ts` | 2      |
| `formats/sensorml/parser.ts`            | 2      |
| `formats/sensorml/physical-system.ts`   | 3      |
| `formats/sensorml/simple-process.ts`    | 1      |

**Test files (10 files, 90 errors):**

| File                                         | Errors |
| -------------------------------------------- | ------ |
| `formats/sensorml/aggregate-process.spec.ts` | 1      |
| `formats/sensorml/parser.spec.ts`            | 1      |
| `formats/sensorml/physical-system.spec.ts`   | 2      |
| `formats/sensorml/simple-process.spec.ts`    | 1      |
| `formats/sensorml/types.spec.ts`             | **32** |
| `formats/swecommon/data-record.spec.ts`      | **14** |
| `formats/swecommon/index.spec.ts`            | 1      |
| `formats/swecommon/parser.spec.ts`           | 1      |
| `formats/swecommon/types.spec.ts`            | **27** |
| `integration/observation.spec.ts`            | 3      |

**Fix approach:** Remove unused imports entirely, or convert `import { X }` to `import type { X }` where the import is used only as a type. Do NOT prefix with `_` unless it is a function parameter (not an import). All fixes are mechanical — removing an unused import cannot change runtime behavior.

### 4.3 Execution Sequence

```bash
# 1. Apply Prettier (automated)
npx prettier --write "src/ogc-api/csapi/**/*.ts"
npx prettier --write "fixtures/ogc-api/csapi/**/*.json"
npx prettier --write "src/ogc-api/endpoint.ts"

# 2. Fix ESLint errors (manual — 15 files, 99 removals)
# [Remove or convert unused imports per §4.2]

# 3. Verify
npx prettier --check "src/ogc-api/csapi/**/*.ts" \
  "fixtures/ogc-api/csapi/**/*.json" "src/ogc-api/endpoint.ts"
npx eslint src/ogc-api/csapi/
```

**Ordering matters:** Prettier first, ESLint second. Prettier and ESLint do not conflict — ESLint enforces no formatting rules in the upstream configuration.

### 4.4 Commit Message

```
style(csapi): apply prettier formatting and fix eslint errors

Formatting-only commit — no logic changes. Applied npx prettier --write
to all CSAPI source, test, and fixture files. Fixed 99 ESLint
no-unused-vars errors across 15 files by removing/renaming unused
imports.

51 files changed (46 CSAPI source/test + 4 fixture JSON + endpoint.ts).
url_builder.spec.ts accounts for ~55% of the formatting diff due to
inline link object expansion at 80-char printWidth.

Required to pass upstream CI: npm run format:check and npm run lint.
```

---

## 5. Commit 15 — Architecture Refactoring

**Purpose:** Decouple CSAPI from the core library. The actual deliverable of Phase 6.

### 5.1 Files Created

| #   | Path                                | Purpose                                           | Approx Lines |
| --- | ----------------------------------- | ------------------------------------------------- | ------------ |
| C1  | `src/ogc-api/csapi/index.ts`        | Barrel file — re-exports all public CSAPI symbols | ~190         |
| C2  | `src/ogc-api/csapi/factory.ts`      | `createCSAPIBuilder` async factory function       | ~55          |
| C3  | `src/ogc-api/csapi/factory.spec.ts` | Tests for factory function                        | ~30          |

### 5.2 Files Modified

| #   | Path                           | Nature of Change                                                             | Lines Removed | Lines Added | Net  |
| --- | ------------------------------ | ---------------------------------------------------------------------------- | ------------- | ----------- | ---- |
| M1  | `src/ogc-api/endpoint.ts`      | Remove 2 CSAPI imports, 1 cache field, 2 methods; change 2 methods to public | ~65           | ~2          | −63  |
| M2  | `src/index.ts`                 | Remove all CSAPI export lines (lines 45–227)                                 | ~183          | 0           | −183 |
| M3  | `src/ogc-api/endpoint.spec.ts` | Remove 3 tests (2 migrated to factory.spec.ts, 1 caching test removed)       | ~30           | 0           | −30  |
| M4  | `package.json`                 | Add `"./csapi"` sub-path export; add `"sideEffects": false`                  | 0             | ~8          | +8   |

### 5.3 Files NOT Changed

| File                                       | Why                                                                                |
| ------------------------------------------ | ---------------------------------------------------------------------------------- |
| `src/ogc-api/info.ts`                      | Zero CSAPI imports — uses only conformance URI strings inline                      |
| `src/shared/mime-type.ts`                  | CSAPI MIME functions live in `shared/`, not `csapi/` — constraint 3 does not apply |
| All 56 existing CSAPI files                | Zero business logic changes — only formatting in Commit 14                         |
| `vite.node-config.js`                      | Node build uses `src-node/index.ts`, not CSAPI                                     |
| `vite.worker-config.js`                    | `vite-plugin-dts` uses glob `src/**/*.ts` — already covers `csapi/`                |
| `tsconfig.json`                            | `include: ["src"]` already covers `csapi/`                                         |
| `jest.config.cjs` / `jest.node.config.cjs` | Test pattern `**/*.spec.ts` matches any location                                   |

### 5.4 Commit Message

```
refactor(csapi): decouple from endpoint with separate entry point

Architectural refactoring to satisfy upstream review requirements:
1. CSAPI symbols removed from root src/index.ts (~183 lines)
2. New barrel file csapi/index.ts re-exports all CSAPI public API
3. New factory function createCSAPIBuilder(endpoint, collectionId)
   replaces endpoint.csapi() method
4. Two CSAPI imports removed from endpoint.ts (constraint 3)
5. root and getCollectionDocument changed from private to public
6. csapi(), extractRootResourceUrls(), and CSAPI cache removed
7. ./csapi sub-path added to package.json exports
8. sideEffects: false added for tree-shaking support
9. 3 endpoint CSAPI tests migrated to new factory.spec.ts

Consumer API: import { createCSAPIBuilder } from '@camptocamp/ogc-client/csapi'

Boundary conditions verified:
- git grep 'from.*csapi' src/ogc-api/endpoint.ts → 0 matches
- git grep 'csapi' src/index.ts → 0 matches
- Removing csapi/ leaves core fully functional
```

---

## 6. New File Specifications

### 6.1 Barrel File: `csapi/index.ts`

**Path:** `src/ogc-api/csapi/index.ts`
**Approx Lines:** ~190
**Pattern:** Follows existing `csapi/formats/index.ts` (344 lines) — sectioned JSDoc comment dividers, `export` for values, `export type` for types.

**Organization (6 sections):**

````typescript
/**
 * OGC API — Connected Systems (CSAPI) module.
 *
 * This barrel file re-exports all public CSAPI symbols accessible
 * via `@camptocamp/ogc-client/csapi`.
 *
 * @example
 * ```ts
 * import { createCSAPIBuilder } from '@camptocamp/ogc-client/csapi';
 * import type { System, Datastream } from '@camptocamp/ogc-client/csapi';
 * ```
 *
 * @module csapi
 */

// ── Factory Function ───────────────────────────────────────
export { createCSAPIBuilder } from './factory.js';

// ── Query Builder ──────────────────────────────────────────
export { default as CSAPIQueryBuilder } from './url_builder.js';

// ── Model Values ───────────────────────────────────────────
export {
  CSAPIResourceTypes,
  CommandStatusCodes,
  SystemTypeUris,
} from './model.js';

// ── Model Types ────────────────────────────────────────────
export type {
  CSAPIResourceType,
  CommandStatusCode,
  SystemTypeUri,
  TimeInterval,
  ResourceLink,
  CSAPIResourceRef,
  CsapiDateTimeParameter,
  QueryOptions as CSAPIQueryOptions,
  SystemQueryOptions,
  DeploymentQueryOptions,
  // ... (~35 types total from model.js)
} from './model.js';

// ── Format Handler Values ──────────────────────────────────
export {
  parseSensorML30,
  parseSWEComponent,
  CSAPI_CONTENT_TYPES,
  // ... (~27 values from formats/index.js)
} from './formats/index.js';

// ── Format Handler Types ───────────────────────────────────
export type {
  SensorMLProcess,
  SWEComponent,
  DataEncoding,
  // ... (~75 types from formats/index.js)
} from './formats/index.js';
````

**Key rules:**

- All paths use `.js` extensions (`'./model.js'`, NOT `'./model'`)
- Values use `export { ... }`; types use `export type { ... }`
- Does NOT export internal utilities (`scanCsapiLinks`, `formatDateTimeParameter`, etc.)
- Mirrors the exact symbols currently exported from `src/index.ts` lines 45–227

**How to build the complete export list:** The barrel file must re-export every symbol currently exported from `src/index.ts` lines 45–227. Copy each export from `index.ts`, trace it to its source in `csapi/`, and re-export from the barrel with correct relative path. The final barrel should make `src/index.ts` removing those lines a zero-breakage operation for consumers who switch to the new import path.

### 6.2 Factory Function: `csapi/factory.ts`

**Path:** `src/ogc-api/csapi/factory.ts`
**Approx Lines:** ~55

````typescript
import type OgcApiEndpoint from '../endpoint.js';
import type { OgcApiCollectionInfo } from '../model.js';
import { EndpointError } from '../../shared/errors.js';
import CSAPIQueryBuilder from './url_builder.js';
import { scanCsapiLinks } from './helpers.js';

/**
 * Creates a {@link CSAPIQueryBuilder} for constructing Connected Systems
 * query URLs against the given collection.
 *
 * This is the primary consumer API for the CSAPI module. It replaces the
 * former `endpoint.csapi()` method, moving the CSAPI creation logic from
 * the core endpoint into the CSAPI module itself.
 *
 * @param endpoint - An initialized OGC API endpoint instance.
 * @param collectionId - The collection identifier to create a builder for.
 * @returns A CSAPIQueryBuilder scoped to the specified collection.
 * @throws {EndpointError} If the endpoint does not support Connected Systems.
 *
 * @example
 * ```ts
 * import OgcApiEndpoint from '@camptocamp/ogc-client';
 * import { createCSAPIBuilder } from '@camptocamp/ogc-client/csapi';
 *
 * const endpoint = new OgcApiEndpoint('https://api.example.com');
 * const builder = await createCSAPIBuilder(endpoint, 'weather-stations');
 * const url = builder.getSystems({ bbox: [-180, -90, 180, 90], limit: 50 });
 * ```
 */
export async function createCSAPIBuilder(
  endpoint: OgcApiEndpoint,
  collectionId: string
): Promise<CSAPIQueryBuilder> {
  if (!(await endpoint.hasConnectedSystems)) {
    throw new EndpointError('Endpoint does not support Connected Systems');
  }

  const collectionDoc = await endpoint.getCollectionDocument(collectionId);
  const rootDoc = await endpoint.root;
  const links = rootDoc?.links;
  const resourceUrls = Array.isArray(links)
    ? scanCsapiLinks(links)
    : new Map<string, string>();

  return new CSAPIQueryBuilder(
    collectionDoc as unknown as OgcApiCollectionInfo,
    resourceUrls
  );
}
````

**Import pattern analysis:**

| Import                 | Type             | Direction          | Runtime?                                               |
| ---------------------- | ---------------- | ------------------ | ------------------------------------------------------ |
| `OgcApiEndpoint`       | `import type`    | CSAPI → core       | No (erased at compile)                                 |
| `OgcApiCollectionInfo` | `import type`    | CSAPI → core model | No (erased at compile)                                 |
| `EndpointError`        | `import` (value) | CSAPI → shared     | Yes — but `shared/` is common infrastructure, not core |
| `CSAPIQueryBuilder`    | `import` (value) | CSAPI → CSAPI      | Internal                                               |
| `scanCsapiLinks`       | `import` (value) | CSAPI → CSAPI      | Internal                                               |

**No runtime imports from core.** The `import type` statements are erased during TypeScript compilation, creating zero runtime dependency from CSAPI to `endpoint.ts`.

**No automatic caching.** Both `getCollectionDocument` and `root` are internally cached by the endpoint already. Consumers cache the builder themselves if needed. The `collection_id_to_csapi_builder_` cache on endpoint is removed entirely.

### 6.3 Factory Tests: `csapi/factory.spec.ts`

**Path:** `src/ogc-api/csapi/factory.spec.ts`
**Approx Lines:** ~30
**Fixture URL:** `http://local/csapi/sample-data-hub` (same fixtures as existing endpoint CSAPI tests)

Two tests, migrated and rewritten from `endpoint.spec.ts`:

| #   | Test                                           | Origin                                               | Behavior                                                                                        |
| --- | ---------------------------------------------- | ---------------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| 1   | Creates a builder for a CSAPI-capable endpoint | Migrated from `can produce a CSAPI query builder`    | Calls `createCSAPIBuilder(endpoint, 'iot-sensors')`, verifies `availableResources` is populated |
| 2   | Throws on non-CSAPI endpoint                   | Migrated from `throws an error when calling csapi()` | Calls `createCSAPIBuilder(nonCsapiEndpoint, collectionId)`, expects `EndpointError`             |

**Not migrated:** The `caches the CSAPI query builder` test (lines 2862–2869 in endpoint.spec.ts) is removed entirely — the factory has no auto-caching; this behavior no longer exists.

---

## 7. Modified File Specifications

### 7.1 `src/ogc-api/endpoint.ts`

**Current:** 896 lines → **After:** ~833 lines (−63 net)

#### Removals

| What                                                     | Location       | Lines |
| -------------------------------------------------------- | -------------- | ----- |
| `import CSAPIQueryBuilder from './csapi/url_builder.js'` | Line 52        | 1     |
| `import { scanCsapiLinks } from './csapi/helpers.js'`    | Line 53        | 1     |
| `private collection_id_to_csapi_builder_: Map<...>`      | Lines 70–71    | 2     |
| `csapi()` method + JSDoc                                 | ~Lines 363–411 | ~49   |
| `extractRootResourceUrls()` + JSDoc                      | ~Lines 424–437 | ~14   |

#### Changes

| What                        | Before                                         | After                                                                |
| --------------------------- | ---------------------------------------------- | -------------------------------------------------------------------- |
| Root accessor               | `private get root()`                           | `public get root()`                                                  |
| Collection doc method       | `private getCollectionDocument(`               | `public getCollectionDocument(`                                      |
| `hasConnectedSystems` JSDoc | `@see {@link csapi} to create a query builder` | `@see Import createCSAPIBuilder from '@camptocamp/ogc-client/csapi'` |

#### What Stays (Confirmed Safe)

- `hasConnectedSystems` getter — zero CSAPI imports, uses `info.ts` `checkHasConnectedSystems()` with conformance URIs only
- `csapiCollections` getter — zero CSAPI imports, filters collections by link relations
- All other endpoint functionality (Features, EDR, Tiles, Records, Maps, Styles, etc.)

### 7.2 `src/index.ts`

**Current:** 252 lines → **After:** ~69 lines (−183)

**Action:** Remove all CSAPI export lines (lines 45–227).

**What stays:**

- Lines 1–43: WFS, WMS, WMTS, shared model exports
- Line 44: `export * from './ogc-api/model.js'` (OGC API shared types — NOT CSAPI)
- Lines 228+: TMS, STAC, cache, shared utilities, worker exports (renumbered after removal)

**Verification:** `git grep "csapi\|CSAPI" src/index.ts` → 0 matches after removal.

**No unused imports created** — the removed lines are all re-exports (`export { ... } from '...'`), not import statements.

### 7.3 `src/ogc-api/endpoint.spec.ts`

**Current:** 2,888 lines → **After:** ~2,858 lines (−30)

**Test disposition (6 tests in CSAPI block, lines 2836–2887):**

| Test                                   | Line | Decision    | Destination                 |
| -------------------------------------- | ---- | ----------- | --------------------------- |
| `detects Connected Systems support`    | 2845 | **Stays**   | endpoint.spec.ts            |
| `can list all CSAPI collections`       | 2849 | **Stays**   | endpoint.spec.ts            |
| `can produce a CSAPI query builder`    | 2854 | **Moves**   | factory.spec.ts (rewritten) |
| `caches the CSAPI query builder`       | 2862 | **Removed** | N/A (no auto-caching)       |
| `reports no Connected Systems support` | 2877 | **Stays**   | endpoint.spec.ts            |
| `throws an error when calling csapi()` | 2881 | **Moves**   | factory.spec.ts (rewritten) |

**Remaining CSAPI block in endpoint.spec.ts (3 tests):**

```typescript
describe('OgcApiEndpoint with CSAPI', () => {
  let endpoint: OgcApiEndpoint;
  describe('nominal case', () => {
    beforeEach(() => {
      endpoint = new OgcApiEndpoint('http://local/csapi/sample-data-hub');
    });
    it('detects Connected Systems support', async () => {
      await expect(endpoint.hasConnectedSystems).resolves.toBe(true);
    });
    it('can list all CSAPI collections', async () => {
      await expect(endpoint.csapiCollections).resolves.toEqual(['iot-sensors']);
    });
  });
  describe('non-CSAPI endpoint', () => {
    beforeEach(() => {
      endpoint = new OgcApiEndpoint('http://local/sample-data/');
    });
    it('reports no Connected Systems support', async () => {
      await expect(endpoint.hasConnectedSystems).resolves.toBe(false);
    });
  });
});
```

### 7.4 `package.json`

**Two changes:**

#### 1. Add `"./csapi"` sub-path to `"exports"`

**Before:**

```json
"exports": {
  ".": {
    "types": "./dist/index.d.ts",
    "import": "./dist/dist-node.js",
    "browser": "./dist/index.js",
    "default": "./dist/dist-node.js"
  }
}
```

**After:**

```json
"exports": {
  ".": {
    "types": "./dist/index.d.ts",
    "import": "./dist/dist-node.js",
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

**Condition ordering:** `"types"` first — this is the ecosystem convention (6/6 surveyed libraries) and required by TypeScript for proper type resolution.

**Path rationale:** esbuild's per-file compilation outputs each `.ts` file to a mirror path under `dist/`. So `src/ogc-api/csapi/index.ts` compiles to `dist/ogc-api/csapi/index.js`. No build config changes needed.

#### 2. Add `"sideEffects": false`

Add at the top level of `package.json` (after `"type": "module"`):

```json
"sideEffects": false,
```

**Purpose:** Enables bundlers to tree-shake unused CSAPI exports. Critical for ensuring consumers who import only one CSAPI symbol don't bundle all format parsers.

**Worker-fallback note:** `src/index.ts` line 251 has a bare side-effect import: `import './worker-fallback/index.js'`. Risk is LOW — this import is inside the root entry point which is always evaluated when a consumer imports from `@camptocamp/ogc-client`. The `sideEffects` field mainly affects tree-shaking of unused re-exports from barrels, not bare side-effect imports inside actively-used entry points. All 5/6 surveyed libraries use plain `false`. If tests reveal breakage, the alternative is `"sideEffects": ["./dist/index.js", "./dist/worker-fallback/index.js"]`.

---

## 8. Consumer API Migration

The only user-facing change is how CSAPI functionality is accessed:

```typescript
// ──────────────────────────────────────────────────────
// BEFORE (Phase 5 — current PR state)
// ──────────────────────────────────────────────────────
import { OgcApiEndpoint } from '@camptocamp/ogc-client';
import type { System, Datastream } from '@camptocamp/ogc-client';

const endpoint = new OgcApiEndpoint('https://api.example.com');
const builder = await endpoint.csapi('weather-stations');
const url = builder.getSystems({ limit: 50 });

// ──────────────────────────────────────────────────────
// AFTER (Phase 6 — refactored)
// ──────────────────────────────────────────────────────
import { OgcApiEndpoint } from '@camptocamp/ogc-client';
import { createCSAPIBuilder } from '@camptocamp/ogc-client/csapi';
import type { System, Datastream } from '@camptocamp/ogc-client/csapi';

const endpoint = new OgcApiEndpoint('https://api.example.com');
const builder = await createCSAPIBuilder(endpoint, 'weather-stations');
const url = builder.getSystems({ limit: 50 });
```

**What does NOT change:**

- `OgcApiEndpoint` import path (still `@camptocamp/ogc-client`)
- `endpoint.hasConnectedSystems` (still works, stays on endpoint)
- `endpoint.csapiCollections` (still works, stays on endpoint)
- Direct `CSAPIQueryBuilder` construction with pre-resolved data
- All builder method signatures and return values
- All CSAPI types (same names, same shapes)

**Migration is NOT breaking** for external consumers — CSAPI has never been in a released version. PR #136 is a Draft PR. There are no external consumers to migrate.

---

## 9. Verification Plan

12 concrete gates, each with an expected output. No judgment calls.

### 9.1 Boundary Verification

| #   | Command                                                                    | Expected  | Constraint                             |
| --- | -------------------------------------------------------------------------- | --------- | -------------------------------------- |
| V1  | `git grep "from.*csapi" src/ogc-api/endpoint.ts`                           | 0 matches | No outward CSAPI imports from endpoint |
| V2  | `git grep "csapi\|CSAPI" src/index.ts`                                     | 0 matches | No CSAPI in root exports               |
| V3  | `git grep "import.*from.*csapi" -- "src/" ":!src/ogc-api/csapi/"`          | 0 matches | No outward imports (full scan)         |
| V4  | `git grep "from.*csapi" -- "src/" ":!src/ogc-api/csapi/" ":!src/index.ts"` | 0 matches | No remaining cross-boundary imports    |

### 9.2 CI Verification

| #   | Command                | Expected       |
| --- | ---------------------- | -------------- |
| V5  | `npm run format:check` | Exit code 0    |
| V6  | `npm run typecheck`    | Exit code 0    |
| V7  | `npm run lint`         | Exit code 0    |
| V8  | `npm run test:browser` | All tests pass |
| V9  | `npm run test:node`    | All tests pass |

### 9.3 Litmus Test

Verify one-way dependency — removing CSAPI entirely leaves core functional:

```bash
# Step 1: Temporarily hide CSAPI module
mv src/ogc-api/csapi src/ogc-api/_csapi_backup

# Step 2: Verify core compiles without CSAPI
# endpoint.ts has 0 imports from csapi/ → should compile
# index.ts has 0 csapi/ references → should compile
# Non-CSAPI tests should pass

# Step 3: Restore
mv src/ogc-api/_csapi_backup src/ogc-api/csapi
```

### 9.4 Diff Review

```bash
# Total diff against upstream/main
git diff --stat upstream/main..clean-pr

# Refactoring-only diff (commits 14-15)
git diff --stat HEAD~2..HEAD

# Architecture-only diff (commit 15 only — this is what jahow reviews)
git diff --stat HEAD~1..HEAD
```

---

## 10. Git Command Runbook

### 10.1 Phase 0: Preparation

```bash
# Ensure we're on phase-6 branch (CSAPI_2 repo) and clean
git checkout phase-6
git status  # Should be clean

# Verify starting state
git log --oneline -5  # Confirm HEAD is latest research commit
```

### 10.2 Phase 1: Commit 14

```bash
# Apply Prettier to all CSAPI source/test files
npx prettier --write "src/ogc-api/csapi/**/*.ts"

# Apply Prettier to CSAPI fixture JSON files
npx prettier --write "fixtures/ogc-api/csapi/**/*.json"

# Apply Prettier to endpoint.ts
npx prettier --write "src/ogc-api/endpoint.ts"

# Fix ESLint no-unused-vars errors (manual edits across 15 files)
# [See §4.2 for the 15 files and error counts]

# Verify formatting passes
npx prettier --check "src/ogc-api/csapi/**/*.ts" \
  "fixtures/ogc-api/csapi/**/*.json" "src/ogc-api/endpoint.ts"

# Verify ESLint passes
npx eslint src/ogc-api/csapi/

# Stage and commit
git add -A
git commit -m "style(csapi): apply prettier formatting and fix eslint errors
[full message per §4.4]"
```

### 10.3 Phase 2: Commit 15

```bash
# 2a. Create barrel file: src/ogc-api/csapi/index.ts
# [Contents per §6.1]

# 2b. Create factory file: src/ogc-api/csapi/factory.ts
# [Contents per §6.2]

# 2c. Create factory test file: src/ogc-api/csapi/factory.spec.ts
# [Contents per §6.3]

# 2d. Modify src/ogc-api/endpoint.ts
# [Changes per §7.1]

# 2e. Modify src/index.ts
# [Remove lines 45–227 per §7.2]

# 2f. Modify src/ogc-api/endpoint.spec.ts
# [Remove 3 tests per §7.3]

# 2g. Modify package.json
# [Add exports + sideEffects per §7.4]

# Verify all CI gates
npm run format:check
npm run typecheck
npm run lint
npm run test:browser
npm run test:node

# Stage and commit
git add -A
git commit -m "refactor(csapi): decouple from endpoint with separate entry point
[full message per §5.4]"
```

### 10.4 Phase 3: Verification and Push

```bash
# Run boundary verification (V1–V4)
git grep "from.*csapi" src/ogc-api/endpoint.ts
git grep "csapi\|CSAPI" src/index.ts
git grep "import.*from.*csapi" -- "src/" ":!src/ogc-api/csapi/"
git grep "from.*csapi" -- "src/" ":!src/ogc-api/csapi/" ":!src/index.ts"
# All should return 0 matches

# Run litmus test (§9.3)

# Review diff
git diff --stat HEAD~2..HEAD
git diff --stat HEAD~1..HEAD

# Push to phase-6 branch
git push origin phase-6
```

---

## 11. Branching Strategy and Rebase Path

### Repository Roles

| Repository           | Branch    | Role                                                                              |
| -------------------- | --------- | --------------------------------------------------------------------------------- |
| `ogc-client-CSAPI_2` | `main`    | **Archive — untouched.** Preserves complete Phase 1–5 state.                      |
| `ogc-client-CSAPI_2` | `phase-6` | **Implementation workspace.** Research docs + implementation commits.             |
| `clean-pr`           | `main`    | **Contribution-ready fork.** 13 commits above `upstream/main`, HEAD at `3061c68`. |

### Rebase Path (Post-Implementation)

```
ogc-client-CSAPI_2 phase-6 branch
  ├── Research docs (not rebased)
  └── Implementation commits 14, 15 (code changes only)
              ↓
        Cherry-pick or rebase implementation commits to clean-pr
              ↓
        clean-pr: 15 commits total (13 existing + 2 new)
              ↓
        git push --force-with-lease clean-fork clean-pr
              ↓
        PR #136 updated → Draft PR ready for jahow
```

**Key points:**

- Research documents stay on `phase-6` — they are NOT rebased to `clean-pr`
- Only code-change commits (14 + 15) move to `clean-pr`
- `--force-with-lease` prevents accidental overwrites
- Create `pre-refactor-backup` tag on `clean-pr` before force-push

### Point-of-No-Return Checklist

Before force-pushing to `clean-fork/clean-pr`:

- [ ] All V1–V9 verification gates pass
- [ ] Litmus test passes (§9.3)
- [ ] `pre-refactor-backup` tag exists on old `clean-pr` HEAD
- [ ] `git log --oneline upstream/main..clean-pr` shows exactly 15 commits
- [ ] Architecture diff (`HEAD~1..HEAD`) shows only expected files
- [ ] PR description updated to reflect new consumer API

---

## 12. Risk Register

| #   | Risk                                                     | Likelihood | Impact | Mitigation                                                                              | Rollback                                           |
| --- | -------------------------------------------------------- | ---------- | ------ | --------------------------------------------------------------------------------------- | -------------------------------------------------- |
| 1   | Line numbers shift after Prettier                        | Certain    | Low    | Apply formatting FIRST (Commit 14), base architecture on formatted code                 | N/A — ordering prevents this                       |
| 2   | TypeScript fails after removing CSAPI from index.ts      | Low        | High   | Create barrel file in SAME commit as removal                                            | `git reset --hard HEAD~1`                          |
| 3   | Factory tests use incorrect fixtures                     | Low        | Low    | Use same fixture URLs as existing endpoint tests                                        | Fix fixture paths                                  |
| 4   | Force-push overwrites remote changes                     | Low        | High   | `pre-refactor-backup` tag + `--force-with-lease`                                        | `git push clean-fork pre-refactor-backup:clean-pr` |
| 5   | Prettier reformats new files unexpectedly                | Low        | Low    | Write new files Prettier-compliant from start                                           | `npx prettier --write <file>`                      |
| 6   | `url_builder.spec.ts` formatting diff surprises reviewer | Certain    | Low    | Note in commit message (55% of formatting diff)                                         | N/A — informational                                |
| 7   | `"sideEffects": false` breaks worker-fallback            | Low        | Medium | Tests will catch immediately. Alternative: `"sideEffects": ["./dist/index.js"]`         | Revert to array form                               |
| 8   | `getCollectionDocument` public exposes internal API      | Low        | Low    | Already used by multiple internal features — it's a general-purpose method              | Can revert to private if needed                    |
| 9   | ESLint fixes accidentally change behavior                | Near-zero  | High   | All fixes are `no-unused-vars` — removing unused imports cannot change runtime behavior | Review each removal                                |

---

## 13. Scope Boundaries

### In Scope

| Item                                       | Justification                               |
| ------------------------------------------ | ------------------------------------------- |
| Remove CSAPI exports from `index.ts`       | Directly required by jahow                  |
| Create barrel file `csapi/index.ts`        | Required for `./csapi` sub-path entry point |
| Add `"./csapi"` to `package.json` exports  | Directly required by jahow                  |
| Add `"sideEffects": false`                 | Enables tree-shaking (1 line)               |
| Remove 2 CSAPI imports from `endpoint.ts`  | Directly required by jahow                  |
| Remove `csapi()` method and related code   | Enables import removal                      |
| Create `createCSAPIBuilder` factory        | Replacement API for removed `csapi()`       |
| Make `root`/`getCollectionDocument` public | Factory needs access (1-word each)          |
| Create `factory.spec.ts`                   | Tests for new code                          |
| Migrate 3 endpoint tests                   | Tests reference removed method              |
| Apply Prettier to 51 files                 | CI compliance                               |
| Fix 99 ESLint errors                       | CI compliance                               |

### Out of Scope (Deferred)

| Item                                              | Why Not                                                                        |
| ------------------------------------------------- | ------------------------------------------------------------------------------ |
| ESLint `import/no-restricted-paths` boundary rule | Enforcement, not requirement. jahow didn't ask for it                          |
| Custom boundary integration test                  | Enforcement tooling — `git grep` verification suffices                         |
| TypeScript Project References                     | Heavyweight for one sub-module. No surveyed library uses this for one sub-path |
| `typesVersions` fallback                          | 5/6 libraries skip it. Only needed for TypeScript <4.7                         |
| Move CSAPI MIME functions from `shared/`          | Constraint 3 does not apply to `shared/` utilities                             |
| Generalized link scanner utility                  | Problem self-resolves with factory pattern (Plan 06)                           |
| Any CSAPI business logic changes                  | Zero changes — types, builders, parsers all preserved                          |

---

## 14. Research Foundation

Phase 6 is backed by an 8-plan research arc. Each plan investigated a specific aspect of the refactoring. The findings are consolidated into an executable implementation specification in [Plan 08](../../research/phase-6/findings/08-file-level-changelist-and-commit-strategy.md).

| Plan | Title                                    | Questions | Key Decision                                                                           |
| ---- | ---------------------------------------- | --------- | -------------------------------------------------------------------------------------- |
| 01   | Build System & Entry Point Analysis      | 31        | No build config changes needed; esbuild per-file output covers CSAPI                   |
| 02   | EDR Integration Pattern Analysis         | 35        | EDR is accepted precedent; `hasConnectedSystems`/`csapiCollections` follow EDR pattern |
| 03   | Separate Entry Point Design Patterns     | 35        | 4-condition `"exports"` + barrel + `"sideEffects": false`; 6 library survey            |
| 04   | Sub-Module API Design Patterns           | 38        | Two-layer API: sync constructor + async factory; 7 library survey                      |
| 05   | Module Decoupling Patterns               | 37        | Level 3.5 coupling (`Pick<>` + `import type`); one-shot extraction                     |
| 06   | Endpoint Decoupling Architecture         | 42        | Factory signature, barrel contents, test migration, public method changes              |
| 07   | Prettier & ESLint Configuration Analysis | 27        | Format First strategy; 46 files need Prettier; 99 ESLint errors                        |
| 08   | File-Level Changelist & Commit Strategy  | 40        | Complete implementation spec: 2 commits, 7 files, 12 gates                             |

**Total: 285 questions answered, ~8,000 lines of findings.**

All findings available at [`docs/research/phase-6/findings/`](../../research/phase-6/findings/).

**Supplementary documents:**

- [P6 Contribution Goal and Definition](P6-contribution-goal-and-definition.md) — Phase 6 scope, acceptance criteria, and success condition
- [Deferred Issues Scope Assessment](../../research/phase-6/deferred-issues-scope-assessment.md) — 5 deferred issues evaluated, all remain deferred
- [Implementation Readiness Recommendation](../../research/phase-6/implementation-readiness-recommendation.md) — Rationale for proceeding with implementation
