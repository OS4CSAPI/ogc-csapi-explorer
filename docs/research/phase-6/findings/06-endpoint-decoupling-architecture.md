# Findings Report 06: Endpoint Decoupling Architecture — Complete Design Blueprint for CSAPI Extraction

> **Plan 6 of 8** | **Phase 6 — Upstream Acceptance Refactoring**

---

## Metadata

| Field                  | Value                                                                                                 |
| ---------------------- | ----------------------------------------------------------------------------------------------------- |
| **Research Plan**      | [Plan 06: Endpoint Decoupling Architecture](../research-plans/06-endpoint-decoupling-architecture.md) |
| **Plan Type**          | Design synthesis                                                                                      |
| **Date Started**       | 2026-02-24                                                                                            |
| **Date Completed**     | 2026-02-24                                                                                            |
| **Research Time**      | ~4 hours (actual)                                                                                     |
| **Estimated Time**     | 3–4 hours (from plan)                                                                                 |
| **Questions Answered** | 44 of 44 detailed questions                                                                           |
| **Depends On**         | Plans 02, 03, 04, 05                                                                                  |
| **Blocks**             | Plan 08 (File-Level Changelist and Commit Strategy)                                                   |

---

## Source Summary

### Primary Sources Consulted

| Source                        | Path / URL                                         | What Was Extracted                                                                                                                                                                                                                                                                                                                                                     |
| ----------------------------- | -------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| OGC API endpoint class        | `src/ogc-api/endpoint.ts` (896 lines)              | All CSAPI imports (lines 52–53), class fields, `csapi()` method (lines 385–413), `extractRootResourceUrls()` (lines 425–436), `getCollectionDocument()` (lines 438–468), `hasConnectedSystems` (lines 320–338), `csapiCollections` (lines 237–247), `edr()` method (lines 341–354), constructor (`private baseUrl: string`, line 155), private `root` getter (line 72) |
| Root barrel file              | `src/index.ts` (252 lines)                         | ~170 lines of CSAPI re-exports (lines 45–227): 1 default class, 3 value exports, ~27 function exports, ~110 type exports                                                                                                                                                                                                                                               |
| CSAPIQueryBuilder constructor | `src/ogc-api/csapi/url_builder.ts` (lines 106–174) | Constructor: `Pick<OgcApiCollectionInfo, 'id' \| 'title' \| 'links'>` + optional `Map<string, string>`. Uses `import type`.                                                                                                                                                                                                                                            |
| `scanCsapiLinks`              | `src/ogc-api/csapi/helpers.ts` (lines 129–174)     | Accepts `Array<{rel?, href?}>`, returns `Map<string, string>`. Uses `CSAPIResourceTypes` internally.                                                                                                                                                                                                                                                                   |
| CSAPI endpoint tests          | `src/ogc-api/endpoint.spec.ts` (lines 2836–2900)   | 6 `it()` blocks in 2 describe blocks: nominal (4 tests) + non-CSAPI (2 tests)                                                                                                                                                                                                                                                                                          |
| Info utilities                | `src/ogc-api/info.ts`                              | `checkHasConnectedSystems` (lines 112–123): zero CSAPI imports, conformance URIs only. `parseCollections`: link regex only.                                                                                                                                                                                                                                            |
| CSAPI formats barrel          | `src/ogc-api/csapi/formats/index.ts` (344 lines)   | Complete re-exports from constants, GeoJSON, SensorML, SWE Common                                                                                                                                                                                                                                                                                                      |
| CSAPI model                   | `src/ogc-api/csapi/model.ts` (776 lines)           | All type and value exports; imports are `import type` from `shared/` and `../model.js`                                                                                                                                                                                                                                                                                 |
| EDR demo example              | `app/examples/edr.ts`                              | EDR consumer pattern — uses `endpoint.edr(collection)`                                                                                                                                                                                                                                                                                                                 |

### Prior Findings Used

| Finding | Path                                                  | What Was Consumed                                                                                                                                                                                                                              |
| ------- | ----------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Plan 02 | `findings/02-edr-integration-pattern-analysis.md`     | EDR decoupling baseline: 1 import, 3 public members, 0 root exports, `edr()` uses `getCollectionInfo` (not raw doc). Why EDR is acceptable at 656 lines but CSAPI fails at 11,767 lines. Key takeaway: scale is the differentiator.            |
| Plan 03 | `findings/03-separate-entry-point-design-patterns.md` | `package.json` `"exports"` configuration: 4 conditions (`types`, `import`, `browser`, `default`), barrel file necessity, `"sideEffects": false`, no `typesVersions` needed. All bundlers compatible.                                           |
| Plan 04 | `findings/04-sub-module-api-design-patterns.md`       | Two-layer API recommendation: sync constructor (unchanged) + async factory `createCSAPIBuilder(endpoint, collectionId)`. Constructor injection dominant for stateful sub-modules. No library has CSAPI's exact "async data from core" pattern. |
| Plan 05 | `findings/05-module-decoupling-patterns.md`           | Keep Level 3.5 coupling (`Pick<>` + `import type`). Generalize `scanCsapiLinks` into shared link scanner. One-shot extraction. Barrel file + `"exports"`. Factory function serves dual duty (consumer API + decoupling).                       |

---

## 1. Executive Summary

This report synthesizes all prior research (Plans 02–05) into a concrete, implementation-ready architecture for decoupling CSAPI from `endpoint.ts`. Every architectural decision for the upstream refactoring is made here.

**Selected Architecture:**

- **Consumer API:** `createCSAPIBuilder(endpoint, collectionId)` — an async factory function exported from `@camptocamp/ogc-client/csapi` that replaces `endpoint.csapi(collectionId)`. Lives in `src/ogc-api/csapi/factory.ts`.
- **Coupling Level:** Keep Level 3.5 (`Pick<OgcApiCollectionInfo, 'id' | 'title' | 'links'>` + `import type`). Zero change to `CSAPIQueryBuilder` constructor signature.
- **Module Boundary:** `hasConnectedSystems` and `csapiCollections` **stay** on `OgcApiEndpoint` (zero CSAPI imports — they follow the accepted EDR pattern). The `csapi()` method, `extractRootResourceUrls()`, and `collection_id_to_csapi_builder_` cache are **removed**.
- **`scanCsapiLinks` Resolution:** Stays in `csapi/helpers.ts` unchanged. The problem resolves itself: once `csapi()` and `extractRootResourceUrls()` are removed from the endpoint, the endpoint no longer calls `scanCsapiLinks`, eliminating the constraint violation. No generalization needed.
- **Public API Changes:** `getCollectionDocument()` and `root` on `OgcApiEndpoint` change from `private` to `public` (two 1-word changes). These are needed by the factory function and are consistent with the existing public API pattern.
- **Barrel File:** New `src/ogc-api/csapi/index.ts` re-exports all ~141 symbols currently in `src/index.ts` from CSAPI modules, plus the new `createCSAPIBuilder` factory function.
- **Test Migration:** 4 of 6 CSAPI tests stay in `endpoint.spec.ts` (they test `hasConnectedSystems` and `csapiCollections`). 2 tests are rewritten for the factory function and move to a CSAPI test file.

**Key Simplification Over Prior Plans:** Plan 05 recommended generalizing `scanCsapiLinks` into a shared `scanResourceLinks` utility. This report finds that generalization is **unnecessary** — removing `csapi()` and `extractRootResourceUrls()` from the endpoint eliminates all `csapi/` imports from `endpoint.ts` without needing a shared scanner. The simplest path was always available: just move the orchestration to the CSAPI module.

---

## 2. Prior Findings Synthesis

### Question 1: What consumer API pattern did Plan 04 recommend? What coupling level did Plan 05 recommend? Do they align?

**Answer:** They align completely.

- **Plan 04:** Two-layer API — sync constructor (unchanged `CSAPIQueryBuilder(doc, urls)`) + async factory function (`createCSAPIBuilder(endpoint, collectionId)`). Constructor injection is the dominant pattern for stateful sub-modules (4/7 studied libraries).
- **Plan 05:** Keep Level 3.5 coupling (`Pick<>` + `import type`). The factory function from Plan 04 is the mechanism for removing the `CSAPIQueryBuilder` import from `endpoint.ts` — "the factory function serves double duty (consumer API + architectural decoupling)."

**No conflict.** Plan 04's factory function accepts the endpoint instance (Level 1 for the factory) while Plan 05's Level 3.5 applies to what the constructor accepts (extracted data). The factory bridges these: it accepts the endpoint (convenient for consumers), extracts the data, and passes it to the constructor (narrow coupling). This is the same layered pattern seen in AWS SDK (sync `Upload` constructor + async `done()`) and Angular CDK (static factory → internal construction).

### Question 2: How does Plan 02's EDR pattern inform the CSAPI design?

**Answer:** EDR demonstrates the accepted integration pattern: a builder class in a sub-folder, a factory method on `OgcApiEndpoint`, conformance checks in `info.ts`, and collection detection in `parseCollections()`. The EDR pattern is acceptable because:

