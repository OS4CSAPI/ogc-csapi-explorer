# Section 16: Worker Extensions Testing Strategy - Research Plan

> **🚫 OUT OF SCOPE (February 2026):** Worker extensions have been removed from the CSAPI contribution scope entirely. No upstream JSON-based API uses Web Workers. This research plan is retained as reference material only. See ROADMAP v3.1 and Guide §8.

**Status:** ✅ COMPLETE  
**Last Updated:** February 6, 2026  
**Research Time:** 2.5 hours (Estimated: 3-4 hours)  
**Test Implementation Lines:** 2,310-2,860 lines (201 test scenarios)

---

## 1. Research Objective

Define testing strategy for the 9 Web Worker message types and background processing.

**Why Sixteenth:** Worker testing has unique challenges (async, message passing, fallback behavior). Address after core testing patterns established.

---

## 2. Research Questions

### Core Questions

1. How to test Worker message types in Jest?
2. How to test async parsing operations?
3. How to test fallback for non-worker environments?
4. What fixtures needed for heavy parsing operations?
5. How to test performance characteristics?
6. What integration tests needed with parsers?

### Detailed Questions

- What are the 9 Web Worker message types?
- How to mock Worker message passing in tests?
- How to test Worker initialization and termination?
- What error scenarios exist in Worker communication?
- How to test Worker thread isolation?
- How to validate parsing results from Workers?
- What timeout/performance thresholds to test?
- How to test Worker fallback to main thread?

---

## 3. Primary Resources

- **Implementation Guide**: [docs/planning/csapi-implementation-guide.md](../../../planning/csapi-implementation-guide.md) (Worker Extensions section)
- **ROADMAP**: [docs/planning/ROADMAP.md](../../../planning/ROADMAP.md) (Phase 4: Task 1 - Worker Extensions)

## 4. Supporting Resources

- Existing worker tests in camptocamp/ogc-client
- Web Workers API documentation
- Jest testing documentation for Workers
- Section 9 deliverable (SensorML parser testing patterns)
- Section 10 deliverable (SWE Common parser testing patterns)
- Section 11 deliverable (GeoJSON parser testing patterns)

---

## 5. Research Methodology

### Phase 1: Worker Architecture Analysis ✅ (45 minutes)

**Objective:** Understand Worker implementation architecture and message types

**Tasks:**

1. ✅ Document all 9 Web Worker message types from Implementation Guide
2. ✅ Map message types to parser operations
3. ✅ Analyze Worker initialization and lifecycle
4. ✅ Identify fallback behavior requirements
5. ✅ Document Worker architecture patterns

**Findings:**

- Existing 4 message types: parseWmsCapabilities, parseWfsCapabilities, queryWfsFeatureTypeDetails, parseWmtsCapabilities
- Request/response protocol via `WorkerRequest`/`WorkerResponse` with unique requestId
- Fallback mechanism uses EventTarget for non-worker environments
- `sendTaskRequest()` returns Promise, `addTaskHandler()` registers handlers

### Phase 2: Upstream Worker Test Analysis ✅ (30 minutes)

**Objective:** Analyze existing Worker test patterns in camptocamp/ogc-client

**Tasks:**

1. ✅ Locate Worker-related tests in upstream codebase
2. ✅ Analyze Worker mocking approaches
3. ✅ Document test structure patterns
4. ✅ Identify reusable test utilities
5. ✅ Extract best practices

**Findings:**

- Existing test: `src/worker-fallback/worker-fallback.spec.ts` (WMS/WFS endpoints)
- Pattern: Use `enableFallbackWithoutWorker()` for testing without real worker
- Tests actual handler code via fallback mechanism (no worker mocking needed)
- Cache mocked to avoid persistence: `jest.mock('../shared/cache')`

### Phase 3: Jest Worker Testing Patterns ✅ (20 minutes)

**Objective:** Understand Jest capabilities for Worker testing

**Tasks:**

1. ✅ Research Jest Worker testing documentation
2. ✅ Identify Worker mocking strategies
3. ✅ Analyze async message passing test patterns
4. ✅ Document test isolation approaches
5. ✅ Identify performance testing capabilities

**Findings:**

- **Strategy 1 (Recommended):** Fallback mode testing with `enableFallbackWithoutWorker()`
- **Strategy 2:** Mock Worker `postMessage`/`addEventListener` for message passing tests
- **Strategy 3:** Real worker with worker_threads polyfill (performance testing)
- Async tests use async/await with `expect().rejects.toThrow()` for errors
- Performance tests use `performance.now()` for timing

### Phase 4: Test Scenario Design ✅ (60 minutes)

**Objective:** Design test scenarios for all Worker operations

**Tasks:**

1. ✅ Define test scenarios for each of 9 message types
2. ✅ Design async operation test patterns
3. ✅ Define fallback behavior test scenarios
4. ✅ Design performance/timeout test scenarios
5. ✅ Define error handling test scenarios
6. ✅ Document fixture requirements for heavy parsing

