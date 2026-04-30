# Issue Creation Prompt Template — Phase 8

**Purpose:** Reusable template for creating GitHub issues that implement the Phase 8 roadmap. Phase 8 closes the senior developer's second code review (7 accepted findings) plus 2 server-interop bugs surfaced by CS-Go integration testing, and refreshes [PR #136](https://github.com/camptocamp/ogc-client/pull/136) for upstream maintainer [@jahow](https://github.com/jahow)'s final review. Every issue produced from this template acts as an AI scope-containment boundary **and** carries forward the locked decisions from the Phase 8 trio so the AI cannot drift back into "should we reconsider Option B?" mid-execution.

**Usage:** Copy the template below, fill in the placeholders (marked with `{{...}}`), and create the issue via the GitHub API or UI.

**Version:** 1.1
**Date:** April 29, 2026
**Complements:** [`issue-creation-prompt-template-code-review.md`](issue-creation-prompt-template-code-review.md) (v1.0) — that template is the general-purpose form for findings outside a phase. **Use _this_ template for every Phase 8 task (A1–E2) on the [P8-ROADMAP](../planning/phase-8/P8-ROADMAP.md).**

**v1.1 changelog (operator directive, April 29, 2026):**

- **No manual-review acceptance gates.** Every gate must be an automated command whose exit code or output decides pass/fail. Wording like "Manual review confirmation — paste a one-paragraph statement that …" is forbidden in any Acceptance Gate, Acceptance Criteria checkbox, or Expected Output bullet. If a gate cannot be expressed as `prettier --check` / `npm run typecheck` / `npm run lint` / `npm run test:browser` / `npm run test:node` / `git grep` / `npx tsc --noEmit` / a scratch script — surface that to the user; do **not** smuggle in a manual step.
- **Closing the issue with a summary comment is part of the issue's own definition of done.** An issue is not complete until: (1) every Acceptance Criteria checkbox in the body is ticked `[x]`, (2) all changes are committed and pushed/synced to the GitHub remote, and (3) the issue is closed with a summary comment posted in the same step. If any of those three is missing, the issue is still open work.

---

## Why a Phase 8 variant exists

The general-purpose code-review template was built for **discovery-mode** findings — surface the problem, present Option A vs. Option B, let the issue-implementer decide. Phase 8 is in **execution mode**: the option analyses already happened in [P8-triage.md](../planning/phase-8/P8-triage.md), the per-finding MDs under [`docs/code-review/`](../code-review/) (017, 018, 019, 021, 022, 023, 024), and the [P8-implementation-guide](../planning/phase-8/P8-implementation-guide.md) — and the decisions are locked in [P8-contribution-goal-and-definition.md §3](../planning/phase-8/P8-contribution-goal-and-definition.md). Re-presenting Option A/B in each Phase 8 issue invites re-litigation of locked decisions, which violates the AI Operational Constraints precedence chain.

**This variant therefore:**

- Replaces "Proposed Solutions" with a single **Locked Decision** section that names the decision, names where it's locked, and forbids re-litigation in this issue.
- Adds a **Phase 8 Task** header (A1 / A2 / … / D1 / E1 / E2) that points at the [P8-ROADMAP](../planning/phase-8/P8-ROADMAP.md) row.
- Adds a **Source** field with three valid values: `Senior dev code review #2` / `CS-Go integration testing` / `Roadmap delivery task`.
- Collapses ownership verification to one line — every Phase 8 task is `Ours (CSAPI module + endpoint composition)`.
- Adds a per-task **Acceptance Gate** subsection inside Acceptance Criteria carrying the exact `git grep` / CI command from the roadmap. **Automated commands only — no manual-review gates.**
- Adds a **Definition of Done / Closing Workflow** section that codifies the three-step close: tick boxes → commit & sync → close with summary comment.
- Makes **Dependencies** mandatory and points at the roadmap's dependency graph.
- Updates the **Operational Constraints** precedence chain to insert the trio above per-finding MDs.

---

## Before Creating an Issue

