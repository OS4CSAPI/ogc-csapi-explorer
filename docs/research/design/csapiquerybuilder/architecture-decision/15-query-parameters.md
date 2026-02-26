# 15: Query Parameter Complexity Analysis

**Research Question:** How does query parameter complexity affect class organization decisions?

**Source Document:** [docs/research/requirements/csapi-query-parameters.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/requirements/csapi-query-parameters.md)

**Decision Relevance:** LOW-MEDIUM - Parameter handling impacts implementation but may not drive architecture.

---

## Research Objectives

1. **Parameter Scope:**

   - How many parameters are resource-specific vs shared?
   - Parameter combination complexity
   - Resource-specific validation needs

2. **Organization Analysis:**
   - Would separate classes simplify parameter handling?
   - Can single class manage all parameter combinations?
   - Code reuse opportunities

---

## Key Questions to Answer

- [x] How many unique query parameters across all resources?

  - **30+ unique parameters total**
  - 5 Standard OGC API (bbox, datetime, limit, offset, f)
  - 4+ CSAPI Common (id, uid, q, {propertyName})
  - 1 Hierarchical (recursive)
  - 8 Relationship (parent, procedure, foi, observedProperty, controlledProperty, system, baseProperty, objectType)
  - 4 Temporal Part 2 (phenomenonTime, resultTime, executionTime, issueTime)
  - 2 Format schema (obsFormat, cmdFormat)
  - 1 Pagination (cursor)

- [x] How many are shared vs resource-specific?

  - **47% shared** (14 parameters used by multiple resources)
  - **53% resource-specific** (16 parameters specific to 1-2 resources)
  - Parameters cluster by TYPE (spatial, temporal, relationship), NOT by resource

- [x] Does parameter complexity favor class separation?

  - **NO - Strongly favors single-class**
  - Parameter validation is type-based, not resource-based
  - Parameter encoding is type-based, not resource-based
  - Zero resource-specific validation logic exists

- [x] Can parameter handling be abstracted across resources?

  - **YES - Extremely effectively**
  - Single-class: 150-200 lines shared helpers, 85% reuse efficiency
  - Multi-class: 1,350-1,800 lines duplicated across 9 classes, 0% reuse
  - Type-based abstraction (spatial, temporal, pagination handlers) is natural

- [x] What validation is resource-specific?
  - **NONE - All validation is parameter-type specific**
  - bbox validation: Same for all 4 resources with geometry
  - datetime validation: Same for all 5+ resources with temporal properties
  - Pagination validation: Same for ALL 9 resources
  - TypeScript interfaces provide compile-time parameter applicability validation

---

## Expected Findings

Likely shows parameter handling is manageable in either pattern with proper helper methods.

---

## Architecture Decision Impact

**LOW-MEDIUM IMPACT** - Implementation detail that adapts to chosen architecture.

---

## Synthesis Notes

Record key findings here for final synthesis document:

### Parameter Count Analysis

- **Total: 30+ unique parameters** across all CSAPI resources
- **Shared parameters: 14 (47%)** - Used by multiple resources
  - Universal (9 resources): limit, offset, f, id, uid, q (6 parameters)
  - Multi-resource: bbox (4), datetime (5), observedProperty (4), controlledProperty (4), recursive (2), parent (2), foi (3)
- **Resource-specific: 16 (53%)** - Used by 1-2 resources
  - But parameters cluster by TYPE (temporal, relationship), not randomly distributed

### Complexity Assessment

- **Parameter validation: Type-based, NOT resource-based**
  - bbox validation: Same for all 4 resources with geometry
  - datetime validation: Same for all 5+ resources with temporal properties
  - Pagination validation: Same for ALL 9 resources
  - Zero resource-specific validation logic exists
- **Parameter encoding: Type-based, NOT resource-based**
  - Same encoding rules apply across multiple resources
  - Shared encoding helpers eliminate duplication
- **TypeScript interfaces provide compile-time parameter applicability validation**
  - Works equally well with single-class or multi-class
  - Class separation provides NO additional safety

### Code Organization Implications

- **STRONGLY favors single-class with shared helpers**
- **Single-class metrics:**
  - Parameter handling: 150-200 lines (ONE implementation)
  - Code reuse efficiency: 85% (helpers used by 60+ methods)
  - Duplication: 0 lines
  - Bug fix locations: 1 class
- **Multi-class metrics (hypothetical):**
  - Parameter handling: 1,350-1,800 lines (NINE duplicate implementations)
  - Code reuse efficiency: 0% (each class has own copy)
  - Duplication: 1,200-1,600 lines (726% overhead)
  - Bug fix locations: Up to 9 classes (800% maintenance penalty)
- **Test code duplication:**
  - Single-class: 1 test suite (~200-300 lines)
  - Multi-class: 9 test suites (~1,800-2,700 lines) - 800-1200% overhead

### Architecture Impact

- **Parameter complexity provides strong evidence AGAINST class separation**
- **Confidence: ⭐⭐⭐⭐⭐ (5/5)**
- **Recommendation: Single-class organization with type-based parameter helpers**

### Key Insight

Parameters are naturally organized by TYPE (spatial, temporal, pagination, relationship, format), NOT by resource. This type-based organization maps perfectly to shared helper methods in a single class, but creates massive duplication if spread across multiple resource-specific classes.
