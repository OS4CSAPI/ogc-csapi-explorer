# Phase 5: Parser Completion — Roadmap

**Version:** 1.0  
**Date:** February 19, 2026  
**Status:** Draft — Pending Review  
**Scope:** 9 parser gaps only (from [Parsing Coverage Audit](../../research/phase-5/parsing-coverage-audit.md))

---

## Executive Summary

This roadmap covers the implementation of **9 parser gaps** identified by the Parsing Coverage Audit, organized into **9 tasks** spanning an estimated **14–22 hours of development time** (2–3 weeks calendar time).

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

### Task 2: `parseDatastream()` + Tests

**Estimated Time:** ~2–3 hours  
**Complexity:** Medium  
**Gap:** #2 from Parsing Coverage Audit  
**File:** `src/ogc-api/csapi/formats/part2.ts` (new)  
**Test File:** `src/ogc-api/csapi/formats/part2.spec.ts` (new)

- Implement `parseDatastream(json: unknown): Datastream`
- Input guard: throw if input is not a non-null object
- Parse 3 time fields via `parseValidTime()`: `validTime`, `phenomenonTime`, `resultTime`
- Extract: `id`, `name`, `description`, `formats`, `outputName`, `observedProperties`, `resultType`, `live`, `type`, `links`
- Normalize `observedProperties`: handle both object array and string array forms
- Cross-references (`system@id`, `system@link`) are NOT extracted — not in the `Datastream` interface
- **Test:** 8 cases — full Datastream (OSH ST#7), minimal Datastream, all 3 time fields parsed, `observedProperties` as objects, `observedProperties` as strings, `phenomenonTime` null pass-through, missing optional fields, non-object input throws
- **Fixtures:** Real OSH response data from Smoke Test #7
- **JSDoc:** Document time field handling, `observedProperties` normalization
- **Dependencies:** None (imports `parseValidTime()` from `geojson.ts`)

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

### Task 5: `parseCommand()` + Tests

**Estimated Time:** ~1.5–2 hours  
**Complexity:** Medium-High  
**Gap:** #5 from Parsing Coverage Audit  
**File:** `src/ogc-api/csapi/formats/part2.ts`  
**Test File:** `src/ogc-api/csapi/formats/part2.spec.ts`

- Implement `parseCommand(json: unknown): Command`
- Input guard: throw if input is not a non-null object
- `issueTime` is an ISO 8601 **instant** (string pass-through) — NOT `parseValidTime()`
- `executionTime` is a time **period** (array of 2 strings) — parse with `parseValidTime()`
- This asymmetry is the key complexity: two time fields, two different types
- Validate `currentStatus` against `CommandStatusCodes` enum; fall back to undefined if unrecognized
- Extract: `id`, `issueTime`, `executionTime`, `sender`, `currentStatus`, `parameters`, `links`
- Introduce `normalizeStatusCode()` shared utility (validates string against `CommandStatusCodes` array)
- Cross-reference (`controlstream@id`) is NOT extracted
- **Test:** 8 cases — full Command (OSH ST#10 F31), minimal Command, `currentStatus` valid, `currentStatus` invalid → undefined, `executionTime` present → TimeInterval, `executionTime` absent, complex nested parameters, non-object input throws
- **Fixtures:** Real OSH response data from Smoke Test #10 (F31)
- **JSDoc:** Document `issueTime`/`executionTime` type asymmetry, status code normalization
- **Dependencies:** Task 2 (shares file)

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
- **Dependencies:** Task 5 (`normalizeStatusCode()` utility)

---

### Task 7: Schema Response Parsers + Tests

**Estimated Time:** ~2–3 hours  
**Complexity:** Medium  
**Gap:** #7 and #8 from Parsing Coverage Audit  
**File:** `src/ogc-api/csapi/formats/schema-response.ts` (new)  
**Test File:** `src/ogc-api/csapi/formats/schema-response.spec.ts` (new)

- Define 2 new interfaces in `model.ts`:
  - `DatastreamSchemaResponse` — `obsFormat`, `resultSchema?` (SWEComponent), `recordSchema?` (SWEComponent), `encoding?` (DataEncoding)
  - `ControlStreamSchemaResponse` — `commandFormat`, `parametersSchema?` (SWEComponent), `encoding?` (DataEncoding)
- Implement `parseDatastreamSchemaResponse(json: unknown): DatastreamSchemaResponse`
  - Extract `obsFormat` (fall back to empty string)
  - Delegate `resultSchema` or `recordSchema` to existing `parseSWEComponent()` if present
  - Delegate `encoding` to `parseEncoding()` if present
  - Handle both JSON format (`resultSchema`) and SWE Common format (`recordSchema` + `encoding`)
- Implement `parseControlStreamSchemaResponse(json: unknown): ControlStreamSchemaResponse`
  - Extract `commandFormat` (fall back to empty string)
  - Delegate `parametersSchema` to existing `parseSWEComponent()` if present
  - Delegate `encoding` to `parseEncoding()` if present
- **Test (Datastream):** 5 cases — JSON format response, SWE Common format response, missing schema fields, nested DataRecord with full SWE parse tree, non-object input throws
- **Test (ControlStream):** 4 cases — JSON format response, missing parametersSchema, nested DataRecord, non-object input throws
- **Fixtures:** Real OSH schema response data from Smoke Test #7; spec-derived for ControlStream schema
- **JSDoc:** Document delegation to SWE Common parser, schema format variants
- **Cross-reference:** Issue #17 (demo app finding F-14) first identified this gap
- **Dependencies:** None (delegates to existing SWE Common parsers)

---

### Task 8: Recursive Delegation Fix + Tests

**Estimated Time:** ~1.5–2 hours  
**Complexity:** Medium-High  
**Gap:** #9 from Parsing Coverage Audit  
**Files Modified:** `src/ogc-api/csapi/formats/sensorml/physical-system.ts`, `src/ogc-api/csapi/formats/sensorml/aggregate-process.ts`  
**Test Files Modified:** existing `physical-system.spec.ts`, `aggregate-process.spec.ts`

- **Current behavior:** `parseComponentEntry()` in `physical-system.ts` only recursively parses inline `PhysicalSystem` children; `parseComponentEntry()` in `aggregate-process.ts` only recursively parses inline `AggregateProcess` children. All other inline process types (SimpleProcess, PhysicalComponent, and cross-type cases) are returned as raw unparsed JSON.
- **Fix:** Replace the type-specific recursive call with delegation to `parseSensorML30()`, which already dispatches all 4 process types. Both files get the same transformation:
  - Before: `if (value.type === 'PhysicalSystem') { parsePhysicalSystem(value) }` + fallthrough
  - After: `if (knownTypes.includes(value.type)) { parseSensorML30(value) }` + fallthrough for external links and unknown types
- **Circular import:** Adding `import { parseSensorML30 } from './parser'` creates a cycle (`parser.ts → physical-system.ts → parser.ts`). TypeScript ESM handles this via live bindings — `parseSensorML30` is resolved at call time, not import time, and is never called during module initialization. Verified safe. Fallback if needed: pass `parseSensorML30` as a callback parameter.
- **Test (physical-system):** 5 cases — PhysicalSystem with SimpleProcess child (parsed), PhysicalSystem with PhysicalComponent child (parsed), PhysicalSystem with AggregateProcess child (parsed), PhysicalSystem with PhysicalSystem child (regression), external link component (passed through)
- **Test (aggregate-process):** 5 cases — AggregateProcess with SimpleProcess child (parsed), AggregateProcess with PhysicalSystem child (parsed), AggregateProcess with PhysicalComponent child (parsed), AggregateProcess with AggregateProcess child (regression), unknown type string (passed through)
- **JSDoc:** Update `parseComponentEntry()` JSDoc in both files to document full type dispatch
- **Dependencies:** None (modifies existing files, no dependency on Tasks 1–7)

---

### Task 9: Integration Wiring

**Estimated Time:** ~1–2 hours  
**Complexity:** Medium  
**Gap:** Integration of all new parsers into the response pipeline  
**Files Modified:** QueryBuilder methods in `url_builder.ts` (or call site equivalent)

- Connect new parsers to the `parseCollectionResponse()` pipeline
- **Recommended approach (Option B from Implementation Guide §8.1):** Parse at the call site, not inside `parseCollectionResponse()`. The QueryBuilder methods (e.g., `getDataStreams()`) call `parseCollectionResponse()` for envelope extraction, then map items through the appropriate parser. This keeps `parseCollectionResponse()` generic.
- Schema endpoints (`/datastreams/{id}/schema`, `/controlstreams/{id}/schema`) return single objects, not collections — call schema response parsers directly, not through `parseCollectionResponse()`
- Verify end-to-end: raw JSON → envelope extraction → item parsing → typed output
- **Test:** End-to-end test for at least 1 resource type (e.g., Datastream) through the full pipeline: fixture JSON → `parseCollectionResponse()` → `parseDatastream()` → verify typed `Datastream` output with parsed `TimeInterval` fields
- **JSDoc:** Document integration pattern at call sites
- **Dependencies:** Tasks 1–8 (all parsers must exist)

---

## Deliverables Summary

| Category | Files | Estimated Lines |
|----------|-------|----------------|
| New implementation files | 3 (`property.ts`, `part2.ts`, `schema-response.ts`) | ~300–500 |
| Modified implementation files | 2 (`physical-system.ts`, `aggregate-process.ts`) | ~20–40 (net change) |
| New test files | 3 (`property.spec.ts`, `part2.spec.ts`, `schema-response.spec.ts`) | ~400–600 |
| Modified test files | 2 (`physical-system.spec.ts`, `aggregate-process.spec.ts`) | ~80–120 (net change) |
| New interfaces | 2 (`DatastreamSchemaResponse`, `ControlStreamSchemaResponse` in `model.ts`) | ~20–30 |
| Integration wiring | QueryBuilder call sites | ~30–60 |
| **Total** | **~10 files touched** | **~850–1,350 lines** |

**Quality Targets:**
- >80% code coverage on all new parser files
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

| Finding | Impact |
|---------|--------|
| F34 | Commands only available under nested `/controlstreams/{id}/commands` on OSH — fixtures come from nested endpoints |
| F38 | CommandStatus shape (`command@id`, `reportTime`, `statusCode`, `executionTime` array) directly informs `parseCommandStatus()` |
| F39 | All Part 2 resources use `items` envelope — confirms `parseCollectionResponse()` handles envelope; parsers only need item-level logic |
| F45 | Envelope varies by server/format — already handled by `parseCollectionResponse()` |
| F49 | Validates tolerant extraction — never gate on missing fields |
| F85 | `validTime` absent/null from servers — validates `parseValidTime()` tolerant design, reused by new parsers |

---

## Risk Register

| # | Risk | Likelihood | Impact | Mitigation |
|---|------|-----------|--------|------------|
| 1 | No Property test data — both servers return 0 items | Certain | Medium | Build fixtures from OGC 23-001 spec. Document as known limitation. |
| 2 | Circular import from Gap #9 fix | Low | High | TypeScript ESM live bindings handle it. Verify with test suite. Fallback: callback parameter. |
| 3 | `observedProperties` shape variance | Medium | Low | Handle both object array and string array in `parseDatastream()`. Test both. |
| 4 | 52North Part 2 differences | Medium | Medium | Use OSH fixtures as primary. Tolerant extraction handles most variance. Add 52North fixtures when available. |
| 5 | Schema response format variance | Medium | Low | Handle both `resultSchema` and `recordSchema` wrapper fields. Test both formats. |
| 6 | `CommandStatusCodes` enum drift | Low | Low | `normalizeStatusCode()` returns undefined for unrecognized values. |

---

## Version History

**Version 1.0 (February 19, 2026):**
- Initial Phase 5 roadmap covering 9 parser gaps from the Parsing Coverage Audit
- 9 tasks with time estimates and complexity ratings
- Derived from [P5 Contribution Goal](P5-contribution-goal-and-definition.md), [P5 Implementation Guide](P5-parser-completion-implementation-guide.md), and [Task Package](parser-completion-task-package.md)
