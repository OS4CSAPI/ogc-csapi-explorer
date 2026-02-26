# Live Server Smoke Test Prompt Template

**Purpose:** Reusable prompt for triggering AI-driven live server smoke tests after coding progress. Produces a standardized report placed in `docs/implementation/` following the format established by the Phase 2.1 through 2.3 smoke tests, the 52North comparative test, and the cross-server interoperability analysis.

**Version:** 1.0  
**Date:** February 14, 2026  
**Report destination:** `docs/implementation/live-server-smoke-test-post-phase-{X.Y}.md`

---

## When to Use

Trigger this prompt after any of these milestones:

1. **A new resource type is implemented** (e.g., Issue #9 Properties methods)
2. **A fix to discovery, link scanning, or URL construction** is completed (e.g., Issue #39 Convention 3 fixes)
3. **Before starting a new phase** (gate validation)
4. **After multiple related issues** are completed in a single session

Do NOT trigger after test-only changes, doc-only changes, or code review cleanups that don't affect URL generation or server interaction.

---

## How to Use

Copy the prompt below and paste it into the conversation after completing coding work. Replace all `{{...}}` placeholders with actual values.

---

## Prompt

````
Please perform a live server smoke test of the work completed since the last smoke test.

### Scope

**Phase:** {{Phase number, e.g., "2.5"}}
**Issues completed since last smoke test:** {{List issue numbers and titles}}
**Methods to focus on:** {{e.g., "8 new SamplingFeatures methods" or "all 36 methods"}}
**Last smoke test:** {{Reference the previous smoke test doc, e.g., "docs/implementation/live-server-smoke-test-post-phase-2.3.md"}}

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

- **Known characteristics:**
  - Advertises 20+ CSAPI conformance classes (Parts 1, 2, 3)
  - Uses Convention 2 (plain `rel` names) at root level for resource links
  - Uses Convention 3 (`rel: "items"`) at collection level
  - Response envelope: `{ items: [...], links: [...] }` (non-standard)
  - Has real data: systems, datastreams, observations, sampling features, control streams
  - Some resource types may have zero entries (deployments, procedures, properties)

#### Server 2: 52North

- **URL:** `https://csa.demo.52north.org/`
- **Auth:** None required
- **SSL:** Certificate is expired — all PowerShell commands MUST use `-SkipCertificateCheck`
- **PowerShell pattern:**
  ```powershell
  Invoke-RestMethod -Uri "https://csa.demo.52north.org/" -SkipCertificateCheck
  ```
- **Known characteristics:**
  - Advertises ZERO CSAPI conformance classes (only OGC API Common core)
  - No root-level resource links — discovery relies entirely on Convention 3
  - Response envelope: `{ type: "FeatureCollection", features: [...] }` (standard GeoJSON)
  - Uses `featuresOfInterest` in collection hrefs (our code normalizes to `samplingFeatures`)
  - Collection links include `?f=application/json` query parameters (our code strips these)
  - All collections may be empty — URL acceptance can be confirmed, but data filtering cannot
  - Some endpoints may return 500 or 404 (server bugs, not our code)

### Test Instructions

Follow this exact sequence. Do NOT modify any code during the smoke test (Lesson 10 — smoke tests are read-only observation).

#### Step 1: Document Prior Findings

Read the previous smoke test report and list ALL prior findings with their current status. For each:

- If it was marked "Fixed" — re-verify it's still fixed
- If it was marked "Deferred" — confirm it's still deferred, note if anything changed
- If it was marked "Server limitation" — confirm it's still present

#### Step 2: Test Server Connectivity and Profiles

For EACH server:

1. Fetch the root API document
2. Fetch `/conformance` — record conformance classes
3. Fetch `/collections` — record all collections and their links
4. Document root document links (resource type → URL mappings)
5. Record the server resource inventory (which endpoints return 200, which fail)

#### Step 3: Test Resource Discovery

Simulate our `scanCsapiLinks()` behavior against BOTH servers:

1. **Convention 1** (ogc-cs: prefix): Check if any links use the `ogc-cs:` prefix
2. **Convention 2** (plain rel name): Check root document links for plain resource type names (`rel: "systems"`, `rel: "deployments"`, etc.)
3. **Convention 3** (rel: "items" + href): For each collection, extract `rel: "items"` links, verify segment extraction works with:
   - Query parameters in hrefs (must be stripped)
   - `featuresOfInterest` naming (must be normalized to `samplingFeatures`)
   - Mixed leading-slash conventions

Record how many resource types are discovered per convention per server.

#### Step 4: Test URL Generation — All Implemented Methods

For EACH server, test every implemented builder method. Use real resource IDs where available (from list endpoint responses). Record:

| Method | Generated URL | Server | HTTP Status | Notes |
| ------ | ------------- | ------ | ----------- | ----- |

For methods that require a resource ID but the server has zero entries for that type, mark as **N/A (no data)** — the URL pattern is still validated by confirming the list endpoint works.

For CRUD methods (create, update, delete), do NOT execute write operations. Only verify the URL is correctly formed (correct path, correct HTTP method target).

#### Step 5: Test Query Parameter Acceptance

Test each of these parameters against both servers (using a resource type with data if possible, otherwise test URL acceptance with empty results):

| Parameter           | Method Used | URL | OSH Result | 52North Result |
| ------------------- | ----------- | --- | ---------- | -------------- |
| limit               |             |     |            |                |
| offset              |             |     |            |                |
| q                   |             |     |            |                |
| bbox                |             |     |            |                |
| datetime (single)   |             |     |            |                |
| datetime (interval) |             |     |            |                |
| id (single)         |             |     |            |                |
| id (array)          |             |     |            |                |
| recursive           |             |     |            |                |
| f (format)          |             |     |            |                |
| cursor              |             |     |            |                |
| parent              |             |     |            |                |

#### Step 6: Record Data Shape Observations

For any responses that return actual data, note the response shape. These observations are Phase 3 reference material:

- Envelope type (`items` vs `features` vs `FeatureCollection`)
- Field names and types (especially `validTime`, temporal fields, geometry)
- Pagination metadata (numbered vs link-based)
- Any new response shapes not seen in prior smoke tests

#### Step 7: Cross-Server Comparison

If testing both servers (which should be every time), produce a comparison table:

| Dimension | OpenSensorHub | 52North | Match? |
| --------- | ------------- | ------- | ------ |

#### Step 8: Classify New Findings

For each new finding, classify with:

- **Severity:** Critical / Moderate / Low / Informational
- **Category:** Code bug / Server limitation / Interoperability concern / Naming variation
- **Affects:** Which function or code path
- **Ownership:** "Ours" (our code needs a fix) / "Upstream" (server-side) / "Shared" (both)
- **Status:** Needs fix / Needs design decision / Informational / Deferred to Phase N

#### Step 9: Generate Impact Assessment

For any findings classified as "Ours" or "Shared":

1. Identify the specific file and function affected
2. Assess upstream impact (does the fix touch any upstream file?)
3. Estimate fix complexity (one-line, small, medium, architectural)

### Report Format

Generate the report as a markdown file and save it to:
`docs/implementation/live-server-smoke-test-post-phase-{{X.Y}}.md`

If this is a comparative test of a new server implementation, use:
`docs/implementation/live-server-smoke-test-{{server-name}}.md`

If cross-server analysis warrants its own document, also generate:
`docs/implementation/cross-server-interoperability-analysis.md` (update existing or create new)

Use this exact structure (matching prior smoke tests):

```markdown
# Live Server Smoke Test — Post Phase {{X.Y}}

**Date:** {{YYYY-MM-DD}}
**Milestone:** After completing Phase {{X.Y}} (Issues {{list}})
**Servers:** OpenSensorHub demo instance, 52North demo instance
**Auth:** OSH: Basic auth required (credentials not stored in repo); 52North: None (expired SSL cert)
**Purpose:** {{One-sentence purpose statement}}

> This is smoke test #{{N}} in the series. See also:
>
> - [Previous smoke test](link)

## Test Methodology

{{Brief description — no code changes, raw HTTP calls, read-only observation}}

## Server Profiles

### OpenSensorHub

| Spec Part | Conformance Classes |
| --------- | ------------------- |
| ...       | ...                 |

Collections: {{list}}
Top-level resource links: {{table}}
Server resource inventory: {{table with counts}}

### 52North

{{Same structure}}

## Results

### Prior Findings — Regression Check

| Finding | Status                                    | Evidence |
| ------- | ----------------------------------------- | -------- |
| ...     | Still Fixed ✅ / Still Deferred / Changed | ...      |

### URL Generation — All {{N}} Methods

#### {{Resource Type}} Methods ({{N}} methods) {{— NEW if applicable}}

| Method Call | URL Pattern | OSH       | 52North   |
| ----------- | ----------- | --------- | --------- |
| ...         | ...         | ✅/❌/N/A | ✅/❌/N/A |

### Query Parameter Acceptance

| Parameter | Method | URL | OSH   | 52North |
| --------- | ------ | --- | ----- | ------- |
| ...       | ...    | ... | ✅/❌ | ✅/❌   |

## New Findings

### F{{N}} ({{Severity}}): {{Title}}

**Severity:** {{Critical/Moderate/Low/Informational}}
**Category:** {{Code bug / Server limitation / Interoperability concern}}
**Affects:** {{function/file}}
**Ownership:** {{Ours / Upstream / Shared}}
**Evidence:** {{What was observed}}
**Status:** {{Needs fix / Deferred / Informational}}

## Data Shape Observations (Phase 3 Reference)

{{Numbered list of response shape observations}}

## Cross-Server Comparison

| Dimension | OpenSensorHub | 52North | Match? |
| --------- | ------------- | ------- | ------ |
| ...       | ...           | ...     | ✅/❌  |

## What WORKS (Verified)

| Capability | Status |
| ---------- | ------ |
| ...        | ✅     |

## What Remains (Phase 3 Concerns)

| Issue | Severity | Component | Target Phase |
| ----- | -------- | --------- | ------------ |
| ...   | ...      | ...       | ...          |

## Comparison: Phase {{prev}} → Phase {{current}}

| Dimension           | Phase {{prev}} | Phase {{current}} |
| ------------------- | -------------- | ----------------- |
| Methods implemented | {{N}}          | {{N}}             |
| ...                 | ...            | ...               |

## Verdict

{{2-3 paragraph assessment: regressions?, new findings?, readiness to proceed?}}
```

Then commit the report, push, and confirm the file is at the expected path.

If any new findings are classified as "Ours — Needs fix", create a GitHub
issue for each using `docs/governance/issue-creation-prompt-template.md`.

```

---

## Post-Smoke-Test Workflow

After the smoke test report is generated:

1. **Review new findings** — decide which are "fix now" vs "defer"
2. **Create GitHub issues** for "Ours — Needs fix" findings using `docs/governance/issue-creation-prompt-template.md`
3. **Complete fix issues** before proceeding to the next resource type
4. **The next smoke test will re-verify** all prior findings — nothing is forgotten
5. **Update the cross-server interoperability analysis** if both servers were tested and new interoperability findings emerged

---

## Critical Rules (Non-Negotiable)

These rules come from Lesson 8 and Lesson 10 in `docs/governance/phase-2-lessons-learned.md`:

- [ ] **Read-only observation** — Do NOT modify any code during the smoke test. If you find a bug, document it and create an issue after the report is complete.
- [ ] **Both servers tested** — Every smoke test MUST hit both OpenSensorHub AND 52North. Single-server testing missed real bugs (F1/F2 in the 52North test) across three prior smoke tests.
- [ ] **OSH credentials not in repo** — The OpenSensorHub username and password are NEVER committed to the repository, NEVER written into any file, and NEVER included in the report. If you don't have them, ask the user.
- [ ] **52North needs `-SkipCertificateCheck`** — Every PowerShell command to the 52North server MUST include this flag due to the expired SSL certificate.
- [ ] **All prior findings re-checked** — The regression check section must cover EVERY finding from EVERY prior smoke test, not just the most recent one.
- [ ] **New findings get ownership classification** — Every new finding must be classified as "Ours", "Upstream", or "Shared" with evidence.

---

## Naming Convention

Reports follow these naming patterns:

```

docs/implementation/live-server-smoke-test-post-phase-{X.Y}.md — Standard post-phase smoke test
docs/implementation/live-server-smoke-test-{server-name}.md — New server comparative test
docs/implementation/cross-server-interoperability-analysis.md — Cross-server synthesis
docs/implementation/live-server-retest-post-issues-{N}-{M}.md — Targeted retest after fixes

```

Examples from our history:
- `live-server-smoke-test-post-phase-2.1.md` (first test — found F1/F2 critical findings)
- `live-server-smoke-test-post-phase-2.2.md` (validated F1/F2 fixes)
- `live-server-smoke-test-post-phase-2.3.md` (validated Procedures, expanded query param coverage)
- `live-server-smoke-test-52north.md` (second server — found Convention 3 bugs)
- `cross-server-interoperability-analysis.md` (synthesis of both server tests)
- `live-server-retest-post-issues-34-35.md` (targeted retest after specific fixes)

---

## Reference Documents

When performing a smoke test, the tester should have access to:

| Document | Location | Purpose |
|----------|----------|---------|
| Lessons Learned | `docs/governance/phase-2-lessons-learned.md` | Lesson 8 (multi-server testing), Lesson 10 (read-only) |
| Previous Smoke Test | `docs/implementation/live-server-smoke-test-post-phase-{prev}.md` | Prior findings to re-check |
| Cross-Server Analysis | `docs/implementation/cross-server-interoperability-analysis.md` | Known server differences |
| Implementation Guide | `docs/planning/csapi-implementation-guide.md` | Spec-correct URL patterns |
| AI Operational Constraints | `docs/governance/AI_OPERATIONAL_CONSTRAINTS.md` | Behavioral boundaries |

---

## Server Quick Reference

| Property | OpenSensorHub | 52North |
|----------|--------------|---------|
| URL | `http://45.55.99.236:8080/sensorhub/api` | `https://csa.demo.52north.org/` |
| Auth | Basic (⚠️ ask user for credentials) | None |
| SSL | HTTP (no SSL issues) | HTTPS (expired cert — use `-SkipCertificateCheck`) |
| Conformance | 20+ CSAPI classes | Zero CSAPI classes |
| Discovery | Convention 2 (root) + Convention 3 (collections) | Convention 3 only (collections) |
| Response envelope | `{ items: [...] }` | `{ type: "FeatureCollection", features: [...] }` |
| Data availability | Rich (systems, datastreams, observations, etc.) | Mostly empty |
| Resource naming | `samplingFeatures` | `featuresOfInterest` (in collection hrefs) |
```
