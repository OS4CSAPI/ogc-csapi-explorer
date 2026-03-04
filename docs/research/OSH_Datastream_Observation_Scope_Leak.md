# OSH Bug: Datastream-Scoped Observation Queries Return Cross-Datastream Results

**Date:** 2026-03-04  
**Server:** OSH on Oracle Cloud (latest `master` branch)  
**Encoding:** JSON (`application/json`)

---

## Summary

`GET /datastreams/{id}/observations` returns observations that belong to **other datastreams**, identified by mismatched `datastream@id` values in the response. The contamination pattern affects datastreams that share a parent system, but also extends across system boundaries in at least one case.

This is a data isolation bug: the datastream ID in the URL path is not being used as a filter; instead, the server appears to aggregate observations at a broader scope (possibly system-level or global) and return them under the wrong datastream endpoint.

---

## Environment

- **Server:** `https://os4csapi-osh.duckdns.org/sensorhub/api`
- **OSH version:** Latest `master` branch as of 2026-03
- **Date tested:** 2026-03-04
- **Client:** PowerShell `Invoke-RestMethod` and `curl`

---

## Reproduction

### Setup: System with multiple datastreams

System `0420` (AZ-MA-1) has 8 datastreams, including:

| DS ID | Name | outputName |
|-------|------|------------|
| `04c0` | AZ-MA-1 LOB | `az_ma_1_lob` |
| `04dg` | AZ-MA-1 Detection Capabilities | `az_ma_1_detection_capabilities` |
| `0430` | AZ-MA-1 Classification Probabilities | `az_ma_1_classification_probabilities` |
| ... | (5 more) | ... |

The LOB datastream (`04c0`) has many observations (LOB bearing data). The Detection Capabilities datastream (`04dg`) has 1 observation (static range config with `minRange_m`, `nominalRange_m`, `maxRange_m`).

### Request

```http
GET /sensorhub/api/datastreams/04dg/observations?limit=10 HTTP/1.1
Accept: application/json
Authorization: Basic <credentials>
```

### Expected Response

Only observations belonging to datastream `04dg` should be returned. The response should contain the 1 detection range observation.

### Actual Response

```json
{
  "items": [
    {
      "id": "040t1jkupk32bemg80",
      "datastream@id": "04c0",
      "phenomenonTime": "2026-03-04T03:30:24.633Z",
      "resultTime": "2026-03-04T03:30:24.633Z",
      "result": {
        "timestamp": 1772595024.6336455,
        "trackId": 1,
        "bearingTrue": 309.15,
        "bearingStdDev": 2.93,
        "sensorLat": 31.6490196,
        "sensorLon": -110.2758537,
        "classification": "UAS"
      }
    },
    { "id": "040tbjkupk32bemg80", "datastream@id": "04c0", "..." : "..." },
    { "id": "040tljkupk32bemg80", "datastream@id": "04c0", "..." : "..." },
    { "id": "040tvjkupk32bemg80", "datastream@id": "04c0", "..." : "..." },
    { "id": "040u9jkupk32bemg80", "datastream@id": "04c0", "..." : "..." },
    { "id": "040ujjkupk32bemg80", "datastream@id": "04c0", "..." : "..." },
    { "id": "040utjkupk32bemg80", "datastream@id": "04c0", "..." : "..." },
    { "id": "040v7jkupk32bemg80", "datastream@id": "04c0", "..." : "..." },
    { "id": "040vhjkupk32bemg80", "datastream@id": "04c0", "..." : "..." },
    { "id": "040vrjkupk32bemg80", "datastream@id": "04c0", "..." : "..." }
  ]
}
```

**All 10 observations have `datastream@id: "04c0"` (the LOB datastream), NOT `"04dg"` (the requested datastream).** The actual detection range observation is buried and only appears when fetching 50+ results.

### Verification: The detection range observation exists

```http
GET /sensorhub/api/observations/040uvjsupk30000000 HTTP/1.1
```

