# Phase 2C: Standards & Quality Category Deep Dive

**Review Date:** February 2026  
**Reviewer:** AI Review Agent  
**Phase:** 2C of multi-phase research document review  
**Category:** Standards & Quality (6 documents)  
**Anti-Pattern Catalog:** [Phase 0: Lessons from Failed Attempt](phase-0-lessons-from-failed-attempt.md)

---

## 1. Phase Overview

### 1.1 Documents Reviewed

| #   | Document                                                                                            | Lines | Status      | Verdict               |
| --- | --------------------------------------------------------------------------------------------------- | ----- | ----------- | --------------------- |
| 03  | [typescript-testing-standards.md](../findings/03-typescript-testing-standards.md)                   | 1,834 | ✅ Reviewed | ⚠️ Issues Found       |
| 17  | [coverage-targets-and-metrics.md](../findings/17-coverage-targets-and-metrics.md)                   | 873   | ✅ Reviewed | ❌ Significant Issues |
| 20  | [test-to-code-ratio-validation.md](../findings/20-test-to-code-ratio-validation.md)                 | 949   | ✅ Reviewed | ⚠️ Issues Found       |
| 35  | [jsdoc-testing-documentation-standards.md](../findings/35-jsdoc-testing-documentation-standards.md) | 1,850 | ✅ Reviewed | ❌ Significant Issues |
| 36  | [test-quality-checklist-review-process.md](../findings/36-test-quality-checklist-review-process.md) | 1,966 | ✅ Reviewed | ❌ Critical Issues    |
| 37  | [test-maintenance-evolution-strategy.md](../findings/37-test-maintenance-evolution-strategy.md)     | 1,837 | ✅ Reviewed | ❌ Significant Issues |

**Total Lines Reviewed:** 9,309

### 1.2 Review Focus

These 6 documents define the quality standards, metrics, documentation, review processes, and maintenance strategy for CSAPI testing. The review evaluates:

1. **Client vs. Server Orientation** — Do standards test client code behavior or server spec-compliance?
2. **Anti-Pattern Cross-Reference** — Do standards avoid the 5 anti-patterns identified in Phase 0?
3. **Upstream Alignment** — Do standards match actual upstream practices in `camptocamp/ogc-client`?
4. **Proportionality** — Are processes proportionate to the OSS contribution context?
5. **Internal Consistency** — Do the 6 documents agree with each other and with previously reviewed documents?
6. **Hallucination Detection** — Are claims grounded in the actual codebase?

---

## 2. Review Methodology

### 2.1 Anti-Pattern Cross-Reference

Each document was checked against all 5 Phase 0 anti-patterns:

| ID  | Anti-Pattern                 | Description                                                   |
| --- | ---------------------------- | ------------------------------------------------------------- |
| AP1 | Testing Response Content     | Tests validate server responses rather than client code       |
| AP2 | Hybrid Fixture/Live          | Tests designed to run against live servers OR fixtures        |
| AP3 | OGC Requirement Traceability | Test structure mirrors spec requirements, not client code     |
| AP4 | Asserting Data Shape         | Tests check response structure without testing transformation |
| AP5 | Graceful Skipping            | Tests skip based on fixture content rather than failing       |

### 2.2 Upstream Baseline (Verified)

Before reviewing, the following upstream facts were independently verified:

| Fact                | Verified Value                                                             | Source                                                    |
| ------------------- | -------------------------------------------------------------------------- | --------------------------------------------------------- |
| Jest import style   | Global (no `@jest/globals` imports)                                        | All 31 `.spec.ts` files                                   |
| `@types/jest`       | Installed (`^29.5.11`)                                                     | `package.json`                                            |
| Coverage thresholds | **None configured**                                                        | `jest.config.cjs` — no `coverageThreshold`                |
| Coverage scripts    | **None**                                                                   | `package.json` — only `test`, `test:browser`, `test:node` |
| JSDoc in test files | Near zero (0 `@fileoverview`, 0 `@module`, ~1 JSDoc block in ~9,000 lines) | All `.spec.ts` files                                      |
| Test-to-code ratios | WFS≈1.86, WMS≈1.21, WMTS≈2.47, TMS≈1.04, STAC≈0.66, OGC-API≈1.47           | Line counts                                               |
| Average ratio       | ~1.45:1                                                                    | Computed                                                  |
| Review process      | Standard GitHub PR review by maintainer(s)                                 | Upstream contribution model                               |

