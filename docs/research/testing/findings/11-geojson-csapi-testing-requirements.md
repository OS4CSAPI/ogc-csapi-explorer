# Section 11: GeoJSON CSAPI Testing Requirements

> **⚠️ REVIEW NOTICE — Phase 2D Issues H3, M3, L2 (Resolved)**
>
> This document contains strong GeoJSON extension research (property extraction
> patterns, `identifyResourceType()` logic, `parseValidTime()` transformation,
> `parseAssociationLinks()`, FeatureCollection parsing, geometry constraints)
> but also includes content that needs reorientation before implementation:
>
> **H3 — Server Data Validation Functions:** Sections 5, 7, 12, 17.3, and
> Appendix A contain `validateUID()`, `validateName()`, `validateFeatureType()`,
> `validateSystemType()`, and `validateAssetType()` functions that test whether
> server-provided values conform to the spec (valid URI format, SOSA vocabulary
> membership, enum allowlists). These are server-side concerns — our parser
> should _extract_ these values into typed properties, not _validate_ them.
> Parser tests should verify: `parseSystemFeature(fixture).uid === 'urn:...'`
> not: `isValidURI(feature.properties.uid) === true`. See review notices at
> each affected section.
>
> **M3 — Property Matrix Mirrors Spec Structure:** Section 4 catalogs every
> property across 5 resource types with 150+ validation rules. This is useful
> as a _reference_ for what properties exist and which are required, but should
> not be translated into 150+ individual test cases. Tests should be structured
> as: `parseSystemFeature(fullFixture) → verify all typed properties extracted`.
>
> **L2 — Over-Specified Test Organization:** Section 14 prescribes test file
> structure, describe-block hierarchy, and naming conventions before any code
> exists. Let test organization emerge from implementation following upstream
> patterns (see `src/wfs/featureprops.spec.ts`).
>
> **Directly usable content:** Sections 1-3 (scope, reuse strategy, extension
> requirements, `identifyResourceType()`), Section 8 (`parseValidTime()`),
> Section 9 (`parseAssociationLinks()`), Section 10 (FeatureCollection parsing),
> Section 11 (geometry constraints), Section 16 (anti-patterns — especially
> "DON'T re-test RFC 7946").
>
> **Prerequisite:** An output model (TypeScript interfaces) must be defined
> before these requirements can become concrete test cases.

**Research Plan:** [Research Plan 11: GeoJSON CSAPI Extensions Testing Requirements](../research-plans/11-geojson-csapi-testing-requirements.md)  
**Research Questions:** 74 questions about CSAPI Part 1 GeoJSON requirements, existing GeoJSON parser analysis, resource type differentiation across 5 types, property validation (URI formats, controlled vocabularies, temporal), geometry handling, featureType vocabulary, temporal property validation, link validation, FeatureCollection testing, error handling, specification examples, OpenSensorHub real-world examples, and parser implementation testing  
**Methodology:** 5-phase systematic analysis (CSAPI Part 1 GeoJSON requirements extraction for all 5 resource types → Existing parser analysis documenting RFC 7946 coverage and reuse strategy → Resource type deep dive defining Systems/Deployments/Procedures/SamplingFeatures/Properties specific testing → Example and fixture analysis from spec and OpenSensorHub → Test strategy design for integration with existing parser)  
**Research Time:** 2 hours (February 5, 2026)

**Primary Source(s):**

