# Query Parameter Demonstration Coverage

> **Date**: 2026-02-17  
> **Context**: Assessment of whether the CSAPI Explorer demo app demonstrates the contribution-goal claim: *"Complete query parameter support (spatial, temporal, hierarchical, relationship-based, property-based filters)"*  
> **Methodology**: Exhaustive search of all demo app source files (`app/src/`) for query parameter usage, nested resource method calls, and UI controls that set filter values.

---

## Verdict: Partial — 3 of 5 filter categories demonstrated

The demo app demonstrates **spatial**, **temporal**, and **property-based** (free-text) filters against a live server. It does **not** demonstrate **hierarchical** or **relationship-based** query filters.

---

## Category-by-Category Analysis

### Spatial — DEMONSTRATED

| Parameter | UI Control | File | Notes |
|---|---|---|---|
| `bbox` | Interactive map drawing (OpenLayers Draw box) | `MapViewPage.vue` L110, L272, L433, L478, L588 | User draws a rectangle on the map; sent as `[minX, minY, maxX, maxY]` to systems, deployments, procedures, samplingFeatures, datastreams, controlStreams |

### Temporal — MOSTLY DEMONSTRATED

| Parameter | UI Control | File | Notes |
|---|---|---|---|
| `datetime` | DatePicker (start/end) | `ResourceList.vue` L73 | Part 1 types: systems, deployments, procedures, samplingFeatures, properties |
| `phenomenonTime` | DatePicker (start/end) | `ResourceList.vue` L67 | Part 2: observations and datastreams |
| `issueTime` | DatePicker (start/end) | `ResourceList.vue` L70 | Part 2: commands |
| `resultTime` | — | — | **NOT DEMONSTRATED** — never set in any component |
| `executionTime` | — | — | **NOT DEMONSTRATED** — never set in any component |

### Hierarchical — NOT DEMONSTRATED

| Parameter / Method | Status |
|---|---|
| `parent` | Never set as a query filter |
| `recursive` | Never set as a query filter |
| `getSystemSubsystems()` | Never called |
| `getDeploymentSubdeployments()` | Never called |

### Relationship-based — NOT DEMONSTRATED (as query filters)

| Parameter | Status |
|---|---|
| `systemId` | Never passed as a list filter |
| `procedureId` | Never passed as a list filter |
| `foiId` | Never passed as a list filter |
| `observedPropertyId` | Never passed as a list filter |
| `controlledPropertyId` | Never passed as a list filter |

> **Note:** The demo *does* use nested resource methods for CRUD URL routing (`getSystemDataStreams`, `getSystemControlStreams`, `createObservation`, `createCommand`), but those construct URL paths — they do not exercise relationship-based query *filters*.

### Property-based / Pagination — PARTIAL

| Parameter | UI Control | File | Demonstrated? |
|---|---|---|---|
| `q` (free-text) | InputText | `ResourceList.vue` L34, L110, L142 | **Yes** |
| `limit` | InputNumber (default 10) | `ResourceList.vue` L32; `MapViewPage.vue` L272 (hardcoded 200) | **Yes** |
| `offset` | Programmatic (prev/next buttons) | `ResourceList.vue` L33, L141, L243, L252 | **Yes** |
| `cursor` | Toggle button (offset↔cursor mode) | `ResourceList.vue` L91, L171–L178 | **Yes** |
| `id` | — | — | **Not demonstrated** as a collection query filter |
| `uid` | — | — | **Not demonstrated** as a collection query filter |
| `currentStatus` | — | — | **Not demonstrated** |
| `f` (format) | — | — | **Not demonstrated** (Accept header used instead) |
| `crs` | — | — | **Not demonstrated** |
| `sortBy` | — | — | **Not demonstrated** |
| `sortOrder` | — | — | **Not demonstrated** |

---

## Nested Resource / Relationship Methods

### Demonstrated (via CSAPIQueryBuilder)