```json
{
  "id": "040uvjsupk30000000",
  "datastream@id": "04dg",
  "phenomenonTime": "2026-03-04T03:33:03Z",
  "result": {
    "timestamp": 1772595183.01,
    "shape": "circular",
    "minRange_m": 667.0,
    "nominalRange_m": 1833.0,
    "maxRange_m": 3000.0,
    "confidence": 0.7,
    "basis": "estimated"
  }
}
```

The observation exists and correctly reports `datastream@id: "04dg"`. It just doesn't surface in the standard datastream-scoped query because it's drowned by foreign observations.

---

## Scope of Contamination

### All 3 detection_capabilities datastreams are affected

| Queried DS | DS Name | Obs Returned | Foreign Obs | Contaminating DS (`datastream@id`) |
|------------|---------|-------------|-------------|-----------------------------------|
| `04dg` | MA-1 Detection Capabilities | 50 | 49 (98%) | `04c0` (AZ-MA-1 LOB) |
| `04e0` | MA-2 Detection Capabilities | 50 | 49 (98%) | `04cg` (AZ-MA-2 LOB) |
| `04eg` | MA-3 Detection Capabilities | 50 | 49 (98%) | `04f0` (UAS Location Estimate) |

### Contamination crosses system boundaries

| Queried DS | Parent System | Contaminating DS | Parent System | Same System? |
|------------|---------------|------------------|---------------|--------------|
| `04dg` | `0420` (AZ-MA-1) | `04c0` | `0420` (AZ-MA-1) | **Yes** — siblings |
| `04e0` | `0490` (AZ-MA-2) | `04cg` | `0490` (AZ-MA-2) | **Yes** — siblings |
| `04eg` | `049g` (AZ-MA-3) | `04f0` | `04n0` (Localizer) | **No** — different system entirely |

MA-3's detection_capabilities DS (`04eg`, system `049g`) is contaminated by the localizer DS (`04f0`, system `04n0`). These are on **completely different systems**, so the leak is not limited to same-system siblings.

### Contamination is unidirectional

LOB datastreams return only their own observations when queried directly:

```http
GET /sensorhub/api/datastreams/04c0/observations?limit=3 HTTP/1.1
```

All 3 returned observations have `datastream@id: "04c0"` — no leakage from detection_capabilities back into LOB queries.

---

## Impact

1. **Data integrity:** Clients querying a specific datastream receive data from unrelated datastreams with different schemas
2. **Query reliability:** `resultTime=latest` on a datastream with 1 observation returns a foreign observation with a later timestamp, making the real data unreachable via standard query patterns
3. **Silent failure:** The contaminating observations are returned with HTTP 200 — no indication that they don't belong to the queried datastream. Only the `datastream@id` field (if checked) reveals the mismatch
4. **Practical consequence:** Our detection range rings disappeared 3 times during live development because `GET /datastreams/{id}/observations?resultTime=latest&limit=1` consistently returned LOB data instead of range config data

---

## Workaround (implemented)

Frontend `fetchDetectionRangeConfigs()` now:
1. Fetches `limit=50` instead of `limit=1`
2. Scans results for the first observation containing `minRange_m` (schema-based filtering)
3. Ignores observations that don't match the expected schema

This is fragile — if more than 49 contaminating observations precede the real data, the detection range observation won't be in the first page.

---

## Expected Behavior

`GET /datastreams/{id}/observations` should return **only** observations that belong to datastream `{id}`. The `datastream@id` on every returned observation should match the `{id}` in the URL path.

---

## Cross-References

- [opensensorhub/osh-core#337](https://github.com/opensensorhub/osh-core/issues/337) — deployment association gaps (related but different: `@link` field persistence)
- [opensensorhub/osh-core#339](https://github.com/opensensorhub/osh-core/issues/339) — `samplingFeature@link` silently dropped (same silent-failure pattern)
