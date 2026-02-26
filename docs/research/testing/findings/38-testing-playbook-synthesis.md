# CSAPI Testing Playbook

**Research Plan:** [Research Plan 38: Testing Playbook Synthesis](../research-plans/38-testing-playbook-synthesis.md)

**Research Questions:** 6 core questions about step-by-step testing process for each component, workflow for each roadmap phase, validating tests during writing, tools and commands needed, measuring progress, and illustrative examples.

**Methodology:** 7-phase systematic synthesis (Phase 1: Synthesis of All Research → Phase 2: Workflow Design by Phase → Phase 3: Component Pattern Synthesis → Phase 4: Practical Example Creation → Phase 5: Tool and Command Documentation → Phase 6: Progress Tracking Design → Phase 7: Final Synthesis)

**Research Time:** 45 minutes – February 6, 2026

**Primary Source(s):**

- ALL previous section deliverables (Sections 1-37)
- [ROADMAP](../../../planning/ROADMAP.md)
- [Implementation Guide](../../../planning/csapi-implementation-guide.md)
- Section 36 deliverable: Test Quality Checklist

**Supporting Resources:**

- Section 35: [JSDoc Testing Documentation Standards](35-jsdoc-testing-documentation-standards.md) (test documentation)
- Section 37: [Test Maintenance and Evolution Strategy](37-test-maintenance-evolution-strategy.md) (maintenance)
- Sections 8-31: All component testing specifications

**Document Purpose:** Comprehensive step-by-step testing playbook synthesizing all 37 research sections into practical implementation workflows, component patterns, examples, tools, and validation mechanisms for Phase 1-4 ROADMAP execution.

**Version:** 1.0  
**Last Updated:** February 6, 2026  
**Based On:** Sections 1-37 Research Findings + ROADMAP v3.0

> **⚠️ Phase 3 Review Notice (February 14, 2026)**
>
> This playbook was written February 6, 2026. Phase 2A-2F review corrections (February 12-13, 2026) take precedence where they conflict with this document. Key conflicts:
>
> - **Performance testing is OUT OF SCOPE** (Doc 33) — Parts 3.4, 6.4, and 8.3 contain performance content that should be disregarded
> - **Phase 3 task count:** This document references "15 subtasks" but ROADMAP v3.0 specifies 17 tasks — refer to ROADMAP v3.0 for authoritative task list
> - **Coverage targets:** This document's targets (90/85/88%) are stretch goals; ROADMAP v3.0 minimum is >80% statement and branch
> - **Phase 1 checklist (Part 7.2):** Checkmarks are examples of completed format, not actual progress
>
> See [Phase 3 Synthesis Validation Report](../review/phase-3-synthesis-validation.md) for the full 10-issue review.

---

## How to Use This Playbook

This playbook transforms 37 research sections into **step-by-step testing workflows** you can follow during CSAPI implementation.

**Structure:**

- **Part 1:** Setup (one-time)
- **Part 2:** Phase-by-phase workflows (follow during implementation)
- **Part 3:** Component patterns (reference when writing tests)
- **Part 4:** Examples (copy/adapt these)
- **Part 5:** Quality validation (use before committing)
- **Part 6:** Tools (daily commands)
- **Part 7:** Progress tracking (measure completion)
- **Part 8:** Troubleshooting (when stuck)
- **Part 9:** Reference (quick lookup)
- **Part 10:** Maintenance (ongoing)

**Quick Start:**

1. Complete Part 1 (Setup) once
2. Go to Part 2 for your current ROADMAP phase
3. Follow step-by-step workflow
4. Reference Part 3 for component-specific patterns
5. Use Part 4 examples as templates
6. Validate with Part 5 checklist before committing

---

## Part 1: Getting Started

### 1.1 Prerequisites

**Before starting any testing:**

✅ **Dependencies Installed:**

```bash
npm install
```

✅ **Test Framework Configured:**

- Jest 29.7.0+ installed
- TypeScript 5.3.3+ configured
- Coverage reporting enabled

✅ **Knowledge Requirements:**

- TypeScript fundamentals
- Jest testing basics
- CSAPI specification familiarity (read Parts 1-3 overview)
- ogc-client architecture (read existing Features/Tiles implementations)

✅ **Research Sections Read:**

- Section 1: EDR Test Blueprint (upstream patterns)
- Section 12: QueryBuilder Testing Strategy (core approach)
- Section 34: Test Utility Design (helper functions)
- Section 35: JSDoc Standards (documentation)
- Section 36: Quality Checklist (validation)

### 1.2 Test Environment Setup

**Directory Structure:**

```
src/
  ogc-api/
    csapi/
      model.spec.ts
      helpers.spec.ts
      url_builder.spec.ts
      test-utils.ts
      parsers/
        sensorml-parser.spec.ts
        swe-common-parser.spec.ts
fixtures/
  ogc-api/
    csapi/
      collections/
      systems/
      datastreams/
      observations/
      sensorml/
      swe-common/
```

**Create Test Utilities (Phase 1, Task 2):**

`src/ogc-api/csapi/test-utils.ts`:

```typescript
import { URL } from 'url';

/**
 * Parse and validate URL structure.
 * USE THIS IN EVERY URL TEST - validates both URL correctness and structure.
 *
 * NOTE: This is a simplified parse-only version. The authoritative specification
 * with full validation support (accepting an `expected` parameter) is defined in
 * Section 34: Test Utility & Helper Design. During implementation, use the
 * Section 34 specification as the canonical reference.
 * See: [Section 34](34-test-utility-helper-design.md)
 */
export function parseAndValidateUrl(url: string): {
  pathname: string;
  searchParams: URLSearchParams;
  segments: string[];
} {
  const parsed = new URL(url, 'http://example.com');
  return {
    pathname: parsed.pathname,
    searchParams: parsed.searchParams,
    segments: parsed.pathname.split('/').filter(Boolean),
  };
}

/**
 * Load fixture from file system.
 */
export function loadFixture(path: string): any {
  return require(`../../../../fixtures/csapi/${path}`);
}

/**
 * Create mock OgcApiEndpoint for testing.
 */
export function createMockEndpoint(collectionInfo: any): any {
  return {
    apiUrl: 'https://example.com/api',
    _collections: [collectionInfo],
  };
}
```

### 1.3 Fixture Organization

**Fixture Structure (from Section 15, revised in Phase 2A — see also [Section 15 Part 2](15-part-2-fixture-documentation-best-practices.md) for documentation best practices):**

CSAPI fixtures use URL-path-mirroring under `fixtures/csapi/`, matching the upstream `fixtures/ogc-api/` pattern. Parser fixtures (SensorML, SWE Common) use flat directories. See [Section 15 §5.2](15-fixture-sourcing-organization.md) for the authoritative directory structure.

```
fixtures/
├── csapi/                                # CSAPI service protocol
│   ├── sample-server.json                # Landing page for mock CSAPI server
│   ├── sample-server/
│   │   ├── conformance.json              # /conformance
│   │   ├── collections.json              # /collections
│   │   ├── systems.json                  # /systems (collection)
│   │   ├── systems/
│   │   │   ├── weather-station-001.json  # /systems/{id}
│   │   │   └── weather-station-001/
│   │   │       └── datastreams.json      # /systems/{id}/datastreams
│   │   ├── datastreams.json
│   │   ├── datastreams/
│   │   │   └── temperature-series-001.json
│   │   └── observations.json
│   ├── no-csapi.json                     # Server without CSAPI conformance
│   └── empty-server.json                 # Server with empty collections
├── sensorml/                             # SensorML parser fixtures
│   ├── physicalsystem-weather-station.json
│   ├── physicalcomponent-thermometer.json
│   └── physicalsystem-missing-identifier.json
├── swe-common/                           # SWE Common parser fixtures
│   ├── json/
│   │   ├── quantity-temperature.json
│   │   ├── datarecord-weather-data.json
│   │   └── dataarray-trajectory.json
│   └── text/                             # Defer until parser supports text
├── ogc-api/                              # (existing — unchanged)
└── ...                                   # wfs/, wms/, wmts/, stac/, tms/
```

**Fixture Naming Convention:**

Follow existing project pattern - use descriptive filenames:

- `system-{type}-{identifier}.json` (e.g., `system-weather-station-001.json`)
- `deployment-{purpose}-{identifier}.json` (e.g., `deployment-arctic-mission-2025.json`)
- `datastream-{property}-{identifier}.json` (e.g., `datastream-temperature-001.json`)
- Include spec section in comments at top of fixture files based on OGC 23-001 v1.0.0

Example fixture header comment:

```json
{
  "_comment": "Based on OGC 23-001 v1.0.0 Section 19.1.5 - System Feature in GeoJSON",
  "type": "Feature",
  "id": "123",
  "properties": {
    "uid": "urn:x-ogc:systems:001",
    "name": "Weather Station 001"
  }
}
```

**Note**: Existing project fixtures (WFS, WMS, etc.) use descriptive names without additional documentation. Follow same pattern for CSAPI fixtures.

### 1.4 Tool Installation

**VSCode Extensions (Recommended):**

- Jest Runner (run individual tests)
- Test Explorer UI (view test tree)
- Coverage Gutters (inline coverage)

**Global Tools:**

```bash
npm install -g npm-check-updates  # Dependency updates
```

### 1.5 First Test Validation

**Run this to verify setup:**

```bash
# Run all tests
npm test

# Run with coverage
npm run test:coverage

# Should see:
# PASS src/ogc-api/features/url-builder.spec.ts
# PASS src/ogc-api/tiles/url-builder.spec.ts
# ... (existing tests)
```

✅ **Setup Complete** - Ready to write CSAPI tests!

---

## Part 2: Phase-by-Phase Workflows

### Phase 1: Core Structure (12-16 hours, 4 tasks)

**Goal:** Foundation types, helper utilities, stub QueryBuilder, integration with OgcApiEndpoint

**Dependencies:** None (first phase)

**When to Test:** Write tests **immediately after each subtask** (not batched)

---

#### Task 1.1: Type System (4-5 hours)

**Implementation File:** `src/ogc-api/csapi/model.ts` (~350-400 lines)

**Step-by-Step Workflow:**

**Step 1: Create model.ts with Part 1 resource types (45 min)**

```typescript
/**
 * @fileoverview CSAPI Part 1: Feature Resources type definitions
 * @specification OGC 23-001 v1.0.0
 */

import { Feature, FeatureCollection, Point, Geometry } from 'geojson';
import { Link, TimeExtent } from '../../shared/models';

/**
 * System resource (OGC 23-001 §7.2)
 */
export interface System extends Feature {
  type: 'Feature';
  id: string;
  geometry: Point | null;
  properties: {
    name: string;
    description?: string;
    systemType?: string;
    status?: string;
    validTime?: TimeExtent;
    links?: Link[];
  };
}

/**
 * Systems collection
 */
export interface SystemCollection extends FeatureCollection {
  type: 'FeatureCollection';
  features: System[];
}

// ... (Deployment, Procedure, SamplingFeature, Property interfaces)
```

**Step 2: Write type validation tests immediately (30 min)**

Create `src/ogc-api/csapi/model.spec.ts`:

```typescript
/**
 * @fileoverview Type definition tests for CSAPI model
 * @module csapi/model
 * @specification OGC 23-001 v1.0.0, OGC 23-002 v1.0.0
 */

import { System, SystemCollection } from '../model';

describe('CSAPI Type System', () => {
  describe('System Interface', () => {
    /**
     * Validates System conforms to GeoJSON Feature structure.
     * @specification OGC 23-001 §7.2, Table 4
     */
    it('conforms to GeoJSON Feature structure', () => {
      const system: System = {
        type: 'Feature',
        id: 'sys-001',
        geometry: {
          type: 'Point',
          coordinates: [-117.123, 34.567],
        },
        properties: {
          name: 'Weather Station Alpha',
          description: 'Rooftop weather monitoring station',
          systemType: 'WeatherStation',
          status: 'active',
        },
      };

      expect(system.type).toBe('Feature');
      expect(system.id).toBeDefined();
      expect(system.geometry?.type).toBe('Point');
      expect(system.properties.name).toBeDefined();
    });

    /**
     * System with null geometry is valid per spec.
     * @specification OGC 23-001 §7.2.1
     */
    it('allows null geometry for non-spatial systems', () => {
      const system: System = {
        type: 'Feature',
        id: 'sys-002',
        geometry: null,
        properties: {
          name: 'Virtual System',
        },
      };

      expect(system.geometry).toBeNull();
    });

    /**
     * Required properties must be present.
     * @specification OGC 23-001 §7.2, Table 4
     */
    it('requires name property', () => {
      const system: System = {
        type: 'Feature',
        id: 'sys-003',
        geometry: null,
        properties: {
          name: 'Minimal System',
        },
      };

      expect(system.properties.name).toBe('Minimal System');
    });
  });

  describe('SystemCollection Interface', () => {
    it('conforms to GeoJSON FeatureCollection structure', () => {
      const collection: SystemCollection = {
        type: 'FeatureCollection',
        features: [
          {
            type: 'Feature',
            id: 'sys-001',
            geometry: null,
            properties: { name: 'System 1' },
          },
        ],
      };

      expect(collection.type).toBe('FeatureCollection');
      expect(Array.isArray(collection.features)).toBe(true);
      expect(collection.features).toHaveLength(1);
    });
  });
});
```

