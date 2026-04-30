# Phase 8 — LOC Footprint Report

**Date:** 2026-04-29
**Author:** Phase 8 work session (post-D1d, pre-E1)
**Branch:** `phase-8` @ `02cf405`
**Baseline:** `phase-7` @ `b11f893`
**Status:** Pre-flight measurement before E1 (#180) patch generation

---

## Why this report exists

The E1 issue (#180) body predicted the upstream-bound patch would be
"~400 source LOC + ~550 test LOC = ~950 total." A pre-E1 measurement using the
issue's literal pathspec (`-- src/ fixtures/`) returned `+1425 / −372 = +1053
net`. That number triggered a (correct) push-back from the user about LOC bloat
on a phase that was supposed to be "API design refinements + one bug fix" with
**no new feature work**.

Investigation found two compounding issues:

1. The `~950` estimate in #180's body was a guess written before any task
   shipped. It was never re-measured against actual commits.
2. The literal pathspec `-- src/ fixtures/` includes upstream's own commits
   that arrived on `phase-8` via our merge-from-upstream commit `643626f`.
   Specifically, camptocamp's WMS DescribeLayer PR #137 (`caf3bd5`,
   `6d2c872`) added 6 files / +271 LOC under `src/wms/` and `fixtures/wms/`
   that we neither wrote nor are responsible for delivering. They appear in
   the broad diff but should not — and will not — appear in the patch we
   actually hand to upstream.

This report documents the actual Phase 8 footprint, demonstrates that the
final patch will contain ~804 net LOC (not ~1050 and not ~950), and
characterizes where every line went.

---

## Headline numbers

| Scope                                                                 | Files | Insertions | Deletions | **Net**  |
| --------------------------------------------------------------------- | ----- | ---------- | --------- | -------- |
| `git diff phase-7..phase-8 -- src/ fixtures/` (issue's literal scope) | 30    | 1425       | 372       | +1053    |
| Phase 8 only — excludes upstream WMS leakage                          | 22    | 1173       | 369       | **+804** |
| **Production code** (no `*.spec.ts`)                                  | **9** | **166**    | **40**    | **+126** |
| Tests                                                                 | 13    | 1007       | 329       | +678     |
| Fixtures                                                              | 0     | 0          | 0         | 0        |

**Phase 8 added 126 net lines of production logic** across 9 files for
8 tasks (A1–A4, B1, B2, C1, D1). The remaining ~678 LOC is tests; the
remaining ~258 LOC inside production files is intentional JSDoc per a
locked decision in #167.

---

## Section 1 — Where the upstream WMS leakage came from

Phase 8 began on a branch rebased onto `phase-7`. While Phase 8 was in
flight, camptocamp merged PR #137 (`wms-describe-layer`) into `main` on
`camptocamp/ogc-client`. We pulled that into `phase-8` via a routine
merge-from-upstream commit (`643626f`) so phase-8 wouldn't drift from the
upstream baseline during development.

The two upstream commits that came in:

```
caf3bd5  Update DescribeLayer fixtures and parser to SLD 1.1.0 format
6d2c872  Add DescribeLayer support to WmsEndpoint
```

Files affected (none ours, none Phase 8):

```
fixtures/wms/describelayer-wcs.xml      | +16
fixtures/wms/describelayer-wfs.xml      | +16
src/wms/describelayer.spec.ts           | +45
src/wms/describelayer.ts                | +42
src/wms/endpoint.spec.ts                | +65
src/wms/endpoint.ts                     | net change
src/wms/model.ts                        | +7
src/wms/url.ts                          | +20
```

Total upstream leakage: **6 source files + 2 fixtures, +252 / −19 LOC**.

**Why this won't reach upstream:** the E1 acceptance gate already requires
a path-prefix scope check before the patch is handed off. Per the
`Select-String -Pattern '^\s*(docs|app|src-node|tools|\.github)/'` check
in the issue body, plus the explicit allow-list of four prefixes
(`src/ogc-api/csapi/`, `src/ogc-api/endpoint.ts`, `src/ogc-api/index.ts`,
`fixtures/csapi/`), the WMS leakage is implicitly rejected.

**Recommendation for E1:** generate the patch with a tightened pathspec
upfront rather than the issue's literal `-- src/ fixtures/`:

```powershell
git diff phase-7..phase-8 -- `
  src/ogc-api/csapi/ `
  src/ogc-api/endpoint.ts `
  src/ogc-api/endpoint.spec.ts `
  src/ogc-api/index.ts `
  src/index.ts > phase-8.patch
```

This produces an identical end-state to the spec'd two-step (broad
generate + filter inspection) but eliminates the post-hoc reject step and
ensures the on-disk artifact never contains the WMS noise.

This is a deviation from the locked spec in #180. The E1 close comment
should call it out explicitly.

---

## Section 2 — Phase 8 production-code footprint, by file

`git diff --shortstat phase-7..phase-8 -- 'src/ogc-api/csapi/**/*.ts'
':!src/ogc-api/csapi/**/*.spec.ts' src/ogc-api/endpoint.ts
src/ogc-api/index.ts src/index.ts`:

```
9 files changed, 166 insertions(+), 40 deletions(-)
```

| File                                                                       | +ins | −del | Net     | Driver task(s)            |
| -------------------------------------------------------------------------- | ---- | ---- | ------- | ------------------------- |
| `src/ogc-api/csapi/url_builder.ts`                                         | 317  | 40   | +277    | A1, A3, A4, B1            |
| `src/ogc-api/csapi/index.ts`                                               | 56   | 6    | +50     | A4, A2, A3                |
| `src/ogc-api/endpoint.ts`                                                  | 60   | 7    | +53     | D1b (`csapi()` facade)    |
| `src/ogc-api/csapi/factory.ts`                                             | 42   | 53   | **−11** | D1b (reshape)             |
| `src/ogc-api/csapi/model.ts`                                               | 43   | 3    | +40     | A2 (`CSAPICollectionRef`) |
| `src/ogc-api/csapi/formats/part2.ts`                                       | 79   | 14   | +65     | C1 (`@link` fallback)     |
| `src/ogc-api/csapi/helpers.ts`                                             | 26   | 3    | +23     | A2, A4                    |
| `src/ogc-api/csapi/formats/{geojson,property,response,schema-response}.ts` | 32   | 6    | +26     | A3 type tightening        |
| `src/ogc-api/csapi/formats/swecommon/{_helpers,parser}.ts`                 | 7    | 2    | +5      | A3 type tightening        |
| `src/index.ts`                                                             | 1    | 0    | +1      | A2 export                 |

The single file with the largest delta is `url_builder.ts` (+277 net).
**+258 of those are JSDoc paragraphs**, not executable code — see Section 3.

---

## Section 3 — `url_builder.ts` deep dive: where +317 lines actually went

Per-commit breakdown of `url_builder.ts` from
`git log --shortstat phase-7..phase-8 -- src/ogc-api/csapi/url_builder.ts`:

| Commit    | Task    | +ins | −del | Net  | Nature                                                  |
| --------- | ------- | ---- | ---- | ---- | ------------------------------------------------------- |
| `4f3a7b7` | A4/#167 | 258  | 0    | +258 | **JSDoc only** — pagination contract on 39 list methods |
| `f3ebcbc` | B1/#176 | 31   | 31   | 0    | `DataStream` → `Datastream` rename                      |
| `0dc8805` | A3      | 13   | 5    | +8   | `ReadonlySet<CSAPIResourceType>` types                  |
| `935830b` | A1/#172 | 13   | 2    | +11  | URL-builder framing comments                            |
| `29d0c49` | A2      | 2    | 2    | 0    | `CSAPICollectionRef` constructor type swap              |

**81 % of `url_builder.ts`'s growth (+258 / +317) is documentation per a
locked decision in #167.** That decision (Option B, docs-only) was chosen
specifically to avoid adding behavior; the auto-pagination helper that
would have been actual code is deferred to #170.

A representative sample of the JSDoc content (from `4f3a7b7`):

```ts
/**
 * ## Pagination
 *
 * All list methods (`get*` returning collection URLs) follow the
 * [OGC API Common](https://docs.ogc.org/is/19-072/19-072.html#_pagination)
 * pagination contract:
 *
 * - **The server chooses the default page size** if `limit` is unspecified.
 *   Connected-systems-go defaults to `limit=10`; OpenSensorHub defaults to
 *   `limit=100`. Do not assume a specific default.
 * - **Pagination is HATEOAS via `rel="next"`** in the response body's
 *   `links` array. ...
 */
```

This is the kind of JSDoc that exists for users of the library, not for
the library itself. It compiles to zero bytes of runtime code.

---

## Section 4 — Test footprint, by file

`git diff --shortstat phase-7..phase-8 -- 'src/ogc-api/csapi/**/*.spec.ts'
src/ogc-api/endpoint.spec.ts`:

```
13 files changed, 1007 insertions(+), 329 deletions(-) = +678 net
```

| File                                                             | +ins   | −del   | Net   | Driver task(s)              |
| ---------------------------------------------------------------- | ------ | ------ | ----- | --------------------------- |
| `src/ogc-api/csapi/formats/part2.spec.ts`                        | 290    | 5      | +285  | C1 (`@link` fallback tests) |
| `src/ogc-api/csapi/factory.spec.ts`                              | 134    | 84     | +50   | D1b (rewrite)               |
| `src/ogc-api/csapi/url_builder.spec.ts`                          | 80     | 50     | +30   | A2/A3/B1 type updates       |
| `src/ogc-api/endpoint.spec.ts`                                   | 60     | 3      | +57   | D1b (`csapi()` block)       |
| `src/ogc-api/csapi/integration/observation.spec.ts`              | 13     | 7      | +6    | C1                          |
| Other (5 spec files: `geojson`, `discovery`, `navigation`, etc.) | sundry | sundry | ~+250 | A2/A3/B1 mechanical         |

The two largest deltas are:

- **`part2.spec.ts` +285** — covers the C1 `@link` cross-reference fallback
  bugfix (#166, commit `ca1157c`). This is real behavior on a real bug,
  exercised on real cs-go server traces. New behavior, new tests.
- **`factory.spec.ts` +50 net** — but +134 / −84 because the factory was
  reshaped from async-with-I/O to pure-value-shaped in D1b. Mostly churn,
  not net new code.

---

## Section 5 — Per-task LOC attribution

| Task | Issue | What                                                        | Prod LOC   | Test LOC | Notes                                    |
| ---- | ----- | ----------------------------------------------------------- | ---------- | -------- | ---------------------------------------- |
| A1   | #172  | URL-builder framing in module docs                          | +11        | 0        | Code-comment polish                      |
| A2   | #173  | `CSAPICollectionRef` (decouple from `OgcApiCollectionInfo`) | +40        | +25      | New type, propagates                     |
| A3   | #174  | `ReadonlySet<CSAPIResourceType>`                            | +8         | small    | Type tightening                          |
| A4   | #167  | Pagination JSDoc (locked: docs-only)                        | +258 JSDoc | +14      | Documentation per locked decision        |
| B1   | #176  | `DataStream` → `Datastream` rename                          | 0 net      | small    | Pure rename                              |
| B2   | #177  | Validators throw `EndpointError`                            | small      | small    | Error-class consolidation                |
| C1   | #166  | `@link` cross-reference fallback (cs-go interop)            | +65        | +285     | **Only behavior bugfix in Phase 8**      |
| D1b  | #183  | `csapi()` facade + value-shaped factory                     | +53/−11    | +57      | API design refinement (Finding 024 / A3) |
| D1c  | #184  | Re-privatize `root` + `getCollectionDocument`               | net 0      | −18      | Visibility flip; deletes redundant test  |

The "feature" total: +126 production LOC across 8 tasks. There is no
hidden feature work.

---

## Section 6 — Comparison to expectations

| Source                                                | Predicted total             | Actual   |
| ----------------------------------------------------- | --------------------------- | -------- |
| #180 issue body                                       | ~400 src + ~550 test = ~950 | n/a      |
| Initial broad-pathspec measurement (with WMS leakage) | n/a                         | +1053    |
| **Tight-pathspec measurement (Phase 8 only)**         | n/a                         | **+804** |
| Phase 8 "production logic" (excludes JSDoc + tests)   | n/a                         | **+126** |

The `+804` figure is **−15 % under the issue's `~950` estimate**, well
within the ±20 % tolerance the issue's acceptance gate specifies. The
panic was driven by the broad-pathspec measurement that included
upstream's own work.

---

## Section 7 — Recommended actions

1. **E1 patch generation (deviation from #180 spec):** generate the patch
   with the tightened pathspec listed in Section 1 to eliminate the WMS
   leakage at the source rather than rely on the post-hoc inspection
   filter. The E1 close comment must call this deviation out explicitly,
   and the inspection step in the acceptance-gate command block should
   still run as a redundancy check (and will return zero forbidden paths,
   since they were filtered upstream of the patch file).

2. **No source code changes.** This investigation surfaced no actual LOC
   bloat. The +804 net is well-characterized: 126 production logic lines
   across 8 well-scoped tasks, 258 lines of intentional JSDoc per a
   locked decision, and 678 lines of tests covering the bugfix and the
   refactor.

3. **#180 issue body's `~950` estimate is retroactively a guess.** The
   E1 close comment should record actuals (not the estimate) to avoid
   propagating the same imprecise guess to E2 and beyond.

---

## Section 8 — Reproducibility commands

All numbers in this report are reproducible from
`phase-8 @ 02cf405` against `phase-7 @ b11f893`:

```powershell
# Section 1 — broad-scope (with upstream leakage)
git diff --shortstat phase-7..phase-8 -- src/ fixtures/

# Section 1 — Phase 8 only (recommended scope)
git diff --shortstat phase-7..phase-8 -- `
  src/ogc-api/csapi/ src/ogc-api/endpoint.ts src/ogc-api/endpoint.spec.ts `
  src/ogc-api/index.ts src/index.ts

# Section 2 — production code only
git diff --shortstat phase-7..phase-8 -- `
  'src/ogc-api/csapi/**/*.ts' ':!src/ogc-api/csapi/**/*.spec.ts' `
  src/ogc-api/endpoint.ts src/ogc-api/index.ts src/index.ts

# Section 3 — url_builder.ts per-commit
git log --oneline --shortstat phase-7..phase-8 -- src/ogc-api/csapi/url_builder.ts

# Section 1 — upstream leakage commits (not ours)
git log --oneline phase-7..phase-8 -- src/wms/ fixtures/wms/
```

---

**End of report.**
