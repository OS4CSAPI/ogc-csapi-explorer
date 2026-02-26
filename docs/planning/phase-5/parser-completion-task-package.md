# Phase 5: Parser Completion — Task Package

**Version:** 1.0  
**Date:** February 19, 2026  
**Status:** Draft — Pending Review  
**Scope:** Parser gap work only (9 items from Parsing Coverage Audit)

---

## Purpose

This document packages a single task: **create three planning documents for the Phase 5 parser completion work.** It defines what each document must contain, which reference document it mirrors, and what scope constraints apply. No implementation, no code changes, no GitHub issues — just three documents.

---

## Background

The [Parsing Coverage Audit](../../research/phase-5/parsing-coverage-audit.md) identified **9 gaps** in our parser layer:

| #   | Gap                                      | Category                                                                   |
| --- | ---------------------------------------- | -------------------------------------------------------------------------- |
| 1   | `parseProperty()`                        | Missing Part 1 non-GeoJSON resource parser                                 |
| 2   | `parseDatastream()`                      | Missing Part 2 resource parser                                             |
| 3   | `parseObservation()`                     | Missing Part 2 resource parser                                             |
| 4   | `parseControlStream()`                   | Missing Part 2 resource parser                                             |
| 5   | `parseCommand()`                         | Missing Part 2 resource parser                                             |
| 6   | `parseCommandStatus()`                   | Missing Part 2 resource parser                                             |
| 7   | `parseDatastreamSchemaResponse()`        | Missing schema response parser                                             |
| 8   | `parseControlStreamSchemaResponse()`     | Missing schema response parser                                             |
| 9   | SensorML recursive sub-parser delegation | Incomplete — fix in 2 files (`physical-system.ts`, `aggregate-process.ts`) |

**Current behavior:** `parseCollectionResponse<T>()` extracts items from collection envelopes but passes inner objects through as raw untyped JSON. Time fields that should be `TimeInterval` objects remain raw `[start, end]` arrays. Cross-reference fields use abbreviated notation. No field-level transformation or validation occurs for Part 2 resources or Property.

**What is NOT in scope:** QueryBuilder methods, URL building, format detection, GeoJSON handler extensions, SWE Common parsers, SensorML parsers (all complete), collection envelope handling (complete), content negotiation, integration tests, or any other work outside the 9 parser gaps listed above.

---

## Deliverables

Three documents, all placed in `docs/planning/phase-5/`:

### Document 1: Contribution Goal and Definition

**Filename:** `contribution-goal-and-definition.md`  
**Reference:** [`docs/planning/contribution-goal-and-definition.md`](../contribution-goal-and-definition.md) (Version 1.1, 65 lines)

**Structure to follow:**

1. **Header block** — Version, Date
2. **Contribution Goal** — 1-2 paragraphs stating what the parser completion work achieves and why it matters
3. **Contribution Definition** — Scoped breakdown with these subsections:
   - **Resource Parsers** — The 6 missing resource parse functions (Property, Datastream, Observation, ControlStream, Command, CommandStatus), what each does (time field parsing, cross-reference expansion, type-safe output)
   - **Schema Parsers** — The 2 missing schema response parsers (datastream schema, controlstream schema), what they wrap
   - **Recursive Delegation Fix** — The 1 fix in 2 files, what it corrects
   - **Quality Standards** — Test coverage expectations, TypeScript safety, JSDoc, consistency with existing parser patterns (SensorML, SWE Common, GeoJSON)
   - **Deliverables** — Estimated file count, line count, test file count

**Scope constraints:**

- Must reference ONLY the 9 parser gaps — no QueryBuilder, no URL building, no format detection
- Must reference the audit as the source of truth for gap definitions
- Tone and density should match the reference document (concise, factual, no narrative)
- Estimated line count: ~50-80 lines

---

### Document 2: Implementation Guide

**Filename:** `parser-completion-implementation-guide.md`  
**Reference:** [`docs/planning/csapi-implementation-guide.md`](../csapi-implementation-guide.md) (Version 7.0, 4,715 lines)

**Structure to follow:**

1. **Header block** — Version, Date, Table of Contents
2. **Executive Summary** — What this guide covers (parser completion only), relationship to the main implementation guide, what is NOT covered
3. **Architecture Context** — Where the new parsers fit in the existing format handler architecture (`src/ogc-api/csapi/formats/`), relationship to existing parsers (SensorML, SWE Common, GeoJSON), how they integrate with `parseCollectionResponse()`
4. **Resource Parser Implementation** — One section per missing parser:
   - **parseProperty()** — Input shape, output interface (`Property`), field transformations (`validTime` → `TimeInterval`), no GeoJSON wrapping
   - **parseDatastream()** — Input shape, output interface (`Datastream`), time field parsing (`phenomenonTime`, `resultTime`), schema reference handling
   - **parseObservation()** — Input shape, output interface (`Observation`), time fields, `result` field with SWE Common schema-aware handling, cross-references (`foi@id`, `datastream@id`)
   - **parseControlStream()** — Input shape, output interface (`ControlStream`), time fields, control schema reference
   - **parseCommand()** — Input shape, output interface (`Command`), `executionTime` parsing, parameter handling
   - **parseCommandStatus()** — Input shape, output interface (`CommandStatus`), `executionTime`, `statusCode`, `command@id` cross-reference
