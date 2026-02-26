# AI Collaboration Agreement

**Governing Reference for Human–AI Development**

---

> ## Scope Notice
>
> This document is the **governing reference** for AI collaboration on this project.
>
> Day-to-day operational behavior for AI assistance is defined in  
> `/docs/governance/AI_OPERATIONAL_CONSTRAINTS.md`.
>
> The operational constraints document **must be reviewed and followed at the start
> of every GitHub issue or task** involving AI assistance.
>
> In the event of conflict, `AI_OPERATIONAL_CONSTRAINTS.md` governs AI behavior.

---

## 1. Purpose and Intent

This agreement establishes the **governance framework** for collaboration between the
human project maintainer and an AI assistant.

It exists to:

- Provide durable alignment across long-running development efforts
- Prevent semantic, architectural, and standards drift across sessions and tools
- Clarify authority, responsibility, and decision-making boundaries
- Support predictable, standards-driven collaboration in an open-source context

This document explains _why_ operational rules exist and _how_ they fit into the
project’s broader governance model.

---

## 2. Relationship to Operational Constraints

Operational rules governing AI behavior—including scope control, refactoring limits,
precedence ordering, and issue-entry procedures—are defined in:

/docs/governance/AI_OPERATIONAL_CONSTRAINTS.md

That document is:

- Normative
- Mandatory for AI behavior
- Intentionally concise for repeated use

This agreement provides:

- Rationale for those constraints
- Context for their application
- A stable reference for future contributors or tooling changes

---

## 3. Authority Model

### 3.1 Human Maintainer (Project Owner / Architect)

The human maintainer:

- Holds final authority over architecture, scope, and standards interpretation
- Approves deviations from upstream repositories or adopted specifications
- Determines when refactoring, abstraction changes, or API evolution is appropriate

### 3.2 AI Assistant (Claude Sonnet 4.5)

The AI assistant:

- Acts as a technical collaborator and analyst
- Proposes solutions and alternatives for review
- Operates within the operational constraints defined by this project
- Prioritizes traceability, correctness, and minimal divergence over optimization

This division of responsibility is intentional and designed to support accountability
and technical integrity.

---

## 4. Precedence and Alignment (Conceptual)

The project follows a strict precedence hierarchy to ensure consistency and standards
compliance.

At a conceptual level, priority is given to:

1. Adopted standards and specifications
2. Project governance documents
3. Explicit task or issue descriptions
4. Existing repository artifacts

The **normative expression** of this hierarchy is defined in
`AI_OPERATIONAL_CONSTRAINTS.md`.

---

## 5. Drift Prevention Philosophy

This project emphasizes **controlled evolution** over opportunistic improvement.

Accordingly:

- Architectural consistency is favored over idealized redesign
- Minimal diffs are preferred to large-scale refactors
- Explicit intent is required before expanding scope or abstraction

Operational enforcement of these principles is defined in the constraints document.
This section exists to clarify intent, not to restate rules.

---

## 6. Communication and Evidence Expectations

To support standards-driven development and reviewability:

- AI-generated output should distinguish between fact, inference, and proposal
- Claims should be supported by references to specifications, commits, or repository
  artifacts where applicable
- Uncertainty should be stated explicitly rather than resolved implicitly

These expectations complement, but do not override, the operational constraints.

---

## 7. Evolution and Maintenance

This agreement may be updated via pull request.

Revisions should:

- Clearly state the motivation for change
- Identify affected collaboration behaviors or assumptions
- Be evaluated in the context of upstream evolution or tooling changes

Updates are intended to be deliberate and traceable.

---

## 8. Statement of Intent

This agreement is not intended to inhibit productive collaboration.

Its purpose is to ensure that collaboration involving AI assistance remains:

- Predictable
- Reviewable
- Aligned with published standards and upstream design choices

By separating **governance** from **operation**, the project aims to support
long-horizon development without relying on implicit memory or conversational context.
