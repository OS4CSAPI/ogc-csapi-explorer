# Library Findings Gap Analysis — GitHub Issues vs. Full Findings

> **Date**: 2026-02-16 (updated 2026-02-17)
> **Context**: After building the CSAPI Explorer demo webapp, we documented 16 library findings and 7 server observations in [`docs/upstream-findings.md`](../upstream-findings.md). Four of those findings were selected as the initial set of GitHub issues for upstream contribution. This document maps all findings to their issue status and provides detailed analysis of each. Three additional findings (F-83–F-85) were identified during subsystem/subdeployment hierarchy testing on 2026-02-17.

---

## Summary: GitHub Issues Created vs. Full Findings

### Covered by the 4 GitHub issues we created:

| Finding | GitHub Issue |
|---|---|
| F-1 (`createDataStream()` generates wrong URL) | [#5 — Fix createDataStream() URL generation + add missing nested create methods](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/5) |
| F-2 (missing nested create methods) | [#5 — Fix createDataStream() URL generation + add missing nested create methods](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/5) |
| F-3 (`extractCSAPIFeature()` undocumented limitations) | [#8 — Add JSDoc documentation for extractCSAPIFeature() limitations](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/8) |
| F-10 (no Content-Type guidance) | [#6 — Add CSAPI_CONTENT_TYPES helper map for content negotiation](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/6) |
| + unit tests for the above | [#7 — Write unit tests for new nested create methods and Content-Type map](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/7) |

### NOT yet covered — 8 additional library findings:

| Finding | Summary | Actionable? |
|---|---|---|
| **F-4** | `Accept: application/json` returns empty from 52North — needs `application/geo+json` | Yes — library could auto-negotiate |
| **F-5** | Pre-existing bug in `ogc-api/endpoint.ts` L74 | Yes — bug fix |
| **F-6** | `EndpointError` XML dependency | **RESOLVED** already — no action needed |
| **F-7** | No generic CRUD method for dynamic-type consumers | Yes — DX improvement |
| **F-8** | `OgcApiCollectionInfo` overly broad for constructor | Yes — type narrowing |
| **F-9** | `extractCSAPIFeature()` union return requires type guards | Yes — DX improvement |
| **F-11** | Resource discovery depends on server link quality | Design note — hard to fix |
| **F-12** | No `Location` header parsing helper | Yes — utility addition |

### Findings from subsystem/subdeployment hierarchy testing (2026-02-17):

| Finding | Summary | Actionable? |
|---|---|---|
| **F-83** | Missing `createSubsystem(parentId)` and `createSubdeployment(parentId)` URL builder methods | Yes — amends [#5](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/5) |
| **F-84** | No nested resource type abstraction for CRUD operations | Yes — new issue needed |
| **F-85** | No resource deletion ordering guidance | Yes — documentation (low priority) |

### Server-side observations (S-1 through S-7):

These are **not library issues** — they're quirks/bugs in the OSH and 52North servers themselves (no REST datastream creation, read-only live streams, missing conformance classes, CORS failures, expired SSL, etc.). Not actionable on the library side.

---

## Detailed Breakdown of Each Finding

---

### F-1. `createDataStream()` Generates Wrong URL

| | |
|---|---|
| **Severity** | High |
| **GitHub Issue** | [#5](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/5) |
| **Status** | Issue created, PR pending |
| **Affected File** | `src/ogc-api/csapi/url_builder.ts` (L1255–L1258) |

#### What's broken

The `createDataStream()` method builds a top-level URL (`/datastreams`) instead of the OGC-required nested URL (`/systems/{systemId}/datastreams`). Per OGC 23-002r1 §7.2, datastreams must be created as sub-resources of a parent system.

#### Evidence

The OSH SensorHub server returns **405 Method Not Allowed** with the message: _"Datastreams can only be created within a System resource"_ when a POST is sent to the top-level `/datastreams` endpoint.

#### Current code

```typescript
createDataStream(): string {
  this.assertResourceAvailable('datastreams');
  return this.buildResourceUrl('datastreams');
  // Produces: /collections/iot/datastreams  ← WRONG
}
```

#### Correct pattern (already exists for observations)

```typescript
createObservation(datastreamId: string): string {
  this.assertResourceAvailable('datastreams');
  return this.buildResourceUrl('datastreams', datastreamId, 'observations');
  // Produces: /collections/iot/datastreams/{id}/observations  ← CORRECT
}
```

#### Demo app workaround

The bridge module in `demo/src/api.ts` uses `getSystemDataStreams(systemId)` as the POST target URL, which generates the correct path but is semantically named as a GET operation.

#### Impact on webapp

None visible — the workaround handles it. The fix benefits future library consumers.

---

### F-2. Missing Nested Create Methods

| | |
|---|---|
| **Severity** | Medium |
| **GitHub Issue** | [#5](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/5) (combined with F-1) |
| **Status** | Issue created, PR pending |
| **Affected File** | `src/ogc-api/csapi/url_builder.ts` |

#### What's missing

The library has nested **listing** methods but no nested **creation** methods for three resource types:

| Listing Method (exists) | Creation Method (missing) | URL Pattern |
|---|---|---|
| `getSystemDataStreams(id)` | `createDataStreamForSystem(id)` | `POST /systems/{id}/datastreams` |
| `getSystemControlStreams(id)` | `createControlStreamForSystem(id)` | `POST /systems/{id}/controlstreams` |
| `getSystemSamplingFeatures(id)` | `createSamplingFeatureForSystem(id)` | `POST /systems/{id}/samplingFeatures` |

#### Why it matters

This is an API design inconsistency. `createObservation(datastreamId)` and `createCommand(controlStreamId)` already follow the correct nested pattern — they accept a parent ID and produce a nested URL. The three missing methods should follow the same convention. Without them, consumers must use the listing URL as a POST target, which is confusing and error-prone.

#### Demo app workaround

The bridge module dispatches to `getSystemDataStreams()` / `getSystemControlStreams()` / `getSystemSamplingFeatures()` and uses those URLs for POST requests.

---

### F-3. `extractCSAPIFeature()` Only Works for GeoJSON Features

| | |
|---|---|
| **Severity** | High |
| **GitHub Issue** | [#8](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/8) |
| **Status** | Issue created, PR pending |
| **Affected File** | `src/ogc-api/csapi/formats/geojson.ts` (L307–L387) |

#### What's undocumented

The function has three major limitations that no JSDoc or documentation mentions:

1. **Only accepts GeoJSON Feature format** — Requires `properties.featureType`, `properties.uid`, `properties.name`, `geometry`, and `links`. This is the GeoJSON representation of Part 1 resources only.

2. **Return type excludes Part 2 resources** — Returns `System | Deployment | Procedure | SamplingFeature`. DataStreams, Observations, Control Streams, and Commands are explicitly not supported. The function name `extractCSAPIFeature` gives no hint that it's Part-1-only.

3. **Fails on SensorML responses** — Some servers (e.g., 52North with `Accept: application/sml+json`) return flat objects without `properties.featureType`. The function throws a generic error: `"Cannot extract CSAPI feature: unrecognized or missing featureType"`.

#### How this was discovered

During integration testing, the demo app attempted to use `extractCSAPIFeature()` on DataStream objects (TypeError — no `properties.featureType`), Observation objects (same), and 52North SML-format system responses (unhelpful error thrown). Each failure required manual debugging to understand the constraint.

#### 52North SML response format (what breaks)

```json
{
  "type": "PhysicalSystem",
  "id": "5400-526",
  "label": "Doppler Current Profiler Sensor",
  "definition": "sosa:Sensor"
}
```

No `properties.featureType` exists. The type information is in `definition` and `type` at the top level, but the function doesn't look there.

#### Demo app workaround

The app parses API responses directly from JSON instead of using `extractCSAPIFeature()`, accessing properties it needs without going through the extraction function.

---

### F-4. Content Negotiation: `application/json` Returns Empty from 52North

| | |
|---|---|
| **Severity** | High |
| **GitHub Issue** | None yet |
| **Status** | Documented but no issue created |
| **Affected Area** | Library HTTP layer (Accept header defaults) |

#### What happens

This is the single most impactful interoperability finding. The 52North server routes requests to different internal providers based on the `Accept` header:

| Accept Header | 52N Items | 52N Envelope | Content-Type Returned |
|---|---|---|---|
| `application/json` | **0** | features (empty FeatureCollection) | application/json |
| `application/sml+json` | **3** | items | application/sml+json |
| `application/geo+json` | **3** | features (populated FeatureCollection) | application/geo+json |
| *(none / default)* | **3** | items | application/sml+json |

On OSH SensorHub, **all** Accept headers return the same 5 items — it ignores the Accept header entirely.

#### Why it's critical

Any client that sends `Accept: application/json` (the standard default for most HTTP libraries including `fetch()`) will see an **empty 52North server**. The library's HTTP layer should negotiate the correct Accept header automatically.

#### The correct default

`application/geo+json` is the only Accept header that:
- Returns data from **both** servers
- Uses the standard GeoJSON envelope (`FeatureCollection` / `features`)
- Is compatible with `extractCSAPIFeature()` and `parseCollectionResponse()`
- Is the OGC-specified response format for Part 1 resources

#### Demo app workaround

The bridge module in `demo/src/api.ts` defaults to `Accept: application/json` but the Vite proxy configuration for 52North is set up with special handling. The library should handle this automatically.

#### Recommendation

The library should use `application/geo+json` as the default Accept header for Part 1 resource requests (systems, deployments, procedures, samplingFeatures).

---

### F-5. Pre-Existing Bug: `ogc-api/endpoint.ts` Line 74

| | |
|---|---|
| **Severity** | Low |
| **GitHub Issue** | None yet |
| **Status** | Documented but no issue created |
| **Affected File** | `src/ogc-api/endpoint.ts` (L74) |

#### What's wrong

The `root` getter in `ogc-api/endpoint.ts` throws `new Error(...)` on line 74, but the corresponding test at `endpoint.spec.ts:1789` expects `new EndpointError(...)`. The production code should use `EndpointError` to match:
1. The test expectation
2. The library's established error hierarchy
3. Consumer code that catches `EndpointError` specifically

#### Context

This is pre-existing — it was not introduced by the CSAPI work. It was discovered during EndpointError isolation testing when we refactored `EndpointError` into its own module.

#### Risk

Low. A consumer who catches `EndpointError` specifically (rather than generic `Error`) would miss this particular error. The fix is literally changing `new Error(` to `new EndpointError(` on one line.

#### Demo app impact

None — the demo app doesn't hit this code path.

---

### F-6. `EndpointError` Transitive XML Dependency — RESOLVED

| | |
|---|---|
| **Severity** | Was High → **Resolved** |
| **GitHub Issue** | None needed |
| **Status** | Fixed in commit `e73cff8` |
| **Files Changed** | 18 files, +44 −28 lines |

#### What was wrong

`CSAPIQueryBuilder` imported `EndpointError` from `shared/errors.ts`, which transitively imported `@rgrove/parse-xml` (an XML parsing library) via `ServiceExceptionError`. This meant **any code importing CSAPIQueryBuilder pulled in an XML parser**, even though CSAPI is a JSON-only API. This caused Vite build failures in browser environments without a Node.js `stream` polyfill.

#### What we did

Extracted `EndpointError` into `src/shared/endpoint-error.ts` (23 lines, zero imports). Updated 14 files across CSAPI, OGC API, and STAC modules to import from the new location. Added a backward-compatible re-export in `errors.ts`.

#### Critical implementation detail

The re-export in `errors.ts` must use two statements:
```typescript
import { EndpointError } from './endpoint-error.js';
export { EndpointError };
```
A direct `export { X } from 'y'` re-export does **NOT** create a local binding — `encodeError()` and `decodeError()` in the same file would get `ReferenceError` at runtime.

#### Verification

317 unit tests pass (19 in `errors.spec` + 298 in `url_builder.spec`). Demo app builds without the `@rgrove/parse-xml` Vite alias workaround. This fix benefits not just CSAPI consumers, but also OGC API Features and STAC consumers.

#### Demo app impact

This fix was essential — without it, the demo app literally could not build. Already committed and working.

---

### F-7. No Generic CRUD Method for Dynamic-Type Consumers

| | |
|---|---|
| **Severity** | Medium |
| **GitHub Issue** | None yet |
| **Status** | Documented but no issue created |
| **Affected File** | `src/ogc-api/csapi/url_builder.ts` |

#### What's missing

The library provides 77+ type-specific methods (`getSystems()`, `getDeployments()`, `createSystem()`, etc.) with excellent TypeScript type safety. However, any consumer working with resource types **dynamically** — UI frameworks, CLI tools, admin panels — needs boilerplate dispatchers:

```typescript
function getListUrl(type: string, options: QueryOptions): string {
  switch (type) {
    case 'systems': return builder.getSystems(options);
    case 'deployments': return builder.getDeployments(options);
    case 'procedures': return builder.getProcedures(options);
    case 'samplingFeatures': return builder.getSamplingFeatures(options);
    case 'datastreams': return builder.getDataStreams(options);
    // ... 4 more cases
  }
}
```

The demo app's bridge module required this pattern for **five operations**: list, detail, create, update, and delete — that's 5 switch statements with 9 cases each (45 lines of pure boilerplate).

#### Recommendation

Add a `getResources(type: CSAPIResourceType, options?: QueryOptions)` convenience method alongside the type-specific methods. It would lose the type-specific query option extensions but cover the common case. The type-specific methods remain for consumers who know the type at compile time.

#### Demo app impact

Would eliminate ~45 lines of switch/case boilerplate from `api.ts`. No visible UI change.

---

### F-8. `OgcApiCollectionInfo` Overly Broad for Constructor

| | |
|---|---|
| **Severity** | Medium |
| **GitHub Issue** | None yet |
| **Status** | Documented but no issue created |
| **Affected File** | `src/ogc-api/csapi/url_builder.ts` (constructor) |

#### What's awkward

`CSAPIQueryBuilder`'s constructor requires an `OgcApiCollectionInfo` object (from `src/ogc-api/model.ts`), which is a large interface with many fields (`id`, `title`, `links`, `extent`, `itemType`, `crs`, etc.). The constructor only actually uses `id`, `title`, and `links`.

Consumers creating a builder outside of `OgcApiEndpoint` — a valid use case for proxy/gateway scenarios, direct URL construction, or testing — must either:
1. Provide a full object with dummy data for all unused fields, or
2. Use `as OgcApiCollectionInfo` type assertion to bypass TypeScript

#### How we hit it

The demo app constructs builders directly (without going through `OgcApiEndpoint`) because it uses a proxy architecture. We had to create synthetic collection objects with placeholder values for fields the builder never reads.

#### Recommendation

Accept `Pick<OgcApiCollectionInfo, 'id' | 'title' | 'links'>` or create a dedicated `CSAPIBuilderOptions` interface that only declares the properties actually used.

#### Demo app impact

Would clean up the synthetic collection creation code slightly. No visible UI change.

---

### F-9. `extractCSAPIFeature()` Union Return Type Causes TypeScript Friction

| | |
|---|---|
| **Severity** | Medium |
| **GitHub Issue** | None yet |
| **Status** | Documented but no issue created |
| **Affected File** | `src/ogc-api/csapi/formats/geojson.ts` |

#### What's frustrating

`extractCSAPIFeature()` returns `System | Deployment | Procedure | SamplingFeature`. The `validTime` property exists on `System`, `Deployment`, and `SamplingFeature` but **NOT** on `Procedure`. TypeScript correctly prevents accessing `typedResource.properties.validTime` because the type could be `Procedure`.

Consumers must use unsafe casts:
```typescript
<!-- In Vue templates -->
<span v-if="(typedResource.properties as any)?.validTime">
  {{ (typedResource.properties as any).validTime.start.toISOString() }}
</span>
```

Similarly, `assetType` only exists on `Procedure`, `systemType` only on `System`, `deployedSystems` only on `Deployment`, etc. Every type-specific property access requires `as any`.

#### Recommendation

Add type-narrowing guard functions:
```typescript
export function isSystem(r: ReturnType<typeof extractCSAPIFeature>): r is System { ... }
export function isDeployment(r: ...): r is Deployment { ... }
export function isProcedure(r: ...): r is Procedure { ... }
export function isSamplingFeature(r: ...): r is SamplingFeature { ... }
```

These let consumers narrow the union safely:
```typescript
if (isSystem(resource)) {
  // TypeScript now knows resource.properties.systemType exists
  console.log(resource.properties.systemType);
}
```

#### Demo app impact

Would eliminate `as any` casts in the ResourceDetail component. Cleaner code, no visible UI change.

---

### F-10. No Content-Type Guidance from the Builder

| | |
|---|---|
| **Severity** | Medium |
| **GitHub Issue** | [#6](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/6) |
| **Status** | Issue created, PR pending |
| **Affected File** | `src/ogc-api/csapi/url_builder.ts` |

#### What's missing

The builder constructs URLs for write operations but provides zero guidance on the required `Content-Type` header. The CSA spec requires different content types for different resource categories:

- **Part 1** resources (systems, deployments, procedures, samplingFeatures): `application/geo+json`
- **Part 2** resources (datastreams, observations, controlStreams, commands): `application/json`

Sending the wrong Content-Type results in 400 or 415 errors from servers.

#### Proposed solution

A `CSAPI_CONTENT_TYPES` constant map (typed as `Record<CSAPIResourceType, string>`) that maps every resource type to its required Content-Type. Plus a `getContentTypeForResource()` helper function.

#### Demo app workaround

The bridge module has its own inline array of Part 1 type names and conditionally sets the Content-Type header.

---

### F-11. Resource Discovery Depends on Server Link Quality

| | |
|---|---|
| **Severity** | Medium |
| **GitHub Issue** | None yet |
| **Status** | Documented but no issue created |
| **Affected Area** | `src/ogc-api/csapi/helpers.ts` (`scanCsapiLinks()`) |

#### What happens

`assertResourceAvailable()` throws `EndpointError` for servers that don't advertise CSAPI link relations, even if the resources actually exist at standard paths. The `scanCsapiLinks()` function returns different results depending on how a server structures its links:

| Server | Root Discovery | Collection Discovery |
|---|---|---|
| OSH SensorHub | 6 resource types | 4 resource types |
| 52North (root) | **0 resource types** | 5 resource types |

52North's root document has links, but not in the CSAPI-specific format that `scanCsapiLinks()` recognizes. The resources are fully accessible at their standard paths.

#### Why it's hard to fix

The OGC Connected Systems API spec does not **require** servers to include CSAPI-specific link relations in the landing page. Servers can advertise resources via:
1. Root-level link relations (OSH does this)
2. Collection-level link relations (52North does this)
3. Conformance class declarations (52North declares none — see S-3)
4. Well-known paths (both servers support this)

The library currently only checks root and collection links. If neither matches, it declares the resource unavailable.

#### Recommendation

1. Implement multi-strategy discovery: root links → collection links → well-known paths fallback
2. Document that `availableResources` reflects *advertised* links, not *actual* capabilities
3. Consider an `assumeAllResourcesAvailable()` option or `tryGetSystems()` methods that return `null` instead of throwing

#### Demo app workaround

The bridge module constructs URLs directly instead of using `assertResourceAvailable()`, bypassing the discovery mechanism entirely.

---

### F-12. No Location Header Parsing Helper

| | |
|---|---|
| **Severity** | Low |
| **GitHub Issue** | None yet |
| **Status** | Documented but no issue created |
| **Affected Area** | No existing file — would be new utility |

#### What's missing

On successful creation (HTTP 201), OGC API servers return an empty response body with a `Location` header containing the URL of the created resource, e.g.:
```
Location: /sensorhub/api/systems/043g
```

The resource ID must be extracted from the last path segment. This is standard OGC API behavior, but the library provides no helper for it.

#### Why it's low priority

The extraction is trivial:
```typescript
const id = locationHeader.split('/').pop();
```

However, a proper helper would:
- Handle trailing slashes
- Handle query parameters
- Extract both the resource type and ID
- Handle edge cases (empty header, malformed URL)

#### Demo app workaround

The bridge module in `api.ts` does its own `Location` header parsing with a one-liner.

#### Recommendation

Consider a `parseLocationHeader(header: string): { resourceType: string; id: string }` utility, but this is low priority since consumers can easily implement it themselves.

---

## Server-Side Observations (Not Library Bugs)

These findings document real server behaviors that affect library consumers but are **not bugs in the library itself**. They inform documentation and defensive coding practices.

---

### S-1. OSH SensorHub: No REST Datastream Creation

OSH rejects `POST /systems/{id}/datastreams` for **all** Content-Types tested (7 types including `application/json`, `application/geo+json`, `application/swe+json`, `application/sml+json`). Response: `400 "Unsupported format"`.

**Why**: Datastreams in OSH are auto-generated by internal sensor drivers (Java SPI plugins), not created via REST API. The OSH architecture ties datastreams to live sensor instances that produce data — you can't create a "detached" datastream via REST.

**Impact on consumers**: Any admin UI or client that expects full CRUD on datastreams will fail on OSH. The library should document that datastream creation support is server-dependent.

---

### S-2. OSH SensorHub: Live Datastreams Are Read-Only

`POST /datastreams/{id}/observations` returns `400 "Resource is not writable"` for existing sensor-driven datastreams. The datastreams are actively receiving data from physical sensors and are marked read-only at the server level.

**Impact on consumers**: Observation creation only works on datastreams explicitly created for that purpose (which OSH doesn't support via REST — see S-1). This creates a chicken-and-egg problem for testing write operations on OSH.

---

### S-3. 52North: Declares Zero CSA Conformance Classes

52North's `/conformance` endpoint only declares `ogcapi-common-1/1.0/conf/core`. It does not declare any Connected Systems API conformance classes despite implementing Part 1 resources (3 systems, 1 deployment, 1 procedure).

**Impact on consumers**: Any library logic that gates CSAPI features on conformance class declarations will incorrectly conclude that 52North doesn't support CSA. The library should **not** rely solely on conformance declarations to determine CSAPI availability.

---

### S-4. 52North: Part 2 Endpoints Return 400/500

DataStreams and Observations endpoints are not implemented on 52North:

| Request | Response |
|---|---|
| `GET /datastreams` with `Accept: application/json` | HTTP 500 Internal Server Error |
| `GET /datastreams` with `Accept: application/sml+json` | HTTP 400: `"expected [] got 'application/sml+json'"` |

**Impact on consumers**: 52North is Part 1 only. Library consumers should handle 400/500 responses from Part 2 endpoints gracefully rather than assuming all CSAPI servers implement the full spec.

---

### S-5. OSH SensorHub: Omits Standard `rel="data"` Link

OSH uses resource-name-based link relations directly on the root document (e.g., links with `rel="systems"`, `rel="datastreams"`) rather than the standard `rel="data"` pointing to `/collections` as an intermediate step.

**Impact on consumers**: The library's `scanCsapiLinks()` handles this correctly (it recognizes plain-name relations), so this is not a problem in practice. But it means servers can legitimately omit the `/collections` intermediary, which the library should continue to support.

---

### S-6. 52North: SSL Certificate Expired

The 52North demo server at `https://csa.demo.52north.org` has an expired SSL certificate. All HTTPS connections fail unless certificate validation is disabled:
- Node.js: `NODE_TLS_REJECT_UNAUTHORIZED=0`
- Vite proxy: `secure: false`
- Browsers: refuse direct connection entirely

**Impact on consumers**: This is a server operations issue, not a library concern. The demo app routes all 52North traffic through a Vite proxy with `secure: false` to work around it.

---

### S-7. 52North: Write Preflight CORS Fails

52North's server is missing `Access-Control-Allow-Methods` and `Access-Control-Allow-Headers` in OPTIONS preflight responses. Browsers block all POST/PUT/DELETE requests due to CORS policy violations.

**Impact on consumers**: Any browser-based client must proxy write requests to 52North. The demo app handles this through its Vite proxy, but a production deployment would need a backend proxy or the server would need CORS configuration updates.

---

## Findings from Subsystem/Subdeployment Hierarchy Testing (2026-02-17)

> **Context**: During implementation of hierarchical navigation (commit `8ee5ecb`) and the expansion of the automated CRUD smoke test to cover subsystem and subdeployment resources (commit `bdeae49`), three additional library findings were identified. These are numbered in the global finding sequence (F-83 through F-85) to maintain continuity with findings documented in `docs/implementation/`.

---

### F-83. Missing `createSubsystem(parentId)` and `createSubdeployment(parentId)` URL Builder Methods

| | |
|---|---|
| **Severity** | Medium |
| **GitHub Issue** | Amends [#5](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/5) |
| **Status** | Workaround applied in demo app |
| **Affected File** | `src/ogc-api/csapi/url_builder.ts` |

#### What's missing

The `CSAPIQueryBuilder` provides listing methods for nested resources:
- `getSystemSubsystems(id)` → `GET /systems/{id}/subsystems`
- `getDeploymentSubdeployments(id)` → `GET /deployments/{id}/subdeployments`

But there are **no corresponding creation methods**:
- ❌ No `createSubsystem(parentId)` → `POST /systems/{id}/subsystems`
- ❌ No `createSubdeployment(parentId)` → `POST /deployments/{id}/subdeployments`

This is the same gap identified in F-2 (missing nested create methods for datastreams, observations, etc.), extended to the hierarchy-forming resource relationships.

#### Demo app workaround

The demo's `csapi-bridge.ts` repurposes the listing URL as a creation URL by stripping query parameters:

```typescript
case 'subsystems':
  return parentId ? b.getSystemSubsystems(parentId).split('?')[0] : '/systems';
case 'subdeployments':
  return parentId ? b.getDeploymentSubdeployments(parentId).split('?')[0] : '/deployments';
```

This works but is fragile — it depends on the listing URL having the same path as the creation endpoint, which is true today but not guaranteed.

#### Recommended fix

Add explicit creation methods to `CSAPIQueryBuilder`:

```typescript
createSubsystem(systemId: string): string {
  this.assertResourceAvailable('systems');
  return this.buildResourceUrl('systems', systemId, 'subsystems');
}

createSubdeployment(deploymentId: string): string {
  this.assertResourceAvailable('deployments');
  return this.buildResourceUrl('deployments', deploymentId, 'subdeployments');
}
```

#### Relationship to existing issues

Issue [#5](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/5) covers `createDataStream()`, `createObservation()`, `createControlStream()`, and `createCommand()`. The subsystem/subdeployment creation methods should be added to the same issue scope or filed as a follow-up.

---

### F-84. No Nested Resource Type Abstraction for CRUD Operations

| | |
|---|---|
| **Severity** | Medium |
| **GitHub Issue** | Not yet — new issue needed |
| **Status** | Workaround applied in demo app |
| **Affected Area** | Library API design / consumer DX |

#### The problem

When performing CRUD operations on subsystems and subdeployments, consumers face a type-resolution challenge: these are the same underlying API resource types (`systems` and `deployments`) but accessed through different URL paths and requiring parent context. The demo app's smoke test needed **three lookup tables** to bridge this gap:

```typescript
const NESTED_ACTUAL_TYPE: Record<string, string> = {
  subsystems: 'systems',
  subdeployments: 'deployments',
};

const NESTED_PARENT_TYPE: Record<string, string> = {
  subsystems: 'systems',
  subdeployments: 'deployments',
};

const NESTED_LABELS: Record<string, string> = {
  subsystems: 'Subsystem',
  subdeployments: 'Subdeployment',
};
```

Every CRUD operation must resolve the actual type before calling any URL builder or content-type helper:

```typescript
const actualType = NESTED_ACTUAL_TYPE[step.resourceType] || step.resourceType;
const contentType = getContentType(actualType); // not getContentType('subsystems')
const detailUrl = getDetailUrl(actualType, id);  // not getDetailUrl('subsystems', id)
```

#### Why it matters

Any consumer that needs subsystem/subdeployment CRUD (admin UIs, data management tools, migration scripts) would independently reinvent this same boilerplate. The library already has all the knowledge needed to resolve these relationships.

#### Recommended enhancement

Add a nested resource type resolver to the library:

```typescript
interface NestedResourceInfo {
  actualType: string;        // 'systems' | 'deployments'
  parentType: string;        // 'systems' | 'deployments'
  relation: string;          // 'subsystems' | 'subdeployments'
  contentType: string;       // 'application/geo+json'
  label: string;             // 'Subsystem' | 'Subdeployment'
}

function resolveNestedType(virtualType: string): NestedResourceInfo | null;
```

This complements F-7 (generic CRUD method) — a generic dispatch method that understood nested resource types would eliminate most of the consumer-side boilerplate.

---

### F-85. No Resource Deletion Ordering Guidance

| | |
|---|---|
| **Severity** | Low |
| **GitHub Issue** | Not yet — optional, documentation-only |
| **Status** | Documented in smoke test implementation |
| **Affected Area** | Library documentation |

#### The problem

The OGC Connected Systems API has implicit resource dependency ordering that affects deletion. The demo app's smoke test must delete resources in a specific order to avoid server-side referential integrity errors:

```typescript
const deleteOrder = [
  'commands',          // depends on controlStreams
  'controlStreams',    // depends on systems
  'observations',      // depends on datastreams
  'datastreams',       // depends on systems
  'subsystems',        // depends on parent systems
  'subdeployments',    // depends on parent deployments
  'samplingFeatures',  // depends on systems
  'deployments',       // may reference systems
  'procedures',        // may be referenced by systems
  'systems',           // root resource — delete last
];
```

Deleting in the wrong order (e.g., parent system before subsystem) results in 409 Conflict or cascading failures depending on server implementation.

#### Why it matters

This is standard REST resource lifecycle knowledge, but it's not documented anywhere in the library or the OGC spec examples. Consumers building cleanup, migration, or admin tooling must discover this ordering empirically.

#### Recommended enhancement

Add a `CSAPI_DELETE_ORDER` constant or a `getDependencySafeDeleteOrder()` helper to the library, paired with JSDoc explaining the dependency graph. This could live alongside the `CSAPI_CONTENT_TYPES` map proposed in Issue [#6](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/6).

---

## Actionability Summary

| Finding | Has GitHub Issue? | Actionable? | Effort | Priority |
|---|---|---|---|---|
| **F-1** | [#5](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/5) | Yes — bug fix | Low | **1** (High) |
| **F-2** | [#5](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/5) | Yes — API gap | Low | **1** (High) |
| **F-3** | [#8](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/8) | Yes — documentation | Low | **4** (Medium) |
| **F-4** | Not yet | Yes — Accept header default | Low | **1** (High) |
| **F-5** | Not yet | Yes — one-line bug fix | Low | **6** (Low) |
| **F-6** | N/A | **Already resolved** | Done | N/A |
| **F-7** | Not yet | Yes — DX improvement | Medium | **5** (Medium) |
| **F-8** | Not yet | Yes — type narrowing | Low | **5** (Medium) |
| **F-9** | Not yet | Yes — type guards | Low | **5** (Medium) |
| **F-10** | [#6](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/6) | Yes — helper constant | Low | **3** (Medium) |
| **F-11** | Not yet | Partially — design challenge | Medium | **5** (Medium) |
| **F-12** | Not yet | Yes — utility function | Low | **6** (Low) |
| **F-83** | Amends [#5](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/5) | Yes — API gap | Low | **2** (High) |
| **F-84** | Not yet | Yes — DX improvement | Medium | **4** (Medium) |
| **F-85** | Not yet | Yes — documentation | Low | **6** (Low) |
| **S-1–S-9** | N/A | No — server-side issues | N/A | N/A |
| **S-15** | N/A | No — server-side issue | N/A | N/A |
