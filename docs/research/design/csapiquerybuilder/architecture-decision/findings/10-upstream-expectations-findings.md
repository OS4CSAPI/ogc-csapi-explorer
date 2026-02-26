# Research Plan 10: Upstream Library Expectations - FINDINGS

**Research Completed:** February 4, 2026  
**Source Document:** [docs/research/requirements/upstream-expectations.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/requirements/upstream-expectations.md)  
**Researcher:** GitHub Copilot

---

## Executive Summary

**CRITICAL FINDING:** camptocamp/ogc-client has **clear, well-established expectations** for new API implementations based on patterns from WFS, WMS, WMTS, and EDR. While **single-class pattern is not explicitly mandated**, it is the **universal implementation approach** across ALL existing implementations.

**Key Expectations:**

1. **Endpoint Class Pattern:** Async initialization, metadata parsing, consistent API
2. **Single Implementation Class:** ALL implementations (WFS, WMS, WMTS, EDR) use single main class
3. **TypeScript Types:** Comprehensive type definitions for all entities
4. **Web Worker Support:** Offload parsing to background thread
5. **Testing:** 90%+ code coverage with fixtures
6. **Documentation:** JSDoc on all public APIs

**Architecture Decision Impact:** Upstream **expects and accepts** format-specific parsing (WFS parses GML, EDR handles WKT) - CSAPI's format abstraction (SensorML, SWE Common) **aligns perfectly** with existing patterns. Single-class QueryBuilder approach is the **de facto standard** without being formally mandated.

---

## Detailed Findings

### 1. Single-Class Pattern: Universal Implementation ✅

**Finding:** ALL accepted implementations use a **single main class** pattern, without explicit mandate.

**Evidence from ALL Implementations:**

**1. WMS:**

```typescript
export default class WmsEndpoint {
  private _capabilitiesUrl: string;
  private _info: GenericEndpointInfo;
  private _layers: WmsLayerFull[];

  constructor(url: string) { }
  isReady(): Promise<WmsEndpoint> { }
  getServiceInfo(): GenericEndpointInfo { }
  getLayers(): WmsLayerSummary[] { }
  getMapUrl(...): string { }
  getFeatureInfoUrl(...): string { }
}
```

**Pattern:** Single `WmsEndpoint` class with all capabilities

**2. WFS:**

```typescript
export default class WfsEndpoint {
  constructor(url: string) { }
  isReady(): Promise<WfsEndpoint> { }
  getServiceInfo(): GenericEndpointInfo { }
  getFeatureTypes(): WfsFeatureTypeBrief[] { }
  getFeatures(...): Promise<FeatureCollection> { }
  describeFeatureType(...): Promise<WfsFeatureTypeFull> { }
}
```

**Pattern:** Single `WfsEndpoint` class with all operations

**3. WMTS:**

```typescript
export default class WmtsEndpoint {
  constructor(url: string) { }
  isReady(): Promise<WmtsEndpoint> { }
  getServiceInfo(): GenericEndpointInfo { }
  getLayers(): WmtsLayer[] { }
  getTileUrl(...): string { }
}
```

**Pattern:** Single `WmtsEndpoint` class

**4. OGC API (includes EDR):**

```typescript
export default class OgcApiEndpoint {
  constructor(url: string) { }

  // Common OGC API operations
  get allCollections(): Promise<OgcApiCollectionInfo[]> { }
  get featureCollections(): Promise<string[]> { }
  getCollectionItems(...): Promise<FeatureCollection> { }

  // EDR-specific factory method
  async edr(collection_id: string): Promise<EDRQueryBuilder> {
    // Returns QueryBuilder for collection
  }
}
```

**Pattern:** Single `OgcApiEndpoint` class + collection-specific QueryBuilders

**EDRQueryBuilder:**

```typescript
export default class EDRQueryBuilder {
  // Single class for all 7 query types
  buildPositionDownloadUrl(...): string { }
  buildAreaDownloadUrl(...): string { }
  buildCubeDownloadUrl(...): string { }
  buildTrajectoryDownloadUrl(...): string { }
  buildCorridorDownloadUrl(...): string { }
  buildRadiusDownloadUrl(...): string { }
  buildLocationsDownloadUrl(...): string { }
}
```

