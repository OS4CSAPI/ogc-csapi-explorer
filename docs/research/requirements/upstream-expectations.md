# Upstream Library Expectations - camptocamp/ogc-client

**Purpose:** Define what the upstream ogc-client library expects from CSAPI implementation based on existing patterns from WFS, WMS, WMTS, EDR, and OGC API implementations.

**Context:** CSAPI will be contributed to camptocamp/ogc-client as a new module. Must follow established patterns, conventions, and quality standards.

**Date:** 2026-01-31

---

## Executive Summary

**Core Finding:** camptocamp/ogc-client expects implementations to provide **endpoint-oriented API** with:

1. Capabilities parsing (extract server metadata)
2. URL builders (construct request URLs with parameters)
3. Typed models (TypeScript interfaces for all entities)
4. Consistent patterns (common interface across OGC standards)
5. Web Worker support (parse XML/JSON in background thread)

**CSAPI Fit:** CSAPI follows same patterns - parse conformance/collections, build resource URLs, provide TypeScript types. Format abstraction layer (SensorML, SWE Common, GeoJSON) aligns with WFS GML parsing and WMTS tile matrix handling.

---

## 1. Architecture Patterns

### 1.1 Endpoint Class Pattern

**All implementations follow "Endpoint" class pattern:**

```typescript
// WMS Example
export default class WmsEndpoint {
  private _capabilitiesUrl: string;
  private _capabilitiesPromise: Promise<void>;
  private _info: GenericEndpointInfo;
  private _layers: WmsLayerFull[];

  constructor(url: string) {
    this._capabilitiesUrl = setQueryParams(url, {
      SERVICE: 'WMS',
      REQUEST: 'GetCapabilities',
    });

    this._capabilitiesPromise = useCache(
      () => parseWmsCapabilities(this._capabilitiesUrl),
      'WMS',
      'CAPABILITIES',
      this._capabilitiesUrl
    ).then(({ info, layers, url, version }) => {
      this._info = info;
      this._layers = layers;
      this._url = url;
      this._version = version;
    });
  }

  isReady(): Promise<WmsEndpoint> {
    return this._capabilitiesPromise.then(() => this);
  }

  getServiceInfo(): GenericEndpointInfo {
    return this._info;
  }

  getLayers(): WmsLayerSummary[] {
    return this._layers;
  }
}

// WFS Example
export default class WfsEndpoint {
  constructor(url: string) {
    // Similar pattern - parse capabilities, cache results
  }

  isReady(): Promise<WfsEndpoint> {
    /* ... */
  }
  getServiceInfo(): GenericEndpointInfo {
    /* ... */
  }
  getFeatureTypes(): WfsFeatureTypeBrief[] {
    /* ... */
  }
}

// WMTS Example
export default class WmtsEndpoint {
  constructor(url: string) {
    // Similar pattern
  }

  isReady(): Promise<WmtsEndpoint> {
    /* ... */
  }
  getServiceInfo(): GenericEndpointInfo {
    /* ... */
  }
  getLayers(): WmtsLayer[] {
    /* ... */
  }
}

// OGC API Example
export default class OgcApiEndpoint {
  constructor(url: string) {
    // Parses landing page, conformance, collections
  }

  get allCollections(): Promise<OgcApiCollectionInfo[]> {
    /* ... */
  }
  get featureCollections(): Promise<OgcApiCollectionInfo[]> {
    /* ... */
  }
  getCollectionItems(collectionId: string): Promise<FeatureCollection> {
    /* ... */
  }
}
```

**Pattern Requirements for CSAPI:**

- Endpoint class: `CSAPIEndpoint`
- Constructor takes base URL
- Async initialization: `isReady()` returns Promise
- Service info getter: `getServiceInfo()`
- Resource type getters: `getCollections()`, `getSystems()`, etc.
- URL builders: `getSystemUrl()`, `createSystem()`, etc.

### 1.2 Capabilities Parsing Pattern

**All implementations parse capabilities/metadata documents:**