**Step 3: Add Part 2 resource types (45 min)**

Add to `model.ts`:

```typescript
/**
 * @fileoverview CSAPI Part 2: Observation Data type definitions
 * @specification OGC 23-002 v1.0.0
 */

/**
 * DataStream resource (OGC 23-002 §8.1)
 */
export interface DataStream extends Feature {
  type: 'Feature';
  id: string;
  geometry: Point | null;
  properties: {
    name: string;
    description?: string;
    observedProperty: Link;
    phenomenonTime?: TimeExtent;
    resultTime?: TimeExtent;
    links?: Link[];
  };
}

/**
 * Observation resource (OGC 23-002 §8.2)
 */
export interface Observation {
  id?: string;
  type: 'Feature';
  phenomenonTime: string | TimeExtent;
  result: any;
  resultTime?: string;
  parameters?: Record<string, any>;
}

// ... (ControlStream, Command interfaces)
```

**Step 4: Write Part 2 type tests (30 min)**

Add to `model.spec.ts`:

```typescript
describe('DataStream Interface', () => {
  /**
   * DataStream validates observed property link.
   * @specification OGC 23-002 §8.1, Table 8
   */
  it('requires observedProperty link', () => {
    const datastream: DataStream = {
      type: 'Feature',
      id: 'ds-001',
      geometry: null,
      properties: {
        name: 'Temperature Stream',
        observedProperty: {
          href: 'http://example.com/properties/temperature',
          rel: 'observedProperty',
        },
      },
    };

    expect(datastream.properties.observedProperty).toBeDefined();
    expect(datastream.properties.observedProperty.href).toContain(
      'temperature'
    );
  });
});

describe('Observation Interface', () => {
  /**
   * Observation phenomenonTime can be instant or interval.
   * @specification OGC 23-002 §8.2.1
   */
  it('supports instant phenomenonTime', () => {
    const obs: Observation = {
      type: 'Feature',
      phenomenonTime: '2024-01-15T12:00:00Z',
      result: 23.5,
    };

    expect(typeof obs.phenomenonTime).toBe('string');
  });

  it('supports interval phenomenonTime', () => {
    const obs: Observation = {
      type: 'Feature',
      phenomenonTime: ['2024-01-15T00:00:00Z', '2024-01-15T23:59:59Z'],
      result: [20.1, 22.3, 23.5, 21.8],
    };

    expect(Array.isArray(obs.phenomenonTime)).toBe(true);
  });
});
```

**Step 5: Add query options interfaces (45 min)**

```typescript
/**
 * Base query options for all CSAPI resources
 */
export interface QueryOptions {
  bbox?: [number, number, number, number];
  datetime?: string;
  limit?: number;
  offset?: number;
}

/**
 * System-specific query options
 */
export interface SystemQueryOptions extends QueryOptions {
  systemType?: string;
  status?: string;
  parentSystem?: string;
}

/**
 * Observation-specific query options
 */
export interface ObservationQueryOptions extends QueryOptions {
  observedProperty?: string;
  resultTime?: string;
  foi?: string;
}

// ... (DataStreamQueryOptions, etc.)
```

**Step 6: Write query options tests (30 min)**

```typescript
describe('Query Options', () => {
  /**
   * SystemQueryOptions extends base QueryOptions.
   * @specification OGC 23-001 §7.2.2
   */
  it('supports system-specific filters', () => {
    const options: SystemQueryOptions = {
      limit: 10,
      systemType: 'WeatherStation',
      status: 'active',
      bbox: [-118, 34, -117, 35],
    };

    expect(options.systemType).toBe('WeatherStation');
    expect(options.limit).toBe(10);
  });
});
```

**Step 7: Run tests and validate (15 min)**

```bash
npm test -- model.spec.ts

# Should see:
# PASS src/ogc-api/csapi/model.spec.ts
#   CSAPI Type System
#     System Interface
#       ✓ conforms to GeoJSON Feature structure
#       ✓ allows null geometry for non-spatial systems
#       ✓ requires name property
#     SystemCollection Interface
#       ✓ conforms to GeoJSON FeatureCollection structure
#     DataStream Interface
#       ✓ requires observedProperty link
#     Observation Interface
#       ✓ supports instant phenomenonTime
#       ✓ supports interval phenomenonTime
#     Query Options
#       ✓ supports system-specific filters
#
# Tests: 8 passed, 8 total
```

**✅ Task 1.1 Complete** - Types defined and validated

---

#### Task 1.2: Helper Utilities (3-4 hours)

**Implementation File:** `src/ogc-api/csapi/helpers.ts` (~50-80 lines)

**Step-by-Step Workflow:**

**Step 1: Create helpers.ts with core URL builder (30 min)**

```typescript
/**
 * @fileoverview Helper utilities for CSAPI URL construction
 * @module csapi/helpers
 */

/**
 * Build resource URL with optional ID and sub-path.
 *
 * @param baseUrl - API base URL
 * @param collectionId - Collection identifier
 * @param resourceType - Resource type (systems, datastreams, etc.)
 * @param id - Optional resource ID
 * @param subPath - Optional sub-path (e.g., 'datastreams', 'observations')
 * @returns Complete resource URL
 *
 * @example
 * buildResourceUrl('https://api.com', 'col1', 'systems')
 * // => 'https://api.com/collections/col1/systems'
 *
 * @example
 * buildResourceUrl('https://api.com', 'col1', 'systems', 'sys-001')
 * // => 'https://api.com/collections/col1/systems/sys-001'
 *
 * @example
 * buildResourceUrl('https://api.com', 'col1', 'systems', 'sys-001', 'datastreams')
 * // => 'https://api.com/collections/col1/systems/sys-001/datastreams'
 */
export function buildResourceUrl(
  baseUrl: string,
  collectionId: string,
  resourceType: string,
  id?: string,
  subPath?: string
): string {
  let url = `${baseUrl}/collections/${collectionId}/${resourceType}`;

  if (id) {
    url += `/${id}`;
  }

  if (subPath) {
    url += `/${subPath}`;
  }

  return url;
}
```

**Step 2: Write helper tests immediately (30 min)**

Create `src/ogc-api/csapi/helpers.spec.ts`:

```typescript
/**
 * @fileoverview Tests for CSAPI helper utilities
 * @module csapi/helpers
 */

import { buildResourceUrl } from '../helpers';
import { parseAndValidateUrl } from './test-utils';

describe('CSAPI Helper Utilities', () => {
  describe('buildResourceUrl', () => {
    const baseUrl = 'https://example.com/api';
    const collectionId = 'weather-sensors';

    /**
     * Builds collection-level resource URL.
     */
    it('builds collection resource URL', () => {
      const url = buildResourceUrl(baseUrl, collectionId, 'systems');

      const { pathname, segments } = parseAndValidateUrl(url);

      expect(pathname).toBe('/api/collections/weather-sensors/systems');
      expect(segments).toEqual([
        'api',
        'collections',
        'weather-sensors',
        'systems',
      ]);
    });

    /**
     * Builds individual resource URL with ID.
     */
    it('builds individual resource URL with ID', () => {
      const url = buildResourceUrl(baseUrl, collectionId, 'systems', 'sys-001');

      const { segments } = parseAndValidateUrl(url);

      expect(segments).toEqual([
        'api',
        'collections',
        'weather-sensors',
        'systems',
        'sys-001',
      ]);
    });

    /**
     * Builds nested resource URL with sub-path.
     */
    it('builds nested resource URL with sub-path', () => {
      const url = buildResourceUrl(
        baseUrl,
        collectionId,
        'systems',
        'sys-001',
        'datastreams'
      );

      const { segments } = parseAndValidateUrl(url);

      expect(segments).toEqual([
        'api',
        'collections',
        'weather-sensors',
        'systems',
        'sys-001',
        'datastreams',
      ]);
    });

    /**
     * Handles URL with trailing slash correctly.
     */
    it('handles baseUrl with trailing slash', () => {
      const url = buildResourceUrl(
        'https://example.com/api/',
        collectionId,
        'systems'
      );

      expect(url).not.toContain('//collections');
      expect(url).toBe(
        'https://example.com/api/collections/weather-sensors/systems'
      );
    });
  });
});
```

**Step 3: Add query string builder (30 min)**

Add to `helpers.ts`:

```typescript
/**
 * Build query string from options object.
 *
 * @param options - Query options
 * @returns URL query string (without leading '?')
 *
 * @example
 * buildQueryString({ limit: 10, status: 'active' })
 * // => 'limit=10&status=active'
 *
 * @example
 * buildQueryString({ bbox: [-118, 34, -117, 35] })
 * // => 'bbox=-118,34,-117,35'
 */
export function buildQueryString(options?: Record<string, any>): string {
  if (!options || Object.keys(options).length === 0) {
    return '';
  }

  const params = new URLSearchParams();

  for (const [key, value] of Object.entries(options)) {
    if (value !== undefined && value !== null) {
      if (Array.isArray(value)) {
        params.append(key, value.join(','));
      } else {
        params.append(key, String(value));
      }
    }
  }

  // Normalize + to %20 for OGC API compatibility (matches upstream setQueryParams pattern)
  return params.toString().replace(/\+/g, '%20');
}
```

**Step 4: Write query string tests (30 min)**

Add to `helpers.spec.ts`:

```typescript
describe('buildQueryString', () => {
  /**
   * Builds query string from simple parameters.
   */
  it('builds query string from simple parameters', () => {
    const qs = buildQueryString({ limit: 10, offset: 20 });

    expect(qs).toBe('limit=10&offset=20');
  });

  /**
   * Encodes array parameters as comma-separated values.
   */
  it('encodes bbox as comma-separated values', () => {
    const qs = buildQueryString({ bbox: [-118, 34, -117, 35] });

    expect(qs).toBe('bbox=-118%2C34%2C-117%2C35');
  });

  /**
   * Omits undefined and null values.
   */
  it('omits undefined and null values', () => {
    const qs = buildQueryString({ limit: 10, offset: undefined, foo: null });

    expect(qs).toBe('limit=10');
  });

  /**
   * Returns empty string for empty options.
   */
  it('returns empty string for empty options', () => {
    expect(buildQueryString({})).toBe('');
    expect(buildQueryString(undefined)).toBe('');
  });

  /**
   * URL-encodes special characters.
   */
  it('encodes special characters', () => {
    const qs = buildQueryString({ name: 'Weather Station #1' });

    expect(qs).toContain('Weather%20Station%20%231');
  });
});
```

**Step 5: Add temporal parsing utilities (30 min)**

```typescript
/**
 * Parse datetime parameter to ISO 8601 format.
 *
 * @param datetime - Datetime string (instant or interval)
 * @returns Normalized datetime string
 *
 * @example
 * parseDatetime('2024-01-15')
 * // => '2024-01-15T00:00:00Z'
 *
 * @example
 * parseDatetime('2024-01-15/2024-01-16')
 * // => '2024-01-15T00:00:00Z/2024-01-16T23:59:59Z'
 */
export function parseDatetime(datetime: string): string {
  // Simple implementation - normalize to ISO 8601
  if (datetime.includes('/')) {
    const [start, end] = datetime.split('/');
    return `${normalizeDate(start)}/${normalizeDate(end)}`;
  }
  return normalizeDate(datetime);
}

function normalizeDate(date: string): string {
  if (date.includes('T')) {
    return date.endsWith('Z') ? date : `${date}Z`;
  }
  return `${date}T00:00:00Z`;
}
```

