# Resource Explorer — Implementation Report

> **Date**: 2026-02-16
> **Commit**: `fc44243` — `feat: add Resource Explorer with full CRUD for all 9 resource types`
> **Prerequisite commit**: `9dd717e` — `docs: add demo app scaffold implementation report`
> **Location**: `demo/src/` — new files across `pages/`, `components/`, and root-level modules

---

## What We Did

Built the complete Resource Explorer — Page 2 of the CSAPI Explorer demo app — providing full CRUD operations for all 9 Connected Systems API resource types. This is the core functional page of the entire demo. It involved:

1. Researching the full CSAPIQueryBuilder API surface to understand every available method
2. Installing Vue Router 4 for page navigation
3. Designing and implementing shared application state
4. Building an API helper module for authenticated requests
5. Restructuring the app from single-page to multi-page with routing
6. Building the Resource Explorer layout with a categorized sidebar
7. Implementing five CRUD sub-components (List, Detail, Create, Update, Delete)
8. Handling two different server response envelope formats
9. Supporting both offset-based and cursor-based pagination
10. Fixing PrimeVue 4 API incompatibilities discovered during development
11. Verifying both proxy endpoints return real data from live servers
12. Committing and pushing

Each step is detailed below, followed by findings, concerns, and recommendations.

---

## Step 1: API Surface Research

### What We Did

Before writing any component code, we performed a thorough audit of the CSAPIQueryBuilder class and all related CSAPI code in the repository. This was essential because the demo app's entire purpose is to exercise this API — we needed to understand every method signature, every query parameter, and every response format.

### Key Files Examined

| File | Purpose |
|------|---------|
| `src/ogc-api/csapi/url_builder.ts` | CSAPIQueryBuilder — the URL builder for all CRUD operations |
| `src/ogc-api/csapi/model.ts` | TypeScript interfaces for all 9 resource types, query options, collections |
| `src/ogc-api/endpoint.ts` | OgcApiEndpoint class — the `csapi()` method that returns a builder |
| `src/ogc-api/csapi/formats/index.ts` | Barrel exports for all parsers |
| `src/ogc-api/csapi/formats/response.ts` | `parseCollectionResponse()` — the main response parser |
| `src/index.ts` | Public API surface — what's exported for consumers |

### What We Found

The API is extensive. Across all 9 resource types, there are **70+ URL-building methods**. Here's the CRUD summary:

| Resource | List | Get | Create | Update | Delete | Extra Methods |
|----------|------|-----|--------|--------|--------|---------------|
| **Systems** | ✓ | ✓ | ✓ | ✓ | ✓ | history, subsystems, datastreams, control streams, sampling features, deployments, procedures |
| **Deployments** | ✓ | ✓ | ✓ | ✓ | ✓ | history, subdeployments, systems |
| **Procedures** | ✓ | ✓ | ✓ | ✓ | ✓ | history, systems, datastreams |
| **Sampling Features** | ✓ | ✓ | ✓ | ✓ | ✓ | history, systems, observations |
| **Properties** | ✓ | ✓ | — | — | — | history, systems, datastreams, control streams |
| **Datastreams** | ✓ | ✓ | ✓ | ✓ | ✓ | schema, observations, systems, procedures, history |
| **Observations** | ✓ | ✓ | ✓* | ✓ | ✓ | datastream, sampling feature, system, history |
| **Control Streams** | ✓ | ✓ | ✓ | ✓ | ✓ | schema, commands, feasibility check |
| **Commands** | ✓ | ✓ | ✓* | ✓ | ✓ | status, result, cancel, bulk create |

*Observations and Commands have **nested creation** — you create an Observation by POSTing to `datastreams/{id}/observations`, and a Command by POSTing to `controlStreams/{id}/commands`. This is an OGC API design pattern, not a quirk of our library.

### Critical Design Insight: Properties Are Read-Only

Properties have no `createProperty()`, `updateProperty()`, or `deleteProperty()` methods. This makes sense semantically — properties (like "temperature", "pressure") are typically server-managed reference data, not user-created resources. The demo app needed to handle this by hiding the Create/Update/Delete tabs for Properties.

### Query Parameter Options

