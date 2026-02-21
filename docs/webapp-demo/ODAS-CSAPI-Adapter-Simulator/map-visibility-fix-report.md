# ODAS Map Visibility Fix — Explorer MapViewPage Location Cache Overhaul

**Date:** February 20, 2026  
**Commit:** `37a76d4`  
**File Modified:** `demo/src/pages/MapViewPage.vue`  
**Repository:** [OS4CSAPI/ogc-csapi-explorer](https://github.com/OS4CSAPI/ogc-csapi-explorer)

---

## 1. Problem

After ingesting the full 64-resource ODAS data model (see [ingestion-report.md](./ingestion-report.md)), the Explorer's **Map View** displayed only the 5 deployment features that have inline GeoJSON geometry. All other resource types — systems, datastreams, observations, control streams — were invisible. The observation points/tracks layers showed zero features.

### What Should Have Appeared

| Resource Type | Count | Expected Map Behavior |
|---|---|---|
| Systems | 14 | Enriched from deployment/observation locations |
| Deployments | 5 | Direct geometry (Point + Polygon) ✅ already visible |
| Procedures | 5 | Geometry is always `null` (expected — no fix needed) |
| Sampling Features | 3 | Enriched from parent system locations |
| Datastreams | 5 | Placed at parent system's location |
| Control Streams | 1 | Placed at parent system's location |
| Observation Points | 3 | Triangulated-position observations have lat/lon results |
| Observation Tracks | 0–1 | Triangulated-position coordinates form a track |

Only the 5 deployments were visible. Everything else was invisible or showed 0 count in the legend.

---

## 2. Root Cause

The `buildSystemLocationCache()` function was the sole mechanism for determining where to place non-geometry resources on the map. It worked by:

1. Fetch all datastreams from the server
2. Filter to "location-related" datastreams (GPS/location data)
3. Fetch the latest observation from each
4. Extract `lat`/`lon` from the observation result
5. Cache the coordinates keyed by parent system ID

The ODAS data model has **zero GPS or location datastreams**. Its five datastreams are all domain-specific:

| Datastream | Type | Observation Fields |
|---|---|---|
| SSL Potential Sources | Acoustic DOA | `{numSources, source0: {x, y, z, energy}, ...}` |
| SST Tracked Sources | Acoustic tracking | `{numTracks, track0: {id, tag, x, y, z, activity}, ...}` |
| Geographic Lines of Bearing | Acoustic bearing | `{numBearings, bearing0: {sourceId, azimuth, elevation, energy}, ...}` |
| Triangulated 3D Source Positions | Geographic | `{latitude, longitude, altitude, accuracy, confidence, numArrays}` |
| System Health and Status | Telemetry | `{cpuLoad, usbConnected, activeTrackCount, bufferHealth, threshold}` |

None of these matched the old filter which checked for:
- Name containing `gps_data` or `location`
- `observedProperties` containing `Location` in definition or label

**Result:** Empty location cache → every enrichment and Part 2 placement path failed → nothing visible on the map.

### Secondary Issues

Even if the cache had been populated, two additional problems would have prevented full visibility:

1. **No deployment-to-system location propagation**: The ODAS systems (Platform, SSL Module, SST Module, etc.) all have `geometry: null`. The deployments have geometry and are linked to systems via `platform@link`, but the old code never read `platform@link` to derive system locations from deployment coordinates.

2. **No subsystem inheritance**: The ODAS data model has deeply nested subsystems (Platform → DSP Pipeline → SSL Module). Even if the platform system got a location, its children (which own the datastreams) would not inherit it.

3. **Narrow coordinate extraction**: The `Triangulated 3D Source Positions` datastream uses `result.latitude` / `result.longitude` field names. The old extractor only handled `result.lat` / `result.lon`, `result.Location.lat`, and `result.location.lat`.

---

## 3. Fix — Three-Phase Location Cache

The `buildSystemLocationCache()` function was refactored into a three-phase pipeline that combines multiple location discovery strategies:

```
┌──────────────────────────────────────────────────────────┐
│              buildSystemLocationCache()                   │
│                                                          │
│  Phase A: Static geometry from loaded Part 1 features    │
│    • Systems with non-null geometry → cache by ID        │
│    • Deployments → platform@link → cache system ID       │
│                                                          │
│  Phase B: Subsystem location propagation                 │
│    • For each cached system, fetch /subsystems           │
│    • Propagate parent location to all children           │
│                                                          │
│  Phase C: Observation-derived locations (broadened)       │
│    • Datastream filter: name + observedProperty match    │
│    • Coordinate extraction: 5 field-name conventions     │
│    • Include ALL DS for spatially-cached systems         │
└──────────────────────────────────────────────────────────┘
```

### Phase A: `cacheLocationsFromLoadedFeatures()`

Scans already-loaded Part 1 OpenLayers features (which `loadResourceType()` has already placed on the map) and extracts coordinates:

**Systems with geometry:** Extract Point coordinates directly from the OL feature. (Not applicable to ODAS — all systems have `geometry: null`.)

**Deployments → `platform@link` → system ID:** For each deployment feature that has geometry:

1. Read the centroid (Point coordinates or Polygon extent center)
2. Read `platform@link` from the raw GeoJSON properties
3. Extract the system ID from the link's `href` (last path segment)
4. Cache `{ lat, lon }` keyed by the system ID

For the ODAS data, this gives the Platform system (`04fg`) the coordinates of the Single Array deployment (`-77.0365, 38.8977`) — the first deployment loaded.

### Phase B: `cacheSubsystemLocations()`

For every system now in the location cache, fetches `/systems/{id}/subsystems?limit=200` and propagates the parent's cached location to all children:

```
Platform (04fg): { lat: 38.8977, lon: -77.0365 }  ← from deployment geometry
  ├── Mic Array (04g0):   inherit → { lat: 38.8977, lon: -77.0365 }
  ├── DSP Pipeline (04k0): inherit → { lat: 38.8977, lon: -77.0365 }
  │   ├── SSL Module (04kg): inherit → { lat: 38.8977, lon: -77.0365 }
  │   └── SST Module (04l0): inherit → { lat: 38.8977, lon: -77.0365 }
  ├── Config Actuator (04lg): inherit → { lat: 38.8977, lon: -77.0365 }
  └── Tri Engine (04m0): inherit → { lat: 38.8977, lon: -77.0365 }
```

If a subsystem has its own non-null geometry, that takes priority over the inherited location.

**Note:** OSH supports the `/systems/{id}/subsystems` endpoint (it's part of the vertical data path), so this call succeeds reliably.

### Phase C: Broadened observation-derived locations

The existing observation-based strategy remains as a fallback for servers with GPS datastreams, but with two improvements:

**Broadened datastream filter** (`isLocationRelatedDatastream()`):

| Old Filter | New Filter |
|---|---|
| Name contains `gps_data` or `location` | + `position` |
| Property definition/label contains `Location` | + `latitude`, `longitude`, `geodeticlatitude`, `geolocation` |

This catches the ODAS "Triangulated 3D Source Positions" datastream via the `GeodeticLatitude` definition URI.

**Expanded observation layer list:** After the location filter, the code now also adds **all datastreams** for any system that has a cached location (from Phase A/B). This ensures that even non-geographic datastreams (SSL, SST, System Health) get included in the observation layer pipeline — their observations won't have map coordinates, but datastreams/control streams attached to those systems will be correctly placed.

---

## 4. Shared `extractLatLonFromResult()` Helper

A new utility function consolidates coordinate extraction from observation results, replacing duplicated inline logic in both `buildSystemLocationCache()` and `loadObservationLayers()`:

| Convention | Fields | Example Source |
|---|---|---|
| Direct `lat`/`lon` | `result.lat`, `result.lon` | GPS location datastreams |
| Nested `Location` | `result.Location.lat`, `result.Location.lon` | OSH weather stations |
| Nested `location` | `result.location.lat`, `result.location.lon` | Generic location wrapper |
| Full-word | `result.latitude`, `result.longitude` | ODAS Triangulated Positions |
| Capitalized | `result.Latitude`, `result.Longitude` | Various GIS conventions |

The `alt`/`altitude`/`Altitude` field is also extracted when present.

This resolves the secondary issue where the Triangulated Positions observations (which use `latitude`/`longitude` naming) were invisible because the old extractor only handled `lat`/`lon`.

---

## 5. ODAS Data Flow on the Map (After Fix)

With the three-phase cache, the full ODAS resource graph becomes visible:

### Step 1: Part 1 features load

| Type | Loaded | With Geometry | Notes |
|---|---|---|---|
| Systems | 14 | 0 | All have `geometry: null` |
| Deployments | 5 | 5 | Points + Polygon ✅ |
| Procedures | 5 | 0 | Always `null` per spec |
| Sampling Features | 3 | 0 | All have `geometry: null` |

### Step 2: Location cache builds

| Phase | Systems Cached | Source |
|---|---|---|
| A (deployments) | 1 — Platform `04fg` | `platform@link` on deployment with Point geometry |
| B (subsystems) | +6 — DSP, SSL, SST, Actuator, Tri, MicArray | Inherited from Platform |
| C (observations) | +0 | Triangulated Positions DS matched but system already cached |

**Total cached:** 7 systems with coordinates.

### Step 3: Enrichment

| Type | Enriched | Source |
|---|---|---|
| Systems | 7 | From cache (null geometry → placed at deployment location) |
| Sampling Features | ~3 | From parent system cache via `/systems/{id}/samplingFeatures` |

### Step 4: Part 2 placement

| Type | Placed | Mechanism |
|---|---|---|
| Datastreams | 5 | `system@id` → location cache → deployment coordinates |
| Control Streams | 1 | `system@id` → location cache → deployment coordinates |

### Step 5: Observation layers

| Layer | Features | Source |
|---|---|---|
| Observation Points | 3 | Triangulated Positions DS: `latitude`/`longitude` in result ✅ |
| Observation Tracks | 1 | 3 coordinates form a short track ✅ |
| (Other DS observations) | 0 | SSL/SST/LOB/Status have no geographic coords — correctly skipped |

---

## 6. Before / After Summary

| Metric | Before | After |
|---|---|---|
| Systems on map | 0 | 7 (enriched from deployment geometry) |
| Deployments on map | 5 | 5 (unchanged — direct geometry) |
| Datastreams on map | 0 | 5 (placed at parent system location) |
| Control streams on map | 0 | 1 (placed at parent system location) |
| Observation points | 0 | 3 (triangulated positions) |
| Observation tracks | 0 | 1 (triangulated position trail) |
| Sampling features | 0 | ~3 (enriched from parent system) |
| **Total visible features** | **5** | **~25** |

---

## 7. Compatibility

The fix is **fully backward-compatible** with existing server data:

- **Servers with GPS datastreams** (the original design target): Phase C still finds them, exactly as before — the broadened filter is a strict superset of the old filter.
- **Servers without deployment `platform@link`**: Phase A simply doesn't find any deployment→system mappings; the cache remains empty for those servers and falls through to Phase C.
- **Servers that don't support `/subsystems`**: Phase B catches the error and skips quietly — no subsystem propagation, but no crash either.
- **Observation coordinate extraction**: The new `extractLatLonFromResult()` checks all five conventions in priority order; existing `lat`/`lon` patterns match first.

---

## 8. Files Changed

| File | Lines Changed | Description |
|---|---|---|
| `demo/src/pages/MapViewPage.vue` | +185 / -37 | Refactored `buildSystemLocationCache()` into 3-phase pipeline; added `extractLatLonFromResult()`, `isLocationRelatedDatastream()`, `cacheLocationsFromLoadedFeatures()`, `cacheSubsystemLocations()` |

---

## 9. Relationship to Other Fixes

This fix builds on the `@link` association work documented in [Sections 11–14 of the ingestion report](./ingestion-report.md#11-cross-resource-associations-link-fields):

- **Phase A** reads `platform@link` from deployment properties — this field was added by the `fix-associations.py` script and the updated `ingest-odas-data-model.py`
- **Phase C** reads `system@id` from datastream responses — this is a raw server field that the library parsers strip (tracked in [ogc-client-CSAPI\_2 #103](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/103))
- The `@link` property gap analysis report ([csapi-link-property-gap-analysis.md](../csapi-link-property-gap-analysis.md)) documents why the library doesn't preserve these fields and the upstream issues filed to fix it
