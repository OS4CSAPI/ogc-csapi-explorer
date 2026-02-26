# CSAPI Previous Iteration Gap Analysis

**Purpose:** Identify gaps, errors, and lessons from the first implementation attempt to avoid repeating mistakes in v2.

**Context:** First iteration (OS4CSAPI/ogc-client-CSAPI repository) had scope issues that led to rejection. This analysis ensures v2 correctly defines "what should be included vs excluded."

**Date:** 2026-01-31

---

## Executive Summary

**Key Finding:** The first iteration **incompletely implemented format parsing capabilities** that are core to CSAPI client library value proposition. The library must provide **format abstraction** so users work with canonical data models, not raw format structures.

**Primary Issue:** Implemented partial SensorML parsing (~1,500+ lines) that covered common cases but lacked comprehensive format support, extensibility, and proper error handling. Format parsing was present but not done well enough.

**Recommendation:** v2 should provide **comprehensive format abstraction layer** with complete parsers for all CSAPI-defined formats (GeoJSON, SensorML JSON, SWE Common), robust validation, automatic format detection, and extensible architecture for future formats.

---

## 1. What Was Implemented (First Iteration)

### 1.1 Core Implementation Scope

**Implemented Components:**

1. **SensorML Parsers** (~1,500+ lines)

   - SystemParser with PhysicalSystem/PhysicalComponent parsing
   - DeploymentParser with Deployment-specific handling
   - ProcedureParser with SimpleProcess/AggregateProcess support
   - PropertyParser with DerivedProperty extraction
   - Position extraction from multiple SWE Common types (Vector, DataRecord, Pose)
   - Geometry conversion from SensorML position to GeoJSON
   - Common property extraction (identifiers, classifiers, capabilities, etc.)

2. **SWE Common Parsers** (~800+ lines)

   - DataStream schema parsing
   - Observation parsing (scalar, vector, DataRecord)
   - Command parsing
   - SWE component extraction

3. **Format Detection** (~200+ lines)

   - Auto-detect GeoJSON vs SensorML vs SWE Common
   - Content-Type header analysis
   - Body structure inspection
   - Confidence scoring

4. **Validation Framework** (~400+ lines)

   - SensorML validation with Ajv
   - Required property checking
   - Type validation
   - GeoJSON structure validation
   - Strict vs non-strict modes

5. **Type Definitions** (~1,000+ lines)
   - Complete SensorML type hierarchy
   - DescribedObject interfaces
   - Position types (Vector, DataRecord, Pose, Text)
   - SWE Common component types
   - Capability/Characteristic interfaces

**Total Code:** ~3,900+ lines of parsing/validation logic

### 1.2 Resource Coverage

**Part 1 Resources:**

- ✅ Systems - Full parser with SensorML support
- ✅ Deployments - Full parser with location extraction
- ✅ Procedures - Full parser with process types
- ✅ Sampling Features - GeoJSON only (correct—no SensorML format)
- ✅ Properties - Full parser with DerivedProperty support

**Part 2 Resources:**

- ✅ DataStreams - GeoJSON + SWE Common schema parsing
- ✅ Observations - JSON + SWE Common parsing
- ✅ ControlStreams - GeoJSON only
- ✅ Commands - JSON + SWE Common parsing

**Part 3 Resources:**

- ❌ Not implemented (streaming deferred)

---

## 2. What Was Incompletely Implemented

### 2.1 SensorML Parsing (PRIMARY ISSUE)

**Problem:** Client library implemented **partial SensorML parsing** without comprehensive coverage, proper extensibility, or robust error handling.

**What Was Implemented:**

```typescript
// base.ts - SystemParser.parseSensorML() method
parseSensorML(data: Record<string, unknown>): SystemFeature {
  const sml = data as unknown as SensorMLProcess;

  // Validate it's a physical system/component
  if (sml.type !== 'PhysicalSystem' && sml.type !== 'PhysicalComponent') {
    throw new CSAPIParseError(
      `Expected PhysicalSystem or PhysicalComponent, got ${sml.type}`
    );
  }

  // Extract geometry from position
  const geometry =
    'position' in sml ? extractGeometry(sml.position as Position) : undefined;

  // Build properties from SensorML metadata
  const properties: Record<string, unknown> = {
    ...extractCommonProperties(sml),
    featureType: 'System',
    systemType: sml.type === 'PhysicalSystem' ? 'platform' : 'sensor',
  };

  // Add inputs/outputs/parameters if present
  if ('inputs' in sml && sml.inputs) properties.inputs = sml.inputs;
  if ('outputs' in sml && sml.outputs) properties.outputs = sml.outputs;
  if ('parameters' in sml && sml.parameters)
    properties.parameters = sml.parameters;

  // Add components for systems
  if (
    sml.type === 'PhysicalSystem' &&
    'components' in sml &&
    sml.components
  ) {
    properties.components = sml.components;
  }

  return {
    type: 'Feature',
    id: sml.id || sml.uniqueId,
    geometry: geometry || null,
    properties,
  } as unknown as SystemFeature;
}

// Position extraction with multiple format support
function extractGeometry(position?: Position): Geometry | undefined {
  if (!position) return undefined;

  // Handle Point geometry
  if (position.type === 'Point') {
    return position as Geometry;
  }

  // Handle Vector with coordinates array
  if (position.type === 'Vector' && 'coordinates' in position) {
    const coords = (position as any).coordinates;
    if (Array.isArray(coords) && coords.length >= 2) {
      return {
        type: 'Point',
        coordinates: [coords[0], coords[1], coords[2] || 0],
      };
    }
  }

  // Handle DataRecord with lat/lon fields
  if (position.type === 'DataRecord' && 'fields' in position) {
    const fields = (position as any).fields;
    const lat = fields.find((f: any) => f.name === 'lat' || f.name === 'latitude')?.value;
    const lon = fields.find((f: any) => f.name === 'lon' || f.name === 'longitude')?.value;
    const alt = fields.find((f: any) => f.name === 'h' || f.name === 'altitude')?.value || 0;

    if (lat !== undefined && lon !== undefined) {
      return {
        type: 'Point',
        coordinates: [lon, lat, alt],
      };
    }
  }

  // Handle Pose with position object
  if ('position' in position) {
    const pos = (position as any).position;
    if (pos.lat !== undefined && pos.lon !== undefined) {
      return {
        type: 'Point',
        coordinates: [pos.lon, pos.lat, pos.h || 0],
      };
    }
  }

  return undefined;
}

// Common properties extraction
function extractCommonProperties(
  sml: DescribedObject
): Record<string, unknown> {
  const props: Record<string, unknown> = {};

  if (sml.id) props.id = sml.id;
  if (sml.uniqueId) props.uniqueId = sml.uniqueId;
  if (sml.label) props.name = sml.label;
  if (sml.description) props.description = sml.description;
  if (sml.lang) props.language = sml.lang;

  // Extract keywords
  if (sml.keywords) {
    if (Array.isArray(sml.keywords) && sml.keywords.length > 0) {
      if (typeof sml.keywords[0] === 'string') {
        props.keywords = sml.keywords;
      } else {
        props.keywords = (sml.keywords as Keyword[]).map(k => k.value || k.label);
      }
    }
  }

  // Extract identifiers
  if (sml.identifiers) props.identifiers = sml.identifiers;

  // Extract classifiers
  if (sml.classifiers) props.classifiers = sml.classifiers;

  // Extract validTime
  if (sml.validTime) props.validTime = sml.validTime;

  // Extract contacts
  if (sml.contacts) props.contacts = sml.contacts;

  // Extract documents
  if (sml.documents) props.documents = sml.documents;

  // Extract constraints
  if (sml.securityConstraints) props.securityConstraints = sml.securityConstraints;
  if (sml.legalConstraints) props.legalConstraints = sml.legalConstraints;

  // Extract capabilities
  if (sml.capabilities) props.capabilities = sml.capabilities;

  // Extract characteristics
  if (sml.characteristics) props.characteristics = sml.characteristics;

  return props;
}
```

