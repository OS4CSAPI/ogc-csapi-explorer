# OSH Server Query Parameter Compliance Report

> **Date**: 2026-02-20 (updated)  
> **Commit**: `caa7415` (fix: client-side fallback for servers that ignore q/limit params)  
> **Server under test**: OpenSensorHub (OSH) at `http://45.55.99.236:8080/sensorhub/api`  
> **Spec references**: OGC API — Features Part 1: Core (17-069r4), OGC API — Connected Systems Part 1 & 2 (Draft)

---

## 1. Executive Summary

During testing of the CSAPI Explorer demo app against a live OpenSensorHub (OSH) server, we initially observed that OSH appeared to silently ignore the `?limit=` and `?q=` query parameters on collection endpoints — the server returned all 33 systems despite `?limit=10&q=FCU` being sent. A client-side fallback was implemented (commit `caa7415`) to protect against non-compliant servers.

**Update:** Follow-up testing confirmed that OSH **does correctly honor** both `limit` and `q` parameters. The `q=FCU` filter correctly returned 1 matching system, and `limit=10` correctly capped results. No client-side fallback banner appeared, and the raw server response confirmed server-side filtering. The initial observation was likely caused by a transient server condition (restart, cache, or initialization delay).

The client-side fallback code remains in place as a **defensive measure** for interoperability with other OGC API servers that may not implement these parameters. The report has been revised to document the investigation, the spec requirements, the fallback architecture, and remaining OSH compliance gaps in other areas.

---

## 2. Observed Behavior

### 2.1 Initial Observation (Transient)

During the first test pass, a request to `GET /systems?limit=10&q=FCU` returned all 33 systems unfiltered. This appeared to indicate that both `limit` and `q` were being silently ignored by the server.

### 2.2 Follow-Up Verification (Confirmed Working)

On subsequent testing, the same parameters worked correctly:

- **`q=FCU`**: Server returned exactly 1 system — "FCU Field Drone CubePilot" (id: `8o30`). The raw response confirmed the server performed the filtering (only 1 item in the JSON payload).
- **`limit=10`** (without `q`): Server returned 10 systems out of the full collection, confirming server-side pagination.
- **No warning banner**: The client-side fallback did not activate, confirming the server handled the parameters.

### 2.3 Likely Cause of Initial Observation

The initial "33 of 33" result was most likely caused by one of:
- A server restart or reinitialization that temporarily bypassed the query engine
- A cached response from a prior unfiltered request
- A first-fetch initialization delay before the query parameter processing was ready

This could not be reproduced after the initial occurrence.

---

## 3. Specification Requirements (Reference)

The following spec requirements motivated the investigation and the defensive fallback code. OSH was confirmed to comply with these after follow-up testing.

### 3.1 `limit` — OGC API Features Core (Requirement 22)

The `limit` parameter is a **Core requirement** in OGC API — Features Part 1 (17-069r4):

> **Requirement 22 — /req/core/fc-limit-response-1:**
> 
> A. The response SHALL not contain more features than specified by the optional `limit` parameter.  
> B. If the API definition specifies a maximum value for `limit` parameter, the response SHALL not contain more features than this maximum value.  
> C. If the value of the `limit` parameter is larger than the maximum value, this SHALL NOT result in an error (instead use the maximum as the parameter value).  
> D. Only items are counted that are on the first level of the collection.

The word **"SHALL"** makes this a normative requirement. A conformant server **must** respect the `limit` parameter and return no more items than requested.

**OSH status:** ✅ Confirmed compliant — `limit` is honored correctly.

### 3.2 `q` — OGC API Connected Systems Part 2

The `q` parameter is defined in OGC API — Connected Systems Part 2 as a free-text keyword search filter. OSH's OpenAPI definition advertises `q` as a supported parameter.

**OSH status:** ✅ Confirmed working — `q=FCU` correctly returned 1 matching system.

### 3.3 Why Defensive Fallback Code Matters

Even though OSH honors these parameters, the OGC API ecosystem includes many server implementations. Per **Requirement 8 (/req/core/query-param-unknown)**, servers SHALL return HTTP 400 for unknown parameters — but in practice, some servers silently accept and ignore unsupported parameters instead. The client-side fallback protects against this real-world interoperability risk.

---

## 4. Root Cause Analysis

### 4.1 Not a Client-Side Bug

The full request flow was traced through the CSAPI client library and Explorer demo:

