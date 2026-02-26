# 18: Part 2 Resource Scope and Complexity

**Research Question:** How does Part 2's dynamic data complexity (4 resource types with schemas, pagination, temporal queries) affect architecture?

**Source Document:** [docs/research/requirements/csapi-part2-requirements.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/requirements/csapi-part2-requirements.md)

**Decision Relevance:** MEDIUM - Part 2's additional complexity may be the tipping point for architecture decisions.

---

## Research Objectives

1. **Complexity Assessment:**

   - Part 2 resource count and operations
   - Schema operations complexity
   - Temporal query patterns
   - Cursor pagination differences

2. **Combined Scope:**
   - Total Part 1 + Part 2 method count estimate
   - Single class feasibility with both parts
   - Code organization at full scale

---

## Key Questions to Answer

- [ ] How many unique operations for 4 Part 2 resources?
- [ ] What additional complexity does Part 2 add (schemas, cursors)?
- [ ] Combined method count estimate (Part 1 + Part 2)?
- [ ] Is single class still manageable at full CSAPI scope?
- [ ] Would Part 1/Part 2 split make sense?

---

## Expected Findings

Part 2 complexity added to Part 1 scope may reveal single-class challenges. Could justify separate organization for Part 2 resources.

---

## Architecture Decision Impact

**MEDIUM IMPACT** - Combined scope is the real test of single-class pattern viability.

---

## Synthesis Notes

Record key findings here for final synthesis document:

- Part 2 operation count: [Number]
- Additional complexity factors: [List]
- Combined method estimate: [Total]
- Single-class viability: [Assessment]
- Part 1/Part 2 split consideration: [Analysis]
