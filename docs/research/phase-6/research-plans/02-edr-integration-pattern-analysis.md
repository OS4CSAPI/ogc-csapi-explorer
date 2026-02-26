# Research Plan 02: EDR Integration Pattern Analysis

> **Plan 2 of 8** | **Phase 6 — Upstream Acceptance Refactoring**

---

## Metadata

| Field                  | Value                                                     |
| ---------------------- | --------------------------------------------------------- |
| **Status**             | Not Started                                               |
| **Plan Type**          | Internal analysis                                         |
| **Date Created**       | 2026-02-23                                                |
| **Last Updated**       | 2026-02-23                                                |
| **Estimated Time**     | 1–2 hours                                                 |
| **Actual Time**        | —                                                         |
| **Depends On**         | None                                                      |
| **Blocks**             | Plan 06 (Endpoint Decoupling Architecture)                |
| **Strategy Reference** | [research-strategy.md § Plan 02](../research-strategy.md) |

---

## 1. Research Objective

Produce a precise, side-by-side comparison of how EDR and CSAPI integrate with `endpoint.ts`, `info.ts`, `model.ts`, and `index.ts` — documenting every import, method, property, type reference, and test case — to determine exactly why the EDR integration pattern is acceptable for EDR but unacceptable for CSAPI. The output is a structured analysis that identifies the specific points of failure in the CSAPI integration, quantifies the scale difference, and extracts the architectural principles that Plan 06 must satisfy. This plan answers the question: **what does EDR get right that CSAPI gets wrong, and what boundary separates "small enough to embed" from "must be its own entry point"?**

---

## 2. Sequencing Rationale

### Why Plan 2?

