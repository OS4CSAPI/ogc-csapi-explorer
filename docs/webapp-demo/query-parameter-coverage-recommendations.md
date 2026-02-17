# Query Parameter Coverage — Recommendations

> **Date**: 2026-02-17  
> **Context**: Actionable follow-up to the [Query Parameter Demonstration Coverage](query-parameter-demonstration-coverage.md) audit, which found the demo app exercises 3 of 5 filter categories (spatial, temporal, property-based partial) and does not exercise hierarchical or relationship-based query filters.  
> **Goal**: Close the coverage gaps so the demo app can credibly demonstrate the contribution-goal claim: *"Complete query parameter support (spatial, temporal, hierarchical, relationship-based, property-based filters)."*

---

## Coverage Gap Summary

| Filter Category | Current Status | Gap |
|---|---|---|
| **Spatial** | Demonstrated | — |
| **Temporal** | Mostly demonstrated | `resultTime`, `executionTime` not exercised |
| **Hierarchical** | Not demonstrated | `parent`, `recursive`, subsystem/subdeployment methods unused |
| **Relationship-based** | Not demonstrated | `systemId`, `procedureId`, `foiId`, `observedPropertyId`, `controlledPropertyId` unused as list filters |
| **Property-based** | Partial | `currentStatus`, `id`, `uid`, `sortBy`, `sortOrder`, `f`, `crs` unused |

---

## Recommendations

### Recommendation 1 — Replace Manual URL Construction with Builder Methods

**Priority**: 1 (Highest)  
**Effort**: Low  
**Category**: Code quality + relationship-based coverage  

**Problem**: `MapViewPage.vue` constructs 3 nested-resource URLs by hand (e.g., `` `/datastreams/${id}/observations?limit=1` ``), bypassing the `CSAPIQueryBuilder` entirely. This means the demo cannot claim those builder methods are tested against a live server.

**Proposed Change**: Replace the manual `fetch()` calls with the corresponding builder methods:

| Current (manual) | Replacement (builder) |
|---|---|
| `/datastreams/{id}/observations?limit=1` | `builder.getDataStreamObservations(id).limit(1)` |
| `/systems/{sysId}/samplingFeatures?limit=100` | `builder.getSystemSamplingFeatures(sysId).limit(100)` |
| `/datastreams/{id}/observations?limit=500` | `builder.getDataStreamObservations(id).limit(500)` |

**Signal value**: Demonstrates `getDataStreamObservations()` and `getSystemSamplingFeatures()` — two relationship methods currently listed as "Not Demonstrated" in the coverage audit. Eliminates a code smell (hardcoded URLs). Zero UI change required.

**Acceptance criteria**:
- All 3 manual URL constructions in `MapViewPage.vue` replaced with builder method calls via `csapi-bridge.ts`
- Map view continues to function identically (observation tracks, sampling features, system locations)
- No new dependencies or UI components needed

---

### Recommendation 2 — Add "Filter by System" Dropdown on Datastreams List

**Priority**: 2  
**Effort**: Medium  
**Category**: Relationship-based filter coverage  

**Problem**: The `ResourceList.vue` component never passes `systemId` (or any relationship filter) as a query parameter when listing datastreams, control streams, observations, or commands. The builder's `QueryOptions` interfaces support these filters but the demo never exercises them.

**Proposed Change**: Add a dropdown (PrimeVue `Select` component) to the datastreams list page that:
1. Fetches the list of systems from the server (already available via `getSystems()`)
2. Lets the user select one system
3. Passes `systemId` to the datastreams query via `QueryOptions`
4. Re-fetches the filtered list

**Signal value**: Proves `systemId` works as a relationship filter against the live server. This is the single most natural relationship query — "show me datastreams belonging to this system" — and the one most likely to be used in a real application.

**Acceptance criteria**:
- System dropdown appears above the datastreams list
- Selecting a system re-fetches datastreams filtered by `systemId`
- Clearing the dropdown returns to the unfiltered list
- Works against OSH SensorHub

---

### Recommendation 3 — Add `currentStatus` Filter Dropdown on Commands List

**Priority**: 3  
**Effort**: Low  
**Category**: Property-based filter coverage  

**Problem**: `currentStatus` is a string-enum filter available on commands (and potentially systems), but the demo never uses it. This is the simplest property-based filter to add — it has a known set of values defined in the CSAPI spec.

**Proposed Change**: Add a dropdown to the commands list with CSAPI-defined status values (e.g., `completed`, `failed`, `rejected`, `accepted`, `executing`). When selected, pass `currentStatus` into the query options.

