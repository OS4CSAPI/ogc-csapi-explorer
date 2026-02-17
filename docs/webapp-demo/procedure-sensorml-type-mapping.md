# Procedure ↔ SensorML Process Type Mapping

## Overview

In the OGC API — Connected Systems (CSAPI), the **Procedure** resource represents a methodology for observation, actuation, or sampling. When requested in **GeoJSON** format (`application/geo+json`), the server returns a lightweight Feature with minimal metadata. When requested in **SensorML JSON** format (`application/sml+json`), the server returns a rich process description using one of four concrete SensorML 3.0 process types.

This document explains the implicit relationship between the CSAPI `Procedure` resource and the SensorML 3.0 type hierarchy, and identifies a documentation gap in the `ogc-client` library source code.

---

## The Concept Mapping

| CSAPI Concept | SensorML Concept | Description |
|---|---|---|
| **Procedure** (GeoJSON) | — | Lightweight Feature: `id`, `featureType`, `uid`, `name`, `description`, `geometry: null` |
| **Procedure** (SensorML) | `SensorMLProcess` | Rich process description — one of 4 concrete types below |
| — | `SimpleProcess` | Indivisible computational process (algorithm, function) |
| — | `AggregateProcess` | Composite process of interconnected sub-processes |
| — | `PhysicalComponent` | Physical device (detector, actuator) with location importance |
| — | `PhysicalSystem` | Aggregate of physical/non-physical sub-processes (e.g., weather station, UAV) |

### Content Negotiation

A client requests the same Procedure resource with different `Accept` headers to get different representations:

```
GET /api/procedures/{id}
Accept: application/geo+json     → Procedure (GeoJSON Feature)
Accept: application/sml+json     → SensorMLProcess (one of 4 types)
```

The `featureType` discriminator URI in the GeoJSON response hints at which concrete SensorML type the Procedure describes.

---

## SensorML 3.0 Type Hierarchy

From the OGC SensorML 3.0 spec (OGC 23-000), all components are modeled as processes. The inheritance hierarchy is:

```
DescribedObject
  ├─ Mode
  └─ AbstractProcess
       ├─ SimpleProcess          (type = 'SimpleProcess')
       ├─ AggregateProcess       (type = 'AggregateProcess')
       └─ AbstractPhysicalProcess
            ├─ PhysicalComponent (type = 'PhysicalComponent')
            └─ PhysicalSystem    (type = 'PhysicalSystem')
```

### Concrete Process Types (from OGC SensorML 3.0 — OGC 23-000)

#### SimpleProcess (Clause 8.3)
> "A simple process is a process that, for whatever reason, is considered indivisible. That is, there is no intent to further divide the process description into an aggregation of sub-processes."

- Typical use: mathematical functions, computational processes
- Has a `method` property describing the algorithm
- Example: A windchill computation taking temperature and wind speed inputs

#### AggregateProcess (Clause 8.4)
> "An aggregate process is a collection of autonomous component processes with an explicit mapping of the data flow between these processes. Components of an aggregate process can be simple processes (i.e., atomic) or be aggregate processes themselves."

- Contains `components` (sub-processes) and `connections` (data flow links)
- Execution-engine agnostic
- Example: A process chain applying linear transformation then clipping

#### PhysicalComponent (Clause 8.5)
> "A process shall be modeled as a 'Physical Component' if it provides a processing function with well-defined inputs and outputs, if there is no intent to further divide the device description into sub-process components, and if knowledge of its physical location is of importance."

- Extends `AbstractPhysicalProcess` with position/location support
- Has a `method` property (like SimpleProcess)
- Example: An outdoor thermometer sensor at a specific geographic location

#### PhysicalSystem (Clause 8.6)
> "A process shall be modeled as a 'Physical System' if it provides a processing function with well-defined inputs and outputs, if the device description is further divided into subprocess components, and if knowledge of its physical location is of importance."

- Combines physical positioning with `components` and `connections`
- Example: A weather station composed of thermometer, barometer, wind sensor, and computational sub-processes

### DescribedObject (Clause 8.2.2)
All process types inherit from `DescribedObject`, which provides:
- `uniqueId` — globally unique identifier
- `label` / `description` — human-readable metadata
- `keywords`, `identifiers`, `classifiers` — discovery support
- `capabilities` / `characteristics` — quantitative properties
- `contacts` / `documents` — organizational metadata
- `history` — maintenance/calibration events
- `validTime` — temporal validity period
- `securityConstraints` / `legalConstraints`

### AbstractProcess (Clause 8.2.9)
Extends `DescribedObject` and adds:
- `inputs` / `outputs` / `parameters` — process I/O using SWE Common data types
- `typeOf` — inheritance/configuration from a general process
- `featureOfInterest` — the entity being observed
- `configuration` — settings for configurable processes

---

## SensorML 3.0 Media Type

The registered media type for SensorML JSON encoding is:

- **Type**: `application/sml+json`
- **Spec reference**: OGC 23-000, Clause 9.1.2.1

> "The draft media type submission to IANA is provided below: Type name: application, Subtype name: sml+json"

Implementations may also use `application/vnd.ogc.sml+json` as a preliminary media type.

---

## Library Source Code References

### GeoJSON Procedure Interface
- **File**: `src/ogc-api/csapi/model.ts` (line ~323)
- **Interface**: `Procedure`
- **JSDoc states**: "detailed descriptions use SensorML" — but provides NO cross-reference to the SensorML types

### SensorML Process Types
- **File**: `src/ogc-api/csapi/formats/sensorml/types.ts` (916 lines)
- **Key types**: `DescribedObject`, `AbstractProcess`, `AbstractPhysicalProcess`, `SimpleProcess`, `AggregateProcess`, `PhysicalComponent`, `PhysicalSystem`, `SensorMLProcess` (union)
- **Gap**: The word "Procedure" never appears in this file — no mention that these types represent what CSAPI calls "Procedure" resources

### SensorML Parser
- **File**: `src/ogc-api/csapi/formats/sensorml/parser.ts`
- **Function**: `parseSensorML30()` — parses raw JSON into `SensorMLProcess` types

---

## Documentation Gap Identified

The implicit relationship between `Procedure` (GeoJSON) and `SensorMLProcess` (SensorML) is undocumented in both directions:

1. **`model.ts`**: The `Procedure` interface JSDoc says "detailed descriptions use SensorML" but does not reference `SensorMLProcess`, `SimpleProcess`, `PhysicalSystem`, etc., nor `sensorml/types.ts`

2. **`sensorml/types.ts`**: The module-level JSDoc thoroughly documents the SensorML hierarchy but never mentions that these types represent what CSAPI calls "Procedure" resources when served with `Accept: application/sml+json`

A developer asking "show me the SensorML type for a Procedure" would find no connecting thread between these two files. This is tracked as a GitHub issue for JSDoc cross-reference improvements.

---

## OGC Specification References

| Standard | Document | URL |
|---|---|---|
| SensorML 3.0 | OGC 23-000 | https://docs.ogc.org/is/23-000/23-000.html |
| CSAPI Part 1 | OGC 23-001 | https://docs.ogc.org/is/23-001/23-001.html |
| Procedure Resources | CSAPI §Procedure | https://docs.ogc.org/is/23-001/23-001.html#_procedure_resources |
| SWE Common 3.0 | OGC 08-094r1 | https://portal.ogc.org/files/?artifact_id=41157 |
| SensorML 2.1 | OGC 12-000r2 | https://docs.ogc.org/is/12-000r2/12-000r2.html |
