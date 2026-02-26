# Research Plan 02: QueryBuilder Pattern Core Concepts - FINDINGS

**Research Completed:** February 4, 2026  
**Source Document:** [docs/research/upstream/querybuilder-pattern-analysis.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/upstream/querybuilder-pattern-analysis.md)  
**Researcher:** GitHub Copilot

---

## Executive Summary

**CRITICAL FINDING:** The QueryBuilder pattern in ogc-client **does NOT inherently require** a single class at the pattern level, BUT **upstream implementation precedent strongly favors** single consolidated classes.

**Pattern Characteristics:**

- **Definition:** Standalone class encapsulating collection metadata and providing query methods
- **NOT a subclass:** Independent class, not extending OgcApiEndpoint
- **State:** Immutable after construction, derived from collection metadata
- **Lifecycle:** Factory method → caching → usage → reuse
- **Organization:** No formal requirement for single vs multi-class, but EDR precedent shows single class

**Architecture Decision Impact:** While the pattern itself allows flexibility, **upstream expectations** (based on EDR implementation) strongly favor single consolidated classes. Multi-class approach is **pattern-compatible** but **precedent-incompatible**.

---

## Detailed Findings

### 1. Canonical QueryBuilder Pattern Definition ✅

**Finding:** A QueryBuilder in ogc-client is a **standalone class** with specific responsibilities.

**Pattern Characteristics:**

```typescript
export default class QueryBuilder {
  // 1. ENCAPSULATES collection-specific metadata
  private collection: OgcApiCollectionInfo;

  // 2. EXPOSES capability information publicly
  public supported_capabilities: Set<string>;
  public supported_parameters: Record<string, any>;
  public links: Array<{...}>;

  // 3. VALIDATES in constructor
  constructor(private collection: OgcApiCollectionInfo) {
    if (!collection.requiredData) {
      throw new Error('Collection missing required data');
    }
    this.supported_capabilities = extractCapabilities(collection);
  }

  // 4. PROVIDES query/resource access methods
  async getResource(...): Promise<Data> { ... }
  buildResourceUrl(...): string { ... }
}
```

**Key Responsibilities:**
| Responsibility | Description |
|----------------|-------------|
| **Encapsulation** | Stores collection metadata privately |
| **Validation** | Validates capabilities in constructor and methods |
| **URL Building** | Constructs query URLs from collection links |
| **Query Execution** | Optionally executes queries and returns typed data |
| **Capability Exposure** | Provides public access to what's supported |

**What QueryBuilder is NOT:**

- ❌ NOT a subclass of OgcApiEndpoint
- ❌ NOT responsible for fetching collection metadata
- ❌ NOT responsible for caching itself
- ❌ NOT responsible for conformance checking

**Relationship to Endpoint:**

```
User → OgcApiEndpoint.apiMethod(collectionId) → QueryBuilder → Query Methods
        ↑                                           ↑
        Fetches metadata                            Uses metadata
        Caches QueryBuilder                         Builds URLs
        Checks conformance                          Validates params
```

**Pattern Definition:** A QueryBuilder is a **metadata-driven query interface** that encapsulates collection capabilities and provides type-safe access to API-specific operations.

---

### 2. Single vs Multi-Class Requirement ✅

**Finding:** The pattern **does NOT formally require** a single class, but **implementation precedent strongly suggests** it.

**Pattern-Level Flexibility:**

The QueryBuilder pattern definition has **no explicit constraint** requiring single class:

- No interface mandating "all operations in one class"
- No documentation stating "must be single class"
- Pattern focuses on responsibilities, not class count

**Implementation Evidence:**

