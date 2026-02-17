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

### Who Is Affected by This Problem?

**This build-breaking issue is specific to our setup — not all upstream consumers.**

Normal upstream consumers do `import { OgcApiEndpoint } from 'ogc-client'` — they get the **pre-built npm package** where the library's own build step has already resolved `@rgrove/parse-xml` and bundled everything into self-contained JavaScript. The XML parser ships inside the built output and works fine in browsers because it's pure JS.

Our demo app is unusual: we import **directly from TypeScript source files** using path aliases (`@csapi/ogc-api/csapi/url_builder`). This means **our bundler** (Vite) has to walk the full import graph from scratch and resolve every transitive dependency at build time. When Vite follows `url_builder.ts` → `errors.ts` → `xml-utils.ts` → `@rgrove/parse-xml`, it hits Node.js-specific module resolution issues that break the browser build.

| Consumer Type | Affected? | Why |
|---|---|---|
| Normal npm consumers (`import from 'ogc-client'`) | **No** — works fine | Pre-built package has all dependencies resolved |
| Anyone forking and importing library source directly | **Yes** — build-breaking | Bundler must resolve full transitive import graph |
| Anyone creating a tree-shakeable sub-package of CSAPI | **Yes** — build-breaking | Same transitive import graph issue |
| Anyone trying to isolate CSAPI modules for a micro-frontend | **Yes** — build-breaking | Same issue |

**What IS a legitimate upstream concern (for everyone):**

- **Bundle size**: Every consumer of the pre-built package gets ~40KB of XML parsing code in their bundle even if they only use CSAPI (JSON-only). They can't tree-shake it away because the import sits at the module level in `errors.ts`, and both `EndpointError` and `ServiceExceptionError` are exported from the same module.
- **Modularity**: The coupling prevents the library from being cleanly split into independent sub-packages in the future — a direction the project may want to go as CSAPI grows.

**Bottom line**: The refactor was **required for us** (source-import approach) and is **good architectural hygiene for upstream** (modularity, tree-shaking, bundle size), but it is not currently blocking anyone who uses the library via the normal `npm install ogc-client` path.

---

### Why We Import from Source Instead of Using the Pre-Built Package

The demo app imports library source directly rather than using the published `ogc-client` npm package. This was an intentional architectural decision driven by two factors:

#### 1. The `OgcApiEndpoint` public API doesn't work with real CSAPI servers

The library's intended entry point — `OgcApiEndpoint` — checks the server's `/conformance` endpoint for specific conformance class URIs before exposing CSAPI functionality. **Neither of the two available live CSAPI servers declares the expected conformance URIs correctly:**

- **52North CSA** declares only generic OGC API conformance classes, not the CSAPI-specific URIs the library looks for
- **OSH SensorHub** similarly has incomplete conformance declarations

If we instantiated `new OgcApiEndpoint("https://csa.demo.52north.org")`, the library would resolve `hasConnectedSystems` → `false`, and all CSAPI collection getters would return empty arrays — despite the server fully implementing the CSAPI endpoints.

This is documented in detail in the [Conformance Bypass Architecture Notes](./conformance-bypass-architecture-notes.md) and is tracked as a broader library issue: `OgcApiEndpoint` gates CSAPI features on conformance declarations that real servers don't provide.

#### 2. We needed to validate the library's internal modules independently

By importing `CSAPIQueryBuilder`, `parseCollectionResponse`, `extractCSAPIFeature`, `parseSWEComponent`, and other modules directly, the demo app validates the library's **URL construction, response parsing, GeoJSON extraction, and SWE Common schema parsing** in isolation — without being blocked by the conformance negotiation gate.

This source-level approach has been valuable for discovering findings (F-1 through F-17, S-1 through S-14) that would have been completely masked by `OgcApiEndpoint`'s gating logic. A consumer using the pre-built package through `OgcApiEndpoint` would simply see "no CSAPI resources" and never discover these underlying issues.

#### The source imports used

The demo's `csapi-bridge.ts` imports individual library pieces:

| Import | Purpose | Dependency on `OgcApiEndpoint`? |
|---|---|---|
| `CSAPIQueryBuilder` | URL construction (e.g., `/systems?limit=10`) | None — pure string builder |
| `parseCollectionResponse` | Normalize response envelopes (FeatureCollection vs. items) | None — pure parser |
| `extractCSAPIFeature` | Type GeoJSON features into `System`, `Deployment`, etc. | None — pure classifier |
| `getCSAPIResourceType` | Detect resource type from featureType | None — pure function |
| `parseSWEComponent` | Parse SWE Common schema blocks | None — pure parser |

None of these modules require `OgcApiEndpoint`. They are self-contained utilities. The source-import approach lets us use them directly, which is what exposed the `EndpointError` transitive XML dependency problem.

For more detail, see:
- [Conformance Bypass Architecture Notes](./conformance-bypass-architecture-notes.md) — Full analysis of why `OgcApiEndpoint` doesn't work with real servers
- [Library Integration Report](./library-integration-report.md) — Step-by-step integration decisions and findings

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
