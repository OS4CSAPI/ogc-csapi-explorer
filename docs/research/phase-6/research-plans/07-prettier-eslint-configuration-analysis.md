# Research Plan 07: Prettier and ESLint Configuration Analysis

> **Plan 7 of 8** | **Phase 6 — Upstream Acceptance Refactoring**

---

## Metadata

| Field                  | Value                                                     |
| ---------------------- | --------------------------------------------------------- |
| **Status**             | Not Started                                               |
| **Plan Type**          | Mechanical analysis                                       |
| **Date Created**       | 2026-02-23                                                |
| **Last Updated**       | 2026-02-23                                                |
| **Estimated Time**     | 1–2 hours                                                 |
| **Actual Time**        | —                                                         |
| **Depends On**         | None                                                      |
| **Blocks**             | Plan 08 (File-Level Changelist and Commit Strategy)       |
| **Strategy Reference** | [research-strategy.md § Plan 07](../research-strategy.md) |

---

## 1. Research Objective

Produce a complete formatting and linting impact assessment that documents: (a) every Prettier and ESLint rule configured in upstream's toolchain, including how each rule's default interacts with the explicit configuration, (b) the exact set of changes Prettier will apply to our CSAPI files across all 27 source files and 29 test files, (c) every ESLint error or warning our code will trigger, (d) the interaction between `eslint-plugin-import`, `typescript-eslint`, and our import patterns, (e) the role of the installed-but-inactive `eslint-plugin-require-extensions` package, and (f) a recommended execution order for formatting and linting relative to the architectural refactoring (Plan 06).

The key output is a **file-by-file impact matrix** that Plan 08 can consume directly to determine whether formatting changes should be a separate commit, interleaved with architectural changes, or applied as a final pass.

This plan is mechanical — it runs tools and documents results rather than making design decisions. However, the findings are critical because a single Prettier or ESLint failure will block CI, and understanding the _scope_ of changes is essential for commit strategy. If Prettier reformats 2,000 lines across 56 files, that affects the diff readability of the PR and may need to be isolated in its own commit. If ESLint flags real code issues (not just formatting), those must be addressed as part of the refactoring.

---

## 2. Sequencing Rationale

### Why Plan 7?

This plan is positioned late in the sequence because its findings are purely mechanical — they don't inform architectural decisions (that's Plans 02–06) and they don't depend on any prior research. However, Plan 08 (File-Level Changelist and Commit Strategy) must know the formatting/linting impact to design the commit sequence. Specifically:

- If Prettier changes are extensive (many files, many lines), Plan 08 may recommend a dedicated "format only" commit before or after the architectural changes, to keep the refactoring diff clean.
- If ESLint flags real code issues (unused variables, type errors, import order violations), those must be tracked as additional changes in the changelist.
- The `typescript-eslint/recommended` ruleset includes rules beyond formatting that may interact with the architectural changes (e.g., `no-unused-vars` will flag variables that become unused after removing the `csapi()` method from endpoint, or `import/extensions` may require attention when creating the new barrel file).

### Dependency Chain

- **Builds on:** Nothing — this is independent mechanical analysis. However, it benefits from understanding which files will be created/modified by the architectural refactoring (Plan 06), so running it after Plan 06 is designed (but before Plan 08) is ideal.
- **Feeds into:**
  - **Plan 08** (File-Level Changelist and Commit Strategy): Needs the formatting/linting impact to determine: (1) whether a dedicated formatting commit is needed, (2) which files have formatting-only changes vs code+formatting changes, (3) whether the commit sequence should be "refactor then format" or "format then refactor" or "atomic commits with formatting included", (4) what the PR diff will look like to reviewers.

---

## 3. Boundary Conditions

### Non-Negotiable Constraints

1. **CI compliance (Constraint 5):** All code must pass `npm run format:check` (Prettier), `npm run lint` (ESLint), and `npm run typecheck` (TypeScript). These are hard gates in the upstream CI pipeline (`qa.yml`). A single failure blocks the PR.
2. **Upstream configuration is authoritative:** We do NOT modify `.prettierrc.json`, `eslint.config.js`, or any linting/formatting configuration. Our code conforms to upstream's rules, not the reverse. The upstream configuration is fixed — the only variable is our code.
3. **No CSAPI in root exports (Constraint 1):** When evaluating ESLint impact on `src/index.ts`, the analysis must account for the removal of ~170 lines of CSAPI exports. ESLint's `no-unused-vars` and `import/extensions` will behave differently on the post-refactoring `index.ts`.
4. **New files must also comply:** Any new files created by the refactoring (e.g., `src/ogc-api/csapi/index.ts` barrel file, potential factory files) must be written to comply with Prettier and ESLint from the start.

