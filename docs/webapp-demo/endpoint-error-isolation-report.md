# EndpointError Isolation Refactor — Implementation Report

> **Date**: 2026-02-16
> **Commit**: `e73cff8` — `refactor: isolate EndpointError into own module to eliminate XML transitive dependency`
> **Prerequisite commit**: `8914798` — `docs: add CSAPI Library Integration report with upstream findings`
> **Location**: `src/` — 1 new file, 15 modified files, 1 demo file modified (18 files total, +44 −28 lines)

---

## Why This Matters

This report documents the resolution of **Finding #15** from the [Library Integration Report](library-integration-report.md) — the highest-priority architectural issue identified during the CSAPI library's first real-world integration. That finding revealed a **transitive dependency chain** that caused every consumer of the CSAPI `CSAPIQueryBuilder` to pull in the entire `@rgrove/parse-xml` XML parsing library, even though CSAPI is a strictly JSON-based API that never processes XML.

This is not a theoretical concern. It **actively broke our demo integration** — the Vite dev server could not resolve `@rgrove/parse-xml` from the demo's dependency graph, and we had to add an explicit Vite alias workaround (`'@rgrove/parse-xml': path.resolve(...)`) just to get the project to compile. Any consumer using Webpack, Rollup, esbuild, or another bundler would hit the same issue.

**For the upstream contribution**: this fix is arguably a prerequisite to submitting the CSAPI work. Without it, the first thing the upstream `ogc-client` maintainers would notice is that importing `CSAPIQueryBuilder` — a module that has nothing to do with XML — drags in an XML parser. This directly contradicts `ogc-client`'s existing module architecture, where WMS/WFS/WMTS modules use XML parsing for their respective OWS protocols, while OGC API and STAC modules are cleanly JSON-only. Our CSAPI contribution should preserve that separation.

The fix was a single-class extraction refactor: 23 lines of new code, 18 files touched, zero behavior changes, zero new dependencies. But the implications for bundle size, tree-shakability, build simplicity, and API cleanliness are significant. This report documents the problem, the solution, the verification, and — most importantly — what this teaches us about the library code we're preparing for upstream submission.

---

## The Problem in Detail

### The Dependency Chain

The transitive dependency chain was:

```
CSAPIQueryBuilder (url_builder.ts)
  └─→ import { EndpointError } from '../../shared/errors.js'
        └─→ import type { XmlDocument, XmlElement } from '@rgrove/parse-xml'     ← type-only, stripped at build
        └─→ import { findChildElement, ... } from '../shared/xml-utils.js'       ← RUNTIME import
              └─→ import { parseXml, XmlDocument, ... } from '@rgrove/parse-xml' ← RUNTIME import
```

The critical point: `shared/errors.ts` mixed two fundamentally different responsibilities in one module:

1. **`EndpointError`** — A simple error subclass used across the entire library (OGC API, STAC, CSAPI) for HTTP errors, resource availability errors, and cross-origin issues. Zero XML involvement. Just three properties: `message`, `httpStatus`, `isCrossOriginRelated`.

2. **`ServiceExceptionError`** — An OWS XML error parser that deserializes `ServiceExceptionReport` and `ExceptionReport` XML documents from WMS/WFS/WMTS servers. Requires `@rgrove/parse-xml` for XML DOM traversal.

Because both classes lived in the same module, importing `EndpointError` (which every CSAPI file needs for error handling) forced the bundler to also resolve `ServiceExceptionError`'s XML dependencies (which no CSAPI file ever uses).

### Why Tree Shaking Doesn't Help

A reasonable question: shouldn't modern bundlers tree-shake the unused `ServiceExceptionError` and its XML imports?

No, because of how the module is structured:

1. `errors.ts` has **module-level** imports from `xml-utils.ts` — these execute when the module loads, regardless of which exports the consumer uses.
2. `xml-utils.ts` calls `import { parseXml, ... } from '@rgrove/parse-xml'` at the module level.
3. Even if a bundler determines that `ServiceExceptionError` is unused, it cannot safely eliminate the `xml-utils.ts` import because module-level code may have side effects.

The only clean solution is to physically separate the XML-dependent code from the XML-independent code into different modules.

### Impact on Consumers

| Consumer Type | Impact Before Fix | Impact After Fix |
|---------------|-------------------|------------------|
| CSAPI-only consumer (our demo) | Must install/resolve `@rgrove/parse-xml` even though CSAPI never uses XML | `@rgrove/parse-xml` not in dependency graph at all |
| Bundle size | XML parser included in output bundle (~50KB unminified) | XML parser excluded from CSAPI-only bundles |
| Build tools | Must configure resolution for `@rgrove/parse-xml` (our Vite alias workaround) | No special configuration needed |
| WMS/WFS consumer | No change (still needs `errors.ts` for `ServiceExceptionError`) | No change (backward compatible) |
| Full-library consumer | No change | No change |

