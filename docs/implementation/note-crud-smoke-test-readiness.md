# Note: CRUD Smoke Test Readiness Assessment

**Date:** February 15, 2026  
**Context:** Question raised during Phase 3.9 about when create/update/delete operations can be added to live server smoke tests.

---

## Key Insight

The current ROADMAP (Phases 1–4, 33 issues) builds a **client library** — URL construction and response parsing layers. There is no HTTP client layer that actually executes `fetch()` calls with POST/PUT/DELETE methods, sets request bodies, or handles response status codes. The smoke tests performed to date are read-only by design (Lesson 10) and use ad-hoc scripts that call `fetch()` directly — they are not part of the library itself.

## What Exists Today

| Layer                                            | Status                    | What It Does                                                          |
| ------------------------------------------------ | ------------------------- | --------------------------------------------------------------------- |
| URL builder (`url_builder.ts`)                   | ✅ Complete               | Produces correct POST/PUT/DELETE target URLs for all 9 resource types |
| Response parsers (SensorML, SWE Common, GeoJSON) | ✅ Complete / In Progress | Parse server responses (JSON → typed objects) — **one-directional**   |
| Smoke tests                                      | ✅ Read-only              | Fetch JSON from live servers via GET, pipe through parsers            |

## What's Missing Before CRUD Smoke Tests

| Prerequisite                   | Status           | Notes                                                                                                                  |
| ------------------------------ | ---------------- | ---------------------------------------------------------------------------------------------------------------------- |
| HTTP client / response handler | ❌ Not built     | Nothing in the codebase calls `fetch()` with POST/PUT/DELETE or handles status codes (201, 204, 400, 404, etc.)        |
| Request body serialization     | ❌ Not built     | Parsers are inbound only (JSON → types). No serializer converts typed objects back to JSON/SensorML for request bodies |
| Dedicated test server          | ❌ Not available | Public demo servers (52North, OSH) are shared infrastructure — write operations would modify other users' data         |
| Phase 4 integration tests      | ❌ Not started   | ROADMAP Phase 4 Task 1 covers fixture-based CRUD workflow tests with mocked `fetch()`                                  |

## Path Forward

1. **Phase 4 Task 1 (next)** — Fixture-based integration tests that mock `fetch()` for CRUD workflows (create → 201, update → 200, delete → 204). Validates request/response plumbing without touching a live server.

2. **Post-Phase 4** — Build the HTTP client layer that wires URL builder + serializer + `fetch()` + response parser into an actual API client.

3. **Then** — Live CRUD smoke tests become meaningful, provided a dedicated test server is available for safe write operations.

## Why This Matters

The URL builder methods like `createSystem()`, `updateSystem(id)`, `deleteSystem(id)` produce URLs — they don't execute requests. The library's current scope is analogous to building a navigation system that can give you directions but doesn't drive the car. The "driving" layer (HTTP client) sits above everything built in Phases 1–4.

---

## Upstream Verification: ogc-client Is Architecturally Read-Only

An audit of the upstream ogc-client codebase confirms that the library has **no write-operation infrastructure whatsoever**. This is not a gap in the CSAPI fork — the upstream was never designed to perform write operations.

### The HTTP layer is hardcoded to GET/HEAD

The sole HTTP utility, `sharedFetch()` in `shared/http-utils.ts`, has this TypeScript signature:

```ts
method: 'GET' | 'HEAD' = 'GET'
```

It literally cannot accept POST/PUT/DELETE/PATCH at the type level. The source code comment reinforces this: _"Note: this should only be used for GET requests!"_

### Every upstream module routes through that single GET-only path

| Module     | HTTP mechanism                                          | Method |
| ---------- | ------------------------------------------------------- | ------ |
| `ogc-api/` | `link-utils.ts` → `sharedFetch(..., 'GET', true)`       | GET    |
| `stac/`    | `link-utils.ts` → `sharedFetch(...)`                    | GET    |
| `tms/`     | `link-utils.ts` → `sharedFetch(..., 'GET', true)`       | GET    |
| `wfs/`     | `endpoint.ts` → `queryXmlDocument(...)` → `sharedFetch` | GET    |
| `wms/`     | (same pattern as WFS via worker)                        | GET    |
| `wmts/`    | (same pattern via worker)                               | GET    |

