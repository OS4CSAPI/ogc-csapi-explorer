# CSAPI Export Inventory — Issue #119

**Task:** P6 Task 4a — Audit and Build CSAPI Export Inventory
**Date:** 2026-02-24
**Branch:** `phase-6`
**Source of truth:** `src/index.ts` lines 45–227 (post-Commit 14 formatting)
**Deliverable:** Complete symbol-to-source mapping organized by the 6 barrel file sections

---

## Summary

| Section | Source Module        | Values | Types   | Total   |
| ------- | -------------------- | ------ | ------- | ------- |
| 1       | `./factory.js`       | 0\*    | 0       | 0\*     |
| 2       | `./url_builder.js`   | 1      | 0       | 1       |
| 3       | `./model.js`         | 3      | 0       | 3       |
| 4       | `./model.js`         | 0      | 42      | 42      |
| 5       | `./formats/index.js` | 27     | 0       | 27      |
| 6       | `./formats/index.js` | 0      | 98      | 98      |
| **All** |                      | **31** | **140** | **171** |

\*Section 1 will contain 1 value (`createCSAPIBuilder`) after Task 5 creates the factory function. It is not currently exported from `src/index.ts`.

---

## Section 1 — Factory Function (`./factory.js`)

> _Will be created in Task 5. Not currently in `src/index.ts`._

```
(none — Task 5 deliverable)
```

Expected after Task 5:

- `createCSAPIBuilder` [value]

---

## Section 2 — Query Builder (`./url_builder.js`)

**1 value.**

| #   | Symbol              | Kind  | Export Form                               | Source Line          |
| --- | ------------------- | ----- | ----------------------------------------- | -------------------- |
| 1   | `CSAPIQueryBuilder` | value | `export { default as CSAPIQueryBuilder }` | `url_builder.ts:116` |

**Note:** `CSAPIQueryBuilder` is a `default export` in its source module. The barrel re-exports it as a **named export** using the `{ default as CSAPIQueryBuilder }` pattern, matching the current `src/index.ts` line 45.

---

## Section 3 — Model Values (`./model.js`)

**3 values.**

| #   | Symbol               | Kind  | Export Form      | Source Line   |
| --- | -------------------- | ----- | ---------------- | ------------- |
| 1   | `CSAPIResourceTypes` | value | `export { ... }` | `model.ts:35` |
| 2   | `CommandStatusCodes` | value | `export { ... }` | `model.ts:58` |
| 3   | `SystemTypeUris`     | value | `export { ... }` | `model.ts:81` |

All three are `const` arrays (tuple literals) that double as both runtime values and type sources via `typeof` indexed access.

---

## Section 4 — Model Types (`./model.js`)

**42 types.** Uses `export type { ... }` — two separate blocks.

### Block A — Primary model types (40 types)