**Findings:**

- **Total test scenarios:** 201 (139 message type unit tests + 62 integration tests)
- **Per message type:** 10-23 scenarios (happy path, error, performance)
- **Integration tests:** Parser integration (12), fallback (9), concurrent (6), error (15), performance (20)
- **Fixture requirements:** 10 new worker-specific fixtures, leverage existing from Sections 9-11
- **Performance thresholds:** Defined per operation type and input size

### Phase 5: Synthesis ✅ (45 minutes)

**Objective:** Create comprehensive Worker testing strategy

**Tasks:**

1. ✅ Consolidate test patterns per message type
2. ✅ Create Worker test structure templates
3. ✅ Document mocking and assertion patterns
4. ✅ Estimate test implementation effort
5. ✅ Create deliverable document

**Deliverables:**

- Complete test strategy document (15 sections, ~11,000 lines)
- Test scenarios for all 9 message types (detailed specifications)
- Jest testing patterns (3 strategies with examples)
- Integration test patterns (parser, fallback, concurrent, error, performance)
- Test organization structure (13 new test files)
- Implementation estimates: 47-61 hours test implementation, 22.5-31.5 hours worker implementation

---

## 6. Success Criteria ✅

This research is complete when:

- ✅ All 9 Worker message types have test scenarios
- ✅ Jest Worker testing approach is validated
- ✅ Async message passing test patterns are documented
- ✅ Fallback behavior test strategy is defined
- ✅ Performance testing approach is documented
- ✅ Worker test structure templates are ready
- ✅ Deliverable document is peer-reviewed

---

## 7. Deliverable

**Worker testing strategy with message type test specifications**

Content includes:

- Test scenarios for all 9 Worker message types
- Jest Worker testing patterns and utilities
- Async message passing test templates
- Fallback behavior test scenarios
- Performance testing approach
- Worker-specific fixture requirements
- Integration test patterns with parsers
- Implementation estimates

---

## 8. Dependencies

**Must Complete Before Starting:**

- Section 1: Upstream Blueprint Analysis (general test patterns)
- Section 2: Existing Upstream Test Pattern Survey (Worker test patterns)
- Section 9: SensorML 3.0 Format Testing Requirements (parser integration)
- Section 10: SWE Common 3.0 Format Testing Requirements (parser integration)
- Section 11: GeoJSON CSAPI Extensions Testing Requirements (parser integration)

**Blocks:**

- Section 19: Test Organization and File Structure (Worker test organization)
- Phase 4 implementation (Worker Extensions cannot be implemented without test strategy)

---

## 9. Research Status Checklist ✅

- ✅ Phase 1: Worker Architecture Analysis - Complete (45 minutes)
- ✅ Phase 2: Upstream Worker Test Analysis - Complete (30 minutes)
- ✅ Phase 3: Jest Worker Testing Patterns - Complete (20 minutes)
- ✅ Phase 4: Test Scenario Design - Complete (60 minutes)
- ✅ Phase 5: Synthesis - Complete (45 minutes)
- ✅ Deliverable document created and reviewed
- ✅ Cross-references updated in related documents

**Total Research Time:** 2.5 hours (200 minutes)  
**Completion Date:** February 6, 2026

---

## 10. Notes and Open Questions

<!-- Add notes and unresolved questions here as research progresses -->

**Initial Observations:**

- Implementation Guide Phase 4, Task 1 mentions Worker Extensions
- 9 Web Worker message types listed in Implementation Guide
- Need to verify Jest's capabilities for Worker testing
- Worker fallback is critical for browser compatibility

**Research Findings:**

- ✅ All 9 message types cataloged with detailed specifications
- ✅ Jest fallback testing strategy validated (existing pattern works)
- ✅ Worker testing does NOT require complex mocking (use fallback mode)
- ✅ Parser integration tests can reuse fixtures from Sections 9-11
- ✅ Performance testing straightforward with `performance.now()`
- ✅ Concurrent request testing uses Promise.all() pattern

**Key Insights:**

1. **Fallback Mode is Ideal:** Testing via fallback mode is simpler and more reliable than mocking workers
2. **Fixture Reuse:** Most fixtures already exist from parser testing sections (only 10 new fixtures needed)
3. **Test Volume:** 201 test scenarios across 13 test files (~2,310-2,860 lines)
4. **Implementation Effort:** 47-61 hours for test implementation, 22.5-31.5 hours for worker code
5. **Critical Priorities:** Format parsing workers (PARSE_SENSORML_3, PARSE_SWE_RESULT, PARSE_SWE_BINARY) are highest priority

**Open Questions (Implementation Phase):**

- ❓ Should performance tests run in CI or only locally?
- ❓ What's the optimal worker pool size for concurrent requests?
- ❓ Should large fixtures (10,000 observations) be generated programmatically or committed?

---

**Next Steps:** ROADMAP Phase 4 - Implement worker extensions and tests per this strategy.
