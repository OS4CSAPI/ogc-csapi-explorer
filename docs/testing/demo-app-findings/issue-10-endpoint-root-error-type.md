# Issue #10 Findings Report — Fix endpoint.ts root getter to throw EndpointError instead of plain Error (F-5)

> **Date:** 2026-02-17
> **Issue:** [OS4CSAPI/ogc-csapi-explorer#10](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/10) — "Fix endpoint.ts root getter to throw EndpointError instead of plain Error (F-5)"
> **Repository under review:** `OS4CSAPI/ogc-client-CSAPI_2` (`src/ogc-api/endpoint.ts`)
> **Labels:** bug

---

## Table of Contents

1. [AI Operational Constraints Acknowledgment](#1-ai-operational-constraints-acknowledgment)
2. [Executive Summary](#2-executive-summary)
3. [Issue Description](#3-issue-description)
4. [Source Code Review](#4-source-code-review)
5. [Reference Document Review](#5-reference-document-review)
6. [Risk Assessment](#6-risk-assessment)
7. [Analysis: Error Type Consistency](#7-analysis-error-type-consistency)
8. [Recommendation](#9-recommendation)
9. [Appendix A: Authority Precedence Analysis](#appendix-a-authority-precedence-analysis)
10. [Appendix B: Cross-Reference Matrix](#appendix-b-cross-reference-matrix)

---

## 1. AI Operational Constraints Acknowledgment

Per the [AI Operational Constraints](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/governance/AI_OPERATIONAL_CONSTRAINTS.md), this review follows the required authority precedence:

1. **OGC specifications** — primary authority
2. **AI Collaboration Agreement** — governing constraints
3. **Issue description** — task scope
4. **Existing code patterns** — implementation precedent
5. **Conversation context** — supplementary guidance

This report does not propose behavioral modifications to the library without approval. All recommendations distinguish between **fact** (verified), **inference** (reasoned), and **proposal** (requires approval), per Section 3 of the constraints.

---

## 2. Executive Summary

**Issue #10 identifies a genuine, pre-existing one-word bug in the upstream `ogc-client` library where `endpoint.ts` line 75 throws `new Error(...)` instead of `new EndpointError(...)`. The fix is trivial, no-risk, and aligns the production code with both the existing test expectation and the library's established error hierarchy.**

| Aspect                           | Assessment                                                                                                                                     |
| -------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| **Change type**                  | Bug fix — error constructor mismatch                                                                                                           |
| **Scope**                        | One word: `Error` → `EndpointError` on line 75 of `endpoint.ts`                                                                                |
| **Production behavior modified** | Yes — the thrown error is now an `EndpointError` instance instead of `Error`                                                                   |
| **Existing tests affected**      | Yes — **positively**; the test at `endpoint.spec.ts` L1791 already expects `EndpointError` and currently fails due to this bug                 |
| **Risk to library integrity**    | **None** — the import already exists, every other throw in the same file uses `EndpointError`, and the test explicitly expects `EndpointError` |
| **Pre-existing upstream bug**    | Yes — this bug predates all CSAPI work                                                                                                         |
| **Estimated effort**             | One-word change on one line                                                                                                                    |

**Key findings from this review:**

1. **Fact:** The `root` getter (line 75) is the **only** place in `endpoint.ts` that throws a plain `Error`. All five other throws in the class (lines 344, 387, 442, 482) use `EndpointError`.

2. **Fact:** The `EndpointError` import already exists at line 38: `import { EndpointError } from '../shared/errors.js'`. No new imports are needed.

3. **Fact:** The test at `endpoint.spec.ts` L1791 expects `new EndpointError(...)`. This test is currently broken (fails) because the production code throws `new Error(...)` instead.

4. **Fact:** This bug was discovered during the EndpointError isolation testing documented in the [endpoint-error-isolation-report](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/endpoint-error-isolation-report.md) (Finding F).

5. **Fact:** This is ranked as finding **F-5** in the [upstream findings document](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/upstream-findings.md), priority #11 (Low severity). The low severity is because the error message and behavior are identical — only the constructor type is wrong.

---

## 3. Issue Description

### 3.1 Origin: Finding F-5

Issue #10 corresponds to **Finding F-5** from the [upstream findings document](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/upstream-findings.md). It was first identified as **Finding F** in the [EndpointError Isolation Report](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/endpoint-error-isolation-report.md) during test verification of the EndpointError extraction refactor.

### 3.2 The Bug

The `root` private getter in `OgcApiEndpoint` catches errors from `fetchRoot()` and re-throws them. However, it uses `new Error(...)` instead of `new EndpointError(...)`:

```typescript
// endpoint.ts L72-80
private get root(): Promise<OgcApiDocument> {
  if (!this.root_) {
    this.root_ = fetchRoot(this.baseUrl).catch((e) => {
      throw new Error(`The endpoint appears non-conforming, the following error was encountered:
${e.message}`);
    });
  }
  return this.root_;
}
```

### 3.3 The Mismatch

|                                                             | Production Code (L75) | Test Expectation (L1791) |
| ----------------------------------------------------------- | --------------------- | ------------------------ |
| Error constructor                                           | `new Error(...)`      | `new EndpointError(...)` |
| `instanceof EndpointError`                                  | `false`               | `true` (expected)        |
| Catchable by `catch(e) { if (e instanceof EndpointError) }` | **No** — missed       | **Yes** — expected       |

### 3.4 Why This Matters

A consumer who catches `EndpointError` specifically — the documented error type for endpoint-level failures — will **miss** this particular error because it is a plain `Error`. The error message is identical; only the constructor is wrong. Any consumer code like this will silently fail to handle the error:

```typescript
try {
  const info = await endpoint.info;
} catch (e) {
  if (e instanceof EndpointError) {
    // This branch is NEVER reached for the root getter failure
    handleEndpointFailure(e);
  }
}
```

---

## 4. Source Code Review

### 4.1 `endpoint.ts` — All EndpointError Usage (L38, L72–80, L344, L387, L442, L482)

**Import (L38):**

```typescript
import { EndpointError } from '../shared/errors.js';
```

**The buggy line (L75) — the ONLY throw using plain `Error`:**

```typescript
throw new Error(`The endpoint appears non-conforming, the following error was encountered:
${e.message}`);
```

**All other throws in the same class — correctly use `EndpointError`:**

| Line | Context                           | Code                                                                        |
| ---- | --------------------------------- | --------------------------------------------------------------------------- |
| 344  | `edr()` method — no EDR support   | `throw new EndpointError('Endpoint does not support EDR')`                  |
| 387  | `csapi()` method — no CSA support | `throw new EndpointError('Endpoint does not support Connected Systems...')` |
| 442  | Collection lookup — not found     | `throw new EndpointError(\`Collection not found: ${collectionId}\`)`        |
| 482  | Style lookup — not found          | `throw new EndpointError(\`Style not found: "${styleId}".\`)`               |

**Assessment:** Line 75 is clearly an oversight. Every other throw in the class uses `EndpointError`. The import exists. The test expects `EndpointError`. This is a textbook one-line bug.

### 4.2 `endpoint.spec.ts` — Test Expectations (L1783–1797)

```typescript
describe('a failure happens while parsing the endpoint capabilities', () => {
  beforeEach(() => {
    endpoint = new OgcApiEndpoint('http://local/sample-data/notjson');
  });
  describe('#info', () => {
    it('throws an explicit error', async () => {
      await expect(endpoint.info).rejects.toEqual(
        new EndpointError(
          `The endpoint appears non-conforming, the following error was encountered:
The document at http://local/sample-data/notjson?f=json does not appear to be valid JSON. ...`
        )
      );
    });
  });
});
```

**Assessment:** The test uses `rejects.toEqual(new EndpointError(...))`. Jest's `toEqual` performs a deep equality check including the constructor. Because the production code throws `new Error(...)` (which has `name: 'Error'`), but the test expects `new EndpointError(...)` (which has `name: 'EndpointError'`), the test **fails**. This is a pre-existing test failure.

### 4.3 `errors.ts` — EndpointError Class (L11)

```typescript
export class EndpointError extends Error {
  constructor(
    message: string,
    public readonly httpStatus?: number,
    public readonly isCrossOriginRelated?: boolean
  ) {
    super(message);
    this.name = 'EndpointError';
  }
}
```

**Assessment:** `EndpointError` extends `Error` with two optional properties (`httpStatus`, `isCrossOriginRelated`). In the root getter fix, neither optional property is needed — the change is purely constructor type alignment. The `name` property change from `'Error'` to `'EndpointError'` is the only observable difference.

---

## 5. Reference Document Review

All 12 linked reference documents from the ogc-csapi-explorer repository were reviewed. The following are directly relevant to Issue #10:

### 5.1 Upstream Findings (`upstream-findings.md`)

Finding **F-5** is defined here:

> _"The `root` getter in `ogc-api/endpoint.ts` throws `new Error(...)` on line 74, but the corresponding test at `endpoint.spec.ts:1789` expects `new EndpointError(...)`. The production code should use `EndpointError` to match the test expectation and the library's error hierarchy."_
>
> Priority rank: **#11** (Low severity, Low effort)

F-5 is categorized under **Category 1: Library Bugs (Must Fix)** despite its low severity. It is the last item in the priority ranking.

### 5.2 EndpointError Isolation Report (`endpoint-error-isolation-report.md`)

**Finding F** in this report is where the bug was originally discovered:

> _"During test verification, we discovered that the OGC API endpoint's `root` getter throws `new Error(...)` on line 74 [...] This is a **pre-existing bug**: the production code should use `new EndpointError(...)` instead of `new Error(...)` to match the test expectation and align with the library's error hierarchy."_

The report also notes: _"If we're already touching `endpoint.ts` imports for the `EndpointError` migration, this would be an easy fix."_

Under **Pre-Existing Test Failures**: The report explicitly categorizes this as a pre-existing failure unrelated to any CSAPI work:

> | Suite                          | Failures | Root Cause                                                                                                            |
> | ------------------------------ | -------- | --------------------------------------------------------------------------------------------------------------------- |
> | `src/ogc-api/endpoint.spec.ts` | 1        | Line 74 of `endpoint.ts` throws `new Error(...)` but the test at line 1789 expects `EndpointError`. Pre-existing bug. |

### 5.3 Contribution Goal Accuracy Assessment (`contribution-goal-accuracy-assessment.md`)

This document validates that `EndpointError` usage is the library's established pattern. Under "Quality Standards": _"Compliance with OGC API specifications"_ — which includes consistent error hierarchy.

### 5.4 Library Source Changes Audit (`library-source-changes-audit.md`)

Confirms that only 1 commit has touched library source files (the EndpointError isolation refactor). Fixing this bug would be the second non-CSAPI library source change. However, this is a pre-existing upstream bug fix, not CSAPI-specific.

### 5.5 Other Documents Reviewed

The following documents were reviewed and found to have no direct bearing on Issue #10 (the error type mismatch does not affect URL building, content negotiation, CRUD operations, schema display, or conformance bypass):

| Document                                                                                                                                                       | Location           | Relevance                                                              |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------ | ---------------------------------------------------------------------- |
| [library-findings-gap-analysis.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/library-findings-gap-analysis.md)                 | ogc-csapi-explorer | Lists F-5 but no additional analysis                                   |
| [library-integration-report.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/library-integration-report.md)                       | ogc-csapi-explorer | Not directly relevant — covers bridge integration, not error hierarchy |
| [conformance-bypass-architecture-notes.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/conformance-bypass-architecture-notes.md) | ogc-csapi-explorer | Not relevant — demo bypasses OgcApiEndpoint entirely                   |
| [crud-smoke-test-findings.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/crud-smoke-test-findings.md)                           | ogc-csapi-explorer | Not relevant — covers write operations, not endpoint error handling    |
| [e2e-cross-server-report.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/e2e-cross-server-report.md)                             | ogc-csapi-explorer | Not relevant — covers cross-server interoperability, not error types   |
| [e2e-write-operations-report.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/e2e-write-operations-report.md)                     | ogc-csapi-explorer | Not relevant — covers write operations                                 |
| [schema-display-findings.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/schema-display-findings.md)                             | ogc-csapi-explorer | Not relevant — covers SWE Common schema display                        |

---

## 6. Risk Assessment

| Risk Category                 | Level        | Rationale                                                                                                                                                                        |
| ----------------------------- | ------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Regression risk**           | **None**     | The change makes the test that already expects `EndpointError` pass. No test expects plain `Error`.                                                                              |
| **Behavioral impact**         | **Minimal**  | Only consumers specifically checking `instanceof Error` but NOT `instanceof EndpointError` could notice. Since `EndpointError extends Error`, `instanceof Error` remains `true`. |
| **Scope creep**               | **None**     | One-word change on one line. No new abstractions, no new files, no new imports.                                                                                                  |
| **Upstream compatibility**    | **Positive** | Aligns production code with the test the upstream authors wrote. This is what upstream intended.                                                                                 |
| **CSAPI contribution impact** | **None**     | This is a pre-existing upstream bug in non-CSAPI code. The fix does not touch any CSAPI module.                                                                                  |

### 6.1 `instanceof` Compatibility

Because `EndpointError extends Error`:

```
new EndpointError(...) instanceof Error        → true   (unchanged)
new EndpointError(...) instanceof EndpointError → true   (FIXED — was false)
```

Any consumer catching `Error` generically will continue to catch this error. Consumers who specifically check for `EndpointError` (the documented pattern) will now correctly catch it. There is **no scenario** where this change breaks existing consumer code.

---

## 7. Analysis: Error Type Consistency

### 7.1 Pattern Analysis

The `OgcApiEndpoint` class has exactly six places where errors are thrown. Five use `EndpointError`. One does not:

| Line         | Method/Getter    | Error Type              | Consistent?      |
| ------------ | ---------------- | ----------------------- | ---------------- |
| 75           | `root` getter    | `Error`                 | **NO** ← the bug |
| 344          | `edr()`          | `EndpointError`         | Yes              |
| 387          | `csapi()`        | `EndpointError`         | Yes              |
| 442          | `allCollections` | `EndpointError`         | Yes              |
| 482          | `getStyle()`     | `EndpointError`         | Yes              |
| (spec L2883) | `csapi()` test   | expects `EndpointError` | Yes              |

The pattern is clear: `EndpointError` is the class's standard error type. Line 75 is the sole deviation.

### 7.2 Historical Context

This bug is likely an oversight from the original upstream development. The `root` getter was probably written before `EndpointError` was established as the standard endpoint error type, and was never updated when the class's error hierarchy was formalized.

Evidence: The `EndpointError` import exists in the file (line 38), which means some developer added `EndpointError` usage to the class but missed updating the `root` getter. The test was written (or updated) to expect `EndpointError`, but the production code was not updated to match.

### 7.3 Whether This Should Be Part of the CSAPI Upstream PR

The [upstream findings document](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/upstream-findings.md) ranks this as priority #11 and notes: _"technically outside the CSAPI contribution scope, but it's an easy one-line fix if touched during the upstream PR."_

The [endpoint-error-isolation-report](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/endpoint-error-isolation-report.md) similarly suggests: _"If we're already touching `endpoint.ts` imports for the `EndpointError` migration, this would be an easy fix."_

**Options for inclusion in upstream PR:**

| Option              | Pros                                                                           | Cons                                 |
| ------------------- | ------------------------------------------------------------------------------ | ------------------------------------ |
| Include in CSAPI PR | Fixes pre-existing test failure; one-line diff; already touching `endpoint.ts` | Technically outside CSAPI scope      |
| Separate PR         | Clean scope separation                                                         | Overhead of separate PR for one word |
| Leave for upstream  | Zero diff                                                                      | Bug remains; test failure persists   |

**Inference:** Including this fix in the CSAPI upstream PR is the pragmatic choice. The diff is one word, the fix is unambiguous, and the test already expects `EndpointError`. The upstream maintainers are already reviewing `endpoint.ts` changes (the `csapi()` factory method is added to this file). Including a one-word bug fix in the same review reduces overhead for everyone.

---

## 8. Recommendation

### 8.1 Proposed fix

Change line 75 of `src/ogc-api/endpoint.ts`:

```diff
  this.root_ = fetchRoot(this.baseUrl).catch((e) => {
-   throw new Error(`The endpoint appears non-conforming, the following error was encountered:
+   throw new EndpointError(`The endpoint appears non-conforming, the following error was encountered:
  ${e.message}`);
  });
```

**No other changes are needed.** The `EndpointError` import already exists at line 38.

### 8.2 Verification plan

1. Change `Error` → `EndpointError` on line 75
2. Run `npx jest src/ogc-api/endpoint.spec.ts` — the test at L1791 should now pass (it currently fails due to this bug)
3. Run full test suite: `npx jest` — confirm no regressions
4. Verify that `instanceof EndpointError` now resolves to `true` for the root getter error

### 8.3 What NOT to do

- **Do NOT** add new properties to the `EndpointError` constructor call — no `httpStatus` or `isCrossOriginRelated` is needed here; the error is about a non-conforming endpoint, not an HTTP failure.
- **Do NOT** change the error message — the test expects the exact message text, and it correctly describes the failure.
- **Do NOT** change the import path — the import from `'../shared/errors.js'` is the current pattern in this file. Import path changes (if the EndpointError isolation refactor is applied later) are a separate concern.
- **Do NOT** refactor other error handling in the class — the other five throws are already correct.

---

## Appendix A: Authority Precedence Analysis

| Authority Level | Source                     | Says About This Fix                                                                                                                                                      | Weight        |
| --------------- | -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------- |
| 1 (Highest)     | Library error hierarchy    | `EndpointError` is the documented error type for endpoint-level failures                                                                                                 | Definitive    |
| 2               | AI Operational Constraints | "Prefer minimal diffs over idealized rewrites" — one word is minimal; "Do not expand scope beyond the issue description" — the issue describes exactly this one-line fix | Supportive    |
| 3               | Issue description          | Explicitly identifies the bug and proposes the exact fix                                                                                                                 | Scoping       |
| 4               | Existing code patterns     | Five of six throws in the class use `EndpointError`; one doesn't — that's the bug                                                                                        | Confirming    |
| 5               | Test expectations          | `endpoint.spec.ts` L1791 expects `EndpointError`; the test is correct, the production code is wrong                                                                      | Confirming    |
| 6               | Reference documents        | F-5 in upstream-findings.md; Finding F in endpoint-error-isolation-report.md — both describe the same bug and recommend the same fix                                     | Corroborating |

---

## Appendix B: Cross-Reference Matrix

| Document                                                                                                                                                       | Location           | Relevance to Issue #10                                                                                      |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------ | ----------------------------------------------------------------------------------------------------------- |
| [upstream-findings.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/upstream-findings.md)                                                     | ogc-csapi-explorer | F-5 definition; priority #11; Category 1 "Library Bugs (Must Fix)"                                          |
| [endpoint-error-isolation-report.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/endpoint-error-isolation-report.md)             | ogc-csapi-explorer | Finding F — where this bug was originally discovered during test verification; documents it as pre-existing |
| [contribution-goal-accuracy-assessment.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/contribution-goal-accuracy-assessment.md) | ogc-csapi-explorer | Validates EndpointError as the library's established error pattern                                          |
| [library-source-changes-audit.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/library-source-changes-audit.md)                   | ogc-csapi-explorer | Context: only 1 prior commit touched library source; this would be an additional pre-existing bug fix       |
| [library-findings-gap-analysis.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/library-findings-gap-analysis.md)                 | ogc-csapi-explorer | Lists F-5; no additional analysis beyond upstream-findings.md                                               |
| [library-integration-report.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/library-integration-report.md)                       | ogc-csapi-explorer | Not directly relevant — covers bridge integration patterns                                                  |
| [conformance-bypass-architecture-notes.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/conformance-bypass-architecture-notes.md) | ogc-csapi-explorer | Not relevant — demo bypasses OgcApiEndpoint                                                                 |
| [crud-smoke-test-findings.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/crud-smoke-test-findings.md)                           | ogc-csapi-explorer | Not relevant — covers write operations                                                                      |
| [e2e-cross-server-report.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/e2e-cross-server-report.md)                             | ogc-csapi-explorer | Not relevant — covers cross-server interoperability                                                         |
| [e2e-write-operations-report.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/e2e-write-operations-report.md)                     | ogc-csapi-explorer | Not relevant — covers write operations                                                                      |
| [schema-display-findings.md](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/docs/webapp-demo/schema-display-findings.md)                             | ogc-csapi-explorer | Not relevant — covers SWE Common schema display                                                             |
| [AI_OPERATIONAL_CONSTRAINTS.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/governance/AI_OPERATIONAL_CONSTRAINTS.md)                        | ogc-client-CSAPI_2 | Authority precedence; minimal diffs; no scope expansion                                                     |

---

## Conclusion

Issue #10 is the most straightforward finding in the entire test series. The `root` getter on line 75 of `endpoint.ts` throws `new Error(...)` where it should throw `new EndpointError(...)`. The import exists. The test expects `EndpointError`. Every other throw in the class uses `EndpointError`.

The fix is one word. The risk is zero. The test that currently fails will pass. No new imports, no new files, no new abstractions. This is a pre-existing upstream bug that should be fixed either as part of the CSAPI upstream PR (pragmatic, minimal overhead) or as a separate one-line PR (clean scope separation).

**Recommendation: Fix the bug. Change `Error` to `EndpointError` on line 75 of `src/ogc-api/endpoint.ts`.**