| #   | Symbol                                   | Kind | Source Line    | Notes                                                       |
| --- | ---------------------------------------- | ---- | -------------- | ----------------------------------------------------------- |
| 1   | `CSAPIResourceType`                      | type | `model.ts:48`  | Derived from `CSAPIResourceTypes` array                     |
| 2   | `CommandStatusCode`                      | type | `model.ts:71`  | Derived from `CommandStatusCodes` array                     |
| 3   | `SystemTypeUri`                          | type | `model.ts:90`  | Derived from `SystemTypeUris` array                         |
| 4   | `TimeInterval`                           | type | `model.ts:100` | Interface                                                   |
| 5   | `ResourceLink`                           | type | `model.ts:109` | Type alias for `OgcApiDocumentLink`                         |
| 6   | `CSAPIResourceRef`                       | type | `model.ts:121` | Interface                                                   |
| 7   | `CsapiDateTimeParameter`                 | type | `model.ts:20`  | Type alias                                                  |
| 8   | `QueryOptions` → **`CSAPIQueryOptions`** | type | `model.ts:145` | **Renamed on export** (`QueryOptions as CSAPIQueryOptions`) |
| 9   | `SystemQueryOptions`                     | type | `model.ts:172` | Interface extends `QueryOptions`                            |
| 10  | `DeploymentQueryOptions`                 | type | `model.ts:191` | Interface extends `QueryOptions`                            |
| 11  | `ProcedureQueryOptions`                  | type | `model.ts:204` | Type alias = `QueryOptions`                                 |
| 12  | `SamplingFeatureQueryOptions`            | type | `model.ts:210` | Type alias = `QueryOptions`                                 |
| 13  | `PropertyQueryOptions`                   | type | `model.ts:216` | Interface extends `QueryOptions`                            |
| 14  | `DatastreamQueryOptions`                 | type | `model.ts:227` | Interface extends `QueryOptions`                            |
| 15  | `ObservationQueryOptions`                | type | `model.ts:247` | Interface extends `QueryOptions`                            |
| 16  | `ControlStreamQueryOptions`              | type | `model.ts:263` | Interface extends `QueryOptions`                            |
| 17  | `CommandQueryOptions`                    | type | `model.ts:289` | Interface extends `QueryOptions`                            |
| 18  | `CommandStatusQueryOptions`              | type | `model.ts:313` | Interface extends `QueryOptions`                            |
| 19  | `System`                                 | type | `model.ts:332` | Interface — Part 1 resource                                 |
| 20  | `Deployment`                             | type | `model.ts:380` | Interface — Part 1 resource                                 |
| 21  | `Procedure`                              | type | `model.ts:434` | Interface — Part 1 resource                                 |
| 22  | `SamplingFeature`                        | type | `model.ts:464` | Interface — Part 1 resource                                 |
| 23  | `Property`                               | type | `model.ts:499` | Interface — Part 1 resource                                 |
| 24  | `Datastream`                             | type | `model.ts:532` | Interface — Part 2 resource                                 |
| 25  | `Observation`                            | type | `model.ts:573` | Interface — Part 2 resource                                 |
| 26  | `ControlStream`                          | type | `model.ts:604` | Interface — Part 2 resource                                 |
| 27  | `Command`                                | type | `model.ts:642` | Interface — Part 2 resource                                 |
| 28  | `CommandStatus`                          | type | `model.ts:669` | Interface — Part 2 resource                                 |
| 29  | `FeatureCollection`                      | type | `model.ts:747` | Generic interface `<T>`                                     |
| 30  | `ItemCollection`                         | type | `model.ts:760` | Generic interface `<T>`                                     |
| 31  | `SystemCollection`                       | type | `model.ts:769` | Type alias = `FeatureCollection<System>`                    |
| 32  | `DeploymentCollection`                   | type | `model.ts:771` | Type alias                                                  |
| 33  | `ProcedureCollection`                    | type | `model.ts:773` | Type alias                                                  |
| 34  | `SamplingFeatureCollection`              | type | `model.ts:775` | Type alias                                                  |
| 35  | `PropertyCollection`                     | type | `model.ts:777` | Type alias = `ItemCollection<Property>`                     |
| 36  | `DatastreamCollection`                   | type | `model.ts:779` | Type alias                                                  |
| 37  | `ObservationCollection`                  | type | `model.ts:781` | Type alias                                                  |
| 38  | `ControlStreamCollection`                | type | `model.ts:783` | Type alias                                                  |
| 39  | `CommandCollection`                      | type | `model.ts:785` | Type alias                                                  |
| 40  | `CommandStatusCollection`                | type | `model.ts:787` | Type alias                                                  |

### Block B — Schema response types (2 types)

| #   | Symbol                        | Kind | Source Line    |
| --- | ----------------------------- | ---- | -------------- |
| 41  | `DatastreamSchemaResponse`    | type | `model.ts:704` |
| 42  | `ControlStreamSchemaResponse` | type | `model.ts:730` |

**Note:** These are exported in a separate `export type { ... }` statement in `src/index.ts` (lines 96–98). The barrel file may merge them into Block A's single `export type` statement.

---

## Section 5 — Format Handler Values (`./formats/index.js`)

**27 values.** Uses `export { ... }`.

