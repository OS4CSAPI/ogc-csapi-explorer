# CSAPI Demo Webapp — Assessment & Recommendations

## The "HTTP Client" Gap — What It Means

Our work in the ogc-client library built three things:

1. **URL builders** — `CSAPIQueryBuilder` constructs the correct URL for any CRUD operation on any resource type
2. **Response parsers** — parse GeoJSON features, SensorML documents, SWE Common schemas, collection responses, pagination envelopes
3. **Type definitions** — TypeScript interfaces for all 9 resource types, query options, status codes, etc.

What the library does NOT do is **execute** the HTTP calls for write operations. It tells you _where_ to send a POST/PUT/DELETE and how to _parse_ what comes back, but it doesn't perform the mutation itself. The upstream ogc-client has always been a discovery/parsing library — its built-in `fetch` usage is only for GET requests during endpoint discovery.

**For a demo app, this means:** you use our library to discover endpoints and build URLs, then call `fetch()` yourself with the right method and body. This is not a huge amount of code — it's a thin layer on top of what we built. A generic function that does `fetch(builder.createSystem(), { method: 'POST', body: JSON.stringify(payload) })` and then pipes the response through our parsers.

**On the testing gap:** The unit test architecture (mocked HTTP responses) is standard practice for library development, but it does mean writes were only validated at the URL-construction and response-parsing level, not end-to-end against real servers. That's exactly the gap this demo app would close.

---

## CORS — The Real Technical Risk

When a webapp in a browser makes requests to a different domain (the demo servers), the browser enforces CORS. If those servers don't send `Access-Control-Allow-Origin` headers, _every request gets blocked_ — not by the server, but by the browser itself.

**The fix is simple: a Vite dev server proxy.** The browser talks to `localhost:5173/api/52north/...`, Vite forwards it to `csa.demo.52north.org/...` server-side, and CORS never enters the picture. This also solves the basic auth problem — the proxy can inject `Authorization` headers so credentials never touch the browser. This works identically in Codespaces (Codespaces forwards the dev server port).

This is a ~10-line config. It's proven, reliable, and how most dev setups handle this.

---

## Architecture: Where Should This Live?

| Option                                  | Pros                                  | Cons                                                                             |
| --------------------------------------- | ------------------------------------- | -------------------------------------------------------------------------------- |
| **A) Inside `app/` (existing Vue app)** | Zero setup, already imports library   | Wrong design pattern (it's a docs site), mixes concerns, adds weight to upstream |
| **B) New folder `demo/` in our repo**   | Can import `../src/` directly, simple | Still in the library repo, not cleanly separated                                 |
| **C) Fork our fork, build there**       | Has library code                      | Confusing (fork of a fork), overkill                                             |
| **D) New standalone repo**              | Cleanest separation                   | Must solve library consumption (npm link or copy) — adds friction                |

**Recommendation: Option B** — a `demo/` folder in our existing repo. Reasons:

- Importing from `../src/` "just works" with zero publishing/linking steps
- It's isolated from `app/` (doesn't touch the upstream demo site)
- When we're done, we can delete it or keep it as validation evidence
- Fastest path to running code

If we later want to share it separately, extracting to its own repo is easy. Starting there adds friction we don't need right now.

---

## Framework: What to Build With

For a "quick and dirty CRUD explorer," what we need is:

- Forms (server URL, auth, query filters, resource creation/editing)
- Tables (resource listing with pagination)
- Tabs/navigation (9 resource types)
- Optionally a map

**Vue 3 + Vite** is the clear winner here:

- Already the pattern in this repo
- Vite proxy config for CORS is trivial
- Fast HMR dev loop
- Can import our library directly

For UI components (tables, forms, tabs without building from scratch), options include **PrimeVue**, **Vuetify**, or even just **raw HTML + minimal CSS**. PrimeVue gives us DataTable with built-in pagination, form inputs, tab panels, sidebar — basically everything we need — with zero CSS work. But it's another dependency. Plain HTML with a tiny bit of CSS works too for absolute minimal dependencies.