**Why This Implementation Was Insufficient:**

1. **Incomplete Coverage:** Even with 1,500 lines, implementation covered only common cases:

   - No support for AggregateProcess traversal (nested components)
   - No connection/link resolution between processes
   - No configuration mode handling (deployment contexts)
   - No history parsing (configuration changes over time)
   - Missing many SensorML 3.0 elements (modes, featureOfInterest, etc.)
   - No support for TypedProcess extensions
   - Limited handling of capabilities/characteristics structures

2. **Poor Error Handling:** Parser threw generic errors without specific guidance:

   - "Expected PhysicalSystem" - but why did it get something else?
   - No validation of position coordinate systems
   - No handling of malformed SensorML from servers
   - No graceful degradation for unknown elements

3. **No Format Versioning:** SensorML has multiple versions (2.0, 3.0) with different schemas:

   - No version detection
   - No version-specific parsing
   - Would break when servers update SensorML versions

4. **Rigid Architecture:** Hard to extend for new SensorML elements:

   - No plugin system for custom parsers
   - No way to handle server-specific extensions
   - Tightly coupled to specific SensorML structure

5. **Insufficient Testing:** 1,200+ lines of tests but missing edge cases:
   - No tests for malformed SensorML
   - No tests for unknown elements
   - No tests for version differences
   - No tests for complex nested structures

**What Should Have Been Done:**

```typescript
// CORRECT APPROACH - Comprehensive format abstraction
export class SystemEndpoint {
  constructor(
    private http: HttpClient,
    private formatRegistry: FormatRegistry
  ) {
    // Register parsers for all supported formats
    this.formatRegistry.register('application/geo+json', new GeoJSONParser());
    this.formatRegistry.register('application/sml+json', new SensorMLParser());
  }

  async getSystem(id: string, options?: GetSystemOptions): Promise<System> {
    const url = this.buildUrl(`/systems/${id}`, options);
    const response = await this.http.get(url);

    // Automatic format detection and parsing
    const contentType = response.headers['content-type'];
    const parser = this.formatRegistry.getParser(contentType);

    if (!parser) {
      throw new UnsupportedFormatError(
        `No parser registered for format: ${contentType}`
      );
    }

    try {
      // Parse to canonical System model
      return parser.parse(response.data);
    } catch (error) {
      throw new FormatParseError(`Failed to parse ${contentType} response`, {
        cause: error,
        rawData: response.data,
      });
    }
  }
}

// Extensible parser architecture
interface FormatParser<T> {
  parse(data: unknown): T;
  validate(data: unknown): ValidationResult;
  serialize(obj: T): unknown;
}

// Comprehensive SensorML parser with full coverage
class SensorMLParser implements FormatParser<System> {
  parse(data: unknown): System {
    const sml = this.validate(data);

    // Handle all SensorML types
    switch (sml.type) {
      case 'PhysicalSystem':
        return this.parsePhysicalSystem(sml);
      case 'PhysicalComponent':
        return this.parsePhysicalComponent(sml);
      case 'AggregateProcess':
        return this.parseAggregateProcess(sml);
      default:
        throw new Error(`Unknown SensorML type: ${sml.type}`);
    }
  }

  private parsePhysicalSystem(sml: PhysicalSystem): System {
    return {
      id: sml.id || sml.uniqueId,
      type: 'Feature',
      geometry: this.extractGeometry(sml.position),
      properties: {
        featureType: 'System',
        uid: sml.uniqueId,
        name: sml.label,
        description: sml.description,
        // Extract ALL properties, not just common ones
        validTime: sml.validTime,
        contacts: sml.contacts,
        documentation: sml.documentation,
        capabilities: this.parseCapabilities(sml.capabilities),
        characteristics: this.parseCharacteristics(sml.characteristics),
        // Handle components recursively
        components: sml.components?.map((c) => this.parse(c)),
        // Handle connections
        connections: this.parseConnections(sml.connections),
        // Handle modes
        modes: sml.modes?.map((m) => this.parseMode(m)),
      },
      links: this.extractLinks(sml),
    };
  }

  private extractGeometry(position?: Position): Geometry | null {
    if (!position) return null;

    // Handle ALL SWE Common position types
    switch (position.type) {
      case 'Point':
        return this.parsePointGeometry(position);
      case 'Vector':
        return this.parseVectorGeometry(position);
      case 'DataRecord':
        return this.parseDataRecordGeometry(position);
      case 'Pose':
        return this.parsePoseGeometry(position);
      case 'Text':
        return this.parseWKTGeometry(position);
      default:
        // Graceful degradation for unknown types
        console.warn(`Unknown position type: ${position.type}`);
        return null;
    }
  }

  validate(data: unknown): SensorMLProcess {
    // Comprehensive validation with detailed error messages
    const result = validateSensorML(data);
    if (!result.valid) {
      throw new SensorMLValidationError('Invalid SensorML structure', {
        errors: result.errors,
        warnings: result.warnings,
      });
    }
    return data as SensorMLProcess;
  }
}

// Users work with canonical System model, not raw formats
const client = new CSAPIClient('https://server.com/api');

// Format is transparent - user gets System regardless of server format
const system = await client.systems.get('system-1');
console.log(system.properties.name); // Works whether GeoJSON or SensorML

// Access parsed components directly
if (system.properties.components) {
  system.properties.components.forEach((comp) => {
    console.log(comp.properties.name, comp.geometry);
  });
}

// Library handles format complexity internally
```

### 2.2 SWE Common Parsing

**Problem:** Implemented partial SWE Common parsing for DataStream schemas and Observations without comprehensive component coverage.

**What Was Implemented:**

```typescript
// resources.ts - DatastreamParser.parseSWE()
parseSWE(data: Record<string, unknown>): DatastreamFeature {
  const sweDS = data as any;

  // Extract schema from elementType
  const schema = sweDS.elementType?.component;

  return {
    type: 'Feature',
    id: sweDS.id,
    geometry: null,
    properties: {
      featureType: 'Datastream',
      uid: sweDS.definition,
      name: sweDS.label,
      description: sweDS.description,
      schema: schema, // Embedded schema - not parsed
    },
  } as DatastreamFeature;
}

// ObservationParser with result extraction
parseSWE(data: Record<string, unknown>): Record<string, unknown> {
  // Parse SWE observation
  return data; // Just returns raw data
}
```

**What Was Missing:**

1. **Incomplete Component Coverage:** SWE Common has 30+ component types but implementation only handled DataRecord/DataArray:

   - Missing: Quantity, Count, Boolean, Text, Category, Time
   - Missing: Vector, Matrix, DataChoice, Geometry
   - Missing: AbstractSimpleComponent extensions
   - No recursive component parsing (DataRecord contains DataRecords)

2. **No Encoding Support:** SWE Common has 3 encodings but implementation only handled JSON partially:

   - JSON encoding: partial support
   - Text/CSV encoding: not implemented
   - Binary encoding: not implemented
   - No encoding detection/selection

3. **No Schema Interpretation:** DataStream schemas define observation structure but parser didn't use them:

   - Schema embedded but not parsed
   - No validation of observations against schema
   - No automatic result decoding based on schema
   - No UoM extraction from schema

4. **No Result Decoding:** Observations have complex result structures:
   - Scalar results (single value) - handled
   - Vector results (array) - partial
   - DataRecord results (object) - not parsed
   - DataArray results (time series) - not parsed

**What Should Have Been Done:**

