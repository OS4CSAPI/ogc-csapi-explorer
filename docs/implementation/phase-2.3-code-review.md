# Phase 2.3 Code Review — Procedures Methods

**Date:** 2025-06-26  
**Reviewer:** GitHub Copilot (Claude Opus 4.6)  
**Scope:** Issue #7 — 8 Procedures methods in `CSAPIQueryBuilder`  
**Commit:** `8dbb9c5` (`feat(csapi): implement 8 Procedures methods (Issue #7)`)

---

## Verification Status

| Check                                                    | Result                                              |
| -------------------------------------------------------- | --------------------------------------------------- |
| `tsc --noEmit`                                           | ✅ Clean                                            |
| CSAPI unit tests (url_builder, model, helpers)           | ✅ All passing                                      |
| Endpoint integration tests                               | ✅ 82/83 passing (1 pre-existing non-CSAPI failure) |
| `assertResourceAvailable('procedures')` in all 8 methods | ✅ Verified via grep                                |
| Lessons Learned L1–L7 compliance                         | ✅ All applied                                      |

---

## Files Reviewed

### Issue #7: Procedures Methods

| File                                    | Lines Changed     | Phase 2.3 Lines  |
| --------------------------------------- | ----------------- | ---------------- |
| `src/ogc-api/csapi/url_builder.ts`      | +168 (624 → 793)  | Lines 2, 626–793 |
| `src/ogc-api/csapi/url_builder.spec.ts` | +186 (893 → 1079) | Lines 893–1079   |

Total production code: 168 new lines (8 methods + JSDoc)  
Total test code: 186 new lines (20 tests in 7 describe blocks)

---

## Phase 2.2 Findings Reaffirmation

### [P2-F1] RESOLVED: Dead `encodeArrayParameter` function

**Status:** Fixed in Issue #38 cleanup. Function and tests removed from `helpers.ts` / `helpers.spec.ts`. Grep confirms zero references remain.

---

### [P2-F2] RESOLVED: DRY violation in link-scanning logic

**Status:** Fixed in Issue #38. Shared `scanCsapiLinks()` helper extracted to `helpers.ts`. Both `url_builder.ts` (line 114) and `endpoint.ts` (line 380) now call the shared function.

---

### [P2-F3] RESOLVED: Strict-mode type safety in `buildResourceUrl`

**Status:** Fixed in Issue #38. Code now uses variable capture:

```typescript
const topLevelUrl = this.resourceUrls_.get(resourceType);
const resourceBase = topLevelUrl
  ? topLevelUrl.replace(/\/+$/, '')
  : `${this.baseUrl}/${resourceType}`;
```

This is strict-mode safe — truthiness check on the captured value narrows correctly.

---

### [P2-F4] STILL OPEN: Weak datetime test for `getDeployments`

**File:** `src/ogc-api/csapi/url_builder.spec.ts` line 747  
**Status:** Unchanged. Test still uses `toContain('datetime=')` instead of an exact `toBe()` assertion. Contrast with the Procedures tests which use exact assertions throughout.

---

### [P2-F5] STILL OPEN: Missing `parent` and `recursive` tests for `getDeployments`

**File:** `src/ogc-api/csapi/url_builder.spec.ts`  
**Status:** Unchanged. `DeploymentQueryOptions` supports `parent`, `systemId`, and `recursive`, but only `systemId` is tested.

---

### [P2-F6] STILL OPEN: Missing pagination test for `getDeploymentSubdeployments`

**File:** `src/ogc-api/csapi/url_builder.spec.ts`  
**Status:** Unchanged. Only tests no-options and `recursive=true`. No pagination+filtering test.

---

### [P2-F7] STILL OPEN: No test for cursor-based pagination

**File:** `src/ogc-api/csapi/url_builder.spec.ts`  
**Status:** Unchanged. `QueryOptions.cursor` has zero test coverage across all resource types.

---

### [P2-F8] PARTIALLY RESOLVED: No test for `offset` with an actual value

**File:** `src/ogc-api/csapi/url_builder.spec.ts`  
**Status:** Partially addressed. The Procedures tests now include an explicit `offset: 20` test (line 920), validating it produces the correct URL. However, `getSystems` and `getDeployments` still lack an explicit offset test. The finding is resolved for Procedures but still open for Systems/Deployments.