```typescript
// WMS - parseWmsCapabilities() in worker
export function readInfoFromCapabilities(doc: XmlDocument): GenericEndpointInfo {
  const service = findChildElement(getRootElement(doc), 'Service');
  return {
    title: getElementText(findChildElement(service, 'Title')),
    name: getElementText(findChildElement(service, 'Name')),
    abstract: getElementText(findChildElement(service, 'Abstract')),
    keywords: [...],
    outputFormats: readOutputFormatsFromCapabilities(doc),
    infoFormats: readInfoFormatsFromCapabilities(doc),
  };
}

export function readLayersFromCapabilities(doc: XmlDocument): WmsLayerFull[] {
  // Parse layer tree with inheritance
}

// WFS - similar pattern
export function readFeatureTypesFromCapabilities(doc: XmlDocument): WfsFeatureTypeInternal[] {
  // Parse feature types
}

// WMTS - similar pattern
export function readLayersFromCapabilities(doc: XmlDocument): WmtsLayer[] {
  // Parse tile layers
}
```

**Pattern Requirements for CSAPI:**

- Parse `/` (landing page) for service info
- Parse `/conformance` for capability detection
- Parse `/collections` for resource catalogs
- Cache parsed results (useCache utility)
- Extract: title, description, links, extent, CRS, formats
- Store in standard `GenericEndpointInfo` structure

### 1.3 URL Builder Pattern

**All implementations provide URL building functions:**

```typescript
// WMS
export function generateGetMapUrl(
  serviceUrl: string,
  version: WmsVersion,
  layers: string[],
  bbox: BoundingBox,
  crs: CrsCode,
  width: number,
  height: number,
  outputFormat: MimeType
): string {
  const params = new URLSearchParams();
  params.set('SERVICE', 'WMS');
  params.set('REQUEST', 'GetMap');
  params.set('LAYERS', layers.join(','));
  // ... more parameters
  return `${serviceUrl}?${params.toString()}`;
}

// WFS
export function generateGetFeatureUrl(
  serviceUrl: string,
  version: WfsVersion,
  featureType: string,
  outputFormat?: MimeType,
  maxFeatures?: number,
  bbox?: BoundingBox
  // ... more parameters
): string {
  // Build URL with parameters
}

// EDR (OGC API)
export default class EDRQueryBuilder {
  buildPositionDownloadUrl(
    coords: WellKnownTextString,
    optional_params: optionalPositionParams = {}
  ): string {
    let url = `${this.base_collection_url}/position?coords=${coords}`;
    if (optional_params.datetime) {
      url += `&datetime=${DateTimeParameterToEDRString(
        optional_params.datetime
      )}`;
    }
    // ... more parameters
    return url;
  }
}
```

**Pattern Requirements for CSAPI:**

- URL builder functions for each operation
- Parameter encoding (bbox, datetime, arrays, etc.)
- Format negotiation (f parameter, Accept header)
- Query parameter builders for filtering
- Sub-resource URL building (/systems/{id}/datastreams)

### 1.4 Web Worker Pattern

**All XML/JSON parsing happens in Web Worker:**

```typescript
// worker/worker.ts
addTaskHandler('parseWmsCapabilities', globalThis, ({ url }: { url: string }) =>
  queryXmlDocument(url)
    .then((xmlDoc) => check(xmlDoc, url))
    .then((xmlDoc) => ({
      info: wmsCapabilities.readInfoFromCapabilities(xmlDoc),
      layers: wmsCapabilities.readLayersFromCapabilities(xmlDoc),
      url: wmsCapabilities.readOperationUrlsFromCapabilities(xmlDoc),
      version: wmsCapabilities.readVersionFromCapabilities(xmlDoc),
    }))
);

// worker/index.ts
export function parseWmsCapabilities(capabilitiesUrl: string): Promise<{
  version: WmsVersion;
  url: Record<OperationName, OperationUrl>;
  info: GenericEndpointInfo;
  layers: WmsLayerFull[];
}> {
  return sendMessageToWorker('parseWmsCapabilities', { url: capabilitiesUrl });
}
```

**Pattern Requirements for CSAPI:**

- Register task handlers in `worker/worker.ts`
- Export functions in `worker/index.ts`
- Parse conformance/collections in worker
- Parse resource responses in worker (SensorML, SWE Common)
- Support fallback mode (`enableFallbackWithoutWorker()`)