5. **Schema Response Parsers** — `parseDatastreamSchemaResponse()` and `parseControlStreamSchemaResponse()`, wrapper format, relationship to SWE Common parser
6. **Recursive Delegation Fix** — What `parseComponentEntry()` currently does, what it should do (delegate to `parseSensorML30()`), both affected files, expected behavior change
7. **Integration Points** — How `parseCollectionResponse()` calls the new parsers, how the response pipeline changes
8. **Testing Strategy** — Test patterns for each parser (input fixtures, expected output, edge cases), relationship to existing test files
9. **Smoke Test Cross-References** — Relevant findings from the server quirks reference (F38 command status cross-references, F45 envelope variance, etc.)

**Scope constraints:**

- Must cover ONLY the 9 parser gaps — no QueryBuilder implementation, no new URL patterns
- Should reference existing parser implementations as patterns to follow (e.g., "follow the same structure as `parsePhysicalSystem()`")
- Should reference the existing model interfaces (they already exist — no new interfaces needed except the 2 schema response interfaces)
- Must include real JSON examples where possible (from fixtures or smoke test observations)
- Estimated line count: ~400-800 lines (much shorter than the 4,715-line main guide because scope is narrow)

---

### Document 3: Roadmap

**Filename:** `ROADMAP.md`  
**Reference:** [`docs/planning/ROADMAP.md`](../ROADMAP.md) (Version 3.4, 795 lines)

**Structure to follow:**

1. **Header block** — Version, Date
2. **Executive Summary** — Total estimated hours, number of tasks, what this covers (parser completion only)
3. **Task Ordering Rationale** — Why tasks are ordered the way they are (dependencies, complexity progression)
4. **Tasks** — Each task as a numbered item with:
   - Task name
   - Estimated time (hours)
   - Complexity rating (Low / Medium / Medium-High)
   - What to implement (function signature, file location, field transformations)
   - What to test (specific test cases, fixture references)
   - Dependencies on other tasks (if any)
5. **Deliverables Summary** — Total files, total lines, total test lines

**Suggested task breakdown** (to be refined during drafting):

| #   | Task                                                                             | Estimated Scope                                      |
| --- | -------------------------------------------------------------------------------- | ---------------------------------------------------- |
| 1   | `parseProperty()` + tests                                                        | Simplest — flat SWE Common object, single time field |
| 2   | `parseDatastream()` + tests                                                      | Two time fields, schema reference                    |
| 3   | `parseObservation()` + tests                                                     | Time fields, cross-references, SWE Common result     |
| 4   | `parseControlStream()` + tests                                                   | Time fields, control schema reference                |
| 5   | `parseCommand()` + tests                                                         | `executionTime`, parameter handling                  |
| 6   | `parseCommandStatus()` + tests                                                   | `executionTime`, `statusCode`, `command@id`          |
| 7   | `parseDatastreamSchemaResponse()` + `parseControlStreamSchemaResponse()` + tests | Wrapper parsers, new interfaces                      |
| 8   | SensorML recursive delegation fix + tests                                        | 2-file fix, delegate to `parseSensorML30()`          |
| 9   | Integration wiring — connect parsers to `parseCollectionResponse()` pipeline     | Glue code, end-to-end test                           |

**Scope constraints:**

- Must cover ONLY the 9 parser gaps
- Time estimates should be realistic for the narrow scope (these are parsers, not full resource handlers)
- Should reference the audit's gap descriptions as task definitions
- Should note that model interfaces already exist (no type system work needed, except 2 schema response interfaces)
- Should explicitly state what is NOT included (everything from the main ROADMAP that is already done)
- Estimated line count: ~150-300 lines (much shorter than the 795-line main roadmap)

---

## Source Documents

Comprehensive catalog of every document with potential to inform the three Phase 5 planning deliverables. Organized into tiers by relevance. Not all documents need to be read in full — the tier system indicates priority and depth.

**Guidance:** Tier 1 must be read completely. Tier 2 should be read for the sections noted. Tiers 3–6 are available for reference and should be consulted as needed during drafting, not pre-loaded in bulk (to avoid context overload and AI-related drift/hallucination).

---

### Tier 1: Primary Sources (Must Read — Define the Work + Structural Templates)

These documents directly define the 9 parser gaps or serve as the structural templates the three deliverables must mirror.

| #   | Document                         | Location                                                                                            | Role                                                                                                                  |
| --- | -------------------------------- | --------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| 1   | Parsing Coverage Audit           | [docs/research/phase-5/parsing-coverage-audit.md](../../research/phase-5/parsing-coverage-audit.md) | **Source of truth** for all 9 gaps — gap definitions, interface names, file locations, current behavior, coverage map |
| 2   | Contribution Goal and Definition | [docs/planning/contribution-goal-and-definition.md](../contribution-goal-and-definition.md)         | Structural template for Document 1 (Version 1.1, 65 lines)                                                            |
| 3   | CSAPI Implementation Guide       | [docs/planning/csapi-implementation-guide.md](../csapi-implementation-guide.md)                     | Structural template for Document 2 (Version 7.0, 4,715 lines)                                                         |
| 4   | ROADMAP                          | [docs/planning/ROADMAP.md](../ROADMAP.md)                                                           | Structural template for Document 3 (Version 3.4, 795 lines)                                                           |
| 5   | Server Quirks Reference          | [docs/implementation/server-quirks-reference.md](../../implementation/server-quirks-reference.md)   | All 90 findings (F1–F90) — cross-reference for parser-relevant server behaviors (F34, F38, F39, F45, F49, etc.)       |

---

### Tier 2: Parser Design Context (Should Read — Directly Inform Parser Design)

These documents define details the parsers must handle — data shapes, field semantics, time formats, cross-references, schema wrappers.

#### OGC Standards (define what the parsers must produce)