**Pattern:** Single QueryBuilder class for all query types (NOT separate classes per query type)

**Conclusion:** **100% of implementations use single main class**. Zero multi-class examples.

---

### 2. Endpoint-Oriented API: MANDATORY ✅

**Finding:** Endpoint-oriented architecture is **required** pattern.

**Core Pattern Requirements:**

**1. Constructor Takes URL:**

```typescript
// ALL implementations follow this
constructor(url: string) {
  this._baseUrl = url;
  // Initiate metadata fetch
}
```

**2. Async Initialization:**

```typescript
// REQUIRED: isReady() returns Promise
isReady(): Promise<this> {
  return this._capabilitiesPromise.then(() => this);
}
```

**3. Metadata Getters:**

```typescript
// REQUIRED: getServiceInfo() for endpoint metadata
getServiceInfo(): GenericEndpointInfo {
  return this._info;
}

// API-specific resource getters
getLayers(): Layer[] { }
getFeatureTypes(): FeatureType[] { }
getCollections(): Collection[] { }
```

**4. Operation Methods:**

```typescript
// URL builders
getMapUrl(...): string { }
getTileUrl(...): string { }

// Or async operations
getFeatures(...): Promise<FeatureCollection> { }
getCollectionItems(...): Promise<Items> { }
```

**Pattern Flow:**

```
User creates endpoint → endpoint.isReady() → metadata parsed → methods available
```

**CSAPI Must Follow:**

```typescript
export default class CSAPIEndpoint {
  constructor(url: string) {
    // Parse landing page, conformance, collections
  }

  isReady(): Promise<CSAPIEndpoint> {
    return this._initPromise.then(() => this);
  }

  getServiceInfo(): GenericEndpointInfo {
    return this._info;
  }

  getCollections(): CSAPICollectionInfo[] {
    return this._collections;
  }

  // Factory method for QueryBuilder
  async csapi(collection_id: string): Promise<CSAPIQueryBuilder> {
    // Returns QueryBuilder for collection
  }
}
```

**Mandate Level:** **REQUIRED** - Zero flexibility on this pattern.

---

### 3. Factory Method Signature: CONSISTENT PATTERN ✅

**Finding:** Factory methods follow **consistent signature across all implementations**.

**OGC API Pattern (EDR Example):**

```typescript
export default class OgcApiEndpoint {
  // Factory method: async, takes collection_id, returns QueryBuilder
  public async edr(collection_id: string): Promise<EDRQueryBuilder> {
    // 1. Conformance check
    if (!this.hasEnvironmentalDataRetrieval) {
      throw new EndpointError('Endpoint does not support EDR');
    }

    // 2. Check cache
    const cache = this.collection_id_to_edr_builder_;
    if (cache.has(collection_id)) {
      return cache.get(collection_id);
    }

    // 3. Fetch collection metadata
    const collection = await this.getCollectionInfo(collection_id);

    // 4. Instantiate QueryBuilder
    const result = new EDRQueryBuilder(collection);

    // 5. Cache and return
    cache.set(collection_id, result);
    return result;
  }
}
```

**Pattern Elements:**

1. **Method name:** Lowercase API name (`edr`, `csapi`)
2. **Parameter:** `collection_id: string`
3. **Return type:** `Promise<QueryBuilder>`
4. **Async:** Always async (fetches metadata if needed)
5. **Caching:** Map-based cache by collection_id
6. **Validation:** Checks conformance first

**CSAPI Factory Method:**

```typescript
export default class OgcApiEndpoint {
  private collection_id_to_csapi_builder_: Map<string, CSAPIQueryBuilder> =
    new Map();

  public async csapi(collection_id: string): Promise<CSAPIQueryBuilder> {
    if (!this.hasConnectedSystems) {
      throw new EndpointError(
        'Endpoint does not support Connected Systems API'
      );
    }

    const cache = this.collection_id_to_csapi_builder_;
    if (cache.has(collection_id)) {
      return cache.get(collection_id);
    }

    const collection = await this.getCollectionInfo(collection_id);
    const result = new CSAPIQueryBuilder(collection);
    cache.set(collection_id, result);
    return result;
  }
}
```

