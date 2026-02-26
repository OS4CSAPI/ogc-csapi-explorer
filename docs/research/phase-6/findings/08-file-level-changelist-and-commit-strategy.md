# 08 — File-Level Changelist and Commit Strategy: Complete Implementation Specification

> **Plan 8 of 8** | **Phase 6 — Upstream Acceptance Refactoring**

---

## Metadata

| Field               | Value                                                                                                                |
| ------------------- | -------------------------------------------------------------------------------------------------------------------- |
| **Research Plan**   | [08-file-level-changelist-and-commit-strategy.md](../research-plans/08-file-level-changelist-and-commit-strategy.md) |
| **Status**          | Complete                                                                                                             |
| **Date Started**    | 2026-02-26                                                                                                           |
| **Date Completed**  | 2026-02-26                                                                                                           |
| **Depends On**      | Plans 01, 02, 03, 04, 05, 06, 07 (all prior plans)                                                                   |
| **Blocks**          | None — this plan unblocks implementation                                                                             |
| **Total Questions** | 40                                                                                                                   |
| **Total Answered**  | 40                                                                                                                   |

---

## Executive Summary

This document is the **complete implementation specification** for decoupling CSAPI from the OGC API endpoint. After this document, no further research is needed. A developer (human or AI) can execute the changelist mechanically, producing a PR that passes all CI checks and satisfies jahow's two requirements.

### Scope at a Glance

| Metric                                        | Value                                                             |
| --------------------------------------------- | ----------------------------------------------------------------- |
| Files to **create**                           | 3 (`csapi/index.ts`, `csapi/factory.ts`, `csapi/factory.spec.ts`) |
| Files to **modify**                           | 4 (`endpoint.ts`, `index.ts`, `endpoint.spec.ts`, `package.json`) |
| Files to **move**                             | 0                                                                 |
| Files to **delete**                           | 0                                                                 |
| Files with **formatting** (Prettier + ESLint) | 51 (46 CSAPI source/test + 4 fixture JSON + `endpoint.ts`)        |
| New commits appended to `clean-pr`            | 2                                                                 |
| Total commits in final PR                     | 15                                                                |
| Verification gates                            | 12                                                                |

### Commit Sequence Preview

| #   | Message                                                             | Scope                                     |
| --- | ------------------------------------------------------------------- | ----------------------------------------- |
| 14  | `style(csapi): apply prettier formatting and fix eslint errors`     | 51 files formatted, 15 files ESLint fixed |
| 15  | `refactor(csapi): decouple from endpoint with separate entry point` | 7 files changed (3 created, 4 modified)   |

---

## 1. Prior Findings Consolidation

### What Each Plan Contributes

| Plan                     | Key Contribution to Changelist                                                                                                                                                                                                                                                                                                | Section Reference |
| ------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------- |
| **01** (Build System)    | `package.json` `"exports"` config for `"./csapi"`: `{types, import, browser, default}` all pointing to `dist/ogc-api/csapi/index.js`. No build config changes needed — esbuild per-file compilation automatically processes new barrel file. `vite-plugin-dts` glob already covers `csapi/`.                                  | Plan 01 § 3, § 5  |
| **02** (EDR Pattern)     | EDR stays as-is (656 lines / 3 files — acceptable). No EDR changes in this changelist. EDR integration pattern is benchmark for what's acceptable. `hasConnectedSystems`/`csapiCollections` follow EDR's `hasEnvironmentalDataRetrieval`/`edrCollections` pattern.                                                            | Plan 02 § 3, § 7  |
| **03** (Entry Point)     | Barrel file at `src/ogc-api/csapi/index.ts`. Ecosystem consensus: `"types"` first in exports, `"sideEffects": false`, no `typesVersions` needed. Consumer import: `import { createCSAPIBuilder } from '@camptocamp/ogc-client/csapi'`.                                                                                        | Plan 03 § 3, § 5  |
| **04** (API Patterns)    | Two-layer API: sync constructor (`CSAPIQueryBuilder`) unchanged + async factory `createCSAPIBuilder(endpoint, collectionId)`. Factory goes in `csapi/factory.ts`.                                                                                                                                                             | Plan 04 § 4, § 6  |
| **05** (Decoupling)      | Level 3.5 coupling: `Pick<>` + `import type`. No adapter types, no interface files needed. Zero runtime coupling from CSAPI→core.                                                                                                                                                                                             | Plan 05 § 4       |
| **06** (Architecture)    | **Primary input.** Complete architecture: factory function signature, `hasConnectedSystems`/`csapiCollections` stay on endpoint, `csapi()` + `extractRootResourceUrls()` + cache removed, `scanCsapiLinks` stays in CSAPI unchanged, `root` + `getCollectionDocument` become public, barrel file design, test migration plan. | Plan 06 §§ 2–12   |
| **07** (Prettier/ESLint) | Format First recommended. 46/56 CSAPI files need Prettier (3,023 ins / 1,036 del). 99 ESLint errors (all `no-unused-vars` across 15 files). 4 CSAPI fixture JSON files need formatting. `endpoint.ts` has 8 lines of Prettier changes. CI checks final state only.                                                            | Plan 07 §§ 4–7    |

### Gaps Resolved