### Excluded From Scope

- **Modifying upstream's formatting or linting configuration:** We use upstream's rules as-is. If a rule is overly strict or causes problems, we document it but do not propose changing it.
- **Formatting/linting of non-CSAPI files:** While `npm run format:check` and `npm run lint` run against the entire repository, this plan focuses on files we own or modify. Upstream files that are already formatted/linted correctly are not our concern.
- **Architecture decisions informed by linting:** Linting doesn't determine architecture — Plan 06 does. If ESLint flags something in our architectural design, we adapt our code to the rule, not the architecture to the linter.
- **IDE-specific formatting configuration:** `.editorconfig`, VS Code settings, and other IDE-level formatting are not part of the CI pipeline.

### What Remains Open

- **Execution order:** Should Prettier be run before the architectural refactoring (format existing code first, then refactor), after (refactor first, then format), or atomically (each commit is individually formatted)?
- **Prettier diff scope:** How many files and lines will Prettier change? Is it a small diff (suitable for inline) or a large diff (needs its own commit)?
- **ESLint error severity:** Are there real code issues (errors) or only style warnings? Do any ESLint errors overlap with Prettier changes?
- **`eslint-plugin-require-extensions` status:** This plugin is installed (`^0.1.3` in devDependencies) but NOT configured in `eslint.config.js`. Is it intentionally inactive? Was it superseded by `eslint-plugin-import`'s `import/extensions` rule? Does upstream intend to activate it? Does its presence in `package.json` indicate future intent?
- **`typescript-eslint/recommended` ruleset:** Which specific rules from this preset are active? Are there typescript-specific rules that may flag our patterns (e.g., `no-non-null-assertion`, `prefer-const`, `consistent-type-imports`)?
- **Trailing comma behavior:** Prettier 2.8.8 defaults to `trailingComma: "all"` — do our files already follow this convention? Are there trailing comma differences?
- **Line width:** Prettier defaults to `printWidth: 80`. Are there lines in our CSAPI code that exceed 80 characters?

---

## 4. Research Questions

### Core Questions

1. What is the complete effective Prettier configuration (explicit settings + defaults for Prettier 2.8.8) and what changes will it apply to our CSAPI files?
2. What is the complete effective ESLint configuration (all active rules from `@eslint/js` recommended + `typescript-eslint` recommended + custom rules) and what errors/warnings will it produce on our CSAPI files?
3. What is the recommended execution order for formatting/linting relative to the architectural refactoring, and should formatting be a separate commit?
4. Are there any ESLint or Prettier issues that will require code changes beyond simple formatting (i.e., real logic or structure changes)?
5. What is the exact scope of Prettier formatting changes (file count, line count, change categories)?
6. How do the formatting/linting tools interact with the module boundary refactoring — are there emergent issues when CSAPI exports move from `src/index.ts` to the barrel file?

### Detailed Questions

#### Prettier Configuration and Defaults (8 questions)

1. What version of Prettier is configured in the upstream repository? The `package.json` specifies `"prettier": "2.8.8"`. What are the _default_ settings for this specific version, since only `semi` and `singleQuote` are explicitly configured in `.prettierrc.json`?
2. What is the effective `trailingComma` setting? Prettier 2.8.8 defaults to `"all"` for trailing commas. Is this the active setting, or did an earlier Prettier version default to `"es5"`? (Prettier 2.x defaults to `"all"` since 2.0, but confirm for 2.8.8 specifically.)
3. What is the effective `printWidth` setting? The default is 80. Are there lines in our CSAPI files that exceed 80 characters? If so, how many files and lines are affected?
4. What is the effective `tabWidth` setting? Default is 2. Do our files use 2-space indentation consistently?
5. What is the effective `endOfLine` setting? Default is `"lf"`. Do our files use LF line endings, or are there CR/LF inconsistencies (common on Windows development environments)?
6. What is the effective `arrowParens` setting? Default is `"always"`. Do our arrow functions already include parentheses around single parameters?
7. What files does `.prettierignore` exclude? Currently: `fixtures/**/*.xml`, `fixtures/**/notjson.json`, `dist`, `app/dist`, `node_modules`, `app/node_modules`. Does this affect any CSAPI files? (It should not — CSAPI source is in `src/`, not `fixtures/`.)
8. When running `npx prettier --check src/ogc-api/csapi/`, how many files fail the check? What is the nature of the failures (trailing commas, line width, quote style, semicolons, or other)?

