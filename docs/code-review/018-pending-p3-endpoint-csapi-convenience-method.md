---
status: accepted
priority: p3
issue_id: '018'
tags: [code-review, api-design, ergonomics]
dependencies: []
phase: 8
coordinated-with: ['024']
---

# Asymmetry: `endpoint.edr(id)` vs `createCSAPIBuilder(endpoint, id)`

## Problem Statement

EDR exposes its query builder as a method on `OgcApiEndpoint`:

```ts
const builder = endpoint.edr(collectionId);
```

CSAPI exposes its builder as a standalone factory function imported from a
sub-path:

```ts
import { createCSAPIBuilder } from '@camptocamp/ogc-client/csapi';
const builder = await createCSAPIBuilder(endpoint, collectionId);
```

Both solve the same problem; the asymmetry hurts discoverability. A consumer
exploring `OgcApiEndpoint` in their IDE won't find the CSAPI entry point.

## Findings

**Files:**

- `src/ogc-api/endpoint.ts` (no `csapi()` method exists)
- `src/ogc-api/csapi/factory.ts` (the standalone factory)
- EDR comparison: `endpoint.edr()` is defined on `OgcApiEndpoint`

The sub-path import (`@camptocamp/ogc-client/csapi`) is intentional and
should remain — it preserves tree-shaking and mirrors the OGC Part 1 / Part 2
split. The fix is **additive**, not a replacement.

## Proposed Solutions

### Option A: Add `endpoint.csapi(id)` as a thin wrapper (Recommended)

Add a method on `OgcApiEndpoint` that delegates to `createCSAPIBuilder`:

```ts
public async csapi(collectionId: string): Promise<CSAPIQueryBuilder> {
  if (!(await this.hasConnectedSystems)) {
    throw new EndpointError('Endpoint does not support Connected Systems');
  }
  const collection = await this.getCollectionInfo(collectionId);
  const rootDoc = await this.root; // private access (after 024)
  const links = Array.isArray(rootDoc?.links) ? rootDoc.links : [];
  const { createCSAPIBuilder } = await import('./csapi/factory.js');
  const { scanCsapiLinks } = await import('./csapi/helpers.js');
  return createCSAPIBuilder(collection, scanCsapiLinks(links));
}
```

A dynamic import keeps the main bundle tree-shakeable for consumers who don't
use CSAPI. The standalone `createCSAPIBuilder` remains an exported entry
point (refactored to value-shaped inputs per finding 024); `endpoint.csapi()`
is the discoverable IDE entry point that mirrors `endpoint.edr(id)`.

**Effort:** Small | **Risk:** Low (touches `endpoint.ts` — already in our diff)

### Option B: Leave as-is and document the entry point in JSDoc on `OgcApiEndpoint`

Cheaper but doesn't address discoverability for IDE users.

## Ownership Assessment

Touches `src/ogc-api/endpoint.ts` (upstream file we already modified in Phase 6
for `hasConnectedSystems`, `root`, and `getCollectionDocument`). The diff is
minimal and additive.

## Coordination with Finding 024

This finding is now treated as a single coordinated change with finding
[024](024-pending-p2-endpoint-root-publicly-exposed.md). The composition
inside `endpoint.csapi()` is the mechanism by which 024's Option A3
re-privatizes `root` and `getCollectionDocument` while still letting the
factory access what it needs. See 024 for the full investigation. Net
result: one new public method here, two members reverted to private there,
and the unsound `isCollectionInfo` cast in `factory.ts` is eliminated as a
side benefit.

## Decision

**Option A — add `endpoint.csapi(id)` thin wrapper, coordinated with 024.**
Decided April 28, 2026.

## Triage

**Accept — Phase 8 (executes together with finding 024).**
