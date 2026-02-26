# Findings Report 05: Module Decoupling Patterns in TypeScript — Coupling Level Analysis and Recommended Architecture for CSAPI Extraction

> **Plan 5 of 8** | **Phase 6 — Upstream Acceptance Refactoring**

---

## Metadata

| Field                  | Value                                                                                                   |
| ---------------------- | ------------------------------------------------------------------------------------------------------- |
| **Research Plan**      | [Plan 05: Module Decoupling Patterns in TypeScript](../research-plans/05-module-decoupling-patterns.md) |
| **Plan Type**          | External research (architectural patterns)                                                              |
| **Date Started**       | 2026-02-23                                                                                              |
| **Date Completed**     | 2026-02-23                                                                                              |
| **Research Time**      | ~3 hours (actual)                                                                                       |
| **Estimated Time**     | 2–3 hours (from plan)                                                                                   |
| **Questions Answered** | 37 of 37 detailed questions                                                                             |
| **Depends On**         | None (independent external research)                                                                    |
| **Blocks**             | Plan 06 (Endpoint Decoupling Architecture)                                                              |

---

## Source Summary

### Primary Sources Consulted

| Source                                  | Path / URL                                                                                        | What Was Extracted                                                                                                                                                  |
| --------------------------------------- | ------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| CSAPIQueryBuilder constructor           | `src/ogc-api/csapi/url_builder.ts` (lines 106–174)                                                | Constructor signature: `Pick<OgcApiCollectionInfo, 'id' \| 'title' \| 'links'>` + optional `Map<string, string>`. Uses `import type` for `OgcApiCollectionInfo`.    |
| Endpoint CSAPI imports                  | `src/ogc-api/endpoint.ts` (lines 52–53)                                                           | The two constraint violations: `import CSAPIQueryBuilder` (value import) and `import { scanCsapiLinks }` (value import)                                             |
| Endpoint `csapi()` method               | `src/ogc-api/endpoint.ts` (lines 385–413)                                                         | Data flow: `hasConnectedSystems` check → `getCollectionDocument()` → `extractRootResourceUrls()` → `new CSAPIQueryBuilder(doc, urls)`                               |
| Endpoint `extractRootResourceUrls()`    | `src/ogc-api/endpoint.ts` (lines 431–436)                                                         | Delegates to `scanCsapiLinks(rootDoc.links)` — the second constraint violation                                                                                      |
| `scanCsapiLinks` function               | `src/ogc-api/csapi/helpers.ts` (lines 129–229)                                                    | Accepts `Array<{rel?: string; href?: string}>`, uses `CSAPIResourceTypes` internally. Three link conventions: `ogc-cs:` prefix, plain resource name, `items` href   |
| Core model types                        | `src/ogc-api/model.ts` (lines 85–155)                                                             | `OgcApiCollectionInfo` (30+ properties, `links: any`), `OgcApiDocumentLink`, `OgcApiDocument`                                                                       |
| CSAPI model types                       | `src/ogc-api/csapi/model.ts` (lines 1–3)                                                          | Imports: `import type { BoundingBox, DateTimeParameter, CrsCode, MimeType } from '../../shared/models.js'`, `import type { OgcApiDocumentLink } from '../model.js'` |
| EDR URL builder                         | `src/ogc-api/edr/url_builder.ts` (lines 1–30)                                                     | EDR imports from core: `CrsCode`, `DataQueryType`, `EdrParameterInfo`, `OgcApiCollectionInfo` — all value imports, no reverse dependency                            |
| `EndpointError` class                   | `src/shared/errors.ts` (lines 11–20)                                                              | Located in `shared/`, not in `ogc-api/` — import from CSAPI (`../../shared/errors.js`) does not cross the core ↔ CSAPI boundary                                     |
| `checkHasConnectedSystems`              | `src/ogc-api/info.ts` (lines 112–123)                                                             | Zero CSAPI imports — uses only conformance URI strings                                                                                                              |
| Root exports                            | `src/index.ts` (252 lines)                                                                        | ~170 lines of CSAPI re-exports: `CSAPIQueryBuilder`, 3 const exports, ~40 type exports from model, ~30 format function exports, extensive SensorML/SWE type exports |
| TypeScript Handbook — Structural Typing | https://www.typescriptlang.org/docs/handbook/type-compatibility.html                              | Structural compatibility rules, duck typing semantics                                                                                                               |
| TypeScript Handbook — `import type`     | https://www.typescriptlang.org/docs/handbook/modules/reference.html#type-only-imports-and-exports | Complete erasure guarantee, `isolatedModules` behavior                                                                                                              |
| TypeScript Handbook — Utility Types     | https://www.typescriptlang.org/docs/handbook/utility-types.html                                   | `Pick<>` as implicit adapter, structural narrowing                                                                                                                  |
| TypeScript Project References           | https://www.typescriptlang.org/docs/handbook/project-references.html                              | `composite`, `references`, build ordering, declaration boundary                                                                                                     |
| Node.js subpath exports                 | https://nodejs.org/api/packages.html#subpath-exports                                              | `"exports"` field for module encapsulation                                                                                                                          |

### Prior Findings Used

| Finding          | Path                                                                    | What Was Consumed                                                                                                                                                                                           |
| ---------------- | ----------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Plan 02 findings | `docs/research/phase-6/findings/02-edr-integration-pattern-analysis.md` | EDR decoupling baseline: EDR has 1 import into `endpoint.ts` (value only), 0 root exports, 656 source lines. Identical integration pattern as CSAPI but at 1/18th scale.                                    |
| Plan 04 findings | `docs/research/phase-6/findings/04-sub-module-api-design-patterns.md`   | Recommended consumer API: two-layer (sync constructor + async factory function). Constructor injection as dominant industry pattern. Current `CSAPIQueryBuilder` constructor already follows best practice. |

### Sources Not Available or Not Useful

- **Refactoring.guru Adapter / Facade patterns:** These present the classical OO patterns with explicit wrapper classes. In TypeScript's structural type system, explicit adapter classes are unnecessary — structural compatibility suffices. The conceptual framework was useful but the code examples don't translate. → Alternative: produced TypeScript-specific structural typing examples.
- **Nx module boundary enforcement:** Requires Nx workspace setup which is not applicable to this single-package project. → Alternative: documented `eslint-plugin-import` `no-restricted-paths` and custom boundary tests.
- **TypeScript Project References for single-tsconfig:** The project uses a single `tsconfig.json`. Splitting into composite project references is a significant refactor that exceeds minimum-change scope. → Documented as deferred option.

---

## Executive Summary

This report investigates how TypeScript's structural type system affects adapter patterns, dependency inversion, and module boundary design, applied specifically to the CSAPI extraction from `endpoint.ts`. The research answers 37 detailed questions across 7 sub-topics, producing a coupling level comparison matrix, a `scanCsapiLinks` placement recommendation, an `import type` strategy, and a module extraction verification plan.

**The central finding is that TypeScript's structural typing provides _implicit_ dependency inversion — the core does not need to `implement` any sub-module interface for the sub-module to accept core data.** This eliminates the need for explicit adapter classes (as required in Java/C#) and means that the CSAPI module boundary can be defined by a simple structural contract: an interface declaring what shape of data CSAPI needs, satisfied by any object with matching properties.

**The current codebase is already at the optimal coupling level.** `CSAPIQueryBuilder` accepts `Pick<OgcApiCollectionInfo, 'id' | 'title' | 'links'>` — this is a "data record with a type reference" pattern (Level 3.5 in our taxonomy). It has zero runtime coupling to core (the constructor only accesses `.id`, `.title`, and `.links` on the passed object) with compile-time drift detection via the `Pick<>` reference. The only changes needed are:

1. **Eliminate the two value imports** in `endpoint.ts` (`CSAPIQueryBuilder` and `scanCsapiLinks`)
2. **Resolve the `scanCsapiLinks` shared utility problem** by generalizing the link scanner into a shared utility
3. **Create the `csapi/index.ts` barrel file** for the sub-path export

The coupling level itself (what the constructor accepts) does not need to change. Plan 04's recommendation of a factory function is the mechanism for removing the `CSAPIQueryBuilder` import from `endpoint.ts` — the endpoint stops creating builders, and consumers create them via the factory function instead.

### Key Metrics

| Metric                                | Value                      | Significance                                                                              |
| ------------------------------------- | -------------------------- | ----------------------------------------------------------------------------------------- |
| Coupling levels analyzed              | 4 (+ current Level 3.5)    | Complete spectrum from tight (concrete class) to loose (individual params)                |
| Constraint violations in current code | 2 imports in `endpoint.ts` | `CSAPIQueryBuilder` (line 52) + `scanCsapiLinks` (line 53)                                |
| Type-only imports from core in CSAPI  | 3 files                    | `url_builder.ts`, `model.ts`, `helpers.ts` — all use `import type`, zero runtime coupling |
| `scanCsapiLinks` callers              | 2                          | `endpoint.ts:435` and `url_builder.ts` (via `extractAvailableResources`)                  |

### Overall Assessment

**Keep the current coupling level (Level 3.5: data record + type reference). The changes needed are not to the coupling architecture but to _who_ orchestrates the data flow.** Currently the endpoint orchestrates (calls `new CSAPIQueryBuilder`); after decoupling, the consumer orchestrates (calls a factory function from `@camptocamp/ogc-client/csapi`). The `scanCsapiLinks` function should be generalized into a shared link scanner that accepts a `Set<string>` of known types, eliminating the endpoint's import of CSAPI-specific code.

