# Phase 2 Implementation Lessons Learned

**Purpose:** Actionable lessons extracted from Phase 1–2.8 code reviews, smoke tests, and fix reports. Every remaining Phase 2 issue (Issues #7–#13) **must** be read alongside this document. These are not suggestions — they are guardrails derived from mistakes we actually made and documented. Six consecutive defect-free phases (2.3–2.8) validate that these lessons work as intended.

**Version:** 1.2  
**Date:** February 14, 2026  
**Source documents:**

- `docs/implementation/phase-1-code-review.md` (Findings F1–F9)
- `docs/implementation/phase-1-fix-report.md` (Fixes for F1, F5)
- `docs/implementation/phase-2.2-code-review.md` (Findings F1–F15, Root Cause Analysis)
- `docs/implementation/live-server-smoke-test-post-phase-2.1.md` (5 server findings)
- `docs/implementation/live-server-smoke-test-post-phase-2.2.md` (Validation of fixes)
- `docs/implementation/live-server-smoke-test-52north.md` (52North comparative test)
- `docs/implementation/cross-server-interoperability-analysis.md` (Cross-server analysis)
- `docs/implementation/phase-2.3-code-review.md` (Procedures — zero defects)
- `docs/implementation/live-server-smoke-test-post-phase-2.3.md` (Procedures smoke test)
- `docs/implementation/phase-2.4-code-review.md` (SamplingFeatures — zero defects)
- `docs/implementation/live-server-smoke-test-post-phase-2.4.md` (SamplingFeatures smoke test)
- `docs/implementation/phase-2.5-code-review.md` (Properties — zero defects)
- `docs/implementation/live-server-smoke-test-post-phase-2.5.md` (Properties smoke test)
- `docs/implementation/phase-2.6-code-review.md` (DataStreams — zero defects)
- `docs/implementation/live-server-smoke-test-post-phase-2.6.md` (DataStreams smoke test)
- `docs/implementation/phase-2.7-code-review.md` (Observations — zero defects)
- `docs/implementation/live-server-smoke-test-post-phase-2.7.md` (Observations smoke test)
- `docs/implementation/phase-2.8-code-review.md` (ControlStreams — zero defects)
- `docs/implementation/live-server-smoke-test-post-phase-2.8.md` (ControlStreams smoke test)

---

## How to Use This Document

When working on any Phase 2 issue (#7–#13):

1. **Read this document first** — before reading the issue body
2. **Use the test checklist** in Lesson 1 as a mandatory gate before marking the issue complete
3. **Check the query options table** in Lesson 2 to confirm which parameters apply to your resource type
4. **Check the temporal keys note** in Lesson 3 if your resource type has temporal parameters
5. **Verify the resource type string** per Lesson 4 in every `assertResourceAvailable()` call
6. **Do not create new files** per Lesson 5 — all work goes into existing files
7. **Smoke test against both servers** per Lesson 8 — OpenSensorHub (auth required, ask for credentials) and 52North
8. **Do not modify code during smoke tests** per Lesson 10 — report findings, then create issues for fixes

---

## Lesson 1: Test Thoroughness Decays Across Resource Types

**What happened:** Systems (Issue #5, the first resource type) got thorough tests — exact URL assertions with `toBe()`, per-field query option tests, nested resource pagination tests. Deployments (Issue #6, the second resource type) got weaker tests — `toContain()` instead of `toBe()` for datetime, missing tests for `parent`/`recursive` query options, no pagination test for subdeployments.

**Root cause:** "Second-resource-type syndrome" — the first implementation gets careful attention, the second gets "it follows the same pattern, so it's fine." The pattern was copied but not the thoroughness.

**Why it matters:** This compounds. By the seventh resource type, tests could be skeletal if not actively guarded against.

**Mandatory test checklist for every resource type:**

For each resource type being implemented, the test suite must include:

- [ ] **Collection query with exact URL assertion** — use `toBe()`, not `toContain()`
- [ ] **Every query option field** that applies to this resource type gets its own test (check the table in Lesson 2)
- [ ] **Single resource retrieval** (`get{Resource}(id)`) with exact URL
- [ ] **CRUD operation URLs** (`create`, `update`, `delete`) — at minimum verify the base URL and ID placement
- [ ] **Each nested/association method** gets at least one test with exact URL
- [ ] **At least one nested method with pagination + filtering** (e.g., `{ limit: 5, offset: 10 }`) to verify query params pass through
- [ ] **Resource validation failure** — calling any method when the resource type is NOT in `availableResources` throws `EndpointError`
- [ ] **Temporal parameters** (if applicable) use exact `toBe()` assertions on the serialized ISO 8601 string, not `toContain()`

---

## Lesson 2: Each Resource Type Has Different Query Options

**What happened:** Query options were over-copied from Systems when implementing Deployments, and some resource-specific fields were not tested because they looked "similar enough."

**Why it matters:** Each resource type has a distinct set of applicable query parameters. Copying tests from a previous resource type and changing the method name is not sufficient — you must verify the correct fields for _this_ resource type.

**Query parameter applicability (from the Implementation Guide §6):**

| Parameter            | Systems | Deployments | Procedures | SamplingFeatures | Properties | DataStreams | Observations | ControlStreams | Commands |
| -------------------- | ------- | ----------- | ---------- | ---------------- | ---------- | ----------- | ------------ | -------------- | -------- |
| `id`                 | ✅      | ✅          | ✅         | ✅               | ✅         | ✅          | ✅           | ✅             | ✅       |
| `uid`                | ✅      | ✅          | ✅         | ✅               | ✅         | ✅          | —            | ✅             | —        |
| `q` (keyword)        | ✅      | ✅          | ✅         | ✅               | ✅         | ✅          | —            | ✅             | —        |
| `bbox`               | ✅      | ✅          | —          | ✅               | —          | —           | —            | —              | —        |
| `datetime`           | ✅      | ✅          | —          | ✅               | —          | ✅          | ✅           | ✅             | ✅       |
| `limit`              | ✅      | ✅          | ✅         | ✅               | ✅         | ✅          | ✅           | ✅             | ✅       |
| `offset`             | ✅      | ✅          | ✅         | ✅               | ✅         | ✅          | —            | —              | —        |
| `cursor`             | —       | —           | —          | —                | —          | —           | ✅           | ✅             | ✅       |
| `f` (format)         | ✅      | ✅          | ✅         | ✅               | ✅         | ✅          | ✅           | ✅             | ✅       |
| `parent`             | ✅      | ✅          | —          | —                | —          | —           | —            | —              | —        |
| `recursive`          | ✅      | ✅          | —          | —                | —          | —           | —            | —              | —        |
| `system`             | —       | —           | —          | —                | —          | ✅          | —            | ✅             | —        |
| `procedure`          | ✅      | —           | —          | —                | —          | ✅          | —            | ✅             | —        |
| `foi`                | —       | —           | —          | —                | —          | ✅          | ✅           | —              | —        |
| `observedProperty`   | —       | —           | —          | —                | —          | ✅          | —            | —              | —        |
| `controlledProperty` | —       | —           | —          | —                | —          | —           | —            | ✅             | —        |
| `phenomenonTime`     | —       | —           | —          | —                | —          | —           | ✅           | —              | —        |
| `resultTime`         | —       | —           | —          | —                | —          | —           | ✅           | —              | —        |
| `issueTime`          | —       | —           | —          | —                | —          | —           | —            | —              | ✅       |
| `executionTime`      | —       | —           | —          | —                | —          | —           | —            | —              | ✅       |

**Action:** Before writing tests, consult this table. Write one test for each ✅ in your resource type's column.

---

## Lesson 3: Temporal Keys Are Hardcoded in `buildQueryString`

**What happened:** Phase 1 code review finding P1-F6 identified that temporal parameter keys are hardcoded in `buildQueryString()`:

```typescript
if (key === 'datetime' || key === 'phenomenonTime' || key === 'resultTime' || key === 'issueTime' || key === 'executionTime') {
```

**Why it matters:** This list must include every temporal key that any resource type's query options might pass. If a new temporal key is added to a `QueryOptions` interface but not to this condition, the value will be serialized as a raw string (e.g., `[object Object]`) instead of a formatted ISO 8601 string.

**Current temporal keys in the condition:** `datetime`, `phenomenonTime`, `resultTime`, `issueTime`, `executionTime`.

**Action:**

- Issues #7–#9 (Procedures, SamplingFeatures, Properties): These resource types do NOT add new temporal keys. No changes needed to `buildQueryString`.
- Issues #10–#13 (DataStreams, Observations, ControlStreams, Commands): These introduce `phenomenonTime`, `resultTime`, `issueTime`, `executionTime`. **Verify** that each temporal key used in your `QueryOptions` interface is already present in the `buildQueryString` condition. If it's not, flag it — do not add it yourself (that's infrastructure, owned by Issue #3's scope).

---

## Lesson 4: Verify `assertResourceAvailable` Uses the Correct String

**What happened:** This is a latent risk identified during code review. Every public method starts with:

```typescript
this.assertResourceAvailable('systems');
```

When copying Systems methods to create Deployments methods, it's easy to change the method name but forget to change the resource type string.

**Why it matters:** If `getProcedures()` calls `this.assertResourceAvailable('systems')` instead of `this.assertResourceAvailable('procedures')`, it will silently check access for the wrong resource — the method appears to work but validates against the wrong capability.

**Action:** After implementing all methods for a resource type, grep for the resource type string to verify every method uses the correct one:

- `procedures` for Issue #7
- `samplingFeatures` for Issue #8
- `properties` for Issue #9
- `datastreams` for Issue #10
- `observations` for Issue #11
- `controlStreams` for Issue #12
- `commands` for Issue #13

---

## Lesson 5: All Work Goes Into Existing Files

**What happened:** Phase 1–2.2 established that all Phase 2 resource-type methods are added to the same two files: `url_builder.ts` and `url_builder.spec.ts`. There is a temptation to create separate files per resource type, or to add parsers, response types, or Phase 3 concerns prematurely.

**Why it matters:** Creating new files increases merge complexity, splits related logic, and crosses issue scope boundaries.

**Action for every Phase 2 issue:**

- Methods go into `src/ogc-api/csapi/url_builder.ts` (modify only)
- Tests go into `src/ogc-api/csapi/url_builder.spec.ts` (modify only)
- Do NOT create new `.ts` files
- Do NOT modify `model.ts`, `helpers.ts`, `endpoint.ts`, `info.ts`, or `index.ts`
- Do NOT add response parsing, data transformation, or Phase 3 concerns

---

## Lesson 6: Review Findings Must Become Work Items

**What happened:** The Phase 1 code review identified P1-F4 (missing exports) with the recommendation "fix before Phase 2." Phase 2 then proceeded through four issues without addressing it. The finding was documented but never converted to a tracked work item.

**Why it matters:** Reviews are only useful if findings get tracked. A documented finding without an issue or task is a finding that gets forgotten.

**Action:** After completing each Phase 2 issue, if any unexpected behavior, design concern, or potential improvement is noticed during implementation, note it as a comment on the issue (not just in a commit message or conversation). It will be reviewed and converted to an issue if warranted.

---

## Lesson 7: DRY Violations Compound Across Issues

**What happened:** Issues #34 and #35 were implemented back-to-back in the same session. Issue #34 wrote 3-convention link scanning in `extractAvailableResources()`. Issue #35, implemented immediately after, needed the same logic for `extractRootResourceUrls()` — but duplicated it instead of extracting a shared helper. This was fixed in Issue #38.

**Why it matters:** Each issue is naturally treated as an isolated unit of work. When the same logic appears in the issue you just closed, the reflex is "that's done, don't touch it" instead of "that's shared infrastructure, extract it."

**Action:** If your implementation requires logic that already exists in a method from a previous issue, do NOT duplicate it. Instead:

1. If the existing logic can be called directly, call it
2. If it needs to be extracted into a shared helper, flag it as a comment on the issue — do not make the extraction yourself (that crosses issue scope)
3. Do not copy-paste method bodies and change names/strings — this is the #1 source of DRY violations in our history

---

## Lesson 8: Single-Server Testing Creates False Confidence

**What happened:** We ran three smoke tests (Phase 2.1, 2.2, 2.3) against a single server (OpenSensorHub). All three declared Convention 3 link detection working. Two real bugs — query params in hrefs breaking segment extraction, and `featuresOfInterest` not matching our `samplingFeatures` resource type — were invisible because OpenSensorHub doesn't use either pattern. It took a second server from a different vendor (52North) to expose them.

**Why it matters:** A single server exercises one implementation's conventions. Real interoperability bugs hide in the gaps between implementations. Three smoke tests against the same server gave us false confidence that discovery was solid.

**Action:** Every phase-end smoke test should hit both live servers:

- **OpenSensorHub** (`http://45.55.99.236:8080/sensorhub/api`) — requires Basic auth. Credentials are NOT stored in the repository. If you have forgotten them, ask the human collaborator.
- **52North** (`https://csa.demo.52north.org/`) — no auth, but requires `-SkipCertificateCheck` (expired SSL cert).

---

## Lesson 9: "Works By Luck" Is a Bug

**What happened:** Convention 3 parsing works on 52North _only_ because HTML links (no query params) happen to appear before JSON links (with query params) in the server's response. If link ordering changed, discovery would silently break. The code produced correct output for the wrong reason.

**Why it matters:** Code that succeeds due to incidental conditions (response ordering, favorable data shapes, specific server behavior) is fragile. It passes tests and smoke tests but breaks when assumptions shift.

**Action:** When testing against live servers, look for cases where our code succeeds — then ask _why_ it succeeds. If the answer depends on response ordering or other incidental server behavior, that's a latent bug to track.

---

## Lesson 10: Smoke Tests Are Read-Only — Fixes Come Through Issues

**What happened:** The 52North smoke test revealed two real bugs in `scanCsapiLinks()`. Rather than fixing them immediately during the smoke test, we documented them in the smoke test report, discussed the findings, assessed upstream impact, and then created a tracked issue (#39) with a scoped fix plan.

**Why it matters:** Smoke tests exist to observe and report, not to drive code changes directly. If we fix bugs during the smoke test itself, we bypass the discussion → assessment → scoping workflow that prevents premature or poorly scoped changes. Our established process is:

1. **Complete the phase work** — implement per the issue scope
2. **Run the smoke test** — observe, do not modify code
3. **Write the report** — document findings with evidence
4. **Discuss** — determine what's ours vs. upstream, assess impact
5. **Create issues** — scope fixes with acceptance criteria and constraints
6. **Implement fixes** — per the new issue, with tests

**Action:** Never modify source code as a result of a smoke test finding without first going through steps 3–5. Smoke test reports must not include code changes — they are documentation artifacts only.
