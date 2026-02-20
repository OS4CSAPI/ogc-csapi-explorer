# Phase 4 — Live Server Smoke Test Prompt Template

**Purpose:** Exhaustive end-to-end smoke test prompt for Phase 4 development. Covers full CRUD operations, Part 2 resource workflows, schema validation, SensorML content negotiation, cross-server comparison, and regression verification of all prior findings. Produces a standardized report in `docs/implementation/`.

**Version:** 1.0
**Date:** February 18, 2026
**Supersedes:** `docs/governance/smoke-test-prompt-template.md` (Phase 3)
**Report destination:** `docs/implementation/live-server-smoke-test-post-phase-{X.Y}.md`

---

## When to Use

Trigger this prompt after any of these milestones:

1. **A new resource type's CRUD operations are implemented** (create/update/delete methods)
2. **A fix to discovery, link scanning, URL construction, or serialization** is completed
3. **Before starting a new phase** (gate validation)
4. **After multiple related issues** are completed in a single session
5. **After changes to content negotiation, parsing, or SensorML handling**

Do NOT trigger after test-only changes, doc-only changes, or code review cleanups that don't affect URL generation, serialization, or server interaction.

---

## How to Use

Copy the **Prompt** section below and paste it into the conversation after completing coding work. Replace all `{{...}}` placeholders with actual values.

---

## Prompt

```
Please perform a Phase 4 live server smoke test of the work completed since the last smoke test.

### Scope

**Phase:** {{Phase number, e.g., "4.1"}}
**Issues completed since last smoke test:** {{List issue numbers and titles}}
**Methods to focus on:** {{e.g., "8 new SamplingFeatures CRUD methods" or "all 85+ methods"}}
**Last smoke test:** {{Reference the previous smoke test doc, e.g., "docs/implementation/live-server-smoke-test-post-phase-3.16.md"}}

### Required Reading — BEFORE Starting

Read these documents IN FULL before issuing any HTTP requests:

| Document | Location | Purpose |
|----------|----------|---------|
| Known Server Quirks | `docs/governance/known-server-quirks.md` | **CRITICAL** — All known server behaviors, bugs, content-negotiation rules. Prevents re-discovering known issues |
| Previous Smoke Test | `docs/implementation/live-server-smoke-test-post-phase-{prev}.md` | Prior findings to re-check |
| Cross-Server Analysis | `docs/implementation/cross-server-interoperability-analysis.md` | Known server differences |
| Implementation Guide | `docs/planning/csapi-implementation-guide.md` | Spec-correct URL patterns |
| AI Operational Constraints | `docs/governance/AI_OPERATIONAL_CONSTRAINTS.md` | Behavioral boundaries |
| Fixtures Guide | `docs/testing/fixtures-guide.md` | Fixture structure for reference |

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
  ```
- **Key quirks (read `known-server-quirks.md` for full details):**
  - **Ignores Accept headers entirely** — use `?f=json`, `?f=geojson`, `?f=sml3` for content negotiation
  - Full CRUD works (POST → 201 empty body + Location header; PUT requires `uid` in body)
  - All Part 2 endpoints work (datastreams, observations, controlstreams, commands)
  - Sub-resource relationship endpoints return 400 (except subsystems/subdeployments)
  - Use lowercase `/controlstreams` — camelCase returns 400
  - Do NOT send `Accept: application/geo+json` on POST requests

#### Server 2: 52North

- **URL:** `https://csa.demo.52north.org/`
- **Auth:** None required
- **SSL:** Certificate is expired — all PowerShell commands MUST use `-SkipCertificateCheck`
- **PowerShell pattern:**
  ```powershell
  Invoke-RestMethod -Uri "https://csa.demo.52north.org/" -SkipCertificateCheck
  ```
- **Key quirks (read `known-server-quirks.md` for full details):**
  - `Accept` header routes to different backends (dual-backend architecture)
  - **NEVER use `Accept: application/json`** — returns empty collections
  - Use `Accept: application/geo+json` or `Accept: application/sml+json`
  - All Part 2 endpoints are broken (500/400/404) — Part 2 testing must use OSH only
  - featureType vocabulary mixes CURIEs and full URIs; systems have null featureType in GeoJSON
  - SensorML data is rich (identifiers, classifiers, components)

