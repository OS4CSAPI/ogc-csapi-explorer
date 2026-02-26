# Upstream PR Preparation — Strategy Discussion

**Date:** 2026-02-21  
**Participants:** Sam Bolling, GitHub Copilot (Claude Opus 4.6)  
**Decision:** Option A — Fresh Fork + Rebase Plan

---

## User Prompt

> ok man, I think we are ready to prepare a draft PR to submit our code contribution to the upstream repo for the maintainers. but before we do that, I would like to rebase somehow. you mentioned a squash strategy, but I don't know what that means. I do know that for what we submit to the upstream, I want to remove the docs folder entirely. I don't want any of our exploratory documentation to be there for them because I don't think they want it. I do however want to preserve it somewhere for us. I'm not saying we rebase this way, I am open to options and I want you to present them with your recommendations, but an approach we took earlier with a failed attempt (not because of the rebase, but because the implementation I made with ChatGPT was not good enough) worked really well. we created a brand new fork of the upstream, then we created a "rebase plan" with the intent to add the end result of our original forked repo work into the newly forked repo with a clean, reasonably minimal set of commits, in a very well-organized, clean, logical, sensible, practical, story-telling manner. We didn't carry over anything that we deemed shouldn't be part of the contribution, like I don't want our massive doc folder. For your awareness, the example I am referring to, here was the original fork that was deemed exploratory with a large number of commits that took place to get the job done https://github.com/OS4CSAPI/ogc-client-homework and here was the rebased version of it that we submitted the PR from https://github.com/OS4CSAPI/ogc-client. can you please think deeply and weigh in?

---

## Analysis Context

