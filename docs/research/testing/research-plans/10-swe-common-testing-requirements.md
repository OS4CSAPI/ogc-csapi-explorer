# Research Plan: SWE Common 3.0 Format Testing Requirements

**Section:** 10 of 38  
**Status:** Not Started  
**Last Updated:** February 5, 2026  
**Estimated Time:** 3-4 hours  
**Estimated Lines:** 1,700-2,500 lines

---

## 1. Research Objective

Define comprehensive testing requirements for SWE Common 3.0 parser covering all three encodings (JSON, Text, Binary), 12+ component types, and complex schema validation. Create detailed test plan that ensures binary encoding correctness and deep structural validation.

### Why This Research Tenth

**Dependency Chain:** After SensorML testing requirements (Section 9), address the even more complex SWE Common format.

**Highest Rejection Risk:** SWE Common is the most complex format in CSAPI with:

- **3 encodings:** JSON, Text (CSV-like), Binary (custom byte format)
- **12+ component types:** Quantity, Count, Boolean, Category, Text, Time, DataRecord, Vector, DataArray, Matrix, DataChoice, DataStream
- **Binary encoding complexity:** Endianness, IEEE 754 floats, multi-byte integers, variable-length data
- **Schema validation:** Observations must conform to DataStream schema
- **Recursive structures:** DataRecord within DataRecord, nested arrays

This research defines:

- **Encoding Coverage:** All three encodings with specific test strategies
- **Component Coverage:** All 12+ component types
- **Binary Encoding Tests:** Byte-level validation (most critical and error-prone)
- **Schema Validation:** Observation conformance to schema
- **Edge Cases:** Complex nesting, encoding edge cases, malformed data
- **Test Depth:** What constitutes "meaningful" SWE Common testing

### Sequencing Rationale

Section 9 addressed SensorML 3.0 format testing (systems, deployments, procedures encoding). Section 10 addresses SWE Common 3.0 format testing, which is even more complex due to three encodings and observation data parsing. SWE Common is used for DataStream capabilities, observation schemas, and observation results - making it critical for Part 2 CSAPI functionality. Binary encoding testing is the highest priority as it was a major weakness in previous iterations and has the highest rejection risk.

---

## 2. Research Questions

### Core Questions

1. What are all SWE Common 3.0 component types and their testing priorities across three encodings?
2. What are the binary encoding byte format specifications and how should they be tested?
3. What schema validation requirements exist for observations conforming to DataStream schemas?
4. What fixtures are available (spec examples vs OpenSensorHub) and how should binary fixtures be generated?
5. What constitutes "meaningful" SWE Common parser testing across JSON, Text, and Binary encodings?
6. What is the appropriate test organization strategy for three encodings and 12+ component types?

### Detailed Questions

### Detailed Questions

**SWE Common 3.0 Specification Analysis (10 questions):**

1. What are all the SWE Common component types defined in spec?
2. What properties are mandatory vs optional for each component?
3. What validation rules are normative (SHALL, MUST)?
4. How do the 3 encodings differ (JSON, Text, Binary)?
5. What encoding choice rules exist (when to use which)?
6. What are the recursive structure limits?
7. How does encoding definition work (BinaryEncoding, TextEncoding)?
8. What endianness rules exist for binary encoding?
9. What are the data type byte sizes (float32, float64, int8, int16, etc.)?
10. What block separation rules exist for binary arrays?

**JSON Encoding Requirements (7 questions):** 11. What JSON structure validation is required? 12. How to test DataRecord parsing (nested fields)? 13. How to test DataArray parsing (values array)? 14. How to test all 12+ component types in JSON? 15. What property validation is required (UOM, definition, quality)? 16. How to handle optional properties? 17. What JSON-specific edge cases exist?

**Text Encoding Requirements (7 questions):** 18. What delimiter characters are supported (comma, space, tab, custom)? 19. How to test token separator parsing? 20. How to test block separator parsing? 21. What decimal separator handling is required? 22. How to test quoted strings in text encoding? 23. What text encoding edge cases exist (escaped delimiters, whitespace)? 24. How to handle missing values in text encoding?

**Binary Encoding Requirements - CRITICAL (13 questions):** 25. What byte orders are supported (big-endian, little-endian)? 26. How to test float32 parsing (IEEE 754)? 27. How to test float64 parsing (IEEE 754)? 28. How to test int8/int16/int32/int64 parsing? 29. How to test uint8/uint16/uint32/uint64 parsing? 30. How to test boolean parsing (1 byte)? 31. How to test string parsing (length-prefixed or fixed)? 32. How to test time parsing (ISO 8601 in binary)? 33. How to test block separators in binary arrays? 34. What binary encoding edge cases exist? 35. How to handle byte alignment issues? 36. How to test variable-length binary data? 37. What endianness edge cases exist (mixed endianness)?

**Component Type Testing (12 questions):** 38. **Quantity:** What validation rules (value, UOM, quality)? 39. **Count:** What validation rules (value, constraint)? 40. **Boolean:** What validation rules (true/false)? 41. **Category:** What validation rules (value, codeSpace)? 42. **Text:** What validation rules (value, constraint)? 43. **Time:** What validation rules (value, UOM, referenceFrame)? 44. **DataRecord:** What validation rules (fields array, field definitions)? 45. **Vector:** What validation rules (coordinates, referenceFrame)? 46. **DataArray:** What validation rules (elementType, encoding, values)? 47. **Matrix:** What validation rules (rows, columns, element type)? 48. **DataChoice:** What validation rules (item array, selection mechanism)? 49. **DataStream:** What validation rules (elementType, encoding, values)?

**Nested Structure Testing (6 questions):** 50. How deep can DataRecord nesting go? 51. How to test DataRecord within DataRecord? 52. How to test DataArray of DataRecords? 53. How to test Matrix of DataRecords? 54. What performance issues with deep nesting? 55. What stack overflow risks exist?

**Schema Validation - Observations (6 questions):** 56. How to validate observation values against DataStream schema? 57. What validation rules exist for schema conformance? 58. How to test mismatched schemas (wrong field count, wrong types)? 59. How to test optional fields in schema? 60. How to test DataChoice selection against schema? 61. What error messages for schema violations?

**Units of Measure - UOM (4 questions):** 62. What UOM formats must be supported (UCUM, URI)? 63. How to validate UOM codes? 64. How to test UOM conversion (if any)? 65. What edge cases exist for UOM (missing, invalid, unrecognized)?

**Quality Information (4 questions):** 66. How to test quality indicators? 67. What quality types are defined (SimpleQuality, QuantityRange)? 68. How deep to validate quality information? 69. Is quality validation critical or optional?

**Time Reference Frames (4 questions):** 70. What time reference frames must be supported (ISO 8601, GPS, TAI)? 71. How to test time reference frame parsing? 72. How to validate time values against reference frame? 73. What edge cases exist (leap seconds, time zones)?

**Coordinate Reference Systems (3 questions):** 74. What CRS must be supported for Vector components? 75. How to test CRS parsing and validation? 76. How to handle missing CRS (default assumptions)?

**Error Handling (6 questions):** 77. What error conditions must be tested per encoding? 78. How to handle malformed JSON? 79. How to handle invalid text delimiters? 80. How to handle corrupted binary data? 81. How to handle schema mismatches? 82. What error messages should be provided per encoding?

**Specification Examples (5 questions):** 83. What complete observation examples exist in spec? 84. What encoding examples exist (JSON, Text, Binary)? 85. What component type examples exist? 86. What nested structure examples exist? 87. Can all spec examples be extracted as fixtures?

