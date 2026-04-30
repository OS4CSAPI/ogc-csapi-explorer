# Issue Creation Prompt Template — Code Review

**Purpose:** Reusable template for creating GitHub issues from external code review findings. Designed for findings that fall outside the original ROADMAP phases — discovered by human reviewers or automated analysis tools after the implementation was considered complete. Every issue produced from this template acts as an AI scope-containment boundary.

**Usage:** Copy the template below, fill in the placeholders (marked with `{{...}}`), and create the issue via the GitHub API or UI.

**Version:** 1.0
**Date:** March 6, 2026
**Complements:** `issue-creation-prompt-template-phase-6.md` (v4.0) — use that template for planned ROADMAP tasks and verification gate failures. Use _this_ template for post-implementation code review findings.

---

## Before Creating an Issue

1. **Verify ownership** — Determine whether the finding is in code we wrote or pre-existing upstream code:
   - Run `git diff upstream/main clean-fork/clean-pr -- <file>` and check if the affected lines appear in our diff
   - If the lines are **not in our diff**, the finding is **upstream** (pre-existing in camptocamp/ogc-client)
   - If the lines **are in our diff**, the finding is **ours**
   - If our changes interact with upstream code to produce the issue, it is **shared**
2. **Determine the destination repo:**
   - **Ours:** File on `OS4CSAPI/ogc-client-CSAPI_2`
   - **Upstream:** File on `OS4CSAPI/ogc-client-CSAPI_2` as a tracking item with label `upstream`. Do NOT file directly on `camptocamp/ogc-client` without maintainer relationship context.
   - **Shared:** File on `OS4CSAPI/ogc-client-CSAPI_2`
3. **Check for duplicates** — Search existing issues to confirm no duplicate already tracks this work
4. **Read the finding source** — Review the full code review report or analysis output that produced the finding
5. **Identify the exact files** — List every file that would need to change to resolve the finding

---

## Template C: Code Review Finding

````markdown
## Finding

{{One-sentence summary. Example: "Path traversal via unencoded itemId in getCollectionItem" or "parseCollectionResponse<T> casts raw JSON to T[] without validation."}}

**Review Source:** {{Who or what produced this finding — e.g., "Senior developer code review of clean-pr" or "Security analysis agent"}}
**Severity:** {{P1-Critical / P2-Important / P3-Minor / P4-Informational}}
**Category:** {{Security / Type Safety / Code Quality / API Design / Documentation / Error Handling}}
**Ownership:** {{Ours / Upstream / Shared}}

---

## Problem Statement

