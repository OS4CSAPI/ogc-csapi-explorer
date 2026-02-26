# Section 3.1: Common Format Requirements

## Overview

This section documents the common format requirements and negotiation mechanisms that apply across all CSAPI resource types in both Part 1 (Core Resources) and Part 2 (Dynamic Data). These requirements establish the foundation for how the client library should handle format selection, content negotiation, and format-specific processing.

**Key Objectives:**

- Define required vs optional formats for different resource types
- Document media type identifiers and their purposes
- Explain format negotiation mechanisms (Accept headers, query parameters)
- Establish minimum viable format support for client library
- Define parsing requirements (full parsing vs pass-through)
- Document serialization requirements for write operations
- Establish validation approach for each format
- Define client API surface for format handling
- Document error handling patterns for format-related issues

---

## Required vs Optional Formats

### Part 1: Core Resources (Systems, Deployments, Procedures, etc.)

**Required Formats:**

1. **application/json** (Plain JSON)

   - **Status:** REQUIRED for all Part 1 resources
   - **Purpose:** Base JSON representation
   - **Resources:** All resource types support this
   - **Read Operations:** MUST be supported
   - **Write Operations:** MUST be supported (if resource writable)
   - **Client Library:** MUST support

2. **application/geo+json** (GeoJSON)

   - **Status:** REQUIRED for spatial resources
   - **Purpose:** Spatial feature representation
   - **Resources:** Systems, Deployments, Procedures, SamplingFeatures (any resource with geometry)
   - **Read Operations:** Server MUST advertise support via Accept headers (Requirement 77)
   - **Write Operations:** Server MUST accept for CREATE/UPDATE (Requirement 78)
   - **Client Library:** MUST support for spatial resources

3. **application/sml+json** (SensorML)
   - **Status:** REQUIRED for system metadata
   - **Purpose:** Rich system/procedure descriptions
   - **Resources:** Systems, Procedures (resources with detailed metadata)
   - **Read Operations:** Server MUST advertise support via Accept headers (Requirement 89)
   - **Write Operations:** Server MUST accept for CREATE/UPDATE (Requirement 90)
   - **Client Library:** MUST support for system/procedure resources

**Optional Formats:**

- Servers MAY support additional formats (e.g., HTML, XML)
- Servers MUST advertise all supported formats
- Client library SHOULD support common formats (GeoJSON, SensorML) but MAY defer uncommon formats

### Part 2: Dynamic Data (Observations, Commands)

**Required Formats:**

1. **application/json** (Plain JSON)

   - **Status:** REQUIRED for all Part 2 resources
   - **Purpose:** Base JSON representation
   - **Resources:** DataStreams, Observations, ControlStreams, Commands, CommandStatus, CommandResult, SystemEvents
   - **Read Operations:** MUST be supported
   - **Write Operations:** MUST be supported (if resource writable)
   - **Client Library:** MUST support

2. **application/swe+json** (SWE Common JSON)

   - **Status:** OPTIONAL but recommended for structured data
   - **Purpose:** SWE Common Data Model 3.0 JSON encoding
   - **Resources:** Observations, Commands, schemas
   - **Characteristics:** More compact, preserves SWE Common structure
   - **Client Library:** SHOULD support (required for full functionality)

3. **application/swe+text** (SWE Common CSV/DSV)

   - **Status:** OPTIONAL
   - **Purpose:** Delimiter-separated values (2-5x more compact than JSON)
   - **Resources:** Observations, Commands
   - **Characteristics:** Human-readable, spreadsheet-friendly, requires schema
   - **Client Library:** SHOULD support (useful for bulk data)

4. **application/swe+binary** (SWE Common Binary)
   - **Status:** OPTIONAL
   - **Purpose:** Binary encoding (10-100x more compact than JSON)
   - **Resources:** Observations, Commands
   - **Characteristics:** Most compact, not human-readable, requires schema
   - **Client Library:** SHOULD support (critical for high-frequency data)

**Optional Formats:**

- **application/geo+json** - DataStreams/ControlStreams MAY support for spatial discovery
- Servers MAY support additional formats
- Servers MUST advertise supported formats in `formats` property

---

## Media Type Identifiers

### Complete Media Type Matrix

