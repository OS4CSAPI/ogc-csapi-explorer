# Section 22: Conformance and Capability Testing - FINDINGS

**Research Plan:** [Research Plan 22: Conformance and Capability Testing](../research-plans/22-conformance-capability-testing.md)

**Research Questions:** 6 core questions about testing conformance class detection from /conformance endpoint, hasConnectedSystems method, resource availability checking, graceful degradation when resources unavailable, conformance scenarios requiring tests, and mocking different server capability profiles

**Methodology:** 6-phase systematic analysis (Phase 1: CSAPI Conformance Class Analysis cataloging all Part 1 & Part 2 classes → Phase 2: Real Server Conformance Analysis of OpenSensorHub/52°North → Phase 3: Client Conformance Logic Analysis mapping conformance to behavior → Phase 4: Test Scenario Design for full/partial/missing conformance → Phase 5: Mocking Strategy for capability profiles → Phase 6: Synthesis into comprehensive conformance testing strategy)

**Research Time:** ~4 hours (February 5, 2026)

**Primary Source(s):**

- [Conformance Capabilities Requirements](../../requirements/csapi-conformance-capabilities.md)
- [52°North Analysis](../../requirements/csapi-52north-analysis.md) (partial conformance example)
- [OpenSensorHub Analysis](../../requirements/csapi-opensensorhub-analysis.md) (full conformance example)
- [CSAPI Implementation Guide](../../../planning/csapi-implementation-guide.md) (Conformance checking specification)

**Supporting Resources:**

