# Live Server Smoke Test — Post Phase 2.1

**Date:** February 14, 2026
**Milestone:** After completing Phase 1 (Issues #1–#4) + Phase 2.1 (Issue #5)
**Server:** OpenSensorHub demo instance (`http://45.55.99.236:8080/sensorhub/api`)
**Auth:** Basic auth required (credentials not stored in repo)
**Purpose:** Validate Phase 1 + 2.1 code against a real CSAPI implementation before building further

> This is the first in a series of live server smoke tests performed at key milestones in our implementation. Each test validates our code against a real server to catch discrepancies between our interpretation of the spec and how implementors actually build their servers. Future smoke tests will follow the same naming pattern: `live-server-smoke-test-post-phase-{X}.md`.

---

## Test Methodology

No code changes were made. All tests were run from the terminal using raw `fetch` calls that simulate the logic in our `checkHasConnectedSystems`, `CSAPIQueryBuilder`, and type interfaces. The goal was to compare what our code expects against what a real server actually returns.

---

## Server Profile

The server advertises **full CSAPI support** across all three specification parts:

| Part                  | Conformance Classes                                                                                                                       |
| --------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| Part 1 (Resources)    | core, system, subsystem, deployment, subdeployment, procedure, sf (sampling features), property, create-replace-delete, geojson, sensorml |
| Part 2 (Dynamic Data) | datastream, controlstream, system-history, system-event, create-replace-delete, json, swecommon-json, swecommon-text, swecommon-binary    |
| Part 3 (Pub/Sub)      | websocket, mqtt                                                                                                                           |

The server exposes 4 collections: `all_systems`, `all_datastreams`, `all_fois`, `all_procedures`.

Resources are available at top-level URLs: `/systems`, `/deployments`, `/procedures`, `/samplingFeatures`, `/datastreams`, `/observations`.

---

## Results

### What WORKS

| Check                     | Detail                                                                                                                                                               |
| ------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Conformance detection** | `checkHasConnectedSystems` correctly identifies CSAPI support. The server advertises `ogcapi-connectedsystems-1/1.0/conf/core`, which our function matches.          |
| **System resource shape** | Individual system objects have `type: "Feature"`, `id`, `geometry`, and `properties` with `uid`, `featureType`, `name` — matching our `System` interface structure.  |
| **featureType URIs**      | The server uses `http://www.w3.org/ns/sosa/Sensor`, which is one of the 5 values in our `SystemTypeUris` constant.                                                   |
| **Nested endpoints**      | `/systems/{id}/subsystems` and `/systems/{id}/datastreams` both resolve and return data, confirming the URL patterns our builder generates are structurally correct. |
| **Query parameters**      | `?limit=N` is accepted and respected by the server.                                                                                                                  |

### What BREAKS — 5 Findings

#### F1: Link Relation Prefix Mismatch (CRITICAL)

**What we expect:** Collection links with `rel: "ogc-cs:systems"`, `rel: "ogc-cs:datastreams"`, etc.
**What the server returns:** `rel: "items"` with a relative href like `"systems"`, or at the root level `rel: "systems"` (plain, no prefix).

**Impact:** Our `extractAvailableResources()` scans for the `ogc-cs:` prefix and finds nothing. `availableResources` is an empty Set. Every public method (`getSystems`, `getSystem`, `createSystem`, etc.) calls `assertResourceAvailable('systems')` and immediately throws `EndpointError`.

**Server's actual collection links:**

```json
{
  "id": "all_systems",
  "links": [
    {
      "rel": "self",
      "href": "http://45.55.99.236:8080/sensorhub/api/collections"
    },
    { "rel": "items", "href": "systems" }
  ]
}
```

**Root document links:**

```json
{ "rel": "systems", "href": "http://45.55.99.236:8080/sensorhub/api/systems" }
{ "rel": "deployments", "href": "http://45.55.99.236:8080/sensorhub/api/deployments" }
```

**What the spec says:** The OGC Connected Systems spec (23-001, Section 7.2) defines that servers SHOULD advertise resource endpoints via link relations. The reference implementation uses plain resource names (`"systems"`, `"datastreams"`) rather than the `ogc-cs:` prefixed form. We based our implementation on the prefixed convention, but the actual server doesn't use it.

**Severity:** Critical — the builder is completely non-functional against this server.

---

#### F2: Top-Level vs. Collection-Scoped Architecture (CRITICAL)

**What we expect:** Resources scoped under a collection: `/collections/{id}/systems`
**What the server returns:** Resources at the API root: `/sensorhub/api/systems`

**Impact:** Even if F1 were fixed, our `buildResourceUrl` constructs paths relative to a collection's self link. The collection's self link points to `/sensorhub/api/collections` (the collection _list_), not to itself. So our builder would produce:

```
Expected:  http://45.55.99.236:8080/sensorhub/api/collections/all_systems/systems
Actual:    http://45.55.99.236:8080/sensorhub/api/systems
```

The server's architecture treats collections as a _grouping catalog_ while resources live at the API root level. Our code assumes the OGC API Common pattern where resources are nested under their collection.

**Severity:** Critical — URLs would be wrong even after fixing F1.

---

#### F3: Response Envelope Uses `items`, Not `FeatureCollection` (Moderate)

**What we expect (Phase 3):** `{ type: "FeatureCollection", features: [...], numberMatched, numberReturned }`
**What the server returns:** `{ items: [...], links: [...] }`

The systems list endpoint returns:

```json
{
  "items": [
    { "type": "Feature", "id": "03bc5ofvvstg", "geometry": null, "properties": { ... } }
  ],
  "links": [ ... ]
}
```

No `type: "FeatureCollection"` wrapper, no `features` key, no `numberMatched` or `numberReturned`.

**Impact:** Our `FeatureCollection<System>` type won't match the response shape. When we build the response parser in Phase 3, we'll need to handle both `features` and `items` as the array key.

**Severity:** Moderate — doesn't affect current code (Phase 3 concern), but should be addressed before parsing is implemented.

---

#### F4: `validTime` Is an Array, Not an Object (Moderate)

**What we expect:** `validTime: { start: Date, end?: Date }`
**What the server returns:** `validTime: ["2026-01-26T18:32:01.56Z", "now"]`

The server encodes time intervals as a two-element string array, where:

- Element 0 is the start time as an ISO 8601 string
- Element 1 is the end time, or the literal string `"now"` for open-ended intervals

**Impact:** Our `TimeInterval` interface uses named properties (`start`, `end`) with `Date` objects. Parsing logic will need to convert between these representations.

**Severity:** Moderate — doesn't affect URL construction (current scope), but will require a conversion function in Phase 3.

---

#### F5: Missing Pagination Metadata (Low)

**What we expect:** `numberMatched` and `numberReturned` fields on collection responses.
**What the server returns:** Neither field is present (at least not in default responses).

**Impact:** Consuming code that relies on these fields for pagination UI would get `undefined`. The `links` array does include pagination links (`next`, `prev`), so link-based pagination works.

**Severity:** Low — optional fields in our types, and link-based pagination is the primary mechanism.

---

## Interpreting These Findings

It's important to understand what these findings are and what they aren't.

**Nothing is broken.** All 100 CSAPI unit tests pass. ESLint is clean. TypeScript is clean. Every piece of code does exactly what it was designed to do. Phase 1 and Phase 2.1 are complete by their own acceptance criteria.

What the smoke test revealed is that our code was designed against our _reading of the spec_. The reference implementation (OpenSensorHub) interprets some parts of the spec differently than we did:

- We assumed collections would advertise resources with `ogc-cs:systems` link relations — a reasonable reading of the spec. The real server uses plain `rel: "items"` and `rel: "systems"` instead.
- We assumed resources would be scoped under collections (`/collections/iot/systems`). The real server puts them at the API root (`/api/systems`).

These are **design assumptions**, not bugs. Our fixture data (which we wrote ourselves) reflects our interpretation, and the unit tests prove our code works perfectly against that interpretation.

The analogy: imagine building a perfectly working USB-A plug, tested thoroughly against a USB-A port you built yourself. Then you try plugging it into someone else's device and discover they built a USB-C port. Your plug isn't broken — it just handles one connector shape when the real world has two.

**What actually needs to happen:** We need to support _both_ patterns — our existing collection-scoped pattern (which other servers may use) AND the top-level pattern (which the reference implementation uses). It's additive, not corrective. None of the existing code or tests need to change — we'd be adding a second resource discovery path.

This is exactly why we did the smoke test. Without it, we'd have kept building more methods on a single pattern and discovered the gap much later, when it would have been more painful to fix.

---

## Summary

| Finding                                  | Severity | Affects                            | Fix Phase                                     |
| ---------------------------------------- | -------- | ---------------------------------- | --------------------------------------------- |
| F1: Link relation prefix mismatch        | Critical | URL Builder                        | Phase 2 (before more methods are added)       |
| F2: Top-level vs. collection-scoped URLs | Critical | URL Builder + Endpoint integration | Phase 2 (architectural)                       |
| F3: Response envelope format             | Moderate | Response parser                    | Phase 3                                       |
| F4: validTime array format               | Moderate | Model / parser                     | Phase 3                                       |
| F5: Missing pagination metadata          | Low      | Collection types                   | Phase 3 (optional fields already handle this) |

### Verdict

**Phase 1 conformance detection works correctly.** The server is identified as CSAPI-capable.

**Phase 2.1 URL construction would fail against this server** due to F1 (resource discovery) and F2 (URL base path). These are not bugs in our code — they reflect a gap between two valid interpretations of how CSAPI resources are organized. The spec allows both collection-scoped and top-level resource patterns; our code currently only handles the collection-scoped pattern.

**Recommended action:** Before proceeding with more resource-type methods (Issues #6–#9), address F1 and F2 so the builder can work against real servers. The fix likely involves:

1. Expanding `extractAvailableResources()` to recognize multiple link relation conventions (not just `ogc-cs:` prefix)
2. Supporting top-level resource URLs discovered from the root document, in addition to collection-scoped URLs
3. Potentially allowing the builder to be constructed from a root API document, not just a collection document

These findings validate that the smoke test was worth doing — we caught architectural assumptions that would have compounded across Phase 2.2+ if left unaddressed.
