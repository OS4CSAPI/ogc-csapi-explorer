# Known Server Quirks, Bugs, and Limitations — Test Server Reference

**Purpose:** Comprehensive reference of all known behaviors, bugs, limitations, and content-negotiation quirks for the two CSAPI test servers. This document exists so that smoke test prompts can include it by reference, preventing the AI from re-discovering (or worse, forgetting) known issues.

**Version:** 1.0
**Date:** 2026-02-18
**Source:** Smoke Tests #1–#18 (Phase 2.1–3.16), Demo App CRUD Testing (Issues #5–#26), Cross-Server Interoperability Analysis, F57 Content-Negotiation Correction

---

## Server 1: OpenSensorHub (OSH)

### Connection

| Property                | Value                                                                   |
| ----------------------- | ----------------------------------------------------------------------- |
| **Base URL**            | `http://45.55.99.236:8080/sensorhub/api`                                |
| **Auth**                | Basic Auth — credentials provided per-session, **NEVER stored in repo** |
| **SSL**                 | None (plain HTTP)                                                       |
| **API Title**           | "Connected Systems API Service"                                         |
| **Conformance Classes** | 20+ CSAPI conformance classes advertised                                |

### PowerShell Pattern

```powershell
$cred = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("USERNAME:PASSWORD"))
$headers = @{ Authorization = "Basic $cred" }
Invoke-RestMethod -Uri "http://45.55.99.236:8080/sensorhub/api" -Headers $headers
```

⚠️ **You MUST ask the user for credentials if you don't have them from earlier in the conversation. Do not guess.**

---

### Resource Inventory (as of Smoke Test #18)

| Endpoint            | Count | Notes                                                                                          |
| ------------------- | ----: | ---------------------------------------------------------------------------------------------- |
| `/systems`          |    33 | 12 `sosa/Sensor` + 21 `sosa/Platform`. Originally 12; grew from CSAPI Explorer smoke test data |
| `/deployments`      |    16 | 15× `sosa/Deployment`, 1× `ssn/Deployment` (F83). Originally 0; all smoke test data            |
| `/procedures`       |    15 | 15× `sosa/Procedure`. Originally 0; all smoke test data                                        |
| `/samplingFeatures` |    66 | 51× `sensorml/2.0#Feature` + 15× `sosa/Sample`.                                                |
| `/properties`       |     0 | Always empty                                                                                   |
| `/datastreams`      |   100 | Stable. Part 2 resource — `application/json` envelope                                          |
| `/observations`     |   100 | Stable. Part 2 resource                                                                        |
| `/controlstreams`   |     8 | Stable. **Lowercase path required** — `/controlStreams` returns 400                            |
| `/commands`         |     — | **No top-level endpoint** (F34). Only via `/controlstreams/{id}/commands`                      |

### Known Resource IDs

| Type            | ID             | Name/UID                                                   |
| --------------- | -------------- | ---------------------------------------------------------- |
| System          | `03bc5ofvvstg` | "LIVE - Field Drone" (`urn:osh:driver:mavsdk:cube:replay`) |
| SamplingFeature | `040g`         | `urn:android:foi:Run-20260211-041356`                      |
| Datastream      | `03tbj7mvqg50` | Temperature                                                |
| Datastream      | `02au905kq85g` | StatusEvent                                                |
| Datastream      | `021qpiurq85g` | gps_data                                                   |
| Datastream      | `02vp7efvjs70` | Acceleration                                               |
| Datastream      | `02v937ubpscg` | Location                                                   |
| ControlStream   | `0o10`         | Location Control                                           |
| ControlStream   | `0o4g`         | Enable Location                                            |
| ControlStream   | `0o40`         | Flight mode                                                |
| ControlStream   | `0o20`         | Landing                                                    |
| ControlStream   | `0o2g`         | Mission                                                    |
| ControlStream   | `0o3g`         | System Shell                                               |
| ControlStream   | `0o1g`         | Takeoff                                                    |
| ControlStream   | `0o30`         | Offboard                                                   |

---

### Content Negotiation — OSH IGNORES ALL Accept HEADERS

**This is the single most important OSH quirk.** OSH ignores the `Accept` header entirely (F46/F64). It always returns `Content-Type: application/json` regardless of what you ask for.

**Use the `?f=` query parameter instead:**