1. **Scale:** 656 lines / 3 files vs. CSAPI's 11,767 lines / 27 files
2. **Root exports:** EDR exports zero symbols from `index.ts`; CSAPI exports ~170 lines
3. **Import footprint:** EDR has 1 import into `endpoint.ts`; CSAPI has 2
4. **jahow's explicit feedback:** EDR was approved; CSAPI was rejected with two specific requirements

The critical insight from Plan 02 is that `hasConnectedSystems` and `csapiCollections` follow the **identical pattern** as `hasEnvironmentalDataRetrieval` and `edrCollections` — they use `info.ts` functions that check conformance URIs and link relation regex with **zero imports from `csapi/`**. If the EDR equivalents are acceptable, the CSAPI equivalents should be too.

### Question 3: What `package.json` `"exports"` configuration did Plan 03 recommend?

**Answer:** Add `"./csapi"` sub-path with 4 conditions:

```json
"./csapi": {
  "types": "./dist/ogc-api/csapi/index.d.ts",
  "import": "./dist/ogc-api/csapi/index.js",
  "browser": "./dist/ogc-api/csapi/index.js",
  "default": "./dist/ogc-api/csapi/index.js"
}
```

Plus `"sideEffects": false` on the root `package.json`. This fits the barrel file design perfectly — all conditions point to the barrel output. All bundlers (Vite, webpack 5, esbuild, Rollup) and Node.js ≥ 12.7 resolve it correctly.

### Question 4: What `import type` strategy did Plan 05 recommend?

**Answer:** Keep relative paths, keep `Pick<>`, keep current `import type` statements:

```typescript
// In csapi/url_builder.ts — KEEP (erased at runtime, provides drift detection):
import type { OgcApiCollectionInfo } from '../model.js';
```

`import type` creates a compile-time dependency but zero runtime dependency. This does NOT violate constraint 3 — constraint 3 prohibits _core importing from CSAPI_, not _CSAPI importing types from core_. The `import type` direction (CSAPI → core) is the explicitly allowed dependency direction.

### Question 5: What `scanCsapiLinks` placement did Plan 05 recommend?

**Answer:** Plan 05 recommended Option C — generalize into a shared `scanResourceLinks` utility in `ogc-api/link-utils.ts`.

**This report overrides that recommendation.** The generalization is unnecessary because:

1. `endpoint.ts` calls `scanCsapiLinks` only inside `extractRootResourceUrls()` (line 435)
2. `extractRootResourceUrls()` is called only by `csapi()` (line 407)
3. We are removing `csapi()` from the endpoint
4. Therefore `extractRootResourceUrls()` has no callers and is also removed
5. Therefore the `import { scanCsapiLinks }` on line 53 has no usages and is removed

The generalization solves a problem that no longer exists. `scanCsapiLinks` stays in `csapi/helpers.ts`, called only by CSAPI internal code (`url_builder.ts:extractAvailableResources`) and the new factory function (also in CSAPI). Zero constraint violations.

**This is the key simplification of the entire design.** By removing the `csapi()` method and its private helper from the endpoint, both CSAPI imports become unused and can be deleted. No shared utilities, no generalization, no duplication.

### Question 6: Did any Plan 04 case study demonstrate a pattern where the core provides async data to the sub-module without importing it?

**Answer:** No library had CSAPI's exact "async data from core" challenge. Plan 04's findings: "No studied library has a sub-module that needs HTTP-resolved data from the core as a prerequisite."

The recommended solution is the factory function pattern, which Plan 04 identifies as an "original contribution to the pattern catalog." The factory:

1. Accepts the endpoint instance (runtime dependency via parameter, not import)
2. Calls endpoint's public methods to resolve data asynchronously
3. Passes resolved data to the synchronous constructor

The closest parallels are AWS SDK's `Upload` (sync constructor + async `done()`) and drizzle-orm's `drizzle()` factory (accepts connection config, resolves lazily).

---

## 3. Consumer API Design

### Question 7: After decoupling, who performs each of the 4 operations currently in `csapi()`?

**Answer:**

| Operation                       | Currently (endpoint)                             | After (factory function)                             |
| ------------------------------- | ------------------------------------------------ | ---------------------------------------------------- |
| (a) Check `hasConnectedSystems` | `await this.hasConnectedSystems`                 | `await endpoint.hasConnectedSystems`                 |
| (b) Check cache                 | `cache.has(collectionId)`                        | **Removed** — no automatic caching                   |
| (c) Get raw collection document | `await this.getCollectionDocument(collectionId)` | `await endpoint.getCollectionDocument(collectionId)` |
| (d) Extract root resource URLs  | `await this.extractRootResourceUrls()`           | `scanCsapiLinks((await endpoint.root)?.links ?? [])` |
| Construct builder               | `new CSAPIQueryBuilder(doc, urls)`               | `new CSAPIQueryBuilder(doc, urls)`                   |

All operations move to the factory function in `csapi/factory.ts`. The factory calls endpoint methods that are being made public (`getCollectionDocument`, `root`). The `scanCsapiLinks` call is internal to CSAPI — no constraint violation.

### Question 8: Must `getCollectionDocument` become public?

**Answer:** Yes. This is the minimum change required.

`getCollectionDocument(collectionId)` is currently private (line 438). The factory function needs it to obtain the raw collection document with links intact (because `parseBaseCollectionInfo()` strips the `links` array, making `getCollectionInfo()` unsuitable for CSAPI).

**Implications of making it public:**

- **Positive:** Useful for any consumer who needs the raw collection JSON (not just CSAPI)
- **Positive:** Already used by `getStyleMetadataDocument()` — a well-tested, stable method
- **Neutral:** Return type `Promise<OgcApiDocument>` is generic, not CSAPI-specific
- **Risk:** jahow may question why a new public method is being added

The 1-word change (`private` → `public`) is the minimum viable path. The alternative (having the factory fetch the collection document itself via HTTP) would duplicate logic and waste HTTP requests.

### Question 9: Must `extractRootResourceUrls` become public?

**Answer:** No. It is removed entirely. The factory function scans root links directly:

```typescript
const rootDoc = await endpoint.root;
const links = rootDoc?.links;
const resourceUrls = Array.isArray(links) ? scanCsapiLinks(links) : new Map();
```

This requires `endpoint.root` to be public.

**Must `root` become public?** Yes — the `root` getter (line 72) is currently private. The factory function needs access to the root document's links for resource URL discovery. Making it public is a 1-word change.

**Justification:** The endpoint already exposes parsed views of the root document (`info`, `conformanceClasses`). Exposing the raw root document is consistent with this pattern and useful beyond CSAPI (any consumer wanting to inspect the raw root).

### Question 10: Recommended consumer code, end-to-end

**Answer:**

**Before (current):**

```typescript
import { OgcApiEndpoint } from '@camptocamp/ogc-client';

const endpoint = await new OgcApiEndpoint('https://api.example.com');
const builder = await endpoint.csapi('weather-stations');
const url = builder.getSystems({ bbox: [-180, -90, 180, 90], limit: 50 });
```

**After (recommended):**

```typescript
import { OgcApiEndpoint } from '@camptocamp/ogc-client';
import { createCSAPIBuilder } from '@camptocamp/ogc-client/csapi';

const endpoint = await new OgcApiEndpoint('https://api.example.com');
const builder = await createCSAPIBuilder(endpoint, 'weather-stations');
const url = builder.getSystems({ bbox: [-180, -90, 180, 90], limit: 50 });
```

**Change for consumers:** One additional import line, and `endpoint.csapi(id)` becomes `createCSAPIBuilder(endpoint, id)`. The builder API is identical.

**Advanced usage (direct construction, Layer 1):**

```typescript
import CSAPIQueryBuilder from '@camptocamp/ogc-client/csapi';

// Consumer already has collection data from own API calls
const builder = new CSAPIQueryBuilder(
  { id: 'weather-stations', title: 'Weather Stations', links: collectionLinks },
  rootResourceUrls
);
```

### Question 11: How does caching work after decoupling?

**Answer:** **No automatic caching.** The `collection_id_to_csapi_builder_` Map is removed from the endpoint.

**Why this is acceptable:**

- The `CSAPIQueryBuilder` constructor is cheap — it only scans links and extracts a base URL (no HTTP requests)
- The expensive operations (`getCollectionDocument`, `root`) are already cached internally by the endpoint (they return cached Promises)
- Calling `createCSAPIBuilder(endpoint, 'weather-stations')` twice constructs two builder instances, but both reuse the same cached endpoint data

**If consumers need instance caching:** They cache the builder themselves:

```typescript
const builders = new Map<string, CSAPIQueryBuilder>();
async function getBuilder(endpoint, id) {
  if (!builders.has(id))
    builders.set(id, await createCSAPIBuilder(endpoint, id));
  return builders.get(id);
}
```

