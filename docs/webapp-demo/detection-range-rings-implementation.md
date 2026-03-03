# Detection Range Rings — Implementation Report

**Date:** 2026-03-02  
**Branch:** `main` (commit `37f204f`)  
**Feature:** MIL-STD-2525E Weapon/Sensor Range Fan (Circular) for AZ-MA acoustic nodes  

---

## 1. Summary

Added a toggleable "Detection Ranges" overlay to the CSAPI Explorer map view that draws concentric geodesic circle polygons around deployment emplacements whose linked systems have known detection range configurations. Styled per MIL-STD-2525E Appendix L, TABLE L-XVII — Weapon/Sensor Range fan, Circular (Symbol Set 25, Value 242100).

---

## 2. Background

### 2.1 STANAG 2525E Reference

The MIL-STD-2525E standard defines a **Weapon/Sensor Range fan, Circular** tactical graphic:

| Field | Value |
|-------|-------|
| Type | Entity Type |
| Entity | Fire Area |
| Symbol Set | 25 |
| Value | 242100 |
| Draw Rules | Circular2 — Dynamic |

The template specifies:
- **Anchor point** centered over the known location of a weapon or sensor system
- **MIN RG** — Minimum range with altitude
- **MAX RG(1)** — First maximum range with altitude
- **MAX RG(2)** — Second maximum range with altitude
- Concentric circles, increasing radius outward

### 2.2 Design Decision — Approach Selection

Three approaches were evaluated:

| Option | Description | Chosen? |
|--------|-------------|---------|
| **A — Pure client-side OL layer** | Hardcoded ranges, drawn as OL geodesic polygons | ✅ **Implemented** |
| **B — CSAPI property-driven** | Store `detectionRange` as a custom property on the system resource | ❌ Server strips unknown properties |
| **C — Full 2525E tactical graphic** | Use the actual Symbol Set 25/242100 multi-point renderer | ❌ `milsymbol` only supports single-point icons |

**Option B was attempted first.** The detection range schema was PUT onto all three AZ-MA system resources (0420, 0490, 049g) via the Oracle server API. The server accepted the PUT (HTTP 204) but **silently discarded** the `detectionRange` property — OSH SensorHub only persists known SWE/SOS schema fields. Subsequent GET returned the property as `null`.

**Option A was implemented** with a client-side config map keyed by system UID. The config uses the same JSON schema proposed for Option B, so when OSH gains custom property support, the migration is trivial: read from `props.detectionRange` instead of the config map.

---

## 3. Detection Range Schema

```json
{
  "detectionRange": {
    "shape": "circular",
    "rings": [
      { "label": "min",     "radius_m": 250 },
      { "label": "nominal", "radius_m": 1500 },
      { "label": "max",     "radius_m": 3000 }
    ],
    "altitude": { "min_m": 0, "max_m": null, "ref": "AGL" },
    "confidence": 0.7,
    "basis": "estimated",
    "asOf": "2026-03-02T18:00:00Z"
  }
}
```

### Schema Fields

| Field | Type | Description |
|-------|------|-------------|
| `shape` | string | Geometry type (`"circular"` for now; `"sector"` reserved for directional fans) |
| `rings` | array | Ordered list of concentric rings |
| `rings[].label` | string | Ring identifier: `"min"`, `"nominal"`, `"max"` |
| `rings[].radius_m` | number | Radius in meters from anchor point |
| `altitude.min_m` | number | Minimum detection altitude in meters |
| `altitude.max_m` | number \| null | Maximum detection altitude (`null` = unlimited) |
| `altitude.ref` | string | Altitude reference frame: `"AGL"`, `"MSL"`, `"HAE"` |
| `confidence` | number | Probability of detection at nominal range (0–1) |
| `basis` | string | `"estimated"`, `"measured"`, `"manufacturer"` |
| `asOf` | ISO 8601 | Timestamp when range data was last validated |

### Design Rationale

- **`radius_m`** not `r` — Self-documenting, unambiguous units
- **Stored on the system, not the deployment** — Detection range is an inherent sensor capability. If the sensor redeploys, the range travels with the system. The deployment just provides the anchor location via `platform@link`.
- **`altitude` kept even though 2D map can't render it** — Useful in popups, tooltips, and SENREP context
- **`confidence` and `basis`** — Metadata for analysts, displayed in feature info popups

---

## 4. Implementation Details

### 4.1 Architecture

