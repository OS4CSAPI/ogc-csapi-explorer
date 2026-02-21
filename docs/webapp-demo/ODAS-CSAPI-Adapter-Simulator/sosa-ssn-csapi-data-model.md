# ODAS Acoustic Array — Complete SOSA/SSN → CSAPI Data Model

**Date:** 2026-02-20
**Status:** Reference design — comprehensive mapping of SOSA/SSN ontology to CSAPI Part 1 & Part 2 resources

---

## Purpose

This document defines a **complete, fully-populated data model** for an ODAS (Open embeddeD Audition System) acoustic microphone array expressed through every CSAPI resource type. The goal is to exercise the full depth of the SOSA/SSN ontology as realized by the OGC Connected Systems API, leaving no resource type or property field unused.

### CSAPI Resource Types Covered

| # | Resource Type | OGC Part | SOSA/SSN Concept | Used? |
|---|---|---|---|---|
| 1 | **systems** | Part 1 | `sosa:Sensor`, `sosa:Platform`, `sosa:Actuator`, `ssn:System` | ✅ |
| 2 | **deployments** | Part 1 | `ssn:Deployment` | ✅ |
| 3 | **procedures** | Part 1 | `sosa:Procedure` | ✅ |
| 4 | **samplingFeatures** | Part 1 | `sosa:Sample` / `sosa:FeatureOfInterest` | ✅ |
| 5 | **properties** | Part 1 | `sosa:ObservableProperty` / `sosa:ActuatableProperty` | ✅ |
| 6 | **datastreams** | Part 2 | Link between `sosa:Sensor` → `sosa:Observation` | ✅ |
| 7 | **observations** | Part 2 | `sosa:Observation` | ✅ |
| 8 | **controlStreams** | Part 2 | Link between `sosa:Actuator` → `sosa:Actuation` | ✅ |
| 9 | **commands** | Part 2 | `sosa:Actuation` (commands to change system state) | ✅ |

---

## 1. Systems (Part 1) — `sosa:Platform`, `sosa:Sensor`, `sosa:Actuator`, `ssn:System`

The SOSA/SSN ontology defines a hierarchy: **Platform** hosts **Systems**, which have **Subsystems**. A Sensor is a subclass of System. We model the full hardware and software hierarchy.

### 1.1 Platform: XMOS xCORE Microphone Array Board

The physical circuit board is a `sosa:Platform` — it hosts the sensors and processing systems.

```json
{
  "type": "Feature",
  "id": "xcore-mic-board-001",
  "geometry": null,
  "properties": {
    "featureType": "http://www.w3.org/ns/sosa/Platform",
    "uid": "urn:x-odas:platform:xcore-mic-board-001",
    "name": "XMOS xCORE-200 Microphone Array Board #001",
    "description": "7-microphone circular PDM MEMS array on XMOS xCORE-200 multicore microcontroller board. USB Audio Class 1.0 interface. Hosts the physical microphone sensors and runs the ODAS DSP processing pipeline.",
    "assetType": "Equipment",
    "validTime": ["2026-01-15T00:00:00Z", null]
  },
  "links": [
    {
      "href": "{api_root}/systems/xcore-mic-board-001/subsystems",
      "rel": "subsystems",
      "title": "Hosted subsystems (microphone array, DSP processor)"
    },
    {
      "href": "{api_root}/systems/xcore-mic-board-001/deployments",
      "rel": "deployments",
      "title": "Deployments of this platform"
    }
  ]
}
```

**SOSA/SSN justification:**
- `sosa:Platform` — "an entity that hosts other entities, particularly Sensors, Actuators, Samplers, and other Platforms"
- `sosa:hosts` → the microphone array sensor and DSP system are hosted on this platform
- `assetType: Equipment` — physical electronic device

### 1.2 Sensor: 7-Microphone Circular Array (composite sensor)

The microphone array as a composite sensing unit. This is an `ssn:System` that is also a `sosa:Sensor` — it implements the beamforming procedure and has individual mics as subsystems.

```json
{
  "type": "Feature",
  "id": "mic-array-001",
  "geometry": null,
  "properties": {
    "featureType": "http://www.w3.org/ns/sosa/Sensor",
    "uid": "urn:x-odas:sensor:mic-array-001",
    "name": "7-Microphone Circular PDM Array",
    "description": "Circular arrangement of 7 PDM MEMS microphones with 38mm diameter. Functions as a phased array for spatial sound field sampling. Each microphone captures omnidirectional audio; the spatial geometry enables beamforming and direction-of-arrival estimation via cross-correlation of microphone pairs.",
    "assetType": "Equipment",
    "validTime": ["2026-01-15T00:00:00Z", null],
    "systemKind@link": {
      "href": "{api_root}/procedures/pdm-mems-audio-capture",
      "rel": "systemKind",
      "title": "PDM MEMS Audio Capture Procedure"
    }
  },
  "links": [
    {
      "href": "{api_root}/systems/xcore-mic-board-001",
      "rel": "parent",
      "title": "Parent platform (XMOS board)"
    },
    {
      "href": "{api_root}/systems/mic-array-001/subsystems",
      "rel": "subsystems",
      "title": "Individual microphone sensors (7)"
    },
    {
      "href": "{api_root}/systems/mic-array-001/datastreams",
      "rel": "datastreams",
      "title": "Raw audio data streams"
    }
  ]
}
```

**SOSA/SSN justification:**
- `sosa:Sensor` — "responds to a Stimulus, e.g., a change in the environment, and generates a Result"
- `ssn:hasSubSystem` → individual microphones
- `ssn:implements` → links to the audio capture Procedure
- The stimulus here (§4.3.2.10 `ssn:Stimulus`) is sound waves arriving at the array; sound pressure changes are the proxy (`ssn:isProxyFor`) for observable properties like direction-of-arrival

### 1.3 Sensors: Individual Microphones (×7)

Each physical microphone is a leaf-level `sosa:Sensor`. Example for microphone #1 (center):

```json
{
  "type": "Feature",
  "id": "mic-001-ch1",
  "geometry": null,
  "properties": {
    "featureType": "http://www.w3.org/ns/sosa/Sensor",
    "uid": "urn:x-odas:sensor:mic-001-ch1",
    "name": "Microphone #1 (Center)",
    "description": "PDM MEMS microphone at array center position. Position relative to array origin: (0.000, 0.000, 0.000) meters. Omnidirectional sensitivity pattern.",
    "assetType": "Equipment",
    "validTime": ["2026-01-15T00:00:00Z", null]
  },
  "links": [
    {
      "href": "{api_root}/systems/mic-array-001",
      "rel": "parent",
      "title": "Parent system (microphone array)"
    }
  ]
}
```

