# Hierarchical Navigation for Subsystems & Subdeployments

## Background — Senior Dev Feedback

During a review of the CSAPI Explorer demo webapp, a senior developer identified a significant gap: **subsystems and subdeployments were entirely missing from the demo**. The webapp presented all 9 CSAPI resource types as flat, top-level collections only, with no way to navigate the parent–child hierarchies that are central to the Connected Systems API specification.

This is a critical omission because:

- **Systems** in CSAPI are inherently hierarchical — a weather station (parent system) may contain a thermometer, barometer, and anemometer as subsystems
- **Deployments** are similarly nested — a field campaign may contain regional sub-deployments
- The ability to browse `GET /systems/{id}/subsystems` and `GET /deployments/{id}/subdeployments` is a core CSAPI capability that distinguishes it from flat OGC API endpoints
- Without hierarchical navigation, the demo fails to exercise a significant portion of the library's API surface

---

## Investigation — Gap Audit

### Library Support (Fully Present)

An audit of the `ogc-client` library's `CSAPIQueryBuilder` (`src/ogc-api/csapi/url_builder.ts`) confirmed **complete support** for nested resource navigation. The builder exposes 10+ methods for hierarchical traversal:

| Builder Method | URL Pattern | Description |
|---|---|---|
| `getSystemSubsystems(id)` | `/systems/{id}/subsystems` | Child systems of a system |
| `getSystemDataStreams(id)` | `/systems/{id}/datastreams` | Datastreams belonging to a system |
| `getSystemControlStreams(id)` | `/systems/{id}/controlstreams` | Control streams belonging to a system |
| `getSystemSamplingFeatures(id)` | `/systems/{id}/samplingFeatures` | Sampling features of a system |
| `getSystemDeployments(id)` | `/systems/{id}/deployments` | Deployments associated with a system |
| `getSystemProcedures(id)` | `/systems/{id}/procedures` | Procedures implemented by a system |
| `getDeploymentSubdeployments(id)` | `/deployments/{id}/subdeployments` | Child deployments of a deployment |
| `getDeploymentSystems(id)` | `/deployments/{id}/systems` | Systems involved in a deployment |

All methods accept typed query options (e.g., `SystemQueryOptions`, `DeploymentQueryOptions`) and produce correctly formatted URLs with query parameters.

Additionally, the library's `SystemQueryOptions` and `DeploymentQueryOptions` interfaces include `parent` and `recursive` query parameters that were never exercised by the demo. These relate to existing GitHub issues:

- **Issue #24** — `parent` query parameter not exercised
- **Issue #25** — Subsystem/Subdeployment hierarchical navigation not demonstrated

### Webapp Support (Zero — Before This Work)

The audit confirmed the demo webapp had **zero support** for hierarchical navigation:

- Only 9 flat top-level resource types defined in `RESOURCE_TYPES` (state.ts)
- `csapi-bridge.ts` only dispatched to flat collection methods (`getSystems()`, `getDeployments()`, etc.)
- `ResourceList.vue` only called `getListUrl()` for top-level collections
- `ResourceDetail.vue` showed raw JSON and parsed output but no links to related/child resources
- `ResourceExplorerPage.vue` sidebar listed the 9 types with no nesting
- The only nesting the UI acknowledged was create-time parent IDs for observations (→ datastream) and commands (→ control stream)

---

## Implementation — Hierarchical Navigation Feature

**Commit:** `8ee5ecb` — `feat: add hierarchical navigation for subsystems and subdeployments`

### Architecture Decision

Used **route query parameters** rather than new routes to carry nested context:

```
/explore/{childType}?parentType=X&parentId=Y&relation=Z
```

This approach reuses the existing `ResourceList` rendering pipeline — the only difference is the URL source switches from `getListUrl()` to `getNestedListUrl()` when parent context is present. No new routes, pages, or components were needed.

### Files Modified (6 files, +216 lines)

#### 1. `demo/src/state.ts` — Related Resource Definitions

Added `RelatedResourceLink` interface and `RELATED_RESOURCES` record:

```typescript
export interface RelatedResourceLink {
  childType: string    // e.g., 'systems' for subsystems
  label: string        // Button text: 'Subsystems'
  icon: string         // PrimeIcons class
  relation: string     // URL segment: 'subsystems'
}

export const RELATED_RESOURCES: Record<string, RelatedResourceLink[]> = {
  systems: [
    { childType: 'systems',          label: 'Subsystems',         icon: 'pi pi-sitemap',     relation: 'subsystems' },
    { childType: 'datastreams',      label: 'Datastreams',        icon: 'pi pi-chart-line',  relation: 'datastreams' },
    { childType: 'controlStreams',   label: 'Control Streams',    icon: 'pi pi-sliders-h',   relation: 'controlstreams' },
    { childType: 'samplingFeatures', label: 'Sampling Features',  icon: 'pi pi-map-marker',  relation: 'samplingFeatures' },
    { childType: 'deployments',      label: 'Deployments',        icon: 'pi pi-map',         relation: 'deployments' },
    { childType: 'procedures',       label: 'Procedures',         icon: 'pi pi-cog',         relation: 'procedures' },
  ],
  deployments: [
    { childType: 'deployments', label: 'Subdeployments',   icon: 'pi pi-sitemap', relation: 'subdeployments' },
    { childType: 'systems',     label: 'Deployed Systems', icon: 'pi pi-server',  relation: 'systems' },
  ],
}
```

Systems get **6 child relations**; deployments get **2**.

#### 2. `demo/src/csapi-bridge.ts` — Nested URL Builder

Added `getNestedListUrl()` function that dispatches to the correct library builder method:

```typescript
export function getNestedListUrl(
  parentType: string, parentId: string, relation: string, options?: QueryOptions
): string {
  // parentType='systems', relation='subsystems' → b.getSystemSubsystems(parentId, options)
  // parentType='deployments', relation='subdeployments' → b.getDeploymentSubdeployments(parentId, options)
  // ... etc. for all 8 supported relations
}
```

This is the critical bridge between the UI's query-param-based navigation and the library's typed builder methods — it validates that the library produces correct nested URLs end-to-end.

#### 3. `demo/src/components/ResourceDetail.vue` — Related Resources Button Bar

When viewing a system or deployment detail, a styled button bar now appears above the side-by-side JSON/parsed panels:

- **"Related Resources"** header with sitemap icon
- One button per relation (e.g., "Subsystems", "Datastreams", "Control Streams")
- Clicking navigates to `/explore/{childType}?parentType=X&parentId=Y&relation=Z`

#### 4. `demo/src/pages/ResourceExplorerPage.vue` — Nested Context & Breadcrumb

- Reads `parentType`, `parentId`, `relation` from `route.query`
- Shows a breadcrumb bar when in nested mode: **"← Back to top-level | System abc123 → subsystems"**
- Passes parent context as props to `ResourcePanel`
- Component `:key` includes parent context to force re-render on navigation

#### 5. `demo/src/components/ResourcePanel.vue` — Prop Threading

Accepts `parentType`, `parentId`, `parentRelation` props and forwards them to `ResourceList`.

#### 6. `demo/src/components/ResourceList.vue` — Nested URL Dispatch

- Added `isNested` computed and `buildListUrl()` helper
- When parent context exists, `buildListUrl()` calls `getNestedListUrl()` instead of `getListUrl()`
- Both `fetchResources()` and `fetchTotalCount()` use the unified helper
- Watcher reacts to parent context changes (not just resource type)

### User Flow

```
1. Connect to server (e.g., OSH SensorHub)
2. Navigate to Systems → List tab
3. Click eye icon on a system to view its Detail
4. See "Related Resources" button bar with Subsystems, Datastreams, etc.
5. Click "Subsystems"
6. URL changes to /explore/systems?parentType=systems&parentId=X&relation=subsystems
7. Breadcrumb bar appears: "← Back to top-level | System X → subsystems"
8. ResourceList fetches /systems/X/subsystems via library builder
9. Results show child systems; click any to view their detail (and drill deeper)
```

### Library Methods Now Exercised

| Method | Previously Exercised | Now Exercised |
|---|---|---|
| `getSystemSubsystems()` | No | **Yes** |
| `getSystemDataStreams()` | No | **Yes** |
| `getSystemControlStreams()` | No | **Yes** |
| `getSystemSamplingFeatures()` | No | **Yes** |
| `getSystemDeployments()` | No | **Yes** |
| `getSystemProcedures()` | No | **Yes** |
| `getDeploymentSubdeployments()` | No | **Yes** |
| `getDeploymentSystems()` | No | **Yes** |

This brings the total library API surface exercised by the demo to **8 additional builder methods** beyond the flat CRUD operations.

---

## Related Issues

| GitHub Issue | Status | Relevance |
|---|---|---|
| #24 — `parent` query parameter not exercised | Open | Related but distinct — `parent` filters top-level collections by parent ID; this feature navigates nested endpoints directly |
| #25 — Subsystem/Subdeployment hierarchical navigation | Open | **Directly addressed** by this implementation |

---

## Build Verification

- `vue-tsc --noEmit` — clean (zero type errors)
- `vite build` — successful (585 modules, 5.58s)
- Production bundle: 1,374 KB JS / 51 KB CSS (unchanged from before — no new dependencies)
