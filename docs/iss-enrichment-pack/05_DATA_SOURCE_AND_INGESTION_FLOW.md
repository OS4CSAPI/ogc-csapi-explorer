# 05 Data Source and Ingestion Flow

## Official/primary references
- NASA ISS overview:
  - https://www.nasa.gov/international-space-station/space-station-overview/
- NASA ISS reference page:
  - https://www.nasa.gov/reference/international-space-station/
- CelesTrak GP data formats:
  - https://celestrak.org/NORAD/documentation/gp-data-formats.php
- CelesTrak element sets index:
  - https://celestrak.org/NORAD/elements/
- satellite.js repository:
  - https://github.com/shashwatak/satellite-js
- SensorML 3.0:
  - https://docs.ogc.org/is/23-000/23-000.html
- OGC API Connected Systems:
  - https://www.ogc.org/standards/ogc-api-connected-systems/

## Source data
### Provider
CelesTrak

### What is fetched
General perturbations orbital elements (preferably JSON/OMM-capable endpoint rather than TLE-only assumptions).

### How it is made available
Public HTTP query endpoint:
- `gp.php?...&FORMAT=JSON`
- legacy `FORMAT=TLE` if needed

## Ingestion steps
1. Fetch latest orbital element set for NORAD 25544.
2. Parse and validate source fields.
3. Record:
   - fetch time
   - element epoch
   - source format
4. Run SGP4 propagation.
5. Convert to geodetic position.
6. Publish position observations.
7. Periodically sample a window of propagated positions to create orbit-track products.
8. Publish orbit-track observations.

## What we do with it
### Position feed
Publish near-real-time point fixes to `satPositionWGS84`.

### Orbit-track feed
Publish past + predicted sampled path products to `orbitGroundTrack`.

### Explorer usage
- latest point from `satPositionWGS84`
- latest orbit-track product from `orbitGroundTrack`
- optional observation-derived trail from recent position fixes

## Recommended source/provenance fields to carry into products
- `sourceProvider = "CelesTrak"`
- `sourceUrl`
- `elementFormat`
- `sourceEpoch`
- `sourceAgeSec`
- `propagationModel = "SGP4"`
- `library = "satellite.js"` (or chosen implementation)