- [CSAPI Part 1 Specification (23-001)](https://docs.ogc.org/is/23-001/23-001.html) (GeoJSON encoding sections)
- [GeoJSON RFC 7946](https://tools.ietf.org/html/rfc7946)
- [CSAPI Implementation Guide](../../../planning/csapi-implementation-guide.md) (GeoJSON handler extensions)

**Supporting Resources:**

- Section 8: [CSAPI Specification Reference](08-csapi-specification-test-requirements.md) (reclassified from test requirements — spec property catalog, not test generator)
- [Part 1 Requirements Analysis](../../requirements/csapi-part1-requirements.md) (property definitions)
- [Format Requirements Analysis](../../requirements/csapi-format-requirements.md) (GeoJSON requirements)
- [OpenSensorHub Analysis](../../requirements/csapi-opensensorhub-analysis.md) (real-world GeoJSON examples)
- Section 6: [Meaningful vs Trivial Definition](06-meaningful-vs-trivial-definition.md) (quality context for test depth)
- Section 1-2: Upstream GeoJSON parser and tests (reuse strategy)

**Document Purpose:** Define comprehensive testing requirements for CSAPI-specific GeoJSON extensions building on existing RFC 7946 GeoJSON parser, focusing exclusively on CSAPI property validation (uniqueIdentifier, featureType, systemType, vocabularies), temporal properties (validTime), and resource-specific properties across 5 Part 1 resource types (Systems, Deployments, Procedures, SamplingFeatures, Properties) with clear reuse strategy to avoid duplicating standard GeoJSON tests, requiring ~30 fixtures and estimated 492-829 test lines.

---

## Table of Contents

1. [Testing Scope and Strategy](#1-testing-scope-and-strategy)
2. [Existing GeoJSON Parser Coverage](#2-existing-geojson-parser-coverage)
3. [CSAPI Extension Requirements](#3-csapi-extension-requirements)
4. [Resource Type Property Matrix](#4-resource-type-property-matrix)
5. [Common Property Validation](#5-common-property-validation)
6. [Resource-Specific Property Validation](#6-resource-specific-property-validation)
7. [Vocabulary Validation Requirements](#7-vocabulary-validation-requirements)
8. [Temporal Property Validation](#8-temporal-property-validation)
9. [Link Structure Validation](#9-link-structure-validation)
10. [FeatureCollection Testing](#10-featurecollection-testing)
11. [Geometry Handling Strategy](#11-geometry-handling-strategy)
12. [Error Handling Requirements](#12-error-handling-requirements)
13. [Fixture Requirements](#13-fixture-requirements)
14. [Test Organization](#14-test-organization)
15. [Test Depth and Priorities](#15-test-depth-and-priorities)
16. [Testing Anti-Patterns](#16-testing-anti-patterns)
17. [Implementation Notes](#17-implementation-notes)
18. [References](#18-references)

---

## 1. Testing Scope and Strategy

### 1.1 Core Testing Philosophy

**DO Test (CSAPI-Specific):**

- ✅ CSAPI property extraction from `properties` object
- ✅ CSAPI property validation (URI format, vocabulary values, temporal periods)
- ✅ Resource type differentiation via `featureType` property
- ✅ CSAPI-specific vocabularies (systemType, procedureType, assetType)
- ✅ Resource-specific property requirements (required vs optional)
- ✅ Association link structures (deployedSystems, subsystems, datastreams, etc.)
- ✅ Temporal validity periods (validTime encoding/parsing)
- ✅ CSAPI-specific error conditions

**DON'T Test (Inherited from Existing Parser):**

- ❌ RFC 7946 geometry validation (Point, LineString, Polygon, etc.)
- ❌ Coordinate validation (longitude [-180,180], latitude [-90,90])
- ❌ Polygon ring closure and right-hand rule
- ❌ CRS encoding (WGS 84 is default and only allowed CRS)
- ❌ Standard GeoJSON Feature structure (type, id, geometry, properties)
- ❌ FeatureCollection structure (type, features array)
- ❌ Basic JSON parsing

### 1.2 Extension Strategy

**Layered Testing Approach:**

```
┌─────────────────────────────────────────────────┐
│  CSAPI Property Validation Layer                │  ← NEW TESTING LAYER
│  - Property extraction                          │     (This specification)
│  - CSAPI vocabularies                           │
│  - Temporal validation                          │
│  - Link structures                              │
└─────────────────────────────────────────────────┘
         ↓ extends
┌─────────────────────────────────────────────────┐
│  RFC 7946 GeoJSON Compliance                    │  ← EXISTING COVERAGE
│  - Geometry validation                          │     (Assumed working)
│  - Coordinate validation                        │
│  - Feature structure                            │
└─────────────────────────────────────────────────┘
```

**Implementation Approach:**

- Extend existing GeoJSON parser with CSAPI property recognizers
- Add CSAPI-specific validation layer on top of RFC 7946 parsing
- Reuse existing geometry handling WITHOUT modification
- Focus test effort on CSAPI-specific semantics

### 1.3 Resource Type Coverage

**5 CSAPI Part 1 Resource Types:**

1. **Systems** (`sosa:System`)

   - Sensors, platforms, actuators, samplers
   - Spatial (geometry required or null)
   - Temporal validity (validTime optional)

2. **Deployments** (`sosa:Deployment`)

   - System deployment events
   - Spatial (geometry optional but typical)
   - Temporal validity (validTime REQUIRED - deployment period)

3. **Procedures** (`sosa:Procedure`)

   - Observation/sampling/actuation methods
   - **Non-spatial** (geometry must be null)
   - No temporal validity

4. **Sampling Features** (`sosa:Sample`)

   - Sampling geometry/methodology
   - Spatial (geometry required)
   - System-specific (always has parentSystem)

5. **Properties** (`sosa:Property`)
   - Observable/controllable/asserted properties
   - **Non-spatial** (geometry must be null)
   - Uses `itemType` property (NOT `featureType`)

---

## 2. Existing GeoJSON Parser Coverage

### 2.1 Upstream Parser Capabilities

**From ogc-client library analysis:**

**Existing Functionality:**

- Parses GeoJSON Feature and FeatureCollection structures
- Handles all 7 RFC 7946 geometry types:
  - Point, MultiPoint
  - LineString, MultiLineString
  - Polygon, MultiPolygon
  - GeometryCollection
- Validates coordinate ranges
- Validates polygon ring closure
- Uses `@types/geojson` TypeScript definitions
- Supports format negotiation (`application/geo+json`)
- WFS GeoJSON parsing (`parseFeaturePropsGeojson`)

**Test Coverage Examples:**

```typescript
// From src/wfs/featureprops.spec.ts
describe('parseFeatureProps and parseFeaturePropsGeojson', () => {
  it('geojson format', () => {
    expect(parseFeaturePropsGeojson(getFeatureStates200Geojson)).toEqual(
      expectedFeatureProps
    );
  });
});
```

### 2.2 What CSAPI Can Assume

**Validated by Existing Tests:**

- ✅ Geometry type validation (valid type values)
- ✅ Coordinate structure (arrays of correct depth)
- ✅ Coordinate ranges (lon [-180,180], lat [-90,90])
- ✅ Polygon ring closure (first = last coordinate)
- ✅ Feature structure (required type, geometry, properties)
- ✅ FeatureCollection structure (type, features array)
- ✅ CRS handling (WGS 84 default)

**CSAPI Tests Can Skip:**

- ❌ Re-testing geometry coordinate validation
- ❌ Re-testing polygon ring rules
- ❌ Re-testing basic Feature structure
- ❌ Re-testing coordinate order (longitude, latitude)

### 2.3 Reuse Strategy

**Integration Points:**

1. **Geometry Handling**: Call existing geometry parser, no additional validation
2. **Feature Structure**: Assume valid Feature structure, focus on `properties` object
3. **Coordinate Validation**: Trust existing validator, test CSAPI semantics
4. **Type Definitions**: Extend `@types/geojson` with CSAPI property interfaces

**Example Integration:**

```typescript
// CSAPI parser extends existing GeoJSON parser
import { Feature, FeatureCollection, Geometry } from 'geojson';

interface SystemGeoJSONProperties {
  uid: string;
  name: string;
  featureType: 'sosa:System' | 'sosa:Sensor' | 'sosa:Platform' | /* ... */;
  systemType?: string;
  assetType?: 'Equipment' | 'Human' | 'Simulation';
  validTime?: [string, string | null];
  // ... other CSAPI properties
}

type SystemFeature = Feature<Geometry | null, SystemGeoJSONProperties>;

// Parser focuses on CSAPI property extraction
function parseCSAPISystemFeature(feature: SystemFeature): System {
  // Geometry already validated by existing parser
  const { geometry } = feature;

  // CSAPI-specific validation
  validateCSAPIProperties(feature.properties);
  validateSystemType(feature.properties.systemType);
  validateValidTime(feature.properties.validTime);

  // Extract CSAPI properties
  return extractSystemProperties(feature);
}
```

---

## 3. CSAPI Extension Requirements

### 3.1 Property Extraction Requirements

**From GeoJSON Feature to CSAPI Resource:**

**Input (GeoJSON Feature):**

```json
{
  "type": "Feature",
  "id": "sensor123",
  "geometry": {
    "type": "Point",
    "coordinates": [-122.08, 37.42, 25.5]
  },
  "properties": {
    "uid": "urn:x-sensor:id:sensor123",
    "name": "Temperature Sensor TS-001",
    "description": "High-precision temperature sensor",
    "featureType": "http://www.w3.org/ns/sosa/Sensor",
    "systemType": "http://www.w3.org/ns/sosa/Sensor",
    "assetType": "Equipment",
    "validTime": ["2024-01-01T00:00:00Z", null]
  },
  "links": [
    {
      "rel": "datastreams",
      "href": "/systems/sensor123/datastreams"
    }
  ]
}
```

**Output (CSAPI System Resource):**

```typescript
{
  id: "sensor123",
  uid: "urn:x-sensor:id:sensor123",
  name: "Temperature Sensor TS-001",
  description: "High-precision temperature sensor",
  featureType: "http://www.w3.org/ns/sosa/Sensor",
  systemType: "http://www.w3.org/ns/sosa/Sensor",
  assetType: "Equipment",
  validTime: {
    begin: new Date("2024-01-01T00:00:00Z"),
    end: null
  },
  geometry: {
    type: "Point",
    coordinates: [-122.08, 37.42, 25.5]
  },
  links: [
    {
      rel: "datastreams",
      href: "/systems/sensor123/datastreams"
    }
  ]
}
```

**Extraction Requirements:**

1. Extract `properties` object from GeoJSON Feature
2. Map CSAPI properties to resource object
3. Validate property types (string, URI, array, etc.)
4. Parse temporal properties (ISO 8601 → Date objects)
5. Preserve unknown properties (forward compatibility)
6. Extract links array
7. Preserve geometry (already validated)

### 3.2 Resource Type Recognition

**Feature Type Identification:**

**Via `featureType` Property:**

```typescript
// Systems
properties.featureType =
  'sosa:System' |
  'sosa:Sensor' |
  'sosa:Platform' |
  'sosa:Actuator' |
  'sosa:Sampler';

// Deployments
properties.featureType = 'sosa:Deployment';

// Procedures
properties.featureType =
  'sosa:Procedure' |
  'sosa:ObservingProcedure' |
  'sosa:SamplingProcedure' |
  'sosa:ActuatingProcedure';

// Sampling Features
properties.featureType = 'sosa:Sample';
```

**Via `itemType` Property (Properties Resource):**

```typescript
// Properties (collection-level, not feature-level)
itemType = 'sosa:Property';
```

**Recognition Logic:**

```typescript
function identifyResourceType(feature: Feature): ResourceType {
  const { featureType } = feature.properties;

  if (
    featureType.includes('sosa:System') ||
    featureType.includes('sosa:Sensor') ||
    featureType.includes('sosa:Platform') ||
    featureType.includes('sosa:Actuator') ||
    featureType.includes('sosa:Sampler')
  ) {
    return 'System';
  }

  if (featureType.includes('sosa:Deployment')) {
    return 'Deployment';
  }

  if (featureType.includes('sosa:Procedure')) {
    return 'Procedure';
  }

  if (featureType.includes('sosa:Sample')) {
    return 'SamplingFeature';
  }

  throw new Error(`Unknown CSAPI feature type: ${featureType}`);
}
```

### 3.3 Validation Layer Requirements

> **⚠️ REVIEW NOTICE (H3):** Rules 1 and 2 below (URI Validation, Vocabulary
> Validation) are server-side data quality concerns. Our parser extracts
> `uid`, `systemType`, `featureType` as string values — it does not need to
> validate their format or vocabulary membership. Rule 3 (Temporal Validation)
> is partially legitimate: parsing ISO 8601 strings into Date objects is parser
> behavior, but enforcing start ≤ end ordering is a data quality check.
> **Reframe as:** What properties to extract and what TypeScript types they map to.

**Property Validation Rules:**

1. **URI Validation**:

   - `uid` must be valid URI (preferably URN per RFC 8141)
   - `systemType`, `procedureType`, `featureType` must be valid URIs
   - Vocabulary URIs must match SOSA/SSN namespace

2. **Vocabulary Validation**:

   - `systemType` values from SOSA vocabulary
   - `procedureType` values from Table 16 (CSAPI Part 1)
   - `assetType` values: Equipment | Human | Simulation

3. **Temporal Validation**:

   - `validTime` must be ISO 8601 period or instant
   - Support open-ended intervals: `[start, null]`
   - Support closed intervals: `[start, end]`
   - Validate start ≤ end for closed intervals

4. **Required Property Validation**:

   - Per resource type (see Section 4)
   - Fail if required property missing
   - Warn for unknown properties (forward compatibility)

5. **Association Validation**:
   - `deployedSystems`, `subsystems`, etc. must be arrays
   - Array items must be valid links or inline features
   - Links must have `href` and `rel` properties

---

## 4. Resource Type Property Matrix

> **⚠️ REVIEW NOTICE (M3):** The property tables below catalog every property
> across 5 resource types with detailed validation rules. This is valuable as
> a _specification reference_ for what properties exist, which are required,
> and what their types are. However, these 150+ validation rules should NOT
> become 150+ individual test cases. Parser tests should be structured as:
> `parseSystemFeature(fullFixture) → assert all typed properties extracted`
> using a small number of representative fixtures per resource type.
> The "Validation" column describes spec constraints on server data, not
> parser behavior — our parser extracts values, it doesn't police them.

### 4.1 Systems Resource Properties

**Feature Type:** `sosa:System` (or subtypes: `sosa:Sensor`, `sosa:Platform`, `sosa:Actuator`, `sosa:Sampler`)

**Common Properties:**
| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `uid` | URI (string) | Yes | Unique persistent identifier (preferably URN) |
| `name` | string | Yes | Human-readable name |
| `description` | string | No | Detailed description |
| `featureType` | URI (string) | Yes | Resource ontology type from SOSA/SSN |

**System-Specific Properties:**
| Property | Type | Required | Description | Validation |
|----------|------|----------|-------------|------------|
| `systemType` | URI (string) | No | System type from SOSA vocabulary | Must be SOSA URI if present |
| `assetType` | enum | No | Equipment \| Human \| Simulation | Exact value match |
| `validTime` | [ISO 8601, ISO 8601 \| null] | No | Temporal validity period | ISO 8601 format, start ≤ end |
| `subsystems` | array | No | Array of System links or features | Valid link structure |
| `deployments` | array | No | Array of Deployment links | Valid link structure |
| `procedures` | array | No | Array of Procedure links | Valid link structure |
| `samplingFeatures` | array | No | Array of Sampling Feature links | Valid link structure |
| `datastreams` | array | No | Array of Datastream links | Valid link structure |
| `controlstreams` | array | No | Array of Controlstream links | Valid link structure |

**Geometry Requirements:**

- Geometry: Point, MultiPoint, LineString, Polygon, or null
- Typically Point for fixed sensors, LineString for mobile platforms
- null geometry allowed (non-localized systems)

**Test Requirements:**

- ✅ Parse all common + system-specific properties
- ✅ Validate systemType vocabulary (if present)
- ✅ Validate assetType enum values (if present)
- ✅ Parse validTime temporal periods (if present)
- ✅ Parse association arrays
- ✅ Handle null geometry
- ✅ Handle missing optional properties

### 4.2 Deployments Resource Properties

**Feature Type:** `sosa:Deployment`

**Common Properties:** uid, name, description, featureType (same as Systems)

**Deployment-Specific Properties:**
| Property | Type | Required | Description | Validation |
|----------|------|----------|-------------|------------|
| `validTime` | [ISO 8601, ISO 8601 \| null] | **Yes** | Deployment period (REQUIRED for Deployments) | ISO 8601 format, start ≤ end |
| `deployedSystems` | array | **Yes** | Systems deployed (at least one) | Non-empty array, valid links |
| `deploymentType` | URI (string) | No | Deployment type URI | Valid URI format |
| `platform` | Feature | No | Platform feature (vessel, aircraft, etc.) | Valid Feature structure |
| `featuresOfInterest` | array | No | Features being observed/controlled | Valid link structure |
| `samplingFeatures` | array | No | Sampling features used | Valid link structure |
| `datastreams` | array | No | Datastreams from deployment | Valid link structure |
| `controlstreams` | array | No | Controlstreams from deployment | Valid link structure |
| `subdeployments` | array | No | Nested subdeployments | Valid link structure |

**Geometry Requirements:**

- Geometry: Any RFC 7946 type or null
- Typically Polygon for spatial extent, Point for fixed location
- null for non-spatial deployments

**Test Requirements:**

- ✅ Validate validTime is present (required for Deployments)
- ✅ Validate deployedSystems is present and non-empty
- ✅ Parse deployment period (closed or open-ended)
- ✅ Handle platform Feature extraction
- ✅ Parse subdeployments hierarchy
- ❌ Fail if validTime missing
- ❌ Fail if deployedSystems missing or empty

### 4.3 Procedures Resource Properties

**Feature Type:** `sosa:Procedure` (or subtypes: `sosa:ObservingProcedure`, `sosa:SamplingProcedure`, `sosa:ActuatingProcedure`)

**Common Properties:** uid, name, description, featureType (same as Systems)

**Procedure-Specific Properties:**
| Property | Type | Required | Description | Validation |
|----------|------|----------|-------------|------------|
| `procedureType` | URI (string) | **Yes** | Procedure type from Table 16 | Must be valid URI from vocabulary |
| `implementingSystems` | array | No | Systems implementing this procedure | Valid link structure |

**Geometry Requirements:**

- **Geometry MUST be null** (Procedures are non-spatial)
- Parser MUST reject non-null geometry for Procedures

**Test Requirements:**

- ✅ Validate procedureType vocabulary
- ✅ Parse implementingSystems array
- ✅ Validate geometry is null
- ❌ Fail if geometry is not null
- ❌ Fail if procedureType missing

### 4.4 Sampling Features Resource Properties

**Feature Type:** `sosa:Sample`

**Common Properties:** uid, name, description, featureType (same as Systems)

**Sampling Feature-Specific Properties:**
| Property | Type | Required | Description | Validation |
|----------|------|----------|-------------|------------|
| `samplingFeatureType` | URI (string) | No | Sampling feature type URI | Valid URI format |
| `parentSystem` | Link or inline System | **Yes** | System that created sampling feature | Valid link or Feature |
| `sampledFeature` | Link or inline Feature | **Yes** | Ultimate feature of interest | Valid link or Feature |
| `sampleOf` | array | No | Sub-sampling relationships | Valid link structure |
| `datastreams` | array | No | Datastreams from this sampling feature | Valid link structure |
| `controlstreams` | array | No | Controlstreams from this sampling feature | Valid link structure |

**Geometry Requirements:**

- Geometry: Any RFC 7946 type (typically NOT null)
- Represents sampling geometry (point, trajectory, footprint, etc.)

**Test Requirements:**

- ✅ Validate parentSystem is present
- ✅ Validate sampledFeature is present
- ✅ Parse sub-sampling relationships (sampleOf)
- ✅ Handle inline Features vs links
- ❌ Fail if parentSystem missing
- ❌ Fail if sampledFeature missing

### 4.5 Properties Resource Properties

**Item Type:** `sosa:Property` (uses `itemType`, not `featureType`)

**Common Properties:** uid, name, description (NOT featureType)

**Property-Specific Properties:**
| Property | Type | Required | Description | Validation |
|----------|------|----------|-------------|------------|
| `baseProperty` | Link or Property resource | No | Base property (inheritance) | Valid link or inline Property |
| `objectType` | URI (string) | No | Kind of object/feature | Valid URI format |

**Geometry Requirements:**

- **Geometry MUST be null** (Properties are non-spatial)
- Properties resource does NOT use `featureType` property
- Uses `itemType = "sosa:Property"` at collection level

**Test Requirements:**

- ✅ Validate geometry is null
- ✅ Handle absence of featureType property
- ✅ Parse baseProperty (inline or link)
- ✅ Validate objectType URI (if present)
- ❌ Fail if geometry is not null

---

## 5. Common Property Validation

> **⚠️ REVIEW NOTICE (H3 — Core Section):** This section defines
> `validateUID()`, `validateName()`, and `validateFeatureType()` functions
> that test whether server-provided values conform to URI format rules and
> SOSA vocabulary membership. These are server data validation concerns —
> our parser should _extract_ these values into typed properties, not
> _validate_ them against the spec.
>
> **What to keep:** The property descriptions, types, and examples are useful
> reference for building TypeScript interfaces and understanding what the
> parser needs to extract from `feature.properties`.
>
> **What to reframe:** Replace `validateUID(uid): boolean` with
> `parseSystemFeature(fixture).uid === 'urn:...'` — test that extraction works,
> not that the value is a valid URI. The ✅/❌ test case lists describe spec
> conformance, not parser behavior.

### 5.1 Required Common Properties

**All CSAPI Resources (except Properties):**

**uid (Unique Identifier):**

```typescript
// Required: Yes
// Type: URI (string)
// Format: Valid URI, preferably URN per RFC 8141
// Examples:
//   - "urn:uuid:31f6865e-f438-430e-9b57-f965a21ee255"
//   - "urn:x-sensor:id:sensor123"
//   - "http://example.com/sensors/sensor123"

// Validation:
function validateUID(uid: string): boolean {
  // Must be valid URI
  try {
    new URL(uid);
    return true;
  } catch {
    // Check if valid URN
    return /^urn:[a-zA-Z0-9][a-zA-Z0-9-]{1,31}:.+/.test(uid);
  }
}

// Test Cases:
✅ "urn:uuid:550e8400-e29b-41d4-a716-446655440000"
✅ "urn:x-sensor:id:temp-sensor-01"
✅ "http://example.com/systems/123"
❌ "sensor123" (not a URI)
❌ "urn:invalid" (incomplete URN)
❌ "" (empty string)
```

**name (Human-Readable Name):**

```typescript
// Required: Yes
// Type: string (non-empty)
// Examples:
//   - "Temperature Sensor TS-001"
//   - "Weather Station Alpha"
//   - "Marine Deployment 2024-01"

// Validation:
function validateName(name: string): boolean {
  return typeof name === 'string' && name.trim().length > 0;
}

// Test Cases:
✅ "Weather Station"
✅ "Sensor-123"
❌ "" (empty string)
❌ "   " (whitespace only)
❌ null (not a string)
```

**featureType (Resource Ontology Type):**

```typescript
// Required: Yes (except Properties resource)
// Type: URI (string) from SOSA/SSN vocabulary
// Examples:
//   - "http://www.w3.org/ns/sosa/System"
//   - "http://www.w3.org/ns/sosa/Sensor"
//   - "sosa:Platform" (shorthand)

// Validation:
const VALID_FEATURE_TYPES = [
  'http://www.w3.org/ns/sosa/System',
  'http://www.w3.org/ns/sosa/Sensor',
  'http://www.w3.org/ns/sosa/Platform',
  'http://www.w3.org/ns/sosa/Actuator',
  'http://www.w3.org/ns/sosa/Sampler',
  'http://www.w3.org/ns/sosa/Deployment',
  'http://www.w3.org/ns/sosa/Procedure',
  'http://www.w3.org/ns/sosa/ObservingProcedure',
  'http://www.w3.org/ns/sosa/SamplingProcedure',
  'http://www.w3.org/ns/sosa/ActuatingProcedure',
  'http://www.w3.org/ns/sosa/Sample',
  // Shorthand versions
  'sosa:System', 'sosa:Sensor', 'sosa:Platform', /* ... */
];

function validateFeatureType(featureType: string): boolean {
  return VALID_FEATURE_TYPES.includes(featureType);
}

// Test Cases:
✅ "http://www.w3.org/ns/sosa/Sensor"
✅ "sosa:Platform"
❌ "http://example.com/MyType" (not from SOSA/SSN)
❌ "Sensor" (not a URI)
❌ "" (empty string)
```

### 5.2 Optional Common Properties

**description (Detailed Description):**

```typescript
// Required: No
// Type: string
// Validation: Allow any string (including empty)

// Test Cases:
✅ "High-precision temperature sensor for marine environments"
✅ "" (empty string allowed)
✅ undefined (property absent allowed)
✅ null (property null allowed)
```

**links (HATEOAS Navigation Links):**

```typescript
// Required: No
// Type: array of Link objects
// Structure: { rel: string, href: string, type?: string, title?: string }

interface Link {
  rel: string;      // Link relationship
  href: string;     // Target URL
  type?: string;    // Media type
  title?: string;   // Human-readable title
}

// Validation:
function validateLinks(links: unknown): boolean {
  if (links === undefined || links === null) return true; // Optional
  if (!Array.isArray(links)) return false;

  return links.every(link =>
    typeof link.rel === 'string' &&
    typeof link.href === 'string' &&
    (link.type === undefined || typeof link.type === 'string') &&
    (link.title === undefined || typeof link.title === 'string')
  );
}

// Test Cases:
✅ [{ rel: "self", href: "/systems/123" }]
✅ [{ rel: "datastreams", href: "/systems/123/datastreams", type: "application/json" }]
✅ [] (empty array)
✅ undefined (property absent)
❌ [{ rel: "self" }] (missing href)
❌ [{ href: "/systems/123" }] (missing rel)
❌ "not-an-array"
```

---

## 6. Resource-Specific Property Validation

### 6.1 Systems Resource Validation

**systemType (System Type URI):**

```typescript
// Required: No
// Type: URI (string) from SOSA vocabulary
// Allowed Values:
const SYSTEM_TYPES = [
  'http://www.w3.org/ns/sosa/System',
  'http://www.w3.org/ns/sosa/Sensor',
  'http://www.w3.org/ns/sosa/Platform',
  'http://www.w3.org/ns/sosa/Actuator',
  'http://www.w3.org/ns/sosa/Sampler',
  // Shorthand
  'sosa:System', 'sosa:Sensor', 'sosa:Platform', 'sosa:Actuator', 'sosa:Sampler'
];

// Test Cases:
✅ "http://www.w3.org/ns/sosa/Sensor"
✅ "sosa:Platform"
✅ undefined (optional property)
❌ "http://example.com/CustomSensor" (not from SOSA)
❌ "Sensor" (not a URI)
```

**assetType (Asset Type Enum):**

```typescript
// Required: No
// Type: enum (string)
// Allowed Values: "Equipment" | "Human" | "Simulation"

// Test Cases:
✅ "Equipment"
✅ "Human"
✅ "Simulation"
✅ undefined (optional property)
❌ "Robot" (not in enum)
❌ "equipment" (case-sensitive)
❌ 123 (not a string)
```

**subsystems (Subsystem Links/Features):**

```typescript
// Required: No
// Type: array of Links or inline System features
// Validation: Array items must be valid links or Features

// Test Cases:
✅ [{ rel: "subsystem", href: "/systems/child1" }]
✅ [{ type: "Feature", geometry: {...}, properties: {...} }] (inline)
✅ [] (empty array)
✅ undefined (property absent)
❌ [{ rel: "subsystem" }] (missing href)
❌ "not-an-array"
```

### 6.2 Deployments Resource Validation

**validTime (Deployment Period - REQUIRED):**

```typescript
// Required: YES (unique to Deployments)
// Type: [ISO 8601 string, ISO 8601 string | null]
// Format: [startTime, endTime] where endTime can be null (open-ended)

// Validation:
function validateDeploymentValidTime(validTime: unknown): boolean {
  if (!Array.isArray(validTime) || validTime.length !== 2) return false;

  const [start, end] = validTime;

  // Start must be valid ISO 8601
  if (!isValidISO8601(start)) return false;

  // End must be valid ISO 8601 or null
  if (end !== null && !isValidISO8601(end)) return false;

  // If both defined, start <= end
  if (end !== null && new Date(start) > new Date(end)) return false;

  return true;
}

// Test Cases:
✅ ["2024-01-01T00:00:00Z", "2024-12-31T23:59:59Z"] (closed interval)
✅ ["2024-01-01T00:00:00Z", null] (open-ended)
✅ ["2024-06-15T12:00:00Z", "2024-06-15T12:00:00Z"] (instant)
❌ undefined (required for Deployments)
❌ ["2024-01-01T00:00:00Z"] (missing end)
❌ ["2024-12-31T23:59:59Z", "2024-01-01T00:00:00Z"] (start > end)
❌ ["invalid", null] (invalid ISO 8601)
```

**deployedSystems (Deployed System Links - REQUIRED):**

```typescript
// Required: YES
// Type: array of Links (non-empty)
// Validation: At least one system link

// Test Cases:
✅ [{ rel: "system", href: "/systems/sensor1" }]
✅ [
    { rel: "system", href: "/systems/sensor1" },
    { rel: "system", href: "/systems/sensor2" }
  ]
❌ undefined (required for Deployments)
❌ [] (empty array - at least one system required)
❌ [{ rel: "system" }] (missing href)
```

### 6.3 Procedures Resource Validation

**procedureType (Procedure Type URI - REQUIRED):**

```typescript
// Required: YES
// Type: URI (string) from Table 16 (CSAPI Part 1)
// Allowed Values:
const PROCEDURE_TYPES = [
  'http://www.w3.org/ns/sosa/Procedure',
  'http://www.w3.org/ns/sosa/ObservingProcedure',
  'http://www.w3.org/ns/sosa/SamplingProcedure',
  'http://www.w3.org/ns/sosa/ActuatingProcedure',
  // Shorthand
  'sosa:Procedure', 'sosa:ObservingProcedure', 'sosa:SamplingProcedure', 'sosa:ActuatingProcedure'
];

// Test Cases:
✅ "http://www.w3.org/ns/sosa/ObservingProcedure"
✅ "sosa:SamplingProcedure"
❌ undefined (required for Procedures)
❌ "http://example.com/MyProcedure" (not from vocabulary)
❌ "Procedure" (not a URI)
```

**Geometry Constraint (MUST be null):**

```typescript
// Procedures are non-spatial
// Geometry MUST be null

// Test Cases:
✅ null
❌ { type: "Point", coordinates: [-122.08, 37.42] }
❌ undefined (must be explicitly null)
```

### 6.4 Sampling Features Resource Validation

**parentSystem (Parent System Link - REQUIRED):**

```typescript
// Required: YES
// Type: Link or inline System feature
// Validation: Must be valid link or Feature

// Test Cases:
✅ { rel: "system", href: "/systems/parent123" }
✅ { type: "Feature", geometry: {...}, properties: { featureType: "sosa:System", ... } }
❌ undefined (required for Sampling Features)
❌ {} (empty object)
❌ "system-id" (not a valid link structure)
```

**sampledFeature (Feature of Interest Link - REQUIRED):**

```typescript
// Required: YES
// Type: Link or inline Feature
// Validation: Must be valid link or Feature

// Test Cases:
✅ { rel: "foi", href: "http://dbpedia.org/resource/Seawater" }
✅ { type: "Feature", geometry: {...}, properties: {...} }
❌ undefined (required for Sampling Features)
❌ {} (empty object)
```

### 6.5 Properties Resource Validation

**Geometry Constraint (MUST be null):**

```typescript
// Properties are non-spatial
// Geometry MUST be null

// Test Cases:
✅ null
❌ { type: "Point", coordinates: [-122.08, 37.42] }
❌ undefined (must be explicitly null)
```

**featureType Absence:**

```typescript
// Properties resource does NOT use featureType property
// Uses itemType at collection level instead

// Test Cases:
✅ properties object WITHOUT featureType property
❌ Presence of featureType property (not used for Properties)
```

---

## 7. Vocabulary Validation Requirements

> **⚠️ REVIEW NOTICE (H3):** The vocabulary lists below are useful as
> _reference material_ for understanding CSAPI resource type ontology.
> However, testing whether the parser rejects values outside these lists
> (`validateSystemType()`, `validateAssetType()`) is server data validation.
> Our parser extracts `systemType` as a string — it does not need to check
> it against an allowlist. These lists inform TypeScript type definitions
> (e.g., `type AssetType = 'Equipment' | 'Human' | 'Simulation'`) but
> should not generate vocabulary-membership test cases.

### 7.1 SOSA/SSN Vocabulary

**Namespace:** `http://www.w3.org/ns/sosa/`

**System Types:**

- `sosa:System` - Generic system
- `sosa:Sensor` - Observing system
- `sosa:Platform` - Hosting system
- `sosa:Actuator` - Acting system
- `sosa:Sampler` - Sampling system

**Deployment Types:**

- `sosa:Deployment`

**Procedure Types:**

- `sosa:Procedure` - Generic procedure
- `sosa:ObservingProcedure` - Observation method
- `sosa:SamplingProcedure` - Sampling method
- `sosa:ActuatingProcedure` - Actuation method

**Sampling Feature Types:**

- `sosa:Sample`

**Property Types:**

- `sosa:Property` (used as itemType, not featureType)
- `sosa:ObservableProperty` - Observable
- `sosa:ActuatableProperty` - Controllable

### 7.2 Asset Type Vocabulary

**Namespace:** CSAPI-specific (not SOSA)

**Allowed Values:**

- `Equipment` - Physical hardware
- `Human` - Human observer/operator
- `Simulation` - Simulated system

**Validation:**

- Exact case-sensitive match
- No variations or extensions

### 7.3 Vocabulary Testing Strategy

**DO Test:**

- ✅ Valid SOSA URI recognition (full URI and shorthand)
- ✅ Invalid URI rejection (non-SOSA namespace)
- ✅ Case-sensitive enum matching (assetType)
- ✅ Vocabulary completeness (all expected values)

**DON'T Test:**

- ❌ SOSA ontology semantics (reasoning, inference)
- ❌ URI dereferenceability (network calls)
- ❌ Vocabulary versioning (assume current)

**Test Implementation:**

```typescript
describe('SOSA Vocabulary Validation', () => {
  describe('systemType', () => {
    it('accepts valid SOSA system type URIs', () => {
      const validTypes = ['http://www.w3.org/ns/sosa/Sensor', 'sosa:Platform'];
      validTypes.forEach((type) => {
        expect(validateSystemType(type)).toBe(true);
      });
    });

    it('rejects non-SOSA URIs', () => {
      expect(validateSystemType('http://example.com/Sensor')).toBe(false);
    });
  });

  describe('assetType', () => {
    it('accepts valid asset type enums', () => {
      expect(validateAssetType('Equipment')).toBe(true);
      expect(validateAssetType('Human')).toBe(true);
      expect(validateAssetType('Simulation')).toBe(true);
    });

    it('rejects invalid values', () => {
      expect(validateAssetType('equipment')).toBe(false); // case-sensitive
      expect(validateAssetType('Robot')).toBe(false); // not in vocab
    });
  });
});
```

---

## 8. Temporal Property Validation

### 8.1 validTime Property Structure

**Format:** Array of two ISO 8601 strings: `[startTime, endTime]`

**ISO 8601 Temporal Formats:**

```
Date-time:     2024-01-15T10:30:00Z
               2024-01-15T10:30:00+00:00
               2024-01-15T10:30:00.123Z

Date:          2024-01-15

Open-ended:    [2024-01-01T00:00:00Z, null]
Closed:        [2024-01-01T00:00:00Z, 2024-12-31T23:59:59Z]
Instant:       [2024-06-15T12:00:00Z, 2024-06-15T12:00:00Z]
```

### 8.2 Temporal Validation Rules

**Rule 1: Array Structure**

```typescript
// validTime must be array of length 2
validTime: [string, string | null]

✅ ["2024-01-01T00:00:00Z", "2024-12-31T23:59:59Z"]
✅ ["2024-01-01T00:00:00Z", null]
❌ "2024-01-01T00:00:00Z" (not an array)
❌ ["2024-01-01T00:00:00Z"] (length 1)
❌ ["2024-01-01T00:00:00Z", "2024-12-31T23:59:59Z", "2025-01-01T00:00:00Z"] (length 3)
```

**Rule 2: ISO 8601 Format**

```typescript
// Both elements must be valid ISO 8601 strings (or null for end)

✅ ["2024-01-15T10:30:00Z", null]
✅ ["2024-01-15T10:30:00+00:00", "2024-12-31T23:59:59Z"]
✅ ["2024-01-15", "2024-12-31"] (date-only format)
❌ ["01/15/2024", null] (invalid format)
❌ ["2024-01-15", "invalid"]
❌ [null, "2024-12-31T23:59:59Z"] (start cannot be null)
```

**Rule 3: Temporal Ordering**

```typescript
// If end is not null, start <= end

✅ ["2024-01-01T00:00:00Z", "2024-12-31T23:59:59Z"] (start < end)
✅ ["2024-06-15T12:00:00Z", "2024-06-15T12:00:00Z"] (start = end, instant)
✅ ["2024-01-01T00:00:00Z", null] (open-ended, no ordering check)
❌ ["2024-12-31T23:59:59Z", "2024-01-01T00:00:00Z"] (start > end)
```

### 8.3 Temporal Parsing Requirements

**Parse to Date Objects:**

```typescript
interface TemporalExtent {
  begin: Date;
  end: Date | null;
}

function parseValidTime(validTime: [string, string | null]): TemporalExtent {
  return {
    begin: new Date(validTime[0]),
    end: validTime[1] ? new Date(validTime[1]) : null
  };
}

// Test Cases:
✅ ["2024-01-01T00:00:00Z", null] → { begin: Date(2024-01-01...), end: null }
✅ ["2024-01-01T00:00:00Z", "2024-12-31T23:59:59Z"] → { begin: Date(...), end: Date(...) }
```

### 8.4 Temporal Property Test Cases

**Valid Cases:**

```typescript
describe('validTime parsing', () => {
  it('parses open-ended periods', () => {
    const validTime: [string, null] = ['2024-01-01T00:00:00Z', null];
    const result = parseValidTime(validTime);
    expect(result.begin).toEqual(new Date('2024-01-01T00:00:00Z'));
    expect(result.end).toBeNull();
  });

  it('parses closed periods', () => {
    const validTime: [string, string] = [
      '2024-01-01T00:00:00Z',
      '2024-12-31T23:59:59Z',
    ];
    const result = parseValidTime(validTime);
    expect(result.begin).toEqual(new Date('2024-01-01T00:00:00Z'));
    expect(result.end).toEqual(new Date('2024-12-31T23:59:59Z'));
  });

  it('parses temporal instants', () => {
    const validTime: [string, string] = [
      '2024-06-15T12:00:00Z',
      '2024-06-15T12:00:00Z',
    ];
    const result = parseValidTime(validTime);
    expect(result.begin).toEqual(result.end);
  });
});
```

**Invalid Cases:**

```typescript
describe('validTime validation errors', () => {
  it('rejects invalid array structure', () => {
    expect(() => parseValidTime('2024-01-01T00:00:00Z')).toThrow();
    expect(() => parseValidTime(['2024-01-01T00:00:00Z'])).toThrow();
  });

  it('rejects invalid ISO 8601 format', () => {
    expect(() => parseValidTime(['01/01/2024', null])).toThrow();
    expect(() => parseValidTime(['2024-01-01T00:00:00Z', 'invalid'])).toThrow();
  });

  it('rejects start > end', () => {
    expect(() =>
      parseValidTime(['2024-12-31T23:59:59Z', '2024-01-01T00:00:00Z'])
    ).toThrow();
  });
});
```

---

## 9. Link Structure Validation

### 9.1 CSAPI Link Object Structure

**Standard Link Object:**

```typescript
interface Link {
  rel: string; // Link relationship (REQUIRED)
  href: string; // Target URL (REQUIRED)
  type?: string; // Media type (OPTIONAL)
  title?: string; // Human-readable title (OPTIONAL)
}
```

**Example Links:**

```json
{
  "links": [
    {
      "rel": "self",
      "href": "/systems/sensor123",
      "type": "application/geo+json"
    },
    {
      "rel": "datastreams",
      "href": "/systems/sensor123/datastreams",
      "title": "Datastreams from this system"
    },
    {
      "rel": "subsystems",
      "href": "/systems/sensor123/subsystems"
    }
  ]
}
```

### 9.2 Link Relationship Types

**CSAPI-Specific rel Values:**

**Navigation Links:**

- `self` - Canonical resource URL
- `collection` - Parent collection
- `item` - Collection item

**Association Links (Systems):**

- `subsystems` - Child systems
- `deployments` - System deployments
- `procedures` - Implemented procedures
- `samplingFeatures` - Sampling features
- `datastreams` - Data output streams
- `controlstreams` - Control input streams

**Association Links (Deployments):**

- `deployedSystems` - Deployed system(s)
- `subdeployments` - Nested subdeployments
- `platform` - Deployment platform
- `featuresOfInterest` - Observed/controlled features

**Association Links (Sampling Features):**

- `parentSystem` - Creating system
- `sampledFeature` - Ultimate feature of interest
- `sampleOf` - Parent sampling feature (sub-sampling)

### 9.3 Link Validation Rules

**Required Properties:**

```typescript
// rel and href are REQUIRED
✅ { rel: "self", href: "/systems/123" }
❌ { href: "/systems/123" } (missing rel)
❌ { rel: "self" } (missing href)
```

**Optional Properties:**

```typescript
// type and title are OPTIONAL
✅ { rel: "self", href: "/systems/123", type: "application/geo+json" }
✅ { rel: "self", href: "/systems/123", title: "System 123" }
✅ { rel: "self", href: "/systems/123" } (no optional properties)
```

**href Format:**

```typescript
// href can be relative or absolute URL
✅ "/systems/123" (relative)
✅ "/systems/123/datastreams" (relative path)
✅ "http://example.com/systems/123" (absolute)
✅ "http://dbpedia.org/resource/Seawater" (external URI)
```

### 9.4 Association Link Arrays

**Array Validation:**

```typescript
// Association properties (subsystems, deployments, etc.) can be:
// 1. Array of Link objects
// 2. Array of inline Features
// 3. Mixed array (links + inline features)

// Valid Structures:
✅ [{ rel: "subsystem", href: "/systems/child1" }] (links only)
✅ [{ type: "Feature", geometry: {...}, properties: {...} }] (inline only)
✅ [
    { rel: "subsystem", href: "/systems/child1" },
    { type: "Feature", geometry: {...}, properties: {...} }
  ] (mixed)
✅ [] (empty array)
```

**Link Array Test Cases:**

```typescript
describe('Association link arrays', () => {
  it('parses link-only arrays', () => {
    const subsystems = [
      { rel: 'subsystem', href: '/systems/child1' },
      { rel: 'subsystem', href: '/systems/child2' },
    ];
    expect(parseAssociationLinks(subsystems)).toHaveLength(2);
  });

  it('parses inline feature arrays', () => {
    const subsystems = [
      {
        type: 'Feature',
        geometry: null,
        properties: { uid: '...', name: 'Child' },
      },
    ];
    expect(parseAssociationLinks(subsystems)).toHaveLength(1);
  });

  it('handles empty arrays', () => {
    expect(parseAssociationLinks([])).toHaveLength(0);
  });

  it('rejects invalid link structures', () => {
    const invalid = [{ rel: 'subsystem' }]; // missing href
    expect(() => parseAssociationLinks(invalid)).toThrow();
  });
});
```

---

## 10. FeatureCollection Testing

### 10.1 CSAPI FeatureCollection Structure

**Standard Structure:**

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "id": "system1",
      "geometry": { "type": "Point", "coordinates": [-122.08, 37.42] },
      "properties": { "uid": "...", "name": "System 1", ... }
    },
    {
      "type": "Feature",
      "id": "system2",
      "geometry": null,
      "properties": { "uid": "...", "name": "System 2", ... }
    }
  ],
  "links": [
    { "rel": "self", "href": "/systems" },
    { "rel": "next", "href": "/systems?offset=20" }
  ],
  "timeStamp": "2024-01-15T10:00:00Z",
  "numberMatched": 250,
  "numberReturned": 20
}
```

### 10.2 FeatureCollection Properties

**Required Properties:**

- `type`: "FeatureCollection" (required)
- `features`: Array of Feature objects (required, can be empty)

**Optional Properties:**

- `links`: Pagination and navigation links
- `timeStamp`: When collection was generated (ISO 8601)
- `numberMatched`: Total matching features (before pagination)
- `numberReturned`: Number of features in this response
- `bbox`: Bounding box of all features (inherited from RFC 7946)

### 10.3 FeatureCollection Validation

**Structure Validation:**

```typescript
describe('FeatureCollection structure', () => {
  it('parses valid feature collections', () => {
    const collection = {
      type: 'FeatureCollection',
      features: [
        {
          type: 'Feature',
          geometry: null,
          properties: { uid: '...', name: '...' },
        },
      ],
    };
    expect(parseFeatureCollection(collection)).toBeDefined();
  });

  it('handles empty feature arrays', () => {
    const collection = {
      type: 'FeatureCollection',
      features: [],
    };
    expect(parseFeatureCollection(collection).features).toHaveLength(0);
  });

  it('rejects invalid type', () => {
    const invalid = { type: 'Collection', features: [] };
    expect(() => parseFeatureCollection(invalid)).toThrow();
  });
});
```

**Pagination Links:**

```typescript
describe('Pagination links', () => {
  it('extracts pagination links', () => {
    const collection = {
      type: 'FeatureCollection',
      features: [],
      links: [
        { rel: 'self', href: '/systems' },
        { rel: 'next', href: '/systems?offset=20' },
        { rel: 'prev', href: '/systems?offset=0' },
      ],
    };
    const result = parseFeatureCollection(collection);
    expect(result.links).toHaveLength(3);
    expect(result.links.find((l) => l.rel === 'next')).toBeDefined();
  });
});
```

**Metadata Properties:**

```typescript
describe('Collection metadata', () => {
  it('parses timeStamp', () => {
    const collection = {
      type: 'FeatureCollection',
      features: [],
      timeStamp: '2024-01-15T10:00:00Z',
    };
    const result = parseFeatureCollection(collection);
    expect(result.timeStamp).toEqual(new Date('2024-01-15T10:00:00Z'));
  });

  it('parses pagination counts', () => {
    const collection = {
      type: 'FeatureCollection',
      features: [],
      numberMatched: 250,
      numberReturned: 20,
    };
    const result = parseFeatureCollection(collection);
    expect(result.numberMatched).toBe(250);
    expect(result.numberReturned).toBe(20);
  });
});
```

---

## 11. Geometry Handling Strategy

### 11.1 Geometry Reuse Policy

**DO NOT Re-test Geometry Validation:**

- ❌ Coordinate validation (lon [-180,180], lat [-90,90])
- ❌ Polygon ring closure (first = last coordinate)
- ❌ Polygon right-hand rule
- ❌ Geometry type validation
- ❌ Coordinate array depth
- ❌ CRS encoding

**DO Test Geometry Semantics:**

- ✅ Null geometry handling (per resource type)
- ✅ Geometry presence requirements
  - Procedures: MUST be null
  - Properties: MUST be null
  - Sampling Features: typically NOT null
  - Systems: can be null or valid geometry
  - Deployments: can be null or valid geometry

### 11.2 Geometry Presence Tests

**Procedures (Must be null):**

```typescript
describe('Procedure geometry constraints', () => {
  it('accepts null geometry for Procedures', () => {
    const feature = {
      type: 'Feature',
      geometry: null,
      properties: {
        uid: 'urn:example:procedure:1',
        name: 'Temperature Measurement',
        featureType: 'sosa:Procedure',
        procedureType: 'sosa:ObservingProcedure',
      },
    };
    expect(parseProcedureFeature(feature)).toBeDefined();
  });

  it('rejects non-null geometry for Procedures', () => {
    const feature = {
      type: 'Feature',
      geometry: { type: 'Point', coordinates: [-122.08, 37.42] },
      properties: {
        uid: 'urn:example:procedure:1',
        name: 'Temperature Measurement',
        featureType: 'sosa:Procedure',
        procedureType: 'sosa:ObservingProcedure',
      },
    };
    expect(() => parseProcedureFeature(feature)).toThrow(
      /Procedures cannot have geometry/
    );
  });
});
```

**Properties (Must be null):**

```typescript
describe('Property geometry constraints', () => {
  it('accepts null geometry for Properties', () => {
    const feature = {
      type: 'Feature',
      geometry: null,
      properties: {
        uid: 'urn:example:property:temperature',
        name: 'Air Temperature',
      },
    };
    expect(parsePropertyFeature(feature)).toBeDefined();
  });

  it('rejects non-null geometry for Properties', () => {
    const feature = {
      type: 'Feature',
      geometry: { type: 'Point', coordinates: [-122.08, 37.42] },
      properties: {
        uid: 'urn:example:property:temperature',
        name: 'Air Temperature',
      },
    };
    expect(() => parsePropertyFeature(feature)).toThrow(
      /Properties cannot have geometry/
    );
  });
});
```

**Systems/Deployments (null or valid):**

```typescript
describe('System geometry handling', () => {
  it('accepts null geometry', () => {
    const feature = {
      type: 'Feature',
      geometry: null,
      properties: { uid: '...', name: '...', featureType: 'sosa:System' },
    };
    expect(parseSystemFeature(feature).geometry).toBeNull();
  });

  it('accepts Point geometry', () => {
    const feature = {
      type: 'Feature',
      geometry: { type: 'Point', coordinates: [-122.08, 37.42] },
      properties: { uid: '...', name: '...', featureType: 'sosa:System' },
    };
    expect(parseSystemFeature(feature).geometry.type).toBe('Point');
  });

  // Coordinate validation inherited from existing parser - DON'T re-test
});
```

---

## 12. Error Handling Requirements

### 12.1 Error Categories

**Category 1: Missing Required Property**

```typescript
// Error when required property absent
// Applies to: uid, name, featureType, validTime (Deployments), etc.

Error: "Missing required property: {propertyName}"
HTTP Status: 400 Bad Request

// Examples:
"Missing required property: uid"
"Missing required property: validTime (required for Deployments)"
"Missing required property: deployedSystems"
```

**Category 2: Invalid Property Type**

```typescript
// Error when property has wrong type
// Applies to: string properties, arrays, objects

Error: "Invalid type for property '{propertyName}': expected {expectedType}, got {actualType}"
HTTP Status: 400 Bad Request

// Examples:
"Invalid type for property 'name': expected string, got number"
"Invalid type for property 'subsystems': expected array, got string"
```

**Category 3: Invalid Vocabulary Value**

> **⚠️ REVIEW NOTICE (H3):** This error category describes server-side
> rejection of invalid vocabulary values. Our parser extracts vocabulary
> values as strings — it does not reject unrecognized values. Remove or
> reframe as: parser extracts `systemType` value regardless of vocabulary.

```typescript
// Error when vocabulary value not recognized
// Applies to: featureType, systemType, procedureType, assetType

Error: "Invalid {propertyName} value: '{value}'. Must be one of: {allowedValues}"
HTTP Status: 400 Bad Request

// Examples:
"Invalid systemType value: 'http://example.com/Sensor'. Must be SOSA/SSN URI."
"Invalid assetType value: 'Robot'. Must be one of: Equipment, Human, Simulation"
```

**Category 4: Invalid URI Format**

> **⚠️ REVIEW NOTICE (H3):** This error category describes server-side
> rejection of malformed URIs. Our parser extracts URI values as strings —
> it does not validate URI format. Remove or reframe.

```typescript
// Error when URI property has invalid format
// Applies to: uid, systemType, procedureType, featureType

Error: "Invalid URI format for property '{propertyName}': {value}"
HTTP Status: 400 Bad Request

// Examples:
"Invalid URI format for property 'uid': sensor123"
"Invalid URI format for property 'systemType': Sensor"
```

**Category 5: Invalid Temporal Format**

```typescript
// Error when validTime has invalid format or ordering
// Applies to: validTime property

Error: "Invalid validTime: {reason}"
HTTP Status: 400 Bad Request

// Examples:
"Invalid validTime: must be array of length 2"
"Invalid validTime: start time is not valid ISO 8601"
"Invalid validTime: start time must be before or equal to end time"
```

**Category 6: Invalid Geometry Constraint**

```typescript
// Error when geometry violates resource type constraints
// Applies to: Procedures, Properties (must be null)

Error: "{resourceType} resources cannot have non-null geometry"
HTTP Status: 400 Bad Request

// Examples:
"Procedure resources cannot have non-null geometry"
"Property resources cannot have non-null geometry"
```

**Category 7: Invalid Association Structure**

```typescript
// Error when association array has invalid items
// Applies to: subsystems, deployments, datastreams, etc.

Error: "Invalid {associationName} array: {reason}"
HTTP Status: 400 Bad Request

// Examples:
"Invalid subsystems array: item missing 'href' property"
"Invalid deployedSystems array: cannot be empty (at least one system required)"
```

### 12.2 Error Handling Test Cases

**Missing Required Properties:**

```typescript
describe('Missing required property errors', () => {
  it('throws error for missing uid', () => {
    const feature = {
      type: 'Feature',
      geometry: null,
      properties: { name: 'System 1', featureType: 'sosa:System' },
    };
    expect(() => parseSystemFeature(feature)).toThrow(
      /Missing required property: uid/
    );
  });

  it('throws error for missing name', () => {
    const feature = {
      type: 'Feature',
      geometry: null,
      properties: { uid: 'urn:example:1', featureType: 'sosa:System' },
    };
    expect(() => parseSystemFeature(feature)).toThrow(
      /Missing required property: name/
    );
  });

  it('throws error for missing validTime on Deployment', () => {
    const feature = {
      type: 'Feature',
      geometry: null,
      properties: {
        uid: 'urn:example:deployment:1',
        name: 'Deployment 1',
        featureType: 'sosa:Deployment',
        deployedSystems: [{ rel: 'system', href: '/systems/1' }],
      },
    };
    expect(() => parseDeploymentFeature(feature)).toThrow(
      /Missing required property: validTime/
    );
  });
});
```

**Invalid Vocabulary Values:**

```typescript
describe('Vocabulary validation errors', () => {
  it('throws error for invalid systemType', () => {
    const feature = {
      type: 'Feature',
      geometry: null,
      properties: {
        uid: 'urn:example:1',
        name: 'System 1',
        featureType: 'sosa:System',
        systemType: 'http://example.com/CustomSensor',
      },
    };
    expect(() => parseSystemFeature(feature)).toThrow(
      /Invalid systemType value/
    );
  });

  it('throws error for invalid assetType', () => {
    const feature = {
      type: 'Feature',
      geometry: null,
      properties: {
        uid: 'urn:example:1',
        name: 'System 1',
        featureType: 'sosa:System',
        assetType: 'Robot',
      },
    };
    expect(() => parseSystemFeature(feature)).toThrow(
      /Invalid assetType value.*Equipment, Human, Simulation/
    );
  });
});
```

**Geometry Constraint Violations:**

```typescript
describe('Geometry constraint errors', () => {
  it('throws error for non-null Procedure geometry', () => {
    const feature = {
      type: 'Feature',
      geometry: { type: 'Point', coordinates: [-122.08, 37.42] },
      properties: {
        uid: 'urn:example:procedure:1',
        name: 'Procedure 1',
        featureType: 'sosa:Procedure',
        procedureType: 'sosa:ObservingProcedure',
      },
    };
    expect(() => parseProcedureFeature(feature)).toThrow(
      /cannot have non-null geometry/
    );
  });
});
```

---

## 13. Fixture Requirements

### 13.1 Fixture Sources

**Source 1: CSAPI Part 1 Specification Examples**

- Extract GeoJSON examples from specification document
- Cover all 5 resource types
- Include common property examples
- Estimated: 10-15 fixtures

**Source 2: OpenSensorHub Example Responses**

- Real-world GeoJSON from OSH implementation
- Focus on Systems and Deployments (most common)
- Include complex hierarchies (subsystems, subdeployments)
- Estimated: 10-15 fixtures

**Source 3: Hand-Crafted Test Cases**

- Edge cases: null geometry, open-ended validTime
- Error cases: missing required properties, invalid vocabularies
- Minimal examples: only required properties
- Maximal examples: all optional properties
- Estimated: 5-10 fixtures

**Total Fixtures: ~30**

### 13.2 Fixture Organization

**Directory Structure:**

```
fixtures/csapi-geojson/
├── systems/
│   ├── system-sensor-minimal.json           (required properties only)
│   ├── system-sensor-full.json              (all optional properties)
│   ├── system-platform-with-subsystems.json (hierarchical)
│   ├── system-actuator.json
│   ├── system-sampler.json
│   ├── system-null-geometry.json
│   ├── system-invalid-uid.json              (error case)
│   └── system-invalid-systemtype.json       (error case)
├── deployments/
│   ├── deployment-minimal.json
│   ├── deployment-full.json
│   ├── deployment-open-ended-validtime.json
│   ├── deployment-with-subdeployments.json
│   ├── deployment-missing-validtime.json    (error case)
│   └── deployment-missing-systems.json      (error case)
├── procedures/
│   ├── procedure-observing.json
│   ├── procedure-sampling.json
│   ├── procedure-actuating.json
│   ├── procedure-null-geometry.json
│   └── procedure-non-null-geometry.json     (error case)
├── sampling-features/
│   ├── sampling-feature-point.json
│   ├── sampling-feature-trajectory.json
│   ├── sampling-feature-with-subsample.json
│   ├── sampling-feature-missing-parent.json (error case)
│   └── sampling-feature-missing-foi.json    (error case)
├── properties/
│   ├── property-observable.json
│   ├── property-actuatable.json
│   ├── property-null-geometry.json
│   └── property-non-null-geometry.json      (error case)
└── collections/
    ├── systems-collection.json              (FeatureCollection)
    ├── deployments-collection.json
    ├── systems-collection-paginated.json    (with pagination links)
    └── systems-collection-empty.json        (empty features array)
```

### 13.3 Fixture Requirements by Resource Type

**Systems Fixtures (8 total):**

- ✅ Minimal (required properties only)
- ✅ Full (all optional properties)
- ✅ Each system type (Sensor, Platform, Actuator, Sampler)
- ✅ Hierarchical (with subsystems)
- ✅ Null geometry
- ✅ Error: Invalid uid
- ✅ Error: Invalid systemType vocabulary

**Deployments Fixtures (6 total):**

- ✅ Minimal (required: validTime, deployedSystems)
- ✅ Full (all optional properties)
- ✅ Open-ended validTime
- ✅ Hierarchical (with subdeployments)
- ✅ Error: Missing validTime
- ✅ Error: Missing deployedSystems

**Procedures Fixtures (5 total):**

- ✅ ObservingProcedure
- ✅ SamplingProcedure
- ✅ ActuatingProcedure
- ✅ Null geometry (valid)
- ✅ Error: Non-null geometry

**Sampling Features Fixtures (5 total):**

- ✅ Point sampling
- ✅ Trajectory sampling
- ✅ Sub-sampling (sampleOf)
- ✅ Error: Missing parentSystem
- ✅ Error: Missing sampledFeature

**Properties Fixtures (4 total):**

- ✅ ObservableProperty
- ✅ ActuatableProperty
- ✅ Null geometry (valid)
- ✅ Error: Non-null geometry

**Collections Fixtures (4 total):**

- ✅ Systems FeatureCollection
- ✅ Deployments FeatureCollection
- ✅ Paginated collection (with links)
- ✅ Empty collection

---

## 14. Test Organization

> **⚠️ REVIEW NOTICE (L2):** This section prescribes test file structure,
> describe-block hierarchy, and naming conventions before any code exists.
> This level of detail is premature — let test organization emerge from
> implementation following upstream patterns (see `src/wfs/featureprops.spec.ts`
> for how ogc-client organizes parser tests). The single-file approach
> (`geojson-csapi.spec.ts`) is a reasonable starting point, but the internal
> structure should follow whatever the parser API looks like, not a plan
> written before the parser exists.

### 14.1 Test File Structure

**Single Test File:** `geojson-csapi.spec.ts`

**File Organization:**

```typescript
// geojson-csapi.spec.ts
import { describe, it, expect } from '@jest/globals';
import {
  parseSystemFeature,
  parseDeploymentFeature,
  parseProcedureFeature,
  parseSamplingFeatureFeature,
  parsePropertyFeature,
  parseFeatureCollection,
} from '../src/csapi/geojson-parser';

// Import fixtures
import systemSensorMinimal from '../../fixtures/csapi-geojson/systems/system-sensor-minimal.json';
import deploymentFull from '../../fixtures/csapi-geojson/deployments/deployment-full.json';
// ... other fixtures

describe('CSAPI GeoJSON Parser', () => {
  describe('Common Property Parsing', () => {
    describe('uid (Unique Identifier)', () => {
      /* ... */
    });
    describe('name', () => {
      /* ... */
    });
    describe('featureType', () => {
      /* ... */
    });
    describe('description (optional)', () => {
      /* ... */
    });
    describe('links (optional)', () => {
      /* ... */
    });
  });

  describe('Systems Resource', () => {
    describe('Property Extraction', () => {
      /* ... */
    });
    describe('systemType Validation', () => {
      /* ... */
    });
    describe('assetType Validation', () => {
      /* ... */
    });
    describe('validTime Parsing', () => {
      /* ... */
    });
    describe('Association Arrays', () => {
      /* ... */
    });
    describe('Geometry Handling', () => {
      /* ... */
    });
    describe('Error Cases', () => {
      /* ... */
    });
  });

  describe('Deployments Resource', () => {
    describe('Required validTime', () => {
      /* ... */
    });
    describe('Required deployedSystems', () => {
      /* ... */
    });
    describe('Temporal Period Parsing', () => {
      /* ... */
    });
    describe('Subdeployments Hierarchy', () => {
      /* ... */
    });
    describe('Error Cases', () => {
      /* ... */
    });
  });

  describe('Procedures Resource', () => {
    describe('procedureType Validation', () => {
      /* ... */
    });
    describe('Geometry Constraint (must be null)', () => {
      /* ... */
    });
    describe('Error Cases', () => {
      /* ... */
    });
  });

  describe('Sampling Features Resource', () => {
    describe('Required parentSystem', () => {
      /* ... */
    });
    describe('Required sampledFeature', () => {
      /* ... */
    });
    describe('Sub-sampling (sampleOf)', () => {
      /* ... */
    });
    describe('Error Cases', () => {
      /* ... */
    });
  });

  describe('Properties Resource', () => {
    describe('Geometry Constraint (must be null)', () => {
      /* ... */
    });
    describe('featureType Absence', () => {
      /* ... */
    });
    describe('Error Cases', () => {
      /* ... */
    });
  });

  describe('FeatureCollection Parsing', () => {
    describe('Structure Validation', () => {
      /* ... */
    });
    describe('Pagination Links', () => {
      /* ... */
    });
    describe('Metadata Properties', () => {
      /* ... */
    });
  });
});
```

### 14.2 Test Block Organization

**Describe Block Hierarchy:**

```
geojson-csapi.spec.ts
├── Common Property Parsing (shared across all resources)
│   ├── uid
│   ├── name
│   ├── featureType
│   ├── description
│   └── links
├── Systems Resource
│   ├── Property Extraction
│   ├── systemType Validation
│   ├── assetType Validation
│   ├── validTime Parsing
│   ├── Association Arrays
│   ├── Geometry Handling
│   └── Error Cases
├── Deployments Resource (similar structure)
├── Procedures Resource (similar structure)
├── Sampling Features Resource (similar structure)
├── Properties Resource (similar structure)
└── FeatureCollection Parsing
    ├── Structure Validation
    ├── Pagination Links
    └── Metadata Properties
```

### 14.3 Test Naming Conventions

**it() Block Naming:**

```typescript
// Positive tests: "parses/accepts/extracts..."
it('parses valid uid URN', () => {
  /* ... */
});
it('accepts null geometry for Systems', () => {
  /* ... */
});
it('extracts systemType from properties', () => {
  /* ... */
});

// Negative tests: "throws/rejects/fails..."
it('throws error for missing uid', () => {
  /* ... */
});
it('rejects invalid systemType vocabulary', () => {
  /* ... */
});
it('fails for Procedure with non-null geometry', () => {
  /* ... */
});

// Edge cases: "handles..."
it('handles open-ended validTime periods', () => {
  /* ... */
});
it('handles empty association arrays', () => {
  /* ... */
});
it('handles unknown properties (forward compatibility)', () => {
  /* ... */
});
```

---

## 15. Test Depth and Priorities

### 15.1 Test Depth Criteria

**From Section 6: "Meaningful vs Trivial" Definition:**

**MEANINGFUL Tests (DO write):**

- ✅ Parser extracts correct properties from nested JSON
- ✅ Vocabulary values validated against allowed lists
- ✅ Temporal periods parsed to Date objects correctly
- ✅ Association arrays parsed (links vs inline features)
- ✅ Resource type differentiation via featureType
- ✅ Required property presence validation
- ✅ Geometry constraints enforced (null for Procedures/Properties)

**TRIVIAL Tests (DON'T write):**

- ❌ TypeScript type checking (compiler does this)
- ❌ RFC 7946 geometry validation (existing parser)
- ❌ JSON.parse() functionality
- ❌ Array.isArray() behavior
- ❌ String comparison logic
- ❌ Date object creation

### 15.2 Priority Levels

**CRITICAL (P0) - Must Pass for Release:**

- Required property extraction (uid, name, featureType)
- Resource type recognition (featureType → System/Deployment/etc.)
- Vocabulary validation (systemType, procedureType, assetType)
- Temporal parsing (validTime → Date objects)
- Geometry constraints (Procedures/Properties must be null)
- Required Deployment properties (validTime, deployedSystems)
- Required Sampling Feature properties (parentSystem, sampledFeature)
- Missing required property errors

**HIGH (P1) - Important but not blocking:**

- Optional property extraction (description, validTime for Systems)
- Association array parsing (subsystems, deployments, etc.)
- Link structure validation (rel, href required)
- FeatureCollection parsing
- Pagination link extraction
- Invalid vocabulary value errors
- Invalid URI format errors

**MEDIUM (P2) - Nice to have:**

- Unknown property preservation (forward compatibility)
- Inline feature parsing (vs links)
- Sub-sampling relationships (sampleOf)
- Platform feature extraction (Deployments)
- Open-ended validTime handling
- Empty association array handling

**LOW (P3) - Edge cases:**

- Temporal instant handling (start = end)
- Mixed link/inline feature arrays
- Optional link properties (type, title)
- FeatureCollection metadata (timeStamp, numberMatched)
- Date-only ISO 8601 format (vs datetime)

### 15.3 Test Coverage Goals

**Target Coverage:**

- ✅ 100% of CRITICAL (P0) tests
- ✅ 90% of HIGH (P1) tests
- ✅ 70% of MEDIUM (P2) tests
- ✅ 30% of LOW (P3) tests

**Coverage Metrics:**

- Code coverage: >80% for GeoJSON parser module
- Feature coverage: All 5 resource types tested
- Property coverage: All required properties tested
- Error coverage: All error categories tested

---

## 16. Testing Anti-Patterns

### 16.1 What NOT to Test

**DON'T Re-test RFC 7946 Geometry:**

```typescript
// ❌ BAD: Re-testing coordinate validation
it('rejects invalid longitude', () => {
  const geometry = { type: "Point", coordinates: [200, 37.42] }; // lon > 180
  expect(() => parseSystemFeature({ geometry, ... })).toThrow();
});

// ✅ GOOD: Assume existing parser validates coordinates
// Focus on CSAPI semantics (null geometry for Procedures)
it('rejects non-null geometry for Procedures', () => {
  const feature = {
    geometry: { type: "Point", coordinates: [-122.08, 37.42] }, // valid coords
    properties: { featureType: "sosa:Procedure", ... }
  };
  expect(() => parseProcedureFeature(feature)).toThrow(/cannot have non-null geometry/);
});
```

**DON'T Test TypeScript Type System:**

```typescript
// ❌ BAD: Testing type checking
it('uid is a string', () => {
  const feature = parseSystemFeature(...);
  expect(typeof feature.uid).toBe('string');
});

// ✅ GOOD: Test business logic (URI validation)
it('throws error for invalid uid format', () => {
  const feature = {
    properties: { uid: "not-a-uri", name: "...", featureType: "..." }
  };
  expect(() => parseSystemFeature(feature)).toThrow(/Invalid URI format/);
});
```

**DON'T Test JSON Parsing:**

```typescript
// ❌ BAD: Testing JSON.parse()
it('parses JSON string to object', () => {
  const json = '{"type":"Feature","properties":{}}';
  const obj = JSON.parse(json);
  expect(obj.type).toBe('Feature');
});

// ✅ GOOD: Test CSAPI property extraction from parsed object
it('extracts uid from properties object', () => {
  const feature = {
    type: 'Feature',
    properties: { uid: 'urn:example:1', name: '...', featureType: '...' },
  };
  const result = parseSystemFeature(feature);
  expect(result.uid).toBe('urn:example:1');
});
```

**DON'T Test Framework Behavior:**

```typescript
// ❌ BAD: Testing Jest/expect behavior
it('expect().toThrow() catches errors', () => {
  expect(() => {
    throw new Error('test');
  }).toThrow();
});

// ✅ GOOD: Test parser error handling
it('throws error for missing required property', () => {
  const feature = { properties: { name: '...' } }; // missing uid
  expect(() => parseSystemFeature(feature)).toThrow(
    /Missing required property: uid/
  );
});
```

### 16.2 Duplication Anti-Patterns

**DON'T Duplicate Test Logic:**

```typescript
// ❌ BAD: Duplicating validation logic in tests
it('validates uid format', () => {
  const isValid = /^(https?|urn):/.test("urn:example:1");
  expect(isValid).toBe(true);
});

// ✅ GOOD: Test parser behavior
it('accepts valid uid URN', () => {
  const feature = { properties: { uid: "urn:example:1", ... } };
  expect(parseSystemFeature(feature).uid).toBe("urn:example:1");
});
```

**DON'T Duplicate Across Resource Types:**

```typescript
// ❌ BAD: Repeating common property tests for each resource
describe('Systems', () => {
  it('validates uid', () => {
    /* ... */
  });
  it('validates name', () => {
    /* ... */
  });
});
describe('Deployments', () => {
  it('validates uid', () => {
    /* same test logic ... */
  });
  it('validates name', () => {
    /* same test logic ... */
  });
});

// ✅ GOOD: Test common properties once
describe('Common Property Parsing', () => {
  describe('uid', () => {
    it.each([
      { resourceType: 'System', fixture: systemFixture },
      { resourceType: 'Deployment', fixture: deploymentFixture },
      // ... other resources
    ])('validates uid for $resourceType', ({ fixture }) => {
      // Test logic applies to all resource types
    });
  });
});
```

### 16.3 Over-Testing Anti-Patterns

**DON'T Over-Specify Implementation:**

```typescript
// ❌ BAD: Testing internal implementation details
it('uses Date constructor for temporal parsing', () => {
  const spy = jest.spyOn(global, 'Date');
  parseValidTime(['2024-01-01T00:00:00Z', null]);
  expect(spy).toHaveBeenCalled();
});

// ✅ GOOD: Test observable behavior
it('parses validTime to Date objects', () => {
  const result = parseValidTime(['2024-01-01T00:00:00Z', null]);
  expect(result.begin).toEqual(new Date('2024-01-01T00:00:00Z'));
  expect(result.end).toBeNull();
});
```

**DON'T Test Every Permutation:**

```typescript
// ❌ BAD: Testing every vocabulary value individually
it('accepts sosa:Sensor', () => {
  /* ... */
});
it('accepts sosa:Platform', () => {
  /* ... */
});
it('accepts sosa:Actuator', () => {
  /* ... */
});
// ... 20 more tests for each vocabulary value

// ✅ GOOD: Test representative cases + edge cases
it('accepts valid SOSA system types', () => {
  const validTypes = ['sosa:Sensor', 'sosa:Platform', 'sosa:Actuator'];
  validTypes.forEach((type) => {
    expect(validateSystemType(type)).toBe(true);
  });
});
it('rejects non-SOSA URIs', () => {
  expect(validateSystemType('http://example.com/Sensor')).toBe(false);
});
```

---

## 17. Implementation Notes

### 17.1 TypeScript Integration

**Extend @types/geojson:**

```typescript
import { Feature, FeatureCollection, Geometry } from 'geojson';

// CSAPI-specific property interfaces
interface CSAPICommonProperties {
  uid: string;
  name: string;
  description?: string;
  featureType: string;
}

interface SystemProperties extends CSAPICommonProperties {
  systemType?: string;
  assetType?: 'Equipment' | 'Human' | 'Simulation';
  validTime?: [string, string | null];
  subsystems?: Array<Link | SystemFeature>;
  // ... other properties
}

interface DeploymentProperties extends CSAPICommonProperties {
  validTime: [string, string | null]; // REQUIRED for Deployments
  deployedSystems: Array<Link | SystemFeature>; // REQUIRED
  // ... other properties
}

// CSAPI resource types extend GeoJSON Feature
type SystemFeature = Feature<Geometry | null, SystemProperties>;
type DeploymentFeature = Feature<Geometry | null, DeploymentProperties>;
type SystemCollection = FeatureCollection<Geometry | null, SystemProperties>;
```

### 17.2 Parser Architecture

**Layered Parsing:**

```typescript
// Layer 1: RFC 7946 parsing (existing)
function parseGeoJSONFeature(json: unknown): Feature {
  // Existing parser handles:
  // - Geometry validation
  // - Coordinate validation
  // - Feature structure
  return existingGeoJSONParser(json);
}

// Layer 2: CSAPI property extraction (new)
function parseCSAPIFeature(feature: Feature): CSAPIResource {
  // CSAPI extension handles:
  // - Property extraction from properties object
  // - Vocabulary validation
  // - Temporal parsing
  // - Link structure validation
  const resourceType = identifyResourceType(feature);

  switch (resourceType) {
    case 'System':
      return parseSystemFeature(feature);
    case 'Deployment':
      return parseDeploymentFeature(feature);
    case 'Procedure':
      return parseProcedureFeature(feature);
    case 'SamplingFeature':
      return parseSamplingFeatureFeature(feature);
    case 'Property':
      return parsePropertyFeature(feature);
  }
}

// Combined parser
function parseCSAPIGeoJSON(json: unknown): CSAPIResource {
  const feature = parseGeoJSONFeature(json); // RFC 7946 layer
  return parseCSAPIFeature(feature); // CSAPI layer
}
```

### 17.3 Validation Strategy

> **⚠️ REVIEW NOTICE (H3):** The "progressive validation" pattern below
> mixes property extraction (Steps 1 and 4) with server data validation
> (Steps 2 and 3). `validateURI()`, `validateFeatureType()`,
> `validateSystemTypeVocabulary()`, and `validateAssetTypeEnum()` are
> server-side concerns. The parser should extract and type-coerce, not
> validate vocabulary membership or URI format. Step 1 (check required
> properties exist) and Step 4 (extract) are directly usable.

**Progressive Validation:**

```typescript
function parseSystemFeature(feature: Feature): System {
  // Step 1: Validate required common properties
  validateRequiredProperty(feature.properties, 'uid');
  validateRequiredProperty(feature.properties, 'name');
  validateRequiredProperty(feature.properties, 'featureType');

  // Step 2: Validate property types
  validateURI(feature.properties.uid);
  validateString(feature.properties.name);
  validateFeatureType(feature.properties.featureType);

  // Step 3: Validate resource-specific properties
  if (feature.properties.systemType) {
    validateSystemTypeVocabulary(feature.properties.systemType);
  }
  if (feature.properties.assetType) {
    validateAssetTypeEnum(feature.properties.assetType);
  }
  if (feature.properties.validTime) {
    validateTemporalPeriod(feature.properties.validTime);
  }

  // Step 4: Extract and return resource
  return extractSystemProperties(feature);
}
```

### 17.4 Error Handling Pattern

**Descriptive Error Messages:**

```typescript
class CSAPIValidationError extends Error {
  constructor(
    public propertyName: string,
    public reason: string,
    public value?: unknown
  ) {
    super(
      `Invalid ${propertyName}: ${reason}${value ? ` (value: ${value})` : ''}`
    );
    this.name = 'CSAPIValidationError';
  }
}

// Usage:
function validateSystemType(systemType: string): void {
  if (!SYSTEM_TYPES.includes(systemType)) {
    throw new CSAPIValidationError(
      'systemType',
      'Must be valid SOSA/SSN vocabulary URI',
      systemType
    );
  }
}
```

---

## 18. References

### 18.1 Specifications

**CSAPI:**

- [OGC Connected Systems API - Part 1: Feature Resources](https://docs.ogc.org/is/23-001/23-001.html)
  - Section 7: Systems Resource
  - Section 8: Deployments Resource
  - Section 9: Procedures Resource
  - Section 10: Sampling Features Resource
  - Section 11: Properties Resource
  - Annex B: GeoJSON Encoding

**GeoJSON:**

- [RFC 7946: The GeoJSON Format](https://datatracker.ietf.org/doc/html/rfc7946)
  - Section 3: GeoJSON Object Structure
  - Section 3.2: Feature Object
  - Section 3.3: FeatureCollection Object
  - Section 4: CRS (Coordinate Reference System)

**URIs:**

- [RFC 8141: URN Syntax](https://datatracker.ietf.org/doc/html/rfc8141)
- [RFC 3986: URI Generic Syntax](https://datatracker.ietf.org/doc/html/rfc3986)

**Temporal:**

- [ISO 8601: Date and Time Format](https://www.iso.org/iso-8601-date-and-time-format.html)

### 18.2 Ontologies

**SOSA/SSN:**

- [SOSA/SSN Ontology](https://www.w3.org/TR/vocab-ssn/)
  - sosa:System, sosa:Sensor, sosa:Platform, sosa:Actuator, sosa:Sampler
  - sosa:Deployment
  - sosa:Procedure, sosa:ObservingProcedure, sosa:SamplingProcedure, sosa:ActuatingProcedure
  - sosa:Sample
  - sosa:ObservableProperty, sosa:ActuatableProperty

### 18.3 CSAPI Project Documents

**Testing:**

- Section 8: CSAPI Specification Test Requirements (test philosophy, fixtures approach)
- Section 6: "Meaningful vs Trivial" Definition (test depth criteria)
- Section 1: Upstream Parser Analysis - GeoJSON Capabilities
- Section 2: Upstream Test Blueprint - EDR Testing Patterns

**Requirements:**

- CSAPI Part 1 Requirements Analysis (property definitions)
- CSAPI Format Requirements Analysis (GeoJSON structure)

**Implementation:**

- CSAPI Implementation Guide (GeoJSON Handler extension strategy)
- CSAPI Functional Specification (TypeScript types)

### 18.4 Upstream Resources

**ogc-client Library:**

- WFS GeoJSON Parser: `src/wfs/featureprops.ts` (parseFeaturePropsGeojson)
- Type Definitions: `@types/geojson` package
- WFS Feature Tests: `src/wfs/featureprops.spec.ts`

---

## Appendix A: Example Test Implementation

> **⚠️ REVIEW NOTICE (H3):** The example tests below mix legitimate parser
> tests (property extraction, validTime parsing) with server data validation
> tests (systemType vocabulary rejection, assetType enum validation, URI
> format checking). Use the property extraction and temporal parsing tests
> as models; replace vocabulary/format validation tests with extraction-
> focused assertions.

### Full Example: Systems Resource Testing

```typescript
import { describe, it, expect } from '@jest/globals';
import { parseSystemFeature } from '../src/csapi/geojson-parser';
import systemSensorMinimal from '../../fixtures/csapi-geojson/systems/system-sensor-minimal.json';
import systemSensorFull from '../../fixtures/csapi-geojson/systems/system-sensor-full.json';
import systemInvalidUID from '../../fixtures/csapi-geojson/systems/system-invalid-uid.json';

describe('Systems Resource GeoJSON Parsing', () => {
  describe('Property Extraction', () => {
    it('extracts required properties from minimal fixture', () => {
      const result = parseSystemFeature(systemSensorMinimal);
      expect(result.uid).toBe('urn:x-sensor:id:sensor123');
      expect(result.name).toBe('Temperature Sensor TS-001');
      expect(result.featureType).toBe('http://www.w3.org/ns/sosa/Sensor');
    });

    it('extracts all properties from full fixture', () => {
      const result = parseSystemFeature(systemSensorFull);
      expect(result.uid).toBeDefined();
      expect(result.name).toBeDefined();
      expect(result.featureType).toBeDefined();
      expect(result.description).toBeDefined();
      expect(result.systemType).toBeDefined();
      expect(result.assetType).toBe('Equipment');
      expect(result.validTime).toBeDefined();
      expect(result.subsystems).toBeDefined();
    });
  });

  describe('systemType Validation', () => {
    it('accepts valid SOSA system type', () => {
      const feature = {
        type: 'Feature',
        geometry: null,
        properties: {
          uid: 'urn:example:1',
          name: 'System 1',
          featureType: 'http://www.w3.org/ns/sosa/System',
          systemType: 'http://www.w3.org/ns/sosa/Sensor',
        },
      };
      const result = parseSystemFeature(feature);
      expect(result.systemType).toBe('http://www.w3.org/ns/sosa/Sensor');
    });

    it('accepts shorthand SOSA syntax', () => {
      const feature = {
        type: 'Feature',
        geometry: null,
        properties: {
          uid: 'urn:example:1',
          name: 'System 1',
          featureType: 'sosa:System',
          systemType: 'sosa:Platform',
        },
      };
      const result = parseSystemFeature(feature);
      expect(result.systemType).toBe('sosa:Platform');
    });

    it('throws error for invalid systemType vocabulary', () => {
      const feature = {
        type: 'Feature',
        geometry: null,
        properties: {
          uid: 'urn:example:1',
          name: 'System 1',
          featureType: 'sosa:System',
          systemType: 'http://example.com/CustomSensor',
        },
      };
      expect(() => parseSystemFeature(feature)).toThrow(
        /Invalid systemType value.*SOSA/
      );
    });
  });

  describe('assetType Validation', () => {
    it.each(['Equipment', 'Human', 'Simulation'])(
      'accepts valid assetType: %s',
      (assetType) => {
        const feature = {
          type: 'Feature',
          geometry: null,
          properties: {
            uid: 'urn:example:1',
            name: 'System 1',
            featureType: 'sosa:System',
            assetType,
          },
        };
        const result = parseSystemFeature(feature);
        expect(result.assetType).toBe(assetType);
      }
    );

    it('throws error for invalid assetType', () => {
      const feature = {
        type: 'Feature',
        geometry: null,
        properties: {
          uid: 'urn:example:1',
          name: 'System 1',
          featureType: 'sosa:System',
          assetType: 'Robot',
        },
      };
      expect(() => parseSystemFeature(feature)).toThrow(
        /Invalid assetType.*Equipment, Human, Simulation/
      );
    });
  });

  describe('validTime Parsing', () => {
    it('parses open-ended validTime period', () => {
      const feature = {
        type: 'Feature',
        geometry: null,
        properties: {
          uid: 'urn:example:1',
          name: 'System 1',
          featureType: 'sosa:System',
          validTime: ['2024-01-01T00:00:00Z', null],
        },
      };
      const result = parseSystemFeature(feature);
      expect(result.validTime?.begin).toEqual(new Date('2024-01-01T00:00:00Z'));
      expect(result.validTime?.end).toBeNull();
    });

    it('parses closed validTime period', () => {
      const feature = {
        type: 'Feature',
        geometry: null,
        properties: {
          uid: 'urn:example:1',
          name: 'System 1',
          featureType: 'sosa:System',
          validTime: ['2024-01-01T00:00:00Z', '2024-12-31T23:59:59Z'],
        },
      };
      const result = parseSystemFeature(feature);
      expect(result.validTime?.begin).toEqual(new Date('2024-01-01T00:00:00Z'));
      expect(result.validTime?.end).toEqual(new Date('2024-12-31T23:59:59Z'));
    });

    it('throws error for start > end', () => {
      const feature = {
        type: 'Feature',
        geometry: null,
        properties: {
          uid: 'urn:example:1',
          name: 'System 1',
          featureType: 'sosa:System',
          validTime: ['2024-12-31T23:59:59Z', '2024-01-01T00:00:00Z'],
        },
      };
      expect(() => parseSystemFeature(feature)).toThrow(
        /start time must be before or equal to end time/
      );
    });
  });

  describe('Error Cases', () => {
    it('throws error for missing uid', () => {
      const feature = {
        type: 'Feature',
        geometry: null,
        properties: {
          name: 'System 1',
          featureType: 'sosa:System',
        },
      };
      expect(() => parseSystemFeature(feature)).toThrow(
        /Missing required property: uid/
      );
    });

    it('throws error for invalid uid format', () => {
      expect(() => parseSystemFeature(systemInvalidUID)).toThrow(
        /Invalid URI format.*uid/
      );
    });
  });
});
```

---

## Document Metadata

**Status:** Complete — Review notices added (Phase 2D issues H3, M3, L2)  
**Word Count:** ~15,000 words  
**Sections:** 18  
**Estimated Test Count:** ~150 tests across all resource types  
**Estimated Fixtures:** ~30 JSON files  
**Implementation Effort:** 3-5 days (parsing + tests)

**Review Checklist:**

- ✅ All 74 research questions answered
- ✅ All 5 resource types covered comprehensively
- ✅ Reuse strategy clear (extend existing, don't duplicate)
- ✅ Vocabulary validation requirements defined
- ✅ Temporal validation specifications complete
- ✅ Link structure requirements documented
- ✅ Geometry handling strategy (null constraints)
- ✅ Error handling requirements per category
- ✅ 18 required sections completed
- ✅ Test organization designed (single file, 7 describe blocks)
- ✅ Test depth priorities defined (P0-P3)
- ✅ Anti-patterns documented
- ✅ Fixture requirements (~30 total)
- ✅ Example test implementation provided

**Next Steps:**

1. Review document with team
2. Create fixture directory structure
3. Implement GeoJSON parser extensions
4. Write tests following this specification
5. Validate with OpenSensorHub examples
