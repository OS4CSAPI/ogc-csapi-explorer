# Phase 2 Implementation Overview

## The Big Picture

Phase 1 built the **plumbing** — the type system, helper utilities, a stub QueryBuilder with 2 proof-of-concept methods, and the integration with `OgcApiEndpoint`. Phase 2 took that foundation and **filled it in completely**: every resource type that the Connected Systems API defines now has full URL-building support.

By the end of Phase 2, you can construct the correct URL for **any** operation on **any** CSAPI resource — querying collections with filters, retrieving individual resources, creating/updating/deleting, navigating associations, fetching schemas, tracking command status — all with proper query parameter encoding and resource validation.

Phase 2 doesn't fetch or parse server responses. It produces _the right URL string_ for each operation. Phase 3 will add the response-handling layer that actually calls those URLs and turns the JSON into typed objects.

---

## What Was Built

### The Central Piece: `url_builder.ts` (1,863 lines)

The `CSAPIQueryBuilder` class grew from 2 methods to **79 public methods** across 9 resource types. Each resource type follows the same pattern:

1. **Collection query** — list resources with filters (`getSystems({ limit: 10, bbox: [...] })`)
2. **Single resource** — retrieve by ID (`getSystem('sys-001')`)
3. **CRUD** — create, update, delete URLs
4. **Associations** — navigate to related resources (`getSystemDataStreams('sys-001')`)
5. **Type-specific operations** — schemas, status, feasibility, cancel, etc.

Every method validates that the server actually supports the requested resource type before building the URL. If you call `getObservations()` on a server that doesn't have observations, you get a clear `EndpointError` — not a meaningless 404.

### The 9 Resource Types

| Resource Type        | Methods | What It Represents                                                                                                                                                                         |
| -------------------- | ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Systems**          | 12      | Physical things: sensors, platforms, vehicles, weather stations. The anchors that everything else connects to.                                                                             |
| **Deployments**      | 8       | When and where a system was deployed. A weather station might have been at Site A in 2023 and Site B in 2024.                                                                              |
| **Procedures**       | 8       | How a system operates — its methodology, calibration, processing steps. Multiple systems can share one procedure.                                                                          |
| **SamplingFeatures** | 8       | The real-world thing being measured — a river cross-section, a soil sample point, an air quality monitoring zone.                                                                          |
| **Properties**       | 6       | Observable properties like temperature, humidity, wind speed. Shared vocabulary across systems and datastreams.                                                                            |
| **DataStreams**      | 11      | A continuous flow of observations from a system. Links a system + procedure + sampling feature → observations. Has a schema describing the data format.                                    |
| **Observations**     | 8       | Individual measurement results within a datastream. The actual data: "42.3°C at 2024-01-15T12:00:00Z."                                                                                     |
| **ControlStreams**   | 8       | The control counterpart of DataStreams — channels for sending commands _to_ a system (e.g., "rotate camera 30° left"). Has a schema describing the command format.                         |
| **Commands**         | 10      | Instructions sent through a control stream. The control counterpart of Observations — data that flows _to_ systems rather than _from_ them. Includes status tracking and result retrieval. |

### How a Method Works (Example)

```typescript
// User writes:
const url = builder.getObservations({
  resultTime: 'latest',
  limit: 5,
  f: 'application/geo+json',
});

// Internally:
// 1. assertResourceAvailable('observations') — checks server supports it
// 2. buildResourceUrl('observations', undefined, undefined, options) — constructs:
//    "https://server.com/api/observations?resultTime=latest&limit=5&f=application%2Fgeo%2Bjson"
```

Every method follows this two-step pattern: **validate**, then **build**. The private `buildResourceUrl()` and `buildQueryString()` helpers handle all the URL construction, encoding, and temporal formatting. Public methods are thin wrappers that express _intent_.

### Query Parameter Support

The builder handles sophisticated filtering across all resource types:

