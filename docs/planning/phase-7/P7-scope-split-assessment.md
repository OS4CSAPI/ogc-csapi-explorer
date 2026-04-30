# Phase 7: Scope & Split Assessment

**Date:** March 7, 2026
**Assessor:** GitHub Copilot (Claude Opus 4.6)
**Purpose:** Determine which Phase 7 GitHub issues can be resolved in a single pass vs. which need to be split into multiple parts for safe execution

---

## Methodology

Each of the 17 issues in the P7 plan was reviewed against:

1. **Actual codebase measurements** — line counts, call-site counts, file sizes
2. **Nature of changes** — mechanical vs. semantic, single-file vs. cross-file
3. **Known agent failure modes** — edit accuracy degrades past ~40 edits in one file, and past ~8 files touched in one pass

The `url_builder.ts` file (2,490 lines, 87 public methods) was measured in detail since it is the primary target of 6 of the 16 steps.

---

## Key Measurements

| File                        | Lines | Public Methods                      | `assertResourceAvailable` calls              | `buildResourceUrl` calls |
| --------------------------- | ----- | ----------------------------------- | -------------------------------------------- | ------------------------ |
| `url_builder.ts`            | 2,490 | 87                                  | 87                                           | 87                       |
| `parser.ts` (swecommon)     | —     | —                                   | 19 redundant casts                           | —                        |
| `data-array.ts` (swecommon) | —     | —                                   | 8 redundant casts                            | —                        |
| `part2.ts`                  | —     | 5 parsers with identical null-guard | 2 duplicated stream parsers (~30 lines each) | —                        |

### url_builder.ts Method Breakdown by Resource Type

| Resource Type    | Total Methods | List/Create (keep assert) | Per-ID (remove assert) |
| ---------------- | ------------- | ------------------------- | ---------------------- |
| Systems          | 16            | 2                         | 14                     |
| Deployments      | 9             | 2                         | 7                      |
| Procedures       | 8             | 2                         | 6                      |
| SamplingFeatures | 8             | 2                         | 6                      |
| Properties       | 6             | 1                         | 5                      |
| Datastreams      | 11            | 2                         | 9                      |
| Observations     | 8             | 1                         | 7                      |
| ControlStreams   | 11            | 2                         | 9                      |
| Commands         | 10            | 1                         | 9                      |
| **Total**        | **87**        | **15**                    | **72**                 |

### Issue #151 — Test Fixture Factory Scope

| Spec File             | Factory Name            | Lines          | Links |
| --------------------- | ----------------------- | -------------- | ----- |
| `discovery.spec.ts`   | `makeCSAPICollection()` | 51             | 10    |
| `observation.spec.ts` | `makeCollection()`      | 39             | 4     |
| `command.spec.ts`     | `makeCollection()`      | 38             | 4     |
| `navigation.spec.ts`  | `makeFullCollection()`  | 49             | 9     |
| **Total duplicated**  |                         | **~177 lines** |       |

---

## Assessment Results

### Single Pass — Confident (13 issues)

| Step | Issue | Scope                                            | Rationale                     |
| ---- | ----- | ------------------------------------------------ | ----------------------------- |
| 1    | #98   | JSDoc edit, 1 line                               | Trivial                       |
| 2    | #148  | 27 cast deletions, 2 files                       | Mechanical, identical pattern |
| 3    | #149  | Extract 1 helper, 5 call sites, 1 file           | Small scope                   |
| 4    | #146  | Extract 1 helper from 2 functions, 1 file        | ~30 duplicated lines          |
| 5    | #140  | 1-line fallback + 1 test fixture                 | Trivial                       |
| 7    | #143  | Null check before 1 cast, 1 function             | Trivial                       |
| 8    | #144  | ~1-3 functions, SensorML parsers                 | See flag below                |
| 9    | #142  | Union type + runtime check, 2 functions, 2 files | Focused scope                 |
| 10   | #139  | Fix 1 method + update test fixture               | Small scope                   |
| 12   | #102  | Add optional param to 14 methods (7+7 clustered) | Patterned, clustered          |
| 14   | #150  | 1-line body replacement                          | Trivial                       |
| 15   | #147  | Scheme validation at 3 points, 1 function        | Small scope                   |
| 16   | #151  | Create 1 shared file, modify 4 spec files        | Straightforward extract       |

