# Phase 0: Baseline Assessment

**Purpose:** Record the inherited state of the forked repository before any CSAPI implementation work begins. This document establishes a "before" snapshot so that during Phases 1-4, any test failure or build issue can be compared against this baseline to determine whether it is a pre-existing upstream condition or a CSAPI regression.

**Date:** February 14, 2026  
**Assessed by:** AI assistant (GitHub Copilot, Claude Opus 4.6)  
**Repository:** `OS4CSAPI/ogc-client-CSAPI_2` (fork of `camptocamp/ogc-client`)  
**HEAD at time of assessment:** `862de47` (main branch)

> **⚠️ Scope disclaimer:** This assessment documents inherited state only. Any failures, warnings, or vulnerabilities reported here are **pre-existing upstream conditions**. This project is not responsible for identifying, diagnosing, or fixing upstream issues. This document exists solely to distinguish pre-existing conditions from CSAPI regressions.

---

## 1. Environment

| Component | Version                            |
| --------- | ---------------------------------- |
| Node.js   | v25.6.1                            |
| npm       | 11.9.0                             |
| OS        | Windows                            |
| Package   | `@camptocamp/ogc-client@1.3.1-dev` |

---

## 2. Dependency Installation (`npm install`)

**Command:** `npm install`  
**Result:** ✅ Success (dependencies already up to date)

```
up to date, audited 745 packages in 3s
153 packages are looking for funding
15 vulnerabilities (1 low, 10 moderate, 3 high, 1 critical)
```

### Security Audit Summary

**Total vulnerabilities:** 15 (1 low, 10 moderate, 3 high, 1 critical)

| Severity | Package                         | Advisory                                        |
| -------- | ------------------------------- | ----------------------------------------------- |
| Critical | form-data 4.0.0-4.0.3           | GHSA-fjxv-7rqg-78g4 — unsafe random in boundary |
| High     | rollup 4.0.0-4.22.3             | GHSA-gcx4-mw62-g8wm — DOM clobbering XSS        |
| High     | validator ≤13.15.20             | GHSA-9965-vmph-33xx — URL validation bypass     |
| High     | validator ≤13.15.20             | GHSA-vghf-hv5q-vc2g — incomplete filtering      |
| High     | ws 8.0.0-8.17.0                 | GHSA-3h5v-q93c-6h6q — DoS via HTTP headers      |
| Moderate | brace-expansion (4 instances)   | GHSA-v6h2-p8h4-qcjw — ReDoS                     |
| Moderate | esbuild ≤0.24.2                 | GHSA-67mh-4wv8-2f99 — dev server request access |
| Moderate | js-yaml (2 instances)           | GHSA-mh29-5h37-fv8m — prototype pollution       |
| Moderate | lodash 4.0.0-4.17.21            | GHSA-xxjr-mmjv-4gpg — prototype pollution       |
| Moderate | nanoid <3.3.8                   | GHSA-mwcw-c2x4-8c55 — predictable generation    |
| Moderate | vite ≤6.1.6                     | Depends on vulnerable esbuild                   |
| Moderate | vue-template-compiler ≥2.0.0    | GHSA-g3ch-rx76-35fx — XSS                       |
| Moderate | word-wrap <1.2.4                | GHSA-j8xg-fqg3-53r7 — ReDoS                     |
| Low      | brace-expansion (covered above) | Second advisory instance                        |

**Assessment:** All vulnerabilities are in upstream dependencies. None are introduced by our fork. Most have fixes available via `npm audit fix` but we are not running that — dependency updates are an upstream concern.

---

## 3. Test Suite (`npm test`)

The test suite runs in two modes: browser (jsdom) and node.

### 3.1 Browser Tests (`npm run test:browser`)

**Command:** `jest` (jsdom environment)  
**Result:** ❌ 2 test suites failed, 26 passed (28 total); 5 tests failed, 322 passed (327 total)

#### Failure 1: `src/ogc-api/endpoint.spec.ts`

**Test:** `OgcApiEndpoint › a failure happens while parsing the endpoint capabilities › #info › throws an explicit error`

**Root cause:** The test asserts `rejects.toEqual(new EndpointError(...))` but the thrown error is a plain `Error`, not an `EndpointError`. The error message content matches but the class/prototype does not. This is a pre-existing upstream issue — the error wrapping in the endpoint code does not preserve the `EndpointError` type in this specific code path.

