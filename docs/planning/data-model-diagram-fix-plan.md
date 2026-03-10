# Data Model Diagram — Fix Implementation Plan

**Companion to:** [`docs/webapp-demo/data-model-diagram-audit.md`](../webapp-demo/data-model-diagram-audit.md)  
**Date:** 2025-03-10  
**Scope:** Client-side webapp fixes only — no server changes

---

## Overview

Five priority fixes that address the most impactful issues from the audit. Each fix is self-contained and can be landed independently, though Fix 1 (bare-ID resolution) unblocks several others.

---

## Fix 1 — Resolve Bare-ID `platform@link.href` (D4, C2)

**Problem:** OSH returns `platform@link.href` as a bare ID (e.g. `"0520"`) rather than a URL path (`"/systems/0520"`). `normalizeLinkHref()` assumes a path and all downstream URL construction fails silently.

**Files:** `DataModelDiagram.vue`, `ResourceDetail.vue`

**Change:**  
In `normalizeLinkHref()` (present in both files), add a guard at the top:

```ts
// If href is a bare ID (no slashes), prefix with the appropriate collection path
if (href && !href.includes('/')) {
  // Determine collection from context — platform@link always references a system
  href = `/systems/${href}`;
}
```

For the general case, detect the link relation name and map it:
- `platform@link` → `/systems/{id}`
- `deployment@link` → `/deployments/{id}`
- `datastream@link` → `/datastreams/{id}`

**Impact:** Unblocks Fixes 3 and 4. Deployment → Systems resolution, Systems → Deployments reverse lookup, and all `@link`-based navigation start working.

**Effort:** Small

---

## Fix 2 — Procedure Discovery Fallback (A2, A4, A5, B1, C3)

**Problem:** The `systemKind@link` property and SML3 `typeOf` field are both absent on this server. The Procedure relationship is entirely undiscoverable — the node always shows 0 and clicks do nothing.

**Files:** `DataModelDiagram.vue`, `ResourceDetail.vue`

**Change:**  
Add a new fallback strategy for procedure resolution:

1. **In `DataModelDiagram.vue` `fetchCounts()`:**  
   When viewing a System, after the primary `/systems/{id}/procedures` call returns 400, fall back to:
   - Fetch the system's SML3 detail (already cached in many cases)
   - Check for any `classifiers` → `procedureType`, `implementsProcess`, or `definition` fields
   - If a procedure UID/definition is found, search `/procedures?uid={uid}` or `/procedures?definition={def}`
   - Set the procedure count to the result count

2. **In `ResourceDetail.vue` `tryLinkFallback()`:**  
   Add a new branch for `type === 'procedures'` that uses the same SML3 classifier/definition lookup.

3. **In `DataModelDiagram.vue` `fetchCounts()`:**  
   When viewing a Procedure, after `/procedures/{id}/systems` returns 400, fall back to:
   - Fetch all systems (paginated) and check each system's SML3 for a matching procedure reference
   - Or, if the procedure has a `definition` or `uid`, search `/systems?procedure.definition={def}`

4. **Procedure → Datastreams transitive fallback (A5):**  
   When `/procedures/{id}/datastreams` returns 400:
   - First resolve procedure → systems (using step 3 above)
   - Then for each system, fetch `/systems/{sysId}/datastreams`
   - Aggregate and deduplicate

**Impact:** Procedure node becomes functional — shows correct counts and supports click navigation.

**Effort:** Medium — requires SML3 introspection logic and may need caching to avoid repeated fetches.

**Risk:** If the server has no classifiers or definition fields in SML3, this fallback also returns 0. Verify SML3 content first. If no machine-readable procedure linkage exists, this fix should at minimum suppress the 0-count display and grey out the node instead of showing a misleading count.

---

## Fix 3 — Unblock Deployment → Systems Click (A3, C1)

**Problem:** `navigateToType('systems')` in the deployment context has an early `return` statement that fires unconditionally, preventing navigation even when `resolveDeployedSystems()` has successfully identified systems via `platform@link`.

**Files:** `DataModelDiagram.vue`

**Change:**  
In the `navigateToType()` function, locate the deployment→systems guard:

```ts
// BEFORE (broken):
if (props.resourceType === 'deployments' && type === 'systems') {
  return; // ← unconditional block
}

// AFTER (fixed):
if (props.resourceType === 'deployments' && type === 'systems') {
  if (deployedSystemIds.value.length > 0) {
    // Navigate to the first deployed system, or emit a list
    emit('navigate', { type: 'systems', ids: deployedSystemIds.value });
    return;
  }
  // No deployed systems found — fall through to default behavior or show empty state
  return;
}
```

