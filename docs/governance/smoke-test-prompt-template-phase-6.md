# Phase 6 — Architecture Verification Test Prompt Template

**Purpose:** Reusable prompt for triggering comprehensive architecture verification of Phase 6 (Upstream Acceptance Refactoring) work. The primary focus is **module boundary isolation, export completeness, build correctness, and bundle independence** (Steps 1–12). A focused **live server regression check** (Step 13) is included to confirm the restructuring introduced no runtime regressions against either server. The CSAPI business logic is unchanged; what changed is how it's packaged and accessed.

**Version:** 1.1  
**Date:** February 24, 2026  
**Supersedes:** v1.0 of this template (added Step 13 live server regression)  
**Sibling:** `smoke-test-prompt-template-phase-5.md` (Phase 5) remains the authoritative template for exhaustive parser validation and full CRUD testing.  
**Report destination:** `docs/implementation/phase-6-architecture-verification.md`

---

## Why "Architecture Verification" Instead of "Smoke Test"?

Phase 5 smoke tests validated **runtime behavior** — parsers producing correct typed output from real server JSON. Phase 6 changes **zero runtime behavior**. It restructures the integration boundary (imports, exports, entry points). The primary validation is structural, not behavioral — but a focused live server regression step (Step 13) provides end-to-end confidence that the restructuring breaks nothing at runtime:

| Dimension            | Phase 5 Smoke Test                            | Phase 6 Architecture Verification                                                                                |
| -------------------- | --------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| What's tested        | Parser correctness against live data          | Module boundary isolation and build correctness + **focused live server regression**                             |
| Requires servers     | Yes (OSH + 52North)                           | Steps 1–12: No (entirely local). **Step 13: Yes (OSH + 52North)**                                                |
| HTTP requests        | 100+ per test                                 | Steps 1–12: Zero. **Step 13: ~20–30 focused requests**                                                           |
| Primary tool         | `Invoke-RestMethod`                           | `git grep`, `npx tsc`, `npm run test`, `node --conditions`, **`Invoke-RestMethod` (Step 13)**                    |
| Risk being mitigated | Parsers disagree with real server data        | Consumer imports break, bundle includes unwanted code, TypeScript resolution fails, **packaging breaks runtime** |
| Success criteria     | All parsers handle all server response shapes | All 12 verification gates pass, litmus test passes, consumer simulation succeeds, **no live server regressions** |

All Phase 5 smoke test findings (F1–F90, P4-F1–F5, P5-F\*) remain valid and unchanged — Phase 6 did not modify any parser, URL builder, or format handler behavior. Step 13 spot-checks a representative sample of those findings to confirm continuity.

---

## When to Use

Trigger this prompt after:

1. **Commit 15 is complete** (Phase B architecture refactoring done)
2. **Before Task 10b** (pushing to `clean-pr` / upstream) — this is the final gate
3. **After any fix to a Phase 6 code review finding** — re-verify the fix didn't break isolation
4. **Before updating PR #136** — full verification before jahow sees the changes

Do NOT trigger after Phase A (formatting only) — formatting changes cannot break boundaries. Do NOT trigger for doc-only changes.

---

## How to Use

Copy the **Prompt** section below and paste it into the conversation after completing Phase B work. Replace all `{{...}}` placeholders with actual values.

---

## Prompt

````
Please perform a Phase 6 architecture verification test of the module boundary refactoring.

### Scope

**Phase:** 6
**Commits to verify:** {{Commit 14 SHA}} (formatting), {{Commit 15 SHA}} (architecture)
**Last review:** {{Reference the previous review doc, or "none — first Phase 6 verification"}}

### Required Reading — BEFORE Starting

Read these documents IN FULL before running any verification commands:

| Document | Location | Purpose |
|----------|----------|---------|
| P6 Contribution Goal | `docs/planning/phase-6/P6-contribution-goal-and-definition.md` | 12 acceptance criteria — the source of truth for pass/fail |
| P6 Implementation Guide | `docs/planning/phase-6/P6-implementation-guide.md` | Complete file specifications — what each file should contain |
| P6 ROADMAP | `docs/planning/phase-6/P6-ROADMAP.md` | Task definitions and verification gates |
| AI Operational Constraints | `docs/governance/AI_OPERATIONAL_CONSTRAINTS.md` | Behavioral boundaries |
| Previous Code Review | `docs/implementation/phase-{prev}-code-review.md` | Prior findings and open items |
| Known Server Quirks | `docs/governance/known-server-quirks.md` | **CRITICAL for Step 13** — All known server behaviors, content negotiation rules |
| Previous Smoke Test | `docs/implementation/live-server-smoke-test-post-phase-{prev}.md` | Prior findings for Step 13e regression check |

### Test Instructions

Follow this exact sequence. Record EVERYTHING — every command, every output, every observation.

