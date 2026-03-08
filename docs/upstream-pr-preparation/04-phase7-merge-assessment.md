# Phase 7 Merge Assessment — `upstream/phase-7` → `main`

**Date:** 2026-03-08
**Upstream repo:** `OS4CSAPI/ogc-client-CSAPI_2` (branch `phase-7`)
**Target repo:** `OS4CSAPI/ogc-csapi-explorer` (branch `main`)

---

## Merge Cleanliness

**Result: Nearly clean — 2 trivial conflicts only.**

| File | Nature | Resolution |
|---|---|---|
| `.gitignore` | Both sides added ignore entries in the same region | Keep both (our explorer-specific entries + upstream test output entries) |
| `src/ogc-api/csapi/formats/schema-response.ts` | Both sides independently added the same `paramsSchema` fallback fix with slightly different comment wording | Pick either — the generated code is identical |

All other files (60 of 62) auto-merge cleanly.

---

## Scope of Changes

- **64 commits** (20 from phase-6 + 44 phase-7-specific)
- **28 code commits**, remainder are docs/governance
- **62 source files** changed: +5,262 / −2,368 lines
- **5 new files** added (`factory.ts`, `factory.spec.ts`, `_parse-utils.ts`, `index.ts`, `_fixtures.ts`)

---

## Code Changes by Category

### Bug Fixes

| Commit | Fix | Impact |
|---|---|---|
| `29a6646` | Recognize `..` as open-ended interval sentinel in `parseValidTime` | ISO 8601-2:2019 `..` was passed to `new Date()` → `NaN`, silently dropping `validTime` for open-ended resources. Fixes #162. |
| `1cb3e43` | Wrap bare-object `observedProperties`/`controlledProperties` into arrays | Single-property datastreams returned as plain objects instead of arrays, breaking property iteration. |
| `940591e` | Fall back to `label` when `definition` is absent in `observedProperties` | Relevant for OSH servers where property definitions may be missing. |
| `0ef76ec` | Guard `extractCSAPIFeature` against null `properties` | Prevents crash on GeoJSON features with null properties. Fixes #143. |
| `010bcfb` | Accept `paramsSchema` fallback for older OSH servers | Handles older OSH builds using `paramsSchema` instead of `parametersSchema`. Fixes #140. (Already fixed locally.) |
| `7858a76` | Remove 27 redundant `as Record` casts in SWE Common parsers | Fixes #148. Improves type safety. |
| `596ef3c` | Constrain `subPath` parameters with union types | Prevents invalid sub-path strings at compile time. |
| `b11f893` | Correct false P7-F3 claims in code comments and tests | Housekeeping — removes misleading comments. |

### Security

| Commit | Fix | Impact |
|---|---|---|
| `b1759e0` | URL scheme validation in `scanCsapiLinks` | Rejects `javascript:`, `data:`, and other dangerous URI schemes in CSAPI link relations. Fixes #147. |

### New Features

| Commit | Feature | Impact |
|---|---|---|
| `00ea485` | `sortBy`/`sortOrder` query parameters in `QueryOptions` | Enables sorted collection fetching (e.g., sort observations by time). Fixes #161. |
| `423da95` | Optional parent IDs for nested command/observation paths | Supports hierarchical system queries (e.g., sub-deployment observations). |
| `829164f` | `parseItem` callback in `parseCollectionResponse` | Customizable per-item parsing for collection responses. |
| New file | `createCSAPIBuilder` factory function + barrel `index.ts` | Clean public API: `import { CSAPIQueryBuilder } from '@camptocamp/ogc-client/csapi'` |

### Major Refactors

| Commit(s) | Refactor | Scope |
|---|---|---|
| `3fb211d`, `154b36e`, `f84a874` | `build()` helper pattern | Rewrites 87 methods across all resource types. Fixes #158, #159, #160, #111. |
| `693388a`, `3f2bd4f` | Remove `assertResourceAvailable` | 72 per-ID methods simplified. Fixes #100. |
| `f25acf0` | Extract `parseBaseStream` helper | Eliminates duplication between `parseDatastream`/`parseControlStream`. |
| `d0912ce` | Extract `requireObject` helper in `part2.ts` | Replaces 5 duplicated null-guard+cast patterns. Fixes #149. |
| `7487d29` | Consolidate `isRecord()` type guard | Moved to shared `_parse-utils.ts`. |
| `916dedb` | Replace raw JSON spread coercions in SensorML parsers | Typed parsers instead of `...json as Record`. |
| `451aa95` | `createCommands` delegates to `createCommand` | Eliminates method duplication. Fixes #150. |
| `85686ed` | Extract shared collection fixture factory | `_fixtures.ts` for integration tests. Fixes #151. |

---

## Test Count Comparison

| Metric | Current `main` | After merge |
|---|---|---|
| Total test cases (`it()`) | 1,697 | 1,752 (+55) |
| `url_builder.spec.ts` tests | 335 | 359 (+24) |
| Source files touched | — | 62 |
| New source files | — | 5 |

---

## Webapp Impact Assessment

### Direct Functional Improvements

1. **`sortBy`/`sortOrder` support** — The explorer can now request sorted collections from the API. This could improve the observation loading flow (e.g., requesting newest-first instead of relying on time-window workarounds).

2. **Nested parent ID paths** — Enables querying observations/commands scoped to a specific parent system, which could improve specificity when the explorer loads ISS or sub-deployment data.

3. **`observedProperties` bare-object fix** — If any datastream on the OSH server returns a single observed property as a plain object instead of an array, the explorer's property display would silently break. This fix makes property iteration robust.

4. **`..` interval parsing fix** — Resources with open-ended `validTime` (e.g., currently-active deployments) were losing their time information. This fix ensures deployment/system temporal metadata is correctly parsed and available for display.

5. **`observedProperties` label fallback** — The OSH server sometimes omits `definition` URIs. This ensures the explorer can still display meaningful property names.

### Security Improvements

6. **Link scheme validation** — Prevents potential XSS vectors if the OSH server ever returns malicious link relations. Defense-in-depth for the explorer's link-following logic.

### Indirect Quality Improvements

7. **87-method `build()` refactor** — While not directly visible to users, this makes the URL builder significantly more maintainable and consistent. Future feature additions to the explorer that need new CSAPI endpoints will be easier to implement correctly.

8. **+55 new tests** — Increased test coverage reduces the risk of regressions when making explorer-specific changes to the client library.

### What It Does NOT Change

- **No changes to the demo/ webapp code** — All changes are in `src/` (the client library). The explorer's Vue components, map rendering, live mode polling, LOB rendering, etc. are completely untouched by this merge.
- **No changes to the HTTP transport layer** — The `apiFetch()` helper and API connection logic in the explorer are separate from the upstream client library.
- **No performance changes** — The refactors are structural (DRY, type safety) not algorithmic. Request patterns and payload sizes are unchanged.

### Verdict

The merge provides **meaningful bug fixes** (#162, #143, property parsing) that affect real data the explorer displays, **one new feature** (`sortBy`/`sortOrder`) we could leverage to improve observation fetching, and **security hardening**. The refactors improve maintainability without introducing risk. The 2 conflicts are trivially resolvable. **Recommended to merge.**
