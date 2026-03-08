# ISS Bootstrap Implementation Report

**Date:** 2026-03-08  
**Status:** Complete — live and verified  
**Commit:** `a3b0644`  
**Repository:** `OS4CSAPI/ogc-csapi-explorer`

---

## 1. Overview

The ISS (International Space Station) dual-product bootstrap creates all server-side resources needed for real-time ISS position tracking and orbit prediction on the live CSAPI server. This replaces the earlier single-system ISS model with a richer, two-system architecture that publishes both instantaneous position fixes and full orbit ground tracks.

### Products

| Product | System | DataStream | Cadence |
|---------|--------|------------|---------|
| ISS Position (SGP4) | `urn:os4csapi:system:iss-position-publisher:v2` | 11-field observation (lat, lon, alt, velocity, heading, etc.) | 30 seconds |
| ISS Orbit Ground Track | `urn:os4csapi:system:iss-orbit-track-publisher:v2` | 7-field observation with 100-point trackPointsJson | 5 minutes |

---

## 2. Resources Created

All resources were created on the live server at `https://os4csapi-osh.duckdns.org/sensorhub/api`.

### 2.1 Procedures

| Resource | Server ID | UID | Notes |
|----------|-----------|-----|-------|
| SGP4 Propagation | `045g` | `urn:os4csapi:procedure:sgp4-propagation:v1` | Pre-existing — shared with new systems |
| Orbit Track Procedure | `0470` | `urn:os4csapi:procedure:orbit-ground-track:v1` | Created by bootstrap |

### 2.2 Systems (with SensorML Metadata)

| Resource | Server ID | UID |
|----------|-----------|-----|
| ISS Position Publisher | `04og` | `urn:os4csapi:system:iss-position-publisher:v2` |
| ISS Orbit Track Publisher | `04p0` | `urn:os4csapi:system:iss-orbit-track-publisher:v2` |

Both systems received full SensorML 3.0 rich metadata via a two-step process:
1. **POST** a minimal GeoJSON Feature stub to `/systems` (creates the resource)
2. **PUT** the full SensorML body with `Content-Type: application/sml+json` (applies metadata)

Verified metadata includes: keywords, identifiers (NORAD 25544, COSPAR 1998-067A), classifiers, capabilities (position accuracy, orbit accuracy, track resolution), contacts (NASA, Roscosmos), and reference documents.

### 2.3 DataStreams

| Resource | Server ID | Parent System | Output Name |
|----------|-----------|---------------|-------------|
| Position DS | `04gg` | `04og` | `iss_position_sgp4_v2` |
| Orbit Track DS | `04h0` | `04p0` | `iss_orbit_ground_track` |

### 2.4 Deployment Tree

| Resource | Server ID | UID | Parent |
|----------|-----------|-----|--------|
| Orbital Tracking Demo | `048g` | `urn:os4csapi:deployment:orbital-tracking:demo` | Root (pre-existing) |
| LEO Objects | `04a0` | `urn:os4csapi:deployment:orbital-tracking:leo-objects` | 048g |
| ISS Tracking | `04ag` | `urn:os4csapi:deployment:orbital-tracking:iss` | 04a0 |
| Position Feed | `04b0` | `urn:os4csapi:deployment:orbital-tracking:iss:position-feed` | 04ag |
| Orbit Feed | `04bg` | `urn:os4csapi:deployment:orbital-tracking:iss:orbit-feed` | 04ag |

Position Feed and Orbit Feed deployments include `platform@link` references to their respective systems, resolved at bootstrap time.

---

## 3. Architecture

### 3.1 Script: `scripts/bootstrap_iss.py`

- **Lines:** 1,119
- **Dependencies:** Python stdlib only (urllib, json, base64, ssl)
- **4-phase execution:**
  1. **Procedures** — POST GeoJSON Features to `/procedures`
  2. **Systems** — POST GeoJSON stub → PUT SensorML body
  3. **DataStreams** — POST JSON to `/systems/{id}/datastreams`
  4. **Deployments** — Recursive POST to `/deployments` and `/deployments/{id}/subdeployments`
- **CLI flags:** `--clean` (delete + recreate), `--clean-only` (teardown only), `--dry-run`
- **Features:** UID cache for deduplication, skip-if-exists behavior, retry logic, `find_by_uid()` for system ID resolution

### 3.2 Publisher: `scripts/iss_publisher_v3.py`

- **Deployed to:** Oracle VM (`129.80.248.53`) as `iss-publisher.service` (systemd)
- **Runtime:** Python venv at `/home/ubuntu/iss-publisher-venv/`
- **Dual-product:** Position observations every 30s, orbit track every 5 min
- **TLE source:** CelesTrak API (auto-refreshes)
- **Env vars:** `POS_SYSTEM_UID`, `POS_DS_NAME`, `TRACK_SYSTEM_UID`, `TRACK_DS_NAME`, `NORAD_ID`

