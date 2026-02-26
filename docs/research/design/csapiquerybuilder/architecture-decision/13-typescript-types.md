# 13: TypeScript Type System Organization

**Research Question:** How does class structure affect TypeScript type organization and type safety?

**Source Document:** [docs/research/upstream/typescript-types-analysis.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/upstream/typescript-types-analysis.md)

**Decision Relevance:** MEDIUM - Type organization impacts developer experience and maintainability.

---

## Research Objectives

1. **Type Organization Patterns:**

   - How are types organized in single-class implementations?
   - How would types be organized for multi-class?
   - Shared vs specific type definitions

2. **Type Safety Analysis:**

   - Does single class affect method type safety?
   - Can multi-class provide better type specificity?
   - Generic type patterns

3. **Developer Experience:**
   - Autocomplete and IntelliSense implications
   - Type inference quality
   - Error messaging clarity

---

## Key Questions to Answer

- [x] How are query parameter types organized in EDR?
- [x] Are types resource-specific or shared?
- [x] Would separate classes improve type safety?
- [x] How are return types handled?
- [x] What is the type import/export strategy?
- [x] Do types drive class organization or vice versa?

---

## Synthesis Notes

**Research Status:** ✅ COMPLETE

**Key Findings:**

1. **Query Parameter Types:** EDR uses 7 optional parameter interfaces (one per query type), all in model.ts (126 lines). CSAPI should use shared QueryOptions interface + 2-3 extended versions (40 lines total).

2. **Type Organization:** Three-tier hierarchy (shared → ogc-api → csapi). All API-specific types in single model.ts file. EDR: 126 lines. CSAPI: 350-400 lines (9 resources × 39-44 lines avg).

3. **Shared vs Resource-Specific:** Types are shared across classes. Single model.ts imports: 1 statement. Multi-class imports: 9 statements (one per builder). Type definitions IDENTICAL regardless of class count.

4. **Type Safety:** IDENTICAL between single-class and multi-class. Both have fully typed method signatures with same QueryOptions, System, Deployment, etc. types. NO type safety advantage for multi-class.

5. **Return Types:** Resource interfaces (System, Deployment, etc.) used as return types. Collections use generic Collection<T> with type aliases (SystemCollection = Collection<System>).

6. **Import/Export Strategy:** Export resource types and query options from src/index.ts for user annotations. DON'T export QueryBuilder (factory method access). Reuse shared types (BoundingBox, DateTimeParameter) - don't redefine.

7. **Types Don't Drive Class Organization:** Type organization is COMPLETELY INDEPENDENT of class count. All types live in one model.ts file for both single-class and multi-class approaches.

**Developer Experience:**

- Single-class: IntelliSense shows all 70-80 methods immediately
- Multi-class: IntelliSense shows only 8-12 methods per builder (must know which builder to use first)
- **Winner:** Single-class (better method discovery)

**Type System Verdict:**

- ✅ Type organization: IDENTICAL (TIE)
- ✅ Type safety: IDENTICAL (TIE)
- ✅ Import complexity: Single-class better (1 vs 9 imports)
- ✅ IntelliSense: Single-class better (all methods visible)
- ❌ Multi-class advantages: ZERO

**Recommendation:** Type system is **NEUTRAL to SLIGHT FAVOR for single-class**. Types DO NOT favor multi-class. Single-class has simpler imports and better autocomplete/IntelliSense.

**Impact on Part 1 Decision:** Reinforces single-class choice - type organization is identical, but single-class has better developer experience.

**Detailed Analysis:** See [findings/13-typescript-types-findings.md](findings/13-typescript-types-findings.md)

---
