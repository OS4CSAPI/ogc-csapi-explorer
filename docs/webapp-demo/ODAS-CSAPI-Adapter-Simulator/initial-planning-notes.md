# ODAS CSAPI Adapter Simulator — Initial Planning Notes

**Date:** 2026-02-20
**Status:** Early exploration / feasibility assessment

---

## Background

This document captures the initial discussion and planning around building a CSAPI adapter for [ODAS (Open embeddeD Audition System)](https://github.com/introlab/odas) — an open-source C library for real-time sound source localization, tracking, separation, and post-filtering using microphone arrays.

The goal is to explore whether ODAS output data can be modeled as OGC API - Features collections and consumed through the CSAPI client library.

---

## What ODAS Does

ODAS is a processing pipeline with four main stages:

1. **SSL (Sound Source Localization)** — Identifies potential sound sources from microphone array input. Outputs `pots` (potential sources) as JSON: `{ x, y, z, E }` where `(x, y, z)` is a direction on a unit sphere and `E` is energy.

2. **SST (Sound Source Tracking)** — Assigns persistent IDs to sources and tracks them over time. Outputs `tracks` as JSON: `{ id, tag, x, y, z, activity }` where direction vectors are maintained across frames with identity persistence.

3. **SSS (Sound Source Separation)** — Produces separated audio streams per tracked source.

4. **Classification** — Categorizes tracked sources (e.g., speech vs. noise).

ODAS is written entirely in C, optimized for low-cost embedded hardware, and outputs data as JSON over TCP sockets or to files. It uses Kalman or particle filters for tracking. It supports configurable microphone array geometries (e.g., the 8SoundsUSB and 16SoundsUSB open-source hardware arrays).

Key source structures from the codebase:
- `tracks_obj`: `nTracks`, `ids` (unsigned long long), `tags` (char strings), `array` (float xyz × nTracks), `activity` (float per track)
- `msg_tracks_obj`: wraps `tracks_obj` with `timeStamp` and `fS` (sample rate)
- `pots` output: array of `{ x, y, z, E }` per potential source

---

## Feasibility Assessment: Can ODAS Map to CSAPI?

**Yes.** The mapping is natural, with one key nuance.

### What maps well

- ODAS outputs structured JSON — already machine-readable
- Tracks have **persistent IDs** — natural for feature identity in OGC API
- **Temporal data** (timestamps) is already present in the output
- The **collections pattern** (`pots`, `tracks`, `categories`) maps cleanly to OGC API - Features collections
- Standard OGC filtering applies: time windows, spatial bounding boxes, property filters (energy threshold, activity level, source ID)

### The coordinate nuance

ODAS direction vectors `(x, y, z)` are on a **unit sphere relative to the array**, not geographic coordinates. They represent the *direction* a sound is coming from, not a location in lat/lon space.

To make this geospatial, we need:
- The array's **geographic position** (lat/lon, from GPS or manual config)
- The array's **orientation** (heading/north reference)
- A projection from unit-sphere direction → true azimuth bearing

---

## Line of Bearing (LOB) Approach

This is the key insight that makes the data genuinely spatial: each detected source direction becomes a **Line of Bearing** on the map.

### How it works

1. Sensor position is known (lat/lon)
2. Sensor orientation/heading is known (north reference)
3. ODAS gives a direction vector `(x, y, z)` for each detected source
4. Convert to **azimuth**: `atan2(x, y)` + sensor heading offset → true bearing in degrees
5. Project a **LineString** from sensor position outward along that bearing for a configurable range

Each LOB is a standard GeoJSON `LineString` feature — two points: the sensor origin and a projected endpoint.

### Example LOB as GeoJSON

```json
{
  "type": "Feature",
  "geometry": {
    "type": "LineString",
    "coordinates": [
      [-77.0365, 38.8977],
      [-77.0341, 38.8992]
    ]
  },
  "properties": {
    "sensor_id": "array-01",
    "azimuth_deg": 32.5,
    "elevation_deg": 5.2,
    "energy": 0.87,
    "source_id": 42,
    "tag": "dynamic",
    "activity": 0.95,
    "timestamp": "2026-02-20T14:30:00Z"
  }
}
```

### Multi-array triangulation

With **two or more arrays**, intersecting LOBs yield triangulated source positions:
- Each array produces LOBs independently
- Where lines intersect = estimated source position (`Point` feature)
- Angular error creates an uncertainty area (`Polygon` feature)

---

## Proposed OGC API - Features Collections

| Collection | Geometry | Description | Key Properties |
|---|---|---|---|
| `sensors` | `Point` (lat/lon) | Microphone array locations | orientation, mic_count, config, status |
| `bearings` | `LineString` (sensor → projected point) | Lines of bearing from detected sources | azimuth, elevation, energy, timestamp, source_id |
| `tracks` | `Point` (triangulated) or `LineString` (history) | Tracked source positions over time | id, tag, activity, classification, confidence |
| `intersections` | `Point` + `Polygon` (uncertainty) | Multi-array triangulated positions | contributing_sensors, timestamp, confidence |

---

## Data Flow Architecture

```
ODAS (or Simulator)          Adapter Layer              OGC API - Features
┌─────────────┐        ┌──────────────────┐        ┌─────────────────────┐
│ SSL → pots  │───────►│ Direction → LOB  │───────►│ bearings collection │
│ {x,y,z,E}   │        │ (azimuth from    │        │ (LineString)        │
│              │        │  sensor position │        │                     │
│ SST → tracks│───────►│  + orientation)  │───────►│ tracks collection   │
│ {id,tag,    │        │                  │        │ (Point / LineString)│
│  x,y,z,     │        │ Triangulation    │───────►│ intersections       │
│  activity}  │        │ (multi-array)    │        │ (Point + Polygon)   │
└─────────────┘        └──────────────────┘        └─────────────────────┘
```

---

## Simulator Purpose

For development and testing without requiring physical microphone arrays and a running ODAS instance, the **simulator** component will:

- Generate realistic ODAS-format `pots` and `tracks` JSON output
- Model moving sound sources with configurable trajectories
- Support multiple virtual sensor arrays at configurable geographic positions
- Produce data consumable by the adapter layer (same format as real ODAS TCP socket output)

---

## Analogies and Prior Art

This approach mirrors how military/intelligence direction-finding (DF) systems work — using radio signal bearings rather than sound, but the same LOB + triangulation geometry. It's a well-understood pattern in SIGINT and acoustic surveillance domains.

---

## Findings from IROS2017 Paper

**Paper:** "Localization of RW-UAVs Using Particle Filtering Over Distributed Microphone Arrays"
*Lauzon, Grondin, Létourneau, Lussier Desbiens, Michaud — IEEE/RSJ IROS 2017*
**File:** `IROS2017-multi-array-localization.pdf` (in this folder)

### Paper Summary

The paper demonstrates **3D localization of drones** by combining Sound Source Localization (SSL) from multiple distributed microphone arrays using particle filtering. Three 8-microphone arrays were placed in a 10m triangle on the ground and used to track a Parrot Bebop 2 drone outdoors, with GPS providing ground truth.

Each array produces a **Direction of Arrival (DOA)** — a unit vector **q** pointing toward the loudest sound source, plus an energy value **e**. This is exactly the `{x, y, z, E}` format ODAS outputs as SSL "pots." A central node collects DOAs from all arrays and uses particle filtering to estimate the 3D source position.

### Key Takeaways for Our Effort

#### 1. Validates the LOB Architecture
The paper's entire approach is what we planned: each array produces a direction vector, multiple arrays' directions combine to find position. Our LOB-as-GeoJSON-LineString idea maps 1:1 to their DOA vectors. This isn't a simplification — it's literally how the system works.

#### 2. Ray-to-Ray Intersection Math
Equations 18–22 provide the triangulation algorithm we need for the `intersections` collection. For two arrays at positions L_a and L_b with DOA unit vectors q_a and q_b, the nearest intersection point is:

```
Z_ab = ( (L_a + G_a * q_a) + (L_b + G_b * q_b) ) / 2
```

For K arrays, average all K(K-1)/2 pair intersections. This translates directly into computed Point features with uncertainty polygons.

#### 3. Data Flow Matches Our Pipeline
Their block diagram maps cleanly:
- **Per-array SSL** → ODAS `ssl_pots` → our `bearings` collection (LineString)
- **Central fusion** → particle filter / Ray-to-Ray → our `intersections` collection (Point)
- **Tracking state** → particle birth/death → our `tracks` collection (updates over time)

#### 4. Realistic Simulation Parameters
The paper provides concrete values to model:

| Parameter | Value | Relevance |
|---|---|---|
| Energy threshold (E_T) | 600 | Source detection vs. noise discrimination |
| Particle count (H) | 500 | Tracker complexity |
| Array spacing | 10m triangle | Practical geometry baseline |
| Sample rate | 48,000 Hz | Audio acquisition (ODAS default is 16kHz) |
| Position variance (σ_pos) | 25 | Gaussian spread for initial position estimate |
| Velocity variance (σ_vel) | 25 | Gaussian spread for speed estimate |
| Angle deviation (σ_φ) | 0.0961 rad (~5.5°) | DOA accuracy — drives LOB beam width |
| New source threshold (T_new) | 0.75 | Detection confidence threshold |
| Remove threshold (T_remove) | 0.3 | Track loss threshold |
| Consecutive frames to confirm (F_new) | 10 | Prevents false positive detections |
| Consecutive frames to remove (F_remove) | 10 | Prevents premature track loss |

**Motion state model** (per particle):
| State | Damping (α) | Excitation (β) | Probability |
|---|---|---|---|
| Stationary | 2 | 0.05 | 10% |
| Constant velocity | 0.5 | 3 | 40% |
| Acceleration | 1.5 | 6 | 50% |

#### 5. Important Constraints to Model
- **Z-axis precision degrades** as elevation increases (far-field effect with ground-plane arrays) — our uncertainty polygons should be elliptical, elongated vertically
- **Single loudest source tracked** per filter instance — simulator should respect this for v1
- **Time synchronization** only needs ~100ms precision via NTP — relevant for distributed array timing
- **Background noise interference** (trucks, speech, vehicles) causes tracking dropouts — useful for realistic sim scenarios

#### 6. Refined Collection Schema

Based on the paper's data structures:

| Collection | Geometry | Key Properties |
|---|---|---|
| `sensors` | Point | array_id, mic_count, position (lat/lon + height), orientation |
| `bearings` | LineString | array_id, azimuth, elevation, energy, timestamp, confidence (P_k) |
| `tracks` | Point (+ history as LineString) | track_id, position_3d, velocity, motion_state (stationary/constant/accel), particle_weight_diversity |
| `intersections` | Point + Polygon uncertainty | source_arrays, ray_ray_distance, estimated_position, uncertainty_ellipse |

#### 7. Future Roadmap Alignment
Their planned improvements map to incremental features we could add:
- Time-frequency masking for noise robustness → "noise conditions" parameter in simulator
- Multi-source SST per array → multiple simultaneous tracks in our collections
- Elevation-based filtering (ignore ground sources) → filter property in our API

---

## Hardware Reference

**XMOS xCORE 7-microphone array** — The physical device under consideration:
- 7 PDM MEMS microphones in circular arrangement
- XMOS xCORE multicore microcontroller for real-time processing
- USB Audio Class 1.0 interface
- Compact form factor suitable for distributed deployment

The paper used 8-microphone arrays (8SoundsUSB), but the same principles apply to 7-mic or any geometry — ODAS configuration specifies each mic's position, uncertainty, and directivity.

---

## Open Questions

- What microphone array configuration to simulate (7-mic circular matching XMOS, or 8-mic matching the paper)?
- Should the simulator run as a standalone server or integrate into the existing demo app?
- What geographic scenario to default to (indoor room-scale, outdoor campus, urban area)?
- Should we model elevation angles or flatten to 2D bearings for the initial version?
- How to represent uncertainty / confidence in the LOB (beam width as a wedge polygon, using σ_φ ≈ 5.5° from the paper)?
- Should we implement the full particle filter, or start with simpler Ray-to-Ray intersection only?

---

## Next Steps

- [ ] Design the simulator data generation module (using paper parameters as defaults)
- [ ] Define the adapter transformation layer (unit sphere → geographic LOB)
- [ ] Implement Ray-to-Ray triangulation for the `intersections` collection
- [ ] Implement OGC API - Features endpoint serving the collections
- [ ] Build a visual demo showing LOBs on a map
- [ ] Test integration with the CSAPI client library
- [ ] Add noise/interference modeling for realistic simulation scenarios
