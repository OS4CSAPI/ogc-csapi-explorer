# AZ-MA-2 & AZ-MA-3 Oracle Server Migration Report

**Date:** 2026-03-02  
**Server:** `https://os4csapi-osh.duckdns.org/sensorhub/api` (Oracle Cloud, 129.80.248.53)  
**Script:** `scripts/bootstrap_v4.py`  
**Branch:** `main`  
**Operator:** Copilot agent, directed by S. Bolling

---

## Executive Summary

AZ-MA-2 and AZ-MA-3 — two additional ODAS 7-microphone acoustic monitoring
array nodes — were successfully provisioned on the Oracle OSH server. Both
nodes mirror the hardware structure of the existing AZ-MA-1 node (13
subsystems each) and are deployed as sibling nodes alongside Node 1 under
Sensor String Alpha. **No observations** were provisioned for MA-2 or MA-3;
datastreams and control streams exist but are empty, pending future data
replay.

All 50 new resources were created with zero errors. The authoritative
bootstrap script (`bootstrap_v4.py`) was updated to maintain single-source-of-
truth coverage of the entire Oracle server state.

---

## Scope

| Item | Count |
|---|---|
| New top-level systems | 2 (AZ-MA-2, AZ-MA-3) |
| New subsystems | 26 (13 per node) |
| New deployment nodes | 2 (Node 2, Node 3 under String Alpha) |
| New datastreams | 14 (7 per node) |
| New control streams | 6 (3 per node) |
| New platform@link bindings | 2 (Node 2 → MA-2, Node 3 → MA-3) |
| Observations provisioned | 0 (by design) |
| **Total new resources** | **50** |

---

## Server State After Migration

### Systems (6 total)

| System | ID | Type | Notes |
|---|---|---|---|
| Sensor Employment Team (SET-A) | `040g` | sosa:Platform | Pre-existing |
| Monitoring Site Node 1 | `0410` | sosa:Platform | Pre-existing |
| Relay / Repeater 001 | `041g` | sosa:Platform | Pre-existing |
| ODAS Mic Array Node AZ-MA-1 | `0420` | sosa:System | Pre-existing |
| **ODAS Mic Array Node AZ-MA-2** | **`0490`** | sosa:System | **NEW** |
| **ODAS Mic Array Node AZ-MA-3** | **`049g`** | sosa:System | **NEW** |

### Subsystems (39 total: 13 × 3 nodes)

Each MA node has an identical set of 13 subsystems:

| Subsystem | Type | MA-1 ID | MA-2 ID | MA-3 ID |
|---|---|---|---|---|
| Tripod Platform | sosa:Platform | `042g` | `04a0` | `04gg` |
| MICARRAY | sosa:Sensor | `0430` | `04ag` | `04h0` |
| EDGE | sosa:Platform | `043g` | `04b0` | `04hg` |
| COMMS | sosa:Platform | `0440` | `04bg` | `04i0` |
| POWER | sosa:Platform | `044g` | `04c0` | `04ig` |
| ACTUATOR | sosa:Actuator | `0450` | `04cg` | `04j0` |
| MIC1 | sosa:Sensor | `045g` | `04d0` | `04jg` |
| MIC2 | sosa:Sensor | `0460` | `04dg` | `04k0` |
| MIC3 | sosa:Sensor | `046g` | `04e0` | `04kg` |
| MIC4 | sosa:Sensor | `0470` | `04eg` | `04l0` |
| MIC5 | sosa:Sensor | `047g` | `04f0` | `04lg` |
| MIC6 | sosa:Sensor | `0480` | `04fg` | `04m0` |
| MIC7 | sosa:Sensor | `048g` | `04g0` | `04mg` |

### Deployment Hierarchy (9 levels)

```
ICO (040g)
 └─ R&S (0410)
     └─ SSO (041g)  [deployedSystemUIDs: SET-A]
         └─ SNET (0420)  [deployedSystemUIDs: Mon Site, Relay]
             └─ Field 001 (042g)
                 └─ String Alpha (0430)
                     ├─ Node 1 — AZ-MA-1 (043g)  [platform@link → /systems/0420]
                     ├─ Node 2 — AZ-MA-2 (0440)  [platform@link → /systems/0490]  ← NEW
                     └─ Node 3 — AZ-MA-3 (044g)  [platform@link → /systems/049g]  ← NEW
```

### Datastreams (22 total: 1 SENREP + 7 × 3 nodes)

Each MA node has 7 identical datastream types with node-specific names and outputNames:

| Datastream Type | MA-1 ID | MA-2 ID | MA-3 ID |
|---|---|---|---|
| Classification Probabilities | `0430` | `0450` | `048g` |
| Health | `043g` | `045g` | `0490` |
| LOB | `0420` | `0460` | `049g` |
| Scene Summary | `0440` | `046g` | `04a0` |
| SSL Potential Sources | `0410` | `0470` | `04ag` |
| SST Tracked Sources | `041g` | `047g` | `04b0` |
| Track Updates | `042g` | `0480` | `04bg` |

SENREP datastream (`044g` on SET-A) unchanged.

### Control Streams (9 total: 3 × 3 nodes)

Each MA node's ACTUATOR subsystem hosts 3 control stream types:

| Control Stream | MA-1 ACTUATOR (`0450`) | MA-2 ACTUATOR (`04cg`) | MA-3 ACTUATOR (`04j0`) |
|---|---|---|---|
| ODAS Control | ✓ | ✓ | ✓ |
| Request Snapshot | ✓ | ✓ | ✓ |
| Start/Stop | ✓ | ✓ | ✓ |

