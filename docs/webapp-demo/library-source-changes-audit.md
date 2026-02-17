# Library Source Changes Audit — Demo App Fork

> **Date**: 2026-02-16
> **Repository**: [`OS4CSAPI/ogc-csapi-explorer`](https://github.com/OS4CSAPI/ogc-csapi-explorer)
> **Scope**: All changes to `src/` (library source code) made after the demo app was created
> **Methodology**: Full `git log` audit of every commit touching `src/` from the demo app scaffolding commit (`1139dbb`) through `HEAD`

---

## Executive Summary

**Exactly one commit** modified library source code (`src/`) during the entire demo app development lifecycle. All other demo app functionality — including all CRUD smoke test workarounds — was implemented exclusively in `demo/` (the demo app) and `docs/` (documentation).

The single library change is a **pure structural refactor** with zero behavioral impact, zero API surface change, and zero test behavior change. It was the highest-priority upstream recommendation from the library integration assessment.

---

## The One Change

### Commit `e73cff8` — "refactor: isolate EndpointError into own module to eliminate XML transitive dependency"

| | |
|---|---|
| **Commit** | [`e73cff8`](https://github.com/OS4CSAPI/ogc-csapi-explorer/commit/e73cff8) |
| **Finding** | F-6 ([library-findings-gap-analysis.md](./library-findings-gap-analysis.md#f-6-endpointerror-transitive-xml-dependency--resolved)) |
| **Integration Report** | Finding #15 ([library-integration-report.md](./library-integration-report.md)) |
| **Detailed Report** | [endpoint-error-isolation-report.md](./endpoint-error-isolation-report.md) |
| **Files Changed** | 18 (1 new, 17 modified) |
| **Lines Added** | 44 |
| **Lines Removed** | 28 |
| **Net Change** | +16 lines |
| **Behavioral Impact** | None — pure import path refactor |
| **Tests Affected** | 0 (all 317 tests in affected suites pass unchanged) |

---

### What Was Changed

#### 1. New File: `src/shared/endpoint-error.ts` (23 lines)

The `EndpointError` class was extracted from `src/shared/errors.ts` into its own zero-dependency module. The class itself is **byte-for-byte identical** to what was in `errors.ts`:

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

No properties, methods, constructor parameters, or behavior were changed.

#### 2. Modified File: `src/shared/errors.ts`

The inline `EndpointError` class definition (10 lines) was replaced with an import + re-export (4 lines):

```typescript
// Before (in errors.ts):
export class EndpointError extends Error { ... }

// After (in errors.ts):
import { EndpointError } from './endpoint-error.js';
export { EndpointError };
```

**Backward compatibility**: Any existing code that does `import { EndpointError } from 'shared/errors.js'` continues to work identically. The re-export ensures the same class is obtained regardless of import path.

#### 3. Import Path Updates: 14 files

Changed `import { EndpointError } from '../shared/errors.js'` → `import { EndpointError } from '../shared/endpoint-error.js'` in:

**Upstream camp-to-camp files (9 files):**

| File | Module | Usage |
|---|---|---|
| `src/ogc-api/endpoint.ts` | OGC API | Thrown by endpoint methods |
| `src/ogc-api/endpoint.spec.ts` | OGC API tests | Assertion target |
| `src/ogc-api/info.ts` | OGC API | Thrown for info errors |
| `src/ogc-api/link-utils.ts` | OGC API | Thrown for missing links |
| `src/stac/endpoint.ts` | STAC | Thrown by STAC endpoint methods |
| `src/stac/endpoint.spec.ts` | STAC tests | Assertion target |
| `src/stac/info.ts` | STAC | Thrown for STAC info errors |
| `src/stac/link-utils.ts` | STAC | Thrown for missing STAC links |
| `src/stac/link-utils.spec.ts` | STAC tests | Assertion target |

**CSAPI files from OS4CSAPI fork (5 files):**

| File | Module | Usage |
|---|---|---|
| `src/ogc-api/csapi/url_builder.ts` | CSAPI | Thrown by `assertResourceAvailable()` |
| `src/ogc-api/csapi/url_builder.spec.ts` | CSAPI tests | Assertion target |
| `src/ogc-api/csapi/integration/command.spec.ts` | CSAPI integration tests | Assertion target |
| `src/ogc-api/csapi/integration/discovery.spec.ts` | CSAPI integration tests | Assertion target |
| `src/ogc-api/csapi/integration/navigation.spec.ts` | CSAPI integration tests | Assertion target |

#### 4. Export Re-routing: `src/index.ts`

The public barrel export was updated to source `EndpointError` from the new module:

```typescript
// Before:
export { check, ServiceExceptionError, EndpointError } from './shared/errors.js';

// After:
export { check, ServiceExceptionError } from './shared/errors.js';
export { EndpointError } from './shared/endpoint-error.js';
```

**Backward compatibility**: The public API surface is unchanged. `import { EndpointError } from 'ogc-client'` resolves to the same class.

#### 5. Vite Config Cleanup: `demo/vite.config.ts`

Removed the `@rgrove/parse-xml` alias workaround that was previously needed to resolve the transitive dependency at build time:

```diff
- '@rgrove/parse-xml': path.resolve(__dirname, '../node_modules/@rgrove/parse-xml'),
```

This was a demo-only workaround that became unnecessary after the refactor.

---

### Why This Change Was Made

The `EndpointError` class lived in `src/shared/errors.ts` alongside `ServiceExceptionError`, which parses XML error responses from legacy OWS services (WMS, WFS, etc.). Because of this co-location:

```
CSAPIQueryBuilder
  └─→ import { EndpointError } from 'shared/errors.ts'
        └─→ errors.ts also imports @rgrove/parse-xml (for ServiceExceptionError)
        └─→ errors.ts also imports xml-utils.ts (XML DOM utilities)
```

**Any code importing CSAPIQueryBuilder — or any CSAPI module that uses EndpointError — transitively pulled in the entire XML parsing library**, even though CSAPI is a JSON-only API that never uses XML.

This caused:
- **Vite build failures** in browser environments without Node.js `stream` polyfill
- **Unnecessary bundle bloat** (~40KB of XML parsing code for JSON-only consumers)
- **Tree-shaking failure** — the module-level imports in `errors.ts` prevented bundlers from eliminating unused XML code

The refactor eliminated this transitive dependency by moving `EndpointError` (zero dependencies) to its own file, so CSAPI consumers' import graphs never reach the XML parsing stack.

---

### Verification

| Check | Result |
|---|---|
| All 317 tests in affected suites pass | ✅ |
| `errors.spec.ts`: 19/19 pass | ✅ |
| `url_builder.spec.ts`: 298/298 pass | ✅ |
| Public API surface unchanged | ✅ |
| Backward-compatible re-export in `errors.ts` | ✅ |
| `instanceof EndpointError` works across import paths | ✅ |
| Demo builds without `@rgrove/parse-xml` alias | ✅ |

---

## What Was NOT Changed

All demo app workarounds were implemented **outside** the library source:

| Workaround | Finding | Implemented In | Library Touched? |
|---|---|---|---|
| URL path normalization (`controlStreams` → `controlstreams`) | [F-17 / Issue #20](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/20) | `demo/src/csapi-bridge.ts` | **No** |
| controlStream schema field names | [S-10](./crud-smoke-test-phase-2-findings.md) | `demo/src/pages/SmokeTestPage.vue` | **No** |
| controlStream UPDATE fetch-then-merge | [S-12](./crud-smoke-test-phase-2-findings.md) | `demo/src/pages/SmokeTestPage.vue` | **No** |
| Observations/commands immutable (CRD) | [S-13](./crud-smoke-test-phase-2-findings.md) | `demo/src/pages/SmokeTestPage.vue` | **No** |
| Commands async dispatch (CREATE-only) | [S-14](./crud-smoke-test-phase-2-findings.md) | `demo/src/pages/SmokeTestPage.vue` | **No** |
| Schema URL `f=` param removal | [F-13](./schema-display-findings.md) | `demo/src/csapi-bridge.ts` | **No** |
| Content-Type negotiation | [F-15](./crud-smoke-test-findings.md) | `demo/src/api.ts` | **No** |
| Nested parent URLs for Part 2 creates | [F-16](./crud-smoke-test-findings.md) | `demo/src/csapi-bridge.ts` | **No** |
| Conformance bypass (direct CSAPIQueryBuilder) | [Architecture notes](./conformance-bypass-architecture-notes.md) | `demo/src/csapi-bridge.ts` | **No** |

---

## Upstream Contribution Assessment

The `e73cff8` refactor is explicitly designed as an **upstream-ready contribution**:

1. **For the camp-to-camp `ogc-client` repo**: The 9 upstream files changed are pure import path updates with full backward compatibility. The refactor improves modularity for all consumers, not just CSAPI.

2. **For the OS4CSAPI `ogc-client-CSAPI_2` repo**: The 5 CSAPI files changed are also pure import path updates. This change should be contributed upstream *first* (to camp-to-camp), then the CSAPI fork rebases on it.

3. **The new `src/shared/endpoint-error.ts` file**: This is a net-new file that doesn't conflict with any existing code. It extracts functionality rather than modifying it.

This was identified as the **highest-priority architectural fix** in both the [Library Integration Report](./library-integration-report.md) (Finding #15) and the [Library Findings Gap Analysis](./library-findings-gap-analysis.md) (F-6).

---

## Related Documents

| Document | Relevance |
|---|---|
| [Library Integration Report](./library-integration-report.md) | Finding #15 identified the transitive dependency problem |
| [Library Findings Gap Analysis](./library-findings-gap-analysis.md) | F-6 tracks the finding and its resolution |
| [EndpointError Isolation Report](./endpoint-error-isolation-report.md) | Detailed implementation report for commit `e73cff8` |
| [Conformance Bypass Architecture Notes](./conformance-bypass-architecture-notes.md) | Why the demo bypasses `OgcApiEndpoint` (related architectural context) |
| [CRUD Smoke Test Phase 2 Findings](./crud-smoke-test-phase-2-findings.md) | All demo-only workarounds (F-17, S-10–S-14) — none touch library source |
| [CRUD Smoke Test Findings](./crud-smoke-test-findings.md) | Earlier demo-only workarounds (F-15, F-16, S-8) — none touch library source |

---

## Conclusion

The demo app fork (`ogc-csapi-explorer`) modified library source code in **exactly one commit** (`e73cff8`), which is a zero-behavioral-impact structural refactor that was the top recommended upstream contribution. Every other workaround — URL casing, field name mapping, schema fetch-then-merge, immutability handling, async command dispatch — was implemented in the demo app layer (`demo/src/`) without touching `src/`.

The library source in this fork remains suitable for clean upstream contribution via cherry-pick or PR.