| Parameter    | Status | Content-Type Returned  | Notes                                                  |
| ------------ | ------ | ---------------------- | ------------------------------------------------------ |
| _(none)_     | 200    | `application/json`     | Default — GeoJSON-like structure in `{items}` envelope |
| `?f=json`    | 200    | `application/json`     | Same as default                                        |
| `?f=geojson` | 200    | `application/geo+json` | Standard GeoJSON `FeatureCollection` envelope          |
| `?f=sml3`    | 200    | `application/sml+json` | **Only way to get SensorML data from OSH** (F71)       |
| `?f=swe`     | 400    | —                      | Bad Request                                            |

### Response Envelope Format

| Request                | Envelope                                         | Items Key  | Links Key                  |
| ---------------------- | ------------------------------------------------ | ---------- | -------------------------- |
| Default JSON           | `{ items: [...] }`                               | `items`    | **Missing entirely** (F82) |
| `?f=geojson`           | `{ type: "FeatureCollection", features: [...] }` | `features` | Present                    |
| `?f=sml3` (collection) | `{ items: [...] }`                               | `items`    | Missing                    |
| `?f=sml3` (individual) | Unwrapped SML object                             | N/A        | N/A                        |

- **No `numberMatched`, `numberReturned`, or `timeStamp`** in any response (F5)
- Pagination uses `links[rel=next]` with offset parameter
- Features have **empty** `links: []` arrays (F48)

### featureType Vocabulary

OSH uses **full URIs only** (never CURIEs):

| Endpoint          | featureType                                   |                   Count |
| ----------------- | --------------------------------------------- | ----------------------: |
| /systems          | `http://www.w3.org/ns/sosa/Sensor`            |                      12 |
| /systems          | `http://www.w3.org/ns/sosa/Platform`          |                      21 |
| /deployments      | `http://www.w3.org/ns/sosa/Deployment`        |                      15 |
| /deployments      | `http://www.w3.org/ns/ssn/Deployment`         | 1 (F83 — SSN namespace) |
| /procedures       | `http://www.w3.org/ns/sosa/Procedure`         |                      15 |
| /samplingFeatures | `http://www.opengis.net/sensorml/2.0#Feature` |                      51 |
| /samplingFeatures | `http://www.w3.org/ns/sosa/Sample`            |                      15 |

### validTime Behavior

- Format: `["2026-01-26T18:32:01.56Z", "now"]` — ISO 8601 start + `"now"` sentinel
- Some SamplingFeatures: `validTime: null`
- Deployments: **validTime absent entirely** (F85 — contradicts Table 10)

### Part 2 Endpoint Status

| Endpoint                         | Status             | Notes                                                     |
| -------------------------------- | ------------------ | --------------------------------------------------------- |
| `/datastreams`                   | ✅ Works           | 100 items                                                 |
| `/datastreams/{id}/schema`       | ✅ Works           | Returns SWE Common DataRecord. Content-Type: `auto` (F56) |
| `/datastreams/{id}/observations` | ✅ Works           |                                                           |
| `/observations`                  | ✅ Works           | 100 items                                                 |
| `/controlstreams`                | ✅ Works           | 8 items. **Lowercase path only**                          |
| `/controlstreams/{id}/schema`    | ✅ Works           | Returns SWE Common DataRecord                             |
| `/controlstreams/{id}/commands`  | ✅ Works           |                                                           |
| `/commands` (top-level)          | ❌ Not implemented | F34                                                       |
| `/commands/{id}/cancel`          | ❌ Not implemented | F35                                                       |
| `/commands/{id}/result`          | ❌ 404             | Expected for fire-and-forget commands (F37)               |

### Sub-Resource/Relationship Endpoints — ALL RETURN 400

**Every sub-resource relationship endpoint returns 400 on OSH:**

| Endpoint                            | Finding |
| ----------------------------------- | ------- |
| `systems/{id}/deployments`          | F6      |
| `systems/{id}/procedures`           | F7      |
| `samplingFeatures/{id}/systems`     | F8      |
| `samplingFeatures/{id}/history`     | F9      |
| `datastreams/{id}/systems`          | F16     |
| `datastreams/{id}/procedures`       | F17     |
| `datastreams/{id}/history`          | F18     |
| `observations/{id}/datastream`      | F21     |
| `observations/{id}/samplingFeature` | F22     |
| `observations/{id}/system`          | F23     |
| `observations/{id}/history`         | F24     |
| `controlstreams/{id}/feasibility`   | F28     |

**Subsystem and subdeployment endpoints DO work** (tested via demo app CRUD):
| Endpoint | Status |
|----------|--------|
| `systems/{id}/subsystems` | ✅ Works (GET and POST) |
| `deployments/{id}/subdeployments` | ✅ Works (GET and POST) |

### Write Operations