### Question 12: How does the `hasConnectedSystems` guard work?

**Answer:** The factory function checks it, matching the current behavior:

```typescript
export async function createCSAPIBuilder(
  endpoint: OgcApiEndpoint,
  collectionId: string
): Promise<CSAPIQueryBuilder> {
  if (!(await endpoint.hasConnectedSystems)) {
    throw new EndpointError('Endpoint does not support Connected Systems');
  }
  // ... construct builder
}
```

This mirrors `csapi()`'s current guard. The consumer can also check beforehand:

```typescript
if (await endpoint.hasConnectedSystems) {
  const builder = await createCSAPIBuilder(endpoint, 'weather-stations');
}
```

### Question 13: Complete factory function signature with JSDoc

**Answer:**

````typescript
import type OgcApiEndpoint from '../endpoint.js';
import type { OgcApiCollectionInfo } from '../model.js';
import { EndpointError } from '../../shared/errors.js';
import CSAPIQueryBuilder from './url_builder.js';
import { scanCsapiLinks } from './helpers.js';

/**
 * Creates a {@link CSAPIQueryBuilder} for constructing Connected Systems
 * query URLs against the given collection on an OGC API endpoint.
 *
 * This factory function replaces the former `endpoint.csapi(collectionId)`
 * method, which was removed to decouple the CSAPI module from the core
 * endpoint class.
 *
 * The function:
 * 1. Verifies the endpoint supports Connected Systems
 * 2. Fetches the raw collection document (preserving link relations)
 * 3. Scans the root API document for top-level CSAPI resource URLs
 * 4. Constructs and returns a CSAPIQueryBuilder
 *
 * @param endpoint - An OGC API endpoint instance.
 * @param collectionId - The collection identifier to create a builder for.
 * @returns A CSAPIQueryBuilder scoped to the specified collection.
 * @throws {EndpointError} If the endpoint does not support Connected Systems.
 * @throws {EndpointError} If the collection is not found.
 *
 * @example
 * ```ts
 * import { OgcApiEndpoint } from '@camptocamp/ogc-client';
 * import { createCSAPIBuilder } from '@camptocamp/ogc-client/csapi';
 *
 * const endpoint = await new OgcApiEndpoint('https://api.example.com');
 * const builder = await createCSAPIBuilder(endpoint, 'weather-stations');
 * const url = builder.getSystems({ bbox: [-180, -90, 180, 90], limit: 50 });
 * ```
 *
 * @see {@link CSAPIQueryBuilder} for all available query methods
 * @see https://docs.ogc.org/is/23-001/23-001.html
 * @see https://docs.ogc.org/is/23-002/23-002.html
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

**Import analysis:**

- `import type OgcApiEndpoint` — type-only, erased at runtime. CSAPI → core direction (allowed).
- `import type { OgcApiCollectionInfo }` — type-only, already exists in `url_builder.ts`. Used for the type assertion.
- `import { EndpointError }` — value import from `shared/` (not from core `ogc-api/`). Acceptable per Plan 05 findings.
- `import CSAPIQueryBuilder` — internal CSAPI import. Fine.
- `import { scanCsapiLinks }` — internal CSAPI import. Fine.

### Question 14: Impact on `app/examples/edr.ts` and other consumer examples

**Answer:** No CSAPI consumer examples exist in the repo. `app/examples/edr.ts` uses the EDR pattern (`endpoint.edr(collection)`) — unchanged. No demo files reference `endpoint.csapi()` or `CSAPIQueryBuilder`.

---

## 4. `hasConnectedSystems` and `csapiCollections` Placement

### Question 15: Can `hasConnectedSystems` stay on the endpoint?

**Answer:** Yes. Explicit constraint verification:

| Constraint                  | Status | Evidence                                                                                                                                                                                                   |
| --------------------------- | ------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1. No CSAPI in root exports | ✓ N/A  | `hasConnectedSystems` is not an export in `index.ts` — it's a property on `OgcApiEndpoint`                                                                                                                 |
| 2. Separate entry point     | ✓ N/A  | Not related to the `./csapi` entry point                                                                                                                                                                   |
| 3. No outward imports       | ✓ Pass | `hasConnectedSystems` calls `checkHasConnectedSystems()` from `info.ts` (line 112), which checks conformance URI strings only: `cc.indexOf('ogcapi-connectedsystems-1') > -1`. Zero imports from `csapi/`. |
| 4. One-way dependency       | ✓ Pass | Removing `src/ogc-api/csapi/` entirely does not affect `hasConnectedSystems` — it has no reference to CSAPI code.                                                                                          |

**Precedent:** `hasEnvironmentalDataRetrieval` follows the identical pattern and was accepted by jahow in PR #114.

### Question 16: Can `csapiCollections` stay on the endpoint?

**Answer:** Yes. Explicit constraint verification:

| Constraint                  | Status | Evidence                                                                                                                                                                                             |
| --------------------------- | ------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1. No CSAPI in root exports | ✓ N/A  | Property on `OgcApiEndpoint`, not a separate export                                                                                                                                                  |
| 2. Separate entry point     | ✓ N/A  | Not related                                                                                                                                                                                          |
| 3. No outward imports       | ✓ Pass | `csapiCollections` calls `parseCollections()` from `info.ts`, which checks `collection.links?.some(link => /^ogc-cs:.+$/.test(link.rel ?? ''))`. Zero imports from `csapi/`. Uses string regex only. |
| 4. One-way dependency       | ✓ Pass | Removing `csapi/` does not affect `csapiCollections`.                                                                                                                                                |

**Precedent:** `edrCollections` follows the identical pattern.

### Question 17: Discoverability story without `endpoint.csapi()`

**Answer:** The endpoint provides discovery but not construction:

1. Consumer checks `endpoint.hasConnectedSystems` — endpoint says "yes, CSAPI is available"
2. Consumer checks `endpoint.csapiCollections` — endpoint says "these collections have CSAPI resources"
3. Consumer imports `createCSAPIBuilder` from `@camptocamp/ogc-client/csapi` — documented in JSDoc on `hasConnectedSystems` and `csapiCollections`
4. Consumer calls `createCSAPIBuilder(endpoint, collectionId)` — factory returns a builder

The JSDoc on `hasConnectedSystems` and `csapiCollections` should be updated to reference the factory function:

```typescript
/**
 * @see Import `createCSAPIBuilder` from `@camptocamp/ogc-client/csapi` to create a query builder
 */