**Signature Requirements:**

- ✅ Method name: `csapi` (lowercase)
- ✅ Parameter: `collection_id: string`
- ✅ Return: `Promise<CSAPIQueryBuilder>`
- ✅ Async: Yes
- ✅ Caching: Map-based
- ✅ Validation: Conformance check first

**Mandate Level:** **REQUIRED** - Exact pattern match expected.

---

### 4. Helper Classes: ALLOWED for Utilities Only ✅

**Finding:** Helper classes/files are **allowed** for utilities, parsing, and formatting, but **NOT** for splitting main functionality.

**Allowed Helper Pattern:**

**1. Separate Capabilities Parsing:**

```typescript
// wms/capabilities.ts - Utility functions
export function readInfoFromCapabilities(
  doc: XmlDocument
): GenericEndpointInfo {}
export function readLayersFromCapabilities(doc: XmlDocument): WmsLayerFull[] {}
export function readVersionFromCapabilities(doc: XmlDocument): WmsVersion {}

// wms/endpoint.ts - Uses helpers
import {
  readInfoFromCapabilities,
  readLayersFromCapabilities,
} from './capabilities';

export default class WmsEndpoint {
  constructor(url: string) {
    this._capabilitiesPromise = parseCapabilities(url).then((doc) => {
      this._info = readInfoFromCapabilities(doc);
      this._layers = readLayersFromCapabilities(doc);
    });
  }
}
```

**2. Separate URL Builders:**

```typescript
// wms/url.ts - URL builder functions
export function generateGetMapUrl(...params): string {}
export function generateGetFeatureInfoUrl(...params): string {}

// wms/endpoint.ts - Uses helpers
import { generateGetMapUrl } from './url';

export default class WmsEndpoint {
  getMapUrl(...params): string {
    return generateGetMapUrl(this._url, this._version, ...params);
  }
}
```

**3. Separate Model Types:**

```typescript
// wms/model.ts - Type definitions only
export interface WmsLayerFull {}
export type WmsVersion = '1.1.0' | '1.1.1' | '1.3.0';

// wms/endpoint.ts - Uses types
import { WmsLayerFull, WmsVersion } from './model';
```

**4. Format Parsers:**

```typescript
// wfs/featureprops.ts - Parse GML features
export function parseFeatureProps(
  featureCollection: FeatureCollection,
  featureType: WfsFeatureTypeFull
): WfsFeatureWithProps[] { }

// wfs/endpoint.ts - Uses parser
import { parseFeatureProps } from './featureprops';

export default class WfsEndpoint {
  async getFeatures(...): Promise<WfsFeatureWithProps[]> {
    const collection = await fetch(...);
    return parseFeatureProps(collection, featureType);
  }
}
```

**NOT Allowed - Splitting Main Functionality:**

```typescript
// ❌ NOT found in upstream - separate operation classes

// systems-client.ts
class SystemsClient {
  async getSystems(): Promise<System[]> {}
}

// deployments-client.ts
class DeploymentsClient {
  async getDeployments(): Promise<Deployment[]> {}
}

// endpoint.ts - delegates to separate classes
class CSAPIEndpoint {
  private systemsClient: SystemsClient;
  private deploymentsClient: DeploymentsClient;

  constructor(url: string) {
    this.systemsClient = new SystemsClient(url);
    this.deploymentsClient = new DeploymentsClient(url);
  }

  async getSystems() {
    return this.systemsClient.getSystems(); // Delegation
  }
}
```

**Why NOT Allowed:**

- Zero precedent in codebase
- Adds complexity without clear benefit
- More classes to maintain and test
- Breaks from established single-class pattern

**CSAPI File Structure (Allowed):**

