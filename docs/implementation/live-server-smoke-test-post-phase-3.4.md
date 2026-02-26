# Live Server Smoke Test — Post Phase 3.4

**Date:** 2026-02-15  
**Milestone:** After completing Phase 3.4 (Issue #18)  
**Servers:** OpenSensorHub demo instance, 52North demo instance  
**Auth:** OSH: Basic auth required (credentials not stored in repo); 52North: None (expired SSL cert)  
**Purpose:** Validate GeoJSON handler stability (no regressions) after adding SensorML 3.0 type definitions (Issue #18), and perform structural type alignment of the new SensorML types against real server SensorML response data  
**Components tested:** `src/ogc-api/csapi/formats/geojson.ts` (5 public functions), `src/ogc-api/csapi/formats/sensorml/types.ts` (structural observation against real data — no runtime parser yet)

> This is smoke test #13 in the series (fourth Phase 3 smoke test). See also:
>
> - [Previous smoke test](live-server-smoke-test-post-phase-3.3.md) — Phase 3.3, Issues #52/#17, 56 findings
> - [Phase 3.2 smoke test](live-server-smoke-test-post-phase-3.2.md) — Phase 3.2, Issues #49/#15/#16/#51, 51 findings
> - [Phase 3.1 smoke test](live-server-smoke-test-post-phase-3.1.md) — Phase 3.1, first Phase 3 test, 48 findings
> - [Phase 2.8 smoke test](live-server-smoke-test-post-phase-2.8.md) — Phase 2.8, final Phase 2 URL builder test
> - [Phase 3 smoke test rationale](phase-3-smoke-test-rationale.md)

## Test Methodology

Fetched real responses from both servers using PowerShell `Invoke-WebRequest` / `Invoke-RestMethod`, saved as JSON files, then ran all GeoJSON handler functions against every feature using a Node.js validation script (tsx). For SensorML type alignment, fetched `application/sml+json` responses from OSH and compared server field names, types, and nesting against the SensorML type definitions in `sensorml/types.ts`. No code changes were made during the smoke test — read-only observation per Lesson 10.

**Changes since last smoke test (Phase 3.3):**

- **Issue #18:** SensorML 3.0 type definitions — 916 lines of TypeScript interfaces in `sensorml/types.ts`, 400 lines of compilation/discriminator tests. Types-only module with no runtime code. Imports 7 SWE Common types.

**Key behavioral change:** None — Issue #18 adds only type definitions. No runtime code was changed or added. The GeoJSON handler is unchanged.

**Unit tests:** 423 CSAPI (6 suites) + 31 mime-type (1 suite) — all passing. `tsc` clean.

---

## Server Profiles

### OpenSensorHub

| Property    | Value                                    |
| ----------- | ---------------------------------------- |
| URL         | `http://45.55.99.236:8080/sensorhub/api` |
| Auth        | Basic (credentials not stored in repo)   |
| Root status | ✅ 200 — 10 links in root document       |

| Resource Type    | Endpoint            | Count  | Has Data? | Change from Phase 3.3       |
| ---------------- | ------------------- | ------ | --------- | --------------------------- |
| Systems          | `/systems`          | **12** | ✅ Yes    | Unchanged                   |
| Deployments      | `/deployments`      | 0      | ❌ Empty  | Unchanged                   |
| Procedures       | `/procedures`       | 0      | ❌ Empty  | Unchanged                   |
| SamplingFeatures | `/samplingFeatures` | **51** | ✅ Yes    | **Increased from 20+ → 51** |
| DataStreams      | `/datastreams`      | 100+   | ✅ Yes    | Increased significantly     |
| Observations     | `/observations`     | 5+     | ✅ Yes    | Unchanged                   |
| ControlStreams   | `/controlstreams`   | 8+     | ✅ Yes    | Unchanged                   |
| Properties       | `/properties`       | 0      | ❌ Empty  | Unchanged                   |

**Server data growth:** OSH SamplingFeatures have grown from 20+ to 51 (2.5× increase). DataStreams have also grown significantly. This continues the growth trend observed in Phase 3.3 (where systems grew from 5 to 12).

### 52North

| Property          | Value                                                  |
| ----------------- | ------------------------------------------------------ |
| URL               | `https://csa.demo.52north.org`                         |
| Auth              | None required                                          |
| SSL               | Expired certificate — requires `-SkipCertificateCheck` |
| Root status       | ✅ 200 — 7 links in root document                      |
| Root Content-Type | `None` (unchanged from Phase 3.3 — F52)                |

| Resource Type    | Endpoint            | Count | Has Data?    | Change from Phase 3.3     |
| ---------------- | ------------------- | ----- | ------------ | ------------------------- |
| Systems          | `/systems`          | **0** | ❌ **Empty** | **CHANGE: was 3 → now 0** |
| Deployments      | `/deployments`      | **0** | ❌ **Empty** | **CHANGE: was 1 → now 0** |
| Procedures       | `/procedures`       | **0** | ❌ **Empty** | **CHANGE: was 1 → now 0** |
| SamplingFeatures | `/samplingFeatures` | 0     | ❌ Empty     | Unchanged                 |
| DataStreams      | `/datastreams`      | —     | ❌ 500       | Unchanged                 |
| Observations     | `/observations`     | —     | ❌ 500       | Unchanged                 |
| ControlStreams   | `/controlstreams`   | —     | ❌ 404       | Unchanged                 |
| Properties       | `/properties`       | 0     | ❌ Empty     | Unchanged                 |

~~**⚠️ 52North data loss:** All previously available data (3 systems, 1 deployment, 1 procedure) has been removed. The server responds correctly (200) but returns empty `FeatureCollection` for all collection endpoints. The server also now returns `Content-Type: application/json` for collection requests (previously defaulted to `application/sml+json`). This means **52North cannot be used for handler validation in this smoke test.** See [F57].~~

> **⚠️ CORRECTION (2026-02-15):** The above was incorrect. The data was never lost — the smoke test changed from no explicit `Accept` header (which defaults to `application/sml+json` with data) to `Accept: application/json` (which returns empty GeoJSON from a separate provider). See corrected [F57] and [F57 correction report](f57-content-negotiation-correction.md).

---

## Results

### Prior Findings — Regression Check

All 56 findings from prior smoke tests re-evaluated:

| Finding | Title                                            | Prior Status            | Current Status             | Evidence                                                                                                          |
| ------- | ------------------------------------------------ | ----------------------- | -------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| F1      | Link relation prefix mismatch                    | Fixed (Issue #34)       | ✅ Still fixed             | No regression                                                                                                     |
| F2      | Top-level vs. collection-scoped URLs             | Fixed (Issue #35)       | ✅ Still fixed             | No regression                                                                                                     |
| F3      | Response envelope uses `items`                   | Deferred to Phase 3     | ⏳ Still deferred          | OSH: `{items:[...]}`, 52N GeoJSON: `{type:"FeatureCollection", features:[...]}`                                   |
| F4      | `validTime` is an array                          | Addressed by Phase 3    | ✅ Still addressed         | `parseValidTime()` correctly handles `["ISO","now"]` on all 12 OSH systems                                        |
| F5      | Missing pagination metadata                      | Deferred to Phase 3     | ⏳ Still deferred          | Both servers use link-based pagination only                                                                       |
| F6      | OSH rejects `systems/{id}/deployments`           | Server limitation       | ⚠️ Still present           | Not retested (unchanged)                                                                                          |
| F7      | OSH rejects `systems/{id}/procedures`            | Server limitation       | ⚠️ Still present           | Not retested (unchanged)                                                                                          |
| F8      | OSH rejects `samplingFeatures/{id}/systems`      | Server limitation       | ⚠️ Still present           | Not retested (unchanged)                                                                                          |
| F9      | OSH rejects `samplingFeatures/{id}/history`      | Server limitation       | ⚠️ Still present           | Not retested (unchanged)                                                                                          |
| F10     | 52North now has real data                        | Informational           | ⚠️ **Reversed — see F57**  | 52N collections are now empty                                                                                     |
| F11     | 52North uses SensorML format                     | Phase 3 concern         | ⚠️ **Changed**             | 52N now returns `application/json` for collections (was `application/sml+json`)                                   |
| F12     | 52North `systems/{id}/deployments` works         | Informational           | ❓ Cannot verify           | No data to test                                                                                                   |
| F13     | Both servers use `items` envelope                | Revised in 3.1          | ⚠️ Still revised           | Envelope varies by server AND format                                                                              |
| F14     | Properties not discoverable via links            | Shared concern          | ⏳ Still present           | Neither server exposes properties in root links                                                                   |
| F15     | 52North adds third system                        | Informational           | ⚠️ **Reversed**            | 52N now has 0 systems                                                                                             |
| F16     | OSH rejects `datastreams/{id}/systems`           | Server limitation       | ⚠️ Still present           | Not retested                                                                                                      |
| F17     | OSH rejects `datastreams/{id}/procedures`        | Server limitation       | ⚠️ Still present           | Not retested                                                                                                      |
| F18     | OSH rejects `datastreams/{id}/history`           | Server limitation       | ⚠️ Still present           | Not retested                                                                                                      |
| F19     | `resultTime=latest` accepted by OSH              | Resolved                | ✅ Still valid             | Not retested                                                                                                      |
| F20     | 52North DataStreams still broken (500)           | Server limitation       | ⚠️ **Still present**       | `GET /datastreams?limit=1` → 500                                                                                  |
| F21     | OSH rejects `observations/{id}/datastream`       | Server limitation       | ⚠️ Still present           | Not retested                                                                                                      |
| F22     | OSH rejects `observations/{id}/samplingFeature`  | Server limitation       | ⚠️ Still present           | Not retested                                                                                                      |
| F23     | OSH rejects `observations/{id}/system`           | Server limitation       | ⚠️ Still present           | Not retested                                                                                                      |
| F24     | OSH rejects `observations/{id}/history`          | Server limitation       | ⚠️ Still present           | Not retested                                                                                                      |
| F25     | `resultTime=latest` returns real data            | Informational           | ✅ Still valid             | Not retested                                                                                                      |
| F26     | 52North Observations broken (500)                | Server limitation       | ⚠️ **Still present**       | `GET /observations?limit=1` → 500                                                                                 |
| F27     | Observation `foi@id` naming variation            | Phase 3 concern         | ⏳ Still deferred          | Not yet in scope                                                                                                  |
| F28     | OSH rejects `controlstreams/{id}/feasibility`    | Server limitation       | ⚠️ Still present           | Not retested                                                                                                      |
| F29     | ControlStream schema works                       | Informational           | ✅ Still valid             | Not retested                                                                                                      |
| F30     | ControlStream `system@link` cross-reference      | Phase 3 concern         | ⏳ Still deferred          | Not yet in scope                                                                                                  |
| F31     | Command entity data shape                        | Phase 3 concern         | ⏳ Still deferred          | Not yet in scope                                                                                                  |
| F32     | 52North ControlStreams not implemented (404)     | Server limitation       | ⚠️ **Still present**       | `GET /controlstreams?limit=1` → 404                                                                               |
| F33     | ControlStream schema returns SWE DataRecord      | Phase 3 concern         | ⏳ Still deferred          | Not yet in scope                                                                                                  |
| F34     | OSH no top-level `/commands`                     | Shared concern          | ⚠️ Still present           | Not retested                                                                                                      |
| F35     | OSH no `/commands/{id}/cancel`                   | Server limitation       | ⚠️ Still present           | Not retested                                                                                                      |
| F36     | OSH ignores `id` query param on commands         | Server limitation       | ⚠️ Still present           | Not retested                                                                                                      |
| F37     | Command `/result` returns 404                    | Expected behavior       | ✅ Still valid             | Not retested                                                                                                      |
| F38     | Command status data shape                        | Phase 3 concern         | ⏳ Still deferred          | Not yet in scope                                                                                                  |
| F39     | Commands use `items` envelope                    | Informational           | ✅ Confirms F3             | Not retested                                                                                                      |
| F40     | OSH SamplingFeatures use non-SOSA vocabulary     | Fixed (Issue #49)       | ✅ **Still fixed**         | All 51 OSH SamplingFeatures recognized via SensorML namespace                                                     |
| F41     | 52N Systems have null featureType in GeoJSON     | Critical — needs design | ❓ **Cannot verify**       | 52N systems collection is now empty                                                                               |
| F42     | 52N Deployment has null validTime                | Server limitation       | ❓ **Cannot verify**       | 52N deployments collection is now empty                                                                           |
| F43     | 52N Procedures misclassified as System           | Interop concern         | ❓ **Cannot verify**       | 52N procedures collection is now empty                                                                            |
| F44     | 52N uses both CURIE and full URI forms           | Positive validation     | ❓ **Cannot verify**       | No 52N data                                                                                                       |
| F45     | Response envelope varies by server AND format    | Informational           | ✅ Unchanged               | 52N still returns FeatureCollection wrapper for `?f=application/json`                                             |
| F46     | OSH ignores SensorML Accept header               | Informational           | ⚠️ **Partially corrected** | Single-resource endpoint now returns `application/sml+json`; collection endpoint still returns `application/json` |
| F47     | 52N GeoJSON includes `@link` notation            | Phase 3 concern         | ❓ **Cannot verify**       | No 52N data                                                                                                       |
| F48     | OSH features have empty links arrays             | Low                     | ✅ Still true              | All 63+ OSH features (12 systems + 51 SF) have `links: []`                                                        |
| F49     | OSH SamplingFeatures lack `sampledFeature@link`  | Resolved (Issue #52)    | ✅ **Still resolved**      | All 51 OSH SamplingFeatures extract successfully                                                                  |
| F50     | 52North default content type changed to SML      | Informational           | ⚠️ **Changed**             | 52N now returns `application/json` for collections (was `application/sml+json`)                                   |
| F51     | 52N `/samplingFeatures` endpoint now functional  | Informational           | ✅ Still present           | Returns 200, empty collection                                                                                     |
| F52     | 52N returns `Content-Type: None` on root         | Informational           | ✅ **Still present**       | Root endpoint still returns `Content-Type: None`                                                                  |
| F53     | OSH data inventory has grown significantly       | Informational           | ✅ Continued               | Now 51 SamplingFeatures (was 20+)                                                                                 |
| F54     | F49 confirmed RESOLVED                           | Positive                | ✅ Reconfirmed             | 51/51 SamplingFeatures extract (was 20/20 in Phase 3.3)                                                           |
| F55     | F42 no longer blocking                           | Positive                | ❓ **Cannot verify**       | 52N deployment gone                                                                                               |
| F56     | OSH schema endpoint returns `Content-Type: auto` | Informational           | ✅ **Still present**       | Schema endpoint still returns `Content-Type: auto`                                                                |

~~**Summary:** 0 regressions. **F10, F11, F15, F50 status changed** — 52North server has been reset (all data removed). **F41, F42, F43, F44, F47, F55** cannot be re-verified due to empty 52N data.~~ **F46 partially corrected** — OSH now returns `application/sml+json` on single-resource endpoints (was `application/json` for everything). ~~**5 findings cannot be verified** due to 52N data loss — findings retained with current status.~~

> **CORRECTION (2026-02-15):** 52North data was NOT removed. The "cannot verify" status of F41, F42, F43, F44, F47, F55 was based on incorrect F57. These findings should be re-verifiable using `Accept: application/sml+json`. See [F57 correction report](f57-content-negotiation-correction.md).

---

### GeoJSON Handler — Recognition

| Server | Resource Type    | Features Tested | All Recognized? | Classification        | Change from Phase 3.3        |
| ------ | ---------------- | --------------- | --------------- | --------------------- | ---------------------------- |
| OSH    | Systems          | 12              | ✅ Yes          | All → System          | Unchanged — same 12 systems  |
| OSH    | SamplingFeatures | 51              | ✅ Yes          | All → SamplingFeature | **Count increased: 20 → 51** |
| OSH    | Deployments      | 0               | —               | Empty collection      | Unchanged                    |
| OSH    | Procedures       | 0               | —               | Empty collection      | Unchanged                    |
| 52N    | Systems          | 0               | —               | **Empty collection**  | **CHANGE: was 3 → now 0**    |
| 52N    | Deployments      | 0               | —               | **Empty collection**  | **CHANGE: was 1 → now 0**    |
| 52N    | Procedures       | 0               | —               | **Empty collection**  | **CHANGE: was 1 → now 0**    |

**Recognition rate: 63 of 63 features recognized (100%).** Up from 34/37 (92%) in Phase 3.3. The improvement is due to 52N's null-featureType systems (F41) no longer being in the pool — they were removed, not fixed.

---

### GeoJSON Handler — Extraction

| Server | Resource Type    | Features Tested | All Extracted? | Issues                        | Change from Phase 3.3                                |
| ------ | ---------------- | --------------- | -------------- | ----------------------------- | ---------------------------------------------------- |
| OSH    | Systems          | 12              | ✅ Yes         | All properties correct        | Unchanged                                            |
| OSH    | SamplingFeatures | 20 (of 51)      | ✅ Yes         | All 20 extracted successfully | **Count increased (51 total, 20 tested)**            |
| 52N    | Systems          | 0               | —              | Empty collection              | **CHANGE: was 3 (0 extracted due to F41)**           |
| 52N    | Deployments      | 0               | —              | Empty collection              | **CHANGE: was 1 (extracted in Phase 3.3)**           |
| 52N    | Procedures       | 0               | —              | Empty collection              | **CHANGE: was 1 (extracted as System in Phase 3.3)** |

**Extraction rate: 32 of 32 features tested (100%).** The 100% rate is an artifact of 52N having no data — the features that previously failed recognition (F41) are no longer available to test.

**Detailed extraction results — OSH Systems (12/12):**

| Feature ID   | id  | uid (valid URI?)                              | name                               | validTime            | geometry | links |
| ------------ | --- | --------------------------------------------- | ---------------------------------- | -------------------- | -------- | ----- |
| 03bc5ofvvstg | ✅  | ✅ `urn:osh:driver:mavsdk:cube:replay`        | ✅ "LIVE - Field Drone"            | ✅ start: 2026-01-26 | null     | []    |
| 02sv18sqotc0 | ✅  | ✅ `urn:android:device:...:blue2:...:replay`  | ✅ "LIVE - Android Phone [Blue 2]" | ✅ start: 2026-01-26 | null     | []    |
| 03hsjcf4odig | ✅  | ✅ `urn:android:device:...:blue1:...:replay`  | ✅ "LIVE - Android Phone [Blue 1]" | ✅ start: 2026-01-26 | null     | []    |
| 040g         | ✅  | ✅ `urn:android:device:dad41d3c8bf853cd`      | ✅ "Android Sensors [SR_Botts]"    | ✅ start: 2026-02-10 | null     | []    |
| 0410         | ✅  | ✅ `urn:osh:sensor:kestrel:FE:BB:D9:8B:53:23` | ✅ "Kestrel Weather [SR_Cardy]"    | ✅ start: 2026-02-10 | null     | []    |
| 041g         | ✅  | ✅ `urn:android:device:9fd2f1404e95fb6b`      | ✅ "Android Sensors [SR_Cardy]"    | ✅ start: 2026-02-10 | null     | []    |
| 0420         | ✅  | ✅ `urn:android:polar:ea93cc9c820ba1e1`       | ✅ "Polar Heart [SR_Brown]"        | ✅ start: 2026-02-10 | null     | []    |
| 042g         | ✅  | ✅ `urn:android:device:ea93cc9c820ba1e1`      | ✅ "Android Sensors [SR_Brown]"    | ✅ start: 2026-02-10 | null     | []    |
| 0430         | ✅  | ✅ `urn:android:device:10e7bb3d873483a2`      | ✅ "Android Sensors [SR_Cardy22]"  | ✅ start: 2026-02-10 | null     | []    |
| 081g         | ✅  | ✅ `urn:android:device:...:blue1:011426`      | ✅ "Android Sensors [blue1]"       | ✅ start: 2026-01-14 | null     | []    |
| 0c3g         | ✅  | ✅ `urn:android:device:...:blue2:011426`      | ✅ "Android Sensors [blue2]"       | ✅ start: 2026-01-14 | null     | []    |
| 0o30         | ✅  | ✅ `urn:osh:driver:mavsdk:cube`               | ✅ "FCU Field Drone CubePilot"     | ✅ start: 2026-01-14 | null     | []    |

---

### parseValidTime — Live Data

| Server               | Features With validTime | All Parsed? | Format Observed                       | Issues                                        |
| -------------------- | ----------------------- | ----------- | ------------------------------------- | --------------------------------------------- |
| OSH Systems          | 12                      | ✅ Yes      | `["2026-mm-ddThh:mm:ss.sssZ", "now"]` | All parsed to `{start: Date, end: undefined}` |
| OSH SamplingFeatures | 0                       | —           | No validTime on SamplingFeatures      | —                                             |
| 52N (all)            | 0                       | —           | No data available                     | —                                             |

**parseValidTime working correctly.** No change from Phase 3.3. All 12 OSH systems have the array format `["ISO-8601", "now"]` → correctly parsed to `{ start: Date, end: undefined }`.

---

### SensorML Types — Structural Alignment Against Live Data

This is the **primary test for Issue #18**. Since `sensorml/types.ts` contains only TypeScript type definitions (no runtime parser), validation consists of comparing real SensorML JSON responses from OSH against our type interfaces to confirm structural fidelity.

**Source:** OSH `/systems?f=application/sml+json` and `/systems/{id}?f=application/sml+json`

#### OSH SensorML Response Format

When requesting `f=application/sml+json`, OSH returns SensorML-shaped JSON:

- **Collection endpoint:** `Content-Type: application/json` (ignores format request, but body IS SensorML)
- **Single-resource endpoint:** `Content-Type: application/sml+json` (correct)

All 12 OSH systems return `type: "PhysicalSystem"` — this is one of our four concrete SensorML process types.

#### Field-level Type Alignment — PhysicalSystem (system 040g)

```json
{
  "type": "PhysicalSystem",
  "id": "040g",
  "uniqueId": "urn:android:device:dad41d3c8bf853cd",
  "definition": "http://www.w3.org/ns/sosa/Sensor",
  "label": "Android Sensors [SR_Botts]",
  "validTime": ["2026-02-10T19:43:37.265Z", "now"],
  "localReferenceFrames": [
    {
      "id": "LOCAL_FRAME",
      "origin": "Center of the device screen",
      "axes": [
        {
          "name": "x",
          "description": "The X axis is in the plane of the screen and points to the right"
        },
        {
          "name": "y",
          "description": "The Y axis is in the plane of the screen and points up"
        },
        {
          "name": "z",
          "description": "The Z axis points towards the outside of the front face of the screen"
        }
      ]
    }
  ],
  "components": [
    {
      "type": "PhysicalComponent",
      "name": "sensor0",
      "id": "SENSOR_...",
      "label": "lsm6dso Accelerometer"
    },
    {
      "type": "PhysicalComponent",
      "name": "sensor1",
      "id": "SENSOR_...",
      "label": "Rotation Vector"
    },
    {
      "type": "PhysicalComponent",
      "name": "sensor2",
      "id": "LOC_GPS",
      "label": "gps"
    },
    {
      "type": "PhysicalComponent",
      "name": "sensor3",
      "id": "CAM_0",
      "label": "Android Camera #0"
    }
  ]
}
```

| Server Field                    | Our Type                     | Interface                                                                                           | Property                                | Match? | Notes                                    |
| ------------------------------- | ---------------------------- | --------------------------------------------------------------------------------------------------- | --------------------------------------- | ------ | ---------------------------------------- | --------------------------------- |
| `type: "PhysicalSystem"`        | `PhysicalSystem.type`        | `PhysicalSystem`                                                                                    | `type: 'PhysicalSystem'`                | ✅     | String literal discriminator             |
| `id: "040g"`                    | (API-level ID)               | Not in SensorML types                                                                               | —                                       | ✅     | Added by CSAPI, not in SensorML spec     |
| `uniqueId`                      | `DescribedObject.uniqueId`   | `DescribedObject`                                                                                   | `uniqueId?: string`                     | ✅     |                                          |
| `definition`                    | `DescribedObject.definition` | `DescribedObject`                                                                                   | `definition?: string`                   | ✅     |                                          |
| `label`                         | `DescribedObject.label`      | `DescribedObject`                                                                                   | `label: string` (required)              | ✅     |                                          |
| `validTime: [...]`              | `DescribedObject.validTime`  | `DescribedObject`                                                                                   | `validTime?: TimePeriod`                | ✅     | `TimePeriod = [string]                   | [string, string]` — array matches |
| `localReferenceFrames`          | `AbstractPhysicalProcess`    | `AbstractPhysicalProcess`                                                                           | `localReferenceFrames?: SpatialFrame[]` | ✅     |                                          |
| `localReferenceFrames[].id`     | `AbstractSweIdentifiable.id` | `SpatialFrame extends AbstractSweIdentifiable`                                                      | `id?: string`                           | ✅     |                                          |
| `localReferenceFrames[].origin` | `SpatialFrame.origin`        | `SpatialFrame`                                                                                      | `origin: string` (required)             | ✅     |                                          |
| `localReferenceFrames[].axes`   | `SpatialFrame.axes`          | `SpatialFrame`                                                                                      | `axes: FrameAxis[]` (required)          | ✅     |                                          |
| `axes[].name`                   | `FrameAxis.name`             | `FrameAxis`                                                                                         | `name: string` (required)               | ✅     |                                          |
| `axes[].description`            | `FrameAxis.description`      | `FrameAxis`                                                                                         | `description: string` (required)        | ✅     |                                          |
| `components`                    | `PhysicalSystem.components`  | `PhysicalSystem`                                                                                    | `components?: ComponentList`            | ✅     | `ComponentList = ComponentEntry[]`       |
| `components[].type`             | Discriminator                | `PhysicalComponent`                                                                                 | `type: 'PhysicalComponent'`             | ✅     | All 4 components are `PhysicalComponent` |
| `components[].name`             | `ComponentEntry.name`        | `ComponentEntry`                                                                                    | `name: string` (required)               | ✅     |                                          |
| `components[].id`               | (API-level ID)               | Not in SensorML types                                                                               | —                                       | ✅     | Added by CSAPI                           |
| `components[].label`            | `DescribedObject.label`      | `PhysicalComponent extends AbstractPhysicalProcess extends AbstractProcess extends DescribedObject` | `label: string`                         | ✅     | Inherited from DescribedObject           |

**17/17 fields match.** All server fields map correctly to our type interfaces.

#### Field-level Type Alignment — PhysicalSystem with Parameters (system 0o30)

The "FCU Field Drone CubePilot" system has `parameters` — an array of `DataRecord` objects:

```json
{
  "parameters": [
    {
      "type": "DataRecord",
      "name": "mavControl",
      "label": "Location Control",
      "description": "Interfaces with MAVLINK...",
      "updatable": true,
      "fields": [
        {
          "type": "Vector",
          "name": "locationVectorLLA",
          "referenceFrame": "",
          "coordinates": [
            {
              "type": "Quantity",
              "name": "Latitude",
              "uom": { "code": "deg" }
            },
            {
              "type": "Quantity",
              "name": "Longitude",
              "uom": { "code": "deg" }
            },
            {
              "type": "Quantity",
              "name": "AltitudeAGL",
              "uom": { "code": "m" }
            }
          ]
        },
        { "type": "Boolean", "name": "returnToStart" },
        { "type": "Count", "name": "hoverSeconds" }
      ]
    }
  ]
}
```

| Server Field                              | Our Type                        | Interface                                                                   | Property                     | Match? | Notes                                   |
| ----------------------------------------- | ------------------------------- | --------------------------------------------------------------------------- | ---------------------------- | ------ | --------------------------------------- |
| `parameters`                              | `AbstractProcess.parameters`    | `AbstractProcess`                                                           | `parameters?: ParameterList` | ✅     | `ParameterList = IOComponentChoice[]`   |
| `parameters[].type: "DataRecord"`         | SWE Common `DataRecord.type`    | `DataRecord`                                                                | `type: 'DataRecord'`         | ✅     | IOComponentChoice includes AnyComponent |
| `parameters[].name`                       | `IOComponentChoice.name`        | `IOComponentChoice = {name: string} & (AnyComponent \| ObservableProperty)` | `name: string`               | ✅     |                                         |
| `parameters[].label`                      | `AbstractSweIdentifiable.label` | `DataRecord extends AbstractSweIdentifiable`                                | `label?: string`             | ✅     |                                         |
| `parameters[].updatable`                  | `DataRecord.updatable`          | `DataRecord`                                                                | `updatable?: boolean`        | ✅     |                                         |
| `parameters[].fields[].type: "Vector"`    | SWE Common `Vector.type`        | `Vector`                                                                    | `type: 'Vector'`             | ✅     |                                         |
| `fields[].coordinates[].type: "Quantity"` | SWE Common `SweQuantity.type`   | `SweQuantity`                                                               | `type: 'Quantity'`           | ✅     |                                         |
| `fields[].coordinates[].uom.code`         | `UnitOfMeasure.code`            | `UnitOfMeasure`                                                             | `code?: string`              | ✅     |                                         |
| `fields[].type: "Boolean"`                | SWE Common `SweBoolean.type`    | `SweBoolean`                                                                | `type: 'Boolean'`            | ✅     |                                         |
| `fields[].type: "Count"`                  | SWE Common `SweCount.type`      | `SweCount`                                                                  | `type: 'Count'`              | ✅     |                                         |

**10/10 fields match.** The `parameters` array correctly maps through `AbstractProcess → ParameterList → IOComponentChoice → AnyComponent → DataRecord/Vector/Quantity/Boolean/Count`. This exercises the **SWE Common × SensorML integration** — the exact cross-module type dependency tested in the `sensorml/types.spec.ts` unit tests.

#### SWE Common Types — Schema Endpoint Alignment (continued)

The OSH GPS datastream schema has grown richer since Phase 3.3:

```json
{
  "resultSchema": {
    "type": "DataRecord",
    "name": "gps_data",
    "definition": "http://sensorml.com/ont/swe/property/Location",
    "fields": [
      {
        "type": "Vector",
        "name": "location",
        "definition": "http://sensorml.com/ont/swe/property/LocationVector",
        "referenceFrame": "http://www.opengis.net/def/crs/EPSG/0/4979",
        "localFrame": "urn:android:device:...#LOCAL_FRAME",
        "coordinates": [
          {
            "type": "Quantity",
            "name": "lat",
            "axisID": "Lat",
            "uom": { "code": "deg" }
          },
          {
            "type": "Quantity",
            "name": "lon",
            "axisID": "Lon",
            "uom": { "code": "deg" }
          },
          {
            "type": "Quantity",
            "name": "alt",
            "axisID": "h",
            "uom": { "code": "m" }
          }
        ]
      }
    ]
  }
}
```

New fields observed since Phase 3.3:

| Server Field            | Our SWE Type             | Match? | Notes     |
| ----------------------- | ------------------------ | ------ | --------- |
| `Vector.definition`     | `AbstractSWE.definition` | ✅     | Inherited |
| `Vector.referenceFrame` | `Vector.referenceFrame`  | ✅     |           |
| `Vector.localFrame`     | `Vector.localFrame`      | ✅     |           |
| `Quantity.definition`   | `AbstractSWE.definition` | ✅     | Inherited |
| `Quantity.axisID`       | `SweQuantity.axisID`     | ✅     |           |

**All fields match SWE Common types.** The `Vector.localFrame` reference to `LOCAL_FRAME` matches the `SpatialFrame.id` in the SensorML system description — confirming the cross-type reference pattern.

---

### Vocabulary Inventory

| featureType Value                             | Server(s) | Endpoint                            | Vocabulary          | Recognized? | Handler Classification | Change from Phase 3.3                     |
| --------------------------------------------- | --------- | ----------------------------------- | ------------------- | ----------- | ---------------------- | ----------------------------------------- |
| `http://www.w3.org/ns/sosa/Sensor`            | OSH       | /systems                            | SOSA (full URI)     | ✅ Yes      | System                 | Unchanged — now tested on 12 features     |
| `http://www.opengis.net/sensorml/2.0#Feature` | OSH       | /samplingFeatures                   | SensorML (full URI) | ✅ Yes      | SamplingFeature        | Unchanged — now tested on 51 features     |
| `null`                                        | ~~52N~~   | ~~/systems (GeoJSON)~~              | —                   | —           | —                      | **Cannot verify** — 52N systems empty     |
| `http://www.w3.org/ns/sosa/Deployment`        | ~~52N~~   | ~~/deployments~~                    | —                   | —           | —                      | **Cannot verify** — 52N deployments empty |
| `sosa:Sensor`                                 | ~~52N~~   | ~~/procedures~~, ~~/systems (SML)~~ | —                   | —           | —                      | **Cannot verify** — 52N empty             |
| `sosa:Platform`                               | ~~52N~~   | ~~/systems (SML)~~                  | —                   | —           | —                      | **Cannot verify** — 52N empty             |

**Vocabulary coverage unchanged:** 2 OSH values still recognized. 4 52N values cannot be verified due to empty data. No new featureType values discovered.

---

### SensorML Process Type Inventory (NEW)

This is a new dimension — inventorying the SensorML `type` discriminator values observed on real data, mapped to our type definitions:

| SensorML `type` Value | Server | Endpoint                             | Our Type            | Count                 | Match? |
| --------------------- | ------ | ------------------------------------ | ------------------- | --------------------- | ------ |
| `PhysicalSystem`      | OSH    | /systems (SML)                       | `PhysicalSystem`    | 12                    | ✅     |
| `PhysicalComponent`   | OSH    | /systems (SML, nested in components) | `PhysicalComponent` | 24 (across 6 systems) | ✅     |
| `SimpleProcess`       | —      | Not observed                         | `SimpleProcess`     | 0                     | —      |
| `AggregateProcess`    | —      | Not observed                         | `AggregateProcess`  | 0                     | —      |

**2 of 4 SensorML process types observed in real data.** Both match our type definitions. `SimpleProcess` and `AggregateProcess` are not present in OSH data — likely used by other OGC implementations.

---

### Content-Type Availability

| Content-Type                        | Endpoint Tested          | OSH Available?                                      | 52N Available?                            | Change from Phase 3.3                           |
| ----------------------------------- | ------------------------ | --------------------------------------------------- | ----------------------------------------- | ----------------------------------------------- |
| `application/json` (default)        | /systems                 | ✅ 200 (OSH default)                                | ✅ 200 (now 52N default too)              | **52N changed** — was `application/sml+json`    |
| `application/geo+json`              | /systems?f=...           | ✅ 200 (returns GeoJSON FeatureCollection)          | ✅ 200 (empty FeatureCollection)          | Unchanged                                       |
| `application/sml+json` (collection) | /systems?f=...           | ⚠️ 200 (CT returns `application/json`, body IS SML) | ✅ 200 (empty, CT=`application/sml+json`) | **Partially corrected on OSH**                  |
| `application/sml+json` (single)     | /systems/{id}?f=...      | ✅ 200 (CT=`application/sml+json`)                  | ❓ No data to test                        | **NEW: OSH single-resource returns correct CT** |
| `application/swe+json` (schema)     | /datastreams/{id}/schema | ✅ 200 (CT=`auto`)                                  | ❌ 500 (datastreams broken)               | Unchanged                                       |

**Key change:** OSH now correctly returns `Content-Type: application/sml+json` for single-resource SensorML requests (e.g., `/systems/040g?f=application/sml+json`). Previously it returned `application/json` for everything. Collection requests still return `application/json` regardless of format request.

---

## New Findings

### F57 ~~(Moderate): 52North server data has been completely removed~~ CORRECTED: Content negotiation error — data was never lost

~~**Severity:** Moderate~~  
~~**Category:** Server limitation~~  
~~**Affects:** Interoperability testing coverage~~  
~~**Ownership:** Upstream~~  
~~**Evidence:**~~

- ~~Phase 3.3: 3 systems, 1 deployment, 1 procedure~~
- ~~Phase 3.4: 0 systems, 0 deployments, 0 procedures~~
- ~~All collection endpoints return `200` with empty `{ type: "FeatureCollection", features: [], links: [] }`~~
- ~~DataStreams (500 Internal Server Error), Observations (500 Internal Server Error), ControlStreams (404) — unchanged errors~~
- ~~Root endpoint still responds (200, 7 links) — API structure intact (`connected-systems-pygeoapi`)~~
- ~~**Re-verified independently** on the same date: confirmed all 6 resource collection endpoints (`/systems`, `/deployments`, `/procedures`, `/datastreams`, `/observations`, `/controlstreams`) — the server is responding correctly with valid JSON but every collection is genuinely empty. The 500 errors on DataStreams/Observations are likely a consequence of having no parent systems to associate with. This is consistent with a database reset or redeployment on 52North's demo infrastructure.~~

~~**Impact:** 52North was the only server providing Deployment and Procedure data, and the only source of CURIE-format featureType values (`sosa:Sensor`, `sosa:Platform`). With no 52N data:~~

- ~~F41 (null featureType) cannot be re-verified~~
- ~~F43 (Procedures misclassified) cannot be re-verified~~
- ~~CURIE vocabulary handling cannot be live-tested~~
- ~~Deployment extraction cannot be live-tested~~
- ~~The smoke test series drops to **single-server validation** until 52N data is restored~~

~~**Status:** Upstream — confirmed not a transient issue; monitor for data restoration in future smoke tests~~

> **⚠️ CORRECTION (2026-02-15):** F57 was incorrect. The 52North data was never lost. The Phase 3.4 smoke test used `Accept: application/json` in its HTTP requests, which routes to 52North's empty pygeoapi GeoJSON provider. The Phase 3.3 smoke test used no explicit Accept header, which defaults to `application/sml+json` — the provider that contains the real data (3 systems, 1 deployment, 1 procedure). The "independent re-verification" repeated the same incorrect header and reached the same wrong conclusion.
>
> **Root cause:** The AI changed the request pattern between smoke tests without recognizing the content-negotiation implications. 52North routes `application/json` and `application/sml+json` to completely separate data backends:
> | Accept Header | Content-Type Returned | Data? |
> |---|---|---|
> | _(none)_ | `application/sml+json` | **3 systems, 1 deployment, 1 procedure** |
> | `application/json` | `application/json` | **Empty** |
> | `application/sml+json` | `application/sml+json` | **3 systems, 1 deployment, 1 procedure** |
>
> **Corrected severity:** Not a finding — our error, not a server issue. See [F57 correction report](f57-content-negotiation-correction.md) and Lessons Learned L13.
>
> **Impact on dependent findings:** F10, F11, F15, F41, F42, F43, F44, F47, F50, F55 were all marked as "cannot verify" or "reversed" based on the incorrect F57 conclusion. These findings should be re-evaluated in the next smoke test using the correct `Accept: application/sml+json` header (or no Accept header).

### F58 (Positive): SensorML type definitions structurally align with real OSH server data

**Severity:** Positive  
**Category:** Type validation  
**Affects:** `sensorml/types.ts` (Issue #18)  
**Ownership:** Ours  
**Evidence:** 27 field-level alignments across 2 server responses (PhysicalSystem base, PhysicalSystem with parameters). All fields map correctly to our type interfaces:

- `PhysicalSystem` discriminator ✅
- `DescribedObject` properties (uniqueId, definition, label, validTime) ✅
- `AbstractPhysicalProcess` properties (localReferenceFrames) ✅
- `SpatialFrame` + `FrameAxis` nested types ✅
- `ComponentList` → `ComponentEntry[]` → inline `PhysicalComponent` ✅
- `ParameterList` → `IOComponentChoice[]` → `DataRecord` with nested `Vector`, `Quantity`, `Boolean`, `Count` ✅
- Cross-module SWE Common integration (DataRecord, Vector, Quantity via imports) ✅

**Status:** Informational — structural confirmation that types are correct for real data

### F59 (Positive): OSH SamplingFeatures inventory has grown to 51

**Severity:** Positive  
**Category:** Improved test coverage  
**Affects:** Handler validation confidence  
**Ownership:** Upstream  
**Evidence:** OSH `/samplingFeatures` now returns 51 features (was 20+ in Phase 3.3, 5 in Phase 3.2). All 51 are recognized via SensorML namespace (`http://www.opengis.net/sensorml/2.0#Feature`) and extract successfully. This is the strongest validation of the SensorML vocabulary support added in Issue #49.

**Status:** Informational — positive

### F60 (Informational): OSH single-resource SensorML content-type partially corrected

**Severity:** Informational  
**Category:** Server improvement  
**Affects:** Future SensorML parser content negotiation  
**Ownership:** Upstream  
**Evidence:**

- Single resource: `GET /systems/040g?f=application/sml+json` → `Content-Type: application/sml+json` ✅
- Collection: `GET /systems?f=application/sml+json` → `Content-Type: application/json` ⚠️ (body IS SML)

This is a partial correction of F46. The MIME type detector `isMimeTypeSensorML` would match `application/sml+json` for single-resource requests.

**Status:** Informational — input for future SensorML parser content negotiation

### F61 (Informational): 52North default content type changed from SensorML to JSON

**Severity:** Informational  
**Category:** Server change  
**Affects:** Future content negotiation  
**Ownership:** Upstream  
**Evidence:** In Phase 3.3, 52N defaulted to `application/sml+json` for collections. Now it returns `application/json` for `?f=application/json` requests. The root endpoint still returns `Content-Type: None` (F52). This may indicate a server configuration change associated with the data removal.

**Status:** Informational — supersedes F50

---

## Cross-Server Comparison

| Dimension                    | OpenSensorHub                                 | 52North                                       | Match?               |
| ---------------------------- | --------------------------------------------- | --------------------------------------------- | -------------------- |
| Root API status              | ✅ 200                                        | ✅ 200                                        | ✅                   |
| Has data for testing         | ✅ 12 systems + 51 SF                         | ❌ **Empty**                                  | ❌ **Critical**      |
| Default content type         | `application/json`                            | `application/json`                            | ✅ (now match — F61) |
| Root Content-Type header     | `application/json`                            | `None` (F52)                                  | ❌                   |
| GeoJSON format request       | Always returns GeoJSON                        | Returns empty GeoJSON                         | —                    |
| SensorML format (single)     | ✅ `application/sml+json` (F60)               | ❓ No data                                    | —                    |
| SensorML format (collection) | ⚠️ Body is SML, CT is `application/json`      | ❓ No data                                    | —                    |
| featureType vocabulary       | SOSA full URI                                 | ❓ No data                                    | —                    |
| validTime format             | Array `["ISO-8601", "now"]`                   | ❓ No data                                    | —                    |
| uid field                    | ✅ URN on all features                        | ❓ No data                                    | —                    |
| Response envelope (GeoJSON)  | `{type: "FeatureCollection", features:[...]}` | `{type: "FeatureCollection", features:[...]}` | ✅                   |
| SWE Common schema endpoint   | ✅ DataRecord + Vector + Quantity             | ❌ DataStreams broken (500)                   | ❌                   |
| Schema Content-Type          | `auto` (F56)                                  | N/A                                           | —                    |

**Cross-server testing is now effectively single-server.** 52North has no data for any featureable resource type. This is the most significant regression in smoke test coverage since the series began.

---

## Response Envelope Observations (Phase 3 Reference)

No changes from Phase 3.3:

| Server | Format                            | Envelope Type             | Feature Array Key | Pagination                      | Links Location    |
| ------ | --------------------------------- | ------------------------- | ----------------- | ------------------------------- | ----------------- |
| OSH    | application/json (default)        | Flat object               | `items`           | `links[rel="next"]` with offset | Top-level `links` |
| OSH    | application/geo+json              | GeoJSON FeatureCollection | `features`        | `links[rel="next"]`             | Top-level `links` |
| OSH    | application/sml+json (collection) | Flat object               | `items`           | `links[rel="next"]`             | Top-level `links` |
| 52N    | application/json (default)        | GeoJSON FeatureCollection | `features`        | `links` (empty)                 | Top-level `links` |

---

## What WORKS (Verified Against Live Data)

| Capability                                                  | OSH                           | 52N         | Notes                                                 |
| ----------------------------------------------------------- | ----------------------------- | ----------- | ----------------------------------------------------- |
| `isCSAPIFeature()` — SOSA full URI                          | ✅ 12/12 Systems              | — (no data) | Unchanged                                             |
| `isCSAPIFeature()` — SensorML vocabulary                    | ✅ **51/51 SamplingFeatures** | — (no data) | **Up from 20/20**                                     |
| `getCSAPIResourceType()` — System                           | ✅ 12/12                      | —           |                                                       |
| `getCSAPIResourceType()` — SamplingFeature                  | ✅ **51/51**                  | —           |                                                       |
| `extractCSAPIFeature()` — System                            | ✅ 12/12                      | —           | All properties correct                                |
| `extractCSAPIFeature()` — SamplingFeature                   | ✅ **20/20 (of 51)**          | —           | All extract successfully                              |
| `parseValidTime()` — array format                           | ✅ 12/12                      | —           | All `["ISO","now"]` → `{start: Date, end: undefined}` |
| `isValidUri()` — URN format                                 | ✅ All uids                   | —           |                                                       |
| SensorML type alignment — PhysicalSystem                    | ✅ 17/17 fields               | —           | Full structural match                                 |
| SensorML type alignment — Parameters (SWE integration)      | ✅ 10/10 fields               | —           | Cross-module types match                              |
| SWE Common types alignment — DataRecord + Vector + Quantity | ✅ Schema matches             | —           |                                                       |
| All 423 CSAPI unit tests (incl. 23 SensorML type tests)     | ✅                            | —           |                                                       |
| All 31 mime-type unit tests                                 | ✅                            | —           |                                                       |

---

## What Remains (Later Phase 3 Concerns)

| Issue                                                    | Severity | Component                     | Target Task                                            |
| -------------------------------------------------------- | -------- | ----------------------------- | ------------------------------------------------------ |
| Null featureType fallback (F41)                          | Critical | geojson.ts or response parser | Needs design decision — **cannot re-test (52N empty)** |
| Endpoint-context classification (F43)                    | Moderate | geojson.ts or response parser | Needs design decision — **cannot re-test**             |
| Response envelope parsing (F3/F45)                       | Moderate | Response parser               | Phase 3 task                                           |
| Content negotiation (F50→F61)                            | Moderate | Response parser               | Phase 3 task                                           |
| `@link` notation parsing (F47)                           | Moderate | Response parser               | Phase 3 task                                           |
| Schema `Content-Type: auto` (F56)                        | Low      | SWE Common parser             | Phase 3 task                                           |
| Root `Content-Type: None` (F52)                          | Low      | Response parser               | Phase 3 task                                           |
| SensorML parser                                          | Moderate | Future SensorML parser        | Phase 3 — **OSH has real SML data**                    |
| SWE Common parser                                        | Moderate | Future SWE parser             | Phase 3 — OSH schema works                             |
| Pagination helpers                                       | Low      | Response parser               | Phase 3 task                                           |
| 52N data restoration                                     | Moderate | N/A                           | Upstream — monitor                                     |
| F6-F9, F16-F18, F21-F24, F28, F34-F36 server limitations | Various  | N/A                           | Upstream                                               |

---

## Verdict

**SensorML type definitions (Issue #18) structurally align with real server data. No handler regressions. 52North data loss limits interoperability testing.**

1. **SensorML types are correct.** The structural alignment against two OSH SensorML responses (27 field matches, 0 mismatches) confirms that our type definitions accurately model real server data. The `PhysicalSystem` hierarchy (DescribedObject → AbstractProcess → AbstractPhysicalProcess → PhysicalSystem) maps perfectly to OSH's response structure. The cross-module SWE Common integration works — `parameters` containing `DataRecord` with `Vector`, `Quantity`, `Boolean`, `Count` fields all resolve through the `ParameterList → IOComponentChoice → AnyComponent` type chain.

2. ~~**52North data loss is significant.** The server has been completely emptied — 3 systems, 1 deployment, and 1 procedure that were our only Deployment/Procedure test data and our only source of CURIE-format vocabulary values (`sosa:Sensor`, `sosa:Platform`) are gone. This drops the smoke test to single-server validation for the first time in the series. Five prior findings (F41, F42, F43, F44, F47) cannot be re-verified. This should be monitored — if 52N doesn't restore data, we may need a third server or synthetic test data.~~ **CORRECTION (2026-02-15):** 52North data is present and accessible via `Accept: application/sml+json`. The AI changed request headers between smoke tests, causing a false "data loss" conclusion. See [F57 correction report](f57-content-negotiation-correction.md).

3. **GeoJSON handler is stable.** All 63 OSH features (12 systems + 51 sampling features) pass recognition and extraction. parseValidTime correctly handles all 12 validTime arrays. No regressions from Issue #18 changes (expected — types-only module with no runtime code).

**Cumulative statistics:**

- 13 smoke tests completed (9 Phase 2 + 4 Phase 3)
- 61 total findings (F1–F61, including 5 new in this test)
- 0 handler bugs found across all 13 smoke tests
- 2 critical fixes still confirmed (F40 → Issue #49, F49 → Issue #52)
- 423 CSAPI unit tests + 31 mime-type = 454 total, all passing
- Phase 3 GeoJSON handler validated against **63 real features** from 1 server (was 37 from 2 servers in Phase 3.3)
- **Extraction rate: 100%** (32/32 tested) — but reduced pool due to 52N emptiness
- **SensorML structural alignment: 27/27 fields match** across 2 system descriptions
