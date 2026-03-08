---
status: pending
priority: p2
issue_id: "009"
tags: [code-review, dry, architecture, url-builder]
dependencies: []
---

# `assertResourceAvailable` + `buildResourceUrl` Repeated 90 Times in `url_builder.ts`

## Problem Statement

Every one of the 90 public URL-building methods in `CSAPIQueryBuilder` follows the exact same two-line pattern:

```typescript
this.assertResourceAvailable('resourceType');
return this.buildResourceUrl('resourceType', id, subPath, options);
```

This guard-then-build sequence is repeated identically across all 90 methods. The only variation is the resource type string, the optional `id`, optional `subPath`, and optional `options`. The methods are otherwise pure delegation — no method adds logic between the guard and the URL construction.

## Findings

**File:** `src/ogc-api/csapi/url_builder.ts` (2,490 lines)

Confirmed counts via grep:
- `assertResourceAvailable` — **90 occurrences** (1 definition + 89 call sites)
- `buildResourceUrl` — **89 occurrences** (1 definition + 88 standard calls + 1 concatenation variant at `getCommandStatus`)

Representative examples of the repeated pattern:

```typescript
// Line 386 — getSystems()
getSystems(options?: SystemQueryOptions): string {
  this.assertResourceAvailable('systems');
  return this.buildResourceUrl('systems', undefined, undefined, options);
}

// Line 407 — getSystem()
getSystem(id: string, options?: QueryOptions): string {
  this.assertResourceAvailable('systems');
  return this.buildResourceUrl('systems', id, undefined, options);
}

// Line 426 — createSystem()
createSystem(): string {
  this.assertResourceAvailable('systems');
  return this.buildResourceUrl('systems');
}

// Line 2486 — cancelCommand()
cancelCommand(id: string): string {
  this.assertResourceAvailable('commands');
  return this.buildResourceUrl('commands', id, 'cancel');
}
```

All 90 public methods follow this exact pattern. The only exception is `getCommandStatus()` (line 2404) which concatenates `buildQueryString(options)` separately rather than passing `options` through `buildResourceUrl()` — tracked in issue #111.

## Ownership Assessment

**Verdict: 100% ours.**

- The file does not exist on `upstream/main` (zero commits via `git log upstream/main -- src/ogc-api/csapi/url_builder.ts`)
- All 2,489 lines authored by Sam-Bolling (`git blame --line-porcelain` → Count 2489, all "author Sam-Bolling")
- 10+ development commits visible in git log, all by Sam-Bolling

## Proposed Solutions

### Option A: Add private `build()` method that fuses guard and URL construction (Recommended)

```typescript
/**
 * Guards resource availability and constructs the URL in one step.
 * All public methods delegate to this single private method.
 */
private build(
  resourceType: string,
  id?: string,
  subPath?: string,
  options?: QueryOptions
): string {
  this.assertResourceAvailable(resourceType);
  return this.buildResourceUrl(resourceType, id, subPath, options);
}
```

All 90 public methods then become one-liners:

```typescript
getSystems(options?: SystemQueryOptions): string {
  return this.build('systems', undefined, undefined, options);
}

getSystem(id: string, options?: QueryOptions): string {
  return this.build('systems', id, undefined, options);
}

cancelCommand(id: string): string {
  return this.build('commands', id, 'cancel');
}
```

**Pros:** Eliminates ~90 lines of mechanical repetition. Single point of change if the guard logic ever changes. Every public method becomes a one-liner.
**Cons:** Adds one level of indirection. Minor — the method name `build()` must be distinct from `buildResourceUrl()`.
**Effort:** Medium (mechanical — 90 call sites to update) | **Risk:** Low (pure refactor, no behavioral change)

### Option B: ESLint lint rule to enforce the pattern

Create a custom ESLint rule that verifies every public method calls `assertResourceAvailable` before `buildResourceUrl`.

**Pros:** Catches deviations automatically in CI.
**Cons:** Does NOT reduce code. The 90-method repetition remains. Adds lint rule maintenance overhead.
**Effort:** Medium | **Risk:** Low

**Not recommended.** Linting enforces the pattern but doesn't solve the DRY violation.

## Coordination Notes

**⚠️ Must coordinate with issue #100** (`assertResourceAvailable()` overly strict for per-ID methods):
- Issue #100 proposes removing `assertResourceAvailable()` from 69 per-ID methods entirely
- If #100 is implemented first, only ~21 collection/list methods would retain the guard-then-build pattern
- The `build()` method would need to handle the asymmetry (guard for collection methods, no guard for per-ID methods)
- **Recommendation:** Resolve #100 first, then apply the `build()` fusion to the remaining methods. Or if finding 010 (CRUD groups / table-driven) is pursued, it would subsume both.

**Also related:**
- Issue #111 (`getCommandStatus` concatenation) — would be automatically resolved by the `build()` method
- Issue #102 (nested-only servers) — adds optional parent ID parameters that would interact with the `build()` method signature
- Finding 010 (CRUD groups / table-driven approach) — a table-driven refactor would make both this finding and #100 largely moot

## Recommended Action

Option A — add the private `build()` method. However, implementation should be coordinated with #100 (which should be resolved first) and considered in light of finding 010's table-driven approach.

## Technical Details

- **Affected file:** `src/ogc-api/csapi/url_builder.ts` — all 90 public methods (lines 386–2490)
- **Private methods involved:**
  - `assertResourceAvailable()` (line 355) — guard
  - `buildResourceUrl()` (line 256) — URL construction
- **Resource types covered:** systems, deployments, procedures, samplingFeatures, properties, datastreams, observations, controlStreams, commands

## Acceptance Criteria

- [ ] Private `build()` method (or equivalent fusion) is added
- [ ] All 90 public methods delegate to it (no direct `assertResourceAvailable` calls from public methods)
- [ ] `getCommandStatus()` concatenation pattern (#111) is resolved as a side effect
- [ ] All URL-builder tests pass (`url_builder.spec.ts`)
- [ ] No lint errors (`npm run lint`)
- [ ] All modified files pass `npx prettier --check`

## Work Log

- 2026-03-06: Identified by senior developer code review of `clean-pr`
- 2026-03-06: Reviewed, ownership verified (100% ours, 2489 lines all Sam-Bolling, zero upstream), coordination risks identified with #100/#102/#111
