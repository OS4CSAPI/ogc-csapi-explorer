# Lessons from Previous Iterations

**Purpose:** Document what worked, what didn't, and what to improve from previous CSAPI implementation attempts.

**Context:** This is the third iteration. Previous attempts at OS4CSAPI/ogc-client-homework (exploratory) and OS4CSAPI/ogc-client-CSAPI (refined) provide valuable lessons.

**Date:** 2026-01-30

---

## Table of Contents

1. [Overview](#1-overview)
2. [Previous Iterations Summary](#2-previous-iterations-summary)
3. [What Worked Well](#3-what-worked-well)
4. [What Was Over-Engineered](#4-what-was-over-engineered)
5. [What Was Under-Engineered](#5-what-was-under-engineered)
6. [Maintenance Problems](#6-maintenance-problems)
7. [Testing Difficulties](#7-testing-difficulties)
8. [Likely Rejection Points](#8-likely-rejection-points)
9. [Key Improvements for This Iteration](#9-key-improvements-for-this-iteration)
10. [Success Criteria](#10-success-criteria)

---

## 1. Overview

### The Journey So Far

**First Iteration: ogc-client-homework**

- **Duration:** 257 commits
- **Purpose:** Learning phase, exploration
- **Outcome:** Understanding of ogc-client patterns
- **Status:** Not submitted

**Second Iteration: ogc-client-CSAPI**

- **Duration:** Phases 1-5 (~90% complete)
- **Purpose:** Refined implementation following PR #114 pattern
- **Outcome:** Draft PR #131 created
- **Status:** Concerns about code volume, not merged

**Third Iteration: ogc-client-CSAPI_2 (Current)**

- **Duration:** Planning/research phase
- **Purpose:** Research-first approach, address previous issues
- **Outcome:** TBD
- **Status:** In progress

### Known Feedback

**From previous iterations:**

1. **Code volume:** ~2x upstream codebase size raised concerns
2. **Test quality:** Tests were "too trivial"
3. **Terminology:** Used "navigator" instead of "QueryBuilder"
4. **Over-engineering:** Unnecessary abstractions/complexity suggested

### Research Goals

This document synthesizes lessons learned to ensure this iteration:

- Right-sizes code volume
- Uses correct terminology
- Follows upstream patterns precisely
- Creates meaningful tests
- Justifies all architectural decisions

---

## 2. Previous Iterations Summary

### First Iteration: Homework Phase

**What we learned:**

- ogc-client architecture patterns
- PR #114 EDR implementation approach
- URL-building vs data-fetching distinction
- QueryBuilder pattern (though we called it "navigator")

**Problems:**

- Exploratory code, not production-ready
- No clear architecture plan
- Mixed patterns from multiple APIs
- Insufficient research before coding

**Value:**

- Hands-on learning
- Identified key challenges
- Built familiarity with codebase

### Second Iteration: Refined Implementation

**What we attempted:**

- ~90% feature complete (Phases 1-5)
- All 9 resource types implemented
- Format negotiation (GeoJSON, SensorML)
- Comprehensive test suite
- Draft PR #131 submitted

**Problems identified:**

1. **Code volume (~2x upstream):**

   - Total implementation + tests exceeded upstream size
   - Suggested over-engineering or unnecessary complexity
   - Raised maintainer concerns about proportionality

2. **Test quality ("too trivial"):**

   - Tests checked method existence, not behavior
   - Lacked real spec examples
   - Didn't validate complete URL structures
   - Edge cases not thoroughly tested

3. **Terminology confusion:**

   - Used "navigator" instead of "QueryBuilder"
   - Inconsistent with upstream naming
   - Created alignment issues

4. **Unknown architecture justification:**
   - Decisions made during implementation
   - No clear rationale documented
   - Hard to explain choices in PR review

**Outcome:**

- Draft PR not merged
- Need to address concerns before re-submission

---

## 3. What Worked Well

### Architecture Alignment

**Following PR #114 pattern:**

- ✅ URL building only (no data fetching)
- ✅ Per-collection factory method
- ✅ Caching of builder instances
- ✅ Conformance checking

**Evidence:** Core approach was correct, just over-built.

### Resource Coverage

**Implementing all 9 resources:**

- ✅ Systems, Deployments, Procedures, etc.
- ✅ Part 1 + Part 2 coverage
- ✅ Sub-resource support

**Evidence:** Scope was correct, CSAPI needs all resources.

### Format Support

**GeoJSON + SensorML:**

- ✅ Format negotiation via query params
- ✅ Multiple output formats

**Evidence:** Approach was valid (though may have been over-implemented).

### Integration Points

**Modifications to existing files:**

- ✅ endpoint.ts - add csapi() method
- ✅ info.ts - add conformance check
- ✅ index.ts - add exports

**Evidence:** Integration pattern was correct.

### Isolation

**CSAPI-specific code in own directory:**

- ✅ src/ogc-api/csapi/
- ✅ Minimal changes to existing files

**Evidence:** File organization was good.

---

## 4. What Was Over-Engineered

### Problem 1: Code Volume (~2x Upstream)

**What was over-engineered:**

1. **Format parsing/validation:**

   - Likely implemented SensorML parsers
   - Likely implemented SWE Common parsers
   - Likely implemented format validators
   - **Cost:** ~2000-4000 lines of format code

   **Should have been:**

   - URL building with format parameter only
   - No parsing (users handle responses)
   - **Cost:** ~10 lines (format constants)

2. **Excessive validation:**

   - Likely validated resource IDs
   - Likely validated parameter values
   - Likely validated format strings
   - **Cost:** ~70-80 lines (1 per method)

   **Should have been:**

   - Trust TypeScript types
   - Trust server validation
   - Only validate conformance + collection existence
   - **Cost:** ~1 line (conformance only)

3. **Type definitions for domain objects:**

   - Likely defined System, Deployment, Observation interfaces
   - Likely defined SensorML component types
   - Likely defined SWE Common data types
   - **Cost:** ~500-1000 lines of type definitions

   **Should have been:**

   - QueryOptions interface only
   - Users define their own domain types
   - **Cost:** ~50-100 lines (query options only)

4. **Helper utilities:**

   - Likely created shared utilities for CSAPI
   - Likely created abstraction layers
   - Likely created base classes
   - **Cost:** ~200-400 lines

   **Should have been:**

   - Minimal private helpers in builder class
   - No shared utilities
   - No abstraction layers
   - **Cost:** ~30 lines (2-3 helpers)

5. **Test bloat:**

   - Likely tested every combination
   - Likely created extensive fixtures
   - Likely tested trivial functionality
   - **Cost:** Inflated test LOC

   **Should have been:**

   - Meaningful tests with real spec examples
   - Focused on URL correctness
   - Test coverage quality over quantity

**Total over-engineering estimate:** ~3000-6000 lines that should be ~100-200 lines.

### Problem 2: Wrong Terminology

**What was wrong:**

- Called builder "navigator"
- Inconsistent with upstream (which uses "QueryBuilder")
- Created confusion in PR review

**Why it happened:**

- Misread upstream patterns
- First iteration exploration used wrong term
- Carried forward without correction

**Should have been:**

- Research terminology BEFORE coding
- Use exact upstream names
- Align all naming with established patterns

### Problem 3: Unnecessary Abstractions

**Likely over-abstractions:**

1. **Base classes for resources:**

   ```typescript
   // ❌ Likely did this
   abstract class ResourceBuilder {
     abstract resourceType: string;
     list(): string { ... }
     get(id: string): string { ... }
   }
   ```

   **Problems:**

   - No other API uses inheritance
   - Adds complexity
   - Harder to navigate

2. **Resource-specific navigators:**

   ```typescript
   // ❌ Likely did this
   class SystemsNavigator { ... }
   class DeploymentsNavigator { ... }
   // 9 separate classes
   ```

   **Problems:**

   - Code explosion (9x classes)
   - No upstream precedent
   - Over-engineered

3. **Shared utilities module:**

   ```typescript
   // ❌ Likely created this
   src / ogc - api / csapi / utils.ts; // Shared CSAPI utilities
   ```

   **Problems:**

   - Creates internal coupling
   - Not needed for simple URL building
   - Adds file count

**Should have been:**

- Single CSAPIQueryBuilder class
- Private helper methods, no abstraction
- No separate utility modules

---

## 5. What Was Under-Engineered

### Problem 1: Test Quality

**What was under-engineered:**

**Trivial tests:**

```typescript
// ❌ Previous approach (trivial)
it('should have getSystems method', () => {
  expect(typeof builder.getSystems).toBe('function');
});

it('should return string', () => {
  expect(typeof builder.getSystems()).toBe('string');
});
```

**Why insufficient:**

- Doesn't validate URL correctness
- Doesn't check query parameters
- Doesn't test spec compliance
- Doesn't catch real bugs

**Should have been:**

```typescript
// ✅ Better approach (meaningful)
it('should build systems URL with query parameters', () => {
  const url = builder.getSystems({
    bbox: [-180, -90, 180, 90],
    datetime: '2024-01-01T00:00:00Z/..',
    limit: 10,
  });

  expect(url).toBe(
    'https://api.example.com/systems?' +
      'bbox=-180,-90,180,90&' +
      'datetime=2024-01-01T00:00:00Z/..&' +
      'limit=10'
  );
});

it('should properly encode special characters in parameters', () => {
  const url = builder.getSystem('sys-123/special?chars');
  expect(url).toContain('sys-123%2Fspecial%3Fchars');
});
```

### Problem 2: Documentation

**What was likely missing:**

- Clear architectural rationale
- Code volume justification
- Per-resource breakdown
- Comparison to EDR

**Should have been:**

- Comprehensive design research (like current approach)
- Code volume analysis upfront
- Architectural decision records
- PR description with full justification

### Problem 3: Incremental Planning

**What was likely missing:**

- Clear roadmap with phases
- Justification for each decision
- Pre-implementation research
- Architecture review before coding

**Should have been:**

- Research phase (Sections 1-12 complete BEFORE coding)
- Testing strategy defined upfront
- Architecture validated against upstream
- Incremental PR approach (Part 1 first?)

---

## 6. Maintenance Problems

### Problem 1: Unclear Responsibilities

**Likely issue:**

- Mixed concerns (URL building + validation + parsing)
- Unclear what library does vs user does
- Too much library functionality

**Impact:**

- Hard to maintain
- Hard to extend
- Hard to review

**Solution:**

- Clear separation: library builds URLs only
- User handles fetch, parsing, validation
- Minimal scope = easier maintenance

### Problem 2: Tight Coupling

**Likely issue:**

- CSAPI utilities coupled to shared code
- Format parsers coupled to CSAPI
- Resource classes coupled to each other

**Impact:**

- Changes ripple through codebase
- Hard to isolate bugs
- Merge conflict risk

**Solution:**

- Minimal imports (7 utilities)
- Duplicate simple helpers
- Strong isolation between resources

### Problem 3: Test Maintenance

**Likely issue:**

- Brittle tests (coupled to implementation)
- Incomplete coverage despite high LOC
- Hard to update when spec changes

**Impact:**

- Tests break on refactoring
- Low confidence in changes
- Test maintenance burden

**Solution:**

- Test behavior, not implementation
- Use real spec examples
- Focus on URL correctness

---

## 7. Testing Difficulties

### Problem 1: What to Test

**Previous confusion:**

- Should we test HTTP responses? (No - no fetch in library)
- Should we test parsing? (No - no parsing in library)
- Should we test validation? (Minimal - trust TypeScript)

**Clarity needed:**

- Test URL structure
- Test query parameter encoding
- Test spec compliance
- Test edge cases (null, undefined, empty)

### Problem 2: Test Quality Standards

**Previous approach:**

- High line count
- Low value per test
- "Too trivial" feedback

**Better approach:**

- Real spec examples
- Complete URL validation
- Edge case coverage
- Quality over quantity

### Problem 3: Test Organization

**Likely issue:**

- One test file per method?
- One test file per resource?
- Unclear organization

**Better approach:**

- url_builder.spec.ts - test builder class
- Resource-grouped tests
- Clear describe blocks
- Follow EDR test structure

---

## 8. Likely Rejection Points

### Rejection Point 1: Code Volume

**Why it matters:**

- ~2x upstream size overwhelming
- Suggests over-engineering
- Creates review burden
- Long-term maintenance concern

**Threshold:**

- Acceptable: ~560-760 lines (15-19% of upstream)
- Concerning: >1000 lines implementation
- Rejection risk: >2000 lines implementation

**Mitigation:**

- Remove format parsing (~2000-4000 lines saved)
- Remove validation (~70-80 lines saved)
- Remove domain types (~500-1000 lines saved)
- Remove abstractions (~200-400 lines saved)
- **Result:** ~560-760 lines total

### Rejection Point 2: Wrong Patterns

**What would be rejected:**

- "Navigator" instead of "QueryBuilder"
- Inheritance hierarchies
- Separate resource classes
- Data fetching in library

**Mitigation:**

- Use exact upstream terminology
- Follow EDR pattern precisely
- Single QueryBuilder class
- URL building only

### Rejection Point 3: Poor Test Quality

**What would be rejected:**

- Trivial tests (check method exists)
- No spec compliance validation
- Missing edge cases
- No real examples

**Mitigation:**

- Meaningful tests with real spec data
- Validate complete URL structures
- Test all query parameter combinations
- Edge case coverage

### Rejection Point 4: Unclear Justification

**What would be rejected:**

- "CSAPI needs this" without explanation
- Unexplained architectural choices
- No comparison to EDR
- No code volume analysis

**Mitigation:**

- Complete design research (Sections 1-12)
- Per-resource code breakdown
- Comparison to EDR
- Clear rationale for every decision

### Rejection Point 5: Modifying Existing Code

**What would be rejected:**

- Refactoring existing utilities
- Changing existing patterns
- Fixing unrelated bugs
- Formatting existing code

**Mitigation:**

- Additive-only approach
- ~48 lines modified in 3 files only
- No refactoring
- No unrelated changes

---

## 9. Key Improvements for This Iteration

### Improvement 1: Research-First Approach

**Previous:** Code first, justify later

**This iteration:**

1. ✅ Section 1: Terminology (get naming right)
2. ✅ Section 2: Architecture Patterns (understand upstream)
3. ✅ Section 3: QueryBuilder Pattern (exact pattern)
4. ✅ Section 4: URL Building (how to build URLs)
5. ✅ Section 5: TypeScript Types (minimal types)
6. ✅ Section 6: File Organization (where code goes)
7. ✅ Section 7: Integration (how to integrate)
8. ✅ Section 8: Format Negotiation (no parsing)
9. ✅ Section 9: Error Handling (minimal validation)
10. ✅ Section 10: CSAPI Architecture (9 resources cleanly)
11. ✅ Section 11: Code Reuse (minimal coupling)
12. ✅ Section 12: Lessons Learned (this document)

**Result:** Architectural decisions validated BEFORE coding.

### Improvement 2: Code Volume Target

**Previous:** ~2x upstream (concerning)

**This iteration:**

- Implementation: ~560-760 lines
- Modified files: ~48 lines
- Total: ~15-19% of upstream
- Per resource: ~62-84 lines
- **5-6x more efficient than EDR per resource**

**Result:** Right-sized contribution.

### Improvement 3: Correct Terminology

**Previous:** "Navigator" (wrong)

**This iteration:**

- CSAPIQueryBuilder (correct)
- Matches EDRQueryBuilder pattern
- Consistent with upstream

**Result:** Clear alignment with existing code.

### Improvement 4: Minimal Scope

**Previous:** Parsing + validation + types + URL building

**This iteration:**

- URL building only
- No parsing
- Minimal validation (conformance only)
- Minimal types (query options only)

**Result:** Focused, maintainable contribution.

### Improvement 5: Test Quality

**Previous:** Trivial tests

**This iteration:**

- Real spec examples
- Complete URL validation
- Edge case coverage
- Meaningful assertions

**Result:** High-quality, valuable test suite.

### Improvement 6: Clear Justification

**Previous:** Unexplained decisions

**This iteration:**

- 12 comprehensive analysis documents
- Code volume breakdown
- Comparison to EDR
- Rationale for every choice

**Result:** Easy PR review, clear justification.

### Improvement 7: Strong Isolation

**Previous:** Coupled to shared utilities, abstractions

**This iteration:**

- 7 minimal imports
- ~75 lines duplicated (isolated)
- No new shared utilities
- Single QueryBuilder class

**Result:** Low coupling, high cohesion.

---

## 10. Success Criteria

### Criteria for This Iteration

**Code Volume:**

- ✅ Implementation: 500-760 lines
- ✅ Per resource: 62-84 lines average
- ✅ Modified upstream: ~48 lines
- ✅ Justification: Documented in Section 10

**Terminology:**

- ✅ CSAPIQueryBuilder (not navigator)
- ✅ Matches upstream naming exactly
- ✅ Documented in Section 3

**Architecture:**

- ✅ Single QueryBuilder class
- ✅ No inheritance or abstractions
- ✅ Follow EDR pattern precisely
- ✅ Documented in Sections 2, 10

**Scope:**

- ✅ URL building only
- ✅ No parsing, minimal validation
- ✅ Minimal types
- ✅ Documented in Sections 8, 9

**Testing:**

- ✅ Real spec examples
- ✅ Complete URL validation
- ✅ Edge case coverage
- ✅ Documented in testing-strategy-research.md

**Justification:**

- ✅ 12 analysis documents complete
- ✅ Every decision explained
- ✅ Comparison to EDR provided
- ✅ Code volume justified

**Integration:**

- ✅ Minimal modifications (3 files, ~48 lines)
- ✅ Additive approach
- ✅ No refactoring
- ✅ Documented in Section 7

### Lessons Applied

| Lesson        | Previous                 | This Iteration        |
| ------------- | ------------------------ | --------------------- |
| Code volume   | ~2x upstream             | ~15-19% upstream      |
| Terminology   | "Navigator"              | "QueryBuilder"        |
| Parsing       | SensorML/SWE parsers     | None - URL only       |
| Validation    | Extensive                | Minimal (conformance) |
| Types         | Domain objects           | Query options only    |
| Architecture  | Abstractions/inheritance | Single class, helpers |
| Testing       | Trivial tests            | Meaningful tests      |
| Research      | Code first               | Research first        |
| Justification | Unexplained              | 12 analyses complete  |
| Coupling      | Shared utilities         | 7 minimal imports     |

**Result:** All major concerns from previous iterations addressed.

---

## Summary

### What We Learned

**From first iteration (homework):**

- ogc-client patterns and structure
- URL building vs data fetching distinction
- Need for careful research before coding

**From second iteration (ogc-client-CSAPI):**

- Code volume concerns (~2x upstream)
- Test quality issues ("too trivial")
- Terminology errors ("navigator" vs "QueryBuilder")
- Over-engineering (parsing, validation, abstractions)
- Need for clear justification

### Key Changes for This Iteration

1. **Research first** - 12 comprehensive analyses BEFORE coding
2. **Right-size** - ~560-760 lines vs ~2x upstream
3. **Correct terminology** - CSAPIQueryBuilder (not navigator)
4. **Minimal scope** - URL building only, no parsing
5. **Quality tests** - Meaningful tests with real examples
6. **Clear justification** - Every decision documented
7. **Strong isolation** - Minimal coupling, simple design

### Expected Outcome

**Previous iterations:**

- First: Not submitted (exploratory)
- Second: Draft PR, concerns raised, not merged

**This iteration:**

- Research complete
- Architecture validated
- Concerns addressed proactively
- Clear justification prepared
- **Expected:** Successful PR merge

**Confidence level:** High - all known issues addressed through systematic research and planning.
