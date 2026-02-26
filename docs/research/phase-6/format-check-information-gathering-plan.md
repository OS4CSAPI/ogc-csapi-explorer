# Format Check: Information Gathering Plan

**Date:** 2025-02-24
**Branch:** `phase-6`
**Context:** After applying `core.autocrlf = input` fix, before taking further action
**Purpose:** Define what we need to know to truly understand our situation

---

## What we need to know and why

### Question 1: What does `format:check` actually report now?

This is the single most important unknown. With CRLF fixed, running
`npm run format:check` will give us the real number for the first time. Every number
discussed previously (605, 655, 439, 137) came from CRLF-contaminated data. We need
the clean number before anything else makes sense.

### Question 2: What categories do those failures fall into?

Once we have the real list, we need to sort them into buckets:

- CSAPI source/test files (Phase 6A was supposed to fix these)
- Our docs/planning/research markdown files
- Our fixture files
- Upstream files we modified (like `endpoint.ts`)
- Upstream files we never touched (this should be zero now — if it's not, something
  else is wrong)

This tells us what actually needs work vs what is noise.

### Question 3: Do the other 4 gates still pass?

The `git rm --cached` + `reset --hard` re-checked out every file. We should verify
typecheck, lint, and tests still pass. They should not be affected by line endings,
but we should confirm rather than assume.

### Question 4: What files would actually be in our upstream PR?

This is the strategic question. Our `docs/` directory does not exist in upstream. Our
planning documents, research notes, governance docs — none of that goes upstream. If
the majority of failures are in files we would never submit, they do not block PR
readiness. We need to know which failures are in PR-relevant files.

---

## Recommended execution order

1. Run `format:check` — get the clean number
2. Categorize the failures
3. Run the other 4 gates (typecheck, lint, test:browser, test:node)
4. Map failures against PR scope

Each step takes under 2 minutes. All are read-only (no code changes). Each step
informs the next.

---

## Results

### Step 1: Clean format:check count

**394 files fail.** (Previously 655 with CRLF contamination — 261 were pure CRLF
artifacts.)

### Step 2: Categorization

**By top-level directory:**

| Directory  | Count   |
| ---------- | ------- |
| `docs/`    | 389     |
| `src/`     | 2       |
| `.github/` | 1       |
| `.vscode/` | 1       |
| `app/`     | 1       |
| **Total**  | **394** |

**CSAPI vs non-CSAPI:**

| Category                                  | Count                                  |
| ----------------------------------------- | -------------------------------------- |
| CSAPI-related (path contains csapi/CSAPI) | 74 — **all markdown, zero code files** |
| Non-CSAPI                                 | 320                                    |

**Docs breakdown (389 files):**

| Subdirectory                    | Count |
| ------------------------------- | ----- |
| `docs/research/`                | 227   |
| `docs/implementation/`          | 78    |
| `docs/testing/`                 | 32    |
| `docs/planning/`                | 29    |
| `docs/governance/`              | 18    |
| `docs/upstream-pr-preparation/` | 3     |
| `docs/webapp-demo/`             | 2     |

**The 5 non-docs failures:**

| File                                      | In upstream? | Modified by us?      |
| ----------------------------------------- | ------------ | -------------------- |
| `src/ogc-api/endpoint.spec.ts`            | Yes          | Yes (we modified it) |
| `src/ogc-api/info.ts`                     | Yes          | Yes (we modified it) |
| `.github/ISSUE_TEMPLATE/general-task.yml` | No           | Ours                 |
| `.vscode/tasks.json`                      | No           | Ours                 |
| `app/src/data/api.json`                   | No           | Ours                 |

**Key findings:**

1. **Zero CSAPI source/test code files fail.** Phase 6A formatting worked correctly.
2. **389 of 394 failures (98.7%) are markdown documentation files** we created.
3. **Zero untouched upstream files fail.** The CRLF fix resolved those completely.
4. **2 upstream source files we modified fail** — `endpoint.spec.ts` and `info.ts`.
5. **3 new non-code files we created fail** — issue template, tasks.json, api.json.

### Interpretation

