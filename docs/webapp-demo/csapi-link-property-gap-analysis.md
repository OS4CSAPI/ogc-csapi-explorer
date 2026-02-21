# CS API `@link` / `@id` Property Gap Analysis

> **Scope:** `ogc-client-CSAPI_2` library — TypeScript interfaces, parsers, and utilities  
> **Date:** 2026-02-20  
> **Author:** AI-assisted audit (ogc-csapi-explorer development)  
> **Related Issue:** [ogc-client-CSAPI\_2 #103](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/103) — Part 2 parser cross-reference stripping

---

## 1. Executive Summary

The OGC Connected Systems API (CS API) spec defines **inline cross-reference
fields** — properties with `@link` or `@id` suffixes — that encode
parent–child and peer associations directly within resource JSON
representations. These fields are the primary mechanism by which a server
communicates structural relationships (e.g., *which procedure a system
implements*, *which platform a deployment is on*, *which system a datastream
belongs to*).

An audit of the `ogc-client-CSAPI_2` library source reveals **three
systematic gaps** that prevent consumers from accessing these relationships
through the library's typed API:

| # | Gap | Affected Files | Upstream Issue |
|---|-----|----------------|----------------|
| 1 | Part 1 (GeoJSON) TypeScript interfaces omit all `@link` fields | `model.ts` | [#108](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/108) |
| 2 | Part 1 `extractCSAPIFeature()` parser silently drops all `@link` properties | `geojson.ts` | [#109](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/109) |
| 3 | No `@link` resolution utilities exist | `helpers.ts` | [#110](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/110) |

> **Note:** The Part 2 parser gap is already tracked in
> [#103](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/103) and is
> _not_ duplicated here. This report covers the remaining three gaps.

---

## 2. Background — What Are `@link` / `@id` Fields?

The CS API JSON encoding (OGC 23-001 §16, OGC 23-002 §16.1) defines inline
properties that carry cross-resource references:

- **`@link` fields** — structured objects with `{ href, uid?, title?, rt? }`
  that resolve to another resource. Example: `systemKind@link` on a System
  points to the Procedure that describes it.

- **`@id` fields** — scalar strings containing the server-assigned ID of the
  referenced parent resource. Example: `system@id` on a Datastream contains
  the ID of the parent System.

These fields are **not** part of the HATEOAS `links[]` array — they are
**inline properties** within the resource JSON, alongside `name`,
`description`, etc.

### Example: System JSON from OSH SensorHub

```json
{
  "id": "of45kp7s5ims",
  "type": "Feature",
  "properties": {
    "featureType": "http://www.w3.org/ns/sosa/Platform",
    "uid": "urn:osh:sensor:odas:buoy:46042",
    "name": "ODAS Station 46042 — Monterey",
    "description": "Monterey offshore buoy, 36.785°N 122.469°W",
    "systemKind@link": {
      "href": "http://45.55.99.236:8080/sensorhub/api/procedures/of45l6iqgims",
      "uid": "urn:osh:sensor:odas:procedure:buoy-platform",
      "rt": "http://www.w3.org/ns/sosa/Procedure",
      "title": "ODAS Standard Buoy Platform"
    }
  },
  "geometry": { "type": "Point", "coordinates": [-122.469, 36.785] },
  "links": [...]
}
```

The `systemKind@link` property tells any consumer: *this system is an instance
of procedure `of45l6iqgims`*. After library parsing, **this property
disappears**.

---

## 3. Gap 1 — Part 1 TypeScript Interfaces Omit `@link` Fields

### Affected File

`src/ogc-api/csapi/model.ts`

### Problem

The TypeScript interfaces for all four Part 1 GeoJSON resources (`System`,
`Deployment`, `Procedure`, `SamplingFeature`) do not include any `@link`
fields. The interfaces model only the base property set (`featureType`, `uid`,
`name`, `description`, `assetType`, `validTime`) plus `geometry` and `links`.

### Evidence

**System interface** (model.ts ~L262-283):

```typescript
export interface System {
  id: string;
  type: 'Feature';
  properties: {
    featureType: SystemTypeUri | string;
    uid: string;
    name: string;
    description?: string;
    assetType?: 'Equipment' | 'Human' | ...;
    validTime?: TimeInterval;
  };
  geometry?: Geometry;
  links: ResourceLink[];
}
```

No `systemKind@link`, no `procedure@link`, no `parent@link`.

**Deployment interface** (model.ts ~L300-324):

Same structure — no `platform@link`, no `deployedSystems@link`.

**SamplingFeature interface** (model.ts ~L368-392):

Notably, the **JSDoc** (line ~L367) states:  
> *"The `sampledFeature@link` link relation is also required."*

…but the interface below it does not include a `sampledFeatureLInk` field.

### Spec-Required `@link` Fields by Resource Type

| Resource | `@link` Field | Spec Reference | Required? |
|----------|--------------|----------------|-----------|
| System | `systemKind@link` | OGC 23-001 §8.3 Table 8 | Conditional — when procedure exists |
| Deployment | `platform@link` | OGC 23-001 §8.5 Table 10 | Optional |
| Deployment | `deployedSystems@link` | OGC 23-001 §8.5 Table 10 | Required (array) |
| SamplingFeature | `sampledFeature@link` | OGC 23-001 §8.9 Table 14 | Required |

### Impact

- Consumers cannot type-safely read `@link` fields from parsed resources
- Code accessing these properties must use `(resource as any)['systemKind@link']` or bracket notation on raw JSON
- IDE autocomplete and TypeScript static analysis cannot help

---

## 4. Gap 2 — Part 1 `extractCSAPIFeature()` Drops All `@link` Properties

### Affected File

`src/ogc-api/csapi/formats/geojson.ts`

### Problem

The `extractCSAPIFeature()` function (line ~L395) is the sole entry point for
parsing Part 1 GeoJSON resources. It destructures the raw JSON's `properties`
object and extracts **only six named fields**:

1. `featureType`
2. `uid`
3. `name`
4. `description`
5. `assetType` (System only)
6. `validTime`

Any property not in this list is silently discarded — including all `@link`
fields.

### Evidence

**System case** (geojson.ts ~L441-453):

```typescript
case 'System':
  return {
    id: String(f.id ?? ''),
    type: 'Feature',
    properties: {
      ...baseProperties,
      ...(typeof p.assetType === 'string' ? { assetType: p.assetType } : {}),
      ...(validTime !== undefined ? { validTime } : {}),
    },
    ...(geometry !== undefined ? { geometry } : {}),
    links,
  } satisfies System;
```

The `satisfies System` constraint guarantees that only fields defined in the
`System` interface survive — since the interface has no `@link` fields, none
can be included.

**Input vs. Output:**

```
Input JSON properties:
  ├── featureType     ✅ extracted
  ├── uid             ✅ extracted
  ├── name            ✅ extracted
  ├── description     ✅ extracted
  ├── assetType       ✅ extracted
  ├── validTime       ✅ extracted
  ├── systemKind@link ❌ DROPPED
  └── parent@link     ❌ DROPPED
```

### How It Differs from Issue #103

Issue #103 covers the **Part 2** parsers (`parseDatastream`,
`parseControlStream`, etc.) in `part2.ts` which *explicitly* discard
cross-reference fields with JSDoc comments stating "intentionally ignored."

This gap covers the **Part 1** parser in `geojson.ts` which discards `@link`
fields *implicitly* by only extracting a fixed allowlist of property names.
The mechanism is different (allowlist vs. explicit skip) but the result is the
same: cross-reference data is lost.

---

## 5. Gap 3 — No `@link` Resolution Utilities

### Affected File

`src/ogc-api/csapi/helpers.ts` (and absence across the codebase)

### Problem

Even if Gaps 1 and 2 were fixed and `@link` fields survived parsing, there are
**no utility functions** to help consumers do anything useful with them.

### What Exists Today

`scanCsapiLinks()` (helpers.ts ~L131-172) scans **collection-level HATEOAS
`links[]` arrays** for resource type URLs — it operates on the document envelope,
not on inline `@link` properties within a resource.

`CSAPIQueryBuilder` (url_builder.ts, 2329 lines) has complete URL construction
methods for navigation endpoints (`getSystemProcedures()`,
`getSystemDeployments()`, `getDeploymentSystems()`, etc.) — but these require
the server to **implement** those endpoints. When a server doesn't (as is the
case with OSH SensorHub), `@link` fields are the only fallback.

### What Is Missing

| Utility | Purpose |
|---------|---------|
| `resolveLinkHref()` | Given a `@link` object `{ href, uid?, title? }`, fetch the target resource and return a typed result |
| `extractParentId()` | Given a parsed resource, return the parent resource's ID (from `@id` field) and type |
| `buildLinkFallbackUrl()` | Given a `@link` href and the API root, resolve relative or absolute URLs to a fetchable URL |
| `getAllCrossReferences()` | Given a raw or parsed resource, return a map of all `@link` / `@id` fields present |

### Real-World Impact

In the [ogc-csapi-explorer](https://github.com/OS4CSAPI/ogc-csapi-explorer),
we had to implement `tryLinkFallback()` in `ResourceDetail.vue` (~105 lines)
to manually:

1. Check if the raw resource has `systemKind@link`, `platform@link`, etc.
2. Parse the href from the `@link` object
3. Fetch the referenced resource directly
4. Display it in the UI

This pattern would need to be reimplemented by every consumer of the library
that encounters a server not supporting all navigation endpoints.

---

## 6. Cascading Dependency

The three gaps have a natural dependency chain:

```
Gap 1 (interfaces) → Gap 2 (parsers) → Gap 3 (utilities)
```

- Interfaces must define the fields before parsers can populate them
- Parsers must preserve the fields before utilities can operate on them
- Utilities provide the consumer-facing API for resolving references

However, **Gap 3 could be implemented independently** of Gaps 1–2 by operating
on raw JSON objects, similar to the explorer's `tryLinkFallback()` approach.

---

## 7. Discovery Context

These gaps were discovered during development of the
[ogc-csapi-explorer](https://github.com/OS4CSAPI/ogc-csapi-explorer) demo
application while ingesting the ODAS (Ocean Data Acquisition Systems) data
model into an OSH SensorHub server.

The ODAS data model includes 33 Part 1 resources (Systems, Deployments,
Procedures, SamplingFeatures) with rich `@link` cross-references. When the
Explorer attempted to display deployment associations and procedure links, all
panels showed "0 / None found" because:

1. **Layer 1 (server):** OSH SensorHub doesn't implement cross-resource
   navigation endpoints (`/systems/{id}/deployments` returns 400)
2. **Layer 2 (library):** Even when `@link` data is present in the raw JSON,
   the library strips it during parsing

The Explorer's `tryLinkFallback()` workaround (commit
[ad06b52](https://github.com/OS4CSAPI/ogc-csapi-explorer/commit/ad06b52))
solves the immediate UI problem but highlights a systemic gap in the library.

Full ingestion report:
[ODAS-CSAPI-Adapter-Simulator/ingestion-report.md](./ODAS-CSAPI-Adapter-Simulator/ingestion-report.md)

---

## 8. Upstream Issues Filed

The following issues have been filed on
[OS4CSAPI/ogc-client-CSAPI\_2](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues):

| Issue | Title | Gap |
|-------|-------|-----|
| [#103](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/103) | Parsed Part 2 models discard all cross-reference fields | Part 2 parsers |
| [#108](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/108) | Part 1 (GeoJSON) TypeScript interfaces omit all `@link` association properties | Gap 1 |
| [#109](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/109) | Part 1 `extractCSAPIFeature()` silently drops all `@link` properties during parsing | Gap 2 |
| [#110](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/110) | No `@link` / `@id` resolution utilities for cross-resource reference following | Gap 3 |

> All issues filed 2026-02-20.

---

## 9. OGC Spec References

- **OGC 23-001 §8.3** (Table 8) — System associations: `procedure` (Conditional)
- **OGC 23-001 §8.5** (Table 10) — Deployment associations: `platform` (Optional), `deployedSystems` (Required)
- **OGC 23-001 §8.9** (Table 14) — SamplingFeature associations: `sampledFeature` (Required)
- **OGC 23-001 §16** — JSON encoding for Part 1 resources (GeoJSON + `@link` inline properties)
- **OGC 23-002 §16.1** — JSON encoding for Part 2 resources (`@id` / `@link` inline properties)
- **OGC 23-002 §9.2** (Table 5) — Datastream associations: `system` (Required)
- **OGC 23-002 §10.2** (Table 10) — ControlStream associations: `system` (Required)
