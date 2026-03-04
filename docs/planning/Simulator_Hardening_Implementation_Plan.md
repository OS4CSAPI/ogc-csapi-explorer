# Simulator Hardening Implementation Plan

**Date:** 2026-03-04  
**Status:** Ready to implement  
**Prerequisite for:** SENREP demo tab, all future observation-producing features

---

## Overview

Three critical fixes to `simulator/main.py` + one admin console UI update. Makes the clear/reset infrastructure safe before SENREP observations go live.

---

## Phase 1: Simulator Backend (simulator/main.py)

### 1.1 — Split DS ID Lists

**Location:** [L476–486](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/simulator/main.py#L476)

**Current:**
```python
DETECTION_DS_IDS = ["04dg", "04e0", "04eg"]
CLEARABLE_DS_IDS = [
    "044g", "0430", "043g", "04c0", "0440", "0410", "041g", "042g",
    "0450", "045g", "04cg", "046g", "0470", "047g", "0480",
    "048g", "0490", "04d0", "04a0", "04ag", "04b0", "04bg",
]
ALL_DS_IDS = CLEARABLE_DS_IDS + DETECTION_DS_IDS
```

**Change to:**
```python
DETECTION_DS_IDS = ["04dg", "04e0", "04eg"]       # never cleared, auto-seeded
SENREP_DS_IDS = ["044g"]                            # cleared only on /reset (Tier 3)
SIM_DS_IDS = [                                      # cleared on /clear (Tier 2)
    "0430", "043g", "04c0", "0440", "0410", "041g", "042g",
    "0450", "045g", "04cg", "046g", "0470", "047g", "0480",
    "048g", "0490", "04d0", "04a0", "04ag", "04b0", "04bg",
]
ALL_DS_IDS = SIM_DS_IDS + SENREP_DS_IDS + DETECTION_DS_IDS
```

- Pull `044g` out of sim list into `SENREP_DS_IDS`
- Rename `CLEARABLE_DS_IDS` → `SIM_DS_IDS`

### 1.2 — Add Scope Leak Filter to Clear Loop

**Location:** [L489–543](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/simulator/main.py#L489)

**Current:** `clear_all_observations()` iterates `CLEARABLE_DS_IDS`, fetches observations, deletes all without checking ownership.

**Change:**
- Refactor to `clear_observations(ds_ids: list[str]) -> dict[str, int]` — accepts DS list as parameter
- After fetching items, filter: only delete where `obs.get("datastream@id") == ds_id` or `datastream@id` is absent
- Skip foreign observations, increment `foreign_skipped` counter
- Return `{"deleted": N, "errors": N, "foreign_skipped": N}`

### 1.3 — Gate `/clear` on Both Sim and Localizer

**Location:** [L636–645](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/simulator/main.py#L636)

**Current:** Only checks `state.running`.

**Change:**
- Also check `loc_state.running`
- Error message: `"Stop both simulator and localizer before clearing"`
- `/clear` calls `clear_observations(SIM_DS_IDS)` — Tier 2 only

### 1.4 — Add `/reset` Endpoint (Tier 3)

**New endpoint:** `POST /reset`

```python
@app.post("/reset", response_model=MessageResponse)
def reset_demo():
    with state.lock:
        if state.running:
            return MessageResponse(ok=False, message="Stop both simulator and localizer before resetting")
    with loc_state.lock:
        if loc_state.running:
            return MessageResponse(ok=False, message="Stop both simulator and localizer before resetting")

    result = clear_observations(SIM_DS_IDS + SENREP_DS_IDS)
    return MessageResponse(
        ok=True,
        message=f"Full reset: deleted {result['deleted']} observations "
                f"({result['errors']} errors, {result['foreign_skipped']} foreign skipped)",
    )
```

### 1.5 — Update `/clear` to Use New Function

```python
@app.post("/clear", response_model=MessageResponse)
def clear_sim_data():
    # Gate on both sim and localizer
    with state.lock:
        if state.running:
            return MessageResponse(ok=False, message="Stop both simulator and localizer before clearing")
    with loc_state.lock:
        if loc_state.running:
            return MessageResponse(ok=False, message="Stop both simulator and localizer before clearing")

    result = clear_observations(SIM_DS_IDS)
    return MessageResponse(
        ok=True,
        message=f"Cleared sim data: {result['deleted']} deleted "
                f"({result['errors']} errors, {result['foreign_skipped']} foreign skipped)",
    )
```

---

## Phase 2: Frontend Admin Console (SimulatorAdminPage.vue)

### 2.1 — Rename Clear Button

**Location:** [~L356–363](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/demo/src/pages/SimulatorAdminPage.vue#L356)

Change `label="Clear All Observations"` → `label="Clear Sim Data"`

### 2.2 — Update Clear Button Disabled State

Add localizer running check: `:disabled="!connected || (status?.running ?? false) || (locStatus?.running ?? false)"`

### 2.3 — Add Full Demo Reset Button

New button next to Clear:
```html
<Button
  label="Full Demo Reset"
  icon="pi pi-refresh"
  severity="danger"
  :loading="resetting"
  :disabled="!connected || (status?.running ?? false) || (locStatus?.running ?? false)"
  @click="resetDemo"
/>
```

### 2.4 — Add `resetDemo()` Function

```ts
const resetting = ref(false)

async function resetDemo() {
  if (!confirm('Full demo reset: delete ALL sim data AND reports. Detection rings will be re-seeded on next start. Continue?')) return
  resetting.value = true
  actionMessage.value = ''
  try {
    const data = await apiFetch('/reset', { method: 'POST' })
    actionMessage.value = data.message
    actionSeverity.value = data.ok ? 'success' : 'error'
  } catch (e: any) {
    actionMessage.value = e.message
    actionSeverity.value = 'error'
  } finally {
    resetting.value = false
  }
}
```

### 2.5 — Update Clear Confirm Dialog Text

Change from `'Delete ALL observations from every datastream on the server?'` to `'Clear all sensor/localizer data? SENREP reports will be preserved.'`

---

## Phase 3: Deploy & Verify

| Step | Command | Validates |
|---|---|---|
| 3.1 Deploy simulator | `flyctl deploy --remote-only` | Backend changes on Fly.io |
| 3.2 Verify Tier 2 | Start sim+loc, stop both, Clear Sim Data | `044g` untouched, sim DSes empty |
| 3.3 Verify Tier 3 | Full Demo Reset | `044g` now empty, detection rings re-seed on next start |
| 3.4 Check scope leak filter | Inspect `foreign_skipped` in response | Scope leak handled, no collateral |
| 3.5 Deploy frontend | `cd demo && npm run build && npx wrangler pages deploy dist --project-name ogc-csapi-explorer --commit-dirty=true` | New buttons visible |

---

## Files Modified

| File | Changes |
|---|---|
| [simulator/main.py](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/simulator/main.py) | Split DS lists, rename `SIM_DS_IDS`, scope leak filter, localizer gate, `/reset` endpoint, refactored `clear_observations()` |
| [demo/src/pages/SimulatorAdminPage.vue](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/demo/src/pages/SimulatorAdminPage.vue) | Rename Clear button, add Full Demo Reset button + function, update disabled states, update confirm text |

---

## What This Does NOT Include

Deferred to SENREP Demo Implementation Plan:
- SENREP schema/datastream bootstrap
- SamplingFeature track creation
- Demo tab UI (click-to-report)
- SENREP markers on map
- `verify_senrep_infrastructure()` auto-seed
- Contact ID management (`C-YYYYMMDD-NNN`)
