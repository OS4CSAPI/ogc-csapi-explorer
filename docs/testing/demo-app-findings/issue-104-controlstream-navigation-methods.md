# Issue #104 — Findings Report: ControlStream Missing Nested Navigation Methods

**Issue**: [#104 — URL builder: ControlStream missing nested navigation methods that DataStream has (systems, procedures, history)](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/104)

**Date**: 2025-07-17
**Status**: Assessed — Recommendation: **FIX**
**Risk Level**: Low (purely additive, uses existing patterns)

---

## AI Operational Constraints Acknowledgment

This report was prepared in accordance with the project's
[AI Operational Constraints](../../governance/AI_OPERATIONAL_CONSTRAINTS.md), which establish:

- **Authority Precedence**: OGC standards → project governance → AI operational constraints.
- **Standards Discipline**: All implementations must be directly traceable to normative OGC specifications.
- **Mandatory Stop Conditions**: Implementation must not proceed if spec authority is unclear, risk of data loss exists, or changes could silently alter library behavior.

The recommendation below is constrained by these rules. Any code change must be purely additive and must not modify, remove, or alter the behavior of any existing method.

---

## Executive Summary

`CSAPIQueryBuilder` in `src/ogc-api/csapi/url_builder.ts` provides five sub-resource navigation methods for **DataStream** (Schema, Observations, Systems, Procedures, History) but only three for **ControlStream** (Schema, Commands, Feasibility). ControlStream is missing the `Systems`, `Procedures`, and `History` navigation methods.

This is an implementation gap — not a design choice. OGC 23-002 (Connected Systems API — Part 2) defines structurally identical association tables for both resource types (Table 5 for DataStream, Table 10 for ControlStream), and every other resource type in the url_builder already has a History method. ControlStream is the sole exception.

**Recommendation**: FIX — Add three new methods (`getControlStreamSystems`, `getControlStreamProcedures`, `getControlStreamHistory`) plus corresponding unit tests. The change is purely additive with zero backward compatibility risk.

---

## Issue Description

### What Was Reported

Issue #104 identifies an asymmetry between DataStream and ControlStream navigation methods in `CSAPIQueryBuilder`. DataStream has five sub-resource methods while ControlStream has only three:

| Navigation Method | DataStream                          | ControlStream                          |
| ----------------- | ----------------------------------- | -------------------------------------- |
| Schema            | `getDataStreamSchema` (L1998→L2000) | `getControlStreamSchema` (L1998→L2000) |
| Child resources   | `getDataStreamObservations` (L1571) | `getControlStreamCommands` (L2023)     |
| Systems           | `getDataStreamSystems` (L1615)      | **MISSING**                            |
| Procedures        | `getDataStreamProcedures` (L1636)   | **MISSING**                            |
| History           | `getDataStreamHistory` (L1657)      | **MISSING**                            |
| Feasibility       | N/A                                 | `checkCommandFeasibility` (~L2052)     |

### Context

ControlStream is the **only** resource type in the entire url_builder that lacks a History method. All other types — System (L470), Deployment (L888), Procedure (L1065), SamplingFeature (L1245), Property (L1394), DataStream (L1657), Observation (L1847) — implement it.

---

## Source Code Review

### File: `src/ogc-api/csapi/url_builder.ts` (2329 lines)

**DataStream pattern** (lines 1615–1670): All three methods follow an identical structure:

```typescript
getDataStreamSystems(id: string, options?: QueryOptions): string {
  this.assertResourceAvailable('datastreams');
  return this.buildResourceUrl('datastreams', id, 'systems', options);
}

getDataStreamProcedures(id: string, options?: QueryOptions): string {
  this.assertResourceAvailable('datastreams');
  return this.buildResourceUrl('datastreams', id, 'procedures', options);
}

getDataStreamHistory(id: string, options?: QueryOptions): string {
  this.assertResourceAvailable('datastreams');
  return this.buildResourceUrl('datastreams', id, 'history', options);
}
```

**ControlStream section** (lines 1985–2060): Implements Schema, Commands, and Feasibility only. The three missing methods would follow the exact same `buildResourceUrl` pattern with `'controlStreams'` as the resource type.

**Proposed addition** (would be inserted between `checkCommandFeasibility` at ~L2060 and the Commands section at ~L2065):

```typescript
getControlStreamSystems(id: string, options?: QueryOptions): string {
  this.assertResourceAvailable('controlStreams');
  return this.buildResourceUrl('controlStreams', id, 'systems', options);
}

getControlStreamProcedures(id: string, options?: QueryOptions): string {
  this.assertResourceAvailable('controlStreams');
  return this.buildResourceUrl('controlStreams', id, 'procedures', options);
}

getControlStreamHistory(id: string, options?: QueryOptions): string {
  this.assertResourceAvailable('controlStreams');
  return this.buildResourceUrl('controlStreams', id, 'history', options);
}
```

### File: `src/ogc-api/csapi/url_builder.spec.ts`

Existing ControlStream tests cover Schema (L2272) and Commands (L2295), plus EndpointError guards for both (L2371–L2372). New tests for Systems, Procedures, and History would mirror the DataStream equivalents at L1896, L1906, L1917 and add EndpointError guards.

---

## Reference Document Review

### OGC 23-002 — Connected Systems API Part 2: Dynamic Data

**Table 5 — DataStream Associations**:
| Association | SOSA/SSN Mapping | Cardinality |
|---|---|---|
| system | sosa:isObservedBy | Required — single System |
| observations | sosa:hasMember | Required — list of Observations |
| procedure | sosa:usedProcedure | Optional — single Procedure |
| deployment | — | Optional — single Deployment |
| samplingFeatures | sosa:hasFeatureOfInterest | Optional — list |
| featuresOfInterest | sosa:hasUltimateFeatureOfInterest | Optional — list |

**Table 10 — ControlStream Associations**:
| Association | SOSA/SSN Mapping | Cardinality |
|---|---|---|
| system | sosa:madeByActuator | Required — single System |
| commands | sosa:hasMember | Required — list of Commands |
| procedure | sosa:usedProcedure | Optional — single Procedure |
| deployment | — | Optional — single Deployment |
| samplingFeatures | sosa:hasFeatureOfInterest | Optional — list |
| featuresOfInterest | sosa:hasUltimateFeatureOfInterest | Optional — list |

**Key finding**: The association structures are **identical** (only the domain-specific resource differs: Observations vs Commands, isObservedBy vs madeByActuator). Both define `system` and `procedure` as navigable associations. There is no specification basis for the current asymmetry.

### OGC 23-002 — History Endpoint

The `history` sub-resource is a versioning endpoint that applies uniformly across all resource types. The spec's design intent does not exclude ControlStream from version history — every resource accessible through a canonical URL can have a history. ControlStream's canonical URL is explicitly defined in Requirement 19 (`{api_root}/controlstreams/{id}`), confirming it participates in the same resource lifecycle.

---

## Risk Assessment

| Risk Factor                | Assessment                                                                                            |
| -------------------------- | ----------------------------------------------------------------------------------------------------- |
| **Backward compatibility** | **None** — purely additive (3 new methods). No existing method is modified or removed.                |
| **Behavioral change**      | **None** — all existing methods, return values, and error behaviors remain identical.                 |
| **Pattern consistency**    | **Improves** — eliminates the only asymmetry in the url_builder's navigation methods.                 |
| **Spec conformance**       | **Improves** — Tables 5 and 10 define identical associations; the implementation should reflect that. |
| **Test coverage**          | **Improves** — adds tests for previously untested navigation paths.                                   |
| **Estimated diff size**    | ~80 lines (3 methods with JSDoc + 6–9 test cases).                                                    |

### Stop Condition Check (per AI_OPERATIONAL_CONSTRAINTS.md)

| Condition                        | Status                                                 |
| -------------------------------- | ------------------------------------------------------ |
| Spec authority unclear?          | **No** — Tables 5/10 are unambiguous.                  |
| Risk of data loss?               | **No** — URL builder is read-only (generates strings). |
| Changes silently alter behavior? | **No** — purely additive.                              |

**All stop conditions clear. Implementation may proceed.**

---

## Recommendation

**FIX** — Add three methods to `CSAPIQueryBuilder`:

1. `getControlStreamSystems(id, options?)` → `controlStreams/{id}/systems`
2. `getControlStreamProcedures(id, options?)` → `controlStreams/{id}/procedures`
3. `getControlStreamHistory(id, options?)` → `controlStreams/{id}/history`

Each method follows the exact pattern established by the DataStream equivalents: call `assertResourceAvailable('controlStreams')`, then delegate to `buildResourceUrl`.

**Test additions**:

- 3 happy-path URL generation tests (mirroring DataStream tests at L1896, L1906, L1917)
- 3 EndpointError guard tests (mirroring DataStream guards at L1959–L1961)

**Implementation priority**: This is a straightforward gap-fill with minimal risk. It can be implemented independently of Issues #102 and #103.

---

## Related Issues

- **Issue #102** — ControlStream query parameter model incomplete (DEFERRED — `CommandQueryOptions` type scope)
- **Issue #103** — Cross-reference fields not extracted in Part 2 parsers (FIXED — commit `617b42f`)
- **Issue #99** — EDR collection type detection (NO ACTION)
- **Issue #100** — Fixture metadata inconsistencies (DEFERRED)

---

## Appendices

### A. Reference Documents

- [OGC 23-002 — Connected Systems API Part 2: Dynamic Data](https://docs.ogc.org/is/23-002/23-002.html) — Tables 5, 10; Requirements 17–34
- [AI_OPERATIONAL_CONSTRAINTS.md](../../governance/AI_OPERATIONAL_CONSTRAINTS.md)
- [Issue #104](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/104)

### B. Files Reviewed

| File                                            | Lines                | Purpose                                        |
| ----------------------------------------------- | -------------------- | ---------------------------------------------- |
| `src/ogc-api/csapi/url_builder.ts`              | 1610–1680, 1985–2095 | DataStream and ControlStream method comparison |
| `src/ogc-api/csapi/url_builder.spec.ts`         | 1896–1961, 2272–2372 | Existing test patterns                         |
| `docs/governance/AI_OPERATIONAL_CONSTRAINTS.md` | 1–100                | Operational constraints verification           |
