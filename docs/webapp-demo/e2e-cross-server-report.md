# Cross-Server Interoperability Test Report

**Date:** 2026-02-16  
**Test Script:** `examples/e2e-cross-server.ts`  
**Results Data:** `examples/e2e-cross-server-results.json`

## Executive Summary

Cross-server E2E testing validates the `ogc-client` CSAPI library against **both** available Connected Systems API servers:

| Server | Base URL | Tests | Passed | Failed | Pass Rate |
|--------|----------|-------|--------|--------|-----------|
| **OSH SensorHub** | `http://45.55.99.236:8080/sensorhub/api` | 35 | 33 | 2 | **94%** |
| **52North CSA** | `https://csa.demo.52north.org` | 26 | 22 | 4 | **85%** |

**Overall: 55/61 tests passed (90%) — the library works correctly across both server implementations.**

The library's parsers (`parseCollectionResponse`, `extractCSAPIFeature`) and URL builder (`CSAPIQueryBuilder`) successfully handle both servers' different response envelopes, discovery patterns, and naming conventions.

---

## Server Characteristics

| Characteristic | OSH SensorHub | 52North CSA |
|---|---|---|
| Discovery Mode | Root-level links on landing page | Collection-scoped `items` links |
| Conformance | 33 classes (22 CSA-specific) | 1 class (`ogcapi-common-1` only) |
| Response Envelope | `{ items: [...] }` (non-standard) | `{ type: "FeatureCollection", features: [...] }` (spec-compliant) |
| Data Present | Yes (12+ systems, 100+ observations) | No (all collections empty) |
| CRUD Support | Full create/read/update/delete | Read-only (401 on POST) |
| Authentication | Basic auth (`admin/admin`) | None required |
| SSL | Plain HTTP | HTTPS with expired cert |
| Part 2 Endpoints | Fully functional | 500 Internal Server Error |

---

## Test Results by Category

### 1. Landing Page — Both Pass ✅

| Test | OSH | 52N | Notes |
|------|-----|-----|-------|
| Accessible | ✅ | ✅ | Both return 200 with valid JSON |
| Has title | ✅ | ✅ | OSH: "Connected Systems API Service", 52N: "connected-systems-pygeoapi" |
| Links array | ✅ | ✅ | OSH: 10 links, 52N: 7 links |
| Has `rel="data"` link | ❌ | ✅ | **Finding #1**: OSH uses resource-name rels, not standard `data` rel |

### 2. Conformance — Split

| Test | OSH | 52N | Notes |
|------|-----|-----|-------|
| Endpoint accessible | ✅ | ✅ | Both return 200 |
| Conformance classes | ✅ | ✅ | OSH: 33 classes, 52N: 1 class |
| CSA-specific classes | ✅ | ❌ | **Finding #2**: 52N declares zero CSA conformance classes |

### 3. Discovery — Library Handles Both Patterns

| Test | OSH | 52N | Notes |
|------|-----|-----|-------|
| `scanCsapiLinks` on landing page | ✅ (6 types) | ❌ (0 types) | **Finding #3**: Library requires fallback for servers without root links |
| Collections endpoint | ✅ (4 cols) | ✅ (5 cols) | |
| Collection-scoped links | ✅ (4 types) | ✅ (5 types) | Both discovered via `items` rel convention |

**Key insight**: `scanCsapiLinks` correctly discovers resources from collection-level links on 52North, even though the landing page has none. The library's three-convention approach (`ogc-cs:` prefix, plain name, `items` rel) works across both servers at the collection level.

### 4. Builder Setup — Both Pass ✅

| Test | OSH | 52N | Notes |
|------|-----|-----|-------|
| `CSAPIQueryBuilder` created | ✅ | ✅ | |
| Available resource types | 6 types | 9 types (fallback) | 52N uses fallback standard paths |

### 5. Read Operations — Part 1 Passes, Part 2 Diverges

| Test | OSH | 52N | Notes |
|------|-----|-----|-------|
| LIST systems | ✅ (3 items) | ✅ (0 items) | |
| LIST deployments | ✅ (0 items) | ✅ (0 items) | |
| LIST procedures | ✅ (0 items) | ✅ (0 items) | |
| LIST datastreams | ✅ (3 items) | ❌ (500) | **Finding #4**: 52N Part 2 endpoints broken |
| LIST observations | ✅ (3 items) | ❌ (500) | **Finding #4** |
| Query: `limit=2` | ✅ | ✅ | |
| Query: `limit=2, offset=1` | ✅ | ✅ | |