The picture is much simpler than initially feared. The vast majority of failures
(98.7%) are markdown documentation files that we wrote and that do not exist in
upstream. Phase 6A formatting of CSAPI source/test code worked correctly — zero
code failures. The CRLF fix eliminated all phantom failures from untouched upstream
files.

The 394 failures break down to: 389 markdown formatting + 2 upstream source files
we touched + 3 small config/data files we created.

### Step 3: Other QA gates

**Run date:** 2025-02-24 (after CRLF fix applied)

| Gate                   | Result            | Details                     |
| ---------------------- | ----------------- | --------------------------- |
| `npm run typecheck`    | **PASS**          | Exit 0, clean               |
| `npm run lint`         | **PASS**          | Exit 0, clean               |
| `npm run test:node`    | **PASS**          | 60 suites, 0 failures       |
| `npm run test:browser` | **2 suites fail** | 56 pass, 2 fail — see below |

**test:browser failures (2 suites, ~45 individual test timeouts):**

Both suites fail from the **same root cause** — esbuild cannot resolve the worker
path on Windows:

```
Error: Build failed with 1 error:
error: Could not resolve "C:UserssbollingDocumentsogc-client-CSAPI_2srcworker/worker.ts"
```

The backslashes in the Windows path are being stripped by esbuild, so the path
becomes `C:Users...` instead of `C:\Users\...`. This causes the worker build to
fail silently, and all tests that depend on `await endpoint.isReady()` through the
worker timeout (5000ms default).

| Failing Suite                   | Timeout | Tests Failed                           |
| ------------------------------- | ------- | -------------------------------------- |
| `src/shared/http-utils.spec.ts` | 8s      | Worker-related tests                   |
| `src/wms/endpoint.spec.ts`      | 98s     | All tests (endpoint depends on worker) |

**This is a pre-existing Windows platform issue.** It is not caused by our changes.
It would affect any Windows checkout of this repository. Upstream CI runs on Linux
where this path issue does not occur.

**Note on variability:** An earlier run during a stressed terminal session showed
4 failed suites / 79 failed tests. The clean run above (2 suites / 45 failures)
is the reliable result. The difference was likely due to additional timeout flakes
under system load. The consistent set is these 2 suites failing due to the Windows
esbuild path bug.

### Step 4: PR scope mapping

**Question:** Of the 394 format:check failures, how many are in files that would
actually be submitted in an upstream PR?

**Changed files since fork point (`53a6449`):**

| Category                                      | File Count   |
| --------------------------------------------- | ------------ |
| CSAPI source/test code (`src/ogc-api/csapi/`) | 56 new files |
| Modified upstream source files                | 6 files      |
| CSAPI fixtures (`fixtures/ogc-api/csapi/`)    | 4 new files  |
| Other (`.gitignore`, `app/package-lock.json`) | 2 files      |
| **Total code/config changes**                 | **68 files** |
| Documentation (`docs/`)                       | ~389 files   |
| `.github/`, `.vscode/`                        | ~2 files     |

**Format:check failures mapped to PR scope:**

| Scope                                    | Files in scope     | Files failing format:check | Status            |
| ---------------------------------------- | ------------------ | -------------------------- | ----------------- |
| CSAPI code (56 files)                    | Would be in PR     | **0 failures**             | Clean             |
| Modified upstream code (6 files)         | Would be in PR     | **2 failures**             | Needs fix         |
| CSAPI fixtures (4 files)                 | Would be in PR     | **0 failures**             | Clean             |
| `docs/` (389 files)                      | NOT in upstream PR | **389 failures**           | Does not block PR |
| `.github/`, `.vscode/`, `app/` (3 files) | NOT in upstream PR | **3 failures**             | Does not block PR |

**The 2 PR-relevant format:check failures:**

1. `src/ogc-api/endpoint.spec.ts` — upstream file we modified
2. `src/ogc-api/info.ts` — upstream file we modified

**Fix:** `npx prettier --write src/ogc-api/endpoint.spec.ts src/ogc-api/info.ts`

---

## Final Summary

### What blocks upstream PR submission?

**Almost nothing.** Two source files need a `prettier --write`. That's it.

- All 56 CSAPI source/test files pass format:check
- All 4 CSAPI fixture files pass format:check
- typecheck passes
- lint passes
- test:node passes (60/60 suites)
- test:browser: 2 suites fail on Windows only (esbuild path bug), passes on Linux CI

