---
status: pending
priority: p3
issue_id: '023'
tags: [code-review, api-design, type-safety]
dependencies: []
phase: 8
---

# `availableResources` Typed as `Set<string>` Instead of `ReadonlySet<CSAPIResourceType>`

## Problem Statement

The public `availableResources` property on `CSAPIQueryBuilder` is typed as
`Set<string>`. The actual values are always members of the `CSAPIResourceType`
union (`'systems' | 'deployments' | 'procedures' | ...`), but the type
declaration doesn't reflect that. Consumers cannot type-safely iterate or
narrow the set, and the `Set` is mutable through the public reference even
though the builder maintains the invariant that it represents discovery results.

## Findings

**File:** `src/ogc-api/csapi/url_builder.ts`, **line 156**

```ts
public readonly availableResources: Set<string>;
```

`extractAvailableResources()` already only emits `CSAPIResourceType` values via
`scanCsapiLinks(links).keys()`. The `string` typing is a missed precision
opportunity.

## Proposed Solutions

### Option A: Tighten to `ReadonlySet<CSAPIResourceType>` (Recommended)

```ts
public readonly availableResources: ReadonlySet<CSAPIResourceType>;
```

- `ReadonlySet` prevents external mutation through the public reference.
- `CSAPIResourceType` lets consumers narrow on `.has()` and iterate with the
  union type.

**Effort:** Trivial (one type annotation change + verify `extractAvailableResources` return type)
**Risk:** Theoretically a tightening — if a consumer is currently passing a
custom string into `resourceUrls`, that string would no longer satisfy
`CSAPIResourceType`. In practice the `resourceUrls` constructor parameter is
documented to use known resource types only.

### Option B: Tighten to `ReadonlySet<string>` (less precise)

Cheaper to verify but doesn't get the union-type narrowing benefit.

## Ownership Assessment

100% ours.

## Triage

**Accept — Phase 8.** Bundle with finding 022 (same constructor / same file).