### Finding Numbering

Phase 4 findings use a new series: **P4-F1**, **P4-F2**, **P4-F3**, etc.

Prior findings (F1–F90 from Phase 2/3) retain their original numbers in the regression check. New findings discovered in Phase 4 get the P4-F prefix.

### Test Instructions

Follow this exact sequence. Record EVERYTHING — every HTTP request, every response status, every observation.

---

#### Step 1: Document Prior Findings (Regression Check)

Read the previous smoke test report and list ALL prior findings with their current status. For each:
- If it was marked **"Fixed"** — re-verify it's still fixed with a live request
- If it was marked **"Deferred"** — confirm it's still deferred, note if anything changed
- If it was marked **"Server limitation"** — confirm it's still present
- If it was marked **"Retracted"** — note that it stays retracted
- If it was marked **"Resolved"** — re-verify the resolution still holds

**Every** prior finding must appear in the regression table. None are "too old" to re-check.

---

#### Step 2: Test Server Connectivity, Profiles, and Resource Inventory

For EACH server:

1. Fetch the root API document
2. Fetch `/conformance` — record conformance classes
3. Fetch `/collections` — record all collections and their links
4. Document root document links (resource type → URL mappings)
5. **Build the full resource inventory:**

| Endpoint | Accept Header Used | HTTP Status | Item Count | Notes |
|----------|-------------------|-------------|-----------|-------|
| /systems | | | | |
| /deployments | | | | |
| /procedures | | | | |
| /samplingFeatures | | | | |
| /properties | | | | |
| /datastreams | | | | |
| /observations | | | | |
| /controlstreams | | | | |
| /commands | | | | |

6. Record specific resource IDs that will be used in subsequent steps (at least 2 per resource type if available)

---

#### Step 3: Test Resource Discovery

Simulate our `scanCsapiLinks()` behavior against BOTH servers:

1. **Convention 1** (ogc-cs: prefix): Check if any links use the `ogc-cs:` prefix
2. **Convention 2** (plain rel name): Check root document links for plain resource type names (`rel: "systems"`, `rel: "deployments"`, etc.)
3. **Convention 3** (rel: "items" + href): For each collection, extract `rel: "items"` links, verify segment extraction works with:
   - Query parameters in hrefs (must be stripped)
   - `featuresOfInterest` naming (must be normalized to `samplingFeatures`)
   - Mixed leading-slash conventions

Record how many resource types are discovered per convention per server.

---

#### Step 4: Hierarchical Navigation (Subsystems, Subdeployments, Bidirectional Links)

Test parent-child navigation for both servers (where endpoints work):

| Navigation | URL Pattern | OSH Status | 52N Status | Notes |
|------------|-------------|-----------|-----------|-------|
| System → subsystems | `/systems/{id}/subsystems` | | | |
| Subsystem → parent system | Verify parent link exists | | | |
| Deployment → subdeployments | `/deployments/{id}/subdeployments` | | | |
| System → deployments | `/systems/{id}/deployments` | | | |
| System → procedures | `/systems/{id}/procedures` | | | |
| System → datastreams | `/systems/{id}/datastreams` | | | |
| System → controlstreams | `/systems/{id}/controlstreams` | | | |
| System → samplingFeatures | `/systems/{id}/samplingFeatures` | | | |
| SF → systems | `/samplingFeatures/{id}/systems` | | | |
| Datastream → system | `/datastreams/{id}/systems` | | | |
| Datastream → observations | `/datastreams/{id}/observations` | | | |
| ControlStream → commands | `/controlstreams/{id}/commands` | | | |

For endpoints that return 400 (OSH known limitation), confirm they still return 400 (regression check, not a new finding).

---

#### Step 5: Test URL Generation — All Implemented Methods

For EACH server, test every implemented builder method. Use real resource IDs from Step 2. Record:

| Method | Generated URL | Server | HTTP Status | Notes |
|--------|--------------|--------|-------------|-------|

For methods that require a resource ID but the server has zero entries for that type, mark as **N/A (no data)** — the URL pattern is still validated by confirming the list endpoint works.

---

#### Step 6: Test Query Parameter Acceptance

Test each of these parameters against both servers (using a resource type with data where possible):

