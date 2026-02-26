# Issue #8 Findings Report — JSDoc Documentation for extractCSAPIFeature() Limitations

> **Date:** 2026-02-17
> **Issue:** [OS4CSAPI/ogc-csapi-explorer#8](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/8) — "Add JSDoc documentation for extractCSAPIFeature() limitations"
> **Repository under review:** `OS4CSAPI/ogc-client-CSAPI_2` (`src/ogc-api/csapi/formats/geojson.ts`)
> **Dependencies:** None — this is a standalone documentation change
> **Labels:** documentation

---

## Table of Contents

1. [AI Operational Constraints Acknowledgment](#1-ai-operational-constraints-acknowledgment)
2. [Executive Summary](#2-executive-summary)
3. [Issue Description](#3-issue-description)
4. [Source Code Review](#4-source-code-review)
5. [Reference Document Review](#5-reference-document-review)
6. [Risk Assessment](#6-risk-assessment)
7. [Analysis: Existing JSDoc vs. Proposed JSDoc](#7-analysis-existing-jsdoc-vs-proposed-jsdoc)
8. [Rename Proposal Assessment](#8-rename-proposal-assessment)
9. [Recommendation](#9-recommendation)
10. [Appendix A: Authority Precedence Analysis](#appendix-a-authority-precedence-analysis)
11. [Appendix B: Cross-Reference Matrix](#appendix-b-cross-reference-matrix)

---

## 1. AI Operational Constraints Acknowledgment

Per the [AI Operational Constraints](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/governance/AI_OPERATIONAL_CONSTRAINTS.md), this review follows the required authority precedence:

1. **OGC specifications** (23-001r1 Part 1, 23-002r1 Part 2) — primary authority
2. **AI Collaboration Agreement** — governing constraints
3. **Issue description** — task scope
4. **Existing code patterns** — implementation precedent
5. **Conversation context** — supplementary guidance

This report does not expand scope beyond what Issue #8 describes. No behavioral modifications are proposed. All recommendations target JSDoc comments only within `geojson.ts`.

---

## 2. Executive Summary

**Issue #8 is correct. The proposed JSDoc enhancements are warranted and carry zero risk to library integrity.**

Issue #8 proposes enhancing the JSDoc documentation on `extractCSAPIFeature()` (L307) and `getCSAPIResourceType()` (L176) to make their Part 1 / GeoJSON-only limitations more explicit. Both functions **already have JSDoc** that partially documents these constraints, but the existing documentation does not explicitly state the Part 1 limitation, the GeoJSON format requirement, or the SensorML incompatibility in terms that would prevent consumer confusion.

| Aspect                           | Assessment                                                                                                                  |
| -------------------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| **Change type**                  | Documentation-only — JSDoc comment modifications                                                                            |
| **Production behavior modified** | None — zero runtime impact                                                                                                  |
| **Existing tests affected**      | None — JSDoc changes cannot affect test outcomes                                                                            |
| **Risk to library integrity**    | **Zero**                                                                                                                    |
| **Estimated scope**              | ~30–40 lines of JSDoc replacement in `geojson.ts`                                                                           |
| **Dependencies**                 | None — can be implemented independently                                                                                     |
| **Rename proposal**              | **Rejected** — renaming `extractCSAPIFeature()` would be a breaking change (see [Section 8](#8-rename-proposal-assessment)) |

**Key finding:** The existing JSDoc already communicates the core constraints through its return type signature (`System | Deployment | Procedure | SamplingFeature`), its `@throws` annotation, and its module-level documentation stating "Supported resource types: System, Deployment, Procedure, SamplingFeature." Issue #8's enhancement makes these implicit constraints explicit — a meaningful improvement for consumer discoverability, but the current documentation is not _incorrect_, only _incomplete_.

---

## 3. Issue Description

### 3.1 Origin: Finding F-3

Issue #8 corresponds to **Finding F-3** from the [upstream findings document](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/upstream-findings.md), which identified three scenarios where `extractCSAPIFeature()` limitations cause consumer confusion:

| Scenario                       | What Happens                                      | Root Cause                                                                                                                    |
| ------------------------------ | ------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| **A. SensorML responses**      | Throws "unrecognized or missing featureType"      | 52North returns SML format when no `Accept: application/geo+json` header is sent; SML responses lack `properties.featureType` |
| **B. Part 2 resources**        | Throws "unrecognized or missing featureType"      | DataStreams, Observations, Control Streams, Commands are flat JSON objects, not GeoJSON Features                              |
| **C. Function name ambiguity** | Consumer expects it to handle all CSAPI resources | Name `extractCSAPIFeature` does not indicate Part-1-only scope                                                                |

### 3.2 What Issue #8 Proposes

1. **Replace the existing JSDoc on `extractCSAPIFeature()`** with a comprehensive version explicitly documenting:

   - Part 1 resource limitation
   - GeoJSON Feature format requirement
   - SensorML response incompatibility
   - `@example` blocks showing success and failure cases

2. **Replace the existing JSDoc on `getCSAPIResourceType()`** with a version that explicitly states it only resolves Part 1 types.

3. **Optional rename** (explicitly marked as optional in the issue): `extractCSAPIGeoJSONFeature()` or `extractCSAPIPart1Feature()`.

### 3.3 Affected File

- [`src/ogc-api/csapi/formats/geojson.ts`](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/src/ogc-api/csapi/formats/geojson.ts) — 387 lines, containing all target functions

---

## 4. Source Code Review

### 4.1 Module-level JSDoc (L1–L11)

The file header already states the supported resource types:

```typescript
/**
 * GeoJSON handler extensions for OGC API — Connected Systems (CSAPI).
 *
 * Provides featureType recognition and CSAPI property extraction
 * for GeoJSON Feature resources returned by CSAPI endpoints.
 *
 * Supported resource types: System, Deployment, Procedure, SamplingFeature.
 *
 * @see https://docs.ogc.org/is/23-001/23-001.html
 * @module
 */
```

**Assessment:** The module JSDoc correctly scopes the file to "GeoJSON Feature resources" and lists the 4 supported types. This establishes context but is not surfaced by IDE tooltips when a consumer hovers over a specific function.

### 4.2 `getCSAPIResourceType()` — Existing JSDoc (L165–L175)

```typescript
/**
 * Classifies a GeoJSON Feature into a CSAPI resource type by its `featureType`.
 *
 * Checks the SOSA vocabulary first, then the SensorML vocabulary.
 * Classification priority within SOSA: System > Deployment > Procedure > SamplingFeature.
 * This ordering ensures that featureType values shared between System and
 * Procedure schemas (per OGC spec) resolve as System.
 *
 * @param feature - A candidate GeoJSON Feature object.
 * @returns The resource type name, or `null` if unrecognized.
 */
```

**Assessment:** This JSDoc already:

- ✅ States "GeoJSON Feature" in both the description and `@param`
- ✅ Explains the SOSA/SensorML vocabulary precedence
- ✅ Documents the return behavior for unrecognized input (`null`)
- ✅ Return type `CSAPIResourceTypeName | null` limits to `'System' | 'Deployment' | 'Procedure' | 'SamplingFeature'`
- ❌ Does **not** explicitly state that Part 2 resource types are not recognized
- ❌ Does **not** warn about SensorML response format incompatibility

### 4.3 `extractCSAPIFeature()` — Existing JSDoc (L297–L309)

```typescript
/**
 * Extracts and converts a raw GeoJSON Feature into a typed CSAPI resource.
 *
 * Uses {@link getCSAPIResourceType} for recognition, then parses
 * `validTime` from server format to {@link TimeInterval} and returns the
 * appropriately typed resource. Follows Postel's Law — extraction succeeds
 * for any recognized feature, regardless of missing optional or required
 * spec fields.
 *
 * @param feature - A raw GeoJSON Feature from the server.
 * @returns The typed CSAPI resource.
 * @throws {Error} If the feature has an unrecognized or missing featureType.
 */
```

**Assessment:** This JSDoc already:

- ✅ States "GeoJSON Feature" explicitly in both description and `@param`
- ✅ References `getCSAPIResourceType` via `{@link}`
- ✅ Documents the Postel's Law approach
- ✅ Includes `@throws` annotation
- ✅ Return type `System | Deployment | Procedure | SamplingFeature` implicitly communicates Part-1-only
- ❌ Does **not** explicitly state "Part 1 only"
- ❌ Does **not** warn that Part 2 resources (DataStreams, etc.) will throw
- ❌ Does **not** mention SensorML format incompatibility
- ❌ Does **not** include `@example` blocks

### 4.4 Key observation: The existing code is already well-documented

The existing JSDoc is **not incorrect** — it accurately describes what the functions do. However, it communicates constraints _implicitly_ through type signatures and terminology ("GeoJSON Feature") rather than _explicitly_ through warnings and limitation callouts. Issue #8's proposed enhancement converts implicit documentation into explicit documentation, which improves discoverability for consumers who may not be familiar with the Part 1 / Part 2 distinction in the Connected Systems API.

---

## 5. Reference Document Review

All 12 linked reference documents from the ogc-csapi-explorer repository were reviewed. Key corroboration for Issue #8:

### 5.1 Upstream Findings

- **F-3** (Category 1: "Function Behavior & Naming", 3 scenarios) — the finding that directly maps to Issue #8
- Recommended approaches: (1) Default to `Accept: application/geo+json` header for Part 1 resources (preferred, separate concern), or (2) Document the limitation in JSDoc (minimum, which is what Issue #8 proposes)
- The upstream findings document classifies F-3 as a documentation gap, not a bug

### 5.2 Library Findings Gap Analysis

- Maps F-3 to Issue #8 with: **Severity: High** (consumer impact), **Implementation Risk: Low** (documentation-only), **Priority Rank: 4 (Medium)**
- The gap analysis explicitly notes: "The function name `extractCSAPIFeature` doesn't indicate this is Part-1-only"
- Actionability assessment: "Straightforward — JSDoc additions only"

### 5.3 Library Integration Report

- **Finding #9:** Confirms `extractCSAPIFeature()` only works for GeoJSON Features — 52North flat SML objects fail with "unrecognized or missing featureType"
- **Finding #10:** Documents union return type TypeScript friction (`System | Deployment | Procedure | SamplingFeature` requires narrowing before use); better JSDoc could help consumers with this
- Both findings were discovered during real integration and support the need for clearer documentation

### 5.4 E2E Cross-Server Report

- **Finding #6:** Confirms `extractCSAPIFeature` fails on SensorML response bodies from 52North
- Recommendation: Use `Accept: application/geo+json` as primary request Content-Type for Part 1 resources — a runtime mitigation that is separate from but complementary to Issue #8's documentation approach
- 62/69 cross-server tests passing; the function works correctly when given GeoJSON input

### 5.5 E2E Write Operations Report

- **Finding #5:** Explicitly titled "extractCSAPIFeature Only Works for Part 1 Resources" — severity Low, type "Documentation gap"
- **Priority 4 recommendation:** "Document Part 1 vs Part 2 Parser Limitations" — directly supports Issue #8
- Parser validation section confirms: Part 2 resources (DataStreams, Observations) fail with "no featureType property — not a GeoJSON Feature"

### 5.6 Contribution Goal Accuracy Assessment

- Validates library is "specification-scoped" — the Part 1 limitation is by design, not a bug
- Documents that the validation scope change (Postel's Law) was an intentional design decision
- Confirms the function correctly handles all Part 1 resource types

### 5.7 Conformance Bypass Architecture Notes

- Demo bypasses `OgcApiEndpoint` and uses library pieces directly (including `extractCSAPIFeature`)
- This direct usage is what exposed the documentation gap — consumers using the function in isolation need explicit JSDoc

### 5.8 CRUD Smoke Test Findings

- F-15, F-16, S-8 — not directly related to Issue #8
- Provides context on Content-Type negotiation challenges that are separate from documentation concerns

### 5.9 EndpointError Isolation Report

- Not directly related to Issue #8 (addresses transitive XML dependency)
- Confirms the import verification graph shows `formats/geojson.ts` has type-only imports — documentation changes cannot affect the import graph

### 5.10 Library Source Changes Audit

- Confirms only one commit (`e73cff8`) has modified library source during the demo lifecycle
- Issue #8's JSDoc changes would be the second source modification — but documentation-only, with zero behavioral impact
- Lists `extractCSAPIFeature` and `getCSAPIResourceType` among the source imports used by the demo

### 5.11 Schema Display Findings

- F-13 (JSDoc conflates `f` with `obsFormat`) and F-14 (no schema response parser) — separate concerns
- Establishes precedent that JSDoc accuracy matters for consumer experience — supports Issue #8's rationale

### 5.12 AI Operational Constraints

- Authority precedence: JSDoc should accurately reflect spec behavior — OGC spec is primary authority
- "Prefer minimal diffs" — JSDoc replacement qualifies as minimal
- "Do not refactor for style, clarity, or 'best practice' unless explicitly requested" — Issue #8 explicitly requests the JSDoc enhancement, so this is authorized
- No scope expansion: Issue #8 is documentation-only within a single file

---

## 6. Risk Assessment

### 6.1 What could go wrong?

| Risk                                                   | Likelihood     | Impact | Mitigation                                                                        |
| ------------------------------------------------------ | -------------- | ------ | --------------------------------------------------------------------------------- |
| JSDoc changes affect runtime behavior                  | **Impossible** | N/A    | JSDoc comments are stripped at compile time — they cannot affect execution        |
| JSDoc changes break existing tests                     | **Impossible** | N/A    | Test assertions match function behavior, not comments                             |
| New JSDoc is factually incorrect                       | **Very low**   | Low    | Proposed JSDoc is consistent with 12 reference documents and verified source code |
| JSDoc becomes outdated if functions are later extended | **Possible**   | Low    | Standard documentation maintenance concern — not specific to this change          |
| Consumers misread new warnings as deprecation          | **Very low**   | Low    | Proposed JSDoc uses "Important limitations" framing, not deprecation language     |

### 6.2 Risk classification

**This is a ZERO RISK change to library integrity.**

JSDoc documentation modifications are the absolute safest category of code change:

- They **do not** modify any runtime behavior
- They **do not** change the public API surface
- They **do not** affect TypeScript compilation
- They **do not** add or remove dependencies
- They **do not** change test outcomes
- They **are** stripped entirely from the compiled JavaScript output

### 6.3 Integrity assessment

The library's integrity is **completely unaffected** by this change. Enhancing JSDoc:

- Improves consumer experience for direct library users
- Reduces debugging time when consumers encounter the documented limitations
- Aligns documentation with the 12 reference documents' findings
- Adds `@example` blocks that serve as inline usage guidance

---

## 7. Analysis: Existing JSDoc vs. Proposed JSDoc

### 7.1 What the existing JSDoc already communicates

| Constraint                   | How Currently Communicated                                                              | Sufficient?                                                             |
| ---------------------------- | --------------------------------------------------------------------------------------- | ----------------------------------------------------------------------- |
| GeoJSON format required      | "raw GeoJSON Feature" (description), "A raw GeoJSON Feature from the server" (`@param`) | Partially — implies GeoJSON but doesn't warn about other formats        |
| Part 1 only                  | Return type `System \| Deployment \| Procedure \| SamplingFeature`                      | Partially — TypeScript-literate consumers can infer this; others cannot |
| Throws on unrecognized input | `@throws {Error} If the feature has an unrecognized or missing featureType`             | Yes — this is clearly stated                                            |
| SensorML incompatibility     | Not mentioned                                                                           | No                                                                      |
| Part 2 resources unsupported | Not mentioned                                                                           | No                                                                      |

### 7.2 What Issue #8's proposed JSDoc adds

| New Element                                       | Value to Consumers                                                  |
| ------------------------------------------------- | ------------------------------------------------------------------- |
| Explicit "Only supports Part 1 resources" warning | High — prevents confusion when Part 2 resources throw               |
| "Requires GeoJSON Feature format" callout         | High — prevents SensorML/XML submission attempts                    |
| "Throws on unrecognized input" expansion          | Medium — explains the "missing featureType" scenario in more detail |
| `@example` blocks with success/failure cases      | High — provides copy-pasteable patterns and anti-patterns           |
| `@see` reference to OGC 23-002r1 Part 1           | Low — useful for spec-aware consumers                               |

### 7.3 Assessment

The existing JSDoc is **accurate but not defensive**. The proposed JSDoc is **accurate and defensive**. For a function that processes external server data with known failure modes (documented across 6+ reference documents), defensive documentation is the appropriate standard.

The proposed JSDoc in Issue #8 is well-written, factually correct, and consistent with both the source code behavior and the OGC specifications. The `@example` blocks demonstrating failure cases are particularly valuable — they give consumers immediate context for what to expect.

---

## 8. Rename Proposal Assessment

Issue #8 includes an optional suggestion:

> "If a rename is acceptable in a future version, `extractCSAPIGeoJSONFeature()` or `extractCSAPIPart1Feature()` would make the limitation self-documenting."

### 8.1 Assessment: **Reject the rename**

| Concern                        | Analysis                                                                                                                                                                                                                         |
| ------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Breaking change**            | Renaming a public exported function is a breaking change for all consumers. Any code calling `extractCSAPIFeature()` would need to be updated.                                                                                   |
| **AI Operational Constraints** | "Do not refactor for style, clarity, or 'best practice' unless explicitly requested" — renaming for clarity is a style refactor. The issue marks it as "optional, non-breaking alternative" but it is in fact a breaking change. |
| **Scope expansion**            | Issue #8 is labeled `documentation` only. A rename would be a code change that modifies the public API surface.                                                                                                                  |
| **Minimal diffs**              | A rename would touch import statements across multiple files and potentially affect downstream consumers. JSDoc enhancement achieves the same clarity goal with zero code impact.                                                |
| **Existing precedent**         | The function lives in a file named `geojson.ts` within a `formats/` directory — the file path already communicates the GeoJSON context.                                                                                          |

### 8.2 Recommendation

The JSDoc enhancement alone (proposals #1 and #2 from Issue #8) achieves the documentation goal completely. The rename (proposal #3) is unnecessary and introduces breaking-change risk with no additional runtime benefit. **Do not rename.**

---

## 9. Recommendation

### Primary recommendation: **Proceed with Issue #8's JSDoc proposals #1 and #2. Reject proposal #3 (rename).**

#### 9.1 `extractCSAPIFeature()` — Replace existing JSDoc

Replace the current JSDoc at L297–L309 with the comprehensive version proposed in Issue #8. The proposed text is factually correct, well-structured, and consistent with all reference documents. Specific elements to include:

- **"Important limitations" section** — explicitly lists Part 1 limitation, GeoJSON requirement, and throw behavior
- **`@param` enhancement** — specifies expected object shape (`{ type: "Feature", properties: { featureType, uid, name, ... }, geometry, links }`)
- **`@returns` enhancement** — explicitly states "Part 1 resource" and lists the 4 types
- **`@throws` expansion** — clarifies that Part 2 resources and SensorML responses trigger this
- **`@example` blocks** — shows success case (GeoJSON Feature) and failure cases (Part 2, SensorML)
- **`@see` references** — links to `getCSAPIResourceType` and OGC 23-002r1 Part 1

#### 9.2 `getCSAPIResourceType()` — Enhance existing JSDoc

Enhance the current JSDoc at L165–L175 with:

- Explicit statement that only Part 1 resource types are recognized
- `@see` reference to SOSA/SSN Ontology
- Preserve the existing SOSA/SensorML precedence documentation (it is accurate and useful)

#### 9.3 What NOT to do

- **Do not** rename `extractCSAPIFeature()` or `getCSAPIResourceType()` — this would be a breaking change
- **Do not** modify any function logic — Issue #8 is documentation-only
- **Do not** change the return types or parameter types
- **Do not** add runtime validation logic (e.g., format detection) — that would be scope expansion
- **Do not** modify the module-level JSDoc at L1–L11 — it is already correct

#### 9.4 Verification after implementation

1. Run `npx jest geojson` — confirm no test changes needed (JSDoc cannot affect tests)
2. Verify the full test suite: `npx jest url_builder.spec.ts` — confirm 298 tests still pass
3. Build the library: `npm run build` — confirm JSDoc is stripped from output and produces no compilation errors
4. Optionally inspect IDE tooltip: hover over `extractCSAPIFeature` in any consuming file to verify the enhanced JSDoc renders correctly

---

## Appendix A: Authority Precedence Analysis

| Authority Level | Source                     | Says About This Documentation                                                                                                                | Weight      |
| --------------- | -------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- | ----------- |
| 1 (Highest)     | OGC 23-001r1 Part 1        | Defines Part 1 resources as GeoJSON Features (Systems, Deployments, Procedures, SamplingFeatures) — supports the limitation being documented | Definitive  |
| 2               | OGC 23-002r1 Part 2        | Defines Part 2 resources as non-GeoJSON (DataStreams, Observations, etc.) — confirms why `extractCSAPIFeature` does not support them         | Definitive  |
| 3               | AI Collaboration Agreement | Documentation changes strengthen contribution quality                                                                                        | Supportive  |
| 4               | AI Operational Constraints | "Prefer minimal diffs" — JSDoc replacement is minimal; "Do not refactor unless requested" — Issue #8 explicitly requests this                | Authorizing |
| 5               | Issue #8                   | Proposes specific JSDoc text that is factually correct                                                                                       | Scoping     |
| 6               | Existing source code       | Functions already work correctly; only documentation needs enhancement                                                                       | Precedent   |
| 7               | 12 reference documents     | 6+ documents independently confirm the Part 1 / GeoJSON limitation                                                                           | Evidence    |

---

## Appendix B: Cross-Reference Matrix

| Document                                                                                                                                                       | Location           | Relevance to Issue #8                                                                 |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------ | ------------------------------------------------------------------------------------- |
| [upstream-findings.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/upstream-findings.md)                                                     | ogc-csapi-explorer | F-3 — the finding that Issue #8 addresses; 3 failure scenarios documented             |
| [library-findings-gap-analysis.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/library-findings-gap-analysis.md)                 | ogc-csapi-explorer | Maps F-3 → Issue #8; Severity High, Risk Low, Priority 4 (Medium)                     |
| [library-integration-report.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/library-integration-report.md)                       | ogc-csapi-explorer | Finding #9: extractCSAPIFeature GeoJSON-only; Finding #10: union return type friction |
| [e2e-cross-server-report.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/e2e-cross-server-report.md)                             | ogc-csapi-explorer | Finding #6: extractCSAPIFeature fails on SensorML; recommends geo+json Accept header  |
| [e2e-write-operations-report.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/e2e-write-operations-report.md)                     | ogc-csapi-explorer | Finding #5: Part 1 only; Priority 4: document parser limitations                      |
| [contribution-goal-accuracy-assessment.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/contribution-goal-accuracy-assessment.md) | ogc-csapi-explorer | Validates "specification-scoped" design; Part 1 limitation is intentional             |
| [conformance-bypass-architecture-notes.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/conformance-bypass-architecture-notes.md) | ogc-csapi-explorer | Direct function usage exposed the documentation gap                                   |
| [crud-smoke-test-findings.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/crud-smoke-test-findings.md)                           | ogc-csapi-explorer | S-8 Content-Type context; not directly related to Issue #8                            |
| [endpoint-error-isolation-report.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/endpoint-error-isolation-report.md)             | ogc-csapi-explorer | Import graph confirms geojson.ts has type-only imports; documentation changes safe    |
| [library-source-changes-audit.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/library-source-changes-audit.md)                   | ogc-csapi-explorer | Lists extractCSAPIFeature among source imports; confirms clean source state           |
| [schema-display-findings.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/schema-display-findings.md)                             | ogc-csapi-explorer | F-13 JSDoc accuracy precedent; separate concern from Issue #8                         |
| [AI_OPERATIONAL_CONSTRAINTS.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/governance/AI_OPERATIONAL_CONSTRAINTS.md)                        | ogc-client-CSAPI_2 | Authority precedence, no scope expansion, minimal diffs, explicitly requested change  |

---

## Conclusion

Issue #8 proposes a well-scoped, factually correct JSDoc enhancement for two functions in `geojson.ts`. The changes are:

1. **Correct** — the proposed JSDoc accurately describes limitations confirmed across 6+ independent reference documents and verified in the source code
2. **Consistent** — follows established JSDoc patterns in the codebase (module-level doc, `@param`, `@returns`, `@throws`, `@see`)
3. **Non-impacting** — JSDoc comments are stripped at compile time; zero runtime, test, or API surface changes
4. **Zero-risk** — documentation changes cannot degrade library integrity under any circumstances
5. **Explicitly authorized** — Issue #8 is labeled `documentation`, the change is requested (not speculative), and it aligns with AI Operational Constraints

**One rejection:** The optional rename proposal (`extractCSAPIGeoJSONFeature()` / `extractCSAPIPart1Feature()`) should not be implemented. It would constitute a breaking change to the public API, violating the minimal-diff and no-refactoring constraints. The JSDoc enhancement alone achieves the documentation goal completely.

The recommended approach is: replace the existing JSDoc on `extractCSAPIFeature()` and enhance the JSDoc on `getCSAPIResourceType()` as proposed in Issue #8, then verify with `npx jest geojson` and `npm run build`.
