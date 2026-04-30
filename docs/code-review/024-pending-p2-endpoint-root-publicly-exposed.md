---
status: accepted
priority: p2
issue_id: '024'
tags: [code-review, api-design, upstream-surface]
dependencies: []
phase: 8
needs-decision: false
decision: 'Option A3 — re-privatize and compose via endpoint.csapi()'
coordinated-with: ['018']
---

# `OgcApiEndpoint.root` and `getCollectionDocument` Newly Public

## Problem Statement

Phase 6 / Phase 7 made two `OgcApiEndpoint` members public so `factory.ts`
could access them across the module boundary:

- `OgcApiEndpoint.root` — getter returning `Promise<OgcApiDocument>`
- `OgcApiEndpoint.getCollectionDocument(id)` — method returning
  `Promise<OgcApiDocument>`

Both return `OgcApiDocument`, which is a `Record<string, unknown>` wrapper.
Making these public freezes the document format into the public API of
`OgcApiEndpoint` — a change that affects upstream-authored class members and
may draw maintainer pushback during PR review.

## Findings

**File:** `src/ogc-api/endpoint.ts`

The two members were promoted from `private` to `public` in commit `20a35d2`
("refactor(endpoint): remove CSAPI coupling, Issue #122, Task 6"). The
commit message records both the removals and the visibility changes
explicitly:

> Removals (5 items): `import CSAPIQueryBuilder`,
> `import { scanCsapiLinks }`, `private collection_id_to_csapi_builder_`
> cache map, `csapi()` method + JSDoc (~49 lines),
> `extractRootResourceUrls()` + JSDoc (~14 lines).
>
> Visibility changes (2 items): `private get root()` → `public get root()`;
> `private getCollectionDocument()` → `public getCollectionDocument()`.
>
> File: 892 → 773 lines. Zero CSAPI imports remain.

