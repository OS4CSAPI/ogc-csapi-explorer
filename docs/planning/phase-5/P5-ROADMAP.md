# Phase 5: Parser Completion — Roadmap

**Version:** 1.1  
**Date:** February 19, 2026  
**Status:** Draft — Pending Review  
**Scope:** 9 parser gaps only (from [Parsing Coverage Audit](../../research/phase-5/parsing-coverage-audit.md))

---

## Executive Summary

This roadmap covers the implementation of **9 parser gaps** identified by the Parsing Coverage Audit, organized into **9 tasks (14 execution units)** spanning an estimated **14–22 hours of development time** (2–3 weeks calendar time).

Tasks 2, 5, 7, 8, and 9 are broken into subtasks to ensure each execution unit can be completed confidently in a single pass. Tasks 1, 3, 4, and 6 are simple enough to execute as single units.

**What this covers:**

- 6 resource parse functions (Property, Datastream, Observation, ControlStream, Command, CommandStatus)
- 2 schema response parse functions (DatastreamSchemaResponse, ControlStreamSchemaResponse)
- 1 recursive delegation fix in 2 files (physical-system.ts, aggregate-process.ts)

**Estimated volume:**

- ~300–500 lines of implementation across 3 new files + 2 modified files
- ~400–600 lines of tests across 3 new spec files + 2 modified spec files
- 2 new TypeScript interfaces (DatastreamSchemaResponse, ControlStreamSchemaResponse)

