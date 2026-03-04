# Demo Reset Hardening Review

**Date:** 2026-03-04  
**Status:** Review  
**Context:** Review of ChatGPT's weigh-in on `Demo_Reset_SENREP_Resilience.md`, verified against actual simulator code

---

## Source Material

- ChatGPT's `Demo_Reset_SENREP_Resilience_Weigh_In.md` — five-point hardening review
- [Demo_Reset_SENREP_Resilience.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/research/Demo_Reset_SENREP_Resilience.md) — three-tier reset architecture design
- [simulator/main.py](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/simulator/main.py) — current clear logic, DS ID lists, endpoint guards

---

## Verdict: All Five Points Valid

ChatGPT correctly identified real issues in the current code and in the reset design doc. Three are critical hardening changes; two are good design extensions.

---

## Point 1: SENREP DS Is Currently in the Blast Radius — CONFIRMED

[`CLEARABLE_DS_IDS` at main.py L479–483](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/simulator/main.py#L479) **already includes `044g`** (the SENREP datastream), with a comment `# SENREP + MA-1`. The existing `/clear` endpoint wipes SENREPs today.

The design doc proposed splitting DS lists but didn't flag that the current code already violates Tier 2 semantics. Before any SENREP data goes live, `044g` must be pulled out of `CLEARABLE_DS_IDS` into a new `SENREP_DS_IDS` list.

**Action:** Split `044g` out of `CLEARABLE_DS_IDS` → `SENREP_DS_IDS`.

---

## Point 2: Scope Leak Affects Deletes Too — CONFIRMED, Critical

The [clear loop at main.py L505–538](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/simulator/main.py#L505) iterates `CLEARABLE_DS_IDS`, fetches observations for each DS, and deletes what it sees. But the [OSH scope leak bug](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/research/OSH_Datastream_Observation_Scope_Leak.md) means querying DS `04c0` (MA-1 LOB) can return observations that actually belong to `04d0` (MA-3 LOB). If the delete executes against the wrong DS path, either:
- OSH deletes it anyway → cross-DS collateral damage
- OSH returns 404 → wasted error, observation survives in wrong DS

This is the same bug we fixed in the frontend with the [`datastream@id` filter in loadObservationLayers()](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/demo/src/pages/MapViewPage.vue). The clear function needs the same protection: only delete observations where `obs["datastream@id"] == dsId`.

**Action:** Add `datastream@id` filter to `clear_all_observations()`.

---

## Point 3: Clear Only Gates on Simulator, Not Localizer — CONFIRMED, Real Bug

The [/clear endpoint at main.py L636–645](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/simulator/main.py#L636) checks `state.running` (simulator) but does **not** check `loc_state.running` (localizer). If the localizer is running during a clear, it continues polling LOBs and posting new location estimates — gold dots reappear immediately after deletion. This race condition would look like "/clear doesn't work" during a demo.

Both Tier 2 (`/clear`) and Tier 3 (`/reset`) must gate on `state.running == false AND loc_state.running == false`.

**Action:** Add `loc_state.running` check to `/clear` and future `/reset`.

---

## Point 4: Date-Stamped IDs on SamplingFeature UIDs — Good Extension

Using `C-20260304-001` as both the SENREP `contactId` result field AND the SamplingFeature `uid` is clean. Same identifier everywhere, no mapping table needed. Filtering the track list by date prefix for the demo day is a useful UI convenience.

**Action:** Adopt as part of SENREP implementation.

---

## Point 5: Provenance Fields as Audit Trail — Correct Framing

In Tier 2, gold dots are deleted but SENREPs survive. `sourceFixObsId` in surviving SENREPs will reference a deleted observation. This is fine — the field is audit trail, not a live hyperlink. A tooltip in the UI ("Source observation cleared") would be a nice touch.

**Action:** No code change needed. UI can handle gracefully.

---

## Three Critical Hardening Changes (Pre-Implementation Checklist)

Priority order, all in [simulator/main.py](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/simulator/main.py):

| # | Change | Location | Risk if Skipped |
|---|---|---|---|
| 1 | Split `044g` out of `CLEARABLE_DS_IDS` into `SENREP_DS_IDS` | [L479–483](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/simulator/main.py#L479) | `/clear` nukes all SENREP reports |
| 2 | Add `datastream@id` filter to delete loop in `clear_all_observations()` | [L505–538](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/simulator/main.py#L505) | Scope leak causes cross-DS collateral deletes |
| 3 | Gate `/clear` on both `state.running` AND `loc_state.running` | [L636–645](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/simulator/main.py#L636) | Localizer repopulates during clear, reset appears broken |

---

## GitHub Resources

### Reports (this conversation thread)
- [SENREP_Workflow_Design.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/research/SENREP_Workflow_Design.md) — full SENREP pipeline design
- [SENREP_Track_FOI_Review.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/research/SENREP_Track_FOI_Review.md) — cross-review of FOI modeling positions
- [Demo_Reset_SENREP_Resilience.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/research/Demo_Reset_SENREP_Resilience.md) — three-tier reset architecture

### OSH Bug Reports
- [OSH_Datastream_Observation_Scope_Leak.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/research/OSH_Datastream_Observation_Scope_Leak.md) — scope leak (affects both rendering and clearing)
- [OS4CSAPI/osh-core#3](https://github.com/OS4CSAPI/osh-core/issues/3) — filed issue for scope leak

### Code to Modify
- [simulator/main.py — CLEARABLE_DS_IDS](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/simulator/main.py#L479) — DS list that currently includes SENREP `044g`
- [simulator/main.py — clear_all_observations()](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/simulator/main.py#L489) — delete loop missing `datastream@id` filter
- [simulator/main.py — /clear endpoint](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/simulator/main.py#L636) — only gates on simulator, not localizer
- [simulator/main.py — seed_detection_ranges()](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/simulator/main.py#L130) — auto-seed pattern to replicate for SENREP infrastructure

### Frontend (scope leak filter precedent)
- [MapViewPage.vue — datastream@id filter in loadObservationLayers()](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/demo/src/pages/MapViewPage.vue) — existing pattern to replicate in clear logic

### Existing SENREP Schema
- [bootstrap_v25.py — SENREP schema](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/scripts/bootstrap_v25.py#L449) — full doctrinal SENREP DataRecord
- [bootstrap_v25.py — SET system + procedure + datastream](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/scripts/bootstrap_v25.py#L345) — Monitoring Team A, SENREP procedure

### Migration Inventory
- [AZ-MA-2_MA-3_Oracle_Migration_Report.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/research/phase-6/AZ-MA-2_MA-3_Oracle_Migration_Report.md) — all system/DS IDs including SENREP `044g`