**Step 6: Write temporal parsing tests (30 min)**

```typescript
describe('parseDatetime', () => {
  it('normalizes date to ISO 8601 instant', () => {
    expect(parseDatetime('2024-01-15')).toBe('2024-01-15T00:00:00Z');
  });

  it('preserves datetime with timezone', () => {
    expect(parseDatetime('2024-01-15T12:00:00Z')).toBe('2024-01-15T12:00:00Z');
  });

  it('normalizes interval to ISO 8601', () => {
    const result = parseDatetime('2024-01-15/2024-01-16');
    expect(result).toBe('2024-01-15T00:00:00Z/2024-01-16T00:00:00Z');
  });
});
```

**Step 7: Run all helper tests (15 min)**

```bash
npm test -- helpers.spec.ts

# Should see:
# PASS src/ogc-api/csapi/helpers.spec.ts
#   CSAPI Helper Utilities
#     buildResourceUrl
#       ✓ builds collection resource URL
#       ✓ builds individual resource URL with ID
#       ✓ builds nested resource URL with sub-path
#       ✓ handles baseUrl with trailing slash
#     buildQueryString
#       ✓ builds query string from simple parameters
#       ✓ encodes bbox as comma-separated values
#       ✓ omits undefined and null values
#       ✓ returns empty string for empty options
#       ✓ encodes special characters
#     parseDatetime
#       ✓ normalizes date to ISO 8601 instant
#       ✓ preserves datetime with timezone
#       ✓ normalizes interval to ISO 8601
#
# Tests: 12 passed, 12 total
```

**✅ Task 1.2 Complete** - Helpers implemented and tested

---

#### Task 1.3: Stub QueryBuilder (2-3 hours)

**Implementation File:** `src/ogc-api/csapi/url_builder.ts` (stub, ~100-150 lines)

**Step-by-Step Workflow:**

**Step 1: Create stub QueryBuilder class (45 min)**

```typescript
/**
 * @fileoverview CSAPI QueryBuilder for URL construction
 * @module csapi/url_builder
 */

import { buildResourceUrl, buildQueryString } from './helpers';
import { SystemQueryOptions, DataStreamQueryOptions } from './model';

/**
 * Query builder for CSAPI resources.
 *
 * @example
 * const builder = new CSAPIQueryBuilder(collectionInfo, endpoint);
 * const url = builder.getSystems({ limit: 10 });
 */
export class CSAPIQueryBuilder {
  private apiUrl: string;
  private collectionId: string;
  private availableResources: Set<string>;

  constructor(collectionInfo: any, endpoint: any) {
    this.apiUrl = endpoint.apiUrl;
    this.collectionId = collectionInfo.id;
    this.availableResources = this.extractAvailableResources(collectionInfo);
  }

  /**
   * Extract available resource types from collection links.
   *
   * @param collectionInfo - Collection metadata
   * @returns Set of available resource types
   */
  private extractAvailableResources(collectionInfo: any): Set<string> {
    const resources = new Set<string>();

    if (collectionInfo.links) {
      for (const link of collectionInfo.links) {
        if (link.rel && link.rel.includes('systems')) {
          resources.add('systems');
        }
        if (link.rel && link.rel.includes('datastreams')) {
          resources.add('datastreams');
        }
        // ... (check other resource types)
      }
    }

    return resources;
  }

  /**
   * Validate resource is available in collection.
   *
   * @throws Error if resource not available
   */
  private validateResource(resourceType: string): void {
    if (!this.availableResources.has(resourceType)) {
      throw new Error(
        `Resource type "${resourceType}" not available in collection "${this.collectionId}"`
      );
    }
  }

  /**
   * Get systems collection URL.
   *
   * @param options - Query options
   * @returns Systems URL
   *
   * @example
   * builder.getSystems({ limit: 10, systemType: 'WeatherStation' })
   * // => 'https://api.com/collections/col1/systems?limit=10&systemType=WeatherStation'
   */
  getSystems(options?: SystemQueryOptions): string {
    this.validateResource('systems');

    const url = buildResourceUrl(this.apiUrl, this.collectionId, 'systems');
    const qs = buildQueryString(options);

    return qs ? `${url}?${qs}` : url;
  }

  /**
   * Get individual system URL.
   *
   * @param id - System ID
   * @returns System URL
   *
   * @example
   * builder.getSystem('sys-001')
   * // => 'https://api.com/collections/col1/systems/sys-001'
   */
  getSystem(id: string): string {
    this.validateResource('systems');

    return buildResourceUrl(this.apiUrl, this.collectionId, 'systems', id);
  }
}
```

**Step 2: Write QueryBuilder tests immediately (60 min)**

Create `src/ogc-api/csapi/url_builder.spec.ts`:

```typescript
/**
 * @fileoverview Tests for CSAPI QueryBuilder
 * @module csapi/url_builder
 */

import { CSAPIQueryBuilder } from '../url_builder';
import { parseAndValidateUrl } from './test-utils';

describe('CSAPIQueryBuilder', () => {
  const mockEndpoint = {
    apiUrl: 'https://example.com/api',
  };

  const mockCollection = {
    id: 'weather-sensors',
    links: [
      {
        rel: 'systems',
        href: 'https://example.com/api/collections/weather-sensors/systems',
      },
      {
        rel: 'datastreams',
        href: 'https://example.com/api/collections/weather-sensors/datastreams',
      },
    ],
  };

  let builder: CSAPIQueryBuilder;

  beforeEach(() => {
    builder = new CSAPIQueryBuilder(mockCollection, mockEndpoint);
  });

  describe('Constructor', () => {
    /**
     * QueryBuilder initializes with collection info.
     */
    it('initializes with collection info', () => {
      expect(builder).toBeDefined();
      expect(builder).toBeInstanceOf(CSAPIQueryBuilder);
    });

    /**
     * Extracts available resources from collection links.
     */
    it('extracts available resources from collection links', () => {
      // Access private property for testing (use type assertion)
      const resources = (builder as any).availableResources;

      expect(resources.has('systems')).toBe(true);
      expect(resources.has('datastreams')).toBe(true);
    });
  });

  describe('getSystems', () => {
    /**
     * Builds systems collection URL.
     * @specification OGC 23-001 §7.2.2
     */
    it('builds systems collection URL', () => {
      const url = builder.getSystems();

      const { pathname, segments } = parseAndValidateUrl(url);

      expect(pathname).toBe('/api/collections/weather-sensors/systems');
      expect(segments).toEqual([
        'api',
        'collections',
        'weather-sensors',
        'systems',
      ]);
    });

    /**
     * Adds query parameters.
     * @specification OGC 23-001 §7.2.2
     */
    it('adds query parameters', () => {
      const url = builder.getSystems({
        limit: 10,
        systemType: 'WeatherStation',
      });

      const { searchParams } = parseAndValidateUrl(url);

      expect(searchParams.get('limit')).toBe('10');
      expect(searchParams.get('systemType')).toBe('WeatherStation');
    });

    /**
     * Throws error if systems not available.
     */
    it('throws error if systems not available', () => {
      const emptyCollection = { id: 'empty', links: [] };
      const emptyBuilder = new CSAPIQueryBuilder(emptyCollection, mockEndpoint);

      expect(() => emptyBuilder.getSystems()).toThrow(
        'Resource type "systems" not available'
      );
    });
  });

  describe('getSystem', () => {
    /**
     * Builds individual system URL.
     * @specification OGC 23-001 §7.2.2
     */
    it('builds individual system URL', () => {
      const url = builder.getSystem('sys-001');

      const { segments } = parseAndValidateUrl(url);

      expect(segments).toEqual([
        'api',
        'collections',
        'weather-sensors',
        'systems',
        'sys-001',
      ]);
    });

    /**
     * Throws error if systems not available.
     */
    it('throws error if systems not available', () => {
      const emptyCollection = { id: 'empty', links: [] };
      const emptyBuilder = new CSAPIQueryBuilder(emptyCollection, mockEndpoint);

      expect(() => emptyBuilder.getSystem('sys-001')).toThrow(
        'Resource type "systems" not available'
      );
    });
  });
});
```

**Step 3: Run tests (15 min)**

```bash
npm test -- url_builder.spec.ts

# Should see:
# PASS src/ogc-api/csapi/url_builder.spec.ts
#   CSAPIQueryBuilder
#     Constructor
#       ✓ initializes with collection info
#       ✓ extracts available resources from collection links
#     getSystems
#       ✓ builds systems collection URL
#       ✓ adds query parameters
#       ✓ throws error if systems not available
#     getSystem
#       ✓ builds individual system URL
#       ✓ throws error if systems not available
#
# Tests: 7 passed, 7 total
```

**✅ Task 1.3 Complete** - Stub QueryBuilder working

---

#### Task 1.4: OgcApiEndpoint Integration (3-4 hours)

**Implementation Files:**

- `src/ogc-api/endpoint.ts` (+35 lines)
- `src/ogc-api/shared/info.ts` (+12 lines)
- `src/ogc-api/index.ts` (+17 lines)

**Step-by-Step Workflow:**

**Step 1: Add CSAPI detection to info.ts (30 min)**

Modify `src/ogc-api/shared/info.ts`:

```typescript
/**
 * Check if endpoint supports Connected Systems API.
 *
 * @param endpoint - OGC API endpoint
 * @returns True if Connected Systems support detected
 */
export function checkHasConnectedSystems(endpoint: OgcApiEndpoint): boolean {
  const conformance = endpoint.conformance;

  // Check for CSAPI Part 1 Core conformance
  const hasPart1 = conformance.some(
    (uri) =>
      uri.includes('connected-systems/part1/core') ||
      uri.includes('ogcapi-connectedsystems-1')
  );

  // Check for CSAPI Part 2 Dynamic Data conformance
  const hasPart2 = conformance.some(
    (uri) =>
      uri.includes('connected-systems/part2/dynamic-data') ||
      uri.includes('ogcapi-connectedsystems-2')
  );

  return hasPart1 && hasPart2;
}
```

**Step 2: Write conformance detection tests (30 min)**

Add to `src/ogc-api/info.spec.ts`:

```typescript
describe('checkHasConnectedSystems', () => {
  /**
   * Detects CSAPI support from conformance classes.
   */
  it('detects CSAPI support from conformance classes', () => {
    const endpoint = {
      conformance: [
        'http://www.opengis.net/spec/ogcapi-common-1/1.0/conf/api-common',
        'http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/api-common',
        'http://www.opengis.net/spec/ogcapi-connectedsystems-2/1.0/conf/datastream',
      ],
    };

    expect(checkHasConnectedSystems(endpoint)).toBe(true);
  });

  /**
   * Returns false if Part 1 missing.
   */
  it('returns false if Part 1 missing', () => {
    const endpoint = {
      conformance: [
        'http://www.opengis.net/spec/ogcapi-connectedsystems-2/1.0/conf/datastream',
      ],
    };

    expect(checkHasConnectedSystems(endpoint)).toBe(false);
  });

  /**
   * Returns false if Part 2 missing.
   */
  it('returns false if Part 2 missing', () => {
    const endpoint = {
      conformance: [
        'http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/api-common',
      ],
    };

    expect(checkHasConnectedSystems(endpoint)).toBe(false);
  });
});
```

**Step 3: Add OgcApiEndpoint integration (45 min)**

Modify `src/ogc-api/endpoint.ts`:

```typescript
import { CSAPIQueryBuilder } from './csapi/url_builder';

export class OgcApiEndpoint {
  // ... existing properties

  private csapiBuilderCache = new Map<string, CSAPIQueryBuilder>();

  /**
   * Get collections that support Connected Systems API.
   *
   * @returns Array of CSAPI-enabled collection IDs
   */
  get csapiCollections(): string[] {
    return this._collections
      .filter((col) => this.isCSAPICollection(col))
      .map((col) => col.id);
  }

  /**
   * Check if endpoint has Connected Systems API support.
   *
   * @returns True if CSAPI supported
   */
  get hasConnectedSystems(): boolean {
    return checkHasConnectedSystems(this);
  }

  /**
   * Get CSAPI query builder for a collection.
   *
   * @param collectionId - Collection identifier
   * @returns CSAPI query builder instance
   * @throws Error if collection doesn't support CSAPI
   *
   * @example
   * const builder = endpoint.csapi('weather-sensors');
   * const url = builder.getSystems();
   */
  csapi(collectionId: string): CSAPIQueryBuilder {
    // Check cache
    if (this.csapiBuilderCache.has(collectionId)) {
      return this.csapiBuilderCache.get(collectionId)!;
    }

    // Find collection
    const collection = this._collections.find((c) => c.id === collectionId);
    if (!collection) {
      throw new Error(`Collection "${collectionId}" not found`);
    }

    // Validate CSAPI support
    if (!this.isCSAPICollection(collection)) {
      throw new Error(
        `Collection "${collectionId}" does not support Connected Systems API`
      );
    }

    // Create and cache builder
    const builder = new CSAPIQueryBuilder(collection, this);
    this.csapiBuilderCache.set(collectionId, builder);

    return builder;
  }

  private isCSAPICollection(collection: any): boolean {
    // Check collection links for CSAPI resources
    return (
      collection.links?.some(
        (link: any) =>
          link.rel?.includes('systems') || link.rel?.includes('datastreams')
      ) ?? false
    );
  }
}
```

**Step 4: Write endpoint integration tests (60 min)**

Add to `src/ogc-api/endpoint.spec.ts`:

```typescript
describe('OgcApiEndpoint - CSAPI Integration', () => {
  describe('hasConnectedSystems', () => {
    /**
     * Detects CSAPI support from endpoint conformance.
     */
    it('detects CSAPI support from conformance', async () => {
      const endpoint = new OgcApiEndpoint('http://example.com/api', {
        conformance: [
          'http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/api-common',
          'http://www.opengis.net/spec/ogcapi-connectedsystems-2/1.0/conf/datastream',
        ],
      });

      expect(endpoint.hasConnectedSystems).toBe(true);
    });
  });

  describe('csapiCollections', () => {
    /**
     * Returns collections with CSAPI support.
     */
    it('returns collections with CSAPI support', async () => {
      const endpoint = new OgcApiEndpoint('http://example.com/api', {
        collections: [
          {
            id: 'weather-sensors',
            links: [
              {
                rel: 'systems',
                href: 'http://example.com/api/collections/weather-sensors/systems',
              },
            ],
          },
          {
            id: 'features-only',
            links: [
              {
                rel: 'items',
                href: 'http://example.com/api/collections/features-only/items',
              },
            ],
          },
        ],
      });

      expect(endpoint.csapiCollections).toEqual(['weather-sensors']);
    });
  });

  describe('csapi()', () => {
    /**
     * Returns cached QueryBuilder instance.
     */
    it('returns cached QueryBuilder instance', async () => {
      const endpoint = new OgcApiEndpoint('http://example.com/api', {
        collections: [
          {
            id: 'weather-sensors',
            links: [{ rel: 'systems', href: '...' }],
          },
        ],
      });

      const builder1 = endpoint.csapi('weather-sensors');
      const builder2 = endpoint.csapi('weather-sensors');

      expect(builder1).toBe(builder2); // Same instance
    });

    /**
     * Throws error for non-existent collection.
     */
    it('throws error for non-existent collection', async () => {
      const endpoint = new OgcApiEndpoint('http://example.com/api', {});

      expect(() => endpoint.csapi('nonexistent')).toThrow(
        'Collection "nonexistent" not found'
      );
    });

    /**
     * Throws error for non-CSAPI collection.
     */
    it('throws error for non-CSAPI collection', async () => {
      const endpoint = new OgcApiEndpoint('http://example.com/api', {
        collections: [
          {
            id: 'features-only',
            links: [{ rel: 'items', href: '...' }],
          },
        ],
      });

      expect(() => endpoint.csapi('features-only')).toThrow(
        'does not support Connected Systems API'
      );
    });
  });
});
```

**Step 5: Export from index.ts (15 min)**

Modify `src/ogc-api/index.ts`:

```typescript
// Export CSAPI types
export {
  System,
  SystemCollection,
  DataStream,
  Observation,
  QueryOptions,
  SystemQueryOptions,
  DataStreamQueryOptions,
} from './csapi/model';

// Export CSAPI QueryBuilder
export { CSAPIQueryBuilder } from './csapi/url_builder';

// Export CSAPI helpers
export {
  buildResourceUrl,
  buildQueryString,
  parseDatetime,
} from './csapi/helpers';
```

**Step 6: Run all Phase 1 tests (15 min)**

```bash
npm test -- csapi

# Should see:
# PASS src/ogc-api/csapi/model.spec.ts
# PASS src/ogc-api/csapi/helpers.spec.ts
# PASS src/ogc-api/csapi/url_builder.spec.ts
# PASS src/ogc-api/endpoint.spec.ts (CSAPI tests)
# PASS src/ogc-api/info.spec.ts (CSAPI tests)
#
# Tests: 35 passed, 35 total
# Coverage: Statement 90%, Branch 85%, Function 88%
```

**✅ Phase 1 Complete!** - Foundation ready for QueryBuilder expansion

---

### Phase 2: QueryBuilder (20-28 hours, 9 tasks)

**Goal:** Complete URL building for all 70-80 CSAPI methods across 9 resource types

**Dependencies:** Phase 1 complete (types, helpers, stub QueryBuilder)

**When to Test:** Write tests for each resource type immediately after implementing methods

**Pattern:** Each task follows same workflow:

1. Add methods to QueryBuilder (45-60 min per resource type)
2. Write tests immediately (60-90 min per resource type)
3. Run tests and validate (15 min)
4. Move to next resource type

---

#### Task 2.1: Systems Methods (2-3 hours)

**Add to url_builder.ts (~150-200 lines):**

```typescript
/**
 * Get system's datastreams.
 *
 * @param systemId - System ID
 * @param options - Query options
 * @returns DataStreams URL
 *
 * @specification OGC 23-001 §7.2.3
 *
 * @example
 * builder.getSystemDataStreams('sys-001', { limit: 10 })
 * // => 'https://api.com/collections/col1/systems/sys-001/datastreams?limit=10'
 */
getSystemDataStreams(systemId: string, options?: DataStreamQueryOptions): string {
  this.validateResource('systems');

  const url = buildResourceUrl(
    this.apiUrl,
    this.collectionId,
    'systems',
    systemId,
    'datastreams'
  );

  const qs = buildQueryString(options);
  return qs ? `${url}?${qs}` : url;
}

/**
 * Get system's subsystems.
 *
 * @param systemId - System ID
 * @param options - Query options
 * @returns Subsystems URL
 *
 * @specification OGC 23-001 §7.2.4
 */
getSystemSubsystems(systemId: string, options?: SystemQueryOptions): string {
  this.validateResource('systems');

  const url = buildResourceUrl(
    this.apiUrl,
    this.collectionId,
    'systems',
    systemId,
    'subsystems'
  );

  const qs = buildQueryString(options);
  return qs ? `${url}?${qs}` : url;
}

/**
 * Get system's sampling features.
 *
 * @param systemId - System ID
 * @param options - Query options
 * @returns SamplingFeatures URL
 *
 * @specification OGC 23-001 §7.2.5
 */
getSystemSamplingFeatures(systemId: string, options?: QueryOptions): string {
  this.validateResource('systems');

  const url = buildResourceUrl(
    this.apiUrl,
    this.collectionId,
    'systems',
    systemId,
    'samplingFeatures'
  );

  const qs = buildQueryString(options);
  return qs ? `${url}?${qs}` : url;
}

// ... (8-10 more system methods)
```

**Write tests immediately (~150-200 lines):**

```typescript
describe('System Methods', () => {
  describe('getSystemDataStreams', () => {
    /**
     * Builds system datastreams URL.
     * @specification OGC 23-001 §7.2.3
     */
    it('builds system datastreams URL', () => {
      const url = builder.getSystemDataStreams('sys-001');

      const { segments } = parseAndValidateUrl(url);

      expect(segments).toEqual([
        'api',
        'collections',
        'weather-sensors',
        'systems',
        'sys-001',
        'datastreams',
      ]);
    });

    it('adds query parameters', () => {
      const url = builder.getSystemDataStreams('sys-001', { limit: 10 });

      const { searchParams } = parseAndValidateUrl(url);

      expect(searchParams.get('limit')).toBe('10');
    });
  });

  describe('getSystemSubsystems', () => {
    it('builds system subsystems URL', () => {
      const url = builder.getSystemSubsystems('sys-001');

      const { segments } = parseAndValidateUrl(url);

      expect(segments[segments.length - 1]).toBe('subsystems');
    });
  });

  // ... (tests for all 8-10 system methods)
});
```

**✅ Task 2.1 Complete** when all system methods tested

---

#### Task 2.2-2.9: Remaining Resource Types

> **Note:** For complete method lists per resource type (including all CRUD, navigation, and temporal methods), see [ROADMAP v3.0 Phase 2 tasks](../../../planning/ROADMAP.md).

**Follow same pattern for:**

- Task 2.2: DataStreams Methods (2-3 hours, ~10 methods)
- Task 2.3: Observations Methods (3-4 hours, ~12 methods - most complex)
- Task 2.4: Deployments Methods (2-3 hours, ~8 methods)
- Task 2.5: Procedures Methods (2-3 hours, ~8 methods)
- Task 2.6: SamplingFeatures Methods (2-3 hours, ~8 methods)
- Task 2.7: Properties Methods (2-3 hours, ~8 methods)
- Task 2.8: ControlStreams Methods (2-3 hours, ~8 methods)
- Task 2.9: Commands Methods (2-3 hours, ~8 methods)

**Each task:**

1. Implement methods (~45-60 min)
2. Write tests (~60-90 min)
3. Run tests (~15 min)

**At end of Phase 2:**

```bash
npm test -- url_builder.spec.ts

# Should see:
# PASS src/ogc-api/csapi/url_builder.spec.ts
#   CSAPIQueryBuilder
#     Constructor (2 tests)
#     System Methods (24 tests)
#     DataStream Methods (22 tests)
#     Observation Methods (28 tests)
#     Deployment Methods (18 tests)
#     Procedure Methods (18 tests)
#     SamplingFeature Methods (18 tests)
#     Property Methods (18 tests)
#     ControlStream Methods (18 tests)
#     Command Methods (18 tests)
#
# Tests: 184 passed, 184 total
# Time: 8.5s
# Coverage: Statement >80%, Branch >80% (ROADMAP minimum)
```

**✅ Phase 2 Complete!** - All 70-80 QueryBuilder methods implemented and tested

---

### Phase 3: Format Handling (16-28 hours, 17 tasks per ROADMAP v3.0)

> **Note:** This playbook groups Phase 3 into simplified subtask ranges (3.1-3.5, 3.6-3.10, 3.11-3.15) for readability. ROADMAP v3.0 defines **17 granular tasks** with explicit dependency ordering. Refer to [ROADMAP v3.0 Phase 3](../../../planning/ROADMAP.md) for the authoritative task list and dependencies.

**Goal:** SensorML/SWE parsers + GeoJSON/Format Detector/Validator extensions

**Dependencies:** Phase 1-2 complete. **Critical:** SWE Common types must be completed before SensorML types (dependency).

**Incremental Testing:** Write tests immediately after each subtask (not batched)

**Pattern:** Create parser → Write parse tests → Add type inference → Write type tests → Add validation → Write validation tests

---

#### Subtask 3.1-3.5: SWE Common Parser (6-10 hours)

**Workflow:**

**Subtask 3.1: DataRecord Parser (2-3 hours)**

1. Create `src/ogc-api/csapi/parsers/swe-common-parser.ts` (30 min)
2. Implement `parseDataRecord()` (45 min)
3. **Write tests immediately** (60 min): `swe-common-parser.spec.ts`
4. Run tests (15 min)

**Subtask 3.2: DataArray Parser (2-3 hours)**

1. Add `parseDataArray()` to parser (45 min)
2. **Write tests immediately** (60 min)
3. Run tests (15 min)

**Subtask 3.3-3.5:** Vector, Matrix, Choice parsers - same pattern

**Example Test Pattern:**