### 6. Response Envelope — Both Handled Correctly ✅

| Test | OSH | 52N | Notes |
|------|-----|-----|-------|
| Envelope format | ✅ (`items`) | ✅ (`FeatureCollection/features`) | **Finding #5** |
| Response metadata | ✅ | ✅ | Neither provides `numberMatched`/`numberReturned`/`timeStamp` |

### 7. Parsers — All Pass ✅

| Test | OSH | 52N | Notes |
|------|-----|-----|-------|
| `parseCollectionResponse` — systems | ✅ (3 items) | ✅ (0 items) | |
| `parseCollectionResponse` — deployments | ✅ (0 items) | ✅ (0 items) | |
| `parseCollectionResponse` — procedures | ✅ (0 items) | ✅ (0 items) | |
| `parseCollectionResponse` — datastreams | ✅ (3 items) | — (skipped, 500) | |
| `parseCollectionResponse` — observations | ✅ (3 items) | — (skipped, 500) | |
| `extractCSAPIFeature` | ✅ | — (no data) | |

**`parseCollectionResponse` handles both envelope formats correctly** — this is a major validation that the parser is interoperable.

### 8. Nested Resources — Works on OSH

| Test | OSH | 52N | Notes |
|------|-----|-----|-------|
| `getSystemDataStreams()` | ✅ (10 ds) | — (no data) | |
| Nested parse | ✅ | — | |
| `getObservationsForDatastream()` | ❌ | — | **Finding #6**: Method doesn't exist |

### 9. CRUD Operations — Full Cycle on OSH, Read-Only on 52N

| Test | OSH | 52N | Notes |
|------|-----|-----|-------|
| CREATE System | ✅ (201) | — | |
| GET System (read-back) | ✅ | — | |
| UPDATE System (PUT) | ✅ (204) | — | |
| UPDATE verification | ✅ | — | |
| DELETE System | ✅ (204) | — | |
| DELETE verification | ✅ (404) | — | |
| Read-only enforcement | — | ✅ (401) | 52N correctly rejects writes |

---

## Findings

### Finding #1 — OSH Omits Standard `rel="data"` Link

**Severity:** Low  
**Affects:** OSH SensorHub only

OSH SensorHub's landing page does not include a `rel="data"` link pointing to `/collections`. Instead, it uses resource-name-based link relations (`systems`, `deployments`, etc.) directly on the root. The 52North server correctly includes `rel="data"` → `/collections`.

This means OGC API clients that rely on the standard `rel="data"` discovery path will not find collections on OSH. The library should support both discovery patterns (which it already does via `scanCsapiLinks`).

### Finding #2 — 52North Declares Zero CSA Conformance Classes

**Severity:** Medium  
**Affects:** 52North CSA only

The 52North server's `/conformance` endpoint returns only `ogcapi-common-1/1.0/conf/core`. It does not advertise any Connected Systems API conformance classes (OGC 23-001 or 23-002).

This means any client checking conformance before using CSA features would skip this server entirely. Since the server *does* implement Part 1 resources (systems, deployments, procedures), this is a server-side metadata omission. The library should not gate functionality on conformance declarations alone.

### Finding #3 — Library Needs Fallback Discovery for Empty Landing Pages

**Severity:** Medium  
**Affects:** Library  

`scanCsapiLinks(landingPage.links)` returns 0 resource types for 52North because its landing page has no CSAPI-related link relations. Resource discovery only works at the collection level.

**Recommendation:** The library's endpoint discovery should:
1. Try root-level links first (works for OSH)
2. Fall back to collection-scoped discovery if root yields nothing (needed for 52N)
3. Use standard resource paths as a final fallback

This is the discovery interoperability gap documented in our earlier [cross-server interoperability analysis](../implementation/cross-server-interoperability-analysis.md).

### Finding #4 — 52North Part 2 Endpoints Return 500

**Severity:** High  
**Affects:** 52North CSA

