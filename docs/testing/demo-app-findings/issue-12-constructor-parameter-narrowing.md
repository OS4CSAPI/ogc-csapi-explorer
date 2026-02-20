# Issue #12 Findings Report — Narrow CSAPIQueryBuilder constructor parameter to only required fields (F-8)

> **Date:** 2026-02-17
> **Issue:** [OS4CSAPI/ogc-csapi-explorer#12](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/12) — "Narrow CSAPIQueryBuilder constructor parameter to only required fields (F-8)"
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
7. [Analysis: Constructor Parameter Narrowing](#7-analysis-constructor-parameter-narrowing)
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

**Key constraint assessment for this issue:** Section 2.2 of the AI Operational Constraints states: *"Do not introduce new abstractions, layers, or dependencies without approval."* Issue #12 proposes narrowing an existing parameter type using TypeScript's built-in `Pick<>` utility. This does **not** introduce a new abstraction, layer, or dependency — it tightens an existing type signature. Section 2.2 is **not triggered** by this change. However, Section 2.2 also states: *"Prefer minimal diffs over idealized rewrites."* This is relevant — the change should be minimal and targeted.

---

## 2. Executive Summary

**Issue #12 proposes narrowing the `CSAPIQueryBuilder` constructor's `collection_` parameter from the full `OgcApiCollectionInfo` interface (25+ fields) to `Pick<OgcApiCollectionInfo, 'id' | 'title' | 'links'>` (3 fields). This is a type-only change with zero behavioral impact that improves the library's API ergonomics for consumers who construct builders outside of `OgcApiEndpoint`.**

| Aspect | Assessment |
|--------|------------|
| **Change type** | Type signature narrowing — no behavioral change |
| **Scope** | 1 line in `url_builder.ts` (constructor parameter type annotation) |
| **Production behavior modified** | **No** — zero runtime impact; the constructor's logic does not change |
| **Existing tests affected** | **None** — all existing tests pass without modification (they pass full `OgcApiCollectionInfo` objects, which satisfy the narrower type) |
| **Risk to library integrity** | **None** — fully backward-compatible; `OgcApiCollectionInfo` is a supertype of `Pick<OgcApiCollectionInfo, 'id' | 'title' | 'links'>`, so existing callers compile without change |
| **New abstraction introduced** | **No** — uses TypeScript's built-in `Pick<>` utility type, not a new interface |
| **Upstream pattern precedent** | **Positive** — narrowing parameter types is standard TypeScript practice; no upstream module requires broader types than it uses |
| **AI Constraints trigger** | **No** — Section 2.2 ("no new abstractions") does not apply to type narrowing |
| **Priority ranking** | #8 in upstream-findings.md (Medium severity, Low effort) — "Should Address" category |

**Key findings from this review:**

1. **Fact:** The `CSAPIQueryBuilder` constructor accesses only **2 fields** of the `collection_` parameter: `id` (L273, in error messages) and `links` (L139and L176, for base URL extraction and resource discovery). The field `title` is **never accessed** anywhere in `url_builder.ts`, contrary to the issue description's claim.

2. **Fact:** The library's own factory method in `endpoint.ts` (L405-407) already uses a double cast — `collectionDoc as unknown as OgcApiCollectionInfo` — to force a raw collection document into the `OgcApiCollectionInfo` type. Narrowing the constructor parameter would eliminate this unsafe cast.

3. **Fact:** The test helper `makeCollection()` in `url_builder.spec.ts` (L8-28) provides 13 dummy required field values (`description: ''`, `itemFormats: []`, `bulkDownloadLinks: {}`, etc.) solely to satisfy the `OgcApiCollectionInfo` type. Every integration test file has its own copy of this pattern.

4. **Fact:** `Pick<OgcApiCollectionInfo, 'id' | 'title' | 'links'>` is fully backward-compatible. TypeScript's structural typing means any value of type `OgcApiCollectionInfo` also satisfies `Pick<OgcApiCollectionInfo, 'id' | 'title' | 'links'>`. No existing caller would break.

5. **Fact (correction to issue):** The issue states `title` is "used in some error messages." This is **incorrect** — `title` is not accessed anywhere in `url_builder.ts`. Only `id` appears in the error message at L273. The technically minimal `Pick<>` could be `Pick<OgcApiCollectionInfo, 'id' | 'links'>`, but including `title` is harmless and future-proofs the type if error messages are enhanced later.

6. **Inference:** This change is strictly positive: it improves consumer DX, eliminates unsafe casts in the library's own code, simplifies test helpers, and has zero risk. It is the lowest-risk change among all open findings.

---

## 3. Issue Description

### 3.1 Origin: Finding F-8

Issue #12 corresponds to **Finding F-8** from the [upstream findings document](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/upstream-findings.md). It was first identified as **Library Finding #3** in the [library integration report](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/library-integration-report.md) during the bridge module's synthetic collection construction.

### 3.2 The Problem

The `CSAPIQueryBuilder` constructor signature:

```typescript
constructor(
  private collection_: OgcApiCollectionInfo,
  resourceUrls?: Map<string, string>
)
```

`OgcApiCollectionInfo` is a large interface from `src/ogc-api/model.ts` (L85-135) with 20+ fields, most of which are required:

```typescript
export interface OgcApiCollectionInfo {
  links: any;
  title: string;
  description: string;           // ← never used by CSAPIQueryBuilder
  id: string;
  itemType?: 'feature' | 'record';
  itemFormats: MimeType[];       // ← never used
  bulkDownloadLinks: Record<string, MimeType>; // ← never used
  jsonDownloadLink: string;      // ← never used
  crs: CrsCode[];                // ← never used
  storageCrs?: CrsCode;
  itemCount: number;             // ← never used
  keywords?: string[];
  language?: string;
  updated?: Date;
  extent?: BoundingBox;
  publisher?: { ... };
  license?: string;
  queryables: CollectionParameter[]; // ← never used
  sortables: CollectionParameter[];  // ← never used
  mapTileFormats: MimeType[];    // ← never used
  vectorTileFormats: MimeType[]; // ← never used
  supportedTileMatrixSets: string[]; // ← never used
  data_queries?: { ... };
  parameter_names?: Record<string, EdrParameterInfo>;
}
```

The constructor only accesses `id` and `links`. All other fields are carried as dead weight in the type signature.

### 3.3 The Proposed Solution (Option A from the Issue)

```typescript
constructor(
  private collection_: Pick<OgcApiCollectionInfo, 'id' | 'title' | 'links'>,
  resourceUrls?: Map<string, string>
)
```

This allows consumers to pass minimal objects:

```typescript
// ✅ Clean and type-safe — no dummy values or casts
const builder = new CSAPIQueryBuilder({
  id: 'my-collection',
  title: 'My Collection',
  links: [...],
});
```

### 3.4 Why This Matters for Consumers

The issue identifies three consumer categories affected:

1. **Proxy/gateway architectures** — Consumers who construct builders directly (without `OgcApiEndpoint`) because they route requests through a proxy. The demo app's bridge module is a concrete example.
2. **Testing** — Test files must construct full `OgcApiCollectionInfo` objects with 13+ dummy fields. Every CSAPI test file has its own `makeCollection()` helper.
3. **The library itself** — `endpoint.ts` L405-407 uses `as unknown as OgcApiCollectionInfo` to force a raw collection document into the type, because `getCollectionDocument()` returns an untyped document, not a parsed `OgcApiCollectionInfo`.

---

## 4. Source Code Review

### 4.1 `url_builder.ts` — Constructor (L121-128)

```typescript
constructor(
  private collection_: OgcApiCollectionInfo,
  resourceUrls?: Map<string, string>
) {
  this.resourceUrls_ = resourceUrls ?? new Map();
  this.baseUrl = this.extractBaseUrl();
  this.availableResources = this.extractAvailableResources();
}
```

**Assessment:** The constructor stores `collection_` as a private field and calls two private methods. Those methods are the only code paths that access `collection_`.

### 4.2 `url_builder.ts` — `extractBaseUrl()` (L138-156)

```typescript
private extractBaseUrl(): string {
  const links = this.collection_.links;       // ← only uses .links
  if (!Array.isArray(links) || links.length === 0) {
    return '';
  }
  const selfLink = links.find(
    (l: { rel?: string; href?: string }) => l.rel === 'self'
  );
  if (selfLink?.href) {
    return selfLink.href.replace(/\/$/, '');
  }
  const first = links.find(
    (l: { href?: string }) => typeof l.href === 'string'
  );
  return first?.href?.replace(/\/$/, '') ?? '';
}
```

**Assessment:** Only accesses `this.collection_.links`. Does not use `id`, `title`, or any other field.

### 4.3 `url_builder.ts` — `extractAvailableResources()` (L175-181)

```typescript
private extractAvailableResources(): Set<string> {
  const links = this.collection_.links;       // ← only uses .links
  if (!Array.isArray(links)) {
    return new Set<string>();
  }
  return new Set(scanCsapiLinks(links).keys());
}
```

**Assessment:** Only accesses `this.collection_.links`. Same as `extractBaseUrl()`.

### 4.4 `url_builder.ts` — `assertResourceAvailable()` (L270-277)

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

**Assessment:** Accesses `this.collection_.id` in the error message string. This is the only usage of `id` in the entire file.

### 4.5 Complete `collection_` Usage Inventory

| Location | Field Accessed | Purpose |
|----------|---------------|---------|
| L139 (`extractBaseUrl`) | `.links` | Scans for `self` link to determine base URL |
| L176 (`extractAvailableResources`) | `.links` | Passes to `scanCsapiLinks()` for resource discovery |
| L273 (`assertResourceAvailable`) | `.id` | Error message: "Collection '{id}' does not support..." |

**Total fields actually accessed: 2** (`id` and `links`). The field `title` is **never accessed**.

### 4.6 `endpoint.ts` — Factory Method (L385-410)

```typescript
public async csapi(collectionId: string): Promise<CSAPIQueryBuilder> {
  // ...
  const collectionDoc = await this.getCollectionDocument(collectionId);
  const resourceUrls = await this.extractRootResourceUrls();
  const result = new CSAPIQueryBuilder(
    collectionDoc as unknown as OgcApiCollectionInfo,  // ← double cast!
    resourceUrls
  );
  cache.set(collectionId, result);
  return result;
}
```

**Assessment:** The double cast (`as unknown as OgcApiCollectionInfo`) proves the current type is too broad. `getCollectionDocument()` returns a raw JSON document that has `id`, `title`, and `links` (plus other fields), but is not typed as `OgcApiCollectionInfo`. The double cast bypasses TypeScript's type safety entirely. Narrowing the constructor parameter would allow a single safe cast or none at all.

### 4.7 `url_builder.spec.ts` — Test Helper (L1-28)

```typescript
function makeCollection(
  overrides: Partial<OgcApiCollectionInfo> = {}
): OgcApiCollectionInfo {
  return {
    links: [],
    title: 'Test Collection',
    description: 'A test collection',  // ← dummy
    id: 'test-collection',
    itemFormats: [],                    // ← dummy
    bulkDownloadLinks: {},              // ← dummy
    jsonDownloadLink: '',               // ← dummy
    crs: [],                            // ← dummy
    itemCount: 0,                       // ← dummy
    queryables: [],                     // ← dummy
    sortables: [],                      // ← dummy
    mapTileFormats: [],                 // ← dummy
    vectorTileFormats: [],              // ← dummy
    supportedTileMatrixSets: [],        // ← dummy
    ...overrides,
  };
}
```

**Assessment:** 10 of the 13 fields provided are dummy values that exist solely to satisfy the `OgcApiCollectionInfo` type. This pattern is repeated in 5 additional test files (`command-routing.spec.ts`, and 4 files under `integration/`). With the narrowed type, all these helpers could be simplified to `{ id, title, links, ...overrides }`.

---

## 5. Reference Document Review

All 12 linked reference documents from the ogc-csapi-explorer repository were reviewed. The following are directly relevant to Issue #12:

### 5.1 Upstream Findings (`upstream-findings.md`)

Finding **F-8** is defined here:

> *"`CSAPIQueryBuilder`'s constructor requires an `OgcApiCollectionInfo` object (from `src/ogc-api/model.ts`), which is a large interface with many fields (`id`, `title`, `links`, `extent`, etc.). The constructor only uses `id`, `title`, and `links`."*
>
> Priority rank: **#8** (Medium severity, Low effort)

F-8 is categorized under **Category 2: Library Design Improvements (Should Address)** — notably NOT Category 1 (Must Fix). The recommended solution matches the issue: *"Accept `Pick<OgcApiCollectionInfo, 'id' | 'title' | 'links'>` or create a dedicated `CSAPIBuilderOptions` interface."*

**Note:** The upstream findings document (and the issue) incorrectly state that `title` is used. Source code review confirms only `id` and `links` are accessed.

### 5.2 Library Integration Report (`library-integration-report.md`)

**Library Finding #3** is where F-8 was first identified:

> *"The `OgcApiCollectionInfo` type (from `src/ogc-api/model.ts`) is a large interface with many required fields. [...] The `CSAPIQueryBuilder` only actually uses `id`, `title`, and `links`. We had to cast our minimal object with `as OgcApiCollectionInfo` to satisfy the type system."*

The report documents the synthetic collection pattern used in the bridge module — constructing a minimal object with only the needed fields and using `as OgcApiCollectionInfo` to bypass TypeScript. This is the exact consumer friction that Issue #12 would eliminate.

### 5.3 Library Findings Gap Analysis (`library-findings-gap-analysis.md`)

F-8 actionability assessment:

| Finding | Actionable? | Effort | Priority |
|---------|------------|--------|----------|
| F-8 | Yes — type narrowing | Low | 5 (Medium) |

The document notes: *"Would clean up the synthetic collection creation code slightly. No visible UI change."*

### 5.4 E2E Write Operations Report (`e2e-write-operations-report.md`)

The test environment section documents the same pattern:

> *"Construct a synthetic `OgcApiCollectionInfo` with resource links"*

This confirms the synthetic collection workaround is used across multiple test artifacts, not just the demo app.

### 5.5 Contribution Goal Accuracy Assessment (`contribution-goal-accuracy-assessment.md`)

Confirms the library is a URL builder, not an HTTP client. The constructor's type broadness is an API design concern, not a specification compliance issue. The assessment validates that narrowing the type is within the library's design improvement scope.

### 5.6 AI Operational Constraints (`AI_OPERATIONAL_CONSTRAINTS.md`)

**Section 2.2** — *"Do not introduce new abstractions, layers, or dependencies without approval."*

The `Pick<>` approach does **not** introduce a new abstraction. It uses TypeScript's built-in utility type to narrow an existing parameter. No new interfaces, classes, or modules are created. This constraint is **not triggered**.

**Section 2.2** also states: *"Prefer minimal diffs over idealized rewrites."*

This is relevant. The change is exactly 1 line modified (the constructor parameter type annotation). This is the minimal possible diff for the improvement. Option B from the issue (creating a new `CSAPIBuilderOptions` interface) and Option C (union type) would both increase the diff surface unnecessarily.

### 5.7 Other Documents Reviewed

| Document | Location | Relevance to Issue #12 |
|----------|----------|----------------------|
| [endpoint-error-isolation-report.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/endpoint-error-isolation-report.md) | ogc-csapi-explorer | Not relevant — covers EndpointError refactoring |
| [library-source-changes-audit.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/library-source-changes-audit.md) | ogc-csapi-explorer | Context — the upstream PR diff is documented; a 1-line type change adds negligible surface |
| [conformance-bypass-architecture-notes.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/conformance-bypass-architecture-notes.md) | ogc-csapi-explorer | Not relevant — covers demo app architecture |
| [crud-smoke-test-findings.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/crud-smoke-test-findings.md) | ogc-csapi-explorer | Not relevant — covers CRUD smoke testing |
| [e2e-cross-server-report.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/e2e-cross-server-report.md) | ogc-csapi-explorer | Not relevant — covers cross-server interoperability |
| [schema-display-findings.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/schema-display-findings.md) | ogc-csapi-explorer | Not relevant — covers SWE Common schema display |

---

## 6. Risk Assessment

| Risk Category | Level | Rationale |
|---------------|-------|-----------|
| **Regression risk** | **None** | No behavioral change; no existing code paths are modified |
| **Backward compatibility** | **Full** | `OgcApiCollectionInfo` satisfies `Pick<OgcApiCollectionInfo, 'id' | 'title' | 'links'>` via structural typing — existing callers compile without change |
| **Runtime impact** | **None** | TypeScript types are erased at compile time; zero runtime effect |
| **Test impact** | **None** | Existing tests pass unmodified. Test helpers _could_ be simplified but do not _need_ to be changed. |
| **Type safety impact** | **Positive** | Current code forces double casts (`as unknown as OgcApiCollectionInfo` in `endpoint.ts`). Narrowing the parameter type eliminates the need for unsafe casts. |
| **Scope creep** | **None** | 1-line change; no new modules, interfaces, or abstractions |
| **Upstream acceptance** | **High likelihood** | Narrowing parameter types is a standard TypeScript best practice. No upstream reviewer would object to accepting a subtype where only a subset of fields is used. |
| **CSAPI contribution impact** | **Positive** | Improves the API's developer experience with zero cost |
| **Diff size impact** | **Negligible** | 1 line modified in `url_builder.ts`. Optional: simplify test helpers (~10 lines each across 6 files), but this is not required. |
| **AI Constraints compliance** | **Compliant** | Section 2.2 does not apply (no new abstraction). Section 2.1 is satisfied (within issue scope). Section 2.2 preference for "minimal diffs" is satisfied (1 line). |

---

## 7. Analysis: Constructor Parameter Narrowing

### 7.1 The Three Options from the Issue

| Option | Approach | Pros | Cons |
|--------|----------|------|------|
| **A (preferred)** | `Pick<OgcApiCollectionInfo, 'id' \| 'title' \| 'links'>` | 1-line change; uses built-in utility type; fully backward-compatible; no new type to learn | Includes `title` even though it's not used (harmless) |
| **B** | New `CSAPIBuilderOptions` interface | Explicit; self-documenting | Creates a new type consumers must discover; 2+ files modified; violates "prefer minimal diffs" |
| **C** | Union: `OgcApiCollectionInfo \| CSAPIBuilderOptions` | Supports both patterns explicitly | Requires Option B's new interface; adds union complexity; `private collection_` field type is the union, requiring type guards internally |

### 7.2 Why Option A Is Correct

1. **Minimal diff** — 1 line changed, satisfying AI Constraints Section 2.2.
2. **No new types** — `Pick<>` is a built-in TypeScript utility, not a custom abstraction.
3. **Fully backward-compatible** — Every existing caller passes `OgcApiCollectionInfo`, which structurally satisfies `Pick<OgcApiCollectionInfo, 'id' | 'title' | 'links'>`.
4. **Eliminates unsafe casts** — `endpoint.ts` can drop the `as unknown as OgcApiCollectionInfo` double cast.
5. **Simplifies tests** — Test helpers can optionally be reduced from 13+ dummy fields to 3.
6. **Standard practice** — TypeScript's `Pick<>` is the idiomatic way to express "I only use these fields."

### 7.3 The `title` Question

The issue proposes including `title` in the `Pick<>`. Source code review shows `title` is **not accessed** anywhere in `url_builder.ts`. The minimal accurate `Pick<>` would be `Pick<OgcApiCollectionInfo, 'id' | 'links'>`.

However, including `title` is the **conservative** choice:

- **Future-proofing:** If error messages are enhanced to include the collection title (a reasonable improvement), the type would already support it.
- **Self-documentation:** `id`, `title`, and `links` are the three fields that semantically identify a collection. Including all three communicates intent even if one is currently unused.
- **No cost:** Including an unused optional field in a `Pick<>` has zero runtime or type-safety impact.

**Recommendation: Include `title` as the issue proposes.** The marginal cost is zero, and it avoids a second type change if title usage is added later.

### 7.4 Impact on `endpoint.ts`

The current factory method in `endpoint.ts` (L405-407):

```typescript
const result = new CSAPIQueryBuilder(
  collectionDoc as unknown as OgcApiCollectionInfo,  // ← unsafe double cast
  resourceUrls
);
```

After narrowing the constructor parameter, this could become:

```typescript
const result = new CSAPIQueryBuilder(
  collectionDoc as Pick<OgcApiCollectionInfo, 'id' | 'title' | 'links'>,  // ← single safe cast
  resourceUrls
);
```

Or, if the raw document has `id`, `title`, and `links` properties (which it does for any valid OGC API collection document), the cast could potentially be eliminated entirely, depending on the return type of `getCollectionDocument()`.

**Note:** Modifying `endpoint.ts` is outside the scope of this findings report (the issue only targets `url_builder.ts`). This is mentioned for completeness.

### 7.5 Impact on Test Files

The `makeCollection()` helper pattern exists in 6 test files:

| File | Helper Location |
|------|----------------|
| `url_builder.spec.ts` | L8-28 |
| `command-routing.spec.ts` | L27-32 |
| `integration/command.spec.ts` | L34-35 |
| `integration/discovery.spec.ts` | L38-39 |
| `integration/navigation.spec.ts` | L49-50 |
| `integration/observation.spec.ts` | L27-28 |

After the type narrowing, these helpers could optionally be simplified from:

```typescript
function makeCollection(overrides = {}): OgcApiCollectionInfo {
  return {
    links: [], title: 'Test', description: '', id: 'test',
    itemFormats: [], bulkDownloadLinks: {}, jsonDownloadLink: '',
    crs: [], itemCount: 0, queryables: [], sortables: [],
    mapTileFormats: [], vectorTileFormats: [], supportedTileMatrixSets: [],
    ...overrides,
  };
}
```

To:

```typescript
function makeCollection(overrides = {}) {
  return { links: [], title: 'Test', id: 'test', ...overrides };
}
```

**However, this simplification is optional.** The existing test helpers pass more data than needed, which is harmless. Simplifying them is a nice-to-have that reduces test boilerplate but is not required for the type change to work.

---

## 8. Recommendation

### 8.1 Assessment: Low-Risk, High-Value Type Improvement

Issue #12 describes the **lowest-risk, highest-certainty improvement** among all open findings. The analysis is unambiguous:

- The constructor uses 2 of 25+ fields → the type should reflect this.
- The change is 1 line → minimal diff.
- Backward compatibility is guaranteed by TypeScript's structural typing → no breakage.
- The library's own code already works around the overly broad type with double casts → the problem is real and internal.
- No new abstractions are introduced → AI Constraints Section 2.2 does not apply.

### 8.2 Options

| Option | Pros | Cons |
|--------|------|------|
| **A. Include in CSAPI PR** | Improves API ergonomics; eliminates unsafe cast in `endpoint.ts`; 1-line diff; fully backward-compatible | None identified |
| **B. Defer to follow-up PR** | Keeps initial PR unchanged | Leaves an unsafe double cast in `endpoint.ts`; consumers continue needing dummy values or type assertions |

### 8.3 Recommended Path: Option A (Include in CSAPI PR)

**This change should be included in the initial CSAPI upstream PR.**

Rationale:
- The diff is 1 line — it adds negligible reviewer burden.
- It **improves** the library's own code quality by eliminating a double cast in `endpoint.ts`.
- It improves consumer DX with zero risk.
- Unlike Issue #11 (generic CRUD methods), this does not introduce a new abstraction or establish a new API pattern. It is a type correction — the existing type was broader than necessary.
- It is the kind of change an upstream reviewer would flag themselves during PR review: *"Why does the constructor require `OgcApiCollectionInfo` when it only uses 2 fields?"*

### 8.4 Proposed Implementation (1-Line Change)

In `src/ogc-api/csapi/url_builder.ts`, change the constructor signature from:

```typescript
constructor(
  private collection_: OgcApiCollectionInfo,
  resourceUrls?: Map<string, string>
)
```

To:

```typescript
constructor(
  private collection_: Pick<OgcApiCollectionInfo, 'id' | 'title' | 'links'>,
  resourceUrls?: Map<string, string>
)
```

**No other changes are required** for the type narrowing to take effect. Test helpers and `endpoint.ts` can optionally be simplified but do not need to change.

### 8.5 What NOT to Do

- **Do NOT create a new `CSAPIBuilderOptions` interface** (Option B from the issue) — it adds unnecessary surface area and violates the "minimal diffs" preference.
- **Do NOT use a union type** (Option C from the issue) — it adds complexity to the internal `collection_` field type for no benefit.
- **Do NOT modify test helpers as part of this change** — they work correctly as-is. Simplifying them is a separate, optional cleanup.
- **Do NOT modify `endpoint.ts` as part of this change** — the double cast there can be addressed separately. The type narrowing in `url_builder.ts` makes the cast-reduction possible but does not require it.

---

## Appendix A: Authority Precedence Analysis

| Authority Level | Source | Says About This Change | Weight |
|----------------|--------|----------------------|--------|
| 1 (Highest) | OGC specifications | Silent — specs define resource semantics, not TypeScript type signatures | N/A |
| 2 | AI Operational Constraints | Section 2.2: "Prefer minimal diffs over idealized rewrites" — **supports Option A** (1-line change). "Do not introduce new abstractions" — **not triggered** (no new abstraction). | Supportive |
| 2 | AI Operational Constraints | Section 2.1: "Do not expand scope beyond the issue description" — the proposed change matches the issue exactly. | Compliant |
| 3 | Issue description | Clearly defines the problem, three options, and recommends Option A (`Pick<>`) | Scoping |
| 4 | Existing code patterns | `endpoint.ts` already uses `as unknown as OgcApiCollectionInfo` — proving the type is too broad even for the library's own use | Strongly supportive |
| 5 | Reference documents | F-8 priority #8 "Should Address" (Low effort, Medium severity); Library Finding #3 documents the consumer friction | Supportive |

---

## Appendix B: Cross-Reference Matrix

| Document | Location | Relevance to Issue #12 |
|----------|----------|-----------------------|
| [upstream-findings.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/upstream-findings.md) | ogc-csapi-explorer | F-8 definition; priority #8; Category 2 "Library Design Improvements (Should Address)" |
| [library-integration-report.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/library-integration-report.md) | ogc-csapi-explorer | Library Finding #3 — where F-8 was first identified during the synthetic collection workaround; documents `as OgcApiCollectionInfo` cast |
| [library-findings-gap-analysis.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/library-findings-gap-analysis.md) | ogc-csapi-explorer | F-8 actionability: "type narrowing", Low effort, priority 5 |
| [contribution-goal-accuracy-assessment.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/contribution-goal-accuracy-assessment.md) | ogc-csapi-explorer | Confirms the library is a URL builder; type narrowing is within design improvement scope |
| [library-source-changes-audit.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/library-source-changes-audit.md) | ogc-csapi-explorer | Context: a 1-line type change adds negligible diff surface to the upstream PR |
| [e2e-write-operations-report.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/e2e-write-operations-report.md) | ogc-csapi-explorer | Documents the synthetic collection constructor pattern used in E2E tests |
| [endpoint-error-isolation-report.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/endpoint-error-isolation-report.md) | ogc-csapi-explorer | Not relevant — covers EndpointError refactoring |
| [conformance-bypass-architecture-notes.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/conformance-bypass-architecture-notes.md) | ogc-csapi-explorer | Not relevant — covers demo app conformance architecture |
| [crud-smoke-test-findings.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/crud-smoke-test-findings.md) | ogc-csapi-explorer | Not relevant — covers CRUD smoke testing |
| [e2e-cross-server-report.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/e2e-cross-server-report.md) | ogc-csapi-explorer | Not relevant — covers cross-server interoperability |
| [schema-display-findings.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/schema-display-findings.md) | ogc-csapi-explorer | Not relevant — covers SWE Common schema display |
| [AI_OPERATIONAL_CONSTRAINTS.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/governance/AI_OPERATIONAL_CONSTRAINTS.md) | ogc-client-CSAPI_2 | Section 2.2 not triggered (no new abstraction); "minimal diffs" preference supports Option A |

---

## Conclusion

Issue #12 describes a straightforward, low-risk type improvement to the `CSAPIQueryBuilder` constructor. The constructor requires 25+ fields via `OgcApiCollectionInfo` but accesses only 2 (`id` and `links`). The proposed `Pick<OgcApiCollectionInfo, 'id' | 'title' | 'links'>` narrowing is:

- **Correct** — the constructor does not use the other fields.
- **Backward-compatible** — existing callers pass full `OgcApiCollectionInfo` objects, which satisfy the narrower type.
- **Minimal** — 1-line change, no new interfaces or abstractions.
- **Internally beneficial** — eliminates the `as unknown as OgcApiCollectionInfo` double cast in the library's own `endpoint.ts` factory method.
- **Consumer-friendly** — proxy architectures, gateway scenarios, and tests no longer need dummy values or type assertions.

**One correction to the issue:** `title` is not accessed by the constructor or any method in `url_builder.ts`. Only `id` and `links` are used. The `Pick<>` could technically be `Pick<OgcApiCollectionInfo, 'id' | 'links'>`, but including `title` is the conservative, future-proof choice at zero cost.

**Recommendation: Include this 1-line type change in the initial CSAPI upstream PR.** It is the lowest-risk improvement in the entire findings inventory and improves both the library's internal code quality and its external API ergonomics.
