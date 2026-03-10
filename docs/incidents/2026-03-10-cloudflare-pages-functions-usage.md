# Incident Report: Cloudflare Pages Functions — 80 % Daily Request Limit

**Date:** 2026-03-10  
**Detected:** Cloudflare email notification ("account has reached 80 % of daily requests limit")  
**Severity:** Warning — service not yet degraded, but free-tier exhaustion is imminent  
**Status:** Open — mitigations planned, not yet implemented  

---

## 1. Symptoms

- Cloudflare sent an automated email stating the account had reached **80 %** of its daily Pages Functions request quota.
- The production webapp at `https://ogc-csapi-explorer.pages.dev` continued to function normally at the time of detection.
- No user-facing errors were observed, but exceeding the limit would cause **all Pages Function invocations to fail** (HTTP 500), breaking every API call the webapp makes.

## 2. Architecture Background

The csapi-explorer demo webapp uses **Cloudflare Pages Functions** as a reverse-proxy layer between the browser and the upstream OSH SensorHub server:

| Function Route | Upstream Target | Purpose |
|----------------|-----------------|---------|
| `/api/osh/[[path]]` | `https://os4csapi-osh.duckdns.org/sensorhub/api/…` | Main CSAPI proxy (all `apiFetch()` calls) |
| `/api/osh-do/[[path]]` | `https://os4csapi-osh.duckdns.org/sensorhub/api/…` | Direct-observation proxy (SSE live streams) |
| `/api/52north/[[path]]` | `https://ogc-api.nrw.de/inspire-us-hydrometeo/v1/…` | Optional 52North cross-server demo |

Every single API call the browser makes becomes **one Pages Function invocation**, counted against the daily quota.

### Cloudflare Free Tier Limit

| Metric | Limit |
|--------|-------|
| Daily Function requests | **100,000** |
| Per-invocation CPU time | 10 ms |

## 3. Root Cause Analysis

### 3.1 Map View Live-Mode Polling

The **Map View** (`/map`) is the primary consumer.  When live mode is active (the default), `refreshLiveLayers()` runs every **8 seconds** (`LIVE_REFRESH_MS = 8000`) and performs approximately **49 API calls per cycle**:

| Call Group | Approx. Calls | Description |
|------------|---------------|-------------|
| ISS orbit track observations | 1 | Latest ISS position |
| ISS deployed-system observations | 8 | Subsystem telemetry |
| Weather station observations | 10 | 10 NWS stations, 1 call each |
| NDBC buoy observations | 5 | 5 NDBC buoys, 1 call each |
| BuoyCAM observations | 5 | 5 buoy camera image URLs |
| LOB bearing observations | ~10 | Line-of-bearing tracks |
| Miscellaneous/relation calls | ~10 | Schema, system metadata, etc. |

**Result per tab:**

$$
\frac{49\ \text{calls}}{8\ \text{s}} \times 86{,}400\ \text{s/day} \approx 529{,}200\ \text{requests/day}
$$

A **single browser tab** left open on the Map page for the full day would consume **~5.3 × the daily limit**.

### 3.2 Other Contributors

| Source | Est. Share | Notes |
|--------|-----------|-------|
| Map View live-mode polling | **~90 %+** | Dominant by far |
| Initial page load / navigation | ~5 % | Systems, deployments, collections listing |
| Deployed System Card composition | ~3 % | Fetches datastreams + latest obs for info cards |
| Miscellaneous (detail views, etc.) | ~2 % | On-demand browsing |

### 3.3 Timeline to Exhaustion

| Scenario | Time to 100 K |
|----------|---------------|
| 1 tab, live-mode on | **~4.5 hours** |
| 2 tabs simultaneously | **~2.25 hours** |
| 3 tabs simultaneously | **~1.5 hours** |

## 4. Impact

- **If the limit is exceeded**: all three Pages Function routes return HTTP 500 until the counter resets at midnight UTC. The webapp becomes non-functional (no data loads, map is empty).
- **Current risk**: any developer or reviewer leaving the Map page open for several hours will exhaust the quota, blocking all other users for the rest of the day.

## 5. Recommended Mitigations

### 5.1 Increase Polling Interval (Quick Win)

Raise `LIVE_REFRESH_MS` from `8000` to `30000` or `60000`.  A 30 s interval reduces requests by ~75 %; a 60 s interval by ~87 %.

| Interval | Est. Requests/Day (1 tab) |
|----------|--------------------------|
| 8 s (current) | ~529,200 |
| 30 s | ~141,120 |
| 60 s | ~70,560 |

### 5.2 Default Live Mode to Off

Change `liveMode` default from `true` to `false` in `MapViewPage.vue`.  Users opt in only when they want real-time updates.

### 5.3 Batch / Consolidate Queries

Where possible, combine per-system observation fetches into a single parameterized query (e.g., `?system=id1,id2,…`), cutting call count per cycle.

### 5.4 Add Cache-Control Headers

For slowly-changing data (weather observations, buoy metadata), the Pages Function can add `Cache-Control: public, max-age=60` so the browser and Cloudflare CDN skip re-invocations for repeated identical requests.

### 5.5 Bypass the Proxy for Public GET Requests

If CORS is configured on the upstream Caddy server, unauthenticated read-only requests could go directly to `os4csapi-osh.duckdns.org`, bypassing Pages Functions entirely.  This requires a Caddy CORS configuration change but would reduce function invocations dramatically.

## 6. Action Items

| # | Action | Priority | Owner | Status |
|---|--------|----------|-------|--------|
| 1 | Increase `LIVE_REFRESH_MS` to 30 s | High | — | Not started |
| 2 | Default `liveMode` to `false` | High | — | Not started |
| 3 | Evaluate batch observation queries | Medium | — | Not started |
| 4 | Add Cache-Control to Pages Functions | Medium | — | Not started |
| 5 | Investigate direct CORS bypass | Low | — | Not started |

## 7. References

- Cloudflare Pages Functions limits: <https://developers.cloudflare.com/pages/functions/pricing/>
- `demo/functions/api/osh/[[path]].ts` — main proxy function
- `demo/src/pages/MapViewPage.vue` — live-mode polling logic (`LIVE_REFRESH_MS`, `refreshLiveLayers()`)