The exact navigation mechanism depends on how the parent `ResourceDetail.vue` handles the `navigate` event — may need to support a multi-ID navigation mode or pick the first result.

**Impact:** Clicking "Systems" on a deployment diagram navigates to the deployed systems instead of doing nothing.

**Effort:** Small

**Depends on:** Fix 1 (bare-ID resolution) for `platform@link.href` to resolve correctly.

---

## Fix 4 — Aggregate System Count for Root Deployments (B2, B6)

**Problem:** Root deployments (e.g. `04mg`) have neither `platform@link` nor `deployedSystems@link`. The current `resolveDeployedSystems()` only reads these fields from the current deployment, so root deployments always show 0 systems.

**Files:** `DataModelDiagram.vue`

**Change:**  
Extend `resolveDeployedSystems()` to walk the subdeployment tree:

```ts
async function resolveDeployedSystems(deploymentId: string): Promise<string[]> {
  const systemIds: Set<string> = new Set();
  
  async function walk(depId: string) {
    const detail = await fetchDeploymentDetail(depId);
    
    // Collect platform@link from this level
    const platformLink = detail?.properties?.['platform@link'];
    if (platformLink?.href) {
      systemIds.add(normalizeLinkHref(platformLink.href));
    }
    
    // Recurse into subdeployments
    const subs = await fetchSubdeployments(depId);
    for (const sub of subs) {
      await walk(sub.id);
    }
  }
  
  await walk(deploymentId);
  return [...systemIds];
}
```

Add a depth limit (e.g. 5) to prevent runaway recursion on malformed data.

**Impact:** Root and group deployment diagrams show accurate aggregated system counts.

**Effort:** Medium — needs async tree walk with error handling and depth limiting.

**Depends on:** Fix 1 (bare-ID resolution) for `platform@link.href` values.

---

## Fix 5 — Grey Out Unavailable Nodes (B3, B4)

**Problem:** Properties and SamplingFeatures nodes always show 0 because the server has no data for them. Showing "0" is technically accurate but visually misleading — users may think navigation is broken.

**Files:** `DataModelDiagram.vue`

**Change:**  
After `fetchCounts()` completes, for any node whose count is 0 **and** whose primary endpoint returned 400 or whose collection is empty:

```ts
// Add a 'dimmed' class to nodes that are structurally unavailable
const unavailableNodes = computed(() => {
  return nodes.filter(n => 
    counts.value[n.type] === 0 && failedEndpoints.value.has(n.type)
  );
});
```

In the SVG template, apply reduced opacity and a tooltip explaining the node is not available on this server:

```html
<g :class="{ dimmed: unavailableNodes.includes(node) }">
```

```css
.dimmed { opacity: 0.35; pointer-events: none; }
```

**Impact:** Users get clear visual feedback about which relationships exist on this server vs. which are structurally absent.

**Effort:** Small

---

## Implementation Order

```
Fix 1 (bare-ID)  ──→  Fix 3 (unblock click)  ──→  Fix 4 (aggregate walk)
                  ──→  Fix 2 (procedure fallback)
Fix 5 (grey out) can be done independently at any time
```

| Order | Fix | Effort | Blocking? |
|-------|-----|--------|-----------|
| 1st   | Fix 1 — Bare-ID resolution     | Small  | Yes — unblocks 3, 4 |
| 2nd   | Fix 3 — Unblock deployment click | Small  | No |
| 3rd   | Fix 4 — Root deployment walk     | Medium | No |
| 4th   | Fix 2 — Procedure fallback       | Medium | No |
| 5th   | Fix 5 — Grey out unavailable     | Small  | No |

---

## Verification Approach

After each fix, verify on the live demo against these resources:

| Resource                     | ID     | What to Check                                |
|------------------------------|--------|----------------------------------------------|
| NWS KTUS system              | `0520` | Deployments count > 0, procedure clickable   |
| NWS Root Deployment          | `04mg` | Systems count > 0, aggregated from subs      |
| NWS Station Deployment KTUS  | `04ng` | Systems count = 1, click navigates to `0520` |
| NWS Procedure                | `049g` | Systems count = 10, datastreams count = 10   |
| NWS Datastream KTUS          | `04qg` | Observations count > 0, parent nav works     |
| ISS System                   | `040g` | Datastreams visible, deployment linkable      |
