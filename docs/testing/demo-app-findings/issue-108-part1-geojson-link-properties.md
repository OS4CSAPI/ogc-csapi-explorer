# Issue #108 Findings Report — Part 1 (GeoJSON) TypeScript Interfaces Omit All `@link` Association Properties

> **Date:** 2026-02-21
> **Issue:** [OS4CSAPI/ogc-client-CSAPI_2#108](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/108) — "Part 1 (GeoJSON) TypeScript interfaces omit all `@link` association properties"
> **Repository under review:** `OS4CSAPI/ogc-client-CSAPI_2` (`src/ogc-api/csapi/model.ts`, `src/ogc-api/csapi/formats/geojson.ts`)
> **Discovered by:** [ogc-csapi-explorer `tryLinkFallback()` workaround](https://github.com/OS4CSAPI/ogc-csapi-explorer/commit/ad06b52), [Gap Analysis Report](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/csapi-link-property-gap-analysis.md)
> **Labels:** enhancement, model

---

## Table of Contents

1. [AI Operational Constraints Acknowledgment](#1-ai-operational-constraints-acknowledgment)
2. [Executive Summary](#2-executive-summary)
3. [Issue Description](#3-issue-description)
4. [Source Code Review](#4-source-code-review)
5. [Spec Reference Review](#5-spec-reference-review)
6. [Relationship to Issue #103](#6-relationship-to-issue-103)
7. [Risk Assessment](#7-risk-assessment)
8. [Recommendation](#8-recommendation)
9. [Appendix A: Authority Precedence Analysis](#appendix-a-authority-precedence-analysis)
10. [Appendix B: Scope Boundary — What This Issue Does NOT Cover](#appendix-b-scope-boundary--what-this-issue-does-not-cover)

---

## 1. AI Operational Constraints Acknowledgment

Per the [AI Operational Constraints](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/governance/AI_OPERATIONAL_CONSTRAINTS.md), this review follows the required authority precedence:

1. **OGC specifications** (OGC 23-001 Part 1) — primary authority
2. **AI Collaboration Agreement** — governing constraints
3. **Issue description** — task scope
4. **Existing code patterns** — implementation precedent
5. **Conversation context** — supplementary guidance

This report does not expand scope beyond what Issue #108 describes. Per §2.1 (do not infer unstated requirements), §2.2 (preserve existing patterns, prefer minimal diffs), and §2.3 (no refactoring for style), this report evaluates the existing interface definitions against the OGC specification and provides a risk-calibrated recommendation.

---

## 2. Executive Summary

**Issue #108 identifies a genuine specification conformance gap — the four Part 1 GeoJSON resource interfaces (`System`, `Deployment`, `Procedure`, `SamplingFeature`) do not include any `@link` fields defined by OGC 23-001 §16 for encoding structural associations between resources. The proposed fix is purely additive — optional fields on existing interfaces plus a new shared type — with zero impact on existing consumers or tests.**

| Finding | Description | Severity | Recommendation |
|---------|-------------|----------|----------------|
| **F-108.1** | 3 of 4 Part 1 interfaces are missing spec-defined `@link` fields that encode structural associations between resources | **SPEC GAP** | **FIX** — add optional `@link`-derived fields to interfaces |
| **F-108.2** | `SamplingFeature` JSDoc (L412) explicitly states `sampledFeature@link` is required, but the interface omits it | **SELF-CONTRADICTORY** | FIX — interface should match its own documentation |
| **F-108.3** | Proposed `CSAPIResourceRef` type matches spec's `@link` object shape (`{href, uid?, title?, rt?}`) and has no existing equivalent | **NEW TYPE NEEDED** | Add shared type — follows existing pattern (`ResourceLink` for HATEOAS links) |
| **F-108.4** | All new fields are optional (`?`) — servers are not required to include `@link` properties in every response context | **LOW RISK** | Backward-compatible by definition |
| **F-108.5** | `Procedure` has no spec-defined `@link` properties; issue correctly excludes it from changes | **NO CHANGE** | Correct — no modification needed |
| **F-108.6** | This is the **interface-only** half of the fix; parser changes (`extractCSAPIFeature()`) are tracked separately in #109 | **SCOPE BOUNDARY** | Respect issue separation — this issue is model-only |

**Conclusion:** This is a genuine spec-conformance gap that is the direct Part 1 counterpart to Issue #103 (Part 2 `@id` fields). The fix is minimal (1 new type + 4 optional fields across 3 interfaces), purely additive, and backward-compatible. The contribution goal explicitly states the library should support "GeoJSON extensions recognizing all CSAPI-specific resource types **and properties**." `@link` properties are spec-defined properties. Recommend fixing with careful implementation.

---

## 3. Issue Description

Issue #108 reports that the OGC CS API JSON encoding (OGC 23-001 §16) defines inline `@link` properties on Part 1 GeoJSON resources to encode structural associations:

```
System ──systemKind@link──→ Procedure
Deployment ──platform@link──→ System (platform)
Deployment ──deployedSystems@link──→ [System, System, ...]
SamplingFeature ──sampledFeature@link──→ Feature
```

These `@link` fields are **inline properties** within the GeoJSON `properties` object — they are distinct from the HATEOAS `links[]` array that provides navigation URLs. The `@link` objects have a different shape (`{href, uid?, title?, rt?}`) than `ResourceLink` / `OgcApiDocumentLink` (`{rel, type, title, href}`).

After `extractCSAPIFeature()` parses server JSON, all `@link` data is silently discarded because the TypeScript interfaces have no `@link` fields, and the parser uses an allowlist extraction pattern that only copies named interface properties.

### Real-World Impact

The gap was discovered during development of the [ogc-csapi-explorer](https://github.com/OS4CSAPI/ogc-csapi-explorer) demo app against OSH SensorHub. That server:
- **Does NOT** implement cross-resource navigation endpoints (`/systems/{id}/procedures` returns 400)
- **DOES** include `@link` properties in GeoJSON responses (the only path to procedure associations)

The explorer had to implement a `tryLinkFallback()` workaround ([commit ad06b52](https://github.com/OS4CSAPI/ogc-csapi-explorer/commit/ad06b52)) that bypasses the library's typed models and reads `@link` fields from raw JSON.

---

## 4. Source Code Review

### 4.1 Current Interface Definitions

**System** ([model.ts L306–328](src/ogc-api/csapi/model.ts#L306-L328)):
```typescript
export interface System {
  id: string;
  type: 'Feature';
  properties: {
    featureType: SystemTypeUri | string;
    uid: string;
    name: string;
    description?: string;
    assetType?: 'Equipment' | 'Human' | 'LivingThing' | 'Simulation' | 'Process' | 'Group' | 'Other';
    validTime?: TimeInterval;
    // ← no systemKind@link
  };
  geometry?: Geometry;
  links: ResourceLink[];
}
```

**Missing:** `systemKind@link` (Conditional — when a procedure exists)

**Deployment** ([model.ts L342–368](src/ogc-api/csapi/model.ts#L342-L368)):
```typescript
export interface Deployment {
  id: string;
  type: 'Feature';
  properties: {
    featureType: string;
    uid: string;
    name: string;
    description?: string;
    validTime?: TimeInterval;
    // ← no platform@link
    // ← no deployedSystems@link
  };
  geometry?: Geometry;
  links: ResourceLink[];
}
```

**Missing:** `platform@link` (Optional), `deployedSystems@link` (Required — array)

**SamplingFeature** ([model.ts L416–433](src/ogc-api/csapi/model.ts#L416-L433)):
```typescript
export interface SamplingFeature {
  id: string;
  type: 'Feature';
  properties: {
    featureType: string;
    uid: string;
    name: string;
    description?: string;
    validTime?: TimeInterval;
    // ← no sampledFeature@link (despite JSDoc stating it is required)
  };
  geometry?: Geometry;
  links: ResourceLink[];
}
```

**Missing:** `sampledFeature@link` (**Required** per OGC 23-001 §8.9 Table 14)

**Procedure** ([model.ts L386–403](src/ogc-api/csapi/model.ts#L386-L403)) — **correctly has no `@link` fields.** The OGC spec defines no `@link` properties for Procedure resources. No change needed.

### 4.2 No `CSAPIResourceRef` Type Exists

A search for `CSAPIResourceRef` across the entire codebase returns zero matches. No type currently models the `@link` object shape (`{href, uid?, title?, rt?}`).

The existing `ResourceLink` (alias for `OgcApiDocumentLink`: `{rel, type, title, href}`) models HATEOAS navigation links, not inline `@link` properties. The two have different shapes and serve different purposes:

| Concept | Type | Shape | Purpose |
|---------|------|-------|---------|
| HATEOAS links | `ResourceLink` | `{rel, type, title, href}` | Server-provided navigation (self, alternate, items) |
| Inline associations | *none* | `{href, uid?, title?, rt?}` | Structural resource-to-resource relationships |

### 4.3 SamplingFeature JSDoc Is Self-Contradictory

The JSDoc on [model.ts L412](src/ogc-api/csapi/model.ts#L412) explicitly states:

> *"The `sampledFeature@link` link relation is also required."*

But the `SamplingFeature` interface defined immediately below it (L416–433) does not include a `sampledFeatureLink` field. The documentation acknowledges the association field but the type definition omits it.

### 4.4 Existing Test Data Includes `@link` Fields

The test file ([geojson.spec.ts L433](src/ogc-api/csapi/formats/geojson.spec.ts#L433)) provides raw SamplingFeature input data that includes `sampledFeature@link`:

```typescript
const raw = makeFeature('sosa:SamplingFeature', {
  geometry: { type: 'Point', coordinates: [12.31, -86.98, -21] },
  'sampledFeature@link': { href: 'http://example.com/feature/1' },
});
```

The test then asserts `featureType`, `geometry`, etc. — but **never asserts that `sampledFeature@link` survives extraction**. The test on [L499](src/ogc-api/csapi/formats/geojson.spec.ts#L499) explicitly documents that extraction without `sampledFeature@link` is tolerated.

This confirms the test suite is already structured to support `@link` data in test input — it just doesn't verify the extracted output carries it forward.

### 4.5 The `extractCSAPIFeature()` Parser Uses Allowlist Extraction

The parser ([geojson.ts L395–472](src/ogc-api/csapi/formats/geojson.ts#L395-L472)) builds return objects using explicit field listings — only named properties survive. Each case uses `satisfies Type` which enforces that the returned object conforms to the interface.

**This means:** Once optional `@link`-derived fields are added to the interfaces (this issue), the parser can be updated to extract them (tracked in Issue #109). The `satisfies` constraint will naturally accommodate optional fields — they can be present or absent.

---

## 5. Spec Reference Review

### 5.1 OGC 23-001 §8.3 Table 8 — System Associations

| Association | Multiplicity | Description |
|-------------|-------------|-------------|
| `procedure` | 0..1 (Conditional) | Link to the procedure/method this system implements. Encoded as `systemKind@link` in JSON. |

### 5.2 OGC 23-001 §8.5 Table 10 — Deployment Associations

| Association | Multiplicity | Description |
|-------------|-------------|-------------|
| `platform` | 0..1 (Optional) | Link to the platform system. Encoded as `platform@link` in JSON. |
| `deployedSystems` | 1..* (Required) | Links to deployed systems. Encoded as `deployedSystems@link` (array) in JSON. |

### 5.3 OGC 23-001 §8.9 Table 14 — SamplingFeature Associations

| Association | Multiplicity | Description |
|-------------|-------------|-------------|
| `sampledFeature` | 1 (Required) | Link to the sampled feature. Encoded as `sampledFeature@link` in JSON. |

### 5.4 OGC 23-001 §16 — JSON Encoding

Section 16 defines the inline `@link` property convention for Part 1 GeoJSON resources. The `@link` suffix indicates a structured reference object with the shape:

```json
{
  "href": "https://server/api/procedures/abc123",
  "uid": "urn:example:procedure:weather-station",
  "title": "Weather Station Procedure",
  "rt": "http://www.w3.org/ns/sosa/Procedure"
}
```

Only `href` is required; `uid`, `title`, and `rt` are optional contextual metadata.

---

## 6. Relationship to Issue #103

Issue #103 (now closed, resolved) addressed the **Part 2** counterpart: five Part 2 interfaces were missing `@id` cross-reference fields (`systemId`, `datastreamId`, `controlStreamId`, `commandId`, etc.). That fix:

- Added optional `@id`-derived fields (scalar strings) to 5 Part 2 interfaces
- Updated 5 parsers to extract `@id` fields using tolerant extraction
- Was purely additive, backward-compatible, minimal diff

Issue #108 is the **Part 1** counterpart with two key differences:

| Dimension | Issue #103 (Part 2) | Issue #108 (Part 1) |
|-----------|--------------------|--------------------|
| Resource types | Datastream, Observation, ControlStream, Command, CommandStatus | System, Deployment, SamplingFeature |
| Field suffix | `@id` (scalar string) | `@link` (structured object) |
| Value shape | `string` → `string` | `{href, uid?, title?, rt?}` → `CSAPIResourceRef` |
| New shared type | None needed | `CSAPIResourceRef` (new) |
| Parser file | `formats/part2.ts` | `formats/geojson.ts` (tracked in #109) |
| Discarding mechanism | Explicit ("intentionally ignored" JSDoc) | Implicit (allowlist extraction — only named fields survive) |

The dependency is natural: #108 defines the interface fields, #109 updates the parser to populate them — exactly as #103 did both in one issue for Part 2.

---

## 7. Risk Assessment

### 7.1 Changes Proposed by Issue #108

| Change | Risk | Rationale |
|--------|------|-----------|
| New `CSAPIResourceRef` interface | **NONE** | New type — no existing code references it |
| Add `systemKindLink?: CSAPIResourceRef` to `System.properties` | **NONE** | Optional field — existing code cannot break |
| Add `platformLink?: CSAPIResourceRef` to `Deployment.properties` | **NONE** | Optional field — existing code cannot break |
| Add `deployedSystemsLink?: CSAPIResourceRef[]` to `Deployment.properties` | **NONE** | Optional field — existing code cannot break |
| Add `sampledFeatureLink?: CSAPIResourceRef` to `SamplingFeature.properties` | **NONE** | Optional field — existing code cannot break |
| Export `CSAPIResourceRef` from `src/index.ts` | **NONE** | Additive export — no existing exports change |

### 7.2 What Does NOT Change

- **No method signatures change** — no function parameter or return type is modified
- **No existing interface fields change** — all current fields remain identical
- **No behavior changes** — the parser is not modified in this issue (that's #109)
- **No existing tests need updating** — all 334+ tests pass unchanged
- **No existing consumers are affected** — adding optional fields to interfaces is a non-breaking change in TypeScript

### 7.3 Why This Is Safe

Adding optional properties to a TypeScript interface is the **most minimal, non-breaking change possible**:

1. **Structural typing**: TypeScript uses structural typing. Objects that previously satisfied `System` will continue to satisfy `System` — the new field is optional, so its absence is valid.
2. **`satisfies` keyword**: The parser's `satisfies System` constraint will still pass — optional fields can be absent.
3. **Generic consumers**: Code that operates on `System`, `Deployment`, or `SamplingFeature` without accessing the new fields is completely unaffected.
4. **Fields are `undefined` until parser is updated**: Until Issue #109 is implemented, the fields will simply be absent from parsed objects — exactly the same behavior as today, just now typed.

### 7.4 Contribution Scope Alignment

The [contribution goal](docs/planning/contribution-goal-and-definition.md) explicitly states:

> *"GeoJSON extensions recognizing all CSAPI-specific resource types **and properties**"*

`@link` properties are spec-defined properties on Part 1 GeoJSON resources. Omitting them leaves the library's type system incomplete for an explicit contribution deliverable.

---

## 8. Recommendation

### Verdict: **FIX — Add optional `@link`-derived fields to Part 1 interfaces**

This is a genuine spec-conformance gap that falls squarely within the CSAPI contribution scope. The fix is:

1. **Spec-driven** — OGC 23-001 Tables 8, 10, 14 define these associations
2. **Purely additive** — new type + optional fields; nothing existing changes
3. **Zero-risk to existing consumers** — optional fields cannot break callers
4. **Consistent with Issue #103 precedent** — same pattern (interface fields for cross-reference data) already applied to Part 2
5. **Minimal diff** — 1 new interface (~8 lines) + 4 optional fields across 3 interfaces

### Implementation Notes

The proposed `CSAPIResourceRef` type and field naming convention from Issue #108 are well-designed:

- `CSAPIResourceRef` matches the spec's `@link` object shape exactly
- camelCase field names (`systemKindLink` not `systemKind@link`) maintain TypeScript ergonomics
- `deployedSystemsLink` is correctly typed as `CSAPIResourceRef[]` (array of links, not a single reference)
- All fields are optional (`?`) — tolerant of servers that omit them

### Scope Boundary

**This issue covers interfaces only.** Parser changes to populate these fields from server JSON are tracked in Issue #109. This separation follows the natural dependency chain identified in the [gap analysis report](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/csapi-link-property-gap-analysis.md): interfaces must define fields before parsers can populate them.

---

## Appendix A: Authority Precedence Analysis

| Level | Source | Says | Supports Fix? |
|-------|--------|------|---------------|
| 1 (highest) | OGC 23-001 §8.3, §8.5, §8.9, §16 | `@link` properties are spec-defined associations on Part 1 GeoJSON resources | **YES** |
| 2 | AI Collaboration Agreement / AI Operational Constraints | §2.2: Preserve upstream structure, prefer minimal diffs | **YES** — additive optional fields are minimal |
| 3 | Issue #108 description | Add optional `@link`-derived fields to Part 1 interfaces | **YES** — clear scope |
| 4 | Existing code (model.ts) | SamplingFeature JSDoc already states `sampledFeature@link` is required | **YES** — self-documenting gap |
| 5 | Explorer workaround (ad06b52) | Consumers must bypass typed models to access `@link` data | **YES** — real-world impact confirmed |

No authority level contradicts the fix. All five levels support it.

---

## Appendix B: Scope Boundary — What This Issue Does NOT Cover

Per AI Operational Constraints §2.1 (do not expand scope beyond the issue description), the following items are explicitly **out of scope** for Issue #108:

| Out-of-Scope Item | Why | Tracked In |
|--------------------|-----|------------|
| Parser changes to `extractCSAPIFeature()` | Separate concern — parser must extract, interfaces must define | [#109](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/109) |
| `@link` resolution utility functions | Higher-level consumer API — depends on both #108 and #109 | [#110](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/110) |
| Part 2 `@link` fields (as distinct from `@id`) | Part 2 resources also have `@link` variants; #103 covered `@id` only | Deferred to future issue |
| Changes to `ResourceLink` / `OgcApiDocumentLink` | Different type for a different purpose (HATEOAS vs. inline associations) | N/A |
| Changes to `Procedure` interface | No spec-defined `@link` properties for Procedure resources | N/A |

---

## Linked References

- [AI Operational Constraints](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/governance/AI_OPERATIONAL_CONSTRAINTS.md)
- [Contribution Goal and Definition](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/planning/contribution-goal-and-definition.md)
- [Issue #103 — Part 2 cross-reference fields](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/103) (closed, resolved — the Part 2 counterpart)
- [Issue #103 Findings Report](docs/testing/demo-app-findings/issue-103-part2-cross-reference-fields.md)
- [Issue #109 — Part 1 parser drops `@link` properties](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/109) (parser changes)
- [Issue #110 — No `@link` resolution utilities](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/110) (utility functions)
- [Gap Analysis Report](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/csapi-link-property-gap-analysis.md) — Full audit of all `@link` gaps
- [ogc-csapi-explorer `tryLinkFallback()` workaround (ad06b52)](https://github.com/OS4CSAPI/ogc-csapi-explorer/commit/ad06b52)
- OGC 23-001 §8.3 (Table 8) — System resource model
- OGC 23-001 §8.5 (Table 10) — Deployment resource model
- OGC 23-001 §8.9 (Table 14) — SamplingFeature resource model
- OGC 23-001 §16 — JSON encoding for Part 1 GeoJSON resources