### 2.3 Cross-Document Consistency Check

This category's estimates were validated against previously reviewed documents:

| Metric                   | Doc 19 (authoritative) | Doc 20      | Doc 17            | Consistent?            |
| ------------------------ | ---------------------- | ----------- | ----------------- | ---------------------- |
| Test file count          | 22 files               | —           | —                 | ✅                     |
| Test lines               | 4,040–5,340            | 4,150–5,850 | **13,090–17,016** | ❌ Doc 17 is 3× higher |
| CSAPI test-to-code ratio | —                      | 0.86–0.90:1 | —                 | ✅ Reasonable          |

---

## 3. Overall Assessment: ⚠️ CONDITIONAL GO

**The standards & quality documents are a mixed bag.** Doc 03 (TypeScript standards) and Doc 20 (test-to-code ratio) are fundamentally sound with minor issues. However, Docs 35, 36, and 37 collectively propose an enterprise-grade quality bureaucracy — spec-traceability JSDoc tags, 41-item review checklists, 3-stage sign-off processes, monthly health checks, and custom traceability tools — that is wildly disproportionate to contributing to an existing open-source library. Doc 17 has a critical test line count inconsistency.

**The systemic AP3 problem is the most concerning finding.** Documents 35, 36, and 37 form an interconnected spec-traceability system built on `@specification` JSDoc tags that map tests to OGC spec sections. This is exactly the AP3 anti-pattern (OGC Requirement Traceability) that was the structural failure of the previous attempt. These documents should be treated as reference material only, not as processes to implement.

**Confidence level:** MEDIUM — The underlying technical standards (Doc 03) are solid, but the process documents (Docs 35, 36, 37) would actively harm the project if implemented as written.

---

## 4. Critical Issues

### C1: Doc 36 — "Spec Compliance Over Implementation" Philosophy

**Severity:** CRITICAL  
**Document:** [36-test-quality-checklist-review-process.md](../findings/36-test-quality-checklist-review-process.md)  
**Status:** ✅ Resolved

**Problem:** Document 36 explicitly states as a quality philosophy:

> **Spec Compliance Over Implementation:**
>
> - ❌ Test implementation details (private methods, internals)
> - ✅ Test spec requirements (public API, conformance classes)

This directly prescribes AP3 (OGC Requirement Traceability). Testing "spec requirements" and "conformance classes" is testing whether a _server_ is spec-compliant, not testing whether _our client code_ correctly builds URLs, parses responses, and handles errors. The senior developer's feedback was precisely that tests were "too geared towards evaluating a server and not a client."

The document further reinforces this with checklist item M-6: "Tests validate against spec requirements explicitly."

**Fix Required:** Replace "Spec Compliance Over Implementation" with "Client Behavior Over Spec Compliance." The quality philosophy should be: test that our code produces correct URLs, parses responses correctly, and handles errors — not that our code validates OGC conformance.

**Resolution:** Replaced philosophy heading with "Spec-Informed Client Behavior" — spec knowledge is legitimate INPUT to test design (it tells us what correct behavior looks like), but spec compliance is not the GOAL of testing. Changes applied:

- Philosophy section: Added explicit distinction between spec-conformance testing (❌) and spec-informed client behavior testing (✅)
- M-6 checklist item: Reframed from "validate against spec requirements" to "validate correct client behavior (informed by spec)"
- "Missing Specification Links" example: Replaced with "Testing Spec Compliance Instead of Client Behavior" showing parser output assertions
- All four sample checklists: M-6 now validates client outputs (URLs, parsed objects, errors) not `@specification` tag counts
- Conclusion: "All spec requirements validated" → "All client behaviors verified (informed by spec expectations)"

---

### C2: Docs 35, 36, 37 — Systemic AP3 Through `@specification` Tags

**Severity:** CRITICAL  
**Documents:** [35-jsdoc-testing-documentation-standards.md](../findings/35-jsdoc-testing-documentation-standards.md), [36-test-quality-checklist-review-process.md](../findings/36-test-quality-checklist-review-process.md), [37-test-maintenance-evolution-strategy.md](../findings/37-test-maintenance-evolution-strategy.md)  
**Status:** ✅ Resolved