### No write-method strings exist anywhere in `src/`

A regex search of the entire `src/` tree for `'POST'`, `'PUT'`, `'DELETE'`, `'PATCH'` as string literals returned **zero matches** in actual HTTP call code.

### The one "Post" reference is metadata, not execution

`shared/models.ts` defines `type HttpMethod = 'Get' | 'Post'`, but this is used exclusively by WFS and WMS endpoints to **parse capabilities documents** that report what methods a server supports. The library records this metadata (e.g., "this WFS operation supports Get and Post") but never executes a POST — it always fetches via GET regardless.

Usage is limited to:

- `wfs/endpoint.ts` — `getOperationUrl(operationName, method: HttpMethod = 'Get')` to look up a URL from parsed capabilities
- `wms/endpoint.ts` — same pattern

### Conclusion

The upstream ogc-client is architecturally a **read-only discovery and parsing library**. There is no HTTP client layer for write operations, no request body serialization, and no infrastructure to extend. Adding CRUD execution to the CSAPI fork would be a **net-new capability**, not an extension of something that already exists in the upstream.

### The upstream Vue demo app is also read-only

The upstream includes a Vue demo application (`app/`) that provides a UI for exploring endpoints. It does **not** introduce an independent HTTP client. Every Vue component instantiates a library endpoint class (e.g., `new OgcApiEndpoint(url)`, `new WfsEndpoint(url)`) and calls read-only methods like `.info`, `.allCollections`, `.getFeatureTypes()`. Those endpoint classes internally use `sharedFetch` (GET only). The demo is purely a presentation layer on top of the same read-only library — it adds zero write capability.

---

## How We Know the CRUD Work Is Correct Today

Even without live write-side smoke tests, the CRUD URL builder methods have three layers of verification:

### 1. Unit tests (706 passing)

The URL builder spec (`url_builder.spec.ts`) has dedicated test blocks for every CRUD method across all 9 resource types:

| Method                                                                         | Assertion example                                             |
| ------------------------------------------------------------------------------ | ------------------------------------------------------------- |
| `createSystem()`                                                               | → `https://example.com/collections/iot/systems` (POST target) |
| `updateSystem('sys-001')`                                                      | → `…/systems/sys-001` (PUT target)                            |
| `deleteSystem('sys-001')`                                                      | → `…/systems/sys-001` (DELETE target)                         |
| `createDataStream()`                                                           | → `…/datastreams` (POST target)                               |
| `deleteDataStream('ds-001')`                                                   | → `…/datastreams/ds-001` (DELETE target)                      |
| `createObservation('ds-001')`                                                  | → `…/datastreams/ds-001/observations` (POST target)           |
| `deleteObservation('obs-001')`                                                 | → `…/observations/obs-001` (DELETE target)                    |
| (same pattern for deployments, procedures, sampling features, control streams) |                                                               |

Edge cases are also covered:

- Special character encoding: `urn:example:sys:1` → `urn%3Aexample%3Asys%3A1`
- `EndpointError` thrown when required link relations are missing
- Guard clauses for unavailable sub-resources

### 2. Read-side live smoke tests (already done)

The live smoke tests hit real servers and verify that the URL builder produces GET URLs that return real data, and that the parsers can digest it. This validates the URL construction pattern end-to-end for the read path. Since the CRUD methods use the exact same URL construction logic (same base URL resolution, same path appending, same ID encoding), the read-side validation provides indirect confidence in the write-side URLs.

### 3. What remains untested: write-side round-trip

The gap is that nobody has called `fetch(createSystem(), { method: 'POST', body: ... })` against a live server to confirm a 201 comes back. But that's outside the URL builder's responsibility — it produces the string. Whether the server accepts a POST to that URL depends on the server, the auth configuration, and the request body content.

### Summary

The CRUD URL builder methods are **tested and verified** through unit tests. What cannot be tested today is the full round-trip (send request → receive 201/204 back), because there is no HTTP execution layer and no safe dedicated server to write against. That is a future-layer concern, not a deficiency in the current work.

---

_This note was created to clarify a scope boundary that wasn't immediately obvious from the ROADMAP task descriptions. The ROADMAP Phase 2 tasks list CRUD method names (e.g., `createSystem(body) - POST new system`) which read as if they perform HTTP operations, but they are URL builder methods that return target URL strings._
