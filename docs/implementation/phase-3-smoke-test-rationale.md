# Phase 3 Smoke Test Rationale

**Date:** 2026-02-14  
**Context:** Decision to continue live server smoke testing into Phase 3

---

## Question

Phase 2 smoke tests (against OpenSensorHub and Gnosis Earth demo servers) were valuable for validating URL builder output. Does it still make sense to run live smoke tests for Phase 3 format handler code? Is it even possible?

## Answer: Yes — and more valuable than in Phase 2

### Why Phase 3 smoke tests matter more

**Phase 2 smoke tests validated outputs we control.** The URL builder constructs URLs from known inputs — the code is deterministic. Smoke testing confirmed the servers _accept_ those URLs, which was useful but the risk was relatively low since we followed the spec closely.

**Phase 3 smoke tests validate handling of inputs we don't control.** Format handlers parse _real server responses_ — responses with real-world quirks, vocabulary choices, optional fields that may or may not be present, and encoding decisions that vary by server implementation. This is where surprises live.

### Evidence from Phase 2 smoke tests

The Phase 2.8 smoke test already revealed issues that directly shaped the GeoJSON handler:

| Finding        | What it taught us                                                                                                |
| -------------- | ---------------------------------------------------------------------------------------------------------------- |
| F4 (validTime) | Server sends `["ISO", "now"]` array, not a `TimeInterval` object — this became `parseValidTime`'s primary format |
| F10 (review)   | OpenSensorHub may use non-SOSA vocabularies for SamplingFeature featureTypes — our handler only recognizes SOSA  |

### What a GeoJSON handler smoke test can validate

1. **`isCSAPIFeature()`** — Does every real feature from the server return `true`? If not, we've found a vocabulary gap.
2. **`getCSAPIResourceType()`** — Does every System classify as `'System'`, every Deployment as `'Deployment'`, etc.? Do any return `null`?
3. **`validateCSAPIFeature()`** — Do real features pass validation? Do any produce unexpected errors (e.g., a real Procedure with non-null geometry)?
4. **`extractCSAPIFeature()`** — Does extraction succeed? Are `validTime`, `uid`, `name`, `description` all populated correctly from real data?
5. **`parseValidTime()`** — Does the real `validTime` format parse correctly on both servers?

### Feasibility

Straightforward to execute. Fetch JSON from the live endpoints (the same ones used in Phase 2 — Systems, Deployments, Procedures, SamplingFeatures), then pipe individual features through the GeoJSON handler functions. No special setup needed beyond `fetch` + function calls.

### Caveat for later Phase 3 components

Smoke tests for SensorML parser and SWE Common parser will require fetching `application/sml+json` and `application/swe+json` responses, which depends on those content types being available on the demo servers. For the GeoJSON handler, the same `application/geo+json` endpoints from Phase 2 provide perfect test data.

### Recommendation

Run a smoke test for the GeoJSON handler now, while the two demo servers are fresh in memory, before building subsequent Phase 3 components on top of it.
