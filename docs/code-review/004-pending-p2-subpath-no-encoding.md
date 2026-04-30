---
status: pending
priority: p2
issue_id: '004'
tags: [code-review, security, input-encoding]
dependencies: []
---

# `subPath` Appended to URLs Without Encoding or Allowlist Validation

## Problem Statement

`buildResourceUrl()` in `url_builder.ts` and `buildNestedCommandUrl()` in `command-routing.ts` both append a `subPath` parameter to URLs without encoding or validating it. All current call sites use hardcoded string literals (safe today), but the `subPath` parameter is typed as `string` with no enforcement — a future contributor passing user-controlled data here has no guard.

## Findings

**File:** `src/ogc-api/csapi/url_builder.ts`, **line 270**

```typescript
if (id) url += `/${encodeResourceId(id)}`;
if (subPath) url += `/${subPath}`; // ← no encoding, no validation
```

**File:** `src/ogc-api/csapi/command-routing.ts`, **line 160**

```typescript
if (commandId) url += `/${encodeResourceId(commandId)}`;
if (subPath) url += `/${subPath}`; // ← same pattern
```

Known sub-paths used today (all safe literals): `'subsystems'`, `'subdeployments'`, `'history'`, `'datastreams'`, `'controlstreams'`, `'samplingFeatures'`, `'procedures'`, `'status'`, `'result'`, `'cancel'`.

## Proposed Solutions

### Option A: Validate `subPath` against an allowlist (Recommended)

```typescript
const ALLOWED_SUB_PATHS = new Set([
  'history',
  'subsystems',
  'subdeployments',
  'systems',
  'deployments',
  'samplingFeatures',
  'procedures',
  'datastreams',
  'controlstreams',
  'observations',
  'commands',
  'status',
  'result',
  'cancel',
  'schema',
]);

if (subPath) {
  if (!ALLOWED_SUB_PATHS.has(subPath)) {
    throw new EndpointError(`Invalid subPath: "${subPath}"`);
  }
  url += `/${subPath}`;
}
```

**Effort:** Small | **Risk:** None (all current call sites use known-good values)

### Option B: Encode `subPath` with `encodeURIComponent`

```typescript
if (subPath) url += `/${encodeURIComponent(subPath)}`;
```

**Pros:** Simple one-character fix.
**Cons:** `encodeURIComponent` would encode `samplingFeatures` to `samplingFeatures` (no change for ASCII-only values), but any accidental special char in a future value would be encoded rather than rejected.
**Effort:** Trivial | **Risk:** None

### Option C: Change `subPath` to a discriminated union type

```typescript
type ResourceSubPath = 'subsystems' | 'history' | 'datastreams' | 'status' | 'result' | 'cancel' | ...;
private buildResourceUrl(
  resourceType: string, id?: string, subPath?: ResourceSubPath, options?: QueryOptions
): string
```

**Pros:** Compile-time enforcement — no runtime check needed.
**Cons:** Private method; adds type verbosity.
**Effort:** Small | **Risk:** None

## Recommended Action

Option C (union type) for the `buildResourceUrl` private method — compile-time safety is free and eliminates any future path injection by construction. Combine with Option A's runtime allowlist for defense-in-depth in `command-routing.ts` where the subPath arrives via a public function parameter.

## Technical Details

- **Affected files:** `src/ogc-api/csapi/url_builder.ts:270`, `src/ogc-api/csapi/command-routing.ts:160`
- **Risk today:** Low (all call sites are hardcoded). Risk is architectural/preventative.

## Acceptance Criteria

- [ ] `subPath` parameter is either typed as a union or validated against an allowlist
- [ ] A caller passing an unexpected subPath value gets a clear error (either compile-time or runtime)
- [ ] All existing call sites still pass (no behavioral regression)

## Work Log

- 2026-03-05: Identified by security-sentinel agent during code review of `clean-pr`