- [CSAPI Part 1 Specification](https://docs.ogc.org/is/23-001/23-001.html) (conformance classes)
- [CSAPI Part 2 Specification](https://docs.ogc.org/is/23-002/23-002.html) (conformance classes)
- Section 1: [EDR Test Blueprint](01-edr-test-blueprint.md) (upstream conformance patterns)
- Section 2: [Upstream Test Consistency](02-upstream-test-consistency.md) (capability testing)
- Section 13: [Resource Method Testing Patterns](13-resource-method-testing-patterns.md) (resource availability)

**Document Purpose:** Defines testing strategy for 25 modular CSAPI conformance classes with 8+ server capability profiles (minimal to full), conformance-based method availability, graceful degradation, resource availability checking, and mock /conformance responses, using 52°North's partial Part 2 implementation as primary test case

---

## Executive Summary

CSAPI defines 25 modular conformance classes with no mandatory "core" - servers can implement different capability profiles. The client must detect capabilities via the `/conformance` endpoint and adapt behavior accordingly. Testing strategy requires:

1. **8+ server capability profiles** (minimal to full conformance)
2. **Conformance-based method availability** (enable/disable features)
3. **Graceful degradation** (fallback or error strategies)
4. **Resource availability checking** (validate references)
5. **Mock /conformance responses** (fixture-based testing)

**Key Insight:** 52°North implements Part 1 fully but Part 2 partially (DataStreams only, no ControlStreams) - this is the primary partial conformance test case.

---

## Table of Contents

1. [CSAPI Conformance Class Catalog](#1-csapi-conformance-class-catalog)
2. [Real Server Conformance Profiles](#2-real-server-conformance-profiles)
3. [Conformance-to-Behavior Mapping](#3-conformance-to-behavior-mapping)
4. [Capability Detection Test Patterns](#4-capability-detection-test-patterns)
5. [Conformance Test Scenarios](#5-conformance-test-scenarios)
6. [Server Capability Mocking Strategy](#6-server-capability-mocking-strategy)
7. [Test Implementation Templates](#7-test-implementation-templates)
8. [Implementation Estimates](#8-implementation-estimates)

---

## 1. CSAPI Conformance Class Catalog

### 1.1 Part 1: System Metadata (13 Classes)

| Conformance Class               | URI Suffix                    | Required?              | Depends On | Key Capabilities                   |
| ------------------------------- | ----------------------------- | ---------------------- | ---------- | ---------------------------------- |
| **A.1: Common**                 | `/conf/api-common`            | ✅ YES                 | -          | Core OGC API functionality         |
| **A.2: System Features**        | `/conf/system`                | ⚠️ At least 1 resource | A.1        | `/systems` CRUD                    |
| **A.3: Subsystems**             | `/conf/subsystem`             | ❌ Optional            | A.2        | `/systems/{id}/subsystems`         |
| **A.4: Deployment Features**    | `/conf/deployment`            | ⚠️ At least 1 resource | A.1        | `/deployments` CRUD                |
| **A.5: Subdeployments**         | `/conf/subdeployment`         | ❌ Optional            | A.4        | `/deployments/{id}/subdeployments` |
| **A.6: Procedure Features**     | `/conf/procedure`             | ⚠️ At least 1 resource | A.1        | `/procedures` CRUD                 |
| **A.7: Sampling Features**      | `/conf/sf`                    | ❌ Optional            | A.1, A.2   | `/fois` CRUD                       |
| **A.8: Property Definitions**   | `/conf/property`              | ⚠️ At least 1 resource | A.1        | `/properties` CRUD                 |
| **A.9: Advanced Filtering**     | `/conf/advanced-filtering`    | ❌ Optional            | -          | CQL2 queries (22 requirements)     |
| **A.10: Create/Replace/Delete** | `/conf/create-replace-delete` | ❌ Optional            | -          | POST, PUT, DELETE                  |
| **A.11: Update**                | `/conf/update`                | ❌ Optional            | A.10       | PATCH operations                   |
| **A.12: GeoJSON Format**        | `/conf/geojson`               | ⚠️ At least 1 encoding | -          | `application/geo+json`             |
| **A.13: SensorML Format**       | `/conf/sensorml`              | ⚠️ At least 1 encoding | -          | `application/sml+json`             |

**Minimum Requirements:**

- A.1 (Common) + at least 1 resource type (A.2, A.4, A.6, or A.8) + at least 1 encoding (A.12 or A.13)

### 1.2 Part 2: Dynamic Data & Control (12 Classes)

| Conformance Class                            | URI Suffix                    | Required?    | Depends On | Key Capabilities                 |
| -------------------------------------------- | ----------------------------- | ------------ | ---------- | -------------------------------- |
| **A.1: Common**                              | `/conf/api-common`            | ✅ If Part 2 | Part 1 A.1 | Core Part 2 functionality        |
| **A.2: DataStreams & Observations**          | `/conf/datastream`            | ❌ Optional  | Part 1     | `/datastreams`, `/observations`  |
| **A.3: Control Streams & Commands**          | `/conf/controlstream`         | ❌ Optional  | Part 1     | `/controlstreams`, `/commands`   |
| **A.4: Command Feasibility**                 | `/conf/feasibility`           | ❌ Optional  | A.3        | `/commands/{id}/feasibility`     |
| **A.5: System Events**                       | `/conf/system-event`          | ❌ Optional  | Part 1 A.2 | `/systems/{id}/events`           |
| **A.6: Advanced Filtering**                  | `/conf/advanced-filtering`    | ❌ Optional  | -          | CQL2 for dynamic resources       |
| **A.7: Create/Replace/Delete**               | `/conf/create-replace-delete` | ❌ Optional  | -          | POST, PUT, DELETE                |
| **A.8: Update**                              | `/conf/update`                | ❌ Optional  | A.7        | PATCH operations                 |
| **A.9: Observations Encoding - JSON**        | `/conf/json`                  | ✅ If A.2    | -          | `application/om+json` (required) |
| **A.10: Observations Encoding - SWE JSON**   | `/conf/swecommon-json`        | ❌ Optional  | -          | `application/swe+json`           |
| **A.11: Observations Encoding - SWE Text**   | `/conf/swecommon-text`        | ❌ Optional  | -          | `application/swe+text`           |
| **A.12: Observations Encoding - SWE Binary** | `/conf/swecommon-binary`      | ❌ Optional  | -          | `application/swe+binary`         |

**Minimum Requirements:**

- If implementing Part 2: Part 2 A.1 + at least 1 dynamic resource (A.2 or A.3) + required encoding (A.9 for DataStreams)

### 1.3 Conformance Class Hierarchy

```
Part 1 (System Metadata)
│
├─ A.1: Common (REQUIRED)
│   │
│   ├─ A.2: System Features (At least 1 of A.2/A.4/A.6/A.8)
│   │   ├─ A.3: Subsystems (Optional, requires A.2)
│   │   └─ A.7: Sampling Features (Optional, requires A.2)
│   │
│   ├─ A.4: Deployment Features (At least 1 of A.2/A.4/A.6/A.8)
│   │   └─ A.5: Subdeployments (Optional, requires A.4)
│   │
│   ├─ A.6: Procedure Features (At least 1 of A.2/A.4/A.6/A.8)
│   │
│   └─ A.8: Property Definitions (At least 1 of A.2/A.4/A.6/A.8)
│
├─ A.9: Advanced Filtering (Optional)
│
├─ A.10: Create/Replace/Delete (Optional)
│   └─ A.11: Update (Optional, requires A.10)
│
└─ Encodings (At least 1 of A.12/A.13)
    ├─ A.12: GeoJSON Format
    └─ A.13: SensorML Format

Part 2 (Dynamic Data)
│
├─ A.1: Common (REQUIRED if Part 2)
│   │
│   ├─ A.2: DataStreams & Observations (Optional)
│   │   └─ A.9: O&M JSON Encoding (REQUIRED if A.2)
│   │
│   ├─ A.3: Control Streams & Commands (Optional)
│   │   └─ A.4: Command Feasibility (Optional, requires A.3)
│   │
│   └─ A.5: System Events (Optional, requires Part 1 A.2)
│
├─ A.6: Advanced Filtering (Optional)
│
├─ A.7: Create/Replace/Delete (Optional)
│   └─ A.8: Update (Optional, requires A.7)
│
└─ Optional Encodings
    ├─ A.10: SWE JSON
    ├─ A.11: SWE Text
    └─ A.12: SWE Binary
```

---

## 2. Real Server Conformance Profiles

> **⚠️ REVIEW NOTICE (Phase 2D — M4):** This section documents real server profiles (OpenSensorHub, 52°North) with live URLs, pagination limits, and backend details. These profiles are **reference context only** — they inform fixture design and explain _why_ certain test scenarios exist. All test code in this document correctly uses `mockFetchForProfile()` with static fixture data; no tests should ever make live HTTP requests. When implementing tests, derive fixtures from these profiles but never import live URLs or server-specific behaviors into test assertions.

### 2.1 OpenSensorHub (Full Conformance)

**Implementation:** Java/Spring, production-ready  
**Live Server:** http://45.55.99.236:8080/sensorhub/api  
**Version:** CSAPI Parts 1, 2, 3

**Conformance Classes (33/33):**

**Part 1:** ✅ All 13 classes

- A.1: Common
- A.2: System Features
- A.3: Subsystems
- A.4: Deployment Features
- A.5: Subdeployments
- A.6: Procedure Features
- A.7: Sampling Features
- A.8: Property Definitions
- A.9: Advanced Filtering
- A.10: Create/Replace/Delete
- A.11: Update
- A.12: GeoJSON Format
- A.13: SensorML Format

**Part 2:** ✅ All 12 classes

- A.1: Common
- A.2: DataStreams & Observations
- A.3: Control Streams & Commands
- A.4: Command Feasibility
- A.5: System Events
- A.6: Advanced Filtering
- A.7: Create/Replace/Delete
- A.8: Update
- A.9: O&M JSON Encoding
- A.10: SWE JSON Encoding
- A.11: SWE Text Encoding
- A.12: SWE Binary Encoding

**Part 3:** ✅ All classes (not documented in detail - beyond CSAPI 1.0)

**Server Behaviors:**

- Default pagination limit: 100
- Max limit: 10,000
- Supports WebSocket streaming (`ws://`)
- Supports MQTT streaming
- Live observations with `validTime=[...,"now"]`
- Full CRUD on all resources
- Complex CQL2 filtering
- All encoding formats

**Test Value:** Full conformance baseline - all features should work

---

### 2.2 52°North (Partial Conformance - Reference Implementation)

**Implementation:** Python/Quart/pygeoapi  
**Live Server:** https://csa.demo.52north.org/  
**Version:** CSAPI Part 1 (full), Part 2 (partial - in development)

**Conformance Classes:**

**Part 1:** ✅ Full implementation (13/13 classes)

- ✅ All 5 resource types (Systems, Deployments, Procedures, Properties, Sampling Features)
- ✅ Subsystems, Subdeployments (hierarchical)
- ✅ Advanced Filtering
- ✅ Full CRUD (Create/Replace/Delete, Update)
- ✅ GeoJSON + SensorML encodings

**Part 2:** ⚠️ **PARTIAL - DataStreams ONLY** (2/12 classes)

- ✅ A.1: Common
- ✅ A.2: DataStreams & Observations
- ❌ **A.3: Control Streams & Commands** (NOT IMPLEMENTED)
- ❌ A.4: Command Feasibility
- ❌ A.5: System Events
- ✅ A.6: Advanced Filtering
- ✅ A.7: Create/Replace/Delete
- ✅ A.8: Update
- ✅ A.9: O&M JSON Encoding
- ✅ A.10: SWE JSON Encoding
- ❌ A.11: SWE Text Encoding
- ❌ A.12: SWE Binary Encoding

**Server Behaviors:**

- Default pagination limit: 10 (different from OSH)
- Backend: Elasticsearch (Part 1) + TimescaleDB (Part 2)
- Preferred format: SensorML for Part 1 resources
- O&M JSON + SWE JSON for observations

**Test Value:** **PRIMARY PARTIAL CONFORMANCE TEST CASE**

- Tests client adaptation to missing ControlStreams
- Tests partial Part 2 implementation
- Tests different pagination defaults
- Tests incomplete conformance declarations (known issue)

---

### 2.3 Minimum Viable Configurations (6 Test Profiles)

**Profile 1: Read-Only System Registry**

```json
{
  "conformsTo": [
    "http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/api-common",
    "http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/system",
    "http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/geojson"
  ]
}
```

- Only Systems resource (no Deployments, Procedures, etc.)
- No CRUD operations (read-only)
- GeoJSON format only

**Profile 2: Read-Only Deployment Registry**

```json
{
  "conformsTo": [
    "http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/api-common",
    "http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/deployment",
    "http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/sensorml"
  ]
}
```

- Only Deployments resource
- No CRUD operations
- SensorML format only

**Profile 3: Transactional System Registry**

```json
{
  "conformsTo": [
    "http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/api-common",
    "http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/system",
    "http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/subsystem",
    "http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/create-replace-delete",
    "http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/update",
    "http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/geojson",
    "http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/sensorml"
  ]
}
```

- Systems + Subsystems
- Full CRUD (POST, PUT, PATCH, DELETE)
- GeoJSON + SensorML formats

**Profile 4: Sensor Data Server (Part 1 + Part 2 DataStreams)**

```json
{
  "conformsTo": [
    "http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/api-common",
    "http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/system",
    "http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/deployment",
    "http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/geojson",
    "http://www.opengis.net/spec/ogcapi-connectedsystems-2/1.0/conf/api-common",
    "http://www.opengis.net/spec/ogcapi-connectedsystems-2/1.0/conf/datastream",
    "http://www.opengis.net/spec/ogcapi-connectedsystems-2/1.0/conf/json"
  ]
}
```

- Systems + Deployments (Part 1)
- DataStreams + Observations (Part 2)
- No ControlStreams (sensor-only)
- **Matches 52°North profile**

**Profile 5: Actuator Control Server (Part 1 + Part 2 ControlStreams)**

```json
{
  "conformsTo": [
    "http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/api-common",
    "http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/system",
    "http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/geojson",
    "http://www.opengis.net/spec/ogcapi-connectedsystems-2/1.0/conf/api-common",
    "http://www.opengis.net/spec/ogcapi-connectedsystems-2/1.0/conf/controlstream",
    "http://www.opengis.net/spec/ogcapi-connectedsystems-2/1.0/conf/feasibility",
    "http://www.opengis.net/spec/ogcapi-connectedsystems-2/1.0/conf/json"
  ]
}
```

- Systems (Part 1)
- ControlStreams + Commands + Feasibility (Part 2)
- No DataStreams (control-only)

**Profile 6: Full-Featured Server (All Conformance Classes)**

```json
{
  "conformsTo": [
    // All 25 URIs from Part 1 + Part 2
  ]
}
```

- **Matches OpenSensorHub profile**

---

## 3. Conformance-to-Behavior Mapping

### 3.1 Client Initialization Logic

```typescript
class CSAPIClient {
  private conformance: Set<string> = new Set();
  private capabilities: ServerCapabilities;

  // Resource clients (conditionally initialized)
  public systems?: SystemsResource;
  public deployments?: DeploymentsResource;
  public datastreams?: DataStreamsResource;
  public controlstreams?: ControlStreamsResource;
  // ... etc.

  async initialize(baseUrl: string) {
    // Step 1: Fetch /conformance
    const response = await fetch(`${baseUrl}/conformance`);
    if (!response.ok) {
      throw new Error(`Conformance endpoint failed: ${response.status}`);
    }

    const data = await response.json();
    this.conformance = new Set(data.conformsTo || []);

    // Step 2: Detect capabilities
    this.capabilities = this.detectCapabilities();

    // Step 3: Configure resource clients based on capabilities
    this.configureResources();
  }

  private detectCapabilities(): ServerCapabilities {
    return {
      // Part 1 resources
      hasSystems: this.hasConformance(
        'ogcapi-connectedsystems-1/1.0/conf/system'
      ),
      hasSubsystems: this.hasConformance(
        'ogcapi-connectedsystems-1/1.0/conf/subsystem'
      ),
      hasDeployments: this.hasConformance(
        'ogcapi-connectedsystems-1/1.0/conf/deployment'
      ),
      hasSubdeployments: this.hasConformance(
        'ogcapi-connectedsystems-1/1.0/conf/subdeployment'
      ),
      hasProcedures: this.hasConformance(
        'ogcapi-connectedsystems-1/1.0/conf/procedure'
      ),
      hasSamplingFeatures: this.hasConformance(
        'ogcapi-connectedsystems-1/1.0/conf/sf'
      ),
      hasProperties: this.hasConformance(
        'ogcapi-connectedsystems-1/1.0/conf/property'
      ),

      // Part 2 resources
      hasDataStreams: this.hasConformance(
        'ogcapi-connectedsystems-2/1.0/conf/datastream'
      ),
      hasControlStreams: this.hasConformance(
        'ogcapi-connectedsystems-2/1.0/conf/controlstream'
      ),
      hasCommandFeasibility: this.hasConformance(
        'ogcapi-connectedsystems-2/1.0/conf/feasibility'
      ),
      hasSystemEvents: this.hasConformance(
        'ogcapi-connectedsystems-3/1.0/conf/system-event'
      ),

      // Operations
      hasCRUD:
        this.hasConformance(
          'ogcapi-connectedsystems-1/1.0/conf/create-replace-delete'
        ) ||
        this.hasConformance(
          'ogcapi-connectedsystems-2/1.0/conf/create-replace-delete'
        ),
      hasUpdate:
        this.hasConformance('ogcapi-connectedsystems-1/1.0/conf/update') ||
        this.hasConformance('ogcapi-connectedsystems-2/1.0/conf/update'),
      hasAdvancedFiltering:
        this.hasConformance(
          'ogcapi-connectedsystems-1/1.0/conf/advanced-filtering'
        ) ||
        this.hasConformance(
          'ogcapi-connectedsystems-2/1.0/conf/advanced-filtering'
        ),

      // Formats
      supportsGeoJSON: this.hasConformance(
        'ogcapi-connectedsystems-1/1.0/conf/geojson'
      ),
      supportsSensorML: this.hasConformance(
        'ogcapi-connectedsystems-1/1.0/conf/sensorml'
      ),
      supportsOMJSON: this.hasConformance(
        'ogcapi-connectedsystems-2/1.0/conf/json'
      ),
      supportsSWEJSON: this.hasConformance(
        'ogcapi-connectedsystems-2/1.0/conf/swecommon-json'
      ),
      supportsSWEText: this.hasConformance(
        'ogcapi-connectedsystems-2/1.0/conf/swecommon-text'
      ),
      supportsSWEBinary: this.hasConformance(
        'ogcapi-connectedsystems-2/1.0/conf/swecommon-binary'
      ),
    };
  }

  private configureResources() {
    // Conditionally initialize resource clients
    if (this.capabilities.hasSystems) {
      this.systems = new SystemsResource(this);
    }
    if (this.capabilities.hasDeployments) {
      this.deployments = new DeploymentsResource(this);
    }
    if (this.capabilities.hasDataStreams) {
      this.datastreams = new DataStreamsResource(this);
    }
    if (this.capabilities.hasControlStreams) {
      this.controlstreams = new ControlStreamsResource(this);
    }
    // ... etc.
  }

  private hasConformance(suffix: string): boolean {
    // Check full URI
    const fullURI = `http://www.opengis.net/spec/${suffix}`;
    return this.conformance.has(fullURI);
  }
}
```

### 3.2 Resource Client Method Availability

```typescript
class SystemsResource {
  constructor(private client: CSAPIClient) {}

  // Always available if resource exists
  async list(options?: QueryOptions): Promise<SystemCollection> {
    return this.client.get('/systems', options);
  }

  async get(id: string): Promise<System> {
    return this.client.get(`/systems/${id}`);
  }

  // CRUD methods - check conformance
  async create(data: SystemInput): Promise<System> {
    if (!this.client.capabilities.hasCRUD) {
      throw new ConformanceError(
        'Server does not support create operations (missing /conf/create-replace-delete)',
        'hasCRUD',
        'create'
      );
    }
    return this.client.post('/systems', data);
  }

  async update(id: string, patch: Partial<SystemInput>): Promise<void> {
    if (!this.client.capabilities.hasUpdate) {
      throw new ConformanceError(
        'Server does not support update operations (missing /conf/update)',
        'hasUpdate',
        'update'
      );
    }
    return this.client.patch(`/systems/${id}`, patch);
  }

  async replace(id: string, data: SystemInput): Promise<System> {
    if (!this.client.capabilities.hasCRUD) {
      throw new ConformanceError(
        'Server does not support replace operations (missing /conf/create-replace-delete)',
        'hasCRUD',
        'replace'
      );
    }
    return this.client.put(`/systems/${id}`, data);
  }

  async delete(id: string): Promise<void> {
    if (!this.client.capabilities.hasCRUD) {
      throw new ConformanceError(
        'Server does not support delete operations (missing /conf/create-replace-delete)',
        'hasCRUD',
        'delete'
      );
    }
    return this.client.delete(`/systems/${id}`);
  }

  // Nested resources - check conformance
  subsystems(id: string): SubsystemsResource | null {
    if (!this.client.capabilities.hasSubsystems) {
      return null; // Graceful degradation
    }
    return new SubsystemsResource(this.client, id);
  }

  // Part 2 resources - check conformance
  datastreams(id: string): DataStreamsResource | null {
    if (!this.client.capabilities.hasDataStreams) {
      return null;
    }
    return new DataStreamsResource(this.client, id);
  }

  events(id: string): SystemEventsResource | null {
    if (!this.client.capabilities.hasSystemEvents) {
      return null;
    }
    return new SystemEventsResource(this.client, id);
  }
}
```

### 3.3 Error Classes

```typescript
export class ConformanceError extends Error {
  constructor(
    message: string,
    public readonly capability: keyof ServerCapabilities,
    public readonly operation: string
  ) {
    super(message);
    this.name = 'ConformanceError';
  }
}

// Usage:
try {
  await client.systems.create(systemData);
} catch (error) {
  if (error instanceof ConformanceError) {
    console.error(
      `Operation '${error.operation}' unavailable: ${error.message}`
    );
    console.error(`Missing capability: ${error.capability}`);
  }
}
```

---

## 4. Capability Detection Test Patterns

### 4.1 Conformance Endpoint Tests

**File:** `src/ogc-api/csapi/conformance.spec.ts`

```typescript
describe('CSAPI Conformance Detection', () => {
  describe('hasConnectedSystems getter', () => {
    it('returns true when Part 1 common conformance present', async () => {
      const endpoint = new OgcApiEndpoint('https://test.csapi.org');

      // Mock /conformance response
      globalThis.fetch = jest.fn().mockResolvedValueOnce({
        ok: true,
        json: () =>
          Promise.resolve({
            conformsTo: [
              'http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/api-common',
            ],
          }),
      });

      await expect(endpoint.hasConnectedSystems).resolves.toBe(true);
    });

    it('returns false when no CSAPI conformance present', async () => {
      const endpoint = new OgcApiEndpoint('https://test.ogc.org');

      globalThis.fetch = jest.fn().mockResolvedValueOnce({
        ok: true,
        json: () =>
          Promise.resolve({
            conformsTo: [
              'http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/core',
            ],
          }),
      });

      await expect(endpoint.hasConnectedSystems).resolves.toBe(false);
    });

    it('handles malformed conformance response', async () => {
      const endpoint = new OgcApiEndpoint('https://test.csapi.org');

      globalThis.fetch = jest.fn().mockResolvedValueOnce({
        ok: true,
        json: () =>
          Promise.resolve({
            // Missing conformsTo array
          }),
      });

      await expect(endpoint.hasConnectedSystems).resolves.toBe(false);
    });

    it('handles conformance endpoint failure', async () => {
      const endpoint = new OgcApiEndpoint('https://test.csapi.org');

      globalThis.fetch = jest.fn().mockResolvedValueOnce({
        ok: false,
        status: 404,
      });

      await expect(endpoint.hasConnectedSystems).rejects.toThrow();
    });
  });

  describe('csapiCollections getter', () => {
    it('returns CSAPI collections when hasConnectedSystems is true', async () => {
      // Mock conformance + collections endpoints
      // Assert collection IDs match CSAPI item types
    });

    it('returns empty array when hasConnectedSystems is false', async () => {
      // Mock non-CSAPI conformance
      // Assert empty array
    });
  });
});
```

### 4.2 Capability Detection Tests

**File:** `src/ogc-api/csapi/capabilities.spec.ts`

```typescript
describe('ServerCapabilities Detection', () => {
  let client: CSAPIClient;

  describe('Full Conformance (OpenSensorHub Profile)', () => {
    beforeEach(async () => {
      // Mock /conformance with all 25 classes
      globalThis.fetch = jest.fn().mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(FIXTURES.conformance.opensensorhub),
      });

      client = new CSAPIClient('https://osh.test.org');
      await client.initialize();
    });

    it('detects all Part 1 resources', () => {
      expect(client.capabilities.hasSystems).toBe(true);
      expect(client.capabilities.hasSubsystems).toBe(true);
      expect(client.capabilities.hasDeployments).toBe(true);
      expect(client.capabilities.hasSubdeployments).toBe(true);
      expect(client.capabilities.hasProcedures).toBe(true);
      expect(client.capabilities.hasSamplingFeatures).toBe(true);
      expect(client.capabilities.hasProperties).toBe(true);
    });

    it('detects all Part 2 resources', () => {
      expect(client.capabilities.hasDataStreams).toBe(true);
      expect(client.capabilities.hasControlStreams).toBe(true);
      expect(client.capabilities.hasCommandFeasibility).toBe(true);
      expect(client.capabilities.hasSystemEvents).toBe(true);
    });

    it('detects all operations', () => {
      expect(client.capabilities.hasCRUD).toBe(true);
      expect(client.capabilities.hasUpdate).toBe(true);
      expect(client.capabilities.hasAdvancedFiltering).toBe(true);
    });

    it('detects all encodings', () => {
      expect(client.capabilities.supportsGeoJSON).toBe(true);
      expect(client.capabilities.supportsSensorML).toBe(true);
      expect(client.capabilities.supportsOMJSON).toBe(true);
      expect(client.capabilities.supportsSWEJSON).toBe(true);
      expect(client.capabilities.supportsSWEText).toBe(true);
      expect(client.capabilities.supportsSWEBinary).toBe(true);
    });

    it('initializes all resource clients', () => {
      expect(client.systems).toBeDefined();
      expect(client.deployments).toBeDefined();
      expect(client.procedures).toBeDefined();
      expect(client.properties).toBeDefined();
      expect(client.samplingFeatures).toBeDefined();
      expect(client.datastreams).toBeDefined();
      expect(client.controlstreams).toBeDefined();
    });
  });

  describe('Partial Conformance (52°North Profile)', () => {
    beforeEach(async () => {
      // Mock /conformance with Part 1 full + Part 2 partial
      globalThis.fetch = jest.fn().mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(FIXTURES.conformance['52north']),
      });

      client = new CSAPIClient('https://52n.test.org');
      await client.initialize();
    });

    it('detects all Part 1 resources', () => {
      expect(client.capabilities.hasSystems).toBe(true);
      expect(client.capabilities.hasDeployments).toBe(true);
      expect(client.capabilities.hasProcedures).toBe(true);
    });

    it('detects partial Part 2 resources', () => {
      expect(client.capabilities.hasDataStreams).toBe(true);
      expect(client.capabilities.hasControlStreams).toBe(false); // MISSING
      expect(client.capabilities.hasCommandFeasibility).toBe(false);
      expect(client.capabilities.hasSystemEvents).toBe(false);
    });

    it('does not initialize ControlStreams client', () => {
      expect(client.controlstreams).toBeUndefined();
    });

    it('initializes DataStreams client', () => {
      expect(client.datastreams).toBeDefined();
    });
  });

  describe('Minimal Conformance (Read-Only System Registry)', () => {
    beforeEach(async () => {
      globalThis.fetch = jest.fn().mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(FIXTURES.conformance.minimalSystems),
      });

      client = new CSAPIClient('https://minimal.test.org');
      await client.initialize();
    });

    it('detects only Systems resource', () => {
      expect(client.capabilities.hasSystems).toBe(true);
      expect(client.capabilities.hasDeployments).toBe(false);
      expect(client.capabilities.hasProcedures).toBe(false);
      expect(client.capabilities.hasDataStreams).toBe(false);
    });

    it('detects no CRUD operations', () => {
      expect(client.capabilities.hasCRUD).toBe(false);
      expect(client.capabilities.hasUpdate).toBe(false);
    });

    it('only initializes Systems client', () => {
      expect(client.systems).toBeDefined();
      expect(client.deployments).toBeUndefined();
      expect(client.datastreams).toBeUndefined();
    });
  });
});
```

### 4.3 Method Availability Tests

**File:** `src/ogc-api/csapi/systems.spec.ts`

```typescript
describe('SystemsResource Method Availability', () => {
  let client: CSAPIClient;

  describe('Read-Only Server', () => {
    beforeEach(async () => {
      globalThis.fetch = jest.fn().mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(FIXTURES.conformance.minimalSystems),
      });

      client = new CSAPIClient('https://readonly.test.org');
      await client.initialize();
    });

    it('list() method works', async () => {
      globalThis.fetch = jest.fn().mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ features: [] }),
      });

      await expect(client.systems.list()).resolves.toBeDefined();
    });

    it('get() method works', async () => {
      globalThis.fetch = jest.fn().mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ id: 'sys123' }),
      });

      await expect(client.systems.get('sys123')).resolves.toBeDefined();
    });

    it('create() throws ConformanceError', async () => {
      await expect(client.systems.create({ name: 'Test' })).rejects.toThrow(
        ConformanceError
      );
    });

    it('update() throws ConformanceError', async () => {
      await expect(
        client.systems.update('sys123', { name: 'Updated' })
      ).rejects.toThrow(ConformanceError);
    });

    it('replace() throws ConformanceError', async () => {
      await expect(
        client.systems.replace('sys123', { name: 'Test' })
      ).rejects.toThrow(ConformanceError);
    });

    it('delete() throws ConformanceError', async () => {
      await expect(client.systems.delete('sys123')).rejects.toThrow(
        ConformanceError
      );
    });

    it('ConformanceError contains correct metadata', async () => {
      try {
        await client.systems.create({ name: 'Test' });
        fail('Should have thrown');
      } catch (error) {
        expect(error).toBeInstanceOf(ConformanceError);
        expect(error.capability).toBe('hasCRUD');
        expect(error.operation).toBe('create');
        expect(error.message).toContain('/conf/create-replace-delete');
      }
    });
  });

  describe('Transactional Server', () => {
    beforeEach(async () => {
      globalThis.fetch = jest.fn().mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(FIXTURES.conformance.transactionalSystems),
      });

      client = new CSAPIClient('https://crud.test.org');
      await client.initialize();
    });

    it('all CRUD methods work', async () => {
      globalThis.fetch = jest
        .fn()
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ id: 'sys123' }),
        }) // create
        .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve({}) }) // update
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({ id: 'sys123' }),
        }) // replace
        .mockResolvedValueOnce({ ok: true, status: 204 }); // delete

      await expect(
        client.systems.create({ name: 'Test' })
      ).resolves.toBeDefined();
      await expect(
        client.systems.update('sys123', { name: 'Updated' })
      ).resolves.toBeUndefined();
      await expect(
        client.systems.replace('sys123', { name: 'Test' })
      ).resolves.toBeDefined();
      await expect(client.systems.delete('sys123')).resolves.toBeUndefined();
    });
  });

  describe('Nested Resources', () => {
    it('subsystems() returns null when not supported', async () => {
      globalThis.fetch = jest.fn().mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(FIXTURES.conformance.minimalSystems),
      });

      client = new CSAPIClient('https://test.org');
      await client.initialize();

      expect(client.systems.subsystems('sys123')).toBeNull();
    });

    it('subsystems() returns resource when supported', async () => {
      globalThis.fetch = jest.fn().mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(FIXTURES.conformance.opensensorhub),
      });

      client = new CSAPIClient('https://test.org');
      await client.initialize();

      const subsystems = client.systems.subsystems('sys123');
      expect(subsystems).toBeDefined();
      expect(subsystems).toBeInstanceOf(SubsystemsResource);
    });

    it('datastreams() returns null when Part 2 not supported', async () => {
      globalThis.fetch = jest.fn().mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(FIXTURES.conformance.minimalSystems),
      });

      client = new CSAPIClient('https://test.org');
      await client.initialize();

      expect(client.systems.datastreams('sys123')).toBeNull();
    });

    it('events() returns null when not supported (52°North)', async () => {
      globalThis.fetch = jest.fn().mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(FIXTURES.conformance['52north']),
      });

      client = new CSAPIClient('https://test.org');
      await client.initialize();

      expect(client.systems.events('sys123')).toBeNull();
    });
  });
});
```

---

## 5. Conformance Test Scenarios

### 5.1 Test Scenario Matrix

| Scenario                             | Profile       | Part 1               | Part 2              | CRUD | Advanced Filtering | Key Tests                                 |
| ------------------------------------ | ------------- | -------------------- | ------------------- | ---- | ------------------ | ----------------------------------------- |
| **S1: Minimal System Registry**      | Read-only     | Systems only         | None                | ❌   | ❌                 | Resource init, read-only ops, CRUD errors |
| **S2: Minimal Deployment Registry**  | Read-only     | Deployments only     | None                | ❌   | ❌                 | Different resource type, format detection |
| **S3: Transactional Systems**        | Full CRUD     | Systems + Subsystems | None                | ✅   | ✅                 | All CRUD ops, CQL2 filtering              |
| **S4: Sensor Data Server**           | 52°North-like | Full Part 1          | DataStreams only    | ✅   | ✅                 | Partial Part 2, no ControlStreams         |
| **S5: Actuator Control Server**      | Control-only  | Systems only         | ControlStreams only | ✅   | ❌                 | Control without sensors                   |
| **S6: Full-Featured Server**         | OpenSensorHub | All Part 1           | All Part 2          | ✅   | ✅                 | All features, baseline                    |
| **S7: Missing Conformance Endpoint** | Error case    | N/A                  | N/A                 | N/A  | N/A                | Initialization failure                    |
| **S8: Malformed Conformance**        | Error case    | N/A                  | N/A                 | N/A  | N/A                | Parse errors, graceful handling           |

### 5.2 Scenario Implementations

**S1: Minimal System Registry**

```typescript
describe('Scenario 1: Minimal System Registry', () => {
  let client: CSAPIClient;

  beforeEach(async () => {
    globalThis.fetch = jest
      .fn()
      .mockImplementation(mockFetchForProfile('minimal-systems'));
    client = new CSAPIClient('https://test.org');
    await client.initialize();
  });

  it('initializes only Systems resource', () => {
    expect(client.systems).toBeDefined();
    expect(client.deployments).toBeUndefined();
    expect(client.procedures).toBeUndefined();
    expect(client.datastreams).toBeUndefined();
  });

  it('Systems GET operations work', async () => {
    const systems = await client.systems.list();
    expect(systems.features).toBeInstanceOf(Array);

    const system = await client.systems.get('sys123');
    expect(system.id).toBe('sys123');
  });

  it('Systems CRUD operations throw ConformanceError', async () => {
    await expect(client.systems.create({ name: 'Test' })).rejects.toThrow(
      ConformanceError
    );
    await expect(
      client.systems.update('sys123', { name: 'Test' })
    ).rejects.toThrow(ConformanceError);
    await expect(client.systems.delete('sys123')).rejects.toThrow(
      ConformanceError
    );
  });

  it('Subsystems returns null', () => {
    expect(client.systems.subsystems('sys123')).toBeNull();
  });

  it('Advanced filtering unavailable', () => {
    expect(client.capabilities.hasAdvancedFiltering).toBe(false);
  });
});
```

**S4: Sensor Data Server (52°North Profile)**

```typescript
describe('Scenario 4: Sensor Data Server (52°North)', () => {
  let client: CSAPIClient;

  beforeEach(async () => {
    globalThis.fetch = jest
      .fn()
      .mockImplementation(mockFetchForProfile('52north'));
    client = new CSAPIClient('https://test.org');
    await client.initialize();
  });

  it('Part 1 fully available', () => {
    expect(client.systems).toBeDefined();
    expect(client.deployments).toBeDefined();
    expect(client.procedures).toBeDefined();
    expect(client.properties).toBeDefined();
    expect(client.samplingFeatures).toBeDefined();
  });

  it('Part 2 DataStreams available', () => {
    expect(client.datastreams).toBeDefined();
    expect(client.capabilities.hasDataStreams).toBe(true);
  });

  it('Part 2 ControlStreams NOT available', () => {
    expect(client.controlstreams).toBeUndefined();
    expect(client.capabilities.hasControlStreams).toBe(false);
    expect(client.capabilities.hasCommandFeasibility).toBe(false);
  });

  it('System.datastreams() returns resource', () => {
    const datastreams = client.systems.datastreams('sys123');
    expect(datastreams).toBeDefined();
  });

  it('System.events() returns null', () => {
    expect(client.systems.events('sys123')).toBeNull();
  });

  it('DataStreams CRUD operations work', async () => {
    await expect(
      client.datastreams.create({ system: 'sys123', name: 'DS1' })
    ).resolves.toBeDefined();
    await expect(client.datastreams.list()).resolves.toBeDefined();
  });

  it('Full CRUD available on Part 1', () => {
    expect(client.capabilities.hasCRUD).toBe(true);
    expect(client.capabilities.hasUpdate).toBe(true);
  });

  it('Advanced filtering available', () => {
    expect(client.capabilities.hasAdvancedFiltering).toBe(true);
  });

  it('Encodings: GeoJSON, SensorML, O&M JSON, SWE JSON', () => {
    expect(client.capabilities.supportsGeoJSON).toBe(true);
    expect(client.capabilities.supportsSensorML).toBe(true);
    expect(client.capabilities.supportsOMJSON).toBe(true);
    expect(client.capabilities.supportsSWEJSON).toBe(true);
    expect(client.capabilities.supportsSWEText).toBe(false);
    expect(client.capabilities.supportsSWEBinary).toBe(false);
  });
});
```

**S6: Full-Featured Server (OpenSensorHub Profile)**

```typescript
describe('Scenario 6: Full-Featured Server (OSH)', () => {
  let client: CSAPIClient;

  beforeEach(async () => {
    globalThis.fetch = jest
      .fn()
      .mockImplementation(mockFetchForProfile('opensensorhub'));
    client = new CSAPIClient('https://test.org');
    await client.initialize();
  });

  it('all resource clients initialized', () => {
    expect(client.systems).toBeDefined();
    expect(client.deployments).toBeDefined();
    expect(client.procedures).toBeDefined();
    expect(client.properties).toBeDefined();
    expect(client.samplingFeatures).toBeDefined();
    expect(client.datastreams).toBeDefined();
    expect(client.controlstreams).toBeDefined();
  });

  it('all capabilities enabled', () => {
    const caps = client.capabilities;

    // Part 1
    expect(caps.hasSystems).toBe(true);
    expect(caps.hasSubsystems).toBe(true);
    expect(caps.hasDeployments).toBe(true);
    expect(caps.hasSubdeployments).toBe(true);
    expect(caps.hasProcedures).toBe(true);
    expect(caps.hasSamplingFeatures).toBe(true);
    expect(caps.hasProperties).toBe(true);

    // Part 2
    expect(caps.hasDataStreams).toBe(true);
    expect(caps.hasControlStreams).toBe(true);
    expect(caps.hasCommandFeasibility).toBe(true);
    expect(caps.hasSystemEvents).toBe(true);

    // Operations
    expect(caps.hasCRUD).toBe(true);
    expect(caps.hasUpdate).toBe(true);
    expect(caps.hasAdvancedFiltering).toBe(true);

    // Formats
    expect(caps.supportsGeoJSON).toBe(true);
    expect(caps.supportsSensorML).toBe(true);
    expect(caps.supportsOMJSON).toBe(true);
    expect(caps.supportsSWEJSON).toBe(true);
    expect(caps.supportsSWEText).toBe(true);
    expect(caps.supportsSWEBinary).toBe(true);
  });

  it('all nested resources available', () => {
    expect(client.systems.subsystems('sys123')).toBeDefined();
    expect(client.systems.datastreams('sys123')).toBeDefined();
    expect(client.systems.events('sys123')).toBeDefined();

    expect(client.deployments.subdeployments('dep123')).toBeDefined();
  });

  it('all CRUD operations work on all resources', async () => {
    // Test sample of resources
    await expect(
      client.systems.create({ name: 'Test' })
    ).resolves.toBeDefined();
    await expect(
      client.deployments.create({ name: 'Test' })
    ).resolves.toBeDefined();
    await expect(
      client.datastreams.create({ system: 'sys123', name: 'DS1' })
    ).resolves.toBeDefined();
    await expect(
      client.controlstreams.create({ system: 'sys123', name: 'CS1' })
    ).resolves.toBeDefined();
  });
});
```

**S7: Missing Conformance Endpoint**

```typescript
describe('Scenario 7: Missing Conformance Endpoint', () => {
  it('throws error when /conformance returns 404', async () => {
    globalThis.fetch = jest.fn().mockResolvedValueOnce({
      ok: false,
      status: 404,
    });

    const client = new CSAPIClient('https://test.org');
    await expect(client.initialize()).rejects.toThrow(
      'Conformance endpoint failed: 404'
    );
  });

  it('throws error when /conformance returns 500', async () => {
    globalThis.fetch = jest.fn().mockResolvedValueOnce({
      ok: false,
      status: 500,
    });

    const client = new CSAPIClient('https://test.org');
    await expect(client.initialize()).rejects.toThrow(
      'Conformance endpoint failed: 500'
    );
  });

  it('throws error when /conformance network fails', async () => {
    globalThis.fetch = jest
      .fn()
      .mockRejectedValueOnce(new Error('Network error'));

    const client = new CSAPIClient('https://test.org');
    await expect(client.initialize()).rejects.toThrow('Network error');
  });
});
```

**S8: Malformed Conformance**

```typescript
describe('Scenario 8: Malformed Conformance', () => {
  it('handles missing conformsTo array', async () => {
    globalThis.fetch = jest.fn().mockResolvedValueOnce({
      ok: true,
      json: () =>
        Promise.resolve({
          // Missing conformsTo
        }),
    });

    const client = new CSAPIClient('https://test.org');
    await client.initialize();

    expect(client.capabilities.hasSystems).toBe(false);
    expect(client.systems).toBeUndefined();
  });

  it('handles empty conformsTo array', async () => {
    globalThis.fetch = jest.fn().mockResolvedValueOnce({
      ok: true,
      json: () =>
        Promise.resolve({
          conformsTo: [],
        }),
    });

    const client = new CSAPIClient('https://test.org');
    await client.initialize();

    expect(Object.values(client.capabilities).every((v) => v === false)).toBe(
      true
    );
  });

  it('handles invalid JSON', async () => {
    globalThis.fetch = jest.fn().mockResolvedValueOnce({
      ok: true,
      json: () => Promise.reject(new SyntaxError('Invalid JSON')),
    });

    const client = new CSAPIClient('https://test.org');
    await expect(client.initialize()).rejects.toThrow('Invalid JSON');
  });

  it('handles non-array conformsTo', async () => {
    globalThis.fetch = jest.fn().mockResolvedValueOnce({
      ok: true,
      json: () =>
        Promise.resolve({
          conformsTo:
            'http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/system',
        }),
    });

    const client = new CSAPIClient('https://test.org');
    await client.initialize();

    // Should handle gracefully (treat as empty)
    expect(client.capabilities.hasSystems).toBe(false);
  });
});
```

---

## 6. Server Capability Mocking Strategy

### 6.1 Fixture Structure

```
fixtures/ogc-api/csapi/
  conformance/
    opensensorhub.json          # Full conformance (25 classes)
    52north.json                # Partial Part 2 (DataStreams only)
    minimal-systems.json        # Profile 1
    minimal-deployments.json    # Profile 2
    transactional-systems.json  # Profile 3
    sensor-data-server.json     # Profile 4 (52N-like)
    actuator-control-server.json # Profile 5
    empty.json                  # Empty conformsTo array
    malformed.json              # Test error handling

  collections/
    opensensorhub/
      systems.json              # Systems collection metadata
      deployments.json
      datastreams.json
      controlstreams.json
      # ... etc.

    52north/
      systems.json
      datastreams.json          # DataStreams present
      # No controlstreams.json - not implemented

    minimal/
      systems.json              # Only systems collection