The visibility changes were the **cost** of decoupling: by moving
`csapi()` and `extractRootResourceUrls()` out of `OgcApiEndpoint` into
`src/ogc-api/csapi/factory.ts`, helper code that previously had private
access to `root_` and `getCollectionDocument` now had to reach them across
a module boundary. They are not arbitrary — they are residue of a
deliberate architectural decision (Issue #122).

### What the factory actually uses

The factory does this with the two members:

```ts
// src/ogc-api/csapi/factory.ts
const collectionDoc = await endpoint.getCollectionDocument(collectionId); // raw OgcApiDocument
const rootDoc = await endpoint.root; // raw OgcApiDocument
const links = rootDoc?.links;
const resourceUrls = Array.isArray(links) ? scanCsapiLinks(links) : new Map();

if (!isCollectionInfo(collectionDoc)) {
  // hand-rolled validator
  throw new EndpointError(/* ... */);
}

return new CSAPIQueryBuilder(collectionDoc, resourceUrls);
```

**Of the full `OgcApiDocument` (`Record<string, unknown>`), the factory
uses:**

- From `getCollectionDocument`: just enough to satisfy `isCollectionInfo`
  (i.e., `id: string`) and to feed the `CSAPIQueryBuilder` constructor,
  which actually accepts
  `Pick<OgcApiCollectionInfo, 'id' | 'title' | 'links'>`.
- From `root`: only `rootDoc.links` (an array of `{rel?, href?}` objects),
  passed straight to `scanCsapiLinks`.

Neither call needs the full document. Both touch a small slice.

### Existing public surface that already covers most of this

- `OgcApiEndpoint.getCollectionInfo(id): Promise<OgcApiCollectionInfo>` —
  pre-existing upstream method (line 416). Returns the **typed parsed**
  object. Replacing the factory's `getCollectionDocument` call with
  `getCollectionInfo` removes the need for the hand-rolled
  `isCollectionInfo` validator and the unsound cast that follows it
  (the cast pattern is the same as upstream-findings finding 003).
- `OgcApiEndpoint.csapiCollections: Promise<string[]>` and
  `hasConnectedSystems: Promise<boolean>` — added in our work, but narrow
  and CSAPI-aware, unlike the broad `root` / `getCollectionDocument` pair.

### EDR's pattern (the symmetry finding 018 wants us to mirror)

`endpoint.edr(id)` calls `this.getCollectionInfo(id)` internally and
constructs an `EDRQueryBuilder`. It does **not** touch
`getCollectionDocument` or `root` directly — `getCollectionInfo` is enough.
EDR also caches builders in a private `Map`. This is the model A3
proposes for CSAPI.

### Active external use of the two flagged members

Outside of the factory, the codebase touches them in exactly two places,
both in tests:

- `src/ogc-api/endpoint.spec.ts:2868` — a test asserts the shape returned
  by `endpoint.getCollectionDocument('iot-sensors')` (specifically that
  `links` includes `{rel: 'ogc-cs:systems'}`).
- `src/ogc-api/csapi/factory.ts` lines 55–56 — the only production call
  sites.

`endpoint.root` is **not used anywhere in the workspace except the
factory.** No tests call it; no other production code calls it. Reverting
it to private therefore costs nothing in test churn.

## Options Evaluated

| Option                                                                            | Public-surface cost                               | Reverses #122?               | Eliminates unsound `isCollectionInfo` cast? | Maintainer-friendliness |
| --------------------------------------------------------------------------------- | ------------------------------------------------- | ---------------------------- | ------------------------------------------- | ----------------------- |
| C (in-endpoint method only)                                                       | +1 method, removes both flagged members           | **Yes**                      | No                                          | Low                     |
| B (keep public, document in PR)                                                   | +2 broad members permanent                        | No                           | No                                          | Medium                  |
| A1 (private + new `rootLinks` getter)                                             | +1 narrow getter, −2 broad                        | No                           | Yes (via existing `getCollectionInfo`)      | High                    |
| A2 (private + new `csapiResourceUrls` getter)                                     | +1 narrow getter, −2 broad                        | Partially (re-adds 1 import) | Yes                                         | High                    |
| **A3 (private + reuse `endpoint.csapi()` from finding 018 to compose privately)** | **+1 method (already accepted in 018), −2 broad** | **No**                       | **Yes**                                     | **Highest**             |

### Option C — Rejected

Reverses commit `20a35d2`. Re-introduces the import (`CSAPIQueryBuilder`,
`scanCsapiLinks`), the cache map, and the method body that Issue #122
explicitly removed. Going down this path invalidates #122's closing
rationale and likely requires re-litigating that decision with the upstream
maintainer. The reviewer's framing of Option C did not have visibility into
#122. Note that Option C is **not** the same thing as finding 018's
`endpoint.csapi()` wrapper — finding 018 is an additive thin delegator that
preserves tree-shaking via dynamic import, whereas Option C imports CSAPI
modules statically into `endpoint.ts`.

### Option B — Rejected

Lowest effort but highest long-term cost. Permanently commits the maintainer
to public `root` and `getCollectionDocument` for any future refactor, even
though nothing in their codebase uses them. Also retains the unsound
`isCollectionInfo` cast in `factory.ts`. "Document in PR" is fine in
principle, but explaining "we needed two new public getters to support a
sub-path factory we extracted from the same class" invites a justified
"why didn't you use `getCollectionInfo`?" follow-up.

### Option A3 — Accepted (recommended)

Coordinate findings 018 and 024 in a single execution step. The
`endpoint.csapi(id)` method we are already adding under finding 018 becomes
the place where private access happens; the standalone `createCSAPIBuilder`
is refactored to take value-shaped inputs.

```ts
// On OgcApiEndpoint (private members again):
private get root(): Promise<OgcApiDocument> { /* unchanged body */ }
private getCollectionDocument(id: string): Promise<OgcApiDocument> { /* unchanged body */ }

// New public method (finding 018):
public async csapi(collectionId: string): Promise<CSAPIQueryBuilder> {
  if (!(await this.hasConnectedSystems)) {
    throw new EndpointError('Endpoint does not support Connected Systems');
  }
  const collection = await this.getCollectionInfo(collectionId); // typed
  const rootDoc = await this.root;                                // private access
  const links = Array.isArray(rootDoc?.links) ? rootDoc.links : [];
  const { createCSAPIBuilder } = await import('./csapi/factory.js'); // tree-shake-friendly
  return createCSAPIBuilder(collection, scanCsapiLinks(links));
}
```

```ts
// Refactored standalone factory (now value-shaped, pure, easy to test):
export function createCSAPIBuilder(
  collection: Pick<OgcApiCollectionInfo, 'id' | 'title' | 'links'>,
  resourceUrls: ReadonlyMap<string, string>
): CSAPIQueryBuilder {
  return new CSAPIQueryBuilder(collection, resourceUrls);
}
```

**Net result:**

- `endpoint.root` and `endpoint.getCollectionDocument` revert to private.
- The unsound `isCollectionInfo` validator in `factory.ts` disappears —
  `getCollectionInfo` returns a typed object.
- Issue #122's decoupling decision is preserved (no static CSAPI imports in
  `endpoint.ts`; `endpoint.csapi()` uses dynamic `import()`).