| Media Type               | Standard       | Part | Resources              | Purpose                           |
| ------------------------ | -------------- | ---- | ---------------------- | --------------------------------- |
| `application/json`       | JSON           | 1, 2 | All resources          | Base JSON representation          |
| `application/geo+json`   | RFC 7946       | 1, 2 | Spatial resources      | GeoJSON Feature/FeatureCollection |
| `application/sml+json`   | SensorML 3.0   | 1    | Systems, Procedures    | System/procedure metadata         |
| `application/swe+json`   | SWE Common 3.0 | 2    | Observations, Commands | SWE Common JSON encoding          |
| `application/swe+text`   | SWE Common 3.0 | 2    | Observations, Commands | CSV/DSV encoding                  |
| `application/swe+binary` | SWE Common 3.0 | 2    | Observations, Commands | Binary encoding                   |
| `text/uri-list`          | RFC 2483       | 1    | Collection additions   | URI list (one per line)           |

### Media Type Characteristics

**application/json:**

- Standard: JSON (ECMA-404)
- Charset: UTF-8 (default)
- Binary: No
- Requires Schema: No
- Human-Readable: Yes
- Compression: High (verbose)

**application/geo+json:**

- Standard: RFC 7946 (GeoJSON)
- Charset: UTF-8 (MUST be UTF-8)
- Binary: No
- Requires Schema: No (self-describing)
- Human-Readable: Yes
- Compression: High (verbose)

**application/sml+json:**

- Standard: SensorML 3.0 (OGC 23-000)
- Charset: UTF-8 (default)
- Binary: No
- Requires Schema: Yes (SensorML classes)
- Human-Readable: Yes
- Compression: High (verbose)

**application/swe+json:**

- Standard: SWE Common 3.0 (OGC 23-000)
- Charset: UTF-8 (default)
- Binary: No
- Requires Schema: Yes (DataComponent schema)
- Human-Readable: Yes
- Compression: Medium (more compact than JSON)

**application/swe+text:**

- Standard: SWE Common 3.0 (TextEncoding)
- Charset: UTF-8 (default)
- Binary: No
- Requires Schema: Yes (DataComponent schema + separators)
- Human-Readable: Yes
- Compression: Medium (2-5x smaller than JSON)

**application/swe+binary:**

- Standard: SWE Common 3.0 (BinaryEncoding)
- Charset: N/A (binary)
- Binary: Yes
- Requires Schema: Yes (DataComponent schema + byte layout)
- Human-Readable: No
- Compression: Low (10-100x smaller than JSON)

---

## Format Negotiation Mechanisms

### Accept Header Mechanism (HTTP Content Negotiation)

**Part 1 Format Negotiation (Section 5.3):**

Client specifies desired format via Accept header:

```http
GET /systems/sys123
Accept: application/geo+json
```

```http
GET /procedures/proc456
Accept: application/sml+json
```

**Part 2 Format Negotiation:**

Client specifies desired observation format:

```http
GET /datastreams/ds123/observations
Accept: application/swe+binary
```

**Multiple Accept Values:**

```http
GET /systems/sys123
Accept: application/geo+json, application/json;q=0.8
```

**Quality Values (q):**

- RFC 9110 quality value mechanism
- Client specifies preference weights
- Server selects best match based on weights and capabilities

### Query Parameter Mechanism

**Part 1 Query Parameters:**

1. **`f` parameter (short form):**

   ```
   GET /systems/sys123?f=geojson
   GET /procedures/proc456?f=sml
   ```

2. **`format` parameter (full media type):**
   ```
   GET /systems/sys123?format=application/geo+json
   GET /procedures/proc456?format=application/sml+json
   ```

**Part 2 Query Parameters:**

1. **`f` parameter (full media type):**

   ```
   GET /datastreams/ds123/observations?f=application/swe+binary
   GET /controlstreams/cs456/commands?f=application/swe+json
   ```

2. **Schema-specific format parameter:**
   ```
   GET /datastreams/ds123/schema?obsFormat=application/swe+binary
   GET /controlstreams/cs456/schema?cmdFormat=application/swe+json
   ```

**URL Encoding:**

- `+` character MUST be URL-encoded as `%2B`
- Example: `application/swe+csv` → `application/swe%2Bcsv`
- Proper encoding: `?f=application/swe%2Bcsv`

### Content-Type Response Header

**Server Indicates Format:**