| Parameter Category        | Examples                                   | Used By                                   |
| ------------------------- | ------------------------------------------ | ----------------------------------------- |
| **Pagination**            | `limit`, `offset`, `cursor`                | All resource types                        |
| **Keyword search**        | `q`                                        | All resource types                        |
| **ID filtering**          | `id` (single or array)                     | All resource types                        |
| **Format selection**      | `f` (media type)                           | All resource types                        |
| **Spatial filtering**     | `bbox` (bounding box)                      | Systems, SamplingFeatures, Observations   |
| **Temporal filtering**    | `datetime`, `phenomenonTime`, `resultTime` | DataStreams, Observations                 |
| **Temporal (Part 2)**     | `issueTime`, `executionTime`               | Commands                                  |
| **Status filtering**      | `currentStatus`                            | Commands                                  |
| **Association filtering** | `systemId`, `controlledPropertyId`         | ControlStreams                            |
| **Schema format**         | `obsFormat`, `cmdFormat` (via `f`)         | DataStream/ControlStream schema endpoints |

Temporal parameters are particularly nuanced — they support single instants, closed intervals, open-start, and open-end ranges, all properly ISO 8601 encoded.

---

## How It Was Built: The Development Cycle

Each of the 9 resource types followed a disciplined cycle:

```
Implement methods → Code review → Fix findings → Smoke test live servers → Backfill test gaps → Next resource type
```

This wasn't planned from the start — it **evolved** from lessons learned. The first few resource types (Systems, Deployments) had a less structured flow. By Phase 2.4 (SamplingFeatures), the cycle was formalized with reusable prompt templates for code reviews and smoke tests.

### The 9 Sub-Phases

| Sub-Phase | Issue         | Resource Type                       | Methods | New Tests | Cumulative Tests |
| --------- | ------------- | ----------------------------------- | ------- | --------- | ---------------- |
| 2.1       | #5            | Systems                             | 12      | 19        | 100              |
| 2.2       | #6, #34, #35  | Deployments + link convention fixes | 8       | 28        | 128              |
| 2.3       | #7            | Procedures                          | 8       | 20        | 156              |
| 2.4       | #8, #40       | SamplingFeatures + review backfill  | 8       | 30        | 186              |
| 2.5       | #9, #41       | Properties + review fixes           | 6       | 17        | 203              |
| 2.6       | #10, #42      | DataStreams + test backfill         | 11      | 39        | 242              |
| 2.7       | #11, #43, #44 | Observations + resultTime=latest    | 8       | 29        | 271              |
| 2.8       | #12, #45      | ControlStreams + test backfill      | 8       | 19        | 290              |
| 2.9       | #13, #46      | Commands + test backfill            | 10      | 24        | 314              |

### Bug Fixes Along the Way

Phase 2 wasn't just "add methods." Several issues arose from live server testing that required code or architecture fixes:

- **Issue #34** — OSH uses three different link relation conventions (`ogc-cs:systems`, plain `systems`, and `rel:"items"` with resource type in href). Our original code only recognized one. Fixed by expanding `extractAvailableResources()` to scan all three conventions.
- **Issue #35** — OSH serves resources at top-level paths (`/api/systems`) instead of collection-scoped paths (`/api/collections/iot/systems`). Added `extractRootResourceUrls()` and an optional `resourceUrls` map to the builder constructor.
- **Issue #38** — Code review found dead code, DRY violations, and weak test assertions from the first two resource types. Cleaned up in a focused fix commit.
- **Issue #40** — Accumulated code review findings: missing exports, weak temporal assertions, missing pagination test patterns. All resolved.
- **Issue #43** — Live testing found that `resultTime=latest` is accepted by OSH as a genuine filter. Added `'latest'` to the `TemporalFilterValue` type union.

---

## Live Server Testing

One of Phase 2's defining features was **testing against real servers after every resource type**. Two servers were used:

| Server                  | URL                                      | Auth            | What It Has                                                                                              |
| ----------------------- | ---------------------------------------- | --------------- | -------------------------------------------------------------------------------------------------------- |
| **OpenSensorHub (OSH)** | `http://45.55.99.236:8080/sensorhub/api` | Basic (ogc/ogc) | 12 systems, 100+ datastreams, 100+ observations, 8 control streams, 200+ commands. Heavy Part 2 support. |
| **52North**             | `https://csa.demo.52north.org/`          | None            | 3 systems, 1 deployment, 1 procedure. Part 1 only; Part 2 endpoints broken or missing.                   |