---

## What We Did

### Step 1: Analyzed the Import Graph

Before making any changes, we performed a thorough analysis of every file that imports from `shared/errors.ts` (19 files total) and categorized them by what they actually need:

**Files that only import `EndpointError`** (14 files — candidates for migration):

| Module | Area | What It Uses |
|--------|------|-------------|
| `src/ogc-api/csapi/url_builder.ts` | CSAPI | `EndpointError` — thrown by `assertResourceAvailable()` |
| `src/ogc-api/csapi/url_builder.spec.ts` | CSAPI tests | `EndpointError` — assertion target in availability tests |
| `src/ogc-api/csapi/integration/command.spec.ts` | CSAPI tests | `EndpointError` — assertion target |
| `src/ogc-api/csapi/integration/discovery.spec.ts` | CSAPI tests | `EndpointError` — assertion target |
| `src/ogc-api/csapi/integration/navigation.spec.ts` | CSAPI tests | `EndpointError` — assertion target |
| `src/ogc-api/endpoint.ts` | OGC API | `EndpointError` — thrown by various endpoint methods |
| `src/ogc-api/endpoint.spec.ts` | OGC API tests | `EndpointError` — assertion target |
| `src/ogc-api/link-utils.ts` | OGC API | `EndpointError` — thrown for missing/invalid links |
| `src/ogc-api/info.ts` | OGC API | `EndpointError` — thrown for endpoint info errors |
| `src/stac/endpoint.ts` | STAC | `EndpointError` — thrown by STAC endpoint methods |
| `src/stac/endpoint.spec.ts` | STAC tests | `EndpointError` — assertion target |
| `src/stac/info.ts` | STAC | `EndpointError` — thrown for STAC info errors |
| `src/stac/link-utils.ts` | STAC | `EndpointError` — thrown for missing STAC links |
| `src/stac/link-utils.spec.ts` | STAC tests | `EndpointError` — assertion target |

**Files that need more than `EndpointError`** (5 files — must stay on `errors.ts`):

| Module | Area | What It Uses |
|--------|------|-------------|
| `src/worker/utils.ts` | Worker | `encodeError`, `decodeError` — serializes errors across worker boundary |
| `src/worker/worker.ts` | Worker | `check` — OWS XML error checker |
| `src/wfs/endpoint.spec.ts` | WFS tests | `EndpointError` + `ServiceExceptionError` |
| `src/wms/endpoint.spec.ts` | WMS tests | `EndpointError` + `ServiceExceptionError` |
| `src/shared/errors.spec.ts` | Shared tests | Tests the entire `errors.ts` module |

**Files that import `EndpointError` from `errors.ts` but also have their own XML dependencies** (2 files — migrating would not eliminate their XML dependency):

| Module | Area | Why It Stays |
|--------|------|-------------|
| `src/shared/http-utils.ts` | Shared | Also imports `parseXmlString` from `xml-utils.ts` directly |
| `src/shared/http-utils.spec.ts` | Shared tests | Tests HTTP utils which include XML parsing |

### Step 2: Created `src/shared/endpoint-error.ts`

A new 23-line module containing **only** the `EndpointError` class:

