# CSAPI Library — Consolidated Findings for Upstream Review

> **Date**: 2026-02-16  
> **Source**: End-to-end validation of the CSAPI library against two live Connected Systems API servers  
> **Tested Against**: OSH SensorHub (`http://45.55.99.236:8080/sensorhub/api`) and 52North CSA (`https://csa.demo.52north.org`)  
> **Library Code**: `src/ogc-api/csapi/` — `url_builder.ts`, `helpers.ts`, `model.ts`, `formats/response.ts`, `formats/geojson.ts`  
> **Test Artifacts**: `examples/e2e-cross-server.ts`, `examples/e2e-write-results.json`, `examples/e2e-nested-results.json`

---

## Executive Summary

We built a demo webapp (Vue 3 + Vite + PrimeVue) that exercises the CSAPI library against two independent live servers — OSH SensorHub (full CRUD) and 52North CSA (read-only). This produced **62/69 cross-server tests passing** and **14/15 write-operation tests passing**, along with a comprehensive library integration via a bridge module.

This document consolidates every finding from 6 separate test reports into a single deduplicated reference, organized by priority for the upstream contribution.

**Finding counts by category:**
| Category | Count | Summary |
|----------|-------|---------|
| Library bugs to fix | 5 | Wrong URLs, missing methods, parser gaps, content negotiation |
| Design improvements | 7 | API ergonomics, type narrowing, helpers, discovery strategy |
| Already resolved | 1 | EndpointError XML dependency isolation |
| Server-side observations | 7 | Not library bugs, but useful context for documentation |
| Working correctly | 9 | Positive validations of library behavior |

---

## Category 1: Library Bugs (Must Fix)

### F-1. `createDataStream()` Generates Wrong URL

| | |
|---|---|
| **Severity** | High |
| **Affected Method** | `CSAPIQueryBuilder.createDataStream()` |
| **Generated URL** | `/datastreams` (top-level collection) |
| **Expected URL** | `/systems/{systemId}/datastreams` (nested under parent system) |
| **Server Response** | `405 Method Not Allowed: "Datastreams can only be created within a System resource"` |
| **Spec Reference** | OGC 23-002, §7.2 — Datastreams are created as sub-resources of Systems |
| **Evidence** | E2E write operations test, Suite 2 Phase 2 |

Per the CSA specification and confirmed by server behavior, datastream creation requires a POST to the nested endpoint under a parent system. The top-level `/datastreams` collection only supports GET (listing).

**Workaround**: Use `getSystemDataStreams(systemId)` as the POST target URL. This generates the correct path but is semantically named as a GET operation.

**Recommendation**: Add `createDataStreamForSystem(systemId: string): string`. See also F-2 for the full set of missing nested create methods.

---

### F-2. Missing Nested Create Methods

| | |
|---|---|
| **Severity** | Medium |
| **Type** | API gap — inconsistency in method coverage |
| **Evidence** | E2E write operations test, cross-server test |

The library provides nested **listing** methods but not nested **creation** methods for resource types that can only be created as sub-resources:

| Listing Method (exists) | Creation Method (missing) | URL Pattern |
|-------------------------|--------------------------|-------------|
| `getSystemDataStreams(id)` | `createDataStreamForSystem(id)` | `POST /systems/{id}/datastreams` |
| `getSystemControlStreams(id)` | `createControlStreamForSystem(id)` | `POST /systems/{id}/controlstreams` |
| `getSystemSamplingFeatures(id)` | `createSamplingFeatureForSystem(id)` | `POST /systems/{id}/samplingFeatures` |
| *(none)* | `getObservationsForDatastream(id)` | `GET /datastreams/{id}/observations` |

Note: `createObservation(datastreamId)` and `createCommand(controlStreamId)` already follow the nested pattern correctly — making this inconsistency more visible.

**Recommendation**: Add the four missing methods. Consider deprecating or documenting `createDataStream()` (which generates the top-level URL that servers reject).

---

### F-3. `extractCSAPIFeature()` Only Works for GeoJSON Features

| | |
|---|---|
| **Severity** | High |
| **Affected Functions** | `extractCSAPIFeature()`, `getCSAPIResourceType()` |
| **Root Cause** | Requires `properties.featureType` (GeoJSON convention) |
| **Evidence** | Library integration, E2E write operations, cross-server test |