```typescript
describe('SWE Common Parser', () => {
  describe('parseDataRecord', () => {
    /**
     * Parses simple DataRecord structure.
     * @specification OGC 08-094r1 §7.1
     * @fixture swe-common/datarecord-simple.json
     */
    it('parses simple DataRecord', () => {
      const fixture = loadFixture('swe-common/datarecord-simple.json');

      const result = parseDataRecord(fixture);

      expect(result.type).toBe('DataRecord');
      expect(result.fields).toHaveLength(3);
      expect(result.fields[0].name).toBe('temperature');
    });

    /**
     * Parses nested DataRecord (1-2 levels).
     * @specification OGC 08-094r1 §7.1.2
     * @fixture swe-common/datarecord-nested.json
     */
    it('parses nested DataRecord', () => {
      const fixture = loadFixture('swe-common/datarecord-nested.json');

      const result = parseDataRecord(fixture);

      expect(result.fields[0].type).toBe('DataRecord');
      expect(result.fields[0].fields).toHaveLength(2);
    });
  });
});
```

**✅ Subtasks 3.1-3.5 Complete** when all SWE Common parsers tested

---

#### Subtask 3.6-3.10: SensorML Parser (6-10 hours)

**Same incremental pattern:**

- Subtask 3.6: SimpleProcess (2-3 hours)
- Subtask 3.7: PhysicalSystem (2-3 hours)
- Subtask 3.8: PhysicalComponent (2-3 hours)
- Subtask 3.9: Capabilities/Characteristics (1-2 hours)
- Subtask 3.10: Position/Location (1-2 hours)

**Each subtask:** Implement → Test immediately → Validate

---

#### Subtask 3.11-3.15: Extensions (4-8 hours)

- Subtask 3.11: GeoJSON extensions (1-2 hours)
- Subtask 3.12: Format detector updates (1-2 hours)
- Subtask 3.13: Validator extensions (1-2 hours)
- Subtask 3.14: Integration tests (1-2 hours)
- Subtask 3.15: Documentation (1-2 hours)

**At end of Phase 3:**

```bash
npm test -- parsers

# Should see:
# PASS src/ogc-api/csapi/parsers/swe-common-parser.spec.ts
#   SWE Common Parser
#     parseDataRecord (8 tests)
#     parseDataArray (6 tests)
#     parseVector (4 tests)
#     parseMatrix (4 tests)
#     parseChoice (4 tests)
#
# PASS src/ogc-api/csapi/parsers/sensorml-parser.spec.ts
#   SensorML Parser
#     parseSimpleProcess (6 tests)
#     parsePhysicalSystem (8 tests)
#     parsePhysicalComponent (6 tests)
#     parseCapabilities (4 tests)
#     parsePosition (4 tests)
#
# Tests: 54 passed, 54 total
# Coverage: Statement 88%, Branch 82%, Function 86%
```

**✅ Phase 3 Complete!** - All parsers implemented and tested incrementally

---

### Phase 4: Worker & Tests (12-16 hours, 4 tasks)

**Goal:** Worker extensions, integration tests, documentation

---

#### Task 4.1: Worker Extensions (4-5 hours)

**Implementation:** `src/worker/index.ts` modifications

**Step-by-Step:**

1. Add CSAPI message types (30 min)
2. Add parser message handlers (60 min)
3. **Write worker tests immediately** (90 min)
4. Run tests (15 min)

**Worker Test Pattern:**

```typescript
describe('Worker - CSAPI Support', () => {
  /**
   * Worker handles SWE Common parsing.
   */
  it('handles SWE Common parsing', async () => {
    const message = {
      type: 'PARSE_SWE_COMMON',
      data: sweCommonFixture,
    };

    const result = await worker.handleMessage(message);

    expect(result.type).toBe('PARSE_SUCCESS');
    expect(result.data.type).toBe('DataRecord');
  });

  /**
   * Worker handles SensorML parsing.
   */
  it('handles SensorML parsing', async () => {
    const message = {
      type: 'PARSE_SENSORML',
      data: sensorMLFixture,
    };

    const result = await worker.handleMessage(message);

    expect(result.type).toBe('PARSE_SUCCESS');
    expect(result.data.type).toBe('PhysicalSystem');
  });
});
```

**✅ Task 4.1 Complete** when worker tests passing

---

#### Task 4.2: Integration Tests (4-5 hours)

**Create:** `src/ogc-api/csapi/integration/`

**Integration Test Pattern:**

```typescript
/**
 * @fileoverview Integration tests for CSAPI workflows
 * @module csapi/integration/discovery
 *
 * NOTE: "Integration tests" in this project = multi-component workflow tests
 * through the public API with mocked HTTP responses (per Section 14). The
 * term "end-to-end" is reserved for tests using real servers (out of scope).
 * See Section 7 and Section 14 for the full terminology discussion.
 */

describe('CSAPI Integration - Discovery Workflow', () => {
  /**
   * Complete discovery workflow: endpoint → collection → systems → datastreams → observations.
   *
   * @specification OGC 23-001 (all parts)
   * @fixture csapi/collections/collection-weather-sensors.json
   * @fixture csapi/systems/system-weather-station-001.json
   * @fixture csapi/datastreams/datastream-temperature.json
   * @fixture csapi/observations/observations-temperature-timeseries.json
   */
  it('discovers and queries complete system hierarchy', async () => {
    // Step 1: Load endpoint with CSAPI collections
    const endpoint = new OgcApiEndpoint(
      'https://example.com/api',
      loadFixture('collections/collection-weather-sensors.json')
    );

    expect(endpoint.hasConnectedSystems).toBe(true);
    expect(endpoint.csapiCollections).toContain('weather-sensors');

    // Step 2: Get CSAPI query builder
    const builder = endpoint.csapi('weather-sensors');

    // Step 3: Query systems
    const systemsUrl = builder.getSystems({ limit: 10 });
    expect(systemsUrl).toContain('/systems?limit=10');

    // Step 4: Get specific system
    const systemUrl = builder.getSystem('sys-weather-001');
    expect(systemUrl).toContain('/systems/sys-weather-001');

    // Step 5: Get system's datastreams
    const datastreamsUrl = builder.getSystemDataStreams('sys-weather-001');
    expect(datastreamsUrl).toContain('/systems/sys-weather-001/datastreams');

    // Step 6: Get datastream observations
    const obsUrl = builder.getDataStreamObservations('ds-temp-001', {
      datetime: '2024-01-15/2024-01-16',
    });
    expect(obsUrl).toContain('/datastreams/ds-temp-001/observations');
    expect(obsUrl).toContain('datetime=2024-01-15');
  });

  /**
   * Observation query workflow with temporal filtering.
   *
   * @specification OGC 23-002 §8.2
   */
  it('queries observations with temporal filters', async () => {
    const endpoint = new OgcApiEndpoint(
      'https://example.com/api',
      loadFixture('collections/collection-weather-sensors.json')
    );

    const builder = endpoint.csapi('weather-sensors');

    // Query observations for specific time period
    const url = builder.getObservations({
      datetime: '2024-01-15T00:00:00Z/2024-01-15T23:59:59Z',
      observedProperty: 'temperature',
      limit: 100,
    });

    const { searchParams } = parseAndValidateUrl(url);

    expect(searchParams.get('datetime')).toContain('2024-01-15');
    expect(searchParams.get('observedProperty')).toBe('temperature');
    expect(searchParams.get('limit')).toBe('100');
  });
});
```

**Create 8-10 integration tests covering:**

- Discovery workflow
- Observation query workflow
- Command execution workflow
- Nested resource navigation
- Error handling
- Format parsing integration

**✅ Task 4.2 Complete** when 8-10 integration tests passing

---

#### Task 4.3: Documentation (2-3 hours)

**Create:**

- `docs/CSAPI.md` - User guide
- `docs/API.md` - API reference (update)
- README updates
- JSDoc completion review

**✅ Task 4.3 Complete** when documentation reviewed

---

#### Task 4.4: Final Validation (2-3 hours)

**Checklist:**

```bash
# Run full test suite
npm test

# Check coverage
npm run test:coverage

# Should see:
# Tests: 320+ passed, 0 failed
# Statement coverage: 90%+
# Branch coverage: 85%+
# Function coverage: 88%+
```

**Manual validation:**

- All ROADMAP tasks checked off
- All research section recommendations implemented
- Quality checklist passed
- No TODOs or FIXMEs remaining
- Documentation complete

**✅ Phase 4 Complete!** - CSAPI implementation fully tested and documented

---

## Part 3: Component Testing Patterns

### 3.1 QueryBuilder Testing Pattern

**Pattern:** URL validation + parameter encoding + resource availability

**Standard Test Structure** (follows the universal template from [Section 13 §3.1](13-resource-method-testing-patterns.md) — see Doc 13 for the full resource method testing template):

```typescript
describe('[ResourceType] Methods', () => {
  describe('get[ResourceType]s', () => {
    it('builds collection URL', () => {
      const url = builder.get[ResourceType]s();
      const { pathname, segments } = parseAndValidateUrl(url);
      expect(segments).toEqual([...expected]);
    });

    it('adds query parameters', () => {
      const url = builder.get[ResourceType]s({ limit: 10, filter: 'value' });
      const { searchParams } = parseAndValidateUrl(url);
      expect(searchParams.get('limit')).toBe('10');
      expect(searchParams.get('filter')).toBe('value');
    });

    it('handles bbox parameter', () => {
      const url = builder.get[ResourceType]s({ bbox: [-118, 34, -117, 35] });
      const { searchParams } = parseAndValidateUrl(url);
      expect(searchParams.get('bbox')).toBe('-118,34,-117,35');
    });

    it('throws error if resource not available', () => {
      const emptyBuilder = new CSAPIQueryBuilder({ id: 'empty', links: [] }, mockEndpoint);
      expect(() => emptyBuilder.get[ResourceType]s()).toThrow('not available');
    });
  });

  describe('get[ResourceType]', () => {
    it('builds individual resource URL', () => {
      const url = builder.get[ResourceType]('id-001');
      const { segments } = parseAndValidateUrl(url);
      expect(segments[segments.length - 1]).toBe('id-001');
    });
  });

  describe('get[ResourceType][SubResource]s', () => {
    it('builds nested resource URL', () => {
      const url = builder.get[ResourceType][SubResource]s('parent-id');
      const { segments } = parseAndValidateUrl(url);
      expect(segments).toContain('parent-id');
      expect(segments[segments.length - 1]).toBe('subresources');
    });
  });
});
```

**Key Points:**

- ✅ Use `parseAndValidateUrl()` in every test
- ✅ Test collection URL (no params)
- ✅ Test with query parameters
- ✅ Test bbox encoding
- ✅ Test datetime encoding
- ✅ Test resource availability validation
- ✅ Test nested resources
- ✅ Add @specification tags

### 3.2 Parser Testing Pattern

**Pattern:** Structure validation + type inference + nested parsing + error handling

**Standard Test Structure:**

```typescript
describe('[ParserName] Parser', () => {
  describe('parse[Type]', () => {
    /**
     * @specification [spec] §[section]
     * @fixture [fixture-path]
     */
    it('parses simple [type]', () => {
      const fixture = loadFixture('[fixture-path]');
      const result = parse[Type](fixture);

      expect(result.type).toBe('[ExpectedType]');
      expect(result.fields).toHaveLength(expectedCount);
      expect(result.fields[0].name).toBe('expectedName');
    });

    it('parses nested [type] (1-2 levels)', () => {
      const fixture = loadFixture('[nested-fixture]');
      const result = parse[Type](fixture);

      expect(result.fields[0].type).toBe('[NestedType]');
      expect(result.fields[0].fields).toHaveLength(expectedCount);
    });

    it('infers TypeScript types from [type]', () => {
      const fixture = loadFixture('[fixture-path]');
      const result = parse[Type](fixture);

      expect(result.fields[0].typeInfo.tsType).toBe('number');
      expect(result.fields[1].typeInfo.tsType).toBe('string');
    });

    it('handles missing optional fields', () => {
      const minimal = { ...minimalFixture };
      const result = parse[Type](minimal);

      expect(result).toBeDefined();
      expect(result.optionalField).toBeUndefined();
    });

    it('throws error for invalid [type]', () => {
      const invalid = { invalid: 'structure' };
      expect(() => parse[Type](invalid)).toThrow('[ExpectedError]');
    });
  });
});
```

**Key Points:**

