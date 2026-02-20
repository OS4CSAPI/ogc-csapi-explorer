# OSH Server Query Parameter Compliance Report

> **Date**: 2026-02-20  
> **Commit**: `caa7415` (fix: client-side fallback for servers that ignore q/limit params)  
> **Server under test**: OpenSensorHub (OSH) at `http://45.55.99.236:8080/sensorhub/api`  
> **Spec references**: OGC API — Features Part 1: Core (17-069r4), OGC API — Connected Systems Part 1 & 2 (Draft)

---

## 1. Executive Summary

During testing of the CSAPI Explorer demo app against a live OpenSensorHub (OSH) server, we discovered that OSH **silently ignores** the `?limit=` and `?q=` query parameters on collection endpoints. The server accepts both parameters without returning an error (no HTTP 400), but does not apply them — it returns the full, unfiltered collection regardless. This violates the OGC API — Features Core requirement for `limit` and the Connected Systems Part 2 requirement for `q`.

A client-side workaround has been implemented in the Explorer demo (commit `caa7415`), but the root cause is a server-side compliance gap that should be addressed by the OSH maintainers.

---

## 2. Observed Behavior

### 2.1 The `limit` Parameter Is Ignored

**Request sent:**
```
GET /sensorhub/api/systems?limit=10
Accept: application/json
```

**Expected behavior:** Response contains at most 10 items, with a `next` link if more are available.

**Actual behavior:** Response contains all 33 systems. The `limit` parameter is accepted (no error) but has no effect on the result set.

### 2.2 The `q` (Keyword Search) Parameter Is Ignored

**Request sent:**
```
GET /sensorhub/api/systems?limit=10&q=FCU
Accept: application/json
```

**Expected behavior:** Response contains only systems matching the keyword "FCU", limited to 10 results.

**Actual behavior:** Response contains all 33 systems, unfiltered. The `q` parameter is accepted (no error) but has no effect on the result set.

### 2.3 Impact on Client Applications

The demo UI showed **"33 of 33 results"** even though the user had:
- Set the limit to 10
- Entered "FCU" as a keyword filter

This is confusing because the URL bar confirms the parameters were sent correctly — the server simply did not honor them.

---

## 3. Specification Requirements

### 3.1 `limit` — OGC API Features Core (Requirement 22)

The `limit` parameter is a **Core requirement** in OGC API — Features Part 1 (17-069r4):

> **Requirement 22 — /req/core/fc-limit-response-1:**
> 
> A. The response SHALL not contain more features than specified by the optional `limit` parameter.  
> B. If the API definition specifies a maximum value for `limit` parameter, the response SHALL not contain more features than this maximum value.  
> C. If the value of the `limit` parameter is larger than the maximum value, this SHALL NOT result in an error (instead use the maximum as the parameter value).  
> D. Only items are counted that are on the first level of the collection.

The word **"SHALL"** makes this a normative requirement. A conformant server **must** respect the `limit` parameter and return no more items than requested.

### 3.2 `q` — OGC API Connected Systems Part 2

The `q` parameter is defined in OGC API — Connected Systems Part 2 as a free-text keyword search filter. While this is still a draft specification, OSH claims to implement Connected Systems and its API definition (OpenAPI) advertises the `q` parameter. Per **Requirement 9 (/req/core/query-param-invalid)** from the Features Core:

> The server SHALL respond with a response with the status code 400, if the request URI includes a query parameter that has an invalid value.

And per **Requirement 8 (/req/core/query-param-unknown)**:

> The server SHALL respond with a response with the status code 400, if the request URI includes a query parameter that is not specified in the API definition.

Since OSH accepts `q` without a 400 error, it implicitly claims to support it. Accepting the parameter and silently ignoring it is worse than rejecting it — it gives the client a false impression that filtering was applied.

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

## 5. Client-Side Workaround

Commit `caa7415` implements a client-side fallback in `ResourceList.vue` to maintain a correct UI when servers ignore parameters:

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

### 5.5 Limitations of the Workaround

| Limitation | Impact |
|-----------|--------|
| **Client filtering only works on data already fetched** | If the server has 10,000 items and returns all of them, the client can filter — but if the server's own default limit caps at, say, 100, the client can only filter within those 100 |
| **`q` matching is naive** | The client matches against a limited set of string fields (`id`, `name`, `title`, `description`, `uniqueId`). Server-side `q` could match against additional fields, nested properties, or use full-text search |
| **Pagination is broken** | With the server ignoring `limit` and `offset`, offset-based pagination cannot work correctly. The client can only paginate within locally-held data |
| **Performance** | Fetching all items when only a page is needed wastes bandwidth and processing time |

---

## 6. Recommendations for OSH Maintainers

### 6.1 Priority 1: Implement `limit` Parameter (Core Compliance)

**Why:** This is a normative SHALL requirement from OGC API — Features Core. Without it, the server cannot claim OGC API Core conformance.

