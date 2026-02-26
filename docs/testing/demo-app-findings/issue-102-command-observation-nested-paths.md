# Issue #102 Findings Report — Command/Observation CRUD Methods Require Top-Level Endpoints

> **Date:** 2026-02-20
> **Issue:** [OS4CSAPI/ogc-client-CSAPI_2#102](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/102) — "URL builder: command/observation CRUD methods require top-level endpoints, fail on nested-only servers"
> **Repository under review:** `OS4CSAPI/ogc-client-CSAPI_2` (`src/ogc-api/csapi/url_builder.ts`)
> **Discovered by:** [OS4CSAPI/ogc-csapi-explorer#32](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/32) (CommandStatus history panel)
> **Labels:** bug, url-builder

---

## Table of Contents

1. [AI Operational Constraints Acknowledgment](#1-ai-operational-constraints-acknowledgment)
2. [Executive Summary](#2-executive-summary)
3. [Issue Description](#3-issue-description)
4. [Source Code Review](#4-source-code-review)
5. [Reference Document Review](#5-reference-document-review)
6. [Risk Assessment](#6-risk-assessment)
7. [Recommendation](#7-recommendation)
8. [Appendix A: Authority Precedence Analysis](#appendix-a-authority-precedence-analysis)
9. [Appendix B: Cross-Reference to Related Issues](#appendix-b-cross-reference-to-related-issues)

---

## 1. AI Operational Constraints Acknowledgment

Per the [AI Operational Constraints](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/governance/AI_OPERATIONAL_CONSTRAINTS.md), this review follows the required authority precedence:

1. **OGC specifications** (OGC 23-001 Part 1, OGC 23-002 Part 2) — primary authority
2. **AI Collaboration Agreement** — governing constraints
3. **Issue description** — task scope
4. **Existing code patterns** — implementation precedent
5. **Conversation context** — supplementary guidance

This report does not expand scope beyond what Issue #102 describes. Per §2.1 (do not infer unstated requirements), §2.2 (preserve existing patterns, prefer minimal diffs), and §2.3 (no refactoring for style), this report evaluates the existing implementation against the issue's claims before recommending any action.

---

## 2. Executive Summary

**Issue #102 identifies a real interoperability concern — 14 command and observation per-ID methods call `assertResourceAvailable('commands')` or `assertResourceAvailable('observations')`, which fails on servers that only expose these resources as nested sub-resources. However, this is fundamentally the same problem as Issue #100 (DEFERRED), applied to a specific 14-method subset with a different proposed solution (optional parent ID parameters instead of assertion removal).**

| Finding     | Description                                                                                                                                                                                                | Severity    | Recommendation                                               |
| ----------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------- | ------------------------------------------------------------ |
| **F-102.1** | Issue's core claim is **technically valid**: 14 command/observation per-ID methods fail on nested-only servers like OSH                                                                                    | VALID       | **DEFER** — subset of already-deferred Issue #100            |
| **F-102.2** | The create methods already work correctly with nested paths: `createCommand(controlStreamId)`, `createCommands(controlStreamId)`, `createObservation(datastreamId)` — confirming the **asymmetry** is real | CONFIRMED   | Pattern precedent exists for nested-aware methods            |
| **F-102.3** | The proposed fix (Option A: optional parent parameters) would change **14 method signatures** and require parallel test additions for each                                                                 | MEDIUM RISK | API surface expansion pre-contribution                       |
| **F-102.4** | This is a **strict subset** of Issue #100's scope (14 of 69 per-ID methods) with the same root cause (`assertResourceAvailable()` blocking per-ID access)                                                  | OVERLAP     | Should be resolved together with #100, not independently     |
| **F-102.5** | The `resourceUrls` constructor workaround already mitigates this — callers can register `commands` and `observations` as available resource types                                                          | MITIGATED   | Existing escape hatch works for both #100 and #102 scenarios |

**Conclusion:** Issue #102 is a well-documented, narrowly scoped manifestation of the same fundamental problem analyzed in Issue #100 — `assertResourceAvailable()` is overly strict for per-ID methods when the resource type is only available as nested sub-resources. The proposed solution differs (add optional parent parameters vs. remove assertions), but the timing concerns are identical: invasive API surface changes to a thoroughly tested module pre-contribution. **Recommend deferring alongside Issue #100**, with a note that the two issues should be resolved together in a post-contribution enhancement that addresses all 69 affected per-ID methods holistically.

---

## 3. Issue Description

Issue #102 reports that 14 methods for **commands** (7) and **observations** (7) require `commands` or `observations` to be discovered as top-level resource types. On servers like OpenSensorHub (OSH) that only expose these resources as nested sub-resources under control streams and datastreams respectively, these methods throw `EndpointError` before any URL is constructed.

The asymmetry with the create methods is the key observation:

| Pattern                                   | Methods                                                                                                | Behavior                                                             |
| ----------------------------------------- | ------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------- |
| **Create (nested-aware ✅)**              | `createCommand(controlStreamId)`, `createCommands(controlStreamId)`, `createObservation(datastreamId)` | Accept parent ID, assert parent type, build nested path              |
| **CRUD/sub-resource (top-level only ❌)** | 7 command methods + 7 observation methods                                                              | Assert `commands`/`observations` directly, build top-level path only |

**Real-world failure on OSH:**

```
builder.getCommandStatus('cmd-001')
// ❌ EndpointError: Collection 'csapi-explorer' does not support 'commands' resource.
//    Available resources: systems, deployments, procedures, samplingFeatures, properties

builder.getObservation('obs-001')
// ❌ EndpointError: Collection 'csapi-explorer' does not support 'observations' resource.
```

The OSH server returns `400 Bad Request` for top-level `/commands/{id}` and `/observations/{id}` — these resources genuinely only exist under their respective parent paths (`/controlstreams/{csId}/commands/{cmdId}`, `/datastreams/{dsId}/observations/{obsId}`).

---

## 4. Source Code Review

### 4.1 Affected Command Methods (7 top-level only)

All 7 command per-ID methods (`url_builder.ts` L2095–2329) follow the same pattern:

```typescript
getCommand(id: string, options?: QueryOptions): string {
  this.assertResourceAvailable('commands');          // ← blocks on nested-only servers
  return this.buildResourceUrl('commands', id, undefined, options);
}

getCommandStatus(id: string): string {
  this.assertResourceAvailable('commands');          // ← blocks
  return this.buildResourceUrl('commands', id, 'status');
}
```

Full list: `getCommand`, `updateCommand`, `deleteCommand`, `getCommandStatus`, `updateCommandStatus`, `getCommandResult`, `cancelCommand`.

### 4.2 Affected Observation Methods (7 top-level only)

All 7 observation per-ID methods (`url_builder.ts` L1706–1866) follow the same pattern:

```typescript
getObservation(id: string, options?: QueryOptions): string {
  this.assertResourceAvailable('observations');      // ← blocks on nested-only servers
  return this.buildResourceUrl('observations', id, undefined, options);
}

getObservationDatastream(id: string): string {
  this.assertResourceAvailable('observations');      // ← blocks
  return this.buildResourceUrl('observations', id, 'datastream');
}
```

Full list: `getObservation`, `updateObservation`, `deleteObservation`, `getObservationDatastream`, `getObservationSamplingFeature`, `getObservationSystem`, `getObservationHistory`.

### 4.3 Create Methods — Already Nested-Aware

The existing create methods demonstrate the correct nested pattern that Issue #102 proposes extending:

```typescript
// url_builder.ts L2142 — accepts controlStreamId, asserts controlStreams
createCommand(controlStreamId: string): string {
  this.assertResourceAvailable('controlStreams');
  return this.buildResourceUrl('controlStreams', controlStreamId, 'commands');
}

// url_builder.ts L2173 — same pattern for bulk creation
createCommands(controlStreamId: string): string {
  this.assertResourceAvailable('controlStreams');
  return this.buildResourceUrl('controlStreams', controlStreamId, 'commands');
}

// url_builder.ts L1594 — accepts datastreamId, asserts datastreams
createObservation(datastreamId: string): string {
  this.assertResourceAvailable('datastreams');
  return this.buildResourceUrl('datastreams', datastreamId, 'observations');
}
```

This precedent confirms that the builder already supports nested-path URL construction via `buildResourceUrl()` — the infrastructure exists, it's just not exposed on the CRUD/sub-resource methods.

### 4.4 Collection-Level List Methods (2 also affected, but appropriately)

The list methods `getCommands(options?)` and `getObservations(options?)` also assert their respective resource types. Unlike per-ID methods, these assertions are **appropriate** — listing all commands/observations requires a valid collection endpoint, which genuinely doesn't exist on nested-only servers.

### 4.5 buildResourceUrl() — Nested Paths Already Supported

The private `buildResourceUrl()` method (`url_builder.ts` L248–262) already produces correct nested paths when given a parent type, parent ID, and sub-path:

```typescript
private buildResourceUrl(
  resourceType: string, id?: string, subPath?: string, options?: QueryOptions
): string {
  const topLevelUrl = this.resourceUrls_.get(resourceType);
  const resourceBase = topLevelUrl
    ? topLevelUrl.replace(/\/+$/, '')
    : `${this.baseUrl}/${toUrlPathSegment(resourceType)}`;
  let url = resourceBase;
  if (id) url += `/${encodeResourceId(id)}`;
  if (subPath) url += `/${subPath}`;
  return url + this.buildQueryString(options);
}
```

Issue #102's proposed Option A would leverage this by passing `controlStreamId` as the `id` and a compound `subPath` like `commands/${commandId}/status`:

```typescript
// Proposed (from Issue #102):
getCommandStatus(id: string, controlStreamId?: string): string {
  if (controlStreamId) {
    this.assertResourceAvailable('controlStreams');
    return this.buildResourceUrl('controlStreams', controlStreamId, `commands/${id}/status`);
  }
  this.assertResourceAvailable('commands');
  return this.buildResourceUrl('commands', id, 'status');
}
```

This would work correctly with the existing `buildResourceUrl()` infrastructure.

### 4.6 Test Impact

The test suite has dedicated assertion validation blocks:

**Observation resource validation** (`url_builder.spec.ts` L2139–2159): 8 `toThrow(EndpointError)` assertions covering all 8 observation methods (including `getObservations` list method).

**Command resource validation** (`url_builder.spec.ts` L2559–2579): 8 `toThrow(EndpointError)` assertions covering all 8 command methods (including `getCommands` list method), plus 2 assertions for `createCommand`/`createCommands` when `controlStreams` is unavailable.

If the fix were applied to the 14 per-ID methods:

- **14 existing assertion tests** would need to be updated (they currently expect `EndpointError`; with the optional parent param, the no-parent-ID path would still throw, but new test paths for the parent-ID branch would be needed)
- **~28 new test cases** for the nested-path branches (14 methods × 2 scenarios: successful nested path + nested path with unavailable parent type)
- The existing `getCommands`/`getObservations` list method assertions would remain unchanged

---

## 5. Reference Document Review

### OGC API — Connected Systems Part 2 (OGC 23-002)

Issue #102 correctly references the OGC spec:

> - **§7.5** — Observations accessible via `/datastreams/{id}/observations` (nested) AND optionally `/observations` (top-level)
> - **§7.9** — Commands accessible via `/controlstreams/{id}/commands` (nested) AND optionally `/commands` (top-level)

This is accurate. The spec defines top-level command and observation endpoints as **optional**. A server that only implements the nested pattern is fully conformant. The URL builder's per-ID methods currently assume the top-level pattern is available, which is not guaranteed by the spec.

### Cross-Server Behavior (from Issue #102)

| Endpoint                                         | OSH SensorHub      | Spec Requirement         |
| ------------------------------------------------ | ------------------ | ------------------------ |
| `/controlstreams/{csId}/commands`                | ✅ Works           | Required (nested)        |
| `/controlstreams/{csId}/commands/{cmdId}`        | ✅ Works           | Required (nested)        |
| `/controlstreams/{csId}/commands/{cmdId}/status` | ✅ Works           | Required (nested)        |
| `/commands/{cmdId}`                              | ❌ 400 Bad Request | **Optional** (top-level) |
| `/commands/{cmdId}/status`                       | ❌ 400 Bad Request | **Optional** (top-level) |
| `/datastreams/{dsId}/observations`               | ✅ Works           | Required (nested)        |
| `/observations/{obsId}`                          | ❌ 400 Bad Request | **Optional** (top-level) |

### Relationship to Issue #100

Issue #102 is a **strict subset** of Issue #100:

| Dimension                      | Issue #100                                        | Issue #102                                         |
| ------------------------------ | ------------------------------------------------- | -------------------------------------------------- |
| **Root cause**                 | `assertResourceAvailable()` blocks per-ID methods | Same root cause                                    |
| **Scope**                      | All 69 per-ID methods across 9 resource types     | 14 per-ID methods for commands + observations only |
| **Proposed fix**               | Remove assertions from per-ID methods             | Add optional parent parameters to per-ID methods   |
| **`resourceUrls` workaround**  | Applicable                                        | Applicable                                         |
| **Recommendation in findings** | DEFER                                             | (this report)                                      |

The key difference is in the proposed solution: Issue #100 proposes **removing guards** (assertion deletion), while Issue #102 proposes **adding parameters** (signature expansion). Both approaches are backward-compatible but for different reasons:

- #100: Methods stop throwing → callers that catch `EndpointError` to detect unsupported resources may behave differently
- #102: Methods gain optional parameters → existing callers unaffected, but the API surface grows

### AI Operational Constraints

- **§2.1:** "Do not infer unstated requirements; do not expand scope." — The issue requests adding optional parent parameters to 14 methods. This is the defined scope.
- **§2.2:** "Preserve upstream structure/naming/patterns; prefer minimal diffs." — Adding optional parameters to 14 methods is a non-trivial API surface expansion. The existing methods follow a uniform pattern (assert own type, build own path). Adding branching logic creates a non-uniform pattern within the method bodies.
- **§2.3:** "No refactoring for style/clarity/'best practice'." — This is a behavioral enhancement, not a style change.

---

## 6. Risk Assessment

### Risk of Making Changes Now

| Risk                                  | Severity   | Description                                                                                                                                                                                                                                                                                                                           |
| ------------------------------------- | ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **API surface expansion**             | **MEDIUM** | 14 method signatures gain optional parameters, expanding the public API surface before upstream submission. Upstream reviewers will need to evaluate these additions.                                                                                                                                                                 |
| **Test suite growth**                 | **MEDIUM** | ~28 new test cases needed for nested-path branches, plus updates to 14 existing assertion tests. Test suite growth without proportional production value at this stage.                                                                                                                                                               |
| **Partial fix creates inconsistency** | **HIGH**   | Fixing 14 of 69 affected methods (commands + observations only) while leaving the other 55 per-ID methods (systems, deployments, procedures, etc.) unchanged creates an inconsistent API where some resource types support nested paths and others do not. Issue #100 addresses all 69 — resolving #102 alone creates a half-measure. |
| **Upstream contribution risk**        | **HIGH**   | Same as Issue #100 — the CSAPI library is pending upstream submission with a consistent, thoroughly tested design. Adding branching logic to 14 methods at this stage complicates the review without addressing the architectural question holistically.                                                                              |
| **Compound subPath fragility**        | **LOW**    | The proposed `buildResourceUrl('controlStreams', csId, 'commands/${cmdId}/status')` uses a multi-segment subPath string. While `buildResourceUrl()` handles this correctly today, it's a pattern not used elsewhere in the codebase — future refactoring of the URL builder could inadvertently break compound subPaths.              |

### Risk of Doing Nothing

| Risk                                                                 | Severity   | Description                                                                                                                                                  |
| -------------------------------------------------------------------- | ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Interoperability gap for nested-only command/observation servers** | **MEDIUM** | Callers cannot use the 14 affected methods on servers like OSH without the `resourceUrls` workaround or manual URL construction. This is a known limitation. |
| **Demo app complexity**                                              | **LOW**    | The explorer demo's workaround (extract parent ID from raw JSON, manually construct nested URL) is functional and documented in the issue.                   |
| **Post-contribution work required**                                  | **LOW**    | The change can be made after upstream acceptance, ideally as part of a holistic resolution of Issue #100 that addresses all 69 per-ID methods.               |

---

## 7. Recommendation

### **DEFER — Subset of Already-Deferred Issue #100, Same Timing Concerns**

Issue #102 identifies a **genuine interoperability concern** that is consistent with the OGC specification and confirmed by real-world OSH server behavior. The analysis confirms:

1. The issue's core claim is **technically valid** — 14 command/observation per-ID methods fail on nested-only servers
2. The **asymmetry with create methods is real** — `createCommand(controlStreamId)` works correctly while `getCommandStatus(commandId)` fails
3. The OGC spec **does not require** top-level command/observation endpoints (§7.5, §7.9)
4. The proposed fix **would work** — `buildResourceUrl()` already supports the nested path pattern

However, this report recommends **deferring the change** for the following reasons:

1. **This is a strict subset of Issue #100** — the root cause (`assertResourceAvailable()` blocking per-ID methods) is identical. Fixing 14 of 69 methods independently creates an inconsistent partial fix.
2. **The `resourceUrls` workaround applies equally** — callers can register `commands` and `observations` as available resource types via the constructor, bypassing the assertion for all methods at once.
3. **Pre-contribution API surface expansion is risky** — adding optional parameters to 14 methods grows the public API surface before upstream review, without holistically addressing the other 55 affected methods.
4. **Issues #100 and #102 should be resolved together** — a post-contribution enhancement that either removes assertions from all 69 per-ID methods (Issue #100 Option A) or adds optional parent parameters across all affected resource types would be more architecturally coherent.

### If the change IS made in the future:

The holistic approach would be to resolve Issues #100 and #102 together:

1. **Phase 1 (from #100):** Remove `assertResourceAvailable()` from all 69 per-ID methods. This is the simplest fix — one-line deletions — and `buildResourceUrl()` already has graceful fallback. This resolves the client library's interop gap without requiring callers to know parent IDs.

2. **Phase 2 (from #102):** For the specific case where servers don't support top-level paths at all (OSH returns 400), add optional parent parameters to methods where the caller is likely to have the parent context (commands → `controlStreamId`, observations → `datastreamId`). This provides a complete nested-path alternative.

Phase 1 alone may be sufficient — if `buildResourceUrl()` returns a valid top-level URL and the server rejects it, that's a server-side 400, not a client-side `EndpointError`. The caller can then try the nested path. Phase 2 adds convenience for known nested-only scenarios.

### Immediate Action: None

No code changes are recommended at this time. The `resourceUrls` constructor parameter and the demo app's manual URL construction provide adequate mitigation. The library's internal consistency should be preserved for the upstream contribution.

---

## Appendix A: Authority Precedence Analysis

| Authority Level                   | Source                                                                                                              | Ruling                                                                         |
| --------------------------------- | ------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------ |
| **1. OGC Specification**          | OGC 23-002 §7.5, §7.9 — top-level command/observation endpoints are optional; nested paths are the required pattern | **Supports** the change — spec allows nested-only servers                      |
| **2. AI Collaboration Agreement** | §2.2 — preserve structure, prefer minimal diffs                                                                     | **Opposes** the change now — 14 method signature changes + branching logic     |
| **3. Issue Description**          | #102 — add optional parent parameters to 14 methods                                                                 | Defines scope; does not mandate timing                                         |
| **4. Existing Code**              | Create methods already use nested pattern; CRUD methods uniformly use top-level pattern                             | **Partial support** — precedent exists but current uniformity favors deferring |
| **5. Conversation Context**       | User prioritizes protecting CSAPI contribution integrity; Issue #100 already deferred                               | **Strongly opposes** the change now                                            |

**Conclusion:** Authority level 1 (OGC spec) supports the change in principle. Authority levels 2, 4 (uniformity), and 5 oppose making it now. The strong overlap with already-deferred Issue #100 further supports deferring. The balance favors **deferring** to post-contribution, to be resolved holistically with Issue #100.

---

## Appendix B: Cross-Reference to Related Issues

| Issue                                                                                                                                                        | Repository         | Relationship                                                                                      | Status          |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------ | ------------------------------------------------------------------------------------------------- | --------------- |
| [#102](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/102)                                                                                            | ogc-client-CSAPI_2 | **This issue** — command/observation CRUD methods require top-level endpoints                     | Open            |
| [#100](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/100)                                                                                            | ogc-client-CSAPI_2 | **Parent issue** — `assertResourceAvailable()` overly strict for all 69 per-ID methods (DEFERRED) | Open (Deferred) |
| [#99](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/99)                                                                                              | ogc-client-CSAPI_2 | **Related** — `?f=` format support (already exists; NO ACTION)                                    | Closed          |
| [#101](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/101)                                                                                            | ogc-client-CSAPI_2 | **Adjacent** — `parseDataRecord()` complex types (FIX)                                            | Closed          |
| [#32](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/32)                                                                                              | ogc-csapi-explorer | **Discovery source** — CommandStatus history panel implementation                                 | Open            |
| [Issue #100 findings report](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/testing/demo-app-findings/issue-100-assert-resource-available.md) | ogc-client-CSAPI_2 | **Predecessor** — comprehensive analysis of all 84 assertion call sites; DEFERRED                 | Report exists   |

### Linked Reference Documents

| Document                         | Location                                                                                                                                                                                                | Relevance                                                                                    |
| -------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| AI Operational Constraints       | [docs/governance/AI_OPERATIONAL_CONSTRAINTS.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/governance/AI_OPERATIONAL_CONSTRAINTS.md)                                                 | §2.1 (no scope expansion), §2.2 (preserve structure/minimal diffs) — supports deferring      |
| Issue #100 Findings Report       | [docs/testing/demo-app-findings/issue-100-assert-resource-available.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/testing/demo-app-findings/issue-100-assert-resource-available.md) | Comprehensive analysis of the parent problem; DEFER recommendation                           |
| OGC API Connected Systems Part 2 | OGC 23-002, §7.5 (observations), §7.9 (commands)                                                                                                                                                        | Top-level endpoints are optional; nested paths under datastreams/controlstreams are required |
| `assertResourceAvailable()`      | `src/ogc-api/csapi/url_builder.ts` L320–327                                                                                                                                                             | The guard method causing the assertion failures                                              |
| `buildResourceUrl()`             | `src/ogc-api/csapi/url_builder.ts` L248–262                                                                                                                                                             | Already supports nested-path URL construction                                                |
| `createCommand()`                | `src/ogc-api/csapi/url_builder.ts` L2142                                                                                                                                                                | Nested-aware create method — demonstrates the correct pattern                                |
| `createObservation()`            | `src/ogc-api/csapi/url_builder.ts` L1594                                                                                                                                                                | Nested-aware create method — demonstrates the correct pattern                                |
| `resourceUrls` constructor param | `src/ogc-api/csapi/url_builder.ts` L150–175                                                                                                                                                             | Existing workaround applicable to both #100 and #102 scenarios                               |