- ✅ Test simple structures
- ✅ Test nested structures (1-2 levels minimum)
- ✅ Test type inference
- ✅ Test optional fields
- ✅ Test error cases
- ✅ Use real fixtures from spec
- ✅ Add @fixture tags

### 3.3 Integration Testing Pattern

**Pattern:** End-to-end workflow + fixture-driven + multi-step validation

**Standard Test Structure:**

```typescript
describe('Integration - [Workflow Name]', () => {
  /**
   * Complete [workflow] workflow: step1 → step2 → step3 → step4.
   *
   * @specification [specs involved]
   * @fixture [fixture1]
   * @fixture [fixture2]
   * @coverage Complete end-to-end [workflow] flow
   */
  it('completes [workflow] workflow', async () => {
    // Step 1: Setup - Load endpoint
    const endpoint = new OgcApiEndpoint(
      'https://example.com/api',
      loadFixture('[collection-fixture]')
    );

    // Step 2: Validate - Check capabilities
    expect(endpoint.hasConnectedSystems).toBe(true);
    expect(endpoint.csapiCollections).toContain('collection-id');

    // Step 3: Execute - Get query builder
    const builder = endpoint.csapi('collection-id');

    // Step 4: Query - Build URLs for resources
    const step1Url = builder.get[Resource1]s();
    expect(step1Url).toContain('/resource1s');

    const step2Url = builder.get[Resource1][SubResource]s('id-001');
    expect(step2Url).toContain('/resource1s/id-001/subresources');

    // Step 5: Parse - Process response formats
    const parsed = parse[Format](loadFixture('[format-fixture]'));
    expect(parsed.type).toBe('[ExpectedType]');

    // Step 6: Validate - Complete workflow success
    expect(parsed.fields).toHaveLength(expectedCount);
  });
});
```

**Key Points:**

- ✅ Test complete workflows (3+ operations)
- ✅ Use realistic fixtures
- ✅ Validate each step
- ✅ Test error paths
- ✅ Document workflow in JSDoc
- ✅ Add @coverage tags

### 3.4 Test Utilities Pattern

**Pattern:** Pure functions + comprehensive edge cases + performance validation

**Standard Test Structure:**

```typescript
describe('[UtilityName] Utility', () => {
  describe('[functionName]', () => {
    it('handles typical case', () => {
      const result = functionName(typicalInput);
      expect(result).toEqual(expectedOutput);
    });

    it('handles empty input', () => {
      const result = functionName('');
      expect(result).toBe(expectedDefault);
    });

    it('handles null/undefined', () => {
      expect(functionName(null)).toBe(expectedDefault);
      expect(functionName(undefined)).toBe(expectedDefault);
    });

    it('handles edge case: [description]', () => {
      const result = functionName(edgeCaseInput);
      expect(result).toEqual(expectedEdgeOutput);
    });

    it('throws error for invalid input', () => {
      expect(() => functionName(invalidInput)).toThrow('[ExpectedError]');
    });
  });
});
```

> **⚠️ PERFORMANCE TESTING IS NOT IN SCOPE ⚠️**
>
> The original pattern included a performance timing test (`performance.now()` with `expect(duration).toBeLessThan(100)`). Per Doc 33 and project-wide decision, **performance testing will NOT be implemented**. Upstream `ogc-client` has ZERO performance tests. Do not add performance assertions to test utilities.

**Key Points:**

- ✅ Test typical case
- ✅ Test empty input
- ✅ Test null/undefined
- ✅ Test edge cases
- ✅ Test error cases
- ✅ Test performance (if relevant)
- ✅ 100% function coverage required

### 3.5 Worker Testing Pattern

**Pattern:** Message handling + async operations + error propagation

**Standard Test Structure:**

```typescript
describe('Worker - [Feature]', () => {
  it('handles [message type] message', async () => {
    const message = {
      type: '[MESSAGE_TYPE]',
      data: testData,
    };

    const result = await worker.handleMessage(message);

    expect(result.type).toBe('SUCCESS');
    expect(result.data).toEqual(expectedData);
  });

  it('handles async operations', async () => {
    const message = {
      type: 'ASYNC_OPERATION',
      data: testData,
    };

    const promise = worker.handleMessage(message);

    expect(promise).toBeInstanceOf(Promise);

    const result = await promise;

    expect(result.type).toBe('SUCCESS');
  });

  it('propagates errors correctly', async () => {
    const message = {
      type: '[MESSAGE_TYPE]',
      data: invalidData,
    };

    const result = await worker.handleMessage(message);

    expect(result.type).toBe('ERROR');
    expect(result.error).toBeDefined();
    expect(result.error.message).toContain('expected error');
  });
});
```

**Key Points:**

- ✅ Test message handling
- ✅ Test async operations
- ✅ Test error propagation
- ✅ Test message types
- ✅ Mock minimal dependencies

---

## Part 4: Practical Examples

### Example 1: First QueryBuilder Test

**Scenario:** Writing first test for getSystems() method

**Step 1: Create test file**

```typescript
/**
 * @fileoverview Tests for CSAPI QueryBuilder
 * @module csapi/url_builder
 */

import { CSAPIQueryBuilder } from '../url_builder';
import { parseAndValidateUrl } from './test-utils';

describe('CSAPIQueryBuilder', () => {
  // Setup mock data
  const mockEndpoint = {
    apiUrl: 'https://example.com/api',
  };

  const mockCollection = {
    id: 'weather-sensors',
    links: [
      {
        rel: 'systems',
        href: 'https://example.com/api/collections/weather-sensors/systems',
      },
    ],
  };

  let builder: CSAPIQueryBuilder;

  beforeEach(() => {
    builder = new CSAPIQueryBuilder(mockCollection, mockEndpoint);
  });

  describe('getSystems', () => {
    /**
     * Builds systems collection URL.
     * @specification OGC 23-001 §7.2.2
     */
    it('builds systems collection URL', () => {
      // ACT: Call the method
      const url = builder.getSystems();

      // ASSERT: Validate URL structure using parseAndValidateUrl
      const { pathname, segments } = parseAndValidateUrl(url);

      expect(pathname).toBe('/api/collections/weather-sensors/systems');
      expect(segments).toEqual([
        'api',
        'collections',
        'weather-sensors',
        'systems',
      ]);
    });
  });
});
```

**Step 2: Run test**

```bash
npm test -- url_builder.spec.ts

# Output:
# PASS src/ogc-api/csapi/url_builder.spec.ts
#   CSAPIQueryBuilder
#     getSystems
#       ✓ builds systems collection URL (5 ms)
```

**✅ Success!** First test passing

---

### Example 2: First Parser Test

**Scenario:** Writing first test for SWE Common DataRecord parser

**Step 1: Create fixture**

Create `fixtures/swe-common/json/datarecord-simple.json`:

```json
{
  "type": "DataRecord",
  "definition": "http://example.com/definitions/weather-obs",
  "label": "Weather Observation",
  "field": [
    {
      "name": "temperature",
      "type": "Quantity",
      "definition": "http://qudt.org/vocab/quantitykind/Temperature",
      "uom": {
        "code": "Cel"
      }
    },
    {
      "name": "humidity",
      "type": "Quantity",
      "definition": "http://qudt.org/vocab/quantitykind/RelativeHumidity",
      "uom": {
        "code": "%"
      }
    }
  ],
  "_comment": "Fixture metadata is NOT embedded per Doc 15 Part 2 findings — use descriptive filenames + git history instead"
}
```

**Step 2: Create parser**

Create `src/ogc-api/csapi/parsers/swe-common-parser.ts`:

```typescript
/**
 * Parse SWE Common DataRecord.
 *
 * @param data - DataRecord JSON
 * @returns Parsed DataRecord structure
 */
export function parseDataRecord(data: any): any {
  return {
    type: data.type,
    definition: data.definition,
    label: data.label,
    fields: data.field.map((f: any) => ({
      name: f.name,
      type: f.type,
      definition: f.definition,
      uom: f.uom,
    })),
  };
}
```

**Step 3: Create test**

Create `src/ogc-api/csapi/parsers/swe-common-parser.spec.ts`:

```typescript
/**
 * @fileoverview Tests for SWE Common parser
 * @module csapi/parsers/swe-common-parser
 */

import { parseDataRecord } from '../../parsers/swe-common-parser';
import { loadFixture } from '../test-utils';

describe('SWE Common Parser', () => {
  describe('parseDataRecord', () => {
    /**
     * Parses simple DataRecord structure.
     * @specification OGC 08-094r1 §7.1
     * @fixture swe-common/datarecord-simple.json
     */
    it('parses simple DataRecord', () => {
      // ARRANGE: Load fixture
      const fixture = loadFixture('swe-common/datarecord-simple.json');

      // ACT: Parse fixture
      const result = parseDataRecord(fixture);

      // ASSERT: Validate structure
      expect(result.type).toBe('DataRecord');
      expect(result.label).toBe('Weather Observation');
      expect(result.fields).toHaveLength(2);
      expect(result.fields[0].name).toBe('temperature');
      expect(result.fields[0].uom.code).toBe('Cel');
      expect(result.fields[1].name).toBe('humidity');
      expect(result.fields[1].uom.code).toBe('%');
    });
  });
});
```

**Step 4: Run test**

```bash
npm test -- swe-common-parser.spec.ts

# Output:
# PASS src/ogc-api/csapi/parsers/swe-common-parser.spec.ts
#   SWE Common Parser
#     parseDataRecord
#       ✓ parses simple DataRecord (12 ms)
```

**✅ Success!** First parser test passing

---

### Example 3: First Integration Test

**Scenario:** Testing complete discovery workflow

**Step 1: Create collection fixture**

`fixtures/csapi/sample-server/collections/collection-weather-sensors.json`:

```json
{
  "id": "weather-sensors",
  "title": "Weather Sensor Network",
  "links": [
    {
      "rel": "systems",
      "href": "https://example.com/api/collections/weather-sensors/systems"
    },
    {
      "rel": "datastreams",
      "href": "https://example.com/api/collections/weather-sensors/datastreams"
    }
  ],
  "conformance": [
    "http://www.opengis.net/spec/ogcapi-connectedsystems-1/1.0/conf/api-common",
    "http://www.opengis.net/spec/ogcapi-connectedsystems-2/1.0/conf/datastream"
  ]
}
```

**Step 2: Create integration test**

`src/ogc-api/csapi/integration/discovery.spec.ts`:

```typescript
/**
 * @fileoverview Integration tests for CSAPI discovery workflow
 * @module csapi/integration/discovery
 */

import { OgcApiEndpoint } from '../../../endpoint';
import { loadFixture } from '../test-utils';

describe('CSAPI Integration - Discovery Workflow', () => {
  /**
   * Complete discovery workflow: endpoint → collection → systems → datastreams.
   *
   * @specification OGC 23-001 (Part 1), OGC 23-002 (Part 2)
   * @fixture collections/collection-weather-sensors.json
   * @coverage Discovery and navigation workflow
   */
  it('discovers CSAPI capabilities and navigates resources', async () => {
    // STEP 1: Load endpoint with CSAPI collection
    const collectionFixture = loadFixture(
      'collections/collection-weather-sensors.json'
    );

    const endpoint = new OgcApiEndpoint('https://example.com/api', {
      conformance: collectionFixture.conformance,
      collections: [collectionFixture],
    });

    // STEP 2: Validate CSAPI detection
    expect(endpoint.hasConnectedSystems).toBe(true);
    expect(endpoint.csapiCollections).toEqual(['weather-sensors']);

    // STEP 3: Get CSAPI query builder
    const builder = endpoint.csapi('weather-sensors');

    expect(builder).toBeDefined();
    expect(builder).toBeInstanceOf(CSAPIQueryBuilder);

    // STEP 4: Build systems URL
    const systemsUrl = builder.getSystems({ limit: 10 });

    expect(systemsUrl).toContain('/collections/weather-sensors/systems');
    expect(systemsUrl).toContain('limit=10');

    // STEP 5: Build datastreams URL
    const datastreamsUrl = builder.getDataStreams();

    expect(datastreamsUrl).toContain(
      '/collections/weather-sensors/datastreams'
    );

    // STEP 6: Build nested URL (system → datastreams)
    const systemDatastreamsUrl = builder.getSystemDataStreams('sys-001');

    expect(systemDatastreamsUrl).toContain('/systems/sys-001/datastreams');
  });
});
```