```
System (AZ-MA-1)                    Deployment (Node 1 Emplacement)
  └─ detectionRange config    ←──   platform@link.uid ──→ system UID
      (client-side map)             (provides anchor point)
```

The rendering flow:
1. After `enrichDeployments()` resolves all deployment geometry
2. `buildDetectionRanges()` iterates deployment features on the map
3. For each deployment with `platform@link`, resolves the linked system UID
4. Looks up `DETECTION_RANGE_CONFIGS[systemUid]`
5. If found, draws geodesic circle polygons at the deployment's coordinates

### 4.2 Rendering

| Ring | Radius | Dash Pattern | Fill Alpha | Stroke Width |
|------|--------|-------------|------------|-------------|
| MIN | 250m | `[4, 4]` | 0.12 | 1.5 |
| NOMINAL | 1500m | `[8, 6]` | 0.07 | 1.5 |
| MAX | 3000m | `[12, 8]` | 0.04 | 1.0 |

- **Color:** `#60a5fa` (friendly blue per 2525E conventions)
- **Geometry:** `ol/geom/Polygon.circular([lon, lat], radius_m, 64)` — true geodesic circles, 64 vertices
- **Projection:** Created in EPSG:4326, transformed to EPSG:3857 for display
- **Labels:** `"{LABEL} {radius}m"` placed at north pole of each ring

### 4.3 Layer Configuration

| Property | Value |
|----------|-------|
| Layer key | `detectionRanges` |
| z-index | 3 (below tracks at 5, below features at 10) |
| Default visibility | OFF |
| Sidebar section | "Overlays" (new section below Part 2) |

### 4.4 Files Modified

| File | Changes |
|------|---------|
| `demo/src/pages/MapViewPage.vue` | +174 lines: config, layer, render function, sidebar toggle |

### 4.5 Systems Covered

| System UID | System Name | Deployment Anchor |
|-----------|-------------|------------------|
| `urn:os4csapi:system:odas:az-ma-1` | ODAS Mic Array Node AZ-MA-1 | Node 1 — AZ-MA-1 (0470) |
| `urn:os4csapi:system:odas:az-ma-2` | ODAS Mic Array Node AZ-MA-2 | Node 2 — AZ-MA-2 (047g) |
| `urn:os4csapi:system:odas:az-ma-3` | ODAS Mic Array Node AZ-MA-3 | Node 3 — AZ-MA-3 (0480) |

All three share the same detection range values (250m / 1500m / 3000m).

---

## 5. OSH Server Limitation — Custom Properties

### 5.1 Attempted Server Storage

```
PUT /sensorhub/api/systems/{id}
Content-Type: application/json

{
  "properties": {
    ... existing fields ...,
    "detectionRange": { ... }
  }
}
```

- **Response:** HTTP 204 (accepted)
- **Subsequent GET:** `detectionRange` is absent — silently stripped

### 5.2 Root Cause

OSH SensorHub persists only known schema fields for system resources:
- `uid`, `featureType`, `name`, `description`, `validTime`

Any additional properties are discarded during write. This is a server-side schema constraint, not a CSAPI specification limitation.

### 5.3 Migration Path

When OSH adds support for custom properties (or an extension mechanism):
1. PUT the `detectionRange` JSON onto each system resource
2. In `buildDetectionRanges()`, replace the `DETECTION_RANGE_CONFIGS[uid]` lookup with:
   ```ts
   const sysProps = systemData.properties || {}
   const config = sysProps.detectionRange || DETECTION_RANGE_CONFIGS[uid]
   ```
3. Remove the client-side config entries as systems gain server-stored ranges

Zero rendering code changes required.

---

## 6. Future Extensions

| Feature | Approach |
|---------|----------|
| **Directional sensor fans** | Add `shape: "sector"` with `azimuth_deg` and `beamwidth_deg` fields; render as polygon sector |
| **Per-ring altitude labels** | Display `ALT {min_m}` on each ring (2525E spec supports this) |
| **Dynamic ranges from observations** | Read actual detection events to compute empirical range rings |
| **Range ring popup** | Click a ring to see confidence, basis, altitude, and last-validated timestamp |
| **Multiple ring colors** | Vary intensity by confidence level |
| **3D rendering** | When a 3D globe view is added (Cesium/CesiumJS), render as cylinders or domes using altitude data |

---

## 7. Related Reports

- [deployment-geometry-map-rendering-analysis.md](deployment-geometry-map-rendering-analysis.md) — Deployment rendering pipeline, ghost dot fixes, platform@link gate
