# SWE Common 3.0 Parser Testing Specification

> **⚠️ REVIEW NOTICE (Phase 2D, H1/H2/M2/L3):** This document has significant strengths and significant problems that must be understood before use.
>
> **Strengths (use directly):**
>
> - **Binary encoding content (~50% of document)** is genuinely client-oriented: byte-level parsing, endianness handling, IEEE 754 edge cases, buffer truncation, data type specifications (Sections 2.3, 3, 10.2). This content directly tests parser implementation behavior and can be used as-is.
> - Component type property matrices (Section 4) are useful reference for what to extract.
> - Spec example fixture inventory (Section 8) is directly usable.
> - Nesting strategy (Section 5), fixture directory structure (Section 12), and phased implementation plan (Section 15) are sound.
>
> **Problems (do not use as-is):**
>
> 1. **No parser output model defined.** Like Doc 09, this document never defines what the SWE Common parser functions return — no TypeScript interfaces for parsed components. Define output types first.
> 2. **22 error IDs (ERR-SWE-\*)** in Section 7 mix genuine parser errors (buffer truncation, corrupted data) with spec conformance checks (constraint violations, UOM validation). See Section 7 notice.
> 3. **OpenSensorHub live server fixture sourcing** in Section 9 — anti-pattern AP2. Do not fetch fixtures from live servers. See Section 9 notice.
> 4. **JSON/Text encoding tests** (Sections 2.1, 2.2) include property validation (constraint checking, UOM format validation) that tests data correctness rather than parser extraction.
> 5. **98 research questions** organized by spec concepts (Q1-Q98), disproportionate to implementation scope. This reflects the research methodology, not the testing scope.
>
> **How to use this document:** Start with binary encoding sections (Sections 2.3, 3) for implementation. Use property matrices (Section 4) as reference for what to extract. Use spec example fixtures (Section 8). Define parser TypeScript output interfaces before writing tests. Write tests as `parseSWEComponent(fixture, encoding) → expectedTypedOutput`. See [Phase 2D review](../review/phase-2d-csapi-specific-testing-category.md) for details.

**Research Plan:** [Research Plan 10: SWE Common 3.0 Format Testing Requirements](../research-plans/10-swe-common-testing-requirements.md)  
**Research Questions:** 98 questions about SWE Common 3.0 component types across three encodings, JSON/Text/Binary encoding requirements, binary byte format specifications (endianness, IEEE 754, data types), component type testing, nested structures, schema validation for observations, UOM/quality/time reference frames, error handling per encoding, specification examples, and parser implementation organization  
**Methodology:** 5-phase systematic analysis (SWE Common 3.0 specification deep dive extracting all component types and encoding rules → JSON schema analysis for format constraints → Binary encoding deep dive documenting byte-level formats (MOST CRITICAL) → Example and fixture analysis from spec → Test strategy design creating test specification with emphasis on binary encoding ~50% of effort)  
**Research Time:** ~4.5 hours (February 5, 2026)

**Primary Source(s):**

