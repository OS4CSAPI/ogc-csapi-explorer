# Research Plan [NN]: [Title]

> **Plan [N] of [Total]** | **Phase 6 — Upstream Acceptance Refactoring**

---

## Metadata

| Field                  | Value                                                                                                                                                                                     |
| ---------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Status**             | Not Started                                                                                                                                                                               |
| **Plan Type**          | [Internal analysis / External research (industry) / External research (architecture) / External research (standards) / Design synthesis / Implementation synthesis / Mechanical analysis] |
| **Date Created**       | [YYYY-MM-DD]                                                                                                                                                                              |
| **Last Updated**       | [YYYY-MM-DD]                                                                                                                                                                              |
| **Estimated Time**     | [X–Y hours]                                                                                                                                                                               |
| **Actual Time**        | —                                                                                                                                                                                         |
| **Depends On**         | [Plan numbers, or "None"]                                                                                                                                                                 |
| **Blocks**             | [Plan numbers that cannot start until this completes]                                                                                                                                     |
| **Strategy Reference** | [research-strategy.md § Plan NN](../research-strategy.md)                                                                                                                                 |

---

## 1. Research Objective

[2–3 sentences describing what this research plan will investigate and what understanding it will produce. Be specific about the output — not "understand X" but "produce a [document/matrix/decision/catalog] that answers Y."]

---

## 2. Sequencing Rationale

### Why Plan [N]?

[1–2 paragraphs explaining why this plan is in this position in the sequence.]

### Dependency Chain

- **Builds on:** [What prior plans provide the foundation? What knowledge from those plans is needed here?]
- **Feeds into:** [What subsequent plans depend on this plan's findings? What decisions are blocked until this completes?]

---

## 3. Boundary Conditions

### Non-Negotiable Constraints

[Restate the specific boundary conditions from the research strategy that apply to this plan. Reference the constraint numbers from the strategy document.]

1. [Constraint and how it applies to this plan's scope]
2. [Constraint and how it applies to this plan's scope]

### Excluded From Scope

[Explicitly list patterns, approaches, or topics that are OUT of scope for this plan, and why.]

- **[Pattern/topic]:** [Why excluded — which constraint does it violate, or which other plan covers it?]
- **[Pattern/topic]:** [Why excluded]

### What Remains Open

[Explicitly list the genuine design decisions or open questions this plan IS authorized to explore.]

- [Open question 1]
- [Open question 2]

---

## 4. Research Questions

### Core Questions

[3–6 high-level questions that frame the entire investigation. These are the questions that, if answered, mean the research objective is met.]

1. [Core question]
2. [Core question]
3. [Core question]

### Detailed Questions

[Organized by sub-topic. Each sub-topic has 3–8 specific, answerable questions. Number all questions sequentially across sub-topics for easy reference in findings reports.]

#### [Sub-topic A] ([N] questions)

1. [Specific, answerable question]
2. [Specific, answerable question]
3. [Specific, answerable question]

#### [Sub-topic B] ([N] questions)

4. [Specific, answerable question]
5. [Specific, answerable question]
6. [Specific, answerable question]

#### [Sub-topic C] ([N] questions)

7. [Specific, answerable question]
8. [Specific, answerable question]
9. [Specific, answerable question]

**Total: [N] detailed questions**

---

## 5. Sources

### Primary Sources (In Workspace)

[Files in the repository that are the main inputs for this research. Include relative paths.]

| Source        | Path                        | What to Extract                 |
| ------------- | --------------------------- | ------------------------------- |
| [Description] | [relative/path/to/file.ext] | [What specifically to look for] |
| [Description] | [relative/path/to/file.ext] | [What specifically to look for] |

### External Sources

[URLs, documentation sites, GitHub repositories, specifications, etc.]

| Source        | URL/Reference      | What to Extract                 |
| ------------- | ------------------ | ------------------------------- |
| [Description] | [URL or reference] | [What specifically to look for] |
| [Description] | [URL or reference] | [What specifically to look for] |

### Prior Research Findings

[Findings from earlier plans that this plan builds on.]

| Finding            | Path                                | What to Use                      |
| ------------------ | ----------------------------------- | -------------------------------- |
| [Plan NN findings] | [relative/path/to/findings/NN-*.md] | [What specifically to reference] |

---

## 6. Research Methodology

### Phase 1: [Phase Name] (~[N] minutes)

**Objective:** [One sentence]

**Tasks:**

1. [Concrete, verifiable task]
2. [Concrete, verifiable task]
3. [Concrete, verifiable task]

**Output:** [What this phase produces that feeds into the next phase]

### Phase 2: [Phase Name] (~[N] minutes)

**Objective:** [One sentence]

**Tasks:**

1. [Concrete, verifiable task]
2. [Concrete, verifiable task]
3. [Concrete, verifiable task]

**Output:** [What this phase produces]

### Phase 3: [Phase Name] (~[N] minutes)

**Objective:** [One sentence]

**Tasks:**

1. [Concrete, verifiable task]
2. [Concrete, verifiable task]
3. [Concrete, verifiable task]

**Output:** [What this phase produces]

### Phase 4: Synthesis and Documentation (~[N] minutes)

**Objective:** Consolidate all phase outputs into the deliverable document

**Tasks:**

1. Synthesize findings from Phases 1–3
2. Verify all [N] research questions are answered
3. Validate findings against boundary conditions
4. Write deliverable document
5. Cross-reference with dependent plans

**Output:** Completed findings report at `docs/research/phase-6/findings/[NN]-[slug].md`

---

## 7. Success Criteria

This research is complete when:

- [ ] All [N] detailed research questions have specific, evidenced answers
- [ ] Findings respect all boundary conditions listed in Section 3
- [ ] [Plan-specific success criterion]
- [ ] [Plan-specific success criterion]
- [ ] [Plan-specific success criterion]
- [ ] Deliverable document is complete and follows the findings report template
- [ ] Findings are cross-referenced with dependent plans

---

## 8. Deliverable

**Title:** [Descriptive title of the findings document]

**Location:** `docs/research/phase-6/findings/[NN]-[slug].md`

**Required Sections:** (per findings report template)

1. Executive Summary — key findings in 2–4 paragraphs
2. [Section matching first research question sub-topic]
3. [Section matching second research question sub-topic]
4. [Section matching third research question sub-topic]
5. Key Takeaways — numbered list of critical findings
6. Impact on Implementation — how findings affect design/code
7. Open Questions — anything unresolved that feeds into later plans

---

## 9. Risks and Mitigation

| Risk                  | Impact                                        | Mitigation         |
| --------------------- | --------------------------------------------- | ------------------ |
| [What could go wrong] | [How it affects the plan or downstream plans] | [How to handle it] |
| [What could go wrong] | [How it affects the plan]                     | [How to handle it] |

---

## 10. Research Status Checklist

- [ ] Phase 1: [Phase Name] — Not Started
- [ ] Phase 2: [Phase Name] — Not Started
- [ ] Phase 3: [Phase Name] — Not Started
- [ ] Phase 4: Synthesis and Documentation — Not Started
- [ ] Deliverable document created
- [ ] Cross-references updated in dependent plans

**Start Date:** —
**Completion Date:** —
**Actual Time:** —

---

## 11. Notes

[Space for observations, questions that arise during research, or adjustments to the plan. Remove this section if empty when the plan is created; add it back if notes are needed during execution.]