---

## 2. TypeScript Type System

### 2.1 Shared Models

**All implementations use `shared/models.ts` types:**

```typescript
// shared/models.ts
export type BoundingBox = [number, number, number, number];
export type CrsCode = string;
export type MimeType = string;

export interface Address {
  deliveryPoint: string;
  city: string;
  administrativeArea: string;
  postalCode: string;
  country: string;
}

export interface Contact {
  name: string;
  position: string;
  phone: string;
  fax: string;
  address: Address;
  email: string;
}

export interface Provider {
  name: string;
  site: string;
  contact: Contact;
}

export type GenericEndpointInfo = {
  name: string;
  title: string;
  abstract: string;
  fees: string;
  constraints: string;
  keywords: string[];
  provider?: Provider;
  outputFormats?: MimeType[];
  infoFormats?: MimeType[];
  exceptionFormats?: string[];
};
```

**Pattern Requirements for CSAPI:**

- Extend `GenericEndpointInfo` for CSAPI service info
- Use `BoundingBox`, `CrsCode`, `MimeType` types
- Add CSAPI-specific shared types: `Feature`, `Geometry`, `Link`
- Export all types from `src/csapi/model.ts`

### 2.2 Implementation-Specific Models

**Each implementation defines its own model types:**

```typescript
// wms/model.ts
export interface WmsLayerFull {
  name: string;
  title: string;
  abstract: string;
  availableCrs: CrsCode[];
  styles: LayerStyle[];
  boundingBoxes: Record<CrsCode, BoundingBox>;
  children?: WmsLayerFull[]; // Recursive tree structure
}

export type WmsVersion = '1.1.0' | '1.1.1' | '1.3.0';

// wfs/model.ts
export interface WfsFeatureTypeFull {
  name: string;
  title?: string;
  abstract?: string;
  defaultCrs: CrsCode;
  otherCrs: CrsCode[];
  outputFormats: MimeType[];
  latLonBoundingBox?: BoundingBox;
  properties: WfsFeatureTypePropsDetails;
}

export type WfsVersion = '1.0.0' | '1.1.0' | '2.0.0';

// wmts/model.ts
export interface WmtsLayer {
  name: string;
  abstract: string;
  defaultStyle: string;
  styles: LayerStyle[];
  matrixSets: MatrixSetLink[];
  dimensions: LayerDimension[];
  latLonBoundingBox: BoundingBox;
}

// ogc-api/model.ts
export interface OgcApiCollectionInfo {
  id: string;
  title: string;
  description: string;
  extent?: {
    spatial?: { bbox: BoundingBox[] };
    temporal?: { interval: string[][] };
  };
  itemType?: string;
  links: Link[];
}
```

**Pattern Requirements for CSAPI:**

- Define `CSAPIEndpointInfo extends GenericEndpointInfo`
- Define resource types: `System`, `Deployment`, `Procedure`, etc.
- Define collection types: `SystemCollection`, `SystemFeature`
- Define query option types: `QueryParams`, `GetSystemOptions`
- Export all from `src/csapi/model.ts` and re-export from `src/index.ts`

### 2.3 Export Pattern

**Main index exports all public APIs:**

```typescript
// src/index.ts
export { default as WfsEndpoint } from './wfs/endpoint.js';
export type {
  WfsVersion,
  WfsFeatureWithProps,
  WfsFeatureTypeSummary,
  WfsFeatureTypeBrief,
  WfsFeatureTypeFull,
  WfsGetFeatureOptions,
} from './wfs/model.js';

export { default as WmsEndpoint } from './wms/endpoint.js';
export type { WmsLayerFull, WmsVersion, WmsLayerSummary } from './wms/model.js';

export { default as WmtsEndpoint } from './wmts/endpoint.js';
export type {
  WmtsLayer,
  WmtsEndpointInfo,
  WmtsMatrixSet,
} from './wmts/model.js';

export { default as OgcApiEndpoint } from './ogc-api/endpoint.js';
export type { OgcApiCollectionInfo } from './ogc-api/model.js';

export type {
  BoundingBox,
  CrsCode,
  MimeType,
  GenericEndpointInfo,
  Contact,
  Provider,
} from './shared/models.js';
```