Server MUST include Content-Type header in response:

```http
HTTP/1.1 200 OK
Content-Type: application/geo+json; charset=utf-8

{
  "type": "Feature",
  ...
}
```

```http
HTTP/1.1 200 OK
Content-Type: application/swe+binary

<binary data>
```

**Charset Parameter:**

- JSON formats: `charset=utf-8` (SHOULD be included)
- Binary formats: No charset parameter

### Format Selection Rules (Precedence)

**OGC API Convention (Part 1, Section 5.3):**

1. **Query parameter takes precedence:**

   - If `f` or `format` parameter specified → use requested format
   - Query parameter overrides Accept header
   - Example: `?f=geojson` with `Accept: application/sml+json` → returns GeoJSON

2. **Accept header as fallback:**

   - If no query parameter → use Accept header
   - Select best match based on quality values
   - Example: `Accept: application/geo+json` → returns GeoJSON

3. **Default format:**

   - If no query parameter and no Accept header → use server default
   - Default is implementation-dependent
   - Typically: GeoJSON for spatial resources, SensorML for non-spatial (Part 1)
   - Typically: JSON for all resources (Part 2)

4. **Format not supported:**
   - Server returns `406 Not Acceptable` status code
   - Response body contains error details

**Precedence Order:**

```
Query Parameter (f/format)
  ↓ (if not specified)
Accept Header
  ↓ (if not specified)
Server Default Format
  ↓ (if format not supported)
406 Not Acceptable
```

### Format Advertisement

**Part 1: Implicit Advertisement**

- Server MUST advertise support via Accept headers (Requirements 77, 89)
- Format support discovered through API metadata
- No explicit `formats` property in resources

**Part 2: Explicit Advertisement**

DataStream/ControlStream `formats` property:

```json
{
  "type": "DataStream",
  "id": "ds123",
  "name": "Temperature Sensor",
  "formats": [
    "application/json",
    "application/swe+json",
    "application/swe+binary"
  ]
}
```

**Client Discovery:**

- Client SHOULD check `formats` property before requesting specific format
- Client SHOULD fall back to `application/json` if preferred format not listed
- Client SHOULD handle 406 errors gracefully

---

## Minimum Viable Format Support

### Client Library Requirements

**MUST Support (Core Formats):**

1. **application/json** - All resource types

   - Parse JSON responses
   - Serialize JSON for write operations
   - Validate JSON structure

2. **application/geo+json** - Spatial resources (Part 1)

   - Parse GeoJSON Feature/FeatureCollection
   - Extract geometry and properties
   - Serialize GeoJSON for write operations
   - Validate geometry structure

3. **application/sml+json** - System metadata (Part 1)
   - Parse core SensorML properties (type, label, uniqueId)
   - Extract identifiers and classifiers
   - Serialize SensorML for write operations
   - Preserve unknown properties

**SHOULD Support (Extended Formats):**

4. **application/swe+json** - Observations/Commands (Part 2)

   - Parse SWE Common JSON encoding
   - Decode data according to schema
   - Serialize SWE Common JSON for write operations
   - Validate against schema

5. **application/swe+text** - Bulk observations (Part 2)

   - Parse CSV/DSV according to schema
   - Decode text encoding (separators, decimal separator)
   - Serialize CSV/DSV for write operations
   - Validate field count and types

6. **application/swe+binary** - High-frequency data (Part 2)
   - Parse binary encoding according to schema
   - Decode binary structure (byte order, data types)
   - Serialize binary encoding for write operations
   - Validate binary layout

**MAY Support (Optional Formats):**

- HTML, XML, custom formats
- Client library MAY pass-through unsupported formats
- Client library SHOULD log warning for unsupported formats

### Format Support Matrix

| Format                 | Part | Status | Read         | Write | Validate | Client API          |
| ---------------------- | ---- | ------ | ------------ | ----- | -------- | ------------------- |
| application/json       | 1, 2 | MUST   | ✓            | ✓     | ✓        | Full support        |
| application/geo+json   | 1    | MUST   | ✓            | ✓     | ✓        | Geometry utilities  |
| application/sml+json   | 1    | MUST   | ✓            | ✓     | ✓        | Metadata extraction |
| application/swe+json   | 2    | SHOULD | ✓            | ✓     | ✓        | Schema-driven       |
| application/swe+text   | 2    | SHOULD | ✓            | ✓     | ✓        | Schema-driven       |
| application/swe+binary | 2    | SHOULD | ✓            | ✓     | ✓        | Schema-driven       |
| Other formats          | 1, 2 | MAY    | Pass-through | -     | -        | Raw access          |