```typescript
// Comprehensive SWE Common parser
class SWECommonParser {
  parseComponent(component: SWEComponent): ParsedComponent {
    switch (component.type) {
      case 'Quantity':
        return this.parseQuantity(component);
      case 'Count':
        return this.parseCount(component);
      case 'Boolean':
        return this.parseBoolean(component);
      case 'Text':
        return this.parseText(component);
      case 'Category':
        return this.parseCategory(component);
      case 'Time':
        return this.parseTime(component);
      case 'DataRecord':
        return this.parseDataRecord(component);
      case 'DataArray':
        return this.parseDataArray(component);
      case 'Vector':
        return this.parseVector(component);
      case 'Matrix':
        return this.parseMatrix(component);
      case 'DataChoice':
        return this.parseDataChoice(component);
      case 'Geometry':
        return this.parseGeometry(component);
      default:
        throw new Error(`Unknown SWE component type: ${component.type}`);
    }
  }

  // Use schema to decode observation results
  decodeObservationResult(
    result: unknown,
    schema: SWEComponent,
    encoding?: SWEEncoding
  ): DecodedResult {
    if (!encoding || encoding.type === 'JSON') {
      return this.decodeJSONResult(result, schema);
    } else if (encoding.type === 'Text') {
      return this.decodeTextResult(result as string, schema, encoding);
    } else if (encoding.type === 'Binary') {
      return this.decodeBinaryResult(result as ArrayBuffer, schema, encoding);
    }
    throw new Error(`Unknown encoding type: ${encoding?.type}`);
  }
}

// DataStream parser uses schema
class DatastreamParser {
  parseSWE(data: Record<string, unknown>): DatastreamFeature {
    const sweDS = data as SWEDataStream;

    // Parse schema component fully
    const schema = sweDS.elementType?.component
      ? this.sweParser.parseComponent(sweDS.elementType.component)
      : undefined;

    return {
      type: 'Feature',
      id: sweDS.id,
      geometry: null,
      properties: {
        featureType: 'Datastream',
        uid: sweDS.definition,
        name: sweDS.label,
        description: sweDS.description,
        schema: schema, // Fully parsed schema
        encoding: sweDS.encoding, // Include encoding info
      },
    };
  }
}

// Observation parser uses schema to decode results
class ObservationParser {
  parseObservation(data: unknown, datastream: Datastream): Observation {
    const obs = data as RawObservation;

    // Decode result using datastream schema
    const decodedResult = this.sweParser.decodeObservationResult(
      obs.result,
      datastream.properties.schema,
      datastream.properties.encoding
    );

    return {
      id: obs.id,
      phenomenonTime: obs.phenomenonTime,
      resultTime: obs.resultTime,
      result: decodedResult, // Structured, typed result
    };
  }
}
```

### 2.3 Format Validation

**Problem:** Implemented basic validation with Ajv but missing comprehensive format-specific validation and detailed error messages.

**What Was Implemented:**

```typescript
// validation/sensorml-validator.ts
async function validateSensorMLProcess(
  data: SensorMLProcess
): Promise<{ valid: boolean; errors?: string[]; warnings?: string[] }> {
  const ajv = await initializeValidator();

  const errors: string[] = [];
  const warnings: string[] = [];

  // Basic required property checks
  if (!data.type) {
    errors.push('Missing required property: type');
  }

  // Basic valid types check
  const validTypes = [
    'PhysicalSystem',
    'PhysicalComponent',
    'SimpleProcess',
    'AggregateProcess',
    'Deployment',
    'DerivedProperty',
  ];
  if (data.type && !validTypes.includes(data.type)) {
    errors.push(`Invalid type: ${data.type}`);
  }

  // Generic warnings
  if (!data.uniqueId && !data.id) {
    warnings.push('Object should have uniqueId or id for identification');
  }

  return {
    valid: errors.length === 0,
    errors: errors.length > 0 ? errors : undefined,
    warnings: warnings.length > 0 ? warnings : undefined,
  };
}
```

**What Was Missing:**

1. **Incomplete Validation Rules:** Only validated structure, not semantics:

   - No coordinate system validation for positions
   - No UoM code validation
   - No uniqueId URI format validation
   - No validTime range validation
   - No capability/characteristic value validation

2. **Poor Error Messages:** Generic errors without actionable guidance:

   - "Invalid type" - but what types are valid in this context?
   - "Missing required property" - but which properties are required for this operation?
   - No JSON path to error location
   - No suggestions for fixing errors

3. **No Format-Specific Validation:** Different formats have different rules:

   - GeoJSON: strict GeoJSON spec compliance
   - SensorML: version-specific validation (2.0 vs 3.0)
   - SWE Common: component type-specific validation

4. **No Pre-Request Validation:** Should validate before sending to server:
   - Create operations: validate required properties
   - Update operations: validate allowed properties
   - Query parameters: validate value formats

**What Should Have Been Done:**

```typescript
// Comprehensive validation system
class FormatValidator {
  // Validate with detailed, actionable errors
  validate(data: unknown, schema: ValidationSchema): ValidationResult {
    const errors: ValidationError[] = [];
    const warnings: ValidationWarning[] = [];

    // Structural validation
    const structuralErrors = this.validateStructure(data, schema);
    errors.push(...structuralErrors);

    // Semantic validation
    const semanticErrors = this.validateSemantics(data, schema);
    errors.push(...semanticErrors);

    // Format-specific validation
    const formatErrors = this.validateFormat(data, schema);
    errors.push(...formatErrors);

    return {
      valid: errors.length === 0,
      errors: errors.map((e) => ({
        path: e.path, // JSON path to error location
        message: e.message, // Human-readable message
        code: e.code, // Error code for programmatic handling
        expected: e.expected, // What was expected
        actual: e.actual, // What was received
        suggestion: e.suggestion, // How to fix it
      })),
      warnings: warnings.map((w) => ({
        path: w.path,
        message: w.message,
        suggestion: w.suggestion,
      })),
    };
  }

  validateStructure(
    data: unknown,
    schema: ValidationSchema
  ): ValidationError[] {
    // Use JSON Schema validation with detailed errors
    const ajv = new Ajv({ allErrors: true, verbose: true });
    addFormats(ajv);

    const validate = ajv.compile(schema);
    const valid = validate(data);

    if (!valid && validate.errors) {
      return validate.errors.map((err) => ({
        path: err.instancePath,
        message: err.message || 'Validation error',
        code: 'STRUCTURE_ERROR',
        expected: err.params,
        actual: err.data,
        suggestion: this.getSuggestion(err),
      }));
    }

    return [];
  }

  validateSemantics(
    data: unknown,
    schema: ValidationSchema
  ): ValidationError[] {
    const errors: ValidationError[] = [];

    // Validate uniqueId is valid URI
    if (data.uniqueId && !this.isValidURI(data.uniqueId)) {
      errors.push({
        path: '/uniqueId',
        message: 'uniqueId must be a valid URI',
        code: 'INVALID_URI',
        actual: data.uniqueId,
        expected: 'Valid URI format',
        suggestion: 'Use format: http://example.com/systems/system-1',
      });
    }

    // Validate position coordinate system
    if (data.position && data.position.referenceFrame) {
      if (!this.isValidCRS(data.position.referenceFrame)) {
        errors.push({
          path: '/position/referenceFrame',
          message: 'Invalid coordinate reference system',
          code: 'INVALID_CRS',
          actual: data.position.referenceFrame,
          expected: 'EPSG code or OGC CRS URI',
          suggestion: 'Use format: http://www.opengis.net/def/crs/EPSG/0/4326',
        });
      }
    }

    // Validate UoM codes
    if (data.capabilities) {
      data.capabilities.forEach((cap, i) => {
        if (cap.uom && !this.isValidUoM(cap.uom)) {
          errors.push({
            path: `/capabilities/${i}/uom`,
            message: 'Invalid unit of measure code',
            code: 'INVALID_UOM',
            actual: cap.uom,
            expected: 'UCUM code or OGC UoM URI',
            suggestion: 'Use UCUM codes: m, deg, Cel, etc.',
          });
        }
      });
    }

    return errors;
  }
}

// Pre-request validation
class SystemEndpoint {
  async createSystem(system: SystemInput): Promise<System> {
    // Validate before sending to server
    const validation = this.validator.validate(system, CREATE_SYSTEM_SCHEMA);

    if (!validation.valid) {
      throw new ValidationError('Invalid system data', {
        errors: validation.errors,
        warnings: validation.warnings,
      });
    }

    // Log warnings even if valid
    if (validation.warnings && validation.warnings.length > 0) {
      console.warn('System validation warnings:', validation.warnings);
    }

    const response = await this.http.post('/systems', system);
    return this.parseResponse(response);
  }
}
```

