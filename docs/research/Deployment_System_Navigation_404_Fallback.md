# Deployment → Systems Navigation: 404 Fallback via `platform@link`

**Date:** 2026-05-10  
**Status:** Fixed — deployed to production  
**Commits:** `2dae09f`, `e639ad7` (`OS4CSAPI/ogc-csapi-explorer`); `b662445`, `d512d60` (`OS4CSAPI/OSHConnect-Python`)  
**Affects:** All deployments with a linked system; all publishers

---

## 1. Summary

Navigating to the Systems sub-resource of any leaf deployment (e.g., clicking
"systems" in the deployment detail panel, or loading
`/explore/systems?parentType=deployments&parentId={id}&relation=systems`)
produced a persistent `404 : 404 page not found` error. The underlying cause
was that `csapi-go-v2` does not implement the nested sub-resource endpoint
`GET /deployments/{id}/systems`. The fix adds a client-side fallback in the
Explorer that resolves the linked system(s) directly from the deployment's
`platform@link` (or `deployedSystems@link`) inline property instead of relying
on the unimplemented endpoint.

---

## 2. Background

OGC API — Connected Systems Part 1 (OGC 23-001) defines a hierarchy of
navigable sub-resource endpoints. For deployments, Table 43 lists:

| Path | Description |
|------|-------------|
| `GET /deployments/{id}/systems` | Systems deployed within this deployment |
| `GET /deployments/{id}/subdeployments` | Child deployments |
| `GET /deployments/{id}/samplingFeatures` | Sampling features |

In parallel, the standard also defines inline properties that carry the same
association without requiring a server-side endpoint:

| Property | Description |
|----------|-------------|
| `platform@link` | Link to the single system this deployment is a mission for |
| `deployedSystems@link[]` | Array of links to all deployed systems |

`csapi-go-v2` implements the top-level collections and inline properties but
does **not** implement the nested navigation paths. This is a valid partial
implementation under the spec, but the Explorer treated the absence as an
unrecoverable error.

---

## 3. Root Cause Analysis

### 3.1 Two separate code paths — only one was patched initially

The Explorer has two places that load systems in the context of a deployment:

1. **`ResourceDetail.vue` — inline relations panel** (`fetchRelation()` /
   `resolveDeployedSystemsInline()`). Called when a deployment record is
   open in the Detail tab and the "systems" relation is expanded inline.

2. **`ResourceList.vue` — List tab** (`fetchResources()` /
   `buildListUrl()`). Called when `ResourceList` is rendered with
   `parentType=deployments`, `parentRelation=systems`, and a `parentId`.
   This is the component that drives the List tab in `ResourcePanel`, and
   it is also what renders when the user is routed to
   `/explore/systems?parentType=deployments&parentId=...&relation=systems`.

The initial fix (`2dae09f`) added `resolveDeployedSystemsInline` only in
`ResourceDetail.vue`. `ResourceList.vue` had no fallback and surfaced the
404 directly.

### 3.2 URL construction for the List path

`ResourceList.buildListUrl()` calls:

```ts
getNestedListUrl(props.parentType!, props.parentId!, props.parentRelation!, options)
```

which dispatches to `b.getDeploymentSystems(parentId, options)` in
`csapi-bridge.ts`, returning `/deployments/{id}/systems`. This hits the
unimplemented endpoint and returns 404.

### 3.3 `platform@link.href` format inconsistency across publishers

A secondary issue was discovered during the NDBC hierarchy repair. The
bootstrap scripts for all publishers stored a bare UUID as
`platform@link.href`:

```json
"platform@link": { "href": "04og", "rel": "...", "title": "..." }
```

This is not standards-conformant — OGC API links should use resolvable URIs.
The NDBC bootstrap was updated to build an absolute URL
(`base_url + '/systems/' + uuid`). All other publishers still emit bare UUIDs
and were not updated in this sprint. The Explorer fallback handles both forms
via `normalizeLinkHrefForList()`.

### 3.4 Deployment hierarchy breakage (side effect of earlier fix)

An intermediate repair attempt used `PUT /deployments/{id}` to update the
`platform@link.href` values on the NDBC station deployments. The csapi-go-v2
server's PUT handler strips the `ogc-rel:parentDeployment` link from the
resource on write, silently orphaning the child deployment. This converted
the five NDBC station sub-deployments into top-level peers. Recovery required
deleting and re-POSTing each station deployment under the group via
`POST /deployments/{groupId}/subdeployments`.

---

## 4. Fixes Applied

### 4.1 `ResourceList.vue` — `platform@link` fallback (`e639ad7`)

When `fetchResources()` receives a 404 (or 400) and the context is
`parentType=deployments`, `parentRelation=systems`:

1. Fetch the deployment detail (`GET /deployments/{id}`).
2. Check `properties.deployedSystems@link[]` — resolve each href in sequence.
3. If empty, check `properties.platform@link.href` — resolve that single href.
4. If any systems are resolved, populate `items` directly and return early.
5. Show a yellow advisory banner via `clientSideFallbackDetails` indicating
   which fallback path was used.

```ts
if ((res.status === 404 || res.status === 400) &&
    props.parentType === 'deployments' &&
    props.parentRelation === 'systems' &&
    props.parentId) {
  const depRes = await apiFetch<any>(`/deployments/${props.parentId}`, ...)
  // ... resolve deployedSystems@link[] or platform@link ...
}
```

### 4.2 `normalizeLinkHrefForList()` — href normalization

