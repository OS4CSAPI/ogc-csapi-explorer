# Phase 7 — Live Server Smoke Test Prompt Template

**Purpose:** Comprehensive live server smoke test for the full CSAPI contribution, with focused validation of Phase 7 (Code Review Cleanup) changes. Covers all 9 resource types across 3 live OGC Connected Systems servers: exhaustive parser validation, full CRUD operations, query parameter coverage (including new `sortBy`/`sortOrder`), hierarchical navigation, SensorML content negotiation, schema parsing, cross-server interoperability comparison, and Phase 7 bug-fix / security-fix regression verification.

**Version:** 1.0
**Date:** March 7, 2026
**Supersedes:** `docs/governance/smoke-test-prompt-template-phase-5.md` (Phase 5 — still valid for historical reference)
**Related:** `docs/governance/smoke-test-prompt-template-phase-6.md` (Phase 6 — architecture verification only, not live server testing)
**Report destination:** `docs/implementation/live-server-smoke-test-post-phase-7.md`

---

## What's New in This Template vs Phase 5

| Aspect                       | Phase 5 Template           | Phase 7 Template                                                              |
| ---------------------------- | -------------------------- | ----------------------------------------------------------------------------- |
| Servers tested               | 2 (OSH + 52North)          | **3** (OSH + 52North + **OS4CSAPI-OSH**)                                      |
| Query parameters             | 12 params                  | **14 params** (+`sortBy`, +`sortOrder`)                                       |
| Phase 7 bug-fix verification | N/A                        | **Dedicated step** (Step 16) — 7 specific fixes verified against live servers |
| Security fix verification    | N/A                        | **Included in Step 16** — URL scheme validation, subPath encoding             |
| Finding series               | P5-F1, P5-F2...            | **P7-F1, P7-F2...**                                                           |
| Test baseline                | 1,283 tests / 29 suites    | **1,339 tests / 30 suites**                                                   |
| Required reading             | 8 documents                | **10 documents** (+ Phase 7 code reviews, review report)                      |
| Steps                        | 18                         | **20** (Steps 16–17 are new Phase 7 verification)                             |
| Prior findings to regress    | F1–F90, P4-F1–F5, P5-F1–F5 | **All prior** + Phase 6 architecture verification                             |
| Nested parent ID CRUD        | Not tested                 | **Tested** — command/observation CRUD with parent IDs                         |
| 3rd server comparison        | N/A                        | **Full cross-server comparison** across 3 servers                             |

---

## When to Use

Trigger this prompt after any of these milestones:

1. **Phase 7 (Code Review Cleanup) is complete** — this is the primary trigger
2. **Before merging to `clean-pr`** — final gate before upstream submission
3. **After fixing any Phase 7 smoke test finding** — re-verify the fix
4. **Before updating PR #136** — comprehensive validation before jahow sees changes
5. **After changes to URL generation, serialization, parsing, or security hardening**
6. **After adding or changing query parameter support** (e.g., sortBy/sortOrder)

Do NOT trigger after doc-only changes, test-only changes, or code review cleanups that don't affect URL generation, serialization, parsing, or server interaction.

---

## How to Use

Copy the **Prompt** section below and paste it into the conversation after completing coding work. Replace all `{{...}}` placeholders with actual values.

---

## Prompt

````
Please perform a Phase 7 live server smoke test of the full CSAPI contribution with focused Phase 7 verification.

### Scope

