# Design Notes — Removing Feature-Level Validators from Scope

**Date:** 2026-02-15  
**Context:** Phase 3.2 smoke test finding F49, upstream pattern analysis, contribution strategy  
**Status:** Design decision documented — implementation pending (see Issue #52)

---

## Problem Statement

The Phase 3.2 smoke test (finding F49) revealed that all 5 OSH SamplingFeatures are now correctly **recognized** as SamplingFeature resources (thanks to the SensorML vocabulary extension in Issue #49), but they fail **extraction** because they lack the `sampledFeature@link` property that the validator requires per the OGC spec.

The root cause is architectural: `extractCSAPIFeature()` calls `validateCSAPIFeature()` as a hard gate — if validation returns any errors, extraction throws and returns nothing. This means **100% of OSH SamplingFeatures are currently inaccessible through the client library**, even though they contain perfectly usable data (geometry, uid, name, featureType, validTime).

This finding prompted a broader examination: do the feature-level validators belong in this contribution at all?

---

## Current Design Tension

The current flow in `extractCSAPIFeature()` (lines 425–435 of `geojson.ts`) is:

```
recognize → validate → extract (on success) / throw (on failure)
```

This creates a hard coupling between validation and extraction. The validator correctly enforces the spec (SamplingFeatures require `sampledFeature@link`), but the extractor incorrectly uses validation as a precondition for extraction. The result: any server that returns slightly non-conformant data — even data that is 95% complete and perfectly usable — gets completely blocked.

The initial response was to decouple validation from extraction — keep the validators but stop using them as a gate. But further analysis revealed a more fundamental question: **should these validators exist in the contribution at all?**

---

## Upstream Pattern Analysis

A thorough audit of the upstream ogc-client library (camptocamp) across **every** existing format handler reveals a nuanced picture:

### Handlers with Zero Validation (WMS, WFS, WMTS, TMS)

The mature, established handlers perform **no validation** of server response data:

- **WMS** (`src/wms/capabilities.ts`, `src/wms/endpoint.ts`) — Pure extraction from XML. Returns `null`/`undefined` for missing data. Has explicit TODO comments: `// TODO: check supported CRS`, `// TODO: check supported output formats`.
- **WFS** (`src/wfs/capabilities.ts`, `src/wfs/featureprops.ts`) — Zero validation on capabilities parsing. One structural check: is this a GeoJSON `FeatureCollection`?
- **WMTS** (`src/wmts/capabilities.ts`, `src/wmts/endpoint.ts`) — Zero validation. Returns `null` for missing data. Silent `NaN` fallback for bbox parsing.
- **TMS** (`src/tms/link-utils.ts`) — Root element name checking only (is this a `<TileMapService>` or `<TileMap>` element?).

### The STAC Exception — Inline Required-Field Validation

The STAC handler (`src/stac/info.ts`) is a **notable exception**. It performs spec-level structural validation before allowing extraction:

- `parseStacCatalog()` — checks 5 required fields (`stac_version`, `type`, `id`, `description`, `links`)
- `parseStacCollection()` — checks 7 required fields (`stac_version`, `type`, `id`, `description`, `license`, `extent`, `links`), with the explicit comment: _"After validation, we know the document has the correct structure"_
- `parseStacItem()` — checks 4 required fields (`type`, `id`, `properties`, `links`)
- `parseEndpointInfo()` — checks 3 required fields (`id`, `description`, `stac_version`)

This is validate-then-extract in the same function — if a required field is missing, `EndpointError` is thrown, the caller gets nothing.

### How STAC Validation Differs from CSAPI Validation

| Aspect          | STAC validation                          | CSAPI validation                                               |
| --------------- | ---------------------------------------- | -------------------------------------------------------------- |
| **Structure**   | Inline `if/throw` in each parse function | Separate `validate*()` functions returning `ValidationError[]` |
| **Granularity** | ~20 presence checks (truthy / is-array)  | ~50+ checks including URI format, nested objects, cross-field  |
| **Error type**  | Simple `EndpointError` (string message)  | Structured `ValidationError` (severity, path, message)         |
| **Coupling**    | Validation IS extraction (same function) | Validation separate, then gated extraction                     |
| **Formality**   | Ad-hoc                                   | Formal validation framework                                    |

### EDR — Client-Side Input Validation Only

The EDR handler (`src/ogc-api/edr/url_builder.ts`) validates **client input parameters** (does the collection support this query type? is this CRS valid?), not server response data. This is a different concern entirely and is analogous to our `validateLimit`/`validateBbox` functions (which we are keeping).

### OGC API Core — Conformance Checks Only

`src/ogc-api/link-utils.ts` and `src/ogc-api/info.ts` check landing page conformance links and document fetchability. This is endpoint-level discovery, not response data validation.

### Corrected Assessment

The earlier claim of "zero validation across all upstream handlers" was inaccurate. The honest framing:

> The mature WMS, WFS, WMTS, and TMS handlers perform **zero validation** of server response data — they blindly extract values with no structural or spec-compliance checking. However, the **STAC handler is a notable exception** — it validates ~20 required fields per the STAC spec before allowing extraction. No handler has a **formal validation framework** with structured error objects, severity levels, and per-field paths like our CSAPI validators do. The STAC validation is ad-hoc `if/throw` patterns inline within parse functions.

### Why We Still Remove (Not Adopt the STAC Pattern)

The STAC handler demonstrates that upstream _has_ used inline required-field checks. But adopting that pattern for CSAPI would reproduce the F49 problem:

1. **STAC's pattern has the same fragility.** If a real STAC server omits `license` from a Collection response, `parseStacCollection()` throws and the caller gets nothing. That's F49 — validators blocking access to usable data.
2. **Connected Systems servers are less mature than STAC servers.** OSH (OpenSensorHub) is an early implementation; its responses frequently omit spec-required fields like `sampledFeature@link`. STAC servers tend to be more compliant because STAC is a more mature ecosystem.
3. **The dominant upstream pattern is tolerance.** The older, more established handlers (WMS, WFS, WMTS) all follow Postel's Law. The STAC inline validation is the exception, not the rule.
4. **If upstream reviewers later want STAC-style guards** on truly fundamental fields (like `id`), that's a 10-line PR — not a 500-line validation framework.

---

## Decision: Remove Feature-Level Validators Entirely

After examining the upstream patterns, the conclusion is clear: **the feature-level validators (`validateCSAPIFeature`, the 13 per-type validators, the `ValidationError` type) should be removed from the contribution scope entirely.**

### What We Built (Now Being Removed)

- `validateCSAPIFeature()` in `geojson.ts` — unified validation entry point
- 13 per-type validators in `helpers.ts` (`validateSystem`, `validateDeployment`, `validateProcedure`, `validateSamplingFeature`, `validateProperty`, `validateDataStream`, `validateObservation`, `validateControlStream`, `validateCommand`, plus partial validators)
- `ValidationError` type with path, message, severity
- ~300+ lines of validation code
- ~200+ lines of validation tests

### Why Remove (Not Just Decouple)

Initially, the plan was to decouple validation from extraction — keep the validators as opt-in diagnostics. But this still raises the question: **would the upstream accept 500+ lines of code (validators + tests) for a formal validation framework that no other handler has?**

The STAC handler _does_ have inline required-field checks, but those are ad-hoc `if/throw` patterns within parse functions — not a separate validation layer. Our validators are a qualitatively different thing: a formal framework with structured `ValidationError[]` objects, severity levels, property paths, per-type validator functions, and cross-field checks. Here's why that framework should be removed:

1. **No precedent for a formal validation framework.** While STAC has inline required-field checks, no handler has separate `validate*()` functions, `ValidationError` types, or structured error arrays. The upstream reviewers would ask "why does CSAPI need a validation _framework_ when STAC gets by with inline checks?"

2. **No caller.** After decoupling from extraction, no code in the library calls the validators. They exist only for external callers who might want conformance checking — a use case the library does not serve for any other API.

3. **Maintenance burden.** Validators must track spec changes. If OGC Part 1 changes `sampledFeature@link` from required to optional, someone has to update the validator. The upstream maintainers would inherit this burden for a feature they didn't ask for.

4. **Scope creep.** A contribution that adds 500+ lines of code for a formal validation framework with no precedent and no consumer will be seen as scope creep, regardless of how well-implemented it is.

5. **Wrong layer.** Validation is a server-side responsibility (validate inputs before persisting) or an application-side concern (the consuming app can implement its own validation rules). The client library sits between these layers — its job is transport and parsing, not enforcement.

6. **STAC-style inline checks would reproduce F49.** If we simplified to STAC's pattern (`if (!field) throw`), we'd block all OSH SamplingFeatures that lack `sampledFeature@link`. The whole point of F49 is to be _more tolerant_, not to replicate a fragility pattern.

### What Stays

- **Recognition** (`isCSAPIFeature`, `getCSAPIResourceType`) — stays. This is core to extraction and has clear purpose.
- **Extraction** (`extractCSAPIFeature`) — stays. This is the primary function of the handler.
- **Type system** (all interfaces in `model.ts`) — stays. TypeScript types provide compile-time safety.
- **Helper utilities** (`parseValidTime`, `isValidUri`, `buildAtLinkObject`) — stay. These serve extraction.
- **Format detection** (`mime-type.ts` extensions) — stays. This is infrastructure.

### What Goes

- `validateCSAPIFeature()` — removed from `geojson.ts`
- All 13 per-type validators — removed from `helpers.ts`
- `ValidationError` type — removed from `helpers.ts`
- All validation tests — removed from `geojson.spec.ts` and `helpers.spec.ts`
- The validation gate in `extractCSAPIFeature()` — removed (extraction relies only on recognition)

### What We Learned

The validators were not wasted effort. Building them forced deep engagement with the OGC Part 1 and Part 2 specs — understanding required fields, URI constraints, temporal validity rules, association integrity requirements. That knowledge is embedded in the type system and extraction logic. The validators were the scaffolding; the types and extractors are the building.

---

## Design Principles Applied

1. **Postel's Law** — Be liberal in what you accept from servers. Server-side responsibility for validation, client-side responsibility for access. The mature WMS/WFS/WMTS handlers follow this; STAC's inline checks are the exception.
2. **Upstream Consistency** — Match the dominant upstream pattern: tolerant extraction without a formal validation framework. While the STAC handler has inline required-field checks, no handler has a separate `validate*()` layer. Our contribution should not introduce a new architectural pattern.
3. **Minimal Contribution Surface** — A contribution should add what the library needs, not what might be nice to have. The upstream reviewers evaluate additions by necessity and precedent.
4. **Data Accessibility** — A client library that blocks access to usable server data is failing its core purpose. Validators can only block, never enable.
5. **Maintenance Stewardship** — Don't hand upstream maintainers code they'll need to maintain without clear benefit. Validators are maintenance debt for a feature with no upstream consumer.

---

## Impact Assessment

- **Lines removed:** ~500+ (validators + validation tests)
- **Lines changed:** ~20-30 (`extractCSAPIFeature` updated to rely only on recognition, JSDoc updates)
- **Risk:** Low — removing code is lower risk than adding or changing it
- **Benefit:** Cleaner contribution, no maintenance burden, extraction immediately works for all recognized features (including OSH SamplingFeatures from F49)
- **Test Impact:** Validation tests are removed. Extraction tests updated to expect success for any recognized feature. All other tests unchanged.

---

## References

- **F49 (Phase 3.2 smoke test):** OSH SamplingFeatures lack `sampledFeature@link` — recognized but extraction blocked
- **F40 (Phase 3.1 smoke test, Issue #49):** SensorML vocabulary extension — the fix that made recognition work
- **Issue #51:** Unified validation surface refactoring — moved validators to helpers, which is how the tight coupling became visible
- **Issue #52:** Remove validators entirely and update extraction to rely only on recognition
- **Upstream patterns:** `src/ogc-api/endpoint.ts`, `src/wms/endpoint.ts`, `src/wfs/endpoint.ts` — all use tolerant extraction, none have validators
- **STAC handler:** `src/stac/info.ts` — inline required-field checks (~20 checks), the one upstream exception; uses ad-hoc `if/throw`, not a formal framework
- **OGC Part 1 spec (23-001):** SamplingFeature requires `sampledFeature@link` — the spec is correct; but enforcement belongs to servers, not client libraries