This function fails in two distinct scenarios:

**Scenario A — 52North SML responses**: When 52North returns `application/sml+json`, systems are flat objects:
```json
{
  "type": "PhysicalSystem",
  "id": "5400-526",
  "label": "Doppler Current Profiler Sensor",
  "definition": "sosa:Sensor"
}
```
No `properties.featureType` exists. The information is available via `definition` and `type` at the top level, but the library doesn't look there.

**Scenario B — Part 2 resources**: Datastreams, observations, control streams, and commands are not GeoJSON Features and have no `featureType`. This is by design, but underdocumented.

**Recommendation**: Either:
1. Use `Accept: application/geo+json` as the default request type for Part 1 resources (this returns GeoJSON from 52North with data, and works on OSH unchanged) — **this is the preferred approach**, or
2. Add a SensorML-aware extraction path that checks `definition`/`type` at the top level, or
3. At minimum, document that `extractCSAPIFeature()` requires GeoJSON Feature format and list Part 2 as explicitly unsupported.

---

### F-4. Content Negotiation: `application/json` Returns Empty from 52North

| | |
|---|---|
| **Severity** | High |
| **Type** | Library HTTP layer must set correct Accept header |
| **Evidence** | Cross-server test (Content Negotiation phase), Issue #15 |

This is the single most impactful interoperability finding. The 52North server routes requests to different internal providers based on the `Accept` header:

| Accept Header | 52N Items | 52N Envelope | 52N Content-Type |
|---|---|---|---|
| `application/json` | **0** | features (empty FeatureCollection) | application/json |
| `application/sml+json` | **3** | items | application/sml+json |
| `application/geo+json` | **3** | features (populated FeatureCollection) | application/geo+json |
| *(none / default)* | **3** | items | application/sml+json |

On OSH SensorHub, all Accept headers return the same data (5 items).

**Impact**: Any client that sends `Accept: application/json` (the standard default for most HTTP libraries) will see an empty 52North server. The library's HTTP layer must negotiate the correct Accept header.

**Recommendation**: The library should use `application/geo+json` as the default Accept header for Part 1 resource requests. This content type:
- Returns data from **both** servers
- Uses the standard GeoJSON envelope (`FeatureCollection`/`features`)
- Is compatible with `extractCSAPIFeature()` and `parseCollectionResponse()`
- Is the OGC-specified response format for Part 1 resources

---

### F-5. Pre-Existing Bug: `ogc-api/endpoint.ts` Line 74

| | |
|---|---|
| **Severity** | Low |
| **Type** | Error type mismatch |
| **Evidence** | Discovered during EndpointError isolation test runs |

The `root` getter in `ogc-api/endpoint.ts` throws `new Error(...)` on line 74, but the corresponding test at `endpoint.spec.ts:1789` expects `new EndpointError(...)`. The production code should use `EndpointError` to match the test expectation and the library's error hierarchy.

This is pre-existing (not introduced by our work) and technically outside the CSAPI contribution scope, but it's an easy one-line fix if touched during the upstream PR.

---

## Category 2: Library Design Improvements (Should Address)

### F-6. `EndpointError` Transitive XML Dependency — RESOLVED

| | |
|---|---|
| **Severity** | High (was) → Resolved |
| **Resolution** | Commit `e73cff8` |
| **Files Changed** | 18 files, +44 −28 lines |

`CSAPIQueryBuilder` imported `EndpointError` from `shared/errors.ts`, which transitively imported `@rgrove/parse-xml` (an XML parsing library) via `ServiceExceptionError`. This meant **any code importing CSAPIQueryBuilder pulled in an XML parser**, even though CSAPI is a JSON-only API.

**What we did**: Extracted `EndpointError` into `src/shared/endpoint-error.ts` (23 lines, zero imports). Updated 14 files across CSAPI, OGC API, and STAC modules to import from the new location. Added a backward-compatible re-export in `errors.ts`.

**Verification**: 317 unit tests pass (19 in errors.spec + 298 in url_builder.spec). Demo app builds without the `@rgrove/parse-xml` Vite alias workaround.