**Step 3: Run test**

```bash
npm test -- integration/discovery.spec.ts

# Output:
# PASS src/ogc-api/csapi/integration/discovery.spec.ts
#   CSAPI Integration - Discovery Workflow
#     ✓ discovers CSAPI capabilities and navigates resources (45 ms)
```

**✅ Success!** First integration test passing

---

## Part 5: Test Quality Validation

### 5.1 Using the Quality Checklist

**Before committing any tests, validate against Section 36 checklist:**

> **Note:** This is a condensed 27-item version of Section 36's full 41-item checklist, optimized for quick pre-commit self-review. Section 36 also provides a simplified 10-item self-review checklist for rapid checks — use that for day-to-day commits and this 27-item version for thorough validation of new test files. See [Section 36: Test Quality Checklist and Review Process](36-test-quality-checklist-review-process.md) for the complete checklist and review process details. Also reference [Section 18: Error Condition Testing Strategy](18-error-condition-testing-strategy.md) for systematic error testing approaches (network errors, validation errors, HTTP status codes, timeout handling).

**Pre-Commit Checklist:**

```markdown
## Test Quality Self-Review

### Meaningful Tests (5 items)

- [ ] Tests validate real behavior (not mocks)
- [ ] Tests use `parseAndValidateUrl()` for URL validation
- [ ] Tests check URL structure (segments, parameters)
- [ ] Tests validate error conditions
- [ ] Tests have clear purpose documented in JSDoc

### Useful Tests (4 items)

- [ ] Tests would catch real bugs
- [ ] Validated by intentionally breaking code
- [ ] Tests fail when implementation is wrong
- [ ] Tests cover edge cases

### Deep Coverage (6 items)

- [ ] Statement coverage >85%
- [ ] Branch coverage >80%
- [ ] All public methods tested
- [ ] Error paths tested
- [ ] Edge cases tested (empty, null, invalid)
- [ ] Nested structures tested (if applicable)

### End-to-End Workflows (4 items)

- [ ] Integration tests cover 3+ operations
- [ ] Tests use real fixtures from spec
- [ ] Tests validate complete workflows
- [ ] Tests demonstrate value to users

### Documentation (4 items)

- [ ] @specification tags present
- [ ] @fixture tags present (if using fixtures)
- [ ] JSDoc describes test purpose
- [ ] Complex logic explained

### Code Quality (4 items)

- [ ] No trivial assertions (toBeTruthy, toBeDefined alone)
- [ ] Clear test names
- [ ] Proper arrange/act/assert structure
- [ ] No duplicate tests
```

**Validation Process:**

```bash
# 1. Run tests
npm test -- [your-test-file]

# 2. Check coverage
npm run test:coverage

# 3. Review coverage report
# Open coverage/lcov-report/index.html

# 4. Identify gaps
# - Lines not covered (red)
# - Branches not covered (yellow)

# 5. Add missing tests

# 6. Re-run validation
npm test -- [your-test-file]
npm run test:coverage

# 7. Verify checklist complete
```

### 5.2 Common Quality Issues and Fixes

**Issue 1: Trivial Test**

❌ **BAD:**

```typescript
it('returns URL', () => {
  const url = builder.getSystems();
  expect(url).toBeTruthy();
});
```

✅ **GOOD:**

```typescript
it('builds systems collection URL with correct structure', () => {
  const url = builder.getSystems();
  const { pathname, segments } = parseAndValidateUrl(url);

  expect(pathname).toBe('/api/collections/weather-sensors/systems');
  expect(segments).toEqual([
    'api',
    'collections',
    'weather-sensors',
    'systems',
  ]);
});
```

**Issue 2: Testing Mocks Instead of Behavior**

❌ **BAD:**

```typescript
it('calls parser', () => {
  const mockParser = jest.fn().mockReturnValue({ type: 'DataRecord' });
  const result = processData(data, mockParser);

  expect(mockParser).toHaveBeenCalled();
  expect(result.type).toBe('DataRecord');
});
```

✅ **GOOD:**

```typescript
it('parses DataRecord and extracts fields', () => {
  const fixture = loadFixture('swe-common/datarecord-simple.json');
  const result = parseDataRecord(fixture);

  expect(result.type).toBe('DataRecord');
  expect(result.fields).toHaveLength(2);
  expect(result.fields[0].name).toBe('temperature');
});
```

**Issue 3: Missing Edge Cases**

❌ **BAD:**

```typescript
it('builds query string', () => {
  const qs = buildQueryString({ limit: 10 });
  expect(qs).toBe('limit=10');
});
```

✅ **GOOD:**

```typescript
describe('buildQueryString', () => {
  it('builds query string from parameters', () => {
    const qs = buildQueryString({ limit: 10, offset: 20 });
    expect(qs).toBe('limit=10&offset=20');
  });

  it('handles empty options', () => {
    expect(buildQueryString({})).toBe('');
    expect(buildQueryString(undefined)).toBe('');
  });

  it('omits null and undefined values', () => {
    const qs = buildQueryString({ limit: 10, offset: null, foo: undefined });
    expect(qs).toBe('limit=10');
  });

  it('encodes array parameters', () => {
    const qs = buildQueryString({ bbox: [-118, 34, -117, 35] });
    expect(qs).toContain('bbox=-118%2C34%2C-117%2C35');
  });
});
```

**Issue 4: Missing @specification Tags**

❌ **BAD:**

```typescript
it('gets systems', () => {
  const url = builder.getSystems();
  expect(url).toContain('/systems');
});
```

✅ **GOOD:**

```typescript
/**
 * Builds systems collection URL per spec.
 * @specification OGC 23-001 §7.2.2
 */
it('builds systems collection URL', () => {
  const url = builder.getSystems();
  const { pathname } = parseAndValidateUrl(url);
  expect(pathname).toBe('/api/collections/weather-sensors/systems');
});
```

### 5.3 Bug Detection Validation

**Critical:** Always validate tests catch bugs by intentionally breaking code

**Process:**

1. Write test
2. Verify test passes
3. **Break implementation intentionally**
4. Verify test fails
5. Fix implementation
6. Verify test passes again

**Example:**

```typescript
// Test
it('validates system ID parameter is required', () => {
  expect(() => builder.getSystem('')).toThrow('System ID is required');
});

// Break implementation (comment out validation)
getSystem(id: string): string {
  // if (!id) throw new Error('System ID is required'); // COMMENTED OUT
  return buildResourceUrl(this.apiUrl, this.collectionId, 'systems', id);
}

// Run test - should FAIL
npm test -- url_builder.spec.ts
// ❌ Expected test to throw error, but didn't

// Fix implementation (uncomment validation)
getSystem(id: string): string {
  if (!id) throw new Error('System ID is required'); // RESTORED
  return buildResourceUrl(this.apiUrl, this.collectionId, 'systems', id);
}

// Run test - should PASS
npm test -- url_builder.spec.ts
// ✅ Test catches bug correctly
```

---

## Part 6: Tools and Commands

### 6.1 Daily Commands

**Run all tests:**

```bash
npm test
```

**Run specific test file:**

```bash
npm test -- url_builder.spec.ts
```

**Run tests matching pattern:**

```bash
npm test -- --testNamePattern="getSystems"
```

**Run tests for specific folder:**

```bash
npm test -- csapi/
```

**Watch mode (re-run on file changes):**

```bash
npm test -- --watch
```

**Run tests with coverage:**

```bash
npm run test:coverage
```

**View coverage report:**

```bash
# Open in browser
start coverage/lcov-report/index.html  # Windows
open coverage/lcov-report/index.html   # Mac
```

### 6.2 Debugging Commands

**Debug specific test:**

```bash
node --inspect-brk node_modules/.bin/jest --runInBand url_builder.spec.ts
```

**Run single test:**

```bash
npm test -- url_builder.spec.ts --testNamePattern="builds systems collection URL"
```

**Verbose output:**

```bash
npm test -- --verbose
```

**Show test timing:**

```bash
npm test -- --verbose --testTimeout=10000
```

### 6.3 Coverage Commands

**Check coverage thresholds:**

```bash
npm run test:coverage

# Should see:
# =============================== Coverage summary ===============================
# Statements   : 90.12% ( 1234/1369 )
# Branches     : 85.67% ( 456/532 )
# Functions    : 88.45% ( 89/100 )
# Lines        : 90.12% ( 1234/1369 )
# ================================================================================
```

**Generate coverage for specific files:**

```bash
npm test -- --coverage --collectCoverageFrom="src/ogc-api/csapi/**/*.ts"
```

**Coverage by file:**

```bash
npm test -- --coverage --verbose
```

### 6.4 Performance Commands

> **⚠️ PERFORMANCE TESTING IS NOT IN SCOPE ⚠️**
>
> Per Doc 33, performance testing will NOT be implemented. Upstream `ogc-client` has ZERO performance tests. The commands below are retained for reference only — do not implement performance test infrastructure.

**Profile test execution:**

```bash
npm test -- --logHeapUsage
```

**Check slow tests:**

```bash
npm test -- --verbose | grep "ms)" | sort -rn
```

### 6.5 Fixture Commands

**Validate all fixtures:**

```bash
npm run fixtures:validate
```

**Validate specific fixtures:**

```bash
npm run fixtures:validate -- --resource systems
```

---

## Part 7: Progress Tracking

### 7.1 Component Completion Criteria

**QueryBuilder Component:**

- [ ] All resource types implemented (9 types)
- [ ] All methods tested (70-80 methods)
- [ ] All URL patterns validated
- [ ] All parameter encodings tested
- [ ] Resource availability validation tested
- [ ] Integration with OgcApiEndpoint tested
- [ ] Coverage: Statement >80%, Branch >80% (ROADMAP minimum)

**Parser Component:**

- [ ] All SWE Common types implemented (5 types)
- [ ] All SensorML types implemented (5 types)
- [ ] All parsing functions tested
- [ ] Nested structures tested (1-2 levels)
- [ ] Type inference tested
- [ ] Error handling tested
- [ ] Coverage: Statement >80%, Branch >80% (ROADMAP minimum)

**Integration Component:**

- [ ] 8-10 integration tests written
- [ ] Discovery workflow tested
- [ ] Observation query workflow tested
- [ ] Command execution workflow tested
- [ ] Error handling tested
- [ ] Fixtures validated
- [ ] Coverage: Statement >80%, Branch >80% (ROADMAP minimum)

### 7.2 Phase Completion Checklist

> **Note:** The Phase 1 entries below show `[x]` checkmarks as **examples of what completed entries look like** — Phase 1 has NOT been implemented yet. Use `[ ]` unchecked boxes when tracking actual progress.

**Phase 1: Core Structure** _(example of completed format)_

- [ ] Task 1.1: Type System ✅

  - [x] model.ts created (~350-400 lines)
  - [x] model.spec.ts created (~200-300 lines)
  - [x] All tests passing
  - [x] Coverage >80% (ROADMAP minimum)

- [ ] Task 1.2: Helper Utilities ✅

  - [x] helpers.ts created (~50-80 lines)
  - [x] helpers.spec.ts created (~150-200 lines)
  - [x] All tests passing
  - [x] Coverage >80% (ROADMAP minimum)

- [ ] Task 1.3: Stub QueryBuilder ✅

  - [x] url_builder.ts created (~100-150 lines)
  - [x] url_builder.spec.ts created (~100-150 lines)
  - [x] All tests passing
  - [x] Coverage >80% (ROADMAP minimum)

- [ ] Task 1.4: OgcApiEndpoint Integration ✅
  - [x] endpoint.ts modified (+35 lines)
  - [x] info.ts modified (+12 lines)
  - [x] index.ts modified (+17 lines)
  - [x] Integration tests added
  - [x] All tests passing

**Phase 2: QueryBuilder**

- [ ] 9 resource types completed

  - [ ] Systems (12 methods, 24 tests)
  - [ ] DataStreams (10 methods, 22 tests)
  - [ ] Observations (14 methods, 28 tests)
  - [ ] Deployments (9 methods, 18 tests)
  - [ ] Procedures (9 methods, 18 tests)
  - [ ] SamplingFeatures (9 methods, 18 tests)
  - [ ] Properties (9 methods, 18 tests)
  - [ ] ControlStreams (9 methods, 18 tests)
  - [ ] Commands (9 methods, 18 tests)