| Operation                               | Status                                                    | Notes                                                                                                                                          |
| --------------------------------------- | --------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| **POST** (create)                       | ✅ Works                                                  | Returns `201 Created` with **empty body** + `Location` header. Parse `Location` to get new ID                                                  |
| **PUT** (update)                        | ✅ Works                                                  | **Requires `uid` in payload body** even though resource is addressed by ID in URL. Returns 400 "Missing feature UID" without it (F16/issue-19) |
| **DELETE**                              | ✅ Works                                                  |                                                                                                                                                |
| **Content-Type for Part 1 POST/PUT**    | Must be `application/geo+json`                            | OSH rejects `application/json` for Part 1 resources                                                                                            |
| **Content-Type for Part 2 POST/PUT**    | Must be `application/json`                                |                                                                                                                                                |
| **Accept header on POST**               | ⚠️ **Do NOT send `Accept: application/geo+json` on POST** | Causes network-level failures (S-8 from demo testing)                                                                                          |
| **Top-level POST for nested resources** | ❌ 405                                                    | `POST /datastreams` returns 405. Must use `POST /systems/{id}/datastreams` (issue-5 F-1)                                                       |

### SWE Common Schema Details

**Datastream Schemas:**

| DS ID          | Name         | Fields                                             |
| -------------- | ------------ | -------------------------------------------------- |
| `03tbj7mvqg50` | Temperature  | 1× Quantity (uom.href)                             |
| `02au905kq85g` | StatusEvent  | 2× Text                                            |
| `021qpiurq85g` | gps_data     | 1× Vector (3× Quantity w/ axisID)                  |
| `02vp7efvjs70` | Acceleration | 1× Vector (3× Quantity)                            |
| `02v937ubpscg` | Location     | 1× Vector (3× Quantity, referenceFrame: EPSG:4979) |

**Control Stream Schemas:**

| CS ID  | Name             | Fields                   |
| ------ | ---------------- | ------------------------ |
| `0o10` | Location Control | Vector + Boolean + Count |
| `0o4g` | Enable Location  | 1× Boolean               |
| `0o40` | Flight mode      | 1× Quantity              |
| `0o20` | Landing          | 1× Boolean               |
| `0o2g` | Mission          | Count + Boolean          |
| `0o3g` | System Shell     | 1× Text                  |
| `0o1g` | Takeoff          | 1× Quantity              |
| `0o30` | Offboard         | Vector + Quantity        |

**Schema quirks:**

- `uom` appears in both `{href: ...}` and `{code: ...}` forms
- Vector includes `referenceFrame` and `coordinates` array with `axisID`
- Schema endpoint returns `Content-Type: auto` (not a valid media type — F56)
- Observations use implicit JSONEncoding (no explicit `encoding` field — F81)
- Observation `result` is flat JSON keyed by field names

### SensorML Behavior

- Access via `?f=sml3` only (Accept headers ignored)
- All systems: `type: "PhysicalSystem"`, `definition: "http://www.w3.org/ns/sosa/Sensor"` (full URI)
- Minimal structure: `{type, id, uniqueId, definition, label, validTime}` — no identifiers, classifiers, components, or position
- Successfully parsed by `parsePhysicalSystem` (F68)

---

## Server 2: 52North (52N)

### Connection

| Property                | Value                                                                                            |
| ----------------------- | ------------------------------------------------------------------------------------------------ |
| **Base URL**            | `https://csa.demo.52north.org/`                                                                  |
| **Auth**                | None required                                                                                    |
| **SSL**                 | **Expired certificate** — ALL commands must use `-SkipCertificateCheck` or equivalent TLS bypass |
| **API Title**           | "connected-systems-pygeoapi"                                                                     |
| **Conformance Classes** | **Zero** CSAPI conformance classes advertised (F3)                                               |

### PowerShell Pattern

```powershell
Invoke-RestMethod -Uri "https://csa.demo.52north.org/" -SkipCertificateCheck
# For specific Accept header:
Invoke-RestMethod -Uri "https://csa.demo.52north.org/systems" -SkipCertificateCheck -Headers @{ Accept = "application/geo+json" }
```

---

### Resource Inventory (as of Smoke Test #18)

