# Phase 6: Upstream Acceptance Refactoring — Contribution Goal and Definition

**Version:** 1.0  
**Date:** February 23, 2026

---

## Context

On February 21, 2026, upstream maintainer [@jahow](https://github.com/jahow) reviewed [PR #136](https://github.com/camptocamp/ogc-client/pull/136) and provided the following feedback:

> "Impressive work @Sam-Bolling, thank you for the contribution."

> "I'm willing to take you at your word and consider this as a separate module which you, @Sam-Bolling, will be in charge to maintain (at least in the near future, maybe other parties will join in later). I have neither the time nor expertise to review all of it."

> "This being said, I would request one major thing: that all things related to the CS API not be part of the main `index.ts` file, but instead imported through `@camptocamp/ogc-client/csapi`. Basically I want to make sure that anyone using the library as before do not end up with all this code in their bundle overnight."

> "This means that:
>
> - anything part of the `src/ogc-api/csapi` should not be included in the root `index.ts` file.
> - anything not part of the `src/ogc-api/csapi` should not import things from the CSAPI code at all
>
> (unless we find a better way to handle tree-shaking)."

> "I'm going to review the changes to the existing code and give you a more thorough feedback."

> "could you please give me a rough time frame for when this would be ready? I'd really like to do a 2.0 release for the library soon, and I'd like to know if this will be in it or in a subsequent release."

jahow has signaled willingness to merge the CSAPI contribution — potentially as part of a **2.0 major release** — if the architectural requirements above are met. This phase exists to satisfy those requirements precisely, with no scope creep, so that the PR is ready for final review and merge.

---

## Contribution Goal

Refactor the existing CSAPI implementation on [PR #136](https://github.com/camptocamp/ogc-client/pull/136) to satisfy jahow's two acceptance requirements:

1. **CSAPI symbols must not appear in the root `index.ts` file.** Consumers import CSAPI functionality through a dedicated sub-path: `@camptocamp/ogc-client/csapi`.

2. **Nothing outside `src/ogc-api/csapi/` may import from the CSAPI module.** The dependency direction is strictly one-way: CSAPI depends on core, never the reverse.

The CSAPI implementation itself (types, URL builder, parsers, tests) is complete from Phases 1–5. Phase 6 changes **zero CSAPI business logic**. It restructures the integration boundary so that the CSAPI module is fully decoupled from the core library, passes all upstream CI checks, and is ready for jahow's final review.

---

## Acceptance Criteria

These criteria are derived directly from jahow's PR review and upstream CI requirements. Every criterion is objectively verifiable.

### Architectural (from jahow's review)

| #   | Criterion                                                                                                         | Verification                                                                                                       |
| --- | ----------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| A1  | Zero CSAPI symbols exported from `src/index.ts`                                                                   | `git grep "csapi\|CSAPI" src/index.ts` returns 0 matches                                                           |
| A2  | CSAPI importable via `@camptocamp/ogc-client/csapi`                                                               | `"./csapi"` sub-path present in `package.json` `"exports"` with `types`, `import`, `browser`, `default` conditions |
| A3  | Zero imports from `csapi/` in any file outside `src/ogc-api/csapi/`                                               | `git grep "from.*csapi" -- "src/" ":!src/ogc-api/csapi/"` returns 0 matches                                        |
| A4  | One-way dependency: removing `src/ogc-api/csapi/` entirely leaves core compilable and all non-CSAPI tests passing | Litmus test: `mv csapi/ _backup/`, verify core compiles, restore                                                   |

### CI Compliance (from upstream pipeline)

| #   | Criterion                     | Verification                            |
| --- | ----------------------------- | --------------------------------------- |
| C1  | Prettier formatting passes    | `npm run format:check` exits 0          |
| C2  | TypeScript compilation passes | `npm run typecheck` exits 0             |
| C3  | ESLint passes                 | `npm run lint` exits 0                  |
| C4  | Browser test suite passes     | `npm run test:browser` — all tests pass |
| C5  | Node test suite passes        | `npm run test:node` — all tests pass    |

### Behavioral (preservation guarantees)

| #   | Criterion                                                                     | Verification                                                         |
| --- | ----------------------------------------------------------------------------- | -------------------------------------------------------------------- |
| B1  | `endpoint.hasConnectedSystems` still works (CSAPI-capable endpoint detection) | Existing test passes                                                 |
| B2  | `endpoint.csapiCollections` still works (CSAPI collection listing)            | Existing test passes                                                 |
| B3  | All non-CSAPI ogc-client functionality unchanged                              | Full test suite passes                                               |
| B4  | CSAPI query building available via new consumer API                           | `createCSAPIBuilder(endpoint, collectionId)` factory function tested |

---

## Contribution Definition

### What Changes

Phase 6 appends **2 commits** to the existing 13 on `clean-pr`, bringing the PR to 15 total commits.

**Commit 14 — `style(csapi): apply prettier formatting and fix eslint errors`**

Mechanical cleanup only. Zero logic changes.

- Apply Prettier to 46 CSAPI source/test files, 4 CSAPI fixture JSON files, and `endpoint.ts` (51 files total)
- Fix 99 ESLint `@typescript-eslint/no-unused-vars` errors across 15 files by removing unused imports
- Required to pass upstream CI gates `format:check` and `lint`

**Commit 15 — `refactor(csapi): decouple from endpoint with separate entry point`**

Architectural refactoring. The core deliverable of Phase 6.

_Files created (3):_

| File                                | Purpose                                                                                                              | Lines |
| ----------------------------------- | -------------------------------------------------------------------------------------------------------------------- | ----- |
| `src/ogc-api/csapi/index.ts`        | Barrel file re-exporting all public CSAPI symbols                                                                    | ~190  |
| `src/ogc-api/csapi/factory.ts`      | `createCSAPIBuilder(endpoint, collectionId)` async factory function — replaces the removed `endpoint.csapi()` method | ~55   |
| `src/ogc-api/csapi/factory.spec.ts` | Tests for the factory function                                                                                       | ~30   |

_Files modified (4):_

| File                           | Changes                                                                                                                                                                         | Net Lines |
| ------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------- |
| `src/ogc-api/endpoint.ts`      | Remove 2 CSAPI imports, remove `csapi()` method + `extractRootResourceUrls()` + CSAPI cache field; change `root` and `getCollectionDocument` from private to public             | −63       |
| `src/index.ts`                 | Remove all CSAPI export lines (lines 45–227)                                                                                                                                    | −183      |
| `src/ogc-api/endpoint.spec.ts` | Remove 3 tests that reference the deleted `csapi()` method (2 migrated to `factory.spec.ts`, 1 caching test removed); keep 3 tests for `hasConnectedSystems`/`csapiCollections` | −30       |
| `package.json`                 | Add `"./csapi"` sub-path to `"exports"`; add `"sideEffects": false`                                                                                                             | +8        |

_Files NOT changed (confirmed safe):_

| File                                                       | Why                                                                                |
| ---------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| `src/ogc-api/info.ts`                                      | Zero CSAPI imports — uses only conformance URI strings                             |
| `src/shared/mime-type.ts`                                  | CSAPI MIME functions live in `shared/`, not `csapi/` — constraint 3 does not apply |
| All 56 existing CSAPI files                                | Zero business logic changes — only formatting in Commit 14                         |
| Build configs (`vite.*.js`, `tsconfig.json`, `jest.*.cjs`) | No changes needed — existing globs already cover CSAPI                             |

### What Does NOT Change

- **Zero CSAPI business logic changes.** The URL builder, format parsers, model types, helpers, command routing, SensorML/SWE Common parsers, integration tests — all untouched.
- **Zero new dependencies.** No new npm packages, build tools, or configuration systems.
- **Zero changes to non-CSAPI ogc-client functionality.** WFS, WMS, WMTS, TMS, STAC, OGC API Features/Records/Tiles/Maps/Styles — all unaffected.
- **Zero file moves or deletes.** All 56 CSAPI files remain in `src/ogc-api/csapi/`. All 4 CSAPI fixtures remain in `fixtures/ogc-api/csapi/`.

### Consumer API Migration

The only user-facing change is how CSAPI functionality is accessed:

```typescript
// BEFORE (Phase 5 — current PR state):
import { OgcApiEndpoint } from '@camptocamp/ogc-client';
const endpoint = new OgcApiEndpoint('https://api.example.com');
const builder = await endpoint.csapi('weather-stations');

// AFTER (Phase 6 — refactored):
import { OgcApiEndpoint } from '@camptocamp/ogc-client';
import { createCSAPIBuilder } from '@camptocamp/ogc-client/csapi';
const endpoint = new OgcApiEndpoint('https://api.example.com');
const builder = await createCSAPIBuilder(endpoint, 'weather-stations');
```

The `CSAPIQueryBuilder` class and all CSAPI types remain available — they are simply imported from `@camptocamp/ogc-client/csapi` instead of `@camptocamp/ogc-client`. Direct construction of `CSAPIQueryBuilder` with pre-resolved data continues to work unchanged.

---

## Architectural Design Decisions

These decisions are final, backed by the 8-plan Phase 6 research arc (165 questions, ~8,000 lines of findings). Each decision is traced to its research source and to jahow's requirements.

| Decision                                                                 | Rationale                                                                                                                                                                                                                                                                | Research Source                                        |
| ------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------ |
| **Separate sub-path export** (`"./csapi"` in `package.json` `"exports"`) | Ecosystem standard pattern — all 6 surveyed libraries use conditional sub-path exports. Enables bundle isolation.                                                                                                                                                        | Plan 01 (build system), Plan 03 (entry point patterns) |
| **Barrel file** at `src/ogc-api/csapi/index.ts`                          | Universal pattern (6/6 libraries). Single source of truth for CSAPI public API. Automatically compiled by existing esbuild + vite-plugin-dts tooling.                                                                                                                    | Plan 01, Plan 03, Plan 05                              |
| **Factory function** `createCSAPIBuilder(endpoint, collectionId)`        | Replaces `endpoint.csapi()` — moves builder creation from core to CSAPI module. Constructor injection is the dominant pattern for stateful sub-modules (4/7 surveyed libraries).                                                                                         | Plan 04 (API design), Plan 06 (architecture)           |
| **`hasConnectedSystems` and `csapiCollections` stay on endpoint**        | These properties have zero CSAPI imports — they use `info.ts` functions that check conformance URIs only. They follow the identical pattern as `hasEnvironmentalDataRetrieval` and `edrCollections` (EDR), which jahow approved in PR #114.                              | Plan 02 (EDR pattern analysis)                         |
| **Level 3.5 coupling** (`Pick<>` + `import type`)                        | CSAPIQueryBuilder constructor already uses `Pick<OgcApiCollectionInfo, 'id' \| 'title' \| 'links'>` — the narrowest coupling of any surveyed library. `import type` is erased at compile time, creating zero runtime dependency. No constructor signature change needed. | Plan 05 (decoupling patterns)                          |
| **`scanCsapiLinks` stays in CSAPI**                                      | Plan 05 recommended generalizing it into a shared utility. Plan 06 overrode this — the problem self-resolves when `endpoint.ts` stops calling it. The factory function in CSAPI calls it directly. Minimum-change principle.                                             | Plan 05 → Plan 06 override                             |
| **`root` and `getCollectionDocument` made public**                       | Factory function needs access to endpoint data to construct the builder. Both methods are already called internally by multiple endpoint features. Making them public is a 1-word change per method.                                                                     | Plan 06 (architecture)                                 |
| **Format First commit strategy**                                         | Upstream has 5+ formatting-only commit precedents. Separating the 3,023-insertion Prettier diff from the logic diff makes Commit 15 reviewable. CI checks final state only.                                                                                              | Plan 07 (Prettier/ESLint analysis)                     |
| **`"sideEffects": false`** added to `package.json`                       | 5/6 surveyed libraries declare this. Enables tree-shaking through barrel files. Critical for ensuring consumers who import only one CSAPI symbol don't bundle all format parsers.                                                                                        | Plan 03 (entry point patterns)                         |
| **Append commits** (not amend or squash)                                 | Safest path, best reviewability, zero rebase conflict risk. jahow can see the refactoring layered on top of the original work. If squashing is requested later, it's a trivial `git rebase -i`.                                                                          | Plan 08 (commit strategy)                              |

---

## Verification Plan

12 concrete gates, each with an expected output. No judgment calls.

**Boundary verification (4 gates):**

1. `git grep "from.*csapi" src/ogc-api/endpoint.ts` → 0 matches
2. `git grep "csapi\|CSAPI" src/index.ts` → 0 matches
3. `git grep "import.*from.*csapi" -- "src/" ":!src/ogc-api/csapi/"` → 0 matches
4. `git grep "from.*csapi" -- "src/" ":!src/ogc-api/csapi/" ":!src/index.ts"` → 0 matches

**CI verification (5 gates):** 5. `npm run format:check` → exit 0 6. `npm run typecheck` → exit 0 7. `npm run lint` → exit 0 8. `npm run test:browser` → all pass 9. `npm run test:node` → all pass

**Structural verification (3 gates):** 10. Litmus test: temporarily remove `src/ogc-api/csapi/`, verify core compiles 11. Diff review: `git diff --stat HEAD~2..HEAD` shows expected files only 12. Commit count: `git log --oneline upstream/main..clean-pr` shows exactly 15 commits

---

## Scope Boundaries

### In Scope

- Decoupling CSAPI from core (imports, exports, factory function)
- Prettier/ESLint compliance for all CSAPI files
- `package.json` sub-path export + `sideEffects` declaration
- Migration of 3 endpoint tests to factory test file
- PR description update to reflect new consumer API

### Out of Scope (Deferred)

- ESLint `import/no-restricted-paths` boundary enforcement rule — not required by jahow
- Custom boundary integration test — enforcement, not requirement
- TypeScript Project References — heavyweight, not warranted for one sub-module
- `typesVersions` fallback for legacy TypeScript consumers — 5/6 libraries skip this
- Generalized link scanner utility — problem self-resolves with factory pattern
- Moving CSAPI MIME functions from `shared/` — constraint 3 does not apply to `shared/`
- Any changes to CSAPI business logic, types, parsers, or tests (beyond formatting)

---

## Relationship to Prior Work

| Phase                       | Scope                                                                                 | Status                                               |
| --------------------------- | ------------------------------------------------------------------------------------- | ---------------------------------------------------- |
| **Phases 1–4**              | CSAPI types, URL builder, format parsers, endpoint integration, root exports          | Complete — 10 commits on `clean-pr`                  |
| **Phase 5**                 | Parser completion (Part 2 resources, schema responses, recursive SensorML delegation) | Complete — 3 commits on `clean-pr`                   |
| **Phase 6** (this document) | Upstream acceptance refactoring — decouple CSAPI from core per jahow's requirements   | In progress — research complete, implementation next |

Phase 6 does not undo or rewrite Phases 1–5. It restructures the integration boundary while preserving all CSAPI functionality intact.

---

## Research Foundation

Phase 6 is backed by an 8-plan research arc conducted on the `phase-6` branch. Each plan investigated a specific aspect of the refactoring, and the findings are consolidated into an executable implementation specification.

| Plan | Title                                    | Questions | Key Decision                                                                                          |
| ---- | ---------------------------------------- | --------- | ----------------------------------------------------------------------------------------------------- |
| 01   | Build System & Entry Point Analysis      | 31        | No build config changes needed; per-file esbuild output already covers CSAPI                          |
| 02   | EDR Integration Pattern Analysis         | 35        | EDR is the accepted precedent; `hasConnectedSystems`/`csapiCollections` follow EDR pattern            |
| 03   | Separate Entry Point Design Patterns     | 35        | 4-condition `"exports"` + barrel file + `"sideEffects": false`; validated by 6 library survey         |
| 04   | Sub-Module API Design Patterns           | 38        | Two-layer API: sync constructor + async `createCSAPIBuilder` factory; validated by 7 library survey   |
| 05   | Module Decoupling Patterns               | 37        | Level 3.5 coupling (`Pick<>` + `import type`); one-shot extraction; `import type` for drift detection |
| 06   | Endpoint Decoupling Architecture         | 42        | Factory function signature, barrel file contents, test migration plan, public method changes          |
| 07   | Prettier & ESLint Configuration Analysis | 27        | Format First strategy; 46 files need Prettier; 99 ESLint errors (all `no-unused-vars`)                |
| 08   | File-Level Changelist & Commit Strategy  | 40        | Complete implementation spec: 2 commits, 7 files changed, 12 verification gates                       |

**Total: 285 questions answered across 8 plans, ~8,000 lines of findings.**

All findings are available at [`docs/research/phase-6/findings/`](../../research/phase-6/findings/).

---

## Deliverables

| #   | Deliverable                         | Description                                                                    |
| --- | ----------------------------------- | ------------------------------------------------------------------------------ |
| D1  | Commit 14 on `clean-pr`             | Prettier + ESLint formatting (51 files, zero logic)                            |
| D2  | Commit 15 on `clean-pr`             | Architecture refactoring (3 created, 4 modified, 12 verification gates passed) |
| D3  | Updated PR #136 description         | Reflects new consumer API and module architecture                              |
| D4  | Force-push to `clean-fork/clean-pr` | PR #136 updated with 15 total commits                                          |

---

## Success Condition

PR #136 is in a state where:

- jahow's two explicit requirements are satisfied (verifiable via `git grep`)
- All 5 upstream CI checks pass
- The CSAPI module is fully self-contained and tree-shakeable
- A consumer who does not import from `@camptocamp/ogc-client/csapi` gets zero CSAPI code in their bundle
- jahow can review the changes to existing code (Commit 15) in isolation from the formatting diff (Commit 14)
- The PR is ready for jahow to mark as "Ready for Review" and merge into ogc-client, potentially as part of the 2.0 release