**Pattern Requirements for CSAPI:**

```typescript
// Add to src/index.ts:
export { default as CSAPIEndpoint } from './csapi/endpoint.js';
export type {
  System,
  SystemFeature,
  SystemCollection,
  Deployment,
  DeploymentFeature,
  Procedure,
  SamplingFeature,
  Property,
  DataStream,
  Observation,
  ControlStream,
  Command,
  QueryParams,
  GetSystemOptions,
  // ... all public types
} from './csapi/model.js';
```

---

## 3. Code Organization

### 3.1 File Structure

**Consistent file structure across implementations:**

```
src/
├── wfs/
│   ├── endpoint.ts        # Main endpoint class
│   ├── capabilities.ts    # Parse capabilities doc
│   ├── model.ts          # TypeScript types
│   ├── url.ts            # URL builder functions
│   ├── featureprops.ts   # Feature property parsing
│   └── endpoint.spec.ts  # Tests
├── wms/
│   ├── endpoint.ts
│   ├── capabilities.ts
│   ├── model.ts
│   ├── url.ts
│   └── endpoint.spec.ts
├── wmts/
│   ├── endpoint.ts
│   ├── capabilities.ts
│   ├── model.ts
│   ├── url.ts
│   └── endpoint.spec.ts
├── ogc-api/
│   ├── endpoint.ts
│   ├── model.ts
│   ├── link-utils.ts
│   └── edr/
│       ├── url_builder.ts
│       └── helpers.ts
├── shared/
│   ├── models.ts         # Shared types
│   ├── http-utils.ts    # HTTP utilities
│   ├── xml-utils.ts     # XML parsing
│   ├── cache.ts         # Caching
│   └── errors.ts        # Error handling
└── worker/
    ├── worker.ts         # Web Worker handlers
    └── index.ts          # Worker API
```

**Pattern Requirements for CSAPI:**

```
src/csapi/
├── endpoint.ts           # CSAPIEndpoint class
├── conformance.ts        # Parse /conformance
├── collections.ts        # Parse /collections
├── model.ts             # All TypeScript types
├── url.ts               # URL builders
├── formats/
│   ├── geojson.ts       # GeoJSON parser
│   ├── sensorml.ts      # SensorML parser
│   ├── swe-common.ts    # SWE Common parser
│   ├── validator.ts     # Validation
│   └── detector.ts      # Format detection
├── resources/
│   ├── systems.ts       # System operations
│   ├── deployments.ts   # Deployment operations
│   ├── datastreams.ts   # DataStream operations
│   └── observations.ts  # Observation operations
└── endpoint.spec.ts     # Tests
```

### 3.2 Module Exports

**Each module has clear responsibilities:**

```typescript
// capabilities.ts - Parse metadata
export function readInfoFromCapabilities(doc): GenericEndpointInfo {}
export function readLayersFromCapabilities(doc): Layer[] {}
export function readVersionFromCapabilities(doc): Version {}

// url.ts - Build request URLs
export function generateGetMapUrl(...params): string {}
export function generateGetFeatureInfoUrl(...params): string {}

// model.ts - Type definitions
export interface Layer {}
export interface LayerFull extends Layer {}
export type Version = '1.0.0' | '1.1.0';

// endpoint.ts - Main API
export default class Endpoint {
  constructor(url: string) {}
  isReady(): Promise<this> {}
  getServiceInfo(): GenericEndpointInfo {}
}
```

---

## 4. Quality Standards

### 4.1 Testing Requirements

**All implementations have comprehensive tests:**