---

## Parse vs Pass-Through Strategy

### Full Parsing (MUST Support)

**application/json:**

- Parse to JavaScript objects
- Validate JSON structure
- No schema required (self-describing)
- Example: `JSON.parse(responseBody)`

**application/geo+json:**

- Parse to GeoJSON Feature objects
- Validate geometry structure (coordinates, type)
- Extract properties (ogc-rel: prefix)
- Example: See Section 3.2 (GeoJSON Requirements)

**application/sml+json:**

- Parse to SensorML component objects
- Extract core properties (type, label, uniqueId)
- Preserve complex metadata (inputs, outputs, characteristics)
- Example: See Section 3.3 (SensorML Requirements)

### Schema-Driven Parsing (SHOULD Support)

**application/swe+json:**

- Fetch schema from DataStream/ControlStream
- Parse according to DataComponent structure
- Decode data according to field definitions
- Example: See Section 3.4 (SWE Common Requirements)

**application/swe+text:**

- Fetch schema from DataStream/ControlStream
- Parse CSV/DSV according to separators
- Decode fields according to DataComponent types
- Example: See Section 3.4 (SWE Common Requirements)

**application/swe+binary:**

- Fetch schema from DataStream/ControlStream
- Parse binary data according to byte layout
- Decode fields according to data types
- Example: See Section 3.4 (SWE Common Requirements)

### Pass-Through (MAY Support)

**Unsupported Formats:**

- Return raw response body
- No parsing or validation
- Client application handles format-specific processing
- Example: HTML, XML, custom formats

**Client API Design:**

```typescript
interface FormatOptions {
  format?: string;
  parse?: boolean; // false for pass-through
}

// Full parsing (default)
const system = await client.systems.get('sys123', {
  format: 'application/geo+json',
});
// Returns: GeoJSONFeature object

// Pass-through
const systemRaw = await client.systems.get('sys123', {
  format: 'application/xml',
  parse: false,
});
// Returns: string (raw XML)
```

---

## Serialization Requirements (Write Operations)

### Part 1: Core Resources

**application/json:**

- Serialize JavaScript objects to JSON
- Include required properties (uid, name, featureType)
- Omit undefined/null optional properties
- Example: `JSON.stringify(resourceObject)`

**application/geo+json:**

- Serialize to GeoJSON Feature
- Include `type: "Feature"` property
- Serialize geometry (type, coordinates)
- Serialize properties (ogc-rel: prefix for relationships)
- Validate geometry before serialization
- Example: See Section 3.2 (GeoJSON Requirements)

**application/sml+json:**

- Serialize to SensorML component
- Include required properties (type, label, uniqueId)
- Preserve complex metadata (inputs, outputs, characteristics)
- Validate SensorML structure before serialization
- Example: See Section 3.3 (SensorML Requirements)

### Part 2: Dynamic Data

**application/json:**

- Serialize Observation/Command objects to JSON
- Include required properties (phenomenonTime, result, etc.)
- Example: `JSON.stringify(observationObject)`

**application/swe+json:**

- Fetch schema from DataStream/ControlStream
- Serialize according to DataComponent structure
- Encode data according to field definitions
- Validate against schema before serialization
- Example: See Section 3.4 (SWE Common Requirements)

**application/swe+text:**

- Fetch schema from DataStream/ControlStream
- Serialize to CSV/DSV according to separators
- Encode fields according to DataComponent types
- Validate field types before serialization
- Example: See Section 3.4 (SWE Common Requirements)

**application/swe+binary:**

- Fetch schema from DataStream/ControlStream
- Serialize to binary data according to byte layout
- Encode fields according to data types
- Validate data types before serialization
- Example: See Section 3.4 (SWE Common Requirements)

### Content-Type Header (Client-Side)

**POST/PUT/PATCH Requests:**

Client MUST include Content-Type header:

```typescript
const response = await fetch('/systems', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/geo+json; charset=utf-8',
  },
  body: JSON.stringify(geoJsonFeature),
});
```