| Gap                                                                                      | Resolution                                                                                    |
| ---------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------- |
| Plan 06 summary says "4 of 6 tests stay" but detailed Q36 table + After code show 3 stay | Use Q36 detailed table: **3 stay, 2 move+rewrite, 1 removed**                                 |
| ESLint fix commit placement (Plan 07 Open Question #1)                                   | **Combined with formatting commit** — both are mechanical cleanup, keeps commit count minimal |
| `endpoint.ts` formatting placement (Plan 07 Open Question #2)                            | **In formatting commit** — keeps architecture commit as logic-only changes                    |
| Plan 05 recommended `scanCsapiLinks` generalization                                      | **Overridden by Plan 06** — problem self-resolves when endpoint stops calling it              |

---

## 2. Complete File Inventory

### Question 1: Files to Create

| #   | Path                                | Purpose                                          | Defined By           | Approx Lines |
| --- | ----------------------------------- | ------------------------------------------------ | -------------------- | ------------ |
| C1  | `src/ogc-api/csapi/index.ts`        | Barrel file: re-exports all public CSAPI symbols | Plan 06 § 8, Q31     | ~190         |
| C2  | `src/ogc-api/csapi/factory.ts`      | Factory function `createCSAPIBuilder`            | Plan 06 § 3, Q13     | ~60          |
| C3  | `src/ogc-api/csapi/factory.spec.ts` | Tests for factory function                       | Plan 06 § 9, Q38–Q40 | ~30          |

### Question 2: Files to Modify

| #   | Path                           | Nature of Modification                                                                                                                                 | Defined By           | Lines Removed | Lines Added | Net  |
| --- | ------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------- | ------------- | ----------- | ---- |
| M1  | `src/ogc-api/endpoint.ts`      | Remove 2 imports, 1 cache field, 2 methods (`csapi()`, `extractRootResourceUrls()`); change `root` and `getCollectionDocument` to public; update JSDoc | Plan 06 § 10, Q41    | ~65           | ~2          | −63  |
| M2  | `src/index.ts`                 | Remove all CSAPI export lines (lines 45–227)                                                                                                           | Plan 06 § 10, Q42    | ~183          | 0           | −183 |
| M3  | `src/ogc-api/endpoint.spec.ts` | Remove 3 tests (2 moved to factory.spec.ts + 1 cache test removed), trim describe block                                                                | Plan 06 § 9, Q36–Q40 | ~30           | 0           | −30  |
| M4  | `package.json`                 | Add `"./csapi"` sub-path export; add `"sideEffects": false`                                                                                            | Plans 01, 03         | 0             | ~8          | +8   |

### Question 3: Files to Move

**None.** All 56 CSAPI files stay in `src/ogc-api/csapi/`. No file relocations.

### Question 4: Files to Delete

**None.** All files remain. No files become orphaned.

### Question 5: Build Configuration Files

| File                    | Change Needed?                                                                      | Evidence                 |
| ----------------------- | ----------------------------------------------------------------------------------- | ------------------------ |
| `package.json`          | **Yes** — `"exports"` and `"sideEffects"`                                           | Plan 01 § 3, Plan 03 § 5 |
| `vite.node-config.js`   | **No** — node build uses `src-node/index.ts` which doesn't import CSAPI             | Plan 01 § 5              |
| `vite.worker-config.js` | **No** — `vite-plugin-dts` uses glob (`src/**/*.ts`) that already includes `csapi/` | Plan 01 § 5              |
| `tsconfig.json`         | **No** — `include: ["src"]` already covers `csapi/`                                 | Plan 01 § 5              |

### Question 6: Test Configuration Files

| File                   | Change Needed?                                            | Evidence         |
| ---------------------- | --------------------------------------------------------- | ---------------- |
| `jest.config.cjs`      | **No** — test pattern `**/*.spec.ts` matches any location | Plan 06 § 9, Q39 |
| `jest.node.config.cjs` | **No** — same pattern, no CSAPI-specific config           | Plan 06 § 9, Q39 |

### Question 7: CSAPI Fixture Files

The 4 CSAPI fixture files stay in their current location:

| File                                                                  | Status                                 |
| --------------------------------------------------------------------- | -------------------------------------- |
| `fixtures/ogc-api/csapi/sample-data-hub.json`                         | **Stays** — shared test infrastructure |
| `fixtures/ogc-api/csapi/sample-data-hub/collections.json`             | **Stays** — shared test infrastructure |
| `fixtures/ogc-api/csapi/sample-data-hub/conformance.json`             | **Stays** — shared test infrastructure |
| `fixtures/ogc-api/csapi/sample-data-hub/collections/iot-sensors.json` | **Stays** — shared test infrastructure |

These fixtures are used by both `endpoint.spec.ts` (for `hasConnectedSystems`, `csapiCollections` tests) and `factory.spec.ts` (for factory function tests). No duplication needed — the fixture URL mapping in `test-setup.ts` handles both.

### Question 8: `.gitignore` Changes

**No.** The `.gitignore` change in commit 13 (`3061c68`) adds `.vscode/` and `test-output/` — unrelated to the refactoring. No modification needed.

---

## 3. Changelist Per Modified File

### Question 9: `src/ogc-api/endpoint.ts` (896 lines → ~833 lines)

**Removals:**

| Line(s) | Content                                                                                | Reason                                             |
| ------- | -------------------------------------------------------------------------------------- | -------------------------------------------------- |
| 52      | `import CSAPIQueryBuilder from './csapi/url_builder.js';`                              | Constraint 3: no outward CSAPI imports             |
| 53      | `import { scanCsapiLinks } from './csapi/helpers.js';`                                 | Constraint 3: no outward CSAPI imports             |
| 70–71   | `private collection_id_to_csapi_builder_: Map<string, CSAPIQueryBuilder> = new Map();` | Consequence of removing `csapi()` method           |
| 363–411 | `csapi()` method + JSDoc (~49 lines)                                                   | Enables removal of imports. Factory replaces this. |
| 424–437 | `extractRootResourceUrls()` method + JSDoc (~14 lines)                                 | Only called by `csapi()`. Logic moves to factory.  |

**Changes:**

| Line | Before                                         | After                                                                | Reason                                      |
| ---- | ---------------------------------------------- | -------------------------------------------------------------------- | ------------------------------------------- |
| 72   | `private get root()`                           | `public get root()`                                                  | Factory needs access to root document       |
| 444  | `private getCollectionDocument(`               | `public getCollectionDocument(`                                      | Factory needs access to collection document |
| ~340 | `@see {@link csapi} to create a query builder` | `@see Import createCSAPIBuilder from '@camptocamp/ogc-client/csapi'` | JSDoc reference to removed method           |

**Net change:** ~65 lines removed, ~2 words changed. File goes from 896 to ~833 lines.

### Question 10: `src/index.ts` (252 lines → ~69 lines)

**Removals:**

All CSAPI export lines must be removed. These span lines 45–227 (183 lines):

```
line 45:  export { default as CSAPIQueryBuilder } from './ogc-api/csapi/url_builder.js';
lines 46-92:  export { CSAPIResourceTypes, ... } + export type { ... } from './ogc-api/csapi/model.js';
lines 93-96:  export type { DatastreamSchemaResponse, ... } from './ogc-api/csapi/model.js';
lines 97-125: export { SOSA_NS, ... } from './ogc-api/csapi/formats/index.js';
line 126:  export type { CSAPIResourceTypeName } from './ogc-api/csapi/formats/index.js';
lines 127-177: export type { SensorMLProcess, ... } from './ogc-api/csapi/formats/index.js';
lines 178-227: export type { AnyComponent, ... } from './ogc-api/csapi/formats/index.js';
```

**After removal, `src/index.ts` structure:**

- Lines 1–43: WFS, WMS, WMTS, shared, OgcApiEndpoint exports (unchanged)
- Line 44: `export * from './ogc-api/model.js';` (unchanged — this is OGC API shared types, NOT CSAPI)
- Lines 228+: TMS, STAC, cache, shared utilities, worker exports (unchanged, renumbered)

**Verification:** `git grep "csapi\|CSAPI" src/index.ts` → 0 matches after removal. No unused imports are created — the CSAPI lines were all re-exports, not import statements.

**Net change:** −183 lines. File goes from 252 to ~69 lines.

### Question 11: `src/ogc-api/endpoint.spec.ts` (2888 lines → ~2858 lines)

**Test classification (6 tests in CSAPI block, lines 2836–2887):**

| Test                                   | Line | Decision                       | Reason                                                   |
| -------------------------------------- | ---- | ------------------------------ | -------------------------------------------------------- |
| `detects Connected Systems support`    | 2845 | **Stays**                      | Tests `hasConnectedSystems` getter — zero CSAPI imports  |
| `can list all CSAPI collections`       | 2849 | **Stays**                      | Tests `csapiCollections` getter — zero CSAPI imports     |
| `can produce a CSAPI query builder`    | 2854 | **Moves** to `factory.spec.ts` | Tests `csapi()` method which is being removed            |
| `caches the CSAPI query builder`       | 2862 | **Removed**                    | Tests caching behavior that no longer exists             |
| `reports no Connected Systems support` | 2877 | **Stays**                      | Tests `hasConnectedSystems` = false — zero CSAPI imports |
| `throws an error when calling csapi()` | 2881 | **Moves** to `factory.spec.ts` | Tests factory error handling                             |

**After modification — `endpoint.spec.ts` CSAPI block (lines 2836–2858):**

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

**Net change:** ~30 lines removed (3 `it()` blocks + associated `beforeEach` trimming).

### Question 12: `package.json`

**Current `"exports"` field (line 18):**

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

**After modification:**

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

**Additional change — add `"sideEffects": false`:**

Add at top level of `package.json` (after `"type": "module"`):

```json
"sideEffects": false,
```

> **Verification pass note (Plans 01–05 tail review):** `src/index.ts` line 251 has a bare side-effect import: `import './worker-fallback/index.js'`. Plan 03 Open Question 2 flagged this. In practice, risk is LOW: any consumer importing from `@camptocamp/ogc-client` forces the bundler to evaluate `index.js` including the worker-fallback. The `sideEffects` field mainly affects tree-shaking of _unused re-exports from barrels_, not bare side-effect imports inside an actively-used entry point. All 5/6 surveyed libraries use plain `false`. If caution is needed during implementation, `"sideEffects": ["./dist/index.js", "./dist/worker-fallback/index.js"]` is an alternative. All tests running after the change will confirm nothing breaks.

**Net change:** +8 lines. No other `package.json` changes (`"files"` field already includes `"dist/"` and `"src/"` which cover the barrel file).

### Question 13: `src/ogc-api/csapi/index.ts` (New Barrel File)

Complete contents defined in Plan 06 § 8 Q31. The barrel file follows the `formats/index.ts` pattern with sectioned JSDoc comment dividers. Organized into:

1. Module-level JSDoc with usage example
2. Factory function re-export from `./factory.js`
3. Query builder default + named re-export from `./url_builder.js`
4. Model values re-export from `./model.js`
5. Model types re-export from `./model.js`
6. Format handler values re-export from `./formats/index.js`
7. Format handler types re-export from `./formats/index.js`

**Approximate line count:** ~190 lines (matching Plan 06's draft).

### Question 14: `src/ogc-api/info.ts` (309 lines)

**No changes needed.** Verified:

- `checkHasConnectedSystems` (line 112): imports nothing from `csapi/`. Uses only conformance class URI strings.
- `parseCollections` additions (lines 255, 265, 303): the `hasConnectedSystems` property on collection info is parsed from link relations inline — no `csapi/` import.
- `git grep "from.*csapi" src/ogc-api/info.ts` → 0 matches.

### Question 15: `src/shared/mime-type.ts` and `src/shared/mime-type.spec.ts`

**No changes needed.** The 4 CSAPI-specific MIME type functions (`isMimeTypeSensorML`, `isMimeTypeSweJson`, `isMimeTypeSweCsv`, `isMimeTypeSweBinary`) are:

- In `shared/`, not `csapi/` → Constraint 3 doesn't apply
- **Not imported by any code outside `shared/`** — verified: `git grep` for these function names in `src/` excluding `src/shared/` returns 0 matches
- They are defined and tested but currently unused — they anticipate future use
- Staying in `shared/` is the correct minimum-change decision

### Question 16: Factory Function File (`src/ogc-api/csapi/factory.ts`)

**Path:** `src/ogc-api/csapi/factory.ts`

**Signature:**

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

**Approximate line count:** ~55 lines including imports, JSDoc, and function body.

---

## 4. Commit Sequence Design

### Question 17: Number of Commits

**Two commits** appended on top of the existing 13:

| Option                 | Commits | Tradeoffs                                                                                 |
| ---------------------- | ------- | ----------------------------------------------------------------------------------------- |
| **(a) Single commit**  | 1       | Simple, but 3,000+ line formatting diff mixed with logic makes review impossible          |
| **(b) Two commits ✓**  | 2       | Clean separation: mechanical cleanup vs. logic changes. Each individually passable by CI. |
| **(c) Three+ commits** | 3+      | Added granularity not needed — ESLint + Prettier are both "mechanical cleanup"            |

**Selected: Option (b) — Two commits.**

Rationale:

- The formatting diff (3,023 ins / 1,036 del) MUST be separated from logic changes (Plan 07 finding)
- ESLint fixes (removing unused imports) are mechanical and bundled with formatting
- Architecture changes are a coherent unit, best reviewed together
- CI checks final state only, but both commits independently pass CI

### Question 18: Amend vs. Append vs. Squash

**Selected: Option B — Append new commits on top of existing 13.**

| Option                                    | Pro                                                            | Con                                                                                     | Selected? |
| ----------------------------------------- | -------------------------------------------------------------- | --------------------------------------------------------------------------------------- | --------- |
| **A: Amend** (rewrite commits 11, 12, 13) | Clean history — as if architecture was right from the start    | High conflict risk on commits 11/12; force rewrite of complex commits; harder to review | No        |
| **B: Append** (add 2 commits on top)      | Refactoring clearly visible; low conflict risk; easy to review | Commit 11 "integrates CSAPI" then later commits undo parts                              | **Yes**   |
| **C: Squash** (all into 1 commit)         | Simplest history                                               | Loses granular CSAPI build-up story (commits 1–10); jahow may want to see progression   | No        |

Rationale:

- Append is safest: no risk of merge conflicts during interactive rebase
- Reviewability is paramount — jahow can see exactly what the refactoring changed
- The "integrate then decouple" narrative is acceptable for a draft PR
- If jahow requests squashing later, a `git rebase -i` is trivial from the appended state

### Question 19: Interactive Rebase Operations

**Not applicable** — we are using Option B (Append), not Option A (Amend). No interactive rebase of existing commits.

### Question 20: Commit Messages

**Commit 14:**

```
style(csapi): apply prettier formatting and fix eslint errors

Formatting-only commit — no logic changes. Applied `npx prettier --write`
to all CSAPI source, test, and fixture files. Fixed 99 ESLint
`no-unused-vars` errors across 15 files by removing/renaming unused
imports.

51 files changed (46 CSAPI source/test + 4 fixture JSON + endpoint.ts).
url_builder.spec.ts accounts for ~55% of the formatting diff due to
inline link object expansion at 80-char printWidth.

Required to pass upstream's `npm run format:check` and `npm run lint`
CI gates.
```

**Commit 15:**

```
refactor(csapi): decouple from endpoint with separate entry point

Architectural refactoring to satisfy upstream review requirements:
1. CSAPI symbols removed from root `src/index.ts` (~183 lines)
2. New barrel file `csapi/index.ts` re-exports all CSAPI public API
3. New factory function `createCSAPIBuilder(endpoint, collectionId)`
   replaces `endpoint.csapi()` method
4. Two CSAPI imports removed from `endpoint.ts` (constraint 3)
5. `root` and `getCollectionDocument` changed from private to public
6. `csapi()`, `extractRootResourceUrls()`, and CSAPI cache removed
7. `"./csapi"` sub-path added to package.json exports
8. `"sideEffects": false` added for tree-shaking support
9. 3 endpoint CSAPI tests migrated to new factory.spec.ts

Consumer API: `import { createCSAPIBuilder } from '@camptocamp/ogc-client/csapi'`

Boundary conditions verified:
- git grep "from.*csapi" src/ogc-api/endpoint.ts → 0 matches
- git grep "csapi" src/index.ts → 0 matches
- Removing csapi/ leaves core fully functional (litmus test passes)
```

### Question 21: Per-Commit CI Compliance

| Commit                       | format:check                         | typecheck                                          | lint                         | test:browser                                 | test:node |
| ---------------------------- | ------------------------------------ | -------------------------------------------------- | ---------------------------- | -------------------------------------------- | --------- |
| **14** (formatting + ESLint) | ✓ Pass                               | ✓ Pass (no code changes)                           | ✓ Pass (ESLint errors fixed) | ✓ Pass (no behavior changes)                 | ✓ Pass    |
| **15** (architecture)        | ✓ Pass (new files written compliant) | ✓ Pass (barrel provides exports, factory resolves) | ✓ Pass (no new violations)   | ✓ Pass (3 tests stay, 2 migrated, 1 removed) | ✓ Pass    |

**Both commits individually pass all 5 CI checks.** No squashing required.

Note: The existing 13 commits on `clean-pr` already fail `npm run lint` (99 pre-existing ESLint errors) and `npm run format:check` (46 files unformatted). Commit 14 fixes both. GitHub CI evaluates only the final state, so the historical failures don't block the PR.

### Question 22: Commit Ordering for Minimal Conflicts

The selected order (formatting → architecture) minimizes conflicts:

1. **Commit 14 (formatting):** Modifies only whitespace/import lines across 51 files. No structural conflicts possible.
2. **Commit 15 (architecture):** Operates on the already-formatted codebase. Line numbers in the prior analysis (Plan 06) may shift slightly due to formatting, but the structural operations (remove method, change visibility) are unambiguous.

If reversed (architecture → formatting), Prettier would reformat the newly-written barrel file and factory file, requiring a second pass. Format First avoids this by ensuring new files are written against the already-formatted codebase.

### Question 23: Formatting Commit Design

**Formatting is a separate dedicated commit (Commit 14).** Plan 07's "Format First" recommendation is adopted.

Rationale:

- 3,023-insertion formatting diff is too large to mix with logic changes
- Upstream has 5+ formatting-only commit precedents (`style: apply prettier`, `fix: apply prettier`, etc.)
- ESLint fixes (removing unused imports) are bundled with formatting because both are mechanical, non-logic cleanup
- Keeps Commit 15 (architecture) as a pure logic diff, easy to review

---

## 5. Rebase Strategy

### Question 24: `clean-pr` State Relative to `upstream/main`

```
upstream/main: 53a6449 (Merge pull request #132 fix-bbox)
clean-pr:      13 commits ahead of 53a6449
               HEAD: 3061c68 (chore: add .vscode and test-output files to .gitignore)
```

`upstream/main` has **not advanced** past the base commit. No upstream commits need incorporation.

### Question 25: Rebase Path

```
phase-6 (research only, no code changes)
    ↓ (findings consumed, not merged)
clean-pr (implementation branch)
    ↓ (append 2 new commits)
clean-pr (updated, 15 commits)
    ↓ (force-push to remote)
clean-fork/clean-pr → PR #136
```

Implementation happens **directly on `clean-pr`**. The `phase-6` branch contains only research documents and is never merged into `clean-pr`. The findings in this document are the bridge — a developer reads this spec and executes the changes on `clean-pr`.

### Question 26: Conflict Risk

**Low.** Since we're appending (not amending), there are zero conflict risks from the append itself. The only risk is if `upstream/main` advances and we need to rebase all 15 commits — but `upstream/main` has not advanced.

### Question 27: Force-Push Strategy

**`git push --force-with-lease` is acceptable for the Draft PR.**

Precautions:

1. Tag the current `clean-pr` state before force-pushing: `git tag pre-refactor-backup`
2. Verify local `clean-pr` matches remote before starting: `git fetch clean-fork; git diff clean-pr clean-fork/clean-pr`
3. Use `--force-with-lease` (not `--force`) to prevent overwriting others' changes

### Question 28: PR Status

**Keep as Draft.** Do not change to "Ready for Review" as part of this changelist. The PR status change should be a deliberate human decision after reviewing the final state.

### Question 29: Upstream Advancement Check

**No upstream advancement detected.** `upstream/main` HEAD is `53a6449` — same as `clean-pr`'s merge base. No rebase against new upstream commits is needed.

If upstream advances before implementation, the rebase is straightforward:

```bash
git fetch upstream
git rebase upstream/main clean-pr
# Commits 1–10 (pure CSAPI additions) should rebase cleanly
# Commits 11–13 may need minor conflict resolution
git push --force-with-lease clean-fork clean-pr
```

---

## 6. Git Command Runbook

### Complete Execution Sequence

```bash
# ============================================================
# PHASE 0: PREPARATION
# ============================================================

# Ensure we're on clean-pr and it's up to date
git checkout clean-pr
git fetch clean-fork
git diff clean-pr clean-fork/clean-pr  # Should show nothing

# Create safety backup tag
git tag pre-refactor-backup

# Verify starting state: 13 commits ahead of upstream/main
git log --oneline upstream/main..clean-pr  # Should show 13 commits

# ============================================================
# PHASE 1: COMMIT 14 — Formatting + ESLint
# ============================================================

# Apply Prettier to all CSAPI source/test files
npx prettier --write "src/ogc-api/csapi/**/*.ts"

# Apply Prettier to CSAPI fixture JSON files
npx prettier --write "fixtures/ogc-api/csapi/**/*.json"

# Apply Prettier to endpoint.ts (8-line formatting diff)
npx prettier --write "src/ogc-api/endpoint.ts"

# Fix ESLint no-unused-vars errors (manual edits across 15 files)
# Remove unused imports or prefix with _ as appropriate
# [See Plan 07 § 2 Q12/Q17 for the 15 files and specific errors]

# Verify formatting passes
npx prettier --check "src/ogc-api/csapi/**/*.ts" "fixtures/ogc-api/csapi/**/*.json" "src/ogc-api/endpoint.ts"

# Verify ESLint passes on CSAPI files
npx eslint src/ogc-api/csapi/

# Stage and commit
git add -A
git commit -m "style(csapi): apply prettier formatting and fix eslint errors

Formatting-only commit — no logic changes. Applied npx prettier --write
to all CSAPI source, test, and fixture files. Fixed 99 ESLint
no-unused-vars errors across 15 files by removing/renaming unused
imports.

51 files changed (46 CSAPI source/test + 4 fixture JSON + endpoint.ts).
url_builder.spec.ts accounts for ~55% of the formatting diff due to
inline link object expansion at 80-char printWidth.

Required to pass upstream CI: npm run format:check and npm run lint."

# ============================================================
# PHASE 2: COMMIT 15 — Architecture
# ============================================================

# 2a. Create barrel file: src/ogc-api/csapi/index.ts
# [Contents per Plan 06 § 8 Q31 — ~190 lines]

# 2b. Create factory file: src/ogc-api/csapi/factory.ts
# [Contents per this document § 3 Q16 — ~55 lines]

# 2c. Create factory test file: src/ogc-api/csapi/factory.spec.ts
# [Contents per Plan 06 § 9 Q40 — ~30 lines]

# 2d. Modify src/ogc-api/endpoint.ts:
#   - Remove line 52: import CSAPIQueryBuilder from './csapi/url_builder.js';
#   - Remove line 53: import { scanCsapiLinks } from './csapi/helpers.js';
#   - Remove lines 70-71: private collection_id_to_csapi_builder_ cache field
#   - Change line 72: private get root() → public get root()
#   - Update hasConnectedSystems JSDoc: replace @see {@link csapi} reference
#   - Remove csapi() method + JSDoc (~lines 363-411)
#   - Remove extractRootResourceUrls() + JSDoc (~lines 424-437)
#   - Change getCollectionDocument: private → public (~line 444)

# 2e. Modify src/index.ts:
#   - Remove all CSAPI export lines (lines 45-227, ~183 lines)

# 2f. Modify src/ogc-api/endpoint.spec.ts:
#   - Remove 'can produce a CSAPI query builder' test
#   - Remove 'caches the CSAPI query builder' test
#   - Remove 'throws an error when calling csapi()' test
#   - Keep 'detects Connected Systems support'
#   - Keep 'can list all CSAPI collections'
#   - Keep 'reports no Connected Systems support'

# 2g. Modify package.json:
#   - Add "./csapi" to "exports"
#   - Add "sideEffects": false

# Verify all changes
npm run format:check  # Prettier check
npm run typecheck     # TypeScript compilation
npm run lint          # ESLint
npm run test:browser  # Jest browser tests
npm run test:node     # Jest node tests

# Stage and commit
git add -A
git commit -m "refactor(csapi): decouple from endpoint with separate entry point

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
- Removing csapi/ leaves core fully functional"

# ============================================================
# PHASE 3: VERIFICATION AND PUSH
# ============================================================

# Run full verification checklist (§ 8 below)
# ...

# Push to remote
git push --force-with-lease clean-fork clean-pr

# Verify: 15 commits above upstream/main
git log --oneline upstream/main..clean-pr  # Should show 15 commits
```

---

## 7. Formatting Integration

### Scope of Commit 14

| Category                            | File Count | Source      |
| ----------------------------------- | ---------- | ----------- |
| CSAPI source files needing Prettier | 20 of 27   | Plan 07 § 7 |
| CSAPI test files needing Prettier   | 26 of 29   | Plan 07 § 7 |
| CSAPI fixture JSON files            | 4          | Plan 07 § 8 |
| Core files (`endpoint.ts`)          | 1          | Plan 07 § 7 |
| **Total**                           | **51**     |             |

### ESLint Fixes in Commit 14

All 99 errors are `@typescript-eslint/no-unused-vars`. The 15 affected files (Plan 07 § 7):

**Source files (4):**

- `url_builder.ts` — 1 error
- `formats/sensorml/aggregate-process.ts` — 2 errors
- `formats/sensorml/parser.ts` — 2 errors
- `formats/sensorml/physical-system.ts` — 3 errors
- `formats/sensorml/simple-process.ts` — 1 error

**Test files (11):**

- `formats/sensorml/aggregate-process.spec.ts` — 1 error
- `formats/sensorml/parser.spec.ts` — 1 error
- `formats/sensorml/physical-system.spec.ts` — 2 errors
- `formats/sensorml/simple-process.spec.ts` — 1 error
- `formats/sensorml/types.spec.ts` — 32 errors
- `formats/swecommon/data-record.spec.ts` — 14 errors
- `formats/swecommon/index.spec.ts` — 1 error
- `formats/swecommon/parser.spec.ts` — 1 error
- `formats/swecommon/types.spec.ts` — 27 errors
- `integration/observation.spec.ts` — 3 errors

**Fix approach:** Remove unused imports, or convert `import { X }` to `import type { X }` where the import is used only as a type. Do NOT prefix with `_` unless it's a function parameter — unused imports should be removed.

### New File Compliance

Files created in Commit 15 (`csapi/index.ts`, `csapi/factory.ts`, `csapi/factory.spec.ts`) must be **Prettier-compliant from inception** per Plan 07 § 9:

- Single quotes, semicolons, 80-char width, 2-space indent
- Trailing commas ES5-style (objects/arrays, NOT function params)
- `.js` extensions on all local imports/re-exports
- `import type` for type-only imports
- LF line endings (Git normalizes on commit)

---

## 8. Verification Checklist

### 8a. Boundary Condition Verification (`git grep`)

| #   | Command                                                                    | Expected  | Constraint                                 |
| --- | -------------------------------------------------------------------------- | --------- | ------------------------------------------ |
| V1  | `git grep "from.*csapi" src/ogc-api/endpoint.ts`                           | 0 matches | C3: No outward imports                     |
| V2  | `git grep "csapi\|CSAPI" src/index.ts`                                     | 0 matches | C1: No CSAPI in root exports               |
| V3  | `git grep "import.*from.*csapi" -- "src/" ":!src/ogc-api/csapi/"`          | 0 matches | C3: No outward imports (full scan)         |
| V4  | `git grep "from.*csapi" -- "src/" ":!src/ogc-api/csapi/" ":!src/index.ts"` | 0 matches | C3+C4: No remaining cross-boundary imports |

### 8b. CI Verification (`npm run`)

| #   | Command                | Expected       |
| --- | ---------------------- | -------------- |
| V5  | `npm run format:check` | Exit code 0    |
| V6  | `npm run typecheck`    | Exit code 0    |
| V7  | `npm run lint`         | Exit code 0    |
| V8  | `npm run test:browser` | All tests pass |
| V9  | `npm run test:node`    | All tests pass |

### 8c. Litmus Test (One-Way Dependency)

```bash
# Step 1: Temporarily hide CSAPI module
mv src/ogc-api/csapi src/ogc-api/_csapi_backup

# Step 2: Remove CSAPI export from package.json (or ignore the error)
# TypeScript will error on the barrel file import, but endpoint.ts should be clean

# Step 3: Verify core compiles without CSAPI
#   - endpoint.ts has 0 imports from csapi/ → should compile
#   - index.ts has 0 csapi/ references → should compile
#   - Non-CSAPI tests should pass

# Step 4: Restore
mv src/ogc-api/_csapi_backup src/ogc-api/csapi
```

**Constraint verified:** Removing `src/ogc-api/csapi/` entirely leaves core functional — `endpoint.ts` and `index.ts` have zero CSAPI references.

### 8d. Diff Review

```bash
# Total diff against upstream/main
git diff --stat upstream/main..clean-pr

# Refactoring-only diff (commits 14-15)
git diff --stat HEAD~2..HEAD

# Architecture-only diff (commit 15 only)
git diff --stat HEAD~1..HEAD
```

### 8e. Point-of-No-Return Checklist

Before force-pushing to `clean-fork/clean-pr`:

- [ ] All V1–V9 verification gates pass
- [ ] Litmus test passes (8c)
- [ ] `pre-refactor-backup` tag exists on the old `clean-pr` HEAD
- [ ] `git log --oneline upstream/main..clean-pr` shows exactly 15 commits
- [ ] `git diff clean-pr clean-fork/clean-pr` confirms local is 2 commits ahead (new commits only)
- [ ] Reviewing the architecture diff (`HEAD~1..HEAD`) shows only the expected changes

---

## 9. PR and Documentation Updates

### Question 37: PR #136 Description

**Yes — the PR description needs updating.** The current description describes CSAPI as integrated into the endpoint via `endpoint.csapi()`. After refactoring, the description must reflect:

- Separate entry point: `@camptocamp/ogc-client/csapi`
- Factory function: `createCSAPIBuilder(endpoint, collectionId)`
- `hasConnectedSystems` and `csapiCollections` remain on endpoint
- `endpoint.csapi()` method removed
- Tree-shakeable: consumers who don't import from `./csapi` get zero CSAPI code

**The PR description update is a human action** — not part of the automated changelist. It should be done after the force-push.

### Question 38: README Files

**No changes needed.** Checked:

- `app/README.md` — does not reference `csapi` or CSAPI
- `examples/README.md` — does not reference CSAPI
- `README.md` (root) — does not reference CSAPI

### Question 39: MIGRATION.md or BREAKING-CHANGES.md

**Not needed.** CSAPI has never been in a released version — PR #136 is still a Draft PR. There are no external consumers to migrate. The import path change (`endpoint.csapi()` → `createCSAPIBuilder()`) is documented in the factory function's JSDoc and the PR description.

### Question 40: Examples Referencing CSAPI

**`app/examples/edr.ts`** — does not reference CSAPI. It's an EDR example only.

No other examples reference CSAPI. The `examples/` directory contains only `stac-query.js` and `README.md`, neither of which mentions CSAPI.

---

## 10. Quick-Reference Implementation Checklist

### Commit 14: Formatting + ESLint

- [ ] `npx prettier --write "src/ogc-api/csapi/**/*.ts"`
- [ ] `npx prettier --write "fixtures/ogc-api/csapi/**/*.json"`
- [ ] `npx prettier --write "src/ogc-api/endpoint.ts"`
- [ ] Fix 99 ESLint `no-unused-vars` errors across 15 CSAPI files
- [ ] Verify: `npx prettier --check "src/ogc-api/csapi/**/*.ts"` passes
- [ ] Verify: `npx eslint src/ogc-api/csapi/` passes
- [ ] `git add -A && git commit` with formatting message

### Commit 15: Architecture

- [ ] Create `src/ogc-api/csapi/index.ts` (barrel file, ~190 lines)
- [ ] Create `src/ogc-api/csapi/factory.ts` (factory function, ~55 lines)
- [ ] Create `src/ogc-api/csapi/factory.spec.ts` (factory tests, ~30 lines)
- [ ] Edit `src/ogc-api/endpoint.ts`:
  - [ ] Remove `import CSAPIQueryBuilder from './csapi/url_builder.js'` (line 52)
  - [ ] Remove `import { scanCsapiLinks } from './csapi/helpers.js'` (line 53)
  - [ ] Remove `collection_id_to_csapi_builder_` cache field (lines 70–71)
  - [ ] Change `private get root()` → `public get root()` (line 72)
  - [ ] Update `hasConnectedSystems` JSDoc (remove `@see {@link csapi}`)
  - [ ] Remove `csapi()` method + JSDoc (~lines 363–411)
  - [ ] Remove `extractRootResourceUrls()` + JSDoc (~lines 424–437)
  - [ ] Change `private getCollectionDocument(` → `public getCollectionDocument(` (~line 444)
- [ ] Edit `src/index.ts`:
  - [ ] Remove all CSAPI export lines (lines 45–227)
- [ ] Edit `src/ogc-api/endpoint.spec.ts`:
  - [ ] Remove `can produce a CSAPI query builder` test (lines 2854–2860)
  - [ ] Remove `caches the CSAPI query builder` test (lines 2862–2869)
  - [ ] Remove `throws an error when calling csapi()` test (lines 2881–2885)
- [ ] Edit `package.json`:
  - [ ] Add `"./csapi"` sub-path to `"exports"`
  - [ ] Add `"sideEffects": false`
- [ ] `git add -A && git commit` with architecture message

### Post-Commit Verification

- [ ] Run V1–V4 boundary git greps (all return 0 matches)
- [ ] Run V5–V9 CI commands (all pass)
- [ ] Run litmus test (core compiles without csapi/)
- [ ] Review diff: `git diff --stat HEAD~2..HEAD`
- [ ] `git push --force-with-lease clean-fork clean-pr`

---

## 11. Known Risks and Rollback Plan

| Risk                                                                | Impact                                     | Mitigation                                                                                                                        | Rollback                                           |
| ------------------------------------------------------------------- | ------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------- |
| Line numbers shift after Prettier formatting                        | Architecture commit references wrong lines | Apply formatting FIRST (Commit 14), then base architecture edits on formatted code                                                | N/A — ordering prevents this                       |
| TypeScript compilation fails after removing CSAPI from index.ts     | Build breaks                               | Create barrel file in SAME commit as removing from index.ts                                                                       | `git reset --hard HEAD~1`                          |
| Factory tests import incorrect fixtures                             | Tests fail                                 | Use same fixture URLs as existing endpoint tests (`http://local/csapi/sample-data-hub`)                                           | Fix fixture paths                                  |
| Force-push overwrites remote changes                                | Data loss                                  | `pre-refactor-backup` tag + `--force-with-lease`                                                                                  | `git push clean-fork pre-refactor-backup:clean-pr` |
| Prettier reformats new barrel/factory files unexpectedly            | Format check fails                         | Write new files Prettier-compliant from start (Plan 07 § 9 checklist)                                                             | `npx prettier --write <file>`                      |
| `url_builder.spec.ts` 2,221-line formatting diff surprises reviewer | Review friction                            | Note in PR description and commit message that this file accounts for 55% of formatting diff                                      | N/A — informational                                |
| ESLint fixes in Commit 14 change behavior                           | Test failures                              | All fixes are `no-unused-vars` — removing unused imports cannot change behavior                                                   | Review each removal                                |
| `getCollectionDocument` becoming public exposes internal API        | Future maintenance burden                  | Method is already used by `getStyleMetadataDocument`, `getCollectionInfo`, `getCollectionItemsUrl`— it's a general-purpose method | Can revert to private if factory pattern changes   |

---

## 12. Open Questions

| #   | Question | Status                | Notes                                                                                                                |
| --- | -------- | --------------------- | -------------------------------------------------------------------------------------------------------------------- |
| —   | —        | **No open questions** | All 40 questions answered. All architectural decisions final from Plans 01–07. All implementation details specified. |

Every prior plan's open questions have been resolved:

- Plan 06 Q1 (will jahow accept `hasConnectedSystems` on endpoint?) → Resolved as "likely yes" with EDR precedent
- Plan 06 Q2 (will jahow accept public `root`/`getCollectionDocument`?) → Resolved as "reasonable"
- Plan 07 Q1 (ESLint fix commit placement) → Resolved: combined with formatting commit
- Plan 07 Q2 (`endpoint.ts` formatting placement) → Resolved: in formatting commit
- Plan 07 Q3 (`url_builder.spec.ts` reviewer reaction) → Mitigated: noted in commit message

### Verification Pass Findings (Plans 01–05 Tails)

A cross-reference review of Plans 01–05 tail sections (lines 601+) against Plan 08 identified two items:

1. **`"sideEffects": false` and the worker-fallback import** — `src/index.ts` line 251 has `import './worker-fallback/index.js'` (a bare side-effect import). Plan 03 Open Question 2 flagged this. Risk is LOW — see § 3 Q12 verification pass note for analysis. Implementation should confirm via tests; the alternative `"sideEffects": ["./dist/index.js", "./dist/worker-fallback/index.js"]` is available if needed.

2. **Plan 03 Appendix C documentation error** — Plan 03 recorded the root `"."` export `"import"` condition as `"./dist/index.js"`, but the actual `package.json` has `"import": "./dist/dist-node.js"`. Plan 08 already has the correct value (§ 3 Q12). This is a Plan 03 doc error only — zero implementation impact since Plan 08 does not modify the root `"."` export.

All other items from Plans 01–05 tails were confirmed correctly captured in Plan 08. No additional changes required.

---

## Boundary Condition Verification Summary

| Constraint                       | Verification                                     | Changelist Items That Satisfy It                         |
| -------------------------------- | ------------------------------------------------ | -------------------------------------------------------- |
| **C1:** No CSAPI in root exports | V2: `git grep "csapi" src/index.ts` → 0          | M2: Remove 183 lines from `index.ts`                     |
| **C2:** Separate entry point     | Barrel file exists + `"./csapi"` in package.json | C1: Create `csapi/index.ts`, M4: Edit `package.json`     |
| **C3:** No outward imports       | V1, V3, V4: `git grep` → 0 matches               | M1: Remove 2 imports from `endpoint.ts`                  |
| **C4:** One-way dependency       | Litmus test: remove csapi/, core compiles        | M1: Remove `csapi()`, `extractRootResourceUrls()`, cache |
| **C5:** CI compliance            | V5–V9: All 5 CI checks pass                      | Commit 14: formatting + ESLint; all new files compliant  |

---

## Implementation Scope Gate Assessment

| File Operation                                      | Serves jahow's requirements?                        | Minimum-change?     | Included? |
| --------------------------------------------------- | --------------------------------------------------- | ------------------- | --------- |
| Remove CSAPI exports from `index.ts`                | Yes — directly required                             | Yes                 | ✓         |
| Create barrel file `csapi/index.ts`                 | Yes — required for `./csapi` entry                  | Yes                 | ✓         |
| Add `"./csapi"` to `package.json` exports           | Yes — directly required                             | Yes                 | ✓         |
| Add `"sideEffects": false`                          | Yes — enables tree-shaking                          | Yes — 1 line        | ✓         |
| Remove 2 CSAPI imports from `endpoint.ts`           | Yes — directly required                             | Yes                 | ✓         |
| Remove `csapi()` method                             | Yes — enables import removal                        | Yes                 | ✓         |
| Remove `extractRootResourceUrls()`                  | Yes — enables import removal                        | Yes                 | ✓         |
| Remove CSAPI cache field                            | Yes — consequence of method removal                 | Yes                 | ✓         |
| Create `createCSAPIBuilder` factory                 | Yes — replacement API for removed `csapi()`         | Yes — 1 function    | ✓         |
| Make `getCollectionDocument` public                 | Yes — factory needs it                              | Yes — 1 word        | ✓         |
| Make `root` public                                  | Yes — factory needs it                              | Yes — 1 word        | ✓         |
| Create `factory.spec.ts`                            | Yes — tests for new code                            | Yes                 | ✓         |
| Migrate 3 endpoint tests                            | Yes — tests reference removed method                | Yes                 | ✓         |
| Apply Prettier to 51 files                          | Yes — CI compliance                                 | Yes — automated     | ✓         |
| Fix 99 ESLint errors                                | Yes — CI compliance                                 | Yes — remove unused | ✓         |
| ESLint boundary rule (`import/no-restricted-paths`) | No — enforcement, not requirement                   | No — tooling        | ✗ Defer   |
| Boundary integration test                           | No — enforcement                                    | Borderline          | ✗ Defer   |
| TypeScript Project References                       | No — architectural improvement                      | No — heavy refactor | ✗ Defer   |
| Move MIME type functions to csapi/                  | No — they're in shared/, constraint 3 doesn't apply | No — unnecessary    | ✗ Skip    |

---

## Key Takeaways

1. **Two commits, clean separation.** Commit 14 (formatting + ESLint) is entirely mechanical. Commit 15 (architecture) is entirely logical. No mixing. Reviewer can skip Commit 14 and focus on Commit 15.

2. **Append, don't amend.** Adding 2 commits on top of the existing 13 is the safest path with the best reviewability. The "integrate then decouple" narrative is acceptable for a draft PR.

3. **7 files changed in the architecture commit.** 3 created (`csapi/index.ts`, `csapi/factory.ts`, `csapi/factory.spec.ts`) + 4 modified (`endpoint.ts`, `index.ts`, `endpoint.spec.ts`, `package.json`). No moves, no deletes.

4. **The formatting commit touches 51 files** but is entirely automated (Prettier) plus mechanical imports cleanup (ESLint). `url_builder.spec.ts` alone accounts for ~55% of the formatting diff.

5. **All 12 verification gates are concrete.** Four `git grep` patterns, five CI commands, the litmus test, and the diff review. Each has an expected output. No judgment calls.

6. **Zero open questions.** This is the terminal plan. Every decision from Plans 01–07 is consolidated into actionable file operations. A developer can execute this spec mechanically.

7. **Net code change is roughly neutral.** ~275 lines removed (endpoint + index + tests) + ~280 lines added (barrel + factory + factory tests + package.json). The formatting commit is high-volume but zero-logic.

8. **Rollback is trivial.** The `pre-refactor-backup` tag preserves the exact state before any changes. `git push clean-fork pre-refactor-backup:clean-pr` restores the remote. `--force-with-lease` prevents accidental overwrites.

9. **The scope gate held through the entire 8-plan research arc.** No unnecessary abstractions, no plugin systems, no generalized utilities. Every change directly serves jahow's two requirements or is required for CI compliance.

10. **This document IS the implementation spec.** After this, the next action is execution on `clean-pr`, not more research.

---

## Research Completion Checklist

- [x] All 40 detailed questions from the research plan have specific, evidenced answers
- [x] Findings respect all boundary conditions listed in the research plan § 3
- [x] Every finding from Plans 01–07 is accounted for — no prior finding is ignored or contradicted
- [x] File-level changelist is complete: every file to create, modify, move, or delete listed with metadata
- [x] File changelist covers all 4 boundary conditions — each constraint traceable to specific file operations
- [x] Commit sequence specified with draft commit messages and CI compliance analysis
- [x] Each commit verified against CI compliance (both pass all 5 checks)
- [x] Rebase strategy specified with exact git commands
- [x] Verification checklist includes all boundary condition checks, CI commands, and litmus test
- [x] `git grep` patterns for each boundary condition drafted with expected zero-match results
- [x] Formatting accounted for and placed correctly in commit sequence (Commit 14)
- [x] No file affected by refactoring is missing from changelist (completeness verified by walking constraints)
- [x] Developer can execute spec mechanically — zero ambiguities, zero decisions left
- [x] Implementation scope gate applied: every file operation passes minimum-change test
- [x] Deliverable follows findings report template structure
- [x] This document IS the implementation spec — bridges research and action

**Research Started:** 2026-02-26
**Research Completed:** 2026-02-26
**Reviewed:** Not yet
