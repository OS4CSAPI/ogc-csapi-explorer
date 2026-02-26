# CSAPI Module — Comprehensive Code Audit (Phase 6)

**Branch:** `phase-6`  
**Date:** 2025  
**Scope:** All 28+ source files in `src/ogc-api/csapi/`, modified upstream files, package configuration

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Severity Legend](#2-severity-legend)
3. [Per-File Analysis](#3-per-file-analysis)
   - [3.1 Core Module](#31-core-module)
   - [3.2 Formats — Part 1 (GeoJSON)](#32-formats--part-1-geojson)
   - [3.3 Formats — Part 2 (JSON)](#33-formats--part-2-json)
   - [3.4 Formats — SensorML 3.0](#34-formats--sensorml-30)
   - [3.5 Formats — SWE Common 3.0](#35-formats--swe-common-30)
   - [3.6 Modified Upstream Files](#36-modified-upstream-files)
   - [3.7 Package Configuration](#37-package-configuration)
4. [Cross-Cutting Findings](#4-cross-cutting-findings)
5. [Findings by Severity](#5-findings-by-severity)
6. [Metrics Summary](#6-metrics-summary)
7. [Recommendations](#7-recommendations)

---

## 1. Executive Summary

The CSAPI module is a well-structured, densely documented TypeScript library implementing OGC API — Connected Systems Parts 1 & 2, SensorML 3.0, and SWE Common 3.0. The codebase exhibits strong engineering discipline: correct ESM import conventions, consistent `import type` usage, a clean three-tier dependency hierarchy, and exceptional JSDoc coverage.

Key findings:

| Severity      | Count |
| ------------- | ----- |
| BUG           | 1     |
| DESIGN        | 8     |
| GAP           | 2     |
| CONSISTENCY   | 4     |
| INFORMATIONAL | 5     |
| POSITIVE      | 12    |

No runtime-breaking bugs were found. The single BUG-level finding is a planned `as any` cast in `factory.ts` that is already tracked (Issue #122). Design-level findings center on code duplication and a structural circular import.

---

## 2. Severity Legend

| Level             | Meaning                                                               |
| ----------------- | --------------------------------------------------------------------- |
| **BUG**           | Incorrect behavior, type-safety hole, or runtime risk                 |
| **DESIGN**        | Architectural concern or code smell that increases maintenance burden |
| **GAP**           | Missing feature, incomplete implementation, or spec deviation         |
| **CONSISTENCY**   | Inconsistency in naming, patterns, or conventions                     |
| **INFORMATIONAL** | Observation or documentation note; no action needed                   |
| **POSITIVE**      | Exemplary practice worth preserving                                   |

---

## 3. Per-File Analysis

### 3.1 Core Module

#### `factory.ts` — 60 lines

| Aspect              | Assessment                                                                                                                                                                                |
| ------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Purpose**         | Creates `CSAPIQueryBuilder` instances from `OgcApiEndpoint` + `collectionId`                                                                                                              |
| **Imports**         | `import type OgcApiEndpoint` (correct), `import type { OgcApiCollectionInfo }` (correct), value imports from `shared/errors.js`, `url_builder.js`, `helpers.js` — all `.js` extensions ✅ |
| **Exports**         | `createCSAPIBuilder` (async function)                                                                                                                                                     |
| **JSDoc**           | Complete: `@param`, `@returns`, `@throws`, `@example`, `@see`                                                                                                                             |
| **Spec compliance** | N/A (factory pattern, no OGC normative behavior)                                                                                                                                          |

**Findings:**

- **[BUG] `as any` on line 46** — `const ep = endpoint as any;` bypasses TypeScript to access `private` members `.root` and `.getCollectionDocument()` on `OgcApiEndpoint`. The `as unknown as OgcApiCollectionInfo` double cast on line 57 compounds this. Both are documented with a comment referencing Issue #122 (Task 6) which will make these members public. **Risk:** If `OgcApiEndpoint`'s private API changes, this silently breaks with no compile-time error.
- **[POSITIVE]** Comment on lines 44–45 clearly explains the rationale and planned removal timeline.

---

#### `index.ts` — 209 lines

| Aspect              | Assessment                                                        |
| ------------------- | ----------------------------------------------------------------- |
| **Purpose**         | Barrel re-export file for `@camptocamp/ogc-client/csapi` sub-path |
| **Imports**         | All re-exports use `.js` extensions ✅                            |
| **Exports**         | ~170 named symbols (values + types), grouped by category          |
| **JSDoc**           | `@module` with usage example                                      |
| **Spec compliance** | N/A (re-export only)                                              |

**Findings:**

- **[POSITIVE]** Uses `export type` correctly for every type-only re-export.
- **[POSITIVE]** Logical grouping by resource tier (factory → builder → model → formats → SensorML → SWE Common).
- **[INFORMATIONAL]** At ~170 exports this is one of the larger barrel files; if tree-shaking issues arise, consider splitting.

---

#### `model.ts` — 788 lines

| Aspect              | Assessment                                                                                                                                            |
| ------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Purpose**         | All CSAPI TypeScript interfaces, types, and const value arrays                                                                                        |
| **Imports**         | `import type` from `../../shared/models.js`, `../model.js`, `geojson` — all correct ✅                                                                |
| **Exports**         | 9 resource interfaces, query option interfaces, collection types, schema response types, `CSAPIResourceTypes`, `CommandStatusCodes`, `SystemTypeUris` |
| **JSDoc**           | Thorough — `@see` links to spec table numbers throughout                                                                                              |
| **Spec compliance** | Closely tracks OGC 23-001 & 23-002 table definitions                                                                                                  |

**Findings:**

- **[DESIGN]** `SystemTypeUris` (line ~43) contains only full URI forms (`http://www.w3.org/ns/sosa/Sensor`, etc.). A **different** `SystemTypeUris` in `formats/constants.ts` has both CURIE (`sosa:Sensor`) and full URI forms. Same exported name, different values, from different modules. See [Finding D-1](#d-1--systemtypeuris-name-collision).
- **[POSITIVE]** `Deployment.validTime` is marked optional with a detailed Postel's Law justification comment, despite being "Required" in spec Table 10.
- **[POSITIVE]** Uses inline `import()` types for SWE Common references in `DatastreamSchemaResponse`/`ControlStreamSchemaResponse` — avoids importing the full SWE Common module at the type level.
- **[INFORMATIONAL]** `CommandStatusCodes` includes both full URIs and CURIEs — consistent with the Part 2 spec's allowance of both.

---

#### `helpers.ts` — 226 lines

| Aspect              | Assessment                                                                                                                                         |
| ------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Purpose**         | Utility functions: temporal formatting, validation, link scanning                                                                                  |
| **Imports**         | Value + type imports from `./model.js`, `./formats/constants.js` — `.js` extensions ✅                                                             |
| **Exports**         | `formatDateTimeParameter`, `isValidResourceType`, `assertValidResourceType`, `encodeResourceId`, `scanCsapiLinks`, `validateLimit`, `validateBbox` |
| **JSDoc**           | Complete — every function has `@param`, `@returns`, `@throws`                                                                                      |
| **Spec compliance** | Handles 3 link-relation conventions (ogc-cs:, plain name, items-with-href)                                                                         |

**Findings:**

- **[POSITIVE]** `scanCsapiLinks` normalizes `featuresOfInterest` → `samplingFeatures`, handling the alias cleanly.
- **[POSITIVE]** `validateBbox` validates both 4-element and 6-element bounding boxes with per-element `isFinite()` checks.
- **[INFORMATIONAL]** No `as any` casts.

---

#### `url_builder.ts` — 2,490 lines

| Aspect              | Assessment                                                                                  |
| ------------------- | ------------------------------------------------------------------------------------------- |
| **Purpose**         | Main `CSAPIQueryBuilder` class — URL construction for all 9 resource types                  |
| **Imports**         | Type imports from `./model.js`, value import from `./helpers.js` — `.js` extensions ✅      |
| **Exports**         | `CSAPIQueryBuilder` (default), `PARAM_NAME_MAP`, `TEMPORAL_KEYS`, `RESOURCE_PATH_OVERRIDES` |
| **JSDoc**           | Exceptional — every public method has `@param`, `@returns`, `@throws`, `@example`, `@see`   |
| **Spec compliance** | Implements query parameters per Part 1 Table 8 & Part 2 Table 6                             |

**Findings:**

- **[CONSISTENCY] `getCommandStatus` vs other methods** — Most methods delegate query string construction to `buildQueryString()`, but `getCommandStatus` manually appends the query string with `new URLSearchParams()`. This works correctly but breaks the internal pattern.
- **[POSITIVE]** `PARAM_NAME_MAP` cleanly maps TypeScript names to OGC wire names (`currentStatus → statusCode`, `systemId → system`, `foiId → foi`).
- **[POSITIVE]** Comment documents the historical double-encoding bug (F5) and how it was fixed.
- **[POSITIVE]** `RESOURCE_PATH_OVERRIDES` handles the `controlStreams → controlstreams` URL lowercasing.
- **[INFORMATIONAL]** At 2,490 lines this is the largest file. The class has ~80 public methods. Consider splitting into sub-classes by resource type in a future refactor, but the current monolith is coherent and well-organized.

---

#### `command-routing.ts` — 163 lines

| Aspect              | Assessment                                                                                                                                   |
| ------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| **Purpose**         | Per-server routing fallback for `/commands` rejection (OSH compatibility)                                                                    |
| **Imports**         | Value + type imports — `.js` extensions ✅                                                                                                   |
| **Exports**         | `getCommandRoutingPreference`, `setCommandRoutingPreference`, `clearCommandRoutingCache`, `isCommandRouteRejection`, `buildNestedCommandUrl` |
| **JSDoc**           | Complete with `@module`, `@example`, `@param`, `@returns`                                                                                    |
| **Spec compliance** | Implements fallback for servers that reject top-level routes                                                                                 |

**Findings:**

- **[DESIGN] Module-level mutable state** — `routingCache_` is a module-level `Map<string, CommandRoutingPreference>`. This is acceptable for a caching layer but means it's shared across all usages in the same JS context. The `clearCommandRoutingCache()` export mitigates this for testing.
- **[POSITIVE]** Clean separation of routing logic from the main builder.

---

### 3.2 Formats — Part 1 (GeoJSON)

#### `formats/index.ts` — 341 lines

| Aspect              | Assessment                                                                    |
| ------------------- | ----------------------------------------------------------------------------- |
| **Purpose**         | Barrel re-export for all format handlers                                      |
| **Imports/Exports** | Re-exports from 9 sub-modules — `.js` extensions ✅, `export type` correct ✅ |
| **JSDoc**           | Module-level comment                                                          |

**Findings:**

- **[CONSISTENCY]** Some type re-exports are individual lines (e.g., `export type { Link }` on its own) rather than grouped with related types. Minor style inconsistency.
- **[POSITIVE]** Clean separation of concerns across sub-modules.

---

#### `formats/constants.ts` — 336 lines

| Aspect              | Assessment                                                                                         |
| ------------------- | -------------------------------------------------------------------------------------------------- |
| **Purpose**         | Media types, vocabulary URIs, asset types, content-type map                                        |
| **Imports**         | `import type` from `../model.js` ✅                                                                |
| **Exports**         | 7 media type constants, `*TypeUris` objects, `CSAPI_CONTENT_TYPES`, vocabulary namespace constants |
| **JSDoc**           | Complete with spec references                                                                      |
| **Spec compliance** | Closely tracks OGC 23-001 Requirement Classes                                                      |

**Findings:**

- **[DESIGN]** <a id="d-1--systemtypeuris-name-collision"></a>**D-1: `SystemTypeUris` name collision** — `constants.ts` defines `SystemTypeUris` with both CURIE forms (`sosa:Sensor`, `ssn:System`) **and** full URI forms. `model.ts` defines `SystemTypeUris` with only full URI forms. Both are exported from the barrel. Consumer code importing from different modules gets different values under the same name. **Recommendation:** Rename one — e.g., `SystemTypeVocabulary` in constants vs `SystemTypeUris` in model, or consolidate into a single source.
- **[POSITIVE]** `CSAPI_CONTENT_TYPES` correctly maps resource types to appropriate `Content-Type` headers for write operations.

---

#### `formats/geojson.ts` — 527 lines

| Aspect              | Assessment                                                                                      |
| ------------------- | ----------------------------------------------------------------------------------------------- |
| **Purpose**         | GeoJSON Feature type recognition and Part 1 resource extraction                                 |
| **Imports**         | Type + value imports from model, constants, sensorml — `.js` extensions ✅                      |
| **Exports**         | `isCSAPIFeature`, `getCSAPIResourceType`, `parseValidTime`, `isValidUri`, `extractCSAPIFeature` |
| **JSDoc**           | Complete                                                                                        |
| **Spec compliance** | Implements classification priority: SOSA → SSN → SensorML vocabularies                          |

**Findings:**

- **[POSITIVE]** `extractCSAPIFeature` returns a typed union and uses `satisfies` for type narrowing — clean pattern.
- **[POSITIVE]** Parses `@link` inline associations (`systemKind@link`, `platform@link`, `deployedSystems@link`, `sampledFeature@link`) per the OGC extension pattern.
- **[POSITIVE]** `parseResourceRef` handles OSH's `type` fallback for `rt` — good interoperability.
- **[INFORMATIONAL]** Line 492: `as unknown[]` appears in a spread context — safe widening, not a type-safety hole.

---

#### `formats/classification.ts` — 126 lines

| Aspect      | Assessment                                                                    |
| ----------- | ----------------------------------------------------------------------------- |
| **Purpose** | Endpoint-context fallback for servers returning `featureType: null` (52North) |
| **Imports** | Type import from model — `.js` extension ✅                                   |
| **Exports** | `inferResourceTypeFromPath`, `classifyFeature`                                |
| **JSDoc**   | Complete                                                                      |

**Findings:**

- **[POSITIVE]** `classifyFeature` never overrides a valid `featureType` — only fills in when null. Defensive design.

---

#### `formats/property.ts` — 56 lines

| Aspect      | Assessment                                                                                |
| ----------- | ----------------------------------------------------------------------------------------- |
| **Purpose** | Parse Property (DerivedProperty) — the only Part 1 resource that is NOT a GeoJSON Feature |
| **Imports** | Type import — `.js` extension ✅                                                          |
| **Exports** | `parseProperty`                                                                           |
| **JSDoc**   | Complete; notes no live server currently returns Property data                            |

**Findings:**

- **[GAP]** Parser cannot be tested against live data — "No live server currently returns Property data (confirmed Smoke Test #6)". Low risk; the parser is structurally simple.

---

#### `formats/response.ts` — 131 lines

| Aspect      | Assessment                                            |
| ----------- | ----------------------------------------------------- |
| **Purpose** | Normalize FeatureCollection vs Items envelope formats |
| **Imports** | Value + type imports — `.js` extensions ✅            |
| **Exports** | Envelope normalization functions                      |
| **JSDoc**   | Complete                                              |

**Findings:**

- **[POSITIVE]** Handles both `features[]` (RFC 7946) and `items[]` (OSH / Part 2) envelope formats.

---

#### `formats/schema-response.ts` — 178 lines

| Aspect      | Assessment                                                                     |
| ----------- | ------------------------------------------------------------------------------ |
| **Purpose** | Parse datastream & control stream schema responses                             |
| **Imports** | Delegates to `parseSWEComponent()` and `parseEncoding()` — `.js` extensions ✅ |
| **Exports** | `parseDatastreamSchemaResponse`, `parseControlStreamSchemaResponse`            |
| **JSDoc**   | Complete                                                                       |

**Findings:**

- **[INFORMATIONAL]** Clean delegation to SWE Common parsers.

---

### 3.3 Formats — Part 2 (JSON)

#### `formats/part2.ts` — 518 lines

| Aspect              | Assessment                                                                                                               |
| ------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| **Purpose**         | All 5 Part 2 resource parsers                                                                                            |
| **Imports**         | Type + value imports — `.js` extensions ✅                                                                               |
| **Exports**         | `parseDatastream`, `parseObservation`, `parseControlStream`, `parseCommand`, `parseCommandStatus`, `normalizeStatusCode` |
| **JSDoc**           | Complete with spec references                                                                                            |
| **Spec compliance** | Tracks Part 2 Tables closely                                                                                             |

**Findings:**

- **[CONSISTENCY] Time field asymmetry** — `parseObservation` passes time strings through as-is, while `parseDatastream`/`parseControlStream` parse intervals. Documented in comments, but a future consumer expecting uniform behavior could be surprised. Each approach matches its spec table, so this is spec-driven rather than a bug.
- **[CONSISTENCY] Default statusCode handling** — `parseCommandStatus` defaults to `'PENDING'` when `statusCode` is missing, while `parseCommand`'s `currentStatus` remains `undefined` when absent. Both approaches are defensible but inconsistent.
- **[POSITIVE]** `normalizeObservedProperties` handles both `[{definition, label}]` and `["uri"]` forms — good server interoperability.
- **[POSITIVE]** Extracts cross-references (`system@id` → `systemId`, `datastream@id`, `samplingFeature@id`, `foi@id`) per Part 2 convention.

---

### 3.4 Formats — SensorML 3.0

#### `formats/sensorml/index.ts` — 141 lines

| Aspect      | Assessment                                                      |
| ----------- | --------------------------------------------------------------- |
| **Purpose** | Barrel re-export for SensorML parsers + types                   |
| **Exports** | Values + types from parser, sub-parsers, helpers, errors, types |
| **JSDoc**   | Module-level                                                    |

**Findings:**

- **[POSITIVE]** Clean barrel with correct `export type` usage.

---

#### `formats/sensorml/types.ts` — 928 lines

| Aspect      | Assessment                                                     |
| ----------- | -------------------------------------------------------------- |
| **Purpose** | Complete SensorML 3.0 type hierarchy                           |
| **Imports** | None (leaf type file)                                          |
| **Exports** | All SensorML interfaces, types, `SENSORML_PROCESS_TYPES` const |
| **JSDoc**   | Thorough — `@see` OAS line references throughout               |

**Findings:**

- **[POSITIVE]** Clean discriminated union via `SensorMLProcess['type']`.
- **[POSITIVE]** `SENSORML_PROCESS_TYPES` as const tuple enables runtime validation.

---

#### `formats/sensorml/parser.ts` — 457 lines

| Aspect      | Assessment                                                                                                                      |
| ----------- | ------------------------------------------------------------------------------------------------------------------------------- |
| **Purpose** | Main SensorML parser — type discrimination + shared property parsers                                                            |
| **Imports** | Type + value imports from `types.js`, SWE Common `types.js`, `errors.js`, `_helpers.js`, sub-parser files — `.js` extensions ✅ |
| **Exports** | `parseSensorML30`, plus shared parsers for DescribedObject/AbstractProcess/AbstractPhysicalProcess levels                       |
| **JSDoc**   | Excellent — `@module` with entry points listed                                                                                  |

**Findings:**

- **[DESIGN]** <a id="d-2--circular-import"></a>**D-2: Circular import** — `parser.ts` → sub-parsers → `_helpers.ts` → `parser.ts`. The cycle: `_helpers.ts` line 30 imports `parseSensorML30` from `parser.ts` to support recursive component parsing. Node.js ESM handles this at runtime (deferred binding), but it's a design smell. **Recommendation:** Use a callback injection pattern (like SWE Common's `ComponentParser`) instead of a direct circular import.
- **[POSITIVE]** Clean type-discriminator dispatch (`switch (json.type)`).

---

#### `formats/sensorml/_helpers.ts` — 277 lines

| Aspect      | Assessment                                                                                                                                               |
| ----------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Purpose** | Shared internal parsing helpers consolidating previously-duplicated code (Issue #54)                                                                     |
| **Imports** | Types from `types.js`, `SensorMLParseError` from `errors.js`, **`parseSensorML30` from `parser.js`** — `.js` extensions ✅                               |
| **Exports** | `isRecord`, `optionalString`, `parseLink`, `parseIOList`, `parseSettings`, `parseFeatureList`, `parseModes`, `parseProcessMethod`, `parseComponentEntry` |
| **JSDoc**   | Complete                                                                                                                                                 |

**Findings:**

- **[DESIGN]** Source of [circular import D-2](#d-2--circular-import) — line 30: `import { parseSensorML30 } from './parser.js';`. Used only in `parseComponentEntry` (line ~265) for recursive inline‐process parsing.
- **[DESIGN]** `isRecord()` is duplicated — identical function exists in `swecommon/_helpers.ts`. Could be shared at a common level.
- **[POSITIVE]** Consolidation from previously-duplicated private functions (Issue #54) is a clear improvement.

---

#### `formats/sensorml/errors.ts` — 40 lines

| Aspect      | Assessment                                      |
| ----------- | ----------------------------------------------- |
| **Purpose** | `SensorMLParseError` class with optional `path` |
| **JSDoc**   | Complete                                        |

**Findings:**

- **[POSITIVE]** Minimal, focused error class. Parallels `SweCommonParseError`.

---

#### `formats/sensorml/physical-system.ts` — 660 lines

| Aspect              | Assessment                                                                                                                                                 |
| ------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Purpose**         | `PhysicalSystem` + `PhysicalComponent` parsers, plus `parsePosition`                                                                                       |
| **Imports**         | Types from `types.js`, helpers from `_helpers.js` — `.js` extensions ✅                                                                                    |
| **Exports**         | `parsePhysicalSystem`, `parsePhysicalComponent`, `parsePosition`, `parseComponentList`, `parseConnectionList`, `parseProcessMethod`, `parseComponentEntry` |
| **JSDoc**           | Complete                                                                                                                                                   |
| **Spec compliance** | Tracks AbstractPhysicalProcess properties (attachedTo, localReferenceFrames, localTimeFrames, position)                                                    |

**Findings:**

- **[DESIGN]** <a id="d-3--duplication"></a>**D-3: Duplicated `parseComponentList` + `parseConnectionList`** — Both functions are **identically** implemented in this file (lines 70–143) **and** in `aggregate-process.ts` (lines 62–133). They are functionally the same: null check → array check → map with `parseComponentEntry`/`parseConnection`. **Recommendation:** Consolidate into `_helpers.ts` (where `parseComponentEntry` already lives) and import from both consumers.
- **[DESIGN]** Also duplicates `parseConnection` (private, identical logic in both files).
- **[DESIGN] Spread-then-delete pattern** — Lines 621–640 build the result via `{ ...(json as Record<string, unknown>), type: 'PhysicalComponent' as const }` then iterate `managedKeys` to delete raw values before re-assigning parsed versions. This intentionally preserves unknown/pass-through properties but can leak unexpected fields into typed results. The pattern is documented and intentional for DescribedObject pass-through.
- **[INFORMATIONAL]** `as unknown as GeoJsonPoint` (line 290) and `as unknown as Position` (line 390) — used for validated pass-through of GeoJSON structures; safe given preceding validation.

---

#### `formats/sensorml/simple-process.ts` — 148 lines

| Aspect      | Assessment                            |
| ----------- | ------------------------------------- |
| **Purpose** | `SimpleProcess` parser                |
| **Imports** | Types + helpers — `.js` extensions ✅ |
| **Exports** | `parseSimpleProcess`                  |
| **JSDoc**   | Complete                              |

**Findings:**

- **[DESIGN]** Same spread-then-delete pattern as physical-system.ts — consistent but carries same property-leak risk.
- **[INFORMATIONAL]** Smallest sub-parser. No `components`/`connections`.

---

#### `formats/sensorml/aggregate-process.ts` — 252 lines

| Aspect      | Assessment                                                                                                        |
| ----------- | ----------------------------------------------------------------------------------------------------------------- |
| **Purpose** | `AggregateProcess` parser                                                                                         |
| **Imports** | Types + helpers — `.js` extensions ✅                                                                             |
| **Exports** | `parseAggregateProcess`, `parseComponentList`, `parseConnectionList`, `parseComponentEntry`, `SensorMLParseError` |
| **JSDoc**   | Complete                                                                                                          |

**Findings:**

- **[DESIGN]** Source of duplication [D-3](#d-3--duplication) — `parseComponentList` and `parseConnectionList` duplicated here from `physical-system.ts`.
- **[DESIGN]** Same spread-then-delete pattern.

---

### 3.5 Formats — SWE Common 3.0

#### `formats/swecommon/index.ts` — 145 lines

| Aspect      | Assessment                                                                      |
| ----------- | ------------------------------------------------------------------------------- |
| **Purpose** | Barrel re-export for SWE Common parsers + types                                 |
| **Exports** | Values + types from parser, components, data-array, data-record, helpers, types |
| **JSDoc**   | Module-level                                                                    |

**Findings:**

- **[POSITIVE]** Clean barrel with correct `export type` usage.

---

#### `formats/swecommon/types.ts` — 740 lines

| Aspect      | Assessment                             |
| ----------- | -------------------------------------- |
| **Purpose** | Complete SWE Common 3.0 type hierarchy |
| **Imports** | None (leaf type file)                  |
| **Exports** | All SWE Common interfaces and types    |
| **JSDoc**   | Thorough with spec references          |

**Findings:**

- **[POSITIVE]** Clean type definitions matching OGC 24-014 schemas.

---

#### `formats/swecommon/_helpers.ts` — 88 lines

| Aspect      | Assessment                                                                           |
| ----------- | ------------------------------------------------------------------------------------ |
| **Purpose** | Shared helpers (`isRecord`, `parseBaseProperties`, `parseAssociationAttributeGroup`) |
| **Imports** | Type import from `types.js` ✅                                                       |
| **Exports** | 3 functions                                                                          |
| **JSDoc**   | Complete                                                                             |

**Findings:**

- **[DESIGN]** `isRecord()` duplicated from `sensorml/_helpers.ts` — see [D-4](#d-4--isrecord-duplication).

---

#### `formats/swecommon/parser.ts` — 1,470 lines

| Aspect      | Assessment                                                                                                                                                              |
| ----------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Purpose** | Main SWE Common parser: type discrimination, Vector, Matrix, DataChoice, Geometry, validation                                                                           |
| **Imports** | Types from `types.js`, values from `components.js`, `data-record.js`, `data-array.js`, `_helpers.js` — `.js` extensions ✅                                              |
| **Exports** | `parseSWEComponent`, `parseVector`, `parseMatrix`, `parseDataChoice`, `parseGeometry`, `detectEncoding`, `validateAgainstSchema`, `ValidationResult`, `ValidationError` |
| **JSDoc**   | Exceptional — `@module` with entry-point list, every function fully documented                                                                                          |

**Findings:**

- **[DESIGN]** <a id="d-5--swecommon-duplication"></a>**D-5: `SIMPLE_COMPONENT_TYPES` duplicated 3 times** — Identical `new Set([...])` in `parser.ts` (line 99), `data-record.ts` (line 66), `data-array.ts` (line 66). Should be a shared constant in `_helpers.ts`.
- **[DESIGN]** <a id="d-6--islinkreference-duplication"></a>**D-6: `isLinkReference` duplicated 3 times** — Identical function in `parser.ts` (line 129), `data-record.ts` (line 83), `data-array.ts` (line 83). Should be consolidated.
- **[INFORMATIONAL]** This pattern of duplication was used to avoid circular imports — `data-record.ts` and `data-array.ts` use a `ComponentParser` callback injection instead of importing `parseSWEComponent` directly, which is the correct approach that avoids the circular issue the SensorML module has.
- **[POSITIVE]** `ComponentParser` callback injection pattern in `data-record.ts`/`data-array.ts` avoids circular imports — better than the SensorML approach.

---

#### `formats/swecommon/components.ts` — 791 lines

| Aspect      | Assessment                                                                                                                                                                                         |
| ----------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Purpose** | All 10 simple component parsers (6 scalar + 4 range)                                                                                                                                               |
| **Imports** | Types from `types.js`, `isRecord` from `_helpers.js` — `.js` extensions ✅                                                                                                                         |
| **Exports** | `parseSimpleComponent` (discriminator), `parseQuantity`, `parseCount`, `parseBoolean`, `parseText`, `parseTime`, `parseCategory`, plus range variants, `parseUnitOfMeasure`, `SweCommonParseError` |
| **JSDoc**   | Complete                                                                                                                                                                                           |

**Findings:**

- **[POSITIVE]** `SweCommonParseError` parallels `SensorMLParseError` with same `path` pattern.
- **[POSITIVE]** Thorough constraint parsing (AllowedValues, AllowedTokens, AllowedTimes).

---

#### `formats/swecommon/data-array.ts` — 597 lines

| Aspect      | Assessment                                                       |
| ----------- | ---------------------------------------------------------------- |
| **Purpose** | DataArray parser with encoding support (JSON, Text, Binary, XML) |
| **Imports** | Types, components, data-record, \_helpers — `.js` extensions ✅  |
| **Exports** | `parseDataArray`, `parseEncoding`                                |
| **JSDoc**   | Complete with example                                            |

**Findings:**

- **[DESIGN]** Contains duplicated `SIMPLE_COMPONENT_TYPES` and `isLinkReference` — see [D-5](#d-5--swecommon-duplication), [D-6](#d-6--islinkreference-duplication).
- **[POSITIVE]** Supports all 4 encoding types per OGC 24-014.

---

#### `formats/swecommon/data-record.ts` — 247 lines

| Aspect      | Assessment                                         |
| ----------- | -------------------------------------------------- |
| **Purpose** | DataRecord parser with recursive field support     |
| **Imports** | Types, components, \_helpers — `.js` extensions ✅ |
| **Exports** | `parseDataRecord`, `ComponentParser` type          |
| **JSDoc**   | Complete with nested example                       |

**Findings:**

- **[DESIGN]** Contains duplicated `SIMPLE_COMPONENT_TYPES` and `isLinkReference` — see [D-5](#d-5--swecommon-duplication), [D-6](#d-6--islinkreference-duplication).
- **[POSITIVE]** `ComponentParser` callback type is clean — breaks potential circular import.

---

### 3.6 Modified Upstream Files

#### `src/ogc-api/endpoint.ts`

**Findings:**

- **[POSITIVE]** Adds `hasConnectedSystems` getter and `csapiCollections` getter — minimal upstream touch.

#### `src/ogc-api/info.ts`

**Findings:**

- **[POSITIVE]** `checkHasConnectedSystems` checks conformance for Part 1 Core **or** Part 2 Dynamic Data URIs.
- **[POSITIVE]** `parseCollections` uses `ogc-cs:` link prefix to set `hasConnectedSystems` flag.

#### `src/shared/mime-type.ts`

**Findings:**

- **[POSITIVE]** Adds 5 CSAPI MIME type detectors (sml+json, swe+json, swe+text, swe+csv, swe+binary).

#### `src/index.ts` — 69 lines

**Findings:**

- **[POSITIVE]** Does NOT re-export CSAPI — correct, because CSAPI uses a separate `./csapi` sub-path export.

---

### 3.7 Package Configuration

#### `package.json`

**Findings:**

- **[POSITIVE]** `"./csapi"` sub-path export configured with `types`, `import`, `browser`, `default` entries.
- **[POSITIVE]** `"sideEffects": false` enables tree-shaking.
- **[INFORMATIONAL]** The sub-path export correctly points to `dist/` outputs, matching the build pipeline.

---

## 4. Cross-Cutting Findings

### Import Conventions

- **All relative imports use `.js` extensions** — verified by regex search across all files. **0 violations.**
- **`import type` correctly used** for all type-only imports throughout the module. **0 violations.**
- **Three-tier dependency hierarchy holds**: CSAPI imports from `shared/` and `ogc-api/`, never the reverse direction.

### Type Cast Audit

| Location                   | Cast                                   | Justification                         | Risk                          |
| -------------------------- | -------------------------------------- | ------------------------------------- | ----------------------------- |
| `factory.ts:46`            | `as any`                               | Access private OgcApiEndpoint members | **High** — tracked Issue #122 |
| `factory.ts:57`            | `as unknown as OgcApiCollectionInfo`   | Double cast on collection doc         | **Medium** — compounds above  |
| `geojson.ts:492`           | `as unknown[]`                         | Safe array widening                   | None                          |
| `physical-system.ts:290`   | `as unknown as GeoJsonPoint`           | Validated GeoJSON pass-through        | Low                           |
| `physical-system.ts:390`   | `as unknown as Position`               | Validated position pass-through       | Low                           |
| `aggregate-process.ts:233` | `as unknown as Record<string,unknown>` | Delete during spread-then-delete      | Low (pattern)                 |
| All SensorML sub-parsers   | `as Record<string, unknown>`           | Spread-then-delete pattern            | Low (intentional)             |
| `_helpers.ts:276`          | `as unknown as ComponentEntry`         | Unrecognized component pass-through   | Low                           |

All `as any` casts in `.spec.ts` files are test-only and acceptable for testing boundary conditions.

### Circular Import Analysis

| Cycle      | Files                                                   | Mechanism                          |
| ---------- | ------------------------------------------------------- | ---------------------------------- |
| SensorML   | `parser.ts` → sub-parsers → `_helpers.ts` → `parser.ts` | Direct import of `parseSensorML30` |
| SWE Common | ✅ **None** — uses `ComponentParser` callback injection | Clean architecture                 |

---

## 5. Findings by Severity

### BUG (1)

| ID  | File               | Description                                                                               |
| --- | ------------------ | ----------------------------------------------------------------------------------------- |
| B-1 | `factory.ts:46,57` | `as any` + double cast accessing private `OgcApiEndpoint` members. Tracked by Issue #122. |

### DESIGN (8)

| ID  | File(s)                                                                                | Description                                                                       |
| --- | -------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------- |
| D-1 | `model.ts` / `constants.ts`                                                            | `SystemTypeUris` name collision — same name, different values, across two modules |
| D-2 | `sensorml/_helpers.ts` → `parser.ts`                                                   | Circular import; should use callback injection                                    |
| D-3 | `physical-system.ts` / `aggregate-process.ts`                                          | Duplicated `parseComponentList`, `parseConnectionList`, `parseConnection`         |
| D-4 | <a id="d-4--isrecord-duplication"></a>`sensorml/_helpers.ts` / `swecommon/_helpers.ts` | Duplicated `isRecord()` type guard                                                |
| D-5 | `swecommon/parser.ts` / `data-record.ts` / `data-array.ts`                             | `SIMPLE_COMPONENT_TYPES` duplicated 3 times                                       |
| D-6 | `swecommon/parser.ts` / `data-record.ts` / `data-array.ts`                             | `isLinkReference()` duplicated 3 times                                            |
| D-7 | All SensorML sub-parsers                                                               | Spread-then-delete pattern can leak unknown properties into typed results         |
| D-8 | `command-routing.ts`                                                                   | Module-level mutable state (`routingCache_`)                                      |

### GAP (2)

| ID  | File                                          | Description                                                                |
| --- | --------------------------------------------- | -------------------------------------------------------------------------- |
| G-1 | `formats/property.ts`                         | Parser untested against live server data (no server returns Property)      |
| G-2 | SensorML capability/characteristic/IO parsing | Uses `as unknown as` pass-through; full parsing deferred to Issues #24–#28 |

### CONSISTENCY (4)

| ID  | File(s)            | Description                                                                                                      |
| --- | ------------------ | ---------------------------------------------------------------------------------------------------------------- |
| C-1 | `url_builder.ts`   | `getCommandStatus` manually builds query string instead of using `buildQueryString()`                            |
| C-2 | `formats/part2.ts` | Time field parsing asymmetry: Observation pass-through vs Datastream/ControlStream interval parsing              |
| C-3 | `formats/part2.ts` | `parseCommandStatus` defaults missing statusCode to `'PENDING'`; `parseCommand` leaves `currentStatus` undefined |
| C-4 | `formats/index.ts` | Some type re-exports on individual lines vs grouped                                                              |

### INFORMATIONAL (5)

| ID  | File                 | Description                                                              |
| --- | -------------------- | ------------------------------------------------------------------------ |
| I-1 | `index.ts`           | ~170 exports in barrel — monitor for tree-shaking impact                 |
| I-2 | `url_builder.ts`     | 2,490 lines / ~80 methods — largest file, but coherent                   |
| I-3 | `model.ts`           | `CommandStatusCodes` includes both full URIs and CURIEs (spec-compliant) |
| I-4 | `schema-response.ts` | Clean delegation to SWE Common parsers                                   |
| I-5 | `package.json`       | Sub-path export correctly configured                                     |

### POSITIVE (12)

| ID   | Scope               | Description                                                                                                  |
| ---- | ------------------- | ------------------------------------------------------------------------------------------------------------ |
| P-1  | All files           | **Zero `.js` extension violations** — every relative import uses `.js` ✅                                    |
| P-2  | All files           | **Correct `import type` usage** throughout ✅                                                                |
| P-3  | All files           | **Three-tier hierarchy** (csapi → ogc-api → shared) never violated ✅                                        |
| P-4  | All files           | **Exceptional JSDoc quality** — `@param`, `@returns`, `@throws`, `@example`, `@see` on nearly every function |
| P-5  | Barrel files        | Correct `export type` for all type-only re-exports                                                           |
| P-6  | `helpers.ts`        | `scanCsapiLinks` normalizes `featuresOfInterest` → `samplingFeatures` alias                                  |
| P-7  | `geojson.ts`        | Classification priority (SOSA→SSN→SensorML), `@link` parsing, OSH `type` fallback                            |
| P-8  | `part2.ts`          | `normalizeObservedProperties` handles both object and string array forms                                     |
| P-9  | SWE Common          | `ComponentParser` callback injection avoids circular imports                                                 |
| P-10 | `sensorml/types.ts` | Clean discriminated union + `SENSORML_PROCESS_TYPES` const tuple                                             |
| P-11 | `factory.ts`        | Clear comment documenting planned `as any` removal timeline                                                  |
| P-12 | `package.json`      | `sideEffects: false` + correct sub-path export                                                               |

---

## 6. Metrics Summary

| Metric                                | Value                                                               |
| ------------------------------------- | ------------------------------------------------------------------- |
| Total production source files audited | 28                                                                  |
| Total production lines (approx.)      | ~11,200                                                             |
| Files with complete JSDoc             | 28/28 (100%)                                                        |
| `.js` extension violations            | 0                                                                   |
| `import type` violations              | 0                                                                   |
| Three-tier hierarchy violations       | 0                                                                   |
| `as any` in production code           | 1 (factory.ts)                                                      |
| Circular imports                      | 1 (SensorML)                                                        |
| Duplicated function groups            | 3 (components/connections, SIMPLE_COMPONENT_TYPES, isLinkReference) |

---

## 7. Recommendations

### Priority 1 — Before merging to main

1. **Resolve factory.ts `as any`** (B-1) — Depends on Issue #122 making `root`/`getCollectionDocument` public. Once resolved, remove both casts.

### Priority 2 — Near-term cleanup

2. **Consolidate `parseComponentList`/`parseConnectionList`/`parseConnection`** (D-3) — Move to `sensorml/_helpers.ts` and import from both `physical-system.ts` and `aggregate-process.ts`.
3. **Break SensorML circular import** (D-2) — Adopt the `ComponentParser` callback injection pattern that SWE Common already uses. Pass `parseSensorML30` as a callback to `parseComponentEntry` rather than importing directly.
4. **Resolve `SystemTypeUris` name collision** (D-1) — Either rename one or consolidate into a single definition with both CURIE and full URI forms.

### Priority 3 — Quality improvement

5. **Consolidate SWE Common duplicates** (D-5, D-6) — Move `SIMPLE_COMPONENT_TYPES` and `isLinkReference` to `swecommon/_helpers.ts`.
6. **Share `isRecord()`** (D-4) — Create a common utility or have one module re-export from the other.
7. **Standardize `getCommandStatus` query building** (C-1) — Refactor to use `buildQueryString()` like other methods.
8. **Complete SensorML capability/characteristic/IO parsing** (G-2) — Issues #24–#28.