**Charset Parameter:**

- JSON formats: Include `charset=utf-8`
- Binary formats: Omit charset parameter

---

## Validation Requirements

### Client-Side Validation Strategy

**Pre-Send Validation:**

- Validate format structure before sending to server
- Prevent 400 Bad Request errors
- Improve client-side error messages

**Post-Receive Validation:**

- Validate format structure after receiving from server
- Detect malformed responses
- Handle server-side errors gracefully

### Format-Specific Validation

**application/json:**

- JSON syntax validation (automatic with `JSON.parse()`)
- Schema validation (optional, JSON Schema)
- Required property validation

**application/geo+json:**

- GeoJSON structure validation (type, coordinates)
- Geometry validation (coordinate count, closure)
- CRS validation (WGS84/CRS84 only)
- See Section 3.2 for detailed validation rules

**application/sml+json:**

- SensorML structure validation (type, label, uniqueId)
- Component type validation (PhysicalSystem, etc.)
- Required property validation
- See Section 3.3 for detailed validation rules

**application/swe+json:**

- DataComponent structure validation
- Field type validation
- Unit validation (UCUM codes)
- See Section 3.4 for detailed validation rules

**application/swe+text:**

- Field count validation (matches schema)
- Field type validation (numeric, string, datetime)
- Separator validation (consistent use)
- See Section 3.4 for detailed validation rules

**application/swe+binary:**

- Byte layout validation (matches schema)
- Data type validation (byte length)
- Byte order validation (BIG_ENDIAN/LITTLE_ENDIAN)
- See Section 3.4 for detailed validation rules

### Validation Libraries

**Recommended:**

- **ajv** - JSON Schema validation
- **@turf/turf** - GeoJSON geometry validation
- Custom validators for SensorML and SWE Common

**Client Library API:**

```typescript
interface ValidationOptions {
  validate?: boolean; // default: true
  strict?: boolean; // default: false
}

// Validate before sending
const system = await client.systems.create(systemData, {
  format: 'application/geo+json',
  validate: true,
  strict: true,
});

// Skip validation (for performance)
const observation = await client.observations.create(obsData, {
  format: 'application/swe+json',
  validate: false,
});
```

---

## Client API Design

### Format Selection API

**Method-Level Format Parameter:**

```typescript
// Explicit format selection
const system = await client.systems.get('sys123', {
  format: 'application/geo+json',
});

// Default format (application/json)
const system = await client.systems.get('sys123');

// Multiple format preferences
const system = await client.systems.get('sys123', {
  formats: ['application/geo+json', 'application/json'],
});
```

**Global Format Preferences:**

```typescript
const client = new CSAPIClient({
  baseURL: 'https://api.example.org',
  defaultFormats: {
    systems: 'application/geo+json',
    procedures: 'application/sml+json',
    observations: 'application/swe+binary',
  },
});
```

### Format-Specific Convenience Methods

**GeoJSON Methods:**

```typescript
// Get system as GeoJSON Feature
const feature = await client.systems.getAsGeoJSON('sys123');

// Get systems as GeoJSON FeatureCollection
const featureCollection = await client.systems.listAsGeoJSON({ limit: 100 });

// Create system from GeoJSON Feature
const system = await client.systems.createFromGeoJSON(geoJsonFeature);
```

**SensorML Methods:**

```typescript
// Get system as SensorML
const sensorML = await client.systems.getAsSensorML('sys123');

// Extract identifiers from SensorML
const identifiers = await client.systems.getIdentifiers('sys123');

// Extract characteristics from SensorML
const characteristics = await client.systems.getCharacteristics('sys123');
```

**SWE Common Methods:**

```typescript
// Get observations with specific encoding
const observations = await client.observations.list('ds123', {
  format: 'application/swe+binary',
  limit: 10000,
});

// Decode observations according to schema
const decoded = await client.observations.decode(observations, schema);

// Encode observations for write operation
const encoded = await client.observations.encode(
  observationData,
  schema,
  'application/swe+binary'
);
```

### Format Detection API

**Automatic Format Detection:**

```typescript
// Detect format from Content-Type header
const system = await client.systems.get('sys123');
console.log(system.format); // 'application/geo+json'

// Detect format from response body
const detectedFormat = client.formats.detect(responseBody);
console.log(detectedFormat); // 'application/geo+json'
```

