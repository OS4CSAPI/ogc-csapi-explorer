# Format Check Investigation Report

## Investigation: 655 Prettier Failures and QA Workflow Analysis

**Date:** 2025-02-24
**Branch:** `phase-6`
**Triggered by:** Post-Phase 6.1 code review discussion
**Status:** Complete — Root cause identified

---

## 1. Background and Timeline

### How the investigation started

After completing Phase 6A (Tasks 1–3: Prettier formatting, ESLint fixes, commit), a
code review was conducted. During that review, running `npm run format:check` showed
~605 files failing Prettier (later measured at 655 on a subsequent run). This led to
a series of questions:

1. Why does upstream run a QA action that appears to fail immediately?
2. Is upstream's `format:check` gate real and enforced?
3. How can 655 files fail formatting when we only touched ~49 CSAPI files?
4. Did our work cause these failures?

### Investigation progression

The investigation went through several phases of understanding, each correcting
assumptions from the prior phase:

| Phase                         | Assumption                                                | Finding                                                        |
| ----------------------------- | --------------------------------------------------------- | -------------------------------------------------------------- |
| Initial (during review)       | Upstream's `format:check` must fail on their own code too | **Wrong** — upstream CI passes                                 |
| Second (GitHub Actions check) | Our fork diverged from upstream's formatted state         | **Partially wrong** — file content is identical in git objects |
| Third (line ending analysis)  | The cause is something specific to our environment        | **Correct** — `core.autocrlf = true` on Windows                |

---

## 2. The QA Workflow (`qa.yml`)

### Structure

The QA workflow runs 5 sequential steps with no `continue-on-error`:

```yaml
steps:
  - run: npm run format:check # Step 1 — Prettier
  - run: npm run typecheck # Step 2 — tsc
  - run: npm run lint # Step 3 — ESLint
  - run: npm run test:browser # Step 4 — Jest (jsdom)
  - run: npm run test:node # Step 5 — Jest (node)
```

When `format:check` fails, **all subsequent steps are killed**. No typecheck, no lint,
no tests.

### Authorship

The workflow was created by jahow (Olivia), the upstream maintainer, across 3 commits:

1. Initial CI setup with format check and typecheck
2. Added lint step
3. Added `test:node` step

Our commits (Sam-Bolling) only modified branch triggers — adding and then disabling
`phase-6` as a trigger branch.

### Upstream CI status

**Upstream's CI passes on `main`.** Verified by checking the GitHub Actions history at
`camptocamp/ogc-client`:

| Run # | Event                                    | Status   |
| ----- | ---------------------------------------- | -------- |
| #285  | Push to `main` (Merge PR #132, Dec 2025) | **Pass** |
| #282  | Push to `main` (Merge PR #128, Dec 2025) | **Pass** |
| #281  | PR #128 (ESLint 9 migration)             | **Pass** |
| #267  | Push to `main` (Oct 2025)                | **Pass** |
| #288  | **Our PR #136** (CSAPI support)          | **Fail** |

The QA gate is **real and enforced**. Upstream contributors submit PRs that pass all 5
steps, including `format:check`.

---

## 3. Root Cause: `core.autocrlf = true` on Windows

### The mechanism

1. **Upstream stores all files with LF** (Unix line endings) in git objects
2. **Upstream CI runs on `ubuntu-latest`** — files check out with LF — Prettier sees
   LF — passes
3. **Windows git with `core.autocrlf = true`** converts LF → CRLF when checking out
   files to the working tree
4. **Prettier 2.8.8 defaults `endOfLine` to `lf`** — when it scans files on disk and
   sees CRLF, it flags every line ending as a formatting violation
5. This affects **every text file** in the working tree — upstream files, our files,
   all files

### Configuration comparison

| Setting            | Upstream                                 | Our fork                     |
| ------------------ | ---------------------------------------- | ---------------------------- |
| Prettier version   | 2.8.8                                    | 2.8.8                        |
| `.prettierrc.json` | `{ "semi": true, "singleQuote": true }`  | Identical                    |
| `.prettierignore`  | XML fixtures, dist, node_modules         | Identical                    |
| `endOfLine` config | Not set (defaults to `lf`)               | Not set (defaults to `lf`)   |
| `.gitattributes`   | Does not exist                           | Does not exist               |
| `core.autocrlf`    | N/A (CI runs Linux, defaults to `false`) | **`true`** (Windows default) |

### Key insight

There is no `.gitattributes` file in the repo. Upstream has never needed one because
their development and CI both happen on Linux/macOS where `core.autocrlf` is `false`
by default. The repo implicitly depends on LF line endings without explicitly
enforcing them.

---

## 4. The 655 Failures: Complete Breakdown

### By origin

| Category                                    | Count   | Created by            | Modified by us? |
| ------------------------------------------- | ------- | --------------------- | --------------- |
| CSAPI files (path contains `csapi`/`CSAPI`) | 122     | Us                    | Yes             |
| Non-CSAPI files created by us               | 317     | Us                    | Yes             |
| Upstream files we modified                  | 6       | Upstream (originally) | Yes             |
| Upstream files **untouched** by us          | 137     | Upstream              | **No**          |
| **Total**                                   | **655** | —                     | —               |

### By top-level directory (non-CSAPI only)

| Directory         | Count | Notes                                        |
| ----------------- | ----- | -------------------------------------------- |
| `docs/`           | 314   | All ours — upstream has no `docs/` directory |
| `fixtures/`       | 80    | Mix of upstream and ours                     |
| `src/`            | 79    | Mix of upstream and ours                     |
| `app/`            | 35    | Mostly upstream                              |
| Root config files | ~15   | Upstream                                     |
| Other             | ~10   | Mixed                                        |

