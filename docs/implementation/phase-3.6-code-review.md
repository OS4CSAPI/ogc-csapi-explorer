# Phase 3.6 Code Review — AggregateProcess Sub-Parser + Validation Sweep

**Review Date:** 2026-02-15
**Reviewer:** AI (Claude Opus 4.6, GitHub Copilot)
**Issues:** #20 — SensorML Aggregate Process Parser + smoke test template cleanup
**Commits:**

- `035b3df` — "docs: remove obsolete validateCSAPIFeature from smoke test template"
- `814aef6` — "feat(sensorml): add AggregateProcess sub-parser (Issue #20)"

**Previous Review:** Phase 3.5 — SensorML SimpleProcess Sub-Parser (Issue #19)
**Previous Smoke Test:** `6cd5ae8` — Phase 3.5 Live Server Smoke Test
**Review Category:** C (Parser modules — fixture → typed output assertions) + Validation Sweep

---

## Verification Gates

| Gate                   | Command                                | Result                                |
| ---------------------- | -------------------------------------- | ------------------------------------- |
| TypeScript compilation | `npx tsc --noEmit`                     | ✅ Clean (0 errors)                   |
| CSAPI test suite       | `npx jest "src/ogc-api/csapi"`         | ✅ **511 passed** (8 suites)          |
| Endpoint test suite    | `npx jest "src/ogc-api/endpoint.spec"` | ✅ 82 passed, 1 failed (pre-existing) |
| Format tests           | `npx jest "src/ogc-api/csapi/formats"` | ✅ **197 passed** (5 suites)          |
| AggregateProcess tests | `npx jest "aggregate-process"`         | ✅ **50 passed** (1 suite)            |

**Test delta from Phase 3.5:** +50 tests (from 147 → 197 format tests), +50 net in CSAPI (from 461 → 511).

---

## Scope

### Files Reviewed

| File                                                           | Lines      | Status       |
| -------------------------------------------------------------- | ---------- | ------------ |
| `src/ogc-api/csapi/formats/sensorml/aggregate-process.ts`      | 439 (+439) | **NEW**      |
| `src/ogc-api/csapi/formats/sensorml/aggregate-process.spec.ts` | 646 (+646) | **NEW**      |
| `docs/governance/smoke-test-prompt-template-phase-3.md`        | +5 / −17   | **MODIFIED** |

**Total new code:** 1,085 lines (439 production + 646 test).
**Total doc edits:** 3 locations updated (Step 3c, report format validation section, Component Test Matrix row).

### Not in Scope

- `docs/implementation/live-server-smoke-test-post-phase-3.5.md` (smoke test report, documentation only)
- `docs/implementation/phase-3.5-code-review.md` (previous review, unchanged)

---

## Validation Code Sweep

**User requested a sweep for lingering validation code.** Full audit performed:

| Search Target                                                      | Files in `src/**/*.ts` | Result   |
| ------------------------------------------------------------------ | ---------------------- | -------- |
| `validateCSAPIFeature`                                             | 0 matches              | ✅ Clean |
| `ValidationError` (type)                                           | 0 matches              | ✅ Clean |
| Per-type validators (`validateSystem`, `validateDeployment`, etc.) | 0 matches              | ✅ Clean |
| `validator.ts` or validation modules in `formats/`                 | 0 files                | ✅ Clean |
| Validate-then-extract gate patterns                                | 0 matches              | ✅ Clean |
| Import of `validator`/`validation` from csapi/formats              | 0 matches              | ✅ Clean |

**Acceptable validation-related code in `src/`:**

- `helpers.ts` — `validateLimit()` and `validateBbox()` — query-parameter guards (not feature-level validators); file ends with `// (End of module — feature-level validators removed per Issue #52)`
- `isValidUri()` in `geojson.ts` — URI format check utility, not a feature validator

**Documentation references:** All `docs/` references to removed validators are historical/archival (design decision notes, lessons learned, smoke test reports). The smoke test template (`035b3df`) was updated in this review period to explicitly note the removal.

**Verdict: The Issue #52 validator removal is fully complete. Zero lingering validation code in source.**

---

## Step 1: Lessons Learned Check

| Lesson                                                     | Applicable? | Status | Evidence                                                                                                                                                                                   |
| ---------------------------------------------------------- | ----------- | ------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **L1:** Audit upstream before building new layers          | ✅          | PASS   | AggregateProcess sub-parser follows the pattern established by Issue #19. No new architectural layer.                                                                                      |
| **L2:** Postel's Law — never gate extraction on validation | ✅          | PASS   | Validates only 3 required fields (`type`, `label`, `uniqueId`). All optional properties gracefully return `undefined`. Components/connections are `undefined` when absent/null.            |
| **L3:** Don't couple validation to extraction              | ✅          | PASS   | Parser extracts what is present. `parseComponentEntry` uses recognition (check `type` discriminator) not validation. External links passed through as-is.                                  |
| **L4:** Don't build parallel systems                       | ✅          | PASS   | Single parser entry point. Internal helpers duplicated from SimpleProcess (see F3 below) but not an alternative path.                                                                      |
| **L5:** Verify upstream claims by reading source           | N/A         | —      | No upstream claims made.                                                                                                                                                                   |
| **L6:** Real-world server data diverges from spec          | ✅          | PASS   | Null/undefined handling for all 10 optional properties. `parseFeatureList` silently filters invalid links. `parseModes` silently filters invalid modes.                                    |
| **L7:** Phase 3 smoke tests are essential                  | N/A         | —      | Sub-parser doesn't connect to live servers.                                                                                                                                                |
| **L8:** Layered architecture enables clean extension       | ✅          | PASS   | Error class → shared helpers → component-specific helpers (`parseComponentEntry`, `parseConnection`, `parseComponentList`, `parseConnectionList`) → main parser (`parseAggregateProcess`). |
| **L9:** Content negotiation cannot be assumed              | N/A         | —      | Not applicable to sub-parser (no HTTP).                                                                                                                                                    |
| **L10:** Type naming must avoid built-in collisions        | ✅          | PASS   | `SensorMLParseError` clearly namespaced. No collisions.                                                                                                                                    |
| **L11:** Document architectural decisions formally         | ✅          | PASS   | Recursive parsing decision documented in module JSDoc (lines 11-16). Deferral of other process types to Issue #22 documented in `parseComponentEntry` JSDoc and inline comments.           |
| **L12:** "Should we build it at all?"                      | ✅          | PASS   | ROADMAP Task 7 explicitly scopes this parser. Required for Issue #22 (main parser).                                                                                                        |

**Result: 8/8 applicable lessons pass. 4 not applicable.**

---

## Step 4: Prior Findings Reaffirmation

### Phase 2 Findings — Unchanged

All Phase 2 accumulated findings (36 unchanged + 10 moot + 1 resolved) carry forward with no changes. The AggregateProcess parser does not touch URL builder code, helpers, or model definitions.

### Phase 3.1–3.3 Findings — Unchanged

- **Phase 3.1 F7 / carried forward as F13:** `as` type assertions in `extractCSAPIFeature` — **still open, carried forward**
- **Phase 3.3 F12 / Phase 3.4 F12:** Exports not in barrel — **still correct** (barrel updates deferred to Issue #23)
- **Phase 3.2 F1–F11:** Moot (validator removal) — **still moot**

### Phase 3.4 Findings — Unchanged

| Finding                                         | Status             | Notes                                  |
| ----------------------------------------------- | ------------------ | -------------------------------------- |
| F1–F2 (POSITIVE type hierarchy, discriminators) | Unchanged          | Types consumed by aggregate-process.ts |
| F3 (DESIGN Document name)                       | ACCEPTED-BY-DESIGN | Unchanged                              |
| F4–F10 (POSITIVE)                               | Unchanged          | Type layer findings                    |
| F11–F13 (INFORMATIONAL)                         | Unchanged          |                                        |
| F14 (DESIGN `as` casts)                         | Carried forward    | Not in scope                           |

### Phase 3.5 Findings — Status Update

| Finding                                              | Phase 3.5 Status | Current Status      | Notes                                                                     |
| ---------------------------------------------------- | ---------------- | ------------------- | ------------------------------------------------------------------------- |
| F1 (POSITIVE Postel's Law)                           | POSITIVE         | Unchanged           | AggregateProcess follows same pattern                                     |
| F2 (POSITIVE DescribedObject passthrough)            | POSITIVE         | Unchanged           | Same spread-then-delete-then-assign pattern used                          |
| F3 (POSITIVE error messages with positional context) | POSITIVE         | Unchanged           | AggregateProcess adds `components[N]` and `connections[N]` indexed errors |
| F4 (POSITIVE IOComponentChoice deferral)             | POSITIVE         | Unchanged           | Same pattern reused                                                       |
| F5 (DESIGN parseSettings JSDoc)                      | RESOLVED         | **Still resolved**  | Deferral JSDoc present in aggregate-process.ts line 173                   |
| F6 (POSITIVE Mode validation)                        | POSITIVE         | Unchanged           | Same `parseMode`/`parseModes` reused                                      |
| F7 (POSITIVE Link parsing)                           | POSITIVE         | Unchanged           | Same `parseLink` reused                                                   |
| F8 (POSITIVE test fixtures)                          | POSITIVE         | Unchanged           | AggregateProcess follows same 2-fixture pattern                           |
| F9 (POSITIVE edge case coverage)                     | POSITIVE         | Unchanged           | AggregateProcess adds component/connection edge cases                     |
| F10 (POSITIVE JSDoc)                                 | POSITIVE         | Unchanged           | Comprehensive JSDoc with spec cross-refs                                  |
| F11 (INFORMATIONAL exports deferred)                 | INFORMATIONAL    | **Unchanged**       | Barrel update deferred to Issue #23                                       |
| F12 (INFORMATIONAL InputList casts)                  | INFORMATIONAL    | Unchanged           | Same casts used in aggregate-process.ts                                   |
| F13 (DESIGN `as` casts, carried forward)             | DESIGN (low)     | **Carried forward** | Not in scope                                                              |

---

## Phase 3.6 Findings — New

### [F1] POSITIVE: ComponentList parsing with recursive support and external link handling

`parseComponentEntry()` (lines 258–290) correctly handles the three component variants:

1. **Inline AggregateProcess** (recursive): Detects `type === 'AggregateProcess'` and calls `parseAggregateProcess()` recursively, then restores the `name` property via spread.
2. **Other inline process types** (SimpleProcess, PhysicalComponent, PhysicalSystem): Passed through as-is with documented deferral to Issue #22.
3. **External links** (`type: 'Link'`): Passed through as-is for later resolution.

The recursive test (spec line 259) verifies a 2-level deep nesting: AggregateProcess → AggregateProcess → SimpleProcess, with connections at the inner level correctly preserved.

**Severity:** POSITIVE

---

### [F2] POSITIVE: ConnectionList parsing with strict required-field validation

`parseConnection()` (lines 333–352) validates both `source` and `destination` as required strings, producing indexed error messages:

```
connections[0] must have a string "source" property
connections[0] must have a string "destination" property
```

This correctly reflects the OAS ConnectionList schema where both fields are required. The implementation produces a clean `{ source, destination }` object rather than a pass-through cast — appropriate because Connection has only 2 defined fields with no extension properties.

**Severity:** POSITIVE

---

### [F3] DESIGN (low): Internal helpers duplicated from SimpleProcess

The following 8 internal helpers are **exact duplicates** between `simple-process.ts` and `aggregate-process.ts`:

| Helper                         | SimpleProcess Lines | AggregateProcess Lines |
| ------------------------------ | ------------------- | ---------------------- |
| `SensorMLParseError` class     | 41–47               | 53–59                  |
| `isRecord()`                   | 55–57               | 67–69                  |
| `optionalString()`             | 62–64               | 74–76                  |
| `parseLink()`                  | 72–82               | 84–96                  |
| `parseIOComponentChoice()`     | 112–127             | 108–125                |
| `parseIOList()`                | 138–155             | 136–155                |
| `parseSettings()`              | 163–166             | 170–175                |
| `parseFeatureList()`           | 174–183             | 183–192                |
| `parseMode()` / `parseModes()` | 194–219             | 201–226                |

This is **expected and correct for Phase 3** — Issue #22 (SensorML Main Parser) will coordinate shared helpers and extract the common code. The Issue #20 requirements explicitly state "Do NOT modify files outside the 'Files to Create or Modify' table." Extracting shared helpers into a common module would require modifying `simple-process.ts`, which is out of scope.

However, the `SensorMLParseError` class is now defined in two places with identical behavior. When Issue #22 consolidates these, one canonical error class should be chosen.

**Recommendation:** No action now. Issue #22 should extract the ~9 duplicated helpers into a shared internal module (e.g., `sensorml/_helpers.ts`) and re-export `SensorMLParseError` from a single location. Track as a known consolidation point.

**Severity:** DESIGN (low — expected, scoped to Issue #22)

---

### [F4] POSITIVE: `parseComponentEntry` correctly re-attaches `name` after recursive parsing

Lines 285–287:

```typescript
if (value.type === 'AggregateProcess') {
  const parsed = parseAggregateProcess(value);
  return { ...parsed, name: value.name as string } as ComponentEntry;
}
```

When a nested AggregateProcess is parsed recursively, `parseAggregateProcess()` spreads the raw JSON (which includes `name`) but does not explicitly preserve `name` as a managed property. The `{ ...parsed, name: value.name as string }` spread ensures the `name` property from `SoftNamedProperty` is always present on the returned `ComponentEntry`, regardless of whether the recursive parser preserved it. This is defensive and correct.

**Severity:** POSITIVE

---

### [F5] POSITIVE: Comprehensive test coverage across all Category C dimensions

50 tests across 7 `describe` blocks with full Category C coverage:

| Dimension                            | Tests | Evidence                                                                                                                                                                                                                                                                          |
| ------------------------------------ | ----- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Valid input → correct typed output   | 8     | Minimal, full, typeOf, configuration, features, I/O, modes, DescribedObject                                                                                                                                                                                                       |
| Component parsing (spec-specific)    | 6     | Inline SimpleProcess, PhysicalComponent, external links, mixed, recursive, absent                                                                                                                                                                                                 |
| Connection handling (spec-specific)  | 3     | Multi-connection, single, absent                                                                                                                                                                                                                                                  |
| Invalid input → `SensorMLParseError` | 14    | null, non-object, array, missing type, wrong type, missing label, missing uniqueId, non-array components, component without name, non-object component, non-array connections, missing source, missing destination, non-object connection, non-array inputs, error class identity |
| Edge cases (null, empty, unknown)    | 5     | Empty arrays (components + connections), null optional fields (10 fields), unknown property passthrough, single component, empty I/O arrays                                                                                                                                       |
| Standalone helper tests              | 14    | `parseComponentList` (4), `parseConnectionList` (4), `parseComponentEntry` (4) — each with valid, undefined, null, and invalid cases                                                                                                                                              |

**Severity:** POSITIVE

---

### [F6] POSITIVE: Recursive parsing test verifies 2-level nesting with inner connections

The recursive nesting test (spec lines 259–281) constructs a document with:

```
AggregateProcess (outer)
  └─ component "subPipeline" (AggregateProcess inner)
       ├─ component "innerStep" (SimpleProcess)
       └─ connection: inputs/data → components/innerStep/inputs/raw
```

The test asserts that the inner AggregateProcess's `components` and `connections` are correctly parsed at depth, and that the inner connection's `source` path is preserved exactly. This directly validates the recursive capability required by the issue acceptance criteria.

**Severity:** POSITIVE

---

### [F7] POSITIVE: `parseComponentList` error handling preserves original SensorMLParseError

Lines 303–310:

```typescript
try {
  return parseComponentEntry(item, i);
} catch (err) {
  if (err instanceof SensorMLParseError) throw err;
  throw new SensorMLParseError(
    `Invalid components[${i}]: ${(err as Error).message}`
  );
}
```

The re-throw guard (`if (err instanceof SensorMLParseError) throw err`) preserves the specific error message from `parseComponentEntry` (e.g., `"components[2] must have a string 'name' property"`) without double-wrapping. Only unexpected non-SensorMLParseError exceptions get wrapped with a generic message. This is more precise than the simpler pattern in `parseIOList` — appropriate because component parsing involves recursion where the original error location must be preserved.

**Severity:** POSITIVE

---

### [F8] POSITIVE: Smoke test template cleanup (commit `035b3df`) is accurate and well-phrased

Three locations updated:

1. **Step 3c** — replaced with strikethrough + explanatory note referencing Issue #52, F49, design decision document, and Postel's Law
2. **Report format validation section** — struck through with concise note
3. **Component Test Matrix** — "Validator extensions" row struck through

Each note is factually correct, cites the right references, and preserves step numbering. The `> Note` block in Step 3c is comprehensive without being verbose.

**Severity:** POSITIVE

---

### [F9] INFORMATIONAL: AggregateProcess exports not yet in barrel file

Same as Phase 3.3 F12, Phase 3.4 F12, and Phase 3.5 F11. The barrel file `formats/index.ts` re-exports only GeoJSON symbols. AggregateProcess exports (`parseAggregateProcess`, `parseComponentList`, `parseConnectionList`, `parseComponentEntry`, `SensorMLParseError`) are not re-exported.

This is correct per the established pattern — barrel updates deferred to Issue #23 (SensorML Index).

**Severity:** INFORMATIONAL (no action needed)

---

### [F10] INFORMATIONAL: `parseIOComponentChoice` is not exported from aggregate-process.ts

In `simple-process.ts`, `parseIOComponentChoice` is exported (for standalone reuse). In `aggregate-process.ts`, it is a private `function` (not exported). This is intentional — the function is an exact duplicate, and exporting it from two files would create a confusing dual source. Issue #22 will consolidate these into one shared export.

**Severity:** INFORMATIONAL (correct decision)

---

### [F11] INFORMATIONAL: `SensorMLParseError` exported from two files

Both `simple-process.ts` and `aggregate-process.ts` export `SensorMLParseError`. These are identical classes, but they are technically **different class constructors** at runtime — an `instanceof` check against one would not match errors thrown by the other.

Currently this causes no issues because:

- Each parser's tests import from the corresponding file
- The main parser (Issue #22) hasn't been created yet
- No consumer currently catches `SensorMLParseError` across sub-parsers

When Issue #22 consolidates, it should establish a single canonical export to avoid `instanceof` cross-module surprises.

**Severity:** INFORMATIONAL (no current impact, tracked for Issue #22)

---

## Test Quality Heatmap

### Phase 2 (URL Builder) — Carried Forward

No changes from Phase 3.5 heatmap. All entries unchanged.

### Phase 3 (Format Handlers + Types + Parsers) — Current

**Category A — GeoJSON Handler: 6/6 dimensions (100%)** — Unchanged from Phase 3.5.

**Category A — Format Detector: 6/6 dimensions (100%)** — Unchanged from Phase 3.5.

**Category B — SWE Common Types: 6/6 dimensions (100%)** — Unchanged from Phase 3.5.

**Category B — SensorML Types: 6/6 dimensions (100%)** — Unchanged from Phase 3.5.

**Category C — SimpleProcess Sub-Parser: 6/6 dimensions (100%)** — Unchanged from Phase 3.5.

**Category C — AggregateProcess Sub-Parser** — NEW

| Dimension                            | Status | Evidence                                                                                                                               |
| ------------------------------------ | ------ | -------------------------------------------------------------------------------------------------------------------------------------- |
| Valid input → correct typed output   | ✅     | 8 valid document tests covering all AbstractProcess + AggregateProcess properties                                                      |
| Invalid input → `SensorMLParseError` | ✅     | **14 invalid document tests** covering null, non-object, array, type errors, missing required fields, malformed components/connections |
| Nested/recursive structures          | ✅     | 2-level nesting test: AggregateProcess → AggregateProcess → SimpleProcess with inner connections                                       |
| Component type discrimination        | ✅     | 4 component variants tested: inline SimpleProcess, PhysicalComponent, external Link, recursive AggregateProcess                        |
| Standalone helper tests              | ✅     | `parseComponentList` (4), `parseConnectionList` (4), `parseComponentEntry` (4) = **12 standalone tests**                               |
| Edge cases (null, empty, unknown)    | ✅     | **5 edge case tests**: empty arrays, null optional fields (10 fields), unknown properties, single component, empty I/O arrays          |

**AggregateProcess Sub-Parser: 6/6 dimensions (100%)**

---

## Smoke Test Findings Integration

> No new smoke test findings to integrate in this review period. The smoke test template cleanup (commit `035b3df`) addressed stale references to the removed validation function but did not produce new findings.

| Finding                           | Status                | Evidence                                                           |
| --------------------------------- | --------------------- | ------------------------------------------------------------------ |
| F4 (validTime)                    | ✅ **Addressed**      | `parseValidTime` in geojson.ts (unchanged)                         |
| F33-F39                           | N/A                   | Scoped to later Phase 3/4 tasks                                    |
| F40 (SensorML featureType)        | ✅ **Addressed**      | `SENSORML_NS` + `toSensormlLocalName()` (unchanged)                |
| F49 (validators block extraction) | ✅ **Fully resolved** | Validators removed (Issue #52); sweep confirms zero lingering code |
| F50 (content type change)         | N/A                   | Response parser scope                                              |

**3 of 5 relevant findings addressed. No change from Phase 3.5.**

---

## Validation Sweep Summary

**Requested by user** to verify no validation code lingers after Issue #52 removal.

| Category                                            | Status                                                                                       |
| --------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| `src/**/*.ts` — validator functions                 | ✅ **Zero matches**                                                                          |
| `src/**/*.ts` — `ValidationError` type              | ✅ **Zero matches**                                                                          |
| `src/**/*.ts` — validate-then-extract patterns      | ✅ **Zero matches**                                                                          |
| `src/**/*.ts` — validator/validation module imports | ✅ **Zero matches**                                                                          |
| `src/**/*.ts` — validator/validation file existence | ✅ **No files**                                                                              |
| `docs/**` — historical references                   | ✅ **All archival/struck-through**                                                           |
| Acceptable `validate*` in `src/`                    | `validateLimit()`, `validateBbox()` in helpers.ts (parameter guards, not feature validators) |

**Conclusion: The Issue #52 validator removal is complete and thorough. No remediation needed.**

---

## Overall Codebase Metrics (Cumulative)

### Production Code

| File                                          | Lines     | Purpose                                                   |
| --------------------------------------------- | --------- | --------------------------------------------------------- |
| `csapi/model.ts`                              | 560       | Type definitions (9 resource types, discriminated unions) |
| `csapi/url_builder.ts`                        | 1,863     | URL builder (79 public methods)                           |
| `csapi/helpers.ts`                            | 194       | Shared helpers (cursor, validation, assertions)           |
| `csapi/formats/index.ts`                      | 19        | Barrel file (GeoJSON re-exports)                          |
| `csapi/formats/geojson.ts`                    | 334       | GeoJSON handler (5 functions)                             |
| `csapi/formats/swecommon/types.ts`            | 657       | SWE Common 3.0 type definitions                           |
| `csapi/formats/sensorml/types.ts`             | 851       | SensorML 3.0 type definitions                             |
| `csapi/formats/sensorml/simple-process.ts`    | 310       | SimpleProcess sub-parser                                  |
| `csapi/formats/sensorml/aggregate-process.ts` | 439       | **AggregateProcess sub-parser** ← NEW                     |
| **Total Production**                          | **5,227** |                                                           |

### Test Code

| File                                               | Lines     | Tests                                     | Purpose                                 |
| -------------------------------------------------- | --------- | ----------------------------------------- | --------------------------------------- |
| `csapi/model.spec.ts`                              | 377       | 56                                        | Model type tests                        |
| `csapi/url_builder.spec.ts`                        | 2,118     | 314                                       | URL builder tests                       |
| `csapi/helpers.spec.ts`                            | 268       | 44                                        | Helper tests                            |
| `csapi/formats/geojson.spec.ts`                    | 431       | 53                                        | GeoJSON handler tests                   |
| `csapi/formats/swecommon/types.spec.ts`            | 375       | 6                                         | SWE Common type tests                   |
| `csapi/formats/sensorml/types.spec.ts`             | 369       | —                                         | SensorML type tests                     |
| `csapi/formats/sensorml/simple-process.spec.ts`    | 438       | 38                                        | SimpleProcess parser tests              |
| `csapi/formats/sensorml/aggregate-process.spec.ts` | 646       | 50                                        | **AggregateProcess parser tests** ← NEW |
| **Total Test**                                     | **5,022** | **511** (CSAPI) + 82 (endpoint) = **593** |                                         |

### Combined

| Metric              | Phase 3.5   | Phase 3.6                | Delta      |
| ------------------- | ----------- | ------------------------ | ---------- |
| Production code     | 4,784 lines | 5,227 lines              | **+443**   |
| Test code           | 4,376 lines | 5,022 lines              | **+646**   |
| Total lines         | ~9,160      | ~10,249                  | **+1,089** |
| CSAPI tests         | 461         | 511                      | **+50**    |
| Format tests        | 147         | 197                      | **+50**    |
| Test suites         | 8           | 9 (8 CSAPI + 1 endpoint) | **+1**     |
| Production files    | 8           | 9                        | **+1**     |
| Public API elements | 306         | 306 + 5 = **311**        | **+5**     |

---

## Summary

| Category                    | Count | Items                                                                                                                                                                    |
| --------------------------- | ----- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Prior findings unchanged    | All   | Phase 2–3.5 accumulated findings carry forward                                                                                                                           |
| **New — positive findings** | **8** | F1 (ComponentList recursive), F2 (ConnectionList strict), F4 (name re-attach), F5 (test coverage), F6 (recursive test), F7 (error re-throw guard), F8 (template cleanup) |
| **New — design (low)**      | **1** | F3 (helper duplication — expected, deferred to Issue #22)                                                                                                                |
| **New — informational**     | **3** | F9 (exports deferred to #23), F10 (IOComponentChoice not dual-exported), F11 (SensorMLParseError dual class)                                                             |
| **New bugs**                | **0** | —                                                                                                                                                                        |
| **Validation sweep**        | ✅    | Zero lingering validation code in `src/`                                                                                                                                 |

---

## Recommendations

### Fix Now (before next issue)

None. The module is clean.

### Fix Before Phase 4

1. **[F3/F11] Issue #22 should consolidate shared helpers and canonical `SensorMLParseError`** — When the main parser is implemented, extract the 9 duplicated helpers into a shared internal module and establish one `SensorMLParseError` export. This will eliminate the `instanceof` cross-module risk noted in F11.

2. **[F13/3.1-F7] Replace `as` casts with `satisfies` in `extractCSAPIFeature`** — Carried forward from Phase 3.1. Recommend fixing when extraction function is next modified.

3. **Systems consolidated resource validation tests** — Carried forward from Phase 2.9.

### Defer (Low Priority)

4. **Cursor standalone tests** — Deployments, Procedures, SamplingFeatures, Properties, ControlStreams.

5. **`id` (single) tests for Systems and Deployments** — Same serialization path.

6. **[Phase 2.8 F8] JSDoc example casing alignment** — No functional impact.

---

## Root Cause Analysis — Continued Zero Defects

Phase 3.6 is the **thirteenth consecutive phase** with zero new defects. The streak: Procedures → SamplingFeatures → Properties → DataStreams → Observations → ControlStreams → Commands → GeoJSON Handler → SensorML Vocab + Format Detector + Validators → Validator Removal + SWE Common Types → SensorML Types → SimpleProcess Sub-Parser → **AggregateProcess Sub-Parser**.

### Why this issue was clean

**Issue #20 (AggregateProcess Sub-Parser):**

1. **Direct sibling precedent** — The SimpleProcess parser (Issue #19) established the exact pattern: error class, internal helpers, parsed AbstractProcess properties, spread-then-delete-then-assign output construction. The AggregateProcess parser followed this blueprint identically, adding only `parseComponentList`, `parseConnectionList`, and recursive handling.
2. **Well-defined type targets** — The SensorML types (Issue #18) provide `AggregateProcess`, `ComponentEntry`, `ComponentList`, `Connection`, `ConnectionList` with clear required/optional field definitions. The parser maps directly to these types.
3. **Bounded recursion scope** — The recursive parsing is limited to one type (`AggregateProcess` → `AggregateProcess`). Other inline process types are passed through. This keeps the recursion simple and testable — no mutual recursion, no unbounded depth concerns.
4. **Explicit scope boundaries** — The Issue #20 requirements clearly define what NOT to touch. The implementation stays within its 2-file scope. No modifications to SimpleProcess, types, or any other files.

---

## Overall Assessment

**Phase 3.6 is clean and extends the sub-parser pattern with the distinguishing feature of recursive component handling.**

1. **The AggregateProcess parser is the second behavioral module in the SensorML format layer,** directly mirroring the SimpleProcess parser with the addition of ComponentList and ConnectionList parsing. It follows the established pattern precisely — 50 tests covering all 6 Category C dimensions at 100%.

2. **The helper duplication (F3) is the most notable architectural observation,** but it is **expected and scoped**. Both Issue #19 and Issue #20 specify "do not modify other files." The duplication creates a clean consolidation opportunity for Issue #22, which is explicitly designed to coordinate shared helpers across sub-parsers. This is the correct sequence: build independent modules first, then consolidate when the coordinator module is created.

3. **The recursive parsing implementation (F1, F4, F6) is the distinguishing contribution.** The `parseComponentEntry` → `parseAggregateProcess` → `parseComponentEntry` recursion is correctly bounded (only triggers for `type === 'AggregateProcess'`), preserves component names through the spread pattern, and is verified by a 2-level nesting test. This pattern will be reused when PhysicalSystem (Issue #21) is implemented, since PhysicalSystem also has a ComponentList.

4. **The validation sweep confirms that the Issue #52 cleanup is complete.** Zero lingering validation code exists in `src/`. All documentation references are appropriately archival. The `validateLimit()`/`validateBbox()` parameter guards in `helpers.ts` are the only `validate*` functions remaining, and they are appropriate query-parameter sanitizers, not feature-level validators.

**Cumulative project quality:**

- **13 consecutive phases** with zero defects (Phase 2.3 → Phase 3.6)
- **0 open bug or gap findings**
- **1 new low-severity design finding** (F3: helper duplication) + **1 carried forward** (F13: `as` casts)
- **593 tests** (511 CSAPI + 82 endpoint), all passing except 1 pre-existing endpoint failure
- **~10,249 lines** of production + test code
- **Phase 2:** 79 public methods, 9 resource types, 314 tests — **complete**
- **Phase 3:** 5 GeoJSON functions + 5 mime-type detectors + 48 SWE types + 50 SensorML types + 2 constants + 4 SimpleProcess exports + 5 AggregateProcess exports = **119 public API elements**, 197 Phase 3 tests — **in progress**