**Problem:** Three documents form an interconnected spec-traceability system:

1. **Doc 35** defines `@specification OGC 23-001 §7.2` as a "Recommended" custom JSDoc tag (line 77), used in 20+ code examples throughout the document
2. **Doc 37** builds on this with a "Test-to-Spec Traceability System" (line 56) and proposes `scripts/test-traceability.js` to generate spec coverage matrices
3. **Doc 36** requires checklist item M-6: "Tests validate against spec requirements explicitly"

This entire system is AP3 (OGC Requirement Traceability) — organizing tests around OGC spec sections rather than around client code behavior. The upstream codebase has zero JSDoc in test files and zero spec-traceability infrastructure. This system would:

- Structure tests around spec sections instead of client code modules
- Create maintenance burden tracking spec version changes
- Encourage testing spec compliance rather than client behavior
- Add ~2,000 lines of JSDoc overhead to a ~5,000 line test suite

**Fix Required:** Remove the `@specification` tag from Doc 35's recommended tags. Remove the traceability system from Doc 37. Reframe Doc 36's checklist around client behavior validation, not spec compliance. Spec references can exist as _comments_ for context but should never be structural/machine-readable tags that drive test organization.

**Resolution:** Dismantled the interconnected `@specification` tag traceability system across all three documents. Key principle preserved: spec knowledge is legitimate INPUT to test design as plain comments; the structural JSDoc tag infrastructure is the problem. Changes applied:

**Doc 35 (JSDoc Standards):**

- `@specification` tag: changed from "Recommended" to "Not recommended" in tag table (with strikethrough)
- `#### @specification` subsection: replaced with AP3 warning and plain `// Spec context:` comment guidance
- Key Principle #2: "Specification Traceability" → "Spec-Informed Context"
- §5.3 "Specification Linking Standards": replaced with "Spec Context Comments" section
- All 4 JSDoc templates: `@specification` tag → `Spec context:` comment in description
- Summary sections (7.3, 9.2, 10.1, 10.3, 10.6): reframed from traceability to context
- Added top-level AP3 review notice warning that remaining `@specification` instances in code examples should be read as plain comments

**Doc 37 (Maintenance Strategy):**

- Executive summary: "Test-to-Spec Traceability System" → "Spec-Informed Test Maintenance" with AP3 warning
- §2.3: Removed entire traceability system (tag format, `scripts/test-traceability.js`, npm commands, spec change impact analysis) → replaced with lightweight grep-based approach
- Proactive maintenance: "Spec-to-test traceability (via @specification tags)" → "Spec-aware test context (plain comments)"
- Scenario 4: Removed `@specification` tag references from documentation drift detection
- Test file header example: Removed `@specification` tag, added spec context comment
- Spec update workflow: "Update @specification version tags" → "Update spec context comments"
- Component owner: "Spec Compliance" → "Spec Awareness", removed tag maintenance
- Rot indicators: "Broken @specification" → "Outdated Spec Context"
- Monthly health check: "@specification tags validated" → "Spec context comments reference current spec version"
- Pre-commit checklist: "Tests link to spec (@specification tags)" → "Tests note spec context (plain comments)"
- §7.1: Removed Traceability Tool entirely with AP3 warning
- §7.2: Removed Spec Version Updater tool
- Success metrics: "% of @specification tags valid" → "Spec context comments reference latest spec version"
- Added top-level AP3 review notice

**Doc 36 (Quality Checklist):** Already fixed in C1 — M-6 reframed from spec compliance to client behavior validation.

---

## 5. High-Priority Issues

### H1: Doc 17 — Test Line Count 3× Inconsistency

**Severity:** HIGH  
**Document:** [17-coverage-targets-and-metrics.md](../findings/17-coverage-targets-and-metrics.md)  
**Status:** ✅ Resolved

**Problem:** Doc 17 contains two contradictory test line estimates within the same document:

- Line 59: "Total Test Lines: ~4,500-6,000 lines expected" (from Implementation Guide)
- Line 139: "Total Estimated Test Lines: ~13,090-17,016 lines" (from component target matrix)

The 13,090–17,016 figure is **3× higher** than every other estimate in the research series:

- Doc 19 (authoritative): 4,040–5,340 lines
- Doc 20: 4,150–5,850 lines
- Implementation Guide: 4,400–6,300 lines

