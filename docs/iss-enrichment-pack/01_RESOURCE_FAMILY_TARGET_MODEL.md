# 01 Resource Family Target Model

## Goal
Make the ISS branch:
- deployment-first,
- structurally honest,
- semantically richer,
- and easier to explain to a user.

## Target deployment backbone
```text
Orbital Tracking Demo (deployment)
└── LEO Objects (subdeployment)
    └── ISS Tracking Role (subdeployment)
        ├── ISS Tracking — Position Feed (leaf deployed system)
        │    platform@link -> iss-position-publisher
        └── ISS Tracking — Orbit Track Feed (leaf deployed system)
             platform@link -> iss-orbittrack-publisher
```

## Target producer systems
### `iss-position-publisher`
Produces:
- `satPositionWGS84`

### `iss-orbittrack-publisher`
Produces:
- `orbitGroundTrack`

## Target procedures
- `sgp4-propagation:v1`
- `orbit-track-generation:v1`

## Target datastreams
### `satPositionWGS84`
Purpose:
- near-real-time point position fixes

### `orbitGroundTrack`
Purpose:
- periodically refreshed past + predicted ground-track product for map rendering

## Asset identity treatment
The ISS is the thing being tracked. The publishers are not the ISS.

Use:
- `noradId = 25544`
- `assetName = "ISS (ZARYA)"`

Carry those in:
- producer system metadata
- result payloads
- linked/attached documents/media

Later, if FOI links persist correctly, add:
- SamplingFeature / asset resource representing the ISS identity
- observation-level FOI links to that asset

## Recommended minimum descriptive media
- NASA ISS overview page
- one official ISS image
- CelesTrak source documentation
- one simple architecture diagram showing:
  source data -> publisher -> CSAPI datastreams -> Explorer
