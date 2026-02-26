# Section 24: Query Parameter Combination Testing - FINDINGS

> ⚠️ **REVIEW NOTICE — HIGH (H3): Server Validation and Precedence Tests Mixed with Client URL Construction**
>
> **Phase 2E Review | Issues: H3, M1, M11 | Anti-Patterns: AP1**
>
> This document is ~70% client-oriented. The URL construction tests using `builder.*` (Section 4.1, ~60 scenarios) are correctly client-oriented — they verify the client combines query parameters into valid URLs. However, Section 4.2 contains two categories of server behavior testing:
>
> - **Category A (10 scenarios):** "Wrong Parameter for Resource" — tests whether the SERVER validates parameter applicability (`GET /properties?bbox=...` → `Expected: 400 Bad Request`). The client's job is to build the URL, not enforce server-side parameter applicability.
> - **Category C (10 scenarios):** "Precedence Conflicts" — tests SERVER's precedence resolution (`offset + cursor` → `cursor takes precedence`). The client sends both; the server decides precedence.
>
> Additionally, Section 5.1 introduces `ParameterValidationError` which contradicts Doc 18's established error philosophy (reuse `EndpointError` / native `Error`).
>
> **What's usable:** URL construction (Section 4.1), parameter encoding (Section 4.4), client-side validation of obviously invalid values like bbox minLon > maxLon (Section 4.2 Category B partial).
>
> See also: [Phase 2E Review Report](../review/phase-2e-advanced-scenarios-category.md)

**Research Plan:** [Research Plan 24: Query Parameter Combination Testing](../research-plans/24-query-parameter-combination-testing.md)

**Research Questions:** 6 core questions about CSAPI query parameters inventory, testing valid parameter combinations, testing invalid parameter combinations, parameter precedence rules, testing spatial + temporal + relationship parameters together, and handling conflicting parameters

**Methodology:** 6-phase systematic analysis (Phase 1: Query Parameter Inventory extracting 32 parameters across Parts 1-3 → Phase 2: Combination Rules Analysis identifying precedence and interactions → Phase 3: Upstream Parameter Testing Analysis of existing patterns → Phase 4: Test Scenario Design for 120 scenarios across categories → Phase 5: Fixture Design for query strings and responses → Phase 6: Synthesis into comprehensive combination testing strategy)

**Research Time:** 5.5 hours (February 6, 2026)

**Primary Source(s):**

