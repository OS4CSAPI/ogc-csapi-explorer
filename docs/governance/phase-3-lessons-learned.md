# Phase 3 Implementation Lessons Learned

**Purpose:** Actionable lessons extracted from Phase 3 (Format Handling) code reviews, smoke tests, fix reports, and architectural decisions. Every remaining Phase 3 issue **must** be read alongside this document and the Phase 2 lessons (`phase-2-lessons-learned.md`). The Phase 2 lessons remain valid for URL-builder concerns; this document covers the distinct failure modes of parser/format handler code, type definitions, and real-world server tolerance.

**Version:** 1.0  
**Date:** February 15, 2026  
**Source documents:**

- `docs/implementation/phase-3.1-code-review.md` (Findings F1–F11, GeoJSON handler)
- `docs/implementation/phase-3.2-code-review.md` (Findings F1–F14, Format detector + Validator)
- `docs/implementation/live-server-smoke-test-post-phase-3.1.md` (Findings F40–F48)
- `docs/implementation/live-server-smoke-test-post-phase-3.2.md` (Findings F49–F51)
- `docs/implementation/design-notes-validation-extraction-decoupling.md` (Validator removal rationale)
- `docs/implementation/phase-3-smoke-test-rationale.md` (Why Phase 3 smoke tests are more valuable)
- ROADMAP v3.6 changelog (Phase 3 Task 3 removal)
- Issue #49 (SensorML vocabulary extension)
- Issue #51 (Unified validation surface)
- Issue #52 (Validator removal + STAC audit correction)

---

## How to Use This Document

When working on any Phase 3 issue:

1. **Read this document first** — before reading the issue body
2. **Read `phase-2-lessons-learned.md` second** — Lessons 8 (multi-server) and 10 (read-only smoke tests) are still mandatory
3. **Apply the upstream audit check** in Lesson 1 before building any new architectural layer
4. **Apply Postel's Law** per Lesson 2 — never gate extraction on validation
5. **Check the type naming rules** in Lesson 10 when defining types from external specs
6. **When in doubt about scope**, ask: "Does any upstream handler do this?" (Lesson 1)
7. **After smoke tests**, document findings formally per Lesson 7 — never fix during observation

---

## Lesson 1: Audit Upstream Before Building New Layers

**What happened:** Issue #16 built a formal validation framework (~500 lines, 13 per-type validators, `ValidationError` type, 61 tests). Phase 3.2 code review praised it (F4, F5, F8 — all positive). Then smoke test F49 revealed validators _blocked_ real-world data, and Issue #52's upstream audit discovered that **no upstream handler has a formal validation framework**. The entire feature was removed — ~500 lines of code and 61 tests deleted.

**Root cause:** Building what seemed "correct" from a spec perspective without first checking whether _any_ upstream handler (WMS, WFS, WMTS, TMS, STAC, EDR) uses the same pattern. The STAC handler has ~20 inline `if/throw` checks, but no handler has structured `ValidationError[]` returns, per-type validators, or a validation gate on extraction.

**Why it matters:** Code that has no upstream precedent cannot survive a contribution review. The upstream library maintains architectural consistency — a new pattern that only one handler uses is a pattern that will be rejected.

**This has happened twice:**

1. **Phase 2:** Worker extensions (Phase 4 Task 4.1) were removed from ROADMAP v3.1 — no upstream JSON API uses workers
2. **Phase 3:** Validators were removed from ROADMAP v3.6 — no upstream handler has a formal validation framework

**Action:** Before implementing any code that introduces a new _category_ of functionality (not just a new function within an existing category), answer these questions:

1. Does any upstream handler (WMS/WFS/WMTS/TMS/STAC/EDR) do this?
2. If yes, what pattern do they use?
3. If no, **stop and discuss with the human collaborator** — the feature likely belongs at the application layer, not the client library layer.

---

## Lesson 2: Postel's Law Governs Client Libraries

**What happened:** `extractCSAPIFeature()` used `validateCSAPIFeature()` as a hard precondition — any validation error threw and returned nothing. OpenSensorHub's SamplingFeatures lack the spec-required `sampledFeature@link` property (F49). Result: **100% of OSH SamplingFeatures were inaccessible** despite being perfectly usable data. The validator correctly identified a spec violation, but the validator-as-gate pattern turned "non-conformant" into "invisible."

**Root cause:** Treating validation as a precondition for extraction. The validate-then-extract pattern was modeled after STAC's `parseStacCollection()`, but STAC servers are more mature and compliant than CSAPI servers. Connected Systems is a newer standard with fewer conformant implementations.