**OpenSensorHub Real-World Examples (5 questions):** 88. What SWE Common examples available from OpenSensorHub? 89. What encoding complexity exists in real-world data? 90. What edge cases do real-world examples expose? 91. What binary encoding examples exist? 92. Can OpenSensorHub provide binary observation examples?

**Parser Implementation Testing (6 questions):** 93. What parsing functions must be unit tested per encoding? 94. What integration tests needed (full observation parsing)? 95. What test organization (one file per encoding or combined)? 96. What test depth per component type? 97. How many fixtures per component type and encoding? 98. What's the balance between spec examples and hand-crafted tests?

---

## 3. Primary Resources

- **SWE Common 3.0 Specification:** https://docs.ogc.org/is/24-014/24-014.html
- **SWE Common 3.0 JSON Schema:** https://schemas.opengis.net/sweCommon/3.0/
- **CSAPI Implementation Guide:** [docs/planning/csapi-implementation-guide.md](../../../planning/csapi-implementation-guide.md) (SWE Common parser specification)

---

## 4. Supporting Resources

- **Section 8 Deliverable:** CSAPI specification requirements (SWE Common validation rules extracted)
- **Section 9 Deliverable:** SensorML testing requirements (integration context - characteristics/capabilities use SWE Common)
- **Format Requirements Analysis:** [docs/research/requirements/csapi-format-requirements.md](../../requirements/csapi-format-requirements.md)
- **OpenSensorHub Analysis:** [docs/research/requirements/csapi-opensensorhub-analysis.md](../../requirements/csapi-opensensorhub-analysis.md)
- Section 6 Deliverable: "Meaningful vs Trivial" guide (quality context for test depth)
- Section 1-2 Deliverables: Upstream format parser test patterns (quality benchmarks)
- JSON schema validator (tool)
- Binary hex editor/viewer (tool)
- Binary fixture generator (tool)
- OpenSensorHub API access (tool)

---

## 5. Research Methodology

## 5. Research Methodology

### Phase 1: SWE Common 3.0 Specification Deep Dive (60-90 minutes)

**Objective:** Extract all component types, encoding rules, and normative validation requirements

**Tasks:**

1. Read SWE Common 3.0 specification sections on all 3 encodings (JSON, Text, Binary)
2. Extract all component type definitions (12+ types: Quantity, Count, Boolean, Category, Text, Time, DataRecord, Vector, DataArray, Matrix, DataChoice, DataStream)
3. Document all normative validation rules (SHALL, MUST statements with spec references)
4. Extract encoding-specific rules for JSON, Text, and Binary encodings
5. Document binary encoding byte formats in detail (all data types, endianness, IEEE 754)
6. Extract all specification examples (with encoding type notation)
7. Create component type requirement matrix (per-type, per-encoding)
8. Create encoding-specific requirement matrices (focus on binary encoding complexity)

### Phase 2: JSON Schema Analysis (30-45 minutes)

**Objective:** Extract schema-level validation rules for JSON encoding

**Tasks:**

1. Parse SWE Common 3.0 JSON schemas from https://schemas.opengis.net/sweCommon/3.0/
2. Extract validation rules per component type (required/optional properties, constraints)
3. Document required vs optional properties for each component type
4. Document format and enumeration constraints (URI formats, UCUM codes, controlled vocabularies)
5. Cross-validate with specification text (identify conflicts or gaps)
6. Create schema validation checklist (what parser must enforce vs accept)

### Phase 3: Binary Encoding Deep Dive (45-60 minutes)

**Objective:** Document byte-level binary encoding specifications - MOST CRITICAL

**Tasks:**

1. Document all binary data type byte formats (boolean, int8-64, uint8-64, float32, float64, strings)
2. Create byte-level parsing specifications with hex examples
3. Document endianness handling (big-endian vs little-endian per data type)
4. Extract binary encoding examples from spec (with hex dumps if available)
5. Design binary encoding test strategy (byte-level validation, endianness tests, IEEE 754 edge cases)
6. Create binary fixture generation plan (how to create .bin files with known byte sequences)

### Phase 4: Example and Fixture Analysis (30-45 minutes)

**Objective:** Inventory available fixtures and assess complexity per encoding

**Tasks:**

1. Extract all specification examples organized by encoding (JSON, Text, Binary)
2. Fetch real-world examples from OpenSensorHub (all three encodings if available)
3. Analyze encoding complexity per example (nesting depth, component types used, data sizes)
4. Identify edge cases in real-world data (non-standard extensions, validation issues, encoding variations)
5. Document fixture sourcing strategy (spec examples priority, OpenSensorHub supplemental, binary generation requirements)
6. Create fixture inventory per encoding (categorized by component type, complexity, source)

### Phase 5: Test Strategy Design (30-45 minutes)

**Objective:** Create comprehensive test specification document with 18 required sections

**Tasks:**

1. Map component types to test requirements per encoding (12+ types × 3 encodings)
2. Define unit test scope per encoding (parsing functions, byte-level validation for binary)
3. Define integration test scope (schema validation, nested structures, full observation parsing)
4. Design fixture organization per encoding (separate directories, binary with hex dumps)
5. Define test depth per component type per encoding (CRITICAL/HIGH/MEDIUM/LOW priorities)
6. Create test specification document with all 18 required sections (detailed in Deliverable)

---

## 6. Success Criteria

This research is complete when:

- [ ] All 12+ SWE Common component types have test requirements defined for all 3 encodings
- [ ] Binary encoding byte formats documented in detail (all data types, endianness, IEEE 754)
- [ ] Endianness testing strategy defined (big-endian and little-endian explicit tests)
- [ ] IEEE 754 edge cases addressed (NaN, Infinity, -Infinity, denormalized numbers)
- [ ] Schema validation requirements complete (observation conformance to DataStream schema)
- [ ] Nested structure testing strategy defined (DataRecord nesting, DataArray of DataRecords)
- [ ] Fixture inventory complete (120+ fixtures: ~40 per encoding, including binary .bin files with hex dumps)
- [ ] Test depth defined meeting "meaningful" criteria from Section 6
- [ ] Error handling requirements specified per encoding (JSON parse errors, text delimiter errors, binary corruption)
- [ ] Test organization documented (3 files: JSON, Text, Binary + schema validation file)
- [ ] Test estimates realistic (1,700-2,500 lines total, binary encoding ~50% of effort)
- [ ] Validated against upstream patterns (Section 1-2 format parser test patterns)
- [ ] Cross-validated with Implementation Guide (SWE Common parser specification alignment)
- [ ] All 98 research questions answered with specific findings

---

## 7. Deliverable

**SWE Common 3.0 Parser Testing Specification document**

**Location:** `docs/research/testing/findings/10-swe-common-testing-requirements.md`

**Note:** This goes in `findings/` because it's detailed analysis (test strategy synthesis will occur in Section 14+).

Content includes:

Content includes:

1. **Executive Summary**

   - Total component types to test: 12+
   - Total encodings to test: 3 (JSON, Text, Binary)
   - Testing priorities per encoding (Binary is CRITICAL, JSON/Text are HIGH)
   - Fixture count requirements per encoding (~40 per encoding, 120+ total)
   - Estimated test lines (1,700-2,500 lines total)
   - Key testing challenges (binary encoding byte-level validation, endianness, IEEE 754, schema validation)

