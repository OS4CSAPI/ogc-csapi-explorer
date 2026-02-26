# Phase 1 Implementation Overview

## The Big Picture

The upstream project **ogc-client** is a JavaScript library that helps web developers talk to geospatial servers. It already supports several OGC standards (WFS, WMS, WMTS, OGC API Features, EDR). Our contribution adds support for a new standard: **OGC Connected Systems API (CSAPI)** — which is used for IoT sensor networks and observation systems (think weather stations, traffic sensors, environmental monitors).

Phase 1 is the **foundation layer**. It doesn't fetch live data from servers yet — it builds the machinery needed to construct the right URLs and parse the right data structures when we do.

---

## What Each Piece Does

### 1. Type System (`src/ogc-api/csapi/model.ts`)

This defines the _shape_ of every data object the Connected Systems API can return. Think of it as a dictionary that tells TypeScript: "A `System` looks like this, a `Deployment` looks like this, an `Observation` looks like this."

There are **9 resource types**: System, Deployment, Procedure, SamplingFeature, Property, Datastream, Observation, Command, ControlStream, and CommandStatus. Each is a TypeScript interface with required and optional fields matching the OGC spec.

It also defines **query option types** — what parameters you can use when searching for resources (e.g., filter by bounding box, time range, keyword, limit).

**Why it matters:** Without these types, every consumer of the library would have to guess what fields exist on a response. The types give autocompletion, compile-time error checking, and serve as living documentation.

---

### 2. Helper Utilities (`src/ogc-api/csapi/helpers.ts`)

Six small, pure functions that handle common tasks:

- `formatDateTimeParameter` — Converts JS Date objects or ISO strings into the specific format the CSAPI spec requires for time filters (e.g., `"2024-01-01T00:00:00Z/2024-12-31T23:59:59Z"`)
- `isValidResourceType` / `assertValidResourceType` — Checks if a string like `"systems"` is a real CSAPI resource type
- `encodeResourceId` — Safely URL-encodes an ID for use in a URL path
- `encodeArrayParameter` — Turns `["sys-001", "sys-002"]` into `"sys-001,sys-002"` for query strings
- `validateLimit` / `validateBbox` — Checks that user-supplied parameters are valid before building a URL

**Why it matters:** These prevent bugs. Instead of every piece of code manually formatting dates or encoding IDs, there's one correct implementation that's tested.

---

### 3. Query Builder (`src/ogc-api/csapi/url_builder.ts`)

This is the core class: `CSAPIQueryBuilder`. You give it a collection document (the JSON a server returns describing what it offers), and it figures out:

- **What's the base URL** of this Connected Systems endpoint
- **Which resource types are available** (does this server have systems? datastreams? observations?)

Then you can call methods like:

```typescript
builder.getSystems(); // → "https://server.com/api/collections/iot/systems"
builder.getSystem('sys-001'); // → "https://server.com/api/collections/iot/systems/sys-001"
builder.getSystems({ limit: 10, bbox: [-180, -90, 180, 90] }); // → URL with query params
```

Right now it only has `getSystems()` and `getSystem(id)` as proof-of-concept. Phase 2 will add the remaining resource types (deployments, datastreams, observations, etc.) using the same pattern.

**How it figures out available resources:** It reads the `links` array from the collection document. CSAPI servers advertise their resources via links with specific `rel` values like `"ogc-cs:systems"`, `"ogc-cs:datastreams"`, etc. The builder scans for those link relations and extracts the URLs.

---

### 4. Integration with OgcApiEndpoint

Changes to `src/ogc-api/endpoint.ts`, `src/ogc-api/info.ts`, and `src/index.ts` wire everything together so library consumers can do:

```typescript
const endpoint = new OgcApiEndpoint('https://some-server.com/api');

// Check if the server supports Connected Systems
if (await endpoint.hasConnectedSystems) {
  // Get a query builder for the "iot-sensors" collection
  const builder = await endpoint.csapi('iot-sensors');
  const url = builder.getSystems({ limit: 50 });
}
```

Under the hood, this:

1. Fetches the server's **conformance classes** and checks for the CSAPI URIs
2. Scans all **collections** for ones that have `ogc-cs:*` link relations
3. Exposes `hasConnectedSystems` (boolean) and `csapiCollections` (list of collection names)
4. The `csapi(collectionId)` factory fetches the raw collection document (preserving links) and passes it to `CSAPIQueryBuilder`

---

## How It's Tested

**76 unit tests** across 3 test files, plus **6 integration tests**:

| Test File                        | Tests | What It Verifies                                                                                                                                                                          |
| -------------------------------- | ----- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `model.spec.ts`                  | 27    | Every resource type can be constructed with required fields, optional fields work, type constraints are enforced                                                                          |
| `helpers.spec.ts`                | 30    | Date formatting (single dates, ranges, open-ended), validation (valid/invalid types, limit bounds, bbox length), encoding (special chars, empty arrays)                                   |
| `url_builder.spec.ts`            | 19    | Builder extracts base URL and available resources from a collection doc, generates correct URLs with/without query params, rejects invalid inputs                                         |
| `endpoint.spec.ts` (CSAPI block) | 6     | Full round-trip: mock HTTP responses → endpoint detects CSAPI support → lists CSAPI collections → produces a working builder → caches it → rejects non-CSAPI endpoints with a clear error |

The integration tests use **fixture files** — static JSON files in `fixtures/ogc-api/csapi/` that mimic real server responses. The test setup intercepts HTTP calls (via `globalThis.fetch` mock) and returns these fixtures, so tests run fast with no network.

---

## What It Doesn't Do Yet

- **No actual HTTP fetching of resources** — the builder produces URLs but doesn't call them
- **Only `getSystems()` and `getSystem(id)` work** — other resource types (deployments, observations, etc.) will be added in Phase 2
- **No response parsing** — Phase 3 will add code to fetch a URL and parse the JSON into typed objects
- **No real-time subscriptions** — Phase 4 (WebSocket/MQTT support)

In short: Phase 1 built the **type-safe plumbing** — the vocabulary, the URL construction, and the endpoint detection — so that Phases 2–4 can focus on actually talking to servers and returning data.