| Parameter | Method Used | URL | OSH Result | 52North Result |
|-----------|-------------|-----|------------|----------------|
| limit | | | | |
| offset | | | | |
| q | | | | |
| bbox | | | | |
| datetime (single) | | | | |
| datetime (interval) | | | | |
| id (single) | | | | |
| id (array) | | | | |
| recursive | | | | |
| f (format) | | | | |
| cursor | | | | |
| parent | | | | |

---

#### Step 7: DataStreams, Observations, and Schemas (Part 2)

*This step targets OSH only (52N Part 2 is completely broken).*

1. **List datastreams** — record count, sample IDs
2. **Fetch individual datastream** by ID — verify response shape
3. **Fetch datastream schema** (`/datastreams/{id}/schema`) — record:
   - Content-Type returned (expect `auto` on OSH — known quirk)
   - Schema structure: DataRecord fields, Quantity/Text/Vector types, uom formats
   - Compare at least 3 different datastream schemas (e.g., Temperature, Location, Acceleration)
4. **List observations** for a datastream — record:
   - Response envelope format
   - Observation `result` structure (flat JSON keyed by field names)
   - Verify `result` fields match the schema field names
5. **Test temporal filtering** on observations:
   - `datetime=2026-01-01T00:00:00Z/..` (open-ended)
   - `datetime=../2026-02-01T00:00:00Z` (open-ended past)
   - `datetime=2026-01-01T00:00:00Z/2026-02-01T00:00:00Z` (bounded)

---

#### Step 8: ControlStreams, Commands, and Command Status (Part 2)

*This step targets OSH only.*

1. **List controlstreams** (lowercase path!) — record count, sample IDs
2. **Fetch individual controlstream** by ID — verify response shape
3. **Fetch controlstream schema** (`/controlstreams/{id}/schema`)
4. **List commands** for a controlstream (`/controlstreams/{id}/commands`)
5. **Verify top-level `/commands` returns 404 or equivalent** (known limitation)
6. Document command status workflow if any command has a status endpoint

---

#### Step 9: SensorML Content Negotiation

For EACH server:

1. **OSH:** Fetch `/systems` with `?f=sml3` — verify SensorML JSON response
   - Record: `type`, `id`, `uniqueId`, `definition`, `label`, `validTime`
   - Verify `definition` is a full URI (SOSA namespace)
   - Verify `parsePhysicalSystem` can parse the response
2. **52N:** Fetch `/systems` with `Accept: application/sml+json`
   - Record all fields: identifiers, classifiers, documents, typeOf, definition
   - Verify `definition` vocabulary (CURIE vs full URI)
   - Verify parsers handle 52N's richer SML structure
3. **Cross-server SML comparison:**
   - Field presence/absence
   - Vocabulary format differences (URI vs CURIE)
   - Structure differences (minimal vs rich)

---

#### Step 10: FULL CRUD Testing — Write Operations

**⚠️ CRITICAL RULES:**
- **Only delete what you create during this test.** Do NOT delete any pre-existing data.
- **Create test data first**, use it for subsequent verification, then clean up at the end.
- **Record every write operation** with request body, response status, and response headers.
- **If a write operation fails, document the failure as a finding** — do not skip it.

##### 10a: Create Test Resources (OSH)

Create one resource of each type in this order (parent resources first):

1. **Create a System** (`POST /systems`)
   - Body: minimal valid GeoJSON Feature with `featureType: "http://www.w3.org/ns/sosa/Sensor"`
   - Content-Type: `application/geo+json`
   - Record: Location header → new system ID
   - **Do NOT include Accept header on POST**

2. **Create a Procedure** (`POST /procedures`)
   - Body: minimal valid GeoJSON Feature with `featureType: "http://www.w3.org/ns/sosa/Procedure"`
   - Record: new procedure ID

3. **Create a Deployment** (`POST /deployments`)
   - Body: minimal valid GeoJSON Feature with `featureType: "http://www.w3.org/ns/sosa/Deployment"`
   - Record: new deployment ID

4. **Create a SamplingFeature** (`POST /samplingFeatures`)
   - Body: minimal valid GeoJSON Feature with `featureType: "http://www.w3.org/ns/sosa/Sample"`
   - Record: new SF ID

