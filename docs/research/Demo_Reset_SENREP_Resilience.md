# Demo Reset & SENREP Resilience Design

**Date:** 2026-03-04  
**Status:** Planning  
**Context:** Review of ChatGPT's SENREP weigh-in + analysis of demo reset/restart resilience

---

## Part 1: Review of ChatGPT's Weigh-In on SENREP_Track_FOI_Review

### Three-Way Consensus (Achieved)

| Decision | Claude | ChatGPT | Status |
|---|---|---|---|
| SENREP = Observation, FOI = track | Yes | Yes | **Unanimous** |
| Track = SamplingFeature | Yes | Yes | **Unanimous** |
| SET creates track on first SENREP | Yes | Yes | **Unanimous** |
| `contactId` = sole join key | Yes | Yes | **Unanimous** |
| Skip `samplingFeature@link` for now | Yes | Yes | **Unanimous** |
| candidateId/promotion is v2 | Yes | Yes | **Unanimous** |
| Keep retrieval datastream-scoped | Yes | Yes | **Unanimous** |

No remaining disagreements on core architecture.

### One New Idea Worth Adopting

ChatGPT proposed provenance fields in the SENREP result: `sourceFixObsId` and `sourceLobObsIds`. These are cheap (two extra string fields in the schema), and they make the report self-auditing. For a demo audience, being able to say "this report traces back to that gold dot and those three LOBs" is a powerful narrative. **Adopted — add to schema.**

### Conformance Probe for `samplingFeature@link`

ChatGPT suggested a CI script to detect when OSH starts persisting the link. Reasonable concept, but low priority — the existing probe report documents the gap, and a manual re-test suffices. **Deferred.**

---

## Part 2: Demo Reset / Restart Resilience

### The Problem

Once SENREP observations and SamplingFeature tracks exist on the server, the reset question gains a new dimension: **do you clear the reports too, or just the sensor data?** A demo may need to restart due to A/V issues, audience requests to "see it again," or mid-demo failures.

### Current Reset Mechanism

The simulator has a tiered clear system:
- **Detection ranges** (`DETECTION_DS_IDS`) — never cleared, auto-seeded on simulator start via `seed_detection_ranges()`
- **Sim data** (`CLEARABLE_DS_IDS`, 22 datastreams) — wiped by `/clear` endpoint; covers LOBs, location estimates, tracks
- Admin console: Stop → Clear → Start is the operator reset flow

### Three Reset Tiers (Proposed)

| Tier | What it clears | What survives | Use case |
|---|---|---|---|
| **Tier 1: Restart Sim** | Stop/start sim thread only. No data deleted. | Everything — LOBs, gold dots, SENREPs, detection rings, tracks | "Sim hiccupped, just restart it." Data continues accumulating. |
| **Tier 2: Clear Sim Data** | LOBs, gold dots, location estimates (existing `/clear` behavior) | Detection rings, SENREPs, SamplingFeature tracks | "Start the sensor demo over, but keep the reports to show persistence." |
| **Tier 3: Full Demo Reset** | Everything in Tier 2 + SENREP observations + SamplingFeature tracks | Detection rings only (auto-seeded on next start) | "Start the whole demo from scratch." |

### Implementation

**Tier 1** — already works (Stop/Start).

**Tier 2** — already works (existing `/clear` endpoint).

**Tier 3** requires:

1. **New `SENREP_DS_IDS` list** in `main.py` — separate from `CLEARABLE_DS_IDS` so Tier 2 doesn't touch reports by default
2. **New `/reset` endpoint** (or `?full=true` flag on `/clear`) — clears `CLEARABLE_DS_IDS` + `SENREP_DS_IDS` + deletes demo SamplingFeatures
3. **SamplingFeature deletion** — needs a probe to confirm OSH supports `DELETE /samplingFeatures/{id}`. If it does, the reset script deletes demo tracks. If not, they accumulate harmlessly (orphaned features with no referencing observations). The CSAPI bridge already has `deleteSamplingFeature()` wired up.

### Contact ID Management Across Resets

| Option | Behavior | Pros | Cons |
|---|---|---|---|
| **A: Always reset to 001** | After Tier 3, next report → `CONTACT-001` | Simple, predictable | Collision risk if SamplingFeature DELETE fails |
| **B: Query and continue** | Find max contact number, increment | Resilient to partial resets | Extra query, more code |
| **C: Date-stamped IDs** | `C-20260304-001`, `C-20260304-002` | Zero collisions, zero extra queries, self-documenting | None meaningful |

**Recommendation: Option C (date-stamped IDs).** Format: `C-YYYYMMDD-NNN`. Trivially generated, never collides, self-documenting, and consistent with military/intel reporting conventions where date-stamps are standard.

### Frontend State on Reset

When the operator triggers a Tier 3 reset:
1. Frontend calls the full reset endpoint
2. On success, clears all local reactive state: SENREP markers layer, track list, report timeline, gold dots, LOBs
3. Map returns to detection-rings-only state
4. Operator hits Start → fresh demo begins

Same pattern as the current Clear flow, extended to cover the SENREP layer.

### Mid-Demo Recovery (the "oh shit" scenario)