| #   | Symbol                             | Kind  | Original Source (via `formats/index.ts`) |
| --- | ---------------------------------- | ----- | ---------------------------------------- |
| 1   | `SOSA_NS`                          | value | `constants.ts`                           |
| 2   | `SSN_NS`                           | value | `constants.ts`                           |
| 3   | `SENSORML_NS`                      | value | `geojson.ts`                             |
| 4   | `isCSAPIFeature`                   | value | `geojson.ts`                             |
| 5   | `getCSAPIResourceType`             | value | `geojson.ts`                             |
| 6   | `parseValidTime`                   | value | `geojson.ts`                             |
| 7   | `isValidUri`                       | value | `geojson.ts`                             |
| 8   | `extractCSAPIFeature`              | value | `geojson.ts`                             |
| 9   | `parseSensorML30`                  | value | `sensorml/index.ts`                      |
| 10  | `parseSWEComponent`                | value | `swecommon/index.ts`                     |
| 11  | `parseVector`                      | value | `swecommon/index.ts`                     |
| 12  | `parseMatrix`                      | value | `swecommon/index.ts`                     |
| 13  | `parseDataChoice`                  | value | `swecommon/index.ts`                     |
| 14  | `parseGeometry`                    | value | `swecommon/index.ts`                     |
| 15  | `detectEncoding`                   | value | `swecommon/index.ts`                     |
| 16  | `validateAgainstSchema`            | value | `swecommon/index.ts`                     |
| 17  | `CSAPI_CONTENT_TYPES`              | value | `constants.ts`                           |
| 18  | `getContentTypeForResource`        | value | `constants.ts`                           |
| 19  | `parseProperty`                    | value | `property.ts`                            |
| 20  | `parseDatastream`                  | value | `part2.ts`                               |
| 21  | `parseObservation`                 | value | `part2.ts`                               |
| 22  | `parseControlStream`               | value | `part2.ts`                               |
| 23  | `parseCommand`                     | value | `part2.ts`                               |
| 24  | `parseCommandStatus`               | value | `part2.ts`                               |
| 25  | `normalizeStatusCode`              | value | `part2.ts`                               |
| 26  | `parseDatastreamSchemaResponse`    | value | `schema-response.ts`                     |
| 27  | `parseControlStreamSchemaResponse` | value | `schema-response.ts`                     |

**Barrel import path:** All 27 values are re-exported through `./formats/index.js`. The barrel imports from `./formats/index.js` only — it does NOT import from individual sub-modules.

---

## Section 6 — Format Handler Types (`./formats/index.js`)

**98 types.** Uses `export type { ... }`.

### 6a — GeoJSON Types (1 type)

| #   | Symbol                  | Kind | Original Source |
| --- | ----------------------- | ---- | --------------- |
| 1   | `CSAPIResourceTypeName` | type | `geojson.ts`    |

### 6b — SensorML 3.0 Types (49 types)

