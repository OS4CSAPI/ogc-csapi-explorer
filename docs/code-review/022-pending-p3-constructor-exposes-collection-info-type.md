---
status: pending
priority: p3
issue_id: '022'
tags: [code-review, api-design, type-safety]
dependencies: []
phase: 8
---

# `CSAPIQueryBuilder` Constructor Exposes Internal `OgcApiCollectionInfo` Type

## Problem Statement

The public `CSAPIQueryBuilder` constructor takes a `Pick<OgcApiCollectionInfo, 'id' | 'title' | 'links'>`. The `Pick<>` limits the field surface, but the type
name `OgcApiCollectionInfo` is an internal model imported from
`src/ogc-api/model.js`. Consumers who construct a builder directly (bypassing
`createCSAPIBuilder`) must import an internal type from a non-sub-path module.
Refactors of `OgcApiCollectionInfo` (rename, field changes) become breaking
changes to the CSAPI public API.

## Findings

**File:** `src/ogc-api/csapi/url_builder.ts`, **line 222**

```ts
constructor(
  private collection_: Pick<OgcApiCollectionInfo, 'id' | 'title' | 'links'>,
  resourceUrls?: Map<string, string>
) { ... }
```

Most consumers call `createCSAPIBuilder(endpoint, id)` and never see the
constructor signature. Direct constructor use is documented in `url_builder.ts`
JSDoc as the workaround for servers that don't advertise CSAPI links.

## Proposed Solutions

### Option A: Define a public `CSAPICollectionRef` interface (Recommended)

In `src/ogc-api/csapi/model.ts`:

```ts
export interface CSAPICollectionRef {
  id: string;
  title?: string;
  links: ResourceLink[];
}
```

Update `CSAPIQueryBuilder`'s constructor signature and export the type from
`csapi/index.ts`. The internal `OgcApiCollectionInfo` is no longer part of the
CSAPI public API surface.

**Effort:** Small | **Risk:** None (structural compatibility — `Pick<>` is
already structurally identical to the proposed shape)

### Option B: Mark constructor `@internal` and require `createCSAPIBuilder`

More restrictive. Would break the documented direct-construction workaround
for servers without CSAPI link advertisements.

## Ownership Assessment

100% ours — both files are in `src/ogc-api/csapi/`.

## Triage

**Accept — Phase 8.** Combine with finding 023 (same constructor) for a single
pass.
