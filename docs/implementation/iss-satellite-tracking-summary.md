# ISS Satellite Tracking — Implementation Summary

**Date:** March 5, 2026  
**Commits:** `a13f360` through `83b6ec2` (17 commits)  
**Scope:** 5 files changed, 772 insertions, 42 deletions  

---

## Objective

Add live ISS (International Space Station) satellite tracking to the CSAPI Explorer map view, demonstrating that OGC API — Connected Systems can model and render real-time space assets alongside ground-based sensor networks — all through standard CSAPI Part 1 and Part 2 resources on a single OSH server.

---

## What Was Delivered

### 1. ISS Publisher Service (`scripts/iss_publisher.py`)
- Python service using **SGP4** orbital propagation with **CelesTrak OMM JSON** TLE data
- POSTs ISS position observations every **30 seconds** to the OSH server
- Observation schema: `lat_deg`, `lon_deg`, `alt_km`, `velocity_km_s`
- Deployed as `iss-publisher.service` on the Oracle Cloud VM (systemd, auto-restart)
- Bootstrap created all required server resources:
  - Procedure `045g` (ISS SGP4 Tracker)
  - System `04ng` (ISS Zarya)
  - DataStream `04fg` (ISS Position - SGP4)
  - Deployment tree: `048g` (root) → `0490` (leaf)

### 2. Frontend Visualization
- **Orbit track rendering** with antimeridian (date-line) splitting via `splitTrackAtDateLine()`
- **Glow effect** on orbit track (wide translucent blue outer + solid cyan inner)
- **MIL-STD-2525D symbol**: Neutral (green) Satellite with LEO modifier — SIDC `10040500001101000100`
- **Symbol space**: `SS_SPACE = '05'` (first space asset in the system)
- **Live mode support**: ISS marker updates every 8 seconds, snapped to last track coordinate

### 3. Symbol Mapper Enhancements (`demo/src/symbol-mapper.ts`)
- ISS keyword rule: `['iss', 'space station', 'zarya']` → Neutral Satellite LEO
- **Word-boundary regex** for short keywords (≤3 chars) to prevent `'iss'` matching inside `'retransmission'` (which broke the relay symbol)
- Symbol size reduction: 38px → 26px (normal), 28px → 22px (small), 20px → 16px (tiny)

### 4. Anti-Blink Architecture (MapViewPage + SimulatorAdminPage)
- **Atomic source swap**: observation layers collect features into pending arrays during async fetch, then clear+addFeatures in one synchronous block — eliminates the 1-2 second visual blink where features vanish during API calls
- **Satellite race elimination**: `updateMovingSystemPositions()` skips satellite datastreams entirely; ISS position is managed exclusively by the snap-to-track-tip code in `loadObservationLayers()` — single source of truth, no race
- **Simulator poll resilience**: 3 consecutive failures required before marking disconnected (was: 1 failure → instant UI flash)

---

## Bugs Encountered and Resolved

| # | Bug | Root Cause | Fix |
|---|-----|-----------|-----|
| 1 | SamplingFeature orbit track crashed OSH | H2 database crashes on LineString geometry | Removed SF, render orbit from observations instead (`9b7f8ad`) |
| 2 | ISS marker stranded (not at orbit tip) | `limit=200` returns oldest 200 (OSH sorts oldest-first, ignores sort params) | 2-hour time window for position DS (`5dee14b`) |
| 3 | ISS marker not moving in live mode | `updateMovingSystemPositions()` not awaited | Added `await`, then later replaced with snap-to-track-tip |
| 4 | ISS symbol rendered as pink rectangle | MIL-STD entity 120900 (Space Station) not supported by milsymbol | Reverted to entity 110100 (Satellite) with Neutral identity + LEO modifier (`9c53956`) |
| 5 | Relay symbol turned green | `'iss'` keyword matched as substring inside `'retransmission'` | Word-boundary regex `\b` for keywords ≤3 chars (`e6faf1e`) |
| 6 | ISS marker offset from track (zoom view) | Separate API calls for marker vs. track returned data seconds apart; ISS moves ~7.7 km/s | Snap marker to last track coordinate — same data, zero race (`d088467`) |
| 7 | Live mode: ISS doesn't move, symbol disappears | `loadObservationLayers` cleared all sources every 8s; `skipSatellite` parameter broke initial load | Full revert to `e76475c` + 2 surgical re-applies (`252c3bc`) |
| 8 | All observations disappeared (0 count) | `skipSatellite` + `isLive` check killed observations during non-live initial load | Reverted — clean code restored (`252c3bc`) |
| 9 | UI panels blink on/off (Map + Simulator pages) | Sources cleared before fetch starts; simulator marks disconnected on 1 failed poll | Atomic swap pattern; 3-failure threshold (`4746e49`) |
| 10 | ISS marker blinks to wrong position each refresh | `updateMovingSystemPositions()` and snap-to-track-tip raced in `Promise.all` | Skip satellite DS in `updateMovingSystemPositions()` (`83b6ec2`) |

