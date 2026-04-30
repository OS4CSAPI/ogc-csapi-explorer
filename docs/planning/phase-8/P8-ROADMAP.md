# Phase 8 Roadmap

**Last Updated:** April 29, 2026
**Version:** 1.0
**Status:** Ready for execution
**Parent guide:** [P8-implementation-guide.md](P8-implementation-guide.md)
**Phase definition:** [P8-contribution-goal-and-definition.md](P8-contribution-goal-and-definition.md)

---

## Executive Summary

This roadmap breaks Phase 8 — the third upstream-acceptance pass on PR #136 — into **10 sequential tasks** organized across **5 phases** (A–E). Each task is sized to map roughly **1:1 onto a GitHub issue** so progress is trackable from the issue board without consulting the implementation guide.

> **📋 FULL CONTEXT**
>
> This roadmap extracts the execution-unit breakdown from the complete [P8-implementation-guide.md](P8-implementation-guide.md). The implementation guide is the authoritative "how" — this roadmap is the authoritative "what order, in what unit, with what gate."
>
> The "why" for each finding lives in its per-finding MD under [`docs/code-review/`](../../code-review/) (017, 018, 019, 021, 022, 023, 024). Triage rationale for the 6 CS-Go issues lives in [P8-triage.md](P8-triage.md) and the issue threads themselves.

**Phase Overview:**

- **Phase A: Documentation & Type-Hardening (4 tasks)** — Low-risk, parallel-safe foundation: docs framing, type extraction, set-typing tightening, pagination JSDoc. Builds the ground every other phase walks on without any behavioral or mechanical-rename impact.
- **Phase B: API Surface Refinements (2 tasks)** — Mechanical rename + error-type standardization. Reshapes the public surface without changing any URL strings or parser outputs.
- **Phase C: Server-Interop Bug Fix (1 task)** — Part 2 `@link` fallback. Independent of Phases A and B; isolated to `formats/part2.ts`.
- **Phase D: Coordinated Structural Refactor (1 task)** — `endpoint.csapi()` + re-privatization (findings 018 + 024 as one indivisible unit). Highest-risk, highest-payoff. Must run last; everything else green first.
- **Phase E: Delivery (2 tasks)** — Full CI gate, source-only patch generation, squash onto `clean-pr`, push, PR #136 description update, @jahow tag.

**Total Scope:**

- **Source changes:** ~400 LOC across 8 files (all under `src/ogc-api/csapi/` plus `src/ogc-api/endpoint.ts` for Phase D).
- **Test changes:** ~550 LOC across 6 spec files (mostly `formats/part2.spec.ts`, `endpoint.spec.ts`, `factory.spec.ts`).
- **Total Code:** ~950 lines.
- **Planning artifacts:** Already shipped on `phase-8` (do not flow to `clean-pr`).
- **Delivery:** One squashed commit appended to `OS4CSAPI/ogc-client` `clean-pr` to refresh PR #136.

