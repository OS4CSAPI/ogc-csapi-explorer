# Live Data Simulation — Architecture & Implementation Plan

**Date:** 2026-03-02  
**Status:** Approved for implementation  
**Scope:** Standalone Python simulator + map auto-refresh

---

## 1. Problem Statement

The current system has no way to produce a continuous stream of realistic sensor observations over time. The existing ingestion scripts (`ingest-odas-data-model.py`, `ingest-part2.py`) are one-shot bulk loaders — they POST a batch of observations and exit. The DemoPage dashboard polls for existing data but nothing is writing new data.

**Goal:** A simulator that can be started, runs for 1 hour, and every 5 seconds publishes new observations to all 3 AZ-MA sensor nodes — making it look like a UAV flies into their detection range and moves across all three arrays. The web app map should display these observations in near-real-time as they arrive.

---

## 2. Architecture Decision

**Standalone Python script** (`scripts/simulate_scenario.py`), same pattern as `bootstrap_v4.py`.

### Why not browser-side?

| Concern | Browser (Option A) | Python (Option B) |
|---------|-------------------|-------------------|
| Needs browser open for 1 hour | Yes | No |
| CORS / proxy issues | Yes | No — direct API |
| Can run headless / on server | No | Yes |
| Aligns with OSHConnect-Python tooling model | No | Yes |
| Rich CLI progress display | No | Yes (`rich` library) |
| Testable without web app | No | Yes |

The web app's role stays clean: it *consumes and displays* data. The simulator *produces* data. These are different concerns that belong in different executables. This separation is the whole point of the CSAPI architecture — any compliant client can read data regardless of how it was produced.

---

## 3. Simulator Architecture

### 3.1 File Structure

```
scripts/
  bootstrap_v4.py              ← creates the server state (exists)
  simulate_scenario.py         ← animates the server state (new)
```

If the simulator grows, it can be factored into a package:

```
scripts/simulator/
  __main__.py                  ← entry point: python -m simulator
  scenario.py                  ← UAV waypoints + interpolation
  sensor_model.py              ← bearing, range, energy, classification math
  publisher.py                 ← formats + POSTs observations to OSH
  config.py                    ← server URL, auth, tick interval, duration
```

Start with the single-file approach (matching `bootstrap_v4.py` convention).

### 3.2 Components

#### Scenario Model — UAV Flight Path

Pre-defined waypoints describing a UAV trajectory through the sensor field:

- **Spawn:** ~3 km south of the sensor string
- **Flight:** NNE at ~30 km/h (8.3 m/s), passing through all 3 detection ranges
- **Duration:** ~15–20 minutes per pass through the field
- **Pattern:** 2–3 passes over 1 hour (fly through, loop back, fly through again)

A `get_position_at_time(elapsed_seconds)` function interpolates the UAV position along the waypoint path using great-circle math.

#### Sensor Model — What Each Array "Sees"

Given a UAV position and a sensor node position, compute:

| Output | Formula | Datastream |
|--------|---------|------------|
| **Azimuth bearing** | `atan2(Δlon, Δlat)` + projection correction | LOB |
| **Slant range** | Haversine distance (m) | SSL, SST |
| **Energy** | Inverse-square law: `E = E₀ / r²`, clamped | SSL Potential Sources |
| **Detection probability** | Sigmoid based on range vs. detection envelope | Classification Probabilities |
| **Track ID** | Persistent ID assigned when UAV enters detection range | SST Tracked Sources |
| **Track state** | `new` → `tracking` → `lost` based on range vs. max | Track Updates |
| **Activity level** | `1.0` when detected, decaying when leaving range | Scene Summary |
| **Health telemetry** | Constant nominal values (CPU, mem, temp) | Health |

Detection logic: a sensor only "sees" the UAV when range < `max_detection_range` (900m per current config). LOB observations are only published for sensors that have a detection. Health is always published.

#### Observation Publisher

For each 5-second tick:

1. Compute UAV position at current elapsed time
2. For each of the 3 sensor nodes:
   - Compute range and bearing to UAV
   - If in detection range → publish LOB, SSL, SST, Track Updates, Classification, Scene Summary observations
   - Always publish Health observation
3. POST each observation to `POST /datastreams/{id}/observations`

**Observation format** (CSAPI-compliant):

```json
{
  "phenomenonTime": "2026-03-02T23:14:05Z",
  "resultTime": "2026-03-02T23:14:05Z",
  "result": {
    "timestamp": 1740956045.0,
    "azimuth_deg": 312.4,
    "elevation_deg": -2.1,
    "energy": 0.67
  }
}
```

Result schemas must match the existing datastream schemas created by `bootstrap_v4.py`.

### 3.3 Configuration

```python
BASE_URL      = "https://os4csapi-osh.duckdns.org/sensorhub/api"
AUTH          = ("os4csapi", "ogc134mm")
TICK_INTERVAL = 5          # seconds between observation cycles
DURATION      = 3600       # total simulation duration (seconds)
UAV_SPEED     = 8.3        # m/s (~30 km/h)
```

### 3.4 CLI Interface

```
python scripts/simulate_scenario.py                  # run 1-hour simulation
python scripts/simulate_scenario.py --duration 300   # 5-minute test run
python scripts/simulate_scenario.py --dry-run        # print observations without POSTing
python scripts/simulate_scenario.py --clean           # delete all simulation observations
```