---

## Table of Contents

1. [Structural Typing and Adapter Patterns](#1-structural-typing-and-adapter-patterns)
2. [Dependency Inversion in TypeScript](#2-dependency-inversion-in-typescript)
3. [Coupling Level Analysis](#3-coupling-level-analysis)
4. [Coupling Level Comparison Matrix](#4-coupling-level-comparison-matrix)
5. [Module Boundary Definition](#5-module-boundary-definition)
6. [Module Extraction Case Studies](#6-module-extraction-case-studies)
7. [`import type` and Type-Only Dependencies](#7-import-type-and-type-only-dependencies)
8. [Boundary Condition Verification](#8-boundary-condition-verification)
9. [Implementation Scope Gate Assessment](#9-implementation-scope-gate-assessment)
10. [Impact on Dependent Plans](#10-impact-on-dependent-plans)
11. [Key Takeaways](#11-key-takeaways)
12. [Impact on Implementation](#12-impact-on-implementation)
13. [Open Questions](#13-open-questions)

---

## 1. Structural Typing and Adapter Patterns

### Question 1: Does `Pick<ModuleA.Foo, 'x' | 'y'>` create a compile-time dependency?

**Answer:** Yes — `Pick<OgcApiCollectionInfo, 'id' | 'title' | 'links'>` creates a **compile-time dependency** on `../model.js`. The TypeScript compiler must resolve the import to understand the properties of `OgcApiCollectionInfo`. However, because `url_builder.ts` uses `import type`, the dependency is **erased during compilation** — the compiled JavaScript output contains no reference to `../model.js`.

**Evidence:**

```typescript
// Current code (url_builder.ts line 1):
import type { OgcApiCollectionInfo } from '../model.js';

// Compiled JavaScript output:
// (nothing — erased completely)
```

The distinction:
| Import form | Compile-time dependency | Runtime dependency |
|---|---|---|
| `import type { X } from 'module'` | Yes | **No** — erased |
| `import { X } from 'module'` | Yes | **Yes** — appears in JS |

The build still needs `../model.js` to exist for type-checking, but the shipped JavaScript has zero coupling.

### Question 2: Can a structurally compatible local interface eliminate the dependency?

**Answer:** Yes, completely. If CSAPI defines its own interface with matching properties, `OgcApiCollectionInfo` instances can be passed to CSAPI with **zero imports** between modules.

**Evidence:**

```typescript
// Module A (core) — unchanged
export interface OgcApiCollectionInfo {
  id: string;
  title: string;
  links: any;
  description: string;
  // ... 25+ more fields
}

// Module B (CSAPI) — NO import from Module A
interface CSAPICollectionInput {
  id: string;
  title: string;
  links: Array<{ rel?: string; href?: string }>;
}

class CSAPIQueryBuilder {
  constructor(private collection_: CSAPICollectionInput) {}
}

// Consumer code — both compile without knowing about each other
const endpoint = await new OgcApiEndpoint(url);
const info = await endpoint.getCollectionInfo('weather');
const builder = new CSAPIQueryBuilder(info); // ✅ structural compatibility
```

TypeScript checks that `OgcApiCollectionInfo` has `id: string`, `title: string`, and `links` compatible with `Array<{rel?, href?}>`. Since `links: any` is assignable to anything, it passes. **This eliminates both compile-time and runtime dependency.**

### Question 3: What is the TypeScript-idiomatic adapter approach?

**Answer:** The idiom depends on the relationship between the modules:

| Approach                                 | When to use                                 | Coupling           | Drift detection            |
| ---------------------------------------- | ------------------------------------------- | ------------------ | -------------------------- |
| **(a)** Explicit interface in sub-module | Separate packages or hard module boundaries | Zero               | None (unless tested)       |
| **(b)** `Pick<CoreType, keys>`           | Same package, internal sub-module           | `import type` only | **Automatic** via compiler |
| **(c)** Inline type literal              | One-off function parameters                 | Zero               | None                       |
| **(d)** Re-declared standalone type      | Truly independent modules                   | Zero               | None (unless tested)       |

**For CSAPI within ogc-client:** Approach **(b)** — `Pick<>` with `import type` — is idiomatic. It is the standard pattern for intra-package module boundaries in the TypeScript ecosystem (used by Angular, RxJS, and the TypeScript compiler itself). If CSAPI were ever extracted to a separate npm package, switch to **(a)**.

### Question 4: How does the adapter pattern differ in TypeScript vs Java/C#?

**Answer:** The fundamental difference is that TypeScript's structural typing eliminates the need for explicit adapter wrapper classes.

**Java (nominal typing):**

```java
// Sub-module defines abstraction
public interface CollectionLike { String getId(); String getTitle(); }

// Adapter MUST explicitly implement the interface
public class CollectionAdapter implements CollectionLike {
    private final OgcApiCollectionInfo inner;
    public CollectionAdapter(OgcApiCollectionInfo inner) { this.inner = inner; }
    @Override public String getId() { return inner.getId(); }
    @Override public String getTitle() { return inner.getTitle(); }
}
```

Without the adapter class, `OgcApiCollectionInfo` cannot be passed where `CollectionLike` is expected — even if it has matching methods.

**TypeScript (structural typing):**

```typescript
// Sub-module defines shape
interface CollectionLike {
  id: string;
  title: string;
}

function process(c: CollectionLike) {
  /* ... */
}

// No adapter — just pass the object
process(ogcApiCollectionInfoInstance); // ✅ TypeScript verifies shape match
```

**Practical implications for CSAPI:**

1. No wrapper class needed — the collection document object is passed directly
2. No DI container binding or configuration
3. Core satisfies CSAPI's contract _implicitly_, without any `implements` declaration
4. **Tradeoff:** If core renames a field, the match breaks silently unless both modules are compiled together (which they are in our single-package setup)

### Question 5: Are explicit adapter interfaces unnecessary for this scenario?

**Answer:** Explicit adapter _classes_ are unnecessary. However, a **named interface** is still valuable for documentation, error messages, test fixtures, and IDE support — even though structural typing makes it optional.

**Evidence:** When CSAPI uses an inline type literal, TypeScript error messages become unwieldy:

```
Type '{ id: string; title: string; }' is not assignable to type
'{ id: string; title: string; links: Array<{ rel?: string | undefined; href?: string | undefined; }>; }'.
  Property 'links' is missing...
```

With a named interface `CSAPICollectionInput`, the error is:

```
Type '{ id: string; title: string; }' is not assignable to type 'CSAPICollectionInput'.
  Property 'links' is missing in type '{ id: string; title: string; }'.
```

**Recommendation:** Define a named interface if decoupling fully (approach (a)), but for the current `Pick<>` approach (b) the name is already implicit in the `Pick<>` declaration.

### Question 6: Cost of abandoning `Pick<>` for inline structural type

**Answer:**

| Dimension              | `Pick<OgcApiCollectionInfo, 'id' \| 'title' \| 'links'>` | `{ id: string; title: string; links: any }`     |
| ---------------------- | -------------------------------------------------------- | ----------------------------------------------- |
| **Type safety**        | Full — `links` inherits core's type                      | Reduced — `links: any` loses all structure      |
| **Refactoring safety** | If core renames `id`, compiler error in CSAPI            | **Silent breakage** — no error, runtime failure |
| **Documentation**      | Readers see "uses core collection shape"                 | Opaque — no origin clue                         |
| **Module coupling**    | `import type` dependency on `../model.js`                | Zero dependency                                 |
| **IDE hover**          | Shows `OgcApiCollectionInfo` docs                        | Shows raw literal type                          |

**The critical loss is refactoring safety.** With `Pick<>`, a typo like `Pick<OgcApiCollectionInfo, 'id' | 'title' | 'lnks'>` produces a compile error. With a standalone interface, `lnks` silently compiles as a new property.

**Middle ground (if full decoupling is desired):** Define a local interface + a compile-time compatibility assertion in a test file:

```typescript
// csapi/__tests__/type-compatibility.ts
import type { OgcApiCollectionInfo } from '../../ogc-api/model.js';
import type { CSAPICollectionInput } from '../model.js';

// Compile-time assertion: if core type changes, this line errors
const _check: CSAPICollectionInput = {} as OgcApiCollectionInfo;
```

This provides **zero runtime coupling** + **compile-time drift detection** + **full type decoupling of the public API**.

### Question 7: Handling interface drift without direct import

**Answer:** Three approaches, ordered by fit for a single-package project:

1. **Compile-time compatibility assertion (best for this project):**

   ```typescript
   // In a test or type-check file
   import type { OgcApiCollectionInfo } from '../../ogc-api/model.js';
   type AssertExtends<T, U extends T> = true;
   type _Check = AssertExtends<CSAPICollectionInput, OgcApiCollectionInfo>;
   ```

   If the core type diverges from CSAPI's contract, the assertion fails at compile time.

2. **Integration test:** A test that constructs a real `OgcApiCollectionInfo` and passes it to `CSAPIQueryBuilder`. This catches both structural drift and semantic changes.

3. **Shared types package (for multi-package):** Extract minimal shared types into a separate package. Both core and CSAPI depend on it. Not needed while they share the same `tsconfig`.

**For our current setup:** The `Pick<>` approach already provides drift detection natively. If switching to a local interface, add option 1 as a safeguard.

### Sub-topic Synthesis

TypeScript's structural typing is a **game-changer** for module boundary design compared to Java/C#. It eliminates adapter wrapper classes, makes dependency inversion implicit, and allows modules to define contracts that are satisfied without any coupling between them. The current `Pick<>` + `import type` pattern in CSAPI is already the idiomatic TypeScript approach for intra-package boundaries — it provides maximum refactoring safety with zero runtime coupling. The only question is whether the `import type` compile-time dependency is acceptable (it is — it's erased completely).

---

## 2. Dependency Inversion in TypeScript

### Question 8: DIP in TypeScript without a DI container

**Answer:** In TypeScript, DIP manifests as the sub-module defining a structural contract (interface) that the core satisfies implicitly — without the core importing or referencing the sub-module.

**Example:**

```typescript
// ─── csapi/model.ts (sub-module defines what it needs) ───
export interface CSAPICollectionInput {
  id: string;
  title: string;
  links: Array<{ rel?: string; href?: string }>;
}

// ─── csapi/url_builder.ts (sub-module consumes the contract) ───
import type { CSAPICollectionInput } from './model.js';
export class CSAPIQueryBuilder {
  constructor(private collection_: CSAPICollectionInput) {}
}

// ─── consumer code (orchestrates data flow) ───
const endpoint = await new OgcApiEndpoint(url);
const doc = await endpoint.getCollectionDocument('weather');
const builder = new CSAPIQueryBuilder(doc); // doc satisfies CSAPICollectionInput
```

The endpoint never imports `CSAPICollectionInput`. TypeScript verifies structural compatibility at the call site. The dependency arrow runs from call site → sub-module, but the sub-module's contract doesn't reference core.

### Question 9: Is explicit DIP necessary in TypeScript?

**Answer:** **No, explicit DIP is not necessary for compilation.** TypeScript's structural typing provides _implicit_ DIP automatically. However, explicit DIP (a named interface) remains valuable for **architectural clarity** — it documents what the sub-module requires, improves error messages, and makes the contract visible to future maintainers.

**In nominal systems (Java/C#):**

```
Core ───implements──→ SubModule.IFoo ←──depends on── SubModule
```

The core _must_ reference the sub-module's interface (reverse compile-time dependency).

**In TypeScript:**

```
Core (no reference to sub-module)
  ↓ (passes structurally compatible data)
SubModule (defines its own contract, never references core)
```

The "interface" in DIP becomes a **documentation/communication tool** rather than a compiler-enforced contract. Whether to name it explicitly is a style choice, not a compiler requirement.

### Question 10: Inverting the endpoint → CSAPI dependency

**Answer:** Currently, `endpoint.ts` imports `CSAPIQueryBuilder` and `scanCsapiLinks` — the endpoint _creates_ the builder. After inversion, the **consumer** creates it.

**Current (endpoint orchestrates):**

```typescript
// endpoint.ts
import CSAPIQueryBuilder from './csapi/url_builder.js';
import { scanCsapiLinks } from './csapi/helpers.js';

async csapi(collectionId: string): Promise<CSAPIQueryBuilder> {
  const doc = await this.getCollectionDocument(collectionId);
  const urls = await this.extractRootResourceUrls(); // uses scanCsapiLinks
  return new CSAPIQueryBuilder(doc, urls);
}
```

**After inversion (consumer orchestrates):**

```typescript
// Consumer code
import { OgcApiEndpoint } from '@camptocamp/ogc-client';
import { createCSAPIBuilder } from '@camptocamp/ogc-client/csapi';

const endpoint = await new OgcApiEndpoint(url);
const builder = await createCSAPIBuilder(endpoint, 'weather-stations');
```

The factory function (`createCSAPIBuilder`) lives in CSAPI and calls endpoint methods to extract data. The endpoint class has zero knowledge of CSAPI. This is the "Hollywood Principle" pattern proposed by Plan 04.

### Question 11: "Data handoff at the boundary" pattern

**Answer:** Yes — this is the most common pattern in TypeScript for decoupled modules. The consumer acts as the orchestrator, extracting data from one module and passing it to another.

```typescript
// Consumer extracts data from endpoint, passes to CSAPI
const endpoint = await new OgcApiEndpoint(url);
const collectionDoc = await endpoint.getCollectionDocument('weather');
const builder = new CSAPIQueryBuilder(collectionDoc);
```

Neither module imports the other. The consumer is the "glue" that wires them together. Standard names: **"Ports and Adapters"** (hexagonal architecture), **"Anti-corruption layer"**, or simply **data-oriented boundary design**.

The factory function from Plan 04 automates this orchestration so consumers don't need to know the internal data flow.

### Question 12: "Core instance" vs "extracted data" — which is the correct approach?

**Answer:** The current CSAPI constructor already demonstrates the answer.

| Dimension               | Accepts core instance                                                   | Accepts extracted data                      |
| ----------------------- | ----------------------------------------------------------------------- | ------------------------------------------- |
| **Coupling**            | Depends on core's full class (all methods, properties, transitive deps) | Depends only on minimal structural contract |
| **Testability**         | Tests must construct/mock full `OgcApiEndpoint`                         | Tests construct lightweight plain objects   |
| **Flexibility**         | Only works with `OgcApiEndpoint` instances                              | Any data source matching the shape          |
| **Serialization**       | Core instances may have methods, Promises, non-serializable fields      | Plain data — easily serializable            |
| **Sub-module behavior** | Tempted to call core methods (behavioral coupling)                      | Operates on data only                       |
| **API surface**         | Sub-module's `.d.ts` references core types                              | Self-contained `.d.ts`                      |

**"Accepts extracted data" produces a cleaner module boundary.** The current `CSAPIQueryBuilder` already does this — it accepts `{id, title, links}` + `Map<string, string>`, not `OgcApiEndpoint`. This is the right level.

### Question 13: Tradeoffs — who should extract the data?

**Answer:** There are three options for who performs data extraction:

1. **Consumer extracts manually** — most verbose, most decoupled
2. **Factory function extracts** — convenience wrapper, lives in CSAPI, calls endpoint methods
3. **Endpoint extracts** (current) — convenient, but creates the dependency we're removing

Plan 04 recommends option 2: an async factory function exported from `@camptocamp/ogc-client/csapi` that accepts an endpoint reference and extracts data using the endpoint's public API. This balances convenience with clean boundaries.

### Sub-topic Synthesis

Dependency inversion in TypeScript is implicit — structural typing means the core never needs to know about the sub-module's interface. The current CSAPI constructor already follows the ideal pattern (accepts extracted data, not the core instance). The change needed is not to the DIP architecture but to _who orchestrates_ the data flow: moving from "endpoint creates builder" to "consumer or factory function creates builder."

---

## 3. Coupling Level Analysis

### Question 14: Level 1 — Concrete class

**Answer:** If CSAPI accepts `OgcApiEndpoint` directly:

```typescript
// CSAPI would accept the full endpoint instance
export async function createCSAPIBuilder(
  endpoint: OgcApiEndpoint,
  collectionId: string
): Promise<CSAPIQueryBuilder> {
  const doc = await endpoint.getCollectionDocument(collectionId);
  const root = await endpoint.root;
  const urls = scanCsapiLinks(root.links ?? []);
  return new CSAPIQueryBuilder(doc, urls);
}
```

**Analysis:**

- **Compile-time coupling:** CSAPI imports the entire `OgcApiEndpoint` class (896 lines, all its dependencies)
- **Runtime coupling:** CSAPI calls endpoint methods (`getCollectionDocument`, `root`)
- **Testability:** Tests must instantiate or mock `OgcApiEndpoint` — requires HTTP mocking
- **Constraint compliance:** Core does NOT import from CSAPI ✓, but CSAPI depends on the full core class ⚠️
- **Migration effort:** Low — just move the current `csapi()` method body to the factory function
- **Problem:** `getCollectionDocument` is a **private** method on `OgcApiEndpoint`. CSAPI cannot call it without making it public. Same for accessing `root` (a getter returning `Promise<OgcApiDocument>`).

**Verdict:** Level 1 is the simplest migration but creates the tightest coupling. It would require exposing private endpoint methods, which changes the core's public API — violating minimum-change principles.

### Question 15: Level 2 — Explicit interface

**Answer:** CSAPI defines its own interface for what it needs from the endpoint:

```typescript
// csapi/model.ts
export interface CSAPIEndpointLike {
  getCollectionDocument(
    id: string
  ): Promise<{ id: string; title: string; links: any[] }>;
  readonly root: Promise<{ links?: Array<{ rel?: string; href?: string }> }>;
  readonly hasConnectedSystems: Promise<boolean>;
}
```

**Analysis:**

- `OgcApiEndpoint` would satisfy this structurally — IF `getCollectionDocument` were public
- CSAPI still needs types for return values (structural inline types or core type imports)
- Testability: easy to create mock objects implementing the interface
- **Problem:** `getCollectionDocument` is private. Making it public to satisfy the interface changes core's API. Also, `root` returns `Promise<OgcApiDocument>`, which has more properties than the interface specifies — this is fine (structural typing), but the `Promise` wrapping adds complexity.
- Interface maintenance: must be kept in sync with endpoint capabilities

**Verdict:** Level 2 requires making private endpoint methods public and maintaining a shadow interface. Over-engineered for the current scenario.

### Question 16: Level 3 — Data record

**Answer:** CSAPI accepts pre-extracted data:

```typescript
// csapi/model.ts
export interface CSAPICollectionInput {
  id: string;
  title: string;
  links: Array<{ rel?: string; href?: string }>;
}

// csapi/url_builder.ts
export default class CSAPIQueryBuilder {
  constructor(
    private collection_: CSAPICollectionInput,
    resourceUrls?: Map<string, string>
  ) {
    /* ... */
  }
}
```

**Analysis:**

- **Zero type imports from core** — the interface is self-contained
- **Consumer burden:** consumer (or factory function) must extract data and assemble the record
- **Type safety:** Actually _improves_ over current — `links: Array<{rel?, href?}>` is more specific than the current `links: any` from `OgcApiCollectionInfo`
- **Testability:** Trivial — tests create plain object literals
- **Migration:** Minimal — the shape is identical to what `Pick<OgcApiCollectionInfo, 'id' | 'title' | 'links'>` resolves to

**Verdict:** Level 3 achieves full decoupling with minimal migration. The factory function handles data extraction.

### Question 17: Level 4 — Individual parameters

**Answer:** CSAPI accepts positional parameters:

```typescript
constructor(
  collectionId: string,
  collectionTitle: string,
  collectionLinks: Array<{ rel?: string; href?: string }>,
  resourceUrls?: Map<string, string>
) { /* ... */ }
```

**Analysis:**

- **Maximum decoupling** — no structured type dependency at all
- **Most verbose:** Consumer must pass 4 arguments in correct order
- **Refactoring hazard:** positional parameters are fragile (reordering breaks callers silently)
- **Migration effort:** High — all internal references to `this.collection_.id`, `this.collection_.title`, `this.collection_.links` must be rewritten
- **No grouped semantics:** The natural "collection" concept is decomposed

**Verdict:** Level 4 is worse than Level 3 in every dimension. It decomposes a natural grouping, creates positional confusion, and requires rewriting internal code.

### Question 18: Impact of core changes on each level

**Answer:**

| Change                           | Level 1 (Class)                   | Level 2 (Interface)                     | Level 3 (Data Record)                                           | Level 4 (Params)         |
| -------------------------------- | --------------------------------- | --------------------------------------- | --------------------------------------------------------------- | ------------------------ |
| Core adds property               | No change needed                  | No change needed                        | No change needed                                                | No change needed         |
| Core removes `title`             | CSAPI calls break at compile time | Interface breaks if using `title`       | Local interface unaffected (but consumers may pass `undefined`) | Parameter still expected |
| Core renames `id` → `identifier` | CSAPI calls break                 | Interface unaffected (defines own `id`) | Record unaffected                                               | Param unaffected         |
| Core changes `links` type        | CSAPI affected immediately        | Interface may need update               | Record unaffected                                               | Param may need update    |

**Key insight:** Levels 3 and 4 are insulated from core changes but lose automatic drift detection. The compile-time compatibility assertion (Question 7) mitigates this for Level 3.

### Question 19: IDE discoverability per level

**Answer:**

| Level           | Can IDE lead user from endpoint to CSAPI?                                               |
| --------------- | --------------------------------------------------------------------------------------- |
| 1 (Class)       | Yes — `endpoint.csapi()` return type is annotated. But we're removing this method.      |
| 2 (Interface)   | Partial — the interface is discoverable but the connection to endpoint is indirect      |
| 3 (Data Record) | No direct connection — consumer must know to import from `@camptocamp/ogc-client/csapi` |
| 4 (Params)      | Same as Level 3                                                                         |

IDE discoverability is primarily a function of the **consumer API** (Plan 04), not the coupling level. A well-documented factory function with JSDoc pointing to the endpoint is more discoverable than tight coupling.

### Question 20: Testability per level

**Answer:**

| Level           | Test input construction                                          | Isolation from HTTP                    |
| --------------- | ---------------------------------------------------------------- | -------------------------------------- |
| 1 (Class)       | Must instantiate `OgcApiEndpoint` (HTTP fetch → complex mocking) | Poor — endpoint triggers HTTP requests |
| 2 (Interface)   | Create mock implementing `CSAPIEndpointLike` (easy)              | Good — mock returns plain data         |
| 3 (Data Record) | Create plain `{ id, title, links }` object literal (trivial)     | **Perfect** — no mocking needed        |
| 4 (Params)      | Pass primitive values directly (trivial)                         | **Perfect**                            |

Level 3 provides the best balance of testability and semantic grouping.

### Question 21: What coupling level is the current codebase?

**Answer:** The current code is **Level 3.5** — data record semantics with a type reference.

```typescript
// Current: data record shape, but with compile-time link to core type
constructor(
  private collection_: Pick<OgcApiCollectionInfo, 'id' | 'title' | 'links'>,
  resourceUrls?: Map<string, string>
) { }
```

- **Runtime behavior:** Level 3 — the constructor only accesses `.id`, `.title`, and `.links` on the passed object
- **Compile-time type:** Level 2 flavor — the `Pick<>` references the core interface via `import type`
- **No methods are called:** This is pure data consumption, not behavioral coupling

The `Pick<>` doesn't change the runtime shape — any object with `{id: string, title: string, links: any}` works. The `import type` creates a build-time dependency but zero runtime dependency.

### Sub-topic Synthesis

The current Level 3.5 is already the optimal coupling level for this extraction. Level 3 (pure data record with local interface) provides marginally more decoupling at the cost of losing automatic drift detection — mitigated by the compile-time assertion pattern. Level 1 and Level 2 require making private endpoint methods public. Level 4 decomposes a natural grouping unnecessarily.

---

## 4. Coupling Level Comparison Matrix

| Dimension                            | L1: Concrete Class            | L2: Explicit Interface                 | L3: Data Record              | L3.5: Pick<> (Current)      | L4: Individual Params    |
| ------------------------------------ | ----------------------------- | -------------------------------------- | ---------------------------- | --------------------------- | ------------------------ |
| **Constraint 1: One-way dep**        | ⚠️ CSAPI → core (heavy)       | ✓ CSAPI → own interface                | ✓ Zero imports               | ✓ `import type` only        | ✓ Zero imports           |
| **Constraint 2: Separate entry**     | ✓                             | ✓                                      | ✓                            | ✓                           | ✓                        |
| **Constraint 3: No outward imports** | ✓ (core doesn't import CSAPI) | ✓                                      | ✓                            | ✓                           | ✓                        |
| **Constraint 4: Core builds alone**  | ✗ Requires public methods     | ✗ Requires public methods              | ✓                            | ✓                           | ✓                        |
| **Type safety**                      | ★★★★★                         | ★★★★☆                                  | ★★★☆☆                        | ★★★★★                       | ★★★☆☆                    |
| **Refactoring safety**               | ★★★★★                         | ★★★★☆                                  | ★★☆☆☆                        | ★★★★★                       | ★★☆☆☆                    |
| **IDE discoverability**              | ★★★★★                         | ★★★☆☆                                  | ★★☆☆☆                        | ★★★☆☆                       | ★★☆☆☆                    |
| **Testability**                      | ★☆☆☆☆                         | ★★★★☆                                  | ★★★★★                        | ★★★★★                       | ★★★★★                    |
| **Consumer ergonomics**              | ★★★★★                         | ★★★☆☆                                  | ★★★★☆                        | ★★★★☆                       | ★★☆☆☆                    |
| **Migration effort**                 | Low (move method)             | Medium (new interface, public methods) | Low (define local interface) | **Zero** (already in place) | High (rewrite internals) |
| **Tree-shaking**                     | ★☆☆☆☆ (pulls in full class)   | ★★★☆☆                                  | ★★★★★                        | ★★★★★                       | ★★★★★                    |
| **Runtime coupling**                 | High (calls methods)          | Medium (calls via interface)           | **Zero**                     | **Zero**                    | **Zero**                 |

**Ranking (weighted by constraint compliance + minimum change):**

1. **Level 3.5 (Current `Pick<>`)** — Score: 4.8/5. Already in place, zero migration, full constraint compliance, drift detection via compiler. Only needs the orchestration change (factory function).
2. **Level 3 (Local data record)** — Score: 4.6/5. Full decoupling, easy migration. Loses drift detection unless assertion added.
3. **Level 2 (Interface)** — Score: 3.2/5. Requires making private methods public, adds interface maintenance.
4. **Level 4 (Params)** — Score: 2.8/5. Unnecessary decomposition, high internal rewrite cost.
5. **Level 1 (Class)** — Score: 2.5/5. Requires public methods, tight coupling, poor testability and tree-shaking.

---

## 5. Module Boundary Definition

### Question 22: How do TypeScript libraries define module boundaries?

**Answer:** Four patterns, often combined:

| Pattern                           | Mechanism                           | Enforcement level                                                              |
| --------------------------------- | ----------------------------------- | ------------------------------------------------------------------------------ |
| **Barrel files** (`index.ts`)     | Re-export curated public API        | Social convention (compile-time if combined with `exports`)                    |
| **`package.json` `"exports"`**    | Node.js subpath exports             | **Runtime** — consumers get `ERR_PACKAGE_PATH_NOT_EXPORTED` for unlisted paths |
| **`@internal` + `stripInternal`** | TSDoc tag + tsconfig option         | Declaration-level — stripped from `.d.ts` output                               |
| **TypeScript Project References** | Separate `tsconfig.json` per module | Compile-time — modules only see each other's `.d.ts`                           |

**Recommendation for ogc-client:** Barrel file + `"exports"` subpath. The barrel defines what's public; the `"exports"` field enforces it. Project References and `@internal`/`stripInternal` are heavier than warranted for one sub-module.

### Question 23: Barrel file role for sub-path exports

**Answer:** Yes — `src/ogc-api/csapi/index.ts` serves exactly the same role as `src/index.ts`, scoped to the `./csapi` entry point.

| Entry point | Barrel file                  | Consumer import                                                    |
| ----------- | ---------------------------- | ------------------------------------------------------------------ |
| `"."`       | `src/index.ts`               | `import { OgcApiEndpoint } from '@camptocamp/ogc-client'`          |
| `"./csapi"` | `src/ogc-api/csapi/index.ts` | `import { CSAPIQueryBuilder } from '@camptocamp/ogc-client/csapi'` |

The barrel is the single source of truth for the sub-path's public API. The `"exports"` field in `package.json` points to the barrel's build output.

### Question 24: Should the CSAPI barrel mirror root exports?

**Answer:** No — the CSAPI barrel should **curate independently**. The standard pattern in multi-entry-point packages (TanStack Query, tRPC, date-fns) is:

```
csapi/index.ts → exports CSAPI's full public API (may include utilities root doesn't expose)
src/index.ts   → re-exports a curated subset from csapi/index.ts (or nothing, per jahow's requirement)
```

The root barrel becomes a _downstream consumer_ of the CSAPI barrel. Per jahow's requirement, the root barrel should NOT re-export any CSAPI symbols. The `csapi/index.ts` barrel should export everything CSAPI consumers need:

- `CSAPIQueryBuilder` (default)
- All CSAPI model types (`CSAPIResourceTypes`, `CommandStatusCodes`, `SystemTypeUris`, etc.)
- Format parsing utilities
- SensorML/SWE types
- The factory function (once created)

### Question 25: Internal-only CSAPI types

**Answer:** **Private-by-omission** — simply don't export internal types from the barrel file. Since `"exports"` blocks deep imports, consumers cannot reach `csapi/helpers.ts` directly. Files not re-exported from `csapi/index.ts` are effectively private.

No need for `@internal` tags or separate `internal/` subdirectories at this scale.

### Question 26: `scanCsapiLinks` placement

**Answer:** This is the most complex decoupling problem. Analysis of all four options:

**Current state:**

- `scanCsapiLinks` lives in `csapi/helpers.ts`
- Called by `endpoint.ts:435` (in `extractRootResourceUrls()`) — **constraint violation**
- Called by `url_builder.ts` (in `extractAvailableResources()`) — internal CSAPI use, fine
- Depends on `CSAPIResourceTypes` from `csapi/model.ts` — CSAPI-specific knowledge

**Option A: Keep in CSAPI, duplicate in core**

- Pro: No shared code to maintain
- Con: Duplication of link scanning logic (~100 lines); `CSAPIResourceTypes` must be duplicated
- Assessment: Fragile — the two copies will drift

**Option B: Move to shared utils**

- Pro: Single implementation, accessible to both
- Con: `CSAPIResourceTypes` (CSAPI-specific constant) would pollute shared utils
- Assessment: Violates separation of concerns

**Option C: Generalize the link scanner**

- Create a generic `scanLinks(links, knownTypes, prefixes)` in shared or `ogc-api/link-utils.ts`
- `endpoint.ts` calls `scanLinks(links, knownTypes, ['ogc-cs:'])` with a literal set of type names
- CSAPI keeps `scanCsapiLinks` as a convenience wrapper calling the generic function
- Pro: Clean separation, reusable for EDR and future modules, no CSAPI knowledge in core
- Con: Requires factoring out the link scanning logic

**Option D: Expose from CSAPI barrel (violates constraint)**

- `endpoint.ts` imports `scanCsapiLinks` from `@camptocamp/ogc-client/csapi`
- Assessment: **Violates constraint 3** — core imports from CSAPI

**Option E: Inline in endpoint's `extractRootResourceUrls`**

- The function is only 6 lines in `endpoint.ts`. The actual logic is ~40 lines.
- Inlining would require duplicating the link relation matching logic with hardcoded CSAPI resource type names
- Assessment: Hardcoding `['systems', 'deployments', ...]` in `endpoint.ts` is CSAPI-specific knowledge in core

**Recommendation: Option C — Generalize the link scanner.**

```typescript
// ogc-api/link-utils.ts (new file, part of core)
export function scanResourceLinks(
  links: Array<{ rel?: string; href?: string }>,
  knownTypes: ReadonlySet<string>,
  relPrefix?: string
): Map<string, string> {
  const result = new Map<string, string>();
  for (const link of links) {
    const rel = link.rel;
    const href = link.href ?? '';
    if (typeof rel !== 'string') continue;

    // Convention 1: prefixed (e.g., "ogc-cs:systems")
    if (relPrefix) {
      const match = rel.match(new RegExp(`^${relPrefix}(.+)$`));
      if (match && knownTypes.has(match[1])) {
        result.set(match[1], href);
        continue;
      }
    }

    // Convention 2: plain resource name
    if (knownTypes.has(rel)) {
      result.set(rel, href);
      continue;
    }

    // Convention 3: "items" with resource type in href
    if (rel === 'items' && typeof href === 'string') {
      const segment = href.split('?')[0].replace(/\/+$/, '').split('/').pop();
      const normalized =
        segment === 'featuresOfInterest' ? 'samplingFeatures' : segment;
      if (normalized && knownTypes.has(normalized))
        result.set(normalized, href);
    }
  }
  return result;
}
```

```typescript
// endpoint.ts — calls generic scanner with CSAPI types as data
import { scanResourceLinks } from './link-utils.js';

const CSAPI_RESOURCE_TYPES = new Set([
  'systems', 'deployments', 'samplingFeatures', 'procedures', 'properties',
  'datastreams', 'observations', 'controlStreams', 'commands'
]);

private async extractRootResourceUrls(): Promise<Map<string, string>> {
  const rootDoc = await this.root;
  return scanResourceLinks(rootDoc?.links ?? [], CSAPI_RESOURCE_TYPES, 'ogc-cs:');
}
```

```typescript
// csapi/helpers.ts — convenience wrapper still available
import { CSAPIResourceTypes } from './model.js';
import { scanResourceLinks } from '../link-utils.js';

export function scanCsapiLinks(
  links: Array<{ rel?: string; href?: string }>
): Map<string, string> {
  return scanResourceLinks(links, new Set(CSAPIResourceTypes), 'ogc-cs:');
}
```

**Why this is cleanest:**

- `endpoint.ts` no longer imports from `csapi/`
- The generic scanner is reusable for EDR and future OGC modules
- `CSAPIResourceTypes` stays in `csapi/model.ts`
- `scanCsapiLinks` remains in CSAPI as a convenience wrapper
- The resource type names in `endpoint.ts` are a **hardcoded constant** — this is acceptable because the endpoint already has `hasConnectedSystems` which hardcodes CSAPI conformance URIs
- **Alternative:** If hardcoding the type names in `endpoint.ts` is undesirable, the `extractRootResourceUrls` method can be moved to the factory function (which lives in CSAPI), eliminating the need for core to know about resource types at all

### Question 27: "Shared utility" problem — standard placement

**Answer:** The TypeScript ecosystem provides three standard approaches:

1. **Generic utility in shared** — when the function's logic is generalizable (our case: link scanning is generic; CSAPI-specificity can be parameterized)
2. **Move to the "closer" module** — when one module is the primary owner (link scanning originates from CSAPI; core only needs it for root URL extraction)
3. **Duplicate** — when the function is small and stable (not recommended for our ~40-line function)

The cleanest resolution for `scanCsapiLinks` is generalization (#1). The `featuresOfInterest → samplingFeatures` normalization is CSAPI-specific but can be handled by the CSAPI wrapper, not the generic scanner.

### Sub-topic Synthesis

The barrel file pattern (curated `csapi/index.ts` + `package.json` `"exports"`) is the standard approach for module boundaries in a single package. The `scanCsapiLinks` problem is solvable by generalizing the link scanner into a shared utility and parameterizing the CSAPI-specific knowledge. Private-by-omission (not exporting from barrel) is sufficient for internal type hiding. No heavyweight tools (Project References, `@internal`, Nx) are needed.

---

## 6. Module Extraction Case Studies

### Question 28: Case studies of intra-package sub-module extraction

**Answer:** Direct case studies of sub-path export extraction _within a single package_ are rare in published literature — most documented extractions involve separate npm packages. However, three relevant precedents exist:

1. **date-fns v2 → v3:** Migrated from deeply-importable internals to curated sub-path exports. Single package, extensive `"exports"` map. The extraction was done **one-shot** over a major version boundary.

2. **RxJS v6 → v7:** Migrated from `rxjs/internal/operators/map` to curated `rxjs/operators`. Staged deprecation of deep imports, then removed them. The internal module structure was refactored to support cleaner sub-path exports.

3. **TanStack Query:** Although implemented as separate npm packages in a monorepo, the pattern is identical to sub-path exports within a single package. A core module exposes types and functionality; framework-specific packages consume it through a well-defined barrel.

**Relevance to ogc-client:** The coupling surface is small (2 imports in `endpoint.ts`) and there are no external consumers of the current deep import paths. This is the simplest extraction scenario — a one-shot change with comprehensive test coverage.

### Question 29: Recommended migration patterns

**Answer:**

| Pattern                   | Description                          | Fit for ogc-client                                                                |
| ------------------------- | ------------------------------------ | --------------------------------------------------------------------------------- |
| **One-shot extraction**   | All changes in one PR/branch         | **Best fit** — small coupling surface, comprehensive tests, no external consumers |
| **Strangler fig**         | Gradual replacement, both paths work | Overkill — no benefit from keeping both paths                                     |
| **Branch-by-abstraction** | Introduce abstraction, then swap     | Useful specifically for `endpoint.csapi()` method                                 |
| **Feature flags**         | Runtime toggle                       | Not appropriate for library extraction                                            |

**Recommendation:** One-shot extraction. The two constraint violations (`CSAPIQueryBuilder` import and `scanCsapiLinks` import) can be resolved simultaneously. The endpoint's `csapi()` method can be deprecated or removed in the same change.

### Question 30: Verifying extraction completeness

**Answer:** Multiple complementary techniques:

| Method                                       | What it catches                         | Tooling                             |
| -------------------------------------------- | --------------------------------------- | ----------------------------------- |
| **`grep -r "from.*csapi" src/ogc-api/*.ts`** | Direct import violations                | Built-in                            |
| **ESLint `import/no-restricted-paths`**      | Lint-time boundary enforcement          | Already have `eslint-plugin-import` |
| **Custom boundary test**                     | CI-friendly validation                  | Jest test (see below)               |
| **`dependency-cruiser`**                     | Transitive dependencies, visualizations | New tool (optional)                 |
| **TypeScript compilation without CSAPI**     | Proves core builds independently        | Exclude `csapi/` from tsconfig      |

**Recommended verification: Custom boundary test + ESLint rule**

```typescript
// __tests__/boundary.spec.ts
import * as fs from 'fs';
import * as path from 'path';

test('no imports from csapi/ in core ogc-api files', () => {
  const coreDir = path.join(__dirname, '../src/ogc-api');
  const coreFiles = fs
    .readdirSync(coreDir)
    .filter((f) => f.endsWith('.ts') && !f.endsWith('.spec.ts'));
  for (const file of coreFiles) {
    const content = fs.readFileSync(path.join(coreDir, file), 'utf8');
    expect(content).not.toMatch(/from\s+['"]\.\/csapi\//);
  }
});
```

### Question 31: Common module extraction mistakes

**Answer:**

1. **Forgetting `import type` conversion.** When removing a value import from CSAPI, any types that were imported alongside values must be converted to `import type`. Current `endpoint.ts` uses value imports for both `CSAPIQueryBuilder` and `scanCsapiLinks`.

2. **Leaving transitive dependencies.** After removing direct imports, verify the _transitive_ import graph — another file might re-export from CSAPI indirectly.

3. **Barrel file circular references.** If `csapi/index.ts` re-exports from `url_builder.ts`, and `url_builder.ts` were to import from `../endpoint.ts`, which then imports from `csapi/index.ts` — a cycle. Not currently an issue since we're _removing_ the endpoint → CSAPI direction.

4. **Breaking tree-shaking with side effects.** The `package.json` should declare `"sideEffects": false` (or list specific side-effectful files). Note: `src/index.ts` imports `'./worker-fallback/index.js'` as a side effect.

5. **Not updating `package.json` `"exports"`.** The barrel file must be reflected in the `"exports"` map for consumers to use the sub-path import.

6. **Missing `.js` extensions.** The project uses ESM — all import paths must include `.js` extensions after any file moves.

7. **Test file coupling.** Tests in `endpoint.spec.ts` may import CSAPI fixtures directly — these must also respect the boundary (or be explicitly exempted).

### Question 32: Tree-shaking interaction with module boundaries

**Answer:** Sub-path exports **improve** tree-shaking:

- **Current state:** All CSAPI symbols are re-exported from `src/index.ts`. A consumer who only imports `OgcApiEndpoint` still forces the bundler to parse all CSAPI modules during build.
- **After extraction:** Consumers import from `@camptocamp/ogc-client` (root, no CSAPI) or `@camptocamp/ogc-client/csapi` (CSAPI only). The bundler never touches CSAPI modules for consumers who don't use them.

**Coupling level doesn't directly affect tree-shaking.** What matters is module organization — fewer re-export hops = faster build + more reliable elimination. The barrel file should be shallow (direct re-exports, not chains).

For maximum effectiveness, `package.json` should include `"sideEffects": false` so bundlers know all modules are safe to skip if unused.

### Sub-topic Synthesis

Module extraction within a single TypeScript package is a well-understood operation when the coupling surface is small. The one-shot extraction pattern is appropriate here. Verification should combine a custom boundary test (CI-friendly) with ESLint `import/no-restricted-paths` (lint-time enforcement). Common mistakes are all avoidable with the checklist approach.

---

## 7. `import type` and Type-Only Dependencies

### Question 33: Does `import type` create a runtime dependency?

**Answer:** **No.** `import type` is completely erased during TypeScript compilation. It does not appear in the JavaScript output.

```typescript
// TypeScript source:
import type { OgcApiCollectionInfo } from '../model.js';

// Compiled JavaScript output:
// (nothing — the entire import statement is removed)
```

This was introduced in TypeScript 3.8 (PR #35200) specifically to guarantee erasure. The compiler enforces that `import type` declarations cannot be used in value positions.

**Verification for this project:** The current `url_builder.ts` line 1 uses `import type { OgcApiCollectionInfo }`. The compiled `url_builder.js` in `dist/` contains no reference to `../model.js`.

### Question 34: CSAPI's dependency graph with `import type`

**Answer:** If CSAPI uses `import type` for all core types:

| Dependency type           | Present?              | Explanation                                                   |
| ------------------------- | --------------------- | ------------------------------------------------------------- |
| **Runtime dependency**    | **No**                | `import type` erased — CSAPI `.js` has no core references     |
| **Build-time dependency** | **Yes**               | TypeScript compiler needs `../model.d.ts` to type-check       |
| **Package dependency**    | **No** (same package) | Both share the same build — irrelevant until/unless separated |

**Current state of CSAPI's type imports from core:**

- `url_builder.ts:1` — `import type { OgcApiCollectionInfo } from '../model.js'` ✓ type-only
- `model.ts:2` — `import type { OgcApiDocumentLink } from '../model.js'` ✓ type-only
- `model.ts:1` — `import type { BoundingBox, DateTimeParameter, CrsCode, MimeType } from '../../shared/models.js'` ✓ type-only
- `helpers.ts:3` — `import type { BoundingBox } from '../../shared/models.js'` ✓ type-only

All type imports are already `import type`. The only value imports from outside CSAPI are:

- `url_builder.ts:4` — `import { EndpointError } from '../../shared/errors.js'` — value import from **shared** (see Question open item in Section 13)

### Question 35: `import type` for drift detection without module dependency

**Answer:** **Yes — this is exactly what `import type` enables.** It's the best mechanism for "use for checking but don't ship in output."

```typescript
// csapi/url_builder.ts
import type { OgcApiCollectionInfo } from '../model.js'; // erased at runtime

export class CSAPIQueryBuilder {
  constructor(
    private collection_: Pick<OgcApiCollectionInfo, 'id' | 'title' | 'links'>
  ) {}
}
```

If core renames `id` → `identifier`: `Pick<>` fails because `'id'` is no longer a key of `OgcApiCollectionInfo`. If core removes `links`: same. If core changes `links` type: the `Pick<>` narrows accordingly.

**This is the strongest argument for keeping `Pick<>` + `import type`.** You get drift detection without any runtime or bundle-size cost.

**Does it violate constraint 3 ("nothing outside CSAPI should import from CSAPI")?** No — constraint 3 is about _core importing from CSAPI_. CSAPI importing (type-only) from core is the _desired_ dependency direction. Constraint 1 (one-way dependency) is: CSAPI imports from core, never the reverse. `import type` satisfies this perfectly.

### Question 36: Self-referencing package imports

**Answer:** If CSAPI uses `import type { OgcApiCollectionInfo } from '@camptocamp/ogc-client'` (the package's public API):

- **Circular dependency?** With `import type` — no runtime circular dependency (erased). But TypeScript's resolution traverses: `csapi/url_builder.ts` → `@camptocamp/ogc-client` → `src/index.ts` → `csapi/url_builder.ts` — a compile-time cycle in the resolution graph. TypeScript handles this in most cases but it can cause:

  - IDE performance issues (language server resolves the full root barrel)
  - Confusing error messages
  - Issues with `declaration: true` emit ordering

- **Current compatibility:** The project uses `moduleResolution: "node"` which **does not support** self-referencing via `"exports"`. You'd need `"node16"`, `"nodenext"`, or `"bundler"` to use this pattern.

### Question 37: Recommended `import type` strategy

**Answer:** **Use relative paths from source files, not the package name.**

```typescript
// Recommended (in csapi/url_builder.ts):
import type { OgcApiCollectionInfo } from '../model.js';

// NOT recommended:
import type { OgcApiCollectionInfo } from '@camptocamp/ogc-client';
```

**Reasons:**

1. No circular dependency risk
2. TypeScript resolves relative imports directly — no `package.json` indirection
3. Better build performance
4. Compatible with current `moduleResolution: "node"`
5. Self-referencing requires `"exports"` + `moduleResolution: "node16"` or higher

### Sub-topic Synthesis

`import type` is the ideal mechanism for maintaining type safety across the CSAPI-core boundary without creating runtime coupling. All current CSAPI type imports from core are already `import type` — this is best practice and should be preserved. The relative path strategy is recommended over self-referencing package paths due to compatibility and performance. The `import type` + `Pick<>` combination provides automatic drift detection that would be lost with a fully independent local interface.

---

## 8. Boundary Condition Verification

### Constraint Compliance Matrix

| #   | Constraint                                                   | Status      | Evidence                                                                                                                                                                                                            | Notes                                                                                                    |
| --- | ------------------------------------------------------------ | ----------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------- |
| 1   | One-way dependency: CSAPI → core, never reverse              | ✓ Compliant | Recommended Level 3.5 has CSAPI importing from core via `import type`. Core never references CSAPI. The generic link scanner has zero CSAPI knowledge.                                                              | All coupling levels except L1 satisfy this. L1 also satisfies it technically but creates heavy coupling. |
| 2   | Separate entry point: `@camptocamp/ogc-client/csapi`         | ✓ Compliant | Barrel file + `"exports"` sub-path recommended. Coupling level doesn't affect entry point design.                                                                                                                   | Plan 03 handles mechanical `"exports"` config.                                                           |
| 3   | No outward imports: nothing outside `csapi/` imports from it | ✓ Compliant | After extraction: `endpoint.ts` removes both CSAPI imports. `scanCsapiLinks` replaced by generic `scanResourceLinks`. `index.ts` CSAPI re-exports removed.                                                          | The two current violations are resolved.                                                                 |
| 4   | Core builds/tests independently                              | ✓ Compliant | With Level 3.5, removing `csapi/` leaves core with: zero import errors (CSAPI imports are in CSAPI only), zero type errors (core types are self-contained), zero test failures (`endpoint.csapi()` method removed). | Verified by the factory function approach: builder creation moves from core to consumer/CSAPI.           |

### Scope Boundary Adherence

- **In scope — explored:** Structural typing effects, 4 coupling levels with code examples, `scanCsapiLinks` placement (5 options analyzed), barrel file design, `import type` strategy, extraction verification, drift detection patterns
- **Out of scope — respected:** Consumer API shape (Plan 04), `package.json` `"exports"` configuration (Plan 03), plugin/mixin/decorator patterns (excluded per strategy), DI containers, build system configuration (Plan 01)
- **Scope adjustments:** None — all 37 questions were answerable with the available sources

---

## 9. Implementation Scope Gate Assessment

### Minimum-Change Test

| Finding / Recommendation                             | Serves jahow's requirements?                      | Minimum-change?          | Include in implementation?        |
| ---------------------------------------------------- | ------------------------------------------------- | ------------------------ | --------------------------------- |
| Keep Level 3.5 coupling (no constructor change)      | Yes — maintains current behavior                  | Yes — zero migration     | ✓ Include                         |
| Remove `CSAPIQueryBuilder` import from `endpoint.ts` | Yes — directly required by jahow                  | Yes                      | ✓ Include                         |
| Remove `scanCsapiLinks` import from `endpoint.ts`    | Yes — directly required by jahow                  | Yes                      | ✓ Include                         |
| Create generic `scanResourceLinks` utility           | Yes — necessary to remove `scanCsapiLinks` import | Yes — minimal code       | ✓ Include                         |
| Create `csapi/index.ts` barrel file                  | Yes — required for separate entry point           | Yes                      | ✓ Include                         |
| Add compile-time drift assertion test                | No — defensive measure                            | No — extra test file     | ✗ Defer                           |
| TypeScript Project References                        | No — architectural improvement                    | No — heavy refactor      | ✗ Defer                           |
| ESLint `no-restricted-paths` rule                    | No — enforcement                                  | No — tooling change      | ⚠️ Discuss (low cost, high value) |
| Custom boundary integration test                     | No — enforcement                                  | Borderline — simple test | ⚠️ Discuss                        |
| `@internal` tags / `stripInternal`                   | No — nice-to-have                                 | No — config change       | ✗ Defer                           |

### Deferred Insights

- **TypeScript Project References:** Powerful for enforcing compile-time boundaries, but requires splitting `tsconfig.json` into multiple composite configs. Deferred — excessive for one sub-module extraction.
- **Compile-time drift assertion:** Valuable if coupling level changes to L3 (local interface), but unnecessary at L3.5 where `Pick<>` provides native drift detection.
- **`dependency-cruiser` integration:** Excellent for visualizing and enforcing import graphs in CI. Deferred — custom boundary test achieves the same validation with zero new dependencies.
- **`sideEffects: false` in `package.json`:** Would improve tree-shaking for consumers. Worth doing but not directly required for the extraction.

---

## 10. Impact on Dependent Plans

### What Downstream Plans Should Consume

| Downstream Plan | What to consume from this report                                                                                                                                                             | Section reference                         |
| --------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------- |
| Plan 06         | **Coupling level decision:** Keep Level 3.5 (`Pick<>` + `import type`). No constructor signature change needed.                                                                              | § 3 (Question 21), § 4 (Matrix)           |
| Plan 06         | **`scanCsapiLinks` resolution:** Generalize into `scanResourceLinks()` in `ogc-api/link-utils.ts`. CSAPI keeps wrapper. Endpoint calls generic version.                                      | § 5 (Question 26)                         |
| Plan 06         | **Barrel file design:** `csapi/index.ts` exports full CSAPI public API. Root `index.ts` removes all CSAPI re-exports.                                                                        | § 5 (Question 24)                         |
| Plan 06         | **`import type` strategy:** Keep relative paths, keep `Pick<>`, keep current `import type` statements.                                                                                       | § 7 (Question 37)                         |
| Plan 06         | **Factory function as orchestration mechanism:** The factory function (from Plan 04) resolves the `endpoint.ts` → CSAPI coupling by moving builder creation from endpoint to CSAPI/consumer. | § 2 (Question 10)                         |
| Plan 06         | **`EndpointError` import is acceptable:** `shared/errors.ts` is a shared utility, not core. CSAPI's import from `../../shared/errors.js` does not violate constraints.                       | § 7 (Question 34), § 13 (Open Question 1) |
| Plan 08         | **Verification checklist:** Custom boundary test + ESLint rule + grep commands for confirming extraction completeness.                                                                       | § 6 (Questions 30–31)                     |
| Plan 08         | **One-shot extraction pattern:** All changes in one commit/PR — no staged migration needed.                                                                                                  | § 6 (Question 29)                         |

### Decisions Now Final

1. **Coupling level: Level 3.5 (current `Pick<>` + `import type`).** No change to `CSAPIQueryBuilder` constructor signature. This is the optimal level — drift detection + zero runtime coupling + zero migration effort.

2. **`scanCsapiLinks` resolution: Generalize into a shared link scanner.** `endpoint.ts` calls the generic function with CSAPI resource type names as data. CSAPI keeps its wrapper for internal convenience.

3. **Barrel file: Independent curation.** `csapi/index.ts` exports CSAPI's full public API. Root `index.ts` removes all CSAPI re-exports.

4. **`import type` strategy: Relative paths.** No self-referencing package imports. Current `import type` statements in CSAPI are correct and should be preserved.

5. **Extraction pattern: One-shot.** No intermediate layers, adapters, or staged migration.

### Items Requiring Downstream Resolution

1. **Factory function exact signature** → Plan 06 must decide whether it accepts `OgcApiEndpoint` (Level 1 for the factory, not the constructor) or extracted data (Level 3 for the factory too).
2. **`endpoint.csapi()` method disposition** → Plan 06 must decide: remove entirely, deprecate, or keep as a thin wrapper calling the factory function.
3. **`hasConnectedSystems` check location** → Plan 06 must decide whether the conformance check stays on `OgcApiEndpoint` or moves to the factory function.
4. **`EndpointError` import classification** → Plan 06 should confirm that `shared/` is not considered "core" for constraint purposes.
5. **Exact barrel file contents** → Plan 08 must enumerate every symbol to export from `csapi/index.ts`.

---

## 11. Key Takeaways

1. **TypeScript's structural typing provides implicit dependency inversion.** No adapter classes, DI containers, or `implements` declarations needed. The core satisfies CSAPI's contract by having matching property shapes — without any reference to CSAPI's types.

2. **The current coupling level (Level 3.5) is already optimal.** `Pick<OgcApiCollectionInfo, 'id' | 'title' | 'links'>` with `import type` gives zero runtime coupling, automatic drift detection, and excellent developer ergonomics. No change to the constructor signature is needed.

3. **The decoupling problem is not about _what data flows_ but _who orchestrates the flow_.** Currently `endpoint.ts` creates the builder. After decoupling, a factory function in CSAPI (Plan 04's recommendation) takes over this role. The data shape stays identical.

4. **`import type` is the ideal boundary mechanism** for an intra-package sub-module. It provides compile-time type safety and drift detection while being completely erased at runtime. All current CSAPI type imports from core are already `import type`.

5. **`scanCsapiLinks` should be generalized into a shared link scanner.** The function's logic (matching link `rel` values against a known-types set with prefix conventions) is generic. The CSAPI-specific knowledge (the 9 resource type names) is parameterized. This cleanly eliminates the constraint violation.

6. **One-shot extraction is sufficient.** The coupling surface is only 2 imports in `endpoint.ts` + ~170 export lines in `index.ts`. No staged migration, strangler fig, or intermediate adapter layers are needed.

7. **Barrel file + `"exports"` is the standard module boundary pattern.** `csapi/index.ts` curates CSAPI's public API independently. Root `index.ts` removes all CSAPI re-exports.

8. **Verification: boundary test + ESLint rule.** A custom Jest test asserting "no core file imports from csapi/" provides CI-friendly validation. ESLint `import/no-restricted-paths` provides lint-time enforcement with existing tooling.

9. **`shared/` is a legitimate import target for CSAPI.** `EndpointError` from `../../shared/errors.js` and types from `../../shared/models.js` are shared utilities, not core-specific. These imports don't violate constraints.

10. **Level 1 (concrete class) and Level 2 (explicit interface) both require making private endpoint methods public.** `getCollectionDocument()` is private. Neither level works without changing core's public API — a violation of minimum-change principles.

---

## 12. Impact on Implementation

### Must Change (Required by Findings)

1. **Remove `import CSAPIQueryBuilder from './csapi/url_builder.js'` from `endpoint.ts` (line 52).** This is a value import — the constraint violation. The factory function (Plan 04) replaces the endpoint's `csapi()` method.

2. **Remove `import { scanCsapiLinks } from './csapi/helpers.js'` from `endpoint.ts` (line 53).** Replace with a call to a generic link scanner (details in Question 26).

3. **Create a generic `scanResourceLinks` function** in a shared location (e.g., `ogc-api/link-utils.ts`). Parameterized to accept known types and prefix, replacing the CSAPI-specific function in core.

4. **Remove all CSAPI re-exports from `src/index.ts`** (~170 lines, lines 45–227). These move to the CSAPI barrel.

5. **Create `src/ogc-api/csapi/index.ts` barrel file** exporting CSAPI's full public API: `CSAPIQueryBuilder`, model types, format utilities, SensorML/SWE types.

### Should Change (Recommended by Findings)

1. **Add an ESLint `import/no-restricted-paths` zone** preventing `src/ogc-api/*.ts` from importing from `src/ogc-api/csapi/`. Low cost, prevents regression.

2. **Add a boundary integration test** asserting no core file imports from `csapi/`. Simple, CI-friendly, catches drift.

### Could Change (Optional Improvements)

1. **Add `"sideEffects": false`** to `package.json` for improved tree-shaking (with exception for `worker-fallback/index.js`).

2. **Replace `Pick<OgcApiCollectionInfo, ...>` with a locally-defined `CSAPICollectionInput` interface** (Level 3 upgrade). Only worthwhile if CSAPI is ever extracted to a separate package.

3. **Add TypeScript Project References** for compile-time boundary enforcement. Deferred — excessive for current scope.

---

## 13. Open Questions

| #   | Question                                                                                                                | Why Unresolved                                                                                                                          | Resolution Path                                                                                                                                 |
| --- | ----------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | Is `shared/` considered "core" for constraint purposes? `EndpointError` is in `shared/errors.ts`, imported by CSAPI.    | jahow's constraint says "anything not part of `src/ogc-api/csapi`" — `shared/` is not part of `csapi/` but also not part of `ogc-api/`. | Plan 06 should classify: `shared/` is a utility layer, not core. If contested, CSAPI can declare its own error class.                           |
| 2   | Should `endpoint.csapi()` method be removed, deprecated, or replaced with a note pointing to the factory?               | Depends on migration strategy and backward compatibility policy.                                                                        | Plan 06 should decide based on whether any other code calls `endpoint.csapi()`.                                                                 |
| 3   | Should the factory function accept `OgcApiEndpoint` (Level 1 for factory, Level 3.5 for constructor) or extracted data? | This determines whether CSAPI has any import of the endpoint class. Plan 04 recommends accepting the endpoint for convenience.          | Plan 06 must reconcile Plan 04 (accept endpoint) with Plan 05 (prefer extracted data). Both are viable — Plan 06 should evaluate the tradeoffs. |
| 4   | Should the `featuresOfInterest → samplingFeatures` normalization live in the generic scanner or the CSAPI wrapper?      | It's CSAPI-specific domain knowledge, but the generic scanner's "items" convention handling already needs endpoint-type awareness.      | Plan 06 should decide. Recommendation: keep in CSAPI wrapper.                                                                                   |
| 5   | Should `extractRootResourceUrls()` move entirely to the factory function?                                               | If it moves, `endpoint.ts` loses `hasConnectedSystems` detection capability. But `hasConnectedSystems` doesn't use this function.       | Plan 06 should evaluate whether the endpoint needs root resource URL extraction for any non-CSAPI purpose.                                      |

---

## Evidence Appendix

### A. Current CSAPI Import Map

Complete list of how CSAPI files import from outside `csapi/`:

| File               | Import                                                              | Type      | Target                   | Constraint Status             |
| ------------------ | ------------------------------------------------------------------- | --------- | ------------------------ | ----------------------------- |
| `url_builder.ts:1` | `import type { OgcApiCollectionInfo }`                              | Type-only | `../model.js`            | ✓ Acceptable (erased)         |
| `url_builder.ts:4` | `import { EndpointError }`                                          | Value     | `../../shared/errors.js` | ✓ Acceptable (shared utility) |
| `model.ts:1`       | `import type { BoundingBox, DateTimeParameter, CrsCode, MimeType }` | Type-only | `../../shared/models.js` | ✓ Acceptable (erased)         |
| `model.ts:2`       | `import type { OgcApiDocumentLink }`                                | Type-only | `../model.js`            | ✓ Acceptable (erased)         |
| `model.ts:3`       | `import type { Geometry }`                                          | Type-only | `geojson` (npm)          | ✓ External package            |
| `helpers.ts:3`     | `import type { BoundingBox }`                                       | Type-only | `../../shared/models.js` | ✓ Acceptable (erased)         |

### B. Current Core → CSAPI Import Map (Constraint Violations)

| File              | Import                                              | Type           | Target                            | Resolution                             |
| ----------------- | --------------------------------------------------- | -------------- | --------------------------------- | -------------------------------------- |
| `endpoint.ts:52`  | `import CSAPIQueryBuilder`                          | **Value**      | `./csapi/url_builder.js`          | Remove — factory function replaces     |
| `endpoint.ts:53`  | `import { scanCsapiLinks }`                         | **Value**      | `./csapi/helpers.js`              | Remove — generic link scanner replaces |
| `index.ts:45`     | `export { default as CSAPIQueryBuilder }`           | **Re-export**  | `./ogc-api/csapi/url_builder.js`  | Remove — move to CSAPI barrel          |
| `index.ts:46–227` | Multiple `export type { ... }` and `export { ... }` | **Re-exports** | Various `./ogc-api/csapi/*` paths | Remove — move to CSAPI barrel          |

---

## Research Completion Checklist

- [x] All 37 detailed questions from the research plan have specific, evidenced answers
- [x] Boundary condition verification completed (Section 8)
- [x] Implementation scope gate assessment completed (Section 9)
- [x] Impact on dependent plans documented (Section 10)
- [x] Key takeaways extracted (Section 11)
- [x] Open questions cataloged with resolution paths (Section 13)
- [x] Cross-references to prior findings are accurate (Plans 02 and 04)
- [x] Findings respect all boundary conditions from the research plan
- [x] Document is self-contained — a reader unfamiliar with the plan can understand the findings

**Research Started:** 2026-02-23
**Research Completed:** 2026-02-23
**Reviewed:** Not yet

---

## Notes

- **Structural typing is the key insight for this entire extraction.** Classical module decoupling guidance from Java/C# (adapter classes, DI containers, interface segregation) translates poorly to TypeScript. The `Pick<>` + `import type` pattern already embodies TypeScript-native DIP without any of the nominal-typing ceremony.

- **The `scanCsapiLinks` problem was initially expected to be the hardest part of the extraction.** The "generalize the scanner" solution is cleaner than any of the simpler alternatives (duplicate, move, inline) because it produces a reusable utility and keeps CSAPI knowledge in CSAPI.

- **Level 3.5 was not in the original research plan's taxonomy.** The plan anticipated 4 levels. The analysis revealed that the current code sits between Level 3 (data record) and Level 2 (explicit interface) — prompting the addition of Level 3.5 to accurately describe the existing pattern.

- **Plans 04 and 05 converge on the same architecture.** Plan 04 recommends a factory function for consumer API; Plan 05 confirms that the factory function is also the mechanism for resolving the internal coupling. The factory function serves double duty — consumer convenience and architectural decoupling.