The inflation comes from extremely granular component estimates: Endpoint (~4,800 lines), Workers (~2,310–2,860 lines), Parsers (~2,200–3,300 lines) that appear to have been estimated independently without reconciliation against the authoritative Doc 19 file inventory.

**Fix Required:** Reconcile the component target matrix (Section 2.1) with Doc 19's authoritative 22-file / 4,040–5,340 line inventory. Add a cross-reference note acknowledging the discrepancy and clarifying which estimate is authoritative.

**Resolution:** Added a discrepancy warning directly after the “Total Estimated Test Lines” figure in the component target matrix. The warning cross-references the Implementation Guide, Doc 19, and Doc 20 estimates, identifies the Endpoint ~4,800 line figure as the primary inflation driver, and directs readers to use Doc 19’s file inventory for sizing. Coverage percentage targets preserved as valid.

---

### H2: Doc 36 — Invented Enterprise Review Process

**Severity:** HIGH  
**Document:** [36-test-quality-checklist-review-process.md](../findings/36-test-quality-checklist-review-process.md)  
**Status:** ✅ Resolved

**Problem:** Doc 36 proposes a 3-stage review process with invented roles:

- **Stage 1:** Self-review (15–30 minutes per test file)
- **Stage 2:** Peer review ("not original developer")
- **Stage 3:** Tech Lead sign-off

This includes a **41-item checklist** (21 "critical"), elaborate markdown review templates, and a requirement for "100 runs with 0 failures" to verify non-flakiness (QM-4, line 636).

Upstream `camptocamp/ogc-client` is a small open-source library where contributions go through standard GitHub PR review. There is no "Tech Lead sign-off," no peer reviewer role distinct from maintainer review, and no 41-item quality gate. This enterprise QA framework would be rejected by upstream maintainers as over-engineering.

**Fix Required:** Simplify to a single-stage self-review checklist (8–12 items maximum) aligned with upstream's actual PR review expectations. Remove invented roles. Remove the 100-run flakiness requirement.

**Resolution:** Replaced 3-stage enterprise review (Self-Review → Peer Review → Tech Lead Sign-Off) with single-stage self-review containing 10 items. Removed invented roles, 41-item/21-critical checklist, elaborate markdown templates (Self-Review, Peer Review, Sign-Off), 3-tier remediation escalation, and the QM-4 100-run flakiness requirement. Simplified overview table from 41 items / 6 dimensions / 3 stages to 4 dimensions / single stage. Added H2 review notice.

---

### H3: Doc 37 — Over-Engineered Maintenance Framework

**Severity:** HIGH  
**Document:** [37-test-maintenance-evolution-strategy.md](../findings/37-test-maintenance-evolution-strategy.md)  
**Status:** ✅ Resolved

**Problem:** Doc 37 proposes enterprise-level maintenance infrastructure for a library contribution:

- Monthly health checks (2–4 hours/month)
- ~70–120 hours/year maintenance burden
- Custom `scripts/test-traceability.js` tool
- Custom `scripts/validate-fixtures.js` tool
- GitHub Actions workflow for monthly automated health checks (`.github/workflows/test-health.yml`)
- Dependabot/Renovate configuration
- A 9-step spec update workflow with 2–4 week timeline
- RACI matrix with 5 roles

All of this is for a contribution to someone else's repository. The contributor doesn't control CI configuration, doesn't set Dependabot policies, and shouldn't propose 70–120 hours/year of ongoing maintenance overhead. Upstream maintains its tests with zero documented maintenance process.

**Fix Required:** Reduce to a brief "test maintenance guidelines" section covering: (1) update fixtures when upstream API changes, (2) keep test patterns aligned with upstream conventions, (3) fix broken tests promptly. Remove all invented tools, workflows, and organizational infrastructure.

**Resolution:** Replaced enterprise maintenance infrastructure throughout Doc 37. Removed: RACI matrix with 5 invented roles (Test Owner, Component Maintainer, Release Manager, Tech Lead, Documentation Maintainer), 9-step spec update workflow with ASCII art flowcharts, monthly health check procedures and templates, custom tooling (rot detection, fixture validation, health report generator, fixture migration, spec version updater, test metrics dashboard), GitHub Actions workflows (monthly cron job, Dependabot config), implementation estimates (33.5–46.5 hours tooling, 84–184 hours/year maintenance), elaborate issue templates, changelogs, migration guides, and test inventory documentation. Replaced with three core maintenance practices, simplified update workflows, and practical guidance. Added H3 review notices throughout.