Every list endpoint accepts these base parameters:

```typescript
interface QueryOptions {
  limit?: number;       // Max results per page
  offset?: number;      // Offset-based pagination
  cursor?: string;      // Cursor-based pagination (opaque token)
  bbox?: BoundingBox;   // Spatial filter [minx, miny, maxx, maxy]
  datetime?: DateTimeParameter;  // Temporal filter
  q?: string;           // Free-text search
  id?: string | string[];    // Filter by local ID(s)
  uid?: string | string[];   // Filter by globally unique URI(s)
  f?: MimeType;         // Response format
  crs?: CrsCode;        // CRS for response geometries
}
```

Resource-specific extensions add parameters like `parent`, `systemId`, `procedureId`, `observedPropertyId`, `phenomenonTime`, `resultTime` (which supports the special `'latest'` keyword), and `currentStatus` for commands.

### Two Response Envelope Formats

This was a significant finding. The library's `parseCollectionResponse()` handles two distinct formats:

1. **FeatureCollection** (Part 1 / GeoJSON): `{ type: "FeatureCollection", features: [...] }` — used by Systems, Deployments, Procedures, Sampling Features
2. **Items envelope** (Part 2 / OpenSensorHub): `{ items: [...] }` — used by Datastreams, Observations, Control Streams, Commands, Properties

Both servers actually use *different* envelope formats even for the same resource type. 52North returns Part 2-style `items` envelopes for systems, while OSH returns GeoJSON `FeatureCollection`. The ResourceList component needed to handle both patterns gracefully.

---

## Step 2: Install Vue Router

### What We Did

Ran `npm install vue-router@4` in the `demo/` directory.

### Why

The demo app has two distinct pages:
- **Server Connect** — configure and connect to a server
- **Resource Explorer** — browse and CRUD resources

Without a router, we'd need manual show/hide logic in a single component. Vue Router gives us proper URL-based navigation (`/` for connect, `/explore/systems` for the explorer), browser back/forward support, and clean code separation between pages.

### Route Structure

```
/                    → ServerConnectPage.vue
/explore/:resourceType? → ResourceExplorerPage.vue (defaults to 'systems')
```

The `:resourceType?` parameter is optional with a default of `systems`. This means `/explore` and `/explore/systems` both work, and clicking a resource type in the sidebar navigates to `/explore/deployments`, `/explore/observations`, etc.

---

## Step 3: Shared Application State

### What We Did

Created `demo/src/state.ts` — a reactive state module that holds the active server connection and resource type metadata.

### Why a Shared Module (Not a Store Library)

For a demo app with a tight scope, a full state management library (Pinia, Vuex) adds complexity without value. Vue 3's `reactive()` is sufficient — we export a single reactive object that any component can import and read/write directly. This is the simplest pattern that works.

### What It Contains

**`connection`** — reactive object with:
```typescript
{
  connected: boolean      // Is a server connected?
  label: string           // Display name (e.g., "52North CSA Demo")
  baseUrl: string         // Proxy path (e.g., "/api/52north")
  authHeaders: {}         // Auth headers to include in every request
  landingPage: any        // Server's landing page response
  conformance: string[]   // Conformance class URIs
  collections: any[]      // Available collections
}
```

**`RESOURCE_TYPES`** — static array of all 9 resource types with metadata:
```typescript
{
  key: 'systems',              // URL path segment and internal identifier
  label: 'System',             // Singular display name
  plural: 'Systems',           // Plural display name
  icon: 'pi pi-server',       // PrimeIcons class for sidebar
  part: 1,                     // CSAPI Part (1 = Features, 2 = Observations/Commands)
  readOnly: false,             // Whether create/update/delete are available
  createParentType?: string,   // For nested creation (observations → datastreams)
  createParentLabel?: string,  // UI label for the parent ID field
}
```

The `createParentType` field is the key to handling the nested creation pattern. When `ResourceCreate` sees that a resource type has a `createParentType`, it shows an additional "Datastream ID" or "Control Stream ID" input and constructs the POST URL as `/{parentType}/{parentId}/{resourceType}` instead of `/{resourceType}`.

---

## Step 4: API Helper Module

### What We Did

