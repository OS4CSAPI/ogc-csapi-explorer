# Incident Report: Global /datastreams Endpoint 500 — Localizer DS Corruption

**Date:** 2026-03-10  
**Detected:** ~01:00 EST (operator reported webapp "not working" on production)  
**Resolved:** ~02:15 EST (broken datastreams deleted from server)  
**Root cause:** Corrupted datastream metadata records in OSH H2 database  
**Severity:** Critical — broke ALL datastream listing endpoints, prevented map rendering  

---

## 1. Symptoms

- Production webapp at `https://ogc-csapi-explorer.pages.dev/map` failed to render ISS, observation tracks, and LOB bearing lines
- `GET /datastreams?limit=200` returned HTTP 200 but with **malformed JSON** — first item serialized correctly, then `{"status":500,"message":"Internal server error"}` was appended mid-response
- `GET /systems/040g/datastreams` (SET-A) — same malformed JSON behavior
- `GET /systems/04o0/datastreams` (Localizer) — HTTP 500

## 2. Root Cause

Two datastream records under the **AZ String Alpha Localizer** system (`04o0`) had corrupted metadata that the OSH SensorHub's JSON serializer could not process:

| DS ID | Name | Output Name | Notes |
|-------|------|-------------|-------|
| `04hg` | Location Estimate | `locationEstimate` | WLS position estimates from contributing LOBs |
| `04i0` | Sensor Report | `senrep_v1_1` | Formal SENREP with enrichments |

Both datastreams existed in the H2 database and their `/schema` and `/observations` sub-endpoints returned HTTP 200. Only the metadata serialization (`GET /datastreams/{id}`) crashed with HTTP 500.

### Why this broke the global endpoint

The OSH server serializes datastream listings as a streaming JSON array. When the serializer encountered a broken DS record mid-stream (after writing the HTTP 200 headers and the first valid items), it injected a raw error object into the response body, producing syntactically invalid JSON:

```json
{
  "items": [
    { "id": "044g", "name": "SENREP (Sensor Report)", ... }
  ]{
  "status": 500,
  "message": "Internal server error"
}
```

The `items` array was never properly closed with `]}`.

### Why per-system queries were also affected

- `GET /systems/040g/datastreams` crashed because `040g` (SET-A) had DS `044g`, and the server's iteration order placed the broken localizer DS (`04hg`) immediately after SET-A's SENREP in the global iteration sequence.
- `GET /systems/04o0/datastreams` returned HTTP 500 because both DS under the localizer were broken.

## 3. Resolution

**Deleted both broken datastream records** via HTTP DELETE:

```
DELETE /sensorhub/api/datastreams/04hg  → 204 No Content
DELETE /sensorhub/api/datastreams/04i0  → 204 No Content
```

### Post-fix verification

| Endpoint | Before | After |
|----------|--------|-------|
| `GET /datastreams?limit=200` | Malformed JSON (500 mid-stream) | 32 items, valid JSON |
| `GET /systems/040g/datastreams` | Malformed JSON | 1 item (SENREP), valid JSON |
| `GET /systems/04o0/datastreams` | HTTP 500 | 0 items, valid JSON |
| Production proxy (`/api/osh/datastreams?limit=200`) | Malformed JSON | 32 items, valid JSON |

## 4. Impact

- Localizer system (`04o0`) now has 0 datastreams — location estimate and enriched SENREP outputs are gone
- Localizer observation data may still exist in the H2 database but is no longer accessible via the API
- The localizer bootstrap script (`scripts/bootstrap_localizer.py`) will need to be re-run if localizer functionality is restored

## 5. Lessons Learned

1. **Same pattern as RC-1 in 2026-03-05 incident**: OSH's H2 backend produces corrupt metadata records for certain schema configurations. This was previously seen with LineString SamplingFeatures; now also affects DataStream records.
2. **Streaming JSON serialization is fragile**: When the server encounters a serialization error mid-response, it cannot change the HTTP status code (headers already sent). This turns a single bad record into a poison pill that breaks the entire listing endpoint.
3. **Client-side resilience**: The `apiFetch()` wrapper correctly catches malformed JSON and returns `{ok: false}`, but downstream code relied on the global `/datastreams` endpoint for feature discovery (Phase C of `buildSystemLocationCache()`, `discoverLocalizerDatastream()`).

## 6. Related

- `docs/incidents/2026-03-05-iss-orbit-track-rendering.md` — previous incident with same H2 serialization bug pattern
- `docs/research/OSH_Global_Datastreams_Endpoint_500_Bug.md` (in OSHConnect-Python) — initial investigation filed earlier today
- Commit `4da42e1` — client-side ISS fix (supplementary DS discovery via deployment chain) — still useful as defense-in-depth