```

### 6.2 Fixture Examples

**opensensorhub.json (Full Conformance):**

```json
{
  "conformsTo": [
    "http://www.opengis.net/spec/ogcapi-common-1/1.0/conf/core",
    "http://www.opengis.net/spec/ogcapi-common-2/1.0/conf/collections",
    "http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/core",
    "http://www.opengis.net/spec/ogcapi-features-4/1.0/conf/create-replace-delete",

    "http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/api-common",
    "http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/system",
    "http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/subsystem",
    "http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/deployment",
    "http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/subdeployment",
    "http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/procedure",
    "http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/sf",
    "http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/property",
    "http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/advanced-filtering",
    "http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/create-replace-delete",
    "http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/update",
    "http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/geojson",
    "http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/sensorml",

    "http://www.opengis.net/spec/ogcapi-connectedsystems-2/1.0/conf/api-common",
    "http://www.opengis.net/spec/ogcapi-connectedsystems-2/1.0/conf/datastream",
    "http://www.opengis.net/spec/ogcapi-connectedsystems-2/1.0/conf/controlstream",
    "http://www.opengis.net/spec/ogcapi-connectedsystems-2/1.0/conf/feasibility",
    "http://www.opengis.net/spec/ogcapi-connectedsystems-2/1.0/conf/system-event",
    "http://www.opengis.net/spec/ogcapi-connectedsystems-2/1.0/conf/advanced-filtering",
    "http://www.opengis.net/spec/ogcapi-connectedsystems-2/1.0/conf/create-replace-delete",
    "http://www.opengis.net/spec/ogcapi-connectedsystems-2/1.0/conf/update",
    "http://www.opengis.net/spec/ogcapi-connectedsystems-2/1.0/conf/json",
    "http://www.opengis.net/spec/ogcapi-connectedsystems-2/1.0/conf/swecommon-json",
    "http://www.opengis.net/spec/ogcapi-connectedsystems-2/1.0/conf/swecommon-text",
    "http://www.opengis.net/spec/ogcapi-connectedsystems-2/1.0/conf/swecommon-binary"
  ]
}
```

**52north.json (Partial Part 2):**

```json
{
  "conformsTo": [
    "http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/api-common",
    "http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/system",
    "http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/subsystem",
    "http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/deployment",
    "http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/subdeployment",
    "http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/procedure",
    "http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/sf",
    "http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/property",
    "http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/advanced-filtering",
    "http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/create-replace-delete",
    "http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/update",
    "http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/geojson",
    "http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/sensorml",

    "http://www.opengis.net/spec/ogcapi-connectedsystems-2/1.0/conf/api-common",
    "http://www.opengis.net/spec/ogcapi-connectedsystems-2/1.0/conf/datastream",
    "http://www.opengis.net/spec/ogcapi-connectedsystems-2/1.0/conf/advanced-filtering",
    "http://www.opengis.net/spec/ogcapi-connectedsystems-2/1.0/conf/create-replace-delete",
    "http://www.opengis.net/spec/ogcapi-connectedsystems-2/1.0/conf/update",
    "http://www.opengis.net/spec/ogcapi-connectedsystems-2/1.0/conf/json",
    "http://www.opengis.net/spec/ogcapi-connectedsystems-2/1.0/conf/swecommon-json"
  ]
}
```

**minimal-systems.json (Profile 1):**

```json
{
  "conformsTo": [
    "http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/api-common",
    "http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/system",
    "http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/geojson"
  ]
}
```

### 6.3 Mock Fetch Implementation

```typescript
// test-setup.ts
import { readFile } from 'fs/promises';
import path from 'path';

