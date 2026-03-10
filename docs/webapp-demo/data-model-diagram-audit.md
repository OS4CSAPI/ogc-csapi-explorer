# Data Model Diagram — Navigation Audit

**Date:** 2025-03-10  
**Scope:** `DataModelDiagram.vue`, `ResourceDetail.vue`, `state.ts`  
**Server:** OSH SensorHub @ `os4csapi-osh.duckdns.org`  
**Method:** Code review + live endpoint testing (30+ endpoints)

---

## Executive Summary

The interactive data model diagram in the Resource Detail view visualises the CSAPI / SOSA / SSN resource graph (9 node types, 11 edges). Testing against the live OSH SensorHub server revealed **20 issues** across four categories: server endpoints returning 400, diagram highlighting / count problems, navigation link failures, and edge / relationship model gaps.

All issues documented below are **client-side observable** — the fixes proposed in the companion implementation plan are entirely webapp changes; no server modifications are required.

---

## A — Server Endpoints Returning 400 (Not Implemented)

These CSAPI navigation endpoints are defined in the spec but not implemented by the OSH server. The webapp currently attempts them and silently fails.

| ID  | Endpoint                          | Expected Relation           | Impact                                     |
|-----|-----------------------------------|-----------------------------|---------------------------------------------|
| A1  | `GET /systems/{id}/deployments`   | System → Deployments        | Deployment count always 0 on system diagram |
| A2  | `GET /systems/{id}/procedures`    | System → Procedures         | Procedure count always 0 on system diagram  |
| A3  | `GET /deployments/{id}/systems`   | Deployment → Systems        | Systems count always 0 on deployment diagram|
| A4  | `GET /procedures/{id}/systems`    | Procedure → Systems         | Systems count always 0 on procedure diagram |
| A5  | `GET /procedures/{id}/datastreams`| Procedure → Datastreams     | Datastreams count always 0 on procedure diagram |
| A6  | `GET /datastreams/{id}/systems`   | Datastream → parent System  | No reverse navigation from datastream       |

---

## B — Diagram Node Highlighting & Count Issues

| ID  | Issue                                           | Detail |
|-----|-------------------------------------------------|--------|
| B1  | Procedure node always shows count 0             | `systemKind@link` never present in GeoJSON or SML3; `typeOf` absent; no fallback exists |
| B2  | Deployment node shows count 0 for systems       | `resolveDeployedSystems()` follows `platform@link` but root deployments lack it entirely |
| B3  | Properties node always shows count 0            | `/properties` collection returns 0 items on this server |
| B4  | SamplingFeatures node always shows count 0      | No sampling features registered; `foi@id` absent from observations |
| B5  | Observations grandchild count may be inaccurate | `fetchCounts()` sums observation counts across all child datastreams; if any DS fetch fails the total is silently 0 |
| B6  | Root deployment aggregated system count is 0    | Root deployment (e.g. `04mg`) has neither `platform@link` nor `deployedSystems@link`; sub-deployments are not walked to aggregate |

---

## C — Navigation Link Issues

| ID  | Issue                                              | Detail |
|-----|----------------------------------------------------|--------|
| C1  | Deployment → Systems click is unconditionally blocked | `navigateToType('systems')` in the deployment context hits an early `return` that was intended to guard empty clusters but fires always |
| C2  | Systems → Deployments click produces empty list    | Falls back to `tryLinkFallback()` which scans all deployments for `platform@link` matching current system; works in theory but `platform@link.href` is a bare ID (see D4) |
| C3  | Procedure resolution never triggers                | Both `systemKind@link` (GeoJSON) and `typeOf` (SML3) are absent; `tryLinkFallback()` procedure branch is unreachable |
| C4  | Parent-link back-navigation from Observations      | Observations contain `datastream@id` but not `system@id` or `foi@id`; navigating to parent system requires an extra hop through the datastream |

---

## D — Edge / Relationship Model Issues

| ID  | Issue                                                 | Detail |
|-----|-------------------------------------------------------|--------|
| D1  | `RELATED_RESOURCES` lists `procedures` under systems  | Server returns 400; no client-side fallback exists |
| D2  | `RELATED_RESOURCES` lists `systems` under procedures   | Server returns 400; no client-side fallback exists |
| D3  | `RELATED_RESOURCES` lists `systems` under deployments  | Server returns 400; `resolveDeployedSystems()` provides partial coverage via `@link` fields |
| D4  | `platform@link.href` is a bare ID, not a URL path     | OSH returns `{"href": "0520", ...}` instead of `"/systems/0520"`; `normalizeLinkHref()` does not handle this case — all URL construction from this value fails silently |

---

## Summary by Resource Type

| Viewing…          | Working Links         | Broken / Always 0         | Notes                                |
|-------------------|-----------------------|---------------------------|--------------------------------------|
| **System**        | subsystems, datastreams, controlStreams, samplingFeatures (structure only) | deployments (A1), procedures (A2) | Core child relations work            |
| **Deployment**    | subdeployments        | systems (A3, C1, D4)      | `platform@link` bare-ID issue blocks resolution |
| **Procedure**     | —                     | systems (A4), datastreams (A5) | Entire node is unreachable           |
| **Datastream**    | observations          | parent system (A6)        | Forward navigation works             |
| **ControlStream** | commands              | —                         | Works as expected                    |
| **Observation**   | —                     | parent system (C4)        | Only `datastream@id` present         |
| **Properties**    | —                     | all (B3)                  | Collection empty on server           |
| **SamplingFeatures** | —                  | all (B4)                  | None registered; `foi@id` absent     |

---

## Server Field Availability (Reference)

Verified via live API calls — these findings drive which client-side fallbacks are feasible.

| Field / Link             | Present? | Location                   | Value Example          |
|--------------------------|----------|----------------------------|------------------------|
| `systemKind@link`        | ❌ No    | System GeoJSON properties  | —                      |
| `typeOf`                 | ❌ No    | System SML3                | —                      |
| `platform@link`          | ✅ Yes*  | Deployment (leaf only)     | `{"href": "0520", …}`  |
| `deployedSystems@link`   | ❌ No    | Deployment                 | —                      |
| `deployedSystemUIDs`     | ❌ No    | Deployment                 | —                      |
| `datastream@id`          | ✅ Yes   | Observation                | `"04qg"`               |
| `system@id`              | ❌ No    | Observation                | —                      |
| `foi@id`                 | ❌ No    | Observation                | —                      |

\* Only on leaf/station deployments, not on root or group deployments.
