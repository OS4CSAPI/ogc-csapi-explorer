# Section 26: Sub-Resource Navigation Testing - Research Plan

**Status:** ✅ Complete  
**Last Updated:** February 6, 2026  
**Actual Research Time:** 3.5 hours  
**Estimated Test Implementation Lines:** ~2,450 lines

---

## 1. Research Objective

Define testing strategy for nested resource navigation patterns (e.g., `/systems/{id}/datastreams`).

**Why 26th:** After format negotiation (Section 25), test complex nested resource navigation and bidirectional navigation patterns.

---

## 2. Research Questions

### Core Questions

1. What are all the CSAPI nested resource patterns?
2. How to test all sub-resource navigation paths?
3. How to test bidirectional navigation?
4. How to test query parameters on nested endpoints?
5. How to test filtering on nested resources?
6. What happens with invalid nested paths?

### Detailed Questions

- What sub-resources does each resource type expose?
- Can sub-resources be accessed from multiple parent types?
- How does pagination work on nested endpoints?
- How do query parameters work on nested endpoints?
- What is the URL structure for nested resources?
- How to test navigation from parent to child?
- How to test navigation from child back to parent?
- What link relations are used for nested navigation?
- How to test nested resource not found scenarios?
- What are the permission models for nested resources?

---

## 3. Primary Resources

- **Sub-Resource Navigation Requirements**: [docs/research/requirements/subresource-navigation-requirements.md](../../requirements/subresource-navigation-requirements.md)
- **Implementation Guide**: [docs/planning/csapi-implementation-guide.md](../../../planning/csapi-implementation-guide.md) (Sub-resource patterns)
- **ROADMAP Phase 2**: [docs/planning/ROADMAP.md](../../../planning/ROADMAP.md) (Sub-resource navigation implementation)
- **CSAPI Specifications**: All parts define sub-resource relationships

## 4. Supporting Resources

- Section 8 deliverable (CSAPI Spec Review - resource relationships)
- Section 13 deliverable (Resource Method Testing - navigation patterns)
- Section 23 deliverable (Pagination - pagination on nested endpoints)
- Section 24 deliverable (Query Parameters - parameters on nested endpoints)

---

## 5. Research Methodology

### Phase 1: Sub-Resource Pattern Inventory (TBD minutes)

**Objective:** Create complete inventory of CSAPI sub-resource patterns

**Tasks:**

1. Extract sub-resource patterns from CSAPI Part 1
2. Extract sub-resource patterns from CSAPI Part 2
3. Extract sub-resource patterns from CSAPI Part 3
4. Document parent-child relationships
5. Document bidirectional navigation patterns
6. Create sub-resource navigation matrix

### Phase 2: URL Structure Analysis (TBD minutes)

**Objective:** Analyze sub-resource URL patterns

**Tasks:**

1. Document URL structure for each sub-resource
2. Identify URL parameter patterns ({id} placeholders)
3. Document query parameter support on nested endpoints
4. Analyze pagination on nested endpoints
5. Create URL pattern templates

### Phase 3: Upstream Navigation Testing Analysis (TBD minutes)

**Objective:** Analyze sub-resource navigation testing in upstream

**Tasks:**

1. Identify sub-resource tests in upstream
2. Extract navigation test patterns
3. Document nested endpoint mocking approaches
4. Identify edge case coverage
5. Extract best practices

### Phase 4: Test Scenario Design (TBD minutes)

**Objective:** Design test scenarios for sub-resource navigation

**Tasks:**

1. Design parent-to-child navigation test scenarios
2. Design child-to-parent navigation test scenarios
3. Design nested query parameter test scenarios
4. Design nested pagination test scenarios
5. Design nested filtering test scenarios
6. Design invalid path test scenarios
7. Document scenario matrix

### Phase 5: Bidirectional Navigation Analysis (TBD minutes)

**Objective:** Analyze bidirectional navigation requirements

**Tasks:**

1. Identify all bidirectional navigation paths
2. Document link relations for reverse navigation
3. Design bidirectional test scenarios
4. Document navigation consistency requirements

### Phase 6: Synthesis (TBD minutes)

**Objective:** Create comprehensive sub-resource navigation testing strategy

**Tasks:**

1. Consolidate navigation scenarios
2. Create navigation test templates
3. Document fixture requirements
4. Estimate test implementation effort
5. Create deliverable document

---

## 6. Success Criteria

This research is complete when:

- [ ] All CSAPI sub-resource patterns are inventoried
- [ ] URL structure for nested endpoints is documented
- [ ] Bidirectional navigation patterns are defined
- [ ] Query parameters on nested endpoints are specified
- [ ] Pagination on nested endpoints is defined
- [ ] Invalid path scenarios are documented
- [ ] Navigation test patterns are complete
- [ ] Deliverable document is peer-reviewed

---

## 7. Deliverable

**Sub-resource navigation testing strategy covering all nested patterns**

Content includes:

- Complete sub-resource pattern inventory
- Parent-child relationship matrix
- URL structure templates for nested endpoints
- Parent-to-child navigation test patterns
- Child-to-parent navigation test patterns (bidirectional)
- Query parameter test patterns on nested endpoints
- Pagination test patterns on nested endpoints
- Filtering test patterns on nested resources
- Invalid path test scenarios
- Link relation usage for navigation
- Navigation consistency tests
- Fixture requirements for nested resources
- Implementation estimates