EDR (PR #114) is the direct precedent we followed when integrating CSAPI into `endpoint.ts`. jahow himself pointed to PR #114 as a reference in issue #118 and later rejected the CSAPI integration in PR #136 — meaning the EDR pattern doesn't scale to CSAPI's size. Understanding exactly where and why it fails is prerequisite to designing the decoupled architecture (Plan 06). Without this analysis, we'd be designing the new architecture without understanding what the old one does wrong.

This plan has no dependencies and can run in parallel with Plans 01, 04, 05, and 07. However, its findings are critical input to Plan 06, which synthesizes all prior research into the final decoupling design.

### Dependency Chain

- **Builds on:** Nothing — this is an independent analysis of existing code. However, familiarity with the codebase structure is assumed.
- **Feeds into:**
  - **Plan 06** (Endpoint Decoupling Architecture): Needs the specific integration touchpoints identified here to know exactly what to change. Needs the scale analysis to justify the architectural boundary. Needs the "EDR principles" to know what patterns are acceptable at small scale.
  - **Plan 08** (File-Level Changelist and Commit Strategy): Needs the inventory of CSAPI touchpoints in `endpoint.ts`, `info.ts`, `model.ts`, and `index.ts` to build the change list.

---

## 3. Boundary Conditions

### Non-Negotiable Constraints

1. **No CSAPI in root exports (Constraint 1):** The root `index.ts` currently exports ~170 lines of CSAPI types and values. EDR exports zero lines from `index.ts`. This asymmetry is a primary finding to document.
2. **No outward imports (Constraint 3):** `endpoint.ts` currently imports `CSAPIQueryBuilder` and `scanCsapiLinks` from the CSAPI module. This violates constraint 3 — nothing outside `src/ogc-api/csapi/` should import from CSAPI. The EDR equivalent (`import EDRQueryBuilder`) technically violates the same rule but was accepted because EDR is small. Documenting this threshold is key.
3. **One-way dependency (Constraint 4):** The CSAPI module must depend on core, never the reverse. Currently, `endpoint.ts` (core) imports from `csapi/` (reverse dependency). Understanding how EDR handles this same pattern and why it was tolerated matters for the design.

### Excluded From Scope

- **Designing the replacement architecture:** This plan documents the current state and analyzes why it's problematic. The actual decoupled design is Plan 06's territory.
- **Build system mechanics:** How entry points work at the `package.json`/bundler level is Plan 01. This plan focuses on source-level integration patterns.
- **External industry patterns:** How other libraries solve sub-module composition is Plans 04 and 05. This plan is strictly internal analysis.
- **Formatting and linting:** Plan 07. Not relevant to the structural integration analysis.
- **Proposing a solution for `hasConnectedSystems` or `csapiCollections` placement:** The analysis will document these touchpoints and flag the open questions, but choosing where they should live is Plan 06's decision.

### What Remains Open

- Whether `hasConnectedSystems` can stay on `endpoint.ts` without violating constraint 3 (it currently uses `checkHasConnectedSystems` from `info.ts`, which does NOT import from the CSAPI module — so it might be safe)
- Whether `csapiCollections` can stay on `endpoint.ts` under the same reasoning (it uses `parseCollections` from `info.ts` and checks `hasConnectedSystems` from the link `rel` pattern — also no CSAPI module import)
- Whether EDR's current pattern would also need to change in the future, or if its size genuinely makes it a non-issue
- What the exact "size threshold" is that makes a module too large for the EDR pattern (is it lines of code? Number of exports? Number of imports into endpoint.ts? Surface area of public API?)
- Whether EDR types being in the shared `model.ts` (vs CSAPI types being in their own `csapi/model.ts`) is a meaningful architectural difference or incidental

---

## 4. Research Questions

### Core Questions

1. How does EDR integrate with `endpoint.ts`, `info.ts`, `model.ts`, and `index.ts`, and what is the complete inventory of touchpoints?
2. How does CSAPI integrate with the same files, and how do its touchpoints differ from EDR's?
3. What quantitative and qualitative differences between EDR and CSAPI explain why the EDR pattern is acceptable for EDR but not for CSAPI?
4. Which CSAPI touchpoints in `endpoint.ts` and `info.ts` actually import from the CSAPI module, and which only reference core types?
5. What architectural principles can be extracted from the EDR integration that define the boundary between "embed in endpoint" and "separate entry point"?

### Detailed Questions

#### EDR Integration Inventory (8 questions)

1. What imports does `endpoint.ts` have from `src/ogc-api/edr/`? List every import statement with file path.
2. What properties and methods does `OgcApiEndpoint` expose for EDR? (`edrCollections`, `hasEnvironmentalDataRetrieval`, `edr()`, `collection_id_to_edr_builder_`)
3. How does the `edr()` method work internally? What data does it extract from the endpoint to construct `EDRQueryBuilder`?
4. What imports does `info.ts` have from `src/ogc-api/edr/`? (Expected: none — `checkHasEnvironmentalDataRetrieval` checks conformance URIs only)
5. How does `parseCollections()` in `info.ts` detect EDR collections? Does it import from the EDR module, or use core/shared types only?
6. What does `index.ts` export from the EDR module? (Expected: nothing — EDR is not exposed in the package's public API)
7. Where do EDR types (`DataQueryType`, `EdrParameterInfo`) live? Are they in `ogc-api/model.ts` (shared) or in `edr/model.ts` (EDR-specific)?
8. How many tests exist in `endpoint.spec.ts` for EDR functionality, and what do they test?

#### CSAPI Integration Inventory (8 questions)

9. What imports does `endpoint.ts` have from `src/ogc-api/csapi/`? List every import statement with file path.
10. What properties and methods does `OgcApiEndpoint` expose for CSAPI? (`csapiCollections`, `hasConnectedSystems`, `csapi()`, `collection_id_to_csapi_builder_`, `extractRootResourceUrls()`)
11. How does the `csapi()` method work internally? What data does it extract — and how does it differ from `edr()`? (Note: `csapi()` uses `getCollectionDocument` for raw links, not `getCollectionInfo`; it also calls `extractRootResourceUrls()`)
12. What imports does `info.ts` have from `src/ogc-api/csapi/`? (Expected: none — `checkHasConnectedSystems` checks conformance URIs only; `parseCollections` checks `link.rel` regex)
13. How does `parseCollections()` in `info.ts` detect CSAPI collections? Does it use `ogc-cs:*` link relations from core types, or does it import CSAPI-specific logic?
14. What does `index.ts` export from the CSAPI module? Categorize into: (a) value exports, (b) type exports, (c) function exports. Count the lines.
15. Where do CSAPI types live? How are they organized across `csapi/model.ts`, `csapi/formats/index.ts`, and `csapi/formats/` sub-modules?
16. How many tests exist in `endpoint.spec.ts` for CSAPI functionality, and what do they test?

#### Scale Comparison (7 questions)

17. What is the total source line count (non-spec) for EDR vs CSAPI? How many files in each module?
18. How many type exports does EDR contribute to the package's public API (via `model.ts` or `index.ts`) vs how many CSAPI contributes?
19. How many import statements does EDR add to `endpoint.ts` vs how many CSAPI adds?
20. How many new methods/properties does EDR add to `OgcApiEndpoint` vs how many CSAPI adds?
21. Does EDR add any private helper methods to `OgcApiEndpoint`? Does CSAPI? (`extractRootResourceUrls()` is CSAPI-only)
22. What is the constructor signature complexity of `EDRQueryBuilder` vs `CSAPIQueryBuilder`? (EDR takes `OgcApiCollectionInfo`; CSAPI takes `OgcApiCollectionInfo` + `Map<string, string>` for resource URLs)
23. How many sub-directories does each module have? (EDR: 0; CSAPI: `formats/`, `integration/`)

#### Info.ts and Model.ts Integration Analysis (6 questions)

24. Does `checkHasConnectedSystems()` in `info.ts` import anything from `src/ogc-api/csapi/`? Or does it purely check conformance URI strings?
25. Does `checkHasEnvironmentalDataRetrieval()` in `info.ts` import anything from `src/ogc-api/edr/`? Or does it purely check conformance URI strings?
26. Does `parseCollections()` in `info.ts` import anything from `src/ogc-api/csapi/` to detect CSAPI collections? Or does it use the `ogc-cs:*` regex against core link types?
27. Does `parseCollections()` in `info.ts` import anything from `src/ogc-api/edr/` to detect EDR collections? Or does it check `collection.data_queries` from `OgcApiCollectionInfo`?
28. Are there EDR-specific types in `ogc-api/model.ts` (`DataQueryType`, `EdrParameterInfo`, `data_queries` property on `OgcApiCollectionInfo`)? If so, how many lines do they occupy? Does the shared model absorb EDR concerns, and is that pattern acceptable?
29. Are there CSAPI-specific types in `ogc-api/model.ts`? Or are all CSAPI types in the CSAPI module's own files?

#### Architectural Boundary Analysis (6 questions)

30. What exactly makes the EDR integration acceptable to the maintainer? Is it (a) the code is small, (b) EDR doesn't pollute `index.ts`, (c) EDR types are in the shared model, (d) EDR is an OGC standard with upstream consensus, or (e) some combination?
31. At what point would EDR need the same treatment as CSAPI? If EDR grew to 5,000 lines with its own type system, format parsers, and sub-modules, would it too need a separate entry point?
32. Is the core issue "CSAPI is in `index.ts`" (public API pollution) or "CSAPI is in `endpoint.ts`" (implementation coupling) or both?
33. jahow said CSAPI should be a separate entry point. Did he say anything about the `endpoint.ts` integration (the `csapi()` method, `hasConnectedSystems`, `csapiCollections`)? Or is the constraint specifically about the root exports?
34. Can `hasConnectedSystems` and `csapiCollections` remain on `OgcApiEndpoint` if they don't import from `csapi/`? (They currently don't — they use `info.ts` functions that only check conformance URIs and link relations.) Is this the same pattern as `hasEnvironmentalDataRetrieval` and `edrCollections`?
35. Can the `csapi()` method stay on `OgcApiEndpoint` if the imports from `csapi/` are removed and the builder is constructed through a different mechanism? Or must the method itself move to the CSAPI module?

**Total: 35 detailed questions**

---

## 5. Sources

### Primary Sources (In Workspace)

| Source                 | Path                               | What to Extract                                                                                                                      |
| ---------------------- | ---------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| OGC API endpoint class | `src/ogc-api/endpoint.ts`          | All EDR and CSAPI imports, properties, methods, cache maps, private helpers                                                          |
| Info utilities         | `src/ogc-api/info.ts`              | `checkHasEnvironmentalDataRetrieval`, `checkHasConnectedSystems`, `parseCollections` — import lists and implementation details       |
| OGC API model types    | `src/ogc-api/model.ts`             | EDR-specific types (`DataQueryType`, `EdrParameterInfo`, `data_queries` on `OgcApiCollectionInfo`)                                   |
| Root barrel file       | `src/index.ts`                     | All EDR exports (expected: none) and all CSAPI exports (~170 lines)                                                                  |
| EDR module             | `src/ogc-api/edr/`                 | Full directory: `url_builder.ts` (562 lines), `model.ts` (126 lines), `helpers.ts` (17 lines)                                        |
| CSAPI module           | `src/ogc-api/csapi/`               | Directory structure and file inventory: `url_builder.ts`, `model.ts`, `helpers.ts`, `command-routing.ts`, `formats/`, `integration/` |
| Endpoint tests         | `src/ogc-api/endpoint.spec.ts`     | EDR test block (lines ~2543–2835) and CSAPI test block (lines ~2836–2886)                                                            |
| CSAPIQueryBuilder      | `src/ogc-api/csapi/url_builder.ts` | Constructor signature, what data it needs from the endpoint                                                                          |
| EDRQueryBuilder        | `src/ogc-api/edr/url_builder.ts`   | Constructor signature, what data it needs from the endpoint                                                                          |
| CSAPI helpers          | `src/ogc-api/csapi/helpers.ts`     | `scanCsapiLinks()` — what it does and why it's imported into `endpoint.ts`                                                           |

### External Sources

| Source          | URL/Reference                                       | What to Extract                                                        |
| --------------- | --------------------------------------------------- | ---------------------------------------------------------------------- |
| PR #114 (EDR)   | https://github.com/camptocamp/ogc-client/pull/114   | Review comments, merge decision, maintainer approval criteria          |
| PR #136 (CSAPI) | https://github.com/camptocamp/ogc-client/pull/136   | jahow's comments on why CSAPI needs a separate entry point             |
| Issue #118      | https://github.com/camptocamp/ogc-client/issues/118 | jahow's original guidance referencing PR #114 as the integration model |

### Prior Research Findings

| Finding | Path | What to Use                                                                                                                                                                                        |
| ------- | ---- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| None    | —    | This is Plan 2 — no prior findings from Phase 6. Earlier research in `docs/research/design/` and `docs/research/upstream/` documented the original integration approach but is not required input. |

---

## 6. Research Methodology

### Phase 1: EDR Integration Audit (~20 minutes)

**Objective:** Document every point where EDR code touches files outside `src/ogc-api/edr/`.

**Tasks:**

1. Read `endpoint.ts` imports — extract all EDR-related imports (expected: 1 import of `EDRQueryBuilder from './edr/url_builder.js'`)
2. Read `endpoint.ts` class body — document every EDR property, method, and cache map
3. Read `info.ts` — document `checkHasEnvironmentalDataRetrieval()` (conformance check only), confirm no EDR module imports
4. Read `info.ts` `parseCollections()` — document how it detects `hasDataQueries` (checks `collection.data_queries` property, no EDR import)
5. Read `model.ts` — document EDR-specific types: `DataQueryTypes`, `DataQueryType`, `EdrParameterInfo`, `data_queries` field on `OgcApiCollectionInfo`
6. Confirm `index.ts` has zero EDR exports — EDRQueryBuilder, EDR model types, and EDR helpers are NOT in the public API
7. Read `edr/url_builder.ts` constructor — document what data it needs from the endpoint (`OgcApiCollectionInfo` with `data_queries`)
8. Count EDR test cases in `endpoint.spec.ts` (lines ~2543–2835): number of `it()` blocks, what they test

**Output:** Complete EDR integration touchpoint inventory

### Phase 2: CSAPI Integration Audit (~25 minutes)

**Objective:** Document every point where CSAPI code touches files outside `src/ogc-api/csapi/`.

**Tasks:**

1. Read `endpoint.ts` imports — extract all CSAPI-related imports (expected: 2 imports — `CSAPIQueryBuilder from './csapi/url_builder.js'` and `{ scanCsapiLinks } from './csapi/helpers.js'`)
2. Read `endpoint.ts` class body — document every CSAPI property, method, cache map, and private helper (`extractRootResourceUrls()`)
3. Read `info.ts` — document `checkHasConnectedSystems()` (conformance check only), confirm no CSAPI module imports
4. Read `info.ts` `parseCollections()` — document how it detects `hasConnectedSystems` (checks `link.rel` via `/^ogc-cs:.+$/` regex, no CSAPI module import)
5. Confirm `model.ts` has zero CSAPI-specific types — all CSAPI types live in `csapi/model.ts` and `csapi/formats/`
6. Read `index.ts` — document every CSAPI export, organized by category: (a) value exports (CSAPIQueryBuilder, CSAPIResourceTypes, etc.), (b) type-only exports, (c) function exports (from `formats/index.js`)
7. Read `csapi/url_builder.ts` constructor — document what data it needs (`OgcApiCollectionInfo` + resource URLs map)
8. Read `csapi/helpers.ts` — document `scanCsapiLinks()` and why `endpoint.ts` needs it (to extract root-level resource URLs from the API document's links)
9. Count CSAPI test cases in `endpoint.spec.ts` (lines ~2836–2886): number of `it()` blocks, what they test

**Output:** Complete CSAPI integration touchpoint inventory

### Phase 3: Scale and Structural Comparison (~20 minutes)

**Objective:** Quantify the differences that explain why one pattern is acceptable and the other is not.

**Tasks:**

1. Create side-by-side comparison table:
   - Source lines (non-spec): EDR 656 vs CSAPI 11,767
   - Source files (non-spec): EDR 3 vs CSAPI ~27
   - Sub-directories: EDR 0 vs CSAPI 2 (`formats/`, `integration/`)
   - Imports into `endpoint.ts`: EDR 1 vs CSAPI 2
   - New methods on `OgcApiEndpoint`: EDR 3 vs CSAPI 4+ (including private helper)
   - Root exports (`index.ts`): EDR 0 lines vs CSAPI ~170 lines
   - Types in shared model (`model.ts`): EDR ~35 lines vs CSAPI 0 lines
   - Constructor complexity: EDR 1 param vs CSAPI 2 params
   - Test lines in endpoint.spec.ts: EDR ~290 lines vs CSAPI ~50 lines
2. Calculate ratios: CSAPI is ~18x larger by source lines, ∞x more exported types, 2x more imports into endpoint.ts
3. Analyze where EDR types live (shared `model.ts`) vs where CSAPI types live (own module) — is this an incidental difference or deliberate architectural choice?
4. Analyze the `edr()` vs `csapi()` method complexity — `csapi()` needs `getCollectionDocument` (raw doc with links) plus `extractRootResourceUrls()`, while `edr()` only needs `getCollectionInfo`
5. Document the "complexity cliff" — EDR is a thin wrapper around a URL builder; CSAPI is a full sub-system with format parsers, SensorML, SWE Common, command routing, etc.

**Output:** Quantified comparison table with analysis of why the scale difference matters

### Phase 4: External Context from PRs and Issues (~15 minutes)

**Objective:** Extract jahow's exact words about why CSAPI needs different treatment, and understand the EDR approval context.

**Tasks:**

1. Review PR #114 (EDR) review comments — what did jahow say (approve/request changes)? What was the merge rationale?
2. Review PR #136 (CSAPI) review comments — extract jahow's exact phrasing about separate entry point, import direction, and module boundary
3. Review issue #118 — extract jahow's original guidance about using PR #114 as a model
4. Identify any explicit or implicit "scale threshold" in jahow's feedback — does he mention code size, number of exports, or module complexity?
5. Determine whether jahow's objection is to (a) CSAPI in `index.ts`, (b) CSAPI in `endpoint.ts`, (c) both, or (d) something else entirely

**Output:** Curated quotes from jahow with analysis of what specifically triggered the separate-entry-point requirement

### Phase 5: Boundary Line Analysis (~15 minutes)

**Objective:** Extract the architectural principles that define when a module needs its own entry point vs. when it can embed in the endpoint pattern.

**Tasks:**

1. Synthesize EDR's "passing pattern" — what characteristics make it acceptable?
   - Small size (~650 lines)
   - Zero public API exports (not in `index.ts`)
   - Types absorbed into shared model
   - Single import into endpoint.ts
   - No sub-modules or sub-directories
   - No format parsers or encoding logic
2. Define CSAPI's "failing pattern" — what characteristics make it unacceptable?
   - Large size (~11,700 lines, 18x EDR)
   - Massive public API surface (~170 lines of exports in `index.ts`)
   - Own type system in own module files
   - Multiple imports into endpoint.ts
   - Sub-modules with deep hierarchies
   - Complex format parsers (SensorML, SWE Common, GeoJSON)
3. Derive the boundary criteria (at least 3 distinct dimensions): public API footprint, implementation size, module self-containment
4. Analyze the open question: can `hasConnectedSystems` and `csapiCollections` stay on `OgcApiEndpoint`? (They follow the exact same pattern as `hasEnvironmentalDataRetrieval` and `edrCollections` — using `info.ts` functions that don't import from the module. The key question is whether jahow objects to these properties existing on the endpoint at all, or only to the `csapi()` method and the root exports.)
5. Formulate specific recommendations for Plan 06 based on the boundary analysis

**Output:** Boundary criteria definition and specific open questions for Plan 06

### Phase 6: Synthesis and Documentation (~15 minutes)

**Objective:** Consolidate all phase outputs into the deliverable document.

**Tasks:**

1. Synthesize findings from Phases 1–5
2. Verify all 35 research questions are answered
3. Validate findings against boundary conditions (Constraints 1, 3, 4)
4. Write deliverable document in findings report format
5. Flag specific inputs for Plan 06 and Plan 08

**Output:** Completed findings report at `docs/research/phase-6/findings/02-edr-integration-pattern-analysis.md`

---

## 7. Success Criteria

This research is complete when:

- [ ] All 35 detailed research questions have specific, evidenced answers
- [ ] Findings respect all boundary conditions listed in Section 3
- [ ] Complete EDR integration touchpoint inventory is documented (every import, method, property, type, test)
- [ ] Complete CSAPI integration touchpoint inventory is documented (same coverage)
- [ ] Side-by-side quantitative comparison table is produced with at least 8 dimensions
- [ ] jahow's exact feedback is extracted and analyzed from PR #114, PR #136, and issue #118
- [ ] At least 3 distinct boundary criteria are defined that explain when embeddability fails
- [ ] The status of `hasConnectedSystems`, `csapiCollections`, and the `csapi()` method is analyzed — which ones import from `csapi/` and which don't
- [ ] The question "is the problem the root exports, the endpoint.ts imports, or both?" is definitively answered
- [ ] Specific inputs for Plan 06 are identified and documented
- [ ] Deliverable document is complete and follows the findings report template

---

## 8. Deliverable

**Title:** EDR vs CSAPI Integration Pattern Comparison: Why the Patterns Must Differ

**Location:** `docs/research/phase-6/findings/02-edr-integration-pattern-analysis.md`

**Required Sections:** (per findings report template)

1. Executive Summary — the core finding about why EDR embeds but CSAPI must separate
2. EDR Integration Inventory — complete touchpoint map across `endpoint.ts`, `info.ts`, `model.ts`, `index.ts`
3. CSAPI Integration Inventory — same touchpoint map for comparison
4. Scale and Structural Comparison — quantified side-by-side table with analysis
5. Maintainer Feedback Analysis — jahow's exact words and what they mean for our design constraints
6. Boundary Line Definition — the architectural principles extracted (when is "too big to embed"?)
7. Open Questions for Plan 06 — `hasConnectedSystems` placement, `csapiCollections` placement, `csapi()` method future
8. Key Takeaways — numbered list of critical findings
9. Impact on Implementation — what specifically Plan 06 and Plan 08 should consume from this analysis

---

## 9. Risks and Mitigation

| Risk                                                                                                                                | Impact                                                                                  | Mitigation                                                                                                                                                                 |
| ----------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| PR #114 review comments may be sparse or missing                                                                                    | Can't determine why jahow accepted EDR's integration pattern                            | Infer from the code structure itself — EDR's small size and zero root exports make the rationale self-evident even without explicit comments                               |
| jahow's PR #136 feedback may be ambiguous about what exactly must change                                                            | Can't distinguish between "remove from index.ts" and "remove from endpoint.ts entirely" | Document both interpretations and flag as an open question for Plan 06; may need to ask jahow for clarification before implementing                                        |
| The "boundary line" between embeddable and non-embeddable may not have a clean rule                                                 | Can't produce clean criteria for Plan 06                                                | Use multiple dimensions (size, API surface, module complexity) as a composite heuristic rather than a single threshold; document the continuum                             |
| `hasConnectedSystems` and `csapiCollections` may appear safe (no CSAPI imports) but jahow may still want them removed from endpoint | Incorrect assumption that conformance-only checks can stay                              | Document the technical finding (no CSAPI imports in info.ts) but flag that jahow's intent may go further than the technical constraint; recommend asking for clarification |
| Our earlier research docs may contain outdated integration analysis that contradicts current code                                   | Confusion between past designs and current state                                        | Use ONLY the current source code as the ground truth; reference prior research docs only for historical context, never as authoritative                                    |

---

## 10. Research Status Checklist

- [ ] Phase 1: EDR Integration Audit — Not Started
- [ ] Phase 2: CSAPI Integration Audit — Not Started
- [ ] Phase 3: Scale and Structural Comparison — Not Started
- [ ] Phase 4: External Context from PRs and Issues — Not Started
- [ ] Phase 5: Boundary Line Analysis — Not Started
- [ ] Phase 6: Synthesis and Documentation — Not Started
- [ ] Deliverable document created
- [ ] Cross-references updated in Plan 06 and Plan 08

**Start Date:** —
**Completion Date:** —
**Actual Time:** —
