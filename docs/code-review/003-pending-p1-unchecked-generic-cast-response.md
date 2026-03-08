---
status: pending
priority: p1
issue_id: "003"
tags: [code-review, typescript, type-safety]
dependencies: []
---

# `parseCollectionResponse<T>` Lies About Its Generic Type

## Problem Statement

`parseCollectionResponse<T>` casts the raw `features` or `items` array directly to `T[]` without validating any element. `Array.isArray` only confirms an array exists — it says nothing about element types. The function promises `CollectionResponse<T>` but delivers `CollectionResponse<unknown>` masked as typed. Every downstream caller (all Part 2 parsers) receives data they believe is typed but may be `null`, numbers, or malformed objects.

**Why it matters:** This is the single boundary where untyped server JSON enters the typed system. If this boundary is dishonest, all of CSAPI's type safety downstream is illusory. A server returning `{ "items": [null, 42, "oops"] }` produces runtime TypeErrors at field access with no TS warning at the call site.

## Findings

**File:** `src/ogc-api/csapi/formats/response.ts`, **lines 98–102**

```typescript
let items: T[];
if (Array.isArray(obj.features)) {
  items = obj.features as T[];   // ← lie: no element is validated
} else if (Array.isArray(obj.items)) {
  items = obj.items as T[];      // ← same lie
}
```

**Concrete scenario:**
```typescript
// Server returns { "items": [null, 42, { "no-id": true }] }
const result = parseCollectionResponse<Datastream>(body);
result.items[0].id   // TypeError: Cannot read properties of null
result.items[1].id   // TypeError: undefined is not a property of number
// TypeScript shows no warning — it believes items are all Datastream
```

## Proposed Solutions

### Option A: Add `parseItem` callback parameter (Recommended)
```typescript
export function parseCollectionResponse<T>(
  body: unknown,
  parseItem: (item: unknown, index: number) => T
): CollectionResponse<T> {
  // ...existing envelope normalization unchanged...
  const rawItems = Array.isArray(obj.features) ? obj.features : (obj.items as unknown[]);
  const items = rawItems.map((item, i) => parseItem(item, i));
  return { items, links, numberMatched, numberReturned, timeStamp };
}
```

All callers become:
```typescript
parseCollectionResponse(body, parseDatastream)
parseCollectionResponse(body, parseObservation)
parseCollectionResponse(body, extractCSAPIFeature)
```

**Pros:** Closes the gap completely; each item goes through its own parser; composable; consistent with the existing pattern where every resource has a dedicated parser function.
**Cons:** Breaking API change for any existing callers of `parseCollectionResponse` (currently only internal). Small migration effort.
**Effort:** Medium | **Risk:** Low (internal function only)

### Option B: Change return type to `CollectionResponse<unknown>` and let callers map
```typescript
export function parseCollectionResponse(body: unknown): CollectionResponse<unknown>
```
Callers then do `result.items.map(parseDatastream)`.
**Pros:** Honest about what the function does.
**Cons:** Loses the convenience of single-call parse; callers must always map.
**Effort:** Small | **Risk:** Low

### Option C: Keep current API, add runtime filter
```typescript
items = (Array.isArray(obj.features) ? obj.features : obj.items)
  .filter((item): item is T => item !== null && typeof item === 'object');
```
**Pros:** No API change; filters obvious garbage.
**Cons:** Still lying about T — filters objects but doesn't confirm shape.
**Effort:** Trivial | **Risk:** Low (still technically a lie, but safer)

## Recommended Action

Option A. The `parseItem` callback is the correct, complete fix. It is the same pattern used consistently throughout the rest of the CSAPI module. The function is only used internally so migration is contained.

## Technical Details

- **Affected file:** `src/ogc-api/csapi/formats/response.ts:87–130`
- **Affected callers:** all `parseCollectionResponse` call sites (search `formats/` and `integration/`)
- **Impact:** All Part 2 parsers (`parseDatastream`, `parseObservation`, etc.) receive unvalidated items today

## Acceptance Criteria

- [ ] `parseCollectionResponse` with a server returning `[null, 42]` either throws during parsing or skips invalid elements — never returns them typed as `T`
- [ ] All callers updated to pass a `parseItem` function
- [ ] TypeScript confirms the return type is `CollectionResponse<T>` where `T` is the concrete parsed type
- [ ] Existing integration tests pass

## Work Log

- 2026-03-05: Identified by TypeScript quality agent during code review of `clean-pr`

## Resources

- TypeScript agent full report: `/private/tmp/claude-501/-Users-bruceb-projects-os-ogc-client/tasks/a085ef4.output`
