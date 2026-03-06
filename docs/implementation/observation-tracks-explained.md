# Observation Tracks — Architecture & Implementation

**Date:** March 5, 2026

---

## What They Are

Observation tracks are **client-side-only visualizations**. They do not exist as a CSAPI resource type. There is no `/tracks` endpoint, no track object in the OSH database, and no track concept in the OGC API — Connected Systems specification.

An observation track is a `LineString` drawn on the map by connecting the geographic positions from a sequence of observations belonging to the same datastream, in chronological order.

---

## How They're Made

Inside `loadObservationLayers()` in [MapViewPage.vue](../../demo/src/pages/MapViewPage.vue), for each location datastream:

1. **Fetch observations** — up to 200 for position datastreams, fewer for LOB/bearing datastreams
2. **Parse each observation** — extract lat/lon from the `result` object (field names vary: `lat_deg`/`lon_deg` for ISS, `lat`/`lon` for ground sensors)
3. **Accumulate coordinates** — push each `[lon, lat]` pair into a `trackCoords` array
4. **Build LineString** — if 2+ coordinates exist, create an OpenLayers `LineString` feature and add it to the `trackSource` vector layer

Both observation points and observation tracks are built from **the same data in a single pass** — no extra API calls.

```
Observations from server          Client rendering
┌──────────────────────┐
│ obs 1: lat, lon      │ ──────► ● point marker
│ obs 2: lat, lon      │ ──────► ● point marker
│ obs 3: lat, lon      │ ──────► ● point marker
│ ...                  │         │
│ obs N: lat, lon      │ ──────► ● point marker
└──────────────────────┘         │
                                 ▼
                          ────── LineString (track)
                          connecting all N points
```

---

## Where They Fit in the Architecture

### Server Side (OSH SensorHub)

Only **observations** exist. Each observation is an independent JSON object:

```json
{
  "phenomenonTime": "2026-03-05T22:00:00Z",
  "resultTime": "2026-03-05T22:00:00Z",
  "result": {
    "lat_deg": 31.66,
    "lon_deg": -110.28,
    "alt_km": 420.5,
    "velocity_km_s": 7.66
  }
}
```

The server has no knowledge of tracks. It stores individual time-stamped observations in datastreams.

### Client Side (MapViewPage)

The map view creates **three layers** from the same observation fetch:

| Layer | Source Key | What It Shows |
|-------|-----------|---------------|
| Observation Points | `observationPoints` | Individual dot markers at each observation's lat/lon |
| Observation Tracks | `observationTracks` | LineString connecting all points from the same datastream |
| Lines of Bearing | `bearingLines` | Bearing/LOB lines from sensor nodes toward detected targets |

The sidebar count "Observation Tracks: N" is the number of distinct `LineString` features — one per datastream that produced position observations.

---

## Current Tracks on the Map

As of this writing, the map shows **2 observation tracks**:

### 1. ISS Orbit Track
- **Datastream:** ISS Position - SGP4 (`04fg`)
- **Style:** Cyan dashed line with translucent blue glow
- **Data window:** 2-hour rolling window (~200 observations at 30s cadence)
- **Special handling:** `splitTrackAtDateLine()` breaks the line at ±180° longitude to avoid a straight line spanning the entire map when the orbit crosses the antimeridian
- **Marker snap:** ISS deployment/system features are snapped to the last track coordinate to guarantee the marker sits exactly on the track tip

### 2. UAV Ground Track
- **Datastream:** Position observations from the simulator's sensor nodes
- **Style:** Default observation track style (solid line)
- **Data window:** Up to 200 observations (most recent, using 2-hour time window in live mode)

---

## Anti-Blink Pattern

Observation tracks (along with points and bearings) use an **atomic swap** pattern to avoid visual flickering during live refresh:

1. New features are collected into **pending arrays** during the async fetch
2. Only after all API calls complete, sources are **cleared and repopulated in one synchronous block**
3. The source is empty for <1ms instead of 1-2 seconds

This was implemented in commit `4746e49` after users reported visible blinking on every 8-second live refresh cycle.

---

## Key Constraints

- **OSH returns oldest-first:** `limit=200` returns the 200 *oldest* observations, not the most recent. For position datastreams, we work around this by first querying `resultTime=latest&limit=1` to discover the newest timestamp, then fetching a 2-hour time window ending at that timestamp.
- **No server-side sorting:** OSH ignores sort parameters. Chronological order within the time window is the only ordering available.
- **Scope-leak bug:** OSH per-datastream observation queries sometimes return observations from other datastreams. The track building code tolerates this because `extractLatLonFromResult()` naturally rejects observations with incompatible result schemas.
