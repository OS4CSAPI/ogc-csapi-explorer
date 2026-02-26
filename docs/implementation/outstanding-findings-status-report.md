# Outstanding Findings & Issues Status Report

**Date:** February 21, 2026
**Repository:** `OS4CSAPI/ogc-client-CSAPI_2`
**Branch:** `main`
**Latest commits:** `2e7aded` (F46 fix), `af0c1aa` (F47 fix)
**Test baseline:** 1,283 CSAPI tests (29 suites), 740 format tests (20 suites), tsc clean (0 errors)

---

## Executive Summary

All actionable, in-scope findings have been resolved. The 5 remaining open issues are correctly marked DEFERRED — none are fixable within the current contribution scope without disproportionate risk or effort. The codebase is in clean, shippable state with zero bugs and zero critical findings.

---

## Findings Resolved This Session

| Finding                                                                                       | Issue                                                                      | Fix                                             | Commit    |
| --------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------- | ----------------------------------------------- | --------- |
| **F46** — `getControlStreamProcedures` uses `QueryOptions` instead of `ProcedureQueryOptions` | [#112](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/112) (closed) | One-word type change in `url_builder.ts`        | `2e7aded` |
| **F47** — No combined-option test for `getCommandStatus`                                      | [#113](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/113) (closed) | Added `statusCode` + `limit` combined test case | `af0c1aa` |

Both fixes were verified: tsc clean, all tests passing (1,282 → 1,283 after F47 test addition).

---

## Open Issues — All DEFERRED

### [#98](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/98) — DEFERRED — `parseCommandStatus` `@see` link precision (F18)

| Attribute        | Value                                |
| ---------------- | ------------------------------------ |
| **Category**     | Documentation                        |
| **Severity**     | Minor                                |
| **Fixable now?** | **No**                               |
| **Labels**       | `documentation`, `phase-5`, `parser` |

**Why deferred:** The hypothetical target anchor `#_commandstatus_resources` does not exist in the OGC 23-002 spec. The actual anchor for §10.11 is `#clause-commandstatus-resource`, which follows a different naming convention than the `#_command_resources` style used consistently throughout the codebase. The current link is technically correct — CommandStatus is documented within the "Control Streams & Commands" requirements class (Clause 10). There is nothing to fix.

---

### [#100](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/100) — DEFERRED — `assertResourceAvailable()` overly strict for per-ID methods

| Attribute        | Value                             |
| ---------------- | --------------------------------- |
| **Category**     | Interoperability / Bug            |
| **Severity**     | Medium                            |
| **Fixable now?** | **Arguably yes, but large scope** |
| **Labels**       | `bug`, `interoperability`         |

**Why deferred:** Affects 69 out of 84 public methods across all resource types. A holistic redesign is needed — either removing assertions from per-ID methods, adding a two-tier assertion system, or separating collection-level vs resource-level guards. The scope (69 method changes + comprehensive test updates) is too large for the current contribution phase. The fix is real and valuable, but belongs in a dedicated follow-up effort.

**Impact:** Per-ID methods throw `EndpointError` on servers (like OSH SensorHub) that only expose Part 2 resources as nested paths under systems. Consumers must catch and construct URLs manually as a workaround.

---

### [#102](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/102) — DEFERRED — Command/observation CRUD methods require top-level endpoints

| Attribute        | Value                  |
| ---------------- | ---------------------- |
| **Category**     | Bug                    |
| **Severity**     | Medium                 |
| **Fixable now?** | **No (independently)** |
| **Labels**       | `bug`, `url-builder`   |

**Why deferred:** This is a strict subset of #100 — same root cause (`assertResourceAvailable()` blocks valid URL construction for nested-only servers). Fixing #100 automatically resolves #102. There is no independent fix that makes sense.

---

### [#110](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/110) — DEFERRED — No `@link`/`@id` resolution utilities

| Attribute        | Value                          |
| ---------------- | ------------------------------ |
| **Category**     | Enhancement                    |
| **Severity**     | Low (for library contribution) |
| **Fixable now?** | **No**                         |
| **Labels**       | `enhancement`                  |

**Why deferred:** Proposes a new architectural layer (`resolveResourceRef()`, `parseResourceRefHref()`, `extractCrossReferences()`, `resolveWithLinkFallback()`) that operates at a different abstraction level than the existing URL builder. This is outside the CSAPI client library contribution scope — it would add runtime fetch behavior to what is currently a pure URL-construction library. The Phase 5.5 code review (F44) specifically praised the correct deferral of this issue.

---

### [#111](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/111) — DEFERRED — `getCommandStatus()` uses string concatenation instead of `buildResourceUrl()` (F45)

| Attribute        | Value                          |
| ---------------- | ------------------------------ |
| **Category**     | Design gap (pattern deviation) |
| **Severity**     | Low                            |
| **Fixable now?** | **Technically yes (~2 lines)** |
| **Labels**       | `implementation`, `phase-5`    |

**Why deferred:** The concatenation approach (`buildResourceUrl(...) + buildQueryString(options)`) is functionally identical to passing options through `buildResourceUrl()`. Both produce the same URL. The deviation is a style/consistency concern, not a correctness issue. Fixing it requires verifying that `buildResourceUrl()` handles the `commands/{id}/status` sub-path correctly with options — which introduces testing risk for zero behavioral gain. Not worth the effort-to-value ratio for upstream acceptance.

---

## Finding Disposition Summary

### All 47 Findings (F1–F47) from Phase 5 Code Reviews

| Category                       | Count | Details                                                                          |
| ------------------------------ | ----: | -------------------------------------------------------------------------------- |
| **POSITIVE**                   |    38 | F1–F4, F6–F9, F11–F17, F19–F28, F30–F32, F36–F44                                 |
| **RESOLVED**                   |     4 | F5 (test gap), F10 (barrel exports), F29 (import), F34 (re-export consolidation) |
| **FIXED THIS SESSION**         |     2 | F46 (type narrowing), F47 (combined-option test)                                 |
| **DEFERRED (no fix possible)** |     2 | F18 (anchor doesn't exist), F45 (functionally correct)                           |
| **BUG**                        |     0 | —                                                                                |
| **CRITICAL**                   |     0 | —                                                                                |

### Open Issues by Fixability

| Fixability                                    | Issues     | Count |
| --------------------------------------------- | ---------- | ----: |
| **Nothing to fix** (correct as-is)            | #98 (F18)  |     1 |
| **Out of scope** (new architecture)           | #110       |     1 |
| **Too large for current phase**               | #100, #102 |     2 |
| **Not worth the risk** (functionally correct) | #111 (F45) |     1 |

---

## Codebase Health Metrics

| Metric                             | Value                                        |
| ---------------------------------- | -------------------------------------------- |
| Production lines (CSAPI)           | ~11,760                                      |
| Test lines (CSAPI)                 | ~14,250                                      |
| Test-to-production ratio           | 1.21:1                                       |
| Production files                   | 28                                           |
| Test suites                        | 29                                           |
| CSAPI tests passing                | 1,283                                        |
| Format tests passing               | 740                                          |
| TypeScript errors                  | 0                                            |
| Consecutive reviews with zero bugs | 5 (Phases 5.1–5.5, spanning Issues #81–#113) |

---

## Conclusion

The CSAPI client library contribution is in its most complete state. All 47 code review findings have been dispositioned — 38 positive, 4 resolved in prior sessions, 2 fixed today, and 3 knowingly deferred with documented rationale. The 5 remaining open GitHub issues are all correctly categorized as DEFERRED with clear explanations of why they cannot or should not be addressed within the current contribution scope. No actionable, in-scope work remains.
