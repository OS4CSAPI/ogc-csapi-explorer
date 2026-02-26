# CSAPI Parsing Coverage Audit Report

**Date:** February 19, 2026  
**Phase:** 5 — Pre-Implementation Gap Analysis  
**Scope:** Full inventory of all parseable formats defined by OGC Connected Systems API (Parts 1 & 2), SensorML 3.0, and SWE Common 3.0 — mapped against implemented parse functions in `src/ogc-api/csapi/formats/`.

---

## Purpose

This report answers one question: **Does our codebase parse everything the spec says it should?**

The claim is that we support parsing all resources and formats within the supported scope (CSAPI Part 1 + Part 2, SensorML 3.0, SWE Common 3.0). This audit validates that claim by mapping every model interface to its corresponding parse function and identifying all gaps.

---

## Model Inventory

### Part 1 Resource Types (GeoJSON Features)

| #   | Interface         | Category | GeoJSON Feature?                |
| --- | ----------------- | -------- | ------------------------------- |
| 1   | `System`          | Part 1   | Yes                             |
| 2   | `Deployment`      | Part 1   | Yes                             |
| 3   | `Procedure`       | Part 1   | Yes (geometry always null)      |
| 4   | `SamplingFeature` | Part 1   | Yes                             |
| 5   | `Property`        | Part 1   | **No** — flat SWE Common object |

### Part 2 Resource Types (Flat JSON)

| #   | Interface       | Category | GeoJSON Feature? |
| --- | --------------- | -------- | ---------------- |
| 6   | `Datastream`    | Part 2   | No               |
| 7   | `Observation`   | Part 2   | No               |
| 8   | `ControlStream` | Part 2   | No               |
| 9   | `Command`       | Part 2   | No               |
| 10  | `CommandStatus` | Part 2   | No               |

### Collection/Envelope Types

| #   | Type                        | Wraps                                |
| --- | --------------------------- | ------------------------------------ |
| 11  | `SystemCollection`          | `FeatureCollection<System>`          |
| 12  | `DeploymentCollection`      | `FeatureCollection<Deployment>`      |
| 13  | `ProcedureCollection`       | `FeatureCollection<Procedure>`       |
| 14  | `SamplingFeatureCollection` | `FeatureCollection<SamplingFeature>` |
| 15  | `PropertyCollection`        | `ItemCollection<Property>`           |
| 16  | `DatastreamCollection`      | `ItemCollection<Datastream>`         |
| 17  | `ObservationCollection`     | `ItemCollection<Observation>`        |
| 18  | `ControlStreamCollection`   | `ItemCollection<ControlStream>`      |
| 19  | `CommandCollection`         | `ItemCollection<Command>`            |
| 20  | `CommandStatusCollection`   | `ItemCollection<CommandStatus>`      |

### SensorML 3.0 Process Types

| #   | Type                | Description                                   |
| --- | ------------------- | --------------------------------------------- |
| 21  | `PhysicalSystem`    | System with components, connections, position |
| 22  | `PhysicalComponent` | Leaf-level physical process with method       |
| 23  | `SimpleProcess`     | Non-physical process with method              |
| 24  | `AggregateProcess`  | Process composed of sub-processes             |

### SWE Common 3.0 Component Types (16 total)

| #   | Type            |
| --- | --------------- |
| 25  | `Quantity`      |
| 26  | `Count`         |
| 27  | `Boolean`       |
| 28  | `Text`          |
| 29  | `Time`          |
| 30  | `Category`      |
| 31  | `QuantityRange` |
| 32  | `CountRange`    |
| 33  | `TimeRange`     |
| 34  | `CategoryRange` |
| 35  | `DataRecord`    |
| 36  | `DataArray`     |
| 37  | `Vector`        |
| 38  | `Matrix`        |
| 39  | `DataChoice`    |
| 40  | `Geometry`      |

---

## Existing Parse Functions

### `formats/geojson.ts` — Part 1 GeoJSON Feature Parsing

| Function                        | Output                                                 |
| ------------------------------- | ------------------------------------------------------ |
| `extractCSAPIFeature(feature)`  | `System \| Deployment \| Procedure \| SamplingFeature` |
| `isCSAPIFeature(feature)`       | `boolean` (recognition check)                          |
| `getCSAPIResourceType(feature)` | Resource type string or null                           |
| `parseValidTime(value)`         | `TimeInterval \| undefined`                            |
| `isValidUri(value)`             | `boolean`                                              |

