# AI Operational Constraints

**Mandatory Ground Rules for AI Collaboration**

This document defines **non-negotiable operational constraints** for AI assistance on this project.

It must be reviewed and followed at the start of **every GitHub issue, task, or major discussion** involving AI assistance.

These constraints exist to prevent architectural drift, scope creep, and standards misalignment.

---

## 1. Authority and Precedence

In all cases of ambiguity or conflict, apply the following precedence order **strictly**:

1. Adopted standards, specifications, and normative references
2. AI Collaboration Agreement (`AI_COLLABORATION_AGREEMENT.md`)
3. Active GitHub issue description
4. Existing repository code and documentation
5. Conversational context or prior AI responses

Do not override higher-precedence sources based on inference or convenience.

---

## 2. Mandatory Behavioral Rules

### 2.1 Assumptions and Scope

- Do **not** infer unstated requirements
- Do **not** expand scope beyond the issue description
- When intent is unclear, **stop and ask for clarification**

### 2.2 Architectural Alignment

- Preserve upstream structure, naming, and patterns unless explicitly instructed otherwise
- Prefer **minimal diffs** over idealized rewrites
- Do not introduce new abstractions, layers, or dependencies without approval

### 2.3 Refactoring Prohibitions

- Do **not** refactor for style, clarity, or “best practice” unless explicitly requested
- Do **not** rename files, symbols, or tests unless required by the task
- Avoid changes that increase diff noise

---

## 3. Standards and Evidence Discipline

- Treat cited specifications as authoritative
- Clearly distinguish between:
  - **Fact** (verifiable)
  - **Inference** (reasoned but not explicit)
  - **Proposal** (requires approval)
- Cite specific clauses, sections, commits, or files when possible
- Avoid authoritative language when uncertainty exists

---

## 4. Issue Entry Procedure (Required)

At the start of **every new GitHub issue or major task**, the AI assistant must:

1. Acknowledge review of this document
2. Restate the issue goal in **one concise sentence**
3. Identify any assumptions requiring confirmation

**Required acknowledgment format:**

> I have reviewed the AI Operational Constraints.  
> Issue goal: \<one-sentence restatement\>.  
> Assumptions requiring confirmation: \<if any\>.

If drift, contradiction, or uncertainty arises, pause and re-anchor to this document before proceeding.

---

## 5. Stop Condition

When uncertainty cannot be resolved using the precedence rules above, the AI assistant must **stop and request clarification** rather than proceed based on assumption.

---

## 6. Relationship to Other Documents

This document defines **mandatory operational behavior**.

The full `AI_COLLABORATION_AGREEMENT.md` provides additional context, rationale, and governance guidance and may be referenced as needed.

Issues involving AI implementation work should follow the template defined in
`issue-creation-prompt-template.md` (same directory) to ensure uniform scope
boundaries, acceptance criteria, and reference documentation across all tasks.
