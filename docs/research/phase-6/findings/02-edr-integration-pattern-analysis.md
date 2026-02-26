# Findings Report 02: EDR vs CSAPI Integration Pattern Comparison — Why the Patterns Must Differ

> **Plan 2 of 8** | **Phase 6 — Upstream Acceptance Refactoring**

---

## Metadata

| Field                  | Value                                                                                                 |
| ---------------------- | ----------------------------------------------------------------------------------------------------- |
| **Research Plan**      | [Plan 02: EDR Integration Pattern Analysis](../research-plans/02-edr-integration-pattern-analysis.md) |
| **Plan Type**          | Internal analysis                                                                                     |
| **Date Started**       | 2026-02-23                                                                                            |
| **Date Completed**     | 2026-02-23                                                                                            |
| **Research Time**      | ~2 hours (actual)                                                                                     |
| **Estimated Time**     | 1–2 hours (from plan)                                                                                 |
| **Questions Answered** | 35 of 35 detailed questions                                                                           |
| **Depends On**         | None                                                                                                  |
| **Blocks**             | Plan 06 (Endpoint Decoupling Architecture), Plan 08 (File-Level Changelist)                           |

---

## Source Summary

### Primary Sources Consulted

| Source                 | Path / URL                                             | What Was Extracted                                                                                                                                                               |
| ---------------------- | ------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| OGC API endpoint class | `src/ogc-api/endpoint.ts` (896 lines)                  | All EDR and CSAPI imports, properties, methods, cache maps, private helpers; `edr()` and `csapi()` method bodies                                                                 |
| Info utilities         | `src/ogc-api/info.ts` (~350 lines)                     | `checkHasEnvironmentalDataRetrieval`, `checkHasConnectedSystems`, `parseCollections` — confirmed zero imports from either `edr/` or `csapi/`                                     |
| OGC API model types    | `src/ogc-api/model.ts` (279 lines)                     | EDR-specific types (~45 lines): `DataQueryTypes`, `DataQueryType`, `EdrParameterInfo`, `data_queries` and `parameter_names` on `OgcApiCollectionInfo`. Zero CSAPI-specific types |
| Root barrel file       | `src/index.ts` (252 lines)                             | Zero EDR exports; ~183 lines of CSAPI exports (lines 45–227)                                                                                                                     |
| EDR module             | `src/ogc-api/edr/` (3 non-spec files, 656 lines)       | `url_builder.ts` (529), `model.ts` (110), `helpers.ts` (17) — constructor signature, module structure                                                                            |
| CSAPI module           | `src/ogc-api/csapi/` (27 non-spec files, 11,767 lines) | Module structure, constructor signature, `scanCsapiLinks()` implementation, format parser hierarchy                                                                              |
| Endpoint tests         | `src/ogc-api/endpoint.spec.ts`                         | EDR test block (lines 2543–2835, 11 `it()` blocks, ~293 lines); CSAPI test block (lines 2836–2900, 6 `it()` blocks, ~64 lines)                                                   |
| CSAPIQueryBuilder      | `src/ogc-api/csapi/url_builder.ts` (2,307 lines)       | Constructor: 2 params (`OgcApiCollectionInfo` + `Map<string, string>`), link scanning, resource discovery                                                                        |
| EDRQueryBuilder        | `src/ogc-api/edr/url_builder.ts` (529 lines)           | Constructor: 1 param (`OgcApiCollectionInfo`), data query extraction                                                                                                             |
| CSAPI helpers          | `src/ogc-api/csapi/helpers.ts` (200 lines)             | `scanCsapiLinks()` (lines 129–174): scans link relations for `ogc-cs:` prefixed, plain resource name, and `items` href patterns                                                  |

### External Sources Consulted

| Source          | URL                                                 | What Was Extracted                                                                                                     |
| --------------- | --------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| PR #114 (EDR)   | https://github.com/camptocamp/ogc-client/pull/114   | jahow's review comments, approval rationale, composition-over-inheritance guidance, merge decision                     |
| PR #136 (CSAPI) | https://github.com/camptocamp/ogc-client/pull/136   | jahow's two requirements: (1) CSAPI must not be in root `index.ts`, (2) nothing outside `csapi/` should import from it |
| Issue #118      | https://github.com/camptocamp/ogc-client/issues/118 | jahow's original guidance pointing to PR #114 as the integration model                                                 |

### Prior Findings Used

| Finding | Path | What Was Consumed                    |
| ------- | ---- | ------------------------------------ |
| None    | —    | Plan 02 has no upstream dependencies |

### Sources Not Available or Not Useful

- **PR #114 inline code review comments:** Many file-level comments were marked "Outdated / Show resolved" and could not be expanded without GitHub authentication. The conversation-level comments provided sufficient context for all questions. → Alternative: used the visible conversation comments, which contained all architectural guidance.

---

## Executive Summary

This report documents the complete integration touchpoints of both EDR and CSAPI with ogc-client's core files (`endpoint.ts`, `info.ts`, `model.ts`, `index.ts`) and performs a side-by-side analysis of why the EDR integration pattern is acceptable at EDR's scale but fails at CSAPI's scale.

**The core finding is that EDR and CSAPI follow the exact same integration pattern** — a URL builder class in a sub-folder, a factory method on `OgcApiEndpoint`, a conformance check in `info.ts`, and collection detection in `parseCollections()`. The pattern itself is not the problem. The problem is that CSAPI is **18× larger than EDR** (11,767 vs 656 non-spec lines), exports **183 lines of types and functions into the root `index.ts`** (EDR exports zero), and introduces **2 imports from `csapi/` into `endpoint.ts`** where EDR only introduces 1. At CSAPI's scale, the same pattern that works for EDR causes two concrete problems: bundle pollution (anyone importing ogc-client gets ~12K lines of CSAPI code whether they use it or not) and reverse dependency (core files importing from the CSAPI module).

jahow's feedback on PR #136 was precise: _"anything part of `src/ogc-api/csapi` should not be included in the root `index.ts` file"_ and _"anything not part of `src/ogc-api/csapi` should not import things from the CSAPI code at all."_ These two statements define the exact changes required.

Critically, `hasConnectedSystems`, `csapiCollections`, and `checkHasConnectedSystems()` in `info.ts` do **not** import from `csapi/` — they use only conformance URI strings and link relation regex. They follow the identical pattern as their EDR equivalents and may be safe to keep. The only files that actually import from `csapi/` are `endpoint.ts` (2 imports) and `index.ts` (~183 lines of exports).

### Key Metrics

| Metric                                     | EDR | CSAPI          | Ratio |
| ------------------------------------------ | --- | -------------- | ----- |
| Non-spec source lines                      | 656 | 11,767         | 18×   |
| Non-spec source files                      | 3   | 27             | 9×    |
| Sub-directories                            | 0   | 4              | ∞     |
| Imports into `endpoint.ts`                 | 1   | 2              | 2×    |
| New methods/properties on `OgcApiEndpoint` | 3   | 4 (+1 private) | 1.7×  |
| Root exports in `index.ts` (lines)         | 0   | 183            | ∞     |
| Types in shared `model.ts` (lines)         | ~45 | 0              | —     |
| Constructor params                         | 1   | 2              | 2×    |
| Test lines in `endpoint.spec.ts`           | 293 | 64             | 0.2×  |