### 2.4 Format Detection

**Problem:** Implemented basic format detection but missing version detection, confidence scoring, and fallback strategies.

**What Was Implemented:**

```typescript
// formats.ts
export function detectFormat(
  contentType: string | null,
  data: unknown
): FormatInfo {
  // Check Content-Type header first
  if (contentType) {
    if (contentType.includes('geo+json')) {
      return { format: 'geojson', confidence: 'high', source: 'content-type' };
    }
    if (contentType.includes('sml+json')) {
      return { format: 'sensorml', confidence: 'high', source: 'content-type' };
    }
    if (contentType.includes('swe+json') || contentType.includes('swe+text')) {
      return { format: 'swe', confidence: 'high', source: 'content-type' };
    }
  }

  // Fallback to body inspection
  return detectFormatFromBody(data);
}
```

**What Was Missing:**

1. **No Version Detection:** Formats have versions with different schemas:

   - SensorML 2.0 vs 3.0 (different structure)
   - GeoJSON (RFC 7946) vs legacy GeoJSON
   - SWE Common 2.0 vs 2.1
   - No version-specific parsing

2. **Basic Confidence Scoring:** Only "high", "medium", "low" - not granular:

   - No scoring algorithm
   - No multiple indicator aggregation
   - No confidence threshold handling

3. **No Fallback Strategies:** When detection fails:

   - No graceful degradation
   - No user override mechanism
   - No "try multiple parsers" approach

4. **Limited Body Inspection:** Only checks type field:
   - Doesn't check namespace URIs
   - Doesn't check schema locations
   - Doesn't check encoding properties
   - Could misidentify formats

**What Should Have Been Done:**

```typescript
// Comprehensive format detection system
class FormatDetector {
  detect(
    contentType: string | null,
    data: unknown,
    context?: DetectionContext
  ): FormatDetectionResult {
    const indicators: FormatIndicator[] = [];

    // 1. Check Content-Type header (highest priority)
    if (contentType) {
      const headerIndicator = this.detectFromContentType(contentType);
      if (headerIndicator) {
        indicators.push({
          format: headerIndicator.format,
          version: headerIndicator.version,
          confidence: 0.9, // High confidence from header
          source: 'content-type',
        });
      }
    }

    // 2. Check body structure
    if (data && typeof data === 'object') {
      const bodyIndicators = this.detectFromBody(data);
      indicators.push(...bodyIndicators);
    }

    // 3. Check context (endpoint, file extension, etc.)
    if (context) {
      const contextIndicators = this.detectFromContext(context);
      indicators.push(...contextIndicators);
    }

    // 4. Aggregate indicators with weighted scoring
    const aggregated = this.aggregateIndicators(indicators);

    // 5. Apply confidence threshold
    const bestMatch = aggregated[0];
    if (bestMatch && bestMatch.confidence >= 0.7) {
      return {
        format: bestMatch.format,
        version: bestMatch.version,
        confidence: bestMatch.confidence,
        alternatives: aggregated.slice(1),
      };
    }

    // 6. Fallback to JSON if uncertain
    return {
      format: 'json',
      version: null,
      confidence: 0.5,
      alternatives: aggregated,
    };
  }

  private detectFromContentType(contentType: string): FormatIndicator | null {
    // Parse media type with parameters
    const [type, ...params] = contentType.split(';').map((s) => s.trim());
    const paramMap = new Map(
      params.map((p) => p.split('=').map((s) => s.trim()) as [string, string])
    );

    // GeoJSON detection
    if (type === 'application/geo+json') {
      return {
        format: 'geojson',
        version: paramMap.get('version') || 'rfc7946',
        confidence: 0.95,
        source: 'content-type',
      };
    }

    // SensorML detection with version
    if (type === 'application/sml+json') {
      return {
        format: 'sensorml',
        version: paramMap.get('version') || '3.0',
        confidence: 0.95,
        source: 'content-type',
      };
    }

    // SWE Common detection with version and encoding
    if (type === 'application/swe+json') {
      return {
        format: 'swe-json',
        version: paramMap.get('version') || '2.0',
        confidence: 0.95,
        source: 'content-type',
      };
    }

    return null;
  }

  private detectFromBody(data: object): FormatIndicator[] {
    const indicators: FormatIndicator[] = [];

    // GeoJSON detection
    if (
      'type' in data &&
      ['Feature', 'FeatureCollection'].includes(data.type as string)
    ) {
      indicators.push({
        format: 'geojson',
        version: 'rfc7946',
        confidence: 0.8,
        source: 'body-structure',
      });
    }

    // SensorML detection with version
    const sensorMLTypes = [
      'PhysicalSystem',
      'PhysicalComponent',
      'SimpleProcess',
      'AggregateProcess',
      'Deployment',
      'DerivedProperty',
    ];
    if ('type' in data && sensorMLTypes.includes(data.type as string)) {
      // Check for version indicators
      let version = '3.0'; // Default to latest
      if ('definition' in data) version = '3.0';
      if ('identifier' in data && !('definition' in data)) version = '2.0';

      indicators.push({
        format: 'sensorml',
        version,
        confidence: 0.75,
        source: 'body-structure',
      });
    }

    // SWE Common detection
    const sweTypes = [
      'DataRecord',
      'DataArray',
      'Vector',
      'Matrix',
      'Quantity',
      'Count',
      'Boolean',
      'Text',
      'Category',
      'Time',
    ];
    if ('type' in data && sweTypes.includes(data.type as string)) {
      indicators.push({
        format: 'swe',
        version: '2.0',
        confidence: 0.7,
        source: 'body-structure',
      });
    }

    return indicators;
  }

  private aggregateIndicators(
    indicators: FormatIndicator[]
  ): AggregatedFormat[] {
    // Group by format+version
    const grouped = new Map<string, FormatIndicator[]>();
    indicators.forEach((ind) => {
      const key = `${ind.format}:${ind.version || 'unknown'}`;
      if (!grouped.has(key)) grouped.set(key, []);
      grouped.get(key)!.push(ind);
    });

    // Aggregate confidence scores
    const aggregated = Array.from(grouped.entries()).map(([key, inds]) => {
      // Weighted average of confidence scores
      const totalConfidence = inds.reduce(
        (sum, ind) => sum + ind.confidence,
        0
      );
      const avgConfidence = totalConfidence / inds.length;

      const [format, version] = key.split(':');
      return {
        format,
        version: version === 'unknown' ? null : version,
        confidence: avgConfidence,
        sources: inds.map((i) => i.source),
      };
    });

    // Sort by confidence descending
    return aggregated.sort((a, b) => b.confidence - a.confidence);
  }
}

// Parser uses detection with fallback
class FormatParser {
  parse(response: HttpResponse): ParsedData {
    const detection = this.detector.detect(
      response.headers['content-type'],
      response.data,
      { endpoint: response.url }
    );

    // Try primary format
    try {
      const parser = this.getParser(detection.format, detection.version);
      return parser.parse(response.data);
    } catch (primaryError) {
      // Try alternatives if primary fails
      for (const alt of detection.alternatives || []) {
        if (alt.confidence >= 0.5) {
          try {
            const altParser = this.getParser(alt.format, alt.version);
            return altParser.parse(response.data);
          } catch (altError) {
            // Continue to next alternative
          }
        }
      }

      // No parser succeeded
      throw new FormatDetectionError('Could not determine data format', {
        detection,
        primaryError,
      });
    }
  }
}
```

### 2.5 Collection Parsers

**Problem:** Implemented collection-specific parsers (SystemCollectionParser, DeploymentCollectionParser, etc.) with format-specific handling.

**What Was Implemented:**

