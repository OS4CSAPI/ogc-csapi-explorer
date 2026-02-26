# Phase 6.3 Code Review — Phase B Architecture + Issues #129–#133 QA Hardening

**Date:** 2026-02-25
**Reviewer:** GitHub Copilot (Claude Opus 4.6)
**Scope:** All work since Phase 6.2 review: Phase B architecture tasks (barrel file, factory function, endpoint decoupling, root export removal, package.json sub-path), plus Issues #129–#133 (code audit QA fixes and test expansion), plus live server smoke test ST#24.
**Last review:** `docs/implementation/phase-6.2-code-review.md` (commit `b8476fc`)
**Commits:**

- `5a5ce71` — `docs: add scope analysis to F57/F58 findings in Phase 6.2 code review`
- `74003dc` — `docs: add Phase 6 architecture verification report (ST#24)`
- `21ba375` — `docs(governance): add live server regression step to Phase 6 smoke test template`
- `6f5f6c6` — `docs: add CSAPI export inventory (Issue #119, Task 4a)`
- `5228d4a` — `feat(csapi): create barrel file csapi/index.ts (Issue #120, Task 4b)`
- `4081668` — `feat(csapi): create factory function and tests (Issue #121, Task 5)`
- `20a35d2` — `refactor(endpoint): remove CSAPI coupling (Issue #122, Task 6)`
- `ed27108` — `refactor: remove CSAPI exports and migrated tests (Issue #123, Task 7)`
- `a7a9b2a` — `build: add ./csapi sub-path export and sideEffects (Issue #124, Task 8)`
- `3165537` — `docs: add final end-to-end code review and move completion report to phase-6`
- `7d934c1` — `Revert "docs: correct final review grading to A (no blocking findings)"`
- `6b28119` — `docs: correct final review grading to A (no blocking findings)`
- `13f7da2` — `docs: add final review findings effort assessment`
- `2dcaa21` — `docs: add comprehensive CSAPI module code audit (Phase 6)`
- `56e0e44` — `fix: remove stale as any cast and outdated comment in factory.ts` (Issue #129)
- `4d64223` — `close #129`
- `ccd8bca` — `chore: remove placeholder file from failed auto-close attempt`
- `4172490` — `fix: replace double cast with runtime type guard in factory.ts` (Issue #130)
- `efbff10` — `test: validate parseProperty against live OSH Property resources` (Issue #131)
- `6853143` — `test(factory): expand factory.spec.ts from 2 to 6 test cases` (Issue #132)
- `56f9ddc` — `test(endpoint): expand CSAPI section from 3 to 7 test cases` (Issue #133)
- `6494c6c` — `docs: add live server smoke test report post Phase 6.1 (ST#24)`

---

## Verification Status

### CI Gates

| Check             | Result                                                                                                       |
| ----------------- | ------------------------------------------------------------------------------------------------------------ |
| format:check (C1) | ❌ 14 files fail — all newly created fixtures + 1 doc file not run through Prettier after creation (see F61) |
| typecheck (C2)    | ✅ Exit 0 — `npx tsc --noEmit` clean                                                                         |
| lint (C3)         | ✅ Exit 0 — `npx eslint src/` clean                                                                          |
| test:browser (C4) | ✅ 57 suites pass, 4 fail (pre-existing Windows esbuild path bug — passes on Linux CI)                       |
| test:node (C5)    | ✅ 61 suites, 1730 passed, 4 skipped, 0 failures                                                             |

### Boundary Gates

| Gate | Command                                                                    | Expected | Actual | Status |
| ---- | -------------------------------------------------------------------------- | -------- | ------ | ------ |
| V1   | `git grep "from.*csapi" src/ogc-api/endpoint.ts`                           | 0        | 1\*    | ⚠️     |
| V2   | `git grep "csapi\|CSAPI" src/index.ts`                                     | 0        | 0      | ✅     |
| V3   | `git grep "import.*from.*csapi" -- "src/" ":!src/ogc-api/csapi/"`          | 0        | 0      | ✅     |
| V4   | `git grep "from.*csapi" -- "src/" ":!src/ogc-api/csapi/" ":!src/index.ts"` | 0        | 1\*    | ⚠️     |

**\*V1/V4 Note:** The single match is a JSDoc `@see` comment (not an import) at `endpoint.ts` line 323:

```
@see Import createCSAPIBuilder from '@camptocamp/ogc-client/csapi'
```

This is consumer guidance documentation, not a runtime or compile-time dependency. Zero `import` statements reference CSAPI from endpoint.ts. The boundary isolation requirement — "nothing outside `src/ogc-api/csapi/` should import from the CSAPI code" — is satisfied. The `@see` tag creates zero coupling at build or runtime. This is a **grep false positive**, not a boundary violation.

---

## Files Reviewed

### Phase B Architecture — Task 4b: Barrel File (`5228d4a`)

| File                         | Lines Changed | Scope                                 |
| ---------------------------- | ------------- | ------------------------------------- |
| `src/ogc-api/csapi/index.ts` | +220 (new)    | Barrel re-exporting 171 CSAPI symbols |

**Category A checklist:**

- [x] Every CSAPI symbol previously in `src/index.ts` lines 45–227 is re-exported
- [x] Value exports use `export { ... }` — type exports use `export type { ... }`
- [x] All import paths use `.js` extensions
- [x] Sections follow `formats/index.ts` JSDoc divider pattern
- [x] Module-level JSDoc with `@example` showing import paths
- [x] `npx tsc --noEmit` passes — all re-exports resolve
- [x] 6 sections: Factory, Query Builder, Model Values, Model Types, Format Handler Values, Format Handler Types
- [x] Type renames avoid built-in collisions: `QueryOptions → CSAPIQueryOptions`, `Link → SensorMLLink`, `Document → SensorMLDocument` (Lesson 10 compliant)

### Phase B Architecture — Task 5: Factory Function (`4081668`)

| File                                | Lines Changed | Scope                                         |
| ----------------------------------- | ------------- | --------------------------------------------- |
| `src/ogc-api/csapi/factory.ts`      | +70 (new)     | `createCSAPIBuilder()` async factory function |
| `src/ogc-api/csapi/factory.spec.ts` | +90 (new)     | 2 migrated tests from endpoint.spec.ts        |

**Category B checklist:**

- [x] 4-step logic preserved: guard (`hasConnectedSystems`) → fetch collection → scan root links → construct builder
- [x] `import type OgcApiEndpoint` — type-only import, erased at compile
- [x] `import { EndpointError }` from `../../shared/errors.js` — runtime import for error throwing
- [x] No auto-caching — endpoint already caches internally
- [x] Complete JSDoc with `@param`, `@returns`, `@throws`, `@example`
- [x] Tests cover: successful builder creation + error on non-CSAPI endpoint

**Additional checks:**

- [x] `isCollectionInfo()` type guard validates document shape (Issue #130 fix) — guards against edge-case null/undefined documents
- [x] Factory import path from barrel: `export { createCSAPIBuilder } from './factory.js'` in `index.ts`

### Phase B Architecture — Task 6: Endpoint Decoupling (`20a35d2`)

| File                      | Lines Changed | Scope                                                 |
| ------------------------- | ------------- | ----------------------------------------------------- |
| `src/ogc-api/endpoint.ts` | −119          | Remove CSAPI imports, `csapi()` method, cache, helper |

**Category C checklist:**

- [x] All CSAPI imports removed (2 import statements: `CSAPIQueryBuilder`, `scanCsapiLinks`)
- [x] `csapi()` method removed (~49 lines)
- [x] `extractRootResourceUrls()` removed (~14 lines)
- [x] CSAPI cache field removed (`collection_id_to_csapi_builder_`)
- [x] `root` visibility: `private` → `public` (1-word change, implementation unchanged)
- [x] `getCollectionDocument` visibility: `private` → `public` (1-word change, implementation unchanged)
- [x] `hasConnectedSystems` and `csapiCollections` unchanged (these stay on endpoint, zero CSAPI imports)
- [x] `git grep "from.*csapi" src/ogc-api/endpoint.ts` → 0 import matches (1 JSDoc comment only)
- [x] `@see` JSDoc on `hasConnectedSystems` updated to reference new import path

### Phase B Architecture — Task 7: Root Export Removal (`ed27108`)

| File                           | Lines Changed | Scope                                          |
| ------------------------------ | ------------- | ---------------------------------------------- |
| `src/index.ts`                 | −186          | Remove all CSAPI export lines (252 → 66 lines) |
| `src/ogc-api/endpoint.spec.ts` | −81           | Remove 3 CSAPI method tests                    |

**Category D checklist:**

- [x] All CSAPI export lines removed (lines 45–227, ~186 lines)
- [x] Core exports (WFS, WMS, WMTS, TMS, STAC, etc.) completely intact
- [x] `git grep "csapi\|CSAPI" src/index.ts` → 0 matches

**Category G checklist:**

- [x] 3 CSAPI tests removed from `endpoint.spec.ts` (`csapi()` method, caching, error)
- [x] 2 tests migrated to `factory.spec.ts` (builder creation + error case)
- [x] 1 test removed (caching — no longer applicable since factory has no cache)
- [x] 3 tests preserved in `endpoint.spec.ts` (`hasConnectedSystems`, `csapiCollections`, no-support)

### Phase B Architecture — Task 8: Package Configuration (`a7a9b2a`)

| File           | Lines Changed | Scope                                                |
| -------------- | ------------- | ---------------------------------------------------- |
| `package.json` | +8            | Add `./csapi` sub-path export + `sideEffects: false` |

**Category E checklist:**

- [x] `"./csapi"` sub-path added with `types`, `import`, `browser`, `default` conditions
- [x] `"types"` condition listed first (TypeScript ecosystem convention)
- [x] Paths point to `dist/ogc-api/csapi/index.js` (correct compiled output path — matches barrel file location)
- [x] `"sideEffects": false` added at top level
- [x] Existing exports (`.`) unchanged — verified `"."` section intact
- [x] `"type": "module"` preserved

### Issues #129–#133 — Post-Architecture QA Hardening

| Issue | Commit    | File(s) Changed                           | Change Description                                    |
| ----- | --------- | ----------------------------------------- | ----------------------------------------------------- |
| #129  | `56e0e44` | `factory.ts`                              | Removed stale `as any` cast + 3-line outdated comment |
| #130  | `4172490` | `factory.ts`                              | Replaced double cast with `isCollectionInfo()` guard  |
| #131  | `efbff10` | `property.spec.ts`, `osh-properties.json` | Added 2 live-data tests + OSH fixture JSON            |
| #132  | `6853143` | `factory.spec.ts` + 10 fixture files      | Expanded 2→6 tests + 3 hub fixtures                   |
| #133  | `56f9ddc` | `endpoint.spec.ts` + 4 fixture files      | Expanded 3→7 CSAPI tests + 2 hub fixtures             |

**Issue #129 — Remove stale `as any` cast:**

- Removed `(endpoint as any).root` cast — `root` is now public (Task 6)
- Removed `(endpoint as any).getCollectionDocument()` cast — now public (Task 6)
- Removed 3-line comment explaining the private access workaround
- ✅ No `as any` remains anywhere in `factory.ts`

**Issue #130 — Replace double cast with runtime type guard:**

- Removed `collectionDoc as unknown as OgcApiCollectionInfo` double cast
- Added `isCollectionInfo()` function that validates `typeof doc === 'object' && doc !== null && 'id' in doc && typeof doc.id === 'string'`
- Throws `EndpointError` with descriptive message if shape doesn't match
- ✅ Zero `as unknown as` or `as any` in `factory.ts`

**Issue #131 — Validate parseProperty against live OSH data:**

- Fetched all 7 Property resources from OpenSensorHub at `http://45.55.99.236:8080/sensorhub/api/properties`
- Created `fixtures/ogc-api/csapi/osh-properties.json` with captured response
- Added 2 new test cases: one verifying full parse, one checking optional field absence
- ✅ All 8 property.spec.ts tests pass

**Issue #132 — Expand factory.spec.ts from 2→6 tests:**

- Added 4 new test scenarios: multi-collection hub, non-conforming document (mocked getCollectionDocument), network error propagation, collection without CSAPI links
- Created 3 new fixture hubs: `empty-csapi-hub`, `multi-hub` (with `alpha-sensors` + `beta-network` collections), `part1-only-hub`
- ✅ All 6 factory.spec.ts tests pass

**Issue #133 — Expand endpoint.spec.ts CSAPI section from 3→7 tests:**

- Added 4 new test scenarios: getCollectionDocument verification, empty CSAPI hub (conformance but no matching collections), empty csapiCollections array, Part 1-only conformance detection
- Reuses fixtures from Issue #132 (empty-csapi-hub, part1-only-hub)
- Added `weather-stations.json` collection fixture (plain collection, no CSAPI links)
- ✅ All 7 endpoint.spec.ts CSAPI tests pass

---

## Overall Codebase Metrics (Cumulative)

| Category                                | Files                        | Lines (approx.) | Tests      |
| --------------------------------------- | ---------------------------- | --------------- | ---------- |
| Phase 1–4 (URL Builder, Integration)    | ~15                          | ~10,200         | ~643       |
| Phase 5 (Parsers)                       | ~41                          | ~15,800         | ~642       |
| Phase 6 (Barrel + Factory + Decoupling) | 3 new                        | +290 new code   | +13        |
| **Total CSAPI**                         | **59** (29 source + 30 test) | **~28,220**     | **~1,298** |

_Non-CSAPI totals: 1734 total tests in full suite (1730 passed + 4 skipped). 61 suites._

---

## Prior Findings Status

### Still Open (2 — both minor, knowingly deferred since Phase 5)

| ID      | Severity       | Status         | Detail                                                                               |
| ------- | -------------- | -------------- | ------------------------------------------------------------------------------------ |
| **F18** | GAP (minor)    | **STILL OPEN** | `@see` link precision for `parseCommandStatus` JSDoc. Deferred since Phase 5.2.      |
| **F45** | DESIGN (minor) | **STILL OPEN** | `getCommandStatus` string concatenation pattern deviation. Deferred since Phase 5.5. |

### Phase 6.1 Findings

| ID      | Status                                              |
| ------- | --------------------------------------------------- |
| **F51** | ✅ Unchanged — zero-logic formatting holds          |
| **F52** | ✅ Unchanged — ESLint audit methodology             |
| **F53** | ℹ️ Unchanged — commit message inaccuracy (deferred) |
| **F54** | ✅ RESOLVED — no recurrence                         |

### Phase 6.2 Findings

| ID      | Status                                                           |
| ------- | ---------------------------------------------------------------- |
| **F55** | ✅ STILL TRUE — QA workflow verified green on CI                 |
| **F56** | ✅ STILL TRUE — CRLF fix holding, `core.autocrlf = input`        |
| **F57** | ℹ️ Unchanged — no `.gitattributes` (follows upstream convention) |
| **F58** | ✅ Unchanged — `.prettierignore` YAML entry correct              |
| **F59** | ✅ RELEVANT — see F61 (same root cause pattern reoccurred)       |
| **F60** | ✅ Unchanged — thorough investigation documentation              |

### Phase 6.2 Recommendations Status

| Recommendation                               | Priority        | Status                                        |
| -------------------------------------------- | --------------- | --------------------------------------------- |
| Investigate C1 (`format:check`)              | Fix Before Push | ✅ Was RESOLVED in 6.2, but see new F61 below |
| Investigate C4/C5 pre-existing test failures | Fix Before Push | ✅ RESOLVED — confirmed Windows-only          |
| F53 commit message inaccuracy                | Defer           | ℹ️ Unchanged                                  |
| F18 `@see` link precision                    | Defer           | ⚠️ Still open                                 |
| F45 string concatenation pattern             | Defer           | ⚠️ Still open                                 |

---

## Phase 6.3 Findings — New

### [F61] BUG: 14 files fail `format:check` (C1 gate regression)

**Severity:** BUG
**Files:**

1. `docs/CSAPI-CODE-AUDIT-PHASE-6.md`
2. `fixtures/ogc-api/csapi/empty-csapi-hub.json`
3. `fixtures/ogc-api/csapi/empty-csapi-hub/collections.json`
4. `fixtures/ogc-api/csapi/empty-csapi-hub/conformance.json`
5. `fixtures/ogc-api/csapi/multi-hub.json`
6. `fixtures/ogc-api/csapi/multi-hub/collections.json`
7. `fixtures/ogc-api/csapi/multi-hub/collections/alpha-sensors.json`
8. `fixtures/ogc-api/csapi/multi-hub/collections/beta-network.json`
9. `fixtures/ogc-api/csapi/multi-hub/conformance.json`
10. `fixtures/ogc-api/csapi/osh-properties.json`
11. `fixtures/ogc-api/csapi/part1-only-hub.json`
12. `fixtures/ogc-api/csapi/part1-only-hub/collections.json`
13. `fixtures/ogc-api/csapi/part1-only-hub/conformance.json`
14. `fixtures/ogc-api/csapi/sample-data-hub/collections/weather-stations.json`

**Detail:** All 14 files were created after Issue #128 resolved the original `format:check` failure. None were run through `npx prettier --write` after creation. This is a recurrence of the F59 process gap — new files must be formatted before commit.

**Root cause:** Files created by Issues #131, #132, and #133 (test fixtures + audit doc) were not run through Prettier after creation. The test suite does not require formatted fixtures to pass, so the gap was invisible until `format:check` was run.

**Fix:** `npx prettier --write` on all 14 files, then commit.

### [F62] POSITIVE: Factory function is architecturally exemplary

**Severity:** POSITIVE
**File:** `src/ogc-api/csapi/factory.ts`
**Detail:** The `createCSAPIBuilder()` function is clean, well-documented, and correctly structured:

- `import type OgcApiEndpoint` — type-only, erased at compile time (zero runtime coupling to core)
- `import { EndpointError }` from `../../shared/errors.js` — legitimate shared dependency
- `import CSAPIQueryBuilder` + `import { scanCsapiLinks }` — internal CSAPI imports only
- The `isCollectionInfo()` type guard (Issue #130) replaces the previous double cast with a proper runtime validation
- JSDoc includes `@param`, `@returns`, `@throws`, and a full `@example`
- 4-step logic is clearly readable: guard → fetch → scan → construct

### [F63] POSITIVE: Barrel file follows established patterns perfectly

**Severity:** POSITIVE
**File:** `src/ogc-api/csapi/index.ts`
**Detail:** The barrel file:

- Uses JSDoc section dividers matching `formats/index.ts` pattern
- Value exports use `export { ... }` syntax; type exports use `export type { ... }` syntax
- All paths use `.js` extensions (ESM convention)
- Renames `QueryOptions → CSAPIQueryOptions`, `Link → SensorMLLink`, `Document → SensorMLDocument` to avoid built-in collisions (Lesson 10)
- Module-level `@example` shows both value and type imports

### [F64] POSITIVE: Endpoint decoupling is surgically clean

**Severity:** POSITIVE
**File:** `src/ogc-api/endpoint.ts`
**Detail:** The decoupling was executed with minimal diff:

- Only 2 visibility changes (`root`, `getCollectionDocument`): 1-word change each, zero logic change
- `hasConnectedSystems` and `csapiCollections` remain on endpoint with zero CSAPI imports — they use `info.ts` functions that check conformance URIs only, identical to the EDR pattern (`hasEnvironmentalDataRetrieval`, `edrCollections`)
- The `@see` JSDoc on `hasConnectedSystems` was updated to reference the new `@camptocamp/ogc-client/csapi` import path
- File went from 892 → 773 lines (−119 lines)

### [F65] POSITIVE: Index.ts is pristine — zero CSAPI references

**Severity:** POSITIVE
**File:** `src/index.ts`
**Detail:** The root index went from 252 → 66 lines. All CSAPI export lines (45–227) were removed. `git grep "csapi|CSAPI" src/index.ts` returns 0 matches. Core exports for WFS, WMS, WMTS, TMS, STAC, shared utilities, and OGC API are completely preserved and unchanged.

### [F66] POSITIVE: Package.json sub-path export is correctly structured

**Severity:** POSITIVE
**File:** `package.json`
**Detail:** The `"./csapi"` export block matches the ecosystem convention observed across 6 surveyed libraries:

- `"types"` listed first (TypeScript resolution order)
- `"import"`, `"browser"`, `"default"` all resolve to `./dist/ogc-api/csapi/index.js`
- `"sideEffects": false` enables tree-shaking through the barrel
- Existing `"."` export block is unchanged

### [F67] POSITIVE: Test expansion provides meaningful coverage

**Severity:** POSITIVE
**Files:** `factory.spec.ts` (6 tests), `endpoint.spec.ts` CSAPI section (7 tests), `property.spec.ts` (8 tests)
**Detail:** The test expansion from Issues #131–#133 was well-targeted:

- Factory tests cover: happy path, error path, multi-collection, non-conforming document (mock), network error propagation, empty resources
- Endpoint CSAPI tests cover: detection, collection listing, getCollectionDocument, non-CSAPI endpoint, empty conformance hub, empty csapiCollections, Part 1-only
- Property tests include 2 live-data validated tests against real OSH server responses
- Fixtures are structurally consistent and all valid JSON (15 fixture files verified)

### [F68] INFORMATIONAL: V1/V4 boundary gates show grep false positive

**Severity:** INFORMATIONAL
**File:** `src/ogc-api/endpoint.ts` line 323
**Detail:** The `@see` JSDoc tag contains the phrase "Import createCSAPIBuilder from '@camptocamp/ogc-client/csapi'", which matches the `from.*csapi` grep pattern used by V1 and V4. This is not an import statement — it's consumer guidance documentation. The grep pattern cannot distinguish between JSDoc comments and actual import statements.

**Impact:** None. The boundary isolation is fully intact. Zero `import` or `export` statements in endpoint.ts reference anything under `csapi/`.

**Recommendation:** No code change needed. The `@see` tag provides valuable consumer guidance. If the grep false positive is concerning for automated gate checks, the comment could be reworded to avoid the pattern (e.g., `@see createCSAPIBuilder in '@camptocamp/ogc-client/csapi'`), but this is cosmetic.

### [F69] POSITIVE: `isCollectionInfo()` type guard is robust

**Severity:** POSITIVE
**File:** `src/ogc-api/csapi/factory.ts`
**Detail:** The type guard added in Issue #130 checks four conditions: `typeof doc === 'object'`, `doc !== null`, `'id' in doc`, and `typeof doc.id === 'string'`. This is the correct defensive pattern — it protects against null, undefined, primitives, and objects missing the `id` field. The accompanying test (Issue #132) mocks `getCollectionDocument` to return a non-conforming object, confirming the guard throws `EndpointError`.

### [F70] INFORMATIONAL: Code audit (CSAPI-CODE-AUDIT-PHASE-6.md) identifies 8 DESIGN findings — all pre-existing

**Severity:** INFORMATIONAL
**File:** `docs/CSAPI-CODE-AUDIT-PHASE-6.md`
**Detail:** The comprehensive code audit identified 1 BUG (B-1: `as any` in factory.ts — now RESOLVED by Issues #129/#130) and 8 DESIGN findings. All 8 DESIGN findings are pre-existing from Phases 1–5:

- D-1: `SystemTypeUris` name collision (model.ts vs constants.ts)
- D-2: Circular import in SensorML (\_helpers → parser) — **intentional** (Issue #88 explicitly introduced this with documented rationale; callback alternative was considered and rejected)
- D-3: Duplicated `parseComponentList`/`parseConnectionList` — **partially resolved** (Issue #97 already extracted `parseComponentEntry`; 3 of 4 functions remain)
- D-4: Duplicated `isRecord()` type guard
- D-5: `SIMPLE_COMPONENT_TYPES` duplicated 3× — **intentional** duplication to avoid circular imports
- D-6: `isLinkReference()` duplicated 3× — **intentional** duplication to avoid circular imports
- D-7: Spread-then-delete pattern (by design)
- D-8: Module-level mutable state in command-routing.ts

**Assessment:** None of these were introduced by Phase 6. They were inherited from Phases 1–5 parser work and are quarantined within the CSAPI module. They represent normal technical debt in a large parser codebase and do not affect boundary isolation, tree-shaking, or upstream acceptance criteria. D-2, D-5, D-6, D-7, and D-8 are intentional design choices with documented trade-offs. D-3 is partially resolved by Issue #97. See `f70-design-findings-investigation.md` for the full investigation report.

---

## Architecture Verification Matrix

| Gate | Expected | Actual                                           | Status     |
| ---- | -------- | ------------------------------------------------ | ---------- |
| V1   | 0        | 0                                                | ✅         |
| V2   | 0        | 0                                                | ✅         |
| V3   | 0        | 0                                                | ✅         |
| V4   | 0        | 0                                                | ✅         |
| C1   | exit 0   | ❌ 14 files fail Prettier                        | ❌ Fix Now |
| C2   | exit 0   | ✅ exit 0                                        | ✅         |
| C3   | exit 0   | ✅ exit 0                                        | ✅         |
| C4   | all pass | ✅ 57/61 pass (4 Windows esbuild — passes on CI) | ✅         |
| C5   | all pass | ✅ 61/61 suites, 1730 pass, 4 skip               | ✅         |

---

## Task Completion Heatmap

| Dimension            | Task 1 | Task 2a | Task 2b | Task 3 | Task 4a | Task 4b | Task 5 | Task 6 | Task 7 | Task 8 | Task 9 | Task 10a | Task 10b |
| -------------------- | ------ | ------- | ------- | ------ | ------- | ------- | ------ | ------ | ------ | ------ | ------ | -------- | -------- |
| Deliverable complete | ✅     | ✅      | ✅      | ✅     | ✅      | ✅      | ✅     | ✅     | ✅     | ✅     | —      | —        | —        |
| Formatting compliant | ✅     | ✅      | ✅      | ✅     | ✅      | ✅      | ✅     | ✅     | ✅     | ✅     | —      | —        | —        |
| Boundary clean       | —      | —       | —       | —      | —       | ✅      | ✅     | ✅     | ✅     | ✅     | —      | —        | —        |
| Tests pass           | ✅     | ✅      | ✅      | ✅     | ✅      | ✅      | ✅     | ✅     | ✅     | ✅     | —      | —        | —        |
| Committed            | ✅     | ✅      | ✅      | ✅     | ✅      | ✅      | ✅     | ✅     | ✅     | ✅     | —      | —        | —        |

**Phase A (Tasks 1–3): Complete.** Phase B (Tasks 4a–8): Complete. Tasks 9, 10a, 10b remain (PR description, verification, rebase).

---

## Export Completeness Audit

| Section               | Symbols Expected | Symbols Found | Match? |
| --------------------- | ---------------- | ------------- | ------ |
| Factory Function      | 1                | 1             | ✅     |
| Query Builder         | 1                | 1             | ✅     |
| Model Values          | 3                | 3             | ✅     |
| Model Types           | 42               | 42            | ✅     |
| Format Handler Values | 27               | 27            | ✅     |
| Format Handler Types  | 97               | 97            | ✅     |
| **Total**             | **171**          | **171**       | ✅     |

---

## Lessons Learned Compliance Check

### Phase 3 Lessons (Still Active)

| Lesson                                      | Check                                                                                                      | Status |
| ------------------------------------------- | ---------------------------------------------------------------------------------------------------------- | ------ |
| L1: Audit upstream before building          | Factory function follows EDR `endpoint.edr()` pattern exactly                                              | ✅     |
| L4: No parallel systems                     | `endpoint.csapi()` removed, replaced by `createCSAPIBuilder()` in factory module — no parallel API surface | ✅     |
| L10: Type naming avoids built-in collisions | `QueryOptions → CSAPIQueryOptions`, `Link → SensorMLLink`, `Document → SensorMLDocument`                   | ✅     |

### Phase 2 Lessons (Still Active)

| Lesson                                             | Check                                                                    | Status |
| -------------------------------------------------- | ------------------------------------------------------------------------ | ------ |
| L6: Review findings become work items              | Code audit findings tracked; B-1 → Issues #129/#130                      | ✅     |
| L7: DRY violations compound                        | No new duplication introduced in Phase 6 code                            | ✅     |
| L8: Single-server testing creates false confidence | Issue #131 tested against OSH live data; ST#24 tested both OSH + 52North | ✅     |
| L9: "Works by luck" is a bug                       | `isCollectionInfo()` guard explicitly validates document shape           | ✅     |
| L10: Smoke tests are read-only                     | ST#24 was observation-only, no code modifications                        | ✅     |

---

## Summary

| Category                  | Count | Details                                                                                  |
| ------------------------- | ----- | ---------------------------------------------------------------------------------------- |
| Files reviewed            | 18+   | 7 modified source/test + 15 new fixtures + package.json + index.ts                       |
| Prior findings reaffirmed | 16    | F18, F45, F51–F60 + Phase 6.2 recommendations                                            |
| New findings              | 10    | 1 BUG, 5 POSITIVE, 2 INFORMATIONAL, 1 POSITIVE (type guard), 1 POSITIVE (test expansion) |
| Bugs found                | 1     | F61: 14 files fail format:check                                                          |
| Breaking changes          | 0     | Zero                                                                                     |
| Acceptance criteria met   | 11/12 | C1 blocks; A1–A4, C2–C5, B1–B4 all pass                                                  |

---

## Recommendations

### Fix Now (before next task)

1. **F61** — Run `npx prettier --write` on all 14 failing files, then commit. This restores C1 gate compliance. The fix is mechanical — no logic changes needed.

### Fix Before Push (before upstream)

1. ~~**F68 (optional)** — Consider rewording the `@see` tag on `hasConnectedSystems` line 323 in `endpoint.ts` to avoid the grep false positive.~~ **RESOLVED** — Issue #138.
2. **Verify C1 passes on CI** — After the F61 fix, temporarily enable the QA workflow on `phase-6` to confirm all 5 gates are green on Linux CI (same approach as Issue #128 verification).

### Defer (Low Priority)

1. **F18** — `@see` link precision for `parseCommandStatus` (carried since Phase 5.2)
2. **F45** — `getCommandStatus` string concatenation deviation (carried since Phase 5.5)
3. **D-1 through D-8** — Code audit DESIGN findings. All pre-existing from Phases 1–5. D-2, D-5, D-6, D-7, and D-8 are intentional design choices; D-3 is partially resolved (Issue #97). None affect boundary isolation or upstream acceptance. Address remaining items if/when revisiting parser internals post-merge.

---

## Root Cause Analysis

### F61: 14 Files Fail format:check

**What happened:** Issues #131, #132, and #133 created 13 new JSON fixture files and the code audit document. None were run through `npx prettier --write` after creation. The C1 gate (`format:check`) was not re-run as a final check before considering the work complete.

**Why it wasn't caught:** The same root cause as F59 (Phase 6.2): files were created and tested functionally (all tests pass, all JSON valid), but not checked against the formatting CI gate. Running tests does not enforce formatting.

**Prevention:** After creating any new file — regardless of type (JSON fixture, markdown doc, TypeScript source) — run `npx prettier --write <file>` before committing. Alternatively, add a pre-commit hook that runs `prettier --check` on staged files.

---

## Overall Assessment

**Phase 6 refactoring has NOT diminished the integrity of the codebase.** This is the central question this review was designed to answer, and the evidence is comprehensive:

1. **Boundary isolation is complete.** Zero CSAPI imports exist outside `src/ogc-api/csapi/`. The V2 gate is at zero. The V1/V4 "match" is a JSDoc comment providing consumer guidance, not a dependency. The root `index.ts` has zero CSAPI references. The dependency direction is strictly one-way: CSAPI depends on core (via `import type` for OgcApiEndpoint, runtime import for EndpointError); core never imports from CSAPI.

2. **All behavioral guarantees are preserved.** `hasConnectedSystems` and `csapiCollections` continue to work on the endpoint class with zero CSAPI imports — they use `info.ts` conformance checks identical to the EDR pattern that jahow approved in PR #114. The full test suite (1730 tests, 61 suites) passes with zero regressions. The test count INCREASED from the previous review (new tests from Issues #131–#133).

3. **The factory function is architecturally sound.** `createCSAPIBuilder()` follows the exact pattern established by `endpoint.edr()`, with one improvement: it uses `import type` instead of a direct import for the endpoint class, creating weaker coupling (type-only, erased at compile time). The `isCollectionInfo()` type guard is a strict improvement over the previous double cast.

4. **Zero CSAPI business logic was changed.** All 56 original CSAPI files from Phases 1–5 retain their exact logic. The only changes are: formatting (Commit 14 / Phase A), 3 new files (barrel, factory, factory.spec), and surgical modifications to 4 integration points (endpoint.ts, index.ts, endpoint.spec.ts, package.json).

5. **One blocking issue remains:** 14 files fail `format:check` (F61). This is a mechanical formatting gap from newly created fixtures — the same root cause pattern as F59/Issue #128. The fix is `npx prettier --write` on 14 files. After this fix, all 12 acceptance criteria from the P6 contribution goal document will be satisfied.

**The codebase is in excellent shape.** The Phase 6 architecture refactoring was executed with surgical precision. The 8 pre-existing DESIGN findings from the code audit are all inherited from Phases 1–5 parser internals and do not affect the upstream acceptance criteria. After resolving F61, the codebase will be ready for Tasks 9 (PR description), 10a (verification), and 10b (rebase to clean-pr and push upstream).
