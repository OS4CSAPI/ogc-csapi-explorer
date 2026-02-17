# Bbox Spatial Filter — How It Works

## Overview

The Map page in the CSAPI Explorer demo app includes a **bounding box spatial filter** that lets users draw a rectangle on the map to filter resources by geographic area. The filter is applied **server-side** — the OGC Connected Systems API server only returns resources whose geometry intersects the bounding box. This feature directly exercises the **CSAPIQueryBuilder** client library built in the forked `ogc-client` repo.

## The Flow: Draw → Library → Server → Map

### 1. Draw a rectangle on the map

The user clicks "Draw Bbox Filter" in the sidebar and drags a rectangle on the map. OpenLayers captures the two corners and converts them to WGS84 coordinates:

```
bboxFilter = [-79.616, 37.869, -74.781, 39.649]  // [minLon, minLat, maxLon, maxLat]
```

### 2. The demo app passes bbox to the client library

Every resource query goes through the `getListUrl()` bridge function in `demo/src/csapi-bridge.ts`:

```ts
const url = getListUrl('systems', { limit: 200, bbox: bboxFilter.value })
```

This dispatches to the **CSAPIQueryBuilder** built in the forked `ogc-client` repo:

```ts
case 'systems': return b.getSystems(options as SystemQueryOptions)
case 'datastreams': return b.getDataStreams(options as DatastreamQueryOptions)
case 'controlStreams': return b.getControlStreams(options as ControlStreamQueryOptions)
// etc.
```

### 3. The client library serializes the bbox into a query parameter

