# Phase 2.3 Implementation Overview — Where We Stand Now

## The Story So Far

Phase 1 built the **foundation**: a type system, helper utilities, a stub query builder, and the endpoint integration that wired everything into `OgcApiEndpoint`.

Phase 2.1 (Issue #5) turned that stub into a **complete Systems surface** — 12 methods covering reading, writing, history, hierarchy, and cross-resource navigation.

Phase 2.2 (Issues #6, #34, #35, #38) fixed two critical live-server findings (three link relation conventions, top-level resource URLs), implemented the full Deployments surface (8 methods), refactored a DRY violation into the shared `scanCsapiLinks()` helper, and did a comprehensive code review that produced a governance-level lessons learned document.

Phase 2.3 (Issue #7) adds the **Procedures** resource type — the third resource surface and the first one implemented with the lessons learned guardrails in place.

---

## What Changed Since Phase 2.2

### Issue #38 — Code Review Cleanup (End of Phase 2.2)

Before starting Procedures, we closed out three findings from the Phase 2.2 code review:

- **F1 (Dead code)**: Removed unused `encodeArrayParameter` from `helpers.ts` and its 4 tests
- **F2 (DRY violation)**: Extracted 3-convention link scanning into `scanCsapiLinks()` in `helpers.ts`, refactored both `extractAvailableResources()` and `extractRootResourceUrls()` to use it
- **F3 (Strict-mode bug)**: Fixed a latent `Map.get()` type-narrowing issue in `buildResourceUrl()` using a local variable pattern

### Lessons Learned Governance Document

After closing out Issue #38 and completing a live server smoke re-test, we distilled all findings from Phase 1 through 2.2 into a shared governance document: [`docs/governance/phase-2-lessons-learned.md`](../governance/phase-2-lessons-learned.md).

This document contains 7 actionable lessons:

| #   | Lesson                                            | Key Guardrail                                                 |
| --- | ------------------------------------------------- | ------------------------------------------------------------- |
| L1  | Test thoroughness decays                          | Mandatory 8-item test checklist per resource type             |
| L2  | Each resource type has different query options    | Query parameter applicability table (9 resources × 20 params) |
| L3  | Temporal keys are hardcoded in `buildQueryString` | Verify temporal keys match `QueryOptions` interfaces          |
| L4  | `assertResourceAvailable` string must be correct  | Grep-verify after implementation                              |
| L5  | All work goes into existing files                 | No new `.ts` files in Phase 2                                 |
| L6  | Review findings must become work items            | Note concerns as issue comments                               |
| L7  | DRY violations compound across issues             | Don't copy-paste method bodies                                |

Each remaining Phase 2 issue (#7–#13) received a customized comment linking to this document with issue-specific callouts. This is the first resource type where the lessons were applied from the start.

### Issue #7 — Procedures Methods

Procedures is the third Part 1 resource type. It represents methodologies for observation, actuation, or sampling (e.g., a thermometer calibration procedure, a satellite imaging protocol). In GeoJSON encoding, a Procedure's geometry is always `null` — detailed descriptions use SensorML.

Eight new public methods:

```typescript
// ── Reading ──
builder.getProcedures({ limit: 10, q: 'thermometer' });
builder.getProcedure('proc-001');

// ── Writing ──
builder.createProcedure();
builder.updateProcedure('proc-001');
builder.deleteProcedure('proc-001');

// ── Navigation ──
builder.getProcedureSystems('proc-001', { limit: 5 });
builder.getProcedureDataStreams('proc-001');

// ── History ──
builder.getProcedureHistory('proc-001', { limit: 5 });
```

### Why Procedures Is Simpler Than Systems/Deployments

`ProcedureQueryOptions` is defined as a type alias for the base `QueryOptions`:

```typescript
export type ProcedureQueryOptions = QueryOptions;
```

This means Procedures supports only the base query parameters:

| Supported            | Not Supported                   |
| -------------------- | ------------------------------- |
| `limit`, `offset`    | `bbox`                          |
| `q` (keyword search) | `datetime`                      |
| `id` (filter by ID)  | `parent` / `recursive`          |
| `f` (format)         | `phenomenonTime` / `resultTime` |
| `cursor`             | Any resource-specific filter    |

Procedures has no spatial extent (geometry is always null), no temporal parameters, and no hierarchy (no sub-procedures). This made the implementation straightforward — each method delegates to `buildResourceUrl()` and `buildQueryString()` with no special casing needed.

### Association Methods

Procedures introduces two cross-resource navigation methods:

**`getProcedureSystems(id, options?)`** — Lists systems that implement a given procedure. For example, "which sensors use this thermometer calibration procedure?" Builds `/procedures/{id}/systems`.

**`getProcedureDataStreams(id, options?)`** — Lists datastreams associated with a procedure. This is a Part 2 cross-reference — it connects a Part 1 procedure to the Part 2 datastreams that use it. Builds `/procedures/{id}/datastreams`.

Both methods accept optional `QueryOptions` for pagination and filtering of the results.

---

## Lessons Learned Compliance

This is the first resource type implemented with the lessons learned document as a mandatory pre-read. Here's how each lesson was applied:

### L1 — Test Checklist ✅

All 8 checklist items verified:

| Checklist Item                             | Status | Evidence                                                              |
| ------------------------------------------ | ------ | --------------------------------------------------------------------- |
| Collection query with exact URL (`toBe()`) | ✅     | `getProcedures` — 8 tests with exact URL assertions                   |
| Every applicable query option tested       | ✅     | `limit`, `offset`, `q`, `id`, array `id`, `f`, multiple combined      |
| Single resource retrieval with exact URL   | ✅     | `getProcedure('proc-001')` with exact URL                             |
| CRUD operation URLs                        | ✅     | `createProcedure`, `updateProcedure`, `deleteProcedure` all exact     |
| Each nested/association method tested      | ✅     | `getProcedureSystems`, `getProcedureDataStreams` both tested          |
| Nested method with pagination + filtering  | ✅     | `getProcedureSystems('proc-001', { limit: 5, offset: 10 })` exact URL |
| Resource validation failure                | ✅     | All 8 methods verified to throw `EndpointError` when unavailable      |
| Temporal parameters with `toBe()`          | N/A    | Procedures has no temporal parameters                                 |

### L2 — Query Parameter Applicability ✅

Consulted the parameter table. Correctly excluded `bbox`, `datetime`, `parent`, `recursive` — no tests for those parameters on Procedures methods.

### L3 — Temporal Keys ✅

Procedures does not add new temporal keys. No changes to `buildQueryString` needed — confirmed.

### L4 — Resource String Verification ✅

Grep-verified after implementation: all 8 methods call `this.assertResourceAvailable('procedures')`. No copy-paste errors from Systems/Deployments resource strings.

### L5 — File Scope ✅

Only two files modified: `url_builder.ts` and `url_builder.spec.ts`. No new files created.

### L6/L7 — No Findings ✅

No unexpected behavior observed. No DRY violations — each method delegates to shared infrastructure without duplicating logic.

---

## All 28 Public Methods

| #   | Method                        | Resource    | Pattern                                       |
| --- | ----------------------------- | ----------- | --------------------------------------------- |
| 1   | `getSystems`                  | Systems     | Collection list with `SystemQueryOptions`     |
| 2   | `getSystem`                   | Systems     | Single item by ID                             |
| 3   | `createSystem`                | Systems     | POST target                                   |
| 4   | `updateSystem`                | Systems     | PUT target                                    |
| 5   | `deleteSystem`                | Systems     | DELETE target                                 |
| 6   | `getSystemHistory`            | Systems     | `/systems/{id}/history`                       |
| 7   | `getSystemSubsystems`         | Systems     | `/systems/{id}/subsystems`                    |
| 8   | `getSystemDataStreams`        | Systems     | `/systems/{id}/datastreams`                   |
| 9   | `getSystemControlStreams`     | Systems     | `/systems/{id}/controlstreams`                |
| 10  | `getSystemSamplingFeatures`   | Systems     | `/systems/{id}/samplingFeatures`              |
| 11  | `getSystemDeployments`        | Systems     | `/systems/{id}/deployments`                   |
| 12  | `getSystemProcedures`         | Systems     | `/systems/{id}/procedures`                    |
| 13  | `getDeployments`              | Deployments | Collection list with `DeploymentQueryOptions` |
| 14  | `getDeployment`               | Deployments | Single item by ID                             |
| 15  | `createDeployment`            | Deployments | POST target                                   |
| 16  | `updateDeployment`            | Deployments | PUT target                                    |
| 17  | `deleteDeployment`            | Deployments | DELETE target                                 |
| 18  | `getDeploymentSubdeployments` | Deployments | `/deployments/{id}/subdeployments`            |
| 19  | `getDeploymentSystems`        | Deployments | `/deployments/{id}/systems`                   |
| 20  | `getDeploymentHistory`        | Deployments | `/deployments/{id}/history`                   |
| 21  | `getProcedures`               | Procedures  | Collection list with `ProcedureQueryOptions`  |
| 22  | `getProcedure`                | Procedures  | Single item by ID                             |
| 23  | `createProcedure`             | Procedures  | POST target                                   |
| 24  | `updateProcedure`             | Procedures  | PUT target                                    |
| 25  | `deleteProcedure`             | Procedures  | DELETE target                                 |
| 26  | `getProcedureSystems`         | Procedures  | `/procedures/{id}/systems`                    |
| 27  | `getProcedureDataStreams`     | Procedures  | `/procedures/{id}/datastreams`                |
| 28  | `getProcedureHistory`         | Procedures  | `/procedures/{id}/history`                    |

---

## The Complete File Inventory

### Source Files

| File                               | Lines | Purpose                                                                                                     |
| ---------------------------------- | ----- | ----------------------------------------------------------------------------------------------------------- |
| `src/ogc-api/csapi/model.ts`       | 581   | Type system — 9 resource types, 10 query options interfaces, collection types, constants                    |
| `src/ogc-api/csapi/helpers.ts`     | 210   | 6 pure utility functions + `scanCsapiLinks()` — temporal formatting, encoding, validation, link scanning    |
| `src/ogc-api/csapi/url_builder.ts` | 792   | `CSAPIQueryBuilder` class — 28 methods (12 Systems + 8 Deployments + 8 Procedures) + private infrastructure |
| `src/ogc-api/endpoint.ts`          | 840   | Integration — `hasConnectedSystems`, `csapiCollections`, `csapi()`, `extractRootResourceUrls()`             |

### Test Files

| File                                         | Tests | Coverage                                                                                                               |
| -------------------------------------------- | ----- | ---------------------------------------------------------------------------------------------------------------------- |
| `src/ogc-api/csapi/model.spec.ts`            | 27    | Every resource interface, constant correctness, type compatibility                                                     |
| `src/ogc-api/csapi/helpers.spec.ts`          | 34    | All helpers including `scanCsapiLinks()` with 3 conventions, edge cases, error paths                                   |
| `src/ogc-api/csapi/url_builder.spec.ts`      | 91    | Constructor (10), resource validation (4), top-level URLs (7), 12 Systems, 8 Deployments, 8 Procedures describe blocks |
| `src/ogc-api/endpoint.spec.ts` (CSAPI block) | 6     | End-to-end with fixture data: detection, collection filtering, builder creation, caching, error handling               |

**Total: 152 CSAPI unit tests + 6 integration tests = 158 tests.**

### Documentation Files (This Phase)

| File                                                           | Purpose                                                      |
| -------------------------------------------------------------- | ------------------------------------------------------------ |
| `docs/implementation/phase-2.2-code-review.md`                 | 15 findings (F1–F15) with root cause analysis                |
| `docs/implementation/live-server-smoke-test-post-phase-2.2.md` | Post-cleanup smoke test confirming all fixes                 |
| `docs/governance/phase-2-lessons-learned.md`                   | 7 actionable lessons with test checklist and parameter table |
| `docs/implementation/phase-2.3-overview.md`                    | This document                                                |

---

## How The Procedures Tests Are Organized

The Procedures tests add 20 new test cases organized in 7 describe blocks:

| Block                  | Tests | What It Verifies                                                                                           |
| ---------------------- | ----- | ---------------------------------------------------------------------------------------------------------- |
| `getProcedures`        | 8     | No options, limit, offset, q, single id, array id, f (format), multiple combined — all with exact `toBe()` |
| `getProcedure`         | 2     | Basic URL with ID, special character encoding (`urn:example:proc:001`)                                     |
| Procedure CRUD         | 3     | `createProcedure` (POST target), `updateProcedure` (PUT target), `deleteProcedure` (DELETE target)         |
| Procedure associations | 4     | `getProcedureSystems` basic + with pagination, `getProcedureDataStreams` basic + with options              |
| `getProcedureHistory`  | 2     | Basic URL, with limit parameter                                                                            |
| Resource validation    | 1     | All 8 methods throw `EndpointError` when `procedures` is not in `availableResources`                       |

The resource validation test checks all 8 methods in a single test case (not 8 separate tests) to verify that the `assertResourceAvailable` guard works consistently across the entire Procedures surface.

---

## How The Pieces Fit Together

The developer experience now includes 3 complete resource surfaces:

```typescript
import { OgcApiEndpoint } from 'ogc-client';

const endpoint = new OgcApiEndpoint('https://sensors.example.com/api');

if (await endpoint.hasConnectedSystems) {
  const builder = await endpoint.csapi('weather-stations');

  // ── Systems (Phase 2.1) — 12 methods ──
  const systems = builder.getSystems({ limit: 20, recursive: true });
  const system = builder.getSystem('station-42');
  const create = builder.createSystem();
  const streams = builder.getSystemDataStreams('station-42');
  const history = builder.getSystemHistory('station-42');
  const subs = builder.getSystemSubsystems('station-42', { recursive: true });

  // ── Deployments (Phase 2.2) — 8 methods ──
  const deps = builder.getDeployments({ systemId: 'station-42' });
  const dep = builder.getDeployment('dep-001');
  const subdeps = builder.getDeploymentSubdeployments('dep-001');
  const depSys = builder.getDeploymentSystems('dep-001');

  // ── Procedures (Phase 2.3) — 8 methods ──
  const procs = builder.getProcedures({ q: 'thermometer', limit: 10 });
  const proc = builder.getProcedure('proc-001');
  const createP = builder.createProcedure();
  const updateP = builder.updateProcedure('proc-001');
  const deleteP = builder.deleteProcedure('proc-001');
  const procSys = builder.getProcedureSystems('proc-001', { limit: 5 });
  const procDS = builder.getProcedureDataStreams('proc-001');
  const procHist = builder.getProcedureHistory('proc-001', { limit: 5 });
}
```

---

## What Comes Next

Phase 2.3 completed Procedures — the third of five Part 1 resources. The remaining Phase 2 issues:

| Issue  | Resource Type        | Methods | Complexity  | Notes                                                                                               |
| ------ | -------------------- | ------- | ----------- | --------------------------------------------------------------------------------------------------- |
| **#8** | **SamplingFeatures** | 8       | Medium      | Part 1; supports `bbox` but NOT `datetime`. Has `getSamplingFeatureObservations` (Part 2 cross-ref) |
| **#9** | **Properties**       | 6       | Medium      | Part 1; read-only (no create/update/delete). NOT a GeoJSON Feature.                                 |
| #10    | DataStreams          | 11      | Medium-High | First Part 2 resource; introduces temporal filtering (`datetime`)                                   |
| #11    | Observations         | 9       | Medium-High | Part 2; `phenomenonTime`, `resultTime`, cursor pagination, bulk create                              |
| #12    | ControlStreams       | 8       | Medium-High | Part 2; mirrors DataStreams for control/actuation; `cmdFormat`, feasibility                         |
| #13    | Commands             | 10      | Medium-High | Part 2; status lifecycle, cancel operation; final resource type                                     |

Issues #8–#9 are similar in complexity to #7 — Part 1 resources with base query options. After those, Issues #10–#13 introduce Part 2 temporal parameters and new patterns (cursor pagination, format parameters, feasibility checking). The infrastructure already handles all these parameter types in `buildQueryString()`.

---

## Summary

| Metric                               | Phase 2.2                | Phase 2.3 (now)       | Delta |
| ------------------------------------ | ------------------------ | --------------------- | ----- |
| Public methods on CSAPIQueryBuilder  | 20                       | 28                    | +8    |
| Resource types with full API surface | 2 (Systems, Deployments) | 3 (+ Procedures)      | +1    |
| CSAPI unit tests                     | 128                      | 152                   | +24   |
| Total tests (incl. integration)      | 134                      | 158                   | +24   |
| url_builder.ts lines                 | 624                      | 792                   | +168  |
| url_builder.spec.ts tests            | 71                       | 91                    | +20   |
| Issues closed (cumulative)           | 9 (1–6, 34, 35, 38)      | 10 (+ #7)             | +1    |
| Governance documents                 | 2                        | 3 (+ lessons learned) | +1    |

Phase 2.3 is a clean, incremental addition. Unlike Phase 2.2 — which required infrastructure fixes, a code review, and a cleanup issue — Phase 2.3 was pure feature work: 8 methods, 20 tests, one commit, zero findings. The lessons learned document did its job — the implementation was right the first time.