#### ESLint Configuration and Rules (10 questions)

9. What is the complete list of rules activated by `js.configs.recommended` (`@eslint/js`)? Which of these are relevant to TypeScript code?
10. What is the complete list of rules activated by `typescriptEslint.configs.recommended`? Specifically: does it enable `@typescript-eslint/consistent-type-imports`, `@typescript-eslint/no-non-null-assertion`, `@typescript-eslint/prefer-const`, `@typescript-eslint/no-inferrable-types`, or other rules that may affect our code?
11. The `import/extensions` rule is set to `['error', 'always', { ignorePackages: true }]`. All CSAPI files already use `.js` extensions on local imports and omit extensions on package imports (`'geojson'`). Are there any CSAPI files that violate this rule? What about the new barrel file (`csapi/index.ts`) — will its re-exports need `.js` extensions?
12. The `@typescript-eslint/no-unused-vars` rule uses pattern `^_` for ignored parameters. Do any of our CSAPI files have unused variables that don't follow this convention? Will the architectural refactoring (removing `csapi()` from endpoint, removing CSAPI exports from `src/index.ts`) create new unused-variable situations?
13. The `@typescript-eslint/no-explicit-any` rule is turned off (`'off'`). Does our CSAPI code use `any` types? This is informational — we won't be flagged, but it's relevant for code quality assessment.
14. `eslint-plugin-require-extensions` (version `^0.1.3`) is installed in devDependencies but is NOT imported or configured in `eslint.config.js`. It is a dead dependency — installed but inactive. Why? Was it superseded by the `import/extensions` rule from `eslint-plugin-import`? Should we assume it will be activated in the future? Does its presence in `package.json` indicate upstream intent?
15. Does the `eslint-plugin-import` plugin enforce import ordering (e.g., `import/order` rule)? The ESLint config does not explicitly set `import/order`, but some plugins enable it by default. If active, what order does it require (built-ins first, then external packages, then internal modules)?
16. Are there any ESLint rules that interact with the barrel file pattern? For example, does `import/no-cycle` detect circular imports? Is `import/no-self-import` active? These are relevant because the barrel file (`csapi/index.ts`) will re-export from internal modules.
17. When running `npx eslint src/ogc-api/csapi/`, how many errors and warnings are produced? What categories do they fall into (import issues, unused variables, type issues, style issues)?
18. The ESLint config uses the flat config format (`eslint.config.js` with `defineConfig`). Does this affect how we configure any new files? Are there glob patterns that might miss CSAPI files or the new barrel file?

#### Cross-Tool Interactions (5 questions)

19. Do Prettier and ESLint conflict on any rules? For example, does ESLint enforce a formatting style that Prettier overrides, or vice versa? The typical pattern is to let Prettier handle formatting and ESLint handle logic/import rules — is this how the upstream config works? (Note: there is no `eslint-config-prettier` or `eslint-plugin-prettier` in the devDependencies.)
20. TypeScript's `noEmit` mode (`"typecheck": "tsc --noEmit"`) catches type errors. Does it overlap with any `typescript-eslint` rules? For example, if `typescript-eslint` reports a type error that `tsc` also reports, is there double reporting?
21. How does `prettier --check` interact with `eslint .` in CI? Are they run sequentially or in parallel? Does the order matter? (Check the `qa.yml` workflow or the `package.json` scripts.)
22. If Prettier reformats a file that ESLint then flags for a different reason (e.g., Prettier adds trailing commas but ESLint flags an unused import on the same line), what is the correct resolution order?
23. The CSAPI test files (29 files in `csapi/*.spec.ts` and `csapi/integration/*.spec.ts`) — do they have different Prettier or ESLint rules applied? The ESLint config has an override for `**/__mocks__/**/*` but not for `*.spec.ts` files. Do test files follow the same rules as source files?

#### Formatting Impact on CSAPI Files (6 questions)

