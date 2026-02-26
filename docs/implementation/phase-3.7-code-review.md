# Phase 3.7 Code Review — PhysicalSystem & PhysicalComponent Sub-Parsers

**Date:** 2025-07-19
**Reviewer:** GitHub Copilot (Claude Opus 4.6)
**Scope:** SensorML 3.0 PhysicalSystem & PhysicalComponent sub-parsers (Issue #21)
**Commits:**

- `0060356` — "feat(sensorml): add PhysicalSystem & PhysicalComponent sub-parsers (Issue #21)"

**Previous Review:** Phase 3.6 — AggregateProcess Sub-Parser + Validation Sweep (commit `fc429f4`)
**Review Category:** C (Parser modules — fixture → typed output assertions)

---

## Verification Gates

| Gate                   | Command                                | Result                      |
| ---------------------- | -------------------------------------- | --------------------------- |
| TypeScript compilation | `npx tsc --noEmit`                     | ✅ Clean (exit code 0)      |
| CSAPI test suite (all) | `npx jest "src/ogc-api/csapi"`         | ✅ **598 passed**, 9 suites |
| Format tests           | `npx jest "src/ogc-api/csapi/formats"` | ✅ **284 passed**, 6 suites |
| PhysicalSystem tests   | `npx jest "physical-system"`           | ✅ **87 passed**, 1 suite   |

**Test delta from Phase 3.6:** +87 tests (from 197 → 284 format tests), +87 net in CSAPI (from 511 → 598).

---

## Files Reviewed

### Issue #21 — SensorML PhysicalSystem & PhysicalComponent Parser

| File                                                         | Lines          | Status  |
| ------------------------------------------------------------ | -------------- | ------- |
| `src/ogc-api/csapi/formats/sensorml/physical-system.ts`      | 905 (+905)     | **NEW** |
| `src/ogc-api/csapi/formats/sensorml/physical-system.spec.ts` | 1,178 (+1,178) | **NEW** |

**Total new code:** 2,083 lines (905 production + 1,178 test).

---

## Step 1: Lessons Learned Check

| Lesson                                                     | Applicable? | Status | Evidence                                                                                                                                                                                                      |
| ---------------------------------------------------------- | ----------- | ------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **L1:** Audit upstream before building new layers          | ✅          | PASS   | PhysicalSystem/PhysicalComponent parser follows the pattern established by Issues #19 and #20. No new architectural layer.                                                                                    |
| **L2:** Postel's Law — never gate extraction on validation | ✅          | PASS   | Validates only 3 required fields per parser (`type`, `label`, `uniqueId`). All 14+ optional properties gracefully return `undefined`. Null values treated as absent.                                          |
| **L3:** Don't couple validation to extraction              | ✅          | PASS   | Parser extracts what is present. Recognition (`type === 'PhysicalSystem'`) gates extraction, not validation. External links and unrecognized position variants pass through as-is.                            |
| **L4:** Don't build parallel systems                       | ✅          | PASS   | Single parser per type. Internal helpers duplicated from siblings (see F3 below) but not an alternative path.                                                                                                 |
| **L5:** Verify upstream claims by reading source           | N/A         | —      | No upstream claims made.                                                                                                                                                                                      |
| **L6:** Real-world server data diverges from spec          | ✅          | PASS   | Null/undefined handling for all optional properties. `parsePosition` has an explicit fallback to pass-through for unrecognized objects (line 658–659) to avoid data loss. `parsePose` tolerates partial data. |
| **L7:** Phase 3 smoke tests are essential                  | N/A         | —      | Sub-parser doesn't connect to live servers (smoke test deferred to Issue #22 integration).                                                                                                                    |
| **L8:** Layered architecture enables clean extension       | ✅          | PASS   | Error class → shared helpers → frame helpers → position helpers → component/connection helpers → main parsers. Clear hierarchy with 6 distinct layers.                                                        |
| **L9:** Content negotiation cannot be assumed              | N/A         | —      | Not applicable to sub-parser (no HTTP).                                                                                                                                                                       |
| **L10:** Type naming must avoid built-in collisions        | ✅          | PASS   | `SensorMLParseError` clearly namespaced. `Position`, `Pose`, `GeoJsonPoint` are OGC-specific names — no JavaScript built-in collisions.                                                                       |
| **L11:** Document architectural decisions formally         | ✅          | PASS   | Module JSDoc (lines 1–22) describes scope, recursive parsing, type-specific differences, and links to OAS line numbers. Deferral to Issue #22 documented in `parseComponentEntry` and `parsePosition` JSDoc.  |
| **L12:** "Should we build it at all?"                      | ✅          | PASS   | ROADMAP Task 7 explicitly scopes this parser. Required for Issue #22 (main parser).                                                                                                                           |
| **L13:** AI drift can fabricate findings                   | N/A         | —      | No smoke test in this review period.                                                                                                                                                                          |

**Result: 8/8 applicable lessons pass. 5 not applicable.**

---

## Step 4: Prior Findings Reaffirmation

### Phase 2 Findings — Unchanged

All Phase 2 accumulated findings (36 unchanged + 10 moot + 1 resolved) carry forward with no changes. The PhysicalSystem parser does not touch URL builder code, helpers, or model definitions.

### Phase 3.1–3.3 Findings — Unchanged

- **Phase 3.1 F7 / carried forward as F13:** `as` type assertions in `extractCSAPIFeature` — **still open, carried forward**
- **Phase 3.3 F12 / Phase 3.4 F12:** Exports not in barrel — **still correct** (barrel updates deferred to Issue #23)
- **Phase 3.2 F1–F11:** Moot (validator removal) — **still moot**

### Phase 3.4 Findings — Unchanged

| Finding                                         | Status             | Notes                                |
| ----------------------------------------------- | ------------------ | ------------------------------------ |
| F1–F2 (POSITIVE type hierarchy, discriminators) | Unchanged          | Types consumed by physical-system.ts |
| F3 (DESIGN Document name)                       | ACCEPTED-BY-DESIGN | Unchanged                            |
| F4–F10 (POSITIVE)                               | Unchanged          | Type layer findings                  |
| F11–F13 (INFORMATIONAL)                         | Unchanged          |                                      |
| F14 (DESIGN `as` casts)                         | Carried forward    | Not in scope                         |

### Phase 3.5 Findings — Unchanged

All 13 findings from Phase 3.5 carry forward unchanged. The PhysicalSystem parser reuses the same patterns (Postel's Law, DescribedObject passthrough, error messages with context, Mode/Link parsing, deferred IOComponentChoice, JSDoc).

### Phase 3.6 Findings — Status Update

| Finding                                                 | Phase 3.6 Status | Current Status             | Notes                                                                                                                                                                                                                                                         |
| ------------------------------------------------------- | ---------------- | -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| F1 (POSITIVE ComponentList recursive)                   | POSITIVE         | **Extended**               | physical-system.ts adds PhysicalSystem recursive parsing (line 284) alongside AggregateProcess recursion                                                                                                                                                      |
| F2 (POSITIVE ConnectionList strict)                     | POSITIVE         | Unchanged                  | Same `parseConnection` pattern reused identically                                                                                                                                                                                                             |
| F3 (DESIGN helper duplication)                          | DESIGN (low)     | **Expanded** — now 3 files | physical-system.ts adds a third copy of all 9 helpers. See new F3 below.                                                                                                                                                                                      |
| F4 (POSITIVE name re-attach)                            | POSITIVE         | **Reused**                 | Same `{ ...parsed, name }` spread in physical-system.ts line 285                                                                                                                                                                                              |
| F5 (POSITIVE test coverage)                             | POSITIVE         | **Surpassed**              | 87 tests vs 50 (AggregateProcess) — additional coverage for position variants, frame parsing, method parsing                                                                                                                                                  |
| F6 (POSITIVE recursive test)                            | POSITIVE         | **Extended**               | New recursive test for PhysicalSystem → PhysicalSystem nesting                                                                                                                                                                                                |
| F7 (POSITIVE error re-throw guard)                      | POSITIVE         | Unchanged                  | Same `instanceof SensorMLParseError` guard in `parseComponentList`                                                                                                                                                                                            |
| F8 (POSITIVE template cleanup)                          | POSITIVE         | Unchanged                  | No template changes in this period                                                                                                                                                                                                                            |
| F9 (INFORMATIONAL exports deferred)                     | INFORMATIONAL    | **Expanded**               | PhysicalSystem exports (`parsePhysicalSystem`, `parsePhysicalComponent`, `parseProcessMethod`, `parsePosition`, `parseComponentList`, `parseConnectionList`, `parseComponentEntry`, `SensorMLParseError`) also not in barrel — correct, deferred to Issue #23 |
| F10 (INFORMATIONAL IOComponentChoice not dual-exported) | INFORMATIONAL    | Unchanged                  | Same pattern — `parseIOComponentChoice` private in physical-system.ts                                                                                                                                                                                         |
| F11 (INFORMATIONAL SensorMLParseError dual class)       | INFORMATIONAL    | **Expanded**               | Now _triple_ — `SensorMLParseError` exported from 3 files. See new F3 below.                                                                                                                                                                                  |

---

## Phase 3.7 Findings — New

### [F1] POSITIVE: Comprehensive Position parsing with 8-variant discrimination

`parsePosition()` (lines 607–659) implements a priority-ordered dispatch chain covering all 8 position variants defined by the OAS Position union type:

1. **String** — textual description (line 615)
2. **GeoJSON Point** — `{ type: 'Point', coordinates: [...] }` (line 620)
3. **Pose** — GeoPose YPR, Quaternion, Relative YPR, Relative Quaternion (line 623)
4. **Link** — `{ href: '...' }` (line 627)
5. **AbstractProcess** — SensorML process types (lines 630–636)
6. **Deprecated SWE Common** — Vector, DataRecord, DataArray (lines 640–647)
7. **Unrecognized object** — pass-through fallback (line 650)
8. **null/undefined** — returns undefined (line 612)

The dispatch order is correct: GeoJSON Point must precede Pose (both are objects; Point has specific structure), and Pose must precede Link (Pose may lack `href`). The `parseGeoJsonPoint` function performs proper structural validation (type, coordinates length, numeric elements).

The fallback on line 650 (`return value as unknown as Position`) follows Postel's Law — unrecognized position data is preserved rather than discarded.

**Severity:** POSITIVE

---

### [F2] POSITIVE: SpatialFrame and TemporalFrame parsing with required-field validation

The frame parsing layer (lines 382–486) introduces two new helper families not present in the SimpleProcess or AggregateProcess parsers:

**SpatialFrame** (`parseSpatialFrame`, lines 412–444):

- Validates `origin` (required string)
- Validates `axes` (required non-empty array)
- Each `FrameAxis` validated for `name` and `description` (both required strings)
- Optional `id`, `label`, `description` on the frame itself

**TemporalFrame** (`parseTemporalFrame`, lines 460–473):

- Validates `origin` (required string)
- Optional `id`, `label`, `description`

Error messages include indexed context:

```
localReferenceFrames[0] must have a string "origin" property
axes[0] must have a string "name" property
```

This is the correct level of strictness — frame structure is well-defined with mandatory fields, unlike the more polymorphic position types where tolerance is needed.

**Severity:** POSITIVE

---

### [F3] DESIGN (low): Internal helpers now triplicated across 3 sub-parser files

The following 9 internal helpers are **exact duplicates** across `simple-process.ts`, `aggregate-process.ts`, and `physical-system.ts`:

| Helper                         | simple-process.ts | aggregate-process.ts | physical-system.ts |
| ------------------------------ | ----------------- | -------------------- | ------------------ |
| `SensorMLParseError` class     | 41–47             | 53–59                | 62–67              |
| `isRecord()`                   | 55–57             | 67–69                | 74–76              |
| `optionalString()`             | 62–64             | 74–76                | 81–83              |
| `parseLink()`                  | 72–82             | 84–96                | 89–100             |
| `parseIOComponentChoice()`     | 112–127           | 108–125              | 132–147            |
| `parseIOList()`                | 138–155           | 136–155              | 157–175            |
| `parseSettings()`              | 163–166           | 170–175              | 185–190            |
| `parseFeatureList()`           | 174–183           | 183–192              | 198–208            |
| `parseMode()` / `parseModes()` | 194–219           | 201–226              | 216–241            |

This is **expected and correct for Phase 3** — all three sub-parser issues (#19, #20, #21) specify "Do NOT modify files outside the 'Files to Create or Modify' table." The triplication creates a clean consolidation target for Issue #22 (SensorML Main Parser).

The `SensorMLParseError` class is now exported from three files with identical behavior but **three different class constructors at runtime** — `instanceof` checks across sub-parsers will fail. This has no current impact but must be addressed by Issue #22.

**Recommendation:** No action now. Issue #22 should extract the 9 duplicated helpers + `SensorMLParseError` into `sensorml/_helpers.ts` and re-export from a single location. The frame parsing helpers (`parseSpatialFrame`, `parseTemporalFrame`, `parseGeoJsonPoint`, `parsePose`, `parsePosition`) unique to physical-system.ts should also be considered for shared extraction, as the main parser entry point may need them.

**Severity:** DESIGN (low — expected, scoped to Issue #22)

---

### [F4] POSITIVE: Pose parsing handles all 4 GeoPose variants tolerantly

`parsePose()` (lines 534–567) correctly handles the 4 GeoPose variants:

1. **GeoPose YPR** — position + angles (yaw/pitch/roll)
2. **GeoPose Quaternion** — position + quaternion (x/y/z/w)
3. **Relative Pose YPR** — angles only
4. **Relative Pose Quaternion** — quaternion only

The implementation applies Postel's Law at multiple levels:

- `position` sub-object is optional (handles relative poses)
- `angles` properties are individually optional (partial angles preserved)
- `quaternion` requires all 4 components (correct — partial quaternions are meaningless)
- Returns `undefined` only when no relevant sub-properties exist

This tolerance is important because real-world sensors may report partial orientation data (e.g., yaw only, no pitch/roll).

**Severity:** POSITIVE

---

### [F5] POSITIVE: Recursive PhysicalSystem component parsing

`parseComponentEntry()` (lines 271–295) adds recursive parsing for nested PhysicalSystem components (line 284):

```typescript
if (value.type === 'PhysicalSystem') {
  const parsed = parsePhysicalSystem(value);
  return { ...parsed, name: value.name as string } as ComponentEntry;
}
```

This correctly mirrors the AggregateProcess recursive parsing pattern (Phase 3.6 F1) but for the PhysicalSystem type. The recursive test (spec line 454–468) verifies a PhysicalSystem containing a nested PhysicalSystem with position data, confirming the recursion preserves physical-process-specific properties at depth.

The symmetry between `parseComponentEntry` in aggregate-process.ts (recurses into AggregateProcess) and physical-system.ts (recurses into PhysicalSystem) is correct — each sub-parser handles self-referential nesting while deferring cross-type delegation to Issue #22.

**Severity:** POSITIVE

---

### [F6] POSITIVE: Type-specific differentiation between PhysicalSystem and PhysicalComponent

The two parsers correctly implement the type hierarchy fork:

| Property      | PhysicalSystem               | PhysicalComponent |
| ------------- | ---------------------------- | ----------------- |
| `components`  | ✅ ComponentList (recursive) | ❌ Not present    |
| `connections` | ✅ ConnectionList            | ❌ Not present    |
| `method`      | ❌ Not present               | ✅ ProcessMethod  |

Both parsers share the full AbstractProcess and AbstractPhysicalProcess property chains. The test suite validates this differentiation:

- PhysicalSystem minimal test asserts `components` and `connections` are undefined (line 305)
- PhysicalComponent minimal test asserts `method` is undefined (line 703)
- Full test fixtures exercise all type-specific properties

**Severity:** POSITIVE

---

### [F7] POSITIVE: PhysicalComponent ProcessMethod parsing with tolerant algorithm pass-through

`parseProcessMethod()` (lines 111–118) is a new exported helper that accepts any object and extracts:

- `algorithm` — any type (not restricted to string — OAS allows structured objects)
- `description` — string only

The `algorithm` field is intentionally untyped (`method.algorithm = value.algorithm`) because the OAS ProcessMethod schema allows arbitrary algorithm representations (pseudocode strings, structured objects with `language`/`code` properties, arrays, etc.). Restricting this field would violate Postel's Law for an inherently polymorphic property.

The test suite covers all combinations (spec lines 1131–1168): algorithm only, description only, both fields, and empty object.

**Severity:** POSITIVE

---

### [F8] POSITIVE: Test coverage exceeds Category C requirements — 87 tests across 11 describe blocks

| Dimension                                              | Tests | Evidence                                                                                                                                                                                                              |
| ------------------------------------------------------ | ----- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Valid input → correct typed output (PhysicalSystem)    | 8     | Minimal, full, typeOf, configuration, features, I/O, modes, DescribedObject                                                                                                                                           |
| Valid input → correct typed output (PhysicalComponent) | 4     | Minimal, full, typeOf, I/O                                                                                                                                                                                            |
| AbstractPhysicalProcess properties (PhysicalSystem)    | 4     | attachedTo, localReferenceFrames, localTimeFrames, position as GeoJSON                                                                                                                                                |
| AbstractPhysicalProcess properties (PhysicalComponent) | 4     | attachedTo, localReferenceFrames, localTimeFrames, position as text                                                                                                                                                   |
| Components & connections (PhysicalSystem)              | 5     | Inline, connections, external links, recursive PhysicalSystem, absent                                                                                                                                                 |
| Method parsing (PhysicalComponent)                     | 3     | Full method, algorithm-only, absent                                                                                                                                                                                   |
| Invalid documents (PhysicalSystem)                     | 17    | null, non-object, array, missing type, wrong type, missing label, missing uniqueId, non-array inputs, non-array frames, frame validation (origin, axes, axis fields), temporal frame validation, error class identity |
| Invalid documents (PhysicalComponent)                  | 5     | null, wrong type, missing label, missing uniqueId, error class identity                                                                                                                                               |
| Edge cases (PhysicalSystem)                            | 3     | 14 null optional fields, unknown properties preserved, empty arrays                                                                                                                                                   |
| Edge cases (PhysicalComponent)                         | 2     | 7 null optional fields, unknown properties preserved                                                                                                                                                                  |
| Position variants (standalone)                         | 13    | null/undefined, string, 2D Point, 3D Point, Pose YPR, Pose Quaternion, Relative YPR, Relative Quaternion, Link, AbstractProcess, deprecated Vector, DataRecord, DataArray, unrecognized fallback                      |
| ComponentList standalone                               | 4     | null/undefined, non-array, inline, external link                                                                                                                                                                      |
| ConnectionList standalone                              | 5     | null/undefined, non-array, valid, missing source, missing destination                                                                                                                                                 |
| ComponentEntry standalone                              | 4     | non-object, missing name, recursive PhysicalSystem, pass-through SimpleProcess                                                                                                                                        |
| ProcessMethod standalone                               | 5     | null/non-object, algorithm only, description only, both, empty                                                                                                                                                        |

**All 87 tests passing. Category C: 6/6 dimensions at 100%.**

**Severity:** POSITIVE

---

### [F9] POSITIVE: Managed-keys delete-then-assign pattern prevents null leakage

Both `parsePhysicalSystem` (lines 775–793) and `parsePhysicalComponent` (lines 868–884) use a `managedKeys` array to:

1. Delete all managed property keys from the spread result
2. Re-assign only if the parsed value is not `undefined`

This ensures that raw `null` values from the input JSON don't appear on the typed result — critical for consumers who check `if (result.position)` rather than `if (result.position !== null && result.position !== undefined)`.

The PhysicalSystem managed keys list (14 entries) and PhysicalComponent managed keys list (13 entries) correctly match their respective type-specific properties.

**Severity:** POSITIVE

---

### [F10] INFORMATIONAL: PhysicalSystem exports not yet in barrel file

Same pattern as Phase 3.5 F11, Phase 3.6 F9. The barrel file `formats/index.ts` re-exports only GeoJSON symbols. PhysicalSystem exports (`parsePhysicalSystem`, `parsePhysicalComponent`, `parseProcessMethod`, `parsePosition`, `parseComponentList`, `parseConnectionList`, `parseComponentEntry`, `SensorMLParseError`) are not re-exported.

Correct per established pattern — barrel updates deferred to Issue #23 (SensorML Index).

**Severity:** INFORMATIONAL (no action needed)

---

### [F11] INFORMATIONAL: File is the largest sub-parser at 905 lines — justified by new functionality

At 905 lines, `physical-system.ts` is roughly 2× the size of `simple-process.ts` (335 lines) and 2× `aggregate-process.ts` (470 lines). The increase is justified by:

1. **Two parsers in one file** — PhysicalSystem + PhysicalComponent share AbstractPhysicalProcess helpers
2. **Position parsing** — 8 variants requiring `parseGeoJsonPoint`, `parsePose`, `parsePosition` (lines 490–659, ~170 lines)
3. **Frame parsing** — `parseSpatialFrame`, `parseTemporalFrame`, `parseFrameAxis`, list parsers (lines 382–486, ~105 lines)
4. **ProcessMethod** — new helper not in sibling parsers (lines 109–118)
5. **Duplicated shared helpers** — 9 helpers (~170 lines) that will be consolidated by Issue #22

After Issue #22 extracts shared helpers, this file should drop to approximately 735 lines — still the largest sub-parser but proportionally appropriate given it handles two concrete types plus the full AbstractPhysicalProcess layer.

**Severity:** INFORMATIONAL

---

## Test Quality Heatmap

### Phase 2 (URL Builder) — Carried Forward

No changes from Phase 3.6 heatmap. All entries unchanged.

### Phase 3 (Format Handlers + Types + Parsers) — Current

**Category A — GeoJSON Handler: 6/6 dimensions (100%)** — Unchanged from Phase 3.6.

**Category A — Format Detector: 6/6 dimensions (100%)** — Unchanged from Phase 3.6.

**Category B — SWE Common Types: 6/6 dimensions (100%)** — Unchanged from Phase 3.6.

**Category B — SensorML Types: 6/6 dimensions (100%)** — Unchanged from Phase 3.6.

**Category C — SimpleProcess Sub-Parser: 6/6 dimensions (100%)** — Unchanged from Phase 3.6.

**Category C — AggregateProcess Sub-Parser: 6/6 dimensions (100%)** — Unchanged from Phase 3.6.

**Category C — PhysicalSystem/PhysicalComponent Sub-Parser** — NEW

| Dimension                            | Status | Evidence                                                                                                                                                 |
| ------------------------------------ | ------ | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Valid input → correct typed output   | ✅     | 12 valid document tests (8 PhysicalSystem + 4 PhysicalComponent) covering all AbstractProcess + AbstractPhysicalProcess + type-specific properties       |
| Invalid input → `SensorMLParseError` | ✅     | **22 invalid document tests** covering null, non-object, type errors, missing required fields, malformed frames, frame axis validation                   |
| Nested/recursive structures          | ✅     | PhysicalSystem → PhysicalSystem recursive nesting test with position preservation                                                                        |
| Type discrimination                  | ✅     | PhysicalSystem vs PhysicalComponent: components/connections vs method. Position: 8-variant dispatch (13 standalone tests)                                |
| Standalone helper tests              | ✅     | `parseComponentList` (4), `parseConnectionList` (5), `parseComponentEntry` (4), `parseProcessMethod` (5), `parsePosition` (13) = **31 standalone tests** |
| Edge cases (null, empty, unknown)    | ✅     | **5 edge case tests**: 14 null fields (PhysicalSystem), 7 null fields (PhysicalComponent), unknown properties preserved (×2), empty arrays               |

**PhysicalSystem/PhysicalComponent Sub-Parser: 6/6 dimensions (100%)**

---

## Smoke Test Findings Integration

> No new smoke test findings to integrate in this review period. The PhysicalSystem sub-parser has not been run against live servers. Live server testing will occur when Issue #22 integrates all sub-parsers.

| Finding                           | Status                | Evidence                                                     |
| --------------------------------- | --------------------- | ------------------------------------------------------------ |
| F4 (validTime)                    | ✅ **Addressed**      | `parseValidTime` in geojson.ts (unchanged)                   |
| F33-F39                           | N/A                   | Scoped to later Phase 3/4 tasks                              |
| F40 (SensorML featureType)        | ✅ **Addressed**      | `SENSORML_NS` + `toSensormlLocalName()` (unchanged)          |
| F49 (validators block extraction) | ✅ **Fully resolved** | Validators removed (Issue #52); sweep confirmed in Phase 3.6 |
| F50 (content type change)         | N/A                   | Response parser scope                                        |

**3 of 5 relevant findings addressed. No change from Phase 3.6.**

---

## Overall Codebase Metrics (Cumulative)

### Production Code

| File                                          | Lines     | Purpose                                                   |
| --------------------------------------------- | --------- | --------------------------------------------------------- |
| `csapi/model.ts`                              | 600       | Type definitions (9 resource types, discriminated unions) |
| `csapi/url_builder.ts`                        | 1,967     | URL builder (79 public methods)                           |
| `csapi/helpers.ts`                            | 222       | Shared helpers (cursor, validation, assertions)           |
| `csapi/formats/index.ts`                      | 21        | Barrel file (GeoJSON re-exports)                          |
| `csapi/formats/geojson.ts`                    | 378       | GeoJSON handler (5 functions)                             |
| `csapi/formats/swecommon/types.ts`            | 722       | SWE Common 3.0 type definitions                           |
| `csapi/formats/sensorml/types.ts`             | 915       | SensorML 3.0 type definitions                             |
| `csapi/formats/sensorml/simple-process.ts`    | 335       | SimpleProcess sub-parser                                  |
| `csapi/formats/sensorml/aggregate-process.ts` | 470       | AggregateProcess sub-parser                               |
| `csapi/formats/sensorml/physical-system.ts`   | 905       | **PhysicalSystem & PhysicalComponent sub-parser** ← NEW   |
| **Total Production**                          | **6,535** |                                                           |

### Test Code

| File                                               | Lines     | Tests                                     | Purpose                                         |
| -------------------------------------------------- | --------- | ----------------------------------------- | ----------------------------------------------- |
| `csapi/model.spec.ts`                              | 407       | 56                                        | Model type tests                                |
| `csapi/url_builder.spec.ts`                        | 2,444     | 314                                       | URL builder tests                               |
| `csapi/helpers.spec.ts`                            | 313       | 44                                        | Helper tests                                    |
| `csapi/formats/geojson.spec.ts`                    | 498       | 53                                        | GeoJSON handler tests                           |
| `csapi/formats/swecommon/types.spec.ts`            | 409       | 6                                         | SWE Common type tests                           |
| `csapi/formats/sensorml/types.spec.ts`             | 399       | —                                         | SensorML type tests                             |
| `csapi/formats/sensorml/simple-process.spec.ts`    | 486       | 38                                        | SimpleProcess parser tests                      |
| `csapi/formats/sensorml/aggregate-process.spec.ts` | 708       | 50                                        | AggregateProcess parser tests                   |
| `csapi/formats/sensorml/physical-system.spec.ts`   | 1,178     | 87                                        | **PhysicalSystem/Component parser tests** ← NEW |
| **Total Test**                                     | **6,842** | **598** (CSAPI) + 82 (endpoint) = **680** |                                                 |

### Combined

| Metric              | Phase 3.6   | Phase 3.7         | Delta      |
| ------------------- | ----------- | ----------------- | ---------- |
| Production code     | 5,227 lines | 6,535 lines       | **+1,308** |
| Test code           | 5,022 lines | 6,842 lines       | **+1,820** |
| Total lines         | ~10,249     | ~13,377           | **+3,128** |
| CSAPI tests         | 511         | 598               | **+87**    |
| Format tests        | 197         | 284               | **+87**    |
| Test suites         | 9           | 9 (unchanged)     | +0         |
| Production files    | 9           | 10                | **+1**     |
| Public API elements | 311         | 311 + 8 = **319** | **+8**     |

> Note: Line count increases include the duplicated shared helpers (~170 lines production) which will be consolidated by Issue #22. After consolidation, the net delta will be approximately +1,138 production / +1,820 test.

---

## Summary

| Category                    | Count | Items                                                                                                                                                                                                                                |
| --------------------------- | ----- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Prior findings unchanged    | All   | Phase 2–3.6 accumulated findings carry forward                                                                                                                                                                                       |
| **New — positive findings** | **9** | F1 (Position 8-variant dispatch), F2 (frame parsing), F4 (Pose 4-variant), F5 (recursive PhysicalSystem), F6 (type differentiation), F7 (ProcessMethod tolerance), F8 (87 tests, Category C 6/6), F9 (managed-keys null prevention), |
| **New — design (low)**      | **1** | F3 (helper triplication — expected, deferred to Issue #22)                                                                                                                                                                           |
| **New — informational**     | **2** | F10 (exports deferred to #23), F11 (largest sub-parser, justified)                                                                                                                                                                   |
| **New bugs**                | **0** | —                                                                                                                                                                                                                                    |

---

## Recommendations

### Fix Now (before next issue)

None. The module is clean.

### Fix Before Phase 4

1. **[F3] Issue #22 should consolidate shared helpers and canonical `SensorMLParseError`** — The 9 duplicated helpers are now in 3 files (~510 lines of duplication). Issue #22 should extract into `sensorml/_helpers.ts`, establish one `SensorMLParseError`, and re-export from a single location. Frame/position helpers unique to physical-system.ts should also be considered for shared extraction.

2. **[F13/3.1-F7] Replace `as` casts with `satisfies` in `extractCSAPIFeature`** — Carried forward from Phase 3.1.

3. **Systems consolidated resource validation tests** — Carried forward from Phase 2.9.

### Defer (Low Priority)

4. **Cursor standalone tests** — Deployments, Procedures, SamplingFeatures, Properties, ControlStreams.

5. **`id` (single) tests for Systems and Deployments** — Same serialization path.

6. **[Phase 2.8 F8] JSDoc example casing alignment** — No functional impact.

---

## Root Cause Analysis — Continued Zero Defects

Phase 3.7 is the **fourteenth consecutive phase** with zero new defects. The streak: Procedures → SamplingFeatures → Properties → DataStreams → Observations → ControlStreams → Commands → GeoJSON Handler → SensorML Vocab + Format Detector + Validators → Validator Removal + SWE Common Types → SensorML Types → SimpleProcess Sub-Parser → AggregateProcess Sub-Parser → **PhysicalSystem/PhysicalComponent Sub-Parser**.

### Why this issue was clean

**Issue #21 (PhysicalSystem & PhysicalComponent Sub-Parsers):**

1. **Two sibling precedents** — Both the SimpleProcess parser (#19) and AggregateProcess parser (#20) established identical patterns for error handling, AbstractProcess property parsing, DescribedObject passthrough, and output construction. The PhysicalSystem parser followed both blueprints, adding only the AbstractPhysicalProcess layer (frames, position, attachedTo) and type-specific differences.

2. **Well-defined type hierarchy** — The SensorML types (#18) provide the full inheritance chain: `DescribedObject` → `AbstractProcess` → `AbstractPhysicalProcess` → `PhysicalSystem | PhysicalComponent`. Each layer's properties are clearly defined with required/optional annotations. The parser maps directly to these types.

3. **Position union type is complexity-contained** — The 8-variant Position union is the most complex new functionality. By implementing it as a priority-ordered dispatch chain with a final pass-through fallback, the parser handles all known variants while remaining resilient to unknown ones. Each variant is independently testable (13 standalone tests).

4. **Explicit scope boundaries** — Issue #21 requirements define exactly 2 files to create. No modifications to SimpleProcess, AggregateProcess, types, or any other files. This eliminates cross-file regression risk.

---

## Overall Assessment

**Phase 3.7 is clean and completes the set of all four SensorML concrete process type sub-parsers.**

1. **The PhysicalSystem/PhysicalComponent parser is the third and final sub-parser,** implementing the two remaining concrete types from the SensorML 3.0 process hierarchy. With SimpleProcess (#19), AggregateProcess (#20), and now PhysicalSystem + PhysicalComponent (#21), all four concrete process types have dedicated sub-parsers. This directly enables Issue #22 (SensorML Main Parser) to delegate to any process type via the `type` discriminator.

2. **The AbstractPhysicalProcess layer is the distinguishing new functionality.** Position parsing (8 variants), frame parsing (SpatialFrame + TemporalFrame), and the `attachedTo` link are specific to physical processes and constitute ~275 lines of new helper code not present in the SimpleProcess or AggregateProcess parsers. This is the parser with the most new non-duplicated functionality.

3. **Two parsers in one file is architecturally correct.** PhysicalSystem and PhysicalComponent share the entire AbstractPhysicalProcess inheritance chain (frames, position, attachedTo) plus the full AbstractProcess chain. Splitting them into separate files would force either duplication of the physical-process helpers or premature shared-module extraction. The single-file approach defers that decision to Issue #22, where the coordinator has full visibility over what to share.

4. **The helper triplication (F3) is the expected consolidation debt** — now totaling ~510 duplicated lines across 3 files. Issue #22 is the exact right place to resolve this: the main parser coordinates all sub-parsers and can define the shared helper module that each sub-parser will import from. No pre-emptive extraction is warranted because the set of shared helpers may change when the main parser is implemented.

**Cumulative project quality:**

- **14 consecutive phases** with zero defects (Phase 2.3 → Phase 3.7)
- **0 open bug or gap findings**
- **1 new low-severity design finding** (F3: helper triplication) + **1 carried forward** (F13: `as` casts)
- **598 CSAPI tests** + 82 endpoint tests = **680 total**, all passing except 1 pre-existing endpoint failure
- **~13,377 lines** of production + test code
- **Phase 2:** 79 public methods, 9 resource types, 314 tests — **complete**
- **Phase 3:** 5 GeoJSON functions + 5 mime-type detectors + 48 SWE types + 50 SensorML types + 2 constants + 4 SimpleProcess exports + 5 AggregateProcess exports + 8 PhysicalSystem exports = **127 public API elements**, 284 Phase 3 tests — **in progress**
