# 01 Resource Family Target Model

## Goal
Keep the doctrine-aligned deployment backbone you already have, while making the
UAS / localizer / SENREP family more structurally honest, more richly described,
and easier for both humans and clients to understand.

## Current backbone to preserve
```text
ICO
└── RSO
    └── SSO
        └── SNET
            └── Sensor Field 001
                └── String Alpha
                    ├── Node 1 Emplacement -> AZ-MA-1
                    ├── Node 2 Emplacement -> AZ-MA-2
                    ├── Node 3 Emplacement -> AZ-MA-3
                    ├── SET-A Emplacement -> SET-A
                    ├── Monitoring Site Emplacement -> Monitoring Site
                    └── Relay Emplacement -> Relay
```

## Recommended target model
Preserve the above, but add explicit string-level and reporting-level resources:

```text
ICO
└── RSO
    └── SSO
        └── SNET
            └── Sensor Field 001
                └── String Alpha
                    ├── Node 1 Emplacement -> AZ-MA-1
                    ├── Node 2 Emplacement -> AZ-MA-2
                    ├── Node 3 Emplacement -> AZ-MA-3
                    ├── SET-A Emplacement -> SET-A
                    ├── Monitoring Site Emplacement -> Monitoring Site
                    ├── Relay Emplacement -> Relay
                    └── String Alpha Localizer Feed -> AZ String Alpha Localizer
```

### Optional future addition
If you want track identity to be even more explicit, add:
- `Track FOI / SamplingFeature` resources created at the SET reporting tier
- a stable `urn:os4csapi:track:{contactId}` pattern

## Why this target model
The current branch already does many things right:
- deployments are first-class,
- doctrinal echelons are visible,
- node/support emplacements exist,
- SET owns the SENREP datastream,
- localizer exists as a real producer.

What is still too thin:
1. the localizer is structurally under-expressed relative to its operational importance
2. the SENREP branch is not yet metadata-rich enough
3. the transition from localizer fix -> operator report -> track identity is not explicit enough in the resource family itself

## Target producer/reporting resources

### Systems
- `AZ-MA-1`
- `AZ-MA-2`
- `AZ-MA-3`
- `AZ String Alpha Localizer`
- `SET-A`
- `Monitoring Site`
- `Relay`

### Procedures
- ODAS node procedures (already present)
- `lob-wls-triangulation:v1`
- `senrep:sop:v1`
- optional future: `track-creation-from-senrep:v1`

### DataStreams
- per-node LOB
- per-node classification probabilities
- per-node health
- per-node scene summary
- per-node SSL / SST / track updates
- per-node detection capabilities
- string-level location estimate
- SET-level SENREP

### SamplingFeatures / track identity
- create one SamplingFeature per committed contact/track
- recommended stable key: `contactId`
- recommended UID pattern: `urn:os4csapi:track:{contactId}`

## Structural recommendation in one sentence
Do **not** rebuild the deployment tree; keep it.  
Instead, strengthen the family by:
- clarifying leaf meanings,
- adding a localizer leaf deployment,
- enriching SET/reporting semantics,
- and formalizing track identity resources at the reporting tier.