---

## Implementation Approach

### Factory/Clone Pattern

Rather than triplicating hundreds of lines of inline data, a recursive
`_clone_for_node(obj, n)` utility was added to `bootstrap_v4.py`. It performs
deep-copy with string replacement:

- `az-ma-1` → `az-ma-{n}` (UIDs, descriptions)
- `AZ-MA-1` → `AZ-MA-{n}` (display names)
- `az_ma_1` → `az_ma_{n}` (outputNames, schema field names)

This allowed MA-2 and MA-3 definitions (subsystems, datastreams, control
streams) to be generated from MA-1's authoritative definitions in three lines
each.

### Coordinate Spacing

Nodes are spaced ~110m apart along a north-south line on String Alpha:

| Node | Position | Coordinates |
|---|---|---|
| AZ-MA-1 (Node 1) | North | `[-110.272897, 31.663006]` |
| AZ-MA-2 (Node 2) | Center | `[-110.272897, 31.662006]` |
| AZ-MA-3 (Node 3) | South | `[-110.272897, 31.661006]` |

Deployment node coordinates (inside the deployment tree) use the existing
String Alpha coordinate pattern (`-110.3441, 31.55xx`).

### Bootstrap Engine Updates

The following engine methods were generalized from single-node to multi-node:

| Method | Change |
|---|---|
| `clean()` | Iterates control stream deletion over all 3 ACTUATOR subsystems; iterates subsystem deletion over `ALL_MA_SUBSYSTEMS` |
| `create_subsystems()` | Iterates over `ALL_MA_SUBSYSTEMS` dict (parent UID → coord + defs) |
| `create_control_streams()` | Iterates over `ALL_CONTROL_STREAMS` (9 entries) |
| `verify()` | Checks all 3 nodes' platform@links; checks control stream counts on all 3 ACTUATORs; verifies all 39 subsystems |

### Data Aggregation

| Variable | Contents |
|---|---|
| `ALL_MA_SUBSYSTEMS` | Dict mapping 3 parent UIDs to (coord, subsystem_defs) |
| `ALL_DATASTREAMS` | List of 22 datastream definitions (SENREP + 7×3) |
| `ALL_CONTROL_STREAMS` | List of 9 control stream definitions (3×3) |

---

## Verification Results

### Live Run Summary (2026-03-02T20:20Z)

```
created=50  deleted=0  patched=0  skipped=36  errors=0
```

- **36 skips**: All pre-existing MA-1 resources correctly detected and preserved
- **50 creates**: All MA-2 and MA-3 resources provisioned successfully
- **0 errors**: No HTTP failures, no missing parent resources

### Post-Creation Verification (automated)

| Check | Result |
|---|---|
| 6 systems present | ✅ ALL OK |
| 39 subsystems present | ✅ ALL OK |
| 9 deployment nodes present | ✅ ALL OK |
| 22 datastreams present | ✅ ALL OK |
| 3/3/3 control streams per node | ✅ ALL OK |
| Node 1 platform@link → `/systems/0420` | ✅ OK |
| Node 2 platform@link → `/systems/0490` | ✅ OK |
| Node 3 platform@link → `/systems/049g` | ✅ OK |
| SNET deployedSystemUIDs | ✅ OK |

---

## Known Limitations

1. **No observations**: MA-2 and MA-3 datastreams are empty. Future data
   replay (via `scripts/replay.py` or equivalent) is required to populate them.

2. **`deployedSystems@link` not set on nodes**: OSH silently drops this field
   (documented in `OSH_DeployedSystems_Conformance_Probe.md`). The
   `platform@link` property is used as the deployment → system bridge instead.

3. **`deployment@link` not set on datastreams**: OSH silently drops this field
   (documented in `OSH_Deployment_Link_Persistence_Gap.md`). Datastream →
   deployment association is only inferrable client-side.

4. **Deployment-scoped endpoints return 400**: `/deployments/{id}/datastreams`
   and `/deployments/{id}/systems` are non-functional on OSH. System-scoped
   endpoints must be used instead.

---

## File Changes

| File | Change |
|---|---|
| `scripts/bootstrap_v4.py` | Extended with MA-2/MA-3 data (factory pattern), multi-node engine, updated docstring |

---

## Related Documents

| Document | Location |
|---|---|
| AZ-MA-2/MA-3 Migration Procedure Analysis | `OSHConnect-Python:docs/research/AZ-MA-2_MA-3_Migration_Procedure_Analysis.md` |
| CSAPI Deployment Modeling Standards Conformance | `OSHConnect-Python:docs/research/CSAPI_Deployment_Modeling_Standards_Conformance.md` |
| OSH DeployedSystems Conformance Probe | `OSHConnect-Python:docs/research/OSH_DeployedSystems_Conformance_Probe.md` |
| CSAPI Deployment Reparenting Feasibility | `OSHConnect-Python:docs/research/CSAPI_Deployment_Reparenting_Feasibility.md` |
| CSAPI Deployed Systems Design Pattern | `OSHConnect-Python:docs/research/CSAPI_Deployed_Systems_Design_Pattern.md` |
| CSAPI Deployment Semantics Analysis | `OSHConnect-Python:docs/research/CSAPI_Deployment_Semantics_Analysis.md` |
| OSH Deployment Link Persistence Gap | `OSHConnect-Python:docs/research/OSH_Deployment_Link_Persistence_Gap.md` |