### Needs Splitting — 3 Issues

#### Issue #141 — `parseCollectionResponse` element validation (Step 6)

**Problem:** The function signature changes to require a `parseItem` callback. ~45 call sites across 7 test files need updating, each with a different `T` type requiring a different callback. This is not mechanical find-and-replace — each call site requires semantic judgment about which parser function to pass.

**Recommended split (2 parts):**

| Part  | Scope                                                                                                                                                              | Edits        |
| ----- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------ |
| **A** | Implement `parseCollectionResponse` change + update production callers + `response.spec.ts` unit tests                                                             | ~8-10 edits  |
| **B** | Update integration test call sites (`discovery.spec.ts`, `observation.spec.ts`, `command.spec.ts`, `navigation.spec.ts`, `pipeline.spec.ts`, remaining spec files) | ~35-40 edits |

---

#### Issue #100 — Remove `assertResourceAvailable` from 72 per-ID methods (Step 11)

**Problem:** 72 one-line deletions in a 2,490-line file. Each deletion is identical in pattern, but 72 edits in a single pass on a file this large leads to dropped edits and off-by-one placement errors. The methods are grouped by resource type, providing natural split points.

**Recommended split (2 parts):**

| Part  | Resource Types                                                                          | Method Count |
| ----- | --------------------------------------------------------------------------------------- | ------------ |
| **A** | Systems (14) + Deployments (7) + Procedures (6) + SamplingFeatures (6)                  | 33           |
| **B** | Properties (5) + Datastreams (9) + Observations (7) + ControlStreams (9) + Commands (9) | 39           |

---

#### Issue #145 — Add `build()` wrapper, rewrite all 87 methods (Step 13)

**Problem:** The single largest change in the plan. Requires (1) creating a new private `build()` method, then (2) rewriting all 87 public method bodies to delegate to it. After #100 removes asserts from 72 methods, there are two different pre-existing patterns (15 with assert retained, 72 without), adding complexity. 87 method rewrites in a 2,490-line file is the highest-risk item.

**Recommended split (3 parts):**

| Part  | Resource Types                                                            | Method Count |
| ----- | ------------------------------------------------------------------------- | ------------ |
| **A** | Create `build()` helper + Systems (16) + Deployments (9) + Procedures (8) | 33           |
| **B** | SamplingFeatures (8) + Properties (6) + Datastreams (11)                  | 25           |
| **C** | Observations (8) + ControlStreams (11) + Commands (10)                    | 29           |

---

### Flag: Issue #144 — SensorML Scope May Be Overstated

The issue describes "raw JSON spread" in 3 parser files (`physical-system.ts`, `aggregate-process.ts`, `simple-process.ts`), but codebase measurement found **only 1 raw JSON spread in production code** (in `_helpers.ts` at line 270). The pattern may manifest differently than a literal `...json` spread, or the issue's scope may have changed since filing. Recommend reading the actual affected functions before committing to a plan when we reach Step 8.

If scope is confirmed as small (1-3 functions with minor changes), single pass is fine. If scope is larger than expected, reassess.

---

## Totals

| Category           | Issues       | Plan Steps | Execution Passes |
| ------------------ | ------------ | ---------- | ---------------- |
| Single pass        | 13           | 13         | 13               |
| Split into 2 parts | #141, #100   | 2          | 4                |
| Split into 3 parts | #145         | 1          | 3                |
| **Total**          | **16 steps** | **16**     | **20 passes**    |

---

## Next Steps

1. Split Issues #141, #100, and #145 into sub-issues on GitHub (with clear part labels and scope boundaries)
2. Update the P7 plan to reference the sub-issues
3. Begin execution: one issue (or sub-issue) per pass, validating after each