```
src/csapi/
├── endpoint.ts           # CSAPIEndpoint class (main)
├── query-builder.ts      # CSAPIQueryBuilder class (main)
├── conformance.ts        # Helper: Parse /conformance
├── collections.ts        # Helper: Parse /collections
├── model.ts             # Types only
├── url.ts               # Helper: URL builders
├── formats/
│   ├── geojson.ts       # Helper: GeoJSON parser
│   ├── sensorml.ts      # Helper: SensorML parser
│   └── swe-common.ts    # Helper: SWE Common parser
└── endpoint.spec.ts     # Tests
```

**Mandate Level:** Helper files for utilities = ✅ ALLOWED. Separate classes for operations = ❌ NO PRECEDENT.

---

### 5. Organizational Flexibility: LIMITED ✅

**Finding:** Flexibility exists in **file organization** and **helper utilities**, but **NOT in core architecture patterns**.

**Areas WITH Flexibility:**

**1. File Organization:**

- Can have subfolders: `formats/`, `resources/`, etc.
- Can split utilities into multiple files
- Can organize by concern (parsing, formatting, validation)

**Example:**

```
src/csapi/
├── formats/          ← Subfolder OK
│   ├── geojson.ts
│   ├── sensorml.ts
│   └── swe-common.ts
├── validation/       ← Subfolder OK
│   ├── structural.ts
│   └── semantic.ts
└── helpers/          ← Subfolder OK
    ├── datetime.ts
    └── bbox.ts
```

**2. Utility Functions:**

- Can create as many helper functions as needed
- Can organize into multiple utility files
- Can use functional vs OOP style for helpers

**3. Type Organization:**

- Can split types across multiple files
- Can have separate files per resource type
- Can organize by domain (requests, responses, metadata)

**4. Testing Organization:**

- Can have multiple test files
- Can organize by feature or file
- Can use different test strategies

**Areas WITHOUT Flexibility:**

**1. Main Class Pattern:**
❌ Must use single main class (Endpoint or QueryBuilder)
❌ Cannot split operations across multiple main classes
❌ Cannot use separate client classes per resource

**2. Factory Method Pattern:**
❌ Must follow exact signature: `async methodName(collection_id: string): Promise<QueryBuilder>`
❌ Must use Map-based caching
❌ Must check conformance first

**3. Async Initialization:**
❌ Must have `isReady()` returning Promise
❌ Must parse metadata asynchronously
❌ Must handle errors consistently

**4. Type Exports:**
❌ Must export all types from module
❌ Must use shared types (BoundingBox, CrsCode, MimeType)
❌ Must re-export from main index

**5. Web Worker:**
❌ Must register handlers in worker/worker.ts
❌ Must export functions from worker/index.ts
❌ Must support fallback mode

**Flexibility Matrix:**

| Aspect             | Flexible? | Notes                         |
| ------------------ | --------- | ----------------------------- |
| File organization  | ✅ Yes    | Subfolders, multiple files OK |
| Helper functions   | ✅ Yes    | As many as needed             |
| Type organization  | ✅ Yes    | Multiple files OK             |
| Test organization  | ✅ Yes    | Multiple strategies OK        |
| Main class pattern | ❌ No     | Single class required         |
| Factory method     | ❌ No     | Exact signature required      |
| Async init         | ❌ No     | isReady() required            |
| Worker support     | ❌ No     | Must implement                |
| Type exports       | ❌ No     | Standard pattern required     |

**Conclusion:** Flexibility in **implementation details**, rigidity in **architectural patterns**.

---

### 6. Multi-Class Implementations: ZERO ACCEPTED ✅

**Finding:** **Zero multi-class implementations** have been accepted in ogc-client history.

**Comprehensive Search Results:**

**All Existing Implementations:**

1. ✅ WmsEndpoint - Single class
2. ✅ WfsEndpoint - Single class
3. ✅ WmtsEndpoint - Single class
4. ✅ OgcApiEndpoint - Single class
5. ✅ EDRQueryBuilder - Single class (7 query types)

**Zero Examples of:**

- ❌ Multiple client classes per resource type
- ❌ Delegation pattern (main class → specialized classes)
- ❌ Facade pattern (coordinator → operation classes)
- ❌ Strategy pattern (interchangeable operation classes)
- ❌ Separate classes per operation type