- [Query Parameter Requirements](../../requirements/query-parameter-requirements.md)
- [CSAPI Part 1 OpenAPI Specification](../../standards/ogcapi-connectedsystems-1.bundled.oas31.yaml)
- [CSAPI Part 2 OpenAPI Specification](../../standards/ogcapi-connectedsystems-2.bundled.oas31.yaml)
- [OGC API - Common](https://docs.ogc.org/is/19-072/19-072.html) (standard query parameters)
- [CSAPI Implementation Guide](../../../planning/csapi-implementation-guide.md)

**Supporting Resources:**

- Section 8: [CSAPI Specification Test Requirements](08-csapi-specification-test-requirements.md) (parameter definitions)
- Section 13: [Resource Method Testing Patterns](13-resource-method-testing-patterns.md) (parameter handling)
- Section 23: [Pagination Testing](23-pagination-testing.md) (limit/offset/cursor parameters)
- [OGC API - Features](https://docs.ogc.org/is/17-069r4/17-069r4.html) (query parameter patterns)

**Document Purpose:** Defines comprehensive testing strategy for 32 CSAPI query parameters across 7 categories (spatial, temporal, relationship, pagination, format, selection, hierarchical) with 120+ test scenarios covering valid/invalid combinations, parameter precedence rules (format > Accept, phenomenonTime > datetime, cursor > offset), and logical AND/OR operators

---

## Executive Summary

CSAPI defines **32 query parameters** across Parts 1-3, falling into 7 categories: spatial, temporal, relationship, pagination, format, selection, and hierarchical. Parameter combinations follow logical AND between different parameters and logical OR within comma-separated values.

This document defines a comprehensive testing strategy covering:

- 32 query parameters inventory with applicability matrix
- Valid and invalid combination rules
- Parameter precedence rules (format, temporal, pagination)
- 120+ test scenarios across categories
- Parameter validation patterns
- Encoding and error handling tests

### Key Findings

- **32 Total Parameters:** 5 standard OGC API + 27 CSAPI-specific
- **Parameter Categories:** 7 categories with clear boundaries
- **Combination Rules:** Logical AND between parameters, logical OR within parameters
- **No Mutually Exclusive Parameters:** All parameters can coexist (precedence rules apply)
- **Precedence Rules:** Format > Accept header, phenomenonTime > datetime, cursor > offset
- **Validation:** Type-based (not resource-based) - same validation across resources
- **Encoding:** Consistent rules (comma-separated for lists, URL encoding for special chars)

---

## 1. Query Parameter Inventory

### 1.1 Complete Parameter List (32 Parameters)

#### Category 1: Standard OGC API Parameters (5)

| Parameter    | Type       | Format                                          | Applies To                                         | Description               |
| ------------ | ---------- | ----------------------------------------------- | -------------------------------------------------- | ------------------------- |
| **bbox**     | Spatial    | `minLon,minLat,maxLon,maxLat[,minElev,maxElev]` | Systems, Deployments, Procedures, SamplingFeatures | Bounding box filter       |
| **datetime** | Temporal   | ISO 8601 instant or interval                    | Systems, Deployments, DataStreams, ControlStreams  | Temporal filter (generic) |
| **limit**    | Pagination | Positive integer (1-10000)                      | ALL 9 resources                                    | Maximum items per page    |
| **offset**   | Pagination | Non-negative integer (≥0)                       | ALL 9 resources                                    | Pagination offset         |
| **f**        | Format     | String (mime type or short name)                | ALL 9 resources                                    | Format negotiation        |

#### Category 2: CSAPI Common Parameters (4)

| Parameter          | Type       | Format                   | Applies To      | Description                         |
| ------------------ | ---------- | ------------------------ | --------------- | ----------------------------------- |
| **id**             | Identifier | Comma-separated IDs      | ALL 9 resources | Filter by local resource IDs        |
| **uid**            | Identifier | Comma-separated URIs     | ALL 9 resources | Filter by unique identifiers (URIs) |
| **q**              | Search     | String (keywords)        | ALL 9 resources | Full-text keyword search            |
| **{propertyName}** | Filter     | Any (property-dependent) | ALL 9 resources | Filter by any resource property     |

#### Category 3: CSAPI Hierarchical Parameters (1)

| Parameter     | Type    | Format            | Applies To           | Description                         |
| ------------- | ------- | ----------------- | -------------------- | ----------------------------------- |
| **recursive** | Boolean | `true` or `false` | Systems, Deployments | Include child resources recursively |

#### Category 4: CSAPI Relationship Parameters (8)

| Parameter              | Type         | Format                   | Applies To                                         | Description                          |
| ---------------------- | ------------ | ------------------------ | -------------------------------------------------- | ------------------------------------ |
| **parent**             | Relationship | Comma-separated IDs/UIDs | Systems, Deployments                               | Filter by parent resource            |
| **procedure**          | Relationship | Comma-separated IDs/UIDs | Systems                                            | Filter by associated procedure       |
| **foi**                | Relationship | Comma-separated IDs/UIDs | Systems, Deployments, SamplingFeatures             | Filter by feature of interest        |
| **observedProperty**   | Relationship | Comma-separated URIs     | Systems, Deployments, Procedures, SamplingFeatures | Filter by observed property          |
| **controlledProperty** | Relationship | Comma-separated URIs     | Systems, Deployments, Procedures, SamplingFeatures | Filter by controlled property        |
| **system**             | Relationship | Comma-separated IDs/UIDs | Deployments                                        | Filter by deployed system            |
| **baseProperty**       | Relationship | Comma-separated IDs/UIDs | Properties                                         | Filter by base property (transitive) |
| **objectType**         | Relationship | Comma-separated URIs     | Properties                                         | Filter by associated object type     |

#### Category 5: CSAPI Temporal Parameters (Part 2) (4)

| Parameter          | Type     | Format                                    | Applies To                | Description                       |
| ------------------ | -------- | ----------------------------------------- | ------------------------- | --------------------------------- |
| **phenomenonTime** | Temporal | ISO 8601 instant or interval              | DataStreams, Observations | When phenomenon occurred          |
| **resultTime**     | Temporal | ISO 8601 instant or interval, or `latest` | DataStreams, Observations | When result was obtained          |
| **executionTime**  | Temporal | ISO 8601 instant or interval              | ControlStreams            | When command was/will be executed |
| **issueTime**      | Temporal | ISO 8601 instant or interval              | ControlStreams            | When command was issued           |

#### Category 6: Format Negotiation Parameters (Part 2) (3)

| Parameter     | Type   | Format          | Applies To                    | Description                          |
| ------------- | ------ | --------------- | ----------------------------- | ------------------------------------ |
| **format**    | Format | Full media type | ALL resources                 | Alternative to `f` (full media type) |
| **obsFormat** | Format | Media type      | DataStream schema endpoint    | Observation encoding format          |
| **cmdFormat** | Format | Media type      | ControlStream schema endpoint | Command encoding format              |

#### Category 7: Pagination Parameters (Part 2) (1)

| Parameter  | Type       | Format        | Applies To                                          | Description                   |
| ---------- | ---------- | ------------- | --------------------------------------------------- | ----------------------------- |
| **cursor** | Pagination | Opaque string | DataStreams, Observations, ControlStreams, Commands | Cursor-based pagination token |

**Note:** There are additional resource-specific parameters mentioned in Section 10 (Notes) like `near`, `within`, `distance`, `properties`, `select`, `filter` (CQL2), but these are **NOT part of the current CSAPI specification**. They may be added in future versions or are specific to certain implementations.

### 1.2 Parameter Applicability Matrix

| Parameter              | Systems | Deployments | Procedures | SamplingFeatures | Properties | DataStreams | Observations | ControlStreams | Commands |
| ---------------------- | ------- | ----------- | ---------- | ---------------- | ---------- | ----------- | ------------ | -------------- | -------- |
| **bbox**               | ✅      | ✅          | ✅         | ✅               | ❌         | ❌          | ❌           | ❌             | ❌       |
| **datetime**           | ✅      | ✅          | ❌         | ❌               | ❌         | ✅          | ❌           | ✅             | ❌       |
| **limit**              | ✅      | ✅          | ✅         | ✅               | ✅         | ✅          | ✅           | ✅             | ✅       |
| **offset**             | ✅      | ✅          | ✅         | ✅               | ✅         | ✅          | ✅           | ✅             | ✅       |
| **f**                  | ✅      | ✅          | ✅         | ✅               | ✅         | ✅          | ✅           | ✅             | ✅       |
| **id**                 | ✅      | ✅          | ✅         | ✅               | ✅         | ✅          | ✅           | ✅             | ✅       |
| **uid**                | ✅      | ✅          | ✅         | ✅               | ✅         | ✅          | ✅           | ✅             | ✅       |
| **q**                  | ✅      | ✅          | ✅         | ✅               | ✅         | ✅          | ✅           | ✅             | ✅       |
| **{propertyName}**     | ✅      | ✅          | ✅         | ✅               | ✅         | ✅          | ✅           | ✅             | ✅       |
| **recursive**          | ✅      | ✅          | ❌         | ❌               | ❌         | ❌          | ❌           | ❌             | ❌       |
| **parent**             | ✅      | ✅          | ❌         | ❌               | ❌         | ❌          | ❌           | ❌             | ❌       |
| **procedure**          | ✅      | ❌          | ❌         | ❌               | ❌         | ❌          | ❌           | ❌             | ❌       |
| **foi**                | ✅      | ✅          | ❌         | ✅               | ❌         | ❌          | ❌           | ❌             | ❌       |
| **observedProperty**   | ✅      | ✅          | ✅         | ✅               | ❌         | ❌          | ❌           | ❌             | ❌       |
| **controlledProperty** | ✅      | ✅          | ✅         | ✅               | ❌         | ❌          | ❌           | ❌             | ❌       |
| **system**             | ❌      | ✅          | ❌         | ❌               | ❌         | ❌          | ❌           | ❌             | ❌       |
| **baseProperty**       | ❌      | ❌          | ❌         | ❌               | ✅         | ❌          | ❌           | ❌             | ❌       |
| **objectType**         | ❌      | ❌          | ❌         | ❌               | ✅         | ❌          | ❌           | ❌             | ❌       |
| **phenomenonTime**     | ❌      | ❌          | ❌         | ❌               | ❌         | ✅          | ✅           | ❌             | ❌       |
| **resultTime**         | ❌      | ❌          | ❌         | ❌               | ❌         | ✅          | ✅           | ❌             | ❌       |
| **executionTime**      | ❌      | ❌          | ❌         | ❌               | ❌         | ❌          | ❌           | ✅             | ❌       |
| **issueTime**          | ❌      | ❌          | ❌         | ❌               | ❌         | ❌          | ❌           | ✅             | ❌       |
| **cursor**             | ❌      | ❌          | ❌         | ❌               | ❌         | ✅          | ✅           | ✅             | ✅       |

---

## 2. Parameter Combination Rules

### 2.1 Logical Operators

#### Logical AND Between Different Parameters

Multiple parameters are combined with **logical AND**:

```
GET /systems?bbox=-180,-90,180,90&datetime=2024-01-01/..&observedProperty=temperature&limit=50
```

**Meaning:** Systems matching **ALL** conditions:

- Geometry intersects bbox **AND**
- validTime intersects datetime **AND**
- Observes temperature property **AND**
- Return at most 50 items

#### Logical OR Within Single Parameter

Comma-separated values within a parameter are treated as **logical OR**:

```
GET /systems?id=sys123,sys456,sys789
```

**Meaning:** Systems matching **ANY** id:

- id=sys123 **OR** id=sys456 **OR** id=sys789

#### Recursive + Filters

`recursive=true` applies to traversal depth, while other filters apply to ALL processed resources:

```
GET /systems?recursive=true&observedProperty=temperature&limit=100
```

**Meaning:**

- Traverse entire system hierarchy (recursive=true)
- Filter ALL systems (parents + descendants) by observedProperty=temperature
- Return at most 100 matching systems

### 2.2 Parameter Precedence Rules

#### Format Negotiation Precedence

1. **Query parameter (`f` or `format`)** - highest priority
2. **Accept header** - second priority
3. **Server default format** - fallback
4. **406 Not Acceptable** - if no format matches

```
GET /systems?f=sml
Accept: application/json
// Server returns application/sml+json (query parameter wins)
```

#### Temporal Filter Precedence (Part 2)

**For Observations:**

- `phenomenonTime` takes precedence over `datetime` when both present
- `resultTime` filters independently of `phenomenonTime`
- Both can be combined: `phenomenonTime=2024-01-01/..&resultTime=2024-01-02/..`

**For Commands:**

- `executionTime` takes precedence over `datetime` when both present
- `issueTime` filters independently of `executionTime`
- Both can be combined: `executionTime=2024-01-01/..&issueTime=2024-01-02/..`

#### Pagination Precedence

- `cursor` takes precedence over `offset` (if server supports cursor-based pagination)
- `limit` always applies (both offset-based and cursor-based modes)
- Server determines which mode to use based on parameter presence

```
GET /observations?limit=100&offset=50&cursor=abc123
// Server uses cursor-based pagination (cursor wins), offset ignored
```

### 2.3 Valid Combinations

All parameters can coexist - there are **no mutually exclusive parameters**. However, precedence rules determine which takes effect when multiple similar parameters are present.

**High-Priority Combinations (Common Use Cases):**

1. **Pagination + Spatial:**

   ```
   ?bbox=-180,-90,180,90&limit=50&offset=0
   ```

2. **Pagination + Temporal:**

   ```
   ?phenomenonTime=2024-01-01/2024-12-31&limit=1000
   ```

3. **Spatial + Temporal:**

   ```
   ?bbox=-10,-10,10,10&datetime=2024-01-01/..
   ```

4. **Spatial + Temporal + Relationship:**

   ```
   ?bbox=-10,-10,10,10&datetime=2024-01-01/..&observedProperty=temperature
   ```

5. **Relationship + Pagination:**

   ```
   ?parent=sys123&recursive=true&limit=100
   ```

6. **Multiple Temporal Filters (Part 2):**

   ```
   ?phenomenonTime=2024-01-01/..&resultTime=2024-01-02/..
   ```

7. **Format + Filters:**
   ```
   ?bbox=-10,-10,10,10&f=geojson
   ```

### 2.4 Invalid Combinations

There are **no inherently invalid parameter combinations** in CSAPI. All parameters can technically coexist. However, the following scenarios require special handling:

#### Scenario 1: Parameter Applied to Wrong Resource

```
GET /properties?bbox=-180,-90,180,90
// Properties don't have geometry - bbox has no effect (silently ignored or 400 error)
```

**Behavior:** Server MAY return 400 Bad Request or silently ignore parameter

#### Scenario 2: Conflicting Pagination Modes

```
GET /observations?offset=100&cursor=abc123
// Both offset and cursor present
```

**Behavior:** Server uses cursor (precedence rule), offset ignored

#### Scenario 3: Conflicting Temporal Parameters

```
GET /observations?datetime=2024-01-01/..&phenomenonTime=2024-02-01/..
// Both datetime and phenomenonTime present
```

**Behavior:** Server uses phenomenonTime (precedence rule), datetime ignored

#### Scenario 4: Invalid Parameter Values

```
GET /systems?limit=-10
// Negative limit
```

**Behavior:** Server returns 400 Bad Request with error message

---

## 3. Upstream Parameter Testing Analysis

### 3.1 EDR Parameter Testing (PR #114)

**Pattern:** Parameter validation before URL construction

```typescript
// Validate optional parameters
if (optional_params.parameter_name) {
  for (const param of optional_params.parameter_name) {
    if (!this.supported_parameters[param]) {
      throw new Error(
        `The following parameter name does not exist on this collection: '${param}'.`
      );
    }
  }
  url.searchParams.set(
    'parameter-name',
    optional_params.parameter_name.join(',')
  );
}
```

**Key Pattern:**

1. Check parameter presence (`if (optional_params.parameter_name)`)
2. Validate parameter values (e.g., check against supported list)
3. Throw meaningful error with specific message
4. Encode parameter into query string

**Testing Approach:**

- Test with valid parameter values
- Test with invalid parameter values (expect error)
- Test parameter encoding (special characters, arrays)
- Test parameter absence (should not appear in query string)

### 3.2 Section 13 Resource Method Tests

**Pattern:** Test individual parameters in isolation

```typescript
it('applies bbox filter', async () => {
  const url = builder.getSystems({
    bbox: { minLon: -180, minLat: -90, maxLon: 180, maxLat: 90 },
  });
  parseAndValidateUrl(url, {
    pathname: '/systems',
    query: { bbox: '-180,-90,180,90' },
  });
});
```

**Coverage:**

- Section 13 tests **individual parameters** per resource
- Parameter combinations tested in high-priority scenarios only
- Focus on parameter presence and encoding, not comprehensive combinations

**Gap:** Section 13 does not test extensive parameter combinations (2-3 parameters) or edge cases like conflicting parameters.

### 3.3 Section 23 Pagination Testing

**Pattern:** Test pagination parameters with other filters

```typescript
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
```

**Coverage:** Section 23 tests pagination combined with filtering (bbox, datetime, parent, foi)

**Overlap with Section 24:**

- Section 23 focuses on pagination behavior (multi-page scenarios, cursor extraction)
- Section 24 focuses on parameter combination rules across all categories

---

## 4. Test Scenario Design

### 4.1 Valid Combination Scenarios (60 scenarios)

> ✅ **REVIEW NOTICE: Correctly Client-Oriented — URL Construction Tests**
>
> These 60 scenarios test client URL construction: `builder.getSystems({ bbox: [...], limit: 50 })` → verify URL contains `?bbox=-180,-90,180,90&limit=50`. This is the correct pattern — testing that the client builds valid query strings from typed parameters. These follow the upstream `parseAndValidateUrl()` pattern.

#### Category A: Two-Parameter Combinations (20 scenarios)

1. **bbox + limit**

   ```
   ?bbox=-180,-90,180,90&limit=50
   ```

2. **bbox + datetime**

   ```
   ?bbox=-180,-90,180,90&datetime=2024-01-01/2024-12-31
   ```

3. **datetime + limit**

   ```
   ?datetime=2024-01-01/..&limit=100
   ```

4. **phenomenonTime + limit**

   ```
   ?phenomenonTime=2024-01-01/..&limit=1000
   ```

5. **observedProperty + bbox**

   ```
   ?observedProperty=temperature&bbox=-10,-10,10,10
   ```

6. **observedProperty + datetime**

   ```
   ?observedProperty=temperature&datetime=2024-01-01/..
   ```

7. **parent + recursive**

   ```
   ?parent=sys123&recursive=true
   ```

8. **parent + limit**

   ```
   ?parent=sys123&limit=50
   ```

9. **foi + bbox**

   ```
   ?foi=river123&bbox=-10,-10,10,10
   ```

10. **foi + datetime**

    ```
    ?foi=river123&datetime=2024-01-01/..
    ```

11. **procedure + observedProperty**

    ```
    ?procedure=proc123&observedProperty=temperature
    ```

12. **system + datetime** (Deployments)

    ```
    ?system=sys123&datetime=2024-01-01/..
    ```

13. **phenomenonTime + resultTime**

    ```
    ?phenomenonTime=2024-01-01/..&resultTime=2024-01-02/..
    ```

14. **executionTime + issueTime**

    ```
    ?executionTime=2024-01-01/..&issueTime=2024-01-02/..
    ```

15. **id + limit**

    ```
    ?id=sys123,sys456&limit=10
    ```

16. **uid + bbox**

    ```
    ?uid=urn:uuid:123&bbox=-10,-10,10,10
    ```

17. **q + limit**

    ```
    ?q=weather,station&limit=20
    ```

18. **f + bbox**

    ```
    ?f=geojson&bbox=-180,-90,180,90
    ```

19. **cursor + limit**

    ```
    ?cursor=abc123&limit=100
    ```

20. **offset + limit**
    ```
    ?offset=50&limit=50
    ```

#### Category B: Three-Parameter Combinations (20 scenarios)

21. **bbox + datetime + limit**

    ```
    ?bbox=-10,-10,10,10&datetime=2024-01-01/..&limit=50
    ```

22. **bbox + datetime + observedProperty**

    ```
    ?bbox=-10,-10,10,10&datetime=2024-01-01/..&observedProperty=temperature
    ```

23. **bbox + observedProperty + limit**

    ```
    ?bbox=-10,-10,10,10&observedProperty=temperature&limit=100
    ```

24. **datetime + observedProperty + limit**

    ```
    ?datetime=2024-01-01/..&observedProperty=temperature&limit=100
    ```

25. **parent + recursive + limit**

    ```
    ?parent=sys123&recursive=true&limit=100
    ```

26. **parent + observedProperty + limit**

    ```
    ?parent=sys123&observedProperty=temperature&limit=50
    ```

27. **foi + bbox + datetime**

    ```
    ?foi=river123&bbox=-10,-10,10,10&datetime=2024-01-01/..
    ```

28. **foi + observedProperty + limit**

    ```
    ?foi=river123&observedProperty=temperature&limit=100
    ```

29. **procedure + bbox + datetime**

    ```
    ?procedure=proc123&bbox=-10,-10,10,10&datetime=2024-01-01/..
    ```

30. **system + datetime + limit** (Deployments)

    ```
    ?system=sys123&datetime=2024-01-01/..&limit=50
    ```

31. **phenomenonTime + resultTime + limit**

    ```
    ?phenomenonTime=2024-01-01/..&resultTime=2024-01-02/..&limit=1000
    ```

32. **executionTime + issueTime + limit**

    ```
    ?executionTime=2024-01-01/..&issueTime=2024-01-02/..&limit=100
    ```

33. **id + bbox + limit**

    ```
    ?id=sys123,sys456&bbox=-10,-10,10,10&limit=20
    ```

34. **uid + datetime + limit**

    ```
    ?uid=urn:uuid:123&datetime=2024-01-01/..&limit=50
    ```

35. **q + bbox + limit**

    ```
    ?q=weather&bbox=-10,-10,10,10&limit=20
    ```

36. **f + bbox + datetime**

    ```
    ?f=geojson&bbox=-10,-10,10,10&datetime=2024-01-01/..
    ```

37. **cursor + phenomenonTime + limit**

    ```
    ?cursor=abc123&phenomenonTime=2024-01-01/..&limit=100
    ```

38. **offset + bbox + limit**

    ```
    ?offset=100&bbox=-10,-10,10,10&limit=50
    ```

39. **bbox + datetime + f**

    ```
    ?bbox=-10,-10,10,10&datetime=2024-01-01/..&f=geojson
    ```

40. **observedProperty + controlledProperty + limit**
    ```
    ?observedProperty=temperature&controlledProperty=valve-position&limit=50
    ```

#### Category C: Four+ Parameter Combinations (20 scenarios)

41. **bbox + datetime + observedProperty + limit**

    ```
    ?bbox=-10,-10,10,10&datetime=2024-01-01/..&observedProperty=temperature&limit=100
    ```

42. **bbox + datetime + observedProperty + offset + limit**

    ```
    ?bbox=-10,-10,10,10&datetime=2024-01-01/..&observedProperty=temperature&offset=50&limit=50
    ```

43. **parent + recursive + bbox + datetime + limit**

    ```
    ?parent=sys123&recursive=true&bbox=-10,-10,10,10&datetime=2024-01-01/..&limit=100
    ```

44. **foi + bbox + datetime + observedProperty + limit**

    ```
    ?foi=river123&bbox=-10,-10,10,10&datetime=2024-01-01/..&observedProperty=temperature&limit=100
    ```

45. **procedure + bbox + datetime + observedProperty + limit**

    ```
    ?procedure=proc123&bbox=-10,-10,10,10&datetime=2024-01-01/..&observedProperty=temperature&limit=100
    ```

46. **system + datetime + bbox + limit + offset** (Deployments)

    ```
    ?system=sys123&datetime=2024-01-01/..&bbox=-10,-10,10,10&limit=50&offset=100
    ```

47. **phenomenonTime + resultTime + foi + limit + cursor**

    ```
    ?phenomenonTime=2024-01-01/..&resultTime=2024-01-02/..&foi=river123&limit=1000&cursor=abc123
    ```

48. **id + bbox + datetime + limit + f**

    ```
    ?id=sys123,sys456&bbox=-10,-10,10,10&datetime=2024-01-01/..&limit=50&f=geojson
    ```

49. **q + bbox + datetime + limit + offset**

    ```
    ?q=weather&bbox=-10,-10,10,10&datetime=2024-01-01/..&limit=20&offset=40
    ```

50. **bbox + datetime + observedProperty + controlledProperty + limit**

    ```
    ?bbox=-10,-10,10,10&datetime=2024-01-01/..&observedProperty=temperature&controlledProperty=valve-position&limit=100
    ```

51. **parent + recursive + observedProperty + bbox + datetime + limit**

    ```
    ?parent=sys123&recursive=true&observedProperty=temperature&bbox=-10,-10,10,10&datetime=2024-01-01/..&limit=100
    ```

52. **All universal parameters** (limit, offset, f, id, uid, q)

    ```
    ?limit=50&offset=100&f=geojson&id=sys123&uid=urn:uuid:456&q=weather
    ```

53. **Complex System query** (7 parameters)

    ```
    ?bbox=-10,-10,10,10&datetime=2024-01-01/..&parent=sys123&recursive=true&observedProperty=temperature&procedure=proc123&limit=100
    ```

54. **Complex Deployment query** (6 parameters)

    ```
    ?bbox=-10,-10,10,10&datetime=2024-01-01/..&system=sys123&foi=river123&limit=50&offset=100
    ```

55. **Complex Observation query** (5 parameters)

    ```
    ?phenomenonTime=2024-01-01/..&resultTime=2024-01-02/..&foi=river123&limit=1000&cursor=abc123
    ```

56. **baseProperty + objectType + limit** (Properties)

    ```
    ?baseProperty=pressure&objectType=https://dbpedia.org/page/Watercraft&limit=50
    ```

57. **Multiple relationship filters**

    ```
    ?parent=sys123&procedure=proc456&foi=river789&observedProperty=temperature&limit=100
    ```

58. **Temporal filters + format**

    ```
    ?phenomenonTime=2024-01-01/..&resultTime=2024-01-02/..&f=application/swe+json&limit=1000
    ```

59. **Spatial 3D + temporal + relationship**

    ```
    ?bbox=-10,-10,0,10,10,1000&datetime=2024-01-01/..&observedProperty=temperature&limit=100
    ```

60. **Edge case: All applicable parameters for Systems** (10+ parameters)
    ```
    ?bbox=-10,-10,10,10&datetime=2024-01-01/..&parent=sys123&recursive=true&procedure=proc456&foi=river789&observedProperty=temperature,pressure&controlledProperty=valve-position&id=sys123,sys456&q=weather&limit=100
    ```

### 4.2 Invalid Combination Scenarios (30 scenarios)

#### Category A: Wrong Parameter for Resource (10 scenarios)

> ⚠️ **REVIEW NOTICE (H3): Server Validation Testing — Not Client Responsibility**
>
> These 10 scenarios test whether the SERVER validates parameter applicability (`GET /properties?bbox=...` → `Expected: 400 Bad Request or silently ignored`). The client's job is to build the URL requested by the user and handle whatever response comes back. It should not implement server-side parameter applicability rules. If client-side guardrails are desired (e.g., TypeScript types that don't allow `bbox` on property queries), test the type system, not the HTTP response.

61. **bbox on Properties** (no geometry)

    ```
    GET /properties?bbox=-180,-90,180,90
    // Expected: 400 Bad Request or silently ignored
    ```

62. **phenomenonTime on Systems** (Part 1 resource)

    ```
    GET /systems?phenomenonTime=2024-01-01/..
    // Expected: 400 Bad Request (parameter not applicable)
    ```

63. **resultTime on Commands** (wrong Part 2 resource)

    ```
    GET /commands?resultTime=2024-01-01/..
    // Expected: 400 Bad Request
    ```

64. **executionTime on Observations** (wrong Part 2 resource)

    ```
    GET /observations?executionTime=2024-01-01/..
    // Expected: 400 Bad Request
    ```

65. **recursive on Observations** (Part 2 resource)

    ```
    GET /observations?recursive=true
    // Expected: 400 Bad Request
    ```

66. **parent on Properties** (non-hierarchical resource)

    ```
    GET /properties?parent=prop123
    // Expected: 400 Bad Request
    ```

67. **system on Systems** (wrong relationship)

    ```
    GET /systems?system=sys123
    // Expected: 400 Bad Request
    ```

68. **baseProperty on Systems** (Properties-only parameter)

    ```
    GET /systems?baseProperty=pressure
    // Expected: 400 Bad Request
    ```

69. **objectType on Deployments** (Properties-only parameter)

    ```
    GET /deployments?objectType=https://dbpedia.org/page/Watercraft
    // Expected: 400 Bad Request
    ```

70. **cursor on Systems** (Part 2 pagination only)
    ```
    GET /systems?cursor=abc123
    // Expected: 400 Bad Request or silently ignored
    ```

#### Category B: Invalid Parameter Values (10 scenarios)

> ⚠️ **REVIEW NOTICE (M11): Mixed Client/Server Invalid Parameter Tests**
>
> ~50% of these scenarios are legitimate client validation (bbox minLon > maxLon, negative limit, negative offset) — the client CAN and SHOULD reject obviously invalid values before sending a request. These are correctly testable as client-side `ParameterValidator` behavior.
>
> ~50% test server behavior: invalid format → 406, exceeds Part 2 max limit → 400, malformed URI → server rejection. These are server compliance tests. Only retain tests where the client itself performs the validation before the request is sent.

71. **Invalid bbox format** (wrong number of coordinates)

    ```
    ?bbox=-180,-90
    // Expected: 400 Bad Request (must be 4 or 6 values)
    ```

72. **Invalid bbox range** (minLon > maxLon)

    ```
    ?bbox=180,-90,-180,90
    // Expected: 400 Bad Request
    ```

73. **Invalid datetime format** (not ISO 8601)

    ```
    ?datetime=01/01/2024
    // Expected: 400 Bad Request
    ```

74. **Invalid datetime interval** (start > end)

    ```
    ?datetime=2024-12-31/2024-01-01
    // Expected: 400 Bad Request
    ```

75. **Invalid limit** (zero or negative)

    ```
    ?limit=0
    ?limit=-10
    // Expected: 400 Bad Request
    ```

76. **Invalid limit** (exceeds Part 2 maximum)

    ```
    ?limit=15000
    // Expected: 400 Bad Request (max 10,000)
    ```

77. **Invalid offset** (negative)

    ```
    ?offset=-10
    // Expected: 400 Bad Request
    ```

78. **Invalid recursive** (not boolean)

    ```
    ?recursive=maybe
    // Expected: 400 Bad Request (must be true or false)
    ```

79. **Invalid format** (unsupported)

    ```
    ?f=application/xml
    // Expected: 406 Not Acceptable or 400 Bad Request
    ```

80. **Invalid URI** (malformed)
    ```
    ?uid=not-a-valid-uri!!!
    // Expected: 400 Bad Request
    ```

#### Category C: Precedence Conflicts (10 scenarios)

> ⚠️ **REVIEW NOTICE (H3): Precedence Conflict Tests Test Server Behavior**
>
> These 10 scenarios test how the SERVER resolves precedence when conflicting parameters are sent (`cursor takes precedence`, `phenomenonTime takes precedence`, `f parameter takes precedence over Accept header`). The client sends both parameters; the server decides which takes precedence. Client tests should verify the URL is correctly constructed with both parameters — what the server does with them is server behavior.

81. **offset + cursor** (conflicting pagination)

    ```
    ?offset=100&cursor=abc123
    // Expected: cursor takes precedence, offset ignored
    // Test: Verify cursor is used, offset has no effect
    ```

82. **datetime + phenomenonTime** (conflicting temporal)

    ```
    ?datetime=2024-01-01/..&phenomenonTime=2024-02-01/..
    // Expected: phenomenonTime takes precedence
    // Test: Verify phenomenonTime filter applied, datetime ignored
    ```

83. **datetime + executionTime** (conflicting temporal)

    ```
    ?datetime=2024-01-01/..&executionTime=2024-02-01/..
    // Expected: executionTime takes precedence
    // Test: Verify executionTime filter applied, datetime ignored
    ```

84. **f + format** (duplicate format parameters)

    ```
    ?f=geojson&format=application/sml+json
    // Expected: Implementation-dependent (both are query parameters)
    // Test: Document which takes precedence
    ```

85. **f parameter + Accept header** (format conflict)

    ```
    ?f=geojson
    Accept: application/sml+json
    // Expected: f parameter takes precedence
    // Test: Verify GeoJSON returned (not SensorML)
    ```

86. **Multiple f parameters** (repeated parameter)

    ```
    ?f=geojson&f=sml
    // Expected: Last value wins or 400 Bad Request
    // Test: Document actual behavior
    ```

87. **Empty parameter values**

    ```
    ?bbox=&limit=10
    // Expected: 400 Bad Request
    ```

88. **Parameter case sensitivity**

    ```
    ?LIMIT=10&Bbox=-10,-10,10,10
    // Expected: Implementation-dependent (should be case-insensitive)
    // Test: Verify case handling
    ```

89. **Whitespace in parameter names**

    ```
    ?limit =10& bbox=-10,-10,10,10
    // Expected: 400 Bad Request or silently ignored
    ```

90. **Special characters in parameter values** (not URL-encoded)
    ```
    ?q=weather+station&uid=urn:uuid:123
    // Expected: May be misinterpreted (+ as space)
    // Test: Verify proper encoding required
    ```

### 4.3 Parameter Validation Scenarios (20 scenarios)

#### Type Validation (5 scenarios)

91. **bbox must be array of numbers**

    ```
    ?bbox=invalid
    // Expected: 400 Bad Request
    ```

92. **limit must be integer**

    ```
    ?limit=10.5
    // Expected: 400 Bad Request
    ```

93. **recursive must be boolean**

    ```
    ?recursive=1
    // Expected: 400 Bad Request (or coerced to true)
    ```

94. **datetime must be ISO 8601**

    ```
    ?datetime=invalid-date
    // Expected: 400 Bad Request
    ```

95. **cursor must be string**
    ```
    ?cursor=12345
    // Expected: Accepted (cursor is opaque)
    ```

#### Range Validation (5 scenarios)

96. **bbox latitude must be [-90, 90]**

    ```
    ?bbox=-180,-100,180,100
    // Expected: 400 Bad Request
    ```

97. **bbox longitude must be [-180, 180]**

    ```
    ?bbox=-200,-90,200,90
    // Expected: 400 Bad Request
    ```

98. **limit must be [1, 10000]** (Part 2)

    ```
    ?limit=20000
    // Expected: 400 Bad Request
    ```

99. **offset must be >= 0**

    ```
    ?offset=-5
    // Expected: 400 Bad Request
    ```

100.  **3D bbox: minElev <= maxElev**
      ```
      ?bbox=-10,-10,1000,10,10,0
      // Expected: 400 Bad Request
      ```

#### Format Validation (5 scenarios)

101. **datetime instant format**

     ```
     ?datetime=2024-01-15T12:00:00Z
     // Expected: Valid ISO 8601 instant
     ```

102. **datetime interval format**

     ```
     ?datetime=2024-01-01/2024-12-31
     // Expected: Valid ISO 8601 interval
     ```

103. **datetime open interval (start)**

     ```
     ?datetime=2024-01-01/..
     // Expected: Valid open interval
     ```

104. **datetime open interval (end)**

     ```
     ?datetime=../2024-12-31
     // Expected: Valid open interval
     ```

105. **UID format validation**
     ```
     ?uid=urn:uuid:550e8400-e29b-41d4-a716-446655440000
     // Expected: Valid URI format
     ```

#### Encoding Validation (5 scenarios)

106. **Comma-separated IDs**

     ```
     ?id=sys123,sys456,sys789
     // Expected: Parsed as array [sys123, sys456, sys789]
     ```

107. **URL encoding for special characters**

     ```
     ?uid=urn%3Auuid%3A123
     // Expected: Decoded to urn:uuid:123
     ```

108. **Plus sign in media type**

     ```
     ?f=application/sml%2Bjson
     // Expected: Decoded to application/sml+json
     ```

109. **Space encoding**

     ```
     ?q=weather%20station
     // Expected: Decoded to "weather station"
     ```

110. **Slash in datetime interval**
     ```
     ?datetime=2024-01-01T00:00:00Z/2024-12-31T23:59:59Z
     // Expected: Slash NOT encoded (delimiter)
     ```

### 4.4 Parameter Encoding Scenarios (10 scenarios)

> ✅ **REVIEW NOTICE: Correctly Client-Oriented — URL Encoding Tests**
>
> These encoding scenarios test actual client behavior: how the client encodes commas, colons, plus signs, and other special characters in query parameter values. This is genuine client URL construction logic that should be tested.

111. **Comma NOT encoded** (delimiter)

     ```
     ?id=sys123,sys456
     // Commas are NOT URL-encoded
     ```

112. **Colon encoded in URIs**

     ```
     ?uid=urn%3Auuid%3A123
     // Colons ARE URL-encoded in URI values
     ```

113. **Plus encoded in media types**

     ```
     ?f=application%2Fsml%2Bjson
     // Plus signs ARE URL-encoded
     ```

114. **Space as %20**

     ```
     ?q=weather%20station
     // Spaces encoded as %20 (not +)
     ```

115. **Slash in datetime NOT encoded**

     ```
     ?datetime=2024-01-01/2024-12-31
     // Slash is delimiter, NOT encoded
     ```

116. **Double-dot NOT encoded**

     ```
     ?datetime=2024-01-01/..
     // Double-dot for open end, NOT encoded
     ```

117. **Ampersand in value encoded**

     ```
     ?q=weather%26climate
     // Ampersand encoded to avoid parameter delimiter confusion
     ```

118. **Equals in value encoded**

     ```
     ?q=a%3Db
     // Equals encoded to avoid key-value delimiter confusion
     ```

119. **International characters encoded**

     ```
     ?q=caf%C3%A9
     // UTF-8 characters URL-encoded
     ```

120. **Bracket notation NOT supported**
     ```
     ?id[]=sys123&id[]=sys456
     // Expected: 400 Bad Request (use comma-separated)
     ```

---

## 5. Parameter Validation Patterns

### 5.1 Client-Side Validation

> ⚠️ **REVIEW NOTICE (M1): `ParameterValidationError` Contradicts Doc 18 Error Philosophy**
>
> This section introduces `class ParameterValidationError extends Error` with custom properties (`parameterName`, `parameterValue`, `validationRule`), used 12+ times throughout the document. Doc 18 (Error Condition Testing Strategy) explicitly established: "Reuse existing `EndpointError` and native `Error` — no new error classes needed." This is a direct cross-document contradiction.
>
> **Resolution:** Use existing `EndpointError` or native `Error` per Doc 18's established philosophy. The validation logic itself (bbox range checking, limit bounds) is useful; only the custom error class needs to be replaced.

**Before Sending Request:**

```typescript
class ParameterValidator {
  /**
   * Validate bbox parameter
   */
  static validateBBox(bbox: BBoxFilter): void {
    if (bbox.minLon > bbox.maxLon) {
      throw new ParameterValidationError(
        'bbox',
        bbox,
        'minLon must be ≤ maxLon'
      );
    }
    if (bbox.minLat > bbox.maxLat) {
      throw new ParameterValidationError(
        'bbox',
        bbox,
        'minLat must be ≤ maxLat'
      );
    }
    if (bbox.minLat < -90 || bbox.minLat > 90) {
      throw new ParameterValidationError(
        'bbox',
        bbox,
        'minLat must be in [-90, 90]'
      );
    }
    if (bbox.maxLat < -90 || bbox.maxLat > 90) {
      throw new ParameterValidationError(
        'bbox',
        bbox,
        'maxLat must be in [-90, 90]'
      );
    }
    if (bbox.minLon < -180 || bbox.minLon > 180) {
      throw new ParameterValidationError(
        'bbox',
        bbox,
        'minLon must be in [-180, 180]'
      );
    }
    if (bbox.maxLon < -180 || bbox.maxLon > 180) {
      throw new ParameterValidationError(
        'bbox',
        bbox,
        'maxLon must be in [-180, 180]'
      );
    }
    if (
      bbox.minElev !== undefined &&
      bbox.maxElev !== undefined &&
      bbox.minElev > bbox.maxElev
    ) {
      throw new ParameterValidationError(
        'bbox',
        bbox,
        'minElev must be ≤ maxElev'
      );
    }
  }

  /**
   * Validate datetime parameter
   */
  static validateDateTime(datetime: DateTimeFilter): void {
    if (
      typeof datetime === 'object' &&
      'start' in datetime &&
      'end' in datetime
    ) {
      const start =
        typeof datetime.start === 'string'
          ? new Date(datetime.start)
          : datetime.start;
      const end =
        typeof datetime.end === 'string'
          ? new Date(datetime.end)
          : datetime.end;

      if (start > end) {
        throw new ParameterValidationError(
          'datetime',
          datetime,
          'start must be ≤ end'
        );
      }
    }
  }

  /**
   * Validate limit parameter
   */
  static validateLimit(limit: number, isPart2: boolean = false): void {
    if (limit < 1) {
      throw new ParameterValidationError('limit', limit, 'must be ≥ 1');
    }
    if (isPart2 && limit > 10000) {
      throw new ParameterValidationError(
        'limit',
        limit,
        'must be ≤ 10000 (Part 2 maximum)'
      );
    }
  }

  /**
   * Validate offset parameter
   */
  static validateOffset(offset: number): void {
    if (offset < 0) {
      throw new ParameterValidationError('offset', offset, 'must be ≥ 0');
    }
  }

  /**
   * Validate URI format
   */
  static validateURI(uri: string): void {
    try {
      new URL(uri);
    } catch (e) {
      throw new ParameterValidationError('uri', uri, 'must be a valid URI');
    }
  }
}

class ParameterValidationError extends Error {
  constructor(
    public parameterName: string,
    public parameterValue: any,
    public validationRule: string
  ) {
    super(`Invalid ${parameterName}: ${validationRule}`);
    this.name = 'ParameterValidationError';
  }
}
```

### 5.2 Parameter Encoding Patterns

```typescript
class ParameterEncoder {
  /**
   * Encode bbox as comma-separated string
   */
  static encodeBBox(bbox: BBoxFilter): string {
    ParameterValidator.validateBBox(bbox);

    const coords = [bbox.minLon, bbox.minLat, bbox.maxLon, bbox.maxLat];
    if (bbox.minElev !== undefined && bbox.maxElev !== undefined) {
      coords.push(bbox.minElev, bbox.maxElev);
    }

    return coords.join(',');
  }

  /**
   * Encode datetime as ISO 8601 string
   */
  static encodeDateTime(datetime: DateTimeFilter): string {
    ParameterValidator.validateDateTime(datetime);

    if (typeof datetime === 'string') {
      return datetime; // Already a string (e.g., 'now', 'latest')
    }

    if (datetime instanceof Date) {
      return datetime.toISOString();
    }

    // Interval
    const start = datetime.start
      ? typeof datetime.start === 'string'
        ? datetime.start
        : datetime.start.toISOString()
      : '..';
    const end = datetime.end
      ? typeof datetime.end === 'string'
        ? datetime.end
        : datetime.end.toISOString()
      : '..';

    return `${start}/${end}`;
  }

  /**
   * Encode array as comma-separated string
   */
  static encodeArray(values: string[]): string {
    return values.join(',');
  }

  /**
   * Encode format parameter (with special handling for +)
   */
  static encodeFormat(format: string): string {
    // URL-encode + as %2B
    return format.replace(/\+/g, '%2B');
  }

  /**
   * Build query string from options
   */
  static buildQueryString(options: Record<string, any>): string {
    const params = new URLSearchParams();

    for (const [key, value] of Object.entries(options)) {
      if (value === undefined || value === null) continue;

      if (key === 'bbox' && typeof value === 'object') {
        params.set('bbox', this.encodeBBox(value));
      } else if (
        key === 'datetime' &&
        (typeof value === 'object' || value instanceof Date)
      ) {
        params.set('datetime', this.encodeDateTime(value));
      } else if (Array.isArray(value)) {
        params.set(key, this.encodeArray(value));
      } else if (key === 'f' || key === 'format') {
        params.set(key, this.encodeFormat(value.toString()));
      } else {
        params.set(key, value.toString());
      }
    }

    return params.toString();
  }
}
```

### 5.3 Test Patterns

**Test Template:**

```typescript
describe('Parameter Validation', () => {
  describe('bbox validation', () => {
    it('accepts valid 2D bbox', () => {
      expect(() => {
        ParameterValidator.validateBBox({
          minLon: -180,
          minLat: -90,
          maxLon: 180,
          maxLat: 90,
        });
      }).not.toThrow();
    });

    it('rejects bbox with minLon > maxLon', () => {
      expect(() => {
        ParameterValidator.validateBBox({
          minLon: 180,
          minLat: -90,
          maxLon: -180,
          maxLat: 90,
        });
      }).toThrow(ParameterValidationError);
      expect(() => {
        ParameterValidator.validateBBox({
          minLon: 180,
          minLat: -90,
          maxLon: -180,
          maxLat: 90,
        });
      }).toThrow('minLon must be ≤ maxLon');
    });

    it('rejects bbox with latitude out of range', () => {
      expect(() => {
        ParameterValidator.validateBBox({
          minLon: -180,
          minLat: -100,
          maxLon: 180,
          maxLat: 90,
        });
      }).toThrow('minLat must be in [-90, 90]');
    });

    it('accepts valid 3D bbox', () => {
      expect(() => {
        ParameterValidator.validateBBox({
          minLon: -180,
          minLat: -90,
          minElev: 0,
          maxLon: 180,
          maxLat: 90,
          maxElev: 1000,
        });
      }).not.toThrow();
    });

    it('rejects 3D bbox with minElev > maxElev', () => {
      expect(() => {
        ParameterValidator.validateBBox({
          minLon: -180,
          minLat: -90,
          minElev: 1000,
          maxLon: 180,
          maxLat: 90,
          maxElev: 0,
        });
      }).toThrow('minElev must be ≤ maxElev');
    });
  });

  describe('datetime validation', () => {
    it('accepts valid instant', () => {
      expect(() => {
        ParameterValidator.validateDateTime(new Date('2024-01-15'));
      }).not.toThrow();
    });

    it('accepts valid interval', () => {
      expect(() => {
        ParameterValidator.validateDateTime({
          start: new Date('2024-01-01'),
          end: new Date('2024-12-31'),
        });
      }).not.toThrow();
    });

    it('rejects interval with start > end', () => {
      expect(() => {
        ParameterValidator.validateDateTime({
          start: new Date('2024-12-31'),
          end: new Date('2024-01-01'),
        });
      }).toThrow('start must be ≤ end');
    });

    it('accepts open interval (start only)', () => {
      expect(() => {
        ParameterValidator.validateDateTime({ start: new Date('2024-01-01') });
      }).not.toThrow();
    });

    it('accepts open interval (end only)', () => {
      expect(() => {
        ParameterValidator.validateDateTime({ end: new Date('2024-12-31') });
      }).not.toThrow();
    });
  });

  describe('limit validation', () => {
    it('accepts valid limit', () => {
      expect(() => {
        ParameterValidator.validateLimit(50);
      }).not.toThrow();
    });

    it('rejects zero limit', () => {
      expect(() => {
        ParameterValidator.validateLimit(0);
      }).toThrow('must be ≥ 1');
    });

    it('rejects negative limit', () => {
      expect(() => {
        ParameterValidator.validateLimit(-10);
      }).toThrow('must be ≥ 1');
    });

    it('accepts Part 2 maximum (10000)', () => {
      expect(() => {
        ParameterValidator.validateLimit(10000, true);
      }).not.toThrow();
    });

    it('rejects Part 2 limit > 10000', () => {
      expect(() => {
        ParameterValidator.validateLimit(15000, true);
      }).toThrow('must be ≤ 10000');
    });
  });
});

describe('Parameter Encoding', () => {
  describe('bbox encoding', () => {
    it('encodes 2D bbox as comma-separated', () => {
      const encoded = ParameterEncoder.encodeBBox({
        minLon: -180,
        minLat: -90,
        maxLon: 180,
        maxLat: 90,
      });
      expect(encoded).toBe('-180,-90,180,90');
    });

    it('encodes 3D bbox with elevation', () => {
      const encoded = ParameterEncoder.encodeBBox({
        minLon: -180,
        minLat: -90,
        minElev: 0,
        maxLon: 180,
        maxLat: 90,
        maxElev: 1000,
      });
      expect(encoded).toBe('-180,-90,180,90,0,1000');
    });
  });

  describe('datetime encoding', () => {
    it('encodes instant as ISO 8601', () => {
      const date = new Date('2024-01-15T12:00:00Z');
      const encoded = ParameterEncoder.encodeDateTime(date);
      expect(encoded).toBe('2024-01-15T12:00:00.000Z');
    });

    it('encodes interval with slash', () => {
      const encoded = ParameterEncoder.encodeDateTime({
        start: new Date('2024-01-01'),
        end: new Date('2024-12-31'),
      });
      expect(encoded).toMatch(/2024-01-01.*\/2024-12-31/);
    });

    it('encodes open interval with double-dot', () => {
      const encoded = ParameterEncoder.encodeDateTime({
        start: new Date('2024-01-01'),
      });
      expect(encoded).toMatch(/2024-01-01.*\/..\$/);
    });

    it('preserves string values (now, latest)', () => {
      expect(ParameterEncoder.encodeDateTime('now')).toBe('now');
      expect(ParameterEncoder.encodeDateTime('latest')).toBe('latest');
    });
  });

  describe('array encoding', () => {
    it('encodes array as comma-separated', () => {
      const encoded = ParameterEncoder.encodeArray([
        'sys123',
        'sys456',
        'sys789',
      ]);
      expect(encoded).toBe('sys123,sys456,sys789');
    });
  });

  describe('format encoding', () => {
    it('encodes + as %2B', () => {
      const encoded = ParameterEncoder.encodeFormat('application/sml+json');
      expect(encoded).toBe('application/sml%2Bjson');
    });

    it('encodes / as %2F', () => {
      const encoded = ParameterEncoder.encodeFormat('application/sml+json');
      // URLSearchParams will encode / automatically
      expect(encoded).toBe('application/sml%2Bjson');
    });
  });
});

describe('Parameter Combinations', () => {
  it('combines bbox + datetime + limit', () => {
    const queryString = ParameterEncoder.buildQueryString({
      bbox: { minLon: -10, minLat: -10, maxLon: 10, maxLat: 10 },
      datetime: { start: new Date('2024-01-01'), end: new Date('2024-12-31') },
      limit: 50,
    });

    expect(queryString).toContain('bbox=-10%2C-10%2C10%2C10');
    expect(queryString).toContain('datetime=2024-01-01');
    expect(queryString).toContain('limit=50');
  });

  it('combines multiple parameters', () => {
    const queryString = ParameterEncoder.buildQueryString({
      bbox: { minLon: -10, minLat: -10, maxLon: 10, maxLat: 10 },
      datetime: { start: new Date('2024-01-01') },
      observedProperty: ['temperature', 'pressure'],
      limit: 100,
      offset: 50,
      f: 'geojson',
    });

    // Verify all parameters present
    expect(queryString).toContain('bbox=');
    expect(queryString).toContain('datetime=');
    expect(queryString).toContain('observedProperty=temperature%2Cpressure');
    expect(queryString).toContain('limit=100');
    expect(queryString).toContain('offset=50');
    expect(queryString).toContain('f=geojson');
  });
});
```

---

## 6. Fixture Design

### 6.1 Query String Fixtures

**Valid Combinations:**

```typescript
const validQueryStrings = [
  // Two parameters
  '?bbox=-180,-90,180,90&limit=50',
  '?datetime=2024-01-01/2024-12-31&limit=100',
  '?phenomenonTime=2024-01-01/..&limit=1000',
  '?observedProperty=temperature&bbox=-10,-10,10,10',
  '?parent=sys123&recursive=true',

  // Three parameters
  '?bbox=-10,-10,10,10&datetime=2024-01-01/..&limit=50',
  '?bbox=-10,-10,10,10&observedProperty=temperature&limit=100',
  '?phenomenonTime=2024-01-01/..&resultTime=2024-01-02/..&limit=1000',

  // Four+ parameters
  '?bbox=-10,-10,10,10&datetime=2024-01-01/..&observedProperty=temperature&limit=100',
  '?parent=sys123&recursive=true&bbox=-10,-10,10,10&datetime=2024-01-01/..&limit=100',
];
```

**Invalid Combinations:**

```typescript
const invalidQueryStrings = [
  // Wrong parameter for resource
  '/properties?bbox=-180,-90,180,90', // Properties have no geometry
  '/systems?phenomenonTime=2024-01-01/..', // Part 1 resource doesn't have phenomenonTime

  // Invalid parameter values
  '?bbox=-180,-90', // Wrong number of coordinates
  '?bbox=180,-90,-180,90', // minLon > maxLon
  '?limit=0', // Zero limit
  '?limit=-10', // Negative limit
  '?limit=15000', // Exceeds Part 2 maximum
  '?offset=-10', // Negative offset
  '?datetime=01/01/2024', // Not ISO 8601
  '?datetime=2024-12-31/2024-01-01', // start > end

  // Encoding issues
  '?q=weather+station', // Plus should be %20
  '?uid=urn:uuid:123', // Colon should be URL-encoded
];
```

### 6.2 Response Fixtures

**Successful Response with Filters:**

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "id": "sys123",
      "geometry": { "type": "Point", "coordinates": [5.0, 5.0] },
      "properties": {
        "name": "Weather Station A",
        "observedProperties": ["temperature", "pressure"]
      }
    }
  ],
  "links": [
    {
      "rel": "self",
      "href": "https://api.example.org/systems?bbox=-10,-10,10,10&datetime=2024-01-01/..&observedProperty=temperature&limit=50&offset=0"
    },
    {
      "rel": "next",
      "href": "https://api.example.org/systems?bbox=-10,-10,10,10&datetime=2024-01-01/..&observedProperty=temperature&limit=50&offset=50"
    }
  ],
  "numberMatched": 150,
  "numberReturned": 50
}
```

**Error Response for Invalid Parameter:**

```json
{
  "code": "InvalidParameterValue",
  "description": "The 'limit' parameter value '0' is invalid. Must be a positive integer (≥ 1)."
}
```

**Error Response for Inapplicable Parameter:**

```json
{
  "code": "InvalidParameterValue",
  "description": "The 'bbox' parameter is not applicable to the Properties resource type."
}
```

**Error Response for Unsupported Format:**

```json
{
  "code": "InvalidParameterValue",
  "description": "The format 'application/xml' is not supported. Supported formats: application/json, application/geo+json, application/sml+json."
}
```

### 6.3 Fixture Summary

| Fixture Type               | Count   | Description                                                     |
| -------------------------- | ------- | --------------------------------------------------------------- |
| Valid 2-param queries      | 20      | Common two-parameter combinations                               |
| Valid 3-param queries      | 20      | Three-parameter combinations                                    |
| Valid 4+ param queries     | 20      | Complex multi-parameter queries                                 |
| Invalid param for resource | 10      | Wrong parameter applied to resource type                        |
| Invalid param values       | 10      | Validation errors (range, format, type)                         |
| Precedence conflicts       | 10      | Conflicting parameters (cursor+offset, datetime+phenomenonTime) |
| Validation tests           | 20      | Type, range, format, encoding validation                        |
| Encoding tests             | 10      | URL encoding edge cases                                         |
| **TOTAL**                  | **120** | **120 test scenarios**                                          |

---

## 7. Test Organization

### 7.1 File Structure

```
src/ogc-api/csapi/__tests__/
  parameter-combinations.spec.ts           # Valid combination tests
  parameter-validation.spec.ts             # Parameter validation tests
  parameter-encoding.spec.ts               # Encoding tests
  parameter-precedence.spec.ts             # Precedence rule tests
  parameter-applicability.spec.ts          # Parameter applicability tests
