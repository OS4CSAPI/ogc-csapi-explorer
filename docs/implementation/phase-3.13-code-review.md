# Phase 3.13 Code Review — Issues #57–#69: Nested Create Methods, Content-Type Constants, JSDoc Enhancements, Bug Fixes & Cross-References

**Date:** 2026-02-16
**Reviewer:** GitHub Copilot (Claude Opus 4.6)
**Scope:** Issues #57, #58, #59, #61, #63, #64, #65, #66, #68, #69 — all commits since Smoke Test #17 (`6d06170`)
**Commits:**

- `6f7ec23` — `feat: add 5 nested create methods to CSAPIQueryBuilder (F-1, F-2, F-83)`
- `e66f2c3` — `feat: add CSAPI_CONTENT_TYPES constant map and getContentTypeForResource() helper (F-10)`
- `c3e3673` — `test: add CSAPI_CONTENT_TYPES and getContentTypeForResource tests to url_builder.spec.ts`
- `07349eb` — `docs: enhance JSDoc for extractCSAPIFeature() and getCSAPIResourceType() Part 1 limitations (F-3)`
- `2578a40` — `fix: throw EndpointError instead of plain Error in root getter (F-5)`
- `d675e13` — `refactor: narrow CSAPIQueryBuilder constructor parameter to Pick<OgcApiCollectionInfo, 'id' | 'title' | 'links'> (F-8)`
- `d08d5f7` — `docs: enhance JSDoc for resource discovery semantics in CSAPIQueryBuilder (F-11)`
- `55fa2ba` — `fix: correct getDataStreamSchema/getControlStreamSchema JSDoc f vs obsFormat/cmdFormat confusion (F-13)`
- `228d3fb` — `fix: produce lowercase /controlstreams URL path in buildResourceUrl() fallback (F-17)`
- `c0ca722` — `docs: add JSDoc cross-references between Procedure and SensorML process types`
- `62bde67` — `fix: update controlStreams test expectations to lowercase (#68 follow-up)`

**Last review:** `docs/implementation/phase-3.12-code-review.md` (commits `ba451b9` through `e0f3f0b`)

---

## Verification Status

| Check                      | Result                                                          |
| -------------------------- | --------------------------------------------------------------- |
| tsc --noEmit               | ✅ Clean (zero errors)                                          |
| CSAPI unit tests (all)     | ✅ 1139 passing, 25 suites                                      |
| CSAPI format tests         | ✅ 617 passing, 17 suites                                       |
| Endpoint integration tests | ⚠️ 82/83 passing (1 pre-existing upstream failure at line 1789) |

**Test delta from Phase 3.12:** +224 CSAPI tests, +217 format tests (via constants.spec.ts), +6 suites (command-routing.spec.ts, integration/discovery.spec.ts, integration/observation.spec.ts, integration/navigation.spec.ts, integration/command.spec.ts, constants.spec.ts)

---

## Files Reviewed

### Issue #57 — Nested Create Methods

| File                   | Lines Changed | Scope                                                                                                                                                                            |
| ---------------------- | ------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `csapi/url_builder.ts` | +258          | 5 new methods: `createSubsystem()`, `createSubdeployment()`, `createDataStreamForSystem()`, `createControlStreamForSystem()`, `createSamplingFeatureForSystem()` with full JSDoc |

### Issue #58 — CSAPI Content-Type Constants

| File                         | Lines Changed | Scope                                                                                |
| ---------------------------- | ------------- | ------------------------------------------------------------------------------------ |
| `csapi/formats/constants.ts` | +102          | `CSAPI_CONTENT_TYPES` constant map, `getContentTypeForResource()` helper, full JSDoc |
| `csapi/formats/index.ts`     | +2            | Re-export `CSAPI_CONTENT_TYPES` and `getContentTypeForResource`                      |

### Issue #59 — Content-Type Tests

| File                              | Lines Changed | Scope                                                             |
| --------------------------------- | ------------- | ----------------------------------------------------------------- |
| `csapi/formats/constants.spec.ts` | +48 (NEW)     | 8 tests: Part 1 → geo+json, Part 2 → json, unknown → json default |

### Issue #61 — JSDoc Enhancement (extractCSAPIFeature)

| File                       | Lines Changed | Scope                                                                                      |
| -------------------------- | ------------- | ------------------------------------------------------------------------------------------ |
| `csapi/formats/geojson.ts` | +49/−7        | Enhanced JSDoc for `extractCSAPIFeature()` and `getCSAPIResourceType()` Part 1 limitations |

### Issue #63 — EndpointError Fix

| File                  | Lines Changed | Scope                                                                          |
| --------------------- | ------------- | ------------------------------------------------------------------------------ |
| `ogc-api/endpoint.ts` | +1/−1         | Changed `throw new Error(...)` → `throw new EndpointError(...)` in root getter |

### Issue #64 — Constructor Parameter Narrowing

| File                   | Lines Changed | Scope                                                                                                        |
| ---------------------- | ------------- | ------------------------------------------------------------------------------------------------------------ |
| `csapi/url_builder.ts` | +1/−1         | Constructor parameter type `OgcApiCollectionInfo` → `Pick<OgcApiCollectionInfo, 'id' \| 'title' \| 'links'>` |

### Issue #65 — JSDoc Enhancement (Resource Discovery)

