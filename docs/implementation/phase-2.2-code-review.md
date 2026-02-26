# Phase 2.2 Code Review Report

**Date:** February 14, 2026  
**Reviewer:** AI (GitHub Copilot)  
**Scope:** Phase 2 work completed so far (Issues #5, #6, #34, #35) plus reaffirmation of Phase 1 (Issues #1–#4). This is an incremental mid-phase review — Phase 2 is not yet complete; Issues #7–#13 remain.  
**Commits:** `1bb2230` (Issue #5), `6ed3e1f` (Issue #34), `87ea772` (Issue #35), `6942a59` (Issue #6)

---

## Verification Status

| Check                                            | Result                                                                             |
| ------------------------------------------------ | ---------------------------------------------------------------------------------- |
| 128 CSAPI unit tests                             | **PASS**                                                                           |
| 6 integration tests (endpoint.spec.ts)           | **PASS**                                                                           |
| `tsc --noEmit` (full project)                    | **CLEAN**                                                                          |
| VS Code diagnostics (all CSAPI + endpoint files) | **CLEAN**                                                                          |
| 82/83 endpoint tests pass                        | 1 pre-existing failure (EndpointError vs Error class mismatch — not CSAPI-related) |

---

## Files Reviewed

### Phase 2 — Issue #5 (Systems Methods)

- `src/ogc-api/csapi/url_builder.ts` — 12 Systems methods added (from ~211 to ~420 lines)
- `src/ogc-api/csapi/url_builder.spec.ts` — 23 new Systems tests added

### Phase 2 — Issue #34 (F1 Fix: Link Relation Discovery)

- `src/ogc-api/csapi/url_builder.ts` — `extractAvailableResources()` expanded (3 conventions)
- `src/ogc-api/csapi/url_builder.spec.ts` — 5 new constructor tests

### Phase 2 — Issue #35 (F2 Fix: Top-Level Resource URLs)

- `src/ogc-api/csapi/url_builder.ts` — constructor accepts `resourceUrls`, `buildResourceUrl()` updated
- `src/ogc-api/endpoint.ts` — `extractRootResourceUrls()` added, `csapi()` factory updated
- `src/ogc-api/csapi/url_builder.spec.ts` — 7 new top-level URL tests

### Phase 2 — Issue #6 (Deployments Methods)

- `src/ogc-api/csapi/url_builder.ts` — 8 Deployments methods added (from ~420 to 612 lines)
- `src/ogc-api/csapi/url_builder.spec.ts` — 16 new Deployments tests (total file: 893 lines)

### Phase 1 — Reaffirmation (Issues #1–#4)

- `src/ogc-api/csapi/model.ts` (542 lines) — unchanged, still solid
- `src/ogc-api/csapi/helpers.ts` (145 lines) — unchanged except F5 fix addressed in url_builder.ts
- `src/ogc-api/csapi/model.spec.ts` (355 lines, 27 tests) — unchanged
- `src/ogc-api/csapi/helpers.spec.ts` (179 lines, 30 tests) — unchanged
- `src/ogc-api/info.ts` — CSAPI detection logic unchanged
- `src/ogc-api/endpoint.spec.ts` — CSAPI integration block (6 tests) unchanged
- `src/index.ts` — CSAPI exports unchanged

---

## Phase 1 Findings — Reaffirmation

### [P1-F1] RESOLVED: `allCollections` missing `hasConnectedSystems`

**Original:** The `allCollections` getter's return type didn't include `hasConnectedSystems`.  
**Status:** **Fixed.** The type annotation at `endpoint.ts` line 179 now includes `hasConnectedSystems?: boolean`.

---

### [P1-F2] UNCHANGED: `as unknown as OgcApiCollectionInfo` cast in `csapi()`

**File:** `src/ogc-api/endpoint.ts` line 354  
**Status:** Still present, still necessary. The `csapi()` factory uses `getCollectionDocument` (raw doc with links intact) because `parseBaseCollectionInfo` strips links. The double cast is documented with a clear comment. No action needed.

---

### [P1-F3] UNCHANGED: Pre-existing EDR `edr()` missing `await`

**File:** `src/ogc-api/endpoint.ts` line 313  
**Status:** Still present (`if (!this.hasEnvironmentalDataRetrieval)` without `await`). Not our code, not our fix. Our `csapi()` correctly uses `await`.

---

### [P1-F4] STILL OPEN: Missing collection type exports from `index.ts`

**File:** `src/index.ts` lines 44–68  
**Status:** **Still partially open.** The Phase 1 review noted that `CSAPIResourceTypes` (const array), `FeatureCollection<T>`, `ItemCollection<T>`, and all collection type aliases were not exported. The current state:

| Symbol                                         | Kind                        | Exported? |
| ---------------------------------------------- | --------------------------- | --------- |
| `CSAPIResourceTypes`                           | const array (runtime value) | **No**    |
| `CommandStatusCodes`                           | const array (runtime value) | **No**    |
| `SystemTypeUris`                               | const array (runtime value) | **No**    |
| `FeatureCollection<T>`                         | generic interface           | **No**    |
| `ItemCollection<T>`                            | generic interface           | **No**    |
| `SystemCollection` … `CommandStatusCollection` | type aliases                | **No**    |

All individual resource types (`System`, `Deployment`, etc.), query options, and discriminator types **are** exported. The gaps are: runtime const arrays and collection wrapper types that consumers will need in Phase 3 when parsing responses.

**Severity:** Low (consumers don't need these until Phase 3 response parsing)  
**Recommendation:** Fix before Phase 3 begins — add `CSAPIResourceTypes`, `CommandStatusCodes`, `SystemTypeUris` as value exports and all collection/wrapper types to the `export type {}` block.

---

### [P1-F5] RESOLVED: Double-encoding in array params

**Original:** `buildQueryString` called `encodeArrayParameter()` which pre-encoded values before `URLSearchParams` encoded them again.  
**Status:** **Fixed.** `buildQueryString` at url_builder.ts line 213 now uses `value.join(',')` directly. A clear comment documents the fix:

```typescript
// Use plain join — URLSearchParams.append() handles percent-encoding.
// Previously used encodeArrayParameter() here, which pre-encoded values
// before URLSearchParams encoded them again (double-encoding bug F5).
params.append(key, value.join(','));
```

A dedicated test at url_builder.spec.ts line 346 verifies no double-encoding occurs with special characters.

---

### [P1-F6] UNCHANGED: Hardcoded temporal parameter keys

**File:** `src/ogc-api/csapi/url_builder.ts` line 203  
**Status:** Still hardcoded as a chain of `||` comparisons:

```typescript
if (key === 'datetime' || key === 'phenomenonTime' || key === 'resultTime' || key === 'issueTime' || key === 'executionTime') {
```

This works but is fragile. When Part 2 resource methods (Issues #10–#13) are added, these temporal keys will be exercised more heavily.

**Recommendation:** Extract to a `Set` before Phase 2 Part 2 work begins. No action needed now.

---

### [P1-F8] REAFFIRMED: Model types match OGC spec

All 9 resource interfaces, 10 query options, collection wrappers, and const arrays remain correct and unchanged from Phase 1. The `DeploymentQueryOptions` additions (`parent`, `systemId`, `recursive`) correctly align with the OGC spec.

---

### [P1-F9] REAFFIRMED: Test quality remains high

The Phase 1 test suite (27 model + 30 helper + 6 integration = 63 tests) is unchanged and passing. Phase 2 added 65 new url_builder tests that follow the same quality patterns.

---

## Phase 2.2 Findings — New

### [F1] DEAD CODE: `encodeArrayParameter` is no longer used

**File:** `src/ogc-api/csapi/helpers.ts` lines 106–114  
**Severity:** Style

The `encodeArrayParameter()` function was the source of the Phase 1 F5 double-encoding bug. Phase 2 fixed the bug by replacing its usage with `value.join(',')` in `buildQueryString`. However, the function itself was left in `helpers.ts` along with its test coverage in `helpers.spec.ts`.

It is not imported by any production code. It's only referenced by:

- Its own definition in `helpers.ts`
- Its tests in `helpers.spec.ts`
- A comment in `url_builder.ts` line 210 explaining why it was replaced

**Recommendation:** Remove `encodeArrayParameter` and its tests in the next cleanup pass. Low priority — it causes no harm but adds maintenance noise. Alternatively, if there's a standalone use case for the function (e.g., manual URL construction by consumers), document that intent.

---

### [F2] DESIGN: Duplicated link-scanning logic (DRY violation)

**Files:** `src/ogc-api/csapi/url_builder.ts` lines 108–149 and `src/ogc-api/endpoint.ts` lines 376–412  
**Severity:** Medium (maintainability)

The three-convention link scanning loop is implemented in two places:

| Method                        | File             | Returns                                              |
| ----------------------------- | ---------------- | ---------------------------------------------------- |
| `extractAvailableResources()` | `url_builder.ts` | `Set<string>` — resource type names only             |
| `extractRootResourceUrls()`   | `endpoint.ts`    | `Map<string, string>` — resource type → absolute URL |

Both implementations use the same regex, the same `knownTypes` Set from `CSAPIResourceTypes`, and the same three-step convention matching. The only difference is whether the `href` value is kept (Map) or discarded (Set).

If a Convention 4 is ever needed (unlikely but possible), two files must be updated in lockstep.

**Recommendation:** Extract a shared helper like `scanCsapiLinks(links): Map<string, string>` that both callers use. The Set consumer can convert with `new Set(map.keys())`. Medium priority — address before adding more link convention changes.

---

### [F3] DESIGN: `buildResourceUrl` has a latent strict-mode type safety issue

**File:** `src/ogc-api/csapi/url_builder.ts` lines 175–177  
**Severity:** Low

```typescript
const resourceBase = this.resourceUrls_.has(resourceType)
  ? this.resourceUrls_.get(resourceType).replace(/\/+$/, '')
  : `${this.baseUrl}/${resourceType}`;
```

`Map.get()` returns `T | undefined`, and TypeScript does not narrow based on a prior `.has()` call. This compiles today because the project's `tsconfig.json` does not enable `strict` or `strictNullChecks`. At runtime the `.has()` guard ensures `.get()` returns a string, so there's no actual bug.

However, if `strict` mode is ever enabled, this line will produce a compile error (`Object is possibly 'undefined'`).

**Recommendation:** Proactively add a non-null assertion: `this.resourceUrls_.get(resourceType)!.replace(...)`, or restructure to capture the value with a variable:

```typescript
const absUrl = this.resourceUrls_.get(resourceType);
const resourceBase = absUrl
  ? absUrl.replace(/\/+$/, '')
  : `${this.baseUrl}/${resourceType}`;
```

Low priority but easy fix.

---

### [F4] GAP: Weak datetime test for `getDeployments`

**File:** `src/ogc-api/csapi/url_builder.spec.ts` lines 747–753  
**Severity:** Low (test gap)

The `getDeployments` datetime test uses a **weak assertion**:

```typescript
it('returns correct URL with datetime parameter', () => {
  const url = makeDepBuilder().getDeployments({
    datetime: {
      start: new Date('2025-01-01T00:00:00Z'),
      end: new Date('2025-12-31T23:59:59Z'),
    },
  });
  expect(url).toContain('datetime='); // ← only checks key exists
});
```

Compare with `getSystems` datetime test which verifies the exact formatted value:

```typescript
expect(url).toBe(
  'https://example.com/collections/iot/systems?datetime=2024-06-01T00%3A00%3A00.000Z'
);
```

A bug in interval formatting for deployments would go undetected by the current test.

**Recommendation:** Strengthen to verify the exact URL. This is especially valuable because it tests _interval_ formatting (start/end) which is more complex than the single-instant test in getSystems.

---

### [F5] GAP: Missing `parent` and `recursive` tests for `getDeployments`

**File:** `src/ogc-api/csapi/url_builder.spec.ts`  
**Severity:** Low (test gap)

`DeploymentQueryOptions` extends `QueryOptions` with three deployment-specific fields: `parent`, `systemId`, and `recursive`. Only `systemId` is tested (line 755). The `parent` and `recursive` parameters have no test coverage for `getDeployments`.

Compare with `getSystems` which has individual tests for all six `SystemQueryOptions`-specific fields (`parent`, `procedureId`, `foiId`, `observedPropertyId`, `controlledPropertyId`, `recursive`).

**Recommendation:** Add tests for `getDeployments({ parent: 'urn:parent:1' })` and `getDeployments({ recursive: true })`.

---

### [F6] GAP: Missing pagination+filtering test for `getDeploymentSubdeployments`

**File:** `src/ogc-api/csapi/url_builder.spec.ts`  
**Severity:** Low (test asymmetry)

`getSystemSubsystems` has 3 tests: no options, recursive=true, and pagination+filtering (limit + q). `getDeploymentSubdeployments` has only 2 tests: no options and recursive=true. The pagination+filtering test was not carried over.

**Recommendation:** Add a test like:

```typescript
it('returns correct URL with pagination and filtering', () => {
  const url = makeDepBuilder().getDeploymentSubdeployments('dep-001', {
    limit: 10,
    q: 'regional',
  });
  expect(url).toBe(
    'https://example.com/collections/iot/deployments/dep-001/subdeployments?limit=10&q=regional'
  );
});
```

---

### [F7] GAP: No test coverage for cursor-based pagination

**File:** `src/ogc-api/csapi/url_builder.spec.ts`  
**Severity:** Low (untested code path)

`QueryOptions.cursor` is a defined parameter but has zero test coverage. The value correctly falls through to the generic `String(value)` handler in `buildQueryString`, so it works — but there's no test proving it.

**Recommendation:** Add a single test:

```typescript
it('returns correct URL with cursor parameter', () => {
  const url = makeIotBuilder().getSystems({ cursor: 'eyJuZXh0IjoiYWJjMTIz' });
  expect(url).toBe(
    'https://example.com/collections/iot/systems?cursor=eyJuZXh0IjoiYWJjMTIz'
  );
});
```

---

### [F8] GAP: No test for `offset` with an actual value

**File:** `src/ogc-api/csapi/url_builder.spec.ts`  
**Severity:** Low (untested code path)

`offset` appears only in the "skips undefined option values" test (line 334) where it's `undefined` and thus explicitly _not_ serialized. There's no test that passes an actual offset value to verify it appears in the query string.

**Recommendation:** Add a test:

```typescript
it('returns correct URL with offset parameter', () => {
  const url = makeIotBuilder().getSystems({ offset: 50 });
  expect(url).toBe('https://example.com/collections/iot/systems?offset=50');
});
```

---

### [F9] POSITIVE: Navigation validates parent only (correct design)

All cross-resource navigation methods (`getSystemDataStreams`, `getSystemDeployments`, `getDeploymentSystems`, etc.) validate only the **parent** resource type, not the sub-resource. For example, `getDeploymentSystems('dep-001')` asserts `deployments` is available but does not check `systems`.

This is architecturally correct — per the OGC spec, sub-resource endpoints are nested under the parent resource path (`/deployments/{id}/systems`), so what matters for URL construction is that the parent resource exists on the collection. Whether the server actually supports the sub-resource endpoint is a runtime concern for the fetch layer (Phase 3).

---

### [F10] POSITIVE: F5 fix is well-documented and regression-tested

The Phase 1 double-encoding bug (F5) was fixed cleanly. The `buildQueryString` method has a multi-line comment explaining the fix, and a dedicated test ("does not double-encode special characters in array values" at line 346) uses `sys 001` and `sys:002` to verify single-encoding.

---

### [F11] POSITIVE: Three-convention link discovery is robust

The `extractAvailableResources()` implementation (Issue #34) is well-structured:

- Convention 1 (ogc-cs: prefix) preserves backward compatibility
- Convention 2 (plain rel) uses `CSAPIResourceTypes` validation to avoid false positives from rels like `self`, `alternate`, `describedby`
- Convention 3 (items + href path) correctly strips trailing slashes before segment extraction
- All three populate the same Set, ensuring deduplication
- Verified against live server behavior (OpenSensorHub demo)

---

### [F12] POSITIVE: Top-level URL support is backward-compatible

The `resourceUrls` parameter is optional (defaulting to `new Map()`). When absent, `buildResourceUrl()` falls back to the original collection-scoped path computation. The 7 dedicated tests include a regression guard confirming collection-scoped behavior is unaffected. Trailing slash normalization is tested.

---

### [F13] POSITIVE: Deployments follow the established Systems pattern

The 8 Deployments methods are structurally identical to their Systems counterparts, making the codebase consistent and predictable. The `DeploymentQueryOptions` extensions (`parent`, `systemId`, `recursive`) are correctly handled by the generic `buildQueryString` — `parent` and `systemId` fall through to `String(value)`, and `recursive` falls through to `String(value)` producing `"true"` or `"false"`.

---

### [F14] POSITIVE: JSDoc quality is excellent

Every public method has:

- A description of what it does
- `@param` tags for all parameters
- `@returns` description
- `@throws` with the specific error type
- `@example` with realistic code
- `@see` with OGC spec links

The private helpers (`extractBaseUrl`, `extractAvailableResources`, `buildResourceUrl`, `buildQueryString`, `assertResourceAvailable`) also have thorough JSDoc, including the three-convention explanation with numbered examples.

---

### [F15] INFORMATIONAL: `recursive: false` is serialized as `?recursive=false`

Not a bug, but worth noting: if a consumer passes `recursive: false`, it serializes as `?recursive=false` in the URL. Some servers might treat the mere _presence_ of `recursive` as "true" regardless of value. The OGC spec requires the value to be interpreted, so this is correct behavior — but in practice, servers vary.

There's no test for `recursive: false`. If the design intent is that `false` should be omitted from the URL entirely (letting the server use its default), a guard would be needed in `buildQueryString`. This is a Phase 3 concern when we start testing against real servers at scale.

---

## Summary

| Category                                       | Count | Items                                                                                                                |
| ---------------------------------------------- | ----- | -------------------------------------------------------------------------------------------------------------------- |
| Phase 1 findings resolved                      | **2** | P1-F1 (allCollections type), P1-F5 (double-encoding)                                                                 |
| Phase 1 findings still open                    | **2** | P1-F4 (missing exports), P1-F6 (hardcoded temporal keys)                                                             |
| Phase 1 findings reaffirmed as not-our-concern | **2** | P1-F2 (cast), P1-F3 (EDR await)                                                                                      |
| New — dead code                                | **1** | F1 (encodeArrayParameter)                                                                                            |
| New — design issues                            | **2** | F2 (DRY violation), F3 (strict-mode latent issue)                                                                    |
| New — test gaps                                | **5** | F4 (weak datetime), F5 (missing parent/recursive), F6 (missing pagination), F7 (no cursor test), F8 (no offset test) |
| New — positive findings                        | **6** | F9–F14 (navigation design, F5 fix quality, link discovery robustness, backward compat, consistency, JSDoc quality)   |
| New — informational                            | **1** | F15 (recursive:false serialization)                                                                                  |

---

## Recommendations

### Fix Now (before next Phase 2 issue)

1. **[F4–F8] Test gaps** — Add ~6 tests to `url_builder.spec.ts`:
   - Strengthen `getDeployments` datetime test with exact URL assertion
   - Add `getDeployments({ parent: ... })` and `getDeployments({ recursive: true })` tests
   - Add `getDeploymentSubdeployments` pagination+filtering test
   - Add `getSystems({ cursor: ... })` test
   - Add `getSystems({ offset: 50 })` test

### Fix Before Phase 3

2. **[P1-F4] Add missing exports** — `CSAPIResourceTypes`, `CommandStatusCodes`, `SystemTypeUris` as value exports; `FeatureCollection`, `ItemCollection`, and all collection type aliases as type exports
3. **[F2] Extract shared link-scanning helper** — Consolidate `extractAvailableResources()` and `extractRootResourceUrls()` into a shared function
4. **[F1] Remove dead `encodeArrayParameter`** — Delete function and its tests

### Defer (Low Priority)

5. **[F3] Add non-null assertion** — `this.resourceUrls_.get(resourceType)!.replace(...)` or restructure
6. **[P1-F6] Extract temporal keys to a Set** — Before Part 2 resource methods
7. **[F15] Consider `recursive: false` omission** — Evaluate during Phase 3 server testing

---

## Root Cause Analysis — How These Issues Happened

None of these findings are mysterious bugs. They're process gaps, and tracing each one back to how it was introduced reveals a clear pattern.

### The dead code (F1 — `encodeArrayParameter`)

When the Phase 1 double-encoding bug (P1-F5) was fixed, the _call site_ in `buildQueryString` was changed to use `value.join(',')` instead of calling `encodeArrayParameter()`. But the function itself was never removed from `helpers.ts`. Classic "fix the symptom, leave the artifact" — the full dependency chain wasn't traced after the fix.

### The DRY violation (F2 — duplicated link scanning)

This is the most frustrating one because it happened _within the same session_. Issue #34 implemented the three link conventions in `extractAvailableResources()`. Then Issue #35, implemented immediately after, needed the same link scanning logic for `extractRootResourceUrls()`. Instead of extracting a shared helper from code that was _just written_, it was duplicated with a different return type. Each issue was treated as an isolated unit of work rather than stepping back and refactoring what had just been produced.

### The test gaps (F4–F8 — weaker Deployments tests)

This is the most telling pattern. When the 12 Systems methods were built (Issue #5), thorough tests were written — every `SystemQueryOptions` field got its own test, datetime used exact assertions, subsystems got a pagination test. Then when the 8 Deployments methods were built (Issue #6), _fewer_ tests were written per method. `getDeployments` tests `systemId` but not `parent` or `recursive`. The datetime test uses `toContain` instead of `toBe`. `getDeploymentSubdeployments` skips the pagination test. The _pattern_ was copied but not the _thoroughness_. The first resource type got careful attention; the second got "good enough."

This will compound if not addressed. Issues #7–#9 (Procedures, SamplingFeatures, Properties) will be the third through fifth resources using this pattern, and the temptation to write even thinner tests grows each time.

### The still-open P1-F4 (missing exports)

The Phase 1 review explicitly said "fix before Phase 2." Phase 2 work then proceeded through four issues without ever going back to address it. The review identified it, it was documented, and then it sat there. Reviews are only useful if findings get tracked as work items.

### The underlying process pattern

Three things are happening:

1. **Each issue is treated as disposable context.** Issues #34 and #35 were done back-to-back, but #34's output wasn't examined when writing #35. Each GitHub issue becomes a tunnel — get in, implement, test, commit, close, move on. There's no "step back and look at what we've built across the last 2–3 issues" moment.

2. **Second-resource-type syndrome.** The first implementation of a pattern (Systems) gets full attention. The second (Deployments) gets "it follows the same pattern, so it's fine." But the tests didn't follow the same pattern — they followed a reduced version of it.

3. **Review findings aren't tracked as work items.** Findings get documented but not converted into issues or blocking tasks. The review becomes a record rather than a forcing function.

This review is specifically designed to catch these gaps _now_, at Phase 2.2, rather than at the end of Phase 2 when the debt would be much larger.

---

## Overall Assessment

**Phase 2.2 is solid — the code works correctly and the architecture has matured significantly.** The findings here are about process discipline, not functional defects:

- The 12 Systems methods (Issue #5) and 8 Deployments methods (Issue #6) are **consistent, well-documented, and functionally correct**
- The F1 fix (three link conventions) makes the builder **spec-tolerant** — verified against a live OpenSensorHub server
- The F2 fix (top-level URLs) makes the builder **scope-aware** — verified backward-compatible with collection-scoped paths
- All existing Phase 1 infrastructure (types, helpers, integration) remains **unchanged and stable**
- The **5 test gaps** found are all low-severity (the code works correctly — it's the tests that need strengthening)
- The **DRY violation** in link scanning is the most significant design concern but is well-contained (2 files, same behavior)

The purpose of this incremental review is to catch and correct these gaps before they compound across Issues #7–#13. The findings are small individually (~30 minutes of total remediation work), but left unaddressed they would accumulate into a larger problem by the end of Phase 2.
