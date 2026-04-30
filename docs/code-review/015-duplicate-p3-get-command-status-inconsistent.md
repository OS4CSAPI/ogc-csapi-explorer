---
status: duplicate
priority: p3
issue_id: '015'
tags: [code-review, dry, quality]
dependencies: [009]
duplicate_of: '#111'
---

# `getCommandStatus` Manually Appends Query String Instead of Using `buildResourceUrl`

> **Duplicate:** This finding is identical to Issue [#111](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/111) (F45 from Phase 5.5 code review, status: DEFERRED). It would also be auto-resolved by Issue [#145](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/145) (`build()` wrapper refactor). No new issue filed.

## Problem Statement

`getCommandStatus` is the only method in `url_builder.ts` (out of ~90) that splits URL construction into two calls — it calls `buildResourceUrl` for the path then manually appends the query string via a second `buildQueryString` call. Every other method passes `options` as the fourth argument to `buildResourceUrl`, which handles query string building internally. This inconsistency is a latent bug: if `buildResourceUrl` is ever changed to modify how URLs are assembled, `getCommandStatus` will silently diverge.

## Findings

**File:** `src/ogc-api/csapi/url_builder.ts`, **lines 2403–2409**

```typescript
// INCONSISTENT (only this method does this):
getCommandStatus(id: string, options?: CommandStatusQueryOptions): string {
  this.assertResourceAvailable('commands');
  return (
    this.buildResourceUrl('commands', id, 'status') +   // ← no options
    this.buildQueryString(options)                       // ← manually appended
  );
}

// CONSISTENT (every other method with subPath + options):
getSystemHistory(id: string, options?: QueryOptions): string {
  this.assertResourceAvailable('systems');
  return this.buildResourceUrl('systems', id, 'history', options);  // ← options as 4th arg
}
```

## Origin

The inconsistency was introduced in commit `23126d4` (Issue #106 — "Add missing Part 2 query option fields"). The original `getCommandStatus` (commit `b1c08d4`, Issue #13) had no options parameter and simply called `buildResourceUrl('commands', id, 'status')`. When options were added, the author concatenated `buildQueryString(options)` instead of passing `options` as the 4th argument to `buildResourceUrl`.

**Upstream status:** The entire `src/ogc-api/csapi/` directory is fork-only code — it does not exist in the upstream camptocamp repo. This is 100% fork-introduced.

## Proposed Solutions

### Option A: Pass `options` as the fourth arg to `buildResourceUrl` (Recommended)

```typescript
getCommandStatus(id: string, options?: CommandStatusQueryOptions): string {
  this.assertResourceAvailable('commands');
  return this.buildResourceUrl('commands', id, 'status', options);
}
```

**Effort:** Trivial | **Risk:** None (identical behavior — `buildResourceUrl` calls `buildQueryString` internally)

### Option B: Wait for Issue #145 (`build()` wrapper)

The `build()` method proposed in #145 / Finding 009 would collapse this to:

```typescript
getCommandStatus(id: string, options?: CommandStatusQueryOptions): string {
  return this.build('commands', id, 'status', options);
}
```

This resolves the inconsistency automatically as part of the broader DRY refactor.

## Recommended Action

No new issue — already tracked as Issue #111 (DEFERRED) and subsumed by Issue #145. Filed as a code-review record only to document the external reviewer's independent rediscovery.

## Technical Details

- **Affected file:** `src/ogc-api/csapi/url_builder.ts:2403–2409`
- **Dependency:** Becomes trivial after Finding 009 (`build()` wrapper) is implemented

## Acceptance Criteria

- [ ] `getCommandStatus` passes options through `buildResourceUrl` (or `build()`)
- [ ] No separate `buildQueryString` call in the method body
- [ ] URL output is identical to current behavior

## Work Log

- 2026-03-05: Identified by external reviewer during code review of `clean-pr`
- 2026-03-07: Filed as code-review record; confirmed duplicate of Issue #111 (F45)
