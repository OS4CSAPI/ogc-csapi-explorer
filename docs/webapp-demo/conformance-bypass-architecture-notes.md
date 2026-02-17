# Conformance Bypass Architecture Notes

**Date:** 2026-02-16 (updated with OSH verification results)  
**Context:** CSAPI Explorer demo app working with 52North CSA despite missing conformance declarations; OSH SensorHub verified to have full conformance but different link-relation issue

## The Question

The ogc-client library's `OgcApiEndpoint` class checks the `/conformance` endpoint for specific conformance URIs before exposing functionality. The 52North Connected Systems API demo server (`https://csa.demo.52north.org`) only declares:

```
http://www.opengis.net/spec/ogcapi-common-1/1.0/conf/core
```

It does **not** declare:
- `http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/core`
- `http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/core`
- `http://www.opengis.net/spec/ogcapi-connectedsystems-2/1.0/conf/dynamic-data`

Yet our demo app works with it. How?

## Architecture: Bypassing OgcApiEndpoint

The demo app **does not use** the `OgcApiEndpoint` class at all. Instead, it imports and uses individual lower-level library modules directly:

### What we DON'T use

`OgcApiEndpoint` — the high-level class in `src/ogc-api/endpoint.ts` that:
- Fetches `/conformance` and checks for specific conformance URIs
- Gates `hasFeatures` behind `ogcapi-features-1/1.0/conf/core`
- Gates `hasConnectedSystems` behind `ogcapi-connectedsystems-1/1.0/conf/core` or `ogcapi-connectedsystems-2/1.0/conf/dynamic-data`
- Returns empty results when conformance classes aren't declared

If we instantiated `new OgcApiEndpoint("https://csa.demo.52north.org")`, it would resolve `hasFeatures` → `false`, `hasConnectedSystems` → `false`, and all collection getters would return empty arrays.

### What we DO use

The demo's `csapi-bridge.ts` imports individual library pieces directly:

| Module | Purpose | Conformance check? |
|--------|---------|-------------------|
| `CSAPIQueryBuilder` | URL construction (e.g., `/systems?limit=10`) | None — just builds path strings |
| `scanCsapiLinks()` | Link discovery from landing page and collection documents | None — pattern-matches `rel` attributes |
| `extractCSAPIFeature()` | Typed GeoJSON feature parsing | None — operates on response data |
| `getCSAPIResourceType()` | Resource type identification from `featureType` | None — pattern-matches property values |
| `parseCollectionResponse()` | Collection response parsing | None — parses JSON structure |
| `parseSWEComponent()` | SWE Common schema parsing | None — parses XML/JSON schema |

The demo's own `apiFetch()` in `api.ts` handles HTTP transport: raw `fetch()` with proxy URL prepending, auth headers, and content-type handling.

### Discovery Fallback

In `csapi-bridge.ts`, the `initializeBuilder()` function:

1. Scans landing page and collection links using `scanCsapiLinks()` for CSAPI resource link patterns
2. If CSAPI links are found → uses only those discovered resource types
3. **If no CSAPI links are found** (as with 52North) → **falls back to assuming all 9 standard resource types** exist at their standard paths (`/systems`, `/deployments`, `/procedures`, etc.)

This fallback is what makes 52North work — we optimistically try all standard CSAPI paths and let the server respond with data or errors.

## Critical Finding: Demo Does Not Validate the Public API

This bypass architecture means **the demo app is not using the library the way a real developer would**. A normal consumer of ogc-client would write:

```typescript
import { OgcApiEndpoint } from 'ogc-client';

const endpoint = new OgcApiEndpoint('https://csa.demo.52north.org');

const hasCSAPI = await endpoint.hasConnectedSystems; // → false (blocked by conformance)
const collections = await endpoint.csapiCollections;  // → [] (empty)
```

They would conclude that the server does not support Connected Systems, and never see any resources.

### What this means

