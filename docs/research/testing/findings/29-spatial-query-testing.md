# Section 29: Spatial Query Testing Strategy

> ⚠️ **REVIEW NOTICE — MEDIUM (M7): Same `response.ok` Pattern as Doc 28**
>
> **Phase 2E Review | Issues: M7 | Anti-Pattern: AP1**
>
> This document is ~65% client-oriented — milder than Docs 27-28. The URL construction tests (`response.requestUrl.toContain('bbox=...')`) are correctly client-oriented, and the bbox validation/encoding logic (Sections 7.3-7.4) is genuinely testable client code. However, the same `expect(response.ok).toBe(true)` pattern from Doc 28 appears throughout Section 4, and table descriptions like "Returns resources in North America" describe server filtering behavior.
>
> **What's usable:** Bbox URL construction, coordinate validation (Section 7.3), bbox encoding (Section 7.4), antimeridian handling (Section 8), edge case analysis (Section 3).
>
> **What to fix:** Remove `response.ok` assertions; retain `requestUrl` assertions; add tests for `validateBbox()` and `encodeBbox()` utility functions.
>
> See also: [Phase 2E Review Report](../review/phase-2e-advanced-scenarios-category.md)

**Research Plan:** [Research Plan 29: Spatial Query Testing Strategy](../research-plans/29-spatial-query-testing.md)

**Research Questions:** 6 core questions about bbox format, geometry intersection, CRS handling, spatial edge cases, validation errors, and fixtures.

**Methodology:** 7-phase systematic analysis (Phase 1: Spatial Parameter Specification Analysis → Phase 2: CRS and Coordinate System Analysis → Phase 3: Spatial Edge Case Analysis → Phase 4: Upstream Spatial Testing Analysis → Phase 5: Test Scenario Design → Phase 6: Fixture Design → Phase 7: Synthesis)

**Research Time:** 210 minutes (3.5 hours) – February 6, 2026

**Primary Source(s):**