| Method | File | Context |
|---|---|---|
| `getSystemDataStreams(parentId)` | `csapi-bridge.ts` L224 | Nested datastream creation under a system |
| `getSystemControlStreams(parentId)` | `csapi-bridge.ts` L227 | Nested control stream creation under a system |
| `createObservation(parentId)` | `csapi-bridge.ts` L225 | Creates observation under a datastream |
| `createCommand(parentId)` | `csapi-bridge.ts` L226 | Creates command under a control stream |
| `getDataStreamSchema(id)` | `csapi-bridge.ts` L296–L301 | Schema retrieval for SweSchemaDisplay |

### Demonstrated (manual URL construction, bypassing builder)

| Pattern | File | Context |
|---|---|---|
| `/datastreams/{id}/observations?limit=1` | `MapViewPage.vue` L352 | Fetch latest observation for system location |
| `/systems/{sysId}/samplingFeatures?limit=100` | `MapViewPage.vue` L544 | Enrich sampling features with parent system location |
| `/datastreams/{id}/observations?limit=500` | `MapViewPage.vue` L670 | Load observation tracks for map layer |

### Not Demonstrated

| Method | Category |
|---|---|
| `getSystemSubsystems()` | Hierarchical |
| `getDeploymentSubdeployments()` | Hierarchical |
| `getSystemDeployments()` | Relationship |
| `getSystemSamplingFeatures()` | Relationship (done manually, not via builder) |
| `getDataStreamObservations()` | Relationship (done manually, not via builder) |
| `getControlStreamCommands()` | Relationship |
| `getSystemHistory()` | History |
| `getDeploymentHistory()` | History |
| `getDataStreamHistory()` | History |
| `getObservationDatastream()` | Relationship (reverse) |
| `getCommandControlStream()` | Relationship (reverse) |

---

## CRUD Operations Through Builder

All 9 resource types go through the builder for full CRUD via bridge helpers:

| Bridge Function | Builder Methods Called | Used By |
|---|---|---|
| `getListUrl()` | `getSystems()`, `getDeployments()`, `getProcedures()`, `getSamplingFeatures()`, `getProperties()`, `getDataStreams()`, `getObservations()`, `getControlStreams()`, `getCommands()` | ResourceList.vue, MapViewPage.vue |
| `getDetailUrl()` | `getSystem()`, `getDeployment()`, ... all 9 | ResourceDetail.vue, SmokeTestPage.vue |
| `getCreateUrl()` | `createSystem()`, ..., `createObservation(parentId)`, `createCommand(parentId)` | ResourceCreate.vue, SmokeTestPage.vue |
| `getUpdateUrl()` | `updateSystem()`, ..., all 8 (properties are read-only) | ResourceUpdate.vue, SmokeTestPage.vue |
| `getDeleteUrl()` | `deleteSystem()`, ..., all 8 | ResourceDelete.vue, SmokeTestPage.vue |
| `getSchemaUrl()` | `getDataStreamSchema()` | SweSchemaDisplay.vue |

---

## Summary

| Filter Category | Demonstrated? | Parameters Exercised |
|---|---|---|
| **Spatial** | **Yes** | `bbox` (interactive map drawing) |
| **Temporal** | **Mostly** | `datetime`, `phenomenonTime`, `issueTime` — missing `resultTime`, `executionTime` |
| **Hierarchical** | **No** | `parent`, `recursive`, subsystem/subdeployment navigation unused |
| **Relationship-based** | **No** (as filters) | `systemId`, `procedureId`, `foiId`, `observedPropertyId`, `controlledPropertyId` unused |
| **Property-based** | **Partial** | `q`, `limit`, `offset`, `cursor` — missing `id`, `uid`, `currentStatus`, `f`, `crs`, `sortBy`, `sortOrder` |

The demo app proves the demonstrated capabilities work against a live server for the parameters it uses. However, someone looking to verify the contribution-goal claim across all five filter categories would find **hierarchical** and **relationship-based filters** unexercised. Those capabilities exist in the library's `QueryOptions` interfaces and `buildQueryString()` method but the demo UI has no controls for them and never passes them in API calls.