A local helper (mirrors `normalizeLinkHref` in `ResourceDetail.vue`) converts
any `@link href` form into an API-relative path usable by `apiFetch()`:

| Input form | Output |
|---|---|
| `"04og"` (bare UUID, no slash) | `/systems/04og` |
| `"/systems/04og"` | `/systems/04og` |
| `"https://server/csapi-go-v2/systems/04og"` | `/systems/04og` |
| `"/api/csapi/systems/04og"` | `/systems/04og` |

### 4.3 `bootstrap_ndbc.py` — full URI in `platform@link.href` (`b662445`)

`_deploy_station()` now accepts `base_url` and builds:

```python
"platform@link": {
    "href": base_url.rstrip('/') + '/systems/' + system_server_id,
    ...
}
```

### 4.4 NDBC hierarchy restored (`d512d60`)

`reparent_station_deployments.py` deleted the five orphaned top-level NDBC
station deployments and re-POSTed them under the group ID via
`POST /deployments/{groupId}/subdeployments`, restoring the correct
three-level hierarchy.

---

## 5. Publisher Audit

| Publisher | `platform@link.href` format | Fixed? | Notes |
|---|---|---|---|
| NDBC | Absolute URL (after `b662445`) | ✅ | Re-bootstrapped with full URI |
| Aviation WX | Bare UUID | ⚠️ | Works via normalization; non-conformant |
| CO-OPS | Bare UUID | ⚠️ | Same |
| NWS | Bare UUID | ⚠️ | Same |
| OpenSky | Bare UUID | ⚠️ | Same |
| USGS Earthquake | Bare UUID | ⚠️ | Same |
| USGS NIMS | Bare UUID | ⚠️ | Same |
| USGS Water | Bare UUID | ⚠️ | Same |
| ISS | No `platform@link` | N/A | ISS uses deployment-to-deployment hierarchy; no single platform system |

---

## 6. Known Server Behavior: `PUT /deployments/{id}` Strips `parentDeployment` Link

**Severity: High (data loss)**

`csapi-go-v2` silently drops the `ogc-rel:parentDeployment` link when a
deployment is updated via `PUT /deployments/{id}`. This has no error or
warning in the response. Any `PUT` to a child deployment permanently orphans
it from its parent.

**Workaround:** Never use `PUT /deployments/{id}` on a deployment that has a
parent. If the resource must be updated, delete and re-POST it via
`POST /deployments/{parentId}/subdeployments`.

This behavior is tracked in
[docs/governance/known-server-quirks.md](../governance/known-server-quirks.md).

---

## 7. Future Design Improvements

### 7.1 Standardize `platform@link.href` across all publishers

All bootstrap scripts except NDBC still emit bare UUIDs as `platform@link.href`.
The `_deploy_station()` pattern from `bootstrap_ndbc.py` should be applied to
every publisher. This requires:

- Updating each bootstrap's `_deploy_*` leaf function to accept `base_url`
- Calling with `base_url=BASE_URL` at the bootstrap call site
- Re-running each bootstrap (idempotent via `ensure_deployment`) to update
  existing server records

This makes the data portable and standards-conformant independent of any
Explorer-side normalization.

### 7.2 Implement `GET /deployments/{id}/systems` in csapi-go-v2

The correct long-term fix is for the server to implement the OGC 23-001
Table 43 nested endpoint. The client-side `platform@link` fallback is a
workaround for an unimplemented server capability. A proper server
implementation would:

- Resolve `platform@link` and `deployedSystems@link[]` server-side
- Return a proper OGC API items envelope with pagination support
- Enable filtering (`?q=`, `?datetime=`) over the systems collection

Until implemented, the Explorer fallback should remain in place.

### 7.3 Centralize `@link` href normalization

`normalizeLinkHref` exists in `ResourceDetail.vue` and a copy
(`normalizeLinkHrefForList`) was added in `ResourceList.vue` to avoid a
cross-component import cycle. Both should be extracted to a shared utility
module (e.g., `demo/src/utils/link-utils.ts`) so the logic is maintained in
one place. The current duplication means a future server path change would
require updating two files.

### 7.4 Protect against `PUT` stripping parent links

The publisher library's `ensure_deployment()` helper uses `PUT` to update
existing deployments. It should detect when a deployment has a
`parentDeployment` link and use `PATCH` instead of `PUT`, or re-attach the
parent link after the update. Alternatively, add a pre-flight `GET` to
retrieve the existing `links[]`, merge them into the PUT body, and re-send
the full link set.

### 7.5 Surface the `platform@link` fallback path in the UI more clearly

The current fallback shows a yellow warning banner with a technical message.
Consider:

- A more user-facing label: *"System resolved from deployment properties
  (server does not support `/deployments/{id}/systems`)"*
- An icon or badge in the resource row indicating it was resolved indirectly
- A link directly to the open upstream issue in csapi-go-v2

### 7.6 Extend fallback to other unimplemented nested endpoints

The same pattern (`404 → fetch parent → resolve via @link`) could apply to
other unimplemented nested endpoints. Candidates:

| Endpoint | Inline property fallback |
|---|---|
| `GET /procedures/{id}/systems` | `typeOf@link` on systems (when server round-trips it) |
| `GET /systems/{id}/deployments` | `deployedIn@link` on systems |
| `GET /deployments/{id}/samplingFeatures` | `samplingFeatures@link` |

Each should be evaluated once the server's behavior for that endpoint is
confirmed (some return 400, some 404, some return empty results).