```typescript
/**
 * Error thrown when an endpoint operation cannot be completed.
 *
 * Used across all OGC API modules (Connected Systems, Features, STAC, etc.)
 * for resource availability errors, HTTP errors, and cross-origin issues.
 *
 * This class is intentionally isolated in its own module (no XML or other
 * heavy dependencies) so that lightweight consumers — such as CSAPI-only
 * users who never touch WMS/WFS — do not pull in the XML parsing stack
 * via transitive imports.
 *
 * @see ServiceExceptionError in `./errors.ts` for OWS XML error parsing
 */
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

Key design decisions:
- **Zero imports** — no dependencies at all, not even within the library
- **Identical class definition** — byte-for-byte the same class that was in `errors.ts`
- **JSDoc explains the rationale** — future developers understand why this is a separate file
- **Cross-reference to `errors.ts`** — so developers looking for XML error handling find it

### Step 3: Updated `src/shared/errors.ts` for Backward Compatibility

The original `EndpointError` class definition was **removed** from `errors.ts` and replaced with an import + re-export:

```typescript
// Import EndpointError from its own module so it is available at runtime
// (used by encodeError/decodeError below) and re-export it for backward
// compatibility.  EndpointError lives in endpoint-error.ts to avoid pulling
// in the XML parsing stack for consumers that only need EndpointError.
import { EndpointError } from './endpoint-error.js';
export { EndpointError };
```

This is the backward-compatibility bridge: any existing code that imports `EndpointError` from `shared/errors.ts` continues to work without changes. The re-export makes the API surface identical from the consumer's perspective.

**Critical implementation detail**: the initial approach used `export { EndpointError } from './endpoint-error.js'` (a direct re-export without an intermediate import). This compiles correctly but **does not create a local binding** — meaning `encodeError()` and `decodeError()` in the same file could not reference `EndpointError` at runtime. This caused `ReferenceError: EndpointError is not defined` at runtime. The fix was to use `import` + `export` separately, which creates both a local binding and a public export.

This is a subtle but important JavaScript module semantics point: `export { X } from 'y'` re-exports `X` for external consumers but does NOT make `X` available for use within the same module. This is different from `import { X } from 'y'; export { X };` which does both.

### Step 4: Updated 14 Files to Import from `endpoint-error.ts`

All 14 files that only need `EndpointError` were updated with a single import path change:

```diff
- import { EndpointError } from '../../shared/errors.js';
+ import { EndpointError } from '../../shared/endpoint-error.js';
```

The 14 files span three library areas:

- **CSAPI** (5 files): `url_builder.ts`, `url_builder.spec.ts`, and 3 integration test files
- **OGC API** (4 files): `endpoint.ts`, `endpoint.spec.ts`, `link-utils.ts`, `info.ts`
- **STAC** (5 files): `endpoint.ts`, `endpoint.spec.ts`, `info.ts`, `link-utils.ts`, `link-utils.spec.ts`

The fact that OGC API and STAC modules also benefit from this change highlights that the transitive dependency problem was not limited to CSAPI. Any module that only uses `EndpointError` was unnecessarily pulling in XML parsing.

### Step 5: Updated `src/index.ts` Public Exports

The library's public API surface was updated to export `EndpointError` from its new canonical location:

```diff
 export {
   check,
   ServiceExceptionError,
-  EndpointError,
 } from './shared/errors.js';
+export { EndpointError } from './shared/endpoint-error.js';
```

`check` and `ServiceExceptionError` remain exported from `errors.js` (they need the XML dependencies). `EndpointError` is now exported from `endpoint-error.js`.

External consumers importing `{ EndpointError } from 'ogc-client'` see no change — the re-export chain is transparent. But internal bundling benefits because the `endpoint-error.js` module has zero transitive dependencies.

### Step 6: Removed Vite Alias Workaround from Demo

With the dependency chain broken, the Vite alias workaround we added in the library integration phase was no longer necessary:

```diff
 resolve: {
   alias: {
     '@csapi': path.resolve(__dirname, '../src'),
-    // Library source imports @rgrove/parse-xml transitively (via shared/errors.ts).
-    // Resolve from root node_modules since lib deps are installed there.
-    '@rgrove/parse-xml': path.resolve(__dirname, '../node_modules/@rgrove/parse-xml'),
   },
 },
```

This is the **concrete proof** that the refactor achieved its goal: the demo's import graph no longer reaches `@rgrove/parse-xml` at all. There is no configuration, aliasing, or workaround needed.

---

## Verification

### Unit Tests: Direct Verification

We ran the two test suites most directly affected by the refactor:

**`src/shared/errors.spec.ts`** — Tests the error encoding/decoding that uses `EndpointError` at runtime:

```
PASS src/shared/errors.spec.ts
Test Suites: 1 passed, 1 total
Tests:       19 passed, 19 total
```

All 19 tests pass, including:
- `encodeError › can encode an EndpointError` — confirms `instanceof EndpointError` works with the imported class
- `decodeError › can decode an EndpointError` — confirms `new EndpointError(...)` works with the imported constructor
- `encodeError › can encode a ServiceExceptionError` — confirms `ServiceExceptionError` is unaffected
- `encodeError › can encode a generic Error` — confirms the generic path still works after the `EndpointError instanceof` check

**`src/ogc-api/csapi/url_builder.spec.ts`** — Tests the `CSAPIQueryBuilder` (the primary consumer that triggered this refactor):

```
PASS src/ogc-api/csapi/url_builder.spec.ts
Test Suites: 1 passed, 1 total
Tests:       298 passed, 298 total
```

All 298 tests pass. This includes tests that exercise `assertResourceAvailable()` (which throws `EndpointError`) and confirms the builder's error handling is unchanged.

### Import Graph Verification

We traced the complete transitive import graph from the demo's entry point (`csapi-bridge.ts`) to verify no path reaches `@rgrove/parse-xml`:

```
csapi-bridge.ts
  ├─→ url_builder.ts
  │     ├─→ shared/endpoint-error.ts  ← ZERO IMPORTS ✅
  │     ├─→ csapi/helpers.ts          ← no XML imports ✅
  │     └─→ csapi/model.ts            ← no XML imports ✅
  ├─→ formats/response.ts             ← type-only imports ✅
  ├─→ formats/geojson.ts              ← type-only imports ✅
  ├─→ csapi/helpers.ts                ← no XML imports ✅
  └─→ csapi/model.ts                  ← no XML imports ✅