| Endpoint            |          Count | Notes                                                             |
| ------------------- | -------------: | ----------------------------------------------------------------- |
| `/systems`          |              3 | Doppler Current Profiler, EXO3 Sonde, SMARTGUARD Platform         |
| `/deployments`      |              1 | "Messtonne 1 - 2025 Test" with geometry Point(12.08, 54.13)       |
| `/procedures`       |              1 | "Doppler Current Profiler Sensor" — **misclassified** (see below) |
| `/samplingFeatures` |              0 | Empty for geo+json/json; **400** for sml+json (F86)               |
| `/properties`       |              0 | Empty via sml+json                                                |
| `/datastreams`      | ❌ **500/400** | Completely broken — F20/F76/F87                                   |
| `/observations`     |     ❌ **400** | Broken — F26                                                      |
| `/controlstreams`   |     ❌ **404** | Not implemented — F32                                             |
| `/commands`         |     ❌ **404** | Not implemented                                                   |

### Known Resource IDs

| Type       | ID               | Name/UID                                                                 |
| ---------- | ---------------- | ------------------------------------------------------------------------ |
| System     | `5400-526`       | Doppler Current Profiler (`urn:sensor:5400-526`)                         |
| System     | `YSI599503-00-1` | EXO3 Sonde (`urn:sensor:YSI599503-00-1`)                                 |
| System     | `5300-909`       | SMARTGUARD Platform (`urn:platform:5300-909`)                            |
| Deployment | `af41f84f-...`   | "Messtonne 1 - 2025 Test" (`urn:messtonne:1:2025-demo`)                  |
| Procedure  | `4e09de42-...`   | "Doppler Current Profiler Sensor" (`urn:sensortype:aanderaa:dcps:td304`) |

---

### Content Negotiation — DUAL-BACKEND ARCHITECTURE

**This is the single most important 52N quirk.** The `Accept` header routes the request to different data providers with different data:

| Accept Header          | Provider                  | Content-Type           | Has Data?                                      | Envelope                                                    |
| ---------------------- | ------------------------- | ---------------------- | ---------------------------------------------- | ----------------------------------------------------------- |
| `application/sml+json` | SensorML store            | `application/sml+json` | **Yes** (3 systems, 1 deployment, 1 procedure) | `{ items: [...], links: [] }`                               |
| `application/geo+json` | pygeoapi GeoJSON          | `application/geo+json` | **Yes** (same data)                            | `{ type: "FeatureCollection", features: [...], links: [] }` |
| `application/json`     | pygeoapi JSON             | `application/json`     | **Empty** (0 features)                         | `{ type: "FeatureCollection", features: [], links: [] }`    |
| _(no header)_          | SensorML (server default) | `application/sml+json` | **Yes**                                        | `{ items: [...], links: [] }`                               |

