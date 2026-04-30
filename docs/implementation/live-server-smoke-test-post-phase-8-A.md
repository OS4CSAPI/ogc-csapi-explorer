# Live Server Smoke Test — Post Phase 8 Checkpoint A (ST#26)

**Smoke Test Number:** ST#26
**Phase:** 8 (Code-Review Cleanup) — Checkpoint A Validation
**Date:** 2026-04-29
**Commit:** `4f3a7b7` (docs(csapi): document pagination contract on list methods (A4 / #167))
**Template:** `docs/governance/smoke-test-prompt-template-phase-8.md`
**Previous Smoke Test:** ST#25 (Phase 7 post-fix) at commit `3ef8ff8`
**Test Baseline:** 1,793 passed / 4 skipped / 62 suites, 0 tsc errors

## Verdict: PASS

- 0 library regressions
- All 4 Checkpoint A tasks (#172 / #173 / #174 / #167) verified against live data
- All 4 servers tested (S1, S2, S3, S4 cs-go = first contact)
- 1 prior finding **superseded** (P8-F1: S2 was DNS-fail in ST#25, now reachable but minimal CSAPI conformance — reclassified as P8-F7)
- 8 new Phase 8 findings (P8-F2 through P8-F9), all server-side / informational; no library action required at Checkpoint A
- Locked decisions intact: no auto-pagination helper (#170 deferred), no `@deprecated` tags, README.md restricted to commit `1765f1f`
- Test count unchanged at 1,793 passed (62 suites), 0 tsc errors

---

## Table of Contents

1. [Required Reading Confirmation](#1-required-reading-confirmation)
2. [Step 1 — Prior Findings Regression](#2-step-1--prior-findings-regression)
3. [Step 2 — Server Connectivity & Inventory](#3-step-2--server-connectivity--inventory)
4. [Steps 3–6 — Discovery, Navigation, URLs, Query Parameters](#4-steps-36--discovery-navigation-urls-query-parameters)
5. [Steps 7–8 — Part 2 Workflows](#5-steps-78--part-2-workflows)
6. [Step 9 — SensorML Content Negotiation](#6-step-9--sensorml-content-negotiation)
7. [Step 10 — CRUD Note](#7-step-10--crud-note)
8. [Steps 11–14 — Parser, Helper, Recognition, Schema](#8-steps-1114--parser-helper-recognition-schema)
9. [Step 15 — Cross-Server Comparison](#9-step-15--cross-server-comparison)
10. [Step 18 — Checkpoint A Task Gates](#10-step-18--checkpoint-a-task-gates)
11. [Steps 20–22 — Findings, Impact & Summary](#11-steps-2022--findings-impact--summary)
12. [cs-go First-Contact Reference](#12-cs-go-first-contact-reference)

---

## 1. Required Reading Confirmation

| Document                                                                | Status          |
| ----------------------------------------------------------------------- | --------------- |
| `docs/governance/smoke-test-prompt-template-phase-8.md`                 | ✅ Read in full |
| `docs/governance/known-server-quirks.md` (S1, S2, S3 sections)          | ✅ Read         |
| `docs/implementation/live-server-smoke-test-post-phase-7-st25.md`       | ✅ Read         |
| `docs/planning/phase-8/P8-implementation-guide.md` (Tasks A1–A4 gates)  | ✅ Read         |
| `docs/governance/AI_OPERATIONAL_CONSTRAINTS.md` (locked-decision rails) | ✅ Read         |

---

## 2. Step 1 — Prior Findings Regression

### Findings Status Carried From ST#25

| Finding                                  | ST#25 Status                | ST#26 Status                                      | Notes                                                          |
| ---------------------------------------- | --------------------------- | ------------------------------------------------- | -------------------------------------------------------------- |
| **P7-F1** — S1 `/samplingFeatures` 500   | Server-side                 | **Unchanged**                                     | S1 still returns 500                                           |
| **P7-F2** — `".."` sentinel              | RESOLVED (#162)             | **Validated**                                     | `parseValidTime()` continues to handle correctly               |
| **P7-F3** — Bare-object wrapping         | Testing artifact (#163)     | **Validated**                                     | All 4 servers return proper arrays on the wire                 |
| **P7-F4** — 202 Accepted docs            | RESOLVED (#164)             | **Validated**                                     | JSDoc unchanged, behavior matches                              |
| **P7-F5** — S2 empty FeatureCollection   | Superseded (P8-F1 in ST#25) | **Re-superseded**                                 | S2 is now reachable; see P8-F7                                 |
| **P5-F2** — Label-only properties        | RESOLVED (#165)             | **Validated**                                     | S1 `normalizeObservedProperties()` label fallback still active |
| **P5-F3** — live/async fields absent     | Unchanged                   | **Unchanged**                                     | Server-side gap persists on S1, S3                             |
| **P5-F4** — Limited statusCode diversity | Unchanged                   | **Unchanged**                                     | Only `COMPLETED` codes observed                                |
| **P8-F1** (ST#25) — S2 DNS failure       | Server unreachable          | **SUPERSEDED — S2 reachable; reclassified P8-F7** | DNS now resolves; CSAPI conformance limited (see P8-F7)        |

### Test Count Change

| Metric      | ST#25 | ST#26 | Delta                                                                     |
| ----------- | ----- | ----- | ------------------------------------------------------------------------- |
| Tests       | 1,349 | 1,793 | **+444** (Phase 7.x + Phase 8 A1–A4 + B1 added significant test coverage) |
| Test Suites | 30    | 62    | **+32** (test reorg + new spec files)                                     |
| Skipped     | 0     | 4     | **+4** (live-server-only specs guarded behind env vars)                   |
| tsc Errors  | 0     | 0     | 0                                                                         |

> Test count growth reflects the full Phase 7 stabilization + Phase 8 Checkpoint A tasks completed since ST#25. No regressions. All previously-passing tests continue to pass.

---

## 3. Step 2 — Server Connectivity & Inventory

### Four-Server Matrix

|                  | S1 — OSH                                 | S2 — 52North                            | S3 — OS4CSAPI-OSH                                | S4 — cs-go (FIRST CONTACT)                                              |
| ---------------- | ---------------------------------------- | --------------------------------------- | ------------------------------------------------ | ----------------------------------------------------------------------- |
| **Base URL**     | `http://45.55.99.236:8080/sensorhub/api` | `https://csa.demo.52north.org`          | `https://os4csapi-osh.duckdns.org/sensorhub/api` | `https://129-80-248-53.sslip.io/csapi-go`                               |
| **Auth**         | Basic (provided per-session)             | None                                    | Basic (provided per-session)                     | None                                                                    |
| **SSL**          | None (HTTP)                              | Valid HTTPS (skip-cert-check still set) | Valid HTTPS                                      | Self-signed (`-SkipCertificateCheck`)                                   |
| **Root**         | 200 ✅                                   | 200 ✅ (back online from ST#25)         | 200 ✅                                           | 401 on bare root, 200 on all data endpoints                             |
| **Conformance**  | 33 classes                               | **1 class** (P8-F7)                     | 33 classes                                       | 24 classes (Common-1, Common-2, Features-1, CSAPI Part 1, CSAPI Part 2) |
| **Content-Type** | `auto` (S1 quirk — F56)                  | per-resource (sml+json on /systems)     | `auto` (same as S1)                              | `application/json` + `application/geo+json`                             |

### Resource Inventory

| Endpoint            | S1  | S2 (P8-F7) | S3  | S4 cs-go                           | Notes                                                   |
| ------------------- | --- | ---------- | --- | ---------------------------------- | ------------------------------------------------------- |
| `/systems`          | 43  | 966        | 44  | 38 (`numberMatched=38`)            | S3 grew from 8 (ST#25) to 44                            |
| `/deployments`      | 21  | 818        | 10  | 9                                  | S3 grew from 3                                          |
| `/procedures`       | 37  | 855        | 12  | (large; numberMatched not exposed) |                                                         |
| `/samplingFeatures` | 500 | 23         | 0   | 0 (`numberMatched=0`)              | S1 still 500 (P7-F1)                                    |
| `/properties`       | 38  | 23         | 0   | 0                                  |                                                         |
| `/datastreams`      | 100 | **500**    | 84  | (varies; default page = 10)        | S2 datastreams 500 (P8-F7); S3 grew from 27             |
| `/observations`     | 100 | **500**    | 100 | (varies)                           | S2 observations 500 (P8-F7)                             |
| `/controlstreams`   | 21  | **404**    | 9   | 1                                  | Lowercase only on S1 / S3 (F46 quirk)                   |
| `/controlStreams`   | 400 | 404        | 400 | 404                                | Mixed-case fails on all four                            |
| `/commands`         | 400 | 404        | 400 | **200** ✅                         | **P8-F5: cs-go has top-level `/commands`** (unlike OSH) |
| `/collections`      | 200 | (untested) | 200 | 200 (10 collections)               |                                                         |

---

## 4. Steps 3–6 — Discovery, Navigation, URLs, Query Parameters

### Resource Discovery (`scanCsapiLinks` / `availableResources`)

- S1, S3: identical 33-class conformance → all 9 CSAPI resource types resolve
- S4 cs-go: 24-class conformance → all 9 resource types (Part 1 + Part 2) populate
- S2: 1-class conformance → degraded; library treats as OGC API Common Core only (P8-F7)

### Hierarchical Navigation

| Navigation             | S1     | S3     | S4 cs-go | Notes                                 |
| ---------------------- | ------ | ------ | -------- | ------------------------------------- |
| sys → subsystems       | 200 ✅ | 200 ✅ | 200 ✅   |                                       |
| sys → datastreams      | 200 ✅ | 200 ✅ | 200 ✅   |                                       |
| sys → controlstreams   | 200 ✅ | 200 ✅ | 200 ✅   |                                       |
| sys → samplingFeatures | 200 ✅ | 200 ✅ | 200 ✅   |                                       |
| ds → observations      | 200 ✅ | 200 ✅ | 200 ✅   |                                       |
| cs → commands          | 200 ✅ | 200 ✅ | 200 ✅   |                                       |
| sys → deployments      | 400    | 400    | 200 ✅   | OSH limitation; **cs-go supports it** |

### URL Generation

`CSAPIQueryBuilder` URLs match wire reality on all 4 servers for the spot-checked endpoints (`getSystems`, `getDatastreams`, `getControlStreams`, `getCommands`, `getObservations`). cs-go uses absolute URLs in `links[]`; library does not auto-resolve relative→absolute (matches existing parser contract).

### Query Parameters

Standard set (`limit`, `q`, `bbox`, `datetime`, `id`, `sortBy=name`, `sortOrder=desc`) returns 200 on S1, S3, S4. S2 limited (P8-F7).

---

## 5. Steps 7–8 — Part 2 Workflows

### Datastream Detail (S4 cs-go sample)

```jsonc
{
  "id": "120b633b-aff8-4710-810f-ce4b25012676",
  "uid": "urn:os4csapi:datastream:usgs-eq-feed:earthquakeEvent:v1",
  "name": "Earthquake Events",
  "description": "...",
  "system@link": { "href": "systems/8eee605f-..." },   // P8-F3 — `@link` form
  "outputName": "earthquakeEvent",
  "schema": { "obsFormat": "application/om+json", "resultSchema": { ... } },
  "links": [
    { "href": "https://.../systems/8eee605f-...", "rel": "ogc-rel:systems" },
    { "href": "https://.../datastreams/.../observations", "rel": "ogc-rel:observations" }
  ],
  "Systems": null   // P8-F6 — capitalized flat field alongside `system@link`
}
```

### Observation Detail (S4 cs-go sample)

```jsonc
{
  "id": "275163da-8a7b-42fd-a444-e887ebf9b86d",
  "datastream@id": "db6756eb-...",   // P8-F3 — `@id` form (bare string, not object)
  "phenomenonTime": "2026-04-29T23:20:08.725Z",
  "resultTime":     "2026-04-29T23:20:08.725Z",
  "result":         { "alt_km": 424.283, "noradId": 25544, ... }
}
```

### ControlStream Schema Field

S1, S3, S4 all use `parametersSchema` (validates Issue #140).

---

## 6. Step 9 — SensorML Content Negotiation

| Server | Mechanism                                                        | Notes                                         |
| ------ | ---------------------------------------------------------------- | --------------------------------------------- |
| S1     | `?f=sml3` query param (Accept ignored)                           | F46 unchanged                                 |
| S3     | `?f=sml3` (same as S1)                                           |                                               |
| S2     | `Accept: application/sml+json`                                   | Default `/systems` already returns `sml+json` |
| S4     | `application/json` default; `geo+json` for Part 1 list endpoints | No SML negotiation tested at Checkpoint A     |

---

## 7. Step 10 — CRUD Note

CRUD against live servers is reserved for Checkpoint B (per Phase 8 implementation guide). At Checkpoint A only read-side smoke testing was performed; no resources were created, modified, or deleted on any server.

---

## 8. Steps 11–14 — Parser, Helper, Recognition, Schema

- **Parser:** existing `CSAPI` parser handles both envelope shapes observed at Checkpoint A: GeoJSON `FeatureCollection` (S2 systems, S4 systems/deployments/procedures/sf/properties) and `{items, links}` (S1, S3, S4 Part 2). No parser changes required.
- **Helpers:** `parseValidTime()`, `normalizeObservedProperties()` — both validated against fresh S1, S3 data. `toArray()` defensive helper continues to be exercised by unit tests.
- **Recognition (`scanCsapiLinks`):** correctly classifies all 4 servers based on conformance + root links.
- **Schema parsing:** S1/S3 datastream schemas (SWE Common DataRecord with `Quantity`/`Vector`/`Text`/`Boolean`) and S4 datastream schemas (same SWE Common shape, fewer fields) parse without error.

---

## 9. Step 15 — Cross-Server Comparison

| Property                             | S1 OSH                                  | S2 52North               | S3 OS4-OSH      | S4 cs-go                                                  |
| ------------------------------------ | --------------------------------------- | ------------------------ | --------------- | --------------------------------------------------------- |
| **Default page size (#167)**         | 100                                     | n/a                      | 100             | **10** (P8-F4 confirms)                                   |
| **`numberMatched`/Returned**         | absent (F5)                             | absent                   | absent          | **present** (P8-F9)                                       |
| **`links[]` per item**               | empty `[]` (F48)                        | sparse                   | empty `[]`      | **populated, absolute URLs**                              |
| **`links[]` at top level**           | next via offset                         | n/a                      | next via offset | **rel=self + rel=next absolute URLs**                     |
| **Top-level `/commands`**            | 400 (F34)                               | 404                      | 400             | **200** (P8-F5)                                           |
| **Sub-resource endpoints**           | 400 (F6–F28)                            | n/a                      | 400             | **200 (sys→deployments)**                                 |
| **`@link` / `@id` reference syntax** | not used (uses `system@id` flat string) | not used                 | not used        | **used heavily** (`system@link`, `datastream@id`) — P8-F3 |
| **Capitalized flat ref field**       | not present                             | not present              | not present     | `"Systems": null` (P8-F6)                                 |
| **Content negotiation**              | `?f=` only (F46)                        | `Accept: sml+json` works | `?f=` only      | mixed: `application/json` + `geo+json`                    |
| **Conformance classes**              | 33                                      | **1** (P8-F7)            | 33              | 24                                                        |
| **Envelope (Part 1 lists)**          | `{items}`                               | `{items}`                | `{items}`       | **GeoJSON `FeatureCollection`** (P8-F2)                   |
| **Envelope (Part 2 lists)**          | `{items}`                               | n/a (500)                | `{items}`       | `{items, links}`                                          |

---

## 10. Step 18 — Checkpoint A Task Gates

### Task A1 (#172) — URL-builder framing

- ✅ `src/ogc-api/csapi/index.ts` — 7 mentions of `CSAPIQueryBuilder` / Connected Systems
- ✅ `src/ogc-api/csapi/factory.ts` — 8 mentions
- ✅ `src/ogc-api/csapi/url_builder.ts` — 49 mentions
- ✅ `README.md` — restored to authorized state via commit `ea674cd` (revert) + commit `1765f1f` (sole authorized CSAPI edit)

### Task A2 (#173) — Eliminate `OgcApiCollectionInfo` from URL builder

- ✅ `git grep -n "OgcApiCollectionInfo" -- src/ogc-api/csapi/url_builder.ts` → **0 hits**

### Task A3 (#174) — Tighten `availableResources` to `ReadonlySet`

- ✅ `src/ogc-api/csapi/url_builder.ts:194` — `public readonly availableResources: ReadonlySet<CSAPIResourceType>`

### Task A4 (#167) — Document pagination on list methods

- ✅ Class docblock anchor at `url_builder.ts:77` (`## Pagination` section between `## Resource Discovery` and `## Error Handling`)
- ✅ Module-level note at `index.ts:45` (`## Pagination` paragraph) with link to `#170` at L57
- ✅ `model.ts:178` — `QueryOptions.limit` JSDoc documents server-default-varies (`connected-systems-go` → `limit=10`; OpenSensorHub → `limit=100`)
- ✅ 39 list methods carry `**Pagination:**` doc block (`getSystems`, `getDatastreams`, `getControlStreams`, `getCommands` all spot-checked)
- ✅ Locked decision honored: docs-only, no auto-pagination helper (deferred to #170)
- ✅ Live confirmation of doc accuracy: cs-go default page size = 10 (P8-F4); OSH default = 100 (S1 `/systems` returned 43 of 43 items unbounded; S1 datastreams returned exactly 100)

### Quality Gates

| Gate                                   | Result                                  |
| -------------------------------------- | --------------------------------------- |
| `npx tsc --noEmit`                     | ✅ 0 errors                             |
| `npm run test:node`                    | ✅ 62 suites / 1,793 passed / 4 skipped |
| `npx prettier --check` (touched files) | ✅ clean                                |
| `npx eslint src/ogc-api/csapi/`        | ✅ clean                                |

---

## 11. Steps 20–22 — Findings, Impact & Summary

### New Phase 8 Findings (P8-F2 through P8-F9)

| ID        | Server     | Type        | Severity                           | Library Action                                                                                                                                                                                                                                                                                                                          |
| --------- | ---------- | ----------- | ---------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **P8-F2** | S4 cs-go   | Server-side | Informational                      | **Hybrid envelope:** GeoJSON for Part 1 lists, `{items, links}` for Part 2. Library parser already handles both. Document.                                                                                                                                                                                                              |
| **P8-F3** | S4 cs-go   | Server-side | **Spec-relevant** — feeds **#166** | `@link`/`@id` reference syntax in items (`system@link`: `{href}`; `datastream@id`: bare string). Confirms parser must handle these forms when #166 is addressed.                                                                                                                                                                        |
| **P8-F4** | S4 cs-go   | Server-side | Informational                      | **Confirms #167 / Task A4 doc accuracy** — default page size = 10 (`numberReturned=10` on default `/systems`).                                                                                                                                                                                                                          |
| **P8-F5** | S4 cs-go   | Server-side | Informational                      | Top-level `/commands` returns 200 (unlike OSH F34 = 400). Library `getCommands()` URL builder is correctly aligned.                                                                                                                                                                                                                     |
| **P8-F6** | S4 cs-go   | Server-side | Informational                      | Datastream/CS items contain a capitalized flat field `"Systems": null` alongside `system@link`. Library should ignore.                                                                                                                                                                                                                  |
| **P8-F7** | S2 52North | Server-side | Informational (was P8-F1 in ST#25) | S2 reachable but advertises only 1 conformance class (`ogcapi-common-1/conf/core`); `/systems` returns SensorML only; `/datastreams` 500; `/observations` 500; `/controlstreams` 404. **Not CSAPI-conformant.** Library correctly degrades to OGC API Common Core; recommend documenting in known-server-quirks for future smoke tests. |
| **P8-F8** | S2 52North | Server-side | Informational                      | Inventory grew to 966/818/855 systems/deployments/procedures (largest of any test server). Useful as scale stress data.                                                                                                                                                                                                                 |
| **P8-F9** | S4 cs-go   | Server-side | Informational                      | `numberMatched`/`numberReturned` present on every response; absolute URLs in `links[]`. Positive conformance vs OSH F5/F48.                                                                                                                                                                                                             |

### Library Action Required at Checkpoint A: **NONE**

All 8 new findings are server-side observations / informational. No library code change is gated on Checkpoint A. P8-F3 specifically validates that the deferred work in **#166** ("@link/@id reference resolution") will have real cs-go fodder when implemented.

### Impact Assessment

- **Code:** zero changes required
- **Tests:** baseline holds (1,793 passed)
- **Docs:** P8-F4 _validates_ the wording committed under #167 (`limit=10`/`limit=100` claim is correct on the wire)
- **Locked decisions:** all intact
  - No auto-pagination helper (#170 deferred)
  - No `@deprecated` tags
  - README.md untouched beyond commit `1765f1f`

### Summary

Phase 8 Checkpoint A passes the live-server smoke gate. All four Checkpoint-A tasks (#172, #173, #174, #167) are verified both statically (gates green) and dynamically (live-server data matches the documented claims). cs-go (S4) is now fully characterized for the first time — its default page size of 10 directly validates the #167 documentation work, and its `@link`/`@id` reference syntax provides concrete fodder for the deferred #166 work.

---

## 12. cs-go First-Contact Reference

This section captures observations that should be folded into `docs/governance/known-server-quirks.md` in a separate doc-maintenance pass.

### Connection

| Property                | Value                                                           |
| ----------------------- | --------------------------------------------------------------- |
| **Base URL**            | `https://129-80-248-53.sslip.io/csapi-go`                       |
| **Auth**                | None on data endpoints; bare root URL returns 401               |
| **SSL**                 | Self-signed (`-SkipCertificateCheck` required from PowerShell)  |
| **API Title**           | (cs-go)                                                         |
| **Conformance Classes** | 24 (Common-1, Common-2, Features-1, CSAPI Part 1, CSAPI Part 2) |

### Resource Inventory (as of ST#26)

| Endpoint            | numberMatched | Notes                                                                   |
| ------------------- | ------------- | ----------------------------------------------------------------------- |
| `/systems`          | 38            | GeoJSON FeatureCollection envelope                                      |
| `/deployments`      | 9             | GeoJSON                                                                 |
| `/procedures`       | (large)       | GeoJSON; `numberMatched` not exposed in surveyed response               |
| `/samplingFeatures` | 0             | GeoJSON, empty                                                          |
| `/properties`       | 0             | GeoJSON, empty                                                          |
| `/datastreams`      | (varies)      | `{items, links}` envelope; default page = 10                            |
| `/observations`     | (varies)      | `{items, links}`                                                        |
| `/controlstreams`   | 1             | `{items, links}`. **Lowercase path required** — `/controlStreams` = 404 |
| `/commands`         | (varies)      | **Top-level GET works (200)** — unlike OSH F34                          |
| `/collections`      | 10            | OGC API Common Collections; itemType=feature for all                    |

### Envelope Patterns

| Endpoint Type                       | Envelope                                                           | Items Key  | Top `links` rels | numberMatched |
| ----------------------------------- | ------------------------------------------------------------------ | ---------- | ---------------- | ------------- |
| Part 1 (sys/dep/proc/sf/properties) | GeoJSON `{ type, features, numberMatched, numberReturned, links }` | `features` | `self`, `next`   | yes           |
| Part 2 (ds/obs/cs/cmd)              | `{ items, links }`                                                 | `items`    | `self`, `next`   | not always    |

### `@link` / `@id` Reference Syntax (P8-F3 — #166 fodder)

| Field           | Type            | Example                                  |
| --------------- | --------------- | ---------------------------------------- |
| `system@link`   | `{href: "..."}` | `{ "href": "systems/8eee605f-..." }`     |
| `datastream@id` | bare string     | `"db6756eb-e4ed-47e9-94c2-02eff5edf8d4"` |

In addition, every Part 2 list item carries a normal absolute-URL `links[]` array with `ogc-rel:systems`, `ogc-rel:observations`, `ogc-rel:commands` as appropriate, and a capitalized flat field `"Systems": null` (P8-F6) sitting alongside `system@link`.

### Default Page Size (P8-F4 — validates #167)

`GET /systems` (no `limit` param) → `numberReturned=10` of `numberMatched=38`. Confirms the doc claim committed under #167 / Task A4: cs-go default = 10.

### Content Negotiation

- Default `application/json` for Part 2 endpoints
- `application/geo+json` for Part 1 procedures (and when `?f=geojson` requested elsewhere)
- SensorML negotiation not exercised at Checkpoint A

### Notable Differences vs OSH

- Top-level `/commands` works (P8-F5)
- Sub-resource `sys → deployments` works (OSH returns 400)
- `numberMatched`/`numberReturned` consistently present (OSH lacks — F5)
- Items carry populated `links[]` with absolute URLs (OSH returns empty `[]` — F48)
- `@link`/`@id` reference syntax used heavily (OSH uses `system@id` as flat string instead)
- Conformance count: 24 (OSH advertises 33; difference is mainly in advanced filtering and SensorML extension classes)

---

**End of report.**