**Format Capabilities API:**

```typescript
// Get supported formats for resource type
const formats = await client.systems.getSupportedFormats('sys123');
console.log(formats); // ['application/json', 'application/geo+json', 'application/sml+json']

// Check if format supported
const supported = await client.systems.supportsFormat(
  'sys123',
  'application/geo+json'
);
console.log(supported); // true
```

---

## Error Handling

### Format-Related Errors

**Unsupported Format (406 Not Acceptable):**

```typescript
try {
  const system = await client.systems.get('sys123', {
    format: 'application/xml',
  });
} catch (error) {
  if (error.status === 406) {
    console.error('Format not supported:', error.requestedFormat);
    // Fall back to default format
    const system = await client.systems.get('sys123');
  }
}
```

**Malformed Content (Parse Error):**

```typescript
try {
  const observations = await client.observations.list('ds123', {
    format: 'application/swe+binary',
  });
} catch (error) {
  if (error instanceof ParseError) {
    console.error('Failed to parse binary data:', error.message);
    // Log error and retry with different format
    const observations = await client.observations.list('ds123', {
      format: 'application/json',
    });
  }
}
```

**Validation Error (400 Bad Request):**

```typescript
try {
  const system = await client.systems.create(invalidSystemData, {
    format: 'application/geo+json',
  });
} catch (error) {
  if (error.status === 400) {
    console.error('Validation failed:', error.validationErrors);
    // Fix validation errors and retry
  }
}
```

### Error Types

**UnsupportedFormatError:**

- Thrown when requested format not supported by server
- HTTP Status: 406 Not Acceptable
- Includes: `requestedFormat`, `supportedFormats`

**MalformedFormatError:**

- Thrown when response cannot be parsed
- Includes: `format`, `responseBody`, `parseError`

**ValidationError:**

- Thrown when data fails validation
- HTTP Status: 400 Bad Request
- Includes: `validationErrors`, `fieldPath`, `expectedType`

**FormatConversionError:**

- Thrown when format conversion fails
- Includes: `sourceFormat`, `targetFormat`, `conversionError`

### Error Handling Strategy

**Graceful Degradation:**

1. Try preferred format
2. If 406 error → fall back to `application/json`
3. If parse error → log and retry with different format
4. If all formats fail → throw error

**Format Fallback Chain:**

```typescript
const formatChain = [
  'application/swe+binary', // Preferred
  'application/swe+json', // Fallback 1
  'application/json', // Fallback 2 (always supported)
];

let observations;
for (const format of formatChain) {
  try {
    observations = await client.observations.list('ds123', { format });
    break;
  } catch (error) {
    if (error.status === 406) {
      continue; // Try next format
    }
    throw error; // Other error, don't retry
  }
}
```

**Logging and Monitoring:**

```typescript
client.on('format-error', (error) => {
  console.warn('Format error:', {
    type: error.type,
    format: error.format,
    resource: error.resourceType,
    message: error.message,
  });
});

// Metrics
client.metrics.incrementCounter('format_errors', {
  format: 'application/swe+binary',
  error_type: 'parse_error',
});
```

---

## Summary

This section establishes the foundation for format handling in the CSAPI client library:

1. **Required Formats:**

   - Part 1: `application/json`, `application/geo+json`, `application/sml+json`
   - Part 2: `application/json`, `application/swe+json`, `application/swe+text`, `application/swe+binary`

2. **Format Negotiation:**

   - Query parameter (f/format) takes precedence
   - Accept header as fallback
   - Server default if neither specified
   - 406 Not Acceptable if format not supported

3. **Client Library Requirements:**

   - MUST support: JSON, GeoJSON, SensorML
   - SHOULD support: SWE Common (JSON, CSV, Binary)
   - MAY support: Other formats (pass-through)

4. **Processing Strategy:**

   - Full parsing for all MUST/SHOULD formats
   - Schema-driven parsing for SWE Common formats
   - Pass-through for unsupported formats

5. **API Design:**
   - Format parameter in all methods
   - Format-specific convenience methods
   - Format detection and capabilities API
   - Graceful error handling with fallback

See Sections 3.2 (GeoJSON), 3.3 (SensorML), and 3.4 (SWE Common) for format-specific implementation details.