1. **Our demo validates parsing/formatting logic** (CSAPIQueryBuilder URL building, GeoJSON extraction, SWE parsing) — which is valuable — but **does not validate the developer experience** of using the library as intended
2. **52North would be completely broken** for any real consumer using `OgcApiEndpoint` as the entry point — they would never discover CSAPI resources
3. **OSH SensorHub does NOT have the same conformance problem** — verified on 2026-02-16 that OSH declares 33 conformance classes including 22 CSAPI-specific ones (see [OSH Verification Results](#osh-sensorhub-verification-results) below). However, OSH has a **different** `OgcApiEndpoint` compatibility issue: its root landing page uses link rel `collections` instead of the OGC API Common rel `data`, which would cause the library's `collectionsUrl` resolution to fail (see details below)
4. This is arguably **the most significant finding** from the demo project, and it is **not captured in any of the existing issues #5–#17**

### Recommended actions

- ~~**Verify** whether OSH SensorHub also fails the `OgcApiEndpoint` conformance check~~ ✅ **Done** (2026-02-16) — OSH passes conformance check but fails at collections discovery due to link rel mismatch (see below)
- **Create a new upstream issue** about `OgcApiEndpoint` being unusable with real CSAPI servers due to two distinct problems: (a) missing conformance declarations (52North) and (b) non-standard root link relations (OSH)
- **Propose** that `checkHasConnectedSystems()` add a duck-typing fallback: if `/conformance` doesn't declare CSAPI classes, probe for CSAPI collections by `featureType` or attempt a request to `/systems` as a secondary signal
- **Propose** that `collectionsUrl` also accept link rel `collections` as a fallback, not just `data` / `http://www.opengis.net/def/rel/ogc/1.0/data`
- **Consider refactoring** part of the demo to also exercise the `OgcApiEndpoint` public API path, so both the intended developer workflow and the internal utilities are validated

## OSH SensorHub Verification Results

**Verified:** 2026-02-16

### Conformance: PASS ✅

OSH SensorHub declares **33 conformance classes**, including **22 CSAPI-specific** ones:

| Category | Classes | Examples |
|---|---|---|
| Part 1 (Core + Resources) | 11 | `core`, `system`, `subsystem`, `deployment`, `subdeployment`, `procedure`, `sf`, `property`, `create-replace-delete`, `geojson`, `sensorml` |
| Part 2 (Dynamic Data) | 8 | `datastream`, `controlstream`, `system-history`, `system-event`, `create-replace-delete`, `json`, `swecommon-json`, `swecommon-text`, `swecommon-binary` |
| Part 3 (Pub/Sub) | 2 | `websocket`, `mqtt` |
| Non-CSAPI (OGC API Common) | 11 | Standard OGC API Common classes |

The library's `checkHasConnectedSystems()` matches on `ogcapi-connectedsystems-1/1.0/conf/core` → returns **`true`**.

### Collections Discovery: FAIL ❌

Despite passing conformance, `csapiCollections` would still return **empty** because of a **link relation mismatch**:

| What the library expects | What OSH provides |
|---|---|
| Root link with rel `data` or `http://www.opengis.net/def/rel/ogc/1.0/data` | Root link with rel `collections` |

OSH's root landing page links:
```
service-desc  → .../openapi-connectedsystems-1.yaml
service-desc  → .../openapi-connectedsystems-2.yaml
conformance   → /sensorhub/api/conformance
collections   → /sensorhub/api/collections       ← rel is "collections", not "data"
systems       → /sensorhub/api/systems
deployments   → /sensorhub/api/deployments
procedures    → /sensorhub/api/procedures
samplingFeatures → /sensorhub/api/samplingFeatures
datastreams   → /sensorhub/api/datastreams
observations  → /sensorhub/api/observations
```

The library's `collectionsUrl` getter in `endpoint.ts` uses `getLinkUrl(root, ['data', 'http://www.opengis.net/def/rel/ogc/1.0/data'])` — it does **not** check for rel `collections`. So `collectionsUrl` resolves to `null`, `data` resolves to `null`, and `csapiCollections` returns `[]`.

### Net Result

| Check | 52North | OSH SensorHub |
|---|---|---|
| `hasConnectedSystems` | `false` (no CSA conformance classes) | `true` (22 CSA classes) |
| `collectionsUrl` | Possibly works (untested, server SSL expired) | `null` (rel `collections` not `data`) |
| `csapiCollections` | `[]` (blocked at conformance gate) | `[]` (blocked at collections URL gate) |
| **End result** | ❌ Unusable | ❌ Unusable (different reason) |

Both servers fail `OgcApiEndpoint` but for **completely different reasons**:
- **52North**: Conformance gate blocks everything (the server doesn't declare CSA classes)
- **OSH**: Conformance passes but collections discovery fails (the server uses non-standard link relations)

---

## Implications

### For the library (upstream concern)

`OgcApiEndpoint` is currently unusable with **both** real CSAPI servers tested, but for different reasons:

1. **Conformance gating** (affects 52North): Servers that implement CSAPI but don't declare conformance URIs are invisible. The library could benefit from a duck-typing fallback: if `/systems` returns valid CSAPI GeoJSON, treat the server as CSAPI-capable even without conformance declaration
2. **Collections URL resolution** (affects OSH): The library only looks for link rel `data` to find `/collections`, but OSH uses rel `collections`. The `collectionsUrl` getter should also check for rel `collections` as a fallback
3. Alternatively, the `checkHasConnectedSystems()` function could also check for CSAPI collection `featureType` values (e.g., `system`, `deployment`, `procedure`) as a secondary signal

### For the 52North server

The server arguably has an incomplete conformance declaration. It implements Connected Systems Part 1 endpoints but only declares `ogcapi-common-1` conformance. This is either:
- A bug in the server's conformance response
- An intentional choice because the implementation may not be fully conformant

### For the OSH SensorHub server

OSH has excellent conformance coverage (33 classes, 22 CSAPI-specific) but uses link rel `collections` instead of the OGC API Common-specified `data`/`http://www.opengis.net/def/rel/ogc/1.0/data` relation. This is likely a minor spec compliance gap since the actual `/collections` endpoint works correctly — it's just advertised under a different rel attribute.

### For the demo app

The current bypass architecture is **intentional and appropriate** for a demo/testing tool. It validates the library's URL construction, parsing, and data extraction capabilities in isolation, without being blocked by conformance negotiation issues. This separation has been valuable for discovering server quirks (Content-Type: auto, Accept header requirements, etc.) that would be masked by `OgcApiEndpoint`'s gating logic.

However, the demo should ideally also exercise the `OgcApiEndpoint` path to validate the complete intended developer workflow.

## Related Issues

- This finding is related to but distinct from existing issues #5–#20 on ogc-csapi-explorer
- **52North conformance gap**: Documented as S-3 in [server-observations-gap-analysis.md](./server-observations-gap-analysis.md) — this is a server-side issue (52North's responsibility)
- **OSH link relation mismatch**: New finding from the 2026-02-16 verification — this is both a server-side spec compliance gap (OSH uses `collections` instead of `data`) and a library resilience gap (library should accept both)
- **Library resilience**: Two potential upstream improvements: (a) duck-typing fallback for conformance detection, (b) accept `collections` rel as alternative to `data` rel
- These are upstream concerns — the conformance issue belongs to the respective server teams, and the library resilience improvements belong to the camp-to-camp/ogc-client upstream
