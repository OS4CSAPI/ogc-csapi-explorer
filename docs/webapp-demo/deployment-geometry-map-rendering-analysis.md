# Deployment Geometry Map Rendering Analysis

**Date:** 2026-03-02  
**Scope:** How deployment and subdeployment location geometry is resolved and drawn on the map view  
**File:** `demo/src/pages/MapViewPage.vue` — `enrichDeployments()` function  

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
| **(c)** | Inherit parent | Leaf subdeployment with no children or systems → inherits the parent deployment's centroid |
| **(d)** | Nothing | Top-level with no data → no geometry (not drawn on map) |

### Step 5 — Build Map Features (Two Passes)

**First pass** — Subdeployments with **native GeoJSON geometry**:
- Creates standard OpenLayers features via `createOlFeature()`.
- Applies current bbox filter.

**Second pass** — Deployments **without native geometry**:
- For each, collects direct subdeployment centroids + deployed system locations.
- If still empty, inherits parent centroid (leaf subdeployment rule).
- Deduplicates points within ~0.00001°.
- Builds OL geometry:
  - **1 unique point** → `Point`
  - **Multiple unique points** → `LineString` connecting the locations
- Styled via `getStyle('deployments', ...)` — applies STANAG mil-symbols for deployments that have `platform@link`, plain green dot otherwise.

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

### Map Representation

Field 001 is drawn as a **single green Point** at the average centroid of all resolvable locations under SNET. This is effectively a meaningless inherited position — the geographic center of all SNET's children — since Field 001 itself has:
- No geometry of its own
- No linked system
- No children

The marker is a plain green deployment dot (no STANAG mil-symbol, due to the absence of `platform@link`).

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