2. **Component Type Testing Requirements**

   ```markdown
   | Component Type | Priority | Encodings to Test      | Fixtures Needed           | Test Lines Estimate |
   | -------------- | -------- | ---------------------- | ------------------------- | ------------------- |
   | Quantity       | CRITICAL | JSON, Text, Binary     | 4 per encoding (12 total) | 120-180             |
   | Count          | HIGH     | JSON, Text, Binary     | 3 per encoding (9 total)  | 90-120              |
   | Boolean        | HIGH     | JSON, Text, Binary     | 2 per encoding (6 total)  | 60-80               |
   | Category       | MEDIUM   | JSON, Text, Binary     | 2 per encoding (6 total)  | 60-80               |
   | Text           | HIGH     | JSON, Text, Binary     | 3 per encoding (9 total)  | 90-120              |
   | Time           | CRITICAL | JSON, Text, Binary     | 4 per encoding (12 total) | 120-180             |
   | DataRecord     | CRITICAL | JSON, Text, Binary     | 5 per encoding (15 total) | 200-300             |
   | Vector         | MEDIUM   | JSON, Text, Binary     | 2 per encoding (6 total)  | 60-90               |
   | DataArray      | CRITICAL | JSON, Text, Binary     | 6 per encoding (18 total) | 250-400             |
   | Matrix         | LOW      | JSON, Text, Binary     | 2 per encoding (6 total)  | 60-90               |
   | DataChoice     | MEDIUM   | JSON, Text, Binary     | 3 per encoding (9 total)  | 90-150              |
   | DataStream     | HIGH     | JSON, Text, Binary     | 4 per encoding (12 total) | 150-200             |
   | **TOTAL**      |          | **36 test categories** | **~120 fixtures**         | **~1,350-1,990**    |
   ```

3. **Encoding-Specific Test Requirements**

   **JSON Encoding Testing:**

   ```markdown
   | Test Category       | Test Count | Lines per Test | Total Lines | Priority |
   | ------------------- | ---------- | -------------- | ----------- | -------- |
   | All component types | 12         | 10-15          | 120-180     | HIGH     |
   | Nested DataRecords  | 4          | 15-20          | 60-80       | HIGH     |
   | DataArray parsing   | 6          | 15-25          | 90-150      | CRITICAL |
   | Schema validation   | 5          | 12-18          | 60-90       | CRITICAL |
   | Error handling      | 6          | 8-12           | 48-72       | MEDIUM   |
   | **JSON TOTAL**      | **33**     | **~12 avg**    | **378-572** |          |
   ```

   **Text Encoding Testing:**

   ```markdown
   | Test Category        | Test Count | Lines per Test | Total Lines | Priority |
   | -------------------- | ---------- | -------------- | ----------- | -------- |
   | All component types  | 12         | 10-15          | 120-180     | HIGH     |
   | Delimiter variations | 5          | 12-15          | 60-75       | HIGH     |
   | DataArray parsing    | 6          | 15-20          | 90-120      | CRITICAL |
   | Quoted strings       | 3          | 10-12          | 30-36       | MEDIUM   |
   | Missing values       | 3          | 10-12          | 30-36       | MEDIUM   |
   | Error handling       | 5          | 8-12           | 40-60       | MEDIUM   |
   | **Text TOTAL**       | **34**     | **~11 avg**    | **370-507** |          |
   ```

   **Binary Encoding Testing (MOST CRITICAL):**

   ```markdown
   | Test Category                     | Test Count | Lines per Test | Total Lines   | Priority |
   | --------------------------------- | ---------- | -------------- | ------------- | -------- |
   | All component types               | 12         | 12-20          | 144-240       | CRITICAL |
   | Endianness (big/little)           | 8          | 15-20          | 120-160       | CRITICAL |
   | Float32/Float64 (IEEE 754)        | 6          | 15-25          | 90-150        | CRITICAL |
   | Integer types (int8-64, uint8-64) | 8          | 12-18          | 96-144        | CRITICAL |
   | DataArray binary parsing          | 8          | 20-30          | 160-240       | CRITICAL |
   | Block separators                  | 4          | 15-20          | 60-80         | HIGH     |
   | Variable-length data              | 4          | 15-20          | 60-80         | HIGH     |
   | Schema validation                 | 5          | 15-20          | 75-100        | HIGH     |
   | Error handling (corrupted data)   | 6          | 10-15          | 60-90         | HIGH     |
   | **Binary TOTAL**                  | **61**     | **~14 avg**    | **865-1,284** |          |
   ```

4. **Binary Encoding Byte Format Specifications**

   ```markdown
   | Data Type        | Byte Size | Endianness | Format                    | Test Fixtures Needed   |
   | ---------------- | --------- | ---------- | ------------------------- | ---------------------- |
   | boolean          | 1         | N/A        | 0x00 (false), 0x01 (true) | 2                      |
   | byte (int8)      | 1         | N/A        | Signed byte               | 2                      |
   | ubyte (uint8)    | 1         | N/A        | Unsigned byte             | 2                      |
   | short (int16)    | 2         | Big/Little | Signed 16-bit             | 4 (2 per endian)       |
   | ushort (uint16)  | 2         | Big/Little | Unsigned 16-bit           | 4                      |
   | int (int32)      | 4         | Big/Little | Signed 32-bit             | 4                      |
   | uint (uint32)    | 4         | Big/Little | Unsigned 32-bit           | 4                      |
   | long (int64)     | 8         | Big/Little | Signed 64-bit             | 4                      |
   | ulong (uint64)   | 8         | Big/Little | Unsigned 64-bit           | 4                      |
   | float (float32)  | 4         | Big/Little | IEEE 754 single           | 6 (including NaN, Inf) |
   | double (float64) | 8         | Big/Little | IEEE 754 double           | 6 (including NaN, Inf) |
   | string (ASCII)   | Variable  | N/A        | Length-prefixed or fixed  | 4                      |
   | string (UTF-8)   | Variable  | N/A        | Length-prefixed or fixed  | 4                      |
   ```

   **Example Binary Test Fixture:**

   ```
   Hex: 40 49 0F DB (big-endian float32)
   Value: 3.14159 (π approximation)

   Test: Parse as big-endian float32, assert value ≈ 3.14159
   ```

5. **Property Testing Matrix per Component Type**

   **Example: Quantity Component**

   ```markdown
   | Property   | JSON     | Text     | Binary                  | Validation Rules        | Edge Cases                 | Priority |
   | ---------- | -------- | -------- | ----------------------- | ----------------------- | -------------------------- | -------- |
   | value      | Required | Required | Required                | Numeric                 | NaN, Inf, -Inf, very large | CRITICAL |
   | uom.code   | Optional | Optional | N/A (separate encoding) | UCUM or URI             | Missing, invalid code      | HIGH     |
   | quality    | Optional | Optional | Optional                | Valid quality structure | Missing, complex nesting   | MEDIUM   |
   | definition | Optional | N/A      | N/A                     | Valid URI               | Relative URI, missing      | LOW      |
   ```

   Repeat for all 12+ component types (Quantity, Count, Boolean, Category, Text, Time, DataRecord, Vector, DataArray, Matrix, DataChoice, DataStream).