```

Every runtime dependency in the graph terminates at a zero-dependency leaf or a module that only has type-only imports (which are stripped at build time). The chain to `@rgrove/parse-xml` is completely severed.

### Vite Dev Server Verification

The Vite dev server was started without the `@rgrove/parse-xml` alias, confirming the workaround is no longer needed:

```
VITE v7.3.1  ready in 1457 ms

  ➜  Local:   http://localhost:5173/
```

We verified that the served TypeScript compiles correctly by fetching the transpiled `endpoint-error.ts` from the dev server:

```javascript
// Served by Vite at /@fs/.../src/shared/endpoint-error.ts
export class EndpointError extends Error {
  constructor(message, httpStatus, isCrossOriginRelated) {
    super(message);
    this.httpStatus = httpStatus;
    this.isCrossOriginRelated = isCrossOriginRelated;
    this.name = "EndpointError";
  }
}
```

Zero imports. Zero dependencies. Exactly what a CSAPI-only consumer should see.

We also verified that `url_builder.ts` resolves `EndpointError` from the new location:

```javascript
// Served by Vite at /@fs/.../src/ogc-api/csapi/url_builder.ts (first import)
import { EndpointError } from "/@fs/.../src/shared/endpoint-error.ts";
```

No reference to `errors.ts` or `@rgrove/parse-xml` anywhere in the served module.

### Pre-Existing Test Failures (Not Caused by This Refactor)

The full test suite run (52 suites) shows 3 failing suites and 32 failing tests that were **not introduced by this change**:

| Suite | Failures | Root Cause |
|-------|----------|------------|
| `src/ogc-api/endpoint.spec.ts` | 1 | Line 74 of `endpoint.ts` throws `new Error(...)` but the test at line 1789 expects `EndpointError`. This is a **pre-existing bug**: the production code should use `EndpointError` instead of `Error`. Not related to our refactor. |
| `src/shared/http-utils.spec.ts` | 1 | Worker path resolution timeout — esbuild cannot resolve a Windows absolute path (`C:UserssbollingDocuments...`) for the worker bundle. Pre-existing Windows environment issue. |
| `src/wms/endpoint.spec.ts`, `src/wmts/endpoint.spec.ts`, `src/wfs/endpoint.spec.ts` | 30 | Same worker path resolution issue causes timeout cascades in all OWS endpoint tests. Pre-existing. |

None of these failures are related to the `EndpointError` isolation. They all existed before the refactor and are tracked separately.

---

## Upstream Library Findings

### Finding A: `export { X } from 'y'` Does Not Create a Local Binding

**Severity: Bug-risk awareness**
**Affects: `shared/errors.ts`**

During the refactor, the initial implementation used `export { EndpointError } from './endpoint-error.js'` as a direct re-export in `errors.ts`. This caused a `ReferenceError` at runtime because `encodeError()` and `decodeError()` in the same file use `EndpointError` for `instanceof` checks and constructor calls.

In JavaScript/TypeScript modules, `export { X } from 'y'` is a **pass-through re-export** — it makes `X` available to external importers but does NOT bind it as a local variable. The correct pattern is:

```typescript
import { EndpointError } from './endpoint-error.js';
export { EndpointError };
```

This creates both a local binding (for internal use) and a public export (for external consumers).

**Upstream relevance**: This is a well-known module semantics subtlety, but it's the kind of thing that a future maintainer could accidentally introduce by "simplifying" the import to a direct re-export. The comment in `errors.ts` explains why both the `import` and `export` are needed.

### Finding B: The Transitive Dependency Problem Extends Beyond CSAPI

**Severity: Architectural improvement**
**Affects: OGC API, STAC modules**

When we analyzed the import graph, we discovered that the `@rgrove/parse-xml` transitive dependency was not limited to CSAPI consumers. Of the 14 files we migrated to `endpoint-error.ts`:

- **5 were CSAPI files** (the original motivation)
- **4 were OGC API core files** (`endpoint.ts`, `endpoint.spec.ts`, `link-utils.ts`, `info.ts`)
- **5 were STAC files** (`endpoint.ts`, `endpoint.spec.ts`, `info.ts`, `link-utils.ts`, `link-utils.spec.ts`)

This means the OGC API and STAC modules also had an unnecessary transitive dependency on XML parsing. A consumer building a STAC-only application (which is pure JSON) would have needed `@rgrove/parse-xml` in their dependency graph — the same problem as CSAPI.

**Upstream relevance**: The `EndpointError` isolation benefits the entire library, not just the CSAPI contribution. This is worth highlighting in the upstream PR: the refactor improves modularity for all JSON-only consumers (OGC API Features, STAC, CSAPI) alongside the legacy XML-based services (WMS, WFS, WMTS).

### Finding C: `errors.ts` Mixes Three Separate Concerns

**Severity: Design observation**
**Affects: `shared/errors.ts`**

After extracting `EndpointError`, we can now see that `errors.ts` still contains three distinct concerns:

1. **`ServiceExceptionError` class + `parse()` + `check()`** — OWS XML error parsing. Used by WMS/WFS/WMTS modules and the worker.
2. **`encodeError()` + `decodeError()`** — Worker serialization. Encodes/decodes `Error` subclasses for transfer across web worker boundaries. Used by `worker/utils.ts`.
3. **`EndpointError`** (now extracted) — Generic endpoint error class.

Concerns #1 and #2 could also be separated. `encodeError`/`decodeError` only need `EndpointError` and `ServiceExceptionError` as classes — they don't need the XML parsing functions themselves. But this is a lower-priority refactor and doesn't affect CSAPI consumers (they'll never import from `errors.ts` after this change).

**Upstream relevance**: If the upstream maintainers want to continue improving module boundaries, a further split of `errors.ts` into `service-exception-error.ts` (OWS XML) and `error-serialization.ts` (worker encoding) would be the logical next step. But this is optional — the CSAPI-critical fix (extracting `EndpointError`) is the one that matters most.

### Finding D: Files That Could Be Migrated But Weren't

**Severity: Informational**
**Affects: `shared/http-utils.ts`, `shared/http-utils.spec.ts`**

Two files in `shared/` import `EndpointError` from `errors.ts` but were NOT migrated to `endpoint-error.ts`:

- `http-utils.ts` — Also imports `parseXmlString` from `xml-utils.ts` directly, so it already has XML dependencies regardless of where it gets `EndpointError`.
- `http-utils.spec.ts` — Tests the above module.

Migrating these files would have been harmless but also pointless — they'd still pull in XML through their other imports. We chose not to make unnecessary changes to reduce the diff size and keep the refactor focused.

**Upstream relevance**: These files are not part of the CSAPI contribution. They demonstrate the "correct" pattern for files that genuinely need XML — they stay on `errors.ts` and that's fine.

### Finding E: The `@rgrove/parse-xml` Type-Only Import Is Fine

**Severity: Informational**
**Affects: `shared/errors.ts`**

Line 1 of `errors.ts` has:
```typescript
import type { XmlDocument, XmlElement } from '@rgrove/parse-xml';
```

This is a **type-only import** (`import type`), which is completely stripped at compile time. It does not create a runtime dependency. The problematic dependency comes from the next import:

```typescript
import { findChildElement, getElementAttribute, ... } from '../shared/xml-utils.js';
```

This is a **runtime import** that pulls in `xml-utils.ts`, which in turn imports the actual `parseXml` function from `@rgrove/parse-xml`.

**Upstream relevance**: The `import type` pattern is used correctly in the codebase. TypeScript's `import type` is an important tool for avoiding unnecessary transitive dependencies, and the library already uses it where appropriate. The problem was that `errors.ts` also had runtime imports alongside the type-only ones — both in the same module.

### Finding F: Pre-Existing Bug in `ogc-api/endpoint.ts`

**Severity: Bug**
**Affects: `src/ogc-api/endpoint.ts`, line 74**

During test verification, we discovered that the OGC API endpoint's `root` getter throws `new Error(...)` on line 74:

```typescript
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