---

#### Step 1: Pre-Verification State Check

Before running any verification, establish the starting state:

1. Confirm current branch: `git branch --show-current` → expect `phase-6`
2. Confirm clean working tree: `git status` → expect "nothing to commit"
3. Record HEAD commit: `git log --oneline -3`
4. Record commit diff stats:
   ```bash
   # Commit 14 (formatting)
   git diff --stat HEAD~1..HEAD    # if HEAD is Commit 15
   git diff --stat HEAD~2..HEAD~1  # Commit 14 only

   # Commit 15 (architecture)
   git diff --stat HEAD~1..HEAD    # architecture only
````

5. Verify exactly 7 files changed in Commit 15:
   - 3 created: `csapi/index.ts`, `csapi/factory.ts`, `csapi/factory.spec.ts`
   - 4 modified: `endpoint.ts`, `index.ts`, `endpoint.spec.ts`, `package.json`

---

#### Step 2: Boundary Verification (V1–V4)

Run all 4 boundary gates. Every one must return 0 matches.

| #   | Gate                                 | Command                                                                    | Expected  |
| --- | ------------------------------------ | -------------------------------------------------------------------------- | --------- |
| V1  | Endpoint has zero CSAPI imports      | `git grep "from.*csapi" src/ogc-api/endpoint.ts`                           | 0 matches |
| V2  | Root index has zero CSAPI references | `git grep "csapi\|CSAPI" src/index.ts`                                     | 0 matches |
| V3  | No cross-module CSAPI imports        | `git grep "import.*from.*csapi" -- "src/" ":!src/ogc-api/csapi/"`          | 0 matches |
| V4  | No non-index CSAPI imports           | `git grep "from.*csapi" -- "src/" ":!src/ogc-api/csapi/" ":!src/index.ts"` | 0 matches |

**Record:** For each gate, record the exact command run and the output (including "no matches" if clean).

**If any gate fails:** Stop. Record the failing matches. This is a blocking issue that must be fixed before continuing.

---

#### Step 3: CI Compliance (C1–C5)

Run all 5 upstream CI gates. Every one must pass.

```bash
npm run format:check    # C1 — Prettier
npm run typecheck        # C2 — TypeScript
npm run lint             # C3 — ESLint
npm run test:browser     # C4 — Browser test suite
npm run test:node        # C5 — Node test suite
```

**Record for each gate:**

- Exit code (0 = pass)
- For C4: total passing tests, total suites, any failures
- For C5: total passing tests, any failures
- Note any pre-existing issues (e.g., `@types/node` errors, WMTS/WFS timeouts)

**Expected baseline (from Phase 5):**

- C4: 1,282+ tests passing, 29+ suites
- C5: All non-browser tests passing

**If any gate fails:** Record the full error output. Determine if it's a pre-existing issue or a Phase 6 regression.

---

#### Step 4: Litmus Test (A4) — Core Independence

This is the critical test: does the core library compile and pass tests WITHOUT the CSAPI module?

```bash
# 1. Backup CSAPI
mv src/ogc-api/csapi src/ogc-api/_csapi_backup

# 2. Verify core compiles
npx tsc --noEmit 2>&1 | head -50
# Expected: Compiles cleanly (ignore errors that reference only csapi/ paths)
# If endpoint.ts has zero csapi imports, it should compile fine

# 3. Verify root index has no broken references
# (All CSAPI exports were removed in Task 7 — index.ts should be self-contained)

# 4. Restore CSAPI
mv src/ogc-api/_csapi_backup src/ogc-api/csapi