Created `demo/src/api.ts` — a thin wrapper around `fetch()` that handles authentication, JSON parsing, and error formatting.

### Why Not Use the Library Directly?

The session handoff document explains the "HTTP Client Gap": the ogc-client library builds URLs and parses responses, but does **not** execute HTTP requests for write operations. For this initial implementation, we went with a simpler approach — direct `fetch()` calls with path-based URL construction — rather than instantiating `OgcApiEndpoint` and `CSAPIQueryBuilder`.

This was a deliberate trade-off:
- **Pro**: Faster to implement, no dependency on library build chain, works immediately
- **Con**: Doesn't exercise the library's URL-building methods
- **Plan**: Phase 2 can swap the direct fetch calls for library-based URL construction, which would be a thin refactor (the component structure stays the same, only the URL source changes)

### What It Provides

**`apiFetch<T>(path, options)`** — the core function. It:
1. Prepends `connection.baseUrl` to the path (so components just say `/systems`, not `/api/52north/systems`)
2. Injects auth headers from the shared connection state
3. Defaults `Accept` to `application/json`
4. Returns a structured `ApiResponse<T>` with `ok`, `status`, `data`, `error`, and `headers` fields
5. Handles network errors, non-JSON responses, and 204 No Content (common for DELETE)
6. Extracts response headers into a plain object (useful for `Location` header after POST)

**`getResourcePath(resourceType)`** — maps resource type keys to API path segments:
```
systems → /systems
deployments → /deployments
samplingFeatures → /samplingFeatures
...
```

**`buildQueryString(params)`** — converts a filter object to a URL query string, skipping null/undefined/empty values. Handles arrays (comma-joined) for multi-value parameters.

### Error Handling Philosophy

Per the scope tiers in the assessment doc, we're skipping production-quality error handling. But we still need *useful* error messages for development. The API helper captures:
- HTTP status + status text
- First 500 characters of the error response body (servers often return JSON error details)
- Network errors (DNS resolution, connection refused, timeout)

These get displayed in PrimeVue `Message` components with red severity in the UI.

---

## Step 5: App Restructure — From Single Page to Routed

### What Changed

The original scaffold had:
- `App.vue` → directly renders `ServerConnect` component
- No routing, no pages

After this step:
- `App.vue` → renders a navigation header + `<router-view />`
- `pages/ServerConnectPage.vue` → the connect page (evolved from the old `ServerConnect`)
- `pages/ResourceExplorerPage.vue` → the explorer page with sidebar + main content area
- `router.ts` → route definitions
- `main.ts` → now registers the router plugin

### App.vue — The Navigation Header

The header shows:
- **Left**: "CSAPI Explorer" title (links back to `/`)
- **Right**: Connection status badge (green checkmark + server label when connected), "Explorer" link (only when connected), "Connect" link (always)

This gives persistent navigation context regardless of which page you're on. The connection badge is reactive — it appears instantly when you connect and disappears when you disconnect.

### ServerConnectPage.vue — Evolved from ServerConnect

The original `ServerConnect.vue` component was refactored into a page component. Key changes:
- Now stores connection data in the shared `connection` state (not just local reactive variables)
- Adds an "Open Explorer" button that navigates to `/explore/systems` after successful connection
- Adds a "Disconnect" button that clears shared state and resets the form
- Still shows all the same discovery info (landing page, conformance, collections)

The old `ServerConnect.vue` component was deleted.

---

## Step 6: Resource Explorer Layout

### What We Built

`ResourceExplorerPage.vue` — a two-column layout:

```
┌─────────────────────────────────────────────────────┐
│  [CSAPI Explorer]          [● 52North]  [Explorer]  │
├────────────┬────────────────────────────────────────┤
│            │                                        │
│  Part 1    │                                        │
│  ────────  │   ResourcePanel                        │
│  Systems   │   ┌──────────────────────────────┐     │
│  Deploy... │   │ List │ Detail │ Create │ ... │     │
│  Proced... │   ├──────────────────────────────┤     │
│  Sampling. │   │                              │     │
│  Propert.. │   │  (active tab content)        │     │
│            │   │                              │     │
│  Part 2    │   │                              │     │
│  ────────  │   │                              │     │
│  Datast... │   │                              │     │
│  Observ... │   └──────────────────────────────┘     │
│  Control.. │                                        │
│  Commands  │                                        │
│            │                                        │
└────────────┴────────────────────────────────────────┘
```

