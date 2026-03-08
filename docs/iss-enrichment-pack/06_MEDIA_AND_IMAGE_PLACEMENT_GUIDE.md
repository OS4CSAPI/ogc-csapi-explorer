# 06 Media and Image Placement Guide

## Principle
Put descriptive images/documents where they explain the right concept.

## Deployment resources
Use for:
- operational context image
- mission/demo overview image
- context diagram
- branch-level architecture figure

### Recommended for ISS branch
#### `Orbital Tracking Demo`
Attach:
- architecture diagram image
- short overview document

#### `ISS Tracking Role`
Attach:
- role/context explanation image (optional)
- demo screenshot if useful

## System resources
Use for:
- official platform/publisher image
- product photo/render
- vendor/manufacturer reference
- system diagram

### Recommended for ISS systems
#### `iss-position-publisher`
Attach:
- official ISS image
- NASA ISS overview page
- publisher architecture diagram

#### `iss-orbittrack-publisher`
Attach:
- orbit-track illustration image
- method note / track generation explainer

## Procedure resources
Use for:
- algorithm/block diagram
- reference links
- methodological notes

### Recommended
#### `sgp4-propagation:v1`
Attach:
- propagation diagram
- CelesTrak docs
- library reference

#### `orbit-track-generation:v1`
Attach:
- sampled orbit-track illustration
- assumptions note (window length, sample period, dateline behavior)

## DataStream resources
Use for:
- schema explainer
- small illustrative thumbnail
- legend-like graphics

### Recommended
#### `satPositionWGS84`
Attach:
- example point fix schema image or mini diagram

#### `orbitGroundTrack`
Attach:
- example orbit-track product image/thumbnail

## What not to do
- Do not bury the only useful ISS image inside an observation.
- Do not add arbitrary image fields with no consistent semantics.
- Do not put role/context images only on the producer system if they explain the deployment context better.