# 5. Verify restoration is clean
npx tsc --noEmit
```

**Record:**

- Compilation result with CSAPI removed
- Any errors that appear (expected: zero from core files)
- Compilation result after restoration (must be clean)

**If core doesn't compile without CSAPI:** This means there's still a dependency from core → CSAPI. Record the exact error and which file has the import.

---

#### Step 5: Export Completeness Audit

Verify that the barrel file re-exports every symbol that was previously in `src/index.ts`:

1. **Count symbols in barrel file:**

   ```bash
   git grep "export " src/ogc-api/csapi/index.ts | wc -l
   ```

2. **Count CSAPI symbols removed from root index:**

   ```bash
   git diff HEAD~1..HEAD -- src/index.ts | grep "^-export" | wc -l
   # or if Commit 15 is HEAD:
   git diff HEAD~1..HEAD -- src/index.ts | grep "^-" | grep -v "^---" | wc -l
   ```

3. **Cross-reference:** Every CSAPI symbol removed from `src/index.ts` must appear in `src/ogc-api/csapi/index.ts`.

4. **Verify barrel sections** — the barrel file should have 6 organized sections:

   - [ ] Factory function (`createCSAPIBuilder`)
   - [ ] Query builder (`CSAPIQueryBuilder` and related)
   - [ ] Model values (enums, constants)
   - [ ] Model types (interfaces)
   - [ ] Format handler values (parser functions)
   - [ ] Format handler types (format interfaces)

5. **Verify `export type` correctness:** Type-only exports must use `export type { ... }`, value exports must use `export { ... }`.

**Record:** Symbol count from barrel vs symbols removed from root index. Flag any mismatches.

---

#### Step 6: Factory Function Verification

1. **Verify factory function signature:**

   ```bash
   git grep "createCSAPIBuilder" src/ogc-api/csapi/factory.ts
   ```

   Expected: `async function createCSAPIBuilder(endpoint, collectionId)`

2. **Verify factory uses type-only endpoint import:**

   ```bash
   git grep "import type.*endpoint\|import type.*Endpoint" src/ogc-api/csapi/factory.ts
   ```

   Expected: `import type OgcApiEndpoint` (type-only — erased at compile)

3. **Verify factory tests exist and pass:**

   ```bash
   npm run test:browser -- --testPathPattern factory
   ```

   Expected: 2 tests passing (builder creation + error case)

4. **Verify factory is re-exported from barrel:**
   ```bash
   git grep "createCSAPIBuilder" src/ogc-api/csapi/index.ts
   ```
   Expected: Appears in an `export { ... }` statement

---

#### Step 7: Package.json Verification

1. **Verify sub-path export exists:**

   ```bash
   node -e "const pkg = require('./package.json'); console.log(JSON.stringify(pkg.exports['./csapi'], null, 2))"
   ```

   Expected: `types`, `import`, `browser`, `default` conditions pointing to `dist/ogc-api/csapi/index.*`

2. **Verify `"types"` is first condition:**
   Inspect `package.json` — `"types"` must appear before `"import"` in the `"./csapi"` object.

3. **Verify `sideEffects` declaration:**

   ```bash
   node -e "const pkg = require('./package.json'); console.log(pkg.sideEffects)"
   ```

   Expected: `false`

4. **Verify existing exports unchanged:**
   ```bash
   node -e "const pkg = require('./package.json'); console.log(Object.keys(pkg.exports))"
   ```
   Expected: `.`, `./worker`, `./csapi` (3 entries — first two unchanged)

---

#### Step 8: Consumer Import Simulation

Simulate how a real consumer would import from both entry points:

1. **Core import (should have zero CSAPI):**

   ```bash
   # Check that the root index.ts has no CSAPI references
   node -e "
     const fs = require('fs');
     const content = fs.readFileSync('src/index.ts', 'utf-8');
     const csapiLines = content.split('\n').filter(l => /csapi/i.test(l));
     console.log('CSAPI lines in root index:', csapiLines.length);
     if (csapiLines.length > 0) csapiLines.forEach(l => console.log('  ', l.trim()));
   "
   ```

   Expected: 0 CSAPI lines

2. **CSAPI import (should resolve all symbols):**

   ```bash
   # Verify barrel file compiles independently
   npx tsc --noEmit src/ogc-api/csapi/index.ts
   ```

   Expected: Clean compilation

3. **Verify the consumer API migration pattern works:**
   ```
   // Old: import { CSAPIQueryBuilder } from '@camptocamp/ogc-client'
   // New: import { CSAPIQueryBuilder } from '@camptocamp/ogc-client/csapi'
   // Verify the new path resolves all previously-available symbols
   ```

---

#### Step 9: Diff Review

Review the actual changes to confirm they match the Implementation Guide specifications:

1. **Commit 14 diff summary:**

   ```bash
   git diff --stat HEAD~2..HEAD~1  # Formatting only
   ```

   - Expected: ~51 files changed, ~3,023 insertions, minimal deletions
   - Verify: Zero logic changes — only whitespace and import removal

2. **Commit 15 diff summary:**

   ```bash
   git diff --stat HEAD~1..HEAD    # Architecture only
   ```

   - Expected: Exactly 7 files (3 created, 4 modified)
   - Expected net change: ~+5 lines (excluding the 3 new files)

3. **Verify no unexpected files changed:**
   ```bash
   git diff --name-only HEAD~2..HEAD
   ```
   - All files should be in: `src/ogc-api/csapi/`, `src/ogc-api/endpoint.ts`, `src/index.ts`, `src/ogc-api/endpoint.spec.ts`, `package.json`, `fixtures/ogc-api/csapi/`

---

#### Step 10: Acceptance Criteria Matrix

Fill in the complete 12-gate acceptance matrix from the [Contribution Goal](../planning/phase-6/P6-contribution-goal-and-definition.md):

| #   | Category     | Criterion                       | Verification           | Result |
| --- | ------------ | ------------------------------- | ---------------------- | ------ |
| A1  | Architecture | Zero CSAPI in `index.ts`        | `git grep`             | ✅/❌  |
| A2  | Architecture | `"./csapi"` sub-path in exports | Inspect `package.json` | ✅/❌  |
| A3  | Architecture | Zero outward CSAPI imports      | `git grep`             | ✅/❌  |
| A4  | Architecture | Core compiles without CSAPI     | Litmus test            | ✅/❌  |
| C1  | CI           | Prettier passes                 | `npm run format:check` | ✅/❌  |
| C2  | CI           | TypeScript compiles             | `npm run typecheck`    | ✅/❌  |
| C3  | CI           | ESLint passes                   | `npm run lint`         | ✅/❌  |
| C4  | CI           | Browser tests pass              | `npm run test:browser` | ✅/❌  |
| C5  | CI           | Node tests pass                 | `npm run test:node`    | ✅/❌  |
| B1  | Behavioral   | `hasConnectedSystems` works     | Existing test passes   | ✅/❌  |
| B2  | Behavioral   | `csapiCollections` works        | Existing test passes   | ✅/❌  |
| B3  | Behavioral   | All non-CSAPI unchanged         | Full test suite passes | ✅/❌  |

**All 12 gates must be ✅ for the verification to pass.**

---

#### Step 11: Classify All Findings

For each issue discovered during verification, classify with:

- **ID:** P6-V{N} (P6-V1, P6-V2, etc.)
- **Severity:** Blocking / Moderate / Low / Informational
- **Category:** Boundary violation / Export gap / Build error / Test regression / Configuration issue
- **Gate affected:** Which of the 12 acceptance criteria it blocks
- **Evidence:** Command run and actual output
- **Status:** Needs fix / Informational

---

#### Step 12: Present Results to User

After completing Steps 1–11, present a summary:

1. **Quick verdict:** PASS (all 12 gates green + no live server regressions) / FAIL (list failing gates or regressions)
2. **Gate scorecard:** 12/12 ✅, or N/12 with failures listed
3. **Litmus test result:** Core compiles without CSAPI? Yes/No
4. **Export completeness:** All symbols accounted for? Yes/No
5. **Factory function:** Tests pass? Yes/No
6. **Any findings?** Count by severity
7. **Ready for Step 13?** If all structural gates pass, proceed to live server regression.
8. Ask: "Should I proceed to Step 13 (live server regression)?"

After completing Step 13, present the live server regression summary:

9. **Live server verdict:** PASS / FAIL
10. **Server connectivity:** Both reachable? Yes/No
11. **Parser regression:** All spot-checked parsers correct? Yes/No
12. **CRUD regression:** Create/read/delete cycle successful? Yes/No
13. **Prior findings stable?** Any status changes? Yes/No
14. **Ready for Task 10b (push to upstream)?** Yes/No/Conditional
15. Ask: "Should I write the full report and commit it?"

---

#### Step 13: Live Server Regression Verification

Phase 6 changed zero runtime behavior — parsers, URL builders, and CRUD methods are identical to Phase 5. This step confirms that the restructured imports and packaging introduced no runtime regression. It is NOT a full Phase 5 smoke test; it is a focused confidence check against both live servers.

**⚠️ CREDENTIAL REMINDER:** OSH requires Basic authentication. If you do not have the credentials from prior conversation context, you MUST ask the user before proceeding. Credentials are NEVER committed to the repository.

##### 13a: Server Connectivity

For EACH server, verify the root API is reachable and returns the expected structure:

| Server | URL                                      | Auth                             | Command Pattern                                                            |
| ------ | ---------------------------------------- | -------------------------------- | -------------------------------------------------------------------------- |
| OSH    | `http://45.55.99.236:8080/sensorhub/api` | Basic (ask user for credentials) | `Invoke-RestMethod -Uri "..." -Headers @{ Authorization = "Basic $cred" }` |
| 52N    | `https://csa.demo.52north.org/`          | None                             | `Invoke-RestMethod -Uri "..." -SkipCertificateCheck`                       |