```typescript
// base.ts
export class SystemCollectionParser extends CSAPIParser<SystemFeature[]> {
  parseGeoJSON(data: Feature | FeatureCollection): SystemFeature[] {
    if (data.type === 'Feature') {
      return [data as SystemFeature];
    }
    return (data as FeatureCollection).features as SystemFeature[];
  }

  parseSensorML(data: Record<string, unknown>): SystemFeature[] {
    throw new CSAPIParseError(
      'SensorML collection parsing not yet implemented'
    );
  }

  parseSWE(data: Record<string, unknown>): SystemFeature[] {
    throw new CSAPIParseError('SWE format not applicable for System resources');
  }
}

// resources.ts - Generic collection parser
export class CollectionParser<T> extends CSAPIParser<T[]> {
  constructor(private itemParser: CSAPIParser<T>) {
    super();
  }

  parseGeoJSON(data: Feature | FeatureCollection): T[] {
    if (data.type === 'FeatureCollection') {
      return data.features.map((feature) =>
        this.itemParser.parseGeoJSON(feature)
      );
    }
    return [this.itemParser.parseGeoJSON(data)];
  }

  parseSensorML(data: Record<string, unknown>): T[] {
    if (Array.isArray(data)) {
      return data.map((item) => this.itemParser.parseSensorML(item));
    }
    return [this.itemParser.parseSensorML(data)];
  }
}
```

**Why This Is Wrong:**

1. **Unnecessary Abstraction:** Collections are just arrays. No special parser needed—map over items.

2. **Format Mixing:** Collections always use same format (GeoJSON FeatureCollection or JSON array). No need for per-item format detection.

**What Should Have Been Done:**

```typescript
// CORRECT - Simple array handling
async listSystems(options?: QueryParams): Promise<SystemCollection> {
  const response = await this.http.get('/systems', { params: options });

  // Response is FeatureCollection or paginated JSON response
  // No parsing - just return it
  return {
    items: response.data.features || response.data.items,
    links: response.data.links,
    numberMatched: response.data.numberMatched,
  };
}
```

---

## 3. What Was Missing

### 3.1 HTTP Operation Focus

**What Was Missing:** First iteration focused on parsing but missed core HTTP client responsibilities.

**Should Have Implemented:**

1. **URL Building with Query Parameters**

   ```typescript
   // Robust query parameter handling
   buildUrl(path: string, params?: QueryParams): string {
     const url = new URL(path, this.baseUrl);

     // Handle bbox (array → comma-separated)
     if (params?.bbox) {
       url.searchParams.set('bbox', params.bbox.join(','));
     }

     // Handle datetime (Date → ISO 8601)
     if (params?.datetime) {
       url.searchParams.set('datetime', params.datetime.toISOString());
     }

     // Handle id lists (array → comma-separated)
     if (params?.id) {
       url.searchParams.set('id', params.id.join(','));
     }

     // Handle limit/offset
     if (params?.limit) url.searchParams.set('limit', params.limit.toString());
     if (params?.offset) url.searchParams.set('offset', params.offset.toString());

     return url.toString();
   }
   ```

2. **Format Negotiation**

   ```typescript
   async request<T>(
     method: string,
     path: string,
     options?: {
       params?: QueryParams;
       body?: unknown;
       format?: string; // Desired response format
     }
   ): Promise<T> {
     const headers: Record<string, string> = {};

     // Set Accept header for format negotiation
     if (options?.format) {
       headers['Accept'] = options.format;
     }

     // Set Content-Type for request body
     if (options?.body) {
       headers['Content-Type'] = 'application/json';
     }

     const response = await fetch(this.buildUrl(path, options?.params), {
       method,
       headers,
       body: options?.body ? JSON.stringify(options.body) : undefined,
     });

     if (!response.ok) {
       throw new Error(`HTTP ${response.status}: ${await response.text()}`);
     }

     return response.json();
   }
   ```

3. **Link Following**

   ```typescript
   // Follow rel=next links for pagination
   async *listSystemsPaginated(params?: QueryParams): AsyncGenerator<System> {
     let url: string | null = this.buildUrl('/systems', params);

     while (url) {
       const response = await this.http.get(url);
       const collection = response.data as FeatureCollection;

       // Yield all items from this page
       for (const feature of collection.features) {
         yield feature as System;
       }

       // Find next link
       const nextLink = collection.links?.find(l => l.rel === 'next');
       url = nextLink?.href || null;
     }
   }
   ```

4. **Error Handling with OGC Exception Reports**

   ```typescript
   async request<T>(method: string, path: string, options?: RequestOptions): Promise<T> {
     try {
       const response = await fetch(this.buildUrl(path, options?.params), { method });

       if (!response.ok) {
         // Check for OGC Exception Report
         const contentType = response.headers.get('content-type');
         if (contentType?.includes('xml')) {
           const text = await response.text();
           if (text.includes('ExceptionReport') || text.includes('ServiceException')) {
             throw parseOGCException(text);
           }
         }

         throw new Error(`HTTP ${response.status}: ${await response.text()}`);
       }

       return response.json();
     } catch (error) {
       throw new CSAPIError('Request failed', error);
     }
   }
   ```

5. **Conformance-Based Feature Detection**

   ```typescript
   async initialize(): Promise<void> {
     // Fetch conformance classes
     const conformance = await this.http.get('/conformance');
     this.conformanceClasses = new Set(conformance.conformsTo);

     // Detect available resources
     this.capabilities = {
       systems: this.supportsConformance('http://www.opengis.net/spec/ogcapi-connected-systems-1/1.0/conf/system-features'),
       deployments: this.supportsConformance('http://www.opengis.net/spec/ogcapi-connected-systems-1/1.0/conf/deployment-features'),
       datastreams: this.supportsConformance('http://www.opengis.net/spec/ogcapi-connected-systems-2/1.0/conf/datastream-features'),
       // ... etc
     };
   }

   supportsConformance(uri: string): boolean {
     return this.conformanceClasses.has(uri);
   }
   ```

### 3.2 Convenience Methods

**What Was Missing:** Methods that simplify common workflows without over-parsing.

**Should Have Implemented:**

1. **Fluent API for Sub-Resource Navigation**

   ```typescript
   // Chainable resource access
   const datastreams = await client.systems.get('system-1').datastreams.list();

   // Implementation
   class SystemResource {
     constructor(private client: CSAPIClient, private id: string) {}

     get datastreams() {
       return new DataStreamResource(this.client, { system: this.id });
     }

     get deployments() {
       return new DeploymentResource(this.client, { system: this.id });
     }
   }
   ```

2. **Bulk Operations**

   ```typescript
   // Fetch multiple systems in one request
   const systems = await client.systems.getMany(['sys-1', 'sys-2', 'sys-3']);
   // GET /systems?id=sys-1,sys-2,sys-3
   ```

3. **Stream Helpers**

   ```typescript
   // Auto-pagination iterator
   for await (const system of client.systems.stream()) {
     console.log(system.id, system.name);
   }
   ```

4. **Spatial Query Helpers**
   ```typescript
   // Bbox query builder
   const systems = await client.systems.list({
     bbox: [minLon, minLat, maxLon, maxLat],
     datetime: { start: new Date('2024-01-01'), end: new Date('2024-12-31') },
   });
   ```

### 3.3 TypeScript Type Exports

**What Was Missing:** Clean, focused type exports for users.

**Should Have Implemented:**

```typescript
// types/index.ts - Clean public API
export interface System {
  id: string;
  type: 'Feature';
  geometry: Geometry | null;
  properties: SystemProperties;
  links?: Link[];
}

export interface SystemProperties {
  featureType: 'System';
  uid: string; // URI
  name: string;
  description?: string;
  validTime?: [string, string];
  // ... essentials only, not every SensorML property
}

export interface QueryParams {
  limit?: number;
  offset?: number;
  bbox?: [number, number, number, number];
  datetime?: string | { start: Date; end: Date };
  id?: string[];
  q?: string[];
  // ... standard query params only
}

export interface CSAPIClient {
  systems: SystemEndpoint;
  deployments: DeploymentEndpoint;
  procedures: ProcedureEndpoint;
  samplingFeatures: SamplingFeatureEndpoint;
  properties: PropertyEndpoint;
  datastreams: DataStreamEndpoint;
  observations: ObservationEndpoint;
  controlstreams: ControlStreamEndpoint;
  commands: CommandEndpoint;
}
```

