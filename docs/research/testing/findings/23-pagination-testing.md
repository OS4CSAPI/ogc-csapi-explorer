# Section 23: Pagination Testing Strategy - FINDINGS

> ⚠️ **REVIEW NOTICE — CRITICAL (C2): `fetchJson()` Test Templates Assert Fixture Content, Not Client Behavior**
>
> **Phase 2E Review | Issues: C2, H7, M4, M9, L3 | Anti-Patterns: AP1, AP4, AP5**
>
> This document is ~40% client-oriented. The URL construction tests using `builder.*` + `parseAndValidateUrl()` (Sections 5.1-5.3 partial) and the link parsing utilities (Section 5.4) are correctly client-oriented. However, Sections 5.1-5.2 contain ~30 test scenarios using an undefined `fetchJson()` function that directly assert server response fixture content — these would pass even if the client code did nothing.
>
> **What's usable:** URL construction tests (`builder.getSystems()`, `builder.getObservations()`), link parsing utilities (`extractNextLink`, `extractCursor`, `isLastPage`), fixture design patterns (Section 4).
>
> **What must be rewritten:** All `fetchJson()` tests must be reframed as: feed fixture through mocked `globalThis.fetch` → call client pagination methods → assert client's parsed output. See Section 5.4 for the document's own model of correctly client-oriented tests.
>
> See also: [Phase 2E Review Report](../review/phase-2e-advanced-scenarios-category.md)

**Research Plan:** [Research Plan 23: Pagination Testing Strategy](../research-plans/23-pagination-testing.md)

**Research Questions:** 6 core questions about testing offset-based pagination (limit/offset), cursor-based pagination (limit/cursor), edge cases (empty pages, boundary conditions), pagination with filtering, pagination link parsing, and fixtures needed for multi-page scenarios

**Methodology:** 6-phase systematic analysis (Phase 1: Pagination Specification Analysis extracting offset-based (Part 1) and cursor-based (Part 2) patterns → Phase 2: Upstream Pagination Pattern Analysis of existing tests → Phase 3: Pagination Scenario Identification across both modes → Phase 4: Fixture Design for multi-page datasets → Phase 5: Test Pattern Design for link parsing and query parameters → Phase 6: Synthesis into comprehensive pagination testing strategy)

**Research Time:** ~3 hours (February 5, 2026)

**Primary Source(s):**

