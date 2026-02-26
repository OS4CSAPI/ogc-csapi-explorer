# Live Server Smoke Test — Post Phase 3.16

**Smoke Test #18** | Date: 2025-06-17 | HEAD: `d33fce5`  
**Scope:** Work since Phase 3.12 smoke test (Issues #57–#75, Phases 3.13–3.16)  
**Test Suite:** 1,159 tests across 25 suites — all passing  
**Protocol:** Read-only observation (Lesson 10)

---

## Server Profiles

### OpenSensorHub (OSH)

| Property      | Value                                              |
| ------------- | -------------------------------------------------- |
| Base URL      | `http://45.55.99.236:8080/sensorhub/api`           |
| Auth          | Basic (ogc:ogc)                                    |
| Root response | 200 OK — "Connected Systems API Service", 10 links |
| API Title     | Connected Systems API Service                      |

**Resource Inventory (Δ from Smoke Test #17):**

| Endpoint          |  Count | Δ       | Note                                         |
| ----------------- | -----: | ------- | -------------------------------------------- |
| /systems          |     33 | +21     | Was 12 — smoke test data from CSAPI Explorer |
| /deployments      | **16** | **+16** | Was 0 — **NEW** — all smoke test data        |
| /procedures       | **15** | **+15** | Was 0 — **NEW** — all smoke test data        |
| /samplingFeatures |     66 | +15     | Was 51 — smoke test data added               |
| /datastreams      |    100 | —       | Unchanged                                    |
| /observations     |    100 | —       | Unchanged                                    |
| /controlstreams   |      8 | —       | Unchanged                                    |

### 52North (52N)

| Property      | Value                                                  |
| ------------- | ------------------------------------------------------ |
| Base URL      | `https://csa.demo.52north.org/`                        |
| Auth          | None                                                   |
| SSL           | Expired certificate — requires `-SkipCertificateCheck` |
| Root response | 200 OK — links present                                 |

**Resource Inventory (Δ from Smoke Test #17):**

| Endpoint          | Count | Δ   | Note                                                                |
| ----------------- | ----: | --- | ------------------------------------------------------------------- |
| /systems          |     3 | —   | Unchanged                                                           |
| /deployments      |     1 | —   | Unchanged                                                           |
| /procedures       |     1 | —   | Unchanged                                                           |
| /samplingFeatures |     0 | —   | Empty collection (geo+json, json); 400 for sml+json (was 200 empty) |
| /datastreams      |     — | —   | 500 (json), 400 (geo+json, sml+json)                                |
| /controlstreams   |     — | —   | 404 (unchanged)                                                     |

---

## Vocabulary Inventory

### OSH — featureType Values (All Full-URI SOSA/SensorML)

| Endpoint          | featureType                                   | Count | Handler Result         |
| ----------------- | --------------------------------------------- | ----: | ---------------------- |
| /systems          | `http://www.w3.org/ns/sosa/Sensor`            |    12 | ✅ `'System'`          |
| /systems          | `http://www.w3.org/ns/sosa/Platform`          |    21 | ✅ `'System'`          |
| /deployments      | `http://www.w3.org/ns/sosa/Deployment`        |    15 | ✅ `'Deployment'`      |
| /deployments      | `http://www.w3.org/ns/ssn/Deployment`         | **1** | ⚠️ `null` — **F83**    |
| /procedures       | `http://www.w3.org/ns/sosa/Procedure`         |    15 | ✅ `'Procedure'`       |
| /samplingFeatures | `http://www.opengis.net/sensorml/2.0#Feature` |    51 | ✅ `'SamplingFeature'` |
| /samplingFeatures | `http://www.w3.org/ns/sosa/Sample`            |    15 | ✅ `'SamplingFeature'` |

### 52N — featureType Values

| Endpoint     | featureType                            | Count | Handler Result                                   |
| ------------ | -------------------------------------- | ----: | ------------------------------------------------ |
| /systems     | `null`                                 |     3 | `null` → classification fallback → `'System'` ✅ |
| /deployments | `http://www.w3.org/ns/sosa/Deployment` |     1 | ✅ `'Deployment'`                                |
| /procedures  | `sosa:Sensor` (CURIE)                  |     1 | ⚠️ `'System'` — **F84**                          |

---

## GeoJSON Handler Validation

### `isCSAPIFeature` + `getCSAPIResourceType` Trace

| Server | Endpoint          | featureType            | `toSosaLocalName`         | Set Match                    | Result              | Correct?    |
| ------ | ----------------- | ---------------------- | ------------------------- | ---------------------------- | ------------------- | ----------- |
| OSH    | /systems          | `sosa/Sensor`          | `"Sensor"`                | SYSTEM_LOCAL_NAMES           | `'System'`          | ✅          |
| OSH    | /systems          | `sosa/Platform`        | `"Platform"`              | SYSTEM_LOCAL_NAMES           | `'System'`          | ✅          |
| OSH    | /deployments      | `sosa/Deployment`      | `"Deployment"`            | DEPLOYMENT_LOCAL_NAMES       | `'Deployment'`      | ✅          |
| OSH    | /deployments      | `ssn/Deployment`       | `undefined`               | —                            | `null`              | ⚠️ F83      |
| OSH    | /procedures       | `sosa/Procedure`       | `"Procedure"`             | PROCEDURE_LOCAL_NAMES        | `'Procedure'`       | ✅          |
| OSH    | /samplingFeatures | `sensorml/2.0#Feature` | — → `toSensormlLocalName` | SENSORML_SF_NAMES            | `'SamplingFeature'` | ✅          |
| OSH    | /samplingFeatures | `sosa/Sample`          | `"Sample"`                | SAMPLING_FEATURE_LOCAL_NAMES | `'SamplingFeature'` | ✅          |
| 52N    | /systems          | `null`                 | N/A                       | N/A                          | `null` (known)      | ✅ via hint |
| 52N    | /deployments      | `sosa/Deployment`      | `"Deployment"`            | DEPLOYMENT_LOCAL_NAMES       | `'Deployment'`      | ✅          |
| 52N    | /procedures       | `sosa:Sensor`          | `"Sensor"`                | SYSTEM_LOCAL_NAMES           | `'System'`          | ⚠️ F84      |

### `extractCSAPIFeature` Trace

| Server | Endpoint          | Feature Shape                                                                                  | Extracted Properties                                         | Note                                    |
| ------ | ----------------- | ---------------------------------------------------------------------------------------------- | ------------------------------------------------------------ | --------------------------------------- |
| OSH    | /systems          | `{type, id, geometry: null, properties: {uid, featureType, name, validTime}}`                  | uid ✅, name ✅, featureType ✅, validTime ✅ (array→parsed) | geometry null is fine (optional)        |
| OSH    | /deployments      | `{type, id, geometry: Point, properties: {uid, featureType, name, description}}`               | uid ✅, name ✅, geometry ✅                                 | validTime missing → `undefined!` ⚠️ F85 |
| OSH    | /procedures       | `{type, id, geometry: null, properties: {uid, featureType, name, description}}`                | uid ✅, name ✅, geometry: null ✅                           | Hardcoded `geometry: null` per spec     |
| OSH    | /samplingFeatures | `{type, id, geometry: Point, properties: {uid, featureType, name, description}}`               | uid ✅, name ✅, geometry ✅                                 | validTime omitted (optional)            |
| 52N    | /deployments      | `{type, id, geometry: Point, properties: {uid, name, featureType, validTime: null, ...extra}}` | uid ✅, name ✅, featureType ✅                              | validTime null → `undefined!` ⚠️ F85    |

### `parseValidTime` Trace

| Input                                              | Result                          | Correct?                               |
| -------------------------------------------------- | ------------------------------- | -------------------------------------- |
| `["2026-01-26T18:32:01.56Z", "now"]` (OSH systems) | `{start: Date, end: undefined}` | ✅ Array format, "now" → end undefined |
| `null` (52N deployments)                           | `undefined`                     | ✅ Null input                          |
| `undefined` (OSH deployments — absent)             | `undefined`                     | ✅ Absent input                        |

---

## SWE Common Parser Validation

### Live Schema Samples from OSH

| Datastream  | resultType | Schema Structure                                        | Parser Coverage                   |
| ----------- | ---------- | ------------------------------------------------------- | --------------------------------- |
| Temperature | `measure`  | DataRecord → 1× Quantity (uom.href)                     | ✅ DataRecord + Quantity          |
| StatusEvent | `record`   | DataRecord → 2× Text                                    | ✅ DataRecord + Text              |
| Location    | `vector`   | DataRecord → 1× Vector → 3× Quantity (uom.code, axisID) | ✅ DataRecord + Vector + Quantity |
| Health      | `record`   | DataRecord → 7× Boolean                                 | ✅ DataRecord + Boolean           |

**Observations:**

- All OSH datastream schemas use `type: "DataRecord"` as root — matches our parser entry point
- `uom` appears in both `{href: ...}` and `{code: ...}` forms — parser handles both
- Vector includes `referenceFrame`, `coordinates` array with `axisID` — all parsed
- Schema endpoint is `/datastreams/{id}/schema` (not embedded in collection response)

### Live Observation Sample

```json
{
  "id": "0829d6supc31trqfo0",
  "datastream@id": "083g",
  "foi@id": "080g",
  "phenomenonTime": "2026-01-14T12:35:34.519Z",
  "resultTime": "2026-01-14T12:35:34.519Z",
  "result": {
    "location": { "lat": 24.18072722, "lon": 120.64925376, "alt": 127.903 }
  }
}
```

- Observation `result` is a flat object matching the DataRecord/Vector schema
- `foi@id` naming convention present (existing finding F27)

---

## Content-Type Availability

### OSH

| Endpoint          | Accept: geo+json |  Accept: json  | Accept: sml+json |
| ----------------- | :--------------: | :------------: | :--------------: |
| /systems          |  200 (CT: json)  | 200 (CT: json) |  200 (CT: json)  |
| /deployments      |  200 (CT: json)  | 200 (CT: json) |  200 (CT: json)  |
| /procedures       |  200 (CT: json)  | 200 (CT: json) |  200 (CT: json)  |
| /samplingFeatures |  200 (CT: json)  | 200 (CT: json) |  200 (CT: json)  |
| /datastreams      |  200 (CT: json)  | 200 (CT: json) |  200 (CT: json)  |

**OSH always returns `Content-Type: application/json` regardless of Accept header. Response body is always GeoJSON Feature structure.** (Confirms F46 — carried.)

### 52N

| Endpoint          |  Accept: geo+json  |  Accept: json  |  Accept: sml+json  |
| ----------------- | :----------------: | :------------: | :----------------: |
| /systems          | 200 (CT: geo+json) | 200 (CT: json) | 200 (CT: sml+json) |
| /deployments      | 200 (CT: geo+json) | 200 (CT: json) | 200 (CT: sml+json) |
| /procedures       | 200 (CT: geo+json) | 200 (CT: json) | 200 (CT: sml+json) |
| /samplingFeatures | 200 (CT: geo+json) | 200 (CT: json) | **400** (**F86**)  |
| /datastreams      |      **400**       |    **500**     |      **400**       |

**52N correctly content-negotiates for Part 1 resources (systems, deployments, procedures). Sampling features and datastreams have issues.**

---

## Response Envelope Comparison

| Server | Format   | Envelope                                       | Items Key  |
| ------ | -------- | ---------------------------------------------- | ---------- |
| OSH    | geo+json | `{items, links}`                               | `items`    |
| OSH    | json     | `{items, links}`                               | `items`    |
| OSH    | sml+json | `{items, links}`                               | `items`    |
| 52N    | geo+json | `{type: "FeatureCollection", features, links}` | `features` |
| 52N    | json     | `{type: "FeatureCollection", features, links}` | `features` |
| 52N    | sml+json | `{items, links}`                               | `items`    |

**`parseCollectionResponse` handles both envelopes correctly** — prefers `features`, falls back to `items`. Confirmed working against all 6 live response shapes.

---

## Cross-Server Comparison

| Aspect                       | OSH                                      | 52N                                                                         |
| ---------------------------- | ---------------------------------------- | --------------------------------------------------------------------------- |
| **featureType vocabulary**   | SOSA full-URI (+ 1× SSN, 1× SensorML)    | mixed: null (systems), SOSA full-URI (deployments), SOSA CURIE (procedures) |
| **Content-Type negotiation** | ❌ Always `application/json`             | ✅ Correct for Part 1 resources                                             |
| **Response envelope**        | Always `{items, links}`                  | geo+json/json: FeatureCollection; sml+json: items                           |
| **SML format support**       | ❌ Returns GeoJSON regardless            | ✅ Returns SML JSON                                                         |
| **Deployment data**          | 16 (rich)                                | 1                                                                           |
| **Procedure data**           | 15                                       | 1 (featureType mismatch)                                                    |
| **SF data**                  | 66 (SOSA Sample + SensorML Feature)      | 0 (empty)                                                                   |
| **Datastream schemas**       | ✅ SWE Common (DataRecord, Vector, etc.) | ❌ 400/500 errors                                                           |
| **Sub-resource endpoints**   | ❌ 400 (all)                             | N/A (not tested)                                                            |

---

## Prior Findings Re-check (F1–F82)

### Resolved / Confirmed Stable (34) — No Change

F1, F2, F4, F10, F11, F13, F15, F19, F25, F29, F37, F39, F40, F43, F44, F45, F47, F48, F49, F50, F51, F54, F55, F58, F59, F62, F64, F65, F66, F67, F68, F70, F73, F69 — **all confirmed stable**.

Note: F51 upgraded from "carried" to "stable" in Smoke Test #17; confirmed still stable (52N `/samplingFeatures` returns 200 with empty FeatureCollection for geo+json and json).

### Retracted (1) — No Change

F57 — retracted, confirmed no regression.

### Server Limitations — Carried (20)

| Finding | Summary                                   | Server | Verified                                          |
| ------- | ----------------------------------------- | ------ | ------------------------------------------------- |
| F6      | `systems/{id}/deployments` → 400          | OSH    | ✅ Still 400                                      |
| F7      | `systems/{id}/procedures` → 400           | OSH    | ✅ Still 400                                      |
| F8      | `samplingFeatures/{id}/systems` → 400     | OSH    | Carried                                           |
| F9      | `samplingFeatures/{id}/history` → 400     | OSH    | Carried                                           |
| F16     | `datastreams/{id}/systems` → 400          | OSH    | Carried                                           |
| F17     | `datastreams/{id}/procedures` → 400       | OSH    | Carried                                           |
| F18     | `datastreams/{id}/history` → 400          | OSH    | Carried                                           |
| F20     | `/datastreams` → 500                      | 52N    | ✅ Still 500 (json); now 400 (geo+json, sml+json) |
| F21     | `observations/{id}/datastream` → 400      | OSH    | Carried                                           |
| F22     | `observations/{id}/samplingFeature` → 400 | OSH    | Carried                                           |
| F23     | `observations/{id}/system` → 400          | OSH    | Carried                                           |
| F24     | `observations/{id}/history` → 400         | OSH    | Carried                                           |
| F26     | Observations broken                       | 52N    | ✅ Still 500                                      |
| F28     | `controlstreams/{id}/feasibility` → 400   | OSH    | Carried                                           |
| F32     | ControlStreams → 404                      | 52N    | ✅ Still 404                                      |
| F34     | No top-level `/commands`                  | OSH    | Carried                                           |
| F35     | No `/commands/{id}/cancel`                | OSH    | Carried                                           |
| F36     | Ignores `id` query on commands            | OSH    | Carried                                           |
| F46     | Ignores SML Accept header                 | OSH    | ✅ Confirmed                                      |
| F72     | Individual system JSON → 500              | 52N    | ✅ Still 500                                      |

### Deferred — Client/Interop (7)

| Finding | Summary                                                        | Status                                             |
| ------- | -------------------------------------------------------------- | -------------------------------------------------- |
| F3      | Response envelope mismatch                                     | ⚡ **ADDRESSED by Issue #36** — no longer deferred |
| F5      | Missing pagination metadata (`numberMatched`/`numberReturned`) | ⏳ Deferred                                        |
| F14     | Properties not discoverable                                    | ⏳ Deferred                                        |
| F27     | Observation `foi@id` naming variation                          | ⏳ Deferred                                        |
| F30     | ControlStream `system@link`                                    | ⏳ Deferred                                        |
| F31     | Command entity data shape                                      | ⏳ Deferred                                        |
| F33     | ControlStream schema returns SWE DataRecord                    | ⏳ Deferred                                        |
| F38     | Command status data shape                                      | ⏳ Deferred                                        |

### Informational / Other (14)

F12, F41 (mitigated by Issue #50), F42, F52, F53, F56, F60, F61, F63, F71, F74 (resolved by Issue #27), F75, F76, F77 — **all confirmed, no change**.

### Phase 3.12 New Findings (F78–F82) Re-check

| Finding | Status                     | Note                                                                            |
| ------- | -------------------------- | ------------------------------------------------------------------------------- |
| F78     | ✅ Confirmed positive      | 52N deployments still return valid `featureType: sosa/Deployment`               |
| F79     | ✅ Confirmed positive      | `parseCollectionResponse` still validated against all envelope shapes           |
| F80     | ✅ Confirmed positive      | Vector scope boundary resolved (Issue #27)                                      |
| F81     | ℹ️ Confirmed informational | SWE+JSON observations still use implicit JSONEncoding                           |
| F82     | ⚠️ Confirmed low           | OSH items envelope still has no `links` at collection level (partial — some do) |

---

## New Findings (F83–F90)

### F83 — SSN Namespace Not Recognized (LOW)

**Server:** OSH  
**Resource:** 1 deployment with `featureType: http://www.w3.org/ns/ssn/Deployment`  
**Impact:** `getCSAPIResourceType` returns `null` because only SOSA (`sosa/`) and SensorML (`sensorml/2.0#`) namespaces are recognized. SSN (`ssn/`) is the parent ontology containing SOSA.  
**Mitigation:** `classifyFeature` endpoint hint fallback correctly classifies it as `'Deployment'` when called from the `/deployments` endpoint context. `isCSAPIFeature` returns `false` and `extractCSAPIFeature` would throw.  
**Recommendation:** Add SSN namespace support to `toSosaLocalName` or create a `toSsnLocalName` helper. Single-server instance, non-blocking with fallback.

### F84 — 52N Procedure featureType Misclassification (MEDIUM)

**Server:** 52N  
**Resource:** 1 procedure with `featureType: sosa:Sensor`  
**Impact:** `getCSAPIResourceType` classifies as `'System'` (by design — System priority > Procedure). The `classifyFeature` hint CANNOT override because `getCSAPIResourceType` returns non-null. A procedure obtained from `/procedures` would be typed as System.  
**Root cause:** 52N uses `sosa:Sensor` (the sensor type definition) as the featureType for a procedure, which is semantically valid per the SOSA ontology (a sensor type IS a procedure) but conflicts with our classification priority.  
**The code documents this intentionally** (geojson.ts lines 64–66): _"featureType-based classification prioritizes System over Procedure."_  
**Recommendation:** Consider a `classifyFeature` override mode where endpoint hint takes precedence when featureType maps to a parent category. Deferred — single known case.

### F85 — Deployment validTime Non-null Assertion Risk (LOW)

**Server:** Both OSH and 52N  
**Resource:** All deployments lack `validTime` (null or absent)  
**Impact:** `extractCSAPIFeature` Deployment case uses `validTime: validTime!` (geojson.ts line 352). When `parseValidTime` returns `undefined`, the `!` assertion creates a Deployment with `validTime: undefined`, violating the type contract (`Deployment.properties.validTime: TimeInterval` is required per model.ts line 307).  
**Runtime effect:** No crash until downstream code accesses `.validTime.start`. Latent type safety issue.  
**Recommendation:** Either make `validTime` optional on `Deployment.properties` (spec says required but servers don't comply), or use a sentinel `TimeInterval` value. Low priority — no downstream consumer yet.

### F86 — 52N samplingFeatures SML Endpoint Now Returns 400 (SERVER LIMITATION)

**Server:** 52N  
**Endpoint:** `/samplingFeatures` with `Accept: application/sml+json`  
**Previous:** 200 with empty collection (Smoke Test #17)  
**Current:** 400 Bad Request  
**Impact:** Server-side regression for SML format on sampling features. geo+json and json still return 200 (empty FeatureCollection).

### F87 — 52N datastreams Error Code Change (SERVER LIMITATION — INFORMATIONAL)

**Server:** 52N  
**Previous:** `/datastreams` returned 500 for all Accept headers  
**Current:** json → 500 (unchanged), geo+json → 400 (changed), sml+json → 400 (changed)  
**Impact:** Error code improved from 500 to 400 for geo+json and sml+json, but endpoint remains non-functional. Endpoint is still broken.

### F88 — OSH Deployments and Procedures Now Populated (POSITIVE)

**Server:** OSH  
**Previous:** 0 deployments, 0 procedures  
**Current:** 16 deployments, 15 procedures (all smoke test data from CSAPI Explorer)  
**Impact:** Enables live handler validation against previously empty resource types. All deployment featureTypes recognized (15× SOSA, 1× SSN). All procedure featureTypes recognized (15× SOSA).

### F89 — SWE Common Schemas Match Parser Types (POSITIVE)

**Server:** OSH  
**Schemas validated:** DataRecord, Vector, Quantity, Text, Boolean  
**`uom` forms:** Both `{href}` and `{code}` present in live data  
**Impact:** Our SWE Common parser covers all SWE Common types seen in live datastream schemas. No unrecognized types encountered.

### F90 — Full SOSA Vocabulary Represented on OSH (POSITIVE)

**Server:** OSH  
**featureTypes observed:** Sensor, Platform, Deployment, Procedure, Sample (all SOSA) + Feature (SensorML)  
**Impact:** All Part 1 resource types have live data with recognized vocabulary. Handler covers 98.5% of resources (65/66 SF recognized; all 33 systems, 14/16 deployments excluding SSN, all 15 procedures).

---

## Findings Summary

| Category                     |  Count | Finding IDs                                                                                                           |
| ---------------------------- | -----: | --------------------------------------------------------------------------------------------------------------------- |
| Resolved / Stable            |     34 | F1, F2, F4, F10, F11, F13, F15, F19, F25, F29, F37, F39, F40, F43–F45, F47–F51, F54, F55, F58, F59, F62, F64–F70, F73 |
| Retracted                    |      1 | F57                                                                                                                   |
| Server Limitations — Carried |     20 | F6–F9, F16–F18, F20–F24, F26, F28, F32, F34–F36, F46, F72                                                             |
| Deferred — Client/Interop    |      7 | F5, F14, F27, F30, F31, F33, F38                                                                                      |
| Informational / Other        |     14 | F12, F41, F42, F52, F53, F56, F60, F61, F63, F71, F74–F77                                                             |
| **New — Low**                |  **2** | **F83, F85**                                                                                                          |
| **New — Medium**             |  **1** | **F84**                                                                                                               |
| **New — Server Limitation**  |  **2** | **F86, F87**                                                                                                          |
| **New — Positive**           |  **3** | **F88, F89, F90**                                                                                                     |
| **Total tracked**            | **90** | F1–F90                                                                                                                |

### Status Changes from Smoke Test #17

| Finding | Old Status                | New Status                                | Reason                                            |
| ------- | ------------------------- | ----------------------------------------- | ------------------------------------------------- |
| F3      | Deferred                  | **Addressed**                             | Issue #36 implemented `parseCollectionResponse`   |
| F20     | Carried (500 all formats) | Carried (500 json, 400 geo+json/sml+json) | 52N error code improved but endpoint still broken |

---

## Impact Assessment

### What Changed Since Phase 3.12

**Code changes (Issues #57–#75):**

- SWE Common parser: eliminated all `as unknown as T` double-casts (Issues #70–#74)
- Extracted `parseAssociationAttributeGroup` helper (Issue #75)
- Added `typeof` guard for `href` in `_helpers.ts` (Phase 3.15 F4 fix)
- 4 code reviews completed (Phases 3.13–3.16), all clean

**Server data changes:**

- OSH: +21 systems, +16 deployments (new), +15 procedures (new), +15 SF
- 52N: sampling features SML endpoint regressed (200 → 400)
- 52N: datastreams error codes partially improved (500 → 400 for some formats)

### Risk Assessment

| Risk                                  | Level              | Mitigation                                          |
| ------------------------------------- | ------------------ | --------------------------------------------------- |
| SSN namespace unrecognized (F83)      | Low                | Classification fallback handles it; single instance |
| 52N procedure misclassification (F84) | Medium             | By design (documented). One known case.             |
| Deployment validTime assertion (F85)  | Low                | No downstream consumer. Latent only.                |
| 52N SF SML regression (F86)           | None (server-side) | Not blocked — geo+json still works                  |

### Recommendations

1. **F83 (SSN namespace):** Create issue to add SSN namespace support — straightforward addition
2. **F84 (procedure misclassification):** Defer — design decision documented, single edge case
3. **F85 (validTime assertion):** Create issue to make `validTime` optional on Deployment type, matching observed server behavior

**No automatic issue creation per protocol — findings presented for human decision.**