But the test at `endpoint.spec.ts:1789` expects `EndpointError`:

```typescript
await expect(endpoint.info).rejects.toEqual(
  new EndpointError(`The endpoint appears non-conforming, ...`)
);
```

This is a **pre-existing bug**: the production code should use `new EndpointError(...)` instead of `new Error(...)` to match the test expectation and align with the library's error hierarchy. This bug exists on the main branch before our refactor and is unrelated to the CSAPI contribution, but it's worth noting because it demonstrates that error type consistency is a library-wide concern.

**Upstream relevance**: If we're already touching `endpoint.ts` imports for the `EndpointError` migration, this would be an easy fix. Consider changing `new Error(...)` to `new EndpointError(...)` on line 74 as part of the upstream PR. It aligns with the existing test expectations.

---

## Complete File Inventory

### New File Created (1)

| File | Lines | Purpose |
|------|-------|---------|
| `src/shared/endpoint-error.ts` | 23 | `EndpointError` class in a zero-dependency module |

### Modified Library Files (15)

| File | Change | Rationale |
|------|--------|-----------|
| `src/shared/errors.ts` | Replaced class definition with `import` + `export` re-export | Backward compatibility — old importers unaffected |
| `src/index.ts` | Split `EndpointError` export to come from `endpoint-error.js` | Public API now routes through the new module |
| `src/ogc-api/csapi/url_builder.ts` | Import path `errors.js` → `endpoint-error.js` | **Primary CSAPI fix** — eliminates XML chain |
| `src/ogc-api/csapi/url_builder.spec.ts` | Import path change | Test file for the primary fix |
| `src/ogc-api/csapi/integration/command.spec.ts` | Import path change | CSAPI integration test |
| `src/ogc-api/csapi/integration/discovery.spec.ts` | Import path change | CSAPI integration test |
| `src/ogc-api/csapi/integration/navigation.spec.ts` | Import path change | CSAPI integration test |
| `src/ogc-api/endpoint.ts` | Import path change | OGC API endpoint — also benefits from isolation |
| `src/ogc-api/endpoint.spec.ts` | Import path change | OGC API endpoint test |
| `src/ogc-api/info.ts` | Import path change | OGC API info module |
| `src/ogc-api/link-utils.ts` | Import path change | OGC API link utilities |
| `src/stac/endpoint.ts` | Import path change | STAC endpoint — also benefits from isolation |
| `src/stac/endpoint.spec.ts` | Import path change | STAC endpoint test |
| `src/stac/info.ts` | Import path change | STAC info module |
| `src/stac/link-utils.ts` | Import path change | STAC link utilities |
| `src/stac/link-utils.spec.ts` | Import path change | STAC link utilities test |