**Important detail**: The re-export in `errors.ts` must use `import { EndpointError } from './endpoint-error.js'; export { EndpointError };` (two statements). A direct `export { X } from 'y'` re-export does NOT create a local binding — `encodeError()` and `decodeError()` in the same file would get `ReferenceError` at runtime.

**Broader impact**: This fix benefits not just CSAPI consumers, but also OGC API Features and STAC consumers — all JSON-only protocols that previously had an unnecessary transitive XML dependency through `EndpointError`.

---

### F-7. No Generic CRUD Method for Dynamic-Type Consumers

| | |
|---|---|
| **Severity** | Medium |
| **Type** | API ergonomics |
| **Evidence** | Library integration (bridge module required 5 switch/case dispatchers) |

The library provides 77+ type-specific methods (`getSystems()`, `getDeployments()`, etc.) with excellent TypeScript type safety. However, any consumer working with resource types dynamically (UI frameworks, CLI tools, admin panels) needs boilerplate dispatchers:

```typescript
function getListUrl(type: string, options: QueryOptions): string {
  switch (type) {
    case 'systems': return builder.getSystems(options);
    case 'deployments': return builder.getDeployments(options);
    // ... 7 more cases
  }
}
```

Our bridge module required this pattern for list, detail, create, update, and delete — five dispatchers.

**Recommendation**: Add a `getResources(type: CSAPIResourceType, options?: QueryOptions)` convenience method alongside the type-specific methods. It would lose the type-specific query option extensions but cover the common case. The type-specific methods remain for consumers who know the type at compile time.

---

### F-8. `OgcApiCollectionInfo` Overly Broad for Constructor

| | |
|---|---|
| **Severity** | Medium |
| **Type** | API ergonomics |
| **Evidence** | Library integration (synthetic collection workaround) |

`CSAPIQueryBuilder`'s constructor requires an `OgcApiCollectionInfo` object (from `src/ogc-api/model.ts`), which is a large interface with many fields (`id`, `title`, `links`, `extent`, etc.). The constructor only uses `id`, `title`, and `links`.

Consumers creating a builder outside of `OgcApiEndpoint` (a valid use case for proxy/gateway scenarios) must either provide a full object with dummy data for unused fields, or use `as OgcApiCollectionInfo` type assertion.

**Recommendation**: Accept `Pick<OgcApiCollectionInfo, 'id' | 'title' | 'links'>` or create a dedicated `CSAPIBuilderOptions` interface.

---

### F-9. `extractCSAPIFeature()` Union Return Type Causes TypeScript Friction

| | |
|---|---|
| **Severity** | Medium |
| **Type** | TypeScript ergonomics |
| **Evidence** | Library integration (ResourceDetail component) |

The function returns `System | Deployment | Procedure | SamplingFeature`. The `validTime` property exists on `System`, `Deployment`, and `SamplingFeature` but NOT on `Procedure`. TypeScript correctly prevents accessing `typedResource.properties.validTime` because the type could be `Procedure`.

Consumers must use `as any` casts:
```typescript
<span v-if="(typedResource.properties as any)?.validTime">
  {{ (typedResource.properties as any).validTime.start.toISOString() }}
</span>
```

**Recommendation**: Add type-narrowing guards: `isSystem(r): r is System`, `isDeployment(r): r is Deployment`, etc. This lets consumers narrow the union type safely without `as any`.

---

### F-10. No Content-Type Guidance from the Builder

| | |
|---|---|
| **Severity** | Medium |
| **Type** | Missing helper |
| **Evidence** | Library integration, E2E write operations |

The builder constructs URLs for write operations but provides no guidance on the required `Content-Type` header. The CSA spec requires:
- Part 1 resources (systems, deployments, procedures, samplingFeatures): `application/geo+json`
- Part 2 resources (datastreams, observations, controlStreams, commands): `application/json`

Sending the wrong Content-Type results in 400 or 415 errors.

**Recommendation**: Add a constant map and/or helper:
```typescript
export const CSAPI_CONTENT_TYPES: Record<CSAPIResourceType, string> = {
  systems: 'application/geo+json',
  deployments: 'application/geo+json',
  procedures: 'application/geo+json',
  samplingFeatures: 'application/geo+json',
  properties: 'application/geo+json',
  datastreams: 'application/json',
  observations: 'application/json',
  controlStreams: 'application/json',
  commands: 'application/json',
};
```

