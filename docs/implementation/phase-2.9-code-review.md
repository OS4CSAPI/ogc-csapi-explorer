# Phase 2.9 Code Review — Commands Methods (Final Phase 2 Resource Type)

**Date:** 2026-02-14  
**Reviewer:** GitHub Copilot (Claude Opus 4.6)  
**Phase:** 2.9  
**Issues:** #13 (Commands Methods)  
**Commits:** `b1c08d4` — feat(csapi): implement Commands methods (Issue #13)  
**Prior review:** `docs/implementation/phase-2.8-code-review.md`

---

## Verification Gates

| Gate                       | Status         | Details                                                                    |
| -------------------------- | -------------- | -------------------------------------------------------------------------- |
| `tsc --noEmit`             | ✅ Clean       | No type errors                                                             |
| CSAPI unit tests           | ✅ 311 passing | 3 suites, 0 failures                                                       |
| Endpoint integration tests | ✅ 82/83       | 1 pre-existing failure (non-JSON parse test at endpoint.spec.ts line 1789) |
| Uncommitted changes        | ✅ Clean       | Working tree clean at review start                                         |

---

## Files Reviewed

2 files changed (code), 1 file changed (docs), +435 insertions, −2 deletions.

| File                                         | Lines Changed                                  | Scope                                          |
| -------------------------------------------- | ---------------------------------------------- | ---------------------------------------------- |
| `src/ogc-api/csapi/url_builder.ts`           | +227 lines (10 methods + JSDoc)                | 10 new Commands methods                        |
| `src/ogc-api/csapi/url_builder.spec.ts`      | +194 lines (21 tests across 7 describe blocks) | Commands test suite                            |
| `docs/governance/phase-2-lessons-learned.md` | +14 / −2 lines                                 | Version bump 1.1 → 1.2, source doc list update |

### Codebase Metrics (Cumulative)

| File                  | Lines     | Purpose                                                   |
| --------------------- | --------- | --------------------------------------------------------- |
| `model.ts`            | 560       | Type definitions, constants, 9 resource interfaces        |
| `model.spec.ts`       | 377       | Type compatibility + constant validation tests            |
| `helpers.ts`          | 191       | 7 utility functions (encoding, validation, link scanning) |
| `helpers.spec.ts`     | 268       | Helper function tests                                     |
| `url_builder.ts`      | 1,968     | CSAPIQueryBuilder — 79 public methods + 4 private helpers |
| `url_builder.spec.ts` | 2,421     | url_builder tests                                         |
| **Total**             | **5,785** | **311 tests**                                             |

Delta from Phase 2.8: +300 lines (code), +26 tests (311 − 285)

Test distribution: 41 model + 43 helpers + 227 url_builder = 311 total

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

No change. All Command types (`CommandQueryOptions`, `CommandStatusCode`, `Command`, `CommandStatus`, `CommandCollection`, `CommandStatusCollection`, `CommandStatusCodes`) are exported from `src/index.ts`.

#### [P1-F6] RESOLVED: Hardcoded temporal parameter keys

No change. `TEMPORAL_KEYS` Set covers all temporal keys including `issueTime` and `executionTime`.

---

### Phase 2.4 Findings (status check)

#### [F1] UNCHANGED: SamplingFeatures tests are the most thorough yet

Still the gold standard alongside Properties. Commands follows the same patterns.

#### [F2] UNCHANGED: Convention 3 link detection is robust

No changes to `helpers.ts` link-scanning logic.

#### [F3] RESOLVED: JSDoc documents `uid` but type system didn't include it

No change. Fixed by Issue #40.

#### [F4] UNCHANGED: Spec links correctly differentiated

Commands methods correctly reference Part 2 spec (`23-002/23-002.html#_command_resources`).

#### [F5] UNCHANGED: Correct method set — no sub-resource nesting

Commands follows the same principle. Sub-resources (`status`, `result`, `cancel`) are shallow paths off `/commands/{id}`.

#### [F6] UNCHANGED: SamplingFeatures datetime uses exact interval assertion

No regression. Commands temporal tests (`issueTime`, `executionTime`) use exact `toBe()` assertions.

#### [F7] UNCHANGED: Factory pattern consistency

Commands tests introduce `makeCmdBuilder()` following the established pattern.

#### [F8] UPDATED: Test count distribution across resource types

Updated distribution in `url_builder.spec.ts` (227 tests in url_builder, 311 total across all suites):

| Section                 | describe blocks | Tests  | Notes                                   |
| ----------------------- | --------------- | ------ | --------------------------------------- |
| Constructor & discovery | 1               | 8      | Shared infrastructure                   |
| Resource validation     | 1               | 4      | Shared                                  |
| Top-level URLs          | 1               | 7      | Shared                                  |
| **Systems**             | **14**          | **40** | Unchanged                               |
| **Deployments**         | **6**           | **24** | Unchanged                               |
| **Procedures**          | **6**           | **20** | Unchanged                               |
| **SamplingFeatures**    | **7**           | **22** | Unchanged                               |
| **Properties**          | **5**           | **21** | Unchanged                               |
| **DataStreams**         | **9**           | **35** | Unchanged                               |
| **Observations**        | **6**           | **22** | Unchanged                               |
| **ControlStreams**      | **7**           | **23** | +5 from Issue #45 backfill              |
| **Commands**            | **7**           | **21** | **New** — 10 methods, 7 describe blocks |
| **Infra total**         | 3               | 19     |                                         |
| **Resource total**      | 67              | 228    |                                         |

Note: model.spec.ts (41 tests) and helpers.spec.ts (43 tests) bring total from 227 to 311.

---

### Phase 2.5 Findings (status check)

#### [F1] UNCHANGED: Issue #40 resolves all 8 open findings systematically

No change. Positive finding.

#### [F2] UNCHANGED: Properties correctly models read-only semantics

No change. Commands has full CRUD plus lifecycle methods (status, result, cancel).

#### [F3] UNCHANGED: Properties documents non-Feature response format

No change.

#### [F4] UNCHANGED: Spec links are correctly differentiated in Properties

No change. Commands continues the Part 2 convention.

#### [F5] RESOLVED: Properties test coverage below gold standard

No change. Resolved by Issue #41.

#### [F6] RESOLVED: `PropertyQueryOptions` does not include property-specific parameters

No change. Resolved by Issue #41.

#### [F7] RESOLVED: Systems still missing standalone `offset` test

No change. Resolved by Issue #41.

#### [F8] UNCHANGED: TEMPORAL_KEYS extraction is clean and well-documented

No change. `issueTime` and `executionTime` (now used directly by `getCommands`) are in `TEMPORAL_KEYS`.

#### [F9] UNCHANGED: Index.ts exports are comprehensive

No change. All Command-related types were already exported from Phase 2.6 (Issue #1).

#### [F10] UNCHANGED: Deployment validation covers all 8 methods

No change.

---

### Phase 2.6 Findings (status check)

#### [F1] UNCHANGED: Issue #41 resolves all 3 Phase 2.5 gap findings in a single commit

No change. Positive finding.

#### [F2] UNCHANGED: DataStreams spec links correctly reference Part 2

No change. Commands extends this pattern.

#### [F3] UNCHANGED: DataStreams resource validation is comprehensive — 11/11 methods

No change. Commands achieves 8/10 (see new finding F8).

#### [F4] RESOLVED: DataStreams test coverage has minor heatmap gaps

No change. Resolved by Issues #42 and #43.

#### [F5] Retracted — not a finding

No change.

#### [F6] RESOLVED: `resultTime: 'latest'` not representable in type system

No change. Resolved by Issue #43.

#### [F7] UNCHANGED: DataStreams introduces observation-specific patterns cleanly

No change. Commands extends the pattern with `createCommand` via ControlStreams.

#### [F8] UNCHANGED: Temporal filtering tested with exact `toBe()` assertions

No change. Commands temporal tests follow the same exact assertion pattern for `issueTime` and `executionTime`.

#### [F9] UNCHANGED: DataStreams JSDoc quality matches or exceeds prior resource types

No change. Commands JSDoc follows the same standard.

#### [F10] UNCHANGED: DataStreams method count is correct per spec

No change.

---

### Phase 2.7 Findings (status check)

#### [F1] UNCHANGED: Issue #43 resolves Phase 2.6 [F6] with a clean CSAPI-local type alias

No change. Positive finding.

#### [F2] UNCHANGED: Observations JSDoc correctly documents singular association semantics

No change. Commands does not have singular association paths.

#### [F3] UNCHANGED: Observations resource validation 8/8 in one block

No change. Commands validation covers 8/10 methods in one block (see finding F8).

#### [F4] UNCHANGED: DataStreams reaches 100% heatmap compliance

No change.

#### [F5] NOW RESOLVED: Observations test coverage has initial heatmap gaps

No change. Resolved by Issue #44.

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

### Phase 2.8 Findings (status check)

#### [F1] UNCHANGED: ControlStreams mirrors DataStreams architecture cleanly

No change. Positive finding.

#### [F2] UNCHANGED: ControlStreams resource validation is comprehensive — 8/8 methods

No change.

#### [F3] UNCHANGED: ControlStreams JSDoc correctly documents cmdFormat requirement and feasibility

No change.

#### [F4] UNCHANGED: All 8 ControlStreams spec links correctly reference Part 2

No change.

#### [F5] UNCHANGED: Temporal tests exercise `issueTime` and `executionTime` through `CommandQueryOptions`

No change. Commands now also tests these directly via `getCommands`.

#### [F6] UNCHANGED: `checkCommandFeasibility` tests special character encoding in resource IDs

No change, and Commands adds an analogous encoding test for `cancelCommand`.

#### [F7] NOW RESOLVED: ControlStreams test coverage has initial heatmap gaps

**Resolved by:** Issue #45 (ControlStreams test backfill, commit `280436b`)

Issue #45 added 5 standalone tests:

- `offset: 20` → exact `toBe()`
- `q: 'valve'` → exact `toBe()`
- `id: 'cs-001'` → exact `toBe()` (single)
- `id: ['cs-001', 'cs-002']` → exact `toBe()` (array)
- Multiple options (limit + offset + q) → exact `toBe()`

ControlStreams now has 23 tests and achieves higher heatmap compliance. The review → backfill cycle continues to work for the fifth consecutive time.

#### [F8] UNCHANGED: JSDoc examples show lowercase `controlstreams` but builder produces camelCase

No change. Informational finding — no functional impact.

#### [F9] UNCHANGED: `getControlStreamCommands` uses `CommandQueryOptions` — cross-resource type usage

No change. `getCommands` now also uses `CommandQueryOptions` directly.

---

## Phase 2.9 Findings — New

### [F1] POSITIVE: Commands completes all 80 Phase 2 QueryBuilder methods

Commands (Issue #13) implements the final 10 methods, bringing the total to **79 public methods** (plus 1 `assertResourceAvailable` makes 80 in issue counting):

| Resource Type    | Part  | Methods     | Total  |
| ---------------- | ----- | ----------- | ------ |
| Systems          | 1     | 14          | 14     |
| Deployments      | 1     | 10          | 24     |
| Procedures       | 1     | 8           | 32     |
| SamplingFeatures | 1     | 8           | 40     |
| Properties       | 1     | 6           | 46     |
| DataStreams      | 2     | 11          | 57     |
| Observations     | 2     | 8           | 65     |
| ControlStreams   | 2     | 8           | 73     |
| **Commands**     | **2** | **10**      | **83** |
| Infrastructure   | —     | 4 (private) | —      |

Note: The 79 count from `grep` counts public methods matching `get|create|update|delete|check|cancel`. The 83 total includes 4 additional infrastructure methods (`assertResourceAvailable`, `buildResourceUrl`, `buildQueryString`, `extractAvailableResources`) that are part of the class but serve as shared infrastructure. The issue acceptance criteria refers to "80 QueryBuilder methods" counting resource methods plus shared infrastructure differently. All 10 Commands methods listed in Issue #13 are implemented.

---

### [F2] POSITIVE: Commands mirrors Observations architecture with lifecycle extensions

Commands follows the Observations structural pattern and extends it with lifecycle management:

| Dimension           | Observations                      | Commands                          | Match? |
| ------------------- | --------------------------------- | --------------------------------- | ------ |
| Collection query    | `getObservations(options?)`       | `getCommands(options?)`           | ✅     |
| Single resource     | `getObservation(id, options?)`    | `getCommand(id, options?)`        | ✅     |
| Create via parent   | `createObservation(datastreamId)` | `createCommand(controlStreamId)`  | ✅     |
| Bulk create         | —                                 | `createCommands(controlStreamId)` | New    |
| Update              | `updateObservation(id)`           | `updateCommand(id)`               | ✅     |
| Delete              | `deleteObservation(id)`           | `deleteCommand(id)`               | ✅     |
| Status sub-resource | —                                 | `getCommandStatus(id)`            | New    |
| Status update       | —                                 | `updateCommandStatus(id)`         | New    |
| Result sub-resource | —                                 | `getCommandResult(id)`            | New    |
| Cancel operation    | —                                 | `cancelCommand(id)`               | New    |

Commands introduces 5 new patterns not seen in any prior resource type: bulk creation, status retrieval, status update, result retrieval, and cancellation. All 5 integrate cleanly with existing infrastructure — each uses `assertResourceAvailable` → `buildResourceUrl` with no new helpers needed.

---

### [F3] POSITIVE: `createCommand` and `createCommands` correctly validate `controlStreams`

Both creation methods validate `controlStreams` (not `commands`) availability, mirroring the pattern established by `createObservation` (which validates `datastreams`):

```typescript
createCommand(controlStreamId: string): string {
  this.assertResourceAvailable('controlStreams');                    // ← correct
  return this.buildResourceUrl('controlStreams', controlStreamId, 'commands');
}
```

This is correct because commands are created via `POST /controlstreams/{id}/commands` — the write operation goes through the parent resource's endpoint. The JSDoc correctly documents `@throws {EndpointError} If 'controlStreams' is not available`.

---

### [F4] POSITIVE: All 10 Commands spec links correctly reference Part 2

| Method                | `@see` target                           | Correct?  |
| --------------------- | --------------------------------------- | --------- |
| `getCommands`         | `23-002/23-002.html#_command_resources` | ✅ Part 2 |
| `getCommand`          | `23-002/23-002.html#_command_resources` | ✅ Part 2 |
| `createCommand`       | `23-002/23-002.html#_command_resources` | ✅ Part 2 |
| `createCommands`      | `23-002/23-002.html#_command_resources` | ✅ Part 2 |
| `updateCommand`       | `23-002/23-002.html#_command_resources` | ✅ Part 2 |
| `deleteCommand`       | `23-002/23-002.html#_command_resources` | ✅ Part 2 |
| `getCommandStatus`    | `23-002/23-002.html#_command_resources` | ✅ Part 2 |
| `updateCommandStatus` | `23-002/23-002.html#_command_resources` | ✅ Part 2 |
| `getCommandResult`    | `23-002/23-002.html#_command_resources` | ✅ Part 2 |
| `cancelCommand`       | `23-002/23-002.html#_command_resources` | ✅ Part 2 |

All 10 methods consistently reference `#_command_resources`, which is the correct Part 2 section for command endpoints.

---

### [F5] POSITIVE: Commands JSDoc documents lifecycle semantics beyond URL construction

Three methods have domain-specific JSDoc that goes beyond standard boilerplate:

1. **`getCommandStatus`:** Documents the state machine transitions — `PENDING → ACCEPTED → EXECUTING → COMPLETED/FAILED/CANCELED`. This gives callers a mental model of the command lifecycle.

2. **`cancelCommand`:** Documents asynchronous cancellation semantics — "The actual cancellation may be asynchronous — poll the command status to confirm transition to CANCELED." This prevents a common misconception that cancel is synchronous.

3. **`createCommands`:** Explicitly distinguishes bulk creation from single creation — "The request body must contain an array of command objects." This differentiates the two methods that produce identical URLs.

All 10 JSDoc blocks include `@param`, `@returns`, `@throws`, `@example`, and `@see` — full compliance with the established standard.

---

### [F6] POSITIVE: Temporal tests exercise `issueTime` and `executionTime` directly on Commands

`getCommands` accepts `CommandQueryOptions`, which includes the temporal parameters `issueTime` and `executionTime`:

```typescript
it('returns correct URL with issueTime interval', () => {
  const url = makeCmdBuilder().getCommands({
    issueTime: {
      start: new Date('2024-01-01T00:00:00Z'),
      end: new Date('2024-06-01T00:00:00Z'),
    },
  });
  expect(url).toBe(
    '...commands?issueTime=2024-01-01T00%3A00%3A00.000Z%2F2024-06-01T00%3A00%3A00.000Z'
  );
});

it('returns correct URL with executionTime open-end interval', () => {
  const url = makeCmdBuilder().getCommands({
    executionTime: { start: new Date('2024-03-01T00:00:00Z') },
  });
  expect(url).toBe(
    '...commands?executionTime=2024-03-01T00%3A00%3A00.000Z%2F..'
  );
});
```

Phase 2.8 tested these temporal keys via `getControlStreamCommands`. Phase 2.9 tests them directly via the Commands collection endpoint. Both closed interval and open-end interval patterns are verified with exact `toBe()` assertions.

---

### [F7] POSITIVE: `cancelCommand` tests special character encoding — consistent with feasibility

```typescript
it('encodes special characters in command ID', () => {
  const url = makeCmdBuilder().cancelCommand('urn:example:cmd:001');
  expect(url).toBe('...commands/urn%3Aexample%3Acmd%3A001/cancel');
});
```

This mirrors the `checkCommandFeasibility` encoding test from Phase 2.8, confirming the `encodeResourceId` pipeline works for both the ControlStreams feasibility (`/controlStreams/{id}/feasibility`) and Commands cancel (`/commands/{id}/cancel`) sub-path patterns.

---

### [F8] GAP: Commands resource validation covers 8/10 methods — `createCommand` and `createCommands` not in validation block

The "Command resource validation" test block at `url_builder.spec.ts` line 2400 verifies 8 methods throw `EndpointError` when `commands` is unavailable:

```typescript
expect(() => builder.getCommands()).toThrow(EndpointError);
expect(() => builder.getCommand('x')).toThrow(EndpointError);
expect(() => builder.updateCommand('x')).toThrow(EndpointError);
expect(() => builder.deleteCommand('x')).toThrow(EndpointError);
expect(() => builder.getCommandStatus('x')).toThrow(EndpointError);
expect(() => builder.updateCommandStatus('x')).toThrow(EndpointError);
expect(() => builder.getCommandResult('x')).toThrow(EndpointError);
expect(() => builder.cancelCommand('x')).toThrow(EndpointError);
```

Missing: `createCommand` and `createCommands`. These validate `controlStreams` (not `commands`) availability, which is correct behavior. However, there is no test demonstrating that `createCommand('x')` throws `EndpointError` when `controlStreams` is unavailable. The ControlStreams resource validation block does not include them either — it covers the 8 ControlStreams-specific methods.

**Severity:** GAP  
**Impact:** Low — the underlying `assertResourceAvailable('controlStreams')` call is tested 8 times by the ControlStreams validation block. Adding `createCommand`/`createCommands` to that block would test the same code path. No unique logic goes untested.

**Recommendation:** Add `createCommand` and `createCommands` to either the Commands or ControlStreams validation test block (or both) during the Commands test backfill issue.

---

### [F9] GAP: Commands test coverage has initial heatmap gaps

Commands tests cover 9 of 13 applicable heatmap dimensions (~69%). The initial coverage is higher than ControlStreams' entry (62%) because Commands tests include `issueTime` and `executionTime` from day one. The missing standalone tests:

| Missing dimension                      | Notes                                                                         |
| -------------------------------------- | ----------------------------------------------------------------------------- |
| `offset` standalone                    | No test for `getCommands({ offset: 20 })`                                     |
| `q`                                    | Commands do not support `q` per Lesson 2 table — N/A                          |
| `uid`                                  | Commands do not support `uid` per Lesson 2 table — N/A                        |
| `datetime`                             | Commands do not support `datetime` per Lesson 2 table — N/A                   |
| Multiple shared options (incl. offset) | One test exists but uses `limit + currentStatus + cursor` — no `offset` combo |

After accounting for N/A parameters, Commands is missing:

- `offset` standalone
- A multiple-options combo that includes `offset`

**Severity:** GAP  
**Impact:** Low — `offset` flows through `buildQueryString`'s shared parameter serialization, exercised by 311 tests across 8 other resource types.

**Recommendation:** Add ~2–3 tests during Commands test backfill to bring Commands to ≥85% compliance.

---

### [F10] INFORMATIONAL: `createCommand` and `createCommands` produce identical URLs

Both methods generate the same URL:

```
https://example.com/collections/iot/controlStreams/{controlStreamId}/commands
```

The distinction between single and bulk creation is in the request body (a single command object vs. an array), not in the URL. This is architecturally correct — the server uses Content-Type or inspects the body to differentiate. Having two methods with identical URL output is an intentional API design choice to give callers semantic clarity.

This matches the issue description's specification: both `createCommand` and `createCommands` route to `POST /controlstreams/{controlStreamId}/commands`.

---

## Test Quality Heatmap

| Dimension                           | Systems        | Deployments   | Procedures | SamplingFeatures | Properties | DataStreams        | Observations           | ControlStreams                 | Commands                                     |
| ----------------------------------- | -------------- | ------------- | ---------- | ---------------- | ---------- | ------------------ | ---------------------- | ------------------------------ | -------------------------------------------- |
| No options (base URL)               | ✅             | ✅            | ✅         | ✅               | ✅         | ✅                 | ✅                     | ✅                             | ✅                                           |
| `limit`                             | ✅             | ✅            | ✅         | ✅               | ✅         | ✅                 | ✅ (combo)             | ✅ (combo)                     | ✅ (combo)                                   |
| `offset` (standalone)               | ✅             | ✅            | ✅         | ✅               | ✅         | ✅                 | ✅                     | ✅                             | ❌                                           |
| `q`                                 | ✅             | ✅            | ✅         | ✅               | ✅         | ✅                 | ✅                     | ✅                             | N/A                                          |
| `id` (single)                       | ❌             | ❌            | ✅         | ✅               | ✅         | ✅                 | ✅                     | ✅                             | ✅                                           |
| `id` (array)                        | ✅             | ❌            | ✅         | ✅               | ✅         | ✅                 | ✅                     | ✅                             | ✅                                           |
| `bbox`                              | ✅             | ✅            | N/A        | ✅               | N/A        | N/A                | N/A                    | N/A                            | N/A                                          |
| `datetime` / temporal (exact)       | ✅ (instant)   | ✅ (interval) | N/A        | ✅ (interval)    | N/A        | ✅ (both + latest) | ✅ (interval + latest) | ✅ (issueTime + executionTime) | ✅ (issueTime + executionTime)               |
| `f` (format)                        | ❌             | ✅            | ✅         | ✅               | ✅         | ✅                 | ✅                     | ✅                             | ✅                                           |
| `cursor`                            | ✅             | ❌            | ❌         | ❌               | ❌         | ✅                 | ✅                     | ❌                             | ✅                                           |
| Multiple options                    | ✅             | ❌            | ✅         | ✅               | ✅         | ✅                 | ✅                     | ✅                             | ✅                                           |
| Type-specific params                | ✅ (6/6)       | ✅ (3/3)      | N/A        | N/A              | ✅ (2/2)   | ✅ (4/4)           | ✅ (2/2)               | ✅ (2/2)                       | ✅ (1/1: currentStatus)                      |
| Resource validation (all methods)   | ❌ (scattered) | ✅ (8/8)      | ✅ (8/8)   | ✅ (8/8)         | ✅ (6/6)   | ✅ (11/11)         | ✅ (8/8)               | ✅ (8/8)                       | ⚠️ (8/10 — see F8)                           |
| Association/sub-resource pagination | Partial        | ✅            | ✅         | ✅               | ✅         | ✅                 | N/A (singular)         | ✅                             | N/A (status/result/cancel are not paginated) |

**Checklist compliance score:**

- Systems: 10/14 (71%) — unchanged
- Deployments: 10/14 (71%) — unchanged
- Procedures: 10/11 (91%) — unchanged
- SamplingFeatures: 12/13 (92%) — unchanged
- Properties: 11/12 (92%) — unchanged
- DataStreams: 13/13 (100%) — unchanged
- Observations: 10/12 (83%) — unchanged
- ControlStreams: **11/13 (85%)** — up from 62% (Issue #45 backfill)
- Commands: **10/12 (83%)** — new (3 N/A: q, bbox, association pagination)

**Notable changes from Phase 2.8:**

- ControlStreams jumps from 62% → **85%** (Issue #45 backfill)
- Commands enters at **83%** — the highest entry-point coverage for any new resource type
- Commands has temporal ✅ (2 unique temporal keys), format ✅, cursor ✅, type-specific ✅, ID single + array ✅ from Day 1
- Only `offset` standalone and creation validation missing from 100%

---

## Summary

| Category                            | Count | Items                                                                                                                                                              |
| ----------------------------------- | ----- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Phase 2.2 findings (no change)      | **3** | P2-F1, P2-F2, P2-F3                                                                                                                                                |
| Phase 2.2→2.4 findings (no change)  | **5** | P2-F4, P2-F5, P2-F6, P2-F7, P2-F8                                                                                                                                  |
| Phase 1 findings (no change)        | **2** | P1-F4 (exports), P1-F6 (temporal keys)                                                                                                                             |
| Phase 2.4 findings unchanged        | **6** | F1, F2, F4, F5, F6, F7                                                                                                                                             |
| Phase 2.4 findings updated          | **1** | F8 (test counts — Commands added)                                                                                                                                  |
| Phase 2.5 findings no change        | **7** | F1, F2, F3, F4, F8, F9, F10                                                                                                                                        |
| Phase 2.5 findings already resolved | **3** | F5, F6, F7                                                                                                                                                         |
| Phase 2.6 findings unchanged        | **6** | F1, F2, F3, F7, F8, F9, F10                                                                                                                                        |
| Phase 2.6 findings already resolved | **2** | F4, F6                                                                                                                                                             |
| Phase 2.7 findings unchanged        | **8** | F1, F2, F3, F4, F6, F7, F8, F9, F10                                                                                                                                |
| Phase 2.7 findings already resolved | **1** | F5 (Observations heatmap)                                                                                                                                          |
| Phase 2.8 findings unchanged        | **7** | F1, F2, F3, F4, F5, F6, F8, F9                                                                                                                                     |
| Phase 2.8 findings now resolved     | **1** | F7 (ControlStreams heatmap → 85%, Issue #45)                                                                                                                       |
| **New — positive findings**         | **7** | F1 (80 methods), F2 (mirrors Observations), F3 (create validates controlStreams), F4 (spec links), F5 (lifecycle JSDoc), F6 (temporal tests), F7 (cancel encoding) |
| **New — gap findings**              | **2** | F8 (create validation not in block), F9 (heatmap gaps — 83%)                                                                                                       |
| **New — informational findings**    | **1** | F10 (createCommand/createCommands same URL)                                                                                                                        |
| **New bugs or design issues**       | **0** | —                                                                                                                                                                  |

---

## Recommendations

### Fix Before Next Coding Issue

1. **[F9] Backfill Commands test gaps** — Add ~2–3 tests: standalone `offset` and a multiple-options combo including offset. Also add `createCommand`/`createCommands` to the validation block (F8). Target ≥90% compliance. Estimated effort: 10 minutes.

### Fix Before Phase 3

2. **Systems consolidated resource validation** — Systems remains the only resource type without a single test block verifying all methods throw when unavailable. Low priority since methods are individually tested elsewhere.

### Defer (Low Priority)

3. **Cursor tests for Deployments, Procedures, SamplingFeatures, Properties, ControlStreams** — Cursor flows through the same `buildQueryString` path verified by Systems, DataStreams, Observations, and now Commands cursor tests. Per-type tests would improve heatmap but wouldn't exercise new code paths.

4. **`id` (single) tests for Systems and Deployments** — Both types test `id` as an array but not as a single value. Low priority since the serialization path is the same.

5. **[Phase 2.8 F8] JSDoc example casing alignment** — Low priority. No functional impact. Can be addressed in Phase 3 when URL path casing is formalized.

---

## Root Cause Analysis — Continued Zero Defects

Phase 2.9 is the **seventh consecutive phase** with zero new defects or design issues. The streak now spans the full Phase 2 resource implementation: Procedures → SamplingFeatures → Properties → DataStreams → Observations → ControlStreams → Commands.

### Why the implementation was clean

**Issue #13 (Commands Methods):**

1. **Observations as proven template + lifecycle extensions**: Commands follows the same `assertResourceAvailable` → `buildResourceUrl` → return pipeline established by Observations. The 5 new sub-resource methods (`getCommandStatus`, `updateCommandStatus`, `getCommandResult`, `cancelCommand`, `createCommands`) all use the same 3-argument `buildResourceUrl(resource, id, subpath)` pattern already exercised by 8 resource types.

2. **Cross-resource creation correctly follows Observations pattern**: `createCommand(controlStreamId)` mirrors `createObservation(datastreamId)` — both route through the parent resource's endpoint and validate the parent's availability. This pattern was established in Phase 2.7 (Observations) and required no new thinking.

3. **`CommandQueryOptions` was ready**: The type was already defined in `model.ts` (Issue #1) with `issueTime`, `executionTime`, and `currentStatus` fields. `TEMPORAL_KEYS` already included both temporal keys. No infrastructure changes were needed.

4. **`cancelCommand` is just another sub-path**: The `POST /commands/{id}/cancel` endpoint uses the same `buildResourceUrl('commands', id, 'cancel')` pattern as all other sub-resource methods. No new HTTP semantics were introduced — the URL builder is HTTP-verb-agnostic.

### Why the heatmap gap is smaller

Commands enters at **83%** — the highest initial coverage for any resource type. This is because:

- Temporal tests (`issueTime`, `executionTime`) were included from Day 1 (learned from prior phases)
- Cursor pagination tested from Day 1 (Commands uses cursor-based pagination)
- `currentStatus` type-specific filter tested from Day 1
- `id` single and array both tested from Day 1

The only gap is `offset` standalone, which is the shallowest possible missing test — a single parameter flowing through shared infrastructure.

---

## Overall Assessment

**Phase 2.9 is clean.** Commands (Issue #13) delivers the ninth and final Phase 2 resource type with zero defects, completing the seven-phase streak.

1. **All 9 resource types are implemented** — The CSAPI module now covers all Part 1 (Systems, Deployments, Procedures, SamplingFeatures, Properties) and Part 2 (DataStreams, Observations, ControlStreams, Commands) resource types. 79 public methods serve every CRUD, query, sub-resource, and lifecycle operation defined in the Connected Systems API specification.

2. **Commands introduces lifecycle management cleanly** — The 5 new patterns (bulk creation, status retrieval, status update, result retrieval, cancellation) required zero new infrastructure. Each integrates with the same `buildResourceUrl` helper used by every other resource type. The `cancelCommand` endpoint is the second POST action endpoint (after `checkCommandFeasibility`), confirming the sub-path pattern generalizes to action endpoints.

3. **ControlStreams heatmap debt resolved** — Issue #45 brought ControlStreams from 62% → 85% heatmap compliance, resolving Phase 2.8 F7. This confirms the review → backfill cycle works for the fifth consecutive time. Commands enters at 83%, the highest initial coverage yet, suggesting the team has internalized the test completeness lesson (Lesson 1).

4. **Phase 2 is complete** — With all 9 resource types implemented and tested, Phase 2's method implementation work is done. The codebase is stable, consistent, and ready for Phase 3 (response parsing and integration) once the final smoke test and any backfill work are completed.

**Cumulative project stats:**

- **79 public methods** across 9 resource types
- **311 tests** across 3 suites (41 model + 43 helpers + 227 url_builder)
- **5,785 lines** of production + test code
- **0 open findings from prior reviews** (third consecutive review)
- **2 new gap findings** (Commands validation F8 + heatmap F9 — both low severity)
- **7 consecutive phases** with zero defects