1. **Confirm the task is on the Phase 8 roadmap.** Open [P8-ROADMAP.md](../planning/phase-8/P8-ROADMAP.md) and identify the task ID (A1, A2, A3, A4, B1, B2, C1, D1, E1, or E2). If the work isn't on the roadmap, **stop** — Phase 8 has a hard scope fence; new ideas become new issues filed against a future phase, not new Phase 8 tasks.
2. **Read the authoritative source.**
   - Findings 017–024 → the per-finding MD in [`docs/code-review/`](../code-review/) (search by finding number).
   - Issues #166 / #167 → the existing GitHub issue threads.
   - Delivery tasks (E1, E2) → [P8-implementation-guide.md §11](../planning/phase-8/P8-implementation-guide.md#11-two-repo-delivery-sequence).
3. **Verify the locked decision.** Confirm the decision is recorded in the per-finding MD's "Decision" section (or, for issues #166/#167, in the [P8-implementation-guide](../planning/phase-8/P8-implementation-guide.md) §5.1 / §5.2 acceptance criteria). If a "Decision" section is missing or contradicts the trio, **stop and surface the discrepancy** — do not file the issue.
4. **Check existing issues.** #166 and #167 already exist — Tasks C1 and A4 should reference them rather than duplicate.
5. **List dependencies.** Walk the [P8-ROADMAP §Roadmap Summary](../planning/phase-8/P8-ROADMAP.md#roadmap-summary) dependency rows and the per-task `Dependencies:` lines. Phase 8 tasks have explicit dependencies (A2 + B2 → D1; B2 → C1) — every issue must list them.

---

## Phase 8 Task Reference

Quick reference for filling in the **Phase 8 Task** header. See [P8-ROADMAP.md](../planning/phase-8/P8-ROADMAP.md) for full detail.

| Task   | Title                                                                    | Source                    | Authoritative MD / issue                                                                                                                                                                 |
| ------ | ------------------------------------------------------------------------ | ------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **A1** | Finding 017 — URL-builder framing in module docs                         | Senior dev code review #2 | [`docs/code-review/017`](../code-review/017-pending-p3-docs-url-builder-framing.md)                                                                                                      |
| **A2** | Finding 022 — `CSAPICollectionRef` type extraction                       | Senior dev code review #2 | [`docs/code-review/022`](../code-review/022-pending-p3-constructor-exposes-collection-info-type.md)                                                                                      |
| **A3** | Finding 023 — `availableResources: ReadonlySet<...>`                     | Senior dev code review #2 | [`docs/code-review/023`](../code-review/023-pending-p3-availableresources-set-typing.md)                                                                                                 |
| **A4** | Issue #167 — Pagination-contract JSDoc on list methods                   | CS-Go integration testing | [Issue #167](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/167)                                                                                                                  |
| **B1** | Finding 019 — `DataStream` → `Datastream` method rename                  | Senior dev code review #2 | [`docs/code-review/019`](../code-review/019-pending-p2-method-naming-datastream-vs-datastream.md)                                                                                        |
| **B2** | Finding 021 — Validators throw `EndpointError`                           | Senior dev code review #2 | [`docs/code-review/021`](../code-review/021-pending-p2-validators-throw-plain-error.md)                                                                                                  |
| **C1** | Issue #166 — Part 2 `@link` fallback in cross-ref fields                 | CS-Go integration testing | [Issue #166](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/166); [OGC 23-002 §16.1](https://docs.ogc.org/is/23-002/23-002.html)                                                  |
| **D1** | Findings 018 + 024 (coordinated) — `endpoint.csapi()` + re-privatization | Senior dev code review #2 | [`docs/code-review/018`](../code-review/018-pending-p3-endpoint-csapi-convenience-method.md) + [`docs/code-review/024`](../code-review/024-pending-p2-endpoint-root-publicly-exposed.md) |
| **E1** | Full CI gate + source-only patch generation                              | Roadmap delivery task     | [P8-implementation-guide §11 steps 2–3](../planning/phase-8/P8-implementation-guide.md#11-two-repo-delivery-sequence)                                                                    |
| **E2** | Squash onto `clean-pr` + push + PR #136 refresh                          | Roadmap delivery task     | [P8-implementation-guide §11 steps 4–8](../planning/phase-8/P8-implementation-guide.md#11-two-repo-delivery-sequence)                                                                    |

---

## Template P8: Phase 8 Task

````markdown
## Phase 8 Task

**Task ID:** {{A1 / A2 / A3 / A4 / B1 / B2 / C1 / D1 / E1 / E2}}
**Title:** {{Mirror the title from the Phase 8 Task Reference table}}
**Source:** {{Senior dev code review #2 / CS-Go integration testing / Roadmap delivery task}}
**Severity:** {{P1-Critical / P2-Important / P3-Minor / P4-Informational}}
**Category:** {{Security / Type Safety / Code Quality / API Design / Documentation / Error Handling / Server Interop / Delivery}}
**Ownership:** Ours (CSAPI module + endpoint composition)
**Phase 8 phase:** {{A — Documentation & Type-Hardening / B — API Surface Refinements / C — Server-Interop Bug Fix / D — Coordinated Structural Refactor / E — Verification & Delivery}}

---

## Goal

{{Restate the per-task acceptance criterion verbatim from the P8-ROADMAP entry. One paragraph; no Option A/B framing; no re-litigation.}}

**Acceptance criterion (from [P8-contribution-goal-and-definition.md](../planning/phase-8/P8-contribution-goal-and-definition.md)):** {{A1 / A2 / … / B2 / or "(no top-level acceptance criterion — see implementation guide §X)"}}

## Locked Decision

> **⚠️ This decision is locked. Do not re-litigate in this issue.** Surface deviations to the user; do not silently re-decide.

**Decision:** {{One paragraph stating the locked decision. Examples:

- (019) "Straight rename, no aliases, no @deprecated tags. PR #136 unmerged ⇒ no consumers ⇒ no deprecation cycle to document."
- (021) "EndpointError only; no CSAPIError subclass. The reviewer's concern was narrowability, not type-granularity; EndpointError already carries httpStatus and isCrossOriginRelated."
- (024) "Option A3: re-privatize root and getCollectionDocument; add public endpoint.csapi(id); refactor createCSAPIBuilder to value-shaped (collection, resourceUrls). Net public surface decreases by 1 method."
- (#166) "Add extractCrossReferenceId(obj, fieldName) helper supporting both @id (scalar) and @link (object with href) forms; @id wins when both present, per OGC 23-002 §16.1."
  }}

**Locked in:**

- [P8-contribution-goal-and-definition.md §3](../planning/phase-8/P8-contribution-goal-and-definition.md) — Phase 8 design rails
- [P8-implementation-guide.md §3](../planning/phase-8/P8-implementation-guide.md#3-design-principles--decisions-already-locked) — execution-level rails
- {{Per-finding MD's "Decision" section, e.g. `docs/code-review/021-...md`}}

---

## Problem Statement

{{What the reviewer / integration test found. Include the specific code, why it's problematic, and what could go wrong. Be concrete — show the incorrect / inadequate code and a scenario that demonstrates the issue.}}

**Affected code:**

```typescript
// Show the current code with file path and line reference
```
````

**Scenario / consumer-impact example:**

```typescript
// Show a concrete consumer-facing example that demonstrates the gap
```

**Impact:** {{What breaks, degrades, or becomes confusing for the consumer. For server-interop bugs, name the affected server (e.g., connected-systems-go).}}

## Files to Modify

| File                       | Action          | Est. Lines | Purpose                                     |
| -------------------------- | --------------- | ---------- | ------------------------------------------- |
| {{`path/to/file.ts`}}      | Modify          | {{~N}}     | {{Brief purpose}}                           |
| {{`path/to/file.spec.ts`}} | Modify          | {{~N}}     | {{Brief purpose}}                           |
| {{`path/to/new-file.ts`}}  | Add (if needed) | {{~N}}     | {{Brief purpose — e.g., new helper module}} |

> Cross-reference [P8-implementation-guide §X](../planning/phase-8/P8-implementation-guide.md) for the canonical files-modified list. If you find yourself adding a file that isn't in the implementation guide, **stop** — surface the question.

## Implementation Approach

{{Pull this from the implementation guide section that matches this task. Prefer linking the guide section over duplicating its content. Include only the minimum needed for an implementer to start work without bouncing between tabs.}}

**Implementation guide section:** [P8-implementation-guide §{{4.X / 5.X / 11}}]({{relative anchor}})

**Code sketch (from guide):**

```typescript
// Pull the canonical sketch from the implementation guide; do not invent a new one.
```

## Scope — What NOT to Touch

- ❌ Do NOT modify files outside the "Files to Modify" table above
- ❌ Do NOT refactor adjacent code that isn't part of this task
- ❌ Do NOT change public API signatures unless this task's locked decision specifically requires it
- ❌ Do NOT add `@deprecated` tags anywhere in Phase 8 (locked decision; PR unmerged ⇒ no consumers)
- ❌ Do NOT absorb consumer-side ergonomic helpers into the library (Phase 8 hard scope fence; #168 / #169 stay closed wontfix)
- ❌ Do NOT re-open a Phase 8 deferred finding (020, 025, 026) or a deferred CS-Go issue (#170, #171) inside this task
- ❌ {{Additional task-specific scope fences}}

## Acceptance Criteria

- [ ] {{Specific change implemented per the locked decision and implementation guide section}}
- [ ] {{Test additions / updates per the implementation guide's "Test impact" subsection}}
- [ ] All modified files pass `npx prettier --check`
- [ ] `npm run format:check` exits 0
- [ ] `npm run typecheck` exits 0
- [ ] `npm run lint` exits 0
- [ ] `npm run test:browser` exits 0
- [ ] `npm run test:node` exits 0

> **Forbidden:** Do **not** add an acceptance-criteria checkbox that requires a manual-review paragraph, a hand-written confirmation statement, or any other human-judgment artifact. Every box must resolve to a command exit code, a `git grep` line count, a test pass/fail, or a checked-in file's contents.

### Acceptance Gate (verification command)

The Phase 8 roadmap defines a **specific verification command** for each task. Paste the output of this command on the issue before closing. **The gate must be 100% automated** — no "paste a paragraph confirming X" steps; if a check cannot be automated, surface that to the user instead of inserting a manual step.

```powershell
{{Exact command from P8-ROADMAP §"Acceptance gate" for this task. Examples:
- A1 — npx prettier --check src/ogc-api/csapi/index.ts src/ogc-api/csapi/factory.ts src/ogc-api/csapi/url_builder.ts README.md; full upstream QA suite (format:check / typecheck / lint / test:browser / test:node)
- A2 — git grep -n "OgcApiCollectionInfo" -- src/ogc-api/csapi/url_builder.ts (must return 0 lines)
- A3 — npx tsc --noEmit + scratch script that attempts to mutate availableResources fails to compile
- A4 — automated JSDoc-presence check (e.g., grep for the pagination contract phrase across every list method)
- B1 — git grep -n "DataStream" -- 'src/ogc-api/csapi/' (must return 0 lines outside intentional history references)
- B2 — git grep -n "throw new Error\|throw new TypeError" -- src/ogc-api/csapi/ (must return 0 lines)
- C1 — npm run test:browser src/ogc-api/csapi/formats/part2.spec.ts
- D1 — combined: git grep "public root\|public getCollectionDocument" (0 lines), git grep "isCollectionInfo" (0 lines), new endpoint.csapi() suite green
- E1 — all five CI commands exit 0; phase-8.patch generated
- E2 — PR #136 shows new squashed commit; CI green; description updated
}}
```

**Expected output:** {{What the command must return for the gate to be green — typically "0 lines", "exit 0", or a specific test pass count. Must be checkable by reading the command output, not by reading prose.}}

## Definition of Done / Closing Workflow

> **An issue is not complete until it is closed with a summary comment.** Closing-with-comment is part of the issue's own definition of done — if you have not done all three steps below, you are not finished.

**Three-step close (in order):**

1. **Tick every Acceptance Criteria box.** Edit the issue body so every `[ ]` becomes `[x]`. The boxes are the contract; un-ticked boxes mean unfinished work, not optional work.
2. **Commit and sync.** All implementation changes are committed locally and pushed to the GitHub remote (`origin/<branch>`). The commit SHA must appear in the closing summary comment.
3. **Close with a summary comment.** Post one comment that contains, at minimum:

- The commit SHA (with a GitHub commit-link).
- The list of files modified (from the "Files to Modify" table — confirm reality matched plan).
- The acceptance-gate command output (or a tight summary: "prettier --check OK, typecheck OK, lint OK, test:node 1793/1793 passed, test:browser modulo pre-existing X").
- Any deviation from the locked decision (or `Deviation from locked decision: none.`).
- Then close the issue (`state=closed`, `state_reason=completed`).

**Forbidden shortcuts:**

- ❌ Closing the issue without a summary comment.
- ❌ Posting the summary comment but leaving the issue open.
- ❌ Ticking the boxes locally in a working file but not updating the GitHub issue body.
- ❌ Pushing the commit but not running the acceptance-gate commands (or running them but not recording the result).

## Dependencies

> **Mandatory.** Walk the [P8-ROADMAP dependency graph](../planning/phase-8/P8-ROADMAP.md#roadmap-summary) and fill in every applicable row.

**Blocked by:** {{Issue #N — Phase 8 Task X — title, or "Nothing"}}
**Blocks:** {{Issue #N — Phase 8 Task X — title, or "Nothing"}}
**Related:** {{Issue #N — title, if related but independent}}

**Roadmap dependency row:** {{Quote the relevant cell of P8-ROADMAP §Roadmap Summary, e.g. "Phase D depends on Phases A–C"}}

## References

| #   | Document                                                                                             | What It Provides                                           |
| --- | ---------------------------------------------------------------------------------------------------- | ---------------------------------------------------------- |
| 1   | [P8-contribution-goal-and-definition.md](../planning/phase-8/P8-contribution-goal-and-definition.md) | Phase 8 goal, scope, acceptance criteria, locked decisions |
| 2   | [P8-implementation-guide.md](../planning/phase-8/P8-implementation-guide.md)                         | Authoritative execution-level guide (this task: §{{X}})    |
| 3   | [P8-ROADMAP.md](../planning/phase-8/P8-ROADMAP.md)                                                   | Task ordering, dependencies, acceptance gates              |
| 4   | {{Per-finding MD or GitHub issue link}}                                                              | Authoritative "why" for this finding                       |
| 5   | {{Affected source file with line reference}}                                                         | Code to modify                                             |
| 6   | {{OGC spec section if applicable, e.g. OGC 23-002 §16.1 for #166}}                                   | Spec authority                                             |
| 7   | {{Related existing pattern in codebase — e.g., EDR's endpoint.edr() for D1}}                         | Blueprint                                                  |

```

---

## Template Usage Notes

### Severity Levels (same as v1.0)

| Level | Meaning | Examples |
|-------|---------|---------|
| **P1-Critical** | Spec non-conformance; consumer interop blocker | #166 (OGC 23-002 §16.1 fallback) |
| **P2-Important** | API contract / type safety / error contract gap | 019 (rename), 021 (error type), 024 (re-privatization) |
| **P3-Minor** | Maintainability / typing tightening / docs gap | 017, 022, 023, 018 (convenience method), #167 |
| **P4-Informational** | Roadmap-only delivery task | E1, E2 |

### Categories — additions for Phase 8

In addition to the v1.0 categories (`Security` / `Type Safety` / `Code Quality` / `API Design` / `Documentation` / `Error Handling`), Phase 8 adds:

| Category | When to Use |
|---------|-------------|
| `Server Interop` | Bug found via integration testing against a known-good server (#166, #167) |
| `Delivery` | E1, E2 — no source change, pure delivery / verification |

### Labels — Phase 8

Apply these labels consistently to every Phase 8 issue:

| Label | When to Use |
|-------|-------------|
| `phase-8` | **Every Phase 8 issue.** Mandatory. |
| `code-review` | Tasks A1, A2, A3, B1, B2, D1 (senior-dev review findings) |
| `server-interop` | Tasks A4, C1 (CS-Go integration findings) |
| `delivery` | Tasks E1, E2 |
| `type-safety` | Findings 022, 023 |
| `api-design` | Findings 017, 018, 019, 022, 024 |
| `error-handling` | Finding 021 |
| `documentation` | Finding 017, Issue #167 |
| `bug` | Issue #166 |
| `coordinated` | Task D1 (findings 018 + 024 must execute as one indivisible unit) |
| `locked-decision` | **Every Phase 8 issue.** Mandatory. Signals the issue carries a locked decision and re-litigation is out of scope. |

### Re-litigation Policy

If, while implementing a Phase 8 issue, an instinct arises to revisit the locked decision (e.g., "what if we add deprecated aliases just to be safe?"), **stop**. The Phase 8 trio is the contract. Surface the concern to the user; do not silently re-decide. The "Locked Decision" section of this template exists to make that boundary unmistakable.

### No-Manual-Gate Policy

Every acceptance gate must be **automated** — a command whose exit code, output line-count, or test result decides pass/fail without human reading. Phrases that signal a manual gate has crept in (and must be removed before the issue is filed):

- "Manual review confirmation — paste a one-paragraph statement that …"
- "Confirm by reading the file that …"
- "Paragraph affirmatively states …"
- "Reviewer-attested paragraph …"

If a property genuinely cannot be checked by a command (rare; usually means the gate is mis-specified), surface it to the user before filing the issue. **Do not** ship an issue containing a manual gate; the operator has explicitly rejected manual-review steps as a matter of standing policy.

### Closing-with-Comment Policy

The issue's last step is **always** a summary comment immediately followed by closing the issue. This step is part of the issue's own definition of done — not a courtesy, not optional, not separately tracked. An issue with all boxes ticked and the commit pushed but no closing comment is **still open work**. See the "Definition of Done / Closing Workflow" section of the template for the required comment contents.

### Coordinated Tasks (D1)

Findings 018 and 024 must execute as **one indivisible unit** — splitting them re-introduces the unsound `isCollectionInfo` runtime cast. The single Task D1 issue covers both findings; do not file separate issues for 018 and 024.

### Deferred-Finding Sentries

Each Phase 8 issue's "Scope — What NOT to Touch" section explicitly fences off the deferred Phase 8 findings (020, 025, 026) and the deferred CS-Go issues (#170, #171). If a Phase 8 task starts trying to fix one of those, the issue is being mis-scoped — stop and surface.

---

## Operational Constraints (Phase 8 specific)

> **⚠️ MANDATORY:** Before starting work on any Phase 8 issue, review [`docs/governance/AI_OPERATIONAL_CONSTRAINTS.md`](AI_OPERATIONAL_CONSTRAINTS.md).

**Phase 8 precedence chain (replaces the v1.0 chain):**

```

OGC specifications
→ AI Collaboration Agreement
→ P8-contribution-goal-and-definition.md
→ P8-implementation-guide.md
→ P8-ROADMAP.md
→ This issue description
→ Per-finding MD under docs/code-review/
→ Existing code
→ Conversational context

```

**Phase 8 execution rails (every issue inherits these):**

- **No scope expansion.** Fix the task, nothing more. New ideas become new issues filed against a future phase.
- **Minimal diffs.** Smallest change that satisfies the per-task acceptance gate.
- **Locked decisions stay locked.** Surface deviations; do not silently re-decide.
- **No `@deprecated` tags.** Phase 8 ships zero deprecation aliases (PR unmerged, no consumers).
- **No cross-task scope creep.** Each issue's diff stays within its own "Files to Modify" table.
- **Two-repo workflow respected.** Source changes land on `phase-8` first; `clean-pr` is delivery-only (Tasks E1+E2).
- **Wontfix decisions stay closed.** #168 and #169 are not reopened without explicit user direction.
- **Deferred findings stay deferred.** 020, 025, 026, #170, #171 are out of Phase 8 scope; do not absorb mid-execution.

---

## Relationship to Other Templates

| Template | File | Use When |
|---------|------|---------|
| **Phase 8 (this template)** | `issue-creation-prompt-template-phase-8.md` | **Every Phase 8 task (A1–E2). Default for any issue tied to the P8-ROADMAP.** |
| Code Review (general purpose) | [`issue-creation-prompt-template-code-review.md`](issue-creation-prompt-template-code-review.md) | Findings discovered outside any phase; use after Phase 8 closes if a future review surfaces new findings |
| Phase 6 ROADMAP / Verification | `issue-creation-prompt-template-phase-6.md` | Historical — Phase 6 retrospective only |
| Phase 5 Parsers | `issue-creation-prompt-template-phase-5.md` | Historical — Phase 5 retrospective only |

---

## Phase 8 Issue Filing Checklist

Before submitting a Phase 8 issue, confirm:

- [ ] Task ID matches a row in [P8-ROADMAP](../planning/phase-8/P8-ROADMAP.md) (A1 through E2)
- [ ] Source field is one of the three valid values (`Senior dev code review #2` / `CS-Go integration testing` / `Roadmap delivery task`)
- [ ] Locked Decision section names the decision and links the lock-in source
- [ ] Files to Modify table matches the implementation guide's files-modified list for this task
- [ ] Acceptance Gate command is the exact command from P8-ROADMAP for this task **and is 100% automated** (zero manual-review steps)
- [ ] No Acceptance Criteria checkbox requires a manual-review paragraph or human-judgment artifact
- [ ] **Definition of Done / Closing Workflow** section is present and unmodified — three-step close (tick boxes → commit & sync → close with summary comment) is intact
- [ ] Dependencies section walks the roadmap dependency graph (especially A2 + B2 → D1)
- [ ] Labels include both `phase-8` and `locked-decision` at minimum
- [ ] References table includes the trio (P8-contribution-goal-and-definition / P8-implementation-guide / P8-ROADMAP) plus the per-finding MD or issue
- [ ] Scope fences include the deferred-finding sentries
- [ ] Issue title format: `Phase 8 / Task {{ID}}: {{Title}}` (e.g., `Phase 8 / Task A1: Finding 017 — URL-builder framing in module docs`)
```