6. **Nested Structure Testing**

   ```markdown
   | Nesting Scenario                        | Complexity | Encodings | Fixtures Needed    | Test Lines | Priority |
   | --------------------------------------- | ---------- | --------- | ------------------ | ---------- | -------- |
   | DataRecord with 5 simple fields         | Low        | All 3     | 3 (1 per encoding) | 30-45      | CRITICAL |
   | DataRecord within DataRecord (2 levels) | Medium     | All 3     | 3                  | 45-60      | HIGH     |
   | DataRecord within DataRecord (3 levels) | High       | All 3     | 3                  | 60-90      | MEDIUM   |
   | DataArray of DataRecords                | High       | All 3     | 3                  | 60-90      | CRITICAL |
   | DataArray of DataArrays                 | High       | All 3     | 3                  | 60-90      | MEDIUM   |
   | Matrix of DataRecords                   | Very High  | All 3     | 3                  | 90-120     | LOW      |
   ```

7. **Schema Validation Testing**

   ```markdown
   | Validation Scenario                          | Test Requirement                 | Priority |
   | -------------------------------------------- | -------------------------------- | -------- |
   | Values match schema exactly                  | Assert field count, types, order | CRITICAL |
   | Schema has optional field, value missing     | Should pass                      | HIGH     |
   | Schema has optional field, value present     | Should pass                      | HIGH     |
   | Value has extra field not in schema          | Should warn or error             | MEDIUM   |
   | Value missing required field                 | Should error                     | CRITICAL |
   | Value field type mismatch (string vs number) | Should error                     | CRITICAL |
   | DataChoice selection matches schema option   | Should pass                      | MEDIUM   |
   | DataArray element count matches schema       | Should pass                      | HIGH     |
   ```

8. **Error Condition Testing per Encoding**

   **JSON Encoding Errors:**

   ```markdown
   | Error Condition           | Test Scenario                      | Expected Error   | Priority |
   | ------------------------- | ---------------------------------- | ---------------- | -------- |
   | Malformed JSON            | Invalid JSON syntax                | Parse error      | HIGH     |
   | Missing required property | Quantity without value             | Validation error | HIGH     |
   | Invalid type              | value = "string" instead of number | Type error       | HIGH     |
   | Unknown component type    | type = "UnknownComponent"          | Error or warning | MEDIUM   |
   ```

   **Text Encoding Errors:**

   ```markdown
   | Error Condition        | Test Scenario               | Expected Error                 | Priority |
   | ---------------------- | --------------------------- | ------------------------------ | -------- |
   | Incorrect delimiter    | Expected comma, got tab     | Parse error                    | HIGH     |
   | Missing value          | "1.5,,3.7" (empty token)    | Missing value error or default | HIGH     |
   | Invalid numeric format | "1.5.3" (double decimal)    | Parse error                    | MEDIUM   |
   | Unmatched quotes       | "text without closing quote | Parse error                    | MEDIUM   |
   ```

   **Binary Encoding Errors (CRITICAL):**

   ```markdown
   | Error Condition            | Test Scenario                            | Expected Error                       | Priority |
   | -------------------------- | ---------------------------------------- | ------------------------------------ | -------- |
   | Insufficient bytes         | Buffer ends mid-value                    | Truncation error                     | CRITICAL |
   | Wrong endianness detection | Parse as big-endian when little-endian   | Wrong value (should detect or error) | HIGH     |
   | Invalid byte sequence      | 0xFF 0xFF 0xFF 0xFF (NaN or invalid)     | Handle gracefully (NaN)              | MEDIUM   |
   | Misaligned data            | Wrong byte offset                        | Parse error or wrong value           | HIGH     |
   | Block separator violation  | Missing separator between array elements | Parse error                          | MEDIUM   |
   ```

9. **Specification Example Fixtures**

   ```markdown
   | Spec Section | Example Type | Encoding | Component Type | Complexity | Usable | Notes                                      |
   | ------------ | ------------ | -------- | -------------- | ---------- | ------ | ------------------------------------------ |
   | §7.2         | DataRecord   | JSON     | DataRecord     | Medium     | Yes    | Weather observation (3 fields)             |
   | §8.1         | Quantity     | JSON     | Quantity       | Simple     | Yes    | Temperature with UOM                       |
   | §9.1         | DataArray    | JSON     | DataArray      | High       | Yes    | Time series (10 observations)              |
   | §10.1        | DataArray    | Text     | DataArray      | High       | Yes    | CSV-like observation array                 |
   | §11.1        | DataArray    | Binary   | DataArray      | Very High  | Yes    | Binary observation array with encoding def |
   | ...          | ...          | ...      | ...            | ...        | ...    | ...                                        |
   ```

10. **OpenSensorHub Fixture Inventory**

    ```markdown
    | Resource URL                                         | Encoding | Component Type | Complexity | Usable | Notes                                    |
    | ---------------------------------------------------- | -------- | -------------- | ---------- | ------ | ---------------------------------------- |
    | /datastreams/temp-ds-01/observations?encoding=json   | JSON     | DataArray      | Medium     | Yes    | Real temperature observations            |
    | /datastreams/temp-ds-01/observations?encoding=text   | Text     | DataArray      | Medium     | Yes    | CSV-format observations                  |
    | /datastreams/temp-ds-01/observations?encoding=binary | Binary   | DataArray      | High       | Yes    | Binary observation array (CRITICAL TEST) |
    | ...                                                  | ...      | ...            | ...        | ...    | ...                                      |
    ```

11. **Test Organization**

    ```markdown
    Test Files:

    - `src/ogc-api/formats/swe-common-json.spec.ts` (JSON encoding)
    - `src/ogc-api/formats/swe-common-text.spec.ts` (Text encoding)
    - `src/ogc-api/formats/swe-common-binary.spec.ts` (Binary encoding - LARGEST FILE)
    - `src/ogc-api/formats/swe-common-schema-validation.spec.ts` (Schema validation)

    Binary Test File Structure:

    - describe('SWE Common Binary Encoding')
      - describe('Data Type Parsing')
        - describe('Float32 (IEEE 754)')
          - it('should parse big-endian float32')
          - it('should parse little-endian float32')
          - it('should handle NaN')
          - it('should handle Infinity')
          - ...
        - describe('Float64 (IEEE 754)')
          - ...
        - describe('Integer Types')
          - it('should parse int8')
          - it('should parse uint8')
          - it('should parse big-endian int16')
          - it('should parse little-endian int16')
          - ...
      - describe('Component Type Parsing')
        - describe('Quantity Binary')
          - it('should parse quantity value')
          - ...
        - describe('DataRecord Binary')
          - ...
        - describe('DataArray Binary')
          - it('should parse simple array')
          - it('should parse array with block separators')
          - it('should parse array of records')
          - ...
      - describe('Error Handling')
        - it('should error on insufficient bytes')
        - it('should handle corrupted data')
        - ...
    ```

12. **Test Depth Definition**

    **"Meaningful" SWE Common Test Characteristics:**

    ✅ **DO:**

    - Parse complete fixture in all 3 encodings
    - Validate byte-level correctness for binary encoding
    - Test schema validation with mismatches
    - Test nested structures (DataRecord in DataRecord, DataArray of DataRecords)
    - Test all data type variations (float32, float64, int types)
    - Test endianness explicitly (big and little)
    - Test error conditions per encoding
    - Use real spec examples or OpenSensorHub data

    ❌ **DON'T (Trivial):**

    - Just check `result !== null`
    - Skip binary encoding tests (most critical)
    - Test only JSON (easiest, but not sufficient)
    - Use overly simple hand-crafted fixtures when spec examples exist
    - Skip schema validation
    - Skip endianness testing
    - Test only happy path without edge cases