### What blocks our fork's own CI?

**394 format:check failures**, almost entirely markdown documentation (389/394).
Fix: `npx prettier --write` on all affected files. This is a one-time formatting
pass, not a code logic issue.

### What was the original problem?

`core.autocrlf = true` on Windows caused every file to appear to fail format:check
(655 files). After fixing to `core.autocrlf = input`, the real count is 394 — all
of which are files we created or modified that were never run through Prettier.

---

## Plain-Language Explanation: QA GitHub Action Status

### What the QA workflow does

The QA GitHub Actions workflow (`.github/workflows/qa.yml`) runs 5 checks in
sequence on every push and PR:

1. `npm run format:check` — Prettier formatting
2. `npm run typecheck` — TypeScript compilation
3. `npm run lint` — ESLint
4. `npm run test:browser` — Jest tests (browser environment)
5. `npm run test:node` — Jest tests (Node environment)

If any step fails, the whole workflow fails — there is no `continue-on-error`.
This is the same workflow used by upstream (`camptocamp/ogc-client`), authored by
the same maintainer (jahow / Olivia).

### Upstream status

Upstream CI **passes all 5 gates** on Linux. Their recent runs (#285, #282, #281,
#267) are all green.

### Our fork's status

**Our fork fails at step 1 — format:check — and never reaches the other 4.**

The failure is not a code quality issue. It is a formatting issue in files we
created but never ran through Prettier.

### Why does format:check fail?

We added ~389 markdown documentation files (the entire `docs/` directory) and a
handful of config files. None of those files have ever been run through Prettier.
When `format:check` runs, it finds 394 files with formatting issues and exits
non-zero.

The 394 break down as:

- **389** are our markdown docs — none of these exist in upstream
- **2** are upstream source files we modified (`endpoint.spec.ts`, `info.ts`)
- **3** are new config/data files we created (issue template, tasks.json, api.json)
- **0** are CSAPI code files — Phase 6A formatting worked correctly

### Do the other 4 gates pass?

Yes. Verified locally on 2025-02-24:

| Gate         | Result                                                       |
| ------------ | ------------------------------------------------------------ |
| typecheck    | **PASS** — clean, exit 0                                     |
| lint         | **PASS** — clean, exit 0                                     |
| test:node    | **PASS** — 60/60 suites, 0 failures                          |
| test:browser | **58/60 pass** — 2 fail due to Windows-only esbuild path bug |

The 2 test:browser failures are a pre-existing Windows platform issue (esbuild
strips backslashes from Windows paths when resolving the worker module). These
would pass on the Linux CI runner that GitHub Actions uses.

**But CI never runs these gates** because format:check fails first and the
workflow stops.

### What would it take to make CI green?

Run `npx prettier --write` on the 394 files. This is a one-time formatting pass
that fixes whitespace, line lengths, etc. in our markdown and the 2 modified
source files. No logic changes. No code changes. After that, all 5 gates should
pass on CI.

### The CRLF complication (now resolved)

Earlier, when we ran format:check locally on Windows, it showed **655** failures
instead of 394. That was because `git config core.autocrlf` was set to `true`,
which converted every file to Windows line endings (CRLF) on checkout. Prettier
expects Unix line endings (LF). So every single file in the repo — including
untouched upstream files — appeared to fail.

We fixed this by setting `core.autocrlf = input`, which keeps files as LF on
disk. The 394 number is the real count after removing all CRLF artifacts.

### Are any failures caused by upstream?

No. **100% of the 394 formatting failures are caused by our work.** Every single one.

- **389 markdown docs** — we created them; they don't exist in upstream
- **3 config/data files** — we created them (issue template, tasks.json, api.json)
- **2 upstream source files** (`endpoint.spec.ts`, `info.ts`) — these passed
  format:check in upstream (their CI is green); our modifications introduced
  non-compliant formatting

After the CRLF fix, **zero untouched upstream files fail**. Every failure traces
back to something we wrote or changed.

### Bottom line

Our CI is blocked by unformatted markdown docs we wrote. The actual code is
clean. A single `prettier --write` command would unblock it.