5. **Create a Subsystem** (`POST /systems/{parentId}/subsystems`)
   - Use the system created in step 1 as parent
   - Record: new subsystem ID

6. **Create a Subdeployment** (`POST /deployments/{parentId}/subdeployments`)
   - Use the deployment created in step 3 as parent
   - Record: new subdeployment ID

7. **Create a Datastream** (`POST /systems/{id}/datastreams`)
   - Must use nested path (top-level POST returns 405)
   - Content-Type: `application/json`
   - Body: include schema (DataRecord with at least one Quantity field)
   - Record: new datastream ID

8. **Create a ControlStream** (`POST /systems/{id}/controlstreams`)
   - Must use nested path
   - Body: include schema
   - Record: new controlstream ID

9. **Create an Observation** (`POST /datastreams/{id}/observations`)
   - Use the datastream created in step 7
   - Body: result matching the datastream schema
   - Content-Type: `application/json`
   - Record: new observation ID

10. **Create a Command** (`POST /controlstreams/{id}/commands`)
    - Use the controlstream created in step 8
    - Body: parameters matching the controlstream schema
    - Record: new command ID

**Record all created resource IDs in a cleanup table:**

| Resource Type | ID | Parent | Created At |
|--------------|-----|--------|------------|
| System | | — | |
| Procedure | | — | |
| Deployment | | — | |
| SamplingFeature | | — | |
| Subsystem | | System {id} | |
| Subdeployment | | Deployment {id} | |
| Datastream | | System {id} | |
| ControlStream | | System {id} | |
| Observation | | Datastream {id} | |
| Command | | ControlStream {id} | |

##### 10b: Read-Back Verification

For each created resource, immediately fetch it by ID and verify:
- HTTP status is 200
- Response contains the fields you sent
- `uid` matches what was assigned
- Resource appears in the parent's list endpoint

##### 10c: Update Test Resources (OSH)

For each Part 1 resource created (system, procedure, deployment, samplingFeature):

1. **PUT** the resource with a modified `label` or `description`
   - Content-Type: `application/geo+json`
   - ⚠️ **Include `uid` in the PUT body** — OSH returns 400 without it
2. **GET** the resource again — verify the update took effect
3. Record: request body, response status, response body diff

| Resource | PUT Status | Field Changed | Verified via GET? |
|----------|-----------|---------------|-------------------|
| System | | | |
| Procedure | | | |
| Deployment | | | |
| SamplingFeature | | | |

##### 10d: Delete Test Resources (Cleanup)

Delete resources in **reverse creation order** (children first, parents last):

1. Delete Command
2. Delete Observation
3. Delete ControlStream
4. Delete Datastream
5. Delete Subdeployment
6. Delete Subsystem
7. Delete SamplingFeature
8. Delete Deployment
9. Delete Procedure
10. Delete System

For each deletion:
- Record HTTP status (expect 204 or 200)
- Verify the resource is no longer accessible (GET returns 404)
- Verify the resource no longer appears in the parent's list endpoint

| Resource | DELETE Status | GET After Delete | Cleaned Up? |
|----------|-------------|-----------------|-------------|
| Command | | | |
| Observation | | | |
| ControlStream | | | |
| Datastream | | | |
| Subdeployment | | | |
| Subsystem | | | |
| SamplingFeature | | | |
| Deployment | | | |
| Procedure | | | |
| System | | | |

**⚠️ If any deletion fails, document it as a finding and manually verify the resource still exists. Do NOT attempt to delete other pre-existing resources to "clean up."**

##### 10e: 52North Write Operations (If Supported)

If write capabilities have been added to 52N since the last test:
1. Attempt a system create (`POST /systems`)
2. Record result — if 405/500/501, note as "52N write not supported" and move on
3. If successful, perform the same create/read/update/delete cycle as OSH

---

#### Step 11: Recognition, Extraction, and Parsing Validation

**Carried forward from Phase 3 — these tests are NOT dropped.**

1. **`classifyFeature` recognition:** For each resource fetched in Steps 2–4, verify that the library's `classifyFeature` function correctly identifies the resource type from `featureType`
   - Test full URI forms (OSH)
   - Test CURIE forms (52N)
   - Test null featureType (52N systems)
   - Test misclassified featureType (52N procedure with `sosa:Sensor`)

