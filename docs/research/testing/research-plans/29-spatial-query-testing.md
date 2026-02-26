# Section 29: Spatial Query Testing Strategy - Research Plan

**Status:** ✅ Complete  
**Last Updated:** February 6, 2026  
**Research Time:** 210 minutes (3.5 hours)  
**Test Implementation Lines:** 650-850 lines (43 tests)

---

## 1. Research Objective

Define testing strategy for spatial query parameters (bbox, geometry intersection).

**Why 29th:** Spatial queries are critical for Part 1 resources. After query parameter testing (Section 24), deep dive on spatial.

---

## 2. Research Questions

### Core Questions

1. How to test bbox query parameter?
2. How to test geometry intersection queries?
3. What CRS handling is required?
4. What spatial edge cases must be tested (antimeridian, poles)?
5. How to test spatial validation errors?
6. What fixtures needed for spatial scenarios?

### Detailed Questions

- What spatial parameters does CSAPI define?
- What is the bbox parameter format?
- Which resources support spatial queries?
- What coordinate reference systems (CRS) must be supported?
- How to test CRS transformations?
- What is the default CRS?
- How to test antimeridian crossing (±180° longitude)?
- How to test polar regions (near ±90° latitude)?
- How to test bbox validation (min > max)?
- How to test geometry intersection types (contains, intersects, within)?
- How to test spatial queries with pagination?
- What happens with invalid coordinates?

---

## 3. Primary Resources

- **Query Parameter Requirements**: [docs/research/requirements/csapi-query-parameters.md](../../requirements/csapi-query-parameters.md) (spatial parameters)
- **CSAPI Part 1 Specification**: https://docs.ogc.org/is/23-001/23-001.html (spatial queries)
- **GeoJSON RFC 7946**: Spatial structures and coordinate systems
- **OGC API - Features**: Spatial query patterns

## 4. Supporting Resources

- Section 24 deliverable (Query Parameter Combination Testing - parameter interactions)
- Section 11 deliverable (GeoJSON Testing Requirements - spatial structures)
- Section 23 deliverable (Pagination - spatial queries with pagination)
- CRS (Coordinate Reference System) standards

---

## 5. Research Methodology

### Phase 1: Spatial Parameter Specification Analysis (TBD minutes)

**Objective:** Extract spatial parameter requirements from CSAPI

**Tasks:**

1. Identify all spatial parameters (bbox, geometry, etc.)
2. Document bbox parameter format specification
3. Map spatial parameters to resource types
4. Extract CRS requirements
5. Document spatial parameter precedence rules
6. Create spatial parameter matrix

### Phase 2: CRS and Coordinate System Analysis (TBD minutes)

**Objective:** Understand coordinate reference system requirements

**Tasks:**

1. Identify supported CRS (WGS 84, CRS84, etc.)
2. Document default CRS (typically WGS 84)
3. Identify CRS transformation requirements
4. Document CRS representation in queries
5. Create CRS test matrix

### Phase 3: Spatial Edge Case Analysis (TBD minutes)

**Objective:** Identify spatial edge cases requiring testing

**Tasks:**

1. Document antimeridian crossing scenarios
2. Document polar region scenarios
3. Document bbox validation edge cases
4. Identify coordinate precision issues
5. Document spatial topology edge cases
6. Create spatial edge case matrix

### Phase 4: Upstream Spatial Testing Analysis (TBD minutes)

**Objective:** Analyze spatial query testing in upstream

**Tasks:**

1. Identify spatial query tests in upstream
2. Extract bbox test patterns
3. Extract CRS handling patterns
4. Identify spatial edge case coverage
5. Extract best practices

### Phase 5: Test Scenario Design (TBD minutes)

**Objective:** Design test scenarios for spatial queries

**Tasks:**

1. Design bbox query test scenarios
2. Design geometry intersection test scenarios
3. Design CRS handling test scenarios
4. Design antimeridian test scenarios
5. Design polar region test scenarios
6. Design spatial validation error scenarios
7. Document scenario matrix

### Phase 6: Fixture Design (TBD minutes)

**Objective:** Design fixtures for spatial query testing

**Tasks:**

1. Design bbox query string fixtures
2. Design spatial response fixtures
3. Design antimeridian crossing fixtures
4. Design polar region fixtures
5. Design spatial error fixtures
6. Estimate fixture counts

### Phase 7: Synthesis (TBD minutes)

**Objective:** Create comprehensive spatial query testing strategy

**Tasks:**

1. Consolidate spatial scenarios
2. Create spatial query test templates
3. Document fixture requirements
4. Estimate test implementation effort
5. Create deliverable document

---

## 6. Success Criteria

This research is complete when:

- [x] All spatial parameters are specified (bbox, geom)
- [x] Bbox parameter format is fully documented
- [x] CRS handling is defined and tested
- [x] Antimeridian crossing scenarios are specified
- [x] Polar region scenarios are defined
- [x] Spatial validation error scenarios are documented
- [x] Spatial edge cases are identified
- [x] Deliverable document is peer-reviewed

---

## 7. Deliverable

**Spatial query testing strategy with geometry scenario coverage**

Content includes:

- Complete spatial parameter inventory
- Bbox parameter format specification and test patterns
- Geometry intersection test patterns
- CRS (Coordinate Reference System) handling tests
- Default CRS specification
- CRS transformation test scenarios
- Antimeridian crossing test patterns
- Polar region test patterns
- Bbox validation test scenarios (min > max, invalid coordinates)
- Spatial query + pagination interaction tests
- Coordinate precision tests
- Spatial validation error scenarios
- Fixture requirements
- Implementation estimates