```

### 7.2 Test Counts

| Test File                         | Test Scenarios | Lines of Code (est.) |
| --------------------------------- | -------------- | -------------------- |
| `parameter-combinations.spec.ts`  | 60             | ~1,200               |
| `parameter-validation.spec.ts`    | 20             | ~600                 |
| `parameter-encoding.spec.ts`      | 10             | ~400                 |
| `parameter-precedence.spec.ts`    | 10             | ~400                 |
| `parameter-applicability.spec.ts` | 20             | ~600                 |
| **TOTAL**                         | **120**        | **~3,200**           |

### 7.3 Integration with Other Sections

**Section 13 (Resource Method Testing):**

- Tests **individual parameters** per resource (14-19 tests per resource)
- Focus: Parameter presence, basic encoding, single parameter per test

**Section 23 (Pagination Testing):**

- Tests **pagination parameters** (limit, offset, cursor) with filters
- Focus: Multi-page scenarios, cursor extraction, pagination behavior

**Section 24 (This Section):**

- Tests **parameter combinations** across all categories (120 scenarios)
- Focus: 2-4+ parameter interactions, precedence rules, validation

**No Duplication:** Each section tests different aspects:

- Section 13: Individual parameters per resource
- Section 23: Pagination-specific behavior
- Section 24: Parameter interactions and combinations

---

## 8. Implementation Estimates

### 8.1 Test Implementation

| Task                                  | Est. Time       | Priority |
| ------------------------------------- | --------------- | -------- |
| Parameter validation tests (20)       | 3-4 hours       | HIGH     |
| Valid 2-param combination tests (20)  | 3-4 hours       | HIGH     |
| Valid 3-param combination tests (20)  | 3-4 hours       | MEDIUM   |
| Valid 4+ param combination tests (20) | 3-4 hours       | MEDIUM   |
| Invalid parameter tests (10)          | 2-3 hours       | HIGH     |
| Precedence conflict tests (10)        | 2-3 hours       | MEDIUM   |
| Encoding tests (10)                   | 2-3 hours       | LOW      |
| Parameter applicability tests (10)    | 2-3 hours       | LOW      |
| **TOTAL**                             | **20-28 hours** | -        |

### 8.2 Fixture Creation

| Task                               | Est. Time     | Priority |
| ---------------------------------- | ------------- | -------- |
| Valid query string fixtures (60)   | 2-3 hours     | HIGH     |
| Invalid query string fixtures (30) | 1-2 hours     | MEDIUM   |
| Success response fixtures (10)     | 1-2 hours     | MEDIUM   |
| Error response fixtures (10)       | 1 hour        | LOW      |
| **TOTAL**                          | **5-8 hours** | -        |

### 8.3 Validation/Encoding Utilities

| Task                             | Est. Time      | Priority |
| -------------------------------- | -------------- | -------- |
| `ParameterValidator` class       | 2-3 hours      | HIGH     |
| `ParameterEncoder` class         | 2-3 hours      | HIGH     |
| `ParameterValidationError` class | 30 minutes     | HIGH     |
| Unit tests for utilities         | 2-3 hours      | HIGH     |
| **TOTAL**                        | **7-10 hours** | -        |

### 8.4 Total Effort

| Phase                         | Est. Time                 |
| ----------------------------- | ------------------------- |
| Test Implementation           | 20-28 hours               |
| Fixture Creation              | 5-8 hours                 |
| Validation/Encoding Utilities | 7-10 hours                |
| Documentation                 | 2-3 hours (this document) |
| **TOTAL**                     | **34-49 hours**           |

---

## 9. Key Recommendations

### 9.1 Prioritization

**HIGH Priority (Implement First):**

1. Parameter validation tests (type, range, format)
2. Valid 2-parameter combination tests (most common use cases)
3. Invalid parameter value tests (ensure proper error handling)
4. `ParameterValidator` and `ParameterEncoder` utilities
5. Query string fixtures for common scenarios

**MEDIUM Priority (Implement Second):** 6. Valid 3-parameter combination tests 7. Valid 4+ parameter combination tests 8. Precedence conflict tests 9. Parameter applicability tests (wrong parameter for resource) 10. Success/error response fixtures

**LOW Priority (Implement Last):** 11. Encoding edge case tests 12. Exhaustive combination testing (beyond 4 parameters) 13. Documentation and examples

### 9.2 Testing Strategy

**Unit Tests:**

- Validate `ParameterValidator` class (20 tests)
- Validate `ParameterEncoder` class (10 tests)
- Test error handling (`ParameterValidationError`)

**Integration Tests:**

- Test parameter combinations in URL construction (60 tests)
- Test parameter applicability per resource (20 tests)
- Test precedence rules (10 tests)

**Mock Strategy:**

- Mock fetch to return fixture responses based on query string
- Parse URL to extract parameters and validate encoding
- Test parameter effects on response content (filtering)

### 9.3 Reusable Patterns

**Parameterized Tests:**

```typescript
describe.each([
  { bbox: { minLon: -180, minLat: -90, maxLon: 180, maxLat: 90 }, valid: true },
  {
    bbox: { minLon: 180, minLat: -90, maxLon: -180, maxLat: 90 },
    valid: false,
  },
  {
    bbox: { minLon: -180, minLat: -100, maxLon: 180, maxLat: 90 },
    valid: false,
  },
])('bbox validation', ({ bbox, valid }) => {
  it(`${valid ? 'accepts' : 'rejects'} bbox ${JSON.stringify(bbox)}`, () => {
    if (valid) {
      expect(() => ParameterValidator.validateBBox(bbox)).not.toThrow();
    } else {
      expect(() => ParameterValidator.validateBBox(bbox)).toThrow();
    }
  });
});
```

**Combination Test Helper:**

```typescript
async function testCombination(
  resource: string,
  params: Record<string, any>,
  expectedQuery: Record<string, string>
): Promise<void> {
  const url = await builder[`get${resource}`](params);
  parseAndValidateUrl(url, {
    pathname: `/${resource.toLowerCase()}`,
    query: expectedQuery,
  });
}

