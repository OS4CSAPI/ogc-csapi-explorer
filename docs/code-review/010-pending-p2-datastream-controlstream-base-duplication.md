---
status: pending
priority: p2
issue_id: '010'
tags: [code-review, dry, architecture]
dependencies: []
---

# `parseDatastream` and `parseControlStream` Share ~30 Lines of Identical Extraction Logic

## Problem Statement

`parseDatastream` and `parseControlStream` in `part2.ts` share an identical skeleton for extracting base stream fields (`id`, `name`, `description`, `validTime`, `formats`, `systemId`, `links`). Approximately 30 lines are copy-pasted between the two functions, meaning any bug fix or new field must be applied twice.

## Findings

**File:** `src/ogc-api/csapi/formats/part2.ts`

Identical blocks:

- Lines 114–118 (null guard + cast) ↔ Lines 214–219
- Lines 126–129 (`name`, `description`, `id` extraction) ↔ Lines 222–225
- Lines 139–141 (`validTime` extraction) ↔ Lines 228–230
- Lines 143–150 (`formats` extraction) ↔ Lines 232–238
- Lines 153–156 (`systemId` cross-ref) ↔ Lines 240–243
- Lines 161–166 (`links` array) ↔ Lines 247–252

Only the time-interval field names and one or two resource-specific fields differ.

## Proposed Solutions

### Option A: Extract `parseBaseStream` helper (Recommended)

```typescript
interface BaseStream {
  id: string;
  name: string;
  description?: string;
  validTime?: TimeInterval;
  formats: string[];
  systemId?: string;
  links: ResourceLink[];
}

function parseBaseStream(
  fn: string,
  json: unknown
): { base: BaseStream; obj: Record<string, unknown> } {
  if (typeof json !== 'object' || json === null)
    throw new Error(`${fn}: input must be a non-null object`);
  const obj = json as Record<string, unknown>;
  return {
    obj,
    base: {
      id: typeof obj.id === 'string' ? obj.id : '',
      name: typeof obj.name === 'string' ? obj.name : '',
      ...(typeof obj.description === 'string'
        ? { description: obj.description }
        : {}),
      validTime: parseValidTime(obj.validTime),
      formats: Array.isArray(obj.formats)
        ? obj.formats.filter((f): f is string => typeof f === 'string')
        : [],
      ...(typeof obj['system@id'] === 'string'
        ? { systemId: obj['system@id'] as string }
        : {}),
      links: Array.isArray(obj.links) ? (obj.links as ResourceLink[]) : [],
    },
  };
}

export function parseDatastream(json: unknown): Datastream {
  const { base, obj } = parseBaseStream('parseDatastream', json);
  // ...only Datastream-specific fields below
  return {
    ...base,
    observedProperties,
    phenomenonTime,
    resultTime,
    resultType,
    live,
  };
}
```

**Effort:** Medium | **Risk:** Low

### Option B: Leave as-is with a comment linking the two functions

**Effort:** Trivial | **Risk:** None (but bug-magnets remain)

## Recommended Action

Option A. This is a medium-effort cleanup with a direct payoff: the next time a field is added to either resource (likely when the spec adds a new cross-ref), it is added once rather than twice.

## Technical Details

- **Affected file:** `src/ogc-api/csapi/formats/part2.ts`
- **Lines to unify:** ~30 per function (60 total → ~10 + shared helper)

## Acceptance Criteria

- [ ] `parseBaseStream` helper extracts the 7 common fields
- [ ] `parseDatastream` and `parseControlStream` both call it
- [ ] All Part 2 parser tests pass
- [ ] See also Finding 011: `requireObject` for the null-guard portion

## Work Log

- 2026-03-05: Identified by DRY analysis agent during code review of `clean-pr`