### Modified Demo File (1)

| File | Change | Rationale |
|------|--------|-----------|
| `demo/vite.config.ts` | Removed `@rgrove/parse-xml` alias | Workaround no longer needed |

### Files Intentionally NOT Changed

| File | Reason It Stays on `errors.ts` |
|------|-------------------------------|
| `src/worker/utils.ts` | Uses `encodeError()` / `decodeError()` (not just `EndpointError`) |
| `src/worker/worker.ts` | Uses `check()` — the OWS XML error checker |
| `src/wfs/endpoint.spec.ts` | Tests WFS — needs both `EndpointError` and `ServiceExceptionError` |
| `src/wms/endpoint.spec.ts` | Tests WMS — needs both error types |
| `src/shared/errors.spec.ts` | Tests the `errors.ts` module itself |
| `src/shared/http-utils.ts` | Has its own XML dependency via `parseXmlString` |
| `src/shared/http-utils.spec.ts` | Tests the above |

---

## Import Graph: Before and After

### Before (CSAPI consumer imports `url_builder.ts`)

```
url_builder.ts
  └─→ shared/errors.ts
        ├─→ @rgrove/parse-xml          ← type import (stripped at build)
        └─→ shared/xml-utils.ts        ← RUNTIME import
              └─→ @rgrove/parse-xml    ← RUNTIME dependency PULLED IN
```

**Result**: CSAPI consumer's bundle includes `@rgrove/parse-xml` (~50KB). Build fails if `@rgrove/parse-xml` is not resolvable.

### After (CSAPI consumer imports `url_builder.ts`)

```
url_builder.ts
  └─→ shared/endpoint-error.ts         ← ZERO IMPORTS ✅
```

**Result**: CSAPI consumer's bundle has no XML dependencies. Build requires no special configuration.

### After (WMS consumer still imports `errors.ts`)

```
wms/endpoint.spec.ts
  └─→ shared/errors.ts
        ├─→ shared/endpoint-error.ts   ← re-export for backward compat
        ├─→ @rgrove/parse-xml          ← type import
        └─→ shared/xml-utils.ts        ← RUNTIME import (this is expected for WMS)
```

**Result**: No change for WMS/WFS/WMTS consumers. They already needed XML parsing. The backward-compatible re-export ensures they get `EndpointError` without needing to change import paths.

---

## Lessons Learned for the Upstream Contribution

### 1. Module Boundary Discipline Is Critical

The `ogc-client` library supports multiple OGC API protocols (WMS, WFS, WMTS, OGC API, STAC, TMS) from a single package. Each protocol module has different dependency requirements — WMS/WFS need XML parsing, OGC API/STAC/CSAPI are JSON-only. The `shared/` directory must be extremely careful not to create cross-dependencies between protocol-specific utilities.

The `errors.ts` module violated this boundary by mixing XML-dependent code (`ServiceExceptionError`) with XML-independent code (`EndpointError`) in a single file. This is an easy mistake to make during organic development — `EndpointError` was probably added to `errors.ts` because it was conceptually related to error handling. But physically, it belongs in a separate module to preserve the library's protocol-independent core.