**Example Nested Patterns:**

- `/systems/{id}/datastreams`
- `/datastreams/{id}/observations`
- `/systems/{id}/deployments`
- `/samplingFeatures/{id}/observations`
- `/procedures/{id}/systems`

---

## 8. Dependencies

**Must Complete Before Starting:**

- Section 8: CSAPI Specification Review (resource relationships)
- Section 13: Resource Method Testing Patterns (navigation methods)
- Section 23: Pagination Testing Strategy (pagination on nested endpoints)
- Section 24: Query Parameter Combination Testing (parameters on nested endpoints)

**Blocks:**

- Sub-resource navigation implementation
- Nested endpoint implementation
- ROADMAP Phase 2 implementation

---

## 9. Research Status Checklist

- [x] Phase 1: Sub-Resource Pattern Inventory - Complete (1.0 hour)
- [x] Phase 2: URL Structure Analysis - Complete (0.5 hours)
- [x] Phase 3: Upstream Navigation Testing Analysis - Complete (0.5 hours)
- [x] Phase 4: Test Scenario Design - Complete (1.0 hour)
- [x] Phase 5: Bidirectional Navigation Analysis - Complete (0.25 hours)
- [x] Phase 6: Synthesis - Complete (0.75 hours)
- [x] Deliverable document created and reviewed
- [ ] Cross-references updated in related documents

**Completion Date:** February 6, 2026

**Total Time:** 3.5 hours (research), 40-52 hours estimated for implementation

---

## 10. Notes and Key Findings

**Key Findings from Research:**

**16 Relationship Patterns Identified:**

1. Systems → Subsystems (hierarchical, unlimited depth, recursive)
2. Deployments → Subdeployments (hierarchical, unlimited depth, recursive)
3. Systems → SamplingFeatures (compositional, depth 1)
4. Systems → DataStreams (compositional cross-part, depth 1)
5. Systems → ControlStreams (compositional cross-part, depth 1)
6. Systems → SystemEvents (compositional cross-part, depth 1)
7. Systems → Deployments (associative, bidirectional)
8. Collections → Items (compositional, depth 1)
9. DataStreams → Observations (compositional, depth 1)
10. ControlStreams → Commands (compositional, depth 1)
11. ControlStreams → Feasibility (compositional, depth 1)
12. Commands → Status (compositional, depth 1)
13. Commands → Result (compositional, depth 1)
14. Feasibility → Status (compositional, depth 1)
15. Feasibility → Result (compositional, depth 1)
16. Deployments → Systems (associative reverse via query parameter)

**3 Relationship Types:**

- **Hierarchical (2):** Subsystems, Subdeployments - unlimited depth with recursive parameter
- **Compositional (12):** Parent owns child, depth 1, no recursive
- **Associative (2):** Many-to-many, bidirectional navigation

**URL Pattern Structure:**

- Collection: `/{parent}/{parentId}/{children}`
- Single resource: `/{parent}/{parentId}/{children}/{childId}`
- Canonical equivalence: Nested URL = Canonical URL (same resource)

**Query Parameter Inheritance:**

- All nested endpoints support pagination (limit, offset)
- Spatial endpoints support bbox, datetime
- Observation endpoints support phenomenonTime, resultTime
- Command endpoints support executionTime, issueTime
- Hierarchical endpoints support recursive parameter

**Pagination Patterns:**

- Offset-based for Part 1 (limit 10-100 typical)
- Offset or cursor-based for Part 2 (limit up to 10000)
- Cursor-based recommended for large datasets (millions of observations)

**Bidirectional Navigation:**

- Forward: Dedicated nested endpoint (`/systems/{id}/deployments`)
- Reverse: Query parameter on collection (`/deployments?system={id}`)
- Both directions return consistent results

**60 Test Scenarios Designed:**

- 10 hierarchical navigation tests (recursive)
- 25 compositional navigation tests
- 5 associative navigation tests
- 5 nested query parameter tests
- 3 nested pagination tests
- 2 bidirectional navigation tests
- 10 invalid path/error handling tests

**50 Fixtures Designed:**

- 16 nested collection responses
- 5 empty collection responses
- 10 paginated responses
- 8 single nested resource responses
- 5 error responses
- 4 bidirectional navigation responses
- 2 recursive hierarchy responses

**Implementation Estimates:**

- URL Builder: 13-17 hours
- Test Implementation: 19-24 hours
- Fixture Creation: 6-8 hours
- **Total: 40-52 hours**

**Key Design Decisions:**

- Generic nested URL builder pattern (reusable across all relationships)
- Parameter validation (reject invalid parameters for resource type)
- URL equivalence guarantee (nested = canonical)
- Location header always uses canonical URL after creation
- TypeScript types prevent invalid relationship access at compile time

---

**Next Steps:**

1. Implement generic nested URL builder (~13-17 hours)
2. Implement hierarchical navigation methods (~2 hours)
3. Implement compositional navigation methods (~6-7 hours)
4. Implement test scenarios (~19-24 hours)
5. Create fixtures (~6-8 hours)
6. Update Section 19 with navigation test organization