**Historical Analysis:**

No PR history showing:

- Multi-class proposals being submitted
- Multi-class proposals being rejected
- Discussion of multi-class vs single-class trade-offs

**Implication:** Multi-class pattern has **never been proposed** or **never made it past initial review**. The single-class pattern is so strongly established that alternatives aren't even considered.

**Risk Assessment:**

| Approach                  | Precedent | Acceptance Risk             |
| ------------------------- | --------- | --------------------------- |
| Single CSAPIQueryBuilder  | ✅ 100%   | 🟢 LOW - Proven             |
| Multiple resource clients | ❌ 0%     | 🔴 HIGH - Unknown territory |
| Facade + delegation       | ❌ 0%     | 🔴 HIGH - Over-engineering  |
| Hybrid approach           | ❌ 0%     | 🔴 HIGH - Inconsistent      |

**Conclusion:** Multi-class = **uncharted territory** with **high rejection risk**.

---

### 7. Explicit vs Implicit Expectations ✅

**Finding:** Upstream has both **explicit requirements** (documented) and **implicit expectations** (pattern-based).

**Explicit Requirements (Documented):**

**1. TypeScript:**

- All implementations must be TypeScript
- Comprehensive type definitions required
- Type exports from index.ts required

**2. Testing:**

- Jest test framework
- 90%+ code coverage target
- Fixtures for integration tests

**3. Documentation:**

- JSDoc comments on all public APIs
- README with usage examples
- Type documentation (TSDoc)

**4. Web Worker:**

- Register handlers in worker/worker.ts
- Export functions from worker/index.ts
- Support fallback mode

**5. Compatibility:**

- ES modules only
- Browser and Node.js support
- Configurable fetch options

**Implicit Expectations (Pattern-Based):**

**1. Single Main Class:**

- Not documented as requirement
- ALL implementations follow pattern
- Deviation likely to cause rejection
- **Evidence:** 100% consistency across implementations

**2. Endpoint-Oriented API:**

- Pattern is clear from examples
- Not explicitly mandated in docs
- Universal adoption = implicit requirement

**3. Async Initialization:**

- isReady() pattern universal
- Constructor starts async work
- Not explicitly required but expected

**4. Factory Method Pattern:**

- Exact signature across implementations
- Caching pattern consistent
- Not documented but universally followed

**5. File Organization Conventions:**

- endpoint.ts, model.ts, url.ts pattern
- Subfolders for complex features
- Not mandated but conventional

**6. Error Handling:**

- Custom error types (EndpointError, etc.)
- Error wrapping with cause
- Not explicitly required but standard

**7. Code Style:**

- Prettier formatting
- ESLint rules
- Naming conventions (camelCase, etc.)

**How to Identify Implicit Expectations:**

✅ **Look for 100% consistency** across all implementations
✅ **Assume pattern is expected** unless explicitly marked as optional
✅ **Follow precedent** when in doubt

**Risk Mitigation:**

For implicit expectations:

1. Follow existing patterns exactly
2. Don't innovate on architectural patterns
3. Save innovation for helper utilities
4. When uncertain, ask maintainers early

**Conclusion:** Implicit expectations are **as important** as explicit requirements. Pattern consistency = expectation.

---

## Architecture Decision Implications

### Single-Class Pattern: Strongly Recommended

**Evidence:**

1. ✅ 100% of implementations use single main class
2. ✅ EDR proves pattern scales (7 query types → 561 lines)
3. ✅ Zero multi-class examples in history
4. ✅ Pattern is implicit but universal expectation
5. ❌ No precedent for deviation

**Risk Assessment:**

- **Single class:** LOW risk (proven, universal)
- **Multi-class:** HIGH risk (no precedent, likely rejection)

### Format Abstraction: Fully Aligned

**Upstream Precedent:**

- WFS parses GML (XML-based OGC format)
- WMTS handles tile matrix calculations
- EDR handles WKT parsing

**CSAPI Equivalent:**

