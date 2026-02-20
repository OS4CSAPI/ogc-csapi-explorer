# Findings Report: Issue #18 — Handle Empty-Body 201 Created Responses Without Crashing (F-15)

> **Date**: 2026-02-18
> **Source Issue**: [OS4CSAPI/ogc-csapi-explorer#18](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/18)
> **Finding ID**: F-15 (from [crud-smoke-test-findings.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/crud-smoke-test-findings.md))
> **Labels on source issue**: `bug`

---

## AI Constraints Acknowledgment

> I have reviewed the AI Operational Constraints.
> Issue goal: Assess whether the empty-body 201 Created response crash (F-15) requires a fix in our CSAPI client library contribution.
> Assumptions requiring confirmation: None — the issue is well-documented with server evidence and a demo app workaround commit.

---

## Executive Summary

Issue #18 reports that calling `response.json()` on an HTTP `201 Created` response with an empty body throws `SyntaxError: Unexpected end of JSON input`. This crash was discovered in the CSAPI Explorer demo app's `apiFetch()` wrapper during live CRUD smoke testing against OSH SensorHub. The fix was applied in the demo app at commit [`f3dd4ee`](https://github.com/OS4CSAPI/ogc-csapi-explorer/commit/f3dd4ee).

**This issue does not affect our CSAPI client library contribution.** The ogc-client library's CSAPI module (`src/ogc-api/csapi/`) is a pure URL builder — it constructs URLs for API endpoints but does not perform HTTP requests, does not call `fetch()`, and does not parse HTTP response bodies. A comprehensive search of the entire CSAPI source tree (`src/ogc-api/csapi/**`) confirms **zero instances** of `response.json()`, `fetch()`, or `response.text()`. The crash occurred entirely in the consumer layer (the demo app's HTTP wrapper), which is outside the library's architectural boundary.

**Recommendation: NO ACTION REQUIRED** — There is no code in our CSAPI library contribution that handles HTTP response bodies, and therefore no code that could crash on an empty 201 response. The issue is correctly classified as affecting "any HTTP response handling layer (library or consumer `fetch()` wrapper)" — and our library contribution is neither of those things. The workaround has already been applied in the demo app where the crash actually occurred.

---

## Issue Description

### What the issue reports

When a POST request creates a resource successfully, OGC API servers (specifically OSH SensorHub) return HTTP `201 Created` with:
- A `Location` header containing the URL of the new resource
- An **empty response body** (`Content-Length: 0`)

The standard JavaScript `response.json()` method throws when called on an empty body:

```
Failed to execute 'json' on 'Response': Unexpected end of JSON input
```

The resource is created successfully on the server, but the client's response handler crashes because it unconditionally attempts to parse the response body as JSON.

### Scope of impact (per the issue)

All four Part 1 resource types return empty-body 201 responses on OSH SensorHub:

| Operation | Status | Body |
|---|---|---|
| `POST /systems` | 201 | Empty |
| `POST /procedures` | 201 | Empty |
| `POST /deployments` | 201 | Empty |
| `POST /samplingFeatures` | 201 | Empty |

### Where the crash actually occurred

The crash happened in the demo app's `apiFetch()` wrapper in `demo/src/api.ts`, **not** in any library code. The response handling code only guarded against `204 No Content` before attempting `response.json()`:

```typescript
// Only guards against 204
if (response.status === 204) {
  return { ok: true, status: 204, data: null };
}

// Falls through to .json() for ALL other successful responses, including 201
const contentType = response.headers.get('content-type') || '';
if (contentType.includes('json')) {
  data = await response.json();  // ← THROWS on empty body
}
```

### Workaround already applied

