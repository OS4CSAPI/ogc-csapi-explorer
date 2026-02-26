# Issue #9 Findings Report — Default to Accept: application/geo+json for Part 1 Resource Requests

> **Date:** 2026-02-17
> **Issue:** [OS4CSAPI/ogc-csapi-explorer#9](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/9) — "Default to Accept: application/geo+json for Part 1 resource requests (F-4)"
> **Repository under review:** `OS4CSAPI/ogc-client-CSAPI_2` (`src/shared/http-utils.ts`, `src/ogc-api/csapi/`)
> **Dependencies:** Related to Issue #6 (CSAPI_CONTENT_TYPES helper)
> **Labels:** bug, enhancement

---

## Table of Contents

1. [AI Operational Constraints Acknowledgment](#1-ai-operational-constraints-acknowledgment)
2. [Executive Summary](#2-executive-summary)
3. [Issue Description](#3-issue-description)
4. [Source Code Review](#4-source-code-review)
5. [Reference Document Review](#5-reference-document-review)
6. [Risk Assessment](#6-risk-assessment)
7. [Analysis: Architectural Boundaries and Accept Header Placement](#7-analysis-architectural-boundaries-and-accept-header-placement)
8. [Analysis: GET-Only Constraint](#8-analysis-get-only-constraint)
9. [Recommendation](#9-recommendation)
10. [Appendix A: Authority Precedence Analysis](#appendix-a-authority-precedence-analysis)
11. [Appendix B: Cross-Reference Matrix](#appendix-b-cross-reference-matrix)

---

## 1. AI Operational Constraints Acknowledgment

Per the [AI Operational Constraints](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/governance/AI_OPERATIONAL_CONSTRAINTS.md), this review follows the required authority precedence:

1. **OGC specifications** (23-001r1 Part 1, 23-002r1 Part 2) — primary authority
2. **AI Collaboration Agreement** — governing constraints
3. **Issue description** — task scope
4. **Existing code patterns** — implementation precedent
5. **Conversation context** — supplementary guidance

This report does not propose behavioral modifications to the library without approval. All recommendations distinguish between **fact** (verified), **inference** (reasoned), and **proposal** (requires approval), per Section 3 of the constraints.

---

## 2. Executive Summary

**Issue #9 identifies a real and well-documented interoperability problem (F-4, ranked #1 priority across all test reports), but the proposed solution requires careful scoping because it crosses an architectural boundary — the `CSAPIQueryBuilder` is a URL builder, not an HTTP client.**

The core problem: When no `Accept` header is sent (or when `application/json` is used — the library's current default for JSON requests), 52North's CSA server returns empty FeatureCollections for Part 1 resource requests. Only `Accept: application/geo+json` returns populated data from both tested servers (52North and OSH SensorHub).

| Aspect                           | Assessment                                                                                                                                                              |
| -------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Change type**                  | Behavioral — modifies HTTP request headers for Part 1 resource GET requests                                                                                             |
| **Production behavior modified** | Yes — changes what servers receive in the Accept header                                                                                                                 |
| **Existing tests affected**      | Potentially — any test mocking `sharedFetch` with Accept header assertions                                                                                              |
| **Risk to library integrity**    | **Moderate** — behavioral HTTP changes affect all consumers                                                                                                             |
| **Estimated scope**              | Small code change, large behavioral impact surface                                                                                                                      |
| **Dependencies**                 | Related to Issue #6 (CSAPI_CONTENT_TYPES); consumes same Part 1/Part 2 media type mapping                                                                               |
| **GET-only constraint**          | **Critical** — S-8 from CRUD smoke testing confirms OSH SensorHub rejects `Accept: application/geo+json` on POST requests; this default must apply to GET requests only |

**Key findings from this review:**

1. The `CSAPIQueryBuilder` is a **pure URL builder** (2,034 lines, zero HTTP logic). Adding `getAcceptHeader()` to it would expand its architectural scope — contradicting the established pattern and the AI Operational Constraints ("Do not introduce new abstractions, layers, or dependencies without approval").

2. The upstream `sharedFetch()` in `http-utils.ts` **already has** a `customAcceptHeader` parameter. The infrastructure for setting Accept headers already exists; the question is where to place the decision logic.

3. The `MEDIA_TYPE_GEOJSON` constant already exists in `formats/constants.ts`. No new constants are needed.

4. Issue #6's proposed `CSAPI_CONTENT_TYPES` map (for POST/PUT Content-Type) addresses the same Part 1 → `geo+json` / Part 2 → `json` mapping. A companion `CSAPI_ACCEPT_HEADERS` constant (or a unified map serving both purposes) would be the minimal, additive approach consistent with the existing pattern.

5. **S-8** (CRUD smoke test findings) documents that `Accept: application/geo+json` on POST requests **causes network-level failures** on OSH SensorHub. The Accept header default **must be limited to GET requests only**.

---

## 3. Issue Description

### 3.1 Origin: Finding F-4

Issue #9 corresponds to **Finding F-4** from the [upstream findings document](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/upstream-findings.md), which was ranked as the **#1 priority finding** across all integration testing. F-4 identified that the library does not set a default `Accept` header for Part 1 resource requests, causing interoperability failures with servers that respect content negotiation.

### 3.2 Content Negotiation Test Results

The issue documents the following cross-server Accept header behavior:

| Accept Header Value    | OSH SensorHub   | 52North STA                             |
| ---------------------- | --------------- | --------------------------------------- |
| `application/json`     | 5 items (works) | **0 items** (empty FeatureCollection)   |
| `application/sml+json` | 5 items (works) | 3 items (SensorML format)               |
| `application/geo+json` | 5 items (works) | **3 items** (GeoJSON format)            |
| None (browser default) | 5 items         | 3 items (server default, typically SML) |

**Key observation:** `application/geo+json` is the **only** Accept value that returns populated data from both servers. This is consistent with Part 1 of the CSA specification (OGC 23-001r1), which defines Part 1 resources as GeoJSON Features.

### 3.3 What Issue #9 Proposes

1. **Default to `Accept: application/geo+json`** for Part 1 resource GET requests (systems, deployments, procedures, samplingFeatures, properties)
2. **Default to `Accept: application/json`** for Part 2 resource GET requests (datastreams, observations, controlStreams, commands)
3. **Add a `getAcceptHeader(resourceType)` method** alongside URL generation in the builder

### 3.4 Affected Files (per issue)

- `src/shared/http-utils.ts` — upstream HTTP client with existing `customAcceptHeader` parameter
- `src/ogc-api/csapi/url_builder.ts` — the `CSAPIQueryBuilder` class (2,034 lines, pure URL builder)
- `src/ogc-api/csapi/formats/constants.ts` — media type constants (already has `MEDIA_TYPE_GEOJSON`)

---

## 4. Source Code Review

### 4.1 `sharedFetch()` in `http-utils.ts` (L30–100)

The library's HTTP client already supports custom Accept headers:

```typescript
export function sharedFetch(
  url: string,
  method: 'GET' | 'HEAD' = 'GET',
  asJson?: boolean,
  customAcceptHeader?: string
) {
  // ...
  if (customAcceptHeader) {
    options.headers['Accept'] = customAcceptHeader;
  } else if (asJson) {
    options.headers['Accept'] = 'application/json,application/schema+json';
  }
  // ...
}
```

**Assessment:** The `customAcceptHeader` parameter exists and works. When `asJson` is `true` and no custom header is provided, the default is `application/json,application/schema+json`. This is the default that causes 52North to return empty FeatureCollections for Part 1 resources.

**Critical detail:** `sharedFetch` is an **upstream** function used across the entire library (OGC API, STAC, WMS, WFS, WMTS). Changing its default behavior would affect all protocols, not just CSAPI. Any CSAPI-specific Accept header logic must be applied via the `customAcceptHeader` parameter, not by modifying the default.

### 4.2 `CSAPIQueryBuilder` in `url_builder.ts` (L89–200)

The builder class is a pure URL construction utility:

```typescript
export class CSAPIQueryBuilder {
  public readonly availableResources: Set<string>;
  private baseUrl: string;
  private resourceUrls_: Map<string, string>;

  constructor(
    collection_: OgcApiCollectionInfo,
    resourceUrls?: Map<string, string>
  ) {
    /* URL extraction only */
  }

  private extractBaseUrl(): string {
    /* ... */
  }
  private extractAvailableResources(): Set<string> {
    /* ... */
  }
  private buildResourceUrl(
    resourceType: string,
    ...segments: string[]
  ): string {
    /* ... */
  }
}
```

**Assessment:** The builder has **zero HTTP logic** — no `fetch` calls, no header manipulation, no request construction. It takes collection metadata and produces URL strings. Every public method returns `string` (a URL).

Adding `getAcceptHeader(resourceType)` to this class would:

- Expand the class's single responsibility from "URL builder" to "request builder"
- Introduce HTTP concerns into a module that currently has none
- Violate the AI Operational Constraints: "Do not introduce new abstractions, layers, or dependencies without approval"

### 4.3 `formats/constants.ts` (L1–85)

The media type constants already exist:

```typescript
export const MEDIA_TYPE_GEOJSON = 'application/geo+json'; // L27
export const MEDIA_TYPE_JSON = 'application/json'; // L33
export const MEDIA_TYPE_SENSORML_JSON = 'application/sml+json'; // L39
export const MEDIA_TYPE_SWE_JSON = 'application/swe+json'; // L45
// ... (plus SWE_TEXT, SWE_CSV, SWE_BINARY)

export const CSAPI_MEDIA_TYPES = [
  MEDIA_TYPE_GEOJSON,
  MEDIA_TYPE_JSON,
  MEDIA_TYPE_SENSORML_JSON,
  MEDIA_TYPE_SWE_JSON,
  MEDIA_TYPE_SWE_TEXT,
  MEDIA_TYPE_SWE_CSV,
  MEDIA_TYPE_SWE_BINARY,
] as const;
```

**Assessment:** `MEDIA_TYPE_GEOJSON` already exists. No new constants are needed for the Accept header value itself. What's missing is a **mapping** from resource type to appropriate Accept header — the same Part 1/Part 2 mapping that Issue #6 proposes for Content-Type.

### 4.4 Demo app bridge pattern (context from reference documents)

The demo app's bridge module (`csapi-bridge.ts`) **already implements** the Part 1/Part 2 mapping in its own `getContentType()` helper:

```typescript
// From demo bridge module (not library code)
function getContentType(resourceType: string): string {
  const part1 = [
    'systems',
    'deployments',
    'procedures',
    'samplingFeatures',
    'properties',
  ];
  return part1.includes(resourceType)
    ? 'application/geo+json'
    : 'application/json';
}
```

This pattern works correctly in the demo but lives in consumer code, not in the library. Issue #6 proposes moving this pattern into the library as `CSAPI_CONTENT_TYPES`. Issue #9 proposes the same mapping for Accept headers.

---

## 5. Reference Document Review

All 12 linked reference documents from the ogc-csapi-explorer repository were reviewed. Key corroboration for Issue #9:

### 5.1 Upstream Findings

- **F-4** is ranked **#1 priority** in the priority ranking table — the highest-severity finding across all integration testing
- Content Negotiation Appendix documents the full cross-server Accept header matrix (replicated in Section 3.2 above)
- Recommendation: "Use `application/geo+json` as the default Accept header for Part 1 resource requests"
- F-4 is classified under "Category 2: Content Negotiation & HTTP Headers" — distinguishing it from URL/code concerns

### 5.2 Library Findings Gap Analysis

- Maps F-4 to a planned issue (now Issue #9) with: **Severity: High**, **Implementation Risk: Medium**, **Affected Area: Library HTTP layer (Accept header defaults)**
- Gap analysis explicitly states: "The library should use `application/geo+json` as the default Accept header for Part 1 resource requests"
- Notes the dual concern: Accept header (Issue #9) for reads AND Content-Type (Issue #6) for writes use the same Part 1/Part 2 mapping

### 5.3 E2E Cross-Server Report

- **Finding #3** ("Content Negotiation Behavior") — the key empirical evidence for F-4
- Full test matrix with 7 Content-Type / Accept value combinations across 2 servers
- Conclusion: "`application/geo+json` is the most interoperable content type"
- Recommendation #1: "Use `application/geo+json` as default Accept header for Part 1"

### 5.4 Conformance Bypass Architecture Notes

- Documents that the demo bypasses `OgcApiEndpoint` and uses `CSAPIQueryBuilder` directly
- The bridge handles HTTP transport independently — the builder never sees Accept headers
- This confirms the architectural separation: URL building ≠ HTTP transport

### 5.5 Library Integration Report

- **Finding #2:** "No Generic CRUD Method" — the library is a URL builder, not an HTTP client
- **Finding #14:** "No Content-Type Guidance from the Builder" — the bridge's `getContentType()` helper maps Part 1 → geo+json, Part 2 → json; this pattern should be in the library
- Both findings support providing guidance constants rather than embedding HTTP logic in the builder

### 5.6 Contribution Goal Accuracy Assessment

- Key quote: "Content negotiation is guided by the format infrastructure (the `f` query param, the constants) but not performed at the HTTP level"
- Key quote: "detection is comprehensive; 'negotiation' overstates what a URL builder does"
- **Inference:** The assessment explicitly validates that the builder's scope is URL construction, not HTTP negotiation. Accept header guidance should be provided as constants/helpers alongside the builder, not embedded within it.

### 5.7 Library Source Changes Audit

- Confirms exactly 1 commit (`e73cff8`) has modified library source — the EndpointError isolation refactor
- Issue #9's implementation would be the second behavioral change to library source — a significant step requiring careful scoping

### 5.8 CRUD Smoke Test Findings

- **S-8** (critically relevant): "OSH SensorHub: Rejects `Accept: application/geo+json` on POST"
- POST requests with `Accept: application/geo+json` caused **network-level failures** on OSH SensorHub
- The same request with `Accept: application/json` (or no explicit Accept header) succeeded with `201 Created`
- **Impact on Issue #9:** "This default should apply to **GET requests only**, not POST/PUT/DELETE operations where the response is typically empty or status-only"
- This is a **critical scoping constraint** that Issue #9's implementation must respect

### 5.9 E2E Write Operations Report

- **Finding #6:** "Content-Type Mapping Needs Library Guidance" — proposes the same `CSAPI_CONTENT_TYPES` constant map for POST/PUT Content-Type
- Priority 2 recommendation provides the exact constant structure that could serve both Content-Type (Issue #6) and Accept (Issue #9) purposes
- Confirms that the URL builder generates correct URLs; the gap is in HTTP metadata, not URL construction

### 5.10 EndpointError Isolation Report

- Not directly related to Issue #9's Accept header concern
- Documents the only structural refactor to library source (`e73cff8`)
- Confirms `http-utils.ts` has its own XML dependencies — modifying it touches shared library infrastructure

### 5.11 Schema Display Findings

- F-13 documents JSDoc conflation between `f` (response format) and `obsFormat` (schema parameter) — a separate but related content negotiation confusion
- The `f` query parameter is an alternative content negotiation mechanism (URL-based vs. header-based)
- Issue #9 addresses header-based negotiation; `f` parameter handling is a separate concern

### 5.12 AI Operational Constraints

- "Do not expand scope beyond the issue description" — the report must assess what Issue #9 proposes, not invent additional scope
- "Prefer minimal diffs over idealized rewrites" — a constant map is smaller than a new builder method
- "Do not introduce new abstractions, layers, or dependencies without approval" — adding HTTP concerns to the URL builder would be a new abstraction
- "Clearly distinguish between fact, inference, and proposal" — this report follows this discipline throughout

---

## 6. Risk Assessment

### 6.1 What could go wrong?

| Risk                                                                | Likelihood          | Impact       | Mitigation                                                                                                |
| ------------------------------------------------------------------- | ------------------- | ------------ | --------------------------------------------------------------------------------------------------------- |
| Accept header change breaks existing working requests               | **Low**             | **High**     | Only apply to Part 1 GET requests; Part 2 and other protocol requests unaffected                          |
| OSH SensorHub rejects `Accept: application/geo+json` on POST        | **Confirmed (S-8)** | **High**     | Limit the default to GET requests only — do NOT apply to POST/PUT/DELETE                                  |
| Modifying `sharedFetch()` defaults affects all library protocols    | **High if done**    | **Critical** | Do NOT modify `sharedFetch()` defaults — use `customAcceptHeader` parameter or provide guidance constants |
| Adding `getAcceptHeader()` to `CSAPIQueryBuilder` expands its scope | **Certain if done** | **Medium**   | Provide the mapping as a standalone constant/helper in `formats/constants.ts`, not as a builder method    |
| Tests that mock Accept header behavior break                        | **Medium**          | **Low**      | Review test mocks before implementation                                                                   |
| Server behavior changes over time (Accept header handling evolves)  | **Low**             | **Low**      | Document the rationale and test against both servers                                                      |

### 6.2 Risk classification

**This is a MODERATE RISK change to library integrity.**

Unlike Issues #5–#8 (which proposed additive changes: new methods, constants, tests, JSDoc), Issue #9 proposes a **behavioral change** — modifying what HTTP headers the library sends to servers. This is qualitatively different:

- It **does** modify runtime behavior for all consumers making Part 1 GET requests
- It **does** affect what servers receive and how they respond
- It **does** require validation against multiple servers
- It **does** have a confirmed failure mode (S-8: POST with geo+json Accept fails on OSH)

However, the risk is **mitigated** by:

- The `customAcceptHeader` infrastructure already existing in `sharedFetch()`
- The exact media type constant (`MEDIA_TYPE_GEOJSON`) already existing
- The Part 1/Part 2 mapping being well-documented and spec-aligned
- The proposal being constrained to GET requests only

### 6.3 Integrity assessment

The library's integrity requires **careful implementation** if this change proceeds. The safest approach is:

1. Add a guidance constant (like `CSAPI_ACCEPT_HEADERS`) — zero behavioral impact until a consumer uses it
2. Do NOT modify `sharedFetch()` defaults — use the existing `customAcceptHeader` parameter
3. Do NOT add HTTP logic to `CSAPIQueryBuilder` — preserve the URL builder pattern
4. Ensure the default only applies to GET requests (not POST/PUT/DELETE) per S-8

---

## 7. Analysis: Architectural Boundaries and Accept Header Placement

### 7.1 The core architectural question

Issue #9 proposes adding `getAcceptHeader(resourceType)` "alongside URL generation." The question is: where does Accept header guidance belong architecturally?

| Option                                                       | What It Means                                                            | Pros                                                | Cons                                                                     |
| ------------------------------------------------------------ | ------------------------------------------------------------------------ | --------------------------------------------------- | ------------------------------------------------------------------------ |
| **A. Add method to `CSAPIQueryBuilder`**                     | `builder.getAcceptHeader('systems')` returns `'application/geo+json'`    | Co-located with URL generation                      | Expands builder scope from URL → request; violates single responsibility |
| **B. Add standalone constant map in `formats/constants.ts`** | `CSAPI_ACCEPT_HEADERS['systems']` returns `'application/geo+json'`       | Minimal, additive, consistent with Issue #6 pattern | Not co-located with builder                                              |
| **C. Add helper function in a new or existing module**       | `getAcceptHeaderForResource('systems')` returns `'application/geo+json'` | Clean API, can enforce GET-only constraint in JSDoc | New function export, mild scope expansion                                |
| **D. Modify `sharedFetch()` defaults**                       | Change the default `asJson` Accept to `application/geo+json` for CSAPI   | Automatic for all consumers                         | Affects all library protocols; unacceptable risk                         |

### 7.2 Assessment

**Option A (builder method) — Not recommended.** The `CSAPIQueryBuilder` is a 2,034-line class with a clear, single responsibility: URL construction. Every public method returns `string` (a URL). Adding a method that returns a media type string would introduce a conceptually different concern. The [contribution goal accuracy assessment](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/contribution-goal-accuracy-assessment.md) explicitly states: "'negotiation' overstates what a URL builder does." The AI Operational Constraints say: "Do not introduce new abstractions, layers, or dependencies without approval."

**Option B (constant map) — Recommended.** This is the minimal, additive approach. It mirrors the exact pattern proposed by Issue #6 for Content-Type mapping:

```typescript
// Already proposed by Issue #6 for POST/PUT Content-Type:
export const CSAPI_CONTENT_TYPES = {
  systems: 'application/geo+json',
  deployments: 'application/geo+json',
  procedures: 'application/geo+json',
  samplingFeatures: 'application/geo+json',
  properties: 'application/geo+json',
  datastreams: 'application/json',
  observations: 'application/json',
  controlStreams: 'application/json',
  commands: 'application/json',
} as const;

// Issue #9 equivalent for GET Accept headers — same mapping:
export const CSAPI_ACCEPT_HEADERS = {
  systems: 'application/geo+json',
  deployments: 'application/geo+json',
  procedures: 'application/geo+json',
  samplingFeatures: 'application/geo+json',
  properties: 'application/geo+json',
  datastreams: 'application/json',
  observations: 'application/json',
  controlStreams: 'application/json',
  commands: 'application/json',
} as const;
```

**Observation:** The Content-Type map (Issue #6) and Accept header map (Issue #9) contain **identical mappings** — Part 1 → `application/geo+json`, Part 2 → `application/json`. This suggests they could be unified into a single `CSAPI_MEDIA_TYPE_MAP` or similar, with JSDoc explaining the dual purpose (Content-Type for writes, Accept for reads). This decision should be made when both issues are implemented together.

**Option C (helper function) — Acceptable alternative.** A `getMediaTypeForResource(resourceType: string): string` function would provide a clean API and allow JSDoc to document the GET-only constraint for Accept headers. This could coexist with or replace the constant map.

**Option D (modify `sharedFetch` defaults) — Rejected.** `sharedFetch()` is upstream shared infrastructure. Modifying its default Accept header would affect WMS, WFS, WMTS, STAC, and OGC API Features — all of which rely on `application/json` as the default. This would be a cross-protocol behavioral change with unpredictable consequences.

### 7.3 Relationship to Issue #6

Issue #6 ([OS4CSAPI/ogc-csapi-explorer#6](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/6)) proposes `CSAPI_CONTENT_TYPES` for POST/PUT Content-Type headers. Issue #9 proposes Accept header defaults for GET requests. Both use the same Part 1/Part 2 → media type mapping:

| Resource Category                         | Part 1 (Systems, Deployments, Procedures, SamplingFeatures, Properties) | Part 2 (DataStreams, Observations, ControlStreams, Commands) |
| ----------------------------------------- | ----------------------------------------------------------------------- | ------------------------------------------------------------ |
| **Content-Type (Issue #6, for POST/PUT)** | `application/geo+json`                                                  | `application/json`                                           |
| **Accept (Issue #9, for GET)**            | `application/geo+json`                                                  | `application/json`                                           |

**Inference:** These two issues should be implemented together or with awareness of each other. A unified constant map with clear JSDoc documenting both purposes would be the most maintainable solution.

---

## 8. Analysis: GET-Only Constraint

### 8.1 Evidence from S-8

The CRUD smoke test findings document ([crud-smoke-test-findings.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/crud-smoke-test-findings.md)) includes **S-8**:

> "OSH SensorHub: Rejects `Accept: application/geo+json` on POST. During smoke testing, POST requests with `Accept: application/geo+json` header caused network-level failures on OSH SensorHub. The same request with `Accept: application/json` (or no explicit Accept header) succeeded with `201 Created`."

> "Issue #9 should note that this default should apply to **GET requests only**, not POST/PUT/DELETE operations where the response is typically empty or status-only."

### 8.2 Why POST/PUT/DELETE don't need Accept headers

For write operations:

- **POST (201 Created):** Servers typically return an empty body with a `Location` header. The Accept header is irrelevant when there's no response body to negotiate.
- **PUT (204 No Content):** No response body at all.
- **DELETE (204 No Content):** No response body at all.

Setting `Accept: application/geo+json` on these requests is:

1. **Semantically meaningless** — there's no response body to negotiate
2. **Actively harmful** — S-8 confirms it causes failures on OSH SensorHub

### 8.3 Implication for implementation

Any implementation of Issue #9 must clearly scope the Accept header default to **GET requests only**. This must be documented in:

- The constant/helper JSDoc
- Any implementation that automatically sets the header
- The upstream PR description

The `sharedFetch()` function's `method` parameter (`'GET' | 'HEAD'`) already distinguishes request methods, so the infrastructure to limit the default to GET exists.

---

## 9. Recommendation

### Primary recommendation: **Implement Issue #9 as a guidance constant (Option B), not as a builder method (Option A). Coordinate with Issue #6 for a unified media type mapping. Strictly limit to GET requests.**

### 9.1 What to implement

**Add a `CSAPI_ACCEPT_HEADERS` constant map** (or unify with Issue #6's `CSAPI_CONTENT_TYPES` into a single `CSAPI_RESOURCE_MEDIA_TYPES` map) in `src/ogc-api/csapi/formats/constants.ts`:

```typescript
/**
 * Default Accept header values for CSAPI resource GET requests.
 *
 * Part 1 resources (GeoJSON Features) should request `application/geo+json`
 * to ensure interoperability across servers. Part 2 resources use `application/json`.
 *
 * **Important:** This mapping applies to GET requests ONLY. Do NOT use these
 * values as Accept headers for POST, PUT, or DELETE operations — some servers
 * reject `Accept: application/geo+json` on write endpoints (see S-8).
 *
 * For POST/PUT Content-Type headers, see CSAPI_CONTENT_TYPES (Issue #6).
 *
 * @see https://docs.ogc.org/is/23-001/23-001.html — Part 1 (GeoJSON)
 * @see https://docs.ogc.org/is/23-002/23-002.html — Part 2 (JSON)
 */
export const CSAPI_ACCEPT_HEADERS: Record<string, string> = {
  systems: MEDIA_TYPE_GEOJSON,
  deployments: MEDIA_TYPE_GEOJSON,
  procedures: MEDIA_TYPE_GEOJSON,
  samplingFeatures: MEDIA_TYPE_GEOJSON,
  properties: MEDIA_TYPE_GEOJSON,
  datastreams: MEDIA_TYPE_JSON,
  observations: MEDIA_TYPE_JSON,
  controlStreams: MEDIA_TYPE_JSON,
  commands: MEDIA_TYPE_JSON,
} as const;
```

### 9.2 What NOT to do

- **Do NOT** add `getAcceptHeader()` to `CSAPIQueryBuilder` — the builder is a URL builder, not an HTTP client. Adding HTTP concerns would expand its scope.
- **Do NOT** modify `sharedFetch()` defaults — this is upstream shared infrastructure that would affect all library protocols.
- **Do NOT** apply the Accept header default to POST/PUT/DELETE requests — S-8 confirms this causes failures on OSH SensorHub.
- **Do NOT** implement this in isolation from Issue #6 — both issues use the same Part 1/Part 2 mapping and should share infrastructure.

### 9.3 Integration point

Consumers (including the demo app's bridge module) would use the constant like:

```typescript
import { CSAPI_ACCEPT_HEADERS } from 'ogc-client/ogc-api/csapi/formats/constants';

// When making a GET request for systems:
const url = builder.getSystems({ limit: 10 });
const response = await fetch(url, {
  headers: { Accept: CSAPI_ACCEPT_HEADERS['systems'] },
});
```

The library's own `sharedFetch()` could also be called with:

```typescript
sharedFetch(url, 'GET', true, CSAPI_ACCEPT_HEADERS['systems']);
```

This is the existing `customAcceptHeader` parameter — no new infrastructure needed.

### 9.4 Unified approach with Issue #6

If Issue #6 is implemented first or concurrently, consider a single unified map:

```typescript
/**
 * Default media types for CSAPI resource HTTP operations.
 *
 * Use as Content-Type for POST/PUT and as Accept for GET.
 * Part 1 resources: application/geo+json (GeoJSON Features)
 * Part 2 resources: application/json
 *
 * For Accept headers, use ONLY on GET requests — some servers reject
 * application/geo+json Accept on write endpoints (S-8).
 */
export const CSAPI_RESOURCE_MEDIA_TYPES = { ... } as const;
```

### 9.5 Verification plan

1. Confirm the constant map values match the OGC spec (Part 1 = GeoJSON, Part 2 = JSON)
2. Verify the demo app bridge can consume the constant (replace its local `getContentType()` helper)
3. Test GET requests with the Accept header against both servers (OSH SensorHub and 52North)
4. Confirm POST/PUT/DELETE requests do NOT use the Accept header
5. Run full test suite: `npx jest` — confirm no regressions

---

## Appendix A: Authority Precedence Analysis

| Authority Level | Source                     | Says About Accept Headers                                                                                                    | Weight       |
| --------------- | -------------------------- | ---------------------------------------------------------------------------------------------------------------------------- | ------------ |
| 1 (Highest)     | OGC 23-001r1 Part 1        | Defines Part 1 resources as GeoJSON Features; `application/geo+json` is the canonical media type                             | Definitive   |
| 2               | OGC 23-002r1 Part 2        | Defines Part 2 resources as JSON; `application/json` is the canonical media type                                             | Definitive   |
| 3               | AI Collaboration Agreement | Changes should strengthen contribution quality without expanding scope                                                       | Supportive   |
| 4               | AI Operational Constraints | "Do not introduce new abstractions without approval"; "Prefer minimal diffs"; "Do not expand scope beyond issue description" | Constraining |
| 5               | Issue #9 description       | Proposes Accept header defaults with specific mapping; suggests builder method addition                                      | Scoping      |
| 6               | Existing source code       | `sharedFetch()` already has `customAcceptHeader`; `MEDIA_TYPE_GEOJSON` exists; builder is URL-only                           | Precedent    |
| 7               | 12 reference documents     | F-4 ranked #1 priority; S-8 confirms GET-only constraint; demo bridge already implements the mapping                         | Evidence     |

---

## Appendix B: Cross-Reference Matrix

| Document                                                                                                                                                       | Location           | Relevance to Issue #9                                                                                            |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------ | ---------------------------------------------------------------------------------------------------------------- |
| [upstream-findings.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/upstream-findings.md)                                                     | ogc-csapi-explorer | F-4 — the finding Issue #9 addresses; #1 priority ranking; content negotiation appendix with full test matrix    |
| [library-findings-gap-analysis.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/library-findings-gap-analysis.md)                 | ogc-csapi-explorer | Maps F-4 → Issue #9; Severity High, Risk Medium; notes dual concern with Issue #6                                |
| [library-integration-report.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/library-integration-report.md)                       | ogc-csapi-explorer | Finding #2: library is URL builder, not HTTP client; Finding #14: no Content-Type guidance from builder          |
| [e2e-cross-server-report.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/e2e-cross-server-report.md)                             | ogc-csapi-explorer | Finding #3: content negotiation behavior; full test matrix confirming geo+json is most interoperable             |
| [e2e-write-operations-report.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/e2e-write-operations-report.md)                     | ogc-csapi-explorer | Finding #6: Content-Type mapping needs library guidance; Priority 2 recommendation: CSAPI_CONTENT_TYPES constant |
| [contribution-goal-accuracy-assessment.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/contribution-goal-accuracy-assessment.md) | ogc-csapi-explorer | "negotiation overstates what a URL builder does"; validates builder scope is URL-only                            |
| [conformance-bypass-architecture-notes.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/conformance-bypass-architecture-notes.md) | ogc-csapi-explorer | Demo bypasses OgcApiEndpoint; bridge handles HTTP transport separately from builder                              |
| [crud-smoke-test-findings.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/crud-smoke-test-findings.md)                           | ogc-csapi-explorer | **S-8: Critical** — OSH rejects Accept: geo+json on POST; Accept default must be GET-only                        |
| [endpoint-error-isolation-report.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/endpoint-error-isolation-report.md)             | ogc-csapi-explorer | Confirms http-utils.ts has shared dependencies; modifying it affects all protocols                               |
| [library-source-changes-audit.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/library-source-changes-audit.md)                   | ogc-csapi-explorer | Only 1 commit touched library source; Issue #9 would be second behavioral change                                 |
| [schema-display-findings.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/schema-display-findings.md)                             | ogc-csapi-explorer | F-13: `f` parameter vs. header-based negotiation are separate mechanisms; context for content negotiation        |
| [AI_OPERATIONAL_CONSTRAINTS.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/governance/AI_OPERATIONAL_CONSTRAINTS.md)                        | ogc-client-CSAPI_2 | Authority precedence; no scope expansion; no new abstractions without approval; minimal diffs                    |

---

## Conclusion

Issue #9 addresses the **#1 priority finding** (F-4) across all integration testing — a real interoperability problem where servers return empty results when the wrong Accept header is used for Part 1 resource GET requests.

The recommended implementation is:

1. **Add a `CSAPI_ACCEPT_HEADERS` constant map** in `formats/constants.ts` — purely additive, zero behavioral impact until consumed
2. **Coordinate with Issue #6** — both issues use the same Part 1 → geo+json / Part 2 → json mapping; a unified constant is preferable
3. **Do NOT add HTTP logic to `CSAPIQueryBuilder`** — preserve the URL builder pattern
4. **Do NOT modify `sharedFetch()` defaults** — use the existing `customAcceptHeader` parameter
5. **Strictly limit to GET requests** — S-8 confirms POST with geo+json Accept header fails on OSH SensorHub

This approach provides the interoperability guidance consumers need while respecting the library's architectural boundaries and the AI Operational Constraints' minimal-diff and no-new-abstractions principles.