For each server, record:

- HTTP status (expect 200)
- `links` array present and non-empty
- Key link relations visible (e.g., `systems`, `deployments`, `conformance`)

Then fetch `/conformance` from each server — record conformance class count.

##### 13b: Resource Inventory Regression

For EACH server, fetch the resource inventory and compare against the most recent Phase 5 smoke test baseline:

| Endpoint          | Accept / `?f=`  | OSH P5 Count | OSH Now | 52N P5 Count | 52N Now | Changed? |
| ----------------- | --------------- | ------------ | ------- | ------------ | ------- | -------- |
| /systems          | OSH: `?f=json`  | {{prev}}     |         | {{prev}}     |         |          |
|                   | 52N: `geo+json` |              |         |              |         |          |
| /deployments      |                 | {{prev}}     |         | {{prev}}     |         |          |
| /procedures       |                 | {{prev}}     |         | {{prev}}     |         |          |
| /samplingFeatures |                 | {{prev}}     |         | {{prev}}     |         |          |
| /properties       |                 | {{prev}}     |         | N/A          | N/A     |          |
| /datastreams      |                 | {{prev}}     |         | N/A          | N/A     |          |
| /observations     |                 | {{prev}}     |         | N/A          | N/A     |          |
| /controlstreams   |                 | {{prev}}     |         | N/A          | N/A     |          |
| /commands         |                 | {{prev}}     |         | N/A          | N/A     |          |

