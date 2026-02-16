# Demo App Scaffold — Implementation Report

> **Date**: 2026-02-16
> **Commit**: `1139dbb` — `feat: scaffold demo app with server connection page`
> **Location**: `demo/` directory in the repository root

---

## What We Did

Scaffolded the CSAPI Explorer demo webapp from scratch and built a working server connection page — the first functional milestone of the demo app. This involved:

1. Creating a new Vue 3 + Vite + TypeScript application in the `demo/` directory
2. Installing and configuring PrimeVue as the UI component library
3. Configuring Vite's dev server proxy to route requests to both target CSAPI servers
4. Building a `ServerConnect` component that connects to a server and displays its capabilities
5. Verifying that both proxies work against the live servers
6. Committing and pushing everything

Each step is detailed below.

---

## Step 1: Scaffold the App

### What We Did

Ran `npm create vite@latest demo -- --template vue-ts` from the repository root. This uses Vite's official project scaffolding tool to generate a minimal Vue 3 + TypeScript application.

### Why This Way

The session handoff document specified Vue 3 + Vite as the framework choice. Reasons:
- Already the pattern used in this repository (the existing `app/` directory uses the same stack)
- Vite provides the dev server proxy we need for CORS
- Fast HMR (Hot Module Replacement) for quick iteration
- Can import the CSAPI library directly from `../src/` with zero publishing steps

### What It Created

```
demo/
├── .gitignore            # Ignores node_modules, dist, etc.
├── index.html            # Entry HTML file (Vite's entry point)
├── package.json          # Project metadata and dependencies
├── package-lock.json     # Locked dependency versions
├── tsconfig.json         # Root TypeScript config (references app + node configs)
├── tsconfig.app.json     # TypeScript config for application code
├── tsconfig.node.json    # TypeScript config for Node tooling (vite.config.ts)
├── vite.config.ts        # Vite configuration (plugins, proxy, etc.)
├── public/
│   └── vite.svg          # Default favicon
├── src/
│   ├── main.ts           # Application entry point
│   ├── App.vue           # Root component
│   ├── style.css         # Global styles
│   ├── assets/
│   │   └── vue.svg       # Vue logo (from scaffold)
│   └── components/
│       └── ServerConnect.vue  # Our server connection component
└── README.md             # Scaffold readme
```

### What We Modified from the Default Scaffold

- **`index.html`** — Changed `<title>` from "demo" to "CSAPI Explorer"
- **`src/style.css`** — Replaced Vite's dark-theme boilerplate with a minimal light-theme base (white background, system fonts, no centering tricks)
- **`src/App.vue`** — Replaced the default Vite/Vue logo page with our app header and `ServerConnect` component
- **`src/main.ts`** — Added PrimeVue initialization (see Step 2)
- **`vite.config.ts`** — Added proxy configuration (see Step 3)
- **Deleted `HelloWorld.vue`** — Removed the default scaffold component we don't need

---

## Step 2: Install and Configure PrimeVue

### What We Did

Ran `npm install primevue @primevue/themes primeicons` inside the `demo/` directory, then configured PrimeVue in `main.ts`.

### What Was Installed

| Package | Purpose |
|---------|---------|
| `primevue` | Vue 3 UI component library — provides DataTable, form inputs, panels, buttons, tabs, etc. |
| `@primevue/themes` | Theme presets for PrimeVue — we use the "Aura" theme |
| `primeicons` | Icon font used by PrimeVue components (the `pi pi-link`, `pi pi-times` icons on buttons, etc.) |

### How PrimeVue Is Configured

In `demo/src/main.ts`:

```typescript
import PrimeVue from 'primevue/config'
import Aura from '@primevue/themes/aura'
import 'primeicons/primeicons.css'

const app = createApp(App)
app.use(PrimeVue, {
  theme: {
    preset: Aura,
  },
})
app.mount('#app')
```

This registers PrimeVue as a Vue plugin with the Aura theme preset. The Aura theme provides a modern, clean look out of the box with CSS custom properties for easy customization. PrimeIcons CSS is imported globally so icon classes work everywhere.

### Why PrimeVue

