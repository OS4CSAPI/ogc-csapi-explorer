# Issue #105 — Findings Report: Query Parameter Name Mismatches

**Issue**: [#105 — Bug: Query parameter names don't match OGC spec — `currentStatus` should be `statusCode`, `systemId` should be `system`, etc.](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/105)

**Date**: 2026-02-21
**Status**: Assessed — Recommendation: **FIX (scoped remapping only)**
**Risk Level**: Moderate (changes wire format sent to servers; requires careful scoping)

---

## AI Operational Constraints Acknowledgment

This report was prepared in accordance with the project's
[AI Operational Constraints](../../governance/AI_OPERATIONAL_CONSTRAINTS.md), which establish:

- **Authority Precedence**: OGC standards → project governance → AI operational constraints.
- **Standards Discipline**: All implementations must be directly traceable to normative OGC specifications.
- **Mandatory Stop Conditions**: Implementation must not proceed if spec authority is unclear, risk of data loss exists, or changes could silently alter library behavior.

The recommendation below is constrained by these rules. The proposed fix intentionally changes wire format (URL query parameter names) to match the OGC normative spec, which constitutes a deliberate behavioral correction — not a silent alteration.

---

## Executive Summary

`buildQueryString()` in `src/ogc-api/csapi/url_builder.ts` serializes TypeScript property names from `QueryOptions` interfaces directly as URL query parameter names. Several of these property names do not match the parameter names defined in the OGC Connected Systems API specifications (OGC 23-001 and OGC 23-002). This causes **silent filter failures** on spec-compliant servers — the server ignores the unrecognized parameter and returns unfiltered results with HTTP 200 (no error indication).

This report was triggered by [ogc-csapi-explorer#35](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/35), where the demo app's `currentStatus` filter on Commands was silently ignored by the server.

### Verification Summary

| Category                      | Count | Details                                           |
| ----------------------------- | ----- | ------------------------------------------------- |
| **Confirmed spec mismatches** | 6     | Wire name differs from OGC normative requirement  |
| **Non-spec extensions**       | 2     | Parameters not defined in OGC spec (OSH-specific) |
| **Correctly named**           | 12+   | Already match spec                                |

**Recommendation**: FIX — Add a `PARAM_NAME_MAP` remapping layer inside `buildQueryString()` to translate TypeScript property names to OGC-spec parameter names. Do **NOT** rename TypeScript interface properties (that would be a breaking API change). Model property names (e.g., `Command.currentStatus`, `DataStream.systemId`) remain unchanged — those are internal representations, not query parameters.

---

## Issue Description

### What Was Reported

Issue #105 identifies that `buildQueryString()` iterates `Object.entries(options)` and appends each key/value pair directly to the URL. There is no key-name remapping layer, so TypeScript property names are used verbatim as URL query parameter names.

The issue confirmed one mismatch (`currentStatus` → `statusCode`) and flagged four more for verification (`systemId` → `system`, `observedPropertyId` → `observedProperty`, `controlledPropertyId` → `controlledProperty`, `foiId` → `foi`).

### Discovery Context

Discovered during [ogc-csapi-explorer#35](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/35) — adding query filters to related-resource panels in the explorer demo app. The `currentStatus` filter was sent as `?currentStatus=PENDING` but the server (spec-compliant) expected `?statusCode=PENDING` and silently returned unfiltered results. The explorer app implemented a client-side fallback workaround.

---

## Source Code Review

### File: `src/ogc-api/csapi/url_builder.ts` — `buildQueryString()` (lines 280–316)

The method iterates all entries of the options object and appends them as-is:

```typescript
private buildQueryString(options?: QueryOptions): string {
  if (!options) return '';
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(options)) {
    // ... validation for bbox, temporal, limit, arrays ...
    params.append(key, String(value));  // ← key used verbatim
  }
  const queryString = params.toString();
  return queryString ? `?${queryString}` : '';
}
```

There is no remapping step between the TypeScript property name (`key`) and the OGC-spec wire name.

### File: `src/ogc-api/csapi/model.ts` — QueryOptions Interfaces

The interfaces define property names that sometimes match the spec and sometimes don't:

| Interface                   | Property               | Matches spec?                   |
| --------------------------- | ---------------------- | ------------------------------- |
| `SystemQueryOptions`        | `parent`               | ✅                              |
| `SystemQueryOptions`        | `procedureId`          | ❌ (spec: `procedure`)          |
| `SystemQueryOptions`        | `foiId`                | ❌ (spec: `foi`)                |
| `SystemQueryOptions`        | `observedPropertyId`   | ❌ (spec: `observedProperty`)   |
| `SystemQueryOptions`        | `controlledPropertyId` | ❌ (spec: `controlledProperty`) |
| `SystemQueryOptions`        | `recursive`            | ✅                              |
| `DeploymentQueryOptions`    | `parent`               | ✅                              |
| `DeploymentQueryOptions`    | `systemId`             | ❌ (spec: `system`)             |
| `DeploymentQueryOptions`    | `recursive`            | ✅                              |
| `PropertyQueryOptions`      | `system`               | ✅                              |
| `PropertyQueryOptions`      | `baseProperty`         | ✅                              |
| `DatastreamQueryOptions`    | `systemId`             | ⚠️ Not a spec parameter         |
| `DatastreamQueryOptions`    | `observedPropertyId`   | ❌ (spec: `observedProperty`)   |
| `DatastreamQueryOptions`    | `phenomenonTime`       | ✅                              |
| `DatastreamQueryOptions`    | `resultTime`           | ✅                              |
| `ControlStreamQueryOptions` | `systemId`             | ⚠️ Not a spec parameter         |
| `ControlStreamQueryOptions` | `controlledPropertyId` | ❌ (spec: `controlledProperty`) |
| `CommandQueryOptions`       | `issueTime`            | ✅                              |
| `CommandQueryOptions`       | `executionTime`        | ✅                              |
| `CommandQueryOptions`       | `currentStatus`        | ❌ (spec: `statusCode`)         |

Note that `PropertyQueryOptions` already uses the correct spec names (`system`, `baseProperty`), demonstrating that the inconsistency is accidental, not a deliberate design pattern.

---

## OGC Specification Verification

Each mismatch was verified against the normative requirement text in the OGC standards.

### Confirmed Mismatches

#### 1. `currentStatus` → `statusCode`

**Verdict: CONFIRMED MISMATCH**

- **Spec**: OGC 23-002 §13.5.3 `/req/advanced-filtering/cmd-by-status` — "The HTTP GET operation at a Command resources endpoint SHALL support a parameter **statusCode**"
- **OpenAPI fragment in spec**: `name: statusCode`
- **Wire example**: `{api_root}/commands?statusCode=PENDING`
- **Our wire output**: `?currentStatus=PENDING`
- **Note**: The Command _resource property_ is correctly named `currentStatus` (Table 11 in §10.7.1). The distinction is: the resource attribute is `currentStatus`, but the query filter parameter is `statusCode`. These are deliberately different names in the spec.

#### 2. `foiId` → `foi`

**Verdict: CONFIRMED MISMATCH**

- **Spec**: OGC 23-001 §16.5.4 `/req/advanced-filtering/system-by-foi` — "SHALL support a parameter **foi** of type ID_List"
- **Wire example**: `{api_root}/systems?foi=11gsd654g`
- **Also defined as `foi`** in: §16.6.4 (Deployments), §16.8.2 (SamplingFeatures), OGC 23-002 §13.2.4 (DataStreams), §13.3.3 (Observations), §13.4.4 (ControlStreams), §13.5.5 (Commands)
- **Our wire output**: `?foiId=x`

#### 3. `observedPropertyId` → `observedProperty`

**Verdict: CONFIRMED MISMATCH**

- **Spec**: OGC 23-001 §16.5.5 `/req/advanced-filtering/system-by-obsprop` — "SHALL support a parameter **observedProperty** of type ID_List"
- **Wire example**: `{api_root}/systems?observedProperty=4578441`
- **Also defined as `observedProperty`** in: §16.6.5 (Deployments), §16.7.2 (Procedures), §16.8.3 (SamplingFeatures), OGC 23-002 §13.2.3 (DataStreams)
- **Our wire output**: `?observedPropertyId=x`

#### 4. `controlledPropertyId` → `controlledProperty`

**Verdict: CONFIRMED MISMATCH**

- **Spec**: OGC 23-001 §16.5.6 `/req/advanced-filtering/system-by-controlprop` — "SHALL support a parameter **controlledProperty** of type ID_List"
- **Wire example**: `{api_root}/systems?controlledProperty=4578441`
- **Also defined as `controlledProperty`** in: §16.6.6 (Deployments), §16.7.3 (Procedures), §16.8.4 (SamplingFeatures), OGC 23-002 §13.4.3 (ControlStreams)
- **Our wire output**: `?controlledPropertyId=x`

#### 5. `systemId` (DeploymentQueryOptions) → `system`

**Verdict: CONFIRMED MISMATCH**

- **Spec**: OGC 23-001 §16.6.3 `/req/advanced-filtering/deployment-by-system` — "SHALL support a parameter **system** of type ID_List"
- **Wire example**: `{api_root}/deployments?system=b5bxc988rf`
- **Our wire output**: `?systemId=x`
- **Note**: `PropertyQueryOptions` already has the correct name `system?: string` — this inconsistency confirms the mismatch is accidental.

#### 6. `procedureId` (SystemQueryOptions) → `procedure`

**Verdict: CONFIRMED MISMATCH** (not flagged in Issue #105)

- **Spec**: OGC 23-001 §16.5.3 `/req/advanced-filtering/system-by-procedure` — "SHALL support a parameter **procedure** of type ID_List"
- **Wire example**: `{api_root}/systems?procedure=11gsd654g`
- **Our wire output**: `?procedureId=x`
- **Note**: This mismatch was not identified in the original issue but was discovered during this review.

### Non-Spec Extension Parameters (No Fix Needed)

#### `systemId` in `DatastreamQueryOptions` and `ControlStreamQueryOptions`

**Verdict: NOT AN OGC SPEC PARAMETER — OSH extension**

OGC 23-002 §13.2 defines DataStream query parameters as: `phenomenonTime`, `resultTime`, `observedProperty`, `foi`. There is no `system` parameter for DataStream filtering in the normative spec.

Similarly, §13.4 defines ControlStream query parameters as: `issueTime`, `executionTime`, `controlledProperty`, `foi`. No `system` parameter.

The `systemId` property on these QueryOptions interfaces appears to be an OpenSensorHub (OSH)-specific extension. Since there is no OGC normative name to remap to, **no change should be made** — the current name serves as an OSH-compatible extension parameter. If/when the spec adds a `system` parameter for DataStreams/ControlStreams, a remapping can be added at that time.

---

## Impact Analysis

### Current Impact

- **Silent data loss**: When a query parameter name is not recognized, spec-compliant servers return HTTP 200 with **unfiltered results**. The caller receives data and has no indication that filtering was ignored.
- **Affects 6 confirmed parameters** across `SystemQueryOptions`, `DeploymentQueryOptions`, `DatastreamQueryOptions`, `ControlStreamQueryOptions`, and `CommandQueryOptions`.
- **OSH masking**: OpenSensorHub (the primary test server) appears to accept both the spec-compliant names and the `Id`-suffixed names, which is why this has not been caught in practice until tested against a strictly-compliant server or through careful spec review.

### Scope of Affected Code

| Component                                | Impact                                                                                                     |
| ---------------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| `buildQueryString()` in `url_builder.ts` | Must add remapping layer                                                                                   |
| `model.ts` interfaces                    | **NO CHANGE** — TypeScript property names are preserved                                                    |
| Parsed resource objects                  | **NO CHANGE** — `DataStream.systemId`, `Command.currentStatus` etc. are model properties, not query params |
| `url_builder.spec.ts` assertions         | Must update expected URLs in ~17 assertions                                                                |
| Parsers (`part1.ts`, `part2.ts`)         | **NO CHANGE** — parsers populate model objects, not query params                                           |
| Integration tests                        | **NO CHANGE** — use model objects, not wire URLs                                                           |

---

## Proposed Fix Analysis

### Approach A: PARAM_NAME_MAP in `buildQueryString()` — **RECOMMENDED**

Add a static remapping dictionary and apply it during serialization:

```typescript
private static readonly PARAM_NAME_MAP: Readonly<Record<string, string>> = {
  currentStatus: 'statusCode',
  systemId: 'system',
  observedPropertyId: 'observedProperty',
  controlledPropertyId: 'controlledProperty',
  foiId: 'foi',
  procedureId: 'procedure',
};

private buildQueryString(options?: QueryOptions): string {
  if (!options) return '';
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(options)) {
    if (value === undefined || value === null) continue;
    const wireName = CSAPIQueryBuilder.PARAM_NAME_MAP[key] ?? key;
    // ... existing validation for bbox, temporal, limit, arrays ...
    params.append(wireName, String(value));
  }
  // ...
}
```

**Advantages**:

- Preserves TypeScript API — no breaking change for consumers
- Contained to a single method
- Trivially testable
- Can be extended if future mismatches are discovered

**Risks**:

- Changes wire format for 6 parameters (this is intentional — the current wire format is incorrect)
- Existing tests that assert URL strings must be updated (~17 assertions)

### Approach B: Rename TypeScript Properties — **NOT RECOMMENDED**

Renaming `currentStatus` to `statusCode` in `CommandQueryOptions`, `foiId` to `foi` in `SystemQueryOptions`, etc.

**Why not**:

- **Breaking API change** for all consumers of the library
- Would also create naming confusion: `Command.currentStatus` (model property) would coexist with `CommandQueryOptions.statusCode` (query param) — less intuitive than hiding the remapping internally
- Larger diff, harder to review
- Violates AI Operational Constraints §2.3: "Do not rename files, symbols, or tests unless required by the task"

### Approach A Risk Elaboration

The `PARAM_NAME_MAP` approach has one subtle consideration regarding the `systemId` entries in `DatastreamQueryOptions` and `ControlStreamQueryOptions`:

The map entry `systemId: 'system'` would remap `systemId` universally — including for DataStream and ControlStream queries where `systemId` is an OSH extension (not a spec parameter). Remapping to `system` for these cases is reasonable because:

1. If/when the spec adds this parameter, `system` is the most likely name (consistent with Deployment's `system` parameter)
2. OSH likely accepts both forms
3. The alternative — context-dependent remapping — adds disproportionate complexity

However, if there is concern about this, the `systemId` entry could be omitted from the map initially. The 5 remaining entries are unambiguously correct.

---

## Risk Assessment

| Risk Factor                                      | Assessment                                                                               |
| ------------------------------------------------ | ---------------------------------------------------------------------------------------- |
| **Backward compatibility (TypeScript API)**      | **None** — QueryOptions interface properties are not renamed.                            |
| **Wire format change**                           | **Yes, intentional** — 6 URL parameter names change to match OGC spec.                   |
| **Behavioral change for OSH users**              | **None expected** — OSH accepts both forms per Issue #105 note.                          |
| **Behavioral change for spec-compliant servers** | **Positive** — filters that were silently ignored will now work correctly.               |
| **Model property names**                         | **Unchanged** — `Command.currentStatus`, `DataStream.systemId`, etc. remain as-is.       |
| **Test maintenance**                             | **~17 assertions** update expected URL strings.                                          |
| **Pattern consistency**                          | **Improves** — `PropertyQueryOptions` already uses correct names; this aligns the rest.  |
| **Estimated diff size**                          | ~60 lines (10-line map + 2-line `buildQueryString` change + ~17 test assertion updates). |

### Stop Condition Check (per AI_OPERATIONAL_CONSTRAINTS.md)

| Condition                                | Status                                                                                               |
| ---------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| Spec authority unclear?                  | **No** — all 6 mismatches traced to normative requirements with OpenAPI fragments.                   |
| Risk of data loss?                       | **No** — the fix _prevents_ current silent data loss. Without the fix, filters are silently ignored. |
| Changes silently alter library behavior? | **No** — the wire format change is deliberate and documented. The TypeScript API is unchanged.       |

**All stop conditions clear. Implementation may proceed with explicit caution.**

---

## Recommendation

**FIX** — Implement Approach A (`PARAM_NAME_MAP` in `buildQueryString()`).

### Scope Boundaries

**MUST change**:

1. Add `PARAM_NAME_MAP` static dictionary to `CSAPIQueryBuilder`
2. Apply remapping in `buildQueryString()` before `params.append()`
3. Update ~17 test assertions in `url_builder.spec.ts` to expect corrected parameter names

**MUST NOT change**:

1. TypeScript interface property names in `model.ts` — no breaking API changes
2. Model property names on parsed resource objects (`Command.currentStatus`, `DataStream.systemId`, etc.)
3. Parser logic in `part1.ts`, `part2.ts`, `part1.spec.ts`, `part2.spec.ts`
4. Integration test fixtures or command/observation JSON fixtures
5. Any other method in `url_builder.ts` beyond `buildQueryString()`
6. Any existing method signatures or return types

### Implementation Priority

This is a correctness bug that causes silent filter failures. It should be addressed before any new filtering functionality is added (e.g., Issue #106 missing query option fields), since #106 would add more parameters that need correct wire names.

---

## Related Issues

| Issue                                                                             | Relationship                                                                                 |
| --------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| [#105](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/105)                 | Source issue for this report                                                                 |
| [#106](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/106)                 | Missing Part 2 query option fields — dependent on #105 (new params should use correct names) |
| [#107](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/107)                 | Nested builder methods accept base QueryOptions — related but independent                    |
| [ogc-csapi-explorer#35](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/35) | Demo app issue that discovered the mismatch                                                  |

---

## Appendices

### A. Reference Documents

| #   | Document                                                                                | Relevance                                                                                                                             |
| --- | --------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | [OGC 23-001 — Connected Systems API Part 1](https://docs.ogc.org/is/23-001/23-001.html) | §16 Advanced Filtering — normative query parameter definitions for Systems, Deployments, Procedures, SamplingFeatures, Properties     |
| 2   | [OGC 23-002 — Connected Systems API Part 2](https://docs.ogc.org/is/23-002/23-002.html) | §13 Advanced Filtering — normative query parameter definitions for DataStreams, Observations, ControlStreams, Commands, CommandStatus |
| 3   | [AI_OPERATIONAL_CONSTRAINTS.md](../../governance/AI_OPERATIONAL_CONSTRAINTS.md)         | Mandatory operational constraints governing this assessment                                                                           |
| 4   | [Issue #105](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/105)                 | Source issue identifying the parameter name mismatches                                                                                |
| 5   | [ogc-csapi-explorer#35](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/35)       | Demo app issue where filter failure was observed in practice                                                                          |
| 6   | [Issue #106](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/106)                 | Downstream issue — missing query option fields that depend on correct naming                                                          |

### B. Files Reviewed

| File                                            | Lines                                             | Purpose                                                                                                    |
| ----------------------------------------------- | ------------------------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| `src/ogc-api/csapi/url_builder.ts`              | 260–316                                           | `buildQueryString()` implementation — the serialization method with no remapping                           |
| `src/ogc-api/csapi/model.ts`                    | 119–250                                           | QueryOptions interfaces — property names that become wire parameter names                                  |
| `src/ogc-api/csapi/url_builder.spec.ts`         | 380–420, 915–920, 1680–1715, 2180–2190, 2485–2520 | Test assertions verifying current (incorrect) URL output                                                   |
| `src/ogc-api/csapi/formats/part2.ts`            | 164, 257, 272–365                                 | Parser code using `systemId` and `currentStatus` as model properties (NOT query params — no change needed) |
| `docs/governance/AI_OPERATIONAL_CONSTRAINTS.md` | 1–100                                             | Operational constraints verification                                                                       |

### C. Complete Parameter Name Verification Table

| TypeScript Property    | Interface(s)                                        | Current Wire Name         | OGC Spec Wire Name      | Spec Reference                 | Verdict          |
| ---------------------- | --------------------------------------------------- | ------------------------- | ----------------------- | ------------------------------ | ---------------- |
| `currentStatus`        | `CommandQueryOptions`                               | `?currentStatus=PENDING`  | `?statusCode=PENDING`   | 23-002 §13.5.3                 | **MISMATCH**     |
| `foiId`                | `SystemQueryOptions`                                | `?foiId=x`                | `?foi=x`                | 23-001 §16.5.4                 | **MISMATCH**     |
| `observedPropertyId`   | `SystemQueryOptions`, `DatastreamQueryOptions`      | `?observedPropertyId=x`   | `?observedProperty=x`   | 23-001 §16.5.5, 23-002 §13.2.3 | **MISMATCH**     |
| `controlledPropertyId` | `SystemQueryOptions`, `ControlStreamQueryOptions`   | `?controlledPropertyId=x` | `?controlledProperty=x` | 23-001 §16.5.6, 23-002 §13.4.3 | **MISMATCH**     |
| `systemId`             | `DeploymentQueryOptions`                            | `?systemId=x`             | `?system=x`             | 23-001 §16.6.3                 | **MISMATCH**     |
| `procedureId`          | `SystemQueryOptions`                                | `?procedureId=x`          | `?procedure=x`          | 23-001 §16.5.3                 | **MISMATCH**     |
| `systemId`             | `DatastreamQueryOptions`                            | `?systemId=x`             | (not defined)           | —                              | ⚠️ OSH extension |
| `systemId`             | `ControlStreamQueryOptions`                         | `?systemId=x`             | (not defined)           | —                              | ⚠️ OSH extension |
| `parent`               | `SystemQueryOptions`, `DeploymentQueryOptions`      | `?parent=x`               | `?parent=x`             | 23-001 §16.5.2, §16.6.2        | ✅ Correct       |
| `recursive`            | `SystemQueryOptions`, `DeploymentQueryOptions`      | `?recursive=true`         | `?recursive=true`       | 23-001 §10.6                   | ✅ Correct       |
| `system`               | `PropertyQueryOptions`                              | `?system=x`               | `?system=x`             | —                              | ✅ Correct       |
| `baseProperty`         | `PropertyQueryOptions`                              | `?baseProperty=x`         | `?baseProperty=x`       | 23-001 §16.9.2                 | ✅ Correct       |
| `phenomenonTime`       | `DatastreamQueryOptions`, `ObservationQueryOptions` | `?phenomenonTime=x`       | `?phenomenonTime=x`     | 23-002 §13.2.1, §13.3.1        | ✅ Correct       |
| `resultTime`           | `DatastreamQueryOptions`, `ObservationQueryOptions` | `?resultTime=x`           | `?resultTime=x`         | 23-002 §13.2.2, §13.3.2        | ✅ Correct       |
| `issueTime`            | `CommandQueryOptions`                               | `?issueTime=x`            | `?issueTime=x`          | 23-002 §13.5.1                 | ✅ Correct       |
| `executionTime`        | `CommandQueryOptions`                               | `?executionTime=x`        | `?executionTime=x`      | 23-002 §13.5.2                 | ✅ Correct       |
| `q`                    | `QueryOptions`                                      | `?q=x`                    | `?q=x`                  | 23-001 §16.3.3                 | ✅ Correct       |
| `bbox`                 | `QueryOptions`                                      | `?bbox=x`                 | `?bbox=x`               | OGC API Features §7.15.3       | ✅ Correct       |
| `datetime`             | `QueryOptions`                                      | `?datetime=x`             | `?datetime=x`           | 23-001 §8.7                    | ✅ Correct       |
| `limit`                | `QueryOptions`                                      | `?limit=x`                | `?limit=x`              | OGC API Features §7.15.2       | ✅ Correct       |
| `id`                   | `QueryOptions`                                      | `?id=x`                   | `?id=x`                 | 23-001 §16.3.2                 | ✅ Correct       |
| `uid`                  | `QueryOptions`                                      | `?uid=x`                  | `?uid=x`                | —                              | ✅ Correct       |
