# Pagination in the CSAPI Explorer: Offset vs. Cursor

## Overview

The Explorer page provides two pagination modes — **Offset** (default) and **Cursor** — that demonstrate how the client library supports both client-driven and server-driven pagination patterns defined by the OGC API specification.

## Offset Mode (Default)

The client library builds the URL with `limit` + `offset` query parameters:

```
/systems?limit=10&offset=0   → page 1
/systems?limit=10&offset=10  → page 2
/systems?limit=10&offset=20  → page 3
```

The demo app tracks `offset` as a local number and increments/decrements it by `limit` when Next/Previous is clicked. The library's `QueryOptions.offset` is serialized into the URL by `CSAPIQueryBuilder.buildQueryString()`.

- **Pro**: Random access — you can jump to any page.
- **Con**: If items are inserted or deleted between requests, you can skip or duplicate items.

## Cursor Mode

Instead of the client calculating the next offset, the **server tells you** where the next page is via HATEOAS `links` in the response. For example, OSH SensorHub returns:

```json
{
  "items": [...],
  "links": [
    { "rel": "next", "href": "http://server/systems?limit=3&offset=3" },
    { "rel": "prev", "href": "http://server/systems?limit=3&offset=0" }
  ]
}
```

When Next is clicked in cursor mode, the demo **follows the server's `next` link directly** rather than calculating `offset + limit`. The library's `parseCollectionResponse()` normalizes these links from both response envelope formats (`FeatureCollection` and `items`), making them available as `parsed.links`.

- **Pro**: Server-controlled — safe even if data changes between pages, and works with servers that use opaque cursor tokens instead of numeric offsets.
- **Con**: No random access (you can only go forward/backward).

## What the Client Library Provides

The library handles both approaches through two complementary mechanisms:

### 1. URL Construction (`QueryOptions`)

The `QueryOptions` interface (defined in `src/ogc-api/csapi/model.ts`) includes:

| Field     | Type     | Purpose                                           |
|-----------|----------|---------------------------------------------------|
| `limit`   | `number` | Maximum items per page                             |
| `offset`  | `number` | Offset-based pagination — number of items to skip  |
| `cursor`  | `string` | Cursor-based pagination — opaque token from server |

`CSAPIQueryBuilder.buildQueryString()` serializes whichever pagination field is provided into the URL query string.

### 2. Response Parsing (`parseCollectionResponse`)

`parseCollectionResponse()` (in `src/ogc-api/csapi/formats/response.ts`) normalizes server responses into a `CollectionResponse` containing:

| Field            | Type             | Purpose                                        |
|------------------|------------------|------------------------------------------------|
| `items`          | `T[]`            | The resource items for this page               |
| `links`          | `ResourceLink[]` | HATEOAS navigation links (`next`, `prev`, etc) |
| `numberMatched`  | `number?`        | Total items matching the query (if provided)   |
| `numberReturned` | `number?`        | Items returned in this page (if provided)      |

This works regardless of whether the server uses the GeoJSON `FeatureCollection` envelope (`{ type: "FeatureCollection", features: [...] }`) or the items envelope (`{ items: [...] }`).

## How to Demonstrate in the Demo App

1. **Connect to OSH SensorHub**, go to Explorer, select **Systems**.
2. **Set limit to 3** (small enough to see pagination clearly with the ~32 available systems).
3. **In Offset mode**: Click Next a few times — watch the offset counter increment by 3. The URL the library builds changes from `?limit=3` → `?limit=3&offset=3` → `?limit=3&offset=6`.
4. **Toggle to Cursor mode**: Click Fetch, then Next — open the **Raw Response** section at the bottom and look at the `links` array. The demo now follows the server's `next` href instead of calculating the offset itself. The Previous/Next buttons enable/disable based on whether the server provided `prev`/`next` links.

## Key Takeaway

The library gives you **both tools** — `QueryOptions.limit`/`offset` for client-driven pagination, and `parseCollectionResponse().links` for server-driven (HATEOAS) pagination — and the OGC API spec supports both patterns. OSH happens to use offset-based links even in cursor mode, but other servers (like 52North) might use opaque cursor tokens, and the cursor approach handles both transparently because the client simply follows the URL the server provides.
