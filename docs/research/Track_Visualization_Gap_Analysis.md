# Track Visualization Gap Analysis

**Date:** 2026-03-04  
**Status:** Gap identified → Phase 2.5 added to SENREP Demo Implementation Plan

---

## The Question

> "Will there be something that looks and feels like a track on the map during our demo?"

## The Gap

**No.** Neither the Simulator Hardening Implementation Plan nor the SENREP Demo Implementation Plan produces a visible track line on the map. The entire "track" discussion across three review rounds ([SENREP_Track_FOI_Review.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/research/SENREP_Track_FOI_Review.md), [Demo_Reset_SENREP_Resilience.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/research/Demo_Reset_SENREP_Resilience.md), [SENREP_Workflow_Design.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/research/SENREP_Workflow_Design.md)) focused on the **data model identity question** — whether the track is a SamplingFeature, how the SET creates it, how `contactId` links SENREPs to it. None of that produces a visual artifact.

### What the Map Currently Shows

The gold dot layer ([MapViewPage.vue ~L1434–1525](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/demo/src/pages/MapViewPage.vue#L1434)) fetches:

```
GET /datastreams/{localizerDsId}/observations?resultTime=latest&limit=1
```

This returns **exactly one observation** — the latest localizer fix. The map renders:

1. A gold dot (`⊕`) at the estimated lat/lon
2. A dashed gold CEP50 uncertainty circle
3. A text label: `UAS — 5 LOBs`

When the localizer produces a new fix, the old gold dot **disappears** and the new one takes its place. There is no visible history. No polyline. No breadcrumb trail. No sense of movement.

### What the SENREP Plan Adds

The SENREP Demo Implementation Plan adds:

- **Phase 2:** Red diamond SENREP markers on the map (one per report)
- **Phase 3:** Click-to-report panel (click gold dot → submit SENREP → diamond appears)

But the gold dots still show only the latest fix. There's no connecting line between fixes, no concept of a "track" on the screen.

### The Semantic Gap

We spent considerable effort debating whether a track is a SamplingFeature or an Observation — but the audience doesn't see data model entities. They see shapes on a map. Without a polyline connecting historical fixes, there's nothing that "looks like a track" to a human viewer, regardless of how well the data model represents it.

---

## Recommendation: Add Track Line as Phase 2.5

Insert a new phase between Phase 2 (SENREP markers) and Phase 3 (click-to-report panel) that renders a **gold polyline** showing the localizer's fix history.

### What It Looks Like

- **Gold polyline** connecting the last N location estimates (N = 50, configurable)
- **Recency fading:** bright gold at the track head (latest fix), progressively fading to near-transparent at the tail
- **Track head:** a bright gold dot (`⊕`) at the leading end — this is the existing gold dot, now contextually part of the track
- **Track tail:** historical points optionally shown as smaller, faded dots
- **Direction and speed:** implicitly communicated by the polyline's shape and spacing between points

### How It Works

1. **Fetch:** Instead of `limit=1`, fetch `limit=50` (or configurable N) from the localizer datastream:
   ```
   GET /datastreams/{localizerDsId}/observations?resultTime=latest&limit=50
   ```

2. **Build LineString:** Extract `estimatedLat`/`estimatedLon` from each observation's result, ordered by timestamp. Build an OpenLayers `LineString` geometry from the coordinate array.

3. **Style with recency gradient:** Use an OpenLayers `Stroke` with a gradient or segmented styling:
   - Head segment (newest): `rgba(250, 204, 21, 0.9)` — bright gold
   - Middle segments: progressively decrease alpha
   - Tail segment (oldest): `rgba(250, 204, 21, 0.15)` — barely visible

4. **Layer placement:** z-index 7.5 (between bearing lines at 6 and gold dot at 8) — the track line sits behind the current gold dot but above bearing lines.

5. **Live refresh:** During live mode, the track polyline refreshes alongside the gold dot. As new fixes arrive, the line grows at the head and the oldest segment fades or drops off when exceeding N points.

### Code Estimate

~80–100 lines of new code in `MapViewPage.vue`:
- A new `loadTrackLine()` async function (~50 lines)
- Track line styling (~15 lines)
- Integration into the live refresh cycle (~5 lines)
- Layer setup in the same pattern as existing layers (~10–15 lines)

### Why This Phase Placement

| Before Phase 2.5 | After Phase 2.5 |
|---|---|
| Gold dot = lonely point on map | Gold dot = head of a visible track |
| Red diamond SENREPs float by themselves | Red diamonds sit on/near the track line, showing where the operator reported |
| "Where is it?" (no context) | "Where was it, where is it now, where is it going?" (full tactical picture) |

Phase 2.5 depends on Phase 2 (which sets up the SENREP layer infrastructure and patterns). Phase 3 (click-to-report) benefits from Phase 2.5 because the operator clicks a gold dot that's visually part of a track, making the SENREP submission feel like a natural response to observed movement.

### Visual Impact

This is the **highest visual-impact, lowest-effort item** remaining. A gold polyline with a fading tail instantly communicates:

- **Movement:** the target has been here, and it's going there
- **Speed:** tightly-spaced dots = slow, widely-spaced = fast
- **Coverage:** the length of the track shows how long the system has been tracking
- **Recency:** bright head vs. faded tail shows temporal context at a glance

For a demo audience, this is the moment where a map full of static shapes becomes a **live tactical picture**.

---

## What the Track Line Is NOT

- **NOT SENREP markers.** The gold track line shows localizer fix history. SENREP markers (red diamonds) are separate — they show where the human operator submitted reports.
- **NOT a SamplingFeature visualization.** The track line is purely a frontend rendering of observation history. The SamplingFeature data model entity (if created by the SET) is a separate concern.
- **NOT a replacement for the gold dot.** The existing gold dot remains the bright head of the track. It stays at z-index 8 with its CEP50 circle and label.

---

## Files Modified

| File | Change |
|---|---|
| [demo/src/pages/MapViewPage.vue](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/demo/src/pages/MapViewPage.vue) | New `loadTrackLine()` function, track line layer setup, integration into live refresh |

---

## Relationship to Other Documents

| Document | Relationship |
|---|---|
| [SENREP_Demo_Implementation_Plan.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/planning/SENREP_Demo_Implementation_Plan.md) | Phase 2.5 added to the plan based on this analysis |
| [SENREP_Track_FOI_Review.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/research/SENREP_Track_FOI_Review.md) | Data model debate that motivated the "track" question |
| [SENREP_Workflow_Design.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/research/SENREP_Workflow_Design.md) | SET workflow design — track line visualizes the localizer output the SET operator sees |
