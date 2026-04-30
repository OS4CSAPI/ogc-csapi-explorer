---
status: pending
priority: p2
issue_id: '021'
tags: [code-review, error-handling, api-design]
dependencies: []
phase: 8
---

# Error Contract Inconsistency — Validators Throw Plain `Error`; Factory Propagates `TypeError`

## Problem Statement

The CSAPI module's error contract mixes three error types depending on failure mode:

| Failure mode                                       | Error type      | Has `httpStatus`? |
| -------------------------------------------------- | --------------- | ----------------- |
| CSAPI not supported                                | `EndpointError` | No                |
| Invalid collection document                        | `EndpointError` | No                |
| Network failure (propagated from `OgcApiEndpoint`) | `TypeError`     | No                |
| Resource type unavailable                          | `EndpointError` | No                |
| Invalid `limit` / `bbox` / `datetime`              | plain `Error`   | No                |
| Malformed response body                            | plain `Error`   | No                |

Consumer `catch (e) { if (e instanceof EndpointError) ... }` patterns work for
some failure modes and silently miss others. Validators in `helpers.ts` and
parsers in `formats/` throw plain `Error`, breaking the narrowing.

## Findings

**Plain `Error` throws (should be `EndpointError`):**

- `src/ogc-api/csapi/helpers.ts` — `formatDateTimeParameter` (line 47, 77),
  `validateLimit` (line 216, 234), `validateBbox` (line 240, 245, 248)
- `src/ogc-api/csapi/formats/response.ts` — `parseCollectionResponse` (line 94, 106)
- `src/ogc-api/csapi/formats/part2.ts` — `requireObject` (line 48)
- `src/ogc-api/csapi/formats/property.ts` — `parseProperty` (line 42)
- `src/ogc-api/csapi/formats/schema-response.ts` — (lines 70, 150)
- `src/ogc-api/csapi/formats/geojson.ts` — (lines 446, 453)
- `src/ogc-api/csapi/formats/swecommon/_helpers.ts` — (line 75)

**TypeError propagation:**

- `src/ogc-api/csapi/factory.ts` — network errors from `endpoint.root` and
  `endpoint.getCollectionDocument` propagate as `TypeError`. The factory does
  not wrap them.

## Decision (locked April 29, 2026)

**Option A is adopted. No CSAPI-specific error subclass will be introduced.**

Rationale:

- `EndpointError` is the upstream-shipped public exception class (`src/shared/errors.ts`, exported from `src/index.ts`) already used by `stac/`, `wmts/`, and `ogc-api/endpoint.ts`. Consumers already write `catch (e) { if (e instanceof EndpointError) ... }`.
- The reviewer's concern was that narrowing was unreliable, not that finer-grained types were missing. Standardizing on a single existing class fixes the narrowing complaint with no public-surface expansion.
- `EndpointError` already carries `httpStatus` and `isCrossOriginRelated`, which covers every failure mode in the table above.
- Introducing `CSAPIError extends EndpointError` would be the first new public exception type added by the CSAPI work and would fail Phase 8's hard scope fence ("don't expand surface that wasn't asked for").
- If a future reviewer asks for finer typing, that becomes a new issue and a future phase.

This decision is reflected in [P8-contribution-goal-and-definition.md](../planning/phase-8/P8-contribution-goal-and-definition.md) (acceptance criterion A4 and Workstream 1, finding 021). It is not to be revisited within Phase 8.

## Proposed Solutions

### Option A: Validators → `EndpointError`; factory wraps network errors (**Adopted**)

1. Replace all `throw new Error(...)` calls in CSAPI helpers and parsers with
   `throw new EndpointError(...)`. The message stays the same; only the type
   changes.
2. In `createCSAPIBuilder`, wrap the two init `await` calls in a `try/catch`
   that re-throws non-`EndpointError` errors as `EndpointError` with the
   original error attached.

After: every error a CSAPI consumer can receive is `instanceof EndpointError`.

**Effort:** Small (mechanical replace + factory try/catch) | **Risk:** Low

### Option B: Document the mixed contract instead of fixing it (rejected)

Cheaper, but the reviewer's point — that `instanceof EndpointError` does not
reliably narrow — remains valid. **Rejected April 29, 2026.**

## Ownership Assessment

100% ours — all changes inside `src/ogc-api/csapi/`. The `TypeError` originally
comes from upstream's `OgcApiEndpoint`, but our fix is to wrap _in our factory_,
not modify upstream.

## Triage

**Accept — Phase 8.** Combines the reviewer's findings 2e and 5.