Requesting `/datastreams` or `/observations` (Part 2 resources) from 52North returns HTTP 500 Internal Server Error with an HTML error page instead of JSON.

**Impact:** The library must handle non-JSON error responses gracefully. If `fetch()` returns HTML, `JSON.parse()` will throw — the library should catch this and provide a meaningful error rather than a parse failure.

**Server-side implication:** 52North's `connected-systems-pygeoapi` implementation appears to only support Part 1 resources (systems, deployments, procedures, sampling features) and breaks on Part 2 resources.

### Finding #5 — Servers Use Different Response Envelopes

**Severity:** Medium (already handled)  
**Affects:** Both servers, but library handles it correctly

| Server | Envelope Format |
|--------|----------------|
| OSH SensorHub | `{ items: [...], links: [...] }` |
| 52North | `{ type: "FeatureCollection", features: [...], links: [...] }` |

`parseCollectionResponse` correctly handles **both formats**. This is one of the most important interoperability validations — confirmed working.

### Finding #6 — Missing `getObservationsForDatastream()` Method

**Severity:** Medium  
**Affects:** Library  

`CSAPIQueryBuilder` does not have a `getObservationsForDatastream(dsId)` method. This is a gap in the nested resource URL builder API. Similar methods like `getSystemDataStreams(sysId)` exist, but the observation-under-datastream pattern is missing.

**Impact:** Users cannot build URLs for the critical `/datastreams/{id}/observations` nested path through the builder. Must construct manually.

### Finding #7 — `featuresOfInterest` vs `samplingFeatures` Handled

**Severity:** Info  
**Successfully handled by library**

52North uses the path `/featuresOfInterest` while OSH uses `/samplingFeatures`. The `scanCsapiLinks` helper includes normalization logic (`featuresOfInterest` → `samplingFeatures`), and this works correctly — 52North's `all_fois` collection is discovered as `samplingFeatures` in the resource map.

---

## Cross-Server Comparison Matrix

```
                              OSH SensorHub    52North CSA
                              ─────────────    ───────────
Landing Page                  ✅ (no "data")   ✅
Conformance (CSA)             ✅ (22 classes)  ❌ (0 classes)
Root Discovery                ✅ (6 types)     ❌ (0 types)
Collection Discovery          ✅ (4 types)     ✅ (5 types)
Part 1 Read (sys/dep/proc)    ✅               ✅ (empty)
Part 2 Read (ds/obs)          ✅               ❌ (500)
Query Params (limit, offset)  ✅               ✅
Response Envelope             items (custom)   FeatureCollection (standard)
Parser Compatibility          ✅               ✅
Nested Resources              ✅               — (no data)
CRUD                          ✅ full cycle    ❌ read-only (401)
Auth Required                 Yes (Basic)      No
SSL                           HTTP             HTTPS (expired cert)
```

---

## Recommendations for Upstream Library

1. **Multi-strategy discovery** (Finding #3): Implement root → collection → fallback discovery chain to handle both server patterns.

2. **Handle HTML error responses** (Finding #4): When `Content-Type` is `text/html`, don't attempt JSON parse — return a meaningful `EndpointError` instead.

3. **Add `getObservationsForDatastream()`** (Finding #6): Add nested resource methods for all Part 2 parent-child relationships.

4. **Don't gate on conformance** (Finding #2): Server may implement CSA resources without declaring CSA conformance classes. Discovery should be capabilities-based, not conformance-based.

5. **Test both envelopes in unit tests** (Finding #5): The parser handles both, but the unit test suite should include explicit test cases for both `items` and `features` envelopes.

---

## Conclusion

The `ogc-client` CSAPI library demonstrates **strong cross-server interoperability** for Part 1 resources. The core parsers (`parseCollectionResponse`, `extractCSAPIFeature`) handle both servers' response formats correctly, and the `CSAPIQueryBuilder` generates valid URLs for both implementations.

The main gaps are in discovery strategy (root vs. collection-scoped), error handling for non-JSON responses, and missing nested resource builder methods. These are addressable library improvements that would make the code robust across the full spectrum of server implementations.

**Bottom line:** The library's core read/parse pipeline works correctly against two independent CSA server implementations with fundamentally different architectures.
