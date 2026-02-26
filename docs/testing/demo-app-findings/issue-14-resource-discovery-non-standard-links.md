# Issue #14 Findings Report — Improve resource discovery to handle servers with non-standard link structures (F-11)

> **Date:** 2026-02-18
> **Issue:** [OS4CSAPI/ogc-csapi-explorer#14](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/14) — "Improve resource discovery to handle servers with non-standard link structures (F-11)"
> **Repository under review:** `OS4CSAPI/ogc-client-CSAPI_2` (`src/ogc-api/csapi/helpers.ts`, `src/ogc-api/csapi/url_builder.ts`)
> **Labels:** enhancement

---

## Table of Contents

1. [AI Operational Constraints Acknowledgment](#1-ai-operational-constraints-acknowledgment)
2. [Executive Summary](#2-executive-summary)
3. [Issue Description](#3-issue-description)
4. [Source Code Review](#4-source-code-review)
5. [Reference Document Review](#5-reference-document-review)
6. [Risk Assessment](#6-risk-assessment)
7. [Analysis: Proposed Solutions](#7-analysis-proposed-solutions)
8. [Recommendation](#8-recommendation)
9. [Appendix A: Authority Precedence Analysis](#appendix-a-authority-precedence-analysis)
10. [Appendix B: Cross-Reference Matrix](#appendix-b-cross-reference-matrix)

---

## 1. AI Operational Constraints Acknowledgment

Per the [AI Operational Constraints](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/governance/AI_OPERATIONAL_CONSTRAINTS.md), this review follows the required authority precedence:

1. **OGC specifications** — primary authority
2. **AI Collaboration Agreement** — governing constraints
3. **Issue description** — task scope
4. **Existing code patterns** — implementation precedent
5. **Conversation context** — supplementary guidance

This report does not propose behavioral modifications to the library without approval. All recommendations distinguish between **fact** (verified), **inference** (reasoned), and **proposal** (requires approval), per Section 3 of the constraints.

**Key constraint assessment for this issue:** Section 2.2 of the AI Operational Constraints states: _"Do not introduce new abstractions, layers, or dependencies without approval"_ and _"Preserve upstream structure, naming, and patterns unless explicitly instructed otherwise"_ and _"Prefer minimal diffs over idealized rewrites."_ Issue #14 proposes four separate solutions with varying degrees of architectural impact — ranging from documentation-only changes to multi-strategy HTTP-based discovery chains. **Section 2.2 is heavily triggered by three of the four proposals.** Multi-strategy discovery (Solution 1) would introduce a fundamentally new layer of HTTP-based resource probing. Lenient mode `tryGet` methods (Solution 3B) would approximately double the library's public API surface. Even the simpler flag-based options (Solutions 3A/3C) change the behavioral contract of `assertResourceAvailable()`, a method deliberately present as the first call in every public method.

---

## 2. Executive Summary

**Issue #14 proposes improving resource discovery in `CSAPIQueryBuilder` to handle servers whose link structures don't match the three conventions recognized by `scanCsapiLinks()`. After thorough review of the source code, 12 reference documents, and test coverage, this report recommends a CONSERVATIVE approach: improve JSDoc documentation (Solution 2) as the only change for the upstream contribution, and defer all behavioral changes. The existing `resourceUrls` constructor parameter already provides a complete consumer-side workaround, F-11 is actually a symptom of the much larger `OgcApiEndpoint` conformance gating problem, and the risk of introducing architectural changes to a deliberately designed validation system outweighs the benefit for a finding ranked #5 in priority.**

| Aspect                           | Assessment                                                                                                                                            |
| -------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Change type**                  | Ranges from documentation-only to new HTTP-based discovery layer, depending on which solution is adopted                                              |
| **Finding priority**             | #5 in upstream-findings.md — Medium severity, Medium effort, "Should Address" category                                                                |
| **Production behavior modified** | **None** for documentation; **Yes** for all other proposals                                                                                           |
| **Existing tests affected**      | **None** for documentation; behavioral changes would require test modifications to `assertResourceAvailable()` tests                                  |
| **Risk to library integrity**    | **None** (documentation) to **High** (multi-strategy discovery)                                                                                       |
| **New abstraction introduced**   | **No** (documentation/flag) to **Yes** (discovery chain, tryGet methods)                                                                              |
| **Upstream pattern precedent**   | **None** — upstream `ogc-client` has no analogous "lenient mode" or multi-strategy discovery                                                          |
| **AI Constraints trigger**       | **Section 2.2 heavily triggered** by Solutions 1, 3B, and 4; Section 2.1 triggered by Solution 1 (infers unstated requirement for HTTP-based probing) |
| **Existing workaround**          | **Yes** — `resourceUrls` constructor parameter already provides a complete bypass; demo app demonstrates this pattern                                 |

**Key findings from this review:**

1. **Fact:** `scanCsapiLinks()` recognizes three link conventions: (a) `ogc-cs:` prefix, (b) plain resource name matching `CSAPIResourceTypes`, (c) `items` rel with resource type in href. 52North's root document uses none of these conventions, yielding 0 discovered types.

2. **Fact:** Collection-level discovery works for **both** servers tested — OSH SensorHub: 4 types, 52North: 5 types. The gap is only at root-level discovery.

3. **Fact:** The `resourceUrls` constructor parameter (lines 100–106, 122–128 of `url_builder.ts`) already provides a complete mechanism for consumers to bypass discovery and provide explicit resource URLs. The demo app uses exactly this pattern to work with 52North.

4. **Fact:** `assertResourceAvailable()` is a deliberate, verified design choice. It is tested in `url_builder.spec.ts` with at least 20+ test cases that verify it throws `EndpointError` for every resource type when unavailable. Changing its behavior would require modifying these tests.

5. **Fact:** Only 1 commit (`e73cff8`) has ever modified library source (`src/`) during the entire demo app development lifecycle. All other accommodations for server differences were implemented as demo-layer workarounds. This establishes a clear precedent of extreme conservatism toward library modifications.

6. **Inference:** F-11 is actually a **symptom** of the broader `OgcApiEndpoint` conformance gating problem documented in the [conformance-bypass-architecture-notes.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/conformance-bypass-architecture-notes.md). Both real CSAPI servers fail `OgcApiEndpoint` — 52North due to missing conformance declarations, OSH due to non-standard link relations. Addressing F-11 in `CSAPIQueryBuilder` alone would fix only one layer of a multi-layer problem.

7. **Inference:** The OGC Connected Systems API spec ([OGC 23-001](https://docs.ogc.org/is/23-001/23-001.html)) does **not** require servers to include CSAPI-specific link relations in the landing page. The spec defines resource endpoints at well-known paths but does not mandate how they are advertised. This means the discovery gap is a **library design limitation**, not a server bug — but it also means there is no spec-authoritative strategy for discovery fallback.

---

## 3. Issue Description

Issue #14 ([OS4CSAPI/ogc-csapi-explorer#14](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/14)) identifies that `CSAPIQueryBuilder`'s resource discovery depends entirely on the quality and format of link relations in the server's landing page or collection document. When a server uses link structures that don't match the three conventions recognized by `scanCsapiLinks()`, the builder's `availableResources` set is empty, and `assertResourceAvailable()` blocks access to all public methods even if the resources exist at their standard paths.

The issue proposes four solutions:

1. **Multi-strategy discovery** — Fallback chain: links → conformance classes → well-known path probing
2. **JSDoc documentation** — Document that `availableResources` reflects link scanning, not server capability
3. **Lenient mode** — Three variants: (A) `assumeAllAvailable` flag, (B) `tryGet` methods, (C) constructor option like `{ skipAvailabilityChecks: true }`
4. **Enhanced link scanning** — Add more pattern recognition to `scanCsapiLinks()`

---

## 4. Source Code Review

### 4.1 `scanCsapiLinks()` — `helpers.ts` lines 123–166

This function takes an array of link objects and returns a `Map<string, string>` of discovered resource types to their URLs. It implements three detection conventions:

**Convention 1 — `ogc-cs:` prefix (lines 134–138):** Matches `rel: "ogc-cs:systems"` → stores `"systems"` → URL. This is the most explicit CSAPI convention. OSH SensorHub uses this pattern; 52North does not.

**Convention 2 — plain resource name (lines 140–146):** Matches `rel: "systems"` when the rel string is a known value in `CSAPIResourceTypes`. OSH SensorHub uses this pattern for root links like `rel: "systems"`, `rel: "deployments"`, etc.

**Convention 3 — `items` with resource href (lines 148–163):** Matches `rel: "items"` where the href path segment (after stripping query params and trailing slashes) ends with a known resource type name. Also normalizes `featuresOfInterest` → `samplingFeatures`. This matches the OGC API Collections item link pattern.

**Test coverage:** 21+ tests in `helpers.spec.ts` (lines 139–243, 434–481) covering all three conventions, edge cases (missing href, deduplication, mixed valid/invalid relations), and normalization behavior. Well-tested.

### 4.2 `extractAvailableResources()` — `url_builder.ts` lines 188–204

This private method delegates entirely to `scanCsapiLinks()`:

```typescript
private extractAvailableResources(): Set<string> {
  const links = this.collection_?.links ?? [];
  return new Set(scanCsapiLinks(links).keys());
}
```

When `resourceUrls` is provided via the constructor, these are also merged into `availableResources`:

```typescript
// Lines from constructor logic — resourceUrls keys are added to availableResources
for (const key of this.resourceUrls_.keys()) {
  this.availableResources.add(key);
}
```

This means providing `resourceUrls` to the constructor **both** gives explicit URLs **and** marks those resource types as available, bypassing `assertResourceAvailable()` for those types.

### 4.3 `assertResourceAvailable()` — `url_builder.ts` lines 270–278

```typescript
private assertResourceAvailable(resourceType: string): void {
  if (!this.availableResources.has(resourceType)) {
    const available = [...this.availableResources].join(', ');
    throw new EndpointError(
      `Collection '${this.collection_.id}' does not support '${resourceType}' resource. ` +
      `Available resources: ${available || 'none'}`
    );
  }
}
```

This is called as the **first line** of every public method in `CSAPIQueryBuilder`. The error message includes the collection ID and the available resources list, which aids debugging. The method name and behavior clearly communicate that resource availability is a **prerequisite**, not a suggestion.

**Test coverage:** 20+ tests in `url_builder.spec.ts` verify that `EndpointError` is thrown for unavailable resource types across all resource categories (systems, deployments, procedures, sampling features, datastreams, observations, control streams, commands, system events, system history). This is thorough, deliberate, and tested — not an oversight.

### 4.4 `buildResourceUrl()` — `url_builder.ts` lines 224–245

When `resourceUrls_` contains a URL for the requested resource type, it uses that URL instead of computing a collection-relative path. This is the **existing escape hatch**: a consumer that knows resource URLs (e.g., from parsing the root landing page themselves) can provide them via the constructor, and the builder will use them directly.

### 4.5 Constructor — `url_builder.ts` lines 122–128

```typescript
constructor(
  private collection_: OgcApiCollectionInfo,
  resourceUrls?: Map<string, string>
) {
  this.resourceUrls_ = resourceUrls ?? new Map();
  this.baseUrl = this.extractBaseUrl();
  this.availableResources = this.extractAvailableResources();
}
```

The `resourceUrls` parameter is optional and already documented in JSDoc (lines 112–121). The demo app's `csapi-bridge.ts` uses this parameter to pass all 9 resource types when root-level discovery returns 0 types — exactly the fallback pattern Issue #14 wants to make easier.

---

## 5. Reference Document Review

### 5.1 Upstream Findings (`upstream-findings.md`)

F-11 is documented at priority #5 with Medium severity, Medium effort, and categorized as "Should Address" — the middle tier. It is below F-4 (Accept header, priority #1), F-2 (Content-Type helper, priority #2), F-6/F-7 (JSDoc/tests, priority #3/#4), and above F-8/F-9/F-10 (generic CRUD, type guards, constructor narrowing, priorities #6–#9).

**Relevance to recommendation:** This is not a critical finding. Its Medium effort assessment aligns with the analysis that any behavioral solution requires careful design.

### 5.2 Library Integration Report (`library-integration-report.md`)

Finding #5 documents the discovery gap: "Resource discovery depends on server link quality." The report recommends documentation improvement and suggests an `assumeAllResourcesAvailable()` option. Finding #3 documents the constructor design, and Finding #15 (the transitive dependency chain) was already resolved in commit `e73cff8`.

**Relevance to recommendation:** The integration report's own recommendation is conservative — documentation first, optional flag second.

### 5.3 Library Findings Gap Analysis (`library-findings-gap-analysis.md`)

F-11 is assessed as: "Partially [actionable] — design challenge." Medium effort. Status: "Documented but no issue created" (the issue was created later as #14). The gap analysis explicitly labels this a "design challenge" — not a straightforward fix.

**Relevance to recommendation:** The project's own analysis calls this a design challenge requiring careful thought, not a mechanical implementation.

### 5.4 Conformance Bypass Architecture Notes (`conformance-bypass-architecture-notes.md`)

**This is the most important reference document for this issue.** It documents that:

- The demo app **does not use `OgcApiEndpoint` at all** — it imports `CSAPIQueryBuilder`, `scanCsapiLinks()`, and other low-level modules directly.
- Both real CSAPI servers fail `OgcApiEndpoint` — 52North due to missing conformance declarations, OSH due to link rel `collections` instead of `data`.
- The demo's `initializeBuilder()` function implements the exact fallback pattern Issue #14 proposes: scan for CSAPI links → if none found → assume all 9 resource types at standard paths.
- This architecture is described as **"intentional and appropriate for a demo/testing tool"**.

**Critical finding:** The conformance bypass document identifies that `OgcApiEndpoint` is **"unusable with both real CSAPI servers tested"** and describes this as **"arguably the most significant finding from the demo project."** This means F-11 (scanning failure at root level) is a **subset** of a much larger problem: the entire `OgcApiEndpoint` public API path is broken for real CSAPI servers. Fixing only `scanCsapiLinks()` or adding a lenient mode to `CSAPIQueryBuilder` addresses one layer while the conformance gating and collections URL resolution layers remain broken.

**Relevance to recommendation:** Fixing F-11 in isolation is incomplete. The real fix requires addressing `OgcApiEndpoint`'s conformance gating and collections URL resolution — a much larger scope that is outside the CSAPI contribution's charter.

### 5.5 Contribution Goal Accuracy Assessment (`contribution-goal-accuracy-assessment.md`)

Confirms that `assertResourceAvailable()` being "called as the first line of every public method" is a documented, verified design pattern. The assessment describes the library as a "URL builder, not an HTTP client" — it constructs URLs but does not make HTTP requests. This is crucial context for evaluating Solution 1 (multi-strategy discovery), which would require the builder to make HTTP requests to probe server capabilities.

**Relevance to recommendation:** Adding HTTP-based probing to a URL builder fundamentally changes the library's architectural role.

### 5.6 Library Source Changes Audit (`library-source-changes-audit.md`)

Only 1 commit (`e73cff8`) has ever modified library source during the entire demo app development lifecycle. All other server accommodations (conformance bypass, fallback discovery, Content-Type handling, Accept header defaults, empty body handling, UID preservation) were implemented as demo-layer workarounds. This establishes a clear pattern: **the team does not modify library source lightly**.

**Relevance to recommendation:** Any proposed library change must meet a high bar of justification. The team has demonstrated that consumer-side workarounds are preferred over library modifications.

### 5.7 E2E Cross-Server Report (`e2e-cross-server-report.md`)

Finding #4 confirms that `scanCsapiLinks()` returns 0 types for the 52North root landing page. However, collection-level discovery succeeds for both servers (52North: 5 types, OSH: 4 types). The root-level failure only affects consumers who try to build a `CSAPIQueryBuilder` from root-level data without providing `resourceUrls`.

**Relevance to recommendation:** The problem scope is narrower than Issue #14 implies — it's specifically root-level discovery that fails, not all discovery.

### 5.8 E2E Write Operations Report (`e2e-write-operations-report.md`)

Confirms that builder URLs are correct and that CRUD operations succeed when the builder is properly configured. The builder configuration uses `scanCsapiLinks()` results and falls back to all 9 types at standard paths — the same pattern the demo's `initializeBuilder()` uses.

### 5.9 Endpoint Error Isolation Report (`endpoint-error-isolation-report.md`)

Documents the `EndpointError` isolation refactor (commit `e73cff8`) — the only library source change. Confirms that `assertResourceAvailable()` throws `EndpointError` and that this behavior is tested across 298 tests in `url_builder.spec.ts`. The report also confirms the import graph is clean and the CSAPI module has zero XML dependencies.

**Relevance to recommendation:** The careful documentation of the single library change, its 18-file scope, and comprehensive verification demonstrates the level of rigor expected for any library modification.

### 5.10 CRUD Smoke Test Findings (`crud-smoke-test-findings.md`)

Documents F-15 (empty body crash on 201) and F-16 (UID requirement on PUT). Both were resolved as demo-layer workarounds, not library modifications. This reinforces the pattern of consumer-side accommodation.

### 5.11 Schema Display Findings (`schema-display-findings.md`)

Documents F-13 (JSDoc conflates `f` with `obsFormat`/`cmdFormat`) and F-14 (no schema response parser). Not directly related to F-11 but confirms the pattern that JSDoc documentation improvements are lower-risk and higher-value than API surface changes.

### 5.12 AI Operational Constraints (`AI_OPERATIONAL_CONSTRAINTS.md`)

Directly relevant clauses:

- Section 2.1: _"Do not infer unstated requirements"_ — The OGC spec does not define a required discovery mechanism; Solution 1 infers that HTTP probing is expected.
- Section 2.2: _"Do not introduce new abstractions, layers, or dependencies without approval"_ — Multi-strategy discovery, tryGet methods, and lenient mode flags are all new abstractions.
- Section 2.2: _"Prefer minimal diffs over idealized rewrites"_ — Documentation improvement is the minimal diff.
- Section 2.3: _"Do not refactor for style, clarity, or 'best practice' unless explicitly requested"_ — The current `assertResourceAvailable()` behavior is correct; "improving" it is a design preference, not a bug fix.

---

## 6. Risk Assessment

### 6.1 Risk of NOT making changes

| Impact                                                                                                         | Severity                                                                               |
| -------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| Consumers using root-level data without `resourceUrls` see `EndpointError` for servers with non-standard links | Medium — but `resourceUrls` workaround exists                                          |
| JSDoc doesn't clearly explain that `availableResources` reflects links, not capability                         | Low — fixable with documentation                                                       |
| Developer experience for new library consumers is degraded                                                     | Low–Medium — the error message already lists available resources and the collection ID |

### 6.2 Risk of Solution 1 — Multi-strategy discovery

| Risk                                                                         | Severity                                                                                          |
| ---------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| **Architectural role change:** URL builder becomes HTTP client               | **High** — violates separation of concerns documented in contribution-goal-accuracy-assessment.md |
| **Async constructor or init method:** HTTP probing cannot be synchronous     | **High** — changes the entire API contract; current constructor is synchronous                    |
| **Network dependency in unit tests:** Tests would need HTTP mocking          | **Medium** — increases test complexity and fragility                                              |
| **Performance impact:** Additional HTTP round-trips on every instantiation   | **Medium** — probing `/systems`, `/conformance`, etc. adds latency                                |
| **AI Constraints Section 2.1:** Infers unstated requirement for HTTP probing | **High** — the OGC spec does not define a discovery protocol                                      |
| **AI Constraints Section 2.2:** Introduces major new abstraction             | **High** — a multi-strategy discovery chain is a new layer                                        |
| **Upstream rejection risk:** Fundamentally changes the module's purpose      | **High** — upstream reviewers may reject this scope change                                        |

### 6.3 Risk of Solution 2 — JSDoc documentation

| Risk                                                   | Severity                                          |
| ------------------------------------------------------ | ------------------------------------------------- |
| No behavioral change                                   | **None**                                          |
| Documentation may not be sufficient for all developers | **Low** — but it's the convention in `ogc-client` |

### 6.4 Risk of Solution 3A — `assumeAllAvailable` flag

| Risk                                                           | Severity                                               |
| -------------------------------------------------------------- | ------------------------------------------------------ |
| New constructor parameter or method changes public API         | **Low–Medium**                                         |
| Silences errors that protect consumers from server-side issues | **Medium** — `EndpointError` catches real problems too |
| No upstream precedent for "assume" flags                       | **Medium** — introduces a new pattern                  |
| AI Constraints Section 2.2: New abstraction                    | **Medium**                                             |

### 6.5 Risk of Solution 3B — `tryGet` methods

| Risk                                                                              | Severity                                      |
| --------------------------------------------------------------------------------- | --------------------------------------------- |
| Approximately doubles public API surface (~77+ methods × 2)                       | **High** — massive maintenance burden         |
| No upstream precedent                                                             | **High** — introduces an entirely new pattern |
| Consumers must choose between `getSystems()` and `tryGetSystems()` for every call | **Medium** — confusing DX                     |
| AI Constraints Section 2.2: Major new abstraction                                 | **High**                                      |

### 6.6 Risk of Solution 3C — Constructor option `{ skipAvailabilityChecks: true }`

| Risk                                                            | Severity                                                                               |
| --------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| New constructor option type changes public API                  | **Low–Medium**                                                                         |
| Silences all availability errors, not just discovery gaps       | **Medium** — consumers lose protection from real server issues                         |
| AI Constraints Section 2.2: New abstraction                     | **Medium**                                                                             |
| Functionally equivalent to what `resourceUrls` already provides | **Low** — consumers can achieve the same result by passing all types to `resourceUrls` |

### 6.7 Risk of Solution 4 — Enhanced link scanning

| Risk                                                                             | Severity                                                          |
| -------------------------------------------------------------------------------- | ----------------------------------------------------------------- |
| New pattern recognition may produce false positives                              | **Medium** — broader matching means more ambiguity                |
| What patterns to add is not spec-defined                                         | **Medium** — we'd be guessing at server conventions               |
| AI Constraints Section 2.1: Infers unstated conventions                          | **Medium**                                                        |
| Limited benefit: 52North doesn't use ANY recognizable CSAPI link pattern at root | **Low benefit** — the server simply doesn't advertise CSAPI links |

---

## 7. Analysis: Proposed Solutions

### 7.1 Solution 1: Multi-Strategy Discovery — REJECT

**Assessment: High risk, unclear benefit, violates architectural boundaries.**

The `CSAPIQueryBuilder` is documented and verified as a **URL builder**, not an HTTP client. Its constructor is synchronous. It takes a pre-fetched `OgcApiCollectionInfo` object and constructs URLs from it. Introducing HTTP-based probing would:

1. Require an async constructor or a separate `init()` method — changing the API contract for all consumers
2. Make the builder dependent on network availability — currently it works offline with cached data
3. Add HTTP round-trips for conformance checking, well-known path probing, and potentially collection enumeration
4. Introduce new error handling paths for network failures, timeouts, and auth requirements
5. Require extensive HTTP mocking in unit tests (currently the 298 tests are purely synchronous)

The [contribution-goal-accuracy-assessment.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/contribution-goal-accuracy-assessment.md) explicitly confirms the builder's role: _"URL builder, not an HTTP client."_ The [conformance-bypass-architecture-notes.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/conformance-bypass-architecture-notes.md) confirms that the demo successfully works by doing this probing **in the consumer layer** — exactly where it belongs.

AI Constraints Section 2.1 prohibits inferring unstated requirements. The OGC spec does not define a discovery protocol; adding one is a design decision, not a spec requirement.

### 7.2 Solution 2: JSDoc Documentation — ACCEPT

**Assessment: Zero risk, genuine value, addresses the real problem.**

The current JSDoc for the constructor (lines 110–121 of `url_builder.ts`) documents `resourceUrls` but does not explicitly explain:

- That `availableResources` reflects what `scanCsapiLinks()` found in the collection's link array
- That some servers don't advertise CSAPI resources via link relations, resulting in an empty `availableResources` set
- That `resourceUrls` is the recommended workaround for servers with non-standard link structures
- That consumers who perform their own discovery should pass results via `resourceUrls`

Improving this documentation is purely additive, zero-risk, and addresses the DX gap that Issue #14 identifies. It aligns with the library's existing pattern of JSDoc-driven API documentation and with AI Constraints Section 2.2 ("prefer minimal diffs").

### 7.3 Solution 3A: `assumeAllAvailable` Flag — DEFER

**Assessment: Low–medium risk, but functionally redundant with existing `resourceUrls` pattern.**

A consumer who wants to assume all resources are available can already achieve this by constructing a `resourceUrls` map with all 9 types:

```typescript
const allTypes = new Map(CSAPIResourceTypes.map((t) => [t, `${baseUrl}/${t}`]));
const builder = new CSAPIQueryBuilder(collection, allTypes);
```

This is exactly what the demo app's `initializeBuilder()` does. Adding a boolean flag like `assumeAllAvailable` would be syntactic sugar for this existing pattern.

While the sugar is convenient, it introduces a new constructor parameter or property that has no precedent in the upstream library, and it silences `assertResourceAvailable()` entirely — including for cases where the server genuinely doesn't support a resource type. The error message from `assertResourceAvailable()` is often the first signal a consumer gets that they're using the wrong resource type for a given collection.

**If the team decides behavioral change is warranted after the upstream contribution is submitted, this is the lowest-risk behavioral option.** But it should not be included in the initial contribution.

### 7.4 Solution 3B: `tryGet` Methods — REJECT

**Assessment: High risk, massive API surface expansion, no upstream precedent.**

`CSAPIQueryBuilder` has 77+ public methods. Adding `tryGet` variants for each would approximately double the public API surface to 150+ methods. This is:

- A maintenance burden for upstream maintainers
- Confusing for consumers (when to use `getSystems()` vs `tryGetSystems()`?)
- Architecturally unprecedented in the entire `ogc-client` library
- A violation of AI Constraints Section 2.2 ("do not introduce new abstractions")

The same outcome can be achieved by a consumer wrapping any call in `try/catch`:

```typescript
try {
  const url = builder.getSystems();
} catch (e) {
  if (e instanceof EndpointError) {
    // Resource unavailable — use fallback URL
    const url = `${baseUrl}/systems`;
  }
}
```

### 7.5 Solution 3C: Constructor Option `{ skipAvailabilityChecks: true }` — DEFER

**Assessment: Low–medium risk, slightly cleaner DX than 3A, but same concerns apply.**

Functionally equivalent to Solution 3A. The constructor option pattern is slightly more idiomatic (TypeScript options objects) but has the same fundamental issue: it disables a protective check that catches real problems, not just discovery gaps.

**Same deferral recommendation as 3A.**

### 7.6 Solution 4: Enhanced Link Scanning — DEFER (PARTIALLY ADDRESSABLE)

**Assessment: Low–medium risk, but unclear what patterns to add.**

52North's root landing page doesn't use ANY recognizable CSAPI-specific link pattern at the root level. The links it provides are generic OGC API Common links (`self`, `conformance`, `service-desc`, etc.). There is no CSAPI-specific link relation to recognize — the server simply doesn't advertise CSAPI resources in the landing page.

For servers that DO advertise resources but use a convention not yet recognized (e.g., a hypothetical `rel: "http://www.opengis.net/def/rel/ogc-csapi/1.0/systems"` full IRI pattern), adding recognition would be reasonable. However:

- No such server has been encountered in testing
- The OGC spec does not define a required link relation pattern for CSAPI resources
- Adding speculative pattern recognition risks false positives

**If a specific new convention is encountered during further testing, a targeted addition to `scanCsapiLinks()` would be low-risk and appropriate.** But proactively adding patterns for hypothetical conventions is speculative.

---

## 8. Recommendation

### 8.1 For the upstream contribution: Documentation only (Solution 2)

**ACCEPT Solution 2 — Improve JSDoc documentation for `CSAPIQueryBuilder` constructor, `availableResources`, and `scanCsapiLinks()`.**

Specific documentation improvements:

1. Add a JSDoc note to `availableResources` explaining it reflects link scanning results, not actual server capability
2. Add a `@remarks` or `@example` block to the constructor showing the `resourceUrls` workaround pattern for servers with non-standard links
3. Add a JSDoc note to `scanCsapiLinks()` listing the three conventions it recognizes and noting that servers not using these conventions will return an empty map
4. Optionally add a `@see` reference from `assertResourceAvailable()` to the constructor documentation about `resourceUrls`

### 8.2 REJECT for upstream contribution

- **Solution 1 (multi-strategy discovery):** Fundamentally incompatible with the library's URL-builder architecture. Adds HTTP dependencies, requires async constructor, and violates the separation of concerns documented across multiple reference documents.
- **Solution 3B (tryGet methods):** Approximately doubles the public API surface with no upstream precedent. The same outcome is achievable via `try/catch`.

### 8.3 DEFER for post-contribution consideration

- **Solution 3A (assumeAllAvailable flag):** Functionally redundant with existing `resourceUrls` workaround. If DX sugar is desired after the upstream contribution is accepted, this is the lowest-risk behavioral option.
- **Solution 3C (constructor skipAvailabilityChecks option):** Same as 3A; slightly different syntax for the same outcome.
- **Solution 4 (enhanced scanning):** Reasonable if a specific new link convention is encountered, but speculative without a concrete example.

### 8.4 The broader problem

F-11 is a symptom of the larger `OgcApiEndpoint` usability problem documented in [conformance-bypass-architecture-notes.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/conformance-bypass-architecture-notes.md). Both tested CSAPI servers fail the `OgcApiEndpoint` path entirely — 52North due to conformance gating, OSH due to link relation mismatch. The real fix involves:

1. `checkHasConnectedSystems()` duck-typing fallback (or lenient conformance checking)
2. `collectionsUrl` accepting `rel: "collections"` as well as `rel: "data"`
3. Possibly a higher-level "CSAPI service discovery" utility that orchestrates conformance, collections, and resource discovery

These are upstream architectural decisions that are **far beyond the CSAPI contribution's scope**. They should be proposed as upstream issues after the core contribution is accepted, not bundled into the initial PR.

### 8.5 Summary of disposition

| Solution                      | Disposition | Rationale                                                                                        |
| ----------------------------- | ----------- | ------------------------------------------------------------------------------------------------ |
| 1. Multi-strategy discovery   | **REJECT**  | Changes library from URL builder to HTTP client; no spec basis; violates AI Constraints 2.1, 2.2 |
| 2. JSDoc documentation        | **ACCEPT**  | Zero risk; genuine value; addresses DX gap; AI Constraints compliant                             |
| 3A. `assumeAllAvailable` flag | **DEFER**   | Redundant with `resourceUrls`; no upstream precedent; consider post-contribution                 |
| 3B. `tryGet` methods          | **REJECT**  | Doubles API surface; massive maintenance burden; achievable via `try/catch`                      |
| 3C. Constructor option        | **DEFER**   | Same as 3A; slightly different syntax                                                            |
| 4. Enhanced scanning          | **DEFER**   | No concrete new convention to target; would add if specific pattern encountered                  |

---

## Appendix A: Authority Precedence Analysis

| Authority Level               | Source                                                                                                                                  | Guidance for F-11                                                                                                                                                         |
| ----------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1. OGC specifications         | [OGC 23-001](https://docs.ogc.org/is/23-001/23-001.html), [OGC 23-002](https://docs.ogc.org/is/23-002/23-002.html)                      | Spec does NOT require servers to advertise CSAPI resources via link relations; resources exist at well-known paths. No discovery protocol is defined.                     |
| 2. AI Collaboration Agreement | [AI_OPERATIONAL_CONSTRAINTS.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/governance/AI_OPERATIONAL_CONSTRAINTS.md) | Section 2.1: Don't infer unstated requirements. Section 2.2: No new abstractions without approval; prefer minimal diffs. Section 2.3: Don't refactor for "best practice." |
| 3. Issue description          | [#14](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/14)                                                                         | Proposes 4 solutions; acknowledges `resourceUrls` exists; notes this is a "design consideration"                                                                          |
| 4. Existing code patterns     | `url_builder.ts`, `helpers.ts`                                                                                                          | `assertResourceAvailable()` is deliberate; `resourceUrls` is the existing escape hatch; `CSAPIQueryBuilder` is synchronous and has no HTTP dependencies                   |
| 5. Conversation context       | Prior findings reports, demo app experience                                                                                             | Team is extremely conservative about library changes; all server accommodations are in demo layer                                                                         |

**Conclusion:** All authority levels point toward documentation-only changes for the upstream contribution, with optional behavioral changes deferred to post-contribution.

---

## Appendix B: Cross-Reference Matrix

| Reference Document                                                                                                                                             | Relevance to F-11    | Key Finding                                                                                 |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------- | ------------------------------------------------------------------------------------------- |
| [upstream-findings.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/upstream-findings.md)                                                     | Priority ranking     | F-11 is #5, Medium severity, "Should Address" — not critical                                |
| [library-integration-report.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/library-integration-report.md)                       | Discovery gap        | Finding #5: Recommends documentation + optional flag — aligns with our recommendation       |
| [library-findings-gap-analysis.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/library-findings-gap-analysis.md)                 | Actionability        | "Partially actionable — design challenge" — confirms this is not straightforward            |
| [conformance-bypass-architecture-notes.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/conformance-bypass-architecture-notes.md) | Root cause           | F-11 is a symptom of the larger OgcApiEndpoint problem; both servers fail at a higher level |
| [contribution-goal-accuracy-assessment.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/contribution-goal-accuracy-assessment.md) | Architecture         | Library is a URL builder, not HTTP client; assertResourceAvailable is deliberate            |
| [library-source-changes-audit.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/library-source-changes-audit.md)                   | Change history       | Only 1 library commit in entire development lifecycle — team is very conservative           |
| [e2e-cross-server-report.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/e2e-cross-server-report.md)                             | Scope narrowing      | Collection-level discovery works for both servers; gap is root-level only                   |
| [e2e-write-operations-report.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/e2e-write-operations-report.md)                     | Validation           | Builder URLs are correct when properly configured; CRUD succeeds                            |
| [endpoint-error-isolation-report.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/endpoint-error-isolation-report.md)             | Error handling       | EndpointError isolation was the single library change; 298 tests pass                       |
| [crud-smoke-test-findings.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/crud-smoke-test-findings.md)                           | Pattern confirmation | F-15, F-16 both resolved as demo-layer workarounds, not library changes                     |
| [schema-display-findings.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/schema-display-findings.md)                             | Pattern confirmation | JSDoc improvements (F-13) are lower-risk and higher-value than API surface changes          |
| [AI_OPERATIONAL_CONSTRAINTS.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/governance/AI_OPERATIONAL_CONSTRAINTS.md)                        | Governance           | Sections 2.1, 2.2, 2.3 all support conservative approach                                    |