24. How many of the 27 CSAPI source files will Prettier modify? Categorize the changes: (a) files with zero changes (already formatted), (b) files with only whitespace/formatting changes, (c) files with structural changes (line wrapping, trailing commas, parentheses).
25. How many of the 29 CSAPI test files will Prettier modify? Same categorization as Q24.
26. For the files that Prettier modifies, what are the most common change categories? Rank by frequency: trailing commas, line wrapping at 80 chars, quote style changes, semicolon changes, arrow function parentheses, object/array formatting, other.
27. Are there any Prettier changes that affect semantics? (Prettier is supposed to be semantics-preserving, but trailing comma additions in function parameter lists or template literal formatting can occasionally cause issues.)
28. What is the total line diff from `npx prettier --write src/ogc-api/csapi/`? (Run dry-run first with `--check`, then `--write` on a throwaway branch to measure the actual diff.)
29. Do any CSAPI fixture files (in `fixtures/ogc-api/csapi/` or `fixtures/ogc-api/sample-data/`) need formatting? The `.prettierignore` excludes `fixtures/**/*.xml` but not JSON fixtures. Will `prettier --check fixtures/` flag any JSON files we created?

#### Formatting Impact on Modified Core Files (5 questions)

30. The architectural refactoring will modify `src/ogc-api/endpoint.ts` (remove CSAPI imports, `csapi()` method, cache field) and `src/index.ts` (remove ~170 lines of CSAPI exports). Will Prettier format the _remaining_ code in these files differently after the removals? (e.g., if a line was at 79 characters and removing a nearby line causes Prettier to reflow.)
31. Will ESLint's `no-unused-vars` flag any new unused imports in `src/ogc-api/endpoint.ts` after removing the `csapi()` method and related code? Specifically: after removing `import CSAPIQueryBuilder from './csapi/url_builder.js'` and `import { scanCsapiLinks } from './csapi/helpers.js'` (the two constraint violations), are there other imports that become unused?
32. Will ESLint's `import/extensions` rule require `.js` extensions in the new barrel file's re-exports? For example: `export { CSAPIQueryBuilder } from './url_builder.js'` — is the `.js` extension required here?
33. After removing CSAPI exports from `src/index.ts`, will the remaining exports still comply with all ESLint rules? Are there any imports in `src/index.ts` that exist solely to support CSAPI re-exports and will become unused?
34. If new files are created (barrel file, factory file), what Prettier/ESLint rules must they follow from inception? Draft a compliance checklist for new file creation.

#### Execution Order and Commit Strategy Input (4 questions)

35. Should formatting be applied before or after the architectural refactoring? Arguments for "before": formatting-only commit is a clean diff, and subsequent refactoring commits are easier to review because they don't mix formatting with logic changes. Arguments for "after": formatting a file that will be significantly modified is wasted effort if the refactoring changes the same lines.
36. If formatting is applied as a separate commit, how large will the diff be? (Estimate based on Q24–Q29 results.) Is it small enough to review inline, or large enough that reviewers should be told "this is a formatting-only commit, please skip."?
37. Will jahow (the upstream maintainer) prefer seeing formatting changes isolated or interleaved? Is there precedent in the upstream repository for how formatting changes are committed? (Check recent commit history for formatting-only commits.)
38. Does the upstream CI pipeline run `format:check` and `lint` on every commit in a PR, or only on the final state? If every commit is checked, each commit must individually pass formatting and linting — this constrains the commit ordering strategy.

**Total: 38 detailed questions**

---

## 5. Sources

### Primary Sources (In Workspace)