**What NOT to Export:** Complete SensorML type hierarchy (DescribedObject, AbstractProcess, PhysicalSystem, PhysicalComponent, SimpleProcess, AggregateProcess, Deployment, DerivedProperty, Position, Vector, DataRecord, Pose, Text, CapabilityList, CharacteristicList, etc.). Let dedicated SensorML library handle that.

---

## 4. Scope Boundary Definition

### 4.1 Client Library Responsibilities (IN SCOPE)

**✅ HTTP Operations:**

- Build URLs with query parameters
- Execute GET/POST/PUT/PATCH/DELETE requests
- Handle authentication (Basic, Bearer, OAuth)
- Follow pagination links
- Manage request/response headers

**✅ Format Abstraction:**

- Automatic format detection (from Content-Type + body structure + context)
- Format-specific parsing (GeoJSON, SensorML JSON, SWE Common JSON)
- Format validation (pre-request validation, post-response validation)
- Format version handling (detect and parse multiple format versions)
- Format serialization (canonical model → format-specific representation)
- Unified API (users work with canonical data models, not raw formats)

**✅ Error Handling:**

- Parse HTTP status codes
- Extract OGC Exception Reports (XML)
- Provide typed error classes (FormatDetectionError, FormatParseError, ValidationError)
- Include request context in errors
- Detailed validation error messages with JSON paths and suggestions

**✅ Conformance Detection:**

- Fetch /conformance on initialization
- Detect available resource types
- Provide capability checking methods
- Adapt behavior based on conformance

**✅ URL Building:**

- Encode query parameters correctly
- Handle arrays (comma-separated)
- Handle bbox (4-6 values)
- Handle datetime (ISO 8601)
- Handle special characters

**✅ Response Parsing:**

- Parse JSON responses
- Extract links from responses
- Handle pagination (next/prev links)
- Provide collection metadata (numberMatched, timeStamp)
- Convert format-specific representations to canonical models
- Extract geometry from SensorML position objects (all SWE Common position types)
- Parse nested structures (components, connections, modes)
- Decode observation results based on DataStream schemas

**✅ TypeScript Types:**

- Canonical resource interfaces (System, Deployment, etc.)
- Format-specific type definitions (SensorML, SWE Common)
- Query parameter types
- Response collection types
- Error types
- Complete type safety across all formats

**✅ Convenience Methods:**

- Fluent API for sub-resources
- Async iterators for pagination
- Batch operations (getMany)
- Spatial/temporal query builders

### 4.2 NOT Client Library Responsibilities (OUT OF SCOPE)

**❌ Complex Geometry Operations:**

- Coordinate system transformations (use Proj4js)
- Geometry operations (buffer, intersection, etc. - use Turf.js)
- Spatial analysis (use PostGIS or similar)

**❌ Data Transformation Beyond Format Parsing:**

- Unit conversions (use convert-units or similar)
- Time zone conversions (use date-fns-tz or similar)
- Custom data aggregations
- Statistical computations

**❌ Server-Side Logic:**

- Cascade delete implementation (server responsibility)
- Recursive query traversal (server responsibility)
- Access control enforcement (server responsibility)
- Resource validation rules (server responsibility)
- Conformance class dependencies (server responsibility)

**❌ Domain-Specific Functionality:**

- Sensor calibration algorithms
- Data quality assessment
- Observation interpolation
- Prediction/forecasting

### 4.3 Why Format Abstraction IS Library Responsibility

**Justification 1: Spec Defines Multiple Formats as First-Class Citizens**

CSAPI Part 1 and Part 2 specs define multiple formats with equal standing:

- **GeoJSON** (application/geo+json) - mandatory for spatial resources
- **SensorML JSON** (application/sml+json) - optional for systems/deployments/procedures
- **SWE Common** (application/swe+json) - mandatory for observations/commands

The spec requires format negotiation (Section 7.3) and format-specific behavior. The library MUST handle these formats to be spec-compliant.

**Justification 2: Format Abstraction is Core Value Proposition**

Without format abstraction, users must:

```typescript
// ❌ WITHOUT format abstraction - user burden
const response = await client.systems.getRaw('system-1');
const contentType = response.headers['content-type'];

if (contentType === 'application/geo+json') {
  const feature = response.data as Feature;
  console.log(feature.properties.name, feature.geometry);
} else if (contentType === 'application/sml+json') {
  const sml = response.data as PhysicalSystem;
  // User must understand SensorML structure
  const position = sml.position;
  let geometry;
  if (position.type === 'Vector') {
    geometry = { type: 'Point', coordinates: position.coordinates };
  } else if (position.type === 'DataRecord') {
    const lat = position.fields.find((f) => f.name === 'lat')?.value;
    const lon = position.fields.find((f) => f.name === 'lon')?.value;
    geometry = { type: 'Point', coordinates: [lon, lat] };
  }
  // ... more cases
  console.log(sml.label, geometry);
}
```

With format abstraction, library provides unified interface:

```typescript
// ✅ WITH format abstraction - clean API
const system = await client.systems.get('system-1');
// Format is transparent - always get canonical System model
console.log(system.properties.name, system.geometry);
```

**Justification 3: Avoids Multi-Library Dependency Hell**

Without format abstraction, users need:

- `@turf/turf` for GeoJSON operations
- `@ogc/sensorml-parser` for SensorML parsing
- `@ogc/swe-common` for SWE Common parsing
- `geojson` for type definitions
- Custom glue code to integrate all libraries

With format abstraction, single library handles everything:

- `@camptocamp/ogc-client` - one dependency, unified API

**Justification 4: Format Complexity is Not User Concern**

Users care about **what data means**, not **how it's encoded**:

- "Get system location" shouldn't require understanding SWE Common Vector/DataRecord/Pose
- "Create deployment" shouldn't require learning SensorML structure
- "Fetch observations" shouldn't require decoding SWE DataArray encoding

Library hides format complexity, exposing clean domain API.

**Justification 5: Validation Prevents Server Round-Trip Errors**

Pre-request validation catches errors before network call:

```typescript
// ❌ WITHOUT validation - wasted HTTP request
const system = {
  // Missing required 'uid' property
  name: 'Test System',
};
const response = await client.systems.create(system); // 400 Bad Request after network round-trip

// ✅ WITH validation - immediate feedback
const system = {
  name: 'Test System',
};
const validation = client.systems.validate(system);
if (!validation.valid) {
  console.error('Invalid system:', validation.errors);
  // [{ path: '/uid', message: 'Required property missing', suggestion: 'Add uid property with URI value' }]
}
```

Validation = better UX, fewer server errors, faster development.

### 4.4 Where to Draw the Line

**Question:** Should library parse `response.data.features` from a FeatureCollection?

**Answer:** **YES** - This is basic JSON access AND format abstraction. Users expect `listSystems()` to return `System[]`, not raw FeatureCollection.

**Question:** Should library extract `lat/lon` from a SensorML Position object?

**Answer:** **YES** - This is format abstraction core responsibility. SensorML Position is CSAPI-defined format that library must parse to provide unified geometry access.

**Question:** Should library validate that a System has a required `uid` property?

**Answer:** **YES** - Pre-request validation prevents wasted HTTP requests and provides better developer experience with actionable error messages.

**Question:** Should library transform coordinates from EPSG:4326 to EPSG:3857?

**Answer:** **NO** - Coordinate transformation is geometry operation beyond format parsing. Users apply Proj4js for CRS transformations.

**Question:** Should library calculate distance between two systems?

**Answer:** **NO** - Spatial analysis is domain-specific functionality beyond format abstraction. Users apply Turf.js for geometry operations.

---

## 5. Lessons Learned

### 5.1 Format Abstraction Done Right

