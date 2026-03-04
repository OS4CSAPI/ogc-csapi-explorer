# SENREP Workflow Design: Completing the Sensor-to-Report Pipeline

**Date:** 2026-03-04  
**Status:** Planning  
**Context:** Response to ChatGPT's SET/SENREP doctrinal anchor report

---

## Part 1: Analysis of the SET/SENREP Approach

### The Core Insight

The key insight from the SET/SENREP proposal is correct: **identity commitment belongs at the reporting tier, not the measurement tier.** The current pipeline is:

```
LOBs (per-node) → Gold Dots (string-level fixes) → ???
```

Gold dots are derived measurement data — hypotheses about where something might be, produced automatically every 5 seconds. Trying to stamp durable identity on them (via SamplingFeature, track features, etc.) fights two problems at once: the conceptual mismatch (noisy bursty data ≠ authoritative identity) AND OSH's broken `@link` persistence.

The SET/SENREP tier solves both:

```
LOBs → Gold Dots → SENREP (identity committed here)
```

### Why This Maps to What We Already Have

1. The three MA nodes and the localizer already produce the input pipeline — LOBs with `trackId`, location estimates with `trackId`. That data flows.

2. A SENREP observation is just another observation on a new datastream. OSH handles basic observation CRUD fine. No `@link` fields needed — `trackId`, `classification`, `estimatedLat/Lon`, `cep50_m` all go in the `result` record as regular fields. OSH won't drop those.

3. The SENREP schema (STR-NO, TIME, QTY, TGT-TYP, etc.) maps directly to a SWE Common `DataRecord` — same pattern already used for LOBs and detection capabilities.

### Refinement: No Separate Feature Resource

The original report suggests "create/maintain the UAV Feature at the SET layer." The stronger position: **don't create a separate Feature resource at all right now.** Use `contactId` as a string field in the SENREP result. Reasons:

- Every Feature created is another thing OSH might lose associations for
- A `contactId` string field in the observation result is atomic — it survives round-trip guaranteed (proven with LOB data)
- When OSH fixes `samplingFeature@link`, the `contactId` field can retroactively become a join key for a SamplingFeature association
- For the frontend, grouping SENREPs by `contactId` is trivial with a JS `Map`

### Implementation Model

- **System:** `urn:os4csapi:system:set:ft-huachuca:alpha` — the SET team
- **Procedure:** `urn:os4csapi:procedure:senrep-generation` — reusable reporting process
- **Datastream:** `senrep_reports` on the SET system
- **Observations:** Each SENREP is an observation with a schema like:

```
contactId (Text) — operator-assigned track ID
classification (Text) — UAS, rotary-wing, fixed-wing, unknown
estimatedLat (Quantity) — from the gold dot fix
estimatedLon (Quantity) — from the gold dot fix
cep50_m (Quantity) — uncertainty
numContributingLobs (Count)
stringId (Text) — which sensor string produced the fix
reportType (Text) — INIT / UPDATE / FINAL
operatorNotes (Text) — free text
timestamp (Time)
```

### Bottom Line

This approach sidesteps the OSH link bugs, is doctrinally sound, completes the workflow, and is implementable with zero changes to the existing LOB/localizer pipeline. Gold dots stay as-is (useful visualization of the measurement layer), and the SENREP becomes the authoritative product.

---

## Part 2: Demo Tab — The Capstone Feature

### Why the Demo Tab

The admin console is infrastructure — start/stop sim, clear data, localizer controls. The SENREP workflow is the *point* of the demo. It's the moment where an audience sees the full pipeline, from acoustic sensor to analyst report, running through an open standard. The demo tab has been reserved for this.

### The Demo Flow

The operator opens the map. The sim is running. They see:

1. **Detection rings** around the three MA nodes — the sensor footprint
2. **LOB lines** appearing in real-time as the UAV enters detection range — raw measurements
3. **Gold dots** appearing where LOBs intersect — the localizer's hypothesis about where the target is
4. The operator watches the gold dots cluster, LOBs converge, confidence builds

Then the operator acts:

5. They click a gold dot (or a cluster), which opens a **SENREP panel** — pre-populated with the localizer's best fix (lat/lon, CEP, contributing sensors, classification)
6. The operator reviews, adjusts classification if needed, adds notes, assigns a contact ID (or accepts auto-generated one)
7. They hit **Submit Report** — it posts a SENREP observation to the SET's datastream
8. A new marker appears on the map — a SENREP icon, distinct from gold dots, representing the authoritative report

That's the full sensor-to-C2 pipeline in one screen for the audience.

### Design Considerations

**Click-to-report flow:** The gold dot's `rawData` already carries `estimatedLat`, `estimatedLon`, `cep50_m`, `numContributingLobs`, `contributingSensors`, `classification`. That's 80% of the SENREP pre-filled just from the click target. The operator only needs to add judgment: confirm/change classification, add `contactId`, type notes.

**SENREP panel placement:** A slide-out side panel or a modal would both work. Side panel is probably better — the operator can still see the map context (LOBs, dots) while reviewing. PrimeVue `Drawer` or `Dialog` both fit.

**Contact ID management:** First report for a new target = INIT, auto-generate `CONTACT-001` (or let operator name it). Subsequent reports for same contact = UPDATE. This is just a text field. The frontend can suggest the next available ID.

**SENREP markers on the map:** A new layer (like gold dots but different icon — maybe a diamond or a STANAG hostile/suspect symbol). These persist across refreshes since they're real observations on the server. This visually separates "what the sensors measured" from "what the operator reported."

**Timeline:** The demo tab could show a feed/log of submitted SENREPs at the bottom — a running report timeline. Builds the narrative for the audience: "three SENREPs generated in the last 10 minutes, tracking one UAS contact."

### What Makes This Demo-Worthy

The story arc is natural. You start the sim, the audience watches data flow in real-time, then the human steps in and makes a decision. That's the CSAPI value proposition — not just sensor data on a map, but the full observe-orient-decide-act loop modeled as standards-compliant resources. Every piece (system, procedure, datastream, observation) is a CSAPI resource the audience can inspect.

### Backend Work

Minimal. One new system, one procedure, one datastream, one schema — all created once via a bootstrap script (like `add_detection_range.py`). The frontend posts observations directly. No simulator changes needed.

---

## Cross-References

- [Gold_Dots_SamplingFeature_Analysis.md](../research/Gold_Dots_SamplingFeature_Analysis.md) — original SamplingFeature semantic gap analysis
- [OSH_SamplingFeature_Link_Persistence_Gap.md](../research/OSH_SamplingFeature_Link_Persistence_Gap.md) — probe showing OSH drops `samplingFeature@link`
- [OSH_Datastream_Observation_Scope_Leak.md](../research/OSH_Datastream_Observation_Scope_Leak.md) — datastream scope leak bug
