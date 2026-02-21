# Phase 5.5 Code Review — Post-Smoke-Test Issues #101–#110

**Date:** 2026-02-21
**Reviewer:** GitHub Copilot (Claude Opus 4.6)
**Scope:** Sixth Phase 5 code review covering all work since the Phase 5.3 smoke test (ST#22) — Issues #101 through #110 (10 issues: 6 implemented, 4 findings-only/deferred)
**Last review:** `docs/implementation/phase-5.4-code-review.md` (commit `293100d`)

**Commits:**
- `ba989eb` — `fix(swecommon): support complex types in DataRecord fields and DataArray elements (#101)`
- `617b42f` — `fix(part2): extract cross-reference @id fields in all 5 Part 2 parsers (#103)`
- `33dabd0` — `feat: add ControlStream systems, procedures, and history navigation methods (#104)`
- `c1e63f1` — `fix: remap 6 query parameter names to OGC spec wire names (#105)`
- `23126d4` — `Add missing Part 2 query option fields (#106)`
- `9e0ed2f` — `Narrow nested builder method option types (#107)`
- `f8026ea` — `Add CSAPIResourceRef type and @link fields to Part 1 interfaces (#108)`
- `6ed3e09` — `feat: extract @link properties in extractCSAPIFeature() (#109)`

**Findings-only/deferred commits (no source code changes):**
- `51b0a8d` — docs(findings): Issue #101 findings report
- `3e9a854` — docs(findings): Issue #103 findings report
- `9760c33` — docs(findings): Issue #104 findings report
- `2aa1213` — docs(findings): Issue #105 findings report
- `c5f835e` — docs(findings): Issue #106 findings report
- `a8d3b5a` — docs(findings): Issue #107 findings report
- `57592f2` — docs(findings): Issue #108 findings report
- `8c60116` — docs(findings): Issue #109 findings report
- `ad92531` — docs(findings): Issue #110 findings report (DEFERRED)
- `e128322` — docs(findings): Issue #102 findings report (DEFERRED)
- `04130a4` — docs(findings): Issue #100 findings report (DEFERRED)
- `770e535` — docs(findings): Issue #99 findings report (existing support)
- `6d13268` — `style(sensorml): combine re-export lines in physical-system.ts (F34)`

---

## Verification Status

| Check | Result |
|-------|--------|
| tsc --noEmit | ✅ 0 errors (clean) |
| CSAPI unit tests (all) | ✅ 1282 passing, 29 suites |
| CSAPI format tests | ✅ 740 passing, 20 suites |
| Endpoint integration tests | ⚠️ 82/83 passing (1 pre-existing upstream failure — Unicode mismatch at `endpoint.spec.ts:1789`) |

**Test delta from Phase 5.4:** +31 tests (1251 → 1282), 0 new suites (29 → 29).
**Format test delta:** +16 tests (724 → 740), 0 new suites (20 → 20).

Test additions by issue:
| Issue | Tests Added | File |
|-------|------------|------|
| #101 (SWE Common complex types) | +7 | `data-record.spec.ts` (+4), `data-array.spec.ts` (+3) |
| #103 (Part 2 @id extraction) | 0 (modified 5 existing) | `part2.spec.ts` |
| #104 (ControlStream navigation) | +9 (6 happy + 3 guard) | `url_builder.spec.ts` |
| #105 (Query param remapping) | 0 (modified 13 existing) | `url_builder.spec.ts` |
| #106 (Missing query fields) | +7 | `url_builder.spec.ts` |
| #107 (Nested method types) | 0 (type-only change) | — |
| #108 (CSAPIResourceRef type) | 0 (type-only change) | — |
| #109 (@link extraction) | +9 | `geojson.spec.ts` |
| **Total** | **+31** (new) + **18** (modified) | |

---

## Files Reviewed

### Issue #101 — SWE Common Complex Type Support (callback injection)

| File | Lines Changed | Scope |
|------|--------------|-------|
| `src/ogc-api/csapi/formats/swecommon/data-record.ts` | +47 | Add `ComponentParser` type export; add optional `componentParser` param to `parseField()` and `parseDataRecord()`; delegate complex types to callback when provided |
| `src/ogc-api/csapi/formats/swecommon/data-array.ts` | +29 | Import `ComponentParser` from `data-record.ts`; add optional `componentParser` param to `parseElementType()` and `parseDataArray()`; delegate complex types to callback |
| `src/ogc-api/csapi/formats/swecommon/parser.ts` | +4 (2 modified) | Pass `parseSWEComponent` as callback to `parseDataRecord()` and `parseDataArray()` call sites |
| `src/ogc-api/csapi/formats/swecommon/data-record.spec.ts` | +120 | 4 new tests: Vector delegation, DataArray delegation, backward-compat throw, nested callback forwarding |
| `src/ogc-api/csapi/formats/swecommon/data-array.spec.ts` | +83 | 3 new tests: Vector delegation, backward-compat throw, nested DataRecord forwarding |

### Issue #103 — Part 2 Cross-Reference @id Field Extraction

| File | Lines Changed | Scope |
|------|--------------|-------|
| `src/ogc-api/csapi/model.ts` | +10 | Add optional typed fields to 5 Part 2 interfaces (`systemId`, `datastreamId`, `samplingFeatureId`, `featureOfInterestId`, `controlStreamId`, `commandId`) |
| `src/ogc-api/csapi/formats/part2.ts` | +21 | Add tolerant `typeof === 'string'` extraction with conditional spread to all 5 parsers |
| `src/ogc-api/csapi/formats/part2.spec.ts` | +30/−20 | Update 5 existing cross-reference tests from `not.toHaveProperty` exclusion to positive extraction assertions; rename 1 test title |

### Issue #104 — ControlStream Navigation Methods

| File | Lines Changed | Scope |
|------|--------------|-------|
| `src/ogc-api/csapi/url_builder.ts` | +77 | Add `getControlStreamSystems()`, `getControlStreamProcedures()`, `getControlStreamHistory()` with full JSDoc |
| `src/ogc-api/csapi/url_builder.spec.ts` | +75 | 6 happy-path tests (2 per method) + 3 EndpointError guard assertions |

### Issue #105 — Query Parameter Name Remapping

| File | Lines Changed | Scope |
|------|--------------|-------|
| `src/ogc-api/csapi/url_builder.ts` | +23/−6 | Add `PARAM_NAME_MAP` static readonly object (6 mappings); refactor `buildQueryString()` to resolve wire names via map |
| `src/ogc-api/csapi/url_builder.spec.ts` | 13 lines modified | Update 13 test assertions to expect corrected OGC wire names |

### Issue #106 — Missing Part 2 Query Option Fields

| File | Lines Changed | Scope |
|------|--------------|-------|
| `src/ogc-api/csapi/model.ts` | +40 | Add `foiId` to 4 interfaces, `issueTime`/`executionTime` to ControlStreamQueryOptions, `sender` to CommandQueryOptions, new `CommandStatusQueryOptions` interface |
| `src/ogc-api/csapi/url_builder.ts` | +8 (signature change) | Update `getCommandStatus()` to accept `CommandStatusQueryOptions`, import new type |
| `src/ogc-api/csapi/url_builder.spec.ts` | +22 | 7 new tests: `foiId` on 4 resource types, `issueTime`/`executionTime`/`foiId` on ControlStream, `sender`/`foiId` on Command, `statusCode` on CommandStatus |
| `src/index.ts` | +1 | Export `CommandStatusQueryOptions` from barrel |

### Issue #107 — Narrow Nested Builder Method Option Types

| File | Lines Changed | Scope |
|------|--------------|-------|
| `src/ogc-api/csapi/url_builder.ts` | 12 signatures modified | Narrow 12 nested methods from `QueryOptions` to resource-specific types (`SystemQueryOptions`, `DatastreamQueryOptions`, `ObservationQueryOptions`, etc.) |

### Issue #108 — CSAPIResourceRef Type + Part 1 Interface Fields

| File | Lines Changed | Scope |
|------|--------------|-------|
| `src/ogc-api/csapi/model.ts` | +27 | Add `CSAPIResourceRef` interface with JSDoc; add `systemKindLink`, `platformLink`, `deployedSystemsLink`, `sampledFeatureLink` to 3 Part 1 interfaces |
| `src/index.ts` | +1 | Export `CSAPIResourceRef` from barrel |

### Issue #109 — @link Property Extraction in GeoJSON Parser

| File | Lines Changed | Scope |
|------|--------------|-------|
| `src/ogc-api/csapi/formats/geojson.ts` | +39 | Import `CSAPIResourceRef`; add `isCSAPIResourceRef()` type guard and `parseResourceRef()` helper (private); add conditional-spread extraction in System, Deployment, and SamplingFeature switch cases |
| `src/ogc-api/csapi/formats/geojson.spec.ts` | +125 | 9 new tests covering all @link fields with full/minimal/absent/malformed inputs |

### Supplementary — F34 Re-export Consolidation

| File | Lines Changed | Scope |
|------|--------------|-------|
| `src/ogc-api/csapi/formats/sensorml/physical-system.ts` | 2→1 line | Combine two re-export lines from `_helpers.js` into one |

---

## Overall Codebase Metrics (Cumulative)

| Metric | Phase 5.4 | Phase 5.5 | Delta |
|--------|----------:|----------:|------:|
| Production lines (CSAPI all) | 11,469 | 11,759 | +290 |
| Test lines (CSAPI all) | ~13,843 | 14,242 | +399 |
| Total lines (CSAPI) | ~25,312 | 26,001 | +689 |
| Production files | 28 | 28 | 0 |
| Test files (suites) | 29 | 29 | 0 |
| Test count | 1,251 | 1,282 | +31 |
| Test:production ratio | 1.21 | 1.21 | — |

### Key File Changes (Phase 5.4 → 5.5)

| File | Lines (5.4) | Lines (5.5) | Delta | Purpose |
|------|----:|----:|------:|---------|
| `model.ts` | 653 | 730 | +77 | `CSAPIResourceRef`, Part 2 @id fields, query option fields, `CommandStatusQueryOptions` |
| `url_builder.ts` | 2,171 | 2,307 | +136 | 3 ControlStream methods, `PARAM_NAME_MAP`, `getCommandStatus` signature, nested type narrowing |
| `url_builder.spec.ts` | 2,711 | 2,858 | +147 | Tests for #104, #105, #106 |
| `geojson.ts` | 420 | 459 | +39 | @link extraction (#109) |
| `geojson.spec.ts` | 478 | 603 | +125 | 9 @link tests + 2 augmented existing tests |
| `part2.ts` | 476 | 497 | +21 | Cross-reference @id extraction (#103) |
| `part2.spec.ts` | 925 | 927 | +2 | Modified 5 existing tests (net +2 lines) |
| `data-record.ts` | 178 | 225 | +47 | `ComponentParser` type, callback injection (#101) |
| `data-array.ts` | 497 | 526 | +29 | Callback injection (#101) |
| `data-record.spec.ts` | 223 | 343 | +120 | 4 complex type callback tests |
| `data-array.spec.ts` | 497 | 580 | +83 | 3 complex type callback tests |
| `parser.ts` (swecommon) | 1,305 | 1,307 | +2 | Pass `parseSWEComponent` at 2 call sites |
| `physical-system.ts` | 623 | 622 | −1 | Combine re-export lines (F34) |
| `index.ts` (root) | 250 | 252 | +2 | Export `CSAPIResourceRef` + `CommandStatusQueryOptions` |

---

## Phase 3 Lessons Learned Check

| # | Lesson | Status | Evidence |
|---|--------|--------|----------|
| **L1** | Audit upstream before building new layers | ✅ PASS | No new architectural layers. Callback injection (#101) extends existing parsers. `PARAM_NAME_MAP` (#105) is a private lookup table, not an architectural layer. |
| **L2** | Postel's Law governs client libraries | ✅ PASS | All new extraction uses tolerant conditional-spread: `typeof === 'string'` guards on @id fields (#103), `isCSAPIResourceRef()` guard on @link objects (#109). No extraction depends on validation. |
| **L3** | Don't couple validation to extraction | ✅ PASS | `isCSAPIResourceRef()` is a type guard for extraction, not a validation gate. `parseResourceRef()` includes optional fields only when present. |
| **L4** | Don't build parallel systems | ✅ PASS | #109 @link extraction follows the same conditional-spread pattern established by #103 @id extraction. No parallel parsing system. #101 callback injection avoids duplicate complex-type parsers. |
| **L5** | Verify upstream claims by reading source | ✅ PASS | All 10 issue findings reports cite specific spec sections (OGC 23-001/23-002) and source code lines. |
| **L6** | Real-world server data diverges from spec | ✅ PASS | `deployedSystems@link` uses `Array.isArray` + `filter(isCSAPIResourceRef).map(parseResourceRef)` — tolerates mixed-validity arrays. |
| **L7** | Smoke tests are essential | ✅ PASS | This entire review covers work surfaced by ST#22 findings. |
| **L8** | Layered architecture enables clean extension | ✅ PASS | #101 uses callback injection to break circular imports; #105 uses a private static map; both extend without disrupting layers. |
| **L10** | Type naming must avoid built-in collisions | ✅ PASS | `CSAPIResourceRef` uses `CSAPI` prefix. `CommandStatusQueryOptions` follows existing naming convention. `ComponentParser` is exported from `data-record.ts` only. |
| **L12** | "Build it right, but should we build it at all?" | ✅ PASS | Issues #99 (already supported), #100 (DEFERRED), #102 (DEFERRED), #110 (DEFERRED) were correctly assessed and NOT implemented. Only spec-normative gaps were fixed. |
| **L13** | AI drift can fabricate findings | ✅ PASS | Each findings report cross-checked spec citations against the actual OGC spec text. Issue #106 corrected 5 incorrect spec citations from the original issue. |

**Result:** 11/11 applicable lessons PASS. 0 WORSENED.

---

## Phase 2 Lessons Learned Check

| # | Lesson | Status | Evidence |
|---|--------|--------|----------|
| **L6** | Findings become work items | ✅ PASS | Phase 5.4 F34 (re-export consolidation) was addressed in commit `6d13268`. All 10 post-smoke-test issues had findings reports before implementation. |
| **L7** | DRY violations compound | ✅ PASS | `parseResourceRef()` is a single private helper used by 3 @link extraction sites (#109). `PARAM_NAME_MAP` centralizes 6 name mappings (#105). |
| **L10** | Smoke tests are read-only | ✅ PASS | All findings reports were observation-first: assess → recommend → scope → implement (or defer). |

**Result:** 3/3 applicable lessons PASS. 0 WORSENED.

---

## Prior Findings Status

### All Phase 3 findings (F1–F6 from 3.1 through 3.17): ✅ Still RESOLVED

No Phase 5.5 commits modify any Phase 3 file except `physical-system.ts` (cosmetic re-export consolidation F34). All prior findings remain resolved.

### Phase 5.1 findings:

| Finding | 5.4 Status | 5.5 Status | Evidence |
|---------|-----------|-----------|----------|
| [F1] POSITIVE: Consistent tolerant extraction pattern | ✅ Unchanged | ✅ **EXTENDED** | @id extraction (#103) and @link extraction (#109) both use same conditional-spread pattern |
| [F2] POSITIVE: Correct instant-vs-interval distinction | ✅ Unchanged | ✅ Unchanged | No change to time handling |
| [F3] POSITIVE: Opaque `result` pass-through | ✅ Unchanged | ✅ Unchanged | No change |
| [F4] POSITIVE: Cross-reference exclusion tested | ✅ Unchanged | ✅ **EVOLVED** | Cross-reference tests now verify extraction, not exclusion (#103) |
| [F5] POSITIVE: `normalizeObservedProperties()` | ✅ Unchanged | ✅ Unchanged | No change |
| [F6] POSITIVE: `parameters` array guard | ✅ Unchanged | ✅ Unchanged | No change |
| [F7] GAP: No test for unknown `resultType` enum → null | ✅ RESOLVED | ✅ Unchanged | Still resolved |
| [F8] GAP: No test for unknown `type` field → omitted | ✅ RESOLVED | ✅ Unchanged | Still resolved |
| [F9] GAP: Stale module-level JSDoc | ✅ RESOLVED | ✅ Unchanged | Still resolved |
| [F10] INFORMATIONAL: Barrel exports deferred to Task 9a | ✅ RESOLVED | ✅ Unchanged | Still resolved |
| [F11] INFORMATIONAL: `links` cast is trust-the-server | ℹ️ Unchanged | ℹ️ Unchanged | No change |

### Phase 5.2 findings:

| Finding | 5.4 Status | 5.5 Status | Evidence |
|---------|-----------|-----------|----------|
| [F12] POSITIVE: `normalizeStatusCode()` shared reuse | ✅ Unchanged | ✅ Unchanged | No change |
| [F13] POSITIVE: ControlStream parallels Datastream | ✅ Unchanged | ✅ **STRENGTHENED** | #104 adds 3 navigation methods; ControlStream is now fully symmetric with DataStream |
| [F14] POSITIVE: Time field asymmetry documented | ✅ Unchanged | ✅ Unchanged | No change |
| [F15] POSITIVE: Required vs. optional statusCode | ✅ Unchanged | ✅ Unchanged | No change |
| [F16] POSITIVE: Command parameters pass-through | ✅ Unchanged | ✅ Unchanged | No change |
| [F17] POSITIVE: All cross-ref fields excluded | ✅ Unchanged | ✅ **EVOLVED** | Cross-ref fields now extracted, not excluded (#103) — finding meaning updated |
| **[F18] GAP (minor): `@see` link precision for parseCommandStatus** | ⚠️ STILL OPEN | ⚠️ **STILL OPEN** | Issue #98 was closed as `not_planned`. Knowingly deferred — existing link is technically correct. |
| [F19] GAP: Fixture ID collision `cs-minimal` | ✅ RESOLVED | ✅ Unchanged | Still resolved |
| [F20] INFORMATIONAL: Part 2 suite complete | ℹ️ Unchanged | ℹ️ Unchanged | Still complete (now 43 tests + modified cross-ref assertions) |
| [F21] INFORMATIONAL: Command parameters fallback spec-driven | ℹ️ Unchanged | ℹ️ Unchanged | No change |

### Phase 5.3 findings:

| Finding | 5.4 Status | 5.5 Status | Evidence |
|---------|-----------|-----------|----------|
| [F22] POSITIVE: Schema response parsers delegate to SWE Common | ✅ Unchanged | ✅ Unchanged | No change |
| [F23] POSITIVE: Recursive delegation dispatches all 4 types | ✅ Unchanged | ✅ **STRENGTHENED** | #101 extends recursive delegation to DataRecord/DataArray via callback injection |
| [F24] POSITIVE: Complete cross-type test coverage | ✅ Unchanged | ✅ **EXTENDED** | 7 new callback delegation tests in data-record.spec.ts and data-array.spec.ts |
| [F25] POSITIVE: Integration wiring complete at 3 levels | ✅ Unchanged | ✅ Unchanged | No change to barrel exports structure |
| [F26] POSITIVE: E2E pipeline tests validate full chain | ✅ Unchanged | ✅ Unchanged | No change |
| [F27] CONSISTENCY: Duplicated `parseComponentEntry` | ✅ RESOLVED | ✅ Unchanged | Still resolved |
| [F28] GAP: TS2352 cast in `pipeline.spec.ts` | ✅ RESOLVED | ✅ Unchanged | Still resolved |
| [F29] POSITIVE: P4 JSDoc documentation | ✅ Unchanged | ✅ Unchanged | No change |
| [F30] POSITIVE: Schema response inline import types | ✅ Unchanged | ✅ Unchanged | No change |
| [F31] INFORMATIONAL: Phase 5 complete | ℹ️ Unchanged | ℹ️ Unchanged | Phase 5 parsing complete; current work is post-Phase-5 refinement |

### Phase 5.4 findings:

| Finding | 5.4 Status | 5.5 Status | Evidence |
|---------|-----------|-----------|----------|
| [F32] POSITIVE: Enum test gaps correctly closed | ✅ | ✅ Unchanged | No change |
| [F33] POSITIVE: DRY extraction of parseComponentEntry | ✅ | ✅ Unchanged | No change |
| **[F34] CONSISTENCY: Two separate re-export lines** | ⚠️ Trivial | ✅ **RESOLVED** | Commit `6d13268` combines re-export lines in `physical-system.ts` |
| [F35] POSITIVE: Fixture ID rename eliminates ambiguity | ✅ | ✅ Unchanged | No change |

**Summary:** 1 finding resolved (F34). 1 finding still open (F18 — knowingly deferred). All 23 positive findings maintained. 4 findings evolved/extended/strengthened.

---

## Phase 5.5 Findings — New

### [F36] POSITIVE: Callback injection breaks circular imports cleanly (#101)

Issue #101 solves the DataRecord/DataArray complex-type limitation with a clean architectural pattern: optional `componentParser` callback parameter. Key strengths:

1. **Backward compatible** — omitting the callback preserves the original throw behavior (tested explicitly)
2. **No circular imports** — `data-record.ts` defines `ComponentParser` type; `parser.ts` injects `parseSWEComponent` at the two call sites
3. **Callback forwarding** — both `parseDataRecord` and `parseDataArray` pass the callback through to nested recursive calls (tested explicitly)
4. **Exported type** — `ComponentParser` is exported from `data-record.ts` and imported by `data-array.ts`, enabling type-safe usage

The pattern follows L8 (layered architecture) and L1 (audit upstream — this is how the SensorML recursive delegation was already handled via `_helpers.ts`).

**Severity:** POSITIVE

---

### [F37] POSITIVE: Cross-reference @id fields extracted tolerantly across all 5 Part 2 parsers (#103)

Issue #103 reverses the prior design decision to exclude cross-reference fields. The implementation is consistent across all 5 parsers:

```typescript
...(typeof obj['system@id'] === 'string'
  ? { systemId: obj['system@id'] as string }
  : {}),
```

Each field uses:
- `typeof === 'string'` guard (tolerant — no crash on missing/non-string)
- Conditional spread (absent when not a string, not `undefined`)
- TypeScript property name mapped from the raw `@id` key (e.g., `system@id` → `systemId`)
- Optional on the interface (purely additive, zero backward compatibility risk)

The test updates correctly change from `not.toHaveProperty` exclusion assertions to positive extraction assertions, and the `'ignores all cross-reference fields'` test was renamed to `'extracts all cross-reference fields'`.

**Severity:** POSITIVE

---

### [F38] POSITIVE: PARAM_NAME_MAP provides single-source-of-truth parameter remapping (#105)

Issue #105 adds a static `PARAM_NAME_MAP` to `CSAPIQueryBuilder` that remaps 6 TypeScript property names to their OGC-normative wire names:

| TypeScript Name | OGC Wire Name | Spec Reference |
|----------------|---------------|----------------|
| `currentStatus` | `statusCode` | OGC 23-002 §13.5.3 |
| `systemId` | `system` | OGC 23-001 §16.6.3 |
| `observedPropertyId` | `observedProperty` | OGC 23-001 §16.5.5 |
| `controlledPropertyId` | `controlledProperty` | OGC 23-001 §16.5.6 |
| `foiId` | `foi` | OGC 23-001 §16.5.4 |
| `procedureId` | `procedure` | OGC 23-001 §16.5.3 |

Key design choices:
- `Readonly<Record<string, string>>` with `as const`-like immutability
- Applied in `buildQueryString()` via `??` fallback (unmapped keys pass through as-is)
- Zero TypeScript API change — consumer-facing property names are unchanged
- JSDoc with spec links on the map itself

**Severity:** POSITIVE

---

### [F39] POSITIVE: Missing query option fields fill spec-normative gaps (#106)

Issue #106 adds 7 spec-normative query parameters plus 1 new interface:

| Interface | New Fields | Spec Requirement |
|-----------|-----------|-----------------|
| `DatastreamQueryOptions` | `foiId` | Req 48 |
| `ObservationQueryOptions` | `foiId` | Req 51 |
| `ControlStreamQueryOptions` | `issueTime`, `executionTime`, `foiId` | Req 52, 53, 55 |
| `CommandQueryOptions` | `sender`, `foiId` | Req 59, 60 |
| `CommandStatusQueryOptions` (NEW) | `statusCode` | Req 61 |

The findings report also correctly identified and REJECTED 3 non-spec-normative fields that the original issue proposed:
- `dataStream` on Observations (not in §13.3)
- `controlStream` on Commands (not in §13.5)
- `reportTime` on CommandStatus (not in §13.6)

This shows rigorous spec-checking before implementation.

**Severity:** POSITIVE

---

### [F40] POSITIVE: Nested method option types narrowed from generic to resource-specific (#107)

Issue #107 narrows 12 nested builder methods from the generic `QueryOptions` base type to their appropriate resource-specific types:

- `getSystemDataStreams()`: `QueryOptions` → `DatastreamQueryOptions`
- `getSystemControlStreams()`: `QueryOptions` → `ControlStreamQueryOptions`
- `getSystemDeployments()`: `QueryOptions` → `DeploymentQueryOptions`
- `getDeploymentSystems()`: `QueryOptions` → `SystemQueryOptions`
- `getProcedureSystems()`: `QueryOptions` → `SystemQueryOptions`
- `getProcedureDataStreams()`: `QueryOptions` → `DatastreamQueryOptions`
- `getSamplingFeatureSystems()`: `QueryOptions` → `SystemQueryOptions`
- `getSamplingFeatureObservations()`: `QueryOptions` → `ObservationQueryOptions`
- `getPropertySystems()`: `QueryOptions` → `SystemQueryOptions`
- `getPropertyDataStreams()`: `QueryOptions` → `DatastreamQueryOptions`
- `getPropertyControlStreams()`: `QueryOptions` → `ControlStreamQueryOptions`
- `getDataStreamSystems()`: `QueryOptions` → `SystemQueryOptions`

This is a type-safety improvement with zero runtime impact. All specific option types extend `QueryOptions`, so existing code continues to compile.

**Severity:** POSITIVE

---

### [F41] POSITIVE: CSAPIResourceRef type and Part 1 interface @link fields (#108)

Issue #108 establishes the type foundation for @link property support:

```typescript
export interface CSAPIResourceRef {
  href: string;       // URL of the referenced resource
  uid?: string;       // Globally unique identifier
  title?: string;     // Human-readable title
  rt?: string;        // Resource type URI
}
```

Key qualities:
- Only `href` is required (per observed server behavior — minimal objects common)
- Optional fields use TypeScript's `?` syntax correctly
- JSDoc includes `@see` link to OGC 23-001 §16
- Exported from `src/index.ts` for consumer access
- Interface fields on Part 1 types use descriptive names (`systemKindLink`, `platformLink`, `deployedSystemsLink`, `sampledFeatureLink`) that clearly indicate the source `@link` property

**Severity:** POSITIVE

---

### [F42] POSITIVE: @link extraction in GeoJSON parser with robust array handling (#109)

Issue #109 adds @link extraction to `extractCSAPIFeature()` across 3 resource types. The implementation includes:

1. **Private type guard** (`isCSAPIResourceRef`): checks `typeof === 'object' && !== null && typeof href === 'string'` — correctly identifies valid @link objects
2. **Private parser** (`parseResourceRef`): extracts only known fields with `typeof === 'string'` guards on optional fields
3. **Array handling for Deployment**: `deployedSystems@link` uses `Array.isArray()` + `filter(isCSAPIResourceRef).map(parseResourceRef)` — malformed entries are silently filtered
4. **Conditional spread**: absent @link → key absent from output (not `undefined`)

Test coverage is comprehensive (9 tests):
- Full @link with all fields (System, Deployment, SamplingFeature)
- Minimal @link with only `href`
- Absent @link (tolerant extraction)
- Malformed @link missing `href` → silently skipped
- Malformed @link as string → silently skipped
- Mixed-validity array entries → valid-only extracted

**Severity:** POSITIVE

---

### [F43] POSITIVE: ControlStream navigation methods restore full symmetry with DataStream (#104)

Issue #104 adds 3 methods that DataStream already had but ControlStream lacked:
- `getControlStreamSystems()`
- `getControlStreamProcedures()`
- `getControlStreamHistory()`

Each follows the established builder method pattern: validate resource availability via `assertResourceAvailable()`, delegate to `buildResourceUrl()`, full JSDoc with `@param`, `@returns`, `@throws`, `@example`, `@see`. The OGC 23-002 Table 10 defines identical association structures for DataStream and ControlStream — this was the only remaining asymmetry.

**Severity:** POSITIVE

---

### [F44] POSITIVE: Correct deferral of 3 out-of-scope issues (#99, #100/102, #110)

Issues #99, #100, #102, and #110 were correctly assessed and NOT implemented:
- **#99** (query format parameter): Already supported — `f` parameter passes through `buildQueryString()`
- **#100** (assertResourceAvailable for per-ID methods): DEFERRED — holistic fix needed for all 69 methods
- **#102** (command/observation nested paths): DEFERRED — strict subset of #100, same root cause
- **#110** (@link resolution utilities): DEFERRED — outside contribution scope, architectural layer violation

Each deferral has a findings report with spec citations, risk assessment, and clear reasoning. This demonstrates L12 ("should we build it at all?") in practice.

**Severity:** POSITIVE

---

### [F45] DESIGN (minor): `getCommandStatus()` uses string concatenation for query string

In `url_builder.ts`, `getCommandStatus()` appends the query string via concatenation rather than passing `options` to `buildResourceUrl()`:

```typescript
getCommandStatus(id: string, options?: CommandStatusQueryOptions): string {
  this.assertResourceAvailable('commands');
  return this.buildResourceUrl('commands', id, 'status') + this.buildQueryString(options);
}
```

All other methods pass `options` to `buildResourceUrl()` which internally calls `buildQueryString()`:

```typescript
getDataStreamObservations(id: string, options?: ObservationQueryOptions): string {
  this.assertResourceAvailable('datastreams');
  return this.buildResourceUrl('datastreams', id, 'observations', options);
}
```

This deviation exists because `getCommandStatus()` is a sub-resource of a per-ID method (commands/{id}/status) and the `buildResourceUrl()` 4th parameter slot was designed for query options on collection-level paths. The result is functionally correct — both approaches produce `?key=value` query strings — but the pattern inconsistency is notable.

**Impact:** Zero functional impact. Both code paths use the same `buildQueryString()` method. The concatenation approach is actually more explicit about what's happening.

**Severity:** DESIGN (minor)

---

### [F46] CONSISTENCY: `getControlStreamProcedures` uses `QueryOptions` instead of `ProcedureQueryOptions`

In Issue #104, `getControlStreamProcedures()` uses base `QueryOptions`:

```typescript
getControlStreamProcedures(id: string, options?: QueryOptions): string {
```

While `getControlStreamSystems()` correctly uses `SystemQueryOptions`:

```typescript
getControlStreamSystems(id: string, options?: SystemQueryOptions): string {
```

Since Issue #107 narrowed all nested methods to resource-specific types, this new method should follow the same pattern. `ProcedureQueryOptions` is available in the codebase.

**Impact:** Low — `ProcedureQueryOptions` currently extends `QueryOptions` without adding fields, so there's no functional gap. But future additions to `ProcedureQueryOptions` would not be available on this method.

**Severity:** CONSISTENCY (low)

---

### [F47] GAP (minor): No test for `getCommandStatus` with combined `statusCode` + `limit` options

The `getCommandStatus` tests cover `statusCode` alone and `limit` alone, but not the combination:

```typescript
it('getCommandStatus returns correct URL with statusCode filter', () => { ... });
it('getCommandStatus returns correct URL with limit option', () => { ... });
```

Most other multi-option methods have a combined test (e.g., `getCommands({ limit: 10, currentStatus: 'PENDING', cursor: 'abc' })`). This is a minor gap since `buildQueryString()` handles multiple options generically, but it would strengthen coverage.

**Impact:** Very low — the combined case is guaranteed by `buildQueryString()` behavior.

**Severity:** GAP (minor)

---

## Test Quality Heatmap

### Phase 2 (URL Builder) — Updated

| Dimension | Systems | Deployments | Procedures | SF | Properties | DataStreams | Observations | ControlStreams | Commands | CmdStatus |
|-----------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| GET list URL | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| GET by ID URL | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Query options serialized | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Param name remapping (#105) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | n/a |
| Nested method types (#107) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | n/a | n/a |
| Resource validation | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Navigation methods | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ (#104) | ✅ | n/a |

### Phase 3 (Format Handlers) — Updated

| Dimension | GeoJSON | SWE Types | SML Types | Parsers |
|-----------|:---:|:---:|:---:|:---:|
| Valid input → typed output | ✅ | ✅ | ✅ | ✅ |
| Invalid/missing input | ✅ | ✅ | ✅ | ✅ |
| Complex type delegation (#101) | n/a | ✅ | ✅ | ✅ |
| @link extraction (#109) | ✅ | n/a | n/a | n/a |
| Malformed @link tolerance | ✅ | n/a | n/a | n/a |

### Phase 5 (Parser Completion) — Updated

| Dimension | parseProperty | parseDatastream | parseObservation | parseControlStream | parseCommand | parseCommandStatus |
|-----------|:---:|:---:|:---:|:---:|:---:|:---:|
| Fixture → typed output | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Minimal fixture | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Non-object rejection | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Cross-ref @id extraction (#103) | n/a | ✅ | ✅ | ✅ | ✅ | ✅ |
| Time field correctness | n/a | ✅ | ✅ | ✅ | ✅ | ✅ |
| Optional field handling | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Opaque pass-through | n/a | n/a | ✅ | n/a | ✅ | n/a |
| Enum validation | n/a | ✅ | n/a | n/a | ✅ | ✅ |
| `satisfies` typing | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

**Changes from Phase 5.4:** "Cross-ref exclusion" row renamed to "Cross-ref @id extraction" — tests now verify extraction, not exclusion. All cells remain ✅.

---

## Smoke Test Findings Integration

| Finding | Status | Evidence |
|---------|--------|----------|
| F27 (Observation `foi@id`) | ✅ Addressed (Phase 5.1) | No regression. `featureOfInterestId` now extracted (#103). |
| F30 (ControlStream `system@link`) | ✅ Addressed (Phase 5.2) | No regression. `system@link` still excluded from Part 2 model (raw @link is server-specific). |
| F31 (Command `controlstream@id`) | ✅ Addressed (Phase 5.2) | No regression. `controlStreamId` now extracted (#103). |
| F33 (ControlStream schema `commandFormat`/`parametersSchema`) | ✅ Addressed (Phase 5.3) | No regression. |
| F38 (CommandStatus data shape) | ✅ Addressed (Phase 5.2) | No regression. `commandId` now extracted (#103). |

All 5 smoke test findings remain addressed. ✅

---

## Summary

| Category | Count | Details |
|----------|------:|---------|
| POSITIVE | 9 | F36 (callback injection), F37 (@id extraction), F38 (PARAM_NAME_MAP), F39 (query fields), F40 (type narrowing), F41 (CSAPIResourceRef), F42 (@link extraction), F43 (ControlStream symmetry), F44 (correct deferrals) |
| DESIGN | 1 | F45 (getCommandStatus query string concatenation — minor) |
| CONSISTENCY | 1 | F46 (getControlStreamProcedures uses QueryOptions — low) |
| GAP | 1 | F47 (no combined-option test for getCommandStatus — minor) |
| BUG | 0 | — |
| INFORMATIONAL | 0 | — |

**Prior findings resolved this review:** 1 (F34 — re-export consolidation)
**Prior findings still open:** 1 (F18 — parseCommandStatus `@see` link precision, knowingly deferred via Issue #98 closed as not_planned)
**Prior findings evolved/extended:** 4 (F1 pattern extended, F4/F17 cross-ref evolved from exclusion to extraction, F13 ControlStream strengthened, F23/F24 recursive delegation extended)

---

## Recommendations

### Fix Now (before next issue)

None. All new findings are minor. The codebase is in clean, shippable state.

### Fix Before Phase 6 (before upstream submission)

**1. Narrow `getControlStreamProcedures` option type (F46)**

Change `options?: QueryOptions` to `options?: ProcedureQueryOptions` for consistency with Issue #107's type narrowing across all nested methods.

```typescript
// Current:
getControlStreamProcedures(id: string, options?: QueryOptions): string {
// Suggested:
getControlStreamProcedures(id: string, options?: ProcedureQueryOptions): string {
```

### Defer (Low Priority)

**2. Add combined-option test for getCommandStatus (F47)**

```typescript
it('getCommandStatus returns correct URL with statusCode + limit', () => {
  const url = makeCmdBuilder().getCommandStatus('cmd-001', { statusCode: 'EXECUTING', limit: 5 });
  expect(url).toBe('..../commands/cmd-001/status?statusCode=EXECUTING&limit=5');
});
```

**3. Consider unifying getCommandStatus query string approach (F45)**

Low priority — functionally correct, just a pattern deviation. Could be addressed during a broader builder refactoring.

**4. Improve `@see` link precision for parseCommandStatus (F18) — carried forward**

Knowingly deferred since Phase 5.2.

---

## Root Cause Analysis

No defects found. This is the fifth consecutive Phase 5 code review with zero bugs and zero critical design concerns. The streak spans Issues #81–#110 (30 issues) and 47 findings (F1–F47), 38 of which are POSITIVE.

---

## Overall Assessment

Phase 5.5 is the largest single review in the Phase 5 series, covering 8 implementation issues and 4 findings-only/deferred issues. The scope spans three distinct concern areas:

1. **Parser enhancements** (#101 SWE Common complex types, #103 Part 2 @id extraction, #108/#109 Part 1 @link handling) — these fill genuine spec-conformance gaps in the parser layer. The callback injection pattern (#101) is particularly well-designed: it extends `parseDataRecord()` and `parseDataArray()` to handle all 16 AbstractDataComponent types without circular imports, maintaining backward compatibility for standalone callers. The @link extraction (#109) follows the identical conditional-spread pattern established by @id extraction (#103), demonstrating consistent architectural thinking.

2. **Query builder improvements** (#104 ControlStream navigation, #105 parameter remapping, #106 query option fields, #107 type narrowing) — these are all additive, backward-compatible refinements to the URL builder. The `PARAM_NAME_MAP` (#105) is a clean, centralized solution to the 6 parameter name mismatches discovered during smoke testing. Type narrowing (#107) is a zero-runtime-cost improvement that gives consumers better IDE autocomplete and compile-time safety.

3. **Correct deferrals** (#99, #100, #102, #110) — four issues were assessed as out-of-scope, already-supported, or architecturally inappropriate, and all were correctly NOT implemented. The findings reports provide thorough justification with spec citations. This demonstrates disciplined scope management throughout the post-smoke-test work.

The codebase has grown by 689 lines since Phase 5.4, maintaining a healthy 1.21:1 test-to-production ratio. Test count increased by 31 (1251 → 1282) across 29 suites. TypeScript compiles cleanly with zero errors. The two minor findings (F46 consistency, F47 gap) are trivial — neither affects correctness or runtime behavior.

With 1,282 CSAPI tests, 740 format tests, 0 tsc errors, and only 2 minor open findings (F18 knowingly deferred, F46 type narrowing gap), the CSAPI codebase is in its most complete state.