| Source                    | Path                                                 | What to Extract                                                                                                                                                                                                                                   |
| ------------------------- | ---------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Prettier configuration    | `.prettierrc.json`                                   | Explicit rules: `semi: true`, `singleQuote: true`. All other options are Prettier 2.8.8 defaults.                                                                                                                                                 |
| Prettier ignore patterns  | `.prettierignore`                                    | Excluded paths: `fixtures/**/*.xml`, `fixtures/**/notjson.json`, `dist`, `app/dist`, `node_modules`, `app/node_modules`                                                                                                                           |
| ESLint flat config        | `eslint.config.js`                                   | Complete rule configuration: `import/extensions`, `no-explicit-any: off`, `no-unused-vars` with `^_` pattern. Extends `js.configs.recommended` + `typescriptEslint.configs.recommended`. Plugins: `eslint-plugin-import`.                         |
| Package metadata          | `package.json`                                       | Prettier version (`2.8.8`), ESLint version (`^9.38.0`), all ESLint plugins (`eslint-plugin-import ^2.32.0`, `eslint-plugin-require-extensions ^0.1.3`, `typescript-eslint ^8.46.2`). Scripts: `format:write`, `format:check`, `lint`, `lint:fix`. |
| TypeScript config         | `tsconfig.json`                                      | Compiler options affecting lint: `target: ESNext`, `module: ESNext`, `moduleResolution: node`, `declaration: true`                                                                                                                                |
| CSAPI url_builder imports | `src/ogc-api/csapi/url_builder.ts` (lines 1–11)      | Import style: single quotes, semicolons, `.js` extensions, `import type` for type-only imports                                                                                                                                                    |
| CSAPI model imports       | `src/ogc-api/csapi/model.ts` (lines 1–3)             | Import style: `import type` for all imports (type-only module), `.js` extensions on local, no ext on `'geojson'`                                                                                                                                  |
| CSAPI helpers imports     | `src/ogc-api/csapi/helpers.ts` (lines 1–3)           | Import style: consistent with url_builder and model                                                                                                                                                                                               |
| CSAPI formats barrel      | `src/ogc-api/csapi/formats/index.ts`                 | 344-line barrel file — re-export style with `.js` extensions                                                                                                                                                                                      |
| CSAPI command routing     | `src/ogc-api/csapi/command-routing.ts` (lines 26–28) | Import pattern: `import type` for default imports                                                                                                                                                                                                 |
| Core endpoint imports     | `src/ogc-api/endpoint.ts` (lines 1–54)               | Upstream import style — baseline for comparison with CSAPI                                                                                                                                                                                        |
| Core model imports        | `src/ogc-api/model.ts` (lines 1–2)                   | Upstream import style                                                                                                                                                                                                                             |
| Core info imports         | `src/ogc-api/info.ts` (lines 1–21)                   | Upstream import style                                                                                                                                                                                                                             |
| EDR url_builder imports   | `src/ogc-api/edr/url_builder.ts` (lines 1–20)        | EDR import style — baseline for consistency check                                                                                                                                                                                                 |
| Root exports              | `src/index.ts` (lines 45–252)                        | ~170 lines of CSAPI exports that will be removed — ESLint impact of removal                                                                                                                                                                       |
| CSAPI test file example   | `src/ogc-api/csapi/url_builder.spec.ts` (lines 1–20) | Test file import style and formatting                                                                                                                                                                                                             |
| Endpoint CSAPI tests      | `src/ogc-api/endpoint.spec.ts` (lines 2836–2888)     | CSAPI test block — formatting and lint compliance                                                                                                                                                                                                 |
| CSAPI fixture files       | `fixtures/ogc-api/csapi/`                            | JSON fixture files — Prettier may format these                                                                                                                                                                                                    |

### External Sources

| Source                                  | URL/Reference                                                                   | What to Extract                                                                                                                                                                                                                                                  |
| --------------------------------------- | ------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Prettier 2.8.8 documentation            | https://prettier.io/docs/en/options.html                                        | Complete default options for Prettier 2.8.8: `trailingComma` default, `printWidth` default (80), `tabWidth` default (2), `endOfLine` default (`"lf"`), `arrowParens` default (`"always"`), `bracketSpacing` default (`true`), `proseWrap` default (`"preserve"`) |
| Prettier 2.x changelog                  | https://prettier.io/blog/2020/03/21/2.0.0                                       | Confirm `trailingComma` default changed to `"all"` in 2.0.0 — verify this is the behavior in 2.8.8                                                                                                                                                               |
| ESLint `@eslint/js` recommended rules   | https://eslint.org/docs/latest/rules/                                           | Complete list of rules in `js.configs.recommended` — all rules marked ✓ (recommended)                                                                                                                                                                            |
| `typescript-eslint` recommended rules   | https://typescript-eslint.io/rules/                                             | Complete list of rules in `typescriptEslint.configs.recommended` — identify which rules may affect our code                                                                                                                                                      |
| `eslint-plugin-import` rules            | https://github.com/import-js/eslint-plugin-import                               | `import/extensions` detailed behavior, `import/order` if active, `import/no-cycle` if active                                                                                                                                                                     |
| `eslint-plugin-require-extensions` docs | https://github.com/nicolo-ribaudo/eslint-plugin-require-extensions              | What this plugin does, whether it overlaps with `import/extensions`, why it might be installed but unconfigured                                                                                                                                                  |
| Prettier + ESLint integration guide     | https://prettier.io/docs/en/integrating-with-linters.html                       | Best practices for running Prettier and ESLint together without conflicts. Note: upstream does NOT use `eslint-config-prettier` — confirm whether this causes rule conflicts.                                                                                    |
| Upstream CI workflow                    | `https://github.com/camptocamp/ogc-client/blob/master/.github/workflows/qa.yml` | How `format:check`, `lint`, and `typecheck` are run in CI — order, per-commit vs final-state                                                                                                                                                                     |

