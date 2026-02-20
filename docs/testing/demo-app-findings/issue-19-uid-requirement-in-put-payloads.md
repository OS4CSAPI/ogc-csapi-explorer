# Findings Report: Issue #19 — Document/Enforce uid Requirement in PUT Update Payloads (F-16)

> **Date**: 2026-02-18
> **Source Issue**: [OS4CSAPI/ogc-csapi-explorer#19](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/19)
> **Finding ID**: F-16 (from [crud-smoke-test-findings.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/crud-smoke-test-findings.md))
> **Labels on source issue**: `bug`

---

## AI Constraints Acknowledgment

> I have reviewed the AI Operational Constraints.
> Issue goal: Assess whether the `uid` requirement in PUT update payloads (F-16) requires a fix, documentation change, or any action in our CSAPI client library contribution.
> Assumptions requiring confirmation: None — the issue is well-documented with server evidence, a demo app workaround commit, and three proposed solutions.

---

## Executive Summary

Issue #19 reports that OSH SensorHub requires the `uid` field in the request body's `properties` object when updating a Part 1 resource via `PUT /systems/{id}` (and equivalently for deployments, procedures, and samplingFeatures). Omitting `uid` returns `400 "Invalid payload: Missing feature UID"`. The issue proposes three mitigation options: (A) document the requirement, (B) add a library-level "merge update" helper, or (C) enforce `uid` at the TypeScript type level. A workaround was applied in the demo app at commit [`d671f96`](https://github.com/OS4CSAPI/ogc-csapi-explorer/commit/d671f96).

**This issue does not affect our CSAPI client library contribution.** The ogc-client library's CSAPI module (`src/ogc-api/csapi/`) is a **pure URL builder** — it constructs endpoint URLs but does not construct, validate, or send HTTP request payloads. The `updateSystem(id)`, `updateDeployment(id)`, `updateProcedure(id)`, and `updateSamplingFeature(id)` methods each return a URL string (e.g., `PUT /systems/{id}`); the consumer is entirely responsible for constructing the JSON body that accompanies the PUT request. The library has zero `fetch()` calls, zero HTTP request construction code, and zero request payload assembly logic.

**Recommendation: NO ACTION REQUIRED** — The library does not participate in request payload construction. The `uid` field is already correctly typed as **required** (`uid: string`) on all four Part 1 resource interfaces (`System`, `Deployment`, `Procedure`, `SamplingFeature`), so consumers that use these types for their PUT payloads already receive TypeScript compile-time enforcement. There is nothing to fix, add, or document within our library contribution.

---

## Issue Description

### What the issue reports

When updating a Part 1 resource via HTTP `PUT /systems/{id}`, OSH SensorHub requires the `uid` field to be present in the request body's `properties` object, even though:
- The resource is already addressed by its server-assigned `id` in the URL
- The `uid` is server-assigned and immutable per the OGC spec
- No apparent reason exists for the server to require it in an update payload

Omitting `uid` returns:

```
400 Bad Request: "Invalid payload: Missing feature UID"
```

### Scope of impact (per the issue)

All four Part 1 resource types are affected:

| Resource Type | Update Method | Error Without `uid` |
|---|---|---|
| Systems | `PUT /systems/{id}` | 400 "Missing feature UID" |
| Deployments | `PUT /deployments/{id}` | 400 "Missing feature UID" |
| Procedures | `PUT /procedures/{id}` | 400 "Missing feature UID" |
| SamplingFeatures | `PUT /samplingFeatures/{id}` | 400 "Missing feature UID" |

### Proposed solutions (from the issue)

| Option | Description | Impact |
|---|---|---|
| A | Document the requirement | Consumer guidance only |
| B | Library-level "merge update" helper that fetches current resource, merges fields, ensures required fields preserved | New HTTP request + payload logic in library |
| C | Type-level enforcement via required TypeScript interface fields for update payloads | New type definitions in library |

### Workaround already applied

The demo app stores the `uid` from the CREATE phase and includes it in all subsequent UPDATE payloads:

```typescript
const uid = phase === 'create'
  ? `urn:csapi-explorer:smoke-test:${type}:${Date.now()}`
  : createdUids[type]  // Reuse original UID — OSH requires it
```

Applied at commit [`d671f96`](https://github.com/OS4CSAPI/ogc-csapi-explorer/commit/d671f96).

---

## Analysis

### The library's update methods return URL strings only

Each update method in `CSAPIQueryBuilder` follows the identical pattern — verify the resource type is available, then return a URL string:

```typescript
// src/ogc-api/csapi/url_builder.ts, line 358
updateSystem(id: string): string {
  this.assertResourceAvailable('systems');
  return this.buildResourceUrl('systems', id);
}
```

The same pattern holds for `updateDeployment()` (line 611), `updateProcedure()` (line 781), `updateSamplingFeature()` (line 950), and all other update methods. **None of these methods accept a payload parameter, construct a request body, or interact with HTTP in any way.** They return a string; the consumer decides what to PUT to that URL.

### The library has zero HTTP request handling code

A comprehensive search of the entire CSAPI source tree (`src/ogc-api/csapi/**`) — first performed during the Issue #18 analysis and reconfirmed here — yields:

| Search Term | Matches in `src/ogc-api/csapi/**` |
|---|---|
| `fetch(` | 0 |
| `payload` | 0 |
| `body` | 0 |
| `merge` | 0 |

The library does not construct HTTP requests, does not assemble request bodies, and does not send data to servers. It is architecturally impossible for the library to cause or prevent F-16.

### The `uid` field is already required on all Part 1 type interfaces

The library's type definitions in `model.ts` already declare `uid: string` (non-optional) on every Part 1 resource interface:

| Interface | Line | Declaration |
|---|---|---|
| `System.properties.uid` | 269 | `uid: string` |
| `Deployment.properties.uid` | 301 | `uid: string` |
| `Procedure.properties.uid` | 331 | `uid: string` |
| `SamplingFeature.properties.uid` | 361 | `uid: string` |

Any consumer that uses these interfaces to type their PUT request bodies already gets **compile-time enforcement** that `uid` must be present. This is the maximum enforcement a type-definition library can provide — and it already exists. Proposed Option C from the issue (type-level enforcement) is already implemented.

### Proposed Option B would violate architectural boundaries

Option B (a "merge update" helper) would require the library to:
1. **Make an HTTP GET request** to fetch the current resource state
2. **Deep-merge** the caller's partial update with the fetched state
3. **Return or send** the merged payload

This would fundamentally change the library's architecture from a URL builder to an HTTP client. Per the AI Operational Constraints (§2.2): *"Do not introduce new abstractions, layers, or dependencies without approval"* and *"Prefer minimal diffs over idealized rewrites."* Per the CSAPI Implementation Guide's Client Responsibility Model, the library's five responsibilities are Parse, Construct (URLs), Transform, Handle, and Validate — none of which involve assembling or sending HTTP request payloads.

### Conservation record

Across all 14 prior findings reports, exactly **one commit** (`e73cff8`) has ever modified library source code. All other accommodations were applied in the demo app (consumer layer). This finding follows the same pattern as Issue #18 (F-15), Issue #17 (F-14), and Issue #15 (F-12), where the issue was correctly identified as occurring in the consumer or HTTP handling layer, not in the URL builder library.

---

## Assessment of the Three Proposed Options

| Option | Assessment | Rationale |
|---|---|---|
| A. Document the requirement | **Not needed in library** | The library's JSDoc and type definitions already document `uid` as a required field. The demo app is the appropriate place for consumer-facing guidance. |
| B. Merge-update helper | **Would violate constraints** | Introduces HTTP requests, deep-merge logic, and a fundamentally new abstraction into the URL builder. Violates §2.2. |
| C. Type-level enforcement | **Already implemented** | All four Part 1 interfaces already declare `uid: string` as non-optional. TypeScript consumers already get compile-time enforcement. |

---

## Recommendation

**NO ACTION REQUIRED** in our CSAPI client library contribution.

### Justification

1. **The library does not construct request payloads.** Update methods return URL strings. The consumer is responsible for building the JSON body that accompanies the PUT request.

2. **Type-level enforcement already exists.** The `uid` field is declared as required (`uid: string`) on all four Part 1 resource interfaces. Consumers using these types for their payloads already get compile-time enforcement — proposed Option C is already implemented.

3. **The workaround is correctly placed in the consumer layer.** The demo app's fix at commit `d671f96` stores and reuses `uid` in the appropriate scope — the HTTP call site where the PUT body is assembled.

4. **Proposed alternatives would violate architectural constraints.** Option B (merge-update helper) would introduce HTTP request capabilities into the URL builder, fundamentally changing its architectural role. This violates §2.2 of the AI Operational Constraints.

5. **Precedent is consistent.** This is the fourth consecutive finding (F-12, F-14, F-15, F-16) where the issue lies in the HTTP request/response handling layer, not in the URL builder. All four have the same recommendation: no library changes needed.

---

## Cross-References

| Document | Relevance |
|---|---|
| [AI Operational Constraints §2.2](../../governance/AI_OPERATIONAL_CONSTRAINTS.md) | Prohibits new abstractions, requires minimal diffs |
| [CSAPI Implementation Guide](../../planning/csapi-implementation-guide.md) | Defines 5-responsibility Client Responsibility Model; no payload construction |
| [Issue #18 report (F-15)](issue-18-empty-body-201-response.md) | Same architectural analysis: zero `fetch()` calls in library, NO ACTION REQUIRED |
| [Issue #17 report (F-14)](issue-17-schema-response-parser.md) | DEFER — new abstractions violate constraints |
| [Issue #15 report (F-12)](issue-15-parse-location-header.md) | DEFER — library is a URL builder, not a response parser |
| [Issue #6 report (F-3)](issue-6-content-type-helper.md) | Related: Content-Type helpers for request payloads |
| [crud-smoke-test-findings.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/crud-smoke-test-findings.md) | F-16 original finding: severity Medium, workaround applied |
| [model.ts](../../src/ogc-api/csapi/model.ts) | Part 1 interfaces with `uid: string` (lines 269, 301, 331, 361) |
| [url_builder.ts](../../src/ogc-api/csapi/url_builder.ts) | Update methods return URL strings only (lines 358, 611, 781, 950) |