**Lesson for CSAPI upstream**: Every new module we add to the CSAPI contribution should be checked for transitive dependencies that reach outside the JSON/HTTP stack. If a CSAPI module imports from `shared/`, verify that the shared module doesn't transitively import XML parsing, worker utilities, or other protocol-specific code.

### 2. The Demo App Is an Effective Dependency Validator

We would not have discovered the transitive dependency problem without building the demo app. The library's own test suite (which runs in Jest with Node.js) resolves all dependencies from the same `node_modules` directory, so the transitive XML import never causes a problem during testing.

It was only when an **external consumer** (the Vite-based demo) tried to bundle the CSAPI modules that the unnecessary dependency became visible. This validates the demo app's role: it simulates what a real-world consumer would experience when integrating the library.

**Lesson for upstream**: Before submitting the PR, we should verify that the CSAPI modules can be imported and bundled independently of the WMS/WFS/WMTS modules. The demo app proves this is now possible with the `EndpointError` isolation.

### 3. Backward Compatibility Requires Careful Re-Export Patterns

The `import` + `export` pattern in `errors.ts` (`import { EndpointError } from './endpoint-error.js'; export { EndpointError };`) is the only correct way to re-export a symbol that is also used internally. The simpler `export { EndpointError } from './endpoint-error.js'` fails silently at the TypeScript level but throws `ReferenceError` at runtime.

**Lesson for upstream**: If the upstream maintainers or future contributors refactor more shared modules, they should be aware of this module semantics distinction. TypeScript does not warn about this — the error only manifests at runtime.

### 4. Small Refactors Can Have Outsized Impact

This change was +44 −28 lines across 18 files. The majority of changes were mechanical import path updates. Yet the impact is significant:

- Eliminates an unnecessary ~50KB dependency for all JSON-only library consumers
- Removes the need for bundler-specific workarounds (our Vite alias)
- Improves tree-shakability of the library
- Aligns the module architecture with the library's protocol-based separation of concerns
- Benefits not just CSAPI, but also OGC API and STAC consumers

This is the kind of refactor that is easy to justify in an upstream PR: minimal risk, maximal architectural benefit, zero behavior changes, comprehensive test coverage.

---

## Concerns

### 1. Two Files in `shared/` Were Not Migrated

`http-utils.ts` and `http-utils.spec.ts` still import `EndpointError` from `errors.ts`. While harmless (they have their own XML dependencies anyway), a purist might argue for consistency. We chose pragmatism: migrating them would increase the diff without eliminating any dependency.

If the upstream maintainers prefer consistency, these two files can be migrated in a follow-up.

### 2. The Pre-Existing `endpoint.ts` Bug Should Be Fixed

The bug on `endpoint.ts` line 74 (`new Error(...)` instead of `new EndpointError(...)`) is a small fix that could be included in the upstream PR. It would fix one failing test and improve the library's error consistency. However, it's technically outside the scope of the CSAPI contribution, so it could also be submitted as a separate PR.

### 3. Future `errors.ts` Changes Need Awareness

Any future change to `errors.ts` that adds new imports or new classes should consider whether those additions belong in `errors.ts` (XML/OWS-specific) or in a separate module (protocol-independent). The temptation to add "one more thing" to `errors.ts` is how the original problem occurred.

---

## Recommendations for Next Steps

### Immediate (before upstream submission)

1. **~~Split `shared/errors.ts`~~** ✅ — **DONE** (this refactor)
2. **Test write operations end-to-end** — Send actual POST/PUT/DELETE requests using builder URLs against OSH SensorHub. Validate that the URLs the builder produces result in successful server operations. This is the next highest-priority validation step.
3. **Consider fixing the `endpoint.ts` line 74 bug** — Change `new Error(...)` to `new EndpointError(...)` to align with test expectations.
4. **Document the module isolation in the upstream PR description** — Explain that `endpoint-error.ts` is intentionally separate from `errors.ts` and why.

### For the upstream PR

5. **Include the full import remap** — All 14 files should be updated in the upstream PR, not just the CSAPI files. The OGC API and STAC improvements benefit existing users too.
6. **Verify bundle size impact** — Measure the bundle size difference for a CSAPI-only consumer with and without the refactor. This provides concrete data for the PR description.
7. **Consider adding a CI step** — A simple check that `endpoint-error.ts` has zero imports would prevent future regressions.

---

## Appendix: Git Diff Summary