---

## Lessons Learned

1. **Revert early, revert hard.** After 5 incremental patches each introduced new regressions, reverting to the last known-good commit (`e76475c`) and surgically re-applying only 2 essential fixes was the right call. The final working state has 55 fewer lines than the broken intermediate state.

2. **One source of truth for position.** When two parallel async functions both try to set the same feature's geometry, one will always flash the wrong value. The fix is to pick one authoritative code path and exclude the other.

3. **Never clear-then-fetch.** Clearing a map source before the replacement data arrives creates a visible blink proportional to network latency. Atomic swap (collect → clear → add in one synchronous block) eliminates this entirely.

4. **OSH has quirks that must be designed around:**
   - `limit=N` returns the N **oldest** observations (no sort support)
   - H2 database crashes on certain geometry types (LineString in SamplingFeatures)
   - Scope-leak bug: per-DS observation queries return observations from other datastreams
   - `resultTime=latest&limit=1` is the only reliable way to get the most recent observation

5. **milsymbol entity coverage is incomplete.** Entity 120900 (Civilian Space Station) renders as a raw pink rectangle. Entity 110100 (Military Satellite) with Neutral identity works reliably. Always test symbol rendering before deploying.

6. **Short keyword matching needs word boundaries.** The string `'iss'` appears inside `'retransmission'`, `'mission'`, `'commissioner'`, etc. For keywords ≤3 characters, use `\bkeyword\b` regex matching.

---

## Final Architecture

```
Oracle Cloud VM (129.80.248.53)
├── OSH SensorHub (port 8181, Caddy HTTPS on 443)
│   ├── ISS Procedure (045g)
│   ├── ISS System (04ng) 
│   ├── ISS Position DataStream (04fg) — lat_deg/lon_deg/alt_km/velocity_km_s
│   └── ISS Deployment (048g → 0490)
└── iss-publisher.service (systemd, 30s cadence)
    ├── SGP4 orbital propagation (sgp4 2.25)
    └── CelesTrak OMM JSON TLE source

Cloudflare Pages (ogc-csapi-explorer.pages.dev)
├── MapViewPage.vue — orbit track + live marker
├── symbol-mapper.ts — MIL-STD-2525D Neutral Satellite LEO
└── Cloudflare Functions → reverse proxy to OSH
```

---

## Commit Log

| Hash | Time | Description |
|------|------|-------------|
| `a13f360` | 16:22 | feat: live ISS satellite tracking via SGP4 + CelesTrak |
| `9b7f8ad` | 16:49 | fix: remove SamplingFeature orbit track from ISS publisher |
| `e2494c1` | 17:29 | feat: satellite orbit track rendering — MILSYM, date-line split, glow |
| `133ca40` | 17:32 | docs: incident report — ISS orbit track rendering failures |
| `5dee14b` | 17:37 | fix: live mode fetches 2-hour window for position datastreams |
| `e76475c` | 17:44 | fix: ISS marker tracks latest position via resultTime=latest |
| `e2b6900` | 17:54 | fix: ISS symbol → Neutral Civilian Space Station (LEO) |
| `9c53956` | 18:03 | fix: revert ISS entity from Space Station (120900) to Satellite (110100) |
| `e6faf1e` | 18:15 | fix: word-boundary matching prevents relay false match |
| `db2821d` | 18:23 | fix: shrink symbols (38→30px) + position DS always uses 2-hour window |
| `60cee40` | 18:29 | fix: smaller symbols (26px) + await position sync before fitView |
| `d088467` | 18:41 | fix: snap ISS marker to last orbit track point |
| `7d80c6e` | 18:53 | fix: stable live mode — skip sat DS re-fetch, sequential marker update |
| `7843f09` | 20:55 | fix: restore observations — skipSatellite param instead of isLive check |
| `252c3bc` | 21:07 | revert MapViewPage to e76475c + 2 surgical fixes |
| `4746e49` | 21:47 | fix: eliminate UI blinking on live refresh and simulator polling |
| `83b6ec2` | 22:05 | fix: eliminate ISS marker blink during live refresh |

**Total wall-clock time:** ~6 hours (16:22 – 22:05)  
**Effective commits:** 3 features + 1 doc + 13 bug fixes (10 unique bugs)
