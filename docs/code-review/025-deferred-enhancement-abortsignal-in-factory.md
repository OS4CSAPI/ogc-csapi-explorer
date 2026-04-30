---
status: deferred
priority: enhancement
issue_id: '025'
tags: [code-review, api-design, enhancement, cancellation]
dependencies: []
phase: 8
---

# `createCSAPIBuilder` Cannot Be Cancelled — No `AbortSignal` Support

## Problem Statement

`createCSAPIBuilder(endpoint, collectionId)` makes two HTTP calls during
initialization (the conformance check and the collection document fetch).
Neither can be cancelled — there is no way to pass an `AbortSignal` into the
factory. A consumer initializing a CSAPI builder during a navigation that gets
cancelled has no way to abort the in-flight requests.

The reviewer correctly observes this is the **only real HTTP-related extensibility
gap** in the design — once the builder is constructed, it makes zero further
HTTP calls, so per-request hooks are unnecessary.

## Findings

**File:** `src/ogc-api/csapi/factory.ts`

```ts
export async function createCSAPIBuilder(
  endpoint: OgcApiEndpoint,
  collectionId: string
): Promise<CSAPIQueryBuilder> {
  if (!(await endpoint.hasConnectedSystems)) { ... }
  const collectionDoc = await endpoint.getCollectionDocument(collectionId);
  const rootDoc = await endpoint.root;
  ...
}
```

No options parameter, no signal, no timeout.

## Proposed Solutions (for future enhancement)

### Add an options bag with `signal`

```ts
export async function createCSAPIBuilder(
  endpoint: OgcApiEndpoint,
  collectionId: string,
  options?: { signal?: AbortSignal }
): Promise<CSAPIQueryBuilder> { ... }
```

This is non-breaking (new optional parameter) but requires plumbing the signal
through the upstream `OgcApiEndpoint.root` and `getCollectionDocument` getters,
which currently do not accept signals. That plumbing extends to the shared
`http-utils.ts` `fetch` wrappers — a wider change than a single CSAPI commit.

## Triage

**Defer — tracked for follow-up.**

Rationale (matches the [#110 deferral precedent](110-deferred-enhancement-link-resolution-utilities.md)):

- Real gap, sound design, but it's new functionality.
- Plumbing extends beyond `csapi/` into upstream-authored fetch utilities,
  which we should not touch in a cleanup PR.
- Best handled as a follow-up enhancement after the PR is merged, ideally
  paired with a similar enhancement to `OgcApiEndpoint`'s own fetch surface.

## Recommendation

Open as a GitHub issue **after** PR #136 merges, scoped jointly with adding
`signal` support to `OgcApiEndpoint`'s loader functions.