**Lesson:** Format abstraction is core library value - do it comprehensively or suffer user friction.

**Indicators of Good Format Abstraction:**

- Users never write format-specific code
- Single API works regardless of server format choices
- Automatic format detection with fallbacks
- Comprehensive format coverage (not partial)
- Extensible for future formats

**Implementation Strategy:**

- Plugin architecture for format parsers
- Comprehensive unit tests for each format
- Version-specific parsing for format evolution
- Detailed error messages for parse failures
- Performance optimization (minimize parsing overhead)

### 5.2 Validation is Developer Experience

**Transport Layer Responsibilities:**

- Fetch data via HTTP
- Set correct headers (Accept, Content-Type)
- Handle errors
- Return raw response

**Parsing Layer Responsibilities (SEPARATE LIBRARIES):**

- Interpret format structures
- Validate schemas
- Extract nested values
- Transform between formats

**Example Separation:**

```
┌─────────────────────────────────────────────┐
│  User Application                           │
└──────────────┬──────────────────────────────┘
               │
               ├──► @camptocamp/ogc-client (HTTP transport)
               │
               ├──► @ogc/sensorml-parser (SensorML parsing)
               │
               ├──► @ogc/swe-common (SWE Common parsing)
               │
               └──► @turf/turf (GeoJSON operations)
```

### 5.3 TypeScript vs Runtime Validation

**Lesson:** Leverage TypeScript for type safety, avoid runtime validation.

**TypeScript Strengths:**

- Compile-time type checking
- IDE autocomplete and error detection
- Interface contracts
- Generic constraints

**When Runtime Validation Needed:**

- External data from untrusted sources (not applicable—data comes from server)
- Dynamic schemas (not applicable—CSAPI has fixed schemas)
- User input sanitization (not applicable—server validates)

**Conclusion:** For CSAPI client, TypeScript types are sufficient. No Ajv, no Zod, no json-schema.

### 5.4 Test Focus

**Lesson:** Tests should validate HTTP operations, not parsing logic.

**First Iteration Test Distribution:**

- 60% parsing tests (SensorML, SWE, format detection)
- 30% validation tests
- 10% HTTP operation tests

**Correct Test Distribution:**

- 70% HTTP operation tests (URL building, query params, error handling)
- 20% integration tests (real server responses)
- 10% convenience method tests (fluent API, iterators)

**Example Good Test:**

```typescript
describe('SystemEndpoint', () => {
  it('should build correct URL with query parameters', () => {
    const url = endpoint.buildUrl('/systems', {
      bbox: [-180, -90, 180, 90],
      datetime: '2024-01-01T00:00:00Z',
      limit: 100,
    });

    expect(url).toBe(
      'https://server.com/api/systems?bbox=-180,-90,180,90&datetime=2024-01-01T00:00:00Z&limit=100'
    );
  });

  it('should set Accept header based on format parameter', async () => {
    await endpoint.getSystem('sys-1', { format: 'application/sml+json' });

    expect(mockHttp.lastRequest.headers.Accept).toBe('application/sml+json');
  });
});
```

**Example Bad Test:**

```typescript
describe('SystemParser', () => {
  it('should extract latitude from DataRecord position', () => {
    const sml = {
      type: 'PhysicalSystem',
      position: {
        type: 'DataRecord',
        fields: [
          { name: 'lat', value: 45.0 },
          { name: 'lon', value: 5.0 },
        ],
      },
    };

    const result = parser.parseSensorML(sml);
    expect(result.geometry.coordinates).toEqual([5.0, 45.0, 0]);
  });
});
```

This test validates parsing logic that shouldn't exist in the client library.

---

## 6. Upstream Library Patterns

### 6.1 WFS Client Pattern

**Scope:** WFS client in upstream ogc-client is minimal—fetches XML, parses capabilities, returns feature properties.

**What WFS Does:**

```typescript
// wfs/endpoint.ts
async getFeatureType(name: string): Promise<WfsFeatureTypeFull> {
  const url = this.getFeatureTypeUrl(name);
  const response = await fetch(url);
  const xml = await response.text();

  // Parse XML DescribeFeatureType response
  // Extract property names/types only
  return parseFeatureTypeSchema(xml);
}

async getFeatures(typeName: string, options?: QueryOptions): Promise<Feature[]> {
  const url = this.getFeatureUrl(typeName, options);
  const response = await fetch(url);
  const xml = await response.text();

  // Parse GML to extract features
  // NO geometry operations, NO schema validation
  return parseFeatureProps(xml, featureType);
}
```

**What WFS Does NOT Do:**

- ❌ Validate feature properties against schema
- ❌ Transform coordinates
- ❌ Parse complex GML geometries (beyond basic extraction)
- ❌ Validate XML against XSD
- ❌ Interpret WFS filter expressions

**Lesson:** WFS client focuses on **fetching and basic parsing**. Complex geometry operations and validation left to users with dedicated libraries (Turf.js, JSTS, etc.).

### 6.2 WMS Client Pattern

**Scope:** WMS client builds URLs, parses capabilities, returns layer info. No image processing.

**What WMS Does:**

```typescript
// wms/endpoint.ts
getMapUrl(layers: string[], options: GetMapOptions): string {
  const params = new URLSearchParams();
  params.set('SERVICE', 'WMS');
  params.set('REQUEST', 'GetMap');
  params.set('LAYERS', layers.join(','));
  params.set('WIDTH', options.width.toString());
  params.set('HEIGHT', options.height.toString());
  params.set('BBOX', options.bbox.join(','));
  params.set('CRS', options.crs || 'EPSG:4326');

  return `${this.baseUrl}?${params.toString()}`;
}
```

**What WMS Does NOT Do:**

- ❌ Fetch or decode images
- ❌ Validate image formats
- ❌ Transform image data
- ❌ Parse legend graphics
- ❌ Validate bounding boxes

**Lesson:** WMS client is a **URL builder**. Image fetching/processing is user responsibility.

### 6.3 OGC API - Features Pattern

**Scope:** Fetch collections, items, and queryables. Basic JSON parsing only.

**What OGC API Endpoint Does:**

```typescript
// ogc-api/endpoint.ts
async getCollectionItems(
  collectionId: string,
  options?: QueryOptions
): Promise<FeatureCollection> {
  const url = await this.getCollectionItemsUrl(collectionId, options);
  const response = await fetch(url);
  const json = await response.json();

  // Return raw GeoJSON FeatureCollection
  return json;
}
```

**What OGC API Endpoint Does NOT Do:**

- ❌ Parse feature properties beyond JSON access
- ❌ Validate feature schemas
- ❌ Transform geometries
- ❌ Interpret queryable definitions
- ❌ Execute CQL filters locally

**Lesson:** OGC API client is **JSON fetcher**. Schema interpretation and geometry operations are user responsibility.

### 6.4 Pattern Summary

| Library     | Parses                              | Returns                               | User Responsibility                 |
| ----------- | ----------------------------------- | ------------------------------------- | ----------------------------------- |
| **WFS**     | XML Capabilities, GML features      | Feature properties (name/value pairs) | Geometry operations, validation     |
| **WMS**     | XML Capabilities                    | URLs, layer metadata                  | Image fetching, rendering           |
| **WMTS**    | XML Capabilities                    | URLs, tile metadata                   | Tile fetching, rendering            |
| **OGC API** | JSON capabilities, JSON collections | Raw JSON (FeatureCollection)          | Schema interpretation, geometry ops |
| **EDR**     | JSON queries                        | Raw JSON (CoverageJSON)               | Coverage data parsing               |

**CSAPI Should Follow Same Pattern:**

- Parse JSON capabilities (/conformance, /collections)
- Return raw JSON for resources (Systems, Deployments, Observations)
- Let users apply SensorML/SWE libraries for deep parsing

---

## 7. Recommendations for V2

### 7.1 Implementation Strategy

**Phase 1: Core HTTP Client (Week 1-2)**

