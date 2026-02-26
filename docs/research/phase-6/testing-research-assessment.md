# Phase 6: Testing Research Assessment

**Date:** February 24, 2026  
**Status:** No new testing research required

---

## Question

Does Phase 6 require a dedicated testing research effort — similar to the 38-plan arc completed for Phases 1–5 — before proceeding with implementation?

---

## Answer

**No.** The existing 38-plan testing research arc fully covers every Phase 6 testing decision. The evidence is detailed below.

---

## Phase 6 Testing Surface

Phase 6 creates **exactly 2 new tests** in 1 new file. The full testing scope:

| Action                     | Count    | Details                                                       |
| -------------------------- | -------- | ------------------------------------------------------------- |
| New tests created          | 2        | `factory.spec.ts`: builder creation + error case              |
| Tests migrated             | 2        | From `endpoint.spec.ts` to `factory.spec.ts` (rewritten)      |
| Tests removed              | 1        | Obsolete caching test (behavior no longer exists)             |
| Tests preserved            | 3        | `hasConnectedSystems`, `csapiCollections`, non-CSAPI endpoint |
| Regression baseline        | 1,282    | All existing tests must still pass                            |
| ESLint fixes to test files | 15 files | Remove unused imports — zero logic changes                    |

Compare to Phases 1–5: ~6,000 lines of new test code across 29 suites testing URL building (80 methods), format parsing (SensorML, SWE Common, GeoJSON), integration workflows, command lifecycles, temporal queries, spatial filtering, and error conditions. **That** required 38 research plans because those were entirely new behavioral domains.

Phase 6 creates no new behavioral domain. It moves existing behavior from one location to another.

---

## Research Traceability

Every Phase 6 testing decision maps to a specific existing research plan:

| Testing Decision                                          | Research Source                                                                                                                                                                              | What It Covers                                                                                                                                                       |
| --------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Factory test pattern (create builder + verify properties) | [Plan 01: EDR Blueprint](../testing/findings/01-edr-test-blueprint.md), lines ~437–475                                                                                                       | Direct analog: `endpoint.edr('collection-id')` → assert builder, validate properties. Near-exact structural match to `createCSAPIBuilder(endpoint, 'collection-id')` |
| Error case test (non-CSAPI throws `EndpointError`)        | [Plan 14: Integration Test Workflow](../testing/findings/14-integration-test-workflow-design.md), Test 5                                                                                     | "Throws Error for Non-CSAPI Collection" — exact pattern specified                                                                                                    |
| Test file location (`factory.spec.ts` colocated)          | [Plan 19: Test Organization](../testing/findings/19-test-organization-file-structure.md)                                                                                                     | Colocated `.spec.ts` next to implementation, flat directory structure                                                                                                |
| Fixture reuse (same mock fetch as endpoint tests)         | [Plan 15: Fixture Sourcing](../testing/findings/15-fixture-sourcing-organization.md)                                                                                                         | Fixtures shared across test files via `setupMockFetch()`                                                                                                             |
| Quality bar (meaningful assertions, not trivial)          | [Plan 06: Meaningful vs Trivial](../testing/findings/06-meaningful-vs-trivial-definition.md) + [Plan 36: Quality Checklist](../testing/findings/36-test-quality-checklist-review-process.md) | Complete validation, behavior assertions, specific error messages                                                                                                    |
| Endpoint mocking in factory tests                         | [Plan 34: Test Utility Helpers](../testing/findings/34-test-utility-helper-design.md)                                                                                                        | `setupMockFetch()`, `createTestEndpoint()` patterns documented                                                                                                       |
| Removing obsolete caching test                            | [Plan 37: Test Maintenance](../testing/findings/37-test-maintenance-evolution-strategy.md)                                                                                                   | "Remove tests when the feature they test has been removed"                                                                                                           |
| `hasConnectedSystems` stays tested on endpoint            | [Plan 22: Conformance Testing](../testing/findings/22-conformance-capability-testing.md)                                                                                                     | 8+ server capability profiles with fixture JSON for conformance detection                                                                                            |

**8 out of 8 decisions covered. Zero gaps.**

---

## EDR Analog — The Direct Precedent

The factory function test pattern has a near-exact analog in the EDR blueprint (Plan 01):

| Aspect        | EDR (existing precedent)                 | CSAPI Phase 6                                       |
| ------------- | ---------------------------------------- | --------------------------------------------------- |
| Factory call  | `await endpoint.edr('reservoir-api')`    | `await createCSAPIBuilder(endpoint, 'iot-sensors')` |
| Returns       | `EDRQueryBuilder` instance               | `CSAPIQueryBuilder` instance                        |
| Assertion     | Verify builder properties populated      | Verify `availableResources` populated               |
| Error case    | Collection not found / not EDR           | Endpoint not CSAPI → `EndpointError`                |
| Caching test  | `builder1 === builder2` (same reference) | Removed (no auto-caching in factory)                |
| Test location | `endpoint.spec.ts`                       | `factory.spec.ts` (colocated with factory)          |

The only structural difference is location — Phase 6 puts the factory tests in a dedicated colocated file rather than inside `endpoint.spec.ts`. This is fully supported by Plan 19's flat colocated file pattern.

---

## Why Phases 1–5 Needed 38 Plans But Phase 6 Does Not

| Aspect                     | Phases 1–5                                                                                                                                              | Phase 6                                   |
| -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------- |
| New test code              | ~6,000 lines across 29 suites                                                                                                                           | ~30 lines in 1 file                       |
| Behavioral domains         | URL building, format parsing, SensorML, SWE Common, GeoJSON, temporal queries, spatial filtering, command lifecycles, bulk operations, error conditions | Factory function (1 pattern, 1 analog)    |
| Novel patterns             | Many — no upstream precedent for most CSAPI-specific patterns                                                                                           | Zero — direct EDR blueprint analog exists |
| Testing strategy questions | 285+ across 38 plans                                                                                                                                    | 0 open                                    |
| Risk of getting it wrong   | High — 6,000 lines of tests could be trivial or wrong                                                                                                   | Low — 2 tests following a proven pattern  |

---

## Conclusion

The 38-plan testing research arc was essential for Phases 1–5 because those phases created thousands of lines of new behavioral code in domains with no upstream precedent. Phase 6 creates 2 tests that follow a pattern documented in the very first research plan. No new testing research is needed. The existing research is sufficient, and every decision has been traced to a specific source.
