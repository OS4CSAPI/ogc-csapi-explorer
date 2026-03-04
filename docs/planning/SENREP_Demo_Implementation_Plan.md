# SENREP Demo Implementation Plan

**Date:** 2026-03-04  
**Status:** Ready to implement  
**Depends on:** [Simulator Hardening Implementation Plan](Simulator_Hardening_Implementation_Plan.md) (must be completed first)

---

## Overview

Build the click-to-report SENREP workflow in the Demo tab. This is the capstone feature — the moment where an audience sees the full sensor-to-C2 pipeline: acoustic sensor → LOB → gold dot → operator report → authoritative marker on map.

---

## Phase 1: Backend — SENREP Infrastructure Bootstrap

### 1.1 — Verify Existing Server Resources

The [bootstrap_v25.py](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/scripts/bootstrap_v25.py#L345) script already created these on the server:

- **System:** `urn:os4csapi:system:human:monitoring-team-a` (server ID `05eg`)
- **Procedure:** `urn:os4csapi:procedure:senrep:sop:v1`
- **Datastream:** `Monitoring SENREP` (DS ID `044g`, outputName `senrep`)

Verify these still exist on the server. If so, no new server resources needed — the infrastructure is already live.

### 1.2 — Create Demo-Weight SENREP Schema

The existing SENREP schema on the server ([bootstrap_v25.py L449](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/scripts/bootstrap_v25.py#L449)) is the full doctrinal format (title, senderId, seqNo, classification, releasably, dor, etc. — 20 fields). For the demo click-to-report flow, we need a slimmer "demo-weight" observation payload that the frontend posts:

```json
{
  "phenomenonTime": "2026-03-04T14:30:00Z",
  "resultTime": "2026-03-04T14:30:00Z",
  "result": {
    "timestamp": 1741098600,
    "contactId": "C-20260304-001",
    "classification": "UAS",
    "estimatedLat": 31.5555,
    "estimatedLon": -110.3490,
    "cep50_m": 245.3,
    "numContributingLobs": 5,
    "stringId": "STRING-ALPHA",
    "reportType": "INIT",
    "operatorNotes": "",
    "sourceFixObsId": "abc123",
    "sourceLobObsIds": "def456,ghi789,jkl012"
  }
}
```

**Decision:** Post this directly to `044g`. OSH stores result fields as-is — fields not in the schema definition are kept in the result blob. No server-side schema change required. Verified pattern: gold dot observations already store arbitrary result fields that aren't in the declared schema.

### 1.3 — Add `verify_senrep_infrastructure()` to Simulator

**File:** [simulator/main.py](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/simulator/main.py)

New function, following the [seed_detection_ranges()](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/simulator/main.py#L130) pattern:

```python
def verify_senrep_infrastructure() -> bool:
    """Check that the SET system and SENREP datastream exist on the server."""
    try:
        resp = api_get("datastreams/044g")
        return resp is not None and resp.get("id") == "044g"
    except Exception:
        return False
```

Call at the top of `simulation_worker()`, after `seed_detection_ranges()`. Log result but don't block — if it fails, the frontend just won't be able to submit reports.

### 1.4 — Add SENREP DS ID to Simulator Constants

After the hardening plan splits DS lists, add `044g` to `SENREP_DS_IDS` (already planned — this is a confirmation, not a new task).

---

## Phase 2: Frontend — SENREP Layer on Map

### 2.1 — Add SENREP Layer to MapViewPage.vue

**File:** [demo/src/pages/MapViewPage.vue](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/demo/src/pages/MapViewPage.vue)

Add a new map layer for SENREP markers, following the pattern of the location estimate layer at [~L1390–1525](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/demo/src/pages/MapViewPage.vue#L1390):

- **Layer key:** `senrepMarkers`
- **Color:** `#ef4444` (red) — distinct from gold dots (`#facc15`)
- **Symbol:** `◆` (diamond) — distinct from gold dot `⊕`
- **Z-index:** 9 (above gold dots at 8, below popups at 10)

### 2.2 — Add SENREP Data Fetcher

```ts
async function loadSenrepMarkers(): Promise<void> {
  // Fetch all observations from DS 044g
  // Filter by datastream@id to handle scope leak
  // For each, create a diamond marker at estimatedLat/estimatedLon
  // Store rawData with full SENREP fields for popup display
}
```

Called during live refresh cycle alongside `loadLocationEstimates()` and `loadObservationLayers()`.

### 2.3 — SENREP Marker Style

- Red diamond, size 12px
- White border, 2px stroke
- Label below: `contactId — reportType` (e.g., "C-20260304-001 — INIT")
- CEP50 circle if present (red, dashed, semi-transparent)

### 2.4 — SENREP Popup

When clicking a SENREP marker, show:
- Contact ID, classification, report type
- Position (lat/lon), CEP50
- Contributing LOBs count, string ID
- Operator notes
- Timestamp
- Provenance: source fix obs ID and LOB obs IDs

---

## Phase 2.5: Frontend — Track Line Visualization

> **Gap analysis:** [Track_Visualization_Gap_Analysis.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/research/Track_Visualization_Gap_Analysis.md)

The gold dot currently shows only the **latest** localizer fix (`resultTime=latest&limit=1`). There is no visible history — no polyline, no breadcrumb trail, no sense of movement. Without a track line, the map has no visual artifact that "looks like a track" despite all the data model work. This phase adds a gold polyline showing the localizer's fix history.

### 2.5.1 — Fetch Location Estimate History

**File:** [demo/src/pages/MapViewPage.vue](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/demo/src/pages/MapViewPage.vue)

New function `loadTrackLine()`, following the same pattern as `loadLocationEstimates()` at [~L1434](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/demo/src/pages/MapViewPage.vue#L1434):

```ts
async function loadTrackLine(): Promise<void> {
  const source = vectorSources['trackLine']
  if (!source) return
  source.clear()

  if (!localizerDatastreamId) return

  const obsRes = await apiFetch(
    `/datastreams/${localizerDatastreamId}/observations?resultTime=latest&limit=50`,
    { headers: { 'Accept': 'application/om+json' } },
  )
  if (!obsRes.ok || !obsRes.data) return
  const items = obsRes.data.items || []
  if (items.length < 2) return

  // Build coordinate array ordered oldest → newest
  const coords: [number, number][] = items
    .reverse()
    .map((obs: any) => {
      const r = obs.result
      if (typeof r?.estimatedLat === 'number' && typeof r?.estimatedLon === 'number')
        return fromLonLat([r.estimatedLon, r.estimatedLat]) as [number, number]
      return null
    })
    .filter(Boolean) as [number, number][]

  if (coords.length < 2) return

  // Draw polyline with recency-fading segments
  for (let i = 1; i < coords.length; i++) {
    const alpha = 0.15 + 0.75 * (i / (coords.length - 1)) // 0.15 at tail → 0.9 at head
    const segment = new Feature({
      geometry: new LineString([coords[i - 1], coords[i]]),
    })
    segment.setStyle(new Style({
      stroke: new Stroke({
        color: `rgba(250, 204, 21, ${alpha.toFixed(2)})`,
        width: 3,
      }),
    }))
    segment.set('resourceType', 'trackLine')
    source.addFeature(segment)
  }
}
```

### 2.5.2 — Track Line Layer Setup

Add a new vector layer in the layer initialization block, between bearing lines (z-index 6) and location estimates (z-index 8):

- **Layer key:** `trackLine`
- **Z-index:** 7 (between bearing lines and gold dot marker)
- **Style:** per-feature (set on each segment in `loadTrackLine()`)

### 2.5.3 — Integrate into Live Refresh

Call `loadTrackLine()` in the live refresh cycle, immediately before `loadLocationEstimates()`:

```ts
await loadTrackLine()
await loadLocationEstimates()
```

On each refresh, the track line rebuilds: new fixes extend the head, oldest fixes drop off when exceeding 50 points.

### 2.5.4 — Visual Result

| Element | Color | Description |
|---|---|---|
| Track tail | `rgba(250, 204, 21, 0.15)` | Faded gold — oldest fixes |
| Track body | `rgba(250, 204, 21, 0.15–0.9)` | Progressive brightening |
| Track head | `rgba(250, 204, 21, 0.9)` | Bright gold — most recent segment |
| Gold dot (`⊕`) | `#facc15` | Existing marker, sits on top of track head |
| CEP50 circle | `rgba(250, 204, 21, 0.15)` | Existing uncertainty ring around gold dot |

The track line shows direction, speed (spacing), and coverage duration. Combined with red diamond SENREP markers placed along the track, the audience sees the full tactical picture: historical movement + operator reports.

### 2.5.5 — Effort Estimate

~80–100 lines of new code. No new dependencies. No server changes. Pure frontend rendering of data already being fetched (just with a larger `limit`).

---

## Phase 3: Frontend — Click-to-Report Panel

### 3.1 — SENREP Side Panel Component

New component: `demo/src/components/SenrepPanel.vue`

PrimeVue `Drawer` (slide-out from right), triggered when operator clicks a gold dot on the map. The panel shows:

**Pre-filled from gold dot `rawData`:**
- Estimated Lat/Lon (read-only)
- CEP50 (read-only)
- Number of contributing LOBs (read-only)
- Contributing sensors (read-only)
- Classification (editable dropdown: UAS, rotary-wing, fixed-wing, unknown)
- Source fix observation ID (hidden, for provenance)

**Operator fills in:**
- Contact ID (auto-generated as `C-YYYYMMDD-NNN`, editable)
- Report type (dropdown: INIT / UPDATE / FINAL, default INIT)
- Operator notes (free text)

**Actions:**
- Submit Report → POST observation to DS `044g`
- Cancel → close panel

### 3.2 — Gold Dot Click Handler

Modify the existing map click handler in MapViewPage.vue to detect clicks on `locationEstimates` features. When a gold dot is clicked:

1. Extract `rawData` from the feature (already stored — see [~L1497–1510](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/demo/src/pages/MapViewPage.vue#L1497))
2. Open the SENREP panel with pre-filled data
3. Map stays visible behind the side panel for context

### 3.3 — Contact ID Generation

```ts
function generateContactId(): string {
  const d = new Date()
  const date = `${d.getFullYear()}${String(d.getMonth()+1).padStart(2,'0')}${String(d.getDate()).padStart(2,'0')}`
  const seq = String(nextContactSeq++).padStart(3, '0')
  return `C-${date}-${seq}`
}
```

`nextContactSeq` starts at 1 on page load. On submit, increment. If the user edits the ID manually, accept as-is.

### 3.4 — Submit SENREP Observation

```ts
async function submitSenrep(formData: SenrepForm): Promise<void> {
  const now = new Date()
  const obs = {
    phenomenonTime: now.toISOString(),
    resultTime: now.toISOString(),
    result: {
      timestamp: now.getTime() / 1000,
      contactId: formData.contactId,
      classification: formData.classification,
      estimatedLat: formData.estimatedLat,
      estimatedLon: formData.estimatedLon,
      cep50_m: formData.cep50_m,
      numContributingLobs: formData.numContributingLobs,
      stringId: formData.stringId || 'STRING-ALPHA',
      reportType: formData.reportType,
      operatorNotes: formData.operatorNotes || '',
      sourceFixObsId: formData.sourceFixObsId || '',
      sourceLobObsIds: formData.sourceLobObsIds || '',
    },
  }

  await apiFetch(`/datastreams/044g/observations`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/om+json',
      'Accept': 'application/om+json',
    },
    body: JSON.stringify(obs),
  })

  // On success: close panel, refresh SENREP markers layer
  await loadSenrepMarkers()
}
```

Uses the CSAPI bridge's existing POST capability (the bridge already supports observation creation).

### 3.5 — SamplingFeature Creation (Optional, On First SENREP)

On the first SENREP submission for a new `contactId`, create a SamplingFeature:

```ts
async function createTrackFeature(contactId: string, lat: number, lon: number): Promise<void> {
  const payload = {
    type: 'Feature',
    geometry: { type: 'Point', coordinates: [lon, lat] },
    properties: {
      featureType: 'sam:SamplingFeature',
      uid: `urn:os4csapi:track:${contactId}`,
      name: `Track ${contactId}`,
      description: `UAS contact track created by SET on first SENREP`,
    },
  }
  await apiFetch('/samplingFeatures', {
    method: 'POST',
    headers: { 'Content-Type': 'application/geo+json' },
    body: JSON.stringify(payload),
  })
}
```

The CSAPI bridge already has `createSamplingFeature()` wired up ([csapi-bridge.ts](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/demo/src/csapi-bridge.ts)). No `samplingFeature@link` on the observation — `contactId` is the sole join key.

---

## Phase 4: DemoPage.vue — SENREP Integration

### 4.1 — Add SENREP Count to Summary Cards

The [DemoPage.vue](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/demo/src/pages/DemoPage.vue) already displays sensor arrays, observation counts, and datastream tables. Add a summary card showing:
- SENREP count (observations in DS `044g`)
- Latest SENREP contact ID and timestamp

### 4.2 — SENREP Report Timeline

Add a feed/log section at the bottom of the Demo page:
- Shows submitted SENREPs in reverse chronological order
- Each row: timestamp, contactId, classification, reportType, position, source
- Builds narrative for audience: "three SENREPs in the last 10 minutes, tracking one UAS contact"

### 4.3 — Track List (from SamplingFeatures)

If SamplingFeature creation succeeds, show a small "Active Tracks" panel:
- Query `GET /samplingFeatures` filtered by uid prefix `urn:os4csapi:track:C-`
- Show each track with its contactId, creation time, latest SENREP count

---

## Phase 5: Deploy & Verify

| Step | Command | Validates |
|---|---|---|
| 5.1 Verify server resources | `curl` DS `044g`, Monitoring Team system | Infrastructure exists |
| 5.2 Deploy simulator | `flyctl deploy --remote-only` | `verify_senrep_infrastructure()` runs |
| 5.3 Build + deploy frontend | `cd demo && npm run build && npx wrangler pages deploy dist --project-name ogc-csapi-explorer --commit-dirty=true` | New UI live |
| 5.4 End-to-end test | Start sim → wait for gold dots → click gold dot → submit SENREP → verify marker appears | Full pipeline |
| 5.5 Test Tier 2 clear | Clear Sim Data → confirm SENREP markers survive | Reset resilience |
| 5.6 Test Tier 3 reset | Full Demo Reset → confirm SENREP markers gone | Full reset |

---

## Files Created / Modified

| File | Action | Purpose |
|---|---|---|
| [simulator/main.py](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/simulator/main.py) | Modify | Add `verify_senrep_infrastructure()` |
| [demo/src/components/SenrepPanel.vue](https://github.com/OS4CSAPI/ogc-csapi-explorer/tree/main/demo/src/components) | **Create** | Click-to-report side panel |
| [demo/src/pages/MapViewPage.vue](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/demo/src/pages/MapViewPage.vue) | Modify | SENREP layer, markers, popup, gold dot click → panel |
| [demo/src/pages/DemoPage.vue](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/demo/src/pages/DemoPage.vue) | Modify | SENREP count card, report timeline, track list |

---

## Design Decisions (from consensus reports)

| Decision | Source |
|---|---|
| SENREP = Observation, FOI = track | [SENREP_Track_FOI_Review.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/research/SENREP_Track_FOI_Review.md) |
| Track = SamplingFeature (created on first SENREP) | [SENREP_Track_FOI_Review.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/research/SENREP_Track_FOI_Review.md) |
| SET creates track, not localizer | [SENREP_Workflow_Design.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/research/SENREP_Workflow_Design.md) |
| `contactId` = sole join key (no `samplingFeature@link`) | [SENREP_Track_FOI_Review.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/research/SENREP_Track_FOI_Review.md) |
| Date-stamped contact IDs (`C-YYYYMMDD-NNN`) | [Demo_Reset_SENREP_Resilience.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/research/Demo_Reset_SENREP_Resilience.md) |
| Provenance fields (`sourceFixObsId`, `sourceLobObsIds`) | [Demo_Reset_Hardening_Review.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/research/Demo_Reset_Hardening_Review.md) |
| Retrieval stays datastream-scoped (scope leak protection) | [OSH_Datastream_Observation_Scope_Leak.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/research/OSH_Datastream_Observation_Scope_Leak.md) |
| Three-tier reset (SENREP survives Tier 2, cleared on Tier 3) | [Demo_Reset_SENREP_Resilience.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/research/Demo_Reset_SENREP_Resilience.md) |
| Track line = gold polyline of last N localizer fixes (Phase 2.5) | [Track_Visualization_Gap_Analysis.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/research/Track_Visualization_Gap_Analysis.md) |

---

## Implementation Order

1. **Hardening plan first** — DS list split, scope leak filter, localizer gate, `/reset` endpoint
2. **Phase 1** — verify server resources, add `verify_senrep_infrastructure()`
3. **Phase 2** — SENREP layer on map (markers, styles, fetcher)
4. **Phase 2.5** — Track line visualization (gold polyline, recency fading) — see [Track_Visualization_Gap_Analysis.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/research/Track_Visualization_Gap_Analysis.md)
5. **Phase 3** — SenrepPanel.vue + gold dot click handler + submit flow
6. **Phase 4** — DemoPage.vue integration (counts, timeline, track list)
7. **Phase 5** — deploy and end-to-end test