**Why it matters:** Client libraries sit between servers and applications. Their job is to _make data accessible_, not to _enforce server compliance_. A validator can only block, never enable. The upstream dominant pattern is tolerance — WFS parses capabilities even when some `<Layer>` elements are malformed; WMS extracts what it can from non-conformant GetCapabilities responses.

**Action:**

- **Never gate extraction on validation.** Recognition (can we identify what this is?) should gate extraction, not validation (does this meet all spec requirements?).
- Validators are a diagnostic tool — opt-in, not opt-out.
- If a required field is missing, extract what's present and let the consumer deal with the absence.
- The guiding principle: **"Be conservative in what you send, be liberal in what you accept."** (RFC 761, Postel's Law)

---

## Lesson 3: Don't Couple Validation to Extraction

**What happened:** The extraction pipeline had this structure:

```
validate(feature) → if errors, throw → else extract(feature) → return typed result
```

This meant that the only way to get a typed result was to pass validation. When validation was strict (spec-correct), real-world data that failed validation was completely inaccessible to consumers.

**Root cause:** A reasonable-seeming architectural pattern (validate before processing) applied to the wrong context. Input validation before processing is appropriate for _inbound writes_ (protect the system). It's inappropriate for _inbound reads from third-party servers_ (the data is what it is).

**Correct pattern:**

```
recognize(feature) → if recognized, extract(feature) → return typed result
```

Recognition is lightweight: "Does this object have a `type` or `featureType` property we understand?" Extraction is tolerant: map every present field, ignore absent optional fields, provide a useful typed result.

**Action:** When building parsers:

1. Recognition gates extraction (cheap, structural check)
2. Extraction tolerates missing optional fields
3. Validation, if desired, is a separate opt-in call that consumers invoke after extraction

---

## Lesson 4: Don't Build Parallel Systems

**What happened:** Phase 3.1 created `validateCSAPIFeature` in `geojson.ts` returning `string[]`. Phase 3.2 created 13 per-type validators in `helpers.ts` returning `ValidationError[]`. These overlapped in scope but diverged in behavior — the `geojson.ts` validator checked SensorML vocabulary (F13), but the `helpers.ts` validators did not. Two surfaces doing almost-but-not-quite the same thing.

**Root cause:** "The old one is in geojson.ts, the new structured one goes in helpers.ts" — a natural instinct to keep new work in a new location. But the result was two incompatible validation paths with no clear winner.

**Why it matters:** Parallel systems diverge. The moment you have two validation surfaces, they will disagree on edge cases, one will be more complete than the other, and consumers won't know which to use.

**Action:** When extending existing functionality:

1. Either **replace** the existing surface (delete old, create new)
2. Or **delegate** from the existing surface to the new one (old wraps new)
3. Never create a second surface that overlaps with the first

This applies to all component types — parsers, validators, detectors, type systems.

---

## Lesson 5: Verify Upstream Claims by Reading Source

**What happened:** The initial version of `design-notes-validation-extraction-decoupling.md` stated: "zero validation across all upstream handlers." This was factually wrong — the STAC handler has ~20 inline required-field checks (`if (!collection.id) throw ...`). The document was corrected with a detailed STAC comparison table showing that STAC's pattern (inline `if/throw`) differs from a formal validation framework (`ValidationError[]` array return).

**Root cause:** Making claims about upstream code from memory rather than reading the actual source files. The claim was _directionally correct_ (no handler uses formal validation) but _factually wrong_ (STAC has inline checks).

**Why it matters:** In a contribution review, inaccurate claims about the codebase undermine the entire argument. If the reviewer finds one factual error, they question every other claim. The corrected assessment was actually _stronger_ — STAC's inline checks proved that even the most validation-heavy handler doesn't use a formal framework.

**Action:**

- When making claims about upstream patterns, **read the actual source files** and cite specific line numbers or function names.
- Distinguish between "no handler does X" (absolute, verifiable) and "no handler does X _this way_" (nuanced, more accurate).
- An accurate, nuanced claim is stronger than an absolute, inaccurate one.

---

## Lesson 6: Real-World Server Data Diverges from Spec

**What happened:** Phase 3 introduced a new failure category that Phase 2 never encountered: **servers returning real data that deviates from spec requirements.** This never arose in Phase 2 because the URL builder doesn't process server responses.

**Examples from smoke tests:**

| Finding | Server        | Divergence                                                                                         |
| ------- | ------------- | -------------------------------------------------------------------------------------------------- |
| F41     | 52North       | `featureType: null` in GeoJSON (spec requires a string)                                            |
| F42     | 52North       | `validTime: null` for deployments (spec requires a temporal extent)                                |
| F43     | 52North       | Procedures typed as `sosa:Sensor` (semantically wrong — `sosa:Procedure` expected)                 |
| F49     | OpenSensorHub | Missing `sampledFeature@link` on SamplingFeatures (spec-required)                                  |
| F50     | 52North       | Changed default content type from `application/json` to `application/sml+json` between smoke tests |

**Root cause:** Connected Systems is a newer standard. Server implementations are still maturing. Spec-conformant fixtures in unit tests cannot represent the full diversity of real-world responses.

**Why it matters:** Every parser must be designed to handle not just the spec-conformant case but also the "missing field," "null where string expected," and "unexpected value" cases. Unit tests with hand-crafted fixtures will pass, but live servers will break parsers that assume strict conformance.

**Action:**

- Design parsers with optional fields mapped loosely — missing or null values should not throw
- Write "minimal valid" fixture tests (only required fields present) alongside "full" fixture tests
- After implementing a parser, always run a smoke test against both live servers (Lesson 8 from Phase 2 still applies)
- When a smoke test reveals a divergence, document it — it becomes a test case for the parser

---

## Lesson 7: Phase 3 Smoke Tests Are Essential, Not Optional

**What happened:** The Phase 3 smoke test rationale document (`phase-3-smoke-test-rationale.md`) predicted that format handler smoke tests would be more valuable than Phase 2 URL builder smoke tests. This proved correct:

| Phase 2 Smoke Tests                        | Phase 3 Smoke Tests                                                                     |
| ------------------------------------------ | --------------------------------------------------------------------------------------- |
| Confirmed servers accept URLs (200 vs 400) | Discovered vocabulary gaps (F40), null fields (F41), validation-blocks-extraction (F49) |
| Low surprise rate — URLs are simple        | High surprise rate — real data shapes are unpredictable                                 |
| Validated outbound work                    | Validated inbound work ("where the surprises live")                                     |

**Root cause:** Phase 2 tests URL _construction_ (we control the output). Phase 3 tests data _parsing_ (we don't control the input). The space of possible inputs from real servers is vastly larger than the space of URLs we construct.

**Why it matters:** Smoke test F40 (SensorML vocabulary unrecognized) made 100% of OSH SamplingFeatures invisible. This was not detectable from unit tests. F49 (validation blocking extraction) affected the same resource type for a different reason, also invisible from unit tests. Both were critical findings that changed our architecture.

**Action:**

- Every Phase 3 parser component should have its first smoke test within one review cycle of implementation
- Smoke test findings feed directly into parser design — they generate the "adversarial" fixture tests that unit tests alone can't predict
- The finding → issue → fix → verify pipeline (F40 → Issue #49 → fix → F40 confirmed) is the canonical workflow

---

## Lesson 8: Layered Architecture Enables Clean Extension

**What happened:** The GeoJSON handler uses a 5-layer architecture: constants → recognition → parsing → extraction → (removed: validation). When Issue #49 needed to add SensorML vocabulary support, the change fitted cleanly into the existing layers — new constant arrays, new lookup sets, extended recognition helpers, chain extension. Phase 3.1 code review F1 called it "textbook example of extending existing architecture."

**Root cause (positive):** The layered design was established in Issue #14 (GeoJSON Handler Extensions) and followed the pattern from `src/shared/mime-type.ts`. Each layer has a single responsibility and depends only on the layer below it.

**Why it matters:** When vocabulary support needed to change (SOSA-only → SOSA + SensorML), the change was surgical — it touched constants and lookup sets but didn't require restructuring recognition, parsing, or extraction logic. Compare this to a monolithic parser where vocabulary is hardcoded throughout.

**Action:**

- When building new parsers (SWE Common, SensorML), follow the layered pattern: constants → recognition → parsing → extraction
- Each layer should be independently testable
- New vocabulary or format support should require changes to constants/lookup layers, not structural changes to parsing/extraction layers
- If adding a new capability requires changes across _all_ layers, that's a signal the architecture may need a design discussion

---

## Lesson 9: Content Negotiation Cannot Be Assumed

**What happened:** 52North changed its default content type from `application/json` to `application/sml+json` between smoke tests #10 and #11 (F50). Additionally, OSH ignores `Accept: application/sml+json` entirely — it always returns `application/json` regardless of the request (F46).

**Why it matters:** The response parser cannot assume GeoJSON as the default format. It must:

1. Check the `Content-Type` response header
2. Handle multiple media types mapping to the same parser (e.g., `application/json`, `application/geo+json`, and `application/sml+json` may all require the GeoJSON handler)
3. Gracefully handle servers that ignore `Accept` headers

**Action:**

- Always dispatch parsing based on the response `Content-Type`, not the request `Accept` header
- Map multiple media types to the same parser where OGC conventions dictate
- The format detector functions (Issue #15) exist precisely for this purpose — use them as the dispatch mechanism
- Test with fixtures that simulate both content types (`application/json` and `application/sml+json` for the same underlying data)

---

## Lesson 10: Type Naming Must Avoid Built-In Collisions

**What happened:** OGC SWE Common 3.0 defines types named `Boolean`, `Text`, `Count`, `Time`, and `Geometry` — all of which collide with JavaScript/TypeScript built-ins or common library types. Issue #17 (SWE Common Types) resolved this by prefixing with `Swe`: `SweBoolean`, `SweText`, `SweCount`, `SweTime`, `SweGeometry`.

**Why it matters:** If a type is named `Boolean`, TypeScript will compile without error, but consumers will confuse the SWE Common `Boolean` (which has `value`, `quality`, `nilValues`, `constraint` properties) with the JavaScript primitive `boolean`. Auto-import will select the wrong one. IDE tooltips will mislead.

**Action:**

- When defining types from external specifications, check whether the type name conflicts with JavaScript/TypeScript built-ins: `Boolean`, `Number`, `String`, `Object`, `Array`, `Map`, `Set`, `Date`, `Error`, `Symbol`, `Function`
- Also check for collisions with common library types: `Geometry` (GeoJSON), `Feature`, `Point`, `Polygon`
- Use a domain prefix (`Swe`, `Sml`, etc.) for any type that would collide
- Document the naming rationale in the type's JSDoc: `/** SWE Common Boolean component. Named SweBoolean to avoid collision with JavaScript Boolean. */`

---

## Lesson 11: Document Architectural Decisions Formally

**What happened:** The validator removal decision (Issue #52) was documented in `design-notes-validation-extraction-decoupling.md` — a formal architectural decision record (ADR) that captured the problem, current design tension, full upstream audit, decision rationale, what stays/what goes, and design principles applied.

**Why it matters:** Without the design notes document, the "why did we remove validators?" question would require re-reading the full conversation history across multiple sessions. The ADR captures the reasoning once, definitively. It also prevented the STAC audit inaccuracy from propagating — the correction is documented in the same file.

**Action:**

- When a significant architectural decision is made (especially one that _reverses_ prior work), create a design notes document in `docs/implementation/`
- Name it `design-notes-{brief-description}.md`
- Include: problem statement, options considered, upstream audit, decision, rationale, impact
- Reference the design notes from the relevant GitHub issue comment

**When to create an ADR:**

- A feature is removed after being implemented
- An architectural pattern is changed (e.g., validation strategy)
- A design decision affects multiple future issues
- There's disagreement or ambiguity that gets resolved

**When NOT to create an ADR:**

- Routine implementation following an established pattern
- Bug fixes with obvious root cause
- Test additions

---

## Lesson 12: "Build It Right, But Should We Build It At All?"

**What happened:** The validator framework was technically excellent — well-structured, fully tested, architecturally clean. Phase 3.2 code review findings F4, F5, and F8 were all **POSITIVE**. But it was the wrong thing to build for this contribution context.

**Root cause:** The question "is this code good?" was asked and answered (yes). The question "should this code exist in this library?" was not asked until a smoke test forced it.

**Why it matters:** AI-assisted development excels at building things correctly. It does not inherently ask _whether_ the thing should be built. That question requires contribution context (upstream patterns, maintainer expectations, library philosophy) that isn't visible from the specification alone.

**Action:**

- Before starting implementation on any issue, ask: **"Does this introduce a new category of functionality that no upstream handler has?"**
- If yes, document the precedent gap in the issue discussion _before_ writing code
- The human collaborator's role is to approve new categories; the AI's role is to flag them
- This check is especially important for "nice to have" features that feel obviously beneficial (validators, schema checkers, input sanitizers) — these are the features most likely to have no upstream precedent

---

## Lesson 13: AI Drift Can Fabricate Findings That Survive Re-Verification

**What happened:** The Phase 3.4 smoke test reported that 52North's demo server had lost all its data (F57 — "52North server data has been completely removed"). The finding was classified as "Moderate," attributed to "Upstream" ownership, and characterized as "consistent with a database reset or redeployment." It was even "re-verified independently" on the same date, with all 6 resource collection endpoints confirmed empty. Five prior findings (F41, F42, F43, F44, F47) were marked as "cannot verify" and the smoke test series was declared to have dropped to "single-server validation."

**None of this was true.** The data was always there.

**Root cause:** Between the Phase 3.3 and Phase 3.4 smoke tests, the AI changed its HTTP request pattern. Phase 3.3 used no explicit `Accept` header, causing 52North to return its default `application/sml+json` — the content type that routes to the actual SensorML data store (3 systems, 1 deployment, 1 procedure). Phase 3.4 added `Accept: application/json` to its requests, which routes to 52North's separate, empty pygeoapi GeoJSON provider. The AI did not recognize the content-negotiation implications of this change. The "independent re-verification" repeated the same incorrect header and reached the same wrong conclusion — confirming a non-existent problem instead of challenging the original assumption.

**Detection:** The human collaborator noticed that 52North's HTML viewer still showed deployment data. When asked to investigate, the AI initially dismissed this as browser caching. The human pushed back, noting the data survived a hard refresh (Ctrl+Shift+R). Closer investigation of the HTML source revealed a `<cs-viewer>` web component that fetches data client-side. Testing with `Accept: application/sml+json` returned all the data immediately.

**52North's actual behavior:**

| Accept Header          | Content-Type Returned  | Response Shape                                | Data?                                    |
| ---------------------- | ---------------------- | --------------------------------------------- | ---------------------------------------- |
| _(none)_               | `application/sml+json` | `{ items: [...] }`                            | **3 systems, 1 deployment, 1 procedure** |
| `application/json`     | `application/json`     | `{ type: "FeatureCollection", features: [] }` | **Empty**                                |
| `application/sml+json` | `application/sml+json` | `{ items: [...] }`                            | **3 systems, 1 deployment, 1 procedure** |

**Why it matters:** This is the most dangerous type of AI error — a confident, well-documented, internally-consistent finding that is factually wrong. F57 had:

- Evidence bullets
- An "independent re-verification"
- Impact analysis with specific dependent findings cited
- A plausible narrative ("database reset or redeployment")
- Upstream ownership attribution (blaming the server, not ourselves)

All of these made the finding _look_ thoroughly investigated. But none of them challenged the core assumption: "Did we change how we ask for data?" The AI treated its own prior output as evidence rather than questioning whether the observation method had changed.

**Why re-verification failed:** The "independent re-verification" was not independent. It was the same agent, in the same session, using the same request pattern, confirming its own conclusion. True independence requires varying the observation method (different headers, different tools, different content types) — not repeating the same request and expecting a different result.

**Specific L9 violation:** We already documented L9 ("Content Negotiation Cannot Be Assumed") as a lesson learned. The F57 error demonstrates that _knowing_ a lesson and _applying_ it are different. The AI wrote L9, cited it in code reviews, and then violated it in the exact scenario L9 was meant to prevent.

**Action:**

- When a smoke test shows a previously-working server returning no data, **vary the request method before concluding data loss.** Test with: no Accept header, `application/json`, `application/sml+json`, `application/geo+json`, and the `?f=` query parameter form.
- **Never attribute a failure to "upstream" without first ruling out our own changes.** Diff the request patterns between the last-successful and first-failed smoke tests.
- Treat "independent re-verification" as meaningful only if it uses a _different observation method_, not the same request repeated twice.
- When a human collaborator reports evidence that contradicts a finding, treat that as a priority investigation — not a caching artifact.

---

## Quick Reference: Phase 2 Lessons Still Active

These Phase 2 lessons remain fully applicable during Phase 3:

| Phase 2 Lesson                       | Phase 3 Applicability                                                                             |
| ------------------------------------ | ------------------------------------------------------------------------------------------------- |
| Lesson 5: All work in existing files | Modified — Phase 3 _creates_ new files per ROADMAP, but don't create files beyond the issue scope |
| Lesson 6: Findings become work items | Still mandatory — code review findings → tracked issues                                           |
| Lesson 7: DRY violations compound    | Still mandatory — especially across parser components                                             |
| Lesson 8: Multi-server testing       | Still mandatory — dual-server smoke tests are _more_ valuable in Phase 3                          |
| Lesson 9: "Works by luck"            | Still mandatory — parsers that succeed on one server's data shape may fail on another's           |
| Lesson 10: Smoke tests read-only     | Still mandatory — observe, report, discuss, scope, implement                                      |

Phase 2 Lessons 1–4 (test checklist, query options table, temporal keys, `assertResourceAvailable` strings) are Phase 2-specific and do not apply to Phase 3 parser code. The Phase 3 test checklists (Categories A–D in the code review template) replace them.
