# Phase 8: API Design Refinements & Server-Interop — Implementation Guide

**Version:** 1.0
**Date:** April 29, 2026
**Status:** Ready for execution
**Scope:** API surface refinement + 2 server-interop bug fixes; **zero CSAPI parsing logic and zero URL construction logic changes**

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Architecture Context](#2-architecture-context)
3. [Design Principles & Decisions Already Locked](#3-design-principles--decisions-already-locked)
4. [Workstream 1 — Review #2 API Refinements](#4-workstream-1--review-2-api-refinements)
   - 4.1 [Finding 017 — URL-Builder Framing in Module Docs](#41-finding-017--url-builder-framing-in-module-docs)
   - 4.2 [Finding 019 — `DataStream` → `Datastream` Method Rename](#42-finding-019--datastream--datastream-method-rename)
   - 4.3 [Finding 022 — Constructor Exposes `OgcApiCollectionInfo` Type](#43-finding-022--constructor-exposes-ogcapicollectioninfo-type)
   - 4.4 [Finding 023 — `availableResources` Type Tightening](#44-finding-023--availableresources-type-tightening)
   - 4.5 [Finding 021 — Validators Throw Plain `Error`](#45-finding-021--validators-throw-plain-error)
   - 4.6 [Findings 018 + 024 (Coordinated) — `endpoint.csapi()` and Re-Privatization](#46-findings-018--024-coordinated--endpointcsapi-and-re-privatization)
5. [Workstream 2 — Server-Interop Bug Fixes](#5-workstream-2--server-interop-bug-fixes)
   - 5.1 [Issue #166 — Part 2 `@link` Fallback in Cross-Reference Fields](#51-issue-166--part-2-link-fallback-in-cross-reference-fields)
   - 5.2 [Issue #167 — Pagination-Contract JSDoc on List Methods](#52-issue-167--pagination-contract-jsdoc-on-list-methods)
6. [Workstream 3 — Already-Shipped Triage Outputs (Recap)](#6-workstream-3--already-shipped-triage-outputs-recap)
7. [Cross-Cutting Concerns](#7-cross-cutting-concerns)
   - 7.1 [Test Update Pattern](#71-test-update-pattern)
   - 7.2 [Order of Operations Within a Single Sitting](#72-order-of-operations-within-a-single-sitting)
   - 7.3 [`@deprecated` Tag Policy](#73-deprecated-tag-policy)
8. [Verification Plan](#8-verification-plan)
9. [Risk Register](#9-risk-register)
10. [Scope Boundaries — What Does NOT Change](#10-scope-boundaries--what-does-not-change)
11. [Two-Repo Delivery Sequence](#11-two-repo-delivery-sequence)
12. [References](#12-references)

---

## 1. Executive Summary

Phase 8 closes two bodies of work in a single phase, ships the result as one squashed commit appended to `OS4CSAPI/ogc-client`'s `clean-pr` branch, and refreshes [PR #136](https://github.com/camptocamp/ogc-client/pull/136) for upstream maintainer [@jahow](https://github.com/jahow)'s final review.

**Two bodies of work:**

1. **Senior developer's second code review (API design pass).** 10 findings, triaged in [P8-triage.md](P8-triage.md) into 7 accepted (017, 018, 019, 021, 022, 023, 024) + 3 deferred (020, 025, 026). Each accepted finding has a numbered MD under [`docs/code-review/`](../../code-review/) carrying the authoritative "why" and per-finding option analysis.

2. **CS-Go integration testing.** Live validation against the [`connected-systems-go`](https://github.com/OS4CSAPI/connected-systems-go) server — a third independent CSAPI implementation exercised through [`ogc-csapi-explorer`](https://github.com/OS4CSAPI/ogc-csapi-explorer) — surfaced 6 issues. Triage decisions (Phase 8 work):
   - **#166** (P1) — Part 2 parsers missing `@link` fallback. **Accept, fix this phase.**
   - **#167** (P3) — List methods don't document pagination contract. **Accept, fix this phase.**
   - **#168** — `getLatestObservationUrls()` shim. **Closed wontfix; library is spec-correct; server-side gap tracked at [`connected-systems-go#11`](https://github.com/OS4CSAPI/connected-systems-go/issues/11).**
   - **#169** — Heuristic coordinate extraction. **Closed wontfix; architecturally wrong; correct path tracked at #171.**
   - **#170** — Async-iterator pagination helpers. **Filed deferred** alongside finding 026.
   - **#171** — SWE Common-aware result extraction. **Filed deferred.**

**Volume estimate (source/fixture only — flows to `clean-pr`):**

| Category                                      | Source LOC | Test LOC |
| --------------------------------------------- | ---------- | -------- |
| Workstream 1 — API refinements                | ~250       | ~300     |
| Workstream 2 — bug fixes (#166 + #167)        | ~150       | ~250     |
| Workstream 3 — already-shipped triage outputs | 0          | 0        |
| **Total**                                     | **~400**   | **~550** |

**Volume estimate (planning + research artifacts — `phase-8` only, does NOT flow to `clean-pr`):**

- This guide + [P8-contribution-goal-and-definition.md](P8-contribution-goal-and-definition.md) + [P8-ROADMAP.md](P8-ROADMAP.md) + [P8-triage.md](P8-triage.md) + the 7 accepted-finding MDs (017, 018, 019, 021, 022, 023, 024) + [`docs/research/references.md`](../../research/references.md) updates already shipped in commits [`3878577`](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/commit/3878577) and [`a3424a8`](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/commit/a3424a8).

**Relationship to prior guides:**

- [P5-parser-completion-implementation-guide.md](../phase-5/P5-parser-completion-implementation-guide.md) — Phase 5 parser work; structural template for the per-finding execution sections in this guide.
- [P6-implementation-guide.md](../phase-6/P6-implementation-guide.md) — Phase 6 upstream-acceptance module-boundary refactor; closest structural parallel to Phase 8 (external review-driven, two-repo workflow standardized, public-API-surface focused).
- Phase 7 broke the trio doc pattern; Phase 8 restores it.

---

## 2. Architecture Context

### Current state (after Phase 7, on `clean-pr` HEAD)

The CSAPI module on `clean-pr` is **functionally complete and behaviorally correct for two of three known-good servers** (OpenSensorHub, Toolbox4OGC). Phase 7 cleared the senior dev's first review (17 type-safety / DRY / security findings, see [`docs/code-review/`](../../code-review/) entries 003–016 + `upstream-findings-report.md`).

Three issues remain visible to a discerning consumer:

```
┌──────────────────────────────────────────────────────────────────────┐
│ src/ogc-api/endpoint.ts                                               │
│   public get root(): Promise<OgcApiDocument>            ❌ Phase-6     │
│                                                            promotion │
│   public getCollectionDocument(id): Promise<OgcApiDocument> ❌        │
│   (no `csapi(id)` method — asymmetry vs. EDR's `endpoint.edr(id)`)  │
└──────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────────┐
│ src/ogc-api/csapi/factory.ts                                          │
│   await endpoint.root              ← needs the public promotion       │
│   await endpoint.getCollectionDocument(id) ← also needs it            │
│   if (!isCollectionInfo(doc)) throw new EndpointError(...)            │
│       └─ unsound runtime cast (mirrors upstream finding 003)          │
└──────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────────┐
│ src/ogc-api/csapi/url_builder.ts                                      │
│   constructor(collection_: Pick<OgcApiCollectionInfo, ...>) ❌ leaks   │
│   public readonly availableResources: Set<string>           ❌ loose  │
│   13 methods named *DataStream*  vs.  Datastream type/parser ❌ split │
│   throw new Error('limit must be ...')                       ❌ plain │
└──────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────────┐
│ src/ogc-api/csapi/formats/part2.ts                                    │
│   systemId only extracted from `system@id` (scalar)          ❌ #166  │
│   `system@link.href` form silently dropped                            │
│   datastream@id, foi@id, samplingFeature@id, controlstream@id,        │
│   command@id — same problem in 4 more parsers                         │
└──────────────────────────────────────────────────────────────────────┘
```

### Target state (after Phase 8, on `clean-pr` after squashed commit)

```
┌──────────────────────────────────────────────────────────────────────┐
│ src/ogc-api/endpoint.ts                                               │
│   private get root()                                       ✅ A7      │
│   private getCollectionDocument(id)                         ✅ A7      │
│   public async csapi(collectionId): Promise<CSAPIQueryBuilder> ✅ A2 │
│     └─ uses getCollectionInfo() + private root +                      │
│        dynamic import('./csapi/factory.js')                           │
└──────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────────┐
│ src/ogc-api/csapi/factory.ts                                          │
│   createCSAPIBuilder(collection, resourceUrls) ← value-shaped, pure │
│   try { ... } catch (e) { wrap as EndpointError }      ✅ A4         │
│   isCollectionInfo cast removed (unreachable)              ✅ A8      │
└──────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────────┐
│ src/ogc-api/csapi/model.ts                                            │
│   export interface CSAPICollectionRef { id; title?; links }  ✅ A5   │
│   export type CSAPIResourceType = 'systems' | ...           (existing)│
└──────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────────┐
│ src/ogc-api/csapi/url_builder.ts                                      │
│   /** Module JSDoc: this builder produces URLs ... */       ✅ A1     │
│   constructor(collection_: CSAPICollectionRef, ...)         ✅ A5     │
│   public readonly availableResources: ReadonlySet<CSAPIResourceType> │
│                                                              ✅ A6    │
│   13 methods renamed *DataStream* → *Datastream*            ✅ A3     │
│   throw new EndpointError('limit must be ...')              ✅ A4     │
│   /** @remarks Pagination: server picks default limit, ...*/ ✅ B2  │
└──────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────────┐
│ src/ogc-api/csapi/formats/part2.ts                                    │
│   systemId extracted from system@id OR system@link.href     ✅ B1    │
│   (same fallback in datastream@*, foi@*, samplingFeature@*,           │
│    controlstream@*, command@*)                                        │
└──────────────────────────────────────────────────────────────────────┘
```

### What stays untouched

`csapi/formats/geojson.ts`, `csapi/formats/property.ts`, `csapi/formats/schema-response.ts`, `csapi/formats/swecommon/*`, `csapi/command-routing.ts`, `csapi/helpers.ts` (except for `EndpointError` swap in `validateLimit` / `validateBbox` / `formatDateTimeParameter`), `csapi/integration/*`, all SensorML parsers, all Part 1 GeoJSON parsing — **zero behavioral change**.

---

## 3. Design Principles & Decisions Already Locked

These are the rails Phase 8 runs on. Each was settled before this guide was drafted; none is up for re-litigation during execution.

| #   | Decision                                                                                                 | Locked when    | Authoritative source                                                                                        |
| --- | -------------------------------------------------------------------------------------------------------- | -------------- | ----------------------------------------------------------------------------------------------------------- |
| 1   | **Finding 019: straight rename, no aliases, no `@deprecated` tags** (PR #136 unmerged → no consumers)    | April 28, 2026 | [019](../../code-review/019-pending-p2-method-naming-datastream-vs-datastream.md) "Decision"                |
| 2   | **Finding 024: Option A3 — re-privatize and compose via `endpoint.csapi()`** (preserves Issue #122)      | April 28, 2026 | [024](../../code-review/024-pending-p2-endpoint-root-publicly-exposed.md) "Decision"                        |
| 3   | **Finding 021: `EndpointError` only — no `CSAPIError extends EndpointError` subclass**                   | April 29, 2026 | [021](../../code-review/021-pending-p2-validators-throw-plain-error.md) "Decision (locked)"                 |
| 4   | **#168 wontfix:** library is spec-correct per OGC 23-002 §13.3.2 D; ergonomic helper rejected            | April 29, 2026 | [#168](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/168) status banner                             |
| 5   | **#169 wontfix:** heuristic coordinate extraction architecturally wrong; SWE Common path tracked at #171 | April 29, 2026 | [#169](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/169) status banner; 7-point list               |
| 6   | **Two-repo workflow** identical to Phase 7: `phase-8` dev → source-only patch → squash onto `clean-pr`   | Phase 7        | [P7-code-review-cleanup-plan.md](../phase-7/P7-code-review-cleanup-plan.md)                                 |
| 7   | **Hard scope fence:** no consumer-side ergonomic helpers absorbed into the library                       | Phase 8 triage | [P8-contribution-goal-and-definition.md](P8-contribution-goal-and-definition.md) §"What Stays Out of Scope" |

> **If something on the list above feels wrong during execution, stop and surface it — do not silently re-decide.** Per [`docs/governance/AI_OPERATIONAL_CONSTRAINTS.md`](../../governance/AI_OPERATIONAL_CONSTRAINTS.md).

---

## 4. Workstream 1 — Review #2 API Refinements

The 7 accepted findings group naturally into 4 buckets by execution risk and file footprint. The recommended sitting order (smallest blast radius first) is **017 → 019 → 022 → 023 → 021 → 018+024**. Each section below is self-contained but defers the deep "why" to its finding MD.

### 4.1 Finding 017 — URL-Builder Framing in Module Docs

> **Authoritative source:** [017-pending-p3-docs-url-builder-framing.md](../../code-review/017-pending-p3-docs-url-builder-framing.md)

**Goal (acceptance criterion A1):** A consumer reading either `csapi/index.ts`'s module docblock, `createCSAPIBuilder`'s JSDoc, or the README cannot miss that `CSAPIQueryBuilder` returns URL strings and the consumer owns every `fetch()` call.

**Files modified:**

- `src/ogc-api/csapi/index.ts` — module docblock at top
- `src/ogc-api/csapi/factory.ts` — `createCSAPIBuilder` JSDoc cross-references the module docblock
- `src/ogc-api/csapi/url_builder.ts` — class-level JSDoc on `CSAPIQueryBuilder` reinforces the framing
- `README.md` — new "Connected Systems — making a request" section with the 5-step worked example

**Module docblock template (`csapi/index.ts`):**

````ts
/**
 * OGC API — Connected Systems (Parts 1 & 2) URL builder and response parsers.
 *
 * **What this module is:** a URL builder + response parser for the
 * [OGC API — Connected Systems](https://docs.ogc.org/is/23-002/23-002.html)
 * standards Part 1 (Sensor Discovery) and Part 2 (Streams & Tasking).
 *
 * **What this module is NOT:** an HTTP client. `CSAPIQueryBuilder.get*()`
 * methods return URL strings. The consumer is responsible for every
 * `fetch()` call (auth headers, timeouts, retries, abort, error handling).
 *
 * Mirrors the design of {@link EDRQueryBuilder} from
 * `@camptocamp/ogc-client/edr` — same pattern, same rationale.
 *
 * ```ts
 * import { OgcApiEndpoint } from '@camptocamp/ogc-client';
 * import { parseCollectionResponse, parseDatastream } from '@camptocamp/ogc-client/csapi';
 *
 * const endpoint = new OgcApiEndpoint('https://api.example.com');
 * const builder = await endpoint.csapi('weather-stations');
 * const url = builder.getDatastreams({ limit: 10 });
 * const response = await fetch(url, { headers: { Authorization: 'Bearer ...' } });
 * const result = parseCollectionResponse(await response.json(), parseDatastream);
 * ```
 *
 * @module
 */
````

**README section sketch (markdown):** one fenced block with the 5-step example above, one paragraph explaining the URL-builder pattern, one cross-link to `EDRQueryBuilder` for symmetry.

**Test impact:** none. Docs only.

**Effort:** Small (docs only). **Risk:** None.

---

### 4.2 Finding 019 — `DataStream` → `Datastream` Method Rename

> **Authoritative source:** [019-pending-p2-method-naming-datastream-vs-datastream.md](../../code-review/019-pending-p2-method-naming-datastream-vs-datastream.md) — Option A locked

**Goal (acceptance criterion A3):** Single coherent spelling everywhere. `git grep "DataStream" -- src/ogc-api/csapi/url_builder.ts` returns 0 matches except the `@module` JSDoc note (if any). Method names match the existing `Datastream` type, `parseDatastream` parser, and `'datastreams'` resource constant.

**13 methods to rename:**

| Old name                    | New name                    |
| --------------------------- | --------------------------- |
| `getDataStreams`            | `getDatastreams`            |
| `getDataStream`             | `getDatastream`             |
| `createDataStream`          | `createDatastream`          |
| `updateDataStream`          | `updateDatastream`          |
| `deleteDataStream`          | `deleteDatastream`          |
| `getDataStreamSchema`       | `getDatastreamSchema`       |
| `getDataStreamObservations` | `getDatastreamObservations` |
| `getDataStreamSystems`      | `getDatastreamSystems`      |
| `getDataStreamProcedures`   | `getDatastreamProcedures`   |
| `getDataStreamHistory`      | `getDatastreamHistory`      |
| `getSystemDataStreams`      | `getSystemDatastreams`      |
| `createDataStreamForSystem` | `createDatastreamForSystem` |
| `getProcedureDataStreams`   | `getProcedureDatastreams`   |

**Files modified:**

- `src/ogc-api/csapi/url_builder.ts` — declarations and any internal `this.*` calls
- `src/ogc-api/csapi/url_builder.spec.ts` — every test case
- `src/ogc-api/csapi/integration/*.spec.ts` — any integration tests that call these
- `src/ogc-api/csapi/factory.spec.ts` — if it references method names
- `src/ogc-api/csapi/index.ts` — re-exports if any names appear in barrel
- `app/Demo.vue` — demo app references (under our control)
- `app/examples/edr.ts` — only if it references CSAPI methods (unlikely; check)

**Mechanical execution:**

1. In `url_builder.ts`, rename declarations one at a time using VS Code's rename-symbol (F2). Each rename auto-updates internal call sites.
2. After all 13 renames complete, run `git grep -n "DataStream" -- 'src/ogc-api/csapi/'` — expect zero matches.
3. Run `npx tsc --noEmit` — fix any consumer call sites the rename-symbol missed.
4. Run `npm run test:browser src/ogc-api/csapi/url_builder.spec.ts` — fix any test references.

**Test impact:** ~13 spec describe blocks renamed; method invocations in test bodies updated. No new test cases needed for the rename itself.

**No alias layer, no `@deprecated` tags.** Per locked decision: PR #136 unmerged ⇒ no consumers ⇒ "breaking change" framing does not apply. Adding deprecated aliases creates permanent cruft for users that don't exist.

**Effort:** Mechanical, ~1 hour. **Risk:** Low (rename-symbol + tsc gates catch every call site).

---

### 4.3 Finding 022 — Constructor Exposes `OgcApiCollectionInfo` Type

> **Authoritative source:** [022-pending-p3-constructor-exposes-collection-info-type.md](../../code-review/022-pending-p3-constructor-exposes-collection-info-type.md)

**Goal (acceptance criterion A5):** `CSAPIQueryBuilder`'s constructor parameter type lives in `csapi/model.ts` and references no upstream-internal types. Refactoring `OgcApiCollectionInfo` upstream cannot become a breaking change to the CSAPI public API.

**New type in `src/ogc-api/csapi/model.ts`:**

```ts
/**
 * Minimal collection descriptor required to construct a {@link CSAPIQueryBuilder}.
 *
 * Structurally compatible with {@link OgcApiCollectionInfo} but defined
 * locally so that the CSAPI module's public API does not depend on the
 * upstream OGC API collection-info type.
 *
 * @public
 */
export interface CSAPICollectionRef {
  /** Stable collection identifier. */
  id: string;
  /** Optional human-readable title. */
  title?: string;
  /** Resource links discovered from the collection document. */
  links: ResourceLink[];
}
```

**Modification to `src/ogc-api/csapi/url_builder.ts`:**

```diff
-import type { OgcApiCollectionInfo } from '../model.js';
+import type { CSAPICollectionRef } from './model.js';

 export class CSAPIQueryBuilder {
   constructor(
-    private collection_: Pick<OgcApiCollectionInfo, 'id' | 'title' | 'links'>,
+    private collection_: CSAPICollectionRef,
     resourceUrls?: Map<string, string>
   ) { ... }
 }
```

**Modification to `src/ogc-api/csapi/factory.ts`:**

The factory's signature change (Section 4.6) already covers this — it will accept `CSAPICollectionRef` directly.

**Export from barrel:**

```diff
 // src/ogc-api/csapi/index.ts
+export type { CSAPICollectionRef } from './model.js';
```

**Test impact:** `url_builder.spec.ts` and `factory.spec.ts` — wherever a fake `OgcApiCollectionInfo` `Pick<>` literal is constructed, change the type assertion to `CSAPICollectionRef`. Bodies stay identical (structural typing makes the swap invisible at runtime).

**Effort:** Trivial. **Risk:** None (structural compatibility; `Pick<>` was already a subset of the new shape).

---

### 4.4 Finding 023 — `availableResources` Type Tightening

> **Authoritative source:** [023-pending-p3-availableresources-set-typing.md](../../code-review/023-pending-p3-availableresources-set-typing.md)

**Goal (acceptance criterion A6):** `availableResources` is `ReadonlySet<CSAPIResourceType>`. Consumer code that mutates the set fails to compile; consumer code iterating the set narrows automatically to the resource-type union.

**Modification to `src/ogc-api/csapi/url_builder.ts`:**

```diff
-public readonly availableResources: Set<string>;
+public readonly availableResources: ReadonlySet<CSAPIResourceType>;
```

**Verify return type of `extractAvailableResources()`** — the helper that populates the set already only emits `CSAPIResourceType` values via `scanCsapiLinks(links).keys()`. Confirm via `tsc --noEmit`. If the helper's return type is `Set<string>`, tighten it to `Set<CSAPIResourceType>` (it returns a fresh set, so the mutability is internal-only and acceptable; the **public** reference is `ReadonlySet`).

**Test impact:** `url_builder.spec.ts` — any test that does `expect(builder.availableResources.has('systems')).toBe(true)` continues to work unchanged. Any test that mutates `availableResources` (spot check; expected to be zero) must be migrated.

**Effort:** Trivial (one type annotation; possibly one helper return-type annotation). **Risk:** Low (theoretically tightens; in practice the values are already constrained).

---

### 4.5 Finding 021 — Validators Throw Plain `Error`

> **Authoritative source:** [021-pending-p2-validators-throw-plain-error.md](../../code-review/021-pending-p2-validators-throw-plain-error.md) — Decision locked: `EndpointError` only, no subclass.

**Goal (acceptance criterion A4):** Every error a CSAPI consumer can catch is `instanceof EndpointError`. `git grep "throw new Error\|throw new TypeError" -- src/ogc-api/csapi/` returns 0 matches.

**Throws to convert (verified call sites from 021 MD):**

| File                                              | Line(s)       | Function(s)               |
| ------------------------------------------------- | ------------- | ------------------------- |
| `src/ogc-api/csapi/helpers.ts`                    | 47, 77        | `formatDateTimeParameter` |
| `src/ogc-api/csapi/helpers.ts`                    | 216, 234      | `validateLimit`           |
| `src/ogc-api/csapi/helpers.ts`                    | 240, 245, 248 | `validateBbox`            |
| `src/ogc-api/csapi/formats/response.ts`           | 94, 106       | `parseCollectionResponse` |
| `src/ogc-api/csapi/formats/part2.ts`              | 48            | `requireObject`           |
| `src/ogc-api/csapi/formats/property.ts`           | 42            | `parseProperty`           |
| `src/ogc-api/csapi/formats/schema-response.ts`    | 70, 150       | (re-verify in execution)  |
| `src/ogc-api/csapi/formats/geojson.ts`            | 446, 453      | (re-verify in execution)  |
| `src/ogc-api/csapi/formats/swecommon/_helpers.ts` | 75            | (re-verify in execution)  |

**Pattern:**

```diff
+import { EndpointError } from '../../shared/errors.js'; // path varies per file

-throw new Error(`limit must be a positive integer, got ${value}`);
+throw new EndpointError(`limit must be a positive integer, got ${value}`);
```

> Line numbers in 021's table were captured before Phase 7's changes shifted some lines. **Re-verify with `git grep -n "throw new Error\|throw new TypeError" -- src/ogc-api/csapi/` immediately before editing.** Adjust the table; do not blindly trust 021's snapshot.

**Factory error wrapping (`src/ogc-api/csapi/factory.ts`):**

The factory's two `await` calls (`getCollectionInfo` and the `root` access via `endpoint.csapi()` after Section 4.6's refactor) propagate upstream's `TypeError` on network failure. Wrap them so consumers can `instanceof EndpointError`-narrow on every failure mode.

```ts
export async function createCSAPIBuilder(
  collection: CSAPICollectionRef,
  resourceUrls: ReadonlyMap<string, string>
): Promise<CSAPIQueryBuilder> {
  // Pure value-shaped factory — no awaits here after 024 refactor.
  // The wrap-in-EndpointError concern moves into endpoint.csapi() (Section 4.6),
  // which is where the awaited network calls actually live.
  return new CSAPIQueryBuilder(collection, resourceUrls);
}
```

The wrapping `try/catch` lives in `endpoint.csapi()` (Section 4.6), since that's where the network awaits happen after the 018+024 refactor:

```ts
public async csapi(collectionId: string): Promise<CSAPIQueryBuilder> {
  if (!(await this.hasConnectedSystems)) {
    throw new EndpointError('Endpoint does not support Connected Systems');
  }
  let collection: OgcApiCollectionInfo;
  let rootDoc: OgcApiDocument;
  try {
    collection = await this.getCollectionInfo(collectionId);
    rootDoc = await this.root;
  } catch (e) {
    if (e instanceof EndpointError) throw e;
    throw new EndpointError(
      `Failed to initialize CSAPI builder for collection '${collectionId}': ${
        e instanceof Error ? e.message : String(e)
      }`
    );
  }
  const links = Array.isArray(rootDoc?.links) ? rootDoc.links : [];
  const { createCSAPIBuilder } = await import('./csapi/factory.js');
  const { scanCsapiLinks } = await import('./csapi/helpers.js');
  return createCSAPIBuilder(collection, scanCsapiLinks(links));
}
```

> Note the `if (e instanceof EndpointError) throw e;` re-throw guard — never double-wrap. If we threw the error, propagate as-is; only wrap unexpected upstream errors.

**Test impact:**

- `helpers.spec.ts`, `url_builder.spec.ts`, `factory.spec.ts`, parser specs — replace `expect(...).toThrow(Error)` (or absence of type assertion) with `expect(...).toThrow(EndpointError)`.
- New test in `factory.spec.ts` (or wherever `endpoint.csapi()` is tested): mock `getCollectionInfo` to reject with `new TypeError('Network error')`; assert the thrown error is `instanceof EndpointError` and includes the original message.

**Effort:** Mechanical (12+ replace sites + factory wrap + test updates). **Risk:** Low.

---

### 4.6 Findings 018 + 024 (Coordinated) — `endpoint.csapi()` and Re-Privatization

> **Authoritative sources:** [018-pending-p3-endpoint-csapi-convenience-method.md](../../code-review/018-pending-p3-endpoint-csapi-convenience-method.md) + [024-pending-p2-endpoint-root-publicly-exposed.md](../../code-review/024-pending-p2-endpoint-root-publicly-exposed.md) — Option A3 locked, executed as one unit.

**Goal (acceptance criteria A2 + A7 + A8):**

- `OgcApiEndpoint.root` and `getCollectionDocument` revert to `private`.
- New public `OgcApiEndpoint.csapi(collectionId): Promise<CSAPIQueryBuilder>` mirrors `endpoint.edr(id)`.
- The hand-rolled `isCollectionInfo` runtime cast in `factory.ts` disappears (typed `getCollectionInfo()` makes it unreachable).
- Standalone `createCSAPIBuilder` becomes value-shaped, pure, trivially testable (no fake `OgcApiEndpoint` needed).

> **This is the highest-risk and highest-payoff change in Phase 8.** Execute it last, alone, after all other findings have landed and tests are green.

**Step-by-step execution:**

#### Step 1 — Refactor `src/ogc-api/csapi/factory.ts` to value-shaped inputs

Old signature:

```ts
export async function createCSAPIBuilder(
  endpoint: OgcApiEndpoint,
  collectionId: string
): Promise<CSAPIQueryBuilder> {
  // ... awaits, isCollectionInfo cast, scanCsapiLinks, EndpointError throws ...
}
```

New signature:

```ts
import type { CSAPICollectionRef } from './model.js';

/**
 * Constructs a {@link CSAPIQueryBuilder} from pre-resolved collection metadata.
 *
 * Pure factory: no I/O, no `await`, no error wrapping. Network-aware
 * composition lives in {@link OgcApiEndpoint.csapi} (the discoverable
 * entry point); this standalone factory is the value-shaped form for
 * tests and advanced consumers who already hold the inputs.
 *
 * @param collection - Collection descriptor with `id`, optional `title`,
 *   and the `links` array discovered from the collection document.
 * @param resourceUrls - Map of `CSAPIResourceType` → URL produced by
 *   `scanCsapiLinks(rootDoc.links)`.
 * @returns A configured {@link CSAPIQueryBuilder}.
 *
 * @public
 */
export function createCSAPIBuilder(
  collection: CSAPICollectionRef,
  resourceUrls: ReadonlyMap<string, string>
): CSAPIQueryBuilder {
  return new CSAPIQueryBuilder(collection, new Map(resourceUrls));
}
```

The `new Map(resourceUrls)` defensive copy lets the factory accept `ReadonlyMap` from callers while keeping the builder's internal mutable map invariant.

#### Step 2 — Update `src/ogc-api/csapi/factory.spec.ts`

The fake-`OgcApiEndpoint` test doubles disappear. Tests now construct a literal `CSAPICollectionRef` and a literal `Map<CSAPIResourceType, string>` and assert the built builder's behavior directly. **Net test simplification: estimated −60 LOC.**

#### Step 3 — Add `public async csapi()` to `src/ogc-api/endpoint.ts`

Signature, body, error wrapping all per Section 4.5's snippet above.

**Critical:** use **dynamic** `import('./csapi/factory.js')` and `import('./csapi/helpers.js')`. Static imports re-introduce the CSAPI dependency edge that Issue #122 (`20a35d2`) deliberately removed.

#### Step 4 — Re-privatize `root` and `getCollectionDocument`

```diff
-public get root(): Promise<OgcApiDocument> {
+private get root(): Promise<OgcApiDocument> {

-public getCollectionDocument(id: string): Promise<OgcApiDocument> {
+private getCollectionDocument(id: string): Promise<OgcApiDocument> {
```

#### Step 5 — Migrate the one external test caller

`src/ogc-api/endpoint.spec.ts:2868` (per 024 MD) asserts the shape returned by `endpoint.getCollectionDocument('iot-sensors')` (specifically that `links` includes `{rel: 'ogc-cs:systems'}`). **Migration:** assert through `endpoint.getCollectionInfo('iot-sensors')` (the upstream-typed public method) — its returned `OgcApiCollectionInfo.links` exposes the same shape.

> **Re-verify line number** with `git grep -n "getCollectionDocument" -- 'src/ogc-api/endpoint.spec.ts'` immediately before editing — Phase 7's changes may have shifted lines.

#### Step 6 — Verify the `isCollectionInfo` cast is gone

```bash
git grep -n "isCollectionInfo" -- src/ogc-api/csapi/
```

Expected: zero matches (definition site in `factory.ts` removed; no other call sites).

#### Step 7 — Update barrel exports if needed

`src/ogc-api/csapi/index.ts` — only the standalone `createCSAPIBuilder`'s **signature** changed; the export name stays. No barrel change required unless `CSAPICollectionRef` is being newly exported (Section 4.3).

#### Step 8 — Add `endpoint.csapi()` tests

In `src/ogc-api/endpoint.spec.ts`, new describe block with at least:

- happy path (mock `hasConnectedSystems → true`, mock `getCollectionInfo`, mock `root`, assert returned `CSAPIQueryBuilder` instance)
- `hasConnectedSystems → false` (asserts `EndpointError` thrown)
- `getCollectionInfo` rejects with `TypeError` (asserts wrapped `EndpointError`)
- `getCollectionInfo` rejects with `EndpointError` (asserts re-thrown as-is, not double-wrapped)

**Test impact:** `factory.spec.ts` simplifies (−60 LOC est.); `endpoint.spec.ts` gains ~80 LOC of `csapi()` tests; the one shape-assertion test migrates to `getCollectionInfo`.

**Effort:** Medium. **Risk:** Medium — touches `endpoint.ts` (upstream-authored file) and changes a public-API shape on the standalone factory. Mitigation: execute last, in isolation, with all other Phase 8 changes already green.

---

## 5. Workstream 2 — Server-Interop Bug Fixes

### 5.1 Issue #166 — Part 2 `@link` Fallback in Cross-Reference Fields

> **Authoritative source:** [Issue #166](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/166) on this repo.

**Goal (acceptance criterion B1):** All Part 2 parsers extract cross-reference IDs from either the `@id` (scalar string) form OR the `@link` (object with `href`) form, per OGC 23-002 §16.1. Library is conformant for `connected-systems-go` servers (and any future server emitting the object form).

**Spec reference (OGC 23-002 §16.1, paraphrased):** A resource may reference another resource by either:

- `"system@id": "0o123"` — scalar string identifier, OR
- `"system@link": { "href": "https://api.example.com/systems/0o123", "title": "...", ... }` — object form with `href` carrying the identifier (last URL segment) or full URL.

Servers MAY emit either; clients MUST accept either. We currently only accept `@id`.

**Cross-reference fields per parser:**

| Parser               | Fields to fall back                                                                                                      |
| -------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| `parseDatastream`    | `system@id` / `system@link.href`                                                                                         |
| `parseControlStream` | `system@id` / `system@link.href`                                                                                         |
| `parseObservation`   | `datastream@id` / `datastream@link.href`; `foi@id` / `foi@link.href`; `samplingFeature@id` / `samplingFeature@link.href` |
| `parseCommand`       | `controlstream@id` / `controlstream@link.href`                                                                           |
| `parseCommandStatus` | `command@id` / `command@link.href`                                                                                       |

**New helper in `src/ogc-api/csapi/formats/part2.ts` (or `_helpers.ts`):**

````ts
/**
 * Extracts a cross-reference ID from either the scalar `@id` form or the
 * object `@link` form, per OGC 23-002 §16.1.
 *
 * The `@link` form carries an `href` that may be a full URL or just an
 * identifier; the last path segment is used as the ID. When both forms
 * are present, `@id` wins (it is the authoritative scalar form).
 *
 * @param obj - The raw resource object.
 * @param fieldName - Cross-reference field name (e.g., `'system'`, `'datastream'`, `'foi'`).
 * @returns The extracted ID, or `undefined` if neither form is present or well-formed.
 *
 * @example
 * ```ts
 * extractCrossReferenceId({ 'system@id': '0o123' }, 'system');           // '0o123'
 * extractCrossReferenceId(
 *   { 'system@link': { href: 'https://api.example.com/systems/0o123' } },
 *   'system'
 * );                                                                      // '0o123'
 * extractCrossReferenceId({}, 'system');                                  // undefined
 * ```
 */
function extractCrossReferenceId(
  obj: Record<string, unknown>,
  fieldName: string
): string | undefined {
  // Form 1: scalar @id (authoritative; wins if both forms present)
  const idValue = obj[`${fieldName}@id`];
  if (typeof idValue === 'string' && idValue.length > 0) {
    return idValue;
  }
  // Form 2: object @link with href
  const linkValue = obj[`${fieldName}@link`];
  if (
    typeof linkValue === 'object' &&
    linkValue !== null &&
    typeof (linkValue as Record<string, unknown>).href === 'string'
  ) {
    const href = (linkValue as Record<string, unknown>).href as string;
    // href may be full URL or bare ID; use last path segment
    const lastSegment = href.split('/').filter(Boolean).pop();
    if (lastSegment && lastSegment.length > 0) {
      return lastSegment;
    }
  }
  return undefined;
}
````

**Replacement pattern (example for `parseBaseStream` `systemId`):**

```diff
-      ...(typeof obj['system@id'] === 'string'
-        ? { systemId: obj['system@id'] as string }
-        : {}),
+      ...((() => {
+        const systemId = extractCrossReferenceId(obj, 'system');
+        return systemId !== undefined ? { systemId } : {};
+      })()),
```

Apply analogously in `parseObservation` (3 fields), `parseCommand` (1 field), `parseCommandStatus` (1 field).

**Test additions:** in `src/ogc-api/csapi/formats/part2.spec.ts`, add for each affected parser/field a test pair:

```ts
it('parses systemId from system@id (scalar form)', () => {
  const ds = parseDatastream({
    id: 'd1',
    name: 'D1',
    formats: [],
    links: [],
    'system@id': 's1',
  });
  expect(ds.systemId).toBe('s1');
});

it('parses systemId from system@link.href (object form, OGC 23-002 §16.1)', () => {
  const ds = parseDatastream({
    id: 'd1',
    name: 'D1',
    formats: [],
    links: [],
    'system@link': { href: 'https://api.example.com/systems/s1' },
  });
  expect(ds.systemId).toBe('s1');
});

it('prefers @id over @link when both present', () => {
  const ds = parseDatastream({
    id: 'd1',
    name: 'D1',
    formats: [],
    links: [],
    'system@id': 's-scalar',
    'system@link': { href: 'https://api.example.com/systems/s-link' },
  });
  expect(ds.systemId).toBe('s-scalar');
});

it('handles @link.href as bare identifier (no path)', () => {
  const ds = parseDatastream({
    id: 'd1',
    name: 'D1',
    formats: [],
    links: [],
    'system@link': { href: 's1' },
  });
  expect(ds.systemId).toBe('s1');
});

it('returns undefined systemId when neither @id nor @link is present', () => {
  const ds = parseDatastream({ id: 'd1', name: 'D1', formats: [], links: [] });
  expect(ds.systemId).toBeUndefined();
});
```

**Multiply by 5 parsers × 5–6 cross-reference fields = ~25–30 new test cases.**

**Fixture updates:** none required — existing fixtures continue to use the `@id` form, which is still the preferred branch. Optionally add one new fixture file per parser exercising the `@link` form to lock in the contract end-to-end.

**Effort:** Small (one helper + 5 call-site changes + ~25 tests). **Risk:** Low (`@id` form is preferred, so existing behavior is preserved; new branch adds a fallback only).

---

### 5.2 Issue #167 — Pagination-Contract JSDoc on List Methods

> **Authoritative source:** [Issue #167](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/167) on this repo.

**Goal (acceptance criterion B2):** Every list method on `CSAPIQueryBuilder` carries JSDoc that explicitly documents the pagination contract: server picks default page size; consumer follows `next` HATEOAS links to retrieve subsequent pages.

**Background:** `connected-systems-go` defaults to `limit=10`; OpenSensorHub defaults to `limit=100`. A consumer who only tested against the high-default server may silently process only the first page in production against a low-default server. The OGC spec lets servers choose; the library's job is to make that contract impossible to miss.

**List methods (after Section 4.2's rename):**

- `getSystems`
- `getDeployments`
- `getProcedures`
- `getSamplingFeatures`
- `getDatastreams`
- `getDatastreamObservations`
- `getDatastreamSystems`
- `getDatastreamProcedures`
- `getDatastreamHistory`
- `getSystemDatastreams`
- `getSystemSubsystems`
- `getProcedureDatastreams`
- `getControlStreams`
- `getCommands`
- `getCommandStatus` (if it returns a list)
- `getObservations` (if exposed)

**Centralized "Pagination" doc anchor in `csapi/url_builder.ts` module docblock (or class docblock):**

```ts
/**
 * ...
 *
 * ## Pagination
 *
 * All list methods (`get*` returning collection URLs) follow the
 * [OGC API Common](https://docs.ogc.org/is/19-072/19-072.html#_pagination)
 * pagination contract:
 *
 * - **The server chooses the default page size** if `limit` is unspecified.
 *   Defaults vary by implementation — `connected-systems-go` defaults to
 *   `limit=10`; OpenSensorHub defaults to `limit=100`. Code that processes
 *   only the first response may silently lose data on low-default servers.
 *
 * - **The server returns `next` HATEOAS links** in the response body's
 *   `links` array (`rel: "next"`) when more pages are available. The
 *   consumer is responsible for following them; this library does not
 *   auto-paginate.
 *
 * - **A future enhancement** (deferred — see issue
 *   [#170](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/170))
 *   may add an opt-in async-iterator / `followNext` helper. Until then,
 *   consumer code MUST follow `next` links explicitly to avoid data loss.
 *
 * ...
 */
```

**Per-method `@remarks` tag:**

```ts
/**
 * Builds the URL for a paginated list of datastreams.
 *
 * @remarks
 * **Pagination:** server picks the default `limit` if unspecified; the
 * consumer must follow `next` HATEOAS links from the response body to
 * retrieve subsequent pages. See the
 * [Pagination section of this module's docs](#pagination).
 *
 * @param options - Optional query parameters (limit, bbox, datetime, etc.).
 * @returns The fully-formed URL string.
 */
public getDatastreams(options?: DatastreamQueryOptions): string { ... }
```

**Test impact:** none for behavior; one optional snapshot/lint test that asserts every public list method has a JSDoc block matching `/Pagination:.*next.*links/i`. (Skip if it adds more friction than value.)

**Effort:** Trivial (docblock additions on ~15 methods + one centralized anchor). **Risk:** None.

---

## 6. Workstream 3 — Already-Shipped Triage Outputs (Recap)

These are **completed Phase 8 work product** that requires no further execution. Listed for ledger completeness.

| Item                                                                    | Status              | Authoritative location                                                                                   |
| ----------------------------------------------------------------------- | ------------------- | -------------------------------------------------------------------------------------------------------- |
| #168 `getLatestObservationUrls()` shim                                  | Closed wontfix      | [#168 status banner](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/168)                          |
| #169 heuristic coordinate extraction                                    | Closed wontfix      | [#169 status banner](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/169)                          |
| #170 async-iterator pagination helpers                                  | Filed deferred      | [#170](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/170)                                        |
| #171 SWE Common-aware result extraction                                 | Filed deferred      | [#171](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/171)                                        |
| `references.md` "Known Server Conformance Gaps" (4 gaps)                | Shipped (`3878577`) | [`docs/research/references.md`](../../research/references.md)                                            |
| `references.md` "Research Findings Not Adopted, Finding 1"              | Shipped (`a3424a8`) | [`docs/research/references.md`](../../research/references.md)                                            |
| `ogc-csapi-explorer#47` (consolidate `resultTime=latest` fallback)      | Filed               | [Explorer #47](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/47)                                 |
| `ogc-csapi-explorer#48` (replace local extractor when SWE Common lands) | Filed               | [Explorer #48](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/48)                                 |
| `connected-systems-go#11` comment with additional findings              | Posted              | [`cs-go#11` comment](https://github.com/OS4CSAPI/connected-systems-go/issues/11#issuecomment-4340812938) |

> Workstream 3 contributes **zero source/fixture diff to `clean-pr`.** The catalog updates live on `phase-8` only; only Workstreams 1 and 2 flow through the Phase 8 squashed commit.

---

## 7. Cross-Cutting Concerns

### 7.1 Test Update Pattern

For every modified production file, expect to update its co-located `.spec.ts` in the same commit boundary. The pattern across all of Workstream 1:

1. Identify call sites in the spec file (`grep` the old name / shape).
2. Apply mechanical update.
3. Add new test cases ONLY where new behavior is introduced (`@link` fallback in #166, `endpoint.csapi()` in 4.6, error wrapping in 4.5).
4. Run the single spec file in watch mode for fast iteration.
5. Run the full browser + node suites before committing.

### 7.2 Order of Operations Within a Single Sitting

If executing all of Workstream 1 + Workstream 2 in a single sitting (the expected mode), the recommended order is:

1. **017** (docs only — gives confidence the test runner is healthy)
2. **019** (mechanical rename — sets the naming foundation that #167's pagination JSDoc will reference)
3. **022** (`CSAPICollectionRef` type) ← **prerequisite for 4.6**
4. **023** (`ReadonlySet<CSAPIResourceType>`) ← independent, fast
5. **021** (`EndpointError` swap in helpers/parsers) — leaves factory wrap for 4.6
6. **#166** (Part 2 `@link` fallback) — independent of 1–5; isolated to `formats/part2.ts`
7. **#167** (pagination JSDoc) — depends on the renames from #2 being done
8. **018 + 024** (coordinated, last) — refactors factory signature + endpoint composition + error wrapping; everything else must be green first

After each step, run `npm run typecheck && npm run test:browser` against the touched file's spec. After all 8 steps land, run the full CI gate (Section 8).

### 7.3 `@deprecated` Tag Policy

**No `@deprecated` tags are introduced anywhere in Phase 8.**

Rationale (see locked decision #1 in Section 3 and finding 019's "Decision"): PR #136 has not merged upstream; the CSAPI feature set has never shipped; there are no consumers whose code would break from the renames. A `@deprecated` annotation is documentation for a deprecation cycle — there is no cycle to document. Adding deprecation aliases would ship two names for every renamed method on a feature set that has never been released, creating permanent cruft and inviting the maintainer-pushback question "who is this deprecation cycle for?"

If, during execution, an instinct arises to add `@deprecated` tags "just to be safe" — stop. The decision is locked; the savings of clean execution outweigh the imagined cost of a future hypothetical consumer.

---

## 8. Verification Plan

### 8.1 Per-Finding Acceptance Verification

Run these checks **after** each finding's section completes, **before** moving to the next:

| Finding   | Verification command                                                                                                                                                                                     |
| --------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 017       | Manual review: open `csapi/index.ts`, `factory.ts`, `url_builder.ts` JSDoc, README — pattern visible in all 4                                                                                            |
| 019       | `git grep -n "DataStream" -- src/ogc-api/csapi/url_builder.ts` returns 0 lines (modulo `Datastream` matches)                                                                                             |
| 022       | `git grep -n "OgcApiCollectionInfo" -- src/ogc-api/csapi/url_builder.ts` returns 0 (only model.ts may reference it)                                                                                      |
| 023       | `npx tsc --noEmit` passes; manually attempt `builder.availableResources.add('foo')` in a scratch — must error                                                                                            |
| 021       | `git grep -n "throw new Error\|throw new TypeError" -- src/ogc-api/csapi/` returns 0                                                                                                                     |
| #166      | `npm run test:browser src/ogc-api/csapi/formats/part2.spec.ts` — all new `@link` tests pass                                                                                                              |
| #167      | Manual review: every list method's JSDoc has `@remarks` Pagination block                                                                                                                                 |
| 018 + 024 | `git grep -n "public root\|public getCollectionDocument" src/ogc-api/endpoint.ts` returns 0; `git grep -n "isCollectionInfo" -- src/ogc-api/csapi/` returns 0; new `endpoint.csapi(id)` test suite green |

### 8.2 Full CI Gate

After all 8 steps complete, before generating the source patch:

```powershell
cd c:\Users\sbolling\Documents\ogc-client-CSAPI_2
npx prettier --check .
npm run typecheck
npm run lint
npm run test:browser
npm run test:node
```

All five must exit 0. If any fails, fix on `phase-8` before proceeding to delivery.

### 8.3 Behavioral Preservation Spot Checks

- `npm run test:browser src/ogc-api/csapi/integration/` — Phase 5/6 integration tests still pass (regression catch for finding 021's error-type changes affecting any `toThrow(Error)` assertions).
- `git diff phase-7..phase-8 -- src/ ':!src/ogc-api/csapi/' ':!src/index.ts'` — non-CSAPI source changes are limited to `src/ogc-api/endpoint.ts` (the A2 + A7 edits) and nothing else.

### 8.4 Litmus Tests

Three "consumer-perspective" smoke checks, run in a scratch script outside the test suite:

```ts
// 1. Can a consumer narrow on EndpointError uniformly?
try {
  await endpoint.csapi('does-not-exist');
} catch (e) {
  console.assert(e instanceof EndpointError);
}

// 2. Is the discoverable IDE entry point present and typed?
const builder = await endpoint.csapi('weather-stations');
const url: string = builder.getDatastreams({ limit: 10 }); // must compile

// 3. Does @link fallback parse correctly?
const ds = parseDatastream({
  id: 'd1',
  name: 'D1',
  formats: [],
  links: [],
  'system@link': { href: 'https://api.example.com/systems/s1' },
});
console.assert(ds.systemId === 's1');
```

---

## 9. Risk Register

| #   | Risk                                                                                       | Likelihood | Impact | Mitigation                                                                                                    |
| --- | ------------------------------------------------------------------------------------------ | ---------- | ------ | ------------------------------------------------------------------------------------------------------------- |
| R1  | Rename in finding 019 misses a call site outside tracked files (e.g., `app/`, `src-node/`) | Low        | Low    | `git grep -n "DataStream"` workspace-wide post-rename; tsc must be green                                      |
| R2  | `endpoint.csapi()` dynamic import breaks tree-shaking in some bundler                      | Low        | Medium | Mirrors EDR's pattern (which is upstream-blessed); manual `npm run build` + bundle-size spot check            |
| R3  | `EndpointError` swap (021) breaks an existing test asserting `instanceof Error` only       | Medium     | Low    | `EndpointError extends Error` so `instanceof Error` still narrows; only stricter `instanceof TypeError` fails |
| R4  | `@link` fallback (#166) introduces parse divergence between two equivalent server outputs  | Low        | Medium | Test asserts `@id` always wins when both present; helper preserves identifier-uniqueness invariant            |
| R5  | Maintainer rejects new `endpoint.csapi()` method as "more public surface"                  | Low        | Medium | Net public surface decreases (`+1 method, −2 broad members`); coordinated framing in PR #136 update           |
| R6  | One of the deferred findings (020, 025, 026) gets re-litigated mid-execution               | Low        | Low    | Decision rails in Section 3; AI Operational Constraints; surface to user, do not silently re-decide           |
| R7  | `references.md` updates accidentally land in the source-only patch                         | Low        | Medium | Patch is `git diff phase-7..phase-8 -- src/ fixtures/`; explicitly excludes `docs/`                           |
| R8  | Endpoint spec test migration (Step 5 of 4.6) leaves a hole in CSAPI link-shape coverage    | Low        | Low    | New `endpoint.csapi()` happy-path test asserts the same `links` shape end-to-end                              |

---

## 10. Scope Boundaries — What Does NOT Change

**Files not touched (zero behavioral change):**

- `src/ogc-api/csapi/formats/geojson.ts` (Part 1 GeoJSON parsing)
- `src/ogc-api/csapi/formats/property.ts` (except finding 021's `EndpointError` swap)
- `src/ogc-api/csapi/formats/schema-response.ts` (except finding 021)
- `src/ogc-api/csapi/formats/swecommon/*` (except finding 021's `EndpointError` swap in `_helpers.ts`)
- `src/ogc-api/csapi/command-routing.ts` (Phase 7 cleanup is final)
- `src/ogc-api/csapi/integration/*` (regression test only)
- All SensorML parsers
- All non-CSAPI modules (`stac/`, `wfs/`, `wms/`, `wmts/`, `tms/`, `worker/`)
- `package.json` — no new sub-paths, no new dependencies

**Findings explicitly deferred (not Phase 8):**

| Origin               | Item                                                                                                                                  | Rationale                                                                                             |
| -------------------- | ------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| Senior dev review #2 | Finding 020 — positional `controlStreamId` argument ([020](../../code-review/020-deferred-p3-positional-controlstreamid-arg.md))      | Wider signature redesign; would expand scope                                                          |
| Senior dev review #2 | Finding 025 — `AbortSignal` in `createCSAPIBuilder` ([025](../../code-review/025-deferred-enhancement-abortsignal-in-factory.md))     | Enhancement; out of scope until upstream broadens scope                                               |
| Senior dev review #2 | Finding 026 — `followNext` pagination helper ([026](../../code-review/026-deferred-enhancement-follownext-pagination-helper.md))      | Enhancement; duplicate-tracked at #170                                                                |
| Phase 5/6 carry-over | Issue #110 — `@link`/`@id` resolution utilities ([110](../../code-review/110-deferred-enhancement-link-resolution-utilities.md))      | Pre-existing deferred enhancement                                                                     |
| Phase 7 carry-over   | Upstream-authored security findings 001, 002, 005, 006 ([upstream-findings-report.md](../../code-review/upstream-findings-report.md)) | Not our code; not in PR #136                                                                          |
| CS-Go triage         | Issues #168, #169                                                                                                                     | Closed `wontfix`; library is spec-correct (#168) or proposed approach is architecturally wrong (#169) |
| CS-Go triage         | Issues #170, #171                                                                                                                     | Filed deferred; not in scope until upstream broadens scope or a second consumer demonstrates need     |

**Hard scope fence — applies to every line of code written this phase:**

> Phase 8 does **not** absorb consumer-side ergonomic helpers into the published library. The `MapViewPage.vue` patterns that motivated #168 and #169 stay in the consumer's repo. The library stays as narrow as upstream wants it. If during execution a "wouldn't it be nice if the library just..." impulse arises, file a new issue, do not implement.

---

## 11. Two-Repo Delivery Sequence

Identical to Phase 7's pattern (the one part of Phase 7 that was structurally right).

| Step | Action                                                                                                                              | Repo                          |
| ---- | ----------------------------------------------------------------------------------------------------------------------------------- | ----------------------------- |
| 1    | All Workstream 1 + 2 commits land on `phase-8` with full granular history (one commit per finding/issue is fine)                    | `OS4CSAPI/ogc-client-CSAPI_2` |
| 2    | Full CI gate passes locally (Section 8.2)                                                                                           | `phase-8`                     |
| 3    | Generate source/fixture-only patch: `git diff phase-7..phase-8 -- src/ fixtures/ > phase-8.patch`                                   | `phase-8`                     |
| 4    | Switch to `OS4CSAPI/ogc-client` `clean-pr`; `git apply phase-8.patch`; `git add -A`; one squashed commit with comprehensive message | `OS4CSAPI/ogc-client`         |
| 5    | Push `clean-pr`; CI runs on PR #136                                                                                                 | `OS4CSAPI/ogc-client`         |
| 6    | Verify CI green on PR #136                                                                                                          | GitHub                        |
| 7    | Update PR #136 description with a "Phase 8" section (acceptance criteria recap + resolved-findings list + deferred-follow-ups list) | GitHub                        |
| 8    | Tag @jahow for final review with explicit time-frame ask                                                                            | GitHub                        |

**Squashed commit message template (Step 4):**

```
Phase 8: API design refinements + CS-Go server-interop fixes

Resolves the senior developer's second code review (10 findings, 7 accepted /
3 deferred) and two server-interop bugs surfaced by integration testing
against connected-systems-go.

API surface refinements (Workstream 1):
- 017: URL-builder framing in module docs (csapi/index.ts, factory.ts,
  url_builder.ts, README)
- 018+024 (coordinated): add endpoint.csapi(id) convenience method;
  re-privatize OgcApiEndpoint.root and getCollectionDocument; refactor
  createCSAPIBuilder to value-shaped (collection, resourceUrls); remove
  unsound isCollectionInfo cast
- 019: rename 13 *DataStream* methods to *Datastream* (no aliases — PR
  unmerged, no consumers)
- 021: standardize all csapi/ throws on EndpointError (no subclass);
  endpoint.csapi() wraps init network errors
- 022: introduce CSAPICollectionRef type; constructor no longer leaks
  upstream OgcApiCollectionInfo
- 023: tighten availableResources to ReadonlySet<CSAPIResourceType>

Server-interop bug fixes (Workstream 2):
- #166 (P1): Part 2 parsers accept @link object form alongside @id scalar
  form for cross-reference fields, per OGC 23-002 §16.1
- #167 (P3): pagination contract documented on every list method

Deferred (not in this commit):
- Findings 020, 025, 026 (per-MD rationales)
- Issues #170, #171 (filed deferred)
- Upstream-authored findings 001, 002, 005, 006 (out of scope)

Closes (wontfix):
- #168 (library is spec-correct per OGC 23-002 §13.3.2 D; gap is
  server-side, tracked at OS4CSAPI/connected-systems-go#11)
- #169 (heuristic approach is architecturally wrong; SWE Common-aware
  successor tracked at #171)

Verification: full CI gate green (prettier, tsc, eslint, browser tests,
node tests). Zero changes to non-CSAPI public API.
```

---

## 12. References

| #   | Source                                                                                                                                       | Role                                                                        |
| --- | -------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------- |
| 1   | [P8-contribution-goal-and-definition.md](P8-contribution-goal-and-definition.md)                                                             | Goal, acceptance criteria, three-workstream scope                           |
| 2   | [P8-triage.md](P8-triage.md)                                                                                                                 | Triage of the 10 findings from senior dev review #2                         |
| 3   | [P8-ROADMAP.md](P8-ROADMAP.md) (forthcoming)                                                                                                 | Execution-unit grouping with hours and dependencies                         |
| 4   | [`docs/code-review/017`](../../code-review/017-pending-p3-docs-url-builder-framing.md)                                                       | URL-builder framing finding                                                 |
| 5   | [`docs/code-review/018`](../../code-review/018-pending-p3-endpoint-csapi-convenience-method.md)                                              | `endpoint.csapi()` convenience method                                       |
| 6   | [`docs/code-review/019`](../../code-review/019-pending-p2-method-naming-datastream-vs-datastream.md)                                         | Method rename decision (Option A locked)                                    |
| 7   | [`docs/code-review/021`](../../code-review/021-pending-p2-validators-throw-plain-error.md)                                                   | Error-contract decision (`EndpointError` only locked)                       |
| 8   | [`docs/code-review/022`](../../code-review/022-pending-p3-constructor-exposes-collection-info-type.md)                                       | `CSAPICollectionRef` type                                                   |
| 9   | [`docs/code-review/023`](../../code-review/023-pending-p3-availableresources-set-typing.md)                                                  | `availableResources` typing                                                 |
| 10  | [`docs/code-review/024`](../../code-review/024-pending-p2-endpoint-root-publicly-exposed.md)                                                 | Re-privatization decision (Option A3 locked)                                |
| 11  | [`docs/code-review/upstream-findings-report.md`](../../code-review/upstream-findings-report.md)                                              | Upstream-authored findings (out of scope)                                   |
| 12  | [`docs/research/references.md`](../../research/references.md) — "Known Server Conformance Gaps" + "Research Findings Not Adopted, Finding 1" | Workstream 3 catalog outputs                                                |
| 13  | [Issue #166](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/166)                                                                      | Part 2 `@link` fallback bug                                                 |
| 14  | [Issue #167](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/167)                                                                      | Pagination-contract docs gap                                                |
| 15  | [PR #136 (camptocamp/ogc-client)](https://github.com/camptocamp/ogc-client/pull/136)                                                         | The upstream pull request being updated                                     |
| 16  | [P5-parser-completion-implementation-guide.md](../phase-5/P5-parser-completion-implementation-guide.md)                                      | Phase 5 trio precedent                                                      |
| 17  | [P6-implementation-guide.md](../phase-6/P6-implementation-guide.md)                                                                          | Phase 6 trio precedent (closest structural parallel)                        |
| 18  | [`docs/governance/AI_OPERATIONAL_CONSTRAINTS.md`](../../governance/AI_OPERATIONAL_CONSTRAINTS.md)                                            | Operational discipline; precedence rules                                    |
| 19  | [OGC 23-002](https://docs.ogc.org/is/23-002/23-002.html) — Connected Systems Part 2                                                          | Spec authority for §16.1 (`@link`/`@id`) and §13.3.2 D (latest-observation) |

---

## Operational Constraints (recap)

> **⚠️ MANDATORY:** Before starting work on any Phase 8 finding, review [`docs/governance/AI_OPERATIONAL_CONSTRAINTS.md`](../../governance/AI_OPERATIONAL_CONSTRAINTS.md).

Phase 8 execution rails:

- **Precedence:** OGC specs → AI Collaboration Agreement → [P8-contribution-goal-and-definition.md](P8-contribution-goal-and-definition.md) → this guide → per-finding MD → existing code → conversational context.
- **No scope expansion.** If the urge arises during execution, file a new issue and defer.
- **Minimal diffs.** Smallest change that satisfies the acceptance criterion.
- **Locked decisions stay locked.** Section 3's table is the contract. Surface; do not silently re-decide.
- **Two-repo workflow respected.** All source changes land on `phase-8` first; `clean-pr` is delivery-only.
- **Wontfix decisions stay closed.** #168 and #169 are not reopened without explicit user direction.