const FIXTURES_ROOT = path.join(__dirname, 'fixtures', 'ogc-api', 'csapi');

export function mockFetchForProfile(profile: string) {
  return async (urlOrInfo: RequestInfo | URL): Promise<Response> => {
    const url = new URL(
      urlOrInfo instanceof URL || typeof urlOrInfo === 'string'
        ? urlOrInfo
        : urlOrInfo.url
    );

    const pathname = url.pathname.replace(/\/$/, '');

    // Mock /conformance endpoint
    if (pathname.endsWith('/conformance')) {
      const conformancePath = path.join(
        FIXTURES_ROOT,
        'conformance',
        `${profile}.json`
      );
      const contents = await readFile(conformancePath, 'utf-8');
      return {
        ok: true,
        status: 200,
        json: () => Promise.resolve(JSON.parse(contents)),
      } as Response;
    }

    // Mock /collections endpoint
    if (pathname.endsWith('/collections')) {
      const collectionsPath = path.join(
        FIXTURES_ROOT,
        'collections',
        profile,
        'collections.json'
      );
      const contents = await readFile(collectionsPath, 'utf-8');
      return {
        ok: true,
        status: 200,
        json: () => Promise.resolve(JSON.parse(contents)),
      } as Response;
    }

    // Mock resource endpoints
    if (pathname.includes('/systems')) {
      const systemsPath = path.join(
        FIXTURES_ROOT,
        'collections',
        profile,
        'systems.json'
      );
      const contents = await readFile(systemsPath, 'utf-8');
      return {
        ok: true,
        status: 200,
        json: () => Promise.resolve(JSON.parse(contents)),
      } as Response;
    }

    // ... similar for other resources

    return {
      ok: false,
      status: 404,
    } as Response;
  };
}