---

### F-11. Resource Discovery Depends on Server Link Quality

| | |
|---|---|
| **Severity** | Medium |
| **Type** | Robustness gap |
| **Evidence** | Library integration, cross-server test |

`assertResourceAvailable()` throws `EndpointError` for servers that don't advertise CSAPI link relations, even if the resources actually exist at standard paths. `scanCsapiLinks()` returns:
- **OSH SensorHub root**: 6 resource types discovered
- **52North root**: 0 resource types discovered (links present but not in recognized CSAPI format)
- **52North collections**: 5 resource types discovered

The OGC spec does not require servers to include CSAPI-specific link relations in the landing page.

**Recommendation**:
1. Implement multi-strategy discovery: root links → collection links → well-known paths fallback
2. Document that `availableResources` reflects *advertised* links, not *actual* capabilities
3. Consider `assumeAllResourcesAvailable()` option or `tryGetSystems()` methods that return `null` instead of throwing

---

### F-12. No Location Header Parsing Helper

| | |
|---|---|
| **Severity** | Low |
| **Type** | Missing convenience |
| **Evidence** | E2E write operations |

On successful creation (201), servers return an empty response body with a `Location` header containing the path to the created resource (e.g., `/systems/043g`). The resource ID must be extracted from the last path segment. This is standard OGC API behavior, but the library provides no helper for it.

**Recommendation**: Consider a `parseLocationHeader(header: string): { resourceType: string, id: string }` utility. Low priority — consumers can easily implement this themselves.

---

## Category 3: Server-Side Observations (Not Library Bugs)

These findings document real server behaviors that affect library consumers but are not bugs in the library itself. They should inform documentation and defensive coding.

### S-1. OSH SensorHub: No REST Datastream Creation

OSH rejects `POST /systems/{id}/datastreams` for **all** Content-Types tested (7 types including `application/json`, `application/geo+json`, `application/swe+json`, `application/sml+json`). Response: `400 "Unsupported format"`. Datastreams are auto-generated by internal sensor drivers, not created via REST.

### S-2. OSH SensorHub: Live Datastreams Are Read-Only

`POST /datastreams/{id}/observations` returns `400 "Resource is not writable"`. Existing datastreams are sensor-driven and marked read-only.

### S-3. 52North: Declares Zero CSA Conformance Classes

52North only declares `ogcapi-common-1/1.0/conf/core`. It implements CSA resources (3 systems, 1 deployment, 1 procedure) without declaring CSA conformance. **Library should not gate features on conformance declarations alone.**

### S-4. 52North: Part 2 Endpoints Return 400/500

Datastreams and observations are not implemented. Requests return:
- `Accept: application/json` → HTTP 500 Internal Server Error
- `Accept: application/sml+json` → HTTP 400 `"expected [] got 'application/sml+json'"`

### S-5. OSH SensorHub: Omits Standard `rel="data"` Link

OSH uses resource-name-based link relations directly on the root document rather than the standard `rel="data"` pointing to `/collections`.

### S-6. 52North: SSL Certificate Expired

Requires `NODE_TLS_REJECT_UNAUTHORIZED=0` (Node.js) or `secure: false` (Vite proxy) to connect. Browsers refuse direct connection.

### S-7. 52North: Write Preflight CORS Fails

Missing `Access-Control-Allow-Methods` and `Access-Control-Allow-Headers` in OPTIONS preflight responses. Browser blocks all POST/PUT/DELETE. Proxy required for write operations.

---

## Category 4: Working Correctly (Positive Validations)

These are explicit confirmations that library features work as designed against real servers.