2. **`parseValidTime` extraction:** For resources with `validTime`:
   - Array format: `["ISO", "now"]` (OSH)
   - Null value (52N)
   - Absent field (some OSH resources)
   - Verify the library handles all three cases without error

3. **Vocabulary inventory:** Record every unique `featureType` value across both servers:
   | featureType Value | Server | Resource Type | Format |
   |-------------------|--------|---------------|--------|
   | | | | URI / CURIE / null |

4. **Content-Type availability matrix:**
   | Resource Type | OSH json | OSH geojson | OSH sml3 | 52N json | 52N geo+json | 52N sml+json |
   |---------------|----------|-------------|----------|----------|--------------|-------------|
   | systems | | | | | | |
   | deployments | | | | | | |
   | etc. | | | | | | |

---

#### Step 12: Schema Parsing Validation

For OSH datastream and controlstream schemas:

1. Parse each schema with the library's SWE Common parser
2. Verify field names, types, and UOM extraction
3. Cross-reference observation `result` fields with schema field names
4. Test at least 3 datastream schemas and 3 controlstream schemas

---

#### Step 13: Cross-Server Comparison

Produce a comprehensive comparison table:

| Dimension | OpenSensorHub | 52North | Match? |
|-----------|--------------|---------|--------|
| Conformance classes advertised | | | |
| Discovery convention(s) used | | | |
| Default content type | | | |
| Content negotiation mechanism | | | |
| Response envelope format | | | |
| featureType vocabulary | | | |
| validTime format | | | |
| SensorML access method | | | |
| SensorML richness | | | |
| Part 2 endpoint availability | | | |
| Write operation support | | | |
| Sub-resource endpoint support | | | |
| SSL/TLS status | | | |
| Auth requirement | | | |

---

#### Step 14: Classify All New Findings

For each new finding (using **P4-F{N}** numbering), classify with:

- **ID:** P4-F{N}
- **Severity:** Critical / Moderate / Low / Informational
- **Category:** Code bug / Server limitation / Interoperability concern / Naming variation / Design gap
- **Affects:** Which function or code path
- **Ownership:** "Ours" (our code needs a fix) / "Upstream" (server-side) / "Shared" (both)
- **Status:** Needs fix / Needs design decision / Informational / Deferred to Phase N
- **Evidence:** What was observed (include request + response)

---

#### Step 15: Generate Impact Assessment

For any findings classified as "Ours" or "Shared":
1. Identify the specific file and function affected
2. Assess upstream impact (does the fix touch any upstream file?)
3. Estimate fix complexity (one-line, small, medium, architectural)

---

#### Step 16: Present Findings to User

After completing Steps 1–15, present a summary to the user BEFORE writing the report file:

1. Quick verdict: pass/fail/conditional
2. Count of regression issues (if any)
3. Count of new findings by severity
4. CRUD test results summary (create/read/update/delete success rates)
5. Any critical items requiring immediate attention
6. Ask: "Should I write the full report and commit it?"

---

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
**Finding Series:** Phase 4 (P4-F1, P4-F2, ...)

> This is smoke test #{{N}} in the series. See also:
> - [Previous smoke test](link)

## Test Methodology

{{Brief description — includes CRUD operations, not read-only like Phase 3}}

## Server Profiles

### OpenSensorHub
| Spec Part | Conformance Classes |
|-----------|-------------------|
| ... | ... |

Resource Inventory: {{table with counts per endpoint}}
Top-level resource links: {{table}}

### 52North
{{Same structure}}

## Results

### Prior Findings — Regression Check

| Finding | Original Phase | Status | Evidence |
|---------|---------------|--------|----------|
| F1 | Phase 2 | Still Fixed ✅ / Changed ⚠️ | ... |
| ... | ... | ... | ... |

### URL Generation — All {{N}} Methods

#### {{Resource Type}} Methods ({{N}} methods) {{— NEW if applicable}}

| Method Call | URL Pattern | OSH | 52North |
|-------------|------------|-----|---------|
| ... | ... | ✅/❌/N/A | ✅/❌/N/A |

### Query Parameter Acceptance

| Parameter | Method | URL | OSH | 52North |
|-----------|--------|-----|-----|---------|
| ... | ... | ... | ✅/❌ | ✅/❌ |

