# Issue #103 Findings Report — Parsed Part 2 Models Discard Cross-Reference Fields

> **Date:** 2026-02-20
> **Issue:** [OS4CSAPI/ogc-client-CSAPI_2#103](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/103) — "Parsed Part 2 models discard all cross-reference fields — parent resource navigation impossible without raw JSON"
> **Repository under review:** `OS4CSAPI/ogc-client-CSAPI_2` (`src/ogc-api/csapi/formats/part2.ts`, `src/ogc-api/csapi/model.ts`)
> **Discovered by:** [OS4CSAPI/ogc-csapi-explorer commit ecce874](https://github.com/OS4CSAPI/ogc-csapi-explorer/commit/ecce874) (parent navigation breadcrumbs), [OS4CSAPI/ogc-csapi-explorer#32](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/32) (command status history)
> **Labels:** enhancement, model

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

1. **OGC specifications** (OGC 23-002 Part 2) — primary authority
2. **AI Collaboration Agreement** — governing constraints
3. **Issue description** — task scope
4. **Existing code patterns** — implementation precedent
5. **Conversation context** — supplementary guidance

This report does not expand scope beyond what Issue #103 describes. Per §2.1 (do not infer unstated requirements), §2.2 (preserve existing patterns, prefer minimal diffs), and §2.3 (no refactoring for style), this report evaluates the existing implementation against the OGC specification and provides a risk-calibrated recommendation.

---

## 2. Executive Summary

**Issue #103 identifies a genuine specification conformance gap — the five Part 2 parsers intentionally discard cross-reference fields (`system@id`, `datastream@id`, `controlstream@id`, `command@id`, etc.) that the OGC specification defines as Required associations in the resource model tables. Unlike Issues #100/#102 (which proposed behavioral changes to existing guards), this issue proposes a purely additive change — optional fields on existing interfaces — with zero impact on existing consumers or tests.**

| Finding | Description | Severity | Recommendation |
|---------|-------------|----------|----------------|
| **F-103.1** | All 5 Part 2 parsers explicitly discard cross-reference fields that encode Required parent–child associations per OGC 23-002 Tables 5, 7, 10, 12, 15 | **SPEC GAP** | **FIX** — add optional cross-reference fields to interfaces |
| **F-103.2** | The stripping is intentional and documented — each parser's JSDoc says "intentionally ignored," and 10+ test assertions verify `not.toHaveProperty` | DESIGN CHOICE | Was a deliberate scope boundary during initial development |
| **F-103.3** | The proposed fix is **purely additive** — all new interface fields are optional (`?`), no existing method signatures change, no existing behavior changes | **LOW RISK** | Backward-compatible by definition |
| **F-103.4** | Parser changes are minimal (~3–5 lines per function) using the same tolerant extraction pattern already in use | **MINIMAL DIFF** | Follows §2.2 — smallest possible change |
| **F-103.5** | Cross-reference fields are the **canonical** way the JSON encoding communicates parent associations — the `links` array is not a reliable alternative (not all servers populate it with parent refs) | CONFIRMED | Spec examples in §16.1.3–§16.1.9 consistently use `@id`/`@link` fields |

**Conclusion:** This is a genuine spec-conformance gap where Required associations (per the OGC resource model tables) are being discarded during parsing. The fix is minimal, purely additive, and backward-compatible — the narrowest change with the highest spec-conformance return. Recommend fixing with careful implementation.

---

## 3. Issue Description

Issue #103 reports that the five Part 2 parser functions strip all cross-reference fields from the parsed output. These fields encode the fundamental parent–child hierarchy of Connected Systems resources:

```
observation → datastream → system
command → controlStream → system
commandStatus → command → controlStream → system
```

After parsing, a typed `Observation` has no way to determine which `Datastream` it belongs to, even though the server explicitly provided `datastream@id` in the JSON response. Consumers must retain the raw JSON alongside parsed models to navigate the resource hierarchy.

### Fields Being Discarded

| Parser | Discarded Fields | Spec Table |
|--------|-----------------|------------|
| `parseDatastream()` | `system@id`, `system@link`, `samplingFeature@link`, `featureOfInterest@link` | Table 5 — `system` Required |
| `parseControlStream()` | `system@id`, `system@link` | Table 10 — `system` Required |
| `parseObservation()` | `datastream@id`, `samplingFeature@id`, `foi@id` | Table 7 — `datastream` Required |
| `parseCommand()` | `controlstream@id` | Table 12 — `controlstream` Required |
| `parseCommandStatus()` | `command@id` | Table 15 — `command` Required |

### Real-World Discovery

The gap was discovered in the ogc-csapi-explorer demo app when implementing parent navigation breadcrumbs and command status history. The demo had to extract cross-reference fields from raw JSON because the parsed models don't carry them:

```ts
// Must read from raw JSON, not parsed model
if (typeof raw['system@id'] === 'string') {
  links.push({ resourceType: 'systems', resourceId: raw['system@id'] })
}
```

---

## 4. Source Code Review

### 4.1 Parser JSDoc Documents Intentional Stripping

Each parser explicitly documents that cross-reference fields are omitted. For example, `parseDatastream()` (`part2.ts` ~L86):

```typescript
/**
 * Cross-reference fields (`system@id`, `system@link`) present in the raw JSON
 * are intentionally ignored — they are not part of the `Datastream` interface.
 */
```

The same pattern appears in `parseControlStream()` (~L181), `parseObservation()` (~L374), `parseCommand()` (~L298), and `parseCommandStatus()` (~L446). This was a deliberate scope boundary during initial development — the parsers were focused on extracting the resource's own properties, deferring cross-reference support.

### 4.2 Model Interfaces Lack Cross-Reference Fields

The five Part 2 interfaces in `model.ts` do not define any cross-reference fields:

- `Datastream` (L434–465): 14 fields — no `systemId` or `systemLink`
- `Observation` (L473–496): 6 fields — no `datastreamId` or `samplingFeatureId`
- `ControlStream` (L498–532): 13 fields — no `systemId` or `systemLink`
- `Command` (L534–557): 7 fields — no `controlStreamId`
- `CommandStatus` (L559–590): 7 fields — no `commandId`

### 4.3 Parser Extraction Uses `satisfies` — Additive Fields Are Safe

All five parsers return objects using `satisfies Type`:

```typescript
return {
  id: typeof obj.id === 'string' ? obj.id : '',
  // ... field extraction ...
} satisfies Datastream;
```

The `satisfies` keyword ensures the returned object conforms to the interface but does **not** strip extra properties at runtime — it's a compile-time check only. However, because each parser builds the return object with explicit field listings (no spread of the raw input), only the listed fields appear in the output. Adding new optional fields to the interface and new extraction lines to the return object is the correct approach.

### 4.4 Tests Explicitly Verify Stripping

The test suite (`part2.spec.ts`) has explicit assertions verifying cross-reference fields are absent:

**Datastream** (~L95–97):
```typescript
expect(result).not.toHaveProperty('system@id');
expect(result).not.toHaveProperty('system@link');
```

**Observation** (~L323–324, L413–415 in dedicated test):
```typescript
it('ignores all cross-reference fields', () => {
  // Input includes 'datastream@id', 'samplingFeature@id', 'foi@id'
  expect(result).not.toHaveProperty('datastream@id');
  expect(result).not.toHaveProperty('samplingFeature@id');
  expect(result).not.toHaveProperty('foi@id');
});
```

**ControlStream** (~L500–502):
```typescript
expect(result).not.toHaveProperty('system@id');
expect(result).not.toHaveProperty('system@link');
```

**Command** (~L728):
```typescript
expect(result).not.toHaveProperty('controlstream@id');
```

**CommandStatus** (~L943):
```typescript
expect(result).not.toHaveProperty('command@id');
```

**Total: ~10 `not.toHaveProperty` assertions** that would need to be updated if the fix is applied. These would change from verifying absence to verifying presence (with the new camelCase field names, e.g., `systemId` instead of `system@id`).

### 4.5 Existing Tolerant Extraction Pattern

The parsers already use a consistent tolerant extraction pattern for optional fields:

```typescript
...(typeof obj.description === 'string'
  ? { description: obj.description }
  : {}),
```

The proposed cross-reference extraction would follow this identical pattern:

```typescript
...(typeof obj['system@id'] === 'string'
  ? { systemId: obj['system@id'] }
  : {}),
```

This is the established code pattern — no new abstractions, no new helpers, no architectural changes.

---

## 5. Reference Document Review

### OGC API — Connected Systems Part 2 (OGC 23-002)

The spec defines cross-reference associations as **Required** in the resource model tables:

| Spec Section | Table | Resource | Association | Cardinality |
|-------------|-------|----------|-------------|-------------|
| §9.2 | Table 5 | Datastream | `system` | **Required** (1) |
| §9.7 | Table 7 | Observation | `datastream` | **Required** (1) |
| §9.7 | Table 7 | Observation | `samplingFeature` | Optional (0..1) |
| §10.2 | Table 10 | ControlStream | `system` | **Required** (1) |
| §10.7 | Table 12 | Command | `controlstream` | **Required** (1) |
| §10.11 | Table 15 | CommandStatus | `command` | **Required** (1) |

These are not optional metadata — they are **fundamental structural relationships** in the resource model. The JSON encoding (§16.1) uses `@id` and `@link` fields to carry these associations. The spec examples themselves include these fields:

- §16.1.3 (Datastream JSON): includes `system@link`, `featureOfInterest@link`, `samplingFeature@link`
- §16.1.5 (Observation JSON): includes `datastream@id`, `foi@id`
- §16.1.6 (ControlStream JSON): includes `system@link`
- §16.1.8 (Command JSON): includes `controlstream@id`
- §16.1.9 (CommandStatus JSON): includes `command@id`

**Key distinction from Issues #100/#102:** Those issues dealt with debatable design choices (assertion strictness) where the spec was ambiguous about client-side enforcement. Issue #103 deals with **Required associations in the resource data model** — the spec is unambiguous that these relationships exist and are carried in the JSON encoding.

### Comparison with Part 1 Parsers

The Part 1 parsers (systems, deployments, procedures, samplingFeatures, properties) handle GeoJSON Feature objects, which carry cross-references differently (via `links` and `properties`). Part 2 resources are flat JSON objects where `@id`/`@link` fields are the primary cross-reference mechanism. This is a Part 2-specific concern.

### AI Operational Constraints

- **§2.1:** "Do not infer unstated requirements; do not expand scope." — The scope is precisely defined: add optional cross-reference fields to 5 interfaces and extract them in 5 parsers.
- **§2.2:** "Preserve upstream structure/naming/patterns; prefer minimal diffs." — The proposed change uses the identical tolerant extraction pattern already in every parser. The diff is ~3–5 lines per parser function plus interface additions. No new abstractions, no new dependencies.
- **§2.3:** "No refactoring for style." — This is not a refactoring — it is adding missing spec-defined data fields.

---

## 6. Risk Assessment

### Risk of Making the Fix

| Risk | Severity | Description |
|------|----------|-------------|
| **Interface expansion** | **VERY LOW** | All new fields are optional (`?`). Existing consumers that destructure or use Part 2 models are completely unaffected — optional fields they don't access simply don't exist on their objects. |
| **Parser changes** | **VERY LOW** | ~3–5 lines per parser using the identical extraction pattern already in use. The `satisfies` type check ensures type safety at compile time. |
| **Test updates** | **LOW** | ~10 `not.toHaveProperty` assertions need updating. The existing test fixtures already include cross-reference fields in their input — they just verify the output doesn't have them. After the fix, they verify the output does have them (under camelCase names). |
| **Upstream contribution impact** | **POSITIVE** | Preserving spec-defined Required associations **strengthens** the contribution. An upstream reviewer seeing that the parsers extract `datastream@id` as `datastreamId` will recognize spec conformance. A reviewer seeing those fields intentionally discarded might question why Required associations are dropped. |
| **Backward compatibility** | **ZERO RISK** | No existing method signatures change. No existing behavior changes. No existing interface contracts are modified — only extended with optional fields. A consumer who never accesses `observation.datastreamId` sees zero difference. |

### Risk of Doing Nothing

| Risk | Severity | Description |
|------|----------|-------------|
| **Spec conformance gap in contribution** | **MEDIUM** | Required associations per OGC 23-002 Tables 5, 7, 10, 12, 15 are being discarded. Upstream reviewers familiar with the spec may flag this. |
| **Consumer friction** | **MEDIUM** | Any consumer wanting parent navigation must bypass the typed models and work with raw JSON — undermining the purpose of having typed parsers. |
| **Inconsistency with Part 1** | **LOW** | Part 1 GeoJSON parsers preserve the full `properties` bag which includes cross-references. Part 2 parsers strip them, creating an asymmetry in the library's handling of spec-defined associations. |

### Critical Differentiator from Issues #100 and #102

| Dimension | Issues #100/#102 | Issue #103 |
|-----------|-----------------|-----------|
| **Change type** | Behavioral — remove/change assertion guards | Additive — new optional fields |
| **Existing behavior affected** | Yes — methods stop throwing or gain parameters | No — all existing behavior unchanged |
| **Test impact** | 57+ assertion tests + 28 new tests | ~10 assertion flips + ~15 new tests |
| **API contract change** | Yes — catch(EndpointError) patterns break | No — optional fields are invisible to existing consumers |
| **Backward compatible** | Debatable | Unambiguous yes |
| **Spec basis** | Ambiguous (spec doesn't mandate client-side assertion behavior) | Unambiguous (Tables define Required associations) |

---

## 7. Recommendation

### **FIX — Genuine Spec-Conformance Gap, Minimal Risk, Purely Additive**

Issue #103 identifies a **real specification conformance gap** where Required associations defined in the OGC resource model are being discarded during parsing. The analysis confirms:

1. OGC 23-002 Tables 5, 7, 10, 12, 15 define these associations as **Required** — not optional metadata
2. The JSON encoding (§16.1) uses `@id` and `@link` fields as the **canonical** mechanism to carry these associations
3. The current parsers **intentionally strip** these fields — this was a known scope boundary, not an oversight
4. The proposed fix is **purely additive** — optional interface fields, same extraction pattern, zero impact on existing consumers

### Why FIX (not DEFER)

Unlike Issues #100/#102, this change has an entirely different risk profile:

1. **Zero backward compatibility risk** — all new fields are optional, no existing signatures change, no existing behavior changes
2. **Minimal diff** — ~3–5 lines per parser, using the identical pattern already in the codebase
3. **Strengthens the contribution** — upstream reviewers will see spec-conformant handling of Required associations
4. **Unambiguous spec basis** — the resource model tables define these as Required, the JSON examples include them; there is no spec ambiguity here

### Implementation Guidance

If the fix is implemented, the following approach preserves maximal safety:

**1. Interface additions** (`model.ts`) — add optional fields only:

```typescript
export interface Datastream {
  // ... existing 14 fields unchanged ...
  /** ID of the parent system (from `system@id` in raw JSON). */
  systemId?: string;
}

export interface Observation {
  // ... existing 6 fields unchanged ...
  /** ID of the parent datastream (from `datastream@id` in raw JSON). */
  datastreamId?: string;
  /** ID of the sampling feature (from `samplingFeature@id` in raw JSON). */
  samplingFeatureId?: string;
  /** ID of the feature of interest (from `foi@id` in raw JSON). */
  featureOfInterestId?: string;
}

export interface ControlStream {
  // ... existing 13 fields unchanged ...
  /** ID of the parent system (from `system@id` in raw JSON). */
  systemId?: string;
}

export interface Command {
  // ... existing 7 fields unchanged ...
  /** ID of the parent control stream (from `controlstream@id` in raw JSON). */
  controlStreamId?: string;
}

export interface CommandStatus {
  // ... existing 7 fields unchanged ...
  /** ID of the parent command (from `command@id` in raw JSON). */
  commandId?: string;
}
```

**2. Parser extraction** (`part2.ts`) — same tolerant pattern, ~3–5 lines per function:

```typescript
// In parseDatastream() return object:
...(typeof obj['system@id'] === 'string'
  ? { systemId: obj['system@id'] as string }
  : {}),

// In parseObservation() return object:
...(typeof obj['datastream@id'] === 'string'
  ? { datastreamId: obj['datastream@id'] as string }
  : {}),
...(typeof obj['samplingFeature@id'] === 'string'
  ? { samplingFeatureId: obj['samplingFeature@id'] as string }
  : {}),
...(typeof obj['foi@id'] === 'string'
  ? { featureOfInterestId: obj['foi@id'] as string }
  : {}),
```

**3. Scope boundary — `@link` fields:** Issue #103 proposes extracting both `@id` (string) and `@link` (structured object with `href`, `uid?`, `title?`) fields. The **minimum viable fix** is to extract `@id` fields only — these are simple strings and cover the primary use case (parent navigation by ID). The `@link` fields require defining a new interface for the link structure and are a lower-priority addition that could be deferred. This keeps the initial diff smaller.

**4. Test updates** (`part2.spec.ts`) — ~10 assertion flips from `not.toHaveProperty` to `toHaveProperty` with value checks, plus new tests for the extraction:

```typescript
// Before:
expect(result).not.toHaveProperty('system@id');
// After:
expect(result).toHaveProperty('systemId', '0o0o');
```

### What NOT to Change

- **Do not modify the `links` array handling** — the issue correctly identifies that `links` is unreliable for parent references; the fix adds `@id` extraction alongside, not instead of, links.
- **Do not change any existing field types or behaviors** — this is purely additive.
- **Do not extract `@link` structured objects in the initial fix** unless specifically requested — `@id` strings are sufficient for parent navigation and keep the diff minimal.

---

## Appendix A: Authority Precedence Analysis

| Authority Level | Source | Ruling |
|-----------------|--------|--------|
| **1. OGC Specification** | OGC 23-002 Tables 5, 7, 10, 12, 15 — associations marked **Required**; §16.1 JSON examples include `@id`/`@link` fields | **Strongly supports** the fix — Required data is being discarded |
| **2. AI Collaboration Agreement** | §2.2 — preserve structure, prefer minimal diffs | **Supports** the fix — same extraction pattern, minimal additive diff |
| **3. Issue Description** | #103 — add optional cross-reference fields to 5 interfaces and 5 parsers | Defines scope clearly |
| **4. Existing Code** | Parsers use `satisfies` with explicit field listing; JSDoc says "intentionally ignored" | Prior scope boundary — not a design objection to the data |
| **5. Conversation Context** | User prioritizes protecting CSAPI contribution integrity | **Supports** the fix — preserving Required spec associations strengthens the contribution |

**Conclusion:** All five authority levels support making this fix. The OGC spec (highest authority) is unambiguous — these are Required associations. The existing code's "intentionally ignored" comments reflect a prior scope boundary, not a design decision to permanently exclude spec-required data. The AI Operational Constraints' "minimal diffs" rule is satisfied by the additive nature of the change.

---

## Appendix B: Cross-Reference to Related Issues

| Issue | Repository | Relationship | Status |
|-------|------------|-------------|--------|
| [#103](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/103) | ogc-client-CSAPI_2 | **This issue** — Part 2 cross-reference fields discarded | Open |
| [#102](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/102) | ogc-client-CSAPI_2 | **Related** — command/observation nested paths (DEFERRED); workaround required extracting `controlstream@id` from raw JSON — exactly the gap #103 addresses | Open (Deferred) |
| [#100](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/100) | ogc-client-CSAPI_2 | **Related** — `assertResourceAvailable()` overly strict (DEFERRED); same Part 2 interoperability theme | Open (Deferred) |
| [#101](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/101) | ogc-client-CSAPI_2 | **Precedent** — `parseDataRecord()` complex types (FIX applied); similar spec-conformance gap in parser layer | Closed |
| [ogc-csapi-explorer#32](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/32) | ogc-csapi-explorer | **Discovery source** — Command status history; first encountered missing `controlstream@id` | Open |
| [ogc-csapi-explorer ecce874](https://github.com/OS4CSAPI/ogc-csapi-explorer/commit/ecce874) | ogc-csapi-explorer | **Discovery source** — Parent navigation breadcrumbs; required raw JSON for all cross-reference fields | Commit |

### Linked Reference Documents

| Document | Location | Relevance |
|----------|----------|-----------|
| AI Operational Constraints | [docs/governance/AI_OPERATIONAL_CONSTRAINTS.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/governance/AI_OPERATIONAL_CONSTRAINTS.md) | §2.1 (no scope expansion), §2.2 (minimal diffs) — both satisfied by additive-only change |
| OGC API Connected Systems Part 2 | OGC 23-002, §9.2 (Table 5), §9.7 (Table 7), §10.2 (Table 10), §10.7 (Table 12), §10.11 (Table 15) | Resource model association tables — Required associations being discarded |
| OGC 23-002 §16.1 JSON Encoding | §16.1.3 (Datastream), §16.1.5 (Observation), §16.1.6 (ControlStream), §16.1.8 (Command), §16.1.9 (CommandStatus) | Spec examples showing `@id`/`@link` fields in JSON representations |
| `parseDatastream()` | `src/ogc-api/csapi/formats/part2.ts` L114 | Strips `system@id`, `system@link` |
| `parseControlStream()` | `src/ogc-api/csapi/formats/part2.ts` L213 | Strips `system@id`, `system@link` |
| `parseObservation()` | `src/ogc-api/csapi/formats/part2.ts` ~L420 | Strips `datastream@id`, `samplingFeature@id`, `foi@id` |
| `parseCommand()` | `src/ogc-api/csapi/formats/part2.ts` L329 | Strips `controlstream@id` |
| `parseCommandStatus()` | `src/ogc-api/csapi/formats/part2.ts` ~L490 | Strips `command@id` |
| `Datastream` interface | `src/ogc-api/csapi/model.ts` L434 | Lacks `systemId` field |
| `Observation` interface | `src/ogc-api/csapi/model.ts` L473 | Lacks `datastreamId`, `samplingFeatureId`, `featureOfInterestId` fields |
| `ControlStream` interface | `src/ogc-api/csapi/model.ts` L498 | Lacks `systemId` field |
| `Command` interface | `src/ogc-api/csapi/model.ts` L534 | Lacks `controlStreamId` field |
| `CommandStatus` interface | `src/ogc-api/csapi/model.ts` L559 | Lacks `commandId` field |
| Issue #100 Findings Report | [docs/testing/demo-app-findings/issue-100-assert-resource-available.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/testing/demo-app-findings/issue-100-assert-resource-available.md) | DEFER recommendation — different risk profile (behavioral change vs. additive) |
| Issue #101 Findings Report | [docs/testing/demo-app-findings/issue-101-parse-data-record-complex-types.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/testing/demo-app-findings/issue-101-parse-data-record-complex-types.md) | FIX precedent — similar spec-conformance gap in parser layer |
| Issue #102 Findings Report | [docs/testing/demo-app-findings/issue-102-command-observation-nested-paths.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/testing/demo-app-findings/issue-102-command-observation-nested-paths.md) | DEFER recommendation — Issue #102 workaround required exactly the `controlstream@id` field that #103 proposes preserving |