---

### H4: Doc 35 — Massive JSDoc Over-Engineering

**Severity:** HIGH  
**Document:** [35-jsdoc-testing-documentation-standards.md](../findings/35-jsdoc-testing-documentation-standards.md)  
**Status:** ✅ Resolved

**Problem:** Doc 35 correctly identifies that upstream has near-zero JSDoc in test files (~0.3% documentation density, 0 `@fileoverview`, 0 `@module`). But then proposes 12 JSDoc tag types, 12 templates, custom tags (`@specification`, `@fixture`, `@coverage`, `@scenario`), and detailed documentation standards that would add ~2,000 lines of JSDoc boilerplate to a ~5,000 line test suite.

The document honestly acknowledges the tension: "Don't over-document tests (upstream proves tests can be self-documenting)." But its recommendations contradict this acknowledgment.

**Fix Required:** Align recommendations with upstream's proven minimalist approach. JSDoc for test utility functions (`@param`, `@returns`) is reasonable. Custom `@specification` tags, `@fileoverview` blocks for every test file, and `@fixture` annotations are not. Reduce to: (1) JSDoc for exported helper functions, (2) descriptive `describe`/`it` block names (already upstream practice), (3) optional brief comments for complex test setup.

**Resolution:** Rewrote Doc 35 from 2,178 lines to 382 lines. Removed: 12 JSDoc tag type definitions with detailed Purpose/Usage/When to Use/Example blocks, 4 custom tags (`@specification` already removed in C2, plus `@fixture`, `@coverage`, `@scenario`), 3 tag combination patterns, 4-level documentation level design (file/suite/test/helper with elaborate decision matrices), 12 templates (file-level ×3, test case ×3, helper ×3, plus variants), 365 lines of documentation standards and guidelines, documentation review process with roles (Developer/Reviewer/Maintainer), quarterly audit procedures, 287 lines of patterns and anti-patterns, implementation estimates (30 hours for 80 test files, ROI analysis), 285 lines of complete documentation examples (4 full annotated test files), and 3-phase migration strategy. Replaced with three rules: (1) JSDoc for exported test helpers with `@param`/`@returns`/`@example`, (2) self-documenting test names (upstream practice), (3) optional brief `//` comments for non-obvious behavior. Kept §1 upstream analysis (valuable evidence), added H4 review notice.

---

### H5: Doc 20 — EDR File-Level Line Counts Demonstrably Wrong

**Severity:** HIGH  
**Document:** [20-test-to-code-ratio-validation.md](../findings/20-test-to-code-ratio-validation.md)  
**Status:** ✅ Resolved

**Problem:** Doc 20's file-level line counts for EDR module components are significantly wrong when checked against the actual codebase:

| File              | Doc 20 Claim | Actual    | Error     |
| ----------------- | ------------ | --------- | --------- |
| `helpers.ts`      | 26 lines     | 17 lines  | +53%      |
| `model.ts`        | 126 lines    | 110 lines | +15%      |
| `url_builder.ts`  | 380 lines    | 529 lines | **-28%**  |
| `helpers.spec.ts` | 45 lines     | 33 lines  | +36%      |
| `model.spec.ts`   | 97 lines     | 32 lines  | **+203%** |

The `model.spec.ts` claim is off by 3×. These are not counting methodology differences — they are factually wrong and may indicate the counts were generated rather than measured.

**Fix Required:** Re-measure EDR file line counts from the actual codebase and correct the table. Add a note about the version/commit the measurements were taken from.

**Resolution:** Corrected all EDR file line counts in §2.1 to actual values measured from commit `a836fbe`. Added H5 review notice explaining the discrepancies. Updated derived metrics: implementation total corrected from 709 to ~833 lines (url_builder.ts was 39% larger than claimed), test total corrected from 375 to ~363 lines (model.spec.ts was 3× inflated), overall EDR ratio corrected from 0.53:1 to ~0.44:1. Marked integration file line counts as estimates (EDR portions of shared files). Updated CSAPI vs EDR comparison table and §5.1/§5.2 component comparisons that referenced incorrect EDR values. Also fixed a ratio notation error in the §4 table ("2.0-1.25:1" → "1.25-2.0:1").

