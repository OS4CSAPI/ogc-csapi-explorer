# Phase 2.1 Implementation Overview — Where We Stand Now

## The Story So Far

In Phase 1 we built the **foundation**: a type system for every Connected Systems data structure, helper utilities for encoding and validation, a stub query builder that could produce URLs for just two operations (`getSystems` and `getSystem`), and the integration that wired all of this into the existing `OgcApiEndpoint` class.

Phase 2.1 (Issue #5) took that stub and turned it into a **complete Systems API surface**. The query builder now supports every operation the OGC spec defines for the Systems resource — reading, writing, history, hierarchy, and cross-resource navigation — all expressed as type-safe URL construction methods.

---

## What Changed

### Before (Phase 1)

The query builder had exactly **2 methods**:

```typescript
builder.getSystems(); // list systems
builder.getSystem('sys-001'); // get one system
```

That was enough to prove the architecture worked: the builder could discover available resources from a collection document, construct URLs with query parameters, and validate everything along the way.

### After (Phase 2.1)

The query builder now has **12 methods** — the full Systems surface:

```typescript
// ── Reading ──
builder.getSystems({ limit: 10, bbox: [-180, -90, 180, 90] });
builder.getSystem('sys-001');

// ── Writing ──
builder.createSystem(); // URL for POST
builder.updateSystem('sys-001'); // URL for PUT
builder.deleteSystem('sys-001'); // URL for DELETE

// ── History ──
builder.getSystemHistory('sys-001', { limit: 5 });

// ── Hierarchy ──
builder.getSystemSubsystems('sys-001', { recursive: true });

// ── Cross-resource navigation ──
builder.getSystemDataStreams('sys-001');
builder.getSystemControlStreams('sys-001');
builder.getSystemSamplingFeatures('sys-001');
builder.getSystemDeployments('sys-001');
builder.getSystemProcedures('sys-001');
```

---

## What Each Operation Does (In Plain English)

### Reading — `getSystems` and `getSystem`

These existed in Phase 1. `getSystems` builds a URL to list all systems in a collection, with optional filtering by location (bbox), time (datetime), keyword (q), or Systems-specific criteria (parent, procedureId, foiId, observedPropertyId, controlledPropertyId, recursive). `getSystem` builds a URL to fetch a single system by its ID.

### Writing — `createSystem`, `updateSystem`, `deleteSystem`

These produce the **target URLs** for write operations. They don't perform the HTTP request themselves — the builder's job is URL construction, and the actual fetch will come in a later phase. But the pattern is:

- `createSystem()` → returns `https://server.com/…/systems` (you'd POST a System JSON body to this URL)
- `updateSystem('sys-001')` → returns `https://server.com/…/systems/sys-001` (you'd PUT a replacement body here)
- `deleteSystem('sys-001')` → returns `https://server.com/…/systems/sys-001` (you'd send a DELETE here)

Note that `updateSystem` and `deleteSystem` produce the _same_ URL — the HTTP verb is what distinguishes them. Having separate methods keeps the intent clear in consuming code and allows us to attach different validation or query parameters to each one later if the spec evolves.

### History — `getSystemHistory`

Connected Systems tracks **version history** of systems. When a system's metadata changes (e.g., it gets recalibrated or relocated), previous versions are preserved. `getSystemHistory('sys-001')` builds the URL to list those historical versions, and you can filter with `limit`, `offset`, `datetime`, etc.

### Hierarchy — `getSystemSubsystems`

Systems can contain other systems. A weather station (parent) might contain a temperature sensor, a wind gauge, and a humidity probe (subsystems). `getSystemSubsystems('sys-001')` lists the direct children. Passing `{ recursive: true }` includes children-of-children at all levels.

The `recursive` parameter is unique to Systems — it's defined on `SystemQueryOptions` but not on the base `QueryOptions`. The builder serializes it correctly as a boolean query parameter.

### Cross-resource navigation

A system doesn't exist in isolation. It produces data (DataStreams), can be controlled (ControlStreams), monitors locations (SamplingFeatures), follows procedures (Procedures), and is deployed at sites (Deployments). These six navigation methods build URLs for those **nested sub-resources**:

| Method                      | URL Pattern                      | What It Returns                            |
| --------------------------- | -------------------------------- | ------------------------------------------ |
| `getSystemDataStreams`      | `/systems/{id}/datastreams`      | Observation data channels from this system |
| `getSystemControlStreams`   | `/systems/{id}/controlstreams`   | Command/control channels to this system    |
| `getSystemSamplingFeatures` | `/systems/{id}/samplingFeatures` | Physical locations this system monitors    |
| `getSystemDeployments`      | `/systems/{id}/deployments`      | Where/when this system has been deployed   |
| `getSystemProcedures`       | `/systems/{id}/procedures`       | Methodologies this system follows          |
| `getSystemSubsystems`       | `/systems/{id}/subsystems`       | Child systems (hierarchy)                  |

All of these accept optional `QueryOptions` for filtering and pagination.

---

## How The Architecture Works

### The URL Construction Pipeline

Every public method follows the exact same 3-step pattern:

```
1. assertResourceAvailable('systems')    ← throws if server doesn't offer this resource
2. buildResourceUrl(type, id?, sub?, options?)  ← assembles the path
3. buildQueryString(options)             ← serializes filters into ?key=value pairs
```

Here's how `getSystemSubsystems('sys-001', { recursive: true, limit: 5 })` flows:

```
Step 1: Check this.availableResources.has('systems') → yes, proceed
Step 2: Build path = baseUrl + '/systems' + '/sys-001' + '/subsystems'
Step 3: Build query = '?recursive=true&limit=5'
Result: "https://server.com/collections/iot/systems/sys-001/subsystems?recursive=true&limit=5"
```

### Smart Query String Serialization

The `buildQueryString` method handles each parameter type differently:

- **Numbers** (`limit`, `offset`) → validated then stringified
- **Booleans** (`recursive`) → stringified as `"true"` or `"false"`
- **Dates** (`datetime`) → formatted as ISO 8601 via `formatDateTimeParameter`
- **Arrays** (`id`, `bbox`) → joined with commas; `bbox` gets extra coordinate validation
- **Strings** (`q`, `parent`, `procedureId`) → passed directly to `URLSearchParams`
- **undefined/null** → silently skipped

All encoding is handled by `URLSearchParams` — we learned from the Phase 1 F5 bug (double-encoding) that we should let the browser's built-in encoder do its job rather than pre-encoding values.

### Resource Discovery

When you create a `CSAPIQueryBuilder` with a collection document, the constructor does two things:

1. **Extracts the base URL** from the collection's `self` link (e.g., `https://server.com/collections/iot`)
2. **Scans link relations** for `ogc-cs:*` prefixes to build the `availableResources` set

If a server's collection has links with `rel: "ogc-cs:systems"` and `rel: "ogc-cs:datastreams"`, the builder knows systems and datastreams are available. If you call `getSystemDeployments('sys-001')` but the server didn't advertise `systems`, you get a clear error:

```
EndpointError: Collection 'iot' does not support 'systems' resource.
Available resources: datastreams
```

---

## The Complete File Inventory

Here's everything in the CSAPI module as it stands after Phase 2.1:

### Source Files

| File                               | Lines      | Purpose                                                                                        |
| ---------------------------------- | ---------- | ---------------------------------------------------------------------------------------------- |
| `src/ogc-api/csapi/model.ts`       | 582        | Type system — 9 resource types, 10 query options interfaces, collection types, constants       |
| `src/ogc-api/csapi/helpers.ts`     | 164        | 6 pure utility functions — temporal formatting, encoding, validation                           |
| `src/ogc-api/csapi/url_builder.ts` | 420        | `CSAPIQueryBuilder` class — 12 Systems methods + private infrastructure                        |
| `src/ogc-api/endpoint.ts`          | (modified) | Integration — `hasConnectedSystems`, `csapiCollections`, `csapi()` factory on `OgcApiEndpoint` |

### Test Files

| File                                         | Tests | Coverage                                                                                                 |
| -------------------------------------------- | ----- | -------------------------------------------------------------------------------------------------------- |
| `src/ogc-api/csapi/model.spec.ts`            | 27    | Every resource interface, constant correctness, type compatibility                                       |
| `src/ogc-api/csapi/helpers.spec.ts`          | 30    | All 6 helpers with edge cases, error paths, encoding correctness                                         |
| `src/ogc-api/csapi/url_builder.spec.ts`      | 43    | Constructor, resource validation, all 12 Systems methods, query param handling                           |
| `src/ogc-api/endpoint.spec.ts` (CSAPI block) | 6     | End-to-end with fixture data: detection, collection filtering, builder creation, caching, error handling |

**Total: 100 CSAPI unit tests + 6 integration tests = 106 tests, all passing.**

---

## How The Tests Are Organized

The test suite is structured to catch different failure modes at different layers:

### Layer 1 — Type Correctness (`model.spec.ts`, 27 tests)

These construct objects matching each interface and verify TypeScript is happy. They confirm that required fields are enforced, optional fields can be omitted, and constant arrays contain the right values. If someone changes a type definition, these tests break immediately.

### Layer 2 — Utility Correctness (`helpers.spec.ts`, 30 tests)

Pure function tests with known inputs and expected outputs. Covers:

- Date formatting: single dates, open-start ranges, open-end ranges, full intervals, invalid inputs
- Resource type validation: all 9 valid types, invalid strings
- ID encoding: simple text, spaces, slashes, colons, hash/query characters
- Array encoding: empty arrays, single values, multiple values, special characters
- Limit validation: positive integers pass, zero/negative/NaN/non-integers throw
- Bbox validation: valid boxes pass, reversed coordinates throw, non-finite values throw

### Layer 3 — URL Construction (`url_builder.spec.ts`, 43 tests)

Tests the complete query builder, organized into describe blocks that match the API surface:

| Block                       | Tests | What It Verifies                                                                                                                                                                                                                              |
| --------------------------- | ----- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Constructor                 | 4     | Base URL extraction, resource discovery, empty/missing links                                                                                                                                                                                  |
| Resource validation         | 4     | Throws on unsupported resources, lists alternatives in error                                                                                                                                                                                  |
| `getSystems`                | 15    | No options, limit, bbox, q, multiple options, undefined skipping, datetime, array IDs, double-encoding safety, and all 6 SystemQueryOptions-specific params (parent, procedureId, foiId, observedPropertyId, controlledPropertyId, recursive) |
| `getSystem`                 | 3     | Basic URL, special-char encoding in IDs, error on unavailable resource                                                                                                                                                                        |
| `createSystem`              | 2     | Correct POST target URL, error on unavailable resource                                                                                                                                                                                        |
| `updateSystem`              | 2     | Correct PUT target URL, special-char encoding                                                                                                                                                                                                 |
| `deleteSystem`              | 1     | Correct DELETE target URL                                                                                                                                                                                                                     |
| `getSystemHistory`          | 2     | Basic URL, URL with limit                                                                                                                                                                                                                     |
| `getSystemSubsystems`       | 3     | Basic URL, recursive=true, pagination + filtering                                                                                                                                                                                             |
| `getSystemDataStreams`      | 2     | Basic URL, URL with options                                                                                                                                                                                                                   |
| `getSystemControlStreams`   | 1     | Basic URL                                                                                                                                                                                                                                     |
| `getSystemSamplingFeatures` | 1     | Basic URL                                                                                                                                                                                                                                     |
| `getSystemDeployments`      | 2     | Basic URL, URL with options                                                                                                                                                                                                                   |
| `getSystemProcedures`       | 1     | Basic URL                                                                                                                                                                                                                                     |

### Layer 4 — Integration (`endpoint.spec.ts`, 6 tests)

These use fixture JSON files to simulate real server responses. They test the full chain: HTTP mock → `OgcApiEndpoint` detects CSAPI support → `csapiCollections` filters correctly → `csapi('iot')` returns a working builder → builder is cached on second call → non-CSAPI endpoints produce clear errors.

---

## How The Pieces Fit Together

Here's the developer experience from the outside, showing all layers at work:

```typescript
import { OgcApiEndpoint } from 'ogc-client';

const endpoint = new OgcApiEndpoint('https://sensors.example.com/api');

// Phase 1 integration: detect CSAPI support
if (await endpoint.hasConnectedSystems) {
  // Phase 1 integration: get collection names
  const collections = await endpoint.csapiCollections;
  // → ['weather-stations', 'traffic-sensors']

  // Phase 1 integration: create a builder for a collection
  const builder = await endpoint.csapi('weather-stations');

  // Phase 1 (enhanced in Phase 2.1): list systems with filtering
  const listUrl = builder.getSystems({
    limit: 20,
    bbox: [-122.5, 37.7, -122.3, 37.9],
    q: 'temperature',
    recursive: true,
  });
  // → "https://sensors.example.com/api/collections/weather-stations/systems?limit=20&bbox=..."

  // Phase 2.1: get a specific system
  const detailUrl = builder.getSystem('station-42');

  // Phase 2.1: navigate to related resources
  const dataStreamsUrl = builder.getSystemDataStreams('station-42');
  const subsystemsUrl = builder.getSystemSubsystems('station-42', {
    recursive: true,
  });
  const historyUrl = builder.getSystemHistory('station-42', { limit: 10 });

  // Phase 2.1: write operation targets
  const createUrl = builder.createSystem(); // for POST
  const updateUrl = builder.updateSystem('station-42'); // for PUT
  const deleteUrl = builder.deleteSystem('station-42'); // for DELETE
}
```

Each of those URL strings is ready to be used with `fetch()`. The builder guarantees that:

- The base URL comes from the server's own collection document (not hardcoded)
- Special characters in IDs are properly percent-encoded
- Query parameters are validated before serialization
- Unsupported resources produce clear errors rather than malformed URLs

---

## What Comes Next

Phase 2.1 completed the Systems surface. The remaining Phase 2 issues will repeat the same pattern for other resource types:

| Issue | Resource Types                           | Methods                                  |
| ----- | ---------------------------------------- | ---------------------------------------- |
| #6    | Deployments                              | Same CRUD + history + navigation pattern |
| #7    | Procedures, SamplingFeatures, Properties | Part 1 remaining resources               |
| #8    | DataStreams, Observations                | Part 2 observation pipeline              |
| #9    | ControlStreams, Commands                 | Part 2 tasking pipeline                  |

Because the private infrastructure (`buildResourceUrl`, `buildQueryString`, `assertResourceAvailable`) is already built and tested, each new resource type is mostly new public methods — the plumbing is done. The query options interfaces (`DeploymentQueryOptions`, `DatastreamQueryOptions`, etc.) are also already defined in `model.ts`, waiting to be used.

Phase 3 will add **response fetching and parsing** — actually calling those URLs and turning the JSON responses into typed objects. Phase 4 will add **real-time streaming** via WebSocket and MQTT.

---

## Summary

| Metric                              | Phase 1 (before) | Phase 2.1 (now)                                                                                                                |
| ----------------------------------- | ---------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| Public methods on CSAPIQueryBuilder | 2                | 12                                                                                                                             |
| Systems operations covered          | List, Get        | List, Get, Create, Update, Delete, History, Subsystems, DataStreams, ControlStreams, SamplingFeatures, Deployments, Procedures |
| CSAPI unit tests                    | 76               | 100                                                                                                                            |
| Total tests (incl. integration)     | 82               | 106                                                                                                                            |
| url_builder.ts lines                | ~213             | ~420                                                                                                                           |
| url_builder.spec.ts tests           | 20               | 43                                                                                                                             |

The foundation (types, helpers, endpoint integration) from Phase 1 is unchanged — Phase 2.1 was purely additive, building on top without modifying any existing behavior.
