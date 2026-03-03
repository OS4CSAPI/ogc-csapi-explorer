# Bootstrap v4 — Live Server Sync Report

**Date:** 2026-03-02  
**Commit:** `b802344` (main)  
**Branch:** `main`  
**Author:** Copilot + sbolling

## Summary

Synchronized `scripts/bootstrap_v4.py` against the perfected data model running on the live Oracle OSH server (`os4csapi-osh.duckdns.org`). The bootstrap script is the authoritative single-source-of-truth for recreating the entire server state from scratch — it must match the live server exactly.

## Audit Method

1. Queried all systems via `GET /systems?limit=100`
2. Queried top-level deployments via `GET /deployments?limit=100`
3. Recursively walked the full deployment tree via `/subdeployments`
4. Fetched full GeoJSON for every deployment (12 resources) and every system (6 resources)
5. Compared each field (uid, name, description, geometry, properties, validTime) against `bootstrap_v4.py`

## Live Server Inventory

### Systems (6 top-level)

| Server ID | UID | Name | featureType | Geometry |
|-----------|-----|------|-------------|----------|
| `040g` | `urn:os4csapi:system:set:ft-huachuca:001` | Sensor Employment Team (SET-A) | sosa:Platform | Point: -110.2524769, 31.6380757 |
| `0410` | `urn:os4csapi:system:monitoring-site-node:ft-huachuca:001` | Monitoring Site Node 1 | sosa:Platform | Point: -110.2525675, 31.6383956 |
| `041g` | `urn:os4csapi:system:relay:vhf-repeater:ft-huachuca:001` | Relay / Repeater 001 | sosa:Platform | Point: -110.2554653, 31.6429133 |
| `0420` | `urn:os4csapi:system:odas:az-ma-1` | ODAS Mic Array Node AZ-MA-1 | sosa:System | Point: -110.272897, 31.663006 |
| `0490` | `urn:os4csapi:system:odas:az-ma-2` | ODAS Mic Array Node AZ-MA-2 | sosa:System | Point: -110.272897, 31.662006 |
| `049g` | `urn:os4csapi:system:odas:az-ma-3` | ODAS Mic Array Node AZ-MA-3 | sosa:System | Point: -110.272897, 31.661006 |

### Subsystems (39 total: 13 per MA node)

Each AZ-MA-{n} has identical subsystem structure:
- `{n} Tripod Platform` (sosa:Platform)
- `{n} MICARRAY` (sosa:Sensor)
- `{n} EDGE` (sosa:Platform)
- `{n} COMMS` (sosa:Platform)
- `{n} POWER` (sosa:Platform)
- `{n} ACTUATOR` (sosa:Actuator)
- `{n} MIC1` – `{n} MIC7` (sosa:Sensor × 7)

### Deployment Hierarchy

```
ICO (040g) — Intelligence Collection Operation (derived from ICP)
  └── R&S (0410) — Reconnaissance and Surveillance Operation
        └── SSO (041g) — Sensor Surveillance Operation (derived from SSP)
              │   geometry: LineString  |  deployedSystemUIDs: SET-A
              ├── SET-A (0450) — SET-A
              │     geometry: Point(-110.2524769, 31.6380757)
              │     platform@link → system:set:ft-huachuca:001
              └── SNET (0420) — Sensor Network
                    │   geometry: null  |  deployedSystemUIDs: Mon Site, Relay
                    ├── Field 001 (042g) — Sensor Field 001  [leaf, no geometry]
                    ├── Mon Site Emplacement (045g)
                    │     geometry: Point(-110.2525675, 31.6383956)
                    │     platform@link → system:monitoring-site-node:ft-huachuca:001
                    ├── Relay Emplacement (0460)
                    │     geometry: Point(-110.2554653, 31.6429133)
                    │     platform@link → system:relay:vhf-repeater:ft-huachuca:001
                    └── Sensor String Alpha (046g)
                          ├── Node 1 — AZ-MA-1 (0470)
                          │     geometry: Point(-110.2758537, 31.6490196)
                          │     platform@link → system:odas:az-ma-1
                          ├── Node 2 — AZ-MA-2 (047g)
                          │     geometry: Point(-110.2659979, 31.6569236)
                          │     platform@link → system:odas:az-ma-2
                          └── Node 3 — AZ-MA-3 (0480)
                                geometry: Point(-110.2515496, 31.6637961)
                                platform@link → system:odas:az-ma-3
```

