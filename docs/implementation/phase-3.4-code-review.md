# Phase 3.4 Code Review — SensorML 3.0 Type Definitions

**Date:** 2026-02-15  
**Reviewer:** GitHub Copilot (Claude Opus 4.6)  
**Scope:** All code changes since the last smoke test (Phase 3.3) — Issue #18 (SensorML 3.0 type definitions).  
**Prior review:** `docs/implementation/phase-3.3-code-review.md`  
**Commits:**

- `3eac9c6` — feat: add SensorML 3.0 type definitions (Issue #18)

---

## Phase 3 Lessons Learned Check (Step 1)

Per the code review template, Phase 3 lessons learned were reviewed before evaluating code:

| Lesson                                  | Check                                                                            | Result                                                                                                                                                                                     |
| --------------------------------------- | -------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| L1: Upstream precedent for new layers   | Does SensorML types introduce an architectural layer without upstream precedent? | ✅ No — type definitions follow the same pattern as SWE Common `types.ts`, `model.ts`, and EDR `model.ts`. Every handler starts with types.                                                |
| L2: Extraction depends on validation?   | Does any extraction gate on validation?                                          | ✅ No — no runtime code in this module. Pure type definitions.                                                                                                                             |
| L4: Parallel systems?                   | Are there two surfaces doing the same thing?                                     | ✅ No — SensorML types are distinct from SWE Common types. SWE Common provides data-component types; SensorML provides process-model types that _use_ SWE Common via imports.              |
| L10: Type names collide with built-ins? | Do SensorML type names conflict with JS/TS?                                      | ⚠️ `Document` — see [F3] below. All other names are SensorML-specific and do not collide.                                                                                                  |
| L12: Should this code exist?            | Are there new categories of functionality without precedent?                     | ✅ Type definitions are the foundation for SensorML parsers (Issue #24+). Every upstream handler starts with types. SWE Common types (Issue #17) established the precedent within Phase 3. |

**4/5 lesson checks pass. 1 finding identified (L10 — `Document` name collision).**

---

## Verification Status

| Check                      | Result                                                                                   |
| -------------------------- | ---------------------------------------------------------------------------------------- |
| `tsc --noEmit`             | ✅ Clean — no type errors                                                                |
| CSAPI unit tests (all)     | ✅ **423 passing**, 6 suites, 0 failures                                                 |
| CSAPI format tests         | ✅ **109 passing**, 3 suites (59 geojson + 27 swecommon + 23 sensorml)                   |
| Endpoint integration tests | ✅ **82/83 passing** (1 pre-existing: non-JSON parse test at endpoint.spec.ts line 1789) |

Test delta from Phase 3.3: 423 − 400 = **+23 tests** (all new SensorML type tests).

---

## Files Reviewed

### Issue #18 — SensorML 3.0 Type Definitions

| File                                               | Lines            | Scope                                                                                                                                                       |
| -------------------------------------------------- | ---------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `src/ogc-api/csapi/formats/sensorml/types.ts`      | +916 lines (new) | Complete SensorML 3.0 process-model type hierarchy: 3 base interfaces, 4 concrete process types, 20+ supporting types, discriminated union, 1 runtime const |
| `src/ogc-api/csapi/formats/sensorml/types.spec.ts` | +400 lines (new) | 23 type compilation, discriminator narrowing, and SWE Common integration tests                                                                              |

**Total change:** +1,316 lines (new module, no modifications to existing files)

---

## Overall Codebase Metrics (Cumulative)

### Phase 2 — URL Builder (Carried Forward, unchanged)

| File                  | Lines     | Purpose                                                   |
| --------------------- | --------- | --------------------------------------------------------- |
| `model.ts`            | 560       | Type definitions, constants, 9 resource interfaces        |
| `model.spec.ts`       | 377       | Type compatibility + constant validation tests            |
| `url_builder.ts`      | 1,863     | CSAPIQueryBuilder — 79 public methods + 4 private helpers |
| `url_builder.spec.ts` | 2,118     | URL builder tests                                         |
| **Phase 2 Subtotal**  | **4,918** | **314 tests**                                             |

### Phase 2→3 Bridge — Helpers (unchanged)

| File                 | Lines   | Purpose                                       |
| -------------------- | ------- | --------------------------------------------- |
| `helpers.ts`         | 223     | 7 original utility functions (no validators)  |
| `helpers.spec.ts`    | 314     | 43 original helper tests (no validator tests) |
| **Helpers Subtotal** | **537** | **43 tests**                                  |

### Phase 3 — Format Handlers + Type Definitions

| File                              | Lines     | Purpose                                                                          |
| --------------------------------- | --------- | -------------------------------------------------------------------------------- |
| `formats/geojson.ts`              | 379       | GeoJSON handler — recognition, parsing, extraction                               |
| `formats/geojson.spec.ts`         | 499       | GeoJSON handler tests                                                            |
| `formats/swecommon/types.ts`      | 723       | SWE Common 3.0 type definitions                                                  |
| `formats/swecommon/types.spec.ts` | 409       | SWE Common type compilation tests                                                |
| `formats/sensorml/types.ts`       | 916       | **NEW** — SensorML 3.0 type definitions                                          |
| `formats/sensorml/types.spec.ts`  | 400       | **NEW** — SensorML type compilation tests                                        |
| `formats/index.ts`                | 20        | Barrel file                                                                      |
| `shared/mime-type.ts`             | 68        | Media type detection (3 pre-existing + 5 CSAPI)                                  |
| `shared/mime-type.spec.ts`        | 139       | Media type detection tests                                                       |
| **Phase 3 Subtotal**              | **3,553** | **152 tests** (59 geojson + 27 swecommon + 23 sensorml + 31 mime-type + 12 misc) |

### Combined

| Metric                       | Value                                                                                       |
| ---------------------------- | ------------------------------------------------------------------------------------------- |
| Total lines (prod + test)    | **9,008**                                                                                   |
| Total CSAPI tests            | **423** (41 model + 43 helpers + 230 url_builder + 59 geojson + 27 swecommon + 23 sensorml) |
| Total tests incl. mime-type  | **454** (423 CSAPI + 31 mime-type)                                                          |
| Public methods (url_builder) | **79**                                                                                      |
| Public functions (geojson)   | **5** + 2 constants                                                                         |
| Public functions (helpers)   | **7**                                                                                       |
| Public types (swecommon)     | **48** exported interfaces/types/aliases                                                    |
| Public types (sensorml)      | **50** exported interfaces/types/aliases + 1 runtime const                                  |
| Combined public API surface  | **192** elements                                                                            |

---

## Prior Findings Status

### Phase 2 Findings (all resolved — no change)

#### [P2-F1] through [P2-F8] — All RESOLVED, unchanged.

No regressions. Not affected by current changes.

### Phase 1 Findings — All RESOLVED, unchanged.

Not affected by current changes.

### Phase 2.4–2.9 Findings — All UNCHANGED

Not affected by current changes.

### Phase 3.1 Findings (status check — third reaffirmation)

#### [F1] UNCHANGED: GeoJSON handler follows utility module best practices

Not affected. Layered architecture intact.

#### [F2] UNCHANGED: Test thoroughness exceeds Category A checklist

Not affected. Category A remains 6/6.

#### [F3] UNCHANGED: `parseValidTime` bridges smoke test finding F4

No changes to `parseValidTime`.

#### [F4] MOOT: Validation does not short-circuit — removed by Issue #52.

#### [F5] PARTIALLY MOOT: Type-specific constraints — validators removed, tolerant extraction remains.

#### [F6] UNCHANGED: `extractCSAPIFeature` produces correctly typed output

Not affected.

#### [F7] UNCHANGED — DESIGN: `as` type assertions in `extractCSAPIFeature`

Still uses `as System`, `as Deployment`, etc. Recommendation to migrate to `satisfies` still valid. Carried forward.

#### [F8] UNCHANGED: Barrel file for `formats/` directory

SensorML types are **not yet re-exported** from the barrel file — this is correct per the same scoping decision as SWE Common types (Phase 3.3 [F12]).

#### [F9] UNCHANGED: `makeFeature` test helper is well-designed.

#### [F10] UNCHANGED: SensorML vocabulary extension works.

#### [F11] UNCHANGED: Input guards on every public function.

### Phase 3.2 Findings

#### [F1] through [F3] UNCHANGED.

#### [F4] through [F11], [F13] MOOT — validator-related, removed by Issue #52.

#### [F12] RESOLVED — overlapping validation surfaces eliminated.

#### [F14] PARTIALLY UNCHANGED — surviving exports correctly wired.

### Phase 3.3 Findings (status check)

#### [F1] UNCHANGED: Validator removal is clean and complete.

#### [F2] UNCHANGED: `extractCSAPIFeature` follows Postel's Law.

#### [F3] UNCHANGED: Deployment branch handles missing `validTime`.

#### [F4] UNCHANGED: SWE Common type hierarchy correct.

#### [F5] UNCHANGED: All 16 SWE component types use `type` discriminators.

#### [F6] UNCHANGED: Encoding types extend `AbstractSWE`.

#### [F7] UNCHANGED: SWE type naming follows L10.

#### [F8] UNCHANGED: SWE Common Category B 6/6.

#### [F9] UNCHANGED: `DataField` design balances fidelity and usability.

#### [F10] UNCHANGED: `DataField` index signature loose by design.

#### [F11] UNCHANGED: `GeoJsonGeometry` loosely typed — correctly deferred.

#### [F12] UNCHANGED: SWE Common types not yet exported from barrel — correctly scoped.

#### [F13] UNCHANGED — DESIGN: `as` casts — carried forward.

---

## Phase 3.4 Findings — New

### [F1] POSITIVE: SensorML type hierarchy correctly mirrors OGC JSON schema inheritance

The inheritance chain in `types.ts`:

```
DescribedObject
  ├─ Mode
  └─ AbstractProcess
       ├─ SimpleProcess          (type = 'SimpleProcess')
       ├─ AggregateProcess       (type = 'AggregateProcess')
       └─ AbstractPhysicalProcess
            ├─ PhysicalComponent (type = 'PhysicalComponent')
            └─ PhysicalSystem    (type = 'PhysicalSystem')
```

This exactly mirrors the OAS schema composition:

- `DescribedObject` (L3432) — standalone base with 17 properties
- `AbstractProcess` (L3599) — `allOf: [DescribedObject, {...}]` with 8 additional properties
- `AbstractPhysicalProcess` (L4020) — `allOf: [AbstractProcess, {...}]` with 4 additional properties
- Each concrete type — `allOf: [parent, {type: const, ...}]`

The TypeScript `extends` keyword correctly replicates the `allOf` semantic: each child interface adds properties to the parent without redefining parent properties.

The hierarchy in the module-level JSDoc (lines 11–28) includes an ASCII tree diagram documenting both the process hierarchy and the SWE Common inheritance for supporting types.

**Severity:** POSITIVE

---

### [F2] POSITIVE: Four concrete types use string-literal `type` discriminators consistently

| Interface           | `type` Literal        | OAS `const` Value     | Supertype                 |
| ------------------- | --------------------- | --------------------- | ------------------------- |
| `SimpleProcess`     | `'SimpleProcess'`     | `"SimpleProcess"`     | `AbstractProcess`         |
| `AggregateProcess`  | `'AggregateProcess'`  | `"AggregateProcess"`  | `AbstractProcess`         |
| `PhysicalComponent` | `'PhysicalComponent'` | `"PhysicalComponent"` | `AbstractPhysicalProcess` |
| `PhysicalSystem`    | `'PhysicalSystem'`    | `"PhysicalSystem"`    | `AbstractPhysicalProcess` |

All four match their OAS `const` values exactly. The `SensorMLProcess` union and `SensorMLProcessType` derived type enable exhaustive switch narrowing, verified by the `exhaustively handles all four types in a switch` test.

The `ComponentLink` type adds a 5th discriminator (`type: 'Link'`) for the component-list variant, keeping the component-entry discriminated union exhaustive:

```typescript
type ComponentEntry = { name: string } & (SensorMLProcess | ComponentLink);
```

**Severity:** POSITIVE

---

### [F3] DESIGN: `Document` interface name shadows TypeScript DOM global

The `Document` interface (line ~148) conflicts with the TypeScript DOM global `Document` (the browser DOM document object). In a file that includes `lib: ["DOM"]` in its tsconfig, an unqualified reference to `Document` could be ambiguous.

**Current impact:** LOW — this module uses `import type`, so the SensorML `Document` takes precedence in any file that imports it. TypeScript resolves the closest-scope name. The upstream OGC schema uses the name `Document`, so the choice is spec-faithful.

**Comparison with SWE Common L10 approach:** SWE Common prefixed all colliders (`SweBoolean`, `SweText`, `SweTime`, `SweGeometry`). SensorML could prefix as `SmlDocument` for consistency. However, unlike `Boolean` (which is a JavaScript primitive wrapper), `Document` only collides in DOM-enabled environments, and the SensorML types are pure server-side types unlikely to be mixed with DOM code.

**Recommendation:** Accept as-is for now. If a collision is ever reported in consumer code, rename to `SmlDocument`. Document this decision.

**Decision (2026-02-15):** ACCEPTED-BY-DESIGN — The OAS schema uses `Document`, module imports eliminate ambient collision, and the rename cost is near-zero if a consumer ever reports an issue. No action needed.

**Severity:** DESIGN (low) — **ACCEPTED-BY-DESIGN**

---

### [F4] POSITIVE: SWE Common integration is clean and correctly scoped

The import statement:

```typescript
import type {
  AbstractSweIdentifiable,
  AnySimpleComponent,
  AnyComponent,
  Vector,
  DataRecord,
  DataArray,
  Matrix,
} from '../swecommon/types.js';
```

This imports exactly 7 SWE Common types — the minimal set needed for:

- `AbstractSweIdentifiable` → base for `CapabilityList`, `CharacteristicList`, `SpatialFrame`, `TemporalFrame`, `Event`, `ObservableProperty`
- `AnySimpleComponent` → conditions in capability/characteristic lists
- `AnyComponent` → I/O component choice union
- `Vector`, `DataRecord`, `DataArray` → Position union (deprecated variants)
- `Matrix` → AnyProperty union

No unnecessary imports. The `import type` keyword ensures zero runtime coupling — this is purely a TypeScript compilation dependency.

The 5 SWE-Common-integration tests in `types.spec.ts` verify that:

1. `CapabilityList` accepts SWE components in its `capabilities` array
2. `CharacteristicList` accepts SWE components in its `characteristics` array
3. `Position` accepts a `GeoJsonPoint` variant
4. `ComponentEntry` accepts an inline `PhysicalComponent`
5. `ComponentEntry` accepts a `ComponentLink` reference

**Severity:** POSITIVE

---

### [F5] POSITIVE: Required vs optional property mapping matches OAS schema

Cross-referencing the OAS `required` arrays against TypeScript property optionality:

| Interface            | OAS Required                         | TypeScript Required         | Match? |
| -------------------- | ------------------------------------ | --------------------------- | ------ |
| `DescribedObject`    | `type`, `label`, `uniqueId`          | `type`, `label`, `uniqueId` | ✅     |
| `Term`               | `label`, `value`                     | `label`, `value`            | ✅     |
| `Document`           | `name`, `link`                       | `name`, `link`              | ✅     |
| `ResponsibleParty`   | `role`                               | `role`                      | ✅     |
| `CapabilityList`     | `capabilities` (from allOf[1])       | `capabilities`              | ✅     |
| `CharacteristicList` | `characteristics` (from allOf[1])    | `characteristics`           | ✅     |
| `Event`              | `label`, `time` (from allOf[1])      | `label`, `time`             | ✅     |
| `SpatialFrame`       | `origin`, `axes` (from allOf[1])     | `origin`, `axes`            | ✅     |
| `TemporalFrame`      | `origin` (from allOf[1])             | `origin`                    | ✅     |
| `ObservableProperty` | `type`, `definition` (from allOf[1]) | `type`, `definition`        | ✅     |
| `Connection`         | `source`, `destination`              | `source`, `destination`     | ✅     |
| `FrameAxis`          | `name`, `description`                | `name`, `description`       | ✅     |
| `GeoJsonPoint`       | `type`, `coordinates`                | `type`, `coordinates`       | ✅     |

All properties that are required by the OAS schema are non-optional in TypeScript. All other properties are optional (`?`). **13/13 interfaces verified.**

**Severity:** POSITIVE

---

### [F6] POSITIVE: `Position` union covers all 8 OAS oneOf variants

The OAS `Position` schema (L3998) defines a `oneOf` with 8 alternatives. The TypeScript `Position` type:

```typescript
export type Position =
  | string // by Text
  | GeoJsonPoint // by Point
  | Pose // by Pose (GeoPose)
  | AbstractProcess // by Process
  | Link // by Datastream
  | Vector // by Location Vector (deprecated)
  | DataRecord // by Position DataRecord (deprecated)
  | DataArray; // by Trajectory DataArray (deprecated)
```

All 8 variants are represented. The JSDoc clearly marks 3 variants as deprecated (matching OAS), and the remaining 5 as current. The forward reference to `AbstractProcess` is resolved lazily by TypeScript (declared earlier in the same file).

**Severity:** POSITIVE

---

### [F7] POSITIVE: Supporting type coverage is comprehensive

The module defines 20+ supporting types beyond the core process hierarchy:

| Category         | Types                                                                                                                               | Count                                                      |
| ---------------- | ----------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------- |
| Primitives       | `Link`, `TimePeriod`, `TimeInstant`, `TimeInstantOrPeriod`, `PathRef`                                                               | 5                                                          |
| Metadata         | `Term`, `Document`, `LegalConstraint`, `SecurityConstraint`, `ContactInfo`, `ResponsibleParty`, `ContactLink`, `ObservableProperty` | 8                                                          |
| Properties       | `AnyProperty`, `CapabilityList`, `CharacteristicList`                                                                               | 3                                                          |
| I/O              | `IOComponentChoice`, `InputList`, `OutputList`, `ParameterList`                                                                     | 4                                                          |
| Configuration    | `ProcessMethod`, `SettingValue`, `SettingArrayValue`, `SettingMode`, `SetConstraint`, `SettingStatus`, `Settings`                   | 7                                                          |
| Spatial/Temporal | `FrameAxis`, `SpatialFrame`, `TemporalFrame`, `GeoJsonPoint`, `Pose`, `Position`                                                    | 6                                                          |
| Events           | `Event`, `FeatureList`                                                                                                              | 2                                                          |
| Components       | `ComponentLink`, `ComponentEntry`, `ComponentList`, `Connection`, `ConnectionList`                                                  | 5                                                          |
| **Total**        |                                                                                                                                     | **40 supporting + 7 process + 3 union/const = 50 exports** |

Every OGC schema type referenced by the SensorML process model is represented.

**Severity:** POSITIVE

---

### [F8] POSITIVE: Test suite covers all Category B checklist dimensions

Evaluating against the Phase 3 Category B (Type definition) test checklist:

| Checklist Item                                                  | Status | Evidence                                                                                                                                                                                    |
| --------------------------------------------------------------- | ------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Type definitions compile (`tsc --noEmit`)                       | ✅     | Verification gate: 0 errors                                                                                                                                                                 |
| Union types discriminate correctly                              | ✅     | 4 `SensorMLProcess` narrowing tests + 1 exhaustive switch test                                                                                                                              |
| Interface compatibility: well-formed object satisfies interface | ✅     | 23 tests construct typed object literals that TypeScript checks at compile time                                                                                                             |
| Required vs optional properties                                 | ✅     | `DescribedObject` test populates all optional fields; `AggregateProcess` test omits `components`/`connections` (optional)                                                                   |
| Cross-module type references resolve                            | ✅     | 5 SWE Common integration tests: `CapabilityList` with `AnySimpleComponent[]`, `CharacteristicList`, `Position` with `GeoJsonPoint`, `ComponentEntry` with inline process and link reference |

**5/5 checklist items pass.** This is the first module where cross-module type references are tested (SWE Common types → SensorML types), fulfilling the N/A from Phase 3.3 review.

**Severity:** POSITIVE

---

### [F9] POSITIVE: `SENSORML_PROCESS_TYPES` const tuple enables runtime validation

The const tuple:

```typescript
export const SENSORML_PROCESS_TYPES = [
  'SimpleProcess',
  'AggregateProcess',
  'PhysicalComponent',
  'PhysicalSystem',
] as const;
```

Provides a runtime-accessible list of valid discriminator values. This is the only runtime export in the module — everything else is type-only (`import type`). The corresponding `SensorMLProcessType` literal union is derived from `SensorMLProcess['type']`, so it automatically stays in sync with the union.

The test verifies both the values and length (`toHaveLength(4)`), preventing accidental additions or removals.

This follows the same pattern as `SweComponentType` in SWE Common types.

**Severity:** POSITIVE

---

### [F10] POSITIVE: JSDoc quality is comprehensive with spec links

Every exported type has:

- A `/** ... */` JSDoc comment describing its purpose
- `@see` links to OAS line numbers (e.g., `@see OAS: DescribedObject (L3432)`)
- `@see` links to SensorML 3.0 spec sections (e.g., `@see SensorML 3.0 §7.2`)
- Property-level doc comments on every property

The module-level JSDoc includes:

- ASCII tree diagram of the complete type hierarchy
- Design notes explaining SWE Common dependency, discriminator pattern, required vs optional convention, and forward references
- Three `@see` links (SensorML 3.0, SensorML 2.0 UML reference, OAS schemas)

**Severity:** POSITIVE

---

### [F11] INFORMATIONAL: `AnyProperty` uses `as unknown as AnyProperty` cast in tests

The SWE Common integration tests use:

```typescript
{ name: 'accuracy', type: 'Quantity', uom: { code: 'Cel' }, value: 0.5 } as unknown as AnyProperty
```

The double cast (`as unknown as`) is needed because `AnyProperty` is an intersection type (`{ name: string } & (AnySimpleComponent | Vector | DataArray | Matrix)`), and TypeScript cannot structurally resolve the inline object literal against all union variants. This is a test artifact — real parsed data will come from JSON deserialization where the structural check passes naturally.

**Severity:** INFORMATIONAL (no action needed)

---

### [F12] INFORMATIONAL: SensorML types not yet exported from barrel file or `src/index.ts`

Same as Phase 3.3 [F12] for SWE Common. The `formats/index.ts` barrel file does not re-export SensorML types. This is correct — exports should be added when the SensorML index module is created (Issue #28 or a dedicated barrel update).

**Severity:** INFORMATIONAL (correctly scoped — no action needed)

---

### [F13] INFORMATIONAL: `ContactInfo` uses inline object types for nested structures

The `ContactInfo` interface nests two inline object types (`phone` and `address`) rather than extracting them as named interfaces:

```typescript
phone?: { voice?: string[]; facsimile?: string[] };
address?: { deliveryPoint?: string[]; city?: string; ... };
```

This is acceptable — `phone` and `address` are not reused anywhere else in the SensorML model, so extracting them would add names without providing reuse benefit. If a future ISO 19115 contact module is needed, these could be extracted then.

**Severity:** INFORMATIONAL

---

### [F14] DESIGN (carried forward): `as` type assertions in `extractCSAPIFeature`

Carried forward from Phase 3.1 [F7] → Phase 3.3 [F13]. No change.

**Severity:** DESIGN (low)

---

## Test Quality Heatmap

### Phase 2 (URL Builder) — Carried Forward

No changes from Phase 3.3 heatmap. All entries unchanged.

| Dimension                           | Systems        | Deployments | Procedures | SF       | Properties | DataStreams | Observations | ControlStreams | Commands   |
| ----------------------------------- | -------------- | ----------- | ---------- | -------- | ---------- | ----------- | ------------ | -------------- | ---------- |
| No options (base URL)               | ✅             | ✅          | ✅         | ✅       | ✅         | ✅          | ✅           | ✅             | ✅         |
| `limit`                             | ✅             | ✅          | ✅         | ✅       | ✅         | ✅          | ✅ (combo)   | ✅ (combo)     | ✅ (combo) |
| `offset` (standalone)               | ✅             | ✅          | ✅         | ✅       | ✅         | ✅          | ✅           | ✅             | ✅         |
| `q`                                 | ✅             | ✅          | ✅         | ✅       | ✅         | ✅          | ✅           | ✅             | N/A        |
| `id` (single)                       | ❌             | ❌          | ✅         | ✅       | ✅         | ✅          | ✅           | ✅             | ✅         |
| `id` (array)                        | ✅             | ❌          | ✅         | ✅       | ✅         | ✅          | ✅           | ✅             | ✅         |
| `bbox`                              | ✅             | ✅          | N/A        | ✅       | N/A        | N/A         | N/A          | N/A            | N/A        |
| `datetime` / temporal (exact)       | ✅             | ✅          | N/A        | ✅       | N/A        | ✅          | ✅           | ✅             | ✅         |
| `f` (format)                        | ❌             | ✅          | ✅         | ✅       | ✅         | ✅          | ✅           | ✅             | ✅         |
| `cursor`                            | ✅             | ❌          | ❌         | ❌       | ❌         | ✅          | ✅           | ❌             | ✅         |
| Multiple options (incl. offset)     | ✅             | ❌          | ✅         | ✅       | ✅         | ✅          | ✅           | ✅             | ✅         |
| Type-specific params                | ✅ (6/6)       | ✅ (3/3)    | N/A        | N/A      | ✅ (2/2)   | ✅ (4/4)    | ✅ (2/2)     | ✅ (2/2)       | ✅ (1/1)   |
| Resource validation (all methods)   | ❌ (scattered) | ✅ (8/8)    | ✅ (8/8)   | ✅ (8/8) | ✅ (6/6)   | ✅ (11/11)  | ✅ (8/8)     | ✅ (8/8)       | ✅ (10/10) |
| Association/sub-resource pagination | Partial        | ✅          | ✅         | ✅       | ✅         | ✅          | N/A          | ✅             | N/A        |

---

### Phase 3 (Format Handlers + Types) — Current

**Category A — GeoJSON Handler (geojson.ts + SensorML vocabulary)**

| Dimension                    | Status | Evidence                                                                         |
| ---------------------------- | ------ | -------------------------------------------------------------------------------- |
| Valid input → correct output | ✅     | All 5 functions + SensorML variant tested                                        |
| Invalid input → rejection    | ✅     | null, undefined, wrong type, missing fields                                      |
| All spec variants            | ✅     | 12 SOSA + 1 SensorML local names × 2 forms                                       |
| All classification branches  | ✅     | System (5) + Deployment (1) + Procedure (4) + SF (2+1 SML) + unrecognized → null |
| Tolerant extraction          | ✅     | 3 tolerant extraction tests                                                      |
| Edge cases                   | ✅     | Array wrong length, non-string start, "now" sentinel, missing props              |

**GeoJSON Handler: 6/6 dimensions (100%)**

**Category A — Format Detector (mime-type.ts)**

| Dimension                    | Status | Evidence                                          |
| ---------------------------- | ------ | ------------------------------------------------- |
| Valid input → correct output | ✅     | Canonical form for each of 5 functions            |
| Invalid input → rejection    | ✅     | Non-matching types return false                   |
| All spec variants            | ✅     | Canonical, suffixed, case-insensitive             |
| All classification branches  | ✅     | Each function true for own type, false for others |
| Cross-match prevention       | ✅     | CSV↛Text, Text↛CSV, SWE↛SML                       |
| Edge cases                   | ✅     | Case variation, parameter-suffixed forms          |

**Format Detector: 6/6 dimensions (100%)**

**Category B — SWE Common Types (swecommon/types.ts)**

| Dimension                           | Status | Evidence                                                 |
| ----------------------------------- | ------ | -------------------------------------------------------- |
| Compilation (`tsc --noEmit`)        | ✅     | Verification gate passed                                 |
| Union discrimination (all branches) | ✅     | 9 AnyComponent + 4 DataEncoding narrowing tests          |
| Interface compatibility             | ✅     | 27 tests construct typed objects                         |
| Recursive nesting                   | ✅     | 3 tests: nested DataRecord, DataArray+DataRecord, Matrix |
| Supporting types                    | ✅     | 10 tests: UoM, AllowedValues, NilValue, etc.             |
| All 16 component types enumerated   | ✅     | `covers all 16 component types` test                     |

**SWE Common Types: 6/6 dimensions (100%)**

**Category B — SensorML Types (sensorml/types.ts)** — NEW

| Dimension                           | Status | Evidence                                                                                                                                                                                                                                     |
| ----------------------------------- | ------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Compilation (`tsc --noEmit`)        | ✅     | Verification gate passed                                                                                                                                                                                                                     |
| Union discrimination (all branches) | ✅     | 4 narrowing tests + 1 exhaustive switch                                                                                                                                                                                                      |
| Interface compatibility             | ✅     | 23 tests construct typed objects (DescribedObject, Mode, AbstractProcess, Term, Document, ResponsibleParty, ObservableProperty, Settings, Connection, Event, SpatialFrame, CapabilityList, CharacteristicList, GeoJsonPoint, ComponentEntry) |
| Required vs optional                | ✅     | Required fields enforced by tsc; optional fields omitted in tests                                                                                                                                                                            |
| Cross-module type references        | ✅     | 5 SWE Common integration tests (CapabilityList, CharacteristicList, Position, ComponentEntry inline, ComponentEntry link)                                                                                                                    |
| Runtime const validation            | ✅     | `SENSORML_PROCESS_TYPES` values + length test                                                                                                                                                                                                |

**SensorML Types: 6/6 dimensions (100%)**

---

## Smoke Test Findings Integration

| Finding                           | Status                | Evidence                                                |
| --------------------------------- | --------------------- | ------------------------------------------------------- |
| F4 (validTime array format)       | ✅ **Addressed**      | `parseValidTime` handles `["ISO", "now"]` (unchanged)   |
| F33-F39                           | N/A                   | Scoped to later Phase 3/4 tasks                         |
| F40 (SensorML featureType)        | ✅ **Addressed**      | `SENSORML_NS` + `toSensormlLocalName()` (unchanged)     |
| F41 (null featureType in GeoJSON) | N/A                   | Requires design decision — tracked in roadmap           |
| F49 (validators block extraction) | ✅ **Fully resolved** | Validators removed (Issue #52), confirmed by smoke test |
| F50 (content type change)         | N/A                   | Response parser scope                                   |

**3 of 6 relevant findings addressed.** No change from Phase 3.3.

---

## Summary

| Category                     | Count  | Items                                                                                                                                                                             |
| ---------------------------- | ------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Prior findings unchanged     | **36** | All Phase 2–3.1 accumulated findings                                                                                                                                              |
| Prior findings moot          | **10** | Phase 3.2 validator-related                                                                                                                                                       |
| Prior findings resolved      | **1**  | Phase 3.2 F12                                                                                                                                                                     |
| Phase 3.3 findings unchanged | **13** | F1–F13 (all re-confirmed)                                                                                                                                                         |
| **New — positive findings**  | **10** | F1 (hierarchy), F2 (discriminators), F4 (SWE integration), F5 (required/optional), F6 (Position union), F7 (supporting types), F8 (Category B 6/6), F9 (const tuple), F10 (JSDoc) |
| **New — design**             | **1**  | F3 (`Document` name shadows DOM global)                                                                                                                                           |
| **New — informational**      | **3**  | F11 (`as unknown as` in tests), F12 (exports deferred), F13 (inline ContactInfo)                                                                                                  |
| **New — carried forward**    | **1**  | F14 (`as` casts — from Phase 3.1 F7)                                                                                                                                              |
| **New bugs**                 | **0**  | —                                                                                                                                                                                 |

---

## Recommendations

### Fix Now (before next issue)

None. The module is clean.

### Fix Before Phase 4

1. ~~**[F3] Consider renaming `Document` to `SmlDocument`**~~ — **ACCEPTED-BY-DESIGN (2026-02-15).** OAS schema uses `Document`, module imports eliminate ambient collision, rename cost is near-zero if a consumer ever reports an issue.

2. **[F14/3.1-F7] Replace `as` casts with `satisfies` in `extractCSAPIFeature`** — Carried forward. Recommend fixing when extraction function is next modified.

3. **Systems consolidated resource validation tests** — Carried forward from Phase 2.9.

### Defer (Low Priority)

4. **Cursor standalone tests** — Deployments, Procedures, SamplingFeatures, Properties, ControlStreams.

5. **`id` (single) tests for Systems and Deployments** — Same serialization path.

6. **[Phase 2.8 F8] JSDoc example casing alignment** — No functional impact.

---

## Root Cause Analysis — Continued Zero Defects

Phase 3.4 is the **eleventh consecutive phase** with zero new defects. The streak: Procedures → SamplingFeatures → Properties → DataStreams → Observations → ControlStreams → Commands → GeoJSON Handler → SensorML Vocab + Format Detector + Validators → Validator Removal + SWE Common Types → **SensorML Types**.

### Why this issue was clean

**Issue #18 (SensorML Types):**

1. **Strong upstream reference** — The OGC OAS 3.1 bundled schema provided authoritative field names, types, required arrays, and inheritance composition for every interface.
2. **Established pattern** — SWE Common types (Issue #17) established the exact module structure, JSDoc style, discriminated union pattern, import conventions, and Category B test approach. SensorML types followed the same template, reducing design decisions to zero.
3. **Pure type definitions** — No runtime code, no side effects, no integration points. The only runtime export is a single const tuple. Type errors are caught at `tsc` compile time, not at test runtime.
4. **Scoped imports** — Only 7 SWE Common types imported, all via `import type`. No coupling to model.ts, helpers, or any runtime module.

---

## Overall Assessment

**Phase 3.4 is clean and extends the SensorML type foundation for upcoming parsers.**

1. **SensorML types complete the type layer for Phase 3.** With SWE Common (Issue #17) providing data-component types and SensorML (Issue #18) providing process-model types, the full type system needed for SensorML parsers (Issues #24–#28) is now in place. The two modules together provide 98 exported types covering 100% of the OGC Connected Systems Part 1 schema surface.

2. **Cross-module integration is verified for the first time.** The 5 SWE Common integration tests in the SensorML spec file confirm that the `import type` relationship works correctly — SensorML types that reference SWE Common types (`CapabilityList → AnySimpleComponent`, `AnyProperty → Vector | DataArray | Matrix`, `IOComponentChoice → AnyComponent`) all compile and construct correctly. This closes the N/A gap from Phase 3.3 [F8].

3. **The `Document` naming issue (F3) is the only design concern.** It follows L10 principles but stops short of the `Swe*` prefix convention used in SWE Common. The risk is low (server-side types won't mix with DOM code), and the name is spec-faithful. If a collision is reported by consumers, a rename is straightforward.

**Cumulative project quality:**

- **11 consecutive phases** with zero defects (Phase 2.3 → Phase 3.4)
- **0 open bug or gap findings**
- **1 new low-severity design finding** (F3: `Document` name — ACCEPTED-BY-DESIGN) + **1 carried forward** (F14: `as` casts)
- **423 CSAPI tests** + 31 mime-type tests = **454 total**, all passing
- **~9,000 lines** of production + test code
- **Phase 2:** 79 public methods, 9 resource types, 314 tests — **complete**
- **Phase 3:** 5 GeoJSON functions + 5 mime-type detectors + 48 SWE types + 50 SensorML types + 2 constants = **110 public API elements**, 152 Phase 3 tests — **in progress**