Remaining microphones (#2–#7) follow the same pattern at their respective positions on the circular arrangement:
- Mic #2: (0.019, 0.000, 0.000) m — 0° on ring
- Mic #3: (0.0095, 0.0164, 0.000) m — 60°
- Mic #4: (−0.0095, 0.0164, 0.000) m — 120°
- Mic #5: (−0.019, 0.000, 0.000) m — 180°
- Mic #6: (−0.0095, −0.0164, 0.000) m — 240°
- Mic #7: (0.0095, −0.0164, 0.000) m — 300°

### 1.4 System: ODAS DSP Processing Pipeline

The software processing system is a composite `ssn:System` that contains the SSL and SST processing subsystems. This is not a physical sensor — it's a computational system.

```json
{
  "type": "Feature",
  "id": "odas-dsp-001",
  "geometry": null,
  "properties": {
    "featureType": "http://www.w3.org/ns/sosa/System",
    "uid": "urn:x-odas:system:odas-dsp-001",
    "name": "ODAS DSP Processing Pipeline",
    "description": "Software processing pipeline implementing sound source localization (SSL), tracking (SST), separation (SSS), and classification. Runs on host processor, receives raw audio from the XMOS board via USB, outputs structured JSON over TCP sockets.",
    "assetType": "Process",
    "validTime": ["2026-01-15T00:00:00Z", null]
  },
  "links": [
    {
      "href": "{api_root}/systems/xcore-mic-board-001",
      "rel": "parent",
      "title": "Parent platform (XMOS board)"
    },
    {
      "href": "{api_root}/systems/odas-dsp-001/subsystems",
      "rel": "subsystems",
      "title": "SSL and SST processing subsystems"
    }
  ]
}
```

**SOSA/SSN justification:**
- `ssn:System` — "a unit of abstraction for pieces of infrastructure that implement Procedures"
- `assetType: Process` — software/computational process, not a physical device
- Contains subsystems that each implement specific Procedures

### 1.5 Sensor: SSL Module (Sound Source Localizer)

The SSL processing module acts as a virtual `sosa:Sensor` — it observes sound source directions from the raw audio input.

```json
{
  "type": "Feature",
  "id": "odas-ssl-001",
  "geometry": null,
  "properties": {
    "featureType": "http://www.w3.org/ns/sosa/Sensor",
    "uid": "urn:x-odas:sensor:ssl-001",
    "name": "ODAS SSL Module (Sound Source Localizer)",
    "description": "Steered Response Power with Phase Transform (SRP-PHAT) beamformer. Scans a virtual hemisphere around the microphone array counting the sum of microphone-pair cross-correlations at each point. Outputs up to 4 potential sound source directions per frame as unit-sphere vectors with associated energy values.",
    "assetType": "Simulation",
    "validTime": ["2026-01-15T00:00:00Z", null],
    "systemKind@link": {
      "href": "{api_root}/procedures/srp-phat-beamforming",
      "rel": "systemKind",
      "title": "SRP-PHAT Beamforming Procedure"
    }
  },
  "links": [
    {
      "href": "{api_root}/systems/odas-dsp-001",
      "rel": "parent",
      "title": "Parent system (ODAS DSP pipeline)"
    },
    {
      "href": "{api_root}/systems/odas-ssl-001/datastreams",
      "rel": "datastreams",
      "title": "SSL output data streams"
    }
  ]
}
```

**SOSA/SSN justification:**
- `sosa:Sensor` — the SOSA spec explicitly includes "software (simulation)" as valid Sensors
- `assetType: Simulation` — software-based virtual sensor
- `ssn:implements` → SRP-PHAT beamforming Procedure

### 1.6 Sensor: SST Module (Sound Source Tracker)

The SST processing module. Consumes SSL output and produces tracked sources with persistent IDs.

```json
{
  "type": "Feature",
  "id": "odas-sst-001",
  "geometry": null,
  "properties": {
    "featureType": "http://www.w3.org/ns/sosa/Sensor",
    "uid": "urn:x-odas:sensor:sst-001",
    "name": "ODAS SST Module (Sound Source Tracker)",
    "description": "Particle filter-based sound source tracker. Assigns persistent identity to detected sound sources across frames. Manages source birth (instantiation), tracking, and death (removal). Outputs tracked source directions with identity, tag, and activity level.",
    "assetType": "Simulation",
    "validTime": ["2026-01-15T00:00:00Z", null],
    "systemKind@link": {
      "href": "{api_root}/procedures/particle-filter-tracking",
      "rel": "systemKind",
      "title": "Particle Filter Tracking Procedure"
    }
  },
  "links": [
    {
      "href": "{api_root}/systems/odas-dsp-001",
      "rel": "parent",
      "title": "Parent system (ODAS DSP pipeline)"
    },
    {
      "href": "{api_root}/systems/odas-sst-001/datastreams",
      "rel": "datastreams",
      "title": "SST output data streams"
    }
  ]
}
```

### 1.7 System: Multi-Array Triangulation Engine

When multiple arrays are deployed, a higher-level system performs 3D triangulation. This is a computational `ssn:System`.

```json
{
  "type": "Feature",
  "id": "triangulation-engine-001",
  "geometry": null,
  "properties": {
    "featureType": "http://www.w3.org/ns/sosa/System",
    "uid": "urn:x-odas:system:triangulation-engine-001",
    "name": "Multi-Array 3D Triangulation Engine",
    "description": "Central fusion system that collects DOA vectors from multiple distributed microphone arrays and estimates 3D source positions using Ray-to-Ray intersection (Schneider & Eberly 2002) with particle filtering refinement. Requires NTP-synchronized timestamps from each array (±100ms).",
    "assetType": "Process",
    "validTime": ["2026-01-15T00:00:00Z", null],
    "systemKind@link": {
      "href": "{api_root}/procedures/ray-to-ray-triangulation",
      "rel": "systemKind",
      "title": "Ray-to-Ray Triangulation Procedure"
    }
  },
  "links": [
    {
      "href": "{api_root}/systems/triangulation-engine-001/datastreams",
      "rel": "datastreams",
      "title": "Triangulated position data streams"
    }
  ]
}
```

### 1.8 Actuator: ODAS Configuration Controller

The system also has a controllable aspect — runtime parameters can be changed via commands. This maps to `sosa:Actuator`.

```json
{
  "type": "Feature",
  "id": "odas-config-actuator-001",
  "geometry": null,
  "properties": {
    "featureType": "http://www.w3.org/ns/sosa/Actuator",
    "uid": "urn:x-odas:actuator:config-001",
    "name": "ODAS Runtime Configuration Controller",
    "description": "Actuator interface for modifying ODAS runtime parameters. Controls detection thresholds, tracking sensitivity, frame processing rate, and microphone gain. Acts on system configuration properties to tune the processing pipeline for environmental conditions.",
    "assetType": "Process",
    "validTime": ["2026-01-15T00:00:00Z", null],
    "systemKind@link": {
      "href": "{api_root}/procedures/odas-config-procedure",
      "rel": "systemKind",
      "title": "ODAS Configuration Actuation Procedure"
    }
  },
  "links": [
    {
      "href": "{api_root}/systems/xcore-mic-board-001",
      "rel": "parent",
      "title": "Parent platform"
    },
    {
      "href": "{api_root}/systems/odas-config-actuator-001/controlstreams",
      "rel": "controlstreams",
      "title": "Control streams for configuration commands"
    }
  ]
}
```

**SOSA/SSN justification:**
- `sosa:Actuator` — "a device that is used by, or implements, a Procedure that changes the state of the world"
- Here the "world" being changed is the system's own configuration state
- `sosa:actsOnProperty` → detection threshold, tracking sensitivity (ActuatableProperties)

### Systems Hierarchy Summary

```
sosa:Platform — XMOS xCORE Board (xcore-mic-board-001)
├── sosa:Sensor — 7-Mic Array (mic-array-001)
│   ├── sosa:Sensor — Mic #1 Center (mic-001-ch1)
│   ├── sosa:Sensor — Mic #2 (mic-001-ch2)
│   ├── sosa:Sensor — Mic #3 (mic-001-ch3)
│   ├── sosa:Sensor — Mic #4 (mic-001-ch4)
│   ├── sosa:Sensor — Mic #5 (mic-001-ch5)
│   ├── sosa:Sensor — Mic #6 (mic-001-ch6)
│   └── sosa:Sensor — Mic #7 (mic-001-ch7)
├── ssn:System — ODAS DSP Pipeline (odas-dsp-001)
│   ├── sosa:Sensor — SSL Module (odas-ssl-001)
│   └── sosa:Sensor — SST Module (odas-sst-001)
├── sosa:Actuator — Config Controller (odas-config-actuator-001)
└── ssn:System — Triangulation Engine (triangulation-engine-001) [multi-array only]
```

---

## 2. Procedures (Part 1) — `sosa:Procedure`

Procedures describe methodologies: "a workflow, protocol, plan, algorithm, or computational method specifying how to make an Observation, create a Sample, or make a change to the state of the world."

Each procedure in GeoJSON has `geometry: null` — the detailed description lives in SensorML format.

### 2.1 PDM MEMS Audio Capture Procedure

```json
{
  "type": "Feature",
  "id": "pdm-mems-audio-capture",
  "geometry": null,
  "properties": {
    "featureType": "http://www.w3.org/ns/sosa/Procedure",
    "uid": "urn:x-odas:procedure:pdm-mems-audio-capture",
    "name": "PDM MEMS Microphone Audio Capture",
    "description": "Pulse Density Modulation (PDM) microphone sampling procedure. Each MEMS microphone produces a 1-bit PDM bitstream at a high oversampling rate. The XMOS xCORE decimation filter converts PDM to PCM at the target sample rate (16000 Hz default). Frame size: 256 samples, hop size: 128 samples. USB Audio Class 1.0 transport to host.",
    "procedureType": "http://www.w3.org/ns/sosa/ObservingProcedure"
  },
  "links": [
    {
      "href": "{api_root}/systems?procedure=pdm-mems-audio-capture",
      "rel": "implementingSystems",
      "title": "Systems implementing this procedure"
    }
  ]
}
```

### 2.2 SRP-PHAT Beamforming Procedure (SSL)

```json
{
  "type": "Feature",
  "id": "srp-phat-beamforming",
  "geometry": null,
  "properties": {
    "featureType": "http://www.w3.org/ns/sosa/Procedure",
    "uid": "urn:x-odas:procedure:srp-phat-beamforming",
    "name": "SRP-PHAT Steered Response Power Beamforming",
    "description": "Sound Source Localization via Steered Response Power with Phase Transform. For each audio frame: (1) Compute generalized cross-correlation (GCC-PHAT) for all microphone pairs. (2) Scan a virtual hemisphere of candidate directions at configurable angular resolution. (3) For each candidate direction, sum the cross-correlation values for all mic pairs at the expected time delay. (4) The direction with highest accumulated energy is the DOA. Outputs up to 4 potential sources per frame as unit-sphere vectors (x,y,z) with energy E. Input: multi-channel PCM audio. Output: SSL pots {x, y, z, E}[0..3].",
    "procedureType": "http://www.w3.org/ns/sosa/ObservingProcedure"
  },
  "links": [
    {
      "href": "{api_root}/systems?procedure=srp-phat-beamforming",
      "rel": "implementingSystems",
      "title": "SSL modules implementing this procedure"
    }
  ]
}
```

**SOSA/SSN note:** `ssn:hasInput` → multi-channel PCM audio; `ssn:hasOutput` → SSL pots. In SensorML format, these would be fully specified with SWE Common DataRecord schemas.

### 2.3 Particle Filter Tracking Procedure (SST)

```json
{
  "type": "Feature",
  "id": "particle-filter-tracking",
  "geometry": null,
  "properties": {
    "featureType": "http://www.w3.org/ns/sosa/Procedure",
    "uid": "urn:x-odas:procedure:particle-filter-tracking",
    "name": "Particle Filter Sound Source Tracking",
    "description": "Sound Source Tracking via particle filtering. Steps: (1) Prediction — excitation-damping model with three motion states (stationary 10%, constant velocity 40%, acceleration 50%). (2) Instantaneous probability — compare energy to threshold E_T. (3) Observation assignation — Bayesian hypothesis testing (false detection H1, new source H2, existing source H3). (4) Instantiation — initialize H=500 particles from Gaussian distribution when P(new) > T_new for F_new consecutive frames. (5) Removal — destroy filter when P(false) < T_remove for F_remove frames. (6) Weight update — multiply weights by observation likelihood. (7) Resampling — when effective particle count drops below threshold. Output: tracked sources with persistent ID, tag, direction (x,y,z), activity level.",
    "procedureType": "http://www.w3.org/ns/sosa/ObservingProcedure"
  },
  "links": [
    {
      "href": "{api_root}/systems?procedure=particle-filter-tracking",
      "rel": "implementingSystems",
      "title": "SST modules implementing this procedure"
    }
  ]
}
```

### 2.4 Ray-to-Ray Triangulation Procedure

```json
{
  "type": "Feature",
  "id": "ray-to-ray-triangulation",
  "geometry": null,
  "properties": {
    "featureType": "http://www.w3.org/ns/sosa/Procedure",
    "uid": "urn:x-odas:procedure:ray-to-ray-triangulation",
    "name": "Multi-Array Ray-to-Ray 3D Triangulation",
    "description": "3D source position estimation from distributed microphone array DOAs (IROS 2017, Lauzon et al.). For K arrays at known positions L_k with DOA unit vectors q_k: (1) For each pair of arrays (a,b), compute the nearest point Z_ab on the two skew DOA lines using the Ray-to-Ray shortest distance algorithm (Schneider & Eberly 2002). (2) Average all K(K-1)/2 pair intersection points to get estimated position μ_pos. (3) Use this as the initialization mean for the particle filter. (4) Particle filter refines position estimate over time with excitation-damping motion model. Requires NTP synchronization (±100ms) between arrays. Minimum 2 arrays required; 3+ arrays recommended for robust estimation.",
    "procedureType": "http://www.w3.org/ns/sosa/ObservingProcedure"
  },
  "links": []
}
```

### 2.5 ODAS Configuration Actuation Procedure

```json
{
  "type": "Feature",
  "id": "odas-config-procedure",
  "geometry": null,
  "properties": {
    "featureType": "http://www.w3.org/ns/sosa/Procedure",
    "uid": "urn:x-odas:procedure:odas-config-actuation",
    "name": "ODAS Runtime Configuration Actuation",
    "description": "Procedure for modifying ODAS pipeline parameters at runtime. Validates parameter values against permitted ranges, applies changes to the active processing pipeline, and confirms the new state. Supports atomic parameter updates (single parameter) and batch updates (multiple parameters in one command).",
    "procedureType": "http://www.w3.org/ns/sosa/ActuatingProcedure"
  },
  "links": []
}
```

**SOSA/SSN justification:** The O&M alignment (§6.3.3) defines `sosa-om:ActuationProcedure` as a distinct subtype.

---

## 3. Properties (Part 1) — `sosa:ObservableProperty`, `sosa:ActuatableProperty`

Properties define *what* is being observed or controlled. In CSAPI, these are `Property` resources (not GeoJSON Features — flat SWE Common objects).

### 3.1 Observable Properties

#### Sound Source Direction of Arrival (DOA)

```json
{
  "id": "prop-sound-doa",
  "label": "Sound Source Direction of Arrival",
  "description": "The instantaneous direction from which a sound source is perceived by a microphone array. Expressed as a unit vector (x, y, z) on the unit sphere centered on the array, or equivalently as azimuth and elevation angles. The primary observable output of the SSL module.",
  "uniqueId": "urn:x-odas:property:sound-source-doa",
  "baseProperty": "http://qudt.org/vocab/quantitykind/Angle",
  "objectType": "http://www.w3.org/ns/sosa/FeatureOfInterest",
  "links": []
}
```

#### Sound Source Energy

```json
{
  "id": "prop-sound-energy",
  "label": "Sound Source Energy",
  "description": "The accumulated beamformer response energy at the detected direction of arrival. Proportional to the signal-to-noise ratio of the sound source in the direction of interest. Values range from 0 (noise floor) to 1+ (strong source). The energy threshold E_T (default: 600 unnormalized) discriminates real sources from noise.",
  "uniqueId": "urn:x-odas:property:sound-source-energy",
  "baseProperty": "http://qudt.org/vocab/quantitykind/Energy",
  "objectType": "http://www.w3.org/ns/sosa/FeatureOfInterest",
  "links": []
}
```

#### Sound Source Activity Level

```json
{
  "id": "prop-source-activity",
  "label": "Sound Source Activity Level",
  "description": "The tracking activity level of a sound source, representing the tracker's confidence that the source is currently active and producing sound. Ranges from 0.0 (inactive/lost) to 1.0 (highly active). Derived from the particle filter weight diversity and observation assignment probabilities.",
  "uniqueId": "urn:x-odas:property:source-activity-level",
  "baseProperty": "http://qudt.org/vocab/quantitykind/DimensionlessRatio",
  "objectType": "http://www.w3.org/ns/sosa/FeatureOfInterest",
  "links": []
}
```

#### Geographic Bearing (LOB)

```json
{
  "id": "prop-geographic-bearing",
  "label": "Geographic Line of Bearing",
  "description": "The true geographic azimuth bearing from a sensor array to a detected sound source. Computed by transforming the array-local DOA unit vector to a geographic azimuth using the array's known position and orientation. Expressed in degrees clockwise from true north (0-360°).",
  "uniqueId": "urn:x-odas:property:geographic-bearing",
  "baseProperty": "http://qudt.org/vocab/quantitykind/Angle",
  "objectType": "http://www.w3.org/ns/sosa/FeatureOfInterest",
  "links": [
    {
      "href": "{api_root}/properties/prop-sound-doa",
      "rel": "baseProperty",
      "title": "Derived from: Sound Source DOA"
    }
  ]
}
```

#### Triangulated 3D Position

```json
{
  "id": "prop-triangulated-position",
  "label": "Triangulated 3D Source Position",
  "description": "The estimated 3D geographic position of a sound source, derived from multi-array triangulation. Computed via Ray-to-Ray intersection of DOA vectors from 2+ distributed arrays. Includes estimated uncertainty ellipsoid based on DOA angle variance (σ_φ ≈ 0.0961 rad / ~5.5°) and array geometry.",
  "uniqueId": "urn:x-odas:property:triangulated-position",
  "baseProperty": "http://qudt.org/vocab/quantitykind/Position",
  "objectType": "http://www.w3.org/ns/sosa/FeatureOfInterest",
  "links": []
}
```

### 3.2 Actuatable Properties

#### Detection Threshold

```json
{
  "id": "prop-detection-threshold",
  "label": "Detection Energy Threshold",
  "description": "The energy threshold E_T that discriminates real sound sources from noise in the SSL module. Observations with energy below this threshold are classified as noise with probability proportional to (E/E_T)². Default value: 600. Lowering increases sensitivity but also false detections; raising reduces sensitivity but improves precision.",
  "uniqueId": "urn:x-odas:property:detection-threshold",
  "baseProperty": "http://qudt.org/vocab/quantitykind/Energy",
  "objectType": "http://www.w3.org/ns/ssn/System",
  "links": []
}
```

#### Tracking Sensitivity

```json
{
  "id": "prop-tracking-sensitivity",
  "label": "Tracking New Source Sensitivity",
  "description": "The probability threshold T_new that must be exceeded for F_new consecutive frames to instantiate a new tracked source. Default: T_new=0.75, F_new=10 frames. Lower values create tracks more readily; higher values require stronger evidence.",
  "uniqueId": "urn:x-odas:property:tracking-sensitivity",
  "baseProperty": "http://qudt.org/vocab/quantitykind/DimensionlessRatio",
  "objectType": "http://www.w3.org/ns/ssn/System",
  "links": []
}
```

---

## 4. Deployments (Part 1) — `ssn:Deployment`

Deployments describe "where and when systems are deployed for a particular purpose."

### 4.1 Single-Array Indoor Deployment

```json
{
  "type": "Feature",
  "id": "deployment-office-array-001",
  "geometry": {
    "type": "Point",
    "coordinates": [-77.0365, 38.8977, 2.5]
  },
  "bbox": [-77.0366, 38.8976, -77.0364, 38.8978],
  "properties": {
    "featureType": "http://www.w3.org/ns/sosa/Deployment",
    "uid": "urn:x-odas:deployment:office-array-001",
    "name": "Conference Room 3A — Single Array Deployment",
    "description": "Deployment of XMOS microphone array board #001 on the ceiling of Conference Room 3A, Building 7. Array is mounted facing downward at 2.5m height, centered over the conference table. Orientation: array X-axis aligned with geographic north. Purpose: meeting room occupancy sensing and speaker localization for smart building applications.",
    "validTime": ["2026-02-01T09:00:00Z", null],
    "platform@link": {
      "href": "{api_root}/systems/xcore-mic-board-001",
      "rel": "platform",
      "title": "XMOS xCORE Board #001",
      "uid": "urn:x-odas:platform:xcore-mic-board-001"
    },
    "deployedSystems@link": [
      {
        "href": "{api_root}/systems/xcore-mic-board-001",
        "rel": "deployedSystem",
        "title": "Platform with all hosted subsystems"
      },
      {
        "href": "{api_root}/systems/mic-array-001",
        "rel": "deployedSystem",
        "title": "7-Microphone Array"
      },
      {
        "href": "{api_root}/systems/odas-dsp-001",
        "rel": "deployedSystem",
        "title": "ODAS DSP Pipeline"
      },
      {
        "href": "{api_root}/systems/odas-config-actuator-001",
        "rel": "deployedSystem",
        "title": "Configuration Actuator"
      }
    ],
    "featuresOfInterest@link": [
      {
        "href": "{api_root}/samplingFeatures/conference-room-3a",
        "rel": "featureOfInterest",
        "title": "Conference Room 3A acoustic environment"
      }
    ],
    "samplingFeatures@link": [
      {
        "href": "{api_root}/samplingFeatures/monitoring-zone-001",
        "rel": "samplingFeature",
        "title": "Acoustic monitoring zone around array #001"
      }
    ]
  },
  "links": [
    {
      "href": "{api_root}/deployments/deployment-office-array-001/subdeployments",
      "rel": "subdeployments",
      "title": "Sub-deployments (if multi-array)"
    }
  ]
}
```

**SOSA/SSN justification:** Every `ssn:Deployment` property is used:
- `ssn:deployedOnPlatform` → the XMOS board
- `ssn:deployedSystem` → all systems in this deployment
- `ssn:forProperty` → via `featuresOfInterest@link`, the ultimate features being observed
- Geometry → the geographic position where the systems are deployed
- `validTime` → when the deployment is active

### 4.2 Multi-Array Outdoor Triangulation Deployment (parent)

```json
{
  "type": "Feature",
  "id": "deployment-campus-triangulation",
  "geometry": {
    "type": "Polygon",
    "coordinates": [[
      [-77.0380, 38.8970],
      [-77.0350, 38.8970],
      [-77.0350, 38.8990],
      [-77.0380, 38.8990],
      [-77.0380, 38.8970]
    ]]
  },
  "properties": {
    "featureType": "http://www.w3.org/ns/sosa/Deployment",
    "uid": "urn:x-odas:deployment:campus-triangulation",
    "name": "Campus Perimeter — 3-Array Triangulation Deployment",
    "description": "Deployment of three distributed microphone arrays in a triangular configuration (10m spacing) for 3D sound source localization via DOA triangulation. Based on Lauzon et al. IROS 2017 methodology. Arrays positioned on the ground facing upward. Central fusion node performs Ray-to-Ray intersection.",
    "validTime": ["2026-02-15T00:00:00Z", null],
    "deployedSystems@link": [
      {
        "href": "{api_root}/systems/triangulation-engine-001",
        "rel": "deployedSystem",
        "title": "Multi-Array Triangulation Engine"
      }
    ],
    "subdeployments@link": [
      {
        "href": "{api_root}/deployments/deployment-array-north",
        "rel": "subdeployment",
        "title": "North array position"
      },
      {
        "href": "{api_root}/deployments/deployment-array-southeast",
        "rel": "subdeployment",
        "title": "Southeast array position"
      },
      {
        "href": "{api_root}/deployments/deployment-array-southwest",
        "rel": "subdeployment",
        "title": "Southwest array position"
      }
    ]
  },
  "links": []
}
```

**SOSA/SSN justification:** Demonstrates the hierarchical `subdeployments` pattern — the parent deployment covers the overall triangulation mission; each sub-deployment places one physical array at a specific location.

---

## 5. Sampling Features (Part 1) — `sosa:Sample` / `sosa:FeatureOfInterest`

Sampling features represent "the spatial or physical entity at or on which observations are made." In the SOSA ontology, a `sosa:Sample` is "intended to be representative of a FeatureOfInterest."

For acoustic arrays, the **ultimate Feature of Interest** is the acoustic environment (room, outdoor area). The **Sampling Feature** is the spatial zone the array can actually observe — the acoustic monitoring zone. Observations are made *on the sample* to characterize *the feature of interest*.

### 5.1 Ultimate Feature of Interest: Conference Room 3A

```json
{
  "type": "Feature",
  "id": "conference-room-3a",
  "geometry": {
    "type": "Polygon",
    "coordinates": [[
      [-77.0366, 38.8976],
      [-77.0364, 38.8976],
      [-77.0364, 38.8978],
      [-77.0366, 38.8978],
      [-77.0366, 38.8976]
    ]]
  },
  "properties": {
    "featureType": "http://www.opengis.net/def/samplingFeatureType/OGC-OM/2.0/SF_SamplingSurface",
    "uid": "urn:x-odas:foi:conference-room-3a",
    "name": "Conference Room 3A — Acoustic Environment",
    "description": "The acoustic environment of Conference Room 3A, Building 7. Approximately 8m × 6m × 3m. Carpeted floor, acoustic ceiling tiles, glass wall on south side. Typical background noise: HVAC at ~35 dBA. This is the ultimate feature of interest — the room whose acoustic properties we want to characterize.",
    "sampledFeature@link": {
      "href": "https://example.org/building-7",
      "rel": "sampledFeature",
      "title": "Building 7 — parent facility",
      "uid": "urn:x-facility:building-7"
    },
    "parentSystem@link": {
      "href": "{api_root}/systems/xcore-mic-board-001",
      "rel": "parentSystem",
      "title": "Observing system"
    }
  },
  "links": []
}
```

### 5.2 Sampling Feature: Acoustic Monitoring Zone

```json
{
  "type": "Feature",
  "id": "monitoring-zone-001",
  "geometry": {
    "type": "Polygon",
    "coordinates": [[
      [-77.0367, 38.8975],
      [-77.0363, 38.8975],
      [-77.0363, 38.8979],
      [-77.0367, 38.8979],
      [-77.0367, 38.8975]
    ]]
  },
  "properties": {
    "featureType": "http://www.opengis.net/def/samplingFeatureType/OGC-OM/2.0/SF_SamplingSurface",
    "uid": "urn:x-odas:sample:monitoring-zone-001",
    "name": "Array #001 Acoustic Monitoring Zone",
    "description": "The effective acoustic monitoring zone of microphone array #001. Defined by the hemisphere of directions the array can resolve (full 2π steradian hemisphere below the ceiling-mounted array). Effective range depends on source loudness vs. background noise — approximately 5-10m for normal speech, 20-50m for machinery or drone propellers.",
    "sampledFeature@link": {
      "href": "{api_root}/samplingFeatures/conference-room-3a",
      "rel": "sampledFeature",
      "title": "Conference Room 3A acoustic environment",
      "uid": "urn:x-odas:foi:conference-room-3a"
    },
    "sampleOf@link": [
      {
        "href": "{api_root}/samplingFeatures/conference-room-3a",
        "rel": "sampleOf",
        "title": "Sample of Conference Room 3A"
      }
    ],
    "parentSystem@link": {
      "href": "{api_root}/systems/mic-array-001",
      "rel": "parentSystem",
      "title": "Microphone array making observations on this feature"
    }
  },
  "links": []
}
```

**SOSA/SSN justification:**
- `sosa:Sample` — "intended to be representative of a FeatureOfInterest on which Observations may be made"
- `sosa:isSampleOf` → the monitoring zone samples the room's acoustic environment
- `sampledFeature@link` → points to the ultimate FOI (required by spec)
- This mirrors the SSN examples where a weather station samples the atmosphere, or an ice core samples an ice sheet

---

## 6. DataStreams (Part 2) — Sensor → Observation link

DataStreams connect sensors to their observation outputs. Each defines the schema, temporal extent, and observed properties.

### 6.1 SSL Potentials DataStream (raw DOA + energy)

```json
{
  "id": "ds-ssl-pots-001",
  "name": "SSL Potential Sources — Array #001",
  "description": "Raw Sound Source Localization output from array #001. Each observation contains up to 4 potential source directions as unit-sphere vectors with energy values. Updated at frame rate (16000 Hz / 128 hop = 125 frames/sec).",
  "validTime": {"start": "2026-02-01T09:00:00Z"},
  "formats": ["application/om+json", "application/swe+json"],
  "outputName": "ssl_pots",
  "observedProperties": [
    "urn:x-odas:property:sound-source-doa",
    "urn:x-odas:property:sound-source-energy"
  ],
  "phenomenonTime": {"start": "2026-02-01T09:00:00Z"},
  "resultTime": {"start": "2026-02-01T09:00:00Z"},
  "resultType": "record",
  "live": true,
  "type": "observation",
  "links": [
    {
      "href": "{api_root}/systems/odas-ssl-001",
      "rel": "system",
      "title": "SSL Module (sensor)"
    },
    {
      "href": "{api_root}/datastreams/ds-ssl-pots-001/observations",
      "rel": "observations",
      "title": "SSL observations"
    },
    {
      "href": "{api_root}/datastreams/ds-ssl-pots-001/schema",
      "rel": "schema",
      "title": "Observation result schema"
    }
  ]
}
```

**DataStream Schema** (SWE Common DataRecord):

```json
{
  "obsFormat": "application/om+json",
  "resultSchema": {
    "type": "DataRecord",
    "label": "SSL Potential Sources",
    "fields": [
      {
        "name": "numSources",
        "type": "Count",
        "label": "Number of detected sources",
        "constraint": {"min": 0, "max": 4}
      },
      {
        "name": "sources",
        "type": "DataArray",
        "elementCount": 4,
        "elementType": {
          "type": "DataRecord",
          "label": "Potential Source",
          "fields": [
            {
              "name": "direction",
              "type": "Vector",
              "label": "DOA unit vector",
              "referenceFrame": "urn:x-odas:crs:array-local",
              "coordinates": [
                {"name": "x", "type": "Quantity", "uom": {"code": "1"}, "label": "X component"},
                {"name": "y", "type": "Quantity", "uom": {"code": "1"}, "label": "Y component"},
                {"name": "z", "type": "Quantity", "uom": {"code": "1"}, "label": "Z component"}
              ]
            },
            {
              "name": "energy",
              "type": "Quantity",
              "label": "Beamformer energy",
              "uom": {"code": "1"},
              "constraint": {"min": 0.0}
            }
          ]
        }
      }
    ]
  }
}
```

### 6.2 SST Tracked Sources DataStream

```json
{
  "id": "ds-sst-tracks-001",
  "name": "SST Tracked Sources — Array #001",
  "description": "Sound Source Tracking output. Each observation contains currently tracked sources with persistent IDs, direction vectors, activity levels, and classification tags. Sources are born when detection exceeds T_new for F_new frames and die when below T_remove for F_remove frames.",
  "validTime": {"start": "2026-02-01T09:00:00Z"},
  "formats": ["application/om+json"],
  "outputName": "sst_tracks",
  "observedProperties": [
    "urn:x-odas:property:sound-source-doa",
    "urn:x-odas:property:source-activity-level"
  ],
  "phenomenonTime": {"start": "2026-02-01T09:00:00Z"},
  "resultTime": {"start": "2026-02-01T09:00:00Z"},
  "resultType": "record",
  "live": true,
  "type": "observation",
  "links": [
    {
      "href": "{api_root}/systems/odas-sst-001",
      "rel": "system",
      "title": "SST Module (sensor)"
    },
    {
      "href": "{api_root}/datastreams/ds-sst-tracks-001/observations",
      "rel": "observations",
      "title": "SST observations"
    }
  ]
}
```

### 6.3 Geographic Lines of Bearing DataStream

```json
{
  "id": "ds-lob-001",
  "name": "Geographic Lines of Bearing — Array #001",
  "description": "Transformed SSL output projected into geographic coordinates. Each observation contains Lines of Bearing (LOBs) as GeoJSON LineStrings from the array's known position along the computed true azimuth bearing. This is the primary geospatial data stream for map visualization.",
  "validTime": {"start": "2026-02-01T09:00:00Z"},
  "formats": ["application/geo+json", "application/om+json"],
  "outputName": "geographic_lob",
  "observedProperties": [
    "urn:x-odas:property:geographic-bearing",
    "urn:x-odas:property:sound-source-energy"
  ],
  "phenomenonTime": {"start": "2026-02-01T09:00:00Z"},
  "resultTime": {"start": "2026-02-01T09:00:00Z"},
  "resultType": "record",
  "live": true,
  "type": "observation",
  "links": [
    {
      "href": "{api_root}/systems/odas-ssl-001",
      "rel": "system",
      "title": "SSL Module via geographic transform"
    }
  ]
}
```

### 6.4 Triangulated Position DataStream (multi-array)

```json
{
  "id": "ds-triangulated-pos",
  "name": "Triangulated 3D Source Positions",
  "description": "Estimated 3D positions of sound sources from multi-array triangulation. Each observation contains the fused position estimate with uncertainty ellipse, contributing array IDs, and Ray-to-Ray intersection quality metrics. Only populated when 2+ arrays are deployed and observing the same source.",
  "validTime": {"start": "2026-02-15T00:00:00Z"},
  "formats": ["application/geo+json", "application/om+json"],
  "outputName": "triangulated_positions",
  "observedProperties": [
    "urn:x-odas:property:triangulated-position"
  ],
  "phenomenonTime": {"start": "2026-02-15T00:00:00Z"},
  "resultTime": {"start": "2026-02-15T00:00:00Z"},
  "resultType": "record",
  "live": true,
  "type": "observation",
  "links": [
    {
      "href": "{api_root}/systems/triangulation-engine-001",
      "rel": "system",
      "title": "Triangulation Engine"
    }
  ]
}
```

### 6.5 System Status DataStream

```json
{
  "id": "ds-system-status-001",
  "name": "System Health & Status — Array #001",
  "description": "Periodic system health reports: CPU load, audio buffer health, active track count, current parameter values, USB connection state. Published every 5 seconds.",
  "validTime": {"start": "2026-02-01T09:00:00Z"},
  "formats": ["application/om+json"],
  "outputName": "system_status",
  "observedProperties": [],
  "phenomenonTime": {"start": "2026-02-01T09:00:00Z"},
  "resultTime": {"start": "2026-02-01T09:00:00Z"},
  "resultType": "record",
  "live": true,
  "type": "status",
  "links": [
    {
      "href": "{api_root}/systems/odas-dsp-001",
      "rel": "system",
      "title": "ODAS DSP Pipeline"
    }
  ]
}
```

**Note:** The `type: "status"` field distinguishes health/telemetry streams from observation streams, per the CSAPI Part 2 spec.

---

## 7. Observations (Part 2) — `sosa:Observation`

Individual observation records from the data streams.

### 7.1 SSL Observation (single frame)

```json
{
  "id": "obs-ssl-2026-02-20T14-30-00-000",
  "phenomenonTime": "2026-02-20T14:30:00.000Z",
  "resultTime": "2026-02-20T14:30:00.008Z",
  "parameters": {
    "frameIndex": 112500,
    "sampleRate": 16000,
    "hopSize": 128
  },
  "result": {
    "numSources": 2,
    "sources": [
      {
        "direction": {"x": 0.342, "y": 0.940, "z": 0.000},
        "energy": 0.87
      },
      {
        "direction": {"x": -0.766, "y": 0.643, "z": 0.000},
        "energy": 0.42
      },
      {
        "direction": {"x": 0.0, "y": 0.0, "z": 0.0},
        "energy": 0.0
      },
      {
        "direction": {"x": 0.0, "y": 0.0, "z": 0.0},
        "energy": 0.0
      }
    ]
  },
  "links": [
    {
      "href": "{api_root}/datastreams/ds-ssl-pots-001",
      "rel": "datastream",
      "title": "Parent data stream"
    },
    {
      "href": "{api_root}/samplingFeatures/monitoring-zone-001",
      "rel": "featureOfInterest",
      "title": "Acoustic monitoring zone"
    }
  ]
}
```

**SOSA/SSN justification:** Maps 1:1 to `sosa:Observation`:
- `sosa:madeBySensor` → SSL module (via datastream → system link)
- `sosa:hasFeatureOfInterest` → monitoring zone (via `featureOfInterest` link)
- `sosa:observedProperty` → DOA + energy (via datastream → observedProperties)
- `sosa:hasResult` → the `result` object
- `sosa:resultTime` → when the result was produced (8ms processing latency)
- `sosa:phenomenonTime` → when the sound actually occurred
- `sosa:usedProcedure` → SRP-PHAT (via system → systemKind link)

### 7.2 SST Observation (single frame)

```json
{
  "id": "obs-sst-2026-02-20T14-30-00-000",
  "phenomenonTime": "2026-02-20T14:30:00.000Z",
  "resultTime": "2026-02-20T14:30:00.012Z",
  "parameters": {
    "frameIndex": 112500,
    "activeFilterCount": 1,
    "particlesPerFilter": 500
  },
  "result": {
    "numTracks": 1,
    "tracks": [
      {
        "id": 42,
        "tag": "dynamic",
        "direction": {"x": 0.342, "y": 0.940, "z": 0.000},
        "activity": 0.95,
        "motionState": "constantVelocity",
        "framesTracked": 250
      }
    ]
  },
  "links": [
    {
      "href": "{api_root}/datastreams/ds-sst-tracks-001",
      "rel": "datastream"
    }
  ]
}
```

### 7.3 LOB Observation (geographic bearing)

```json
{
  "id": "obs-lob-2026-02-20T14-30-00-000",
  "phenomenonTime": "2026-02-20T14:30:00.000Z",
  "resultTime": "2026-02-20T14:30:00.015Z",
  "result": {
    "bearings": [
      {
        "sourceId": 42,
        "azimuthDeg": 70.0,
        "elevationDeg": 0.0,
        "energy": 0.87,
        "activity": 0.95,
        "geometry": {
          "type": "LineString",
          "coordinates": [
            [-77.0365, 38.8977],
            [-77.0341, 38.8992]
          ]
        }
      }
    ]
  },
  "links": [
    {
      "href": "{api_root}/datastreams/ds-lob-001",
      "rel": "datastream"
    }
  ]
}
```

### 7.4 Triangulated Position Observation

```json
{
  "id": "obs-tri-2026-02-20T14-30-00-000",
  "phenomenonTime": "2026-02-20T14:30:00.000Z",
  "resultTime": "2026-02-20T14:30:00.050Z",
  "parameters": {
    "contributingArrays": ["mic-array-001", "mic-array-002", "mic-array-003"],
    "numArrayPairs": 3,
    "meanRayToRayDistance": 0.45
  },
  "result": {
    "position": {
      "type": "Point",
      "coordinates": [-77.0355, 38.8985, 15.2]
    },
    "uncertaintyEllipse": {
      "type": "Polygon",
      "coordinates": [[
        [-77.0357, 38.8984],
        [-77.0353, 38.8984],
        [-77.0353, 38.8986],
        [-77.0357, 38.8986],
        [-77.0357, 38.8984]
      ]]
    },
    "horizontalAccuracyM": 1.2,
    "verticalAccuracyM": 3.5,
    "confidence": 0.82
  },
  "links": [
    {
      "href": "{api_root}/datastreams/ds-triangulated-pos",
      "rel": "datastream"
    }
  ]
}
```

---

## 8. Control Streams (Part 2) — Actuation channel

Control streams represent channels for sending commands to the system.

### 8.1 Detection Parameters Control Stream

```json
{
  "id": "cs-detection-params-001",
  "name": "Detection Parameters Control — Array #001",
  "description": "Control stream for adjusting SSL/SST detection parameters at runtime. Accepts commands to modify energy threshold (E_T), new source probability threshold (T_new), frames-to-confirm (F_new), and false positive probability (P_false).",
  "validTime": {"start": "2026-02-01T09:00:00Z"},
  "formats": ["application/json"],
  "inputName": "detection_params",
  "controlledProperties": [
    "urn:x-odas:property:detection-threshold",
    "urn:x-odas:property:tracking-sensitivity"
  ],
  "issueTime": null,
  "executionTime": null,
  "live": true,
  "async": false,
  "links": [
    {
      "href": "{api_root}/systems/odas-config-actuator-001",
      "rel": "system",
      "title": "Configuration Actuator"
    },
    {
      "href": "{api_root}/controlstreams/cs-detection-params-001/commands",
      "rel": "commands",
      "title": "Issued commands"
    },
    {
      "href": "{api_root}/controlstreams/cs-detection-params-001/schema",
      "rel": "schema",
      "title": "Command parameters schema"
    }
  ]
}
```

**SOSA/SSN justification:**
- `sosa:Actuator` + `sosa:actsOnProperty` → the actuator acts on the `detection-threshold` and `tracking-sensitivity` properties
- The `controlledProperties` are `sosa:ActuatableProperty` instances

---

## 9. Commands (Part 2) — `sosa:Actuation`

Commands represent individual actuation requests.

### 9.1 Set Detection Threshold Command

```json
{
  "id": "cmd-set-threshold-001",
  "issueTime": "2026-02-20T14:35:00Z",
  "executionTime": {"start": "2026-02-20T14:35:00.005Z", "end": "2026-02-20T14:35:00.005Z"},
  "sender": "urn:x-odas:user:operator-1",
  "currentStatus": "COMPLETED",
  "parameters": {
    "energyThreshold": 400,
    "reason": "Lowering threshold to detect quieter sources in low-noise environment"
  },
  "links": [
    {
      "href": "{api_root}/controlstreams/cs-detection-params-001",
      "rel": "controlstream",
      "title": "Parent control stream"
    },
    {
      "href": "{api_root}/commands/cmd-set-threshold-001/status",
      "rel": "status",
      "title": "Command status history"
    }
  ]
}
```

### 9.2 Command Status

```json
{
  "id": "status-cmd-001-completed",
  "reportTime": "2026-02-20T14:35:00.005Z",
  "statusCode": "COMPLETED",
  "percentCompletion": 100,
  "executionTime": {"start": "2026-02-20T14:35:00.005Z", "end": "2026-02-20T14:35:00.005Z"},
  "message": "Energy threshold updated from 600 to 400. Change effective immediately for all subsequent SSL frames."
}
```

---

## 10. Complete SOSA/SSN Ontology Coverage Audit

| SOSA/SSN Class | CSAPI Resource | Instance in This Model | Notes |
|---|---|---|---|
| **sosa:Platform** | System (`featureType: sosa:Platform`) | XMOS xCORE Board | Hosts sensors and systems |
| **sosa:Sensor** | System (`featureType: sosa:Sensor`) | Mic Array, Individual Mics, SSL Module, SST Module | Physical + software sensors |
| **sosa:Actuator** | System (`featureType: sosa:Actuator`) | Config Controller | Modifies system parameters |
| **ssn:System** | System (`featureType: sosa:System`) | DSP Pipeline, Triangulation Engine | Composite processing systems |
| **sosa:Procedure** | Procedure | 5 procedures (audio capture, SRP-PHAT, particle filter, triangulation, config actuation) | ObservingProcedure + ActuatingProcedure |
| **sosa:ObservableProperty** | Property | DOA, Energy, Activity, Bearing, Triangulated Position | What sensors observe |
| **sosa:ActuatableProperty** | Property | Detection Threshold, Tracking Sensitivity | What actuators control |
| **ssn:Deployment** | Deployment | Single-array + multi-array (with subdeployments) | Where/when systems are deployed |
| **sosa:FeatureOfInterest** | SamplingFeature | Conference Room 3A | Ultimate thing being characterized |
| **sosa:Sample** | SamplingFeature | Acoustic Monitoring Zone | Proxy for the FOI |
| **sosa:Observation** | Observation | SSL obs, SST obs, LOB obs, triangulation obs | Individual measurement events |
| **sosa:Result** | Observation.result | Embedded in each observation | The value of the measurement |
| **sosa:Actuation** | Command | Set threshold, set sensitivity | Commands changing system state |
| **ssn:Stimulus** | *(conceptual — not a CSAPI resource)* | Sound pressure waves | The physical event triggering the sensor |
| **ssn:Input** | *(described in Procedure via SensorML)* | Multi-channel PCM audio | What the procedure consumes |
| **ssn:Output** | *(described in Procedure via SensorML)* | SSL pots, SST tracks | What the procedure produces |
| DataStream | DataStream | 5 streams (SSL, SST, LOB, triangulation, status) | Links sensors to their observations |
| ControlStream | ControlStream | Detection params control | Links actuator to its commands |
| CommandStatus | CommandStatus | Status updates per command | Progress/completion of actuations |

### CSAPI Resource Type Usage: 9/9 (100%)

| Resource | Count | Subtypes Used |
|---|---|---|
| **systems** | 12 | Platform ×1, Sensor ×10, Actuator ×1, System ×2 |
| **deployments** | 4+ | Parent + sub-deployments |
| **procedures** | 5 | ObservingProcedure ×4, ActuatingProcedure ×1 |
| **samplingFeatures** | 2+ | FOI + Sample per deployment |
| **properties** | 7 | ObservableProperty ×5, ActuatableProperty ×2 |
| **datastreams** | 5 | Observation ×4, Status ×1 |
| **observations** | (continuous) | SSL, SST, LOB, triangulation frames |
| **controlStreams** | 1+ | Detection parameters |
| **commands** | (on demand) | Threshold/sensitivity adjustments |

### SOSA/SSN Property Field Usage

Every CSAPI resource property field specified in the OGC 23-001/23-002 schemas is populated in at least one instance above:

**System fields:** `featureType` ✅ `uid` ✅ `name` ✅ `description` ✅ `assetType` ✅ `validTime` ✅ `systemKind@link` ✅ `geometry` ✅ (null for components, set in deployment)

**Deployment fields:** `featureType` ✅ `uid` ✅ `name` ✅ `description` ✅ `validTime` ✅ `platform@link` ✅ `deployedSystems@link` ✅ `featuresOfInterest@link` ✅ `samplingFeatures@link` ✅ `subdeployments@link` ✅ `geometry` ✅ `bbox` ✅

**Procedure fields:** `featureType` ✅ `uid` ✅ `name` ✅ `description` ✅ `procedureType` ✅ `implementingSystems@link` ✅

**SamplingFeature fields:** `featureType` ✅ `uid` ✅ `name` ✅ `description` ✅ `sampledFeature@link` ✅ `sampleOf@link` ✅ `parentSystem@link` ✅ `geometry` ✅

**Property fields:** `id` ✅ `label` ✅ `description` ✅ `uniqueId` ✅ `baseProperty` ✅ `objectType` ✅

**DataStream fields:** `id` ✅ `name` ✅ `description` ✅ `validTime` ✅ `formats` ✅ `outputName` ✅ `observedProperties` ✅ `phenomenonTime` ✅ `resultTime` ✅ `resultType` ✅ `live` ✅ `type` ✅

**Observation fields:** `id` ✅ `phenomenonTime` ✅ `resultTime` ✅ `parameters` ✅ `result` ✅

**ControlStream fields:** `id` ✅ `name` ✅ `description` ✅ `validTime` ✅ `formats` ✅ `inputName` ✅ `controlledProperties` ✅ `issueTime` ✅ `executionTime` ✅ `live` ✅ `async` ✅

**Command fields:** `id` ✅ `issueTime` ✅ `executionTime` ✅ `sender` ✅ `currentStatus` ✅ `parameters` ✅

**CommandStatus fields:** `id` ✅ `reportTime` ✅ `statusCode` ✅ `percentCompletion` ✅ `executionTime` ✅ `message` ✅

---

## 11. Relationship Diagram

```
                           ┌────────────────────────────────┐
                           │    ssn:Deployment              │
                           │  "Campus Triangulation"        │
                           │    validTime, geometry          │
                           │    deployedSystems@link ──────►│──┐
                           │    platform@link ──────────────►│──┼──► sosa:Platform (XMOS Board)
                           │    featuresOfInterest@link ───►│──┼──► sosa:FeatureOfInterest (Room)
                           │    samplingFeatures@link ─────►│──┼──► sosa:Sample (Monitoring Zone)
                           │    subdeployments@link ───────►│──┼──► ssn:Deployment (per array)
                           └────────────────────────────────┘  │
                                                                │
                   ┌────────────────────────────────────────────┘
                   │
                   ▼
sosa:Platform ─── sosa:hosts ──► sosa:Sensor (Mic Array)
  (XMOS Board)                     │
                                   ├── ssn:hasSubSystem ──► sosa:Sensor (Mic #1..#7)
                                   │
                   ├── sosa:hosts ──► ssn:System (ODAS DSP)
                   │                    │
                   │                    ├── ssn:hasSubSystem ──► sosa:Sensor (SSL Module)
                   │                    │                           │
                   │                    │                           ├── ssn:implements ──► sosa:Procedure (SRP-PHAT)
                   │                    │                           │
                   │                    │                           ├── DataStream (SSL pots) ──► Observations
                   │                    │                           └── DataStream (LOBs) ──► Observations
                   │                    │
                   │                    └── ssn:hasSubSystem ──► sosa:Sensor (SST Module)
                   │                                                │
                   │                                                ├── ssn:implements ──► sosa:Procedure (Particle Filter)
                   │                                                └── DataStream (tracks) ──► Observations
                   │
                   └── sosa:hosts ──► sosa:Actuator (Config Controller)
                                        │
                                        ├── ssn:implements ──► sosa:Procedure (Config Actuation)
                                        ├── sosa:actsOnProperty ──► sosa:ActuatableProperty (Threshold)
                                        └── ControlStream ──► Commands ──► CommandStatus
```

---

## References

- W3C SOSA/SSN: https://www.w3.org/TR/vocab-ssn/
- OGC API - Connected Systems Part 1 (23-001): https://docs.ogc.org/is/23-001/23-001.html
- OGC API - Connected Systems Part 2 (23-002): https://docs.ogc.org/is/23-002/23-002.html
- IROS 2017 Paper: Lauzon et al., "Localization of RW-UAVs Using Particle Filtering Over Distributed Microphone Arrays"
- ODAS: https://github.com/introlab/odas
