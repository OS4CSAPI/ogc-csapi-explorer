# Known Server Quirks, Bugs, and Limitations — Test Server Reference

**Purpose:** Comprehensive reference of all known behaviors, bugs, limitations, and content-negotiation quirks for all CSAPI test servers. This document exists so that smoke test prompts can include it by reference, preventing the AI from re-discovering (or worse, forgetting) known issues.

**Version:** 2.0
**Date:** 2026-05-11
**Source:** Smoke Tests #1–#18 (Phase 2.1–3.16), Demo App CRUD Testing (Issues #5–#26), Cross-Server Interoperability Analysis, F57 Content-Negotiation Correction, Phase 9 NIMS/ISS/CO-OPS Map Integration Debugging (2026-05-10)

> **⚠️ Server migration note:** The original OSH server at `45.55.99.236:8080` has been superseded by the Oracle Cloud VM at `129-80-248-53.sslip.io`. Server 1 below documents the original OSH for historical reference. See Server 4 (OSH production) and Server 5 (Go v2) for current production servers.

---

## Server 1: OpenSensorHub (OSH) — ORIGINAL / HISTORICAL

> **Status: DECOMMISSIONED.** This server at `45.55.99.236:8080` is the original Phase 2–8 test server. It has been superseded by Server 4 (OSH on Oracle Cloud). Resource IDs, schema data, and quirks below are historical records from Smoke Tests #1–#18. **For current OSH production, see Server 4.**

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

---

## Server 3: 52North pygeoapi (Live, Oracle Cloud — Phase 9)

### Connection

| Property                | Value                                                                                                  |
| ----------------------- | ------------------------------------------------------------------------------------------------------ |
| **Base URL**            | `https://129-80-248-53.sslip.io/csapi-pygeoapi`                                                        |
| **Auth**                | None                                                                                                   |
| **SSL**                 | HTTPS via Caddy (sslip.io domain, no auth header)                                                      |
| **API Title**           | "connected-systems-pygeoapi"                                                                           |
| **Conformance Classes** | `ogcapi-common-1/1.0/conf/core` only — **no CSAPI classes advertised** in `/conformance`               |
| **OpenAPI**             | `/openapi` is **incomplete** — declares only ~11 paths; many active endpoints are not in the document  |

This is OS4CSAPI's own self-hosted build of [`52North/connected-systems-pygeoapi`](https://github.com/52North/connected-systems-pygeoapi). It is a separate server from the public `csa.demo.52north.org` instance documented as Server 2 above. Deployment notes, image build patches (uv venv `--python`, shapely pin removal, rasterio clang/lld), the Caddy config patch, and seed-data provenance are documented in `ogc-client-CSAPI_2/docs/research/phase-9/03-52north-pygeoapi-deployment-findings.md`.

---

### Resource Inventory (as of 2026-05-09 seed run, captures under `ogc-client-CSAPI_2/docs/research/phase-9/captures/oracle-pygeoapi/`)

| Endpoint            | GET listing | POST          | Notes                                                                                  |
| ------------------- | :---------: | :-----------: | -------------------------------------------------------------------------------------- |
| `/systems`          | OK          | OK (smljson)  | 10 systems after seed; 1 fixture + 9 seeded                                            |
| `/procedures`       | OK          | OK (smljson)  | 7 procedures; **POST is hard-routed through the SensorML writer** regardless of body   |
| `/deployments`      | OK          | OK (smljson)  | 4 deployments; `deployedSystems` field causes server-side `KeyError` if included       |
| `/datastreams`      | OK          | OK            | 16 datastreams; standard CSAPI JSON                                                    |
| `/observations`     | OK          | OK            | 170+ observations across 5 datastreams                                                 |
| `/samplingFeatures` | **broken**  | **405**       | Listing returns empty; detail returns 500; POST returns **405 Method Not Allowed**     |
| `/properties`       | OK          | **read-only** | No nested writer registered                                                            |
| `/controlstreams`   | absent      | absent        | Not implemented in this build                                                          |
| `/commands`         | absent      | absent        | Not implemented in this build                                                          |
| `/systemEvents`     | absent      | absent        | Not implemented in this build                                                          |
| `/systemHistory`    | absent      | absent        | Not implemented in this build                                                          |
| `/features`         | absent      | absent        | Not implemented in this build                                                          |

---

### Write Surface — POST Payload Quirks (CRUD Smoke Test failures expected)

**This server diverges from the spec on POST body shape for three Part 1 resources.** It does **not** accept the CSAPI GeoJSON `Feature` envelope (`{ type: "Feature", properties: {...}, geometry: {...} }`) that OSH and CSAPI-Go accept. The current Smoke Test page uses that envelope and fails predictably as follows:

| Resource         | Status                            | Server Message                                              | Cause                                                                                                                                 |
| ---------------- | --------------------------------- | ----------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| System           | **400 InvalidParameterValue**     | `'AttrDict' object has no attribute 'get'`                  | Internal pygeoapi crash when parsing the `Feature` envelope. Provider expects a stripped JSON body — no `type:"Feature"`, no wrapper. |
| Procedure        | **400 InvalidParameterValue**     | `smljson: ['definition' / 'id' / 'type' required]`          | `POST /procedures` is hard-routed through the SensorML writer. Body must be SML JSON (`{ "type":"PhysicalSystem", "id":..., ... }`).  |
| Deployment       | **400 InvalidParameterValue**     | `smljson: ['id' / 'type' required]`                         | Same as Procedure — POST is wired to the smljson writer.                                                                              |
| Sampling Feature | **405 Method Not Allowed** (HTML) | `The method is not allowed for the requested URL.`          | Read-only on this build. No POST handler registered despite occasional 201s from earlier seed paths.                                  |

These four failures are **expected** when running the CRUD Smoke Test against this server with the current single-shape payload. All other resource types (Subsystem, Subdeployment, Datastream, Control Stream, Observation, Command) skip because their parent CREATE never produced an ID.

---

### Content Negotiation

| Accept Header          | Behavior                                                                                                                     |
| ---------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| `application/sml+json` | Returns SensorML JSON envelope `{ items: [...], links: [] }`. Required form for POST to /systems, /procedures, /deployments. |
| `application/geo+json` | Returns GeoJSON `FeatureCollection`.                                                                                         |
| `application/json`     | Returns CSAPI JSON envelope; populated for /systems, /datastreams, /observations.                                            |
| `?f=smljson`           | Equivalent to `Accept: application/sml+json`.                                                                                |

Unlike Server 2 (`csa.demo.52north.org`), `Accept: application/json` returns populated collections here.

---

### Conformance Posture

`/conformance` advertises only `ogcapi-common-1/1.0/conf/core`. None of the CSAPI Part 1 / Part 2 conformance classes are declared, even though many of the endpoints work. **Treat this server as a partial CSAPI implementation for read paths and as a SensorML-only writer for Part 1 POSTs.** Strict-mode CSAPI conformance probing in the Connect screen will surface this as expected.
---

## Server 4: OpenSensorHub (OSH) — Current Production (Oracle Cloud)

### Connection

| Property                | Value                                                      |
| ----------------------- | ---------------------------------------------------------- |
| **Base URL**            | `https://129-80-248-53.sslip.io/sensorhub/api`            |
| **Auth**                | **None** (public, no auth header required)                 |
| **SSL**                 | HTTPS via Caddy                                            |
| **API Title**           | "Connected Systems API Service"                            |
| **Conformance Classes** | 20+ CSAPI conformance classes advertised                   |

### PowerShell Pattern

```powershell
$headers = @{ Accept = "application/geo+json" }
Invoke-RestMethod -Uri "https://129-80-248-53.sslip.io/sensorhub/api/systems" -Headers $headers
# SML format:
Invoke-RestMethod -Uri "https://129-80-248-53.sslip.io/sensorhub/api/systems/{id}?f=sml3"
```

### Key Quirks (current production, verified 2026-05-10)

| Quirk | Description |
|-------|-------------|
| SML format param | Use `?f=sml3` (NOT `?f=application/sml%2Bjson`) |
| SML response format | Fields at **top level** — `{type:"PhysicalSystem", label:..., documentation:...}` |
| SML key for docs | Uses `documents` (not `documentation`) |
| `system@link.href` | May contain `?f=json` query suffix — strip when extracting system ID |
| `outputName` filter | `?outputName=X` on `/datastreams` is **unreliable** — returns wrong results |
| `resultTime=latest` | Silently ignored |
| Observation sort | Default **ascending** (oldest first) |
| Sub-resource relationships | Most return 400; subsystems/subdeployments work |
| Write Content-Type | Part 1: `application/geo+json`; Part 2: `application/json` |

---

## Server 5: connected-systems-go (Go v2) — Current Production (Oracle Cloud)

### Connection

| Property                | Value                                                        |
| ----------------------- | ------------------------------------------------------------ |
| **Base URL**            | `https://129-80-248-53.sslip.io/csapi-go-v2`                |
| **Auth**                | Basic Auth — `os4csapi:ogc134mm`                             |
| **SSL**                 | HTTPS via Caddy                                              |
| **API Title**           | "OGC Connected Systems API"                                  |
| **Conformance Classes** | CSAPI Part 1 + Part 2 classes advertised                     |

### PowerShell Pattern