Per the assessment document: we need tables (resource listing), forms (server URL, auth, filters), tabs (resource types), and panels — basically a CRUD admin interface. PrimeVue provides all of these as drop-in components with built-in functionality (pagination on DataTable, masked password inputs, collapsible panels, etc.). This avoids writing UI from scratch and keeps our custom code focused on CSAPI logic.

---

## Step 3: Configure the Vite Dev Server Proxy

### What We Did

Added a `server.proxy` configuration to `demo/vite.config.ts`:

```typescript
export default defineConfig({
  plugins: [vue()],
  server: {
    proxy: {
      '/api/52north': {
        target: 'https://csa.demo.52north.org',
        changeOrigin: true,
        secure: false, // their SSL cert is expired as of 2026-02-16
        rewrite: (path) => path.replace(/^\/api\/52north/, ''),
      },
      '/api/osh': {
        target: 'http://45.55.99.236:8080/sensorhub/api',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/osh/, ''),
      },
    },
  },
})
```

### How It Works

When the browser makes a request to `http://localhost:5173/api/52north/collections`, Vite intercepts it **server-side** and forwards it to `https://csa.demo.52north.org/collections`. The response comes back through Vite to the browser. From the browser's perspective, it's talking to `localhost:5173` — same origin — so CORS never enters the picture.

The `rewrite` function strips the proxy prefix from the URL before forwarding. So:
- `http://localhost:5173/api/52north/conformance` → `https://csa.demo.52north.org/conformance`
- `http://localhost:5173/api/osh/systems` → `http://45.55.99.236:8080/sensorhub/api/systems`

### Why Each Option

| Option | Purpose |
|--------|---------|
| `target` | The actual server URL to forward requests to |
| `changeOrigin: true` | Sets the `Host` header to match the target (required for virtual-hosted servers) |
| `secure: false` | **52North only** — disables SSL certificate verification because their cert is expired (see CORS test report) |
| `rewrite` | Strips the `/api/52north` or `/api/osh` prefix so the target server sees clean paths |

### Why a Proxy at All

Our [CORS preflight test](cors-preflight-test-results.md) established that:
- **52North** fails CORS preflight for write operations (missing `Access-Control-Allow-Methods` and `Access-Control-Allow-Headers` in OPTIONS response) AND has an expired SSL certificate
- **OSH SensorHub** has full CORS support and could work without a proxy

The proxy solves both problems:
1. Bypasses CORS entirely (requests come from the same origin)
2. Bypasses the browser's SSL certificate check (Vite handles the connection server-side with `secure: false`)
3. Can inject `Authorization` headers for OSH without exposing credentials in browser-side code (future enhancement)
4. Gives us a uniform request pattern — all server requests go through `/api/{server}/...` regardless of which server

---

## Step 4: Build the Server Connection Page

### What We Built

The `ServerConnect.vue` component is the first page of the demo app (Page 1 in the design spec: "Data Source Manager"). It's located at `demo/src/components/ServerConnect.vue`.

### What It Does

1. **Server selection** — A dropdown with three options:
   - "52North CSA Demo" → routes through `/api/52north`
   - "OSH SensorHub" → routes through `/api/osh`
   - "Custom URL" → shows a text input for any URL

2. **Authentication** — Optional username and password fields (password is masked with a toggle to show it). These are used to construct a `Basic` auth header.

3. **Connect** — Clicking "Connect" triggers three sequential fetches through the proxy:
   - `GET {baseUrl}/` — the OGC API landing page (server title, description, links)
   - `GET {baseUrl}/conformance` — the list of conformance classes the server implements
   - `GET {baseUrl}/collections` — the list of collections (resource groupings) available

4. **Results display** — After connecting, the page shows:
   - **Server Info** panel — title and description from the landing page
   - **Conformance Classes** panel — split into two sections:
     - CSAPI / SensorML / SWE Common classes (the ones relevant to our library)
     - Other OGC API conformance classes
   - **Collections** panel — a table showing each collection's ID, title, and description
   - **Raw Response** panel — collapsed by default, shows the complete JSON from all three requests

5. **Disconnect** — Resets everything back to the initial state

### How It Works Internally

The component uses Vue 3 Composition API (`<script setup lang="ts">`):