### 3.5 Console Output (using `rich`)

```
╭─ ODAS Acoustic Simulation ──────────────────────────────────╮
│  Elapsed: 14:23 / 60:00  │  Tick 172/720  │  UAV: 31.6532°N, -110.2618°W  │  Hdg: 025°  │
├──────────────────────────────────────────────────────────────┤
│  AZ-MA-1: ■ DETECTED  range=743m  bearing=312°  energy=0.67 │
│  AZ-MA-2: ■ DETECTED  range=489m  bearing=287°  energy=0.84 │
│  AZ-MA-3: □ OUT OF RANGE  (1,841m)                          │
├──────────────────────────────────────────────────────────────┤
│  Published: 14 obs this tick  │  Total: 2,408 obs           │
│  ████████████████████░░░░░░░░░░  24%                        │
╰──────────────────────────────────────────────────────────────╯
```

---

## 4. Web App — Map Auto-Refresh

### 4.1 Current State

The MapViewPage does a single bulk fetch on load. No polling, no live updates. The DemoPage has an auto-refresh toggle (5-second `setInterval`) but the map does not.

### 4.2 Proposed Addition

Add a **"Live Mode" toggle** to the MapViewPage sidebar, in the Overlays section:

```
OVERLAYS
  ◎ Detection Ranges       9
  □ Satellite + Labels
  ☑ MIL-STD-2525 Symbols
  ──────────────────────
  [▶ Live Mode]  Last refresh: 22:14:05
```

When enabled:
- Every 5 seconds, re-fetch observations, observation tracks, and bearing lines
- Update the map layers in place (clear + re-add, or diff-based update)
- Show a subtle "last refresh" timestamp
- Optional: pulse animation on new features

### 4.3 Implementation

```typescript
// In MapViewPage.vue
const liveMode = ref(false)
const liveInterval = ref<number | null>(null)

function toggleLiveMode() {
  liveMode.value = !liveMode.value
  if (liveMode.value) {
    liveInterval.value = window.setInterval(refreshLiveLayers, 5000)
  } else {
    clearInterval(liveInterval.value!)
    liveInterval.value = null
  }
}

async function refreshLiveLayers() {
  // Only refresh dynamic layers, not static ones (deployments, systems)
  await Promise.all([
    loadResourceType('observations'),
    loadResourceType('observationTracks'),
    loadResourceType('bearingLines'),
  ])
}
```

This is a small addition (~30 lines) to the existing MapViewPage.

### 4.4 Time-Window Filtering (Future Enhancement)

For a polished look, add a sliding time window to observation queries:

- Only fetch observations from the last N minutes
- Older observations fade out or disappear
- Creates a "radar sweep" effect where you see the UAV's track building behind it

This is a follow-up enhancement, not required for initial functionality. The basic auto-refresh already makes the simulation visible in near-real-time.

---

## 5. Datastream Mapping

The simulator needs to know which datastream ID corresponds to which observation type for each sensor node. These are discovered at startup by querying `GET /systems/{id}/datastreams`.

| System | Server ID | Datastreams (7 per node) |
|--------|-----------|--------------------------|
| AZ-MA-1 | `0420` | LOB, SSL, SST, Track Updates, Classification, Health, Scene Summary |
| AZ-MA-2 | `0490` | (same schema, different IDs) |
| AZ-MA-3 | `049g` | (same schema, different IDs) |

The simulator queries these once at startup and caches the mapping.

---

## 6. Observation Cleanup

The simulator should tag its observations so they can be identified and cleaned up:

- Add a `simulationRun` field to observation results with a UUID or timestamp
- The `--clean` flag queries for observations with this tag and DELETEs them
- Alternatively, use time-range deletion: delete all observations in the simulation's time window

---

## 7. Implementation Order

| Phase | Work | Effort |
|-------|------|--------|
| **Phase 1** | `simulate_scenario.py` — UAV trajectory + sensor model + publisher. Dry-run mode. | 1 day |
| **Phase 2** | Live-run against Oracle server. Verify observations appear via Explorer. | 0.5 day |
| **Phase 3** | Map auto-refresh toggle ("Live Mode") on MapViewPage. | 0.5 day |
| **Phase 4** | Rich CLI console output. | 0.5 day |
| **Phase 5** | Time-window filtering + fade effect on map (polish). | 1 day |
| **Phase 6** | `--clean` flag for observation cleanup. | 0.5 day |

**Total estimated effort:** ~4 days

Phases 1–3 are the MVP. Phases 4–6 are polish.

---

## 8. Success Criteria

1. Start the simulator script from a terminal
2. Switch to the web app map view with Live Mode on
3. Watch LOB lines appear and rotate in real-time as the simulated UAV moves through the detection field
4. See observation count incrementing in the sidebar
5. The simulator runs unattended for 1 hour without errors
6. After the simulation, the full UAV track is visible as a trail of observation points on the map

---

## 9. Dependencies

- **Python 3.10+** (already available in `.venv`)
- **`requests`** library (likely already installed for bootstrap scripts)
- **`rich`** library (new dependency, for CLI console — Phase 4 only)
- No changes to the CSAPI library or server configuration required
- Datastream schemas already exist (created by `bootstrap_v4.py`)