**Expected implementation:**
- Parse the `limit` query parameter from the request URL
- Cap the result set to `min(limit, server_max_limit)` items
- Include a `next` link in the response if more items are available
- Set `numberReturned` to the actual count of items in the response
- Optionally set `numberMatched` to the total number of matching items

**Spec reference:** Requirement 22, `/req/core/fc-limit-response-1`

### 6.2 Priority 2: Implement `offset` Parameter (Paging Support)

**Why:** Without `offset` (or an equivalent cursor mechanism), clients cannot paginate through collections. The `next` link in the response should provide the mechanism, but OSH does not include `next` links either.

**Expected implementation:**
- Parse the `offset` query parameter
- Skip the first `offset` items in the result set
- Include `next` and optionally `prev` links in the response with correct offset values
- Example: `?limit=10&offset=10` → skip first 10, return next 10

**Spec reference:** Recommendation 17–19, response `next` links

### 6.3 Priority 3: Implement `q` Parameter (CSAPI Part 2 Compliance)

**Why:** The OSH OpenAPI definition advertises `q` as a supported parameter. Accepting it without applying it violates the principle of least surprise and makes the API unreliable.

**Expected implementation:**
- Parse the `q` query parameter as a case-insensitive free-text keyword
- Match against relevant text properties of each resource (at minimum: `name`, `description`, `uniqueId`)
- Return only items that match the keyword
- If `q` is not yet implementable, **return HTTP 400** rather than silently ignoring it, per Requirement 8

**Spec reference:** CSAPI Part 2, Features Core Requirement 8 (`/req/core/query-param-unknown`)

### 6.4 Priority 4: Include `numberMatched` / `numberReturned` in Responses

**Why:** Clients need these values to display accurate pagination metadata ("Showing X of Y"). Without them, clients must make additional requests or guess.

**Expected implementation:**
- `numberReturned`: count of items in the current response page
- `numberMatched`: total count of items matching the current filters (optional but strongly recommended)

**Spec reference:** Requirements 31–32, `/req/core/fc-numberMatched`, `/req/core/fc-numberReturned`

### 6.5 General: Reject Unknown/Unsupported Parameters with HTTP 400

Per OGC API — Features Core Requirements 8 and 9, the server **SHALL** return HTTP 400 for unknown or invalid query parameters. If a parameter like `q` is advertised in the OpenAPI definition but not yet implemented, the server should either:

1. **Implement it**, or
2. **Remove it from the OpenAPI definition** and return HTTP 400 when it's used, or
3. **Return HTTP 501 (Not Implemented)** with an informative error message

Silent acceptance without application is the worst option — it prevents clients from detecting the gap and falling back gracefully.

---

## 7. Other OSH Interoperability Gaps Found in This Session

This report focuses on `limit` and `q`, but other compliance gaps were discovered during this testing session:

| Issue | Description | Filed As |
|-------|-------------|----------|
| **Accept header ignored** | OSH ignores the HTTP `Accept` header entirely, always returning JSON regardless of requested content type. The SensorML `Accept: application/sml+json` header is ignored. | Library issue [#99](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/99) |
| **Top-level collections missing** | Datastreams, control streams, and other Part 2 resources are only available nested under systems (e.g., `/systems/{id}/datastreams`), not as top-level collections (`/datastreams`). The `assertResourceAvailable()` check in the client library is overly strict for per-ID methods. | Library issue [#100](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/100) |

---

## 8. Testing Methodology

All testing was performed using the CSAPI Explorer demo app (`http://localhost:5174/`) connected to the live OSH server via CORS proxy. The investigation traced the full request lifecycle:

1. **UI interaction**: Set limit=10, keyword="FCU", clicked Fetch
2. **Client library trace**: Confirmed `CSAPIQueryBuilder.buildQueryString()` produces `?limit=10&q=FCU`
3. **Network inspection**: Verified the HTTP request URL includes both parameters
4. **Response analysis**: Server returns all 33 systems with no filtering applied
5. **Code audit**: Full read of `ResourceList.vue`, `csapi-bridge.ts`, `url_builder.ts`, and `model.ts` confirmed no client-side parameter dropping

---

## 9. Files Changed

| File | Change | Commit |
|------|--------|--------|
| `demo/src/components/ResourceList.vue` | Client-side `q` filtering fallback, client-side `limit` enforcement, total count correction, warning banner | `caa7415` |

---

## 10. Conclusion

The OSH server's silent ignoring of `limit` and `q` query parameters is a significant interoperability gap that affects any client attempting to use standard OGC API filtering and pagination. The `limit` violation is particularly notable because it is a normative **SHALL** requirement from the OGC API — Features Core specification.

The client-side workaround implemented in the Explorer demo provides a reasonable user experience despite the server limitation, but it is inherently limited — true pagination and server-side full-text search cannot be replicated client-side.

We recommend the OSH maintainers prioritize `limit` implementation (Core compliance), followed by `offset`/pagination support, and then `q` keyword search. If any parameter is not yet implementable, it should be rejected with HTTP 400 rather than silently ignored.
