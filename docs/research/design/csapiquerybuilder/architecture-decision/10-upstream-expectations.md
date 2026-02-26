# 10: Upstream Library Expectations

**Research Question:** What does camptocamp/ogc-client expect from new API implementations, and does it favor single-class patterns?

**Source Document:** [docs/research/requirements/upstream-expectations.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/requirements/upstream-expectations.md)

**Decision Relevance:** CRITICAL - Upstream expectations directly determine what will be accepted.

---

## Research Objectives

1. **Expectation Analysis:**

   - What patterns do WFS, WMS, WMTS, EDR follow?
   - Are these patterns mandated or suggested?
   - What breaks acceptance criteria?

2. **API Design Expectations:**

   - Endpoint-oriented API structure
   - QueryBuilder vs client vs navigator terminology
   - Integration point requirements

3. **Flexibility Assessment:**
   - Where is innovation acceptable?
   - What must match existing patterns exactly?
   - What variations have been accepted?

---

## Key Questions to Answer

- [x] Do all accepted implementations use single QueryBuilder class?
  - **Answer:** YES - 100% of implementations (WFS, WMS, WMTS, EDR) use single main class. EDRQueryBuilder handles 7 query types in 561 lines. Zero multi-class examples exist.
- [x] Is endpoint-oriented API mandatory?
  - **Answer:** YES - Required pattern. All implementations: constructor takes URL, isReady() async init, getServiceInfo() metadata, operation methods.
- [x] What is the factory method signature requirement?
  - **Answer:** `async methodName(collection_id: string): Promise<QueryBuilder>` - Exact pattern from EDR must be followed. Map-based caching, conformance check first.
- [x] Are helper classes allowed alongside QueryBuilder?
  - **Answer:** Helper FILES for utilities YES (parsing, formatting, types). Helper CLASSES for operations NO (zero precedent for delegation pattern).
- [x] What organizational flexibility exists?
  - **Answer:** Flexible: file organization, helper functions, type files, test structure. Rigid: main class pattern, factory method, async init, worker support.
- [x] Have any multi-class implementations been accepted?
  - **Answer:** NO - Zero multi-class implementations in history. Pattern has never been proposed or accepted. Single-class is universal (100% consistency).
- [x] What are explicit vs implicit expectations?
  - **Answer:** Explicit: TypeScript, testing, docs, worker, compatibility. Implicit: single class (100% consistent), factory pattern, async init, file conventions, error handling.

---

## Expected Findings

**If single-class is mandatory:**

- Clear requirement for CSAPIQueryBuilder consolidation
- No room for separate-client pattern
- Must follow EDR example

**If flexibility exists:**

- May accommodate separate classes
- Could use facade pattern
- More architectural options

---

## Architecture Decision Impact

**CRITICAL IMPACT** - Defines what will be accepted vs rejected by upstream.

---

## Synthesis Notes

Record key findings here for final synthesis document:

- **Mandatory patterns:** Single main class (100% consistent), factory method `async csapi(collection_id): Promise<CSAPIQueryBuilder>`, Map-based caching, async initialization with isReady(), comprehensive TypeScript types, Web Worker support, 90%+ test coverage, JSDoc documentation, browser/Node.js compatibility
- **Flexible areas:** File organization (subfolders OK), helper files for utilities, type organization, test structure, format parsers
- **Single vs multi-class:** Single class = REQUIRED (implicit but universal). 100% of implementations use single class. Zero multi-class examples. EDR proves scalability (7 types → 561 lines). Multi-class = HIGH rejection risk (no precedent).
- **Acceptance criteria:** Follow established patterns exactly - single main class, factory method signature, async init, helper files for utilities only (NOT separate operation classes), format abstraction aligned with precedent (WFS parses GML, EDR handles WKT, CSAPI handles SensorML/SWE Common)
- **Risk assessment:** Single CSAPIQueryBuilder = LOW risk (proven, universal, expected). Multiple resource clients = HIGH risk (zero precedent, likely rejection, over-engineering, breaks implicit expectations)

**CRITICAL INSIGHT:** Upstream expectations are both explicit (documented) and implicit (pattern-based). Pattern consistency across ALL implementations = de facto requirement. Single-class pattern is universal without being formally mandated.

**RECOMMENDATION:** STRONGLY FAVOR single CSAPIQueryBuilder class following exact EDR pattern. Format abstraction (SensorML, SWE Common, GeoJSON) is fully aligned with upstream precedent.

**COMPLETED:** February 4, 2026  
**Findings Document:** [findings/10-upstream-expectations-findings.md](findings/10-upstream-expectations-findings.md)