```
Expected: [EndpointError: The endpoint appears non-conforming...]
Received: [Error: The endpoint appears non-conforming...]
```

#### Failure 2: `src/shared/http-utils.spec.ts`

**Test:** `HTTP utils › fetch options › used in worker › is used in the fetch() call`

**Root cause:** Timeout (5000ms exceeded). The worker-related test depends on esbuild resolving `src/worker/worker.ts` which fails with a path resolution error on Windows:

```
Could not resolve "C:UserssbollingDocumentsogc-client-CSAPI_2srcworker/worker.ts"
```

This is a **Windows-specific path handling issue** in the esbuild worker build step — backslashes are stripped from the path. The same esbuild error appears as a non-fatal `X [ERROR]` in several other passing test suites but only causes a test failure in `http-utils.spec.ts` where the worker is actually exercised.

**Additional browser failures (4 tests):** All 4 additional test failures in the browser suite are within `http-utils.spec.ts`, caused by the same worker path resolution timeout. The other `X [ERROR]` messages in endpoint/capabilities tests are non-fatal warnings.

### 3.2 Node Tests (`npm run test:node`)

**Command:** `jest --config jest.node.config.cjs`  
**Result:** ❌ 1 test suite failed, 30 passed (31 total); 1 test failed, 4 skipped, 401 passed (406 total)

#### Failure: `src/ogc-api/endpoint.spec.ts`

**Test:** Same `EndpointError` vs `Error` class mismatch as browser tests. Identical failure in both environments.

### 3.3 Test Summary

| Environment     | Suites | Pass | Fail | Tests | Pass | Fail | Skip |
| --------------- | ------ | ---- | ---- | ----- | ---- | ---- | ---- |
| Browser (jsdom) | 28     | 26   | 2    | 327   | 322  | 5    | 0    |
| Node            | 31     | 30   | 1    | 406   | 401  | 1    | 4    |

**Pre-existing failures:**

| #   | Test                                                  | Environment  | Root Cause                                | Upstream Issue     |
| --- | ----------------------------------------------------- | ------------ | ----------------------------------------- | ------------------ |
| 1   | `endpoint.spec.ts` — `#info throws an explicit error` | Both         | `Error` vs `EndpointError` class mismatch | Error wrapping bug |
| 2   | `http-utils.spec.ts` — worker fetch options (4 tests) | Browser only | Windows esbuild path resolution           | Platform-specific  |