---

## 6. Medium-Priority Issues

### M1: Doc 03 — Fabricated Coverage Estimate

**Severity:** MEDIUM  
**Document:** [03-typescript-testing-standards.md](../findings/03-typescript-testing-standards.md)  
**Status:** ✅ Resolved

**Problem:** Doc 03 claims "ogc-client Assessment: Coverage: ~80% estimated ✅ Mature." Upstream has **no coverage reporting**, no coverage thresholds in `jest.config.cjs`, and no coverage scripts in `package.json`. The ~80% figure is a guess presented as a validated finding.

**Fix Required:** Change to "Coverage: Not measured (no coverage thresholds or scripts configured)" and remove the "✅ Mature" assessment for coverage specifically.

**Resolution:** Corrected all 3 occurrences of the fabricated ~80% coverage claim in Doc 03. Changed: (1) comparison table entry from "✅ Match" to "⚠️ Unknown" with "No coverage tooling configured", (2) ogc-client assessment from "✅ Mature" to "⚠️ Unknown" with explanation that no coverage thresholds, scripts, or reporting are configured, (3) summary section from "✅ ~80% estimated coverage" to "⚠️ Coverage not measured."

---

### M2: Doc 17 — AP3 in Behavior Coverage Metrics

**Severity:** MEDIUM  
**Document:** [17-coverage-targets-and-metrics.md](../findings/17-coverage-targets-and-metrics.md)  
**Status:** ✅ Resolved

**Problem:** Doc 17 Section 3 defines "Behavior Coverage" as:

> Behavior Coverage = (Behavior Tests / Total Requirements) × 100%

And lists "Required Behavior Tests" that are spec requirements:

- "Systems list endpoint supports pagination"
- "DataStreams can be filtered by phenomenonTime"

This frames coverage as spec-requirement coverage (AP3), not as code-path coverage. Testing should be organized around client code paths (URL builder methods, parser functions, error handlers), not around OGC spec requirements.

**Fix Required:** Reframe behavior coverage around client code functions and methods, not spec requirements. E.g., "URL builder methods covered: 9/9 resource types" instead of "Spec requirements covered: 27/30."

**Resolution:** Rewrote §3.2.4 from "Behavior-Driven Coverage" (spec-requirement framing) to "Client Code Coverage" (client code path framing). Replaced: 12 spec-requirement-style test descriptions ("Systems list endpoint supports pagination", etc.) with coverage organized by client code area (QueryBuilder methods, Parser functions, Endpoint methods). Changed metric from "Behavior Tests / Total Requirements" to "Tested functions & branches / Total functions & branches" using Jest's built-in `--coverage`. Added M2 review notice. Updated 3 checklist items that referenced "behavior coverage" and "business requirements" to reference public methods and code paths instead.

---

### M3: Doc 20 — Module-Level Ratios Systematically Inflated

**Severity:** MEDIUM  
**Document:** [20-test-to-code-ratio-validation.md](../findings/20-test-to-code-ratio-validation.md)  
**Status:** ✅ Resolved

**Resolution:** All module-level line counts in Doc 20 §1.2, §2.2, §2.3, and §2.4 corrected to actual measured values from the codebase (commit `1694f09`). Added M3 review notice in §1.2 documenting the systematic inflation pattern. Key corrections: WFS 1,124→1,056 impl / 2,003→1,960 test; WMTS 647→611 / 1,543→1,511; STAC 1,296→1,212 / 926→802; TMS 497→448 / 513→467; WMS 738→698 / 876→843. EDR url_builder 380→529. Overall average changed minimally (1.44:1→1.45:1).

---

### M4: Doc 37 — AP2 Risk in Fixture Versioning

**Severity:** MEDIUM  
**Document:** [37-test-maintenance-evolution-strategy.md](../findings/37-test-maintenance-evolution-strategy.md)  
**Status:** ✅ Resolved

**Resolution:** Removed fixture `_metadata` system and `package.json` `csapi` key from Doc 37 §2.1. Section now recommends only README documentation for spec version tracking. Simplified Scenario 4 from "Add metadata fields to all ~280+ fixtures (6-10 hrs)" to "Fixture Schema Update" scoped to affected resource types (1-4 hrs). Removed "Add version metadata to fixtures" from §1.4 Scenario 3 remediation. Added M4 review notices.

