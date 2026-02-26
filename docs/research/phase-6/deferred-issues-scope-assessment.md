# Deferred Issues — Phase 6 Scope Assessment

**Date:** 2025-02-23
**Branch:** `phase-6`
**Author:** AI Agent (Phase 6 research)
**Purpose:** Evaluate whether any of the 5 open deferred issues should be pulled into Phase 6 scope

---

## Phase 6 Acceptance Gate (Reference)

From jahow's PR #136 feedback and the [P6 Contribution Goal](../../../docs/planning/phase-6/P6-contribution-goal-and-definition.md):

1. **CSAPI not in root `index.ts`** — import via `@camptocamp/ogc-client/csapi`
2. **Nothing outside `csapi/` imports from `csapi/`**
3. **CI passes** (tests, tsc, lint)

Phase 6 is a **structural/architectural change** — reorganizing module boundaries and entry points. It does **not** touch CSAPI business logic, method behavior, or feature additions.

---

## Issue Assessments

### #98 — `parseCommandStatus` `@see` link precision (F18)

| Attribute             | Value                                                                                                                                   |
| --------------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| **Labels**            | documentation, parser, phase-5                                                                                                          |
| **Category**          | JSDoc cosmetic                                                                                                                          |
| **What**              | `parseCommandStatus()` JSDoc `@see` references `#_command_resources` instead of `#clause-commandstatus-resource`                        |
| **Phase 6 relevance** | None. Phase 6 doesn't touch parser JSDoc. The existing anchor follows the consistent naming convention used across the entire codebase. |
| **Risk if included**  | Near-zero, but also near-zero value toward jahow's requirements.                                                                        |
| **Verdict**           | **CONTINUE DEFERRING.** Cosmetic JSDoc fix unrelated to module boundaries.                                                              |

---

### #100 — `assertResourceAvailable()` overly strict for per-ID methods

| Attribute               | Value                                                                                                                                                                                                                                       |
| ----------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Labels**              | bug, interoperability                                                                                                                                                                                                                       |
| **Category**            | URL builder behavior                                                                                                                                                                                                                        |
| **What**                | 69 per-ID methods block valid URL construction for nested-only resources (Part 2 servers like OSH SensorHub). `assertResourceAvailable()` conflates "can I list all resources?" with "can I construct a URL for a specific resource by ID?" |
| **Phase 6 relevance**   | None. URL builder assertion behavior is internal CSAPI logic. Phase 6 moves the module to a separate entry point — it doesn't change how the builder validates resources.                                                                   |
| **Risk if included**    | **CRITICAL.** 69 method changes + 57+ test updates. Would dwarf the P6 diff and completely derail the contribution.                                                                                                                         |
| **Existing workaround** | `resourceUrls` constructor parameter is the designed escape hatch (documented in F-100.3).                                                                                                                                                  |
| **Verdict**             | **CONTINUE DEFERRING.** Documented workaround exists. Too invasive for a structural PR.                                                                                                                                                     |

---

### #102 — Command/observation CRUD methods require top-level endpoints