### Sidebar Design Decisions

- **Grouped by CSAPI Part**: Part 1 (Features — Systems through Properties) and Part 2 (Observations & Commands — Datastreams through Commands). This matches the OGC specification structure.
- **Active state**: Blue highlight on the selected type, with contrasting text.
- **Read-only badge**: Properties shows an "R/O" badge to indicate it's read-only before you even click it.
- **Icons**: Each resource type has a PrimeIcons icon for quick visual scanning (server, map, cog, map-marker, tags, chart-line, eye, sliders, send).

### Navigation

Clicking a sidebar item navigates to `/explore/{resourceType}`. The `ResourcePanel` component receives the type as a prop and re-renders with a `:key` binding to ensure clean state when switching types.

### Guard

The explorer page watches `connection.connected` — if it becomes false (disconnect or page refresh), the user is redirected to `/`.

---

## Step 7: The Five CRUD Components

### ResourcePanel.vue — The Tab Container

Wraps all five CRUD sub-components in a PrimeVue tab interface. Shows the resource type name, icon, Part badge, and read-only badge.

Manages cross-tab coordination:
- Clicking "view" (eye icon) in the List tab → switches to Detail tab with the selected resource
- Clicking "edit" (pencil icon) in the List tab → switches to Update tab with the resource pre-loaded
- Creating a resource → switches back to List tab
- Deleting a resource → clears selection and switches back to List tab

**PrimeVue 4 API Issue**: The initial implementation used `<TabView>` with `<TabPanel header="List">`, which is the PrimeVue 3 API. PrimeVue 4 changed to a Headless-style API:
```html
<Tabs>
  <TabList>
    <Tab :value="0">List</Tab>
    <Tab :value="1">Detail</Tab>
    ...
  </TabList>
  <TabPanels>
    <TabPanel :value="0">...</TabPanel>
    <TabPanel :value="1">...</TabPanel>
    ...
  </TabPanels>
</Tabs>
```

This required importing 5 components (`Tabs`, `TabList`, `Tab`, `TabPanels`, `TabPanel`) instead of 2. The migration was caught by TypeScript errors during development — the `header` prop no longer exists on `TabPanel`, and the `value` prop is now required.

### ResourceList.vue — List & Filter

The most complex component. Features:

**Filters**:
- `limit` — number input, controls page size (default 10)
- `q` — free-text search
- `bbox` — bounding box as `minx,miny,maxx,maxy`
- `datetime` — ISO 8601 date/time range as `start/end`

These map directly to the OGC API Common query parameters.

**Dual Pagination**:
- **Offset mode**: Uses `limit` + `offset` parameters. Previous/Next buttons increment/decrement offset by limit. "Previous" disabled when offset is 0, "Next" disabled when fewer items returned than the limit.
- **Cursor mode**: Extracts `next` and `prev` link relations from the response `links` array. Uses the server's opaque cursor tokens for navigation. This is the pattern preferred by Part 2 implementations.

A toggle button switches between modes. Both modes are demonstrated per the must-have requirements.

**Response Parsing**:
```typescript
if (data?.type === 'FeatureCollection' && Array.isArray(data.features)) {
  items = data.features        // Part 1 GeoJSON
} else if (Array.isArray(data?.items)) {
  items = data.items           // Part 2 items envelope
} else if (Array.isArray(data)) {
  items = data                 // Raw array fallback
}
```

**Smart Display Columns**:
- **ID**: Extracts from `item.id`, `item.properties.id`, or `item['@id']` (different servers use different patterns)
- **Name/Title**: Tries `properties.name`, `properties.title`, `name`, `title`, then falls back to truncated description
- **Type**: Shows `type` or `properties.featureType`

**Pagination Link Handling**:
Server responses include absolute URLs in `links[].href` (e.g., `https://csa.demo.52north.org/systems?offset=10`). These can't be used directly because they bypass our proxy. The `extractProxyPath()` function converts them to relative paths (`/systems?offset=10`), which then go through `apiFetch()` which prepends the proxy base URL.