For a map, **OpenLayers** is already a dependency of the upstream library. Or we skip the map for v1 and add it only if time allows. A map is nice but not essential to proving CRUD works.

---

## What Existing Tools Could Do This?

- **Swagger UI / OpenAPI explorers** — These servers likely expose OpenAPI docs. You can test CRUD directly. BUT this doesn't demonstrate _our library_ at all — it tests the server, not our code.
- **Postman / Insomnia** — Same problem. Great for API testing, doesn't validate our library.
- **React Admin / Refine** — CRUD admin panel frameworks with tables, forms, filters, pagination built in. They're powerful but expect a specific data provider pattern and are React-based. Adding React alongside our Vue setup would be friction.
- **Retool / Appsmith** — Low-code tools, but overkill and add SaaS dependency.

The honest answer: **no existing tool directly demos "our library talking to CSAPI servers."** That's inherently custom. But we can leverage component libraries (PrimeVue) to avoid building UI from scratch, making the custom parts thin.

---

## What the Demo App Would Actually Look Like

### Page 1: Server Configuration

- Text inputs for server URL, optional username/password
- "Connect" button → uses `OgcApiEndpoint` to discover capabilities
- Shows: conformance classes, available CSAPI collections, detected resource types
- Save multiple servers (52North + OSH)

### Page 2: Resource Explorer (per resource type)

- Sidebar: list of 9 resource types (Systems, Deployments, Procedures, etc.)
- Main area:
  - **List tab**: Table showing resources, filter inputs (bbox, datetime, q, limit), pagination controls (offset-based and cursor-based), "Refresh" button
  - **Detail tab**: Click a row → show full JSON + parsed fields
  - **Create tab**: JSON editor or simple form → POST → show response
  - **Update tab**: Load existing → edit → PUT → show response
  - **Delete tab**: Select resource → DELETE → confirm

### Page 3 (optional): Map View

- OpenLayers map showing systems/deployments/sampling features with geometry
- Click feature → detail panel

---

## Realistic Scope and Timeline

For a tight deadline, here's what to tier:

### Must-have (core demo, ~4-5 hours of implementation):

- Server connection with auth
- Vite proxy for CORS
- Discovery (show what the server supports)
- List resources (all 9 types) with basic filtering
- View single resource detail (raw JSON)
- Create a resource (JSON body input → POST)
- Update a resource (JSON body input → PUT)
- Delete a resource
- Both pagination styles demonstrated

### Nice-to-have (if time allows):

- Map view for spatial resources
- Structured forms instead of raw JSON for create/update
- Pretty-printed parsed results (not just raw JSON)
- SWE Common schema display for datastreams

### Skip entirely:

- Production-quality error handling
- Responsive design
- Automated tests for the demo app
- Deployment/hosting (Codespaces dev server is sufficient)

---

## Feasibility Assessment

**Is this doable? Yes.** The technical pieces are all solved problems:

- Vue 3 + Vite scaffolding: proven
- Vite proxy for CORS: ~10 lines of config
- `fetch()` with POST/PUT/DELETE: basic browser API
- Our library for URL building + response parsing: already built and tested
- PrimeVue for tables/forms: drop-in components

**Main risks:**

1. Server availability — demo servers might be down when we need them
2. Server-specific quirks — different servers may return slightly different response shapes
3. Auth flow — basic auth through a proxy is straightforward, but if a server uses something else (OAuth, API keys), it's more work
4. Time — keeping scope ruthlessly limited is critical

---

## Bottom Line

Recommended approach: a `demo/` folder in our current repo, Vue 3 + Vite, PrimeVue for UI components, Vite proxy for CORS/auth, and a focused scope of server config + resource CRUD for all 9 types. No map in v1. Codespaces dev server for running it.

### Demo Servers

- 52North: `https://csa.demo.52north.org/`
- OSH SensorHub: `http://45.55.99.236:8080/sensorhub/api` (basic auth required)