Fixed in the demo app at commit [`f3dd4ee`](https://github.com/OS4CSAPI/ogc-csapi-explorer/commit/f3dd4ee) by adding empty-body guards:

```typescript
const contentLength = response.headers.get('content-length');
if (response.status === 204 || contentLength === '0') {
  return { ok: true, status: response.status, data: null, headers: responseHeaders };
}

const text = await response.text();
if (!text || !text.trim()) {
  return { ok: true, status: response.status, data: null, headers: responseHeaders };
}
data = JSON.parse(text);
```

---

## Source Code Review

### The critical question: Does our library contain HTTP response handling code?

**No.** A comprehensive search of the entire CSAPI module (`src/ogc-api/csapi/`) and the broader `src/` directory confirms:

| Search Pattern | Results in `src/ogc-api/csapi/**` | Results in `src/**` |
|---|---|---|
| `response.json()` | **0 matches** | **0 matches** |
| `fetch(` | **0 matches** | **0 matches** |
| `response.text()` | **0 matches** | **0 matches** |

The CSAPI module is architecturally a **pure URL builder**. Its public API consists of:

- **`CSAPIQueryBuilder`** — Constructs URLs for all 9 CSAPI resource types (systems, deployments, procedures, samplingFeatures, properties, datastreams, observations, controlStreams, commands). Its 82 public methods return URL strings. It never calls `fetch()`.
- **`parseCollectionResponse()`** — Parses already-deserialized JSON objects (i.e., the caller has already done `await response.json()` and passes the result). This function takes `unknown` as input, not a `Response` object.
- **`parseSWEComponent()`** — Parses already-deserialized SWE Common JSON objects. Same pattern — takes `unknown`, not `Response`.
- **`extractCSAPIFeature()` / `getCSAPIResourceType()`** — Operate on already-deserialized GeoJSON objects.

**None of these functions interact with HTTP response objects, headers, or body streams.** The architectural boundary is clear: the library builds URLs and parses pre-deserialized data structures. HTTP request execution and response body handling are the consumer's responsibility.

### How the upstream ogc-client handles HTTP (for context)

The upstream `ogc-client` library does have an HTTP layer in `src/shared/` and `src/worker/` that handles `fetch()` calls for the pre-existing handlers (WMS, WFS, WMTS, STAC, OGC API Features). However:

1. This HTTP layer is part of the **upstream** codebase, not our CSAPI contribution
2. The upstream HTTP layer handles **GET requests** for capability documents and resource listings — not POST/PUT/DELETE write operations
3. Our CSAPI contribution does not modify or extend this HTTP layer
4. The upstream HTTP layer is outside the scope of our CSAPI contribution and outside the scope of this findings review

### Related finding: Issue #15 (F-12) — parseLocationHeader()

The [Issue #15 findings report](./issue-15-parse-location-header.md) analyzed a closely related finding (extracting resource IDs from `Location` headers in 201 responses) and also recommended **DEFER** because:
- The library is a URL builder, not an HTTP response parser
- The extraction is trivially self-implementable by consumers
- There are zero internal callers within the library
- Adding it would expand the public API surface without necessity

The same architectural argument applies here with even greater force: F-15 is about HTTP response body handling, which is even further outside the library's boundary than header parsing.

---

## Reference Document Review

### 1. AI Operational Constraints (`AI_OPERATIONAL_CONSTRAINTS.md`)

- **§2.1 Assumptions and Scope**: "Do not expand scope beyond the issue description" — The issue itself acknowledges: "If the library doesn't currently have internal create/update/delete helpers, this pattern should be documented as a recommended practice for consumers." The library does not have such helpers. The issue's own conditional framing confirms this is a consumer-layer concern.
- **§2.2 Architectural Alignment**: "Preserve upstream structure, naming, and patterns" — The upstream library's architecture separates URL construction (library) from HTTP execution (consumer). Our CSAPI module follows this same pattern. Adding HTTP response handling would be an architectural deviation.
- **§2.2**: "Do not introduce new abstractions, layers, or dependencies without approval" — Any fix for F-15 would require introducing an HTTP response handling layer to the CSAPI module, which currently has none.

### 2. CRUD Smoke Test Findings (`crud-smoke-test-findings.md`)

F-15 is documented as:
- **Severity**: High
- **Affected Area**: "Any HTTP response handling layer (library or consumer `fetch()` wrapper)"
- **Status**: "Issue created; workaround applied in demo app"

The document correctly identifies this as affecting the HTTP response handling layer. The key phrase is "library **or** consumer `fetch()` wrapper" — and in our case, the library has no such layer. The demo app's `apiFetch()` wrapper was the affected code, and the fix has been applied there.

### 3. Library Source Changes Audit (`library-source-changes-audit.md`)

Confirms the conservation record:
- **Exactly one commit** (`e73cff8`) has modified library source during the entire demo development lifecycle
- All CRUD smoke test workarounds (including the F-15 empty-body fix) were implemented in the demo app layer without touching `src/`
- The "What Was NOT Changed" table explicitly lists F-15's workaround as demo-only:

| Workaround | Finding | Implemented In | Library Touched? |
|---|---|---|---|
| Content-Type negotiation | F-15 | `demo/src/api.ts` | **No** |

### 4. Library Findings Gap Analysis (`library-findings-gap-analysis.md`)

F-15 is not included in the original gap analysis (which covers F-1 through F-12 and F-83 through F-85). It was discovered later during CRUD smoke testing and documented in the separate crud-smoke-test-findings.md. This positions it as a demo-phase discovery, not a core integration finding.

### 5. Contribution Goal Accuracy Assessment (`contribution-goal-accuracy-assessment.md`)

Confirms the library's architectural scope:
- "The library is a **URL builder**, not an HTTP client — it does not perform fetch operations, manage authentication, or handle response deserialization end-to-end"
- Response parsing exists for data structures (SWE Common, GeoJSON, collection envelopes) — not for HTTP `Response` objects

### 6. Upstream Findings (`upstream-findings.md`)

F-15 was discovered after the original upstream findings document (which covers F-1 through F-12). It does not appear in the priority table. The related F-12 (parseLocationHeader) — which addresses a complementary aspect of 201 response handling — is ranked #10 of 11 (lowest actionable priority).

### 7. Schema Display Findings (`schema-display-findings.md`)

No direct relevance to F-15. Included for completeness — the document covers F-13 (JSDoc confusion) and F-14 (schema response parser), neither of which involves HTTP response body handling.

### 8. Conformance Bypass Architecture Notes (`conformance-bypass-architecture-notes.md`)

Documents why the demo app bypasses `OgcApiEndpoint` and uses `CSAPIQueryBuilder` directly. This architectural decision means the demo app handles its own HTTP requests via `apiFetch()` — which is exactly where the F-15 crash occurred. The library's role is limited to URL construction.

### 9. E2E Write Operations Report (`e2e-write-operations-report.md`)

Directly relevant — documents the end-to-end write operation testing where F-15 was encountered. Finding #8 in this report notes: "201 Created responses have empty bodies — extract resource ID from Location header." This further confirms the issue is at the HTTP response level, not the URL builder level.

### 10. Endpoint Error Isolation Report (`endpoint-error-isolation-report.md`)

Documents the one library source modification (`e73cff8`) — the EndpointError isolation refactor. Relevant as context for the conservation record but not directly related to F-15.

### 11. Library Integration Report (`library-integration-report.md`)

Provides the integration narrative. The library's role as a URL builder is reinforced throughout. HTTP response handling is consistently shown as a consumer responsibility.

### 12. E2E Cross-Server Report (`e2e-cross-server-report.md`)

Documents cross-server testing behavior. Confirms that empty-body 201 responses are standard server behavior for OSH SensorHub, not an anomaly.

---

## Risk Assessment

### Risk of making changes to the library

| Risk Factor | Assessment | Rating |
|---|---|---|
| No code to fix | **There is no HTTP response handling code in the CSAPI module to modify** | **N/A** |
| Architectural deviation | Adding HTTP response handling would cross the library's established URL-builder boundary | **High** |
| Conservation record | Would be the 2nd library source modification and the 1st to add an entirely new architectural concern | **High** |
| Scope creep | The issue itself conditionally acknowledges: "If the library doesn't currently have internal create/update/delete helpers, this pattern should be documented" | **High** |

### Risk of NOT making changes to the library

| Risk Factor | Assessment | Rating |
|---|---|---|
| Consumer impact | **None** — the library doesn't handle HTTP responses; consumers handle their own `fetch()` calls | **None** |
| Demo app impact | **None** — the workaround was already applied at commit `f3dd4ee` | **None** |
| Library functionality gap | **None** — the library's scope is URL construction, not HTTP response handling | **None** |

### Overall risk assessment

There is **no risk** from taking no action because there is **no library code that is affected by this issue**. The risk is entirely in making unnecessary changes — adding HTTP response handling to a URL builder library would be an architectural violation that degrades the integrity of the contribution.

---

## Analysis

### Is there a bug in the library?

**No.** The CSAPI module contains zero lines of HTTP response handling code. There is no `fetch()` call, no `response.json()` call, no `response.text()` call, and no HTTP `Response` object handling anywhere in `src/ogc-api/csapi/`. The crash described in F-15 occurred in the demo app's `apiFetch()` wrapper — consumer code that is outside the library.

### Does the library need to be changed?

**No.** The library's architectural boundary is URL construction and data structure parsing. HTTP request execution and response body handling are the consumer's responsibility. This is the same architecture used by the upstream `ogc-client` library for its other handlers (WMS, WFS, WMTS, STAC), where the HTTP layer is separate from the endpoint/builder layer.

### Is the issue valid?

**Yes — but it's a consumer-layer issue, not a library issue.** The crash is real, the behavior is well-documented, and the fix is correct. But it applies to the demo app's `apiFetch()` wrapper (or any other consumer HTTP wrapper), not to the ogc-client CSAPI module.

### What about the OGC spec behavior?

The OGC Connected Systems API spec states that 201 Created responses have:
- `Location` header (required) — URL of the created resource
- Response body — "Typically empty (201 with Location header)" / "MAY return created resource representation"

This is standard OGC API behavior documented in our own research (`csapi-crud-operations.md` and `csapi-part2-requirements.md`). The library's URL builder correctly constructs the POST target URLs. What servers return in response is outside the library's scope.

### How does this compare to other DEFER recommendations?

| Report | Finding | Issue | Recommendation | Reason |
|---|---|---|---|---|
| Issue #15 | F-12 (parseLocationHeader) | Enhancement | DEFER | Library is URL builder, not response parser; one-liner workaround |
| Issue #17 | F-14 (parseSchemaResponse) | Enhancement | DEFER | Trivial consumer workaround; new abstractions; conservation record |
| **Issue #18** | **F-15 (empty-body 201)** | **Bug (consumer)** | **NO ACTION** | **No library code is affected; crash is in consumer HTTP wrapper** |

This report is the strongest "no action" case of any finding reviewed: there is literally no library code that handles the situation described in the issue.

---

## Recommendation

**NO ACTION REQUIRED — The CSAPI client library contribution is not affected by this issue**

### Rationale

1. **No library code handles HTTP response bodies.** The CSAPI module (`src/ogc-api/csapi/`) is a pure URL builder with zero instances of `response.json()`, `fetch()`, or `response.text()`. There is no code to fix.

2. **The crash occurred in consumer code.** The `apiFetch()` wrapper in the demo app's `demo/src/api.ts` is where `response.json()` was called without guarding against empty bodies. This is outside the library's architectural boundary.

3. **The workaround is already applied.** Commit [`f3dd4ee`](https://github.com/OS4CSAPI/ogc-csapi-explorer/commit/f3dd4ee) fixed the demo app's response handling. The issue is resolved at the layer where it occurred.

4. **Adding HTTP response handling would violate architectural boundaries.** Per AI Operational Constraints §2.2: "Do not introduce new abstractions, layers, or dependencies without approval." The library is a URL builder; adding an HTTP response handling layer would be a fundamental scope expansion.

5. **The issue's own text acknowledges this possibility.** The "Where to apply this" section states: "If the library doesn't currently have internal create/update/delete helpers, this pattern should be documented as a recommended practice for consumers." The library does not have such helpers.

### What already exists (no changes needed)

| Aspect | Status |
|---|---|
| URL construction for POST targets | **Working** — `createSystem()`, `createDataStreamForSystem()`, etc. produce correct URLs |
| Consumer guidance on 201 responses | **Documented** — OGC spec references in `csapi-crud-operations.md` and `csapi-part2-requirements.md` |
| Demo app fix | **Applied** — commit `f3dd4ee` |
| Issue tracking | **Tracked** — [ogc-csapi-explorer#18](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/18) documents the finding |

---

## Appendix A: OGC Specification References

### OGC 23-002 — Connected Systems API: POST Response Behavior

Per the CSAPI Part 1 and Part 2 requirements:

| Response Code | Body | Headers | Usage |
|---|---|---|---|
| 201 Created | Empty or optional resource representation | `Location` (required) | Successful resource creation |
| 204 No Content | Empty | — | Successful update or deletion |

The spec explicitly states that 201 response bodies are "typically empty" and that the `Location` header is the authoritative reference for the created resource. This is standard OGC API behavior, not a server quirk.

### RFC 7231 §6.3.2 — 201 Created

> The 201 (Created) status code indicates that the request has been fulfilled and has resulted in one or more new resources being created. The primary resource created by the request is identified by either a Location header field in the response or, if no Location field is received, by the effective request URI.

The RFC does not require a response body for 201 responses.

---

## Appendix B: Reference Documents Consulted

| # | Document | Key Relevance |
|---|---|---|
| 1 | [AI_OPERATIONAL_CONSTRAINTS.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/governance/AI_OPERATIONAL_CONSTRAINTS.md) | Behavioral rules — no new abstractions without approval, preserve architectural boundaries |
| 2 | [crud-smoke-test-findings.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/crud-smoke-test-findings.md) | F-15 detailed breakdown — crash in `apiFetch()`, not library code |
| 3 | [library-source-changes-audit.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/library-source-changes-audit.md) | Conservation record — one commit, demo-only workarounds for CRUD issues |
| 4 | [contribution-goal-accuracy-assessment.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/contribution-goal-accuracy-assessment.md) | Library scope — URL builder, not HTTP client |
| 5 | [upstream-findings.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/upstream-findings.md) | Priority framework — F-15 not in original findings; related F-12 is #10 of 11 |
| 6 | [library-findings-gap-analysis.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/library-findings-gap-analysis.md) | F-15 not in original gap analysis; discovered during CRUD smoke testing |
| 7 | [library-integration-report.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/library-integration-report.md) | Integration narrative — library as URL builder |
| 8 | [conformance-bypass-architecture-notes.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/conformance-bypass-architecture-notes.md) | Why demo uses `CSAPIQueryBuilder` directly — consumer handles own HTTP |
| 9 | [e2e-write-operations-report.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/e2e-write-operations-report.md) | Finding #8: empty 201 bodies — confirms consumer-level concern |
| 10 | [e2e-cross-server-report.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/e2e-cross-server-report.md) | Cross-server 201 response behavior confirmation |
| 11 | [endpoint-error-isolation-report.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/endpoint-error-isolation-report.md) | Conservation record context — the one library source commit |
| 12 | [schema-display-findings.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/schema-display-findings.md) | No direct relevance; included for completeness per user request |
| 13 | [OGC 23-002](https://docs.ogc.org/is/23-002/23-002.html) | Normative: POST response behavior (201 Created, optional body) |
| 14 | [RFC 7231 §6.3.2](https://www.rfc-editor.org/rfc/rfc7231#section-6.3.2) | Normative: 201 Created semantics — body not required |

---

## Appendix C: Relationship to Other Findings Reports

| Report | Finding | Relationship |
|---|---|---|
| [issue-15-parse-location-header.md](./issue-15-parse-location-header.md) | F-12 (parseLocationHeader) | Closely related — F-12 addresses the other half of 201 response handling (extracting the resource ID from the `Location` header). That report also recommended DEFER because the library is a URL builder, not a response parser. F-15 and F-12 together describe the full 201 response handling pattern: guard against empty body (F-15) + extract ID from Location header (F-12). Both are consumer-layer concerns. |
| [issue-17-schema-response-parser.md](./issue-17-schema-response-parser.md) | F-14 (parseSchemaResponse) | Same pattern — proposed adding response-level parsing to the library where the consumer workaround is trivial. Recommended DEFER. |
| [issue-5-nested-create-methods.md](./issue-5-nested-create-methods.md) | F-1/F-2 (URL bugs) | Contrast — F-1/F-2 are genuine URL generation bugs in the library's core scope. F-15 is a consumer-layer HTTP handling issue outside the library's scope. |
| [issue-16-schema-jsdoc-parameter-confusion.md](./issue-16-schema-jsdoc-parameter-confusion.md) | F-13 (JSDoc) | Contrast — F-13 is a documentation bug in code we wrote (JSDoc guidance causing 400 errors). F-15 is a crash in code we didn't write (demo app HTTP wrapper). |