**Phase:** 7
**Issues completed since last smoke test:** {{List all Phase 7 issue numbers — #98, #100, #102, #111, #139, #140, #141–#151, #154–#161 and titles}}
**Methods/parsers to focus on:** All 91+ public methods, all parsers, all 9 resource types, plus Phase 7 bug fixes and sortBy/sortOrder
**Last smoke test:** `docs/implementation/live-server-smoke-test-post-phase-5.5.md` (ST#23, commit af0c1aa)

### Required Reading — BEFORE Starting

Read these documents IN FULL before issuing any HTTP requests:

| Document | Location | Purpose |
|----------|----------|---------|
| Known Server Quirks | `docs/governance/known-server-quirks.md` | **CRITICAL** — All known server behaviors, bugs, content-negotiation rules. Prevents re-discovering known issues |
| Previous Smoke Test | `docs/implementation/live-server-smoke-test-post-phase-5.5.md` | ST#23 — prior findings to re-check |
| Cross-Server Analysis | `docs/implementation/cross-server-interoperability-analysis.md` | Known server differences |
| Implementation Guide | `docs/planning/csapi-implementation-guide.md` | Spec-correct URL patterns |
| AI Operational Constraints | `docs/governance/AI_OPERATIONAL_CONSTRAINTS.md` | Behavioral boundaries |
| Fixtures Guide | `docs/testing/fixtures-guide.md` | Fixture structure and shape reference |
| Phase 7 Code Review Cleanup Plan | `docs/planning/phase-7/P7-code-review-cleanup-plan.md` | All 17 issues and execution order |
| Phase 7.1 Code Review | `docs/implementation/phase-7.1-code-review.md` | Code review findings and resolutions |
| Full-Scope Contribution Review | `docs/implementation/full-scope-contribution-review.md` | Final gate review — deferred features, test counts |
| Parser Source Files | `src/ogc-api/csapi/formats/` (all files) | Exact parser logic to validate |

### Server Information

We test against THREE servers. All three must be tested in every smoke test.

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
  - All Part 2 endpoints are broken (500/400/404) — Part 2 testing must use OSH servers only
  - featureType vocabulary mixes CURIEs and full URIs; systems have null featureType in GeoJSON
  - SensorML data is rich (identifiers, classifiers, components)

#### Server 3: OS4CSAPI-OSH (User-operated)

- **URL:** `https://os4csapi-osh.duckdns.org/sensorhub/api`
- **Auth:** Basic authentication required
- **⚠️ CREDENTIAL REMINDER:** Same as Server 1 — credentials are NOT stored in this repository. If you do not have the credentials from a prior conversation context, you MUST ask the user for them before proceeding.
- **SSL:** HTTPS with valid certificate (no `-SkipCertificateCheck` needed)
- **PowerShell pattern:**
  ```powershell
  $cred3 = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("{{username}}:{{password}}"))
  $headers3 = @{ Authorization = "Basic $cred3" }
  Invoke-RestMethod -Uri "https://os4csapi-osh.duckdns.org/sensorhub/api" -Headers $headers3
  ```
- **Expected quirks:** This is an OpenSensorHub instance, so most OSH quirks from Server 1 are expected to apply:
  - Likely ignores Accept headers — use `?f=json`, `?f=geojson`, `?f=sml3`
  - Full CRUD likely works (confirm during Step 2)
  - Part 2 endpoints likely work (confirm during Step 2)
  - Use lowercase `/controlstreams`
- **⚠️ FIRST-CONTACT PROTOCOL:** This server has NOT been previously tested. Before running the standard test suite against it, perform the exploratory discovery in Step 2 to understand its capabilities, data inventory, and any unique quirks. Document ALL differences from Server 1.

### Finding Numbering

Phase 7 findings use a new series: **P7-F1**, **P7-F2**, **P7-F3**, etc.

Prior findings (F1–F90 from Phase 2/3, P4-F{N} from Phase 4, P5-F{N} from Phase 5) retain their original numbers in the regression check. New findings discovered in Phase 7 get the P7-F prefix.

### Test Instructions

Follow this exact sequence. Record EVERYTHING — every HTTP request, every response status, every observation.

---

#### Step 1: Document Prior Findings (Regression Check)

Read the previous smoke test report (ST#23, Phase 5.5) and list ALL prior findings with their current status. For each:

- If it was marked **"Fixed"** — re-verify it's still fixed with a live request
- If it was marked **"Deferred"** — confirm it's still deferred, note if anything changed
- If it was marked **"Server limitation"** — confirm it's still present
- If it was marked **"Retracted"** — note that it stays retracted
- If it was marked **"Resolved"** — re-verify the resolution still holds

**Every** prior finding must appear in the regression table. None are "too old" to re-check.

**Phase 7 attention items:** Phase 7 changed parsers (type safety), URL builders (DRY refactor, bug fixes), and security checks. Any finding related to these areas deserves extra scrutiny — Phase 7 should have improved them, not regressed them.

---

#### Step 2: Test Server Connectivity, Profiles, and Resource Inventory

For EACH of the THREE servers:

1. Fetch the root API document
2. Fetch `/conformance` — record conformance classes
3. Fetch `/collections` — record all collections and their links
4. Document root document links (resource type → URL mappings)
5. **Build the full resource inventory:**

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

**For Server 3 (OS4CSAPI-OSH — first contact):**

7. Compare its conformance classes against Server 1 (OSH) — note any differences
8. Build a content negotiation profile: does `?f=json` work? `?f=geojson`? `?f=sml3`?
9. Check if Accept headers are also ignored (same as Server 1?)
10. Record its data inventory — it may have different/fewer resources than Server 1
11. Test if Part 2 endpoints are available (datastreams, observations, controlstreams, commands)
12. Document ALL differences from Server 1 in a dedicated "Server 3 Discovery Notes" section

---

#### Step 3: Test Resource Discovery

Simulate our `scanCsapiLinks()` behavior against ALL THREE servers:

1. **Convention 1** (ogc-cs: prefix): Check if any links use the `ogc-cs:` prefix
2. **Convention 2** (plain rel name): Check root document links for plain resource type names (`rel: "systems"`, `rel: "deployments"`, etc.)
3. **Convention 3** (rel: "items" + href): For each collection, extract `rel: "items"` links, verify segment extraction works with:
   - Query parameters in hrefs (must be stripped)
   - `featuresOfInterest` naming (must be normalized to `samplingFeatures`)
   - Mixed leading-slash conventions

Record how many resource types are discovered per convention per server.

**Phase 7 security verification:** Confirm that `scanCsapiLinks()` would reject any links with non-HTTP(S) schemes (e.g., `javascript:`, `data:`) — this tests Issue #147 (URL scheme validation). If any server returns non-HTTP links, record them as findings.

---

#### Step 4: Hierarchical Navigation (Subsystems, Subdeployments, Bidirectional Links)

Test parent-child navigation for all three servers (where endpoints work):

| Navigation                  | URL Pattern                        | OSH Status | 52N Status | OS4 Status | Notes |
| --------------------------- | ---------------------------------- | ---------- | ---------- | ---------- | ----- |
| System → subsystems         | `/systems/{id}/subsystems`         |            |            |            |       |
| Subsystem → parent system   | Verify parent link exists          |            |            |            |       |
| Deployment → subdeployments | `/deployments/{id}/subdeployments` |            |            |            |       |
| System → deployments        | `/systems/{id}/deployments`        |            |            |            |       |
| System → procedures         | `/systems/{id}/procedures`         |            |            |            |       |
| System → datastreams        | `/systems/{id}/datastreams`        |            |            |            |       |
| System → controlstreams     | `/systems/{id}/controlstreams`     |            |            |            |       |
| System → samplingFeatures   | `/systems/{id}/samplingFeatures`   |            |            |            |       |
| SF → systems                | `/samplingFeatures/{id}/systems`   |            |            |            |       |
| Datastream → system         | `/datastreams/{id}/systems`        |            |            |            |       |
| Datastream → observations   | `/datastreams/{id}/observations`   |            |            |            |       |
| ControlStream → commands    | `/controlstreams/{id}/commands`    |            |            |            |       |

For endpoints that return 400 (OSH known limitation), confirm they still return 400 (regression check, not a new finding).

**Phase 7 verification:** `getDeploymentSystems()` was deprecated in Issue #139 — verify that `deployedSystems` is NOT a valid sub-resource URL on any server (confirming the deprecation was correct).

---

#### Step 5: Test URL Generation — All Implemented Methods

For EACH server, test every implemented builder method. Use real resource IDs from Step 2. Record:

| Method | Generated URL | Server | HTTP Status | Notes |
| ------ | ------------- | ------ | ----------- | ----- |

For methods that require a resource ID but the server has zero entries for that type, mark as **N/A (no data)** — the URL pattern is still validated by confirming the list endpoint works.

---

#### Step 6: Test Query Parameter Acceptance

Test each of these parameters against all three servers (using a resource type with data where possible):

| Parameter           | Method Used | URL | OSH Result | 52N Result | OS4 Result |
| ------------------- | ----------- | --- | ---------- | ---------- | ---------- |
| limit               |             |     |            |            |            |
| offset              |             |     |            |            |            |
| q                   |             |     |            |            |            |
| bbox                |             |     |            |            |            |
| datetime (single)   |             |     |            |            |            |
| datetime (interval) |             |     |            |            |            |
| id (single)         |             |     |            |            |            |
| id (array)          |             |     |            |            |            |
| recursive           |             |     |            |            |            |
| f (format)          |             |     |            |            |            |
| cursor              |             |     |            |            |            |
| parent              |             |     |            |            |            |
| **sortBy (single)** |             |     |            |            |            |
| **sortBy (array)**  |             |     |            |            |            |
| **sortOrder (asc)** |             |     |            |            |            |
| **sortOrder (desc)**|             |     |            |            |            |

**Phase 7 — sortBy/sortOrder testing (Issue #161):**

1. Test `sortBy` with a single string value: `?sortBy=name` against `/systems`
2. Test `sortBy` with a comma-separated array: `?sortBy=name,description`
3. Test `sortOrder=asc` alone and combined with `sortBy`
4. Test `sortOrder=desc` alone and combined with `sortBy`
5. Test combined: `?sortBy=name&sortOrder=desc&limit=5`
6. Record server responses — some servers may not support sorting (return 400 or ignore the parameter). Both behaviors are acceptable; document which.

---

#### Step 7: DataStreams, Observations, and Schemas (Part 2)

_This step targets OSH servers only (52N Part 2 is completely broken). Test against BOTH Server 1 (OSH) and Server 3 (OS4CSAPI-OSH)._

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

**Phase 7 verification — paramsSchema fix (Issue #140):**

6. Fetch a controlstream schema from each OSH server — verify the response includes `commandSchema` or `paramsSchema`
7. If the server returns `paramsSchema` (older OSH format), confirm the library would now accept it (previously it was silently dropped)

---

#### Step 8: ControlStreams, Commands, and Command Status (Part 2)

_This step targets OSH servers only. Test against BOTH Server 1 (OSH) and Server 3 (OS4CSAPI-OSH)._

1. **List controlstreams** (lowercase path!) — record count, sample IDs
2. **Fetch individual controlstream** by ID — verify response shape
3. **Fetch controlstream schema** (`/controlstreams/{id}/schema`)
4. **List commands** for a controlstream (`/controlstreams/{id}/commands`)
5. **Verify top-level `/commands` endpoint behavior** (may return 404 or list all commands)
6. Document command status workflow if any command has a status endpoint

**Phase 7 verification — nested parent IDs (Issue #102):**

7. For command endpoints, verify nested URL patterns work: `/controlstreams/{csId}/commands/{cmdId}`
8. For observation endpoints, verify nested URL patterns work: `/datastreams/{dsId}/observations/{obsId}`
9. Confirm both top-level (`/commands/{id}`) and nested (`/controlstreams/{csId}/commands/{id}`) paths return the same resource

---

#### Step 9: SensorML Content Negotiation

For EACH of the THREE servers:

1. **OSH (Server 1):** Fetch `/systems` with `?f=sml3` — verify SensorML JSON response
   - Record: `type`, `id`, `uniqueId`, `definition`, `label`, `validTime`
   - Verify `definition` is a full URI (SOSA namespace)
   - Verify `parsePhysicalSystem` can parse the response
2. **52N (Server 2):** Fetch `/systems` with `Accept: application/sml+json`
   - Record all fields: identifiers, classifiers, documents, typeOf, definition
   - Verify `definition` vocabulary (CURIE vs full URI)
   - Verify parsers handle 52N's richer SML structure
3. **OS4CSAPI-OSH (Server 3):** Fetch `/systems` with `?f=sml3`
   - Compare SensorML structure to Server 1 — are they identical?
   - Record any differences in field presence, definitions, or vocabulary
4. **Cross-server SML comparison (3-way):**
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

##### 10a: Create Test Resources

_Run against Server 1 (OSH) and Server 3 (OS4CSAPI-OSH). 52N write support is untested._

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

**Record all created resource IDs in a cleanup table (one per server):**

| Resource Type   | OSH ID | OS4 ID | Parent             | Created At |
| --------------- | ------ | ------ | ------------------ | ---------- |
| System          |        |        | —                  |            |
| Procedure       |        |        | —                  |            |
| Deployment      |        |        | —                  |            |
| SamplingFeature |        |        | —                  |            |
| Subsystem       |        |        | System {id}        |            |
| Subdeployment   |        |        | Deployment {id}    |            |
| Datastream      |        |        | System {id}        |            |
| ControlStream   |        |        | System {id}        |            |
| Observation     |        |        | Datastream {id}    |            |
| Command         |        |        | ControlStream {id} |            |

##### 10b: Read-Back Verification

For each created resource on each server, immediately fetch it by ID and verify:

- HTTP status is 200
- Response contains the fields you sent
- `uid` matches what was assigned
- Resource appears in the parent's list endpoint

##### 10c: Update Test Resources

For each Part 1 resource created (system, procedure, deployment, samplingFeature) on each server:

1. **PUT** the resource with a modified `label` or `description`
   - Content-Type: `application/geo+json`
   - ⚠️ **Include `uid` in the PUT body** — OSH returns 400 without it
2. **GET** the resource again — verify the update took effect
3. Record: request body, response status, response body diff

| Resource        | Server | PUT Status | Field Changed | Verified via GET? |
| --------------- | ------ | ---------- | ------------- | ----------------- |
| System          | OSH    |            |               |                   |
| System          | OS4    |            |               |                   |
| Procedure       | OSH    |            |               |                   |
| Procedure       | OS4    |            |               |                   |
| Deployment      | OSH    |            |               |                   |
| Deployment      | OS4    |            |               |                   |
| SamplingFeature | OSH    |            |               |                   |
| SamplingFeature | OS4    |            |               |                   |

##### 10d: Delete Test Resources (Cleanup)

Delete resources in **reverse creation order** (children first, parents last) on EACH server:

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

| Resource        | Server | DELETE Status | GET After Delete | Cleaned Up? |
| --------------- | ------ | ------------- | ---------------- | ----------- |
| Command         | OSH    |               |                  |             |
| Command         | OS4    |               |                  |             |
| Observation     | OSH    |               |                  |             |
| Observation     | OS4    |               |                  |             |
| ...             | ...    |               |                  |             |

**⚠️ If any deletion fails, document it as a finding and manually verify the resource still exists. Do NOT attempt to delete other pre-existing resources to "clean up."**

##### 10e: 52North Write Operations (If Supported)

If write capabilities have been added to 52N since the last test:

1. Attempt a system create (`POST /systems`)
2. Record result — if 405/500/501, note as "52N write not supported" and move on
3. If successful, perform the same create/read/update/delete cycle as the OSH servers

---

#### Step 11: Format Parser Validation Against Live Data

**This is the core parser validation step — validates parsers against real server JSON, not just fixtures.**

For each parser, fetch live data from ALL applicable servers, feed the raw JSON through the parser, and verify the output matches expectations.

##### 11a: Fixture Shape Comparison

Before running parsers, compare the **shapes** of live server responses against unit test fixtures:

1. For each parser's resource type, fetch at least 2 live resources from EACH OSH server
2. Record every top-level field name present in the live JSON
3. Compare against the fixture shapes used in unit tests (`src/ogc-api/csapi/formats/*.spec.ts`)
4. Flag any fields present in live data but absent from fixtures (indicates fixture coverage gap)
5. Flag any fields present in fixtures but absent from live data (indicates over-specification)

| Resource Type | Server | Live Fields | Fixture Fields | Extra in Live | Missing from Live |
| ------------- | ------ | ----------- | -------------- | ------------- | ----------------- |
| Property      | OSH    |             |                |               |                   |
| Property      | OS4    |             |                |               |                   |
| Datastream    | OSH    |             |                |               |                   |
| Datastream    | OS4    |             |                |               |                   |
| Observation   | OSH    |             |                |               |                   |
| Observation   | OS4    |             |                |               |                   |
| ControlStream | OSH    |             |                |               |                   |
| ControlStream | OS4    |             |                |               |                   |
| Command       | OSH    |             |                |               |                   |
| Command       | OS4    |             |                |               |                   |
| CommandStatus | OSH    |             |                |               |                   |
| CommandStatus | OS4    |             |                |               |                   |

##### 11b: parseProperty() Validation

1. Fetch `/properties` from each OSH server — record item count
2. For each property (or a sample of 3+ if many), take the raw JSON object
3. Feed through `parseProperty()` mentally (trace the code path) or via ad-hoc script:
   - Does it throw on the input? (should not)
   - Does `id` get extracted?
   - Does `label` / `description` get extracted?
   - Does `definition` get extracted?
   - Does `objectType` get extracted?
   - Are `links` present?
4. Record any fields in the live response that the parser silently discards
5. Test with 52N `/properties` if the endpoint exists

| Server | Resource ID | parseProperty throws? | Fields extracted | Fields discarded |
| ------ | ----------- | --------------------- | ---------------- | ---------------- |
| OSH    |             |                       |                  |                  |
| OS4    |             |                       |                  |                  |
| 52N    |             |                       |                  |                  |

##### 11c: parseDatastream() Validation

1. Fetch `/datastreams` from each OSH server — sample 3+ datastreams
2. For each, trace `parseDatastream()` against the raw JSON:
   - Does `outputName` get extracted?
   - Does `validTime` get parsed? (array format → `parseValidTime`)
   - Does `resultType` match a known value in `RESULT_TYPES`?
   - Does `observedProperties` get normalized by `normalizeObservedProperties()`?
   - Are `links` cast correctly?
   - Does `phenomenonTime` get extracted if present?
3. Test interval vs absent `validTime` across different datastreams
4. Record every unique `resultType` value seen — compare against the `RESULT_TYPES` set

| Server | DS ID | outputName | validTime format | resultType | observedProps count | links count |
| ------ | ----- | ---------- | ---------------- | ---------- | ------------------- | ----------- |
| OSH    |       |            |                  |            |                     |             |
| OS4    |       |            |                  |            |                     |             |

**resultType coverage (combined across all servers):**

| Live resultType value | In RESULT_TYPES set? | Parser result |
| --------------------- | -------------------- | ------------- |
|                       |                      |               |

##### 11d: parseObservation() Validation

1. Fetch observations from 3+ different datastreams on each OSH server
2. For each observation, trace `parseObservation()`:
   - Does `phenomenonTime` get extracted as a plain string? (instant, not interval)
   - Does `resultTime` get extracted?
   - Does `result` pass through opaquely?
   - Does `datastream@id` get extracted as `datastreamId`?
   - Are `links` optional and handled?
3. Verify `result` shapes vary by datastream (scalar, vector, record) and that the parser passes them through without alteration

| Server | DS ID | Obs ID | phenomenonTime format | result shape | datastreamId? | links? |
| ------ | ----- | ------ | --------------------- | ------------ | ------------- | ------ |
| OSH    |       |        |                       |              |               |        |
| OS4    |       |        |                       |              |               |        |

##### 11e: parseControlStream() Validation

1. Fetch `/controlstreams` from each OSH server — sample 3+ controlstreams
2. For each, trace `parseControlStream()`:
   - Does `inputName` get extracted?
   - Does `validTime` get parsed via `parseValidTime()`?
   - Are `controlledProperties` extracted?
   - Are `links` cast correctly?
3. Compare the response shape to `parseDatastream()` — they should be structurally similar

| Server | CS ID | inputName | validTime format | controlledProps count | links count |
| ------ | ----- | --------- | ---------------- | --------------------- | ----------- |
| OSH    |       |           |                  |                       |             |
| OS4    |       |           |                  |                       |             |

##### 11f: parseCommand() Validation

1. Fetch commands from 3+ controlstreams on each OSH server
2. For each command, trace `parseCommand()`:
   - Does `issueTime` get extracted as a plain string?
   - Does `parameters` get passed through opaquely?
   - Does `controlstream@id` get extracted as `controlstreamId`?
   - Are `links` optional and handled?
3. Compare parameters shapes across different controlstreams

| Server | CS ID | Cmd ID | issueTime format | parameters shape | controlstreamId? | links? |
| ------ | ----- | ------ | ---------------- | ---------------- | ---------------- | ------ |
| OSH    |       |        |                  |                  |                  |        |
| OS4    |       |        |                  |                  |                  |        |

##### 11g: parseCommandStatus() Validation

1. If any command status endpoints are accessible, fetch status records
2. Trace `parseCommandStatus()`:
   - Does `statusCode` get normalized via `normalizeStatusCode()`?
   - Is `executionStatus` extracted?
   - Is `progress` extracted (if present)?
   - Is `result` passed through (if present)?
3. Record all unique `statusCode` values seen — compare against `COMMAND_STATUS_CODES` set

| Server | Status ID | statusCode | normalizedCode | executionStatus | progress | result present? |
| ------ | --------- | ---------- | -------------- | --------------- | -------- | --------------- |
| OSH    |           |            |                |                 |          |                 |
| OS4    |           |            |                |                 |          |                 |

##### 11h: Cross-Server Parser Tolerance (3-Way)

1. For each Part 1 resource type, feed live JSON from ALL three servers through the same parser
2. For Part 2 resources, compare output from Server 1 (OSH) and Server 3 (OS4CSAPI-OSH)
3. Document any different field naming, nesting, or value formats across the three servers
4. Verify parsers handle all server shapes without throwing (Postel's Law tolerance)

If 52N Part 2 endpoints are still broken, document this and note that cross-server parser tolerance cannot be verified for Part 2 parsers against 52N.

---

#### Step 12: Helper Function Validation

Validate Phase 5 helper functions against live data from all applicable servers:

1. **`normalizeObservedProperties()`** — Feed live datastream `observedProperties` through the normalizer:
   - Test with object form: `{ "definition": "...", "label": "..." }`
   - Test with string form: `"http://..."`
   - Test with array of mixed forms (if seen in live data)
   - Record every unique form seen across all datastreams on all servers

2. **`normalizeStatusCode()`** — Feed live command status `statusCode` values:
   - Record all unique values across all servers
   - Verify mapping to canonical codes
   - Test any values not covered by unit test fixtures

3. **`RESULT_TYPES` set coverage** — Compare live `resultType` values against the set:
   - List all live values seen across all servers
   - Identify any live values NOT in the set (these would produce `null`)

4. **`COMMAND_STATUS_CODES` set coverage** — Same analysis for status codes

| Helper                          | Server | Input From Live | Expected Output | Actual/Traced Output | Match? |
| ------------------------------- | ------ | --------------- | --------------- | -------------------- | ------ |
| normalizeObservedProperties     | OSH    |                 |                 |                      |        |
| normalizeObservedProperties     | OS4    |                 |                 |                      |        |
| normalizeStatusCode             | OSH    |                 |                 |                      |        |
| normalizeStatusCode             | OS4    |                 |                 |                      |        |
| RESULT_TYPES membership         | OSH    |                 |                 |                      |        |
| RESULT_TYPES membership         | OS4    |                 |                 |                      |        |
| COMMAND_STATUS_CODES membership | OSH    |                 |                 |                      |        |
| COMMAND_STATUS_CODES membership | OS4    |                 |                 |                      |        |

---

#### Step 13: Recognition, Extraction, and Parsing Validation

**Carried forward from Phase 3/4 — these tests are NOT dropped.**

1. **`classifyFeature` recognition:** For each resource fetched in Steps 2–4, verify that the library's `classifyFeature` function correctly identifies the resource type from `featureType`
   - Test full URI forms (OSH servers)
   - Test CURIE forms (52N)
   - Test null featureType (52N systems)
   - Test misclassified featureType (52N procedure with `sosa:Sensor`)

2. **`parseValidTime` extraction:** For resources with `validTime`:
   - Array format: `["ISO", "now"]` (OSH servers)
   - Null value (52N)
   - Absent field (some OSH resources)
   - Verify the library handles all three cases without error

3. **Vocabulary inventory (3-way):** Record every unique `featureType` value across all three servers:

   | featureType Value | Server | Resource Type | Format |
   |-------------------|--------|---------------|--------|
   | | | | URI / CURIE / null |

4. **Content-Type availability matrix (3-way):**

   | Resource Type | OSH json | OSH geojson | OSH sml3 | 52N json | 52N geo+json | 52N sml+json | OS4 json | OS4 geojson | OS4 sml3 |
   |---------------|----------|-------------|----------|----------|--------------|-------------|----------|-------------|----------|
   | systems       |          |             |          |          |              |             |          |             |          |
   | deployments   |          |             |          |          |              |             |          |             |          |
   | procedures    |          |             |          |          |              |             |          |             |          |
   | etc.          |          |             |          |          |              |             |          |             |          |

---

#### Step 14: Schema Parsing Validation

For datastream and controlstream schemas from BOTH OSH servers:

1. Parse each schema with the library's SWE Common parser
2. Verify field names, types, and UOM extraction
3. Cross-reference observation `result` fields with schema field names
4. Test at least 3 datastream schemas and 3 controlstream schemas per server

---

#### Step 15: Cross-Server Comparison (3-Way)

Produce a comprehensive 3-way comparison table:

| Dimension                      | OpenSensorHub (S1) | 52North (S2) | OS4CSAPI-OSH (S3) | S1=S2? | S1=S3? | S2=S3? |
| ------------------------------ | ------------------ | ------------ | ------------------ | ------ | ------ | ------ |
| Conformance classes advertised |                    |              |                    |        |        |        |
| Discovery convention(s) used   |                    |              |                    |        |        |        |
| Default content type           |                    |              |                    |        |        |        |
| Content negotiation mechanism  |                    |              |                    |        |        |        |
| Response envelope format       |                    |              |                    |        |        |        |
| featureType vocabulary         |                    |              |                    |        |        |        |
| validTime format               |                    |              |                    |        |        |        |
| SensorML access method         |                    |              |                    |        |        |        |
| SensorML richness              |                    |              |                    |        |        |        |
| Part 2 endpoint availability   |                    |              |                    |        |        |        |
| Write operation support        |                    |              |                    |        |        |        |
| Sub-resource endpoint support  |                    |              |                    |        |        |        |
| SSL/TLS status                 |                    |              |                    |        |        |        |
| Auth requirement               |                    |              |                    |        |        |        |
| Parser compatibility (Part 2)  |                    |              |                    |        |        |        |
| sortBy/sortOrder support       |                    |              |                    |        |        |        |

---

#### Step 16: Phase 7 Bug-Fix & Security Verification (NEW)

This step verifies that the 7 key Phase 7 changes are correctly reflected in live server behavior. These are NOT re-tests of existing functionality — they target specific changes made in Phase 7.

##### 16a: Issue #140 — paramsSchema Fix

1. Fetch controlstream schemas from each OSH server
2. Check if any server returns `paramsSchema` instead of `commandSchema`
3. Verify the parser would now accept either field name
4. Record which field name each server uses

| Server | CS ID | Schema Field Name Used | Parser Would Accept? |
| ------ | ----- | --------------------- | ------------------- |
| OSH    |       |                       |                     |
| OS4    |       |                       |                     |

##### 16b: Issue #139 — getDeploymentSystems Deprecation

1. Attempt `GET /deployments/{id}/systems` on each server
2. Record the HTTP status — OGC 23-001 does NOT define this as a sub-resource endpoint
3. Confirm the deprecation was justified

| Server | URL Attempted | HTTP Status | Justification Confirmed? |
| ------ | ------------- | ----------- | ----------------------- |
| OSH    |               |             |                         |
| OS4    |               |             |                         |
| 52N    |               |             |                         |

##### 16c: Issue #100 — assertResourceAvailable Removal

1. Attempt to fetch a per-ID resource (e.g., `GET /systems/{id}`) on each server
2. Verify the library no longer throws before making the request (previously it would throw if the resource type wasn't discovered in the root document)
3. This is primarily a code-path verification — confirm that the URL builder doesn't pre-filter

Note: This cannot be directly tested via HTTP — it's a code behavior change. Verify by reviewing the Phase 7 commit that removed the guards, and confirm that per-ID URLs are constructed correctly for all 9 resource types.

##### 16d: Issue #102 — Nested Parent IDs for Command/Observation CRUD

1. On each OSH server, create a test observation using the nested path: `POST /datastreams/{dsId}/observations`
2. Read it back using BOTH:
   - Top-level: `GET /observations/{obsId}`
   - Nested: `GET /datastreams/{dsId}/observations/{obsId}` (if supported)
3. Repeat for commands: `POST /controlstreams/{csId}/commands` → read back both ways
4. Clean up: delete the test resources

| Resource    | Server | Nested POST Status | Top-Level GET | Nested GET | Same Resource? |
| ----------- | ------ | ------------------ | ------------- | ---------- | ------------- |
| Observation | OSH    |                    |               |            |               |
| Observation | OS4    |                    |               |            |               |
| Command     | OSH    |                    |               |            |               |
| Command     | OS4    |                    |               |            |               |

##### 16e: Issue #142 — subPath Encoding Verification

1. This is a code-level security fix — verify by constructing URLs with characters that need encoding
2. Test a system ID that contains special characters (if any exist on the servers)
3. If all system IDs are clean alphanumeric, note this and verify by code review that `encodeURIComponent` is applied to `subPath` segments

##### 16f: Issue #147 — URL Scheme Validation in scanCsapiLinks

1. Inspect the root API document links from all three servers
2. Record all URL schemes found (should all be `http://` or `https://`)
3. Verify that no non-HTTP schemes exist (if one did, the library would now reject it)
4. This is primarily a defensive security check — document the link schemes observed

| Server | Total Links | HTTP(S) Links | Non-HTTP Links | Schemes Found |
| ------ | ----------- | ------------- | -------------- | ------------- |
| OSH    |             |               |                |               |
| 52N    |             |               |                |               |
| OS4    |             |               |                |               |

##### 16g: Issue #161 — sortBy/sortOrder Query Parameters

(Cross-reference with Step 6 results)

1. Confirm that `sortBy` and `sortOrder` are correctly serialized into query strings
2. Test against each server — record whether the server:
   - Accepts and applies sorting (items returned in sorted order)
   - Accepts but ignores the parameter (items in default order)
   - Rejects with 400 (parameter not supported)
3. All three responses are acceptable server behaviors — document which applies

---

#### Step 17: Phase 7 DRY Refactor Confidence Check (NEW)

Phase 7 replaced 87 methods with the `build()` wrapper pattern. This step spot-checks that the refactored methods produce identical URLs and behavior.

1. For 5 randomly selected methods from different resource types, manually construct the expected URL
2. Compare against what the library's `build()` wrapper would produce
3. Verify no URL construction regressions (e.g., missing segments, wrong query parameter encoding)

| Method | Resource Type | Expected URL | Actual URL Tested | HTTP Status | Match? |
| ------ | ------------- | ------------ | ----------------- | ----------- | ------ |
|        |               |              |                   |             |        |
|        |               |              |                   |             |        |
|        |               |              |                   |             |        |
|        |               |              |                   |             |        |
|        |               |              |                   |             |        |

---

#### Step 18: Classify All New Findings

For each new finding (using **P7-F{N}** numbering), classify with:

- **ID:** P7-F{N}
- **Severity:** Critical / Moderate / Low / Informational
- **Category:** Code bug / Server limitation / Interoperability concern / Naming variation / Design gap / Parser gap / Security concern
- **Affects:** Which function or code path
- **Ownership:** "Ours" (our code needs a fix) / "Upstream" (server-side) / "Shared" (both)
- **Status:** Needs fix / Needs design decision / Informational / Deferred
- **Evidence:** What was observed (include request + response)

---

#### Step 19: Generate Impact Assessment

For any findings classified as "Ours" or "Shared":

1. Identify the specific file and function affected
2. Assess upstream impact (does the fix touch any upstream file?)
3. Estimate fix complexity (one-line, small, medium, architectural)
4. **For parser-related findings:** Indicate whether the unit test fixtures need updating to match live data shapes

---

#### Step 20: Present Findings to User

After completing Steps 1–19, present a summary to the user BEFORE writing the report file:

1. Quick verdict: pass/fail/conditional
2. Count of regression issues (if any)
3. Count of new findings by severity
4. CRUD test results summary (create/read/update/delete success rates per server)
5. **Parser validation summary** — parsers that passed, parsers with issues, fixture shape mismatches
6. **Phase 7 verification summary** — all 7 bug/security fixes verified? Any regressions?
7. **Server 3 discovery summary** — how does OS4CSAPI-OSH compare to Server 1?
8. **sortBy/sortOrder results** — which servers support it?
9. Any critical items requiring immediate attention
10. Ask: "Should I write the full report and commit it?"

---

### Report Format

Generate the report as a markdown file and save it to:
`docs/implementation/live-server-smoke-test-post-phase-7.md`

Use this exact structure:

```markdown
# Live Server Smoke Test — Post Phase 7

**Date:** {{YYYY-MM-DD}}
**Smoke Test Number:** ST#24
**Milestone:** After completing Phase 7 (Code Review Cleanup — 17 issues)
**Servers:** OpenSensorHub (S1), 52North (S2), OS4CSAPI-OSH (S3)
**Auth:** S1/S3: Basic auth required (credentials not stored in repo); S2: None (expired SSL cert)
**Purpose:** Full contribution validation + Phase 7 bug-fix/security-fix verification against 3 live servers
**Finding Series:** Phase 7 (P7-F1, P7-F2, ...)
**Template:** `docs/governance/smoke-test-prompt-template-phase-7.md` v1.0
**Test Baseline:** 1,339 CSAPI tests (30 suites), 0 tsc errors

> This is smoke test #24 in the series. See also:
>
> - [ST#23 — Phase 5.5](live-server-smoke-test-post-phase-5.5.md)
> - [ST#22 — Phase 5.3](live-server-smoke-test-post-phase-5.3.md)

## Test Methodology

Full contribution validation including all 9 resource types, all parsers, full CRUD on both OSH servers,
Phase 7 bug-fix and security-fix verification, sortBy/sortOrder query parameter testing, and first-contact
characterization of the OS4CSAPI-OSH server instance.

## Server Profiles

### Server 1: OpenSensorHub

| Spec Part | Conformance Classes |
| --------- | ------------------- |
| ...       | ...                 |

Resource Inventory: {{table with counts per endpoint}}
Top-level resource links: {{table}}

### Server 2: 52North

{{Same structure}}

### Server 3: OS4CSAPI-OSH (NEW)

{{Same structure + discovery notes section}}

## Results

### Prior Findings — Regression Check

| Finding | Original Phase | Status                      | Evidence |
| ------- | -------------- | --------------------------- | -------- |
| F1      | Phase 2        | Still Fixed ✅ / Changed ⚠️ | ...      |
| ...     | ...            | ...                         | ...      |

### URL Generation — All {{N}} Methods

#### {{Resource Type}} Methods

| Method Call | URL Pattern | OSH       | 52N       | OS4       |
| ----------- | ----------- | --------- | --------- | --------- |
| ...         | ...         | ✅/❌/N/A | ✅/❌/N/A | ✅/❌/N/A |

### Query Parameter Acceptance

| Parameter  | Method | URL | OSH   | 52N   | OS4   |
| ---------- | ------ | --- | ----- | ----- | ----- |
| sortBy     | ...    | ... | ✅/❌ | ✅/❌ | ✅/❌ |
| sortOrder  | ...    | ... | ✅/❌ | ✅/❌ | ✅/❌ |
| ...        | ...    | ... | ✅/❌ | ✅/❌ | ✅/❌ |

### Hierarchical Navigation

| Navigation | OSH | 52N | OS4 | Notes |
| ---------- | --- | --- | --- | ----- |
| ...        | ... | ... | ... | ...   |

### Part 2 — DataStreams & Observations (OSH + OS4)

{{Schema details, observation structure, temporal filtering results}}

### Part 2 — ControlStreams & Commands (OSH + OS4)

{{Schema details, command structure, status workflow}}

### SensorML Content Negotiation (3-Way)

| Aspect        | OSH     | 52N                          | OS4     |
| ------------- | ------- | ---------------------------- | ------- |
| Access method | ?f=sml3 | Accept: application/sml+json | ?f=sml3 |
| ...           | ...     | ...                          | ...     |

### CRUD Operations (OSH + OS4)

#### Create Results

| Resource Type | Server | POST Status | Location Header | Read-Back OK? |
| ------------- | ------ | ----------- | --------------- | ------------- |
| ...           | OSH    | ...         | ...             | ...           |
| ...           | OS4    | ...         | ...             | ...           |

#### Update Results

| Resource Type | Server | PUT Status | Change Verified? |
| ------------- | ------ | ---------- | ---------------- |
| ...           | ...    | ...        | ...              |

#### Delete Results

| Resource Type | Server | DELETE Status | 404 After Delete? | List Removed? |
| ------------- | ------ | ------------- | ----------------- | ------------- |
| ...           | ...    | ...           | ...               | ...           |

### Format Parser Validation

#### Fixture Shape Comparison (3-Way)

| Resource Type | Server | Live Fields | Fixture Fields | Extra in Live | Missing from Live |
| ------------- | ------ | ----------- | -------------- | ------------- | ----------------- |
| ...           | ...    | ...         | ...            | ...           | ...               |

#### Parser Results

| Parser             | Server | Resources Tested | Throws? | Fields Correct? | Issues Found |
| ------------------ | ------ | ---------------- | ------- | --------------- | ------------ |
| parseProperty      | OSH    |                  |         |                 |              |
| parseProperty      | OS4    |                  |         |                 |              |
| parseDatastream    | OSH    |                  |         |                 |              |
| parseDatastream    | OS4    |                  |         |                 |              |
| parseObservation   | OSH    |                  |         |                 |              |
| parseObservation   | OS4    |                  |         |                 |              |
| parseControlStream | OSH    |                  |         |                 |              |
| parseControlStream | OS4    |                  |         |                 |              |
| parseCommand       | OSH    |                  |         |                 |              |
| parseCommand       | OS4    |                  |         |                 |              |
| parseCommandStatus | OSH    |                  |         |                 |              |
| parseCommandStatus | OS4    |                  |         |                 |              |

#### Helper Function Validation

| Helper                      | Server | Live Inputs Tested | All Mapped Correctly? | Uncovered Values |
| --------------------------- | ------ | ------------------ | --------------------- | ---------------- |
| normalizeObservedProperties | OSH    |                    |                       |                  |
| normalizeObservedProperties | OS4    |                    |                       |                  |
| normalizeStatusCode         | OSH    |                    |                       |                  |
| normalizeStatusCode         | OS4    |                    |                       |                  |
| RESULT_TYPES                | both   |                    |                       |                  |
| COMMAND_STATUS_CODES        | both   |                    |                       |                  |

#### Cross-Server Parser Tolerance (3-Way)

{{Results of feeding responses from all 3 servers through parsers}}

### Recognition, Extraction, and Parsing

{{classifyFeature results (3 servers), parseValidTime results, vocabulary inventory (3-way)}}

### Schema Parsing Validation (OSH + OS4)

{{SWE Common parser results for datastream and controlstream schemas from both servers}}

### Phase 7 Bug-Fix Verification

| Issue | Fix Description | Verification Method | OSH Result | OS4 Result | Verified? |
| ----- | --------------- | ------------------- | ---------- | ---------- | --------- |
| #140  | paramsSchema fallback | Schema field name check | | | |
| #139  | getDeploymentSystems deprecation | HTTP status check | | | |
| #100  | assertResourceAvailable removal | Code review + URL test | | | |
| #102  | Nested parent IDs | Nested CRUD cycle | | | |
| #142  | subPath encoding | URL construction review | | | |
| #147  | URL scheme validation | Link scheme audit | | | |
| #161  | sortBy/sortOrder | Query parameter test | | | |

### Phase 7 DRY Refactor Confidence Check

| Method | Expected URL | Actual URL | Match? |
| ------ | ------------ | ---------- | ------ |
| ...    | ...          | ...        | ...    |

## New Findings

### P7-F1 ({{Severity}}): {{Title}}

**Severity:** {{Critical/Moderate/Low/Informational}}
**Category:** {{Code bug / Server limitation / Interoperability concern / Parser gap / Security concern}}
**Affects:** {{function/file}}
**Ownership:** {{Ours / Upstream / Shared}}
**Evidence:** {{What was observed}}
**Status:** {{Needs fix / Deferred / Informational}}

## Cross-Server Comparison (3-Way)

| Dimension | OpenSensorHub | 52North | OS4CSAPI-OSH | S1=S2? | S1=S3? |
| --------- | ------------- | ------- | ------------ | ------ | ------ |
| ...       | ...           | ...     | ...          | ✅/❌  | ✅/❌  |

## Server 3 (OS4CSAPI-OSH) — First-Contact Discovery Notes

{{Dedicated section capturing everything learned about the new server:
  - Conformance profile
  - Content negotiation behavior
  - Available resources and counts
  - Differences from Server 1
  - Any unique quirks discovered
  - Part 2 endpoint availability
  - Write operation support
}}

## What WORKS (Verified)

| Capability | Status |
| ---------- | ------ |
| ...        | ✅     |

## CRUD Summary (2-Server)

| Operation | Systems | Deployments | Procedures | SFs | Datastreams | Observations | ControlStreams | Commands |
| --------- | ------- | ----------- | ---------- | --- | ----------- | ------------ | -------------- | -------- |
| Create    |         |             |            |     |             |              |                |          |
| Read      |         |             |            |     |             |              |                |          |
| Update    |         |             |            |     |             |              |                |          |
| Delete    |         |             |            |     |             |              |                |          |

## Parser Validation Summary

| Parser             | OSH Compatible? | OS4 Compatible? | 52N Compatible? | Fixture Shapes Accurate? | Issues |
| ------------------ | --------------- | --------------- | --------------- | ------------------------ | ------ |
| parseProperty      |                 |                 |                 |                          |        |
| parseDatastream    |                 |                 | N/A             |                          |        |
| parseObservation   |                 |                 | N/A             |                          |        |
| parseControlStream |                 |                 | N/A             |                          |        |
| parseCommand       |                 |                 | N/A             |                          |        |
| parseCommandStatus |                 |                 | N/A             |                          |        |

## Phase 7 Verification Summary

| Category | Issues | All Verified? |
| -------- | ------ | ------------- |
| Bug fixes | #140, #139, #100, #102, #111 | ✅/❌ |
| Security fixes | #142, #147 | ✅/❌ |
| New features | #161 (sortBy/sortOrder) | ✅/❌ |
| DRY refactors | #145 (build() wrapper), #146, #149, #150 | ✅/❌ |
| Type safety | #141, #143, #144, #148 | ✅/❌ |
| Test cleanup | #151 | ✅/❌ |

## What Remains

| Issue | Severity | Component | Target |
| ----- | -------- | --------- | ------ |
| ...   | ...      | ...       | ...    |

## Comparison: Phase 5.5 (ST#23) → Phase 7 (ST#24)

| Dimension           | Phase 5.5 (ST#23) | Phase 7 (ST#24) |
| ------------------- | ------------------ | --------------- |
| Test baseline       | 1,283 / 29 suites | 1,339 / 30 suites |
| Servers tested      | 2                  | 3               |
| Methods implemented | 91+                | 91+             |
| CRUD tested         | Yes (1 server)     | Yes (2 servers) |
| Parsers validated   | 6 parsers          | 6 parsers       |
| sortBy/sortOrder    | N/A                | Tested          |
| Phase 7 fixes       | N/A                | 7 verified      |
| Findings total      | {{N}}              | {{N}}           |

## Verdict

{{3-4 paragraph assessment:
- Do all prior findings remain stable (no regressions)?
- Are all Phase 7 bug fixes and security fixes verified against live servers?
- Did the DRY refactor (build() wrapper) introduce any URL regressions?
- Do the sortBy/sortOrder parameters work correctly?
- How does Server 3 (OS4CSAPI-OSH) compare to Server 1?
- Parser validation results across 3 servers
- CRUD success rates across 2 write-capable servers
- Any critical items?
- Ready for clean-pr merge and upstream submission?
}}
```

Then commit the report, push, and confirm the file is at the expected path.

If any new findings are classified as "Ours — Needs fix", create a GitHub issue for each using `docs/governance/issue-creation-prompt-template-code-review.md`.

````

---

## Post-Smoke-Test Workflow

After the smoke test report is generated:

1. **Review new findings** — decide which are "fix now" vs "defer"
2. **Create GitHub issues** for "Ours — Needs fix" findings using `docs/governance/issue-creation-prompt-template-code-review.md`
3. **Complete fix issues** before proceeding to upstream submission
4. **Update `known-server-quirks.md`** if new server behavior is discovered (especially for Server 3)
5. **Update unit test fixtures** if live data shape mismatches are discovered
6. **Add Server 3 quirks** to the known-server-quirks document based on first-contact findings
7. **Update the cross-server interoperability analysis** with 3-way comparison data
8. **The smoke test report is the final gate** before merging to `clean-pr`

---

## Critical Rules (Non-Negotiable)

- [ ] **Read `known-server-quirks.md` FIRST** — Before issuing any HTTP request, read the full server quirks document. Prevents re-discovering known issues.
- [ ] **All THREE servers tested** — Every step that involves HTTP requests MUST hit all three servers (except Part 2 on 52N, which is known broken). Single-server testing missed real bugs in prior smoke tests.
- [ ] **Credentials not in repo** — The username and password for OSH and OS4CSAPI-OSH are NEVER committed to the repository, NEVER written into any file, and NEVER included in the report. If you don't have them, ask the user.
- [ ] **52North needs `-SkipCertificateCheck`** — Every PowerShell command to the 52North server MUST include this flag due to the expired SSL certificate.
- [ ] **All prior findings re-checked** — The regression check section must cover EVERY finding from EVERY prior smoke test, not just the most recent one.
- [ ] **New findings get P7-F numbering** — Phase 7 findings use `P7-F1`, `P7-F2`, etc. Do not continue the P5-F series.
- [ ] **New findings get ownership classification** — Every new finding must be classified as "Ours", "Upstream", or "Shared" with evidence.
- [ ] **Only delete what you create** — CRUD testing creates test data and deletes ONLY that data. Never delete pre-existing resources. Record every created resource ID in the cleanup table.
- [ ] **Create before you test** — Don't rely on finding existing resources for CRUD testing. Create your own test data, use it, then clean up.
- [ ] **Record every HTTP request** — For CRUD operations, record the full request (method, URL, headers, body) and full response (status, headers, body or summary).
- [ ] **Content-Type matters for writes** — Part 1 POST/PUT uses `application/geo+json`. Part 2 POST/PUT uses `application/json`. Getting this wrong returns 400/415.
- [ ] **Test exhaustively** — Test every capability the library exposes, not just what the demo UI exercises. If the library has a method, test it against a live server.
- [ ] **Document Accept headers / `?f=` used** — For every request, record which content negotiation method was used.
- [ ] **Validate parsers against live data** — Every implemented parser MUST be traced against at least 2 real server responses from each applicable server.
- [ ] **Compare fixture shapes to live data** — Every parser's unit test fixture shapes MUST be compared against actual server response shapes. Document any mismatches.
- [ ] **Phase 7 verification is mandatory** — Step 16 (bug-fix verification) MUST be completed. It is NOT optional. Every Phase 7 change must be verified against at least one live server.
- [ ] **Server 3 first-contact protocol** — Server 3 has never been tested before. Perform thorough discovery (Step 2, items 7–12) before running the standard test suite against it. Document ALL unique behaviors.
- [ ] **NEVER use `Accept: application/json` for 52N** — Returns empty collections. Use `Accept: application/geo+json` or `Accept: application/sml+json`.
- [ ] **OSH servers use `?f=` not Accept headers** — Both Server 1 and Server 3 are OpenSensorHub instances and likely ignore Accept headers. Use `?f=json`, `?f=geojson`, or `?f=sml3`.
- [ ] **Only delete what you create — on EACH server** — The cleanup table tracks resources created on each server separately. Delete only YOUR test resources.

---

## Naming Convention

Reports follow these naming patterns:

```
docs/implementation/live-server-smoke-test-post-phase-{X}.md — Standard post-phase smoke test
docs/implementation/live-server-smoke-test-{server-name}.md  — New server comparative test
docs/implementation/cross-server-interoperability-analysis.md — Cross-server synthesis
docs/implementation/live-server-retest-post-issues-{N}-{M}.md — Targeted retest after fixes
```

---

## Changes from Phase 5 Template

| Aspect                  | Phase 5           | Phase 7                                                                                            |
| ----------------------- | ----------------- | -------------------------------------------------------------------------------------------------- |
| Servers                 | 2 (OSH + 52N)     | **3** (OSH + 52N + OS4CSAPI-OSH)                                                                   |
| Finding numbers         | P5-F1, P5-F2...   | P7-F1, P7-F2... (new series)                                                                       |
| Query parameters tested | 12 params         | **14+ params** (+sortBy, +sortOrder)                                                               |
| Phase 7 verification    | N/A               | **Dedicated steps 16–17** (7 bug/security fixes + DRY refactor confidence)                         |
| Server 3 first-contact  | N/A               | **Exploratory discovery** with dedicated report section                                            |
| Test baseline           | 1,283 / 29 suites | **1,339 / 30 suites**                                                                              |
| Required reading        | 8 documents       | **10 documents**                                                                                   |
| Steps                   | 18                | **20** (+Phase 7 verification, +DRY confidence check)                                              |
| CRUD testing            | 1 server (OSH)    | **2 servers** (OSH + OS4CSAPI-OSH)                                                                 |
| Cross-server comparison | 2-way             | **3-way**                                                                                          |
| Critical rules          | 15 rules          | **20 rules** (+3-server testing, +Phase 7 mandatory, +Server 3 first-contact, +per-server cleanup) |
| Fixture comparison      | 2-server          | **3-server**                                                                                       |
| Parser validation       | 2-server          | **3-server**                                                                                       |
| Post-workflow           | 7 items           | **8 items** (+Server 3 quirks documentation)                                                       |

---

## Server Quick Reference

| Property             | OpenSensorHub (S1)                             | 52North (S2)                                           | OS4CSAPI-OSH (S3)                                |
| -------------------- | ---------------------------------------------- | ------------------------------------------------------ | ------------------------------------------------ |
| URL                  | `http://45.55.99.236:8080/sensorhub/api`       | `https://csa.demo.52north.org/`                        | `https://os4csapi-osh.duckdns.org/sensorhub/api` |
| Auth                 | Basic (⚠️ ask user for credentials)            | None                                                   | Basic (⚠️ ask user for credentials)              |
| SSL                  | HTTP (no SSL issues)                           | HTTPS (expired cert — use `-SkipCertificateCheck`)     | HTTPS (valid cert — no special handling)         |
| Conformance          | 20+ CSAPI classes                              | Zero CSAPI classes                                     | TBD (first contact)                              |
| Content negotiation  | `?f=` query parameter (Accept headers ignored) | `Accept` header (routes to different backends)         | Likely `?f=` (confirm during test)               |
| Default content type | `application/json`                             | `application/sml+json`                                 | TBD (first contact)                              |
| Part 1 resources     | ✅ All work                                    | ✅ systems, deployments, procedures (SFs empty)        | TBD (first contact)                              |
| Part 2 resources     | ✅ All work                                    | ❌ All broken (500/400/404)                            | TBD (first contact)                              |
| Write operations     | ✅ Full CRUD                                   | ❓ Not tested                                          | TBD (first contact)                              |
| SML access           | `?f=sml3`                                      | `Accept: application/sml+json`                         | Likely `?f=sml3` (confirm during test)           |
| Response envelope    | `{items}` or `{FeatureCollection}`             | `{items}` or `{FeatureCollection}` depending on Accept | TBD (first contact)                              |
| Parser testable?     | ✅ All parsers                                 | ⚠️ Part 1 only (Part 2 broken)                         | TBD (first contact — expect full)                |
| Previously tested?   | ✅ ST#1–ST#23                                  | ✅ ST#1–ST#23                                          | ❌ First contact in ST#24                        |