**CSAPI impact:** None. These failures are in `src/ogc-api/endpoint.spec.ts` and `src/shared/http-utils.spec.ts` — neither file is modified by CSAPI until Phase 1 Task 4 (Issue #4), and the `endpoint.spec.ts` failure is in an error-handling path unrelated to our CSAPI factory method additions. The worker path issue is entirely in the Web Worker infrastructure which CSAPI does not use.

---

## 4. Build (`npm run build`)

The build has three steps: `build:worker`, `build:node`, `build:browser`.

### 4.1 build:worker

**Command:** `vite build --config vite.worker-config.js`  
**Result:** ✅ Success

```
vite v5.1.0 building for production...
✓ 10 modules transformed.
dist/worker/index.js  147.79 kB │ gzip: 38.06 kB
Declaration files built in 2997ms.
✓ built in 3.44s
```

### 4.2 build:node

**Command:** `vite build --config vite.node-config.js`  
**Result:** ✅ Success

```
vite v5.1.0 building SSR bundle for production...
✓ 90 modules transformed.
dist/dist-node.js  315.12 kB
✓ built in 730ms
```

### 4.3 build:browser

**Command:** `esbuild $(find ./src ...) --outdir=./dist --platform=neutral --format=esm --sourcemap`  
**Result:** ❌ Failure (Windows-only)

```
X [ERROR] Invalid build flag: "-name"
```

**Root cause:** The `build:browser` script in `package.json` uses a bash `$(find ...)` subshell command that is not compatible with Windows PowerShell/cmd. The `find` command is a Unix utility; on Windows, `find` is a different program (text search), and `$(...)` subshell syntax is not supported in npm scripts on Windows.

**Assessment:** This is a **platform-specific build script issue** inherited from upstream. The upstream project assumes a Unix/macOS/WSL development environment for the full build. The `build:worker` and `build:node` steps work on Windows; only `build:browser` fails due to the shell command syntax.

**CSAPI impact:** None. CSAPI source files will be automatically included in `build:worker` and `build:node` via Vite's module resolution from `src/index.ts`. The `build:browser` step would need to enumerate CSAPI `.ts` files in its `find` command, but since the entire step doesn't work on Windows, this is moot. When running the full build in CI (Linux), CSAPI files will be picked up automatically.

---

## 5. Lint (`npx eslint .`)

**Command:** `npx eslint .`  
**Result:** ✅ Clean (no warnings, no errors)

---

## 6. Upstream Sync Status

| Metric                    | Value                                                        |
| ------------------------- | ------------------------------------------------------------ |
| Fork source               | `camptocamp/ogc-client`                                      |
| Fork point commit         | `53a6449` (Merge pull request #132 from camptocamp/fix-bbox) |
| Fork point date           | December 17, 2025                                            |
| Commits behind upstream   | **0**                                                        |
| Commits ahead of upstream | **436** (all are CSAPI planning/docs commits)                |

**Assessment:** ✅ Fully synced. Upstream has had zero new commits since our fork point (`53a6449`). No merge conflicts possible. The 436 commits ahead are all documentation additions in `docs/` — no source code modifications.

---

## 7. Jest Configuration Compatibility

**Files reviewed:** `jest.config.cjs`, `jest.node.config.cjs`

**Key configuration:**

- Test discovery: Automatic (no explicit `testMatch` or `testPathPattern` restricting to specific directories)
- Module name mapper: `'^(..?/.+)\\.c?jsx?$': '$1'` (handles `.js` extension imports)
- Transform: TypeScript via custom transformer (`jest.ts-transformer.cjs`)
- Setup files: `test-setup.ts` (browser), `test-setup.node.ts` (node)

**CSAPI compatibility:** ✅ No changes needed. Jest will automatically discover test files in `src/ogc-api/csapi/` because there are no path restrictions in the configuration. The module name mapper already handles `.js` extension imports which CSAPI will use.

---

## 8. Summary

### Baseline State

| Check                | Result        | Pre-existing Issues                                 |
| -------------------- | ------------- | --------------------------------------------------- |
| `npm install`        | ✅ Pass       | 15 dependency vulnerabilities (upstream)            |
| `npm test` (browser) | ❌ 5 failures | EndpointError class mismatch + Windows esbuild path |
| `npm test` (node)    | ❌ 1 failure  | EndpointError class mismatch                        |
| `build:worker`       | ✅ Pass       | None                                                |
| `build:node`         | ✅ Pass       | None                                                |
| `build:browser`      | ❌ Fail       | Windows shell command incompatibility               |
| `npx eslint .`       | ✅ Pass       | None                                                |
| Upstream sync        | ✅ Current    | 0 commits behind                                    |
| Jest config          | ✅ Compatible | No changes needed for CSAPI paths                   |

### Pre-existing Issues (inherited, not our responsibility)

1. **`EndpointError` class mismatch** — `endpoint.spec.ts` line 1789: test expects `EndpointError` but receives plain `Error`. Fails in both browser and node environments. Pre-existing upstream bug in error wrapping.

2. **Windows esbuild path resolution** — Worker tests in `http-utils.spec.ts` timeout because esbuild cannot resolve the worker path on Windows (backslashes stripped). Affects 4 browser-environment tests only. Platform-specific issue.

3. **`build:browser` Windows incompatibility** — Build script uses bash `$(find ...)` syntax incompatible with Windows shells. Only affects the browser ESM build step; worker and node builds succeed.

4. **15 dependency vulnerabilities** — All in upstream transitive dependencies. Range from moderate (ReDoS, prototype pollution) to critical (unsafe random in form-data). Not introduced by our fork.

### Go/No-Go for CSAPI Implementation

**Decision: ✅ GO**

None of the pre-existing issues block CSAPI implementation:

- The `EndpointError` test failure is unrelated to our code paths
- The worker path issue is Windows-specific and CSAPI doesn't use workers
- The `build:browser` failure is a Windows shell issue; CI runs on Linux
- The dependency vulnerabilities are upstream concerns
- Jest will discover CSAPI tests automatically — no config changes needed
- Upstream is fully synced — no merge conflicts ahead

**Regression baseline established.** Any new test failure after Phase 1 begins should be compared against this document. If a failure matches one listed above, it is pre-existing and not a CSAPI regression.

---

## Version History

| Version | Date              | Change                      |
| ------- | ----------------- | --------------------------- |
| 1.0     | February 14, 2026 | Initial baseline assessment |
