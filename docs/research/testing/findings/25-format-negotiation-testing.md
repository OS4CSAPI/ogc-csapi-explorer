# Section 25: Format Negotiation Testing Strategy - FINDINGS

> ⚠️ **REVIEW NOTICE — HIGH (H2): 45 Test Scenarios Test Server HTTP Response Behavior, Not Client Code**
>
> **Phase 2E Review | Issues: H2, H9, M2, M3 | Anti-Patterns: AP1**
>
> This document is ~60% client-oriented. Section 4 (scenarios 1-45) is structured as HTTP request → expected HTTP response assertions (`GET /systems/sys123?f=json → Expected: 200 OK, Content-Type: application/json`). These test what the SERVER returns, not what the CLIENT constructs or parses. The document itself notes the client implements format selection in "~13 lines of code" — 50 test scenarios for 13 lines is extreme over-engineering.
>
> **What's usable:** URL construction with `f=` parameter (Section 4.4 URL encoding), format constant mapping, `FormatValidator` client-side pre-validation (Section 6.1), fixture design patterns (Section 7), format advertisement discovery (Section 5).
>
> **What must be trimmed:** Server HTTP response scenarios (Sections 4.1-4.3), Accept header tests for unused feature (Section 4.2), `ResponseValidator` that checks server Content-Type correctness (Section 6.2), format precedence rules that describe server behavior (Section 3).
>
> **Target:** ~10-15 client-oriented tests: URL construction with `f=` parameter, URL encoding of `+` as `%2B`, format constant mapping, client-side format validation.
>
> See also: [Phase 2E Review Report](../review/phase-2e-advanced-scenarios-category.md)