Inside `CSAPIQueryBuilder` (the forked repo's `src/ogc-api/csapi/url_builder.ts`), each method like `getSystems()`, `getDataStreams()`, etc. accepts `QueryOptions` which includes `bbox?: BoundingBox`. The builder serializes it into the URL:

```
/systems?limit=200&bbox=-79.616,37.869,-74.781,39.649
```

This is the **OGC Connected Systems API standard** bbox parameter format. The library handles the formatting so the demo app doesn't need to know the serialization details.

### 4. The server filters and responds

OSH SensorHub receives the request, applies the spatial filter server-side, and returns **only resources whose geometry intersects the bounding box**. Instead of 26 systems, you might get back 20. Instead of all sampling features, only those within the rectangle. The filtering happens on the server — the demo app never downloads resources it doesn't need.

### 5. The demo app displays the filtered results

After the response comes back, the map **clears all existing features** and displays only what the server returned. The sidebar counts update to match the filtered response.

## What the Client Library Specifically Enables

The key work in the forked `ogc-client` repo that makes this possible:

1. **`QueryOptions` interface** with `bbox?: BoundingBox` — defined in `src/ogc-api/csapi/model.ts`. This is extended by `SystemQueryOptions`, `DatastreamQueryOptions`, `ControlStreamQueryOptions`, `ObservationQueryOptions`, `SamplingFeatureQueryOptions`, etc.

2. **`CSAPIQueryBuilder` methods** — `getSystems(opts)`, `getDataStreams(opts)`, `getControlStreams(opts)`, etc. in `src/ogc-api/csapi/url_builder.ts`. Each one accepts the typed options object and produces a properly formatted URL with all query parameters including bbox.

3. **Type safety** — the library enforces that you can't accidentally pass `bbox` to a resource type that doesn't support it. Each resource type has its own options interface.

## Why This Matters

Without the client library, the demo app would have to:
- Manually construct URLs with raw string concatenation
- Know the exact OGC parameter format for bbox
- Handle different query parameter names per resource type
- Risk typos and inconsistencies

With the library, it's just:

```ts
getListUrl('systems', { limit: 200, bbox: [-79.6, 37.8, -74.7, 39.6] })
```

The library handles serialization, URL construction, and type validation. The demo app proves that **the library's CRUD URL building works end-to-end against a real OGC Connected Systems API server** — which is the whole point of this exercise.

## Resource Types and Bbox Handling

| Resource Type | Bbox Source | How It Works |
|---|---|---|
| Systems | Server-side | `bbox` passed to `getSystems()`, server filters by geometry |
| Deployments | Server-side | `bbox` passed to `getDeployments()`, server filters by geometry |
| Procedures | Server-side | `bbox` passed to `getProcedures()`, server filters by geometry |
| Sampling Features | Server-side + enrichment | `bbox` passed to query; enriched features filtered by parent system location |
| Datastreams | Library URL + client filter | `bbox` passed to `getDataStreams()` via library; placed at parent system location, skipped if location outside bbox |
| Control Streams | Library URL + client filter | `bbox` passed to `getControlStreams()` via library; placed at parent system location, skipped if location outside bbox |
| Observations | Client filter | Fetched per-datastream; individual observation lat/lon checked against bbox |
| Observation Tracks | Client filter | Built from filtered observation points |

**Note:** Part 2 resources (datastreams, controlStreams) don't have their own geometry — they inherit their map position from their parent system's location. The bbox is still sent to the server via the library (which is the point of the exercise), and the demo app also filters by the placement coordinates to ensure nothing appears outside the drawn rectangle.

## Key Files

- **`demo/src/pages/MapViewPage.vue`** — Map page with bbox draw interaction, all resource loading, and display logic
- **`demo/src/csapi-bridge.ts`** — Bridge between demo app and client library; `getListUrl()` dispatches to `CSAPIQueryBuilder` methods
- **`src/ogc-api/csapi/url_builder.ts`** — Client library `CSAPIQueryBuilder` class with typed query methods
- **`src/ogc-api/csapi/model.ts`** — `QueryOptions`, `BoundingBox`, and per-resource-type option interfaces

## About csapi-bridge.ts — Scaffolding, Not a Deviation

### What it is

`csapi-bridge.ts` is a **thin adapter** that sits between the demo app's Vue components and the `CSAPIQueryBuilder` class from the library. It does two things:

1. Holds a reactive `shallowRef` to the builder instance (Vue needs this for reactivity)
2. Provides a `getListUrl(resourceType, options)` convenience function that dispatches to the correct typed method (`getSystems()`, `getDataStreams()`, etc.)

That's it. No business logic. No custom query parameter handling. No URL construction. All the actual work — bbox serialization, URL building, type validation — happens inside `CSAPIQueryBuilder` in the library source (`src/ogc-api/csapi/url_builder.ts`).

### Could the upstream fork do this without csapi-bridge.ts?

Yes. The upstream `ogc-client` library's existing pattern uses `OgcApiEndpoint`, which is a higher-level class. If/when the CSAPI work gets upstreamed, the equivalent would be something like:

```ts
const endpoint = await new OgcApiEndpoint(serverUrl)
const systems = await endpoint.csapi.getSystems({ bbox: [-79.6, 37.8, -74.7, 39.6] })
```

The `CSAPIQueryBuilder` would be wired internally behind `OgcApiEndpoint`, just like `WfsEndpoint`, `WmtsEndpoint`, etc. are today. The bridge file wouldn't be needed — `OgcApiEndpoint` would handle the lifecycle.

### Why the demo uses csapi-bridge.ts instead of OgcApiEndpoint

The demo app can't use `OgcApiEndpoint` for CSAPI resources because:

- `OgcApiEndpoint` doesn't know about CSAPI yet (that's the whole point of this fork)
- Wiring CSAPI into `OgcApiEndpoint` requires architectural decisions the upstream maintainers should make (discovery, capability negotiation, etc.)
- The bridge gives us a way to **validate the builder works end-to-end** without prematurely committing to an integration pattern

### Bottom line

The bridge is **scaffolding**, not a deviation. The real value is in `CSAPIQueryBuilder` and `QueryOptions` — those live in the library and will work regardless of how they're accessed. Any fork that has those classes can enable bbox filtering the same way. The bridge just makes it convenient for this particular Vue app.