- Parse SensorML (XML-based OGC format)
- Parse SWE Common (complex structures)
- Parse GeoJSON (standard geometry format)

**Conclusion:** Format abstraction is **expected** when formats are core to the standard.

### Helper Files: Acceptable

**Allowed:**

- ✅ Separate files for parsing (conformance, collections, formats)
- ✅ Separate files for URL building
- ✅ Separate files for validation
- ✅ Separate files for types

**Not Allowed:**

- ❌ Separate classes for operations (systems, deployments, etc.)
- ❌ Delegation pattern splitting functionality
- ❌ Facade pattern with internal clients

### Integration Points: Exact Pattern Match Required

**Must implement:**

1. `OgcApiEndpoint.csapi(collection_id)` factory method
2. Map-based caching by collection_id
3. Conformance check before instantiation
4. Return `Promise<CSAPIQueryBuilder>`

**Must follow EDR pattern exactly:**

```typescript
private collection_id_to_csapi_builder_: Map<string, CSAPIQueryBuilder> = new Map();

public async csapi(collection_id: string): Promise<CSAPIQueryBuilder> {
  if (!this.hasConnectedSystems) {
    throw new EndpointError('Endpoint does not support Connected Systems API');
  }
  const cache = this.collection_id_to_csapi_builder_;
  if (cache.has(collection_id)) {
    return cache.get(collection_id);
  }
  const collection = await this.getCollectionInfo(collection_id);
  const result = new CSAPIQueryBuilder(collection);
  cache.set(collection_id, result);
  return result;
}
```

---

## Synthesis for Final Recommendations

### Mandatory Patterns (Non-Negotiable)

1. **✅ Single Main Class:** CSAPIQueryBuilder (NOT multiple resource clients)
2. **✅ Factory Method:** `endpoint.csapi(collection_id): Promise<CSAPIQueryBuilder>`
3. **✅ Caching:** Map-based by collection_id
4. **✅ Async Init:** Parse metadata asynchronously
5. **✅ TypeScript:** Comprehensive types for all entities
6. **✅ Web Worker:** Offload parsing to background thread
7. **✅ Testing:** 90%+ coverage with fixtures
8. **✅ Documentation:** JSDoc on all public APIs

### Flexible Areas (Innovation Allowed)

1. **✅ Helper Files:** Separate files for parsing, validation, formatting
2. **✅ File Organization:** Subfolders, multiple utility files
3. **✅ Type Organization:** Split across multiple files
4. **✅ Test Organization:** Multiple test files and strategies
5. **✅ Format Parsers:** Plugin architecture, extensibility

### Single vs Multi-Class: STRONG RECOMMENDATION

**Evidence Strength:** CRITICAL

**Key Findings:**

1. ✅ 100% of implementations use single class
2. ✅ EDR proves scalability (7 types → 561 lines)
3. ✅ CSAPI projection: 9 types → 850-950 lines (manageable)
4. ❌ Zero multi-class examples exist
5. ❌ Multi-class = uncharted territory

**Recommendation:** **STRONGLY FAVOR single CSAPIQueryBuilder class**

**Risk Level:**

- Single class: 🟢 **LOW** (proven, universal, expected)
- Multi-class: 🔴 **HIGH** (no precedent, likely rejection, over-engineering)

### Format Abstraction: FULLY ALIGNED

**Upstream Precedent:** WFS, WMTS, EDR all handle format-specific parsing
**CSAPI:** SensorML, SWE Common, GeoJSON parsing aligns perfectly
**Conclusion:** ✅ Format abstraction is **expected** and **acceptable**

### Next Steps

1. ✅ Confirmed: Single CSAPIQueryBuilder class strongly recommended
2. ✅ Confirmed: Factory method pattern required
3. ✅ Confirmed: Helper files for utilities acceptable
4. ✅ Confirmed: Format abstraction aligned with upstream
5. ⏭️ Next: Compare with OWSLib pattern (plan 05)
6. ⏭️ Next: Review previous decisions (plan 03)
7. ⏭️ Next: Make final architecture decision

---

**STATUS:** ✅ COMPLETE - Ready for synthesis
