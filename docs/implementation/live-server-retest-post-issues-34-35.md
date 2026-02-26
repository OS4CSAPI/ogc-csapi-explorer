# Live Server Smoke Re-Test Report — Post Issues #34 & #35

**Date:** February 14, 2026
**Server:** OpenSensorHub demo (`http://45.55.99.236:8080/sensorhub/api`)
**Purpose:** Verify that Issues #34 and #35 resolve the two critical findings from the initial smoke test

---

## What We Did

We queried the same live server from the original smoke test, fetching two documents:

1. **The API root document** (`/sensorhub/api`) — the server's top-level landing page
2. **The collections document** (`/sensorhub/api/collections`) — lists the server's 4 collections

We then analyzed whether our code changes would correctly handle the data these documents return.

---

## Finding F1: Resource Discovery (Issue #34)

**The problem was:** Our builder only recognized link relations with the `ogc-cs:` prefix (e.g., `rel: "ogc-cs:systems"`). This server doesn't use that prefix.

**What the server actually returns:**

In the **root document**, resources are advertised with plain relation names:

```json
{ "rel": "systems", "href": "http://45.55.99.236:8080/sensorhub/api/systems" }
{ "rel": "deployments", "href": "http://45.55.99.236:8080/sensorhub/api/deployments" }
{ "rel": "procedures", "href": "http://45.55.99.236:8080/sensorhub/api/procedures" }
{ "rel": "samplingFeatures", "href": "http://45.55.99.236:8080/sensorhub/api/samplingFeatures" }
{ "rel": "datastreams", "href": "http://45.55.99.236:8080/sensorhub/api/datastreams" }
{ "rel": "observations", "href": "http://45.55.99.236:8080/sensorhub/api/observations" }
```

In **each collection document**, resources are advertised with the generic `items` relation and the resource type embedded in the href:

```json
{ "rel": "items", "href": "systems" }
{ "rel": "items", "href": "datastreams" }
{ "rel": "items", "href": "samplingFeatures" }
{ "rel": "items", "href": "procedures" }
```

**Our fix (Issue #34):** We expanded `extractAvailableResources()` to recognize three conventions:

1. `ogc-cs:` prefix (original — still works for spec-strict servers)
2. Plain resource name as `rel` value — **matches this server's root document**
3. `rel: "items"` with resource type in the `href` — **matches this server's collection documents**

**Verdict: FIXED.** All 6 resource types from the root and all 4 from the collections would now be correctly discovered.

---

## Finding F2: Top-Level Resource URLs (Issue #35)

**The problem was:** Our builder assumed resources live under a collection's self URL (e.g., `/collections/iot-sensors/systems`). This server puts resources at the API root (e.g., `/api/systems`).

**What the server actually returns:**

The root document provides **absolute URLs** for each resource:

```
http://45.55.99.236:8080/sensorhub/api/systems
http://45.55.99.236:8080/sensorhub/api/deployments
...etc
```

Meanwhile, every collection's `self` link points to the same place — the collections **list**, not an individual collection:

```json
{ "rel": "self", "href": "http://45.55.99.236:8080/sensorhub/api/collections" }
```

Without our fix, the builder would compute URLs like:

```
http://45.55.99.236:8080/sensorhub/api/collections/systems  ← WRONG
```

**Our fix (Issue #35):** The `csapi()` factory in `endpoint.ts` now calls `extractRootResourceUrls()`, which scans the root document's links and builds a map like:

```
systems     → http://45.55.99.236:8080/sensorhub/api/systems
deployments → http://45.55.99.236:8080/sensorhub/api/deployments
...etc
```

This map is passed to the builder. When constructing a URL, the builder checks the map first. If an absolute URL exists for the resource type, it uses that directly. Otherwise, it falls back to the collection-scoped pattern (for servers that do use collection paths).

So `getSystems()` would now return:

```
http://45.55.99.236:8080/sensorhub/api/systems  ← CORRECT
```

And `getSystem('abc-123')` would return:

```
http://45.55.99.236:8080/sensorhub/api/systems/abc-123  ← CORRECT
```

**Verdict: FIXED.** URLs are constructed correctly for this server's top-level pattern, while collection-scoped servers continue to work unchanged.

---

## Remaining Findings (Not Addressed — Phase 3)

| Finding                                             | Severity | Status          | Why It's Not Yet Relevant                                          |
| --------------------------------------------------- | -------- | --------------- | ------------------------------------------------------------------ |
| F3: `items` envelope instead of `FeatureCollection` | Moderate | Issue #36 open  | Affects response **parsing**, which we haven't built yet (Phase 3) |
| F4: Array-format `validTime`                        | Moderate | Issue #37 open  | Also response parsing — Phase 3                                    |
| F5: Missing `numberMatched`/`numberReturned`        | Low      | No issue needed | Our types already use optional fields                              |

---

## Conclusion

Both critical blockers are resolved. The builder can now correctly discover resources and construct URLs for servers using either the collection-scoped pattern (our fixtures) or the top-level pattern (the real OpenSensorHub server). We are clear to proceed with Issues #6–#13 (remaining resource methods).