### `formats/response.ts` — Collection Envelope Normalization

| Function                           | Output                                                                      |
| ---------------------------------- | --------------------------------------------------------------------------- |
| `parseCollectionResponse<T>(body)` | `CollectionResponse<T>` — handles both `{features}` and `{items}` envelopes |

### `formats/classification.ts` — Classification

| Function                          | Output                             |
| --------------------------------- | ---------------------------------- |
| `classifyFeature(feature, hint?)` | Resource type string               |
| `inferResourceTypeFromPath(url)`  | Resource type string from URL path |

### `formats/constants.ts` — Content Types

| Function                                  | Output                     |
| ----------------------------------------- | -------------------------- |
| `getContentTypeForResource(resourceType)` | Content-Type header string |

### `formats/sensorml/` — SensorML 3.0 Parsers

| Function                                       | File                   | Output                                             |
| ---------------------------------------------- | ---------------------- | -------------------------------------------------- |
| `parseSensorML30(json)`                        | `parser.ts`            | `SensorMLProcess` (discriminated union of 4 types) |
| `parsePhysicalSystem(json)`                    | `physical-system.ts`   | `PhysicalSystem`                                   |
| `parsePhysicalComponent(json)`                 | `physical-system.ts`   | `PhysicalComponent`                                |
| `parseSimpleProcess(json)`                     | `simple-process.ts`    | `SimpleProcess`                                    |
| `parseAggregateProcess(json)`                  | `aggregate-process.ts` | `AggregateProcess`                                 |
| `parseCapabilityList(json)`                    | `parser.ts`            | `CapabilityList`                                   |
| `parseCharacteristicList(json)`                | `parser.ts`            | `CharacteristicList`                               |
| `parseDescribedObjectProperties(json)`         | `parser.ts`            | `Partial<DescribedObject>`                         |
| `parseAbstractProcessProperties(json)`         | `parser.ts`            | `Partial<AbstractProcess>`                         |
| `parseAbstractPhysicalProcessProperties(json)` | `parser.ts`            | `Partial<AbstractPhysicalProcess>`                 |
| `parsePosition(value)`                         | `physical-system.ts`   | `Position` (8 variants)                            |
| `parseComponentEntry(value, i)`                | `physical-system.ts`   | `ComponentEntry`                                   |
| `parseComponentList(value)`                    | `physical-system.ts`   | `ComponentList`                                    |
| `parseConnectionList(value)`                   | `physical-system.ts`   | `ConnectionList`                                   |

### `formats/swecommon/` — SWE Common 3.0 Parsers

| Function                               | File             | Output                                                                                       |
| -------------------------------------- | ---------------- | -------------------------------------------------------------------------------------------- |
| `parseSWEComponent(json)`              | `parser.ts`      | Any of 16 SWE Common types                                                                   |
| `parseQuantity(json)`                  | `components.ts`  | `SweQuantity`                                                                                |
| `parseCount(json)`                     | `components.ts`  | `SweCount`                                                                                   |
| `parseBoolean(json)`                   | `components.ts`  | `SweBoolean`                                                                                 |
| `parseText(json)`                      | `components.ts`  | `SweText`                                                                                    |
| `parseTime(json)`                      | `components.ts`  | `SweTime`                                                                                    |
| `parseCategory(json)`                  | `components.ts`  | `SweCategory`                                                                                |
| `parseQuantityRange(json)`             | `components.ts`  | `SweQuantityRange`                                                                           |
| `parseCountRange(json)`                | `components.ts`  | `SweCountRange`                                                                              |
| `parseTimeRange(json)`                 | `components.ts`  | `SweTimeRange`                                                                               |
| `parseCategoryRange(json)`             | `components.ts`  | `SweCategoryRange`                                                                           |
| `parseSimpleComponent(json)`           | `components.ts`  | Discriminated union of above 10                                                              |
| `parseDataRecord(json)`                | `data-record.ts` | `DataRecord`                                                                                 |
| `parseDataArray(json)`                 | `data-array.ts`  | `DataArray`                                                                                  |
| `parseVector(json)`                    | `parser.ts`      | `Vector`                                                                                     |
| `parseMatrix(json)`                    | `parser.ts`      | `Matrix`                                                                                     |
| `parseDataChoice(json)`                | `parser.ts`      | `DataChoice`                                                                                 |
| `parseGeometry(json)`                  | `parser.ts`      | `SweGeometry`                                                                                |
| `parseEncoding(json)`                  | `data-array.ts`  | `DataEncoding` (JSON, Text, Binary; XML recognized as pass-through only — not in CSAPI spec) |
| `validateAgainstSchema(value, schema)` | `parser.ts`      | `ValidationResult`                                                                           |
| `parseUnitOfMeasure(json)`             | `components.ts`  | `UnitOfMeasure`                                                                              |
| `parseAllowedValues(json)`             | `components.ts`  | `AllowedValues`                                                                              |
| `parseAllowedTokens(json)`             | `components.ts`  | `AllowedTokens`                                                                              |
| `parseAllowedTimes(json)`              | `components.ts`  | `AllowedTimes`                                                                               |
| `parseNilValues(json)`                 | `components.ts`  | `NilValue[]`                                                                                 |
| `parseQuality(json)`                   | `components.ts`  | `AnySimpleComponent[]`                                                                       |