| #   | Symbol                              | Kind | Notes                                                  |
| --- | ----------------------------------- | ---- | ------------------------------------------------------ |
| 2   | `SensorMLProcess`                   | type | Discriminated union                                    |
| 3   | `SensorMLProcessType`               | type | Literal union                                          |
| 4   | `PhysicalSystem`                    | type | Concrete process                                       |
| 5   | `PhysicalComponent`                 | type | Concrete process                                       |
| 6   | `SimpleProcess`                     | type | Concrete process                                       |
| 7   | `AggregateProcess`                  | type | Concrete process                                       |
| 8   | `DescribedObject`                   | type | Base interface                                         |
| 9   | `AbstractProcess`                   | type | Abstract interface                                     |
| 10  | `AbstractPhysicalProcess`           | type | Abstract interface                                     |
| 11  | `CapabilityList`                    | type |                                                        |
| 12  | `CharacteristicList`                | type |                                                        |
| 13  | `Term`                              | type |                                                        |
| 14  | `ComponentList`                     | type |                                                        |
| 15  | `ComponentEntry`                    | type |                                                        |
| 16  | `ConnectionList`                    | type |                                                        |
| 17  | `Connection`                        | type |                                                        |
| 18  | `Settings`                          | type |                                                        |
| 19  | `Link` → **`SensorMLLink`**         | type | **Renamed on export** (`Link as SensorMLLink`)         |
| 20  | `ResponsibleParty`                  | type |                                                        |
| 21  | `InputList`                         | type |                                                        |
| 22  | `OutputList`                        | type |                                                        |
| 23  | `ParameterList`                     | type |                                                        |
| 24  | `IOComponentChoice`                 | type |                                                        |
| 25  | `Mode`                              | type |                                                        |
| 26  | `Event`                             | type |                                                        |
| 27  | `Position`                          | type |                                                        |
| 28  | `Pose`                              | type |                                                        |
| 29  | `GeoJsonPoint`                      | type |                                                        |
| 30  | `Document` → **`SensorMLDocument`** | type | **Renamed on export** (`Document as SensorMLDocument`) |
| 31  | `FeatureList`                       | type |                                                        |
| 32  | `LegalConstraint`                   | type |                                                        |
| 33  | `SecurityConstraint`                | type |                                                        |
| 34  | `ContactInfo`                       | type |                                                        |
| 35  | `ContactLink`                       | type |                                                        |
| 36  | `ObservableProperty`                | type |                                                        |
| 37  | `AnyProperty`                       | type |                                                        |
| 38  | `ProcessMethod`                     | type |                                                        |
| 39  | `SpatialFrame`                      | type |                                                        |
| 40  | `TemporalFrame`                     | type |                                                        |
| 41  | `TimePeriod`                        | type |                                                        |
| 42  | `TimeInstant`                       | type |                                                        |
| 43  | `TimeInstantOrPeriod`               | type |                                                        |
| 44  | `ComponentLink`                     | type |                                                        |
| 45  | `SettingValue`                      | type |                                                        |
| 46  | `SettingArrayValue`                 | type |                                                        |
| 47  | `SettingMode`                       | type |                                                        |
| 48  | `SetConstraint`                     | type |                                                        |
| 49  | `SettingStatus`                     | type |                                                        |
| 50  | `FrameAxis`                         | type |                                                        |

All 49 SensorML types originate in `sensorml/index.ts` re-exports.

### 6c — SWE Common 3.0 Types (48 types)

| #   | Symbol                      | Kind | Notes               |
| --- | --------------------------- | ---- | ------------------- |
| 51  | `AnyComponent`              | type | Discriminated union |
| 52  | `AnyScalarComponent`        | type | Union subset        |
| 53  | `AnySimpleComponent`        | type | Union subset        |
| 54  | `DataRecord`                | type |                     |
| 55  | `Vector`                    | type |                     |
| 56  | `Matrix`                    | type |                     |
| 57  | `DataChoice`                | type |                     |
| 58  | `DataArray`                 | type |                     |
| 59  | `SweGeometry`               | type |                     |
| 60  | `SweBoolean`                | type |                     |
| 61  | `SweCount`                  | type |                     |
| 62  | `SweQuantity`               | type |                     |
| 63  | `SweText`                   | type |                     |
| 64  | `SweCategory`               | type |                     |
| 65  | `SweTime`                   | type |                     |
| 66  | `SweCountRange`             | type |                     |
| 67  | `SweQuantityRange`          | type |                     |
| 68  | `SweTimeRange`              | type |                     |
| 69  | `SweCategoryRange`          | type |                     |
| 70  | `DataEncoding`              | type | Discriminated union |
| 71  | `TextEncoding`              | type |                     |
| 72  | `JSONEncoding`              | type |                     |
| 73  | `BinaryEncoding`            | type |                     |
| 74  | `XMLEncoding`               | type |                     |
| 75  | `ValidationResult`          | type |                     |
| 76  | `UnitOfMeasure`             | type |                     |
| 77  | `AllowedValues`             | type |                     |
| 78  | `AllowedTokens`             | type |                     |
| 79  | `AllowedTimes`              | type |                     |
| 80  | `DataField`                 | type |                     |
| 81  | `TypedDataField`            | type |                     |
| 82  | `ElementCount`              | type |                     |
| 83  | `EncodedValues`             | type |                     |
| 84  | `AssociationAttributeGroup` | type |                     |
| 85  | `NilValue`                  | type |                     |
| 86  | `NilValuesNumber`           | type |                     |
| 87  | `NilValuesInteger`          | type |                     |
| 88  | `NilValuesText`             | type |                     |
| 89  | `NilValuesTime`             | type |                     |
| 90  | `NumberOrSpecial`           | type |                     |
| 91  | `DateTimeNumberOrSpecial`   | type |                     |
| 92  | `GeometryConstraint`        | type |                     |
| 93  | `GeometryType`              | type |                     |
| 94  | `GeoJsonGeometry`           | type |                     |
| 95  | `BinaryMember`              | type |                     |
| 96  | `BinaryComponent`           | type |                     |
| 97  | `BinaryBlock`               | type |                     |
| 98  | `ValidationError`           | type |                     |