**⚠️ `Accept: application/json` returns EMPTY collections.** This was the root cause of the F57 incident — we changed Accept headers between smoke tests and incorrectly concluded data had been removed. The 52N implementer confirmed this behavior in [OS4CSAPI Discussion #2](https://github.com/orgs/OS4CSAPI/discussions/2).

**Rule: Always use `Accept: application/geo+json` or `Accept: application/sml+json` when testing 52N. Never use `Accept: application/json`.**

### featureType Vocabulary

52N **mixes CURIE and full URI forms** (F44). Additionally, systems have **null featureType** in GeoJSON:

| Endpoint     | GeoJSON featureType                    | SML definition                                    | Issue                                                            |
| ------------ | -------------------------------------- | ------------------------------------------------- | ---------------------------------------------------------------- |
| /systems     | **`null`** (F41)                       | `sosa:Sensor` (2×), `sosa:Platform` (1×) — CURIEs | Requires `classifyFeature` hint fallback                         |
| /deployments | `http://www.w3.org/ns/sosa/Deployment` | `http://www.w3.org/ns/sosa/Deployment` — full URI | Consistent                                                       |
| /procedures  | `sosa:Sensor` (F43/F84)                | `sosa:Sensor` — CURIE                             | **Misclassified as System** because `Sensor` maps to System type |

**F84 (Procedure misclassification):** Filed as [Issue #16 on 52North/connected-systems-pygeoapi](https://github.com/52North/connected-systems-pygeoapi/issues/16). This is an upstream server bug — the procedure's `featureType` should be `sosa:Procedure`, not `sosa:Sensor`.

### validTime Behavior

- All systems: `validTime: null` in both GeoJSON and SML
- Deployment: `validTime: null` (F42)
- Procedure: validTime present in SML only

### Part 2 Endpoint Status — ALL BROKEN

| Endpoint             | Status                                   | Notes                         |
| -------------------- | ---------------------------------------- | ----------------------------- |
| `/datastreams`       | ❌ 500 (json) / 400 (geo+json, sml+json) | F20/F76/F87                   |
| `/observations`      | ❌ 400                                   | F26. Was 500 in earlier tests |
| `/controlstreams`    | ❌ 404 Not Found                         | F32. Not implemented          |
| `/commands`          | ❌ 404 Not Found                         | Not implemented               |
| All schema endpoints | ❌ Not accessible                        | Datastreams broken            |

**52N cannot be used for Part 2 testing.** All Part 2 workflows must target OSH.

### Write Operations

**Not extensively tested against 52N.** Deployment data appears pre-loaded. For CRUD smoke testing, use OSH.

### SensorML Behavior

- Access via `Accept: application/sml+json` (or no Accept header — server default)
- Systems: `type: "PhysicalSystem"`, CURIEs for definition (`sosa:Sensor`, `sosa:Platform`)
- **Rich data:** identifiers, classifiers, documents, typeOf links, procedureType
- Deployment: `type: "Deployment"` — **non-standard** SML type, not a SensorML process type (F65). All four SML parsers reject it correctly
- System 5400-526 typeOf link includes non-standard `urn` property: `{href, rel, urn}` — `parseLink` strips it correctly (F70)
- `@link` notation present in GeoJSON: `platform@link`, `deployedSystems@link` (F47)

### 52N-Specific Bugs

| Finding | Description                                                                    |
| ------- | ------------------------------------------------------------------------------ |
| F41     | Systems GeoJSON: `featureType: null` for all 3 systems                         |
| F42     | Deployment `validTime: null` in GeoJSON                                        |
| F43/F84 | Procedure `featureType: sosa:Sensor` — misclassified as System. Filed upstream |
| F44     | Mixes CURIE and full URI forms for the same vocabulary                         |
| F47     | `@link` notation in GeoJSON (`platform@link`, `deployedSystems@link`)          |
| F50     | Server default is `application/sml+json`, not `application/json`               |
| F52     | Root response `Content-Type: None`                                             |
| F63     | Error codes changed over time (500→400 on some endpoints)                      |
| F65     | SML uses non-standard `type: "Deployment"`                                     |
| F72     | Individual system GET with `Accept: application/json` → 500                    |
| F86     | `/samplingFeatures` with sml+json regressed (200→400)                          |

---

## Cross-Server Comparison

| Dimension                       | OSH                                                 | 52N                                            |
| ------------------------------- | --------------------------------------------------- | ---------------------------------------------- |
| **Content negotiation**         | Ignores Accept; use `?f=`                           | Accept routes to different backends            |
| **Default content type**        | `application/json`                                  | `application/sml+json`                         |
| **Response envelope (default)** | `{items}` (no links key)                            | `{FeatureCollection, features}` or `{items}`   |
| **featureType vocabulary**      | Full URIs always                                    | Mixed: null / CURIEs / full URIs               |
| **validTime**                   | Array `["ISO", "now"]`                              | Mostly null                                    |
| **SML data access**             | `?f=sml3` only                                      | `Accept: application/sml+json`                 |
| **SML richness**                | Minimal                                             | Rich                                           |
| **Part 2 endpoints**            | ✅ All work                                         | ❌ All broken                                  |
| **Sub-resource endpoints**      | ❌ Most return 400 (subsystems/subdeployments work) | Not tested                                     |
| **Write ops**                   | ✅ Full CRUD                                        | Not tested                                     |
| **Conformance classes**         | 20+                                                 | 0                                              |
| **Auth**                        | Basic Auth (ask user)                               | None                                           |
| **SSL**                         | HTTP                                                | HTTPS (expired cert → `-SkipCertificateCheck`) |

---

## Operational Rules Derived from Server Quirks

1. **Always document which `Accept` header you used** for every request. If you change it between smoke tests, note why.
2. **Never conclude "data is gone"** without testing all three Accept variants: none, `application/json`, `application/geo+json`, `application/sml+json`.
3. **OSH: Use `?f=` for content negotiation.** Accept headers are ignored.
4. **52N: Never use `Accept: application/json`.** It returns empty collections.
5. **POST to OSH: Do not include `Accept: application/geo+json`.** It causes network-level failures.
6. **POST to OSH: Include `uid` in PUT payloads.** The library's type interfaces already require it.
7. **POST nested resources to OSH:** Use `POST /systems/{id}/datastreams`, not `POST /datastreams`.
8. **52N: Part 2 is completely broken.** All Part 2 testing must use OSH.
9. **OSH: Sub-resource relationship endpoints return 400** (but subsystems/subdeployments work).
10. **OSH: Use lowercase `/controlstreams`** — camelCase `/controlStreams` returns 400.