---

## Coverage Map

### Fully Covered

| Area                    | Coverage                  | Notes                                                                                        |
| ----------------------- | ------------------------- | -------------------------------------------------------------------------------------------- |
| Part 1 GeoJSON Features | 4/4 types                 | System, Deployment, Procedure, SamplingFeature via `extractCSAPIFeature()`                   |
| SensorML 3.0            | 4/4 process types         | PhysicalSystem, PhysicalComponent, SimpleProcess, AggregateProcess                           |
| SWE Common 3.0          | 16/16 component types     | All simple components, records, arrays, vectors, matrices, choices, geometry                 |
| SWE Common Encodings    | 3/3 CSAPI-specified types | JSON, Text, Binary. XMLEncoding has a defensive pass-through only (not in OGC 24-014 scope). |
| Collection Envelopes    | Both shapes               | `FeatureCollection` and `{items}`                                                            |
| URL Building            | All resource types        | Including subsystems, subdeployments, recursive queries                                      |

### Missing — No Parser Exists

| #   | Missing Parser                       | Model Interface Exists | What It Would Do                                                                    |
| --- | ------------------------------------ | ---------------------- | ----------------------------------------------------------------------------------- |
| 1   | `parseProperty()`                    | Yes — `Property`       | Validate/transform Property JSON; parse `validTime` → `TimeInterval`                |
| 2   | `parseDatastream()`                  | Yes — `Datastream`     | Parse `phenomenonTime`/`resultTime` → `TimeInterval`; validate schema refs          |
| 3   | `parseObservation()`                 | Yes — `Observation`    | Parse time fields; handle `result` with SWE Common schema-aware parsing             |
| 4   | `parseControlStream()`               | Yes — `ControlStream`  | Parse time fields; validate control schema refs                                     |
| 5   | `parseCommand()`                     | Yes — `Command`        | Parse `executionTime`; handle command parameters                                    |
| 6   | `parseCommandStatus()`               | Yes — `CommandStatus`  | Parse `executionTime`, `statusCode`, `command@id` cross-reference                   |
| 7   | `parseDatastreamSchemaResponse()`    | No interface yet       | Parse `{ obsFormat, resultSchema }` wrapper from `/datastreams/{id}/schema`         |
| 8   | `parseControlStreamSchemaResponse()` | No interface yet       | Parse `{ commandFormat, commandSchema }` wrapper from `/controlstreams/{id}/schema` |

**Current behavior:** `parseCollectionResponse<Datastream>()` etc. extracts items from collection envelopes but passes through inner objects as raw untyped JSON. Time fields that should be `TimeInterval` objects remain raw `[start, end]` arrays. No field validation occurs.

### Incomplete — Partial Implementation