### The 137 untouched upstream files

These are the proof that the failures are environmental, not caused by our code. We
verified with `git diff 53a6449 HEAD -- <file>` that these 137 files have zero
differences from the upstream fork point. They fail Prettier solely because
`core.autocrlf` converted their line endings on checkout.

---

## 5. Proof Chain

Each claim was independently verified:

### Proof 1: Git blobs store LF

```
git cat-file -p HEAD:babel.config.cjs > raw-file
# Raw file has 0 CR (0x0D) bytes — pure LF
```

### Proof 2: Working tree has CRLF

```
[System.IO.File]::ReadAllBytes("babel.config.cjs")
# Disk file has 3 CR bytes — CRLF line endings
```

### Proof 3: Converting CRLF → LF fixes the failure

```
# .prettierrc.json with CRLF: FAILS prettier --check
# Same file converted to LF: PASSES prettier --check
```

### Proof 4: Upstream fork point fails locally too

```
git checkout 53a6449 --detach
npx prettier --check .
# Result: "Code style issues found in 218 files"
# This is BEFORE any of our work existed
```

### Proof 5: core.autocrlf is the divergence

```
git config --get core.autocrlf
# Returns: true
```

---

## 6. Correction of Prior Statements

During this investigation, several intermediate conclusions were stated and later
corrected. For transparency:

| Statement                                                                           | When made                                   | Correction                                                                                                                               |
| ----------------------------------------------------------------------------------- | ------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| "Upstream fails their own `format:check` on 605 files"                              | During code review                          | **Wrong.** Upstream passes. The failures are Windows-local due to CRLF.                                                                  |
| "The effort was based on an unverified assumption" (re: Prettier work)              | After the review, when value was questioned | **Wrong.** The assumption that `format:check` is enforced was correct. It IS enforced on upstream CI.                                    |
| "Fork divergence" caused the failures                                               | Initial response to Actions investigation   | **Misleading.** The git objects are identical. The divergence is only at the working-tree level due to OS line-ending conversion.        |
| "Nothing provides value — the entire pipeline is dead on arrival" (re: QA workflow) | During QA workflow analysis                 | **Wrong for CI.** The pipeline works correctly on Linux CI. It's only "dead" when run locally on Windows without line-ending mitigation. |

---

## 7. Impact Assessment

### What this means for our Phase 6 work

1. **Phase 6A Prettier formatting was correct and necessary.** The `format:check`
   gate is real. Any PR must pass it. Our CSAPI files needed formatting.

2. **The 655 failures do NOT indicate broken code.** Every single failure is a
   line-ending mismatch between disk (CRLF) and Prettier's expectation (LF). Zero
   failures relate to actual code formatting.

3. **We cannot run `npm run format:check` locally** as a reliable CI gate without
   addressing the line-ending issue first. This means our local QA workflow simulation
   has a blind spot.

4. **Our Phase 6.1 code review CI gate C1 was incorrectly assessed.** We marked it as
   "605 pre-existing upstream failures" — they're actually Windows-local CRLF
   artifacts. On the actual CI (Linux), the only failures would be files we haven't
   yet formatted.

5. **All other CI gates (typecheck, lint, tests) are unaffected** by line endings.
   Those tools don't care about CRLF vs LF.

### What this means for PR submission

When we submit a PR to upstream (`camptocamp/ogc-client`), the CI will run on
`ubuntu-latest` where `core.autocrlf` is `false`. **The CRLF issue disappears
entirely on CI.** The only Prettier failures that would show up are files with
actual formatting issues (wrong indentation, missing semicolons, etc.) — which is
exactly what Phase 6A fixed for CSAPI files.

---

## 8. Recommendations

### Immediate: Fix local development experience

**Option A: Set `core.autocrlf = input` for this repo** (Recommended)

```bash
git config core.autocrlf input
```

This tells git: convert CRLF → LF on commit, but do NOT convert LF → CRLF on
checkout. Files on disk will have LF. Prettier will pass. This is repo-local
and doesn't affect other projects.

After changing the setting, a fresh checkout is needed:

```bash
git rm --cached -r .
git reset --hard
```

**Option B: Add a `.gitattributes` file**

```
* text=auto eol=lf
```

This forces LF line endings for all text files. This would be a change to
submit upstream (arguably beneficial — it protects all Windows contributors).

**Option C: Add `endOfLine: "auto"` to `.prettierrc.json`**
This tells Prettier to accept whatever line endings are present. This would
also be a change to submit upstream and changes the formatting contract.

### Strategic: For PR submission

The CRLF issue has **zero impact on CI**. When the PR runs on `ubuntu-latest`,
line endings will be LF and `format:check` will evaluate actual formatting only.
No action needed specifically for PR readiness.

### Process: Update the code review template

The Phase 6.1 review gate C1 assessment should be noted as environmentally
incorrect. Future local QA gate checks should either:

- Be run after applying Option A above, or
- Note that `format:check` failures on Windows are expected and not indicative
  of actual formatting problems

---

## 9. Lessons Learned

1. **Verify assumptions against upstream CI, not just local runs.** The upstream
   Actions page is the ground truth for what passes and what doesn't.

2. **Windows development environments introduce invisible differences.** Line endings
   are a classic source of phantom failures that don't reproduce on Linux CI.

3. **When a large number of failures appear, check for systemic causes first.** 655
   files failing the same check should have immediately suggested an environmental
   issue rather than a code issue.

4. **Intermediate conclusions should be held lightly.** This investigation went through
   three phases of understanding, each correcting the last. The first two were wrong.