### Hierarchical Navigation

| Navigation | OSH | 52N | Notes |
|------------|-----|-----|-------|
| ... | ... | ... | ... |

### Part 2 — DataStreams & Observations (OSH)

{{Schema details, observation structure, temporal filtering results}}

### Part 2 — ControlStreams & Commands (OSH)

{{Schema details, command structure, status workflow}}

### SensorML Content Negotiation

| Aspect | OSH | 52N |
|--------|-----|-----|
| Access method | ?f=sml3 | Accept: application/sml+json |
| ... | ... | ... |

### CRUD Operations

#### Create Results

| Resource Type | Server | POST Status | Location Header | Read-Back OK? |
|---------------|--------|-------------|-----------------|---------------|
| ... | ... | ... | ... | ... |

#### Update Results

| Resource Type | Server | PUT Status | Change Verified? |
|---------------|--------|-----------|-----------------|
| ... | ... | ... | ... |

#### Delete Results

| Resource Type | Server | DELETE Status | 404 After Delete? | List Removed? |
|---------------|--------|-------------|-------------------|---------------|
| ... | ... | ... | ... | ... |

### Recognition, Extraction, and Parsing

{{classifyFeature results, parseValidTime results, vocabulary inventory}}

### Schema Parsing Validation

{{SWE Common parser results for datastream and controlstream schemas}}

## New Findings

### P4-F1 ({{Severity}}): {{Title}}

**Severity:** {{Critical/Moderate/Low/Informational}}
**Category:** {{Code bug / Server limitation / Interoperability concern}}
**Affects:** {{function/file}}
**Ownership:** {{Ours / Upstream / Shared}}
**Evidence:** {{What was observed}}
**Status:** {{Needs fix / Deferred / Informational}}

## Data Shape Observations

{{Numbered list of response shape observations}}

## Cross-Server Comparison

| Dimension | OpenSensorHub | 52North | Match? |
|-----------|--------------|---------|--------|
| ... | ... | ... | ✅/❌ |

## What WORKS (Verified)

| Capability | Status |
|------------|--------|
| ... | ✅ |

## CRUD Summary

| Operation | Systems | Deployments | Procedures | SFs | Datastreams | Observations | ControlStreams | Commands |
|-----------|---------|-------------|------------|-----|-------------|-------------|----------------|----------|
| Create | | | | | | | | |
| Read | | | | | | | | |
| Update | | | | | | | | |
| Delete | | | | | | | | |

## What Remains (Phase 4 Concerns)

| Issue | Severity | Component | Target Phase |
|-------|----------|-----------|-------------|
| ... | ... | ... | ... |

## Comparison: Phase {{prev}} → Phase {{current}}

| Dimension | Phase {{prev}} | Phase {{current}} |
|-----------|---------------|------------------|
| Methods implemented | {{N}} | {{N}} |
| CRUD tested | No | Yes |
| Part 2 coverage | {{status}} | {{status}} |
| Findings total | {{N}} | {{N}} |
| ... | ... | ... |

## Verdict

{{2-3 paragraph assessment: regressions?, new findings?, CRUD success rate?, readiness to proceed?}}
```

Then commit the report, push, and confirm the file is at the expected path.

If any new findings are classified as "Ours — Needs fix", create a GitHub issue for each using `docs/governance/issue-creation-prompt-template.md`.
```

---

## Post-Smoke-Test Workflow

After the smoke test report is generated:

1. **Review new findings** — decide which are "fix now" vs "defer"
2. **Create GitHub issues** for "Ours — Needs fix" findings using `docs/governance/issue-creation-prompt-template.md`
3. **Complete fix issues** before proceeding to the next resource type
4. **The next smoke test will re-verify** all prior findings — nothing is forgotten
5. **Update the cross-server interoperability analysis** if new interoperability findings emerged
6. **Update `known-server-quirks.md`** if new server behavior is discovered

---

## Critical Rules (Non-Negotiable)

These rules come from Phase 2 + Phase 3 lessons learned, plus Phase 4 CRUD requirements:

- [ ] **Read `known-server-quirks.md` FIRST** — Before issuing any HTTP request, read the full server quirks document. You wrote the code. You know the servers. Don't waste time re-discovering known issues.
- [ ] **Both servers tested** — Every smoke test MUST hit both OpenSensorHub AND 52North. Single-server testing missed real bugs across three prior smoke tests.
- [ ] **OSH credentials not in repo** — The OpenSensorHub username and password are NEVER committed to the repository, NEVER written into any file, and NEVER included in the report. If you don't have them, ask the user.
- [ ] **52North needs `-SkipCertificateCheck`** — Every PowerShell command to the 52North server MUST include this flag due to the expired SSL certificate.
- [ ] **All prior findings re-checked** — The regression check section must cover EVERY finding from EVERY prior smoke test, not just the most recent one.
- [ ] **New findings get P4-F numbering** — Phase 4 findings use `P4-F1`, `P4-F2`, etc. Do not continue the F1–F90 series.
- [ ] **New findings get ownership classification** — Every new finding must be classified as "Ours", "Upstream", or "Shared" with evidence.
- [ ] **Only delete what you create** — CRUD testing creates test data and deletes ONLY that data. Never delete pre-existing resources. Record every created resource ID in the cleanup table.
- [ ] **Create before you test** — Don't rely on finding existing resources for CRUD testing. Create your own test data at the start of Step 10, use it for all write-operation testing, then clean it up.
- [ ] **Record every HTTP request** — For CRUD operations especially, record the full request (method, URL, headers, body) and full response (status, headers, body or summary).
- [ ] **Content-Type matters for writes** — Part 1 POST/PUT uses `application/geo+json`. Part 2 POST/PUT uses `application/json`. Getting this wrong returns 400/415.
- [ ] **Test exhaustively** — Test every capability the library exposes, not just what the demo UI exercises. If the library has a method, test it against a live server.
- [ ] **Document Accept headers used** — For every request, record which Accept header (or `?f=` parameter) was used.

---

## Naming Convention

Reports follow these naming patterns:

```
docs/implementation/live-server-smoke-test-post-phase-{X.Y}.md     — Standard post-phase smoke test
docs/implementation/live-server-smoke-test-{server-name}.md         — New server comparative test
docs/implementation/cross-server-interoperability-analysis.md       — Cross-server synthesis
docs/implementation/live-server-retest-post-issues-{N}-{M}.md      — Targeted retest after fixes
```

---

## Changes from Phase 3 Template

| Aspect | Phase 3 | Phase 4 |
|--------|---------|---------|
| Finding numbers | F1–F90 (continuing series) | P4-F1, P4-F2, ... (new series) |
| Write operations | Read-only observation (no writes) | Full CRUD — create, read, update, delete |
| Test data | Use existing server data | Create test data, use it, delete only what you created |
| Part 2 coverage | URL generation only | Full workflow — schemas, observations, commands |
| SensorML | Basic fetch verification | Parse validation, cross-server comparison |
| Hierarchical nav | Basic subsystem check | Full bidirectional navigation matrix |
| Server quirks ref | Inline in template | External doc: `known-server-quirks.md` |
| Schema validation | Not tested | SWE Common parser verification |
| Steps | 9 | 16 |
| Scope | Methods the UI exercises | ALL library methods, exhaustively |

---

## Server Quick Reference

| Property | OpenSensorHub | 52North |
|----------|--------------|---------|
| URL | `http://45.55.99.236:8080/sensorhub/api` | `https://csa.demo.52north.org/` |
| Auth | Basic (⚠️ ask user for credentials) | None |
| SSL | HTTP (no SSL issues) | HTTPS (expired cert — use `-SkipCertificateCheck`) |
| Conformance | 20+ CSAPI classes | Zero CSAPI classes |
| Content negotiation | `?f=` query parameter (Accept ignored) | `Accept` header (routes to different backends) |
| Default content type | `application/json` | `application/sml+json` |
| Part 1 resources | ✅ All work | ✅ systems, deployments, procedures (SFs empty) |
| Part 2 resources | ✅ All work | ❌ All broken (500/400/404) |
| Write operations | ✅ Full CRUD | ❓ Not tested |
| SML access | `?f=sml3` | `Accept: application/sml+json` |
| Response envelope | `{items}` or `{FeatureCollection}` | `{items}` or `{FeatureCollection}` depending on Accept |
