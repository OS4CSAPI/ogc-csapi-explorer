# 04: General Architecture Patterns in ogc-client

**Research Question:** What are the established architectural patterns in ogc-client, and do they favor single-class or multi-class designs?

**Source Document:** [docs/research/upstream/architecture-patterns-analysis.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/upstream/architecture-patterns-analysis.md)

**Decision Relevance:** MEDIUM - Understanding general patterns helps identify what's conventional vs innovative.

---

## Research Objectives

1. **Pattern Survey:**

   - What architectural patterns are consistently used?
   - How do WFS, WMS, WMTS, EDR organize code?
   - Are there both single-class and multi-class examples?

2. **Endpoint Extension Patterns:**

   - How are new APIs added to `OgcApiEndpoint`?
   - Factory method patterns across implementations
   - Conformance checking approaches

3. **Code Organization:**

   - File structure patterns
   - Type organization
   - Shared utilities usage

4. **Consistency Requirements:**
   - What patterns must be followed for acceptance?
   - Where is flexibility allowed?
   - What breaks convention?

---

## Key Questions to Answer

- [x] **Do all OGC API implementations use single QueryBuilder classes?**

  - **YES.** 100% of implementations (EDR, Features, Tiles, Styles) use single QueryBuilder class OR single set of endpoint methods. Zero multi-class examples.

- [x] **Are there any multi-class implementations?**

  - **NO.** Zero multi-class implementations exist. Pattern is universal: one main class (or set of methods) per API family.

- [x] **What is the factory method pattern (consistent signature)?**

  - **Signature:** `public async {apiName}(collection_id: string): Promise<{API}QueryBuilder>`
  - **Structure:** 1) Conformance guard, 2) Check cache (Map by collection_id), 3) Fetch collection metadata, 4) Instantiate QueryBuilder, 5) Cache and return
  - **Example:** `public async edr(collection_id: string): Promise<EDRQueryBuilder>`

- [x] **How are types organized across implementations?**

  - **Three-level hierarchy:** 1) Shared (`src/shared/models.ts`): Cross-API primitives (BoundingBox, DateTimeParameter), 2) OGC API Common (`src/ogc-api/model.ts`): OGC API family types, 3) Implementation-Specific (`src/ogc-api/{api}/model.ts`): API-specific types
  - **Flow:** General → Specific (never reverse)

- [x] **What file structure is standard?**

  - **For complex APIs:** `src/ogc-api/{api}/` with `url_builder.ts` (QueryBuilder), `model.ts` (types), `helpers.ts` (optional utilities), and tests
  - **Core integration:** Changes to info.ts (~10 lines), endpoint.ts (~55 lines), model.ts (~50 lines) = ~115 lines total

- [x] **Are there helper classes alongside QueryBuilders?**

  - **NO.** Helper **functions** are used (in helpers.ts), but NO helper **classes** for delegation. All query logic stays in single QueryBuilder class.

- [x] **How consistent are naming conventions?**
  - **Very consistent:** Files: `url_builder.ts`, Classes: `{API}QueryBuilder`, Methods: `build{Type}Url()`, Factory: `async {api}(collection_id)`, Cache: `private collection_id_to_{api}_builder_: Map<>`

---

## Expected Findings

**If all use single class:**

- Strong pattern consistency
- Expectation for CSAPI to follow
- Little precedent for deviation

**If some use multiple classes:**

- Precedent for alternative approaches
- Flexibility in pattern interpretation
- May justify separate clients

---

## Architecture Decision Impact

**MEDIUM IMPACT** - Informs whether we're following convention or breaking new ground.

---

## Synthesis Notes

### Pattern Consistency

**UNIVERSAL** - 100% consistency across all OGC API implementations. The pattern is:

1. Single QueryBuilder class (or endpoint methods for simple APIs)
2. Factory method: `async {api}(collection_id): Promise<{API}QueryBuilder>`
3. Map-based caching by collection_id
4. Composition over inheritance (no endpoint subclassing)
5. Link-driven navigation (never construct URLs)
6. Conformance-based capability detection
7. Minimal core impact (~115 lines to integrate)

### Single vs Multi-Class Prevalence

**Single class: 100% (4/4 implementations)**

- EDR: Single EDRQueryBuilder (561 lines, 7 query types)
- Features: Single set of endpoint methods
- Tiles: Single set of endpoint methods
- Styles: Single set of endpoint methods

**Multi-class: 0% (0/4 implementations)**

- Zero examples of multiple resource clients
- Zero examples of facade + delegation
- Zero examples of sub-resource classes
- Zero examples of helper classes for operation splitting

### Flexibility in Patterns

**Mandatory (no flexibility):**

- Single main class pattern
- Factory method signature and structure
- Map-based caching
- Composition over inheritance
- Link-driven navigation
- Conformance checking
- Type organization hierarchy
- Async everywhere

**Flexible (allowed variation):**

- File organization within subfolder
- Helper function organization
- Method naming (`build{Type}Url` vs `get{Type}Url`)
- Type organization (single vs multiple model files)
- Test structure

**Helper functions: YES, Helper classes: NO**

### Implications for CSAPI

**RECOMMENDATION: Single CSAPIQueryBuilder class**

**Structure:**

```typescript
export default class CSAPIQueryBuilder {
  constructor(private collection: OgcApiCollectionInfo) { ... }

  // 9 resources × 2 methods each (~50 lines per method)
  buildSystemsUrl(options?: QueryOptions): string { ... }
  buildSystemUrl(systemId: string): string { ... }
  buildDeploymentsUrl(options?: QueryOptions): string { ... }
  buildDeploymentUrl(deploymentId: string): string { ... }
  // ... 7 more resource pairs
}
```

**Estimated Size:**

- Core integration: ~115 lines (info.ts, endpoint.ts, model.ts)
- CSAPIQueryBuilder: ~850-950 lines (9 resources × ~95-105 lines)
- Types: ~200-300 lines
- Helpers: ~50-100 lines (optional)
- Tests: ~2,350 lines
- **Total: ~3,565-3,865 lines**

**Risk Assessment:**

- Single class: 🟢 LOW risk (100% pattern match, proven scalable)
- Multi-class: 🔴 HIGH risk (zero precedent, likely rejection)

**Key Architectural Patterns to Follow:**

1. ✅ Composition over inheritance (standalone QueryBuilder)
2. ✅ Factory method with Map-based caching
3. ✅ Link-driven navigation (use getLinkUrl(), never construct)
4. ✅ Conformance-based capability detection
5. ✅ Minimal core impact (~115 lines)
6. ✅ Type hierarchy: Shared → OGC API → Implementation
7. ✅ Standard parameter encoding (limit, offset, bbox, datetime)
8. ✅ Helper functions OK, helper classes NO
9. ✅ Async everywhere
10. ✅ TypeScript type safety

**Conclusion:** Pattern is universal, proven, and non-negotiable. Must follow single-class pattern for CSAPI.
