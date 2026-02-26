# Lessons Learned: CI Formatting Check Failure on PR #136

**Date:** 2026-02-23
**PR:** [camptocamp/ogc-client#136](https://github.com/camptocamp/ogc-client/pull/136)
**Severity:** Low (cosmetic, not correctness)
**Status:** Pending fix

---

## What happened

After pushing the 13-commit `clean-pr` branch to the upstream draft PR, the repository's **Quality Assurance** CI workflow ran and failed at the first step: `npm run format:check` (Prettier).

The CI pipeline runs 5 steps sequentially:

1. `npm run format:check` — **Failed here; pipeline halted**
2. `npm run typecheck` — Never reached
3. `npm run lint` — Never reached
4. `npm run test:browser` — Never reached
5. `npm run test:node` — Never reached

Prettier flagged **279 files** as having formatting inconsistencies. Of these, **57 are our CSAPI files** and **5 are our modified upstream files**. The remaining 217 are existing upstream files that also don't match (Prettier checks everything in the repo, not just the diff).

The workflow is defined in [`.github/workflows/qa.yml`](https://github.com/camptocamp/ogc-client/blob/main/.github/workflows/qa.yml) and triggers on `pull_request: [opened, synchronize, ready_for_review]`.

## What did NOT happen

- **No tests failed.** No test was executed at all — the pipeline stopped before reaching the test steps.
- **No type errors.** `tsc --noEmit` was never reached but passes locally (verified).
- **No lint errors.** ESLint was never reached.
- **No correctness issue.** All 1,285 CSAPI tests and 82/83 endpoint tests pass locally. The code is functionally correct.

## Why we missed it

Our pre-submission verification process was thorough on **correctness** but did not include the upstream CI's **style enforcement** step:

| What we verified           | Tool                                       | Result                         |
| -------------------------- | ------------------------------------------ | ------------------------------ |
| Type safety                | `tsc --noEmit`                             | 0 errors                       |
| CSAPI unit tests           | `npx jest --testPathPattern="csapi"`       | 1,285 passing (29 suites)      |
| Endpoint integration tests | `npx jest -- endpoint.spec.ts`             | 82/83 passing (1 pre-existing) |
| CSAPI endpoint tests       | `npx jest -t "CSAPI"`                      | 6/6 passing                    |
| Rebase integrity           | `git diff main clean-pr -- src/ fixtures/` | Zero diff                      |
| Live server smoke tests    | Manual against OSH + 52°North              | 25 sessions, all passing       |

| What we did NOT verify  | Tool                    | Would have caught      |
| ----------------------- | ----------------------- | ---------------------- |
| **Prettier formatting** | `npm run format:check`  | **This failure**       |
| ESLint rules            | `npm run lint`          | Unknown (likely clean) |
| Full CI pipeline        | All 5 steps in sequence | Everything             |

The root cause is simple: we never ran `npm run format:check` or the equivalent `npx prettier --check .` against the upstream's Prettier configuration (v2.8.8 with their `.prettierrc.json`). Our development process used our own editor formatting settings, which differ from upstream's rules.

## Impact assessment

**On the PR:** The red CI badge is visible but expected for a draft PR. The maintainer (jahow) has not commented on the formatting failure — his feedback is focused on architecture (separate entry point for CSAPI). The formatting failure does not affect his willingness to accept the contribution.

**On our credibility:** Minimal. Formatting issues are universally understood as trivial. Every contributor encounters this on their first PR to a new repo. However, fixing it promptly signals professionalism.

**On the code:** Zero. Prettier reformatting is a mechanical, content-preserving transformation. It changes whitespace, line breaks, quote styles, and trailing commas. It does not alter any logic, types, or behavior. All 1,285 tests will continue to pass after formatting.

## Fix

The fix is a single command:

```sh
npx prettier --write "src/ogc-api/csapi/**" "src/index.ts" "src/ogc-api/endpoint.ts" "src/ogc-api/endpoint.spec.ts" "src/ogc-api/info.ts" "src/shared/mime-type.ts" "src/shared/mime-type.spec.ts" "fixtures/ogc-api/csapi/**" ".gitignore"
```

This will be included in our next push, which will also address jahow's architectural feedback (separate `@camptocamp/ogc-client/csapi` entry point).

**Note:** We should only format files we changed. Reformatting upstream's existing files would pollute the diff and is not our responsibility.

## Process improvement

### Pre-push checklist addition

Before pushing to any upstream PR, run the **full CI pipeline locally**:

```sh
npm run format:check   # Prettier style conformance
npm run typecheck      # TypeScript compilation
npm run lint           # ESLint rules
npm run test:browser   # Jest browser tests
npm run test:node      # Jest Node.js tests
```

If any step fails, fix it before pushing. This exactly mirrors the upstream CI and ensures no surprises.

### Why this wasn't in our process before

Our development workflow was oriented around the archive repo (`ogc-client-CSAPI_2`), which doesn't have the same CI pipeline. We had our own verification gates (code reviews, smoke tests, type checks, unit tests) but these were scoped to correctness, not upstream style conformance.

The rebase process (documented in [`02-rebase-plan.md`](02-rebase-plan.md)) focused on producing a clean commit history on the correct base. It did not include a "run upstream CI locally" step. It should have.

### For future contributions

1. **Clone or check the target repo's CI workflow early** — before starting development, not just before submission
2. **Run `npm run format:check` after every rebase** — formatting can drift when cherry-picking or rebasing commits
3. **Add format enforcement to local development** — consider adding a Prettier config that matches upstream, or a pre-commit hook
4. **Treat CI as the source of truth** — local test passes are necessary but not sufficient; the full CI pipeline is the real gate
