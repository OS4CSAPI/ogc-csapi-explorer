# 08: oscar-viewer TypeScript Production Patterns

**Research Question:** What architectural patterns does oscar-viewer use in production TypeScript, and how does it organize CSAPI access?

**Source Document:** [docs/research/requirements/csapi-oscarviewer-analysis.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/requirements/csapi-oscarviewer-analysis.md)

**Decision Relevance:** MEDIUM - Real-world TypeScript usage, shows what works in production.

---

## Research Objectives

1. **Client Library Usage:**

   - What CSAPI client does oscar-viewer use?
   - How does it organize access to different resources?
   - Wrapper patterns or direct usage?

2. **TypeScript Patterns:**

   - Object-oriented wrapper patterns
   - Type safety approaches
   - Code organization for multi-resource access

3. **Production Insights:**
   - What patterns emerged from real usage?
   - Any pain points with client organization?
   - Preferred access patterns?

---

## Key Questions to Answer

- [ ] What CSAPI client library does oscar-viewer use?
- [ ] Does it wrap client in separate classes per resource?
- [ ] How are System, Datastream, Observation accesses organized?
- [ ] Are there object-oriented wrappers?
- [ ] What TypeScript patterns are used?
- [ ] Any evidence of client organization preferences?

---

## Expected Findings

**If uses separate wrappers:**

- Real-world evidence for separate-class pattern
- Shows benefits in production
- Informs our decision

**If uses single client:**

- Shows single-class pattern works
- May inform method organization
- Different perspective

---

## Architecture Decision Impact

**MEDIUM IMPACT** - Real production usage provides valuable insights into what developers actually need.

---

## Synthesis Notes

Record key findings here for final synthesis document:

- Client library used: [Name]
- Organization pattern: [Description]
- Wrapper strategy: [Analysis]
- Production insights: [Key takeaways]
