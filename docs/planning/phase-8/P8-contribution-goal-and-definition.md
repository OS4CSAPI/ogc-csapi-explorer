# Phase 8: API Design Refinements & Server-Interop Triage — Contribution Goal and Definition

**Version:** 1.0
**Date:** April 29, 2026

---

## Context

[PR #136](https://github.com/camptocamp/ogc-client/pull/136) — the upstream contribution adding Connected Systems API (CSAPI) support to `camptocamp/ogc-client` — has been open since the completion of Phase 6 and is **still unmerged**. Phase 7 ran in March 2026 to resolve the senior developer's first review (17 type-safety / DRY / security findings), the patch was applied to the `clean-pr` branch on the `OS4CSAPI/ogc-client` fork, and PR #136 was updated.

Two new bodies of work have surfaced since Phase 7 closed and now need to land on PR #136 before upstream maintainer [@jahow](https://github.com/jahow) is asked for a final review:

1. **Senior developer's second code review (API design pass).** A full re-review of the `phase-7` clean-pr state from the perspective of a library consumer — ergonomics, consistency, stability, extensibility, error contract, pagination. Produced 10 distinct findings, triaged in [P8-triage.md](P8-triage.md) into 7 accepted + 3 deferred. Each accepted finding has a numbered MD under [`docs/code-review/`](../../code-review/) (017, 018, 019, 021, 022, 023, 024).

2. **Live integration testing against the [`connected-systems-go`](https://github.com/OS4CSAPI/connected-systems-go) server** (a third independent CSAPI server implementation, exercised through the [`ogc-csapi-explorer`](https://github.com/OS4CSAPI/ogc-csapi-explorer) demo app and the [`OSHConnect-Python`](https://github.com/OS4CSAPI/OSHConnect-Python) publisher fleet). This stress test against a wider implementation corpus surfaced six post-Phase-6 issues against this repo (#166, #167, #168, #169, #170, #171), each evaluated and dispositioned during Phase 8 triage.

Phase 8 closes both bodies of work in a single phase, ships them as additional commits on the `OS4CSAPI/ogc-client` `clean-pr` branch, and refreshes PR #136. The same two-repo workflow Phase 7 introduced is reused: development happens here on `phase-8` with full context (planning docs, governance, fixtures); delivery to upstream happens as one source-only patch squashed onto `clean-pr`.

---

## Contribution Goal

Refine the public API surface of the CSAPI module to satisfy the senior developer's second code review, fix the two server-interop bugs surfaced by `connected-systems-go` integration testing, preserve the institutional learning from the four wontfix/deferred dispositions in our research catalog, and deliver the result as one additional clean commit on `OS4CSAPI/ogc-client`'s `clean-pr` branch — bringing PR #136 to a state where upstream maintainer @jahow is asked for a final review and 2.0-release inclusion decision.

The CSAPI implementation itself (URL builder, parsers, integration boundary, command routing) is functionally complete from Phases 1–7. Phase 8 changes **zero CSAPI parsing logic and zero URL construction logic**. It refines naming, type signatures, error handling, encapsulation, and documentation; it fixes two specific bugs whose root cause is on our side (Part 2 `@link` fallback parsing; pagination-contract documentation gaps); and it explicitly does **not** absorb consumer-side ergonomic helpers that belong in consumer repos (per the wontfix dispositions of #168 and #169).

---

## Acceptance Criteria

These criteria are derived directly from the senior dev's second review, the issue triage decisions, and upstream CI requirements. Every criterion is objectively verifiable.

### Architectural & API Surface (from senior dev review #2)

| #   | Criterion                                                                                                       | Verification                                                                                                                                  |
| --- | --------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| A1  | URL-builder framing is explicit in module-level JSDoc and consumer-facing docs (finding 017)                    | `csapi/index.ts` and `factory.ts` JSDoc states `CSAPIQueryBuilder` produces URLs, not data; consumer must `fetch()` them                      |
| A2  | `endpoint.csapi(collectionId)` convenience method exists on `OgcApiEndpoint`, mirroring `endpoint.edr()` (018)  | `OgcApiEndpoint` has a public `csapi(collectionId): Promise<CSAPIQueryBuilder>` method that internally calls `createCSAPIBuilder`             |
| A3  | All `getDataStream*` / `createDataStream*` / `updateDataStream*` / `deleteDataStream*` methods renamed (019)    | `git grep "DataStream" -- src/ogc-api/csapi/url_builder.ts` returns 0 matches except the type alias deprecation note; tests updated to match  |
| A4  | Validators in `csapi/` throw `EndpointError` (no CSAPI-specific subclass), never plain `Error` / `TypeError`    | `git grep "throw new Error\|throw new TypeError" -- src/ogc-api/csapi/` returns 0 matches; factory wraps thrown errors as `EndpointError`     |
| A5  | `CSAPIQueryBuilder` constructor signature does not expose `OgcApiCollectionInfo`; uses a CSAPI-local type (022) | Constructor's parameter type lives in `csapi/model.ts` and contains only `id`, `title`, `links` shape — no `import` of `OgcApiCollectionInfo` |
| A6  | `availableResources` is typed `ReadonlySet<CSAPIResourceType>` rather than `Set<string>` (023)                  | `tsc --noEmit` passes; consumer code that mutates `availableResources` fails to compile                                                       |
| A7  | `OgcApiEndpoint.root` and `OgcApiEndpoint.getCollectionDocument` are private again (024 / coordinated with 018) | `git grep "public root\b\|public getCollectionDocument\b" src/ogc-api/endpoint.ts` returns 0 matches                                          |
| A8  | The `isCollectionInfo` cast in `factory.ts` is removed as a side benefit of A5 + A7                             | `git grep "isCollectionInfo" -- src/ogc-api/csapi/` returns 0 matches                                                                         |

### Server-Interop Bug Fixes (from CS-Go integration testing)

| #   | Criterion                                                                                                                                                                                           | Verification                                                                                                                                                                                                                                                              |
| --- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| B1  | All Part 2 parsers (`parseDatastream`, `parseObservation`, `parseControlStream`, `parseCommand`, `parseCommandStatus`) accept the `@link` cross-reference form in addition to the `@id` form (#166) | New unit tests exercise both `system@id: "..."` (scalar) and `system@link: { href: "..." }` (object) per OGC 23-002 §16.1; both parse to the same `Datastream.systemId` value. Repeated for `datastream@*`, `foi@*`, `samplingFeature@*`, `controlstream@*`, `command@*`. |
| B2  | Public list methods on `CSAPIQueryBuilder` carry JSDoc that explicitly documents the pagination contract (server picks default page size; consumer must follow `next` HATEOAS links) (#167)         | Every list method on `CSAPIQueryBuilder` has a JSDoc `@remarks` section linking to a centralized "Pagination" doc anchor; lint check (manual review) passes                                                                                                               |

### CI & Behavioral Preservation

| #   | Criterion                                                                                    | Verification                                                                                                                                   |
| --- | -------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| C1  | Prettier formatting passes                                                                   | `npx prettier --check .` exits 0                                                                                                               |
| C2  | TypeScript compilation passes                                                                | `npm run typecheck` exits 0                                                                                                                    |
| C3  | ESLint passes                                                                                | `npm run lint` exits 0                                                                                                                         |
| C4  | Browser test suite passes                                                                    | `npm run test:browser` — all tests pass                                                                                                        |
| C5  | Node test suite passes                                                                       | `npm run test:node` — all tests pass                                                                                                           |
| C6  | All Phase 7 fixes still hold (no regression of #141–#151, #98, #100, #102, #111, #139, #140) | Existing tests still pass; spot check: factory error wrapping (021) does not break factory.spec.ts                                             |
| C7  | Public API of non-CSAPI ogc-client functionality unchanged                                   | Full test suite passes; `git diff phase-7..phase-8 -- src/ ':!src/ogc-api/csapi/' ':!src/index.ts'` shows only the changes required by A2 + A7 |

### Delivery (to PR #136)

| #   | Criterion                                                                                                                           | Verification                                                                                            |
| --- | ----------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| D1  | All Phase 8 source/fixture changes land as **one squashed commit** on `OS4CSAPI/ogc-client`'s `clean-pr` branch                     | `git log --oneline upstream/main..clean-pr` shows exactly 16 commits (15 from Phase 7 baseline + 1 new) |
| D2  | The squashed commit message references review-#2 findings + CS-Go issues + lists every finding/issue resolved                       | Manual review of commit message                                                                         |
| D3  | PR #136 description updated with a "Phase 8" section pointing to the new commit, the resolved findings, and the deferred follow-ups | Manual edit of PR description                                                                           |
| D4  | CI on the updated PR #136 passes                                                                                                    | GitHub Actions green checkmark                                                                          |

---

## Contribution Definition

Phase 8 is composed of three workstreams that converge on a single PR #136 update.

### Workstream 1 — Senior dev review #2: API surface refinements

Resolve the **7 accepted findings** from the second code review. Each has a tracking MD with implementation-level detail; this section names what changes and where.

**API ergonomics & symmetry**

- **Finding 017 — URL-builder framing in docs.** Add module-level JSDoc to `csapi/index.ts`, `factory.ts`, and `url_builder.ts` clarifying that `CSAPIQueryBuilder` produces URLs (consumer fetches them); update `README` / `app/Demo.vue` examples accordingly. Docs-only.
- **Finding 018 — `endpoint.csapi()` convenience method.** Add a public `csapi(collectionId): Promise<CSAPIQueryBuilder>` method on `OgcApiEndpoint`, mirroring the `endpoint.edr()` pattern from upstream PR #114. Internally calls `createCSAPIBuilder`. **Coordinated with finding 024** — the new method does the composition privately so that 024's re-privatization can land cleanly.
- **Finding 019 — `DataStream` → `Datastream` method rename (Option A — straight rename).** Rename all `getDataStream*` / `createDataStream*` / `updateDataStream*` / `deleteDataStream*` / `getDataStreamObservations` / etc. methods to `getDatastream*` / `createDatastream*` / etc., aligning method names with the existing `Datastream` type and parser names. PR #136 has not merged upstream and the CSAPI feature set has never shipped, so there are no downstream consumers — "breaking change" framing does not apply. See [019](../../code-review/019-pending-p2-method-naming-datastream-vs-datastream.md).

**Type safety & encapsulation**

- **Finding 022 — Constructor exposes internal `OgcApiCollectionInfo` type.** Replace the `Pick<OgcApiCollectionInfo, ...>` constructor parameter with a CSAPI-local interface (e.g. `CollectionDescriptor` in `csapi/model.ts`) carrying only `id`, `title`, `links`. The upstream type is no longer leaked through the CSAPI public API.
- **Finding 023 — `availableResources: Set<string>` should be `ReadonlySet<CSAPIResourceType>`.** Tightens both mutability and value type. Forces consumer code that mutates the set to fail to compile.
- **Finding 024 — `OgcApiEndpoint.root` / `getCollectionDocument` newly public — re-privatize (Option A3).** Both members were promoted to public during Phase 6 to enable `createCSAPIBuilder` to read endpoint data. With finding 018 adding `endpoint.csapi()`, the composition can happen privately again. Both members revert to private; the standalone `createCSAPIBuilder(endpoint, collectionId)` becomes value-shaped (takes a pre-resolved `CollectionDescriptor` rather than the live endpoint), and `isCollectionInfo`'s unsound cast disappears as a side benefit. See [024](../../code-review/024-pending-p2-endpoint-root-publicly-exposed.md) for the full investigation.

**Error contract**

- **Finding 021 — Validators throw plain `Error`; factory propagates `TypeError`.** Standardize on `EndpointError`. **Decision locked April 29, 2026: no CSAPI-specific error subclass.** `EndpointError` is the upstream-shipped public exception class (see [`src/shared/errors.ts`](../../../src/shared/errors.ts)) already used by `stac/`, `wmts/`, and `ogc-api/endpoint.ts`; consumers already narrow with `e instanceof EndpointError`. Introducing `CSAPIError extends EndpointError` would expand the public API surface without addressing the reviewer's actual concern (reliable narrowing) and would conflict with Phase 8's hard scope fence. All `throw new Error(...)` / `throw new TypeError(...)` in `csapi/` become `throw new EndpointError(...)`. The factory wraps any error thrown during init as `EndpointError` so consumers can `instanceof`-check uniformly. See [021](../../code-review/021-pending-p2-validators-throw-plain-error.md).

### Workstream 2 — CS-Go integration: server-interop bug fixes

Fix the **two accepted bugs** surfaced by integration testing against the `connected-systems-go` server through the `ogc-csapi-explorer` demo app.

- **Issue [#166](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/166) — Part 2 parsers missing `@link` fallback for cross-reference fields.** All Part 2 parsers (`parseDatastream`, `parseObservation`, `parseControlStream`, `parseCommand`, `parseCommandStatus`) currently extract `system@id` / `datastream@id` / `foi@id` / `samplingFeature@id` / `controlstream@id` / `command@id` only as scalar strings. Per OGC 23-002 §16.1, servers may equivalently emit the cross-reference in object form `{ "system@link": { "href": "..." } }` — and `connected-systems-go` does. Add a fallback: if the `@id` form is absent, read `@link.href`. P1 bug, library is non-conformant; affects two of the three independent server implementations in our test corpus.

- **Issue [#167](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/167) — List methods do not document the pagination contract.** Servers are spec-allowed to choose any default `limit` (10 for `connected-systems-go`, 100 for OpenSensorHub). Consumers who only test against high-default servers may silently process only the first page in production. Docs-only fix: every public list method on `CSAPIQueryBuilder` carries JSDoc explicitly stating that the consumer must follow `next` HATEOAS links to retrieve subsequent pages and that the server (not the library) chooses the default page size. P3 fix, no behavior change.

### Workstream 3 — Triage outputs already shipped during Phase 8 planning

These are **completed Phase 8 work product** that doesn't need additional Phase 8 execution. They are listed here so the Phase 8 ledger is complete and so the goal-and-definition reflects what actually happened.

- **Issue [#168](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/168) — `getLatestObservationUrls()` shim** — closed `wontfix` 2026-04-29. The library is spec-correct per OGC 23-002 §13.3.2 D; the gap is server-side and tracked at [`connected-systems-go#11`](https://github.com/OS4CSAPI/connected-systems-go/issues/11). Empirical-probe matrix preserved in [`docs/research/references.md`](../../research/references.md) as Gap 1. A consumer-side ergonomic helper is tracked in [`ogc-csapi-explorer#47`](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/47).
- **Issue [#169](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/169) — Heuristic coordinate extraction utility** — closed `wontfix` 2026-04-29. The proposed heuristic has unit-ambiguity and false-positive problems (see [#169 status banner](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/169) for the 7-point rationale). Six-convention table preserved in `references.md` "Research Findings Not Adopted, Finding 1." The architecturally correct successor (SWE Common–aware extraction) is tracked at [#171](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/171), filed deferred from day one.
- **Issue [#170](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/170) — Async-iterator pagination helpers** — filed deferred 2026-04-29. Same bucket as findings 020/025/026. Out of scope until upstream broadens scope or a second consumer demonstrates need.
- **Issue [#171](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/171) — SWE Common–aware result-vector extraction** — filed deferred 2026-04-29. Architecturally correct future path for #169's problem domain; explicitly fenced from being implemented as a heuristic.
- **`docs/research/references.md` updates** — two commits ([3878577](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/commit/3878577), [a3424a8](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/commit/a3424a8)) added the "Known Server Conformance Gaps" catalog (4 gaps with empirical-probe template) and the "Research Findings Not Adopted" section (Finding 1: six-convention coordinate-extraction analysis). These are research artifacts, not source/fixture changes — they live on `phase-8` only and **do not flow to `clean-pr`**. The PR #136 update remains a source/fixture-only patch.
- **External issues filed during triage** — [`OS4CSAPI/ogc-csapi-explorer#47`](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/47) (consolidate `MapViewPage.vue` `resultTime=latest` fallback sites), [`OS4CSAPI/ogc-csapi-explorer#48`](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/48) (replace local coordinate extractor when SWE Common path lands), [`OS4CSAPI/connected-systems-go#11` comment](https://github.com/OS4CSAPI/connected-systems-go/issues/11#issuecomment-4340812938) (additional findings on temporal-parameter discard scope).

### What Changes (file-level summary)

> Authoritative file-level specifications live in [P8-implementation-guide.md](P8-implementation-guide.md). The list below is summary-only.

_Files modified (estimated):_

| File                                       | Workstream(s)       | Nature of change                                                                                                     |
| ------------------------------------------ | ------------------- | -------------------------------------------------------------------------------------------------------------------- |
| `src/ogc-api/csapi/index.ts`               | 017                 | Module JSDoc clarifying URL-builder framing                                                                          |
| `src/ogc-api/csapi/factory.ts`             | 017, 021, 022, 024  | Error wrapping; new `CollectionDescriptor` parameter shape; remove `isCollectionInfo` cast                           |
| `src/ogc-api/csapi/url_builder.ts`         | 017, 019, 021, 023  | Module JSDoc; method renames (`DataStream` → `Datastream`); `EndpointError`; `ReadonlySet<CSAPIResourceType>` typing |
| `src/ogc-api/csapi/model.ts`               | 022, 023            | New `CollectionDescriptor` type; `CSAPIResourceType` literal-union confirmed                                         |
| `src/ogc-api/csapi/formats/part2.ts`       | #166                | `@link` fallback in all Part 2 parsers                                                                               |
| `src/ogc-api/endpoint.ts`                  | 018, 024            | New `csapi()` method; revert `root`/`getCollectionDocument` to private                                               |
| All `*.spec.ts` for affected files         | 017–024, #166, #167 | Test renames, new test cases for `@link` fallback, error-type assertions, JSDoc lint                                 |
| `src/ogc-api/csapi/url_builder.ts` (JSDoc) | #167                | Pagination-contract `@remarks` on every list method                                                                  |

_Files NOT changed:_

- `src/index.ts` — Phase 6 already removed all CSAPI exports; A2 + A7 don't restore any
- All SensorML / SWE Common parsers — zero changes
- All format detection / classification code — zero changes
- All Part 1 GeoJSON parsing — zero changes
- All command routing logic — zero changes
- `package.json` — no new sub-paths, no new dependencies

### What Stays Out of Scope (Deferred or Closed)

| Origin               | Item                                                                                                         | Status                                                                                                                                                                                               |
| -------------------- | ------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Senior dev review #2 | Finding 020 — positional `controlStreamId` argument                                                          | Deferred — wider signature redesign tracked in [020](../../code-review/020-deferred-p3-positional-controlstreamid-arg.md)                                                                            |
| Senior dev review #2 | Finding 025 — `AbortSignal` in `createCSAPIBuilder`                                                          | Deferred enhancement — see [025](../../code-review/025-deferred-enhancement-abortsignal-in-factory.md)                                                                                               |
| Senior dev review #2 | Finding 026 — `followNext` / async-iterator pagination helper                                                | Deferred enhancement — see [026](../../code-review/026-deferred-enhancement-follownext-pagination-helper.md); duplicate-tracked at [#170](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/170) |
| Phase 5/6 carry-over | Issue [#110](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/110) — `@link`/`@id` resolution utilities | Deferred — see [110-deferred-enhancement-link-resolution-utilities.md](../../code-review/110-deferred-enhancement-link-resolution-utilities.md)                                                      |
| Phase 7 carry-over   | Upstream-authored security findings 001, 002, 005, 006                                                       | Tracked in [upstream-findings-report.md](../../code-review/upstream-findings-report.md); not our code, not in PR #136                                                                                |
| CS-Go triage         | Issue [#168](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/168) — `getLatestObservationUrls()` shim  | Closed `wontfix`; library is spec-correct; server-side root cause                                                                                                                                    |
| CS-Go triage         | Issue [#169](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/169) — heuristic coordinate extraction    | Closed `wontfix`; architecturally wrong; correct path tracked at #171                                                                                                                                |
| CS-Go triage         | Issue [#170](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/170) — async-iterator helpers             | Filed deferred                                                                                                                                                                                       |
| CS-Go triage         | Issue [#171](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/171) — SWE Common–aware extraction        | Filed deferred                                                                                                                                                                                       |

**Hard scope fence:** Phase 8 does **not** absorb consumer-side ergonomic helpers into the published library. The `MapViewPage.vue` patterns that motivated #168 and #169 are tracked in the consumer's repo. The library stays as narrow as upstream wants it.

### Quality Standards

- Unit tests for each new code path (every `@link` fallback branch, every renamed method, every new error-wrapping site, every JSDoc-driven contract).
- Zero TypeScript errors (`tsc --noEmit`).
- Zero ESLint errors / warnings on the changed files.
- All files pass `npx prettier --check`.
- > 80% coverage on changed lines.
- All existing tests still pass — including all Phase 7 regression tests.
- Consistent patterns with existing CSAPI module: tolerant extraction, `EndpointError` for thrown errors, `ReadonlySet` for exposed collections, `import type` for type-only imports.

### Deliverables

- **8 source files modified** (factory, url_builder, model, part2, endpoint, index, factory.spec, plus url_builder.spec) — exact list in P8-implementation-guide.md
- **9 test files modified or added** — covering 7 accepted findings + 2 bug fixes
- **Estimated diff size:** ~600–1,000 lines source changes (mostly renames + JSDoc + small parser branches), ~400–700 lines test changes
- **One squashed commit on `clean-pr`** updating PR #136
- **Updated PR #136 description** linking to the resolved findings and listing the deferred follow-ups
- **Phase 8 trio of planning docs** (this doc + P8-implementation-guide.md + P8-ROADMAP.md) committed to `phase-8` (does not flow to `clean-pr`)

---

## Two-Repo Workflow

Same pattern Phase 7 introduced (and the one part of Phase 7 that was right):

| Repository                    | Branch                    | Purpose                                                               |
| ----------------------------- | ------------------------- | --------------------------------------------------------------------- |
| `OS4CSAPI/ogc-client-CSAPI_2` | `phase-8` (off `phase-7`) | Development — full context, granular commits, planning docs, fixtures |
| `OS4CSAPI/ogc-client`         | `clean-pr`                | Delivery to upstream — squashed commit appended for PR #136 review    |

**Delivery sequence (executed at end of Phase 8):**

1. All Phase 8 commits land on `phase-8` with full context and granular history.
2. Validation gates pass: `tsc --noEmit`, `npm test`, `npm run lint`, `npx prettier --check`.
3. Generate source/fixture-only patch: `git diff phase-7..phase-8 -- src/ fixtures/ > phase-8.patch` (excludes all `docs/` artifacts).
4. Apply to `OS4CSAPI/ogc-client` `clean-pr` as one squashed commit with a message that lists every finding/issue resolved.
5. Push `clean-pr`; CI runs on PR #136; verify green.
6. Update PR #136 description with a "Phase 8" section.
7. Tag jahow for final review with the time-frame request.

---

## References

| #   | Source                                                                                                                                              | Role                                                                                         |
| --- | --------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| 1   | [P8-triage.md](P8-triage.md)                                                                                                                        | Triage decisions for the 10 findings from senior dev review #2                               |
| 2   | [`docs/code-review/017`–`026`](../../code-review/)                                                                                                  | Per-finding implementation analysis (authoritative for "why" of each fix)                    |
| 3   | [`docs/code-review/upstream-findings-report.md`](../../code-review/upstream-findings-report.md)                                                     | Upstream-authored findings (out of scope; tracking only)                                     |
| 4   | [`docs/code-review/110-deferred-enhancement-link-resolution-utilities.md`](../../code-review/110-deferred-enhancement-link-resolution-utilities.md) | Pre-existing deferred enhancement (carried forward)                                          |
| 5   | [`docs/research/references.md` — Known Server Conformance Gaps](../../research/references.md)                                                       | Empirical CS-Go server gap catalog (Workstream 3 output)                                     |
| 6   | [`docs/research/references.md` — Research Findings Not Adopted, Finding 1](../../research/references.md)                                            | Six-convention coordinate-extraction analysis (Workstream 3 output, #169 closure)            |
| 7   | [PR #136](https://github.com/camptocamp/ogc-client/pull/136)                                                                                        | The upstream pull request that Phase 8 ultimately updates                                    |
| 8   | [P5-contribution-goal-and-definition.md](../phase-5/P5-contribution-goal-and-definition.md)                                                         | Phase 5 trio precedent (parser completion)                                                   |
| 9   | [P6-contribution-goal-and-definition.md](../phase-6/P6-contribution-goal-and-definition.md)                                                         | Phase 6 trio precedent (upstream acceptance refactoring) — closest structural parallel to P8 |
| 10  | [P7-code-review-cleanup-plan.md](../phase-7/P7-code-review-cleanup-plan.md)                                                                         | Phase 7 plan (cleanup phase; trio pattern was not used — restored in Phase 8)                |

---

## Operational Constraints

> **⚠️ MANDATORY:** Before starting work on any Phase 8 task, review [`docs/governance/AI_OPERATIONAL_CONSTRAINTS.md`](../../governance/AI_OPERATIONAL_CONSTRAINTS.md).

Key constraints:

- **Precedence:** OGC specifications → AI Collaboration Agreement → This document → Per-finding MD → Existing code → Conversational context.
- **No scope expansion:** Fix the listed findings and bugs, nothing more. New ideas → file a new issue, defer to a later phase.
- **Minimal diffs:** Prefer the smallest change that satisfies the acceptance criterion. Resist the urge to refactor unrelated code.
- **Ask when unclear:** If a per-finding MD's intent is ambiguous against this doc, stop and ask for clarification.
- **Respect the workflow:** All Phase 8 source changes land on `phase-8` first; `clean-pr` is the delivery mechanism, never the development surface.
- **Respect the wontfix decisions:** #168 and #169 are closed for documented reasons. Do not reopen the question of whether to ship a heuristic helper without explicit user direction.