- [ ] Coverage targets met
  - [ ] Statement >80% (ROADMAP minimum)
  - [ ] Branch >80% (ROADMAP minimum)

**Phase 3: Format Handling** _(17 tasks per ROADMAP v3.0)_

- [ ] SWE Common Parser (5 subtasks)
- [ ] SensorML Parser (5 subtasks)
- [ ] Extensions (5 subtasks) + 2 additional tasks (see ROADMAP v3.0)
- [ ] Coverage: Statement >80%, Branch >80% (ROADMAP minimum)

**Phase 4: Worker & Tests**

- [ ] Worker extensions complete
- [ ] Integration tests complete (8-10 tests)
- [ ] Documentation complete
- [ ] Final validation complete

### 7.3 Coverage Targets

**By Component:**

> **Note:** ROADMAP v3.0 specifies **>80% statement and branch coverage** as the minimum requirement. The targets below are stretch goals — meeting the ROADMAP minimum is sufficient for completion.

| Component    | Minimum (ROADMAP)          | Stretch Goal             |
| ------------ | -------------------------- | ------------------------ |
| QueryBuilder | >80% stmt, >80% branch     | 92% stmt, 88% branch     |
| Parsers      | >80% stmt, >80% branch     | 88% stmt, 82% branch     |
| Integration  | >80% stmt, >80% branch     | 90% stmt, 85% branch     |
| Utilities    | >80% stmt, >80% branch     | 95% stmt, 90% branch     |
| **Overall**  | **>80% stmt, >80% branch** | **90% stmt, 85% branch** |

**Measuring Progress:**

```bash
# Check current coverage
npm run test:coverage

# Compare to targets
# If below targets, identify gaps:
open coverage/lcov-report/index.html

# Focus on:
# 1. Red lines (not covered)
# 2. Yellow branches (partially covered)
# 3. Missing function tests
```

### 7.4 Progress Dashboard

**Track progress in:** `docs/test-progress.md`

```markdown
# CSAPI Testing Progress

**Last Updated:** [date]

## Overall Progress

- **Total Tests:** 320 / 330 target (97%)
- **Coverage:** 89.2% / 90% target
- **Phases Complete:** 3 / 4

## Phase Status

### ✅ Phase 1: Core Structure (COMPLETE)

- Duration: 14 hours actual / 12-16 estimated
- Tests: 35 passing
- Coverage: 91%

### ✅ Phase 2: QueryBuilder (COMPLETE)

- Duration: 24 hours actual / 20-28 estimated
- Tests: 184 passing
- Coverage: 92%

### ✅ Phase 3: Format Handling (COMPLETE)

- Duration: 22 hours actual / 16-28 estimated
- Tests: 54 passing
- Coverage: 88%

### 🔄 Phase 4: Worker & Tests (IN PROGRESS)

- Duration: 8 hours / 12-16 estimated
- Tests: 47 / 57 target
- Coverage: 86%

## Next Steps

1. Complete worker integration tests (2 hours)
2. Add 10 integration tests (3 hours)
3. Final documentation (2 hours)
4. Validation and review (2 hours)
```

---

## Part 8: Troubleshooting

### 8.1 Common Test Failures

**Failure: "URL validation failed - segments mismatch"**

```
Expected: ['api', 'collections', 'weather-sensors', 'systems']
Received: ['api', 'collections', 'weather-sensors', 'systems', '']
```

**Cause:** Trailing slash in URL
**Fix:**

```typescript
// Remove trailing slash from baseUrl
const url = baseUrl.replace(/\/$/, '');
```

---

**Failure: "Resource type 'systems' not available"**

**Cause:** Collection links don't include systems resource
**Fix:**

```typescript
// Check collection fixture has correct links
const mockCollection = {
  id: 'weather-sensors',
  links: [
    { rel: 'systems', href: '...' }, // ← Add this
  ],
};
```

---

**Failure: "Fixture not found"**

```
Error: Cannot find module '../../../../fixtures/csapi/systems/system-001.json'
```

**Cause:** Fixture file missing or incorrect path
**Fix:**

```bash
# Check fixture exists
ls fixtures/csapi/sample-server/systems/

# Create fixture if missing
# Verify path in loadFixture() call
```

---

### 8.2 Debugging Strategies

**Strategy 1: Isolate the Problem**

```bash
# Run only failing test
npm test -- url_builder.spec.ts --testNamePattern="builds systems URL"

# Add console.log to understand what's happening
console.log('URL:', url);
console.log('Parsed:', parseAndValidateUrl(url));
```

**Strategy 2: Check Fixtures**

```typescript
// Log fixture content
const fixture = loadFixture('systems/system-001.json');
console.log('Fixture:', JSON.stringify(fixture, null, 2));
```

**Strategy 3: Validate Mocks**

```typescript
// Ensure mocks match real data structure
const mockCollection = {
  id: 'test',
  links: [{ rel: 'systems', href: 'http://example.com/systems' }],
};
console.log('Mock:', mockCollection);
```

### 8.3 Performance Issues

> **⚠️ PERFORMANCE TESTING IS NOT IN SCOPE ⚠️**
>
> Per Doc 33, performance testing will NOT be implemented. The troubleshooting guidance below is retained for reference only if performance symptoms arise during functional testing, but do not add dedicated performance tests or assertions.

**Issue: Tests running slowly (>10 seconds)**

**Cause:** Loading too many fixtures or inefficient tests
**Fix:**

```typescript
// Cache fixtures
const fixtures = {
  system: loadFixture('systems/system-001.json'),
};

// Use beforeAll instead of beforeEach
beforeAll(() => {
  // One-time setup
});
```

**Issue: Memory leaks in tests**

**Cause:** Not cleaning up after tests
**Fix:**

```typescript
afterEach(() => {
  // Clear caches
  builder.clearCache();
  jest.clearAllMocks();
});
```

### 8.4 Where to Get Help

**Documentation:**

- Section 1: EDR Test Blueprint (patterns)
- Section 12: QueryBuilder Testing (URL validation)
- Section 34: Test Utilities (helper functions)
- Section 35: JSDoc Standards (documentation)
- Section 36: Quality Checklist (validation)

**Code Examples:**

- `src/ogc-api/features/` (upstream patterns)
- `src/ogc-api/edr/` (EDR implementation)
- `src/ogc-api/csapi/` (CSAPI tests)

**Team Resources:**

- Tech lead: Architecture questions
- Component maintainer: Component-specific questions
- Documentation maintainer: Documentation questions

**External Resources:**

- Jest documentation: https://jestjs.io/docs/getting-started
- TypeScript testing: https://www.typescriptlang.org/docs/handbook/testing.html
- CSAPI spec: https://docs.ogc.org/is/23-001/23-001.html

---

## Part 9: Reference

### 9.1 Test Utilities API

**parseAndValidateUrl(url: string)**

Parses URL and validates structure. Returns pathname, searchParams, segments.

```typescript
const { pathname, searchParams, segments } = parseAndValidateUrl(url);
```

**loadFixture(path: string)**

Loads fixture from `fixtures/csapi/` directory.

```typescript
const fixture = loadFixture('systems/system-001.json');
```

**createMockEndpoint(collectionInfo: any)**

Creates mock OgcApiEndpoint for testing.

```typescript
const endpoint = createMockEndpoint({ id: 'col1', links: [] });
```

### 9.2 JSDoc Templates

**Test File Header:**

```typescript
/**
 * @fileoverview Tests for [component name]
 * @module csapi/[path]
 * @specification OGC [spec] v[version]
 */
```

**Test Case:**

```typescript
/**
 * [Test description].
 *
 * @specification OGC [spec] §[section]
 * @fixture [fixture-path] (if using fixture)
 * @coverage [coverage area]
 */
it('[test name]', () => {
  // Test implementation
});
```

### 9.3 Quality Checklist (Quick Reference)

**Minimum Requirements:**

- ✅ Tests validate behavior (not mocks)
- ✅ URL tests use parseAndValidateUrl()
- ✅ Tests catch bugs (validated by breaking code)
- ✅ Coverage: Statement >85%, Branch >80%
- ✅ @specification tags present
- ✅ No trivial assertions alone

### 9.4 Specification Links

- **OGC 23-001:** https://docs.ogc.org/is/23-001/23-001.html
- **OGC 23-002:** https://docs.ogc.org/is/23-002/23-002.html
- **OGC 23-003:** https://docs.ogc.org/DRAFTS/23-003.html
- **SWE Common:** http://www.opengis.net/doc/IS/SWE/2.0
- **SensorML:** http://www.opengis.net/doc/IS/SensorML/2.0

---

## Part 10: Maintenance

### 10.1 Test Update Workflow

**When spec updates:**

1. Review spec changelog
2. Find affected tests using @specification tags:
   ```bash
   grep -r "@specification OGC 23-001 §7.2" src/
   ```
3. Update tests to match new spec
4. Update fixtures if needed
5. Run tests and validate

**When code refactors:**

1. Run tests (should still pass if refactoring internal only)
2. If tests fail, update test expectations
3. Validate tests still catch bugs
4. Update JSDoc if behavior changed

**When fixtures update:**

1. Validate fixtures:
   ```bash
   npm run fixtures:validate
   ```
2. Update fixture metadata (spec version, modified date)
3. Re-run tests using those fixtures
4. Update fixture inventory documentation

### 10.2 Regression Testing

> **Reference:** See [Section 20: Regression Testing Strategy](20-regression-testing-strategy.md) for comprehensive regression prevention approaches.

**Before adding CSAPI code:**

1. Run full existing test suite (`npm test`) — all existing tests must pass
2. After adding CSAPI code, run full suite again — no existing tests should break
3. If existing tests fail, the CSAPI addition has introduced a regression — fix before proceeding

**Key principle:** CSAPI is an _addition_ to the library. Existing Features, Tiles, EDR, WFS, WMS, WMTS functionality must remain fully passing at all times.

### 10.3 Adding New Tests

**Checklist:**

- [ ] Test file created in correct location
- [ ] Test follows component pattern (Part 3)
- [ ] Fixtures created if needed
- [ ] @specification tags added
- [ ] Tests use parseAndValidateUrl() for URLs
- [ ] Quality checklist validated (Part 5)
- [ ] Tests run and pass
- [ ] Coverage targets met

### 10.4 Test Health Monitoring

**Monthly health check:**

```bash
# Run full suite
npm test

# Check coverage
npm run test:coverage

# Detect test rot
npm run test:detect-rot

# Validate fixtures
npm run fixtures:validate
```

**Review:**

- All tests passing?
- Coverage maintained?
- No test rot detected?
- Fixtures valid?

**For complete maintenance strategy, see Section 37.**

---

## Summary

**This playbook provides:**

✅ **Phase-by-phase workflows** for ROADMAP implementation  
✅ **Component testing patterns** for QueryBuilder, Parsers, Integration, Utilities, Worker  
✅ **Practical examples** demonstrating each pattern  
✅ **Quality validation** using Section 36 checklist  
✅ **Tools and commands** for daily development  
✅ **Progress tracking** mechanisms and completion criteria  
✅ **Troubleshooting** guides and debugging strategies  
✅ **Quick reference** for specifications, utilities, templates  
✅ **Maintenance** workflows for ongoing test health

**How to use:**

1. Start with Phase 1 (Part 2)
2. Follow step-by-step workflows
3. Reference component patterns (Part 3) as needed
4. Use examples (Part 4) as templates
5. Validate quality (Part 5) before committing
6. Track progress (Part 7) throughout
7. Troubleshoot (Part 8) when stuck
8. Maintain (Part 10) long-term

**Next Steps:**

- Begin Phase 1, Task 1.1 (Type System)
- Create first test file
- Follow step-by-step workflow
- Validate with quality checklist
- Move to next task

**Testing Principles:**

- **Meaningful:** Validate real behavior, not mocks
- **Useful:** Catch real bugs (validated by breaking code)
- **Deep:** Comprehensive coverage (>80% statement, >80% branch per ROADMAP)
- **End-to-End:** Complete workflows (3+ operations)

**For detailed research, reference Sections 1-37.**

---

**Playbook Version:** 1.0  
**Last Updated:** February 6, 2026  
**Status:** ✅ Ready for Phase 1 Implementation
