# 09 Asset and Document Manifest

## Use these as linked/attached descriptive resources where appropriate

### Official ISS references
1. NASA ISS overview
   - https://www.nasa.gov/international-space-station/space-station-overview/
   - Recommended placement:
     - `iss-position-publisher`
     - `iss-orbittrack-publisher`

2. NASA ISS reference page
   - https://www.nasa.gov/reference/international-space-station/
   - Recommended placement:
     - `iss-position-publisher`

### Source data references
3. CelesTrak GP data formats
   - https://celestrak.org/NORAD/documentation/gp-data-formats.php
   - Recommended placement:
     - `sgp4-propagation:v1`
     - `iss-position-publisher`

4. CelesTrak element sets index
   - https://celestrak.org/NORAD/elements/
   - Recommended placement:
     - `iss-position-publisher`

### Method/library references
5. satellite.js
   - https://github.com/shashwatak/satellite-js
   - Recommended placement:
     - `sgp4-propagation:v1`
     - `orbit-track-generation:v1`

### Standards references
6. SensorML 3.0
   - https://docs.ogc.org/is/23-000/23-000.html
   - Recommended placement:
     - branch-level documentation
     - procedure metadata references

7. OGC API Connected Systems
   - https://www.ogc.org/standards/ogc-api-connected-systems/
   - Recommended placement:
     - branch-level documentation

## Suggested descriptive images to source/place
1. Official ISS image/render
   - Place on:
     - `iss-position-publisher`
     - optionally `ISS Tracking Role`

2. Simple ISS tracking architecture diagram
   - Place on:
     - `Orbital Tracking Demo`
     - `iss-position-publisher`

3. Orbit-track product illustration
   - Place on:
     - `iss-orbittrack-publisher`
     - `orbitGroundTrack`

4. Position-feed schema explainer image
   - Place on:
     - `satPositionWGS84`

## Suggested internal asset filenames (if you later store them locally)
- `iss_official_image_primary.jpg`
- `iss_tracking_architecture_diagram.png`
- `iss_orbit_track_example.png`
- `iss_position_schema_explainer.png`
