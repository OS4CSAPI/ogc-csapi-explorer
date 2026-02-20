# Findings Report: Issue #17 — Schema Response Parser Utility (F-14)

> **Date**: 2025-02-17
> **Source Issue**: [OS4CSAPI/ogc-csapi-explorer#17](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/17)
> **Finding ID**: F-14 (from [schema-display-findings.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/main/docs/webapp-demo/schema-display-findings.md))
> **Upstream Finding ID**: F-14 in [schema-display-findings.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/main/docs/webapp-demo/schema-display-findings.md) — Priority #3 (Medium)

---

## AI Constraints Acknowledgment

> I have reviewed the AI Operational Constraints.
> Issue goal: Assess whether the absence of a `parseSchemaResponse()` utility for datastream/controlstream schema endpoint response wrappers requires a fix in our CSAPI client library contribution.
> Assumptions requiring confirmation: None — the issue is well-documented with response examples and real-world demo app evidence.

---

## Executive Summary

Issue #17 proposes adding new `parseDatastreamSchemaResponse()` and `parseControlStreamSchemaResponse()` utility functions to handle the wrapper objects returned by schema endpoints (`/datastreams/{id}/schema` and `/controlstreams/{id}/schema`). These endpoints return `{ obsFormat, resultSchema }` and `{ cmdFormat, commandSchema }` respectively, rather than raw SWE components. The existing `parseSWEComponent()` expects a raw SWE component with a `type` field and throws `SweCommonParseError` when given the wrapper.

**This is not a bug in the existing library code.** The `parseSWEComponent()` function works exactly as designed — it parses SWE Common components. The schema endpoint response wrapper is a separate concern at the HTTP response level, not the SWE component level. The gap is a **missing convenience feature**, and the consumer workaround is a single line of code: `data?.resultSchema ?? data`.

**Recommendation: DEFER** — This is an enhancement that introduces new types, new functions, new exports, and new tests. It does not fix broken functionality. The existing `parseSWEComponent()` is correct and fully functional. The one-line consumer workaround is trivial. Per AI Operational Constraints §2.2, new abstractions should not be introduced without approval, and the conservation record of our fork (exactly one library source commit) should be maintained. This enhancement is better proposed upstream after the core contribution is reviewed and accepted.

---

## Issue Description

### What the issue reports

Schema endpoints defined in OGC 23-002 Part 2 do not return raw SWE Common components. They return a wrapper object containing metadata alongside the SWE component:

**Datastream schema** (`GET /datastreams/{id}/schema`):
```json
{
  "obsFormat": "application/om+json",
  "resultSchema": {
    "type": "DataRecord",
    "name": "gps_data",
    "fields": [ ... ]
  }
}
```

**Control stream schema** (`GET /controlstreams/{id}/schema`):
```json
{
  "cmdFormat": "application/swe+json",
  "commandSchema": {
    "type": "DataRecord",
    "fields": [ ... ]
  }
}
```

The library's `parseSWEComponent()` function expects objects with a `type` property at the top level. When the full wrapper is passed directly, it throws `SweCommonParseError` because the wrapper object `{ obsFormat, resultSchema }` has no `type` field.

### What the issue proposes

1. Add `DatastreamSchemaResponse` and `ControlStreamSchemaResponse` type interfaces to `types.ts`
2. Add `parseDatastreamSchemaResponse()` and `parseControlStreamSchemaResponse()` functions to `parser.ts`
3. Export all new types and functions from `index.ts` and `src/index.ts`
4. Add unit tests for the new functions

### Real-world demo impact

In the CSAPI Explorer demo app's `SweSchemaDisplay.vue`, we added manual extraction:

```typescript
const sweJson = data?.resultSchema ?? data;
try {
  parsed.value = parseSWEComponent(sweJson);
} catch (e) {
  error.value = `Schema fetched but parsing failed: ${e.message}`;
}
```

This one-line workaround (`data?.resultSchema ?? data`) resolves the issue completely. No library modification was needed.

---

## Source Code Review

### Existing parser: `parseSWEComponent()` (`parser.ts` L697–730)

```typescript
export function parseSWEComponent(json: unknown): AnyComponent {
  if (!isRecord(json)) {
    throw new SweCommonParseError(
      'SWE Component input must be a non-null object'
    );
  }

  if (typeof json.type !== 'string') {
    throw new SweCommonParseError(
      'SWE Component must have a string "type" property. ' +
        `Valid types: ${[...ALL_COMPONENT_TYPES].join(', ')}`,
      'type'
    );
  }

  switch (json.type) {
    case 'Quantity':
    case 'Count':
    // ... all 16 component types handled
  }
}
```

**Assessment**: This function works exactly as designed. It parses SWE Common components, which are defined by OGC SWE Common 3.0 (OGC 24-014) as objects with a discriminating `type` property. The schema endpoint response wrapper is not an SWE Common component — it is an OGC Connected Systems API (OGC 23-002) endpoint response envelope. These are two different specifications and two different abstraction levels.

### Existing response pattern: `parseCollectionResponse()` (`response.ts` L87–131)

```typescript
export function parseCollectionResponse<T>(body: unknown): CollectionResponse<T> {
  if (typeof body !== 'object' || body === null) {
    throw new Error('Invalid collection response: expected an object');
  }
  const obj = body as Record<string, unknown>;
  let items: T[];
  if (Array.isArray(obj.features)) {
    items = obj.features as T[];
  } else if (Array.isArray(obj.items)) {
    items = obj.items as T[];
  } else {
    throw new Error('Invalid collection response: missing both "features" and "items" arrays');
  }
  // ... extract links, pagination metadata
}
```

The issue cites this as the pattern to follow. However, there is a key difference:

| Factor | `parseCollectionResponse()` | Proposed `parseSchemaResponse()` |
|---|---|---|
| **Complexity** | Non-trivial — normalizes two envelope formats (FeatureCollection vs items), extracts links, pagination metadata, timestamps | Trivial — extracts one field (`resultSchema` or `commandSchema`) from a flat wrapper |
| **Consumer alternatives** | Consumers would need to duplicate the dual-format detection and metadata extraction logic | Consumers need exactly one line: `data.resultSchema ?? data` |
| **Abstraction benefit** | High — encapsulates a genuinely complex normalization | Low — wraps a trivial property access |
| **Used by the library internally** | Yes — called throughout the library's CSAPI module | No — only useful for external consumers making raw `fetch` calls |

### Current barrel exports: `swecommon/index.ts`

The barrel file currently exports 40+ types and 15+ functions from the SWE Common module. Adding `DatastreamSchemaResponse`, `ControlStreamSchemaResponse`, `parseDatastreamSchemaResponse`, and `parseControlStreamSchemaResponse` would expand the module's API surface with types and functions that operate at a different abstraction level (HTTP endpoint response wrappers vs SWE Common data components).

### Type system: `AnyComponent` (`types.ts` L717–727)

```typescript
export type AnyComponent =
  | AnySimpleComponent
  | DataRecord
  | Vector
  | DataArray
  | Matrix
  | DataChoice
  | SweGeometry;
```

The proposed `DatastreamSchemaResponse` and `ControlStreamSchemaResponse` interfaces would reference `AnyComponent` for their nested schema fields. This creates a dependency within `types.ts` that mixes OGC 23-002 endpoint-level types with OGC 24-014 SWE Common component types. These are concerns from different specifications and should logically be separated.

---

## Reference Document Review

### 1. AI Operational Constraints (`AI_OPERATIONAL_CONSTRAINTS.md`)

- **§2.1 Assumptions and Scope**: "Do not infer unstated requirements" and "Do not expand scope beyond the issue description" — The source issue (#17) describes new functionality to add, not existing functionality that is broken.
- **§2.2 Architectural Alignment**: "Do not introduce new abstractions, layers, or dependencies without approval" — The proposed implementation introduces 2 new types, 2 new functions, and modifies 3–4 barrel export files. These are new abstractions.
- **§2.2**: "Prefer minimal diffs over idealized rewrites" — The proposed changes touch 5+ files for a problem that consumers solve in 1 line.
- **§2.3 Refactoring Prohibitions**: "Avoid changes that increase diff noise" — Adding new types, functions, and exports for a trivial extraction increases the diff for our upstream contribution without fixing existing functionality.

### 2. Schema Display Findings (`schema-display-findings.md`)

F-14 is classified as:
- **Severity**: Medium
- **Type**: Enhancement (not bug)
- **Priority**: #3 (Medium) in the actionability summary

The document confirms: "Consumers must know to extract `.resultSchema` before calling `parseSWEComponent()`." It does not characterize this as broken behavior — it characterizes it as a missing convenience.

### 3. Upstream Findings (`upstream-findings.md`)

F-14 is not listed as a standalone finding in the original upstream-findings.md (which covers F-1 through F-12). It was discovered later during schema display work and is documented only in schema-display-findings.md. This places it outside the original finding set and in the "discovered during demo app feature development" category rather than the "discovered during library integration" category.

### 4. Library Source Changes Audit (`library-source-changes-audit.md`)

Confirms the conservation record:
- **Exactly one commit** (`e73cff8`) has modified library source during the entire demo development lifecycle
- That commit was a zero-behavioral-impact structural refactor (EndpointError isolation)
- Every other workaround was implemented in the demo app layer without touching `src/`
- The audit concludes: "The library source in this fork remains suitable for clean upstream contribution via cherry-pick or PR"

Adding `parseSchemaResponse()` utilities would be the **second library source modification** and would introduce **new functionality** (not a refactor or bug fix), breaking the "exactly one commit, zero behavioral impact" conservation record.

### 5. Library Findings Gap Analysis (`library-findings-gap-analysis.md`)

F-14 is not included in this document (it predates the schema display work). The document's actionability summary covers F-1 through F-12 and F-83 through F-85. The absence of F-14 from this foundational analysis document further positions it as a later-discovered enhancement rather than a core finding.

### 6. Contribution Goal Accuracy Assessment (`contribution-goal-accuracy-assessment.md`)

The assessment confirms the library is a URL builder with parser support:
- "The library is a URL builder, not an HTTP client — it does not perform fetch operations, manage authentication, or handle response deserialization end-to-end"
- Response parsing exists for SWE Common components (data-level parsing) and collection response normalization (complex multi-format envelope handling)
- Schema endpoint response wrapper parsing is neither of these — it is a trivial property extraction from a two-field object

---

## Risk Assessment

### Risk of implementing the enhancement

| Risk Factor | Assessment | Rating |
|---|---|---|
| Introduces new abstractions | **Yes** — 2 new type interfaces + 2 new functions | **Moderate** |
| Modifies barrel exports | **Yes** — `swecommon/index.ts` and potentially `src/index.ts` | **Low-Moderate** |
| Breaks conservation record | **Yes** — would be the 2nd library source commit and the 1st to add new functionality | **Moderate** |
| Requires new tests | **Yes** — happy path, error cases, edge cases as described in Issue #17 | **Low** |
| Diff size for upstream PR | ~100+ new lines across 4–5 files for a convenience wrapper | **Moderate** |
| Mixes abstraction levels | **Yes** — OGC 23-002 endpoint types in SWE Common (OGC 24-014) module | **Low-Moderate** |
| Runtime correctness risk | Low — the proposed implementation is straightforward | **Low** |

### Risk of NOT implementing the enhancement

| Risk Factor | Assessment | Rating |
|---|---|---|
| Consumer inconvenience | **Minimal** — one-line workaround: `data.resultSchema ?? data` | **Low** |
| Missing type safety | **Minimal** — consumers still get full `AnyComponent` type safety after extraction | **Low** |
| Documentation gap | **Real but addressable** — a JSDoc note on `getDataStreamSchema()` could document the wrapper structure | **Low** |
| Demo app impact | **None** — workaround is already in place and working | **None** |

### Overall risk assessment

The risk of implementing the enhancement (adding new abstractions, breaking conservation record, expanding diff surface for upstream PR) **exceeds** the risk of deferring it (trivial one-line consumer workaround, no functional impact). The enhancement provides convenience but does not fix broken functionality.

---

## Analysis

### Is there a bug in the existing library code?

**No.** `parseSWEComponent()` is designed to parse SWE Common components (OGC 24-014). It correctly requires a `type` field to discriminate the component union. Schema endpoint response wrappers (OGC 23-002) are not SWE Common components — they are HTTP endpoint response envelopes that happen to contain an SWE Common component nested inside. The parser is working exactly as intended at the correct abstraction level.

### Is the consumer workaround burdensome?

**No.** The workaround is a single line of code:

```typescript
const sweJson = data.resultSchema ?? data;
const parsed = parseSWEComponent(sweJson);
```

For control streams:
```typescript
const sweJson = data.commandSchema ?? data;
const parsed = parseSWEComponent(sweJson);
```

This is comparable in effort to many standard HTTP API patterns where consumers extract a nested field from a response envelope (e.g., `response.data`, `response.result`, `response.body`). It is not unusual and does not represent a significant library gap.

### Does the existing `parseCollectionResponse()` precedent justify this?

**No.** `parseCollectionResponse()` performs non-trivial normalization: it detects whether the response uses `features` (GeoJSON FeatureCollection) or `items` (Part 2 ItemCollection), extracts pagination metadata (`numberMatched`, `numberReturned`), extracts links, and handles timestamps. The dual-format detection alone justifies a library utility because consumers would need to duplicate complex conditional logic.

The proposed `parseDatastreamSchemaResponse()` extracts one field from a flat two-field object. The complexity difference is an order of magnitude.

### Does this enhancement belong in the SWE Common module?

**Arguably not.** The SWE Common module (`src/ogc-api/csapi/formats/swecommon/`) implements OGC SWE Common 3.0 (OGC 24-014) — a standalone standard for sensor data encoding. The schema endpoint response wrapper is defined by OGC Connected Systems API (OGC 23-002) — a different standard. Placing `DatastreamSchemaResponse` and endpoint-level parsing functions in the SWE Common module mixes concerns from two different OGC specifications.

If implemented, a more architecturally appropriate location might be alongside `parseCollectionResponse()` in `response.ts`, which already handles OGC 23-002 endpoint-level response envelopes. But this further argues that the proposed placement in `swecommon/` is not ideal.

### Should we preserve the conservation record?

**Yes.** The library source changes audit documents that exactly one commit (`e73cff8`) has modified library source during the entire demo development lifecycle. That commit was a pure structural refactor with zero behavioral impact (EndpointError isolation). This record is a significant integrity marker for our upstream contribution:

- It demonstrates discipline — we identified 17+ findings but modified source code only when absolutely necessary
- It demonstrates the workaround-first philosophy — all accommodations were demo-layer workarounds except the one unavoidable build-breaking refactor
- It simplifies the upstream review — maintainers can evaluate our contribution knowing we touched source code exactly once, for a well-justified architectural reason

Adding convenience utility functions breaks this record for a marginal DX improvement that consumers solve in one line.

### What about the GitHub issue #67 already created in ogc-client-CSAPI_2?

Issue [#67](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/67) was created prematurely before this analysis was performed. The findings report and its DEFER recommendation take precedence — the issue documents the enhancement proposal but the report evaluates whether it should be acted on now.

---

## Recommendation

**DEFER — Do not implement `parseSchemaResponse()` utilities in our library fork at this time**

### Rationale

1. **No existing functionality is broken.** `parseSWEComponent()` works correctly at its design scope (SWE Common components). The gap is at the HTTP endpoint response level, which is a different abstraction.

2. **The consumer workaround is trivial.** One line of code (`data.resultSchema ?? data`) resolves the issue completely. This is standard practice for HTTP response envelope extraction.

3. **The enhancement introduces new abstractions.** Per AI Operational Constraints §2.2: "Do not introduce new abstractions, layers, or dependencies without approval." Two new types, two new functions, and modified barrel exports qualify as new abstractions.

4. **The conservation record should be preserved.** Our fork's integrity marker — exactly one library source commit with zero behavioral impact — is a significant asset for upstream review. Adding convenience utilities degrades this.

5. **The enhancement is better proposed upstream.** After the core CSAPI contribution is reviewed and accepted by camp-to-camp maintainers, a follow-up PR can propose `parseSchemaResponse()` utilities with upstream input on placement (SWE Common module vs response module), naming conventions, and scope. Upstream maintainers may prefer a different approach (e.g., a more general response normalization strategy).

6. **The proposed module placement mixes specifications.** OGC 23-002 endpoint-level types do not belong in the OGC 24-014 SWE Common parsing module. The architectural concern would need to be resolved before implementation.

### What to do instead

| Action | Description | When |
|---|---|---|
| **Document the wrapper structure** | A JSDoc note on `getDataStreamSchema()` and `getControlStreamSchema()` could mention that the response contains `{ obsFormat, resultSchema }` / `{ cmdFormat, commandSchema }` and that consumers should extract the nested schema before passing to `parseSWEComponent()`. | Could be included with the Issue #16 JSDoc fix (F-13) if desired |
| **Propose upstream** | After the core contribution is accepted, file an upstream issue proposing `parseSchemaResponse()` utilities with architectural guidance from maintainers. | Post-acceptance |
| **Track in Issue #67** | The existing GitHub issue [#67](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/67) documents the enhancement proposal and can be referenced in upstream discussions. | Already exists |

### Priority assessment

| Factor | Assessment |
|---|---|
| **Finding ID** | F-14 |
| **Priority in schema-display-findings.md** | #3 (Medium) |
| **Type** | Enhancement — new functionality, not a bug fix |
| **Effort** | Low-Medium — ~100+ new lines across 4–5 files plus tests |
| **Impact** | Low — one-line consumer workaround exists |
| **Risk of implementing** | Moderate — breaks conservation record, introduces new abstractions, mixes specification modules |
| **Risk of deferring** | Low — trivial workaround, no functional impact |

---

## Appendix A: OGC Specification References

### OGC 23-002 §Req 11 — Datastream Schema Response

The datastream schema endpoint (`/datastreams/{id}/schema`) returns a response containing:
- `obsFormat` — the observation format the schema describes
- `resultSchema` — the SWE Common component describing the observation result structure

The wrapper is defined by the Connected Systems API (OGC 23-002), not by SWE Common (OGC 24-014).

- Spec URL: https://docs.ogc.org/is/23-002/23-002.html#req_datastream_schema

### OGC 23-002 §Req 25 — Control Stream Schema Response

The control stream schema endpoint (`/controlstreams/{id}/schema`) returns a response containing:
- `cmdFormat` — the command format the schema describes
- `commandSchema` — the SWE Common component describing the command parameter structure

- Spec URL: https://docs.ogc.org/is/23-002/23-002.html#req_controlstream_schema

### OGC 24-014 — SWE Common 3.0

SWE Common defines data components (DataRecord, Vector, Quantity, etc.) discriminated by a `type` property. `parseSWEComponent()` implements parsing for these components. The schema endpoint response wrapper is not defined by this standard.

- Spec URL: https://docs.ogc.org/is/24-014/24-014.html

---

## Appendix B: Reference Documents Consulted

| # | Document | Key Relevance |
|---|---|---|
| 1 | [AI_OPERATIONAL_CONSTRAINTS.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/governance/AI_OPERATIONAL_CONSTRAINTS.md) | Behavioral rules — no new abstractions without approval, minimal diffs, no scope expansion |
| 2 | [schema-display-findings.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/schema-display-findings.md) | Detailed F-14 breakdown — severity Medium, type Enhancement |
| 3 | [upstream-findings.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/upstream-findings.md) | Consolidated findings (F-1 through F-12); F-14 not in original set |
| 4 | [library-source-changes-audit.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/library-source-changes-audit.md) | Conservation record — exactly 1 commit modifying source, zero behavioral impact |
| 5 | [library-findings-gap-analysis.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/library-findings-gap-analysis.md) | Actionability analysis for F-1 through F-12 and F-83 through F-85; F-14 not included |
| 6 | [contribution-goal-accuracy-assessment.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/contribution-goal-accuracy-assessment.md) | Library scope — URL builder with parser support, not full HTTP response handler |
| 7 | [OGC 23-002 §Req 11](https://docs.ogc.org/is/23-002/23-002.html#req_datastream_schema) | Normative: datastream schema response structure |
| 8 | [OGC 23-002 §Req 25](https://docs.ogc.org/is/23-002/23-002.html#req_controlstream_schema) | Normative: control stream schema response structure |
| 9 | [OGC 24-014](https://docs.ogc.org/is/24-014/24-014.html) | Normative: SWE Common 3.0 — defines the component types that `parseSWEComponent()` handles |

---

## Appendix C: Relationship to Other Findings Reports

| Report | Finding | Relationship |
|---|---|---|
| [issue-16-schema-jsdoc-parameter-confusion.md](./issue-16-schema-jsdoc-parameter-confusion.md) | F-13 (JSDoc) | Sister finding — F-13 and F-14 were both discovered during schema display implementation. F-13 is a JSDoc bug (FIX); F-14 is a missing convenience feature (DEFER). The optional JSDoc note documenting the wrapper structure could be included with the F-13 fix. |
| [issue-15-parse-location-header.md](./issue-15-parse-location-header.md) | F-12 (Location header) | Same pattern — F-12 proposed a `parseLocationHeader()` utility for trivial string extraction (splitting a URL by `/`). That report also recommended DEFER because the consumer workaround is trivial and adding a utility would expand scope. |
| [issue-6-content-type-helper.md](./issue-6-content-type-helper.md) | F-10 (Content-Type) | Related concept — both involve response-level metadata that the library does not currently handle automatically. |
| [issue-5-nested-create-methods.md](./issue-5-nested-create-methods.md) | F-1/F-2 (URL bugs) | Contrast — F-1/F-2 are genuine URL generation bugs producing incorrect URLs. F-14 is a missing convenience feature where the existing functionality works correctly. |