**What this does NOT cover:** QueryBuilder methods (complete), URL building (complete), format detection (complete), GeoJSON handler extensions (complete), SWE Common parsers (complete), SensorML parsers (complete except Gap #9), collection envelope handling (complete), content negotiation, integration tests, worker extensions, or any other work outside the 9 parser gaps. See the main [ROADMAP](../ROADMAP.md) (Version 3.4) for Phases 1–4 scope.

**Key Facts:**

- All 6 resource type interfaces already exist in `model.ts` — no type system work except 2 new schema response interfaces
- `parseValidTime()` already exists in `geojson.ts` and handles all time interval cases — reuse, don't reimplement
- `parseSWEComponent()` already exists — schema response parsers delegate to it
- Test suite baseline: 1,525 passed, 5 failed (pre-existing, non-CSAPI), 53 suites

**Execution unit summary:**

| #   | Unit                                                          | Est. Time | Complexity  |
| --- | ------------------------------------------------------------- | --------- | ----------- |
| 1   | Task 1: parseProperty + tests                                 | ~1–1.5h   | Low         |
| 2   | Task 2a: parseDatastream implementation                       | ~1–1.5h   | Medium      |
| 3   | Task 2b: parseDatastream fixtures + tests                     | ~1–1.5h   | Medium      |
| 4   | Task 3: parseObservation + tests                              | ~1.5–2h   | Medium      |
| 5   | Task 4: parseControlStream + tests                            | ~1.5–2h   | Medium      |
| 6   | Task 5a: normalizeStatusCode + parseCommand implementation    | ~1–1.5h   | Medium-High |
| 7   | Task 5b: parseCommand fixtures + tests                        | ~0.5–1h   | Medium      |
| 8   | Task 6: parseCommandStatus + tests                            | ~1–1.5h   | Medium      |
| 9   | Task 7a: parseDatastreamSchemaResponse + interface + tests    | ~1–1.5h   | Medium      |
| 10  | Task 7b: parseControlStreamSchemaResponse + interface + tests | ~1–1.5h   | Medium      |
| 11  | Task 8a: Recursive delegation code fix + regression run       | ~0.5–1h   | Medium-High |
| 12  | Task 8b: Cross-type component test cases + fixtures           | ~1–1.5h   | Medium      |
| 13  | Task 9a: Wire parsers into QueryBuilder call sites            | ~0.5–1h   | Medium      |
| 14  | Task 9b: End-to-end pipeline tests                            | ~0.5–1h   | Medium      |

**Success Factors:**

- Write tests immediately after each parser (not batched at end)
- Follow tolerant extraction philosophy — never gate on missing fields
- Maintain >80% code coverage on all new parser files
- Use `parseValidTime()` for all time intervals; pass through ISO 8601 instants as strings
- Use spec-derived fixtures for Property (no server returns Property data)

---

## Task Ordering Rationale

Tasks are ordered by **complexity progression** and **dependency chain**:

1. **Simplest first** — `parseProperty()` is a flat JSON object with no time fields, making it the ideal starting point to establish the parse function pattern (input guard, field extraction, typed return) without time-parsing complexity.

2. **Part 2 resource parsers in dependency order** — Datastream and ControlStream introduce time interval parsing via `parseValidTime()`. Observation and Command build on those patterns while adding cross-reference handling and status normalization. CommandStatus is last because it shares patterns with both Command (status codes) and Datastream (time intervals) and introduces the `normalizeStatusCode()` shared utility.

3. **Schema response parsers after resource parsers** — Schema parsers delegate to the existing SWE Common parser layer. Implementing them after the resource parsers ensures the pattern (input guard → extract fields → delegate to existing parser → return typed result) is well-practiced.

4. **Recursive delegation fix after all parsers** — Gap #9 modifies 2 existing files rather than creating new ones. It requires `parseSensorML30()` from `parser.ts`, introducing a circular import that must be verified against the test suite. Doing this last means all new parsers are stable and the test suite is a reliable regression baseline.

5. **Integration wiring last** — Connecting the new parsers to the `parseCollectionResponse()` pipeline is glue code that depends on all parsers existing. It also serves as a natural end-to-end validation checkpoint.

**Subtask rationale:** Tasks are split into subtasks when they involve multiple concerns that benefit from separate focus — e.g., creating a new file with implementation vs constructing fixtures and writing tests, or modifying existing code vs verifying the modification with new test cases. Each subtask is scoped to be completable in a single pass with high confidence.

---

## Tasks

### Task 1: `parseProperty()` + Tests

**Estimated Time:** ~1–1.5 hours  
**Complexity:** Low  
**Gap:** #1 from Parsing Coverage Audit  
**File:** `src/ogc-api/csapi/formats/property.ts` (new)  
**Test File:** `src/ogc-api/csapi/formats/property.spec.ts` (new)

- Implement `parseProperty(json: unknown): Property`
- Input guard: throw if input is not a non-null object
- Extract flat fields: `id`, `label`, `description`, `uniqueId`, `baseProperty`, `objectType`, `statistic`, `links`
- **No `validTime`** — Property is a `DerivedProperty` (SWE Common `AbstractSweIdentifiable`), which has no time field. See [validTime coverage analysis](../../research/phase-5/validtime-coverage-analysis.md).
- No GeoJSON wrapping — Property is the only Part 1 resource that is NOT a GeoJSON Feature
- Fall back to empty string for `label`, `uniqueId`, `baseProperty`; undefined for optional fields
- **Test:** 6 cases — full Property, minimal Property, missing optional fields, empty links array, non-object input throws, `id` absent (server-assigned)
- **Fixtures:** Spec-derived from OGC 23-001 `DerivedProperty` schema (no server returns Property data — confirmed ST#6)
- **JSDoc:** Document function with input/output examples, note spec-only fixture basis
- **Dependencies:** None

---

### Task 2: `parseDatastream()`

**Gap:** #2 from Parsing Coverage Audit  
**File:** `src/ogc-api/csapi/formats/part2.ts` (new)  
**Test File:** `src/ogc-api/csapi/formats/part2.spec.ts` (new)  
**Dependencies:** None (imports `parseValidTime()` from `geojson.ts`)

#### Task 2a: `parseDatastream()` Implementation

**Estimated Time:** ~1–1.5 hours  
**Complexity:** Medium

This is the first Part 2 parser and creates the `part2.ts` file. The primary risk is establishing the correct import pattern for `parseValidTime()` and handling 13+ fields with 3 time fields.

- Create `src/ogc-api/csapi/formats/part2.ts`
- Study `parseValidTime()` signature and return type in `geojson.ts` before writing any code
- Study `Datastream` interface in `model.ts` to confirm all field names and types
- Implement `parseDatastream(json: unknown): Datastream`
- Input guard: throw if input is not a non-null object
- Parse 3 time fields via `parseValidTime()`: `validTime`, `phenomenonTime`, `resultTime`
- Extract: `id`, `name`, `description`, `formats`, `outputName`, `observedProperties`, `resultType`, `live`, `type`, `links`
- Normalize `observedProperties`: handle both object array and string array forms
- Cross-references (`system@id`, `system@link`) are NOT extracted — not in the `Datastream` interface
- **JSDoc:** Document time field handling, `observedProperties` normalization
- **Deliverable:** Compiling `parseDatastream()` function with all field extractions + JSDoc

#### Task 2b: `parseDatastream()` Fixtures + Tests

**Estimated Time:** ~1–1.5 hours  
**Complexity:** Medium

- Create `src/ogc-api/csapi/formats/part2.spec.ts`
- Build Datastream fixtures from real OSH response data (Smoke Test #7)
- **Test:** 8 cases:
  1. Full Datastream — all fields from real OSH response
  2. Minimal Datastream — only `id` (required per spec)
  3. All 3 time fields parsed — verify `TimeInterval` output
  4. `observedProperties` as objects — array of `{ definition, label }` objects
  5. `observedProperties` as strings — array of URI strings
  6. `phenomenonTime` null — passes through as null (not undefined)
  7. Missing optional fields — undefined in output
  8. Non-object input — throws Error
- **Deliverable:** Passing test suite with >80% coverage on `parseDatastream()`

---

### Task 3: `parseObservation()` + Tests

**Estimated Time:** ~1.5–2 hours  
**Complexity:** Medium  
**Gap:** #3 from Parsing Coverage Audit  
**File:** `src/ogc-api/csapi/formats/part2.ts` (same file as Task 2)  
**Test File:** `src/ogc-api/csapi/formats/part2.spec.ts` (same file as Task 2)

- Implement `parseObservation(json: unknown): Observation`
- Input guard: throw if input is not a non-null object
- Time fields are **instants** (single ISO 8601 strings), not intervals — pass through as strings, do NOT use `parseValidTime()`
- Extract: `id`, `phenomenonTime`, `resultTime`, `parameters`, `result`, `links`
- `result` is an opaque `Record<string, unknown>` pass-through — the parser does not interpret result values
- Cross-references (`datastream@id`, `foi@id`, `samplingFeature@id`) are NOT extracted — not in the `Observation` interface
- **Test:** 7 cases — full Observation (OSH ST#8), minimal Observation, `result` as nested object, `parameters` present, `phenomenonTime` absent, empty result, non-object input throws
- **Fixtures:** Real OSH response data from Smoke Test #8
- **JSDoc:** Document instant vs interval distinction for time fields
- **Dependencies:** Task 2 (shares file, establishes Part 2 parsing pattern)

---

### Task 4: `parseControlStream()` + Tests

**Estimated Time:** ~1.5–2 hours  
**Complexity:** Medium  
**Gap:** #4 from Parsing Coverage Audit  
**File:** `src/ogc-api/csapi/formats/part2.ts`  
**Test File:** `src/ogc-api/csapi/formats/part2.spec.ts`

- Implement `parseControlStream(json: unknown): ControlStream`
- Input guard: throw if input is not a non-null object
- Parse 3 time fields via `parseValidTime()`: `validTime`, `issueTime`, `executionTime`
- Extract: `id`, `name`, `description`, `formats`, `inputName`, `controlledProperties`, `live`, `async`, `links`
- Structurally parallel to `parseDatastream()` — same time field parsing, analogous fields
- Cross-references (`system@id`, `system@link`) are NOT extracted
- **Test:** 7 cases — full ControlStream (OSH ST#9 F30), minimal ControlStream, all 3 time fields parsed, `controlledProperties` array, missing optional fields, `async` boolean handling, non-object input throws
- **Fixtures:** Real OSH response data from Smoke Test #9 (F30)
- **JSDoc:** Document parallel structure with Datastream parser
- **Dependencies:** Task 2 (shares file, reuses established patterns)

---

### Task 5: `parseCommand()`

**Gap:** #5 from Parsing Coverage Audit  
**File:** `src/ogc-api/csapi/formats/part2.ts`  
**Test File:** `src/ogc-api/csapi/formats/part2.spec.ts`  
**Dependencies:** Task 2 (shares file)

#### Task 5a: `normalizeStatusCode()` Utility + `parseCommand()` Implementation

**Estimated Time:** ~1–1.5 hours  
**Complexity:** Medium-High

The key challenge is the `issueTime`/`executionTime` type asymmetry (instant vs period) and introducing the shared `normalizeStatusCode()` utility that Task 6 will also use.

- Implement `normalizeStatusCode(value: unknown): CommandStatusCode | undefined`
  - Validate string against `CommandStatusCodes` array from `model.ts`
  - Return typed `CommandStatusCode` if recognized, `undefined` if not
  - ~5 lines — small but must be correct since Task 6 depends on it
- Implement `parseCommand(json: unknown): Command`
- Input guard: throw if input is not a non-null object
- `issueTime` is an ISO 8601 **instant** (string pass-through) — NOT `parseValidTime()`
- `executionTime` is a time **period** (array of 2 strings) — parse with `parseValidTime()`
- Validate `currentStatus` via `normalizeStatusCode()`; fall back to undefined if unrecognized
- Extract: `id`, `issueTime`, `executionTime`, `sender`, `currentStatus`, `parameters`, `links`
- Cross-reference (`controlstream@id`) is NOT extracted
- **JSDoc:** Document `issueTime`/`executionTime` type asymmetry, status code normalization, `normalizeStatusCode()` utility
- **Deliverable:** Compiling `normalizeStatusCode()` + `parseCommand()` with all field extractions + JSDoc

#### Task 5b: `parseCommand()` Fixtures + Tests

**Estimated Time:** ~0.5–1 hour  
**Complexity:** Medium

- Build Command fixtures from real OSH response data (Smoke Test #10, F31)
- **Test:** 8 cases:
  1. Full Command — all fields from real OSH response (F31)
  2. Minimal Command — only `id`, `issueTime`, `parameters` (required per spec)
  3. `currentStatus` valid — `"COMPLETED"` → `'COMPLETED'`
  4. `currentStatus` invalid — unknown string → `undefined`
  5. `executionTime` present — parsed to `TimeInterval`
  6. `executionTime` absent — not in output
  7. Complex nested parameters — deep object pass-through
  8. Non-object input — throws Error
- Also test `normalizeStatusCode()` directly: valid code, invalid code, non-string input, undefined input
- **Deliverable:** Passing test suite with >80% coverage on `parseCommand()` and `normalizeStatusCode()`

---

### Task 6: `parseCommandStatus()` + Tests

**Estimated Time:** ~1–1.5 hours  
**Complexity:** Medium  
**Gap:** #6 from Parsing Coverage Audit  
**File:** `src/ogc-api/csapi/formats/part2.ts`  
**Test File:** `src/ogc-api/csapi/formats/part2.spec.ts`

- Implement `parseCommandStatus(json: unknown): CommandStatus`
- Input guard: throw if input is not a non-null object
- `reportTime` is an ISO 8601 **instant** (string pass-through)
- `executionTime` is a time **period** — parse with `parseValidTime()`
- `statusCode` is **required** (unlike `currentStatus` on Command which is optional) — fall back to `'PENDING'` if missing or unrecognized, not undefined
- Reuse `normalizeStatusCode()` from Task 5, with `'PENDING'` as the default for required context
- Extract: `id`, `reportTime`, `statusCode`, `percentCompletion`, `executionTime`, `message`, `links`
- Cross-reference (`command@id`) is NOT extracted
- **Test:** 7 cases — full CommandStatus (OSH ST#10 F38), minimal CommandStatus, `statusCode` valid, `statusCode` invalid → `'PENDING'` fallback, `percentCompletion` present, `executionTime` present → TimeInterval, non-object input throws
- **Fixtures:** Real OSH response data from Smoke Test #10 (F38)
- **JSDoc:** Document required `statusCode` vs optional `currentStatus` distinction
- **Dependencies:** Task 5a (`normalizeStatusCode()` utility)

---

### Task 7: Schema Response Parsers

**Gap:** #7 and #8 from Parsing Coverage Audit  
**File:** `src/ogc-api/csapi/formats/schema-response.ts` (new)  
**Test File:** `src/ogc-api/csapi/formats/schema-response.spec.ts` (new)  
**Cross-reference:** Issue #17 (demo app finding F-14) first identified this gap  
**Dependencies:** None (delegates to existing SWE Common parsers)

#### Task 7a: `parseDatastreamSchemaResponse()` + Interface + Tests

**Estimated Time:** ~1–1.5 hours  
**Complexity:** Medium

This subtask does the hard work: creating the new file, establishing the delegation pattern to `parseSWEComponent()` and `parseEncoding()`, and handling the two format variants (JSON vs SWE Common). Study the `parseSWEComponent()` and `parseEncoding()` APIs in the SWE Common parser before writing code.

- Define `DatastreamSchemaResponse` interface in `model.ts` (~10-15 lines):
  - `obsFormat: string`
  - `resultSchema?: SWEComponent` (JSON format)
  - `recordSchema?: SWEComponent` (SWE Common format)
  - `encoding?: DataEncoding` (SWE Common format)
- Create `src/ogc-api/csapi/formats/schema-response.ts`
- Implement `parseDatastreamSchemaResponse(json: unknown): DatastreamSchemaResponse`
  - Input guard: throw if input is not a non-null object
  - Extract `obsFormat` (fall back to empty string)
  - Delegate `resultSchema` to `parseSWEComponent()` if present
  - Delegate `recordSchema` to `parseSWEComponent()` if present
  - Delegate `encoding` to `parseEncoding()` if present
- Create `src/ogc-api/csapi/formats/schema-response.spec.ts`
- **Test:** 5 cases:
  1. JSON format response — `obsFormat` + `resultSchema` with DataRecord
  2. SWE Common format response — `obsFormat` + `recordSchema` + `encoding`
  3. Missing schema fields — only `obsFormat` present
  4. Nested DataRecord — schema with multiple fields → full SWE parse tree
  5. Non-object input — throws Error
- **Fixtures:** Real OSH schema response data from Smoke Test #7
- **JSDoc:** Document delegation to SWE Common parser, schema format variants
- **Deliverable:** `DatastreamSchemaResponse` interface + compiling parser + passing tests

#### Task 7b: `parseControlStreamSchemaResponse()` + Interface + Tests

**Estimated Time:** ~1–1.5 hours  
**Complexity:** Medium

This subtask follows the pattern established by 7a. The delegation pattern is identical — only the field names differ (`commandFormat` instead of `obsFormat`, `parametersSchema` instead of `resultSchema`/`recordSchema`).

- Define `ControlStreamSchemaResponse` interface in `model.ts` (~8-10 lines):
  - `commandFormat: string`
  - `parametersSchema?: SWEComponent`
  - `encoding?: DataEncoding`
- Implement `parseControlStreamSchemaResponse(json: unknown): ControlStreamSchemaResponse` in `schema-response.ts`
  - Input guard: throw if input is not a non-null object
  - Extract `commandFormat` (fall back to empty string)
  - Delegate `parametersSchema` to `parseSWEComponent()` if present
  - Delegate `encoding` to `parseEncoding()` if present
- **Test:** 4 cases:
  1. JSON format response — `commandFormat` + `parametersSchema` with DataRecord
  2. Missing parametersSchema — only `commandFormat` present
  3. Nested DataRecord — full SWE parse tree verified
  4. Non-object input — throws Error
- **Fixtures:** Spec-derived for ControlStream schema (no real server fixture available for this specific endpoint)
- **JSDoc:** Document parallel structure with Datastream schema parser
- **Deliverable:** `ControlStreamSchemaResponse` interface + compiling parser + passing tests

---

### Task 8: Recursive Delegation Fix

**Gap:** #9 from Parsing Coverage Audit  
**Files Modified:** `src/ogc-api/csapi/formats/sensorml/physical-system.ts`, `src/ogc-api/csapi/formats/sensorml/aggregate-process.ts`  
**Test Files Modified:** existing `physical-system.spec.ts`, `aggregate-process.spec.ts`  
**Dependencies:** None (modifies existing files, no dependency on Tasks 1–7)

#### Task 8a: Code Fix + Circular Import Verification

**Estimated Time:** ~0.5–1 hour  
**Complexity:** Medium-High

The code change is small (~10-15 lines per file) but introduces a circular import that must be verified. This subtask focuses solely on making the code change and confirming the existing test suite still passes.

- Read both `parseComponentEntry()` functions to understand current behavior
- Modify `physical-system.ts`:
  - Add `import { parseSensorML30 } from './parser'`
  - Replace type-specific check (`value.type === 'PhysicalSystem'`) with `knownTypes.includes(value.type)` for all 4 process types
  - Delegate to `parseSensorML30(value)` instead of `parsePhysicalSystem(value)`
  - Preserve external link / unknown type fallthrough
- Apply identical transformation to `aggregate-process.ts`
- Update JSDoc on both `parseComponentEntry()` functions to document full type dispatch
- **Run existing test suite** — verify no regressions and no circular import issues at runtime
- If circular import fails: implement fallback (pass `parseSensorML30` as callback parameter)
- **Deliverable:** Both files modified, existing tests passing, circular import verified safe

#### Task 8b: Cross-Type Component Test Cases + Fixtures

**Estimated Time:** ~1–1.5 hours  
**Complexity:** Medium

The real work here is constructing accurate SensorML fixtures with inline components of different process types. Each fixture must have the correct SensorML process structure with `type`, `name`, and enough fields to verify parsing succeeded (not just that it didn't throw).

- Build fixtures: PhysicalSystem containing inline children of each type, AggregateProcess containing inline children of each type
- **Test (physical-system.spec.ts):** 5 new cases:
  1. PhysicalSystem with SimpleProcess child — child is parsed (has `method` field)
  2. PhysicalSystem with PhysicalComponent child — child is parsed (has `position`)
  3. PhysicalSystem with AggregateProcess child — child is parsed (has `components`)
  4. PhysicalSystem with PhysicalSystem child — still works (regression)
  5. External link component — still passed through as-is
- **Test (aggregate-process.spec.ts):** 5 new cases:
  1. AggregateProcess with SimpleProcess child — child is parsed
  2. AggregateProcess with PhysicalSystem child — child is parsed
  3. AggregateProcess with PhysicalComponent child — child is parsed
  4. AggregateProcess with AggregateProcess child — still works (regression)
  5. Unknown type string — passed through (tolerant extraction)
- **Deliverable:** 10 new test cases passing, verifying full cross-type recursive delegation

---

### Task 9: Integration Wiring

**Gap:** Integration of all new parsers into the response pipeline  
**Files Modified:** QueryBuilder methods in `url_builder.ts` (or call site equivalent)  
**Dependencies:** Tasks 1–8 (all parsers must exist)

#### Task 9a: Wire Parsers into QueryBuilder Call Sites

**Estimated Time:** ~0.5–1 hour  
**Complexity:** Medium

- Discover all QueryBuilder methods that return Part 2 resources or Property (read `url_builder.ts` call sites)
- **Recommended approach (Option B from Implementation Guide §8.1):** Parse at the call site, not inside `parseCollectionResponse()`. The QueryBuilder methods (e.g., `getDataStreams()`) call `parseCollectionResponse()` for envelope extraction, then map items through the appropriate parser. This keeps `parseCollectionResponse()` generic.
- Wire resource parsers: `parseProperty`, `parseDatastream`, `parseObservation`, `parseControlStream`, `parseCommand`, `parseCommandStatus` into their respective collection call sites
- Wire schema parsers: `parseDatastreamSchemaResponse`, `parseControlStreamSchemaResponse` into direct call sites (these are single-object endpoints, not collections)
- Add imports for all new parsers at call sites
- **JSDoc:** Document integration pattern at call sites
- **Deliverable:** All parsers wired into the response pipeline, code compiles

#### Task 9b: End-to-End Pipeline Tests

**Estimated Time:** ~0.5–1 hour  
**Complexity:** Medium

- Verify end-to-end: raw JSON → envelope extraction → item parsing → typed output
- **Test:** At minimum, 1 end-to-end test per parser category:
  1. Resource parser pipeline: fixture JSON collection → `parseCollectionResponse()` → `parseDatastream()` → verify typed `Datastream` output with parsed `TimeInterval` fields
  2. Schema parser pipeline: fixture JSON → `parseDatastreamSchemaResponse()` → verify `DatastreamSchemaResponse` output with parsed `SWEComponent` in `resultSchema`
- Additional end-to-end tests for edge cases if time permits (e.g., Property pipeline with spec-derived fixture, Command pipeline verifying `issueTime`/`executionTime` asymmetry)
- **Deliverable:** End-to-end tests passing, confirming full pipeline works from raw JSON to typed output

---

## Deliverables Summary

| Category                      | Files                                                                       | Estimated Lines      |
| ----------------------------- | --------------------------------------------------------------------------- | -------------------- |
| New implementation files      | 3 (`property.ts`, `part2.ts`, `schema-response.ts`)                         | ~300–500             |
| Modified implementation files | 2 (`physical-system.ts`, `aggregate-process.ts`)                            | ~20–40 (net change)  |
| New test files                | 3 (`property.spec.ts`, `part2.spec.ts`, `schema-response.spec.ts`)          | ~400–600             |
| Modified test files           | 2 (`physical-system.spec.ts`, `aggregate-process.spec.ts`)                  | ~80–120 (net change) |
| New interfaces                | 2 (`DatastreamSchemaResponse`, `ControlStreamSchemaResponse` in `model.ts`) | ~20–30               |
| Integration wiring            | QueryBuilder call sites                                                     | ~30–60               |
| **Total**                     | **~10 files touched**                                                       | **~850–1,350 lines** |

**Quality Targets:**

- > 80% code coverage on all new parser files
- All parse functions return declared interface type — no `any` or `unknown` in output
- JSDoc on all public parse functions
- Consistent with existing SensorML, SWE Common, and GeoJSON parser patterns
- All fixtures documented with source (real server response or spec-derived)

---

## Scope Exclusions

The following are explicitly NOT in Phase 5 scope (all complete in Phases 1–4 per the main [ROADMAP](../ROADMAP.md)):

- Type system creation (Phase 1) — all resource interfaces exist
- QueryBuilder / URL building (Phase 2) — all 80 methods exist
- SensorML 3.0 parsers (Phase 3) — complete (except Gap #9 delegation fix)
- SWE Common 3.0 parsers (Phase 3) — complete
- GeoJSON handler extensions (Phase 3) — complete
- Format detection (Phase 3) — complete
- Collection envelope parsing (Phase 3) — `parseCollectionResponse()` complete
- Integration tests (Phase 4) — separate scope
- Performance testing — no upstream precedent
- Real-world server testing — all tests use local fixtures
- Worker extensions — no upstream JSON API uses Web Workers

---

## Server Quirks Cross-Reference

Parser-relevant findings from the [Server Quirks Reference](../../implementation/server-quirks-reference.md) that directly inform implementation:

| Finding | Impact                                                                                                                                |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| F34     | Commands only available under nested `/controlstreams/{id}/commands` on OSH — fixtures come from nested endpoints                     |
| F38     | CommandStatus shape (`command@id`, `reportTime`, `statusCode`, `executionTime` array) directly informs `parseCommandStatus()`         |
| F39     | All Part 2 resources use `items` envelope — confirms `parseCollectionResponse()` handles envelope; parsers only need item-level logic |
| F45     | Envelope varies by server/format — already handled by `parseCollectionResponse()`                                                     |
| F49     | Validates tolerant extraction — never gate on missing fields                                                                          |
| F85     | `validTime` absent/null from servers — validates `parseValidTime()` tolerant design, reused by new parsers                            |

---

## Risk Register

| #   | Risk                                                | Likelihood | Impact | Mitigation                                                                                                   |
| --- | --------------------------------------------------- | ---------- | ------ | ------------------------------------------------------------------------------------------------------------ |
| 1   | No Property test data — both servers return 0 items | Certain    | Medium | Build fixtures from OGC 23-001 spec. Document as known limitation.                                           |
| 2   | Circular import from Gap #9 fix                     | Low        | High   | TypeScript ESM live bindings handle it. Verify with test suite in Task 8a. Fallback: callback parameter.     |
| 3   | `observedProperties` shape variance                 | Medium     | Low    | Handle both object array and string array in `parseDatastream()`. Test both in Task 2b.                      |
| 4   | 52North Part 2 differences                          | Medium     | Medium | Use OSH fixtures as primary. Tolerant extraction handles most variance. Add 52North fixtures when available. |
| 5   | Schema response format variance                     | Medium     | Low    | Handle both `resultSchema` and `recordSchema` wrapper fields. Test both formats in Task 7a.                  |
| 6   | `CommandStatusCodes` enum drift                     | Low        | Low    | `normalizeStatusCode()` returns undefined for unrecognized values.                                           |

---

## Version History

**Version 1.1 (February 19, 2026):**

- Tasks 2, 5, 7, 8, and 9 broken into subtasks for single-pass execution confidence
- 9 tasks → 14 execution units (Tasks 1, 3, 4, 6 unchanged; 5 tasks split into 10 subtasks)
- Added execution unit summary table to Executive Summary
- Added subtask rationale to Task Ordering Rationale section
- Risk register updated with subtask cross-references
- v1.0 archived at [archive/P5-ROADMAP-v1.0.md](archive/P5-ROADMAP-v1.0.md)

**Version 1.0 (February 19, 2026):**

- Initial Phase 5 roadmap covering 9 parser gaps from the Parsing Coverage Audit
- 9 tasks with time estimates and complexity ratings
- Derived from [P5 Contribution Goal](P5-contribution-goal-and-definition.md), [P5 Implementation Guide](P5-parser-completion-implementation-guide.md), and [Task Package](parser-completion-task-package.md)