- The standalone `createCSAPIBuilder` becomes pure and trivially testable
  (no fake `OgcApiEndpoint` needed in tests).
- One discoverable IDE entry point (`endpoint.csapi(id)`) that mirrors EDR's
  `endpoint.edr(id)` pattern.

**Cost / asymmetries to flag:**

- The standalone `createCSAPIBuilder` signature changes from
  `(endpoint, collectionId)` to `(collection, resourceUrls)`. PR #136 has
  not been merged upstream; the CSAPI feature set has never shipped, so
  there are no downstream consumers — the same "no consumers yet" reasoning
  that drove finding 019's decision applies here.
- The single test at `src/ogc-api/endpoint.spec.ts:2868` that calls
  `endpoint.getCollectionDocument('iot-sensors')` to assert CSAPI link
  shapes will need to be migrated to assert through `getCollectionInfo` or
  through `endpoint.csapi(...)`'s observable behavior.
- `factory.spec.ts` will need updating to match the new value-shaped
  signature; the test doubles become simpler (no `OgcApiEndpoint` fake
  required).

## Coordination with Finding 018

Findings [018](018-pending-p3-endpoint-csapi-convenience-method.md) and 024
are now treated as a single coordinated change. Finding 018 ("add
`endpoint.csapi()` for symmetry with `endpoint.edr()`") is the natural
landing spot for the private composition that 024 needs. Executing 018
alone (without 024) would leave the factory still requiring public access;
executing 024 alone (with one of A1/A2) would add a new narrow getter
without addressing 018's discoverability concern. Doing both together is
strictly less code than either in isolation.

## Decision

**Option A3 — re-privatize and compose via `endpoint.csapi()`.**
Decided April 28, 2026.

Rationale: highest maintainer-friendliness, preserves Issue #122's
decoupling, eliminates the unsound `isCollectionInfo` cast as a side
benefit, makes the standalone factory pure and testable, and folds finding
018's work into the same change with no extra cost.

## Execution Notes (Phase 8 plan input)

Sequence within Phase 8 (subject to confirmation in the execution plan):

1. Refactor `src/ogc-api/csapi/factory.ts` to take
   `(collection, resourceUrls)` instead of `(endpoint, collectionId)`.
   Drop the hand-rolled `isCollectionInfo` validator. Update its JSDoc.
2. Update `src/ogc-api/csapi/factory.spec.ts` to the new signature
   (test doubles simplify).
3. Add `public async csapi(collectionId: string)` to
   `src/ogc-api/endpoint.ts` per finding 018's recommendation, doing the
   private composition described above (uses `getCollectionInfo`,
   private `root`, dynamic `import()` for the factory and `scanCsapiLinks`).
4. Flip `public get root()` → `private get root()` and
   `public getCollectionDocument()` → `private getCollectionDocument()`.
5. Migrate the `endpoint.spec.ts:2868` assertion off
   `getCollectionDocument`.
6. Update `csapi/index.ts` exports if signatures change publicly.
7. Verify `npm run typecheck`, `npm run lint`, `npm run format:check`,
   `npm run test:browser`, `npm run test:node` all pass.

## Triage

**Accept — Phase 8, Option A3 (coordinated with finding 018).**
