---
status: deferred
priority: p3
issue_id: '020'
tags: [code-review, api-design, ergonomics]
dependencies: ['#102']
phase: 8
---

# `getCommand(id, undefined, controlStreamId)` Positional Argument Awkwardness

## Problem Statement

After Phase 7 / issue #102 added optional nested parent IDs to command and
observation CRUD methods, several methods now have a `(id, options?, parentId?)`
signature. To reach the third argument, callers must pass `undefined` as the
options:

```ts
builder.getCommand('cmd-001', undefined, 'cs-001');
```

The two-mode signature is internally consistent (read methods take options;
mutation methods do not), but the `undefined` pass-through is awkward.

## Findings

**File:** `src/ogc-api/csapi/url_builder.ts`

Affected methods (read methods with options + parent-ID parameter):

- `getCommand(id, options?, controlStreamId?)`
- `getObservation(id, options?, datastreamId?)`
- `getCommandStatus(id, options?, controlStreamId?)`

Mutation methods do not have this issue because they do not take options:

- `updateCommand(id, controlStreamId?)`
- `deleteCommand(id, controlStreamId?)`
- `cancelCommand(id, controlStreamId?)`

## Proposed Solutions

### Option A: Convert to a single options object

```ts
builder.getCommand({ id: 'cmd-001', controlStreamId: 'cs-001' });
```

**Effort:** Medium (signature changes + all call sites + integration tests)
**Risk:** Breaking change to public API surface

### Option B: Status quo + JSDoc note (Recommended for now)

The pattern works. Document it. Defer the redesign to a future minor.

## Triage

**Defer — tracked for follow-up.**

Rationale (matches the [#110 deferral precedent](110-deferred-enhancement-link-resolution-utilities.md)):

- Phase 7 already shipped #102 with this signature shape.
- Redesigning is wider than a cleanup pass.
- The cost (`undefined` keystrokes) is small relative to the breaking-change
  cost of redesigning.
- A future PR can introduce options-object overloads without breaking the
  current signature.