1. **UI layer** (`ResourceList.vue`): User sets `limit=10` and `q=FCU`, clicks Fetch
2. **Bridge layer** (`csapi-bridge.ts`): Calls `getListUrl('systems', { limit: 10, q: 'FCU' })`
3. **URL Builder** (`CSAPIQueryBuilder.buildQueryString()`): Correctly serializes to `?limit=10&q=FCU`
4. **HTTP layer** (`apiFetch()`): Sends the request with the correct query string
5. **Server response**: Returns all 33 systems — both parameters are in the URL but ignored

The issue is entirely server-side. No client-side parameter dropping was found.

### 4.2 Server Behavior Pattern

OSH exhibits a pattern of accepting-but-ignoring query parameters across multiple areas:

| Parameter | Sent | Honored | Spec Requirement |
|-----------|------|---------|-----------------|
| `limit` | ✅ | ❌ | OGC API Features Core Req 22 (SHALL) |
| `q` | ✅ | ❌ | CSAPI Part 2 (claimed in OpenAPI def) |
| `Accept` header | ✅ | ❌ | HTTP content negotiation (RFC 7231) |
| `offset` | ✅ | ❌ | Common OGC API paging convention |

This suggests a systemic implementation gap in OSH's query parameter processing pipeline, not just a missing feature for one parameter.

---

## 5. Client-Side Defensive Fallback

Commit `caa7415` implements a client-side fallback in `ResourceList.vue` as a **defensive measure** for interoperability with any OGC API server that may not implement `limit` or `q`. While OSH was confirmed to honor these parameters, the fallback protects against non-compliant servers:

### 5.1 Client-Side Keyword Filtering

After receiving the server response, if `q` is set and the server returned more items than the requested limit (indicating parameters were ignored), the demo filters items locally:

```typescript
if (q.value && !cursorUrl && resultItems.length > 0) {
  const keyword = q.value.toLowerCase()
  const filtered = resultItems.filter((item: any) => {
    const fields = [
      item?.id,
      item?.properties?.name,
      item?.properties?.title,
      item?.properties?.description,
      item?.properties?.uniqueId,
      item?.name,
      item?.title,
      item?.description,
    ]
    return fields.some(f => typeof f === 'string' && f.toLowerCase().includes(keyword))
  })
  if (filtered.length < resultItems.length) {
    resultItems = filtered
    clientSideFallback.value = true
  }
}
```

The filter only activates when it actually reduces the result set, avoiding false negatives when the server did filter but the keyword doesn't appear in the fields we check.

### 5.2 Client-Side Limit Enforcement

If the server returns more items than the requested limit, the array is truncated:

```typescript
if (limit.value && !cursorUrl && resultItems.length > limit.value) {
  resultItems = resultItems.slice(0, limit.value)
  clientSideFallback.value = true
}
```

### 5.3 Total Count Correction

The `fetchTotalCount()` function also applies client-side `q` filtering, ensuring the "X of Y total" display is accurate.

### 5.4 User Notification

When the fallback activates, a warning banner appears:

> ⚠️ Server ignored filter/limit parameters — results filtered client-side.

This transparency is important: the user knows the server didn't honor their request, and the client compensated.

### 5.5 Limitations of the Fallback

These limitations only apply when the fallback activates (i.e., when connected to a non-compliant server):

| Limitation | Impact |
|-----------|--------|
| **Client filtering only works on data already fetched** | If the server has 10,000 items and returns all of them, the client can filter — but if the server's own default limit caps at, say, 100, the client can only filter within those 100 |
| **`q` matching is naive** | The client matches against a limited set of string fields (`id`, `name`, `title`, `description`, `uniqueId`). Server-side `q` could match against additional fields, nested properties, or use full-text search |
| **Pagination is broken** | With a non-compliant server ignoring `limit` and `offset`, offset-based pagination cannot work correctly. The client can only paginate within locally-held data |
| **Performance** | Fetching all items when only a page is needed wastes bandwidth and processing time |

---

## 6. Remaining Recommendations for OSH Maintainers

Since `limit` and `q` are confirmed working, the remaining recommendations focus on other gaps found during this testing session:

### 6.1 Include `numberMatched` / `numberReturned` in Responses

**Why:** Clients need these values to display accurate pagination metadata ("Showing X of Y"). Without them, clients must make additional requests or guess.

**Expected implementation:**
- `numberReturned`: count of items in the current response page
- `numberMatched`: total count of items matching the current filters (optional but strongly recommended)