---

## 4. Issues Encountered & Resolved

### 4.1 DataStream Time Field Compatibility (Critical)

**Symptom:** Publisher returned HTTP 400: `Expected field 'lat_deg' but was 'timestamp'`

**Root cause:** The datastream schema used the OGC standard `SamplingTime` definition:
```json
{
  "definition": "http://www.opengis.net/def/property/OGC/0/SamplingTime",
  "uom": { "href": "http://www.opengis.net/def/uom/ISO-8601/0/Gregorian" }
}
```

OpenSensorHub auto-extracts this timestamp from `phenomenonTime` and does **not** expect it as a field in the result body. When the publisher sent a `timestamp` field, the server rejected it because it expected the next data field (`lat_deg`).

**Fix:** Changed both datastream schemas to use the SensorML.com definition with epoch seconds:
```json
{
  "definition": "http://sensorml.com/ont/swe/property/SamplingTime",
  "referenceTime": "1970-01-01T00:00:00Z",
  "uom": { "code": "s" }
}
```

This is treated as a regular result field by the server, matching the pattern used by the working localizer and old ISS datastreams.

**Lesson:** When creating datastreams for OSH, always use `sensorml.com/ont/swe/property/SamplingTime` with epoch seconds, not the OGC `SamplingTime` with ISO-8601 UOM.

### 4.2 Systemd Environment Variable Quoting

**Symptom:** Publisher found `POS_DS_NAME=ISS` instead of `ISS Position (SGP4)` — values with spaces were truncated.

**Root cause:** Systemd's `Environment=` directive splits unquoted values on whitespace.

**Fix:** Wrap the entire key=value pair in double quotes:
```ini
Environment="POS_DS_NAME=ISS Position (SGP4)"
```

---

## 5. Verification

### 5.1 API Verification

**Position observations** (`GET /datastreams/04gg/observations?limit=1`):
- Full 11-field observation returned: timestamp, lat_deg, lon_deg, alt_km, speed_km_s, heading_deg, inclination_deg, orbital_period_min, revolutions, visibility, norad_id

**Orbit track observations** (`GET /datastreams/04h0/observations?limit=1`):
- 7-field observation with `trackPointsJson` containing 100 coordinate points `[lon, lat, alt]`

### 5.2 SensorML Metadata Verification

**System metadata** (`GET /systems/04og?f=sml3`):
- Keywords present: ISS, International Space Station, SGP4, orbital tracking, etc.
- Identifiers: NORAD Catalog Number (25544), COSPAR ID (1998-067A)
- Classifiers: Intended Application (Space Tracking), Sensor Type (Satellite Tracker)
- Capabilities: Position Accuracy (±10 km), Orbit Accuracy (±50 km), Track Resolution (100 points)
- Contacts: NASA, Roscosmos
- Documents: ISS Wikipedia, CelesTrak TLE source, SGP4 reference

### 5.3 Publisher Health

Both products confirmed flowing with `Inserted observation` log entries for position (30s cadence) and orbit track (5min cadence). Publisher service running continuously on Oracle VM.

---

## 6. Old ISS Resources (Pending Retirement)

The following old single-system ISS resources are still on the server but no longer receiving observations:

| Resource | Server ID | Status |
|----------|-----------|--------|
| Old ISS System | `04ng` | Inactive — superseded by `04og` + `04p0` |
| Old ISS DataStream | `04fg` | Inactive — superseded by `04gg` + `04h0` |
| Old ISS Deployment | `0490` | Inactive — superseded by new hierarchy |
| SGP4 Procedure | `045g` | **Shared** — still in use by new systems |
| Orbital Tracking Root | `048g` | **Shared** — new hierarchy attached under it |

Retirement should occur after confirming the webapp displays new resources correctly.

---

## 7. Bootstrap Patterns (Reference)

For future enrichment packs (UAS, localizer, SENREP), the confirmed working patterns are:

| Resource Type | Method | Content-Type | Endpoint |
|---------------|--------|-------------|----------|
| Procedure | POST | `application/geo+json` | `/procedures` |
| System (stub) | POST | `application/geo+json` | `/systems` |
| System (metadata) | PUT | `application/sml+json` | `/systems/{id}` |
| DataStream | POST | `application/json` | `/systems/{id}/datastreams` |
| Deployment (root) | POST | `application/geo+json` | `/deployments` |
| Deployment (sub) | POST | `application/geo+json` | `/deployments/{id}/subdeployments` |

The `platform@link` field in deployment templates is resolved at runtime by looking up the system's server ID via `find_by_uid("systems", uid)`.