| #   | Document                                        | Location                                                                                                                                      | Relevance                                                                                                        |
| --- | ----------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| 6   | OGC API - Connected Systems Part 1 (OGC 23-001) | [External: docs.ogc.org](https://docs.ogc.org/is/23-001/23-001.html)                                                                          | Defines Property resource structure (the only Part 1 gap)                                                        |
| 7   | OGC API - Connected Systems Part 2 (OGC 23-002) | [External: docs.ogc.org](https://docs.ogc.org/is/23-002/23-002.html)                                                                          | Defines Datastream, Observation, ControlStream, Command, CommandStatus structures, time fields, schema endpoints |
| 8   | Part 1 OpenAPI Specification                    | [docs/research/standards/ogcapi-connectedsystems-1.bundled.oas31.yaml](../../research/standards/ogcapi-connectedsystems-1.bundled.oas31.yaml) | Machine-readable response schemas for Property                                                                   |
| 9   | Part 2 OpenAPI Specification                    | [docs/research/standards/ogcapi-connectedsystems-2.bundled.oas31.yaml](../../research/standards/ogcapi-connectedsystems-2.bundled.oas31.yaml) | Machine-readable response schemas for all Part 2 resources + schema endpoints                                    |
| 10  | OGC SensorML 3.0 (OGC 23-000r1)                 | [External: docs.ogc.org](https://docs.ogc.org/is/23-000r1/23-000r1.html)                                                                      | Context for recursive delegation fix — process type hierarchy and component embedding                            |
| 11  | OGC SWE Common 3.0 (OGC 23-011r1)               | [External: docs.ogc.org](https://docs.ogc.org/is/23-011r1/23-011r1.html)                                                                      | Schema-aware parsing for Observation `result` and Command parameters                                             |

#### Requirements Research (define what the parsers must satisfy)

| #   | Document                              | Location                                                                                                                              | Relevance                                                                                                |
| --- | ------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------- |
| 12  | CSAPI Part 2 Requirements             | [docs/research/requirements/csapi-part2-requirements.md](../../research/requirements/csapi-part2-requirements.md)                     | Complete requirements for all 5 Part 2 resource types — time fields, schema operations, pagination modes |
| 13  | CSAPI Part 1 Requirements             | [docs/research/requirements/csapi-part1-requirements.md](../../research/requirements/csapi-part1-requirements.md)                     | Property resource requirements (Gap #1) — flat SWE Common object, no GeoJSON wrapping                    |
| 14  | CSAPI Format Requirements             | [docs/research/requirements/csapi-format-requirements.md](../../research/requirements/csapi-format-requirements.md)                   | Comprehensive format parsing requirements for GeoJSON, SensorML, SWE Common                              |
| 15  | CSAPI Data Type & Schema Requirements | [docs/research/requirements/csapi-datatype-schema-requirements.md](../../research/requirements/csapi-datatype-schema-requirements.md) | Type system requirements — 100+ schema definitions including the resource types needing parsers          |
| 16  | Common Format Requirements            | [docs/research/requirements/csapi-format-requirements-3.1.md](../../research/requirements/csapi-format-requirements-3.1.md)           | Content negotiation mechanisms applying to parser output                                                 |

#### Demo App Findings (discovered parser gaps in real usage)

| #   | Document               | Location                                                                                                                                | Relevance                                                                                                   |
| --- | ---------------------- | --------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| 17  | Schema Response Parser | [docs/testing/demo-app-findings/issue-17-schema-response-parser.md](../../testing/demo-app-findings/issue-17-schema-response-parser.md) | **Directly addresses Gaps #7 and #8** — schema response parser utility for datastream/controlstream schemas |

---

### Tier 3: Implementation Pattern References (Consult — Show Patterns to Follow)

These documents describe the existing parsers (SensorML, SWE Common, GeoJSON, response envelope) that the new parsers must be consistent with. Consult when drafting the implementation guide to ensure pattern alignment.

#### Phase 3 Code Reviews (existing parser implementations)

| #   | Document               | Location                                                                                        | Relevance                                                                                                                           |
| --- | ---------------------- | ----------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| 18  | Phase 3.1 Code Review  | [docs/implementation/phase-3.1-code-review.md](../../implementation/phase-3.1-code-review.md)   | GeoJSON handler extensions — pattern for `extractCSAPIFeature()`, Property is the only Part 1 type not using GeoJSON                |
| 19  | Phase 3.5 Code Review  | [docs/implementation/phase-3.5-code-review.md](../../implementation/phase-3.5-code-review.md)   | SimpleProcess sub-parser — pattern for parser function structure, JSDoc, error handling                                             |
| 20  | Phase 3.6 Code Review  | [docs/implementation/phase-3.6-code-review.md](../../implementation/phase-3.6-code-review.md)   | AggregateProcess sub-parser — one of the 2 files needing recursive delegation fix (Gap #9)                                          |
| 21  | Phase 3.7 Code Review  | [docs/implementation/phase-3.7-code-review.md](../../implementation/phase-3.7-code-review.md)   | PhysicalSystem & PhysicalComponent sub-parsers — the other file needing recursive delegation fix (Gap #9)                           |
| 22  | Phase 3.8 Code Review  | [docs/implementation/phase-3.8-code-review.md](../../implementation/phase-3.8-code-review.md)   | SensorML main parser (`parseSensorML30()`) — the function that recursive delegation should call                                     |
| 23  | Phase 3.9 Code Review  | [docs/implementation/phase-3.9-code-review.md](../../implementation/phase-3.9-code-review.md)   | SWE Common simple components parser — pattern for field parsing, constraint handling                                                |
| 24  | Phase 3.10 Code Review | [docs/implementation/phase-3.10-code-review.md](../../implementation/phase-3.10-code-review.md) | DataRecord parser — pattern for structured record parsing                                                                           |
| 25  | Phase 3.11 Code Review | [docs/implementation/phase-3.11-code-review.md](../../implementation/phase-3.11-code-review.md) | DataArray parser — pattern for array/encoding parsing                                                                               |
| 26  | Phase 3.12 Code Review | [docs/implementation/phase-3.12-code-review.md](../../implementation/phase-3.12-code-review.md) | **Response parser, classification, collection envelope** — `parseCollectionResponse()` is the integration point for all new parsers |
| 27  | Phase 3.13 Code Review | [docs/implementation/phase-3.13-code-review.md](../../implementation/phase-3.13-code-review.md) | Nested create methods, Content-Type constants, JSDoc patterns, bug fixes                                                            |
| 28  | Phase 3.14 Code Review | [docs/implementation/phase-3.14-code-review.md](../../implementation/phase-3.14-code-review.md) | Quick-fix batch and cast elimination — code quality patterns                                                                        |
| 29  | Phase 3.15 Code Review | [docs/implementation/phase-3.15-code-review.md](../../implementation/phase-3.15-code-review.md) | DRY extraction patterns (`parseAssociationAttributeGroup`)                                                                          |
| 30  | Phase 3.16 Code Review | [docs/implementation/phase-3.16-code-review.md](../../implementation/phase-3.16-code-review.md) | Self-validation fix — error handling pattern refinement                                                                             |
| 31  | Phase 3.17 Code Review | [docs/implementation/phase-3.17-code-review.md](../../implementation/phase-3.17-code-review.md) | SSN namespace recognition, Deployment validTime optional — tolerance patterns                                                       |

#### Phase 2 Code Reviews (QueryBuilder methods that will call the new parsers)

| #   | Document              | Location                                                                                      | Relevance                                                                                |
| --- | --------------------- | --------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------- |
| 32  | Phase 2.5 Code Review | [docs/implementation/phase-2.5-code-review.md](../../implementation/phase-2.5-code-review.md) | Properties methods — consumer of `parseProperty()` (Gap #1)                              |
| 33  | Phase 2.6 Code Review | [docs/implementation/phase-2.6-code-review.md](../../implementation/phase-2.6-code-review.md) | DataStreams methods — consumer of `parseDatastream()` (Gap #2)                           |
| 34  | Phase 2.7 Code Review | [docs/implementation/phase-2.7-code-review.md](../../implementation/phase-2.7-code-review.md) | Observations methods — consumer of `parseObservation()` (Gap #3)                         |
| 35  | Phase 2.8 Code Review | [docs/implementation/phase-2.8-code-review.md](../../implementation/phase-2.8-code-review.md) | ControlStreams methods — consumer of `parseControlStream()` (Gap #4)                     |
| 36  | Phase 2.9 Code Review | [docs/implementation/phase-2.9-code-review.md](../../implementation/phase-2.9-code-review.md) | Commands methods — consumer of `parseCommand()` and `parseCommandStatus()` (Gaps #5, #6) |

#### Design Decisions

| #   | Document                         | Location                                                                                                                                      | Relevance                                                                                                                               |
| --- | -------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| 37  | Validation-Extraction Decoupling | [docs/implementation/design-notes-validation-extraction-decoupling.md](../../implementation/design-notes-validation-extraction-decoupling.md) | **Critical design decision** — why validators were removed from scope; new parsers must follow tolerant extraction, not hard validation |

---

### Tier 4: Testing & Quality Context (Consult — Inform Testing Strategy)

These documents inform how the new parser tests should be structured, what patterns to follow, and what quality standards apply.

#### Testing Research (directly relevant findings)

| #   | Document                           | Location                                                                                                                                                              | Relevance                                                                                             |
| --- | ---------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| 38  | Spec-Derived Test Requirements     | [docs/research/testing/findings/08-csapi-specification-test-requirements.md](../../research/testing/findings/08-csapi-specification-test-requirements.md)             | Test requirements derived from CSAPI spec — resource types, endpoints, query parameters               |
| 39  | SensorML Testing Requirements      | [docs/research/testing/findings/09-sensorml-testing-requirements.md](../../research/testing/findings/09-sensorml-testing-requirements.md)                             | SensorML parser testing patterns — relevant for recursive delegation fix testing                      |
| 40  | SWE Common Testing Requirements    | [docs/research/testing/findings/10-swe-common-testing-requirements.md](../../research/testing/findings/10-swe-common-testing-requirements.md)                         | SWE Common parser testing patterns — relevant for schema-aware observation result testing             |
| 41  | GeoJSON CSAPI Testing Requirements | [docs/research/testing/findings/11-geojson-csapi-testing-requirements.md](../../research/testing/findings/11-geojson-csapi-testing-requirements.md)                   | GeoJSON property extraction testing — pattern for Property parser testing                             |
| 42  | Schema-Driven Validation Testing   | [docs/research/testing/findings/27-schema-driven-validation-testing.md](../../research/testing/findings/27-schema-driven-validation-testing.md)                       | Observation/command schema validation testing — directly relevant to schema response parsers          |
| 43  | Fixture Sourcing & Organization    | [docs/research/testing/findings/15-fixture-sourcing-organization.md](../../research/testing/findings/15-fixture-sourcing-organization.md)                             | How to source and organize test fixtures for the 6 new resource parsers                               |
| 44  | Part 2 Fixture Best Practices      | [docs/research/testing/findings/15-part-2-fixture-documentation-best-practices.md](../../research/testing/findings/15-part-2-fixture-documentation-best-practices.md) | Fixture metadata system for Part 2 resources                                                          |
| 45  | Error Condition Testing            | [docs/research/testing/findings/18-error-condition-testing-strategy.md](../../research/testing/findings/18-error-condition-testing-strategy.md)                       | Client-side error handling, binary parsing edges — relevant for parser error cases                    |
| 46  | Testing Playbook Synthesis         | [docs/research/testing/findings/38-testing-playbook-synthesis.md](../../research/testing/findings/38-testing-playbook-synthesis.md)                                   | Comprehensive testing playbook — workflows, patterns, progress tracking                               |
| 47  | Command Lifecycle Testing          | [docs/research/testing/findings/31-command-lifecycle-testing.md](../../research/testing/findings/31-command-lifecycle-testing.md)                                     | Command lifecycle states, transition rules — relevant for `parseCommand()` and `parseCommandStatus()` |

#### Testing Reviews & Philosophy

| #   | Document                                | Location                                                                                                                                                        | Relevance                                                                                   |
| --- | --------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------- |
| 48  | Parser Testing vs Spec Validation       | [docs/research/testing/review/notes-parser-testing-vs-spec-validation.md](../../research/testing/review/notes-parser-testing-vs-spec-validation.md)             | **Key philosophy** — parser tests verify client extraction, not server compliance           |
| 49  | Why Models Default to Server Validation | [docs/research/testing/review/notes-why-models-default-to-server-validation.md](../../research/testing/review/notes-why-models-default-to-server-validation.md) | AI anti-pattern awareness — prevents creating server-oriented tests instead of parser tests |
| 50  | Fixtures Guide                          | [docs/testing/fixtures-guide.md](../../testing/fixtures-guide.md)                                                                                               | Guide to test data fixtures following upstream methodology                                  |

#### Test Organization & Quality

| #   | Document                           | Location                                                                                                                                                  | Relevance                                                 |
| --- | ---------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------- |
| 51  | Test Organization & File Structure | [docs/research/testing/findings/19-test-organization-file-structure.md](../../research/testing/findings/19-test-organization-file-structure.md)           | Where to place new parser test files, naming conventions  |
| 52  | Meaningful vs Trivial Tests        | [docs/research/testing/findings/06-meaningful-vs-trivial-definition.md](../../research/testing/findings/06-meaningful-vs-trivial-definition.md)           | Quality criteria for ensuring parser tests are meaningful |
| 53  | Test Quality Checklist             | [docs/research/testing/findings/36-test-quality-checklist-review-process.md](../../research/testing/findings/36-test-quality-checklist-review-process.md) | Quality validation checklist for parser test review       |
| 54  | Coverage Targets & Metrics         | [docs/research/testing/findings/17-coverage-targets-and-metrics.md](../../research/testing/findings/17-coverage-targets-and-metrics.md)                   | Component-specific coverage thresholds                    |
| 55  | Resource Method Testing Patterns   | [docs/research/testing/findings/13-resource-method-testing-patterns.md](../../research/testing/findings/13-resource-method-testing-patterns.md)           | Universal describe block templates and shared utilities   |

---

### Tier 5: Server Behavior & Interoperability (Consult — Real-World Edge Cases)

These documents capture actual server responses, quirks, and interoperability issues that the parsers will encounter.

#### Smoke Test Reports (contain real response examples)

| #   | Document                               | Location                                                                                                                        | Relevance                                                                                        |
| --- | -------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| 56  | ST#7: DataStreams (Phase 2.6)          | [docs/implementation/live-server-smoke-test-post-phase-2.6.md](../../implementation/live-server-smoke-test-post-phase-2.6.md)   | Real DataStream responses from OSH + 52North — input shapes for `parseDatastream()`              |
| 57  | ST#8: Observations (Phase 2.7)         | [docs/implementation/live-server-smoke-test-post-phase-2.7.md](../../implementation/live-server-smoke-test-post-phase-2.7.md)   | Real Observation responses — input shapes for `parseObservation()`                               |
| 58  | ST#9: ControlStreams (Phase 2.8)       | [docs/implementation/live-server-smoke-test-post-phase-2.8.md](../../implementation/live-server-smoke-test-post-phase-2.8.md)   | Real ControlStream responses — input shapes for `parseControlStream()`                           |
| 59  | ST#10: Commands (Phase 2.9)            | [docs/implementation/live-server-smoke-test-post-phase-2.9.md](../../implementation/live-server-smoke-test-post-phase-2.9.md)   | Real Command/CommandStatus responses — input shapes for `parseCommand()`, `parseCommandStatus()` |
| 60  | ST#6: Properties (Phase 2.5)           | [docs/implementation/live-server-smoke-test-post-phase-2.5.md](../../implementation/live-server-smoke-test-post-phase-2.5.md)   | Real Property responses — input shapes for `parseProperty()`                                     |
| 61  | ST#11: 52North Cross-Server            | [docs/implementation/live-server-smoke-test-52north.md](../../implementation/live-server-smoke-test-52north.md)                 | Cross-implementation differences — server variance the parsers must tolerate                     |
| 62  | ST#17: SensorML Parsers (Phase 3.7)    | [docs/implementation/live-server-smoke-test-post-phase-3.7.md](../../implementation/live-server-smoke-test-post-phase-3.7.md)   | SensorML component structures — context for recursive delegation fix                             |
| 63  | ST#18b: Response Envelope (Phase 3.12) | [docs/implementation/live-server-smoke-test-post-phase-3.12.md](../../implementation/live-server-smoke-test-post-phase-3.12.md) | Response envelope parsing — the pipeline the new parsers plug into                               |
| 64  | ST#19: Full CRUD (Phase 4.1)           | [docs/implementation/live-server-smoke-test-post-phase-4.1.md](../../implementation/live-server-smoke-test-post-phase-4.1.md)   | Most recent comprehensive test — current state of all resource interactions                      |

#### Server Analysis

| #   | Document                               | Location                                                                                                                            | Relevance                                                                      |
| --- | -------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------ |
| 65  | Cross-Server Interoperability Analysis | [docs/implementation/cross-server-interoperability-analysis.md](../../implementation/cross-server-interoperability-analysis.md)     | Distinguishes client bugs from server quirks — parser must handle both servers |
| 66  | F71 OSH Accept Header Non-Compliance   | [docs/implementation/note-F71-osh-accept-header-noncompliance.md](../../implementation/note-F71-osh-accept-header-noncompliance.md) | OSH ignores Accept headers — parsers must handle unexpected content types      |
| 67  | F57 Content Negotiation Correction     | [docs/implementation/f57-content-negotiation-correction.md](../../implementation/f57-content-negotiation-correction.md)             | False finding correction — caution against AI-introduced Accept header errors  |
| 68  | OpenSensorHub Server Analysis          | [docs/research/requirements/csapi-opensensorhub-analysis.md](../../research/requirements/csapi-opensensorhub-analysis.md)           | Primary server's format behavior, response shapes, quirks                      |
| 69  | 52North Server Analysis                | [docs/research/requirements/csapi-52north-analysis.md](../../research/requirements/csapi-52north-analysis.md)                       | Secondary server's format behavior, Part 2 limitations                         |
| 70  | Known Server Quirks (Governance)       | [docs/governance/known-server-quirks.md](../../governance/known-server-quirks.md)                                                   | Compact reference of known server behaviors and content-negotiation quirks     |

---

### Tier 6: Upstream & Architecture Context (Consult — Ensure Consistency)

These documents define the upstream patterns that the new parsers must remain consistent with.

| #   | Document                       | Location                                                                                                              | Relevance                                                                              |
| --- | ------------------------------ | --------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| 71  | Architecture Patterns Analysis | [docs/research/upstream/architecture-patterns-analysis.md](../../research/upstream/architecture-patterns-analysis.md) | Consistent patterns for adding new OGC API support — parser file placement, exports    |
| 72  | Error Handling Analysis        | [docs/research/upstream/error-handling-analysis.md](../../research/upstream/error-handling-analysis.md)               | Error handling patterns for parser failures — EndpointError, validation errors         |
| 73  | File Organization Analysis     | [docs/research/upstream/file-organization-analysis.md](../../research/upstream/file-organization-analysis.md)         | Where to place new parser files, test files, fixture files                             |
| 74  | Format Negotiation Analysis    | [docs/research/upstream/format-negotiation-analysis.md](../../research/upstream/format-negotiation-analysis.md)       | Format handling patterns — how parsers integrate with format detection                 |
| 75  | Code Reuse Analysis            | [docs/research/upstream/code-reuse-analysis.md](../../research/upstream/code-reuse-analysis.md)                       | When to reuse shared utilities vs duplicate for isolation                              |
| 76  | TypeScript Types Analysis      | [docs/research/upstream/typescript-types-analysis.md](../../research/upstream/typescript-types-analysis.md)           | Type organization patterns — interface design for schema response types                |
| 77  | PR #114 (EDR) Analysis         | [docs/research/upstream/pr114-analysis.md](../../research/upstream/pr114-analysis.md)                                 | Direct blueprint for upstream integration patterns                                     |
| 78  | Upstream Expectations          | [docs/research/requirements/upstream-expectations.md](../../research/requirements/upstream-expectations.md)           | What upstream expects from new implementations — quality, patterns, format abstraction |

---

### Tier 7: Governance & Process (Consult — Operational Guardrails)

| #   | Document                          | Location                                                                                                          | Relevance                                                                    |
| --- | --------------------------------- | ----------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| 79  | AI Operational Constraints        | [docs/governance/AI_OPERATIONAL_CONSTRAINTS.md](../../governance/AI_OPERATIONAL_CONSTRAINTS.md)                   | Non-negotiable constraints preventing architectural drift and scope creep    |
| 80  | AI Collaboration Agreement        | [docs/governance/AI_Collaboration_Agreement.md](../../governance/AI_Collaboration_Agreement.md)                   | Governing reference for human–AI collaboration rules                         |
| 81  | Phase 2 Lessons Learned           | [docs/governance/phase-2-lessons-learned.md](../../governance/phase-2-lessons-learned.md)                         | Lessons from Phase 1–2.8 — code review patterns, smoke test methodology      |
| 82  | Phase 3 Lessons Learned           | [docs/governance/phase-3-lessons-learned.md](../../governance/phase-3-lessons-learned.md)                         | Lessons from Phase 3 — parser/format handler failure modes, server tolerance |
| 83  | Gap Analysis (Previous Iteration) | [docs/research/requirements/csapi-gap-analysis.md](../../research/requirements/csapi-gap-analysis.md)             | Mistakes from previous attempt — what NOT to do with format parsing          |
| 84  | Lessons Learned Analysis          | [docs/research/requirements/lessons-learned-analysis.md](../../research/requirements/lessons-learned-analysis.md) | Over-engineering warnings, under-engineering gaps, maintenance lessons       |

---

### Tier 8: Additional Demo App Findings (Consult — Related Parser & Integration Gaps)

These demo app findings touch on parser-adjacent behavior that the new parsers may need to consider.

| #   | Document                            | Location                                                                                                                                                                    | Relevance                                                                                            |
| --- | ----------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| 85  | Nested Create Methods               | [docs/testing/demo-app-findings/issue-5-nested-create-methods.md](../../testing/demo-app-findings/issue-5-nested-create-methods.md)                                         | `createDataStream()` URL bugs — context for how parsers interact with create responses               |
| 86  | Content-Type Helper                 | [docs/testing/demo-app-findings/issue-6-content-type-helper.md](../../testing/demo-app-findings/issue-6-content-type-helper.md)                                             | `CSAPI_CONTENT_TYPES` map — content type parsing relevant to parser routing                          |
| 87  | Accept Header Default               | [docs/testing/demo-app-findings/issue-9-accept-header-default.md](../../testing/demo-app-findings/issue-9-accept-header-default.md)                                         | Default `Accept: application/geo+json` for Part 1 — affects what format Property responses arrive in |
| 88  | Empty Body 201 Response             | [docs/testing/demo-app-findings/issue-18-empty-body-201-response.md](../../testing/demo-app-findings/issue-18-empty-body-201-response.md)                                   | Empty-body responses — parser must not crash on missing body                                         |
| 89  | Schema JSDoc Parameter Confusion    | [docs/testing/demo-app-findings/issue-16-schema-jsdoc-parameter-confusion.md](../../testing/demo-app-findings/issue-16-schema-jsdoc-parameter-confusion.md)                 | `obsFormat` / `cmdFormat` naming — schema response parser must handle these parameters correctly     |
| 90  | Type Guard Functions                | [docs/testing/demo-app-findings/issue-13-type-guard-functions-for-union-narrowing.md](../../testing/demo-app-findings/issue-13-type-guard-functions-for-union-narrowing.md) | Type guards for union narrowing — pattern for parser return type discrimination                      |
| 91  | Procedure SensorML JSDoc Cross-Refs | [docs/testing/demo-app-findings/issue-26-procedure-sensorml-jsdoc-crossrefs.md](../../testing/demo-app-findings/issue-26-procedure-sensorml-jsdoc-crossrefs.md)             | Cross-references between Procedure and SensorML — context for recursive delegation fix               |

---

### Tier 9: Pre-Implementation Alignment (Reference — Ensure Document Consistency)

These alignment reports validated that the original planning documents (contribution goal, implementation guide, ROADMAP) were internally consistent. The Phase 5 versions should achieve the same alignment.

| #   | Document                                      | Location                                                                                                                                                                                                                                  | Relevance                                                                                                 |
| --- | --------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| 92  | A1: Test Research vs Implementation Guide     | [docs/research/pre-implementation-alignment/findings/A1-test-research-vs-implementation-guide-report.md](../../research/pre-implementation-alignment/findings/A1-test-research-vs-implementation-guide-report.md)                         | Bidirectional alignment methodology — model for ensuring Phase 5 docs are consistent                      |
| 93  | A2: ROADMAP vs Impl Guide + Test Research     | [docs/research/pre-implementation-alignment/findings/A2-roadmap-vs-implementation-guide-and-test-research-report.md](../../research/pre-implementation-alignment/findings/A2-roadmap-vs-implementation-guide-and-test-research-report.md) | ROADMAP alignment checks — methodology for ensuring Phase 5 ROADMAP aligns with Phase 5 impl guide        |
| 94  | A3: Contribution Goal vs Implementation Guide | [docs/research/pre-implementation-alignment/findings/A3-contribution-goal-vs-implementation-guide-report.md](../../research/pre-implementation-alignment/findings/A3-contribution-goal-vs-implementation-guide-report.md)                 | Contribution goal alignment checks — methodology for ensuring Phase 5 goal aligns with Phase 5 impl guide |

---

### Tier 10: Broader Context (Available — Unlikely Needed But Listed for Completeness)

These documents informed earlier phases. They are available if edge cases arise during drafting but are not expected to be consulted directly.

#### Phase Overviews & Assessments

| #   | Document                     | Location                                                                                                    | Relevance                                            |
| --- | ---------------------------- | ----------------------------------------------------------------------------------------------------------- | ---------------------------------------------------- |
| 95  | Phase 0 Baseline Assessment  | [docs/implementation/phase-0-baseline-assessment.md](../../implementation/phase-0-baseline-assessment.md)   | "Before" snapshot of the forked repo                 |
| 96  | Phase 1 Overview             | [docs/implementation/phase-1-overview.md](../../implementation/phase-1-overview.md)                         | Type system, URL construction foundations            |
| 97  | Phase 2 Overview             | [docs/implementation/phase-2-overview.md](../../implementation/phase-2-overview.md)                         | Full URL-building support for all resource types     |
| 98  | Phase 3 Smoke Test Rationale | [docs/implementation/phase-3-smoke-test-rationale.md](../../implementation/phase-3-smoke-test-rationale.md) | Decision rationale for continuing live smoke testing |

#### Requirements Research (broader scope than parser gaps)

| #   | Document                           | Location                                                                                                                      | Relevance                                                                                  |
| --- | ---------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------ |
| 99  | CRUD Operations Requirements       | [docs/research/requirements/csapi-crud-operations.md](../../research/requirements/csapi-crud-operations.md)                   | CRUD operation matrix — write operations produce responses the parsers must handle         |
| 100 | Query Parameter Requirements       | [docs/research/requirements/csapi-query-parameters.md](../../research/requirements/csapi-query-parameters.md)                 | All query parameters — parsers don't handle queries but may see query-influenced responses |
| 101 | Sub-Resource Navigation            | [docs/research/requirements/csapi-subresource-navigation.md](../../research/requirements/csapi-subresource-navigation.md)     | Nested navigation patterns — context for cross-reference fields in responses               |
| 102 | Conformance & Capabilities         | [docs/research/requirements/csapi-conformance-capabilities.md](../../research/requirements/csapi-conformance-capabilities.md) | Conformance classes — may affect parser availability                                       |
| 103 | Usage Scenarios                    | [docs/research/requirements/csapi-usage-scenarios.md](../../research/requirements/csapi-usage-scenarios.md)                   | Real-world workflows — context for parser output consumption                               |
| 104 | Contribution Definition (Research) | [docs/research/requirements/contribution-definition.md](../../research/requirements/csapi-usage-scenarios.md)                 | Complete implementation scope — confirms parser gaps are in scope                          |

#### Client Analysis (other implementations' approaches)

| #   | Document                   | Location                                                                                                                          | Relevance                                                         |
| --- | -------------------------- | --------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------- |
| 105 | OWSLib Analysis            | [docs/research/requirements/csapi-owslib-analysis.md](../../research/requirements/csapi-owslib-analysis.md)                       | Mature Python client's parser approach for Part 2 resources       |
| 106 | OSHConnect-Python Analysis | [docs/research/requirements/csapi-oshconnect-python-analysis.md](../../research/requirements/csapi-oshconnect-python-analysis.md) | Python client's Pydantic validation approach for resource parsing |
| 107 | oscar-viewer Analysis      | [docs/research/requirements/csapi-oscarviewer-analysis.md](../../research/requirements/csapi-oscarviewer-analysis.md)             | TypeScript client's property-based discovery patterns             |
| 108 | osh-viewer Analysis        | [docs/research/requirements/csapi-oshviewer-analysis.md](../../research/requirements/csapi-oshviewer-analysis.md)                 | Vue.js client's format selection patterns                         |

#### Remaining Smoke Tests (earlier phases, less directly relevant)

| #   | Document                 | Location                                                                                                                        | Relevance                                               |
| --- | ------------------------ | ------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------- |
| 109 | ST#1–5 (Phase 2.1–2.4)   | Various in [docs/implementation/](../../implementation/)                                                                        | Earlier smoke tests — Part 1 resource responses         |
| 110 | ST#12–14 (Phase 3.1–3.3) | Various in [docs/implementation/](../../implementation/)                                                                        | GeoJSON handler, format detector, validator smoke tests |
| 111 | ST#15–16 (Phase 3.4–3.5) | Various in [docs/implementation/](../../implementation/)                                                                        | SensorML type alignment and parser smoke tests          |
| 112 | ST#18 (Phase 3.11)       | [docs/implementation/live-server-smoke-test-post-phase-3.11.md](../../implementation/live-server-smoke-test-post-phase-3.11.md) | SWE Common parsers validation                           |
| 113 | ST#18c (Phase 3.16)      | [docs/implementation/live-server-smoke-test-post-phase-3.16.md](../../implementation/live-server-smoke-test-post-phase-3.16.md) | 1,159 passing tests, 25 suites — pre-Phase 4 state      |

#### Documentation & Inventory

| #   | Document                            | Location                                                                                              | Relevance                                                              |
| --- | ----------------------------------- | ----------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------- |
| 114 | Documentation Inventory             | [docs/research/phase-5/documentation-inventory.md](../../research/phase-5/documentation-inventory.md) | Full catalog of all 306 documents — used to compile this resource list |
| 115 | References (Annotated Bibliography) | [docs/research/references.md](../../research/references.md)                                           | Annotated bibliography of all external and internal references         |
| 116 | Demo App Assessment                 | [docs/webapp-demo/demo-app-assessment.md](../../webapp-demo/demo-app-assessment.md)                   | Assessment of CSAPI demo webapp — real-world consumer of parser output |

---

### Summary

| Tier                                  | Count   | Guidance                          |
| ------------------------------------- | ------- | --------------------------------- |
| 1: Primary Sources                    | 5       | **Must read completely**          |
| 2: Parser Design Context              | 12      | **Should read** relevant sections |
| 3: Implementation Pattern References  | 20      | Consult during drafting           |
| 4: Testing & Quality Context          | 18      | Consult for testing strategy      |
| 5: Server Behavior & Interoperability | 15      | Consult for edge cases            |
| 6: Upstream & Architecture Context    | 8       | Consult for consistency           |
| 7: Governance & Process               | 6       | Consult for guardrails            |
| 8: Demo App Findings                  | 7       | Consult for related gaps          |
| 9: Pre-Implementation Alignment       | 3       | Reference for doc consistency     |
| 10: Broader Context                   | 22      | Available if needed               |
| **Total**                             | **116** | —                                 |

---

## Constraints

1. **Parser gaps only.** All three documents must be scoped exclusively to the 9 items from the Parsing Coverage Audit. No QueryBuilder methods, no URL building, no format detection, no GeoJSON extensions, no SWE Common parser additions, no SensorML parser additions beyond the recursive delegation fix.

2. **Mirror the reference documents.** Each document should match the tone, structure, and density of its reference counterpart — not longer where unnecessary, not shorter where detail is needed.

3. **No implementation.** This task package produces documents, not code. The documents themselves describe future implementation, but creating the documents is the only action.

4. **Audit is the source of truth.** Gap definitions, interface names, file locations, and current behavior descriptions should come from the Parsing Coverage Audit, not be re-derived.

5. **Existing interfaces.** The model interfaces for all 6 resource types already exist in the codebase. The only new interfaces needed are the 2 schema response wrapper types (DatastreamSchemaResponse, ControlStreamSchemaResponse).

---

## Acceptance Criteria

- [ ] Three documents created in `docs/planning/phase-5/`
- [ ] Each document follows the structure outlined above
- [ ] Each document is scoped exclusively to the 9 parser gaps
- [ ] Each document references the Parsing Coverage Audit as its source
- [ ] No code changes, no GitHub issues, no implementation included
- [ ] All three documents committed and pushed to main