```typescript
// endpoint.spec.ts pattern
describe('WmsEndpoint', () => {
  let endpoint: WmsEndpoint;

  beforeEach(() => {
    globalThis.fetchResponseFactory = () => capabilitiesXml;
    endpoint = new WmsEndpoint('https://my.server.org/wms');
  });

  describe('#getVersion', () => {
    it('returns the correct version', async () => {
      await endpoint.isReady();
      expect(endpoint.getVersion()).toBe('1.3.0');
    });
  });

  describe('#getServiceInfo', () => {
    it('reads service metadata', async () => {
      await endpoint.isReady();
      const info = endpoint.getServiceInfo();
      expect(info.title).toBe('Test WMS Service');
      expect(info.keywords).toContain('Test');
    });
  });

  describe('#getLayers', () => {
    it('returns layer tree', async () => {
      await endpoint.isReady();
      const layers = endpoint.getLayers();
      expect(layers.length).toBeGreaterThan(0);
    });
  });
});

// capabilities.spec.ts pattern
describe('readInfoFromCapabilities', () => {
  it('parses service info correctly', () => {
    const doc = parseXmlString(capabilitiesXml);
    const info = readInfoFromCapabilities(doc);
    expect(info.title).toBe('Expected Title');
  });
});
```

**Pattern Requirements for CSAPI:**

- Unit tests for each module (conformance, collections, formats, resources)
- Integration tests with fixtures (real server responses)
- Format parser tests (SensorML, SWE Common, GeoJSON)
- Validation tests (pre-request, post-response)
- URL builder tests (parameter encoding, query construction)
- Target: 90%+ code coverage

### 4.2 Documentation Requirements

**JSDoc comments on all public APIs:**

```typescript
/**
 * Represents a WMS endpoint advertising several layers arranged in a tree structure.
 */
export default class WmsEndpoint {
  /**
   * @param url WMS endpoint url; can contain any query parameters, these will be used to
   *   initialize the endpoint
   */
  constructor(url: string) {}

  /**
   * Resolves when the endpoint is ready to use. Returns the same endpoint object for convenience.
   * @throws {EndpointError}
   */
  isReady(): Promise<WmsEndpoint> {}

  /**
   * Returns an array of layers, same as WmsEndpoint.getLayers(), but flattened
   */
  getFlattenedLayers(): WmsLayerSummary[] {}

  /**
   * Returns a URL that can be used to query an image from one or several layers
   * @param layers List of layers to render
   * @param {Object} options
   * @param {number} options.widthPx
   * @param {number} options.heightPx
   * @param {CrsCode} options.crs Coordinate reference system to use for the image
   * @param {BoundingBox} options.extent Expressed in the requested CRS
   * @param {MimeType} options.outputFormat
   * @param {string} [options.styles] List of styles to use, one for each layer requested
   */
  getMapUrl(layers: string[], options: GetMapOptions): string {}
}
```

**Pattern Requirements for CSAPI:**

- JSDoc on all exported classes, methods, types
- Parameter descriptions with types
- Return value descriptions
- Throws declarations for errors
- Examples in doc comments for complex APIs
- README with usage examples

### 4.3 Error Handling

**Consistent error handling patterns:**

```typescript
// shared/errors.ts
export class EndpointError extends Error {
  constructor(message: string, public cause?: Error) {
    super(message);
    this.name = 'EndpointError';
  }
}

// Usage in endpoint
async isReady(): Promise<this> {
  try {
    await this._capabilitiesPromise;
    return this;
  } catch (error) {
    throw new EndpointError(
      `Failed to initialize endpoint: ${this._capabilitiesUrl}`,
      error
    );
  }
}

// XML validation
export function check(xmlDoc: XmlDocument, url: string): XmlDocument {
  const rootEl = getRootElement(xmlDoc);
  if (rootEl.name === 'ServiceExceptionReport' ||
      rootEl.name === 'ExceptionReport') {
    const exception = getElementText(rootEl);
    throw new Error(`Service exception: ${exception}`);
  }
  return xmlDoc;
}
```

**Pattern Requirements for CSAPI:**

- Custom error types: `CSAPIError`, `FormatParseError`, `ValidationError`
- Include original error as cause
- Include request context (URL, resource type)
- Parse OGC Exception Reports
- Detailed error messages with actionable guidance

---

## 5. Performance Expectations

### 5.1 Caching Strategy

**All implementations use caching:**

