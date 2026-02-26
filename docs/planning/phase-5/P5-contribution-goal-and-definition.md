# Phase 5: Parser Completion — Contribution Goal and Definition

**Version:** 1.0  
**Date:** February 19, 2026

---

## Contribution Goal

Complete the CSAPI parser layer so that every resource returned by a Connected Systems API server is transformed into a typed, field-parsed TypeScript object — not passed through as raw JSON.

The SensorML 3.0, SWE Common 3.0, and Part 1 GeoJSON parsers are fully implemented. The Part 2 resource layer (Datastreams, Observations, Control Streams, Commands, Command Statuses), the Part 1 Property resource, the schema response wrappers, and full recursive SensorML component delegation are not. This work closes those 9 gaps identified by the [Parsing Coverage Audit](../../research/phase-5/parsing-coverage-audit.md), bringing parser coverage from partial to complete across all CSAPI resource types.

---

## Contribution Definition

Implementation of the 9 missing parse functions identified by the Parsing Coverage Audit, consisting of:

**Resource Parsers**

- `parseProperty()` — Transform flat Property JSON (not GeoJSON — Property is a SWE Common object) into typed `Property` object; validate/normalize `uniqueId`, `baseProperty`, `objectType`, `statistic`, and `links` fields. Property has no `validTime` per OGC 23-001 (`DerivedProperty` schema). See [validTime coverage analysis](../../research/phase-5/validtime-coverage-analysis.md) for full rationale.
- `parseDatastream()` — Parse `phenomenonTime`, `resultTime`, and `validTime` into `TimeInterval` objects; validate schema references
- `parseObservation()` — Parse time fields; expand cross-references (`foi@id`, `datastream@id`); handle `result` field with SWE Common schema-aware parsing via existing `validateAgainstSchema()`
- `parseControlStream()` — Parse time fields into `TimeInterval`; validate control schema references
- `parseCommand()` — Parse `executionTime` into `TimeInterval`; handle command parameters
- `parseCommandStatus()` — Parse `executionTime` into `TimeInterval`; normalize `statusCode`; expand `command@id` cross-reference

**Schema Response Parsers**

- `parseDatastreamSchemaResponse()` — Parse `{ obsFormat, resultSchema }` wrapper returned by `/datastreams/{id}/schema`; delegate `resultSchema` to existing SWE Common parser
- `parseControlStreamSchemaResponse()` — Parse `{ commandFormat, commandSchema }` wrapper returned by `/controlstreams/{id}/schema`; delegate `commandSchema` to existing SWE Common parser
- Two new TypeScript interfaces: `DatastreamSchemaResponse` and `ControlStreamSchemaResponse`

**Recursive Delegation Fix (Subsystem Parsing)**

- In SensorML 3.0, subsystems are represented as inline `components` within a PhysicalSystem or AggregateProcess. A PhysicalSystem can contain subsystems of any process type — other PhysicalSystems, PhysicalComponents, SimpleProcesses, or AggregateProcesses. The same applies to AggregateProcess component lists.
- Currently, `parseComponentEntry()` in `physical-system.ts` only recursively parses inline components that are themselves `PhysicalSystem` instances. `parseComponentEntry()` in `aggregate-process.ts` only recurses for `AggregateProcess` instances. All other inline component types (e.g., a SimpleProcess sensor embedded within a PhysicalSystem platform) are returned as raw unparsed JSON.
- This means subsystem hierarchies involving mixed process types — which are common in real-world deployments (a PhysicalSystem weather station containing SimpleProcess temperature sensors and PhysicalComponent wind vanes) — are only partially parsed.
- **Fix:** Update both `parseComponentEntry()` functions to delegate to `parseSensorML30()`, which already dispatches all 4 process types. This makes subsystem parsing complete regardless of the component's process type.
  **Why Subdeployments Are Not in Scope**

Subsystems require this fix because SensorML 3.0 provides an inline embedding mechanism: a PhysicalSystem's `components` field can contain child processes directly within the parent's JSON response body. Only Systems and Procedures have SensorML representations — they are the only CSAPI resource types that can be requested as `application/sml+json`. The recursive delegation fix applies exclusively to this inline embedding path.

Subdeployments have no equivalent parser gap because:

- A Deployment describes _when and where_ a System was deployed, not what a System _is_ — it is temporal/spatial metadata, not a process description
- The CSAPI spec defines only GeoJSON encoding for Deployments; there is no SensorML representation of a Deployment
- GeoJSON Features are flat — there is no mechanism for nesting features inside features
- The Deployment schema has no `components` field or any equivalent inline-children structure
- Subdeployments are accessed exclusively via URL navigation (`/deployments/{id}/subdeployments`), and each one arrives as a standard GeoJSON Feature already fully parsed by `extractCSAPIFeature()`

| Resource        | GeoJSON?       | SensorML? | Inline children possible?                            |
| --------------- | -------------- | --------- | ---------------------------------------------------- |
| System          | Yes            | Yes       | Yes — SensorML `components` embeds subsystems inline |
| Procedure       | Yes            | Yes       | Yes — AggregateProcess has `components`              |
| Deployment      | Yes            | No        | No — GeoJSON only; no inline nesting mechanism       |
| SamplingFeature | Yes            | No        | No                                                   |
| Property        | No (flat JSON) | No        | No                                                   |

In short: subsystems need a parser fix because SensorML uniquely allows inline embedding. Subdeployments don't need one because Deployments only exist as flat GeoJSON Features with no inline child structure.

**Quality Standards**

- Unit tests for each new parse function with fixtures derived from real server responses
- TypeScript type safety — all parse functions return their declared interface type, no `any` or `unknown` in output
- JSDoc documentation for all public parse functions
- Consistent patterns with existing parsers (SensorML, SWE Common, GeoJSON) — same error handling, same field transformation conventions, same tolerant extraction philosophy
- > 80% code coverage on new parser files

**Deliverables**

- 6 resource parse functions + 2 schema response parse functions + 1 delegation fix (2 files)
- 2 new TypeScript interfaces (schema response wrappers)
- Integration wiring into `parseCollectionResponse()` pipeline
- Corresponding test files with fixture-based unit tests
- Estimated ~300-500 lines of implementation, ~400-600 lines of tests
