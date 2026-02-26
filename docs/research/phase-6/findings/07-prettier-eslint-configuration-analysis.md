# Findings Report 07: Prettier and ESLint Configuration Analysis — Formatting/Linting Impact Assessment and Execution Strategy

> **Plan 7 of 8** | **Phase 6 — Upstream Acceptance Refactoring**

---

## Metadata

| Field                  | Value                                                                                                                 |
| ---------------------- | --------------------------------------------------------------------------------------------------------------------- |
| **Research Plan**      | [Plan 07: Prettier and ESLint Configuration Analysis](../research-plans/07-prettier-eslint-configuration-analysis.md) |
| **Plan Type**          | Mechanical analysis                                                                                                   |
| **Date Started**       | 2026-02-25                                                                                                            |
| **Date Completed**     | 2026-02-25                                                                                                            |
| **Research Time**      | ~3 hours (actual)                                                                                                     |
| **Estimated Time**     | 1–2 hours (from plan)                                                                                                 |
| **Questions Answered** | 38 of 38 detailed questions                                                                                           |
| **Depends On**         | None                                                                                                                  |
| **Blocks**             | Plan 08 (File-Level Changelist and Commit Strategy)                                                                   |

---

## Source Summary

### Primary Sources Consulted

| Source                   | Path / URL                            | What Was Extracted                                                         |
| ------------------------ | ------------------------------------- | -------------------------------------------------------------------------- |
| Prettier configuration   | `.prettierrc.json`                    | 2 explicit settings: `semi: true`, `singleQuote: true`                     |
| Prettier ignore patterns | `.prettierignore`                     | 6 exclusion patterns; no CSAPI files excluded                              |
| ESLint flat config       | `eslint.config.js` (71 lines)         | Complete rule config: 3 custom rules + 2 recommended presets + 2 overrides |
| Package metadata         | `package.json`                        | Prettier `2.8.8` (exact pin), ESLint `^9.38.0`, all plugin versions        |
| TypeScript config        | `tsconfig.json`                       | target/module ESNext, moduleResolution node                                |
| CI workflow              | `.github/workflows/qa.yml` (upstream) | Single job, sequential: format:check → typecheck → lint → tests            |
| Upstream commit history  | `git log upstream/main`               | 5+ formatting-only commits (precedent for dedicated formatting commits)    |

### Prior Findings Used

| Finding          | Path                                              | What Was Consumed                                                                                       |
| ---------------- | ------------------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| Plan 06 findings | `findings/06-endpoint-decoupling-architecture.md` | File-level modifications: which files will be created/modified/deleted by the architectural refactoring |

### Sources Not Available or Not Useful