| # | Feature | Status | Detail |
|---|---------|--------|--------|
| V-1 | `resourceUrls` Map | ✅ | Works for relative/proxy paths without modification |
| V-2 | `scanCsapiLinks()` | ✅ | All 3 link conventions recognized (ogc-cs: prefix, plain name, items href). `featuresOfInterest` → `samplingFeatures` normalization works. |
| V-3 | `parseCollectionResponse()` | ✅ | Handles both `FeatureCollection`/`features` and `items` envelopes. Tested against all accessible resource types on both servers. Empty collections return 0 items without error. |
| V-4 | `buildQueryString()` | ✅ | Correct encoding, validation (bbox 4 elements, limit positive), temporal formatting. `?limit=10&q=drone` and `?limit=5&bbox=-180,-90,180,90` produce valid responses on both servers. |
| V-5 | `parseValidTime()` | ✅ | Handles array format `["2026-01-26T18:32:01.56Z", "now"]` and object format `{ start, end }`. `"now"` sentinel → `end: undefined`. |
| V-6 | CRUD URL symmetry | ✅ | `createSystem()` = `getSystems()` (collection URL for POST). `updateSystem(id)` = `getSystem(id)` (resource URL for PUT). Correct OGC API pattern for all tested operations. |
| V-7 | Nested creation | ✅ | `createObservation(datastreamId)` → `/datastreams/{id}/observations`. `createCommand(controlStreamId)` → `/controlStreams/{id}/commands`. Parent ID is required (not optional). |
| V-8 | Strict TypeScript | ✅ | All CSAPI modules compile with zero errors under `strict: true` + `noUnusedLocals` + `noUnusedParameters`. |
| V-9 | `items` envelope interop | ✅ | Both servers use `{ items: [...] }` for SML responses. `parseCollectionResponse` handles both `items` and `features` envelopes correctly regardless of server. |

---

## Cross-Server Comparison Matrix

```
                                OSH SensorHub    52North CSA
                                ─────────────    ───────────
Landing Page                    ✅ (no "data")   ✅
Conformance (CSA classes)       ✅ (22 classes)  ❌ (0 classes)
Accept:json data                ✅ (5 items)     ❌ (0 items — F-4)
Accept:sml+json data            ✅ (5 items)     ✅ (3 items)
Accept:geo+json data            ✅ (5 items)     ✅ (3 items)
Root Link Discovery             ✅ (6 types)     ❌ (0 types — F-11)
Collection Discovery            ✅ (4 types)     ✅ (5 types)
Part 1: Systems                 ✅ (12 sys)      ✅ (3 sys)
Part 1: Deployments             ✅ (0)           ✅ (1)
Part 1: Procedures              ✅ (0)           ✅ (1)
Part 2: Datastreams             ✅               ❌ (400/500 — S-4)
Part 2: Observations            ✅               ❌ (400/500 — S-4)
Query Params (limit, offset)    ✅               ✅
parseCollectionResponse         ✅               ✅ (Part 1 only)
extractCSAPIFeature             ✅               ❌ (SML format — F-3)
Nested Resources                ✅               — (Part 2 broken)
CRUD                            ✅ full cycle    ❌ read-only (401)
```

---

## OSH SensorHub CRUD Support Matrix (E2E Verified)

| Operation | Systems | Deployments | Procedures | Datastreams | Observations |
|-----------|---------|-------------|------------|-------------|--------------|
| **LIST** (GET) | ✅ 200 | ✅ 200 | ✅ 200 | ✅ 200 | ✅ 200 |
| **GET** (by ID) | ✅ 200 | — | — | ✅ 200 | ✅ 200 |
| **CREATE** (POST) | ✅ 201 | ✅ 201 | ✅ 201 | ❌ 400/405 | ❌ 400 |
| **UPDATE** (PUT) | ✅ 204 | — | — | — | — |
| **DELETE** | ✅ 204 | ✅ 204 | ✅ 204 | — | — |

Key: ✅ = tested & working, ❌ = tested & rejected (server limitation), — = not tested (URL generation confirmed correct)

---

## Priority Ranking for Upstream PR

### Before Submitting

| Priority | Finding | Effort | Impact |
|----------|---------|--------|--------|
| 1 | **F-4**: Default to `Accept: application/geo+json` for Part 1 | Low | High — fixes empty-server illusion |
| 2 | **F-1 + F-2**: Add nested create methods, fix `createDataStream()` | Low | High — unblocks write operations |
| 3 | **F-6**: EndpointError isolation (already done) | Done | High — eliminates XML dep for all JSON consumers |
| 4 | **F-3**: Document `extractCSAPIFeature()` GeoJSON requirement | Low | Medium — prevents consumer confusion |
| 5 | **F-11**: Multi-strategy resource discovery | Medium | Medium — improves real-server compatibility |