---

## 7. Low-Priority Issues

### L1: Doc 20 — Unverifiable Industry Library Ratios

**Severity:** LOW  
**Document:** [20-test-to-code-ratio-validation.md](../findings/20-test-to-code-ratio-validation.md)  
**Status:** ✅ Resolved

**Resolution:** Added L1 review notice in §3.1 clarifying that library line counts are rough estimates, not independently verified. Marked all ratio values in the Popular Library Ratios table as estimates (~). Changed "Industry Average" notes to "Estimated". The general observation that TypeScript client libraries fall in the 1.0–2.0:1 range remains valid.

---

### L2: Doc 17 — Premature Jest Configuration

**Severity:** LOW  
**Document:** [17-coverage-targets-and-metrics.md](../findings/17-coverage-targets-and-metrics.md)  
**Status:** ✅ Resolved

**Resolution:** Added L2 review notice at the top of §4 (Jest Configuration Specification) clarifying that the configuration is a template for future use. CSAPI files referenced in `coverageThreshold` (e.g., `url_builder.ts`, `parsers/*.ts`) do not exist yet. Configuration should be adapted incrementally as implementation progresses.

---

### L3: Doc 03 — Minor Ratio Measurement Discrepancies

**Severity:** LOW  
**Document:** [03-typescript-testing-standards.md](../findings/03-typescript-testing-standards.md)  
**Status:** ✅ Resolved

**Resolution:** Added L3 review notice in Doc 03’s ogc-client ratio listing noting that values are approximate and methodology-dependent. Added measured values (commit `1694f09`) alongside each module ratio for comparison. Updated average from 1.44× to ~1.45×. Corrected WFS reference from 1,124 to ~1,056 impl lines and updated derived ratio accordingly.

---

## 8. Positive Findings

### P1: Doc 03 — Strong Upstream Pattern Analysis

Doc 03 correctly identifies and recommends upstream conventions:

- Global Jest imports (not `@jest/globals`)
- `jest.fn().mockImplementation()` for fetch mocking
- 0% E2E tests (all mocked)
- Fixture-driven testing throughout
- TypeScript compilation testing as enhancement (correctly characterized as optional)

The document's core recommendation — "follow upstream patterns" — is exactly right.

### P2: Doc 20 — Honest Estimate Reconciliation

Doc 20 performs a useful service by reconciling test line estimates from the Implementation Guide against the Doc 19 file inventory, arriving at a 5–10% reduction. The final CSAPI ratio positioning (0.86–0.90:1) is conservative and reasonable. The document honestly acknowledges that CSAPI's ratio is below the upstream average (1.45:1), which is appropriate for a new module.

### P3: Doc 17 — Phase-Based Coverage Ratcheting

Doc 17's incremental coverage approach (Phase 4: 50% → Phase 5: 70% → Phase 6: 80% → Phase 7: 88%) is a sound strategy that avoids the common mistake of requiring high coverage before any code exists. This allows coverage to grow organically with implementation.

### P4: Doc 36 — Meaningful vs. Trivial Distinction

Despite the process over-engineering, Doc 36's core distinction between meaningful and trivial tests is valuable. The "break the code → does the test fail?" validation concept and the examples of good vs. bad testing patterns are well-illustrated and practically useful.

### P5: Doc 03 — Correct Client-Side Orientation

Doc 03's examples consistently test client behavior (URL construction, response parsing, type validation) rather than server compliance. The document correctly avoids AP1, AP2, and AP5 throughout its code examples.

---

## 9. Cross-Document Consistency Analysis

### 9.1 Interconnected AP3 System

The most concerning cross-document finding is that Docs 35, 36, and 37 form a self-reinforcing AP3 system:

```
Doc 35 (JSDoc) ──defines──→ @specification tags
                                    ↓
Doc 37 (Maintenance) ──uses──→ traceability tool parses @specification tags
                                    ↓
Doc 36 (Quality) ──requires──→ "Tests validate against spec requirements"
```

This system would embed spec-traceability into every test file, every review, and every maintenance cycle. It must be dismantled as a unit — fixing one document without the others would leave orphaned references.

### 9.2 Test Line Estimate Inconsistency

