# Deferred Findings — Final Disposition

**Date:** February 19, 2026  
**Purpose:** Provide definitive verdicts on the 6 findings not covered by the Phase 5 ROADMAP, closing out the question of whether any remaining work is in scope for the CSAPI client library contribution.  
**Related:** [Phase 5 Findings Coverage Analysis](p5-findings-coverage-analysis.md)

---

## Context

The [P5 Findings Coverage Analysis](p5-findings-coverage-analysis.md) identified 11 smoke test findings as potentially "fixable issues" within our CSAPI client library scope. Five are directly addressed by Phase 5 parser tasks (F27, F30, F31, F33, F38). This document provides the final disposition for the remaining six.

---

## Finding-by-Finding Verdicts

### P4-F1 — Command POST Hangs

**Verdict: Phase 4.2 scope. Real work, already planned.**

OSH holds the HTTP connection open on Command POST for streaming status updates (SSE pattern). This is a CRUD/write-path concern, not a parser gap. Smoke Test #19 targets it for Phase 4.2 — it needs a timeout strategy or SSE-aware handler.

---

### P4-F2 — OSH PUT Rejects UID Changes

**Verdict: Phase 4.2 scope. Real work, already planned.**

OSH rejects PUT if the `uid` in the request body doesn't byte-for-byte match the server-stored value. The library's update methods need to preserve the server-assigned uid exactly. This is a CRUD correctness concern, already targeted for Phase 4.2 in the ST#19 verdict.

---

### F82 — OSH Items Envelope Missing `links` Key

**Verdict: Already mitigated. No further work needed.**

`parseCollectionResponse()` already defaults `links` to an empty array when the key is absent. Confirmed as "Low" severity in Smoke Test #19. No code change required.

---

### F5 — Missing Pagination Metadata

**Verdict: Out of scope. Should not have been on the "fixable issues" list.**

Pagination touches `shared` and `ogc-api` — that's upstream territory. If we change how pagination detection works to handle missing `links` keys, we risk breaking WMS/WFS/WMTS pagination. This is either an upstream change or needs very careful scoping to avoid regressions in non-CSAPI endpoints. It does not belong in our CSAPI contribution scope.

---

### F14 — Properties Not Discoverable via Links

**Verdict: No remaining work. Already handled as well as it can be.**

This finding was initially flagged as needing a separate issue, but after thorough review of the actual code, there is nothing to fix.

#### What's Happening

Neither OSH nor 52North advertises `/properties` through link relations in their collection or root documents. Our `scanCsapiLinks()` function checks all three OGC link conventions (`ogc-cs:properties`, plain `"properties"` rel, and `rel: "items"` with `/properties` in href) and finds nothing — because there's nothing to find. The servers simply don't include the link.

#### What We've Already Done

1. **`properties` is in our known resource types list.** `CSAPIResourceTypes` in `model.ts` includes `'properties'`. If any server starts advertising properties via any of the three OGC link conventions, our code will discover it automatically with zero changes.

2. **`scanCsapiLinks()` already scans for it.** The function is convention-aware, not resource-type-aware. It doesn't skip properties — it checks every link against all three conventions. The issue is that no link matches, not that our scanner ignores properties.

3. **Documented the workaround.** The `scanCsapiLinks()` JSDoc explicitly states: *"Servers that do not use any of these three conventions will produce an empty map. In that case, consumers should supply explicit resource URLs via the `resourceUrls` constructor parameter of CSAPIQueryBuilder."*

4. **The QueryBuilder already supports direct URL construction.** A consumer can call `builder.getProperties()` directly — it builds the URL from the base path. Discovery via links is a convenience, not a requirement.

5. **Phase 5 Task 1 builds `parseProperty()`** ([Issue #78](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/78)), which will handle the response data once a consumer reaches the endpoint by any means.

#### Why There's Nothing More To Do

The only theoretical "fix" would be **probing** — automatically trying `/properties` even when no link advertises it. This is a bad idea because:

- It's speculative HTTP requests (trying URLs that might not exist), which is inconsistent with how the upstream `ogc-client` library handles resource discovery
- It would cause unexpected 404s on servers that genuinely don't implement properties
- It changes the library's design philosophy from "discover via advertised links" to "guess and probe"
- The workaround already exists — consumers provide the URL directly via `resourceUrls` or call `getProperties()` on the QueryBuilder

#### Scope Principle

The gap is on the server side (not advertising a working endpoint), not in our scanning logic. Our scanner is spec-correct: it implements all three OGC link relation conventions. Adding a probing fallback would be a design change that goes beyond the CSAPI parser/client contribution scope.

---

### F84 — 52N Procedure Misclassification

**Verdict: No remaining work. Already handled as well as it can be.**

This finding generated the most confusion across multiple reviews, so this section provides full clarity.

#### What's Happening

52North returns `featureType: "sosa:Sensor"` on its procedure resources. In the SOSA/SSN vocabulary, `Sensor` maps to System (sensors are a subtype of system). Our `getCSAPIResourceType()` function correctly resolves `sosa:Sensor` → `'System'`. The result is that 52North's procedure gets classified as a System instead of a Procedure.

#### What We've Already Done

1. **Reported upstream:** Filed as [Issue #16](https://github.com/52North/connected-systems-pygeoapi/issues/16) on `52North/connected-systems-pygeoapi`. The root cause is the server putting the wrong `featureType` value on procedure resources. Ball is in their court.

2. **Built a robust fallback path:** [Issue #50](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/50) added `classifyFeature()` in `classification.ts`, which accepts an optional endpoint-context hint. When our code fetches from `/procedures`, it provides that hint. The two-step logic:
   - First: try `getCSAPIResourceType()` (featureType-based classification)
   - If that returns non-null, trust it
   - If that returns null (e.g., 52North's null-featureType features), fall back to the endpoint hint

3. **Documented the design decision:** The classification priority (System > Deployment > Procedure > SamplingFeature) is deliberate and documented. `sosa:Sensor` legitimately maps to System per the OGC vocabulary.

#### Why There's Nothing More To Do

The only theoretical "fix" would be: **let endpoint hints override featureType**. This is a bad idea because:

- It would mean trusting the URL path over the server's declared type
- It would break classification for spec-compliant servers that serve mixed resource types from the same endpoint
- It's a 52North-specific workaround that doesn't generalize

The misclassification only affects **one resource on one server** (52North's single procedure). The data is still returned and usable — it's just labeled `System` instead of `Procedure` in the type field. If 52North fixes their `featureType` to return `sosa:Procedure` instead of `sosa:Sensor`, our classification will automatically produce the correct result with zero code changes.

#### Scope Principle

Adding server-specific workarounds (e.g., "if server is 52North then do X") would be scope creep. Our classification logic is spec-correct: it implements the OGC SOSA/SSN vocabulary mapping faithfully. The error is in the server's data, not in our mapping.

---

## Summary Table

| Finding | Verdict | Action Required |
|---------|---------|-----------------|
| **P4-F1** | Phase 4.2 scope | Timeout/SSE strategy for command POST |
| **P4-F2** | Phase 4.2 scope | Preserve server-assigned uid on PUT |
| **F82** | Already mitigated | None |
| **F5** | Out of scope | None — upstream concern |
| **F14** | Already handled | None — server-side gap, scanner is spec-correct, workaround exists |
| **F84** | Already handled | None — upstream bug, reported, fallback works |

**Net result:** Of the 6 deferred findings, 2 are real Phase 4.2 work (P4-F1, P4-F2), and 4 require no further action from our CSAPI contribution (F82 mitigated, F5 out of scope, F14 complete, F84 complete).