// Usage in tests
beforeEach(() => {
  globalThis.fetch = jest
    .fn()
    .mockImplementation(mockFetchForProfile('52north'));
});
```

---

## 7. Test Implementation Templates

### 7.1 Conformance Check Function Template

```typescript
// src/ogc-api/csapi/info.ts
export function checkHasConnectedSystems([conformance]: [
  ConformanceClass[]
]): boolean {
  return (
    conformance.indexOf(
      'http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/api-common'
    ) > -1
  );
}

// Test template
describe('checkHasConnectedSystems', () => {
  it('returns true when Part 1 common conformance present', () => {
    const conformance = [
      'http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/api-common',
    ];
    expect(checkHasConnectedSystems([conformance])).toBe(true);
  });

  it('returns false when no CSAPI conformance', () => {
    const conformance = [
      'http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/core',
    ];
    expect(checkHasConnectedSystems([conformance])).toBe(false);
  });

  it('returns false when empty array', () => {
    expect(checkHasConnectedSystems([[]])).toBe(false);
  });
});
```

### 7.2 Capability Detection Test Template

```typescript
describe('ServerCapabilities Detection - [PROFILE NAME]', () => {
  let client: CSAPIClient;

  beforeEach(async () => {
    globalThis.fetch = jest.fn().mockImplementation(mockFetchForProfile('[PROFILE]'));
    client = new CSAPIClient('https://test.org');
    await client.initialize();
  });

  describe('Resource Availability', () => {
    it('detects [RESOURCE] as available/unavailable', () => {
      expect(client.capabilities.has[RESOURCE]).toBe([true/false]);
      expect(client.[resource]).toBe[Defined/Undefined]();
    });

    // Repeat for all resources
  });

  describe('Operation Availability', () => {
    it('detects CRUD as available/unavailable', () => {
      expect(client.capabilities.hasCRUD).toBe([true/false]);
    });

    it('detects Update as available/unavailable', () => {
      expect(client.capabilities.hasUpdate).toBe([true/false]);
    });

    it('detects Advanced Filtering as available/unavailable', () => {
      expect(client.capabilities.hasAdvancedFiltering).toBe([true/false]);
    });
  });

  describe('Format Support', () => {
    it('detects supported encodings', () => {
      expect(client.capabilities.supportsGeoJSON).toBe([true/false]);
      expect(client.capabilities.supportsSensorML).toBe([true/false]);
      // ... etc.
    });
  });
});
```

### 7.3 Method Availability Test Template

```typescript
describe('[RESOURCE]Resource Method Availability - [PROFILE]', () => {
  let client: CSAPIClient;

  beforeEach(async () => {
    globalThis.fetch = jest.fn().mockImplementation(mockFetchForProfile('[PROFILE]'));
    client = new CSAPIClient('https://test.org');
    await client.initialize();
  });

  it('list() method works', async () => {
    globalThis.fetch = jest.fn().mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ features: [] })
    });

    await expect(client.[resource].list()).resolves.toBeDefined();
  });

  it('get() method works', async () => {
    globalThis.fetch = jest.fn().mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ id: '[ID]' })
    });

    await expect(client.[resource].get('[ID]')).resolves.toBeDefined();
  });

  // If CRUD NOT available
  it('create() throws ConformanceError', async () => {
    await expect(client.[resource].create({ name: 'Test' }))
      .rejects.toThrow(ConformanceError);
  });

  // If CRUD available
  it('create() works', async () => {
    globalThis.fetch = jest.fn().mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ id: '[ID]' })
    });

    await expect(client.[resource].create({ name: 'Test' }))
      .resolves.toBeDefined();
  });

  // Repeat for update(), replace(), delete()

  // If nested resources
  it('[NESTED]() returns resource/null based on conformance', () => {
    const nested = client.[resource].[nested]('[ID]');
    expect(nested).toBe[Defined/Null]();
  });
});
```

### 7.4 Integration Test Template

```typescript
describe('CSAPI Integration - [PROFILE] Server', () => {
  let endpoint: OgcApiEndpoint;

  beforeEach(async () => {
    globalThis.fetch = jest
      .fn()
      .mockImplementation(mockFetchForProfile('[PROFILE]'));
    endpoint = new OgcApiEndpoint('https://test.org');
  });

  it('detects CSAPI support', async () => {
    await expect(endpoint.hasConnectedSystems).resolves.toBe(true);
  });

  it('lists CSAPI collections', async () => {
    const collections = await endpoint.csapiCollections;
    expect(collections).toEqual([EXPECTED_COLLECTIONS]);
  });

  it('can get resource builder', async () => {
    const builder = await endpoint.csapi('[RESOURCE]');
    expect(builder).toBeDefined();
    expect(builder.supportedOperations).toEqual([EXPECTED_OPS]);
  });

  it('complete workflow: [DESCRIBE WORKFLOW]', async () => {
    // Multi-step workflow test
    const step1 = await endpoint.csapi('systems');
    const step2 = await step1.list();
    const step3 = await endpoint.csapi('datastreams');
    // ... etc.
  });
});
```

---

## 8. Implementation Estimates

### 8.1 File Structure and Lines of Code

| File                                        | Purpose                               | Est. Lines | Priority |
| ------------------------------------------- | ------------------------------------- | ---------- | -------- |
| **src/ogc-api/csapi/info.ts**               | Conformance check function            | 10-20      | HIGH     |
| **src/ogc-api/csapi/info.spec.ts**          | Conformance function tests            | 50-100     | HIGH     |
| **src/ogc-api/csapi/capabilities.ts**       | ServerCapabilities interface          | 50-80      | HIGH     |
| **src/ogc-api/csapi/capabilities.spec.ts**  | Capability detection tests            | 300-400    | HIGH     |
| **src/ogc-api/csapi/systems.spec.ts**       | Systems method availability tests     | 200-300    | HIGH     |
| **src/ogc-api/csapi/deployments.spec.ts**   | Deployments method availability tests | 150-200    | MEDIUM   |
| **src/ogc-api/csapi/datastreams.spec.ts**   | DataStreams method availability tests | 150-200    | MEDIUM   |
| **src/ogc-api/csapi/conformance-errors.ts** | ConformanceError class                | 20-30      | HIGH     |
| **fixtures/ogc-api/csapi/conformance/**     | Mock conformance responses            | 200-300    | HIGH     |
| **fixtures/ogc-api/csapi/collections/**     | Mock collection metadata              | 300-400    | MEDIUM   |

**Total Estimated Lines:** 1200-1500 lines

### 8.2 Implementation Phases

**Phase 1: Core Conformance Detection (2-3 days)**

- `checkHasConnectedSystems()` function
- `info.spec.ts` tests
- OgcApiEndpoint integration
- Fixtures: opensensorhub.json, 52north.json, minimal-systems.json

**Phase 2: Capability Detection (3-4 days)**

- `ServerCapabilities` interface
- `CSAPIClient.detectCapabilities()` implementation
- `capabilities.spec.ts` tests (all profiles)
- Fixtures: remaining conformance profiles

**Phase 3: Method Availability Enforcement (4-5 days)**

- `ConformanceError` class
- CRUD method conformance checks in all resource classes
- `systems.spec.ts`, `deployments.spec.ts`, `datastreams.spec.ts` tests
- Nested resource availability checks

**Phase 4: Integration Tests (2-3 days)**

- End-to-end workflow tests
- Multi-resource integration scenarios
- Error handling integration

**Total Estimated Time:** 11-15 days (2-3 weeks)

### 8.3 Testing Coverage Goals

**Target Coverage:**

- Statement: 95%+
- Branch: 90%+
- Function: 100%

**Critical Paths:**

- Conformance detection (100% coverage)
- Capability detection (100% coverage)
- Method availability enforcement (100% coverage)
- Error handling (90% coverage)

---

## Appendix A: Conformance URI Reference

### Part 1 URIs

```
http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/api-common
http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/system
http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/subsystem
http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/deployment
http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/subdeployment
http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/procedure
http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/sf
http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/property
http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/advanced-filtering
http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/create-replace-delete
http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/update
http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/geojson
http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/sensorml
```

### Part 2 URIs

```
http://www.opengis.net/spec/ogcapi-connectedsystems-2/1.0/conf/api-common
http://www.opengis.net/spec/ogcapi-connectedsystems-2/1.0/conf/datastream
http://www.opengis.net/spec/ogcapi-connectedsystems-2/1.0/conf/controlstream
http://www.opengis.net/spec/ogcapi-connectedsystems-2/1.0/conf/feasibility
http://www.opengis.net/spec/ogcapi-connectedsystems-2/1.0/conf/system-event
http://www.opengis.net/spec/ogcapi-connectedsystems-2/1.0/conf/advanced-filtering
http://www.opengis.net/spec/ogcapi-connectedsystems-2/1.0/conf/create-replace-delete
http://www.opengis.net/spec/ogcapi-connectedsystems-2/1.0/conf/update
http://www.opengis.net/spec/ogcapi-connectedsystems-2/1.0/conf/json
http://www.opengis.net/spec/ogcapi-connectedsystems-2/1.0/conf/swecommon-json
http://www.opengis.net/spec/ogcapi-connectedsystems-2/1.0/conf/swecommon-text
http://www.opengis.net/spec/ogcapi-connectedsystems-2/1.0/conf/swecommon-binary
```

---

## Appendix B: Key Insights

1. **No Mandatory Core:** Unlike typical OGC APIs, CSAPI has no required "core" conformance class. Servers choose which resource types to implement.

2. **52°North = Primary Test Case:** Partial Part 2 implementation (DataStreams only, no ControlStreams) is the most important test scenario for client adaptability.

3. **Conformance Detection = Critical Path:** `/conformance` endpoint query is the first operation - determines all subsequent client behavior.

4. **Capability-Based Initialization:** Client conditionally initializes resource clients based on detected conformance.

5. **Two Error Strategies:** Client can either throw `ConformanceError` (fail fast) or return `null` (graceful degradation). Both should be tested.

6. **Hierarchical Dependencies:** Some conformance classes require others (e.g., Subsystems requires System, Update requires CRUD).

7. **Format Requirements:** At least 1 encoding required per Part. Part 2 DataStreams requires O&M JSON encoding.

8. **Real-World Testing:** Integration tests should use fixtures based on actual server profiles (OpenSensorHub, 52°North).

---

**END OF FINDINGS DOCUMENT**