| Attribute             | Value                                                                                                                                                                           |
| --------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Labels**            | bug, url-builder                                                                                                                                                                |
| **Category**          | URL builder behavior (subset of #100)                                                                                                                                           |
| **What**              | 14 command/observation per-ID methods fail on nested-only servers. Strict subset of #100 — same root cause (`assertResourceAvailable()` guard), same `resourceUrls` workaround. |
| **Phase 6 relevance** | None. Same orthogonality to module boundary work as #100.                                                                                                                       |
| **Risk if included**  | **HIGH.** Fixing 14 methods independently while leaving 55 others creates an inconsistent partial fix (the issue's own findings report calls this out explicitly).              |
| **Verdict**           | **CONTINUE DEFERRING** alongside #100 for holistic post-contribution resolution of all 69 per-ID methods.                                                                       |

---

### #110 — No `@link`/`@id` resolution utilities for cross-resource reference following

| Attribute             | Value                                                                                                                                                                                                                                                                                  |
| --------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Labels**            | enhancement                                                                                                                                                                                                                                                                            |
| **Category**          | Feature addition (new code)                                                                                                                                                                                                                                                            |
| **What**              | Library lacks utilities for resolving `@link` cross-reference fields into fetchable resources. Proposes `resolveResourceRef()`, `parseResourceRefHref()`, `extractCrossReferences()`, `resolveWithLinkFallback()` in a new `link-resolution.ts` file.                                  |
| **Phase 6 relevance** | None. This is a **feature addition** (new files, new functions, new tests). Phase 6 is about reorganizing existing code, not expanding functionality.                                                                                                                                  |
| **Risk if included**  | **HIGH.** The issue's own findings report recommends "DO NOT IMPLEMENT" — it would introduce `fetch()` into the parse-and-build layer, violating architectural layering. Issues #108/#109 already resolved the root cause (typed `@link` fields now survive parsing and are exported). |
| **Verdict**           | **CONTINUE DEFERRING.** Resolution is consumer responsibility. The library correctly parses and exposes `@link` data; fetching is ~5 lines per field for consumers.                                                                                                                    |

---

### #111 — `getCommandStatus()` uses string concatenation instead of `buildResourceUrl()` (F45)

| Attribute             | Value                                                                                                                                                                                                                 |
| --------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Labels**            | implementation, phase-5                                                                                                                                                                                               |
| **Category**          | Internal pattern consistency                                                                                                                                                                                          |
| **What**              | One method uses `+ this.buildQueryString(options)` instead of passing `options` through `buildResourceUrl()`. Zero functional impact — both approaches produce identical URLs.                                        |
| **Phase 6 relevance** | None. Internal URL builder implementation detail.                                                                                                                                                                     |
| **Risk if included**  | Low risk, but the issue's own deferral rationale states: _"F45 doesn't move the needle"_ for acceptance likelihood. F46 (type narrowing) and F47 (missing combined test) were assessed as higher-value for reviewers. |
| **Verdict**           | **CONTINUE DEFERRING.** Pattern deviation that produces correct output. Not worth including in a structural PR.                                                                                                       |

---

## Summary Matrix

| Issue | Domain                 | Relevance to P6       | Risk if Included                  | Recommendation |
| ----- | ---------------------- | --------------------- | --------------------------------- | -------------- |
| #98   | JSDoc                  | None                  | Near-zero                         | **Defer**      |
| #100  | URL builder assertions | None                  | Critical (69 methods + 57+ tests) | **Defer**      |
| #102  | URL builder assertions | None (subset of #100) | High (inconsistent partial fix)   | **Defer**      |
| #110  | Feature addition       | None                  | High (layer violation)            | **Defer**      |
| #111  | Pattern consistency    | None                  | Low but pointless                 | **Defer**      |

---

## Rationale

All 5 issues operate in the **CSAPI internal business logic layer** (url_builder.ts, parsers, helpers), while Phase 6 operates exclusively at the **module boundary/entry point layer** (index.ts, package.json, new csapi/ barrel export).

There is **zero overlap** between any deferred issue and Phase 6's scope.

Including any of them would:

1. **Expand the PR diff** — mixing structural changes with behavioral changes
2. **Make jahow's review harder** — he needs to verify the decoupling is clean, not audit URL builder assertion logic
3. **Increase regression risk** — especially #100/#102 which touch 69 methods and 57+ tests
4. **Violate minimum-change principle** — Phase 6's commit strategy (Plan 08) was designed to be the smallest diff that satisfies jahow's three requirements

**Conclusion:** All 5 deferred issues should remain deferred. Phase 6 proceeds with its current scope as defined in the [P6 Contribution Goal](../../../docs/planning/phase-6/P6-contribution-goal-and-definition.md).