> **Note**: This is a simplification that works for offset-based pagination where the path + query is the same structure. For cursor-based pagination where the cursor token is in the URL, this also works because the cursor is just a query parameter. But if a server returned a completely different hostname in its `next` link, this would break. In practice, servers return links pointing to themselves, so this is fine.

### ResourceDetail.vue — View Single Resource

Two entry points:
1. Click the eye icon on a list row → auto-fetches the resource by ID
2. Manually type an ID and click Fetch

Displays:
- **Summary fields**: ID, type, name, description, feature type, valid time — extracted from both GeoJSON `properties` and flat object patterns
- **Links table**: All link relations from the resource (rel, type, href) — useful for understanding the server's hypermedia
- **Full JSON**: Pretty-printed, syntax-highlighted, scrollable, open by default

### ResourceCreate.vue — POST New Resources

**Starter Templates**: Pre-populates the JSON editor with a valid template for each resource type. Examples:

Systems:
```json
{
  "type": "Feature",
  "properties": {
    "featureType": "http://www.w3.org/ns/sosa/Platform",
    "name": "My Test System",
    "description": "A test system created via CSAPI Explorer"
  },
  "geometry": null
}
```

Datastreams:
```json
{
  "name": "My Test Datastream",
  "description": "A test datastream",
  "outputName": "test-output"
}
```

These templates serve dual purposes: they show users the expected JSON structure, and they provide a valid starting point for testing CRUD.

**Content-Type Selection**: Part 1 resources (Systems, Deployments, Procedures, Sampling Features) use `application/geo+json`. Part 2 resources use `application/json`. This is the OGC specification requirement — sending the wrong Content-Type will get a 400 or 415 from the server.

**Nested Creation**: When the resource type has `createParentType` set (Observations, Commands), an additional input field appears for the parent ID. The POST URL becomes:
- Observation: `POST /datastreams/{datastreamId}/observations`
- Command: `POST /controlStreams/{controlStreamId}/commands`

**Response Display**: Shows the HTTP status, and if the server returns a `Location` header (standard for 201 Created), displays it. Also shows the response body if the server returns the created resource.

### ResourceUpdate.vue — PUT Existing Resources

Two entry points:
1. Click the pencil icon on a list row → auto-loads the resource's current JSON into the editor
2. Manually type an ID (the JSON editor stays from whatever was last loaded)

Sends a PUT request with the edited JSON. Same Content-Type logic as Create.

### ResourceDelete.vue — DELETE with Confirmation

Two-step confirmation to prevent accidental deletion:
1. Enter/select an ID → click "Delete" → red confirmation box appears
2. Click "Yes, Delete" → sends DELETE request → shows success/error

The confirmation box has a red background and warning icon to visually signal the destructive nature of the operation.

---

## Step 8: TypeScript Error Resolution

### What Happened

After building all components, we ran error checks and found these issues:

| File | Issue | Fix |
|------|-------|-----|
| `ResourcePanel.vue` | PrimeVue 4 TabPanel requires `value` prop, not `header` | Migrated to Tabs/TabList/Tab/TabPanels/TabPanel pattern |
| `ServerConnectPage.vue` | `selectedPreset.value` possibly undefined | Added optional chaining (`?.`) |
| `ResourceExplorerPage.vue` | `route` declared but never used | Removed unused import |
| `ResourceDetail.vue` | `rtInfo` declared but never used | Removed unused import and variable |

All resolved — zero TypeScript errors in the final commit.

---

## Step 9: Live Server Verification

### What We Tested

With the dev server running, we verified that both proxy endpoints return real resource data:

**52North** — `curl.exe -s "http://localhost:5173/api/52north/systems?limit=5"`:
```json
{
  "items": [
    {
      "type": "PhysicalSystem",
      "definition": "sosa:Sensor",
      "id": "5400-526",
      "description": "DCPS #526",
      "uniqueId": "urn:sensor:5400-526",
      "label": "Doppler Current Profiler Sensor"
    },
    // ...
  ],
  "links": []
}
```