- [Query Parameter Requirements](../../requirements/csapi-query-parameters.md)
- [CSAPI Part 1 Specification](https://docs.ogc.org/is/23-001/23-001.html)
- [GeoJSON RFC 7946](https://datatracker.ietf.org/doc/html/rfc7946)
- [OGC API - Features Part 1](https://docs.ogc.org/is/17-069r3/17-069r3.html)

**Supporting Resources:**

- Section 24: [Query Parameter Combination Testing](24-query-parameter-combination-testing.md) (parameter interactions)
- Section 11: [GeoJSON Testing Requirements](11-geojson-testing-requirements.md) (spatial structures)
- Section 8: [CSAPI Specification Review](08-csapi-specification-review.md) (spatial definitions)
- Section 23: [Pagination Testing Strategy](23-pagination-testing.md) (spatial + pagination)

**Document Purpose:** Testing strategy for spatial query parameters (bbox) with geometry scenarios, CRS handling, and edge cases including antimeridian crossing and polar regions.

---

## Executive Summary

This document defines comprehensive testing requirements for CSAPI spatial query parameters, focusing on bbox (bounding box) queries, coordinate reference system handling, spatial edge cases (antimeridian, polar regions), and validation scenarios. Spatial queries are critical for Part 1 resources with geometry (Systems, Deployments, Procedures, SamplingFeatures).

### Key Findings

**Spatial Parameters (2 total):**

- **bbox** - Bounding box spatial filter (OGC API - Common)
- **geom** - Geometry intersection filter (WKT or GeoJSON) - **NOT SUPPORTED in CSAPI initially**

**Bbox Format:**

- **2D:** `bbox=minLon,minLat,maxLon,maxLat` (4 values)
- **3D:** `bbox=minLon,minLat,minElev,maxLon,maxLat,maxElev` (6 values)

**Coordinate Reference System:**

- **Default CRS:** WGS 84 (CRS84) - longitude, latitude order
- **Only CRS:** CSAPI uses WGS 84 exclusively (no CRS transformation required)
- **Coordinate Ranges:** Longitude [-180, 180], Latitude [-90, 90]

**Testing Priorities:**

- **CRITICAL:** Basic bbox queries, coordinate validation, latitude/longitude ranges, min ≤ max validation
- **HIGH:** 3D bbox (with elevation), point bbox (min = max), bbox + pagination
- **MEDIUM:** Edge cases (polar regions, coordinate precision), empty result handling
- **LOW:** Antimeridian crossing (**INVALID** in CSAPI - server returns 400)

**Fixture Requirements:** ~40 fixtures

- Bbox query strings: ~15 fixtures (2D, 3D, edge cases)
- Spatial response fixtures: ~15 fixtures
- Spatial error fixtures: ~10 fixtures

**Estimated Test Implementation:** 650-850 lines

- Basic bbox tests: 150-200 lines (10 tests)
- 3D bbox tests: 90-120 lines (6 tests)
- Validation error tests: 120-160 lines (8 tests)
- Edge case tests: 90-120 lines (6 tests)
- Bbox + pagination tests: 60-80 lines (4 tests)
- Bbox + temporal tests: 90-120 lines (6 tests)
- Point bbox tests: 50-70 lines (3 tests)

**Key Testing Challenges:**

1. **Antimeridian handling** - CSAPI declares minLon > maxLon **INVALID** (400 error), unlike some OGC APIs
2. **Coordinate range validation** - Latitude [-90, 90], Longitude [-180, 180]
3. **3D bbox** - Elevation handling (meters above WGS 84 ellipsoid)
4. **Edge cases** - Polar regions, point bbox (min = max), coordinate precision

### Highest Rejection Risk

Spatial query testing is **MEDIUM RISK** because:

- **Limited scope** - Only bbox parameter (no geom parameter initially)
- **Single CRS** - WGS 84 only (no CRS transformation needed)
- **No antimeridian** - Explicitly invalid in CSAPI (simplifies testing)
- **Standard patterns** - Follows OGC API - Features bbox patterns

**Mitigation:** Comprehensive bbox validation, coordinate range checks, and edge case coverage with ~40 fixtures.

---

## 1. Spatial Parameter Inventory

### 1.1 Spatial Parameter Matrix

| Parameter    | Applies To                                         | Format                                        | CRS            | Semantics                                            | Support Status                 | Priority     |
| ------------ | -------------------------------------------------- | --------------------------------------------- | -------------- | ---------------------------------------------------- | ------------------------------ | ------------ |
| **bbox**     | Systems, Deployments, Procedures, SamplingFeatures | minLon,minLat,maxLon,maxLat[,minElev,maxElev] | WGS 84 (CRS84) | Filters resources whose geometry intersects bbox     | ✅ Supported                   | **CRITICAL** |
| **geom**     | Systems, Deployments, Procedures, SamplingFeatures | WKT or GeoJSON geometry                       | WGS 84 (CRS84) | Filters resources whose geometry intersects geometry | ❌ Not initially supported     | FUTURE       |
| **bbox-crs** | All spatial resources                              | CRS URI                                       | N/A            | Specifies bbox CRS (optional)                        | ❌ Not supported (WGS 84 only) | N/A          |

**Note:** This strategy focuses exclusively on **bbox parameter** as it is the only spatial parameter initially supported in CSAPI.

### 1.2 Resource-Spatial Parameter Mapping

| Resource Type        | Spatial Parameters Supported | Geometry Required      | Primary Use Cases                                    |
| -------------------- | ---------------------------- | ---------------------- | ---------------------------------------------------- |
| **Systems**          | bbox                         | Optional (may be null) | Filter systems by location (sensors, platforms)      |
| **Deployments**      | bbox                         | Optional (may be null) | Filter deployments by location                       |
| **Procedures**       | bbox                         | Optional (may be null) | Filter procedures by applicable area                 |
| **SamplingFeatures** | bbox                         | Optional (may be null) | Filter sampling features by location                 |
| **DataStreams**      | ❌ No spatial queries        | N/A                    | DataStreams inherit geometry from parent System      |
| **ControlStreams**   | ❌ No spatial queries        | N/A                    | ControlStreams inherit geometry from parent System   |
| **Observations**     | ❌ No spatial queries        | N/A                    | Observations inherit geometry from DataStream/System |
| **Commands**         | ❌ No spatial queries        | N/A                    | Commands inherit geometry from ControlStream/System  |

**Spatial Query Behavior:**

- **Intersection semantics:** Returns resources whose geometry **intersects** the bbox (not just contained within)
- **Null geometry:** Resources with null geometry are excluded from spatial queries
- **Empty result:** Valid bbox with no intersecting resources returns empty FeatureCollection

### 1.3 Bbox Parameter Specification

**Format:** `bbox=minLon,minLat,maxLon,maxLat[,minElev,maxElev]`

**2D Bounding Box (4 values):**

```
GET /systems?bbox=-180,-90,180,90
```

- minLon: Minimum longitude (western edge)
- minLat: Minimum latitude (southern edge)
- maxLon: Maximum longitude (eastern edge)
- maxLat: Maximum latitude (northern edge)

**3D Bounding Box (6 values):**

```
GET /systems?bbox=-180,-90,0,180,90,1000
```

- minLon: Minimum longitude
- minLat: Minimum latitude
- minElev: Minimum elevation (meters above WGS 84 ellipsoid)
- maxLon: Maximum longitude
- maxLat: Maximum latitude
- maxElev: Maximum elevation (meters above WGS 84 ellipsoid)

**Coordinate Order:**

- CSAPI uses **WGS 84 (CRS84)**: Longitude, Latitude order
- This is **GeoJSON default** (RFC 7946)
- Different from EPSG:4326 which uses Latitude, Longitude order

**Validation Rules:**

- minLon ≤ maxLon (**MUST** - antimeridian crossing with minLon > maxLon is **INVALID**)
- minLat ≤ maxLat (**MUST**)
- minElev ≤ maxElev (**MUST** if provided)
- Latitude range: **-90 to 90** (inclusive)
- Longitude range: **-180 to 180** (inclusive)
- Elevation: Any numeric value (meters above WGS 84 ellipsoid)

**Error Handling:**

- Invalid coordinate range → **400 Bad Request**
- minLon > maxLon (antimeridian) → **400 Bad Request**
- minLat > maxLat → **400 Bad Request**
- Wrong number of values (not 4 or 6) → **400 Bad Request**
- Non-numeric values → **400 Bad Request**

---

## 2. Coordinate Reference System (CRS) Specification

### 2.1 Default and Only CRS: WGS 84 (CRS84)

**CRS Details:**

- **Name:** World Geodetic System 1984 (WGS 84)
- **EPSG Code:** EPSG:4326 (latitude, longitude order in GIS)
- **GeoJSON Identifier:** CRS84 / OGC:CRS84 (longitude, latitude order)
- **Coordinate Order:** **Longitude, Latitude** (CRS84 convention, RFC 7946 default)

**CSAPI Position:**

- **Only CRS supported:** WGS 84 / CRS84
- **No CRS negotiation:** No bbox-crs parameter support
- **No CRS transformation:** Client and server both use WGS 84
- **Inherits RFC 7946:** Alternative CRS removed from RFC 7946

**Coordinate Ranges:**

- **Longitude:** -180° to +180° (Western Hemisphere negative, Eastern positive)
- **Latitude:** -90° to +90° (Southern Hemisphere negative, Northern positive)
- **Altitude:** Meters above WGS 84 ellipsoid (not orthometric height)

**Special Locations:**

- **Prime Meridian:** 0° longitude (Greenwich, UK)
- **Equator:** 0° latitude
- **International Date Line:** ±180° longitude
- **North Pole:** +90° latitude
- **South Pole:** -90° latitude

### 2.2 Why No CRS Transformation

**RFC 7946 Rationale:**

- RFC 7946 Section 4: "The use of alternative coordinate reference systems was specified in [GeoJSON 2008] but... removed from this version of the specification."
- **Reason:** Interoperability - single CRS ensures consistent interpretation

**CSAPI Inheritance:**

- CSAPI Part 1 inherits RFC 7946 constraint
- All GeoJSON uses WGS 84 / CRS84
- No bbox-crs parameter defined

**Client Library Implications:**

- **No CRS transformation needed** in client library
- If application uses different CRS internally (e.g., Web Mercator EPSG:3857), **application is responsible** for transformation
- Client library assumes all coordinates are WGS 84 / CRS84

### 2.3 Coordinate Order: Longitude, Latitude

**Bbox Coordinate Order:**

```
bbox=minLon,minLat,maxLon,maxLat
bbox=<longitude>,<latitude>,<longitude>,<latitude>
```

**Example - San Francisco Bay Area:**

```
bbox=-122.5,37.5,-122.0,38.0
      ^lon   ^lat  ^lon   ^lat
```

**Common Mistake:**
Many GIS systems use **latitude, longitude** order (EPSG:4326), but:

- **GeoJSON (RFC 7946)** uses **longitude, latitude** (CRS84)
- **CSAPI bbox** uses **longitude, latitude** (follows GeoJSON)

**Coordinate Range Mnemonics:**

- **Longitude (-180 to 180):** "Wraps around the globe" (like time zones)
- **Latitude (-90 to 90):** "North and South poles are the limits"

---

## 3. Spatial Edge Cases

### 3.1 Antimeridian Crossing (Date Line)

**CSAPI Position:** Antimeridian crossing is **INVALID** - server returns **400 Bad Request**

**What is Antimeridian Crossing:**

- International Date Line at ±180° longitude
- Some spatial regions cross date line (e.g., Fiji, Kiribati, Samoa)
- Bbox where minLon > maxLon represents date line crossing

**Invalid Examples:**

```
bbox=170,-10,-170,10
// minLon=170 > maxLon=-170 → INVALID (400 Bad Request)

bbox=175,-20,-175,20
// minLon=175 > maxLon=-175 → INVALID (400 Bad Request)
```

**CSAPI Validation Rule:**

- **minLon ≤ maxLon** (MUST)
- If minLon > maxLon → **400 Bad Request**

**How to Query Antimeridian Regions:**
Since CSAPI does not support antimeridian crossing in bbox parameter, clients must:

1. **Split into two queries:**
   - Query 1: `bbox=170,-10,180,10` (western side, up to date line)
   - Query 2: `bbox=-180,-10,-170,10` (eastern side, from date line)
   - Client merges results
2. **Use full longitude range:** `bbox=-180,-10,180,10` (entire world longitude-wise, loses precision)

**Testing Implication:**

- Test that minLon > maxLon returns **400 Bad Request**
- Test error message indicates antimeridian crossing invalid
- Document workaround for clients

**Comparison to Other OGC APIs:**

- Some OGC API implementations **DO** support antimeridian crossing (minLon > maxLon)
- CSAPI explicitly **DOES NOT** support this (follows stricter interpretation)

### 3.2 Polar Regions

**North Pole:** Latitude +90°  
**South Pole:** Latitude -90°

**Valid Polar Bbox Examples:**

```
// Arctic region (north of 85° latitude)
bbox=-180,85,180,90

// Antarctic region (south of -85° latitude)
bbox=-180,-90,180,-85

// Small region near North Pole
bbox=-10,89,10,90
```

**Polar Region Considerations:**

- **Longitude wrapping:** Near poles, longitude changes rapidly (small geographic distance)
- **Coordinate precision:** At poles, longitude is undefined (all longitudes converge)
- **Bbox interpretation:** Rectangular bbox in WGS 84 may not represent intended area near poles

**Testing Approach:**

- Test bbox with maxLat = 90 (North Pole)
- Test bbox with minLat = -90 (South Pole)
- Test narrow latitude range near poles (e.g., 89° to 90°)
- Verify server handles polar coordinates correctly

**Polar Bbox Edge Cases:**

- **Point at pole:** `bbox=-180,90,180,90` (North Pole, entire longitude range)
- **Single degree band:** `bbox=-180,89,180,90` (Arctic cap within 1° of pole)

### 3.3 Point Bounding Box (min = max)

**Specification:** Point bbox where minLon = maxLon and minLat = maxLat is **VALID**

**Example:**

```
bbox=-122.4194,37.7749,-122.4194,37.7749
// San Francisco City Hall (exact point)
```

**Semantics:**

- Represents a **single point** query
- Returns resources whose geometry intersects or contains this point
- **Point geometry:** Resource with exact point coordinates should match
- **Polygon geometry:** Resource containing this point should match
- **LineString geometry:** Resource passing through this point should match

**Testing:**

- Test point bbox returns correct results
- Test point bbox vs instant queries (semantically equivalent)
- Test point bbox with different geometry types (Point, LineString, Polygon)

### 3.4 Global Bounding Box

**Example:**

```
bbox=-180,-90,180,90
// Entire world
```

**Semantics:**

- Represents **entire Earth** coverage
- Returns **all resources** with non-null geometry
- Equivalent to no bbox filter (if all resources have geometry)

**Testing:**

- Test global bbox returns all spatial resources
- Test global bbox excludes resources with null geometry
- Test global bbox + other filters (e.g., temporal) combines correctly

### 3.5 Empty Bounding Box (min = max for both axes)

**Example:**

```
bbox=-122.4194,37.7749,-122.4194,37.7749
// Zero-area bbox (single point)
```

**Semantics:**

- This is a **point bbox** (see Section 3.3)
- **NOT** an empty bbox (would be invalid)
- Valid and should return resources intersecting the point

### 3.6 Coordinate Precision

**Issue:** Floating-point precision limits

**Example:**

```
bbox=-122.419416,37.774929,-122.419415,37.774930
// Microsecond-level precision (sub-meter accuracy)
```

**Considerations:**

- WGS 84 precision: ~1 meter at equator requires 5-6 decimal places
- 1° longitude ≈ 111 km at equator (varies by latitude)
- 1° latitude ≈ 111 km (constant)
- 0.00001° ≈ 1.1 meters
- 0.000001° ≈ 11 cm

**Testing:**

- Test bbox with high-precision coordinates (6+ decimal places)
- Test bbox with integer coordinates (low precision)
- Test coordinate rounding behavior

### 3.7 Coordinate Range Edge Cases

**Boundary Values:**

```
// Maximum longitude extent
bbox=-180,0,180,0
// Equator, full longitude range

// Maximum latitude extent
bbox=0,-90,0,90
// Prime meridian, full latitude range

// Single latitude line
bbox=-180,0,180,0
// Equator

// Single longitude line
bbox=0,-90,0,90
// Prime meridian
```

**Testing:**

- Test bbox with boundary values (-180, 180, -90, 90)
- Test bbox with coordinates at limits
- Test bbox with negative and positive coordinates

---

## 4. Spatial Query Test Scenarios

### 4.1 Basic Bbox Tests (10 tests)

> ⚠️ **REVIEW NOTICE (M7): `expect(response.ok).toBe(true)` Meaningless Against Fixtures**
>
> Same pattern as Doc 28: `response.ok` assertions only confirm the mock returns `ok: true`. The `expect(response.requestUrl).toContain('bbox=...')` assertions ARE client-oriented and should be retained. Table descriptions like "Returns resources in North America" describe server filtering behavior.
>
> **Retain:** `requestUrl` assertions verifying bbox URL encoding.
> **Remove:** `response.ok` assertions and server filtering descriptions.
> **Add:** Tests for `validateBbox()` and `encodeBbox()` from Section 7.

**Priority:** **CRITICAL**

| Test ID  | Scenario                        | Example Query                      | Expected Behavior                            | Lines |
| -------- | ------------------------------- | ---------------------------------- | -------------------------------------------- | ----- |
| BBOX-001 | Global bbox                     | `bbox=-180,-90,180,90`             | Returns all resources with non-null geometry | 15    |
| BBOX-002 | Regional bbox (North America)   | `bbox=-130,25,-60,50`              | Returns resources in North America           | 15    |
| BBOX-003 | City-scale bbox (San Francisco) | `bbox=-122.5,37.7,-122.3,37.9`     | Returns resources in SF area                 | 15    |
| BBOX-004 | Small bbox (neighborhood)       | `bbox=-122.42,37.77,-122.41,37.78` | Returns resources in ~1km² area              | 15    |
| BBOX-005 | Western Hemisphere              | `bbox=-180,-90,0,90`               | Returns resources in Western Hemisphere      | 15    |
| BBOX-006 | Eastern Hemisphere              | `bbox=0,-90,180,90`                | Returns resources in Eastern Hemisphere      | 15    |
| BBOX-007 | Northern Hemisphere             | `bbox=-180,0,180,90`               | Returns resources in Northern Hemisphere     | 15    |
| BBOX-008 | Southern Hemisphere             | `bbox=-180,-90,180,0`              | Returns resources in Southern Hemisphere     | 15    |
| BBOX-009 | Equatorial bbox                 | `bbox=-180,-10,180,10`             | Returns resources near equator (±10°)        | 15    |
| BBOX-010 | Prime Meridian bbox             | `bbox=-10,-90,10,90`               | Returns resources near Prime Meridian (±10°) | 15    |

**Test Implementation (~150-200 lines, 10 tests):**

```typescript
describe('Basic Bbox Queries', () => {
  it('accepts global bbox (entire world)', async () => {
    const response = await client.systems.list({
      bbox: { minLon: -180, minLat: -90, maxLon: 180, maxLat: 90 },
    });

    expect(response.ok).toBe(true);
    expect(response.requestUrl).toContain('bbox=-180%2C-90%2C180%2C90');
    // Returns all systems with non-null geometry
  });

  it('accepts regional bbox (North America)', async () => {
    const response = await client.systems.list({
      bbox: { minLon: -130, minLat: 25, maxLon: -60, maxLat: 50 },
    });

    expect(response.ok).toBe(true);
    expect(response.requestUrl).toContain('bbox=-130%2C25%2C-60%2C50');
    // Returns systems in North America region
  });

  it('accepts city-scale bbox (San Francisco)', async () => {
    const response = await client.systems.list({
      bbox: { minLon: -122.5, minLat: 37.7, maxLon: -122.3, maxLat: 37.9 },
    });

    expect(response.ok).toBe(true);
    expect(response.requestUrl).toContain('bbox=-122.5%2C37.7%2C-122.3%2C37.9');
  });

  it('accepts small bbox (neighborhood scale)', async () => {
    const response = await client.systems.list({
      bbox: { minLon: -122.42, minLat: 37.77, maxLon: -122.41, maxLat: 37.78 },
    });

    expect(response.ok).toBe(true);
    // Returns systems in ~1km² area
  });

  it('accepts Western Hemisphere bbox', async () => {
    const response = await client.systems.list({
      bbox: { minLon: -180, minLat: -90, maxLon: 0, maxLat: 90 },
    });

    expect(response.ok).toBe(true);
    expect(response.requestUrl).toContain('bbox=-180%2C-90%2C0%2C90');
  });

  it('accepts Eastern Hemisphere bbox', async () => {
    const response = await client.systems.list({
      bbox: { minLon: 0, minLat: -90, maxLon: 180, maxLat: 90 },
    });

    expect(response.ok).toBe(true);
    expect(response.requestUrl).toContain('bbox=0%2C-90%2C180%2C90');
  });

  it('accepts Northern Hemisphere bbox', async () => {
    const response = await client.systems.list({
      bbox: { minLon: -180, minLat: 0, maxLon: 180, maxLat: 90 },
    });

    expect(response.ok).toBe(true);
    expect(response.requestUrl).toContain('bbox=-180%2C0%2C180%2C90');
  });

  it('accepts Southern Hemisphere bbox', async () => {
    const response = await client.systems.list({
      bbox: { minLon: -180, minLat: -90, maxLon: 180, maxLat: 0 },
    });

    expect(response.ok).toBe(true);
    expect(response.requestUrl).toContain('bbox=-180%2C-90%2C180%2C0');
  });

  it('accepts equatorial bbox (±10 degrees)', async () => {
    const response = await client.systems.list({
      bbox: { minLon: -180, minLat: -10, maxLon: 180, maxLat: 10 },
    });

    expect(response.ok).toBe(true);
    // Returns systems within 10° of equator
  });

  it('accepts Prime Meridian bbox (±10 degrees)', async () => {
    const response = await client.systems.list({
      bbox: { minLon: -10, minLat: -90, maxLon: 10, maxLat: 90 },
    });

    expect(response.ok).toBe(true);
    // Returns systems within 10° of Prime Meridian
  });
});
```

### 4.2 3D Bbox Tests (6 tests)

**Priority:** HIGH

| Test ID     | Scenario           | Example Query                            | Expected Behavior                                      | Lines |
| ----------- | ------------------ | ---------------------------------------- | ------------------------------------------------------ | ----- |
| BBOX-3D-001 | 3D global bbox     | `bbox=-180,-90,0,180,90,1000`            | Returns resources between 0-1000m elevation            | 15    |
| BBOX-3D-002 | 3D regional bbox   | `bbox=-122.5,37.7,0,-122.3,37.9,500`     | Returns SF resources 0-500m elevation                  | 15    |
| BBOX-3D-003 | Below sea level    | `bbox=-180,-90,-500,180,90,0`            | Returns resources below sea level (negative elevation) | 15    |
| BBOX-3D-004 | High altitude      | `bbox=-180,-90,5000,180,90,10000`        | Returns resources at high altitude (5-10km)            | 15    |
| BBOX-3D-005 | Surface level only | `bbox=-180,-90,0,180,90,0`               | Returns resources at exactly 0m elevation              | 15    |
| BBOX-3D-006 | Mixed elevation    | `bbox=-122.5,37.7,-100,-122.3,37.9,1000` | Returns SF resources from -100m to 1000m               | 15    |

**Test Implementation (~90-120 lines, 6 tests):**

```typescript
describe('3D Bbox Queries (with Elevation)', () => {
  it('accepts 3D global bbox (0-1000m elevation)', async () => {
    const response = await client.systems.list({
      bbox: {
        minLon: -180,
        minLat: -90,
        minElev: 0,
        maxLon: 180,
        maxLat: 90,
        maxElev: 1000,
      },
    });

    expect(response.ok).toBe(true);
    expect(response.requestUrl).toContain(
      'bbox=-180%2C-90%2C0%2C180%2C90%2C1000'
    );
    // Returns systems with elevation between 0-1000 meters
  });

  it('accepts 3D regional bbox (San Francisco, 0-500m)', async () => {
    const response = await client.systems.list({
      bbox: {
        minLon: -122.5,
        minLat: 37.7,
        minElev: 0,
        maxLon: -122.3,
        maxLat: 37.9,
        maxElev: 500,
      },
    });

    expect(response.ok).toBe(true);
    expect(response.requestUrl).toContain(
      'bbox=-122.5%2C37.7%2C0%2C-122.3%2C37.9%2C500'
    );
  });

  it('accepts 3D bbox below sea level (negative elevation)', async () => {
    const response = await client.systems.list({
      bbox: {
        minLon: -180,
        minLat: -90,
        minElev: -500,
        maxLon: 180,
        maxLat: 90,
        maxElev: 0,
      },
    });

    expect(response.ok).toBe(true);
    // Returns systems below sea level (e.g., underwater sensors)
  });

  it('accepts 3D bbox at high altitude (5-10km)', async () => {
    const response = await client.systems.list({
      bbox: {
        minLon: -180,
        minLat: -90,
        minElev: 5000,
        maxLon: 180,
        maxLat: 90,
        maxElev: 10000,
      },
    });

    expect(response.ok).toBe(true);
    // Returns systems at aircraft/satellite altitudes
  });

  it('accepts 3D bbox at surface level only (0m)', async () => {
    const response = await client.systems.list({
      bbox: {
        minLon: -180,
        minLat: -90,
        minElev: 0,
        maxLon: 180,
        maxLat: 90,
        maxElev: 0,
      },
    });

    expect(response.ok).toBe(true);
    // Returns systems at exactly sea level
  });

  it('accepts 3D bbox with mixed elevation (negative to positive)', async () => {
    const response = await client.systems.list({
      bbox: {
        minLon: -122.5,
        minLat: 37.7,
        minElev: -100,
        maxLon: -122.3,
        maxLat: 37.9,
        maxElev: 1000,
      },
    });

    expect(response.ok).toBe(true);
    // Returns SF systems from 100m below to 1000m above sea level
  });
});
```

### 4.3 Validation Error Tests (8 tests)

**Priority:** **CRITICAL**

| Test ID      | Error Type                     | Example Query                    | Expected Error                                  | Lines |
| ------------ | ------------------------------ | -------------------------------- | ----------------------------------------------- | ----- |
| BBOX-ERR-001 | minLon > maxLon (antimeridian) | `bbox=170,-10,-170,10`           | 400 Bad Request (antimeridian crossing invalid) | 15    |
| BBOX-ERR-002 | minLat > maxLat                | `bbox=-122.5,38.0,-122.3,37.7`   | 400 Bad Request (minLat must be ≤ maxLat)       | 15    |
| BBOX-ERR-003 | Latitude > 90                  | `bbox=-180,-90,180,95`           | 400 Bad Request (latitude must be [-90, 90])    | 15    |
| BBOX-ERR-004 | Latitude < -90                 | `bbox=-180,-95,180,90`           | 400 Bad Request (latitude must be [-90, 90])    | 15    |
| BBOX-ERR-005 | Longitude > 180                | `bbox=-180,-90,185,90`           | 400 Bad Request (longitude must be [-180, 180]) | 15    |
| BBOX-ERR-006 | Longitude < -180               | `bbox=-185,-90,180,90`           | 400 Bad Request (longitude must be [-180, 180]) | 15    |
| BBOX-ERR-007 | Wrong number of values (3)     | `bbox=-122.5,37.7,-122.3`        | 400 Bad Request (bbox must have 4 or 6 values)  | 20    |
| BBOX-ERR-008 | Wrong number of values (5)     | `bbox=-122.5,37.7,0,-122.3,37.9` | 400 Bad Request (bbox must have 4 or 6 values)  | 20    |

**Test Implementation (~120-160 lines, 8 tests):**

```typescript
describe('Bbox Validation Errors', () => {
  it('rejects antimeridian crossing (minLon > maxLon)', async () => {
    await expect(
      client.systems.list({
        bbox: { minLon: 170, minLat: -10, maxLon: -170, maxLat: 10 },
      })
    ).rejects.toThrow(/400.*minLon.*maxLon.*antimeridian/i);
    // Antimeridian crossing (date line) is explicitly invalid in CSAPI
  });

  it('rejects minLat > maxLat', async () => {
    await expect(
      client.systems.list({
        bbox: { minLon: -122.5, minLat: 38.0, maxLon: -122.3, maxLat: 37.7 },
      })
    ).rejects.toThrow(/400.*minLat.*maxLat/i);
  });

  it('rejects latitude > 90', async () => {
    await expect(
      client.systems.list({
        bbox: { minLon: -180, minLat: -90, maxLon: 180, maxLat: 95 },
      })
    ).rejects.toThrow(/400.*latitude.*90/i);
  });

  it('rejects latitude < -90', async () => {
    await expect(
      client.systems.list({
        bbox: { minLon: -180, minLat: -95, maxLon: 180, maxLat: 90 },
      })
    ).rejects.toThrow(/400.*latitude.*-90/i);
  });

  it('rejects longitude > 180', async () => {
    await expect(
      client.systems.list({
        bbox: { minLon: -180, minLat: -90, maxLon: 185, maxLat: 90 },
      })
    ).rejects.toThrow(/400.*longitude.*180/i);
  });

  it('rejects longitude < -180', async () => {
    await expect(
      client.systems.list({
        bbox: { minLon: -185, minLat: -90, maxLon: 180, maxLat: 90 },
      })
    ).rejects.toThrow(/400.*longitude.*-180/i);
  });

  it('rejects bbox with wrong number of values (3)', async () => {
    // Client-side validation should catch this before sending request
    expect(() => {
      validateBBox({ minLon: -122.5, minLat: 37.7, maxLon: -122.3 } as any);
    }).toThrow(/bbox.*4.*6.*values/i);
  });

  it('rejects bbox with wrong number of values (5)', async () => {
    // Client-side validation should catch this before sending request
    expect(() => {
      validateBBox({
        minLon: -122.5,
        minLat: 37.7,
        minElev: 0,
        maxLon: -122.3,
        maxLat: 37.9,
      } as any);
    }).toThrow(/bbox.*4.*6.*values/i);
  });
});
```

### 4.4 Edge Case Tests (6 tests)

**Priority:** MEDIUM

| Test ID       | Edge Case                          | Example Query                                      | Expected Behavior                           | Lines |
| ------------- | ---------------------------------- | -------------------------------------------------- | ------------------------------------------- | ----- |
| BBOX-EDGE-001 | Point bbox (min = max)             | `bbox=-122.4194,37.7749,-122.4194,37.7749`         | Returns resources intersecting single point | 15    |
| BBOX-EDGE-002 | Arctic region (near North Pole)    | `bbox=-180,85,180,90`                              | Returns resources above 85° N               | 15    |
| BBOX-EDGE-003 | Antarctic region (near South Pole) | `bbox=-180,-90,180,-85`                            | Returns resources below -85° S              | 15    |
| BBOX-EDGE-004 | Single latitude line               | `bbox=-180,0,180,0`                                | Returns resources on equator                | 15    |
| BBOX-EDGE-005 | Single longitude line              | `bbox=0,-90,0,90`                                  | Returns resources on Prime Meridian         | 15    |
| BBOX-EDGE-006 | High-precision coordinates         | `bbox=-122.419416,37.774929,-122.419415,37.774930` | Handles sub-meter precision correctly       | 15    |

**Test Implementation (~90-120 lines, 6 tests):**

```typescript
describe('Bbox Edge Cases', () => {
  it('accepts point bbox (min = max)', async () => {
    const response = await client.systems.list({
      bbox: {
        minLon: -122.4194,
        minLat: 37.7749,
        maxLon: -122.4194,
        maxLat: 37.7749,
      },
    });

    expect(response.ok).toBe(true);
    expect(response.requestUrl).toContain(
      'bbox=-122.4194%2C37.7749%2C-122.4194%2C37.7749'
    );
    // San Francisco City Hall (single point)
    // Returns systems whose geometry intersects this point
  });

  it('accepts Arctic region bbox (above 85° N)', async () => {
    const response = await client.systems.list({
      bbox: { minLon: -180, minLat: 85, maxLon: 180, maxLat: 90 },
    });

    expect(response.ok).toBe(true);
    // Returns systems in Arctic region near North Pole
  });

  it('accepts Antarctic region bbox (below -85° S)', async () => {
    const response = await client.systems.list({
      bbox: { minLon: -180, minLat: -90, maxLon: 180, maxLat: -85 },
    });

    expect(response.ok).toBe(true);
    // Returns systems in Antarctic region near South Pole
  });

  it('accepts single latitude line bbox (equator)', async () => {
    const response = await client.systems.list({
      bbox: { minLon: -180, minLat: 0, maxLon: 180, maxLat: 0 },
    });

    expect(response.ok).toBe(true);
    // Returns systems exactly on equator (0° latitude)
  });

  it('accepts single longitude line bbox (Prime Meridian)', async () => {
    const response = await client.systems.list({
      bbox: { minLon: 0, minLat: -90, maxLon: 0, maxLat: 90 },
    });

    expect(response.ok).toBe(true);
    // Returns systems exactly on Prime Meridian (0° longitude)
  });

  it('handles high-precision coordinates (sub-meter accuracy)', async () => {
    const response = await client.systems.list({
      bbox: {
        minLon: -122.419416,
        minLat: 37.774929,
        maxLon: -122.419415,
        maxLat: 37.77493,
      },
    });

    expect(response.ok).toBe(true);
    // 6 decimal places ≈ 11cm precision
    // Returns systems in ~1m² area
  });
});
```

### 4.5 Bbox + Pagination Tests (4 tests)

**Priority:** HIGH

| Test ID      | Scenario                     | Example Query                               | Expected Behavior                     | Lines |
| ------------ | ---------------------------- | ------------------------------------------- | ------------------------------------- | ----- |
| BBOX-PAG-001 | Bbox + limit                 | `bbox=-180,-90,180,90&limit=100`            | Returns first 100 spatial resources   | 15    |
| BBOX-PAG-002 | Bbox + offset                | `bbox=-180,-90,180,90&limit=100&offset=200` | Returns spatial resources 201-300     | 15    |
| BBOX-PAG-003 | Bbox + pagination links      | `bbox=-122.5,37.7,-122.3,37.9&limit=50`     | Next/prev links preserve bbox filter  | 15    |
| BBOX-PAG-004 | Empty bbox result pagination | `bbox=0,0,0.0001,0.0001&limit=10`           | Empty result with no pagination links | 15    |

**Test Implementation (~60-80 lines, 4 tests):**

```typescript
describe('Bbox with Pagination', () => {
  it('combines bbox with limit', async () => {
    const response = await client.systems.list({
      bbox: { minLon: -180, minLat: -90, maxLon: 180, maxLat: 90 },
      limit: 100,
    });

    expect(response.ok).toBe(true);
    expect(response.features.length).toBeLessThanOrEqual(100);
    expect(response.requestUrl).toContain('bbox=-180%2C-90%2C180%2C90');
    expect(response.requestUrl).toContain('limit=100');
  });

  it('combines bbox with offset and limit', async () => {
    const response = await client.systems.list({
      bbox: { minLon: -180, minLat: -90, maxLon: 180, maxLat: 90 },
      limit: 100,
      offset: 200,
    });

    expect(response.ok).toBe(true);
    expect(response.requestUrl).toContain('bbox=-180%2C-90%2C180%2C90');
    expect(response.requestUrl).toContain('limit=100');
    expect(response.requestUrl).toContain('offset=200');
  });

  it('preserves bbox filter in pagination links', async () => {
    const response = await client.systems.list({
      bbox: { minLon: -122.5, minLat: 37.7, maxLon: -122.3, maxLat: 37.9 },
      limit: 50,
    });

    expect(response.ok).toBe(true);
    // Check next link preserves bbox filter
    if (response.links) {
      const nextLink = response.links.find((l) => l.rel === 'next');
      if (nextLink) {
        expect(nextLink.href).toMatch(/bbox=-122\.5/);
      }
    }
  });

  it('handles empty bbox result with pagination', async () => {
    const response = await client.systems.list({
      bbox: { minLon: 0, minLat: 0, maxLon: 0.0001, maxLat: 0.0001 },
      limit: 10,
    });

    expect(response.ok).toBe(true);
    expect(response.features.length).toBe(0);
    // No next/prev links for empty result
  });
});
```

### 4.6 Bbox + Temporal Tests (6 tests)

**Priority:** HIGH

| Test ID       | Scenario                          | Example Query                                                    | Expected Behavior                                | Lines |
| ------------- | --------------------------------- | ---------------------------------------------------------------- | ------------------------------------------------ | ----- |
| BBOX-TEMP-001 | Bbox + datetime instant           | `bbox=-180,-90,180,90&datetime=2024-01-15`                       | Returns spatial resources valid on date          | 15    |
| BBOX-TEMP-002 | Bbox + datetime interval          | `bbox=-122.5,37.7,-122.3,37.9&datetime=2024-01-01/2024-12-31`    | Returns SF systems valid in 2024                 | 15    |
| BBOX-TEMP-003 | Bbox + open-ended datetime        | `bbox=-180,-90,180,90&datetime=2024-01-01/..`                    | Returns spatial resources valid after 2024-01-01 | 15    |
| BBOX-TEMP-004 | Regional bbox + recent datetime   | `bbox=-122.5,37.7,-122.3,37.9&datetime=2024-12-01/..`            | Returns recent SF systems                        | 15    |
| BBOX-TEMP-005 | Global bbox + historical datetime | `bbox=-180,-90,180,90&datetime=2020-01-01/2021-12-31`            | Returns historical spatial resources             | 15    |
| BBOX-TEMP-006 | Small bbox + instant datetime     | `bbox=-122.42,37.77,-122.41,37.78&datetime=2024-01-15T12:00:00Z` | Returns neighborhood systems at instant          | 15    |

**Test Implementation (~90-120 lines, 6 tests):**

```typescript
describe('Bbox with Temporal Filters', () => {
  it('combines bbox with datetime instant', async () => {
    const response = await client.systems.list({
      bbox: { minLon: -180, minLat: -90, maxLon: 180, maxLat: 90 },
      datetime: '2024-01-15',
    });

    expect(response.ok).toBe(true);
    expect(response.requestUrl).toContain('bbox=-180%2C-90%2C180%2C90');
    expect(response.requestUrl).toContain('datetime=2024-01-15');
    // Returns systems with non-null geometry AND validTime intersecting 2024-01-15
  });

  it('combines bbox with datetime interval', async () => {
    const response = await client.systems.list({
      bbox: { minLon: -122.5, minLat: 37.7, maxLon: -122.3, maxLat: 37.9 },
      datetime: '2024-01-01/2024-12-31',
    });

    expect(response.ok).toBe(true);
    expect(response.requestUrl).toContain('bbox=-122.5%2C37.7%2C-122.3%2C37.9');
    expect(response.requestUrl).toContain('datetime=2024-01-01%2F2024-12-31');
    // SF systems valid at any point during 2024
  });

  it('combines bbox with open-ended datetime', async () => {
    const response = await client.systems.list({
      bbox: { minLon: -180, minLat: -90, maxLon: 180, maxLat: 90 },
      datetime: '2024-01-01/..',
    });

    expect(response.ok).toBe(true);
    expect(response.requestUrl).toContain('datetime=2024-01-01%2F..');
    // Spatial resources valid after 2024-01-01
  });

  it('combines regional bbox with recent datetime', async () => {
    const response = await client.systems.list({
      bbox: { minLon: -122.5, minLat: 37.7, maxLon: -122.3, maxLat: 37.9 },
      datetime: '2024-12-01/..',
    });

    expect(response.ok).toBe(true);
    // Recent SF systems (December 2024 onwards)
  });

  it('combines global bbox with historical datetime', async () => {
    const response = await client.systems.list({
      bbox: { minLon: -180, minLat: -90, maxLon: 180, maxLat: 90 },
      datetime: '2020-01-01/2021-12-31',
    });

    expect(response.ok).toBe(true);
    // Historical spatial resources (2020-2021)
  });

  it('combines small bbox with instant datetime', async () => {
    const response = await client.systems.list({
      bbox: { minLon: -122.42, minLat: 37.77, maxLon: -122.41, maxLat: 37.78 },
      datetime: '2024-01-15T12:00:00Z',
    });

    expect(response.ok).toBe(true);
    // Neighborhood-scale systems valid at specific instant
  });
});
```

### 4.7 Point Bbox Tests (3 tests)

> ⚠️ **REVIEW NOTICE (L4): Result Set Size Comparison Tests Server Filtering, Not Client Code (AP4)**
>
> Test BBOX-PT-003 (`expect(responseWithBbox.features.length).toBeLessThanOrEqual(responseWithoutBbox.features.length)`) compares server filtering results rather than testing client code. The client's job is to encode the bbox correctly in the URL — whether the server returns fewer results is server behavior. Tests BBOX-PT-001 and BBOX-PT-002 have the same `response.ok` pattern flagged in Section 4.1 (M7).

**Priority:** MEDIUM

| Test ID     | Scenario                         | Example Query                               | Expected Behavior                          | Lines |
| ----------- | -------------------------------- | ------------------------------------------- | ------------------------------------------ | ----- |
| BBOX-PT-001 | Point bbox with Point geometry   | `bbox=-122.4194,37.7749,-122.4194,37.7749`  | Returns Point resources at exact location  | 20    |
| BBOX-PT-002 | Point bbox with Polygon geometry | `bbox=-122.4194,37.7749,-122.4194,37.7749`  | Returns Polygon resources containing point | 20    |
| BBOX-PT-003 | Point bbox vs no bbox            | Compare results with and without point bbox | Point bbox more restrictive than no bbox   | 20    |

**Test Implementation (~50-70 lines, 3 tests):**

```typescript
describe('Point Bbox Queries', () => {
  it('matches Point geometry at exact location', async () => {
    const response = await client.systems.list({
      bbox: {
        minLon: -122.4194,
        minLat: 37.7749,
        maxLon: -122.4194,
        maxLat: 37.7749,
      },
    });

    expect(response.ok).toBe(true);
    // Should return systems with Point geometry at [-122.4194, 37.7749]
    // May also return systems with geometries that contain or intersect this point
  });

  it('matches Polygon geometry containing point', async () => {
    const response = await client.systems.list({
      bbox: {
        minLon: -122.4194,
        minLat: 37.7749,
        maxLon: -122.4194,
        maxLat: 37.7749,
      },
    });

    expect(response.ok).toBe(true);
    // Should return systems with Polygon geometries that contain this point
    // Includes polygons with point on boundary (depends on implementation)
  });

  it('point bbox is more restrictive than no bbox', async () => {
    const responseWithBbox = await client.systems.list({
      bbox: {
        minLon: -122.4194,
        minLat: 37.7749,
        maxLon: -122.4194,
        maxLat: 37.7749,
      },
    });

    const responseWithoutBbox = await client.systems.list({});

    expect(responseWithBbox.ok).toBe(true);
    expect(responseWithoutBbox.ok).toBe(true);
    expect(responseWithBbox.features.length).toBeLessThanOrEqual(
      responseWithoutBbox.features.length
    );
    // Point bbox should return subset of all systems
  });
});
```

### 4.8 Test Scenario Summary

**Total Tests:** 43 tests  
**Total Lines:** 650-850 lines

| Test Category     | Test Count | Lines   | Priority     |
| ----------------- | ---------- | ------- | ------------ |
| Basic Bbox        | 10         | 150-200 | **CRITICAL** |
| 3D Bbox           | 6          | 90-120  | HIGH         |
| Validation Errors | 8          | 120-160 | **CRITICAL** |
| Edge Cases        | 6          | 90-120  | MEDIUM       |
| Bbox + Pagination | 4          | 60-80   | HIGH         |
| Bbox + Temporal   | 6          | 90-120  | HIGH         |
| Point Bbox        | 3          | 50-70   | MEDIUM       |

---

## 5. Fixture Requirements

### 5.1 Bbox Query String Fixtures (15 fixtures)

| Fixture ID         | Format Type                     | Example                                       | Notes                |
| ------------------ | ------------------------------- | --------------------------------------------- | -------------------- |
| **2D Bbox (10)**   |
| BBOX-QS-001        | Global bbox                     | `-180,-90,180,90`                             | Entire world         |
| BBOX-QS-002        | Regional bbox (North America)   | `-130,25,-60,50`                              | Continental scale    |
| BBOX-QS-003        | City-scale bbox (San Francisco) | `-122.5,37.7,-122.3,37.9`                     | Urban area           |
| BBOX-QS-004        | Neighborhood bbox               | `-122.42,37.77,-122.41,37.78`                 | ~1km²                |
| BBOX-QS-005        | Western Hemisphere              | `-180,-90,0,90`                               | Half the world       |
| BBOX-QS-006        | Northern Hemisphere             | `-180,0,180,90`                               | Above equator        |
| BBOX-QS-007        | Equatorial bbox                 | `-180,-10,180,10`                             | ±10° of equator      |
| BBOX-QS-008        | Prime Meridian bbox             | `-10,-90,10,90`                               | ±10° of 0° longitude |
| BBOX-QS-009        | Arctic region                   | `-180,85,180,90`                              | Above 85° N          |
| BBOX-QS-010        | Antarctic region                | `-180,-90,180,-85`                            | Below -85° S         |
| **3D Bbox (3)**    |
| BBOX-QS-011        | 3D global bbox                  | `-180,-90,0,180,90,1000`                      | 0-1000m elevation    |
| BBOX-QS-012        | 3D regional bbox                | `-122.5,37.7,0,-122.3,37.9,500`               | SF, 0-500m           |
| BBOX-QS-013        | 3D below sea level              | `-180,-90,-500,180,90,0`                      | Underwater           |
| **Point Bbox (2)** |
| BBOX-QS-014        | Point bbox (city hall)          | `-122.4194,37.7749,-122.4194,37.7749`         | Single point         |
| BBOX-QS-015        | High-precision bbox             | `-122.419416,37.774929,-122.419415,37.774930` | Sub-meter            |

### 5.2 Spatial Response Fixtures (15 fixtures)

| Fixture ID    | Resource Type   | Geometry Type            | Bbox Filter | Example Geometry                                                                                        | Notes                                       |
| ------------- | --------------- | ------------------------ | ----------- | ------------------------------------------------------------------------------------------------------- | ------------------------------------------- |
| BBOX-RESP-001 | System          | Point                    | Global      | `[-122.4194, 37.7749]`                                                                                  | SF location                                 |
| BBOX-RESP-002 | System          | Polygon                  | Regional    | `[[[-122.5, 37.7], [-122.3, 37.7], [-122.3, 37.9], [-122.5, 37.9], [-122.5, 37.7]]]`                    | SF boundary                                 |
| BBOX-RESP-003 | System          | LineString               | City-scale  | `[[-122.5, 37.7], [-122.3, 37.9]]`                                                                      | SF diagonal                                 |
| BBOX-RESP-004 | Deployment      | Point                    | Regional    | `[0.0, 51.5]`                                                                                           | London location                             |
| BBOX-RESP-005 | Deployment      | null                     | Global      | `null`                                                                                                  | No geometry (excluded from spatial queries) |
| BBOX-RESP-006 | Procedure       | Point                    | Global      | `[-73.99, 40.73]`                                                                                       | NYC location                                |
| BBOX-RESP-007 | SamplingFeature | Point                    | City-scale  | `[-122.42, 37.77]`                                                                                      | SF sampling point                           |
| BBOX-RESP-008 | System          | Point with elevation     | 3D global   | `[-122.4194, 37.7749, 100]`                                                                             | 100m above sea level                        |
| BBOX-RESP-009 | System          | MultiPoint               | Regional    | `[[-122.5, 37.7], [-122.3, 37.9]]`                                                                      | Multiple sensors                            |
| BBOX-RESP-010 | System          | Point                    | Arctic      | `[0.0, 87.0]`                                                                                           | Near North Pole                             |
| BBOX-RESP-011 | System          | Point                    | Antarctic   | `[0.0, -87.0]`                                                                                          | Near South Pole                             |
| BBOX-RESP-012 | System          | Point                    | Equatorial  | `[0.0, 0.0]`                                                                                            | Prime Meridian + Equator                    |
| BBOX-RESP-013 | Deployment      | Polygon                  | 3D regional | `[[[-122.5, 37.7, 0], [-122.3, 37.7, 0], [-122.3, 37.9, 100], [-122.5, 37.9, 100], [-122.5, 37.7, 0]]]` | 3D polygon                                  |
| BBOX-RESP-014 | System          | Point                    | Point bbox  | `[-122.4194, 37.7749]`                                                                                  | Exact match                                 |
| BBOX-RESP-015 | System          | Polygon containing point | Point bbox  | `[[[-122.42, 37.77], [-122.41, 37.77], [-122.41, 37.78], [-122.42, 37.78], [-122.42, 37.77]]]`          | Contains point                              |

### 5.3 Spatial Error Fixtures (10 fixtures)

| Fixture ID   | Error Type            | Example Query                    | Expected Error Message                                                                        |
| ------------ | --------------------- | -------------------------------- | --------------------------------------------------------------------------------------------- |
| BBOX-ERR-001 | Antimeridian crossing | `bbox=170,-10,-170,10`           | "Invalid bbox: minLon (170) must be ≤ maxLon (-170). Antimeridian crossing is not supported." |
| BBOX-ERR-002 | minLat > maxLat       | `bbox=-122.5,38.0,-122.3,37.7`   | "Invalid bbox: minLat (38.0) must be ≤ maxLat (37.7)."                                        |
| BBOX-ERR-003 | Latitude > 90         | `bbox=-180,-90,180,95`           | "Invalid bbox: maxLat (95) must be in range [-90, 90]."                                       |
| BBOX-ERR-004 | Latitude < -90        | `bbox=-180,-95,180,90`           | "Invalid bbox: minLat (-95) must be in range [-90, 90]."                                      |
| BBOX-ERR-005 | Longitude > 180       | `bbox=-180,-90,185,90`           | "Invalid bbox: maxLon (185) must be in range [-180, 180]."                                    |
| BBOX-ERR-006 | Longitude < -180      | `bbox=-185,-90,180,90`           | "Invalid bbox: minLon (-185) must be in range [-180, 180]."                                   |
| BBOX-ERR-007 | Wrong value count (3) | `bbox=-122.5,37.7,-122.3`        | "Invalid bbox: Expected 4 or 6 values, got 3."                                                |
| BBOX-ERR-008 | Wrong value count (5) | `bbox=-122.5,37.7,0,-122.3,37.9` | "Invalid bbox: Expected 4 or 6 values, got 5."                                                |
| BBOX-ERR-009 | 3D: minElev > maxElev | `bbox=-180,-90,1000,180,90,0`    | "Invalid bbox: minElev (1000) must be ≤ maxElev (0)."                                         |
| BBOX-ERR-010 | Non-numeric value     | `bbox=-122.5,abc,-122.3,37.9`    | "Invalid bbox: All values must be numeric."                                                   |

### 5.4 Fixture Summary

**Total Fixtures:** 40 fixtures

| Fixture Category          | Count | Priority     |
| ------------------------- | ----- | ------------ |
| Bbox Query Strings        | 15    | **CRITICAL** |
| Spatial Response Fixtures | 15    | HIGH         |
| Spatial Error Fixtures    | 10    | **CRITICAL** |

---

## 6. Implementation Estimates

### 6.1 Test Implementation Summary

| Test Category     | Test Count | Lines per Test | Total Lines | Priority     |
| ----------------- | ---------- | -------------- | ----------- | ------------ |
| Basic Bbox        | 10         | 15-20          | 150-200     | **CRITICAL** |
| 3D Bbox           | 6          | 15-20          | 90-120      | HIGH         |
| Validation Errors | 8          | 15-20          | 120-160     | **CRITICAL** |
| Edge Cases        | 6          | 15-20          | 90-120      | MEDIUM       |
| Bbox + Pagination | 4          | 15-20          | 60-80       | HIGH         |
| Bbox + Temporal   | 6          | 15-20          | 90-120      | HIGH         |
| Point Bbox        | 3          | 17-23          | 50-70       | MEDIUM       |
| **TOTAL**         | **43**     | **~16 avg**    | **650-850** |              |

**Test File Organization:**

```
src/ogc-api/spatial/
  bbox-basic-queries.spec.ts           (~150-200 lines, 10 tests)
  bbox-3d-queries.spec.ts              (~90-120 lines, 6 tests)
  bbox-validation-errors.spec.ts       (~120-160 lines, 8 tests)
  bbox-edge-cases.spec.ts              (~90-120 lines, 6 tests)
  bbox-pagination.spec.ts              (~60-80 lines, 4 tests)
  bbox-temporal-queries.spec.ts        (~90-120 lines, 6 tests)
  bbox-point-queries.spec.ts           (~50-70 lines, 3 tests)

fixtures/spatial/
  query-strings/                       (15 fixture files)
  responses/                           (15 fixture files)
  errors/                              (10 fixture files)
```

### 6.2 Implementation Effort Estimates

**Development Tasks:**

| Task                    | Estimated Lines   | Estimated Time  |
| ----------------------- | ----------------- | --------------- |
| Basic bbox tests        | 150-200           | 3-4 hours       |
| 3D bbox tests           | 90-120            | 2-3 hours       |
| Validation error tests  | 120-160           | 2-3 hours       |
| Edge case tests         | 90-120            | 2-3 hours       |
| Bbox + pagination tests | 60-80             | 1-2 hours       |
| Bbox + temporal tests   | 90-120            | 2-3 hours       |
| Point bbox tests        | 50-70             | 1-2 hours       |
| Fixture creation        | 40 files          | 4-6 hours       |
| Documentation           | 50-100            | 1-2 hours       |
| **TOTAL**               | **650-850 lines** | **18-28 hours** |

**Testing Priorities:**

1. **CRITICAL (Priority 1):** 18 tests, ~270-360 lines, 5-7 hours

   - Basic bbox queries (global, regional, city-scale)
   - Validation errors (coordinate ranges, min ≤ max, antimeridian)

2. **HIGH (Priority 2):** 16 tests, ~240-320 lines, 7-11 hours

   - 3D bbox queries (elevation handling)
   - Bbox + pagination interactions
   - Bbox + temporal query combinations

3. **MEDIUM (Priority 3):** 9 tests, ~140-190 lines, 6-10 hours
   - Edge cases (polar regions, point bbox, coordinate precision)

---

## 7. Client API Design

### 7.1 Bbox Parameter Type

```typescript
interface BBoxFilter {
  minLon: number;
  minLat: number;
  maxLon: number;
  maxLat: number;
  minElev?: number; // Optional: 3D bbox
  maxElev?: number; // Optional: 3D bbox
}

// Alternative: Array notation (less type-safe)
type BBoxArray =
  | [number, number, number, number]
  | [number, number, number, number, number, number];
```

### 7.2 Client API Examples

**2D Bbox Query:**

```typescript
// Object notation (recommended)
client.systems.list({
  bbox: {
    minLon: -122.5,
    minLat: 37.7,
    maxLon: -122.3,
    maxLat: 37.9,
  },
});
// Encodes to: ?bbox=-122.5,37.7,-122.3,37.9

// Array notation (alternative)
client.systems.list({
  bbox: [-122.5, 37.7, -122.3, 37.9],
});
// Encodes to: ?bbox=-122.5,37.7,-122.3,37.9
```

**3D Bbox Query:**

```typescript
client.systems.list({
  bbox: {
    minLon: -122.5,
    minLat: 37.7,
    minElev: 0,
    maxLon: -122.3,
    maxLat: 37.9,
    maxElev: 500,
  },
});
// Encodes to: ?bbox=-122.5,37.7,0,-122.3,37.9,500
```

**Point Bbox Query:**

```typescript
client.systems.list({
  bbox: {
    minLon: -122.4194,
    minLat: 37.7749,
    maxLon: -122.4194,
    maxLat: 37.7749,
  },
});
// Encodes to: ?bbox=-122.4194,37.7749,-122.4194,37.7749
```

**Bbox + Temporal Query:**

```typescript
client.systems.list({
  bbox: {
    minLon: -122.5,
    minLat: 37.7,
    maxLon: -122.3,
    maxLat: 37.9,
  },
  datetime: '2024-01-01/2024-12-31',
});
// Encodes to: ?bbox=-122.5,37.7,-122.3,37.9&datetime=2024-01-01%2F2024-12-31
```

**Bbox + Pagination:**

```typescript
client.systems.list({
  bbox: {
    minLon: -180,
    minLat: -90,
    maxLon: 180,
    maxLat: 90,
  },
  limit: 100,
  offset: 200,
});
// Encodes to: ?bbox=-180,-90,180,90&limit=100&offset=200
```

### 7.3 Bbox Validation Function

```typescript
function validateBBox(bbox: BBoxFilter): void {
  // Check required fields
  if (
    bbox.minLon === undefined ||
    bbox.minLat === undefined ||
    bbox.maxLon === undefined ||
    bbox.maxLat === undefined
  ) {
    throw new ParameterValidationError(
      'bbox',
      bbox,
      'minLon, minLat, maxLon, maxLat are required'
    );
  }

  // Validate longitude range
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

  // Validate latitude range
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

  // Validate min ≤ max
  if (bbox.minLon > bbox.maxLon) {
    throw new ParameterValidationError(
      'bbox',
      bbox,
      'minLon must be ≤ maxLon (antimeridian crossing not supported)'
    );
  }
  if (bbox.minLat > bbox.maxLat) {
    throw new ParameterValidationError('bbox', bbox, 'minLat must be ≤ maxLat');
  }

  // Validate elevation (if provided)
  if (bbox.minElev !== undefined && bbox.maxElev !== undefined) {
    if (bbox.minElev > bbox.maxElev) {
      throw new ParameterValidationError(
        'bbox',
        bbox,
        'minElev must be ≤ maxElev'
      );
    }
  } else if (bbox.minElev !== undefined || bbox.maxElev !== undefined) {
    throw new ParameterValidationError(
      'bbox',
      bbox,
      'Both minElev and maxElev must be provided for 3D bbox'
    );
  }
}
```

### 7.4 Bbox Encoding Function

```typescript
function encodeBBox(bbox: BBoxFilter): string {
  if (bbox.minElev !== undefined && bbox.maxElev !== undefined) {
    // 3D bbox (6 values)
    return `${bbox.minLon},${bbox.minLat},${bbox.minElev},${bbox.maxLon},${bbox.maxLat},${bbox.maxElev}`;
  } else {
    // 2D bbox (4 values)
    return `${bbox.minLon},${bbox.minLat},${bbox.maxLon},${bbox.maxLat}`;
  }
}
```

---

## 8. Antimeridian Handling Workarounds

### 8.1 Problem Statement

CSAPI explicitly does **NOT** support antimeridian crossing in bbox parameter:

- `bbox=170,-10,-170,10` → **400 Bad Request** (minLon > maxLon)

This affects regions that cross the International Date Line:

- **Fiji** (177°E to 178°W)
- **Kiribati** (169°E to 169°W)
- **Samoa** (172°W)
- **Tonga** (175°W)
- **Parts of Russia** (Eastern Siberia, 180°E)
- **Parts of Alaska** (Aleutian Islands, 180°W)

### 8.2 Client-Side Workaround: Split Query

**Approach:** Split antimeridian-crossing bbox into two separate queries

**Example - Query Fiji region:**

```typescript
// INVALID: Single query crossing antimeridian
// bbox=177,-20,-178,20 → 400 Bad Request (177 > -178)

// WORKAROUND: Split into two queries
const westQuery = client.systems.list({
  bbox: { minLon: 177, minLat: -20, maxLon: 180, maxLat: 20 },
});
// Returns systems from 177°E to 180°E (date line)

const eastQuery = client.systems.list({
  bbox: { minLon: -180, minLat: -20, maxLon: -178, maxLat: 20 },
});
// Returns systems from -180°W to 178°W

// Client merges results
const mergedFeatures = [...westQuery.features, ...eastQuery.features];
```

**Limitations:**

- Requires two server requests (double network overhead)
- Client must merge and deduplicate results
- Pagination becomes complex (need to paginate both queries)
- Total count (`numberMatched`) requires manual calculation

### 8.3 Alternative Workaround: Expand to Full Longitude

**Approach:** Use full longitude range if region crosses antimeridian

**Example:**

```typescript
// INVALID: bbox=177,-20,-178,20

// WORKAROUND: Expand to full longitude range
client.systems.list({
  bbox: { minLon: -180, minLat: -20, maxLon: 180, maxLat: 20 },
});
// Returns systems in latitude band -20° to 20°, all longitudes
```

**Tradeoffs:**

- ✅ Single query (no merge needed)
- ✅ Simple implementation
- ❌ Returns systems outside target region (less precise)
- ❌ May return many irrelevant results

**When to Use:** Small target latitude range where extra longitude coverage is acceptable

### 8.4 Future Enhancement: Client Library Helper

**Proposed:** Client library could provide antimeridian-aware bbox helper

```typescript
// Helper function (future enhancement)
async function queryBBoxWithAntimeridian(
  client: CSAPIClient,
  bbox: BBoxFilter,
  options?: QueryOptions
): Promise<FeatureCollection> {
  // Detect antimeridian crossing
  if (bbox.minLon > bbox.maxLon) {
    // Split into two queries
    const westPromise = client.systems.list({
      bbox: { ...bbox, maxLon: 180 },
      ...options,
    });
    const eastPromise = client.systems.list({
      bbox: { ...bbox, minLon: -180 },
      ...options,
    });

    const [westResult, eastResult] = await Promise.all([
      westPromise,
      eastPromise,
    ]);

    // Merge results (deduplicate by feature ID)
    return mergeFeatureCollections(westResult, eastResult);
  } else {
    // Normal query
    return client.systems.list({ bbox, ...options });
  }
}
```

**Note:** This is **NOT** in initial scope - document as future enhancement

---

## 9. References

### 9.1 Specifications

- **OGC API - Features Part 1, Clause 7.15.3:** Bbox parameter specification
- **OGC API - Common:** Spatial query patterns
- **GeoJSON RFC 7946:** Coordinate reference system (WGS 84 / CRS84)
- **CSAPI Part 1 Specification:** OGC 23-001 (spatial parameter definitions)

### 9.2 Related Research

- **Section 24:** Query Parameter Combination Testing (spatial + other parameters)
- **Section 11:** GeoJSON Testing Requirements (spatial structures, CRS)
- **Section 8:** CSAPI Specification Test Requirements (spatial parameter specs)
- **Section 23:** Pagination Testing Strategy (spatial + pagination)

### 9.3 Implementation References

- Query Parameter Requirements: `csapi-query-parameters.md` (bbox parameter)
- Part 1 Requirements: `csapi-part1-requirements.md` (spatial filtering)
- Format Requirements: `csapi-format-requirements.md` (CRS specification)
- GeoJSON Testing: `11-geojson-csapi-testing-requirements.md` (geometry handling)

---

## 10. Appendices

### Appendix A: Coordinate System Quick Reference

**WGS 84 (CRS84) Coordinate Ranges:**

```
Longitude: -180° to +180°
  - Western Hemisphere: -180° to 0°
  - Eastern Hemisphere: 0° to +180°
  - Prime Meridian: 0°
  - International Date Line: ±180°

Latitude: -90° to +90°
  - Southern Hemisphere: -90° to 0°
  - Northern Hemisphere: 0° to +90°
  - Equator: 0°
  - North Pole: +90°
  - South Pole: -90°

Elevation: Any numeric value (meters above WGS 84 ellipsoid)
  - Sea level: ~0 meters (varies by location due to geoid)
  - Above sea level: Positive
  - Below sea level: Negative
```

**Coordinate Precision:**

```
Decimal Places | Approximate Distance
---------------|---------------------
0              | 111 km (1 degree)
1              | 11.1 km (0.1 degree)
2              | 1.1 km (0.01 degree)
3              | 111 meters (0.001 degree)
4              | 11 meters (0.0001 degree)
5              | 1.1 meters (0.00001 degree)
6              | 11 cm (0.000001 degree)
7              | 1.1 cm (0.0000001 degree)
```

**Common CRS Identifiers:**

- **WGS 84:** EPSG:4326 (latitude, longitude order - GIS convention)
- **CRS84:** OGC:CRS84 (longitude, latitude order - GeoJSON convention)
- **CSAPI Uses:** CRS84 (longitude, latitude order)

### Appendix B: Example Bbox Coordinates

**Major Cities:**

```
San Francisco:    bbox=-122.5,37.7,-122.3,37.9
New York City:    bbox=-74.1,40.6,-73.9,40.9
London:           bbox=-0.2,51.4,0.1,51.6
Tokyo:            bbox=139.6,35.6,139.9,35.8
Sydney:           bbox=151.1,-34.0,151.3,-33.8
```

**Continents:**

```
North America:    bbox=-170,15,-50,75
South America:    bbox=-82,-56,-34,13
Europe:           bbox=-25,35,40,71
Africa:           bbox=-18,-35,52,37
Asia:             bbox=25,-10,180,80
Australia:        bbox=112,-44,154,-10
Antarctica:       bbox=-180,-90,180,-60
```

**Special Regions:**

```
Equatorial:       bbox=-180,-10,180,10
Arctic:           bbox=-180,66.5,180,90  (above Arctic Circle)
Antarctic:        bbox=-180,-90,180,-66.5  (below Antarctic Circle)
Tropics:          bbox=-180,-23.5,180,23.5  (between Tropics of Cancer/Capricorn)
```

### Appendix C: Bbox Validation Rules Summary

**Required Validation Rules:**

| Rule                  | Description                         | Error Code      |
| --------------------- | ----------------------------------- | --------------- |
| **minLon ≤ maxLon**   | MUST be true (antimeridian invalid) | 400 Bad Request |
| **minLat ≤ maxLat**   | MUST be true                        | 400 Bad Request |
| **minElev ≤ maxElev** | MUST be true (if provided)          | 400 Bad Request |
| **Longitude range**   | -180 ≤ lon ≤ 180 (MUST)             | 400 Bad Request |
| **Latitude range**    | -90 ≤ lat ≤ 90 (MUST)               | 400 Bad Request |
| **Value count**       | 4 or 6 values (MUST)                | 400 Bad Request |
| **Numeric values**    | All values numeric (MUST)           | 400 Bad Request |

**Optional Validation (Implementation-Dependent):**

- Coordinate precision limits (e.g., max 10 decimal places)
- Elevation range limits (e.g., -10000 to 10000 meters)
- Bbox area limits (e.g., reject if too large/too small)

### Appendix D: Spatial Resource Applicability Matrix

| Resource Type        | Geometry Property | Spatial Query Support | Geometry Required      | Notes                       |
| -------------------- | ----------------- | --------------------- | ---------------------- | --------------------------- |
| **Part 1 Resources** |
| Systems              | ✅ Yes            | ✅ bbox               | Optional (may be null) | Sensor/platform location    |
| Deployments          | ✅ Yes            | ✅ bbox               | Optional (may be null) | Deployment location         |
| Procedures           | ✅ Yes            | ✅ bbox               | Optional (may be null) | Applicable area             |
| SamplingFeatures     | ✅ Yes            | ✅ bbox               | Optional (may be null) | Sampling location           |
| **Part 2 Resources** |
| DataStreams          | ❌ No             | ❌ N/A                | N/A                    | Inherits from parent System |
| ControlStreams       | ❌ No             | ❌ N/A                | N/A                    | Inherits from parent System |
| Observations         | ❌ No             | ❌ N/A                | N/A                    | Inherits from DataStream    |
| Commands             | ❌ No             | ❌ N/A                | N/A                    | Inherits from ControlStream |
| SystemEvents         | ❌ No             | ❌ N/A                | N/A                    | No spatial component        |

**Key Points:**

- Only **Part 1 resources** support spatial queries (bbox parameter)
- Part 2 resources inherit geometry from parent resources (not directly queryable)
- Resources with **null geometry** are excluded from bbox queries
- Bbox query uses **intersection semantics** (not containment)

---

**End of Document**