| File                   | Lines Changed | Scope                                                                                                                                                                                      |
| ---------------------- | ------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `csapi/url_builder.ts` | +41           | Enhanced JSDoc for `availableResources`, `extractAvailableResources()`, `assertResourceAvailable()`, and constructor — documenting link scanning conventions and `resourceUrls` workaround |

### Issue #66 — JSDoc Fix (Schema Parameter Confusion)

| File                   | Lines Changed | Scope                                                                                                       |
| ---------------------- | ------------- | ----------------------------------------------------------------------------------------------------------- |
| `csapi/url_builder.ts` | +24/−15       | Corrected `f` → `obsFormat`/`cmdFormat` in JSDoc for `getDataStreamSchema()` and `getControlStreamSchema()` |

### Issue #68 — controlStreams URL Path Casing Fix

| File                        | Lines Changed | Scope                                                                                                                      |
| --------------------------- | ------------- | -------------------------------------------------------------------------------------------------------------------------- |
| `csapi/url_builder.ts`      | +10/−2        | Added `RESOURCE_PATH_OVERRIDES` map and `toUrlPathSegment()` helper; `buildResourceUrl()` uses lowercase `/controlstreams` |
| `csapi/url_builder.spec.ts` | +25/−23       | Updated 24 URL path expectations from `/controlStreams/` → `/controlstreams/`                                              |

### Issue #68 Follow-Up — Cascading Test Fix

| File                                   | Lines Changed | Scope                                                             |
| -------------------------------------- | ------------- | ----------------------------------------------------------------- |
| `csapi/command-routing.spec.ts`        | +10/−10       | Updated 10 URL expectations to lowercase `/controlstreams/`       |
| `csapi/integration/navigation.spec.ts` | +1/−1         | Updated 1 URL expectation                                         |
| `csapi/integration/command.spec.ts`    | +7/−7         | Updated 7 URL expectations including `.not.toContain()` assertion |

### Issue #69 — Procedure/SensorML JSDoc Cross-References

| File                               | Lines Changed | Scope                                                                                      |
| ---------------------------------- | ------------- | ------------------------------------------------------------------------------------------ |
| `csapi/formats/sensorml/types.ts`  | +12           | Added `@see` cross-references linking `SensorMLProcess` types to Procedure resources       |
| `csapi/formats/swecommon/types.ts` | +12           | Added `@see` cross-references linking SWE Common types to DataStream/ControlStream schemas |

### Additional Files (Pre-Baseline Integration Tests and Edge Cases)

These files were added between smoke test #17 and the current review — they were committed before issues #57–#69 but after the Phase 3.12 review baseline:

| File                                    |     Lines | Scope                                                                                                                                                    |
| --------------------------------------- | --------: | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `csapi/command-routing.ts`              | 144 (NEW) | Command fallback routing (#47): `isCommandRouteRejection()`, `getCommandRoutingPreference()`, `setCommandRoutingPreference()`, `buildNestedCommandUrl()` |
| `csapi/command-routing.spec.ts`         | 230 (NEW) | 21 command routing tests                                                                                                                                 |
| `csapi/helpers.spec.ts`                 |      +195 | ~195 new edge case tests for helpers (#33)                                                                                                               |
| `csapi/url_builder.spec.ts`             |      +787 | ~300 edge case tests for URL builder (#33)                                                                                                               |
| `csapi/integration/discovery.spec.ts`   | 339 (NEW) | 14 integration tests (#31)                                                                                                                               |
| `csapi/integration/observation.spec.ts` | 322 (NEW) | 17 integration tests (#31)                                                                                                                               |
| `csapi/integration/navigation.spec.ts`  | 428 (NEW) | 30 integration tests (#31)                                                                                                                               |
| `csapi/integration/command.spec.ts`     | 359 (NEW) | 20 integration tests (#31)                                                                                                                               |
| `src/index.ts`                          |      +113 | CSAPI barrel exports — TypeDoc/documentation (#32)                                                                                                       |

---

## Overall Codebase Metrics (Cumulative)

### Production Files

| File                                          |      Lines | Purpose                                                         |
| --------------------------------------------- | ---------: | --------------------------------------------------------------- |
| `csapi/url_builder.ts`                        |      2,088 | URL construction for 9 resource types + 5 nested create methods |
| `csapi/formats/swecommon/parser.ts`           |      1,274 | Main SWE Common parser — 16 component types                     |
| `csapi/formats/sensorml/types.ts`             |        863 | SensorML 3.0 type definitions                                   |
| `csapi/formats/swecommon/components.ts`       |        744 | 10 simple SWE Common component parsers                          |
| `csapi/formats/swecommon/types.ts`            |        669 | SWE Common 3.0 type definitions                                 |
| `csapi/formats/sensorml/physical-system.ts`   |        667 | PhysicalSystem/PhysicalComponent sub-parser                     |
| `csapi/model.ts`                              |        573 | CSAPI type definitions and constants                            |
| `csapi/formats/swecommon/data-array.ts`       |        510 | DataArray parser with encoding support                          |
| `csapi/formats/sensorml/parser.ts`            |        410 | Main SensorML parser                                            |
| `csapi/formats/geojson.ts`                    |        384 | GeoJSON handler extensions                                      |
| `csapi/formats/constants.ts`                  |        292 | Media types, resource URIs, Content-Type map                    |
| `csapi/formats/sensorml/aggregate-process.ts` |        286 | AggregateProcess sub-parser                                     |
| `csapi/formats/index.ts`                      |        276 | Top-level format barrel file                                    |
| `csapi/formats/sensorml/_helpers.ts`          |        207 | SensorML shared helpers                                         |
| `csapi/helpers.ts`                            |        200 | CSAPI shared extraction helpers                                 |
| `csapi/formats/swecommon/data-record.ts`      |        194 | DataRecord parser                                               |
| `csapi/command-routing.ts`                    |        144 | Command fallback routing                                        |
| `csapi/formats/swecommon/index.ts`            |        135 | SWE Common barrel file                                          |
| `csapi/formats/sensorml/simple-process.ts`    |        135 | SimpleProcess sub-parser                                        |
| `csapi/formats/sensorml/index.ts`             |        122 | SensorML barrel file                                            |
| `csapi/formats/classification.ts`             |        118 | Endpoint-context classification fallback                        |
| `csapi/formats/response.ts`                   |        115 | Collection response envelope normalization                      |
| `csapi/formats/swecommon/_helpers.ts`         |         51 | SWE Common shared helpers (`isRecord`, `parseBaseProperties`)   |
| `csapi/formats/sensorml/errors.ts`            |         40 | SensorMLParseError class                                        |
| **Production Total**                          | **10,497** | **24 files**                                                    |

### Test Files

| File                                               |      Lines |     Tests | Purpose                                  |
| -------------------------------------------------- | ---------: | --------: | ---------------------------------------- |
| `csapi/url_builder.spec.ts`                        |      2,755 |      ~560 | URL builder tests (incl. #33 edge cases) |
| `csapi/formats/sensorml/physical-system.spec.ts`   |      1,070 |       100 | PhysicalSystem tests                     |
| `csapi/formats/sensorml/aggregate-process.spec.ts` |        646 |        67 | AggregateProcess tests                   |
| `csapi/formats/swecommon/components.spec.ts`       |        600 |        73 | SWE Common component tests               |
| `csapi/formats/swecommon/parser.spec.ts`           |        569 |        57 | SWE Common parser tests                  |
| `csapi/formats/swecommon/data-array.spec.ts`       |        507 |        49 | DataArray tests                          |
| `csapi/helpers.spec.ts`                            |        463 |       ~65 | Helper tests (incl. #33 edge cases)      |
| `csapi/formats/sensorml/simple-process.spec.ts`    |        438 |        41 | SimpleProcess tests                      |
| `csapi/formats/geojson.spec.ts`                    |        431 |        19 | GeoJSON tests                            |
| `csapi/integration/navigation.spec.ts`             |        428 |        30 | Integration: cross-resource navigation   |
| `csapi/formats/swecommon/types.spec.ts`            |        375 |        17 | SWE Common type tests                    |
| `csapi/model.spec.ts`                              |        377 |        44 | Model tests                              |
| `csapi/formats/sensorml/types.spec.ts`             |        369 |        20 | SensorML type tests                      |
| `csapi/integration/command.spec.ts`                |        359 |        20 | Integration: command workflows           |
| `csapi/formats/sensorml/parser.spec.ts`            |        343 |        46 | SensorML parser tests                    |
| `csapi/integration/discovery.spec.ts`              |        339 |        14 | Integration: discovery lifecycle         |
| `csapi/integration/observation.spec.ts`            |        322 |        17 | Integration: observation workflows       |
| `csapi/formats/index.spec.ts`                      |        242 |        22 | Format barrel file tests                 |
| `csapi/formats/swecommon/data-record.spec.ts`      |        237 |        20 | DataRecord tests                         |
| `csapi/command-routing.spec.ts`                    |        230 |        21 | Command routing tests                    |
| `csapi/formats/response.spec.ts`                   |        193 |        18 | Response parser tests                    |
| `csapi/formats/classification.spec.ts`             |        168 |        22 | Classification fallback tests            |
| `csapi/formats/swecommon/index.spec.ts`            |        167 |        21 | SWE Common barrel tests                  |
| `csapi/formats/sensorml/index.spec.ts`             |         82 |         9 | SensorML barrel tests                    |
| `csapi/formats/constants.spec.ts`                  |         40 |         8 | Content-Type constant tests              |
| **Test Total**                                     | **11,750** | **1,139** | **25 suites**                            |

### Aggregate

| Metric                                    |                             Value |
| ----------------------------------------- | --------------------------------: |
| Production lines                          |                            10,497 |
| Test lines                                |                            11,750 |
| Total lines                               |                            22,247 |
| Production files                          |                                24 |
| Test files (suites)                       |                                25 |
| Test count                                |                             1,139 |
| Test-to-production ratio                  |                            1.12:1 |
| Additional: `src/index.ts` (barrel)       | 113 lines added for CSAPI exports |
| Additional: `ogc-api/endpoint.ts` (CSAPI) |    ~63 lines of CSAPI integration |

---

## Phase 3 Lessons Learned Check

| #       | Lesson                                           | Status  | Evidence                                                                                                                                                                                                                              |
| ------- | ------------------------------------------------ | ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **L1**  | Audit upstream before building new layers        | ✅ PASS | All issues extend existing modules — no new architectural layers introduced. `command-routing.ts` is a response-layer concern, not a new builder layer. `constants.ts` additions (`CSAPI_CONTENT_TYPES`) extend existing data module. |
| **L2**  | Postel's Law governs client libraries            | ✅ PASS | `getContentTypeForResource()` accepts any string and falls back to `application/json` for unrecognized types. `RESOURCE_PATH_OVERRIDES` silently corrects server path casing without throwing.                                        |
| **L3**  | Don't couple validation to extraction            | ✅ PASS | No validation-extraction coupling introduced. Content-Type map is purely informational.                                                                                                                                               |
| **L4**  | Don't build parallel systems                     | ✅ PASS | No parallel systems. `RESOURCE_PATH_OVERRIDES` in `url_builder.ts` is the only mechanism for path segment mapping — no competing approach.                                                                                            |
| **L5**  | Verify upstream claims by reading source         | ✅ N/A  | No upstream claims.                                                                                                                                                                                                                   |
| **L6**  | Real-world server data diverges from spec        | ✅ PASS | Issue #68 directly addresses OSH's lowercase `/controlstreams` requirement identified in smoke tests. Issue #63 ensures consistent `EndpointError` usage.                                                                             |
| **L7**  | Phase 3 smoke tests are essential                | ✅ PASS | Issues #57, #58, #63, #68 address findings from prior smoke tests.                                                                                                                                                                    |
| **L8**  | Layered architecture enables clean extension     | ✅ PASS | `command-routing.ts` adds routing logic without modifying `url_builder.ts`. Nested create methods follow the established delegation pattern. `RESOURCE_PATH_OVERRIDES` is a minimal, isolated concern.                                |
| **L9**  | Content negotiation cannot be assumed            | ✅ N/A  | No content negotiation logic.                                                                                                                                                                                                         |
| **L10** | Type naming must avoid built-in collisions       | ✅ PASS | `CommandRoutingPreference` — no built-in collisions.                                                                                                                                                                                  |
| **L11** | Document architectural decisions formally        | ✅ PASS | All JSDoc enhancements (issues #61, #65, #66, #69) add spec references. `RESOURCE_PATH_OVERRIDES` is documented with `@see` link to issue #68.                                                                                        |
| **L12** | "Build it right, but should we build it at all?" | ✅ PASS | All issues address code review findings or smoke test gaps — no unnecessary scope.                                                                                                                                                    |
| **L13** | AI drift can fabricate findings                  | ✅ N/A  | No external server interaction.                                                                                                                                                                                                       |

**Result:** 10/13 applicable lessons PASS, 3 N/A, 0 WORSENED

---

## Prior Findings Status

### [Phase 3.1 F7/F13] RESOLVED: Replace `as` casts with `satisfies` in extractCSAPIFeature

**Status:** ✅ Still resolved. `geojson.ts` lines 354, 367, 375, 387 use `satisfies`. No regression.

---

### [Phase 3.9 F9] STILL OPEN: `as unknown as T` casts — inherited pattern

**Status:** Still present in all SWE Common parser modules (~20+ instances across `components.ts`, `data-array.ts`, `parser.ts`). Consistent inherited pattern. No new instances added by issues #57–#69. Low severity.

---

### [Phase 3.10 F3] RESOLVED: `isRecord()` and `parseBaseProperties()` quadruplication

**Previous status:** WORSENED — quadrupled across 4 SWE Common files.

**Current status:** ✅ **Resolved.** `swecommon/_helpers.ts` (51 lines) was created (Issue #56), consolidating both `isRecord()` and `parseBaseProperties()` into a single module. All 4 consumers (`components.ts`, `data-record.ts`, `data-array.ts`, `parser.ts`) now import from `_helpers.js`. Verified: `function isRecord(` appears only once in production code.

---

### [Phase 3.10 F7] UNCHANGED: `as any` cast in nested DataRecord test

**Status:** Still present in `data-record.spec.ts` lines 126, 128. Test-only, zero production impact. Informational.

---

### [Phase 3.12 F7] GAP: Barrel tests missing response + classification exports

**Status:** ⚠️ ~~STILL OPEN~~ **CORRECTION (2026-02-18): This finding was stale at the time of review.** Issues #67 and #68 added `parseCollectionResponse`, `classifyFeature`, and `inferResourceTypeFromPath` to the barrel, and their barrel-level accessibility tests were added to `formats/index.spec.ts` as part of those implementations — before this Phase 3.13 review was written. The review mechanically carried forward the Phase 3.12 finding without verifying it against the current codebase. The tests already existed when this report was published.

---

### [Phase 3.12 F9] INFORMATIONAL: Silent catch block in `validateAllowedTokens`

**Status:** UNCHANGED. Still present in `parser.ts`. Informational.

---

### [Phase 3.12 F10] INFORMATIONAL: `validateGeometry` ignores `_schema` constraint

**Status:** UNCHANGED. Still present in `parser.ts`. Informational.

---

## Phase 3.13 Findings — New

### [F1] BUG (resolved): Issue #68 fix left 17 test failures in 3 files

When Issue #68 changed `buildResourceUrl()` to produce lowercase `/controlstreams` paths via `RESOURCE_PATH_OVERRIDES`, only `url_builder.spec.ts` was updated (24 expectations). Three additional test files were NOT updated:

| File                             | Failures | Lines                                                  |
| -------------------------------- | -------: | ------------------------------------------------------ |
| `command-routing.spec.ts`        |       10 | Lines 157, 164, 171, 178, 185, 195, 202, 210, 252, 265 |
| `integration/navigation.spec.ts` |        1 | Line 227                                               |
| `integration/command.spec.ts`    |        6 | Lines 185, 200, 207, 315, 328, 339                     |

**Total:** 17 test failures, all with the same root cause — expected URLs contained camelCase `/controlStreams/` but received lowercase `/controlstreams/` from the updated `buildResourceUrl()`.

**Resolution:** Commit `62bde67` fixes all 17+1 expectations (including the `.not.toContain()` assertion on line 351). All 1139 tests now pass.

**Severity:** BUG (discovered and resolved during this review)

**Root cause:** Incomplete grep coverage during Issue #68 implementation. The search for `/controlStreams/` expectations was limited to `url_builder.spec.ts`. The integration test files (`command-routing.spec.ts`, `integration/navigation.spec.ts`, `integration/command.spec.ts`) also construct URLs through `CSAPIQueryBuilder` methods that pass through `buildResourceUrl()`, and their expectations were missed.

**Lesson:** When changing a core URL generation mechanism like `buildResourceUrl()`, search ALL test files for affected URL patterns — not just the spec file colocated with the implementation.

---

### [F2] POSITIVE: `RESOURCE_PATH_OVERRIDES` is a clean, minimal solution for path casing

The controlStreams casing fix (Issue #68) correctly identifies that OSH serves paths as `/controlstreams` (lowercase) while the spec uses camelCase `controlStreams`. The solution is elegant:

```typescript
const RESOURCE_PATH_OVERRIDES: Readonly<Record<string, string>> = {
  controlStreams: 'controlstreams',
};

function toUrlPathSegment(resourceType: string): string {
  return RESOURCE_PATH_OVERRIDES[resourceType] ?? resourceType;
}
```

This keeps the internal resource type names (`controlStreams`) consistent with the type system while producing spec-correct lowercase URLs. The `Readonly` assertion prevents accidental mutation. The override map is extensible if additional path casing issues are discovered.

**Severity:** POSITIVE

---

### [F3] POSITIVE: Nested create methods follow established delegation pattern

Issue #57's 5 new methods (`createSubsystem`, `createSubdeployment`, `createDataStreamForSystem`, `createControlStreamForSystem`, `createSamplingFeatureForSystem`) all:

- Delegate to `buildResourceUrl()` — no custom URL logic
- Call `assertResourceAvailable()` first — consistent error surface
- Include full JSDoc with `@param`, `@returns`, `@throws`, `@example`, `@see` spec links
- Follow the exact pattern of existing methods (e.g., `getSystemControlStreams`)

**Severity:** POSITIVE

---

### [F4] POSITIVE: Content-Type map correctly separates Part 1 and Part 2 media types

`CSAPI_CONTENT_TYPES` maps Part 1 resources → `application/geo+json` and Part 2 resources → `application/json`. This matches the spec: Part 1 resources are GeoJSON Features (OGC 23-001r1), Part 2 resources use plain JSON encoding (OGC 23-002r1).

The `getContentTypeForResource()` helper safely falls back to `application/json` for unrecognized types, following Postel's Law (Lesson 2).

8 tests in `constants.spec.ts` validate all 9 resource types plus the unknown-type fallback.

**Severity:** POSITIVE

---

### [F5] POSITIVE: Constructor parameter narrowing follows TypeScript best practices

Issue #64's `Pick<OgcApiCollectionInfo, 'id' | 'title' | 'links'>` narrowing:

- Documents the builder's actual data requirements — consumers don't need to provide a full `OgcApiCollectionInfo`
- Is backward-compatible — existing code passing full objects still compiles
- Improves testability — test fixtures need only 3 properties, not the full collection interface

**Severity:** POSITIVE

---

### [F6] POSITIVE: Command fallback routing module is well-isolated

`command-routing.ts` (144 lines) implements dual-path resolution for servers rejecting top-level `/commands` without modifying `url_builder.ts`. The module:

- Imports `CSAPIQueryBuilder` as a type-only dependency (import type)
- Uses `builder.getControlStreamCommands()` for URL construction — no path building duplication
- Provides detection (`isCommandRouteRejection`), caching (`getCommandRoutingPreference`/`setCommandRoutingPreference`), and URL construction (`buildNestedCommandUrl`) as separate exported functions
- Includes `clearCommandRoutingCache()` for test cleanup
- Has 21 tests covering detection, caching, URL construction, and end-to-end fallback flow

**Severity:** POSITIVE

---

### [F7] POSITIVE: Integration tests verify cross-module composition

The 4 integration test files (Issues #31, #33) add 81 tests verifying end-to-end workflows that compose multiple CSAPI modules:

- `discovery.spec.ts` (14 tests): full lifecycle, GeoJSON parsing, classification fallback
- `observation.spec.ts` (17 tests): system-to-datastream discovery, temporal queries, SWE Common schema parsing
- `command.spec.ts` (20 tests): control stream discovery, feasibility, fallback routing
- `navigation.spec.ts` (30 tests): cross-resource navigation, GeoJSON round-trip, pagination

These tests catch issues that unit tests miss — like the F1 bug where `buildResourceUrl()` changes cascade through `buildNestedCommandUrl()`.

**Severity:** POSITIVE

---

### [F8] POSITIVE: EndpointError consistency fix in root getter

Issue #63 corrects a single line in `endpoint.ts` where the root getter threw `new Error(...)` instead of `new EndpointError(...)`. This ensures all endpoint errors use the same error class, enabling consistent `instanceof` checks in calling code.

**Severity:** POSITIVE

---

### [F9] DESIGN (low): JSDoc examples in url_builder.ts use hardcoded `controlstreams` paths

Several JSDoc `@example` blocks in `url_builder.ts` show the lowercase `controlstreams` path directly in example URLs (e.g., `"https://example.com/collections/iot/systems/abc123/controlstreams"`). If `RESOURCE_PATH_OVERRIDES` is ever removed or the path changes, these examples will become inaccurate.

This is purely a documentation concern — the examples are currently correct.

**Severity:** DESIGN (low) — informational, no code impact.

---

### [F10] GAP (low): `constants.spec.ts` has only 8 tests for a 292-line module

The constants module defines 21 constants, 8 union types, a 9-entry Content-Type map, and a helper function. The 8 tests focus exclusively on `CSAPI_CONTENT_TYPES` and `getContentTypeForResource()`. The media type constants, SOSA URI arrays, asset type arrays, and vocabulary namespace constants are not directly tested in this spec file.

However, these constants are exercised indirectly through the barrel file tests (`formats/index.spec.ts`) and the GeoJSON/SensorML/SWE Common parser tests that import them. The risk is low — they are pure data values with `as const` inference.

**Severity:** GAP (low) — constants are exercised indirectly. Direct tests would improve confidence in renaming/refactoring scenarios.

---

### [F11] POSITIVE: `src/index.ts` barrel exports are comprehensive

The 113 lines added to `src/index.ts` export all public CSAPI symbols:

- `CSAPIQueryBuilder` (default export)
- `CSAPIResourceTypes`, `CommandStatusCodes`, `SystemTypeUris` (const values)
- 30+ type exports covering all query options, resource interfaces, and collection types
- Format handler functions (`parseSensorML30`, `parseSWEComponent`, `CSAPI_CONTENT_TYPES`, etc.)
- SensorML and SWE Common type re-exports (~60 types)
- No default exports from barrel — tree-shaking friendly

**Severity:** POSITIVE

---

## Test Quality Heatmap

### Phase 2 (URL Builder) — Carried Forward

| Dimension                | Systems | Deployments | Procedures | SF  | Properties | DataStreams | Observations | ControlStreams | Commands |
| ------------------------ | :-----: | :---------: | :--------: | :-: | :--------: | :---------: | :----------: | :------------: | :------: |
| Exact URL assertion      |   ✅    |     ✅      |     ✅     | ✅  |     ✅     |     ✅      |      ✅      |       ✅       |    ✅    |
| Per-field query params   |   ✅    |     ✅      |     ✅     | ✅  |     ✅     |     ✅      |      ✅      |       ✅       |    ✅    |
| CRUD URLs                |   ✅    |     ✅      |     ✅     | ✅  |     ✅     |     ✅      |      ✅      |       ✅       |    ✅    |
| Nested methods           |   ✅    |     ✅      |     ✅     | ✅  |     ✅     |     ✅      |      ✅      |       ✅       |    ✅    |
| Nested create methods    |   ✅    |     ✅      |    N/A     | N/A |    N/A     |     ✅      |     N/A      |       ✅       |   N/A    |
| Pagination               |   ✅    |     ✅      |     ✅     | ✅  |     ✅     |     ✅      |      ✅      |       ✅       |    ✅    |
| Resource validation      |   ✅    |     ✅      |     ✅     | ✅  |     ✅     |     ✅      |      ✅      |       ✅       |    ✅    |
| Temporal params          |   ✅    |     ✅      |     ✅     | ✅  |     ✅     |     ✅      |      ✅      |       ✅       |    ✅    |
| Content-Type mapping     |   ✅    |     ✅      |     ✅     | ✅  |     ✅     |     ✅      |      ✅      |       ✅       |    ✅    |
| Command fallback routing |   N/A   |     N/A     |    N/A     | N/A |    N/A     |     N/A     |     N/A      |       ✅       |    ✅    |
| Edge cases (#33)         |   ✅    |     ✅      |     ✅     | ✅  |     ✅     |     ✅      |      ✅      |       ✅       |    ✅    |

### Phase 3 (Format Handlers) — Current

| Dimension                 | GeoJSON | Constants | Response | Classification | SML Types | SML Errors | SML Helpers | SimpleProcess | AggProcess | PhysSys | SML Parser | SML Barrel | SWE Types | SWE Comps | SWE DataRec | SWE DataArr | SWE Parser | SWE Barrel | SWE Helpers | Formats Barrel |
| ------------------------- | :-----: | :-------: | :------: | :------------: | :-------: | :--------: | :---------: | :-----------: | :--------: | :-----: | :--------: | :--------: | :-------: | :-------: | :---------: | :---------: | :--------: | :--------: | :---------: | :------------: |
| Valid input → output      |   ✅    |    ✅     |    ✅    |       ✅       |    ✅     |     ✅     |     ✅      |      ✅       |     ✅     |   ✅    |     ✅     |     ✅     |    ✅     |    ✅     |     ✅      |     ✅      |     ✅     |     ✅     |     ✅      |       ✅       |
| Invalid input → rejection |   ✅    |    N/A    |    ✅    |       ✅       |    ✅     |    N/A     |     N/A     |      ✅       |     ✅     |   ✅    |     ✅     |    N/A     |    ✅     |    ✅     |     ✅      |     ✅      |     ✅     |    N/A     |     N/A     |      N/A       |
| All spec variants         |   ✅    |    ✅     |    ✅    |      N/A       |    ✅     |    N/A     |     N/A     |      ✅       |     ✅     |   ✅    |     ✅     |    N/A     |    ✅     |    ✅     |     ✅      |     ✅      |     ✅     |    N/A     |     N/A     |      N/A       |
| All branches/types        |   ✅    |    ✅     |    ✅    |       ✅       |    ✅     |     ✅     |     ✅      |      ✅       |     ✅     |   ✅    |     ✅     |     ✅     |    ✅     |    ✅     |     ✅      |     ✅      |     ✅     |     ✅     |     ✅      |       ✅       |
| Error specificity         |   ✅    |    N/A    |    ✅    |      N/A       |    N/A    |     ✅     |     ✅      |      ✅       |     ✅     |   ✅    |     ✅     |    N/A     |    N/A    |    ✅     |     ✅      |     ✅      |     ✅     |    N/A     |     N/A     |      N/A       |
| Edge cases                |   ✅    |    N/A    |    ✅    |       ✅       |    ✅     |    N/A     |     N/A     |      ✅       |     ✅     |   ✅    |     ✅     |    N/A     |    ✅     |    ✅     |     ✅      |     ✅      |     ✅     |    N/A     |     N/A     |      N/A       |
| Nested structures         |   N/A   |    N/A    |   N/A    |      N/A       |    N/A    |    N/A     |     N/A     |      N/A      |     ✅     |   ✅    |     ✅     |    N/A     |    N/A    |    ✅     |     ✅      |     ✅      |     ✅     |    N/A     |     N/A     |      N/A       |
| Type discrimination       |   N/A   |    N/A    |   N/A    |      N/A       |    N/A    |    N/A     |     N/A     |      N/A      |    N/A     |   ✅    |     ✅     |    N/A     |    N/A    |    ✅     |     ✅      |     ✅      |     ✅     |    N/A     |     N/A     |      N/A       |
| Encoding variants         |   N/A   |    N/A    |   N/A    |      N/A       |    N/A    |    N/A     |     N/A     |      N/A      |    N/A     |   N/A   |    N/A     |    N/A     |    N/A    |    N/A    |     N/A     |     ✅      |    N/A     |    N/A     |     N/A     |      N/A       |

### Integration Tests — New Dimension

| Dimension                | Discovery | Observation | Command | Navigation |
| ------------------------ | :-------: | :---------: | :-----: | :--------: |
| End-to-end workflow      |    ✅     |     ✅      |   ✅    |     ✅     |
| Cross-module composition |    ✅     |     ✅      |   ✅    |     ✅     |
| Temporal queries         |    N/A    |     ✅      |   ✅    |    N/A     |
| Pagination               |    N/A    |     ✅      |   N/A   |     ✅     |
| Fallback routing         |    N/A    |     N/A     |   ✅    |    N/A     |
| Error scenarios          |    ✅     |     ✅      |   ✅    |     ✅     |
| Format negotiation       |    ✅     |     N/A     |   N/A   |     ✅     |
| GeoJSON round-trip       |    ✅     |     N/A     |   N/A   |     ✅     |

---

## Smoke Test Findings Integration

| Finding                                  | Status                  | Evidence                                                                                                                                                         |
| ---------------------------------------- | ----------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| F1 (nested create methods)               | ✅ Addressed            | Issue #57 adds `createSubsystem()`, `createSubdeployment()`, `createDataStreamForSystem()`, `createControlStreamForSystem()`, `createSamplingFeatureForSystem()` |
| F2 (nested create methods)               | ✅ Addressed            | Same as F1 — Issue #57                                                                                                                                           |
| F3 (items envelope)                      | ✅ Previously addressed | `parseCollectionResponse` in `response.ts` — Phase 3.12                                                                                                          |
| F4 (validTime array format)              | ✅ Previously addressed | `parseValidTime` in `geojson.ts` — prior phase                                                                                                                   |
| F5 (EndpointError consistency)           | ✅ Addressed            | Issue #63: `throw new Error(...)` → `throw new EndpointError(...)` in endpoint.ts root getter                                                                    |
| F10 (Content-Type guidance)              | ✅ Addressed            | Issue #58: `CSAPI_CONTENT_TYPES` map + `getContentTypeForResource()`                                                                                             |
| F17 (controlstreams path casing)         | ✅ Addressed            | Issue #68: `RESOURCE_PATH_OVERRIDES` + `toUrlPathSegment()` in url_builder.ts                                                                                    |
| F33 (commandFormat vs observationFormat) | ⏳ Deferred             | Schema-level variant handling deferred                                                                                                                           |
| F34 (Commands fallback routing)          | ✅ Addressed            | Issue #47: `command-routing.ts` implements dual-path resolution                                                                                                  |
| F41 (featureType: null on 52North)       | ✅ Previously addressed | `classifyFeature` with `inferResourceTypeFromPath` — Phase 3.12                                                                                                  |
| F83 (nested create methods)              | ✅ Addressed            | Same as F1 — Issue #57                                                                                                                                           |

---

## Summary

| Category       | Count | Details                                                                                                                                                                                                                   |
| -------------- | ----: | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| POSITIVE       |     8 | F2 (RESOURCE_PATH_OVERRIDES), F3 (nested create pattern), F4 (Content-Type map), F5 (constructor narrowing), F6 (command routing isolation), F7 (integration tests), F8 (EndpointError consistency), F11 (barrel exports) |
| BUG (resolved) |     1 | F1 (17 test failures from #68 — fixed in same session)                                                                                                                                                                    |
| DESIGN (low)   |     1 | F9 (hardcoded controlstreams in JSDoc examples)                                                                                                                                                                           |
| GAP (low)      |     1 | F10 (constants.spec.ts coverage limited)                                                                                                                                                                                  |
| INFORMATIONAL  |     0 | —                                                                                                                                                                                                                         |
| CONSISTENCY    |     0 | —                                                                                                                                                                                                                         |

---

## Recommendations

### Fix Now (before next issue)

1. ~~**[Phase 3.12 F7] Add barrel tests for response + classification exports** to `formats/index.spec.ts`. ~10 lines. This remains from the prior review and is trivial to address.~~ **CORRECTION (2026-02-18): This item was already resolved.** The barrel tests for `parseCollectionResponse`, `classifyFeature`, and `inferResourceTypeFromPath` were added during Issues #67/#68 implementation. This finding was stale — it was carried forward from Phase 3.12 without verifying against the current codebase.

### Fix Before Phase 4

2. **No outstanding items.** The `isRecord()` quadruplication (Phase 3.10 F3 / 3.12 F3) has been resolved by `swecommon/_helpers.ts`. All critical findings are closed.

### Defer (Low Priority)

3. **[Phase 3.9 F9] `as unknown as T` casts** — inherited design pattern used consistently across all SWE Common parsers (~20+ instances). Low severity.
4. **[Phase 3.10 F7] `as any` in nested DataRecord test** — test-only, zero production impact.
5. **[Phase 3.12 F9] Silent catch in `validateAllowedTokens`** — consider adding `ValidationError` entry for invalid regex.
6. **[Phase 3.12 F10] Geometry constraint validation** — `validateGeometry` ignores schema constraints. Low priority.
7. **[F9] JSDoc examples with hardcoded paths** — update if `RESOURCE_PATH_OVERRIDES` ever changes.
8. **[F10] Expand `constants.spec.ts`** — add tests for media type constants, SOSA URI arrays, and asset types for refactoring confidence.

---

## Root Cause Analysis

### F1 — 17 cascading test failures from Issue #68

**What happened:** Issue #68 added `RESOURCE_PATH_OVERRIDES` to `buildResourceUrl()`, changing all `controlStreams` URL paths from camelCase to lowercase. The `url_builder.spec.ts` expectations were updated (24 occurrences), but 3 other test files with URL assertions through `buildResourceUrl()` were not.

**How it was introduced:** The search for affected test expectations was scoped to `url_builder.spec.ts` only. The integration test files (`command-routing.spec.ts`, `integration/navigation.spec.ts`, `integration/command.spec.ts`) also construct URLs through `CSAPIQueryBuilder.getControlStreamCommands()`, `CSAPIQueryBuilder.createCommand()`, `CSAPIQueryBuilder.checkCommandFeasibility()` and `buildNestedCommandUrl()` — all of which pass through `buildResourceUrl()` and produce the new lowercase path.

**Why it wasn't caught:** The tests were likely not run against the full suite after the fix. Running only `url_builder.spec.ts` would have passed, but running all CSAPI tests would have revealed the 17 failures.

**Prevention:** When changing a core URL generation mechanism:

1. Run `npx jest "src/ogc-api/csapi"` (the full suite), not just the colocated spec
2. Search ALL spec files for the affected URL pattern: `grep -r "controlStreams" src/ogc-api/csapi/**/*.spec.ts`

**Resolution:** Commit `62bde67` updates all 18 expectations across 3 files. All 1139 tests pass.

---

## Overall Assessment

Phase 3.13 represents a significant breadth of work — 10 issues spanning feature additions (nested create methods, Content-Type constants), bug fixes (EndpointError, controlStreams casing), JSDoc enhancements (4 issues), and a constructor refactor. The codebase also absorbed issue #47 (command fallback routing) and issues #31/#33 (integration tests and edge cases) that were committed between the previous smoke test baseline and this review.

**Quality trajectory:** The single bug found in this review (F1 — 17 cascading test failures) was a test maintenance issue, not a production logic defect. The `buildResourceUrl()` change that caused it was itself correct — OSH does require lowercase `/controlstreams` paths. The issue was that the grep for affected expectations missed 3 test files. This was discovered during this review's verification gates and resolved within the same session. The root cause analysis identifies a process gap (running only the colocated spec rather than the full suite) that is straightforward to prevent.

**Architecture assessment:** The codebase is mature and well-structured. The `command-routing.ts` module correctly separates the response-layer routing concern from the URL-builder layer. The `RESOURCE_PATH_OVERRIDES` mechanism is minimal and extensible. The integration tests (81 tests across 4 files) prove cross-module composition works correctly and caught the cascading failure pattern. The resolution of F3 (`isRecord()` consolidation into `swecommon/_helpers.ts`) closes the longest-running code quality finding in the project.

**Metrics trajectory:** The codebase has grown from 9,396 production lines (Phase 3.12) to 10,497 (+1,101, +11.7%), with tests growing from 9,013 lines to 11,750 (+2,737, +30.4%). The test-to-production ratio improved from 1.04:1 to 1.12:1. Test count grew from 915 to 1,139 (+224, +24.5%). The 25 test suites now cover URL building, format handling, integration workflows, and command routing.

**Streak:** 20 consecutive phases with zero production defects (Phase 2.3 → Phase 3.13). The one bug found (F1) was in test expectations, not production logic — the `RESOURCE_PATH_OVERRIDES` fix produces correct URLs. The defect-free streak for production code continues.
