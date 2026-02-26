# CSAPI Explorer — Session Handoff & Context Briefing

> **Purpose:** This document provides full context for continuing work in a new VS Code workspace and chat session. Point the new Copilot instance at this file so it can quickly orient itself.

---

## Project Background

We added **Connected Systems API (CSAPI)** support to the [camp-to-camp/ogc-client](https://github.com/camptocamp/ogc-client) library via a fork at **[OS4CSAPI/ogc-client-CSAPI_2](https://github.com/OS4CSAPI/ogc-client-CSAPI_2)**. That work is **complete** — all 32 GitHub issues across 4 phases are closed, all CSAPI test suites pass, and documentation is done.

### What Was Built (in ogc-client-CSAPI_2)

The CSAPI contribution adds three layers to the ogc-client library:

1. **URL Builders** — `CSAPIQueryBuilder` class constructs correct URLs for all CRUD operations (GET/POST/PUT/DELETE) across all 9 resource types, with full query parameter support (bbox, datetime, pagination, filters)
2. **Response Parsers** — parse GeoJSON FeatureCollection and items envelopes, SensorML 3.0 documents, SWE Common schemas, collection responses, and pagination metadata
3. **Type Definitions** — TypeScript interfaces for all resource types, query options, status codes, media types, etc.

### The 9 CSAPI Resource Types

| Part 1 (GeoJSON) | Part 2 (non-GeoJSON) |
| ---------------- | -------------------- |
| Systems          | Datastreams          |
| Deployments      | Observations         |
| Procedures       | ControlStreams       |
| SamplingFeatures | Commands             |
| Properties       |                      |

### Key Architectural Detail: The HTTP Client Gap

The library builds URLs and parses responses, but does **not** execute HTTP write calls. The upstream ogc-client's built-in `fetch` usage is read-only (GET requests during endpoint discovery). For write operations (POST/PUT/DELETE), the consuming application must call `fetch()` directly using the URLs that `CSAPIQueryBuilder` produces, then pipe responses through the library's parsers. This is a thin layer — not a lot of code.

---

## What We're Doing Now

Building a **quick demo webapp** ("CSAPI Explorer") that uses the ogc-client-CSAPI_2 library to exercise **full CRUD** against live Connected Systems API servers. This validates the library end-to-end and demonstrates every capability added by our contribution.

### New Repository

The demo app lives in a fork of ogc-client-CSAPI_2:

- **Fork created from:** `OS4CSAPI/ogc-client-CSAPI_2`
- **Originally at:** `Sam-Bolling/ogc-client-CSAPI_2`
- **Intended transfer:** To `OS4CSAPI` org, renamed to `csapi-explorer`
- **Check current location:** Look at `https://github.com/OS4CSAPI/csapi-explorer` — if it doesn't exist yet, it may still be at `https://github.com/Sam-Bolling/ogc-client-CSAPI_2`

### Why a Fork (Not a New Repo)

The demo app imports the library directly from `../src/` (or `./src/` depending on where `demo/` lives). By forking the library repo, the full source is available for direct import with zero npm publishing or linking steps.

---

## Demo Servers

| Server        | URL                                      | Auth                             | Notes                          |
| ------------- | ---------------------------------------- | -------------------------------- | ------------------------------ |
| 52North       | `https://csa.demo.52north.org/`          | None                             | Public demo, full CRUD allowed |
| OSH SensorHub | `http://45.55.99.236:8080/sensorhub/api` | Basic auth (username + password) | Full CRUD allowed              |

The user has confirmed **CRUD permission on both servers**.

---

## Technical Decisions Made

| Decision                     | Choice                            | Rationale                                         |
| ---------------------------- | --------------------------------- | ------------------------------------------------- |
| **Where the demo app lives** | `demo/` folder in the forked repo | Direct `../src/` imports, zero setup              |
| **Framework**                | Vue 3 + Vite                      | Already the pattern in the library repo           |
| **UI Components**            | PrimeVue                          | DataTable, forms, tabs, sidebar out of the box    |
| **CORS handling**            | Vite dev server proxy             | ~10 lines of config, also handles auth injection  |
| **Map**                      | Skip for v1                       | Nice-to-have, not essential to proving CRUD works |
| **Deployment**               | Codespaces dev server             | No hosting needed, just `npm run dev`             |

---

## App Design

### Page 1: Server Configuration ("Data Source Manager")

- Text inputs for server URL, optional username/password
- "Connect" button → uses `OgcApiEndpoint` to discover capabilities
- Shows: conformance classes, available CSAPI collections, detected resource types
- Save/manage multiple server connections

### Page 2: Resource Explorer

- **Sidebar:** List of 9 resource types
- **Main area per resource type:**
  - **List:** Table with filter inputs (bbox, datetime, q, limit), pagination controls (offset-based AND cursor-based), refresh
  - **Detail:** Click a row → full JSON + parsed fields
  - **Create:** JSON editor or simple form → POST → show response
  - **Update:** Load existing → edit → PUT → show response
  - **Delete:** Select resource → DELETE → confirm

### Page 3 (optional, time permitting): Map View

- OpenLayers map showing spatial resources
- Click feature → detail panel

---

## Scope Tiers

### Must-have:

- Server connection with auth
- Vite proxy for CORS
- Discovery (show what the server supports)
- List resources (all 9 types) with basic filtering
- View single resource detail (raw JSON)
- Create a resource (JSON body input → POST)
- Update a resource (JSON body input → PUT)
- Delete a resource
- Both pagination styles demonstrated

### Nice-to-have:

- Map view for spatial resources
- Structured forms instead of raw JSON for create/update
- Pretty-printed parsed results
- SWE Common schema display for datastreams

### Skip:

- Production-quality error handling
- Responsive design
- Automated tests
- Deployment/hosting

---

## First Actions in the New Workspace

1. **Scaffold the demo app:**

   ```bash
   npm create vite@latest demo -- --template vue-ts
   cd demo
   npm install
   ```

2. **Add PrimeVue:**

   ```bash
   npm install primevue @primevue/themes primeicons
   ```

3. **Set up Vite proxy config** in `demo/vite.config.ts`:

   ```ts
   server: {
     proxy: {
       '/api/52north': {
         target: 'https://csa.demo.52north.org',
         changeOrigin: true,
         rewrite: (path) => path.replace(/^\/api\/52north/, ''),
       },
       '/api/osh': {
         target: 'http://45.55.99.236:8080/sensorhub/api',
         changeOrigin: true,
         rewrite: (path) => path.replace(/^\/api\/osh/, ''),
         // Basic auth header injection if needed:
         // headers: { Authorization: 'Basic ' + btoa('user:pass') }
       },
     },
   }
   ```

4. **Build a minimal server connection page first** to validate CORS and auth work before building out resource CRUD.

---

## Key Library Entry Points

The demo app will primarily use:

- **`OgcApiEndpoint`** — main entry point for endpoint discovery (`import { OgcApiEndpoint } from '../src/index'`)
- **`endpoint.csapi(collectionId)`** — returns a `CSAPIQueryBuilder` for a specific collection
- **`CSAPIQueryBuilder` methods** — `getSystems()`, `createSystem()`, `updateSystem(id)`, `deleteSystem(id)`, etc. for all 9 resource types
- **Response parsers** — `parseCollectionResponse()`, `extractCSAPIFeature()`, `parseSensorML30()`, `parseSWEComponent()`
- **Types** — `System`, `Deployment`, `Procedure`, `Observation`, `Command`, etc.

### Example Usage Pattern

```ts
import { OgcApiEndpoint } from '../src/index';

// Discover endpoint
const endpoint = new OgcApiEndpoint('http://localhost:5173/api/52north');
const builder = await endpoint.csapi('my-collection');

// READ (GET) — list systems
const url = builder.getSystems({ limit: 10 });
const response = await fetch(url);
const data = await response.json();

// CREATE (POST) — create a system
const createUrl = builder.createSystem();
const result = await fetch(createUrl, {
  method: 'POST',
  headers: { 'Content-Type': 'application/geo+json' },
  body: JSON.stringify(systemPayload),
});

// UPDATE (PUT)
const updateUrl = builder.updateSystem('system-id');
await fetch(updateUrl, { method: 'PUT', headers: {...}, body: JSON.stringify(updated) });

// DELETE
const deleteUrl = builder.deleteSystem('system-id');
await fetch(deleteUrl, { method: 'DELETE' });
```

---

## Important Notes

- **This is a quick, down-and-dirty demo** — not production code. Speed over polish.
- **The assessment doc** with full rationale is at `docs/webapp-demo/demo-app-assessment.md` in the ogc-client-CSAPI_2 repo.
- **The user's communication style:** Prefers discussion before action. Do NOT jump ahead and start executing tools/code without being asked. Present plans, get confirmation, then act.
- **Timeline:** Tight deadline. Ruthlessly limit scope to must-haves.
