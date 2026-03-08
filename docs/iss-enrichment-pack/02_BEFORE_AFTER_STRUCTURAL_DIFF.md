# 02 Before / After Structural Diff

## Current (documented) family
```text
ISS Tracking Deployment
└── ISS Instance
     platform/occupant -> ISS Tracker
         └── ISS Position
Procedure: ISS Tracking Procedure
```

## Proposed family
```text
Orbital Tracking Demo
└── LEO Objects
    └── ISS Tracking Role
        ├── ISS Tracking — Position Feed
        │    platform@link -> iss-position-publisher
        │    └── satPositionWGS84
        └── ISS Tracking — Orbit Track Feed
             platform@link -> iss-orbittrack-publisher
             └── orbitGroundTrack

Procedures:
- sgp4-propagation:v1
- orbit-track-generation:v1
```

## Change summary
### Structural changes
- add two interior deployments for organizational context
- split one leaf into two feed-specific leaves
- split one producer into two producer systems
- split one vague procedure into two explicit procedures
- split one product family into two datastreams

### Metadata changes
- add explicit source/provider links
- add method/provenance metadata
- add image/document attachments
- add quality/freshness fields
- add role/purpose descriptions throughout

## Why not just metadata-enrich the current branch?
Because the current branch still collapses:
- asset identity
- producer capability
- method
- product shape

More descriptive text alone does not fix that conceptual flattening.