```typescript
// shared/cache.ts
export function useCache<T>(
  factory: () => Promise<T>,
  ...cacheKey: string[]
): Promise<T> {
  const key = cacheKey.join('::');
  if (cache.has(key)) {
    return cache.get(key) as Promise<T>;
  }
  const promise = factory();
  cache.set(key, promise);
  return promise;
}

// Usage
this._capabilitiesPromise = useCache(
  () => parseWmsCapabilities(this._capabilitiesUrl),
  'WMS',
  'CAPABILITIES',
  this._capabilitiesUrl
);
```

**Pattern Requirements for CSAPI:**

- Cache conformance responses
- Cache collection metadata
- Cache format detection results
- Cache parsed schemas (DataStream schemas)
- Provide cache invalidation options
- Document cache behavior

### 5.2 Web Worker for Heavy Parsing

**XML/JSON parsing offloaded to worker:**

```typescript
// Capabilities parsing in worker (not main thread)
export function parseWmsCapabilities(url: string): Promise<ParsedCapabilities> {
  if (isWorkerAvailable()) {
    return sendMessageToWorker('parseWmsCapabilities', { url });
  } else {
    return parseWmsCapabilitiesFallback(url);
  }
}
```

**Pattern Requirements for CSAPI:**

- Parse SensorML in worker
- Parse SWE Common in worker
- Parse large observation collections in worker
- Format validation in worker
- Support fallback mode for environments without workers

### 5.3 Bundle Size Considerations

**Library must be tree-shakeable:**

```typescript
// Good - individual exports
export { default as WfsEndpoint } from './wfs/endpoint.js';
export { default as WmsEndpoint } from './wms/endpoint.js';

// User imports only what they need
import { CSAPIEndpoint } from '@camptocamp/ogc-client';
// WFS, WMS code not included in bundle

// Bad - barrel exports that include everything
export * from './wfs';
export * from './wms';
```

**Pattern Requirements for CSAPI:**

- Individual module exports (not barrel exports)
- Lazy load format parsers when needed
- Tree-shakeable utility functions
- Minimize external dependencies
- Target: <50KB gzipped for core, <100KB with all formats

---

## 6. Browser/Node.js Compatibility

### 6.1 Dual Package Support

**Library works in browser and Node.js:**

```json
// package.json
{
  "exports": {
    ".": {
      "import": "./dist/index.js",
      "types": "./dist/index.d.ts"
    },
    "./worker": {
      "import": "./dist/worker/index.js",
      "types": "./dist/worker/index.d.ts"
    }
  },
  "type": "module",
  "module": "./dist/index.js",
  "types": "./dist/index.d.ts"
}

// src-node/index.ts - Node.js specific exports
export * from '../src/index.js';
// Node-specific overrides if needed
```

**Pattern Requirements for CSAPI:**

- ES modules (no CommonJS)
- Works in browser (fetch API)
- Works in Node.js (node-fetch polyfill if needed)
- No Node.js-specific APIs in browser code
- Test both environments

### 6.2 Fetch Options

**Configurable HTTP requests:**

```typescript
// shared/models.ts
export interface FetchOptions {
  headers?: Record<string, string>;
  credentials?: RequestCredentials;
  mode?: RequestMode;
}

// shared/http-utils.ts
let globalFetchOptions: FetchOptions = {};

export function setFetchOptions(options: FetchOptions) {
  globalFetchOptions = options;
}

export function queryXmlDocument(url: string): Promise<XmlDocument> {
  return fetch(url, globalFetchOptions)
    .then((resp) => resp.text())
    .then((text) => parseXmlString(text));
}
```

**Pattern Requirements for CSAPI:**

- Support custom headers (Authorization, etc.)
- Support CORS mode configuration
- Support credentials mode
- Provide `setFetchOptions()` for global config
- Provide per-request options override

---

## 7. Upstream Expectations Summary

### 7.1 Must-Have Requirements

**Non-negotiable requirements for PR acceptance:**

1. **Endpoint Class Pattern**

   - `CSAPIEndpoint` class with async initialization
   - `isReady()` returns Promise
   - Consistent with WFS/WMS/WMTS pattern

2. **TypeScript Types**

   - Export all types from `src/csapi/model.ts`
   - Use shared types (`BoundingBox`, `CrsCode`, `MimeType`)
   - Comprehensive type coverage