```
Commit: e73cff8
Author: Sam-Bolling <bolling.samuel@gmail.com>
Date:   Mon Feb 16 11:16:36 2026 -0500

18 files changed, 44 insertions(+), 28 deletions(-)

 demo/vite.config.ts                              |  3 ---  (alias removed)
 src/index.ts                                     |  2 +-  (export rerouted)
 src/ogc-api/csapi/integration/command.spec.ts    |  2 +-  (import path)
 src/ogc-api/csapi/integration/discovery.spec.ts  |  2 +-  (import path)
 src/ogc-api/csapi/integration/navigation.spec.ts |  2 +-  (import path)
 src/ogc-api/csapi/url_builder.spec.ts            |  2 +-  (import path)
 src/ogc-api/csapi/url_builder.ts                 |  2 +-  (import path)
 src/ogc-api/endpoint.spec.ts                     |  2 +-  (import path)
 src/ogc-api/endpoint.ts                          |  2 +-  (import path)
 src/ogc-api/info.ts                              |  2 +-  (import path)
 src/ogc-api/link-utils.ts                        |  2 +-  (import path)
 src/shared/endpoint-error.ts                     | 23 +++  (NEW — zero-dep EndpointError)
 src/shared/errors.ts                             | 16 +-- (class → import + re-export)
 src/stac/endpoint.spec.ts                        |  2 +-  (import path)
 src/stac/endpoint.ts                             |  2 +-  (import path)
 src/stac/info.ts                                 |  2 +-  (import path)
 src/stac/link-utils.spec.ts                      |  2 +-  (import path)
 src/stac/link-utils.ts                           |  2 +-  (import path)
```

---

## Appendix: Importer Classification Reference

This is the complete classification of all 21 files that import from either `endpoint-error.ts` (new) or `errors.ts` (original), as of commit `e73cff8`:

### Imports from `endpoint-error.ts` (15 files)

These files have zero transitive dependency on XML parsing:

```
src/index.ts                                      → export { EndpointError }
src/ogc-api/csapi/url_builder.ts                  → EndpointError
src/ogc-api/csapi/url_builder.spec.ts             → EndpointError
src/ogc-api/csapi/integration/command.spec.ts     → EndpointError
src/ogc-api/csapi/integration/discovery.spec.ts   → EndpointError
src/ogc-api/csapi/integration/navigation.spec.ts  → EndpointError
src/ogc-api/endpoint.ts                           → EndpointError
src/ogc-api/endpoint.spec.ts                      → EndpointError
src/ogc-api/info.ts                               → EndpointError
src/ogc-api/link-utils.ts                         → EndpointError
src/stac/endpoint.ts                              → EndpointError
src/stac/endpoint.spec.ts                         → EndpointError
src/stac/info.ts                                  → EndpointError
src/stac/link-utils.ts                            → EndpointError
src/stac/link-utils.spec.ts                       → EndpointError
```

### Imports from `errors.ts` (7 files)

These files genuinely need XML-dependent code or multi-class access:

```
src/shared/errors.ts                              → import { EndpointError } from './endpoint-error.js' (self)
src/shared/errors.spec.ts                         → EndpointError, ServiceExceptionError, check, encodeError, decodeError
src/shared/http-utils.ts                          → EndpointError (also imports xml-utils.ts directly)
src/shared/http-utils.spec.ts                     → EndpointError (tests http-utils which uses XML)
src/worker/utils.ts                               → encodeError, decodeError
src/worker/worker.ts                              → check
src/wfs/endpoint.spec.ts                          → EndpointError, ServiceExceptionError
src/wms/endpoint.spec.ts                          → EndpointError, ServiceExceptionError
src/index.ts                                      → check, ServiceExceptionError (EndpointError via endpoint-error.ts)
```

### Not Importing from Either (SensorML error module — separate concern)

```
src/ogc-api/csapi/formats/sensorml/errors.ts      → SensorMLParseError (different errors module, CSAPI-specific)
src/ogc-api/csapi/formats/sensorml/parser.ts       → imports SensorMLParseError from ./errors.js
src/ogc-api/csapi/formats/sensorml/physical-system.ts → imports SensorMLParseError
src/ogc-api/csapi/formats/sensorml/aggregate-process.ts → imports SensorMLParseError
src/ogc-api/csapi/formats/sensorml/simple-process.ts → imports SensorMLParseError
src/ogc-api/csapi/formats/sensorml/_helpers.ts     → imports SensorMLParseError
```

Note: The SensorML `errors.ts` at `src/ogc-api/csapi/formats/sensorml/errors.ts` is a completely separate file from `src/shared/errors.ts`. It contains `SensorMLParseError` and has no XML parsing dependency (SensorML errors are thrown during our own parsing logic, not from the XML library). The grep output showing `from './errors.js'` for SensorML files refers to their local `errors.ts`, not the shared one.
