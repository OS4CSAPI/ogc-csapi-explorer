# Findings Report: Issue #16 — Schema Method JSDoc `f` vs `obsFormat`/`cmdFormat` Parameter Confusion (F-13)

> **Date**: 2025-02-17
> **Source Issue**: [OS4CSAPI/ogc-csapi-explorer#16](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/16) > **Finding ID**: F-13 (from [schema-display-findings.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/main/docs/webapp-demo/schema-display-findings.md))
> **Upstream Finding ID**: F-13 in [upstream-findings.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/main/docs/upstream-findings.md) — Priority #2 (High)

---

## AI Constraints Acknowledgment

> I have reviewed the AI Operational Constraints.
> Issue goal: Assess whether the JSDoc conflation of `f` with `obsFormat`/`cmdFormat` in `getDataStreamSchema()` and `getControlStreamSchema()` requires a fix in our CSAPI client library contribution.
> Assumptions requiring confirmation: None — the issue is well-documented with spec references and real-world server evidence.

---

## Executive Summary

Issue #16 reports that the JSDoc for `getDataStreamSchema()` and `getControlStreamSchema()` in our CSAPI contribution **misleads consumers** by conflating two distinct OGC query parameters: the generic `f` (response format, from OGC API — Common) and the schema-specific `obsFormat` / `cmdFormat` (from OGC 23-002 Part 2, Req 11 and Req 25). The JSDoc says `obsFormat` is "required" but the `@param` description and example code tell consumers to use `f`. When the demo app followed the JSDoc, the OSH SensorHub returned **400 Bad Request**.

**This is a genuine documentation bug in code we wrote.** The URL building functionality itself works correctly — `buildQueryString()` serializes all option keys generically, and any consumer passing `{ obsFormat: 'application/swe+json' }` at runtime would get the correct URL. However, the JSDoc actively steers consumers toward the wrong parameter, and the corresponding test names are factually misleading.

**Recommendation: FIX** — JSDoc correction and test name correction only. Zero runtime behavioral change. Extremely low risk.

---

## Issue Description

### What the issue reports

The `getDataStreamSchema()` JSDoc at `url_builder.ts` L1303–1321 states:

> The `obsFormat` query parameter is **required** per Part 2, Req 11.
> Omitting it causes the server to return 400 Bad Request.

But the `@param` description and code example then tell the consumer to use `{ f: 'application/swe+json' }`, which appends `?f=application%2Fswe%2Bjson` to the URL. These are **two different query parameters**:

| Parameter   | Purpose                                                   | OGC Spec           |
| ----------- | --------------------------------------------------------- | ------------------ |
| `f`         | Generic response format negotiation (JSON vs XML vs HTML) | OGC API — Common   |
| `obsFormat` | Specifies which observation encoding the schema describes | OGC 23-002 §Req 11 |
| `cmdFormat` | Specifies which command encoding the schema describes     | OGC 23-002 §Req 25 |

The same issue affects `getControlStreamSchema()` at `url_builder.ts` L1732–1757, where the JSDoc mentions `cmdFormat` (Part 2, Req 25) but the example uses `f`.

### Real-world impact

When the CSAPI Explorer demo app followed the JSDoc and passed `{ f: 'application/swe+json' }`, the OSH SensorHub returned:

```
400 Bad Request: { "status": 400, "message": "Unsupported format: application/swe+json" }
```

The server interpreted `f=application/swe+json` as a response format and rejected it. Removing the parameter entirely resolved the issue — the server defaults to SWE JSON schema format.

### Test name mismatch

The test at `url_builder.spec.ts` L1656–1658 is named `"returns correct URL with obsFormat parameter"` but actually tests `f`:

```typescript
it('returns correct URL with obsFormat parameter', () => {
  const url = makeDsBuilder().getDataStreamSchema('ds-001', {
    f: 'application/swe+json',
  });
  expect(url).toBe(
    'https://example.com/collections/iot/datastreams/ds-001/schema?f=application%2Fswe%2Bjson'
  );
});
```

The same mismatch exists at `url_builder.spec.ts` L2135–2137 for `getControlStreamSchema`.

---

## Source Code Review

### Affected method: `getDataStreamSchema()` (`url_builder.ts` L1303–1325)

````typescript
/**
 * Returns the URL for retrieving a datastream's result schema.
 *
 * The `obsFormat` query parameter is **required** per Part 2, Req 11.
 * Omitting it causes the server to return 400 Bad Request.
 *
 * @param id - The datastream resource identifier.
 * @param options - Optional query parameters. Should include `f` set to the
 *   desired observation format (e.g., `application/swe+json`).
 * @returns URL string for the datastream schema endpoint.
 * @throws {EndpointError} If 'datastreams' is not available on this collection.
 *
 * @example
 * ```ts
 * const url = builder.getDataStreamSchema('ds-001', { f: 'application/swe+json' });
 * // => "https://example.com/collections/iot/datastreams/ds-001/schema?f=application%2Fswe%2Bjson"
 * ```
 *
 * @see https://docs.ogc.org/is/23-002/23-002.html#req_datastream_schema
 */
getDataStreamSchema(id: string, options?: QueryOptions): string {
  this.assertResourceAvailable('datastreams');
  return this.buildResourceUrl('datastreams', id, 'schema', options);
}
````

**Problems identified:**

1. Line 1305: Says `obsFormat` is "required" — but real servers work fine without it (they default)
2. Line 1305: Claims omitting it causes 400 — this is the opposite of reality (including `f` caused 400)
3. Line 1310: Says to use `f` for "desired observation format" — `f` is response format, not observation format
4. Line 1317: Example uses `{ f: 'application/swe+json' }` — this produces the wrong parameter name in the URL

### Affected method: `getControlStreamSchema()` (`url_builder.ts` L1732–1757)

Same pattern — JSDoc mentions `cmdFormat` (correct concept) but guides consumers to use `f` (wrong parameter name).

### URL building path: `buildResourceUrl()` → `buildQueryString()`

The `buildResourceUrl()` method (L199–214) constructs the base URL and appends the query string via `buildQueryString()` (L234–262). The `buildQueryString()` method serializes **all** entries from the options object generically:

```typescript
for (const [key, value] of Object.entries(options)) {
  // ... handles bbox, temporal, limit, arrays, then falls through to:
  params.append(key, String(value));
}
```

**This means the URL builder would correctly handle `obsFormat` / `cmdFormat` at runtime** if a consumer passed them. The serialization is key-agnostic — any option key becomes a query parameter. The issue is purely in the JSDoc guidance, not in the builder's behavior.

### Type system constraint: `QueryOptions` (`model.ts` L119–140)

The `QueryOptions` interface defines `f?: MimeType` but does NOT include `obsFormat` or `cmdFormat` as named properties and has no index signature:

```typescript
export interface QueryOptions {
  limit?: number;
  offset?: number;
  cursor?: string;
  bbox?: BoundingBox;
  datetime?: DateTimeParameter;
  q?: string;
  id?: string | string[];
  uid?: string | string[];
  f?: MimeType;
  crs?: CrsCode;
}
```

This means TypeScript's excess property checking would **reject** `{ obsFormat: 'application/swe+json' }` at compile time unless the consumer uses a type assertion. This is a secondary concern — the issue (Issue #16) proposes an Option B that adds typed interfaces, but that is an enhancement beyond the core JSDoc bug.

---

## Reference Document Review

### 1. AI Operational Constraints (`AI_OPERATIONAL_CONSTRAINTS.md`)

- **§2.2 Architectural Alignment**: "Preserve upstream structure, naming, and patterns" — JSDoc correction preserves all structure; no renaming of methods, files, or types.
- **§2.2**: "Prefer minimal diffs over idealized rewrites" — JSDoc-only fix is the minimal diff approach.
- **§2.3 Refactoring Prohibitions**: "Do not refactor for style, clarity, or 'best practice' unless explicitly requested" — This is not a style refactor; it's correcting factually incorrect documentation that causes real 400 errors.
- **§3 Standards Discipline**: "Treat cited specifications as authoritative" — The OGC 23-002 §Req 11 and §Req 25 clearly distinguish `obsFormat`/`cmdFormat` from `f`.

### 2. Upstream Findings (`upstream-findings.md`)

F-13 is listed in the consolidated upstream findings at **Priority #2 (High)** under "Should Address":

- Classified as "Bug / Documentation"
- Identified through real-world demo app testing
- Part of the broader body of 13 findings (F-1 through F-12 + F-13/F-14)

### 3. Schema Display Findings (`schema-display-findings.md`)

Provides the detailed breakdown of F-13:

- Documents the exact JSDoc text, the real-world 400 error, and the root cause
- Notes the test name mismatch
- Identifies that `buildQueryString()` serializes all option keys generically — confirming that the URL builder itself is not broken, only the documentation is wrong

### 4. Library Source Changes Audit (`library-source-changes-audit.md`)

Confirms:

- **Exactly one commit** (`e73cff8`) has modified library source during the entire demo development lifecycle
- The schema JSDoc fix described in the demo app's workaround table: "Schema URL `f=` param removal" was implemented in `demo/src/csapi-bridge.ts` — **not** in the library source
- The library source remains suitable for clean upstream contribution

### 5. Contribution Goal Accuracy Assessment (`contribution-goal-accuracy-assessment.md`)

Notes under "Format Support":

- "Content negotiation guidance exists via constants and the `f` query parameter, but HTTP-level Accept header management is outside the library's scope as a URL builder"
- The `f` query parameter is explicitly identified as OGC API Common response format, **not** schema format — reinforcing that the current JSDoc guidance is incorrect

---

## Risk Assessment

### Risk of making the fix

| Risk Factor               | Assessment                                                                      | Rating       |
| ------------------------- | ------------------------------------------------------------------------------- | ------------ |
| Runtime behavioral change | **None** — JSDoc and test name changes have zero runtime impact                 | **Minimal**  |
| API surface change        | **None** — method signatures, return types, and parameter types are unchanged   | **Minimal**  |
| Test behavior change      | **None** — only test names change; assertions and expected URLs are unchanged   | **Minimal**  |
| Upstream compatibility    | **Improved** — corrected JSDoc provides accurate guidance to upstream consumers | **Positive** |
| Diff size                 | **Very small** — ~20 lines of JSDoc text + 2 test name strings                  | **Minimal**  |
| Regression potential      | **None** — no executable code is modified                                       | **Minimal**  |

### Risk of NOT making the fix

| Risk Factor                 | Assessment                                                                               | Rating     |
| --------------------------- | ---------------------------------------------------------------------------------------- | ---------- |
| Consumers hit 400 errors    | **Real** — any consumer following JSDoc guidance will get 400 from real servers          | **Medium** |
| Misleading test names       | **Real** — tests named "obsFormat" but test `f`, creating false confidence               | **Low**    |
| Upstream reviewer confusion | **Real** — reviewers reading JSDoc will see contradictory guidance                       | **Medium** |
| Spec compliance perception  | **Real** — JSDoc incorrectly claims parameter is "required" when servers work without it | **Low**    |

### Overall risk assessment

The fix is **pure documentation correction** with **zero executable code changes**. The risk of making the fix is negligible. The risk of NOT making the fix is that our contribution ships with JSDoc that actively causes 400 errors for consumers who follow it.

---

## Analysis

### Is there actually a bug in our library source code?

**No — the URL building logic is correct.** The `getDataStreamSchema()` method constructs the correct URL (`/datastreams/{id}/schema`) and appends query parameters from whatever the consumer provides. If a consumer passes `{ obsFormat: 'application/swe+json' }`, the URL builder will correctly produce `?obsFormat=application%2Fswe%2Bjson`. The `buildQueryString()` method is deliberately key-agnostic and handles this correctly.

### Is there a bug in our JSDoc?

**Yes.** The JSDoc contains three factual errors:

1. **"The `obsFormat` query parameter is required per Part 2, Req 11. Omitting it causes the server to return 400 Bad Request."** — False. Real servers (OSH SensorHub) return valid schema responses when `obsFormat` is omitted. What DOES cause a 400 is passing `f=application/swe+json`, which is what the JSDoc example tells you to do.

2. **"Should include `f` set to the desired observation format"** — Conflation. `f` is the OGC API Common response format parameter. `obsFormat` is the schema-specific parameter per Part 2 Req 11.

3. **The code example uses `{ f: 'application/swe+json' }`** — This produces `?f=application%2Fswe%2Bjson`, which servers reject. The correct parameter name would be `obsFormat`.

### Are the test names misleading?

**Yes.** The test at `url_builder.spec.ts` L1656 is named `"returns correct URL with obsFormat parameter"` but it passes `{ f: 'application/swe+json' }` and expects `?f=application%2Fswe%2Bjson`. The test name says "obsFormat" but the test code uses `f`. The same applies to the control stream test at L2135.

### Is this within our CSAPI contribution scope?

**Yes.** The `getDataStreamSchema()`, `getControlStreamSchema()`, and all associated JSDoc were written as part of Phase 2.8 of our CSAPI contribution. These methods, their JSDoc, and their tests are entirely our work.

### Should we fix the TypeScript types too (Option B from the issue)?

**Not in this fix.** Option B (adding `DatastreamSchemaOptions` and `ControlStreamSchemaOptions` interfaces) is an enhancement that adds new types to `model.ts` and changes method signatures. While the enhancement has merit, it:

- Introduces new types (violates minimal-diff principle per §2.2)
- Changes method parameter types (non-trivial API surface modification)
- Goes beyond correcting the documented error

Option B should be tracked as a separate enhancement if desired. The JSDoc correction alone fully resolves the consumer-facing confusion.

---

## Recommendation

**FIX — JSDoc correction and test name correction only (Option A from Issue #16)**

### What to fix

| File                                    | Lines      | Change                                                                                                                               | Risk                   |
| --------------------------------------- | ---------- | ------------------------------------------------------------------------------------------------------------------------------------ | ---------------------- |
| `src/ogc-api/csapi/url_builder.ts`      | L1303–1321 | Fix `getDataStreamSchema()` JSDoc: remove false "required" claim, correct parameter guidance from `f` to `obsFormat`, update example | Zero runtime impact    |
| `src/ogc-api/csapi/url_builder.ts`      | L1732–1757 | Fix `getControlStreamSchema()` JSDoc: same pattern as above, correct from `f` to `cmdFormat`                                         | Zero runtime impact    |
| `src/ogc-api/csapi/url_builder.spec.ts` | L1656      | Fix test name to accurately reflect what is being tested                                                                             | Zero behavioral impact |
| `src/ogc-api/csapi/url_builder.spec.ts` | L2135      | Fix test name to accurately reflect what is being tested                                                                             | Zero behavioral impact |

### What NOT to fix in this task

- **Do not** add `DatastreamSchemaOptions` / `ControlStreamSchemaOptions` types (Option B) — this is an enhancement, not a bug fix
- **Do not** change the `QueryOptions` interface — existing consumers may depend on the current type
- **Do not** change method signatures — `getDataStreamSchema(id: string, options?: QueryOptions)` remains unchanged
- **Do not** change test assertions or expected URLs — only the test names are misleading

### Priority assessment

| Factor                               | Assessment                                                               |
| ------------------------------------ | ------------------------------------------------------------------------ |
| **Finding ID**                       | F-13                                                                     |
| **Priority in upstream-findings.md** | #2 (High) — under "Should Address"                                       |
| **Effort**                           | Low — ~20 lines of JSDoc text + 2 test name strings                      |
| **Impact**                           | Medium-High — prevents consumer 400 errors from following JSDoc guidance |
| **Risk**                             | Negligible — zero executable code changes                                |
| **Scope**                            | Within our CSAPI contribution scope — we wrote this JSDoc                |

---

## Appendix A: OGC Specification References

### OGC 23-002 §Req 11 — Datastream Schema

The schema endpoint for datastreams (`/datastreams/{id}/schema`) accepts an `obsFormat` query parameter specifying which observation encoding the schema should describe. This is distinct from the OGC API Common `f` parameter.

- Spec URL: https://docs.ogc.org/is/23-002/23-002.html#req_datastream_schema

### OGC 23-002 §Req 25 — Control Stream Schema

The schema endpoint for control streams (`/controlStreams/{id}/schema`) accepts a `cmdFormat` query parameter specifying which command encoding the schema should describe.

- Spec URL: https://docs.ogc.org/is/23-002/23-002.html#req_controlstream_schema

### OGC API — Common: `f` Parameter

The `f` query parameter is the standard OGC API response format negotiation parameter (e.g., `?f=json`, `?f=html`, `?f=xml`). It controls the response **serialization format**, not the schema **content**.

---

## Appendix B: Reference Documents Consulted

| #   | Document                                                                                                                                                       | Key Relevance                                                               |
| --- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------- |
| 1   | [AI_OPERATIONAL_CONSTRAINTS.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/governance/AI_OPERATIONAL_CONSTRAINTS.md)                        | Behavioral rules — minimal diffs, no unauthorized refactoring               |
| 2   | [upstream-findings.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/upstream-findings.md)                                                     | F-13 priority ranking (#2, High)                                            |
| 3   | [schema-display-findings.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/schema-display-findings.md)                             | Detailed F-13 breakdown with server evidence                                |
| 4   | [library-source-changes-audit.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/library-source-changes-audit.md)                   | Confirms 1 commit modifying library source; schema workaround was demo-only |
| 5   | [contribution-goal-accuracy-assessment.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/contribution-goal-accuracy-assessment.md) | Distinguishes `f` as response format vs schema format                       |
| 6   | [OGC 23-002 §Req 11](https://docs.ogc.org/is/23-002/23-002.html#req_datastream_schema)                                                                         | Normative: `obsFormat` parameter specification                              |
| 7   | [OGC 23-002 §Req 25](https://docs.ogc.org/is/23-002/23-002.html#req_controlstream_schema)                                                                      | Normative: `cmdFormat` parameter specification                              |

---

## Appendix C: Relationship to Other Findings Reports

| Report                                                                 | Finding             | Relationship                                                                                                                                  |
| ---------------------------------------------------------------------- | ------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| [issue-8-jsdoc-documentation.md](./issue-8-jsdoc-documentation.md)     | F-8 (JSDoc)         | Same category — JSDoc accuracy. Issue #8 addressed JSDoc completeness; Issue #16 addresses JSDoc correctness for schema methods specifically. |
| [issue-6-content-type-helper.md](./issue-6-content-type-helper.md)     | F-10 (Content-Type) | Related concept — Content-Type vs Accept vs `f` vs `obsFormat` are all distinct but related HTTP/OGC parameter concerns.                      |
| [issue-9-accept-header-default.md](./issue-9-accept-header-default.md) | F-4 (Accept header) | Related concept — another case where the correct parameter/header matters for cross-server compatibility.                                     |
