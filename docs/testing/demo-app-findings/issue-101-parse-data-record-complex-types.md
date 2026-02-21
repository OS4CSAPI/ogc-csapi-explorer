# Issue #101 Findings Report — `parseDataRecord()` Rejects Complex SWE Component Types as Fields

> **Date:** 2026-02-20
> **Issue:** [OS4CSAPI/ogc-client-CSAPI_2#101](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/101) — "parseDataRecord() rejects complex SWE component types (Vector, DataArray, Matrix, DataChoice, Geometry) as DataRecord fields"
> **Repository under review:** `OS4CSAPI/ogc-client-CSAPI_2` (`src/ogc-api/csapi/formats/swecommon/data-record.ts`, `data-array.ts`, `parser.ts`)
> **Discovered by:** [OS4CSAPI/ogc-csapi-explorer#30](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/30) — encoding display in schema views
> **Labels:** bug, interoperability

---

## Table of Contents

1. [AI Operational Constraints Acknowledgment](#1-ai-operational-constraints-acknowledgment)
2. [Executive Summary](#2-executive-summary)
3. [Issue Description](#3-issue-description)
4. [Source Code Review](#4-source-code-review)
5. [Reference Document Review](#5-reference-document-review)
6. [Risk Assessment](#6-risk-assessment)
7. [Recommendation](#7-recommendation)
8. [Appendix A: Authority Precedence Analysis](#appendix-a-authority-precedence-analysis)
9. [Appendix B: Cross-Reference to Related Issues](#appendix-b-cross-reference-to-related-issues)

---

## 1. AI Operational Constraints Acknowledgment

Per the [AI Operational Constraints](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/governance/AI_OPERATIONAL_CONSTRAINTS.md), this review follows the required authority precedence:

1. **OGC specifications** (OGC SWE Common 3.0 / 24-014) — primary authority
2. **AI Collaboration Agreement** — governing constraints
3. **Issue description** — task scope
4. **Existing code patterns** — implementation precedent
5. **Conversation context** — supplementary guidance

This report does not expand scope beyond what Issue #101 describes. Per §2.1 (do not infer unstated requirements), §2.2 (preserve existing patterns, prefer minimal diffs), and §2.3 (no refactoring for style), this report evaluates the existing implementation against the OGC specification and provides a risk-calibrated recommendation.

---

## 2. Executive Summary

**Issue #101 identifies a genuine specification conformance gap — `parseDataRecord()` and `parseElementType()` throw `SweCommonParseError` for valid SWE Common 3.0 component types (Vector, DataArray, Matrix, DataChoice, Geometry) when encountered as DataRecord fields or DataArray element types.** This is not a design choice or a debatable behavior — the OGC SWE Common 3.0 specification unambiguously defines DataRecord fields as containing **any** `AbstractDataComponent`.

| Finding | Description | Severity | Recommendation |
|---------|-------------|----------|----------------|
| **F-101.1** | `data-record.ts` `parseField()` (L142–146) throws for 5 valid SWE Common component types | **BUG** | **FIX** — Option A callback injection is backward-compatible |
| **F-101.2** | `data-array.ts` `parseElementType()` (L147–149) throws for 4 valid component types | **BUG** | **FIX** — same pattern, same solution |
| **F-101.3** | `parser.ts` `parseField()` (L148–195) already handles all 16 types correctly | CONFIRMED | Already correct — no change needed |
| **F-101.4** | The code comments explicitly say `"Future complex types... are not yet implemented"` — this was a known limitation, not an oversight | ACKNOWLEDGED | The "future" is now; real-world data exposes this gap |
| **F-101.5** | Proposed fix (Option A: callback injection) is fully backward-compatible — adds an optional parameter, no existing call signatures change | LOW RISK | Safe to implement with minimal diff |

**Conclusion:** Unlike Issues #99 (no action) and #100 (deferred), Issue #101 identifies a real spec-conformance gap that affects real-world data. The proposed fix is minimal, backward-compatible, and has been independently validated. Recommend fixing with careful implementation.

---

## 3. Issue Description

Issue #101 reports that `parseDataRecord()` in `data-record.ts` only handles simple scalar components (Quantity, Count, Boolean, Text, Time, Category, and Range variants) and nested DataRecords as field types. Any DataRecord field containing a complex aggregate type — Vector, DataArray, Matrix, DataChoice, or Geometry — throws `SweCommonParseError` with `"unsupported component type"`.

The bug was observed with real-world data from OpenSensorHub where an FCU (Flight Control Unit) control stream schema contains a DataRecord with a `Vector` field for positional data (`locationVectorLLA` with lat/lon/alt coordinates). This is an extremely common pattern in SWE Common 3.0 — Vector fields inside DataRecords represent compound positional, velocity, or acceleration data.

The issue also identifies the same gap in `data-array.ts` `parseElementType()`, which throws for Vector, Matrix, DataChoice, and Geometry as element types.

The root cause is architectural: `data-record.ts` and `data-array.ts` cannot import `parseSWEComponent()` from `parser.ts` because `parser.ts` imports from them (circular dependency). The `parseField()` function inside `parser.ts` does not have this problem — it lives in the same file as `parseSWEComponent()` and correctly delegates all 16 types.

---

## 4. Source Code Review

### 4.1 `data-record.ts` `parseField()` — Throws for Valid Types

`data-record.ts` L127–146 — the `parseField()` function handles only two categories before throwing:

```typescript
// Recursive DataRecord
if (type === 'DataRecord') {
  return { name, component: parseDataRecord(json) } as TypedDataField;
}

// Simple components (Quantity, Count, Boolean, Text, Time, Category, ranges)
if (SIMPLE_COMPONENT_TYPES.has(type)) {
  return { name, component: parseSimpleComponent(json) } as TypedDataField;
}

// Future complex types (DataArray, Vector, Matrix, DataChoice, Geometry)
// are not yet implemented — throw with field context
throw new SweCommonParseError(
  `DataRecord field "${name}" has unsupported component type: "${type}"`,
  `fields[${index}].type`
);
```

**Key observation:** The code comment explicitly acknowledges this is a known limitation (`"Future complex types... are not yet implemented"`). This was an intentional scope boundary during initial development, not an oversight.

### 4.2 `data-array.ts` `parseElementType()` — Same Gap

`data-array.ts` L132–149 — handles DataRecord, DataArray (recursive), and simple components, but throws for Vector, Matrix, DataChoice, Geometry:

```typescript
if (type === 'DataRecord') {
  return { name, component: parseDataRecord(json) };
}
if (type === 'DataArray') {
  return { name, component: parseDataArray(json) };
}
if (SIMPLE_COMPONENT_TYPES.has(type)) {
  return { name, component: parseSimpleComponent(json) };
}
throw new SweCommonParseError(
  `DataArray "elementType" has unsupported component type: "${type}"`,
  'elementType.type'
);
```

### 4.3 `parser.ts` `parseField()` — Already Correct

`parser.ts` L148–195 — the `parseField()` function uses `ALL_COMPONENT_TYPES` (all 16 types) and delegates to `parseSWEComponent()`:

```typescript
if (ALL_COMPONENT_TYPES.has(type)) {
  return { name, component: parseSWEComponent(json) } as TypedDataField;
}
```

This function is used by `parseVector` (coordinates) and `parseDataChoice` (items). It handles every valid SWE Common type by virtue of living in the same file as `parseSWEComponent()`.

### 4.4 Circular Import Architecture

The dependency chain that prevents the simple fix:

```
parser.ts → imports parseDataRecord from data-record.ts
parser.ts → imports parseDataArray from data-array.ts
data-record.ts → CANNOT import parseSWEComponent from parser.ts  ← CIRCULAR
data-array.ts → CANNOT import parseSWEComponent from parser.ts   ← CIRCULAR
```

### 4.5 `parseSWEComponent()` Call Site for DataRecord

`parser.ts` L744 — when `parseSWEComponent()` encounters a DataRecord, it calls `parseDataRecord()` **without any callback**:

```typescript
case 'DataRecord':
  return parseDataRecord(json);
```

This means DataRecords parsed through the main entry point (`parseSWEComponent()`) still use `data-record.ts`'s limited `parseField()`, inheriting the same limitation. The correct `parseField()` in `parser.ts` is orphaned from the DataRecord parsing path.

### 4.6 Test Coverage Analysis

| Test File | Complex types as fields tested? | "Unsupported type" tested? |
|-----------|-------------------------------|---------------------------|
| `data-record.spec.ts` (17 tests) | NO — only DataRecord nesting + simple scalars | YES — but uses `'UnknownType'`, not Vector/DataArray |
| `data-array.spec.ts` (~38 tests) | DataRecord and DataArray only — no Vector/Matrix/DataChoice/Geometry | YES — uses `'UnknownComponent'` |
| `parser.spec.ts` (~48 tests) | NO — DataRecord test uses only Quantity field; Vector test is standalone | N/A |

**Critical gap:** There are zero tests anywhere in the suite that exercise a DataRecord containing a Vector field — the most common real-world pattern that triggers this bug.

---

## 5. Reference Document Review

### OGC SWE Common 3.0 (OGC 24-014)

The specification is unambiguous. DataRecord fields contain **any** `AbstractDataComponent`:

> **DataRecord** — An implementation of ISO 11404 "Record" datatype used to group a fixed number of data components (fields). [...] Each field contains a data component that can be scalar, range, record, array, or choice.

The `AnyComponent` oneOf in the OpenAPI schema (OAS L7606–7616) explicitly includes all 16 component types:

```
AnyComponent: oneOf [
  Quantity, Count, Boolean, Text, Time, Category,          ← simple
  QuantityRange, CountRange, TimeRange, CategoryRange,     ← ranges
  DataRecord, DataArray, Vector, Matrix, DataChoice, Geometry  ← complex
]
```

A DataRecord field containing a Vector is not an edge case — it is the **standard representation** for compound positional data (latitude/longitude/altitude) in SWE Common 3.0.

### AI Operational Constraints

- **§2.1:** "Do not expand scope beyond the issue description." — This report stays within Issue #101's stated scope: the `parseField()` / `parseElementType()` type whitelist limitations.
- **§2.2:** "Prefer minimal diffs." — Option A (callback injection) adds one optional parameter to `parseDataRecord()` and `parseDataArray()`. The diff is minimal and entirely additive. No existing code is removed or restructured.
- **§2.3:** "No refactoring for style." — The proposed change is a **functional fix**, not a refactor. It adds capability to parse valid SWE Common data that currently throws.

### Cross-Server Findings

| Server | Schema with Vector in DataRecord? | `parseSWEComponent()` works? | `parseDataRecord()` works? |
|--------|----------------------------------|------------------------------|----------------------------|
| OpenSensorHub (OSH) | ✅ Yes — FCU control stream has `locationVectorLLA` | ✅ Would work if called directly | ❌ Throws `unsupported component type: "Vector"` |
| 52North CSAPI Demo | N/A — schemas use only simple types | ✅ Yes | ✅ Yes (no complex fields to trigger the bug) |

---

## 6. Risk Assessment

### Risk of Implementing Option A (Callback Injection)

| Risk | Severity | Description |
|------|----------|-------------|
| **Signature change** | **LOW** | `parseDataRecord(json)` → `parseDataRecord(json, componentParser?)`. The parameter is optional with identical behavior when omitted. No existing callers break. |
| **Test updates needed** | **LOW** | Need to add new tests for complex types as fields. Existing tests are unaffected — they don't pass a callback and don't use complex field types. |
| **Diff size** | **LOW** | ~15 lines changed in `data-record.ts`, ~15 lines in `data-array.ts`, 2 lines in `parser.ts`. Total ≈30 lines. |
| **Circular import risk** | **NONE** | The callback pattern explicitly avoids circular imports. `parser.ts` passes `parseSWEComponent` as a function reference; `data-record.ts` and `data-array.ts` never import from `parser.ts`. |
| **Behavioral change** | **LOW** | Only affects the code path through `parseSWEComponent()` → `parseDataRecord()` where the callback is passed. Direct callers of `parseDataRecord(json)` behave identically (throw on complex types, same as today). |
| **Regression risk** | **LOW** | All 17 existing `data-record.spec.ts` tests, 38 `data-array.spec.ts` tests, and 48 `parser.spec.ts` tests should pass unchanged. The existing "unsupported type" tests use `'UnknownType'` which is not in any component type set and will still throw. |

### Risk of NOT Implementing the Fix

| Risk | Severity | Description |
|------|----------|-------------|
| **Spec non-conformance** | **HIGH** | Our parser rejects valid SWE Common 3.0 data. The OGC specification (authority level 1) is unambiguous — DataRecord fields can contain any `AbstractDataComponent`. |
| **Real-world breakage** | **HIGH** | Any server returning DataRecords with Vector fields (extremely common for UAV/sensor payloads) causes parse failures. OSH's FCU schema already triggers this. |
| **Upstream review concern** | **MEDIUM** | An upstream reviewer examining SWE Common compliance could flag this as an incomplete implementation. The code comments explicitly state `"Future complex types... are not yet implemented"` — they may question why. |

### Comparative Risk Summary

| Metric | Implement Fix | Do Nothing |
|--------|--------------|------------|
| Lines changed | ~30 | 0 |
| Existing tests affected | 0 | 0 |
| New tests needed | ~5–8 | 0 |
| Spec conformance | ✅ Improved | ❌ Gap remains |
| Backward compatibility | ✅ Preserved | N/A |
| Validated externally | ✅ Explorer app commit `5ec3df7` | N/A |

---

## 7. Recommendation

### **FIX RECOMMENDED — Option A (Callback Injection)**

Unlike Issues #99 (no action needed — capability already existed) and #100 (deferred — intentional design with workaround), Issue #101 identifies a genuine specification conformance gap that:

1. **Violates OGC SWE Common 3.0** (authority level 1) — DataRecord fields MUST support any `AbstractDataComponent`
2. **Affects real-world data** — OSH's FCU schema (and any server with positional data) triggers the failure
3. **Has a minimal, backward-compatible fix** — one optional parameter, ~30 lines total
4. **Has been independently validated** — the CSAPI Explorer applied the identical fix and all tests pass
5. **Is explicitly marked as known-incomplete** — the code itself says `"Future complex types... are not yet implemented"`

### Implementation Scope

If approved, the fix involves exactly three files:

**1. `data-record.ts`** (~15 lines):
- Add `ComponentParser` type alias
- Add optional `componentParser?` parameter to `parseDataRecord()` and `parseField()`
- In `parseField()`, before the throw: if `componentParser` is provided and the type is recognized, delegate to it

**2. `data-array.ts`** (~15 lines):
- Same callback pattern for `parseElementType()` and `parseDataArray()`

**3. `parser.ts`** (2 lines):
- Change `parseDataRecord(json)` → `parseDataRecord(json, parseSWEComponent)`
- Change `parseDataArray(json)` → `parseDataArray(json, parseSWEComponent)`

**Tests** (~5–8 new test cases):
- DataRecord with Vector field (the triggering real-world case)
- DataRecord with DataArray field
- DataArray with Vector element type
- Verify existing "unsupported type" tests still pass for truly unknown types

### What NOT to Do

- **Do NOT move `parseDataRecord` into `parser.ts`** (Option C) — this would be a large refactor violating §2.3
- **Do NOT add a shared module/registry** (Option B) — adds architectural complexity beyond what's needed
- **Do NOT change any existing test assertions** — all existing tests should pass unchanged
- **Do NOT touch `parser.ts` `parseField()`** — it already works correctly

### Implementation Caution

If this fix is pursued, it should be:
1. Implemented as a standalone commit with a clear message referencing Issue #101
2. Verified against the full test suite (all 1,251 CSAPI tests + 724 format tests + 243 SensorML tests)
3. Verified with `tsc --noEmit` for zero type errors
4. Reviewable as an isolated diff — no other changes bundled

---

## Appendix A: Authority Precedence Analysis

| Authority Level | Source | Ruling |
|-----------------|--------|--------|
| **1. OGC Specification** | SWE Common 3.0 (OGC 24-014) — DataRecord fields contain any `AbstractDataComponent` | **Supports fix** — current code rejects valid data |
| **2. AI Collaboration Agreement** | §2.2 — prefer minimal diffs | **Supports fix** — Option A is ~30 lines, fully additive |
| **3. Issue Description** | #101 — parseDataRecord rejects complex types | Defines scope; fix is within scope |
| **4. Existing Code** | `data-record.ts` L141 comment: `"Future complex types... are not yet implemented"` | Code acknowledges this is incomplete — not a design decision to reject |
| **5. Conversation Context** | User prioritizes protecting contribution integrity | Fix is low-risk; NOT fixing leaves a spec-compliance gap |

**Conclusion:** All five authority levels either support the fix or are neutral. No authority level opposes it. The OGC specification (level 1) directly requires the capability that is currently missing.

---

## Appendix B: Cross-Reference to Related Issues

| Issue | Repository | Relationship | Status |
|-------|------------|-------------|--------|
| [#101](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/101) | ogc-client-CSAPI_2 | **This issue** — `parseDataRecord()` rejects complex component types | Open |
| [#99](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/99) | ogc-client-CSAPI_2 | **Adjacent** — `?f=` parameter support (already exists — NO ACTION) | Closed |
| [#100](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/100) | ogc-client-CSAPI_2 | **Adjacent** — `assertResourceAvailable()` overly strict (DEFERRED) | Open |
| [#30](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/30) | ogc-csapi-explorer | **Discovery source** — encoding display in schema views | — |
| [`5ec3df7`](https://github.com/OS4CSAPI/ogc-csapi-explorer/commit/5ec3df7) | ogc-csapi-explorer | **Validated fix** — Explorer app implemented Option A successfully | Committed |

### Linked Reference Documents

| Document | Location | Relevance |
|----------|----------|-----------|
| AI Operational Constraints | [docs/governance/AI_OPERATIONAL_CONSTRAINTS.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/governance/AI_OPERATIONAL_CONSTRAINTS.md) | §2.1 (no scope expansion), §2.2 (minimal diffs) — both support this fix |
| OGC SWE Common 3.0 | OGC 24-014, DataRecord / AnyComponent | DataRecord fields contain any `AbstractDataComponent` — 16 types |
| `data-record.ts` `parseField()` | `src/ogc-api/csapi/formats/swecommon/data-record.ts` L88–146 | Bug location — throws for Vector, DataArray, Matrix, DataChoice, Geometry |
| `data-array.ts` `parseElementType()` | `src/ogc-api/csapi/formats/swecommon/data-array.ts` L92–149 | Same gap — throws for Vector, Matrix, DataChoice, Geometry |
| `parser.ts` `parseField()` | `src/ogc-api/csapi/formats/swecommon/parser.ts` L148–195 | Correct implementation — delegates all types via `parseSWEComponent()` |
| `parser.ts` `parseSWEComponent()` | `src/ogc-api/csapi/formats/swecommon/parser.ts` L713–768 | Main dispatcher — correctly handles all 16 SWE Common types |
| Issue #99 findings report | `docs/testing/demo-app-findings/issue-99-format-query-parameter.md` | NO ACTION — `?f=` already supported |
| Issue #100 findings report | `docs/testing/demo-app-findings/issue-100-assert-resource-available.md` | DEFERRED — assertion is intentional/documented |
