# Scope Alignment Review Notes

> **Date:** 2026-02-23
> **Context:** Review of all 8 research plans against jahow's actual PR #136 acceptance requirements
> **Outcome:** Research scope validated with refinements; implementation scope gates added

---

## Part 1: Initial Assessment — Plans vs. jahow's Actual Requirements

### jahow's Exact Words (PR #136, the ONLY acceptance requirements issued)

**Comment 1:**

> "I would request one major thing: that all things related to the CS API not be part of the main `index.ts` file, but instead imported through `@camptocamp/ogc-client/csapi`. Basically I want to make sure that anyone using the library as before do not end up with all this code in their bundle overnight."
>
> "This means that:
>
> - anything part of the `src/ogc-api/csapi` should not be included in the root `index.ts` file.
> - anything not part of the `src/ogc-api/csapi` should not import things from the CSAPI code at all
>
> (unless we find a better way to handle tree-shaking).
>
> I'm going to review the changes to the existing code and give you a more thorough feedback."

**Comment 2:**

> "could you please give me a rough time frame for when this would be ready? I'd really like to do a 2.0 release for the library soon"

That is **everything**. Two bullet points plus a timeline question.

### What jahow's requirements actually require us to do

| #      | Concrete Task                                                          | Derived From                                                     |
| ------ | ---------------------------------------------------------------------- | ---------------------------------------------------------------- |
| **T1** | Remove ~184 lines of CSAPI exports from `src/index.ts`                 | "anything part of csapi should not be included in root index.ts" |
| **T2** | Create `src/ogc-api/csapi/index.ts` barrel file                        | "imported through `@camptocamp/ogc-client/csapi`"                |
| **T3** | Add `"./csapi"` to `package.json` `"exports"`                          | "imported through `@camptocamp/ogc-client/csapi`"                |
| **T4** | Remove CSAPI imports from `endpoint.ts` (lines 52-53)                  | "anything not part of csapi should not import things from CSAPI" |
| **T5** | Handle the `csapi()` method, `hasConnectedSystems`, `csapiCollections` | Consequence of T4 — these currently import/use CSAPI code        |
| **T6** | Handle CSAPI tests in `endpoint.spec.ts`                               | Consequence of T4/T5                                             |
| **T7** | Ensure CI passes                                                       | Implicit — PR shows "0/1 checks OK"                              |
| **T8** | Respond with timeline                                                  | "could you give me a rough time frame"                           |

Items T1-T3 are mechanical packaging tasks. T4 is directly required. T5 is the only real design decision. T6-T7 are quality gates. T8 is communication.

### Plan-by-Plan Scope Assessment

#### Plan 01: Build System and Entry Point Analysis — 31 questions

**Alignment: GOOD — directly serves T2/T3**

All questions target how to add the `./csapi` entry point. The build pipeline analysis, `package.json` exports configuration, and TypeScript declaration questions directly support the requirement. The only concern is volume — 31 questions for "add an exports field and a barrel file" is thorough but not wasteful since getting it wrong would break consumers.

**Scope creep items: None identified.** This plan stays focused.

#### Plan 02: EDR Integration Pattern Analysis — 35 questions

**Alignment: PARTIAL — useful context but exceeds requirements**