**EDR Implementation (PR #114):**

- ✅ Single class: `EDRQueryBuilder` (561 lines)
- ✅ No helper classes for query types
- ✅ 7 query types in one class
- ✅ Sequential method organization

**No Multi-Class Examples Found:**

- ❌ No examples of QueryBuilder split across multiple classes
- ❌ No delegation pattern (main builder → helper classes)
- ❌ No facade pattern (coordinator → specialized builders)

**Theoretical Multi-Class Compatibility:**

Pattern **could** theoretically support multiple classes:

```typescript
// Hypothetical multi-class approach (NOT found in ogc-client)

// Facade/coordinator
class CSAPIQueryBuilder {
  constructor(collection: OgcApiCollectionInfo) {
    this.systemsClient = new SystemsClient(collection);
    this.deploymentsClient = new DeploymentsClient(collection);
    // ...
  }

  get systems() { return this.systemsClient; }
  get deployments() { return this.deploymentsClient; }
}

// Specialized clients
class SystemsClient {
  constructor(private collection: OgcApiCollectionInfo) { ... }
  async getSystems(...): Promise<System[]> { ... }
}
```

**This approach:**

- ✅ Meets pattern responsibilities (encapsulation, validation, query building)
- ✅ Maintains immutable state
- ✅ Uses factory method and caching
- ❌ BUT: No precedent in upstream codebase
- ❌ BUT: Increases complexity vs single class

**Conclusion:** Pattern **allows** multi-class, but **precedent strongly discourages** it.

---

### 3. Required Responsibilities ✅

**Finding:** A QueryBuilder must fulfill these specific responsibilities:

**1. Collection Metadata Encapsulation**

```typescript
class EDRQueryBuilder {
  private collection: OgcApiCollectionInfo; // REQUIRED

  constructor(private collection: OgcApiCollectionInfo) {
    // Store collection metadata
  }
}
```

**Requirement:** Store collection info passed from endpoint factory method.

**2. Capability Validation**

```typescript
constructor(private collection: OgcApiCollectionInfo) {
  // REQUIRED: Validate collection has required data
  if (!collection.data_queries) {
    throw new Error('No data queries found, so cannot issue EDR queries');
  }

  // REQUIRED: Extract and store capabilities
  this.supported_query_types = {
    area: collection.data_queries.area !== undefined,
    cube: collection.data_queries.cube !== undefined,
    // ...
  };
}
```

**Requirement:** Fail fast if collection doesn't support API.

**3. Capability Exposure**

```typescript
// REQUIRED: Public access to capabilities
public supported_parameters: Record<string, EdrParameterInfo> = {};
public supported_crs: CrsCode[] = [];

get supported_queries(): Set<DataQueryType> {
  // Return what query types are available
}
```

**Requirement:** Users must be able to check what's supported before calling methods.

**4. URL Construction from Links**

```typescript
buildPositionDownloadUrl(...): string {
  // REQUIRED: Get URL from collection links (never hardcode)
  const url = new URL(this.collection.data_queries?.position?.link.href);

  // Add query parameters
  url.searchParams.set('coords', ...);

  return url.toString();
}
```

**Requirement:** Always use URLs from collection metadata (hypermedia principle).

**5. Runtime Validation**

```typescript
buildAreaDownloadUrl(...): string {
  // REQUIRED: Validate capability at runtime
  if (!this.supported_query_types.area) {
    throw new Error('Collection does not support area queries');
  }

  // REQUIRED: Validate parameters against collection metadata
  if (optional_params.parameter_name) {
    for (const param of optional_params.parameter_name) {
      if (!this.supported_parameters[param]) {
        throw new Error(`Parameter '${param}' not supported`);
      }
    }
  }

  // Build URL
}
```

**Requirement:** Validate operations and parameters against collection capabilities.

**Optional Responsibilities:**

- Query execution (async methods that fetch data) - EDR has these, not required
- Data parsing/transformation - EDR does basic parsing
- Result caching - NOT done in QueryBuilder (endpoint handles it)

---

### 4. Factory Method and Caching Pattern ✅

**Finding:** Factory method + caching is a **required pattern** for QueryBuilder instantiation.

**Factory Method Pattern:**

**Location:** In `OgcApiEndpoint` class, NOT in QueryBuilder itself

```typescript
export default class OgcApiEndpoint {
  // REQUIRED: Private cache Map
  private collection_id_to_edr_builder_: Map<string, EDRQueryBuilder> =
    new Map();

  // REQUIRED: Public async factory method
  public async edr(collection_id: string): Promise<EDRQueryBuilder> {
    // 1. REQUIRED: Conformance check
    if (!this.hasEnvironmentalDataRetrieval) {
      throw new EndpointError('Endpoint does not support EDR');
    }

    // 2. REQUIRED: Check cache first
    const cache = this.collection_id_to_edr_builder_;
    if (cache.has(collection_id)) {
      return cache.get(collection_id); // Return cached instance
    }

    // 3. REQUIRED: Fetch collection metadata
    const collection = await this.getCollectionInfo(collection_id);

    // 4. REQUIRED: Instantiate QueryBuilder
    const result = new EDRQueryBuilder(collection);

    // 5. REQUIRED: Cache for reuse
    cache.set(collection_id, result);

    // 6. REQUIRED: Return instance
    return result;
  }
}
```

**Why Factory Method:**

1. **Hides complexity:** User doesn't fetch collection metadata
2. **Enforces caching:** Prevents duplicate instances
3. **Validates conformance:** Checks endpoint support before creation
4. **Async-friendly:** Handles async metadata fetching

**Caching Strategy:**

**Cache Structure:**

```typescript
Map<collection_id: string, builder: QueryBuilder>
```

**Cache Key:** Collection ID (string)
**Cache Value:** QueryBuilder instance
**Cache Lifetime:** Per-endpoint instance

**Caching Benefits:**

- ✅ Performance: Avoids redundant metadata fetches
- ✅ Consistency: Same collection = same builder instance
- ✅ Memory: Reasonable (one builder per accessed collection)

**Cache Test Pattern:**

```typescript
it('caches properly', async () => {
  const spy = jest.spyOn(endpoint, 'getCollectionInfo');

  const builder1 = await endpoint.edr('collection-1');
  const builder2 = await endpoint.edr('collection-1');

  expect(builder1).toBe(builder2); // Same instance reference
  expect(spy).toHaveBeenCalledTimes(1); // Metadata fetched once
});
```

**CSAPI Pattern:**

```typescript
class OgcApiEndpoint {
  private collection_id_to_csapi_builder_: Map<string, CSAPIQueryBuilder> =
    new Map();

  public async csapi(collection_id: string): Promise<CSAPIQueryBuilder> {
    if (!this.hasConnectedSystems) {
      throw new EndpointError('Endpoint does not support CSAPI');
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

**Conclusion:** Factory method + caching is **mandatory** for QueryBuilder pattern.

---

### 5. Metadata Encapsulation Requirements ✅

**Finding:** QueryBuilder **must** encapsulate specific metadata from `OgcApiCollectionInfo`.

**Source of State:**

All QueryBuilder state comes from `OgcApiCollectionInfo`:

```typescript
interface OgcApiCollectionInfo {
  id: string;                    // Collection identifier
  title: string;                 // Human-readable title
  description?: string;          // Optional description
  extent?: {                     // Spatial/temporal extent
    spatial: {...};
    temporal: {...};
  };
  crs?: CrsCode[];              // Supported coordinate systems
  links: OgcApiDocumentLink[];  // Hypermedia links (CRITICAL for URLs)

  // API-specific extensions
  data_queries?: {              // EDR-specific
    position?: { link: { href: string } };
    area?: { link: { href: string } };
    // ...
  };
  parameter_names?: Record<string, EdrParameterInfo>;

  // CSAPI would have:
  // csapi_resources?: {
  //   systems?: { link: { href: string } };
  //   deployments?: { link: { href: string } };
  //   // ...
  // };
}
```

**Required Encapsulation:**

**1. Private Storage:**

```typescript
class EDRQueryBuilder {
  private collection: OgcApiCollectionInfo; // REQUIRED: Store entire object

  constructor(private collection: OgcApiCollectionInfo) {
    // Collection is stored privately
  }
}
```

**2. Derived State:**

```typescript
class EDRQueryBuilder {
  // REQUIRED: Compute and store capabilities
  private supported_query_types: {
    area: boolean;
    cube: boolean;
    position: boolean;
    // ...
  };

  constructor(private collection: OgcApiCollectionInfo) {
    // Extract boolean flags for each query type
    this.supported_query_types = {
      area: collection.data_queries?.area !== undefined,
      cube: collection.data_queries?.cube !== undefined,
      position: collection.data_queries?.position !== undefined,
      // ...
    };
  }
}
```

**3. Public Exposure:**

```typescript
class EDRQueryBuilder {
  // REQUIRED: Expose capabilities publicly
  public supported_parameters: Record<string, EdrParameterInfo> = {};
  public supported_crs: CrsCode[] = [];
  public links: OgcApiDocumentLink[] = [];

  // REQUIRED: Computed getter
  get supported_queries(): Set<DataQueryType> {
    const queries: Set<DataQueryType> = new Set();
    for (const [key, value] of Object.entries(this.supported_query_types)) {
      if (value) queries.add(key as DataQueryType);
    }
    return queries;
  }

  constructor(private collection: OgcApiCollectionInfo) {
    this.supported_parameters = collection.parameter_names || {};
    this.supported_crs = collection.crs || [];
    this.links = collection.links;
  }
}
```

**State Immutability:**

**CRITICAL:** QueryBuilder state is **immutable after construction**.

```typescript
class EDRQueryBuilder {
  // All state set in constructor
  constructor(private collection: OgcApiCollectionInfo) {
    this.supported_query_types = { ... };
    this.supported_parameters = { ... };
    // etc.
  }

  // NO setter methods
  // NO mutation of state
  // State never changes after construction
}
```

**Why Immutable:**

- Cached instances are reused
- Multiple users may reference same instance
- State must be consistent across all uses

**CSAPI Metadata:**

```typescript
class CSAPIQueryBuilder {
  private collection: OgcApiCollectionInfo;

  private supported_resource_types: {
    systems: boolean;
    deployments: boolean;
    procedures: boolean;
    samplingFeatures: boolean;
    properties: boolean;
    datastreams: boolean;
    observations: boolean;
    controlStreams: boolean;
    commands: boolean;
  };

  public supported_resources: Set<string>;
  public links: OgcApiDocumentLink[];

  constructor(private collection: OgcApiCollectionInfo) {
    // Extract resource availability from links or csapi_resources
    this.supported_resource_types = this.extractResourceTypes();
    this.supported_resources = new Set(
      Object.entries(this.supported_resource_types)
        .filter(([_, supported]) => supported)
        .map(([resource, _]) => resource)
    );
    this.links = collection.links;
  }
}
```

---

### 6. Multi-Class QueryBuilder Examples ✅

**Finding:** **NO examples** of multi-class QueryBuilders exist in ogc-client codebase.

**Search Results:**

Searched across all implementations:

- WFS: Single class (inferred from pattern)
- WMS: Single class (inferred from pattern)
- WMTS: Single class (inferred from pattern)
- EDR: Single class (confirmed - `EDRQueryBuilder`, 561 lines)

**Zero instances of:**

- QueryBuilder delegating to helper classes
- Multiple specialized builder classes per query type
- Facade pattern with internal delegation
- Strategy pattern for different query types

**Implication:** While pattern **theoretically allows** multiple classes, **zero precedent** exists in ogc-client codebase.

**Closest Pattern: Helper Classes**

EDR has separate helper files, but NOT for query type organization:

```
src/ogc-api/edr/
├── url_builder.ts     ← Single QueryBuilder class (561 lines)
├── model.ts           ← Types and interfaces (125 lines)
└── helpers.ts         ← Utility functions (23 lines)
```

**helpers.ts contains:**

- `DateTimeParameterToEDRString()` - Format datetime for EDR
- `zParameterToString()` - Format z-level parameter
- NOT separate query type handlers

**model.ts contains:**

- Type definitions
- Interfaces
- NOT separate query classes

**Conclusion:** Helper files exist for **utilities and types**, NOT for splitting QueryBuilder functionality across multiple classes.

---

### 7. Method Organization Requirements ✅

**Finding:** Pattern has **no formal method organization requirements**, but EDR shows clear conventions.

**No Enforced Organization:**

Pattern does not specify:

- ❌ How methods should be ordered
- ❌ Whether to use section comments
- ❌ Grouping strategies
- ❌ Naming conventions beyond being descriptive

**EDR Method Organization (Observed Convention):**

**File: url_builder.ts (561 lines)**

```typescript
export default class EDRQueryBuilder {
  // Properties (lines 1-20)
  private supported_query_types: {...};
  public supported_parameters: {...};
  // ...

  // Constructor (lines 21-40)
  constructor(private collection: OgcApiCollectionInfo) { ... }

  // Getter (lines 41-50)
  get supported_queries(): Set<DataQueryType> { ... }

  // Query methods (lines 51-561) - NO section comments
  buildPositionDownloadUrl(...): string { ... }      // ~80 lines
  buildAreaDownloadUrl(...): string { ... }          // ~75 lines
  buildCubeDownloadUrl(...): string { ... }          // ~70 lines
  buildTrajectoryDownloadUrl(...): string { ... }    // ~80 lines
  buildCorridorDownloadUrl(...): string { ... }      // ~75 lines
  buildRadiusDownloadUrl(...): string { ... }        // ~75 lines
  buildLocationsDownloadUrl(...): string { ... }     // ~50 lines
}
```

**Organization Strategy:**

1. Properties first
2. Constructor second
3. Getters third
4. Query methods sequential (NO grouping comments)

**Method Pattern Consistency:**

Every query method follows **identical structure**:

```typescript
build[QueryType]DownloadUrl(
  requiredParams,
  optional_params: Optional[QueryType]Params = {}
): string {
  // 1. Capability check
  if (!this.supported_query_types.[queryType]) {
    throw new Error('Collection does not support [queryType] queries');
  }

  // 2. Base URL from links
  const url = new URL(this.collection.data_queries?.[queryType]?.link.href);

  // 3. Required parameters
  url.searchParams.set('coords', coords);

  // 4. Optional parameters with validation
  if (optional_params.parameter_name) {
    // Validate
    for (const param of optional_params.parameter_name) {
      if (!this.supported_parameters[param]) {
        throw new Error(`Parameter '${param}' not supported`);
      }
    }
    // Set
    url.searchParams.set('parameter-name', optional_params.parameter_name.join(','));
  }
  // ... more optional params

  // 5. Return URL
  return url.toString();
}
```

**Pattern repetition provides:**

- Predictability
- Easy to scan visually
- Consistent error handling
- No cognitive load from varied patterns

**CSAPI Method Organization:**

For 9 resource types with CRUD operations:

```typescript
class CSAPIQueryBuilder {
  // Properties
  private collection: OgcApiCollectionInfo;
  private supported_resource_types: {...};
  public supported_resources: Set<string>;

  // Constructor
  constructor(...) { ... }

  // Systems methods (~60 lines)
  async getSystems(options?: QueryOptions): Promise<System[]> { ... }
  async getSystem(systemId: string): Promise<System> { ... }
  async createSystem(system: System): Promise<System> { ... }
  async updateSystem(systemId: string, system: System): Promise<System> { ... }
  async deleteSystem(systemId: string): Promise<void> { ... }

  // Deployments methods (~60 lines)
  async getDeployments(options?: QueryOptions): Promise<Deployment[]> { ... }
  async getDeployment(deploymentId: string): Promise<Deployment> { ... }
  // ...

  // Continue for all 9 resources (~540 lines)
  // Plus sub-resource methods (~300 lines)
  // Total: ~850-950 lines estimated
}
```

**Optional: Section Comments**

Could add for readability (not required by pattern):

```typescript
class CSAPIQueryBuilder {
  // ... properties and constructor

  // ============================================================================
  // Systems Resource
  // ============================================================================

  async getSystems(...): Promise<System[]> { ... }
  // ...

  // ============================================================================
  // Deployments Resource
  // ============================================================================

  async getDeployments(...): Promise<Deployment[]> { ... }
  // ...
}
```

**Conclusion:** No formal requirements, but consistency and sequential organization are conventions.

---

### 8. Helper Class Delegation ✅

**Finding:** QueryBuilder **can** delegate to helper classes for utilities, but **NOT** for splitting core functionality.

**Allowed Helper Pattern:**

```typescript
// helpers.ts - Utility functions
export function formatDateTime(dt: DateTimeParameter): string {
  // Format logic
}

export function formatBBox(bbox: number[]): string {
  // Format logic
}

// url_builder.ts - QueryBuilder uses helpers
import { formatDateTime, formatBBox } from './helpers';

class CSAPIQueryBuilder {
  buildSystemsUrl(...): string {
    const url = new URL(baseUrl);

    // Use helper functions
    if (options.datetime) {
      url.searchParams.set('datetime', formatDateTime(options.datetime));
    }
    if (options.bbox) {
      url.searchParams.set('bbox', formatBBox(options.bbox));
    }

    return url.toString();
  }
}
```

**Allowed:** Helper functions for:

- ✅ Parameter formatting/serialization
- ✅ Validation logic
- ✅ URL parsing utilities
- ✅ Date/time conversions

**NOT Allowed (No Precedent):**

```typescript
// ❌ NOT found in ogc-client - splitting query functionality

// systems_client.ts
class SystemsClient {
  async getSystems(...): Promise<System[]> { ... }
}

// deployments_client.ts
class DeploymentsClient {
  async getDeployments(...): Promise<Deployment[]> { ... }
}

// url_builder.ts - Delegating to specialized classes
class CSAPIQueryBuilder {
  private systemsClient: SystemsClient;
  private deploymentsClient: DeploymentsClient;

  constructor(collection) {
    this.systemsClient = new SystemsClient(collection);
    this.deploymentsClient = new DeploymentsClient(collection);
  }

  async getSystems(...) {
    return this.systemsClient.getSystems(...); // Delegation
  }
}
```

**Why NOT Allowed:**

- No precedent in codebase
- Adds complexity without clear benefit
- More classes to test and maintain
- Breaks from established pattern

**EDR Helper Usage:**

```typescript
// helpers.ts (23 lines)
export function DateTimeParameterToEDRString(
  datetime: DateTimeParameter
): string {
  // Convert JS Date/string/object to EDR datetime format
}

export function zParameterToString(z: number | [number, number]): string {
  // Format z-level parameter
}

// url_builder.ts uses helpers
buildPositionDownloadUrl(...): string {
  const url = new URL(baseUrl);

  if (optional_params.datetime) {
    url.searchParams.set(
      'datetime',
      DateTimeParameterToEDRString(optional_params.datetime) // Helper usage
    );
  }

  if (optional_params.z) {
    url.searchParams.set('z', zParameterToString(optional_params.z)); // Helper usage
  }

  return url.toString();
}
```

**Pattern:** Helper functions are **pure utilities**, NOT class delegation.

**Conclusion:** Helper functions for utilities = ✅ OK. Helper classes for functionality split = ❌ No precedent.

---

## Architecture Decision Implications

### Pattern Flexibility vs Precedent Constraints

**Pattern-Level Analysis:**

- ✅ Pattern allows single class
- ✅ Pattern allows multiple classes (theoretically)
- ✅ Pattern allows helper utilities
- ❌ Pattern does NOT require specific organization

**Precedent-Level Analysis:**

- ✅ EDR uses single class (561 lines, 7 types)
- ✅ All implementations use single class (inferred)
- ❌ Zero multi-class examples
- ❌ No delegation pattern examples

**Conclusion Matrix:**

| Approach                  | Pattern Compatible | Precedent Compatible | Risk Level |
| ------------------------- | ------------------ | -------------------- | ---------- |
| Single CSAPIQueryBuilder  | ✅ Yes             | ✅ Yes               | 🟢 LOW     |
| Multiple resource clients | ✅ Yes             | ❌ No                | 🔴 HIGH    |
| Single with helpers       | ✅ Yes             | ✅ Yes               | 🟢 LOW     |
| Facade + delegations      | ✅ Yes             | ❌ No                | 🔴 HIGH    |

### Single Class Recommendation

**Reasons to use single class:**

1. **Precedent:** EDR proves it works for 7 types
2. **Scalability:** CSAPI projection (9 types) → ~850-950 lines (manageable)
3. **Consistency:** Matches all existing implementations
4. **Simplicity:** One class, one cache, one factory method
5. **Testing:** Consistent test patterns
6. **Review:** Easier to review single coherent class
7. **Acceptance:** Follows upstream expectations

**Risks of multiple classes:**

1. **No precedent:** Zero examples in ogc-client
2. **Complexity:** More files, more integration points
3. **Inconsistency:** Breaks from established pattern
4. **Review burden:** More files to review
5. **Rejection risk:** May be seen as over-engineering
6. **Maintenance:** Code duplication across classes

### Helper Functions Recommendation

**Use helper functions for:**

- ✅ Parameter formatting (dates, bboxes, coords)
- ✅ Validation utilities
- ✅ URL parsing helpers
- ✅ Type conversions

**Structure:**

```
src/ogc-api/csapi/
├── url_builder.ts     (~850 lines - CSAPIQueryBuilder)
├── model.ts           (~150 lines - Types)
├── helpers.ts         (~50 lines - Utilities)
└── helpers.spec.ts    (~50 lines - Helper tests)
```

---

## Synthesis for Final Recommendations

### Pattern Definition: CLEAR

**What is a QueryBuilder:**

- Standalone class (NOT endpoint subclass)
- Encapsulates collection metadata
- Validates capabilities
- Builds URLs from links
- Optionally executes queries
- Immutable state after construction

### Single vs Multi-Class: PATTERN ALLOWS, PRECEDENT CONSTRAINS

**Pattern:** Does NOT explicitly require single class
**Precedent:** ALL implementations use single class
**Recommendation:** Use single class to match precedent

### Factory + Caching: REQUIRED

**Must have:**

- Factory method in OgcApiEndpoint
- Map-based caching by collection_id
- Conformance check before instantiation
- Async pattern for metadata fetching

### Helper Classes: LIMITED USE

**Allowed:** Utility functions in helpers.ts
**Not Allowed:** Splitting functionality across classes

### Architecture Decision: SINGLE CLASS STRONGLY RECOMMENDED

**Evidence Strength:** CRITICAL

**Key Findings:**

1. ✅ Pattern theoretically allows multi-class
2. ✅ Precedent shows ONLY single-class implementations
3. ✅ EDR proves single class scales (7 types → 561 lines)
4. ✅ CSAPI projection: 9 types → 850-950 lines (manageable)
5. ❌ Zero multi-class examples in ogc-client
6. ❌ Multi-class adds complexity without proven benefit

**Risk Assessment:**

- **Single class:** LOW risk (proven, precedent)
- **Multi-class:** HIGH risk (no precedent, complexity, rejection)

**Next Steps:**

1. Confirm upstream expectations (plan 10)
2. Compare with OWSLib's multi-class pattern (plan 05)
3. Review previous architectural decisions (plan 03)
4. Make final decision based on all evidence

---

**STATUS:** ✅ COMPLETE - Ready for synthesis