3. **Web Worker Support**

   - Register handlers in `worker/worker.ts`
   - Export functions from `worker/index.ts`
   - Support fallback mode

4. **Testing**

   - Unit tests for all modules
   - Integration tests with fixtures
   - 90%+ code coverage

5. **Documentation**

   - JSDoc on all public APIs
   - README with examples
   - Type documentation

6. **Error Handling**

   - Custom error types
   - Parse OGC exceptions
   - Detailed error messages

7. **Caching**

   - Use `useCache()` utility
   - Cache conformance/collections
   - Cache parsed responses

8. **Browser/Node.js Support**
   - ES modules
   - Works in both environments
   - Configurable fetch options

### 7.2 Nice-to-Have Features

**Not required but appreciated:**

1. **Performance Optimizations**

   - Lazy loading
   - Streaming responses
   - Incremental parsing

2. **Developer Experience**

   - Fluent API
   - Helper methods
   - TypeScript inference

3. **Extensibility**
   - Plugin architecture for formats
   - Custom validators
   - Event hooks

### 7.3 Out of Scope

**Explicitly not expected:**

1. **UI Components**

   - No React/Vue/Angular components
   - Pure TypeScript library only

2. **Data Visualization**

   - No charting/graphing
   - No map rendering
   - Leave to users

3. **Storage/Persistence**

   - No IndexedDB/LocalStorage
   - Caching only (in-memory)

4. **Server-Side Logic**
   - No server implementation
   - Client library only

---

## 8. Format Abstraction Alignment

### 8.1 Existing Format Handling Examples

**WFS handles GML parsing:**

```typescript
// wfs/featureprops.ts
export function parseFeatureProps(
  featureCollection: FeatureCollection,
  featureType: WfsFeatureTypeFull
): WfsFeatureWithProps[] {
  return featureCollection.features.map((feature) => ({
    id: feature.id,
    geometry: feature.geometry,
    properties: extractProperties(feature.properties, featureType.properties),
  }));
}

// Extracts typed properties from GML
function extractProperties(
  rawProps: Record<string, unknown>,
  schema: WfsFeatureTypePropsDetails
): Record<string, unknown> {
  // Parse based on schema
  // Convert GML types to JavaScript types
}
```

**WMTS handles TileMatrix calculations:**

```typescript
// wmts/ol-tilegrid.ts
export function buildOpenLayersTileGrid(matrixSet: WmtsMatrixSet): TileGrid {
  // Complex calculations for tile matrices
  // Converts WMTS spec to OpenLayers format
}
```

**OGC API EDR handles WKT parsing:**

```typescript
// ogc-api/edr/url_builder.ts
export default class EDRQueryBuilder {
  buildPositionDownloadUrl(
    coords: WellKnownTextString, // e.g., "POINT(lon lat)"
    optional_params: optionalPositionParams = {}
  ): string {
    // Parses WKT, validates, builds URL
  }
}
```

**Pattern:** Format-specific parsing IS within scope when format is core to the standard.

### 8.2 CSAPI Format Abstraction Justification

**CSAPI format abstraction aligns with existing patterns:**

1. **WFS parses GML** → CSAPI parses SensorML

   - Both are XML-based OGC formats
   - Both require schema interpretation
   - Both convert to canonical models

2. **WMTS handles tile matrices** → CSAPI handles SWE Common components

   - Both require complex structure parsing
   - Both provide abstraction over spec complexity
   - Both enable user-friendly API

3. **EDR handles WKT** → CSAPI handles position formats (Vector, DataRecord, Pose)
   - Both parse domain-specific formats
   - Both validate structure
   - Both convert to common representation

**Conclusion:** CSAPI format abstraction (SensorML, SWE Common, GeoJSON) is consistent with upstream patterns. Upstream expects format handling when it's core to the standard.

---

## 9. CSAPI Implementation Checklist

### 9.1 Core Requirements

- [ ] `CSAPIEndpoint` class following endpoint pattern
- [ ] Parse `/` landing page for service info
- [ ] Parse `/conformance` for capability detection
- [ ] Parse `/collections` for resource catalogs
- [ ] Implement `isReady()` async initialization
- [ ] Implement `getServiceInfo()` metadata getter
- [ ] Implement resource getters (systems, deployments, etc.)
- [ ] URL builders for all operations
- [ ] TypeScript types for all entities
- [ ] Export all types from `src/csapi/model.ts`
- [ ] Re-export from `src/index.ts`