```

### Question 18: Should `hasConnectedSystems` also be available from the CSAPI module?

**Answer:** No. Dual availability adds complexity without benefit:

- `hasConnectedSystems` doesn't import from CSAPI, so it naturally belongs on the endpoint
- Adding it to CSAPI would require CSAPI to import from the endpoint (or accept conformance classes as a parameter) — either way, more code
- Consumers already have the endpoint instance when they want to check support

**One location, one source of truth.**

### Question 19: Does Plan 04's `CSAPIClient.isSupported(endpoint)` pattern conflict with keeping `hasConnectedSystems` on the endpoint?

**Answer:** No conflict. Plan 04 noted that pattern as a theoretical option; the recommendation was the factory function approach. The factory function's `hasConnectedSystems` guard serves the same purpose as a hypothetical `isSupported()` static method — but it's simpler because the guard is automatic (built into the factory). Consumers who want to check support first use the existing `endpoint.hasConnectedSystems` property.

---

## 5. `scanCsapiLinks` and `extractRootResourceUrls` Resolution

### Question 20: Is `scanCsapiLinks` fundamentally CSAPI-specific?

**Answer:** Yes. It uses `CSAPIResourceTypes` from `csapi/model.ts` — the constant array of 9 resource type strings (`systems`, `deployments`, `samplingFeatures`, `procedures`, `properties`, `datastreams`, `observations`, `controlStreams`, `commands`). It also implements the `featuresOfInterest → samplingFeatures` normalization, which is CSAPI-specific domain knowledge.

A generic version _could_ be parameterized to accept a known-types set and prefix, but **this is unnecessary** — see Question 5 synthesis.

### Question 21: What are the options for eliminating the `scanCsapiLinks` constraint violation?

**Five options were evaluated:**

| Option | Description                                                               | Constraints ✓/✗ | Minimum-change?                                                         |
| ------ | ------------------------------------------------------------------------- | --------------- | ----------------------------------------------------------------------- |
| A      | Inline `scanCsapiLinks` logic into endpoint (~40 lines duplicated)        | ✓✓✓✓            | No — duplication                                                        |
| B      | Move `scanCsapiLinks` to shared utils                                     | ✓✓✓✓            | No — pollutes shared with CSAPI-specific code                           |
| C      | Generalize into `scanResourceLinks` (Plan 05 recommendation)              | ✓✓✓✓            | No — new shared code, CSAPI wrapper, resource type constant in endpoint |
| D      | **Remove `extractRootResourceUrls` from endpoint entirely**               | ✓✓✓✓            | **Yes** — deletes code instead of moving it                             |
| E      | Move `CSAPIResourceTypes` to shared, then move `scanCsapiLinks` to shared | ✓✓✓✓            | No — moves CSAPI constants to shared                                    |

### Question 22: Constraint verification for each option

**Option D (selected) — remove from endpoint, let factory handle it:**

| Constraint                  | Status | Evidence                                                                                                                               |
| --------------------------- | ------ | -------------------------------------------------------------------------------------------------------------------------------------- |
| 1. No CSAPI in root exports | ✓      | `extractRootResourceUrls` was never in root exports                                                                                    |
| 2. Separate entry point     | ✓      | Not affected                                                                                                                           |
| 3. No outward imports       | ✓      | `endpoint.ts` no longer calls `scanCsapiLinks`. The factory function in CSAPI calls it — that's internal CSAPI, not an outward import. |
| 4. One-way dependency       | ✓      | Removing `csapi/` removes the factory function too. The endpoint has no reference to `scanCsapiLinks` or `extractRootResourceUrls`.    |

### Question 23: Which option has the lowest migration effort?

**Answer:** Option D. It **deletes** ~18 lines from `endpoint.ts` (the `extractRootResourceUrls` method + JSDoc) and removes the `import { scanCsapiLinks }` line. The equivalent logic is written once in the factory function (~4 lines). No new shared utilities, no code duplication, no generalization.

### Question 24: If Option D is chosen, how does the factory get root document links?

**Answer:** The factory calls `endpoint.root` (made public):

```typescript
const rootDoc = await endpoint.root;
const links = rootDoc?.links;
const resourceUrls = Array.isArray(links) ? scanCsapiLinks(links) : new Map();
```

`endpoint.root` returns `Promise<OgcApiDocument>`, which is the cached root document with its `links` array intact.

### Question 25: API surface concern of making `root` public?

**Answer:** Minimal concern. The endpoint already exposes parsed views of the root document:

| Existing public getter | Returns                                                      |
| ---------------------- | ------------------------------------------------------------ |
| `info`                 | `Promise<OgcApiEndpointInfo>` — parsed from root             |
| `conformanceClasses`   | `Promise<ConformanceClass[]>` — parsed from conformance doc  |
| `allCollections`       | `Promise<{name, hasRecords?, ...}[]>` — parsed from data doc |

Adding `root: Promise<OgcApiDocument>` follows the same pattern — it provides the raw document alongside the parsed views. There is precedent in the codebase for exposing raw documents (e.g., `conformance` returns a raw document internally; `root` would do the same publicly).

---

## 6. `getCollectionDocument` and Data Pipeline

### Question 26: Must `getCollectionDocument` become public?

**Answer:** Yes. The factory function requires it to get the raw collection document with links preserved. `getCollectionInfo()` (which is public) is unsuitable because `parseBaseCollectionInfo()` strips the `links` array, and `CSAPIQueryBuilder` needs `ogc-cs:*` link relations.

### Question 27: Public signature and return type

**Answer:**

```typescript
/**
 * Fetches the raw collection document for the given collection ID.
 *
 * Unlike {@link getCollectionInfo}, this returns the unprocessed document
 * with all properties intact, including the `links` array. This is useful
 * for modules that need to inspect link relations (e.g., CSAPI resource
 * discovery).
 *
 * @param collectionId - The collection identifier.
 * @returns The raw collection document.
 * @throws {EndpointError} If the collection is not found.
 */
public getCollectionDocument(collectionId: string): Promise<OgcApiDocument>
```

The return type `Promise<OgcApiDocument>` is the existing type — no narrowing needed. The type is already generic and non-CSAPI-specific.

### Question 28: Where does the `as unknown as OgcApiCollectionInfo` type assertion live?

**Answer:** In the factory function:

```typescript
return new CSAPIQueryBuilder(
  collectionDoc as unknown as OgcApiCollectionInfo,
  resourceUrls
);
```

This assertion bridges `OgcApiDocument` (generic) to `OgcApiCollectionInfo` (typed). The raw collection JSON has `id`, `title`, and `links` fields matching the `Pick<>` — the assertion is safe. Placing it in the factory (not the consumer code) encapsulates this internal detail.

### Question 29: Should CSAPI provide a `prepareCollectionForCSAPI` function?

**Answer:** No. The type assertion in the factory function is sufficient. A separate preparation function adds API surface without value — the assertion is a simple, well-understood TypeScript pattern. The scope gate says "Do NOT introduce ... data record types unless strictly necessary."

### Question 30: Complete data flow diagram

**Before:**

```
Consumer
  │
  └── endpoint.csapi(collectionId)      ← PUBLIC METHOD on OgcApiEndpoint
        │
        ├── await this.hasConnectedSystems     ← endpoint internal (info.ts)
        ├── cache check (collection_id_to_csapi_builder_)
        ├── await this.getCollectionDocument(collectionId)  ← PRIVATE method
        ├── await this.extractRootResourceUrls()  ← PRIVATE method
        │     └── scanCsapiLinks(rootDoc.links)  ← IMPORT from csapi/helpers ✗
        └── new CSAPIQueryBuilder(doc, urls)  ← IMPORT from csapi/url_builder ✗
              │
              └── CSAPIQueryBuilder instance returned to consumer
```

**After:**

```
Consumer
  │
  ├── import { createCSAPIBuilder } from '@camptocamp/ogc-client/csapi'
  │
  └── createCSAPIBuilder(endpoint, collectionId)  ← FUNCTION in csapi/factory.ts
        │
        ├── await endpoint.hasConnectedSystems    ← PUBLIC getter (unchanged)
        ├── await endpoint.getCollectionDocument(collectionId)  ← NOW PUBLIC
        ├── await endpoint.root                   ← NOW PUBLIC
        │     └── scanCsapiLinks(rootDoc.links)   ← INTERNAL csapi import ✓
        └── new CSAPIQueryBuilder(doc, urls)       ← INTERNAL csapi import ✓
              │
              └── CSAPIQueryBuilder instance returned to consumer
