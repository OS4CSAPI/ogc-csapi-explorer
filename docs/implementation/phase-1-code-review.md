# Phase 1 Code Review Report

**Date:** February 14, 2026  
**Reviewer:** AI (GitHub Copilot)  
**Scope:** All Phase 1 deliverables (Issues #1–#4)  
**Commits:** `b5ae216`, `cbdd601`, `b3b7c18`, `0ae92fc`

---

## Verification Status

| Check                         | Result    |
| ----------------------------- | --------- |
| 76 CSAPI unit tests           | **PASS**  |
| 6 integration tests           | **PASS**  |
| ESLint (all 6 modified files) | **CLEAN** |
| `tsc --noEmit` (full project) | **CLEAN** |

---

## Files Reviewed

### Issue #1 — Type System

- `src/ogc-api/csapi/model.ts` (582 lines)
- `src/ogc-api/csapi/model.spec.ts` (383 lines, 27 tests)

### Issue #2 — Helper Utilities

- `src/ogc-api/csapi/helpers.ts` (164 lines)
- `src/ogc-api/csapi/helpers.spec.ts` (30 tests)

### Issue #3 — Stub QueryBuilder

- `src/ogc-api/csapi/url_builder.ts` (211 lines)
- `src/ogc-api/csapi/url_builder.spec.ts` (19 tests)

### Issue #4 — OgcApiEndpoint Integration

- `src/ogc-api/info.ts` (+31 lines)
- `src/ogc-api/endpoint.ts` (+52 lines)
- `src/index.ts` (+25 lines)
- `src/ogc-api/endpoint.spec.ts` (+53 lines, 6 tests)
- `fixtures/ogc-api/csapi/` (4 fixture files)

---

## Findings

### [F1] BUG: `allCollections` return type is stale

**File:** `src/ogc-api/endpoint.ts` lines 170–180  
**Severity:** Minor

The `allCollections` getter has a hardcoded return type that doesn't include `hasConnectedSystems`:

```typescript
get allCollections(): Promise<
  {
    name: string;
    hasRecords?: boolean;
    hasFeatures?: boolean;
    hasVectorTiles?: boolean;
    hasMapTiles?: boolean;
    hasDataQueries?: boolean;
    // MISSING: hasConnectedSystems?: boolean;
  }[]
>
```

`parseCollections()` in `info.ts` now returns objects _with_ `hasConnectedSystems`, but the getter's explicit type annotation strips it. Consumers calling `allCollections` won't see the flag.

**Recommendation:** Add `hasConnectedSystems?: boolean` to the return type annotation. One-line fix.

---

### [F2] DESIGN: `as unknown as OgcApiCollectionInfo` cast in `csapi()` factory

**File:** `src/ogc-api/endpoint.ts` lines 340–341  
**Severity:** Low risk, documented

The `csapi()` factory uses `getCollectionDocument` (raw doc with links intact) instead of `getCollectionInfo` (which strips links via `parseBaseCollectionInfo`). This requires a double cast:

```typescript
const collectionDoc = await this.getCollectionDocument(collectionId);
const result = new CSAPIQueryBuilder(
  collectionDoc as unknown as OgcApiCollectionInfo
);
```

This is a necessary workaround — the comment in the code explains the rationale clearly, and the tests prove it works. However, `CSAPIQueryBuilder` receives a raw `OgcApiDocument` typed as `OgcApiCollectionInfo`.

**Recommendation:** No action needed now. In Phase 2, consider a dedicated `CSAPICollectionInfo` type or adjusting the constructor parameter to `OgcApiDocument` if we ever need typed `OgcApiCollectionInfo` properties (like `itemFormats`, `crs`) inside the builder.

---

### [F3] CONSISTENCY: Pre-existing EDR `edr()` doesn't await conformance check

**File:** `src/ogc-api/endpoint.ts` line 312  
**Severity:** Informational (pre-existing, not our code)

The existing EDR factory does:

```typescript
if (!this.hasEnvironmentalDataRetrieval) {  // Bug: no await — truthy Promise always passes
```

Our `csapi()` correctly awaits:

```typescript
if (!(await this.hasConnectedSystems)) {
```

**Recommendation:** No action needed — pre-existing issue, not introduced by Phase 1. Documented here for awareness.

---

### [F4] MISSING: Collection types not exported from `index.ts`

**File:** `src/index.ts`  
**Severity:** Low

The following types are defined in `model.ts` but not exported from the library's public API:

- `FeatureCollection<T>`, `ItemCollection<T>` (generic collection wrappers)
- `SystemCollection`, `DeploymentCollection`, etc. (convenience type aliases)
- `CSAPIResourceTypes` (const array — useful for runtime validation)
- `CommandStatusCodes`, `SystemTypeUris` (const arrays)
- `ProcedureQueryOptions`, `SamplingFeatureQueryOptions`, `PropertyQueryOptions` (type aliases)

**Recommendation:** Revisit in Phase 2 when the builder returns parsed data. Collection types and const arrays will likely be needed by downstream consumers.

---

### [F5] BUG: `buildQueryString` double-encodes array values

**File:** `src/ogc-api/csapi/url_builder.ts` line 148  
**Severity:** Medium

When handling array values:

```typescript
} else if (Array.isArray(value)) {
  params.append(key, encodeArrayParameter(value));
}
```

`encodeArrayParameter()` already calls `encodeURIComponent()` on each value, then `URLSearchParams.append()` percent-encodes the whole string again. A value like `sys 001` would become `sys%2520001` (double-encoded).

Current tests pass because test IDs (`sys-001`, `sys-002`) contain no special characters. A real ID with spaces or colons would be double-encoded.

**Recommendation:** Fix at the start of Phase 2 — change `encodeArrayParameter` to join without encoding, or skip `encodeArrayParameter` in `buildQueryString` and just do `value.join(',')`.

---

### [F6] STYLE: Temporal parameter keys are hardcoded

**File:** `src/ogc-api/csapi/url_builder.ts` line 141  
**Severity:** Low

```typescript
if (key === 'datetime' || key === 'phenomenonTime' || key === 'resultTime' || key === 'issueTime' || key === 'executionTime') {
```

This is functional but fragile. If a new temporal parameter is added in Phase 2, it could be missed here.

**Recommendation:** Consider a set-based approach (`const TEMPORAL_KEYS = new Set([...])`) or a type guard when expanding in Phase 2.

---

### [F7] GOOD: Defensive link parsing in `parseCollections`

**File:** `src/ogc-api/info.ts` lines 293–302

The Connected Systems detection correctly includes both `Array.isArray(collection.links)` and `typeof link.rel === 'string'` guards, which is more defensive than pre-existing tile/map checks that assume `links` exists.

---

### [F8] GOOD: Model types match OGC spec

Cross-checked against the implementation guide and OGC Connected Systems Parts 1 & 2:

- All 9 resource types present with correct required/optional fields
- `Property` is correctly modeled as flat SWE object (not GeoJSON Feature)
- `Procedure.geometry` is correctly typed as `null`
- `Deployment.validTime` is correctly `required` (not optional)
- All Part 2 temporal fields use ISO string format (not Date objects) for `Observation`/`Command`
- Collection wrapper types correctly distinguish `FeatureCollection<T>` (Part 1 GeoJSON) from `ItemCollection<T>` (Part 2 non-GeoJSON)

---

### [F9] GOOD: Test quality

- Tests cover happy paths, error paths, and edge cases (empty arrays, NaN, Infinity, special characters)
- Integration tests verify the full fetch → parse → build chain
- Cache test uses spy correctly (on private `getCollectionDocument` method)
- Non-CSAPI endpoint test verifies proper rejection with `EndpointError`
- Model tests verify both required and optional field contracts for all resource types

---

## Summary

| Category                   | Count | Items                                                              |
| -------------------------- | ----- | ------------------------------------------------------------------ |
| Bug to fix now             | **1** | F1 — `allCollections` missing `hasConnectedSystems` in return type |
| Bug to fix in Phase 2      | **1** | F5 — Double-encoding in array params                               |
| Design notes (no action)   | **3** | F2 (cast), F3 (pre-existing EDR bug), F6 (hardcoded temporal keys) |
| Gaps to revisit in Phase 2 | **1** | F4 — Missing collection type exports                               |
| Positive findings          | **3** | F7 (defensive parsing), F8 (spec compliance), F9 (test quality)    |

---

## Recommendation

Fix **F1** immediately (1-line change to add `hasConnectedSystems?: boolean` to the `allCollections` return type). Address **F5** (double-encoding) at the start of Phase 2 when expanding the builder methods. All other findings are informational or deferred.

Overall assessment: **Phase 1 is solid.** The code follows upstream patterns, types match the OGC spec, tests are thorough, and the integration is clean.