If something breaks mid-demo (Fly.io idles, OSH hiccups, network blip):

- **Detection rings survive** — seeded on every simulator start; frontend uses schema-based filtering to find them
- **Existing LOBs/gold dots/SENREPs survive** — they're on the server; frontend re-fetches on page load or refresh
- **Restart the sim** → new sensor data flows immediately, picks up where it left off
- **This is actually a demo strength:** "Watch — even after a sensor system restart, the reports and detection configuration persist on the server. That's the value of standards-based data."

### Auto-Seed Pattern Extension

`seed_detection_ranges()` is the proven pattern: check if expected data exists, re-post if missing. Extend this for SENREP infrastructure:

- `seed_detection_ranges()` — already works
- `verify_senrep_infrastructure()` — new function, called on simulator start. Checks that the SET system, procedure, and datastream exist. If not, creates them (bootstrap-on-start). This means the demo "just works" after a fresh deploy without running a separate bootstrap script.

### Admin Console UI

Split button or dropdown on the admin console:
- **Clear Sim Data** (Tier 2) — existing behavior
- **Full Demo Reset** (Tier 3) — clears everything + SENREP layer

```
DETECTION_DS_IDS  → never cleared, auto-seeded       (permanent infrastructure)
SENREP_DS_IDS     → cleared only on Tier 3            (reports)
CLEARABLE_DS_IDS  → cleared on Tier 2 or Tier 3       (sim data)
```

---

## Part 3: Updated SENREP Schema

Based on three-way consensus, the SENREP observation schema should include provenance fields (adopted from ChatGPT's recommendation). The existing schema in the bootstrap script is the doctrinal SENREP format. The demo-path schema for the click-to-report workflow is:

```
contactId        (Text)     — date-stamped operator-assigned ID, e.g. C-20260304-001
classification   (Text)     — UAS, rotary-wing, fixed-wing, unknown
estimatedLat     (Quantity)  — from the gold dot fix
estimatedLon     (Quantity)  — from the gold dot fix
cep50_m          (Quantity)  — uncertainty radius
numContributingLobs (Count)  — how many LOBs contributed to the fix
stringId         (Text)     — which sensor string produced the fix
reportType       (Text)     — INIT / UPDATE / FINAL
operatorNotes    (Text)     — free text
sourceFixObsId   (Text)     — observation ID of the clicked gold dot (provenance)
sourceLobObsIds  (Text)     — comma-separated LOB observation IDs (provenance)
timestamp        (Time)     — report time
```

This is the "demo-weight" SENREP. The full doctrinal SENREP schema (with STR-NO, ETA, classification markings, etc.) already exists on the server via the bootstrap script.

---

## GitHub Resources

### Reports (this conversation thread)
- [SENREP_Workflow_Design.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/research/SENREP_Workflow_Design.md) — full SENREP pipeline design (Claude)
- [SENREP_Track_FOI_Review.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/research/SENREP_Track_FOI_Review.md) — cross-review of ChatGPT and Claude positions

### OSH Bug Reports (informing design constraints)
- [OSH_Datastream_Observation_Scope_Leak.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/research/OSH_Datastream_Observation_Scope_Leak.md) — datastream scope leak bug (why queries can't use FOI filtering)
- [OS4CSAPI/osh-core#3](https://github.com/OS4CSAPI/osh-core/issues/3) — filed issue for scope leak

### Existing SENREP Schema (on server)
- [bootstrap_v25.py — SENREP schema definition](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/scripts/bootstrap_v25.py#L449) — the full doctrinal SENREP `DataRecord` schema (SWE Common)
- [bootstrap_v25.py — SET system + procedure + datastream creation](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/scripts/bootstrap_v25.py#L345) — Monitoring Team A system, SENREP procedure, SENREP datastream

### Infrastructure (existing patterns to extend)
- [simulator/main.py — seed_detection_ranges()](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/simulator/main.py#L130) — auto-seed pattern to replicate for SENREP infrastructure
- [simulator/main.py — CLEARABLE_DS_IDS / DETECTION_DS_IDS](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/simulator/main.py#L476) — tiered DS ID lists to extend with `SENREP_DS_IDS`
- [simulator/main.py — clear_all_observations()](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/simulator/main.py#L489) — existing clear logic to extend for Tier 3
- [scripts/add_detection_range.py](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/scripts/add_detection_range.py) — bootstrap script pattern for new SENREP bootstrap

### Migration Report (server resource inventory)
- [AZ-MA-2_MA-3_Oracle_Migration_Report.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/research/phase-6/AZ-MA-2_MA-3_Oracle_Migration_Report.md) — comprehensive inventory of all systems, datastreams, and DS IDs (including SENREP DS `044g`)

### Frontend (CSAPI bridge + SamplingFeature support)
- [demo/src/csapi-bridge.ts](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/demo/src/csapi-bridge.ts) — already has `createSamplingFeature()`, `deleteSamplingFeature()`, `getSamplingFeatures()` wired up
- [demo/src/pages/MapViewPage.vue](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/demo/src/pages/MapViewPage.vue) — main map page where SENREP markers and click-to-report UI will be added
