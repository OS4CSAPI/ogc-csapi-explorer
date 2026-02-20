# 52North CSA Demo — Part 2 Implementation Evaluation

**Date:** 2026-02-20  
**Prompted by:** Senior developer assertion that 52North "definitely does" implement CSAPI Part 2  
**Method:** Live probing of `https://csa.demo.52north.org` via Vite dev proxy  
**Verdict:** **The 52North CSA Demo server does NOT implement CSAPI Part 2**

---

## Executive Summary

The 52North Connected Systems API demo server implements **Part 1 only** (systems, procedures, deployments, sampling features). Part 2 endpoints (datastreams, observations, control streams, commands) are either non-functional (500/400 errors) or absent (404). The server declares no Part 2 conformance classes and its OpenAPI specification contains zero Part 2 paths.

A `datastreams` collection is *declared* in the collections list, but the endpoint itself crashes — the server returns 500 for `application/json` and 400 for `application/geo+json` with an empty mimetype whitelist error, indicating the datastream handler is either incomplete or misconfigured.

---

## Evidence

### 1. Conformance Declaration

The server declares exactly **1** conformance class:

```
http://www.opengis.net/spec/ogcapi-common-1/1.0/conf/core
```

**Not declared** (would be expected for Part 2):
- `http://www.opengis.net/spec/ogcapi-connectedsystems-2/1.0/conf/dynamic-data`
- `http://www.opengis.net/spec/ogcapi-connectedsystems-2/1.0/conf/datastream`
- `http://www.opengis.net/spec/ogcapi-connectedsystems-2/1.0/conf/controlstream`
- `http://www.opengis.net/spec/ogcapi-connectedsystems-2/1.0/conf/json`
- `http://www.opengis.net/spec/ogcapi-connectedsystems-2/1.0/conf/swecommon-json`

**Not declared** (Part 1 — also missing):
- `http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/core`
- `http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/system`
- `http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/deployment`
- `http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/procedure`

The server doesn't even declare Part 1 conformance, despite clearly implementing Part 1 endpoints. This is either a bug in the conformance response or an intentional choice because the implementation may not be fully conformant.

### 2. OpenAPI Specification

The server's `/openapi` endpoint returns a 136 KB OpenAPI 3.x document with **11 paths total**:

| Path | Part | Status |
|------|------|--------|
| `/` | Common | Root landing page |
| `/conformance` | Common | Conformance declaration |
| `/openapi` | Common | API documentation |
| `/collections` | Common | Collection listing |
| `/collections/{systemCollectionId}/items` | Common/Features | Collection items |
| `/systems` | Part 1 | System listing |
| `/systems/{systemId}` | Part 1 | System detail |
| `/systems/{systemId}/members` | Part 1 | Subsystems |
| `/systems/{systemId}/deployments` | Part 1 | System's deployments |
| `/systems/{systemId}/samplingFeatures` | Part 1 | System's sampling features |
| `/deployments/{deploymentId}/systems` | Part 1 | Deployment's systems |

**Missing Part 2 paths** (zero of these appear):
- `/datastreams`, `/datastreams/{datastreamId}`
- `/observations`, `/observations/{observationId}`
- `/controlstreams`, `/controlstreams/{controlstreamId}`
- `/commands`, `/commands/{commandId}`
- `/systems/{systemId}/datastreams`
- `/systems/{systemId}/controlstreams`
- `/datastreams/{datastreamId}/observations`
- `/controlstreams/{controlstreamId}/commands`

### 3. Live Endpoint Probing

All Part 2 endpoints were probed with multiple `Accept` header values:

| Endpoint | Accept | Status | Response |
|----------|--------|--------|----------|
| `GET /datastreams?limit=2` | `application/json` | **500** | `Internal Server Error` |
| `GET /datastreams?limit=2` | `application/geo+json` | **400** | `"invalid mimetype supplied! expected [] got 'application/geo+json'"` |
| `GET /datastreams?limit=2` | `*/*` | **500** | `Internal Server Error` |
| `GET /datastreams?limit=2&f=json` | *(default)* | **500** | `Internal Server Error` |
| `GET /observations?limit=2` | `application/json` | **500** | `Internal Server Error` |
| `GET /observations?limit=2` | `application/geo+json` | **400** | Same mimetype error |
| `GET /controlstreams` | `application/json` | **404** | `Not Found` |
| `GET /commands` | `application/json` | **404** | `Not Found` |
| `GET /systems/5400-526/datastreams?limit=2` | `application/json` | **500** | `Internal Server Error` |
| `GET /systems/5400-526/datastreams?limit=2` | `application/geo+json` | **400** | Same mimetype error |

