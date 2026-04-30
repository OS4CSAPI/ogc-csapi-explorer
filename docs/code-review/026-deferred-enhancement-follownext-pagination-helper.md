---
status: deferred
priority: enhancement
issue_id: '026'
tags: [code-review, api-design, enhancement, pagination]
dependencies: []
phase: 8
---

# No Pagination Helper for HATEOAS-Style `next` Link Following

## Problem Statement

`CollectionResponse<T>` already exposes everything needed for pagination
(`items`, `links`, `numberMatched`, `numberReturned`), and `QueryOptions`
supports three pagination mechanisms (`limit`+`offset`, cursor, link-following).
But the library exports no helper to **follow** the `rel: 'next'` link or
auto-iterate pages.

A consumer who wants to walk all pages must currently:

```ts
const nextLink = result.links.find((l) => l.rel === 'next');
if (nextLink) {
  const nextResponse = await fetch(nextLink.href);
  const nextResult = parseCollectionResponse(
    await nextResponse.json(),
    parseDatastream
  );
}
```

This works but is boilerplate every consumer reimplements.

## Findings

**Files:**

- `src/ogc-api/csapi/formats/response.ts` — `CollectionResponse<T>` shape and
  `parseCollectionResponse` already provide the data.
- `src/ogc-api/csapi/index.ts` — no `followNext` / `followLinks` /
  `paginate` export.

For comparison, `OgcApiEndpoint.getCollectionItems()` also has no auto-pagination —
this is a library-wide pattern, not a CSAPI-specific gap.

## Proposed Solutions (for future enhancement)

### Option 1: `followNext(result, parseItem)` helper

```ts
export async function followNext<T>(
  result: CollectionResponse<T>,
  parseItem: (raw: unknown) => T
): Promise<CollectionResponse<T> | null> {
  const next = result.links.find((l) => l.rel === 'next');
  if (!next?.href) return null;
  const response = await fetch(next.href);
  return parseCollectionResponse(await response.json(), parseItem);
}
```

### Option 2: Async iterator

```ts
for await (const page of paginate(firstResult, parseDatastream)) { ... }
```

Both designs work; Option 1 is simpler and composes with the existing
URL-builder pattern. Option 2 is more ergonomic for full-walk use cases.

## Triage

**Defer — tracked for follow-up.**

Rationale:

- Matches the [#110 deferral precedent](110-deferred-enhancement-link-resolution-utilities.md)
  — new functionality, not cleanup.
- Pairs naturally with #110 (link-resolution utilities) as part of a unified
  "navigation helpers" follow-up PR.
- Adding a `fetch`-using helper into a library that has so far been
  HTTP-call-free is a design decision worth discussing with the upstream
  maintainer rather than landing inside a cleanup PR.

## Recommendation

Open as a GitHub issue **after** PR #136 merges, scoped jointly with #110
(link resolution) as a "CSAPI navigation utilities" follow-up package.
