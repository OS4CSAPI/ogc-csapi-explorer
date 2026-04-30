# Phase 8 — Live Server Smoke Test Prompt Template

**Purpose:** Live-server validation of the full CSAPI contribution at each Phase 8 roadmap checkpoint. Confirms that **our code still works against real servers** after each Phase 8 task lands. Covers all 9 resource types across **4** live OGC Connected Systems servers — including the newly-deployed `connected-systems-go` (cs-go) instance — with focused regression and verification of Phase 8's API-design refinements (findings 017, 018, 019, 021, 022, 023, 024) and server-interop bug fixes (#166, #167).

**Version:** 1.0
**Date:** April 29, 2026
**Supersedes:** [`docs/governance/smoke-test-prompt-template-phase-7.md`](smoke-test-prompt-template-phase-7.md) (Phase 7 — still valid for historical reference)
**Related:** [P8-ROADMAP.md](../planning/phase-8/P8-ROADMAP.md) — defines the per-task acceptance gates this template runs against. [P8-implementation-guide.md](../planning/phase-8/P8-implementation-guide.md) — authoritative execution detail per task.
**Report destination:** `docs/implementation/live-server-smoke-test-post-phase-8-{checkpoint}.md` (one per checkpoint; see "When to Use" below)

---

## What's New in This Template vs Phase 7

