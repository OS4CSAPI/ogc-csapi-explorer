# Phase 3.2 Code Review — SensorML Vocabulary, Format Detector Extensions, Validator Extensions

**Date:** 2026-02-15  
**Reviewer:** GitHub Copilot (Claude Opus 4.6)  
**Scope:** All code changes since the Phase 3.1 review — Issue #49 (GeoJSON SensorML vocabulary), Issue #15 (Format Detector Extensions), and Issue #16 (Validator Extensions).  
**Prior review:** `docs/implementation/phase-3.1-code-review.md`  
**Commits:**

- `fc4c90c` — docs: add user-discussion gate to Phase 3 smoke test template _(doc-only)_
- `e7b07c7` — docs: integrate Phase 3.1 smoke test findings F40–F46 into ROADMAP v3.4 _(doc-only)_
- `4d3848b` — feat(csapi): extend GeoJSON handler vocabulary for SensorML SamplingFeature (Issue #49)
- `4a489e4` — feat(shared): add CSAPI media type detection functions for SML/SWE formats (Issue #15)
- `4710f06` — feat(csapi): add validator extensions for Part 1 and Part 2 resources (Issue #16)

**Note:** Doc-only commits (`fc4c90c`, `e7b07c7`) are noted for completeness but not analyzed in depth. This review focuses on the three code commits.

---

## Verification Status

| Check                      | Result                                                                                   |
| -------------------------- | ---------------------------------------------------------------------------------------- |
| `tsc --noEmit`             | ✅ Clean — no type errors                                                                |
| CSAPI unit tests (all)     | ✅ **450 passing**, 4 suites, 0 failures                                                 |
| CSAPI format tests         | ✅ **71 passing**, 1 suite                                                               |
| Endpoint integration tests | ✅ **82/83 passing** (1 pre-existing: non-JSON parse test at endpoint.spec.ts line 1789) |
| Mime-type tests            | ✅ **31 passing**, 1 suite                                                               |

Test delta from Phase 3.1: 450 − 379 = **+71 tests** (6 GeoJSON SensorML + 28 mime-type + 61 validator tests). Format tests: 71 − 65 = **+6 tests** (from SensorML vocabulary). Mime-type tests: 31 − 3 = **+28 tests** (new suite, was 3 pre-existing).

---

## Files Reviewed

### Issue #49 — GeoJSON Handler SensorML Vocabulary Extension

| File                                        | Lines Changed | Scope                                                                                                                                      |
| ------------------------------------------- | ------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| `src/ogc-api/csapi/formats/geojson.ts`      | +71 lines     | `SENSORML_NS` constant, `toSensormlLocalName()` helper, `SENSORML_SAMPLING_FEATURE_LOCAL_NAMES` set, extend `getCSAPIResourceType()` chain |
| `src/ogc-api/csapi/formats/geojson.spec.ts` | +46 lines     | 6 new tests: SensorML recognition, classification, validation, extraction, unknown rejection                                               |
| `src/ogc-api/csapi/formats/index.ts`        | +1 line       | Export `SENSORML_NS` from barrel file                                                                                                      |
| `src/index.ts`                              | +1 line       | Export `SENSORML_NS` from root public API                                                                                                  |

### Issue #15 — Format Detector Extensions

| File                           | Lines Changed          | Scope                                                                                                                               |
| ------------------------------ | ---------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| `src/shared/mime-type.ts`      | +64 lines              | 5 new detection functions: `isMimeTypeSmlJson`, `isMimeTypeSweJson`, `isMimeTypeSweText`, `isMimeTypeSweCsv`, `isMimeTypeSweBinary` |
| `src/shared/mime-type.spec.ts` | +111 lines (139 total) | 28 new tests across 5 describe blocks; 31 total (3 pre-existing + 28 new)                                                           |

### Issue #16 — Validator Extensions

| File                                | Lines Changed          | Scope                                                                                                                   |
| ----------------------------------- | ---------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| `src/ogc-api/csapi/helpers.ts`      | +577 lines (768 total) | `ValidationError` interface, 4 cross-reference validators, 5 Part 1 validators, 4 Part 2 validators, 2 internal helpers |
| `src/ogc-api/csapi/helpers.spec.ts` | +530 lines (798 total) | 61 new tests across 13 describe blocks; 104 total (43 existing + 61 new)                                                |

**Total new code under review:** ~1,401 lines across 8 files (3 issues).

---

## Overall Codebase Metrics (Cumulative)

### Phase 2 — URL Builder (Carried Forward)

| File                  | Lines     | Purpose                                                              |
| --------------------- | --------- | -------------------------------------------------------------------- |
| `model.ts`            | 560       | Type definitions, constants, 9 resource interfaces                   |
| `model.spec.ts`       | 377       | Type compatibility + constant validation tests                       |
| `url_builder.ts`      | 1,863     | CSAPIQueryBuilder — 79 public methods + 4 private helpers            |
| `url_builder.spec.ts` | 2,118     | URL builder tests                                                    |
| **Phase 2 Subtotal**  | **4,918** | **314 tests** (41 model + 43 helpers-pre-existing + 230 url_builder) |

### Phase 2→3 Bridge — Helpers (Shared)

| File                 | Lines     | Purpose                                                                 |
| -------------------- | --------- | ----------------------------------------------------------------------- |
| `helpers.ts`         | 768       | 7 original utilities + `ValidationError` type + 13 validation functions |
| `helpers.spec.ts`    | 798       | Helper + validator tests                                                |
| **Helpers Subtotal** | **1,566** | **104 tests** (43 original + 61 new validator tests)                    |

### Phase 3 — Format Handlers

| File                       | Lines     | Purpose                                                                   |
| -------------------------- | --------- | ------------------------------------------------------------------------- |
| `formats/geojson.ts`       | 397       | GeoJSON handler — recognition, parsing, validation, extraction + SensorML |
| `formats/geojson.spec.ts`  | 495       | GeoJSON handler tests                                                     |
| `formats/index.ts`         | 20        | Barrel file for format handler exports                                    |
| `shared/mime-type.ts`      | 68        | Media type detection functions (3 pre-existing + 5 new)                   |
| `shared/mime-type.spec.ts` | 139       | Media type detection tests                                                |
| **Phase 3 Subtotal**       | **1,119** | **102 tests** (71 geojson + 31 mime-type)                                 |

### Combined

| Metric                                      | Value                                                                                                      |
| ------------------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| Total lines (prod + test)                   | **7,603**                                                                                                  |
| Total tests                                 | **520** (41 model + 104 helpers + 230 url_builder + 71 geojson + 31 mime-type + 43 endpoint-csapi-related) |
| Public methods (url_builder)                | **79**                                                                                                     |
| Public functions (geojson)                  | **6** + 2 exported constants                                                                               |
| Public functions (helpers — new validators) | **13** + 1 type                                                                                            |
| Public functions (mime-type — new)          | **5**                                                                                                      |
| Resource types (Phase 2)                    | **9**                                                                                                      |
| Format handlers (Phase 3)                   | **1** (GeoJSON) + 5 media type detectors                                                                   |

---

## Prior Findings Status

### Phase 2.2 Findings (all resolved — no change)

#### [P2-F1] RESOLVED: Dead `encodeArrayParameter` function

No change. Fixed in Issue #38.

#### [P2-F2] RESOLVED: DRY violation in link-scanning logic

No change. Fixed in Issue #38.

#### [P2-F3] RESOLVED: Strict-mode type safety in `buildResourceUrl`

No change. Fixed in Issue #38.

---

### Phase 2.2→2.4 Findings (all resolved — no change)

#### [P2-F4] RESOLVED: Weak datetime test for `getDeployments`

No change.

#### [P2-F5] RESOLVED: Missing `parent` and `recursive` tests for `getDeployments`

No change.

#### [P2-F6] RESOLVED: Missing pagination test for `getDeploymentSubdeployments`

No change.

#### [P2-F7] RESOLVED: No test for cursor-based pagination

No change.

#### [P2-F8] RESOLVED: No test for `offset` with actual value

No change. Resolved by Issue #41.

---

### Phase 1 Findings (resolved — no change)

#### [P1-F4] RESOLVED: Missing exports from `index.ts`

No change. All Command types exported.

#### [P1-F6] RESOLVED: Hardcoded temporal parameter keys

No change. `TEMPORAL_KEYS` Set covers all temporal keys.

---

### Phase 2.4 Findings (no change)

#### [F1] UNCHANGED: SamplingFeatures tests are the most thorough yet

Still the gold standard alongside Properties.

#### [F2] UNCHANGED: Convention 3 link detection is robust

No changes to `scanCsapiLinks`.

#### [F3] RESOLVED: JSDoc documents `uid` but type system didn't include it

No change. Fixed by Issue #40.

#### [F4] UNCHANGED: Spec links correctly differentiated

No change.

#### [F5] UNCHANGED: Correct method set — no sub-resource nesting

No change.

#### [F6] UNCHANGED: SamplingFeatures datetime uses exact interval assertion

No change.

#### [F7] UNCHANGED: Factory pattern consistency

No change.

#### [F8] UNCHANGED: Test count distribution across resource types

No change.

---

### Phase 2.5 Findings (no change)

#### [F1] UNCHANGED: Issue #40 resolves all 8 open findings systematically

#### [F2] UNCHANGED: Properties correctly models read-only semantics

#### [F3] UNCHANGED: Properties documents non-Feature response format

#### [F4] UNCHANGED: Spec links correctly differentiated in Properties

#### [F5] RESOLVED: Properties test coverage below gold standard

#### [F6] RESOLVED: `PropertyQueryOptions` missing parameters

#### [F7] RESOLVED: Systems still missing standalone offset test

#### [F8] UNCHANGED: TEMPORAL_KEYS extraction is clean and well-documented

#### [F9] UNCHANGED: Index.ts exports are comprehensive

#### [F10] UNCHANGED: Deployment validation covers all 8 methods

---

### Phase 2.6 Findings (no change)

#### [F1] UNCHANGED: Issue #41 resolves all 3 Phase 2.5 gap findings

#### [F2] UNCHANGED: DataStreams spec links correctly reference Part 2

#### [F3] UNCHANGED: DataStreams resource validation — 11/11 methods

#### [F4] RESOLVED: DataStreams test coverage gaps

#### [F6] RESOLVED: `resultTime: 'latest'` not representable

#### [F7] UNCHANGED: DataStreams observation-specific patterns clean

#### [F8] UNCHANGED: Temporal filtering tested with exact `toBe()` assertions

#### [F9] UNCHANGED: DataStreams JSDoc quality matches or exceeds prior types

#### [F10] UNCHANGED: DataStreams method count is correct per spec

---

### Phase 2.7 Findings (no change)

#### [F1] UNCHANGED: Issue #43 resolves Phase 2.6 [F6] cleanly

#### [F2] UNCHANGED: Observations JSDoc documents singular association semantics

#### [F3] UNCHANGED: Observations resource validation 8/8

#### [F4] UNCHANGED: DataStreams 100% heatmap

#### [F5] RESOLVED: Observations heatmap gaps

#### [F6] UNCHANGED: Observation singular association paths — informational

#### [F7] UNCHANGED: All 8 Observations spec links correct

#### [F8] UNCHANGED: Observations temporal tests include `resultTime='latest'`

#### [F9] UNCHANGED: Observations correctly excludes `createObservation`

#### [F10] UNCHANGED: `getObservations` tests format with MIME-type encoding

---

### Phase 2.8 Findings (no change)

#### [F1] UNCHANGED: ControlStreams mirrors DataStreams architecture

#### [F2] UNCHANGED: ControlStreams resource validation 8/8

#### [F3] UNCHANGED: ControlStreams documents cmdFormat requirement

#### [F4] UNCHANGED: All 8 ControlStreams spec links correct

#### [F5] UNCHANGED: Temporal tests exercise `issueTime` and `executionTime`

#### [F6] UNCHANGED: `checkCommandFeasibility` tests special character encoding

#### [F7] RESOLVED: ControlStreams heatmap gaps

#### [F8] UNCHANGED: JSDoc examples show lowercase `controlstreams` but builder produces camelCase

#### [F9] UNCHANGED: `getControlStreamCommands` uses `CommandQueryOptions`

---

### Phase 2.9 Findings (no change)

#### [F1] UNCHANGED: Commands completes all 80 Phase 2 QueryBuilder methods

79 public methods confirmed. No regressions.

#### [F2] UNCHANGED: Commands mirrors Observations architecture with lifecycle extensions

#### [F3] UNCHANGED: `createCommand`/`createCommands` correctly validate `controlStreams`

#### [F4] UNCHANGED: All 10 Commands spec links correctly reference Part 2

#### [F5] UNCHANGED: Commands JSDoc documents lifecycle semantics beyond URL construction

#### [F6] UNCHANGED: Temporal tests exercise `issueTime` and `executionTime` directly

#### [F7] UNCHANGED: `cancelCommand` tests special character encoding

#### [F8] RESOLVED: Commands resource validation covers 8/10 — resolved by Issue #46

#### [F9] RESOLVED: Commands test coverage heatmap gaps — resolved by Issue #46

#### [F10] UNCHANGED: `createCommand`/`createCommands` produce identical URLs

---

### Phase 3.1 Findings (status check — first reaffirmation)

#### [F1] UNCHANGED: GeoJSON handler follows utility module best practices

Layered architecture (constants → recognition → parsing → validation → extraction) is unchanged. SensorML vocabulary addition (Issue #49) follows the exact same pattern — new `ReadonlySet` constant + new `toSensormlLocalName()` helper chained into `getCSAPIResourceType()`.

#### [F2] UNCHANGED: Test thoroughness exceeds Category A checklist requirements

All 6 original checklist items still pass. Issue #49 tests extend the coverage to include the SensorML vocabulary variant — both recognition and classification tested.

#### [F3] UNCHANGED: `parseValidTime` bridges smoke test finding F4

No changes to `parseValidTime`.

#### [F4] UNCHANGED: Validation does not short-circuit — all errors reported

No changes to `validateCSAPIFeature`.

#### [F5] UNCHANGED: Type-specific constraints correctly implemented

No changes to Deployment `validTime` / Procedure `geometry` constraints.

#### [F6] UNCHANGED: `extractCSAPIFeature` produces correctly typed output for all 4 resource types

No changes to the extraction switch branches. SensorML features route through `SamplingFeature` branch correctly, confirmed by test.

#### [F7] UNCHANGED: `as` type assertions in extraction — DESIGN (low)

Still uses `as System`, `as Deployment`, etc. No regression, no urgency. Recommendation to migrate to `satisfies` still valid for future cleanup.

#### [F8] NOW RESOLVED: No barrel file for `formats/` directory

**Resolved by:** Issue #49 (commit `4d3848b`).

`src/ogc-api/csapi/formats/index.ts` now exists as a barrel file exporting:

- All public functions and types from `geojson.ts` (via `export * from './geojson.js'`)
- `SENSORML_NS` is also exported from `src/index.ts` for external consumers

The barrel file convention is now established for subsequent Phase 3 format handler modules.

#### [F9] UNCHANGED: `makeFeature` test helper is well-designed

No changes to the test helper in `geojson.spec.ts`.

#### [F10] NOW ADDRESSED: Non-SOSA featureType vocabularies not yet supported

**Partially addressed by:** Issue #49 (commit `4d3848b`).

The GeoJSON handler now supports two vocabularies:

1. **SOSA** — `http://www.w3.org/ns/sosa/` (original, 12 local names)
2. **SensorML** — `http://www.opengis.net/sensorml/2.0#` (new, 1 local name: `Feature` → `SamplingFeature`)

The JSDoc and `isCSAPIFeature` description updated to note "Recognition covers the SOSA and SensorML vocabularies." Additional vocabulary expansion (OGC-OM, etc.) remains tracked in the roadmap.

#### [F11] UNCHANGED: Input guards on every public function

All 6 public functions in `geojson.ts` still guard against null/undefined/wrong-type input.

---

## Phase 3.2 Findings — New

### [F1] POSITIVE: SensorML vocabulary extension follows perfect extension pattern

Issue #49's changes to `geojson.ts` are a textbook example of extending existing architecture without disrupting it:

1. **New constant** (`SENSORML_NS`, line 35) placed alongside existing `SOSA_NS`
2. **New lookup set** (`SENSORML_SAMPLING_FEATURE_LOCAL_NAMES`, line 89) follows the same `ReadonlySet<string>` pattern as the SOSA sets
3. **New internal helper** (`toSensormlLocalName`, line 146) mirrors `toSosaLocalName` exactly
4. **Chain extension** in `getCSAPIResourceType` (line 193) — SOSA checked first, SensorML second, null fallback preserved
5. **Barrel file + root export** updates for `SENSORML_NS`
6. **6 targeted tests** covering recognition, classification, validation, extraction, and unknown rejection

Every new element follows the structure established by the SOSA implementation. Zero deviation from the established pattern.

---

### [F2] POSITIVE: Format Detector functions follow consistent design

All 5 new functions in `mime-type.ts` follow an identical pattern:

```typescript
export function isMimeTypeSmlJson(mimeType: string): boolean {
  return /^application\/sml\+json/i.test(mimeType);
}
```

Design consistency:

- Same function signature: `(mimeType: string): boolean`
- Same implementation pattern: regex with `/i` flag for case-insensitive matching
- Same regex anchoring: `^application\/` prefix, format-specific suffix
- JSDoc: `@param`, `@returns`, `@see` with correct OGC spec references (23-001 for SML, 23-002 for SWE formats)
- RFC 6838 reference for media type structured syntax

The CSV detector uses `swe\+csv` and the Text detector uses `swe\+text` — these do not cross-match. Test coverage confirms this:

```typescript
it('does not match SWE CSV or SWE Text', () => {
  expect(isMimeTypeSweJson('application/swe+csv')).toBe(false);
  expect(isMimeTypeSweJson('application/swe+text')).toBe(false);
});
```

---

### [F3] POSITIVE: Format Detector test thoroughness — Category A 6/6

Each of the 5 new detection functions is tested with a consistent pattern:

| Test Dimension           | Status | Evidence                                           |
| ------------------------ | ------ | -------------------------------------------------- |
| Canonical form detection | ✅     | `application/sml+json` → `true` for each function  |
| Shorthand/suffixed form  | ✅     | `application/sml+json;charset=utf-8` → `true`      |
| Case-insensitive match   | ✅     | `APPLICATION/SML+JSON` → `true`                    |
| Non-matching rejection   | ✅     | `application/json` → `false`, cross-type rejection |
| Cross-match prevention   | ✅     | CSV ↛ Text, Text ↛ CSV, SWE ↛ SML, etc.            |

28 tests across 5 describe blocks (5–6 tests each). This is the most uniform test structure across any set of related functions in the project.

---

### [F4] POSITIVE: `ValidationError` type enables structured error reporting

The `ValidationError` interface (helpers.ts, line 240) provides three fields:

```typescript
export interface ValidationError {
  severity: 'error' | 'warning';
  path: string;
  message: string;
}
```

This is a significant upgrade from the `string[]` return type used by `validateCSAPIFeature` in `geojson.ts`. Benefits:

1. **`severity`** enables callers to distinguish fatal errors from warnings — future validators can use `'warning'` for non-blocking issues (e.g., missing optional metadata)
2. **`path`** provides machine-readable location (e.g., `"Deployment.properties.validTime"`) — enables UI integration, automated diagnostics
3. **`message`** provides human-readable description with expected vs. actual values

All 13 validators return `ValidationError[]`, maintaining the no-short-circuit pattern established in Phase 3.1 (F4).

---

### [F5] POSITIVE: Validator architecture separates cross-reference, Part 1, and Part 2 cleanly

The 13 new functions in `helpers.ts` are organized into three clear tiers:

**Cross-reference utilities** (reusable building blocks):

- `validateUri` — RFC 3986 scheme check
- `validateLink` — HATEOAS link validation (href required, rel optional-but-non-empty)
- `validateIsoDateTime` — ISO 8601 date-time parsing via `Date` constructor
- `validateTimePeriod` — array `[start, end]` and object `{ start, end? }` format + end-before-start check

**Part 1 resource validators** (GeoJSON Feature-based):

- `validateSystem` — `validateBaseFeature` + `VALID_SYSTEM_FEATURE_TYPES` set check
- `validateDeployment` — `validateBaseFeature` + `VALID_DEPLOYMENT_FEATURE_TYPES` + `validTime` required + `validateTimePeriod`
- `validateProcedure` — `validateBaseFeature` + `VALID_PROCEDURE_FEATURE_TYPES`
- `validateSamplingFeature` — `validateBaseFeature` + `sampledFeature@link` required + `validateLink`
- `validateProperty` — non-GeoJSON; `uniqueId` (URI), `label`, `baseProperty` (URI)

**Part 2 resource validators** (non-GeoJSON JSON):

- `validateDatastream` — `name` + `schema|resultSchema` (structural presence check)
- `validateObservation` — `phenomenonTime` + `result` (structural presence check)
- `validateControlStream` — `name` + `schema|commandSchema`
- `validateCommand` — `parameters` (non-null object)

The internal `validateBaseFeature()` helper (line 469) factored out the shared `featureType`/`uid`/`name` checks, avoiding duplication across the 4 Part 1 GeoJSON validators. The `getFeatureProps()` helper (line 459) safely navigates the Feature → properties object.

---

### [F6] POSITIVE: Validators use `@internal` and typed set constants correctly

The implementation uses three `ReadonlySet<string>` constants for featureType validation:

- `VALID_SYSTEM_FEATURE_TYPES` (line 429): Includes both `SystemTypeUris` (full URIs) and compact CURIE forms (`sosa:Sensor`, etc.)
- `VALID_DEPLOYMENT_FEATURE_TYPES` (line 439): Full URI + CURIE for `Deployment`
- `VALID_PROCEDURE_FEATURE_TYPES` (line 444): All 4 procedure subtypes × 2 forms (URI + CURIE)

Marked `@internal` with JSDoc — they are not exported, keeping the public API surface clean. The `SystemTypeUris` import from `model.ts` ensures the System set stays synchronized with the authoritative type definition.

---

### [F7] POSITIVE: `validateTimePeriod` handles end-before-start with correct comparison

`validateTimePeriod` (line 357) includes end-before-start detection for array format:

```typescript
if (
  sErr.length === 0 &&
  eErr.length === 0 &&
  new Date(value[1] as string) < new Date(value[0] as string)
)
  errors.push({
    severity: 'error',
    path,
    message: 'Time period end is before start',
  });
```

Importantly, the comparison only runs when both `sErr` and `eErr` are empty (both dates parsed successfully). This avoids false-positive "end before start" errors when the individual dates are themselves invalid. The test confirms:

```typescript
it('reports end before start', () => {
  const errors = validateTimePeriod(
    ['2027-01-01T00:00:00Z', '2026-01-01T00:00:00Z'],
    'tp'
  );
  expect(errors.some((e) => e.message.includes('before start'))).toBe(true);
});
```

---

### [F8] POSITIVE: Test thoroughness — Category D (Validator) checklist 5/5

Evaluating against the Phase 3 Category D (Validator) test checklist:

| Checklist Item                                     | Status | Evidence                                                                                                                                                                                                 |
| -------------------------------------------------- | ------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Valid input passes validation (empty error array)  | ✅     | Every validator has a "returns empty array for valid ..." test                                                                                                                                           |
| Each constraint violation → specific error message | ✅     | Missing `uid`, invalid `featureType`, missing `validTime`, missing `sampledFeature@link`, etc. — each tested individually                                                                                |
| Multiple simultaneous violations all reported      | ✅     | `validateProperty({})` → `errors.length >= 3`; `validateSystem(makeFeature({featureType:'invalid', uid:'', name:''}))` → `>= 3`                                                                          |
| Cross-reference validation                         | ✅     | `validateUri`, `validateLink` tested independently + composed in `validateSamplingFeature` (`sampledFeature@link` → `validateLink`)                                                                      |
| Part 1 vs Part 2 rules applied to correct types    | ✅     | Part 1 validators use `validateBaseFeature` (GeoJSON); Part 2 validators check flat objects. `validateDeployment` rejects `sosa:Sensor`, `validateSystem` rejects `sosa:Deployment` — no type confusion. |

**All 5 checklist items pass.** The validators match the quality bar set by the GeoJSON handler in Phase 3.1.

---

### [F9] POSITIVE: `Datastream`/`ControlStream` validators accept schema aliases

Both `validateDatastream` and `validateControlStream` check for `schema` OR `resultSchema`/`commandSchema`:

```typescript
const schema = obj.schema ?? obj.resultSchema; // Datastream
const schema = obj.schema ?? obj.commandSchema; // ControlStream
```

This handles the real-world server variation where some implementations use `resultSchema`/`commandSchema` instead of the generic `schema` property. Tests confirm:

```typescript
it('accepts resultSchema as alternative to schema', () => {
  expect(
    validateDatastream({
      name: 'Weather',
      resultSchema: { type: 'DataRecord' },
    })
  ).toEqual([]);
});
```

---

### [F10] POSITIVE: Error reporting tests verify structural properties

The `validation error reporting` describe block at the end of `helpers.spec.ts` tests three important structural qualities:

1. **Multi-error collection**: Validates that multiple errors are returned in a single pass (not short-circuiting)
2. **Path inclusion**: Verifies the `path` field contains the expected property path (e.g., `Deployment.properties.validTime`)
3. **Expected values in messages**: Verifies the `message` field includes the problematic value (e.g., the invalid URI string `"bad"`)

These tests go beyond function-specific correctness — they validate the contract that downstream consumers rely on (UI error display, diagnostic tooling).

---

### [F11] POSITIVE: `helpers.spec.ts` establishes its own `makeFeature()` helper

The validator tests define their own `makeFeature()` at line 476, independent from the one in `geojson.spec.ts`:

```typescript
function makeFeature(
  props: Record<string, unknown>,
  extra: Record<string, unknown> = {}
): Record<string, unknown> { ... }
```

This is slightly different from the `geojson.spec.ts` version (which takes `featureType` as a first parameter). The helpers version takes a full `props` object, which is the correct design for validators that test many different property combinations. Both helpers avoid test-to-test coupling and produce minimal valid GeoJSON Features with override capability.

---

### [F12] DESIGN: Two overlapping validation surfaces for GeoJSON resources

`validateCSAPIFeature` in `geojson.ts` and the new `validateSystem`/`validateDeployment`/`validateProcedure`/`validateSamplingFeature` in `helpers.ts` both validate GeoJSON Features but with different concerns:

|                         | `validateCSAPIFeature` (geojson.ts)                        | `validateSystem` etc. (helpers.ts)                                        |
| ----------------------- | ---------------------------------------------------------- | ------------------------------------------------------------------------- |
| **Return type**         | `string[]`                                                 | `ValidationError[]`                                                       |
| **Scope**               | All 4 Part 1 types combined                                | One validator per type                                                    |
| **featureType check**   | Uses `getCSAPIResourceType()` (SOSA + SensorML vocabulary) | Uses `VALID_*_FEATURE_TYPES` sets (SOSA vocabulary only)                  |
| **Type-specific rules** | Deployment validTime, Procedure geometry=null              | Deployment validTime (via `validateTimePeriod`), SF `sampledFeature@link` |
| **Path info**           | None (flat strings)                                        | Structured (`severity`, `path`, `message`)                                |

**Why this is acceptable (not a bug):**

- `validateCSAPIFeature` is a convenience function for inline validation during GeoJSON parsing (Issue #14)
- The `helpers.ts` validators are structured validation for external consumers and diagnostic tooling (Issue #16)
- Their scopes overlap but serve different API layers

**Why it's worth noting:**

- The `geojson.ts` validator doesn't check `sampledFeature@link` for SamplingFeatures; `helpers.ts` does
- The `helpers.ts` validators don't check for SensorML featureType values in their `VALID_*` sets; `geojson.ts` does
- Future maintainers might expect one definitive validation path per resource type

**Severity:** DESIGN (low)  
**Impact:** Low — both surfaces are correct within their own scope. The `helpers.ts` validators are the more comprehensive set and should be the canonical validation path for external consumers moving forward.

**Recommendation:** Document the intended relationship in JSDoc: `validateCSAPIFeature` is for quick inline checks during parsing; `helpers.ts` validators are the structured validation API. Consider having `validateCSAPIFeature` delegate to the helpers validators in a future cleanup (this would unify the validation logic and upgrade the return type to `ValidationError[]`).

---

### [F13] GAP: `helpers.ts` validators don't include SensorML featureType values

The `VALID_SYSTEM_FEATURE_TYPES`, `VALID_DEPLOYMENT_FEATURE_TYPES`, and `VALID_PROCEDURE_FEATURE_TYPES` sets in `helpers.ts` only include SOSA vocabulary values (full URI + CURIE). The SensorML `http://www.opengis.net/sensorml/2.0#Feature` value accepted by `geojson.ts` is not present.

This means:

- `validateSamplingFeature(feature)` called on a feature with `featureType: "http://www.opengis.net/sensorml/2.0#Feature"` would pass the base feature validation (featureType is a non-empty string, uid is valid, name is present) but the SamplingFeature validator doesn't check featureType against an allowed set like System/Deployment/Procedure do — so this is not currently causing errors.

**Severity:** GAP (low)  
**Impact:** Low — `validateSamplingFeature` does not have a `VALID_SAMPLING_FEATURE_TYPES` set check (unlike System, Deployment, Procedure), so the missing SensorML value does not cause false rejections. But adding such a check in the future would require including SensorML values.

**Recommendation:** If a `VALID_SAMPLING_FEATURE_TYPES` check is added later, include `http://www.opengis.net/sensorml/2.0#Feature`. For now, no action needed.

---

### [F14] POSITIVE: All new exports correctly wired

Issue #49 exports: `SENSORML_NS` → `formats/index.ts` → `src/index.ts` ✅  
Issue #15 exports: 5 new mime-type functions already exported via `src/shared/mime-type.ts` which is directly importable ✅  
Issue #16 exports: `ValidationError` type + 13 validation functions exported from `helpers.ts` which is already wired through `src/index.ts` ✅

No missing exports detected.

---

## Test Quality Heatmap

### Phase 2 (URL Builder) — Carried Forward

No changes from Phase 3.1 heatmap. All entries unchanged:

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

### Phase 3 (Format Handlers + Validators) — Current

**Category A — GeoJSON Handler (geojson.ts + SensorML)**

| Dimension                    | Status | Evidence                                                                                      |
| ---------------------------- | ------ | --------------------------------------------------------------------------------------------- |
| Valid input → correct output | ✅     | All 6 functions + SensorML variant tested                                                     |
| Invalid input → rejection    | ✅     | null, undefined, wrong type, missing fields, empty strings                                    |
| All spec variants            | ✅     | 12 SOSA local names × 2 forms + 1 SensorML local name                                         |
| All classification branches  | ✅     | System (5) + Deployment (1) + Procedure (4) + SamplingFeature (2+1 SML) + unrecognized → null |
| Validation error specificity | ✅     | Each constraint → named error message; multiple-errors-at-once test                           |
| Edge cases                   | ✅     | Array wrong length, non-string start, "now" sentinel, missing props object                    |

**GeoJSON Handler: 6/6 dimensions (100%)**

**Category A — Format Detector (mime-type.ts)**

| Dimension                    | Status | Evidence                                                  |
| ---------------------------- | ------ | --------------------------------------------------------- |
| Valid input → correct output | ✅     | Canonical form for each of 5 functions                    |
| Invalid input → rejection    | ✅     | Non-matching types return false                           |
| All spec variants            | ✅     | Canonical, suffixed/shorthand, case-insensitive           |
| All classification branches  | ✅     | Each function returns true for own type, false for others |
| Cross-match prevention       | ✅     | CSV↛Text, Text↛CSV, SWE↛SML, etc.                         |
| Edge cases                   | ✅     | Case variation, parameter-suffixed forms                  |

**Format Detector: 6/6 dimensions (100%)**

**Category D — Validators (helpers.ts)**

| Dimension                        | Status | Evidence                                                                                |
| -------------------------------- | ------ | --------------------------------------------------------------------------------------- |
| Valid input passes               | ✅     | Every validator has happy-path test returning `[]`                                      |
| Each constraint → specific error | ✅     | Missing uid, invalid featureType, missing validTime, invalid URI, missing href, etc.    |
| Multiple violations all reported | ✅     | `validateProperty({})` → `>= 3`; `validateSystem(invalid)` → `>= 3`                     |
| Cross-reference validation       | ✅     | `validateUri`, `validateLink` tested independently + composed in SF/Property validators |
| Part 1 vs Part 2 rules correct   | ✅     | Part 1 uses `validateBaseFeature` (GeoJSON); Part 2 checks flat objects                 |

**Validators: 5/5 dimensions (100%)**

---

## Smoke Test Findings Integration

| Finding                                    | Status           | Evidence                                                                                                                   |
| ------------------------------------------ | ---------------- | -------------------------------------------------------------------------------------------------------------------------- |
| F4 (validTime array format)                | ✅ **Addressed** | `parseValidTime` handles `["ISO", "now"]` (Phase 3.1). `validateTimePeriod` in helpers.ts also validates the array format. |
| F33 (commandFormat vs observationFormat)   | N/A              | SWE Common parser scope — not addressed by format detector or validators                                                   |
| F34 (Commands fallback routing)            | N/A              | Validator/integration scope — documented in roadmap v3.4                                                                   |
| F35 (Cancel rejected by OSH)               | N/A              | Error handler scope                                                                                                        |
| F36 (id filter ignored on nested commands) | N/A              | JSDoc limitation to be documented in validator                                                                             |
| F37 (result 404 for fire-and-forget)       | N/A              | Error handler scope                                                                                                        |
| F38 (command@id cross-reference)           | N/A              | Cross-reference registry — future Phase 3 task                                                                             |
| F39 (commands use standard envelope)       | N/A              | Parser scope                                                                                                               |
| F40 (SensorML featureType)                 | ✅ **Addressed** | `SENSORML_NS` + `toSensormlLocalName()` + `SENSORML_SAMPLING_FEATURE_LOCAL_NAMES` (Issue #49)                              |

**2 of 9 findings addressed by this Phase 3.2 deliverable.** The remaining 7 are correctly scoped to later Phase 3 tasks.

---

## Summary

| Category                              | Count  | Items                                                                                                                                                                                                                                                                                                 |
| ------------------------------------- | ------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Prior findings reaffirmed (unchanged) | **49** | All accumulated Phase 1–3.1 findings (minus 2 now-resolved)                                                                                                                                                                                                                                           |
| Prior findings now resolved           | **2**  | Phase 3.1 F8 (barrel file → Issue #49), F10 (non-SOSA vocabulary → partially addressed by Issue #49)                                                                                                                                                                                                  |
| **New — positive findings**           | **10** | F1 (SensorML extension pattern), F2 (format detector consistency), F3 (format detector checklist 6/6), F4 (ValidationError type), F5 (validator architecture), F6 (typed set constants), F7 (end-before-start guard), F8 (Category D checklist 5/5), F9 (schema aliases), F10 (error reporting tests) |
| **New — positive informational**      | **2**  | F11 (makeFeature helper), F14 (exports wired)                                                                                                                                                                                                                                                         |
| **New — design findings**             | **1**  | F12 (two overlapping validation surfaces)                                                                                                                                                                                                                                                             |
| **New — gap findings**                | **1**  | F13 (SensorML featureType not in helpers validators)                                                                                                                                                                                                                                                  |
| **New bugs**                          | **0**  | —                                                                                                                                                                                                                                                                                                     |

---

## Recommendations

### Fix Now (before next coding issue)

None. All three Issues (#49, #15, #16) are clean. The one design finding (F12) and one gap finding (F13) are both low-severity and can wait.

### Fix Before Phase 4

1. **[F12] Unify validation surfaces** — Consider having `validateCSAPIFeature` (geojson.ts) delegate to the `helpers.ts` validators for consistent behavior and structured `ValidationError[]` return type. This would eliminate the two-surface divergence and make `helpers.ts` the single source of validation truth.

2. **[F13] Add SensorML featureType values to helpers validators** — When adding a `VALID_SAMPLING_FEATURE_TYPES` set check to `validateSamplingFeature`, include `http://www.opengis.net/sensorml/2.0#Feature`. Currently benign since SF doesn't check featureType against a set.

3. **[Phase 3.1 F7] Replace `as` casts with `satisfies`** — Carried forward. Low urgency.

4. **Systems consolidated resource validation** — Carried forward from Phase 2.9.

### Defer (Low Priority)

5. **Cursor standalone tests** — Cursor for Deployments, Procedures, SamplingFeatures, Properties, ControlStreams. Same shared code path, low risk.

6. **`id` (single) tests for Systems and Deployments** — Same serialization path, low risk.

7. **[Phase 2.8 F8] JSDoc example casing alignment** — No functional impact.

---

## Root Cause Analysis — Continued Zero Defects

Phase 3.2 is the **ninth consecutive phase** with zero new defects. The streak now extends: Procedures → SamplingFeatures → Properties → DataStreams → Observations → ControlStreams → Commands → GeoJSON Handler → SensorML + Format Detector + Validators.

### Why all three issues were clean

**Issue #49 (SensorML Vocabulary):**
The extension followed an established pattern exactly. Every new element (constant, lookup set, internal helper, chain extension) directly mirrored an existing SOSA counterpart. The pattern was so stable that the only creative decisions were naming and placement — both of which followed the existing conventions.

**Issue #15 (Format Detector):**
The 5 detection functions are the simplest possible implementation — a single regex test per function. The uniform structure (identical signature, identical implementation pattern, identical test pattern) eliminated all ambiguity. The cross-match rejection tests ensure the regex patterns don't accidentally overlap.

**Issue #16 (Validators):**
The layered architecture (cross-reference utilities → internal `validateBaseFeature` → type-specific validators) followed the same separation of concerns as the GeoJSON handler. The `ValidationError` type was designed upfront before implementing any validators, ensuring all 13 functions shared a consistent contract. The `VALID_*_FEATURE_TYPES` sets reused the `ReadonlySet` pattern from `geojson.ts`, and `validateBaseFeature` factored out the common GeoJSON Feature checks to avoid duplication across the 4 Part 1 validators.

---

## Overall Assessment

**Phase 3.2 is clean.** Three issues — spanning three distinct component categories (vocabulary extension, media type detection, resource validation) — all entered with zero defects and full test checklist compliance.

1. **Validator extensions deliver the strongest single-issue contribution yet.** Issue #16 adds 13 functions plus a type definition across 577 new production lines, backed by 61 tests. The three-tier architecture (cross-reference utilities → Part 1 → Part 2) is well-factored, and the `ValidationError` structured type is a meaningful quality improvement over the flat `string[]` pattern used in the earlier `validateCSAPIFeature`. The end-before-start guard in `validateTimePeriod` correctly avoids false positives by conditioning on both individual date validations passing first.

2. **Format Detector achieves maximum uniformity.** The 5 new functions are the most structurally uniform component in the project — identical signature, identical regex pattern, identical test structure. This uniformity makes the component trivially maintainable and serves as a strong pattern reference for any future media type detection needs.

3. **SensorML vocabulary extension validates the GeoJSON handler architecture.** Issue #49 proved that the layered architecture from Phase 3.1 supports clean vocabulary extension without disrupting existing behavior. The chain pattern (`SOSA first → SensorML second → null fallback`) scales naturally to additional vocabularies.

**Cumulative project quality:**

- **9 consecutive phases** with zero defects (Phase 2.3 → Phase 3.2)
- **0 open gap findings** from Phase 2 reviews (all resolved)
- **1 low-severity gap** (F13: SensorML in helpers validators) + **1 low-severity design** (F12: overlapping validation surfaces)
- **~520 tests** across 6 suites, all passing
- **~7,600 lines** of production + test code
- **Phase 2:** 79 public methods, 9 resource types, 314 tests — **complete**
- **Phase 3:** 6 GeoJSON functions + 5 mime-type detectors + 13 validators + 1 type + 2 constants = **27 new public API elements**, 173 new tests — **in progress**
