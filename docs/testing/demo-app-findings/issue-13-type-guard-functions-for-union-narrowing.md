# Issue #13 Findings Report — Add type guard functions for extractCSAPIFeature() union type narrowing (F-9)

> **Date:** 2026-02-18
> **Issue:** [OS4CSAPI/ogc-csapi-explorer#13](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/13) — "Add type guard functions for extractCSAPIFeature() union type narrowing (F-9)"
> **Repository under review:** `OS4CSAPI/ogc-client-CSAPI_2` (`src/ogc-api/csapi/formats/geojson.ts`)
> **Labels:** enhancement

---

## Table of Contents

1. [AI Operational Constraints Acknowledgment](#1-ai-operational-constraints-acknowledgment)
2. [Executive Summary](#2-executive-summary)
3. [Issue Description](#3-issue-description)
4. [Source Code Review](#4-source-code-review)
5. [Reference Document Review](#5-reference-document-review)
6. [Risk Assessment](#6-risk-assessment)
7. [Analysis: Type Guard Functions](#7-analysis-type-guard-functions)
8. [Recommendation](#8-recommendation)
9. [Appendix A: Authority Precedence Analysis](#appendix-a-authority-precedence-analysis)
10. [Appendix B: Cross-Reference Matrix](#appendix-b-cross-reference-matrix)

---

## 1. AI Operational Constraints Acknowledgment

Per the [AI Operational Constraints](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/governance/AI_OPERATIONAL_CONSTRAINTS.md), this review follows the required authority precedence:

1. **OGC specifications** — primary authority
2. **AI Collaboration Agreement** — governing constraints
3. **Issue description** — task scope
4. **Existing code patterns** — implementation precedent
5. **Conversation context** — supplementary guidance

This report does not propose behavioral modifications to the library without approval. All recommendations distinguish between **fact** (verified), **inference** (reasoned), and **proposal** (requires approval), per Section 3 of the constraints.

**Key constraint assessment for this issue:** Section 2.2 of the AI Operational Constraints states: *"Do not introduce new abstractions, layers, or dependencies without approval."* Issue #13 proposes adding 4 new exported type guard functions to the library's public API. These are **new public API surface** — not a type annotation tweak or a refactor. They introduce new functions that consumers would depend on, that must be maintained, and that upstream reviewers must accept. **Section 2.2 is directly relevant here.** Unlike Issue #12's `Pick<>` (a built-in utility type applied to an existing parameter), type guards are new hand-written functions with runtime behavior that become part of the library's contract.

---

## 2. Executive Summary

**Issue #13 proposes adding 4 type guard functions (`isSystem()`, `isDeployment()`, `isProcedure()`, `isSamplingFeature()`) to enable TypeScript consumers to narrow the `System | Deployment | Procedure | SamplingFeature` union type returned by `extractCSAPIFeature()` without `as any` casts. After thorough review, this report recommends AGAINST including these type guards in the CSAPI upstream contribution. The change is valid in isolation but carries more risk than benefit given the contribution's current scope, upstream acceptance concerns, and the availability of simpler alternatives that consumers can implement themselves.**

| Aspect | Assessment |
|--------|------------|
| **Change type** | New public API functions — 4 exported type guards with runtime behavior |
| **Scope** | ~40-60 new lines in `geojson.ts` (or new `type-guards.ts`), ~4 new exports in `index.ts`, ~100-200 lines of new tests |
| **Production behavior modified** | **No** — purely additive; no existing code paths change |
| **Existing tests affected** | **None** — additive functions don't break existing tests |
| **Risk to library integrity** | **Low-Medium** — new API surface increases maintenance burden and upstream reviewer scrutiny |
| **New abstraction introduced** | **Yes** — 4 new exported functions that become part of the library's public contract |
| **Upstream pattern precedent** | **None** — the upstream `ogc-client` library does not export type guard functions anywhere |
| **AI Constraints trigger** | **Yes** — Section 2.2 ("no new abstractions... without approval") is triggered |
| **Priority ranking** | #9 in upstream-findings.md (Medium severity, Low effort) — "Should Address" category, lowest priority tier |

**Key findings from this review:**

1. **Fact:** `extractCSAPIFeature()` returns `System | Deployment | Procedure | SamplingFeature`. Accessing `validTime` on the union requires narrowing because `Procedure` does not have a `validTime` property. This is correct TypeScript behavior — the compiler is protecting consumers from runtime errors.

2. **Fact:** The `getCSAPIResourceType()` function (already exported, L189 of geojson.ts) ALREADY provides the runtime discriminator needed for consumers to narrow the union. It returns `'System' | 'Deployment' | 'Procedure' | 'SamplingFeature' | null`. A consumer can write:
   ```typescript
   const resource = extractCSAPIFeature(feature);
   if (getCSAPIResourceType(feature) === 'System') {
     // TypeScript doesn't auto-narrow here, but the check is sound
     const system = resource as System;
   }
   ```

3. **Fact:** The upstream `ogc-client` library contains **zero** type guard functions in its entire codebase. No WMS, WFS, WMTS, STAC, or EDR module exports `isFoo()` type predicates. Adding type guards to the CSAPI module would be the first instance, introducing a pattern with no upstream precedent.

4. **Fact:** The issue's proposed implementation uses `getCSAPIResourceType()` internally, wrapping it in an `is` predicate. The guards add no new classification logic — they are convenience wrappers around an existing function.

5. **Fact:** The consumer friction documented in the issue (Vue template `as any` casts) is real but occurs in the **demo app** (not the library). The library's type system is correct; the friction is at the consumer integration layer.

6. **Inference:** Adding 4 new exported functions increases the library's public API surface by ~4% (4 new exports on top of ~100 existing exports). Each new export is a maintenance commitment that upstream reviewers must evaluate, document, and support in perpetuity.

7. **Inference:** The risk-benefit ratio is unfavorable for the upstream contribution. The benefit is convenience (fewer lines of consumer code). The risk is upstream PR scope creep, reviewer pushback on adding consumer DX helpers to a library that has historically not provided them, and increased maintenance burden.

---

## 3. Issue Description

### 3.1 Origin: Finding F-9

Issue #13 corresponds to **Finding F-9** from the [upstream findings document](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/upstream-findings.md). It was first identified as **Library Finding #10** in the [library integration report](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/library-integration-report.md) during the demo app's ResourceDetail component integration.

### 3.2 The Problem

`extractCSAPIFeature()` returns a 4-way union type:

```typescript
export function extractCSAPIFeature(
  feature: unknown
): System | Deployment | Procedure | SamplingFeature
```

Several properties exist on some union members but not others:

| Property | System | Deployment | Procedure | SamplingFeature |
|----------|--------|------------|-----------|-----------------|
| `properties.validTime` | ✅ optional | ✅ required | ❌ absent | ✅ optional |
| `properties.systemType` | ✅ | ❌ | ❌ | ❌ |
| `properties.assetType` | ✅ | ❌ | ❌ | ❌ |
| `properties.featureType` | ✅ | ✅ | ✅ | ✅ |
| `properties.uid` | ✅ | ✅ | ✅ | ✅ |
| `properties.name` | ✅ | ✅ | ✅ | ✅ |

TypeScript correctly prevents accessing `resource.properties.validTime` without narrowing because the type could be `Procedure`, which has no `validTime`. Consumers must use `as any` casts:

```typescript
// ❌ TypeScript error
console.log(resource.properties.validTime);

// ❌ Unsafe workaround
console.log((resource.properties as any).validTime);
```

### 3.3 The Proposed Solution

Add 4 type guard functions:

```typescript
export function isSystem(resource: CSAPIFeature): resource is System { ... }
export function isDeployment(resource: CSAPIFeature): resource is Deployment { ... }
export function isProcedure(resource: CSAPIFeature): resource is Procedure { ... }
export function isSamplingFeature(resource: CSAPIFeature): resource is SamplingFeature { ... }
```

### 3.4 Why This Report Takes a Conservative Position

The user has expressed strong concern about changes that could degrade the integrity of the CSAPI client library contribution. This change is not a bug fix — it is a **convenience feature** that adds new public API surface to a contribution that is already undergoing upstream review scrutiny. The key question is not "is this useful?" (it is) but "does this belong in the upstream contribution, and is the risk worth it?"

---

## 4. Source Code Review

### 4.1 `geojson.ts` — `extractCSAPIFeature()` (L307-L387)

The function recognizes GeoJSON Features by `featureType` and returns typed resources. The return type `System | Deployment | Procedure | SamplingFeature` is the accurate union of the 4 Part 1 resource types that the function can produce.

**Assessment:** The function's return type is correct. The union type is not a bug — it accurately reflects that the function can return any of 4 types. The TypeScript compiler is working as designed when it prevents unguarded access to type-specific properties.

### 4.2 `geojson.ts` — `getCSAPIResourceType()` (L189-L208)

```typescript
export function getCSAPIResourceType(
  feature: unknown
): CSAPIResourceTypeName | null {
  const ft = getFeatureType(feature);
  if (ft === undefined) return null;

  const sosaLocal = toSosaLocalName(ft);
  if (sosaLocal !== undefined) {
    if (SYSTEM_LOCAL_NAMES.has(sosaLocal)) return 'System';
    if (DEPLOYMENT_LOCAL_NAMES.has(sosaLocal)) return 'Deployment';
    if (PROCEDURE_LOCAL_NAMES.has(sosaLocal)) return 'Procedure';
    if (SAMPLING_FEATURE_LOCAL_NAMES.has(sosaLocal)) return 'SamplingFeature';
    return null;
  }

  const smlLocal = toSensormlLocalName(ft);
  if (smlLocal !== undefined) {
    if (SENSORML_SAMPLING_FEATURE_LOCAL_NAMES.has(smlLocal))
      return 'SamplingFeature';
    return null;
  }

  return null;
}
```

**Assessment:** This function already contains 100% of the classification logic that the proposed type guards would use. The type guards would simply wrap calls to `getCSAPIResourceType()` with an `is` predicate return type. No new recognition logic would be added.

### 4.3 `model.ts` — Interface Definitions (L261-L374)

Reviewed all 4 Part 1 resource interfaces:

| Interface | `validTime` field | Other unique fields |
|-----------|-------------------|---------------------|
| `System` (L261) | `validTime?: TimeInterval` (optional) | `assetType?`, `systemType?` (via `featureType` discriminator) |
| `Deployment` (L293) | `validTime: TimeInterval` (required) | — |
| `Procedure` (L323) | **absent** | `geometry: null` |
| `SamplingFeature` (L353) | `validTime?: TimeInterval` (optional) | — |

**Assessment:** The `validTime` asymmetry is correct per the OGC spec. Procedures describe methodologies — they don't have temporal validity periods. `Procedure.properties` correctly omits `validTime`. This is not a modeling error; it reflects the spec.

### 4.4 `index.ts` — Current Exports (L92-L98)

The library currently exports from `geojson.ts`:
- `SOSA_NS`
- `SENSORML_NS`
- `isCSAPIFeature`
- `getCSAPIResourceType`
- `parseValidTime`
- `isValidUri`
- `extractCSAPIFeature`

**Assessment:** 7 exports from this module. Adding 4 type guards would increase this to 11 — a 57% increase in the module's public API surface. Each export is a maintenance commitment.

### 4.5 Upstream `ogc-client` — Type Guard Precedent Search

Searched the entire codebase for type guard patterns (`is` predicate functions):

**Result: Zero type guard functions exist anywhere in the upstream library.** The WMS, WFS, WMTS, STAC, EDR, and TMS modules do not export `isFoo()` type predicates. Consumers of these modules narrow types using other patterns (direct property checks, explicit casts based on known context).

**Assessment:** Adding type guards to the CSAPI module would establish a new pattern with no upstream precedent. This is exactly the kind of change that AI Operational Constraints Section 2.2 warns against: introducing new patterns that diverge from existing library conventions.

---

## 5. Reference Document Review

### 5.1 Upstream Findings (`upstream-findings.md`)

Finding **F-9** is defined here:

> *"`extractCSAPIFeature()` returns `System | Deployment | Procedure | SamplingFeature`. The `validTime` property exists on `System`, `Deployment`, and `SamplingFeature` but NOT on `Procedure`. TypeScript correctly prevents accessing `typedResource.properties.validTime` because the type could be `Procedure`."*
>
> Priority rank: **#9** (Medium severity, Low effort)

F-9 is ranked **last** in the "Should Address" category — priority #9 out of 11 findings. It is below F-8 (constructor narrowing), F-7 (generic CRUD), and F-10 (Content-Type helper), all of which are simpler and lower-risk changes.

The recommended solution: *"Add type-narrowing guards: `isSystem(r): r is System`, `isDeployment(r): r is Deployment`, etc."*

**Assessment:** The upstream findings document correctly identifies the friction but places it at the bottom of the priority list. The fix is characterized as "Low effort" but has non-trivial implications for upstream acceptance.

### 5.2 Library Integration Report (`library-integration-report.md`)

**Library Finding #10** is where F-9 was first identified:

> *"The function returns `System | Deployment | Procedure | SamplingFeature`. The `validTime` property exists on `System.properties.validTime` (optional), `Deployment.properties.validTime` (required), `SamplingFeature.properties.validTime` (optional), and `Procedure.properties` — no `validTime` field at all."*

The report suggests two potential fixes:
1. Add `validTime?: TimeInterval` to `Procedure.properties` (phantom property)
2. Provide type-narrowing helpers: `isSystemResource(r): r is System`

The report notes: *"The second approach is more correct. The first adds a phantom property to satisfy a different use case."*

**Assessment:** Option 1 (phantom `validTime` on Procedure) would be incorrect — it would claim `Procedure` has a property it doesn't have per the OGC spec. Option 2 (type guards) is technically correct but adds new API surface. There is a third option the report doesn't consider: **do nothing, and let consumers use the existing `getCSAPIResourceType()` function to check the type and cast accordingly.**

### 5.3 Library Findings Gap Analysis (`library-findings-gap-analysis.md`)

F-9 actionability assessment:

| Finding | Actionable? | Effort | Priority |
|---------|------------|--------|----------|
| F-9 | Yes — type guards | Low | 5 (Medium) |

The document notes: *"Would eliminate `as any` casts in the ResourceDetail component. Cleaner code, no visible UI change."*

**Assessment:** The benefit is described in terms of the demo app, not the library consumers broadly. The "Low effort" assessment is accurate for writing the code but does not account for upstream reviewer friction or the precedent it sets.

### 5.4 Contribution Goal Accuracy Assessment (`contribution-goal-accuracy-assessment.md`)

This document assesses the CSAPI library contribution's accuracy against its planning document. It confirms:

> *"The library is a URL builder, not an HTTP client — it does not perform fetch operations, manage authentication, or handle response deserialization end-to-end."*

**Assessment:** The library's core identity is as a URL builder with format parsing. Type guards are a consumer convenience feature that sits at the edge of this scope. They don't build URLs, parse formats, or interact with OGC specifications — they provide TypeScript DX on top of the existing format parser's output.

### 5.5 E2E Write Operations Report (`e2e-write-operations-report.md`)

**Finding #5** references the same area:

> *"Part 2 resources (datastreams, observations, controlStreams, commands) are not GeoJSON Features and don't have a `featureType` property. The `extractCSAPIFeature()` and `getCSAPIResourceType()` functions only work for Part 1 resources."*

**Assessment:** The type guards would only apply to Part 1 resources (the 4-type union). Part 2 resources are already excluded from `extractCSAPIFeature()`. This is consistent — the guards would narrow within the Part 1 resource set only.

### 5.6 AI Operational Constraints (`AI_OPERATIONAL_CONSTRAINTS.md`)

**Section 2.2** — *"Do not introduce new abstractions, layers, or dependencies without approval."*

Type guards are new exported functions — they are new abstractions in the library's public API. Unlike `Pick<>` (a built-in TypeScript utility applied to an existing type annotation), type guards are hand-written functions with runtime behavior that consumers would import and depend on.

**Section 2.2** also states: *"Preserve upstream structure, naming, and patterns unless explicitly instructed otherwise."*

The upstream library has zero type guard exports. Adding 4 would introduce a pattern not present anywhere in the existing codebase.

**Section 2.2** further states: *"Prefer minimal diffs over idealized rewrites."*

The current code is correct. The issue describes a convenience improvement, not a correctness fix. "Minimal diffs" would mean leaving the correct return type as-is.

**Assessment:** Section 2.2 is triggered on multiple criteria. This does not mean the change is categorically wrong — it means it requires explicit approval per the constraints.

### 5.7 Other Documents Reviewed

| Document | Location | Relevance to Issue #13 |
|----------|----------|----------------------|
| [endpoint-error-isolation-report.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/endpoint-error-isolation-report.md) | ogc-csapi-explorer | Not relevant — covers EndpointError refactoring |
| [library-source-changes-audit.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/library-source-changes-audit.md) | ogc-csapi-explorer | Context — confirms only 1 non-CSAPI commit exists (EndpointError extraction); adding type guards would increase the PR surface |
| [conformance-bypass-architecture-notes.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/conformance-bypass-architecture-notes.md) | ogc-csapi-explorer | Not relevant — covers demo app architecture |
| [crud-smoke-test-findings.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/crud-smoke-test-findings.md) | ogc-csapi-explorer | Not relevant — covers CRUD smoke testing |
| [e2e-cross-server-report.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/e2e-cross-server-report.md) | ogc-csapi-explorer | Not relevant — covers cross-server interoperability |
| [schema-display-findings.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/schema-display-findings.md) | ogc-csapi-explorer | Not relevant — covers SWE Common schema display |

---

## 6. Risk Assessment

| Risk Category | Level | Rationale |
|---------------|-------|-----------|
| **Regression risk** | **None** | Purely additive — no existing code paths are modified |
| **Backward compatibility** | **Full** | New exports don't break existing consumers |
| **Runtime impact** | **Negligible** | Guards would call existing `getCSAPIResourceType()` — no new classification logic |
| **Test impact** | **Additive** | New tests required for 4 new functions (~100-200 lines) |
| **Type safety impact** | **Positive** | Eliminates `as any` casts for consumers who adopt the guards |
| **Scope creep risk** | **Medium** | Adds 4 new exports to a contribution already under review; increases PR reviewer burden |
| **Upstream acceptance risk** | **Medium-High** | No upstream precedent for type guard exports; may invite reviewer questions about why CSAPI needs helpers other modules don't |
| **Maintenance burden** | **Low-Medium** | 4 simple functions with stable semantics, but each is a public API commitment in perpetuity |
| **AI Constraints compliance** | **Triggered** | Section 2.2 applies — new exported functions are new abstractions; no upstream pattern precedent |
| **Diff size impact** | **Medium** | ~40-60 lines in geojson.ts + ~4 lines in index.ts + ~100-200 lines of tests = ~150-270 total new lines |
| **CSAPI contribution coherence** | **Questionable** | The contribution is primarily a URL builder with format parsers. Type guards are a consumer DX layer on top. |

---

## 7. Analysis: Type Guard Functions

### 7.1 What the Issue Proposes

The issue proposes 4 type guard functions:

```typescript
export function isSystem(resource: CSAPIFeature): resource is System {
  return resource.featureType !== undefined &&
    getCSAPIResourceType({ properties: resource } as unknown) === 'System';
}
```

(Similarly for `isDeployment`, `isProcedure`, and `isSamplingFeature`.)

### 7.2 What Already Exists

The library already exports `getCSAPIResourceType()`, which provides the exact same classification. A consumer can already write:

```typescript
const resource = extractCSAPIFeature(feature);
const type = getCSAPIResourceType(feature);

if (type === 'System') {
  // Narrow manually
  const system = resource as System;
  console.log(system.properties.systemType);
}
```

This is 1-2 extra lines compared to:

```typescript
if (isSystem(resource)) {
  console.log(resource.properties.systemType);
}
```

The difference is that TypeScript automatically narrows the type with `is` predicates, saving the manual `as System` cast. The cast is safe here because `getCSAPIResourceType()` has already verified the type.

### 7.3 The Upstream Precedent Problem

The strongest argument against this change is the **absence of precedent**. Consider the parallel situations in the existing library:

- **WMS handler** — returns layer objects with varying capability sets. No type guards exported.
- **WFS handler** — returns feature type descriptions with varying properties. No type guards exported.
- **STAC handler** — returns items, collections, and catalogs with different structures. No type guards exported.
- **EDR handler** — returns environmental data resources. No type guards exported.

None of these modules export `isFoo()` type predicates. Consumers of these modules narrow types using standard TypeScript patterns (property checks, string comparisons, explicit casts). The library has consistently left type narrowing as a consumer responsibility.

Adding type guards only to the CSAPI module would:
1. Create an asymmetry in the library's API surface
2. Invite reviewer questions: "Why does CSAPI need these when no other module does?"
3. Set a precedent that may pressure other modules to add similar helpers
4. Suggest the CSAPI contribution is opinionated about consumer patterns in a way the rest of the library is not

### 7.4 The Issue's Internal Inconsistency

The issue's proposed implementation wraps `getCSAPIResourceType()`:

```typescript
export function isSystem(resource: CSAPIFeature): resource is System {
  return resource.featureType !== undefined &&
    getCSAPIResourceType({ properties: resource } as unknown) === 'System';
}
```

This creates an awkward layering: the type guard takes a `CSAPIFeature` (an unwrapped properties object?) but `getCSAPIResourceType()` expects a full GeoJSON Feature (with `properties` wrapper). The issue's code reconstructs the wrapping: `{ properties: resource } as unknown`. This is fragile and suggests the abstraction doesn't map cleanly onto the existing API.

A cleaner implementation would operate on the full GeoJSON Feature (the same input to `extractCSAPIFeature()`), but then the guard's input type would be `System | Deployment | Procedure | SamplingFeature` — *which is the output of `extractCSAPIFeature()`*, meaning the Feature has already been parsed. At that point, the `featureType` string in `properties.featureType` is the discriminator, and a simple string comparison suffices:

```typescript
// Consumer can already do this — no library helper needed:
if (resource.properties.featureType.startsWith('http://www.w3.org/ns/sosa/Sensor')) {
  const system = resource as System;
}
```

Or more robustly:

```typescript
const type = getCSAPIResourceType(originalFeature);
if (type === 'System') { ... }
```

### 7.5 Who Benefits?

The friction described in the issue is specifically the demo app's Vue template pattern:

```html
<span v-if="(typedResource.properties as any)?.validTime">
  {{ (typedResource.properties as any).validTime.start.toISOString() }}
</span>
```

This is a consumer integration concern specific to Vue's template type narrowing limitations. The library cannot solve all consumer framework type-narrowing challenges with exported guards.

Consider: a React consumer using `typedResource.properties.validTime` would face the same issue. An Angular consumer might face a different variant. The fundamental issue is that the consumer has a union type and needs to narrow it — which is a standard TypeScript problem with well-known solutions that don't require library-side helpers.

### 7.6 Alternative: Consumer-Side Type Guards

Any consumer can define their own type guards in 4 lines:

```typescript
import type { System, Deployment, Procedure, SamplingFeature } from 'ogc-client';
import { getCSAPIResourceType } from 'ogc-client';

type CSAPIFeature = System | Deployment | Procedure | SamplingFeature;

function isSystem(feature: CSAPIFeature): feature is System {
  return getCSAPIResourceType(feature) === 'System';
}
```

The library already exports everything needed for a consumer to write this. The question is whether this 4-line pattern should live in the library or in the consumer's codebase. Given the upstream precedent (no other module does this), the answer leans toward the consumer.

### 7.7 What Would Change the Assessment

This assessment would shift if:

1. **Upstream reviewers request it** — If during PR review, upstream maintainers ask for type guards, they should absolutely be added. At that point it becomes an upstream requirement, not a contribution-side addition.
2. **The library adds a discriminated union** — If `featureType` values were made literal types on each interface (e.g., `featureType: 'http://www.w3.org/ns/sosa/Sensor'` on `System`), TypeScript would auto-narrow without guards. This would be the cleanest solution but requires interface changes across all 4 types.
3. **Multiple consumers independently request it** — If the pattern of needing type guards is repeated across multiple real consumers (not just one demo app), it would justify library-level support.

---

## 8. Recommendation

### 8.1 Assessment: Valid Convenience Feature, Wrong Time to Add

Issue #13 describes a **real TypeScript friction point** that affects consumers of `extractCSAPIFeature()`. The proposed type guards are technically correct and would improve DX. However:

- The library already exports `getCSAPIResourceType()`, which provides the same classification
- The upstream library has zero type guard exports — this would be a first
- The CSAPI contribution is already substantial (~10,000 lines); adding convenience helpers increases reviewer surface
- AI Operational Constraints Section 2.2 is triggered (new exported functions with no upstream precedent)
- The friction is at the consumer level, not the library level — the library's types are correct
- The finding is ranked #9 of 11 — last in the "Should Address" tier

### 8.2 Options

| Option | Pros | Cons |
|--------|------|------|
| **A. Do NOT add type guards** | Maintains upstream convention; minimal PR surface; no new API commitment; AI Constraints compliant | Consumer friction persists (mitigated by existing `getCSAPIResourceType()`) |
| **B. Add type guards now** | Eliminates `as any` casts; improves consumer DX; straightforward implementation | No upstream precedent; increases PR scope; new API surface; Section 2.2 triggered |
| **C. Defer to follow-up PR** | Separates core contribution from DX enhancements; can await upstream feedback | Delays the convenience improvement |
| **D. Add as internal JSDoc example** | Documents the consumer-side pattern without adding API surface | No auto-narrowing benefit |

### 8.3 Recommended Path: Option A (Do NOT Add Type Guards)

**Do not include type guard functions in the CSAPI upstream contribution at this time.**

Rationale:
1. **The library's type system is correct.** The union return type accurately reflects what `extractCSAPIFeature()` can produce. The TypeScript compiler is doing its job.
2. **The existing API already provides the building blocks.** `getCSAPIResourceType()` returns a discriminator string that consumers can use for narrowing. The library does not need to provide the narrowing wrapper.
3. **Zero upstream precedent.** No other module in the library exports type guards. Adding them only to CSAPI creates an asymmetry that upstream reviewers will notice and question.
4. **Minimal diffs preference.** AI Operational Constraints Section 2.2 explicitly prefers minimal diffs. Adding ~150-270 lines of new code for a convenience feature is the opposite of minimal.
5. **Consumer-solvable.** Any consumer can write their own type guards in 4 lines using the already-exported `getCSAPIResourceType()` function. This is standard TypeScript practice.
6. **Risk-benefit ratio.** The benefit (fewer cast lines in consumer code) does not outweigh the risk (upstream PR scope creep, reviewer pushback, new maintenance commitment, precedent setting).
7. **Can be added later.** If upstream reviewers request type guards during PR review, they can be trivially added at that point. Removing them is harder than adding them.

### 8.4 What COULD Be Done Instead (Optional, Low-Risk)

If any improvement is desired, consider adding a **JSDoc `@example`** to `extractCSAPIFeature()` that demonstrates the consumer-side narrowing pattern:

```typescript
/**
 * @example Type narrowing with getCSAPIResourceType()
 * ```typescript
 * const resource = extractCSAPIFeature(feature);
 * const type = getCSAPIResourceType(feature);
 * if (type === 'System') {
 *   const system = resource as System;
 *   console.log(system.properties.validTime);
 * }
 * ```
 */
```

This is zero-risk (documentation only), requires no new exports, and directly addresses the consumer friction by showing the recommended narrowing pattern. It is within scope as documentation improvement (Issue #8 on the explorer repo already covers JSDoc for `extractCSAPIFeature()`).

### 8.5 What NOT to Do

- **Do NOT add `validTime?: TimeInterval` to `Procedure.properties`** — This misrepresents the OGC spec. Procedures do not have validity time periods. Adding a phantom property to satisfy a TypeScript convenience use case is incorrect modeling.
- **Do NOT create a new `type-guards.ts` file** — If type guards were to be added (Option B), they should go in `geojson.ts` alongside the functions they narrow. A separate file would add another module to maintain.
- **Do NOT modify `extractCSAPIFeature()`'s return type** — The union type is correct. Overloading it or changing it to a discriminated union would be a larger change with broader implications.

---

## Appendix A: Authority Precedence Analysis

| Authority Level | Source | Says About This Change | Weight |
|----------------|--------|----------------------|--------|
| 1 (Highest) | OGC specifications | Silent — specs define resource semantics, not TypeScript type guards | N/A |
| 2 | AI Operational Constraints | Section 2.2: "Do not introduce new abstractions... without approval" — **triggered** (4 new exported functions). "Preserve upstream structure, naming, and patterns" — **no upstream pattern exists** for type guards. "Prefer minimal diffs" — **150-270 new lines is not minimal**. | **Against** |
| 3 | Issue description | Clearly defines the problem and proposes type guards | Scoping |
| 4 | Existing code patterns | Zero type guard exports anywhere in the upstream library. `getCSAPIResourceType()` already provides the classification logic. | **Against** (the library pattern is to let consumers narrow) |
| 5 | Reference documents | F-9 priority #9 "Should Address" (Low effort, Medium severity) — lowest priority in that tier | Supportive but low priority |

**Precedence conclusion:** Authority levels 2 and 4 both weigh against adding type guards. The AI Operational Constraints (level 2) explicitly flag this as requiring approval. The existing codebase patterns (level 4) have no precedent for type guard exports. Only the issue description (level 3) and reference documents (level 5) support the change, and even the references rank it at the lowest priority.

---

## Appendix B: Cross-Reference Matrix

| Document | Location | Relevance to Issue #13 |
|----------|----------|-----------------------|
| [upstream-findings.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/upstream-findings.md) | ogc-csapi-explorer | F-9 definition; priority #9; Category 2 "Library Design Improvements (Should Address)" — lowest ranked in tier |
| [library-integration-report.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/library-integration-report.md) | ogc-csapi-explorer | Library Finding #10 — where F-9 was first identified; documents `as any` friction in ResourceDetail; suggests 2 fix options |
| [library-findings-gap-analysis.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/library-findings-gap-analysis.md) | ogc-csapi-explorer | F-9 actionability: "type guards", Low effort, priority 5 (Medium) |
| [contribution-goal-accuracy-assessment.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/contribution-goal-accuracy-assessment.md) | ogc-csapi-explorer | Confirms the library is a URL builder; type guards extend beyond core scope |
| [e2e-write-operations-report.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/e2e-write-operations-report.md) | ogc-csapi-explorer | Finding #5 — confirms `extractCSAPIFeature()` is Part 1 only; aligns with type guard scope |
| [AI_OPERATIONAL_CONSTRAINTS.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/governance/AI_OPERATIONAL_CONSTRAINTS.md) | ogc-client-CSAPI_2 | Section 2.2 triggered on 3 criteria: new abstractions, no upstream pattern, minimal diffs preference |
| [endpoint-error-isolation-report.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/endpoint-error-isolation-report.md) | ogc-csapi-explorer | Not relevant — covers EndpointError refactoring |
| [library-source-changes-audit.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/library-source-changes-audit.md) | ogc-csapi-explorer | Context — confirms minimal non-CSAPI changes; adding type guards increases upstream diff |
| [conformance-bypass-architecture-notes.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/conformance-bypass-architecture-notes.md) | ogc-csapi-explorer | Not relevant — covers demo app conformance architecture |
| [crud-smoke-test-findings.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/crud-smoke-test-findings.md) | ogc-csapi-explorer | Not relevant — covers CRUD smoke testing |
| [e2e-cross-server-report.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/e2e-cross-server-report.md) | ogc-csapi-explorer | Not relevant — covers cross-server interoperability |
| [schema-display-findings.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/schema-display-findings.md) | ogc-csapi-explorer | Not relevant — covers SWE Common schema display |

---

## Conclusion

Issue #13 identifies a real TypeScript ergonomics friction with the `extractCSAPIFeature()` union return type. The proposed type guard functions (`isSystem()`, `isDeployment()`, `isProcedure()`, `isSamplingFeature()`) are technically correct and would improve consumer DX.

However, **this report recommends against including them in the CSAPI upstream contribution** because:

1. **The library's types are correct** — the union type accurately models the OGC spec. The friction is at the consumer integration layer, not the library layer.
2. **The classification function already exists** — `getCSAPIResourceType()` is exported and provides the exact discriminator consumers need. Type guards would be a 4-line convenience wrapper.
3. **No upstream precedent** — the library has zero type guard exports across all modules (WMS, WFS, WMTS, STAC, EDR). Adding them only to CSAPI creates an asymmetry.
4. **AI Operational Constraints Section 2.2 is triggered** — new exported functions with runtime behavior are new abstractions, and the upstream codebase does not establish this pattern.
5. **The fix is consumer-solvable** — any consumer can write their own type guards in 4 lines using already-exported library functions.
6. **Risk to contribution integrity** — adding convenience helpers increases PR scope and reviewer burden for minimal payoff, at a time when the contribution should be focused on correctness and completeness, not DX ornaments.

**If upstream reviewers request type guards during PR review, they should absolutely be added.** The implementation is trivial. But proactively adding them risks scope creep and diverges from the library's established conventions.

**Recommended action: No changes to the library at this time.** Optionally, add a JSDoc `@example` to `extractCSAPIFeature()` demonstrating the consumer-side narrowing pattern with `getCSAPIResourceType()`.