13. **Fixture Requirements**

    ```markdown
    Fixture Directories:

    - `fixtures/swe-common/json/` (~40 fixtures)
    - `fixtures/swe-common/text/` (~40 fixtures)
    - `fixtures/swe-common/binary/` (~40 fixtures, includes .bin files + hex dumps)
    - `fixtures/swe-common/schemas/` (DataStream schemas for validation)

    Binary Fixtures Should Include:

    - Hex dump (.hex or .txt with hex representation)
    - Binary file (.bin)
    - Expected parsed result (.json for comparison)
    - Encoding definition (BinaryEncoding structure)

    Example Binary Fixture Set:

    - quantity-float32-big-endian.bin + .hex + expected.json
    - quantity-float32-little-endian.bin + .hex + expected.json
    - dataarray-observations-10.bin + .hex + expected.json + schema.json

    Total: ~120 fixtures across all encodings
    ```

14. **Validation Against Upstream Patterns**

    Compare with Section 1-2 findings:

    - How does EDR test SWE Common parsing?
    - What encoding coverage do other implementations have?
    - Is binary encoding tested upstream?
    - What test depth do other implementations use?
    - Are we aligned with upstream quality standards?

15. **Integration with Implementation Guide**

    Cross-validate with Implementation Guide SWE Common parser specification:

    - ✅ Aligned: Test requirement matches Implementation Guide
    - ⚠️ Gap: Test requirement not addressed in Implementation Guide
    - ❌ Conflict: Test requirement conflicts with Implementation Guide

16. **Testing Estimates**

    ```markdown
    | Encoding          | Test Count | Lines per Test | Total Lines     | Time Estimate   |
    | ----------------- | ---------- | -------------- | --------------- | --------------- |
    | JSON              | 33         | 11-17          | 378-572         | 5-7 hours       |
    | Text              | 34         | 11-15          | 370-507         | 5-7 hours       |
    | Binary            | 61         | 14-21          | 865-1,284       | 12-18 hours     |
    | Schema Validation | 8          | 12-15          | 96-120          | 2-3 hours       |
    | **TOTAL**         | **136**    | **~13 avg**    | **1,709-2,483** | **24-35 hours** |
    ```

    **Note:** Binary encoding is ~50% of total effort due to complexity.

17. **Testing Priorities**

    **CRITICAL (Must Have):**

    - JSON encoding for all component types
    - Binary encoding for primitive types (float, int)
    - Binary DataArray parsing (observations)
    - Schema validation for observations
    - Endianness handling
    - Error handling per encoding

    **HIGH (Should Have):**

    - Text encoding for all component types
    - Binary encoding for complex types (DataRecord, DataChoice)
    - All spec example coverage
    - Nested structure parsing
    - Real-world fixtures from OpenSensorHub

    **MEDIUM (Nice to Have):**

    - Advanced binary edge cases (NaN, Inf handling)
    - Performance testing (large arrays)
    - Matrix and DataStream components
    - Quality information parsing

    **LOW (Optional):**

    - Time reference frame validation
    - CRS validation for Vector
    - Advanced DataChoice logic

18. **Risks and Edge Cases**
    ```markdown
    | Risk/Edge Case                             | Likelihood | Impact   | Mitigation                                                |
    | ------------------------------------------ | ---------- | -------- | --------------------------------------------------------- |
    | Binary encoding bugs cause data corruption | High       | CRITICAL | Extensive binary testing; byte-level validation           |
    | Endianness detection wrong                 | Medium     | High     | Explicit endianness tests; encoding definition validation |
    | IEEE 754 edge cases (NaN, Inf)             | Medium     | Medium   | Specific edge case tests; graceful handling               |
    | Very large arrays cause memory issues      | Low        | Medium   | Test with realistic sizes; streaming if needed            |
    | Schema validation too strict               | Medium     | Medium   | Follow spec strictly; configurable validation             |
    | OpenSensorHub binary examples unavailable  | High       | Medium   | Generate binary fixtures from spec; hex dumps             |
    ```

---

## 8. Dependencies

**Must Complete Before Starting:**

- Section 8: CSAPI Specification Test Requirements (SWE Common validation rules extracted)
- Section 9: SensorML Testing Requirements (integration context - characteristics/capabilities use SWE Common)
- Section 6: "Meaningful vs Trivial" Definition (test depth guidance)
- Section 1-2: Upstream format parser test patterns (quality benchmarks)
- **Format Requirements Analysis:** [docs/research/requirements/csapi-format-requirements.md](../../requirements/csapi-format-requirements.md)

**Blocks (Critical For):**

- Section 9: SensorML Testing (characteristics/capabilities integration - SWE Common DataRecords)
- Section 12: QueryBuilder Testing (observations endpoint requires SWE Common parsing in all 3 encodings)
- Section 14: Integration Test Workflows (observation workflow uses SWE Common)
- Section 15: Fixture Sourcing Strategy (SWE Common fixture inventory, especially binary generation)
- Section 36: Test Quality Checklist (SWE Common test validation criteria)

---

## 9. Research Status Checklist

- [ ] Phase 1: SWE Common 3.0 Specification Deep Dive (60-90 min) - Complete
- [ ] Phase 2: JSON Schema Analysis (30-45 min) - Complete
- [ ] Phase 3: Binary Encoding Deep Dive (45-60 min) - Complete
- [ ] Phase 4: Example and Fixture Analysis (30-45 min) - Complete
- [ ] Phase 5: Test Strategy Design (30-45 min) - Complete
- [ ] Deliverable document created and reviewed
- [ ] All component type matrices complete (12+ types × 3 encodings)
- [ ] Binary encoding byte format specifications complete
- [ ] Fixture inventory complete (~120 fixtures cataloged including binary .bin files)
- [ ] Cross-validation with Implementation Guide complete

---

## 10. Notes and Open Questions

<!-- Add notes and unresolved questions here as research progresses -->

**Initial Observations:**

- SWE Common is most complex format in CSAPI (3 encodings, 12+ component types)
- Binary encoding is highest priority and highest risk (byte-level parsing, endianness, IEEE 754)
- Format parsing weakness in previous iteration - must be extremely thorough
- Real-world binary examples from OpenSensorHub may be difficult to obtain
- Binary fixture generation will require custom utilities

**Risks and Mitigation:**

**Risk:** Binary encoding complexity may lead to bugs and insufficient testing  
**Mitigation:** Prioritize binary tests (~50% of effort); extensive byte-level validation; explicit endianness tests (big-endian and little-endian)

**Risk:** Binary fixtures may be hard to source or generate  
**Mitigation:** Generate from spec examples; create hex dump utilities; use OpenSensorHub if available; manual binary file creation with known byte sequences

**Risk:** Schema validation may be overly complex  
**Mitigation:** Start with simple validation (field count, types, order); iterate based on real-world requirements; configurable strictness

**Risk:** Test suite may be very large (2,000+ lines)  
**Mitigation:** Organize into 4 separate files (JSON, Text, Binary, Schema); prioritize critical tests first; use test generation utilities for repetitive byte-level tests

**Validation Strategy:**

- All component types from spec covered across all 3 encodings
- All 3 encodings thoroughly tested (not just JSON)
- Binary encoding has majority of test effort (~50% - 865-1,284 lines)
- Test depth meets "meaningful" criteria from Section 6
- Fixture count sufficient for coverage (120+ fixtures including binary .bin files with hex dumps)
- Test estimates realistic (1,700-2,500 lines total)
- Schema validation comprehensive (observation conformance to DataStream schema)
- Error conditions comprehensive per encoding (malformed JSON, delimiter errors, binary corruption)