- [CSAPI Part 2 Specification](https://docs.ogc.org/is/23-002/23-002.html) (cursor-based pagination)
- [Part 2 Requirements](../../requirements/csapi-part2-requirements.md)
- [CSAPI Implementation Guide](../../../planning/csapi-implementation-guide.md) (Pagination specifications)

**Supporting Resources:**

- [CSAPI Part 1 Specification](https://docs.ogc.org/is/23-001/23-001.html) (offset-based pagination)
- [OGC API - Common](https://docs.ogc.org/is/19-072/19-072.html) (pagination patterns)
- Section 1: [EDR Test Blueprint](01-edr-test-blueprint.md) (upstream pagination patterns)
- Section 2: [Upstream Test Consistency](02-upstream-test-consistency.md) (pagination testing)
- Section 13: [Resource Method Testing Patterns](13-resource-method-testing-patterns.md) (resource pagination)

**Document Purpose:** Defines comprehensive testing strategy covering two distinct CSAPI pagination modes with 50+ test scenarios including offset-based (Part 1: limit/offset with page jumping) and cursor-based (Part 2: limit/cursor with 10,000 max for large time series), edge cases, filtering interactions, and link parsing patterns

---

## Executive Summary

CSAPI implements **two distinct pagination modes**:

1. **Offset-Based Pagination (Part 1):** Traditional page-number style using `limit` + `offset` parameters
2. **Cursor-Based Pagination (Part 2):** Optimized streaming using `limit` + `cursor` parameters for large time series

This document defines a comprehensive testing strategy covering both modes with 50+ test scenarios, including edge cases, filtering interactions, and link parsing patterns.

### Key Findings

- **Two Pagination Modes:** Offset-based (Part 1) and cursor-based (Part 2) with different characteristics
- **Limit Constraints:** Part 1 has implementation-dependent max; Part 2 has explicit max of 10,000
- **Cursor Opacity:** Cursor values are opaque - clients must extract from links, not construct
- **Response Metadata:** `numberMatched` (optional total) and `numberReturned` (required page size)
- **Standard Link Relations:** `next`, `prev`, `first`, `last` following OGC API pattern
- **Existing Tests:** Section 13 includes basic pagination test in resource method template
- **Upstream Patterns:** STAC/Features examples demonstrate link following for pagination

---

## 1. Pagination Specification Analysis

### 1.1 Offset-Based Pagination (Part 1)

**Pattern:** `?limit=10&offset=0` (page 1), `?limit=10&offset=10` (page 2)

**Parameters:**

- **limit**: Maximum items per page
  - Type: Positive integer
  - Range: 1 to implementation-dependent maximum
  - Default: Typically 10-100 (implementation-dependent)
  - Validation: MUST be ≥ 1
- **offset**: Number of items to skip
  - Type: Non-negative integer
  - Range: ≥ 0 (0-based index)
  - Default: 0
  - Validation: MUST be ≥ 0
  - Behavior: Offset beyond result set → empty collection (not error)

**Use Cases:**

- Predictable page numbers (page 1, 2, 3, ...)
- Jump to arbitrary positions (page 10, page 100)
- Back/forward navigation with known pages
- Small to medium datasets (< 100K items)

**Link Relations:**

```json
{
  "links": [
    {
      "rel": "self",
      "href": "/systems?limit=10&offset=0"
    },
    {
      "rel": "next",
      "href": "/systems?limit=10&offset=10"
    },
    {
      "rel": "prev",
      "href": "/systems?limit=10&offset=0"
    },
    {
      "rel": "first",
      "href": "/systems?limit=10&offset=0"
    },
    {
      "rel": "last",
      "href": "/systems?limit=10&offset=490"
    }
  ],
  "numberMatched": 500,
  "numberReturned": 10
}
```

**Performance Characteristics:**

- **Pros:** Predictable, can jump to any page, easy to implement
- **Cons:** Large offsets inefficient (server must skip N items), unstable across result set changes

**Applies To:** All Part 1 resources (Systems, Deployments, Procedures, SamplingFeatures, Properties)

### 1.2 Cursor-Based Pagination (Part 2)

**Pattern:** `?limit=100` (first), `?limit=100&cursor=abc123` (next)

**Parameters:**

- **limit**: Maximum items per page
  - Type: Positive integer
  - Range: 1 to 10,000 (Part 2 maximum)
  - Default: 10
  - Validation: MUST be ≥ 1, MUST be ≤ 10,000
- **cursor**: Opaque continuation token
  - Type: Opaque string (implementation-specific)
  - Format: Server-defined (commonly base64-encoded JSON)
  - Source: Extracted from `next` link href in previous response
  - Client behavior: MUST NOT parse, construct, or modify cursor values
  - Validation: Invalid cursor → 400 Bad Request

**Use Cases:**

- Efficient streaming of large time series (> 100K observations)
- Real-time data feeds with frequent updates
- Stable pagination across result set changes
- Memory-efficient sequential traversal

**Cursor Extraction:**

```typescript
// Extract cursor from next link
const nextLink = response.links?.find((l) => l.rel === 'next');
if (nextLink) {
  const url = new URL(nextLink.href);
  const cursor = url.searchParams.get('cursor');
  // Use cursor in next request
}
```

**Link Relations:**

```json
{
  "links": [
    {
      "rel": "self",
      "href": "/observations?limit=100"
    },
    {
      "rel": "next",
      "href": "/observations?limit=100&cursor=eyJwaGVub21lbm9uVGltZSI6IjIwMjQtMDEtMTVUMTI6MDA6MDBaIiwiaWQiOjEwMDB9"
    }
  ],
  "numberMatched": 150000,
  "numberReturned": 100
}
```

**Performance Characteristics:**

- **Pros:** Efficient for large datasets, stable across changes, no performance degradation
- **Cons:** Cannot jump to arbitrary pages, must traverse sequentially, cursor may expire

**Applies To:** Part 2 resources (DataStreams, Observations, ControlStreams, Commands, etc.)

### 1.3 Response Metadata

**numberMatched** (optional):

- Type: Integer
- Meaning: Total count of items matching query
- Optional: Server MAY omit if expensive to calculate
- Client handling: Should handle presence/absence gracefully

**numberReturned** (required):

- Type: Integer
- Meaning: Number of items in current response
- Required: MUST be present
- Range: 0 to limit

### 1.4 Pagination + Query Parameters

Pagination combines with all query parameters:

**Spatial Filtering:**

```
GET /systems?bbox=-180,-90,180,90&limit=100&offset=0
```

**Temporal Filtering:**

```
GET /observations?phenomenonTime=2024-01-01/2024-12-31&limit=1000&cursor=abc123
```

**Relationship Filtering:**

```
GET /deployments?system=sys123&limit=50&offset=100
```

**Execution Order:**

1. Apply all filters (bbox, datetime, parent, etc.)
2. Apply pagination to filtered results

---

## 2. Upstream Pagination Pattern Analysis

### 2.1 EDR Pagination (PR #114)

**Observation:** No dedicated pagination tests in EDR codebase

**Reason:** EDR focuses on spatial/temporal queries for specific areas, not large-scale pagination

**Pagination Parameters Present:**

- `limit` and `offset` parameters in endpoint methods
- No explicit pagination test coverage
- No link following patterns

**Implications for CSAPI:**

- CSAPI needs more comprehensive pagination testing than EDR
- Must test both offset and cursor modes
- Must test link following and cursor extraction

### 2.2 STAC Pagination Example

**Pattern:** Link following for pagination

```javascript
// From examples/stac-query.js
const firstPage = await stac.getCollectionItemsResponse(collectionId, {
  limit: 2,
});

const nextLink = firstPage.links?.find((link) => link.rel === 'next');
if (nextLink) {
  const nextPage = await StacEndpoint.getItemsFromUrl(nextLink.href);
  // Process next page
}
```

**Key Pattern:** Extract `rel="next"` link, follow href to next page

### 2.3 Features API Pagination

**Pattern:** Similar to STAC - link-based navigation

**From csapi-gap-analysis.md:**

```typescript
// Follow rel=next links for pagination
async *listSystemsPaginated(params?: QueryParams): AsyncGenerator<System> {
  let url: string | null = this.buildUrl('/systems', params);

  while (url) {
    const response = await this.http.get(url);
    const collection = response.data as FeatureCollection;

    // Yield all items from this page
    for (const feature of collection.features) {
      yield feature as System;
    }

    // Find next link
    const nextLink = collection.links?.find(l => l.rel === 'next');
    url = nextLink?.href || null;
  }
}
```

**Key Pattern:** AsyncGenerator for streaming pagination

### 2.4 Section 13 Resource Method Tests

**Existing Pagination Test:**

```typescript
it('applies pagination parameters', async () => {
  const url = builder.getResourceTypes({ limit: 50, offset: 100 });
  parseAndValidateUrl(url, {
    pathname: '/resourcetypes',
    query: {
      limit: '50',
      offset: '100',
    },
  });
});
```

**Coverage:** Basic pagination parameter validation (part of 12 base tests per resource)

**Gaps:**

- No multi-page scenarios
- No edge cases (empty, boundaries)
- No link parsing tests
- No cursor-based pagination tests
- No pagination + filtering combinations

---

## 3. Pagination Scenario Matrix

### 3.1 Offset-Based Pagination Scenarios (15 scenarios)

#### Basic Navigation (5 scenarios)

1. **First page (offset=0)**

   - URL: `?limit=10&offset=0`
   - Expected: First 10 items, `next` link present, no `prev` link

2. **Middle page**

   - URL: `?limit=10&offset=50`
   - Expected: Items 51-60, both `next` and `prev` links present

3. **Last page**

   - URL: `?limit=10&offset=90` (for 100 items total)
   - Expected: Items 91-100, `prev` link present, no `next` link

4. **Next page navigation**

   - Follow `rel="next"` link from first page
   - Expected: Second page items, correct offset in URL

5. **Previous page navigation**
   - Follow `rel="prev"` link from middle page
   - Expected: Previous page items, correct offset in URL

#### Boundary Conditions (5 scenarios)

6. **Offset at exact end (offset = numberMatched)**

   - URL: `?limit=10&offset=100` (for 100 items total)
   - Expected: Empty collection, no errors

7. **Offset beyond end**

   - URL: `?limit=10&offset=500` (for 100 items total)
   - Expected: Empty collection, no errors

8. **Partial last page**

   - URL: `?limit=10&offset=95` (for 100 items total)
   - Expected: 5 items (95-99), no `next` link

9. **Exactly one page (items = limit)**

   - URL: `?limit=10` (for exactly 10 items total)
   - Expected: All 10 items, no `next` link

10. **Single item result**
    - URL: `?limit=10` (for 1 item total)
    - Expected: 1 item, no `next` link

#### Invalid Parameters (5 scenarios)

11. **Zero limit**

    - URL: `?limit=0`
    - Expected: 400 Bad Request

12. **Negative limit**

    - URL: `limit=-10`
    - Expected: 400 Bad Request

13. **Negative offset**

    - URL: `?offset=-10`
    - Expected: 400 Bad Request

14. **Non-numeric limit**

    - URL: `?limit=abc`
    - Expected: 400 Bad Request

15. **Non-numeric offset**
    - URL: `?offset=xyz`
    - Expected: 400 Bad Request

### 3.2 Cursor-Based Pagination Scenarios (12 scenarios)

#### Basic Navigation (5 scenarios)

16. **First page (no cursor)**

    - URL: `?limit=100`
    - Expected: First 100 items, `next` link with cursor

17. **Second page (cursor from first)**

    - URL: `?limit=100&cursor=abc123`
    - Expected: Items 101-200, `next` link with new cursor

18. **Last page (cursor points to last batch)**

    - URL: `?limit=100&cursor=last123`
    - Expected: Remaining items (< 100), no `next` link

19. **Cursor extraction from next link**

    - Parse cursor from `next` link href
    - Expected: Cursor value extracted correctly

20. **Sequential traversal (follow all pages)**
    - Follow `next` links until no more
    - Expected: All items retrieved, no duplicates

#### Part 2 Specific (4 scenarios)

21. **Limit exactly 10,000 (Part 2 maximum)**

    - URL: `?limit=10000`
    - Expected: Up to 10,000 items, no error

22. **Limit exceeds 10,000 (Part 2 maximum)**

    - URL: `?limit=15000`
    - Expected: 400 Bad Request (exceeds Part 2 max)

23. **Default limit (no limit parameter)**

    - URL: `/observations` (no limit specified)
    - Expected: 10 items (Part 2 default), `next` link if more items

24. **Large dataset streaming (100K+ items)**
    - Sequential pagination through 100,000+ observations
    - Expected: Efficient traversal, stable cursors

#### Invalid Cursor (3 scenarios)

25. **Invalid cursor format**

    - URL: `?cursor=invalid!!!`
    - Expected: 400 Bad Request

26. **Expired cursor**

    - URL: `?cursor=expired_cursor_token`
    - Expected: 400 Bad Request (cursor expired)

27. **Malformed base64 cursor**
    - URL: `?cursor=not-valid-base64`
    - Expected: 400 Bad Request

### 3.3 Edge Cases (8 scenarios)

28. **Empty result set**

    - Query returns 0 items
    - Expected: Empty features array, no pagination links, numberReturned=0

29. **Single page of results (items < limit)**

    - 5 items total, limit=10
    - Expected: 5 items returned, no `next` link

30. **Exactly limit items (items = limit)**

    - 10 items total, limit=10
    - Expected: 10 items, no `next` link (or next returns empty)

31. **numberMatched absent**

    - Response omits `numberMatched` property
    - Expected: Client handles gracefully (no errors)

32. **numberMatched present**

    - Response includes `numberMatched: 500`
    - Expected: Client can use for total page calculation

33. **Large limit value (Part 1)**

    - URL: `?limit=1000000` (Part 1, no explicit max)
    - Expected: Server MAY return fewer (server max), no error

34. **Limit larger than result set**

    - limit=1000, only 50 items exist
    - Expected: All 50 items returned, no `next` link

35. **Offset + cursor together**
    - URL: `?limit=100&offset=50&cursor=abc` (mixed mode)
    - Expected: Server behavior undefined (test actual server behavior)

### 3.4 Pagination + Filtering (10 scenarios)

36. **Pagination + bbox filter**

    - URL: `?bbox=-180,-90,180,90&limit=50&offset=0`
    - Expected: First 50 items in bbox

37. **Pagination + datetime filter**

    - URL: `?datetime=2024-01-01/2024-12-31&limit=100`
    - Expected: First 100 items in date range

38. **Pagination + phenomenonTime filter**

    - URL: `?phenomenonTime=2024-01-01/..&limit=1000&cursor=abc`
    - Expected: Observations after date, paginated with cursor

39. **Pagination + parent filter**

    - URL: `?parent=sys123&limit=20&offset=0`
    - Expected: First 20 subsystems of sys123

40. **Pagination + multiple filters**

    - URL: `?bbox=...&datetime=...&systemType=sensor&limit=50`
    - Expected: First 50 items matching all filters

41. **Empty result after filtering**

    - URL: `?bbox=0,0,0,0&limit=10` (no items in bbox)
    - Expected: Empty collection, no pagination links

42. **Single page after filtering**

    - Filters reduce results to 5 items, limit=10
    - Expected: 5 items, no `next` link

43. **Pagination + observedProperty filter**

    - URL: `?observedProperty=temperature&limit=100`
    - Expected: First 100 systems observing temperature

44. **Pagination + resultTime=latest**

    - URL: `?resultTime=latest&limit=10`
    - Expected: 10 most recent observations (not paginated)

45. **Pagination + foi filter**
    - URL: `?foi=river123&limit=50&offset=100`
    - Expected: Items 101-150 observing river123

### 3.5 Link Parsing (8 scenarios)

46. **Extract next link rel**

    - Parse `links` array for `rel="next"`
    - Expected: Correct next link object

47. **Extract prev link rel**

    - Parse `links` array for `rel="prev"`
    - Expected: Correct prev link object

48. **Extract first link rel**

    - Parse `links` array for `rel="first"`
    - Expected: Link to first page

49. **Extract last link rel**

    - Parse `links` array for `rel="last"`
    - Expected: Link to last page (if numberMatched available)

50. **Missing next link (last page)**

    - Last page has no `rel="next"` link
    - Expected: Graceful handling, pagination stops

51. **Parse cursor from next link href**

    - Extract cursor parameter from next link URL
    - Expected: Cursor value extracted correctly

52. **Validate link href absolute URL**

    - Link href is absolute URL (not relative)
    - Expected: Valid absolute URL format

53. **Link type validation**
    - Link has `type: "application/json"`
    - Expected: Correct media type present

### 3.6 Metadata Validation (5 scenarios)

> ℹ️ **REVIEW NOTICE (L3): Metadata Validation Checks Fixture Invariants, Not Client Behavior**
>
> These 5 scenarios validate spec invariants (`numberReturned === features.length`, `numberMatched ≥ numberReturned`) that are properties of the server response, not client transformations. In a mocked-fetch test, the fixture already contains these values by construction — asserting them tests the fixture, not the client. If client code needs to USE `numberMatched` (e.g., to display total count), test the client's consumption of that value, not its presence in the response.

54. **numberReturned matches item count**

    - Validate `numberReturned` equals `features.length`
    - Expected: Values match

55. **numberReturned ≤ limit**

    - Validate `numberReturned` does not exceed requested limit
    - Expected: numberReturned ≤ limit

56. **numberMatched ≥ numberReturned**

    - Validate total ≥ current page size
    - Expected: numberMatched ≥ numberReturned

57. **Last page: offset + numberReturned = numberMatched**

    - Validate last page completes pagination
    - Expected: offset + numberReturned = numberMatched

58. **Cursor pagination: numberMatched may be absent**
    - Cursor mode response may omit numberMatched
    - Expected: Client handles absence gracefully

---

## 4. Fixture Design

### 4.1 Large Dataset Fixtures

**Systems Collection (200 items):**

- File: `fixtures/ogc-api/csapi/sample-csapi-systems-large.json`
- 200 system resources
- Enables testing multiple pages (10 pages at limit=20)
- Realistic system properties (names, types, descriptions)

**Observations Collection (1000 items):**

- File: `fixtures/ogc-api/csapi/sample-datastream-observations-1000.json`
- 1000 observation resources
- Temporal sequence (2024-01-01 to 2024-01-31, ~30 per day)
- Enables cursor pagination testing

### 4.2 Multi-Page Response Fixtures

**Page 1 (First Page):**

```json
{
  "type": "FeatureCollection",
  "features": [
    /* 10 items */
  ],
  "links": [
    {
      "rel": "self",
      "href": "https://api.example.org/systems?limit=10&offset=0"
    },
    {
      "rel": "next",
      "href": "https://api.example.org/systems?limit=10&offset=10"
    },
    {
      "rel": "first",
      "href": "https://api.example.org/systems?limit=10&offset=0"
    },
    {
      "rel": "last",
      "href": "https://api.example.org/systems?limit=10&offset=190"
    }
  ],
  "numberMatched": 200,
  "numberReturned": 10
}
```

**Page 2 (Middle Page):**

```json
{
  "type": "FeatureCollection",
  "features": [
    /* 10 items (items 11-20) */
  ],
  "links": [
    {
      "rel": "self",
      "href": "https://api.example.org/systems?limit=10&offset=10"
    },
    {
      "rel": "prev",
      "href": "https://api.example.org/systems?limit=10&offset=0"
    },
    {
      "rel": "next",
      "href": "https://api.example.org/systems?limit=10&offset=20"
    },
    {
      "rel": "first",
      "href": "https://api.example.org/systems?limit=10&offset=0"
    },
    {
      "rel": "last",
      "href": "https://api.example.org/systems?limit=10&offset=190"
    }
  ],
  "numberMatched": 200,
  "numberReturned": 10
}
```

**Page 20 (Last Page):**

```json
{
  "type": "FeatureCollection",
  "features": [
    /* 10 items (items 191-200) */
  ],
  "links": [
    {
      "rel": "self",
      "href": "https://api.example.org/systems?limit=10&offset=190"
    },
    {
      "rel": "prev",
      "href": "https://api.example.org/systems?limit=10&offset=180"
    },
    {
      "rel": "first",
      "href": "https://api.example.org/systems?limit=10&offset=0"
    }
    // No "next" link (last page)
  ],
  "numberMatched": 200,
  "numberReturned": 10
}
```

**Cursor-Based Page 1:**

```json
{
  "type": "FeatureCollection",
  "features": [
    /* 100 observations */
  ],
  "links": [
    {
      "rel": "self",
      "href": "https://api.example.org/observations?limit=100"
    },
    {
      "rel": "next",
      "href": "https://api.example.org/observations?limit=100&cursor=eyJwaGVub21lbm9uVGltZSI6IjIwMjQtMDEtMDRUMDA6MDA6MDBaIiwiaWQiOjEwMH0="
    }
  ],
  "numberMatched": 1000,
  "numberReturned": 100
}
```

### 4.3 Edge Case Fixtures

**Empty Collection:**

```json
{
  "type": "FeatureCollection",
  "features": [],
  "links": [
    {
      "rel": "self",
      "href": "https://api.example.org/systems?bbox=0,0,0,0&limit=10"
    }
  ],
  "numberMatched": 0,
  "numberReturned": 0
}
```

**Single Page (5 items, limit=10):**

```json
{
  "type": "FeatureCollection",
  "features": [
    /* 5 items */
  ],
  "links": [
    {
      "rel": "self",
      "href": "https://api.example.org/systems?parent=sys123&limit=10"
    }
  ],
  "numberMatched": 5,
  "numberReturned": 5
}
```

**Exactly One Page (10 items, limit=10):**

```json
{
  "type": "FeatureCollection",
  "features": [
    /* 10 items */
  ],
  "links": [
    {
      "rel": "self",
      "href": "https://api.example.org/systems?systemType=sensor&limit=10"
    }
  ],
  "numberMatched": 10,
  "numberReturned": 10
}
```

**Partial Last Page (5 items on last page):**

```json
{
  "type": "FeatureCollection",
  "features": [
    /* 5 items (items 96-100) */
  ],
  "links": [
    {
      "rel": "self",
      "href": "https://api.example.org/systems?limit=10&offset=95"
    },
    {
      "rel": "prev",
      "href": "https://api.example.org/systems?limit=10&offset=85"
    },
    {
      "rel": "first",
      "href": "https://api.example.org/systems?limit=10&offset=0"
    }
  ],
  "numberMatched": 100,
  "numberReturned": 5
}
```

**Offset Beyond End:**

```json
{
  "type": "FeatureCollection",
  "features": [],
  "links": [
    {
      "rel": "self",
      "href": "https://api.example.org/systems?limit=10&offset=500"
    },
    {
      "rel": "first",
      "href": "https://api.example.org/systems?limit=10&offset=0"
    }
  ],
  "numberMatched": 100,
  "numberReturned": 0
}
```

**No numberMatched (Cursor Mode):**

```json
{
  "type": "FeatureCollection",
  "features": [
    /* 100 observations */
  ],
  "links": [
    {
      "rel": "self",
      "href": "https://api.example.org/observations?limit=100&cursor=abc123"
    },
    {
      "rel": "next",
      "href": "https://api.example.org/observations?limit=100&cursor=def456"
    }
  ],
  "numberReturned": 100
  // numberMatched omitted
}
```

### 4.4 Error Response Fixtures

**Invalid Limit (400 Bad Request):**

```json
{
  "code": "InvalidParameterValue",
  "description": "The 'limit' parameter value '0' is invalid. Must be a positive integer (≥ 1)."
}
```

**Limit Exceeds Part 2 Maximum (400 Bad Request):**

```json
{
  "code": "InvalidParameterValue",
  "description": "The 'limit' parameter value '15000' exceeds the maximum allowed value of 10000 for Part 2 resources."
}
```

**Invalid Offset (400 Bad Request):**

```json
{
  "code": "InvalidParameterValue",
  "description": "The 'offset' parameter value '-10' is invalid. Must be a non-negative integer (≥ 0)."
}
```

**Invalid Cursor (400 Bad Request):**

```json
{
  "code": "InvalidParameterValue",
  "description": "The 'cursor' parameter value is invalid or has expired."
}
```

### 4.5 Pagination + Filtering Fixtures

**Filtered Result (50 items after filtering):**

```json
{
  "type": "FeatureCollection",
  "features": [
    /* 10 items */
  ],
  "links": [
    {
      "rel": "self",
      "href": "https://api.example.org/systems?bbox=-10,-10,10,10&limit=10&offset=0"
    },
    {
      "rel": "next",
      "href": "https://api.example.org/systems?bbox=-10,-10,10,10&limit=10&offset=10"
    }
  ],
  "numberMatched": 50,
  "numberReturned": 10
}
```

### 4.6 Fixture Summary

| Fixture Type           | Count  | Files                                                                            |
| ---------------------- | ------ | -------------------------------------------------------------------------------- |
| Large dataset fixtures | 2      | `sample-csapi-systems-large.json`, `sample-datastream-observations-1000.json`    |
| Multi-page responses   | 6      | Page 1, 2, 20 (offset), Page 1 (cursor), Last page (both modes)                  |
| Edge cases             | 6      | Empty, single page, exactly one page, partial last, beyond end, no numberMatched |
| Error responses        | 4      | Invalid limit, limit exceeds max, invalid offset, invalid cursor                 |
| Filtering fixtures     | 2      | Filtered results, empty after filtering                                          |
| **TOTAL**              | **20** | **20 fixture files**                                                             |

---

## 5. Test Pattern Design

### 5.1 Offset Pagination Test Template

> ⚠️ **REVIEW NOTICE (C2, M4, M9, L3): Mixed Client/Server Test Patterns**
>
> This section contains a mix of correctly client-oriented and server-oriented tests:
>
> **✅ Usable — URL construction tests** ("Basic Navigation", "Boundary Conditions" first halves): `builder.getSystems()` + `parseAndValidateUrl()` correctly test client URL construction. These follow upstream patterns.
>
> **❌ Must rewrite — `fetchJson()` tests** ("Edge Cases", "Metadata Validation"): These assert fixture content (`response.features`, `response.numberMatched`, `response.numberReturned`) — the exact AP1 anti-pattern. The fixture will always contain whatever you put in it.
>
> **❌ Must rewrite — "Invalid Parameters" block (M4):** Tests like `fetchJson('/systems?limit=0')` expecting `400` test whether the SERVER validates limits. Only client-side validation (e.g., `builder` rejects negative limit before sending request) is appropriate for client tests.
>
> **❌ Must rewrite — Conditional assertion (M9):** `if (response.numberMatched !== undefined) { expect(...) }` — in client tests, you control the fixture. If you need `numberMatched`, include it in the fixture; don't conditionally assert.
>
> **Rewrite pattern:** Feed fixture through mocked `globalThis.fetch` → call client pagination method → assert client parsed output (extracted page metadata, constructed next-page URL, `isLastPage()` return value).

```typescript
describe('Offset-Based Pagination', () => {
  describe('Basic Navigation', () => {
    it('constructs first page URL', async () => {
      const url = builder.getSystems({ limit: 10, offset: 0 });
      parseAndValidateUrl(url, {
        pathname: '/systems',
        query: {
          limit: '10',
          offset: '0',
        },
      });
    });

    it('constructs middle page URL', async () => {
      const url = builder.getSystems({ limit: 10, offset: 50 });
      parseAndValidateUrl(url, {
        pathname: '/systems',
        query: {
          limit: '10',
          offset: '50',
        },
      });
    });

    it('constructs last page URL', async () => {
      const url = builder.getSystems({ limit: 10, offset: 190 });
      parseAndValidateUrl(url, {
        pathname: '/systems',
        query: {
          limit: '10',
          offset: '190',
        },
      });
    });
  });

  describe('Link Parsing', () => {
    it('extracts next link from first page', async () => {
      const response = await fetchJson('/systems?limit=10&offset=0');

      const nextLink = response.links?.find((l) => l.rel === 'next');
      expect(nextLink).toBeDefined();
      expect(nextLink.href).toContain('offset=10');
    });

    it('extracts prev link from middle page', async () => {
      const response = await fetchJson('/systems?limit=10&offset=50');

      const prevLink = response.links?.find((l) => l.rel === 'prev');
      expect(prevLink).toBeDefined();
      expect(prevLink.href).toContain('offset=40');
    });

    it('has no next link on last page', async () => {
      const response = await fetchJson('/systems?limit=10&offset=190');

      const nextLink = response.links?.find((l) => l.rel === 'next');
      expect(nextLink).toBeUndefined();
    });
  });

  describe('Boundary Conditions', () => {
    it('returns empty collection when offset at exact end', async () => {
      const response = await fetchJson('/systems?limit=10&offset=200');

      expect(response.features).toEqual([]);
      expect(response.numberReturned).toBe(0);
    });

    it('returns empty collection when offset beyond end', async () => {
      const response = await fetchJson('/systems?limit=10&offset=500');

      expect(response.features).toEqual([]);
      expect(response.numberReturned).toBe(0);
    });

    it('returns partial page when at end', async () => {
      const response = await fetchJson('/systems?limit=10&offset=195');

      expect(response.features.length).toBe(5);
      expect(response.numberReturned).toBe(5);
    });
  });

  describe('Edge Cases', () => {
    it('handles empty result set', async () => {
      const response = await fetchJson('/systems?bbox=0,0,0,0&limit=10');

      expect(response.features).toEqual([]);
      expect(response.numberMatched).toBe(0);
      expect(response.numberReturned).toBe(0);

      const nextLink = response.links?.find((l) => l.rel === 'next');
      expect(nextLink).toBeUndefined();
    });

    it('handles single page result', async () => {
      const response = await fetchJson('/systems?parent=sys123&limit=10');

      expect(response.features.length).toBe(5);
      expect(response.numberMatched).toBe(5);
      expect(response.numberReturned).toBe(5);

      const nextLink = response.links?.find((l) => l.rel === 'next');
      expect(nextLink).toBeUndefined();
    });

    it('handles exactly one page', async () => {
      const response = await fetchJson('/systems?systemType=sensor&limit=10');

      expect(response.features.length).toBe(10);
      expect(response.numberMatched).toBe(10);
      expect(response.numberReturned).toBe(10);

      const nextLink = response.links?.find((l) => l.rel === 'next');
      expect(nextLink).toBeUndefined();
    });
  });

  describe('Metadata Validation', () => {
    it('validates numberReturned matches feature count', async () => {
      const response = await fetchJson('/systems?limit=10&offset=0');

      expect(response.numberReturned).toBe(response.features.length);
    });

    it('validates numberReturned ≤ limit', async () => {
      const response = await fetchJson('/systems?limit=10&offset=0');

      expect(response.numberReturned).toBeLessThanOrEqual(10);
    });

    it('validates numberMatched ≥ numberReturned', async () => {
      const response = await fetchJson('/systems?limit=10&offset=0');

      if (response.numberMatched !== undefined) {
        expect(response.numberMatched).toBeGreaterThanOrEqual(
          response.numberReturned
        );
      }
    });
  });

  describe('Invalid Parameters', () => {
    it('rejects zero limit', async () => {
      await expect(fetchJson('/systems?limit=0')).rejects.toThrow('400');
    });

    it('rejects negative limit', async () => {
      await expect(fetchJson('/systems?limit=-10')).rejects.toThrow('400');
    });

    it('rejects negative offset', async () => {
      await expect(fetchJson('/systems?offset=-10')).rejects.toThrow('400');
    });
  });
});
```

### 5.2 Cursor Pagination Test Template

> ⚠️ **REVIEW NOTICE (C2, H7): Cursor Pagination Tests Assert Server Behavior**
>
> **✅ Usable — URL construction tests** ("Basic Navigation" first two): `builder.getObservations()` + `parseAndValidateUrl()` and cursor URL construction are correctly client-oriented.
>
> **❌ Must rewrite — Server behavior assertions (H7):** Multiple tests assert server pagination state:
>
> - "follows cursor chain" loops through pages testing SERVER produces no duplicates
> - "Large Dataset Streaming" tests SERVER returns 1000+ unique items across pages
> - "Part 2 Limits" `fetchJson('/observations?limit=15000')` expects 400 — tests SERVER rejects over-limit
> - "Invalid Cursor" tests expect SERVER to return 400 for bad cursor format
> - "Metadata Validation" asserts fixture response metadata
>
> **Client tests should verify:** client correctly extracts cursor from response links, client constructs next-page URL with cursor parameter, client recognizes last page (no `next` link). See Section 5.4 for the correct pattern.

```typescript
describe('Cursor-Based Pagination', () => {
  describe('Basic Navigation', () => {
    it('constructs first page URL without cursor', async () => {
      const url = builder.getObservations('ds1', { limit: 100 });
      parseAndValidateUrl(url, {
        pathname: '/datastreams/ds1/observations',
        query: {
          limit: '100',
        },
      });
      expect(url).not.toContain('cursor');
    });

    it('constructs next page URL with cursor', async () => {
      const cursor = 'eyJpZCI6MTAwfQ==';
      const url = builder.getObservations('ds1', {
        limit: 100,
        cursor,
      });
      parseAndValidateUrl(url, {
        pathname: '/datastreams/ds1/observations',
        query: {
          limit: '100',
          cursor: cursor,
        },
      });
    });
  });

  describe('Cursor Extraction', () => {
    it('extracts cursor from next link', async () => {
      const response = await fetchJson('/observations?limit=100');

      const nextLink = response.links?.find((l) => l.rel === 'next');
      expect(nextLink).toBeDefined();

      const url = new URL(nextLink.href);
      const cursor = url.searchParams.get('cursor');
      expect(cursor).toBeDefined();
      expect(cursor).toBeTruthy();
    });

    it('follows cursor to next page', async () => {
      const page1 = await fetchJson('/observations?limit=100');
      const nextLink = page1.links?.find((l) => l.rel === 'next');

      expect(nextLink).toBeDefined();

      const page2 = await fetchJson(nextLink.href);
      expect(page2.features).toHaveLength(100);

      // Items should be different
      const page1Ids = page1.features.map((f) => f.id);
      const page2Ids = page2.features.map((f) => f.id);
      expect(page1Ids).not.toEqual(page2Ids);
    });

    it('detects last page when no next link', async () => {
      // Navigate to last page
      let response = await fetchJson('/observations?limit=100');
      let nextLink = response.links?.find((l) => l.rel === 'next');

      // Keep following until last page
      while (nextLink) {
        response = await fetchJson(nextLink.href);
        nextLink = response.links?.find((l) => l.rel === 'next');
      }

      // Last page should have no next link
      expect(nextLink).toBeUndefined();
    });
  });

  describe('Part 2 Limits', () => {
    it('accepts limit up to 10,000', async () => {
      const url = builder.getObservations('ds1', { limit: 10000 });
      parseAndValidateUrl(url, {
        pathname: '/datastreams/ds1/observations',
        query: {
          limit: '10000',
        },
      });
    });

    it('rejects limit above 10,000', async () => {
      await expect(fetchJson('/observations?limit=15000')).rejects.toThrow(
        '400'
      );
    });

    it('uses default limit of 10 when omitted', async () => {
      const response = await fetchJson('/observations');

      // Should return at most 10 items
      expect(response.numberReturned).toBeLessThanOrEqual(10);
    });
  });

  describe('Invalid Cursor', () => {
    it('rejects invalid cursor format', async () => {
      await expect(
        fetchJson('/observations?limit=100&cursor=invalid!!!')
      ).rejects.toThrow('400');
    });

    it('rejects expired cursor', async () => {
      await expect(
        fetchJson('/observations?limit=100&cursor=expired_token')
      ).rejects.toThrow('400');
    });
  });

  describe('Metadata Validation', () => {
    it('handles absent numberMatched gracefully', async () => {
      const response = await fetchJson('/observations?limit=100&cursor=abc123');

      // numberMatched is optional in cursor mode
      if (response.numberMatched === undefined) {
        expect(response.numberReturned).toBeDefined();
      }
    });

    it('validates numberReturned matches feature count', async () => {
      const response = await fetchJson('/observations?limit=100');

      expect(response.numberReturned).toBe(response.features.length);
    });
  });

  describe('Large Dataset Streaming', () => {
    it('paginates through 1000+ items', async () => {
      let allItems = [];
      let nextLink = { href: '/observations?limit=100' };
      let pageCount = 0;

      while (nextLink && pageCount < 20) {
        // Safety limit
        const response = await fetchJson(nextLink.href);
        allItems.push(...response.features);

        nextLink = response.links?.find((l) => l.rel === 'next');
        pageCount++;
      }

      expect(allItems.length).toBeGreaterThan(1000);

      // Check no duplicates
      const ids = allItems.map((item) => item.id);
      const uniqueIds = new Set(ids);
      expect(uniqueIds.size).toBe(ids.length);
    });
  });
});
```

### 5.3 Pagination + Filtering Test Template

```typescript
describe('Pagination with Filtering', () => {
  it('paginates with bbox filter', async () => {
    const url = builder.getSystems({
      bbox: [-10, -10, 10, 10],
      limit: 50,
      offset: 0,
    });
    parseAndValidateUrl(url, {
      pathname: '/systems',
      query: {
        bbox: '-10,-10,10,10',
        limit: '50',
        offset: '0',
      },
    });
  });

  it('paginates with datetime filter', async () => {
    const url = builder.getSystems({
      datetime: '2024-01-01/2024-12-31',
      limit: 100,
    });
    parseAndValidateUrl(url, {
      pathname: '/systems',
      query: {
        datetime: '2024-01-01/2024-12-31',
        limit: '100',
      },
    });
  });

  it('paginates with phenomenonTime filter', async () => {
    const url = builder.getObservations('ds1', {
      phenomenonTime: '2024-01-01/..',
      limit: 1000,
      cursor: 'abc123',
    });
    parseAndValidateUrl(url, {
      pathname: '/datastreams/ds1/observations',
      query: {
        phenomenonTime: '2024-01-01/..',
        limit: '1000',
        cursor: 'abc123',
      },
    });
  });

  it('paginates with parent filter', async () => {
    const url = builder.getSystems({
      parent: 'sys123',
      limit: 20,
      offset: 0,
    });
    parseAndValidateUrl(url, {
      pathname: '/systems',
      query: {
        parent: 'sys123',
        limit: '20',
        offset: '0',
      },
    });
  });

  it('paginates with multiple filters', async () => {
    const url = builder.getSystems({
      bbox: [-180, -90, 180, 90],
      datetime: '2024-01-01/..',
      systemType: 'sensor',
      limit: 50,
    });
    parseAndValidateUrl(url, {
      pathname: '/systems',
      query: {
        bbox: '-180,-90,180,90',
        datetime: '2024-01-01/..',
        systemType: 'sensor',
        limit: '50',
      },
    });
  });

  it('returns empty page when filters yield no results', async () => {
    const response = await fetchJson('/systems?bbox=0,0,0,0&limit=10');

    expect(response.features).toEqual([]);
    expect(response.numberMatched).toBe(0);
    expect(response.numberReturned).toBe(0);
  });

  it('returns single page when filters reduce results', async () => {
    const response = await fetchJson('/systems?parent=sys123&limit=10');

    expect(response.features.length).toBeLessThanOrEqual(10);

    if (response.features.length < 10) {
      const nextLink = response.links?.find((l) => l.rel === 'next');
      expect(nextLink).toBeUndefined();
    }
  });
});
```

### 5.4 Link Parsing Utility Tests

> ✅ **REVIEW NOTICE: Strongest Section — Correctly Client-Oriented**
>
> This section is the model for how all pagination tests in this document should work. These tests exercise client utility functions (`extractNextLink()`, `extractCursor()`, `isLastPage()`) with deterministic input data and assert client transformation outputs. No `fetchJson()`, no fixture content assertions, no server behavior testing. The `fetchJson()` tests in Sections 5.1-5.2 should be rewritten to follow this pattern: feed fixture → call client function → assert client output.

```typescript
describe('Pagination Link Utilities', () => {
  describe('extractNextLink()', () => {
    it('extracts next link from response', () => {
      const response = {
        links: [
          { rel: 'self', href: '/systems?limit=10&offset=0' },
          { rel: 'next', href: '/systems?limit=10&offset=10' },
        ],
      };

      const nextLink = extractNextLink(response);
      expect(nextLink).toBeDefined();
      expect(nextLink.href).toBe('/systems?limit=10&offset=10');
    });

    it('returns undefined when no next link', () => {
      const response = {
        links: [{ rel: 'self', href: '/systems?limit=10&offset=190' }],
      };

      const nextLink = extractNextLink(response);
      expect(nextLink).toBeUndefined();
    });
  });

  describe('extractCursor()', () => {
    it('extracts cursor from next link', () => {
      const nextLink = {
        rel: 'next',
        href: '/observations?limit=100&cursor=eyJpZCI6MTAwfQ==',
      };

      const cursor = extractCursor(nextLink);
      expect(cursor).toBe('eyJpZCI6MTAwfQ==');
    });

    it('returns undefined when no cursor in link', () => {
      const nextLink = {
        rel: 'next',
        href: '/systems?limit=10&offset=10',
      };

      const cursor = extractCursor(nextLink);
      expect(cursor).toBeUndefined();
    });
  });

  describe('isLastPage()', () => {
    it('detects last page when no next link', () => {
      const response = {
        links: [
          { rel: 'self', href: '/systems?limit=10&offset=190' },
          { rel: 'prev', href: '/systems?limit=10&offset=180' },
        ],
      };

      expect(isLastPage(response)).toBe(true);
    });

    it('detects not last page when next link present', () => {
      const response = {
        links: [
          { rel: 'self', href: '/systems?limit=10&offset=0' },
          { rel: 'next', href: '/systems?limit=10&offset=10' },
        ],
      };

      expect(isLastPage(response)).toBe(false);
    });
  });
});
```

---

## 6. Test Organization

### 6.1 File Structure

```
src/ogc-api/csapi/
  pagination-utils.ts              # Pagination utility functions
  pagination-utils.spec.ts         # Utility tests

src/ogc-api/csapi/__tests__/
  pagination-offset.spec.ts        # Offset pagination tests
  pagination-cursor.spec.ts        # Cursor pagination tests
  pagination-filtering.spec.ts     # Pagination + filtering tests
  pagination-links.spec.ts         # Link parsing tests
```

### 6.2 Test Counts

| Test File                      | Test Scenarios | Lines of Code (est.) |
| ------------------------------ | -------------- | -------------------- |
| `pagination-offset.spec.ts`    | 15             | ~400                 |
| `pagination-cursor.spec.ts`    | 12             | ~350                 |
| `pagination-filtering.spec.ts` | 10             | ~300                 |
| `pagination-links.spec.ts`     | 8              | ~250                 |
| `pagination-utils.spec.ts`     | 8              | ~200                 |
| **TOTAL**                      | **53**         | **~1,500**           |

### 6.3 Integration with Section 13

**Section 13 Resource Method Tests:**

- Include 1 basic pagination test per resource type (9 total)
- Test: `applies pagination parameters`
- Validates limit + offset in query string

**Section 23 Pagination Tests:**

- Dedicated pagination test suite (53 scenarios)
- Covers offset and cursor modes
- Covers edge cases, filtering, link parsing
- Tests pagination behavior, not just URL construction

**No Duplication:** Section 13 tests basic parameter passing, Section 23 tests pagination behavior

---

## 7. Implementation Estimates

### 7.1 Fixture Creation

| Task                       | Est. Time     | Priority |
| -------------------------- | ------------- | -------- |
| Large dataset fixtures (2) | 1-2 hours     | HIGH     |
| Multi-page responses (6)   | 2-3 hours     | HIGH     |
| Edge case fixtures (6)     | 1-2 hours     | MEDIUM   |
| Error responses (4)        | 30 minutes    | MEDIUM   |
| Filtering fixtures (2)     | 30 minutes    | LOW      |
| **TOTAL**                  | **5-8 hours** | -        |

### 7.2 Test Implementation

| Test File                      | Est. Time       | Priority |
| ------------------------------ | --------------- | -------- |
| `pagination-offset.spec.ts`    | 3-4 hours       | HIGH     |
| `pagination-cursor.spec.ts`    | 3-4 hours       | HIGH     |
| `pagination-filtering.spec.ts` | 2-3 hours       | MEDIUM   |
| `pagination-links.spec.ts`     | 2-3 hours       | MEDIUM   |
| `pagination-utils.spec.ts`     | 1-2 hours       | LOW      |
| **TOTAL**                      | **11-16 hours** | -        |

### 7.3 Utility Functions

| Function                               | Est. Time   | Priority |
| -------------------------------------- | ----------- | -------- |
| `extractNextLink(response)`            | 30 minutes  | HIGH     |
| `extractPrevLink(response)`            | 15 minutes  | MEDIUM   |
| `extractCursor(link)`                  | 30 minutes  | HIGH     |
| `isLastPage(response)`                 | 15 minutes  | MEDIUM   |
| `validatePaginationMetadata(response)` | 30 minutes  | LOW      |
| **TOTAL**                              | **2 hours** | -        |

### 7.4 Total Effort

| Phase               | Est. Time                 |
| ------------------- | ------------------------- |
| Fixture Creation    | 5-8 hours                 |
| Test Implementation | 11-16 hours               |
| Utility Functions   | 2 hours                   |
| Documentation       | 1-2 hours (this document) |
| **TOTAL**           | **19-28 hours**           |

---

## 8. Key Recommendations

### 8.1 Prioritization

**HIGH Priority (Implement First):**

1. Offset pagination tests (basic navigation, boundaries)
2. Cursor pagination tests (basic navigation, cursor extraction)
3. Large dataset fixtures (200 systems, 1000 observations)
4. Multi-page response fixtures (pages 1, 2, last)
5. Link parsing utilities (`extractNextLink`, `extractCursor`)

**MEDIUM Priority (Implement Second):** 6. Pagination + filtering tests 7. Edge case fixtures and tests 8. Part 2 limit validation tests 9. Metadata validation tests

**LOW Priority (Implement Last):** 10. Error response tests 11. Pagination utility validation functions 12. Documentation and examples

### 8.2 Testing Approach

**Unit Tests:** URL construction with pagination parameters (covered in Section 13)

**Integration Tests:** Multi-page navigation, link following, cursor extraction (this section)

**Mock Strategy:** Use fixture-based mocking (like EDR PR #114)

- Mock fetch to return fixture responses
- Map URLs to fixture files based on pagination parameters
- Test pagination logic without real server

### 8.3 Reusable Patterns

**Link Extraction:**

```typescript
function extractNextLink(response: FeatureCollection): Link | undefined {
  return response.links?.find((l) => l.rel === 'next');
}
```

**Cursor Extraction:**

```typescript
function extractCursor(link: Link): string | undefined {
  const url = new URL(link.href);
  return url.searchParams.get('cursor') ?? undefined;
}
```

**Pagination Loop:**

```typescript
async function* paginateAll<T>(
  initialUrl: string,
  fetchFn: (url: string) => Promise<FeatureCollection>
): AsyncGenerator<T> {
  let url: string | undefined = initialUrl;

  while (url) {
    const response = await fetchFn(url);
    yield* response.features as T[];

    const nextLink = extractNextLink(response);
    url = nextLink?.href;
  }
}
```

---

## 9. Success Criteria Validation

- [x] **Both pagination modes are fully specified (offset and cursor)** ✅
- [x] **All pagination edge cases are identified** ✅ (58 scenarios)
- [x] **Pagination + query parameter interactions are defined** ✅ (10 filtering scenarios)
- [x] **Multi-page fixtures are designed** ✅ (20 fixtures documented)
- [x] **Pagination test patterns are documented** ✅ (5 test templates)
- [x] **Link parsing test approach is defined** ✅ (8 link parsing scenarios)
- [x] **Deliverable document is peer-reviewed** ⏳ (awaiting review)

---

## 10. References

**CSAPI Specifications:**

- OGC API - Connected Systems Part 1: Clause 7.15.7 (Pagination)
- OGC API - Connected Systems Part 2: Pagination (limit 1-10,000)
- OGC API - Features Part 1: Clause 7.15.7 (Pagination pattern)

**Related Research:**

- Section 01: EDR Test Blueprint (upstream pagination patterns)
- Section 02: Test Pattern Survey (pagination test examples)
- Section 13: Resource Method Testing (basic pagination tests)
- Section 14: Integration Test Workflow (pagination state validation)

**Implementation Guides:**

- `csapi-implementation-guide.md`: Pagination usage examples
- `csapi-query-parameters.md`: Pagination parameter specifications
- `csapi-part1-requirements.md`: Offset-based pagination
- `csapi-part2-requirements.md`: Cursor-based pagination
- `csapi-opensensorhub-analysis.md`: Pagination implementation patterns
- `csapi-52north-analysis.md`: Link generation patterns

**Code Examples:**

- `examples/stac-query.js`: Link following for pagination
- `src/stac/endpoint.ts`: Pagination implementation patterns

---

## Appendix A: Pagination Parameter Matrix

| Parameter  | Part 1 | Part 2 | Type    | Range                                        | Default                      | Required |
| ---------- | ------ | ------ | ------- | -------------------------------------------- | ---------------------------- | -------- |
| **limit**  | ✅     | ✅     | Integer | Part 1: 1 to impl-max<br>Part 2: 1 to 10,000 | Part 1: 10-100<br>Part 2: 10 | No       |
| **offset** | ✅     | ✅     | Integer | ≥ 0                                          | 0                            | No       |
| **cursor** | ❌     | ✅     | String  | Opaque                                       | N/A                          | No       |

---

## Appendix B: Link Relation Matrix

| Link Relation | Offset Mode | Cursor Mode | Description                                         |
| ------------- | ----------- | ----------- | --------------------------------------------------- |
| **next**      | ✅          | ✅          | Next page URL (offset or cursor)                    |
| **prev**      | ✅          | ❌          | Previous page URL (offset only)                     |
| **first**     | ✅          | ❌          | First page URL (offset only)                        |
| **last**      | ✅          | ❌          | Last page URL (offset only, requires numberMatched) |
| **self**      | ✅          | ✅          | Current page URL                                    |

---

## Appendix C: Pagination Workflow Diagrams

### Offset-Based Pagination Workflow

```
User Request
    ↓
GET /systems?limit=10&offset=0
    ↓
Server Response (Page 1)
    ├── features: [item1...item10]
    ├── numberMatched: 200
    ├── numberReturned: 10
    └── links:
        ├── next: /systems?limit=10&offset=10
        ├── first: /systems?limit=10&offset=0
        └── last: /systems?limit=10&offset=190
    ↓
User Follows next Link
    ↓
GET /systems?limit=10&offset=10
    ↓
Server Response (Page 2)
    ├── features: [item11...item20]
    ├── numberMatched: 200
    ├── numberReturned: 10
    └── links:
        ├── prev: /systems?limit=10&offset=0
        ├── next: /systems?limit=10&offset=20
        ├── first: /systems?limit=10&offset=0
        └── last: /systems?limit=10&offset=190
```

### Cursor-Based Pagination Workflow

```
User Request
    ↓
GET /observations?limit=100
    ↓
Server Response (Page 1)
    ├── features: [obs1...obs100]
    ├── numberMatched: 1000 (optional)
    ├── numberReturned: 100
    └── links:
        ├── self: /observations?limit=100
        └── next: /observations?limit=100&cursor=eyJpZCI6MTAwfQ==
    ↓
Extract Cursor from next Link
    ↓
cursor = "eyJpZCI6MTAwfQ=="
    ↓
User Request with Cursor
    ↓
GET /observations?limit=100&cursor=eyJpZCI6MTAwfQ==
    ↓
Server Response (Page 2)
    ├── features: [obs101...obs200]
    ├── numberReturned: 100
    └── links:
        ├── self: /observations?limit=100&cursor=eyJpZCI6MTAwfQ==
        └── next: /observations?limit=100&cursor=eyJpZCI6MjAwfQ==
    ↓
Continue until no next link (last page)
```

---

**Document Status:** ✅ Complete  
**Last Updated:** 2024  
**Next Review:** After peer review and feedback incorporation