**OSH SensorHub** — `curl.exe -s "http://localhost:5173/api/osh/systems?limit=5"`:
```json
{
  "items": [
    {
      "type": "Feature",
      "id": "03bc5ofvvstg",
      "geometry": null,
      "properties": {
        "uid": "urn:osh:driver:mavsdk:cube:replay",
        "featureType": "http://www.w3.org/ns/sosa/Sensor",
        "name": "LIVE - Field Drone"
      }
    }
  ]
}
```

**Key discovery**: Both servers' systems endpoints return data in the `items` envelope, but OSH wraps each item as a GeoJSON `Feature` while 52North returns flat objects without the `Feature` wrapper. The ResourceList's display logic handles both by checking multiple field paths for ID, name, and type.

---

## File Summary

### New Files Created (10)

| File | Lines | Purpose |
|------|-------|---------|
| `demo/src/state.ts` | 64 | Shared reactive state + resource type metadata |
| `demo/src/api.ts` | 119 | Fetch wrapper, resource paths, query string builder |
| `demo/src/router.ts` | 24 | Vue Router config with two routes |
| `demo/src/pages/ServerConnectPage.vue` | 196 | Server connection page (evolved from prior ServerConnect) |
| `demo/src/pages/ResourceExplorerPage.vue` | 115 | Two-column layout with sidebar |
| `demo/src/components/ResourcePanel.vue` | 135 | Tab container for CRUD sub-components |
| `demo/src/components/ResourceList.vue` | 260 | List, filter, paginate resources |
| `demo/src/components/ResourceDetail.vue` | 143 | View single resource by ID |
| `demo/src/components/ResourceCreate.vue` | 169 | JSON editor + POST to create |
| `demo/src/components/ResourceUpdate.vue` | 124 | Load + edit JSON + PUT to update |
| `demo/src/components/ResourceDelete.vue` | 110 | Confirmation dialog + DELETE |

### Modified Files (4)

| File | Change |
|------|--------|
| `demo/src/main.ts` | Added router plugin registration |
| `demo/src/App.vue` | Replaced static page with nav header + `<router-view />` |
| `demo/package.json` | Added vue-router dependency |
| `demo/package-lock.json` | Lockfile update |

### Deleted Files (1)

| File | Reason |
|------|--------|
| `demo/src/components/ServerConnect.vue` | Replaced by `pages/ServerConnectPage.vue` |

---

## Findings and Observations

### 1. The Two Servers Behave Very Differently

This was not fully anticipated. While both servers implement the Connected Systems API, their response structures diverge significantly:

| Aspect | 52North | OSH SensorHub |
|--------|---------|---------------|
| Systems envelope | `{ items: [...] }` with flat objects | `{ items: [...] }` with GeoJSON Features |
| System ID field | `id` at top level | `id` at top level, `uid` in `properties` |
| System name field | `label` | `properties.name` |
| System type | `type: "PhysicalSystem"` at top level | `properties.featureType` URI |
| Links in response | Often empty `[]` | Rich link arrays with rels |

This is exactly the kind of interoperability gap the demo is meant to expose. Our library's parsers normalize these differences, but since we're using direct `fetch()` for this first pass, the component display logic had to handle both patterns.

### 2. 52North's Systems Endpoint Returns Non-GeoJSON

The assessment doc and library code suggested Part 1 resources (Systems, Deployments, etc.) would come back as `FeatureCollection`. The 52North server actually returns an `items` envelope for systems — the same format typically used by Part 2 resources. This may be because 52North's implementation is based on the latest OGC API Connected Systems spec draft which may have unified the response format. Either way, the ResourceList handles it.

### 3. Pagination Links Are Absolute URLs

When a server returns pagination links like:
```json
{ "rel": "next", "href": "https://csa.demo.52north.org/systems?offset=10&limit=5" }
```

These absolute URLs point to the real server, not our proxy. The browser can't follow these directly (CORS + expired SSL). The `extractProxyPath()` function strips the origin and keeps only the path + query, which then routes through the proxy. This is a simplification that works for the current servers but is noted as a potential issue.

### 4. PrimeVue 4's Breaking Tab API Change