All 48 SWE Common types originate in `swecommon/index.ts` re-exports.

---

## Renamed Exports

Three symbols are renamed when exported from `src/index.ts`:

| Source Name    | Exported As         | Section | Reason                                               |
| -------------- | ------------------- | ------- | ---------------------------------------------------- |
| `QueryOptions` | `CSAPIQueryOptions` | 4       | Avoids collision with generic name in consumer scope |
| `Link`         | `SensorMLLink`      | 6b      | Avoids collision with DOM `Link` or other link types |
| `Document`     | `SensorMLDocument`  | 6b      | Avoids collision with DOM `Document`                 |

The barrel file MUST preserve these renames using the same `as` syntax.

---

## Internal Symbols — NOT Exported

These symbols are exported from their source modules (used internally within `csapi/`) but are NOT re-exported from `src/index.ts` and MUST NOT appear in the barrel file:

### From `helpers.ts`

| Symbol                    | Kind     | Purpose                                 |
| ------------------------- | -------- | --------------------------------------- |
| `formatDateTimeParameter` | function | Formats query parameter datetime values |
| `isValidResourceType`     | function | Type guard for resource type strings    |
| `assertValidResourceType` | function | Throws on invalid resource type         |
| `encodeResourceId`        | function | URL-encodes resource IDs                |
| `scanCsapiLinks`          | function | Parses CSAPI link arrays into Maps      |
| `validateLimit`           | function | Validates pagination limit parameter    |
| `validateBbox`            | function | Validates bounding box parameter        |

### From `formats/` sub-modules (exported from `formats/index.ts` but not from `src/index.ts`)

**Values (30):**

| Symbol                                   | Original Source      |
| ---------------------------------------- | -------------------- |
| `MEDIA_TYPE_GEOJSON`                     | `constants.ts`       |
| `MEDIA_TYPE_JSON`                        | `constants.ts`       |
| `MEDIA_TYPE_SENSORML_JSON`               | `constants.ts`       |
| `MEDIA_TYPE_SWE_JSON`                    | `constants.ts`       |
| `MEDIA_TYPE_SWE_TEXT`                    | `constants.ts`       |
| `MEDIA_TYPE_SWE_CSV`                     | `constants.ts`       |
| `MEDIA_TYPE_SWE_BINARY`                  | `constants.ts`       |
| `CSAPI_MEDIA_TYPES`                      | `constants.ts`       |
| `SOSA_PREFIX`                            | `constants.ts`       |
| `DeploymentTypeUris`                     | `constants.ts`       |
| `ProcedureTypeUris`                      | `constants.ts`       |
| `SamplingFeatureTypeUris`                | `constants.ts`       |
| `PropertyTypeUris`                       | `constants.ts`       |
| `ObservationTypeUris`                    | `constants.ts`       |
| `QUDT_NS`                                | `constants.ts`       |
| `UCUM_NS`                                | `constants.ts`       |
| `CF_NS`                                  | `constants.ts`       |
| `AssetTypes`                             | `constants.ts`       |
| `SensorMLParseError`                     | `sensorml/index.ts`  |
| `parseCapabilityList`                    | `sensorml/index.ts`  |
| `parseCharacteristicList`                | `sensorml/index.ts`  |
| `parseDescribedObjectProperties`         | `sensorml/index.ts`  |
| `parseAbstractProcessProperties`         | `sensorml/index.ts`  |
| `parseAbstractPhysicalProcessProperties` | `sensorml/index.ts`  |
| `parsePosition`                          | `sensorml/index.ts`  |
| `SENSORML_PROCESS_TYPES`                 | `sensorml/index.ts`  |
| `parseSimpleComponent`                   | `swecommon/index.ts` |
| `SweCommonParseError`                    | `swecommon/index.ts` |
| `parseUnitOfMeasure`                     | `swecommon/index.ts` |
| `parseAllowedValues`                     | `swecommon/index.ts` |
| `parseAllowedTokens`                     | `swecommon/index.ts` |
| `parseAllowedTimes`                      | `swecommon/index.ts` |
| `parseNilValues`                         | `swecommon/index.ts` |
| `parseQuality`                           | `swecommon/index.ts` |
| `parseDataRecord`                        | `swecommon/index.ts` |
| `parseDataArray`                         | `swecommon/index.ts` |
| `parseEncoding`                          | `swecommon/index.ts` |
| `decodeValues`                           | `swecommon/index.ts` |
| `parseCollectionResponse`                | `response.ts`        |
| `inferResourceTypeFromPath`              | `classification.ts`  |
| `classifyFeature`                        | `classification.ts`  |

