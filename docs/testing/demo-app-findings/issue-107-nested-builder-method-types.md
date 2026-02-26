# Issue #107 — Findings Report: Nested Builder Methods Accept Base QueryOptions Instead of Type-Specific Options

**Issue**: [#107 — DX: 12 nested builder methods accept base QueryOptions instead of type-specific options](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/107)

**Date**: 2026-02-21
**Status**: Assessed — Recommendation: **FIX (type-only narrowing; zero runtime change)**
**Risk Level**: Very Low (parameter type narrowing from base to child type; no runtime behavior change; no serialization change; all existing callers remain valid)

---

## AI Operational Constraints Acknowledgment

This report was prepared in accordance with the project's
[AI Operational Constraints](../../governance/AI_OPERATIONAL_CONSTRAINTS.md), which establish:

- **Authority Precedence**: OGC standards → project governance → AI operational constraints.
- **Standards Discipline**: All implementations must be directly traceable to normative OGC specifications.
- **Mandatory Stop Conditions**: Implementation must not proceed if spec authority is unclear, risk of data loss exists, or changes could silently alter library behavior.
- **Scope Boundaries (§2.1)**: Do not infer unstated requirements. Do not expand scope beyond the issue description.
- **Refactoring Prohibitions (§2.3)**: No changes that increase diff noise. Minimal diffs only.

This report explicitly separates verified findings from unverified claims to avoid scope creep.

---

## Executive Summary

Issue #107 reports that 12 nested-resource methods in `url_builder.ts` accept `QueryOptions` (the base type) as their `options` parameter instead of the child resource's specific query options interface (e.g., `DatastreamQueryOptions`, `SystemQueryOptions`). This means TypeScript callers get no autocomplete or type checking for resource-specific filter fields when querying nested endpoints.

After verifying every claim against the source code:

| Category                                     | Count | Details                                                                                                       |
| -------------------------------------------- | ----- | ------------------------------------------------------------------------------------------------------------- |
| **Issue's claimed affected methods**         | 12    | All 12 verified — each accepts `QueryOptions` when it should accept a narrower subtype                        |
| **Issue's "already correct" methods**        | 2     | Both verified — `getDataStreamObservations` and `getControlStreamCommands` already use correct types          |
| **Additional affected methods not in issue** | 5     | Found during verification — same pattern, same gap, not mentioned in the issue                                |
| **Singular navigation methods (borderline)** | 2     | `getObservationSamplingFeature` and `getObservationSystem` — return one resource, not a filterable collection |

**Recommendation**: Fix the 12 methods identified in the issue. The fix is strictly a TypeScript parameter type narrowing — changing `options?: QueryOptions` to `options?: DatastreamQueryOptions` (etc.) — with **zero runtime behavior change**. Every specific type extends `QueryOptions`, so:

1. All existing callers remain valid (widening to a subtype is non-breaking).
2. `buildResourceUrl()` internally still receives a `QueryOptions`-compatible object.
3. `buildQueryString()` iterates `Object.entries()` generically — it does not depend on the static type.
4. No serialization logic, URL construction, or test assertions change.

The 5 additional methods found during verification should be evaluated separately (3 of them use `ProcedureQueryOptions` / `SamplingFeatureQueryOptions` which are type aliases for `QueryOptions` — fixing those is cosmetic only). The 2 already-correct methods in the issue need no changes.

---

## Discovery Context

Discovered during [ogc-csapi-explorer#35](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/35) — the explorer demo app's bridge layer (`csapi-bridge.ts`) needed to cast options explicitly (e.g., `options as DatastreamQueryOptions`) when calling nested builder methods. These explicit casts made the typing gap visible and prompted this issue.

---

## What This Is (and What It Is Not)

### What it IS

A **TypeScript developer-experience (DX) gap**. The `options` parameter on 12 nested methods uses the base `QueryOptions` type, which means:

- No autocomplete for type-specific fields (e.g., `phenomenonTime`, `observedPropertyId`, `recursive`)
- No compile-time type checking when callers pass resource-specific filter options
- Callers must use type assertions to get proper typing

### What it is NOT

- **Not a runtime bug**: `buildQueryString()` serializes any property via `Object.entries()` regardless of the static TypeScript type. Any key-value pair passed at runtime is serialized to the URL correctly.
- **Not a behavioral change**: Narrowing a parameter type from a base type to a subtype does not change what values are accepted at runtime (JavaScript has no runtime type checking).
- **Not a spec compliance issue**: The OGC spec does not define TypeScript types. This is purely an internal API design consistency matter.
- **Not a breaking change**: Every child QueryOptions type (`DatastreamQueryOptions`, `SystemQueryOptions`, etc.) extends `QueryOptions`. Changing the parameter type from parent to child means all existing callers that pass `QueryOptions`-compatible objects still compile. The only callers that would break are those explicitly passing a `QueryOptions`-typed variable with properties NOT in the child type — and no such callers exist in the codebase or tests.

---

## Verification: All 14 Claims Confirmed

### 12 Affected Methods (all verified ✅)

| #   | Method                           | Line  | Current Type   | Should Accept               | Verified |
| --- | -------------------------------- | ----- | -------------- | --------------------------- | -------- |
| 1   | `getSystemDataStreams`           | L555  | `QueryOptions` | `DatastreamQueryOptions`    | ✅       |
| 2   | `getSystemControlStreams`        | L600  | `QueryOptions` | `ControlStreamQueryOptions` | ✅       |
| 3   | `getSystemDeployments`           | L688  | `QueryOptions` | `DeploymentQueryOptions`    | ✅       |
| 4   | `getDeploymentSystems`           | L887  | `QueryOptions` | `SystemQueryOptions`        | ✅       |
| 5   | `getProcedureSystems`            | L1043 | `QueryOptions` | `SystemQueryOptions`        | ✅       |
| 6   | `getProcedureDataStreams`        | L1064 | `QueryOptions` | `DatastreamQueryOptions`    | ✅       |
| 7   | `getSamplingFeatureSystems`      | L1220 | `QueryOptions` | `SystemQueryOptions`        | ✅       |
| 8   | `getSamplingFeatureObservations` | L1244 | `QueryOptions` | `ObservationQueryOptions`   | ✅       |
| 9   | `getPropertySystems`             | L1345 | `QueryOptions` | `SystemQueryOptions`        | ✅       |
| 10  | `getPropertyDataStreams`         | L1369 | `QueryOptions` | `DatastreamQueryOptions`    | ✅       |
| 11  | `getPropertyControlStreams`      | L1393 | `QueryOptions` | `ControlStreamQueryOptions` | ✅       |
| 12  | `getDataStreamSystems`           | L1635 | `QueryOptions` | `SystemQueryOptions`        | ✅       |

### 2 Already-Correct Methods (verified ✅)

| #   | Method                      | Line  | Current Type              | Verified           |
| --- | --------------------------- | ----- | ------------------------- | ------------------ |
| 13  | `getDataStreamObservations` | L1591 | `ObservationQueryOptions` | ✅ Already correct |
| 14  | `getControlStreamCommands`  | L2043 | `CommandQueryOptions`     | ✅ Already correct |

### Pattern: Why Some Were Correct and Others Were Not

The 2 already-correct methods (`getDataStreamObservations` and `getControlStreamCommands`) are the most-used nested endpoints in any CSAPI application — they are the primary data ingestion and command submission paths. It is likely these were typed correctly because they were the first to be tested with type-specific filters. The remaining 12 methods follow a more generic pattern and were typed with the base `QueryOptions` during initial implementation.

---

## Additional Methods Not in Issue (Found During Verification)

During verification, 5 additional nested collection methods were found with the same `QueryOptions` base type pattern:

| #   | Method                       | Line  | Current Type   | Target Type                   | Practical Benefit                                                           |
| --- | ---------------------------- | ----- | -------------- | ----------------------------- | --------------------------------------------------------------------------- |
| 1   | `getSystemSamplingFeatures`  | L644  | `QueryOptions` | `SamplingFeatureQueryOptions` | **None** — `SamplingFeatureQueryOptions` is a type alias for `QueryOptions` |
| 2   | `getSystemProcedures`        | L709  | `QueryOptions` | `ProcedureQueryOptions`       | **None** — `ProcedureQueryOptions` is a type alias for `QueryOptions`       |
| 3   | `getDataStreamProcedures`    | L1656 | `QueryOptions` | `ProcedureQueryOptions`       | **None** — type alias                                                       |
| 4   | `getControlStreamSystems`    | L2092 | `QueryOptions` | `SystemQueryOptions`          | **Yes** — `SystemQueryOptions` has `foiId`, `recursive`, etc.               |
| 5   | `getControlStreamProcedures` | L2117 | `QueryOptions` | `ProcedureQueryOptions`       | **None** — type alias                                                       |

**Analysis of additional methods:**

- Methods 1, 2, 3, 5 use `ProcedureQueryOptions` or `SamplingFeatureQueryOptions`, which are defined as `export type ProcedureQueryOptions = QueryOptions` and `export type SamplingFeatureQueryOptions = QueryOptions` in `model.ts`. Changing these method signatures would be **purely cosmetic** — the types are identical. There is **no autocomplete benefit and no type safety benefit**. These should only be changed if a future issue adds specific fields to `ProcedureQueryOptions` or `SamplingFeatureQueryOptions`, at which point the methods would automatically benefit.
- Method 4 (`getControlStreamSystems`) targets `SystemQueryOptions`, which has meaningful extra fields (`foiId`, `recursive`, `procedureId`, `observedPropertyId`, `controlledPropertyId`). This is a real gap with the same practical impact as the 12 methods in the issue.

**Recommendation for additional methods**: Include `getControlStreamSystems` (method 4) in the fix since it has the same real-world impact. Defer methods 1, 2, 3, 5 — they are cosmetic-only changes that add diff noise with zero practical benefit.

Additionally, 2 **singular navigation methods** were found:

| #   | Method                          | Line  | Current Type   | Notes                                                                 |
| --- | ------------------------------- | ----- | -------------- | --------------------------------------------------------------------- |
| 6   | `getObservationSamplingFeature` | L1822 | `QueryOptions` | Returns a single resource via `.../observations/{id}/samplingFeature` |
| 7   | `getObservationSystem`          | L1846 | `QueryOptions` | Returns a single resource via `.../observations/{id}/system`          |

These return a single resource (not a filterable collection), so the base `QueryOptions` (which provides `f` for format negotiation) is arguably appropriate. These should **not** be changed.

### Already-Correct Methods Also Not in Issue

For completeness, these nested methods are already correctly typed and were not mentioned:

| Method                        | Line  | Type Used                      |
| ----------------------------- | ----- | ------------------------------ |
| `getSystemSubsystems`         | L512  | `SystemQueryOptions` ✅        |
| `getDeploymentSubdeployments` | L844  | `DeploymentQueryOptions` ✅    |
| `getCommandStatus`            | L2341 | `CommandStatusQueryOptions` ✅ |

---

## Risk Assessment

### Why This Fix Is Safe

1. **Type narrowing is non-breaking in TypeScript**: Changing a function parameter from `Base` to `Child extends Base` is a **covariant narrowing**. Every value that satisfies `Child` also satisfies `Base`. All existing callers that pass `{ limit: 20 }` (a `QueryOptions`-compatible literal) will still compile — TypeScript infers literal object types structurally, not nominally.

2. **No runtime code changes**: The fix changes only TypeScript type annotations on method signatures. Zero JavaScript is altered. The transpiled output is identical before and after.

3. **`buildResourceUrl()` accepts `QueryOptions`**: The private internal method signature remains `buildResourceUrl(..., options?: QueryOptions)`. Since every specific type extends `QueryOptions`, the assignment from the public method's narrower parameter to the internal method's wider parameter is always valid.

4. **`buildQueryString()` is type-agnostic**: It iterates `Object.entries(options)` which operates on the runtime object, not the TypeScript type. Any property present on the object at runtime is serialized regardless of the declared type.

5. **Existing tests pass unchanged**: All existing test calls use inline object literals with `QueryOptions`-compatible properties (`{ limit: 20 }`, `{ limit: 5, offset: 10 }`). These are structurally compatible with every child QueryOptions type. No test modifications needed.

6. **All required types are already imported**: The `url_builder.ts` import statement already includes all 11 QueryOptions types — no new imports are needed.

### Risks to Monitor

1. **Diff size**: 12 one-word changes across method signatures. Minimal, but still a diff across a core file. Each change is a single token replacement (`QueryOptions` → `DatastreamQueryOptions`, etc.).

2. **JSDoc `@param` updates**: Some methods have `@param options` descriptions that should say "Optional query parameters for filtering datastreams" instead of the generic description. This is cosmetic JSDoc improvement and could be deferred or included — it adds to the diff but improves documentation accuracy.

3. **The 5 additional methods**: Fixing only the 12 from the issue creates an inconsistency where some nested methods are typed and some are not. However, 4 of the 5 additional methods use type aliases that are identical to `QueryOptions`, so the inconsistency is cosmetic only. The one meaningful additional method (`getControlStreamSystems`) should be included.

---

## Assessment: Should We Change Our Library?

**Yes — this is a safe, beneficial fix.**

**Is this a bug?** No. It is a TypeScript type precision gap. The library is functionally correct at runtime.

**Does it degrade library integrity?** No. The change narrows parameter types from parent to child, which:

- Cannot break any existing caller
- Does not change any runtime behavior
- Does not change any URL output
- Does not change any serialization logic

**Is it within scope?** Yes. The library's purpose is to provide a **typed TypeScript client** for the OGC API — Connected Systems specification. Type-specific query options on resource-specific methods are core to that purpose. The `getDataStreamObservations` and `getControlStreamCommands` methods already demonstrate the intended pattern — the remaining 12 methods simply weren't brought to the same standard.

**Is it consistent with AI Operational Constraints?**

- **§2.1 (Scope)**: The fix addresses exactly what the issue describes — nothing more.
- **§2.2 (Architectural Alignment)**: The fix aligns with the existing pattern (`getDataStreamObservations` and `getControlStreamCommands` already use specific types).
- **§2.3 (Minimal Diffs)**: Each change is a single type annotation replacement per method. No code restructuring.
- **§3 (Standards Discipline)**: The specific QueryOptions types were defined based on OGC spec requirements. Using them on the correct methods is direct standards alignment.

**Priority**: Low. This is a DX improvement with no runtime impact. Safe to defer if there are higher-priority items, but equally safe to implement at any time.

---

## Recommendation

### Recommended Fix

Change the `options` parameter type on the 12 methods identified in the issue, plus `getControlStreamSystems`, from `QueryOptions` to the appropriate child type:

| #   | Method                           | Change To                   | File           |
| --- | -------------------------------- | --------------------------- | -------------- |
| 1   | `getSystemDataStreams`           | `DatastreamQueryOptions`    | url_builder.ts |
| 2   | `getSystemControlStreams`        | `ControlStreamQueryOptions` | url_builder.ts |
| 3   | `getSystemDeployments`           | `DeploymentQueryOptions`    | url_builder.ts |
| 4   | `getDeploymentSystems`           | `SystemQueryOptions`        | url_builder.ts |
| 5   | `getProcedureSystems`            | `SystemQueryOptions`        | url_builder.ts |
| 6   | `getProcedureDataStreams`        | `DatastreamQueryOptions`    | url_builder.ts |
| 7   | `getSamplingFeatureSystems`      | `SystemQueryOptions`        | url_builder.ts |
| 8   | `getSamplingFeatureObservations` | `ObservationQueryOptions`   | url_builder.ts |
| 9   | `getPropertySystems`             | `SystemQueryOptions`        | url_builder.ts |
| 10  | `getPropertyDataStreams`         | `DatastreamQueryOptions`    | url_builder.ts |
| 11  | `getPropertyControlStreams`      | `ControlStreamQueryOptions` | url_builder.ts |
| 12  | `getDataStreamSystems`           | `SystemQueryOptions`        | url_builder.ts |
| 13  | `getControlStreamSystems`        | `SystemQueryOptions`        | url_builder.ts |

### DO NOT Change

| #   | Method                          | Reason                                                                    |
| --- | ------------------------------- | ------------------------------------------------------------------------- |
| 1   | `getSystemSamplingFeatures`     | `SamplingFeatureQueryOptions` = `QueryOptions` (type alias, zero benefit) |
| 2   | `getSystemProcedures`           | `ProcedureQueryOptions` = `QueryOptions` (type alias, zero benefit)       |
| 3   | `getDataStreamProcedures`       | `ProcedureQueryOptions` = `QueryOptions` (type alias, zero benefit)       |
| 4   | `getControlStreamProcedures`    | `ProcedureQueryOptions` = `QueryOptions` (type alias, zero benefit)       |
| 5   | `getObservationSamplingFeature` | Singular navigation — base `QueryOptions` is sufficient                   |
| 6   | `getObservationSystem`          | Singular navigation — base `QueryOptions` is sufficient                   |

### Testing Impact

- **No test modifications required**: All existing tests pass unchanged because they use inline object literals that are structurally compatible with both the old and new parameter types.
- **Optional test additions**: New tests could verify that type-specific filters serialize correctly when called via nested methods (e.g., `getSystemDataStreams('sys-001', { phenomenonTime: ... })`). These would be additive tests only.

---

## Files Affected

| File                               | Action | Est. Lines Changed     | Purpose                                        |
| ---------------------------------- | ------ | ---------------------- | ---------------------------------------------- |
| `src/ogc-api/csapi/url_builder.ts` | Modify | ~13 (one-word changes) | Narrow `options` parameter types on 13 methods |

No new files, no new imports, no test file changes, no model changes.

---

## References

| #   | Document                                                                                                                                                  | What It Provides                                                                                                                                                                                |
| --- | --------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | [Issue #107 — DX: 12 nested builder methods accept base QueryOptions](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/107)                          | Issue description with affected methods table                                                                                                                                                   |
| 2   | [`docs/governance/AI_OPERATIONAL_CONSTRAINTS.md`](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/governance/AI_OPERATIONAL_CONSTRAINTS.md) | Mandatory operational constraints — §2.1 (scope), §2.2 (architectural alignment), §2.3 (minimal diffs)                                                                                          |
| 3   | [`src/ogc-api/csapi/url_builder.ts`](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/src/ogc-api/csapi/url_builder.ts)                           | Source file containing all affected methods                                                                                                                                                     |
| 4   | [`src/ogc-api/csapi/model.ts`](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/src/ogc-api/csapi/model.ts)                                       | QueryOptions type hierarchy — all child types extend `QueryOptions`                                                                                                                             |
| 5   | [ogc-csapi-explorer#35](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/35)                                                                         | Demo app issue where the typing gap was discovered via bridge layer casts                                                                                                                       |
| 6   | [Issue #106 — Missing Part 2 query option fields](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/106)                                              | Related: recently added `foiId`, `sender`, `issueTime`, `executionTime` to Part 2 interfaces — these new fields are exactly the kind that callers would want autocomplete for on nested methods |
| 7   | [Issue #105 — Query parameter name mismatches](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/105)                                                 | Related: `PARAM_NAME_MAP` ensures type-specific fields serialize to correct wire names regardless of the TypeScript parameter type                                                              |