### Prior Research Findings

| Finding          | Path                                                                     | What to Use                                                                                                         |
| ---------------- | ------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------- |
| Plan 01 findings | `docs/research/phase-6/findings/01-build-system-entry-point-analysis.md` | Build output structure — which files in `dist/` are affected by Prettier (source maps, declarations)                |
| Plan 06 findings | `docs/research/phase-6/findings/06-endpoint-decoupling-architecture.md`  | File-level modifications — which files will be created/modified/deleted, informing the Prettier/ESLint impact scope |

---

## 6. Research Methodology

### Phase 1: Document the Complete Effective Configuration (~25 minutes)

**Objective:** Determine the full effective Prettier and ESLint configuration including all defaults, inherited rules, and plugin interactions.

**Tasks:**

1. Document the complete Prettier 2.8.8 effective configuration — combine the two explicit settings (`semi: true`, `singleQuote: true`) with all Prettier 2.8.8 defaults. Produce a full settings table showing every option and its effective value.
2. Document the complete ESLint effective configuration — enumerate every rule from `js.configs.recommended`, every rule from `typescriptEslint.configs.recommended`, and the three custom rules (`import/extensions`, `no-explicit-any: off`, `no-unused-vars`). For each rule, note: name, severity (error/warn/off), and brief description.
3. Determine the status of `eslint-plugin-require-extensions` — confirm it is inactive (installed but not configured). Research whether it overlaps with `import/extensions` and whether its presence signals upstream intent.
4. Determine whether `eslint-config-prettier` is needed — upstream does NOT have it installed. Check whether any active ESLint rules conflict with Prettier's formatting. If so, document the conflicts.
5. Document the `.prettierignore` exclusions and confirm CSAPI files are not excluded.

**Output:** Complete effective configuration table for both tools, with notes on inactive plugins, potential conflicts, and exclusion patterns.

### Phase 2: Run Tools and Capture Output (~30 minutes)

**Objective:** Execute Prettier and ESLint against the CSAPI codebase and capture every error, warning, and formatting change.

**Tasks:**

1. Run `npx prettier --check src/ogc-api/csapi/` and capture all files that fail the check. Record the count and categorize by change type.
2. Run `npx prettier --check src/ogc-api/endpoint.ts src/index.ts` to check the two core files that will be modified.
3. Run `npx prettier --check fixtures/ogc-api/` to check if any CSAPI-related JSON fixtures fail formatting.
4. Run `npx eslint src/ogc-api/csapi/` and capture all errors and warnings. Categorize by rule name and severity.
5. Run `npx eslint src/ogc-api/endpoint.ts src/index.ts` to check the two core files.
6. On a throwaway branch (or using `git stash`): run `npx prettier --write src/ogc-api/csapi/` and then `git diff --stat` to measure the exact scope of formatting changes. Record: files changed, insertions, deletions.
7. Run `npx prettier --write src/ogc-api/csapi/` then `git diff src/ogc-api/csapi/` to capture the specific changes. Categorize: trailing commas, line wrapping, quote changes, semicolons, arrow parens, other.
8. Revert the formatting changes: `git checkout -- src/ogc-api/csapi/`.

**Output:** Raw tool output for both Prettier and ESLint, categorized and summarized.

### Phase 3: Analyze Interactions and Edge Cases (~25 minutes)

**Objective:** Identify cross-tool interactions, refactoring-specific impacts, and edge cases that affect the commit strategy.

**Tasks:**

1. Cross-reference Prettier changes with ESLint errors — are there files where both tools flag the same line? Are there files where fixing one introduces a violation for the other?
2. Analyze the refactoring impact on ESLint: after removing CSAPI imports from `endpoint.ts` (lines 52–53), CSAPI exports from `index.ts` (lines 45–252), and the `csapi()` method (lines 385–413), identify any new unused imports or variables that `no-unused-vars` will flag.
3. Analyze the barrel file requirements: the new `src/ogc-api/csapi/index.ts` will contain `export { ... } from './url_builder.js'` and similar re-exports. Verify that `import/extensions` requires `.js` on these re-exports. Check the existing barrel file (`csapi/formats/index.ts`, 344 lines) as a reference — does it pass ESLint?
4. Check whether test file formatting differs from source file formatting — run `npx prettier --check src/ogc-api/csapi/**/*.spec.ts` separately and compare the failure rate to source files.
5. Investigate the `endOfLine` setting — since development is on Windows but upstream likely uses LF (common in Node.js projects), check if any CSAPI files have CRLF line endings that Prettier will convert.
6. Determine whether Prettier 2.8.8's `trailingComma: "all"` default applies to our files by checking a sample of function calls, object literals, and import statements for trailing comma presence/absence.