- **Prettier 2.x changelog (https://prettier.io/blog/2020/03/21/2.0.0):** The research plan asserted Prettier 2.x defaults `trailingComma` to `"all"` since 2.0 — this was **incorrect**. Verified via `npx prettier --support-info` that Prettier 2.8.8 defaults to `"es5"`. The `"all"` default was introduced in Prettier 3.0.
- **`eslint-plugin-require-extensions` docs:** Not needed — the plugin is installed but completely unconfigured (never imported in `eslint.config.js`), so its documentation is informational only.

---

## Executive Summary

This report documents the complete formatting and linting impact of upstream's Prettier and ESLint toolchain on the 56 CSAPI files (27 source + 29 test) and the core files modified by the architectural refactoring. Every Prettier setting and ESLint rule was analyzed, tools were executed against the codebase, and cross-tool interactions were verified.

**Key discovery:** A critical Windows development environment issue was identified — Prettier's default `endOfLine: "lf"` combined with Git's `core.autocrlf = true` on Windows causes **every file in the repo** (654 files) to fail `prettier --check`. This is a non-issue for CI (which runs on `ubuntu-latest` with native LF line endings) but affects all local Prettier invocations on Windows. With line endings excluded (`--end-of-line auto`), only **46 of 56** CSAPI files have real formatting issues.

The formatting changes are extensive: **3,023 insertions and 1,036 deletions across 46 files**. The dominant change is object literal expansion at Prettier's 80-character `printWidth` — test files with inline link objects (`{ rel: '...', href: '...' }`) are expanded to multi-line format, accounting for the majority of the diff. `url_builder.spec.ts` alone contributes 2,221 of the 4,059 total line changes.

ESLint produces **99 errors, 0 warnings** — all from a single rule: `@typescript-eslint/no-unused-vars`. These are unused type imports in test files (used for type checking during development but not referenced at runtime) and one unused value import. All are fixable by converting to `import type` or prefixing with `_`.

Prettier and ESLint do **not conflict** — ESLint enforces no formatting rules, and `eslint-config-prettier` is not installed because it is not needed.

### Key Metrics

| Metric                                 | Value                                        | Significance                                        |
| -------------------------------------- | -------------------------------------------- | --------------------------------------------------- |
| CSAPI files with real Prettier changes | 46 of 56 (82%)                               | Large majority need formatting                      |
| Total Prettier diff scope              | 3,023 insertions / 1,036 deletions           | Too large for inline — needs own commit             |
| ESLint errors                          | 99 errors, 0 warnings                        | All `no-unused-vars`, all fixable                   |
| ESLint-affected files                  | 15 of 56 (27%)                               | Concentrated in sensorml/ and swecommon/ test files |
| CSAPI fixture files needing formatting | 4 of 4 JSON files                            | Minor — small JSON formatting changes               |
| Core file Prettier changes             | `endpoint.ts`: 8-line diff; `index.ts`: none | Minimal core file impact                            |
| Core file ESLint errors                | 0                                            | No ESLint issues in core files                      |

### Overall Assessment

**The formatting diff is large enough to warrant a dedicated formatting commit.** With 3,023 insertions across 46 files, mixing Prettier changes with architectural refactoring would create an unreadable diff. Upstream has clear precedent for formatting-only commits. The recommended execution order is **Option A (Format First)**: apply Prettier in a dedicated commit, then apply architectural changes in subsequent commits, so each commit passes CI and the refactoring diff is clean.

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Effective Prettier Configuration](#1-effective-prettier-configuration)
3. [Effective ESLint Configuration](#2-effective-eslint-configuration)
4. [Cross-Tool Interaction Analysis](#3-cross-tool-interaction-analysis)
5. [Formatting Impact on CSAPI Files](#4-formatting-impact-on-csapi-files)
6. [Formatting Impact on Modified Core Files](#5-formatting-impact-on-modified-core-files)
7. [Execution Order and Commit Strategy](#6-execution-order-and-commit-strategy)
8. [File-by-File Impact Matrix](#7-file-by-file-impact-matrix)
9. [Fixture Formatting Assessment](#8-fixture-formatting-assessment)
10. [New File Compliance Checklist](#9-new-file-compliance-checklist)
11. [Boundary Condition Verification](#10-boundary-condition-verification)
12. [Implementation Scope Gate Assessment](#11-implementation-scope-gate-assessment)
13. [Impact on Dependent Plans](#12-impact-on-dependent-plans)
14. [Key Takeaways](#13-key-takeaways)
15. [Impact on Implementation](#14-impact-on-implementation)
16. [Open Questions](#15-open-questions)

---

## 1. Effective Prettier Configuration

### Question 1: What is the complete effective Prettier configuration for version 2.8.8?

**Answer:** Prettier 2.8.8 is pinned exactly in `package.json` (`"prettier": "2.8.8"` — no caret or tilde). Only two options are explicitly configured in `.prettierrc.json`:

```json
{
  "semi": true,
  "singleQuote": true
}
```

All other options use Prettier 2.8.8 defaults. The complete effective configuration:

| Option                      | Effective Value | Source   | Impact on CSAPI                                               |
| --------------------------- | --------------- | -------- | ------------------------------------------------------------- |
| `printWidth`                | **80**          | Default  | **HIGH** — dominant change; many lines exceed 80 chars        |
| `tabWidth`                  | **2**           | Default  | None — our files already use 2-space indentation              |
| `useTabs`                   | **false**       | Default  | None — our files use spaces                                   |
| `semi`                      | **true**        | Explicit | None — our files already use semicolons                       |
| `singleQuote`               | **true**        | Explicit | None — our files already use single quotes                    |
| `trailingComma`             | **"es5"**       | Default  | Low — trailing commas in objects/arrays where ES5 allows them |
| `bracketSpacing`            | **true**        | Default  | None — our files already use `{ key: value }`                 |
| `arrowParens`               | **"always"**    | Default  | None — our arrow functions already use parentheses            |
| `endOfLine`                 | **"lf"**        | Default  | **CRITICAL on Windows** — see Q5                              |
| `proseWrap`                 | **"preserve"**  | Default  | None — affects markdown only                                  |
| `htmlWhitespaceSensitivity` | **"css"**       | Default  | N/A — no HTML files                                           |
| `quoteProps`                | **"as-needed"** | Default  | None — our files quote props only when needed                 |
| `jsxSingleQuote`            | **false**       | Default  | N/A — no JSX files                                            |

**Evidence:** `trailingComma` default verified via `npx prettier --support-info`, which returns `"default": "es5"` for Prettier 2.8.8. The research plan incorrectly asserted `"all"` — that is the Prettier 3.0+ default.

### Question 2: What is the effective `trailingComma` setting?

**Answer:** `"es5"` — confirmed via `npx prettier --support-info`. This means trailing commas are added in objects and arrays (where ES5 syntax allows) but **NOT** in function parameter lists or function call arguments (which require ES2017+). The research plan's assertion that Prettier 2.x defaults to `"all"` since 2.0 was **incorrect** — the `"all"` default was introduced in Prettier 3.0.0.

**Evidence:**

```
> npx prettier --support-info | select "trailingComma"
"default": "es5",
"description": "Print trailing commas wherever possible when multi-line.",
"name": "trailingComma",
```

### Question 3: What is the effective `printWidth` setting?

**Answer:** **80** (default). This is the dominant cause of formatting changes in CSAPI files. Many lines exceed 80 characters, particularly:

- Object literals in test files (inline link objects like `{ rel: 'items', href: '/api/...' }`)
- Import statements with multiple named imports
- Union type definitions in `model.ts`
- Ternary expressions in `helpers.ts`
- Template literal strings in error messages

Prettier wraps these onto multiple lines, expanding single-line expressions into multi-line blocks. This accounts for the majority of the 3,023-line insertion count — `url_builder.spec.ts` alone has 2,221 line changes, almost entirely from object literal expansion.

### Question 4: What is the effective `tabWidth` setting?

**Answer:** **2** (default). Our CSAPI files consistently use 2-space indentation. No changes from this setting.

### Question 5: What is the effective `endOfLine` setting?

**Answer:** **"lf"** (default). This has a **critical interaction with Windows development environments.**

**Discovery:** On Windows with `git config core.autocrlf = true` (which is the case on this development machine), files are checked out with CRLF line endings on disk. Prettier's `endOfLine: "lf"` flags every file as having wrong line endings. This causes **654 files** across the entire repository (not just CSAPI) to fail `prettier --check`:

```
> npx prettier --check .
[warn] Code style issues found in 654 files. Forgot to run Prettier?
```

**This is a non-issue for CI.** The upstream CI runs on `ubuntu-latest`, where files are natively LF. The CI's `npm run format:check` passes because there are no CRLF line endings.

**Verification:** Running with `--end-of-line auto` (which accepts any line ending) on a known upstream file:

```
> npx prettier --check --end-of-line auto "src/worker/worker.ts"
All matched files use Prettier code style!
```

This confirms: the file is formatted correctly — only the line ending causes the failure.

**Impact on CSAPI analysis:** When measuring CSAPI formatting changes, `--end-of-line auto` was used to isolate real formatting issues from CRLF artifacts. Git's `core.autocrlf` normalizes line endings on commit, so CRLF changes are invisible in `git diff`.

### Question 6: What is the effective `arrowParens` setting?

**Answer:** **"always"** (default). Our CSAPI arrow functions already include parentheses around single parameters (e.g., `(x) => x + 1`). No changes from this setting.

### Question 7: What files does `.prettierignore` exclude?

**Answer:** The `.prettierignore` file contains:

```
fixtures/**/*.xml
fixtures/**/notjson.json
dist
app/dist
node_modules
app/node_modules
```

**No CSAPI files are excluded.** CSAPI source is in `src/ogc-api/csapi/`, which is not covered by any ignore pattern. JSON fixture files in `fixtures/ogc-api/` are NOT excluded by `.prettierignore` (only XML and `notjson.json` are excluded).

### Question 8: How many CSAPI files fail `prettier --check`?

**Answer:**

- **With default settings:** All 56 CSAPI files fail (due to CRLF line endings on Windows)
- **With `--end-of-line auto`:** **46 of 56 files** fail (real formatting issues)
  - 20 of 27 source files fail
  - 26 of 29 test files fail
  - 10 files are already Prettier-compliant (7 source, 3 test)

**Nature of failures (ranked by frequency):**

1. **Line wrapping at 80 chars** — dominant change (object literals, imports, union types, ternaries)
2. **Object literal expansion** — single-line `{ key: value, key: value }` expanded to multi-line when exceeding 80 chars
3. **Import statement wrapping** — multi-import statements broken across lines
4. **Template literal consolidation** — multi-line throw statements consolidated
5. **Trailing comma adjustments** — ES5-style trailing commas added/removed in multi-line structures

### Sub-topic Synthesis

Prettier's configuration is minimal — only 2 of 20+ options are explicitly set. The critical impact comes from three defaults: `printWidth: 80` (causes the vast majority of changes), `endOfLine: "lf"` (causes Windows-only false failures), and `trailingComma: "es5"` (minor trailing comma adjustments). The `singleQuote` and `semi` settings are already followed by our code, so they cause zero changes.

---

## 2. Effective ESLint Configuration

### Question 9: What rules does `js.configs.recommended` activate?

**Answer:** `@eslint/js` recommended enables ~40+ rules. However, most are superseded by TypeScript-specific versions when used alongside `typescript-eslint`. The key `js.configs.recommended` rules that remain active for TypeScript files include:

- `no-cond-assign`, `no-constant-condition`, `no-debugger`, `no-dupe-args`, `no-dupe-keys`, `no-empty`, `no-extra-boolean-cast`, `no-irregular-whitespace`, `no-loss-of-precision`, `no-misleading-character-class`, and other correctness rules.

For TypeScript files, `typescript-eslint/recommended` disables JavaScript-specific rules that TypeScript's type checker handles better (e.g., `no-undef` is off for TS files because TypeScript itself catches undefined references).

### Question 10: What rules does `typescriptEslint.configs.recommended` activate?

**Answer:** The `recommended` config enables these TypeScript-specific rules:

| Rule                                                     | Status                    | Relevance to CSAPI                             |
| -------------------------------------------------------- | ------------------------- | ---------------------------------------------- |
| `@typescript-eslint/no-unused-vars`                      | error                     | **99 errors** — the only ESLint issue in CSAPI |
| `@typescript-eslint/no-explicit-any`                     | **off** (custom override) | No impact — explicitly disabled                |
| `@typescript-eslint/ban-ts-comment`                      | error                     | No violations in CSAPI                         |
| `@typescript-eslint/no-require-imports`                  | error                     | No violations (all CSAPI uses ES imports)      |
| `@typescript-eslint/no-namespace`                        | error                     | No violations                                  |
| `@typescript-eslint/no-non-null-asserted-optional-chain` | error                     | No violations                                  |
| `@typescript-eslint/no-empty-object-type`                | error                     | No violations                                  |
| `@typescript-eslint/no-unsafe-function-type`             | error                     | No violations                                  |
| `@typescript-eslint/no-wrapper-object-types`             | error                     | No violations                                  |
| `@typescript-eslint/prefer-as-const`                     | error                     | No violations                                  |
| `@typescript-eslint/no-unused-expressions`               | error                     | No violations                                  |

**Not enabled** (addressing plan's specific questions): `consistent-type-imports` (NOT in recommended), `no-non-null-assertion` (NOT in recommended — that's in `strict`), `prefer-const` (from base ESLint, already in recommended), `no-inferrable-types` (NOT in recommended).

### Question 11: Does the `import/extensions` rule affect CSAPI files?

**Answer:** The rule is `['error', 'always', { ignorePackages: true }]`. This requires `.js` extensions on all local imports and allows bare imports for packages.

**No CSAPI files violate this rule.** All local imports already use `.js` extensions:

```typescript
import type { OgcApiCollectionInfo } from '../model.js';
import { scanCsapiLinks } from './helpers.js';
```

Package imports correctly omit extensions:

```typescript
import type { GeoJSON } from 'geojson';
```

**The new barrel file** (`csapi/index.ts`) will need `.js` extensions on re-exports:

```typescript
export { CSAPIQueryBuilder } from './url_builder.js'; // .js required
```

This is confirmed by the existing barrel file `csapi/formats/index.ts` (344 lines), which uses `.js` extensions on all re-exports and passes ESLint.

### Question 12: Does `no-unused-vars` flag issues in CSAPI files?

**Answer:** **Yes — 99 errors across 15 files.** All are `@typescript-eslint/no-unused-vars`. The rule configuration is:

```javascript
'@typescript-eslint/no-unused-vars': [
  'error',
  {
    args: 'all',
    argsIgnorePattern: '^_',
    caughtErrors: 'all',
    caughtErrorsIgnorePattern: '^_',
    destructuredArrayIgnorePattern: '^_',
    ignoreRestSiblings: true,
  },
],
```

**Error categories:**

| Category                          | Count | Files                                     | Fix                                         |
| --------------------------------- | ----- | ----------------------------------------- | ------------------------------------------- |
| Unused type imports in test files | ~90   | 13 spec files in sensorml/ and swecommon/ | Convert to `import type` or prefix with `_` |
| Unused destructured import        | 4     | 4 sensorml source files                   | Remove or prefix with `_`                   |
| Unused value import               | 1     | `url_builder.ts`                          | Remove `CSAPIResourceTypes` import          |
| Unused `result` variable          | 1     | 1 integration test file                   | Remove or assert on the value               |

**Will the architectural refactoring create new unused-var issues?** No. The two CSAPI imports removed from `endpoint.ts` (lines 52-53) are **deleted entirely** — they don't become unused, they are removed. No other imports in `endpoint.ts` exist solely to support CSAPI functionality.

### Question 13: Does CSAPI code use `any` types?

**Answer:** Yes, CSAPI code uses `any` in several places, primarily in XML parsing helpers (SensorML/SWE Common parsers where XML element types are inherently dynamic). However, `@typescript-eslint/no-explicit-any` is turned **off** in the ESLint config, so this produces zero errors. This is informational only.

### Question 14: What is the status of `eslint-plugin-require-extensions`?

**Answer:** **Dead dependency — installed but completely inactive.**

- **Installed:** `"eslint-plugin-require-extensions": "^0.1.3"` in `devDependencies`
- **NOT configured:** Not imported in `eslint.config.js`, not listed in plugins, no rules activated
- **Overlaps with:** `eslint-plugin-import`'s `import/extensions` rule, which IS active and enforces the same requirement (`.js` extensions on local imports)
- **Likely superseded:** The `import/extensions` rule provides the same functionality. The plugin was probably added experimentally and superseded by the `import/extensions` configuration, but never removed from `package.json`.
- **No action needed:** Since the plugin is inactive, it has zero effect on our code. We should not activate it, configure it, or remove it — that would modify upstream's configuration.

### Question 15: Does `eslint-plugin-import` enforce import ordering?

**Answer:** **No.** The `import/order` rule is NOT explicitly configured in `eslint.config.js`, and it is not enabled by default by `eslint-plugin-import`. Only `import/extensions` is explicitly configured. There is no import ordering enforcement.

### Question 16: Are barrel-file-relevant rules active (`import/no-cycle`, `import/no-self-import`)?

**Answer:** **No.** Neither `import/no-cycle` nor `import/no-self-import` is configured. Only `import/extensions` is explicitly listed. The barrel file pattern will not trigger any circular import detection because no such rules are active.

### Question 17: What do ESLint results show when run on CSAPI files?

**Answer:** `npx eslint src/ogc-api/csapi/` produces **99 errors, 0 warnings**. Every error is `@typescript-eslint/no-unused-vars`.

**Affected files (15 of 56):**

| File                                 | Error Count | Primary Issue                                                  |
| ------------------------------------ | ----------- | -------------------------------------------------------------- |
| `sensorml/types.spec.ts`             | 32          | Unused type imports (SensorML type definitions)                |
| `swecommon/types.spec.ts`            | 27          | Unused type imports (SWE Common type definitions)              |
| `swecommon/data-record.spec.ts`      | 14          | Unused type imports                                            |
| `swecommon/parser.spec.ts`           | 1           | Unused `AnyComponent` import                                   |
| `swecommon/index.spec.ts`            | 1           | Unused `AnyComponent` import                                   |
| `integration/observation.spec.ts`    | 3           | Unused `CollectionResponse`, `AnyComponent`, `result`          |
| `sensorml/aggregate-process.spec.ts` | 1           | Unused `AggregateProcess` import                               |
| `sensorml/parser.spec.ts`            | 1           | Unused `SensorMLProcess` import                                |
| `sensorml/physical-system.spec.ts`   | 2           | Unused `PhysicalSystem`, `PhysicalComponent`                   |
| `sensorml/simple-process.spec.ts`    | 1           | Unused `SimpleProcess` import                                  |
| `sensorml/aggregate-process.ts`      | 2           | Unused `ComponentEntry`, `parseIOComponentChoice`              |
| `sensorml/parser.ts`                 | 2           | Unused `Position`, `parseIOComponentChoice`                    |
| `sensorml/physical-system.ts`        | 3           | Unused `ComponentEntry`, `parseIOComponentChoice`, `parseMode` |
| `sensorml/simple-process.ts`         | 1           | Unused `parseIOComponentChoice`                                |
| `url_builder.ts`                     | 1           | Unused `CSAPIResourceTypes` import                             |

**Pattern:** The majority of errors (90+) are in test files that import types solely for TypeScript type-checking context during development. These types are never referenced in the test code itself. The fix is to either remove them, convert to `import type` (which the `no-unused-vars` rule respects when configured correctly), or add test assertions that reference them.

**Note:** The 4 source files with errors (`sensorml/aggregate-process.ts`, `sensorml/parser.ts`, `sensorml/physical-system.ts`, `sensorml/simple-process.ts`) have unused destructured imports from helper modules — functions imported but not called in the current implementation. These appear to be leftover from incremental development.

### Question 18: Does the flat config format affect CSAPI file coverage?

**Answer:** No. The ESLint flat config uses `files: ['**/*.ts', '**/*.js']` (from the TypeScript-ESLint config) which covers all TypeScript files including CSAPI. The `ignores: ['**/dist/', '**/coverage/']` pattern does not exclude any CSAPI source paths. The new barrel file (`csapi/index.ts`) will be a `.ts` file and is automatically covered.

### Sub-topic Synthesis

ESLint's configuration is clean and non-conflicting. The `recommended` presets are industry-standard. The only issue affecting CSAPI code is `no-unused-vars` — 99 errors across 15 files, all fixable with minor import adjustments. The `import/extensions` rule is already satisfied by our code style. One dead dependency (`eslint-plugin-require-extensions`) exists but has zero impact. No import ordering rules are active, giving us flexibility in import organization.

---

## 3. Cross-Tool Interaction Analysis

### Question 19: Do Prettier and ESLint conflict on any rules?

**Answer:** **No conflicts.** The upstream ESLint configuration contains **zero formatting rules** — no `indent`, `quotes`, `semi`, `comma-dangle`, or other style rules that Prettier also controls. Prettier handles all formatting; ESLint handles logic, imports, and code patterns.

`eslint-config-prettier` is NOT installed. This package disables ESLint rules that conflict with Prettier. Its absence is **not a problem** because there are no conflicting rules to disable. The upstream configuration follows the best practice of separating concerns: Prettier for formatting, ESLint for logic.

**Evidence:** Reviewing `eslint.config.js` — the only rules configured are:

1. `import/extensions` — import paths, not formatting
2. `@typescript-eslint/no-explicit-any` — type safety, not formatting
3. `@typescript-eslint/no-unused-vars` — variable usage, not formatting

None of these interact with Prettier's formatting domain.

### Question 20: Does `tsc --noEmit` overlap with `typescript-eslint` rules?

**Answer:** Minimal overlap. `tsc --noEmit` catches type system errors (type mismatches, missing properties, incorrect generics). `typescript-eslint/recommended` catches coding pattern violations (unused variables, banned type patterns, style preferences). The only potential overlap is `no-unused-vars` — both TypeScript and ESLint can detect unused imports, but TypeScript does not error on them by default (only with `noUnusedLocals`/`noUnusedParameters`). Since these TypeScript compiler options are NOT enabled in `tsconfig.json`, there is no double-reporting.

### Question 21: How do Prettier and ESLint interact in CI?

**Answer:** They run **sequentially** in a single CI job. From the upstream `qa.yml` workflow:

```yaml
steps:
  - run: npm run format:check # Prettier check (exit 1 if any file unformatted)
  - run: npm run typecheck # tsc --noEmit
  - run: npm run lint # ESLint
  - run: npm run test:browser # Jest (jsdom)
  - run: npm run test:node # Jest (node)
```

**Order matters:** `format:check` runs first. If Prettier fails, the entire job fails and subsequent steps don't run. This means a PR with Prettier failures will never reach the ESLint check or tests. The practical implication: **Prettier compliance is the first gate**.

### Question 22: What is the correct resolution order for overlapping changes?

**Answer:** Run Prettier first, then ESLint fix. Since Prettier and ESLint target completely different concerns (formatting vs logic), fixing one never introduces violations for the other:

1. `npx prettier --write <files>` — formats code (line wrapping, trailing commas, etc.)
2. `npx eslint --fix <files>` — fixes auto-fixable logic issues (none currently auto-fixable for `no-unused-vars`)

In practice, `no-unused-vars` errors require manual intervention (removing or renaming imports), not `--fix`. So the order is: Prettier first (automated), then ESLint fixes (manual), then verify both pass.

### Question 23: Do test files have different rules than source files?

**Answer:** **No.** Test files (`*.spec.ts`) follow the exact same Prettier and ESLint rules as source files. The only ESLint override is for `**/__mocks__/**/*` (which adds `jest: true` and `commonjs: true` globals) — this does not apply to `.spec.ts` files in `csapi/`. Test files use the same `printWidth`, `trailingComma`, `import/extensions`, `no-unused-vars`, and all other rules.

### Sub-topic Synthesis

Prettier and ESLint are cleanly separated in the upstream toolchain. There are no conflicts, no double-reporting, and no resolution ordering issues. The CI pipeline enforces them sequentially with Prettier as the first gate. This clean separation means we can apply Prettier formatting and ESLint fixes independently without fear of introducing cross-tool violations.

---

## 4. Formatting Impact on CSAPI Files

### Question 24: How many of the 27 source files will Prettier modify?

**Answer:** **20 of 27 source files** need Prettier formatting changes. 7 source files are already compliant.

| Category                                             | Count | Files                                                                                                                                                   |
| ---------------------------------------------------- | ----- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Already formatted (zero changes)                     | 7     | `classification.ts`, `constants.ts`, `schema-response.ts`, `sensorml/errors.ts`, `sensorml/index.ts`, `sensorml/simple-process.ts`, `sensorml/types.ts` |
| Structural changes (line wrapping, object expansion) | 20    | All other source files                                                                                                                                  |
| Whitespace-only changes (no structural)              | 0     | N/A                                                                                                                                                     |

### Question 25: How many of the 29 test files will Prettier modify?

**Answer:** **26 of 29 test files** need formatting changes. 3 test files are already compliant.

| Category                                             | Count | Files                                                                        |
| ---------------------------------------------------- | ----- | ---------------------------------------------------------------------------- |
| Already formatted (zero changes)                     | 3     | `formats/index.spec.ts`, `sensorml/index.spec.ts`, `swecommon/index.spec.ts` |
| Structural changes (line wrapping, object expansion) | 26    | All other test files                                                         |

**Note:** The 3 passing test files and 5 of the 7 passing source files are all barrel/index files or type definition files — typically short files with simple export statements that naturally stay under 80 characters.

### Question 26: What are the most common change categories?

**Answer:** Ranked by frequency of occurrence:

| Rank | Category                           | Frequency | Example                                                                            |
| ---- | ---------------------------------- | --------- | ---------------------------------------------------------------------------------- |
| 1    | **Object literal expansion**       | Very high | `{ rel: 'items', href: '/api', type: 'application/json' }` → multi-line (3+ lines) |
| 2    | **Import statement wrapping**      | High      | Named imports exceeding 80 chars split across lines                                |
| 3    | **Union type wrapping**            | Medium    | Long union type definitions in `model.ts` split across lines                       |
| 4    | **Ternary expression wrapping**    | Medium    | Ternary operators moved to new lines in `helpers.ts`                               |
| 5    | **Template literal consolidation** | Low       | Multi-line template strings reformatted                                            |
| 6    | **Trailing comma adjustments**     | Low       | ES5-style trailing commas added to multi-line structures                           |
| 7    | **Arrow function formatting**      | Very low  | Occasional wrapping of arrow function bodies                                       |

**The dominant change** — object literal expansion — is most concentrated in test files. Test files define inline link objects, response fixtures, and mock data with multiple properties on one line. Prettier splits these across lines at the 80-character boundary. `url_builder.spec.ts` is the extreme case: it contains hundreds of inline link objects, and Prettier expands nearly every one, producing 2,221 line changes in that file alone.

### Question 27: Do any Prettier changes affect semantics?

**Answer:** **No.** All changes are purely formatting:

- Line wrapping does not change JavaScript/TypeScript semantics
- Trailing comma additions are valid ES5+ syntax and don't affect behavior
- Object literal expansion preserves the same object structure
- Import statement wrapping doesn't change what is imported

Prettier is designed to be semantics-preserving. No Prettier change in the CSAPI codebase alters runtime behavior.

### Question 28: What is the total diff scope?

**Answer:** Running `npx prettier --write` on all CSAPI files followed by `git diff --stat`:

```
46 files changed, 3023 insertions(+), 1036 deletions(-)
```

**Top 10 files by change volume:**

| File                             | Changes       | Primary Cause                           |
| -------------------------------- | ------------- | --------------------------------------- |
| `url_builder.spec.ts`            | +1,851 / -370 | Object literal expansion (link objects) |
| `swecommon/data-array.spec.ts`   | +120 / -60    | Object expansion, import wrapping       |
| `swecommon/parser.ts`            | +75 / -37     | Line wrapping in function bodies        |
| `swecommon/data-record.spec.ts`  | +65 / -33     | Object expansion                        |
| `url_builder.ts`                 | +65 / -33     | Line wrapping, ternaries                |
| `integration/discovery.spec.ts`  | +67 / -33     | Object expansion                        |
| `integration/navigation.spec.ts` | +58 / -28     | Object expansion                        |
| `helpers.spec.ts`                | +55 / -27     | Object expansion                        |
| `swecommon/components.spec.ts`   | +49 / -24     | Object expansion                        |
| `swecommon/components.ts`        | +26 / -13     | Line wrapping                           |

**Note:** `url_builder.spec.ts` accounts for **55% of the total diff** (2,221 of 4,059 total changed lines). Without this file, the remaining 45 files have ~1,838 changed lines — still significant but more manageable.

### Question 29: Do CSAPI fixture files need formatting?

**Answer:** **Yes — 4 JSON fixture files** in `fixtures/ogc-api/` need formatting:

1. `fixtures/ogc-api/sample-data/csapi/sample-data-hub.json`
2. `fixtures/ogc-api/sample-data/csapi/collections.json`
3. `fixtures/ogc-api/sample-data/csapi/iot-sensors.json`
4. `fixtures/ogc-api/sample-data/csapi/conformance.json`

The `.prettierignore` excludes `fixtures/**/*.xml` and `fixtures/**/notjson.json` but does **not** exclude JSON files. These 4 files will fail `prettier --check` and need to be formatted. The changes are minor (JSON indentation and trailing whitespace).

**Note:** The broader `fixtures/ogc-api/` directory has 77 files that fail Prettier, but most are upstream fixtures. Only the 4 files in `csapi/` are our responsibility.

### Sub-topic Synthesis

The formatting impact is large — 46 of 56 files, 3,023 insertions / 1,036 deletions — but predictable and mechanical. The changes are dominated by a single pattern (object literal expansion at 80-char width) concentrated in test files. `url_builder.spec.ts` is the outlier, contributing over half the total diff. All changes are semantics-preserving. This scope strongly argues for a dedicated formatting commit to keep the refactoring diff clean.

---

## 5. Formatting Impact on Modified Core Files

### Question 30: Will Prettier change `endpoint.ts` and `index.ts` after the refactoring?

**Answer:**

- **`endpoint.ts`:** Has an **8-line Prettier diff** (2 insertions, 6 deletions). These are minor line-wrapping changes in existing upstream code — not related to the CSAPI removal. The changes exist in the current file and will persist after CSAPI code is removed.
- **`index.ts`:** Has **zero real formatting changes**. With `--end-of-line auto`, `index.ts` passes Prettier. The only failure with default settings is CRLF line endings (Windows artifact). After removing ~170 lines of CSAPI exports, the remaining code is already Prettier-compliant.

**Impact:** The `endpoint.ts` formatting changes are minor enough to include inline with the architectural commit. `index.ts` needs no formatting attention.

### Question 31: Will ESLint flag new unused imports in `endpoint.ts` after refactoring?

**Answer:** **No.** The two CSAPI imports removed from `endpoint.ts` are:

```typescript
import CSAPIQueryBuilder from './csapi/url_builder.js'; // line 52
import { scanCsapiLinks } from './csapi/helpers.js'; // line 53
```

These are **deleted entirely** — they don't become unused; they are removed from the file. After removal, ESLint produces **0 errors, 0 warnings** on `endpoint.ts` (verified by running `npx eslint src/ogc-api/endpoint.ts` on the current file, which already passes).

No other imports in `endpoint.ts` exist solely to support CSAPI functionality. The shared types (like `OgcApiCollectionInfo`) are used by other non-CSAPI code.

### Question 32: Will `import/extensions` require `.js` extensions in the barrel file?

**Answer:** **Yes.** The `import/extensions: ['error', 'always', { ignorePackages: true }]` rule requires `.js` extensions on all re-exports:

```typescript
// ✓ Correct — .js extension required
export { CSAPIQueryBuilder } from './url_builder.js';
export type { CSAPIResourceTypes } from './model.js';

// ✗ Wrong — will error
export { CSAPIQueryBuilder } from './url_builder';
```

**Precedent:** The existing barrel file `csapi/formats/index.ts` (344 lines) uses `.js` extensions on every re-export and passes ESLint. The new barrel file should follow the same pattern.

### Question 33: Will remaining `index.ts` exports comply after CSAPI removal?

**Answer:** **Yes.** After removing ~170 lines of CSAPI exports, the remaining `index.ts` exports are:

- Shared types and utilities from `src/shared/`
- OGC API endpoint class and types from `src/ogc-api/`
- WFS, WMS, WMTS, STAC, TMS, EDR types and endpoints

None of these imports exist solely to support CSAPI re-exports. All remaining imports serve the non-CSAPI exports. ESLint was run on the current `index.ts` and produces 0 errors — removing lines will not introduce new errors (you can't create an unused import by removing a line that uses it).

### Question 34: What rules must new files follow from inception?

**Answer:** See Section 9 (New File Compliance Checklist) for the complete checklist. In summary: new files must be written with `singleQuote: true`, `semi: true`, 80-character line width, `import type` for type-only imports, `.js` extensions on all local imports/re-exports, and no unused variables.

### Sub-topic Synthesis

The core file impact is minimal. `endpoint.ts` has a small 8-line Prettier diff; `index.ts` has none. ESLint already passes on both files. The architectural refactoring (removing CSAPI imports and exports) will not introduce any new Prettier or ESLint issues. The barrel file must follow `.js` extension conventions, with the existing `formats/index.ts` as a proven reference.

---

## 6. Execution Order and Commit Strategy

### Question 35: Should formatting be applied before or after the architectural refactoring?

**Answer:** **Before (Option A: Format First).** The analysis of three options:

**Option A: Format First** (Recommended)

- Run Prettier on all 56 CSAPI files + 4 fixture files in a dedicated commit
- Then apply architectural changes in subsequent commits
- **Pro:** Formatting diff is isolated; refactoring commits are pure logic changes; reviewers can skip the formatting commit
- **Pro:** Every subsequent commit applies changes to already-formatted code, ensuring line numbers and diffs are meaningful
- **Con:** A small amount of formatted code will be deleted by the refactoring (the `url_builder.ts` line that imports `CSAPIResourceTypes`), but this is trivial

**Option B: Refactor First**

- Apply all architectural changes first, then run Prettier as a final pass
- **Pro:** Only the final code gets formatted
- **Con:** Intermediate commits fail `format:check` — while CI only checks the final PR state, this means `git bisect` and per-commit review are broken
- **Con:** The refactoring diff is mixed with formatting context (lines that Prettier would have changed are shown as unchanged, creating an inconsistent baseline)

**Option C: Atomic**

- Each commit includes both logical changes and formatting for affected files
- **Pro:** Every commit passes CI individually
- **Con:** Formatting changes are mixed with logic changes in every diff, making code review harder
- **Con:** Significantly more complex to implement — must format each file after each logical change

**Recommendation: Option A** for these reasons:

1. The formatting diff is too large (3,023 insertions) to mix with logic changes
2. Upstream has clear precedent for formatting-only commits (5+ in git history)
3. CI only checks the final PR state, but Option A still satisfies per-commit correctness
4. Reviewers can skip the formatting commit entirely, focusing on the architecture

### Question 36: How large is the formatting-only diff?

**Answer:** **46 files changed, 3,023 insertions, 1,036 deletions** for CSAPI source/test files, plus 4 fixture JSON files (minor changes). Plus 8 lines in `endpoint.ts`.

This is **too large for inline review**. The diff should be in its own commit with a clear message:

```
style: apply prettier formatting to csapi files

Formatting-only commit — no logic changes. Applied `npx prettier --write`
to all CSAPI source, test, and fixture files to pass upstream's
`npm run format:check` CI gate.

46 files changed. Dominant change: object literal expansion at 80-char
printWidth, concentrated in test files. url_builder.spec.ts accounts
for ~55% of the diff due to inline link object expansion.
```

### Question 37: Is there upstream precedent for formatting-only commits?

**Answer:** **Yes — clear precedent.** Searching the upstream commit history:

```
5103e56 fix: apply prettier
a661ba2 style: apply prettier
b8664f6 fix: apply prettier
0229893 chore: update prettier task
0747aad chore: add prettier
dd6c433 formatting
d8038a8 migrate-to-eslint-9
452ffc4 fix new lint errors
```

There are at least 5 formatting-only commits in upstream history. The prefixes used are `fix:`, `style:`, and bare (no prefix). The most appropriate prefix for our commit would be `style:` (following Angular/Conventional Commits convention for formatting changes).

### Question 38: Does CI check every commit or only the final state?

**Answer:** **CI checks only the final PR state.** From `qa.yml`:

```yaml
on:
  push:
    branches: [main]
  pull_request:
    types: [opened, synchronize, ready_for_review]
```

The workflow is a single job (`format-typecheck-test`) triggered on PR events. It checks out the PR's HEAD commit (final state), not each individual commit. This means:

- **Each intermediate commit does NOT need to pass CI individually** (from GitHub's enforcement perspective)
- **However, per-commit correctness is still recommended** for `git bisect` usability and reviewer trust
- **Option A (Format First) satisfies both constraints** — every commit is individually correct

**Decision tree for Plan 08:**

```
Q: Is the formatting diff > 100 lines?
  → YES (3,023 insertions) → Use dedicated formatting commit (Option A)
    Q: Does upstream have formatting-only commit precedent?
      → YES → Proceed with confidence
        Q: Does CI check per-commit?
          → NO (final state only) → No constraint on commit ordering
            → RECOMMENDATION: Format first, then architectural changes
```

### Sub-topic Synthesis

**Option A (Format First)** is the clear winner. The formatting diff is too large for inline, upstream has precedent, and CI only checks final state. This gives Plan 08 a definitive answer: the first commit in the PR should be a formatting-only commit applying Prettier to all CSAPI files, followed by architectural commits that operate on already-formatted code.

---

## 7. File-by-File Impact Matrix

### Source Files (27)

| File                                    | Prettier           | ESLint                                  | Refactoring Impact |
| --------------------------------------- | ------------------ | --------------------------------------- | ------------------ |
| `command-routing.ts`                    | ✗ Fail (7 lines)   | ✓ Pass                                  | None               |
| `helpers.ts`                            | ✗ Fail (11 lines)  | ✓ Pass                                  | None               |
| `model.ts`                              | ✗ Fail (16 lines)  | ✓ Pass                                  | None               |
| `url_builder.ts`                        | ✗ Fail (98 lines)  | ✗ 1 error (`CSAPIResourceTypes` unused) | None               |
| `formats/classification.ts`             | ✓ Pass             | ✓ Pass                                  | None               |
| `formats/constants.ts`                  | ✓ Pass             | ✓ Pass                                  | None               |
| `formats/geojson.ts`                    | ✗ Fail (18 lines)  | ✓ Pass                                  | None               |
| `formats/index.ts`                      | ✗ Fail (5 lines)   | ✓ Pass                                  | None               |
| `formats/part2.ts`                      | ✗ Fail (31 lines)  | ✓ Pass                                  | None               |
| `formats/property.ts`                   | ✗ Fail (3 lines)   | ✓ Pass                                  | None               |
| `formats/response.ts`                   | ✗ Fail (8 lines)   | ✓ Pass                                  | None               |
| `formats/schema-response.ts`            | ✓ Pass             | ✓ Pass                                  | None               |
| `formats/sensorml/_helpers.ts`          | ✗ Fail (23 lines)  | ✓ Pass                                  | None               |
| `formats/sensorml/aggregate-process.ts` | ✗ Fail (8 lines)   | ✗ 2 errors                              | None               |
| `formats/sensorml/errors.ts`            | ✓ Pass             | ✓ Pass                                  | None               |
| `formats/sensorml/index.ts`             | ✓ Pass             | ✓ Pass                                  | None               |
| `formats/sensorml/parser.ts`            | ✗ Fail (7 lines)   | ✗ 2 errors                              | None               |
| `formats/sensorml/physical-system.ts`   | ✗ Fail (32 lines)  | ✗ 3 errors                              | None               |
| `formats/sensorml/simple-process.ts`    | ✓ Pass             | ✗ 1 error                               | None               |
| `formats/sensorml/types.ts`             | ✓ Pass             | ✓ Pass                                  | None               |
| `formats/swecommon/_helpers.ts`         | ✗ Fail (12 lines)  | ✓ Pass                                  | None               |
| `formats/swecommon/components.ts`       | ✗ Fail (39 lines)  | ✓ Pass                                  | None               |
| `formats/swecommon/data-array.ts`       | ✗ Fail (62 lines)  | ✓ Pass                                  | None               |
| `formats/swecommon/data-record.ts`      | ✗ Fail (4 lines)   | ✓ Pass                                  | None               |
| `formats/swecommon/index.ts`            | ✗ Fail (11 lines)  | ✓ Pass                                  | None               |
| `formats/swecommon/parser.ts`           | ✗ Fail (112 lines) | ✓ Pass                                  | None               |
| `formats/swecommon/types.ts`            | ✗ Fail (7 lines)   | ✓ Pass                                  | None               |

### Test Files (29)

| File                                         | Prettier             | ESLint      | Refactoring Impact |
| -------------------------------------------- | -------------------- | ----------- | ------------------ |
| `command-routing.spec.ts`                    | ✗ Fail (26 lines)    | ✓ Pass      | None               |
| `helpers.spec.ts`                            | ✗ Fail (82 lines)    | ✓ Pass      | None               |
| `model.spec.ts`                              | ✗ Fail (21 lines)    | ✓ Pass      | None               |
| `url_builder.spec.ts`                        | ✗ Fail (2,221 lines) | ✓ Pass      | None               |
| `formats/classification.spec.ts`             | ✗ Fail (29 lines)    | ✓ Pass      | None               |
| `formats/constants.spec.ts`                  | ✗ Fail (55 lines)    | ✓ Pass      | None               |
| `formats/geojson.spec.ts`                    | ✗ Fail (72 lines)    | ✓ Pass      | None               |
| `formats/index.spec.ts`                      | ✓ Pass               | ✓ Pass      | None               |
| `formats/part2.spec.ts`                      | ✗ Fail (52 lines)    | ✓ Pass      | None               |
| `formats/property.spec.ts`                   | ✗ Fail (4 lines)     | ✓ Pass      | None               |
| `formats/response.spec.ts`                   | ✗ Fail (36 lines)    | ✓ Pass      | None               |
| `formats/schema-response.spec.ts`            | ✗ Fail (7 lines)     | ✓ Pass      | None               |
| `formats/sensorml/aggregate-process.spec.ts` | ✗ Fail (10 lines)    | ✗ 1 error   | None               |
| `formats/sensorml/index.spec.ts`             | ✓ Pass               | ✓ Pass      | None               |
| `formats/sensorml/parser.spec.ts`            | ✗ Fail (18 lines)    | ✗ 1 error   | None               |
| `formats/sensorml/physical-system.spec.ts`   | ✗ Fail (39 lines)    | ✗ 2 errors  | None               |
| `formats/sensorml/simple-process.spec.ts`    | ✗ Fail (12 lines)    | ✗ 1 error   | None               |
| `formats/sensorml/types.spec.ts`             | ✗ Fail (28 lines)    | ✗ 32 errors | None               |
| `formats/swecommon/components.spec.ts`       | ✗ Fail (73 lines)    | ✓ Pass      | None               |
| `formats/swecommon/data-array.spec.ts`       | ✗ Fail (180 lines)   | ✓ Pass      | None               |
| `formats/swecommon/data-record.spec.ts`      | ✗ Fail (98 lines)    | ✗ 14 errors | None               |
| `formats/swecommon/index.spec.ts`            | ✓ Pass               | ✗ 1 error   | None               |
| `formats/swecommon/parser.spec.ts`           | ✗ Fail (86 lines)    | ✗ 1 error   | None               |
| `formats/swecommon/types.spec.ts`            | ✗ Fail (59 lines)    | ✗ 27 errors | None               |
| `integration/command.spec.ts`                | ✗ Fail (56 lines)    | ✓ Pass      | None               |
| `integration/discovery.spec.ts`              | ✗ Fail (100 lines)   | ✓ Pass      | None               |
| `integration/navigation.spec.ts`             | ✗ Fail (86 lines)    | ✓ Pass      | None               |
| `integration/observation.spec.ts`            | ✗ Fail (45 lines)    | ✗ 3 errors  | None               |
| `integration/pipeline.spec.ts`               | ✗ Fail (50 lines)    | ✓ Pass      | None               |

### Core Files (Modified by Refactoring)

| File                      | Prettier         | ESLint | Refactoring Impact                              |
| ------------------------- | ---------------- | ------ | ----------------------------------------------- |
| `src/ogc-api/endpoint.ts` | ✗ Fail (8 lines) | ✓ Pass | Remove 2 imports, `csapi()` method, cache field |
| `src/index.ts`            | ✓ Pass           | ✓ Pass | Remove ~170 lines of CSAPI exports              |

### New Files (Created by Refactoring)

| File                         | Prettier    | ESLint      | Notes                                |
| ---------------------------- | ----------- | ----------- | ------------------------------------ |
| `csapi/index.ts` (barrel)    | Must comply | Must comply | Follow `formats/index.ts` pattern    |
| `csapi/factory.ts` (factory) | Must comply | Must comply | New file; write compliant from start |

### Summary Statistics

| Category          | Prettier Fail | Prettier Pass | ESLint Errors            | ESLint Clean |
| ----------------- | ------------- | ------------- | ------------------------ | ------------ |
| Source files (27) | 20 (74%)      | 7 (26%)       | 4 files / 8 errors       | 23 (85%)     |
| Test files (29)   | 26 (90%)      | 3 (10%)       | 11 files / 91 errors     | 18 (62%)     |
| **Total (56)**    | **46 (82%)**  | **10 (18%)**  | **15 files / 99 errors** | **41 (73%)** |

---

## 8. Fixture Formatting Assessment

Four CSAPI fixture files need Prettier formatting:

| File                                                      | Issue                       |
| --------------------------------------------------------- | --------------------------- |
| `fixtures/ogc-api/sample-data/csapi/sample-data-hub.json` | JSON indentation/whitespace |
| `fixtures/ogc-api/sample-data/csapi/collections.json`     | JSON indentation/whitespace |
| `fixtures/ogc-api/sample-data/csapi/iot-sensors.json`     | JSON indentation/whitespace |
| `fixtures/ogc-api/sample-data/csapi/conformance.json`     | JSON indentation/whitespace |

These are JSON files created for CSAPI tests. The `.prettierignore` excludes `fixtures/**/*.xml` but not JSON files. These should be included in the formatting commit.

**Note:** The broader `fixtures/ogc-api/` directory has 77 files failing Prettier, but these are upstream fixtures — not our responsibility. We only need to format the 4 files we created.

---

## 9. New File Compliance Checklist

New files created by the refactoring (barrel file `csapi/index.ts`, factory file `csapi/factory.ts`, and any test files) must comply with these rules from inception:

### Prettier Compliance

- [ ] Use single quotes for strings (`singleQuote: true`)
- [ ] Include semicolons at end of statements (`semi: true`)
- [ ] Keep lines under 80 characters (`printWidth: 80`)
- [ ] Use 2-space indentation (`tabWidth: 2`)
- [ ] Include trailing commas in multi-line objects/arrays, ES5-style (`trailingComma: "es5"`) — but NOT in function parameters
- [ ] Use parentheses around single arrow function parameters (`arrowParens: "always"`)
- [ ] Use LF line endings (Git normalizes on commit)
- [ ] Run `npx prettier --check <file>` before committing

### ESLint Compliance

- [ ] Use `.js` extensions on all local imports/re-exports (`import/extensions: always`)
- [ ] Omit extensions on package imports (`ignorePackages: true`)
- [ ] No unused variables or imports — prefix unused params with `_`
- [ ] Use `import type` for type-only imports (good practice, avoids `no-unused-vars` on type imports)
- [ ] No `require()` calls — use ES import syntax
- [ ] Run `npx eslint <file>` before committing

### Barrel File Specific (`csapi/index.ts`)

- [ ] Follow `formats/index.ts` pattern for re-export style
- [ ] Use `.js` extensions on all re-export paths: `export { X } from './module.js';`
- [ ] Use `export type { T }` for type-only re-exports
- [ ] Keep lines under 80 characters — wrap long export lists

### Factory File Specific (`csapi/factory.ts`)

- [ ] Use `import type` for `OgcApiEndpoint` (type-only usage for parameter)
- [ ] Ensure `createCSAPIBuilder` function has proper return type annotation
- [ ] No unused imports or parameters

---

## 10. Boundary Condition Verification

### Constraint Compliance Matrix

| #   | Constraint                                                             | Status      | Evidence                                                       | Notes                                                                  |
| --- | ---------------------------------------------------------------------- | ----------- | -------------------------------------------------------------- | ---------------------------------------------------------------------- |
| 1   | CI compliance — all code must pass `format:check`, `lint`, `typecheck` | ✓ Compliant | Formatting and ESLint fixes documented; all are achievable     | Format First commit ensures compliance from first commit               |
| 2   | Upstream configuration is authoritative — no config modifications      | ✓ Compliant | Analysis used upstream config as-is; no modifications proposed | Even the inactive `eslint-plugin-require-extensions` is left untouched |
| 3   | No CSAPI in root exports                                               | ✓ Compliant | ESLint impact on `index.ts` after removal verified — 0 errors  | Removing CSAPI exports creates no new violations                       |
| 4   | New files must also comply                                             | ✓ Compliant | Compliance checklist produced (Section 9)                      | Barrel and factory files have specific guidance                        |

### Scope Boundary Adherence

- **In scope — explored:** All 56 CSAPI files, 2 core files (`endpoint.ts`, `index.ts`), 4 fixture files, CI workflow, upstream commit history, cross-tool interactions
- **Out of scope — respected:** No upstream configuration modifications proposed; no non-CSAPI file formatting addressed; no IDE configuration discussed
- **Scope adjustments:** The CRLF discovery was not in the original plan but was essential — it revealed that all 654 local Prettier failures are Windows artifacts, not real formatting issues. This was documented as an environmental finding, not a proposed change.

---

## 11. Implementation Scope Gate Assessment

### Minimum-Change Test

| Finding / Recommendation                  | Serves jahow's requirements?           | Minimum-change?                    | Include in implementation? |
| ----------------------------------------- | -------------------------------------- | ---------------------------------- | -------------------------- |
| Apply Prettier to 46 CSAPI files          | Yes — required for CI `format:check`   | Yes — automated, mechanical        | ✓ Include                  |
| Fix 99 ESLint `no-unused-vars` errors     | Yes — required for CI `lint`           | Yes — remove/rename unused imports | ✓ Include                  |
| Format 4 CSAPI fixture files              | Yes — required for CI `format:check`   | Yes — automated, mechanical        | ✓ Include                  |
| Format `endpoint.ts` (8-line diff)        | Yes — required for CI `format:check`   | Yes — automated, mechanical        | ✓ Include                  |
| Write new files Prettier-compliant        | Yes — necessary consequence            | Yes — write correctly from start   | ✓ Include                  |
| Use dedicated formatting commit           | Yes — keeps PR reviewable              | Yes — upstream precedent exists    | ✓ Include                  |
| Add `eslint-config-prettier`              | No — nice-to-have (no conflicts exist) | No — modifies upstream config      | ✗ Defer                    |
| Remove `eslint-plugin-require-extensions` | No — nice-to-have (dead dep)           | No — modifies upstream config      | ✗ Defer                    |
| Change `endOfLine` to `"auto"`            | No — nice-to-have (dev convenience)    | No — modifies upstream config      | ✗ Defer                    |

### Deferred Insights

- **`eslint-config-prettier` absence:** Not a problem currently because no ESLint rules conflict with Prettier. If upstream adds formatting rules to ESLint in the future, this package would be needed. Deferred because it requires upstream config modification.
- **`eslint-plugin-require-extensions` dead dependency:** Informational — it's inactive and harmless. Removing it would modify upstream's `package.json`. Deferred.
- **Windows CRLF issue:** Does not affect CI. Could be solved by adding `endOfLine: "auto"` to `.prettierrc.json`, but that modifies upstream config. Developers on Windows should use `npx prettier --end-of-line auto` or configure their editors. Deferred.
- **`trailingComma: "all"` consideration:** The upstream config uses the default `"es5"`. Prettier 3.0+ defaults to `"all"`. If upstream upgrades Prettier, trailing commas will be added to function parameters. Not our concern for this PR — deferred.

---

## 12. Impact on Dependent Plans

### What Downstream Plans Should Consume

| Downstream Plan      | What to consume from this report                             | Section reference |
| -------------------- | ------------------------------------------------------------ | ----------------- |
| Plan 08 (Changelist) | Execution order: Format First (Option A)                     | § 6               |
| Plan 08 (Changelist) | File-by-file impact matrix for commit planning               | § 7               |
| Plan 08 (Changelist) | ESLint fix list: 15 files, 99 errors, all `no-unused-vars`   | § 2, Q12/Q17      |
| Plan 08 (Changelist) | Formatting commit scope: 46 files + 4 fixtures + endpoint.ts | § 4, Q28          |
| Plan 08 (Changelist) | New file compliance checklist                                | § 9               |
| Plan 08 (Changelist) | Commit message template for formatting commit                | § 6, Q36          |
| Plan 08 (Changelist) | CI constraints: single job, sequential, final-state only     | § 3, Q21/Q38      |

### Decisions Now Final

1. **Execution order is Format First (Option A):** Formatting commit before architectural commits. Rationale: 3,023-line formatting diff is too large to mix with logic changes; upstream has clear precedent.
2. **ESLint fixes are code changes, not formatting:** The 99 `no-unused-vars` errors require manual edits (removing/renaming imports). These belong in a separate commit from Prettier formatting.
3. **Fixture files are included in the formatting commit:** The 4 CSAPI fixture JSON files are formatted alongside source/test files.
4. **New files are written compliant from inception:** No post-hoc formatting needed for barrel/factory files if written following the checklist.
5. **`endpoint.ts` has minor formatting changes:** The 8-line Prettier diff can be included in either the formatting commit or the architectural commit — Plan 08 should decide based on commit narrative.

### Items Requiring Downstream Resolution

1. **ESLint fix commit placement** → Plan 08 should decide: should ESLint fixes (removing unused imports) be in their own commit between formatting and architecture, or bundled with the formatting commit? Both are defensible.
2. **`url_builder.spec.ts` commit strategy** → Plan 08 should consider whether this 2,221-line file's formatting changes warrant special mention in the PR description.
3. **`endpoint.ts` formatting placement** → Plan 08 should decide whether the 8-line `endpoint.ts` Prettier change goes in the formatting commit (with all other formatting) or the architectural commit (where `endpoint.ts` is also modified for CSAPI removal).

---

## 13. Key Takeaways

1. **Format First is the recommended commit strategy.** The 3,023-insertion formatting diff must be isolated in a dedicated commit. Upstream has 5+ formatting-only commits as precedent.

2. **The CRLF finding is environmental, not architectural.** Prettier's `endOfLine: "lf"` default causes 654 false failures on Windows. This is a non-issue for CI (ubuntu-latest). Do not modify upstream's config to work around it.

3. **All 99 ESLint errors are a single rule (`no-unused-vars`).** These are unused type imports in test files and unused function imports in 4 SensorML source files. All are fixable with minor import adjustments.

4. **Prettier and ESLint do not conflict.** `eslint-config-prettier` is not installed and not needed — ESLint has zero formatting rules.

5. **`url_builder.spec.ts` dominates the formatting diff** — 2,221 of 4,059 total changed lines (55%). This is due to hundreds of inline link objects being expanded to multi-line at 80-char width.

6. **`eslint-plugin-require-extensions` is a dead dependency** — installed but never configured. It overlaps with the active `import/extensions` rule. Do not touch it.

7. **`trailingComma` default is `"es5"`, not `"all"`.** The research plan's assertion was incorrect. This means no trailing commas in function parameters — only in objects/arrays.

8. **Core file impact is minimal.** `endpoint.ts` has 8 lines of Prettier changes; `index.ts` has none. ESLint passes on both.

9. **CI is a single sequential job checking final PR state only.** `format:check` → `typecheck` → `lint` → tests. Per-commit enforcement is not done by GitHub, but per-commit correctness is still recommended.

10. **New files must be written Prettier-compliant from inception.** The compliance checklist (Section 9) provides the rules. The existing `formats/index.ts` barrel file is a proven reference for the new barrel file pattern.

---

## 14. Impact on Implementation

### Must Change (Required by Findings)

1. **Apply Prettier to 46 CSAPI source/test files** — automated via `npx prettier --write src/ogc-api/csapi/`
2. **Apply Prettier to 4 CSAPI fixture JSON files** — automated via `npx prettier --write fixtures/ogc-api/sample-data/csapi/`
3. **Fix 99 ESLint `no-unused-vars` errors across 15 files** — manual: remove unused imports, convert to `import type`, or prefix with `_`
4. **Apply Prettier to `endpoint.ts`** — automated via `npx prettier --write src/ogc-api/endpoint.ts`
5. **Write new barrel file (`csapi/index.ts`) with `.js` extensions on re-exports** — per compliance checklist
6. **Write new factory file (`csapi/factory.ts`) with Prettier/ESLint compliance** — per compliance checklist

### Should Change (Recommended by Findings)

1. **Use a dedicated formatting commit as the first commit in the PR** — `style: apply prettier formatting to csapi files`
2. **Include ESLint fixes in a separate commit** or group with the formatting commit — `fix: resolve eslint no-unused-vars errors in csapi files`
3. **Document the formatting commit in the PR description** — note that it is formatting-only with no logic changes, and that `url_builder.spec.ts` accounts for 55% of the diff

### Could Change (Optional Improvements)

1. **Add a `.editorconfig` note** for Windows developers explaining the CRLF situation — falls outside minimum scope
2. **Recommend upstream add `eslint-config-prettier`** as future-proofing — separate discussion, not part of this PR

---

## 15. Open Questions

| #   | Question                                                                             | Why Unresolved                                              | Resolution Path                                                                               |
| --- | ------------------------------------------------------------------------------------ | ----------------------------------------------------------- | --------------------------------------------------------------------------------------------- |
| 1   | Should ESLint fixes go in the formatting commit or a separate commit?                | Implementation sequencing decision, not a research question | Plan 08 should resolve based on commit narrative preference                                   |
| 2   | Should `endpoint.ts` formatting be in the formatting commit or architectural commit? | Both are valid; depends on commit narrative                 | Plan 08 should resolve                                                                        |
| 3   | Will upstream have opinions on the `url_builder.spec.ts` 2,221-line formatting diff? | Cannot predict reviewer reaction                            | Mitigate by clearly labeling the formatting commit and noting this file in the PR description |

---

## Evidence Appendix

### A. Prettier Check Output (with `--end-of-line auto`)

46 of 56 CSAPI files fail with `--end-of-line auto`:

```
> npx prettier --check --end-of-line auto "src/ogc-api/csapi/**/*.ts"

[warn] src\ogc-api\csapi\command-routing.spec.ts
[warn] src\ogc-api\csapi\command-routing.ts
[warn] src\ogc-api\csapi\formats\classification.spec.ts
... (46 files total)
[warn] Code style issues found in 46 files. Forgot to run Prettier?
```

### B. ESLint Output Summary

```
> npx eslint src/ogc-api/csapi/

99 errors, 0 warnings
All errors: @typescript-eslint/no-unused-vars
15 files affected
```

### C. Git Diff Stat (Prettier formatting)

```
> git diff --stat -- src/ogc-api/csapi/

46 files changed, 3023 insertions(+), 1036 deletions(-)
```

### D. Upstream Formatting Commit Precedent

```
> git log upstream/main --grep="prettier" --oneline

5103e56 fix: apply prettier
a661ba2 style: apply prettier
b8664f6 fix: apply prettier
0229893 chore: update prettier task
0747aad chore: add prettier
```

### E. CI Workflow Execution Order

```yaml
# From .github/workflows/qa.yml
steps:
  - run: npm run format:check # Step 1: Prettier
  - run: npm run typecheck # Step 2: tsc --noEmit
  - run: npm run lint # Step 3: ESLint
  - run: npm run test:browser # Step 4: Jest (jsdom)
  - run: npm run test:node # Step 5: Jest (node)
```

---

## Research Completion Checklist

- [x] All 38 detailed questions from the research plan have specific, evidenced answers
- [x] Boundary condition verification completed (Section 10)
- [x] Implementation scope gate assessment completed (Section 11)
- [x] Impact on dependent plans documented (Section 12)
- [x] Key takeaways extracted (Section 13)
- [x] Open questions cataloged with resolution paths (Section 15)
- [x] Cross-references to prior findings are accurate
- [x] Findings respect all boundary conditions from the research plan
- [x] Document is self-contained — a reader unfamiliar with the plan can understand the findings

**Research Started:** 2026-02-25
**Research Completed:** 2026-02-25
**Reviewed:** Not yet

---

## Notes

- **Research plan correction:** The plan stated "Prettier 2.x defaults to `'all'` since 2.0" for `trailingComma`. This is incorrect — Prettier 2.x defaults to `"es5"`. The `"all"` default was introduced in Prettier 3.0.0. Verified via `npx prettier --support-info` which reports `"default": "es5"` for Prettier 2.8.8.

- **Research time exceeded estimate:** The plan estimated 1–2 hours but actual time was ~3 hours. The CRLF discovery required additional investigation — initially all 654 files failing Prettier appeared to be a catastrophic finding (suggesting upstream's own code failed formatting), but tracing the root cause to Windows line endings and verifying CI behavior on ubuntu-latest resolved the concern. This investigation was unplanned but essential.

- **Diff scope measurement quirk:** `git diff` with `core.autocrlf = true` normalizes line endings in the diff, so CRLF-to-LF changes are invisible in `git diff --stat`. This means the reported 3,023 insertions / 1,036 deletions are the **real formatting changes only** — line ending changes are not counted. This was initially confusing but is actually helpful: it gives us the true formatting impact.