- **`selectedPreset`** — reactive ref holding the currently selected server preset (or "Custom URL")
- **`connectionResult`** — reactive object holding the connection state: `connected`, `landingPage`, `conformance`, `collections`, and `raw`
- **`getEffectiveUrl()`** — returns either the preset's proxy path (e.g., `/api/52north`) or the custom URL
- **`getAuthHeaders()`** — if username and password are filled in, returns an object with `Authorization: Basic <base64>` header; otherwise returns empty object
- **`connect()`** — async function that fetches landing page, conformance, and collections in sequence, populating `connectionResult`
- **`csapiConformance()` / `otherConformance()`** — filter functions that separate CSAPI-related conformance URIs from other OGC API conformance URIs for cleaner display

PrimeVue components used:
| Component | What For |
|-----------|----------|
| `Select` | Server preset dropdown |
| `InputText` | Custom URL and username fields |
| `Password` | Password field with show/hide toggle |
| `Button` | Connect/Disconnect with loading state and icons |
| `Panel` | Collapsible sections for results |
| `Message` | Error display |
| `ProgressSpinner` | Loading indicator during connection |

### Why This First

Per the handoff doc: *"Build a minimal server connection page first to validate CORS and auth work before building out resource CRUD."* This is the foundational piece — if we can't connect to the servers and see what they support, nothing else works.

This page also serves as a verification step: when you hit Connect and see conformance classes and collections come back, you know the proxy is working, the server is reachable, and the response format is what we expect.

---

## Step 5: Verification

### Proxy Test Results

With the dev server running (`cd demo && npm run dev`), we verified both proxies using curl:

**52North** (`http://localhost:5173/api/52north/`):
```json
{
  "title": "connected-systems-pygeoapi",
  "description": "OGC Connected-Systems API",
  "links": [
    {"rel": "conformance", "href": "https://csa.demo.52north.org/conformance"},
    {"rel": "data", "href": "https://csa.demo.52north.org/collections"},
    ...
  ]
}
```

**OSH SensorHub** (`http://localhost:5173/api/osh/`):
```json
{
  "title": "Connected Systems API Service",
  "links": [
    {"rel": "conformance", "href": "http://45.55.99.236:8080/sensorhub/api/conformance"},
    ...
  ]
}
```

Both returned valid JSON landing pages through the proxy, confirming:
- Vite's proxy routing works correctly for both servers
- The URL rewriting strips prefixes properly
- `secure: false` successfully bypasses 52North's expired SSL cert
- No CORS issues (requests originate from the same domain)

### App UI Test

Opened `http://localhost:5173` in the VS Code Simple Browser — the app renders with the CSAPI Explorer header and the server connection form.

---

## Step 6: Commit and Push

Committed all 15 files (demo app scaffold + our modifications) with a descriptive message, then pushed to origin.

**Files committed:**
```
demo/.gitignore
demo/README.md
demo/index.html
demo/package.json
demo/package-lock.json
demo/public/vite.svg
demo/src/App.vue
demo/src/assets/vue.svg
demo/src/components/ServerConnect.vue
demo/src/main.ts
demo/src/style.css
demo/tsconfig.json
demo/tsconfig.app.json
demo/tsconfig.node.json
demo/vite.config.ts
```

---

## What's Next

With the server connection page working, the next milestone is **Page 2: Resource Explorer**. This involves:

1. **Router setup** — Vue Router to navigate between the connection page and the resource explorer
2. **Sidebar** — List of 9 CSAPI resource types (Systems, Deployments, Procedures, SamplingFeatures, Properties, Datastreams, Observations, ControlStreams, Commands)
3. **Resource listing** — DataTable showing resources fetched from the server, with filter inputs (bbox, datetime, q, limit) and pagination (both offset-based and cursor-based)
4. **Resource detail** — Click a row to see full JSON + parsed fields
5. **CRUD operations** — Create (POST), Update (PUT), Delete (DELETE) for each resource type

The server connection component will evolve to pass the active connection (base URL + auth headers) to the resource explorer components.

---

## How to Run

```bash
cd demo
npm install    # only needed first time
npm run dev    # starts Vite dev server at http://localhost:5173
```

Select a server preset from the dropdown, optionally enter credentials for OSH SensorHub, and click Connect.
