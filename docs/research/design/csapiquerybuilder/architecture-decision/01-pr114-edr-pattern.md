# 01: PR #114 EDR Implementation Pattern Analysis

**Research Question:** What architectural pattern did the accepted EDR implementation use, and does it mandate a single QueryBuilder class approach?

**Source Document:** [docs/research/upstream/pr114-analysis.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/upstream/pr114-analysis.md)

**Decision Relevance:** CRITICAL - This is the pattern that upstream (camptocamp/ogc-client) accepted and merged. It represents their expectations.

---

## Research Objectives

1. **Pattern Identification:**

   - Confirm the EDR implementation used a single `EDRQueryBuilder` class
   - Document factory method signature and instantiation pattern
   - Identify how EDR handled multiple query types (position, area, cube, etc.)

2. **Class Organization:**

   - How many classes were created for EDR support?
   - Was there one class per query type or one consolidated class?
   - How were methods organized within the QueryBuilder?

3. **Integration Points:**

   - What files were modified to integrate EDR? (endpoint.ts, info.ts, index.ts)
   - How many lines of integration code were required?
   - What conformance checking pattern was used?

4. **Scalability Analysis:**
   - EDR has 7 query types; CSAPI has 9 resource types
   - Did EDR's single-class pattern handle 7 types successfully?
   - Are there signs of maintainability issues or code bloat?

---

## Key Questions to Answer

- [x] Does EDR use one `EDRQueryBuilder` class or multiple classes?
  - **Answer:** ONE single class (`EDRQueryBuilder`, 561 lines)
- [x] How many methods are in `EDRQueryBuilder`?
  - **Answer:** 7 primary URL building methods (one per query type)
- [x] How are methods grouped/organized (by query type sections)?
  - **Answer:** Sequential organization, no section comments, each method ~50-80 lines
- [x] What is the factory method signature in `endpoint.ts`?
  - **Answer:** `public async edr(collection_id: string): Promise<EDRQueryBuilder>`
- [x] How is caching implemented for QueryBuilder instances?
  - **Answer:** Map-based: `Map<string, EDRQueryBuilder>`, keyed by collection_id
- [x] What conformance classes does EDR check?
  - **Answer:** `http://www.opengis.net/spec/ogcapi-edr-1/1.0/conf/core`
- [x] How many files were modified for integration?
  - **Answer:** 4 files (endpoint.ts, info.ts, model.ts, link-utils.ts), 115 lines total
- [x] What is the total LOC for the EDR implementation?
  - **Answer:** ~2,800 lines total (750 implementation, 375 tests, 1,700 fixtures)

---

## Expected Findings

**If EDR uses single class:**

- Confirms upstream expectation for consolidated pattern
- Provides direct blueprint for CSAPIQueryBuilder
- Suggests CSAPI should follow same pattern

**If EDR uses multiple classes:**

- Questions current CSAPI design assumptions
- Suggests separate resource clients might be acceptable
- Requires deeper investigation into why

---

## Architecture Decision Impact

**HIGH IMPACT** - This determines whether we:

- Follow proven EDR pattern (single QueryBuilder)
- Deviate and potentially face rejection
- Need to justify any architectural differences

---

## Synthesis Notes

Record key findings here for final synthesis document:

- **Pattern used:** Single class (`EDRQueryBuilder`, 561 lines)
- **Method count:** 7 primary URL building methods (one per query type)
- **Organization strategy:** Sequential methods, each ~50-80 lines, consistent pattern repeated
- **Integration complexity:** 115 lines across 4 files (endpoint.ts +43, info.ts +16, model.ts +47, link-utils.ts +9)
- **Scalability observations:** No issues; 7 query types handled cleanly; CSAPI projection: 850-950 lines for 9 resources
- **Caching pattern:** Map-based (`Map<string, EDRQueryBuilder>`), elegant and simple
- **Testing:** 375 lines of tests, fixture-driven, comprehensive coverage
- **Risk assessment:** Following EDR pattern = LOW risk (proven); Deviating = HIGH risk (rejection)

**RECOMMENDATION:** STRONGLY FAVOR single `CSAPIQueryBuilder` class following exact EDR pattern.

**COMPLETED:** February 4, 2026  
**Findings Document:** [findings/01-pr114-edr-pattern-findings.md](findings/01-pr114-edr-pattern-findings.md)
