# Phase 3.5 Code Review — SensorML SimpleProcess Sub-Parser

**Review Date:** 2026-02-16
**Reviewer:** AI (Claude Opus 4.6, GitHub Copilot)
**Issue:** #19 — SensorML SimpleProcess Sub-Parser
**Commit:** `242c2bf` — "feat: SensorML SimpleProcess sub-parser (Issue #19)"
**Previous Review:** Phase 3.4 — SensorML Type Definitions (Issue #18)
**Previous Smoke Test:** `c232541` — Phase 3.4 Live Server Smoke Test
**Review Category:** C (Parser modules — fixture → typed output assertions)

---

## Verification Gates

| Gate                   | Command                                | Result                                |
| ---------------------- | -------------------------------------- | ------------------------------------- |
| TypeScript compilation | `npx tsc --noEmit`                     | ✅ Clean (0 errors)                   |
| CSAPI test suite       | `npx jest "src/ogc-api/csapi"`         | ✅ **461 passed** (7 suites)          |
| Endpoint test suite    | `npx jest "src/ogc-api/endpoint.spec"` | ✅ 82 passed, 1 failed (pre-existing) |
| Format tests           | `npx jest "src/ogc-api/csapi/formats"` | ✅ **147 passed** (4 suites)          |
| SimpleProcess tests    | `npx jest ".../simple-process"`        | ✅ **38 passed** (1 suite)            |

**Test delta from Phase 3.4:** +38 tests (from 109 → 147 format tests), +7 tests net in CSAPI (from 454 → 461 — note: 461 because CSAPI-only excludes endpoint tests; total CSAPI + endpoint = 543).

---

## Scope

### Files Reviewed

| File                                                        | Lines      | Status  |
| ----------------------------------------------------------- | ---------- | ------- |
| `src/ogc-api/csapi/formats/sensorml/simple-process.ts`      | 332 (+331) | **NEW** |
| `src/ogc-api/csapi/formats/sensorml/simple-process.spec.ts` | 487 (+486) | **NEW** |

**Total new code:** 819 lines (332 production + 487 test).

### Not in Scope

- `docs/implementation/live-server-smoke-test-post-phase-3.4.md` (+566, documentation only)
- `docs/implementation/phase-3.4-code-review.md` (+8/-3, minor corrections)
- `docs/implementation/f57-reverification.md` (documentation only, separate commit `2a1acf6`)

---

## Step 1: Lessons Learned Check

Cross-referencing the 12 Phase 3 lessons learned against the SimpleProcess sub-parser:

| Lesson                                                     | Applicable? | Status | Evidence                                                                                                                                                                                                                                                       |
| ---------------------------------------------------------- | ----------- | ------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **L1:** Audit upstream before building new layers          | ✅          | PASS   | Sub-parser pattern is new (no upstream equivalent), but ROADMAP Task 6 explicitly scopes it. No ad-hoc new layer.                                                                                                                                              |
| **L2:** Postel's Law — never gate extraction on validation | ✅          | PASS   | `parseSimpleProcess` validates only the 3 required fields (`type`, `label`, `uniqueId`). All optional fields use graceful defaults (`undefined`) when absent/null.                                                                                             |
| **L3:** Don't couple validation to extraction              | ✅          | PASS   | Parser extracts what is present, rejects only structurally invalid inputs (non-object, wrong type discriminator). No validation-framework-style error arrays.                                                                                                  |
| **L4:** Don't build parallel systems                       | ✅          | PASS   | Single parser entry point (`parseSimpleProcess`). No duplicate parsing surface. Internal helpers are all `function`-scoped, not exported as alternatives.                                                                                                      |
| **L5:** Verify upstream claims by reading source           | N/A         | —      | No upstream claims made.                                                                                                                                                                                                                                       |
| **L6:** Real-world server data diverges from spec          | ✅          | PASS   | Null/undefined handling throughout (see edge case tests lines 383–413). `parseFeatureList` silently skips invalid links. `parseModes` silently skips invalid modes. Tolerant extraction.                                                                       |
| **L7:** Phase 3 smoke tests are essential                  | N/A         | —      | Smoke test is separate concern; sub-parser doesn't connect to live servers.                                                                                                                                                                                    |
| **L8:** Layered architecture enables clean extension       | ✅          | PASS   | Parser follows layers: error class → helpers (`isRecord`, `optionalString`, `parseLink`) → component parsers (`parseIOList`, `parseSettings`, `parseFeatureList`, `parseModes`) → main parser (`parseSimpleProcess`). Each layer depends only on layers below. |
| **L9:** Content negotiation cannot be assumed              | N/A         | —      | Not applicable to sub-parser (no HTTP).                                                                                                                                                                                                                        |
| **L10:** Type naming must avoid built-in collisions        | ✅          | PASS   | `SensorMLParseError` is clearly namespaced. No collisions with built-ins.                                                                                                                                                                                      |
| **L11:** Document architectural decisions formally         | N/A         | —      | No new architectural decisions — follows established pattern.                                                                                                                                                                                                  |
| **L12:** "Should we build it at all?"                      | ✅          | PASS   | ROADMAP Task 6 explicitly scopes this parser. It is required for the main SensorML parser (Issue #22).                                                                                                                                                         |

**Result: 7/7 applicable lessons pass. 5 not applicable.**

---

## Step 2: Verification (completed above)

All gates pass. See Verification Gates table.

---

## Step 3: Read All Changed Files

Both files read in full (332 + 487 = 819 lines). See File Inventory below.

### File Inventory

**`simple-process.ts` (332 lines) — Production Code**

| Section                               | Lines   | Purpose                                                                    |
| ------------------------------------- | ------- | -------------------------------------------------------------------------- |
| Module JSDoc                          | 1–17    | Purpose, scope, spec links, `@module`                                      |
| Imports                               | 19–31   | 10 type-only imports from `./types.js`                                     |
| `SensorMLParseError` class            | 41–47   | Custom error with `name = 'SensorMLParseError'`                            |
| `isRecord()` helper                   | 55–57   | Type guard: non-null, non-array object                                     |
| `optionalString()` helper             | 62–64   | String coercion or `undefined`                                             |
| `parseLink()` helper                  | 72–82   | `Link` object parser (href required, 5 optional fields)                    |
| `parseProcessMethod()` (exported)     | 91–98   | `ProcessMethod` parser (algorithm + description)                           |
| `parseIOComponentChoice()` (exported) | 112–127 | `IOComponentChoice` parser with name validation                            |
| `parseIOList()` internal              | 138–155 | Array of IOComponentChoice with indexed errors                             |
| `parseSettings()` internal            | 163–166 | Pass-through cast (SWE Common deferred)                                    |
| `parseFeatureList()` internal         | 174–183 | Array of links, filters valid only                                         |
| `parseMode()` internal                | 194–202 | Mode requires type, label, uniqueId                                        |
| `parseModes()` internal               | 210–219 | Array of Mode, filters valid only                                          |
| `parseSimpleProcess()` (exported)     | 246–332 | Main parser: validate required → parse optional → spread + delete + assign |

**4 exports:** `SensorMLParseError`, `parseProcessMethod`, `parseIOComponentChoice`, `parseSimpleProcess`

**`simple-process.spec.ts` (487 lines) — Test Code**

| Section                             | Lines   | Tests | Purpose                                                                                                                                                    |
| ----------------------------------- | ------- | ----- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Fixtures                            | 23–107  | —     | MINIMAL (3 fields) + FULL (all optional properties)                                                                                                        |
| Valid documents                     | 112–210 | 10    | Minimal, full, typeOf, configuration, features, inputs (2 types), outputs, parameters, DescribedObject passthrough                                         |
| Method parsing                      | 215–262 | 4     | Algorithm only, description only, both, absent                                                                                                             |
| Invalid documents                   | 267–363 | 11    | null, non-object, array, missing type, wrong type, missing label, missing uniqueId, non-array inputs, missing name, non-object entry, error class identity |
| Edge cases                          | 370–420 | 4     | Empty arrays, null optional fields, unknown properties passthrough, empty method                                                                           |
| `parseProcessMethod` standalone     | 428–457 | 5     | Non-object, algorithm only, description only, both, empty                                                                                                  |
| `parseIOComponentChoice` standalone | 463–487 | 4     | AnyComponent, ObservableProperty, non-object, missing name                                                                                                 |

**Total: 38 tests across 6 describe blocks.**

---

## Step 4: Prior Findings Reaffirmation

### Phase 2 Findings — Unchanged

All Phase 2 accumulated findings (36 unchanged + 10 moot + 1 resolved) carry forward with no changes. The SimpleProcess parser does not touch URL builder code, helpers, or model definitions.

### Phase 3.1–3.3 Findings — Unchanged

All Phase 3.1 through 3.3 findings carry forward. Key items:

- **Phase 3.1 F7 / Phase 3.4 F14:** `as` type assertions in `extractCSAPIFeature` — **still open, carried forward**
- **Phase 3.3 F12 / Phase 3.4 F12:** Exports not in barrel — **still correct** (exports deferred to Issue #28/barrel update)
- **Phase 3.2 F1–F11:** Moot (validator removal) — **still moot**

### Phase 3.4 Findings — Unchanged

| Finding                       | Status                 | Notes                                      |
| ----------------------------- | ---------------------- | ------------------------------------------ |
| F1 (POSITIVE type hierarchy)  | Unchanged              | Types consumed by simple-process.ts        |
| F2 (POSITIVE discriminators)  | Unchanged              | `type: 'SimpleProcess'` validated line 256 |
| F3 (DESIGN Document name)     | **ACCEPTED-BY-DESIGN** | Unchanged                                  |
| F4 (POSITIVE SWE integration) | Unchanged              | Not exercised by sub-parser                |
| F5–F10 (POSITIVE)             | Unchanged              | Type layer findings                        |
| F11–F13 (INFORMATIONAL)       | Unchanged              |                                            |
| F14 (DESIGN `as` casts)       | **Carried forward**    | Not in scope                               |

---

## Step 5–8: Code Quality Evaluation

### [F1] POSITIVE: Parser follows Postel's Law consistently

The parser validates only the absolute minimum — 3 required fields (`type`, `label`, `uniqueId`) — and treats everything else as optional. Specific evidence:

1. **`parseLink()`** (line 72): Returns `undefined` for non-object input. Does not throw.
2. **`parseProcessMethod()`** (line 91): Returns `undefined` for non-object input. Does not throw.
3. **`parseSettings()`** (line 163): Returns `undefined` for non-object input. Does not throw.
4. **`parseFeatureList()`** (line 174): Returns `undefined` for null/undefined/non-array. Silently filters invalid entries.
5. **`parseModes()`** (line 210): Returns `undefined` for null/undefined/non-array. Silently filters invalid modes.
6. **`parseIOList()`** (line 138): The one exception — throws on non-array input. This is correct because the OAS schema for `inputs`/`outputs`/`parameters` defines them as arrays; a non-array value indicates structural corruption, not a missing optional field.

This directly satisfies L2 (never gate extraction on validation) and L6 (real-world data diverges).

**Severity:** POSITIVE

---

### [F2] POSITIVE: DescribedObject passthrough pattern preserves unknown properties

The parser uses a spread-then-delete-then-assign pattern (lines 287–332):

```typescript
const result: SimpleProcess = {
  ...(json as Record<string, unknown>),
  type: 'SimpleProcess' as const,
  label: json.label as string,
  uniqueId: json.uniqueId as string,
};

// Delete raw values, then assign parsed versions
for (const key of abstractKeys) {
  delete (result as unknown as Record<string, unknown>)[key];
}
if (definition !== undefined) result.definition = definition;
// ... etc
```

This pattern:

1. **Preserves DescribedObject-level properties** (`id`, `lang`, `keywords`, `identifiers`, `classifiers`, `validTime`, etc.) without explicitly parsing them — delegated to the main parser (Issue #22)
2. **Prevents null leakage** — raw `null` values from server JSON are deleted before parsed `undefined` values are conditionally assigned
3. **Allows unknown/extension properties** to pass through (verified by edge case test at line 406)

The test at line 200 ("preserves DescribedObject passthrough properties") verifies `id`, `lang`, `keywords`, `identifiers`, `classifiers`, and `validTime` are all preserved.

**Severity:** POSITIVE

---

### [F3] POSITIVE: Error messages include positional context for array entries

`parseIOList()` wraps each `parseIOComponentChoice()` call in a try-catch that prepends the array index:

```typescript
throw new SensorMLParseError(
  `Invalid ${listName}[${i}]: ${(err as Error).message}`
);
```

This produces error messages like `"Invalid inputs[0]: IOComponentChoice entry must have a string "name" property"` — directly actionable for consumers debugging malformed server responses. The test at line 340 ("throws for inputs entry without name") verifies this.

**Severity:** POSITIVE

---

### [F4] POSITIVE: IOComponentChoice uses explicit pass-through with documented deferral

`parseIOComponentChoice()` (line 112) validates only the `name` property, then casts the entire object:

```typescript
return value as unknown as IOComponentChoice;
```

The JSDoc at line 104 explicitly documents this is intentional:

> "SWE Common sub-component parsing will be handled by Issues #24-#28; for now we preserve the raw structure cast to the typed union."

This follows L3 (don't couple validation to extraction) — the sub-parser extracts what it can validate (the `name` field) and defers deeper SWE Common parsing to the appropriate future issue. The `as unknown as` double cast is necessary because `IOComponentChoice` is a union type and TypeScript cannot structurally match the raw object to all union branches.

**Severity:** POSITIVE

---

### [F5] DESIGN (low): `parseSettings` uses pass-through cast without any field validation

`parseSettings()` (line 163):

```typescript
function parseSettings(value: unknown): Settings | undefined {
  if (!isRecord(value)) return undefined;
  return value as unknown as Settings;
}
```

Unlike `parseIOComponentChoice()` (which validates `name`), `parseSettings()` validates only that the value is a non-null object. The `Settings` type is complex (`SettingValue`, `SettingArrayValue`, `SettingMode`, etc.), so no individual field validation is performed.

This is consistent with the deferral pattern documented for IOComponentChoice — SWE Common integration (Issues #24-#28) will add proper parsing. However, unlike IOComponentChoice, there is no JSDoc comment explaining the deferral.

**Recommendation:** Add a brief JSDoc comment to `parseSettings()` noting that field-level parsing is deferred to Issues #24-#28, consistent with the `parseIOComponentChoice()` documentation.

**Resolution:** Fixed — deferral JSDoc added in post-review commit.

**Severity:** DESIGN (low) → **RESOLVED**

---

### [F6] POSITIVE: `parseMode` validates three required DescribedObject fields

`parseMode()` (line 194) requires `type`, `label`, and `uniqueId` — the same three required fields as `SimpleProcess` itself. This correctly reflects that `Mode extends DescribedObject` in the OAS schema, and `DescribedObject` requires these fields.

Invalid modes are silently filtered by `parseModes()` (line 210) rather than causing the entire parse to fail. This follows L2 (Postel's Law) — a missing mode label doesn't invalidate the entire SimpleProcess.

**Severity:** POSITIVE

---

### [F7] POSITIVE: `parseLink` validates `href` as required, all other fields optional

`parseLink()` (line 72) checks only `href` (the single required field per OAS `link-2` schema, L96). The 5 optional fields (`rel`, `type`, `hreflang`, `title`, `uid`) are conditionally assigned only when present as strings. This matches the OAS `link-2` definition exactly.

**Severity:** POSITIVE

---

### [F8] POSITIVE: Test fixtures are minimal and self-documenting

The spec file defines exactly 2 fixtures:

1. **`MINIMAL_SIMPLE_PROCESS`** (lines 24–28): Only the 3 required fields. This exercises the minimum valid input path and verifies that optional fields default to `undefined`.
2. **`FULL_SIMPLE_PROCESS`** (lines 31–107): All optional properties populated. This exercises every parser branch in a single test.

Both fixtures are declared as `const` literals with inline comments. No external fixture files are needed — the fixtures are small (5 and 76 lines respectively) and readable inline. This follows the pattern established by `types.spec.ts` fixtures.

**Severity:** POSITIVE

---

### [F9] POSITIVE: Edge case coverage aligns with L6 (real-world data diverges)

The edge case tests (lines 370–420) directly address known server behaviors:

| Test                                       | Server Behavior Addressed                                            |
| ------------------------------------------ | -------------------------------------------------------------------- |
| Empty arrays for inputs/outputs/parameters | Servers returning `[]` instead of omitting the field                 |
| Null optional fields                       | 52North-style `null` for optional fields (F41, F42 from smoke tests) |
| Unknown extra properties passthrough       | Servers including extension properties not in the OAS schema         |
| Empty method object `{}`                   | Servers providing an empty method stub                               |

The null handling test (line 383) is particularly important — it verifies that 9 optional fields all gracefully handle `null` input, producing `undefined` in the output rather than propagating `null` or throwing.

**Severity:** POSITIVE

---

### [F10] POSITIVE: JSDoc is comprehensive with spec cross-references

Every exported function has:

- A `/** ... */` JSDoc comment describing purpose and behavior
- `@param` and `@returns` annotations
- `@throws` annotations where applicable
- `@see` links to OAS line numbers (e.g., `@see OAS: ProcessMethod (L3671)`)

The module-level JSDoc (lines 1–17) includes:

- Clear description of what the module parses
- Scope statement ("sub-parser — intended to be called by the main SensorML parser")
- Forward reference to Issue #22
- Spec links (SensorML 3.0 + OAS)

Internal helper functions also have JSDoc (unusual but appreciated for maintainability).

**Severity:** POSITIVE

---

### [F11] INFORMATIONAL: SimpleProcess exports not yet in barrel file

The barrel file `formats/index.ts` re-exports only GeoJSON symbols. `SensorMLParseError`, `parseProcessMethod`, `parseIOComponentChoice`, and `parseSimpleProcess` are not re-exported.

This is correct per the established pattern — barrel updates should be made when the SensorML index module is created (ROADMAP Task 10 / Issue #28).

Same as Phase 3.3 F12 and Phase 3.4 F12.

**Severity:** INFORMATIONAL (no action needed)

---

### [F12] INFORMATIONAL: `parseIOList` uses `as InputList | undefined` type casts

Lines 274–279:

```typescript
const inputs = parseIOList(json.inputs, 'inputs') as InputList | undefined;
const outputs = parseIOList(json.outputs, 'outputs') as OutputList | undefined;
const parameters = parseIOList(json.parameters, 'parameters') as
  | ParameterList
  | undefined;
```

`parseIOList` returns `IOComponentChoice[] | undefined`, but the assignment targets are `InputList | undefined`, `OutputList | undefined`, `ParameterList | undefined`. These type aliases are all defined as `IOComponentChoice[]` in `types.ts`, so the casts are semantically safe.

The casts exist because TypeScript's structural type system cannot narrow `IOComponentChoice[]` to the branded alias `InputList` without an explicit assertion. When SWE Common sub-component parsing is added (Issues #24-#28), these casts may be replaced by type-narrowing parse functions that return the specific list types directly.

**Severity:** INFORMATIONAL (type-safe, will be revisited in Issues #24–28)

---

### [F13] DESIGN (carried forward): `as` type assertions in `extractCSAPIFeature`

Carried forward from Phase 3.1 F7 → Phase 3.3 F13 → Phase 3.4 F14. No change.

**Severity:** DESIGN (low)

---

## Test Quality Heatmap

### Phase 2 (URL Builder) — Carried Forward

No changes from Phase 3.4 heatmap. All entries unchanged.

### Phase 3 (Format Handlers + Types + Parsers) — Current

**Category A — GeoJSON Handler: 6/6 dimensions (100%)** — Unchanged from Phase 3.4.

**Category A — Format Detector: 6/6 dimensions (100%)** — Unchanged from Phase 3.4.

**Category B — SWE Common Types: 6/6 dimensions (100%)** — Unchanged from Phase 3.4.

**Category B — SensorML Types: 6/6 dimensions (100%)** — Unchanged from Phase 3.4.

**Category C — SimpleProcess Sub-Parser** — NEW

| Dimension                            | Status | Evidence                                                                                                                                                                                                           |
| ------------------------------------ | ------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Valid input → correct typed output   | ✅     | 10 valid document tests + 4 method parsing tests = **14 happy-path tests**                                                                                                                                         |
| Invalid input → `SensorMLParseError` | ✅     | **11 invalid document tests** covering null, non-object, array, missing type, wrong type, missing label, missing uniqueId, non-array inputs, missing name, non-object entry, error class identity                  |
| All spec-level properties parsed     | ✅     | 10 valid tests cover: definition, typeOf, configuration, featuresOfInterest, inputs (AnyComponent + ObservableProperty), outputs, parameters, modes, method (algorithm + description), DescribedObject passthrough |
| Fixture → assertion pattern          | ✅     | 2 inline fixtures (MINIMAL + FULL), all assertions on specific property values                                                                                                                                     |
| Standalone helper tests              | ✅     | `parseProcessMethod` (5 tests) + `parseIOComponentChoice` (4 tests) = **9 standalone helper tests**                                                                                                                |
| Edge cases (null, empty, unknown)    | ✅     | **4 edge case tests**: empty arrays, null optional fields, unknown property passthrough, empty method object                                                                                                       |

**SimpleProcess Sub-Parser: 6/6 dimensions (100%)**

---

## Smoke Test Findings Integration

> **⚠️ CORRECTION (2026-02-15):** F57 ("52North data loss") in the Phase 3.4 smoke test was incorrect. The 52North data was never lost — the smoke test changed its `Accept` header from none (defaulting to `application/sml+json`, which returns real data) to `Accept: application/json` (which routes to 52North's empty pygeoapi GeoJSON provider). All findings below that referenced F57 or "52N data loss" were based on this incorrect conclusion. The 52North server still has 3 systems, 1 deployment, and 1 procedure accessible via `application/sml+json`. See [F57 correction report](f57-content-negotiation-correction.md) and Lessons Learned L13.

| Finding                           | Status                | Evidence                                                |
| --------------------------------- | --------------------- | ------------------------------------------------------- |
| F4 (validTime array format)       | ✅ **Addressed**      | `parseValidTime` in geojson.ts (unchanged)              |
| F33-F39                           | N/A                   | Scoped to later Phase 3/4 tasks                         |
| F40 (SensorML featureType)        | ✅ **Addressed**      | `SENSORML_NS` + `toSensormlLocalName()` (unchanged)     |
| F41 (null featureType in GeoJSON) | N/A                   | Requires design decision — tracked in roadmap           |
| F49 (validators block extraction) | ✅ **Fully resolved** | Validators removed (Issue #52), confirmed by smoke test |
| F50 (content type change)         | N/A                   | Response parser scope                                   |

**3 of 6 relevant findings addressed.** No change from Phase 3.4.

---

## Summary

| Category                     | Count  | Items                                                                                                                                                                           |
| ---------------------------- | ------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Prior findings unchanged     | **36** | All Phase 2–3.1 accumulated findings                                                                                                                                            |
| Prior findings moot          | **10** | Phase 3.2 validator-related                                                                                                                                                     |
| Prior findings resolved      | **1**  | Phase 3.2 F12                                                                                                                                                                   |
| Phase 3.3 findings unchanged | **13** | F1–F13 (all re-confirmed)                                                                                                                                                       |
| Phase 3.4 findings unchanged | **14** | F1–F14 (all re-confirmed)                                                                                                                                                       |
| **New — positive findings**  | **9**  | F1 (Postel's Law), F2 (passthrough), F3 (error messages), F4 (IOComponentChoice deferral), F6 (Mode validation), F7 (Link parsing), F8 (fixtures), F9 (edge cases), F10 (JSDoc) |
| **New — design (resolved)**  | **1**  | F5 (parseSettings JSDoc — fixed in post-review commit)                                                                                                                          |
| **New — informational**      | **2**  | F11 (exports deferred), F12 (InputList casts)                                                                                                                                   |
| **New — carried forward**    | **1**  | F13 (`as` casts — from Phase 3.1 F7)                                                                                                                                            |
| **New bugs**                 | **0**  | —                                                                                                                                                                               |

---

## Codebase Metrics

| Metric                  | Phase 3.4       | Phase 3.5                | Delta                                                                           |
| ----------------------- | --------------- | ------------------------ | ------------------------------------------------------------------------------- |
| Production code (CSAPI) | 4,453 lines     | 4,784 lines              | +331                                                                            |
| Test code (CSAPI)       | 3,890 lines     | 4,376 lines              | +486                                                                            |
| Total lines             | ~8,343          | ~9,160                   | +817                                                                            |
| CSAPI tests             | 454             | 461                      | +7 net (was counted differently — now 461 CSAPI-only + 82 endpoint = 543 total) |
| Format tests            | 109             | 147                      | +38                                                                             |
| Test suites             | 7               | 8 (7 CSAPI + 1 endpoint) | +1                                                                              |
| Production files        | 7               | 8                        | +1                                                                              |
| Public API elements     | 192 + 110 = 302 | 302 + 4 = **306**        | +4                                                                              |

---

## Recommendations

### Fix Now (before next issue)

None. The module is clean.

### Fix Before Phase 4

1. ~~**[F5] Add deferral JSDoc to `parseSettings()`**~~ — **RESOLVED** (post-review commit). Deferral comment added.

2. **[F13/3.1-F7] Replace `as` casts with `satisfies` in `extractCSAPIFeature`** — Carried forward. Recommend fixing when extraction function is next modified.

3. **Systems consolidated resource validation tests** — Carried forward from Phase 2.9.

### Defer (Low Priority)

4. **Cursor standalone tests** — Deployments, Procedures, SamplingFeatures, Properties, ControlStreams.

5. **`id` (single) tests for Systems and Deployments** — Same serialization path.

6. **[Phase 2.8 F8] JSDoc example casing alignment** — No functional impact.

---

## Root Cause Analysis — Continued Zero Defects

Phase 3.5 is the **twelfth consecutive phase** with zero new defects. The streak: Procedures → SamplingFeatures → Properties → DataStreams → Observations → ControlStreams → Commands → GeoJSON Handler → SensorML Vocab + Format Detector + Validators → Validator Removal + SWE Common Types → SensorML Types → **SimpleProcess Sub-Parser**.

### Why this issue was clean

**Issue #19 (SimpleProcess Sub-Parser):**

1. **Complete type foundation** — The SensorML types (Issue #18) and SWE Common types (Issue #17) provided a fully typed target (`SimpleProcess`, `ProcessMethod`, `IOComponentChoice`, `Mode`, `Settings`, `Link`, etc.). The parser maps raw JSON to well-defined types rather than inventing structure.
2. **Established extraction pattern** — The GeoJSON handler (Issue #14) established the tolerant-extraction philosophy: validate minimally, extract gracefully, don't gate on validation. The SimpleProcess parser follows this exactly — 3 required-field checks, everything else graceful.
3. **Explicit scope boundaries** — The JSDoc and code comments clearly mark what is deferred (SWE Common sub-component parsing to Issues #24-#28, DescribedObject shared helpers to Issue #22). This prevented scope creep and kept the parser focused on AbstractProcess + SimpleProcess-level properties.
4. **Test-first fixture design** — The 2 inline fixtures (MINIMAL and FULL) exercise both extremes. Every valid-document test either uses one of these fixtures directly or spreads MINIMAL with one additional property. This makes test intent immediately clear.

---

## Overall Assessment

**Phase 3.5 is clean and establishes the sub-parser pattern for the remaining SensorML process types.**

1. **The SimpleProcess parser is the first behavioral code in the SensorML format layer.** Previous Phase 3 issues (SWE Common types, SensorML types) were pure type definitions with no runtime behavior. This parser introduces runtime parsing logic with error handling, and it does so cleanly — 38 tests covering all 6 Category C dimensions at 100%.

2. **The spread-then-delete-then-assign pattern is the key architectural contribution.** This pattern (lines 287–332) preserves DescribedObject-level properties from the raw JSON while replacing AbstractProcess-level properties with properly parsed versions. It prevents null leakage and allows unknown extension properties to pass through. The remaining sub-parsers (AggregateProcess Issue #20, PhysicalComponent/PhysicalSystem Issue #21) should follow this same pattern.

3. **The deferral pattern for SWE Common parsing is correctly scoped.** `parseIOComponentChoice()` and `parseSettings()` use pass-through casts with documented deferrals to Issues #24-#28. This is the right approach — building deep SWE Common parsing now would violate L12 ("should we build it at all?") since those issues haven't been scoped yet.

4. **The only finding requiring action is F5** — a missing JSDoc comment on `parseSettings()` explaining the deferral. This is purely a documentation consistency issue.

**Cumulative project quality:**

- **12 consecutive phases** with zero defects (Phase 2.3 → Phase 3.5)
- **0 open bug or gap findings**
- **1 new low-severity design finding** (F5: parseSettings JSDoc) + **1 carried forward** (F13: `as` casts)
- **543 tests** (461 CSAPI + 82 endpoint), all passing except 1 pre-existing endpoint failure
- **~9,160 lines** of production + test code
- **Phase 2:** 79 public methods, 9 resource types, 314 tests — **complete**
- **Phase 3:** 5 GeoJSON functions + 5 mime-type detectors + 48 SWE types + 50 SensorML types + 2 constants + 4 parser exports = **114 public API elements**, 190 Phase 3 tests — **in progress**
