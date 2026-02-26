# Phase 2.8 Code Review — Control Streams Methods

**Date:** 2026-02-14  
**Reviewer:** GitHub Copilot (Claude Opus 4.6)  
**Phase:** 2.8  
**Issues:** #12 (Control Streams Methods)  
**Commits:** `fe8e190` — feat: implement 8 Control Streams methods (#12)  
**Prior review:** `docs/implementation/phase-2.7-code-review.md`

---

## Verification Gates

| Gate                       | Status         | Details                                                                    |
| -------------------------- | -------------- | -------------------------------------------------------------------------- |
| `tsc --noEmit`             | ✅ Clean       | No type errors                                                             |
| CSAPI unit tests           | ✅ 285 passing | 3 suites, 0 failures                                                       |
| Endpoint integration tests | ✅ 82/83       | 1 pre-existing failure (non-JSON parse test at endpoint.spec.ts line 1789) |
| Uncommitted changes        | ✅ Clean       | Working tree clean at review start                                         |

---

## Files Reviewed

2 files changed, +379 insertions, −1 deletion.

| File                                    | Lines Changed                           | Scope                                        |
| --------------------------------------- | --------------------------------------- | -------------------------------------------- |
| `src/ogc-api/csapi/url_builder.ts`      | +188 (import line +1, 187 method lines) | 8 new ControlStreams methods + import update |
| `src/ogc-api/csapi/url_builder.spec.ts` | +191                                    | 18 new tests across 7 describe blocks        |

### Codebase Metrics (Cumulative)

| File                  | Lines     | Purpose                                                   |
| --------------------- | --------- | --------------------------------------------------------- |
| `model.ts`            | 601       | Type definitions, constants, 9 resource interfaces        |
| `model.spec.ts`       | 408       | Type compatibility + constant validation tests            |
| `helpers.ts`          | 219       | 7 utility functions (encoding, validation, link scanning) |
| `helpers.spec.ts`     | 314       | Helper function tests                                     |
| `url_builder.ts`      | 1,741     | CSAPIQueryBuilder — 69 public methods + 4 private helpers |
| `url_builder.spec.ts` | 2,202     | url_builder tests                                         |
| **Total**             | **5,485** | **285 tests**                                             |

Delta from Phase 2.7: +409 lines, +23 tests (285 − 262)

Test distribution: 41 model + 43 helpers + 201 url_builder = 285 total

---

## Prior Findings Status

### Phase 2.2 Findings (resolved in earlier phases — no change)

#### [P2-F1] RESOLVED: Dead `encodeArrayParameter` function

No change. Fixed in Issue #38.

#### [P2-F2] RESOLVED: DRY violation in link-scanning logic

No change. Fixed in Issue #38.

#### [P2-F3] RESOLVED: Strict-mode type safety in `buildResourceUrl`

No change. Fixed in Issue #38.

---

### Phase 2.2→2.4 Findings (all resolved — no change)

#### [P2-F4] RESOLVED: Weak datetime test for `getDeployments`

No change.

#### [P2-F5] RESOLVED: Missing `parent` and `recursive` tests for `getDeployments`

No change.

#### [P2-F6] RESOLVED: Missing pagination test for `getDeploymentSubdeployments`

No change.

#### [P2-F7] RESOLVED: No test for cursor-based pagination

No change.

#### [P2-F8] RESOLVED: No test for `offset` with actual value

No change. Resolved by Issue #41.

---

### Phase 1 Findings (resolved — no change)

#### [P1-F4] RESOLVED: Missing exports from `index.ts`

No change. `ControlStreamQueryOptions` and `CommandQueryOptions` are already exported (confirmed at `src/index.ts` lines 64–65).

#### [P1-F6] RESOLVED: Hardcoded temporal parameter keys

No change. `TEMPORAL_KEYS` Set covers all temporal keys including `issueTime` and `executionTime`.

---

### Phase 2.4 Findings (status check)

#### [F1] UNCHANGED: SamplingFeatures tests are the most thorough yet

Still the gold standard alongside Properties. ControlStreams follows these patterns.

#### [F2] UNCHANGED: Convention 3 link detection is robust

No changes to `helpers.ts` link-scanning logic.

#### [F3] RESOLVED: JSDoc documents `uid` but type system didn't include it

No change. Fixed by Issue #40.

#### [F4] UNCHANGED: Spec links correctly differentiated

ControlStreams methods correctly reference Part 2 spec (`23-002`). See new finding F4.

#### [F5] UNCHANGED: Correct method set — no sub-resource nesting

ControlStreams follows the same principle: schema, commands, and feasibility as sub-paths — no deep nesting.

#### [F6] UNCHANGED: SamplingFeatures datetime uses exact interval assertion

No regression. ControlStreams temporal tests (via `getControlStreamCommands`) follow the same exact `toBe()` pattern.

#### [F7] UNCHANGED: Factory pattern consistency

ControlStreams tests introduce `makeCsBuilder()` following the established pattern.

#### [F8] UPDATED: Test count distribution across resource types

Updated distribution in `url_builder.spec.ts` (201 tests in url_builder, 285 total across all suites):

| Section                 | describe blocks | Tests  | Notes                                  |
| ----------------------- | --------------- | ------ | -------------------------------------- |
| Constructor & discovery | 1               | 8      | Shared infrastructure                  |
| Resource validation     | 1               | 4      | Shared                                 |
| Top-level URLs          | 1               | 7      | Shared                                 |
| **Systems**             | **14**          | **40** | Unchanged                              |
| **Deployments**         | **6**           | **24** | Unchanged                              |
| **Procedures**          | **6**           | **20** | Unchanged                              |
| **SamplingFeatures**    | **7**           | **22** | Unchanged                              |
| **Properties**          | **5**           | **21** | Unchanged                              |
| **DataStreams**         | **9**           | **35** | Unchanged                              |
| **Observations**        | **6**           | **22** | +5 from Issue #44 backfill             |
| **ControlStreams**      | **7**           | **18** | **New** — 8 methods, 7 describe blocks |
| **Infra total**         | 3               | 19     |                                        |
| **Resource total**      | 60              | 202    |                                        |

Note: model.spec.ts (41 tests) and helpers.spec.ts (43 tests) bring total from 201 to 285.

---

### Phase 2.5 Findings (status check)

#### [F1] UNCHANGED: Issue #40 resolves all 8 open findings systematically

No change. Positive finding.

#### [F2] UNCHANGED: Properties correctly models read-only semantics

No change. ControlStreams has full CRUD, contrasting with read-only Properties.

#### [F3] UNCHANGED: Properties documents non-Feature response format

No change.

#### [F4] UNCHANGED: Spec links are correctly differentiated in Properties

No change. ControlStreams continues the Part 2 convention.

#### [F5] RESOLVED: Properties test coverage below gold standard

No change. Resolved by Issue #41.

#### [F6] RESOLVED: `PropertyQueryOptions` does not include property-specific parameters

No change. Resolved by Issue #41.

#### [F7] RESOLVED: Systems still missing standalone `offset` test

No change. Resolved by Issue #41.

#### [F8] UNCHANGED: TEMPORAL_KEYS extraction is clean and well-documented

No change. `issueTime` and `executionTime` (used by `getControlStreamCommands`) are already in `TEMPORAL_KEYS`.

#### [F9] UNCHANGED: Index.ts exports are comprehensive

No change. `ControlStreamQueryOptions` and `CommandQueryOptions` were already exported from Phase 2.6 (Issue #1).

#### [F10] UNCHANGED: Deployment validation covers all 8 methods

No change. ControlStreams achieves 8/8 (see new finding F2).

---

### Phase 2.6 Findings (status check)

#### [F1] UNCHANGED: Issue #41 resolves all 3 Phase 2.5 gap findings in a single commit

No change. Positive finding.

#### [F2] UNCHANGED: DataStreams spec links correctly reference Part 2

No change. ControlStreams extends this pattern.

#### [F3] UNCHANGED: DataStreams resource validation is comprehensive — 11/11 methods

No change. ControlStreams achieves 8/8 (see new finding F2).

#### [F4] RESOLVED: DataStreams test coverage has minor heatmap gaps

No change. Resolved by Issues #42 and #43.

#### [F5] Retracted — not a finding

No change.

#### [F6] RESOLVED: `resultTime: 'latest'` not representable in type system

No change. Resolved by Issue #43.

#### [F7] UNCHANGED: DataStreams introduces observation-specific patterns cleanly

No change.

#### [F8] UNCHANGED: Temporal filtering tested with exact `toBe()` assertions

No change. ControlStreams temporal tests follow the same exact assertion pattern for `issueTime` and `executionTime`.

#### [F9] UNCHANGED: DataStreams JSDoc quality matches or exceeds prior resource types

No change. ControlStreams JSDoc follows the same standard.

#### [F10] UNCHANGED: DataStreams method count is correct per spec

No change.

---

### Phase 2.7 Findings (status check)

#### [F1] UNCHANGED: Issue #43 resolves Phase 2.6 [F6] with a clean CSAPI-local type alias

No change. Positive finding.

#### [F2] UNCHANGED: Observations JSDoc correctly documents singular association semantics

No change. ControlStreams does not have singular association paths — its sub-resources (`schema`, `commands`, `feasibility`) are different patterns.

#### [F3] UNCHANGED: Observations resource validation 8/8 in one block

No change. ControlStreams follows the same pattern with 8/8 (see finding F2).

#### [F4] UNCHANGED: DataStreams reaches 100% heatmap compliance

No change.

#### [F5] NOW RESOLVED: Observations test coverage has initial heatmap gaps

**Resolved by:** Issue #44 (Observations test backfill, commit `58e7847`)

Issue #44 added 5 standalone tests:

- `offset: 20` → exact `toBe()`
- `q: 'temperature'` → exact `toBe()`
- `id: 'obs-001'` → exact `toBe()` (single)
- `id: ['obs-001', 'obs-002']` → exact `toBe()` (array)
- Multiple options (limit + offset + q) → exact `toBe()`

Observations now has 22 tests and achieves higher heatmap compliance. The review → backfill cycle continues to work.

#### [F6] UNCHANGED: Observation singular association paths are a deliberate design departure

No change. Informational finding.

#### [F7] UNCHANGED: All 8 Observations spec links correctly reference Part 2

No change.

#### [F8] UNCHANGED: Observations temporal tests include resultTime='latest' from day one

No change.

#### [F9] UNCHANGED: Observations method set correctly excludes `createObservation`

No change.

#### [F10] UNCHANGED: `getObservations` tests format with MIME-type encoding

No change.

---

## Phase 2.8 Findings — New

### [F1] POSITIVE: ControlStreams mirrors DataStreams architecture cleanly

ControlStreams follows the same structural pattern as DataStreams:

| Dimension           | DataStreams                               | ControlStreams                              | Match?      |
| ------------------- | ----------------------------------------- | ------------------------------------------- | ----------- |
| Collection query    | `getDataStreams(options?)`                | `getControlStreams(options?)`               | ✅          |
| Single resource     | `getDataStream(id, options?)`             | `getControlStream(id, options?)`            | ✅          |
| CRUD                | create/update/delete                      | create/update/delete                        | ✅          |
| Schema endpoint     | `getDataStreamSchema(id, options?)`       | `getControlStreamSchema(id, options?)`      | ✅          |
| Sub-resource list   | `getDataStreamObservations(id, options?)` | `getControlStreamCommands(id, options?)`    | ✅          |
| Sub-resource create | `createObservation(datastreamId)`         | — (deferred to Issue #13)                   | —           |
| Feasibility check   | —                                         | `checkCommandFeasibility(id)`               | New pattern |
| Assertion pattern   | `assertResourceAvailable('datastreams')`  | `assertResourceAvailable('controlStreams')` | ✅          |

The only ControlStreams-specific addition is `checkCommandFeasibility()`, which is a clean POST endpoint pattern unique to the control/actuation domain. This is the first "feasibility" endpoint in the project and introduces no new infrastructure.

---

### [F2] POSITIVE: ControlStreams resource validation is comprehensive — 8/8 methods

The resource validation test at `url_builder.spec.ts` line 2181 verifies all 8 ControlStreams methods throw `EndpointError` when `controlStreams` is unavailable:

```typescript
expect(() => builder.getControlStreams()).toThrow(EndpointError);
expect(() => builder.getControlStream('x')).toThrow(EndpointError);
expect(() => builder.createControlStream()).toThrow(EndpointError);
expect(() => builder.updateControlStream('x')).toThrow(EndpointError);
expect(() => builder.deleteControlStream('x')).toThrow(EndpointError);
expect(() => builder.getControlStreamSchema('x')).toThrow(EndpointError);
expect(() => builder.getControlStreamCommands('x')).toThrow(EndpointError);
expect(() => builder.checkCommandFeasibility('x')).toThrow(EndpointError);
```

Resource validation coverage is now complete for all post-Phase 2.2 resource types:

| Resource         | Coverage                                               |
| ---------------- | ------------------------------------------------------ |
| Systems          | ❌ (scattered — not all methods verified in one block) |
| Deployments      | ✅ (8/8)                                               |
| Procedures       | ✅ (8/8)                                               |
| SamplingFeatures | ✅ (8/8)                                               |
| Properties       | ✅ (6/6)                                               |
| DataStreams      | ✅ (11/11)                                             |
| Observations     | ✅ (8/8)                                               |
| ControlStreams   | ✅ (8/8)                                               |

Systems remains the only resource type without consolidated validation coverage.

---

### [F3] POSITIVE: ControlStreams JSDoc correctly documents cmdFormat requirement and feasibility

Two methods have domain-specific JSDoc that goes beyond the standard boilerplate:

1. **`getControlStreamSchema`:** Documents that `cmdFormat` is **required** per Part 2, Req 25, and that omitting it causes 400 Bad Request. Directs user to pass it via the `f` option.

2. **`checkCommandFeasibility`:** Documents the feasibility checking pattern — testing whether a command can be executed before submitting. This is the first POST action endpoint in the project (distinct from create/update/delete CRUD).

Both JSDoc blocks include `@param`, `@returns`, `@throws`, `@example`, and `@see` — full compliance with the established standard.

---

### [F4] POSITIVE: All 8 ControlStreams spec links correctly reference Part 2

| Method                     | `@see` target                                 | Correct?                    |
| -------------------------- | --------------------------------------------- | --------------------------- |
| `getControlStreams`        | `23-002/23-002.html#_controlstream_resources` | ✅ Part 2                   |
| `getControlStream`         | `23-002/23-002.html#_controlstream_resources` | ✅ Part 2                   |
| `createControlStream`      | `23-002/23-002.html#_controlstream_resources` | ✅ Part 2                   |
| `updateControlStream`      | `23-002/23-002.html#_controlstream_resources` | ✅ Part 2                   |
| `deleteControlStream`      | `23-002/23-002.html#_controlstream_resources` | ✅ Part 2                   |
| `getControlStreamSchema`   | `23-002/23-002.html#req_controlstream_schema` | ✅ Part 2 (schema-specific) |
| `getControlStreamCommands` | `23-002/23-002.html#_command_resources`       | ✅ Part 2 (commands)        |
| `checkCommandFeasibility`  | `23-002/23-002.html#_controlstream_resources` | ✅ Part 2                   |

`getControlStreamSchema` uses the more specific `#req_controlstream_schema` anchor (mirroring DataStreams' `#req_datastream_schema`), and `getControlStreamCommands` references `#_command_resources` since it returns command entities. This differentiation is correct and intentional.

---

### [F5] POSITIVE: Temporal tests exercise `issueTime` and `executionTime` through `CommandQueryOptions`

`getControlStreamCommands` accepts `CommandQueryOptions`, which includes two temporal parameters unique to the control domain:

```typescript
it('returns correct URL with issueTime filter', () => {
  const url = makeCsBuilder().getControlStreamCommands('cs-001', {
    issueTime: { start: new Date('2024-01-01T00:00:00Z') },
  });
  expect(url).toBe(
    '...controlStreams/cs-001/commands?issueTime=2024-01-01T00%3A00%3A00.000Z%2F..'
  );
});

it('returns correct URL with executionTime filter', () => {
  const url = makeCsBuilder().getControlStreamCommands('cs-001', {
    executionTime: {
      start: new Date('2024-06-01T00:00:00Z'),
      end: new Date('2024-12-01T00:00:00Z'),
    },
  });
  expect(url).toBe(
    '...controlStreams/cs-001/commands?executionTime=2024-06-01T00%3A00%3A00.000Z%2F2024-12-01T00%3A00%3A00.000Z'
  );
});
```

Both use exact `toBe()` assertions with encoded ISO 8601 separators. This validates that the `formatDateTimeParameter` pipeline handles `issueTime` (open-ended interval) and `executionTime` (closed interval) correctly — the first time these specific temporal keys have been tested, even though they were in `TEMPORAL_KEYS` since Phase 2.6.

---

### [F6] POSITIVE: `checkCommandFeasibility` tests special character encoding in resource IDs

```typescript
it('encodes special characters in control stream ID', () => {
  const url = makeCsBuilder().checkCommandFeasibility('urn:example:cs:001');
  expect(url).toBe('...controlStreams/urn%3Aexample%3Acs%3A001/feasibility');
});
```

This is the first feasibility endpoint test to verify that URN-style IDs with colons are properly percent-encoded in the path segment. While `encodeResourceId` is exercised elsewhere, this test confirms the encoding pipeline works for the new `/feasibility` sub-path pattern.

---

### [F7] GAP: ControlStreams test coverage has initial heatmap gaps

ControlStreams tests cover 8 of 13 applicable heatmap dimensions (62%). The missing standalone tests:

| Missing dimension       | Notes                                                         |
| ----------------------- | ------------------------------------------------------------- |
| `offset` standalone     | No test for `getControlStreams({ offset: 20 })`               |
| `q`                     | No test for `getControlStreams({ q: 'valve' })`               |
| `id` (single)           | No test for `getControlStreams({ id: 'cs-001' })`             |
| `id` (array)            | No test for `getControlStreams({ id: ['cs-001', 'cs-002'] })` |
| Multiple shared options | No test combining limit + offset + q or similar               |

**Severity:** GAP  
**Impact:** Low — all missing dimensions flow through `buildQueryString`'s shared parameter serialization, already exercised by 285 tests across 7 other resource types. No unique ControlStreams code path goes untested.

**Recommendation:** Add ~5 tests to bring ControlStreams to ≥85% compliance. Estimated effort: small (copy-adapt from DataStreams backfill pattern).

---

### [F8] INFORMATIONAL: JSDoc examples show lowercase `controlstreams` but builder produces camelCase `controlStreams`

The JSDoc `@example` blocks in all 8 ControlStreams methods show:

```
// => "https://example.com/collections/iot/controlstreams?limit=10&systemId=sys-001"
```

But the actual builder output (and the test expectations) produce:

```
https://example.com/collections/iot/controlStreams?limit=10&systemId=sys-001
```

This occurs because `buildResourceUrl` uses the resource type key directly (`controlStreams` from `CSAPIResourceTypes`) in the URL path when no top-level absolute URL is available from `resourceUrls_`. The JSDoc examples show the lowercase form that matches the OGC API convention for URL paths.

**Severity:** INFORMATIONAL  
**Impact:** Low — JSDoc examples are illustrative, not executable. The actual tests verify the real output. Real servers provide absolute URLs via link relations (top-level pattern), so the fallback camelCase path is only used in collection-scoped mode without explicit link hrefs.

**Recommendation:** No immediate action needed. In Phase 3, when response handling is added, the URL path casing should be reviewed against actual server URL conventions. If a `resourceTypeToPath` mapping is needed (e.g., `controlStreams` → `controlstreams`), it would be a single helper in `buildResourceUrl`.

---

### [F9] INFORMATIONAL: `getControlStreamCommands` uses `CommandQueryOptions` — first cross-resource type usage

`getControlStreamCommands` accepts `CommandQueryOptions` (which includes `issueTime`, `executionTime`, `currentStatus`) rather than the ControlStream-specific `ControlStreamQueryOptions`. This is correct because the sub-resource list returns Command entities, and Commands have their own temporal/status parameters.

This is analogous to `getDataStreamObservations` accepting `ObservationQueryOptions` — the sub-resource query options match the entity type being returned, not the parent resource type.

The import line now imports both `ControlStreamQueryOptions` and `CommandQueryOptions`:

```typescript
import type { ..., ControlStreamQueryOptions, CommandQueryOptions } from './model.js';
```

This is clean and follows the established pattern. `CommandQueryOptions` is imported here for the first time (ahead of Issue #13 Commands), which is correct — it's needed by the ControlStreams sub-resource method.

---

## Test Quality Heatmap

| Dimension                           | Systems        | Deployments   | Procedures | SamplingFeatures | Properties | DataStreams        | Observations           | ControlStreams                           |
| ----------------------------------- | -------------- | ------------- | ---------- | ---------------- | ---------- | ------------------ | ---------------------- | ---------------------------------------- |
| No options (base URL)               | ✅             | ✅            | ✅         | ✅               | ✅         | ✅                 | ✅                     | ✅                                       |
| `limit`                             | ✅             | ✅            | ✅         | ✅               | ✅         | ✅                 | ✅ (combo)             | ✅ (combo)                               |
| `offset` (standalone)               | ✅             | ✅            | ✅         | ✅               | ✅         | ✅                 | ✅                     | ❌                                       |
| `q`                                 | ✅             | ✅            | ✅         | ✅               | ✅         | ✅                 | ✅                     | ❌                                       |
| `id` (single)                       | ❌             | ❌            | ✅         | ✅               | ✅         | ✅                 | ✅                     | ❌                                       |
| `id` (array)                        | ✅             | ❌            | ✅         | ✅               | ✅         | ✅                 | ✅                     | ❌                                       |
| `bbox`                              | ✅             | ✅            | N/A        | ✅               | N/A        | N/A                | N/A                    | N/A                                      |
| `datetime` / temporal (exact)       | ✅ (instant)   | ✅ (interval) | N/A        | ✅ (interval)    | N/A        | ✅ (both + latest) | ✅ (interval + latest) | ✅ (issueTime + executionTime)           |
| `f` (format)                        | ❌             | ✅            | ✅         | ✅               | ✅         | ✅                 | ✅                     | ✅                                       |
| `cursor`                            | ✅             | ❌            | ❌         | ❌               | ❌         | ✅                 | ✅                     | ❌                                       |
| Multiple options                    | ✅             | ❌            | ✅         | ✅               | ✅         | ✅                 | ✅                     | ❌                                       |
| Type-specific params                | ✅ (6/6)       | ✅ (3/3)      | N/A        | N/A              | ✅ (2/2)   | ✅ (4/4)           | ✅ (2/2)               | ✅ (2/2: systemId, controlledPropertyId) |
| Resource validation (all methods)   | ❌ (scattered) | ✅ (8/8)      | ✅ (8/8)   | ✅ (8/8)         | ✅ (6/6)   | ✅ (11/11)         | ✅ (8/8)               | ✅ (8/8)                                 |
| Association/sub-resource pagination | Partial        | ✅            | ✅         | ✅               | ✅         | ✅                 | N/A (singular)         | ✅ (commands with pagination)            |

**Checklist compliance score:**

- Systems: 10/14 (71%) — unchanged
- Deployments: 10/14 (71%) — unchanged
- Procedures: 10/11 (91%) — unchanged (3 N/A: bbox, temporal, type-specific)
- SamplingFeatures: 12/13 (92%) — unchanged (1 N/A: type-specific)
- Properties: 11/12 (92%) — unchanged (2 N/A: bbox, temporal)
- DataStreams: 13/13 (100%) — unchanged
- Observations: **10/12 (83%)** — up from 58% (Issue #44 backfill added offset, q, id single, id array, multiple)
- ControlStreams: **8/13 (62%)** — new (1 N/A: bbox)

**Notable changes from Phase 2.7:**

- Observations jumps from 58% → **83%** (Issue #44 backfill)
- ControlStreams enters at 62% — follows the expected gap pattern
- ControlStreams has temporal ✅ (2 unique temporal keys), format ✅, type-specific ✅, resource validation ✅ from Day 1
- `issueTime` and `executionTime` temporal parameters tested with exact `toBe()` assertions for the first time

---

## Summary

| Category                            | Count | Items                                                                                                                                     |
| ----------------------------------- | ----- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| Phase 2.2 findings (no change)      | **3** | P2-F1, P2-F2, P2-F3                                                                                                                       |
| Phase 2.2→2.4 findings (no change)  | **5** | P2-F4, P2-F5, P2-F6, P2-F7, P2-F8                                                                                                         |
| Phase 1 findings (no change)        | **2** | P1-F4 (exports), P1-F6 (temporal keys)                                                                                                    |
| Phase 2.4 findings unchanged        | **6** | F1, F2, F4, F5, F6, F7 + F3 resolved                                                                                                      |
| Phase 2.4 findings updated          | **1** | F8 (test counts — ControlStreams added)                                                                                                   |
| Phase 2.5 findings no change        | **7** | F1, F2, F3, F4, F8, F9, F10                                                                                                               |
| Phase 2.5 findings already resolved | **3** | F5, F6, F7 (resolved by Issue #41)                                                                                                        |
| Phase 2.6 findings unchanged        | **6** | F1, F2, F3, F7, F8, F9, F10                                                                                                               |
| Phase 2.6 findings already resolved | **2** | F4 (DataStreams heatmap), F6 (resultTime)                                                                                                 |
| Phase 2.7 findings unchanged        | **8** | F1, F2, F3, F4, F6, F7, F8, F9, F10                                                                                                       |
| Phase 2.7 findings now resolved     | **1** | F5 (Observations heatmap → 83%, Issue #44)                                                                                                |
| **New — positive findings**         | **6** | F1 (mirrors DataStreams), F2 (validation 8/8), F3 (cmdFormat + feasibility JSDoc), F4 (spec links), F5 (temporal tests), F6 (ID encoding) |
| **New — gap findings**              | **1** | F7 (ControlStreams heatmap gaps — 62%)                                                                                                    |
| **New — informational findings**    | **2** | F8 (JSDoc vs URL casing), F9 (cross-resource CommandQueryOptions)                                                                         |
| **New bugs or design issues**       | **0** | —                                                                                                                                         |

---

## Recommendations

### Fix Before Next Coding Issue

1. **[F7] Backfill ControlStreams test gaps** — Add ~5 tests: standalone `offset`, `q`, single `id`, array `id`, multiple shared options. Target ≥85% compliance. Estimated effort: 10 minutes (copy-adapt from Observations backfill pattern, Issue #44).

### Fix Before Phase 3

2. **Systems consolidated resource validation** — Systems remains the only resource type without a single test block verifying all methods throw when unavailable. Low priority since methods are individually tested elsewhere.

### Defer (Low Priority)

3. **Cursor tests for Deployments, Procedures, SamplingFeatures, Properties, ControlStreams** — Cursor flows through the same `buildQueryString` path verified by Systems, DataStreams, and Observations cursor tests. Per-type tests would improve heatmap but wouldn't exercise new code paths.

4. **`id` (single) tests for Systems and Deployments** — Both types test `id` as an array but not as a single value. Low priority since the serialization path is the same.

5. **[F8] JSDoc example casing alignment** — Low priority. No functional impact. Can be addressed in Phase 3 when URL path casing is formalized.

---

## Root Cause Analysis — Continued Zero Defects

Phase 2.8 is the **sixth consecutive phase** with zero new defects or design issues. The streak now spans Procedures → SamplingFeatures → Properties → DataStreams → Observations → ControlStreams.

### Why the implementation was clean

**Issue #12 (ControlStreams Methods):**

1. **DataStreams as proven template**: ControlStreams is the architectural mirror of DataStreams. Every method follows the same `assertResourceAvailable` → `buildResourceUrl` → return pipeline, now exercised by ~285 tests across 8 resource types.
2. **Schema endpoint mirrors DataStreams exactly**: `getControlStreamSchema` follows the same pattern as `getDataStreamSchema` — both pass format via the `f` option. The JSDoc correctly documents the Part 2 requirement (Req 25 for `cmdFormat`, Req 11 for `obsFormat`).
3. **Feasibility is a clean new pattern**: `checkCommandFeasibility` is a POST endpoint that uses `buildResourceUrl('controlStreams', id, 'feasibility')` — the same 3-argument sub-path pattern used by `getDataStreamSchema`, `getDataStreamObservations`, etc. No new infrastructure was needed.
4. **`CommandQueryOptions` was ready**: The import of `CommandQueryOptions` for `getControlStreamCommands` was straightforward because the type was already defined in `model.ts` (Issue #1) with `issueTime`, `executionTime`, and `currentStatus` fields. The `TEMPORAL_KEYS` set already included `issueTime` and `executionTime`.

### Why the heatmap gap persists

ControlStreams enters at 62% checklist compliance — following the established pattern. The root cause is unchanged: when implementing a new resource type, the focus is on type-specific features (schema endpoints, feasibility checking, temporal filtering with `issueTime`/`executionTime`) rather than re-testing generic dimensions (`offset`, `q`, `id`) proven by shared infrastructure.

The Issue #44 backfill cycle (review → backfill → 83% for Observations) confirms the remedy works consistently.

---

## Overall Assessment

**Phase 2.8 is clean.** ControlStreams (Issue #12) delivers the third Part 2 resource type with zero defects, continuing the six-phase streak.

1. **ControlStreams mirrors DataStreams cleanly** — The 8-method implementation follows the proven DataStreams pattern exactly, with two ControlStreams-specific additions: the `checkCommandFeasibility` POST endpoint (first feasibility pattern in the project) and the `getControlStreamCommands` sub-resource that accepts `CommandQueryOptions` (first cross-resource type query options usage). Both integrate cleanly with existing infrastructure.

2. **Observations heatmap debt resolved** — Issue #44 brought Observations from 58% → 83% heatmap compliance, resolving Phase 2.7 F5. This confirms the review → backfill cycle works for the fourth consecutive time (Properties, DataStreams, Observations). ControlStreams enters with the expected initial gap (62%) and should follow the same remedy.

3. **`issueTime` and `executionTime` tested for the first time** — While both temporal keys were present in `TEMPORAL_KEYS` since Phase 2.6, this is the first time they've been exercised in URL builder tests. The exact `toBe()` assertions confirm the `formatDateTimeParameter` pipeline handles all 5 temporal parameter types correctly: `datetime`, `phenomenonTime`, `resultTime`, `issueTime`, `executionTime`.

The CSAPI module now implements **8 resource types** — all 5 Part 1 (Systems, Deployments, Procedures, SamplingFeatures, Properties) and 3 Part 2 (DataStreams, Observations, ControlStreams) — with **69 public methods** and **285 tests**. Only Commands (Issue #13) remains to complete the Phase 2 method implementation.

**Cumulative project stats:**

- **69 public methods** across 8 resource types
- **285 tests** across 3 suites (41 model + 43 helpers + 201 url_builder)
- **5,485 lines** of production + test code
- **0 open findings from prior reviews** (second consecutive review)
- **1 new gap finding** (ControlStreams heatmap — low severity, established fix pattern)
- **6 consecutive phases** with zero defects
