# Phase 2.2 Implementation Overview — Where We Stand Now

## The Story So Far

Phase 1 built the **foundation**: a type system, helper utilities, a stub query builder, and the endpoint integration that wired everything into `OgcApiEndpoint`.

Phase 2.1 (Issue #5) turned that stub into a **complete Systems surface** — 12 methods covering reading, writing, history, hierarchy, and cross-resource navigation for the Systems resource type.

After Phase 2.1, we did a **live smoke test** against the OpenSensorHub demo server (`http://45.55.99.236:8080/sensorhub/api`). That test revealed four findings:

- **F1**: The server uses different link relation conventions than we expected
- **F2**: The server exposes top-level resource URLs in its root document, not just within collections
- **F3**: List responses use an `items` envelope instead of GeoJSON `features` (Phase 3 concern)
- **F4**: The `validTime` field comes as an array instead of an ISO 8601 string (Phase 3 concern)

Phase 2.2 fixed F1 and F2, implemented the full Deployments resource surface, and re-tested everything against the live server to confirm the fixes work.

---

## What Changed Since Phase 2.1

### Issue #34 — Three Link Relation Conventions (F1 Fix)

**The problem**: Our builder only recognized `ogc-cs:systems` style link relations. The live server uses two other conventions: plain resource names as `rel` values (e.g., `rel: "systems"`) and `rel: "items"` links where the `href` path ends in a resource type name (e.g., `href: ".../systems"`).

**The fix**: `extractAvailableResources()` now recognizes all three conventions:

```typescript
// Convention 1 — ogc-cs: prefix (original)
{ rel: "ogc-cs:systems", href: ".../systems" }

// Convention 2 — plain resource name as rel
{ rel: "systems", href: ".../systems" }

// Convention 3 — rel:"items" with resource type in href path
{ rel: "items", href: ".../systems" }
```

The method imports `CSAPIResourceTypes` to validate that plain `rel` values and `href` path segments actually match known resource types — `"self"`, `"alternate"`, or any other non-CSAPI relation is safely ignored.

Each discovered resource type is added to the `availableResources` set once, regardless of how many conventions point to it. A single collection document can contain links using a mix of all three conventions.

### Issue #35 — Top-Level Resource URLs (F2 Fix)

**The problem**: The builder always computed URLs relative to a collection: `{baseUrl}/collections/{id}/systems`. But the live server's root document exposes **absolute resource URLs** that are not scoped to a collection at all — for example, `http://server.com/sensorhub/api/systems`. If the client ignores these, it must guess paths that the server may not support.

**The fix**: Two changes, one in the builder and one in the endpoint.

In `CSAPIQueryBuilder`:

```typescript
// Constructor now accepts an optional map of resource type → absolute URL
constructor(collection: OgcApiCollectionInfo, resourceUrls?: Map<string, string>)

// buildResourceUrl() checks the map first:
//   If map has an entry for the resource type → use that absolute URL as the base
//   Otherwise → fall back to collection-scoped path construction
```

In `endpoint.ts`:

```typescript
// New method extracts resource URLs from the root API document
extractRootResourceUrls(rootDoc: OgcApiDocument): Map<string, string>

// csapi() factory now calls extractRootResourceUrls() and passes the result
// to the builder constructor
const resourceUrls = this.extractRootResourceUrls(rootDoc);
const builder = new CSAPIQueryBuilder(collection, resourceUrls);
```

The extraction uses the same three-convention approach as `extractAvailableResources()`. This means the top-level URL map is populated regardless of which convention the server uses for its root document links.

### Issue #6 — Deployments Methods

With the infrastructure fixes in place, Deployments followed the same pattern as Systems. Eight new public methods:

```typescript
// ── Reading ──
builder.getDeployments({ limit: 10, systemId: 'sys-001' });
builder.getDeployment('dep-001');

// ── Writing ──
builder.createDeployment();
builder.updateDeployment('dep-001');
builder.deleteDeployment('dep-001');

// ── Hierarchy ──
builder.getDeploymentSubdeployments('dep-001', { recursive: true });

// ── Navigation ──
builder.getDeploymentSystems('dep-001');

// ── History ──
builder.getDeploymentHistory('dep-001', { limit: 5 });
```

`DeploymentQueryOptions` extends the base `QueryOptions` with three additional fields:

| Field       | Type      | Purpose                                       |
| ----------- | --------- | --------------------------------------------- |
| `parent`    | `string`  | Filter by parent deployment ID                |
| `systemId`  | `string`  | Filter deployments by the system they contain |
| `recursive` | `boolean` | Include nested sub-deployments at all levels  |

These get serialized alongside the base query parameters (limit, offset, bbox, datetime, q, id) by the same `buildQueryString()` pipeline.

---

## Live Server Re-Test Results

After merging the F1 and F2 fixes, we re-tested against the OpenSensorHub demo server to verify the changes work in practice.

### Root Document

The server's root document (`/sensorhub/api`) contains links like:

```json
{ "rel": "systems", "href": "http://45.55.99.236:8080/sensorhub/api/systems" }
{ "rel": "deployments", "href": "http://45.55.99.236:8080/sensorhub/api/deployments" }
{ "rel": "procedures", "href": "http://45.55.99.236:8080/sensorhub/api/procedures" }
{ "rel": "samplingFeatures", "href": "http://45.55.99.236:8080/sensorhub/api/featuresOfInterest" }
```

These use **Convention 2** (plain resource names). `extractRootResourceUrls()` now captures them all, producing a `Map<string, string>` that the builder uses for absolute URL construction.

### Collection Documents

The server's `all` collection (`/sensorhub/api/collections/all`) contains links like:

```json
{ "rel": "items", "href": "http://45.55.99.236:8080/sensorhub/api/collections/all/items" }
{ "rel": "items", "href": "http://45.55.99.236:8080/sensorhub/api/systems" }
```

The first is a generic items link (ignored — doesn't end in a known resource type). The second uses **Convention 3** (`rel: "items"` with resource type in href). Our builder now recognizes both cases correctly — capturing the second and ignoring the first.

### Confirmation

- **F1 (link conventions)**: All three conventions are recognized. The OpenSensorHub server's mix of Convention 2 (root) and Convention 3 (collections) is fully handled.
- **F2 (top-level URLs)**: Absolute URLs from the root document are captured and used as base URLs by the builder. No collection-scoped path guessing is needed when the root document provides direct URLs.

The detailed re-test report is at `docs/implementation/live-server-retest-post-issues-34-35.md`.

---

## What Each Deployment Operation Does

### Reading — `getDeployments` and `getDeployment`

`getDeployments` lists all deployments with optional filtering. Beyond the base parameters (limit, bbox, datetime, q), you can filter by `parent` (only sub-deployments of a specific parent), `systemId` (only deployments containing a specific system), or `recursive` (include all levels of nesting).

`getDeployment` fetches a single deployment by ID.

### Writing — `createDeployment`, `updateDeployment`, `deleteDeployment`

Same pattern as Systems. These produce target URLs for POST, PUT, and DELETE respectively. The builder doesn't execute the HTTP request — it constructs the URL you'd pass to `fetch()`.

### Hierarchy — `getDeploymentSubdeployments`

Deployments can nest. A regional deployment might contain site-level deployments, which contain individual sensor deployments. `getDeploymentSubdeployments` builds the URL for `/deployments/{id}/subdeployments` and supports `DeploymentQueryOptions` for filtering the children.

### Navigation — `getDeploymentSystems`

A deployment contains systems. `getDeploymentSystems('dep-001')` builds `/deployments/dep-001/systems` to list the systems deployed at a particular site.

### History — `getDeploymentHistory`

Like systems, deployments are versioned. Metadata changes (relocation, reconfiguration) produce historical versions. `getDeploymentHistory` builds the URL to list them.

---

## How The Architecture Has Evolved

### Before Phase 2.2

```
Collection document → discover resources → build collection-scoped URLs
                           ↓
                    Only ogc-cs: prefix convention
```

### After Phase 2.2

```
Root document → extract absolute resource URLs (Map<string, string>)
                         ↓
Collection document → discover resources (3 conventions)
                         ↓
buildResourceUrl() → check resourceUrls map first
                   → if found: use absolute URL as base
                   → if not: fall back to collection-scoped path
                         ↓
                   append ID / sub-path / query string
```

The three-convention resource discovery makes the builder **spec-tolerant** — it works with servers that follow the ogc-cs: convention, servers that use plain rel names, and servers that use the generic items pattern. The top-level URL support means the builder can work at two scopes:

- **Collection-scoped**: `https://server.com/api/collections/iot/systems` (computed)
- **Root-scoped**: `https://server.com/api/systems` (from the server's own root document)

The root-scoped approach is preferred when available because it uses URLs the server explicitly advertised.

### All 20 Public Methods

| #   | Method                        | Resource    | Pattern                                       |
| --- | ----------------------------- | ----------- | --------------------------------------------- |
| 1   | `getSystems`                  | Systems     | Collection list with `SystemQueryOptions`     |
| 2   | `getSystem`                   | Systems     | Single item by ID                             |
| 3   | `createSystem`                | Systems     | POST target                                   |
| 4   | `updateSystem`                | Systems     | PUT target                                    |
| 5   | `deleteSystem`                | Systems     | DELETE target                                 |
| 6   | `getSystemHistory`            | Systems     | `/systems/{id}/history`                       |
| 7   | `getSystemSubsystems`         | Systems     | `/systems/{id}/subsystems`                    |
| 8   | `getSystemDataStreams`        | Systems     | `/systems/{id}/datastreams`                   |
| 9   | `getSystemControlStreams`     | Systems     | `/systems/{id}/controlstreams`                |
| 10  | `getSystemSamplingFeatures`   | Systems     | `/systems/{id}/samplingFeatures`              |
| 11  | `getSystemDeployments`        | Systems     | `/systems/{id}/deployments`                   |
| 12  | `getSystemProcedures`         | Systems     | `/systems/{id}/procedures`                    |
| 13  | `getDeployments`              | Deployments | Collection list with `DeploymentQueryOptions` |
| 14  | `getDeployment`               | Deployments | Single item by ID                             |
| 15  | `createDeployment`            | Deployments | POST target                                   |
| 16  | `updateDeployment`            | Deployments | PUT target                                    |
| 17  | `deleteDeployment`            | Deployments | DELETE target                                 |
| 18  | `getDeploymentSubdeployments` | Deployments | `/deployments/{id}/subdeployments`            |
| 19  | `getDeploymentSystems`        | Deployments | `/deployments/{id}/systems`                   |
| 20  | `getDeploymentHistory`        | Deployments | `/deployments/{id}/history`                   |

---

## The Complete File Inventory

### Source Files

| File                               | Lines | Purpose                                                                                         |
| ---------------------------------- | ----- | ----------------------------------------------------------------------------------------------- |
| `src/ogc-api/csapi/model.ts`       | 542   | Type system — 9 resource types, 10 query options interfaces, collection types, constants        |
| `src/ogc-api/csapi/helpers.ts`     | 145   | 6 pure utility functions — temporal formatting, encoding, validation                            |
| `src/ogc-api/csapi/url_builder.ts` | 612   | `CSAPIQueryBuilder` class — 20 methods (12 Systems + 8 Deployments) + private infrastructure    |
| `src/ogc-api/endpoint.ts`          | 820   | Integration — `hasConnectedSystems`, `csapiCollections`, `csapi()`, `extractRootResourceUrls()` |

### Test Files

| File                                         | Tests | Coverage                                                                                                 |
| -------------------------------------------- | ----- | -------------------------------------------------------------------------------------------------------- |
| `src/ogc-api/csapi/model.spec.ts`            | 27    | Every resource interface, constant correctness, type compatibility                                       |
| `src/ogc-api/csapi/helpers.spec.ts`          | 30    | All 6 helpers with edge cases, error paths, encoding correctness                                         |
| `src/ogc-api/csapi/url_builder.spec.ts`      | 71    | Constructor (10), resource validation (4), top-level URLs (7), 12 Systems methods, 8 Deployments methods |
| `src/ogc-api/endpoint.spec.ts` (CSAPI block) | 6     | End-to-end with fixture data: detection, collection filtering, builder creation, caching, error handling |

**Total: 128 CSAPI unit tests + 6 integration tests = 134 tests (128 passing in CSAPI suite, 82/83 in endpoint suite — 1 pre-existing failure unrelated to CSAPI).**

### Documentation Files (This Phase)

| File                                                          | Purpose                                                   |
| ------------------------------------------------------------- | --------------------------------------------------------- |
| `docs/implementation/live-server-retest-post-issues-34-35.md` | Detailed smoke re-test results confirming F1 and F2 fixes |
| `docs/implementation/phase-2.2-overview.md`                   | This document                                             |

---

## How The Tests Are Organized

The CSAPI test structure added two new layers since Phase 2.1:

### Constructor Tests (10 tests, up from 4)

The constructor now has 10 tests covering:

- Base URL extraction from `self` link
- Resource discovery via `ogc-cs:` prefix convention (original)
- Resource discovery via plain `rel` names matching known types (new — F1)
- Resource discovery via `rel:"items"` with resource type in `href` (new — F1)
- Mixed convention discovery in the same collection (new — F1)
- Rejection of unknown plain `rel` values that aren't CSAPI types (new — F1)
- Rejection of `rel:"items"` when `href` doesn't match a known type (new — F1)
- Empty links and missing links edge cases

### Top-Level URL Tests (7 tests, new)

A dedicated describe block for F2:

- Collection-scoped builder still works without change (regression guard)
- Builder uses absolute URL from `resourceUrls` map
- ID appending with top-level URLs
- Sub-path appending (`/systems/{id}/history`)
- Query parameter appending
- Special character encoding in IDs
- Trailing slash normalization

### Deployment Tests (16 tests, new)

Organized in five describe blocks mirroring the Systems tests:

| Block                         | Tests | What It Verifies                                                                    |
| ----------------------------- | ----- | ----------------------------------------------------------------------------------- |
| `getDeployments`              | 3     | No options, with limit, with `DeploymentQueryOptions` (parent, systemId, recursive) |
| `getDeployment`               | 2     | Basic URL, special-char encoding                                                    |
| Deployment CRUD               | 3     | Create (POST target), Update (PUT target), Delete (DELETE target)                   |
| `getDeploymentSubdeployments` | 3     | Basic URL, recursive=true, with pagination                                          |
| Association and history       | 3     | `getDeploymentSystems` basic, with options; `getDeploymentHistory` basic            |
| Validation                    | 2     | Throws on unavailable `deployments`, throws on unavailable `systems` for navigation |

---

## How The Pieces Fit Together

Here's the developer experience now, showing the expanded architecture:

```typescript
import { OgcApiEndpoint } from 'ogc-client';

const endpoint = new OgcApiEndpoint('https://sensors.example.com/api');

if (await endpoint.hasConnectedSystems) {
  // Builder now leverages top-level URLs from root document
  const builder = await endpoint.csapi('weather-stations');

  // ── Systems (Phase 2.1) ──
  const systems = builder.getSystems({ limit: 20, recursive: true });
  const system = builder.getSystem('station-42');
  const create = builder.createSystem();
  const streams = builder.getSystemDataStreams('station-42');
  const history = builder.getSystemHistory('station-42');
  const subs = builder.getSystemSubsystems('station-42', { recursive: true });

  // ── Deployments (Phase 2.2) ──
  const deployments = builder.getDeployments({
    limit: 10,
    systemId: 'station-42',
    recursive: true,
  });
  const deployment = builder.getDeployment('dep-001');
  const createDep = builder.createDeployment();
  const updateDep = builder.updateDeployment('dep-001');
  const deleteDep = builder.deleteDeployment('dep-001');
  const subdeps = builder.getDeploymentSubdeployments('dep-001');
  const depSystems = builder.getDeploymentSystems('dep-001');
  const depHistory = builder.getDeploymentHistory('dep-001', { limit: 5 });
}
```

Every URL produced is:

- **Server-derived** — base URLs come from the server's own documents, never hardcoded
- **Spec-tolerant** — works with any of the three link relation conventions
- **Scope-aware** — uses root-level absolute URLs when available, collection-scoped paths as fallback
- **Validated** — unsupported resources produce clear errors listing what is available
- **Encoded correctly** — special characters in IDs are percent-encoded, query params use URLSearchParams

---

## What Comes Next

Phase 2.2 completed Systems and Deployments. The remaining Phase 2 issues will add the other seven resource types:

| Issue | Resource Types   | Methods              | Notes                                                            |
| ----- | ---------------- | -------------------- | ---------------------------------------------------------------- |
| #7    | Procedures       | ~5 CRUD + history    | Simple Part 1 resource                                           |
| #8    | SamplingFeatures | ~5 CRUD + history    | Simple Part 1 resource                                           |
| #9    | Properties       | ~5 CRUD + history    | Simple Part 1 resource                                           |
| #10   | DataStreams      | ~6 CRUD + navigation | Part 2; has `observedPropertyId`, `phenomenonTime`, `resultTime` |
| #11   | Observations     | ~5 CRUD              | Part 2; has `datastreamId`, `foiId`, temporal params             |
| #12   | ControlStreams   | ~5 CRUD              | Part 2; has `controlledPropertyId`                               |
| #13   | Commands         | ~5 CRUD              | Part 2; has `controlStreamId`, `issuerIds`                       |

Issues #7–#9 will be straightforward — they follow exactly the same pattern as Deployments, with no additional query options beyond the base set. Issues #10–#13 bring more complex query options (temporal filtering, cross-resource references) but the serialization infrastructure already handles all of these parameter types.

After all resource types are covered, Phase 3 will add **response fetching and parsing** — actually calling the URLs and turning JSON responses into typed objects. The F3 (`items` envelope) and F4 (array `validTime`) findings will be addressed there.

Phase 4 will add **real-time streaming** via WebSocket and MQTT.

---

## Summary

| Metric                               | Phase 2.1                  | Phase 2.2 (now)          | Delta       |
| ------------------------------------ | -------------------------- | ------------------------ | ----------- |
| Public methods on CSAPIQueryBuilder  | 12                         | 20                       | +8          |
| Resource types with full API surface | 1 (Systems)                | 2 (Systems, Deployments) | +1          |
| Link relation conventions supported  | 1                          | 3                        | +2          |
| Top-level URL support                | No                         | Yes                      | New         |
| CSAPI unit tests                     | 100                        | 128                      | +28         |
| Total tests (incl. integration)      | 106                        | 134                      | +28         |
| url_builder.ts lines                 | ~420                       | 612                      | +192        |
| url_builder.spec.ts tests            | 43                         | 71                       | +28         |
| Issues closed (cumulative)           | 5 (1–5)                    | 8 (1–6, 34, 35)          | +3          |
| Live server verified                 | Smoke test revealed issues | Fixes confirmed working  | Closed loop |

The builder is now battle-tested against a real server. The link relation discovery and URL construction infrastructure are production-grade — they handle real-world server behavior, not just spec ideals. Each remaining resource type is incremental: new public methods that delegate to the same proven private infrastructure.
