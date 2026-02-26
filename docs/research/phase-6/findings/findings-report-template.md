# Findings Report [NN]: [Descriptive Title]

> **Plan [N] of [Total]** | **Phase 6 — Upstream Acceptance Refactoring**

---

## Metadata

| Field                  | Value                                                                                    |
| ---------------------- | ---------------------------------------------------------------------------------------- |
| **Research Plan**      | [Plan NN: Title](../research-plans/NN-slug.md)                                           |
| **Plan Type**          | [Same as research plan: Internal analysis / External research / Design synthesis / etc.] |
| **Date Started**       | [YYYY-MM-DD]                                                                             |
| **Date Completed**     | [YYYY-MM-DD]                                                                             |
| **Research Time**      | [X hours (actual)]                                                                       |
| **Estimated Time**     | [X–Y hours (from plan)]                                                                  |
| **Questions Answered** | [N of N detailed questions]                                                              |
| **Depends On**         | [Plan numbers this research built upon]                                                  |
| **Blocks**             | [Plan numbers that can now proceed with these findings]                                  |

---

## Source Summary

### Primary Sources Consulted

| Source        | Path / URL             | What Was Extracted        |
| ------------- | ---------------------- | ------------------------- |
| [Description] | [relative/path or URL] | [What was found and used] |
| [Description] | [relative/path or URL] | [What was found and used] |

### Prior Findings Used

| Finding            | Path                                | What Was Consumed                                                 |
| ------------------ | ----------------------------------- | ----------------------------------------------------------------- |
| [Plan NN findings] | [relative/path/to/findings/NN-*.md] | [Specific findings, decisions, or data consumed from that report] |

### Sources Not Available or Not Useful