PrimeVue 4 significantly changed the Tabs API from PrimeVue 3. The old pattern (`<TabView>` + `<TabPanel header="...">`) is gone. The new pattern requires 5 separate component imports and a `value`-based approach. This was caught by TypeScript during development, not at runtime. The lesson: PrimeVue 4 documentation examples online often show the PrimeVue 3 API, which causes confusion.

### 5. HMR Picked Up New Dependencies Automatically

When we added imports for `primevue/tabs`, `primevue/tablist`, etc. (components not previously used), Vite's dependency optimizer detected the new imports and re-optimized on the fly:
```
✨ new dependencies optimized: primevue/tabs, primevue/tablist, primevue/tab, primevue/tabpanels
✨ optimized dependencies changed. reloading
```

No restart needed. This is one of the advantages of Vite's dev server.

### 6. 52North DNS Resolution Briefly Failed

During testing, the dev server logged:
```
[vite] http proxy error: /systems
Error: getaddrinfo EAI_AGAIN csa.demo.52north.org
```

This is a transient DNS resolution failure — `EAI_AGAIN` means "try again." The server came back on the next request. This reinforces the note in the assessment doc about "server availability" being a risk. The demo should handle this gracefully rather than showing a cryptic error.

---

## Concerns

### 1. Not Using the Library Yet

The biggest gap: the demo currently uses direct `fetch()` calls rather than the `CSAPIQueryBuilder` URL builder and `parseCollectionResponse()` parser from the library. This means we're not yet validating the library's CRUD URL construction end-to-end. The plumbing is ready for this — swapping `apiFetch('/systems?limit=10')` for `apiFetch(builder.getSystems({ limit: 10 }))` is straightforward. But it needs to happen.

### 2. Proxy Path Stripping vs. Library URLs

When we do integrate the library, the `CSAPIQueryBuilder` may produce absolute URLs that include the real server hostname (not the proxy prefix). We'll need either:
- A URL rewriting layer that translates server URLs to proxy URLs
- Or configure the library with the proxy base URL so it produces proxy-relative URLs from the start

This is a solvable problem but needs thought before the integration.

### 3. No Error Recovery on Connection Loss

If the server goes down mid-session, every request will fail with a network error. Currently the user sees error messages per-component but there's no global "server disconnected" detection. For a demo this is acceptable, but worth noting.

### 4. Refresh Loses Connection State

The shared state is in-memory (`reactive()`). A browser refresh clears everything — the user has to reconnect. LocalStorage persistence would be easy to add but is in the "nice-to-have" tier.

---

## Recommendations for Next Steps

### Immediate (before calling the demo "complete")

1. **Integrate CSAPIQueryBuilder** — Replace direct path construction in `api.ts` with library URL builder calls. This is the demo's primary purpose.
2. **Integrate response parsers** — Feed responses through `parseCollectionResponse()` and `extractCSAPIFeature()` to validate the library's parsing end-to-end.
3. **Test write operations** — We've verified reads. Need to test POST/PUT/DELETE against at least one server (OSH is the better candidate since it has full CORS + auth).

### If Time Allows

4. **Better display for Part 2 data** — Observations and Datastreams have `result` and `schema` fields with SWE Common structures. Displaying these meaningfully (not just raw JSON) would showcase the library's `parseSWEComponent()`.
5. **Cursor-based pagination UX** — Currently the cursor mode button is a simple toggle. Could show the cursor tokens to demonstrate what cursor-based pagination looks like under the hood.
6. **Connection persistence** — Store the last connection in LocalStorage and auto-reconnect on page load.

---

## How to Run

```bash
cd demo
npm install     # only needed first time
npm run dev     # starts Vite dev server at http://localhost:5173
```

1. Select a server preset (or enter a custom URL)
2. Optionally enter auth credentials (required for OSH SensorHub)
3. Click **Connect** — you'll see server info, conformance classes, and collections
4. Click **Open Explorer** — sidebar shows all 9 resource types
5. Click a resource type → List tab auto-fetches resources
6. Click the eye icon → Detail tab shows full resource
7. Click the pencil icon → Update tab loads resource for editing
8. Use the Create tab with a JSON body → POST to server
9. Use the Delete tab with a resource ID → DELETE with confirmation