{{What the reviewer found. Include the specific code, why it's problematic, and what could go wrong. Be concrete — show the vulnerable or incorrect code and a scenario that demonstrates the issue.}}

**Affected code:**

```typescript
// Show the problematic code with file path and line reference
```
````

**Scenario:**

```typescript
// Show a concrete example that demonstrates the problem
```

**Impact:** {{What breaks, degrades, or becomes exploitable. Which consumers or callers are affected?}}

## Ownership Verification

{{Paste the evidence from the diff check. This section exists to prevent filing issues against our code for pre-existing upstream problems, and vice versa.}}

```
$ git diff upstream/main clean-fork/clean-pr -- <file> | grep -A3 -B3 "<pattern>"
{{Paste the output, or state "No matches — line is not in our diff"}}
```

**Conclusion:** {{This code is ours / This code is pre-existing upstream / This is a shared concern because...}}

## Files to Modify

| File                       | Action | Est. Lines | Purpose           |
| -------------------------- | ------ | ---------- | ----------------- |
| {{`path/to/file.ts`}}      | Modify | {{~N}}     | {{Brief purpose}} |
| {{`path/to/file.spec.ts`}} | Modify | {{~N}}     | {{Brief purpose}} |

## Proposed Solutions

### Option A: {{Short label}} (Recommended)

```typescript
// Show the fix
```

**Pros:** {{...}}
**Cons:** {{...}}
**Effort:** {{Small / Medium / Large}} | **Risk:** {{None / Low / Medium / Breaking}}

### Option B: {{Short label}}

```typescript
// Show the alternative
```

**Pros:** {{...}}
**Cons:** {{...}}
**Effort:** {{Small / Medium / Large}} | **Risk:** {{None / Low / Medium / Breaking}}

## Scope — What NOT to Touch

- ❌ Do NOT modify files outside the "Files to Modify" table above
- ❌ Do NOT refactor adjacent code that isn't part of this finding
- ❌ Do NOT change public API signatures unless the finding specifically requires it
- ❌ {{Additional scope fences specific to this finding}}

## Acceptance Criteria

- [ ] {{Specific fix implemented — describe the concrete change}}
- [ ] {{Negative test — the problematic scenario no longer produces the bad outcome}}
- [ ] Existing tests still pass (`npm test`)
- [ ] No lint errors (`npm run lint`)
- [ ] All modified files pass `npx prettier --check`
- [ ] {{Any finding-specific verification step}}

## Dependencies

**Blocked by:** {{Issue #N — title, or "Nothing"}}
**Blocks:** {{Issue #N — title, or "Nothing"}}
**Related:** {{Issue #N — title, if findings are related but independent}}

---

## Operational Constraints

> **⚠️ MANDATORY:** Before starting work on this issue, review [`docs/governance/AI_OPERATIONAL_CONSTRAINTS.md`](AI_OPERATIONAL_CONSTRAINTS.md).

Key constraints:

- **Precedence:** OGC specifications → AI Collaboration Agreement → This issue description → Existing code → Conversational context
- **No scope expansion:** Fix the finding, nothing more
- **Minimal diffs:** Prefer the smallest change that satisfies the acceptance criteria
- **Ask when unclear:** If intent is ambiguous, stop and ask for clarification
- **Respect ownership:** If the finding is upstream, track it but do not modify upstream code unilaterally

### Ownership-Specific Constraints

**If Ours:**

- Fix on the `phase-6` branch (or the current working branch)
- Include in the next commit to `clean-pr` if the PR is still open
- Add tests that cover the finding

**If Upstream:**

- Do NOT modify the upstream code in our PR — it changes code we didn't write
- Track the issue for potential future contribution or discussion with the maintainer
- If the fix is trivial and clearly beneficial, note in the issue that it could be offered as a separate upstream PR

**If Shared:**

- Fix only the parts that are in our code
- Document the upstream component as a known limitation

---

## References

| #   | Document                                     | What It Provides                   |
| --- | -------------------------------------------- | ---------------------------------- |
| 1   | {{Code review report or analysis output}}    | Original finding with full context |
| 2   | {{Affected source file with line reference}} | Code to modify                     |
| 3   | {{OGC spec or MDN reference if applicable}}  | Spec-correct behavior              |
| 4   | {{Related existing pattern in codebase}}     | Blueprint for the fix              |

```

---

## Template Usage Notes

### Severity Levels

| Level | Meaning | Examples |
|-------|---------|---------|
| **P1-Critical** | Security vulnerability or data corruption risk | Path traversal, injection, unchecked casts at trust boundaries |
| **P2-Important** | Type safety gap or API contract violation that could cause runtime errors | Generic type lies, missing validation at boundaries, incorrect error types |
| **P3-Minor** | Code quality issue that reduces maintainability but doesn't cause runtime errors | Inconsistent patterns, missing JSDoc, unclear naming |
| **P4-Informational** | Style preference or minor improvement opportunity | Alternative approach suggestions, documentation enhancements |

### Categories

| Category | When to Use |
|----------|------------|
| `Security` | Input validation, encoding, injection, traversal, auth |
| `Type Safety` | Unchecked casts, generic lies, missing validation at type boundaries |
| `Code Quality` | Patterns, consistency, maintainability, dead code |
| `API Design` | Public interface clarity, breaking changes, naming |
| `Documentation` | Missing or incorrect JSDoc, README, inline comments |
| `Error Handling` | Missing catch, incorrect error types, swallowed errors |

### Labels

Apply these labels consistently:

| Label | When to Use |
|-------|------------|
| `code-review` | All issues from this template |
| `security` | Security category findings |
| `type-safety` | Type Safety category findings |
| `code-quality` | Code Quality category findings |
| `upstream` | Findings in pre-existing upstream code (not our changes) |
| `post-phase-6` | All findings from post-Phase 6 review |
| `bug` | Findings that represent actual incorrect behavior |
| `enhancement` | Findings that represent improvements to working code |

### Ownership Decision Tree

```

Is the affected code in our diff (git diff upstream/main clean-fork/clean-pr)?
├── YES → Ownership: Ours
│ Action: Fix it. Include in clean-pr if PR is open.
├── NO → Ownership: Upstream
│ Action: Track it. Do NOT modify in our PR.
└── PARTIALLY → Ownership: Shared
Action: Fix our part. Document the upstream part.

```

### Batching Related Findings

If multiple findings affect the same file or function, consider whether they should be:
- **One issue** — if fixing one naturally fixes the others (e.g., two encoding issues in the same method)
- **Separate issues** — if they can be fixed independently and have different severity/ownership (default)

When in doubt, keep them separate. It's easier to close two issues than to track partial completion of one.

---

## Relationship to Other Templates

| Template | File | Use When |
|----------|------|----------|
| Phase 6 ROADMAP / Verification | `issue-creation-prompt-template-phase-6.md` | Planned tasks or verification gate failures |
| Phase 5 Parsers | `issue-creation-prompt-template-phase-5.md` | Parser implementation tasks |
| **Code Review (this template)** | `issue-creation-prompt-template-code-review.md` | Post-implementation findings from human or automated review |
```