**Types (14):**

| Symbol                    | Original Source      |
| ------------------------- | -------------------- |
| `CSAPIMediaType`          | `constants.ts`       |
| `DeploymentTypeUri`       | `constants.ts`       |
| `ProcedureTypeUri`        | `constants.ts`       |
| `SamplingFeatureTypeUri`  | `constants.ts`       |
| `PropertyTypeUri`         | `constants.ts`       |
| `ObservationTypeUri`      | `constants.ts`       |
| `AssetType`               | `constants.ts`       |
| `PathRef`                 | `sensorml/index.ts`  |
| `SweComponentType`        | `swecommon/index.ts` |
| `SweEncodingType`         | `swecommon/index.ts` |
| `AbstractSWE`             | `swecommon/index.ts` |
| `AbstractSweIdentifiable` | `swecommon/index.ts` |
| `AbstractDataComponent`   | `swecommon/index.ts` |
| `AbstractSimpleComponent` | `swecommon/index.ts` |
| `CollectionResponse`      | `response.ts`        |

### From `geojson.ts` (private function, no export keyword)

| Symbol             | Kind     | Purpose                                                                     |
| ------------------ | -------- | --------------------------------------------------------------------------- |
| `parseResourceRef` | function | Parses `@link` objects into `CSAPIResourceRef` — file-private (no `export`) |

---

## Verification Checklist

- [x] Every CSAPI symbol in `src/index.ts` lines 45–227 traced to its source module
- [x] Each symbol classified as value (31) or type (140)
- [x] Symbols organized into 6 barrel sections per Implementation Guide §6.1
- [x] Internal utilities identified as NOT exported (7 from `helpers.ts`, 44 from `formats/` sub-modules, 1 private in `geojson.ts`)
- [x] Total symbol count verified: **171 symbols** in `src/index.ts` lines 45–227 = 171 in inventory
- [x] Three renamed exports documented (`CSAPIQueryOptions`, `SensorMLLink`, `SensorMLDocument`)
- [x] Zero code changes — audit/research output only
- [x] Inventory ready for Task 4b (barrel file authoring)

---

## Import Path Summary for Barrel File

The barrel file (`src/ogc-api/csapi/index.ts`) will use these relative paths:

| Section | Barrel Import Path   | Symbol Count     |
| ------- | -------------------- | ---------------- |
| 1       | `./factory.js`       | 1 (after Task 5) |
| 2       | `./url_builder.js`   | 1                |
| 3       | `./model.js`         | 3                |
| 4       | `./model.js`         | 42               |
| 5       | `./formats/index.js` | 27               |
| 6       | `./formats/index.js` | 98               |