### Should Address

| Priority | Finding | Effort | Impact |
|----------|---------|--------|--------|
| 6 | **F-10**: Content-Type helper/constant | Low | Medium |
| 7 | **F-7**: Generic CRUD method | Medium | Medium |
| 8 | **F-8**: Narrow constructor parameter type | Low | Low |
| 9 | **F-9**: Type-narrowing guards | Low | Low |
| 10 | **F-12**: Location header helper | Low | Low |
| 11 | **F-5**: Fix `endpoint.ts` line 74 Error→EndpointError | Low | Low |

---

## Test Evidence Summary

| Test Suite | Results | Coverage |
|------------|---------|----------|
| Cross-server (both servers) | **62/69 passed** | Discovery, content negotiation, Part 1 read, Part 2 read, parsers, query params, CRUD |
| Write operations (OSH only) | **14/15 passed** (Suite 1), **3/8 passed** (Suite 2) | Full CRUD lifecycle, nested creation, parser validation |
| Unit tests (post-refactor) | **298/298** url_builder, **19/19** errors | EndpointError isolation verification |

The 7 cross-server failures are: 52N Part 2 endpoints (server-side, S-4), `extractCSAPIFeature` on SML (F-3), write operations on read-only server (expected). The 1 write-operations failure is `createDataStream()` wrong URL (F-1). The 5 Suite 2 failures are: OSH REST datastream creation unsupported (S-1), test script bugs, and Part 2 parser limitation (F-3).

---

## Files Changed by This Validation Effort

### Library Source (submitted upstream)

| File | Change | Finding |
|------|--------|---------|
| `src/shared/endpoint-error.ts` | **NEW** — 23 lines, zero-dependency EndpointError | F-6 |
| `src/shared/errors.ts` | Class → import + re-export | F-6 |
| `src/index.ts` | Export rerouted | F-6 |
| 14 consumer files | Import path `errors.js` → `endpoint-error.js` | F-6 |

### Test & Validation (evidence, not submitted upstream)

| File | Purpose |
|------|---------|
| `examples/e2e-cross-server.ts` | Automated cross-server test script |
| `examples/e2e-write-results.json` | Write operations test output |
| `examples/e2e-nested-results.json` | Nested creation test output |
| `demo/` directory | Full demo webapp exercising library end-to-end |

---

## Appendix A: Content Negotiation Reference

Complete test results for all Accept headers tested against both servers' `/systems?limit=5` endpoints:

| Accept Header | OSH Items | OSH Envelope | 52N Items | 52N Envelope |
|---|---|---|---|---|
| `application/json` | 5 | items | **0** | features (empty) |
| `application/sml+json` | 5 | items | 3 | items |
| `application/geo+json` | 5 | items | 3 | features |
| *(none)* | 5 | items | 3 | items |

**Conclusion**: `application/geo+json` is the only Accept header that returns data from both servers in a standard GeoJSON envelope. It should be the library's default for Part 1 resources.

## Appendix B: Finding Cross-Reference

Maps each finding in this document back to its source report(s):

| Finding | Source Report(s) |
|---------|-----------------|
| F-1 | E2E Write Operations #1 |
| F-2 | E2E Write Operations #4, Cross-Server #7 |
| F-3 | Library Integration #9, E2E Write Operations #5, Cross-Server #6 |
| F-4 | Cross-Server #3 (Issue #15) |
| F-5 | EndpointError Isolation Report, Finding F |
| F-6 | Library Integration #15, EndpointError Isolation Report |
| F-7 | Library Integration #2 |
| F-8 | Library Integration #3 |
| F-9 | Library Integration #10 |
| F-10 | Library Integration #14, E2E Write Operations #6 |
| F-11 | Library Integration #5, Cross-Server #4 |
| F-12 | E2E Write Operations #8 |
| S-1 | E2E Write Operations #2 |
| S-2 | E2E Write Operations #3 |
| S-3 | Cross-Server #2 |
| S-4 | Cross-Server #5 |
| S-5 | Cross-Server #1 |
| S-6 | CORS Preflight Test |
| S-7 | CORS Preflight Test |
| V-1 through V-9 | Library Integration #1,4,6,7,11,12,13,16; Cross-Server #8 |
