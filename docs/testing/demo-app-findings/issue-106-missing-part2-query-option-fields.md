# Issue #106 — Findings Report: Missing Part 2 Query Option Fields

**Issue**: [#106 — Missing Part 2 query option fields: foi, controlStream, sender, issueTime on ControlStreams, CommandStatusQueryOptions](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/106)

**Date**: 2026-02-21
**Status**: Assessed — Recommendation: **PARTIAL FIX (spec-normative additions only)**
**Risk Level**: Low (purely additive interface changes; one backward-compatible method signature change)

---

## AI Operational Constraints Acknowledgment

This report was prepared in accordance with the project's
[AI Operational Constraints](../../governance/AI_OPERATIONAL_CONSTRAINTS.md), which establish:

- **Authority Precedence**: OGC standards → project governance → AI operational constraints.
- **Standards Discipline**: All implementations must be directly traceable to normative OGC specifications.
- **Mandatory Stop Conditions**: Implementation must not proceed if spec authority is unclear, risk of data loss exists, or changes could silently alter library behavior.
- **Scope Boundaries (§2.1)**: Do not infer unstated requirements. Do not expand scope beyond the issue description.
- **Refactoring Prohibitions (§2.3)**: No changes that increase diff noise. Minimal diffs only.

This report explicitly separates spec-normative gaps from non-spec proposals to avoid scope creep.

---

## Executive Summary

Issue #106 identifies missing optional filter fields across several Part 2 `QueryOptions` interfaces in `model.ts`. The issue was discovered during [ogc-csapi-explorer#35](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/35) when a demo app built on top of our CSAPI client library needed query filters not surfaced by the library's TypeScript interfaces.

After verifying each claimed gap against the normative OGC 23-002 specification (Clause 13 — Advanced Filtering), this analysis finds:

| Category | Count | Details |
|---|---|---|
| **Confirmed spec-normative gaps** | 7 fields + 1 interface | Missing from our interfaces but normatively required by OGC 23-002 §13 |
| **Not spec-normative (do NOT implement)** | 3 fields | Proposed in the issue but not defined as query parameters in OGC 23-002 §13 |
| **Incorrect spec citations in issue** | 5 | Issue references §2.x and §8.x; actual normative clauses are in §13.x |

**Recommendation**: Add the 7 confirmed spec-normative fields to existing interfaces and create the `CommandStatusQueryOptions` interface. Do **NOT** add `dataStream`, `controlStream`, or `reportTime` — these are not defined as query parameters in the spec. The risk is **low**: all changes are additive optional fields on TypeScript interfaces, with one backward-compatible method signature change on `getCommandStatus()`.

---

## Issue Description

### What Was Reported

Issue #106 identifies five gap categories in Part 2 `QueryOptions` interfaces:

1. `ControlStreamQueryOptions` — missing `issueTime` and `executionTime` temporal filters
2. All Part 2 interfaces — missing `foi` (feature-of-interest) filter
3. `ObservationQueryOptions` — missing `dataStream` filter
4. `CommandQueryOptions` — missing `controlStream` and `sender` filters
5. No `CommandStatusQueryOptions` interface or list method (missing `reportTime`, `statusCode` filters)

### Discovery Context

Discovered during [ogc-csapi-explorer#35](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/35) — implementing query filter panels in the explorer demo app. The demo app needed to filter Part 2 resources by feature-of-interest, temporal ranges, and command sender. The TypeScript interfaces did not expose these fields, so the demo app could not use type-safe filtering for these parameters.

### Important Context: These Are TypeScript-Only Gaps

Unlike Issue #105 (query parameter name mismatches, which caused silent runtime failures), this issue describes **TypeScript typing gaps** — missing optional fields on interfaces. The `buildQueryString()` method already serializes arbitrary key-value pairs from the options object. A savvy caller could work around these gaps by passing options via type assertion. No runtime behavior is broken; the gap is purely in type safety and discoverability.

---

## Spec Verification

Each gap was verified against OGC 23-002 Clause 13 (Advanced Filtering), which is the normative clause defining query parameters for Part 2 resource endpoints.

### Citation Corrections

The issue contains several incorrect spec section references. This table maps each to the actual normative clause:

| Issue Citation | Actual Normative Clause | Notes |
|---|---|---|
| "OGC 23-002 §8.3–8.4 (Req 52-55)" | §13.4.1–13.4.2 (Req 52-53) | §8 is "Common"; §13.4 is "ControlStream Query Parameters". Req 54 is `controlledProperty`, Req 55 is `foi` — not temporal filters. |
| "OGC 23-002 §2.1–2.4" | §13.2.4, §13.3.3, §13.4.4, §13.5.5 | §2 is "Conformance"; §13.x.y are the individual `foi` filter requirements |
| "OGC 23-002 §2.2" | Not in §13.3 | No `dataStream` query parameter is defined anywhere in §13 |
| "OGC 23-002 §2.4" (controlStream) | Not in §13.5 | No `controlStream` query parameter is defined anywhere in §13 |
| "OGC 23-002 §2.4" (sender) | §13.5.4 (Req 59) | `sender` is normatively required |

These inaccuracies are significant because they suggest the issue was written without precise spec cross-referencing. This report corrects each citation before making recommendations.

---

## Gap-by-Gap Analysis

### Gap 1: ControlStreamQueryOptions — missing `issueTime`, `executionTime`

**Status**: ✅ CONFIRMED — Spec-normative

**Current interface** (model.ts):
```typescript
export interface ControlStreamQueryOptions extends QueryOptions {
  systemId?: string;
  controlledPropertyId?: string;
  // issueTime and executionTime are MISSING
}
```

**Spec evidence**:
- OGC 23-002 §13.4.1 — Req 52 (`/req/advanced-filtering/controlstream-by-issuetime`): *"The HTTP GET operation at a ControlStream resources endpoint SHALL support a parameter `issueTime`."*
- OGC 23-002 §13.4.2 — Req 53 (`/req/advanced-filtering/controlstream-by-exectime`): *"The HTTP GET operation at a ControlStream resources endpoint SHALL support a parameter `executionTime`."*

**Wire-name compatibility**: Both `issueTime` and `executionTime` are already in `TEMPORAL_KEYS` (added for `CommandQueryOptions`). They will be correctly handled by `buildQueryString()` (ISO 8601 formatting) and their TypeScript names match the spec wire names — no `PARAM_NAME_MAP` entry needed.

**Risk**: None. Adding optional fields to an existing interface is non-breaking.

---

### Gap 2: All Part 2 interfaces — missing `foi` filter

**Status**: ✅ CONFIRMED — Spec-normative (4 interfaces)

**Affected interfaces and spec references**:

| Interface | Spec Clause | Requirement |
|---|---|---|
| `DatastreamQueryOptions` | §13.2.4 | Req 48: `/req/advanced-filtering/datastream-by-foi` |
| `ObservationQueryOptions` | §13.3.3 | Req 51: `/req/advanced-filtering/obs-by-foi` |
| `ControlStreamQueryOptions` | §13.4.4 | Req 55: `/req/advanced-filtering/controlstream-by-foi` |
| `CommandQueryOptions` | §13.5.5 | Req 60: `/req/advanced-filtering/cmd-by-foi` |

All four requirements use the same language: *"SHALL support a parameter `foi` of type `ID_List`"*.

**Wire-name compatibility**: The spec wire name is `foi`. The TypeScript property name `foi` matches directly — no `PARAM_NAME_MAP` entry needed. Note: `SystemQueryOptions` uses `foiId` (which maps to `foi` via `PARAM_NAME_MAP` from #105). The Part 2 interfaces should use `foi` directly since there's no legacy naming conflict — they are new additions. However, for consistency with the existing Part 1 convention of using `foiId`, a project decision should be made on whether to name the new field `foiId` (and rely on the existing PARAM_NAME_MAP entry) or `foi` (matching the spec directly). Both work at the wire level.

**Risk**: None. Adding optional fields to existing interfaces is non-breaking.

---

### Gap 3: ObservationQueryOptions — missing `dataStream` filter

**Status**: ❌ NOT SPEC-NORMATIVE — Do NOT implement

**Issue claim**: *"Missing: `dataStream` — Spec: OGC 23-002 §2.2"*

**Spec evidence**: OGC 23-002 §13.3 ("Observation Query Parameters") defines exactly three query parameters:
- §13.3.1 `phenomenonTime` (Req 49)
- §13.3.2 `resultTime` (Req 50)
- §13.3.3 `foi` (Req 51)

There is **no** `dataStream` query parameter defined in §13.3 or anywhere else in the Advanced Filtering requirements class.

The spec's intended approach for filtering observations by datastream is the **nested endpoint**: `GET /datastreams/{dsId}/observations` — which our library already supports via `getDataStreamObservations()`.

**Issue's own assessment**: The issue acknowledges this: *"Less critical since `getDataStreamObservations()` exists as a workaround."*

**Recommendation**: Do NOT add. This would be scope expansion (AI_OPERATIONAL_CONSTRAINTS §2.1) and introduce a non-spec parameter.

---

### Gap 4a: CommandQueryOptions — missing `sender` filter

**Status**: ✅ CONFIRMED — Spec-normative

**Spec evidence**: OGC 23-002 §13.5.4 — Req 59 (`/req/advanced-filtering/cmd-by-sender`): *"The HTTP GET operation at a Command resources endpoint SHALL support a parameter `sender`"*

**Wire-name compatibility**: TypeScript name `sender` matches the spec wire name. No `PARAM_NAME_MAP` entry needed.

**Risk**: None. Adding an optional field is non-breaking.

---

### Gap 4b: CommandQueryOptions — missing `controlStream` filter

**Status**: ❌ NOT SPEC-NORMATIVE — Do NOT implement

**Issue claim**: *"Missing: `controlStream` — Spec: OGC 23-002 §2.4"*

**Spec evidence**: OGC 23-002 §13.5 ("Command Query Parameters") defines exactly five query parameters:
- §13.5.1 `issueTime` (Req 56)
- §13.5.2 `executionTime` (Req 57)
- §13.5.3 `statusCode` (Req 58)
- §13.5.4 `sender` (Req 59)
- §13.5.5 `foi` (Req 60)

There is **no** `controlStream` query parameter defined in §13.5 or anywhere else in the Advanced Filtering requirements class.

The spec's intended approach for filtering commands by control stream is the **nested endpoint**: `GET /controlstreams/{csId}/commands` — which our library already supports via `getControlStreamCommands()`.

**Recommendation**: Do NOT add. Not spec-normative.

---

### Gap 5: CommandStatusQueryOptions — missing interface and method

**Status**: ✅ PARTIALLY CONFIRMED

**Current code** (url_builder.ts line 2336):
```typescript
getCommandStatus(id: string): string {
  this.assertResourceAvailable('commands');
  return this.buildResourceUrl('commands', id, 'status');
}
```

The method takes no options parameter, so callers cannot pass any query filters.

**Spec evidence for `statusCode`**: OGC 23-002 §13.6.1 — Req 61 (`/req/advanced-filtering/status-by-statuscode`): *"The HTTP GET operation at a Command Status resources endpoint SHALL support a parameter `statusCode`"*

**Spec evidence for `reportTime`**: OGC 23-002 §13.6 defines only ONE subsection (§13.6.1 — `statusCode`). There is **no** explicit `reportTime` query parameter defined. The base endpoint requirement (Req 31) states: *"The operation SHALL support the parameters `limit` and `datetime`"* — and `datetime` would evaluate against the `reportTime` property of CommandStatus resources. But `datetime` is already in the base `QueryOptions` interface. A dedicated `reportTime` field is **not** required.

**What is confirmed**:
- `statusCode` filter — normatively required (Req 61)
- `limit`, `datetime`, `offset`, `cursor` — already available via base `QueryOptions`

**What is NOT confirmed**:
- `reportTime` as a named query parameter — not in the spec. The `datetime` base parameter serves this purpose.

**Required changes**:
1. Create a `CommandStatusQueryOptions` interface extending `QueryOptions` with `statusCode?: CommandStatusCode`
2. Update `getCommandStatus(id: string)` to `getCommandStatus(id: string, options?: CommandStatusQueryOptions)` and append the query string

**Risk**: Low. The added parameter is optional, so the method signature change is backward-compatible.

---

## Complete Verification Table

| Interface | Field | OGC 23-002 Clause | Requirement | Wire Name | Spec-Normative? | Recommendation |
|---|---|---|---|---|---|---|
| `ControlStreamQueryOptions` | `issueTime` | §13.4.1 | Req 52 | `issueTime` | ✅ YES | ADD |
| `ControlStreamQueryOptions` | `executionTime` | §13.4.2 | Req 53 | `executionTime` | ✅ YES | ADD |
| `ControlStreamQueryOptions` | `foi` | §13.4.4 | Req 55 | `foi` | ✅ YES | ADD |
| `DatastreamQueryOptions` | `foi` | §13.2.4 | Req 48 | `foi` | ✅ YES | ADD |
| `ObservationQueryOptions` | `foi` | §13.3.3 | Req 51 | `foi` | ✅ YES | ADD |
| `CommandQueryOptions` | `sender` | §13.5.4 | Req 59 | `sender` | ✅ YES | ADD |
| `CommandQueryOptions` | `foi` | §13.5.5 | Req 60 | `foi` | ✅ YES | ADD |
| `CommandStatusQueryOptions` *(new)* | `statusCode` | §13.6.1 | Req 61 | `statusCode` | ✅ YES | ADD |
| `ObservationQueryOptions` | `dataStream` | — | — | — | ❌ NO | DO NOT ADD |
| `CommandQueryOptions` | `controlStream` | — | — | — | ❌ NO | DO NOT ADD |
| `CommandStatusQueryOptions` | `reportTime` | — | — | — | ❌ NO | DO NOT ADD |

---

## Risk Assessment

### Why This Is Low Risk

1. **Interface additions are non-breaking**: Adding optional fields to TypeScript interfaces cannot break any existing caller. No runtime behavior changes for code that doesn't use the new fields.

2. **No new serialization code needed**: `buildQueryString()` already handles arbitrary key-value pairs. The new fields will be serialized automatically.

3. **Wire-name compatibility is already solved**: All 7 confirmed new fields use spec-matching TypeScript names (`foi`, `issueTime`, `executionTime`, `sender`, `statusCode`). None require `PARAM_NAME_MAP` entries. Temporal fields (`issueTime`, `executionTime`) are already in `TEMPORAL_KEYS`.

4. **One method signature change is backward-compatible**: Adding an optional `options?` parameter to `getCommandStatus()` does not break callers who pass only `id`.

5. **No parser, fixture, or model changes**: This issue touches only `model.ts` (interfaces) and `url_builder.ts` (one method signature). No parsers, fixtures, or resource model properties are affected.

### Risks to Monitor

1. **Naming convention for `foi`**: `SystemQueryOptions` (Part 1) uses `foiId` which maps to `foi` via `PARAM_NAME_MAP`. The new Part 2 fields could use either `foiId` (consistent with Part 1 convention) or `foi` (matching spec directly). Both serialize correctly, but the choice should be deliberate and consistent. If `foiId` is chosen, no new `PARAM_NAME_MAP` entry is needed (it's already there). If `foi` is chosen, the naming inconsistency with Part 1's `foiId` should be documented.

2. **Test coverage**: New fields need unit tests in `url_builder.spec.ts` to verify they serialize correctly. These are straightforward additions following the existing test patterns.

---

## Recommendation

### Recommended Actions

**Fix the 7 confirmed spec-normative gaps + 1 new interface:**

| # | Change | File | Risk |
|---|---|---|---|
| 1 | Add `issueTime?: DateTimeParameter` to `ControlStreamQueryOptions` | model.ts | None |
| 2 | Add `executionTime?: DateTimeParameter` to `ControlStreamQueryOptions` | model.ts | None |
| 3 | Add `foi?: string` to `ControlStreamQueryOptions` | model.ts | None |
| 4 | Add `foi?: string` to `DatastreamQueryOptions` | model.ts | None |
| 5 | Add `foi?: string` to `ObservationQueryOptions` | model.ts | None |
| 6 | Add `sender?: string` to `CommandQueryOptions` | model.ts | None |
| 7 | Add `foi?: string` to `CommandQueryOptions` | model.ts | None |
| 8 | Create `CommandStatusQueryOptions` with `statusCode?: CommandStatusCode` | model.ts | None |
| 9 | Update `getCommandStatus()` to accept optional `CommandStatusQueryOptions` | url_builder.ts | Low |

### DO NOT Implement

| # | Field | Reason |
|---|---|---|
| 1 | `dataStream` on `ObservationQueryOptions` | Not a spec-defined query parameter. Nested endpoint `getDataStreamObservations()` is the spec-intended approach. |
| 2 | `controlStream` on `CommandQueryOptions` | Not a spec-defined query parameter. Nested endpoint `getControlStreamCommands()` is the spec-intended approach. |
| 3 | `reportTime` on `CommandStatusQueryOptions` | Not a named query parameter in §13.6. The base `datetime` parameter (already in `QueryOptions`) serves this purpose. |

### Open Decision: `foi` vs `foiId` Naming

Before implementation, a project-level decision is needed:

- **Option A: Use `foi`** — Matches OGC spec wire name directly. No `PARAM_NAME_MAP` entry needed. Creates a naming inconsistency with Part 1's `foiId`.
- **Option B: Use `foiId`** — Consistent with Part 1 convention (`SystemQueryOptions.foiId`). Already has a `PARAM_NAME_MAP` entry mapping to `foi`. Maintains internal naming consistency.

Both options produce the same wire output (`?foi=...`). The choice is purely about TypeScript API design consistency.

---

## Files Affected

| File | Action | Est. Lines | Purpose |
|---|---|---|---|
| `src/ogc-api/csapi/model.ts` | Modify | ~15 | Add optional fields to 4 interfaces + create 1 new interface |
| `src/ogc-api/csapi/url_builder.ts` | Modify | ~5 | Update `getCommandStatus()` signature and body |
| `src/ogc-api/csapi/url_builder.spec.ts` | Modify | ~40 | Add tests for new query option fields |

---

## Interaction With Other Issues

- **#105 (Query Parameter Name Mismatches)**: Resolved. The `PARAM_NAME_MAP` and `TEMPORAL_KEYS` are already configured correctly for all 7 new fields. No new map entries are needed (all new TypeScript names match their spec wire names, or are already mapped).
- **#107 (Nested Builder Method Types)**: Independent. That issue concerns method parameter types on nested builder methods, not the QueryOptions interfaces themselves.

---

## Assessment: Scope, Risk, and Implementation Decision

**Is this a bug?** No. The library works correctly at runtime today. `buildQueryString()` already serializes any property passed to it. A savvy caller can use type assertions to pass any query parameter — nothing is broken at the wire level.

**What this is:** Incomplete TypeScript type coverage for spec-normative query parameters. The library's purpose is to provide a **typed TypeScript client** for the CSAPI spec. Missing optional fields on QueryOptions interfaces means callers don't get autocompletion, type checking, or discoverability for 7 spec-normative parameters.

**Is it within scope?** Yes. The library's explicit goal is spec-complete typed coverage of OGC API — Connected Systems. These are additive optional fields directly traceable to normative requirements (Req 48, 51–53, 55, 59–61) in OGC 23-002 §13.

**Priority and risk:**
- **Low priority** — no runtime behavior is broken; this is a developer-experience improvement.
- **Low risk** — all changes are additive optional fields on TypeScript interfaces. One backward-compatible method signature change (`getCommandStatus()`). No parser, fixture, serialization, or model changes.
- **Safe to defer** — nothing breaks if this waits. Nothing regresses.

**Scope creep risk:** The 3 items flagged as "do NOT implement" (`dataStream`, `controlStream`, `reportTime`) are where real risk of scope creep exists. They are not defined in OGC 23-002 §13 and must not be added.

**Naming decision:** Use `foiId` (Option B) for the new `foi` fields on all 4 Part 2 interfaces. This maintains consistency with Part 1's `SystemQueryOptions.foiId` convention and reuses the existing `PARAM_NAME_MAP` entry (`foiId → foi`). The entire library already follows this internal naming convention; introducing `foi` alongside `foiId` would create an inconsistency.

---

## References

| # | Document | What It Provides |
|---|---|---|
| 1 | [OGC 23-002 §13 — Advanced Filtering](https://docs.ogc.org/is/23-002/23-002.html#clause-advanced-filtering) | Normative query parameter definitions for all Part 2 resources |
| 2 | [OGC 23-002 §13.2 — DataStream Query Parameters](https://docs.ogc.org/is/23-002/23-002.html#clause-datastream-query-params) | `phenomenonTime`, `resultTime`, `observedProperty`, `foi` |
| 3 | [OGC 23-002 §13.3 — Observation Query Parameters](https://docs.ogc.org/is/23-002/23-002.html#clause-observation-query-params) | `phenomenonTime`, `resultTime`, `foi` (NO `dataStream`) |
| 4 | [OGC 23-002 §13.4 — ControlStream Query Parameters](https://docs.ogc.org/is/23-002/23-002.html#clause-controlstream-query-params) | `issueTime`, `executionTime`, `controlledProperty`, `foi` |
| 5 | [OGC 23-002 §13.5 — Command Query Parameters](https://docs.ogc.org/is/23-002/23-002.html#clause-command-query-params) | `issueTime`, `executionTime`, `statusCode`, `sender`, `foi` (NO `controlStream`) |
| 6 | [OGC 23-002 §13.6 — CommandStatus Query Parameters](https://docs.ogc.org/is/23-002/23-002.html#_CommandStatus_Query_Params) | `statusCode` only (NO `reportTime`) |
| 7 | [`docs/governance/AI_OPERATIONAL_CONSTRAINTS.md`](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/governance/AI_OPERATIONAL_CONSTRAINTS.md) | Mandatory operational constraints — especially §2.1 (no scope expansion), §2.3 (no refactoring) |
| 8 | [ogc-csapi-explorer#35](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/35) | Demo app issue where missing filter fields were discovered |
| 9 | [Issue #105 — Query parameter name mismatches](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/105) | Resolved. `PARAM_NAME_MAP` and `TEMPORAL_KEYS` already support the new fields |
| 10 | [Issue #105 Findings Report](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/testing/demo-app-findings/issue-105-query-parameter-name-mismatches.md) | Related findings report for query parameter serialization |
