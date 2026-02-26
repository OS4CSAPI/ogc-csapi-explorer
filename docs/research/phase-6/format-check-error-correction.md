# Format Check Investigation: Error Correction

**Date:** 2025-02-24
**Branch:** `phase-6`
**Purpose:** Honest accounting of what was stated incorrectly, what is actually
proven, and what remains unknown

---

## Every wrong thing stated during this investigation, in order

1. **"605 files fail, all pre-existing upstream"** — Wrong. Not checked. Assumed.
2. **"The QA workflow is dead on arrival, nothing provides value"** — Wrong. Said
   this based on local Windows results without looking at upstream's actual CI logs.
3. **"Upstream fails their own format:check on 605 files"** — Wrong. Upstream
   passes on CI. The failures were observed locally and blamed on upstream without
   verification.
4. **"Fork divergence caused the failures"** — Misleading. A theory was invented
   before the evidence was checked.

Each of these was stated with confidence. Each was wrong.

---

## What is actually proven with evidence

These things were verified with direct evidence:

- `core.autocrlf = true` on this Windows machine. Git converts LF → CRLF on
  checkout.
- Prettier 2.8.8 defaults `endOfLine` to `lf`. It sees CRLF on disk. It flags it.
- Upstream CI passes on Linux (`ubuntu-latest`) where there is no CRLF conversion.
- **Every single one of the 655 local failures includes CRLF as a contributing
  factor.** From a local Windows run, it is impossible to tell which files also have
  real formatting issues underneath the CRLF noise. The CRLF masks everything.

---

## What is genuinely not known

- **How many files would fail on CI (Linux).** This number is not 655. It is not 605.
  It is not 439. All numbers derived from the local Windows output are contaminated by
  CRLF and tell us nothing about real formatting failures.
- **Whether our CSAPI files would pass on CI.** Phase 6A ran `prettier --write` which
  should have fixed them, and the correct content is in the git blobs (verified: 0 CR
  bytes in blob). Probably yes, but it has not been proven on a Linux environment.
- **Whether our markdown docs, fixtures, and other new files would fail on CI.**
  Probably some would. The count is unknown.

---

## The one thing that would give actual answers

Fix the CRLF issue locally (`git config core.autocrlf input` + re-checkout), then run
`format:check` again. The number that comes back would be the **real** number — the
same failures CI would see. Right now we are looking at noise and attempting to
interpret noise as signal.

The CRLF issue should have been identified first, fixed, and THEN the results
analyzed — instead of building a tower of conclusions on contaminated data.

---

## Process failure

The core mistake was running full speed ahead with confident conclusions before
establishing clean data. Each wrong conclusion led to the next wrong conclusion,
creating a chain of compounding errors that wasted time and eroded trust. The correct
approach would have been:

1. Observe unexpected result (655 failures)
2. Question whether the test environment is clean
3. Identify the CRLF contamination
4. Fix the environment
5. Re-run to get clean data
6. THEN analyze and draw conclusions

Steps 2–4 were skipped. Steps 5–6 were attempted on dirty data.

---

## Resolution Options Considered

### Option: CI-only formatting checks (rule-based)

Make a rule that formatting is only ever verified through the GitHub Actions QA
workflow, never locally. This guarantees results match the upstream environment
(Ubuntu, LF line endings).

**Advantages:**

- 100% accurate — same OS, same line endings, same environment as upstream
- No need to change local git config
- Simple rule

**Disadvantages:**

- Slow feedback loop — push, wait 40-60s, read logs for every check
- Burns GitHub Actions minutes on every push
- If `format:check` fails, it kills all subsequent steps (typecheck, lint, tests) —
  one unformatted markdown file blocks visibility into test results
- Debugging requires push-wait-read cycles instead of instant local iteration

### Option: Fix `core.autocrlf` locally (one-time fix)

Set `core.autocrlf = input` for this repo, then re-checkout files. This makes local
results match CI results.

**Advantages:**

- Fast local feedback — instant results
- Local and CI agree on what passes and fails
- One-time 30-second fix

**Disadvantages:**

- Requires trusting that the fix actually works (verifiable after applying)

### Decision

Apply the `core.autocrlf input` fix locally as the immediate resolution. CI remains
the authoritative source of truth for all QA gates, but the local fix enables fast
feedback during development. The two approaches are not mutually exclusive.
