# 04 Metadata Enrichment Profile

## Design rule
A resource should answer four questions:
1. What is this?
2. Where/when is it operating?
3. How does it produce its data?
4. How much should I trust it?

## Resource-family priorities

### Deployments
Use deployments to express:
- doctrinal echelon
- operational purpose
- container vs role vs leaf semantics
- active/demo state
- parent mission/context

### Systems
Use systems to express:
- identity
- what the thing is in plain English
- whether it is physical, human/team, software, or support equipment
- who owns/operates it
- where to learn more about it

### Procedures
Use procedures to express:
- what method is being applied
- what inputs it expects
- what outputs it produces
- assumptions, dependencies, limitations
- reference docs/libraries

### DataStreams
Use datastreams to express:
- product meaning
- units/frame/cadence
- raw vs derived vs authoritative
- staleness/quality semantics
- schema docs and illustrative examples

### Observations
Use observations to express:
- the concrete, time-stamped result
- provenance fields
- identity join keys where needed
- quality/confidence where needed

## Recommended metadata buckets
### Identity
- uid
- name
- short description
- version/revision

### Role / classification
- roleType
- systemKind
- missionType
- deploymentType
- productType

### Provenance / method
- sourceProvider
- sourceUrl
- procedure UID
- algorithm/library version
- lastUpdated/lastVerified
- contributing source IDs

### Quality / confidence
- uncertainty/error
- confidence
- freshness/source age
- number of contributing sensors

### Ownership / lifecycle
- ownerOrg
- maintainer
- bootstrapOwner
- authoritative/demo status

### Media / documents
- official reference page
- product photo/render
- architecture diagram
- method note
- schema explainer
