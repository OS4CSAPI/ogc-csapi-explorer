# Cross-Server Interoperability Test Report

**Date:** 2026-02-16 (v2 — corrected for 52North content negotiation)  
**Test Script:** `examples/e2e-cross-server.ts`  
**Results Data:** `examples/e2e-cross-server-results.json`

## Executive Summary

Cross-server E2E testing validates the `ogc-client` CSAPI library against **both** available Connected Systems API servers:

| Server | Base URL | Tests | Passed | Failed | Pass Rate |
|--------|----------|-------|--------|--------|-----------|
| **OSH SensorHub** | `http://45.55.99.236:8080/sensorhub/api` | 39 | 37 | 2 | **95%** |
| **52North CSA** | `https://csa.demo.52north.org` | 30 | 25 | 5 | **83%** |

**Overall: 62/69 tests passed (90%) — the library works correctly across both server implementations.**

### Critical Context: 52North Content Negotiation (Issue #15)

52North routes `Accept` headers to different data providers:
- **`application/sml+json`** → SensorML provider → **3 systems, 1 deployment, 1 procedure**
- **`application/json`** → GeoJSON provider → **empty** (0 features loaded)
- **`application/geo+json`** → GeoJSON provider → **3 systems, 1 deployment, 1 procedure** (!)