**Output:** Interaction analysis, edge case inventory, and refactoring-specific impact list.

### Phase 4: Determine Execution Order and Commit Strategy Recommendation (~20 minutes)

**Objective:** Recommend the formatting/linting execution order relative to the architectural refactoring, with rationale.

**Tasks:**

1. Estimate the total Prettier diff scope (files changed, lines changed) from Phase 2 results.
2. Evaluate three execution orders:
   - **Option A: Format First** — Run Prettier on all CSAPI files in a dedicated commit, then apply architectural changes. Pro: Formatting diff is isolated, reviewers can skip it. Con: Some formatted code will be deleted or moved by the refactoring.
   - **Option B: Refactor First** — Apply all architectural changes, then run Prettier as a final pass. Pro: Only the final code gets formatted. Con: Intermediate commits may fail `format:check` in CI.
   - **Option C: Atomic** — Each commit includes both logical changes and formatting for the affected files. Pro: Every commit passes CI individually. Con: Formatting changes are mixed with logic changes in every diff.
3. Check upstream CI behavior: does the CI workflow check every commit individually, or only the final state of the PR? This determines whether intermediate commits must pass `format:check`.
4. Check upstream commit history for precedent: has jahow or any contributor ever submitted a formatting-only commit? What is the preferred style?
5. Produce the recommendation with rationale, including a decision tree for Plan 08 to follow.

**Output:** Execution order recommendation with rationale, pros/cons matrix, and decision tree for Plan 08.

### Phase 5: Synthesis and Documentation (~20 minutes)

**Objective:** Consolidate all phase outputs into the deliverable findings document.

**Tasks:**

1. Synthesize findings from Phases 1–4 into the findings report structure.
2. Produce the file-by-file impact matrix: for each CSAPI file, record: (a) Prettier status (pass/fail, change categories), (b) ESLint status (errors, warnings, rule names), (c) refactoring interaction (will the file be modified by Plan 06?).
3. Verify all 38 research questions are answered with specific, evidenced results.
4. Validate findings against boundary conditions.
5. Write the deliverable document.
6. Cross-reference with Plan 08 — document exactly what Plan 08 needs from this plan.

**Output:** Completed findings report at `docs/research/phase-6/findings/07-prettier-eslint-configuration-analysis.md`

---

## 7. Success Criteria

This research is complete when:

- [ ] All 38 detailed research questions have specific, evidenced answers
- [ ] Findings respect all boundary conditions listed in Section 3
- [ ] Complete Prettier effective configuration is documented (all options, explicit + defaults)
- [ ] Complete ESLint effective configuration is documented (all active rules from all presets + custom rules)
- [ ] `eslint-plugin-require-extensions` status is definitively resolved (active vs inactive, overlap with `import/extensions`)
- [ ] `npx prettier --check` has been executed against all CSAPI source files, test files, and relevant fixtures, with results captured
- [ ] `npx eslint` has been executed against all CSAPI files, with results captured and categorized by rule
- [ ] File-by-file impact matrix is produced (every CSAPI file × Prettier status × ESLint status × refactoring interaction)
- [ ] Prettier diff scope is measured (files changed, lines changed, change categories ranked)
- [ ] Cross-tool interaction analysis is complete (Prettier ↔ ESLint conflicts, absence of `eslint-config-prettier`)
- [ ] Refactoring-specific ESLint impact is documented (new unused vars after removing `csapi()`, barrel file compliance)
- [ ] Execution order recommendation is produced with rationale and pros/cons matrix
- [ ] New file compliance checklist is drafted (what rules a new barrel/factory file must follow)
- [ ] Deliverable document is complete and follows the findings report template
- [ ] Findings are cross-referenced with Plan 08

---

## 8. Deliverable

**Title:** Prettier and ESLint Configuration Analysis: Formatting/Linting Impact Assessment and Execution Strategy

**Location:** `docs/research/phase-6/findings/07-prettier-eslint-configuration-analysis.md`

**Required Sections:**

