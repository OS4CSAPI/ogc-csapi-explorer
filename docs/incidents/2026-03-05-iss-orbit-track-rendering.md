# Incident Report: ISS Orbit Track Rendering Failures

**Date:** 2026-03-05  
**Detected:** ~17:15 EST (operator observed broken rendering on Map view)  
**Root causes:** 3 (server bug, publisher design flaw, browser cache)  
**Severity:** Medium — broke ALL SamplingFeature rendering site-wide; ISS track unusable  

---

## 1. Symptoms

On the Map view at `https://ogc-csapi-explorer.pages.dev/map`:

- ISS (ZARYA) Tracker rendered as a **large blue rectangle** (generic MIL-STD-2525 Land Unit) instead of a satellite symbol
- Only **3 observation points** visible as scattered pink dots — no coherent orbit track
- **0 Sampling Features** displayed — including pre-existing SENREP track SFs that had previously worked
- ISS marker label showed correct coordinates (`43.42540°, 42.55700°`) but icon was wrong

## 2. Root Cause Analysis

### RC-1: OSH H2 Database Crash on LineString SamplingFeature (Critical)

The ISS publisher (`iss_publisher.py`) created a SamplingFeature (`0420`) containing a `LineString` geometry (91-point ISS orbit track). OSH's H2 database backend **crashes with HTTP 500** when attempting to serialize LineString geometries in SamplingFeature resources.

**Impact:** This was not isolated — the `GET /samplingFeatures?limit=200` endpoint returned **partial JSON followed by a 500 error**, poisoning the entire SamplingFeature listing response. This broke rendering of ALL SamplingFeatures across the site, including existing SENREP track SFs used by the acoustic sensor network.

**Evidence:**
```
GET /sensorhub/api/samplingFeatures?limit=200  → partial JSON, then HTTP 500 (truncated response)
GET /sensorhub/api/samplingFeatures/0420       → HTTP 500 (direct access also crashes)
DELETE /sensorhub/api/samplingFeatures/0420    → 204 (fixed the listing immediately)
```

**Conclusion:** This is a **known limitation of OSH's H2 storage layer** — LineString geometry in SamplingFeatures triggers a serialization crash. Point geometries work fine. This should be reported upstream if/when appropriate.

### RC-2: Publisher Re-creating Broken SF Every 5 Minutes

The ISS publisher had a 5-minute refresh loop that:
1. Propagated the ISS orbit ±45 minutes into past/future (91 points)
2. Built a LineString geometry from those points
3. PUT/POST'd it as a SamplingFeature

After the operator deleted the broken SF `0420`, the publisher **recreated it within 5 minutes**, re-poisoning the endpoint. This required stripping all SF code from the publisher (~95 lines removed).

### RC-3: No Satellite Symbol in MIL-STD-2525 Mapper

The symbol mapper (`symbol-mapper.ts`) had no keyword rules for `satellite`, `iss`, `sgp4`, `orbital`, `zarya`, or `space`. The ISS deployment fell through to the default "friendly land unit" symbol — a blue rectangle — which is visually meaningless for a satellite.

### RC-4: No Antimeridian (Date Line) Track Splitting

The orbit track LineString renderer drew a single continuous line from the first observation to the last. When the ISS crossed ±180° longitude, this produced an **ugly horizontal line spanning the entire map** instead of splitting into separate arc segments.

### RC-5: Browser Cache Serving Stale JS

A prior Cloudflare deploy reported "0 files uploaded (15 already uploaded)" — the content hash hadn't changed because the relevant code changes were already deployed but the browser was serving a cached older bundle. The operator needed `Ctrl+Shift+R` to see the `lat_deg`/`lon_deg` extraction code that was already in production.

## 3. Resolution

| Fix | Commit | Description |
|-----|--------|-------------|
| Delete broken SF | (manual) | `DELETE /sensorhub/api/samplingFeatures/0420` — restored SF endpoint |
| Strip SF code from publisher | `9b7f8ad` | Removed ~95 lines: `build_orbit_track()`, `update_sampling_feature()`, SF constants, SF update loop, SF stats |
| Add satellite MILSYM | `e2494c1` | Added `SS_SPACE` + `ENT_SATELLITE` to symbol mapper; keyword rules for satellite/ISS/SGP4/ZARYA/orbital/NORAD |
| Antimeridian track splitting | `e2494c1` | `splitTrackAtDateLine()` breaks LineString at ±180° lon crossings |
| Orbit track glow style | `e2494c1` | Solid cyan line with translucent glow halo (distinct from dashed acoustic tracks) |
| Satellite obs point style | `e2494c1` | Smaller cyan dots for satellite positions vs. pink generic obs points |

Publisher restarted on Oracle VM as `iss-publisher.service` (SF code removed). Service confirmed running with observations flowing at 30s cadence.

## 4. Lessons Learned

1. **Never create LineString SamplingFeatures on OSH** — H2 backend cannot serialize them. Use Point SFs only, or render tracks client-side from observation history.
2. **Automated publishers must not silently re-create server-side resources** — the 5-minute SF refresh loop undid the manual fix within minutes. Publisher patterns should be idempotent and fail gracefully.
3. **Cloudflare cache vs. browser cache** — even when Cloudflare reports all files already uploaded (content-hash match), browsers may still cache older bundles. Always verify with hard refresh after deploys.
4. **Symbol mapper keyword coverage** — any new domain (space, maritime, cyber, etc.) needs explicit keyword rules or it falls through to a meaningless default icon.

## 5. Server Resource Reference

| Resource | ID | Status |
|----------|----|--------|
| Procedure — SGP4 Orbital Propagation | `045g` | Active |
| System — ISS Tracker (SGP4 Position Feed) | `04ng` | Active |
| DataStream — ISS Position (SGP4) | `04fg` | Active (30s obs cadence) |
| Root Deployment — Orbital Tracking Demo | `048g` | Active |
| Leaf Deployment — ISS (ZARYA) Tracker | `0490` | Active (platform@link → 04ng) |
| SamplingFeature — ISS Orbit Track | `0420` | **DELETED** (caused H2 crash) |