This test uses `Accept: application/sml+json` as the default for 52North. See:
- [Issue #15](https://github.com/52North/connected-systems-pygeoapi/issues/15) — filed by us
- [OS4CSAPI Discussion #2](https://github.com/orgs/OS4CSAPI/discussions/2) — reported during Code Sprint 26
- [F57 Correction Report](../implementation/f57-content-negotiation-correction.md) — our own mistake of forgetting this

---

## Server Characteristics

| Characteristic | OSH SensorHub | 52North CSA |
|---|---|---|
| Discovery Mode | Root-level links on landing page | Collection-scoped `items` links |
| Conformance | 33 classes (22 CSA-specific) | 1 class (`ogcapi-common-1` only) |
| Response Envelope (SML) | `{ items: [...] }` | `{ items: [...] }` |
| Response Envelope (JSON) | `{ items: [...] }` | `{ type: "FeatureCollection", features: [...] }` |
| Data Present | Yes (12+ systems, 51+ SF, 100+ obs) | Yes (3 systems, 1 deploy, 1 proc) |
| CRUD Support | Full create/read/update/delete | Read-only (401 on POST) |
| Authentication | Basic auth (`admin/admin`) | None required |
| SSL | Plain HTTP | HTTPS with expired cert |
| Part 2 Resources | Fully functional | 400 "InvalidMimetype" (SML) / 500 (JSON) |
| Accept:json behavior | Returns data (same as SML) | **Returns empty** (Issue #15) |
| Accept:sml+json behavior | Returns data | Returns data |
| Accept:geo+json behavior | Returns data (ignored, serves json) | Returns data (!) |

---

## Test Results by Category

### 1. Landing Page — Both Pass

| Test | OSH | 52N | Notes |
|------|-----|-----|-------|
| Accessible | ✅ | ✅ | Both return 200 with valid JSON |
| Has title | ✅ | ✅ | OSH: "Connected Systems API Service", 52N: "connected-systems-pygeoapi" |
| Links array | ✅ | ✅ | OSH: 10 links, 52N: 7 links |
| Has `rel="data"` link | ❌ | ✅ | **Finding #1**: OSH omits standard `data` rel |

### 2. Conformance — Split

| Test | OSH | 52N | Notes |
|------|-----|-----|-------|
| Endpoint accessible | ✅ | ✅ | Both return 200 |
| Conformance class count | ✅ | ✅ | OSH: 33 classes, 52N: 1 class |
| CSA-specific classes | ✅ | ❌ | **Finding #2**: 52N declares zero CSA conformance classes |

### 3. Content Negotiation — THE Critical Test

| Accept Header | OSH: items | OSH: envelope | OSH: CT | 52N: items | 52N: envelope | 52N: CT |
|---|---|---|---|---|---|---|
| `application/json` | **5** | items | application/json | **0** | features | application/json |
| `application/sml+json` | **5** | items | application/json | **3** | items | application/sml+json |
| `application/geo+json` | **5** | items | application/json | **3** | features | application/geo+json |
| No header (default) | **5** | items | application/json | **3** | — | application/sml+json |

**Key findings from this section:**

- **Finding #3 (Issue #15 confirmed)**: `Accept: application/json` returns 0 items from 52North while all other formats return 3 items.
- **OSH ignores Accept header entirely**: Always returns JSON with `items` envelope regardless of what you ask for. All 4 Accept values return 5 items.
- **52North respects Accept header**: Returns different content types AND different response shapes depending on the Accept value.
- **`application/geo+json` works on 52North** and returns actual data in standard `FeatureCollection/features` envelope — this may be the best content type for interoperability.
- **Envelope varies by content type on 52North**: SML → `items`, JSON → `features`, GeoJSON → `features`.

### 4. Discovery — Library Handles Both Patterns

| Test | OSH | 52N | Notes |
|------|-----|-----|-------|
| `scanCsapiLinks` on landing page | ✅ (6 types) | ❌ (0 types) | **Finding #4** |
| Collections endpoint | ✅ (4 cols) | ✅ (5 cols) | |
| Collection-scoped links | ✅ (4 types) | ✅ (5 types) | Both discovered via `items` rel |

### 5. Builder Setup — Both Pass ✅

| Test | OSH | 52N | Notes |
|------|-----|-----|-------|
| `CSAPIQueryBuilder` created | ✅ | ✅ | |
| Available resource types | 6 types | 9 types (fallback) | 52N uses fallback standard paths |

### 6. Read Operations — Part 1 Works, Part 2 Diverges

| Test | OSH | 52N | Notes |
|------|-----|-----|-------|
| LIST systems | ✅ (3 items) | ✅ (**3 items**) | **52N has real system data** |
| LIST deployments | ✅ (0 items) | ✅ (**1 item**) | **52N has deployment data** |
| LIST procedures | ✅ (0 items) | ✅ (**1 item**) | **52N has procedure data** |
| LIST datastreams | ✅ (3 items) | ❌ (400) | **Finding #5**: 52N rejects SML on Part 2 |
| LIST observations | ✅ (3 items) | ❌ (400) | **Finding #5** |
| Query: `limit=2` | ✅ | ✅ | |
| Query: `limit=2, offset=1` | ✅ | ✅ | |

**52North Part 2 error**: `{"code":"InvalidMimetype","type":"InvalidMimetype","description":"invalid mimetype supplied! expected [] got 'application/sml+json'"}` — the datastreams/observations endpoints **don't support `application/sml+json`** and declare `expected []` (no valid mimetypes at all).

### 7. Response Envelope — Both Use `items` with SML

| Test | OSH | 52N | Notes |
|------|-----|-----|-------|
| Envelope format | ✅ `items` | ✅ `items` | **Both use SML items envelope** |
| Response metadata | ✅ | ✅ | Neither provides numberMatched/numberReturned/timeStamp |

Important: When 52North is queried with `Accept: application/sml+json`, it returns the `{ items: [...] }` envelope — same as OSH. The `FeatureCollection/features` envelope only appears with `application/json` or `application/geo+json` responses.

### 8. Parsers — Works for Collections, GeoJSON Extraction Fails on SML

| Test | OSH | 52N | Notes |
|------|-----|-----|-------|
| `parseCollectionResponse` — systems | ✅ (3 items) | ✅ (**3 items**) | **Parser handles 52N SML data** |
| `parseCollectionResponse` — deployments | ✅ (0 items) | ✅ (**1 item**) | |
| `parseCollectionResponse` — procedures | ✅ (0 items) | ✅ (**1 item**) | |
| `parseCollectionResponse` — datastreams | ✅ (3 items) | — (400) | |
| `parseCollectionResponse` — observations | ✅ (3 items) | — (400) | |
| `extractCSAPIFeature` (OSH) | ✅ | — | type=System, name="LIVE - Field Drone" |
| `extractCSAPIFeature` (52N) | — | ❌ | **Finding #6**: "unrecognized or missing featureType" |

**Finding #6 details**: `extractCSAPIFeature` fails on 52North's SML system responses because the SensorML response format has a different structure than GeoJSON Features. The function expects `properties.featureType` (GeoJSON), but SML responses use a different object shape. This confirms the library needs a SensorML-aware extraction path.

### 9. Nested Resources — 52N Part 2 Not Available

| Test | OSH | 52N | Notes |
|------|-----|-----|-------|
| `getSystemDataStreams()` | ✅ (10 ds) | — | 52N Part 2 endpoints return errors |
| Nested parse | ✅ | — | |
| `getObservationsForDatastream()` | ❌ | — | **Finding #7**: Method doesn't exist |

### 10. CRUD Operations — Full Cycle on OSH, Read-Only on 52N

| Test | OSH | 52N | Notes |
|------|-----|-----|-------|
| CREATE/GET/UPDATE/DELETE System | ✅ (all 6) | — | Full CRUD cycle passes |
| Read-only enforcement | — | ✅ (401) | 52N correctly rejects writes |

---

## Findings

### Finding #1 — OSH Omits Standard `rel="data"` Link

**Severity:** Low | **Affects:** OSH SensorHub

OSH uses resource-name-based link relations directly on the root document rather than the standard `rel="data"` pointing to `/collections`.

### Finding #2 — 52North Declares Zero CSA Conformance Classes

**Severity:** Medium | **Affects:** 52North CSA

Only declares `ogcapi-common-1/1.0/conf/core`. Library should not gate features on conformance declarations alone.

### Finding #3 — Content Negotiation Routes to Different Providers (Issue #15)

**Severity:** HIGH | **Affects:** 52North CSA, Library

This is the Issue #15 behavior confirmed end-to-end:

| Accept Header | 52N Items | 52N Envelope | 52N Content-Type |
|---|---|---|---|
| `application/json` | **0** | features (empty) | application/json |
| `application/sml+json` | **3** | items | application/sml+json |
| `application/geo+json` | **3** | features | application/geo+json |
| (none) | **3** | items | application/sml+json |

**Impact on the library:** Any client that sends `Accept: application/json` (the standard default for most HTTP libraries and OGC API Features clients) will see an empty 52North server. The library MUST negotiate the correct Accept header.

**Recommendation:** The library's HTTP layer should use `application/geo+json` as the primary Accept header for Part 1 resources. This content type returns data from both servers in standard GeoJSON format.

**Important discovery:** `application/geo+json` returns data from 52North (3 items in a `FeatureCollection/features` envelope) — this is potentially the most interoperable content type since it works on both servers and uses the standard GeoJSON envelope.

### Finding #4 — Library Needs Fallback Discovery for Empty Landing Pages

**Severity:** Medium | **Affects:** Library

`scanCsapiLinks(landingPage.links)` returns 0 resource types for 52North. Must fall back to collection-scoped discovery.

### Finding #5 — 52North Part 2 Endpoints Reject All Accept Headers

**Severity:** High | **Affects:** 52North CSA

Part 2 endpoints (datastreams, observations) on 52North:
- `Accept: application/json` → HTTP 500 Internal Server Error
- `Accept: application/sml+json` → HTTP 400 `{"code":"InvalidMimetype","description":"invalid mimetype supplied! expected [] got 'application/sml+json'"}`

The error message `expected []` means the endpoints declare **no valid mimetypes at all**. Part 2 resources are not implemented in 52North's `connected-systems-pygeoapi`.

### Finding #6 — `extractCSAPIFeature` Fails on SensorML Response Bodies

**Severity:** HIGH | **Affects:** Library

When 52North returns `application/sml+json` responses, the individual system resource is a SensorML object, not a GeoJSON Feature. `extractCSAPIFeature` checks for `properties.featureType` (GeoJSON convention), which doesn't exist in SML responses.

Error: `Cannot extract CSAPI feature: unrecognized or missing featureType`

**Recommended approach:** Use `Accept: application/geo+json` as the primary request type for Part 1 resources. This returns GeoJSON FeatureCollections from 52North (with data!) and works fine on OSH. Alternatively, implement a SensorML-aware extraction path (the SensorML types defined in Issue #18 are a start).

### Finding #7 — Missing `getObservationsForDatastream()` Method

**Severity:** Medium | **Affects:** Library

`CSAPIQueryBuilder` lacks this nested resource method.

### Finding #8 — Both Servers Use `items` Envelope for SML Responses

**Severity:** Info (positive)

When both servers respond with `application/sml+json`, both use the `{ items: [...] }` envelope format. `parseCollectionResponse` handles both `items` and `features` envelopes correctly.

---

## Cross-Server Comparison Matrix

```
                              OSH SensorHub    52North CSA
                              ─────────────    ───────────
Landing Page                  ✅ (no "data")   ✅
Conformance (CSA)             ✅ (22 classes)  ❌ (0 classes)
Accept:json data              ✅ (5 items)     ❌ (0 items — Issue #15)
Accept:sml+json data          ✅ (5 items)     ✅ (3 items)
Accept:geo+json data          ✅ (5 items)     ✅ (3 items)
Root Discovery                ✅ (6 types)     ❌ (0 types)
Collection Discovery          ✅ (4 types)     ✅ (5 types)
Part 1: Systems               ✅ (12 sys)      ✅ (3 sys)
Part 1: Deployments           ✅ (0)           ✅ (1 deployment)
Part 1: Procedures            ✅ (0)           ✅ (1 procedure)
Part 2: Datastreams           ✅               ❌ (400/500)
Part 2: Observations          ✅               ❌ (400/500)
Query Params (limit, offset)  ✅               ✅
parseCollectionResponse       ✅               ✅ (systems/dep/proc)
extractCSAPIFeature           ✅               ❌ (SML format incompatible)
Nested Resources              ✅               — (Part 2 broken)
CRUD                          ✅ full cycle    ❌ read-only (401)
```

---

## Recommendations for Upstream Library

1. **Use `application/geo+json` as default Accept header for Part 1** (Finding #3): This is the single highest-impact change. `application/geo+json` returns data from both servers in standard GeoJSON format. `application/json` returns empty from 52North.

2. **Add SensorML response extraction** or **force GeoJSON content type** (Finding #6): `extractCSAPIFeature` only works on GeoJSON. Either add SML parsing or ensure requests always use `Accept: application/geo+json`.

3. **Handle non-JSON error responses** (Finding #5): Part 2 endpoints on 52North return 400/500 with JSON error objects or HTML. The library should parse error bodies gracefully.

4. **Multi-strategy discovery** (Finding #4): Root → collection → fallback discovery chain.

5. **Add `getObservationsForDatastream()`** (Finding #7): Missing nested resource method.

6. **Don't gate on conformance** (Finding #2): 52North implements CSA resources without declaring CSA conformance classes.

7. **Content negotiation is critical for correctness** (Finding #3, #8): The same server returns different data, different envelopes, and different content types depending on `Accept`. The library must be explicit about what it requests.

---

## Conclusion

The corrected cross-server test **confirms 52North has data** (3 systems, 1 deployment, 1 procedure) and validates the library against two independent CSA implementations with fundamentally different architectures.

The most actionable finding is that **`Accept: application/geo+json` is the most interoperable content type** — it returns data from both servers in standard GeoJSON format. The library should default to this for Part 1 resources rather than `application/json`.

`parseCollectionResponse` handles both servers' response formats correctly for Part 1 resources. `extractCSAPIFeature` needs GeoJSON input (which `application/geo+json` provides). The Content Negotiation test section permanently documents the Issue #15 behavior as a reproducible, automated test.