| Aspect                     | Phase 7 Template                        | Phase 8 Template                                                                                                           |
| -------------------------- | --------------------------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| Servers tested             | 3 (OSH + 52North + OS4CSAPI-OSH)        | **4** (OSH + 52North + OS4CSAPI-OSH + **cs-go**)                                                                           |
| Run cadence                | Once at end of phase                    | **Per-roadmap-checkpoint** (after Phase A, B, C, D — see "When to Use")                                                    |
| Phase verification         | Step 16 — 7 specific bug/security fixes | **Per-checkpoint Phase 8 task verification** (017, 019, 021, 022, 023 / 018+024 / #166, #167)                              |
| `@link` form testing       | N/A                                     | **Dedicated step (Step 16)** — explicitly tests the OGC 23-002 §16.1 `@link` form against cs-go (the server that emits it) |
| `endpoint.csapi()` testing | N/A                                     | **Dedicated step (Step 17)** — exercises the new public entry point added by Task D1                                       |
| Finding series             | P7-F1, P7-F2...                         | **P8-F1, P8-F2...**                                                                                                        |
| Required reading           | 10 documents                            | **11 documents** (+ Phase 8 trio: P8-contribution-goal-and-definition, P8-implementation-guide, P8-ROADMAP)                |
| Steps                      | 20                                      | **22** (Steps 16–17 are new Phase 8 verification; CRUD/parser/cross-server steps inherit the 4-server matrix)              |
| Re-litigation policy       | Implicit                                | **Explicit** — locked decisions in P8 trio are not relitigated mid-smoke-test                                              |
| Write-target servers       | 2 (OSH + OS4CSAPI-OSH)                  | **3** (OSH + OS4CSAPI-OSH + cs-go) — confirm cs-go write support during first contact                                      |

---

## When to Use

Phase 8 smoke testing is **checkpoint-based** — run after each Phase letter on the [P8-ROADMAP](../planning/phase-8/P8-ROADMAP.md) lands, not just at the end. The scope of each checkpoint test is calibrated to what the preceding phase changed; the **live-server validation core (Steps 1–15) runs at every checkpoint** because the whole point of these smoke tests is to keep proving our code still talks to real servers.

| Checkpoint         | Trigger                                          | Scope                                                                                                                                                                                                | Report file                                    |
| ------------------ | ------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------- |
| **Post-A**         | All of Phase A (Tasks A1–A4) merged on `phase-8` | **Steps 1–15 (full live-server validation)** + Step 18 Phase A-specific gates: docs review, `CSAPICollectionRef` type round-trip, `availableResources` mutation rejection, pagination JSDoc presence | `live-server-smoke-test-post-phase-8-A.md`     |
| **Post-B**         | All of Phase B (Tasks B1–B2) merged              | **Steps 1–15** + Step 19 Phase B-specific gates: `Datastream*` rename URL parity (post-rename URLs identical to pre-rename), `EndpointError` contract on validator throws                            | `live-server-smoke-test-post-phase-8-B.md`     |
| **Post-C**         | Task C1 merged                                   | **Steps 1–15** + Step 16 (`@link` form fallback against cs-go) — **the marquee Phase 8 server-interop test**                                                                                         | `live-server-smoke-test-post-phase-8-C.md`     |
| **Post-D**         | Task D1 merged                                   | **Steps 1–15** + Step 17 (`endpoint.csapi()` end-to-end against all 4 servers) + re-privatization gate (`root` and `getCollectionDocument` no longer publicly callable)                              | `live-server-smoke-test-post-phase-8-D.md`     |
| **Post-E (final)** | Tasks E1–E2 merged; PR #136 refreshed            | **Steps 1–22 (full template)** — comprehensive validation before tagging @jahow for final review                                                                                                     | `live-server-smoke-test-post-phase-8-final.md` |

Do NOT trigger after doc-only changes outside the source tree, test-only changes, or anything that doesn't affect URL generation, serialization, parsing, or server interaction. Phase 8 has documentation-heavy tasks (A1, A4) — those still warrant Post-A because **other Phase A tasks (A2, A3) do touch types and constructor signatures**.

---

## How to Use

Copy the **Prompt** section below and paste it into the conversation after completing a Phase 8 checkpoint. Replace all `{{...}}` placeholders with actual values, including the **Checkpoint** field (A / B / C / D / final).

---

## Prompt

````
Please perform a Phase 8 live server smoke test of the full CSAPI contribution at checkpoint **{{Checkpoint: A / B / C / D / final}}**.

### Scope

**Phase:** 8
**Checkpoint:** {{A — post Tasks A1–A4 / B — post Tasks B1–B2 / C — post Task C1 / D — post Task D1 / final — post Tasks E1–E2}}
**Phase 8 tasks completed since last smoke test:** {{List Phase 8 task IDs (A1, A2, A3, A4, B1, B2, C1, D1, E1, E2) and the GitHub issue numbers that closed them}}
**Methods/parsers in scope:** All 91+ public methods (post-rename names if Checkpoint ≥ B), all parsers, all 9 resource types, plus checkpoint-specific Phase 8 verification gates
**Last smoke test:** `docs/implementation/{{previous report file}}` (ST#{{N}}, commit {{hash}})

### Required Reading — BEFORE Starting

Read these documents IN FULL before issuing any HTTP requests:

| Document | Location | Purpose |
|----------|----------|---------|
| Known Server Quirks | `docs/governance/known-server-quirks.md` | **CRITICAL** — All known server behaviors, bugs, content-negotiation rules. Prevents re-discovering known issues |
| Previous Smoke Test | `docs/implementation/{{prev report}}` | Most recent prior findings to re-check |
| Cross-Server Analysis | `docs/implementation/cross-server-interoperability-analysis.md` | Known server differences |
| **P8-contribution-goal-and-definition.md** | `docs/planning/phase-8/P8-contribution-goal-and-definition.md` | **Phase 8 goal, scope, locked decisions** — re-litigation is out of scope for this smoke test |
| **P8-implementation-guide.md** | `docs/planning/phase-8/P8-implementation-guide.md` | **Phase 8 execution-level reference** — per-task acceptance criteria |
| **P8-ROADMAP.md** | `docs/planning/phase-8/P8-ROADMAP.md` | **Per-task acceptance gates** that this smoke test cross-checks |
| AI Operational Constraints | `docs/governance/AI_OPERATIONAL_CONSTRAINTS.md` | Behavioral boundaries |
| Fixtures Guide | `docs/testing/fixtures-guide.md` | Fixture structure and shape reference |
| Per-finding MDs (017, 018, 019, 021, 022, 023, 024) | `docs/code-review/` | Authoritative "why" for each Phase 8 finding |
| Issue #166 + #167 threads | GitHub | CS-Go integration findings |
| Parser Source Files | `src/ogc-api/csapi/formats/` (all files) | Exact parser logic to validate |

### Re-Litigation Policy (non-negotiable)

The Phase 8 trio (`P8-contribution-goal-and-definition.md`, `P8-implementation-guide.md`, `P8-ROADMAP.md`) **locks** the design decisions for findings 017–024 and bug fixes #166/#167. If a smoke test discovery makes you want to revisit a locked decision (e.g., "what if we add `@deprecated` aliases after all?"), **stop**. File a new finding (`P8-F{N}`) with severity and ownership; surface it to the user. Do not silently re-decide.

### Server Information

We test against FOUR servers. All four must be tested in every Phase 8 smoke test (with documented exceptions where a server is known broken for a given resource type).

#### Server 1: OpenSensorHub (OSH)

- **URL:** `http://45.55.99.236:8080/sensorhub/api`
- **Auth:** Basic authentication required
- **⚠️ CREDENTIAL REMINDER:** The username and password are NOT stored in this repository. If you do not have the credentials from a prior conversation context, you MUST ask the user for them before proceeding. Do not guess, do not skip this server.
- **PowerShell pattern:**
  ```powershell
  $cred = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("{{username}}:{{password}}"))
  $headers = @{ Authorization = "Basic $cred" }
  Invoke-RestMethod -Uri "http://45.55.99.236:8080/sensorhub/api" -Headers $headers
  ```
- **Key quirks** (read `known-server-quirks.md` for full details):
  - Ignores Accept headers — use `?f=json`, `?f=geojson`, `?f=sml3`
  - Full CRUD; all Part 2 endpoints work
  - Lowercase `/controlstreams`; do NOT send `Accept: application/geo+json` on POST

#### Server 2: 52North

- **URL:** `https://csa.demo.52north.org/`
- **Auth:** None required
- **SSL:** Certificate is expired — all PowerShell commands MUST use `-SkipCertificateCheck`
- **Key quirks:** Accept-routed dual-backend; Part 2 broken (500/400/404); rich SensorML

#### Server 3: OS4CSAPI-OSH (User-operated OSH instance)

- **URL:** `https://os4csapi-osh.duckdns.org/sensorhub/api`
- **Auth:** Basic authentication required (⚠️ ask user for credentials — not stored in repo)
- **SSL:** Valid certificate (no `-SkipCertificateCheck` needed)
- **Expected quirks:** Same family as Server 1 (OSH).

#### Server 4: connected-systems-go (cs-go) — NEW IN PHASE 8

- **URL:** `https://129-80-248-53.sslip.io/csapi-go`
- **Auth:** {{Confirm with user — likely none, but verify}}
- **SSL:** HTTPS — verify cert behavior in Step 2 (sslip.io domains may have specific cert handling; if the cert is invalid, use `-SkipCertificateCheck`)
- **PowerShell pattern (no auth assumed; adjust if user confirms otherwise):**
  ```powershell
  Invoke-RestMethod -Uri "https://129-80-248-53.sslip.io/csapi-go"
  # If SSL fails, retry with: -SkipCertificateCheck
  ```
- **Why this server matters for Phase 8:** This is the **third independent CSAPI implementation** (alongside the two OSH variants and 52North). Integration testing against cs-go via [`ogc-csapi-explorer`](https://github.com/OS4CSAPI/ogc-csapi-explorer) surfaced **Issues #166 and #167**. cs-go is the server that emits Part 2 cross-references in the **`@link` object form** (per OGC 23-002 §16.1) — which is exactly what Task C1 makes our parsers handle. Validating Phase 8's `@link`-fallback fix against cs-go is the marquee server-interop check of this smoke test cycle.
- **Expected quirks (to confirm during first-contact discovery):**
  - May default to `limit=10` (vs OSH's `limit=100`) — relevant for #167's pagination contract
  - May emit `system@link`, `datastream@link`, `foi@link`, `controlstream@link`, `command@link` object forms in Part 2 responses
  - Conformance class set may differ from OSH/52N — record everything
  - Write operation support: confirm during Step 2; if supported, include cs-go in CRUD testing (Step 10)
- **⚠️ FIRST-CONTACT PROTOCOL (Phase 8 first-time test):** This server has NOT been previously tested in a smoke test. Before running the standard test suite against it, perform exploratory discovery in Step 2 (items 7–14 below) to understand its capabilities, data inventory, and unique quirks. Document ALL differences from Servers 1–3.

### Finding Numbering

Phase 8 findings use a new series: **P8-F1**, **P8-F2**, **P8-F3**, etc.

Prior findings (F1–F90 from Phase 2/3, P4-F{N}, P5-F{N}, P7-F{N}) retain their original numbers in the regression check. New findings discovered in Phase 8 get the P8-F prefix.

### Test Instructions

Follow this exact sequence. Record EVERYTHING — every HTTP request, every response status, every observation.

---

#### Step 1: Document Prior Findings (Regression Check)

Read the most recent prior smoke test report (Phase 7's ST#24, plus any post-Phase-7 retests). For each prior finding:

- If marked **"Fixed"** — re-verify with a live request
- If marked **"Deferred"** — confirm still deferred
- If marked **"Server limitation"** — confirm still present
- If marked **"Retracted"** / **"Resolved"** — re-verify the resolution holds

**Phase 8 attention items:** Phase 8 changes the public API surface (renames, type tightening, error standardization, new `endpoint.csapi()` method). Any prior finding related to error handling, naming, or the `endpoint.root` / `getCollectionDocument` access pattern deserves extra scrutiny — Phase 8 should have improved them, not regressed them.

---

#### Step 2: Test Server Connectivity, Profiles, and Resource Inventory

For EACH of the FOUR servers:

1. Fetch the root API document
2. Fetch `/conformance` — record conformance classes
3. Fetch `/collections` — record all collections and their links
4. Document root document links (resource type → URL mappings)
5. Build the full resource inventory:

| Endpoint          | Accept / `?f=` Used | HTTP Status | Item Count | Notes |
| ----------------- | ------------------- | ----------- | ---------- | ----- |
| /systems          |                     |             |            |       |
| /deployments      |                     |             |            |       |
| /procedures       |                     |             |            |       |
| /samplingFeatures |                     |             |            |       |
| /properties       |                     |             |            |       |
| /datastreams      |                     |             |            |       |
| /observations     |                     |             |            |       |
| /controlstreams   |                     |             |            |       |
| /commands         |                     |             |            |       |

6. Record specific resource IDs that will be used in subsequent steps (at least 2 per resource type if available)

**For Server 4 (cs-go — first contact in Phase 8):**

7. Compare its conformance classes against Servers 1–3 — note any differences
8. Build a content negotiation profile: does `?f=json` work? Accept headers? Default content type?
9. Record its data inventory — may have different/fewer resources than the OSH servers
10. Test if Part 2 endpoints are available (datastreams, observations, controlstreams, commands)
11. **Critical for Phase 8:** Inspect Part 2 responses for the `@link` object form. Record at least one example per cross-reference field (`system@link`, `datastream@link`, `foi@link`, `controlstream@link`, `command@link`). These confirm Task C1's fix is necessary and exercise its acceptance gate.
12. Test pagination defaults: fetch `/systems` with no `limit` parameter — what default page size does cs-go return? Compare to OSH's default. This validates Issue #167's premise.
13. Confirm SSL cert handling and write-operation support
14. Document ALL differences from Servers 1–3 in a dedicated "Server 4 (cs-go) Discovery Notes" section

---

#### Step 3: Test Resource Discovery

Simulate `scanCsapiLinks()` behavior against ALL FOUR servers:

1. **Convention 1** (`ogc-cs:` prefix): Check if any links use this prefix
2. **Convention 2** (plain rel name): Check root document links for plain resource type names
3. **Convention 3** (`rel: "items"` + href): Verify segment extraction with query parameters in hrefs (must be stripped), `featuresOfInterest` naming (must be normalized to `samplingFeatures`), mixed leading-slash conventions

Record how many resource types are discovered per convention per server.

**Phase 7 carry-forward security verification:** Confirm `scanCsapiLinks()` still rejects non-HTTP(S) schemes (Issue #147 from Phase 7 — re-verify, do not regress).

---

#### Step 4: Hierarchical Navigation

Test parent-child navigation across all four servers:

| Navigation                  | URL Pattern                        | OSH | 52N | OS4 | cs-go | Notes |
| --------------------------- | ---------------------------------- | --- | --- | --- | ----- | ----- |
| System → subsystems         | `/systems/{id}/subsystems`         |     |     |     |       |       |
| Deployment → subdeployments | `/deployments/{id}/subdeployments` |     |     |     |       |       |
| System → datastreams        | `/systems/{id}/datastreams`        |     |     |     |       |       |
| System → controlstreams     | `/systems/{id}/controlstreams`     |     |     |     |       |       |
| Datastream → observations   | `/datastreams/{id}/observations`   |     |     |     |       |       |
| ControlStream → commands    | `/controlstreams/{id}/commands`    |     |     |     |       |       |

(Full list per Phase 7 template — extended with the cs-go column.)

---

#### Step 5: Test URL Generation — All Implemented Methods

For EACH server, test every implemented builder method. **For Checkpoint ≥ B**, the methods carry the post-Task-B1 names (`getDatastreams`, `getDatastream`, `createDatastream`, etc. — _not_ `getDataStreams`). For Checkpoint A only, use the pre-rename names. Record:

| Method | Generated URL | Server | HTTP Status | Notes |
| ------ | ------------- | ------ | ----------- | ----- |

For methods with no data, mark **N/A (no data)** — the URL pattern is still validated by confirming the list endpoint works.

---

#### Step 6: Test Query Parameter Acceptance

Test each parameter against all four servers:

| Parameter           | Method Used | URL | OSH | 52N | OS4 | cs-go |
| ------------------- | ----------- | --- | --- | --- | --- | ----- |
| limit               |             |     |     |     |     |       |
| offset              |             |     |     |     |     |       |
| q                   |             |     |     |     |     |       |
| bbox                |             |     |     |     |     |       |
| datetime (single)   |             |     |     |     |     |       |
| datetime (interval) |             |     |     |     |     |       |
| id (single)         |             |     |     |     |     |       |
| id (array)          |             |     |     |     |     |       |
| recursive           |             |     |     |     |     |       |
| f (format)          |             |     |     |     |     |       |
| cursor              |             |     |     |     |     |       |
| parent              |             |     |     |     |     |       |
| sortBy (single)     |             |     |     |     |     |       |
| sortBy (array)      |             |     |     |     |     |       |
| sortOrder (asc)     |             |     |     |     |     |       |
| sortOrder (desc)    |             |     |     |     |     |       |

**Phase 8 carry-forward (sortBy/sortOrder from Phase 7 Issue #161):** still works post-rename; URLs unchanged.

---

#### Step 7: DataStreams, Observations, and Schemas (Part 2)

Target: Server 1 (OSH), Server 3 (OS4CSAPI-OSH), Server 4 (cs-go). 52North Part 2 known-broken — skip.

1. List datastreams — record count, sample IDs
2. Fetch individual datastream by ID
3. Fetch datastream schema (`/datastreams/{id}/schema`)
4. List observations for a datastream
5. Test temporal filtering (single, open-ended, bounded intervals)

**Phase 8-specific within Step 7:** When inspecting datastream and observation responses on cs-go, **explicitly capture every `@link`-form cross-reference field** (e.g., `system@link`, `datastream@link`, `foi@link`). Record the full object value (href + title + any other fields). This data feeds Step 16's `@link` fallback validation.

---

#### Step 8: ControlStreams, Commands, and Command Status (Part 2)

Target: Server 1, Server 3, Server 4. Same as Step 7 for the control side of Part 2.

**Phase 8-specific within Step 8:** Capture every `controlstream@link` and `command@link` object form on cs-go. Feeds Step 16.

---

#### Step 9: SensorML Content Negotiation

Test all four servers for SML access:

1. **OSH (Server 1):** `?f=sml3`
2. **52N (Server 2):** `Accept: application/sml+json`
3. **OS4CSAPI-OSH (Server 3):** `?f=sml3`
4. **cs-go (Server 4):** First-contact — try both `?f=sml3` and `Accept: application/sml+json`; record which works

Cross-server SML comparison (4-way): field presence, vocabulary format, structural richness.

---

#### Step 10: FULL CRUD Testing — Write Operations

**⚠️ CRITICAL RULES** (carry-forward from Phase 7):
- Only delete what you create. Never delete pre-existing data.
- Create test data first; use; clean up at end.
- Record every write operation.
- If a write fails, document as a finding — do not skip.

**Phase 8 update:** Add cs-go to the CRUD matrix if Step 2 confirms it supports writes.

##### 10a: Create Test Resources

Run against Servers 1, 3, and 4 (if cs-go supports writes). 52N write support remains untested.

(All 10 create operations per Phase 7 template — System, Procedure, Deployment, SamplingFeature, Subsystem, Subdeployment, Datastream, ControlStream, Observation, Command.)

**Cleanup table extended:**

| Resource Type   | OSH ID | OS4 ID | cs-go ID | Parent | Created At |
| --------------- | ------ | ------ | -------- | ------ | ---------- |
| System          |        |        |          |        |            |
| ...             |        |        |          |        |            |

##### 10b–10e

Read-back verification, update, delete (reverse order), and 52N write attempt — all per Phase 8 template, extended with cs-go column where applicable.

---

#### Step 11: Format Parser Validation Against Live Data

For each parser, fetch live data from ALL applicable servers and feed through the parser.

##### 11a: Fixture Shape Comparison (4-way)

| Resource Type | Server | Live Fields | Fixture Fields | Extra in Live | Missing from Live |
| ------------- | ------ | ----------- | -------------- | ------------- | ----------------- |
| Property      | OSH    |             |                |               |                   |
| Property      | OS4    |             |                |               |                   |
| Property      | cs-go  |             |                |               |                   |
| Datastream    | OSH    |             |                |               |                   |
| Datastream    | OS4    |             |                |               |                   |
| Datastream    | cs-go  |             |                |               |                   |
| ...           | ...    |             |                |               |                   |

##### 11b–11g: Per-Parser Validation

Per-parser tables extended to include cs-go. **Phase 8-specific assertion within 11c–11g:** for cs-go responses that contain `@link` cross-reference fields, confirm the parser correctly extracts the ID from the `href`'s last URL segment (after Task C1 lands).

##### 11h: Cross-Server Parser Tolerance (4-way)

Document any field naming, nesting, or value-format differences across all four servers. Verify parsers handle all server shapes without throwing.

---

#### Step 12: Helper Function Validation

(Carry-forward from Phase 7 — `normalizeObservedProperties`, `normalizeStatusCode`, `RESULT_TYPES`, `COMMAND_STATUS_CODES` — extended to include cs-go inputs.)

---

#### Step 13: Recognition, Extraction, and Parsing Validation

(Carry-forward from Phase 7 — `classifyFeature`, `parseValidTime`, vocabulary inventory, content-type matrix — all extended to 4-way.)

---

#### Step 14: Schema Parsing Validation

(Carry-forward — datastream/controlstream schemas from OSH, OS4, **and cs-go**; SWE Common parser results.)

---

#### Step 15: Cross-Server Comparison (4-Way)

Produce a 4-way comparison table:

| Dimension                      | OpenSensorHub (S1) | 52North (S2) | OS4CSAPI-OSH (S3) | cs-go (S4) | All match? |
| ------------------------------ | ------------------ | ------------ | ------------------ | ---------- | ---------- |
| Conformance classes advertised |                    |              |                    |            |            |
| Discovery convention(s) used   |                    |              |                    |            |            |
| Default content type           |                    |              |                    |            |            |
| Content negotiation mechanism  |                    |              |                    |            |            |
| Response envelope format       |                    |              |                    |            |            |
| featureType vocabulary         |                    |              |                    |            |            |
| validTime format               |                    |              |                    |            |            |
| SensorML access method         |                    |              |                    |            |            |
| SensorML richness              |                    |              |                    |            |            |
| Part 2 endpoint availability   |                    |              |                    |            |            |
| Write operation support        |                    |              |                    |            |            |
| Sub-resource endpoint support  |                    |              |                    |            |            |
| SSL/TLS status                 |                    |              |                    |            |            |
| Auth requirement               |                    |              |                    |            |            |
| Parser compatibility (Part 2)  |                    |              |                    |            |            |
| sortBy/sortOrder support       |                    |              |                    |            |            |
| **Default page size**          |                    |              |                    |            |            |
| **Cross-ref form: @id only**   |                    |              |                    |            |            |
| **Cross-ref form: @link only** |                    |              |                    |            |            |
| **Cross-ref form: both**       |                    |              |                    |            |            |

---

#### Step 16: Phase 8 — Issue #166 `@link` Fallback Verification (CHECKPOINT C / D / final)

> **Run this step at Checkpoints C, D, and final.** Skip at Checkpoints A and B (Task C1 not yet landed).

This step is the **single most important live-server verification in the entire Phase 8 cycle**. Task C1 ships a fix for spec-conformance with OGC 23-002 §16.1; cs-go is the server that exercises it. If Step 16 doesn't pass on cs-go, Phase 8 is not done.

##### 16a: Confirm cs-go emits `@link` form

Using observations from Step 7 and commands from Step 8 (cs-go), confirm at least one example of each:

| Field           | cs-go example href | Last URL segment (= expected extracted ID) |
| --------------- | ------------------ | ------------------------------------------ |
| `system@link`         |              |                                            |
| `datastream@link`     |              |                                            |
| `foi@link` / `samplingFeature@link` |    |                                            |
| `controlstream@link`  |              |                                            |
| `command@link`        |              |                                            |

If any of these are absent on cs-go, document why (server may emit only some forms; that is acceptable).

##### 16b: Confirm parsers extract IDs correctly

For each `@link`-form example, feed the raw cs-go response through the corresponding parser (`parseDatastream`, `parseControlStream`, `parseObservation`, `parseCommand`, `parseCommandStatus`):

| Parser             | Input field      | href value | Expected `*Id` | Actual `*Id` | Match? |
| ------------------ | ---------------- | ---------- | -------------- | ------------ | ------ |
| parseDatastream    | system@link      |            |                |              |        |
| parseControlStream | system@link      |            |                |              |        |
| parseObservation   | datastream@link  |            |                |              |        |
| parseObservation   | foi@link / samplingFeature@link | |        |              |        |
| parseCommand       | controlstream@link |          |                |              |        |
| parseCommandStatus | command@link     |            |                |              |        |

##### 16c: Confirm `@id` precedence still holds

For at least one parser, fabricate an input (or find a mixed-form server response) that contains BOTH `@id` and `@link` and confirm `@id` wins (per Task C1's locked decision).

##### 16d: Issue #167 — pagination contract live-validation

For each list endpoint on cs-go:

1. Fetch with no `limit` parameter — record the default page size cs-go applies
2. Fetch with `limit=100` — confirm cs-go honors it (or documents otherwise)
3. Inspect the response's `links` array for a `rel: "next"` link — record its presence
4. Follow the `next` link — confirm a second page is reachable
5. Cross-reference: this is the contract our Phase 8 JSDoc (Task A4) documents; the smoke test confirms the contract is real on cs-go

| Endpoint    | Default `limit` | `?limit=100` honored? | `next` link present? | Page 2 reachable? |
| ----------- | --------------- | --------------------- | -------------------- | ----------------- |
| /systems    |                 |                       |                      |                   |
| /datastreams |                |                       |                      |                   |
| /observations |               |                       |                      |                   |
| /controlstreams |             |                       |                      |                   |
| /commands   |                 |                       |                      |                   |

---

#### Step 17: Phase 8 — `endpoint.csapi()` End-to-End Verification (CHECKPOINT D / final)

> **Run this step at Checkpoints D and final.** Skip at Checkpoints A, B, and C (Task D1 not yet landed).

This step exercises the new public `OgcApiEndpoint.csapi(collectionId)` entry point against all four servers and confirms the locked decisions for Findings 018 and 024 hold end-to-end.

##### 17a: Happy path against each server

For each of the four servers, in a scratch script (or via the demo app):

```ts
const endpoint = new OgcApiEndpoint('{{server URL}}');
const builder = await endpoint.csapi('{{collection ID with CSAPI conformance}}');
const url = builder.getDatastreams({ limit: 10 });
const response = await fetch(url, { /* auth headers as needed */ });
console.assert(response.ok, 'expected 2xx');
````

| Server | Collection ID | `endpoint.csapi()` returned `CSAPIQueryBuilder`? | Generated URL | HTTP status |
| ------ | ------------- | ------------------------------------------------ | ------------- | ----------- |
| OSH    |               |                                                  |               |             |
| 52N    |               |                                                  |               |             |
| OS4    |               |                                                  |               |             |
| cs-go  |               |                                                  |               |             |

##### 17b: Error contract — non-CSAPI collection

Pick a collection on any server that does NOT advertise CSAPI conformance. Call `endpoint.csapi(thatId)`. Expect `EndpointError` thrown with message describing the lack of CSAPI support.

| Server | Collection ID | Threw? | `instanceof EndpointError`? | Message |
| ------ | ------------- | ------ | --------------------------- | ------- |
|        |               |        |                             |         |

##### 17c: Error contract — bogus collection

Call `endpoint.csapi('does-not-exist-xyz')`. Expect `EndpointError` with the upstream `TypeError` wrapped (per Task B2 + Task D1 contract).

| Server | Threw? | `instanceof EndpointError`? | Original error preserved in message? |
| ------ | ------ | --------------------------- | ------------------------------------ |
|        |        |                             |                                      |

##### 17d: Re-privatization gate

In a scratch script, attempt to access `endpoint.root` and `endpoint.getCollectionDocument(...)`. **Expect TypeScript compile error** (these are now private).

| Access pattern                          | Compile error? (expected: yes) |
| --------------------------------------- | ------------------------------ |
| `endpoint.root`                         |                                |
| `endpoint.getCollectionDocument('foo')` |                                |

##### 17e: `isCollectionInfo` cast removed

`git grep -n "isCollectionInfo" -- src/ogc-api/csapi/` must return zero matches. Record output.

##### 17f: Standalone factory shape

Confirm `createCSAPIBuilder` is now value-shaped: `(collection: CSAPICollectionRef, resourceUrls: ReadonlyMap<...>): CSAPIQueryBuilder`. No `await`s; no `OgcApiEndpoint` parameter. Construct one from literal values and confirm the resulting builder generates the same URLs as one obtained via `endpoint.csapi()`.

---

#### Step 18: Phase A Per-Task Verification (CHECKPOINT A / final)

> Run at Checkpoints A and final.

##### 18a: Task A1 — URL-builder framing in module docs

Open and review:

- `src/ogc-api/csapi/index.ts` — module docblock present with the 5-step worked example
- `src/ogc-api/csapi/factory.ts` — `createCSAPIBuilder` JSDoc cross-references the module docblock
- `src/ogc-api/csapi/url_builder.ts` — class-level JSDoc on `CSAPIQueryBuilder` reinforces the URL-builder framing
- `README.md` — "Connected Systems — making a request" section present

| Surface                | Present? | URL-builder framing unmistakable? |
| ---------------------- | -------- | --------------------------------- |
| `csapi/index.ts`       |          |                                   |
| `csapi/factory.ts`     |          |                                   |
| `csapi/url_builder.ts` |          |                                   |
| `README.md`            |          |                                   |

##### 18b: Task A2 — `CSAPICollectionRef` type extraction

```bash
git grep -n "OgcApiCollectionInfo" -- src/ogc-api/csapi/url_builder.ts
# expect: 0 matches
```

Construct a literal `CSAPICollectionRef` and pass it to `new CSAPIQueryBuilder(...)` — must compile. Pass an `OgcApiCollectionInfo` — must still compile (structural compatibility).

##### 18c: Task A3 — `availableResources` ReadonlySet

In a scratch script:

```ts
const builder = await endpoint.csapi('foo');
builder.availableResources.add('xxx'); // expect: TypeScript compile error
```

Record the compile-error output.

##### 18d: Task A4 — Pagination JSDoc

Open `src/ogc-api/csapi/url_builder.ts`. Verify:

- Module/class docblock has a "Pagination" anchor section
- Every `get*` list method's JSDoc has an `@remarks` block referencing the Pagination contract

Spot-check at least 4 list methods: `getSystems`, `getDatastreams` (post-B1 name), `getControlStreams`, `getCommands`.

---

#### Step 19: Phase B Per-Task Verification (CHECKPOINT B / final)

> Run at Checkpoints B and final.

##### 19a: Task B1 — `Datastream` rename

```bash
git grep -n "DataStream" -- 'src/ogc-api/csapi/'
# expect: 0 matches (modulo Datastream — note the case difference)
```

```bash
npm run typecheck && npm run test:browser src/ogc-api/csapi/url_builder.spec.ts
# expect: both green
```

For 3 renamed methods (`getDatastreams`, `createDatastream`, `getSystemDatastreams`), confirm the URL strings produced are byte-identical to the pre-rename equivalents (URLs do not change; only method names change).

| Method (post-rename)       | URL produced              | Matches pre-rename URL? |
| -------------------------- | ------------------------- | ----------------------- |
| `getDatastreams`           | /datastreams              |                         |
| `createDatastream`         | /datastreams              |                         |
| `getSystemDatastreams(id)` | /systems/{id}/datastreams |                         |

##### 19b: Task B2 — Validators throw `EndpointError`

```bash
git grep -n "throw new Error\|throw new TypeError" -- src/ogc-api/csapi/
# expect: 0 matches
```

In a scratch script, exercise at least 3 validator paths (e.g., `validateLimit(-1)`, `validateBbox(['bad'])`, `parseProperty(null)`) and confirm each throws an `EndpointError`.

| Validator       | Input     | Threw? | `instanceof EndpointError`? |
| --------------- | --------- | ------ | --------------------------- |
| `validateLimit` | `-1`      |        |                             |
| `validateBbox`  | `['bad']` |        |                             |
| `parseProperty` | `null`    |        |                             |

---

#### Step 20: Classify All New Findings

For each new finding (P8-F{N} numbering):

- **ID:** P8-F{N}
- **Severity:** Critical / Moderate / Low / Informational
- **Category:** Code bug / Server limitation / Interoperability / Naming / Design gap / Parser gap / Security
- **Affects:** Function or code path
- **Ownership:** Ours / Upstream / Shared
- **Status:** Needs fix / Needs design decision / Informational / Deferred
- **Evidence:** Request + response

---

#### Step 21: Generate Impact Assessment

For "Ours" or "Shared" findings: identify file/function, assess upstream impact (does the fix touch any upstream-authored file?), estimate complexity (one-line / small / medium / architectural). For parser-related findings: indicate whether unit test fixtures need updating.

---

#### Step 22: Present Findings to User

After Steps 1–21, present a summary BEFORE writing the report:

1. Quick verdict: pass / fail / conditional
2. Count of regression issues (if any)
3. Count of new findings by severity
4. CRUD test results summary per server (incl. cs-go if applicable)
5. Parser validation summary — passes, issues, fixture mismatches
6. **Phase 8 checkpoint verification summary** — all gates for the active checkpoint green?
7. **cs-go discovery summary** — page-size default, `@link` form coverage, Part 2 availability, write support
8. **`@link` fallback verification result** (Checkpoint C+) — does cs-go interop work end-to-end?
9. **`endpoint.csapi()` verification result** (Checkpoint D+)
10. Any critical items
11. Ask: "Should I write the full report and commit it?"

---

### Report Format

Generate the report at `docs/implementation/live-server-smoke-test-post-phase-8-{{checkpoint}}.md`.

````markdown
# Live Server Smoke Test — Post Phase 8 ({{Checkpoint}})

**Date:** {{YYYY-MM-DD}}
**Smoke Test Number:** ST#{{N}}
**Milestone:** After completing Phase 8 Checkpoint {{A / B / C / D / final}} — {{tasks completed}}
**Servers:** OpenSensorHub (S1), 52North (S2), OS4CSAPI-OSH (S3), cs-go (S4)
**Auth:** S1/S3: Basic auth required (credentials not stored in repo); S2: None (expired SSL cert); S4: {{TBD per first-contact}}
**Purpose:** Phase 8 checkpoint validation — live-server interop + per-task acceptance gate verification
**Finding Series:** Phase 8 (P8-F1, P8-F2, ...)
**Template:** `docs/governance/smoke-test-prompt-template-phase-8.md` v1.0
**Test Baseline:** {{N}} CSAPI tests ({{M}} suites), 0 tsc errors

> Phase 8 trio: see [P8-contribution-goal-and-definition.md](../planning/phase-8/P8-contribution-goal-and-definition.md), [P8-implementation-guide.md](../planning/phase-8/P8-implementation-guide.md), [P8-ROADMAP.md](../planning/phase-8/P8-ROADMAP.md). Locked decisions are not relitigated in this smoke test.

## Test Methodology

{{Per checkpoint: cite the Phase 8 tasks completed since the last smoke test, the per-task acceptance gates verified, and the live-server cross-check coverage. Always include the cs-go interop angle.}}

## Server Profiles

### Server 1: OpenSensorHub

{{...}}

### Server 2: 52North

{{...}}

### Server 3: OS4CSAPI-OSH

{{...}}

### Server 4: cs-go

{{Full discovery profile if first contact; otherwise carry-forward + delta from prior smoke test}}

## Results

### Prior Findings — Regression Check

{{Standard table}}

### URL Generation — All Methods (4-Server)

{{Standard table extended with cs-go column}}

### Query Parameter Acceptance (4-Server)

{{Standard table extended}}

### Hierarchical Navigation (4-Server)

{{...}}

### Part 2 — DataStreams & Observations (OSH + OS4 + cs-go)

{{...}}

### Part 2 — ControlStreams & Commands (OSH + OS4 + cs-go)

{{...}}

### SensorML Content Negotiation (4-Way)

{{...}}

### CRUD Operations

{{Standard tables; cs-go included if writes supported}}

### Format Parser Validation (4-Server)

{{Per-parser tables extended}}

### Helper Function Validation

{{...}}

### Recognition, Extraction, Parsing

{{...}}

### Schema Parsing Validation

{{...}}

### Phase 8 Checkpoint Verification (active checkpoint only)

#### Checkpoint A gates (if applicable)

| Gate                                                                    | Pass? | Evidence |
| ----------------------------------------------------------------------- | ----- | -------- |
| Task A1 — docs framing across 4 surfaces                                |       |          |
| Task A2 — `git grep "OgcApiCollectionInfo" -- url_builder.ts` returns 0 |       |          |
| Task A3 — `availableResources` mutation is a compile error              |       |          |
| Task A4 — Pagination JSDoc on every list method                         |       |          |

#### Checkpoint B gates (if applicable)

| Gate                                                                                        | Pass? | Evidence |
| ------------------------------------------------------------------------------------------- | ----- | -------- |
| Task B1 — `git grep "DataStream" -- src/ogc-api/csapi/` returns 0                           |       |          |
| Task B1 — URL parity (3 spot-checks)                                                        |       |          |
| Task B2 — `git grep "throw new Error\|throw new TypeError" -- src/ogc-api/csapi/` returns 0 |       |          |
| Task B2 — 3 validator paths throw `EndpointError`                                           |       |          |

#### Checkpoint C gates (if applicable)

| Gate                                                      | Pass? | Evidence |
| --------------------------------------------------------- | ----- | -------- |
| cs-go emits `@link` form (≥1 example per cross-ref field) |       |          |
| All Part 2 parsers extract correct IDs from `@link.href`  |       |          |
| `@id` precedence preserved when both forms present        |       |          |
| #167 — cs-go pagination contract observable end-to-end    |       |          |

#### Checkpoint D gates (if applicable)

| Gate                                                                        | Pass? | Evidence |
| --------------------------------------------------------------------------- | ----- | -------- |
| `endpoint.csapi()` happy path on all 4 servers                              |       |          |
| `endpoint.csapi()` non-CSAPI collection throws `EndpointError`              |       |          |
| `endpoint.csapi()` bogus collection wraps upstream error in `EndpointError` |       |          |
| `endpoint.root` / `endpoint.getCollectionDocument` are private              |       |          |
| `git grep "isCollectionInfo" -- src/ogc-api/csapi/` returns 0               |       |          |
| Standalone `createCSAPIBuilder` is value-shaped                             |       |          |

## Cross-Server Comparison (4-Way)

| Dimension | OSH | 52N | OS4 | cs-go | All match? |
| --------- | --- | --- | --- | ----- | ---------- |
| ...       | ... | ... | ... | ...   |            |

## Server 4 (cs-go) — First-Contact Discovery Notes (or Delta)

{{If first contact: full discovery section. Otherwise: delta from prior smoke test.}}

## New Findings

### P8-F1 ({{Severity}}): {{Title}}

**Severity:** {{...}}
**Category:** {{...}}
**Affects:** {{...}}
**Ownership:** {{...}}
**Evidence:** {{...}}
**Status:** {{...}}

## What WORKS (Verified)

| Capability | Status |
| ---------- | ------ |

## What Remains

| Issue | Severity | Component | Target |
| ----- | -------- | --------- | ------ |

## Comparison: Previous Smoke Test → This Smoke Test

| Dimension                   | Previous (ST#{{N-1}}) | This (ST#{{N}}) |
| --------------------------- | --------------------- | --------------- |
| Test baseline               |                       |                 |
| Servers tested              |                       | 4               |
| Phase 8 tasks closed        |                       |                 |
| `@link` interop verified    | N/A                   | {{C+ only}}     |
| `endpoint.csapi()` verified | N/A                   | {{D+ only}}     |
| Findings total              |                       |                 |

## Verdict

{{3–4 paragraph assessment:

- Prior findings stable (no regressions)?
- Active-checkpoint Phase 8 gates all green?
- cs-go interop confirmed (esp. `@link` fallback at Checkpoint C+)?
- `endpoint.csapi()` end-to-end at Checkpoint D+?
- Any critical items?
- Ready for next checkpoint / `clean-pr` squash / @jahow review?
  }}

```

Then commit the report, push, and confirm the file is at the expected path.

If any new findings are classified as "Ours — Needs fix", create a GitHub issue using `docs/governance/issue-creation-prompt-template-phase-8.md` (NOT the general code-review template — Phase 8 issues use the Phase 8 variant).
```
````

---

## Post-Smoke-Test Workflow

After the smoke test report is generated:

1. **Review new findings** — decide which are "fix now" vs "defer"
2. **Create GitHub issues** for "Ours — Needs fix" findings using [`issue-creation-prompt-template-phase-8.md`](issue-creation-prompt-template-phase-8.md)
3. **Complete fix issues** before proceeding to the next Phase 8 checkpoint
4. **Update `known-server-quirks.md`** if new server behavior is discovered (especially for cs-go)
5. **Update unit test fixtures** if live data shape mismatches are discovered
6. **At Checkpoint final:** the smoke test report is the **final live-server gate** before the squash to `clean-pr` and PR #136 refresh (Tasks E1+E2)

---

## Critical Rules (Non-Negotiable)

- [ ] **Read the Phase 8 trio FIRST** — `P8-contribution-goal-and-definition.md`, `P8-implementation-guide.md`, `P8-ROADMAP.md`. They lock the decisions; this smoke test does not relitigate.
- [ ] **Read `known-server-quirks.md` SECOND** — Prevents re-discovering known issues.
- [ ] **All FOUR servers tested** — Every step that involves HTTP requests MUST hit all four servers (except Part 2 on 52N, which is known broken). Single-server testing missed real bugs in prior smoke tests.
- [ ] **cs-go is the marquee Phase 8 server** — It is the integration target that surfaced #166 and #167. Step 16 (`@link` fallback) and Step 7/8 cs-go inspection are non-negotiable at Checkpoint C+.
- [ ] **Credentials not in repo** — Username and password for OSH and OS4CSAPI-OSH are NEVER committed, NEVER written into any file, NEVER in the report. If you don't have them, ask the user. Same rule for cs-go if it requires auth.
- [ ] **52North needs `-SkipCertificateCheck`** — Every PowerShell command to 52N MUST include this flag.
- [ ] **All prior findings re-checked** — Cover EVERY finding from EVERY prior smoke test, not just the most recent.
- [ ] **New findings get P8-F numbering** — Do not continue P7-F or P5-F series.
- [ ] **New findings get ownership classification** — "Ours" / "Upstream" / "Shared" with evidence.
- [ ] **Only delete what you create** — CRUD testing creates and deletes ONLY its own data. Per server. Never delete pre-existing resources.
- [ ] **Create before you test** — Don't rely on existing resources for CRUD testing.
- [ ] **Record every HTTP request** — Full request (method, URL, headers, body) and full response.
- [ ] **Content-Type matters for writes** — Part 1 POST/PUT uses `application/geo+json`. Part 2 POST/PUT uses `application/json`.
- [ ] **Test exhaustively** — Every method the library exposes, against every applicable server.
- [ ] **Validate parsers against live data** — Every implemented parser MUST be traced against at least 2 real responses from each applicable server.
- [ ] **Compare fixture shapes to live data** — Document any mismatches.
- [ ] **Phase 8 checkpoint gates are mandatory** — Step 18 (Checkpoint A), Step 19 (Checkpoint B), Step 16 (Checkpoint C+), Step 17 (Checkpoint D+) are NOT optional. Every gate must be exercised and recorded.
- [ ] **cs-go first-contact protocol** — At Checkpoint A (or whenever first run), perform thorough discovery (Step 2 items 7–14) before running the standard test suite against it.
- [ ] **NEVER use `Accept: application/json` for 52N** — Returns empty collections. Use `Accept: application/geo+json` or `Accept: application/sml+json`.
- [ ] **OSH servers use `?f=` not Accept headers** — Both Server 1 and Server 3 are OpenSensorHub instances.
- [ ] **Locked decisions stay locked** — If a smoke test discovery makes you want to revisit a P8 trio decision, file a P8-F finding; surface it; do not silently re-decide.
- [ ] **Per-server cleanup tracking** — Cleanup tables track resources per server (OSH, OS4, cs-go). Delete only YOUR test resources on each.

---

## Naming Convention

```

docs/implementation/live-server-smoke-test-post-phase-8-{checkpoint}.md
 — Standard Phase 8 checkpoint smoke test (checkpoint ∈ {A, B, C, D, final})
docs/implementation/live-server-smoke-test-{server-name}.md
 — New server comparative test
docs/implementation/cross-server-interoperability-analysis.md
 — Cross-server synthesis (extend to 4-way as Phase 8 checkpoints land)
docs/implementation/live-server-retest-post-issues-{N}-{M}.md
 — Targeted retest after fixes

```

---

## Changes from Phase 7 Template

| Aspect                  | Phase 7                                         | Phase 8                                                                                                     |
| ----------------------- | ----------------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| Servers                 | 3 (OSH + 52N + OS4CSAPI-OSH)                    | **4** (+ **cs-go**)                                                                                         |
| Run cadence             | Once at end of phase                            | **Per-checkpoint** (A / B / C / D / final)                                                                  |
| Finding numbers         | P7-F1, P7-F2...                                 | **P8-F1, P8-F2...** (new series)                                                                            |
| Phase verification      | Step 16 — 7 fixes                               | **Step 16 (#166 `@link`) + Step 17 (`endpoint.csapi()`) + Steps 18/19 (per-Phase A/B gates)**               |
| `@link` fallback test   | N/A                                             | **Step 16 — dedicated cs-go interop test**                                                                  |
| `endpoint.csapi()` test | N/A                                             | **Step 17 — dedicated end-to-end + error contract**                                                         |
| Re-litigation policy    | Implicit                                        | **Explicit** — P8 trio is locked; smoke test does not relitigate                                            |
| Required reading        | 10 documents                                    | **11 documents** (+ Phase 8 trio collectively)                                                              |
| Steps                   | 20                                              | **22**                                                                                                      |
| Issue-creation template | `issue-creation-prompt-template-code-review.md` | **`issue-creation-prompt-template-phase-8.md`** (Phase 8 variant)                                           |
| Cross-server comparison | 3-way                                           | **4-way**                                                                                                   |
| Critical rules          | 20                                              | **22** (+ Phase 8 trio first, + cs-go marquee, + locked-decision policy, + per-checkpoint gate enforcement) |

---

## Server Quick Reference

| Property             | OpenSensorHub (S1)                       | 52North (S2)                            | OS4CSAPI-OSH (S3)                                | cs-go (S4) — NEW IN PHASE 8                            |
| -------------------- | ---------------------------------------- | --------------------------------------- | ------------------------------------------------ | ------------------------------------------------------ |
| URL                  | `http://45.55.99.236:8080/sensorhub/api` | `https://csa.demo.52north.org/`         | `https://os4csapi-osh.duckdns.org/sensorhub/api` | `https://129-80-248-53.sslip.io/csapi-go`              |
| Auth                 | Basic (⚠️ ask user)                      | None                                    | Basic (⚠️ ask user)                              | TBD first contact (⚠️ confirm with user)               |
| SSL                  | HTTP                                     | HTTPS expired (`-SkipCertificateCheck`) | HTTPS valid                                      | HTTPS — confirm cert behavior in Step 2                |
| Conformance          | 20+ CSAPI classes                        | Zero CSAPI classes                      | TBD (likely OSH-family)                          | TBD (third independent CSAPI implementation)           |
| Content negotiation  | `?f=` (Accept ignored)                   | Accept-routed dual-backend              | Likely `?f=`                                     | TBD                                                    |
| Default content type | `application/json`                       | `application/sml+json`                  | TBD                                              | TBD                                                    |
| Default page size    | 100                                      | TBD                                     | 100 (likely)                                     | **10** (per #167 background) — verify in Step 16d      |
| Part 1 resources     | ✅ All                                   | ✅ Subset (SFs empty)                   | TBD                                              | TBD                                                    |
| Part 2 resources     | ✅ All                                   | ❌ All broken                           | TBD                                              | TBD — and emits **`@link` object form** for cross-refs |
| Cross-ref @link form | ❌ (uses `@id` only)                     | N/A                                     | ❌ (uses `@id` only)                             | **✅ (per #166 — the reason Task C1 exists)**          |
| Write operations     | ✅ Full CRUD                             | ❓ Untested                             | TBD                                              | TBD                                                    |
| SML access           | `?f=sml3`                                | `Accept: application/sml+json`          | Likely `?f=sml3`                                 | TBD                                                    |
| Previously tested?   | ✅ ST#1–ST#24                            | ✅ ST#1–ST#24                           | ✅ ST#24                                         | ❌ First contact in Phase 8 ST#{{N}}                   |

```

```