**Key observation:** The 400 error for `application/geo+json` returns `"expected [] got 'application/geo+json'"` — the empty array `[]` indicates the server's mimetype whitelist for the datastream handler is completely unconfigured. This strongly suggests the datastream endpoint was scaffolded but never completed or enabled.

### 4. Collections

The server declares 5 collections:

| Collection ID | Title | featureType |
|---------------|-------|-------------|
| `all_systems` | All Systems Instances | `system` |
| `all_datastreams` | All Datastreams | `datastreams` |
| `all_fois` | All Features of Interest | `featureOfInterest` |
| `all_procedures` | All Procedures and System Datasheets | `procedure` |
| `all_deployments` | All Deployments of Systems | `deployment` |

The `all_datastreams` collection is *declared* but the underlying endpoint is non-functional (see probing results above). No collections exist for observations, control streams, or commands.

### 5. Part 1 — Working Correctly

For contrast, Part 1 endpoints work properly:

| Endpoint | Accept | Status | Result |
|----------|--------|--------|--------|
| `GET /systems?limit=2` | `application/geo+json` | **200** | FeatureCollection with 2 systems |
| `GET /conformance` | `application/json` | **200** | 1 conformance class |
| `GET /collections` | `application/json` | **200** | 5 collections |
| `GET /` | `application/json` | **200** | Landing page with title, links |

Systems include proper GeoJSON features with properties like `uid`, `name`, `description`, `featureType`, `identifiers`, etc.

---

## Comparison with OSH SensorHub

For reference, OSH SensorHub (`http://45.55.99.236:8080/sensorhub/api`) implements both Part 1 and Part 2:

| Capability | 52North | OSH SensorHub |
|------------|---------|---------------|
| Conformance classes | 1 (common only) | 33 (22 CSAPI-specific) |
| Part 1 endpoints | Working | Working |
| Part 2 endpoints | Broken/absent | Working |
| `/datastreams` | 500/400 | 200 with data |
| `/observations` | 500/400 | 200 with data |
| `/controlstreams` | 404 | 200 with data |
| `/commands` | 404 | 200 with data |
| OpenAPI Part 2 paths | None | All present |
| Part 2 conformance classes | None | 8 declared |

---

## Possible Explanations

The senior developer's assertion may stem from one of these:

1. **Roadmap vs. current state:** 52North may be actively developing Part 2 support, and the developer knows it's planned or in progress — but the public demo server does not yet reflect this.

2. **Different server instance:** There may be a separate 52North deployment (staging, internal, or newer version) that does implement Part 2. The public demo at `csa.demo.52north.org` does not.

3. **Partial scaffolding:** The presence of the `all_datastreams` collection suggests Part 2 work has been started (the collection metadata exists), but the actual request handlers are incomplete (empty mimetype configuration, 500 errors).

4. **52North's broader portfolio:** 52North has extensive OGC API experience and likely implements Part 2 in other products or versions. The specific `csa.demo.52north.org` demo server instance is limited to Part 1.

---

## Impact on CSAPI Explorer Demo

Our demo app handles this gracefully:

- **Part 1 resources work**: Systems, procedures, deployments, sampling features all load and display correctly from 52North
- **Part 2 resources fail gracefully**: The Explorer shows error responses when attempting datastreams/observations/etc., but doesn't crash
- **Connection Diagnostics**: The amber "No CSAPI conformance classes" warning on the Connect page correctly flags that 52North doesn't declare CSAPI capabilities
- **Fallback assumption**: The app assumes all 9 resource types exist (since 52North doesn't advertise CSAPI links), but this is harmless — failed endpoints just show errors

---

## Conclusion

As of 2026-02-20, the 52North CSA Demo server at `https://csa.demo.52north.org`:

- **Implements:** OGC API Common + Connected Systems API Part 1 (systems, procedures, deployments, sampling features)
- **Does not implement:** Connected Systems API Part 2 (datastreams, observations, control streams, commands)
- **Has scaffolding for:** Datastreams (collection declared but handler non-functional)
- **Has no trace of:** Control streams, commands, observations

This finding is consistent with all four categories of evidence: conformance declarations, OpenAPI specification, live endpoint behavior, and collection metadata.
