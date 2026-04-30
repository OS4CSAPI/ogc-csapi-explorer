# Phase 8: API Design Review — Triage

**Version:** 0.1 (draft)
**Date:** April 28, 2026
**Status:** Triage — no execution plan yet
**Source:** Senior developer's second code review (API design pass) of the `phase-7` clean-pr state

---

## Background

The senior developer's first code review (Phase 7) focused on type safety, DRY, and security.
This second review focused on **public API design** from a library consumer's
perspective: ergonomics, consistency, stability, extensibility, error contract,
and pagination.

We applied the same triage rules established for the first review:

1. **Upstream-authored code we did not write** → MD-only tracking, no GitHub issue, no fix.
   (See [docs/code-review/upstream-findings-report.md](../../code-review/upstream-findings-report.md).)
2. **New functionality / scope creep** → Defer with a tracking MD.
   (See [docs/code-review/110-deferred-enhancement-link-resolution-utilities.md](../../code-review/110-deferred-enhancement-link-resolution-utilities.md).)
3. **Anything else inside `src/ogc-api/csapi/`** → Fix in this phase.

---

## Findings Inventory

The review produced 10 distinct findings. Each has a tracking MD file under
[docs/code-review/](../../code-review/) numbered 017–026. The table below
summarizes triage decisions; rationale lives in each finding's MD.

| #    | Finding                                                                      | Triage                                        | MD                                                                                  |
| ---- | ---------------------------------------------------------------------------- | --------------------------------------------- | ----------------------------------------------------------------------------------- |
| 1    | URL-builder framing not obvious in docs                                      | **Accept** (docs only)                        | [017](../../code-review/017-pending-p3-docs-url-builder-framing.md)                 |
| 2a   | No `endpoint.csapi()` convenience method (asymmetry with `endpoint.edr()`)   | **Accept** (coordinated with 024)             | [018](../../code-review/018-pending-p3-endpoint-csapi-convenience-method.md)        |
| 2b   | `DataStream` (methods) vs `Datastream` (types/parsers) naming split          | **Accept** (Option A — rename)                | [019](../../code-review/019-pending-p2-method-naming-datastream-vs-datastream.md)   |
| 2c   | `getCommand(id, undefined, controlStreamId)` positional awkwardness          | **Defer**                                     | [020](../../code-review/020-deferred-p3-positional-controlstreamid-arg.md)          |
| 2e/5 | Validators throw plain `Error`; factory propagates `TypeError`               | **Accept**                                    | [021](../../code-review/021-pending-p2-validators-throw-plain-error.md)             |
| 3a   | Constructor exposes internal `OgcApiCollectionInfo` type                     | **Accept**                                    | [022](../../code-review/022-pending-p3-constructor-exposes-collection-info-type.md) |
| 3b   | `availableResources: Set<string>` should be `ReadonlySet<CSAPIResourceType>` | **Accept**                                    | [023](../../code-review/023-pending-p3-availableresources-set-typing.md)            |
| 3c   | `OgcApiEndpoint.root` and `getCollectionDocument` newly public               | **Accept** (Option A3 — coordinated with 018) | [024](../../code-review/024-pending-p2-endpoint-root-publicly-exposed.md)           |
| 4    | No `AbortSignal` for `createCSAPIBuilder` init fetches                       | **Defer** (enhancement)                       | [025](../../code-review/025-deferred-enhancement-abortsignal-in-factory.md)         |
| 6    | No pagination helper (`followNext` / async iterator)                         | **Defer** (enhancement)                       | [026](../../code-review/026-deferred-enhancement-follownext-pagination-helper.md)   |

### Counts

- **Accept (fix in Phase 8):** 7 findings → 017, 018, 019, 021, 022, 023, 024
  - **Coordinated pair:** 018 + 024 execute together (see each MD's
    "Coordination" section)
- **Defer (tracked, follow-up PR):** 3 findings → 020, 025, 026

---

## Overlap with Phase 7 Issues

The new review **does not** re-raise any Phase 7 finding (#141–#151 or the bundled
pre-existing bugs #98, #100, #102, #111, #139, #140). The Phase 7 fixes have held.

The closest overlap is finding 2c (positional `controlStreamId` argument), which
exists _because_ of #102 — adding nested-parent-ID parameters to command and
observation CRUD methods. The shape is awkward but the bug is fixed; redesigning
the signature is a wider change tracked in [020](../../code-review/020-deferred-p3-positional-controlstreamid-arg.md).

Finding 5 (`TypeError` propagated alongside `EndpointError`) partially overlaps
with the upstream-only findings 001/002 from the first review — the network-error
propagation comes from upstream `OgcApiEndpoint` code we did not author. The fix
on our side is wrapping in our `factory.ts`, tracked in [021](../../code-review/021-pending-p2-validators-throw-plain-error.md).

---

## Open Questions (need user input before drafting an execution plan)

1. ~~**For finding 2b (`DataStream` → `Datastream` rename):**~~ **RESOLVED
   April 28, 2026 — Option A (straight rename).** PR #136 has not been merged
   upstream and the CSAPI feature set has never shipped, so there are no
   downstream consumers; "breaking change" framing does not apply. See
   [019](../../code-review/019-pending-p2-method-naming-datastream-vs-datastream.md).

2. ~~**For finding 3c (`OgcApiEndpoint.root` exposed):**~~ **RESOLVED
   April 28, 2026 — Option A3 (re-privatize, compose via `endpoint.csapi()`).**
   Investigation surfaced commit `20a35d2` (Issue #122) as the historical
   context: the two public members are residue of the deliberate decoupling
   that moved `csapi()` and `extractRootResourceUrls()` out of
   `OgcApiEndpoint`. The factory only uses thin slices of `OgcApiDocument`,
   and the typed `getCollectionInfo()` already exists publicly. Option A3
   coordinates with finding 018 (add `endpoint.csapi()`): the new method
   does the composition privately, both flagged members revert to private,
   the standalone `createCSAPIBuilder` becomes value-shaped and pure, and
   the unsound `isCollectionInfo` cast disappears as a side benefit. See
   [024](../../code-review/024-pending-p2-endpoint-root-publicly-exposed.md)
   for the full investigation and option matrix.

3. **Two-repo workflow:** same `phase-8` (CSAPI_2) → patch → squash into
   `clean-pr` (ogc-client) flow as Phase 7?

---

## Out of Scope

Same exclusions as Phase 7 — recorded here for completeness:

- Upstream-authored security findings (001, 002, 005, 006) — see
  [upstream-findings-report.md](../../code-review/upstream-findings-report.md).
- Issue #110 (link resolution utilities) — still deferred per
  [110-deferred-enhancement-link-resolution-utilities.md](../../code-review/110-deferred-enhancement-link-resolution-utilities.md).
- New review's findings 4 and 6 (AbortSignal, pagination helper) — added to the
  "deferred enhancement" bucket alongside #110.
