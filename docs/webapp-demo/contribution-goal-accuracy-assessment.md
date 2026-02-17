# Assessment of `contribution-goal-and-definition.md` (v1.1)

> **Date**: 2026-02-17  
> **Document Under Review**: [`docs/planning/contribution-goal-and-definition.md`](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/planning/contribution-goal-and-definition.md) (v1.1, February 13, 2026)  
> **Methodology**: Reviewed against the actual codebase in `src/ogc-api/csapi/` (the library source that is upstream of the demo app) and against the 20 findings documents in [`docs/webapp-demo/`](https://github.com/OS4CSAPI/ogc-csapi-explorer/tree/main/docs/webapp-demo).  
> **Purpose**: Determine whether the document is an accurate, true, complete, and comprehensive description of the CSAPI portion of the ogc-client library work done in the forked repo.

---

## Overall Verdict: Accurate in scope and intent, conservative on metrics, with two nuances worth noting

The document reads as a *pre-implementation charter* and it faithfully describes what was subsequently built. It under-promises relative to what was actually delivered. There are no false claims — though two items warrant qualification rather than correction.

---

## Claim-by-Claim Analysis

### Contribution Goal (Narrative)

> *"Enable developers to interact with sensor networks, observation data, and system control through the Camptocamp OGC Client Library using the same unified interface they already use for other OGC APIs."*

**Verified.** The `csapi()` factory method on `OgcApiEndpoint` (`src/ogc-api/endpoint.ts` L393) follows the exact same pattern as the pre-existing `edr()` method (`src/ogc-api/endpoint.ts` L342): check conformance → cache lookup → construct builder. The `hasConnectedSystems` property mirrors `hasEnvironmentalDataRetrieval`. A developer who knows how to use `endpoint.edr('collection')` already knows how to use `endpoint.csapi('collection')`. This is not aspirational — it's exactly what was built.

> *"Deliver a production-ready, specification-complete Connected Systems API (CSAPI) implementation…"*

This is the one phrase that invites scrutiny. Through our demo app testing, we discovered:

- **F-1**: `createDataStream()` generates a wrong URL (top-level instead of nested) — see [library-findings-gap-analysis.md](./library-findings-gap-analysis.md) finding F-1
- **F-2**: Three nested create methods are missing (`createDataStreamForSystem`, `createControlStreamForSystem`, `createSamplingFeatureForSystem`)
- The library is a **URL builder**, not an HTTP client — it does not perform fetch operations, manage authentication, or handle response deserialization end-to-end

"Specification-complete" is *arguably* accurate in the sense that all 9 resource types, all query parameters defined in Parts 1 & 2, and all URL patterns (canonical, nested, historical, CRUD) are covered. But the F-1 bug means one of those URL patterns generates an incorrect URL as shipped. This is a known, documented bug with an open issue ([#5](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/5)), not something the document is trying to hide — but a reader could interpret "specification-complete" as "bug-free," which it is not.

**Verdict: Essentially accurate, but "specification-complete" should be understood as "specification-scoped" — the API covers the full spec surface, with known bugs tracked in issues.**

---

### Core Integration

| Claim | Evidence | Verdict |
|---|---|---|
| "Single QueryBuilder class with 80 methods" | **82 total methods** (77 public CRUD methods + 5 private helpers) in `src/ogc-api/csapi/url_builder.ts` (2,034 lines) | **Accurate** (conservative) |
| "covering all 9 CSAPI resource types" | `CSAPIResourceTypes` constant in `src/ogc-api/csapi/model.ts` L31–L41: systems, deployments, samplingFeatures, procedures, properties, datastreams, observations, controlStreams, commands | **Verified** |
| "Factory method integration pattern following established library architecture (EDR pattern)" | `endpoint.csapi()` at `src/ogc-api/endpoint.ts` L393 mirrors `endpoint.edr()` at L342 structurally: conformance check → cache → construct | **Verified** |
| "Resource validation in all methods with fail-fast error handling" | `assertResourceAvailable()` is the first call in every public method; `validateLimit()` and `validateBbox()` fire during query string construction | **Verified** |
| "Complete query parameter support (spatial, temporal, hierarchical, relationship-based, property-based filters)" | 10 `QueryOptions` interfaces in `src/ogc-api/csapi/model.ts` covering `bbox`, `datetime`, `phenomenonTime`, `resultTime`, `issueTime`, `executionTime`, `q`, `id`, `uid`, `parent`, `systemId`, `procedureId`, `foiId`, `observedPropertyId`, `controlledPropertyId`, `recursive`, `currentStatus`, `f`, `crs`, `limit`, `offset`, `cursor` | **Verified** |
| "Both pagination modes (offset-based and cursor-based)" | `QueryOptions` has both `offset?: number` and `cursor?: string` at `src/ogc-api/csapi/model.ts` L130–L133. Our [pagination-offset-vs-cursor-explanation.md](./pagination-offset-vs-cursor-explanation.md) documents how both work in practice. | **Verified** |

---

### Format Support

| Claim | Evidence | Verdict |
|---|---|---|
| "SensorML 3.0 parser with complete type system" | 8 implementation files under `src/ogc-api/csapi/formats/sensorml/` (2,718 lines); 50 type definitions in `types.ts` (851 lines); covers PhysicalSystem, PhysicalComponent, SimpleProcess, AggregateProcess with full DescribedObject → AbstractProcess → AbstractPhysicalProcess hierarchy | **Verified** |
| "recursive component parsing" | Explicit recursion in both `physical-system.ts` L101 and `aggregate-process.ts` L95 — `parseComponentEntry()` calls back into the parent parser for inline nested components | **Verified** |
| "SWE Common 3.0 parser supporting all three encodings (JSON, Text/CSV, Binary) with schema validation" | **Nuance here.** JSON and Text/CSV encodings are fully implemented with actual value decoding in `data-array.ts`. BinaryEncoding is **parsed at the structural level** (byteOrder, byteEncoding, members array are all extracted) but byte-level decoding is explicitly out of scope (code comment: "binary byte-level decoding is out of scope"). Schema validation via `validateAgainstSchema()` in `parser.ts` is implemented. | **Partially accurate** — "supporting" Binary is a stretch; "recognizing and parsing" would be precise |
| "GeoJSON extensions recognizing all CSAPI-specific resource types" | `isCSAPIFeature()`, `getCSAPIResourceType()`, `extractCSAPIFeature()` in `geojson.ts` plus URI constant lookup tables in `constants.ts` covering all 9 resource types | **Verified** |
| "Format detection and content negotiation for all CSAPI media types" | `CSAPI_MEDIA_TYPES` array covers all 7 types. `classifyFeature()` in `classification.ts` handles detection with URL-path fallback for non-compliant servers. However, HTTP `Accept` header management is **not** in the format layer — the library is a URL builder, not an HTTP client. Content negotiation is guided by the format infrastructure (the `f` query param, the constants) but not performed at the HTTP level. | **Partially accurate** — detection is comprehensive; "negotiation" overstates what a URL builder does |

---

### Quality Standards

| Claim | Evidence | Verdict |
|---|---|---|
| "Full TypeScript type safety with three-tier type hierarchy (1,750-2,400 lines of interfaces)" | 2,349 total lines across 4 type files with 156 interface/type definitions. Three tiers: SWE Common → SensorML → CSAPI resources. | **Verified** (at the top of the claimed range) |
| ">80% test coverage" | 24 test files totaling 11,548 lines (vs 24 implementation files at 10,222 lines) — a 1.13:1 test-to-impl ratio by lines. **A coverage tool was not run as part of this assessment**, but the volume and structure (unit + integration tests for every module) suggest the 80% threshold is met. The 4 integration test suites cover cross-module workflows. | **Plausible but unverified** — would need `jest --coverage` to confirm the number |
| "JSDoc documentation for all public APIs" | Sampled 20+ public methods across 5 files — 100% had `@param`, `@returns`, `@throws`, `@see`, and most had `@example`. Class-level JSDoc on CSAPIQueryBuilder is ~80 lines. Module-level `@module` banners on all barrel files. | **Verified** |
| "Compliance with OGC API - Connected Systems specifications (Parts 1 & 2)" | All 9 resource types, Part 1 `datetime` and Part 2 `phenomenonTime`/`resultTime`/`issueTime`/`executionTime` temporal params, nested resource patterns, collection-scoped + root-level URL patterns. Through our demo app testing we confirmed compliance with the spec, though we also found that real servers (OSH) interpret the spec selectively — documented in [temporal-filtering-and-pagination-metadata.md](./temporal-filtering-and-pagination-metadata.md). | **Verified** |
| "Zero-breaking-change integration with existing library functionality" | All pre-existing exports preserved in `src/index.ts`. CSAPI code is entirely in its own directory (`src/ogc-api/csapi/`). The only non-CSAPI file modified was extracting `EndpointError` to its own module ([library-source-changes-audit.md](./library-source-changes-audit.md) confirms: 1 commit, pure refactor, zero behavioral change). | **Verified** |

---

### Deliverables

| Claim | Actual | Verdict |
|---|---|---|
| "24 implementation files (~4,614-6,094 lines)" | **24 files, 10,222 lines** | File count is **exact**. Line count is **significantly understated** — actual is ~1.7x the upper bound of the claimed range. |
| "22 test files (~4,040-5,340 lines)" | **24 files, 11,548 lines** | File count is **understated by 2**. Line count is **significantly understated** — actual is ~2.2x the upper bound. |
| "Complete API documentation" | JSDoc on 100% of sampled public APIs. No separate API reference site, but the JSDoc itself is unusually thorough (spec links, examples, parameter descriptions, throw documentation). | **Verified** (within the scope of inline documentation) |
| "Implementation conforming to all upstream library patterns and conventions" | EDR factory pattern, `EndpointError` usage, barrel file exports, cache pattern, conformance-class gating — all match upstream conventions. | **Verified** |

---

## Deep Dive: The Validation Scope Change

The contribution-goal document references "validation" in two places. During implementation, a significant design decision was made to remove an entire category of validation from scope. This section examines how that decision impacts the document's accuracy.

### Three Distinct Validation Concerns

The word "validation" in this codebase maps to three fundamentally different things:

| # | Validation Concern | Document Phrase | Status |
|---|---|---|---|
| 1 | **Client input validation** — Does the caller pass valid `limit`, `bbox`, resource type? | "Resource validation in all methods with fail-fast error handling" | **Remains — fully implemented** |
| 2 | **SWE Common schema validation** — Does an observation value conform to a DataComponent schema (type checks, range constraints, required fields)? | "with schema validation" | **Remains — fully implemented** (~500 lines in `swecommon/parser.ts` L847–L1406) |
| 3 | **Feature-level response validation** — Does a GeoJSON Feature returned by a server have all OGC-required fields with correct formats? | *Not explicitly mentioned* | **Removed — F49, Postel's Law** |

### What Happened During Implementation

The original intent (as articulated by the project lead before implementation began) was firm about including the capability to validate responses from the server. This encompassed all three concerns above. The implementation roadmap ([ROADMAP.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/planning/ROADMAP.md)) originally included Phase 3 Task 3: "Validator Extensions."

During Phase 3 implementation, the following sequence occurred:

1. **Feature-level validators were built** — `validateCSAPIFeature()` plus 13 per-type validators (`validateSystem`, `validateDeployment`, etc.), a `ValidationError` type with path/message/severity, totaling ~500 lines of validation code plus ~200 lines of tests.

2. **F49 was discovered** — When tested against the live OSH SensorHub, the validators blocked **100% of OSH SamplingFeatures** from extraction because they lacked the spec-required `sampledFeature@link` property. The data was perfectly usable (geometry, uid, name, featureType, validTime) but the validation gate made it completely inaccessible.

3. **Upstream pattern analysis** — A thorough audit of the upstream ogc-client library found:
   - The mature handlers (WMS, WFS, WMTS, TMS) perform **zero validation** of server response data — pure tolerant extraction following Postel's Law.
   - The STAC handler has inline required-field checks (~20 ad-hoc `if/throw` patterns), but **no handler has a formal validation framework** — no separate `validate*()` functions, no `ValidationError` types, no structured error arrays.
   - The EDR handler validates only **client input parameters** (valid CRS, supported query types), not server responses — analogous to concern #1 above.

4. **Design decision: remove entirely** — After analysis, the feature-level validators were removed from scope completely (not just decoupled from extraction). The rationale:
   - No upstream precedent for a formal validation framework
   - No caller within the library after decoupling from extraction
   - Maintenance burden on upstream maintainers for a feature with no consumer
   - Connected Systems servers (OSH) are early implementations with frequent spec-deviations
   - The STAC inline-check pattern would reproduce F49's fragility
   - A 10-line future PR could add STAC-style guards on fundamental fields if upstream reviewers want them

5. **Documented** — The decision is captured in:
   - [ROADMAP.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/planning/ROADMAP.md) Phase 3 Task 3: struck through with `🚫 OUT OF SCOPE` banner
   - [design-notes-validation-extraction-decoupling.md](../implementation/design-notes-validation-extraction-decoupling.md): 173-line rationale document
   - ROADMAP version history: v3.5 (decouple) → v3.6 (remove entirely)
   - `extractCSAPIFeature()` JSDoc: "Follows Postel's Law — extraction succeeds for any recognized feature, regardless of missing optional or required spec fields"

### What Survived vs. What Was Removed

**Still in the codebase:**

- `assertResourceAvailable()` — called as the first line of every public QueryBuilder method
- `validateLimit()` — rejects non-positive-integer limits
- `validateBbox()` — rejects malformed bounding boxes (wrong element count, NaN, Infinity, min > max)
- `validateAgainstSchema()` — validates observation values against SWE Common DataComponent schemas (type checks, range violations, required fields, array dimensions) — 500+ lines with full test coverage, exported from `swecommon/index.ts`
- `ValidationResult` and `ValidationError` types in the SWE Common parser

**Removed from the codebase:**

- `validateCSAPIFeature()` — unified GeoJSON feature validation entry point
- 13 per-type validators (`validateSystem`, `validateDeployment`, `validateProcedure`, `validateSamplingFeature`, `validateProperty`, `validateDataStream`, `validateObservation`, `validateControlStream`, `validateCommand`, plus partial validators)
- The validation gate in `extractCSAPIFeature()` — extraction now relies only on recognition, not conformance

### Impact on the Contribution Goal Document

**Literal accuracy**: The document's two validation phrases remain accurate. "Resource validation in all methods with fail-fast error handling" describes client input validation (concern #1), which is fully implemented. "With schema validation" describes SWE Common schema validation (concern #2), which is fully implemented. Neither phrase claims feature-level response validation.

**Intent accuracy**: The document was written when the original intent included server response validation. Someone reading only the contribution-goal document would not know that a formal feature-level validation framework was planned, built (~500+ lines), found to block real server data, and deliberately removed after upstream pattern analysis. The document is silent on this scope change — understandable for a planning document that predates implementation, but a gap for anyone assessing the full implementation story.

**Recommendation**: The document could benefit from a brief scope note acknowledging the change:

> *Feature-level response validation (validating server-returned GeoJSON features against OGC required fields) was evaluated during implementation and excluded. The library follows Postel's Law, consistent with the upstream codebase's dominant pattern of tolerant extraction. See `design-notes-validation-extraction-decoupling.md`.*

---

## What The Document Does NOT Cover (Gaps in Completeness)

These are things that **were actually built** but are **not mentioned** in the document:

1. **Command routing / fallback module** — `src/ogc-api/csapi/command-routing.ts` (144 lines + 230 test lines) handles servers that reject top-level `/commands`. This is a real-world interoperability feature that goes beyond a pure URL builder. Not mentioned.

2. **Response normalization** — `src/ogc-api/csapi/formats/response.ts` (115 lines + 193 test lines) normalizes both GeoJSON FeatureCollection and `items` envelope formats. This is important for interoperability. Not mentioned.

3. **`CsapiDateTimeParameter` extension** — The `'latest'` keyword extension for `resultTime` (`src/ogc-api/csapi/model.ts` L15) is a CSAPI Part 2 addition over the shared `DateTimeParameter` type. Not mentioned.

4. **Resource URL discovery from root API document** — The constructor accepts a `resourceUrls` map for servers that expose resources at the API root rather than under collections (`src/ogc-api/csapi/url_builder.ts` L118–L120). This dual-mode support is not mentioned.

5. **Known bugs** — F-1 (`createDataStream()` wrong URL) and F-2 (missing nested create methods) are documented in our [library-findings-gap-analysis.md](./library-findings-gap-analysis.md) and tracked in GitHub issues. The document doesn't acknowledge known limitations — understandable for a pre-implementation charter, but worth noting for accuracy.

6. **Feature-level validation scope change** — The removal of `validateCSAPIFeature()` and 13 per-type validators after F49 is a significant implementation-phase design decision not reflected in the document. See the [Deep Dive: The Validation Scope Change](#deep-dive-the-validation-scope-change) section above for full analysis.

---

## Summary

The document is **accurate, true, and comprehensive as a pre-implementation end-state vision**. It describes the architecture, scope, and quality bar that were in fact achieved. The nuances are:

- **Line count metrics are conservative** — the actual implementation is roughly 67–76% larger than claimed (10,222 vs ~5,354 midpoint for implementation; 11,548 vs ~4,690 midpoint for tests). This means the document under-promised and over-delivered, which is the safer direction for a planning document.

- **Two "partial" claims** — "supporting all three encodings" and "content negotiation" overstate slightly. Binary encoding is recognized and parsed but not decoded at the byte level. Content negotiation guidance exists via constants and the `f` query parameter, but HTTP-level `Accept` header management is outside the library's scope as a URL builder.

- **Validation scope change not reflected** — The document's two validation claims (client input validation and SWE Common schema validation) remain literally accurate. However, the broader original intent to validate server responses was explored during implementation and deliberately excluded after the F49 finding and upstream pattern analysis. The document does not mention this scope change, the rationale (Postel's Law, no upstream precedent), or the ~500 lines of validators that were built and removed. The full story is captured in [design-notes-validation-extraction-decoupling.md](../implementation/design-notes-validation-extraction-decoupling.md) and the [ROADMAP.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/planning/ROADMAP.md) version history (v3.5 → v3.6).

Neither of these rises to the level of "inaccurate." The document is an honest, lightly conservative description of what was built, written before implementation began. That's unusual for a planning document — they typically over-promise. This one didn't.