- URL building with query parameters
- GET/POST/PUT/DELETE methods
- Authentication (Basic, Bearer)
- Error handling (HTTP status + OGC exceptions)
- Format negotiation (Accept headers)

**Phase 2: Part 1 Resources (Week 3-4)**

- Systems endpoint
- Deployments endpoint
- Procedures endpoint
- Sampling Features endpoint
- Properties endpoint
- Sub-resource navigation

**Phase 3: Part 2 Resources (Week 5-6)**

- DataStreams endpoint
- Observations endpoint
- ControlStreams endpoint
- Commands endpoint
- Schema endpoints
- Status/Result endpoints

**Phase 4: Convenience (Week 7)**

- Fluent API
- Async iterators
- Batch operations
- Spatial/temporal query builders

**Total Timeline:** 7 weeks (vs 12 weeks for first iteration with parsing)

### 7.2 Code Organization

```
src/
├── core/                      # HTTP client, error handling
│   ├── client.ts
│   ├── errors.ts
│   ├── auth.ts
│   └── url-builder.ts
├── endpoints/                 # Resource endpoints
│   ├── systems.ts
│   ├── deployments.ts
│   ├── procedures.ts
│   ├── sampling-features.ts
│   ├── properties.ts
│   ├── datastreams.ts
│   ├── observations.ts
│   ├── controlstreams.ts
│   └── commands.ts
├── types/                     # TypeScript interfaces
│   ├── system.ts
│   ├── deployment.ts
│   ├── procedure.ts
│   ├── sampling-feature.ts
│   ├── property.ts
│   ├── datastream.ts
│   ├── observation.ts
│   ├── controlstream.ts
│   ├── command.ts
│   ├── query-params.ts
│   └── index.ts
└── utils/                     # Helpers
    ├── conformance.ts
    ├── pagination.ts
    └── links.ts
```

**Total Lines of Code Target:** ~3,000 lines (vs 7,000+ in first iteration)

### 7.3 Documentation Strategy

**User Guide Should Cover:**

1. Installation and setup
2. Authentication
3. Basic CRUD operations
4. Query parameters
5. Pagination
6. Format selection
7. Error handling
8. Using with SensorML/SWE libraries (separate packages)

**User Guide Should NOT Cover:**

- How to parse SensorML (link to @ogc/sensorml-parser docs)
- How to parse SWE Common (link to @ogc/swe-common docs)
- Geometry operations (link to Turf.js docs)
- Schema validation (not needed with TypeScript)

### 7.4 Testing Strategy

**Test Categories:**

1. **URL Building Tests** (30%)

   - Query parameter encoding
   - Array handling (bbox, id lists)
   - Special characters
   - Format parameter

2. **HTTP Operation Tests** (40%)

   - Request headers
   - Response parsing
   - Error status codes
   - Authentication

3. **Integration Tests** (20%)

   - Real server responses (fixtures)
   - Pagination
   - Link following
   - Conformance detection

4. **Convenience Method Tests** (10%)
   - Fluent API
   - Async iterators
   - Batch operations

**Target:** 90%+ code coverage, ~500-600 test cases

---

## 8. Decision Matrix

### 8.1 Feature Inclusion Criteria

For each proposed feature, ask:

| Question                                       | Include If YES | Exclude If YES |
| ---------------------------------------------- | -------------- | -------------- |
| Is this HTTP transport logic?                  | ✅             |                |
| Is this URL building/encoding?                 | ✅             |                |
| Is this basic JSON access?                     | ✅             |                |
| Does upstream WFS/WMS do this?                 | ✅             |                |
| Does this require format-specific knowledge?   |                | ❌             |
| Does this interpret schemas?                   |                | ❌             |
| Does this validate structures?                 |                | ❌             |
| Would a dedicated library handle this better?  |                | ❌             |
| Is this more than 200 lines?                   |                | ❌             |
| Does this require external validation library? |                | ❌             |

### 8.2 Examples

| Feature                                   | Decision   | Reasoning                  |
| ----------------------------------------- | ---------- | -------------------------- |
| URL building for `/systems?bbox=...`      | ✅ Include | Core HTTP transport        |
| Parsing `response.data.features` array    | ✅ Include | Basic JSON access          |
| Following `rel=next` links                | ✅ Include | Standard pagination        |
| Setting Accept header                     | ✅ Include | Format negotiation         |
| Extracting lat/lon from SensorML Position | ❌ Exclude | Format-specific parsing    |
| Validating System has required uid        | ❌ Exclude | TypeScript enforces this   |
| Converting SensorML → GeoJSON             | ❌ Exclude | Format transformation      |
| Parsing SWE DataRecord fields             | ❌ Exclude | Schema interpretation      |
| Decoding SWE Binary encoding              | ❌ Exclude | Complex format decoding    |
| Validating UoM codes                      | ❌ Exclude | Domain-specific validation |

---

## 9. Conclusion

**Primary Gap:** First iteration **incompletely implemented** format parsing (~1,500 lines SensorML, ~800 lines SWE, ~400 lines validation) without comprehensive coverage, proper extensibility, and robust error handling.

**Core Lesson:** Client library MUST provide **format abstraction layer** as core value proposition. CSAPI spec defines multiple formats (GeoJSON, SensorML JSON, SWE Common) as first-class citizens - library must handle all comprehensively.

**Why Format Abstraction is Library Responsibility:**

1. **Spec Requirement:** CSAPI defines format negotiation and multiple mandatory/optional formats
2. **User Experience:** Users should work with canonical models, not raw format structures
3. **Avoid Dependency Hell:** Single library vs juggling @ogc/sensorml-parser + @ogc/swe-common + @turf/turf
4. **Hide Complexity:** Format encoding details (SWE Vector/DataRecord/Pose) shouldn't leak to users
5. **Enable Validation:** Pre-request validation prevents server errors and provides better DX

**V2 Should:**

- **Comprehensive Format Parsing** (~3,000 lines):
  - Complete SensorML parser (all types, all versions, all position formats)
  - Complete SWE Common parser (all components, all encodings)
  - GeoJSON parser with full type support
- **Robust Validation** (~800 lines):
  - Pre-request validation with actionable error messages
  - Post-response validation for server data
  - Format-specific validation rules
  - JSON Schema + semantic validation
- **Automatic Format Detection** (~400 lines):
  - Content-Type + body structure + context detection
  - Version detection for format evolution
  - Confidence scoring with fallbacks
  - Extensible for future formats
- **HTTP Operations** (~1,200 lines):
  - URL building, authentication, error handling
  - Conformance detection, pagination, link following
- **Convenience Methods** (~600 lines):
  - Fluent API, async iterators, batch operations
- **Total: ~6,000 lines** (comprehensive format abstraction + HTTP operations)

**Success Criteria:**

- ✅ Format-transparent API (users never write format-specific code)
- ✅ Comprehensive format coverage (not partial like v1)
- ✅ Validation prevents server errors (better DX)
- ✅ Extensible architecture (plugin system for formats)
- ✅ Well-tested (~3,000 lines tests covering all formats and edge cases)
- ✅ Performant (minimize parsing overhead)

**Architecture:**

```
┌─────────────────────────────────────────────────────────┐
│  User Application                                       │
│  - Works with canonical models (System, Deployment)     │
│  - Never touches format-specific structures             │
└────────────────┬────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────┐
│  @camptocamp/ogc-client CSAPI Module                    │
│  ┌─────────────────────────────────────────────────┐   │
│  │  Format Abstraction Layer                       │   │
│  │  - Automatic format detection                   │   │
│  │  - GeoJSON/SensorML/SWE parsers                │   │
│  │  - Validation (pre-request, post-response)      │   │
│  │  - Canonical model conversion                   │   │
│  └─────────────────┬───────────────────────────────┘   │
│                    │                                     │
│  ┌─────────────────▼───────────────────────────────┐   │
│  │  HTTP Transport Layer                           │   │
│  │  - URL building, authentication                 │   │
│  │  - Request/response handling                    │   │
│  │  - Error handling, conformance detection        │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

---

**End of Gap Analysis**
