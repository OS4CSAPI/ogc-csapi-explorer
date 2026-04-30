# Phase 7: Code Review Cleanup — Plan

**Version:** 1.3
**Date:** March 7, 2026
**Status:** Ready for Execution
**Scope:** Resolve 17 open issues (11 code-review findings + 6 pre-existing bugs) across 20 execution passes

---

## Executive Summary

This plan covers the execution of **Phase 7: Code Review Cleanup** — resolving all actionable findings from the senior developer's code review of the `clean-pr` draft PR (#136) plus 6 pre-existing open issues that overlap with the same files. The work is organized into **6 sequential phases (20 execution passes)** and resolves **17 issues total** (with #111 auto-resolved by #160 at zero extra cost).

**Issue splits for safe single-pass execution** (see `P7-scope-split-assessment.md`):

- #141 → #154 + #155 (2 parts: core impl + integration test call sites)
- #100 → #156 + #157 (2 parts: 33 methods + 39 methods)
- #145 → #158 + #159 + #160 (3 parts: 33 + 25 + 29 methods)

**What this covers:**

- 11 code-review findings (#141–#151) identified by the senior developer
- 6 pre-existing open issues (#98, #100, #102, #111, #139, #140) bundled because they affect the same files
- Type safety fixes, DRY refactors, security hardening, test cleanup

**What this does NOT cover:**

- Upstream-only findings 001, 002, 005, and 006 (tracked in `docs/code-review/upstream-findings-report.md`)
- Issue #110 (new `@link` resolution utilities — deferred, see `docs/code-review/110-deferred-enhancement-link-resolution-utilities.md`)
- Any changes to upstream code we did not author

**Key constraints:**

- All changes must be within `src/ogc-api/csapi/` (upstream isolation requirement per jahow's PR #136 comment)
  - Exception: #141 touches `endpoint.ts` (upstream file we modified) — minimal diff only
- Zero public API signature changes unless explicitly required by the issue

---

## Two-Repo Workflow

This work spans two repositories with different purposes:

| Repository                    | Branch                    | Purpose                                                     |
| ----------------------------- | ------------------------- | ----------------------------------------------------------- |
| `OS4CSAPI/ogc-client-CSAPI_2` | `phase-7` (off `phase-6`) | Development — full context, granular commits, planning docs |
| `OS4CSAPI/ogc-client`         | `clean-pr`                | PR delivery — squashed commit for upstream review           |

### Workflow Steps

**Step 1: Branch in CSAPI_2**

Create a `phase-7` branch off `phase-6` in the development repo. Execute all 20 steps here with one commit per step. This repo has all planning docs, governance files, test infrastructure, and fixture data for full-context development.

**Step 2: Validate in CSAPI_2**

After all 20 steps pass the per-phase validation gates, run the full suite:

- `tsc --noEmit` — zero type errors
- `npm test` — all tests pass
- `npm run lint` — zero lint errors
- `npx prettier --check src/` — all files formatted

The `phase-7` branch now has a complete, validated implementation with full commit history for our audit trail.

**Step 3: Generate source-only diff**

Extract only the `src/` and `fixtures/` changes as a patch — excluding all `docs/` planning artifacts that don't belong in the upstream PR:

```bash
git diff phase-6..phase-7 -- src/ fixtures/ > phase-7-cleanup.patch
```

**Step 4: Apply to `clean-pr` on ogc-client**

Switch to the `ogc-client` fork. Apply the patch to `clean-pr` as a single squashed commit:

```bash
cd ../ogc-client
git checkout clean-pr
git apply ../ogc-client-CSAPI_2/phase-7-cleanup.patch
git add -A
git commit -m "fix: address code review findings (17 issues)

- Type safety: validate parseCollectionResponse elements, null-check
  extractCSAPIFeature properties, replace SensorML raw JSON spread
- DRY: extract parseBaseStream/requireObject helpers in part2.ts,
  add build() wrapper in url_builder.ts (resolves getCommandStatus
  concatenation), delegate createCommands to createCommand
- Security: encode subPath in buildResourceUrl, validate URL schemes
  in scanCsapiLinks
- Bugs: fix paramsSchema data loss, fix getDeploymentSystems URL,
  remove overly strict assertResourceAvailable from per-ID methods,
  add nested parent IDs for command/observation CRUD
- Tests: extract shared integration test fixture factory"
```

**Step 5: Push and verify**

Push `clean-pr` to update PR #136. Run CI once more on the PR branch. The PR diff now includes the cleanup as part of the contribution.

```bash
git push origin clean-pr
```

### Why This Approach

- **Full context during development** — governance docs, planning, all 20 issue descriptions are in CSAPI_2
- **Granular history preserved** — `phase-7` branch keeps per-step commits for our audit trail
- **Clean PR presentation** — camptocamp sees one focused commit, not 20 incremental ones
- **No risk to existing PR** — `clean-pr` is untouched until everything passes in CSAPI_2

### Pre-requisite: Verify `src/` sync

Before starting, confirm that `phase-6` in CSAPI_2 and `clean-pr` in ogc-client have identical `src/` content. If Phase 6 was applied to both, the patch ports cleanly. If they've diverged, reconcile first.

- All tests must pass after each step
- Review `docs/governance/AI_OPERATIONAL_CONSTRAINTS.md` before starting implementation

---

## Issue Inventory

### Code Review Findings (must fix)

| #    | Finding                                                              | Category               | Primary File                 | Severity |
| ---- | -------------------------------------------------------------------- | ---------------------- | ---------------------------- | -------- |
| #141 | `parseCollectionResponse` casts raw JSON to `T[]` without validation | Type Safety            | `endpoint.ts`                | P1       |
| #142 | `subPath` appended without encoding or type constraint               | Type Safety + Security | `url_builder.ts`             | P2       |
| #143 | `extractCSAPIFeature` casts `properties` without null check          | Type Safety            | `geojson.ts`                 | P2       |
| #144 | SensorML parsers spread raw JSON into typed results                  | Type Safety            | `sensorml.ts`                | P2       |
| #145 | `assertResourceAvailable()` + `buildResourceUrl()` repeated 90×      | DRY / Architecture     | `url_builder.ts`             | P2       |
| #146 | `parseDatastream` / `parseControlStream` ~30 lines duplicated        | DRY / Architecture     | `part2.ts`                   | P2       |
| #147 | `scanCsapiLinks()` no URL scheme validation                          | Security               | `helpers.ts`                 | P3       |
| #148 | Redundant `as Record` casts after `isRecord` narrowing               | Code Quality           | `parser.ts`, `data-array.ts` | P3       |
| #149 | Null-guard + cast boilerplate duplicated 5×                          | Code Quality           | `part2.ts`                   | P3       |
| #150 | `createCommand()` / `createCommands()` byte-identical                | DRY                    | `url_builder.ts`             | P3       |
| #151 | Collection fixture factory duplicated in 4 test files                | Code Quality           | `integration/*.spec.ts`      | P3       |

### Pre-existing Issues (bundled — same files)

| #    | Title                                                        | Category      | Primary File     | Why Include                               |
| ---- | ------------------------------------------------------------ | ------------- | ---------------- | ----------------------------------------- |
| #98  | `parseCommandStatus` `@see` link precision (F18)             | Documentation | `part2.ts`       | Same file as #146, #149; trivial          |
| #100 | `assertResourceAvailable()` overly strict for per-ID methods | Bug           | `url_builder.ts` | Must precede #158; split into #156 + #157 |
| #102 | Command/observation CRUD need nested parent IDs              | Bug           | `url_builder.ts` | Must precede #158                         |
| #111 | `getCommandStatus()` string concatenation (F45)              | Bug           | `url_builder.ts` | Auto-resolved by #160                     |
| #139 | `getDeploymentSystems()` builds non-standard URL             | Bug           | `url_builder.ts` | Same file; independent fix                |
| #140 | `parseControlStreamSchemaResponse()` drops `paramsSchema`    | Bug           | `part2.ts`       | Same file; data loss bug                  |

### Excluded

| #    | Title                                              | Reason             | Details                                                                      |
| ---- | -------------------------------------------------- | ------------------ | ---------------------------------------------------------------------------- |
| 001  | Path traversal via unencoded `itemId`              | Upstream-only (P1) | See `docs/code-review/upstream-findings-report.md`                           |
| 002  | Query param injection via `encodeURI`              | Upstream-only (P1) | See `docs/code-review/upstream-findings-report.md`                           |
| 005  | `OgcApiEndpoint` accepts `http://` without warning | Upstream-only (P2) | See `docs/code-review/upstream-findings-report.md`                           |
| 006  | Full `error` object logged — may expose API keys   | Upstream-only (P2) | See `docs/code-review/upstream-findings-report.md`                           |
| #110 | `@link` / `@id` resolution utilities               | New functionality  | See `docs/code-review/110-deferred-enhancement-link-resolution-utilities.md` |

### Issue Splits

Three issues were split into smaller passes for safe single-pass execution (see `P7-scope-split-assessment.md`):

| Parent | Split Into                                                | Rationale                                                                                                                                                                                                      |
| ------ | --------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| #141   | **#154** (Part 1) + **#155** (Part 2)                     | Part 1: core `parseItem` callback impl + unit tests (`response.ts`); Part 2: ~35–40 integration test call site updates (~5 spec files)                                                                         |
| #100   | **#156** (Part 1) + **#157** (Part 2)                     | Part 1: Systems/Deployments/Procedures/SamplingFeatures (33 methods); Part 2: Properties/Datastreams/Observations/ControlStreams/Commands (39 methods)                                                         |
| #145   | **#158** (Part 1) + **#159** (Part 2) + **#160** (Part 3) | Part 1: `build()` helper + Systems/Deployments/Procedures (33 methods); Part 2: SamplingFeatures/Properties/Datastreams (25 methods); Part 3: Observations/ControlStreams/Commands (29 methods, resolves #111) |

Parent issues (#141, #100, #145) are marked `[SPLIT]` on GitHub and reference their child issues.

---

## Execution Plan

### Phase A: Zero-Risk Quick Wins

Low-risk changes that build confidence and establish that the test suite is green.

#### Step 1 — Issue #98: Fix `@see` link precision in `parseCommandStatus`

- **File:** `src/ogc-api/csapi/formats/part2.ts`
- **Action:** Update JSDoc `@see` reference to point to the correct spec section
- **Risk:** None — documentation only
- **Validation:** `npm run lint`, visual inspection

#### Step 2 — Issue #148: Remove redundant `as Record` casts in SWE Common parsers

- **Files:** `src/ogc-api/csapi/formats/swecommon/parser.ts`, `src/ogc-api/csapi/formats/swecommon/data-array.ts`
- **Action:** Delete 27 redundant `as Record<string, unknown>` casts that follow `isRecord()` / `isLinkReference()` narrowing
- **Risk:** None — TypeScript has already narrowed the types
- **Validation:** `tsc --noEmit`, `npm test`

---

### Phase B: `part2.ts` Batch (Parser Cleanup)

All changes in a single file. Run tests once at the end of the batch.

#### Step 3 — Issue #149: Extract `requireObject` helper

- **File:** `src/ogc-api/csapi/formats/part2.ts`
- **Action:** Create private `requireObject(json, fn)` function; replace 5 inline null-guard + cast blocks with one-liner calls
- **Risk:** None — identical behavior, just consolidated
- **Validation:** `npm test`

#### Step 4 — Issue #146: Extract `parseBaseStream` helper

- **File:** `src/ogc-api/csapi/formats/part2.ts`
- **Action:** Create private `parseBaseStream(fn, json)` extracting 7 shared fields (`id`, `name`, `description`, `validTime`, `formats`, `systemId`, `links`); update `parseDatastream()` and `parseControlStream()` to spread `base` and add only resource-specific fields
- **Risk:** Low — internal refactor, no public API change
- **Depends on:** Step 3 (null guard now in `requireObject`, called by `parseBaseStream`)
- **Validation:** `npm test`

#### Step 5 — Issue #140: Fix `paramsSchema` data loss

- **File:** `src/ogc-api/csapi/formats/part2.ts`
- **Action:** Update `parseControlStreamSchemaResponse()` to accept `paramsSchema` (alias used by older OSH servers) in addition to `commandSchema`
- **Risk:** Low — additive, handles a field that was previously silently dropped
- **Validation:** `npm test` + manual check against OSH server response fixture

---

### Phase C: Type Safety Fixes (Steps 6–9)

Fixes across separate files. Each step can be validated independently.

#### Step 6 — Issue #154: Implement `parseItem` callback in `parseCollectionResponse` (Part 1 of #141)

- **Files:** `src/ogc-api/csapi/formats/response.ts`, `src/ogc-api/csapi/formats/response.spec.ts`
- **Action:** Implement `parseItem` callback parameter in `parseCollectionResponse`; add unit tests for element validation
- **Risk:** Low — new parameter, backward-compatible
- **Validation:** `npm test`

#### Step 7 — Issue #155: Update integration test call sites for `parseCollectionResponse` (Part 2 of #141)

- **Files:** ~5 spec files under `src/ogc-api/csapi/`
- **Action:** Update ~35–40 call sites to pass the `parseItem` callback introduced in Step 6
- **Risk:** Low — mechanical, no behavioral change
- **Depends on:** Step 6 (#154)
- **Validation:** `npm test`

#### Step 8 — Issue #143: Add null check to `extractCSAPIFeature`

- **File:** `src/ogc-api/csapi/formats/geojson.ts`
- **Action:** Add null/type check before casting `feature.properties` to `Record<string, unknown>`
- **Risk:** Low — defensive guard, no behavioral change for valid input
- **Validation:** `npm test`

#### Step 9 — Issue #144: Fix SensorML raw JSON spread

- **File:** `src/ogc-api/csapi/formats/sensorml.ts`
- **Action:** Replace `...json` spread (which passes through all raw JSON properties unfiltered) with explicit field extraction for each typed property
- **Risk:** Low-Medium — more invasive change, but isolated to one file
- **Validation:** `npm test` + review output against SensorML fixtures

---

### Phase D: `url_builder.ts` Batch — The Big One (Steps 10–18)

This is the highest-value, highest-effort batch. The dependency chain is: #142 → #139 → #156 → #157 → #102 → #158 → #159 → #160 → #150. Each step builds on the previous.

#### Step 10 — Issue #142: Encode/constrain `subPath` in `buildResourceUrl`

- **File:** `src/ogc-api/csapi/url_builder.ts`
- **Action:** Add type constraint or encoding to the `subPath` parameter in `buildResourceUrl()` to prevent unencoded `/`-delimited strings from being injected
- **Risk:** Low — fixes the foundation before refactoring callers
- **Validation:** `npm test`

#### Step 11 — Issue #139: Fix `getDeploymentSystems()` non-standard URL

- **File:** `src/ogc-api/csapi/url_builder.ts`
- **Action:** Fix URL construction — `deployedSystems` is an inline GeoJSON property, not a sub-resource endpoint per OGC 23-001 Table 43
- **Risk:** Low — independent bug fix
- **Validation:** `npm test`

#### Step 12 — Issue #156: Remove `assertResourceAvailable` — Part 1 of #100

- **File:** `src/ogc-api/csapi/url_builder.ts`
- **Action:** Remove `assertResourceAvailable()` guard from 33 per-ID methods: Systems (14) + Deployments (7) + Procedures (6) + SamplingFeatures (6)
- **Risk:** Medium — changes behavior for callers who relied on the guard. However, the guard was always incorrect for these methods.
- **Validation:** `npm test`

#### Step 13 — Issue #157: Remove `assertResourceAvailable` — Part 2 of #100

- **File:** `src/ogc-api/csapi/url_builder.ts`
- **Action:** Remove `assertResourceAvailable()` guard from 39 per-ID methods: Properties (5) + Datastreams (9) + Observations (7) + ControlStreams (9) + Commands (9)
- **Risk:** Medium — same systematic pattern as Step 12
- **Depends on:** Step 12 (#156) — same systematic pattern, split for safe pass size
- **Validation:** `npm test`

#### Step 14 — Issue #102: Add nested parent ID parameters

- **File:** `src/ogc-api/csapi/url_builder.ts`
- **Action:** Add optional parent ID parameters to command/observation CRUD methods so they can construct nested URLs (e.g., `/controlstreams/{csId}/commands/{cmdId}`)
- **Risk:** Medium — extends method signatures (backward-compatible — new optional params)
- **Must precede:** Steps 15–17 (#158/#159/#160) — finalizes the method signatures before wrapping in `build()`
- **Validation:** `npm test`

#### Step 15 — Issue #158: Add `build()` wrapper — Part 1 of #145

- **File:** `src/ogc-api/csapi/url_builder.ts`
- **Action:** Create private `build(resourceType, id?, subPath?, options?)` method that fuses `assertResourceAvailable()` and `buildResourceUrl()`. Rewrite Systems (16) + Deployments (9) + Procedures (8) = 33 methods to use `build()`
- **Risk:** Medium — mechanical, but large scope per pass
- **Depends on:** Steps 12–14 (#156, #157, #102)
- **Validation:** `npm test`

#### Step 16 — Issue #159: `build()` wrapper — Part 2 of #145

- **File:** `src/ogc-api/csapi/url_builder.ts`
- **Action:** Rewrite SamplingFeatures (8) + Properties (6) + Datastreams (11) = 25 methods to use `build()`
- **Risk:** Medium — same mechanical pattern
- **Depends on:** Step 15 (#158) — `build()` helper exists
- **Validation:** `npm test`

#### Step 17 — Issue #160: `build()` wrapper — Part 3 of #145 (resolves #111)

- **File:** `src/ogc-api/csapi/url_builder.ts`
- **Action:** Rewrite Observations (8) + ControlStreams (11) + Commands (10) = 29 methods to use `build()`. Auto-resolves #111 (`getCommandStatus()` concatenation deviation disappears when rewritten to use `build()`)
- **Risk:** Medium — same mechanical pattern
- **Depends on:** Step 15 (#158)
- **Validation:** `npm test`, verify #111 acceptance criteria met

#### Step 18 — Issue #150: `createCommands` delegates to `createCommand`

- **File:** `src/ogc-api/csapi/url_builder.ts`
- **Action:** Replace `createCommands()` body with `return this.createCommand(controlStreamId)`
- **Risk:** None — trivial after Steps 15–17
- **Validation:** `npm test`

---

### Phase E: Security Hardening (Step 19)

#### Step 19 — Issue #147: Add URL scheme validation to `scanCsapiLinks`

- **File:** `src/ogc-api/csapi/helpers.ts`
- **Action:** Validate that `href` values stored in the `resourceUrls` map use `http:` or `https:` schemes only — reject `javascript:`, `data:`, `//evil.com` etc.
- **Risk:** Low — defense-in-depth, separate file from everything else
- **Validation:** `npm test`

---

### Phase F: Test-Only Cleanup (Step 20)

#### Step 20 — Issue #151: Extract shared `_fixtures.ts` for integration tests

- **Files:** Create `src/ogc-api/csapi/integration/_fixtures.ts`; modify 4 spec files (`discovery.spec.ts`, `observation.spec.ts`, `command.spec.ts`, `navigation.spec.ts`)
- **Action:** Extract `PADDING` constant, `ALL_CSAPI_LINKS` array, and `makeFullCsapiCollection()` factory into shared fixture file; replace 4 local factories with imports
- **Risk:** None — test-only, zero production impact
- **Validation:** `npm test` (full suite — confirms all 81 integration tests still pass)

---

## Dependency Graph

```
Phase A (independent):
  #98  ───→ done
  #148 ───→ done

Phase B (sequential within part2.ts):
  #149 ───→ #146 ───→ #140 ───→ done

Phase C (independent per file, except #154→#155):
  #154 ───→ #155 ───→ done
  #143 ───→ done
  #144 ───→ done

Phase D (strict chain in url_builder.ts):
  #142 ───→ #139 ───→ #156 ───→ #157 ───→ #102 ───→ #158 ───→ #159 ───→ #160 (resolves #111) ───→ #150 ───→ done

Phase E (independent):
  #147 ───→ done

Phase F (independent):
  #151 ───→ done
```

---

## Files Touched Summary

| File                                                | Issues                                               | Total Steps |
| --------------------------------------------------- | ---------------------------------------------------- | ----------- |
| `src/ogc-api/csapi/formats/part2.ts`                | #98, #149, #146, #140                                | 4           |
| `src/ogc-api/csapi/url_builder.ts`                  | #142, #139, #156, #157, #102, #158, #159, #160, #150 | 9           |
| `src/ogc-api/csapi/formats/swecommon/parser.ts`     | #148                                                 | 1           |
| `src/ogc-api/csapi/formats/swecommon/data-array.ts` | #148                                                 | 1           |
| `src/ogc-api/csapi/formats/response.ts`             | #154                                                 | 1           |
| `src/ogc-api/csapi/formats/response.spec.ts`        | #154                                                 | 1           |
| `src/ogc-api/csapi/formats/sensorml.ts`             | #144                                                 | 1           |
| `src/ogc-api/csapi/formats/geojson.ts`              | #143                                                 | 1           |
| `src/ogc-api/csapi/helpers.ts`                      | #147                                                 | 1           |
| `src/ogc-api/csapi/integration/*.spec.ts`           | #155                                                 | 1           |
| `src/ogc-api/csapi/integration/_fixtures.ts`        | #151 (new)                                           | 1           |
| `src/ogc-api/csapi/integration/discovery.spec.ts`   | #151                                                 | 1           |
| `src/ogc-api/csapi/integration/observation.spec.ts` | #151                                                 | 1           |
| `src/ogc-api/csapi/integration/command.spec.ts`     | #151                                                 | 1           |
| `src/ogc-api/csapi/integration/navigation.spec.ts`  | #151                                                 | 1           |

---

## Validation Gates

After each phase:

1. `tsc --noEmit` — zero type errors
2. `npm test` — all tests pass (1,282+ tests, 29 suites)
3. `npm run lint` — zero lint errors
4. `npx prettier --check src/` — all files formatted

After all phases (in CSAPI_2):

5. Full integration test suite pass
6. Visual diff review of all changes

After porting to ogc-client `clean-pr`:

7. Run full validation suite again on `clean-pr`
8. Push to update PR #136

---

## Estimated Effort

| Phase                     | Steps  | Estimated Time  | Risk    |
| ------------------------- | ------ | --------------- | ------- |
| A: Quick Wins             | 2      | 30 min          | None    |
| B: `part2.ts` Batch       | 3      | 1–2 hours       | Low     |
| C: Type Safety            | 4      | 1.5–3 hours     | Low–Med |
| D: `url_builder.ts` Batch | 9      | 5–8 hours       | Medium  |
| E: Security Hardening     | 1      | 30 min          | Low     |
| F: Test Cleanup           | 1      | 30 min–1 hour   | None    |
| Porting to `clean-pr`     | —      | 30 min          | Low     |
| **Total**                 | **20** | **10–16 hours** |         |

---

## Post-Phase 7

After this cleanup is complete and the PR is updated:

- **#110** — `@link` / `@id` resolution utilities — first enhancement, separate PR
- **001, 002, 005, 006** — Upstream security/quality fixes — coordinate with camptocamp maintainer, separate PR(s)