**Notes:**

- Count changes are expected (data is live and servers may have new resources). Failures to reach endpoints are NOT expected — those indicate a regression.
- 52N Part 2 endpoints are expected to be broken (500/400/404) — this is a known server limitation, not a regression.
- **NEVER use `Accept: application/json` for 52N** — it returns empty collections. Use `Accept: application/geo+json`.
- OSH ignores Accept headers — use `?f=json` or `?f=geojson` query parameter.

##### 13c: Parser Regression Spot-Check

Validate at least 2 Part 1 and 2 Part 2 parsers against live data to confirm they still produce correct output. This is a spot-check, not the exhaustive Phase 5 parser validation.

**Part 1 — Both servers:**

1. Fetch 1 system from OSH (`?f=json`) and 1 from 52N (`Accept: application/geo+json`)
2. Trace through `classifyFeature()` — does it still return the correct resource type from `featureType`?
3. Trace through `parseValidTime()` if `validTime` is present — does it handle the server's format (array for OSH, null for 52N)?

**Part 2 — OSH only (52N Part 2 is all broken):**

4. Fetch 1 datastream from OSH — trace through `parseDatastream()`:
   - `outputName`, `validTime`, `resultType`, `observedProperties`, `links` extracted correctly?
5. Fetch 1 observation from OSH — trace through `parseObservation()`:
   - `phenomenonTime`, `resultTime`, `result`, `datastreamId` extracted correctly?

| Parser           | Server | Resource ID | Throws? | Output Correct? | Regression? |
| ---------------- | ------ | ----------- | ------- | --------------- | ----------- |
| classifyFeature  | OSH    |             |         |                 |             |
| classifyFeature  | 52N    |             |         |                 |             |
| parseValidTime   | OSH    |             |         |                 |             |
| parseValidTime   | 52N    |             |         |                 |             |
| parseDatastream  | OSH    |             |         |                 |             |
| parseObservation | OSH    |             |         |                 |             |

**If any parser throws or produces incorrect output, this is a potential Phase 6 regression.** Investigate immediately — Phase 6 should not have changed any parser behavior.

##### 13d: CRUD Smoke Cycle (OSH Only)

Perform a minimal create → read → delete cycle to confirm write operations still work through the restructured module:

1. **Create** a test system:

   ```powershell
   $body = '{"type":"Feature","properties":{"featureType":"http://www.w3.org/ns/sosa/Sensor","name":"P6-smoke-test-temp","description":"Temporary Phase 6 regression test — will be deleted"},"geometry":null}'
   Invoke-RestMethod -Method Post -Uri "http://45.55.99.236:8080/sensorhub/api/systems" -Headers $headers -ContentType "application/geo+json" -Body $body
   ```

   Record: HTTP status (expect 201), Location header → extract new system ID

2. **Read** it back: `GET /systems/{id}` — verify 200, correct `name` and `featureType`

3. **Delete** it: `DELETE /systems/{id}` — verify 204

4. **Confirm deletion**: `GET /systems/{id}` — verify 404

| Operation                 | HTTP Status | Expected | Regression? |
| ------------------------- | ----------- | -------- | ----------- |
| POST /systems             |             | 201      |             |
| GET /systems/{id}         |             | 200      |             |
| DELETE /systems/{id}      |             | 204      |             |
| GET /systems/{id} (after) |             | 404      |             |

**⚠️ Only delete what you create. Do NOT delete pre-existing data.**

**⚠️ Do NOT include an `Accept` header on POST requests to OSH** — this is a known quirk.

**⚠️ PUT requires `uid` in the body on OSH** — but this cycle skips update for brevity. A full CRUD cycle with update is in the Phase 5 template.

##### 13e: Prior Findings Quick Regression

Reference the most recent smoke test report and spot-check **at least 5** representative prior findings. Select findings that cover different categories:

| Finding | Category                 | Original Status | Current Status | Evidence |
| ------- | ------------------------ | --------------- | -------------- | -------- |
| {{id}}  | Code bug                 | {{status}}      |                |          |
| {{id}}  | Server limitation        | {{status}}      |                |          |
| {{id}}  | Interoperability concern | {{status}}      |                |          |
| {{id}}  | Parser gap               | {{status}}      |                |          |
| {{id}}  | Naming variation         | {{status}}      |                |          |

