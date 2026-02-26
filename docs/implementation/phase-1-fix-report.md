# Phase 1 Code Review — Fix Report

**Date:** February 14, 2026  
**Scope:** Fixes for findings F1 and F5 from the Phase 1 Code Review  
**Commit:** Applied on top of `3b12df9`

---

## Summary

Two bugs identified in the Phase 1 code review were fixed prior to starting Phase 2. Both fixes were verified with passing tests, clean ESLint, and clean `tsc --noEmit`.

---

## Fix 1: `allCollections` return type missing `hasConnectedSystems` (F1)

**Finding:** The `allCollections` getter in `endpoint.ts` had a hardcoded return type annotation that did not include `hasConnectedSystems`. The underlying `parseCollections()` function was already returning objects with this flag, but the getter's type stripped it — making the field invisible to TypeScript consumers.

**File changed:** `src/ogc-api/endpoint.ts` (line 176)

**Change:** Added `hasConnectedSystems?: boolean` to the return type annotation:

```typescript
get allCollections(): Promise<
  {
    name: string;
    hasRecords?: boolean;
    hasFeatures?: boolean;
    hasVectorTiles?: boolean;
    hasMapTiles?: boolean;
    hasDataQueries?: boolean;
    hasConnectedSystems?: boolean;  // ← added
  }[]
>
```

**Impact:** Library consumers can now access `hasConnectedSystems` on collection objects returned by `allCollections` with full type safety and autocompletion.

---

## Fix 2: `buildQueryString` double-encodes array values (F5)

**Finding:** In `url_builder.ts`, the `buildQueryString` method was passing array values through `encodeArrayParameter()` (which calls `encodeURIComponent()` on each value) before passing the result to `URLSearchParams.append()` (which percent-encodes its input again). This caused double-encoding for any value containing special characters:

- Input: `{ id: ['sys 001', 'sys:002'] }`
- Before fix: `id=sys%2520001%2Csys%253A002` (double-encoded — `%20` became `%2520`)
- After fix: `id=sys+001%2Csys%3A002` (single-encoded — correct)

Existing tests passed because test IDs (`sys-001`, `sys-002`) contained no special characters, masking the bug.

**Files changed:**

| File                                    | Change                                                                                                                                                     |
| --------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `src/ogc-api/csapi/url_builder.ts`      | Replaced `encodeArrayParameter(value)` with `value.join(',')` in the array branch of `buildQueryString`. Removed unused import. Added explanatory comment. |
| `src/ogc-api/csapi/url_builder.spec.ts` | Added regression test: `'does not double-encode special characters in array values'` using IDs with spaces and colons.                                     |

**Note:** The `encodeArrayParameter()` helper function in `helpers.ts` was not changed — it remains available for standalone use where manual encoding is desired. It is simply no longer called inside `buildQueryString` since `URLSearchParams` handles encoding.

---

## Verification

| Check                                       | Result    |
| ------------------------------------------- | --------- |
| CSAPI unit tests (77 = 76 original + 1 new) | **PASS**  |
| ESLint (3 modified files)                   | **CLEAN** |
| `tsc --noEmit` (full project)               | **CLEAN** |

---

## Deferred Items

The following review findings remain deferred as planned:

| Finding                                | Status    | Action                                                          |
| -------------------------------------- | --------- | --------------------------------------------------------------- |
| F2 — `as unknown as` cast in `csapi()` | Deferred  | Revisit in Phase 2 if builder needs typed collection properties |
| F3 — EDR `edr()` missing await         | No action | Pre-existing upstream bug, not ours                             |
| F4 — Missing collection type exports   | Deferred  | Export when Phase 2 adds methods that return parsed data        |
| F6 — Hardcoded temporal keys           | Deferred  | Refactor to `Set` when adding more resource methods in Phase 2  |
| F7, F8, F9 — Positive findings         | N/A       | No action needed                                                |