---

### [P1-F4] STILL OPEN: Missing exports from `index.ts`

**Status:** Unchanged since Phase 1. `CSAPIResourceTypes`, `CommandStatusCodes`, `SystemTypeUris`, collection type aliases, and `ProcedureQueryOptions` are not exported from the library's public API.

---

### [P1-F6] STILL OPEN: Hardcoded temporal parameter keys

**File:** `src/ogc-api/csapi/url_builder.ts` line 171  
**Status:** Unchanged. Still a chain of `||` comparisons. Will become more relevant in Phase 2 Part 2 (Issues #10–#13) when temporal parameters are exercised heavily.

---

## Phase 2.3 Findings — New

### [F1] POSITIVE: Procedures tests are more thorough than Deployments tests

The 20 Procedures tests demonstrate a measurable improvement in test discipline over the 16 Deployments tests added in Phase 2.2:

| Quality metric                  | Deployments (Phase 2.2)      | Procedures (Phase 2.3) |
| ------------------------------- | ---------------------------- | ---------------------- |
| Assertion style                 | Mixed (`toBe` + `toContain`) | All exact `toBe()`     |
| `offset` test with actual value | ❌                           | ✅ (line 920)          |
| `f` (format) parameter test     | ❌                           | ✅ (line 940)          |
| Resource validation coverage    | 1 of 8 methods checked       | 8 of 8 methods checked |

This is a direct result of applying Lesson L1 (test checklist) from the lessons-learned governance doc. The test quality improvement between Phase 2.2 and Phase 2.3 is evidence that the lessons-learned process works.

---

### [F2] POSITIVE: Resource validation test covers all 8 methods

**File:** `src/ogc-api/csapi/url_builder.spec.ts` lines 1059–1079

The Procedures resource validation test checks all 8 methods in a single `it()` block:

```typescript
expect(() => builder.getProcedures()).toThrow(EndpointError);
expect(() => builder.getProcedure('x')).toThrow(EndpointError);
expect(() => builder.createProcedure()).toThrow(EndpointError);
expect(() => builder.updateProcedure('x')).toThrow(EndpointError);
expect(() => builder.deleteProcedure('x')).toThrow(EndpointError);
expect(() => builder.getProcedureSystems('x')).toThrow(EndpointError);
expect(() => builder.getProcedureDataStreams('x')).toThrow(EndpointError);
expect(() => builder.getProcedureHistory('x')).toThrow(EndpointError);
```

By contrast, the Deployment validation test at line 880 only checks `getDeployments()`. The Systems validation is scattered across individual describe blocks (some methods have error tests, some don't).

**Recommendation:** The Procedures pattern is the best of the three. Consider backfilling Deployment validation to match when addressing P2-F4/F5/F6 test gaps.

---

### [F3] POSITIVE: JSDoc correctly documents unsupported parameters

**File:** `src/ogc-api/csapi/url_builder.ts` line 633

```typescript
 * @param options - Optional query parameters for filtering procedures.
 *   Procedures support: `id`, `uid`, `q`, `limit`, `offset`, `f`.
 *   Procedures do NOT support `bbox`, `datetime`, `parent`, or `recursive`.
```

This is valuable documentation. Since `ProcedureQueryOptions = QueryOptions` and `QueryOptions` includes `bbox` and `datetime` as optional fields, nothing in the type system prevents a consumer from passing them. The JSDoc serves as the contract.

---

### [F4] INFORMATIONAL: Type alias allows unsupported parameters

**File:** `src/ogc-api/csapi/model.ts` line 159

```typescript
export type ProcedureQueryOptions = QueryOptions;
```

Since `QueryOptions` has `bbox`, `datetime`, and 4 temporal keys as optional fields, consumers can pass `getProcedures({ bbox: [-180, -90, 180, 90] })` without a type error. The builder will happily serialize `bbox` into the URL, and the server will either ignore it or return an error.

This is the same pattern used for `DeploymentQueryOptions` (which extends with `parent`/`systemId`/`recursive`) and `SystemQueryOptions` (which extends with 6 fields). For those types, the extensions are additive — the base fields are still valid. For Procedures, some base fields are NOT valid.

**Not a bug in the URL builder** — the builder's responsibility is URL construction, not parameter validation. This is a Phase 3 concern when we add response handling and can surface server errors. No action needed now.

---

### [F5] POSITIVE: Spec links are correctly differentiated

All Procedure methods correctly point to Part 1 spec sections:

| Method                    | `@see` target                              |
| ------------------------- | ------------------------------------------ |
| `getProcedures`           | `23-001/23-001.html#_procedure_resources`  |
| `getProcedure`            | `23-001/23-001.html#_procedure_resources`  |
| `createProcedure`         | `23-001/23-001.html#_procedure_resources`  |
| `updateProcedure`         | `23-001/23-001.html#_procedure_resources`  |
| `deleteProcedure`         | `23-001/23-001.html#_procedure_resources`  |
| `getProcedureSystems`     | `23-001/23-001.html#_procedure_resources`  |
| `getProcedureDataStreams` | `23-002/23-002.html#_datastream_resources` |
| `getProcedureHistory`     | `23-001/23-001.html#_procedure_history`    |

`getProcedureDataStreams` correctly references Part 2 spec (`23-002`) since datastreams are a Part 2 resource. `getProcedureHistory` correctly uses the `_procedure_history` anchor (not `_procedure_resources`). Both follow the patterns established by `getSystemDataStreams` (Part 2 link) and `getSystemHistory` (`_system_history` anchor).

---

### [F6] POSITIVE: Procedures correctly omit sub-resource nesting

Systems have `getSystemSubsystems`, Deployments have `getDeploymentSubdeployments`. Procedures have neither — there is no `getProcedureSubprocedures` method. This is correct: the OGC Connected Systems spec does not define hierarchical nesting for procedures. They are leaf resources.

The method set is exactly right:

- **CRUD:** get list, get single, create, update, delete (5 methods)
- **Associations:** systems implementing the procedure, datastreams using the procedure (2 methods)
- **History:** version history (1 method)

No missing methods. No extraneous methods.

---

### [F7] POSITIVE: Association tests include pagination

**File:** `src/ogc-api/csapi/url_builder.spec.ts` lines 1014–1033

Both `getProcedureSystems` and `getProcedureDataStreams` have tests with and without options:

```typescript
it('getProcedureSystems returns correct URL with pagination', () => {
  const url = makeProcBuilder().getProcedureSystems('proc-001', {
    limit: 5,
    offset: 10,
  });
  expect(url).toBe(
    'https://example.com/.../procedures/proc-001/systems?limit=5&offset=10'
  );
});
```

This addresses a lesson from P2-F6 (the Deployment association tests lacked pagination tests). The improvement was applied proactively.

---

### [F8] CONSISTENCY: `makeProcBuilder` is repeated in every describe block

**File:** `src/ogc-api/csapi/url_builder.spec.ts` lines 897–906, 953–962, 976–985, 1004–1013, 1037–1046, 1059–1068

The factory function `makeProcBuilder()` is defined identically in 6 of the 7 Procedures describe blocks. The 7th (Procedure resource validation) uses a different collection to test the error case.

This is the same pattern used for `makeDepBuilder()` (repeated in 6 Deployment describe blocks) and `makeIotBuilder()` (repeated in 14 Systems describe blocks). It's a deliberate choice — each describe block is self-contained and can be moved or deleted independently.

**Not a finding requiring action.** While a shared setup could reduce repetition, the self-contained approach is better for test maintainability and was the pattern established in Phase 2.1. Consistency with the existing pattern is more important than DRY in test code.

---

## Summary

| Category                              | Count | Items                                                                                                                                              |
| ------------------------------------- | ----- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| Phase 2.2 findings resolved           | **3** | P2-F1 (dead code), P2-F2 (DRY), P2-F3 (strict-mode)                                                                                                |
| Phase 2.2 findings partially resolved | **1** | P2-F8 (offset test — fixed for Procedures, still open for Systems/Deployments)                                                                     |
| Phase 2.2 findings still open         | **4** | P2-F4 (weak datetime), P2-F5 (parent/recursive), P2-F6 (pagination), P2-F7 (cursor)                                                                |
| Phase 1 findings still open           | **2** | P1-F4 (exports), P1-F6 (temporal keys)                                                                                                             |
| New — positive findings               | **6** | F1 (test quality improvement), F2 (validation coverage), F3 (JSDoc quality), F5 (spec links), F6 (correct method set), F7 (association pagination) |
| New — informational                   | **1** | F4 (type alias allows unsupported params)                                                                                                          |
| New — consistency note                | **1** | F8 (repeated factory function — by design)                                                                                                         |
| **New bugs or design issues**         | **0** | —                                                                                                                                                  |

---

## Recommendations

### Fix Before Next Phase 2 Issue

1. **[P2-F4–F7] Backfill Deployment/Systems test gaps** — These have been open since the Phase 2.2 review. The Procedures tests demonstrate the correct patterns. ~6 tests to add:
   - Strengthen `getDeployments` datetime to exact `toBe()` assertion
   - Add `getDeployments({ parent: ... })` and `getDeployments({ recursive: true })` tests
   - Add `getDeploymentSubdeployments` pagination+filtering test
   - Add `getSystems({ cursor: ... })` test
   - Add `getSystems({ offset: 50 })` test
   - Optionally: expand Deployment resource validation to cover all 8 methods (matching Procedures pattern)

### Fix Before Phase 3

2. **[P1-F4] Add missing exports** — Growing list of unexported types now includes `ProcedureQueryOptions`
3. **[P1-F6] Extract temporal keys to a Set** — Before Part 2 resource methods

---

## Root Cause Analysis — Why Phase 2.3 Had Zero New Issues

Phase 2.3 had zero new defects or design issues. This is a meaningful data point — and it deserves explanation because it's easy to dismiss as "simple resource, nothing could go wrong."

### The simplicity factor

Procedures are the simplest of the three Part 1 resource types implemented so far:

- `ProcedureQueryOptions = QueryOptions` — no extensions, no special fields
- No sub-resource nesting (no `getSubprocedures`)
- No spatial support (`bbox` documented as unsupported)
- No temporal support (`datetime` documented as unsupported)

This meant less surface area for bugs than Systems (6 extra query fields) or Deployments (3 extra fields + subdeployments + datetime).

### The lessons-learned factor

The more significant factor is that the lessons-learned governance doc (`phase-2-lessons-learned.md`) was created _before_ Issue #7 was started, not after. Every lesson was applied proactively:

- **L1 (test checklist):** All tests use exact `toBe()` assertions. No `toContain` shortcuts.
- **L2 (query param table):** The JSDoc explicitly lists supported and unsupported parameters.
- **L4 (resource string verification):** All 8 methods verified by grep to use `'procedures'`.
- **L5 (file scope):** Only `url_builder.ts` and `url_builder.spec.ts` modified — narrow, focused scope.
- **L7 (DRY):** No duplicated code; all methods delegate to `buildResourceUrl()` + `buildQueryString()`.

### The compound effect

The test quality improvement between Deployments (Phase 2.2) and Procedures (Phase 2.3) — exact assertions, offset coverage, format parameter coverage, full validation test — directly resulted from creating the lessons-learned doc between the two phases. The process worked exactly as intended: document what went wrong, apply the lessons to the next unit of work, verify the improvement.

The remaining open findings (P2-F4–F7) are all from Deployments code that was written _before_ the lessons were documented. They serve as the control group. The Procedures code serves as the experimental group. The difference is measurable.

---

## Overall Assessment

**Phase 2.3 is clean.** No new bugs, no design issues, no test gaps. The 8 Procedures methods follow the established pattern correctly, the 20 tests are thorough and use exact assertions throughout, and the JSDoc documentation is accurate.

The 6 still-open findings from prior reviews (P2-F4–F7, P1-F4, P1-F6) should be addressed in a dedicated cleanup pass before Issue #8. This would take roughly 30 minutes and would bring the entire test suite to the quality standard established by the Procedures tests.

The CSAPI module now has **28 public methods** across three resource types, with **91 url_builder tests**, **30 helper tests**, and **27 model tests** — all passing.
