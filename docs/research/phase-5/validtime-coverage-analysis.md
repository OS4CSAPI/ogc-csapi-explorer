# validTime Coverage Analysis

**Date:** February 19, 2026  
**Phase:** 5 — Pre-Implementation Gap Analysis  
**Scope:** Which CSAPI resource types have `validTime`, how it's currently handled, and what the Phase 5 parsers need to do.

---

## Purpose

During Phase 5 planning, the Parsing Coverage Audit (Gap #1) stated that `parseProperty()` should "parse `validTime` → `TimeInterval`." This analysis verifies that claim against the OGC spec and the codebase. Finding: **Property does not have `validTime`.** This document records the full `validTime` landscape across all CSAPI resource types to prevent similar assumptions in the remaining Phase 5 parser implementations.

---

## Spec Analysis: Which Resources Have `validTime`?

Source: [OGC API - Connected Systems Part 1 OpenAPI Specification](../standards/ogcapi-connectedsystems-1.bundled.oas31.yaml) and [OGC API - Connected Systems Part 2 (OGC 23-002)](https://docs.ogc.org/is/23-002/23-002.html).

### Part 1 Resources

| Resource        | Schema Name       | `validTime` in Spec? | Required?                                             | Spec Location                                                                                             |
| --------------- | ----------------- | -------------------- | ----------------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| System          | `system`          | **Yes**              | No (optional)                                         | OGC 23-001 §7, OpenAPI L1928                                                                              |
| Deployment      | `deployment`      | **Yes**              | Spec says yes (Table 10), but §8.7 Req 3B contradicts | OpenAPI L4567–L4571                                                                                       |
| Procedure       | `procedure`       | **No**               | —                                                     | Procedures describe methodologies; no temporal validity                                                   |
| SamplingFeature | `samplingFeature` | **Yes**              | No (optional)                                         | OpenAPI L4767                                                                                             |
| Property        | `DerivedProperty` | **No**               | —                                                     | Schema chain: `DerivedProperty` → `AbstractSweIdentifiable` → `AbstractSWE`. No `validTime` at any level. |

### Part 2 Resources

| Resource      | `validTime` in Spec? | Required?     | Notes                                                  |
| ------------- | -------------------- | ------------- | ------------------------------------------------------ |
| Datastream    | **Yes**              | No (optional) | Temporal extent of the datastream                      |
| Observation   | **No**               | —             | Has `phenomenonTime`, `resultTime` — different concept |
| ControlStream | **Yes**              | No (optional) | Temporal extent of the control stream                  |
| Command       | **No**               | —             | Has `issueTime`, `executionTime` — different concept   |
| CommandStatus | **No**               | —             | Has `executionTime`, `statusCode` — different concept  |

---

## Property: Why No `validTime`

The OGC spec defines Property using the `DerivedProperty` schema (OpenAPI L4790–L4828), which inherits from `AbstractSweIdentifiable` → `AbstractSWE`. The full field set:

- `uniqueId` (URI, required)
- `label` (required)
- `description`
- `baseProperty` (URI, required)
- `objectType` (URI)
- `statistic` (URI)
- `qualifiers` (array)
- `links`

No `validTime` appears at any level of the inheritance chain. This is conceptually correct: a Property defines _what can be observed_ (e.g., "air temperature") — it's a vocabulary entry, not a temporal resource. It doesn't start or stop being valid; it describes a measurement concept.

The Parsing Coverage Audit's Gap #1 description ("parse `validTime` → `TimeInterval`") was incorrect for Property. The `parseProperty()` implementation should validate/normalize the flat JSON fields listed above without any time field parsing.

---

## Procedure: Why No `validTime`

Procedures describe methodologies — how a measurement is taken, not when. The `procedure` schema inherits from `AbstractFeature` → `feature`, neither of which defines `validTime`. The existing `extractCSAPIFeature()` function correctly omits `validTime` from its Procedure output path. This is documented in the codebase:

> _"Procedures describe methodologies — they don't have temporal validity periods. `Procedure.properties` correctly omits `validTime`. This is not a modeling error; it reflects the spec."_

---

## Current Implementation: How `validTime` Is Handled

### TypeScript Interfaces (model.ts)

| Interface         | `validTime` Field      | Type           | Optional? |
| ----------------- | ---------------------- | -------------- | --------- |
| `System`          | `properties.validTime` | `TimeInterval` | Yes (`?`) |
| `Deployment`      | `properties.validTime` | `TimeInterval` | Yes (`?`) |
| `SamplingFeature` | `properties.validTime` | `TimeInterval` | Yes (`?`) |
| `Procedure`       | — (absent)             | —              | N/A       |
| `Property`        | — (absent)             | —              | N/A       |
| `Datastream`      | `validTime`            | `TimeInterval` | Yes (`?`) |
| `ControlStream`   | `validTime`            | `TimeInterval` | Yes (`?`) |
| `Observation`     | — (absent)             | —              | N/A       |
| `Command`         | — (absent)             | —              | N/A       |
| `CommandStatus`   | — (absent)             | —              | N/A       |

`TimeInterval` is defined as `{ start: Date; end?: Date }`.

### `parseValidTime()` Function (geojson.ts L274–L324)

Handles three input shapes:

1. **Null/undefined** → returns `undefined`
2. **Array format** (spec-canonical): `["2026-01-26T18:32:01.56Z", "now"]` → `{ start: Date, end: undefined }` (open-ended) or `{ start, end: Date }` (closed)
3. **Object format** (defensive): `{ start: Date|string, end?: Date|string }` → parsed `TimeInterval`
4. **Invalid input** → `undefined` (tolerant extraction)

The `"now"` sentinel string is treated as `end: undefined` (open-ended interval).

### `extractCSAPIFeature()` Usage

- Calls `parseValidTime(p.validTime)` once at the top for all GeoJSON features
- Includes `validTime` in output for **System**, **Deployment**, and **SamplingFeature** via conditional spread: `...(validTime !== undefined ? { validTime } : {})`
- **Does not** include `validTime` for **Procedure** (correct — Procedure has no `validTime`)
- **Does not** handle **Property** at all (correct — Property is not a GeoJSON Feature)

---

## Issue #77: Deployment `validTime` Made Optional

**Background:** During Smoke Test #18 (Finding F85), both live servers returned Deployments without valid `validTime` data:

- OpenSensorHub: `validTime` absent from response
- 52North: `validTime: null`

The original TypeScript interface declared `validTime: TimeInterval` (required). The GeoJSON parser used `validTime: validTime!` (non-null assertion), creating `validTime: undefined` that violated the type contract.

**Fix (Phase 3.17, commit `5161990`, Issue #77):**

1. Changed `Deployment.properties.validTime` from `TimeInterval` to `TimeInterval | undefined` (optional)
2. Changed GeoJSON parser from non-null assertion to conditional spread

**Rationale:** The spec contradicts itself — OGC 23-001 Table 10 lists `validTime` as "Required" for Deployments, but §8.7 Requirement 3B explicitly handles the case where `validTime` is null or not set. Real servers don't comply with the "Required" classification. Following Postel's Law (be liberal in what you accept), the interface was made optional.

---

## Phase 5 Implications: Which New Parsers Need `validTime`?

| New Parser                           | Needs `validTime` Parsing? | Reason                                                                                 |
| ------------------------------------ | -------------------------- | -------------------------------------------------------------------------------------- |
| `parseProperty()`                    | **No**                     | Property has no `validTime` in spec or interface                                       |
| `parseDatastream()`                  | **Yes**                    | Interface has `validTime?: TimeInterval` — parse from raw array/string                 |
| `parseObservation()`                 | **No**                     | Has `phenomenonTime`/`resultTime` instead (different fields, same `TimeInterval` type) |
| `parseControlStream()`               | **Yes**                    | Interface has `validTime?: TimeInterval` — parse from raw array/string                 |
| `parseCommand()`                     | **No**                     | Has `executionTime` instead (different field, same pattern)                            |
| `parseCommandStatus()`               | **No**                     | Has `executionTime` instead                                                            |
| `parseDatastreamSchemaResponse()`    | **No**                     | Schema wrapper — no temporal fields                                                    |
| `parseControlStreamSchemaResponse()` | **No**                     | Schema wrapper — no temporal fields                                                    |
| SensorML recursive delegation fix    | **No**                     | `validTime` on SensorML `DescribedObject` is already parsed by existing parsers        |

**All time-like fields** (`validTime`, `phenomenonTime`, `resultTime`, `executionTime`, `issueTime`) across all Part 2 resources arrive in the same format (ISO 8601 array or instant) and should be parsed with the same `parseValidTime()` function or an equivalent shared helper. The field _name_ varies but the _parsing logic_ is identical.

---

## Test Data Availability

| Resource        | Real `validTime` data from servers?              | Source                |
| --------------- | ------------------------------------------------ | --------------------- |
| System          | Yes — OSH returns `validTime` arrays             | ST#1–#19              |
| Deployment      | Partial — servers omit or null                   | ST#18 (F85), ST#19    |
| SamplingFeature | Yes — OSH returns `validTime`                    | ST#5                  |
| Property        | **No data exists** — both servers return 0 items | ST#6 (confirmed: N/A) |
| Datastream      | Yes — OSH returns `validTime` on datastreams     | ST#7                  |
| ControlStream   | Yes — OSH returns `validTime` on controlstreams  | ST#9                  |

Property test fixtures will need to be constructed from the spec definition alone, as no live server has ever returned Property resources.
