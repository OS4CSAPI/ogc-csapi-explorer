# Phase 5 Findings Coverage Analysis

**Date:** February 19, 2026  
**Purpose:** Cross-reference smoke test findings flagged as "fixable issues" within CSAPI client library scope against the Phase 5 ROADMAP to identify what is covered and what remains.  
**Source Documents:**

- [P5 ROADMAP v1.1](../planning/phase-5/P5-ROADMAP.md)
- [Smoke Test #19 (Post Phase 4.1)](live-server-smoke-test-post-phase-4.1.md)
- [Server Quirks Reference](server-quirks-reference.md)

**See also:**

- [Deferred Findings — Final Disposition](deferred-findings-final-disposition.md) for definitive verdicts on all 6 findings not covered by P5.
- [P4 Findings: Code vs Documentation Reassessment](p4-findings-code-vs-docs-reassessment.md) for the analysis confirming documentation-only is the correct approach for P4-F1/P4-F2.

---

## Findings Under Review

The following findings were assessed as being within scope and lane for the CSAPI client library contribution — i.e., they are "fixable issues" from the library's perspective:

| Finding | Description                                                                          | Category                       |
| ------- | ------------------------------------------------------------------------------------ | ------------------------------ |
| P4-F2   | OSH PUT rejects uid changes — stricter than documented                               | CRUD correctness               |
| F82     | OSH items envelope sometimes has no `links` key                                      | Pagination / envelope handling |
| F5      | Missing pagination metadata (`numberMatched`/`numberReturned`)                       | Pagination handling            |
| P4-F1   | Command POST hangs — connection never returns                                        | CRUD / command lifecycle       |
| F84     | 52N procedure `featureType: sosa:Sensor` misclassified as System                     | Classification                 |
| F14     | Properties not discoverable via any link detection convention                        | Discovery / link scanning      |
| F27     | Observation `foi@id` abbreviated notation                                            | Part 2 data shape              |
| F30     | ControlStream `system@link` cross-reference                                          | Part 2 data shape              |
| F31     | Command entity data shape (`controlstream@id`)                                       | Part 2 data shape              |
| F33     | ControlStream schema returns SWE DataRecord (`commandFormat`/`parametersSchema`)     | Part 2 data shape              |
| F38     | CommandStatus data shape (`command@id`, `reportTime`, `statusCode`, `executionTime`) | Part 2 data shape              |

---

## What the P5 ROADMAP Covers

The P5 ROADMAP is scoped to **9 parser gaps** — building parse functions that transform raw JSON into typed TypeScript objects for 6 resource types, 2 schema response types, and 1 recursive delegation fix. It covers **5 of the 11 findings** above:

| Finding | What P5 Covers                                                                          | P5 Task     | GitHub Issue                                                                                                                     |
| ------- | --------------------------------------------------------------------------------------- | ----------- | -------------------------------------------------------------------------------------------------------------------------------- |
| **F27** | `parseObservation()` handles the `foi@id` field shape tolerantly                        | Task 3      | [#81](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/81)                                                                  |
| **F30** | `parseControlStream()` extracts fields from this data shape                             | Task 4      | [#82](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/82)                                                                  |
| **F31** | `parseCommand()` models this data shape                                                 | Tasks 5a/5b | [#83](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/83), [#84](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/84) |
| **F33** | `parseControlStreamSchemaResponse()` handles `commandFormat`/`parametersSchema` variant | Task 7b     | [#87](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/87)                                                                  |
| **F38** | `parseCommandStatus()` models `command@id`, `reportTime`, `statusCode`, `executionTime` | Task 6      | [#85](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/85)                                                                  |

These 5 findings (F27, F30, F31, F33, F38) are **directly addressed** by Phase 5 — they are the data shapes the parsers are being built to handle.

---

## What Remains After P5

Six findings are **not covered** by the P5 ROADMAP:

| Finding   | Description                                     | Why Not in P5                                                                   | Current Status (ST#19)                | Recommended Target                                                            |
| --------- | ----------------------------------------------- | ------------------------------------------------------------------------------- | ------------------------------------- | ----------------------------------------------------------------------------- |
| **P4-F2** | OSH PUT rejects uid changes                     | CRUD/write-path concern, not a parser gap                                       | Moderate — new Phase 4 finding        | JSDoc issue ([#92](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/92)) |
| **F82**   | OSH items envelope sometimes omits `links`      | Already mitigated — `parseCollectionResponse()` defaults to `[]`                | Confirmed Low — no code change needed | None (resolved)                                                               |
| **F5**    | Missing pagination metadata                     | Pagination touches upstream `shared`/`ogc-api` code — out of scope              | Deferred                              | None (out of scope)                                                           |
| **P4-F1** | Command POST hangs (OSH holds connection open)  | CRUD/write-path concern — needs timeout strategy or SSE-aware handler           | Moderate — new Phase 4 finding        | JSDoc issue ([#93](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/93)) |
| **F84**   | 52N procedure misclassification (`sosa:Sensor`) | Upstream server bug, reported, fallback already works — no remaining work       | Deferred — still present              | None (complete)                                                               |
| **F14**   | Properties not discoverable via links           | Server-side gap — scanner is spec-correct, workaround exists, no remaining work | Deferred — still present              | None (complete)                                                               |

### Disposition Summary

| Category                                 | Count  | Findings                |
| ---------------------------------------- | ------ | ----------------------- |
| **Covered by P5**                        | 5      | F27, F30, F31, F33, F38 |
| **Phase 4 CRUD concerns (JSDoc issues)** | 2      | P4-F1, P4-F2            |
| **Already mitigated (no action needed)** | 3      | F82, F84, F14           |
| **Out of scope (upstream concern)**      | 1      | F5                      |
| **Total**                                | **11** |                         |

---

## Observations

1. **Phase 5 cleanly addresses the Part 2 data shape findings.** All 5 data shape findings (F27, F30, F31, F33, F38) map directly to parser tasks in the P5 ROADMAP. Once Phase 5 is complete, the library will have typed parse functions for every CSAPI resource shape observed in smoke testing.

2. **The two Phase 4 findings (P4-F1, P4-F2) are CRUD concerns — confirmed as JSDoc-only after reassessment.** They were discovered during Smoke Test #19's first CRUD testing pass. After initial scope assessment, both resolved to JSDoc documentation additions. This conclusion was subsequently challenged and re-examined against the library's full architecture (which includes write-path helpers like `getContentTypeForResource()`, deep response parsers, and `fetchDocument()` integration — not just URL construction). The reassessment confirmed: P4-F2's uid check is trivial and belongs in consumer code, not a library validator; P4-F1's root cause is CSAPI Part 2 spec-correct streaming behavior, where the real fix would be a streaming response client — a standalone feature outside contribution scope. Both issues (#92, #93) remain correctly scoped as documentation-only. See [P4 Findings: Code vs Documentation Reassessment](p4-findings-code-vs-docs-reassessment.md) for the full analysis.

3. **F82 requires no further action.** The `parseCollectionResponse()` function already defaults `links` to an empty array when the key is absent. This was confirmed as "Low" severity in ST#19.

4. **Three findings (F5, F14, F84) remain deferred.** Each would need its own scoped issue:
   - **F5 (pagination):** Would require enhancing how the library surfaces `numberMatched`/`numberReturned` to consumers.
   - **F14 (properties discovery):** No remaining work — see clarification below.
   - **F84 (procedure misclassification):** No remaining work — see clarification below.

> **⚠️ Note on F5 (pagination):** F5 is risky because pagination touches `shared` and `ogc-api` — that's upstream territory. If we change how pagination detection works to handle missing `links` keys, we risk breaking WMS/WFS/WMTS pagination. F5 should not have been included on the "fixable issues" list. It is either an upstream change or needs very careful scoping to avoid regressions in non-CSAPI endpoints.

> **✅ Note on F84 (procedure misclassification):** After thorough review, F84 requires no further work. The root cause is upstream (52North returns `sosa:Sensor` for procedures — reported as [Issue #16](https://github.com/52North/connected-systems-pygeoapi/issues/16)). Our `classifyFeature()` already provides an endpoint-context fallback ([Issue #50](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/50)). The only theoretical fix — letting endpoint hints override featureType — would break classification for spec-compliant servers. The misclassification affects one resource on one server and will auto-resolve when 52North fixes their data. See [Deferred Findings — Final Disposition](deferred-findings-final-disposition.md#f84--52n-procedure-misclassification) for the full analysis.

> **✅ Note on F14 (properties not discoverable):** After thorough review, F14 requires no further work. `properties` is already in our `CSAPIResourceTypes` list and `scanCsapiLinks()` already checks all three OGC link conventions for it. The gap is server-side — neither OSH nor 52North includes a properties link in their documents. The workaround already exists: consumers can use the `resourceUrls` parameter or call `getProperties()` directly. The only theoretical fix — speculative URL probing — would be inconsistent with the upstream library's design and could cause unexpected 404s. See [Deferred Findings — Final Disposition](deferred-findings-final-disposition.md#f14--properties-not-discoverable-via-links) for the full analysis.