**Key Principles (locked in [P8-contribution-goal-and-definition.md §3](P8-contribution-goal-and-definition.md) and [P8-implementation-guide.md §3](P8-implementation-guide.md#3-design-principles--decisions-already-locked)):**

1. **Finding 019:** Straight rename — no aliases, no `@deprecated` tags. PR #136 unmerged ⇒ no consumers ⇒ no deprecation cycle to document.
2. **Finding 021:** `EndpointError` only — no `CSAPIError` subclass. Reviewer's concern was narrowability, not type-granularity.
3. **Finding 024:** Option A3 (re-privatize + new `endpoint.csapi()` + value-shaped factory). Net public surface decreases.
4. **#168, #169:** Closed `wontfix` (already shipped). Do not reopen mid-execution.
5. **Hard scope fence:** No consumer-side ergonomic helpers absorbed into the library this phase.

**Success Factors:**

- ✅ Tasks executed in roadmap order — Phases A → B → C → D → E
- ✅ Per-task acceptance gate green before moving to the next task
- ✅ Full CI gate green before generating the source patch
- ✅ One commit per task (granular history on `phase-8`); one squash on `clean-pr`
- ✅ Locked decisions stay locked — surface, do not silently re-decide

---

## Implementation Roadmap

**Complete Roadmap: ALL Work Required for Phase 8 Closure**

This roadmap breaks Phase 8 into 10 numbered tasks ordered by dependency and risk. The order is logical and not a function of resource availability — Phase 8 will execute end-to-end. Each task corresponds to a GitHub issue (or pair of issues, where a finding and its bug-fix issue collapse into one work unit).

### Phase A: Documentation & Type-Hardening (Low Complexity)

**Goal:** Establish the documentation framing and type-system tightening on which all later phases depend, without touching any behavior or method names.

**Why first:** Tasks A1–A4 carry zero behavioral risk — pure docs, additive types, and `readonly` annotations. Running them first builds confidence that the test runner, prettier, lint, and tsc gates are all healthy on `phase-8` before any mechanical edits land. Each task is independent of the others within Phase A; sequencing here is a recommendation, not a hard constraint.

**Tasks:**

1. **Task A1 — Finding 017: URL-Builder Framing in Module Docs** (Low complexity)

   - **GitHub issue:** [#172](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/172) (Phase 8 / Task A1) — labels: `phase-8`, `locked-decision`, `code-review`, `documentation`
   - **Authoritative source:** [`017-pending-p3-docs-url-builder-framing.md`](../../code-review/017-pending-p3-docs-url-builder-framing.md)
   - **Implementation guide:** [§4.1](P8-implementation-guide.md#41-finding-017--url-builder-framing-in-module-docs)
   - **Goal:** A consumer reading any of `csapi/index.ts`'s module docblock, `createCSAPIBuilder`'s JSDoc, `CSAPIQueryBuilder`'s class JSDoc, or the README cannot miss that the module returns URL strings and the consumer owns every `fetch()` call.
   - **Files modified:**
     - `src/ogc-api/csapi/index.ts` — module-level JSDoc with the 5-step worked example
     - `src/ogc-api/csapi/factory.ts` — `createCSAPIBuilder` JSDoc cross-references the module docblock
     - `src/ogc-api/csapi/url_builder.ts` — class-level JSDoc on `CSAPIQueryBuilder`
     - `README.md` — new "Connected Systems — making a request" section
   - **Test impact:** None (docs only).
   - **Acceptance gate:** Manual review — the URL-builder pattern is unmistakable in all 4 docs surfaces. `npx prettier --check` passes.
   - **Effort:** Small (~1 hour). **Risk:** None. **Dependencies:** None.

2. **Task A2 — Finding 022: Constructor Type Decoupling (`CSAPICollectionRef`)** (Low complexity)

   - **GitHub issue:** [#173](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/173) (Phase 8 / Task A2) — labels: `phase-8`, `locked-decision`, `code-review`, `type-safety`
   - **Authoritative source:** [`022-pending-p3-constructor-exposes-collection-info-type.md`](../../code-review/022-pending-p3-constructor-exposes-collection-info-type.md)
   - **Implementation guide:** [§4.3](P8-implementation-guide.md#43-finding-022--constructor-exposes-ogcapicollectioninfo-type)
   - **Goal:** `CSAPIQueryBuilder`'s constructor parameter type is owned by the CSAPI module. Refactoring `OgcApiCollectionInfo` upstream cannot become a breaking change to the CSAPI public API.
   - **Files modified:**
     - `src/ogc-api/csapi/model.ts` — add `CSAPICollectionRef` interface (id, optional title, links)
     - `src/ogc-api/csapi/url_builder.ts` — constructor parameter annotation swap
     - `src/ogc-api/csapi/index.ts` — barrel export of the new type
     - `src/ogc-api/csapi/factory.ts` — signature update (will be touched again in Task D1; here only the parameter type changes, not the shape)
     - `src/ogc-api/csapi/url_builder.spec.ts` — update fake-collection literal type assertions
     - `src/ogc-api/csapi/factory.spec.ts` — same
   - **Test impact:** Type-only — bodies of test fakes are structurally compatible and stay identical at runtime.
   - **Acceptance gate:** `git grep -n "OgcApiCollectionInfo" -- src/ogc-api/csapi/url_builder.ts` returns 0 lines. `npx tsc --noEmit` passes.
   - **Effort:** Trivial (~30 min). **Risk:** None (structural compatibility). **Dependencies:** None within Phase 8; Task D1 builds on this.

3. **Task A3 — Finding 023: `availableResources` `ReadonlySet<CSAPIResourceType>` Tightening** (Low complexity)

   - **GitHub issue:** [#174](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/174) (Phase 8 / Task A3) — labels: `phase-8`, `locked-decision`, `code-review`, `type-safety`
   - **Authoritative source:** [`023-pending-p3-availableresources-set-typing.md`](../../code-review/023-pending-p3-availableresources-set-typing.md)
   - **Implementation guide:** [§4.4](P8-implementation-guide.md#44-finding-023--availableresources-type-tightening)
   - **Goal:** Consumer code that mutates the set fails to compile; consumer code iterating the set narrows automatically to the resource-type union.
   - **Files modified:**
     - `src/ogc-api/csapi/url_builder.ts` — annotation change on the public field; possibly the `extractAvailableResources()` return type
     - `src/ogc-api/csapi/url_builder.spec.ts` — verify no test mutates the set (expected: zero such tests)
   - **Test impact:** None expected for behavior; type-narrowing in `expect(builder.availableResources.has(...))` callsites continues to work.
   - **Acceptance gate:** `npx tsc --noEmit` passes. Scratch attempt to call `builder.availableResources.add('foo')` fails to compile.
   - **Effort:** Trivial (~30 min). **Risk:** Low. **Dependencies:** None.

4. **Task A4 — Issue #167: Pagination-Contract JSDoc on List Methods** (Low complexity)

   - **GitHub issue:** [#167](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/167) (Phase 8 / Task A4 — absorbed in place per Roadmap Summary directive; original finding preserved verbatim in issue body) — labels: `phase-8`, `locked-decision`, `code-review`, `documentation`. Wrapper [#175](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/175) closed as `duplicate_of: 167`.
   - **Authoritative source:** [Issue #167](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/167)
   - **Implementation guide:** [§5.2](P8-implementation-guide.md#52-issue-167--pagination-contract-jsdoc-on-list-methods)
   - **Goal:** Every list method on `CSAPIQueryBuilder` carries JSDoc that explicitly documents the pagination contract — server picks default page size, consumer follows `next` HATEOAS links to retrieve subsequent pages.
   - **Files modified:**
     - `src/ogc-api/csapi/url_builder.ts` — class-level "Pagination" doc anchor + `@remarks` block on each list method (~16 methods after Task B1's renames; for now, written against current `DataStream*` names and adjusted in B1)
   - **Test impact:** None (docs only); optional lint test asserting every public list method's JSDoc matches `/Pagination:.*next.*links/i`.
   - **Acceptance gate:** Manual review — every list method's JSDoc carries the `@remarks` Pagination block; module/class docblock has the centralized "Pagination" anchor.
   - **Effort:** Small (~1.5 hours, mostly mechanical). **Risk:** None. **Dependencies:** Logically depends on Task B1 (the rename) for final method names, but **the JSDoc bodies can be written first against the old names and renamed in lockstep with B1**. Recommended to run A4 _after_ B1 to avoid double-touching the same methods.

   > **Sequencing note:** A4 is in Phase A by complexity (trivial, docs-only) but should be executed _after_ Task B1 to avoid renaming the same JSDoc blocks twice. Either order works mechanically; the post-B1 placement avoids churn.

**Phase A Deliverables:**

- ✅ Module/class/factory/README docs all reinforce the URL-builder framing
- ✅ `CSAPICollectionRef` type owned by CSAPI module
- ✅ `availableResources: ReadonlySet<CSAPIResourceType>`
- ✅ Pagination contract documented on every list method
- ✅ Zero behavioral change

**Dependencies:** None (foundational). Phase A produces the type and doc surface that Phases B–D depend on.

---

### Phase B: API Surface Refinements (Medium Complexity)

**Goal:** Apply the mechanical rename and error-type standardization that constitute the bulk of the senior reviewer's API surface concerns.

**Why second:** These tasks change names and error types but no URL outputs and no parser outputs. Tests are mechanical to update. Doing them after Phase A's docs-and-types foundation lets the rename land on a code surface that is already conceptually framed correctly. Doing them before Phase D means the coordinated structural refactor in D operates on the final method names and final error types, eliminating one whole class of last-minute fix-ups.

**Tasks:**

5. **Task B1 — Finding 019: `DataStream` → `Datastream` Method Rename** (Medium complexity, mechanical)

   - **GitHub issue:** [#176](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/176) (Phase 8 / Task B1) — labels: `phase-8`, `locked-decision`, `code-review`, `breaking-change`
   - **Authoritative source:** [`019-pending-p2-method-naming-datastream-vs-datastream.md`](../../code-review/019-pending-p2-method-naming-datastream-vs-datastream.md) — Option A locked (straight rename, no aliases)
   - **Implementation guide:** [§4.2](P8-implementation-guide.md#42-finding-019--datastream--datastream-method-rename)
   - **Goal:** Single coherent spelling everywhere. `git grep "DataStream" -- src/ogc-api/csapi/` returns 0 matches. Method names match the existing `Datastream` type, `parseDatastream` parser, and `'datastreams'` resource constant.
   - **Files modified:**
     - `src/ogc-api/csapi/url_builder.ts` — 13 method declarations
     - `src/ogc-api/csapi/url_builder.spec.ts` — every test case
     - `src/ogc-api/csapi/integration/*.spec.ts` — any integration tests calling these methods
     - `src/ogc-api/csapi/factory.spec.ts` — if it references method names
     - `src/ogc-api/csapi/index.ts` — barrel re-exports if any names appear
     - `app/Demo.vue` — demo app references (under our control; outside `src/` so does not flow to `clean-pr` but kept consistent)
   - **Mechanical execution:** VS Code rename-symbol (F2) on each declaration; tsc-then-tests cycle catches any missed callsite.
   - **Test impact:** ~13 describe blocks renamed; method invocations updated. No new test cases for the rename itself.
   - **Acceptance gate:** `git grep -n "DataStream" -- 'src/ogc-api/csapi/'` returns 0 (modulo `Datastream` matches). `npm run typecheck` and `npm run test:browser src/ogc-api/csapi/url_builder.spec.ts` pass.
   - **Effort:** Mechanical (~1 hour). **Risk:** Low (rename-symbol + tsc gates catch every call site). **Dependencies:** None within Phase 8 (independent of Phase A); should land before Task A4 finalization.

6. **Task B2 — Finding 021: Validators Throw `EndpointError`** (Medium complexity)

   - **GitHub issue:** [#177](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/177) (Phase 8 / Task B2) — labels: `phase-8`, `locked-decision`, `code-review`, `error-handling`
   - **Authoritative source:** [`021-pending-p2-validators-throw-plain-error.md`](../../code-review/021-pending-p2-validators-throw-plain-error.md) — Decision locked: `EndpointError` only, no subclass
   - **Implementation guide:** [§4.5](P8-implementation-guide.md#45-finding-021--validators-throw-plain-error)
   - **Goal:** Every error a CSAPI consumer can catch is `instanceof EndpointError`. `git grep "throw new Error\|throw new TypeError" -- src/ogc-api/csapi/` returns 0 matches.
   - **Files modified (re-verify exact lines via `git grep -n "throw new Error\|throw new TypeError" -- src/ogc-api/csapi/` immediately before editing):**
     - `src/ogc-api/csapi/helpers.ts`
     - `src/ogc-api/csapi/formats/response.ts`
     - `src/ogc-api/csapi/formats/part2.ts`
     - `src/ogc-api/csapi/formats/property.ts`
     - `src/ogc-api/csapi/formats/schema-response.ts`
     - `src/ogc-api/csapi/formats/geojson.ts`
     - `src/ogc-api/csapi/formats/swecommon/_helpers.ts`
     - Corresponding `.spec.ts` files — replace `expect(...).toThrow(Error)` with `expect(...).toThrow(EndpointError)`
   - **Important:** the factory wrapping `try/catch` in `endpoint.csapi()` is **deferred to Task D1** — that's where the network awaits actually live after the 018+024 refactor. Task B2 covers helpers and parser-internal throws only.
   - **Test impact:** Mechanical replacement of error-type assertions; no new test logic.
   - **Acceptance gate:** `git grep -n "throw new Error\|throw new TypeError" -- src/ogc-api/csapi/` returns 0. All `.spec.ts` files green.
   - **Effort:** Mechanical (~2 hours; ~12 throw sites + spec updates). **Risk:** Low (`EndpointError extends Error`, so any existing `instanceof Error` assertion still narrows). **Dependencies:** None within Phase 8.

**Phase B Deliverables:**

- ✅ All 13 `DataStream*` methods renamed to `Datastream*`
- ✅ Single coherent spelling across types, parsers, methods, and resource constants
- ✅ Every CSAPI throw site emits `EndpointError`
- ✅ Consumer-narrowable error contract on the URL-builder/parser surface (factory/endpoint wrapping deferred to D1)

**Dependencies:** Phase A's `CSAPICollectionRef` type and pagination doc anchor. Phase A's tasks A1–A3 are independent of Phase B and can run interleaved if desired.

---

### Phase C: Server-Interop Bug Fix (Medium Complexity)

**Goal:** Make Part 2 parsers conformant with OGC 23-002 §16.1's optional `@link` object form for cross-reference fields, restoring full interoperability with `connected-systems-go`.

**Why third:** Phase C is mechanically isolated to `formats/part2.ts` and its spec — it does not depend on Phases A or B and could in principle run in parallel. It is sequenced here because its acceptance criterion (the new `@link` test pairs) is easier to write against the post-B2 error-type contract: any parser-internal throw it encounters during testing will already be `EndpointError`-typed, which avoids one round of revisit after B2. The placement also keeps Phase D as the lone "high-risk-last" task.

**Tasks:**

7. **Task C1 — Issue #166: Part 2 `@link` Fallback in Cross-Reference Fields** (Medium complexity)

   - **GitHub issue:** [#166](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/166) (Phase 8 / Task C1 — absorbed in place per Roadmap Summary directive; original finding preserved verbatim in issue body) — labels: `phase-8`, `locked-decision`, `code-review`, `bug`, `server-interop`. Wrapper [#178](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/178) closed as `duplicate_of: 166`.
   - **Authoritative source:** [Issue #166](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/166); spec authority [OGC 23-002 §16.1](https://docs.ogc.org/is/23-002/23-002.html)
   - **Implementation guide:** [§5.1](P8-implementation-guide.md#51-issue-166--part-2-link-fallback-in-cross-reference-fields)
   - **Goal:** All Part 2 parsers extract cross-reference IDs from either the `@id` (scalar string) form or the `@link` (object with `href`) form. Library is conformant for `connected-systems-go` and any future server emitting the object form.
   - **Files modified:**
     - `src/ogc-api/csapi/formats/part2.ts` — add `extractCrossReferenceId(obj, fieldName)` helper; replace 5+ inline `obj['<field>@id']` extractions in `parseDatastream`, `parseControlStream`, `parseObservation` (3 fields), `parseCommand`, `parseCommandStatus` with helper calls
     - `src/ogc-api/csapi/formats/part2.spec.ts` — add the 5-test pattern (scalar, object, both, bare-href, neither) for each affected parser/field — ~25–30 new test cases total
   - **Optional:** add one new fixture file per parser exercising the `@link` form to lock the contract in end-to-end (`fixtures/csapi/part2/<resource>-link-form.json`)
   - **Test impact:** ~25–30 new test cases; existing `@id`-form tests remain unchanged (the extractor prefers `@id` when both are present, preserving current behavior).
   - **Acceptance gate:** `npm run test:browser src/ogc-api/csapi/formats/part2.spec.ts` — all new `@link` tests green. All existing tests still green (regression).
   - **Effort:** Small-Medium (~3 hours: helper + 5 call-site swaps + 25 tests + optional fixtures). **Risk:** Low (`@id` is the preferred branch; `@link` is purely additive fallback). **Dependencies:** Task B2 (so any `EndpointError` throws inside the new helper are already on the standardized type). Independent of Tasks A1–A4 and B1.

**Phase C Deliverables:**

- ✅ Library is OGC 23-002 §16.1-conformant for both `@id` and `@link` forms
- ✅ `connected-systems-go` interop confirmed via test pairs and (optionally) fixtures
- ✅ Existing OpenSensorHub / Toolbox4OGC behavior preserved

**Dependencies:** Phase B Task B2 (recommended sequencing). Phase C could in principle run before B2; the chosen order avoids one revisit.

---

### Phase D: Coordinated Structural Refactor (High Complexity)

**Goal:** Restore the `OgcApiEndpoint` invariant (`root` and `getCollectionDocument` private), add the discoverable `endpoint.csapi(id)` entry point, and refactor `createCSAPIBuilder` into a value-shaped pure factory.

**Why fourth (last):** This is the only task that touches `src/ogc-api/endpoint.ts` (the upstream-authored file outside the CSAPI module). It changes a public-API shape on the standalone factory, removes the unsound `isCollectionInfo` runtime cast, and migrates one external test caller. It is the single highest-risk and highest-payoff change in Phase 8. Running it last — after the renames, error-type standardization, and `@link` fallback are all green — means the refactor operates on a stable target surface and any breakage discovered is unambiguously attributable to the refactor itself.

**Tasks:**

8. **Task D1 — Findings 018 + 024 (Coordinated): `endpoint.csapi()` + Re-Privatization** (High complexity)

   - **GitHub issue:** [#179](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/179) (Phase 8 / Task D1 — coordinated 018 + 024) — labels: `phase-8`, `locked-decision`, `code-review`, `breaking-change`, `high-risk`
   - **Authoritative sources:**
     - [`018-pending-p3-endpoint-csapi-convenience-method.md`](../../code-review/018-pending-p3-endpoint-csapi-convenience-method.md)
     - [`024-pending-p2-endpoint-root-publicly-exposed.md`](../../code-review/024-pending-p2-endpoint-root-publicly-exposed.md) — Option A3 locked
   - **Implementation guide:** [§4.6](P8-implementation-guide.md#46-findings-018--024-coordinated--endpointcsapi-and-re-privatization) — full 8-step execution sequence
   - **Goal (acceptance criteria A2 + A7 + A8 from [P8-contribution-goal-and-definition.md](P8-contribution-goal-and-definition.md)):**
     - `OgcApiEndpoint.root` and `getCollectionDocument` revert to `private`
     - New public `OgcApiEndpoint.csapi(collectionId): Promise<CSAPIQueryBuilder>` mirrors `endpoint.edr(id)`
     - `isCollectionInfo` runtime cast in `factory.ts` disappears (typed `getCollectionInfo()` makes it unreachable)
     - Standalone `createCSAPIBuilder` becomes value-shaped, pure, trivially testable
     - All `endpoint.csapi()` initialization errors `instanceof EndpointError` (closing the factory-level wrapping deferred from Task B2)
   - **Files modified:**
     - `src/ogc-api/csapi/factory.ts` — value-shape signature swap; `await`s removed; `isCollectionInfo` cast removed
     - `src/ogc-api/csapi/factory.spec.ts` — fake-`OgcApiEndpoint` test doubles disappear; tests construct value literals directly (~−60 LOC net simplification)
     - `src/ogc-api/endpoint.ts` — new `public async csapi(collectionId)` method with `try/catch` + re-throw guard; `root` and `getCollectionDocument` flipped back to `private`
     - `src/ogc-api/endpoint.spec.ts` — line 2868 (re-verify) test that asserted on `getCollectionDocument` shape migrates to assert through `getCollectionInfo`; new describe block adds ~80 LOC of `csapi()` tests (happy path, no-CSAPI-conformance, network-error wrap, EndpointError re-throw)
     - `src/ogc-api/csapi/index.ts` — barrel verified; only the standalone `createCSAPIBuilder` signature changed, name unchanged
   - **Dynamic import requirement:** `endpoint.csapi()` must use `await import('./csapi/factory.js')` and `await import('./csapi/helpers.js')` — static imports re-introduce the CSAPI dependency edge that issue #122 (`20a35d2`) deliberately removed.
   - **Test impact:** `factory.spec.ts` simplifies (~−60 LOC); `endpoint.spec.ts` gains ~80 LOC of `csapi()` tests; the one pre-existing shape-assertion test migrates.
   - **Acceptance gate:**
     - `git grep -n "public root\|public getCollectionDocument" src/ogc-api/endpoint.ts` returns 0
     - `git grep -n "isCollectionInfo" -- src/ogc-api/csapi/` returns 0
     - `git grep -n "throw new Error\|throw new TypeError" -- src/ogc-api/csapi/ src/ogc-api/endpoint.ts` returns 0 (combined check with B2 to lock the post-D1 invariant)
     - New `endpoint.csapi(id)` test suite green: happy path, hasConnectedSystems-false, getCollectionInfo-rejects-with-TypeError (asserts wrapped `EndpointError`), getCollectionInfo-rejects-with-EndpointError (asserts re-thrown as-is, not double-wrapped)
   - **Effort:** Medium-High (~6 hours: 8-step sequence + tests + verification). **Risk:** Medium — touches upstream-authored file and changes a published factory shape. **Mitigation:** execute last and alone, with all other Phase 8 changes already green; full CI gate before generating the patch.
   - **Dependencies:**
     - Task A2 (`CSAPICollectionRef`) — required for the new factory signature
     - Task B2 (`EndpointError` standardization) — Task D1 closes the factory-level wrapping that B2 deferred
     - Tasks A1–A4, B1, C1 — should be green; D1 is the single coordinated unit and must not be split

**Phase D Deliverables:**

- ✅ Public CSAPI surface = one constructor entry point (`endpoint.csapi(id)`) + the URL-builder methods + the parser functions
- ✅ Zero unsound runtime casts in CSAPI factory code
- ✅ Standalone `createCSAPIBuilder` is value-shaped, pure, trivially testable without `OgcApiEndpoint` doubles
- ✅ All `endpoint.csapi()` initialization paths `instanceof EndpointError`-narrowable

**Dependencies:** All of Phase A + Phase B + Phase C must be green.

---

### Phase E: Verification & Delivery (No Source Change)

**Goal:** Run the full CI gate against the Phase 8 outcome, generate the source-only patch, squash onto `clean-pr`, push to refresh PR #136, and tag the maintainer for final review.

**Why last:** Identical to Phase 7's pattern (the one part of Phase 7 that was structurally right — see [P8-implementation-guide.md §11](P8-implementation-guide.md#11-two-repo-delivery-sequence)). All source/test changes complete; this phase is pure delivery and contains no production code edits.

**Tasks:**

9. **Task E1 — Full CI Gate + Source Patch Generation** (Low complexity)

   - **GitHub issue:** [#180](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/180) (Phase 8 / Task E1) — labels: `phase-8`, `delivery`, `ci`
   - **Implementation guide:** [§8.2](P8-implementation-guide.md#82-full-ci-gate) + [§11 steps 2–3](P8-implementation-guide.md#11-two-repo-delivery-sequence)
   - **Goal:** All five CI gates exit 0 on `phase-8`; source-only patch generated and saved.
   - **Actions:**
     1. `cd c:\Users\sbolling\Documents\ogc-client-CSAPI_2`
     2. `npx prettier --check .` → must exit 0
     3. `npm run typecheck` → must exit 0
     4. `npm run lint` → must exit 0
     5. `npm run test:browser` → must exit 0
     6. `npm run test:node` → must exit 0
     7. `git diff phase-7..phase-8 -- src/ fixtures/ > phase-8.patch` (Phase 7 baseline; excludes `docs/`, `app/`, `src-node/` so workstream-3 catalog updates do **not** flow to upstream)
     8. Inspect `phase-8.patch` — confirm only `src/ogc-api/csapi/**`, `src/ogc-api/endpoint.ts`, `src/ogc-api/index.ts`, and `fixtures/csapi/**` (if C1 added fixtures) appear; reject anything else
   - **Test impact:** None — verification only.
   - **Acceptance gate:** All five CI commands exit 0; `phase-8.patch` contains only source/fixture diffs and is ~400 source LOC + ~550 test LOC.
   - **Effort:** Small (~30 min, mostly waiting for CI). **Risk:** None (verification only). **Dependencies:** All of Phases A–D complete.

10. **Task E2 — Squash onto `clean-pr` + Push + PR #136 Refresh** (Low complexity)

    - **GitHub issue:** [#181](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/181) (Phase 8 / Task E2) — labels: `phase-8`, `delivery`, `upstream-pr`
    - **Implementation guide:** [§11 steps 4–8](P8-implementation-guide.md#11-two-repo-delivery-sequence) + squashed commit message template
    - **Goal:** PR #136 carries one new squashed commit titled "Phase 8: API design refinements + CS-Go server-interop fixes"; CI green on the PR; @jahow tagged for final review.
    - **Actions:**
      1. Switch to `OS4CSAPI/ogc-client` repo (clone if not already local)
      2. Checkout `clean-pr` branch
      3. `git apply <path>/phase-8.patch`
      4. `git add -A`
      5. `git commit` with the squashed message template from [§11](P8-implementation-guide.md#11-two-repo-delivery-sequence)
      6. `git push origin clean-pr` — refreshes PR #136 in `camptocamp/ogc-client`
      7. Verify CI green on PR #136 (GitHub Actions)
      8. Update PR #136 description with a new "## Phase 8" section: acceptance-criteria recap (A1–A8 + B1–B2), resolved-findings list (017, 018, 019, 021, 022, 023, 024, #166, #167), wontfix-list (#168, #169), deferred-list (020, 025, 026, #170, #171)
      9. Tag @jahow for final review with explicit time-frame ask
    - **Test impact:** None — delivery only.
    - **Acceptance gate:** PR #136 shows one new commit; CI green; PR description has Phase 8 section; @jahow tagged.
    - **Effort:** Small (~1 hour, mostly description writing). **Risk:** Low (mechanical apply; if patch fails to apply cleanly, return to `phase-8` and rebase or regenerate the patch). **Dependencies:** Task E1.

**Phase E Deliverables:**

- ✅ Full CI gate green on `phase-8`
- ✅ Source-only patch generated and applied to `clean-pr`
- ✅ PR #136 refreshed with one new squashed commit
- ✅ CI green on PR #136
- ✅ PR description updated with comprehensive Phase 8 summary
- ✅ @jahow tagged for final review

**Dependencies:** Phases A–D complete.

---

## Roadmap Summary

| Phase     | Tasks  | Complexity | Deliverables                                                                           | Source LOC | Test LOC | Dependencies |
| --------- | ------ | ---------- | -------------------------------------------------------------------------------------- | ---------- | -------- | ------------ |
| **A**     | 4      | Low        | Docs framing + `CSAPICollectionRef` type + `ReadonlySet` tightening + pagination JSDoc | ~80        | ~10      | None         |
| **B**     | 2      | Medium     | `Datastream` rename (13 methods) + `EndpointError` standardization                     | ~120       | ~80      | Phase A      |
| **C**     | 1      | Medium     | `@link` fallback (5 parsers + helper + ~25 tests)                                      | ~80        | ~150     | Phase B      |
| **D**     | 1      | High       | `endpoint.csapi()` + re-privatization (coordinated 018 + 024)                          | ~120       | ~310     | Phases A–C   |
| **E**     | 2      | Low        | CI gate + patch generation + clean-pr squash + PR #136 refresh                         | 0          | 0        | Phases A–D   |
| **TOTAL** | **10** | **Mixed**  | **Phase 8 complete; PR #136 ready for @jahow's final review**                          | **~400**   | **~550** |              |

> **Total Code:** ~950 lines added across `src/ogc-api/` and its specs (no `app/`, no `src-node/`, no `docs/` flowing to `clean-pr`).
>
> **GitHub Issue Mapping (filed on `OS4CSAPI/ogc-client-CSAPI_2`):**
>
> | Task | Issue                                                             | State | Title                                                                                |
> | ---- | ----------------------------------------------------------------- | ----- | ------------------------------------------------------------------------------------ |
> | A1   | [#172](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/172) | open  | Finding 017 — URL-builder framing in module docs                                     |
> | A2   | [#173](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/173) | open  | Finding 022 — Constructor type decoupling (`CSAPICollectionRef`)                     |
> | A3   | [#174](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/174) | open  | Finding 023 — `availableResources` `ReadonlySet` typing                              |
> | A4   | [#167](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/167) | open  | Issue #167 — Pagination-contract JSDoc on list methods _(absorbed in place)_         |
> | B1   | [#176](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/176) | open  | Finding 019 — `DataStream` → `Datastream` method rename                              |
> | B2   | [#177](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/177) | open  | Finding 021 — Validators throw `EndpointError`                                       |
> | C1   | [#166](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/166) | open  | Issue #166 — Part 2 `@link` fallback in cross-reference fields _(absorbed in place)_ |
> | D1   | [#179](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/179) | open  | Findings 018 + 024 (coordinated) — `endpoint.csapi()` + re-privatization             |
> | E1   | [#180](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/180) | open  | Full CI gate + source patch generation                                               |
> | E2   | [#181](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/181) | open  | Squash onto `clean-pr` + push + PR #136 refresh                                      |
>
> **Closed wrappers (duplicates of absorbed issues):** [#175](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/175) → `duplicate_of: 167`; [#178](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/178) → `duplicate_of: 166`. Per the directive in this Roadmap Summary, existing issues #166 and #167 already covered Tasks C1 and A4 respectively and were absorbed in place rather than wrapped — wrapper issues filed during initial Phase 8 issue creation were closed as duplicates and the Phase 8 Task spec was merged into the existing issue body (original finding preserved verbatim below a separator).

**Why This Structure (the principled rationale):**

- **Risk gradient.** Phase A (zero behavioral change) → Phase B (mechanical, reversible) → Phase C (additive parser branch) → Phase D (structural refactor + upstream-authored file). The order is monotonic in risk; a failure inside any phase is bounded by everything before it being green.
- **Dependency-respecting.** A2's `CSAPICollectionRef` and B2's `EndpointError` contract are both prerequisites for D1; the order makes that explicit. C1 is independent of A and B in principle but sequenced after B2 to avoid a revisit.
- **Decision-locked.** Every task's acceptance criterion derives from a decision already locked in [P8-contribution-goal-and-definition.md §3](P8-contribution-goal-and-definition.md) and [P8-implementation-guide.md §3](P8-implementation-guide.md#3-design-principles--decisions-already-locked). Mid-execution second-guessing is out of scope.
- **One commit per task on `phase-8`.** Granular history on the planning branch; one squash on the delivery branch. The two-repo workflow stays clean.
- **1:1 task-to-issue mapping.** Each numbered task is a self-contained unit with a single acceptance gate and a clear definition of done. Issue boards and the roadmap stay in sync with no translation layer.
- **Complete in one phase.** Phase 8 is the third (and intended final) upstream-acceptance pass on PR #136. There is no Phase 9 contemplated. The roadmap reflects that — all 10 tasks ship together.
- **Hard scope fence.** Tasks listed are all the tasks. No "wouldn't it be nice if..." additions. New ideas filed as new issues; deferred items stay deferred per [P8-implementation-guide.md §10](P8-implementation-guide.md#10-scope-boundaries--what-does-not-change).

---

## References

| #   | Source                                                                                                  | Role                                                                              |
| --- | ------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------- |
| 1   | [P8-contribution-goal-and-definition.md](P8-contribution-goal-and-definition.md)                        | Phase 8 goal, scope, acceptance criteria, locked decisions                        |
| 2   | [P8-implementation-guide.md](P8-implementation-guide.md)                                                | Authoritative execution-level guide; per-task code sketches, test patterns, gates |
| 3   | [P8-triage.md](P8-triage.md)                                                                            | Triage of senior dev review #2 findings + CS-Go integration issues                |
| 4   | [`docs/code-review/017–024`](../../code-review/)                                                        | Per-finding authoritative "why"; option analyses; locked decisions                |
| 5   | [Issue #166](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/166)                                 | Part 2 `@link` fallback bug (Task 7)                                              |
| 6   | [Issue #167](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/167)                                 | Pagination-contract docs gap (Task A4)                                            |
| 7   | [PR #136 (camptocamp/ogc-client)](https://github.com/camptocamp/ogc-client/pull/136)                    | The upstream pull request being refreshed in Task E2                              |
| 8   | [P5-parser-completion-implementation-guide.md](../phase-5/P5-parser-completion-implementation-guide.md) | Phase 5 trio precedent                                                            |
| 9   | [P6-implementation-guide.md](../phase-6/P6-implementation-guide.md) + P6-ROADMAP                        | Phase 6 trio precedent (closest structural parallel)                              |
| 10  | [`docs/planning/ROADMAP.md`](../ROADMAP.md)                                                             | Original CSAPI implementation roadmap; structural template for this document      |
| 11  | [`docs/governance/AI_OPERATIONAL_CONSTRAINTS.md`](../../governance/AI_OPERATIONAL_CONSTRAINTS.md)       | Operational discipline; precedence rules                                          |
| 12  | [OGC 23-002](https://docs.ogc.org/is/23-002/23-002.html) — Connected Systems Part 2                     | Spec authority for §16.1 (`@link`/`@id`) — Task 7 acceptance gate                 |

---

## Operational Constraints (recap)

> **⚠️ MANDATORY:** Before starting any Phase 8 task, review [`docs/governance/AI_OPERATIONAL_CONSTRAINTS.md`](../../governance/AI_OPERATIONAL_CONSTRAINTS.md).

Phase 8 execution rails (identical to those in [P8-implementation-guide.md](P8-implementation-guide.md)):

- **Precedence:** OGC specs → AI Collaboration Agreement → [P8-contribution-goal-and-definition.md](P8-contribution-goal-and-definition.md) → [P8-implementation-guide.md](P8-implementation-guide.md) → this roadmap → per-finding MD → existing code → conversational context.
- **No scope expansion.** New ideas mid-execution become new issues, not new tasks.
- **Minimal diffs.** Smallest change that satisfies the per-task acceptance gate.
- **Locked decisions stay locked.** Surface deviations to the user; do not silently re-decide.
- **Two-repo workflow respected.** All source changes land on `phase-8` first; `clean-pr` is delivery-only.
- **Wontfix decisions stay closed.** #168 and #169 are not reopened without explicit user direction.
- **One commit per task on `phase-8`.** One squash on `clean-pr`. The history boundary is the deliverable boundary.
