# 02 Before / After Structural Diff

## Current documented shape
Based on the provided source-materials index, the current authoritative bootstrap (`bootstrap_v4.py`) creates:
- 6 top-level systems
- 39 MA subsystems
- 9 procedures
- a 10-node deployment hierarchy
- 22 datastreams
- 9 control streams

The live branch already contains:
- doctrine-aligned deployment hierarchy
- 3 MA node emplacements
- SET / Monitoring Site / Relay support emplacements
- SET-owned SENREP datastream
- standalone localizer system + procedure + datastream

## What is already good
1. Deployments are already first-class.
2. The hierarchy is closer to doctrine than most CSAPI implementations.
3. The MA nodes are richly backed by SensorML.
4. The SET is already the natural reporting-tier owner of SENREPs.
5. The localizer is already implemented as a real producer.

## What is still weak
### 1) Localizer structural visibility
The localizer is important operationally, but it does not appear to have its own explicit
deployment-leaf role under String Alpha.

### 2) SENREP schema thinness
The current SENREP schema is a 20-field reporting record, but it lacks the stronger
track/join/provenance fields needed for resilient, auditable identity management.

### 3) Track identity explicitness
The design docs say:
- SENREP = Observation
- Track = SamplingFeature
- SET creates the track
- `contactId` is the authoritative join key

That logic is strong, but the pack should make it materially visible in the resource family.

---

## Recommended after-state

### Preserve
- ICO -> RSO -> SSO -> SNET -> Field -> String backbone
- Node 1/2/3, SET, Monitoring Site, Relay emplacements
- rich MA node metadata
- existing localizer procedure

### Add or strengthen
- `String Alpha Localizer Feed` leaf deployment
- enriched `AZ String Alpha Localizer` system metadata
- upgraded SET/SENREP reporting semantics
- track SamplingFeature template and creation semantics
- richer provenance and operator-facing metadata

---

## Structural delta summary

| Concern | Current | Recommended |
|---|---|---|
| Deployment backbone | Already strong | Preserve |
| Localizer deployment visibility | Thin / implicit | Add explicit leaf deployment |
| SET reporting role | Present but lightly described | Enrich and formalize |
| Track identity | Conceptually decided in docs | Add concrete SamplingFeature template + UID convention |
| SENREP schema | 20 fields, doctrinally shaped | Add `contactId`, provenance, confidence/error fields |
| Media/docs placement | Partial | Systematic across deployments/systems/procedures/datastreams |

## Recommendation
Treat this as a **targeted resource family enrichment and completion effort**, not a total redesign.
