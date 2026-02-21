# CSAPI Explorer

> A demo webapp for exploring and assessing live [OGC Connected Systems API](https://docs.ogc.org/DRAFTS/23-001r1.html) (CSAPI) server deployments

## About

**CSAPI Explorer** was originally built to validate the developmental OGC CSAPI client library contribution to the upstream [ogc-client](https://github.com/camptocamp/ogc-client) project (via the [ogc-client-CSAPI_2](https://github.com/OS4CSAPI/ogc-client-CSAPI_2) fork). It exercised every aspect of the library — endpoint discovery, resource parsing, query building, content negotiation, SWE Common schema handling — against real servers, and the findings from that validation work drove dozens of upstream library fixes.

Now that the library contribution has matured, CSAPI Explorer's purpose has shifted: it exists as a **standalone tool for demoing and assessing live CSAPI server deployments**. It lets you connect to any CSAPI-compliant server and interactively browse, inspect, and test all nine resource types defined by the OGC Connected Systems API (Parts 1 & 2).

## Features

- **Server Connection & Diagnostics** — Connect to any CSAPI server URL with automatic endpoint discovery, conformance class detection, transport security checks (HTTPS, SSL certificate, CORS), and detailed diagnostic reporting
- **Resource Explorer** — Browse all 9 CSAPI resource types (Systems, Procedures, Deployments, Sampling Features, Properties, Datastreams, Observations, Control Streams, Commands) with filtering, pagination, and nested resource navigation
- **Interactive Data Model Diagram** — Live SVG visualization of the SOSA/SSN-grounded CSAPI data model showing resource relationships, with real-time count badges and click-to-navigate between related resources
- **Parsed Resource Views** — Structured display of GeoJSON features, SensorML documents, SWE Common data records, and raw JSON with inline schema rendering
- **CRUD Operations** — Create, update, and delete resources directly on writable servers
- **Map View** — OpenLayers-based geographic visualization of systems, deployments, and observation data with automatic location resolution
- **Automated Smoke Test** — One-click endpoint coverage test that probes all resource types and generates a pass/fail report

## Preconfigured Servers

The demo ships with proxy routes for two test servers:

| Server | URL | Notes |
|--------|-----|-------|
| **OSH SensorHub** | `http://45.55.99.236:8080/sensorhub/api` | Full CSAPI Part 1 & Part 2 implementation |
| **52North** | `https://csa.demo.52north.org` | Part 1 only (Part 2 endpoints non-functional) |

You can also connect to any custom CSAPI server URL.

## Getting Started

### Prerequisites

- [Node.js](https://nodejs.org/) v20 or later
- npm (included with Node.js)

### Setup

```bash
# Clone the repository
git clone https://github.com/OS4CSAPI/ogc-csapi-explorer.git
cd ogc-csapi-explorer

# Install the root dependencies (the CSAPI client library)
npm install

# Install the demo app dependencies
cd demo
npm install
```

### Run the Demo App

```bash
# From the demo/ directory
npm run dev
```

This starts the Vite dev server at **http://localhost:5173**. The dev server includes proxy routes for the preconfigured test servers, so you can connect immediately without CORS issues.

### Build for Production

```bash
# From the demo/ directory
npm run build
npm run preview
```

### Adding a Custom Server Proxy

To proxy a new CSAPI server through the Vite dev server (avoids CORS issues), add an entry to [`demo/vite.config.ts`](demo/vite.config.ts):

```typescript
'/api/my-server': {
  target: 'https://my-csapi-server.example.com',
  changeOrigin: true,
  rewrite: (path) => path.replace(/^\/api\/my-server/, ''),
},
```

Then connect using `/api/my-server` as the server URL in the app.

## Repository Structure

```
demo/             → CSAPI Explorer demo webapp (Vue 3 + PrimeVue + Vite)
src/              → Upstream ogc-client library source (including CSAPI contribution)
docs/             → Evaluation reports, findings, governance docs
examples/         → E2E test scripts for cross-server validation
fixtures/         → Test fixtures for the library test suite
```

## Upstream Library

This repository is a fork of [camptocamp/ogc-client](https://github.com/camptocamp/ogc-client), synced via the [OS4CSAPI/ogc-client-CSAPI_2](https://github.com/OS4CSAPI/ogc-client-CSAPI_2) contribution project. The `src/` directory contains the full ogc-client library with the CSAPI extension (endpoint discovery, query builder, GeoJSON/Part 2 parsers, SWE Common support). The demo app imports directly from `src/` via the `@csapi` path alias — no published package required.

## License

[ISC](./LICENSE)
