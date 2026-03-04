# SENREP / Track FOI Design Review

**Date:** 2026-03-04  
**Status:** Review  
**Context:** Cross-review of ChatGPT's SENREP/Track FOI recommendations against Claude's SENREP Workflow Design report and known OSH bugs

---

## Source Material

- ChatGPT's `Gold_Dots_SamplingFeature_Weigh_In.md` — original analysis of the gold dot semantic gap
- ChatGPT's packaged follow-up responses (4 messages) covering FOI modeling, track lifecycle, and creation authority
- Claude's `SENREP_Workflow_Design.md` — prior design doc for the SENREP pipeline
- Empirical probe results: `OSH_SamplingFeature_Link_Persistence_Gap.md`, `OSH_Datastream_Observation_Scope_Leak.md`

---

## Where ChatGPT Is Right (and We Agree)

**The core modeling is correct.** SENREP = Observation, FOI = track/contact. SET is the authority for track creation. `contactId` (or `trackUid`) as a string field in the result blob is the reliable join key. These are consistent with the SENREP Workflow Design doc and are sound CSAPI/SOSA modeling.

**"Option B: FOI = contact/track hypothesis"** is the right long-term choice. Creating the SamplingFeature is cheap — one POST — and gives a named, queryable resource even if OSH can't persist the link to it.

**SET creates the track on first SENREP, not the localizer on first fix.** Doctrinally sound, reduces identity churn from noisy fixes, matches operator workflow.

---

## Where ChatGPT Overcomplicates Things

### 1. The "attempt `samplingFeature@link`, if it fails fall back" strategy is dead code in disguise

`OSH_SamplingFeature_Link_Persistence_Gap.md` already proves OSH drops the link. Writing try/check/fallback code for a thing we *know* fails is wasted effort and dual-path complexity in the frontend. The correct move: skip `samplingFeature@link` entirely for now, use `contactId` as the sole join key, and add the link in a single pass later when OSH is fixed.

### 2. The candidateId → trackUid promotion cycle is premature

Rules 5–7 of ChatGPT's lifecycle spec (candidateId on gold dots, promotion on first SENREP, optional backfill) are multi-target tracking concerns. The demo has ONE simulated UAV. The localizer doesn't need to produce `candidateId` fields, the SET doesn't need promotion logic, and backfill is unnecessary. The gold dot carries `trackId` and `classification` already. The SENREP carries `contactId`. That's the join.

### 3. Ten lifecycle rules when three suffice

For the demo:
1. SET creates the track (SamplingFeature) on first SENREP
2. `contactId` in every SENREP result is the join key
3. Gold dots stay as-is (no changes to localizer pipeline)

Rules about merge/split, closure semantics, candidateId promotion — real concerns for production multi-target systems, but design debt not needed now.

### 4. No mention of the scope leak

Any approach that leans on querying observations by SamplingFeature association will hit the same cross-datastream contamination documented in `OSH_Datastream_Observation_Scope_Leak.md`. The `datastream@id` filter added to `loadObservationLayers()` protects observation rendering, but a naive "get all observations for this FOI" query would return garbage. ChatGPT's recommendations don't account for this because they haven't seen the bug.

---

## Revised Position on SamplingFeature Creation

The SENREP Workflow Design doc originally said "don't create a separate Feature resource at all right now." After reviewing ChatGPT's argument, that position is softened:

**Go ahead and create the SamplingFeature.** It's one POST, it's semantically correct, and it gives a server-side "track registry" enumerable via `GET /samplingFeatures`. That's useful for the demo tab UI — e.g., a track list panel. The cost is near zero and the modeling is cleaner.

**However — don't wire up `samplingFeature@link` on observations, and don't build any logic that depends on it.** Everything flows through `contactId` in the result. The SamplingFeature exists as a reference object, not as an operational association.

---

## Net Recommendation

| Concern | Position |
|---|---|
| SENREP = Observation about a track | **Agree with ChatGPT** |
| Track = SamplingFeature | **Agree with ChatGPT** (revised from prior "skip it") |
| SET creates track on first SENREP | **Agree with ChatGPT** |
| `contactId` as primary join key | **Agree with both** (original position, ChatGPT concurs) |
| Attempt `samplingFeature@link` | **Disagree** — skip entirely, don't "try and fall back" |
| candidateId/promotion/backfill | **Disagree** — premature for single-target demo |
| 10 lifecycle rules | **Trim to 3** for demo scope |
| Changes to localizer/gold dots | **None** — leave as-is |

---

## What to Build

1. **Bootstrap script** — creates SET system, procedure, datastream, and SENREP schema (pattern: `add_detection_range.py`)
2. **Create SamplingFeature** — `UAS-Track-001` on first SENREP (or in bootstrap for the demo)
3. **Demo tab UI** — click gold dot → SENREP panel (pre-filled from fix data) → submit → authoritative marker appears on map
4. **`contactId`** — string field in SENREP result, sole grouping key

Everything else is v2.

---

## Cross-References

- [SENREP_Workflow_Design.md](SENREP_Workflow_Design.md) — full SENREP pipeline design
- [Gold_Dots_SamplingFeature_Analysis.md](Gold_Dots_SamplingFeature_Analysis.md) — original semantic gap analysis
- [OSH_SamplingFeature_Link_Persistence_Gap.md](OSH_SamplingFeature_Link_Persistence_Gap.md) — probe showing OSH drops `samplingFeature@link`
- [OSH_Datastream_Observation_Scope_Leak.md](OSH_Datastream_Observation_Scope_Leak.md) — datastream scope leak bug
