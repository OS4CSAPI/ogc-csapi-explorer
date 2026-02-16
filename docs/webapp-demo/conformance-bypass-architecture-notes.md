# Conformance Bypass Architecture Notes

**Date:** 2026-02-16  
**Context:** CSAPI Explorer demo app working with 52North CSA despite missing conformance declarations

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

## Implications

### For the library (upstream concern)

If `OgcApiEndpoint` is the only entry point for consumers, then servers like 52North that implement CSAPI endpoints but don't declare the expected conformance URIs would be completely invisible to the library. This suggests:

- The library could benefit from a duck-typing fallback: if `/systems` returns valid CSAPI GeoJSON, treat the server as CSAPI-capable even without conformance declaration
- Alternatively, the `checkHasConnectedSystems()` function could also check for CSAPI collection `featureType` values (e.g., `system`, `deployment`, `procedure`) as a secondary signal

### For the 52North server

The server arguably has an incomplete conformance declaration. It implements Connected Systems Part 1 endpoints but only declares `ogcapi-common-1` conformance. This is either:
- A bug in the server's conformance response
- An intentional choice because the implementation may not be fully conformant

### For the demo app

The current bypass architecture is **intentional and appropriate** for a demo/testing tool. It validates the library's URL construction, parsing, and data extraction capabilities in isolation, without being blocked by conformance negotiation issues. This separation has been valuable for discovering server quirks (Content-Type: auto, Accept header requirements, etc.) that would be masked by `OgcApiEndpoint`'s gating logic.

## Related Issues

- This finding is related to but distinct from existing issues #5–#17 on ogc-csapi-explorer
- A potential new upstream issue could propose relaxing `checkHasConnectedSystems()` to also detect CSAPI via collection metadata or endpoint probing