```

**Module boundary crossings:**

- Before: 2 imports from `csapi/` INTO `endpoint.ts` (constraint violations)
- After: 0 imports from `csapi/` in `endpoint.ts`. The factory function uses `import type OgcApiEndpoint` from core (CSAPI → core, allowed direction).

---

## 7. Shared Type Import Strategy

Every type crossing the CSAPI ↔ core boundary:

| Type                                                      | Current Import                                                     | After Import                                            | Strategy                             | Constraint OK?         |
| --------------------------------------------------------- | ------------------------------------------------------------------ | ------------------------------------------------------- | ------------------------------------ | ---------------------- |
| `OgcApiCollectionInfo`                                    | `csapi/url_builder.ts`: `import type` from `../model.js`           | **Unchanged**                                           | `Pick<>` + `import type` (Level 3.5) | ✓ (erased, CSAPI→core) |
| `OgcApiDocumentLink`                                      | `csapi/model.ts`: `import type` from `../model.js`                 | **Unchanged**                                           | `import type`                        | ✓ (erased, CSAPI→core) |
| `BoundingBox`, `DateTimeParameter`, `CrsCode`, `MimeType` | `csapi/model.ts`: `import type` from `../../shared/models.js`      | **Unchanged**                                           | `import type`                        | ✓ (shared, not core)   |
| `BoundingBox`                                             | `csapi/helpers.ts`: `import type` from `../../shared/models.js`    | **Unchanged**                                           | `import type`                        | ✓ (shared, not core)   |
| `EndpointError`                                           | `csapi/url_builder.ts`: value import from `../../shared/errors.js` | **Unchanged**                                           | Value import                         | ✓ (shared, not core)   |
| `OgcApiEndpoint`                                          | N/A (not currently imported by CSAPI)                              | `csapi/factory.ts`: `import type` from `../endpoint.js` | `import type` (new)                  | ✓ (erased, CSAPI→core) |
| `OgcApiCollectionInfo`                                    | N/A                                                                | `csapi/factory.ts`: `import type` from `../model.js`    | `import type` (new)                  | ✓ (erased, CSAPI→core) |

**Key principle:** `shared/` is a utility layer, not core. CSAPI's imports from `../../shared/` don't cross the core ↔ CSAPI boundary. Plan 05 confirmed: "shared is a legitimate import target for CSAPI."

**No types need to change.** All existing `import type` statements in CSAPI are correct and should be preserved. The only new type import is `import type OgcApiEndpoint` in the factory function — erased at runtime.

---

## 8. Barrel File Design

### Question 31: Complete barrel file draft

**Answer:** The barrel file re-exports everything currently in `src/index.ts` from CSAPI modules, with paths adjusted to relative imports. It also exports the new factory function.

````typescript
// src/ogc-api/csapi/index.ts

/**
 * Connected Systems API (CSAPI) module for ogc-client.
 *
 * Provides query URL construction, format parsing, and type definitions
 * for OGC API - Connected Systems Parts 1 and 2.
 *
 * @example
 * ```ts
 * import { createCSAPIBuilder } from '@camptocamp/ogc-client/csapi';
 * import type { System, Datastream } from '@camptocamp/ogc-client/csapi';
 * ```
 *
 * @see https://docs.ogc.org/is/23-001/23-001.html
 * @see https://docs.ogc.org/is/23-002/23-002.html
 * @module
 */

// ========================================
// Factory Function
// ========================================
export { createCSAPIBuilder } from './factory.js';

// ========================================
// Query Builder (default export)
// ========================================
export { default } from './url_builder.js';
export { default as CSAPIQueryBuilder } from './url_builder.js';

// ========================================
// Model — Values
// ========================================
export {
  CSAPIResourceTypes,
  CommandStatusCodes,
  SystemTypeUris,
} from './model.js';

// ========================================
// Model — Types
// ========================================
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
  ProcedureQueryOptions,
  SamplingFeatureQueryOptions,
  PropertyQueryOptions,
  DatastreamQueryOptions,
  ObservationQueryOptions,
  ControlStreamQueryOptions,
  CommandQueryOptions,
  CommandStatusQueryOptions,
  System,
  Deployment,
  Procedure,
  SamplingFeature,
  Property,
  Datastream,
  Observation,
  ControlStream,
  Command,
  CommandStatus,
  FeatureCollection,
  ItemCollection,
  SystemCollection,
  DeploymentCollection,
  ProcedureCollection,
  SamplingFeatureCollection,
  PropertyCollection,
  DatastreamCollection,
  ObservationCollection,
  ControlStreamCollection,
  CommandCollection,
  CommandStatusCollection,
  DatastreamSchemaResponse,
  ControlStreamSchemaResponse,
} from './model.js';

// ========================================
// Format Handlers — Values
// ========================================
export {
  SOSA_NS,
  SSN_NS,
  SENSORML_NS,
  isCSAPIFeature,
  getCSAPIResourceType,
  parseValidTime,
  isValidUri,
  extractCSAPIFeature,
  parseSensorML30,
  parseSWEComponent,
  parseVector,
  parseMatrix,
  parseDataChoice,
  parseGeometry,
  detectEncoding,
  validateAgainstSchema,
  CSAPI_CONTENT_TYPES,
  getContentTypeForResource,
  parseProperty,
  parseDatastream,
  parseObservation,
  parseControlStream,
  parseCommand,
  parseCommandStatus,
  normalizeStatusCode,
  parseDatastreamSchemaResponse,
  parseControlStreamSchemaResponse,
} from './formats/index.js';

// ========================================
// Format Handlers — Types
// ========================================
export type { CSAPIResourceTypeName } from './formats/index.js';
export type {
  SensorMLProcess,
  SensorMLProcessType,
  PhysicalSystem,
  PhysicalComponent,
  SimpleProcess,
  AggregateProcess,
  DescribedObject,
  AbstractProcess,
  AbstractPhysicalProcess,
  CapabilityList,
  CharacteristicList,
  Term,
  ComponentList,
  ComponentEntry,
  ConnectionList,
  Connection,
  Settings,
  Link as SensorMLLink,
  ResponsibleParty,
  InputList,
  OutputList,
  ParameterList,
  IOComponentChoice,
  Mode,
  Event,
  Position,
  Pose,
  GeoJsonPoint,
  Document as SensorMLDocument,
  FeatureList,
  LegalConstraint,
  SecurityConstraint,
  ContactInfo,
  ContactLink,
  ObservableProperty,
  AnyProperty,
  ProcessMethod,
  SpatialFrame,
  TemporalFrame,
  TimePeriod,
  TimeInstant,
  TimeInstantOrPeriod,
  ComponentLink,
  SettingValue,
  SettingArrayValue,
  SettingMode,
  SetConstraint,
  SettingStatus,
  FrameAxis,
} from './formats/index.js';
export type {
  AnyComponent,
  AnyScalarComponent,
  AnySimpleComponent,
  DataRecord,
  Vector,
  Matrix,
  DataChoice,
  DataArray,
  SweGeometry,
  SweBoolean,
  SweCount,
  SweQuantity,
  SweText,
  SweCategory,
  SweTime,
  SweCountRange,
  SweQuantityRange,
  SweTimeRange,
  SweCategoryRange,
  DataEncoding,
  TextEncoding,
  JSONEncoding,
  BinaryEncoding,
  XMLEncoding,
  ValidationResult,
  UnitOfMeasure,
  AllowedValues,
  AllowedTokens,
  AllowedTimes,
  DataField,
  TypedDataField,
  ElementCount,
  EncodedValues,
  AssociationAttributeGroup,
  NilValue,
  NilValuesNumber,
  NilValuesInteger,
  NilValuesText,
  NilValuesTime,
  NumberOrSpecial,
  DateTimeNumberOrSpecial,
  GeometryConstraint,
  GeometryType,
  GeoJsonGeometry,
  BinaryMember,
  BinaryComponent,
  BinaryBlock,
  ValidationError,
} from './formats/index.js';
````

### Question 32: Should the barrel export CSAPI-internal utilities?

**Answer:** No — not by default. Utilities like `scanCsapiLinks`, `formatDateTimeParameter`, `encodeResourceId`, `validateLimit`, `validateBbox`, `isValidResourceType`, `assertValidResourceType` are internal implementation details. They are not exported from `src/index.ts` today. The barrel should match the current public API surface.

Exception: `scanCsapiLinks` could be useful for advanced consumers who want manual control over link scanning. This can be added later if requested, as a non-breaking change.

### Question 33: Should the barrel export the factory function?

**Answer:** Yes. `createCSAPIBuilder` is the primary consumer API for the CSAPI module after decoupling. The barrel file exports it as a named export.

### Question 34: Export organization strategy

**Answer:** Organized by source module (factory, builder, model, formats), then by kind (values first, then types). This matches the existing `src/index.ts` organization pattern and is the most readable for maintainers who need to trace where an export comes from.

### Question 35: Circular dependency check

**Answer:** No circular dependencies. The import chain from the barrel:

```
csapi/index.ts
  ├── csapi/factory.ts
  │     ├── import type ../endpoint.js      (core, no cycle)
  │     ├── import type ../model.js         (core, no cycle)
  │     ├── ../../shared/errors.js          (shared, no cycle)
  │     ├── ./url_builder.js                (internal)
  │     └── ./helpers.js                    (internal)
  ├── csapi/url_builder.ts
  │     ├── import type ../model.js         (core, no cycle)
  │     ├── ../../shared/errors.js          (shared, no cycle)
  │     └── ./helpers.js, ./model.js        (internal)
  ├── csapi/model.ts
  │     ├── import type ../../shared/models.js  (shared)
  │     └── import type ../model.js             (core)
  └── csapi/formats/index.ts
        └── (internal format modules only)
```

No module in this chain imports from `csapi/index.ts`. No cycle.

---

## 9. Test Migration Plan

### Question 36: Classification of each test

| Test                                   | Tests What                        | Location Decision               | Rationale                                                                                               |
| -------------------------------------- | --------------------------------- | ------------------------------- | ------------------------------------------------------------------------------------------------------- |
| `detects Connected Systems support`    | `hasConnectedSystems` getter      | **Stays** in `endpoint.spec.ts` | Tests endpoint behavior, not CSAPI internals. Zero CSAPI imports.                                       |
| `can list all CSAPI collections`       | `csapiCollections` getter         | **Stays** in `endpoint.spec.ts` | Tests endpoint behavior. Zero CSAPI imports.                                                            |
| `can produce a CSAPI query builder`    | `endpoint.csapi('iot-sensors')`   | **Moves + rewrites**            | Tests the factory pattern. Must use `createCSAPIBuilder` instead of `endpoint.csapi()`.                 |
| `caches the CSAPI query builder`       | `endpoint.csapi()` caching        | **Removed**                     | No automatic caching in the new design. Caching is the consumer's responsibility.                       |
| `reports no Connected Systems support` | `hasConnectedSystems` = false     | **Stays** in `endpoint.spec.ts` | Tests endpoint behavior on non-CSAPI endpoint.                                                          |
| `throws an error when calling csapi()` | `endpoint.csapi()` error handling | **Moves + rewrites**            | Tests factory function error handling. `createCSAPIBuilder` throws when endpoint doesn't support CSAPI. |

### Question 37: CSAPI test fixtures

The CSAPI tests use the `http://local/csapi/sample-data-hub` fixture URL, which maps to files in `fixtures/ogc-api/`. These fixture files are NOT specific to `endpoint.spec.ts` — they are shared test infrastructure. They stay in their current location. The migrated tests import from the same fixtures.

### Question 38: New tests needed for the CSAPI module boundary

| Test                                                                   | What It Verifies                                                                |
| ---------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| `createCSAPIBuilder creates a builder with correct availableResources` | Factory produces a builder with expected resources from the collection document |
| `createCSAPIBuilder throws on non-CSAPI endpoint`                      | Factory throws `EndpointError` when `hasConnectedSystems` is false              |
| `CSAPIQueryBuilder accepts manual construction`                        | Direct constructor still works without factory (Layer 1 API)                    |