### Datastreams (22 total)

| System | Count | Streams |
|--------|-------|---------|
| SET-A (`040g`) | 1 | SENREP |
| AZ-MA-1 (`0420`) | 7 | LOB, SSL Potential Sources, SST Tracked Sources, Track Updates, Classification Probabilities, Health, Scene Summary |
| AZ-MA-2 (`0490`) | 7 | (same schema, cloned) |
| AZ-MA-3 (`049g`) | 7 | (same schema, cloned) |

### Control Streams (9 total)

Each AZ-MA-{n}: ODAS Control, Request Snapshot, Start Stop (3 × 3 nodes)

## Differences Found & Corrected

| # | Field | Old (bootstrap_v4.py) | New (live server) | Impact |
|---|-------|----------------------|-------------------|--------|
| 1 | SET-A emplacement name | `SET-A Emplacement` | `SET-A` | Display name in Explorer |
| 2 | SNET deployment name | `Sensor Network/Net Deployment` | `Sensor Network` | Display name |
| 3 | SNET geometry | `LineString [Mon Site → Relay]` | `null` | Eliminates phantom line on map |
| 4 | String Alpha name | `Sensor String Alpha (line-of-emplacement)` | `Sensor String Alpha` | Display name |
| 5 | Node 1 deployment coords | `[-110.272897, 31.663006]` | `[-110.2758537, 31.6490196]` | Map position (~2.3 km shift) |
| 6 | Node 2 deployment coords | `[-110.272897, 31.662006]` | `[-110.2659979, 31.6569236]` | Map position (~1.9 km shift) |
| 7 | Node 3 deployment coords | `[-110.272897, 31.661006]` | `[-110.2515496, 31.6637961]` | Map position (~2.4 km shift) |

### Items Already Correct (no changes needed)

- All 6 system UIDs, names, descriptions, featureTypes, coordinates, validTimes ✓
- All 39 subsystem definitions ✓
- All 22 datastream schemas (SENREP + 7×3 MA streams) ✓
- All 9 control stream schemas ✓
- All deployment UIDs, descriptions, validTimes ✓
- `platform@link` references on all 6 emplacement nodes ✓
- `deployedSystemUIDs` on SSO and SNET ✓
- SSO LineString geometry ✓
- ICO and R&S centroid geometry ✓

## Inter-Node Distance Analysis

The live node coordinates form a non-linear arc (not a straight line as in the old bootstrap):

| Pair | Distance | Bearing |
|------|----------|---------|
| Node 1 ↔ Node 2 | ~1,283 m | NE |
| Node 2 ↔ Node 3 | ~1,569 m | NE |
| Node 1 ↔ Node 3 | ~2,735 m | NE |

This explains why the detection range rings (sized at 65m in a prior commit based on the old 111m spacing) were invisible — the actual spacing is 10–25× larger.

## Related Commits (this session)

| Commit | Description |
|--------|-------------|
| `37f204f` | feat: add detection range rings for AZ-MA sensor nodes |
| `4416f66` | UX: scale detection ranges, click-to-deselect, enter-key connect |
| `49adc50` | UX: resize detection ranges for overlap, default ON |
| `14925e6` | UX: make detection rings permanently visible, non-selectable |
| `d6b0050` | fix: detection ranges sized to actual server coordinates (900m outer) |
| `b802344` | **bootstrap_v4: sync with live Oracle server data model** |
