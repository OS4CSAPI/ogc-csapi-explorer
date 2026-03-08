---
status: pending
priority: p2
issue_id: "007"
tags: [code-review, typescript, type-safety]
dependencies: []
---

# `extractCSAPIFeature` Casts `properties` to Record Without Null Check

## Problem Statement

`extractCSAPIFeature` in `geojson.ts` casts `feature.properties` to `Record<string, unknown>` without first checking it is a non-null object. GeoJSON RFC 7946 explicitly permits `properties: null`. If a server returns a feature with null properties, every subsequent field access (`p.featureType`, `p.uid`, `p.validTime`, etc.) throws a `TypeError` at runtime with no TypeScript warning.

## Findings

**File:** `src/ogc-api/csapi/formats/geojson.ts`, **lines 437–438**
```typescript
const f = feature as Record<string, unknown>;
const p = f.properties as Record<string, unknown>;  // ← no null check on f.properties
// ...
const featureType = p.featureType;   // ← throws if p is null
const uid = p.uid;                   // ← same
```

`isRecord` is already imported in this file and used elsewhere — it checks `typeof x === 'object' && x !== null`.

### Existing Indirect Guard (Mitigating Factor)

`extractCSAPIFeature` calls `getCSAPIResourceType(feature)` at line 430 *before* reaching line 438. That function delegates to `getFeatureType()` (line 114), which explicitly checks:

```typescript
if (typeof props !== 'object' || props === null) {
  return undefined;
}
```

If `properties` is `null`, `getFeatureType` returns `undefined`, `getCSAPIResourceType` returns `null`, and `extractCSAPIFeature` throws `"Cannot extract CSAPI feature: unrecognized or missing featureType"` at line 432 — before ever reaching line 438.

So in practice, `properties: null` features already throw before the unsafe cast. The null path is guarded indirectly. However, relying on an indirect guard in a different function is fragile — if `getCSAPIResourceType` is ever refactored to not call `getFeatureType`, the null guard silently disappears.

## Proposed Solutions

### Option A: Guard with `isRecord` before the cast (Recommended)
```typescript
const f = feature as Record<string, unknown>;
if (!isRecord(f.properties)) {
  throw new Error(
    'Cannot extract CSAPI feature: "properties" must be a non-null object'
  );
}
const p = f.properties;  // now narrowed by isRecord — no cast needed
```
**Pros:** Uses the existing `isRecord` helper; meaningful error message; TypeScript narrows correctly.
**Effort:** Small | **Risk:** None

### Option B: Return `null` / `undefined` on null properties instead of throwing
```typescript
if (!isRecord(f.properties)) return null;
```
**Pros:** Non-throwing; caller decides whether to skip the feature.
**Cons:** Callers must check for `null`; unclear if null-properties CSAPI features are ever valid.
**Effort:** Small | **Risk:** Low (changes return type)

## Recommended Action

Option A — throw with a descriptive error. A CSAPI feature with null properties is malformed; surfacing this explicitly is better than a cryptic `TypeError` three calls deep.

## Technical Details

- **Affected file:** `src/ogc-api/csapi/formats/geojson.ts:437–524`
- **All field accesses on `p` after line 438 are unsafe if `properties` is null**

## Acceptance Criteria

- [ ] A feature with `properties: null` produces a clear `Error` rather than a `TypeError`
- [ ] `isRecord` is used for the guard (consistent with rest of file)
- [ ] TypeScript narrows `p` correctly after the guard — no `as Record<string, unknown>` cast needed

## Ownership Assessment

**Ownership: OURS (OS4CSAPI)** — `src/ogc-api/csapi/formats/geojson.ts` does not exist in upstream camptocamp/ogc-client. Lines 437-438 authored by Sam-Bolling in commits `a30f5bf0` (2026-02-14) and `40bbfe54` (2026-02-15). This is entirely CSAPI code within the `csapi/` isolation boundary.

## Work Log

- 2026-03-05: Identified by TypeScript quality agent during code review of `clean-pr`
- 2026-03-06: Filed to docs/code-review/; mitigating indirect guard documented; GitHub issue filed
