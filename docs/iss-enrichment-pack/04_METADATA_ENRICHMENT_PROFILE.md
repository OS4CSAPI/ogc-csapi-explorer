# 04 Metadata Enrichment Profile

## Design rule
Use rich metadata where it belongs:
- Systems: what the thing/publisher is
- Deployments: what role/context it occupies
- Procedures: how the result is produced
- DataStreams: what product it emits
- Observations: the time-stamped result instances

## Preferred metadata buckets
### Identity
- uid
- name
- short description
- version/revision where applicable

### Classification / role
- platformType
- missionType
- orbitClass
- roleType
- productType

### Provenance / method
- sourceProvider
- sourceUrl
- elementFormat
- propagationModel
- software/library version
- lastElementsFetch
- sourceEpoch
- sourceAgeSec

### Quality / freshness
- updateIntervalSec
- expectedLatencySec
- posErrorM
- samplePeriodSec
- staleness semantics

### Contacts / ownership
- ownerOrg
- maintainer
- bootstrapOwner
- authoritative/demo status

### Media / documents
- official reference page
- datasheet or method notes
- descriptive image
- architecture diagram
- schema explainer

## Strong recommendation
Do not invent random ad hoc image fields everywhere.
Use linked/attached media/documents consistently as part of the rich descriptive metadata layer.