**Next Steps After Completion:**

1. Use test requirements to implement SWE Common parser tests (Phase 3, Task 16)
2. Generate or source binary fixtures (CRITICAL - create utilities for binary file generation)
3. Design test file structure (4 files: JSON, Text, Binary, Schema validation)
4. Validate test coverage against specification requirements (Section 8 cross-check)
5. Create binary fixture generation utilities (hex-to-bin, encoding definition applier)

---

**Actual Research Time:** _[To be filled during research execution]_  
**Started:** _[Date when research begins]_  
**Completed:** _[Date when deliverable is finished]_

```markdown
| Component Type | Priority | Encodings to Test      | Fixtures Needed           | Test Lines Estimate |
| -------------- | -------- | ---------------------- | ------------------------- | ------------------- |
| Quantity       | CRITICAL | JSON, Text, Binary     | 4 per encoding (12 total) | 120-180             |
| Count          | HIGH     | JSON, Text, Binary     | 3 per encoding (9 total)  | 90-120              |
| Boolean        | HIGH     | JSON, Text, Binary     | 2 per encoding (6 total)  | 60-80               |
| Category       | MEDIUM   | JSON, Text, Binary     | 2 per encoding (6 total)  | 60-80               |
| Text           | HIGH     | JSON, Text, Binary     | 3 per encoding (9 total)  | 90-120              |
| Time           | CRITICAL | JSON, Text, Binary     | 4 per encoding (12 total) | 120-180             |
| DataRecord     | CRITICAL | JSON, Text, Binary     | 5 per encoding (15 total) | 200-300             |
| Vector         | MEDIUM   | JSON, Text, Binary     | 2 per encoding (6 total)  | 60-90               |
| DataArray      | CRITICAL | JSON, Text, Binary     | 6 per encoding (18 total) | 250-400             |
| Matrix         | LOW      | JSON, Text, Binary     | 2 per encoding (6 total)  | 60-90               |
| DataChoice     | MEDIUM   | JSON, Text, Binary     | 3 per encoding (9 total)  | 90-150              |
| DataStream     | HIGH     | JSON, Text, Binary     | 4 per encoding (12 total) | 150-200             |
| **TOTAL**      |          | **36 test categories** | **~120 fixtures**         | **~1,350-1,990**    |
```

#### 3. Encoding-Specific Test Requirements

##### JSON Encoding Testing

```markdown
| Test Category       | Test Count | Lines per Test | Total Lines | Priority |
| ------------------- | ---------- | -------------- | ----------- | -------- |
| All component types | 12         | 10-15          | 120-180     | HIGH     |
| Nested DataRecords  | 4          | 15-20          | 60-80       | HIGH     |
| DataArray parsing   | 6          | 15-25          | 90-150      | CRITICAL |
| Schema validation   | 5          | 12-18          | 60-90       | CRITICAL |
| Error handling      | 6          | 8-12           | 48-72       | MEDIUM   |
| **JSON TOTAL**      | **33**     | **~12 avg**    | **378-572** |          |
```

##### Text Encoding Testing

```markdown
| Test Category        | Test Count | Lines per Test | Total Lines | Priority |
| -------------------- | ---------- | -------------- | ----------- | -------- |
| All component types  | 12         | 10-15          | 120-180     | HIGH     |
| Delimiter variations | 5          | 12-15          | 60-75       | HIGH     |
| DataArray parsing    | 6          | 15-20          | 90-120      | CRITICAL |
| Quoted strings       | 3          | 10-12          | 30-36       | MEDIUM   |
| Missing values       | 3          | 10-12          | 30-36       | MEDIUM   |
| Error handling       | 5          | 8-12           | 40-60       | MEDIUM   |
| **Text TOTAL**       | **34**     | **~11 avg**    | **370-507** |          |
```

##### Binary Encoding Testing (MOST CRITICAL)

```markdown
| Test Category                     | Test Count | Lines per Test | Total Lines   | Priority |
| --------------------------------- | ---------- | -------------- | ------------- | -------- |
| All component types               | 12         | 12-20          | 144-240       | CRITICAL |
| Endianness (big/little)           | 8          | 15-20          | 120-160       | CRITICAL |
| Float32/Float64 (IEEE 754)        | 6          | 15-25          | 90-150        | CRITICAL |
| Integer types (int8-64, uint8-64) | 8          | 12-18          | 96-144        | CRITICAL |
| DataArray binary parsing          | 8          | 20-30          | 160-240       | CRITICAL |
| Block separators                  | 4          | 15-20          | 60-80         | HIGH     |
| Variable-length data              | 4          | 15-20          | 60-80         | HIGH     |
| Schema validation                 | 5          | 15-20          | 75-100        | HIGH     |
| Error handling (corrupted data)   | 6          | 10-15          | 60-90         | HIGH     |
| **Binary TOTAL**                  | **61**     | **~14 avg**    | **865-1,284** |          |
```

#### 4. Binary Encoding Byte Format Specifications

```markdown
| Data Type        | Byte Size | Endianness | Format                    | Test Fixtures Needed   |
| ---------------- | --------- | ---------- | ------------------------- | ---------------------- |
| boolean          | 1         | N/A        | 0x00 (false), 0x01 (true) | 2                      |
| byte (int8)      | 1         | N/A        | Signed byte               | 2                      |
| ubyte (uint8)    | 1         | N/A        | Unsigned byte             | 2                      |
| short (int16)    | 2         | Big/Little | Signed 16-bit             | 4 (2 per endian)       |
| ushort (uint16)  | 2         | Big/Little | Unsigned 16-bit           | 4                      |
| int (int32)      | 4         | Big/Little | Signed 32-bit             | 4                      |
| uint (uint32)    | 4         | Big/Little | Unsigned 32-bit           | 4                      |
| long (int64)     | 8         | Big/Little | Signed 64-bit             | 4                      |
| ulong (uint64)   | 8         | Big/Little | Unsigned 64-bit           | 4                      |
| float (float32)  | 4         | Big/Little | IEEE 754 single           | 6 (including NaN, Inf) |
| double (float64) | 8         | Big/Little | IEEE 754 double           | 6 (including NaN, Inf) |
| string (ASCII)   | Variable  | N/A        | Length-prefixed or fixed  | 4                      |
| string (UTF-8)   | Variable  | N/A        | Length-prefixed or fixed  | 4                      |
```

**Example Binary Test Fixture:**

```
Hex: 40 49 0F DB (big-endian float32)
Value: 3.14159 (π approximation)

Test: Parse as big-endian float32, assert value ≈ 3.14159
```

#### 5. Property Testing Matrix per Component Type

**Example: Quantity Component**

```markdown
| Property   | JSON     | Text     | Binary                  | Validation Rules        | Edge Cases                 | Priority |
| ---------- | -------- | -------- | ----------------------- | ----------------------- | -------------------------- | -------- |
| value      | Required | Required | Required                | Numeric                 | NaN, Inf, -Inf, very large | CRITICAL |
| uom.code   | Optional | Optional | N/A (separate encoding) | UCUM or URI             | Missing, invalid code      | HIGH     |
| quality    | Optional | Optional | Optional                | Valid quality structure | Missing, complex nesting   | MEDIUM   |
| definition | Optional | N/A      | N/A                     | Valid URI               | Relative URI, missing      | LOW      |
```

