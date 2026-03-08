---
status: pending
priority: p3
issue_id: "012"
tags: [code-review, typescript, quality]
dependencies: []
---

# Redundant `as Record<string, unknown>` Casts After `isRecord` Narrowing

## Problem Statement

Throughout the SWE Common and SensorML parsers, `isRecord(x)` is called to narrow `x` to `Record<string, unknown>`, but the very next line re-casts with `x as Record<string, unknown>`. TypeScript has already done the narrowing — the re-cast is noise that makes reviewers work harder and implies the first guard was insufficient.

## Findings

Approximately 15 occurrences across:

- **`src/ogc-api/csapi/formats/swecommon/parser.ts`**, lines 363–367, 623–624, 648–653
- **`src/ogc-api/csapi/formats/swecommon/data-array.ts`**, lines 126–132, 575–580
- **`src/ogc-api/csapi/formats/swecommon/data-record.ts`** — correctly does NOT re-cast (use as template)

Representative example at `parser.ts:363–367`:
```typescript
} else if (
  isRecord(json.values) &&
  typeof (json.values as Record<string, unknown>).href === 'string'  // ← redundant cast
) {
  values = parseAssociationAttributeGroup(
    json.values as Record<string, unknown>  // ← also redundant
  );
```

After `isRecord(json.values)`, `json.values` IS `Record<string, unknown>` — no cast needed.

## Proposed Solutions

### Option A: Remove all redundant re-casts in a cleanup pass
Find all `isRecord(x)` calls and verify the narrowed `x` is used directly on the next line without re-casting.
**Effort:** Small | **Risk:** None

## Recommended Action

Option A — small cleanup pass. No behavioral change; purely improves readability and reduces reviewer confusion.

## Technical Details

- **Affected files:** `swecommon/parser.ts`, `swecommon/data-array.ts`
- **Reference (correct pattern):** `swecommon/data-record.ts` — direct assignment after `isRecord` without cast

## Acceptance Criteria

- [ ] No instance of `isRecord(x)` immediately followed by `x as Record<string, unknown>`
- [ ] All SWE Common parser tests pass

## Work Log

- 2026-03-05: Identified by TypeScript quality agent during code review of `clean-pr`