```powershell
$base = "https://129-80-248-53.sslip.io/csapi-go-v2"
$headers = @{ Authorization = "Basic b3M0Y3NhcGk6b2djMTM0bW0="; Accept = "application/geo+json" }
Invoke-RestMethod -Uri "$base/systems" -Headers $headers
# SML format:
$smlHeaders = @{ Authorization = "Basic b3M0Y3NhcGk6b2djMTM0bW0="; Accept = "application/sml+json" }
Invoke-RestMethod -Uri "$base/systems/{id}" -Headers $smlHeaders
```

### Key Quirks (verified 2026-04 → 2026-05-10)

| Quirk | Severity | Description |
|-------|----------|-------------|
| **SML response wrapped as GeoJSON Feature** | P2 | `GET /systems/{id}?f=application/sml+json` returns `{type:"Feature", geometry:{...}, properties:{uid, name, documentation,...}}` — SML fields are in `.properties`, NOT at top level. OSH returns raw SML at top level. **Client must detect `type === 'Feature'` and unwrap `.properties`.** |
| **SML key for docs** | — | Uses `documentation` (not `documents`) |
| **SML format param** | — | Use `?f=application/sml%2Bjson` (NOT `?f=sml3`) |
| **POST `/deployments/{id}/subdeployments` → 400** | P2 | Full deployment body returns HTTP 400. Retry with minimal stub `{uid, name}` only. |
| **`resultTime=latest` silently ignored** | P2 | Filter accepted but has no effect. Root cause: upstream issue #5 (`ToTimeRange` year-0001 bug). |
| **Observations sorted descending** | P2 | Default is newest-first (opposite of OSH). Use `items[0]` to get the latest observation. |
| **`GET /deployments/{id}/systems` → 404** | P2 | Sub-resource relationship endpoint not implemented. Use `platform@link` on deployment resources instead. |
| **POST 201 with empty body** | P3 | Creates resource but returns no body — parse `Location` header for new resource ID. |
| **`outputName` filter works** | — | Unlike OSH, `?outputName=X` on `/datastreams` works correctly. |
| **`GET /api` returns 88-byte stub** | P2 | OpenAPI spec is a TODO stub, missing required `paths` field. |

### SML Field Differences vs OSH

| Field | OSH Server 4 (top-level) | Go v2 Server 5 (in `.properties`) |
|-------|-------------------------|----------------------------------|
| Response root | `{type:"PhysicalSystem", ...}` | `{type:"Feature", properties:{...}, geometry:{...}}` |
| Documentation | `documents` key | `documentation` key |
| Label | `label` | `name` |

### Upstream Issues at SomethingCreativeStudios/connected-systems-go

| Issue | Status | Summary |
|-------|--------|---------|
| [#1](https://github.com/SomethingCreativeStudios/connected-systems-go/issues/1) | Open | `GET /api` stub missing `paths` |
| [#5](https://github.com/SomethingCreativeStudios/connected-systems-go/issues/5) | Open | `ToTimeRange` discards parse errors → year-0001 (explains silent filter failures) |
| [#7](https://github.com/SomethingCreativeStudios/connected-systems-go/issues/7) | Open | `resultTime`/`phenomenonTime` empty string conflation |
| [#10](https://github.com/SomethingCreativeStudios/connected-systems-go/issues/10) | Closed (PR #15) | `@link.href` absolutization fixed |
| [#11](https://github.com/SomethingCreativeStudios/connected-systems-go/issues/11) | Open | Inline `@link` missing enrichment |


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
3. **OSH (Servers 1 & 4): Use `?f=` for content negotiation.** Accept headers are ignored.
4. **52N (Servers 2 & 3): Never use `Accept: application/json`.** It returns empty collections.
5. **POST to OSH: Do not include `Accept: application/geo+json`.** It causes network-level failures.
6. **POST to OSH: Include `uid` in PUT payloads.** The library's type interfaces already require it.
7. **POST nested resources to OSH:** Use `POST /systems/{id}/datastreams`, not `POST /datastreams`.
8. **52N: Part 2 is completely broken.** All Part 2 testing must use OSH or Go v2.
9. **OSH: Sub-resource relationship endpoints return 400** (but subsystems/subdeployments work).
10. **OSH: Use lowercase `/controlstreams`** — camelCase `/controlStreams` returns 400.
11. **Go v2: SML response wraps in GeoJSON Feature.** When you `GET /systems/{id}?f=application/sml%2Bjson`, the SML fields are in `.properties` not at top level. Check for `type === 'Feature'` and unwrap.
12. **Go v2: Observations are sorted newest-first.** Use `items[0]` to get the latest, not `items[-1]`.
13. **Go v2: `resultTime=latest` is silently ignored.** Do not rely on it for fetching latest observations.
14. **Go v2: POST `/deployments/{id}/subdeployments` with full body → 400.** Retry with minimal stub `{uid, name}` only.
15. **Go v2 auth:** `Basic b3M0Y3NhcGk6b2djMTM0bW0=` (os4csapi:ogc134mm).