Repeat for all 12+ component types.

#### 6. Nested Structure Testing

```markdown
| Nesting Scenario                        | Complexity | Encodings | Fixtures Needed    | Test Lines | Priority |
| --------------------------------------- | ---------- | --------- | ------------------ | ---------- | -------- |
| DataRecord with 5 simple fields         | Low        | All 3     | 3 (1 per encoding) | 30-45      | CRITICAL |
| DataRecord within DataRecord (2 levels) | Medium     | All 3     | 3                  | 45-60      | HIGH     |
| DataRecord within DataRecord (3 levels) | High       | All 3     | 3                  | 60-90      | MEDIUM   |
| DataArray of DataRecords                | High       | All 3     | 3                  | 60-90      | CRITICAL |
| DataArray of DataArrays                 | High       | All 3     | 3                  | 60-90      | MEDIUM   |
| Matrix of DataRecords                   | Very High  | All 3     | 3                  | 90-120     | LOW      |
```

#### 7. Schema Validation Testing

```markdown
| Validation Scenario                          | Test Requirement                 | Priority |
| -------------------------------------------- | -------------------------------- | -------- |
| Values match schema exactly                  | Assert field count, types, order | CRITICAL |
| Schema has optional field, value missing     | Should pass                      | HIGH     |
| Schema has optional field, value present     | Should pass                      | HIGH     |
| Value has extra field not in schema          | Should warn or error             | MEDIUM   |
| Value missing required field                 | Should error                     | CRITICAL |
| Value field type mismatch (string vs number) | Should error                     | CRITICAL |
| DataChoice selection matches schema option   | Should pass                      | MEDIUM   |
| DataArray element count matches schema       | Should pass                      | HIGH     |
```

#### 8. Error Condition Testing per Encoding

##### JSON Encoding Errors

```markdown
| Error Condition           | Test Scenario                      | Expected Error   | Priority |
| ------------------------- | ---------------------------------- | ---------------- | -------- |
| Malformed JSON            | Invalid JSON syntax                | Parse error      | HIGH     |
| Missing required property | Quantity without value             | Validation error | HIGH     |
| Invalid type              | value = "string" instead of number | Type error       | HIGH     |
| Unknown component type    | type = "UnknownComponent"          | Error or warning | MEDIUM   |
```

##### Text Encoding Errors

```markdown
| Error Condition        | Test Scenario               | Expected Error                 | Priority |
| ---------------------- | --------------------------- | ------------------------------ | -------- |
| Incorrect delimiter    | Expected comma, got tab     | Parse error                    | HIGH     |
| Missing value          | "1.5,,3.7" (empty token)    | Missing value error or default | HIGH     |
| Invalid numeric format | "1.5.3" (double decimal)    | Parse error                    | MEDIUM   |
| Unmatched quotes       | "text without closing quote | Parse error                    | MEDIUM   |
```

##### Binary Encoding Errors (CRITICAL)

```markdown
| Error Condition            | Test Scenario                            | Expected Error                       | Priority |
| -------------------------- | ---------------------------------------- | ------------------------------------ | -------- |
| Insufficient bytes         | Buffer ends mid-value                    | Truncation error                     | CRITICAL |
| Wrong endianness detection | Parse as big-endian when little-endian   | Wrong value (should detect or error) | HIGH     |
| Invalid byte sequence      | 0xFF 0xFF 0xFF 0xFF (NaN or invalid)     | Handle gracefully (NaN)              | MEDIUM   |
| Misaligned data            | Wrong byte offset                        | Parse error or wrong value           | HIGH     |
| Block separator violation  | Missing separator between array elements | Parse error                          | MEDIUM   |
```

#### 9. Specification Example Fixtures

```markdown
| Spec Section | Example Type | Encoding | Component Type | Complexity | Usable | Notes                                      |
| ------------ | ------------ | -------- | -------------- | ---------- | ------ | ------------------------------------------ |
| §7.2         | DataRecord   | JSON     | DataRecord     | Medium     | Yes    | Weather observation (3 fields)             |
| §8.1         | Quantity     | JSON     | Quantity       | Simple     | Yes    | Temperature with UOM                       |
| §9.1         | DataArray    | JSON     | DataArray      | High       | Yes    | Time series (10 observations)              |
| §10.1        | DataArray    | Text     | DataArray      | High       | Yes    | CSV-like observation array                 |
| §11.1        | DataArray    | Binary   | DataArray      | Very High  | Yes    | Binary observation array with encoding def |
| ...          | ...          | ...      | ...            | ...        | ...    | ...                                        |
```

#### 10. OpenSensorHub Fixture Inventory

```markdown
| Resource URL                                         | Encoding | Component Type | Complexity | Usable | Notes                                    |
| ---------------------------------------------------- | -------- | -------------- | ---------- | ------ | ---------------------------------------- |
| /datastreams/temp-ds-01/observations?encoding=json   | JSON     | DataArray      | Medium     | Yes    | Real temperature observations            |
| /datastreams/temp-ds-01/observations?encoding=text   | Text     | DataArray      | Medium     | Yes    | CSV-format observations                  |
| /datastreams/temp-ds-01/observations?encoding=binary | Binary   | DataArray      | High       | Yes    | Binary observation array (CRITICAL TEST) |
| ...                                                  | ...      | ...            | ...        | ...    | ...                                      |
```

#### 11. Test Organization

```markdown
Test Files:

- `src/ogc-api/formats/swe-common-json.spec.ts` (JSON encoding)
- `src/ogc-api/formats/swe-common-text.spec.ts` (Text encoding)
- `src/ogc-api/formats/swe-common-binary.spec.ts` (Binary encoding - LARGEST FILE)
- `src/ogc-api/formats/swe-common-schema-validation.spec.ts` (Schema validation)

Binary Test File Structure:

- describe('SWE Common Binary Encoding')
  - describe('Data Type Parsing')
    - describe('Float32 (IEEE 754)')
      - it('should parse big-endian float32')
      - it('should parse little-endian float32')
      - it('should handle NaN')
      - it('should handle Infinity')
      - ...
    - describe('Float64 (IEEE 754)')
      - ...
    - describe('Integer Types')
      - it('should parse int8')
      - it('should parse uint8')
      - it('should parse big-endian int16')
      - it('should parse little-endian int16')
      - ...
  - describe('Component Type Parsing')
    - describe('Quantity Binary')
      - it('should parse quantity value')
      - ...
    - describe('DataRecord Binary')
      - ...
    - describe('DataArray Binary')
      - it('should parse simple array')
      - it('should parse array with block separators')
      - it('should parse array of records')
      - ...
  - describe('Error Handling')
    - it('should error on insufficient bytes')
    - it('should handle corrupted data')
    - ...
```

#### 12. Test Depth Definition

**"Meaningful" SWE Common Test Characteristics:**

✅ **DO:**

- Parse complete fixture in all 3 encodings
- Validate byte-level correctness for binary encoding
- Test schema validation with mismatches
- Test nested structures (DataRecord in DataRecord, DataArray of DataRecords)
- Test all data type variations (float32, float64, int types)
- Test endianness explicitly (big and little)
- Test error conditions per encoding
- Use real spec examples or OpenSensorHub data

❌ **DON'T (Trivial):**

- Just check `result !== null`
- Skip binary encoding tests (most critical)
- Test only JSON (easiest, but not sufficient)
- Use overly simple hand-crafted fixtures when spec examples exist
- Skip schema validation
- Skip endianness testing
- Test only happy path without edge cases

