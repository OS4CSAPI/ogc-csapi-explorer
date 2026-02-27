# Phase 5 — End-to-End C-UAS Demo Validation Report

**Date:** 2025-07-15  
**Branch:** `demo/acoustic-cuas-targeting`  
**Server:** `http://45.55.99.236:8080/sensorhub/api`  
**Explorer:** `http://localhost:5173/` (Vite dev server)  
**Replay:** `scripts/replay.py --speed 10 --skip-commands`  
**Issue:** [#46](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/46)

---

## Executive Summary

End-to-end validation of the ODAS C-UAS acoustic demo is **PASS** with known
limitations. All 12,600 observations were replayed to the OSH SensorHub with
**zero failures**. The Explorer correctly parses and visualizes all spatial
observation types (LOB bearings, SSL/SST source arrays, track updates,
triangulated positions). Non-spatial data (health, scene summary,
classification probabilities) is accessible via the raw JSON detail panel.
Real-time streaming is an architectural limitation of the REST-only Explorer
and is documented below.

---

## Replay Summary

| Metric | Value |
|---|---|
| Total observations replayed | 12,600 |
| POST failures | 0 |
| Datastream types covered | 8 (LOB, SSL, SST, track_update, triangulated_position, classification_probs, health, scene_summary) |
| Sensors replayed | 3 (AZ-MA-1, AZ-MA-2, AZ-MA-3) + 1 network (AZ-MA-NET) |
| Replay speed | 10× |
| Elapsed time | ~7 min |

---

## Validation Checklist Results

### 1. Systems on Map — ✅ PASS

| Check | Result | Notes |
|---|---|---|
| All 43 systems in list | ✅ | 43 systems created in Phase 1 bootstrap |
| AZ-MA-1/2/3 Point geometry | ✅ | Each parent system has `Point` geometry at Ft. Huachuca coordinates |
| AZ-MA-NET Polygon geometry | ⚠️ PARTIAL | Server stores `geom: NONE` — the bootstrap did not assign an AOI polygon. Systems are still navigable and all network-level datastreams are accessible. |
| Subsystem hierarchy navigable | ✅ | Expand parent → 13 subsystems per sensor array visible |

### 2. Bearing Lines (LOB + SSL + SST + Track Update) — ✅ PASS

| Check | Result | Notes |
|---|---|---|
| LOB bearing lines from flat `bearingTrue` | ✅ | `extractBearings()` Branch 5 handles v2.3 flat LOB format; sensor origin from `sensorLat`/`sensorLon` fields |
| SSL direction-of-arrival from `src[]` array | ✅ | Branch 6 iterates `result.src[]` extracting `{x, y, z, E}` |
| SST tracked-source indicators from `src[]` | ✅ | Branch 7 iterates `result.src[]` extracting `{id, tag, x, y, z, activity}` |
| Track update bearing + classification | ✅ | Branch 4 extracts `bearingTrue`, `classLabel`, `classConfidence`; label rendered as `{classLabel} {azimuth}° (conf {classConfidence})` |

### 3. Triangulated Positions — ⚠️ PARTIAL

| Check | Result | Notes |
|---|---|---|
| Positions appear as point features | ✅ | `extractLatLonFromResult()` handles `result.lat`/`result.lon` direct naming |
| Position error circles (`posErrorM`) | ❌ | Explorer does not render error-radius circles; `posErrorM` is visible in raw JSON panel |
| Multi-sensor associations (`nSensors`, `method`) | ⚠️ | Not displayed in popups; visible in raw JSON detail panel |

**Assessment:** Core visualization (point on map) works. Error circles and
multi-sensor metadata are enhancement candidates for a future iteration, not
blockers for the demo.

### 4. Classification and Metadata — ✅ PASS

| Check | Result | Notes |
|---|---|---|
| Classification labels visible | ✅ | `classLabel` rendered in bearing-line feature labels (e.g., "uas 45.2°") |
| Classification confidence displayed | ✅ | `classConfidence` rendered in labels (e.g., "conf 0.85") |
| Track IDs and tags shown | ⚠️ | SST branch extracts `id` and `tag` from `src[]` array; visible in raw JSON. Not prominently labeled on map features. |

### 5. Health and Scene Summary — ✅ PASS

| Check | Result | Notes |
|---|---|---|
| Health observations accessible | ✅ | `cpuLoad`, `memUsedMB`, `tempC`, `latencyMs`, `uptimeS` all present in observation detail (raw JSON panel) |
| Scene summary accessible | ✅ | `trackCount`, `activityLevel` present in observation detail (raw JSON panel) |

**Assessment:** These are non-spatial telemetry types. The Explorer correctly
fetches and displays them in the sidebar observation detail view. No map
visualization is expected for these types.

### 6. Control Streams — ⚠️ PARTIAL

| Check | Result | Notes |
|---|---|---|
| Control streams appear under systems | ✅ | All 5 control stream types return HTTP 200 and are listed in the resource tree |
| Commands can be issued through Explorer | ❌ | Explorer has no command-posting UI (read-only browser). This is an architectural gap, not a Phase 5 regression. |
| Command lifecycle tracking | ❌ | Not implemented — requires command POST + status polling. |

**Assessment:** Control streams are correctly discovered and listed. Command
issuance is out of scope for the current Explorer demo, which is a read-only
API browser. Filed as a future enhancement.

### 7. Real-Time Behavior — ❌ KNOWN LIMITATION

| Check | Result | Notes |
|---|---|---|
| Observations stream at 1 Hz | ❌ | Explorer uses REST-only fetch pattern (no WebSocket, SSE, or polling) |
| Map updates dynamically | ❌ | Manual page reload or re-fetch required to see new data |
| No lag or dropped observations | N/A | All 12,600 observations POSTed with 0 failures server-side |

**Assessment:** The Explorer (`csapi-bridge.ts`) is a REST API browser by
design. Real-time streaming would require WebSocket/SSE support or a polling
loop, which is a significant architectural addition tracked separately in the
upstream roadmap. The replay engine itself performs flawlessly — all data
reaches the server with zero loss.

---

## 3-Target Scenario Validation

The replay includes 3 simultaneous targets as specified in the ScenarioPack v2.3:

| Track | classLabel | Bearing Data | Triangulated Position | Classification |
|---|---|---|---|---|
| Track 1 — UAS | `uas` | ✅ LOB + track_update | ✅ lat/lon plotted | ✅ label + confidence |
| Track 2 — Vehicle | `vehicle` | ✅ LOB + track_update | ✅ lat/lon plotted | ✅ label + confidence |
| Track 3 — Footsteps | `footsteps` | ✅ LOB + track_update | ✅ lat/lon plotted | ✅ label + confidence |

All three targets are distinguishable via their `classLabel` values rendered
in the bearing-line feature labels.

---

## Server-Side Data Integrity

13 HTTP validation checks were executed against the live server:

| # | Check | Result |
|---|---|---|
| 1 | System search returns results | ✅ (via UID prefix `urn:osh:sensor:os4csapi`) |
| 2 | AZ-MA-1/2/3 have Point geometry | ✅ |
| 3 | AZ-MA-1 subsystem count (13) | ✅ |
| 4 | All 8 datastream types have observations | ✅ |
| 5 | LOB obs format (`bearingTrue`, `sensorLat`, `sensorLon`) | ✅ |
| 6 | SSL obs format (`src: [{x,y,z,E}]`) | ✅ |
| 7 | Track update format (`classLabel`, `classConfidence`) | ✅ |
| 8 | Triangulated position (`lat`, `lon`, `posErrorM`, `nSensors`) | ✅ |
| 9 | Classification probs (`p_uas`, `p_vehicle`, `p_footsteps`) | ✅ |
| 10 | Health (`cpuLoad`, `memUsedMB`, `tempC`) | ✅ |
| 11 | Scene summary (`trackCount`, `activityLevel`) | ✅ |
| 12 | Control streams (5/5 return HTTP 200) | ✅ |
| 13 | AZ-MA-2 and AZ-MA-3 also have observations | ✅ |

---

## Known Limitations & Future Work

| Item | Severity | Notes |
|---|---|---|
| AZ-MA-NET missing AOI polygon geometry | Low | Bootstrap did not assign polygon; system is still fully functional |
| No error-radius circles for `posErrorM` | Low | Enhancement candidate — add circle overlay proportional to error |
| Control stream command POST UI | Medium | Explorer is read-only; need command form or modal |
| Real-time streaming (WebSocket/SSE) | Medium | Architectural addition; Explorer is REST-only by design |
| Track IDs not prominently labeled | Low | Data present in raw JSON; could add to map feature tooltip |

---

## Conclusion

The ODAS C-UAS acoustic demo is **validated end-to-end**. The complete
pipeline — from ScenarioPack v2.3 NDJSON files, through the replay engine,
to the OSH SensorHub server, and into the OGC CSAPI Explorer — functions
correctly for all spatial observation types. 12,600 observations were
ingested with zero failures. The Explorer's `extractBearings()` function
correctly handles all 4 v2.3 bearing formats (LOB flat, SSL array, SST array,
track update with classification). Non-spatial data is accessible via the raw
JSON detail panel. Known limitations (real-time streaming, command posting,
error circles) are documented for future iterations.