[List any sources from the research plan's source list that were inaccessible, irrelevant, or unhelpful. Briefly explain why and what alternative was used, if any.]

- [Source]: [Why not available/useful] → [Alternative used, or "None needed"]

---

## Executive Summary

[2–4 paragraphs summarizing the key findings. This should be readable standalone — a reader who only reads this section should understand what was investigated, what was found, and what it means for the implementation.]

### Key Metrics

[Optional — include if the research produced quantifiable data. Use a table or bullet list.]

| Metric              | Value   | Significance     |
| ------------------- | ------- | ---------------- |
| [What was measured] | [Value] | [Why it matters] |

### Overall Assessment

[1–2 sentences: the bottom line. What is the single most important takeaway from this research?]

---

## Table of Contents

[Include for findings reports with 5+ sub-topic sections. Omit for shorter reports.]

1. [Executive Summary](#executive-summary)
2. [Sub-topic A Section Title](#section-number-title)
3. [Sub-topic B Section Title](#section-number-title)
4. [Sub-topic C Section Title](#section-number-title)
5. [Boundary Condition Verification](#boundary-condition-verification)
6. [Implementation Scope Gate Assessment](#implementation-scope-gate-assessment)
7. [Impact on Dependent Plans](#impact-on-dependent-plans)
8. [Key Takeaways](#key-takeaways)
9. [Impact on Implementation](#impact-on-implementation)
10. [Open Questions](#open-questions)

---

<!-- ============================================================
     SUB-TOPIC SECTIONS

     Create one numbered section per research question sub-topic
     from the research plan's Section 4 (Detailed Questions).

     Each sub-topic section should:
     - Match the sub-topic heading from the research plan
     - Answer every numbered question under that sub-topic
     - Provide evidence for each answer (code references, spec
       quotes, analysis results, external documentation)
     - Use tables, code blocks, and diagrams where they add clarity

     Number sections sequentially starting from 1.
     ============================================================ -->

## 1. [Sub-topic A — matching research plan sub-topic heading]

[Introduce the sub-topic: what was investigated and why it matters.]

### Question [N]: [Question text from plan]

**Answer:** [Direct, specific answer to the question.]

**Evidence:**
[Supporting evidence — code snippets, file references, spec quotes, analysis results. Cite sources using the Source Summary table references.]

```
[Code example, command output, or structured data if applicable]
```

### Question [N+1]: [Question text from plan]

**Answer:** [Direct, specific answer.]

**Evidence:**
[Supporting evidence.]

### Sub-topic Synthesis

[1–2 paragraphs summarizing what the answers to this sub-topic's questions mean collectively. What pattern emerges? What decision does this inform?]

---

## 2. [Sub-topic B — matching research plan sub-topic heading]

[Repeat the same structure as Sub-topic A: introduction, per-question answers with evidence, sub-topic synthesis.]

---

## 3. [Sub-topic C — matching research plan sub-topic heading]

[Repeat the same structure.]

---

<!-- ============================================================
     Continue adding sub-topic sections as needed until all
     detailed questions from the research plan are answered.
     ============================================================ -->

---

## [N+1]. Boundary Condition Verification

[Verify each boundary condition from the research plan's Section 3 against the research findings. This section confirms that the findings respect the non-negotiable constraints.]

### Constraint Compliance Matrix

| #   | Constraint                        | Status                                    | Evidence                                          | Notes                |
| --- | --------------------------------- | ----------------------------------------- | ------------------------------------------------- | -------------------- |
| 1   | [Constraint text from plan § 3.1] | ✓ Compliant / ✗ Violated / ⚠️ Conditional | [How the findings comply or where tension exists] | [Additional context] |
| 2   | [Constraint text]                 | ✓ / ✗ / ⚠️                                | [Evidence]                                        | [Notes]              |
| 3   | [Constraint text]                 | ✓ / ✗ / ⚠️                                | [Evidence]                                        | [Notes]              |

### Scope Boundary Adherence

[Confirm that the research stayed within the plan's "What Remains Open" boundaries and did not drift into "Excluded From Scope" territory.]

- **In scope — explored:** [List what was investigated]
- **Out of scope — respected:** [List what was intentionally avoided per the plan]
- **Scope adjustments:** [If any planned questions became unanswerable or irrelevant, explain why and what was done instead]

---

## [N+2]. Implementation Scope Gate Assessment

> **Required for Plans 06 and 08. Recommended for all plans.**

[Apply the "research broadly, implement minimally" principle. Document any findings that are intellectually interesting but should NOT translate into implementation work beyond jahow's two requirements.]

### Minimum-Change Test

For each significant finding or recommendation in this report, answer:

| Finding / Recommendation | Serves jahow's requirements?                                              | Minimum-change? | Include in implementation?       |
| ------------------------ | ------------------------------------------------------------------------- | --------------- | -------------------------------- |
| [Finding 1]              | Yes — directly required / Yes — necessary consequence / No — nice-to-have | Yes / No        | ✓ Include / ✗ Defer / ⚠️ Discuss |
| [Finding 2]              | [Assessment]                                                              | [Assessment]    | [Decision]                       |

### Deferred Insights

[List findings that are valuable knowledge but should NOT drive implementation work. These may be useful for future iterations or upstream discussions.]

- [Insight]: [Why it's deferred — which scope gate criterion it fails]

---

## [N+3]. Impact on Dependent Plans

[Explicitly state what each downstream plan should consume from these findings. This is the handoff specification.]

### What Downstream Plans Should Consume

| Downstream Plan | What to consume from this report                          | Section reference            |
| --------------- | --------------------------------------------------------- | ---------------------------- |
| Plan [NN]       | [Specific findings, decisions, data, or artifacts to use] | [§ N.N or "Key Takeaway #N"] |
| Plan [NN]       | [Specific findings]                                       | [Section reference]          |

### Decisions Now Final

[List any decisions that are now settled and should not be revisited by downstream plans unless new constraints emerge.]

1. [Decision]: [Brief rationale]
2. [Decision]: [Brief rationale]

### Items Requiring Downstream Resolution

[List anything this plan could not resolve that a downstream plan must address.]

1. [Item] → [Which plan should resolve it and why]

---

## [N+4]. Key Takeaways

[Numbered list of the 5–12 most important findings. Each takeaway should be one sentence or a short paragraph. Order by importance.]

1. **[Takeaway title]:** [Concise statement of the finding and its significance.]
2. **[Takeaway title]:** [Concise statement.]
3. **[Takeaway title]:** [Concise statement.]
4. **[Takeaway title]:** [Concise statement.]
5. **[Takeaway title]:** [Concise statement.]

---

## [N+5]. Impact on Implementation

[Concrete, actionable implications of these findings for the actual code changes. Organized by type of impact.]

### Must Change (Required by Findings)

[Changes that are directly required to meet jahow's acceptance criteria, now informed by these findings.]

1. [Specific change and why the findings require it]
2. [Specific change]

### Should Change (Recommended by Findings)

[Changes that findings support as best practice but that are not strictly required.]

1. [Recommended change and rationale]

### Could Change (Optional Improvements)

[Changes that findings surfaced as possible improvements but that fall outside minimum implementation scope. Included for completeness and future reference.]

1. [Optional improvement]

---

## [N+6]. Open Questions

[Anything unresolved. Each question should identify which downstream plan (if any) should address it.]

| #   | Question        | Why Unresolved                                   | Resolution Path                                                                           |
| --- | --------------- | ------------------------------------------------ | ----------------------------------------------------------------------------------------- |
| 1   | [Open question] | [Why this couldn't be answered in this research] | [Plan NN should address this / Needs upstream clarification / Deferred to implementation] |
| 2   | [Open question] | [Why unresolved]                                 | [Resolution path]                                                                         |

---

## Evidence Appendix

> **Optional.** Include if the research produced detailed artifacts (code analysis outputs, full specification excerpts, command outputs, dependency graphs, etc.) that are too long for inline inclusion but are needed for traceability.

### A. [Artifact Title]

[Full artifact content or reference to external file.]

### B. [Artifact Title]

[Full artifact content or reference.]

---

## Research Completion Checklist

- [ ] All detailed questions from the research plan have specific, evidenced answers
- [ ] Boundary condition verification completed (Section [N+1])
- [ ] Implementation scope gate assessment completed (Section [N+2])
- [ ] Impact on dependent plans documented (Section [N+3])
- [ ] Key takeaways extracted (Section [N+4])
- [ ] Open questions cataloged with resolution paths (Section [N+6])
- [ ] Cross-references to prior findings are accurate
- [ ] Findings respect all boundary conditions from the research plan
- [ ] Document is self-contained — a reader unfamiliar with the plan can understand the findings

**Research Started:** [YYYY-MM-DD]
**Research Completed:** [YYYY-MM-DD]
**Reviewed:** [Not yet / YYYY-MM-DD]

---

## Notes

[Space for observations, surprises, methodology adjustments, or process improvements discovered during research. Remove this section if empty.]
