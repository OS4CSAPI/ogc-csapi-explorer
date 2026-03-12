# Procedures Show No Related Resources in Explorer

**Date:** 2026-03-11  
**Severity:** Low (cosmetic / data-model completeness)  
**Status:** Open — server-side limitation, no Explorer fix needed

## Symptom

When viewing any Procedure in the Explorer's detail view, the "Implementing
Systems" and "Datastreams" related-resource panels are always empty.

## Root Cause

Three compounding issues on the OSH SensorHub server:

### 1. Nested navigation endpoints not implemented

The CSAPI spec defines `procedures/{id}/systems` and
`procedures/{id}/datastreams` as valid navigation endpoints.  SensorHub
returns **400 "Invalid resource name"** for both:

```
GET /procedures/040g/systems   → 400 {"message": "Invalid resource name: 'systems'"}
GET /procedures/040g/datastreams → 400 {"message": "Invalid resource name: 'datastreams'"}
```

### 2. Collection-level `?procedure=` filter not functional

The Explorer could fall back to `/systems?procedure=040g` to find
implementing systems.  SensorHub accepts the parameter but ignores it,
returning **0 items**.

### 3. `typeOf@link` silently dropped on persist

Every bootstrap script sends `typeOf@link` in the system PUT payload to
associate systems with their procedure:

```json
"typeOf@link": {"href": "040g", "title": "NWS Surface Observation v1"}
```

SensorHub accepts the property on write but does not serialize it back in
GET responses.  The `properties` object on the returned system contains only
`uid`, `name`, `description`, `featureType`, and `validTime` — no
`typeOf@link` or `systemKind@link`.  This means the Explorer's `@link`
fallback path (which resolves procedure references from parent system
properties when the nested endpoint returns 400) has nothing to work with.

## Explorer Code State

The Explorer is correctly wired:

- `state.ts` defines `RELATED_RESOURCES['procedures']` with two relations:
  `{systems, relation: 'systems'}` and `{datastreams, relation: 'datastreams'}`
- `ResourceDetail.vue` `fetchRelation()` tries the nested endpoint first,
  then falls back to `tryLinkFallback()` on 400
- `tryLinkFallback()` handles `systems → procedures` via `systemKind@link`
  but has no reverse path for `procedures → systems`

No Explorer code change is required — the data simply isn't available from
the server.

## Possible Future Workarounds

1. **Client-side reverse lookup** — Fetch all systems, match to procedures
   by UID naming convention (e.g. `urn:os4csapi:procedure:nws-*` →
   `urn:os4csapi:system:nws:*`).  Heuristic but functional for this server.

2. **Upstream SensorHub fix** — File an issue requesting implementation of
   `/procedures/{id}/systems` navigation and/or persistence of `typeOf@link`
   in system properties.

3. **Bootstrap-time link table** — Maintain a static JSON mapping of
   procedure IDs → implementing system IDs, fetched by the Explorer on load.

## Verified Procedure Inventory

| ID   | UID | Name |
|------|-----|------|
| 040g | urn:os4csapi:procedure:nws-surface-observation:v1 | NWS Surface Observation v1 |
| 0410 | urn:os4csapi:procedure:ndbc-buoy-observation:v1 | NDBC Buoy Observation v1 |
| 041g | urn:os4csapi:procedure:ndbc:buoycam-imagery:v1 | NDBC BuoyCAM Imagery v1 |
| 0420 | urn:os4csapi:procedure:coops-water-level:v1 | CO-OPS Coastal Observation v1 |
| 042g | urn:os4csapi:procedure:metar-decoder:v1 | METAR Decoder v1 |
| 0430 | urn:os4csapi:procedure:opensky-adsb-decoder:v1 | OpenSky ADS-B Decoder v1 |
| 043g | urn:os4csapi:procedure:senrep:sop:v1 | SENREP SOP v1 |
| 0440 | urn:os4csapi:procedure:lob-wls-triangulation:v1 | WLS LOB Triangulation v1 |
| 044g | urn:os4csapi:procedure:sgp4-propagation:v1 | SGP4 Propagation v1 |
| 0450 | urn:os4csapi:procedure:orbit-track-generation:v1 | Orbit Track Generation v1 |
| 045g | urn:os4csapi:procedure:usgs-water-observation:v1 | USGS Water Observation v1 |
| 0470 | urn:os4csapi:procedure:usgs-nims-imagery:v1 | USGS NIMS Station Imagery v1 |
| 047g | urn:os4csapi:procedure:usgs-eq-feed-normalizer:v1 | USGS Earthquake Feed Normalizer |
