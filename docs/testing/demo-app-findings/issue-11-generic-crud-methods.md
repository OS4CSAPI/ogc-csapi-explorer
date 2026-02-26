# Issue #11 Findings Report — Add generic CRUD methods for dynamic-type consumers (F-7)

> **Date:** 2026-02-17
> **Issue:** [OS4CSAPI/ogc-csapi-explorer#11](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/11) — "Add generic CRUD methods for dynamic-type consumers (F-7)"
> **Repository under review:** `OS4CSAPI/ogc-client-CSAPI_2` (`src/ogc-api/csapi/url_builder.ts`)
> **Labels:** enhancement

---

## Table of Contents

1. [AI Operational Constraints Acknowledgment](#1-ai-operational-constraints-acknowledgment)
2. [Executive Summary](#2-executive-summary)
3. [Issue Description](#3-issue-description)
4. [Source Code Review](#4-source-code-review)
5. [Reference Document Review](#5-reference-document-review)
6. [Risk Assessment](#6-risk-assessment)
7. [Analysis: Generic CRUD Methods vs. Type-Specific Methods](#7-analysis-generic-crud-methods-vs-type-specific-methods)
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

**Critical constraint for this issue:** Section 2.2 of the AI Operational Constraints states: _"Do not introduce new abstractions, layers, or dependencies without approval."_ Issue #11 proposes adding a new abstraction layer (generic CRUD dispatch methods). This constraint is directly applicable and is central to this report's analysis.

---

## 2. Executive Summary

**Issue #11 proposes adding 5 generic CRUD methods (`getResources()`, `getResource()`, `createResource()`, `updateResource()`, `deleteResource()`) to `CSAPIQueryBuilder`. This is a legitimate developer-experience (DX) enhancement that would reduce consumer boilerplate, but it introduces a new abstraction layer that requires careful evaluation against the AI Operational Constraints, the upstream library's design patterns, and the CSAPI contribution scope.**

| Aspect                           | Assessment                                                                                                                                                    |
| -------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Change type**                  | Enhancement — new public API surface on `CSAPIQueryBuilder`                                                                                                   |
| **Scope**                        | 5 new public methods in `url_builder.ts`, corresponding tests in `url_builder.spec.ts`                                                                        |
| **Production behavior modified** | No — existing methods are untouched; these are purely additive                                                                                                |
| **Existing tests affected**      | None — all existing 298 tests remain unchanged                                                                                                                |
| **Risk to library integrity**    | **Low** — additive-only, delegates to existing `buildResourceUrl()` private method                                                                            |
| **New abstraction introduced**   | **Yes** — a generic dispatch layer over 77+ type-specific methods                                                                                             |
| **Upstream pattern precedent**   | **None** — no equivalent generic dispatch exists in the upstream `ogc-client` library (EDR, WFS, WMS, WMTS modules all use type-specific methods exclusively) |
| **AI Constraints trigger**       | **Yes** — Section 2.2: "Do not introduce new abstractions, layers, or dependencies without approval"                                                          |
| **Priority ranking**             | #7 in upstream-findings.md (Medium severity, Medium effort) — "Should Address" category                                                                       |

**Key findings from this review:**

1. **Fact:** The `CSAPIQueryBuilder` has 77+ type-specific public methods (e.g., `getSystems()`, `getDeployment(id)`, `createSystem()`). Each calls `assertResourceAvailable()` then `buildResourceUrl()` with type-specific parameters.

2. **Fact:** The demo app's bridge module (`csapi-bridge.ts`) required 5 switch/case dispatchers — one each for list, detail, create, update, delete — each with 9 cases, totaling ~45 lines of boilerplate. This is the primary evidence motivating the enhancement.

3. **Fact:** The proposed generic methods would lose type-specific query option types. For example, `getSystems()` accepts `SystemQueryOptions` (with `parent`, `procedureId`, etc.), while a generic `getResources('systems', options)` would only accept `QueryOptions` (the base type without type-specific filters).

4. **Fact:** No other module in the upstream `ogc-client` library provides generic dispatch methods. The EDR module has endpoint-type-specific methods (`getCoverage()`, `getPosition()`, etc.) without a generic `getData(type)` equivalent.

5. **Inference:** The boilerplate described in the issue is a **consumer-side concern**, not a library deficiency. The type-specific API design is intentional and provides TypeScript type safety that a generic method cannot.

6. **Inference:** The proposed generic methods are a convenience for one specific usage pattern (dynamic-type UIs). Static-type consumers — the majority use case for a TypeScript library — gain nothing from generic methods and lose type safety if they adopt them.

---

## 3. Issue Description

### 3.1 Origin: Finding F-7

Issue #11 corresponds to **Finding F-7** from the [upstream findings document](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/upstream-findings.md). It was first identified as **Library Finding #2** in the [library integration report](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/library-integration-report.md) during the demo app bridge module creation.

### 3.2 The Problem

The `CSAPIQueryBuilder` provides 77+ type-specific methods but no generic dispatch. A consumer working with resource types determined at runtime (e.g., a UI dropdown selecting "systems" vs. "deployments") must write switch/case dispatchers:

```typescript
function getListUrl(type: string, options: QueryOptions): string {
  switch (type) {
    case 'systems':
      return builder.getSystems(options as SystemQueryOptions);
    case 'deployments':
      return builder.getDeployments(options as DeploymentQueryOptions);
    case 'procedures':
      return builder.getProcedures(options as ProcedureQueryOptions);
    case 'samplingFeatures':
      return builder.getSamplingFeatures(
        options as SamplingFeatureQueryOptions
      );
    case 'properties':
      return builder.getProperties(options as PropertyQueryOptions);
    case 'datastreams':
      return builder.getDataStreams(options as DataStreamQueryOptions);
    case 'observations':
      return builder.getObservations(options as ObservationQueryOptions);
    case 'controlStreams':
      return builder.getControlStreams(options as ControlStreamQueryOptions);
    case 'commands':
      return builder.getCommands(options as CommandQueryOptions);
    default:
      return `/${type}`;
  }
}
```

This pattern was repeated 5 times in the demo app's bridge module (list, detail, create, update, delete).

### 3.3 The Proposal

Add 5 generic methods to `CSAPIQueryBuilder`:

| Method             | Signature                                                               | Delegates To                                            |
| ------------------ | ----------------------------------------------------------------------- | ------------------------------------------------------- |
| `getResources()`   | `(type: CSAPIResourceType, options?: QueryOptions): string`             | `buildResourceUrl(type, undefined, undefined, options)` |
| `getResource()`    | `(type: CSAPIResourceType, id: string, options?: QueryOptions): string` | `buildResourceUrl(type, id, undefined, options)`        |
| `createResource()` | `(type: CSAPIResourceType): string`                                     | `buildResourceUrl(type)`                                |
| `updateResource()` | `(type: CSAPIResourceType, id: string): string`                         | `buildResourceUrl(type, id)`                            |
| `deleteResource()` | `(type: CSAPIResourceType, id: string): string`                         | `buildResourceUrl(type, id)`                            |

Each method would call `assertResourceAvailable(type)` first, then delegate to the existing `buildResourceUrl()` private method — the same core helper that all 77+ existing methods use.

### 3.4 What Is Lost

The generic methods accept `QueryOptions` (the base interface), not type-specific options like `SystemQueryOptions`. This means:

- `getSystems({ parent: 'urn:...' })` would still work (type-safe, compile-time checked)
- `getResources('systems', { parent: 'urn:...' })` would **not** compile — `parent` is not in `QueryOptions`
- Consumers needing type-specific filters must continue using the type-specific methods

---

## 4. Source Code Review

### 4.1 `url_builder.ts` — The `buildResourceUrl()` Private Method (L199-216)

```typescript
private buildResourceUrl(
  resourceType: string,
  id?: string,
  subPath?: string,
  options?: QueryOptions
): string {
  const topLevelUrl = this.resourceUrls_.get(resourceType);
  const resourceBase = topLevelUrl
    ? topLevelUrl.replace(/\/+$/, '')
    : `${this.baseUrl}/${resourceType}`;
  let url = resourceBase;
  if (id) url += `/${encodeResourceId(id)}`;
  if (subPath) url += `/${subPath}`;
  return url + this.buildQueryString(options);
}
```

**Assessment:** This method already accepts a generic `resourceType: string` parameter. It does not validate the resource type against `CSAPIResourceTypes` — that validation happens in `assertResourceAvailable()`. The proposed generic methods would be thin wrappers: `assertResourceAvailable(type)` + `buildResourceUrl(type, ...)`.

### 4.2 `url_builder.ts` — `assertResourceAvailable()` (L270-277)

```typescript
private assertResourceAvailable(resourceType: string): void {
  if (!this.availableResources.has(resourceType)) {
    throw new EndpointError(
      `Collection '${this.collection_.id}' does not support '${resourceType}' resource. ` +
        `Available resources: ${Array.from(this.availableResources).join(', ')}`
    );
  }
}
```

**Assessment:** Also accepts generic `string`. The proposed methods would use `CSAPIResourceType` as the parameter type, which is a union of the 9 string literals — providing compile-time validation that `assertResourceAvailable()` does not.

### 4.3 `url_builder.ts` — Representative Type-Specific Method Pattern (L298-301)

```typescript
getSystems(options?: SystemQueryOptions): string {
  this.assertResourceAvailable('systems');
  return this.buildResourceUrl('systems', undefined, undefined, options);
}
```

**Assessment:** Every type-specific method follows this exact pattern: assert availability, call `buildResourceUrl()`. The proposed generic methods would replicate this pattern but with a dynamic resource type parameter instead of a hardcoded string.

### 4.4 `model.ts` — `CSAPIResourceType` (L32-43)

```typescript
export const CSAPIResourceTypes = [
  'systems',
  'deployments',
  'samplingFeatures',
  'procedures',
  'properties',
  'datastreams',
  'observations',
  'controlStreams',
  'commands',
] as const;

export type CSAPIResourceType = (typeof CSAPIResourceTypes)[number];
```

**Assessment:** The type union already exists and would enforce compile-time validation in the generic methods. This is good — it prevents consumers from passing arbitrary strings like `getResources('invalid')`.

### 4.5 What the Generic Methods Would NOT Cover

The type-specific API surface includes methods that go beyond simple CRUD:

| Method Category | Example                           | Generic Equivalent?                              |
| --------------- | --------------------------------- | ------------------------------------------------ |
| Nested listings | `getSystemDataStreams(systemId)`  | **No** — requires subPath knowledge              |
| Nested creation | `createObservation(datastreamId)` | **No** — requires parent resource type knowledge |
| History         | `getSystemHistory(systemId)`      | **No** — requires subPath `'history'`            |
| Sub-hierarchies | `getSystemSubsystems(systemId)`   | **No** — requires subPath `'subsystems'`         |

The proposed 5 generic methods only cover the **flat CRUD** operations (list all, get by ID, create at collection level, update by ID, delete by ID). They do not replace the nested/relational methods.

---

## 5. Reference Document Review

All 12 linked reference documents from the ogc-csapi-explorer repository were reviewed. The following are directly relevant to Issue #11:

### 5.1 Upstream Findings (`upstream-findings.md`)

Finding **F-7** is defined here:

> _"The library provides 77+ type-specific methods [...] but no generic method like `getResources(type, options)` or `getResource(type, id)`. [...] Our bridge module required this pattern for list, detail, create, update, and delete — five dispatchers."_
>
> Priority rank: **#7** (Medium severity, Medium effort)

F-7 is categorized under **Category 2: Library Design Improvements (Should Address)** — notably NOT Category 1 (Must Fix). This is an improvement, not a bug.

### 5.2 Library Integration Report (`library-integration-report.md`)

**Library Finding #2** is where this was first identified:

> _"The `CSAPIQueryBuilder` has 77+ type-specific methods [...] but no generic method. [...] any consumer that works with dynamic resource types (like our explorer) must write a switch/case dispatcher over all 9 types."_

The report acknowledges both sides:

- **Pro:** _"Type-specific methods give excellent TypeScript type safety."_
- **Con:** _"Any UI framework, CLI tool, or admin panel that needs to work with resource types dynamically will need the same boilerplate dispatcher."_

The recommendation: _"Consider adding `getResources(type: CSAPIResourceType, options?: QueryOptions)` convenience method alongside the type-specific methods."_

### 5.3 Library Findings Gap Analysis (`library-findings-gap-analysis.md`)

F-7 actionability assessment:

| Finding | Actionable?          | Effort | Priority   |
| ------- | -------------------- | ------ | ---------- |
| F-7     | Yes — DX improvement | Medium | 5 (Medium) |

This document ranks F-7 at priority **5** (Medium), lower than its ranking of **7** in upstream-findings.md. Both agree it is medium priority.

### 5.4 AI Operational Constraints (`AI_OPERATIONAL_CONSTRAINTS.md`)

**Section 2.2** is directly applicable:

> _"Do not introduce new abstractions, layers, or dependencies without approval."_

The generic CRUD methods constitute a new abstraction layer — a dispatch mechanism over the existing type-specific methods. While the implementation is simple (thin wrappers), the API design decision is significant: it establishes a precedent that the library should provide both type-specific and generic access patterns.

**Section 2.1** is also relevant:

> _"Do not expand scope beyond the issue description."_

The issue description focuses on 5 specific methods with clear signatures. However, the issue itself may represent scope expansion relative to the core CSAPI contribution goal (which is to provide a well-typed URL builder for Connected Systems API resources).

### 5.5 Other Documents Reviewed

| Document                                                                                                                                                       | Location           | Relevance to Issue #11                                                                  |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------ | --------------------------------------------------------------------------------------- |
| [endpoint-error-isolation-report.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/endpoint-error-isolation-report.md)             | ogc-csapi-explorer | Not relevant — covers EndpointError refactoring                                         |
| [contribution-goal-accuracy-assessment.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/contribution-goal-accuracy-assessment.md) | ogc-csapi-explorer | Peripheral — validates library's URL builder role; generic methods expand that role     |
| [library-source-changes-audit.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/library-source-changes-audit.md)                   | ogc-csapi-explorer | Context — adding 5 new methods increases the diff surface of the upstream PR            |
| [conformance-bypass-architecture-notes.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/conformance-bypass-architecture-notes.md) | ogc-csapi-explorer | Not relevant — covers demo app architecture                                             |
| [crud-smoke-test-findings.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/crud-smoke-test-findings.md)                           | ogc-csapi-explorer | Peripheral — the smoke test uses the bridge dispatchers that F-7 would make unnecessary |
| [e2e-cross-server-report.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/e2e-cross-server-report.md)                             | ogc-csapi-explorer | Not relevant — covers cross-server interoperability                                     |
| [e2e-write-operations-report.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/e2e-write-operations-report.md)                     | ogc-csapi-explorer | Not relevant — covers write operations                                                  |
| [schema-display-findings.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/schema-display-findings.md)                             | ogc-csapi-explorer | Not relevant — covers SWE Common schema display                                         |

---

## 6. Risk Assessment

| Risk Category                 | Level                 | Rationale                                                                                                                                                                                                                       |
| ----------------------------- | --------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Regression risk**           | **None**              | Additive-only; no existing methods are modified                                                                                                                                                                                 |
| **Behavioral impact**         | **None**              | Existing API surface is unchanged; new methods are supplementary                                                                                                                                                                |
| **Type safety erosion**       | **Low-Medium**        | Consumers who adopt generic methods lose access to type-specific query options (`SystemQueryOptions.parent`, `DataStreamQueryOptions.phenomenonTime`, etc.). This may lead to `as any` casts or runtime query parameter errors. |
| **Scope creep**               | **Medium**            | Introduces a new abstraction pattern not present elsewhere in `ogc-client`. If accepted, consumers may expect similar generic methods in future modules.                                                                        |
| **Upstream acceptance**       | **Uncertain**         | The upstream maintainers may prefer the strict type-specific API design. Adding generic dispatch methods could be seen as weakening the library's type safety guarantees.                                                       |
| **CSAPI contribution impact** | **Low**               | The methods are additive and do not modify the existing CSAPI code. However, they expand the PR's surface area.                                                                                                                 |
| **Diff size impact**          | **Medium**            | ~50 lines for 5 methods + ~100 lines for tests = ~150 additional lines in the upstream PR                                                                                                                                       |
| **AI Constraints compliance** | **Requires approval** | Section 2.2 explicitly requires approval for "new abstractions, layers, or dependencies"                                                                                                                                        |

### 6.1 The Precedent Problem

No other module in the upstream `ogc-client` library provides generic dispatch:

| Module                      | Type-Specific Methods                                                                           | Generic Dispatch?         |
| --------------------------- | ----------------------------------------------------------------------------------------------- | ------------------------- |
| EDR (`EdrEndpoint`)         | `getCoverage()`, `getPosition()`, `getArea()`, `getCube()`, `getTrajectory()`, `getLocations()` | No                        |
| WFS (`WfsEndpoint`)         | `getFeature()`, `getFeatureUrl()`                                                               | No (single resource type) |
| WMS (`WmsEndpoint`)         | `getMapUrl()`, `getFeatureInfoUrl()`                                                            | No                        |
| WMTS (`WmtsEndpoint`)       | `getTileUrl()`                                                                                  | No                        |
| CSAPI (`CSAPIQueryBuilder`) | 77+ methods across 9 resource types                                                             | **Proposed in F-7**       |

Introducing a generic dispatch layer in CSAPI would be the first instance of this pattern in the library. This is not inherently wrong, but it does establish a precedent that the upstream maintainers should evaluate.

---

## 7. Analysis: Generic CRUD Methods vs. Type-Specific Methods

### 7.1 The Core Trade-off

| Dimension                 | Type-Specific Methods (Current)                             | Generic Methods (Proposed)                                      |
| ------------------------- | ----------------------------------------------------------- | --------------------------------------------------------------- |
| **Type safety**           | Full — `SystemQueryOptions`, `DeploymentQueryOptions`, etc. | Reduced — only `QueryOptions` base type                         |
| **IDE autocomplete**      | Discoverable — `builder.get…` shows all options             | Less discoverable — requires knowing `CSAPIResourceType` values |
| **Dynamic-type UIs**      | Requires switch/case dispatcher                             | Direct dispatch: `builder.getResources(type)`                   |
| **Static-type consumers** | Perfect fit — know the type at compile time                 | No benefit; loss of type specificity                            |
| **API surface area**      | 77+ methods (larger surface, higher discoverability)        | 5 additional methods (minimal surface expansion)                |
| **Maintenance burden**    | None — already exists                                       | Low — thin wrappers over `buildResourceUrl()`                   |

### 7.2 Who Benefits?

**Consumers who benefit from generic methods:**

- Dynamic-type UIs (admin panels, explorers, dashboards) that iterate over resource types
- CLI tools that accept resource type as a command argument
- Generic CRUD frameworks that work with arbitrary resource types
- Test harnesses that iterate over all resource types

**Consumers who do NOT benefit:**

- Application code that knows the resource type at compile time (e.g., `builder.getSystems()`)
- Type-safe integrations that need type-specific query options
- Code that works with nested/relational resources (subsystems, datastreams under systems, etc.)

### 7.3 Is the Boilerplate Actually a Problem?

The 45 lines of switch/case boilerplate in the demo app's bridge module is real. However:

1. **It is written once** — The dispatcher is in a single bridge module, not scattered across the codebase.
2. **It is type-safe** — Each case explicitly casts to the correct options type, providing documentation of which types accept which options.
3. **It is complete** — A switch/case over all 9 types with a default fallback handles all cases, including future resource types that the library might not yet support.
4. **It is a consumer-side concern** — The library provides the building blocks; the consumer composes them for its specific usage pattern.

The boilerplate could also be eliminated **without library changes** by creating a consumer-side utility:

```typescript
// Consumer-side generic dispatcher (no library change needed)
const methods = {
  systems: (o?: QueryOptions) => builder.getSystems(o as SystemQueryOptions),
  deployments: (o?: QueryOptions) =>
    builder.getDeployments(o as DeploymentQueryOptions),
  // ... etc.
};

function getResources(type: CSAPIResourceType, options?: QueryOptions): string {
  return methods[type](options);
}
```

This keeps the generic dispatch in the consumer where the type information is lost, rather than embedding it in the library where it weakens the typed API.

### 7.4 Architectural Consideration: Thin Wrappers vs. Real Abstraction

The proposed methods are extremely thin:

```typescript
getResources(type: CSAPIResourceType, options?: QueryOptions): string {
  this.assertResourceAvailable(type);
  return this.buildResourceUrl(type, undefined, undefined, options);
}
```

This adds no new logic — it is literally `assertResourceAvailable()` + `buildResourceUrl()`, which is what every type-specific method already does. The only difference is that the resource type is a parameter instead of a constant.

**Positive:** If the implementation is this thin, there is minimal risk of behavioral divergence between generic and type-specific methods.

**Negative:** If the implementation is this thin, why should the library provide it? The consumer can trivially construct the same dispatch.

---

## 8. Recommendation

### 8.1 Assessment: Legitimate Enhancement, Requires Approval

Issue #11 describes a **legitimate DX improvement**. The boilerplate is real, the proposed solution is sound, and the implementation is low-risk. However:

1. **The AI Operational Constraints (Section 2.2) explicitly require approval** for "new abstractions, layers, or dependencies." This is a new abstraction layer.
2. **No upstream precedent exists** for generic dispatch methods in any `ogc-client` module.
3. **The priority is medium** (#7 in upstream-findings.md), categorized as "Should Address" not "Must Fix."
4. **The enhancement is consumer-convenience**, not correctness. The library is not broken without it.

### 8.2 Options

| Option                                       | Pros                                                                                                            | Cons                                                                                               |
| -------------------------------------------- | --------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| **A. Include in CSAPI PR**                   | Reduces consumer boilerplate; one-time implementation; additive-only                                            | New abstraction; no upstream precedent; increases PR surface; requires approval per AI constraints |
| **B. Defer to a follow-up PR**               | Keeps initial PR focused on core functionality (URL building, types, parsers); smaller diff for upstream review | Enhancement remains unaddressed; consumers write boilerplate                                       |
| **C. Leave as consumer-side concern**        | Zero library changes; consumers implement their own dispatch; type safety preserved                             | Each dynamic-type consumer reinvents the same pattern                                              |
| **D. Propose to upstream maintainers first** | Gets buy-in before implementation; respects that this is an API design decision                                 | Delays implementation; may be rejected                                                             |

### 8.3 Recommended Path: Option B (Defer) or Option D (Propose First)

**Primary recommendation: Defer to a follow-up PR (Option B).**

Rationale:

- The initial CSAPI upstream PR should focus on the core contribution: URL builder, type model, parsers, and bug fixes (F-1 through F-5). This is already a substantial PR (~4,000 lines of library code + tests).
- Adding a new API pattern (generic dispatch) to the initial PR increases reviewer burden and the risk of the PR being rejected or requiring significant revisions.
- The generic methods can be added later once the core CSAPI module is accepted upstream and the maintainers have had a chance to assess the API design.

**Alternative recommendation: Propose to upstream maintainers first (Option D).**

If the user believes this enhancement is important for the initial submission, it should be proposed to the upstream maintainers (e.g., via a GitHub Discussion or issue on `camptocamp/ogc-client`) before implementation. The maintainers may have opinions on whether generic dispatch belongs in the library or is a consumer-side concern.

### 8.4 What NOT to Do

- **Do NOT implement this enhancement without explicit approval** — Section 2.2 of the AI Operational Constraints applies directly.
- **Do NOT modify existing type-specific methods** — They are correct and well-typed. The generic methods must be additive-only.
- **Do NOT add generic methods for nested/relational operations** — The issue scope is limited to flat CRUD (list, detail, create, update, delete). Nested operations (subsystems, datastreams under systems, history) have parent-resource requirements that a generic method cannot safely abstract.
- **Do NOT remove or deprecate type-specific methods** — The generic methods would be supplements, not replacements.

---

## Appendix A: Authority Precedence Analysis

| Authority Level | Source                     | Says About This Enhancement                                                                                                                                        | Weight                    |
| --------------- | -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------- |
| 1 (Highest)     | OGC specifications         | Silent — specs define resource types and operations, not library API design patterns                                                                               | N/A                       |
| 2               | AI Operational Constraints | Section 2.2: "Do not introduce new abstractions, layers, or dependencies without approval" — **directly applicable**                                               | Blocking without approval |
| 2               | AI Operational Constraints | Section 2.1: "Do not expand scope beyond the issue description" — the issue describes the enhancement clearly, but is the issue itself within the project's scope? | Cautionary                |
| 3               | Issue description          | Clearly defines 5 methods with signatures and rationale                                                                                                            | Scoping                   |
| 4               | Existing code patterns     | No upstream module uses generic dispatch; all modules use type-specific methods exclusively                                                                        | Against precedent         |
| 5               | Reference documents        | upstream-findings.md: F-7, priority #7, "Should Address"; library-integration-report.md: Finding #2, acknowledges trade-off                                        | Supportive (with caveats) |

---

## Appendix B: Cross-Reference Matrix

| Document                                                                                                                                                       | Location           | Relevance to Issue #11                                                                                                         |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------ | ------------------------------------------------------------------------------------------------------------------------------ |
| [upstream-findings.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/upstream-findings.md)                                                     | ogc-csapi-explorer | F-7 definition; priority #7; Category 2 "Library Design Improvements (Should Address)"                                         |
| [library-integration-report.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/library-integration-report.md)                       | ogc-csapi-explorer | Library Finding #2 — where F-7 was first identified during bridge module creation; documents the boilerplate and the trade-off |
| [library-findings-gap-analysis.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/library-findings-gap-analysis.md)                 | ogc-csapi-explorer | F-7 actionability: "DX improvement", Medium effort, priority 5                                                                 |
| [contribution-goal-accuracy-assessment.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/contribution-goal-accuracy-assessment.md) | ogc-csapi-explorer | Validates the library's URL builder role; generic methods expand that role                                                     |
| [library-source-changes-audit.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/library-source-changes-audit.md)                   | ogc-csapi-explorer | Context: adding 5 new methods increases diff surface of the upstream PR                                                        |
| [endpoint-error-isolation-report.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/endpoint-error-isolation-report.md)             | ogc-csapi-explorer | Not relevant — covers EndpointError refactoring                                                                                |
| [conformance-bypass-architecture-notes.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/conformance-bypass-architecture-notes.md) | ogc-csapi-explorer | Not relevant — covers demo app conformance architecture                                                                        |
| [crud-smoke-test-findings.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/crud-smoke-test-findings.md)                           | ogc-csapi-explorer | Peripheral — smoke test uses bridge dispatchers that F-7 would make unnecessary                                                |
| [e2e-cross-server-report.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/e2e-cross-server-report.md)                             | ogc-csapi-explorer | Not relevant — covers cross-server interoperability                                                                            |
| [e2e-write-operations-report.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/e2e-write-operations-report.md)                     | ogc-csapi-explorer | Not relevant — covers write operations                                                                                         |
| [schema-display-findings.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/schema-display-findings.md)                             | ogc-csapi-explorer | Not relevant — covers SWE Common schema display                                                                                |
| [AI_OPERATIONAL_CONSTRAINTS.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/governance/AI_OPERATIONAL_CONSTRAINTS.md)                        | ogc-client-CSAPI_2 | Directly applicable — Section 2.2 requires approval for new abstractions                                                       |

---

## Conclusion

Issue #11 describes a real DX friction point — dynamic-type consumers of `CSAPIQueryBuilder` must write repetitive switch/case dispatchers because the library only provides type-specific methods. The proposed 5 generic CRUD methods are well-defined, low-risk, and additive-only.

However, this is an **enhancement** (Category 2: "Should Address"), not a bug fix. It introduces a new abstraction layer that has **no precedent in the upstream `ogc-client` library**, and the AI Operational Constraints **explicitly require approval** for new abstractions (Section 2.2).

The boilerplate motivating this enhancement:

- Is real (~45 lines in the demo bridge)
- Is written once per consumer (not scattered)
- Can be eliminated consumer-side without library changes
- Is an intentional consequence of the library's strong type-specific API design

**Recommendation: Defer this enhancement to a follow-up PR after the core CSAPI module is accepted upstream.** The initial PR should focus on URL building, type models, parsers, and bug fixes (F-1 through F-5, F-10). If the upstream maintainers express interest in generic dispatch methods during the initial PR review, they can be added incrementally.

If the user decides to proceed with implementation despite the deferral recommendation, the change is straightforward, additive, and low-risk. The 5 methods are thin wrappers over `assertResourceAvailable()` + `buildResourceUrl()`, with corresponding tests that verify delegation and `CSAPIResourceType` enforcement.
