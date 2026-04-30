---
status: pending
priority: p3
issue_id: '014'
tags: [code-review, code-quality, duplication]
dependencies: []
---

# `createCommand()` and `createCommands()` Are Byte-Identical Implementations

## Problem Statement

`CSAPIQueryBuilder.createCommand()` (line 2295) and `CSAPIQueryBuilder.createCommands()` (line 2326) in `url_builder.ts` have **identical** method bodies — both call `this.assertResourceAvailable('controlStreams')` followed by `return this.buildResourceUrl('controlStreams', controlStreamId, 'commands')`. The semantic distinction (single-resource POST vs. bulk POST) lives entirely in the request body, not the URL path, so both methods produce the same URL string from the same input.

**Why it matters:** Two public methods with different names promising different behavior but containing identical code is a maintenance trap. A future developer changing `createCommand` might not realize `createCommands` must stay in sync (or vice versa). The duplication also obscures the fact that the OGC API uses the same endpoint for both operations — a key design insight that should be documented once, not silently duplicated.

## Findings

**File:** `src/ogc-api/csapi/url_builder.ts`, **lines 2295–2298 and 2326–2329**

```typescript
// Line 2295
createCommand(controlStreamId: string): string {
  this.assertResourceAvailable('controlStreams');
  return this.buildResourceUrl('controlStreams', controlStreamId, 'commands');
}

// Line 2326
createCommands(controlStreamId: string): string {
  this.assertResourceAvailable('controlStreams');
  return this.buildResourceUrl('controlStreams', controlStreamId, 'commands');
}
```

No other resource type has this singular/plural pair — `createObservation()` (line 1659) has **no** corresponding `createObservations()`.

## Proposed Solutions

### Option A: `createCommands` Delegates to `createCommand` (Recommended)

```typescript
createCommands(controlStreamId: string): string {
  return this.createCommand(controlStreamId);
}
```

**Pros:** Eliminates body duplication; makes the relationship explicit; callers unchanged.
**Cons:** None — both methods survive for discoverability.
**Effort:** Trivial | **Risk:** None

### Option B: Merge Into One Method With JSDoc Note

Remove `createCommands` entirely and document on `createCommand` that the same URL serves both single and bulk POST:

```typescript
/**
 * Returns the URL for creating command(s) within a control stream.
 *
 * The OGC API uses the same endpoint for both single and bulk command
 * creation — multiplicity is determined by the request body, not the URL.
 */
createCommand(controlStreamId: string): string { ... }
```

**Pros:** Single source of truth; no duplication.
**Cons:** Breaking change if external callers use `createCommands`.
**Effort:** Small | **Risk:** Low (internal API)

## Recommended Action

Option A. Delegation preserves both method names for API discoverability while making the shared implementation explicit and maintainable.

## Technical Details

- **Affected file:** `src/ogc-api/csapi/url_builder.ts:2295–2329`
- **Affected callers:** Any code calling `createCommands()` — currently internal only
- **Impact:** Maintenance risk from silent divergence of identical methods

## Acceptance Criteria

- [ ] `createCommands` delegates to `createCommand` (or vice versa) — a single implementation
- [ ] JSDoc on both methods clarifies the relationship and the OGC endpoint design
- [ ] Existing tests still pass (`npm test`)
- [ ] No lint errors (`npm run lint`)

## Work Log