| #   | Gap                                      | Location                                       | Detail                                                                                                                                                                                                                                                                    |
| --- | ---------------------------------------- | ---------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 9   | SensorML recursive sub-parser delegation | `physical-system.ts` `parseComponentEntry()`   | Only recursively parses nested `PhysicalSystem` inline components. `SimpleProcess`, `AggregateProcess`, and `PhysicalComponent` components within a PhysicalSystem are returned as raw JSON. The fix is to call `parseSensorML30()` which already dispatches all 4 types. |
| 10  | Same gap in AggregateProcess             | `aggregate-process.ts` `parseComponentEntry()` | Only recursively parses nested `AggregateProcess`. Same fix — delegate to `parseSensorML30()`.                                                                                                                                                                            |

---

## Subsystems and Subdeployments

### Subsystems (SensorML `components` within PhysicalSystem)

**Status: Partially covered.**

- `parseComponentEntry()` in `physical-system.ts` recursively parses nested `PhysicalSystem` components (subsystems that are themselves PhysicalSystems).
- Other inline sub-process types (`SimpleProcess`, `AggregateProcess`, `PhysicalComponent`) embedded as components within a PhysicalSystem are **not parsed** — they are passed through as raw JSON.
- External link components (components referenced by URL rather than inline) are correctly identified and returned as `Link` type entries.
- The code comment at line 106-108 explicitly acknowledges this: _"Full sub-parser delegation (SimpleProcess, AggregateProcess, PhysicalComponent) is coordinated by the main parser (Issue #22)."_

### Subdeployments

**Status: Covered (not a parser-level concern).**

Subdeployments are navigated via URL path (e.g., `/deployments/{id}/subdeployments`), not embedded in JSON documents. The URL builder has `getDeploymentSubdeployments()` and the query options support `parentDeploymentId` and `recursive` parameters. Individual Deployment resources are flat GeoJSON Features parsed by `extractCSAPIFeature()`.

---

## Alignment with ROADMAP

Per `docs/planning/ROADMAP.md`, Phase 3 (Format Handling) defined the following scope:

| ROADMAP Task                                               | Status |
| ---------------------------------------------------------- | ------ |
| GeoJSON handler extensions                                 | Done   |
| Format detector extensions                                 | Done   |
| SWE Common types + parsers (all 16 components + encodings) | Done   |
| SensorML types + parsers (all 4 process types)             | Done   |
| Collection envelope normalization                          | Done   |
| Format constants and index                                 | Done   |

**Phase 3 is complete per its defined scope.** The ROADMAP did not explicitly list Part 2 resource parsers (Datastream, Observation, ControlStream, Command, CommandStatus, Property) as Phase 3 tasks. These were implicitly deferred — the assumption was that flat JSON objects would be consumed via generic `parseCollectionResponse<T>()` without dedicated transformation.

That assumption is incorrect because:

1. Time fields (`phenomenonTime`, `resultTime`, `executionTime`) need parsing into `TimeInterval` objects
2. Cross-reference fields (`foi@id`, `system@link`, `controlstream@id`, `command@id`) use abbreviated notation that needs expansion
3. The `result` field on Observation is `unknown` and benefits from SWE Common schema-aware validation (which already exists as `validateAgainstSchema()`)
4. No field validation means typos or server inconsistencies pass through silently

---

## Summary

| Category                                | Implemented | Missing        | Coverage |
| --------------------------------------- | ----------- | -------------- | -------- |
| Part 1 GeoJSON resources                | 4           | 0              | 100%     |
| Part 1 non-GeoJSON resources (Property) | 0           | 1              | 0%       |
| Part 2 resources                        | 0           | 5              | 0%       |
| Schema response wrappers                | 0           | 2              | 0%       |
| SensorML 3.0 process types              | 4           | 0              | 100%     |
| SensorML recursive delegation           | Partial     | 2 fixes needed | ~50%     |
| SWE Common 3.0 components               | 16          | 0              | 100%     |
| SWE Common encodings (CSAPI-specified)  | 3           | 0              | 100%     |
| Collection envelopes                    | 2 shapes    | 0              | 100%     |
| URL building                            | All types   | 0              | 100%     |

**Total gaps: 6 missing resource parsers + 2 missing schema parsers + 1 recursive delegation fix (in 2 files) = 9 items.**

The claim that we parse everything from all supported formats is **not yet met**. The SensorML and SWE Common layers are complete. The Part 1 GeoJSON layer is complete. The Part 2 resource layer and the Property resource have interfaces defined but no parse functions — inner objects come through as raw untyped JSON.