1. Executive Summary — key findings: total formatting changes, ESLint error count, recommended execution order
2. Effective Prettier Configuration — complete settings table (explicit + defaults for 2.8.8), `.prettierignore` analysis
3. Effective ESLint Configuration — complete rule inventory (recommended presets + custom rules), plugin status, inactive plugin analysis
4. Prettier Impact Assessment — file-by-file results, change categorization, total diff scope
5. ESLint Impact Assessment — file-by-file results, error/warning categorization by rule, severity summary
6. Cross-Tool Interaction Analysis — Prettier ↔ ESLint conflicts, absence of `eslint-config-prettier`, resolution strategy
7. Refactoring-Specific Impact — new unused imports after `csapi()` removal, barrel file compliance, new file requirements
8. File-by-File Impact Matrix — tabular summary: file × Prettier × ESLint × refactoring interaction
9. Execution Order Recommendation — three options evaluated, recommendation with rationale, decision tree for Plan 08
10. New File Compliance Checklist — rules that new files must follow (barrel file, factory file, test files)
11. Fixture Formatting Assessment — JSON fixture files in `fixtures/ogc-api/` that Prettier may modify
12. Impact on Plan 08 — what Plan 08 consumes: execution order, file list, commit strategy constraints
13. Open Questions — anything unresolved

---

## 9. Risks and Mitigation

| Risk                                                                                                                                                  | Impact                                                                                                                      | Mitigation                                                                                                                                                                                                                                         |
| ----------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Prettier reformats a large number of lines (1,000+), creating a noisy diff that obscures the architectural refactoring                                | Reviewers struggle to distinguish formatting changes from logic changes, increasing review burden and risk of missed issues | Measure the diff scope in Phase 2. If large, recommend a dedicated formatting commit in the execution order. Provide a clear commit message ("formatting only — no logic changes") so reviewers can skip.                                          |
| ESLint flags real code issues (not just formatting) that require logic changes                                                                        | Additional code changes beyond the architectural refactoring, affecting the scope and timeline of Plan 08                   | Capture every ESLint error in Phase 2 and classify as "formatting" vs "logic." Logic issues are added to Plan 08's changelist as additional tasks.                                                                                                 |
| Prettier and ESLint conflict on a rule (e.g., ESLint enforces a format that Prettier overrides)                                                       | Files that pass `npm run lint` fail `npm run format:check`, or vice versa — creating an impossible-to-satisfy state         | Check for the absence of `eslint-config-prettier` in Phase 1. If conflicts exist, document them and recommend adding `eslint-config-prettier` as a separate upstream discussion (not part of our PR). Workaround: run Prettier _after_ ESLint fix. |
| `endOfLine` differences between Windows (CRLF) and upstream (LF) cause Prettier to rewrite every line in every file                                   | Massive diff consisting entirely of line ending changes, drowning out real changes                                          | Check `endOfLine` setting in Phase 1. If CRLF files exist, fix line endings in a dedicated commit before any other changes. Configure Git to handle line endings correctly (`git config --global core.autocrlf input`).                            |
| The `eslint-plugin-require-extensions` plugin is activated by upstream between now and PR submission, introducing new rules our code must comply with | Our code may fail CI if the plugin is activated and our imports don't comply                                                | Document the plugin's rules in Phase 1. Since our files already use `.js` extensions consistently, the risk is low. Note: `import/extensions` already enforces the same requirement.                                                               |
| Running `prettier --write` or `eslint --fix` corrupts a file or introduces a subtle bug                                                               | Code breakage that may not be caught until tests run                                                                        | Always run on a throwaway branch or use `git stash`. Verify with `npm run test:browser` and `npm run test:node` after any automated formatting. Never commit formatting changes without a test run.                                                |
| Trailing comma differences between Prettier 2.8.8 and a newer version upstream might adopt                                                            | Formatting changes that work locally but fail upstream CI if Prettier versions diverge                                      | Pin to the exact Prettier version in `package.json` (`"prettier": "2.8.8"` — already pinned, no caret/tilde). Verify by running the pinned version, not a globally installed one.                                                                  |

---

## 10. Research Status Checklist

- [ ] Phase 1: Document Complete Effective Configuration — Not Started
- [ ] Phase 2: Run Tools and Capture Output — Not Started
- [ ] Phase 3: Analyze Interactions and Edge Cases — Not Started
- [ ] Phase 4: Determine Execution Order and Commit Strategy — Not Started
- [ ] Phase 5: Synthesis and Documentation — Not Started
- [ ] Deliverable document created
- [ ] Cross-references updated in Plan 08

**Start Date:** —
**Completion Date:** —
**Actual Time:** —
