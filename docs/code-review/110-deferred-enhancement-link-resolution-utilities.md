---
status: deferred
priority: enhancement
issue_id: '110'
tags: [enhancement, link-resolution, cross-reference, out-of-scope]
dependencies: ['#108', '#109', '#103']
related: []
---

# Issue #110 — `@link` / `@id` Resolution Utilities: Excluded from Phase 7 Cleanup

> **Decision:** Issue #110 is excluded from the Phase 7 code review cleanup effort. It remains open as a post-PR enhancement.

## What #110 Proposes

A new file (`src/ogc-api/csapi/link-resolution.ts`) with 4 utility functions:

1. `resolveResourceRef()` — fetch a resource from a `@link` href
2. `parseResourceRefHref()` — extract resource type + ID from an href
3. `extractCrossReferences()` — collect all `@link` / `@id` fields from raw JSON
4. `resolveWithLinkFallback()` — try server navigation, fall back to `@link`

These utilities fill a real gap: `CSAPIQueryBuilder` constructs server-side navigation URLs, but when servers return 4xx/5xx for those endpoints (as OpenSensorHub does), there is no library support for resolving the `@link` inline properties that the OGC spec defines as the universal fallback. The ogc-csapi-explorer app had to implement ~105 lines of `tryLinkFallback()` workaround code because of this gap.

## Why It's Within the Contribution's Spirit

The [contribution goal](../planning/contribution-goal-and-definition.md) states: "production-ready, **specification-complete** Connected Systems API implementation." The `@link` mechanism is defined in OGC 23-001 §16 and §8.3/8.5/8.9. A library that builds navigation URLs but cannot resolve `@link` references is arguably not specification-complete — the explorer app proved this in practice.

## Why It's Excluded from Phase 7

1. **It's new functionality, not cleanup.** The Phase 7 effort is about fixing what the senior developer's code review found and resolving pre-existing bugs in files we're already touching. #110 adds new API surface — a 25th implementation file — which is scope creep for a cleanup effort.

2. **It has unresolved dependencies.** #110 depends on #108 (add `CSAPIResourceRef` type and `@link` fields to Part 1 interfaces), #109 (extract `@link` properties in parsers), and #103 (preserve `@id`/`@link` fields in Part 2 parsers). None of these are in the Phase 7 issue list. It's a feature chain, not a standalone fix.

3. **It increases PR review surface.** The upstream draft PR (#136) is already large. Adding new utility functions with `fetch` calls and graceful degradation logic increases the review burden for the camptocamp maintainer. The cleanup effort should reduce reviewer concerns, not add new ones.

4. **The contribution definition's explicit deliverable list doesn't include it.** The definition specifies "24 implementation files" and "80-method QueryBuilder." #110 would be a 25th file with functions outside the QueryBuilder pattern.

## Recommendation

#110 should be the **first enhancement after the PR is accepted** — or contributed as a separate follow-up PR. The gap is real, the design is sound, and every consumer will benefit. But it doesn't belong in this cleanup.
