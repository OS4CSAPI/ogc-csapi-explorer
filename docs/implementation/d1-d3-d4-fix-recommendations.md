# D-1, D-3, D-4 Design Findings — Analysis and Fix Recommendations

**Date:** 2026-02-25
**Source:** Code audit findings D-1, D-3, D-4 from [CSAPI-CODE-AUDIT-PHASE-6.md](../../CSAPI-CODE-AUDIT-PHASE-6.md)
**Context:** [F70 Design Findings Investigation](f70-design-findings-investigation.md) identified D-1, D-3, and D-4 as the fixable subset of the 8 DESIGN findings
**Issues:** [#136](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/136) (D-1), [#134](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/134) (D-3), [#135](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/135) (D-4)

---

## Overview

Of the 8 DESIGN findings in the code audit, 5 are intentional design choices (D-2, D-5, D-6, D-7, D-8) and 3 are fixable technical debt (D-1, D-3, D-4). This document provides the analysis and recommended fix approach for each.

---

## D-1: `SystemTypeUris` Name Collision (model.ts vs constants.ts)

### What It Is

Two different modules export the same symbol name `SystemTypeUris` with different values:

- **`model.ts`** (~line 81): 5 entries — full URI forms only (`http://www.w3.org/ns/sosa/Sensor`, etc.)
- **`formats/constants.ts`** (~line 120): 10 entries — both CURIE forms (`sosa:Sensor`) AND full URI forms

Both are re-exported from the barrel file.

### Why It Matters

This is an **API-surface defect**, not just internal debt. A consumer who writes `import { SystemTypeUris } from '@camptocamp/ogc-client/csapi'` gets whichever one the barrel resolves — likely the last one exported — with no compiler warning that an identically-named but differently-valued object exists. If they need CURIEs (for server-side matching) but get the model-only version, their code silently fails to match. Conversely, if they expect only full URIs, they get extra CURIE entries they didn't anticipate.

### Key Discovery

The barrel (`csapi/index.ts`) only re-exports `model.ts`'s 5-entry version. The `constants.ts` 10-entry version (with CURIEs) is **never exposed to consumers** — it's only used internally by format handlers. So this is not actually a consumer-facing API collision today — it's a **maintainer-facing naming confusion** where two different files define `SystemTypeUris` with different values for different purposes:

| File           | Entries                     | Purpose                                                         |
| -------------- | --------------------------- | --------------------------------------------------------------- |
| `model.ts`     | 5 full URIs                 | Public type system — canonical system type values               |
| `constants.ts` | 10 (5 CURIEs + 5 full URIs) | Internal recognition vocabulary — match both forms when parsing |

### Recommended Fix: Rename the Internal One

**Rename** `SystemTypeUris` in `constants.ts` → `SYSTEM_TYPE_RECOGNITION_VALUES` (and `SystemTypeUri` → `SystemTypeRecognitionValue`).

Concrete steps:

1. In `constants.ts`, rename the const and the derived type
2. Update all internal import sites (grep for `SystemTypeUris` in `formats/` to find them)
3. `model.ts` and the public barrel: **untouched**

**Why this approach:**

- Zero public API change — the barrel export stays `SystemTypeUris` from `model.ts`
- Self-documenting — the name `SYSTEM_TYPE_RECOGNITION_VALUES` immediately communicates "this is a matching table, not the canonical type set"
- The `SCREAMING_CASE` convention signals it's a module-internal constant (consistent with `SIMPLE_COMPONENT_TYPES`, `CSAPI_CONTENT_TYPES` already in `constants.ts`)
- Minimal diff — only `constants.ts` + its internal consumers change

**Alternative considered — derive from model.ts:** Import `SystemTypeUris` from `model.ts` and combine with CURIEs. This is more DRY but the `as const` spreading behavior with tuples can get finicky with TypeScript inference. The simple rename is safer.

**Risk:** Low. Only internal references change.

---

## D-3: Duplicated `parseComponentList` / `parseConnectionList` / `parseConnection`

### What It Is

Three functions are copy-pasted identically between `physical-system.ts` and `aggregate-process.ts`:

- `parseComponentList` (~35 lines each)
- `parseConnectionList` (~35 lines each)
- `parseConnection` (private helper)

A fourth function — `parseComponentEntry` — was already extracted to `_helpers.ts` by Issue #97, proving the pattern works.

### Why It Matters

This is the classic bug-duplication problem. If a parsing bug is found in `parseComponentList`, you must fix it in two places. The SensorML spec is complex enough that parsing edge cases do arise. Issue #97 already demonstrated that extraction to `_helpers.ts` works cleanly and doesn't break anything.

### Recommended Fix: Extract to `_helpers.ts` + Re-export from Originals

Concrete steps:

1. **Move to `_helpers.ts`:** Cut `parseComponentList`, `parseConnection`, and `parseConnectionList` from `physical-system.ts`. Add them to `_helpers.ts` right after `parseComponentEntry`. `parseConnection` becomes exported at the `_helpers.ts` level (acceptable since `_helpers.ts` is internal).
2. **Re-export from both consumers:**

   ```typescript
   // physical-system.ts
   export { parseComponentList, parseConnectionList } from './_helpers.js';

   // aggregate-process.ts
   export { parseComponentList, parseConnectionList } from './_helpers.js';
   ```

   This keeps the existing test import paths working without modification.

3. **Remove the duplicate definitions** from `aggregate-process.ts`.
4. **Run existing tests** — no test changes needed because:
   - `physical-system.spec.ts` imports `parseComponentList` from `./physical-system.js` → still works via re-export
   - `aggregate-process.spec.ts` imports `parseComponentList` from `./aggregate-process.js` → still works via re-export

**Why this approach:**

- Follows the exact precedent from Issue #97 (`parseComponentEntry` extraction)
- Zero test changes required (re-exports preserve existing import paths)
- Zero public API change (these aren't in the barrel)
- Eliminates ~70 lines of exact duplication
- All three functions naturally belong in `_helpers.ts` — they're shared parsing utilities for SensorML component/connection structures

**One subtlety:** `parseConnection` is currently a non-exported function in both files. When moved to `_helpers.ts`, it becomes module-exported. This is fine — `_helpers.ts` is already an internal module.

**Risk:** Very low. The functions are identical, the extraction pattern is proven, and the tests cover both call sites.

---

## D-4: Duplicated `isRecord()` Type Guard

### What It Is

An identical utility function `isRecord()` exists in both:

- `sensorml/_helpers.ts`
- `swecommon/_helpers.ts`

The function is a 3-line pure utility: `(val: unknown): val is Record<string, unknown> => typeof val === 'object' && val !== null && !Array.isArray(value)`. It was independently created in each module because SensorML and SWE Common parsers were developed in parallel (Issues #54 and #56).

### Why It Matters

Functionally, the duplication of a 3-line pure utility is almost costless. The real question is architectural: should `sensorml/` and `swecommon/` share utilities? Currently they're treated as sibling modules with no cross-dependencies. Extracting `isRecord()` forces an architectural decision about where shared parser utilities live:

- A new `formats/_parse-utils.ts`? Creates a new shared layer.
- One module imports from the other? Creates a coupling direction that doesn't currently exist.
- A `csapi/utils.ts` at the top level? Puts a parser micro-utility outside the parser modules.

### Recommended Fix: New `formats/_parse-utils.ts` Shared Utility File

Create a small shared file at the `formats/` level:

```
formats/
  _parse-utils.ts    ← NEW: shared parser utilities
  sensorml/
    _helpers.ts      ← imports isRecord from ../_parse-utils.js
  swecommon/
    _helpers.ts      ← imports isRecord from ../_parse-utils.js
```

Concrete steps:

1. **Create `formats/_parse-utils.ts`** with `isRecord()` and its JSDoc.
2. **In `sensorml/_helpers.ts`:** Remove the local `isRecord` definition, add re-export:
   ```typescript
   export { isRecord } from '../_parse-utils.js';
   ```
   All existing consumers that `import { isRecord } from './_helpers.js'` continue working unchanged.
3. **Same in `swecommon/_helpers.ts`.**
4. **Zero changes to any other file** — all existing `import { isRecord } from './_helpers.js'` statements remain valid.

**Why this approach:**

- Preserves the principle that `sensorml/` and `swecommon/` don't depend on each other
- Creates a natural home for any future shared parser utilities (D-5/D-6 `SIMPLE_COMPONENT_TYPES` and `isLinkReference` could land here eventually)
- The `_` prefix convention signals it's an internal module (consistent with `_helpers.ts`)
- The re-export from both `_helpers.ts` files means **zero downstream import changes**

**Risk:** Very low. The new file has one function, both `_helpers.ts` re-export it, and all downstream code is untouched.

---

## Relative Prioritization

| Finding | Fix Effort                                      | Value                                         | Who Benefits  | Audit Priority |
| ------- | ----------------------------------------------- | --------------------------------------------- | ------------- | -------------- |
| D-3     | Very low (template exists via Issue #97)        | Medium (eliminates ~105 lines of duplication) | Maintainers   | Priority 2, #2 |
| D-1     | Low (rename or consolidate)                     | Medium-High (fixes API-surface ambiguity)     | **Consumers** | Priority 2, #4 |
| D-4     | Trivial code, non-trivial architecture decision | Low (3-line function)                         | Maintainers   | Priority 3, #6 |

### Recommended Sequencing

If fixing all three:

1. **D-4 first** — Create `formats/_parse-utils.ts` and re-export `isRecord` from both `_helpers.ts` files. Establishes the shared utility pattern.
2. **D-3 second** — Extract `parseComponentList`/`parseConnectionList`/`parseConnection` into `sensorml/_helpers.ts`. Uses `isRecord` that now comes from the shared utility (via `_helpers.ts` re-export — no change needed).
3. **D-1 last** — Rename `SystemTypeUris` in `constants.ts`. Fully independent but is the only one touching the `formats/` level outside `sensorml/`/`swecommon/`, so doing it last keeps a clean mental separation.

**Total estimated diff:** ~15 lines added (new `_parse-utils.ts` + re-exports), ~140 lines removed (duplicated functions), ~10 lines changed (rename + import updates). Net: **~115 lines smaller codebase**, three naming/duplication hazards eliminated.