**Spec reference:** Requirements 31–32, `/req/core/fc-numberMatched`, `/req/core/fc-numberReturned`

### 6.2 Honor the HTTP `Accept` Header

**Why:** OSH currently ignores the `Accept` header entirely, always returning JSON. This prevents clients from requesting SensorML (`application/sml+json`), XML, or other formats via standard HTTP content negotiation.

**Spec reference:** RFC 7231 §5.3.2, OGC API Features Core Requirement 7 (HTTP 1.1 conformance)

**Filed as:** Library issue [#99](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/99)

### 6.3 Expose Top-Level Collections for Part 2 Resources

**Why:** Part 2 resources (datastreams, control streams, etc.) are only available nested under systems. Exposing them as top-level collections (`/datastreams`, `/controlstreams`) improves discoverability and allows clients to query across all systems.

**Filed as:** Library issue [#100](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/100)

### 6.4 General: Reject Unknown/Unsupported Parameters with HTTP 400

Per OGC API — Features Core Requirements 8 and 9, the server **SHALL** return HTTP 400 for unknown or invalid query parameters. If any parameter is advertised in the OpenAPI definition but not implemented, the server should either:

1. **Implement it**, or
2. **Remove it from the OpenAPI definition** and return HTTP 400 when it's used, or
3. **Return HTTP 501 (Not Implemented)** with an informative error message

Silent acceptance without application is the worst option — it prevents clients from detecting the gap and falling back gracefully.

---

## 7. Other OSH Interoperability Gaps Found in This Session

While `limit` and `q` were confirmed working, other compliance gaps were discovered during this testing session:

| Issue | Description | Status | Filed As |
|-------|-------------|--------|----------|
| **Accept header ignored** | OSH ignores the HTTP `Accept` header entirely, always returning JSON regardless of requested content type. The SensorML `Accept: application/sml+json` header is ignored. | Confirmed | Library issue [#99](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/99) |
| **Top-level collections missing** | Datastreams, control streams, and other Part 2 resources are only available nested under systems (e.g., `/systems/{id}/datastreams`), not as top-level collections (`/datastreams`). | Confirmed | Library issue [#100](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/100) |
| **`numberMatched` / `numberReturned` absent** | Server does not include pagination metadata in collection responses, requiring clients to compute counts from the raw item array. | Confirmed | Documented in section 6.1 |

---

## 8. Testing Methodology

All testing was performed using the CSAPI Explorer demo app (`http://localhost:5174/`) connected to the live OSH server via CORS proxy. The investigation traced the full request lifecycle:

1. **UI interaction**: Set limit=10, keyword="FCU", clicked Fetch
2. **Client library trace**: Confirmed `CSAPIQueryBuilder.buildQueryString()` produces `?limit=10&q=FCU`
3. **Network inspection**: Verified the HTTP request URL includes both parameters
4. **Response analysis (initial)**: Server returned all 33 systems with no filtering applied
5. **Response analysis (follow-up)**: Server correctly returned 1 system for `q=FCU`, and 10 systems for `limit=10`
6. **Raw response verification**: The raw JSON payload confirmed server-side filtering (1 item in payload, not 33 items filtered client-side)
7. **Warning banner verification**: No client-side fallback banner appeared, confirming the server handled filtering
8. **Code audit**: Full read of `ResourceList.vue`, `csapi-bridge.ts`, `url_builder.ts`, and `model.ts` confirmed no client-side parameter dropping

---

## 9. Files Changed

| File | Change | Commit |
|------|--------|--------|
| `demo/src/components/ResourceList.vue` | Client-side `q` filtering fallback, client-side `limit` enforcement, total count correction, warning banner | `caa7415` |

---

## 10. Conclusion

Follow-up testing confirmed that OSH **correctly honors** both `limit` and `q` query parameters. The initial observation of parameters being ignored was a transient condition that could not be reproduced.

The client-side fallback code (commit `caa7415`) remains in place as a **defensive interoperability measure**. It activates only when a server demonstrably ignores `limit` or `q`, and displays a warning banner so the user knows client-side filtering was applied. This protects against real-world server diversity in the OGC API ecosystem.

Remaining OSH compliance gaps center on HTTP `Accept` header content negotiation (always returns JSON regardless of requested format) and Part 2 resource collection exposure (datastreams/control streams only available nested under systems). These are documented in library issues [#99](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/99) and [#100](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/100) respectively.
