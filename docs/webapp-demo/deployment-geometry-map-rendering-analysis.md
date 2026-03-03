# Deployment Geometry Map Rendering Analysis

**Date:** 2026-03-02  
**Scope:** How deployment and subdeployment location geometry is resolved and drawn on the map view  
**File:** `demo/src/pages/MapViewPage.vue` — `enrichDeployments()` function  
**Status:** Problems identified & fixed — see §3 and §4  

---

## 1. Deployment Geometry Resolution Pipeline

The map view resolves deployment geometry through a multi-step pipeline inside `enrichDeployments()`, which runs **before** system or sampling feature enrichment.

### Step 1 — Fetch the Full Hierarchy

- Top-level deployments are fetched via `loadResourceType('deployments')` **without server-side bbox** filtering, because top-level deployments often have `geometry: null` — their locations are derived from children.
- `fetchSubdeployments()` recursively walks each top-level deployment's `/subdeployments` endpoint down to **depth 8**, collecting all nested items.
- Two relationship maps are built:
  - `childrenMap`: parent ID → array of child IDs
  - `parentMap`: child ID → parent ID

### Step 2 — Build System Location Lookup

- All systems are fetched (`/systems?limit=200`) to build a `uidToLocation` map (system UID → `{lon, lat}`).
- Location is sourced from the `systemLocationCache` (populated by observation datastreams) or the system's native GeoJSON geometry.

### Step 3 — Resolve Deployed System Locations

`getDeployedSystemLocations(item)` checks three link patterns in **priority order**:

| Priority | Property | Mechanism |
|----------|----------|-----------|
| 1 | `deployedSystems@link` | Array of hrefs → look up each system ID in `systemLocationCache` |
| 2 | `platform@link` | Single href → look up system ID in `systemLocationCache` |
| 3 | `deployedSystemUIDs` | Comma-separated UIDs → look up in `uidToLocation` map |

### Step 4 — Bottom-Up Centroid Resolution

`resolveCentroid(depId)` is a **recursive, memoized** function that determines each deployment's representative point. Rules are evaluated in order:

| Priority | Rule | Description |
|----------|------|-------------|
| **(a)** | Native geometry | If the deployment has its own GeoJSON geometry → use its centroid |
| **(b)** | Children + systems | Collect centroids of all direct subdeployments (recursively resolved) plus deployed system locations → compute average centroid |
| **(c)** | No physical anchor | No geometry — organizational containers are not drawn |

> **Pre-fix behavior (removed):** Rule (c) previously inherited the parent's centroid for empty leaf subdeployments, and Rule (d) returned null only for top-level nodes. This caused phantom dots and arbitrary LineStrings — see §3.

### Step 5 — Build Map Features (Two Passes)

**First pass** — Subdeployments with **native GeoJSON geometry**:
- Creates standard OpenLayers features via `createOlFeature()`.
- Applies current bbox filter.

**Second pass** — Deployments **without native geometry but with a direct system link** (`platform@link`, `deployedSystems@link`, or `deployedSystemUIDs`):
- Uses the resolved centroid from the linked system's location.
- Builds a `Point` geometry at that centroid.
- Styled via `getStyle('deployments', ...)` — applies STANAG mil-symbols for deployments that have `platform@link`.

> **Pre-fix behavior (removed):** The second pass previously drew ALL deployments without native geometry, collected child centroids + deployed system locations, and built either a `Point` (1 location) or `LineString` (multiple locations). Organizational parents with multiple children got meaningless lines connecting unrelated child positions in arbitrary API response order.

### Step 6 — Back-Fill System Location Cache

After all deployment centroids are resolved, iterates all items with `platform@link` and **overwrites** the `systemLocationCache` entry for that linked system with the deployment's resolved centroid (tagged `'deployment geometry'`). This ensures:
- `enrichSystems()` (which runs next) places systems at their deployment's location.
- Systems track their deployment when deployment geometry changes.

---

## 2. Sensor Field 001 Analysis

### Current Server State

```json
{
  "type": "Feature",
  "id": "042g",
  "geometry": null,
  "properties": {
    "uid": "urn:os4csapi:deployment:field:ft-huachuca:001",
    "featureType": "sosa:Deployment",
    "name": "Sensor Field 001",
    "description": "A defined lateral boundary containing sensor capabilities.",
    "validTime": ["2026-02-27T00:00:00Z", ".."]
  }
}
```

Key attributes:
- **`geometry`: `null`** — no native GeoJSON geometry
- **No `platform@link`** — not linked to any system
- **No `deployedSystems@link`** or `deployedSystemUIDs`
- **No subdeployments** — it is a leaf node (String Alpha was reparented out)
- **Parent:** SNET (`0420`)

### Resolution Trace

Walking through `resolveCentroid('042g')`:

| Rule | Evaluation | Result |
|------|-----------|--------|
| **(a)** Native geometry | `geometry: null` | Skipped |
| **(b)** Children + systems | `childrenMap['042g']` is empty, no deployed system links | 0 points — skipped |
| **(c)** Inherit parent | Parent is SNET (`0420`). SNET also has `geometry: null` and no `platform@link`, but SNET **does** have children (Field 001, String Alpha, Mon Site Emplacement, Relay Emplacement, SET-A Emplacement). SNET's centroid is the average of its children's resolved centroids — which are the Node 1/2/3 + Mon Site + Relay + SET-A locations. | **Inherits SNET's centroid** |
| **(d)** Nothing | Not reached — rule (c) applies | — |

