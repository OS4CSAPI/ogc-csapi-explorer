# Issue #109 Findings Report — Part 1 `extractCSAPIFeature()` Silently Drops All `@link` Properties During Parsing

> **Date:** 2026-02-21
> **Issue:** [OS4CSAPI/ogc-client-CSAPI_2#109](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/109) — "Part 1 `extractCSAPIFeature()` silently drops all `@link` properties during parsing"
> **Repository under review:** `OS4CSAPI/ogc-client-CSAPI_2` (`src/ogc-api/csapi/formats/geojson.ts`, `src/ogc-api/csapi/formats/geojson.spec.ts`)
> **Discovered by:** [ogc-csapi-explorer `tryLinkFallback()` workaround](https://github.com/OS4CSAPI/ogc-csapi-explorer/commit/ad06b52), [Gap Analysis Report](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/csapi-link-property-gap-analysis.md) > **Labels:** enhancement, parser
> **Dependency:** This issue depends on #108 (interface fields) — **already resolved** as of commit `f8026ea`.

---

## Table of Contents

1. [AI Operational Constraints Acknowledgment](#1-ai-operational-constraints-acknowledgment)
2. [Executive Summary](#2-executive-summary)
3. [Issue Description](#3-issue-description)
4. [Source Code Review](#4-source-code-review)
5. [Precedent Review — Issue #103 Part 2 Parser Fix](#5-precedent-review--issue-103-part-2-parser-fix)
6. [Risk Assessment](#6-risk-assessment)
7. [Recommendation](#7-recommendation)
8. [Appendix A: Authority Precedence Analysis](#appendix-a-authority-precedence-analysis)
9. [Appendix B: Scope Boundary — What This Issue Does NOT Cover](#appendix-b-scope-boundary--what-this-issue-does-not-cover)

---

## 1. AI Operational Constraints Acknowledgment

Per the [AI Operational Constraints](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/governance/AI_OPERATIONAL_CONSTRAINTS.md), this review follows the required authority precedence:

1. **OGC specifications** (OGC 23-001 Part 1) — primary authority
2. **AI Collaboration Agreement** — governing constraints
3. **Issue description** — task scope
4. **Existing code patterns** — implementation precedent
5. **Conversation context** — supplementary guidance

This report does not expand scope beyond what Issue #109 describes. Per §2.1 (do not infer unstated requirements), §2.2 (preserve existing patterns, prefer minimal diffs), and §2.3 (no refactoring for style), this report evaluates the existing parser against the OGC specification and provides a risk-calibrated recommendation.

---

## 2. Executive Summary

**Issue #109 identifies a genuine parser gap — `extractCSAPIFeature()` in `geojson.ts` uses a property-name allowlist that silently discards all `@link` association properties from server JSON. The fix is minimal (~15 lines of new extraction code + 2 private helper functions), follows the exact same tolerant-extraction pattern already proven in the Part 2 parsers (Issue #103), and is fully backward-compatible because every new field is optional and defaults to `undefined` when absent.**

**Critically, the prerequisite is already satisfied:** Issue #108 (adding `CSAPIResourceRef` and `@link`-derived fields to the interfaces) was resolved in commit `f8026ea`. The interfaces now define the target fields — the parser just needs to populate them.

| Finding     | Description                                                                                                       | Severity                   | Recommendation                                                                   |
| ----------- | ----------------------------------------------------------------------------------------------------------------- | -------------------------- | -------------------------------------------------------------------------------- |
| **F-109.1** | `extractCSAPIFeature()` uses a property-name allowlist that discards all `@link` data from raw JSON               | **SPEC GAP**               | **FIX** — add `@link` extraction to each `switch` case                           |
| **F-109.2** | The stripping is **implicit** (allowlist), not explicit (no JSDoc saying "intentionally ignored")                 | **UNINTENTIONAL OMISSION** | Was a scope boundary during initial development, not a deliberate design choice  |
| **F-109.3** | Existing tests include `@link` data in test inputs but never assert it survives extraction                        | **TEST GAP**               | FIX — add assertions that `@link` fields are preserved when present              |
| **F-109.4** | Proposed fix follows the identical pattern already proven in Part 2 parsers (`part2.ts` L163–164, L256–257)       | **ESTABLISHED PATTERN**    | Same `typeof`/conditional-spread approach — zero new abstractions                |
| **F-109.5** | Two small private helper functions (`isCSAPIResourceRef()` and `parseResourceRef()`) encapsulate validation logic | **MINIMAL NEW CODE**       | Localized, testable, no architectural changes                                    |
| **F-109.6** | All new fields are optional (`?`) — existing tests pass unchanged                                                 | **ZERO BREAKAGE RISK**     | Additive extraction only                                                         |
| **F-109.7** | `deployedSystems@link` requires array handling (unlike all other scalar `@link` fields)                           | **ARRAY CASE**             | Use `.filter(isCSAPIResourceRef).map(parseResourceRef)` — same defensive pattern |

**Conclusion:** This is the parser half of the gap identified in #108 (interfaces). The fix is minimal, follows established precedent, and carries effectively zero risk. The contribution goal explicitly calls for "GeoJSON extensions recognizing all CSAPI-specific resource types **and properties**." Recommend fixing with careful implementation.

---

## 3. Issue Description

Issue #109 reports that `extractCSAPIFeature()` (the sole parser for Part 1 GeoJSON resources) builds return objects using an explicit property-name allowlist: only `featureType`, `uid`, `name`, `description`, `assetType`, and `validTime` are extracted. All `@link` properties in the raw JSON `properties` object are silently discarded because they are never referenced by name.

### `@link` Properties Being Dropped

| Resource Type   | Dropped Property | Server JSON Key        | Interface Field (from #108)                |
| --------------- | ---------------- | ---------------------- | ------------------------------------------ |
| System          | Procedure link   | `systemKind@link`      | `systemKindLink?: CSAPIResourceRef`        |
| Deployment      | Platform link    | `platform@link`        | `platformLink?: CSAPIResourceRef`          |
| Deployment      | Deployed systems | `deployedSystems@link` | `deployedSystemsLink?: CSAPIResourceRef[]` |
| SamplingFeature | Sampled feature  | `sampledFeature@link`  | `sampledFeatureLink?: CSAPIResourceRef`    |

### Real-World Discovery

The [ogc-csapi-explorer](https://github.com/OS4CSAPI/ogc-csapi-explorer) demo app encountered this gap when OSH SensorHub — a conformant CS API server — returns `400 Bad Request` for cross-resource navigation endpoints (`/systems/{id}/procedures`), making `@link` properties the **only** mechanism for discovering resource associations. The explorer had to implement `tryLinkFallback()` ([commit ad06b52](https://github.com/OS4CSAPI/ogc-csapi-explorer/commit/ad06b52), ~105 lines) that bypasses the library's typed models and reads `@link` fields from raw JSON.

---

## 4. Source Code Review

### 4.1 Current Parser — Allowlist Extraction

The `extractCSAPIFeature()` function ([geojson.ts L393–472](src/ogc-api/csapi/formats/geojson.ts#L393-L472)) builds return objects in a `switch` statement with four cases. Each case constructs the return object via explicit field listings — only named properties survive. The `satisfies Type` keyword enforces that the returned object conforms to the interface.

**System case (L429–440):**

```typescript
case 'System':
  return {
    id: String(f.id ?? ''),
    type: 'Feature',
    properties: {
      ...baseProperties,
      ...(typeof p.assetType === 'string' ? { assetType: p.assetType as System['properties']['assetType'] } : {}),
      ...(validTime !== undefined ? { validTime } : {}),
      // ← systemKind@link is in `p` but never read
    },
    ...(geometry !== undefined ? { geometry } : {}),
    links,
  } satisfies System;
```

The raw properties object `p` has all the `@link` data from the server, but the parser never accesses `p['systemKind@link']`, `p['platform@link']`, `p['deployedSystems@link']`, or `p['sampledFeature@link']`.

### 4.2 Current Imports — `CSAPIResourceRef` Not Yet Imported

The `geojson.ts` import block ([L13–21](src/ogc-api/csapi/formats/geojson.ts#L13-L21)) currently imports:

```typescript
import type {
  System,
  Deployment,
  Procedure,
  SamplingFeature,
  ResourceLink,
  TimeInterval,
} from '../model.js';
```

`CSAPIResourceRef` (added in #108) is not yet imported — it will need to be added to this import statement.

### 4.3 Existing Tests Already Include `@link` Data — But Don't Assert Survival

Two test cases in [geojson.spec.ts](src/ogc-api/csapi/formats/geojson.spec.ts) provide raw input with `sampledFeature@link`:

**Test 1 — "extracts a SamplingFeature" (L431–440):**

```typescript
it('extracts a SamplingFeature', () => {
  const raw = makeFeature('sosa:SamplingFeature', {
    geometry: { type: 'Point', coordinates: [12.31, -86.98, -21] },
    'sampledFeature@link': { href: 'http://example.com/feature/1' },
  });
  const result = extractCSAPIFeature(raw);
  expect(result.properties.featureType).toBe('sosa:SamplingFeature');
  expect(result.geometry).toEqual({
    type: 'Point',
    coordinates: [12.31, -86.98, -21],
  });
  // ← no assertion that sampledFeatureLink survived
});
```

**Test 2 — "extracts SamplingFeature without sampledFeature@link (tolerant extraction)" (L499–505):**
This test verifies the parser tolerates _missing_ `@link` data — but doesn't test that _present_ `@link` data survives.

The test infrastructure (`makeFeature()`) already supports passing `@link` data via `extraProps` spread — the raw input includes it in `properties`, mirrors real server JSON. No test infrastructure changes needed.

### 4.4 The `satisfies` Keyword Accommodates Optional Fields

Each parser case uses `satisfies Type` (e.g., `satisfies System`). Since `systemKindLink`, `platformLink`, `deployedSystemsLink`, and `sampledFeatureLink` are all optional in their respective interfaces, the `satisfies` constraint will **accept** the return object whether or not the new fields are present. This is the same behavior that allows `validTime` and `description` to be conditionally included today.

### 4.5 What the Fix Looks Like

The fix adds conditional extraction lines to three of the four `switch` cases (Procedure has no `@link` fields). Each line follows the established tolerant-extraction pattern:

**For scalar `@link` fields:**

```typescript
...(isCSAPIResourceRef(p['systemKind@link'])
  ? { systemKindLink: parseResourceRef(p['systemKind@link']) }
  : {}),
```

**For array `@link` fields (`deployedSystems@link`):**

```typescript
...(Array.isArray(p['deployedSystems@link'])
  ? { deployedSystemsLink: (p['deployedSystems@link'] as unknown[]).filter(isCSAPIResourceRef).map(parseResourceRef) }
  : {}),
```

**Two private helper functions (~10 lines total):**

```typescript
/** Type guard for @link objects — validates href is a string. */
function isCSAPIResourceRef(value: unknown): value is Record<string, unknown> {
  return (
    typeof value === 'object' &&
    value !== null &&
    typeof (value as any).href === 'string'
  );
}

/** Parse a raw @link object into a typed CSAPIResourceRef. */
function parseResourceRef(raw: Record<string, unknown>): CSAPIResourceRef {
  return {
    href: String(raw.href),
    ...(typeof raw.uid === 'string' ? { uid: raw.uid } : {}),
    ...(typeof raw.title === 'string' ? { title: raw.title } : {}),
    ...(typeof raw.rt === 'string' ? { rt: raw.rt } : {}),
  };
}
```

---

## 5. Precedent Review — Issue #103 Part 2 Parser Fix

Issue #103 (resolved, commit `23126d4`) added `@id` cross-reference field extraction to the Part 2 parsers. The approach is identical in structure:

### Part 2 Pattern (already in production)

**`parseDatastream()` in `part2.ts` (L163–164):**

```typescript
...(typeof obj['system@id'] === 'string'
  ? { systemId: obj['system@id'] as string }
  : {}),
```

**`parseControlStream()` in `part2.ts` (L256–257):**

```typescript
...(typeof obj['system@id'] === 'string'
  ? { systemId: obj['system@id'] as string }
  : {}),
```

### Comparison: Part 2 `@id` vs Part 1 `@link`

| Dimension           | Part 2 `@id` (Issue #103)   | Part 1 `@link` (Issue #109)                   |
| ------------------- | --------------------------- | --------------------------------------------- |
| Value type          | Scalar string               | Structured object `{href, uid?, title?, rt?}` |
| Validation          | `typeof === 'string'`       | `typeof === 'object' && href is string`       |
| Extraction          | Direct string assignment    | Object construction with field validation     |
| Array case          | None                        | `deployedSystems@link` only                   |
| Tolerant extraction | Yes — `undefined` if absent | Yes — `undefined` if absent                   |
| Pattern             | Conditional spread          | Same conditional spread                       |
| Helper functions    | None needed (scalar)        | `isCSAPIResourceRef()` + `parseResourceRef()` |

The Part 1 fix is slightly more involved because `@link` values are objects (not scalars), requiring a type guard and parser function. But the overall approach — conditional spread with tolerant extraction — is identical.

---

## 6. Risk Assessment

### 6.1 Change Inventory

| Change                                                | File                                | Lines Changed | Risk                                              |
| ----------------------------------------------------- | ----------------------------------- | ------------- | ------------------------------------------------- |
| Add `CSAPIResourceRef` to import statement            | `geojson.ts` L13–21                 | +1 line       | **NONE** — additive import                        |
| Add `isCSAPIResourceRef()` helper                     | `geojson.ts` (new private function) | ~3 lines      | **NONE** — private, used only internally          |
| Add `parseResourceRef()` helper                       | `geojson.ts` (new private function) | ~7 lines      | **NONE** — private, used only internally          |
| Extract `systemKind@link` in System case              | `geojson.ts` L435 area              | +3 lines      | **NONE** — conditional spread, optional field     |
| Extract `platform@link` in Deployment case            | `geojson.ts` L448 area              | +3 lines      | **NONE** — conditional spread, optional field     |
| Extract `deployedSystems@link` in Deployment case     | `geojson.ts` L448 area              | +3 lines      | **LOW** — array case needs `.filter().map()`      |
| Extract `sampledFeature@link` in SamplingFeature case | `geojson.ts` L465 area              | +3 lines      | **NONE** — conditional spread, optional field     |
| Add test assertions                                   | `geojson.spec.ts`                   | ~30–50 lines  | **NONE** — new test cases, no changes to existing |

### 6.2 What Does NOT Change

- **No method signatures change** — `extractCSAPIFeature()` still accepts `unknown` and returns the same union type
- **No existing extraction is altered** — all six existing property extractions remain byte-for-byte identical
- **No existing tests need updating** — adding optional fields to the return object does not break any existing assertion
- **No new dependencies** — `CSAPIResourceRef` is already in `model.ts` (from #108)
- **No architectural changes** — two private helper functions within the same file, no new modules
- **No export surface changes** — helpers are private, not exported

### 6.3 Why This Is Safe

1. **Conditional spread with `undefined` default:** If a `@link` field is missing from the server JSON, the conditional spread produces `{}` (empty object), and the optional interface field remains `undefined`. This is the same pattern used for `description`, `validTime`, and `assetType`.

2. **`satisfies` is compatible:** The `satisfies System` / `satisfies Deployment` / `satisfies SamplingFeature` constraints accept the return object whether or not the optional `@link` fields are present.

3. **No runtime behavior change for existing consumers:** Code that doesn't read `systemKindLink`, `platformLink`, `deployedSystemsLink`, or `sampledFeatureLink` is completely unaffected.

4. **Type guard validates input:** `isCSAPIResourceRef()` checks `typeof value === 'object' && value !== null && typeof (value as any).href === 'string'` before constructing the output. Malformed `@link` data (missing `href`, non-object, etc.) is silently skipped — following the Postel's Law principle already established in the parser.

5. **Proven pattern:** The identical approach (conditional spread for cross-reference fields) has been in production for Part 2 parsers since Issue #103 was resolved.

### 6.4 Contribution Scope Alignment

The [Contribution Goal and Definition](docs/planning/contribution-goal-and-definition.md) states:

> _"GeoJSON extensions recognizing all CSAPI-specific resource types **and properties**"_

`@link` properties are spec-defined properties on Part 1 GeoJSON resources. The parser currently recognizes the resource types correctly but does not recognize all properties.

---

## 7. Recommendation

### Verdict: **FIX — Add `@link` extraction to `extractCSAPIFeature()`**

This is the parser half of the gap identified in #108 (interfaces, now resolved). The fix:

1. **Is spec-driven** — OGC 23-001 §16 defines `@link` inline properties for Part 1 GeoJSON resources
2. **Follows established precedent** — identical conditional-spread pattern used in Part 2 parsers (Issue #103)
3. **Is minimal** — ~15 lines of extraction code + ~10 lines for two private helper functions
4. **Is backward-compatible** — all new fields are optional; existing code is unaffected
5. **Has zero risk to existing tests** — 69 existing `geojson.spec.ts` tests pass unchanged
6. **Addresses a real-world consumer pain point** — the ogc-csapi-explorer had to implement a 105-line workaround

### Implementation Scope

| Component            | What to Change                                                                                          |
| -------------------- | ------------------------------------------------------------------------------------------------------- |
| `geojson.ts` import  | Add `CSAPIResourceRef` to the import from `../model.js`                                                 |
| `geojson.ts` helpers | Add `isCSAPIResourceRef()` type guard and `parseResourceRef()` parser (private)                         |
| System case          | Add `systemKind@link` → `systemKindLink` extraction                                                     |
| Deployment case      | Add `platform@link` → `platformLink` and `deployedSystems@link` → `deployedSystemsLink` extraction      |
| SamplingFeature case | Add `sampledFeature@link` → `sampledFeatureLink` extraction                                             |
| Procedure case       | **No change** — Procedure has no spec-defined `@link` properties                                        |
| `geojson.spec.ts`    | Add test assertions that `@link` fields survive extraction when present and are `undefined` when absent |

### Testing Expectations

New test assertions should cover:

1. **System with `systemKind@link`** — extracted to `systemKindLink`
2. **System without `systemKind@link`** — `systemKindLink` is `undefined`
3. **Deployment with `platform@link`** — extracted to `platformLink`
4. **Deployment with `deployedSystems@link` (array)** — extracted to `deployedSystemsLink[]`
5. **SamplingFeature with `sampledFeature@link`** — extracted to `sampledFeatureLink`
6. **SamplingFeature without `sampledFeature@link`** — already tested (L499), `sampledFeatureLink` is `undefined`
7. **Malformed `@link` (missing `href`)** — silently skipped, field is `undefined`

---

## Appendix A: Authority Precedence Analysis

| Level       | Source                                        | Says                                                                     | Supports Fix?                                |
| ----------- | --------------------------------------------- | ------------------------------------------------------------------------ | -------------------------------------------- |
| 1 (highest) | OGC 23-001 §8.3, §8.5, §8.9, §16              | `@link` properties are spec-defined fields on Part 1 GeoJSON resources   | **YES**                                      |
| 2           | AI Operational Constraints                    | §2.2: Preserve patterns, prefer minimal diffs                            | **YES** — follows established Part 2 pattern |
| 3           | Issue #109 description                        | Extract `@link` properties in `extractCSAPIFeature()`                    | **YES** — clear scope                        |
| 4           | Existing code (`part2.ts` L163–164, L256–257) | Part 2 parsers already extract cross-reference fields using same pattern | **YES** — proven precedent                   |
| 5           | Explorer workaround (ad06b52)                 | Consumers must bypass typed models to access `@link` data                | **YES** — real-world impact confirmed        |

No authority level contradicts the fix. All five levels support it.

---

## Appendix B: Scope Boundary — What This Issue Does NOT Cover

Per AI Operational Constraints §2.1 (do not expand scope beyond the issue description), the following items are explicitly **out of scope** for Issue #109:

| Out-of-Scope Item                         | Why                                                                                                                                   | Tracked In                                                                 |
| ----------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------- |
| Interface changes to `model.ts`           | Already resolved in #108 (commit `f8026ea`)                                                                                           | [#108](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/108) (closed) |
| `@link` resolution utility functions      | Higher-level consumer API — depends on both #108 and #109                                                                             | [#110](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/110)          |
| Part 2 `@link` fields                     | Part 2 resources have `@link` variants — tracked separately                                                                           | Future issue                                                               |
| Changes to `ResourceLink` / HATEOAS links | Different type, different purpose                                                                                                     | N/A                                                                        |
| Changes to `Procedure` parser case        | No spec-defined `@link` properties for Procedure                                                                                      | N/A                                                                        |
| Refactoring `baseProperties` extraction   | §2.3 — no refactoring for style                                                                                                       | N/A                                                                        |
| Adding `parent@link` to System            | Issue #109 lists `parent@link` but #108 did not add a `parentLink` interface field for it — out of scope unless interface is extended | Needs discussion                                                           |

### Note on `parent@link`

Issue #109 mentions `parent@link` (System → parent system for hierarchical systems) in its "What Is Dropped" table. However, Issue #108 did not add a `parentLink` field to the `System` interface — it only added `systemKindLink`. The `parent@link` field represents the parent in a hierarchical system tree, which is a separate association from the procedure link.

**Assessment:** Since no interface field for `parentLink` exists, the parser cannot extract it. Adding a `parentLink` field would be an interface change beyond the scope of Issue #109. This should be tracked separately if desired. This does NOT block the fix for the four `@link` fields that DO have interface targets.

---

## Linked References

- [AI Operational Constraints](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/governance/AI_OPERATIONAL_CONSTRAINTS.md)
- [Contribution Goal and Definition](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/planning/contribution-goal-and-definition.md)
- [Issue #108 — Part 1 interfaces omit `@link` fields](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/108) (closed, resolved — commit `f8026ea`)
- [Issue #108 Findings Report](docs/testing/demo-app-findings/issue-108-part1-geojson-link-properties.md)
- [Issue #103 — Part 2 cross-reference fields](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/103) (closed, resolved — the Part 2 precedent)
- [Issue #103 Findings Report](docs/testing/demo-app-findings/issue-103-part2-cross-reference-fields.md)
- [Issue #110 — No `@link` resolution utilities](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/110) (downstream dependency)
- [Gap Analysis Report](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/csapi-link-property-gap-analysis.md) — Full audit of all `@link` gaps
- [ogc-csapi-explorer `tryLinkFallback()` workaround (ad06b52)](https://github.com/OS4CSAPI/ogc-csapi-explorer/commit/ad06b52)
- OGC 23-001 §8.3 (Table 8) — System resource model
- OGC 23-001 §8.5 (Table 10) — Deployment resource model
- OGC 23-001 §8.9 (Table 14) — SamplingFeature resource model
- OGC 23-001 §16 — JSON encoding for Part 1 GeoJSON resources
