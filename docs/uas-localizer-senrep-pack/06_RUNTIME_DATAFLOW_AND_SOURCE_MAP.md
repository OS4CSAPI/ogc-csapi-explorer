# 06 Runtime Dataflow and Source Map

## Authoritative bootstrap and runtime baseline
### Bootstrap
- `bootstrap_v4.py` = authoritative branch baseline
- `bootstrap_localizer.py` = targeted localizer bootstrap

### Runtime agents
- simulator
- localizer
- Explorer
- SET reporting workflow

## Live runtime chain

```text
UAV simulator
  -> per-node LOB observations
    -> string localizer
      -> location estimate observations
        -> operator click-to-report workflow
          -> SET-A SENREP observation
            -> track SamplingFeature creation / identity commitment
```

## Source/producer responsibilities

### MA nodes
Produce:
- LOB
- classification probabilities
- health
- scene summary
- SSL/SST/track updates
- detection capabilities

### Localizer
Consumes:
- latest node LOBs
Computes:
- weighted least-squares bearing intersection
Produces:
- string-level location estimates

### SET-A
Owns:
- SENREP reporting datastream
Operationally:
- commits identity at reporting tier
- becomes the authoritative source of the formal report product

### Explorer
Renders:
- deployments
- detection ranges
- lines of bearing
- location estimates
- SENREP markers
- track/sampling features
- observation tracks

## Recommended additional explicit source/provenance fields

### Localizer outputs
- `procedureUid`
- `correlationWindowSec`
- `stalenessLimitSec`
- `minLobsRequired`
- `residual_m`
- `numContributingLobs`
- `contributingSensors`
- `contributingLobsJson`

### SENREPs
- `contactId`
- `sourceFixObsId`
- `sourceLobObsIds`
- `posErrorM`
- `confidence`

## Why this matters
This makes every tier auditable:
- what sensed
- what fused
- what was reported
- what identity was committed
