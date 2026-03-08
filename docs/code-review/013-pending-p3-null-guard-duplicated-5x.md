---
status: pending
priority: p3
issue_id: "013"
tags: [code-review, dry, quality]
dependencies: [010]
---

# Null-Guard + Cast Pattern Repeated in Every `part2.ts` Parse Function

## Problem Statement

All 5 parse functions in `part2.ts` begin with identical null-guard + cast boilerplate. This is a 5-way copy-paste that creates a bug-magnet — any future change to the error message format or the cast strategy must be applied to all 5 functions manually.

## Findings

**File:** `src/ogc-api/csapi/formats/part2.ts`

```typescript
// Line 115-118 (parseDatastream)
if (typeof json !== 'object' || json === null) {
  throw new Error('parseDatastream: input must be a non-null object');
}
const obj = json as Record<string, unknown>;

// Lines 215-218 (parseControlStream) — identical structure
// Lines 327-331 (parseCommand) — identical structure
// Lines 408-410 (parseObservation) — identical structure
// Lines 492-496 (parseCommandStatus) — identical structure
```

## Proposed Solutions

### Option A: Extract `requireObject` helper
```typescript
function requireObject(json: unknown, fn: string): Record<string, unknown> {
  if (typeof json !== 'object' || json === null)
    throw new Error(`${fn}: input must be a non-null object`);
  return json as Record<string, unknown>;
}

// Usage:
export function parseDatastream(json: unknown): Datastream {
  const obj = requireObject(json, 'parseDatastream');
  // ...
}
```
**Effort:** Small (10 lines of change, eliminates 15 lines) | **Risk:** None

## Recommended Action

Option A. Tiny helper, clean result. This should be done alongside Finding 010 (parseBaseStream) since they address the same functions.

## Technical Details

- **Affected file:** `src/ogc-api/csapi/formats/part2.ts`
- **Eliminates:** 15 lines of boilerplate across 5 functions

## Acceptance Criteria

- [ ] `requireObject` helper extracted (or inlined into `parseBaseStream`)
- [ ] All 5 parse functions use it
- [ ] All Part 2 parser tests pass

## Work Log

- 2026-03-05: Identified by DRY analysis agent during code review of `clean-pr`
