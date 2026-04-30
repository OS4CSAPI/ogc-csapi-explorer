---
status: pending
priority: p2
issue_id: '008'
tags: [code-review, typescript, type-safety]
dependencies: []
---

# Raw JSON Spread Into Typed SensorML Results Bypasses Type System

## Problem Statement

`physical-system.ts`, `aggregate-process.ts`, and `simple-process.ts` all construct their typed result objects by spreading the raw (unvalidated) server JSON, then deleting managed keys and re-assigning parsed values. This means:

1. Any field the server sends with the wrong type (e.g. `"label": 42`) lands on the result typed as `string` with no runtime or compile-time error
2. The delete-then-reassign mutation pattern is fragile and non-obvious
3. The actual type guarantee is hollow — TypeScript believes the result is `PhysicalSystem` but any field could be a server-side wrong type

## Findings

**File:** `src/ogc-api/csapi/formats/sensorml/physical-system.ts`, **lines 411–438**

```typescript
const result: PhysicalSystem = {
  ...(json as Record<string, unknown>), // ← spreads ALL raw server fields
  type: 'PhysicalSystem' as const,
  label: json.label as string, // ← coerces without checking type
  uniqueId: json.uniqueId as string, // ← same
};
// Then deletes raw keys and reassigns parsed values (lines 421–438)
delete (result as unknown as Record<string, unknown>)['outputs'];
result.outputs = parsedOutputs;
```

Same pattern at `aggregate-process.ts:129` and `simple-process.ts:108`.

## Ownership Assessment

**Verdict: 100% ours.**

All three files are entirely within the `csapi/` isolation boundary and do not exist on `upstream/main` (zero commits). All affected lines authored by Sam-Bolling on 2026-02-15:

| File                            | Commit     | Date       |
| ------------------------------- | ---------- | ---------- |
| `physical-system.ts` L411-416   | `0060356f` | 2026-02-15 |
| `aggregate-process.ts` L129-134 | `814aef64` | 2026-02-15 |
| `simple-process.ts` L108-113    | `242c2bfa` | 2026-02-15 |

## Proposed Solutions

### Option A: Construct result explicitly field-by-field (Recommended)

```typescript
const result: PhysicalSystem = {
  type: 'PhysicalSystem' as const,
  label:
    typeof json.label === 'string'
      ? json.label
      : (() => {
          throw new Error('PhysicalSystem: label must be a string');
        })(),
  uniqueId:
    typeof json.uniqueId === 'string'
      ? json.uniqueId
      : (() => {
          throw new Error('PhysicalSystem: uniqueId must be a string');
        })(),
  // ...all other fields extracted explicitly with type checks
};
```

**Pros:** No raw spread; no delete-then-reassign mutation; type checks are explicit; guaranteed to match the TypeScript interface.
**Cons:** More verbose; all DescribedObject fields must be listed explicitly.
**Effort:** Medium | **Risk:** Low

### Option B: Keep spread, add runtime type checks for required fields only

```typescript
if (typeof json.label !== 'string')
  throw new Error('PhysicalSystem: label required');
if (typeof json.uniqueId !== 'string')
  throw new Error('PhysicalSystem: uniqueId required');
const result: PhysicalSystem = {
  ...(json as Record<string, unknown>),
  type: 'PhysicalSystem' as const,
  label: json.label, // now known to be string
  uniqueId: json.uniqueId,
};
```

**Pros:** Less verbose; retains spread for optional fields; adds guards for required fields.
**Cons:** Still spreads unknown fields. Optional fields are still unguarded.
**Effort:** Small | **Risk:** Low

## Recommended Action

Option B is a pragmatic middle ground that eliminates the silent coercions on required fields while acknowledging that SensorML has a very large optional field surface area where exhaustive validation would be impractical. The delete-then-reassign mutation should also be replaced with explicit field assignment (construct result in two stages or use `Object.assign`).

## Technical Details

- **Affected files:**
  - `src/ogc-api/csapi/formats/sensorml/physical-system.ts:411–438`
  - `src/ogc-api/csapi/formats/sensorml/aggregate-process.ts:129`
  - `src/ogc-api/csapi/formats/sensorml/simple-process.ts:108`

## Acceptance Criteria

- [ ] Required fields (`label`, `uniqueId`, `type`) are type-checked before assignment — wrong type produces a clear error, not a silent coercion
- [ ] The delete-then-reassign mutation pattern is removed
- [ ] Existing SensorML parser tests pass

## Work Log

- 2026-03-05: Identified by TypeScript quality agent during code review of `clean-pr`
- 2026-03-06: Reviewed, ownership verified (100% ours), saved to docs/code-review/
