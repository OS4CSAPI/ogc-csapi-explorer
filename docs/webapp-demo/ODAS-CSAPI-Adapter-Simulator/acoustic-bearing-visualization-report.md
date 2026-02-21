# Acoustic Detection Bearing Visualization — Lines of Bearing on the Map

**Date:** February 20, 2026  
**Commits:** `bcc2640` (subsystem datastream discovery), `d67cfa2` (bearing lines)  
**File Modified:** `demo/src/pages/MapViewPage.vue`  
**Repository:** [OS4CSAPI/ogc-csapi-explorer](https://github.com/OS4CSAPI/ogc-csapi-explorer)

---

## 1. Objective

Render acoustic detection observations from the ODAS data model as **lines of bearing** on the Explorer's map — directional lines that originate from the sensor's geographic location and extend outward along the azimuth at which the sound was detected.

This transforms raw acoustic observation data into an intuitive spatial visualization showing not just *where* sensors are, but *what direction* they're hearing sounds from, and at what confidence level.

---

## 2. Prerequisite Fix — Subsystem Datastream Discovery

Before bearing lines could be rendered, a prerequisite bug had to be fixed: **none of the ODAS datastreams were being discovered by the map's observation pipeline**.

### Root Cause

Phase C of `buildSystemLocationCache()` fetched datastreams from the global `/datastreams?limit=200` endpoint. On OSH SensorHub, this endpoint returns 200 datastreams but does not include datastreams nested under subsystems. All five ODAS datastreams are attached to subsystems (SSL Module, SST Module, DSP Pipeline, Triangulation Engine) and were absent from the response.

Since `locationDatastreamList` had no ODAS entries, `loadObservationLayers()` had nothing to iterate and showed zero observations.

### Fix (`bcc2640`)

After Phase B populates the subsystem location cache, Phase C now also fetches `/systems/{id}/datastreams` for each cached system and merges results into the datastream pool (deduplicating by ID):

```
GET /datastreams?limit=200               → 200 items (no ODAS)
GET /systems/04fg/datastreams?limit=100  → 2 items (Health, TriPos)
GET /systems/04k0/datastreams?limit=100  → 4 items (Health, LOB, SSL, SST)
GET /systems/04kg/datastreams?limit=100  → 2 items (LOB, SSL)
GET /systems/04l0/datastreams?limit=100  → 1 item (SST)
GET /systems/04m0/datastreams?limit=100  → 1 item (TriPos)
                                         → 5 unique ODAS datastreams discovered
```

The same pattern was applied to `loadDatastreams()` and `loadControlStreams()` so all Part 2 resource types discover nested datastreams.

---

## 3. ODAS Observation Data Formats

The ODAS data model has three datastream types that encode acoustic detection directions, each using a different result schema:

### 3.1 Geographic Lines of Bearing (LOB)

**Datastream:** `072g2` — `Geographic Lines of Bearing — Array #001`  
**System:** `04kg` (SSL Module)

```json
{
  "numBearings": 1,
  "bearing0": {
    "sourceId": 42,
    "azimuth": 70.0,
    "elevation": 0.0,
    "energy": 0.85
  }
}
```

Explicit geographic azimuth in degrees from north. Five observations with azimuths 70.0° → 71.2°, tracking source #42.

### 3.2 SSL Potential Sources

**Datastream:** `071g2` — `SSL Potential Sources — Array #001`  
**System:** `04kg` (SSL Module)

```json
{
  "numSources": 2,
  "source0": { "x": 0.9397, "y": 0.342, "z": 0.0, "energy": 0.85 },
  "source1": { "x": -0.5, "y": -0.866, "z": 0.0, "energy": 0.25 }
}
```

Unit direction vectors in a local ENU (East–North–Up) frame. Convention: `x` = East, `y` = North. Two detections per observation — a strong primary source (~70°, energy 0.85) and a weaker secondary (~240°, energy 0.25).

### 3.3 SST Tracked Sources

**Datastream:** `07202` — `SST Tracked Sources — Array #001`  
**System:** `04l0` (SST Module)

```json
{
  "numTracks": 1,
  "track0": {
    "id": 42,
    "tag": "dynamic",
    "x": 0.9397, "y": 0.342, "z": 0.0,
    "activity": 0.92
  }
}
```

Same vector representation as SSL, with track persistence metadata (`id`, `tag`, `activity`).

---

## 4. Bearing Extraction — `extractBearings()`

A unified extraction function handles all three formats and returns a normalized bearing array:

```typescript
Array<{ azimuth: number; elevation: number; energy: number; sourceId?: number }>
```

| Format | Detection Method | Azimuth Source |
|---|---|---|
| LOB | `result.numBearings` present | Direct: `bearing0.azimuth` (degrees from north) |
| SSL | `result.numSources` present | Computed: `atan2(source0.x, source0.y)` → degrees |
| SST | `result.numTracks` present | Computed: `atan2(track0.x, track0.y)` → degrees |

**Vector → Azimuth conversion:** For SSL and SST, `atan2(x, y)` produces the azimuth measured clockwise from true north, matching the ENU convention where x = East and y = North. The result is normalized to [0, 360).

**Zero-vector filter:** Sources/tracks with magnitude < 0.01 are skipped (placeholder entries with `x=0, y=0`).

**Energy threshold:** Bearings with energy < 0.1 are not rendered (filters out noise and empty bearing slots like `bearing1` when `numBearings=1`).

---

## 5. Geographic Rendering

### 5.1 Origin Point

Each bearing line originates from the **sensor system's cached location**. For the ODAS data model, all sensor subsystems (SSL Module, SST Module, etc.) inherit coordinates from the Platform system, which in turn gets its location from deployment geometry via `platform@link` (see [map-visibility-fix-report.md](./map-visibility-fix-report.md)).

The SSL Module (`04kg`) at `38.8977°N, -77.0365°W` is the origin for both LOB and SSL bearing lines.

### 5.2 Endpoint Computation — `computeBearingEndpoint()`

Given a sensor location `(lat, lon)`, bearing azimuth, and line length (default: 1,000 m), the endpoint is computed using a small-distance approximation:

```
dLat = distance_m × cos(azimuth) / 111320
dLon = distance_m × sin(azimuth) / (111320 × cos(lat))
endpoint = (lat + dLat, lon + dLon)
```

This is accurate to within centimeters at distances under 10 km — well within the visualization range.

### 5.3 Line Length

`BEARING_LINE_LENGTH_M = 1000` (1 km). This is a symbolic visualization distance — actual acoustic detections may originate from sources much closer or farther. The length places bearing lines at a readable scale relative to the sensor cluster without overwhelming the map view.

---

## 6. Visual Design — Energy-Proportional Styling

Each bearing line's **stroke width and opacity** are proportional to the detection energy/confidence, making strong detections visually prominent while weak ones fade into the background:

| Energy | Opacity | Stroke Width | Visual |
|---|---|---|---|
| 0.10 (threshold) | 0.46 | 2.2 px | Barely visible — marginal detection |
| 0.25 | 0.55 | 2.5 px | Faint — secondary source |
| 0.50 | 0.70 | 3.0 px | Medium — moderate confidence |
| 0.85 | 0.91 | 3.7 px | Bold — strong primary detection |
| 1.00 | 1.00 | 4.0 px | Full — maximum confidence |

Formulas:
- `opacity = 0.4 + min(energy, 1) × 0.6`
- `width = 2 + min(energy, 1) × 2`

**Color:** Rose (`#f43f5e` / `rgba(244, 63, 94, opacity)`) — distinct from all other layer colors.

**Z-index:** 6 — rendered above observation tracks (5) but below observation points (7) and other resource markers (10).

---

## 7. Expected Bearing Count for ODAS Data

| Datastream | Obs Count | Bearings/Obs | Energy > 0.1 | Features Rendered |
|---|---|---|---|---|
| LOB (072g2) — Geographic Lines of Bearing | 5 | 1 (active only) | 5 | **5** lines ~70°–71.2° |
| SSL (071g2) — Potential Sources | 5 | 2 (source0 + source1) | 10 | **10** lines (~70° + ~240°) |
| SST (07202) — Tracked Sources | 5 | 1 (active track only) | 5 | **5** lines ~70° |
| **Total** | | | | **~20 bearing lines** |

All bearing lines radiate from the same sensor location (SSL Module at the Single Array deployment). The LOB, SSL primary, and SST bearings all point in the same direction (~70° ENE) — as expected, since they're different stages of the same acoustic localization pipeline detecting the same source.

The SSL secondary detections point ~240° (WSW) with lower energy, representing a weaker acoustic signal from a different direction.

---

## 8. Map Layer Integration

### Sidebar Legend

A new "Lines of Bearing" entry appears in the Part 2 — Dynamic Data section of the sidebar legend:

- **Color dot:** Rose (#f43f5e)
- **Label:** Lines of Bearing
- **Count:** Number of bearing line features rendered
- **Toggle:** Click to show/hide the bearing layer

### Click Interaction

Clicking a bearing line on the map opens the feature popup with:

| Field | Value |
|---|---|
| Resource Name | `Bearing 70.0° (energy 0.85)` |
| Datastream | Geographic Lines of Bearing — Array #001 |
| System ID | 04kg |
| Phenomenon Time | 2026-02-20T14:30:00Z |
| Azimuth | 70.0° |
| Elevation | 0.0° |
| Energy | 0.85 |
| Source ID | 42 (LOB/SST only) |
| Sensor Location | 38.8977, -77.0365 |

### Selected Style

When a bearing line is selected (clicked), it highlights with a thick amber stroke (`#fbbf24`, width 5 px) matching the selection style used for other layer types.

---

## 9. Zero Extra HTTP Calls

Bearing extraction is integrated directly into the existing `loadObservationLayers()` loop. The same observation fetch (`GET /datastreams/{id}/observations?limit=500`) that drives observation points and tracks is also scanned for bearing data:

```
for (const obs of items) {
  // 1. Check for lat/lon → observation points + tracks
  const loc = extractLatLonFromResult(obs.result)
  if (loc) { ... add point feature ... }

  // 2. Check for bearing data → lines of bearing
  const obsBearings = extractBearings(obs.result)
  for (const b of obsBearings) { ... add bearing feature ... }
}
```

This means adding the bearing layer costs **zero additional API calls** — all data was already being transferred.

---

## 10. ODAS Acoustic Localization Pipeline — What the Bearings Represent

The bearing lines visualize three stages of the ODAS acoustic source localization pipeline:

```
Stage 1: SSL (Sound Source Localization)
  → Beamforming on microphone array
  → Detects potential sources as direction vectors
  → Multiple candidates per frame (strong + weak)

Stage 2: SST (Sound Source Tracking)
  → Filters SSL candidates over time
  → Assigns persistent track IDs
  → Outputs smoothed direction vectors

Stage 3: LOB (Geographic Lines of Bearing)
  → Converts array-local bearings to geographic azimuths
  → Accounts for array orientation and platform heading
  → Ready for cross-array triangulation (via Triangulation Engine)
```

On the map, all three stages for the primary source point in approximately the same direction (~70° ENE), but:
- SSL shows **both** the primary and secondary (weaker) sources
- SST shows only the **tracked** source (filter applied)
- LOB shows the **geographic** bearing (orientation-corrected)

The progression from raw detection → tracked → geographic is visible through the layer, and the energy-proportional styling makes the signal-to-noise ratio immediately apparent.

---

## 11. Compatibility

The bearing extraction is additive and does not affect non-ODAS data:

- **Non-acoustic observations:** `extractBearings()` checks for `numBearings`, `numSources`, or `numTracks` in the result. Standard observations (temperature, GPS, etc.) have none of these fields, so the function returns an empty array and no bearing lines are created.
- **Other bearing formats:** The three supported schemas (LOB/SSL/SST) are checked by discriminant field presence, not by datastream name, so any observation following these result schemas will be rendered.
- **Performance:** The energy threshold (`< 0.1`) and zero-vector filter (`magnitude < 0.01`) prevent rendering of empty/placeholder entries in the result objects.

---

## 12. Files Changed

| Commit | File | Lines Changed | Description |
|---|---|---|---|
| `bcc2640` | `demo/src/pages/MapViewPage.vue` | +68 / -7 | Fetch subsystem datastreams for observation pipeline |
| `d67cfa2` | `demo/src/pages/MapViewPage.vue` | +184 / -35 | Bearing line layer, extraction, rendering, styling |

---

## 13. Relationship to Other Reports

| Report | Relationship |
|---|---|
| [ingestion-report.md](./ingestion-report.md) | Documents the 64-resource ODAS data model including the 5 datastreams (SSL, SST, LOB, TriPos, Health) whose observations drive bearing lines |
| [map-visibility-fix-report.md](./map-visibility-fix-report.md) | Documents the 3-phase location cache that provides sensor coordinates used as bearing line origins |
| [sosa-ssn-csapi-data-model.md](./sosa-ssn-csapi-data-model.md) | Defines the observation schemas (SSL Pots, SST Tracks, Geographic LOBs) that `extractBearings()` parses |