| Source                 | Estimate                | Status              |
| ---------------------- | ----------------------- | ------------------- |
| Doc 19 (authoritative) | 4,040–5,340 lines       | ✅ Reference        |
| Implementation Guide   | 4,400–6,300 lines       | ✅ Compatible       |
| Doc 20                 | 4,150–5,850 lines       | ✅ Compatible       |
| Doc 03                 | 4,500–6,000 lines       | ✅ Compatible       |
| **Doc 17**             | **13,090–17,016 lines** | **❌ 3× inflation** |

Doc 17 is the sole outlier. Its component-level breakdown appears to have been estimated independently for each component without checking against the authoritative file inventory.

---

## 10. Recommendations

### 10.1 Immediate Actions (Before Implementation)

1. **CRITICAL: Dismantle the AP3 spec-traceability system** across Docs 35, 36, 37. Remove `@specification` tags, the traceability tool, and "spec compliance over implementation" philosophy. Replace with client-behavior-focused quality criteria.

2. **HIGH: Reconcile Doc 17's test line estimate** with the authoritative Doc 19 inventory (4,040–5,340 lines). The 13,090–17,016 figure is not credible.

3. **HIGH: Simplify Doc 36** from a 41-item/3-stage enterprise process to a lightweight self-review checklist appropriate for OSS contribution.

4. **HIGH: Scale back Doc 37** from an enterprise maintenance framework to brief maintenance guidelines (update fixtures when needed, keep patterns upstream-aligned).

5. **HIGH: Correct Doc 20's EDR line counts** from actual codebase measurements.

### 10.2 Documents Usable As-Is

- **Doc 03** — Sound with minor corrections (remove fabricated coverage estimate)
- **Doc 20** — Sound with corrections to EDR line counts and industry ratio caveats

### 10.3 Documents Requiring Major Revision

- **Doc 35** — Useful JSDoc guidance buried under AP3 spec-traceability system
- **Doc 36** — Useful quality criteria buried under enterprise process framework
- **Doc 37** — Some valid maintenance concepts buried under invented infrastructure

### 10.4 Next Phase

Proceed to **Phase 2D: Format Parsers** (Docs 09, 10, 11), which have high AP4 risk and are closest to real implementation code.

---

## 11. Issue Tracker

| ID  | Severity | Document(s) | Issue                                                                     | Status      |
| --- | -------- | ----------- | ------------------------------------------------------------------------- | ----------- |
| C1  | CRITICAL | 36          | "Spec Compliance Over Implementation" philosophy (AP3)                    | ✅ Resolved |
| C2  | CRITICAL | 35, 36, 37  | Systemic AP3 through `@specification` tag traceability system             | ✅ Resolved |
| H1  | HIGH     | 17          | Test line estimate 13,090–17,016 is 3× higher than all other estimates    | ✅ Resolved |
| H2  | HIGH     | 36          | Invented 3-stage enterprise review process with 41-item checklist         | ✅ Resolved |
| H3  | HIGH     | 37          | Over-engineered maintenance framework (70–120 hrs/yr, custom tools, RACI) | ✅ Resolved |
| H4  | HIGH     | 35          | Massive JSDoc over-engineering despite acknowledging upstream minimalism  | ✅ Resolved |
| H5  | HIGH     | 20          | EDR file-level line counts demonstrably wrong (model.spec.ts off by 3×)   | ✅ Resolved |
| M1  | MEDIUM   | 03          | Fabricated "~80% estimated" coverage for upstream                         | ✅ Resolved |
| M2  | MEDIUM   | 17          | AP3 in behavior coverage metrics (spec requirements as coverage targets)  | ✅ Resolved |
| M3  | MEDIUM   | 20          | Module-level ratios systematically inflated 5–13%                         | ✅ Resolved |
| M4  | MEDIUM   | 37          | AP2 risk in fixture `_metadata` versioning system                         | ✅ Resolved |
| L1  | LOW      | 20          | Unverifiable industry library ratio estimates                             | ✅ Resolved |
| L2  | LOW      | 17          | Premature Jest configuration for non-existent files                       | ✅ Resolved |
| L3  | LOW      | 03          | Minor ratio measurement discrepancies (5–12%)                             | ✅ Resolved |

**Summary:** 2 Critical, 5 High, 4 Medium, 3 Low — **14 total issues**
