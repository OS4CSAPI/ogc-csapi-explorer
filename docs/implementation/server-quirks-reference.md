# Complete Server Quirks & Interoperability Reference

**Generated from:** 18 smoke test reports, 6 analysis documents, 19 demo-app findings, and source code review  
**Scope:** All findings F1–F90, organized by server  
**Workspace:** `ogc-client-CSAPI_2`

---

## Table of Contents

- [OpenSensorHub (OSH)](#opensensorhub-osh)
  - [Connection & Auth](#osh-connection--auth)
  - [Content Negotiation](#osh-content-negotiation)
  - [Response Envelope & Data Shape](#osh-response-envelope--data-shape)
  - [Vocabulary & featureType](#osh-vocabulary--featuretype)
  - [Data Availability](#osh-data-availability)
  - [Rejected / Broken Endpoints](#osh-rejected--broken-endpoints)
  - [Known Bugs & Limitations](#osh-known-bugs--limitations)
  - [Timestamps & validTime](#osh-timestamps--validtime)
  - [SensorML Format](#osh-sensorml-format)
  - [SWE Common Schemas](#osh-swe-common-schemas)
- [52North (52N)](#52north-52n)
  - [Connection & Auth](#52n-connection--auth)
  - [Content Negotiation](#52n-content-negotiation)
  - [Response Envelope & Data Shape](#52n-response-envelope--data-shape)
  - [Vocabulary & featureType](#52n-vocabulary--featuretype)
  - [Data Availability](#52n-data-availability)
  - [Rejected / Broken Endpoints](#52n-rejected--broken-endpoints)
  - [Known Bugs & Limitations](#52n-known-bugs--limitations)
  - [Timestamps & validTime](#52n-timestamps--validtime)
  - [SensorML Format](#52n-sensorml-format)
- [Cross-Server Differences](#cross-server-differences)
- [Findings Index (F1–F90)](#findings-index-f1f90)

---

## OpenSensorHub (OSH)

### OSH Connection & Auth

| Property                | Value                                                    |
| ----------------------- | -------------------------------------------------------- |
| **Base URL**            | `http://45.55.99.236:8080/sensorhub/api`                 |
| **Protocol**            | HTTP (no SSL/TLS)                                        |
| **Authentication**      | Basic auth required (credentials via env vars)           |
| **Root response**       | 200 OK — "Connected Systems API Service", 10 links       |
| **Conformance classes** | 33 (Parts 1–3, including create-replace-delete, pub/sub) |

### OSH Content Negotiation

**F46/F64 (CRITICAL): OSH ignores ALL Accept headers.** The server always returns `Content-Type: application/json` regardless of what Accept header is sent. Content negotiation via Accept header is completely broken, violating OGC API Common §7.8.

| Accept Header Sent     | Content-Type Returned | Body Format                  |
| ---------------------- | --------------------- | ---------------------------- |
| `application/json`     | `application/json`    | GeoJSON Feature in `{items}` |
| `application/geo+json` | `application/json`    | GeoJSON Feature in `{items}` |
| `application/sml+json` | `application/json`    | GeoJSON Feature in `{items}` |
| `application/swe+json` | `application/json`    | GeoJSON Feature in `{items}` |
| _(none)_               | `application/json`    | GeoJSON Feature in `{items}` |

**F71: OSH DOES support format selection via `?f=` query parameter:**

| `?f=` Parameter | Status | Content-Type Returned  |
| --------------- | ------ | ---------------------- |
| `?f=json`       | ✅ 200 | `application/json`     |
| `?f=geojson`    | ✅ 200 | `application/geo+json` |
| `?f=sml3`       | ✅ 200 | `application/sml+json` |
| `?f=swe`        | ❌ 400 | Bad Request            |

**F60: Single-resource SensorML content-type partially corrected.** `GET /systems/{id}?f=sml3` returns `Content-Type: application/sml+json` (correctly). Collection `?f=sml3` returns body as SML but Content-Type still says `application/json`.

**F56: OSH schema endpoint returns `Content-Type: auto`** (non-standard) for `/datastreams/{id}/schema`. Body is valid SWE Common JSON.

### OSH Response Envelope & Data Shape

**F3/F13/F45/F82: OSH always uses `{items: [...]}` envelope** — NOT standard GeoJSON FeatureCollection.

| Format                       | Envelope                                         | Items Key  | Links                           | Notes            |
| ---------------------------- | ------------------------------------------------ | ---------- | ------------------------------- | ---------------- |
| `application/json` (default) | `{ items: [...], links: [...] }`                 | `items`    | Sometimes absent entirely (F82) | Non-standard     |
| `?f=geojson`                 | `{ type: "FeatureCollection", features: [...] }` | `features` | Present                         | Standard GeoJSON |
| `?f=sml3` (collection)       | `{ items: [...] }`                               | `items`    | Present                         | Non-standard     |
| `?f=sml3` (single resource)  | Unwrapped SML object                             | N/A        | N/A                             | No envelope      |

- **F82:** OSH items envelope sometimes has **no `links` key at all** (not even empty array). `parseCollectionResponse` must default to `[]`.
- **F5:** No `numberMatched`, `numberReturned`, or `timeStamp` in any response. Only link-based pagination via `links[rel="next"]` with offset parameter.
- **F48:** No per-feature links on any features — always `links: []` or absent.
- **F39:** Commands also use `{items: [...]}` envelope.

**`@` notation cross-references observed on OSH:**

- `system@id`, `system@link` (on datastreams)
- `datastream@id` (on observations)
- `controlstream@id` (on commands)
- `command@id` (on command results)
- `foi@id` (on observations — F27)

### OSH Vocabulary & featureType

All OSH featureType values use **full URIs** (not CURIEs):

| Endpoint          | featureType Value                             | Handler Classification | Count (latest) |
| ----------------- | --------------------------------------------- | ---------------------- | -------------- |
| /systems          | `http://www.w3.org/ns/sosa/Sensor`            | System ✅              | 12             |
| /systems          | `http://www.w3.org/ns/sosa/Platform`          | System ✅              | 21             |
| /deployments      | `http://www.w3.org/ns/sosa/Deployment`        | Deployment ✅          | 15             |
| /deployments      | `http://www.w3.org/ns/ssn/Deployment`         | **null** ⚠️ (F83)      | 1              |
| /procedures       | `http://www.w3.org/ns/sosa/Procedure`         | Procedure ✅           | 15             |
| /samplingFeatures | `http://www.opengis.net/sensorml/2.0#Feature` | SamplingFeature ✅     | 51             |
| /samplingFeatures | `http://www.w3.org/ns/sosa/Sample`            | SamplingFeature ✅     | 15             |

- **F40 (FIXED by Issue #49):** OSH SamplingFeatures use `http://www.opengis.net/sensorml/2.0#Feature` — SensorML namespace, not SOSA. Handler extended to support this.
- **F83 (LOW):** One deployment uses SSN namespace (`http://www.w3.org/ns/ssn/Deployment`) instead of SOSA. `getCSAPIResourceType` returns `null`. Mitigated by `classifyFeature` endpoint hint fallback.
- **F90 (POSITIVE):** As of Phase 3.16, OSH has all 5 SOSA resource types represented: Sensor, Platform, Deployment, Procedure, Sample.

### OSH Data Availability

| Resource Type    | Endpoint            | Count (latest) | Data?                           |
| ---------------- | ------------------- | -------------- | ------------------------------- |
| Systems          | `/systems`          | 33             | ✅                              |
| Deployments      | `/deployments`      | 16             | ✅ (F88 — new since Phase 3.16) |
| Procedures       | `/procedures`       | 15             | ✅ (F88 — new since Phase 3.16) |
| SamplingFeatures | `/samplingFeatures` | 66             | ✅                              |
| DataStreams      | `/datastreams`      | 100            | ✅                              |
| Observations     | `/observations`     | 100            | ✅                              |
| ControlStreams   | `/controlstreams`   | 8              | ✅                              |
| Commands         | nested only         | Yes            | ✅ (under controlstreams)       |
| Properties       | `/properties`       | 0              | ❌ Empty                        |

- **F53/F59:** OSH data inventory has grown over the smoke test series (systems 5→12→33, SF 5→20→51→66, deployments 0→16, procedures 0→15).
- **F14:** Properties not discoverable via links on either server.
- **F34 (CRITICAL):** OSH has **no top-level `/commands` endpoint** — commands only accessible nested under `/controlstreams/{id}/commands`.

### OSH Rejected / Broken Endpoints

OSH returns **400 Bad Request** for many nested association/sub-resource endpoints:

| Finding | Endpoint                            | Status          |
| ------- | ----------------------------------- | --------------- |
| **F6**  | `systems/{id}/deployments`          | 400 rejected    |
| **F7**  | `systems/{id}/procedures`           | 400 rejected    |
| **F8**  | `samplingFeatures/{id}/systems`     | 400 rejected    |
| **F9**  | `samplingFeatures/{id}/history`     | 400 rejected    |
| **F16** | `datastreams/{id}/systems`          | 400 rejected    |
| **F17** | `datastreams/{id}/procedures`       | 400 rejected    |
| **F18** | `datastreams/{id}/history`          | 400 rejected    |
| **F21** | `observations/{id}/datastream`      | 400 rejected    |
| **F22** | `observations/{id}/samplingFeature` | 400 rejected    |
| **F23** | `observations/{id}/system`          | 400 rejected    |
| **F24** | `observations/{id}/history`         | 400 rejected    |
| **F28** | `controlstreams/{id}/feasibility`   | 400 rejected    |
| **F35** | `/commands/{id}/cancel`             | Not implemented |

### OSH Known Bugs & Limitations

| Finding                 | Description                                                                                                  | Severity                                     |
| ----------------------- | ------------------------------------------------------------------------------------------------------------ | -------------------------------------------- |
| **F1**                  | Link relation prefix mismatch — server uses plain rel names, not `ogc-cs:` prefix                            | ✅ FIXED (Issue #34)                         |
| **F2**                  | Top-level vs. collection-scoped URLs — resources at `/api/systems` not `/collections/.../systems`            | ✅ FIXED (Issue #35)                         |
| **F34**                 | No top-level `/commands` endpoint — only nested under controlstreams                                         | CRITICAL                                     |
| **F36**                 | `id` query parameter filter ignored on commands                                                              | Server limitation                            |
| **F46/F64**             | Ignores ALL Accept headers — only `?f=` query param works                                                    | Server limitation                            |
| **F49**                 | SamplingFeatures lack spec-required `sampledFeature@link` property                                           | ✅ RESOLVED (Issue #52 — validators removed) |
| **F56**                 | Schema endpoint returns `Content-Type: auto` (non-standard)                                                  | Low                                          |
| **F82**                 | Items envelope sometimes has no `links` key at all                                                           | Low                                          |
| **F83**                 | SSN namespace (`ssn/Deployment`) not recognized — needs `toSsnLocalName`                                     | Low                                          |
| **F85**                 | Deployments have no `validTime` (absent) — `validTime!` assertion risk                                       | Low                                          |
| **Demo F-17/Issue #20** | `buildResourceUrl()` uses camelCase `controlStreams` in fallback path — should be lowercase `controlstreams` | Bug in library                               |

**Link discovery conventions (from F1/F2 fix):**
OSH root document uses Convention 2 (plain rel names): `{ "rel": "systems", "href": "http://.../api/systems" }`. Collection documents use Convention 3 (`rel: "items"` with resource type in href). Convention 1 (`ogc-cs:` prefix) is not used by OSH. The `scanCsapiLinks()` function now supports all 3 conventions.

### OSH Timestamps & validTime

- **F4:** `validTime` is an **array format**: `["2026-01-26T18:32:01.56Z", "now"]`. ✅ Handled by `parseValidTime()`.
- The `"now"` sentinel maps to `end: undefined`.
- All 12+ systems have validTime in this format.
- SamplingFeatures have **no validTime**.
- Deployments have **no validTime** (absent from properties — F85).
- **F19/F25:** `resultTime=latest` query parameter accepted and returns real observation data.

### OSH SensorML Format

Accessible via `?f=sml3` query parameter (NOT via Accept header — F64/F71).

- **F58/F68:** All 12 OSH systems return `type: "PhysicalSystem"` with `definition: "http://www.w3.org/ns/sosa/Sensor"` (full URI).
- OSH SML data is **minimal**: `{type, id, uniqueId, definition, label, validTime}` — no identifiers, classifiers, documents, or position.
- Some systems have `localReferenceFrames` and `components` (array of `PhysicalComponent`).
- Some systems have `parameters` (array of `DataRecord` with nested Vector, Quantity, Boolean, Count).
- 27/27 field-level type alignments confirmed against our SensorML type definitions (F58).

### OSH SWE Common Schemas

- **F75/F89:** OSH provides rich SWE Common test data via datastream and control stream schemas.
- Schema endpoint: `/datastreams/{id}/schema` → `resultSchema: { type: "DataRecord", ... }`
- Control stream: `/controlstreams/{id}/schema` → `parametersSchema: { type: "DataRecord", ... }`

| SWE Type   | Where Found                        | Count |
| ---------- | ---------------------------------- | ----- |
| DataRecord | All schemas                        | 13+   |
| Vector     | Location, Acceleration, Control    | 5     |
| Quantity   | Temperature, Location coords, etc. | 22+   |
| Text       | StatusEvent                        | 3     |
| Boolean    | Control streams                    | 5     |
| Count      | Control streams                    | 2     |

- `uom` appears in both `{href: ...}` and `{code: ...}` forms.
- **F81:** SWE+JSON observations use implicit JSONEncoding — no explicit `encoding` property in payload.
- **F74 (RESOLVED by Issue #27):** Vector type now handled by `parseVector`.

---

## 52North (52N)

### 52N Connection & Auth

| Property                                                                  | Value                                                            |
| ------------------------------------------------------------------------- | ---------------------------------------------------------------- |
| **Base URL**                                                              | `https://csa.demo.52north.org/`                                  |
| **Protocol**                                                              | HTTPS with **expired SSL certificate**                           |
| **Authentication**                                                        | None required                                                    |
| **SSL workaround**                                                        | Requires `-SkipCertificateCheck` (PowerShell) or equivalent      |
| **Root response**                                                         | 200 OK — "connected-systems-pygeoapi", 7 links                   |
| **Conformance classes**                                                   | 1 only: `ogcapi-common-1/1.0/conf/core` (F3 from 52N smoke test) |
| **F52:** Root endpoint returns `Content-Type: None` (non-standard header) |

### 52N Content Negotiation

**F57 (CORRECTED/RETRACTED): 52North has a dual-backend architecture.** The Accept header routes to completely separate data providers:

| Accept Header          | Content-Type Returned  | Has Data?                      | Envelope                                         |
| ---------------------- | ---------------------- | ------------------------------ | ------------------------------------------------ |
| _(none)_               | `application/sml+json` | **YES** (3 sys, 1 dep, 1 proc) | `{ items: [...] }`                               |
| `application/sml+json` | `application/sml+json` | **YES**                        | `{ items: [...] }`                               |
| `application/geo+json` | `application/geo+json` | **YES** (F62)                  | `{ type: "FeatureCollection", features: [...] }` |
| `application/json`     | `application/json`     | **EMPTY**                      | `{ type: "FeatureCollection", features: [] }`    |

- **F50:** Default content type (no Accept header) is `application/sml+json`.
- **F62:** `Accept: application/geo+json` is a THIRD working format — returns populated GeoJSON FeatureCollection.
- **F57 (RETRACTED):** "52N data loss" was a false finding — the AI changed request headers between smoke tests without recognizing the content-negotiation implications. Data was never lost. This is Lesson L13.
- **F72:** Individual system via `Accept: application/json` returns 500 (but collection returns empty 200).

### 52N Response Envelope & Data Shape

| Format                 | Envelope                                                       | Items Key  | Links                |
| ---------------------- | -------------------------------------------------------------- | ---------- | -------------------- |
| `application/sml+json` | `{ items: [...], links: [...] }`                               | `items`    | Present (empty `[]`) |
| `application/geo+json` | `{ type: "FeatureCollection", features: [...], links: [...] }` | `features` | Present (empty `[]`) |
| `application/json`     | `{ type: "FeatureCollection", features: [...], links: [...] }` | `features` | Present (empty `[]`) |

- 52N always includes an explicit `links: []` (unlike OSH which sometimes omits it — F82).
- No `numberMatched`, `numberReturned`, or `timeStamp` in any response (F5).

**`@link` notation (F47):**

- `systemKind@link: { rel: "ogc-rel:procedures", href: "...", urn: "..." }`
- `platform@link: { href: "urn:platform:5300-909" }`
- `deployedSystems@link: [{ name: "...", system: { href: "...", urn: "..." } }]`

**F70:** `parseLink` correctly strips extra `urn` property from 52N links, preserving only standard OGC link properties.

### 52N Vocabulary & featureType

52N uses a **mix of CURIE and full URI forms** (F44):

| Endpoint               | featureType Value                      | Form     | Handler Classification                                  |
| ---------------------- | -------------------------------------- | -------- | ------------------------------------------------------- |
| /systems (GeoJSON)     | `null`                                 | N/A      | **null** ⚠️ (F41) — mitigated by `classifyFeature` hint |
| /deployments (GeoJSON) | `http://www.w3.org/ns/sosa/Deployment` | Full URI | Deployment ✅ (F78)                                     |
| /procedures (GeoJSON)  | `sosa:Sensor`                          | CURIE    | **System** ⚠️ (F43/F84 — misclassified)                 |

SensorML `definition` values:

- Systems: `sosa:Sensor` (CURIE), `sosa:Platform` (CURIE)
- Deployments: `http://www.w3.org/ns/sosa/Deployment` (full URI)
- Procedures: `sosa:Sensor` (CURIE)

- **F41 (CRITICAL, MITIGATED by Issue #50):** All 3 52N systems have `featureType: null` in GeoJSON format. The data exists in SensorML format (`definition: "sosa:Sensor"`). `classifyFeature` with endpoint URL hint correctly classifies them.
- **F43/F84 (MEDIUM):** 52N procedure has `featureType: "sosa:Sensor"` — classified as System, not Procedure. This is by design (System priority > Procedure in our classificatio). Endpoint hint **cannot override** because `getCSAPIResourceType` returns non-null.
- **F44:** Handler's `toSosaLocalName()` correctly handles both CURIE and full URI forms.

### 52N Data Availability

| Resource Type    | Endpoint            | Count | Status                                            |
| ---------------- | ------------------- | ----- | ------------------------------------------------- |
| Systems          | `/systems`          | 3     | ✅ 200 (via sml+json or geo+json)                 |
| Deployments      | `/deployments`      | 1     | ✅ 200                                            |
| Procedures       | `/procedures`       | 1     | ✅ 200                                            |
| SamplingFeatures | `/samplingFeatures` | 0     | ✅ 200 empty (F51 fixed; F86: 400 for sml+json)   |
| DataStreams      | `/datastreams`      | —     | ❌ 500 json / 400 geo+json,sml+json (F20/F76/F87) |
| Observations     | `/observations`     | —     | ❌ 500 (F26)                                      |
| ControlStreams   | `/controlstreams`   | —     | ❌ 404 (F32)                                      |
| Properties       | `/properties`       | 0     | ✅ 200 empty                                      |

- 52N is the **only server** providing Deployment and Procedure data.
- 52N Part 2 resources (datastreams, observations, controlstreams) are completely broken/missing.
- **F2 (from 52N smoke test):** 52N used `featuresOfInterest` instead of `samplingFeatures` (old alias). Now uses `samplingFeatures` (F51).

### 52N Rejected / Broken Endpoints

| Finding         | Endpoint                                                | Status                                | Notes                                      |
| --------------- | ------------------------------------------------------- | ------------------------------------- | ------------------------------------------ |
| **F20/F76/F87** | `/datastreams`                                          | 500 (json) / 400 (geo+json, sml+json) | Endpoint completely broken                 |
| **F26**         | `/observations`                                         | 500                                   | Completely broken                          |
| **F32**         | `/controlstreams`                                       | 404                                   | Not implemented                            |
| **F72**         | `/systems/{id}` with `Accept: application/json`         | 500                                   | Individual resource broken for json format |
| **F86**         | `/samplingFeatures` with `Accept: application/sml+json` | 400                                   | SML format regressed for SF                |

### 52N Known Bugs & Limitations

| Finding     | Description                                                                       | Severity                                      |
| ----------- | --------------------------------------------------------------------------------- | --------------------------------------------- |
| **F41**     | Systems have `featureType: null` in GeoJSON — invisible to GeoJSON handler        | CRITICAL (mitigated by Issue #50)             |
| **F42**     | Deployment has `validTime: null` — spec requires it for deployments               | Moderate (no longer blocking after Issue #52) |
| **F43/F84** | Procedure typed as `sosa:Sensor` — classified as System, not Procedure            | Medium                                        |
| **F52**     | Root endpoint returns `Content-Type: None`                                        | Informational                                 |
| **F65**     | SML uses non-standard `type: "Deployment"` — not a standard SensorML process type | Informational                                 |
| **F72**     | Individual system via `application/json` returns 500                              | Low                                           |
| **F86**     | `/samplingFeatures` SML endpoint regressed (200 → 400)                            | Server limitation                             |
| **52N-F1**  | Query params embedded in collection hrefs (`?f=application/json`)                 | Informational                                 |
| **52N-F4**  | Mixed leading-slash in collection hrefs                                           | Low                                           |
| **52N-F6**  | Localhost leak in collections outer links                                         | Low                                           |
| **52N-F3**  | No CSAPI conformance classes (only OGC Common core)                               | Informational                                 |

**Link discovery:** 52N root document uses none of the 3 conventions recognized by `scanCsapiLinks()` — yields 0 discovered resource types. The `resourceUrls` constructor parameter provides a workaround (demo-app issue #14).

### 52N Timestamps & validTime

- **F42:** All 52N features have `validTime: null` (systems, deployment, procedure).
- `parseValidTime(null)` correctly returns `undefined`.
- **F85:** `extractCSAPIFeature` Deployment case uses `validTime!` non-null assertion — creates `validTime: undefined` violating type contract. Latent issue.

### 52N SensorML Format

Accessible via `Accept: application/sml+json` header (correct content negotiation).

- 3 systems: all `type: "PhysicalSystem"`, definitions `sosa:Sensor` (2) and `sosa:Platform` (1)
- 1 deployment: `type: "Deployment"` (non-standard SensorML type — F65)
- 1 procedure: `type: "PhysicalSystem"`, `definition: "sosa:Sensor"`, `procedureType: "sosa:Sensor"` (F43)

52N SML data is **richer** than OSH:

- Includes `identifiers` (SerialNo, ProdNo), `classifiers` (SensorType, intendedApplication)
- Includes `documents` (Operating Manual links)
- Includes `typeOf` links with non-standard `urn` property (F70)
- Includes `procedureType` field
- Deployment has `contacts`, `location` (GeoJSON Point), `platform`, `deployedSystems`

No SWE Common data available from 52N — datastreams endpoint broken (F20).

---

## Cross-Server Differences

| Dimension                     | OpenSensorHub                                | 52North                                          |
| ----------------------------- | -------------------------------------------- | ------------------------------------------------ |
| **Protocol**                  | HTTP (no SSL)                                | HTTPS (expired cert)                             |
| **Auth**                      | Basic auth required                          | None                                             |
| **Content negotiation**       | ❌ Ignores Accept; use `?f=` param           | ✅ Accept header routes to backends              |
| **Default content type**      | `application/json`                           | `application/sml+json`                           |
| **GeoJSON envelope**          | `{ items: [...] }` (non-standard)            | `{ type: "FeatureCollection", features: [...] }` |
| **SML envelope**              | `{ items: [...] }` (via `?f=sml3`)           | `{ items: [...] }`                               |
| **featureType form**          | Full URIs always                             | Mixed CURIE + full URI                           |
| **featureType on systems**    | `sosa/Sensor`, `sosa/Platform`               | `null` in GeoJSON                                |
| **validTime format**          | Array `["ISO-8601", "now"]`                  | `null` always                                    |
| **SML data richness**         | Minimal (type, id, uid, label, validTime)    | Rich (identifiers, classifiers, docs, typeOf)    |
| **SML access method**         | `?f=sml3` query param                        | `Accept: application/sml+json` header            |
| **SWE Common**                | ✅ Rich (13+ schemas, observations)          | ❌ Datastreams broken                            |
| **Part 2 resources**          | ✅ Datastreams, observations, controlstreams | ❌ All broken/missing                            |
| **Deployment/Procedure data** | ✅ (since Phase 3.16)                        | ✅ (1 each)                                      |
| **SamplingFeatures**          | 66 (SOSA + SensorML vocab)                   | 0 (empty)                                        |
| **Links in collection**       | Sometimes absent                             | Always `[]`                                      |
| **Sub-resource endpoints**    | Mostly 400 rejected                          | N/A (not tested)                                 |
| **Conformance classes**       | 33                                           | 1                                                |

---

## Findings Index (F1–F90)

### Resolved / Fixed (11)

| ID      | Description                                              | Resolution                                            |
| ------- | -------------------------------------------------------- | ----------------------------------------------------- |
| **F1**  | Link relation prefix mismatch (OSH uses plain rel names) | ✅ Fixed by Issue #34                                 |
| **F2**  | Top-level vs. collection-scoped URLs                     | ✅ Fixed by Issue #35                                 |
| **F3**  | Response envelope uses `items` vs `features`             | ✅ Addressed by Issue #36 (`parseCollectionResponse`) |
| **F4**  | `validTime` is an array `["ISO","now"]`                  | ✅ Addressed by `parseValidTime()`                    |
| **F40** | OSH SF use non-SOSA vocabulary (`sensorml/2.0#Feature`)  | ✅ Fixed by Issue #49                                 |
| **F49** | OSH SF lack `sampledFeature@link` — blocks extraction    | ✅ Resolved by Issue #52 (validators removed)         |
| **F54** | F49 confirmed resolved                                   | ✅ 51/51 SF extract                                   |
| **F55** | F42 no longer blocking extraction                        | ✅ Validators removed                                 |
| **F69** | `instanceof SensorMLParseError` fails cross-module       | ✅ Resolved by Issue #53 (shared module)              |
| **F74** | SWE Common Vector type not handled                       | ✅ Resolved by Issue #27 (`parseVector`)              |
| **F80** | F74 resolved confirmation                                | ✅                                                    |

### Retracted (1)

| ID      | Description                 | Reason                                               |
| ------- | --------------------------- | ---------------------------------------------------- |
| **F57** | ~~52N server data removed~~ | ❌ RETRACTED — AI error in content negotiation (L13) |

### Server Limitations — Active (20)

| ID      | Server | Description                                                  |
| ------- | ------ | ------------------------------------------------------------ |
| **F6**  | OSH    | Rejects `systems/{id}/deployments` (400)                     |
| **F7**  | OSH    | Rejects `systems/{id}/procedures` (400)                      |
| **F8**  | OSH    | Rejects `samplingFeatures/{id}/systems` (400)                |
| **F9**  | OSH    | Rejects `samplingFeatures/{id}/history` (400)                |
| **F16** | OSH    | Rejects `datastreams/{id}/systems` (400)                     |
| **F17** | OSH    | Rejects `datastreams/{id}/procedures` (400)                  |
| **F18** | OSH    | Rejects `datastreams/{id}/history` (400)                     |
| **F20** | 52N    | `/datastreams` broken (500 json, 400 others)                 |
| **F21** | OSH    | Rejects `observations/{id}/datastream` (400)                 |
| **F22** | OSH    | Rejects `observations/{id}/samplingFeature` (400)            |
| **F23** | OSH    | Rejects `observations/{id}/system` (400)                     |
| **F24** | OSH    | Rejects `observations/{id}/history` (400)                    |
| **F26** | 52N    | `/observations` broken (500)                                 |
| **F28** | OSH    | Rejects `controlstreams/{id}/feasibility` (400)              |
| **F32** | 52N    | `/controlstreams` not implemented (404)                      |
| **F34** | OSH    | No top-level `/commands` endpoint                            |
| **F35** | OSH    | `/commands/{id}/cancel` not implemented                      |
| **F36** | OSH    | Ignores `id` query parameter on commands                     |
| **F46** | OSH    | Ignores SML Accept header (superseded by F64, use `?f=sml3`) |
| **F72** | 52N    | Individual system via `application/json` → 500               |

### Deferred / Still Open (8)

| ID      | Description                                                    | Status                            |
| ------- | -------------------------------------------------------------- | --------------------------------- |
| **F5**  | Missing pagination metadata (`numberMatched`/`numberReturned`) | ⏳ Deferred                       |
| **F14** | Properties not discoverable via links                          | ⏳ Deferred                       |
| **F27** | Observation `foi@id` naming variation                          | ⏳ Deferred                       |
| **F30** | ControlStream `system@link` cross-reference                    | ⏳ Deferred                       |
| **F31** | Command entity data shape                                      | ⏳ Deferred                       |
| **F33** | ControlStream schema returns SWE DataRecord                    | ⏳ Deferred                       |
| **F38** | Command status data shape                                      | ⏳ Deferred                       |
| **F41** | 52N systems `featureType: null` in GeoJSON                     | ⚠️ Mitigated (Issue #50 fallback) |

### Informational / Confirmed Stable (37)

| ID      | Description                                                           | Server |
| ------- | --------------------------------------------------------------------- | ------ |
| **F10** | 52N has real data (3 sys, 1 dep, 1 proc)                              | 52N    |
| **F11** | 52N uses SensorML as default format                                   | 52N    |
| **F12** | 52N `systems/{id}/deployments` works (untested)                       | 52N    |
| **F13** | Envelope varies by server AND format                                  | Both   |
| **F15** | 52N has 3 systems                                                     | 52N    |
| **F19** | `resultTime=latest` accepted by OSH                                   | OSH    |
| **F25** | `resultTime=latest` returns real data                                 | OSH    |
| **F29** | ControlStream schema works on OSH                                     | OSH    |
| **F37** | Command `/result` 404 for result-less types (expected)                | OSH    |
| **F39** | Commands use `items` envelope                                         | OSH    |
| **F42** | 52N Deployment has `validTime: null`                                  | 52N    |
| **F43** | 52N Procedure misclassified as System                                 | 52N    |
| **F44** | 52N uses both CURIE and full URI forms                                | 52N    |
| **F45** | Response envelope varies by server AND format                         | Both   |
| **F47** | 52N GeoJSON includes `@link` notation                                 | 52N    |
| **F48** | OSH features have empty links arrays                                  | OSH    |
| **F50** | 52N default content type is `application/sml+json`                    | 52N    |
| **F51** | 52N `/samplingFeatures` endpoint functional (empty)                   | 52N    |
| **F52** | 52N returns `Content-Type: None` on root                              | 52N    |
| **F53** | OSH data inventory has grown significantly                            | OSH    |
| **F56** | OSH schema returns `Content-Type: auto`                               | OSH    |
| **F58** | SensorML types align with real OSH data (27/27 fields)                | OSH    |
| **F59** | OSH SamplingFeatures at 66                                            | OSH    |
| **F60** | OSH single-resource SML CT partially corrected (superseded by F71)    | OSH    |
| **F61** | Superseded (was based on F57 misunderstanding)                        | 52N    |
| **F62** | 52N `application/geo+json` returns data                               | 52N    |
| **F63** | 52N error codes changed 500→400 on some endpoints                     | 52N    |
| **F64** | OSH ignores ALL Accept headers                                        | OSH    |
| **F65** | 52N SML uses non-standard `type: "Deployment"`                        | 52N    |
| **F71** | OSH serves SML via `?f=sml3` parameter                                | OSH    |
| **F75** | OSH provides rich SWE Common test data                                | OSH    |
| **F76** | 52N `/datastreams` degraded 400→500                                   | 52N    |
| **F77** | 52N `/samplingFeatures` now returns empty collection (previously 400) | 52N    |
| **F81** | SWE+JSON observations use implicit JSONEncoding                       | OSH    |
| **F82** | OSH items envelope sometimes has no `links` key                       | OSH    |
| **F86** | 52N SF SML endpoint regressed (200→400)                               | 52N    |
| **F87** | 52N datastreams error codes partially improved                        | 52N    |

### Positive / Validation Findings (13)

| ID      | Description                                          | Server |
| ------- | ---------------------------------------------------- | ------ |
| **F44** | Both CURIE and full URI forms handled correctly      | 52N    |
| **F53** | OSH data inventory growth                            | OSH    |
| **F58** | SensorML type definitions align 27/27 fields         | OSH    |
| **F59** | OSH SF count at 66                                   | OSH    |
| **F66** | SimpleProcess parser validated against live patterns | Both   |
| **F67** | PhysicalSystem parser validated (52N — rich data)    | 52N    |
| **F68** | PhysicalSystem parser handles minimal OSH SML        | OSH    |
| **F70** | `parseLink` correctly strips extra `urn` property    | 52N    |
| **F73** | AggregateProcess rejects correctly                   | Both   |
| **F78** | 52N deployments return valid featureType in GeoJSON  | 52N    |
| **F79** | `parseCollectionResponse` validated against 6 shapes | Both   |
| **F88** | OSH deployments and procedures now populated         | OSH    |
| **F89** | SWE Common schemas match parser types                | OSH    |
| **F90** | Full SOSA vocabulary represented on OSH              | OSH    |

### New / Low-Priority (5)

| ID      | Description                                             | Severity          |
| ------- | ------------------------------------------------------- | ----------------- |
| **F83** | SSN namespace (`ssn/Deployment`) not recognized         | Low               |
| **F84** | 52N procedure featureType misclassification (by design) | Medium            |
| **F85** | Deployment `validTime!` non-null assertion risk         | Low               |
| **F86** | 52N SF SML endpoint regressed                           | Server limitation |
| **F87** | 52N datastreams error code change                       | Informational     |

---

_Total findings tracked: **90** (F1–F90) across 18 smoke tests spanning Phase 2.1 through Phase 3.16._