### Question 39: Test configuration changes

**Answer:** No changes to `jest.config.cjs` or test file patterns. The migrated tests go into a CSAPI test file (e.g., `csapi/factory.spec.ts` or added to `csapi/url_builder.spec.ts`). The test file pattern `**/*.spec.ts` already matches any location.

### Question 40: Before/after for the endpoint CSAPI test block

**Before (`endpoint.spec.ts`):**

```typescript
describe('OgcApiEndpoint with CSAPI', () => {
  let endpoint: OgcApiEndpoint;
  describe('nominal case', () => {
    beforeEach(() => {
      endpoint = new OgcApiEndpoint('http://local/csapi/sample-data-hub');
    });
    it('detects Connected Systems support', async () => { ... });
    it('can list all CSAPI collections', async () => { ... });
    it('can produce a CSAPI query builder', async () => { ... });
    it('caches the CSAPI query builder', async () => { ... });
  });
  describe('non-CSAPI endpoint', () => {
    beforeEach(() => {
      endpoint = new OgcApiEndpoint('http://local/sample-data/');
    });
    it('reports no Connected Systems support', async () => { ... });
    it('throws an error when calling csapi()', async () => { ... });
  });
});
```

**After (`endpoint.spec.ts`) — 4 tests remain:**

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

**After (new `csapi/factory.spec.ts`) — 2 migrated + rewritten tests:**

```typescript
import OgcApiEndpoint from '../endpoint.js';
import { createCSAPIBuilder } from './factory.js';
import { EndpointError } from '../../shared/errors.js';

describe('createCSAPIBuilder', () => {
  it('creates a CSAPI query builder with available resources', async () => {
    const endpoint = new OgcApiEndpoint('http://local/csapi/sample-data-hub');
    const builder = await createCSAPIBuilder(endpoint, 'iot-sensors');
    expect(builder).toBeTruthy();
    expect(builder.availableResources).toEqual(
      new Set(['systems', 'deployments', 'datastreams'])
    );
  });

  it('throws on non-CSAPI endpoint', async () => {
    const endpoint = new OgcApiEndpoint('http://local/sample-data/');
    await expect(
      createCSAPIBuilder(endpoint, 'any-collection')
    ).rejects.toThrow(EndpointError);
  });
});
```

---

## 10. Before/After Code Comparison

### Question 41: `src/ogc-api/endpoint.ts` before/after

**Imports — REMOVED (lines 52–53):**

```diff
- import CSAPIQueryBuilder from './csapi/url_builder.js';
- import { scanCsapiLinks } from './csapi/helpers.js';
```

**Class field — REMOVED (line 68):**

```diff
- private collection_id_to_csapi_builder_: Map<string, CSAPIQueryBuilder> =
-   new Map();
```

**`root` getter — CHANGED (line 72):**

```diff
- private get root(): Promise<OgcApiDocument> {
+ public get root(): Promise<OgcApiDocument> {
```

**`getCollectionDocument` — CHANGED (line 438):**

```diff
- private getCollectionDocument(collectionId: string): Promise<OgcApiDocument> {
+ public getCollectionDocument(collectionId: string): Promise<OgcApiDocument> {
```

**`csapi()` method — REMOVED entirely (~lines 360–413, method + JSDoc):**

```diff
- /**
-  * Creates a {@link CSAPIQueryBuilder} for constructing Connected Systems
-  * query URLs against the given collection.
-  * ... (full JSDoc block)
-  */
- public async csapi(collectionId: string): Promise<CSAPIQueryBuilder> {
-   if (!(await this.hasConnectedSystems)) {
-     throw new EndpointError(
-       'Endpoint does not support Connected Systems'
-     );
-   }
-   const cache = this.collection_id_to_csapi_builder_;
-   if (cache.has(collectionId)) {
-     return cache.get(collectionId);
-   }
-   const collectionDoc = await this.getCollectionDocument(collectionId);
-   const resourceUrls = await this.extractRootResourceUrls();
-   const result = new CSAPIQueryBuilder(
-     collectionDoc as unknown as OgcApiCollectionInfo,
-     resourceUrls
-   );
-   cache.set(collectionId, result);
-   return result;
- }
```

**`extractRootResourceUrls` — REMOVED entirely (~lines 414–436, method + JSDoc):**

```diff
- /**
-  * Extracts absolute resource URLs from the root API document's links.
-  * ... (full JSDoc block)
-  */
- private async extractRootResourceUrls(): Promise<Map<string, string>> {
-   const rootDoc = await this.root;
-   const links = rootDoc?.links;
-   if (!Array.isArray(links)) return new Map();
-   return scanCsapiLinks(links);
- }
```

**`hasConnectedSystems` JSDoc — UPDATED (remove `@see csapi` reference):**

```diff
  * @see {@link csapiCollections} to list available collections
- * @see https://docs.ogc.org/is/23-001/23-001.html
+ * @see Import `createCSAPIBuilder` from `@camptocamp/ogc-client/csapi` to create a query builder
+ * @see https://docs.ogc.org/is/23-001/23-001.html
```

**Summary of `endpoint.ts` changes:**

- 2 imports removed
- 1 class field removed
- 2 methods removed (~60 lines including JSDoc)
- 2 visibility changes (`private` → `public`)
- 1 JSDoc update
- **Net: ~65 lines removed, 2 words changed**

### Question 42: `src/index.ts` before/after

**REMOVED — all CSAPI export lines (~lines 45–227):**

```diff
- export { default as CSAPIQueryBuilder } from './ogc-api/csapi/url_builder.js';
- export {
-   CSAPIResourceTypes,
-   CommandStatusCodes,
-   SystemTypeUris,
- } from './ogc-api/csapi/model.js';
- export type {
-   CSAPIResourceType,
-   CommandStatusCode,
-   ... (all ~170 lines of CSAPI exports)
- } from './ogc-api/csapi/formats/index.js';
```

**After:** `src/index.ts` has zero references to `csapi/`. The line `export * from './ogc-api/model.js'` (line 44) remains — it exports shared OGC API types, not CSAPI types.

### Question 43: New `src/ogc-api/csapi/index.ts` barrel file

**Complete contents:** See Section 8, Question 31 above. The barrel file is ~190 lines of re-export statements organized by category (factory, builder, model values, model types, format values, format types).

### Question 44: New `src/ogc-api/csapi/factory.ts`

**Complete contents:** See Section 3, Question 13 above. The file is ~60 lines including imports, JSDoc, and the `createCSAPIBuilder` function body.

---

## 11. Post-Refactoring Verification Checklist

| #   | Verification                               | Command / Method                                                      | Expected Result                                |
| --- | ------------------------------------------ | --------------------------------------------------------------------- | ---------------------------------------------- |
| 1   | No CSAPI imports in endpoint               | `git grep "from.*csapi" src/ogc-api/endpoint.ts`                      | 0 matches                                      |
| 2   | No CSAPI in root index                     | `git grep "csapi" src/index.ts`                                       | 0 matches                                      |
| 3   | TypeScript compiles                        | `npm run typecheck`                                                   | Exit code 0                                    |
| 4   | Browser tests pass                         | `npm run test:browser`                                                | All pass                                       |
| 5   | Node tests pass                            | `npm run test:node`                                                   | All pass                                       |
| 6   | Formatting correct                         | `npm run format:check`                                                | Exit code 0                                    |
| 7   | Linting passes                             | `npm run lint`                                                        | Exit code 0                                    |
| 8   | **Litmus test:** core builds without CSAPI | Temporarily exclude `csapi/` from tsconfig, run typecheck             | Compiles (endpoint.ts has no CSAPI references) |
| 9   | Barrel file resolves                       | `import { createCSAPIBuilder } from './csapi/index.js'`               | No resolution errors                           |
| 10  | No circular dependencies                   | Trace barrel import chain (§ 8 Q35)                                   | No cycles                                      |
| 11  | Factory function works                     | Run factory.spec.ts tests                                             | All pass                                       |
| 12  | `package.json` `"exports"` valid           | Build project, verify `dist/ogc-api/csapi/index.js` and `.d.ts` exist | Files present                                  |

---

## 12. Boundary Condition Verification Summary

Master verification across all design decisions:

| Design Decision                                 | C1: No root exports | C2: Separate entry | C3: No outward imports       | C4: One-way dep |
| ----------------------------------------------- | ------------------- | ------------------ | ---------------------------- | --------------- |
| Remove CSAPI exports from `index.ts`            | ✓ Direct            | ✓ N/A              | ✓ N/A                        | ✓ N/A           |
| Create `csapi/index.ts` barrel                  | ✓ N/A               | ✓ Direct           | ✓ N/A                        | ✓ N/A           |
| Add `"./csapi"` to `package.json` exports       | ✓ N/A               | ✓ Direct           | ✓ N/A                        | ✓ N/A           |
| Remove `CSAPIQueryBuilder` import from endpoint | ✓ N/A               | ✓ N/A              | ✓ Direct                     | ✓ Direct        |
| Remove `scanCsapiLinks` import from endpoint    | ✓ N/A               | ✓ N/A              | ✓ Direct                     | ✓ Direct        |
| Remove `csapi()` method                         | ✓ N/A               | ✓ N/A              | ✓ Enables                    | ✓ Enables       |
| Remove `extractRootResourceUrls()`              | ✓ N/A               | ✓ N/A              | ✓ Enables                    | ✓ Enables       |
| Remove `collection_id_to_csapi_builder_` cache  | ✓ N/A               | ✓ N/A              | ✓ Enables                    | ✓ Enables       |
| Keep `hasConnectedSystems` on endpoint          | ✓ Pass              | ✓ N/A              | ✓ Pass (zero csapi/ imports) | ✓ Pass          |
| Keep `csapiCollections` on endpoint             | ✓ Pass              | ✓ N/A              | ✓ Pass (zero csapi/ imports) | ✓ Pass          |
| Make `root` public                              | ✓ N/A               | ✓ N/A              | ✓ N/A (no import change)     | ✓ N/A           |
| Make `getCollectionDocument` public             | ✓ N/A               | ✓ N/A              | ✓ N/A (no import change)     | ✓ N/A           |
| Create `createCSAPIBuilder` factory             | ✓ N/A               | ✓ In barrel        | ✓ N/A (lives in CSAPI)       | ✓ CSAPI→core    |
| Factory uses `import type OgcApiEndpoint`       | ✓ N/A               | ✓ N/A              | ✓ N/A (CSAPI→core)           | ✓ Erased        |
| Factory uses `scanCsapiLinks`                   | ✓ N/A               | ✓ N/A              | ✓ Internal CSAPI             | ✓ Internal      |
| Add `"sideEffects": false` to package.json      | ✓ N/A               | ✓ Supports         | ✓ N/A                        | ✓ N/A           |

**All 16 design decisions pass all 4 boundary conditions.**

---

## 13. Impact on Plan 08

### What Plan 08 Should Consume

| Item                                                                                                                                                             | Section Reference     |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------- |
| **Complete file list:** `endpoint.ts`, `index.ts`, `package.json`, new `csapi/index.ts`, new `csapi/factory.ts`, `endpoint.spec.ts`, new `csapi/factory.spec.ts` | §§ 10, 8, 9           |
| **Exact changes per file:** Before/after diffs for endpoint.ts (§ 10 Q41), index.ts (§ 10 Q42), barrel file contents (§ 8 Q31), factory file contents (§ 3 Q13)  | §§ 10, 8, 3           |
| **Test migration plan:** 4 stay, 2 move+rewrite, 1 removed, before/after test code                                                                               | § 9 Q36–Q40           |
| **package.json changes:** `"./csapi"` sub-path + `"sideEffects": false`                                                                                          | § 2 Q3 (from Plan 03) |
| **Verification checklist:** 12-item post-refactoring verification                                                                                                | § 11                  |

### Decisions Now Final

1. **Consumer API:** `createCSAPIBuilder(endpoint, collectionId)` from `@camptocamp/ogc-client/csapi`
2. **Coupling Level:** Level 3.5 — no change to `CSAPIQueryBuilder` constructor
3. **`hasConnectedSystems` + `csapiCollections`:** Stay on endpoint
4. **`csapi()` + `extractRootResourceUrls()` + cache:** Removed from endpoint
5. **`scanCsapiLinks`:** Stays in `csapi/helpers.ts` unchanged — no generalization needed
6. **`getCollectionDocument` + `root`:** Changed to public
7. **Barrel file:** Complete draft in § 8 Q31
8. **Factory file:** Complete draft in § 3 Q13
9. **Test migration:** 4 stay / 2 move / 1 removed
10. **Scope gate verified:** Every decision passes minimum-change test

### Items Deferred (NOT blocking Plan 08)

1. **ESLint `import/no-restricted-paths` boundary rule:** Low cost, high value, but not required for the PR. Can be added in a follow-up.
2. **Boundary integration test** (`__tests__/boundary.spec.ts`): Useful but not strictly required for the refactoring.
3. **`typesVersions` fallback:** Not needed per Plan 03 (5/6 libraries skip it).
4. **Compile-time drift assertion test:** Unnecessary at Level 3.5 — `Pick<>` provides native drift detection.

---

## 14. Open Questions

| #   | Question                                                                                  | Status                                              | Resolution                                                                                                                                                                                                                                                                                                                                                                  |
| --- | ----------------------------------------------------------------------------------------- | --------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | Will jahow accept `hasConnectedSystems` and `csapiCollections` staying on the endpoint?   | **Resolved as "likely yes"**                        | These properties follow the identical pattern as `hasEnvironmentalDataRetrieval` and `edrCollections`, with zero CSAPI imports. The argument is strong (§ 4 Q15–Q16). If jahow objects, the fallback is moving them to the CSAPI module as standalone functions accepting conformance classes / collection data.                                                            |
| 2   | Will jahow accept the two new public methods (`root`, `getCollectionDocument`)?           | **Resolved as "reasonable"**                        | Both expose data the endpoint already computes internally. `getCollectionDocument` is used by styles. `root` complements the existing `info` getter. These are useful general-purpose additions. If jahow objects, the alternative is to have the factory function fetch the root document independently (redundant HTTP possible, but `sharedFetch` caching may mitigate). |
| 3   | Naming: `createCSAPIBuilder` vs `csapi` vs `buildCSAPI`?                                  | **Resolved as `createCSAPIBuilder`**                | Matches the class name `CSAPIQueryBuilder`, follows the `create*` factory naming convention seen in React (createContext), AWS SDK patterns (createMultipartUpload), and is explicit about what it returns.                                                                                                                                                                 |
| 4   | Should the factory function parameter be typed as `OgcApiEndpoint` or a narrow interface? | **Resolved as `OgcApiEndpoint` with `import type`** | Minimum change per scope gate. The `import type` is erased at runtime. Tests can use `as unknown as OgcApiEndpoint` for mocking. A narrow interface can be introduced later if needed.                                                                                                                                                                                      |
| 5   | Is `shared/` considered "core" for constraint purposes?                                   | **Resolved as NO**                                  | `shared/` is a utility layer (`errors.js`, `models.js`, `http-utils.js`, `cache.js`). It is not part of `ogc-api/` core. CSAPI's value import of `EndpointError` from `../../shared/errors.js` is acceptable.                                                                                                                                                               |

**No unresolved questions remain.**

---

## Implementation Scope Gate Assessment

### Minimum-Change Test

| Design Decision                                  | Serves jahow's requirements?                    | Minimum-change?      | Included? |
| ------------------------------------------------ | ----------------------------------------------- | -------------------- | --------- |
| Remove CSAPI exports from `index.ts`             | Yes — directly required                         | Yes                  | ✓         |
| Create barrel file `csapi/index.ts`              | Yes — required for `./csapi` entry              | Yes                  | ✓         |
| Add `"./csapi"` to `package.json` exports        | Yes — directly required                         | Yes                  | ✓         |
| Remove 2 CSAPI imports from `endpoint.ts`        | Yes — directly required                         | Yes                  | ✓         |
| Remove `csapi()` method from endpoint            | Yes — enables import removal                    | Yes                  | ✓         |
| Remove `extractRootResourceUrls()` from endpoint | Yes — enables import removal                    | Yes                  | ✓         |
| Remove CSAPI cache from endpoint                 | Yes — consequence of method removal             | Yes                  | ✓         |
| Create `createCSAPIBuilder` factory              | Yes — minimum replacement for removed `csapi()` | Yes — 1 new function | ✓         |
| Make `getCollectionDocument` public              | Yes — factory needs it                          | Yes — 1 word         | ✓         |
| Make `root` public                               | Yes — factory needs it                          | Yes — 1 word         | ✓         |
| Keep `hasConnectedSystems` on endpoint           | Yes — follows EDR pattern, zero CSAPI imports   | Yes — no change      | ✓         |
| Keep `csapiCollections` on endpoint              | Yes — follows EDR pattern, zero CSAPI imports   | Yes — no change      | ✓         |
| Add `"sideEffects": false`                       | Yes — enables tree-shaking per Plan 03          | Yes — 1 line         | ✓         |
| Generalize `scanCsapiLinks` (Plan 05 Option C)   | **Not needed** — problem self-resolves          | **N/A**              | ✗ Skip    |
| ESLint boundary rule                             | No — enforcement, not requirement               | No — tooling         | ✗ Defer   |
| Boundary integration test                        | No — enforcement, not requirement               | Borderline           | ✗ Defer   |
| TypeScript Project References                    | No — architectural improvement                  | No — heavy refactor  | ✗ Defer   |