#### 13. Fixture Requirements

```markdown
Fixture Directories:

- `fixtures/swe-common/json/` (~40 fixtures)
- `fixtures/swe-common/text/` (~40 fixtures)
- `fixtures/swe-common/binary/` (~40 fixtures, includes .bin files + hex dumps)
- `fixtures/swe-common/schemas/` (DataStream schemas for validation)

Binary Fixtures Should Include:

- Hex dump (.hex or .txt with hex representation)
- Binary file (.bin)
- Expected parsed result (.json for comparison)
- Encoding definition (BinaryEncoding structure)

Example Binary Fixture Set:

- quantity-float32-big-endian.bin + .hex + expected.json
- quantity-float32-little-endian.bin + .hex + expected.json
- dataarray-observations-10.bin + .hex + expected.json + schema.json
```

#### 14. Validation Against Upstream Patterns

Compare with Section 1-2 findings:

- How does EDR test SWE Common parsing?
- What encoding coverage do other implementations have?
- Is binary encoding tested upstream?
- What test depth do other implementations use?
- Are we aligned with upstream quality standards?

#### 15. Integration with Implementation Guide

Cross-validate with Implementation Guide SWE Common parser specification:

- ✅ Aligned: Test requirement matches Implementation Guide
- ⚠️ Gap: Test requirement not addressed in Implementation Guide
- ❌ Conflict: Test requirement conflicts with Implementation Guide

#### 16. Testing Estimates

```markdown
| Encoding          | Test Count | Lines per Test | Total Lines     | Time Estimate   |
| ----------------- | ---------- | -------------- | --------------- | --------------- |
| JSON              | 33         | 11-17          | 378-572         | 5-7 hours       |
| Text              | 34         | 11-15          | 370-507         | 5-7 hours       |
| Binary            | 61         | 14-21          | 865-1,284       | 12-18 hours     |
| Schema Validation | 8          | 12-15          | 96-120          | 2-3 hours       |
| **TOTAL**         | **136**    | **~13 avg**    | **1,709-2,483** | **24-35 hours** |
```

**Note:** Binary encoding is ~50% of total effort due to complexity.

#### 17. Testing Priorities

**CRITICAL (Must Have):**

- JSON encoding for all component types
- Binary encoding for primitive types (float, int)
- Binary DataArray parsing (observations)
- Schema validation for observations
- Endianness handling
- Error handling per encoding

**HIGH (Should Have):**

- Text encoding for all component types
- Binary encoding for complex types (DataRecord, DataChoice)
- All spec example coverage
- Nested structure parsing
- Real-world fixtures from OpenSensorHub

**MEDIUM (Nice to Have):**

- Advanced binary edge cases (NaN, Inf handling)
- Performance testing (large arrays)
- Matrix and DataStream components
- Quality information parsing

**LOW (Optional):**

- Time reference frame validation
- CRS validation for Vector
- Advanced DataChoice logic

#### 18. Risks and Edge Cases

```markdown
| Risk/Edge Case                             | Likelihood | Impact   | Mitigation                                                |
| ------------------------------------------ | ---------- | -------- | --------------------------------------------------------- |
| Binary encoding bugs cause data corruption | High       | CRITICAL | Extensive binary testing; byte-level validation           |
| Endianness detection wrong                 | Medium     | High     | Explicit endianness tests; encoding definition validation |
| IEEE 754 edge cases (NaN, Inf)             | Medium     | Medium   | Specific edge case tests; graceful handling               |
| Very large arrays cause memory issues      | Low        | Medium   | Test with realistic sizes; streaming if needed            |
| Schema validation too strict               | Medium     | Medium   | Follow spec strictly; configurable validation             |
| OpenSensorHub binary examples unavailable  | High       | Medium   | Generate binary fixtures from spec; hex dumps             |
```

### Success Criteria

✅ All 12+ component types have test requirements defined for all 3 encodings  
✅ Binary encoding byte formats documented in detail  
✅ Endianness testing strategy defined  
✅ IEEE 754 edge cases (NaN, Inf) addressed  
✅ Schema validation requirements complete  
✅ Nested structure testing strategy defined  
✅ Fixture inventory complete (120+ fixtures, including binary)  
✅ Test depth defined ("meaningful" criteria met)  
✅ Error handling requirements specified per encoding  
✅ Test organization and estimates documented  
✅ Validated against upstream patterns  
✅ Cross-validated with Implementation Guide

### Validation

- All component types from spec covered
- All 3 encodings thoroughly tested
- Binary encoding has majority of test effort (~50%)
- Test depth meets "meaningful" criteria from Section 6
- Fixture count sufficient for coverage (120+ fixtures)
- Test estimates realistic (1,700-2,500 lines)
- Schema validation comprehensive
- Error conditions comprehensive per encoding

---

## Cross-References

**Builds On:**

- Section 8: CSAPI Specification Test Requirements (SWE Common validation rules)
- Section 9: SensorML Testing Requirements (integration context)
- Section 6: "Meaningful vs Trivial" Definition (test depth guidance)
- Section 1-2: Upstream format parser test patterns
- **Format Requirements Analysis:** [docs/research/requirements/csapi-format-requirements.md](../../requirements/csapi-format-requirements.md)

**Critical For:**

- Section 9: SensorML Testing (characteristics/capabilities use SWE Common)
- Section 12: QueryBuilder Testing (observations endpoint requires SWE Common parsing)
- Section 14: Integration Test Workflows (observation workflow uses SWE Common)
- Section 15: Fixture Sourcing Strategy (SWE Common fixture inventory, especially binary)
- Section 36: Test Quality Checklist (SWE Common test validation criteria)

---

## Next Steps After Completion

1. Use test requirements to implement SWE Common parser tests (Phase 3, Task 16)
2. Generate or source binary fixtures (CRITICAL)
3. Design test file structure (3 files: JSON, Text, Binary)
4. Validate test coverage against specification requirements
5. Create binary fixture generation utilities

---

## Risks and Mitigation

**Risk:** Binary encoding complexity may lead to bugs and insufficient testing  
**Mitigation:** Prioritize binary tests; extensive byte-level validation; explicit endianness tests

**Risk:** Binary fixtures may be hard to source or generate  
**Mitigation:** Generate from spec examples; create hex dump utilities; use OpenSensorHub if available

**Risk:** Schema validation may be overly complex  
**Mitigation:** Start with simple validation; iterate based on real-world requirements

**Risk:** Test suite may be very large (2,000+ lines)  
**Mitigation:** Organize into multiple files; prioritize critical tests; use test generation for repetitive cases

---

## Research Status

- [x] Phase 1: SWE Common 3.0 Specification Deep Dive (60-90 min) ✅
- [x] Phase 2: JSON Schema Analysis (30-45 min) ✅
- [x] Phase 3: Binary Encoding Deep Dive (45-60 min) ✅
- [x] Phase 4: Example and Fixture Analysis (30-45 min) ✅
- [x] Phase 5: Test Strategy Design (30-45 min) ✅
- [x] Deliverable Complete and Reviewed ✅

**Total Estimated Time:** 3-4 hours  
**Actual Time:** ~4.5 hours (extensive binary encoding specifications)  
**Started:** February 5, 2026  
**Completed:** February 5, 2026

**Deliverable:** [10-swe-common-testing-requirements.md](../findings/10-swe-common-testing-requirements.md) (~2,200 lines)
