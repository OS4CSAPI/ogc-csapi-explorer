# Live Server Smoke Test Prompt Template — Phase 3

**Purpose:** Reusable prompt for triggering AI-driven live server smoke tests during Phase 3 (Format Handling). Adapts the Phase 2 smoke test template to validate format handler code against real server responses instead of URL generation.

**Version:** 1.0  
**Date:** February 14, 2026  
**Supersedes:** Nothing — sibling to `smoke-test-prompt-template.md` (Phase 2), which remains valid for any Phase 2 URL builder revisits.  
**Report destination:** `docs/implementation/live-server-smoke-test-post-phase-{X.Y}.md`

---

## Why a Separate Template?

Phase 3 smoke tests differ fundamentally from Phase 2:

| Dimension         | Phase 2 (URL Builder)              | Phase 3 (Format Handlers)                              |
| ----------------- | ---------------------------------- | ------------------------------------------------------ |
| What we test      | URLs we generate → server accepts? | Server responses → our parser produces correct output? |
| Direction of data | Outbound (our code → server)       | Inbound (server → our code)                            |
| Core question     | "Is the URL right?"                | "Does the parser handle real data?"                    |
| Key risk          | URL malformation                   | Vocabulary gaps, format surprises, missing fields      |
| Test method       | HTTP GET, check status code        | HTTP GET, pipe response through handler functions      |
| Write operations  | None (read-only URLs)              | None (read-only parsing)                               |

The Phase 2 template's core steps (3–5: discovery, URL generation, query parameters) are irrelevant for Phase 3. Step 6 (data shape observation) needs to become active validation, not passive observation.

---

## When to Use

Trigger this prompt after any of these Phase 3 milestones:

1. **A format handler is completed** (e.g., Issue #14 GeoJSON Handler Extensions)
2. **A parser component is completed** (e.g., SWE Common parser, SensorML parser)
3. **A validator extension is completed**
4. **Before starting Phase 4** (gate validation for all of Phase 3)
5. **After a fix to any Phase 3 component** that changes parsing or validation behavior

Do NOT trigger after test-only changes, doc-only changes, or barrel file/export-only changes.

---

## How to Use

Copy the prompt below and paste it into the conversation after completing coding work. Replace all `{{...}}` placeholders with actual values.

---

## Prompt

````
Please perform a live server smoke test of the Phase 3 format handler work completed since the last smoke test.

### Scope

**Phase:** {{Phase number, e.g., "3.1"}}
**Issues completed since last smoke test:** {{List issue numbers and titles}}
**Components to test:** {{e.g., "GeoJSON handler (6 public functions)" or "SensorML Simple Process parser"}}
**Last smoke test:** {{Reference the previous smoke test doc}}

### Server Information

We test against TWO servers. Both must be tested in every smoke test.

#### Server 1: OpenSensorHub (OSH)

- **URL:** `http://45.55.99.236:8080/sensorhub/api`
- **Auth:** Basic authentication required
- **⚠️ CREDENTIAL REMINDER:** The username and password are NOT stored in this repository. If you do not have the credentials from a prior conversation context, you MUST ask the user for them before proceeding. Do not guess, do not skip this server.
- **PowerShell pattern:**
  ```powershell
  $cred = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("{{username}}:{{password}}"))
  $headers = @{ Authorization = "Basic $cred" }
  Invoke-RestMethod -Uri "http://45.55.99.236:8080/sensorhub/api" -Headers $headers
````

- **Known response characteristics:**
  - Envelope: `{ items: [...], links: [...] }` (non-standard — NOT GeoJSON FeatureCollection)
  - featureType values: SOSA vocabulary (`sosa:Sensor`, `sosa:Platform`, etc.)
  - validTime format: array `["ISO-8601", "now"]` (spec-canonical timePeriod)
  - Has real data: systems, datastreams, observations, sampling features, control streams, commands
  - Some resource types may have zero entries (deployments, procedures, properties)
  - Uses `uid` field consistently across all feature types

#### Server 2: 52North

- **URL:** `https://csa.demo.52north.org/`
- **Auth:** None required
- **SSL:** Certificate is expired — all PowerShell commands MUST use `-SkipCertificateCheck`
- **PowerShell pattern:**
  ```powershell
  Invoke-RestMethod -Uri "https://csa.demo.52north.org/" -SkipCertificateCheck
  ```
- **⚠️ CONTENT NEGOTIATION WARNING (L13):** 52North runs a **dual-backend architecture**. The `Accept` header determines which data provider handles the request:
  - `Accept: application/sml+json` (or no `Accept` header — server default) → SensorML data store → **has data** (3 systems, 1 deployment, 1 procedure). Envelope: `{ items: [...], links: [...] }`
  - `Accept: application/json` → pygeoapi GeoJSON provider → **empty**. Envelope: `{ type: "FeatureCollection", features: [] }`
  - These are **different backends with different data and different response shapes** on the same server
  - If a request returns empty collections, verify you are using the correct `Accept` header before concluding data is absent
  - See `docs/implementation/f57-content-negotiation-correction.md` for the full investigation
- **Known response characteristics:**
  - Default content type: `application/sml+json` (SensorML format)
  - SML envelope: `{ items: [...], links: [...] }` (non-standard — same shape as OSH)
  - GeoJSON envelope: `{ type: "FeatureCollection", features: [...] }` (standard GeoJSON — but currently empty)
  - featureType values: May use different vocabularies than OSH
  - Some endpoints may return 500 or 404 (server bugs, not our code)

### Test Instructions

Follow this exact sequence. Do NOT modify any code during the smoke test (Lesson 10 — smoke tests are read-only observation).

#### Step 1: Document Prior Findings

Read the previous smoke test report and list ALL prior findings with their current status. For each:

- If it was marked "Fixed" — re-verify it's still fixed
- If it was marked "Deferred" — confirm it's still deferred, note if anything changed
- If it was marked "Server limitation" — confirm it's still present
- If it was marked "Addressed by Phase 3" — verify the Phase 3 code actually addresses it

#### Step 2: Test Server Connectivity

For EACH server:

1. Fetch the root API document — confirm both servers are reachable
2. Fetch one resource collection endpoint (e.g., `/systems`) to confirm data is available
3. Record which resource types have data (non-empty collections) on each server

This step ensures we have test data before proceeding to handler validation.

#### Step 3: GeoJSON Handler Validation

For EACH server, for EACH resource type with data (Systems, Deployments, Procedures, SamplingFeatures):

**3a. Fetch the collection** — GET the resource collection. **Record the exact `Accept` header used** (or note if none was set). The `Accept` header determines the response format and potentially which data backend responds (see 52North content negotiation warning above). If testing GeoJSON handling, use `Accept: application/geo+json`. If testing SensorML handling, use `Accept: application/sml+json`. If a collection returns empty, re-test with the server's default content type (no `Accept` header) before filing a finding. Save the raw JSON response.

**3b. Test recognition on each feature:**

For each feature in the response:

```
isCSAPIFeature(feature)          → expected: true
getCSAPIResourceType(feature)    → expected: matches the resource type endpoint
```

Record results in a table:

| Server | Resource Type | Feature ID | featureType Value | isCSAPIFeature | getCSAPIResourceType | Match? |
| ------ | ------------- | ---------- | ----------------- | -------------- | -------------------- | ------ |

**3c. ~~Test validation on each feature~~ — REMOVED**

> **Note (2026-02-15):** Step 3c previously called `validateCSAPIFeature()`. That function and all 13 per-type validators were removed in Issue #52 (Phase 3.3) after F49 revealed that validation-gated extraction blocked 100% of OSH SamplingFeatures. The design decision (documented in `docs/implementation/design-notes-validation-extraction-decoupling.md`) concluded that feature-level validators don't align with upstream ogc-client architecture — no other handler (WMS, WFS, WMTS, TMS, STAC) has separate `validate*()` functions. Extraction now gates on recognition only (Postel's Law). This step is retained as a placeholder to preserve step numbering.

**3d. Test extraction on each feature:**

```
extractCSAPIFeature(feature)     → expected: typed object with all properties populated
```

For each extracted resource, verify:

- `id` is populated
- `properties.featureType` matches the raw feature
- `properties.uid` is a valid URI
- `properties.name` is populated
- `properties.validTime` (if present) is a proper `TimeInterval` with `start: Date`
- `geometry` is correct (null for Procedures, present/absent as expected for others)
- `links` array preserved

| Server | Resource Type | Feature ID | Extraction | id  | uid | name | validTime | geometry | links |
| ------ | ------------- | ---------- | ---------- | --- | --- | ---- | --------- | -------- | ----- |

**3e. Test parseValidTime specifically:**

For features with `validTime` data, extract the raw `validTime` value and test:

```
parseValidTime(rawValidTime)     → expected: { start: Date, end: Date|undefined }
```

| Server | Feature ID | Raw validTime | Parsed start | Parsed end | Correct? |
| ------ | ---------- | ------------- | ------------ | ---------- | -------- |

#### Step 4: Response Envelope Observations

For each server, document the response envelope structure for each tested endpoint:

| Server | Endpoint | Envelope Type | Feature Array Key | Pagination | Links |
| ------ | -------- | ------------- | ----------------- | ---------- | ----- |

Note any new envelope patterns not seen in prior smoke tests. These observations inform the response parser (later Phase 3 task).

#### Step 5: Vocabulary Inventory

Compile a complete inventory of `featureType` values observed across both servers:

| featureType Value | Server(s) | Resource Type Endpoint | SOSA? | Recognized? | Handler Classification |
| ----------------- | --------- | ---------------------- | ----- | ----------- | ---------------------- |

This table is critical for identifying vocabulary gaps (findings like F10 from Phase 2.8).

#### Step 6: Content-Type Availability (for later Phase 3 components)

For each server, probe which content types are available for future parser work:

| Content-Type           | Endpoint Tested                   | OSH Available? | 52North Available? |
| ---------------------- | --------------------------------- | -------------- | ------------------ |
| `application/geo+json` | /systems                          |                |                    |
| `application/sml+json` | /systems?f=application/sml%2Bjson |                |                    |
| `application/swe+json` | /datastreams/{id}/schema          |                |                    |
| `application/json`     | /systems                          |                |                    |

This informs whether SensorML and SWE Common parsers can be smoke-tested when they're built.

#### Step 7: Cross-Server Comparison

| Dimension | OpenSensorHub | 52North | Match? |
| --------- | ------------- | ------- | ------ |

Include handler-specific dimensions:

- featureType vocabulary
- validTime format
- Presence of uid, name, description fields
- Geometry patterns (null for Procedures?)
- Link structures
- Response envelope type

#### Step 8: Classify New Findings

For each new finding, classify with:

- **Severity:** Critical / Moderate / Low / Informational
- **Category:** Handler bug / Vocabulary gap / Server limitation / Interoperability concern / Spec ambiguity
- **Affects:** Which function in which file
- **Ownership:** "Ours" (handler needs a fix) / "Upstream" (server-side) / "Shared" (both)
- **Status:** Needs fix / Needs design decision / Informational / Deferred to later Phase 3 task

#### Step 9: Generate Impact Assessment

For any findings classified as "Ours" or "Shared":

1. Identify the specific file and function affected
2. Assess whether the fix requires changing validation rules, vocabulary sets, or parsing logic
3. Estimate fix complexity
4. Determine if the fix should block the next Phase 3 task or can be deferred

### Report Format

Generate the report as a markdown file and save it to:
`docs/implementation/live-server-smoke-test-post-phase-{{X.Y}}.md`

Use this exact structure:

```markdown
# Live Server Smoke Test — Post Phase {{X.Y}}

**Date:** {{YYYY-MM-DD}}
**Milestone:** After completing Phase {{X.Y}} (Issues {{list}})
**Servers:** OpenSensorHub demo instance, 52North demo instance
**Auth:** OSH: Basic auth required (credentials not stored in repo); 52North: None (expired SSL cert)
**Purpose:** {{One-sentence purpose statement}}
**Components tested:** {{List handler/parser modules tested}}

> This is smoke test #{{N}} in the series. See also:
>
> - [Previous smoke test](link)

## Test Methodology

{{Brief description — no code changes, fetch real responses, pipe through handler functions, read-only observation}}

## Server Profiles

### OpenSensorHub

Collections with data: {{list with counts}}
Resource inventory: {{table}}

### 52North

Collections with data: {{list with counts}}
Resource inventory: {{table}}

## Results

### Prior Findings — Regression Check

| Finding | Prior Status | Current Status | Evidence |
| ------- | ------------ | -------------- | -------- |
| ...     | ...          | ...            | ...      |

### GeoJSON Handler — Recognition

| Server | Resource Type | Features Tested | All Recognized? | Failures |
| ------ | ------------- | --------------- | --------------- | -------- |
| ...    | ...           | ...             | ✅/❌           | ...      |

### ~~GeoJSON Handler — Validation~~ — N/A

> Removed in Issue #52 (Phase 3.3). See Step 3c note above. `validateCSAPIFeature` no longer exists.

### GeoJSON Handler — Extraction

| Server | Resource Type | Features Tested | All Extracted? | Issues |
| ------ | ------------- | --------------- | -------------- | ------ |
| ...    | ...           | ...             | ✅/❌          | ...    |

### parseValidTime — Live Data

| Server | Features With validTime | All Parsed? | Format Observed | Issues |
| ------ | ----------------------- | ----------- | --------------- | ------ |
| ...    | ...                     | ✅/❌       | ...             | ...    |

### Vocabulary Inventory

| featureType Value | Server(s) | Recognized? | Classification |
| ----------------- | --------- | ----------- | -------------- |
| ...               | ...       | ✅/❌       | ...            |

### Content-Type Availability

| Content-Type | OSH   | 52North |
| ------------ | ----- | ------- |
| ...          | ✅/❌ | ✅/❌   |

## New Findings

### F{{N}} ({{Severity}}): {{Title}}

**Severity:** {{Critical/Moderate/Low/Informational}}
**Category:** {{Handler bug / Vocabulary gap / Server limitation / Interoperability concern}}
**Affects:** {{function/file}}
**Ownership:** {{Ours / Upstream / Shared}}
**Evidence:** {{What was observed, raw data if helpful}}
**Status:** {{Needs fix / Deferred / Informational}}

## Cross-Server Comparison

| Dimension | OpenSensorHub | 52North | Match? |
| --------- | ------------- | ------- | ------ |
| ...       | ...           | ...     | ✅/❌  |

## Response Envelope Observations (Phase 3 Reference)

{{Document response shapes for future parser work}}

## What WORKS (Verified Against Live Data)

| Capability | OSH | 52North |
| ---------- | --- | ------- |
| ...        | ✅  | ✅      |

## What Remains (Later Phase 3 Concerns)

| Issue | Severity | Component | Target Task |
| ----- | -------- | --------- | ----------- |
| ...   | ...      | ...       | ...         |

## Verdict

{{2-3 paragraph assessment: handler correctness against real data, vocabulary gaps found, readiness to proceed to next Phase 3 component}}
```

Then commit the report, push, and confirm the file is at the expected path.

**STOP.** Do NOT create GitHub issues automatically. Instead, present
all new findings to the user in a structured summary (see Step 10 below)
and wait for discussion before taking any further action.

```

---

## Post-Smoke-Test Workflow

After the smoke test report is committed and pushed:

### Step 10: Present Findings to User

**This step is mandatory and must happen before any issue creation.**

Present ALL new findings in a structured summary with recommendations:

```

### New Findings Summary

| #      | Finding   | Severity | Category | Ownership | Recommendation                                                     |
| ------ | --------- | -------- | -------- | --------- | ------------------------------------------------------------------ |
| F{{N}} | {{Title}} | {{Sev}}  | {{Cat}}  | {{Own}}   | {{Your recommendation: create issue / defer / informational only}} |

For each finding where you recommend creating an issue:

- State what the issue would contain (1-2 sentences)
- State which existing ROADMAP task or Phase 3 issue it relates to
- State whether it blocks the next task or can be addressed later

```

Then **STOP and wait for the user to respond**. The user will:
- Approve, modify, or reject each recommendation
- Decide which findings warrant GitHub issues
- Provide additional context or priorities
- Potentially ask follow-up questions about specific findings

### Step 11: Create Issues (Only After User Approval)

**Only after the user explicitly approves issue creation:**

1. Use `docs/governance/issue-creation-prompt-template.md` to draft each approved issue
2. Present the draft issue body to the user for review before creating
3. Create the issue on GitHub only after user confirms the content
4. If the user wants changes, revise and re-present before creating

### Step 12: Post-Issue Workflow

1. **Complete fix issues** before proceeding to the next Phase 3 task
2. **The next smoke test will re-verify** all prior findings — nothing is forgotten
3. **Update vocabulary inventory** if new featureType values were discovered

---

## Critical Rules (Non-Negotiable)

These rules carry forward from Phase 2 (Lessons 8 and 10) with Phase 3 additions:

- [ ] **Read-only observation** — Do NOT modify any code during the smoke test. If you find a handler bug, document it and create an issue after the report is complete.
- [ ] **Both servers tested** — Every smoke test MUST hit both OpenSensorHub AND 52North. Single-server testing missed real interoperability issues in Phase 2.
- [ ] **OSH credentials not in repo** — The OpenSensorHub username and password are NEVER committed to the repository, NEVER written into any file, and NEVER included in the report. If you don't have them, ask the user.
- [ ] **52North needs `-SkipCertificateCheck`** — Every PowerShell command to the 52North server MUST include this flag.
- [ ] **Accept headers documented (L13)** — Every HTTP request in the smoke test MUST record which `Accept` header was used. If no `Accept` header is set, record "none (server default)". The `Accept` header MUST NOT change silently between smoke tests — any change must be deliberate and documented. Before attributing empty responses to "data loss" or "server reset", re-test with at least: (1) no `Accept` header, (2) `Accept: application/json`, and (3) `Accept: application/sml+json`. See `docs/implementation/f57-content-negotiation-correction.md`.
- [ ] **All prior findings re-checked** — The regression check section must cover EVERY finding from EVERY prior smoke test.
- [ ] **New findings get ownership classification** — Every new finding must be classified as "Ours", "Upstream", or "Shared".
- [ ] **Raw data preserved** — When a handler function produces unexpected output, include the raw server JSON (or a representative sample) in the finding so the fix author has the actual input that caused the problem.
- [ ] **Vocabulary inventory updated** — Every smoke test must compile a complete featureType inventory. This is cumulative — new values add to the record, nothing is removed.
- [ ] **No automatic issue creation** — NEVER create GitHub issues during or immediately after the smoke test. Always present findings with recommendations first and wait for explicit user approval before creating any issues. Issues must follow `docs/governance/issue-creation-prompt-template.md` and the user must review the draft before it is posted to GitHub.

---

## Phase 3 Component Test Matrix

As Phase 3 progresses, more components become testable. Use this matrix to determine which steps to run:

| Component | Template Step | Testable When | Content-Type Needed |
|-----------|--------------|---------------|---------------------|
| GeoJSON handler | Step 3 | Now (Issue #14 complete) | `application/geo+json` or `application/json` |
| Format detector | Step 3 (adapted) | After Issue #15 | Any — tests content-type detection |
| ~~Validator extensions~~ | ~~Step 3c~~ | N/A — removed in Issue #52 | — |
| SWE Common types | N/A (types only) | — | — |
| SensorML types | N/A (types only) | — | — |
| SensorML parsers | New Step 10 | After Issues #19–#22 | `application/sml+json` |
| SWE Common parsers | New Step 11 | After Issues #24–#27 | `application/swe+json` |

When a new parser component is ready, add a new step section to the smoke test following the same pattern as Step 3 (fetch → parse → validate output → compare to raw data).

---

## Naming Convention

Reports follow the same naming pattern as Phase 2:

```

docs/implementation/live-server-smoke-test-post-phase-{X.Y}.md

```

The Phase 3 smoke tests continue the numbering sequence from Phase 2. They appear in the same directory and the same series.

---

## Reference Documents

| Document | Location | Purpose |
|----------|----------|---------|
| Phase 2 Smoke Test Template | `docs/governance/smoke-test-prompt-template.md` | Phase 2 sibling (URL builder validation) |
| Lessons Learned | `docs/governance/phase-2-lessons-learned.md` | Lesson 8 (multi-server), Lesson 10 (read-only) |
| Previous Smoke Test | `docs/implementation/live-server-smoke-test-post-phase-{prev}.md` | Prior findings to re-check |
| Phase 3 Smoke Test Rationale | `docs/implementation/phase-3-smoke-test-rationale.md` | Why Phase 3 smoke tests matter more |
| Cross-Server Analysis | `docs/implementation/cross-server-interoperability-analysis.md` | Known server differences |
| GeoJSON Handler | `src/ogc-api/csapi/formats/geojson.ts` | Functions under test |
| AI Operational Constraints | `docs/governance/AI_OPERATIONAL_CONSTRAINTS.md` | Behavioral boundaries |

---

## Server Quick Reference

| Property | OpenSensorHub | 52North |
|----------|--------------|---------|
| URL | `http://45.55.99.236:8080/sensorhub/api` | `https://csa.demo.52north.org/` |
| Auth | Basic (⚠️ ask user for credentials) | None |
| SSL | HTTP (no SSL issues) | HTTPS (expired cert — use `-SkipCertificateCheck`) |
| Content negotiation | Single backend | ⚠️ **Dual backend** — `Accept` header routes to different providers (L13) |
| Default content type | `application/json` | `application/sml+json` |
| SML envelope (`application/sml+json`) | `{ items: [...] }` | `{ items: [...] }` — **has data** |
| GeoJSON envelope (`application/json`) | `{ items: [...] }` | `{ type: "FeatureCollection", features: [...] }` — **empty** |
| featureType vocabulary | SOSA (`sosa:Sensor`, etc.) | May differ |
| validTime format | Array `["ISO", "now"]` | Unknown until tested |
| Data availability | Rich (systems, datastreams, etc.) | Rich via SML; empty via GeoJSON |
```