---

## Key Takeaways

1. **The simplest solution was always available.** Remove `csapi()` and `extractRootResourceUrls()` from the endpoint → both CSAPI imports become unused → delete them. No shared utilities, no generalization, no code duplication. The problem was never about `scanCsapiLinks` placement — it was about who orchestrates the data flow.

2. **The factory function serves triple duty.** (a) Consumer API replacement for `endpoint.csapi()`, (b) Architectural decoupling mechanism (moves CSAPI creation from core to CSAPI module), (c) Encapsulates the type assertion and link scanning complexity from consumers.

3. **`hasConnectedSystems` and `csapiCollections` are safe.** They follow the identical pattern as their EDR equivalents, with zero imports from `csapi/`. The import graph proves this. They provide discovery without crossing the module boundary.

4. **Two 1-word changes enable the entire decoupling.** Making `root` and `getCollectionDocument` public on `OgcApiEndpoint` is the entire scope of changes to core's public API surface. Everything else is removal.

5. **Level 3.5 coupling is already optimal.** No change to `CSAPIQueryBuilder`'s constructor signature. The `Pick<>` + `import type` pattern provides drift detection with zero runtime coupling. Plans 04 and 05 both confirmed this.

6. **Plan 05's `scanCsapiLinks` generalization is unnecessary.** This is the most significant override of a prior plan's recommendation. The problem self-resolves when the endpoint stops orchestrating CSAPI creation. The generalization would have been needed only if the endpoint continued to scan links — which it doesn't.

7. **Net code change is small.** ~65 lines removed from `endpoint.ts`, ~170 lines removed from `index.ts`, ~250 lines added across `csapi/index.ts` (barrel, ~190 lines) and `csapi/factory.ts` (~60 lines). The total footprint is roughly neutral, with all new code in the CSAPI module.

8. **One-shot extraction confirmed.** The coupling surface is small (2 imports + ~170 export lines), there are no external consumers of the current deep import paths, and the test migration is straightforward. No staged migration, strangler fig, or intermediate layers needed.

9. **All 44 questions answered, all 4 constraints satisfied, all 16 design decisions verified.** This design is implementation-ready with no unresolved questions.

10. **The scope gate held.** No unnecessary abstractions, no adapter interfaces, no generalized utilities, no plugin systems. Every change directly serves jahow's two requirements. The design is the minimum viable decoupling.

---

## Evidence Appendix

### A. Complete Import Graph After Refactoring

**Core (`endpoint.ts`) imports:**

```
endpoint.ts
  ├── ./info.js                      (core internal)
  ├── ./model.js                     (core internal)
  ├── ./link-utils.js                (core internal)
  ├── ../shared/errors.js            (shared utility)
  ├── ../shared/models.js            (shared utility)
  ├── ../shared/mime-type.js         (shared utility)
  ├── ../shared/url-utils.js         (shared utility)
  └── ./edr/url_builder.js           (EDR — accepted pattern)

  ✗ NO imports from ./csapi/*
```

**CSAPI (`factory.ts`) imports:**

```
csapi/factory.ts
  ├── import type ../endpoint.js     (core → type-only, erased)
  ├── import type ../model.js        (core → type-only, erased)
  ├── ../../shared/errors.js         (shared utility → value)
  ├── ./url_builder.js               (CSAPI internal → value)
  └── ./helpers.js                   (CSAPI internal → value)
```

**CSAPI (`url_builder.ts`) imports — UNCHANGED:**

```
csapi/url_builder.ts
  ├── import type ../model.js        (core → type-only, erased)
  ├── ../../shared/errors.js         (shared utility → value)
  ├── ./model.js                     (CSAPI internal)
  └── ./helpers.js                   (CSAPI internal)
```

**Direction verification:**

- Core → CSAPI: **0 imports** ✓
- CSAPI → Core: 2 `import type` (erased) + 0 value imports ✓
- CSAPI → Shared: 2 value imports (acceptable) ✓

### B. Complete File Change Summary

| File                                | Action                                                                            | Lines Changed                      |
| ----------------------------------- | --------------------------------------------------------------------------------- | ---------------------------------- |
| `src/ogc-api/endpoint.ts`           | Edit: remove 2 imports, 1 field, 2 methods; change 2 visibilities; update 1 JSDoc | ~65 lines removed, 2 words changed |
| `src/index.ts`                      | Edit: remove all CSAPI export lines                                               | ~170 lines removed                 |
| `src/ogc-api/csapi/index.ts`        | **New file**: barrel with all CSAPI exports                                       | ~190 lines added                   |
| `src/ogc-api/csapi/factory.ts`      | **New file**: `createCSAPIBuilder` function                                       | ~60 lines added                    |
| `src/ogc-api/csapi/factory.spec.ts` | **New file**: factory tests                                                       | ~30 lines added                    |
| `src/ogc-api/endpoint.spec.ts`      | Edit: remove 2 tests, trim describe blocks                                        | ~20 lines removed                  |
| `package.json`                      | Edit: add `"./csapi"` sub-path, add `"sideEffects": false`                        | ~8 lines added                     |

**Net: ~255 lines removed, ~288 lines added. Roughly neutral.**

### C. jahow's Requirements Traceability

| jahow Requirement (PR #136)                                                                     | Design Decision                                                                      | Status      |
| ----------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------ | ----------- |
| "anything part of `src/ogc-api/csapi` should not be included in the root `index.ts` file"       | Remove all CSAPI exports from `src/index.ts` (§ 10 Q42)                              | ✓ Satisfied |
| "imported through `@camptocamp/ogc-client/csapi`"                                               | Create `csapi/index.ts` barrel + `"./csapi"` in `package.json` exports (§ 8, § 2 Q3) | ✓ Satisfied |
| "anything not part of `src/ogc-api/csapi` should not import things from the CSAPI code at all"  | Remove 2 CSAPI imports from `endpoint.ts` (§ 10 Q41)                                 | ✓ Satisfied |
| "anyone using the library as before do not end up with all this code in their bundle overnight" | `"sideEffects": false` + separate entry point ensures tree-shaking                   | ✓ Satisfied |

---

## Research Completion Checklist

- [x] All 44 detailed questions from the research plan have specific, evidenced answers
- [x] Findings respect all boundary conditions listed in the research plan § 3
- [x] Prior findings from Plans 02–05 are synthesized with explicit conflict resolution (§ 2)
- [x] Consumer API is fully specified — exact TypeScript signature, JSDoc, before/after (§ 3 Q10, Q13)
- [x] Every integration point has a concrete placement decision with before/after code (§ 4, 5, 6, 10)
- [x] `scanCsapiLinks` placement resolved — stays in CSAPI, no generalization needed (§ 5 Q21–Q23)
- [x] `hasConnectedSystems` and `csapiCollections` placement resolved with constraint verification (§ 4 Q15–Q16)
- [x] `getCollectionDocument` visibility decision made and documented (§ 6 Q26–Q27)
- [x] Complete barrel file drafted with every exported symbol (§ 8 Q31)
- [x] Data flow diagram produced — before and after (§ 6 Q30)
- [x] All 6 CSAPI tests classified with migration plan (§ 9 Q36)
- [x] Post-refactoring verification checklist complete (§ 11)
- [x] Litmus test verified: removing `csapi/` leaves core functional (§ 11 #8)
- [x] Implementation scope gate applied — every decision passes minimum-change test
- [x] Cross-referenced with Plan 08 — all needed information provided (§ 13)
- [x] Boundary condition verification summary produced (§ 12)

**Research Started:** 2026-02-24
**Research Completed:** 2026-02-24
**Reviewed:** Not yet

---

## Notes

- **The simplest solution insight (§ Key Takeaway #1)** emerged only during the synthesis phase when simultaneously considering the `csapi()` method removal and the `scanCsapiLinks` placement. Plan 05's analysis was correct in isolation (the endpoint needs a way to scan links), but it did not account for the possibility of removing the scanning entirely from the endpoint. This is why the design synthesis plan exists — individual research plans optimize locally, but the synthesis can see the global optimum.

- **The factory function typing** uses `import type OgcApiEndpoint` rather than a narrow interface per the scope gate. If tests prove difficult to write with the concrete class type, a narrow `CSAPIEndpointLike` interface can be introduced later as a non-breaking change.

- **No backward-compatible path for `endpoint.csapi()`.** The method is removed, not deprecated. Consumers must update to `createCSAPIBuilder()`. This is acceptable because the CSAPI module has not been published to npm yet (the PR has never been merged), so there are no external consumers to migrate.

- **The `as unknown as OgcApiCollectionInfo` type assertion** in the factory function is a pragmatic choice. The raw collection document has the same shape as `OgcApiCollectionInfo` at runtime (it's the source data that gets parsed into that type), but TypeScript's type system sees them as different types. The assertion is safe because the `CSAPIQueryBuilder` only accesses `id`, `title`, and `links` — all present on raw collection documents per the OGC API standard.
