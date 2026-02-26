# Findings Report: Issue #26 — Add JSDoc Cross-References Between Procedure (model.ts) and SensorML Process Types (sensorml/types.ts)

> **Date**: 2026-02-18
> **Source Issue**: [OS4CSAPI/ogc-csapi-explorer#26](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/26) > **Labels on source issue**: `documentation`, `enhancement`

---

## AI Constraints Acknowledgment

> I have reviewed the AI Operational Constraints.
> Issue goal: Assess whether the absence of bidirectional JSDoc cross-references between `Procedure` (model.ts) and the SensorML process types (sensorml/types.ts) constitutes a documentation gap worth addressing in our CSAPI client library contribution.
> Assumptions requiring confirmation: None — the source code, existing JSDoc patterns, and the documentation gap are all directly verified.

---

## Executive Summary

Issue #26 identifies a genuine documentation gap in our CSAPI client library. The `Procedure` interface in model.ts mentions "detailed descriptions use SensorML" but provides no `@link` or `@see` references to `SensorMLProcess`, `SimpleProcess`, `AggregateProcess`, `PhysicalComponent`, `PhysicalSystem`, or the `sensorml/types.ts` module. Conversely, the `sensorml/types.ts` module (916 lines) never mentions the word "Procedure" — there is no indication that these types represent what CSAPI calls "Procedure" resources when requested with `Accept: application/sml+json`.

**This is a library documentation concern.** Both files are in our library repository (`src/ogc-api/csapi/model.ts` and `src/ogc-api/csapi/formats/sensorml/types.ts`). The proposed fix is **JSDoc-only**: adding `@see` and `@link` tags to connect the two representations of the same concept. No runtime code, type definitions, or behavioral logic would change.

**Recommendation: FIX RECOMMENDED** — This is a low-risk, high-value documentation improvement. The changes are purely additive JSDoc comments that follow existing patterns already used extensively in both files. They cannot affect compilation, tests, or runtime behavior.

---

## Issue Description

### What the issue reports

Two files in our library describe the same concept (Procedure/process methodology) from different angles but never cross-reference each other:

| File                            | What it describes                                 | Cross-reference gap                                                      |
| ------------------------------- | ------------------------------------------------- | ------------------------------------------------------------------------ |
| `model.ts` (~L312–L343)         | `Procedure` interface — GeoJSON representation    | Says "detailed descriptions use SensorML" but links to no SensorML types |
| `sensorml/types.ts` (916 lines) | `SensorMLProcess` union — SensorML representation | The word "Procedure" never appears in the file                           |

### The conceptual relationship

The same Procedure resource is returned in different formats depending on the `Accept` header:

- `Accept: application/geo+json` → `Procedure` interface (model.ts)
- `Accept: application/sml+json` → `SensorMLProcess` union — one of `SimpleProcess`, `AggregateProcess`, `PhysicalComponent`, `PhysicalSystem` (sensorml/types.ts)

This relationship is documented in [procedure-sensorml-type-mapping.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/procedure-sensorml-type-mapping.md) but is not reflected in the source code JSDoc.

### What the issue proposes

Three JSDoc-only changes:

1. **model.ts — `Procedure` interface JSDoc**: Add `@link` references to `SimpleProcess`, `AggregateProcess`, `PhysicalComponent`, `PhysicalSystem`, and `SensorMLProcess`, plus a `@see` reference to `sensorml/types.ts`.

2. **sensorml/types.ts — Module-level JSDoc**: Add a "CSAPI Relationship" note explaining that these process types represent what the API calls "Procedure" resources, with a `@link` to `Procedure` in model.ts.

3. **sensorml/types.ts — `SensorMLProcess` union JSDoc**: Add a note that this union is the SensorML representation of a "Procedure" resource, with a `@link` to `Procedure`.

### Affected files

- `src/ogc-api/csapi/model.ts` (~L312–L323) — **in our library**
- `src/ogc-api/csapi/formats/sensorml/types.ts` (~L1–L45, ~L800–L820) — **in our library**

---

## Analysis

### The documentation gap is real and verifiable

Current state of the `Procedure` JSDoc (model.ts L312–L322):

```typescript
/**
 * A Procedure resource in GeoJSON format.
 *
 * Procedures describe methodologies for observation, actuation, or sampling.
 * In GeoJSON encoding, geometry is always null; detailed descriptions use SensorML.
 *
 * Required properties: `featureType`, `uid`, `name` (per OGC spec).
 *
 * @see https://docs.ogc.org/is/23-001/23-001.html#_procedure_resources
 */
```

The phrase "detailed descriptions use SensorML" is a dead end — a developer reading this JSDoc has no way to navigate to the SensorML type definitions. No `@link` to `SensorMLProcess`, no `@see` to `sensorml/types.ts`.

Current state of the `SensorMLProcess` JSDoc (sensorml/types.ts L799–L818):

````typescript
/**
 * Discriminated union of all four concrete SensorML process types.
 *
 * Narrow using the `type` property:
 * ```typescript
 * function handle(proc: SensorMLProcess) {
 *   switch (proc.type) {
 *     case 'SimpleProcess':       // proc: SimpleProcess
 *     case 'AggregateProcess':    // proc: AggregateProcess
 *     case 'PhysicalComponent':   // proc: PhysicalComponent
 *     case 'PhysicalSystem':      // proc: PhysicalSystem
 *   }
 * }
 * ```
 */
````

No mention of "Procedure" anywhere — a developer looking at this type has no indication that it represents the SensorML view of a CSAPI Procedure resource.

### Both files already use `@see` and `@link` extensively

- **model.ts** has 20+ `@see` references to OGC spec sections and uses `{@link}` for cross-referencing types (e.g., `{@link DateTimeParameter}` at line 6).
- **sensorml/types.ts** has 20+ `@see` references to OAS schemas, SensorML clauses, and SWE Common sections, plus multiple `{@link}` references to other types within the module.

The proposed changes follow the established documentation patterns. They are not introducing a new convention.

### Risk assessment: Minimal

| Risk factor         | Assessment                                                              |
| ------------------- | ----------------------------------------------------------------------- |
| Compilation impact  | **None** — JSDoc comments are stripped by the TypeScript compiler       |
| Test impact         | **None** — JSDoc changes cannot affect runtime behavior                 |
| Behavioral impact   | **None** — no type signatures, no runtime code, no exports change       |
| Diff size           | **Small** — approximately 15–20 lines of JSDoc additions across 2 files |
| Pattern consistency | **High** — follows existing `@see`/`@link` conventions in both files    |
| Reversibility       | **Trivial** — comment-only changes are easily reverted                  |

### This is distinct from prior "no action required" findings

Prior findings (Issues #18, #19, #21, #22) were about demo app concerns that did not touch library code. Issue #26 is different:

- The affected files are in our library (`src/ogc-api/csapi/model.ts`, `src/ogc-api/csapi/formats/sensorml/types.ts`)
- The gap is verifiable — the cross-references genuinely do not exist
- The proposed fix is within our contribution scope — our contribution goal includes "JSDoc documentation for all public APIs"
- The fix is purely additive and cannot degrade any existing functionality

### Operational constraints compliance

| Constraint                                                        | Compliance                                                                                           |
| ----------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| §2.1 "Do not expand scope beyond the issue description"           | **Compliant** — changes are limited to the 3 JSDoc blocks identified in the issue                    |
| §2.2 "Prefer minimal diffs over idealized rewrites"               | **Compliant** — adds JSDoc lines to existing comment blocks; no structural changes                   |
| §2.2 "Do not introduce new abstractions, layers, or dependencies" | **Compliant** — no new code, types, or dependencies                                                  |
| §2.3 "Do not refactor for style"                                  | **Compliant** — this is not a style refactor; it adds factual cross-references between related types |

---

## Recommendation

**FIX RECOMMENDED** — Add the proposed JSDoc cross-references.

### Justification

1. **The gap is genuine.** The two files describe the same concept (Procedure) in different formats but provide zero navigational links between them. A developer cannot discover the relationship from the source code alone.

2. **The fix is zero-risk.** JSDoc comments are stripped at compile time. Adding `@see` and `@link` tags cannot break compilation, tests, or runtime behavior. The changes are trivially reversible.

3. **The fix follows existing patterns.** Both files already use `@see` and `@link` extensively. The proposed additions are consistent with the established documentation conventions.

4. **The fix is within our contribution scope.** Our contribution goal claims "JSDoc documentation for all public APIs." The `Procedure` interface and `SensorMLProcess` union are both public APIs. Adding cross-references between them strengthens the accuracy of that claim.

5. **The supporting analysis exists.** The [procedure-sensorml-type-mapping.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/procedure-sensorml-type-mapping.md) document provides thorough research on the Procedure↔SensorML relationship, confirming the content negotiation mapping and the four concrete process types.

### Scope guard

The fix should be limited to exactly what Issue #26 describes:

- Add `@link` and `@see` to the `Procedure` interface JSDoc in model.ts
- Add a "CSAPI Relationship" note to the module-level JSDoc in sensorml/types.ts
- Add a `Procedure` cross-reference to the `SensorMLProcess` union JSDoc in sensorml/types.ts

No other changes should be made. No type signatures, no runtime code, no new exports.

---

## Cross-References

| Document                                                                                                                                                       | Relevance                                                                                                                                            |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| [AI Operational Constraints §2.1, §2.2, §2.3](../../governance/AI_OPERATIONAL_CONSTRAINTS.md)                                                                  | Scope boundaries, minimal diffs, no style refactoring — all satisfied by JSDoc-only changes                                                          |
| [procedure-sensorml-type-mapping.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/procedure-sensorml-type-mapping.md)             | **Primary reference** — documents the Procedure↔SensorML relationship, identifies the JSDoc cross-reference gap, and provides the conceptual mapping |
| [contribution-goal-accuracy-assessment.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/contribution-goal-accuracy-assessment.md) | Verifies "JSDoc documentation for all public APIs" claim; adding cross-references strengthens this claim                                             |
| [upstream-findings.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/upstream-findings.md)                                                     | F-9 mentions `Procedure` in the union return type context; unrelated to JSDoc cross-references                                                       |
| [library-findings-gap-analysis.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/library-findings-gap-analysis.md)                 | Comprehensive gap analysis; does not identify this specific JSDoc gap                                                                                |
| [library-integration-report.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/library-integration-report.md)                       | Finding #10 discusses `Procedure` type properties; unrelated to JSDoc cross-references                                                               |
| [conformance-bypass-architecture-notes.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/conformance-bypass-architecture-notes.md) | Conformance gating architecture; unrelated                                                                                                           |
| [crud-smoke-test-findings.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/crud-smoke-test-findings.md)                           | F-15, F-16 CRUD findings; unrelated                                                                                                                  |
| [e2e-cross-server-report.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/e2e-cross-server-report.md)                             | Cross-server testing; Finding #6 mentions SensorML parse failure but about runtime parsing, not JSDoc                                                |
| [e2e-write-operations-report.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/e2e-write-operations-report.md)                     | Write operation testing; unrelated                                                                                                                   |
| [endpoint-error-isolation-report.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/endpoint-error-isolation-report.md)             | EndpointError module refactor; unrelated                                                                                                             |
| [library-source-changes-audit.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/library-source-changes-audit.md)                   | Confirms only 1 source commit during demo development; unrelated                                                                                     |
| [schema-display-findings.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/schema-display-findings.md)                             | F-13 identifies JSDoc issues in schema methods (different area); unrelated to Procedure/SensorML                                                     |
| [model.ts](../../src/ogc-api/csapi/model.ts)                                                                                                                   | `Procedure` interface at L323 — JSDoc mentions SensorML but has no cross-references to SensorML types                                                |
| [sensorml/types.ts](../../src/ogc-api/csapi/formats/sensorml/types.ts)                                                                                         | `SensorMLProcess` union at L814 — JSDoc never mentions "Procedure"; module JSDoc has no CSAPI relationship note                                      |
