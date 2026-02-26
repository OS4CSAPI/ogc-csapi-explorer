# 12: File Organization Implications

**Research Question:** How does single-class vs multi-class affect file organization, and what does ogc-client convention dictate?

**Source Document:** [docs/research/upstream/file-organization-analysis.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/upstream/file-organization-analysis.md)

**Decision Relevance:** MEDIUM - File organization should follow established patterns for consistency.

---

## Research Objectives

1. **Pattern Survey:**

   - EDR file structure (single QueryBuilder)
   - WFS/WMS file structures
   - Common organization patterns

2. **Multi-Class Implications:**

   - How would separate resource clients be organized?
   - Additional file count
   - Export/import complexity

3. **Convention Analysis:**
   - What file organization is standard?
   - Where is flexibility allowed?
   - Test organization patterns

---

## Key Questions to Answer

- [x] What is EDR's file structure?
- [x] One file for QueryBuilder or split across multiple?
- [x] How are types organized?
- [x] How would 9 separate client classes be organized?
- [x] What is the fixture organization pattern?
- [x] How are tests organized (per-resource or consolidated)?
- [x] What conventions must be followed?

---

## Synthesis Notes

**Research Status:** ✅ COMPLETE

**Key Findings:**

1. **EDR File Structure:** 5 files (model.ts, url_builder.ts, helpers.ts + 2 tests), flat structure, 675 total lines
2. **QueryBuilder Organization:** Single file (url_builder.ts), 380 lines for 1 resource → CSAPI needs 700-800 lines for 9 resources (78-89 lines/resource, more efficient than EDR)
3. **Type Organization:** All types in model.ts (126 lines for EDR → 350-400 for CSAPI)
4. **Multi-Class Estimate:** 9 builders = 36-41 total files (breaks flat structure convention, requires subdirectories)
5. **Fixture Pattern:** fixtures/ogc-api/{api}/ with collection + item examples
6. **Test Organization:** Colocated .spec.ts files next to implementation
7. **Conventions:** Flat structure (<10 files), relative imports with .js, default export for classes

**Convention Compliance:**

- Single-class: ✅ 100% (9/9 rules)
- Multi-class: ❌ 50-60% (4-5/9 rules, breaks flat structure)

**Recommendation:** Single-class with 5-6 core files + formats/ subfolder (justified by 3,300+ lines)

**Impact on Part 1 Decision:** Reinforces single-class choice - file organization is simpler, cleaner, follows precedent exactly

**Detailed Analysis:** See [findings/12-file-organization-findings.md](findings/12-file-organization-findings.md)

---

## Expected Findings

**If single-class has simpler organization:**

- Fewer files to manage
- Clearer structure
- Favors consolidation

**If multi-class is acceptable:**

- More files but clear separation
- May improve navigability
- Both patterns viable

---

## Architecture Decision Impact

**MEDIUM IMPACT** - File organization affects maintainability and follows convention.

---

## Synthesis Notes

Record key findings here for final synthesis document:

- EDR file count: [Number]
- Multi-class file estimate: [Number]
- Organization pattern: [Description]
- Convention compliance: [Assessment]
- Recommendation: [File organization perspective]