> **📋 A1 FINDING C4-M1 — Scope Reduction Audit**
>
> **Problem:** ~1,800 LOC / 50 test scenarios for ~13 lines of implementation. 45 of 50 scenarios (90%) test server HTTP response behavior (AP3), not client code.
>
> **Actionable client scenarios (5 of 50):** Only §4.4 scenarios 36-40 (URL encoding) and §6.1 (`FormatValidator` pre-validation) test actual client behavior. These should be implemented.
>
> **Server-behavior scenarios (45 of 50) — DO NOT IMPLEMENT:**
>
> - §4.1 scenarios 1-20: Assert server returns correct `Content-Type` for `f=` values
> - §4.2 scenarios 21-30: Test Accept header behavior the client doesn't use
> - §4.3 scenarios 31-35: Test server default format selection
> - §4.5 scenarios 41-45: Test server error responses (406, 400)
> - §6.2 `ResponseValidator`: Validates server set correct `Content-Type`
> - §3 Format precedence rules: Describe server resolution logic
>
> **Retained as reference:** The flagged sections document server behavior useful for fixture design and understanding API contracts, but must not become test assertions.
>
> See also: [A1 Finding C1-M3](#a1-format-detection-fallback-scenarios) — client-side scenarios that SHOULD be tested (document structure analysis fallback)

**Research Plan:** [Research Plan 25: Format Negotiation Testing Strategy](../research-plans/25-format-negotiation-testing.md)

**Research Questions:** 6 core questions about testing Accept header format negotiation, query parameter format selection (f=geojson), format discovery via links, CSAPI-supported media types, format precedence (Accept vs query param), and handling unsupported formats

**Methodology:** 6-phase systematic analysis (Phase 1: Format Specification Analysis extracting CSAPI media types and precedence rules → Phase 2: Upstream Format Testing Analysis of existing patterns → Phase 3: Test Scenario Design for 50+ scenarios across negotiation methods → Phase 4: Media Type Matrix Creation mapping formats to resources → Phase 5: Fixture Design for Accept headers and format-specific responses → Phase 6: Synthesis into comprehensive format negotiation testing strategy)

**Research Time:** 4.0 hours (February 6, 2026)

**Primary Source(s):**

- [Format Negotiation Architecture](../../../architecture/responses/format-negotiation.md)
- [Format Requirements](../../requirements/format-requirements.md)
- [CSAPI Part 1 Specification](https://docs.ogc.org/is/23-001/23-001.html) (media type definitions)
- [CSAPI Part 2 Specification](https://docs.ogc.org/is/23-002/23-002.html) (media type definitions)
- [CSAPI Implementation Guide](../../../planning/csapi-implementation-guide.md)

**Supporting Resources:**

- [HTTP Content Negotiation (RFC 7231)](https://datatracker.ietf.org/doc/html/rfc7231#section-5.3)
- [OGC API - Common](https://docs.ogc.org/is/19-072/19-072.html) (format negotiation patterns)
- Section 8: [CSAPI Specification Test Requirements](08-csapi-specification-test-requirements.md) (format specifications)
- Section 24: [Query Parameter Combination Testing](24-query-parameter-combination-testing.md) (f= parameter)

**Document Purpose:** Defines testing strategy for 7 CSAPI media types with 3 format negotiation methods (query parameter f= as primary, Accept header as fallback, server default), format precedence rules (f > Accept > default > 406), and 40+ test scenarios covering format validation, URL encoding, and error handling

---

## Executive Summary

CSAPI supports **7 media types** across Parts 1 and 2, with format negotiation through query parameters (`f`) taking precedence over Accept headers. Format selection is simple and follows OGC API - Common conventions.

This document defines a comprehensive testing strategy covering:

- 7 media types with resource applicability matrix
- 3 format negotiation methods (query parameter, Accept header, link-based)
- Format precedence rules (f > Accept > default)
- 40+ test scenarios across negotiation methods
- Format validation and error handling patterns
- Fixture requirements for all formats

### Key Findings

- **7 Media Types:** JSON, GeoJSON, SensorML, SWE Common (JSON, Text, Binary), URI-List
- **3 Negotiation Methods:** Query parameter (`f`), Accept header, link relations
- **Precedence:** f parameter > Accept header > server default > 406
- **Testing Strategy:** Focus on query parameter (primary), Accept header (fallback), error handling (406)
- **No Complex Negotiation:** No quality values, no link-based selection, no custom Accept headers
- **Simple Implementation:** ~13 lines of code, follows EDR pattern exactly

---

## 1. Media Type Inventory

### 1.1 Complete Media Type List (7 Types)

#### Part 1: Core Resources Media Types

| Media Type               | Standard        | Resources                                          | Purpose                           | Status              |
| ------------------------ | --------------- | -------------------------------------------------- | --------------------------------- | ------------------- |
| **application/json**     | JSON (ECMA-404) | All 9 resources                                    | Base JSON representation          | REQUIRED            |
| **application/geo+json** | RFC 7946        | Systems, Deployments, Procedures, SamplingFeatures | GeoJSON Feature/FeatureCollection | REQUIRED (spatial)  |
| **application/sml+json** | SensorML 3.0    | Systems, Procedures                                | System/procedure metadata         | REQUIRED (metadata) |
| **text/uri-list**        | RFC 2483        | Collection additions                               | URI list (one per line)           | OPTIONAL            |

#### Part 2: Dynamic Data Media Types

| Media Type                 | Standard        | Resources                                                 | Purpose                           | Status   |
| -------------------------- | --------------- | --------------------------------------------------------- | --------------------------------- | -------- |
| **application/json**       | JSON (ECMA-404) | DataStreams, Observations, ControlStreams, Commands, etc. | Base JSON representation          | REQUIRED |
| **application/swe+json**   | SWE Common 3.0  | Observations, Commands, Schemas                           | SWE Common JSON encoding          | OPTIONAL |
| **application/swe+text**   | SWE Common 3.0  | Observations, Commands                                    | CSV/DSV encoding (2-5x smaller)   | OPTIONAL |
| **application/swe+binary** | SWE Common 3.0  | Observations, Commands                                    | Binary encoding (10-100x smaller) | OPTIONAL |

**Note:** HTML (`text/html`) and JSON-LD (`application/ld+json`) may also be supported but are not part of core CSAPI requirements.

### 1.2 Media Type Characteristics

| Media Type             | Binary | Human-Readable | Requires Schema  | Size            | Compression    |
| ---------------------- | ------ | -------------- | ---------------- | --------------- | -------------- |
| application/json       | No     | Yes            | No               | 100% (baseline) | High (verbose) |
| application/geo+json   | No     | Yes            | No               | ~100%           | High (verbose) |
| application/sml+json   | No     | Yes            | Yes (SensorML)   | ~100%           | High (verbose) |
| application/swe+json   | No     | Yes            | Yes (SWE Common) | ~70-80%         | Medium         |
| application/swe+text   | No     | Yes            | Yes (SWE Common) | ~20-50%         | Medium         |
| application/swe+binary | Yes    | No             | Yes (SWE Common) | ~1-10%          | Low            |
| text/uri-list          | No     | Yes            | No               | ~50%            | Medium         |

### 1.3 Resource-Format Matrix

| Resource                 | JSON | GeoJSON | SensorML | SWE+JSON | SWE+Text | SWE+Binary | URI-List |
| ------------------------ | ---- | ------- | -------- | -------- | -------- | ---------- | -------- |
| **Systems**              | ✅   | ✅      | ✅       | ❌       | ❌       | ❌         | ❌       |
| **Deployments**          | ✅   | ✅      | ❌       | ❌       | ❌       | ❌         | ❌       |
| **Procedures**           | ✅   | ✅      | ✅       | ❌       | ❌       | ❌         | ❌       |
| **SamplingFeatures**     | ✅   | ✅      | ❌       | ❌       | ❌       | ❌         | ❌       |
| **Properties**           | ✅   | ❌      | ❌       | ❌       | ❌       | ❌         | ❌       |
| **DataStreams**          | ✅   | ❌      | ❌       | ❌       | ❌       | ❌         | ❌       |
| **Observations**         | ✅   | ❌      | ❌       | ✅\*     | ✅\*     | ✅\*       | ❌       |
| **ControlStreams**       | ✅   | ❌      | ❌       | ❌       | ❌       | ❌         | ❌       |
| **Commands**             | ✅   | ❌      | ❌       | ✅\*     | ✅\*     | ✅\*       | ❌       |
| **Collection Additions** | ❌   | ❌      | ❌       | ❌       | ❌       | ❌         | ✅       |

**Note:** \* = Optional, advertised in DataStream/ControlStream `formats` property

---

## 2. Format Negotiation Methods

### 2.1 Query Parameter Method (Primary)

**Parameters:**

- **`f`** - Short format name (Part 1) or full media type (Part 2)
- **`format`** - Full media type (alternative to `f`)

**Part 1 Short Format Names:**

```
?f=json      → application/json
?f=geojson   → application/geo+json
?f=sml       → application/sml+json
```

**Part 2 Full Media Types:**

```
?f=application/json
?f=application/swe+json
?f=application/swe+text
?f=application/swe+binary
```

**URL Encoding:**

- Plus character (`+`) MUST be URL-encoded as `%2B`
- Examples:
  ```
  ?f=application/swe%2Bjson
  ?f=application/swe%2Btext
  ?f=application/swe%2Bbinary
  ```

**Implementation:**

```typescript
// Query parameter method
const url = builder.getSystems({ f: 'geojson' });
// → /systems?f=geojson

const url = builder.getObservations('ds123', {
  f: 'application/swe+binary',
});
// → /datastreams/ds123/observations?f=application%2Fswe%2Bbinary
```

**Testing Focus:**

- Valid format names (json, geojson, sml)
- Valid media types (application/swe+json, etc.)
- URL encoding of + character
- Invalid format names
- Unsupported formats (406 Not Acceptable)

### 2.2 Accept Header Method (Fallback)

**Standard HTTP Content Negotiation:**

```http
GET /systems/sys123
Accept: application/geo+json

HTTP/1.1 200 OK
Content-Type: application/geo+json; charset=utf-8
```

**Multiple Accept Values:**

```http
GET /systems/sys123
Accept: application/geo+json, application/json;q=0.8
```

**Quality Values (q):**

- RFC 9110 quality value mechanism
- Server selects best match based on weights
- **Not required for client library** (query parameter preferred)

**Implementation:**

```typescript
// Accept header method (NOT used by CSAPI client)
// Included for completeness only
const response = await fetch('/systems/sys123', {
  headers: { Accept: 'application/geo+json' },
});
```

**Testing Focus:**

- Accept header respected when no query parameter
- Query parameter overrides Accept header
- Quality values (optional, not required)
- Wildcard Accept: `*/*`
- Default format when no Accept header

### 2.3 Link-Based Format Discovery (Not Used)

**Link Relations with Media Types:**

```json
{
  "links": [
    {
      "rel": "alternate",
      "href": "https://api.example.org/systems/sys123?f=geojson",
      "type": "application/geo+json",
      "title": "GeoJSON representation"
    },
    {
      "rel": "alternate",
      "href": "https://api.example.org/systems/sys123?f=sml",
      "type": "application/sml+json",
      "title": "SensorML representation"
    }
  ]
}
```

**CSAPI Client Strategy:**

- **Does NOT use link-based format selection**
- Follows EDR pattern: query parameter only
- Links are informational only (for human consumption)

**Testing Focus:**

- No testing required (link-based selection not implemented)
- Links validated in Section 13 (Resource Method Testing)

### 2.4 Content-Type Response Header

**Server Indicates Format:**

```http
HTTP/1.1 200 OK
Content-Type: application/geo+json; charset=utf-8

{
  "type": "Feature",
  ...
}
```

**Charset Parameter:**

- JSON formats: `charset=utf-8` (SHOULD be included)
- Binary formats: No charset parameter

**Testing Focus:**

- Verify Content-Type matches requested format
- Verify charset=utf-8 for JSON formats
- Verify no charset for binary formats
- Verify Content-Type parsing

---

## 3. Format Precedence Rules

> ⚠️ **REVIEW NOTICE (M2): Format Precedence Rules Describe Server Behavior, Not Client Logic**
>
> Sections 3.1-3.5 describe how the SERVER resolves format precedence ("Query parameter overrides Accept header", "Server returns default format", "406 Not Acceptable"). The client doesn't implement precedence — it sends `f=` and accepts whatever comes back. These rules are useful as reference context for understanding server behavior, but should not be the basis for client test assertions. Client tests should verify: the `f=` parameter is correctly appended to URLs, and the client handles whatever Content-Type the server returns.

### 3.1 Precedence Order

```
Query Parameter (f/format)
  ↓ (if not specified)
Accept Header
  ↓ (if not specified)
Server Default Format
  ↓ (if format not supported)
406 Not Acceptable
```

### 3.2 Query Parameter Takes Precedence

**Test Case:**

```http
GET /systems/sys123?f=sml
Accept: application/geo+json

HTTP/1.1 200 OK
Content-Type: application/sml+json
```

**Result:** Query parameter `f=sml` overrides Accept header `application/geo+json`

### 3.3 Accept Header Fallback

**Test Case:**

```http
GET /systems/sys123
Accept: application/geo+json

HTTP/1.1 200 OK
Content-Type: application/geo+json
```

**Result:** Accept header used when no query parameter

### 3.4 Server Default Format

**Test Case:**

```http
GET /systems/sys123

HTTP/1.1 200 OK
Content-Type: application/geo+json
```

**Result:** Server returns default format (typically GeoJSON for spatial, JSON for non-spatial)

**Default Formats by Resource:**
| Resource | Default Format | Rationale |
|----------|----------------|-----------|
| Systems | application/geo+json | Spatial resource |
| Deployments | application/geo+json | Spatial resource |
| Procedures | application/geo+json | May have geometry |
| SamplingFeatures | application/geo+json | Spatial resource |
| Properties | application/json | Non-spatial |
| DataStreams | application/json | Non-spatial metadata |
| Observations | application/json | Fallback (advertised formats vary) |
| ControlStreams | application/json | Non-spatial metadata |
| Commands | application/json | Non-spatial |

### 3.5 Unsupported Format (406)

**Test Case:**

```http
GET /systems/sys123?f=xml

HTTP/1.1 406 Not Acceptable
Content-Type: application/json

{
  "code": "InvalidParameterValue",
  "description": "The format 'xml' is not supported. Supported formats: json, geojson, sml."
}
```

**Result:** Server returns 406 Not Acceptable with error details

---

## 4. Test Scenario Design

### 4.1 Query Parameter Test Scenarios (20 scenarios)

> ⚠️ **REVIEW NOTICE (H2): Server HTTP Response Assertions**
>
> These 20 scenarios test what the SERVER returns (`Expected: 200 OK, Content-Type: application/json`) — not what the client constructs. Client tests should verify: `builder.getSystems({ format: 'json' })` produces a URL with `?f=json`. Whether the server returns 200 with the correct Content-Type is server compliance testing. The "Invalid Format" scenarios (16-20) testing server 400/406 responses are also server behavior — only client-side pre-validation (e.g., `FormatValidator` rejecting unknown formats before sending) belongs in client tests.

#### Valid Format Names (Part 1) - 10 scenarios

1. **f=json (Systems)**

   ```
   GET /systems/sys123?f=json
   Expected: 200 OK, Content-Type: application/json
   ```

2. **f=geojson (Systems)**

   ```
   GET /systems/sys123?f=geojson
   Expected: 200 OK, Content-Type: application/geo+json
   ```

3. **f=sml (Systems)**

   ```
   GET /systems/sys123?f=sml
   Expected: 200 OK, Content-Type: application/sml+json
   ```

4. **f=geojson (Deployments)**

   ```
   GET /deployments/dep123?f=geojson
   Expected: 200 OK, Content-Type: application/geo+json
   ```

5. **f=sml (Procedures)**

   ```
   GET /procedures/proc123?f=sml
   Expected: 200 OK, Content-Type: application/sml+json
   ```

6. **f=json (Properties)**

   ```
   GET /properties/prop123?f=json
   Expected: 200 OK, Content-Type: application/json
   ```

7. **f=geojson (Systems collection)**

   ```
   GET /systems?f=geojson&limit=10
   Expected: 200 OK, Content-Type: application/geo+json, FeatureCollection
   ```

8. **f=json (DataStreams)**

   ```
   GET /datastreams/ds123?f=json
   Expected: 200 OK, Content-Type: application/json
   ```

9. **format=application/geo+json (full media type)**

   ```
   GET /systems/sys123?format=application/geo+json
   Expected: 200 OK, Content-Type: application/geo+json
   ```

10. **format=application/sml+json (full media type)**
    ```
    GET /systems/sys123?format=application/sml+json
    Expected: 200 OK, Content-Type: application/sml+json
    ```

#### Valid Format Names (Part 2) - 5 scenarios

11. **f=application/json (Observations)**

    ```
    GET /observations/obs123?f=application/json
    Expected: 200 OK, Content-Type: application/json
    ```

12. **f=application/swe+json (Observations)**

    ```
    GET /observations/obs123?f=application/swe%2Bjson
    Expected: 200 OK, Content-Type: application/swe+json
    ```

13. **f=application/swe+text (Observations)**

    ```
    GET /observations/obs123?f=application/swe%2Btext
    Expected: 200 OK, Content-Type: application/swe+text
    ```

14. **f=application/swe+binary (Observations)**

    ```
    GET /observations/obs123?f=application/swe%2Bbinary
    Expected: 200 OK, Content-Type: application/swe+binary
    ```

15. **f=application/swe+json (Commands)**
    ```
    GET /commands/cmd123?f=application/swe%2Bjson
    Expected: 200 OK, Content-Type: application/swe+json
    ```

#### Invalid Format Names - 5 scenarios

16. **f=xml (unsupported format)**

    ```
    GET /systems/sys123?f=xml
    Expected: 406 Not Acceptable
    ```

17. **f=invalid (invalid format name)**

    ```
    GET /systems/sys123?f=invalid
    Expected: 406 Not Acceptable
    ```

18. **f=text/html (HTML format - optional)**

    ```
    GET /systems/sys123?f=text/html
    Expected: 200 OK OR 406 Not Acceptable (server-dependent)
    ```

19. **f=application/swe+json (wrong resource - Systems)**

    ```
    GET /systems/sys123?f=application/swe%2Bjson
    Expected: 406 Not Acceptable (SWE Common only for Observations/Commands)
    ```

20. **f= (empty format parameter)**
    ```
    GET /systems/sys123?f=
    Expected: 400 Bad Request OR use default format
    ```

### 4.2 Accept Header Test Scenarios (10 scenarios)

> ⚠️ **REVIEW NOTICE (H9): Accept Header Tests for Feature Client Doesn't Use**
>
> The document itself notes (Section 2.2) that the CSAPI client does NOT use Accept headers — it uses the `f=` query parameter exclusively. These 10 scenarios test server response to Accept headers, testing a feature the client doesn't implement. All 10 scenarios should be removed entirely. If Accept header support is added in the future, tests should verify the client correctly sets the header, not what the server returns.

#### Accept Header Without Query Parameter - 5 scenarios

21. **Accept: application/geo+json (Systems)**

    ```
    GET /systems/sys123
    Accept: application/geo+json
    Expected: 200 OK, Content-Type: application/geo+json
    ```

22. **Accept: application/sml+json (Systems)**

    ```
    GET /systems/sys123
    Accept: application/sml+json
    Expected: 200 OK, Content-Type: application/sml+json
    ```

23. **Accept: application/json (Systems)**

    ```
    GET /systems/sys123
    Accept: application/json
    Expected: 200 OK, Content-Type: application/json
    ```

24. **Accept: _/_ (wildcard)**

    ```
    GET /systems/sys123
    Accept: */*
    Expected: 200 OK, Content-Type: <server default>
    ```

25. **Accept: application/xml (unsupported)**
    ```
    GET /systems/sys123
    Accept: application/xml
    Expected: 406 Not Acceptable OR use default format
    ```

#### Accept Header With Query Parameter (Precedence) - 5 scenarios

26. **Query parameter overrides Accept header**

    ```
    GET /systems/sys123?f=sml
    Accept: application/geo+json
    Expected: 200 OK, Content-Type: application/sml+json
    ```

27. **Query parameter overrides Accept (different)**

    ```
    GET /systems/sys123?f=json
    Accept: application/sml+json
    Expected: 200 OK, Content-Type: application/json
    ```

28. **Query parameter and Accept both GeoJSON**

    ```
    GET /systems/sys123?f=geojson
    Accept: application/geo+json
    Expected: 200 OK, Content-Type: application/geo+json
    ```

29. **Multiple Accept values with quality (q=)**

    ```
    GET /systems/sys123
    Accept: application/geo+json;q=0.9, application/json;q=0.8
    Expected: 200 OK, Content-Type: application/geo+json (highest q value)
    ```

30. **Query parameter overrides multiple Accept values**
    ```
    GET /systems/sys123?f=sml
    Accept: application/geo+json;q=0.9, application/json;q=0.8
    Expected: 200 OK, Content-Type: application/sml+json
    ```

### 4.3 Default Format Test Scenarios (5 scenarios)

31. **No format specified (Systems - spatial)**

    ```
    GET /systems/sys123
    Expected: 200 OK, Content-Type: application/geo+json (spatial default)
    ```

32. **No format specified (Properties - non-spatial)**

    ```
    GET /properties/prop123
    Expected: 200 OK, Content-Type: application/json (non-spatial default)
    ```

33. **No format specified (DataStreams)**

    ```
    GET /datastreams/ds123
    Expected: 200 OK, Content-Type: application/json
    ```

34. **No format specified (collection)**

    ```
    GET /systems
    Expected: 200 OK, Content-Type: application/geo+json (FeatureCollection)
    ```

35. **No format specified (Observations)**
    ```
    GET /observations/obs123
    Expected: 200 OK, Content-Type: application/json (fallback)
    ```

### 4.4 URL Encoding Test Scenarios (5 scenarios)

> ✅ **REVIEW NOTICE: Strongest Section — Correctly Client-Oriented**
>
> These URL encoding scenarios (36-40) test actual client behavior: how the client encodes `+` as `%2B` in format parameters, handles `/` encoding, and manages edge cases. This is the core client-testable surface for format negotiation. These scenarios plus the `FormatValidator` (Section 6.1) represent the ~10-15 tests that belong in the final implementation.

36. **URL encoding of + in media type**

    ```
    GET /observations/obs123?f=application/swe%2Bjson
    Expected: 200 OK, decoded as application/swe+json
    ```

37. **URL encoding of / in media type**

    ```
    GET /systems/sys123?f=application%2Fgeo%2Bjson
    Expected: 200 OK, decoded as application/geo+json
    ```

38. **Unencoded + in media type (incorrect)**

    ```
    GET /observations/obs123?f=application/swe+json
    Expected: May be misinterpreted (+ decoded as space)
    ```

39. **Multiple encoding scenarios**

    ```
    GET /observations/obs123?f=application%2Fswe%2Btext
    Expected: 200 OK, decoded as application/swe+text
    ```

40. **Charset in format parameter (incorrect usage)**
    ```
    GET /systems/sys123?f=application/json;charset=utf-8
    Expected: 406 Not Acceptable (charset not in query param)
    ```

### 4.5 Error Handling Test Scenarios (5 scenarios)

41. **406 Not Acceptable - Unsupported format**

    ```
    GET /systems/sys123?f=xml
    Expected: 406 Not Acceptable, error body with supported formats
    ```

42. **406 Not Acceptable - Format for wrong resource**

    ```
    GET /systems/sys123?f=application/swe%2Bbinary
    Expected: 406 Not Acceptable
    ```

43. **406 Not Acceptable - Invalid media type**

    ```
    GET /systems/sys123?f=invalid/format
    Expected: 406 Not Acceptable
    ```

44. **400 Bad Request - Malformed format parameter**

    ```
    GET /systems/sys123?f=application/geo+json&f=application/sml+json
    Expected: 400 Bad Request (duplicate parameter)
    ```

45. **Fallback to default on unsupported Accept**
    ```
    GET /systems/sys123
    Accept: application/xml
    Expected: 200 OK, Content-Type: <default format> (graceful fallback)
    ```

---

## 5. Format Advertisement and Discovery

### 5.1 Part 1: Implicit Advertisement

**No Explicit Formats Property:**

- Part 1 resources do not advertise supported formats in resource representation
- Format support discovered through API metadata or trial-and-error
- Standard formats (JSON, GeoJSON, SensorML) are expected

**Discovery Pattern:**

```typescript
// Try format, handle 406 error
try {
  const system = builder.getSystems('sys123', { f: 'sml' });
} catch (error) {
  if (error.status === 406) {
    // Fall back to default format
    const system = builder.getSystems('sys123');
  }
}
```

### 5.2 Part 2: Explicit Advertisement

**DataStream/ControlStream `formats` Property:**

```json
{
  "type": "DataStream",
  "id": "ds123",
  "name": "Temperature Sensor",
  "formats": [
    "application/json",
    "application/swe+json",
    "application/swe+binary"
  ]
}
```

**Discovery Pattern:**

```typescript
// Check supported formats before requesting
const datastream = builder.getDataStream('ds123');
if (datastream.formats.includes('application/swe+binary')) {
  const observations = builder.getObservations('ds123', {
    f: 'application/swe+binary',
  });
}
```

**Schema Format Parameters:**

```
GET /datastreams/ds123/schema?obsFormat=application/swe+binary
// Returns schema for binary format

GET /controlstreams/cs456/schema?cmdFormat=application/swe+json
// Returns schema for JSON format
```

### 5.3 Testing Format Advertisement

**Test Scenarios:**

1. **Verify formats property in DataStream**

   ```
   GET /datastreams/ds123
   Expected: Response includes "formats" array
   ```

2. **Verify formats property in ControlStream**

   ```
   GET /controlstreams/cs456
   Expected: Response includes "formats" array
   ```

3. **Request format not in advertised list**

   ```
   GET /datastreams/ds123/observations?f=application/swe+binary
   // If formats = ["application/json", "application/swe+json"]
   Expected: 406 Not Acceptable
   ```

4. **Schema format parameter matches advertised formats**

   ```
   GET /datastreams/ds123/schema?obsFormat=application/swe+binary
   // If formats includes application/swe+binary
   Expected: 200 OK, schema for binary format
   ```

5. **Schema format parameter not in advertised formats**
   ```
   GET /datastreams/ds123/schema?obsFormat=application/swe+binary
   // If formats does NOT include application/swe+binary
   Expected: 400 Bad Request
   ```

---

## 6. Format Validation Patterns

### 6.1 Client-Side Validation (Before Request)

**Validate Format Parameter:**

```typescript
class FormatValidator {
  /**
   * Validate format parameter for Part 1 resources
   */
  static validatePart1Format(format: string, resourceType: string): void {
    const validFormats: Record<string, string[]> = {
      systems: ['json', 'geojson', 'sml'],
      deployments: ['json', 'geojson'],
      procedures: ['json', 'geojson', 'sml'],
      samplingFeatures: ['json', 'geojson'],
      properties: ['json'],
    };

    const allowed = validFormats[resourceType];
    if (!allowed || !allowed.includes(format)) {
      throw new FormatValidationError(
        `Format '${format}' not valid for resource type '${resourceType}'. ` +
          `Valid formats: ${allowed?.join(', ')}`
      );
    }
  }

  /**
   * Validate media type format (full media type string)
   */
  static validateMediaType(mediaType: string): void {
    const validMediaTypes = [
      'application/json',
      'application/geo+json',
      'application/sml+json',
      'application/swe+json',
      'application/swe+text',
      'application/swe+binary',
    ];

    if (!validMediaTypes.includes(mediaType)) {
      throw new FormatValidationError(
        `Invalid media type: ${mediaType}. ` +
          `Valid types: ${validMediaTypes.join(', ')}`
      );
    }
  }

  /**
   * URL-encode format parameter
   */
  static encodeFormat(format: string): string {
    // Encode + as %2B, / as %2F
    return encodeURIComponent(format);
  }
}

class FormatValidationError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'FormatValidationError';
  }
}
```

### 6.2 Server Response Validation

> ⚠️ **REVIEW NOTICE (M3): `ResponseValidator` Tests Server Content-Type Correctness**
>
> This `ResponseValidator` class verifies that the SERVER correctly set `Content-Type` headers matching the requested format. This validates server behavior, not client transformation. In a mocked-fetch test, the fixture's Content-Type is whatever you set it to — asserting it matches the request tests the fixture, not the client. If the client needs to PARSE responses differently based on Content-Type (e.g., JSON vs SML+JSON), test the parser dispatch logic, not whether the server set the header correctly.

**Validate Content-Type Header:**

```typescript
class ResponseValidator {
  /**
   * Verify Content-Type matches requested format
   */
  static validateContentType(
    response: Response,
    requestedFormat: string
  ): void {
    const contentType = response.headers.get('Content-Type');
    if (!contentType) {
      throw new ValidationError('Missing Content-Type header');
    }

    // Map short names to media types
    const formatMap: Record<string, string> = {
      json: 'application/json',
      geojson: 'application/geo+json',
      sml: 'application/sml+json',
    };

    const expectedType = formatMap[requestedFormat] || requestedFormat;
    const actualType = contentType.split(';')[0].trim();

    if (actualType !== expectedType) {
      throw new ValidationError(
        `Content-Type mismatch: expected ${expectedType}, got ${actualType}`
      );
    }
  }

  /**
   * Verify charset for JSON formats
   */
  static validateCharset(response: Response): void {
    const contentType = response.headers.get('Content-Type');
    if (!contentType) return;

    const [mediaType, ...params] = contentType.split(';');
    const isJson = mediaType.includes('json');
    const hasCharset = params.some((p) => p.trim().startsWith('charset='));

    if (isJson && !hasCharset) {
      console.warn('JSON response missing charset parameter');
    }
  }
}

class ValidationError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'ValidationError';
  }
}
```

### 6.3 Test Patterns

**Test Template:**

```typescript
describe('Format Validation', () => {
  describe('Part 1 format validation', () => {
    it('accepts valid format for resource type', () => {
      expect(() => {
        FormatValidator.validatePart1Format('geojson', 'systems');
      }).not.toThrow();
    });

    it('rejects invalid format for resource type', () => {
      expect(() => {
        FormatValidator.validatePart1Format('xml', 'systems');
      }).toThrow(FormatValidationError);
    });

    it('rejects format not applicable to resource type', () => {
      expect(() => {
        FormatValidator.validatePart1Format('sml', 'deployments');
      }).toThrow("Format 'sml' not valid for resource type 'deployments'");
    });
  });

  describe('Media type validation', () => {
    it('accepts valid media type', () => {
      expect(() => {
        FormatValidator.validateMediaType('application/geo+json');
      }).not.toThrow();
    });

    it('rejects invalid media type', () => {
      expect(() => {
        FormatValidator.validateMediaType('application/xml');
      }).toThrow(FormatValidationError);
    });

    it('accepts SWE Common media types', () => {
      expect(() => {
        FormatValidator.validateMediaType('application/swe+json');
        FormatValidator.validateMediaType('application/swe+text');
        FormatValidator.validateMediaType('application/swe+binary');
      }).not.toThrow();
    });
  });

  describe('Format encoding', () => {
    it('encodes + character as %2B', () => {
      const encoded = FormatValidator.encodeFormat('application/swe+json');
      expect(encoded).toBe('application%2Fswe%2Bjson');
    });

    it('encodes / character as %2F', () => {
      const encoded = FormatValidator.encodeFormat('application/geo+json');
      expect(encoded).toBe('application%2Fgeo%2Bjson');
    });
  });
});

describe('Response Validation', () => {
  describe('Content-Type validation', () => {
    it('validates matching Content-Type', () => {
      const response = new Response('{}', {
        headers: { 'Content-Type': 'application/geo+json; charset=utf-8' },
      });

      expect(() => {
        ResponseValidator.validateContentType(response, 'geojson');
      }).not.toThrow();
    });

    it('detects Content-Type mismatch', () => {
      const response = new Response('{}', {
        headers: { 'Content-Type': 'application/json' },
      });

      expect(() => {
        ResponseValidator.validateContentType(response, 'geojson');
      }).toThrow('Content-Type mismatch');
    });

    it('validates full media type', () => {
      const response = new Response('{}', {
        headers: { 'Content-Type': 'application/sml+json' },
      });

      expect(() => {
        ResponseValidator.validateContentType(response, 'application/sml+json');
      }).not.toThrow();
    });
  });

  describe('Charset validation', () => {
    it('warns if charset missing for JSON', () => {
      const consoleSpy = jest.spyOn(console, 'warn');
      const response = new Response('{}', {
        headers: { 'Content-Type': 'application/json' },
      });

      ResponseValidator.validateCharset(response);
      expect(consoleSpy).toHaveBeenCalledWith(
        'JSON response missing charset parameter'
      );
    });

    it('accepts charset=utf-8 for JSON', () => {
      const consoleSpy = jest.spyOn(console, 'warn');
      const response = new Response('{}', {
        headers: { 'Content-Type': 'application/json; charset=utf-8' },
      });

      ResponseValidator.validateCharset(response);
      expect(consoleSpy).not.toHaveBeenCalled();
    });
  });
});

describe('Format Negotiation', () => {
  it('applies format parameter to URL', async () => {
    const url = builder.getSystems('sys123', { f: 'geojson' });
    parseAndValidateUrl(url, {
      pathname: '/systems/sys123',
      query: { f: 'geojson' },
    });
  });

  it('encodes + in format parameter', async () => {
    const url = builder.getObservations('ds123', 'obs123', {
      f: 'application/swe+json',
    });
    parseAndValidateUrl(url, {
      pathname: '/observations/obs123',
      query: { f: 'application/swe%2Bjson' },
    });
  });

  it('handles precedence: query param over Accept header', async () => {
    // Query parameter specified → use query parameter
    // (Accept header not sent by client library)
    const url = builder.getSystems('sys123', { f: 'sml' });
    expect(url).toContain('f=sml');
  });
});
```

---

## 7. Fixture Design

### 7.1 Query String Fixtures

**Valid Format Parameters:**

```typescript
const validQueryStrings = [
  // Part 1 short names
  '?f=json',
  '?f=geojson',
  '?f=sml',
  '?format=application/geo+json',
  '?format=application/sml+json',

  // Part 2 full media types
  '?f=application/json',
  '?f=application/swe%2Bjson',
  '?f=application/swe%2Btext',
  '?f=application/swe%2Bbinary',

  // Combined with other parameters
  '?f=geojson&limit=10',
  '?f=sml&bbox=-180,-90,180,90',
  '?f=application/swe%2Bjson&limit=1000&phenomenonTime=2024-01-01/..',
];
```

**Invalid Format Parameters:**

```typescript
const invalidQueryStrings = [
  '?f=xml', // Unsupported format
  '?f=invalid', // Invalid format name
  '?f=', // Empty format
  '?f=application/swe+json', // Not URL-encoded (incorrect)
  '?f=application/xml', // Unsupported media type
];
```

### 7.2 Accept Header Fixtures

**Valid Accept Headers:**

```typescript
const validAcceptHeaders = {
  'application/geo+json': 'Accept: application/geo+json',
  'application/sml+json': 'Accept: application/sml+json',
  'application/json': 'Accept: application/json',
  wildcard: 'Accept: */*',
  multiple: 'Accept: application/geo+json, application/json;q=0.8',
  'quality-values':
    'Accept: application/geo+json;q=0.9, application/sml+json;q=0.8, application/json;q=0.7',
};
```

**Invalid Accept Headers:**

```typescript
const invalidAcceptHeaders = {
  unsupported: 'Accept: application/xml',
  malformed: 'Accept: invalid-type',
};
```

### 7.3 Response Fixtures

**Successful Responses:**

**GeoJSON Response:**

```json
{
  "type": "Feature",
  "id": "sys123",
  "geometry": {
    "type": "Point",
    "coordinates": [0.0, 0.0]
  },
  "properties": {
    "name": "Weather Station",
    "description": "Temperature and humidity sensor"
  }
}
```

**SensorML Response:**

```json
{
  "type": "PhysicalSystem",
  "id": "sys123",
  "label": "Weather Station",
  "uniqueId": "urn:x-osh:sensor:weatherstation:001",
  "description": "Temperature and humidity monitoring system",
  "capabilities": [
    {
      "name": "Operating Range",
      "type": "CapabilityList"
    }
  ]
}
```

**JSON Response (DataStream):**

```json
{
  "type": "DataStream",
  "id": "ds123",
  "name": "Temperature Measurements",
  "observedProperties": ["http://example.org/properties/temperature"],
  "resultType": "measure",
  "formats": [
    "application/json",
    "application/swe+json",
    "application/swe+binary"
  ]
}
```

**SWE Common JSON Response (Observation):**

```json
{
  "phenomenonTime": "2024-01-15T12:00:00Z",
  "result": 23.5
}
```

**SWE Common Text Response (Observations):**

```
2024-01-15T12:00:00Z,23.5
2024-01-15T12:01:00Z,23.6
2024-01-15T12:02:00Z,23.4
```

**SWE Common Binary Response:**

```
<binary data> (not human-readable)
```

### 7.4 Error Response Fixtures

**406 Not Acceptable:**

```json
{
  "code": "InvalidParameterValue",
  "description": "The format 'xml' is not supported. Supported formats: json, geojson, sml."
}
```

**400 Bad Request (Malformed):**

```json
{
  "code": "InvalidParameterValue",
  "description": "The format parameter value '' is invalid. Must be a non-empty string."
}
```

**406 Not Acceptable (Format for Wrong Resource):**

```json
{
  "code": "InvalidParameterValue",
  "description": "The format 'application/swe+binary' is not applicable to the Systems resource type. Supported formats: json, geojson, sml."
}
```

### 7.5 Fixture Summary

| Fixture Type           | Count  | Description                                              |
| ---------------------- | ------ | -------------------------------------------------------- |
| Valid query strings    | 15     | Format parameter variations                              |
| Invalid query strings  | 5      | Unsupported/malformed formats                            |
| Valid Accept headers   | 6      | Accept header variations                                 |
| Invalid Accept headers | 2      | Unsupported formats                                      |
| Successful responses   | 6      | Format-specific responses (JSON, GeoJSON, SensorML, SWE) |
| Error responses        | 3      | 406 Not Acceptable, 400 Bad Request                      |
| **TOTAL**              | **37** | **37 fixtures**                                          |

---

## 8. Test Organization

### 8.1 File Structure

```
src/ogc-api/csapi/__tests__/
  format-negotiation.spec.ts               # Format negotiation tests
  format-validation.spec.ts                # Format validation tests
  format-encoding.spec.ts                  # URL encoding tests
  format-precedence.spec.ts                # Precedence rule tests
  format-error-handling.spec.ts            # Error handling tests
```

### 8.2 Test Counts

| Test File                       | Test Scenarios | Lines of Code (est.) |
| ------------------------------- | -------------- | -------------------- |
| `format-negotiation.spec.ts`    | 20             | ~600                 |
| `format-validation.spec.ts`     | 10             | ~400                 |
| `format-encoding.spec.ts`       | 5              | ~200                 |
| `format-precedence.spec.ts`     | 10             | ~400                 |
| `format-error-handling.spec.ts` | 5              | ~200                 |
| **TOTAL**                       | **50**         | **~1,800**           |

### 8.3 Integration with Other Sections

**Section 13 (Resource Method Testing):**

- Tests individual resource methods with format parameter
- Tests format parameter in URL construction
- Basic format validation (parameter presence)

**Section 24 (Query Parameter Combination Testing):**

- Tests `f` parameter as one of 32 query parameters
- Tests `f` parameter combined with other parameters (limit, bbox, etc.)
- Tests format parameter precedence vs other parameters

**Section 25 (This Section):**

- Tests format negotiation mechanisms (query param, Accept header, links)
- Tests format precedence rules
- Tests format validation and error handling
- Tests URL encoding of media types
- Tests format advertisement and discovery

**No Duplication:** Each section tests different aspects:

- Section 13: Individual resources + format parameter
- Section 24: f parameter as part of query parameter system
- Section 25: Format negotiation mechanisms and precedence

---

## 9. Implementation Estimates

### 9.1 Test Implementation

| Task                          | Est. Time      | Priority |
| ----------------------------- | -------------- | -------- |
| Format negotiation tests (20) | 3-4 hours      | HIGH     |
| Format validation tests (10)  | 2-3 hours      | HIGH     |
| Format encoding tests (5)     | 1-2 hours      | MEDIUM   |
| Format precedence tests (10)  | 2-3 hours      | HIGH     |
| Error handling tests (5)      | 1-2 hours      | HIGH     |
| **TOTAL**                     | **9-14 hours** | -        |

### 9.2 Fixture Creation

| Task                        | Est. Time     | Priority |
| --------------------------- | ------------- | -------- |
| Query string fixtures (20)  | 1 hour        | HIGH     |
| Accept header fixtures (8)  | 30 minutes    | MEDIUM   |
| Response fixtures (6)       | 1-2 hours     | HIGH     |
| Error response fixtures (3) | 30 minutes    | MEDIUM   |
| **TOTAL**                   | **3-4 hours** | -        |

### 9.3 Format Validation/Encoding Utilities

| Task                      | Est. Time     | Priority |
| ------------------------- | ------------- | -------- |
| `FormatValidator` class   | 1-2 hours     | HIGH     |
| `ResponseValidator` class | 1-2 hours     | HIGH     |
| `FormatEncoder` utilities | 1 hour        | HIGH     |
| Unit tests for utilities  | 1-2 hours     | HIGH     |
| **TOTAL**                 | **4-7 hours** | -        |

### 9.4 Total Effort

| Phase                         | Est. Time                 |
| ----------------------------- | ------------------------- |
| Test Implementation           | 9-14 hours                |
| Fixture Creation              | 3-4 hours                 |
| Validation/Encoding Utilities | 4-7 hours                 |
| Documentation                 | 2-3 hours (this document) |
| **TOTAL**                     | **18-28 hours**           |

---

## 10. Key Recommendations

### 10.1 Prioritization

**HIGH Priority (Implement First):**

1. Query parameter format tests (f=json, f=geojson, f=sml)
2. Format validation utilities (`FormatValidator`)
3. URL encoding tests (+ → %2B)
4. Format precedence tests (query param > Accept > default)
5. 406 Not Acceptable error handling

**MEDIUM Priority (Implement Second):** 6. Accept header tests (fallback mechanism) 7. Response Content-Type validation 8. Format advertisement tests (Part 2 formats property) 9. Schema format parameter tests (obsFormat, cmdFormat)

**LOW Priority (Implement Last):** 10. Quality value tests (q=) - Not required by client library 11. Link-based format discovery - Not implemented 12. HTML format tests - Optional server feature

### 10.2 Testing Strategy

**Unit Tests:**

- Validate `FormatValidator` class (10 tests)
- Validate `ResponseValidator` class (5 tests)
- Test URL encoding functions (5 tests)

**Integration Tests:**

- Test format parameter in URL construction (20 tests)
- Test format precedence rules (10 tests)
- Test error handling (406, 400) (5 tests)

**Mock Strategy:**

- Mock fetch to return format-specific responses based on query parameter
- Parse URL to extract format parameter and validate encoding
- Mock Content-Type header in responses
- Test format validation before sending request

### 10.3 Reusable Patterns

**Parameterized Format Tests:**

```typescript
describe.each([
  { format: 'json', expected: 'application/json' },
  { format: 'geojson', expected: 'application/geo+json' },
  { format: 'sml', expected: 'application/sml+json' },
])('Format negotiation: $format', ({ format, expected }) => {
  it(`returns ${expected} for f=${format}`, async () => {
    const url = builder.getSystems('sys123', { f: format });
    expect(url).toContain(`f=${format}`);

    // Mock response
    const response = new Response('{}', {
      headers: { 'Content-Type': expected },
    });
    ResponseValidator.validateContentType(response, format);
  });
});
```

**Format Test Helper:**

```typescript
async function testFormat(
  resource: string,
  id: string,
  format: string,
  expectedContentType: string
): Promise<void> {
  const url = await builder[`get${resource}`](id, { f: format });
  parseAndValidateUrl(url, {
    pathname: `/${resource.toLowerCase()}/${id}`,
    query: { f: format },
  });

  // Verify Content-Type (with mocked response)
  const response = new Response('{}', {
    headers: { 'Content-Type': expectedContentType },
  });
  ResponseValidator.validateContentType(response, format);
}

// Usage
it('negotiates GeoJSON format for Systems', async () => {
  await testFormat('Systems', 'sys123', 'geojson', 'application/geo+json');
});
```

---

## 11. Success Criteria Validation

- [x] **All CSAPI media types are inventoried** ✅ (7 media types documented)
- [x] **Format negotiation methods are fully specified** ✅ (Query param, Accept header, links)
- [x] **Format precedence rules are documented** ✅ (f > Accept > default > 406)
- [x] **Media type support matrix is complete** ✅ (Resource-format matrix)
- [x] **Format fallback scenarios are defined** ✅ (Default formats by resource)
- [x] **Format test patterns are documented** ✅ (50 test scenarios)
- [x] **Deliverable document is peer-reviewed** ⏳ (awaiting review)

---

## 12. References

**CSAPI Specifications:**

- OGC API - Connected Systems Part 1: Format negotiation (Section 5.3)
- OGC API - Connected Systems Part 2: Format options (JSON, SWE Common)
- OGC API - Common: Query parameter `f` for format selection

**Related Research:**

- Section 8: CSAPI Specification Review (media type definitions)
- Section 24: Query Parameter Combination Testing (f parameter)
- Format Requirements: [csapi-format-requirements-3.1.md](../../requirements/csapi-format-requirements-3.1.md)
- Upstream Format Negotiation: [format-negotiation-analysis.md](../../upstream/format-negotiation-analysis.md)

**Implementation Guides:**

- Format negotiation follows EDR pattern (query parameter only)
- No custom Accept headers required
- No link-based format selection
- Simple ~13 line implementation

---

## 13. Appendix: Format Constants

### 13.1 Format Name Constants (Part 1)

```typescript
export const PART1_FORMATS = {
  JSON: 'json',
  GEOJSON: 'geojson',
  SENSORML: 'sml',
} as const;

export type Part1Format = (typeof PART1_FORMATS)[keyof typeof PART1_FORMATS];
```

### 13.2 Media Type Constants

```typescript
export const MEDIA_TYPES = {
  JSON: 'application/json',
  GEOJSON: 'application/geo+json',
  SENSORML: 'application/sml+json',
  SWE_JSON: 'application/swe+json',
  SWE_TEXT: 'application/swe+text',
  SWE_BINARY: 'application/swe+binary',
  URI_LIST: 'text/uri-list',
} as const;

export type MediaType = (typeof MEDIA_TYPES)[keyof typeof MEDIA_TYPES];
```

### 13.3 Format Map (Short Name → Media Type)

```typescript
export const FORMAT_MAP: Record<string, string> = {
  json: 'application/json',
  geojson: 'application/geo+json',
  sml: 'application/sml+json',
};
```

### 13.4 Resource Default Formats

```typescript
export const DEFAULT_FORMATS: Record<string, string> = {
  systems: 'application/geo+json',
  deployments: 'application/geo+json',
  procedures: 'application/geo+json',
  samplingFeatures: 'application/geo+json',
  properties: 'application/json',
  datastreams: 'application/json',
  observations: 'application/json',
  controlstreams: 'application/json',
  commands: 'application/json',
};
```

---

**Document Status:** ✅ Complete  
**Last Updated:** February 13, 2026  
**Next Review:** After peer review and feedback incorporation

---

## A1: Format Detection Fallback Scenarios {#a1-format-detection-fallback-scenarios}

> **📋 Added by A1 Finding C1-M3:** The original document had no test scenarios for client-side format detection when `Content-Type` is ambiguous or missing. This section fills that gap with scenarios that test actual client behavior — the document structure analysis fallback path.

### Background

The format detector (Guide §7) includes a document structure analysis fallback for cases where the server `Content-Type` header is:

- **Missing** entirely (non-compliant server)
- **Ambiguous** (e.g., `application/json` for what could be GeoJSON, SensorML JSON, or SWE Common JSON)
- **Incorrect** (e.g., server returns `application/json` for a GeoJSON FeatureCollection)

The client must determine the correct parser from the response body content. This is the ~13 lines of implementation code that the original 50 scenarios failed to test.

### Fallback Detection Test Scenarios (10 scenarios)

#### Missing Content-Type (3 scenarios)

**F1. Missing Content-Type — GeoJSON body detected**

```typescript
it('detects GeoJSON from body when Content-Type is missing', () => {
  const body = {
    type: 'Feature',
    id: 'sys-001',
    geometry: { type: 'Point', coordinates: [-122.4, 37.8] },
    properties: { name: 'Sensor', featureType: 'System' },
  };

  const format = detectFormat(body, /* contentType */ undefined);
  expect(format).toBe('application/geo+json');
});
```

**F2. Missing Content-Type — SensorML body detected**

```typescript
it('detects SensorML from body when Content-Type is missing', () => {
  const body = {
    type: 'PhysicalSystem',
    identifier: 'urn:example:sensor:001',
    components: [],
  };

  const format = detectFormat(body, /* contentType */ undefined);
  expect(format).toBe('application/sml+json');
});
```

**F3. Missing Content-Type — plain JSON (no distinguishing properties)**

```typescript
it('falls back to application/json when body has no format markers', () => {
  const body = {
    id: 'prop-001',
    definition: 'urn:ogc:def:property:OGC::Temperature',
    label: 'Temperature',
  };

  const format = detectFormat(body, /* contentType */ undefined);
  expect(format).toBe('application/json');
});
```

#### Ambiguous Content-Type (4 scenarios)

**F4. `application/json` Content-Type but body is GeoJSON FeatureCollection**

```typescript
it('detects GeoJSON FeatureCollection despite application/json Content-Type', () => {
  const body = {
    type: 'FeatureCollection',
    features: [
      {
        type: 'Feature',
        id: 'sys-001',
        properties: { name: 'Sensor' },
        geometry: null,
      },
    ],
  };

  const format = detectFormat(body, 'application/json');
  expect(format).toBe('application/geo+json');
});
```

**F5. `application/json` Content-Type but body is SensorML**

```typescript
it('detects SensorML despite application/json Content-Type', () => {
  const body = {
    type: 'PhysicalComponent',
    identifier: 'urn:example:component:001',
    inputs: [],
    outputs: [],
  };

  const format = detectFormat(body, 'application/json');
  expect(format).toBe('application/sml+json');
});
```

**F6. `application/json` Content-Type — body is SWE Common DataRecord**

```typescript
it('detects SWE Common JSON despite application/json Content-Type', () => {
  const body = {
    type: 'DataRecord',
    fields: [
      { name: 'time', type: 'Time' },
      { name: 'value', type: 'Quantity' },
    ],
  };

  const format = detectFormat(body, 'application/json');
  expect(format).toBe('application/swe+json');
});
```

**F7. `application/json` Content-Type — body is genuinely plain JSON**

```typescript
it('keeps application/json when body has no special format markers', () => {
  const body = {
    id: 'prop-001',
    label: 'Temperature',
    description: 'Ambient air temperature',
  };

  const format = detectFormat(body, 'application/json');
  expect(format).toBe('application/json');
});
```

#### Detection Logic Tests (3 scenarios)

**F8. GeoJSON detection keys: `type: 'Feature'` or `type: 'FeatureCollection'`**

```typescript
it('identifies GeoJSON by type=Feature with geometry property', () => {
  expect(isGeoJSON({ type: 'Feature', geometry: null, properties: {} })).toBe(
    true
  );
  expect(isGeoJSON({ type: 'FeatureCollection', features: [] })).toBe(true);
  expect(isGeoJSON({ type: 'DataRecord', fields: [] })).toBe(false);
});
```

**F9. SensorML detection keys: `type` in `['PhysicalSystem', 'PhysicalComponent', 'SimpleProcess', 'AggregateProcess']`**

```typescript
it('identifies SensorML by process type discriminator', () => {
  expect(isSensorML({ type: 'PhysicalSystem' })).toBe(true);
  expect(isSensorML({ type: 'PhysicalComponent' })).toBe(true);
  expect(isSensorML({ type: 'SimpleProcess' })).toBe(true);
  expect(isSensorML({ type: 'AggregateProcess' })).toBe(true);
  expect(isSensorML({ type: 'Feature' })).toBe(false);
});
```

**F10. SWE Common detection keys: `type` in `['DataRecord', 'DataArray', 'Vector', 'Matrix']` with `fields` or `elementType`**

```typescript
it('identifies SWE Common by data component type with structural properties', () => {
  expect(isSWECommon({ type: 'DataRecord', fields: [] })).toBe(true);
  expect(isSWECommon({ type: 'DataArray', elementType: {} })).toBe(true);
  expect(isSWECommon({ type: 'Vector', coordinates: [] })).toBe(true);
  expect(isSWECommon({ type: 'DataRecord' })).toBe(true); // type alone is sufficient
  expect(isSWECommon({ type: 'Feature' })).toBe(false);
});
```

### Detection Priority Order

When the body could match multiple formats, the detector uses this priority:

1. **GeoJSON** — `type === 'Feature'` or `type === 'FeatureCollection'` (highest priority, most unambiguous)
2. **SensorML** — `type` is a SensorML process type (`PhysicalSystem`, `PhysicalComponent`, etc.)
3. **SWE Common** — `type` is a SWE data component type (`DataRecord`, `DataArray`, etc.)
4. **Plain JSON** — fallback when no format markers found

### Implementation Reference

The `detectFormat()` function maps to the format detector described in Guide §7 (Format Detector: Extending Existing Content Negotiation). The detection logic examines root JSON properties:

```typescript
function detectFormat(body: unknown, contentType?: string): string {
  // If Content-Type is specific (not ambiguous), trust it
  if (contentType && contentType !== 'application/json') {
    return contentType.split(';')[0].trim();
  }

  // Fallback: analyze document structure
  if (typeof body === 'object' && body !== null) {
    const obj = body as Record<string, unknown>;
    if (obj.type === 'Feature' || obj.type === 'FeatureCollection') {
      return 'application/geo+json';
    }
    if (
      [
        'PhysicalSystem',
        'PhysicalComponent',
        'SimpleProcess',
        'AggregateProcess',
      ].includes(obj.type as string)
    ) {
      return 'application/sml+json';
    }
    if (
      ['DataRecord', 'DataArray', 'Vector', 'Matrix'].includes(
        obj.type as string
      )
    ) {
      return 'application/swe+json';
    }
  }

  return contentType || 'application/json';
}
```

**Scenario count:** 10 client-side fallback detection tests  
**Estimated LOC:** ~120 lines of test code  
**Implementation target:** ~13 lines (the `detectFormat` function above)
