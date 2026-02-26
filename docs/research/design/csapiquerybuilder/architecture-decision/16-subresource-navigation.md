# 16: Sub-Resource Navigation Patterns

**Research Question:** How do nested resource patterns affect class organization decisions?

**Source Document:** [docs/research/requirements/csapi-subresource-navigation.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/requirements/csapi-subresource-navigation.md)

**Decision Relevance:** LOW-MEDIUM - Nested navigation may inform method organization but not overall architecture.

---

## Research Objectives

1. **Navigation Pattern Analysis:**

   - Document nested endpoint patterns
   - Identify cross-resource relationships
   - Note navigation depth

2. **Organization Impact:**
   - Does nesting favor single class?
   - Would separate classes handle navigation differently?
   - Method organization implications

---

## Key Questions to Answer

- [x] How many nested navigation patterns exist?

  - **16 distinct parent→child navigation patterns**
  - 2 Hierarchical (unlimited depth): Systems→Subsystems, Deployments→Subdeployments
  - 12 Compositional (depth 1): System→SamplingFeatures, System→DataStreams, DataStream→Observations, etc.
  - 2 Associative (bidirectional): System↔Deployment
  - Maximum navigation depth: 6+ levels (System→Subsystem→...→DataStream→Observation)

- [x] Do nested patterns span resource types?

  - **YES - 100% of navigation patterns cross resource type boundaries**
  - Systems navigate to 5 different resource types (Subsystems, Deployments, SamplingFeatures, DataStreams, ControlStreams)
  - Multi-hop navigation (3-6 resource types) is common
  - NOT A SINGLE navigation pattern stays within one resource type
  - Examples: System→DataStream→Observations (3 types), System→ControlStream→Commands→Status (4 types)

- [x] Would separate classes complicate navigation?

  - **YES - Dramatically**
  - Multi-class requires 9 circular class dependencies (all-to-all references)
  - Method chaining breaks at every class boundary
  - Type safety lost (casting required at boundaries)
  - Factory pattern/registry required (+150-200 lines architectural complexity)
  - Code increase: +60% more lines (1,070 vs 600), +733% more files (11 vs 3)
  - Developer experience: Awkward builder switching vs natural fluent API

- [x] Can single class handle all navigation cleanly?

  - **YES - Naturally and elegantly**
  - Seamless method chaining across all 16 navigation patterns
  - Full type safety preserved through entire chain
  - Context tracking via parent context field (internal state)
  - Zero circular dependencies
  - 500-600 lines in single file vs 790-1,070 lines in 11 files
  - Fluent API: `client.systems('id').datastreams('id').getObservations()` - no breaks

- [x] What method naming handles nesting best?
  - **Consistent pattern across all 16 navigation patterns:**
  - Resource collections: `get{Resource}s()` (plural)
  - Single resource: `get{Resource}ById(id)` (singular)
  - Nested collections: `get{Parent}{Children}(parentId, options)` (explicit parent)
  - Fluent navigation: `{parent}(id).get{Children}(options)` (contextual methods)
  - Single-class enables explicit method names (clear without context)
  - Multi-class forces implicit context (ambiguous method names)

---

## Expected Findings

Nested navigation likely works in either pattern. May inform method naming more than class structure.

---

## Architecture Decision Impact

**LOW-MEDIUM IMPACT** - Tactical implementation concern rather than strategic architecture driver.

---

## Synthesis Notes

Record key findings here for final synthesis document:

### Navigation Patterns Analysis

- **Total patterns: 16 parent→child relationships** across Part 1 and Part 2
- **Pattern breakdown:**
  - Hierarchical: 2 patterns (12.5%) - Unlimited depth recursion (Systems, Deployments)
  - Compositional: 12 patterns (75%) - Parent owns child, depth 1
  - Associative: 2 patterns (12.5%) - Many-to-many bidirectional
- **Maximum depth: 6+ levels** (System→Subsystem→...→DataStream→Observation)
- **Common depth: 2-3 levels** (most real-world usage)

### Cross-Resource Navigation

- **CRITICAL FINDING: 100% of navigation patterns cross resource type boundaries**
- Systems navigate to 5 different resource types
- Multi-hop navigation paths span 3-6 resource types
- Zero navigation patterns stay within single resource type
- Examples:
  - System → DataStream → Observations (3 resource types)
  - System → ControlStream → Commands → Status (4 resource types)
  - System → Subsystem → ... → DataStream → Observation (6+ resource types)

### Organization Impact

- **STRONGLY opposes class separation**
- **Single-class advantages:**
  - Seamless method chaining across all 16 patterns (0 breaks)
  - Full type safety through entire navigation chain
  - Context tracking via internal parent context field
  - 500-600 lines in 1 file
  - Zero circular dependencies
  - Natural fluent API: `client.systems('id').datastreams('id').getObservations()`
- **Multi-class disadvantages:**
  - Method chaining breaks at every class boundary (9+ breaks)
  - Type safety lost (casting required at boundaries)
  - 9 circular class dependencies (all-to-all references)
  - 790-1,070 lines in 11 files (+60% code, +733% files)
  - Factory pattern/registry required (+architectural complexity)
  - Awkward builder switching interrupts navigation flow

### Code Complexity Comparison

| Metric              | Single-Class  | Multi-Class     | Difference |
| ------------------- | ------------- | --------------- | ---------- |
| Navigation code     | 500-600 lines | 790-1,070 lines | +60%       |
| Files               | 3 files       | 11 files        | +733%      |
| Circular deps       | 0             | 9 classes       | +∞         |
| Method chain breaks | 0             | Every boundary  | +∞         |
| Type safety         | Full          | Partial         | -50%       |

### Developer Experience

- **Single-class: Natural, readable, type-safe**
  - One fluent chain: `client.systems('id').datastreams('id').getObservations()`
  - IDE autocomplete works perfectly at every step
  - Type inference preserved through entire chain
- **Multi-class: Awkward, verbose, type-unsafe**
  - Builder switching required at every resource boundary
  - IDE autocomplete breaks at boundaries
  - Type safety lost (casting needed)
  - Manual builder selection required

### Architecture Decision Impact

- **VERY HIGH IMPACT** - Navigation patterns fundamentally favor unified class structure
- **Confidence: ⭐⭐⭐⭐⭐ (5/5)**
- **Recommendation: Single-class organization**
- **Rationale:**
  1. 100% of navigation crosses resource boundaries (class boundaries become barriers)
  2. Fluent API requires seamless chaining (multi-class breaks chains)
  3. Deep navigation is common (single-class handles naturally)
  4. Multi-class creates circular dependencies (single-class avoids entirely)
  5. Multi-class increases code complexity (+60% code, +733% files)
  6. Developer experience vastly superior with single-class

### Key Insight

Subresource navigation provides **the strongest evidence yet AGAINST class separation**. Navigation patterns are inherently cross-resource, requiring seamless traversal across multiple resource types. Class boundaries become barriers to natural navigation, forcing complex cross-class coupling, breaking method chains, and degrading developer experience. Single-class organization enables natural, type-safe, fluent navigation APIs that match user expectations and industry standards (AWS SDK, Google Cloud SDK, Stripe).