**Example Spatial Queries:**

- **Simple bbox**: `bbox=-180,-90,180,90` (whole world)
- **Regional bbox**: `bbox=-122.5,37.7,-122.3,37.9` (San Francisco area)
- **Antimeridian**: `bbox=170,-10,-170,10` (crosses date line)
- **Polar**: `bbox=-180,85,180,90` (Arctic region)

**Bbox Format:** `bbox=minLon,minLat,maxLon,maxLat` (4 values) or `bbox=minLon,minLat,minElev,maxLon,maxLat,maxElev` (6 values for 3D)

---

## 8. Dependencies

**Must Complete Before Starting:**

- Section 24: Query Parameter Combination Testing (parameter interaction patterns)
- Section 11: GeoJSON Testing Requirements (spatial structures)
- Section 8: CSAPI Specification Review (spatial parameter definitions)
- Section 23: Pagination Testing Strategy (spatial + pagination)

**Blocks:**

- Spatial query implementation
- Bbox parsing implementation
- CRS handling logic
- Spatial validation

---

## 9. Research Status Checklist

- [x] Phase 1: Spatial Parameter Specification Analysis - Complete (~30 min)
- [x] Phase 2: CRS and Coordinate System Analysis - Complete (~20 min)
- [x] Phase 3: Spatial Edge Case Analysis - Complete (~20 min)
- [x] Phase 4: Upstream Spatial Testing Analysis - Complete (~25 min)
- [x] Phase 5: Test Scenario Design - Complete (~40 min)
- [x] Phase 6: Fixture Design - Complete (~30 min)
- [x] Phase 7: Synthesis - Complete (~60 min)
- [x] Deliverable document created and reviewed
- [x] Cross-references updated in related documents

---

## 10. Notes and Key Findings

**Research Completed:** February 6, 2026

### Key Findings

**Spatial Parameters (2 total):**

- **bbox** - Bounding box spatial filter (PRIMARY)
- **geom** - Geometry intersection filter (NOT initially supported)

**Bbox Format:**

- 2D: `minLon,minLat,maxLon,maxLat` (4 comma-separated values)
- 3D: `minLon,minLat,minElev,maxLon,maxLat,maxElev` (6 values)

**Coordinate Reference System:**

- **Only CRS:** WGS 84 (CRS84) - longitude, latitude order
- **No CRS transformation** required (RFC 7946 constraint)
- **Coordinate ranges:** Longitude [-180, 180], Latitude [-90, 90]

**Critical Discoveries:**

1. **Antimeridian crossing NOT supported** - minLon > maxLon returns 400 Bad Request
2. **CRS simplification** - WGS 84 only, no CRS negotiation (RFC 7946)
3. **Point bbox valid** - min = max for both lon and lat represents single point
4. **3D bbox support** - Optional elevation (meters above WGS 84 ellipsoid)
5. **Polar regions** - Valid bbox queries for Arctic/Antarctic regions

**Testing Coverage:**

- Basic bbox tests: 10 tests (~150-200 lines)
- 3D bbox tests: 6 tests (~90-120 lines)
- Validation errors: 8 tests (~120-160 lines)
- Edge cases: 6 tests (~90-120 lines)
- Bbox + pagination: 4 tests (~60-80 lines)
- Bbox + temporal: 6 tests (~90-120 lines)
- Point bbox: 3 tests (~50-70 lines)
- **Total:** 43 tests, 650-850 lines

**Fixture Requirements:** 40 fixtures

- Bbox query strings: 15 fixtures
- Spatial responses: 15 fixtures
- Error responses: 10 fixtures

**Upstream Patterns:**

- Found 25 bbox tests in WMS/WMTS/WFS specs
- Found bbox-utils.ts with clampBoundingBox function
- Found FILTER_SPATIAL worker extension

**Client Workarounds:**

- Antimeridian crossing requires two separate queries (split at ±180°)
- Client merges results from east and west queries

### Related Documents

- Deliverable: [findings/29-spatial-query-testing.md](../findings/29-spatial-query-testing.md)
- Section 24: Query Parameter Combination Testing
- Section 11: GeoJSON Testing Requirements
- Section 23: Pagination Testing Strategy
- Query Parameters: [csapi-query-parameters.md](../../requirements/csapi-query-parameters.md)
- Format Requirements: [csapi-format-requirements.md](../../requirements/csapi-format-requirements.md)
- Antimeridian and polar regions require special handling

**Coordinate Reference Systems:**

- **WGS 84** (EPSG:4326): Latitude, longitude order (common in GIS)
- **CRS84**: Longitude, latitude order (GeoJSON default, RFC 7946)
- Coordinate order matters for bbox interpretation

**Spatial Edge Cases:**

- **Antimeridian crossing**: bbox where minLon > maxLon (e.g., 170 to -170)
- **Polar regions**: Latitude near ±90°
- **Coordinate wrapping**: Longitude > 180° or < -180°
- **Bbox validation**: minLat > maxLat or minLon > maxLon (non-crossing case)
- **Point on boundary**: Is point exactly on bbox boundary included?

**Spatial Parameter Precedence:**

- If multiple spatial parameters specified, what takes precedence?
- Can bbox and geometry be combined?

---

**Next Steps:** Review OGC API - Common bbox specification and GeoJSON coordinate system requirements.
