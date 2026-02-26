# 02: QueryBuilder Pattern Core Concepts

**Research Question:** What are the essential characteristics of the QueryBuilder pattern in ogc-client, and does it inherently require a single class?

**Source Document:** [docs/research/upstream/querybuilder-pattern-analysis.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/upstream/querybuilder-pattern-analysis.md)

**Decision Relevance:** CRITICAL - Understanding the pattern fundamentals informs whether we must use single class or if multiple classes are pattern-compatible.

---

## Research Objectives

1. **Pattern Definition:**

   - What is a "QueryBuilder" in ogc-client terminology?
   - What responsibilities does a QueryBuilder have?
   - What distinguishes QueryBuilder from other patterns (navigator, client, handler)?

2. **Lifecycle Analysis:**

   - How is a QueryBuilder instantiated? (factory method)
   - What state does it maintain?
   - How is caching implemented?
   - When is a QueryBuilder instance destroyed?

3. **State Management:**

   - What metadata does QueryBuilder encapsulate from collection info?
   - Is state immutable or mutable?
   - How does it validate capabilities?

4. **Method Organization:**
   - Are there organizational requirements for methods?
   - Can methods be split across multiple classes?
   - How are related operations grouped?

---

## Key Questions to Answer

- [x] What is the canonical definition of QueryBuilder pattern?
  - **Answer:** Standalone class that encapsulates collection metadata, validates capabilities, builds URLs from links, and optionally executes queries. NOT an endpoint subclass.
- [x] Must a QueryBuilder be a single class or can it be multiple classes?
  - **Answer:** Pattern does NOT formally require single class, BUT precedent shows ALL implementations use single class (zero multi-class examples)
- [x] What are the required responsibilities of a QueryBuilder?
  - **Answer:** 1) Encapsulate collection metadata, 2) Validate capabilities, 3) Build URLs from links, 4) Validate parameters, 5) Expose capabilities publicly
- [x] How does factory method + caching work?
  - **Answer:** Factory method in endpoint (async, checks conformance) → Map-based cache by collection_id → returns cached or creates new instance
- [x] What metadata must be encapsulated?
  - **Answer:** OgcApiCollectionInfo (private), derived capabilities (private), exposed capabilities (public), links (public) - immutable after construction
- [x] Are there examples of multi-class QueryBuilders in ogc-client?
  - **Answer:** NO - zero examples found. All implementations use single class (WFS, WMS, WMTS, EDR)
- [x] Does the pattern specify method organization?
  - **Answer:** NO formal requirements. EDR convention: properties → constructor → getters → methods (sequential, no section comments)
- [x] Can QueryBuilder delegate to helper classes?
  - **Answer:** YES for utility functions (formatting, validation), NO for splitting core functionality (zero precedent for delegation pattern)

---

## Expected Findings

**If pattern requires single class:**

- Clear mandate for CSAPIQueryBuilder as single class
- No flexibility for separate resource clients
- Must consolidate all 9 resources into one class

**If pattern allows multiple classes:**

- Could use separate classes per resource
- QueryBuilder could be a facade/coordinator
- More flexibility in organization

---

## Architecture Decision Impact

**HIGH IMPACT** - Determines whether pattern constraints force single-class approach or if we have flexibility.

---

## Synthesis Notes

Record key findings here for final synthesis document:

- **Pattern definition:** Standalone class (NOT endpoint subclass) that encapsulates collection metadata, validates capabilities, builds URLs from links, and provides typed query access. Immutable state after construction.
- **Single vs multi-class:** Pattern does NOT formally require single class, BUT precedent is absolute - ALL implementations (WFS, WMS, WMTS, EDR) use single class. Zero multi-class examples exist.
- **State management approach:** Immutable after construction. Private collection metadata, derived capability flags, public capability exposure. Factory method + Map-based caching by collection_id.
- **Method organization rules:** NO formal requirements. EDR convention: properties → constructor → getters → methods (sequential). Pattern repetition provides consistency.
- **Flexibility assessment:** Pattern theoretically allows multi-class, BUT precedent strongly constrains to single class. Helper functions for utilities = OK. Helper classes for delegation = No precedent.

**CRITICAL INSIGHT:** Pattern flexibility vs precedent constraints - while pattern allows multiple classes, zero implementation examples exist. Single class is the de facto standard.

**RECOMMENDATION:** Use single CSAPIQueryBuilder class with helper functions for utilities. Multi-class approach is pattern-compatible but precedent-incompatible (HIGH rejection risk).

**COMPLETED:** February 4, 2026  
**Findings Document:** [findings/02-querybuilder-pattern-findings.md](findings/02-querybuilder-pattern-findings.md)