| Metric                                | Value                                           |
| ------------------------------------- | ----------------------------------------------- |
| Total commits in `ogc-client-CSAPI_2` | 1,179                                           |
| Commits ahead of upstream             | **698**                                         |
| Upstream commits ahead of us          | 0 (we're current with `camptocamp/ogc-client`)  |
| Non-docs files changed vs upstream    | **69 files** (29,768 insertions, 225 deletions) |
| Docs files (exclusion zone)           | **371 files** (~286,000+ lines)                 |
| Upstream repo                         | `camptocamp/ogc-client`                         |
| Prior exploratory fork                | `OS4CSAPI/ogc-client-homework`                  |
| Prior clean fork (submitted PR from)  | `OS4CSAPI/ogc-client`                           |

---

## The Four Options Evaluated

### Option A: Fresh Fork + Rebase Plan (RECOMMENDED — SELECTED)

Create a brand-new fork of `camptocamp/ogc-client`. Write a rebase plan. Reconstruct ~12–15 clean commits by copying the final-state files from this repo into the fresh fork in logical groupings. The current repo (`ogc-client-CSAPI_2`) remains untouched as the archive.

- **Docs exclusion:** Trivial — just don't copy `docs/`
- **Docs preservation:** This repo stays intact forever with all 371 doc files, 1,179 commits
- **Risk to working code:** Zero
- **Reviewer experience:** Excellent — clean narrative, each commit compiles, ~15 digestible diffs
- **Effort:** Medium — need to plan groupings and reconstruct commits, but the file set is well-defined (69 files)

### Option B: Clean Branch in Current Repo

`git checkout -b clean-pr upstream/main` inside this same repo, then reconstruct the same clean commits.

- **Docs exclusion:** Same — don't include them in the commits
- **Docs preservation:** Still on `main` branch
- **Risk:** Low, but the branch lives alongside 698 messy commits
- **Reviewer experience:** Same as Option A if done right
- **Effort:** Same as A, but the PR would come from this repo's fork (which has docs in its history)

### Option C: Single Squash Commit

`git diff upstream/main -- <non-docs files> | git apply` — one commit, everything at once.

- **Docs exclusion:** Easy
- **Reviewer experience:** **Terrible** — one 30,000-line diff, no narrative, no way to review incrementally
- **Effort:** Minimal
- **Not recommended** for a contribution this size

### Option D: Interactive Rebase (`git rebase -i`)

Squash and reorder 698 commits interactively. Drop docs-only commits.

- **Risk:** **Catastrophic** — 698 commits with conflicts cascading at every step
- **Docs exclusion:** Extremely difficult — docs are woven through hundreds of commits
- **Effort:** Days of painful conflict resolution
- **Not recommended** — this is the wrong tool for this job

---

## Why Option A Wins

1. **Proven approach** — we did exactly this going from `ogc-client-homework` (messy) to `ogc-client` (clean 15 commits). That clean fork had a beautiful commit sequence like `feat(csapi): add CSAPI type definitions and model interfaces` → `feat(csapi): implement Part 1 resource clients` → etc.

2. **Zero risk** — `ogc-client-CSAPI_2` stays untouched. All 371 docs, all 1,179 commits, all review reports — forever preserved.

3. **Clean slate for upstream** — maintainers at camptocamp see a fork with exactly their history + 12–15 well-organized feature commits. No docs, no governance files, no smoke test reports.

4. **The file set is well-bounded** — only 69 files need to cross over. The reconstruction is straightforward.

---

## Proposed Commit Plan (Draft)

| #   | Commit Message                                               | Key Files                                                                        |
| --- | ------------------------------------------------------------ | -------------------------------------------------------------------------------- |
| 1   | `feat(csapi): add type definitions and model interfaces`     | `model.ts`, `model.spec.ts`                                                      |
| 2   | `feat(csapi): add URL builder with CRUD query support`       | `url_builder.ts`, `url_builder.spec.ts`                                          |
| 3   | `feat(csapi): add helper utilities and command routing`      | `helpers.ts`, `command-routing.ts` + specs                                       |
| 4   | `feat(csapi): add GeoJSON Part 1 format extraction`          | `formats/geojson.ts`, `constants.ts`, `property.ts`, `classification.ts` + specs |
| 5   | `feat(csapi): add SWE Common data model parsers`             | `formats/swecommon/*`                                                            |
| 6   | `feat(csapi): add SensorML procedure description parsers`    | `formats/sensorml/*`                                                             |
| 7   | `feat(csapi): add Part 2 dynamic data format handlers`       | `formats/part2.ts` + spec                                                        |
| 8   | `feat(csapi): add schema-response and format pipeline`       | `formats/schema-response.ts`, `response.ts`, `formats/index.ts` + specs          |
| 9   | `test(csapi): add CSAPI test fixtures`                       | `fixtures/ogc-api/csapi/*`                                                       |
| 10  | `test(csapi): add integration test suites`                   | `integration/*.spec.ts`                                                          |
| 11  | `feat(csapi): integrate CSAPI detection into OgcApiEndpoint` | `endpoint.ts`, `info.ts`, `mime-type.ts` + specs                                 |
| 12  | `feat(csapi): export CSAPI from main library index`          | `src/index.ts`                                                                   |

Each commit compiles. Each tells one chapter of the story: types → builder → helpers → format parsers (layered) → tests → integration → export.

---

## What Gets Excluded From Upstream PR

- Entire `docs/` folder (371 files — governance, planning, research, reviews, smoke tests)
- `.github/ISSUE_TEMPLATE/general-task.yml` (our workflow artifact)
- `app/package-lock.json` (to be determined — depends on whether demo app changes go in)

---

## What Gets Preserved (in `ogc-client-CSAPI_2`)

Everything. This repo is the permanent archive of the full development journey — all documentation, all code reviews, all smoke test reports, all 1,179 commits.

---

## Next Steps

1. Delete or rename the old `OS4CSAPI/ogc-client` repo (from the previous attempt)
2. Create a fresh fork of `camptocamp/ogc-client` as `OS4CSAPI/ogc-client`
3. Write a detailed rebase plan document with exact file-to-commit mappings
4. Execute the plan — construct each commit, verify, push
5. Open the PR to `camptocamp/ogc-client`