jahow pointed to EDR (PR #114) in issue #118 as a _reference for how to contribute_, not as an architectural requirement. He never said "analyze EDR" or "compare EDR to CSAPI." The EDR comparison is informative background, but 35 questions of deep analysis goes well beyond what's needed.

**Scope creep items:**

- Q30: "What exactly makes the EDR integration acceptable to the maintainer?" — **Speculative.** jahow didn't explain his reasoning in those terms. We're inferring.
- Q31: "At what point would EDR need the same treatment as CSAPI?" — **Out of scope.** jahow didn't ask us to assess EDR. This is not our concern.
- Q32-35: "Architectural boundary analysis" — **Theoretical.** jahow gave two concrete bullet points, not an abstract architectural philosophy for us to reverse-engineer.
- The entire "Scale Comparison" section (Q17-Q23) — While interesting, jahow's requirement is binary: CSAPI not in root, non-CSAPI doesn't import CSAPI. The scale comparison doesn't change what we need to do.

**Risk:** This plan could produce findings that induce us to "fix" EDR too, or design an overly theoretical framework for something that's practically straightforward.

#### Plan 03: Separate Entry Point Design Patterns — 35 questions

**Alignment: GOOD but OVER-RESEARCHED**

The core question — how to configure `"./csapi"` in `package.json` — is directly required. But studying Angular, RxJS, AWS SDK, date-fns, and zod's packaging strategies (Q1-Q8, the "Library Case Studies" section) is disproportionate. Node.js documentation clearly specifies how `"exports"` works. The `typesVersions` fallback questions (Q8, Q27) and extensive bundler compatibility analysis (Q30-Q35) go beyond the immediate need.

**Scope creep items:**

- Q7: "what is the typical number of sub-path exports?" — Irrelevant. We have one.
- Q15: "Can we use wildcard/glob sub-path patterns?" — We don't need wildcards for one sub-path.
- Q27: "Do we need `typesVersions` for older TypeScript?" — Not a jahow requirement. Upstream doesn't use it.
- Q34: "When a consumer imports from both root and sub-path, do bundlers create two separate module instances?" — Interesting edge case, but speculative product-level concern, not a PR acceptance gate.

#### Plan 04: TypeScript Sub-Module API Design Patterns — 38 questions

**Alignment: SCOPE CREEP RISK if findings drive over-engineering**

This plan studies **5+ industry libraries** (AWS SDK v3, Octokit, Angular CDK, RxJS, date-fns, lodash-es, zod) to determine "what consumers should actually type when they use CSAPI." jahow did **not** ask us to redesign the consumer API. He asked us to move CSAPI out of `index.ts` and stop non-CSAPI code from importing CSAPI.

The consumer API _will_ change as a consequence of removing `endpoint.csapi()` (because that method imports CSAPI code), but studying 7 libraries across 38 questions to design the replacement is vastly disproportionate to the scope of the change.

**Scope creep items:**

- The entire AWS SDK section (Q1-Q6) — Studying a multi-package monorepo architecture for a single barrel file addition
- The Octokit plugin section (Q7-Q12) — Plugin architectures are explicitly excluded by our own boundary conditions
- The Angular CDK section (Q13-Q17) — Angular's DI framework is irrelevant to our pure ESM package
- Q22: "How applicable are stateless utility patterns to our use case? CSAPI is stateful." — Deep design territory, not a PR acceptance concern
- Q31-Q38: "Cross-Cutting Synthesis" — Writing an academic pattern catalog is not required to meet jahow's two bullet points

**Risk:** This plan could push us toward an over-engineered consumer API when a simple `createCSAPIClient(endpoint)` function would suffice.

#### Plan 05: Module Decoupling Patterns in TypeScript — 37 questions

**Alignment: SCOPE CREEP RISK if findings drive over-engineering**

This plan invokes Martin Fowler's refactoring catalog, dependency inversion principles, 4 coupling levels with decision matrices, the "Hollywood Principle," structural typing theory, and `import type` strategies. This is advanced software architecture theory applied to what is, from jahow's perspective: "don't import CSAPI from endpoint.ts."

**Scope creep items:**

- Q1: "How does TypeScript's structural type system affect adapter and dependency inversion patterns compared to nominal type systems (Java, C#)?" — **Academic.** Not relevant to meeting jahow's requirements.
- Q3-Q4: Adapter pattern examples, Java/C# comparison — **Theoretical.** We're removing 2 import lines from endpoint.ts and moving a method.
- Q8-Q13: Dependency inversion section — **Over-engineered.** DIP is a valid concept but we don't need a DI container or formal inversion to stop importing 2 files.
- Q14-Q21: 4 coupling levels with decision matrix — **Over-engineered.** Our code already uses `Pick<OgcApiCollectionInfo, ...>` — the coupling level effectively exists. Re-evaluating 4 coupling levels with tradeoff matrices for a simple module extraction is disproportionate.
- Q28-Q32: Module extraction case studies — Useful but the "documented case studies" search scope exceeds what's needed for our concrete, well-defined task.

**Risk:** This plan could lead us to introduce unnecessary abstraction layers (adapter interfaces, factory patterns, data records) when the simplest solution is: move the method to CSAPI, accept the endpoint instance, done.

#### Plan 06: Endpoint Decoupling Architecture — 44 questions

**Alignment: CORE WORK — but over-specified from Plans 04/05 inputs**

This IS the necessary design work. Removing `endpoint.csapi()`, deciding what happens to `hasConnectedSystems` and `csapiCollections`, and creating the barrel file are all directly required. The 44 questions are thorough and the plan is the right scope.

However, it's designed to synthesize Plans 04 and 05, which carry scope creep risk. If Plan 04 produces a 7-library pattern catalog and Plan 05 produces a 4-level coupling decision matrix, Plan 06 will spend significant effort synthesizing inputs that don't need to exist.

**Scope creep items (minor):**

- Q14: "How does the recommended pattern affect the `app/examples/edr.ts` demo?" — The demo app is in our dev fork, not upstream. Not a PR acceptance concern.
- Q38: "After test migration, what is the test coverage for the CSAPI module boundary?" — Test coverage metrics aren't a jahow requirement.

**These are minor.** Plan 06's core questions are well-aligned.

#### Plan 07: Prettier and ESLint Configuration Analysis — 38 questions

**Alignment: GOOD — directly serves T7 (CI compliance)**

CI must pass. Understanding formatting and linting rules is necessary. The plan is thorough but focused on the right problem.

**Scope creep items (minor):**

- Q14: "eslint-plugin-require-extensions is installed but NOT configured. Why?" — Not our concern; it's upstream's decision.
- Q37: "Will jahow prefer seeing formatting changes isolated or interleaved?" — Speculative about reviewer preference.

**These are minor.** Plan 07 is well-aligned overall.

#### Plan 08: File-Level Changelist and Commit Strategy — 40 questions

**Alignment: GOOD — directly produces the implementation spec**

This is the practical synthesis. The file changelist, commit sequence, and verification checklist are all directly needed.

**Scope creep items (minor):**

- Q28: "Should we update the PR from Draft to Ready for Review?" — Process decision, not a code change.
- Q39: "Should a MIGRATION.md or BREAKING-CHANGES.md be created?" — CSAPI was never released. No migration needed.
- Q36: "Should the litmus test be automated as a CI step?" — Over-engineering. A one-time check suffices.

### Summary: Scope Creep Risk Matrix

| Plan   | Questions | Alignment | Scope Creep Risk | Excess Questions                                     |
| ------ | --------- | --------- | ---------------- | ---------------------------------------------------- |
| 01     | 31        | **GOOD**  | Low              | ~0                                                   |
| 02     | 35        | Partial   | **Medium**       | ~10 (arch. boundary theorizing)                      |
| 03     | 35        | Good      | Low-Medium       | ~6 (library case studies, edge cases)                |
| **04** | **38**    | **Risk**  | **HIGH**         | **~30 (5+ library studies for one design decision)** |
| **05** | **37**    | **Risk**  | **HIGH**         | **~25 (decoupling theory, DIP, Martin Fowler)**      |
| 06     | 44        | Good      | Low              | ~3                                                   |
| 07     | 38        | Good      | Low              | ~3                                                   |
| 08     | 40        | Good      | Low              | ~4                                                   |

**Total questions: 298. Questions directly serving jahow's requirements: ~220. Excess: ~80.**

### What jahow explicitly left open

He said **"(unless we find a better way to handle tree-shaking)"** — this alternative has not been explored by any plan. Modern bundlers with ESM tree-shaking might make the separate entry point unnecessary. While the separate entry point is likely still preferred, the fact that he offered this alternative suggests his requirements are more flexible than our strategy assumes.

He also said **"I'm going to review the changes to the existing code and give you a more thorough feedback"** — meaning more requirements may be coming. Building 298 questions of research infrastructure before his detailed review carries the risk that new feedback invalidates prior research.

---

## Part 2: Revised Assessment — After Scope Clarification

### The Clarification

The intent was never to expand implementation scope — it was to **research broadly to make the best design choices** for meeting jahow's requirements. The distinction:

- **Research scope** (broad) — Study industry best practices to make _informed_ design decisions. This is prudent engineering.
- **Implementation scope** (narrow) — Only deliver what jahow requires. No gold-plating.

### Revised Plan Assessment

**Plans 04 and 05 are correctly scoped as research.** Studying how AWS SDK, Octokit, Angular CDK, etc. handle sub-module APIs gives us evidence-based confidence in whichever pattern we choose. Studying coupling levels ensures we pick the right abstraction rather than guessing. The risk isn't the research — it's what we _do_ with the findings.

**The actual scope creep risk is downstream in Plans 06 and 08**, if research findings get translated into implementation work that exceeds jahow's requirements. For example:

- If Plan 04 finds that AWS SDK uses a formal adapter layer, and Plan 06 then _implements_ an adapter layer — that's scope creep. jahow didn't ask for an adapter.
- If Plan 05 finds that data-record coupling is theoretically superior, and Plan 06 then refactors `CSAPIQueryBuilder`'s constructor to accept a new data record type instead of just relocating the existing code — that's scope creep.

The guard rail needed is: **research broadly, implement minimally.** Use the best practice findings to _validate_ that our chosen approach is sound, not to _expand_ what we build.

### What Actually Changes

**Plans 01-05, 07:** No changes needed to research questions. They inform good decision-making.

**Plan 06 needs a scope gate:** "For every design decision, apply the minimum-change test: does this change serve jahow's two bullet points, or are we adding work he didn't request?" Currently Plan 06 has a boundary condition verification checklist (the 4 constraints), but no **implementation scope** check.

**Plan 08 needs a scope gate:** A verification that the changelist only contains changes required by jahow's feedback — no "while we're at it" improvements.

**Research strategy needs a scope gate:** A top-level principle documenting the "research broadly, implement minimally" philosophy.

### Remaining Concerns (Smaller)

**Plan 02, Q31:** "At what point would EDR need the same treatment as CSAPI?" — This is still out of scope. EDR is not our module to refactor, and suggesting EDR changes to jahow would be overstepping. The question is fine as _context_ but the findings must not produce action items.

**"Rule 4" (one-way dependency):** Our strategy calls this "jahow's Four Rules" but he gave two bullet points, not four. Rule 4 ("one-way dependency: core must not depend on CSAPI code") is a reasonable _inference_ from his words, but we should be clear it's our inference, not his requirement. If during implementation we find that a small, clean `import type` from core → CSAPI would make the architecture simpler, we shouldn't rule it out dogmatically — we should ask jahow.

**"unless we find a better way to handle tree-shaking":** He explicitly offered this alternative. None of our plans explore it. Plan 01 or Plan 03 could include a brief question: "Does ESM tree-shaking with modern bundlers already prevent CSAPI from entering consumer bundles when unused, making the separate entry point unnecessary?" If the answer is yes, that's a simpler solution jahow explicitly said he'd accept.

### Bottom Line

The research rigor is an asset, not a liability. The plans are well-designed to produce informed decisions. The only adjustment needed is ensuring Plans 06 and 08 have explicit scope gates that say: "We researched broadly to make the best choice, but we implement only what jahow requires."
