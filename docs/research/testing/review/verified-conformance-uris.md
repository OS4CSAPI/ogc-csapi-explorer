# CSAPI Conformance Class URIs — Authoritative Reference

**Primary Authority:** Published OGC Implementation Standards

- [OGC 23-001 — Part 1: Feature Resources](https://docs.ogc.org/is/23-001/23-001.html)
- [OGC 23-002 — Part 2: Dynamic Data](https://docs.ogc.org/is/23-002/23-002.html)  
  **Cross-referenced Against:** Live OSH SensorHub CSAPI server (`/conformance` endpoint)  
  **Last Updated:** 2026-02-12  
  **Status:** AUTHORITATIVE — published specification takes precedence over any single server implementation

---

## Key Finding: Namespace Uses NO Hyphen

The correct URI namespace is:

```
ogcapi-connectedsystems-1    ← CORRECT (no hyphen between "connected" and "systems")
ogcapi-connected-systems-1   ← WRONG (hyphenated variant found in docs 22, 38)
```

Confirmed in both published specifications AND the live server. **The non-hyphenated form is correct.**

---

## Authoritative Conformance Classes (from Published Specifications)

### Part 1: Feature Resources (`ogcapi-connectedsystems-1`) — OGC 23-001

Source: Annex A (Normative), Conformance Class Abstract Test Suite

| Conformance Class     | Full URI                                                                               | Spec Clause |
| --------------------- | -------------------------------------------------------------------------------------- | ----------- |
| Common                | `http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/api-common`            | Clause 8    |
| System                | `http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/system`                | Clause 9    |
| Subsystem             | `http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/subsystem`             | Clause 10   |
| Deployment            | `http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/deployment`            | Clause 11   |
| Subdeployment         | `http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/subdeployment`         | Clause 12   |
| Procedure             | `http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/procedure`             | Clause 13   |
| Sampling Features     | `http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/sf`                    | Clause 14   |
| Property              | `http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/property`              | Clause 15   |
| Advanced Filtering    | `http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/advanced-filtering`    | Clause 16   |
| Create/Replace/Delete | `http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/create-replace-delete` | Clause 17   |
| Update                | `http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/update`                | Clause 18   |
| GeoJSON Encoding      | `http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/geojson`               | Clause 19.1 |
| SensorML Encoding     | `http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/sensorml`              | Clause 19.2 |

**Total: 13 conformance classes**

### Part 2: Dynamic Data (`ogcapi-connectedsystems-2`) — OGC 23-002

Source: Annex A (Normative), Conformance Class Abstract Test Suite

| Conformance Class     | Full URI                                                                               | Spec Clause |
| --------------------- | -------------------------------------------------------------------------------------- | ----------- |
| Common                | `http://www.opengis.net/spec/ogcapi-connectedsystems-2/1.0/conf/api-common`            | Clause 8    |
| Datastream            | `http://www.opengis.net/spec/ogcapi-connectedsystems-2/1.0/conf/datastream`            | Clause 9    |
| ControlStream         | `http://www.opengis.net/spec/ogcapi-connectedsystems-2/1.0/conf/controlstream`         | Clause 10   |
| Feasibility           | `http://www.opengis.net/spec/ogcapi-connectedsystems-2/1.0/conf/feasibility`           | Clause 11   |
| System Event          | `http://www.opengis.net/spec/ogcapi-connectedsystems-2/1.0/conf/system-event`          | Clause 12   |
| Advanced Filtering    | `http://www.opengis.net/spec/ogcapi-connectedsystems-2/1.0/conf/advanced-filtering`    | Clause 13   |
| Create/Replace/Delete | `http://www.opengis.net/spec/ogcapi-connectedsystems-2/1.0/conf/create-replace-delete` | Clause 14   |
| Update                | `http://www.opengis.net/spec/ogcapi-connectedsystems-2/1.0/conf/update`                | Clause 15   |
| JSON Encoding         | `http://www.opengis.net/spec/ogcapi-connectedsystems-2/1.0/conf/json`                  | Clause 16.1 |
| SWE Common JSON       | `http://www.opengis.net/spec/ogcapi-connectedsystems-2/1.0/conf/swecommon-json`        | Clause 16.2 |
| SWE Common Text       | `http://www.opengis.net/spec/ogcapi-connectedsystems-2/1.0/conf/swecommon-text`        | Clause 16.3 |
| SWE Common Binary     | `http://www.opengis.net/spec/ogcapi-connectedsystems-2/1.0/conf/swecommon-binary`      | Clause 16.4 |

**Total: 12 conformance classes**

### Part 3: Pub/Sub (`ogcapi-connectedsystems-3`)

> **Note:** Part 3 has not yet been verified against a published OGC standard. The URIs below are from the live server only and should be treated as provisional.

| Conformance Class | Full URI                                                                   | Source      |
| ----------------- | -------------------------------------------------------------------------- | ----------- |
| WebSocket         | `http://www.opengis.net/spec/ogcapi-connectedsystems-3/1.0/conf/websocket` | Server only |
| MQTT              | `http://www.opengis.net/spec/ogcapi-connectedsystems-3/1.0/conf/mqtt`      | Server only |

---

## Published Spec vs. Live Server: Full Comparison

Side-by-side comparison of every conformance class defined in the published OGC specifications against what the live OSH SensorHub server reports at its `/conformance` endpoint.

### Part 1: Feature Resources (`ogcapi-connectedsystems-1/1.0`)

| Conformance Class     | Published Spec (Annex A)      | Live Server                   | Match?                                                           |
| --------------------- | ----------------------------- | ----------------------------- | ---------------------------------------------------------------- |
| Common                | `/conf/api-common`            | `/conf/core`                  | **MISMATCH** — spec says `api-common`, server uses legacy `core` |
| System                | `/conf/system`                | `/conf/system`                | YES                                                              |
| Subsystem             | `/conf/subsystem`             | `/conf/subsystem`             | YES                                                              |
| Deployment            | `/conf/deployment`            | `/conf/deployment`            | YES                                                              |
| Subdeployment         | `/conf/subdeployment`         | `/conf/subdeployment`         | YES                                                              |
| Procedure             | `/conf/procedure`             | `/conf/procedure`             | YES                                                              |
| Sampling Features     | `/conf/sf`                    | `/conf/sf`                    | YES                                                              |
| Property              | `/conf/property`              | `/conf/property`              | YES                                                              |
| Advanced Filtering    | `/conf/advanced-filtering`    | _not reported_                | **ABSENT** — optional, server doesn't implement                  |
| Create/Replace/Delete | `/conf/create-replace-delete` | `/conf/create-replace-delete` | YES                                                              |
| Update                | `/conf/update`                | _not reported_                | **ABSENT** — optional, server doesn't implement                  |
| GeoJSON Encoding      | `/conf/geojson`               | `/conf/geojson`               | YES                                                              |
| SensorML Encoding     | `/conf/sensorml`              | `/conf/sensorml`              | YES                                                              |

### Part 2: Dynamic Data (`ogcapi-connectedsystems-2/1.0`)

| Conformance Class     | Published Spec (Annex A)      | Live Server                   | Match?                                          |
| --------------------- | ----------------------------- | ----------------------------- | ----------------------------------------------- |
| Common                | `/conf/api-common`            | _not separately listed_       | **ABSENT** — not reported by server             |
| Datastream            | `/conf/datastream`            | `/conf/datastream`            | YES                                             |
| ControlStream         | `/conf/controlstream`         | `/conf/controlstream`         | YES                                             |
| Feasibility           | `/conf/feasibility`           | _not reported_                | **ABSENT** — optional, server doesn't implement |
| System Event          | `/conf/system-event`          | `/conf/system-event`          | YES                                             |
| Advanced Filtering    | `/conf/advanced-filtering`    | _not reported_                | **ABSENT** — optional, server doesn't implement |
| Create/Replace/Delete | `/conf/create-replace-delete` | `/conf/create-replace-delete` | YES                                             |
| Update                | `/conf/update`                | _not reported_                | **ABSENT** — optional, server doesn't implement |
| JSON Encoding         | `/conf/json`                  | `/conf/json`                  | YES                                             |
| SWE Common JSON       | `/conf/swecommon-json`        | `/conf/swecommon-json`        | YES                                             |
| SWE Common Text       | `/conf/swecommon-text`        | `/conf/swecommon-text`        | YES                                             |
| SWE Common Binary     | `/conf/swecommon-binary`      | `/conf/swecommon-binary`      | YES                                             |

### Server-Only (not in published Parts 1 or 2)

| Live Server URI                                  | Notes                                                      |
| ------------------------------------------------ | ---------------------------------------------------------- |
| `.../connectedsystems-1/1.0/conf/core`           | Legacy name for `/conf/api-common`; renamed in final spec  |
| `.../connectedsystems-2/1.0/conf/system-history` | Not a separate class in published Part 2; server extension |
| `.../connectedsystems-3/1.0/conf/websocket`      | Part 3 — not yet verified against published spec           |
| `.../connectedsystems-3/1.0/conf/mqtt`           | Part 3 — not yet verified against published spec           |

---

## Server Deviations from Published Standard

The live OSH SensorHub server was built against drafts of the specification and has the following deviations from the published final standard:

### Deviation 1: `core` vs `api-common`

|                     | Published Spec     | Live Server               |
| ------------------- | ------------------ | ------------------------- |
| Part 1 Common class | `/conf/api-common` | `/conf/core`              |
| Part 2 Common class | `/conf/api-common` | _(not separately listed)_ |

**Impact for our client:** Our fixtures and detection code must use `/conf/api-common` (the spec-correct name). However, our code should also recognize `/conf/core` as a server-side alias to ensure compatibility with pre-finalization server implementations.

### Deviation 2: Server-only classes not in published Parts 1 or 2

| Server URI                                       | Notes                                                                                                             |
| ------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------- |
| `.../connectedsystems-2/1.0/conf/system-history` | Not a separate conformance class in published Part 2; may be bundled under another class or be a server extension |

### Deviation 3: Spec classes absent from server

These are defined in the published standard but the live server does not report them. This is expected — they are optional conformance classes that the server has not implemented:

| Conformance Class  | Part | Spec URI                                             |
| ------------------ | ---- | ---------------------------------------------------- |
| Advanced Filtering | 1    | `.../connectedsystems-1/1.0/conf/advanced-filtering` |
| Update             | 1    | `.../connectedsystems-1/1.0/conf/update`             |
| Common             | 2    | `.../connectedsystems-2/1.0/conf/api-common`         |
| Feasibility        | 2    | `.../connectedsystems-2/1.0/conf/feasibility`        |
| Advanced Filtering | 2    | `.../connectedsystems-2/1.0/conf/advanced-filtering` |
| Update             | 2    | `.../connectedsystems-2/1.0/conf/update`             |

---

## Discrepancies Found in Research Documents

### Problem 1: Wrong Namespace Prefix (Hyphenated)

**Documents affected:** 22, 38  
**Pattern:** `ogcapi-connected-systems-1` (hyphenated) instead of `ogcapi-connectedsystems-1`  
**Impact:** HIGH — code using this prefix will never match real conformance responses  
**Scope:** ~60+ occurrences across docs 22 and 38

### Problem 2: Wrong Conformance Class Names

**Documents affected:** 06, 12, 14, 18  
**Pattern:** Invented class names that don't exist in the specification

| Wrong (in docs)                 | Correct (from spec)                                            | Affected Docs |
| ------------------------------- | -------------------------------------------------------------- | ------------- |
| `conf/system-features`          | `conf/system`                                                  | 12, 18        |
| `conf/deployment-features`      | `conf/deployment`                                              | 12, 18        |
| `conf/procedure-features`       | `conf/procedure`                                               | 12            |
| `conf/samplingfeature-features` | `conf/sf`                                                      | 12            |
| `conf/property-features`        | `conf/property`                                                | 12            |
| `conf/datastream-schema`        | `conf/datastream`                                              | 12            |
| `conf/observation-features`     | _(no match — observations don't have a separate conf class)_   | 12            |
| `conf/controlstream-schema`     | `conf/controlstream`                                           | 12            |
| `conf/command-features`         | _(no match — commands don't have a separate conf class)_       | 12            |
| `conf/dynamic-data`             | _(not a real class name)_                                      | 14, 38        |
| `req/core`                      | `conf/api-common` (wrong prefix `/req/` AND wrong name `core`) | 06            |
| `req/datastreams`               | `conf/datastream` (wrong prefix AND plural)                    | 06            |
| `req/create`                    | `conf/create-replace-delete`                                   | 06            |

### Problem 3: Wrong Encoding Class Names (Doc 22 only)

| Wrong (in doc 22)   | Correct (from spec)     |
| ------------------- | ----------------------- |
| `conf/o-and-m-json` | `conf/json`             |
| `conf/swe-json`     | `conf/swecommon-json`   |
| `conf/swe-text`     | `conf/swecommon-text`   |
| `conf/swe-binary`   | `conf/swecommon-binary` |

### Problem 4: Previously flagged as "invented" — now confirmed in published spec

The following were previously flagged as "not published by server" but are now **confirmed as valid** conformance classes in the published specification. The server simply doesn't implement them:

- `conf/api-common` — **VALID** (published in both Part 1 and Part 2, Clause 8)
- `conf/feasibility` — **VALID** (published in Part 2, Clause 11)
- `conf/update` — **VALID** (published in both Part 1 and Part 2)
- `conf/advanced-filtering` — **VALID** (published in both Part 1 and Part 2)

> Doc 22 had these correct all along. However, Doc 22 also has the hyphenated namespace problem, so the full URIs are still wrong.

---

## Landing Page Resource Links (Verified from Server)

The server's landing page confirms these rel types and endpoint paths:

| Rel Type           | Endpoint Path       |
| ------------------ | ------------------- |
| `systems`          | `/systems`          |
| `deployments`      | `/deployments`      |
| `procedures`       | `/procedures`       |
| `samplingFeatures` | `/samplingFeatures` |
| `datastreams`      | `/datastreams`      |
| `observations`     | `/observations`     |
| `conformance`      | `/conformance`      |
| `collections`      | `/collections`      |

---

## Recommended Fixture for `checkHasConnectedSystems()`

Based on the published specification, the minimum conformance fixture for CSAPI detection should include:

```json
{
  "conformsTo": [
    "http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/api-common",
    "http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/system",
    "http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/geojson"
  ]
}
```

The detection function should:

1. Check for `ogcapi-connectedsystems-1` (no hyphen) in the conformance URI strings
2. Accept both `/conf/api-common` (spec-correct) and `/conf/core` (server legacy) for maximum compatibility