Prior finding series to check:

- **F1–F90** (Phase 2/3 findings)
- **P4-F1–P4-F5** (Phase 4 findings)
- **P5-F\*** (Phase 5 findings)

**Any finding whose status changed since the last smoke test is a potential Phase 6 regression and must be investigated.** Phase 6 changed zero runtime behavior, so status changes are unexpected.

##### 13f: Live Server Regression Verdict

After completing Steps 13a–13e, provide a live server regression verdict:

1. **Server connectivity:** Both servers reachable? Yes/No
2. **Resource inventory:** Endpoints still respond? Yes/No
3. **Parser spot-check:** All parsers produce correct output? Yes/No
4. **CRUD cycle:** Create/read/delete successful? Yes/No
5. **Prior findings:** Any status changes detected? Yes/No
6. **Overall regression verdict:** PASS (no regressions) / FAIL (regressions found)

---

### Report Format

Generate the report as a markdown file and save it to:
`docs/implementation/phase-6-architecture-verification.md`

Use this exact structure:

```markdown
# Phase 6 Architecture Verification

**Date:** {{YYYY-MM-DD}}
**Verifier:** GitHub Copilot (Claude Opus 4.6)
**Branch:** phase-6
**Commits verified:**

- `{sha}` — Commit 14: `style(csapi): apply prettier formatting and fix eslint errors`
- `{sha}` — Commit 15: `refactor(csapi): decouple from endpoint with separate entry point`

## Pre-Verification State

| Property        | Value               |
| --------------- | ------------------- |
| Branch          | phase-6             |
| HEAD            | {{SHA}}             |
| Working tree    | Clean               |
| Commit 14 files | {{N}} files changed |
| Commit 15 files | {{N}} files changed |

## Acceptance Criteria Matrix

| #   | Category     | Criterion              | Command/Method | Expected | Actual     | Status |
| --- | ------------ | ---------------------- | -------------- | -------- | ---------- | ------ |
| A1  | Architecture | Zero CSAPI in index.ts | git grep       | 0        | {{N}}      | ✅/❌  |
| A2  | Architecture | ./csapi sub-path       | Inspect pkg    | Present  | {{Y/N}}    | ✅/❌  |
| A3  | Architecture | Zero outward imports   | git grep       | 0        | {{N}}      | ✅/❌  |
| A4  | Architecture | Core compiles alone    | Litmus test    | Clean    | {{result}} | ✅/❌  |
| C1  | CI           | Prettier               | format:check   | exit 0   | {{result}} | ✅/❌  |
| C2  | CI           | TypeScript             | typecheck      | exit 0   | {{result}} | ✅/❌  |
| C3  | CI           | ESLint                 | lint           | exit 0   | {{result}} | ✅/❌  |
| C4  | CI           | Browser tests          | test:browser   | all pass | {{N}} pass | ✅/❌  |
| C5  | CI           | Node tests             | test:node      | all pass | {{N}} pass | ✅/❌  |
| B1  | Behavioral   | hasConnectedSystems    | test pass      | ✅       | {{result}} | ✅/❌  |
| B2  | Behavioral   | csapiCollections       | test pass      | ✅       | {{result}} | ✅/❌  |
| B3  | Behavioral   | Non-CSAPI unchanged    | full suite     | ✅       | {{result}} | ✅/❌  |

**Result: {{N}}/12 gates passing**

## Boundary Verification Detail

### V1: Endpoint CSAPI Imports
```

$ git grep "from.\*csapi" src/ogc-api/endpoint.ts
{{output or "no matches"}}

```

### V2: Root Index CSAPI References
```

$ git grep "csapi\|CSAPI" src/index.ts
{{output or "no matches"}}

```

### V3: Cross-Module CSAPI Imports
```

$ git grep "import.*from.*csapi" -- "src/" ":!src/ogc-api/csapi/"
{{output or "no matches"}}

```

### V4: Non-Index CSAPI Imports
```

$ git grep "from.\*csapi" -- "src/" ":!src/ogc-api/csapi/" ":!src/index.ts"
{{output or "no matches"}}