### 9 Smoke Tests, 39 Findings

Each smoke test ran raw HTTP calls against both servers, checked every new method's URL, and cataloged findings:

| Category                    | Count | Examples                                                                                             |
| --------------------------- | ----- | ---------------------------------------------------------------------------------------------------- |
| **Critical (fixed)**        | 2     | F1: link relation mismatch, F2: top-level vs collection-scoped URLs                                  |
| **Server limitations**      | 15    | OSH rejects various nested sub-resource endpoints (400), 52North DataStreams/Observations return 500 |
| **Informational / Phase 3** | 22    | `items` envelope, `@id` cross-references, schema duality, `validTime` arrays                         |

**Zero code bugs found across 9 consecutive smoke tests.** The 2 critical findings (F1, F2) were architectural discoveries from the very first smoke test — the URL construction patterns needed adjustment for how real servers work versus what we assumed from the spec alone. Once fixed, no further code bugs were found.

### The Most Important Discovery: F34

The final smoke test (Phase 2.9) revealed that OSH doesn't support `/commands` as a top-level resource — commands are only accessible via nested paths through their parent control stream (`/controlstreams/{csId}/commands`). This affects 8 of the 10 Commands methods and requires a fallback routing strategy in Phase 3. Tracked as Issue #47.

---

## Code Review Results

**8 code reviews** were performed (Phases 2.2 through 2.9), each following a standardized template:

| Metric                          | Result                    |
| ------------------------------- | ------------------------- |
| Code reviews performed          | 8                         |
| Consecutive zero-defect reviews | 7 (from Phase 2.3 onward) |
| Total review findings           | ~70 (across all reviews)  |
| Findings requiring code fixes   | 8 (all in Phases 2.2–2.5) |
| Positive/informational findings | ~62                       |

The reviews validated JSDoc quality, method signatures, test coverage heatmaps, and adherence to lessons learned. By Phase 2.6, the implementation had reached a steady state where each new resource type was clean on first implementation.

### Test Coverage Heatmap (Final State)

| Resource Type    | Coverage | Notes                                                            |
| ---------------- | -------- | ---------------------------------------------------------------- |
| Systems          | ~95%     | Comprehensive: all 12 methods, pagination, filtering, validation |
| Deployments      | ~90%     | All 8 methods, subdeployment navigation                          |
| Procedures       | ~90%     | All 8 methods, association queries                               |
| SamplingFeatures | ~92%     | All 8 methods, spatial filtering, bbox                           |
| Properties       | ~88%     | All 6 methods, association queries                               |
| DataStreams      | ~92%     | All 11 methods, schema retrieval, temporal filtering             |
| Observations     | ~90%     | All 8 methods, resultTime=latest, temporal                       |
| ControlStreams   | ~90%     | All 8 methods, schema, feasibility, commands sub-resource        |
| Commands         | ~92%     | All 10 methods, status, result, cancel, create validation        |

---

## Governance Process That Emerged

Phase 2 produced several governance artifacts that didn't exist at the start:

| Document                                                                          | Purpose                                                |
| --------------------------------------------------------------------------------- | ------------------------------------------------------ |
| [Code Review Prompt Template](../governance/code-review-prompt-template.md)       | Standardized AI-driven code review process             |
| [Smoke Test Prompt Template](../governance/smoke-test-prompt-template.md)         | Standardized live server testing process               |
| [Issue Creation Prompt Template](../governance/issue-creation-prompt-template.md) | Standardized GitHub issue format for scope containment |
| [AI Operational Constraints](../governance/AI_OPERATIONAL_CONSTRAINTS.md)         | Rules preventing AI scope creep                        |
| [Phase 2 Lessons Learned](../governance/phase-2-lessons-learned.md)               | 10 lessons (v1.2) from implementation experience       |