### Map Representation (Post-Fix)

Field 001 is **no longer drawn on the map**. It has no native geometry, no `platform@link`, no children — there is no meaningful geographic location to plot.

> **Pre-fix behavior:** Field 001 was drawn as a single green Point at the average centroid of all SNET's resolvable children (inherited via rule c). This was a meaningless position.

### Current Oracle Deployment Hierarchy (Post-Reparent)

```
Deployments (12):
  ICO (040g) → R&S (0410) → SSO (041g)
    ├── SET-A Emplacement (0450) → platform@link → SET-A
    └── SNET (0420)
        ├── Mon Site Emplacement (045g) → platform@link → Mon Site
        ├── Relay Emplacement (0460) → platform@link → Relay
        ├── Field 001 (042g)  ← leaf node, no children, no geometry
        └── String Alpha (046g)
            ├── Node 1 (0470) → platform@link → AZ-MA-1
            ├── Node 2 (047g) → platform@link → AZ-MA-2
            └── Node 3 (0480) → platform@link → AZ-MA-3
```

---

## 3. Problems Identified

Three interrelated rendering problems were identified from map inspection:

### Problem 1 — Field 001 "Ghost" Dot

Field 001 is a leaf node with `geometry: null`, no `platform@link`, no children, no deployed systems. It has **zero** geographic meaning. But rule (c) in `resolveCentroid` said "if you're a leaf with no data, inherit your parent's centroid." So it was placed at SNET's averaged centroid — a meaningless spot on the map.

### Problem 2 — SNET Arbitrary LineString

SNET had 5 children with resolved centroids (Field 001's inherited point, String Alpha's averaged point, Mon Site, Relay, SET-A). Since there were multiple unique points, the code constructed a `LineString` connecting them **in whatever order the API returned them**. The green line went off in one direction and abruptly stopped — it was the last point in the array. There was no geographic logic to it.

### Problem 3 — Cascade Up the Entire Hierarchy

ICO → R&S → SSO all inherited from their children the same way. Every organizational level got an increasingly aggregated (and increasingly meaningless) LineString or averaged point. The whole tree of abstract containers polluted the map with visual noise.

### Root Causes

Two rules in the enrichment logic caused all of this:

1. **Rule (c) — parent centroid inheritance**: Empty leaf deployments inherited their parent's centroid, creating phantom dots for deployments with no physical presence.
2. **Multi-point → LineString**: When a deployment resolved multiple child centroids, it drew a `LineString` connecting them in API response order — treating organizational groupings as geographic paths.

---

## 4. Fix Applied

**Commit:** `bce90f7` on `main`

### Changes to `resolveCentroid()`

- **Removed rule (c)** entirely — no more parent centroid inheritance.
- If a deployment has no native geometry AND no children/deployed systems with locations, `resolveCentroid` returns `null`. The deployment is simply not drawn.

### Changes to Second Pass (Derived Geometry Building)

- **Added a system-link gate**: Only deployments with a direct physical anchor are considered:
  - `platform@link` (href to a system)
  - `deployedSystems@link` (array of system hrefs)
  - `deployedSystemUIDs` (comma-separated system UIDs)
- Deployments without any of these links are **skipped entirely** — they're organizational containers.
- The geometry is always a `Point` at the resolved centroid (no more `LineString` construction from multiple child points).
- Removed the now-unused `dedup()` helper function.

### Effect on Each Deployment

| Deployment | Has geometry? | Has `platform@link`? | Drawn? | Reason |
|---|---|---|---|---|
| Node 1 (0470) | no | **yes** → AZ-MA-1 | **Yes** | Physical emplacement |
| Node 2 (047g) | no | **yes** → AZ-MA-2 | **Yes** | Physical emplacement |
| Node 3 (0480) | no | **yes** → AZ-MA-3 | **Yes** | Physical emplacement |
| Mon Site Emp (045g) | no | **yes** → Mon Site | **Yes** | Physical emplacement |
| Relay Emp (0460) | no | **yes** → Relay | **Yes** | Physical emplacement |
| SET-A Emp (0450) | no | **yes** → SET-A | **Yes** | Physical emplacement |
| String Alpha (046g) | no | no | **No** | Organizational (nodes still drawn) |
| Field 001 (042g) | no | no | **No** | Empty leaf, no location |
| SNET (0420) | no | no | **No** | Organizational container |
| SSO (041g) | no | no | **No** | Organizational container |
| R&S (0410) | no | no | **No** | Organizational container |
| ICO (040g) | no | no | **No** | Organizational container |

### Trade-off

String Alpha's connecting line between Node 1/2/3 is gone. But that line was drawn in arbitrary API response order — it was not a geographically meaningful path. If an area or path representation is needed in the future, actual native geometry (a Polygon boundary or ordered LineString) can be set on the server through the Update form.