```

## Litmus Test (Core Independence)

{{Full output of the backup → compile → restore sequence}}

## Export Completeness Audit

| Section | Symbol Count | Verified |
|---------|-------------|----------|
| Factory function | {{N}} | ✅/❌ |
| Query builder | {{N}} | ✅/❌ |
| Model values | {{N}} | ✅/❌ |
| Model types | {{N}} | ✅/❌ |
| Format handler values | {{N}} | ✅/❌ |
| Format handler types | {{N}} | ✅/❌ |
| **Total** | **{{N}}** | |

Symbols removed from root index: {{N}}
Symbols in barrel file: {{N}}
Match: ✅/❌

## Factory Function Verification

- Signature correct: ✅/❌
- Type-only endpoint import: ✅/❌
- Tests passing: ✅/❌ ({{N}} tests)
- Re-exported from barrel: ✅/❌

## Package.json Verification

- `"./csapi"` sub-path: ✅/❌
- `"types"` first: ✅/❌
- Paths correct: ✅/❌
- `"sideEffects": false`: ✅/❌
- Existing exports intact: ✅/❌

## Consumer Import Simulation

- Root index has 0 CSAPI references: ✅/❌
- Barrel compiles independently: ✅/❌

## Diff Review

### Commit 14 (Formatting)
{{diffstat output}}
- Files changed: {{N}}
- Logic changes: Zero ✅/Detected ❌

### Commit 15 (Architecture)
{{diffstat output}}
- Files changed: {{N}} (expected: 7)
- New files: {{list}}
- Modified files: {{list}}

## Findings

### P6-V{{N}} ({{Severity}}): {{Title}}
**Category:** {{Boundary violation / Export gap / Build error / Live server regression / ...}}
**Gate affected:** {{A1/A2/.../B3/R1–R5}}
**Evidence:** {{command and output}}
**Status:** {{Needs fix / Informational}}

## Live Server Regression Results

### Server Connectivity

| Server | HTTP Status | Links Count | Conformance Classes |
| ------ | ----------- | ----------- | ------------------- |
| OSH    |             |             |                     |
| 52N    |             |             |                     |

### Resource Inventory (vs Phase 5 Baseline)

| Endpoint          | OSH P5 | OSH Now | 52N P5 | 52N Now | Regression? |
| ----------------- | ------ | ------- | ------ | ------- | ----------- |
| /systems          |        |         |        |         |             |
| /deployments      |        |         |        |         |             |
| /procedures       |        |         |        |         |             |
| /samplingFeatures |        |         |        |         |             |
| /properties       |        |         | N/A    | N/A     |             |
| /datastreams      |        |         | N/A    | N/A     |             |
| /observations     |        |         | N/A    | N/A     |             |
| /controlstreams   |        |         | N/A    | N/A     |             |
| /commands         |        |         | N/A    | N/A     |             |

### Parser Spot-Check

| Parser             | Server | Resource ID | Throws? | Output Correct? | Regression? |
| ------------------ | ------ | ----------- | ------- | --------------- | ----------- |
| classifyFeature    | OSH    |             |         |                 |             |
| classifyFeature    | 52N    |             |         |                 |             |
| parseDatastream    | OSH    |             |         |                 |             |
| parseObservation   | OSH    |             |         |                 |             |

### CRUD Smoke Cycle (OSH)

| Operation                 | HTTP Status | Expected | Regression? |
| ------------------------- | ----------- | -------- | ----------- |
| POST /systems             |             | 201      |             |
| GET /systems/{id}         |             | 200      |             |
| DELETE /systems/{id}      |             | 204      |             |
| GET /systems/{id} (after) |             | 404      |             |

### Prior Findings Regression

| Finding | Category | Original Status | Current Status | Changed? |
| ------- | -------- | --------------- | -------------- | -------- |
|         |          |                 |                |          |

### Live Server Regression Verdict

- Server connectivity: ✅/❌
- Resource inventory: ✅/❌
- Parser spot-check: ✅/❌
- CRUD cycle: ✅/❌
- Prior findings stable: ✅/❌
- **Overall: PASS / FAIL**

## Verdict

{{2-3 paragraph assessment:
- Do all 12 structural gates pass?
- Is the module boundary clean?
- Are exports complete?
- Is the factory function correct?
- Is the consumer API migration viable?
- Did the live server regression check pass?
- Any prior findings that changed status?
- Ready for Task 10b (push to clean-pr)?
}}
```

Then commit the report, push, and confirm the file is at the expected path.