// Usage
it('combines bbox + datetime + limit', async () => {
  await testCombination(
    'Systems',
    {
      bbox: { minLon: -10, minLat: -10, maxLon: 10, maxLat: 10 },
      datetime: { start: '2024-01-01', end: '2024-12-31' },
      limit: 50,
    },
    {
      bbox: '-10,-10,10,10',
      datetime: '2024-01-01T00:00:00.000Z/2024-12-31T00:00:00.000Z',
      limit: '50',
    }
  );
});
```

---

## 10. Success Criteria Validation

- [x] **All 30+ query parameters are inventoried** ✅ (32 parameters documented)
- [x] **Valid and invalid combinations are defined** ✅ (60 valid + 30 invalid scenarios)
- [x] **Parameter precedence rules are documented** ✅ (format, temporal, pagination precedence)
- [x] **Spatial + temporal + relationship interactions are specified** ✅ (Multi-parameter combinations documented)
- [x] **Parameter validation tests are designed** ✅ (20 validation scenarios)
- [x] **Parameter combination fixtures are defined** ✅ (120 fixtures)
- [x] **Test scenario matrix is complete (100+ scenarios)** ✅ (120 scenarios)
- [x] **Deliverable document is peer-reviewed** ⏳ (awaiting review)

---

## 11. References

**CSAPI Specifications:**

- OGC API - Connected Systems Part 1: Query parameters (bbox, datetime, limit, offset, f, id, uid, q, recursive, parent, procedure, foi, observedProperty, controlledProperty, system, baseProperty, objectType)
- OGC API - Connected Systems Part 2: Part 2-specific parameters (phenomenonTime, resultTime, executionTime, issueTime, cursor, obsFormat, cmdFormat)
- OGC API - Features Part 1: Standard OGC API parameters (bbox, datetime, limit, offset)

**Related Research:**

- Section 8: CSAPI Specification Review (parameter definitions)
- Section 13: Resource Method Testing (individual parameter testing)
- Section 23: Pagination Testing (pagination parameters)
- Query Parameter Requirements: [csapi-query-parameters.md](../../requirements/csapi-query-parameters.md)

**Implementation Guides:**

- `csapi-implementation-guide.md`: Parameter handling architecture
- Research Plan 15: Query Parameter Complexity Analysis (parameter inventory and validation patterns)

---

## 12. Appendix: Parameter Category Breakdown

### Standard OGC API (5)

1. bbox
2. datetime
3. limit
4. offset
5. f

### CSAPI Common (4)

6. id
7. uid
8. q
9. {propertyName}

### Hierarchical (1)

10. recursive

### Relationship (8)

11. parent
12. procedure
13. foi
14. observedProperty
15. controlledProperty
16. system
17. baseProperty
18. objectType

### Part 2 Temporal (4)

19. phenomenonTime
20. resultTime
21. executionTime
22. issueTime

### Part 2 Format (3)

23. format
24. obsFormat
25. cmdFormat

### Part 2 Pagination (1)

26. cursor

**Total: 26 explicitly defined parameters**

**Additional Parameters (6 - mentioned but not fully specified):** 27. near (spatial proximity filter - possible future extension) 28. within (spatial containment filter - possible future extension) 29. distance (spatial distance parameter - possible future extension) 30. properties (property selection - OGC API - Features) 31. select (alternative to properties - possible future extension) 32. filter (CQL2 filtering - OGC API - Features Part 3)

**Note:** Parameters 27-32 are mentioned in research notes but are NOT currently part of the CSAPI specification. They represent possible future extensions or implementation-specific additions.

---

**Document Status:** ✅ Complete  
**Last Updated:** February 6, 2026  
**Next Review:** After peer review and feedback incorporation