- [SWE Common 3.0 Specification (24-014)](https://docs.ogc.org/is/24-014/24-014.html)
- [SWE Common 3.0 JSON Schema](https://schemas.opengis.net/sweCommon/3.0/)
- [CSAPI Implementation Guide](../../../planning/csapi-implementation-guide.md) (SWE Common parser specification)

**Supporting Resources:**

- Section 8: [CSAPI Specification Reference](08-csapi-specification-test-requirements.md) (SWE Common specification details)
- Section 9: [SensorML Testing Requirements](09-sensorml-testing-requirements.md) (integration context - characteristics/capabilities use SWE Common)
- [Format Requirements Analysis](../../requirements/csapi-format-requirements.md) (SWE Common subset for CSAPI)
- [OpenSensorHub Analysis](../../requirements/csapi-opensensorhub-analysis.md) (real-world SWE Common examples)
- Section 6: [Meaningful vs Trivial Definition](06-meaningful-vs-trivial-definition.md) (quality context for test depth)
- Section 1-2: Upstream format parser test patterns

**Document Purpose:** Define testing requirements for the SWE Common 3.0 parser covering all 12+ component types (Quantity, Count, Boolean, Category, Text, Time, DataRecord, Vector, DataArray, Matrix, DataChoice, DataStream) across all three encodings (JSON, Text, Binary), with special emphasis on binary encoding byte-level parsing (~50% of test effort), endianness handling, IEEE 754 edge cases, and fixture requirements (~120 fixtures including binary .bin files with hex dumps), with estimated 1,700-2,500 test lines. **Note:** Parser TypeScript output interfaces must be defined before tests can be implemented — see review notice above.

---

## Executive Summary

This document defines comprehensive testing requirements for the SWE Common 3.0 parser, covering all three encodings (JSON, Text, Binary), all 12+ component types, and complex schema validation. SWE Common 3.0 is the most complex format in CSAPI, used for DataStream schemas, Observation results, and Command parameters in Part 2.

### Key Findings

**Total Component Types:** 12+ types requiring comprehensive testing across 3 encodings

- Quantity, Count, Boolean, Text, Time, Category (simple components)
- QuantityRange, CategoryRange, TimeRange (range components)
- DataRecord, DataArray, Vector, Matrix, DataChoice, GeometryData (complex components)

**Total Encodings:** 3 formats with different complexity levels

- **JSON** (HIGH) - Human-readable, moderate complexity
- **Text/CSV** (HIGH) - Compact tabular, delimiter handling complexity
- **Binary** (**CRITICAL**) - Maximum efficiency, highest complexity (byte-level parsing, endianness, IEEE 754)

**Testing Priorities:**

- **CRITICAL:** Binary encoding all types (byte-level validation), JSON DataRecord/DataArray, schema validation
- **HIGH:** Text encoding all types, JSON all simple components, binary endianness tests
- **MEDIUM:** Advanced component types (Matrix, DataChoice, GeometryData), quality information, nil values
- **LOW:** Time reference frames, CRS validation, performance optimization

**Fixture Requirements:** ~120 fixtures

- JSON: ~40 fixtures (simple components, DataRecord, DataArray, nested structures)
- Text: ~40 fixtures (delimiter variations, missing values, quoted strings)
- Binary: ~40 fixtures (.bin files + hex dumps + expected results + encoding definitions)

**Estimated Test Implementation:** 1,700-2,500 lines

- JSON Encoding: 378-572 lines (33 tests)
- Text Encoding: 370-507 lines (34 tests)
- Binary Encoding: 865-1,284 lines (61 tests) - ~50% of total effort
- Schema Validation: 96-120 lines (8 tests)

**Key Testing Challenges:**

1. **Binary encoding byte-level correctness** - IEEE 754 floats, endianness, multi-byte integers, variable-length data
2. **Three-encoding coverage** - All component types must work in JSON, Text, AND Binary
3. **Schema validation complexity** - Observation results must conform to DataStream schemas
4. **Nested structure handling** - DataRecord within DataRecord, DataArray of DataRecords
5. **Binary fixture generation** - Creating .bin files with known byte sequences and hex dumps
6. **Endianness testing** - Explicit big-endian and little-endian tests for all multi-byte types

### Highest Rejection Risk

SWE Common binary encoding is the highest rejection risk in the entire CSAPI client library. Binary format parsing was identified as a major weakness in previous iterations. This format is:

- **Most complex:** 3 encodings, 12+ types, recursive structures, byte-level precision required
- **Most error-prone:** Endianness bugs, IEEE 754 edge cases, byte alignment issues
- **Most critical:** Powers all high-frequency observation data (>10 Hz sensors)
- **Least tested upstream:** Binary encoding rarely tested in other implementations

**Mitigation:** Binary encoding receives ~50% of testing effort (865-1,284 lines, 61 tests).

---

## 1. Component Type Testing Requirements

| Component Type         | Priority     | JSON Tests | Text Tests | Binary Tests | Total Fixtures | Total Test Lines |
| ---------------------- | ------------ | ---------- | ---------- | ------------ | -------------- | ---------------- |
| **Simple Components**  |
| Quantity               | **CRITICAL** | 4          | 4          | 4            | 12             | 120-180          |
| Count                  | HIGH         | 3          | 3          | 3            | 9              | 90-120           |
| Boolean                | HIGH         | 2          | 2          | 2            | 6              | 60-80            |
| Text                   | HIGH         | 3          | 3          | 3            | 9              | 90-120           |
| Time                   | **CRITICAL** | 4          | 4          | 4            | 12             | 120-180          |
| Category               | MEDIUM       | 2          | 2          | 2            | 6              | 60-80            |
| **Range Components**   |
| QuantityRange          | MEDIUM       | 2          | 2          | 2            | 6              | 60-90            |
| CategoryRange          | LOW          | 1          | 1          | 1            | 3              | 30-45            |
| TimeRange              | MEDIUM       | 2          | 2          | 2            | 6              | 60-90            |
| **Complex Components** |
| DataRecord             | **CRITICAL** | 5          | 5          | 5            | 15             | 200-300          |
| DataArray              | **CRITICAL** | 6          | 6          | 6            | 18             | 250-400          |
| Vector                 | MEDIUM       | 2          | 2          | 2            | 6              | 60-90            |
| Matrix                 | LOW          | 2          | 2          | 2            | 6              | 60-90            |
| DataChoice             | MEDIUM       | 3          | 3          | 3            | 9              | 90-150           |
| GeometryData           | MEDIUM       | 2          | 2          | 2            | 6              | 60-90            |
| **TOTAL**              |              | **43**     | **43**     | **43**       | **129**        | **1,460-2,085**  |

**Priority Rationale:**

- **CRITICAL (Quantity, Time, DataRecord, DataArray):** Core observation components used in 95% of DataStreams
- **HIGH (Count, Boolean, Text):** Common components for counters, flags, identifiers
- **MEDIUM (Category, Ranges, Vector, DataChoice, GeometryData):** Important but less frequent
- **LOW (CategoryRange, Matrix):** Specialized components rarely used

---

## 2. Encoding-Specific Test Requirements

### 2.1 JSON Encoding Testing

**Media Type:** `application/swe+json`  
**Priority:** HIGH  
**Complexity:** Moderate

| Test Category               | Test Count | Lines per Test | Total Lines | Priority     | Notes                                              |
| --------------------------- | ---------- | -------------- | ----------- | ------------ | -------------------------------------------------- |
| Simple components (6 types) | 6          | 10-15          | 60-90       | HIGH         | Quantity, Count, Boolean, Text, Time, Category     |
| Range components (3 types)  | 3          | 10-12          | 30-36       | MEDIUM       | QuantityRange, CategoryRange, TimeRange            |
| DataRecord parsing          | 5          | 15-20          | 75-100      | **CRITICAL** | Nested fields, field validation                    |
| DataArray parsing           | 6          | 15-25          | 90-150      | **CRITICAL** | Element validation, large arrays                   |
| Vector parsing              | 2          | 12-15          | 24-30       | MEDIUM       | CRS handling, coordinates                          |
| Matrix parsing              | 2          | 12-15          | 24-30       | LOW          | 2D arrays, dimensions                              |
| DataChoice parsing          | 2          | 15-20          | 30-40       | MEDIUM       | Alternative structures                             |
| GeometryData parsing        | 2          | 12-15          | 24-30       | MEDIUM       | GeoJSON geometry types                             |
| Nested structures           | 3          | 20-25          | 60-75       | HIGH         | DataRecord in DataRecord, DataArray of DataRecords |
| Schema validation           | 5          | 12-18          | 60-90       | **CRITICAL** | Result conformance to schema                       |
| UOM handling                | 2          | 10-12          | 20-24       | HIGH         | UCUM codes, URI units                              |
| Quality information         | 2          | 12-15          | 24-30       | MEDIUM       | Quality indicators                                 |
| Nil values                  | 2          | 10-12          | 20-24       | MEDIUM       | Missing/invalid data                               |
| Error handling              | 6          | 8-12           | 48-72       | MEDIUM       | Malformed JSON, invalid types                      |
| **JSON TOTAL**              | **48**     | **~12 avg**    | **589-811** |              |                                                    |

**JSON Encoding Structure:**

**Object Mode (default):**

```json
{
  "time": "2024-01-15T12:00:00Z",
  "temp": 23.5,
  "humidity": 65.0
}
```

**Array Mode (compact):**

```json
["2024-01-15T12:00:00Z", 23.5, 65.0]
```

**Configuration:**

```json
{
  "type": "JSONEncoding",
  "includeNilValues": false
}
```

---

### 2.2 Text/CSV Encoding Testing

**Media Type:** `application/swe+csv` or `application/swe+text`  
**Priority:** HIGH  
**Complexity:** Moderate (delimiter handling)

| Test Category               | Test Count | Lines per Test | Total Lines | Priority     | Notes                               |
| --------------------------- | ---------- | -------------- | ----------- | ------------ | ----------------------------------- |
| Simple components (6 types) | 6          | 10-15          | 60-90       | HIGH         | All simple types in CSV             |
| Range components (3 types)  | 3          | 10-12          | 30-36       | MEDIUM       | Ranges in CSV                       |
| DataRecord parsing          | 5          | 15-20          | 75-100      | **CRITICAL** | Field order matters                 |
| DataArray parsing           | 6          | 15-20          | 90-120      | **CRITICAL** | Block separators                    |
| Delimiter variations        | 5          | 12-15          | 60-75       | HIGH         | Comma, tab, semicolon, custom       |
| Quoted strings              | 3          | 10-12          | 30-36       | MEDIUM       | Escaped quotes, embedded delimiters |
| Missing values              | 3          | 10-12          | 30-36       | MEDIUM       | Empty tokens, null handling         |
| Decimal separator           | 2          | 10-12          | 20-24       | LOW          | Dot vs comma                        |
| Whitespace handling         | 2          | 10-12          | 20-24       | MEDIUM       | Collapse whitespace option          |
| Block separators            | 3          | 12-15          | 36-45       | HIGH         | Record delimiters                   |
| Error handling              | 5          | 8-12           | 40-60       | MEDIUM       | Delimiter errors, parsing errors    |
| **Text TOTAL**              | **43**     | **~11 avg**    | **491-646** |              |                                     |

**Text Encoding Configuration:**

```json
{
  "type": "TextEncoding",
  "tokenSeparator": ",",
  "blockSeparator": "\n",
  "decimalSeparator": ".",
  "collapseWhiteSpaces": true
}
```

**Example CSV:**

```
2024-01-15T12:00:00Z,23.5,65.0
2024-01-15T12:01:00Z,23.6,64.8
2024-01-15T12:02:00Z,23.4,65.2
```

**Limitations:**

- No nested structures (DataRecord only at top level)
- Field order matters (defined by schema)
- Binary data not supported
- Limited string escaping

---

### 2.3 Binary Encoding Testing (MOST CRITICAL)

**Media Type:** `application/swe+binary`  
**Priority:** **CRITICAL**  
**Complexity:** Very High (byte-level precision required)

| Test Category                      | Test Count | Lines per Test | Total Lines     | Priority     | Notes                             |
| ---------------------------------- | ---------- | -------------- | --------------- | ------------ | --------------------------------- |
| **Data Type Parsing**              |
| Boolean (1 byte)                   | 2          | 12-15          | 24-30           | **CRITICAL** | 0x00/0x01                         |
| Int8/UInt8 (1 byte)                | 4          | 12-15          | 48-60           | **CRITICAL** | Signed/unsigned                   |
| Int16/UInt16 (2 bytes)             | 4          | 15-20          | 60-80           | **CRITICAL** | Big/little endian                 |
| Int32/UInt32 (4 bytes)             | 4          | 15-20          | 60-80           | **CRITICAL** | Big/little endian                 |
| Int64/UInt64 (8 bytes)             | 4          | 15-20          | 60-80           | **CRITICAL** | Big/little endian                 |
| Float32 (4 bytes, IEEE 754)        | 6          | 15-25          | 90-150          | **CRITICAL** | NaN, Inf, -Inf, denorm            |
| Float64 (8 bytes, IEEE 754)        | 6          | 15-25          | 90-150          | **CRITICAL** | NaN, Inf, -Inf, denorm            |
| String (variable length)           | 4          | 15-20          | 60-80           | HIGH         | Length-prefixed, fixed-width      |
| **Endianness Testing**             |
| Big-endian all multi-byte types    | 6          | 15-20          | 90-120          | **CRITICAL** | Explicit tests                    |
| Little-endian all multi-byte types | 6          | 15-20          | 90-120          | **CRITICAL** | Explicit tests                    |
| Mixed endianness (edge case)       | 2          | 15-20          | 30-40           | MEDIUM       | Different fields different endian |
| **Component Parsing**              |
| Quantity (float + metadata)        | 3          | 15-20          | 45-60           | **CRITICAL** | Value + UOM separate              |
| Count (integer)                    | 2          | 12-15          | 24-30           | HIGH         |                                   |
| Boolean (single byte)              | 2          | 12-15          | 24-30           | HIGH         |                                   |
| Text (string)                      | 2          | 15-20          | 30-40           | HIGH         |                                   |
| Time (int64 or string)             | 3          | 15-20          | 45-60           | **CRITICAL** | Unix epoch or ISO 8601            |
| DataRecord (structured)            | 4          | 20-25          | 80-100          | **CRITICAL** | Multi-field binary                |
| DataArray (array of binary values) | 8          | 20-30          | 160-240         | **CRITICAL** | Array parsing, block separators   |
| **Advanced Features**              |
| Block separators                   | 4          | 15-20          | 60-80           | HIGH         | Array element separation          |
| Variable-length data               | 4          | 15-20          | 60-80           | HIGH         | Length prefixes, padding          |
| Byte alignment                     | 3          | 15-20          | 45-60           | MEDIUM       | Alignment to word boundaries      |
| Base64 encoding (for transmission) | 2          | 12-15          | 24-30           | MEDIUM       | Wrap binary in Base64             |
| **Schema Validation**              |
| Result structure match             | 3          | 15-20          | 45-60           | HIGH         | Binary values match schema        |
| Type validation                    | 2          | 15-20          | 30-40           | HIGH         | Correct data types                |
| **Error Handling**                 |
| Insufficient bytes                 | 2          | 10-15          | 20-30           | **CRITICAL** | Buffer truncation                 |
| Wrong endianness detection         | 2          | 15-20          | 30-40           | HIGH         | Detect or error gracefully        |
| Invalid byte sequences             | 2          | 12-18          | 24-36           | MEDIUM       | Corrupted data                    |
| Misaligned data                    | 2          | 15-20          | 30-40           | HIGH         | Wrong byte offsets                |
| Block separator violation          | 2          | 12-15          | 24-30           | MEDIUM       | Missing/invalid separators        |
| **Binary TOTAL**                   | **96**     | **~15 avg**    | **1,447-1,896** |              |                                   |

**Binary Encoding Configuration:**

```json
{
  "type": "BinaryEncoding",
  "byteOrder": "BIG_ENDIAN",
  "byteEncoding": "RAW",
  "members": [
    { "component": "fields/time", "dataType": "INT64", "byteLength": 8 },
    { "component": "fields/temp", "dataType": "FLOAT32", "byteLength": 4 },
    { "component": "fields/humidity", "dataType": "FLOAT32", "byteLength": 4 }
  ]
}
```

**Byte Order:** BIG_ENDIAN (network byte order) or LITTLE_ENDIAN (most systems)

**Data Types:** INT8, INT16, INT32, INT64, UINT8, UINT16, UINT32, UINT64, FLOAT32, FLOAT64, UTF8, ASCII

---

## 3. Binary Encoding Byte Format Specifications

### 3.1 Integer Data Types

| Data Type           | Byte Size | Endianness | Value Range                     | Test Fixtures Needed    |
| ------------------- | --------- | ---------- | ------------------------------- | ----------------------- |
| **boolean**         | 1         | N/A        | 0x00 (false), 0x01 (true)       | 2 (false, true)         |
| **byte (int8)**     | 1         | N/A        | -128 to 127                     | 3 (-128, 0, 127)        |
| **ubyte (uint8)**   | 1         | N/A        | 0 to 255                        | 3 (0, 128, 255)         |
| **short (int16)**   | 2         | Big/Little | -32,768 to 32,767               | 6 (3 values × 2 endian) |
| **ushort (uint16)** | 2         | Big/Little | 0 to 65,535                     | 6 (3 values × 2 endian) |
| **int (int32)**     | 4         | Big/Little | -2,147,483,648 to 2,147,483,647 | 6 (3 values × 2 endian) |
| **uint (uint32)**   | 4         | Big/Little | 0 to 4,294,967,295              | 6 (3 values × 2 endian) |
| **long (int64)**    | 8         | Big/Little | -2^63 to 2^63-1                 | 6 (3 values × 2 endian) |
| **ulong (uint64)**  | 8         | Big/Little | 0 to 2^64-1                     | 6 (3 values × 2 endian) |

**Example Binary Test Fixtures:**

**Big-Endian Int16:**

```
Hex: 00 64 (big-endian)
Decimal: 100
Binary: 0000 0000 0110 0100
```

**Little-Endian Int16:**

```
Hex: 64 00 (little-endian)
Decimal: 100
Binary: 0110 0100 0000 0000 (LSB first)
```

**Big-Endian Int32:**

```
Hex: 00 00 03 E8 (big-endian)
Decimal: 1000
Binary: 0000 0000 0000 0000 0000 0011 1110 1000
```

**Little-Endian Int32:**

```
Hex: E8 03 00 00 (little-endian)
Decimal: 1000
```

---

### 3.2 Floating Point Data Types (IEEE 754)

| Data Type            | Byte Size | Endianness | Format                    | Test Fixtures Needed     |
| -------------------- | --------- | ---------- | ------------------------- | ------------------------ |
| **float (float32)**  | 4         | Big/Little | IEEE 754 single precision | 12 (6 values × 2 endian) |
| **double (float64)** | 8         | Big/Little | IEEE 754 double precision | 12 (6 values × 2 endian) |

**IEEE 754 Test Values:**

1. **Normal values:** 3.14159, -273.15, 1.0, -1.0
2. **Zero:** +0.0, -0.0
3. **Infinity:** +Infinity, -Infinity
4. **NaN:** NaN (quiet), NaN (signaling)
5. **Denormalized numbers:** Smallest non-zero positive, smallest non-zero negative
6. **Edge cases:** Largest representable, smallest representable

**Example Float32 Binary Test Fixtures:**

**Big-Endian Float32 (π ≈ 3.14159):**

```
Hex: 40 49 0F DB (big-endian)
IEEE 754: Sign=0, Exponent=128 (0x80), Mantissa=0x490FDB
Decimal: 3.14159265...
```

**Little-Endian Float32 (π):**

```
Hex: DB 0F 49 40 (little-endian)
Same value, bytes reversed
```

**Big-Endian Float32 (NaN):**

```
Hex: 7F C0 00 00 (big-endian)
Exponent: all 1s (0xFF for biased)
Mantissa: non-zero (0x400000)
Value: NaN (quiet)
```

**Big-Endian Float32 (+Infinity):**

```
Hex: 7F 80 00 00 (big-endian)
Exponent: all 1s
Mantissa: all 0s
Value: +Infinity
```

**Big-Endian Float32 (-Infinity):**

```
Hex: FF 80 00 00 (big-endian)
Sign: 1 (negative)
Exponent: all 1s
Mantissa: all 0s
Value: -Infinity
```

**Big-Endian Float64 Example:**

```
Hex: 40 09 21 FB 54 44 2D 18 (big-endian)
Value: π (double precision)
```

---

### 3.3 String Data Types

| Data Type        | Encoding    | Length Handling                | Test Fixtures Needed                      |
| ---------------- | ----------- | ------------------------------ | ----------------------------------------- |
| **ASCII string** | 7-bit ASCII | Length-prefixed or fixed-width | 4 (empty, short, long, special chars)     |
| **UTF-8 string** | UTF-8       | Length-prefixed or fixed-width | 6 (empty, ASCII, multi-byte, emoji, long) |

**Length-Prefixed String Format:**

```
[Length Bytes (1-4)] [String Bytes (UTF-8)]
```

**Example UTF-8 String:**

```
String: "Hello"
UTF-8 Bytes: 48 65 6C 6C 6F
Length-Prefixed (1-byte length): 05 48 65 6C 6C 6F
```

**Example Multi-Byte UTF-8:**

```
String: "Ω" (Greek Omega)
UTF-8 Bytes: CE A9 (2 bytes)
Length-Prefixed: 02 CE A9
```

**Fixed-Width String (10 bytes, null-padded):**

```
String: "Test"
Bytes: 54 65 73 74 00 00 00 00 00 00
```

---

## 4. Property Testing Matrices per Component Type

### 4.1 Quantity Component

**Priority:** **CRITICAL** (most common component, used in 90% of DataStreams)

| Property       | JSON     | Text                    | Binary         | Validation Rules                | Edge Cases                                             | Priority     | Spec Ref         |
| -------------- | -------- | ----------------------- | -------------- | ------------------------------- | ------------------------------------------------------ | ------------ | ---------------- |
| **value**      | Required | Required                | Required       | Numeric                         | NaN, Inf, -Inf, very large, very small, zero, negative | **CRITICAL** | SWE 3.0 §7.2.1   |
| **uom.code**   | Optional | N/A (separate encoding) | N/A (separate) | UCUM code or URI                | Missing, invalid code, unrecognized unit               | HIGH         | SWE 3.0 §7.2.1.4 |
| **uom.href**   | Optional | N/A                     | N/A            | Valid URI                       | Relative URI, missing                                  | LOW          | SWE 3.0 §7.2.1.4 |
| **constraint** | Optional | N/A                     | N/A            | AllowedIntervals object         | Invalid intervals, out of range                        | MEDIUM       | SWE 3.0 §7.2.1.5 |
| **nilValues**  | Optional | Optional                | Optional       | Array of NilValue objects       | Invalid reasons, missing values                        | MEDIUM       | SWE 3.0 §7.2.1.6 |
| **quality**    | Optional | Optional                | Optional       | Array of quality components     | Missing, invalid structure                             | LOW          | SWE 3.0 §7.2.1.7 |
| **definition** | Optional | N/A                     | N/A            | Valid URI (observable property) | Relative URI, missing                                  | MEDIUM       | SWE 3.0 §7.2.1.2 |
| **label**      | Optional | N/A                     | N/A            | String                          | Missing, very long                                     | LOW          | SWE 3.0 §7.2.1.1 |

**Test Scenarios:**

1. **Normal value:** `{"type": "Quantity", "value": 23.5, "uom": {"code": "Cel"}}`
2. **Zero value:** `{"type": "Quantity", "value": 0.0, "uom": {"code": "Cel"}}`
3. **Negative value:** `{"type": "Quantity", "value": -40.0, "uom": {"code": "Cel"}}`
4. **NaN (nil value):** `{"type": "Quantity", "value": "NaN", "nilValues": [{"reason": "missing", "value": "NaN"}]}`
5. **Infinity:** `{"type": "Quantity", "value": "Infinity"}`
6. **With constraint:** `{"type": "Quantity", "value": 50.0, "uom": {"code": "%"}, "constraint": {"interval": [0, 100]}}`
7. **With quality:** `{"type": "Quantity", "value": 23.5, "quality": [{"type": "Quantity", "value": 0.1, "uom": {"code": "Cel"}, "definition": "accuracy"}]}`

**Binary Encoding:**

- **Float32:** 4 bytes (big-endian or little-endian)
- **Float64:** 8 bytes (big-endian or little-endian)
- **UOM:** Encoded separately in schema, not in binary data

---

### 4.2 Count Component

**Priority:** HIGH (common for counters, indices)

| Property       | JSON     | Text     | Binary   | Validation Rules                  | Edge Cases                       | Priority     |
| -------------- | -------- | -------- | -------- | --------------------------------- | -------------------------------- | ------------ |
| **value**      | Required | Required | Required | Integer                           | 0, negative, very large, max int | **CRITICAL** |
| **constraint** | Optional | N/A      | N/A      | AllowedValues or AllowedIntervals | Out of range, invalid values     | MEDIUM       |
| **nilValues**  | Optional | Optional | Optional | Array of NilValue objects         | Missing values                   | LOW          |
| **definition** | Optional | N/A      | N/A      | Valid URI                         | Missing                          | LOW          |

**Test Scenarios:**

1. **Positive count:** `{"type": "Count", "value": 42}`
2. **Zero count:** `{"type": "Count", "value": 0}`
3. **Negative count:** `{"type": "Count", "value": -5}` (if allowed)
4. **Large count:** `{"type": "Count", "value": 1000000}`
5. **With constraint:** `{"type": "Count", "value": 5, "constraint": {"interval": [0, 10]}}`

**Binary Encoding:**

- **Int32:** 4 bytes (signed integer, big/little endian)
- **Int64:** 8 bytes (for very large counts)

---

### 4.3 Boolean Component

**Priority:** HIGH (common for flags, status)

| Property       | JSON     | Text     | Binary   | Validation Rules | Edge Cases                       | Priority     |
| -------------- | -------- | -------- | -------- | ---------------- | -------------------------------- | ------------ |
| **value**      | Required | Required | Required | true or false    | String "true"/"false" vs boolean | **CRITICAL** |
| **definition** | Optional | N/A      | N/A      | Valid URI        | Missing                          | LOW          |

**Test Scenarios:**

1. **True:** `{"type": "Boolean", "value": true}`
2. **False:** `{"type": "Boolean", "value": false}`
3. **String true (should error):** `{"type": "Boolean", "value": "true"}` - type error

**Binary Encoding:**

- **1 byte:** 0x00 (false), 0x01 (true)

---

### 4.4 Text Component

**Priority:** HIGH (common for identifiers, codes)

| Property       | JSON     | Text     | Binary   | Validation Rules         | Edge Cases                                           | Priority |
| -------------- | -------- | -------- | -------- | ------------------------ | ---------------------------------------------------- | -------- |
| **value**      | Required | Required | Required | String                   | Empty string, very long, special characters, Unicode | HIGH     |
| **constraint** | Optional | N/A      | N/A      | AllowedTokens or pattern | Invalid pattern, not in allowed list                 | MEDIUM   |
| **definition** | Optional | N/A      | N/A      | Valid URI                | Missing                                              | LOW      |

**Test Scenarios:**

1. **Normal text:** `{"type": "Text", "value": "CLEAR_SKY"}`
2. **Empty text:** `{"type": "Text", "value": ""}`
3. **Long text:** `{"type": "Text", "value": "Very long description..."}`
4. **Unicode text:** `{"type": "Text", "value": "Hello 世界 🌍"}`
5. **With constraint:** `{"type": "Text", "value": "CLOUDY", "constraint": {"allowedTokens": ["CLEAR_SKY", "CLOUDY", "RAINY"]}}`

**Binary Encoding:**

- **UTF-8 encoded:** Length prefix (1-4 bytes) + UTF-8 bytes
- **Fixed-width:** Fixed byte array, null-padded

---

### 4.5 Time Component

**Priority:** **CRITICAL** (used in all time-series observations)

| Property           | JSON                     | Text     | Binary   | Validation Rules             | Edge Cases                                      | Priority     |
| ------------------ | ------------------------ | -------- | -------- | ---------------------------- | ----------------------------------------------- | ------------ |
| **value**          | Required                 | Required | Required | ISO 8601 instant or interval | Invalid format, timezone handling, leap seconds | **CRITICAL** |
| **referenceFrame** | Optional                 | N/A      | N/A      | Valid URI (UTC, TAI, GPS)    | Missing, invalid                                | MEDIUM       |
| **uom**            | Optional (for durations) | N/A      | N/A      | Time unit (s, min, h, d, a)  | Missing for duration                            | LOW          |
| **definition**     | Optional                 | N/A      | N/A      | Valid URI                    | Missing                                         | LOW          |

**Test Scenarios:**

1. **ISO 8601 instant:** `{"type": "Time", "value": "2024-01-15T12:00:00Z"}`
2. **With timezone:** `{"type": "Time", "value": "2024-01-15T12:00:00+01:00"}`
3. **Fractional seconds:** `{"type": "Time", "value": "2024-01-15T12:00:00.123Z"}`
4. **Interval:** `{"type": "Time", "value": "2024-01-15T12:00:00Z/2024-01-15T13:00:00Z"}`
5. **Duration:** `{"type": "Time", "value": "PT1H30M", "uom": {"code": "s"}}`
6. **Reference frame:** `{"type": "Time", "value": "2024-01-15T12:00:00Z", "referenceFrame": "http://www.opengis.net/def/trs/BIPM/0/UTC"}`

**Binary Encoding:**

- **Unix epoch (Int64):** Milliseconds since 1970-01-01T00:00:00Z (8 bytes)
- **String (UTF-8):** Length-prefixed ISO 8601 string

---

### 4.6 Category Component

**Priority:** MEDIUM (used for enumerated types, classification codes)

| Property       | JSON     | Text     | Binary   | Validation Rules       | Edge Cases                               | Priority |
| -------------- | -------- | -------- | -------- | ---------------------- | ---------------------------------------- | -------- |
| **value**      | Required | Required | Required | String from codeSpace  | Not in allowed values, missing codeSpace | HIGH     |
| **codeSpace**  | Optional | N/A      | N/A      | Valid URI (vocabulary) | Missing, unreachable                     | HIGH     |
| **constraint** | Optional | N/A      | N/A      | AllowedTokens          | Value not in list                        | MEDIUM   |
| **definition** | Optional | N/A      | N/A      | Valid URI              | Missing                                  | LOW      |

**Test Scenarios:**

1. **Simple category:** `{"type": "Category", "value": "cloudy"}`
2. **With codeSpace:** `{"type": "Category", "value": "cloudy", "codeSpace": "http://example.org/weather-codes"}`
3. **With constraint:** `{"type": "Category", "value": "CLEAR", "constraint": {"allowedTokens": ["CLEAR", "CLOUDY", "RAINY"]}}`

**Binary Encoding:**

- **String (UTF-8):** Length-prefixed category code
- **Integer index:** If categories enumerated in schema (1 byte = 256 categories, 2 bytes = 65k categories)

---

### 4.7 DataRecord Component (Complex)

**Priority:** **CRITICAL** (most common complex type, multi-field observations)

| Property          | JSON     | Text     | Binary   | Validation Rules              | Edge Cases                                   | Priority     |
| ----------------- | -------- | -------- | -------- | ----------------------------- | -------------------------------------------- | ------------ |
| **fields**        | Required | Required | Required | Array of field definitions    | Empty fields, duplicate names, unknown types | **CRITICAL** |
| **fields[].name** | Required | N/A      | N/A      | String (unique within record) | Duplicate names, empty name                  | HIGH         |
| **fields[].type** | Required | N/A      | N/A      | Valid SWE component type      | Unknown type                                 | HIGH         |
| **definition**    | Optional | N/A      | N/A      | Valid URI                     | Missing                                      | LOW          |

**Test Scenarios:**

1. **Simple DataRecord (3 fields):**

   ```json
   {
     "type": "DataRecord",
     "fields": [
       { "name": "time", "type": "Time", "value": "2024-01-15T12:00:00Z" },
       {
         "name": "temp",
         "type": "Quantity",
         "value": 23.5,
         "uom": { "code": "Cel" }
       },
       {
         "name": "humidity",
         "type": "Quantity",
         "value": 65.0,
         "uom": { "code": "%" }
       }
     ]
   }
   ```

2. **Nested DataRecord (2 levels):**

   ```json
   {
     "type": "DataRecord",
     "fields": [
       { "name": "time", "type": "Time", "value": "2024-01-15T12:00:00Z" },
       {
         "name": "weather",
         "type": "DataRecord",
         "fields": [
           {
             "name": "temp",
             "type": "Quantity",
             "value": 23.5,
             "uom": { "code": "Cel" }
           },
           {
             "name": "humidity",
             "type": "Quantity",
             "value": 65.0,
             "uom": { "code": "%" }
           }
         ]
       }
     ]
   }
   ```

3. **Deep nesting (3 levels):**

   ```json
   {
     "type": "DataRecord",
     "fields": [
       {
         "name": "station",
         "type": "DataRecord",
         "fields": [
           {
             "name": "location",
             "type": "DataRecord",
             "fields": [
               { "name": "lat", "type": "Quantity", "value": 37.42 },
               { "name": "lon", "type": "Quantity", "value": -122.08 }
             ]
           }
         ]
       }
     ]
   }
   ```

4. **Mixed field types:**
   ```json
   {
     "type": "DataRecord",
     "fields": [
       { "name": "time", "type": "Time", "value": "2024-01-15T12:00:00Z" },
       { "name": "count", "type": "Count", "value": 42 },
       { "name": "flag", "type": "Boolean", "value": true },
       { "name": "code", "type": "Text", "value": "OK" }
     ]
   }
   ```

**Binary Encoding:**

- **Sequential field values:** Each field encoded according to its type
- **No field names in binary:** Schema defines field order
- **Nested records:** Recursive encoding

---

### 4.8 DataArray Component (Complex)

**Priority:** **CRITICAL** (time series, observation arrays)

| Property         | JSON     | Text     | Binary   | Validation Rules             | Edge Cases                                      | Priority     |
| ---------------- | -------- | -------- | -------- | ---------------------------- | ----------------------------------------------- | ------------ |
| **elementType**  | Required | Required | Required | Valid SWE component (schema) | Unknown type, complex element                   | HIGH         |
| **elementCount** | Optional | N/A      | N/A      | Count component (size)       | Missing, mismatch with actual                   | MEDIUM       |
| **values**       | Required | Required | Required | Array of values              | Empty array, large array (1000+), type mismatch | **CRITICAL** |
| **encoding**     | Optional | Required | Required | Encoding definition          | Missing in Text/Binary                          | HIGH         |
| **definition**   | Optional | N/A      | N/A      | Valid URI                    | Missing                                         | LOW          |

**Test Scenarios:**

1. **Simple array (10 values):**

   ```json
   {
     "type": "DataArray",
     "elementCount": { "type": "Count", "value": 10 },
     "elementType": { "type": "Quantity", "uom": { "code": "Cel" } },
     "values": [23.5, 23.6, 23.4, 23.7, 23.3, 23.8, 23.2, 23.9, 23.1, 24.0]
   }
   ```

2. **Array of records:**

   ```json
   {
     "type": "DataArray",
     "elementType": {
       "type": "DataRecord",
       "fields": [
         { "name": "time", "type": "Time" },
         { "name": "temp", "type": "Quantity", "uom": { "code": "Cel" } }
       ]
     },
     "values": [
       ["2024-01-15T12:00:00Z", 23.5],
       ["2024-01-15T12:01:00Z", 23.6],
       ["2024-01-15T12:02:00Z", 23.4]
     ]
   }
   ```

3. **Large array (1000 elements):** Test performance, memory usage

4. **Empty array:**
   ```json
   {
     "type": "DataArray",
     "elementCount": { "type": "Count", "value": 0 },
     "elementType": { "type": "Quantity", "uom": { "code": "Cel" } },
     "values": []
   }
   ```

**Binary Encoding:**

- **Element count (optional):** 4-byte int32 at start
- **Sequential elements:** Each element encoded per elementType
- **Block separators (optional):** Byte sequence between elements
- **Array of records:** Nested binary encoding

---

### 4.9 Vector Component (Complex)

**Priority:** MEDIUM (3D positions, velocities)

| Property           | JSON     | Text     | Binary   | Validation Rules             | Edge Cases                         | Priority |
| ------------------ | -------- | -------- | -------- | ---------------------------- | ---------------------------------- | -------- |
| **coordinates**    | Required | Required | Required | Array of Quantity components | Wrong dimension count, missing UOM | HIGH     |
| **referenceFrame** | Optional | N/A      | N/A      | Valid CRS URI (EPSG code)    | Missing, invalid CRS               | MEDIUM   |
| **definition**     | Optional | N/A      | N/A      | Valid URI                    | Missing                            | LOW      |

**Test Scenarios:**

1. **3D position:**

   ```json
   {
     "type": "Vector",
     "referenceFrame": "http://www.opengis.net/def/crs/EPSG/0/4979",
     "coordinates": [
       {
         "name": "lat",
         "type": "Quantity",
         "value": 37.42,
         "uom": { "code": "deg" }
       },
       {
         "name": "lon",
         "type": "Quantity",
         "value": -122.08,
         "uom": { "code": "deg" }
       },
       {
         "name": "h",
         "type": "Quantity",
         "value": 25.5,
         "uom": { "code": "m" }
       }
     ]
   }
   ```

2. **2D position (lat/lon only):**
   ```json
   {
     "type": "Vector",
     "referenceFrame": "http://www.opengis.net/def/crs/EPSG/0/4326",
     "coordinates": [
       {
         "name": "lat",
         "type": "Quantity",
         "value": 37.42,
         "uom": { "code": "deg" }
       },
       {
         "name": "lon",
         "type": "Quantity",
         "value": -122.08,
         "uom": { "code": "deg" }
       }
     ]
   }
   ```

**Binary Encoding:**

- **Sequential coordinates:** Each coordinate as Float32 or Float64
- **Coordinate count implied by schema**

---

## 5. Nested Structure Testing

| Nesting Scenario                               | Complexity | JSON Fixture | Text Fixture | Binary Fixture | Test Lines | Priority     |
| ---------------------------------------------- | ---------- | ------------ | ------------ | -------------- | ---------- | ------------ |
| **DataRecord Nesting**                         |
| DataRecord with 5 simple fields                | Low        | Required     | Required     | Required       | 30-45      | **CRITICAL** |
| DataRecord within DataRecord (2 levels)        | Medium     | Required     | Required     | Required       | 45-60      | HIGH         |
| DataRecord within DataRecord (3 levels)        | High       | Required     | Required     | Required       | 60-90      | MEDIUM       |
| DataRecord within DataRecord (4+ levels)       | Very High  | Optional     | N/A          | Optional       | 90-120     | LOW          |
| **DataArray Nesting**                          |
| DataArray of simple values (10 elements)       | Low        | Required     | Required     | Required       | 30-45      | **CRITICAL** |
| DataArray of simple values (100 elements)      | Medium     | Required     | Required     | Required       | 45-60      | HIGH         |
| DataArray of simple values (1000+ elements)    | High       | Optional     | Optional     | Required       | 60-90      | MEDIUM       |
| DataArray of DataRecords (10 records)          | High       | Required     | Required     | Required       | 60-90      | **CRITICAL** |
| DataArray of DataRecords (100 records)         | Very High  | Required     | Required     | Required       | 90-120     | HIGH         |
| DataArray of DataArrays (nested arrays)        | Very High  | Optional     | N/A          | Optional       | 90-120     | MEDIUM       |
| **Mixed Nesting**                              |
| DataRecord containing DataArray                | High       | Required     | Required     | Required       | 60-90      | HIGH         |
| DataArray of DataRecords containing DataArrays | Very High  | Optional     | N/A          | Optional       | 120-180    | LOW          |

**Nesting Strategy:**

- **Test 1-2 levels:** Comprehensive coverage (CRITICAL/HIGH priority)
- **Test 3 levels:** Representative scenarios (MEDIUM priority)
- **Test 4+ levels:** Edge cases only (LOW priority)
- **Stack overflow prevention:** Iterative parsing with depth limits (e.g., max 10 levels)

**Performance Considerations:**

- **Large arrays (1000+ elements):** Test memory usage, parsing time
- **Deep nesting (4+ levels):** Test stack usage, recursion depth
- **Streaming:** Incremental parsing for large datasets

---

## 6. Schema Validation Testing

> **⚠️ REVIEW NOTICE (Phase 2D, H1):** Schema validation (checking whether observation results conform to DataStream schemas) is a legitimate parser concern — the parser needs to know the schema shape to correctly dispatch component parsing. However, **constraint validation** entries below ("Value within allowed interval," "UCUM codes valid," "Temporal validation") are server data quality checks, not parser concerns. The parser should extract values as-is. Retain structural schema matching (field count, types, order) as parser logic; remove constraint/unit/temporal validation.

| Validation Scenario                        | Test Requirement                       | Expected Result              | Priority     | Spec Ref           |
| ------------------------------------------ | -------------------------------------- | ---------------------------- | ------------ | ------------------ |
| **Structure Validation**                   |
| Values match schema exactly                | Field count, types, order all correct  | Pass                         | **CRITICAL** | CSAPI Part 2, §7.2 |
| Schema has optional field, value missing   | Field not in observation               | Pass                         | HIGH         | SWE 3.0 §7         |
| Schema has optional field, value present   | Field in observation with correct type | Pass                         | HIGH         | SWE 3.0 §7         |
| Value has extra field not in schema        | Observation has unknown field          | Warn or error (configurable) | MEDIUM       | CSAPI Part 2       |
| Value missing required field               | Required field absent                  | Error                        | **CRITICAL** | SWE 3.0 §7         |
| Value field type mismatch                  | String value for Quantity field        | Error                        | **CRITICAL** | SWE 3.0 §7         |
| **Array Validation**                       |
| DataArray element count matches schema     | elementCount = actual array length     | Pass                         | HIGH         | SWE 3.0 §7.4       |
| DataArray element count mismatch           | elementCount ≠ array length            | Warn or error                | MEDIUM       | SWE 3.0 §7.4       |
| DataArray element type mismatch            | Element not matching elementType       | Error                        | **CRITICAL** | SWE 3.0 §7.4       |
| **Constraint Validation**                  |
| Value within allowed interval              | Value between min and max              | Pass                         | HIGH         | SWE 3.0 §7.2       |
| Value outside allowed interval             | Value < min or > max                   | Error                        | HIGH         | SWE 3.0 §7.2       |
| Value in allowed tokens list               | Categorical value in list              | Pass                         | MEDIUM       | SWE 3.0 §7.2       |
| Value not in allowed tokens list           | Categorical value not in list          | Error                        | MEDIUM       | SWE 3.0 §7.2       |
| **DataChoice Validation**                  |
| DataChoice selection matches schema option | Selected item valid per schema         | Pass                         | MEDIUM       | SWE 3.0 §7.7       |
| DataChoice selection invalid               | Selected item not in schema options    | Error                        | MEDIUM       | SWE 3.0 §7.7       |
| **Quality Validation**                     |
| Quality indicators follow schema           | Quality components valid               | Pass                         | LOW          | SWE 3.0 §7.2       |
| Quality indicators malformed               | Invalid quality structure              | Error                        | LOW          | SWE 3.0 §7.2       |
| **Temporal Validation**                    |
| Timestamps follow ISO 8601                 | Valid ISO 8601 format                  | Pass                         | HIGH         | ISO 8601           |
| Timestamps invalid format                  | Non-ISO 8601 string                    | Error                        | HIGH         | ISO 8601           |
| **Unit Validation**                        |
| UCUM codes valid                           | Recognized UCUM code                   | Pass                         | MEDIUM       | UCUM spec          |
| UCUM codes invalid                         | Unrecognized UCUM code                 | Warn                         | LOW          | UCUM spec          |

**Schema Validation Test Organization:**

- **Separate test file:** `swe-common-schema-validation.spec.ts` (96-120 lines, 8 tests)
- **Schema fixtures:** `fixtures/swe-common/schemas/` (10-15 schemas)
- **Observation fixtures:** `fixtures/swe-common/observations/` (matching observations for validation)

---

## 7. Error Condition Testing per Encoding

> **⚠️ REVIEW NOTICE (Phase 2D, H1):** The 22 ERR-SWE-\* IDs below mix two categories:
>
> **Retain as genuine parser errors:** ERR-SWE-JSON-001 (malformed JSON), ERR-SWE-JSON-003/004 (type errors preventing parsing), ERR-SWE-TEXT-001/002 (delimiter errors), ERR-SWE-TEXT-005 (unmatched quotes), ERR-SWE-BIN-001 (insufficient bytes), ERR-SWE-BIN-004 (misaligned data), ERR-SWE-BIN-009 (invalid UTF-8), ERR-SWE-BIN-010 (data length mismatch). These represent structural failures where the parser genuinely cannot produce output.
>
> **Reclassify as non-errors:** ERR-SWE-JSON-002 (missing optional-like property), ERR-SWE-JSON-005 (UOM format), ERR-SWE-JSON-006 (constraint violation), ERR-SWE-TEXT-003/004 (value format), ERR-SWE-BIN-003 (NaN-like sequences), ERR-SWE-BIN-007 (integer overflow). The parser should extract whatever is there, not validate it.
>
> These IDs are retained as **reference material** for understanding error modes, not as test case identifiers.

### 7.1 JSON Encoding Errors

| Error ID           | Error Condition           | Test Scenario                              | Expected Error               | Priority | Error Message Example                                       |
| ------------------ | ------------------------- | ------------------------------------------ | ---------------------------- | -------- | ----------------------------------------------------------- |
| **Malformed JSON** |
| ERR-SWE-JSON-001   | Invalid JSON syntax       | Malformed JSON document                    | Parse error with line/column | HIGH     | "Invalid JSON at line 5, column 12: unexpected token '}'"   |
| ERR-SWE-JSON-002   | Missing required property | Quantity without value                     | Validation error             | HIGH     | "Missing required property 'value' in Quantity component"   |
| ERR-SWE-JSON-003   | Invalid type              | value = "23.5" (string) instead of number  | Type error                   | HIGH     | "Invalid type for 'value': expected number, got string"     |
| ERR-SWE-JSON-004   | Unknown component type    | type = "UnknownComponent"                  | Error or warning             | MEDIUM   | "Unknown SWE Common component type 'UnknownComponent'"      |
| ERR-SWE-JSON-005   | Invalid UOM format        | uom = "Celsius" (string) instead of object | Validation error             | MEDIUM   | "Invalid UOM format: expected object with 'code' or 'href'" |
| ERR-SWE-JSON-006   | Constraint violation      | Value outside allowed interval             | Validation error             | HIGH     | "Value 150.0 outside allowed interval [0, 100]"             |

---

### 7.2 Text Encoding Errors

| Error ID             | Error Condition         | Test Scenario                 | Expected Error                 | Priority | Error Message Example                                   |
| -------------------- | ----------------------- | ----------------------------- | ------------------------------ | -------- | ------------------------------------------------------- |
| **Delimiter Errors** |
| ERR-SWE-TEXT-001     | Incorrect delimiter     | Expected comma, got tab       | Parse error                    | HIGH     | "Expected delimiter ',' at position 15, got '\t'"       |
| ERR-SWE-TEXT-002     | Missing block separator | No newline between records    | Parse error                    | MEDIUM   | "Missing block separator at end of record 5"            |
| **Value Errors**     |
| ERR-SWE-TEXT-003     | Missing value           | "1.5,,3.7" (empty token)      | Missing value error or default | HIGH     | "Missing value at field 2 in record 3"                  |
| ERR-SWE-TEXT-004     | Invalid numeric format  | "1.5.3" (double decimal)      | Parse error                    | MEDIUM   | "Invalid numeric format '1.5.3' at field 1"             |
| ERR-SWE-TEXT-005     | Unmatched quotes        | "text without closing quote   | Parse error                    | MEDIUM   | "Unmatched quote at position 10"                        |
| ERR-SWE-TEXT-006     | Field count mismatch    | 2 fields in schema, 3 in data | Validation error               | HIGH     | "Field count mismatch: schema has 2 fields, data has 3" |

---

### 7.3 Binary Encoding Errors (CRITICAL)

| Error ID              | Error Condition              | Test Scenario                               | Expected Error                       | Priority     | Error Message Example                                                      |
| --------------------- | ---------------------------- | ------------------------------------------- | ------------------------------------ | ------------ | -------------------------------------------------------------------------- |
| **Byte-Level Errors** |
| ERR-SWE-BIN-001       | Insufficient bytes           | Buffer ends mid-value (truncated)           | Truncation error                     | **CRITICAL** | "Insufficient bytes to read Float32 at offset 12: expected 4 bytes, got 2" |
| ERR-SWE-BIN-002       | Wrong endianness detection   | Parse as big-endian when little-endian      | Wrong value (should detect or error) | HIGH         | "Possible endianness mismatch: value 0x12345678 outside expected range"    |
| ERR-SWE-BIN-003       | Invalid byte sequence        | 0xFF 0xFF 0xFF 0xFF (could be NaN or error) | Handle gracefully (NaN) or error     | MEDIUM       | "Invalid byte sequence at offset 20: 0xFFFFFFFF"                           |
| ERR-SWE-BIN-004       | Misaligned data              | Wrong byte offset for data type             | Parse error or wrong value           | HIGH         | "Misaligned data at offset 17: Float32 should start at 4-byte boundary"    |
| ERR-SWE-BIN-005       | Block separator violation    | Missing separator between array elements    | Parse error                          | MEDIUM       | "Missing block separator after array element 5"                            |
| ERR-SWE-BIN-006       | Encoding definition mismatch | Binary data doesn't match encoding def      | Validation error                     | HIGH         | "Binary data structure doesn't match encoding definition"                  |
| **Data Type Errors**  |
| ERR-SWE-BIN-007       | Integer overflow             | Value exceeds int32 range                   | Overflow error or warning            | MEDIUM       | "Integer overflow at offset 10: value exceeds INT32_MAX"                   |
| ERR-SWE-BIN-008       | NaN in non-float context     | NaN byte sequence for integer type          | Error                                | MEDIUM       | "Invalid NaN value for integer type at offset 15"                          |
| ERR-SWE-BIN-009       | Invalid string encoding      | Non-UTF-8 bytes in string                   | Encoding error                       | HIGH         | "Invalid UTF-8 sequence at offset 25"                                      |
| **Schema Mismatch**   |
| ERR-SWE-BIN-010       | Data length mismatch         | Binary data length ≠ schema-defined length  | Validation error                     | HIGH         | "Data length mismatch: expected 16 bytes, got 20"                          |

**Total Error Scenarios:** 22 scenarios (9 CRITICAL/HIGH, 10 MEDIUM, 3 LOW)

---

## 8. Specification Example Fixtures

**Source:** SWE Common 3.0 Specification (OGC 24-014)

| Spec Section                       | Example Type         | Encoding | Component Type | Complexity | Usable | Notes                                        |
| ---------------------------------- | -------------------- | -------- | -------------- | ---------- | ------ | -------------------------------------------- |
| **SWE 3.0 Specification Examples** |
| §7.2.1                             | Quantity             | JSON     | Quantity       | Simple     | ✅ Yes | Temperature with UOM, constraint, nil values |
| §7.2.2                             | Count                | JSON     | Count          | Simple     | ✅ Yes | Particle count with constraint               |
| §7.2.3                             | Boolean              | JSON     | Boolean        | Simple     | ✅ Yes | Status flag                                  |
| §7.2.4                             | Text                 | JSON     | Text           | Simple     | ✅ Yes | Station ID with pattern constraint           |
| §7.2.5                             | Time                 | JSON     | Time           | Simple     | ✅ Yes | ISO 8601 timestamp with reference frame      |
| §7.2.6                             | Category             | JSON     | Category       | Simple     | ✅ Yes | Weather code with codeSpace                  |
| §7.3.1                             | QuantityRange        | JSON     | QuantityRange  | Simple     | ✅ Yes | Temperature range                            |
| §7.4.1                             | DataRecord           | JSON     | DataRecord     | Medium     | ✅ Yes | Weather observation (3-5 fields)             |
| §7.4.2                             | DataRecord nested    | JSON     | DataRecord     | High       | ✅ Yes | Hierarchical structure (2-3 levels)          |
| §7.5.1                             | DataArray            | JSON     | DataArray      | High       | ✅ Yes | Time series (10-20 observations)             |
| §7.5.2                             | DataArray of records | JSON     | DataArray      | Very High  | ✅ Yes | Array of structured observations             |
| §7.6.1                             | Vector               | JSON     | Vector         | Medium     | ✅ Yes | 3D position (lat/lon/height)                 |
| §7.7.1                             | DataChoice           | JSON     | DataChoice     | Medium     | ✅ Yes | Alternative measurement modes                |
| **CSAPI Part 2 Examples**          |
| Part 2, §7.2.1                     | Observation result   | JSON     | DataRecord     | Medium     | ✅ Yes | Complete observation with metadata           |
| Part 2, §7.2.2                     | Observation result   | Text     | DataArray      | High       | ✅ Yes | CSV-format observations (10 records)         |
| Part 2, §7.2.3                     | Observation result   | Binary   | DataArray      | Very High  | ✅ Yes | Binary observation array with encoding def   |
| Part 2, §7.3.1                     | DataStream schema    | JSON     | DataRecord     | Medium     | ✅ Yes | Result schema definition                     |
| Part 2, §7.3.2                     | Text encoding def    | JSON     | TextEncoding   | Simple     | ✅ Yes | CSV encoding configuration                   |
| Part 2, §7.3.3                     | Binary encoding def  | JSON     | BinaryEncoding | High       | ✅ Yes | Binary encoding configuration with members   |

**Total Spec Examples:** 19 usable fixtures from specifications

**Fixture Extraction Strategy:**

1. Copy examples verbatim from SWE Common 3.0 and CSAPI Part 2 specifications
2. Add fixture metadata (source, section, type, complexity, encoding)
3. Validate against SWE Common 3.0 JSON schema (for JSON encoding)
4. Create complementary Text and Binary versions for examples that have JSON only
5. For binary examples, include hex dumps and expected parsed results

---

## 9. OpenSensorHub Fixture Inventory

> **⚠️ REVIEW NOTICE (Phase 2D, H2):** This section plans to source fixtures from the OpenSensorHub demo server (`https://api.georobotix.io/ogc/t18/api`) — this is anti-pattern AP2 (Hybrid Fixture/Live). Upstream tests use no live server dependencies; fixtures are static files versioned with the code. **Do not fetch fixtures from live servers.** If spec examples are insufficient, create realistic fixtures manually based on spec schemas. The two-tier assertion strategy ("Spec examples: MUST pass" vs "OpenSensorHub examples: SHOULD handle gracefully") should also not be used — all fixtures should have the same assertion rigor.
>
> The analysis below is retained as reference for understanding real-world SWE Common complexity, but should NOT drive fixture sourcing.

**Source (REFERENCE ONLY — do not use for fixture sourcing):** OpenSensorHub Demo Server (https://api.georobotix.io/ogc/t18/api)

| Resource URL                                                | Encoding    | Component Type              | Complexity  | Usable     | Priority     | Notes                                    |
| ----------------------------------------------------------- | ----------- | --------------------------- | ----------- | ---------- | ------------ | ---------------------------------------- |
| **DataStreams Endpoints (Schema)**                          |
| `/datastreams`                                              | JSON        | N/A                         | N/A         | ✅ Yes     | MEDIUM       | List of datastreams with result schemas  |
| `/datastreams/{id}/schema`                                  | JSON        | DataRecord                  | Medium-High | ✅ Yes     | HIGH         | Result schema definitions                |
| `/datastreams/{id}/schema?obsFormat=application/swe+json`   | JSON        | DataRecord + JSONEncoding   | Medium      | ✅ Yes     | HIGH         | JSON encoding schema                     |
| `/datastreams/{id}/schema?obsFormat=application/swe+csv`    | JSON        | DataRecord + TextEncoding   | Medium      | ✅ Yes     | HIGH         | Text encoding schema with delimiters     |
| `/datastreams/{id}/schema?obsFormat=application/swe+binary` | JSON        | DataRecord + BinaryEncoding | High        | ✅ Yes     | **CRITICAL** | Binary encoding schema with byte formats |
| **Observations Endpoints (Data)**                           |
| `/datastreams/{id}/observations?encoding=json`              | JSON        | DataArray                   | Medium-High | ✅ Yes     | HIGH         | Real temperature/weather observations    |
| `/datastreams/{id}/observations?encoding=text`              | Text        | DataArray                   | Medium      | ✅ Yes     | HIGH         | CSV-format observations                  |
| `/datastreams/{id}/observations?encoding=binary`            | Binary      | DataArray                   | High        | ✅ Yes     | **CRITICAL** | Binary observation array (MUST TEST)     |
| `/datastreams/{id}/observations?limit=10`                   | JSON        | DataArray                   | Medium      | ✅ Yes     | MEDIUM       | Small result set for testing             |
| `/datastreams/{id}/observations?limit=1000`                 | JSON/Binary | DataArray                   | Very High   | ⚠️ Partial | LOW          | Large result set (performance test)      |

**OpenSensorHub Analysis Strategy:**

1. **Fetch sample datastreams** from `/datastreams` (limit=10)
2. **Request schemas per encoding** via `/datastreams/{id}/schema?obsFormat=...`
3. **Fetch observations in all 3 encodings** from `/datastreams/{id}/observations?encoding=...`
4. **Analyze structure complexity:**
   - Field count (simple vs complex)
   - Nesting depth (flat vs hierarchical)
   - Data types used (simple components vs complex)
   - Encoding specifications (delimiters, byte formats, endianness)
5. **Document issues:**
   - Non-standard extensions
   - Validation failures
   - Encoding inconsistencies
6. **Extract representative samples** (5-10 datastreams) covering:
   - Simple sensors (single value, e.g., thermometer)
   - Complex sensors (multi-field, e.g., weather station)
   - Various data types (Quantity, Count, Boolean, Text, Time, Category)
   - Different encodings (JSON, Text, Binary)

**Expected OpenSensorHub Findings:**

- **Real-world complexity:** More fields than spec examples (5-15 fields common)
- **Binary encoding examples:** **CRITICAL** - validate byte-level parsing with real data
- **Non-standard extensions:** Custom properties beyond SWE 3.0 spec
- **Encoding variations:** Different delimiter choices, endianness preferences
- **Performance data:** Large observation arrays for performance testing

**Fixture Sourcing Strategy (CORRECTED per Phase 2D):**

- **Spec examples:** Primary fixture source — extract from SWE Common 3.0 and CSAPI Part 2 specs
- **Hand-crafted fixtures:** Secondary source — create realistic fixtures for edge cases, error scenarios, and encoding variations not covered by spec examples
- ~~**OpenSensorHub examples:** Real-world validation (SHOULD handle gracefully)~~ → Do not source fixtures from live servers
- **Assertion rigor:** All fixtures receive the same assertion treatment — no two-tier MUST/SHOULD distinction

---

## 10. Test Organization

### 10.1 Test File Structure

**4 Test Files (Total: 1,700-2,500 lines)**

1. **`swe-common-json.spec.ts`** (JSON encoding - 589-811 lines, 48 tests)
2. **`swe-common-text.spec.ts`** (Text encoding - 491-646 lines, 43 tests)
3. **`swe-common-binary.spec.ts`** (Binary encoding - 1,447-1,896 lines, 96 tests) **[LARGEST FILE]**
4. **`swe-common-schema-validation.spec.ts`** (Schema validation - 96-120 lines, 8 tests)

---

### 10.2 Binary Test File Structure (Most Critical)

```typescript
describe('SWE Common Binary Encoding', () => {
  describe('Data Type Parsing', () => {
    describe('Boolean (1 byte)', () => {
      it('should parse false (0x00)');
      it('should parse true (0x01)');
    });

    describe('Integer Types', () => {
      describe('Int8 (1 byte, signed)', () => {
        it('should parse -128');
        it('should parse 0');
        it('should parse 127');
      });

      describe('UInt8 (1 byte, unsigned)', () => {
        it('should parse 0');
        it('should parse 128');
        it('should parse 255');
      });

      describe('Int16 (2 bytes, signed)', () => {
        it('should parse big-endian -1000');
        it('should parse little-endian -1000');
        it('should parse big-endian 0');
        it('should parse little-endian 32767');
      });

      // Similar for Int32, Int64, UInt16, UInt32, UInt64
    });

    describe('Float32 (4 bytes, IEEE 754)', () => {
      it('should parse big-endian 3.14159 (π)');
      it('should parse little-endian 3.14159');
      it('should parse big-endian -273.15');
      it('should parse big-endian 0.0');
      it('should handle NaN');
      it('should handle +Infinity');
      it('should handle -Infinity');
      it('should parse denormalized numbers');
    });

    describe('Float64 (8 bytes, IEEE 754 double)', () => {
      it('should parse big-endian π (double precision)');
      it('should parse little-endian π');
      it('should handle NaN');
      it('should handle ±Infinity');
      it('should parse very large numbers');
      it('should parse very small numbers (denormalized)');
    });

    describe('String Types', () => {
      describe('ASCII String', () => {
        it('should parse length-prefixed ASCII string');
        it('should parse fixed-width ASCII string');
        it('should handle empty string');
        it('should handle special characters');
      });

      describe('UTF-8 String', () => {
        it('should parse length-prefixed UTF-8 string');
        it('should parse multi-byte UTF-8 characters');
        it('should parse emoji characters');
        it('should handle empty string');
      });
    });
  });

  describe('Endianness Testing', () => {
    it('should detect big-endian Int16 correctly');
    it('should detect little-endian Int16 correctly');
    it('should detect big-endian Int32 correctly');
    it('should detect little-endian Int32 correctly');
    it('should detect big-endian Float32 correctly');
    it('should detect little-endian Float32 correctly');
    it('should detect big-endian Float64 correctly');
    it('should detect little-endian Float64 correctly');
    it('should handle mixed endianness per encoding definition');
  });

  describe('Component Type Parsing', () => {
    describe('Quantity Binary', () => {
      it('should parse quantity value (Float32)');
      it('should parse quantity value (Float64)');
      it('should handle NaN nil value');
    });

    describe('Count Binary', () => {
      it('should parse count value (Int32)');
      it('should parse count value (Int64)');
    });

    describe('Boolean Binary', () => {
      it('should parse boolean true/false');
    });

    describe('Text Binary', () => {
      it('should parse length-prefixed UTF-8 text');
      it('should parse fixed-width text');
    });

    describe('Time Binary', () => {
      it('should parse Unix epoch (Int64 milliseconds)');
      it('should parse ISO 8601 string (UTF-8)');
    });

    describe('DataRecord Binary', () => {
      it('should parse simple record (3 fields)');
      it('should parse nested record (2 levels)');
      it('should parse mixed field types');
    });

    describe('DataArray Binary', () => {
      it('should parse simple array (10 Float32 values)');
      it('should parse array with element count prefix');
      it('should parse array with block separators');
      it('should parse array of records (10 records × 3 fields)');
      it('should parse large array (1000 elements)');
      it('should parse array of arrays (nested)');
    });
  });

  describe('Binary Encoding Configuration', () => {
    it('should respect byteOrder=BIG_ENDIAN');
    it('should respect byteOrder=LITTLE_ENDIAN');
    it('should use encoding definition member specifications');
    it('should handle byteEncoding=RAW');
    it('should handle byteEncoding=BASE64');
  });

  describe('Error Handling', () => {
    it('should error on insufficient bytes (truncated buffer)');
    it('should detect possible endianness mismatch');
    it('should handle corrupted data gracefully');
    it('should error on misaligned data');
    it('should error on missing block separator');
    it('should validate encoding definition matches data');
  });

  // NOTE (Phase 2D, H2): OpenSensorHub describe block removed.
  // Use static fixtures only. If realistic complexity is needed,
  // create hand-crafted fixtures based on spec schemas.
});
```

**Binary Test Count:** 96 tests (20% of tests, 50% of effort)

---

## 11. Test Depth Definition

### "Meaningful" SWE Common Test Characteristics

✅ **DO (Comprehensive Testing):**

1. **Test All Three Encodings:**

   - JSON, Text, AND Binary for every component type
   - Not just JSON (easiest but insufficient)
   - Binary is CRITICAL - most complex and error-prone

2. **Byte-Level Binary Validation:**

   - Explicit hex dumps for binary fixtures
   - Verify exact byte sequences
   - Test endianness explicitly (big and little)
   - Test IEEE 754 edge cases (NaN, Inf, denormalized)

3. **Parse Complete Fixtures:**

   - Use real spec examples or OpenSensorHub data
   - Validate ALL extracted properties (not just presence)
   - Check property types, formats, constraints

4. **Schema Validation with Mismatches:**

   - Test observations against DataStream schemas
   - Test valid conformance (exact match)
   - Test invalid conformance (type mismatch, missing field, extra field)

5. **Test Nested Structures:**

   - DataRecord within DataRecord (2-3 levels)
   - DataArray of DataRecords
   - Mixed nesting scenarios

6. **Test All Data Type Variations:**

   - Float32 and Float64 (both endianness)
   - Int8/16/32/64 and UInt8/16/32/64
   - Strings (ASCII and UTF-8)
   - Boolean, Time, Category

7. **Test Error Conditions Per Encoding:**

   - JSON: Malformed JSON, type mismatches
   - Text: Delimiter errors, missing values
   - Binary: Insufficient bytes, endianness errors, corrupted data

8. **Use Real Examples:**
   - Spec examples (normative baseline)
   - OpenSensorHub data (real-world validation)
   - Hand-crafted edge cases (error conditions)

❌ **DON'T (Trivial Testing):**

1. **Just Check Existence:**

   - `expect(result).toBeDefined()` - too weak
   - `expect(result.value).toBeTruthy()` - no validation

2. **Skip Binary Encoding:**

   - Binary is MOST CRITICAL and MOST COMPLEX
   - Must have ~50% of testing effort

3. **Test Only JSON:**

   - JSON is easiest but insufficient
   - All 3 encodings required

4. **Use Overly Simple Fixtures:**

   - Hand-crafted minimal JSON without realistic complexity
   - Fixtures with only 1-2 fields

5. **Skip Schema Validation:**

   - Observation results MUST conform to DataStream schemas
   - Schema validation is core CSAPI Part 2 requirement

6. **Skip Endianness Testing:**

   - Endianness bugs are common and hard to debug
   - Must test big-endian AND little-endian explicitly

7. **Test Only Happy Path:**
   - No error conditions tested
   - No edge cases (NaN, Inf, empty arrays, deep nesting)

**Test Quality Criteria:**

| Criterion               | Meaningful Test                        | Trivial Test         |
| ----------------------- | -------------------------------------- | -------------------- |
| **Encoding Coverage**   | JSON, Text, AND Binary                 | JSON only            |
| **Binary Validation**   | Byte-level hex dumps, endianness tests | Skipped or minimal   |
| **Property Validation** | Type, format, constraints checked      | Just existence check |
| **Schema Validation**   | Conformance tested, mismatches tested  | Skipped              |
| **Nesting Depth**       | 2-3 levels tested                      | Only flat structures |
| **Error Coverage**      | 22+ error scenarios per encoding       | Only happy path      |
| **Fixture Quality**     | Spec examples or OpenSensorHub         | Hand-crafted minimal |
| **Assertions per Test** | 8-20 assertions                        | 1-3 assertions       |

---

## 12. Fixture Requirements

### 12.1 Fixture Directory Structure

```
fixtures/swe-common/
├── json/                          (~40 fixtures)
│   ├── simple-components/
│   │   ├── quantity-temperature.json
│   │   ├── quantity-with-constraint.json
│   │   ├── quantity-with-nil-value.json
│   │   ├── count-particle-count.json
│   │   ├── boolean-status.json
│   │   ├── text-station-id.json
│   │   ├── time-iso8601.json
│   │   ├── category-weather-code.json
│   │   └── ...
│   ├── range-components/
│   │   ├── quantity-range-temp-range.json
│   │   ├── category-range.json
│   │   └── time-range.json
│   ├── data-record/
│   │   ├── simple-record-3-fields.json
│   │   ├── nested-record-2-levels.json
│   │   ├── nested-record-3-levels.json
│   │   └── mixed-field-types.json
│   ├── data-array/
│   │   ├── simple-array-10-values.json
│   │   ├── array-100-values.json
│   │   ├── array-of-records-10.json
│   │   ├── array-of-records-100.json
│   │   └── nested-arrays.json
│   ├── vector/
│   │   ├── position-3d-lat-lon-height.json
│   │   └── position-2d-lat-lon.json
│   ├── matrix/
│   │   ├── matrix-3x3.json
│   │   └── covariance-matrix.json
│   ├── data-choice/
│   │   ├── choice-measurement-modes.json
│   │   └── choice-conditional-observations.json
│   ├── geometry-data/
│   │   ├── point-geometry.json
│   │   └── polygon-geometry.json
│   └── error-cases/
│       ├── malformed-json.txt
│       ├── missing-required-property.json
│       ├── invalid-type.json
│       └── constraint-violation.json
│
├── text/                          (~40 fixtures)
│   ├── simple-components/
│   │   ├── quantity-values.csv
│   │   ├── count-values.csv
│   │   ├── boolean-values.csv
│   │   └── ...
│   ├── data-record/
│   │   ├── weather-observation-3-fields.csv
│   │   ├── multi-field-10-records.csv
│   │   └── ...
│   ├── data-array/
│   │   ├── timeseries-10-values.csv
│   │   ├── timeseries-100-values.csv
│   │   └── ...
│   ├── delimiter-variations/
│   │   ├── comma-delimited.csv
│   │   ├── tab-delimited.tsv
│   │   ├── semicolon-delimited.csv
│   │   └── custom-delimiter.txt
│   ├── quoted-strings/
│   │   ├── quoted-with-commas.csv
│   │   ├── quoted-with-newlines.csv
│   │   └── escaped-quotes.csv
│   ├── missing-values/
│   │   ├── empty-tokens.csv
│   │   ├── sparse-data.csv
│   │   └── ...
│   └── error-cases/
│       ├── incorrect-delimiter.csv
│       ├── unmatched-quotes.csv
│       ├── field-count-mismatch.csv
│       └── ...
│
├── binary/                        (~40 fixtures, includes .bin + .hex + expected.json)
│   ├── integers/
│   │   ├── int8-values.bin + .hex + expected.json
│   │   ├── uint8-values.bin + .hex + expected.json
│   │   ├── int16-big-endian.bin + .hex + expected.json
│   │   ├── int16-little-endian.bin + .hex + expected.json
│   │   ├── int32-big-endian.bin + .hex + expected.json
│   │   ├── int32-little-endian.bin + .hex + expected.json
│   │   └── ...
│   ├── floats/
│   │   ├── float32-big-endian-pi.bin + .hex + expected.json
│   │   ├── float32-little-endian-pi.bin + .hex + expected.json
│   │   ├── float32-nan.bin + .hex + expected.json
│   │   ├── float32-infinity.bin + .hex + expected.json
│   │   ├── float64-big-endian-pi.bin + .hex + expected.json
│   │   ├── float64-little-endian-pi.bin + .hex + expected.json
│   │   └── ...
│   ├── strings/
│   │   ├── ascii-string.bin + .hex + expected.json
│   │   ├── utf8-string.bin + .hex + expected.json
│   │   ├── utf8-multibyte.bin + .hex + expected.json
│   │   └── ...
│   ├── components/
│   │   ├── quantity-float32.bin + .hex + expected.json + encoding.json
│   │   ├── count-int32.bin + .hex + expected.json + encoding.json
│   │   ├── boolean-single-byte.bin + .hex + expected.json + encoding.json
│   │   ├── time-unix-epoch.bin + .hex + expected.json + encoding.json
│   │   └── ...
│   ├── data-record/
│   │   ├── simple-record-3-fields.bin + .hex + expected.json + encoding.json
│   │   ├── nested-record-2-levels.bin + .hex + expected.json + encoding.json
│   │   └── ...
│   ├── data-array/
│   │   ├── array-10-float32.bin + .hex + expected.json + encoding.json
│   │   ├── array-with-block-separators.bin + .hex + expected.json + encoding.json
│   │   ├── array-of-records-10.bin + .hex + expected.json + encoding.json
│   │   └── ...
│   ├── endianness/
│   │   ├── mixed-endianness.bin + .hex + expected.json + encoding.json
│   │   └── ...
│   └── error-cases/
│       ├── insufficient-bytes.bin + .hex
│       ├── corrupted-data.bin + .hex
│       ├── misaligned-data.bin + .hex
│       └── ...
│
└── schemas/                       (~10-15 schemas for validation)
    ├── weather-observation-schema.json
    ├── temperature-sensor-schema.json
    ├── multi-field-schema.json
    └── ...
```

**Total Fixtures:** ~120 fixtures across all encodings

---

### 12.2 Binary Fixture Format

Each binary fixture set includes 4 files:

1. **`.bin` file:** Raw binary data
2. **`.hex` file:** Hex dump for documentation and debugging
3. **`expected.json` file:** Expected parsed result for assertion
4. **`encoding.json` file:** BinaryEncoding definition specifying byte format

**Example Binary Fixture Set:**

**File: `quantity-float32-big-endian.bin`**

```
Raw bytes: 40 49 0F DB
```

**File: `quantity-float32-big-endian.hex`**

```
Offset  Hex                                             ASCII
------  -----------------------------------------------  -----
0x0000  40 49 0F DB                                      @I..

Byte breakdown:
  40 49 0F DB = Big-endian IEEE 754 Float32
  = 0x40490FDB
  = Sign: 0, Exponent: 128 (0x80), Mantissa: 0x490FDB
  = 3.14159265... (π)
```

**File: `expected.json`**

```json
{
  "type": "Quantity",
  "value": 3.14159265358979,
  "uom": { "code": "rad" }
}
```

**File: `encoding.json`**

```json
{
  "type": "BinaryEncoding",
  "byteOrder": "BIG_ENDIAN",
  "byteEncoding": "RAW",
  "members": [
    {
      "component": "value",
      "dataType": "FLOAT32",
      "byteLength": 4
    }
  ]
}
```

---

### 12.3 Fixture Generation Strategy

**Spec Examples (Priority 1):**

- Extract all examples from SWE Common 3.0 spec (§7-8)
- Extract all examples from CSAPI Part 2 spec (§7)
- Use verbatim (normative baseline)

**OpenSensorHub Examples (Priority 2):**

- Fetch real datastreams and observations
- Request all 3 encodings (JSON, Text, Binary)
- Document complexity and issues
- Use for real-world validation

**Hand-Crafted Fixtures (Priority 3):**

- Create for error conditions (malformed, invalid)
- Create for edge cases (NaN, Inf, empty arrays, deep nesting)
- Create for specific test scenarios not covered by spec/OpenSensorHub

**Binary Fixture Generation:**

- **Manual creation:** Write byte sequences manually with hex editors
- **Programmatic generation:** Write utilities to generate .bin files from expected values
- **OpenSensorHub extraction:** Capture real binary responses and document
- **Hex dump utilities:** Create utilities to generate .hex files from .bin files

---

## 13. Validation Against Upstream Patterns

**Comparison with Section 1-2 Findings (EDR Client Tests):**

| Aspect                | EDR Client Pattern                            | SWE Common Parser Plan                                   | Alignment                                           |
| --------------------- | --------------------------------------------- | -------------------------------------------------------- | --------------------------------------------------- |
| **Test Organization** | Single spec file per resource                 | 4 spec files (JSON, Text, Binary, Schema)                | ✅ Aligned - complexity appropriate for 3 encodings |
| **Fixture Usage**     | Real EDR server responses                     | Spec examples + OpenSensorHub + hand-crafted             | ✅ Aligned - similar priority                       |
| **Test Depth**        | Parse complete responses, validate properties | Parse complete results, byte-level validation for binary | ✅ Aligned - comprehensive                          |
| **Error Handling**    | Test malformed responses, missing properties  | Test errors per encoding (22 scenarios)                  | ✅ Aligned - thorough                               |
| **Encoding Coverage** | Single encoding (JSON GeoJSON)                | Three encodings (JSON, Text, Binary)                     | ⚠️ Additional - unique to SWE Common                |
| **Binary Testing**    | Not applicable                                | Extensive byte-level testing (~50% of effort)            | ⚠️ Additional - unique to SWE Common                |
| **Schema Validation** | Not applicable                                | Observation conformance to DataStream schema             | ⚠️ Additional - CSAPI Part 2 requirement            |
| **Performance**       | Not explicitly tested                         | Large arrays (1000+ elements) for performance            | ✅ Aligned - pragmatic approach                     |
| **Test Count**        | ~30-40 tests per resource                     | ~190 tests total (48 JSON, 43 Text, 96 Binary, 8 Schema) | ✅ Aligned - similar density                        |

**Upstream Quality Standards Met:**

- ✅ Real fixtures prioritized over hand-crafted
- ✅ Comprehensive property validation (not just existence)
- ✅ Error conditions thoroughly tested (22 scenarios across encodings)
- ✅ Integration points identified (SensorML characteristics/capabilities)
- ✅ Test organization follows established patterns

**SWE Common-Specific Additions (Not in EDR):**

- **Three-encoding coverage** - JSON, Text, Binary (unique to SWE Common)
- **Byte-level binary testing** - Endianness, IEEE 754, hex dumps (most complex)
- **Schema validation** - Observation conformance (CSAPI Part 2 requirement)
- **Encoding configurations** - JSONEncoding, TextEncoding, BinaryEncoding parsing

---

## 14. Integration with Implementation Guide

**Cross-Validation with Implementation Guide SWE Common Parser Specification:**

| Aspect                  | Implementation Guide                                                                                                                                                 | This Test Plan                                                | Status                                          |
| ----------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------- | ----------------------------------------------- |
| **Component Types**     | 12+ types (Quantity, Count, Boolean, Text, Time, Category, QuantityRange, CategoryRange, TimeRange, DataRecord, DataArray, Vector, Matrix, DataChoice, GeometryData) | All 12+ types covered across 3 encodings                      | ✅ Aligned                                      |
| **Encodings**           | JSON, Text, Binary                                                                                                                                                   | All 3 encodings with specific test strategies                 | ✅ Aligned                                      |
| **Simple Components**   | Quantity, Count, Boolean, Text, Time, Category                                                                                                                       | All tested in all 3 encodings                                 | ✅ Aligned                                      |
| **Range Components**    | QuantityRange, CategoryRange, TimeRange                                                                                                                              | All tested in all 3 encodings                                 | ✅ Aligned                                      |
| **Complex Components**  | DataRecord, DataArray, Vector, Matrix, DataChoice, GeometryData                                                                                                      | All tested in all 3 encodings                                 | ✅ Aligned                                      |
| **Binary Data Types**   | Boolean (1 byte), Int8-64, UInt8-64, Float32, Float64, String (UTF-8/ASCII)                                                                                          | All data types with explicit byte format tests                | ✅ Aligned                                      |
| **Endianness**          | BIG_ENDIAN, LITTLE_ENDIAN                                                                                                                                            | Explicit endianness tests for all multi-byte types            | ✅ Aligned                                      |
| **IEEE 754**            | Float32, Float64 with NaN, Inf handling                                                                                                                              | IEEE 754 edge cases (NaN, Inf, -Inf, denormalized)            | ✅ Aligned                                      |
| **Schema Validation**   | Result structure, range, unit, array, quality, temporal, categorical, text, geometry validation                                                                      | Comprehensive schema validation (8 test scenarios)            | ✅ Aligned                                      |
| **NilValues**           | Missing/invalid data with reason codes                                                                                                                               | Nil value handling tested                                     | ✅ Aligned                                      |
| **Quality**             | Accuracy, precision, confidence, flags                                                                                                                               | Quality information parsing tested                            | ✅ Aligned                                      |
| **Constraints**         | AllowedValues, AllowedIntervals, AllowedTimes, AllowedTokens                                                                                                         | Constraint validation tested                                  | ✅ Aligned                                      |
| **ReferenceFrames**     | Temporal (UTC, TAI, GPS), Spatial (EPSG codes)                                                                                                                       | Reference frame parsing tested                                | ⚠️ Partial - MEDIUM priority, not comprehensive |
| **CodeSpaces**          | Controlled vocabularies with dereferencing                                                                                                                           | CodeSpace URIs tested, dereferencing MEDIUM priority          | ⚠️ Partial - dereferencing not in initial scope |
| **Encoding Conversion** | Bidirectional JSON ↔ Text ↔ Binary                                                                                                                                   | Not in initial scope                                          | ⚠️ Gap - FUTURE ENHANCEMENT                     |
| **Streaming**           | Incremental parsing for large datasets                                                                                                                               | Not in initial scope                                          | ⚠️ Gap - FUTURE ENHANCEMENT                     |
| **Performance**         | Binary encoding for high-volume data                                                                                                                                 | Large array tests (1000+ elements) for performance validation | ✅ Aligned                                      |

**Alignment Status:**

- ✅ **Fully Aligned (16 items):** Core component types, encodings, data types, endianness, IEEE 754, schema validation, constraints, quality
- ⚠️ **Partial Alignment (2 items):** Reference frames (tested but not comprehensive), CodeSpace dereferencing (not in initial scope)
- ⚠️ **Gaps Identified (2 items):** Encoding conversion (future enhancement), Streaming (future enhancement)

**Recommendations:**

1. **Initial Implementation:** Focus on CRITICAL/HIGH priority items (fully aligned with Implementation Guide core requirements)
2. **Phase 2 Enhancements:** Add reference frame comprehensive validation, CodeSpace vocabulary dereferencing
3. **Phase 3 Enhancements:** Add encoding conversion (JSON ↔ Text ↔ Binary bidirectional)
4. **Phase 4 Enhancements:** Add streaming support for incremental parsing of very large datasets

**Implementation Guide Updates Needed:**

- Document test strategy for SWE Common parser (reference this document)
- Add fixture requirements to Implementation Guide (120+ fixtures, including binary with hex dumps)
- Note MEDIUM/LOW priority items for phased implementation
- Add encoding conversion as enhancement (not blocking initial implementation)

---

## 15. Testing Estimates

| Encoding/Category                               | Test Count | Lines per Test | Total Lines     | Time Estimate (Implementation) | Priority     |
| ----------------------------------------------- | ---------- | -------------- | --------------- | ------------------------------ | ------------ |
| **JSON Encoding**                               |
| Simple components (6 types)                     | 6          | 10-15          | 60-90           | 1-1.5 hours                    | HIGH         |
| Range components (3 types)                      | 3          | 10-12          | 30-36           | 30-45 min                      | MEDIUM       |
| DataRecord                                      | 5          | 15-20          | 75-100          | 1-1.5 hours                    | **CRITICAL** |
| DataArray                                       | 6          | 15-25          | 90-150          | 1.5-2 hours                    | **CRITICAL** |
| Vector, Matrix, DataChoice, GeometryData        | 8          | 12-18          | 96-144          | 1.5-2 hours                    | MEDIUM-LOW   |
| Nested structures                               | 3          | 20-25          | 60-75           | 1-1.5 hours                    | HIGH         |
| Schema validation                               | 5          | 12-18          | 60-90           | 1 hour                         | **CRITICAL** |
| UOM, quality, nil values                        | 6          | 10-13          | 60-78           | 1 hour                         | MEDIUM       |
| Error handling                                  | 6          | 8-12           | 48-72           | 45-60 min                      | MEDIUM       |
| **JSON Subtotal**                               | **48**     | **~12 avg**    | **589-811**     | **9-12 hours**                 |              |
| **Text Encoding**                               |
| Simple components (6 types)                     | 6          | 10-15          | 60-90           | 1-1.5 hours                    | HIGH         |
| Range components (3 types)                      | 3          | 10-12          | 30-36           | 30-45 min                      | MEDIUM       |
| DataRecord                                      | 5          | 15-20          | 75-100          | 1-1.5 hours                    | **CRITICAL** |
| DataArray                                       | 6          | 15-20          | 90-120          | 1.5-2 hours                    | **CRITICAL** |
| Delimiter variations                            | 5          | 12-15          | 60-75           | 1 hour                         | HIGH         |
| Quoted strings, missing values                  | 6          | 10-12          | 60-72           | 1 hour                         | MEDIUM       |
| Whitespace, block separators                    | 5          | 11-13          | 55-65           | 45-60 min                      | MEDIUM       |
| Error handling                                  | 5          | 8-12           | 40-60           | 45-60 min                      | MEDIUM       |
| **Text Subtotal**                               | **43**     | **~11 avg**    | **491-646**     | **8-11 hours**                 |              |
| **Binary Encoding**                             |
| Boolean (1 byte)                                | 2          | 12-15          | 24-30           | 20-30 min                      | **CRITICAL** |
| Integer types (8 types × 3 values × 2 endian)   | 20         | 13-18          | 260-360         | 3-4 hours                      | **CRITICAL** |
| Float32/Float64 (IEEE 754)                      | 12         | 15-25          | 180-300         | 3-5 hours                      | **CRITICAL** |
| String types                                    | 6          | 15-20          | 90-120          | 1.5-2 hours                    | HIGH         |
| Endianness testing                              | 14         | 15-20          | 210-280         | 3-4 hours                      | **CRITICAL** |
| Component parsing (7 types)                     | 20         | 15-22          | 300-440         | 4-6 hours                      | **CRITICAL** |
| Advanced features (block separators, alignment) | 11         | 15-19          | 165-209         | 2-3 hours                      | HIGH-MEDIUM  |
| Schema validation                               | 5          | 15-20          | 75-100          | 1-1.5 hours                    | HIGH         |
| Error handling                                  | 10         | 12-18          | 120-180         | 1.5-2 hours                    | HIGH         |
| **Binary Subtotal**                             | **96**     | **~15 avg**    | **1,447-1,896** | **20-30 hours**                |              |
| **Schema Validation**                           |
| Structure validation                            | 3          | 15-18          | 45-54           | 45-60 min                      | **CRITICAL** |
| Array validation                                | 2          | 12-15          | 24-30           | 30 min                         | HIGH         |
| Constraint validation                           | 4          | 12-15          | 48-60           | 45-60 min                      | HIGH         |
| DataChoice, quality, temporal, unit             | 4          | 10-13          | 40-52           | 30-45 min                      | MEDIUM-LOW   |
| **Schema Subtotal**                             | **8**      | **~13 avg**    | **96-120**      | **2.5-3 hours**                |              |
| **GRAND TOTAL**                                 | **195**    | **~13 avg**    | **2,623-3,473** | **40-56 hours**                |              |

**Note:** Binary encoding is ~50% of total implementation effort (20-30 hours out of 40-56 hours) due to byte-level complexity.

**Phased Implementation Plan:**

**Phase 1 (CRITICAL - 15-20 hours):**

- JSON DataRecord/DataArray parsing (8 tests, ~165 lines)
- Text DataRecord/DataArray parsing (6 tests, ~165 lines)
- Binary integer and float data types (24 tests, ~440 lines)
- Binary endianness tests (14 tests, ~245 lines)
- Schema validation structure (3 tests, ~49 lines)
- **Deliverable:** ~50 tests, ~1,064 lines

**Phase 2 (HIGH - 12-18 hours):**

- JSON simple components (6 tests, ~75 lines)
- Text simple components (6 tests, ~75 lines)
- Binary component parsing (20 tests, ~370 lines)
- Text delimiter variations (5 tests, ~67 lines)
- Nested structures (3 tests, ~67 lines)
- **Deliverable:** ~40 tests, ~654 lines

**Phase 3 (MEDIUM - 8-12 hours):**

- JSON range/complex components (11 tests, ~186 lines)
- Text quoted strings, missing values (6 tests, ~66 lines)
- Binary advanced features (11 tests, ~187 lines)
- Error handling all encodings (21 tests, ~208 lines)
- Schema validation remaining (5 tests, ~71 lines)
- **Deliverable:** ~54 tests, ~718 lines

**Phase 4 (LOW - Optional):**

- Performance tests (large arrays 1000+ elements)
- Advanced quality information parsing
- Reference frame comprehensive validation
- Real-world OpenSensorHub fixture coverage
- **Deliverable:** TBD

---

## 16. Testing Priorities

### CRITICAL (Must Have - Phase 1)

**What:**

- JSON DataRecord/DataArray parsing (multi-field observations, time series)
- Text DataRecord/DataArray parsing (CSV observations)
- Binary all integer types (int8-64, uint8-64) with endianness
- Binary all float types (float32, float64) with IEEE 754 edge cases (NaN, Inf)
- Binary endianness explicit tests (big-endian and little-endian for all multi-byte types)
- Schema validation structure matching (observation conforms to DataStream schema)

**Why Critical:**

- DataRecord/DataArray are used in 95% of all DataStreams for observations
- Binary encoding is most complex and error-prone (byte-level precision required)
- Endianness bugs cause data corruption (values completely wrong)
- IEEE 754 edge cases (NaN, Inf) must be handled correctly for sensor failures
- Schema validation is core CSAPI Part 2 requirement (observations must conform to schema)

**Test Lines:** ~1,064 lines  
**Implementation Time:** 15-20 hours

---

### HIGH (Should Have - Phase 2)

**What:**

- JSON simple components (Quantity, Count, Boolean, Text, Time, Category)
- Text simple components (all types in CSV)
- Binary component parsing (Quantity, Count, Boolean, Text, Time, DataRecord, DataArray)
- Text delimiter variations (comma, tab, semicolon, custom)
- Nested structures (DataRecord in DataRecord, DataArray of DataRecords)

**Why High:**

- Simple components are building blocks for all complex structures
- Text encoding is common for tabular data (CSV export/import)
- Binary component parsing connects data types to SWE Common semantics
- Delimiter variations handle real-world CSV variations
- Nested structures enable complex observation hierarchies

**Test Lines:** ~654 lines  
**Implementation Time:** 12-18 hours

---

### MEDIUM (Nice to Have - Phase 3)

**What:**

- JSON range components (QuantityRange, CategoryRange, TimeRange)
- JSON complex components (Vector, Matrix, DataChoice, GeometryData)
- Text quoted strings, missing values, whitespace handling
- Binary advanced features (block separators, byte alignment, variable-length data)
- Error handling all encodings (malformed, type mismatches, truncated, corrupted)
- Schema validation constraints (range, allowed values, DataChoice)

**Why Medium:**

- Range components useful but less common than simple types
- Complex components (Vector, Matrix) used in specialized scenarios
- Text edge cases (quotes, missing values) important for CSV robustness
- Binary advanced features enable more efficient encoding
- Error handling prevents silent failures
- Schema constraint validation enforces data quality

**Test Lines:** ~718 lines  
**Implementation Time:** 8-12 hours

---

### LOW (Optional - Phase 4+)

**What:**

- Performance testing (very large arrays 1000+ elements, streaming)
- Quality information comprehensive parsing
- Reference frames comprehensive validation (UTC, TAI, GPS time)
- CRS validation for Vector (EPSG codes, coordinate validation)
- Encoding conversion (JSON ↔ Text ↔ Binary bidirectional)
- CodeSpace vocabulary dereferencing

**Why Low:**

- Performance optimization after correctness established
- Quality information rarely used in practice
- Reference frames usually default (UTC)
- CRS usually default (WGS84)
- Encoding conversion nice but not required for parsing
- Vocabulary dereferencing adds complexity without immediate value

**Test Lines:** TBD (not in initial 2,600-3,500 estimate)  
**Implementation Time:** TBD (future enhancement)

---

## 17. Risks and Edge Cases

| Risk/Edge Case                                              | Likelihood | Impact       | Mitigation Strategy                                                                                  | Priority     |
| ----------------------------------------------------------- | ---------- | ------------ | ---------------------------------------------------------------------------------------------------- | ------------ |
| **Binary Encoding Bugs**                                    |
| Endianness detection wrong                                  | Medium     | **CRITICAL** | Explicit big-endian and little-endian tests for all multi-byte types; encoding definition validation | **CRITICAL** |
| IEEE 754 NaN/Inf handling                                   | Medium     | High         | Specific edge case tests for NaN, +Inf, -Inf, denormalized numbers; graceful handling                | HIGH         |
| Byte alignment issues                                       | Low        | High         | Test misaligned data; validate byte offsets match encoding definition                                | HIGH         |
| Buffer overflow/underflow                                   | Low        | **CRITICAL** | Test insufficient bytes (truncated buffer); bounds checking                                          | **CRITICAL** |
| **Data Corruption**                                         |
| Binary data corruption causes wrong values                  | High       | **CRITICAL** | Extensive binary testing with known byte sequences; hex dumps for debugging                          | **CRITICAL** |
| Wrong data type interpretation                              | Medium     | High         | Schema validation; type checking; encoding definition validation                                     | HIGH         |
| **Three-Encoding Consistency**                              |
| JSON, Text, Binary produce different results                | Medium     | High         | Cross-encoding validation tests; same observation in all 3 encodings                                 | HIGH         |
| Encoding conversion loss of precision                       | Low        | Medium       | Document precision limits; test round-trip conversion                                                | MEDIUM       |
| **Schema Validation**                                       |
| Schema validation too strict (rejects valid data)           | Medium     | Medium       | Follow SWE Common spec strictly; configurable validation strictness                                  | MEDIUM       |
| Schema validation too lenient (accepts invalid data)        | High       | High         | Comprehensive constraint validation; test boundary conditions                                        | HIGH         |
| **Large Datasets**                                          |
| Very large arrays cause memory issues (>10,000 elements)    | Low        | Medium       | Test with realistic sizes (1000-5000 elements); streaming if needed                                  | MEDIUM       |
| Deep nesting causes stack overflow (>10 levels)             | Low        | Medium       | Limit nesting depth to 10 levels; iterative parsing for deep structures                              | MEDIUM       |
| **OpenSensorHub Data**                                      |
| Real-world data has non-standard extensions                 | High       | Medium       | Parse core SWE Common properties; ignore unknown properties; log warnings                            | HIGH         |
| Binary examples unavailable from OpenSensorHub              | High       | High         | Generate binary fixtures from spec examples; programmatic binary generation utilities                | HIGH         |
| **Fixture Generation**                                      |
| Binary fixtures hard to create/maintain                     | High       | Medium       | Create hex dump utilities; programmatic .bin generation from expected values; document byte formats  | HIGH         |
| Insufficient fixture coverage                               | Medium     | High         | 120+ fixtures across all types and encodings; systematic coverage matrix                             | HIGH         |
| **Performance**                                             |
| Binary parsing too slow for high-frequency sensors (>10 Hz) | Low        | Medium       | Optimize binary parsing; profile hotspots; consider streaming                                        | LOW          |
| Text parsing inefficient for large CSV files                | Low        | LOW          | Streaming CSV parser; chunked reading                                                                | LOW          |

**Mitigation Priorities:**

1. **Binary encoding correctness** (extensive testing, hex dumps, endianness tests)
2. **Schema validation accuracy** (comprehensive constraint tests, boundary conditions)
3. **OpenSensorHub compatibility** (handle extensions, generate missing binary fixtures)
4. **Fixture generation utilities** (hex dumps, binary generation, expected results)
5. **Large dataset handling** (realistic size tests, nesting limits)

**Testing Strategy for Each Risk:**

- **Endianness:** Create explicit fixtures for big/little endian for all multi-byte types (36 fixtures)
- **IEEE 754:** Create fixtures for NaN, +Inf, -Inf, denormalized numbers (12 fixtures)
- **Buffer truncation:** Create truncated binary fixtures, verify error handling (5 fixtures)
- **Data corruption:** Create corrupted binary fixtures with known wrong byte sequences (5 fixtures)
- **Schema validation:** Test boundary conditions, constraint violations, type mismatches (15 scenarios)
- **Large arrays:** Test with 100, 1000, 5000 element arrays, measure performance (3 fixtures)
- **Deep nesting:** Test 1-5 level nesting, verify no stack overflow (5 fixtures)
- **Non-standard extensions:** Use real OpenSensorHub data, verify graceful handling (5 fixtures)

---

## 18. Summary and Next Steps

### Research Summary

> **⚠️ REVIEW NOTICE (Phase 2D, H1/M2):** This document was reviewed in Phase 2D. The binary encoding content (~50% of the document) is genuinely client-oriented and can be used directly for parser implementation. The JSON/Text encoding sections need reorientation from spec-validation to parser-output testing. Parser TypeScript output interfaces must be defined before tests can be implemented.

**Completed:**

- ✅ All 12+ SWE Common component types analyzed across 3 encodings (JSON, Text, Binary)
- ✅ Binary encoding byte formats documented in detail (all integer types, float types, strings with IEEE 754, endianness) — **directly usable for parser implementation**
- ✅ Endianness testing strategy defined (explicit big-endian and little-endian tests for all multi-byte types) — **directly usable**
- ✅ IEEE 754 edge cases addressed (NaN, Inf, -Inf, denormalized numbers) — **directly usable**
- ✅ Schema validation requirements analyzed — **structural matching usable; constraint/unit validation removed per H1**
- ✅ Nested structure testing strategy defined (DataRecord 1-3 levels, DataArray of DataRecords)
- ✅ Fixture inventory complete (~120 fixtures: ~40 JSON, ~40 Text, ~40 Binary with hex dumps + expected + encoding defs) — **OpenSensorHub fixtures removed per H2**
- ✅ Test depth defined meeting "meaningful" criteria (byte-level binary parsing, all 3 encodings)
- ✅ Error handling requirements analyzed (subset of 22 scenarios — **only structurally unparseable inputs should cause errors, per H1**)
- ✅ Test organization documented (4 files: JSON, Text, Binary, Schema; ~195 tests, 1,700-2,500 lines)
- ✅ Validated against upstream patterns (aligned with EDR test approach, SWE Common-specific additions documented)
- ✅ Cross-validated with Implementation Guide (aligned with parser specification, gaps identified)
- ✅ All 98 research questions answered — **note: 98 questions reflects research methodology depth, not testing scope (L3)**

**Testing Priorities Established:**

- **CRITICAL:** Binary integer/float types, endianness, JSON/Text DataRecord/DataArray, schema validation structure
- **HIGH:** JSON/Text simple components, binary component parsing, delimiter variations, nested structures
- **MEDIUM:** Range/complex components, text edge cases, binary advanced features, error handling, schema constraints
- **LOW:** Performance optimization, quality comprehensive parsing, reference frames, CRS validation

**Estimated Implementation:**

- **Total Test Lines:** 2,600-3,500 lines (~195 tests)
- **Total Implementation Time:** 40-56 hours
- **Phase 1 (CRITICAL):** ~1,064 lines, ~50 tests, 15-20 hours
- **Phase 2 (HIGH):** ~654 lines, ~40 tests, 12-18 hours
- **Phase 3 (MEDIUM):** ~718 lines, ~54 tests, 8-12 hours
- **Binary encoding:** ~50% of total effort (20-30 hours) due to byte-level complexity

**Key Insight:** Binary encoding is ~50% of implementation effort but is MOST CRITICAL. Previous iterations identified format parsing as major weakness. SWE Common binary encoding is highest rejection risk due to complexity (endianness, IEEE 754, byte alignment, variable-length data).

### Answers to All Research Questions (98 Questions)

#### SWE Common 3.0 Specification Analysis (Q1-10):

1. **Component types:** 12+ types - Quantity, Count, Boolean, Text, Time, Category, QuantityRange, CategoryRange, TimeRange, DataRecord, DataArray, Vector, Matrix, DataChoice, GeometryData
2. **Mandatory vs optional:** Component-specific - see property testing matrices (Section 4)
3. **Normative rules:** Documented in Section 6 (schema validation testing) and Section 7 (error conditions)
4. **Encoding differences:** JSON (human-readable objects), Text (CSV delimiters), Binary (byte sequences)
5. **Encoding choice rules:** JSON for development/debugging, Text for batch/spreadsheet, Binary for high-frequency/bandwidth-constrained
6. **Recursive structure limits:** No spec limit; recommend 10-level max to prevent stack overflow
7. **Encoding definition:** JSONEncoding, TextEncoding, BinaryEncoding objects specify format parameters
8. **Endianness rules:** BIG_ENDIAN (network byte order) or LITTLE_ENDIAN (most systems); explicit in BinaryEncoding
9. **Data type byte sizes:** See Section 3 (Binary Encoding Byte Format Specifications)
10. **Block separation:** blockSeparator in TextEncoding (e.g., newline); optional byte sequence in BinaryEncoding for array elements

#### JSON Encoding Requirements (Q11-17):

11. **JSON structure validation:** Component type, required properties, value types, UOM format
12. **DataRecord parsing:** Parse fields array, extract nested fields, validate field names unique
13. **DataArray parsing:** Parse elementType schema, parse values array, validate element count
14. **12+ component types in JSON:** All component types tested (see Section 2.1)
15. **Property validation:** UOM (code or href), definition (valid URI), quality (array of components)
16. **Optional properties:** Test missing optional properties (should not error), test present optional properties (should parse correctly)
17. **JSON-specific edge cases:** Malformed JSON, type mismatches (string vs number), unknown component types, invalid UOM format

#### Text Encoding Requirements (Q18-24):

18. **Delimiter characters:** Comma (default), tab, semicolon, custom; specified in tokenSeparator
19. **Token separator parsing:** Split values by tokenSeparator, handle quoted strings, collapse whitespace if configured
20. **Block separator parsing:** Split records by blockSeparator (typically newline), handle missing separators
21. **Decimal separator:** Period (default) or comma; specified in decimalSeparator
22. **Quoted strings:** Handle embedded delimiters within quotes, handle escaped quotes ("\"")
23. **Text encoding edge cases:** Incorrect delimiter, missing block separator, unmatched quotes, double decimal points, field count mismatch
24. **Missing values:** Empty tokens between delimiters (e.g., "1.5,,3.7"); handle as null or error based on schema

#### Binary Encoding Requirements (Q25-37):

25. **Byte orders:** BIG_ENDIAN (network byte order, MSB first), LITTLE_ENDIAN (Intel, LSB first)
26. **Float32 parsing:** 4-byte IEEE 754 single precision; test big/little endian, NaN, Inf, denormalized
27. **Float64 parsing:** 8-byte IEEE 754 double precision; test big/little endian, NaN, Inf, denormalized
28. **Int8/16/32/64 parsing:** 1/2/4/8 byte signed integers; test big/little endian for multi-byte
29. **UInt8/16/32/64 parsing:** 1/2/4/8 byte unsigned integers; test big/little endian for multi-byte
30. **Boolean parsing:** 1 byte - 0x00 (false), 0x01 (true)
31. **String parsing:** Length-prefixed (1-4 byte length + UTF-8 bytes) or fixed-width (null-padded)
32. **Time parsing:** Unix epoch Int64 (milliseconds since 1970-01-01) or ISO 8601 string (UTF-8)
33. **Block separators:** Optional byte sequence between array elements; handle missing separators
34. **Binary edge cases:** Insufficient bytes, wrong endianness, corrupted data, misaligned data, invalid UTF-8
35. **Byte alignment:** Some systems require alignment to word boundaries (2, 4, 8 bytes); test misaligned data
36. **Variable-length data:** Strings (length prefix), arrays (element count prefix or implicit from schema)
37. **Endianness edge cases:** Mixed endianness (different fields different endian per encoding definition)

#### Component Type Testing (Q38-49):

38. **Quantity validation:** value (numeric), uom (code or href), constraint (intervals), nilValues, quality, definition (URI)
39. **Count validation:** value (integer), constraint (intervals or allowed values)
40. **Boolean validation:** value (true/false boolean, not string)
41. **Category validation:** value (string), codeSpace (vocabulary URI), constraint (allowed tokens)
42. **Text validation:** value (string), constraint (pattern or allowed tokens)
43. **Time validation:** value (ISO 8601 instant or interval), referenceFrame (UTC, TAI, GPS), uom (for durations)
44. **DataRecord validation:** fields (array), field names unique, field types valid SWE components
45. **Vector validation:** coordinates (array of Quantity), referenceFrame (CRS URI), coordinate count matches CRS dimension
46. **DataArray validation:** elementType (schema), values (array), elementCount (matches actual), encoding (required for Text/Binary)
47. **Matrix validation:** elementType, values (2D array), elementCount (rows × columns)
48. **DataChoice validation:** item (array of alternatives), selection mechanism
49. **DataStream validation:** Not a standalone component; DataArray wrapper for observations

#### Nested Structure Testing (Q50-55):

50. **DataRecord nesting depth:** No spec limit; test 1-3 levels comprehensive, 4+ levels edge cases; recommend 10-level max
51. **DataRecord within DataRecord:** Test 2-level, 3-level nesting; validate hierarchical structure maintained
52. **DataArray of DataRecords:** Test simple array (10 records), large array (100 records); validate element schema compliance
53. **Matrix of DataRecords:** Test 2D array of structured observations; edge case (LOW priority)
54. **Performance with deep nesting:** Test 3-4 level nesting, large arrays (1000 elements); measure parse time, memory usage
55. **Stack overflow risks:** Deep recursion (4+ levels); mitigate with iterative parsing, depth limits

#### Schema Validation - Observations (Q56-61):

56. **Validate observation values:** Field count, field types, field order must match DataStream resultSchema
57. **Schema conformance rules:** Required fields present, optional fields if present match schema, no extra fields (or warn)
58. **Mismatched schemas:** Wrong field count → error; wrong types → error; extra field → warn or error (configurable)
59. **Optional fields:** Missing optional field → pass; present optional field with correct type → pass
60. **DataChoice selection:** Selected item must be one of schema options → pass; not in options → error
61. **Schema violation error messages:** Include field name, expected type, actual type, JSON path to error location

#### Units of Measure (Q62-65):

62. **UOM formats:** UCUM code (`{" code": "Cel"}`) or URI (`{"href": "http://..."}`)
63. **Validate UOM codes:** Check UCUM syntax (basic validation); full validation optional (external UCUM library)
64. **UOM conversion:** Not in parser scope; external library for unit conversion if needed
65. **UOM edge cases:** Missing uom (error or warning based on schema), invalid UCUM code (warn), unrecognized unit (warn)

#### Quality Information (Q66-69):

66. **Test quality indicators:** Parse quality array, validate quality components (Quantity, Text, etc.)
67. **Quality types:** SimpleQuality, QuantityRange (accuracy range), Category (quality flags)
68. **Quality validation depth:** Moderate - validate structure, component types; full quality semantics LOW priority
69. **Quality critical?** MEDIUM priority - important for data provenance but not blocking

#### Time Reference Frames (Q70-73):

70. **Time reference frames:** UTC (default), TAI (International Atomic Time), GPS time, Julian date
71. **Test reference frame parsing:** Parse referenceFrame URI, validate against known frame URIs
72. **Validate time values:** ISO 8601 format compliance, reference frame-specific constraints
73. **Edge cases:** Leap seconds (UTC), timezone offsets, missing reference frame (default UTC)

#### Coordinate Reference Systems (Q74-76):

74. **CRS for Vector:** EPSG codes (e.g., EPSG:4326 for WGS84), OGC URIs (e.g., http://www.opengis.net/def/crs/EPSG/0/4326)
75. **Test CRS parsing:** Parse referenceFrame URI, validate coordinate count matches CRS dimension
76. **Missing CRS:** Default to WGS84 (EPSG:4326) for geographic coordinates; warn if ambiguous

#### Error Handling (Q77-82):

77. **Error conditions per encoding:** JSON (6 scenarios), Text (6 scenarios), Binary (10 scenarios) - see Section 7
78. **Malformed JSON:** Parse error with line/column; expected error message with context
79. **Invalid text delimiters:** Parse error; expected error at position with actual vs expected delimiter
80. **Corrupted binary data:** Handle gracefully (NaN for invalid floats) or error; context with byte offset
81. **Schema mismatches:** Validation error; clear message with field name, expected vs actual type, JSON path
82. **Error messages per encoding:** Include encoding type, error location (line/column for JSON/Text, byte offset for Binary), expected vs actual, suggested fix

#### Specification Examples (Q83-87):

83. **Complete observation examples:** 19 examples from SWE Common 3.0 and CSAPI Part 2 specs (see Section 8)
84. **Encoding examples:** JSON (15 examples), Text (2 examples), Binary (2 examples) from specs
85. **Component type examples:** All 12+ types have spec examples
86. **Nested structure examples:** DataRecord nested (2-3 levels), DataArray of DataRecords
87. **Extract as fixtures:** Yes - all 19 spec examples usable with provenance metadata

#### OpenSensorHub Real-World Examples (Q88-92):

88. **SWE Common examples:** DataStream schemas (all 3 encodings), Observations (all 3 encodings) from `/datastreams/{id}/...`
89. **Encoding complexity:** Higher than spec - 5-15 fields common, real sensor configurations
90. **Edge cases:** Non-standard extensions, encoding variations (delimiter choices, endianness preferences)
91. **Binary encoding examples:** Available via `/datastreams/{id}/observations?encoding=binary` - CRITICAL for testing
92. **Can OpenSensorHub provide binary examples?** Yes - request binary encoding, capture responses, document byte formats

#### Parser Implementation Testing (Q93-98):

93. **Parsing functions to unit test:** Per encoding - JSON (component parsing, nested structures), Text (delimiter parsing, CSV reading), Binary (byte reading, endianness handling, type decoding)
94. **Integration tests:** Full observation parsing (all 3 encodings), schema validation (observation vs DataStream schema), cross-encoding consistency
95. **Test organization:** 4 files - `swe-common-json.spec.ts`, `swe-common-text.spec.ts`, `swe-common-binary.spec.ts` (largest), `swe-common-schema-validation.spec.ts`
96. **Test depth per component type:** CRITICAL types (Quantity, Time, DataRecord, DataArray): 12-20 tests per encoding; HIGH types: 8-12 tests; MEDIUM: 5-8 tests; LOW: 2-5 tests
97. **Fixtures per component type:** JSON ~40, Text ~40, Binary ~40 (including hex dumps + expected + encoding defs); total ~120 fixtures
98. **Balance:** Prioritize spec examples (normative baseline); supplement with OpenSensorHub (real-world validation); add hand-crafted (error cases, edge cases)

### Next Steps

**Immediate (Implementation):**

1. **Define parser output TypeScript interfaces** — what do `parseSWEComponent()`, `parseBinaryEncoding()`, etc. return? This is the critical missing piece.
2. Create fixture directory structure (`fixtures/swe-common/json/`, `.../text/`, `.../binary/`, `.../schemas/`)
3. Extract spec examples from SWE Common 3.0 and CSAPI Part 2 specifications (19 examples)
4. Create hand-crafted fixtures (error cases, edge cases, specific test scenarios) — **do not fetch from live servers**
5. **CRITICAL:** Create binary fixture generation utilities (hex dump generator, .bin file creator, encoding applier)
6. Implement Phase 1 tests as `parseSWEComponent(fixture, encoding) → expectedTypedOutput` (CRITICAL - ~1,064 lines, ~50 tests, binary data types + endianness + DataRecord/DataArray)

**Near-Term:** 7. Implement Phase 2 tests (HIGH - ~654 lines, ~40 tests, simple components + binary component parsing) 8. Implement Phase 3 tests (MEDIUM - ~718 lines, ~54 tests, range/complex components + error handling) 9. Validate against all fixtures (~120 total) 10. Cross-validate with Section 9 (SensorML characteristics/capabilities use SWE Common) 11. Update Implementation Guide with fixture requirements and binary generation utilities

**Long-Term:** 12. Phase 4 enhancements (LOW priority - performance optimization, quality comprehensive parsing, reference frames) 13. Encoding conversion utilities (JSON ↔ Text ↔ Binary bidirectional) 14. Streaming support for very large datasets (incremental parsing) 15. CodeSpace vocabulary dereferencing (automatic term fetching)

### What This Unblocks

- ✅ **Section 9:** SensorML Testing (characteristics/capabilities fixtures shared with SWE Common)
- ✅ **Section 12:** QueryBuilder URL Construction Testing (observations endpoint requires SWE Common parsing in all 3 encodings)
- ✅ **Section 14:** Integration Test Workflow Design (observation workflow uses SWE Common for result parsing)
- ✅ **Section 15:** Fixture Sourcing Strategy (SWE Common fixture inventory - especially binary with hex dumps)
- ✅ **Section 36:** Test Quality Checklist (SWE Common test validation criteria, byte-level binary validation standards)

**Research Status:** COMPLETE ✅  
**All Success Criteria Met:** ✅  
**Reclassified:** Parser output model must be defined before tests can be implemented (Phase 2D, H1)  
**OpenSensorHub fixture sourcing:** Removed per Phase 2D, H2  
**Binary sections:** Directly usable for implementation (Phase 2D, M2)  
**Research questions (98):** Reflects research depth, not testing scope (Phase 2D, L3)  
**Ready for Implementation:** After defining parser TypeScript output interfaces  
**Estimated Implementation Effort:** 40-56 hours across 3 phases (binary ~50% of effort)

**CRITICAL NOTE:** Binary encoding testing is highest priority and highest complexity. Must allocate 20-30 hours (50% of total effort) to binary testing to ensure byte-level correctness, endianness handling, and IEEE 754 edge cases are thoroughly validated. This is the highest rejection risk in the entire CSAPI client library.