**Signal value**: Proves a non-temporal, non-spatial, non-free-text property filter works. Low risk because the UI control is simple and the parameter is well-defined by the spec.

**Acceptance criteria**:
- Dropdown appears above the commands list with CSAPI status values
- Selecting a status re-fetches commands filtered by `currentStatus`
- Clearing the dropdown returns to the unfiltered list
- Behavior is verified against OSH SensorHub (may return empty for some statuses — that's fine)

---

### Recommendation 4 — Investigate OSH SensorHub for Hierarchical System Data

**Priority**: 4  
**Effort**: Low (research only)  
**Category**: Hierarchical filter coverage — prerequisite  

**Problem**: The demo has no mechanism for demonstrating `parent` or `recursive` query parameters. Before building UI for those filters, we need to determine whether the OSH SensorHub test server actually has hierarchical data (systems with subsystems, or deployments with subdeployments).

**Proposed Investigation**:
1. Query `GET /systems?parent=true` and `GET /systems?recursive=true` to see if the server supports these parameters
2. Query `GET /systems/{id}/subsystems` for each of the 18 known systems to find any that have children
3. Query `GET /deployments/{id}/subdeployments` similarly
4. Document findings: which systems (if any) have hierarchical relationships, and whether the server returns HTTP 200 or errors for `parent`/`recursive` params

**Signal value**: Determines feasibility of Recommendation 5. If no hierarchical data exists on the test server, it may be necessary to create test data or document the limitation.

**Acceptance criteria**:
- Investigation report documenting:
  - Whether `parent`/`recursive` query parameters are accepted by OSH SensorHub
  - Which systems/deployments (if any) have subsystems/subdeployments
  - Whether creating hierarchical test data is possible via the CRUD API
- Report placed in `docs/webapp-demo/` (or added to an existing document)

---

### Recommendation 5 — Add `parent`/`recursive` Filter UI for Hierarchical Navigation

**Priority**: 5  
**Effort**: Medium  
**Category**: Hierarchical filter coverage  
**Depends on**: Recommendation 4 (only proceed if hierarchical data exists or can be created)

**Problem**: `parent` and `recursive` are the two query parameters that enable hierarchical navigation — "show me only top-level systems" (`parent=none`), "show me all systems recursively" (`recursive=true`). The demo never sets them.

**Proposed Change**: Add toggle controls to the systems list:
1. A "Top-level only" toggle → sets `parent=none` on the query
2. A "Show all (recursive)" toggle → sets `recursive=true`
3. Optionally, a "Children of…" dropdown → sets `parent={selectedId}`

**Signal value**: Demonstrates hierarchical query support, completing the 5th and final filter category. Combined with the other recommendations, this would give the demo credible coverage of all 5 filter categories claimed in the contribution goal.

**Acceptance criteria**:
- Toggle/dropdown controls appear on the systems list
- "Top-level only" correctly filters to root-level systems
- "Show all (recursive)" returns all systems including nested ones
- "Children of…" shows only direct children of a selected system
- Works against OSH SensorHub (or documented as blocked if no hierarchical data exists)

---

## Priority Matrix

| # | Recommendation | Effort | Signal | Risk | Categories Closed |
|---|---|---|---|---|---|
| 1 | Replace manual URLs | Low | Medium | Very Low | Partial relationship |
| 2 | systemId dropdown | Medium | High | Low | Relationship-based |
| 3 | currentStatus dropdown | Low | Medium | Low | Property-based |
| 4 | Investigate hierarchical | Low | N/A (prereq) | None | — |
| 5 | parent/recursive UI | Medium | High | Medium | Hierarchical |

**If only one recommendation is implemented**, Recommendation 2 (systemId dropdown) provides the highest signal value for the least risk.

**If two are implemented**, Recommendations 1 + 2 together close the relationship-based gap and improve code quality.

**All five recommendations** together would give the demo app credible coverage of all 5 filter categories in the contribution-goal claim.

---

## References

- [Query Parameter Demonstration Coverage](query-parameter-demonstration-coverage.md) — the audit this document follows up on
- [Contribution Goal Accuracy Assessment](contribution-goal-accuracy-assessment.md) — the broader claim assessment
- [Commands Nested Resource Analysis](commands-nested-resource-analysis.md) — related analysis of nested URL construction
- [CSAPIQueryBuilder source](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/src/ogc-api/csapi-query-builder.ts) — the builder methods to be exercised
- [QueryOptions interfaces](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/src/ogc-api/csapi-query-builder.ts) — filter parameter types