```

---

## Post-Verification Workflow

After the verification report is generated:

1. **If all 12 structural gates pass AND live server regression passes:** Proceed to Task 10b (rebase to `clean-pr`, push to upstream)
2. **If any structural gate fails:** Create a fix issue using `docs/governance/issue-creation-prompt-template-phase-6.md`, fix the issue, then re-run verification
3. **If live server regression fails:** Investigate immediately — Phase 6 changed zero runtime behavior, so regressions indicate a packaging/import issue. Fix before proceeding.
4. **Update the code review** if the verification found issues not caught in code review
5. **The verification report is the final gate** before pushing to upstream — it proves to jahow that all requirements are met

---

## Critical Rules (Non-Negotiable)

- [ ] **All 12 acceptance criteria checked** — no "probably passes" allowed; every gate must be explicitly run and recorded
- [ ] **Litmus test MUST be executed** — the core-compiles-without-CSAPI test is the single most important verification. Do not skip it.
- [ ] **Export completeness verified** — every CSAPI symbol removed from `src/index.ts` must appear in `csapi/index.ts`. Count and compare.
- [ ] **Factory tests pass** — both tests (builder creation + error case) must pass
- [ ] **Zero boundary violations** — V1–V4 must all return 0 matches. Any match is a blocking failure.
- [ ] **Commit 14 has zero logic changes** — the formatting commit must be purely mechanical. If any logic change is detected, it must be moved to Commit 15.
- [ ] **Commit 15 touches exactly 7 files** — 3 created + 4 modified. Any additional file changes are scope creep.
- [ ] **Record every command and output** — the verification report is evidence for jahow. It must be reproducible.
- [ ] **Findings get P6-V numbering** — Phase 6 verification findings use `P6-V1`, `P6-V2`, etc.
- [ ] **OSH credentials not in repo** — The OpenSensorHub username and password are NEVER committed to the repository, NEVER written into any file, and NEVER included in the report. If you don't have them, ask the user.
- [ ] **52North needs `-SkipCertificateCheck`** — Every PowerShell command to the 52North server MUST include this flag due to the expired SSL certificate.
- [ ] **NEVER use `Accept: application/json` for 52N** — Returns empty collections. Use `Accept: application/geo+json` or `Accept: application/sml+json`.
- [ ] **OSH uses `?f=` not Accept headers** — OSH ignores Accept headers entirely. Use `?f=json`, `?f=geojson`, or `?f=sml3`.
- [ ] **Only delete what you create** — The CRUD smoke cycle creates a test resource and deletes ONLY that resource. Never delete pre-existing data.
- [ ] **Prior findings regression is mandatory** — At least 5 prior findings from different categories must be spot-checked. Any status change is a potential Phase 6 regression.
- [ ] **Read `known-server-quirks.md` before Step 13** — Before issuing any HTTP request, read the server quirks document to avoid re-discovering known issues.

---

## Relationship to Phase 5 Smoke Tests

Phase 6 architecture verification does NOT replace Phase 5 smoke tests. Steps 1–12 are structural; Step 13 is a focused regression spot-check. For exhaustive parser validation, full CRUD testing, or new-feature validation, use the Phase 5 template.

| Concern                                               | Validated By                                                        |
| ----------------------------------------------------- | ------------------------------------------------------------------- |
| Parsers produce correct output from live server data  | Phase 5 smoke test (exhaustive) / **Step 13c** (spot-check)        |
| URL builder generates correct URLs                    | Phase 5 smoke test                                                  |
| CRUD operations work against live servers             | Phase 5 smoke test (full cycle) / **Step 13d** (create-read-delete) |
| Module boundary is clean                              | **Steps 1–12** (this template)                                      |
| Bundle isolation works                                | **Steps 1–12** (this template)                                      |
| Consumer imports resolve                              | **Steps 1–12** (this template)                                      |
| CI pipeline passes                                    | **Steps 1–12** (this template)                                      |
| Server connectivity regression                        | **Step 13a** (this template)                                        |
| Resource inventory regression                         | **Step 13b** (this template)                                        |
| Prior findings stability                              | Phase 5 smoke test (full) / **Step 13e** (5-finding spot-check)     |

If a full Phase 5 smoke test is needed after Phase 6, use `smoke-test-prompt-template-phase-5.md` — it remains fully valid since Phase 6 changed zero runtime behavior.

---

## Server Quick Reference

| Property              | OpenSensorHub                                    | 52North                                                             |
| --------------------- | ------------------------------------------------ | ------------------------------------------------------------------- |
| URL                   | `http://45.55.99.236:8080/sensorhub/api`         | `https://csa.demo.52north.org/`                                     |
| Auth                  | Basic (⚠️ ask user for credentials)              | None                                                                |
| SSL                   | HTTP (no SSL issues)                             | HTTPS (expired cert — use `-SkipCertificateCheck`)                  |
| Conformance           | 20+ CSAPI classes                                | Zero CSAPI classes                                                  |
| Content negotiation   | `?f=` query parameter (Accept headers ignored)   | `Accept` header (routes to different backends)                      |
| Default content type  | `application/json`                               | `application/sml+json`                                              |
| Part 1 resources      | ✅ All work                                       | ✅ systems, deployments, procedures (SFs empty)                      |
| Part 2 resources      | ✅ All work                                       | ❌ All broken (500/400/404)                                          |
| Write operations      | ✅ Full CRUD                                      | ❓ Not tested                                                        |
| SML access            | `?f=sml3`                                        | `Accept: application/sml+json`                                      |
| Response envelope     | `{items}` or `{FeatureCollection}`               | `{items}` or `{FeatureCollection}` depending on Accept              |
| Parser testable?      | ✅ All parsers                                    | ⚠️ Part 1 only (Part 2 broken)                                      |
```