### Overall Assessment

The EDR integration is acceptable because it is small, self-contained, and invisible to the public API. The CSAPI integration fails because it is large, pollutes the root exports, and creates reverse dependencies from core into the module. The fix requires exactly two changes: (1) move CSAPI exports to a separate entry point, and (2) remove the 2 CSAPI imports from `endpoint.ts`.

---

## Table of Contents

1. [EDR Integration Inventory](#1-edr-integration-inventory)
2. [CSAPI Integration Inventory](#2-csapi-integration-inventory)
3. [Scale and Structural Comparison](#3-scale-and-structural-comparison)
4. [Info.ts and Model.ts Integration Analysis](#4-infots-and-modelts-integration-analysis)
5. [Architectural Boundary Analysis](#5-architectural-boundary-analysis)
6. [Boundary Condition Verification](#6-boundary-condition-verification)
7. [Implementation Scope Gate Assessment](#7-implementation-scope-gate-assessment)
8. [Impact on Dependent Plans](#8-impact-on-dependent-plans)
9. [Key Takeaways](#9-key-takeaways)
10. [Impact on Implementation](#10-impact-on-implementation)
11. [Open Questions](#11-open-questions)

---

## 1. EDR Integration Inventory

This section documents every point where EDR code touches files outside `src/ogc-api/edr/`.

### Question 1: What imports does `endpoint.ts` have from `src/ogc-api/edr/`?

**Answer:** Exactly one import statement.

**Evidence:** `endpoint.ts` line 51:

```typescript
import EDRQueryBuilder from './edr/url_builder.js';
```

No other file outside `src/ogc-api/edr/` imports from the EDR module. This is the single reverse dependency.

### Question 2: What properties and methods does `OgcApiEndpoint` expose for EDR?

**Answer:** Four touchpoints — 2 public getters, 1 public method, 1 private cache:

| Member                          | Type                                      | Line | Visibility |
| ------------------------------- | ----------------------------------------- | ---- | ---------- |
| `edrCollections`                | getter → `Promise<string[]>`              | 209  | public     |
| `hasEnvironmentalDataRetrieval` | getter → `Promise<boolean>`               | 307  | public     |
| `edr(collection_id)`            | async method → `Promise<EDRQueryBuilder>` | 342  | public     |
| `collection_id_to_edr_builder_` | `Map<string, EDRQueryBuilder>`            | 66   | private    |

### Question 3: How does the `edr()` method work internally?

**Answer:** The `edr()` method is simple — it checks the conformance flag, fetches collection info using the standard `getCollectionInfo()` helper, constructs the builder with a single parameter, and caches:

```typescript
public async edr(collection_id: string): Promise<EDRQueryBuilder> {
  if (!this.hasEnvironmentalDataRetrieval) {
    throw new EndpointError('Endpoint does not support EDR');
  }
  const cache = this.collection_id_to_edr_builder_;
  if (cache.has(collection_id)) {
    return cache.get(collection_id);
  }
  const collection = await this.getCollectionInfo(collection_id);
  const result = new EDRQueryBuilder(collection);
  cache.set(collection_id, result);
  return result;
}
```

Key characteristics:

- Uses `getCollectionInfo()` — the standard parsed collection info (same as features, records, tiles)
- Constructor takes **one** parameter: `OgcApiCollectionInfo`
- No private helpers needed beyond the existing `getCollectionInfo()`
- No additional data extraction from the root document

### Question 4: What imports does `info.ts` have from `src/ogc-api/edr/`?

**Answer:** Zero. `info.ts` does not import anything from the EDR module.

**Evidence:** `info.ts` imports only from:

- `./model.js` (shared OGC API types)
- `./link-utils.js` (shared link utilities)
- `../shared/errors.js`
- `../shared/mime-type.js`

`checkHasEnvironmentalDataRetrieval()` (line 96) checks conformance URI strings only:

```typescript
export function checkHasEnvironmentalDataRetrieval([conformanceClasses]: [
  ConformanceClass[]
]): boolean {
  return conformanceClasses.some(
    (conformanceClass) =>
      conformanceClass.indexOf('ogcapi-edr-1/1.0/conf/core') > -1
  );
}
```

### Question 5: How does `parseCollections()` in `info.ts` detect EDR collections?

**Answer:** It checks for the `data_queries` property on the collection object — a property defined on `OgcApiCollectionInfo` in the shared `model.ts`. No EDR module import needed.

**Evidence:** In `parseCollections()`, the `hasDataQueries` flag is set by checking:

```typescript
hasDataQueries: !!collection.data_queries;
```

The `data_queries` property and its type `DataQueryType` are defined in `src/ogc-api/model.ts` (lines 12–24), not in `edr/model.ts`. This means EDR detection is entirely self-contained within shared types.

### Question 6: What does `index.ts` export from the EDR module?

**Answer:** Nothing. Zero lines. Zero exports.

**Evidence:** A grep search for `edr` and `EDR` in `src/index.ts` returned zero matches. `EDRQueryBuilder`, `EdrParameterInfo`, `DataQueryType`, and all other EDR types are not part of the package's public API. Consumers who want EDR use `endpoint.edr(collectionId)` to get a builder — they never import EDR types directly.

### Question 7: Where do EDR types live?

**Answer:** EDR types are split between the shared `model.ts` and the EDR module's own `model.ts`:

| Type                                                              | Location                               | Lines |
| ----------------------------------------------------------------- | -------------------------------------- | ----- |
| `DataQueryTypes` (array of constants)                             | `src/ogc-api/model.ts` line 12         | 11    |
| `DataQueryType` (union type)                                      | `src/ogc-api/model.ts` line 24         | 1     |
| `EdrParameterInfo` (interface)                                    | `src/ogc-api/model.ts` lines 43–62     | 20    |
| `data_queries` property on `OgcApiCollectionInfo`                 | `src/ogc-api/model.ts` ~line 130       | 7     |
| `parameter_names` property on `OgcApiCollectionInfo`              | `src/ogc-api/model.ts` ~line 138       | 1     |
| **EDR-specific model types** (bbox params, corridor params, etc.) | `src/ogc-api/edr/model.ts` (110 lines) | 110   |

**~45 lines of EDR-specific types live in the shared `model.ts`**, absorbed directly into `OgcApiCollectionInfo`. This is architecturally significant — it means `info.ts` and `endpoint.ts` can detect and work with EDR data without importing from the EDR module.

### Question 8: How many tests exist in `endpoint.spec.ts` for EDR functionality?

**Answer:** 11 `it()` blocks across ~293 lines (lines 2543–2835).

**Test coverage:**

1. Returns endpoint info
2. Supports EDR (conformance detection)
3. Lists all EDR collections
4. Produces an EDR query builder with info and download URLs
5. Caches builder properly
6. Produces area queries with/without optional parameters
7. Produces location queries
8. Throws for invalid parameter names (7 query types tested)
9. Throws for invalid bbox on cube query
10. Throws for invalid CRS (7 query types tested)
11. Throws for invalid bbox (duplicate test)

### Sub-topic Synthesis

EDR's integration is minimal and clean:

- **1 import** into `endpoint.ts`
- **3 public members** added to `OgcApiEndpoint` (following the exact same pattern as features, records, tiles)
- **0 imports** into `info.ts` — detection uses shared types only
- **0 exports** from `index.ts` — EDR is invisible to the public API
- **~45 lines** of EDR types absorbed into the shared `model.ts`
- The `edr()` factory method uses the standard `getCollectionInfo()` path
- Total module size: 656 non-spec lines across 3 files with 0 sub-directories

---

## 2. CSAPI Integration Inventory

This section documents every point where CSAPI code touches files outside `src/ogc-api/csapi/`.

### Question 9: What imports does `endpoint.ts` have from `src/ogc-api/csapi/`?

**Answer:** Two import statements.

**Evidence:** `endpoint.ts` lines 52–53:

```typescript
import CSAPIQueryBuilder from './csapi/url_builder.js';
import { scanCsapiLinks } from './csapi/helpers.js';
```

The second import (`scanCsapiLinks`) is notably absent from the EDR pattern. It exists because the `csapi()` method needs to discover resource URLs from the root API document — a step EDR doesn't require.

### Question 10: What properties and methods does `OgcApiEndpoint` expose for CSAPI?

**Answer:** Five touchpoints — 2 public getters, 1 public method, 1 private cache, 1 private helper:

| Member                            | Type                                          | Line | Visibility  |
| --------------------------------- | --------------------------------------------- | ---- | ----------- |
| `csapiCollections`                | getter → `Promise<string[]>`                  | 234  | public      |
| `hasConnectedSystems`             | getter → `Promise<boolean>`                   | ~315 | public      |
| `csapi(collectionId)`             | async method → `Promise<CSAPIQueryBuilder>`   | ~370 | public      |
| `collection_id_to_csapi_builder_` | `Map<string, CSAPIQueryBuilder>`              | 68   | private     |
| `extractRootResourceUrls()`       | async method → `Promise<Map<string, string>>` | 431  | **private** |

The private helper `extractRootResourceUrls()` is CSAPI-specific — EDR has no equivalent. It exists because CSAPI servers may advertise resources at the API root level (e.g., `/api/systems`) rather than under collections.

### Question 11: How does the `csapi()` method work internally, and how does it differ from `edr()`?

**Answer:** The `csapi()` method is structurally parallel to `edr()` but more complex in three ways:

```typescript
public async csapi(collectionId: string): Promise<CSAPIQueryBuilder> {
  if (!(await this.hasConnectedSystems)) {
    throw new EndpointError('Endpoint does not support Connected Systems');
  }
  const cache = this.collection_id_to_csapi_builder_;
  if (cache.has(collectionId)) {
    return cache.get(collectionId);
  }
  const collectionDoc = await this.getCollectionDocument(collectionId);
  const resourceUrls = await this.extractRootResourceUrls();
  const result = new CSAPIQueryBuilder(
    collectionDoc as unknown as OgcApiCollectionInfo,
    resourceUrls
  );
  cache.set(collectionId, result);
  return result;
}
```

**Three differences from `edr()`:**

1. **Uses `getCollectionDocument()` instead of `getCollectionInfo()`** — because `parseBaseCollectionInfo()` strips the `links` array, and CSAPIQueryBuilder needs `ogc-cs:*` link relations to discover resources.
2. **Calls `extractRootResourceUrls()`** — an additional data extraction step from the root document, using `scanCsapiLinks()` (imported from `csapi/helpers.js`). This is the source of the second CSAPI import.
3. **Constructor takes 2 parameters** — `OgcApiCollectionInfo` + `Map<string, string>` for resource URLs.

### Question 12: What imports does `info.ts` have from `src/ogc-api/csapi/`?

**Answer:** Zero. `info.ts` does not import anything from the CSAPI module.

**Evidence:** Same import list as documented in Question 4. `checkHasConnectedSystems()` (line 112) checks conformance URI strings only:

```typescript
export function checkHasConnectedSystems([conformanceClasses]: [
  ConformanceClass[]
]): boolean {
  return conformanceClasses.some(
    (cc) =>
      cc.indexOf('ogcapi-connectedsystems-1') > -1 ||
      cc.indexOf('ogcapi-connectedsystems-2') > -1
  );
}
```

### Question 13: How does `parseCollections()` in `info.ts` detect CSAPI collections?

**Answer:** It checks link relations using a regex pattern `/^ogc-cs:.+$/` against the collection's `links` array. No CSAPI module import is needed.

**Evidence:** In `parseCollections()`, the `hasConnectedSystems` flag is set by:

```typescript
hasConnectedSystems: collection.links?.some((link: { rel?: string }) =>
  /^ogc-cs:.+$/.test(link.rel ?? '')
);
```

This uses the `links` property that is already on the raw collection document (a core OGC API type). The regex `ogc-cs:` is a string constant, not imported from CSAPI. This is architecturally identical to how EDR detection checks `collection.data_queries` — both use data already present in the shared types.

### Question 14: What does `index.ts` export from the CSAPI module?

**Answer:** ~183 lines of exports (lines 45–227 of `index.ts`), categorized as:

**(a) Value exports (4 items):**

- `CSAPIQueryBuilder` (default from `csapi/url_builder.js`)
- `CSAPIResourceTypes`, `CommandStatusCodes`, `SystemTypeUris` (from `csapi/model.js`)

**(b) Function exports (~27 items from `csapi/formats/index.js`):**

- `SOSA_NS`, `SSN_NS`, `SENSORML_NS` (namespace constants)
- `isCSAPIFeature`, `getCSAPIResourceType`, `parseValidTime`, `isValidUri`, `extractCSAPIFeature`
- `parseSensorML30`, `parseSWEComponent`, `parseVector`, `parseMatrix`, `parseDataChoice`, `parseGeometry`
- `detectEncoding`, `validateAgainstSchema`
- `CSAPI_CONTENT_TYPES`, `getContentTypeForResource`
- `parseProperty`, `parseDatastream`, `parseObservation`, `parseControlStream`, `parseCommand`, `parseCommandStatus`
- `normalizeStatusCode`, `parseDatastreamSchemaResponse`, `parseControlStreamSchemaResponse`

**(c) Type exports (~110+ types):**

- From `csapi/model.js`: 42 types (resource types, query options, resource interfaces, collection types, schema response types)
- From `csapi/formats/index.js` — `CSAPIResourceTypeName`: 1 type
- From `csapi/formats/index.js` — SensorML types: ~40 types (process types, component types, constraints, etc.)
- From `csapi/formats/index.js` — SWE Common types: ~35 types (data components, encodings, constraints, etc.)

**Total: ~4 value exports + ~27 function exports + ~110 type exports = ~141 named exports across 183 lines.**

### Question 15: Where do CSAPI types live?

**Answer:** All CSAPI types live in CSAPI module files. Zero CSAPI-specific types exist in the shared `model.ts`.

| Location                           | Lines   | Content                                                                         |
| ---------------------------------- | ------- | ------------------------------------------------------------------------------- |
| `csapi/model.ts`                   | 730     | All 9 resource type interfaces, query option types, collection types, constants |
| `csapi/formats/index.ts`           | 298     | Re-exports from sub-modules, format pipeline types                              |
| `csapi/formats/sensorml/types.ts`  | 863     | SensorML process model types                                                    |
| `csapi/formats/swecommon/types.ts` | 669     | SWE Common data model types                                                     |
| Other `csapi/formats/*.ts`         | various | Format-specific types                                                           |

This is the architectural opposite of EDR, which absorbs ~45 lines of types into the shared `model.ts`. CSAPI's types are fully encapsulated in its own module — which is actually the correct architectural choice for its size, but creates the problem of needing to re-export them all through `index.ts`.

### Question 16: How many tests exist in `endpoint.spec.ts` for CSAPI functionality?

**Answer:** 6 `it()` blocks across ~64 lines (lines 2836–2900).

**Test coverage:**

Nominal case (using `http://local/csapi/sample-data-hub`):

1. Detects Connected Systems support
2. Lists all CSAPI collections
3. Produces a CSAPI query builder (checks `availableResources`)
4. Caches the CSAPI query builder

Non-CSAPI endpoint (using `http://local/sample-data/`): 5. Reports no Connected Systems support 6. Throws an error when calling `csapi()`

**Note:** This is significantly fewer tests than EDR's 11 blocks (~293 lines), but CSAPI's URL builder has its own extensive test suite (`csapi/url_builder.spec.ts`, 2,862 lines). The endpoint integration tests only verify the discovery and factory pattern, not query building.

### Sub-topic Synthesis

CSAPI follows the same structural pattern as EDR but with greater complexity at every touchpoint:

- **2 imports** into `endpoint.ts` (vs EDR's 1) — the extra import (`scanCsapiLinks`) is needed for root resource URL discovery
- **4 public members + 1 private helper** added to `OgcApiEndpoint` (vs EDR's 3 public + 0 private)
- **0 imports** into `info.ts` — detection uses conformance URIs and link regex only (same as EDR)
- **183 lines of exports** from `index.ts` (vs EDR's 0) — this is the primary problem
- **0 types** in shared `model.ts` (vs EDR's ~45 lines) — CSAPI types are self-contained
- The `csapi()` factory method requires `getCollectionDocument()` + `extractRootResourceUrls()` instead of the simpler `getCollectionInfo()`
- Total module size: 11,767 non-spec lines across 27 files with 4 sub-directories

---

## 3. Scale and Structural Comparison

### Question 17: What is the total source line count and file count?

**Answer:**

| Dimension                 | EDR | CSAPI  | Ratio   |
| ------------------------- | --- | ------ | ------- |
| Non-spec source lines     | 656 | 11,767 | **18×** |
| Non-spec source files     | 3   | 27     | **9×**  |
| Total lines (incl. specs) | 721 | 26,042 | **36×** |
| Total files (incl. specs) | 5   | 57     | **11×** |

**EDR file breakdown (non-spec):**

- `url_builder.ts` — 529 lines
- `model.ts` — 110 lines
- `helpers.ts` — 17 lines

**CSAPI file breakdown (non-spec, 27 files across 4 sub-directories):**

- Root: `url_builder.ts` (2,307), `model.ts` (730), `helpers.ts` (200), `command-routing.ts` (144) — subtotal 3,381
- `formats/`: 8 files — subtotal 2,009
- `formats/sensorml/`: 8 files — subtotal 2,690
- `formats/swecommon/`: 7 files — subtotal 3,687

### Question 18: How many type exports does each contribute to the public API?

**Answer:**

| Dimension                                 | EDR                            | CSAPI |
| ----------------------------------------- | ------------------------------ | ----- |
| Types exported from `index.ts`            | 0                              | ~110  |
| Values/functions exported from `index.ts` | 0                              | ~31   |
| Types in shared `model.ts`                | ~45 lines (4 type definitions) | 0     |

EDR types live in the shared `model.ts` and are exported via `export * from './ogc-api/model.js'` — they ride along with all other OGC API types. They are not separately identifiable as "EDR exports."

CSAPI types are explicitly enumerated in `index.ts` across 183 lines of dedicated export statements.

### Question 19: How many import statements does each add to `endpoint.ts`?

**Answer:** EDR: 1. CSAPI: 2.

The single EDR import is structural (the builder class). The two CSAPI imports are the builder class plus a helper function (`scanCsapiLinks`), which is needed because `extractRootResourceUrls()` delegates link scanning to CSAPI-specific logic.

### Question 20: How many new methods/properties does each add to `OgcApiEndpoint`?

**Answer:** EDR: 3 public. CSAPI: 4 public + 1 private.

| Member                    | EDR                             | CSAPI                             |
| ------------------------- | ------------------------------- | --------------------------------- |
| `has*` conformance getter | `hasEnvironmentalDataRetrieval` | `hasConnectedSystems`             |
| `*Collections` getter     | `edrCollections`                | `csapiCollections`                |
| Factory method            | `edr()`                         | `csapi()`                         |
| Private helper            | —                               | `extractRootResourceUrls()`       |
| Cache map                 | `collection_id_to_edr_builder_` | `collection_id_to_csapi_builder_` |

### Question 21: Does EDR add any private helper methods? Does CSAPI?

**Answer:** EDR: No. CSAPI: Yes — `extractRootResourceUrls()` (line 431).

This private method reads the root API document's links and calls `scanCsapiLinks()`:

```typescript
private async extractRootResourceUrls(): Promise<Map<string, string>> {
  const rootDoc = await this.root;
  const links = rootDoc?.links;
  if (!Array.isArray(links)) return new Map();
  return scanCsapiLinks(links);
}
```

This is the **only reason** `endpoint.ts` imports `scanCsapiLinks` from `csapi/helpers.js`. If this method were moved to the CSAPI module, the second import would be eliminated.

### Question 22: What is the constructor signature complexity?

**Answer:**

| Builder             | Parameters                                                                                                  | Complexity                                             |
| ------------------- | ----------------------------------------------------------------------------------------------------------- | ------------------------------------------------------ |
| `EDRQueryBuilder`   | `collection: OgcApiCollectionInfo`                                                                          | 1 param, shared type only                              |
| `CSAPIQueryBuilder` | `collection_: Pick<OgcApiCollectionInfo, 'id' \| 'title' \| 'links'>`, `resourceUrls?: Map<string, string>` | 2 params, includes resource URL map from root document |

The CSAPIQueryBuilder's second parameter (`resourceUrls`) is what drives the need for `extractRootResourceUrls()` in `endpoint.ts`, which in turn drives the need for `scanCsapiLinks` import.

### Question 23: How many sub-directories does each module have?

**Answer:** EDR: 0. CSAPI: 4.

CSAPI sub-directories:

- `formats/` — format pipeline, GeoJSON, classification, constants, property, response, schema-response, Part 2
- `formats/sensorml/` — SensorML process parsers (physical system, aggregate, simple process)
- `formats/swecommon/` — SWE Common data model parsers (components, data arrays, records)
- `integration/` — end-to-end integration tests (5 spec files)

### Sub-topic Synthesis

The quantitative comparison reveals that the EDR pattern scaled from 656 lines to 11,767 lines — an 18× increase — without any change to the integration architecture. The integration touchpoints only increased modestly (1→2 imports, 3→4 public members, 0→1 private helpers), but the **public API surface** exploded from 0 exports to 183 lines of exports in `index.ts`. The scale difference is most dramatic in:

1. **Root export pollution**: 0 → 183 lines (the primary problem jahow identified)
2. **Module complexity**: 0 sub-directories → 4 sub-directories with format parsers
3. **Code volume**: 656 → 11,767 non-spec lines (18× larger than EDR, or roughly equal to the entire rest of the ogc-client library)

---

## 4. Info.ts and Model.ts Integration Analysis

### Question 24: Does `checkHasConnectedSystems()` import from `csapi/`?

**Answer:** No. It purely checks conformance URI strings. Zero CSAPI module imports.

**Evidence:** The function (info.ts line 112) takes a conformance class string array and checks for substring matches against `'ogcapi-connectedsystems-1'` and `'ogcapi-connectedsystems-2'`. These are literal strings, not imported constants.

### Question 25: Does `checkHasEnvironmentalDataRetrieval()` import from `edr/`?

**Answer:** No. It purely checks conformance URI strings. Zero EDR module imports.

**Evidence:** The function (info.ts line 96) checks for `'ogcapi-edr-1/1.0/conf/core'`. Same pattern as CSAPI.

### Question 26: Does `parseCollections()` import from `csapi/`?

**Answer:** No. It uses a regex pattern `/^ogc-cs:.+$/` against the `link.rel` property from core link types. Zero CSAPI module imports.

### Question 27: Does `parseCollections()` import from `edr/`?

**Answer:** No. It checks `collection.data_queries` from `OgcApiCollectionInfo`. Zero EDR module imports.

### Question 28: Are there EDR-specific types in `ogc-api/model.ts`?

**Answer:** Yes, approximately 45 lines:

| Type                                         | Lines | Purpose                                           |
| -------------------------------------------- | ----- | ------------------------------------------------- |
| `DataQueryTypes` (const array)               | 12–22 | Enumeration of EDR query type strings             |
| `DataQueryType` (type)                       | 24    | Union type derived from `DataQueryTypes`          |
| `EdrParameterInfo` (interface)               | 43–62 | Structure defining an EDR parameter               |
| `data_queries?` on `OgcApiCollectionInfo`    | ~130  | Optional property mapping query types to links    |
| `parameter_names?` on `OgcApiCollectionInfo` | ~138  | Optional property mapping parameter names to info |

**Is this pattern acceptable?** Yes — and it is architecturally intentional. By placing EDR detection types in the shared model, `info.ts` can detect EDR collections without importing from the EDR module. This is what enables the clean separation: the shared `OgcApiCollectionInfo` type carries EDR metadata naturally because EDR data comes embedded in the standard OGC API collection response.

### Question 29: Are there CSAPI-specific types in `ogc-api/model.ts`?

**Answer:** Zero. All CSAPI types live in `csapi/model.ts` (730 lines) and `csapi/formats/` sub-modules.

**Why this differs from EDR:** EDR parameters and data queries are properties of the OGC API collection document itself (`data_queries` appears in the JSON response at `/collections/{id}`). CSAPI resources are accessed via separate link relations and endpoints — they are not properties of the collection document. Therefore, CSAPI types don't naturally belong on `OgcApiCollectionInfo`.

This is a meaningful architectural difference, not incidental. It reflects the different relationship each standard has with the OGC API collection concept.

### Sub-topic Synthesis

The critical finding is that `info.ts` has **zero imports from either `edr/` or `csapi/`**. Both detection mechanisms (conformance checks and collection parsing) operate entirely through shared types and string patterns. This means:

1. `hasConnectedSystems` and `csapiCollections` on `OgcApiEndpoint` could potentially remain even after decoupling, because they don't depend on CSAPI module code.
2. `hasEnvironmentalDataRetrieval` and `edrCollections` demonstrate the accepted precedent for this pattern.
3. The only true cross-boundary dependencies are in `endpoint.ts` (the 2 CSAPI imports) and `index.ts` (the 183 lines of exports).

EDR types being in the shared `model.ts` is architecturally appropriate because EDR data is embedded in collection responses. CSAPI types being in their own module is also architecturally appropriate because CSAPI data is accessed through separate link-relation-driven endpoints.

---

## 5. Architectural Boundary Analysis

### Question 30: What exactly makes the EDR integration acceptable to the maintainer?

**Answer:** Based on PR #114 and the code analysis, the acceptance is driven by a combination of factors:

**(a) Small code size (~650 lines, 3 files):** jahow said EDR "could bring too much complexity" initially but accepted it after the composition refactor. The final merged code was contained.

**(b) Zero root export pollution:** EDR does not appear in `index.ts`. No consumer gets EDR code unless they explicitly use `endpoint.edr()`. Tree-shaking can eliminate the builder entirely for non-EDR users.

**(c) EDR types absorbed into shared model:** `data_queries` and `EdrParameterInfo` are properties of the standard collection response, so they belong on `OgcApiCollectionInfo`. This avoids the need for separate exports.

**(d) EDR is a conformance class of OGC API:** jahow explicitly noted: "EDR is also 'just' another conformance class from OGC API right? The `OgcApiEndpoint` class already handles several conformance classes: features, records, tiles, maps, styles etc." This framing positions EDR as a natural extension of the endpoint class, not a separate module.

**(e) Minimal integration footprint:** 1 import, 3 public members, 0 private helpers. The endpoint class barely notices EDR's presence.

### Question 31: At what point would EDR need the same treatment as CSAPI?

**Answer:** If EDR grew to have:

- Its own type system (currently ~45 lines in shared model → would need hundreds of lines in own module)
- Format parsers (SensorML equivalent, SWE Common equivalent)
- Sub-directories with deep hierarchies
- Dozens of exports needed in the public API
- Multiple imports into `endpoint.ts`

The threshold is not a single number but a composite:

- When the module has **its own public API** that consumers need to import directly (not just via the endpoint class)
- When the module **requires its own entry point** because tree-shaking can't eliminate it from bundles of non-EDR consumers
- When the integration footprint grows beyond "a few lines of glue code" into "dedicated helper methods and additional data extraction"

### Question 32: Is the core issue `index.ts` (public API pollution), `endpoint.ts` (implementation coupling), or both?

**Answer:** **Both, but `index.ts` is primary.** jahow's exact words:

> _"I would request one major thing: that all things related to the CS API not be part of the main `index.ts` file, but instead imported through `@camptocamp/ogc-client/csapi`."_

> _"Basically I want to make sure that anyone using the library as before do not end up with all this code in their bundle overnight."_

The bundle size concern is the primary driver — and that's `index.ts`. But then he added:

> _"This means that: anything part of the `src/ogc-api/csapi` should not be included in the root `index.ts` file."_

> _"anything not part of the `src/ogc-api/csapi` should not import things from the CSAPI code at all"_

The second bullet — "should not import things from the CSAPI code at all" — is the `endpoint.ts` constraint. It requires removing the 2 CSAPI imports from `endpoint.ts`.

jahow also said: _"(unless we find a better way to handle tree-shaking)"_ — leaving open the possibility that if tree-shaking could solve the bundle problem, the import constraint might be relaxed.

### Question 33: Did jahow say anything about `endpoint.ts` integration specifically?

**Answer:** jahow's feedback on PR #136 focused on the export/import boundary, not on specific properties:

1. He said _"anything not part of the `src/ogc-api/csapi` should not import things from the CSAPI code at all"_ — this covers `endpoint.ts`'s 2 imports
2. He said _"I'm going to review the changes to the existing code and give you a more thorough feedback"_ — suggesting he plans further review of the endpoint integration
3. He did NOT specifically mention `hasConnectedSystems`, `csapiCollections`, or the `csapi()` method by name
4. He did NOT say whether conformance-only checks (which don't import from CSAPI) are acceptable

The constraint is stated in terms of import direction, not in terms of specific properties or methods. This leaves room for properties that don't import from CSAPI.

### Question 34: Can `hasConnectedSystems` and `csapiCollections` remain on `OgcApiEndpoint`?

**Answer:** **Likely yes**, because they do not import from `csapi/`.

**Technical analysis:**

| Property                        | Imports from `csapi/`? | Uses `info.ts` function?                     | Pattern matches EDR?                         |
| ------------------------------- | ---------------------- | -------------------------------------------- | -------------------------------------------- |
| `hasConnectedSystems`           | No                     | Yes — `checkHasConnectedSystems()`           | Identical to `hasEnvironmentalDataRetrieval` |
| `csapiCollections`              | No                     | Yes — `parseCollections()`                   | Identical to `edrCollections`                |
| `hasEnvironmentalDataRetrieval` | No                     | Yes — `checkHasEnvironmentalDataRetrieval()` | — (reference)                                |
| `edrCollections`                | No                     | Yes — `parseCollections()`                   | — (reference)                                |

Both CSAPI properties follow the exact same implementation pattern as their EDR equivalents. They use `info.ts` functions that check conformance URIs and link relations — never importing from the CSAPI module.

However, jahow's intent may go further than the technical constraint. He may prefer that even the presence of CSAPI-named properties on `OgcApiEndpoint` is unacceptable, regardless of import direction. This cannot be determined from his current feedback and should be clarified.

### Question 35: Can the `csapi()` method stay on `OgcApiEndpoint`?

**Answer:** **Not in its current form.** The `csapi()` method creates `new CSAPIQueryBuilder(...)` and calls `scanCsapiLinks()` — both imported from `csapi/`. This directly violates jahow's constraint: _"anything not part of the `src/ogc-api/csapi` should not import things from the CSAPI code at all."_

**Options for Plan 06:**

1. **Move `csapi()` to the CSAPI module entirely** — consumers would import a factory function from `@camptocamp/ogc-client/csapi` instead of calling `endpoint.csapi()`
2. **Keep `csapi()` on the endpoint but use dependency injection** — the CSAPI module registers a factory at import time, and `endpoint.csapi()` delegates to it without importing CSAPI code directly
3. **Use a plugin/extension pattern** — the CSAPI module extends `OgcApiEndpoint` at runtime

Each option has trade-offs that Plan 06 must evaluate.

### Sub-topic Synthesis

The architectural boundary analysis reveals that:

1. **The EDR pattern is acceptable because EDR is small and invisible.** It adds minimal code to the endpoint class, zero exports to the public API, and its types naturally belong on shared model types.
2. **The CSAPI pattern fails because CSAPI is large and visible.** 183 lines of root exports, 2 reverse imports, and a private helper method that delegates to CSAPI-specific logic.
3. **The boundary line has at least three dimensions:** public API surface (exports in `index.ts`), import direction (core → module), and module self-containment (own type system, sub-directories, format parsers).
4. **`hasConnectedSystems` and `csapiCollections` are in a gray zone** — they don't violate the import constraint but jahow may still want them removed. This is the primary open question.
5. **The `csapi()` method clearly violates the constraint** and must either move or be restructured.

---

## 6. Boundary Condition Verification

### Constraint Compliance Matrix

| #   | Constraint                              | Status               | Evidence                                                       | Notes                                                             |
| --- | --------------------------------------- | -------------------- | -------------------------------------------------------------- | ----------------------------------------------------------------- |
| 1   | No CSAPI in root exports (Constraint 1) | ✗ Currently Violated | `index.ts` lines 45–227: 183 lines of CSAPI exports            | EDR has zero root exports — this asymmetry is the primary problem |
| 3   | No outward imports (Constraint 3)       | ✗ Currently Violated | `endpoint.ts` lines 52–53: 2 imports from `csapi/`             | EDR has 1 import (same pattern, tolerated at small scale)         |
| 4   | One-way dependency (Constraint 4)       | ✗ Currently Violated | `endpoint.ts` (core) imports from `csapi/` (reverse direction) | `info.ts` does NOT violate this — zero CSAPI imports              |

### Scope Boundary Adherence

- **In scope — explored:** Complete touchpoint inventories for both EDR and CSAPI across all four core files; quantitative comparison; jahow's exact feedback from PRs and issues; architectural boundary analysis
- **Out of scope — respected:** Did not design the replacement architecture (Plan 06); did not analyze build system mechanics (Plan 01); did not research external industry patterns (Plans 04, 05); did not propose solutions for `hasConnectedSystems` placement (deferred to Plan 06)
- **Scope adjustments:** PR #114 inline code review comments were partially inaccessible (resolved/outdated). The conversation-level comments provided sufficient context.

---

## 7. Implementation Scope Gate Assessment

### Minimum-Change Test

| Finding / Recommendation                                      | Serves jahow's requirements?                                            | Minimum-change? | Include in implementation?          |
| ------------------------------------------------------------- | ----------------------------------------------------------------------- | --------------- | ----------------------------------- |
| Remove CSAPI exports from `index.ts`                          | Yes — directly required by jahow                                        | Yes             | ✓ Include                           |
| Create separate entry point `@camptocamp/ogc-client/csapi`    | Yes — directly required by jahow                                        | Yes             | ✓ Include                           |
| Remove 2 CSAPI imports from `endpoint.ts`                     | Yes — directly required: "should not import things from the CSAPI code" | Yes             | ✓ Include                           |
| Remove `extractRootResourceUrls()` from `endpoint.ts`         | Yes — necessary consequence of removing CSAPI imports                   | Yes             | ✓ Include                           |
| Restructure `csapi()` method                                  | Yes — necessary consequence of removing CSAPI imports                   | Yes             | ✓ Include                           |
| Keep `hasConnectedSystems` and `csapiCollections` on endpoint | Yes — they serve discovery without CSAPI imports                        | Yes             | ⚠️ Discuss — jahow's intent unclear |
| Move EDR types out of shared `model.ts`                       | No — not requested, EDR is accepted                                     | No              | ✗ Defer                             |
| Standardize EDR to also have separate entry point             | No — not requested, EDR is accepted                                     | No              | ✗ Defer                             |

### Deferred Insights

- **EDR types in shared `model.ts` may warrant future cleanup:** ~45 lines of EDR-specific types live in the shared model, which works at EDR's scale but could become a pattern problem if more OGC API conformance classes are added. Deferred because jahow did not request this change and it adds risk.
- **EDR's 1 import into `endpoint.ts` follows the same anti-pattern as CSAPI's 2 imports:** It violates the same "no outward imports" principle but is tolerated at small scale. If consistency is ever prioritized, EDR would need the same treatment. Deferred because jahow explicitly accepted this for EDR.

---

## 8. Impact on Dependent Plans

### What Downstream Plans Should Consume

| Downstream Plan                            | What to consume from this report                                                                                                                                                                                                                                            | Section reference           |
| ------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------- |
| Plan 06 (Endpoint Decoupling Architecture) | Complete touchpoint inventories (§ 1, § 2); scale comparison table (§ 3); the three boundary dimensions (§ 5); the specific constraint violations (§ 6); the three options for restructuring `csapi()` (Q35); the open question about `hasConnectedSystems` placement (Q34) | §§ 1–5, Key Takeaways #1–10 |
| Plan 08 (File-Level Changelist)            | The exact files and line ranges that must change: `index.ts` lines 45–227, `endpoint.ts` lines 52–53 (imports) and lines 370–437 (`csapi()` + `extractRootResourceUrls()`); the files that are safe: `info.ts` (zero CSAPI imports)                                         | §§ 1–2, Key Takeaway #6     |

### Decisions Now Final

1. **`info.ts` has zero CSAPI (or EDR) imports and does not need modification** — `checkHasConnectedSystems()` and `parseCollections()` use only conformance URI strings and link relation regex. This is settled.
2. **`model.ts` has zero CSAPI types and does not need modification** — all CSAPI types are already in the CSAPI module.
3. **The CSAPI module is self-contained except for 2 imports in `endpoint.ts` and the `index.ts` exports** — no other core files import from CSAPI.

### Items Requiring Downstream Resolution

1. **Whether `hasConnectedSystems` and `csapiCollections` stay on `OgcApiEndpoint`** → Plan 06 should decide, potentially requiring jahow clarification
2. **The mechanism for restructuring the `csapi()` factory** → Plan 06 must choose between move-to-module, dependency injection, or plugin pattern
3. **How `extractRootResourceUrls()` is handled** → Plan 06 must decide where this logic moves (into CSAPIQueryBuilder constructor, into a CSAPI entry point factory, or elsewhere)

---

## 9. Key Takeaways

1. **EDR and CSAPI follow the identical integration pattern** — both have a builder class, a factory method on the endpoint, a conformance check in `info.ts`, and collection detection in `parseCollections()`. The pattern itself is sound; the scale is the problem.

2. **CSAPI is 18× larger than EDR** (11,767 vs 656 non-spec lines) — this is the fundamental reason the same pattern doesn't scale. CSAPI is not a "thin wrapper around a URL builder" — it is a full sub-system with format parsers, SensorML, SWE Common, command routing, and 4 sub-directories.

3. **The root export pollution is the primary problem** — 183 lines of CSAPI exports in `index.ts` (vs EDR's 0) means every consumer of ogc-client gets ~12K lines of CSAPI code in their bundle. jahow's number-one concern is bundle size.

4. **`endpoint.ts` has exactly 2 CSAPI imports that must be removed** — `CSAPIQueryBuilder` from `csapi/url_builder.js` and `scanCsapiLinks` from `csapi/helpers.js`. The second import exists solely to support `extractRootResourceUrls()`.

5. **`info.ts` is clean and needs no changes** — it has zero imports from either `edr/` or `csapi/`. All detection logic uses conformance URI strings and link relation patterns from shared types.

6. **`model.ts` is clean and needs no changes** — CSAPI types are already fully encapsulated in the CSAPI module's own files; EDR types in the shared model are architecturally appropriate.

7. **`hasConnectedSystems` and `csapiCollections` don't import from CSAPI** — they follow the exact same pattern as `hasEnvironmentalDataRetrieval` and `edrCollections`, using `info.ts` functions that only check conformance URIs and link relations. They may be safe to keep.

8. **The `csapi()` method must be restructured or moved** — it directly creates `new CSAPIQueryBuilder(...)` and calls `scanCsapiLinks()`, both imported from `csapi/`. This is the only method on `OgcApiEndpoint` that creates a direct dependency on CSAPI internals.

9. **jahow's requirements are precise: two bullet points** — (a) CSAPI not in root `index.ts`, import via `@camptocamp/ogc-client/csapi`; (b) nothing outside `csapi/` imports from CSAPI. These define the exact scope of changes.

10. **The boundary between "embed" and "separate" has three dimensions** — (a) public API footprint (exports in `index.ts`), (b) import direction (core → module), and (c) module self-containment (own type system, sub-directories, format parsers). EDR passes all three; CSAPI fails all three.

---

## 10. Impact on Implementation

### Must Change (Required by Findings)

1. **Remove all CSAPI exports from `src/index.ts`** (lines 45–227, ~183 lines) — jahow: _"anything part of `src/ogc-api/csapi` should not be included in the root `index.ts` file."_
2. **Create a separate CSAPI entry point** (e.g., `src/ogc-api/csapi/index.ts`) exportable as `@camptocamp/ogc-client/csapi` — jahow: _"imported through `@camptocamp/ogc-client/csapi`"_
3. **Remove 2 CSAPI imports from `endpoint.ts`** (lines 52–53) — jahow: _"anything not part of `src/ogc-api/csapi` should not import things from the CSAPI code at all"_
4. **Restructure or remove the `csapi()` method** from `OgcApiEndpoint` — it cannot exist in its current form without the CSAPI imports
5. **Remove `extractRootResourceUrls()`** from `endpoint.ts` — it is CSAPI-specific and depends on `scanCsapiLinks`

### Should Change (Recommended by Findings)

1. **Keep `hasConnectedSystems` and `csapiCollections` on `OgcApiEndpoint`** if jahow approves — they follow the accepted EDR pattern, don't import from CSAPI, and provide useful discovery capabilities. Recommend seeking clarification.

### Could Change (Optional Improvements)

1. **Move the `csapi()` factory into the CSAPI module** as a standalone function that accepts an `OgcApiEndpoint` instance — cleanest separation, but changes the consumer API from `endpoint.csapi(id)` to `createCsapiBuilder(endpoint, id)`
2. **Use lazy registration pattern** — CSAPI module registers a factory at import time so `endpoint.csapi()` can still work without a direct import — preserves the consumer API but adds runtime coupling

---

## 11. Open Questions

| #   | Question                                                                                                                            | Why Unresolved                                                                                                                                           | Resolution Path                                                      |
| --- | ----------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------- |
| 1   | Can `hasConnectedSystems` and `csapiCollections` stay on `OgcApiEndpoint`?                                                          | jahow's feedback constrains imports, not properties. His intent regarding conformance-only properties is ambiguous.                                      | Plan 06 should decide; may need jahow clarification                  |
| 2   | Which restructuring pattern should `csapi()` use — move to module, dependency injection, or plugin?                                 | Multiple valid approaches exist; choice affects consumer API, bundle behavior, and implementation complexity.                                            | Plan 06 must evaluate trade-offs against all boundary conditions     |
| 3   | Should `extractRootResourceUrls()` logic move into `CSAPIQueryBuilder` constructor or into the CSAPI entry point factory?           | Both are valid; depends on the chosen factory pattern.                                                                                                   | Plan 06 decides as part of the `csapi()` restructuring               |
| 4   | Does jahow's parenthetical "(unless we find a better way to handle tree-shaking)" open a path that avoids the separate entry point? | Tree-shaking of `index.ts` was not investigated in this plan (build system analysis is Plan 01's territory).                                             | Plan 06 should consider Plan 01 findings on tree-shaking             |
| 5   | Would jahow also want `allCollections` modified to exclude `hasConnectedSystems` from its return type?                              | `allCollections` getter returns objects with `hasConnectedSystems?: boolean` — this is set by `parseCollections()` in `info.ts` with zero CSAPI imports. | Likely safe (same as EDR's `hasDataQueries`) but should be confirmed |

---

## Evidence Appendix

### A. Complete Import Comparison

**`endpoint.ts` EDR imports (1 line):**

```typescript
import EDRQueryBuilder from './edr/url_builder.js'; // line 51
```

**`endpoint.ts` CSAPI imports (2 lines):**

```typescript
import CSAPIQueryBuilder from './csapi/url_builder.js'; // line 52
import { scanCsapiLinks } from './csapi/helpers.js'; // line 53
```

**`info.ts` EDR and CSAPI imports: ZERO from either module.**

### B. CSAPI Module File Inventory (27 non-spec files)

```
csapi/
├── command-routing.ts      144 lines
├── helpers.ts              200 lines
├── model.ts                730 lines
├── url_builder.ts        2,307 lines
├── formats/
│   ├── classification.ts   118 lines
│   ├── constants.ts        292 lines
│   ├── geojson.ts          467 lines
│   ├── index.ts            298 lines
│   ├── part2.ts            497 lines
│   ├── property.ts          57 lines
│   ├── response.ts         115 lines
│   ├── schema-response.ts  165 lines
│   ├── sensorml/
│   │   ├── _helpers.ts     258 lines
│   │   ├── aggregate-process.ts  240 lines
│   │   ├── errors.ts        40 lines
│   │   ├── index.ts        122 lines
│   │   ├── parser.ts       410 lines
│   │   ├── physical-system.ts    622 lines
│   │   ├── simple-process.ts     135 lines
│   │   └── types.ts        863 lines
│   └── swecommon/
│       ├── _helpers.ts      78 lines
│       ├── components.ts   747 lines
│       ├── data-array.ts   526 lines
│       ├── data-record.ts  225 lines
│       ├── index.ts        135 lines
│       ├── parser.ts     1,307 lines
│       └── types.ts        669 lines
                          ─────────
Total:                   11,767 lines
```

### C. EDR Module File Inventory (3 non-spec files)

```
edr/
├── helpers.ts     17 lines
├── model.ts      110 lines
└── url_builder.ts 529 lines
                  ────────
Total:            656 lines
```

### D. jahow's Exact Quotes from PR #136

> **Quote 1 (primary requirement):** "I would request one major thing: that all things related to the CS API not be part of the main `index.ts` file, but instead imported through `@camptocamp/ogc-client/csapi`."

> **Quote 2 (bundle motivation):** "Basically I want to make sure that anyone using the library as before do not end up with all this code in their bundle overnight."

> **Quote 3 (export constraint):** "anything part of the `src/ogc-api/csapi` should not be included in the root `index.ts` file."

> **Quote 4 (import constraint):** "anything not part of the `src/ogc-api/csapi` should not import things from the CSAPI code at all"

> **Quote 5 (tree-shaking caveat):** "(unless we find a better way to handle tree-shaking)."

> **Quote 6 (further review):** "I'm going to review the changes to the existing code and give you a more thorough feedback."

### E. jahow's Key Quotes from PR #114

> **Quote A (pattern approval):** "Very interesting, thank you! I was expecting the EDR support to be done in the existing `OgcApiEndpoint` class, but it seems like it could bring too much complexity to that class."

> **Quote B (folder structure):** "I would put it in an `edr` folder inside `ogc-api` though, and leave all the common stuff inside `ogc-api`"

> **Quote C (conformance class framing):** "EDR is also 'just' another conformance class from OGC API right? The `OgcApiEndpoint` class already handles several conformance classes: features, records, tiles, maps, styles etc."

> **Quote D (composition design):** "how about we define a new class called `OgcApiEdr` which looks something like this... So if the endpoint does not support EDR this property will be null. But if it does support it, then this object will be used for all kinds of data queries and let us avoid adding too much complexity to the endpoint class. At the end of the day this means we do composition over inheritance."

> **Quote E (final approval):** "Ok, this looks really good now. I'll merge this if you're done."

### F. jahow's Quote from Issue #118

> **Quote F (EDR as model):** "As an example you can take a look at [PR #114] implementing support for OGC API EDR (Environment Data Retrieval) by @C-Loftus."

---

## Research Completion Checklist

- [x] All 35 detailed questions from the research plan have specific, evidenced answers
- [x] Boundary condition verification completed (Section 6)
- [x] Implementation scope gate assessment completed (Section 7)
- [x] Impact on dependent plans documented (Section 8)
- [x] Key takeaways extracted (Section 9)
- [x] Open questions cataloged with resolution paths (Section 11)
- [x] Cross-references to prior findings are accurate (no prior findings for Plan 02)
- [x] Findings respect all boundary conditions from the research plan
- [x] Document is self-contained — a reader unfamiliar with the plan can understand the findings

**Research Started:** 2026-02-23
**Research Completed:** 2026-02-23
**Reviewed:** Not yet

---

## Notes

- The CSAPI test count in `endpoint.spec.ts` (6 tests, 64 lines) is deceptively small because the CSAPI URL builder has its own comprehensive test suite (`url_builder.spec.ts`, 2,862 lines) plus 5 integration test files in `integration/`. The endpoint tests only validate the discovery/factory integration, not query building.
- jahow's PR #136 review is very recent (posted "5 hours ago" at time of fetch). He indicated he plans to provide "more thorough feedback" after reviewing the code changes — meaning the two constraints documented here may be supplemented by additional requirements. Plan 06 should monitor for updates.
- The `export * from './ogc-api/model.js'` in `index.ts` (line 44) means `DataQueryType`, `EdrParameterInfo`, and all other EDR types in the shared model are implicitly exported. This is currently invisible because they're mixed in with all OGC API types, but it means EDR does technically contribute types to the root public API — just not through dedicated export statements.