The **lessons learned** document was particularly valuable — it captured patterns like "test every method with exact `toBe` assertions" (Lesson 1), "test against both servers every time" (Lesson 8), and "smoke tests are read-only observation" (Lesson 10). These became enforced checkpoints in later sub-phases.

---

## By the Numbers

### Code

| File                   | Lines     | Purpose                                                 |
| ---------------------- | --------- | ------------------------------------------------------- |
| `url_builder.ts`       | 1,863     | 79 public methods, private helpers, resource validation |
| `url_builder.spec.ts`  | 2,118     | 314 tests across all 9 resource types                   |
| `model.ts`             | 560       | Type interfaces (unchanged from Phase 1)                |
| `helpers.ts`           | 191       | Utility functions (unchanged from Phase 1)              |
| **Total CSAPI source** | **2,614** |                                                         |
| **Total CSAPI tests**  | **2,763** |                                                         |

### GitHub Issues

| Issue     | Type          | Description                          |
| --------- | ------------- | ------------------------------------ |
| #5        | Feature       | Systems methods (12)                 |
| #6        | Feature       | Deployments methods (8)              |
| #7        | Feature       | Procedures methods (8)               |
| #8        | Feature       | SamplingFeatures methods (8)         |
| #9        | Feature       | Properties methods (6)               |
| #10       | Feature       | DataStreams methods (11)             |
| #11       | Feature       | Observations methods (8)             |
| #12       | Feature       | ControlStreams methods (8)           |
| #13       | Feature       | Commands methods (10)                |
| #34       | Fix           | Link relation convention support     |
| #35       | Fix           | Top-level resource URL support       |
| #38       | Fix           | Phase 2.2 code review findings       |
| #40       | Fix           | Accumulated review findings backfill |
| #41       | Fix           | Phase 2.5 code review findings       |
| #42       | Fix           | DataStreams test backfill            |
| #43       | Fix           | `resultTime=latest` type support     |
| #44       | Fix           | Observations test backfill           |
| #45       | Fix           | ControlStreams test backfill         |
| #46       | Fix           | Commands test backfill               |
| **Total** | **19 issues** | **9 features + 10 fixes**            |

### Documentation

| Category                      | Files  | Total Lines |
| ----------------------------- | ------ | ----------- |
| Smoke test reports            | 12     | ~5,600      |
| Code review reports           | 8      | ~4,000      |
| Sub-phase overviews           | 3      | ~400        |
| Cross-server analysis         | 1      | ~300        |
| Governance templates          | 3      | ~700        |
| Lessons learned               | 1      | ~220        |
| **Total implementation docs** | **28** | **~7,000**  |

### Commits

Phase 2 produced **~50 commits** over 9 sub-phases, from `1bb2230` (Issue #5, Systems methods) through `603894d` (roadmap v3.3 with F34-F39 notes).

---

## What Phase 2 Didn't Do

- **No HTTP fetching** — the builder returns URL strings, not data
- **No response parsing** — JSON-to-typed-object conversion is Phase 3
- **No SensorML/SWE Common parsing** — format handling is Phase 3
- **No error recovery** — fallback routing for Commands (F34) is Phase 3
- **No real-time subscriptions** — WebSocket/MQTT is out of scope

## What's Next: Phase 3

Phase 3 adds the **format handling layer** — the code that takes a server's JSON/SensorML/SWE response and turns it into the typed objects defined in Phase 1's `model.ts`. It includes:

- **GeoJSON handler extensions** — recognizing CSAPI-specific properties
- **SensorML 3.0 parsers** — parsing system description documents
- **SWE Common 3.0 parsers** — parsing observation/command data schemas and values
- **Validator extensions** — checking that responses conform to Part 1 and Part 2 rules
- **Fallback routing for Commands** (Issue #47) — handling servers that don't support top-level `/commands`

Phase 3 is estimated at 16-28 hours across 17 tasks. It's the most complex phase — but Phase 2's URL builder and live server testing give it a solid foundation of known-good URL patterns and cataloged server behaviors to work against.