### 9.2 Format Abstraction

- [ ] GeoJSON parser (all geometry types)
- [ ] SensorML parser (all process types, all versions)
- [ ] SWE Common parser (all component types, all encodings)
- [ ] Format detector (Content-Type + body + context)
- [ ] Format validator (pre-request, post-response)
- [ ] Format registry (plugin architecture)
- [ ] Canonical model conversion (format → System/Deployment/etc)
- [ ] Format serialization (canonical → format for requests)

### 9.3 Web Worker

- [ ] Register handlers in `worker/worker.ts`
- [ ] Export functions from `worker/index.ts`
- [ ] Parse conformance in worker
- [ ] Parse collections in worker
- [ ] Parse SensorML in worker
- [ ] Parse SWE Common in worker
- [ ] Support fallback mode (no worker)

### 9.4 Testing

- [ ] Unit tests for conformance parsing
- [ ] Unit tests for collections parsing
- [ ] Unit tests for format detection
- [ ] Unit tests for GeoJSON parser
- [ ] Unit tests for SensorML parser (all types, all versions)
- [ ] Unit tests for SWE Common parser (all components, all encodings)
- [ ] Unit tests for validation (structural + semantic)
- [ ] Unit tests for URL builders
- [ ] Integration tests with fixtures (real server responses)
- [ ] Integration tests for each resource type
- [ ] 90%+ code coverage

### 9.5 Documentation

- [ ] JSDoc on `CSAPIEndpoint` class
- [ ] JSDoc on all public methods
- [ ] JSDoc on all exported types
- [ ] README with installation instructions
- [ ] README with basic usage examples
- [ ] README with advanced usage (validation, formats, queries)
- [ ] Type documentation (TSDoc)

### 9.6 Quality

- [ ] Custom error types (`CSAPIError`, `FormatParseError`, `ValidationError`)
- [ ] Parse OGC Exception Reports
- [ ] Detailed error messages with JSON paths and suggestions
- [ ] Use `useCache()` for conformance/collections
- [ ] Cache parsed schemas
- [ ] Configurable fetch options (`setFetchOptions()`)
- [ ] Browser support (fetch API)
- [ ] Node.js support (polyfills if needed)
- [ ] ES modules (no CommonJS)
- [ ] Tree-shakeable exports
- [ ] Bundle size target: <100KB with all formats

### 9.7 Patterns Compliance

- [ ] Follows WFS/WMS/WMTS endpoint pattern
- [ ] Uses shared types (`BoundingBox`, `CrsCode`, `MimeType`)
- [ ] Uses shared utilities (`http-utils`, `cache`, `errors`)
- [ ] Consistent naming conventions
- [ ] Consistent file structure
- [ ] Consistent code style (Prettier, ESLint)

---

## 10. Conclusion

**Upstream Expectations:** camptocamp/ogc-client expects CSAPI to follow established patterns:

- Endpoint class with async initialization
- Capabilities/metadata parsing
- URL builders with parameter encoding
- TypeScript types for all entities
- Web Worker support for parsing
- Comprehensive testing (90%+ coverage)
- JSDoc documentation
- Browser/Node.js compatibility

**Format Abstraction:** CSAPI's comprehensive format abstraction (SensorML, SWE Common, GeoJSON parsing) **aligns perfectly** with existing upstream patterns:

- WFS parses GML (XML-based OGC format)
- WMTS handles tile matrices (complex spec structures)
- EDR handles WKT (domain-specific format)
- CSAPI handles SensorML/SWE Common (OGC sensor formats)

**Conclusion:** CSAPI implementation plan (Section 17 recommendations) is **fully compatible** with upstream expectations. Format abstraction is not only acceptable but **expected** when formats are core to the standard (as they are in CSAPI spec).

**Next Step:** Define MVP vs full feature set (Section 19) based on upstream patterns and CSAPI requirements.

---

**End of Upstream Expectations Analysis**
