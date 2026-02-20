# Library Findings Scope Assessment — Cross-Repository Issue Triage

> **Date:** 2026-02-20
> **Context:** Issues #11, #13, #15, #17, #18, #19 on `OS4CSAPI/ogc-csapi-explorer` were originally filed as library enhancement/bug findings discovered during demo app development. Each was assessed by the CSAPI_2 library maintainer instance to determine whether it was in scope for the `ogc-client-CSAPI_2` upstream contribution.

---

## Background

During the development of the CSAPI Explorer demo app (`demo/`), 17+ findings were documented where the demo app's integration with the ogc-client CSAPI library revealed friction points, missing conveniences, or behavioral surprises. These findings were catalogued in the [upstream findings document](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/upstream-findings.md) and individual GitHub issues were created on the explorer repository.

Six of these issues (#11, #13, #15, #17, #18, #19) targeted the **ogc-client CSAPI library source code** (`src/ogc-api/csapi/`), not the demo app. To determine whether these should be actioned in the library, each was submitted to the CSAPI_2 library maintainer instance for independent assessment against:

- The OGC specifications (primary authority)
- The [AI Operational Constraints](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/governance/AI_OPERATIONAL_CONSTRAINTS.md) governing the library contribution
- The library's architectural boundary (URL builder, not HTTP client)
- Upstream ogc-client precedent and patterns
- The library fork's conservation record (exactly 1 source commit with zero behavioral impact)

---

## Consolidated Verdicts

| Explorer Issue | Finding | Type | Library Verdict | Rationale Summary |
|---|---|---|---|---|
| [#11](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/11) — Generic CRUD methods | F-7 | Enhancement | **DEFER** | New abstraction layer; no upstream precedent; consumer-solvable boilerplate; AI Constraints §2.2 triggered |
| [#13](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/13) — Type guard functions | F-9 | Enhancement | **DO NOT ADD** | `getCSAPIResourceType()` already provides discriminator; consumer-solvable in 4 lines; zero upstream type guard exports |
| [#15](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/15) — parseLocationHeader() | F-12 | Enhancement | **DEFER** | Lowest-priority actionable finding (#10/11); library is URL builder not response parser; one-liner workaround |
| [#17](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/17) — Schema response parser | F-14 | Enhancement | **DEFER** | One-line consumer workaround (`data?.resultSchema ?? data`); would break conservation record; mixes OGC spec modules |
| [#18](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/18) — Empty-body 201 response | F-15 | Bug (consumer) | **NO ACTION** | Zero HTTP response handling code in CSAPI module; crash was in demo app's `apiFetch()` wrapper; already fixed |
| [#19](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/19) — uid in PUT payloads | F-16 | Bug (consumer) | **NO ACTION** | Library doesn't construct request payloads; `uid` already required on all Part 1 type interfaces |

---

## Common Thread: Architectural Boundary

The ogc-client CSAPI module is a **pure URL builder**. Its public API consists of:

- **`CSAPIQueryBuilder`** — Constructs URLs for all 9 CSAPI resource types. Its 82+ public methods return URL strings. It never calls `fetch()`.
- **`parseCollectionResponse()`** — Parses already-deserialized JSON objects (takes `unknown`, not `Response`).
- **`parseSWEComponent()`** — Parses already-deserialized SWE Common JSON objects.
- **`extractCSAPIFeature()` / `getCSAPIResourceType()`** — Operate on already-deserialized GeoJSON objects.

A comprehensive search of `src/ogc-api/csapi/**` confirms:

| Pattern | Matches |
|---|---|
| `response.json()` | 0 |
| `fetch(` | 0 |
| `response.text()` | 0 |
| `payload` | 0 |
| `body` | 0 |

All 6 issues describe concerns that fall outside this boundary — HTTP response handling (#18), request payload construction (#19), consumer DX wrappers (#11, #13), response parsing (#15, #17).

---

## Verdict Categories Explained

### DEFER (Issues #11, #15, #17)

These enhancements are technically valid but should not be included in the initial upstream CSAPI contribution PR. Rationale:

1. **Conservation record** — The library fork has exactly 1 source commit (`e73cff8`) with zero behavioral impact. Adding convenience utilities degrades this integrity marker.
2. **No upstream precedent** — No other ogc-client module (WMS, WFS, WMTS, STAC, EDR) provides generic dispatch methods, response header parsing, or response envelope extraction utilities. Adding them only to CSAPI creates asymmetry.
3. **AI Operational Constraints §2.2** — "Do not introduce new abstractions, layers, or dependencies without approval." All three DEFER issues would add new exported functions with no internal callers.
4. **Post-acceptance opportunity** — After the core CSAPI module is accepted upstream, these enhancements can be proposed as follow-up PRs with upstream maintainer input on placement and design.

### DO NOT ADD (Issue #13)

Type guard functions are **actively recommended against**, not just deferred:

- The library already exports `getCSAPIResourceType()` which provides the exact discriminator consumers need
- Any consumer can write their own type guards in 4 lines using existing exports
- The upstream library has **zero** type guard exports across all modules
- The guards would add 4 new public API surface functions purely for convenience

### NO ACTION REQUIRED (Issues #18, #19)

These issues describe problems that literally cannot exist in the library:

- **#18 (empty-body 201)** — The library contains zero HTTP response handling code. The crash was in the demo app's `apiFetch()` wrapper.
- **#19 (uid requirement)** — The library's update methods (`updateSystem(id)`) return URL strings only. They don't construct request bodies. The `uid: string` field is already non-optional on all Part 1 interfaces.

---

## Findings Reports

Each issue received a detailed findings report from the library maintainer instance, stored in the CSAPI_2 repository:

| Issue | Findings Report |
|---|---|
| #11 (F-7) | [issue-11-generic-crud-methods.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/testing/demo-app-findings/issue-11-generic-crud-methods.md) |
| #13 (F-9) | [issue-13-type-guard-functions-for-union-narrowing.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/testing/demo-app-findings/issue-13-type-guard-functions-for-union-narrowing.md) |
| #15 (F-12) | [issue-15-parse-location-header.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/testing/demo-app-findings/issue-15-parse-location-header.md) |
| #17 (F-14) | [issue-17-schema-response-parser.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/testing/demo-app-findings/issue-17-schema-response-parser.md) |
| #18 (F-15) | [issue-18-empty-body-201-response.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/testing/demo-app-findings/issue-18-empty-body-201-response.md) |
| #19 (F-16) | [issue-19-uid-requirement-in-put-payloads.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/testing/demo-app-findings/issue-19-uid-requirement-in-put-payloads.md) |

Each report follows the same structure: AI Constraints Acknowledgment, Executive Summary, Issue Description, Source Code Review, Reference Document Review (12+ documents per report), Risk Assessment, Analysis, and Recommendation with rationale.

---

## Actions Taken

All 6 issues were closed on `OS4CSAPI/ogc-csapi-explorer` as **not planned** with closing comments referencing the findings reports:

- **#11** — Closed 2026-02-20 (DEFER — new abstraction, no upstream precedent)
- **#13** — Closed 2026-02-20 (DO NOT ADD — consumer-solvable, existing discriminator)
- **#15** — Closed 2026-02-20 (DEFER — lowest priority, trivial workaround)
- **#17** — Closed 2026-02-20 (DEFER — one-line workaround, conservation record)
- **#18** — Closed 2026-02-20 (NO ACTION — not a library issue)
- **#19** — Closed 2026-02-20 (NO ACTION — not a library issue)

---

## Remaining Open Issues

After this triage, the explorer repository has **1 open issue**:

| Issue | Description | Status |
|---|---|---|
| [#40](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/40) — Animate edge on navigation | Visual polish: animate/highlight the data model diagram edge when navigating between resource types | Open — nice-to-have, low priority |

---

## Process Note

This cross-repository triage demonstrates the separation of concerns between the two project workspaces:

- **`ogc-csapi-explorer`** — Demo app, data model diagram, documentation. Issues targeting the demo UI, diagram features, and app-level behavior belong here.
- **`ogc-client-CSAPI_2`** — The CSAPI client library contribution to upstream ogc-client. Issues targeting library source code (`src/ogc-api/csapi/`) are assessed there against the AI Operational Constraints and upstream contribution strategy.

Findings discovered during demo development are valuable — they document real consumer friction. But the appropriate resolution may be "consumer-side workaround" rather than "library modification," especially when the library's architectural boundary (URL builder) doesn't encompass the concern (HTTP response/request handling).
