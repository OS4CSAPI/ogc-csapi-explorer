# Temporal Filtering & Pagination Metadata in the CSAPI Explorer

## Executive Summary

This document captures findings from implementing and testing temporal filtering and pagination metadata in the CSAPI Explorer demo webapp. It covers the OGC standard's design, OSH SensorHub's actual server behavior, two bugs discovered in the demo app, the workaround for missing `numberMatched` metadata, and practical guidance for demonstrating these features.

---

## 1. OGC Standard: Temporal Query Parameters

The OGC API — Connected Systems specification defines **different temporal query parameters** depending on the resource type and which Part of the spec governs it.

### Part 1 Resources (GeoJSON Features)

| Resource Type | Temporal Parameter | Spec Reference |
|---|---|---|
| Systems | `datetime` | [OGC 23-001 §7.8](https://docs.ogc.org/is/23-001/23-001.html) |
| Deployments | `datetime` | [OGC 23-001 §7.9](https://docs.ogc.org/is/23-001/23-001.html) |
| Procedures | `datetime` | [OGC 23-001 §7.10](https://docs.ogc.org/is/23-001/23-001.html) |
| Sampling Features | `datetime` | [OGC 23-001 §7.11](https://docs.ogc.org/is/23-001/23-001.html) |

The `datetime` parameter is inherited from OGC API — Features (Part 1) and filters resources by their `validTime` interval. The format is ISO 8601 instant or interval: `2025-01-01T00:00:00Z/..`, `../2026-01-01T00:00:00Z`, or `2025-01-01T00:00:00Z/2026-01-01T00:00:00Z`.

### Part 2 Resources (JSON Envelopes)

| Resource Type | Primary Temporal Parameter | Additional Temporal Parameters | Spec Reference |
|---|---|---|---|
| Datastreams | `phenomenonTime` | `resultTime` (supports `'latest'`) | [OGC 23-002 §8.3](https://docs.ogc.org/is/23-002/23-002.html) |
| Observations | `phenomenonTime` | `resultTime` (supports `'latest'`) | [OGC 23-002 §8.4](https://docs.ogc.org/is/23-002/23-002.html) |
| Control Streams | — | — | [OGC 23-002 §8.5](https://docs.ogc.org/is/23-002/23-002.html) |
| Commands | `issueTime` | `executionTime` | [OGC 23-002 §8.6](https://docs.ogc.org/is/23-002/23-002.html) |

The key distinction: Part 2 resources use **domain-specific temporal semantics** (`phenomenonTime`, `resultTime`, `issueTime`, `executionTime`) rather than the generic `datetime`. This is because an observation's temporal identity is when the phenomenon occurred or when the result was produced, not a generic validity window.

### Client Library Support

The ogc-client library's `CSAPIQueryBuilder` models this correctly through typed query option interfaces:

```typescript
// Part 1 — all share the base QueryOptions
interface QueryOptions {
  datetime?: DateTimeParameter;  // ISO 8601 instant or interval
  limit?: number;
  offset?: number;
  // ...
}

// Part 2 — typed extensions with domain-specific temporal params
interface ObservationQueryOptions extends QueryOptions {
  phenomenonTime?: DateTimeParameter;
  resultTime?: CsapiDateTimeParameter;  // includes 'latest' keyword
}

interface CommandQueryOptions extends QueryOptions {
  issueTime?: DateTimeParameter;
  executionTime?: DateTimeParameter;
}

interface DatastreamQueryOptions extends QueryOptions {
  phenomenonTime?: DateTimeParameter;
  resultTime?: CsapiDateTimeParameter;
}
```

The `DateTimeParameter` type accepts `Date` objects or `{start: Date}`, `{end: Date}`, `{start: Date, end: Date}` interval objects. The library's `formatDateTimeParameter()` function serializes these into the ISO 8601 strings required by the OGC API query parameter format.

---

## 2. OSH SensorHub Server Behavior

### Finding: OSH Ignores `datetime` on All Resource Types

Testing against the OSH SensorHub server (`http://45.55.99.236:8080/sensorhub/api`) revealed that **OSH ignores the `datetime` parameter entirely** — on all resource types, every datetime range returns the same result count:

```
GET /systems?limit=1000                              → 32 items
GET /systems?limit=1000&datetime=2026-02-01T00:00:00Z/.. → 32 items
GET /systems?limit=1000&datetime=../2025-01-01T00:00:00Z → 32 items

GET /deployments?limit=1000                              → 15 items
GET /deployments?limit=1000&datetime=2026-02-01T00:00:00Z/.. → 15 items

GET /datastreams?limit=1000                              → 219 items
GET /datastreams?limit=1000&datetime=2026-02-01T00:00:00Z/.. → 219 items
```

This was previously identified as **Finding F64** (Phase 3.5 smoke test) — OSH ignores all Accept headers and several query parameters on Part 1 resources.

### Finding: OSH Honors `phenomenonTime` on Observations

In contrast, the Part 2 temporal parameter `phenomenonTime` **works correctly** on observations:

```
GET /observations?limit=1000                                      → 1000 items
GET /observations?limit=1000&phenomenonTime=2026-02-01T00:00:00Z/.. → 1000 items
GET /observations?limit=1000&phenomenonTime=../2025-01-01T00:00:00Z → 0 items
```

This confirms OSH implements Part 2's temporal filtering but not Part 1's `datetime` filtering.

### Standards Compliance Assessment

The OGC CSAPI Part 1 spec requires servers conforming to the `datetime` conformance class to honor the `datetime` query parameter. OSH's behavior of silently ignoring it (returning a `200 OK` with unfiltered results rather than a `400 Bad Request` or a filtered result set) is a conformance gap. However, it is a common pattern in early OGC API implementations — many servers accept but ignore unsupported parameters rather than rejecting them.

---

## 3. Demo App Bug: Type Mismatch in Temporal Filter

### The Problem

The Explorer page's `ResourceList.vue` component was building the `datetime` value as a **pre-formatted ISO 8601 string** (e.g., `"2025-01-01T00:00:00.000Z/.."`) and passing it to the library via `as any`:

```typescript
// BEFORE (broken)
const datetime = computed(() => {
  const fmt = (d: Date) => d.toISOString()
  if (dtStart.value && dtEnd.value) return `${fmt(dtStart.value)}/${fmt(dtEnd.value)}`
  if (dtStart.value) return `${fmt(dtStart.value)}/..`
  // ...
})

// In fetchResources:
if (datetime.value) options.datetime = datetime.value as any  // ← string, not DateTimeParameter
```

The library's `formatDateTimeParameter()` expects `Date` objects or `{start, end}` objects. When it received a string, the `'start' in "some-string"` check threw a `TypeError`. This error was **silently caught** by `getListUrl()`'s catch block (designed to handle `EndpointError` for unavailable resource types), which fell back to a bare URL path like `/systems` — **dropping ALL query parameters** including `limit`.

### Symptoms

- Setting any temporal filter caused the Explorer to display **all** resources (e.g., 32 systems) regardless of the `limit` setting (e.g., 10 per page)
- The keyword search (`q`) filter worked correctly because it's a plain string, not a typed temporal parameter
- No error was visible to the user — the catch block swallowed the TypeError silently

### The Fix (commit `66e2294`)

Pass proper `DateTimeParameter` objects directly from the PrimeVue `DatePicker` refs:

```typescript
// AFTER (fixed)
const datetimeParam = computed((): DateTimeParameter | null => {
  if (dtStart.value && dtEnd.value) return { start: dtStart.value, end: dtEnd.value }
  if (dtStart.value) return { start: dtStart.value }
  if (dtEnd.value) return { end: dtEnd.value }
  return null
})

// In fetchResources:
if (datetimeParam.value) options.datetime = datetimeParam.value  // ← proper typed object
```

### Lesson Learned

The `as any` cast masked a type-safety violation at the boundary between the demo app and the library. The library's TypeScript types were correct — `DateTimeParameter` is `Date | {start: Date} | {end: Date} | {start: Date, end: Date}` — but the demo bypassed them. This is a reminder that type assertions at API boundaries defeat the purpose of typed interfaces.

---

## 4. Demo App Enhancement: Correct Temporal Parameter Mapping

### The Problem

Even after fixing the type mismatch, the temporal filter still had no visible effect because the demo sent `datetime` for all resource types, and OSH ignores `datetime`.

### The Fix (commit `dd9dbfc`)

Added an `applyTemporalFilter()` helper that maps the date picker value to the correct query parameter based on resource type:

```typescript
function applyTemporalFilter(options: Record<string, any>, resourceType: string, dt: DateTimeParameter) {
  switch (resourceType) {
    case 'observations':
    case 'datastreams':
      options.phenomenonTime = dt
      break
    case 'commands':
      options.issueTime = dt
      break
    default:
      options.datetime = dt
      break
  }
}
```

The UI label next to the date preview now dynamically shows which query parameter is being sent (e.g., `phenomenonTime` when viewing observations, `datetime` when viewing systems).

### Design Rationale

This mapping lives in the demo app (not the library) because the library already provides the correct typed interfaces — `ObservationQueryOptions.phenomenonTime`, `CommandQueryOptions.issueTime`, etc. The demo app's job is to choose the right property based on which resource type the user is exploring. A more complex UI could offer separate controls for each temporal dimension (e.g., both `phenomenonTime` and `resultTime` for observations), but the single date picker with automatic mapping is sufficient for demonstration purposes.

---

## 5. Pagination Metadata: The `numberMatched` Gap

### What the Standard Defines

The OGC API — Features specification (inherited by CSAPI) defines two optional pagination metadata fields in collection responses:

| Field | Purpose | Required? |
|---|---|---|
| `numberMatched` | Total number of items matching the query (across all pages) | Optional |
| `numberReturned` | Number of items in this page | Optional |

These appear at the top level of the response envelope:

```json
{
  "type": "FeatureCollection",
  "numberMatched": 219,
  "numberReturned": 10,
  "features": [...],
  "links": [...]
}
```

Or in the items envelope:

```json
{
  "numberMatched": 219,
  "numberReturned": 10,
  "items": [...],
  "links": [...]
}
```

### Client Library Support

The library's `parseCollectionResponse()` function extracts both fields from either envelope format:

```typescript
interface CollectionResponse<T> {
  items: T[];
  links: ResourceLink[];
  numberMatched?: number;   // extracted if present
  numberReturned?: number;  // extracted if present
  timeStamp?: string;
}
```

Both fields are typed as optional (`number | undefined`) because the standard makes them optional and servers vary in their support.

### OSH SensorHub Behavior

OSH provides **neither** `numberMatched` **nor** `numberReturned` in its responses. A typical OSH response looks like:

```json
{
  "items": [
    { "type": "Feature", "id": "03bc5ofvvstg", ... },
    ...
  ],
  "links": [
    { "rel": "next", "href": "http://server/systems?limit=10&offset=10" }
  ]
}
```

No `numberMatched`, no `numberReturned`. OSH also does not provide a total count via HTTP headers (no `X-Total-Count`, `Content-Range`, or similar).

### Impact on the Demo

Without `numberMatched`, the Explorer page could only show "Showing 10 results" with no indication of how many total resources exist. This makes it impossible to demonstrate the effect of filters — the user can't see whether a temporal filter narrowed 219 datastreams down to 50, because the total is never displayed.

### Workaround: Parallel Count Request (commit `c99822b`)

The demo now fires a **parallel count request** alongside each paginated fetch. This request uses the same filters (keyword search, temporal) but with `limit=1000` (instead of the user's page size), then counts the items array length:

```typescript
async function fetchTotalCount(): Promise<number | null> {
  const countOptions: QueryOptions = { limit: 1000 }
  if (q.value) countOptions.q = q.value
  if (datetimeParam.value) applyTemporalFilter(countOptions, props.resourceType, datetimeParam.value)
  const countPath = getListUrl(props.resourceType, countOptions)
  const countRes = await apiFetch(countPath, { headers: { 'Accept': acceptType } })
  const parsed = parseCollectionResponse(countRes.data)
  return parsed.items.length
}
```

The count request runs concurrently with the paginated request using `Promise` parallelism, so it doesn't add latency to the page load:

```typescript
const totalCountPromise = fetchTotalCount()  // fire immediately
const res = await apiFetch(path, ...)         // paginated request
// ... process paginated results ...
const counted = await totalCountPromise       // resolve count
```

If the server provides `numberMatched` in the paginated response, the parallel count is ignored (server metadata is preferred). The count request is only used as a fallback.

### Display

The results info bar now shows:

```
Showing 10 results of 219 total (offset: 0)
```

The "of **219** total" portion is bold to draw attention, and updates reactively when filters change. For example, applying a temporal filter to observations might show:

```
Showing 10 results of 142 total (offset: 0)
```

### Trade-offs

| Aspect | Assessment |
|---|---|
| **Accuracy** | Limited to 1000 items. If a resource type has more than 1000 matching items, the total will show 1000 (the cap). This is sufficient for the OSH demo server. |
| **Performance** | The count request fetches up to 1000 full resource representations just to count them. A production app might use a HEAD request or a dedicated count endpoint if the server supported one. For the demo's data volume, this is acceptable. |
| **Network** | Doubles the number of HTTP requests. Acceptable for a demo app; a production app should prefer server-provided `numberMatched`. |
| **Correctness** | If the server modifies data between the paginated and count requests, the total could be briefly inconsistent. This is inherent to any non-transactional approach. |

### Initial Bug: Default Server Limit

The count request was initially implemented **without** an explicit `limit`, relying on the server to return all results. However, OSH applies a default server-side limit of approximately 100 items when no `limit` parameter is provided. This meant the total count was silently capped at 100, producing incorrect totals for resource types with more than 100 items (e.g., datastreams with 219, sampling features with 66+).

The fix (commit `dd9dbfc`) set an explicit `limit=1000` on the count request.

---

## 6. Demonstrating Temporal Filtering

### Resources That Respond to Temporal Filters on OSH

| Resource Type | Filter | Effect on OSH |
|---|---|---|
| Observations | `phenomenonTime` | **Works** — filters by observation time |
| Datastreams | `phenomenonTime` | Test — may filter by datastream's active period |
| Commands | `issueTime` | Test — may filter by command issue time |
| Systems | `datetime` | **No effect** — OSH ignores |
| Deployments | `datetime` | **No effect** — OSH ignores |
| Sampling Features | `datetime` | **No effect** — OSH ignores |

### Recommended Demo Script

1. **Connect to OSH SensorHub** (requires basic auth: `admin`/`admin`)
2. Navigate to **Explorer** → select **Observations**
3. Set **Limit** to 10
4. Click **Fetch** — observe "Showing 10 results of **1000** total" (capped at our count limit)
5. Set **Start date/time** to `2026-02-01 00:00` — the label changes to `phenomenonTime`
6. Click **Fetch** — the total should decrease, demonstrating server-side temporal filtering
7. Set **End date/time** to `2025-01-01 00:00` (with no start) — total should drop dramatically or to 0
8. **Toggle to Cursor mode** and repeat — demonstrates HATEOAS pagination combined with temporal filtering

### Demonstrating the Keyword Search Contrast

For a more dramatic comparison, use **Systems** (which has 32 items):

1. Select **Systems**, Limit = 10 → "Showing 10 results of **32** total"
2. Enter `"drone"` in the **Search (q)** field → total changes (keyword filtering works on OSH for systems)
3. Set a **Start date/time** → total stays the same (OSH ignores `datetime` on systems)
4. Switch to **Observations** → temporal filter now has visible effect

This contrast effectively demonstrates which parts of the OGC API specification the server implements and how the client library and demo app handle both cases.

---

## 7. Summary of Commits

| Commit | Description |
|---|---|
| `66e2294` | Fix: pass `DateTimeParameter` objects to builder instead of pre-formatted strings |
| `c99822b` | Feat: show total matching count on Explorer page via parallel count request |
| `dd9dbfc` | Fix: map temporal filter to correct query param per resource type, bump count limit to 1000 |

---

## 8. Implications for the Client Library

### What the Library Does Well

- **Typed temporal parameters**: The `DateTimeParameter` type and `formatDateTimeParameter()` function correctly enforce the structured Date/interval objects, catching misuse at compile time (when `as any` is not used).
- **Resource-specific query options**: `ObservationQueryOptions.phenomenonTime`, `CommandQueryOptions.issueTime`, etc., model the spec's per-resource temporal semantics accurately.
- **Response normalization**: `parseCollectionResponse()` handles both `FeatureCollection` and `items` envelopes, extracting `numberMatched`/`numberReturned` when present and gracefully returning `undefined` when absent.

### What App Developers Need to Know

1. **Don't use `as any` at the library boundary** — the typed interfaces exist to prevent exactly the kind of bug found here.
2. **Choose the right temporal parameter per resource type** — `datetime` is for Part 1 features, `phenomenonTime`/`resultTime` for observations and datastreams, `issueTime`/`executionTime` for commands.
3. **Don't assume `numberMatched` will be present** — many servers omit it. Plan a fallback strategy (parallel count, estimating from pagination links, or simply not showing totals).
4. **Don't assume the server's default limit** — if you need all results, always set an explicit high `limit`. OSH defaults to ~100 when no limit is specified.
5. **Server-provided HATEOAS links are the safest pagination mechanism** — they work regardless of whether the server uses offset-based or token-based cursor pagination internally.
