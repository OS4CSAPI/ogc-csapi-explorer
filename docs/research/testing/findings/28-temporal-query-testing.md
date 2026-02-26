# Section 28: Temporal Query Testing Strategy

> ⚠️ **REVIEW NOTICE — HIGH (H6): Identifies Client Utilities But Doesn't Test Them**
>
> **Phase 2E Review | Issues: H6, M6 | Anti-Patterns: AP1, AP4**
>
> This document is ~55% client-oriented. Section 7 defines 5 client utility functions (`parseInstant()`, `parseInterval()`, `parseDuration()`, `toUTC()`, `validateISO8601()`) that are genuinely useful testable client code. However, the test scenarios in Section 4 only test URL query parameter construction and `response.ok` assertions — no test exercises the temporal parsing/transformation functions.
>
> **What's usable:** ISO 8601 format analysis (Section 2), timezone handling (Section 3), client utility functions (Section 7), URL construction patterns (`response.requestUrl` assertions).
>
> **What must be rewritten:** The `expect(response.ok).toBe(true)` assertions throughout Section 4 are meaningless against mocked responses — they only confirm the mock returns `ok: true`. Tests should instead exercise: `parseInstant('2024-01-15T12:00:00+05:30')` → `Date(UTC 06:30)`, `parseInterval('2024-01-01/..')` → `{start, end: null}`, `toUTC(localDate)` → expected ISO string.
>
> See also: [Phase 2E Review Report](../review/phase-2e-advanced-scenarios-category.md)

**Research Plan:** [Research Plan 28: Temporal Query Testing Strategy](../research-plans/28-temporal-query-testing.md)

**Research Questions:** 6 core questions about testing all ISO 8601 interval formats, open-ended intervals (`../..`, `2024-01-01/..`, `../2024-12-31`), instant vs interval queries, temporal parameter combinations, temporal edge cases, and temporal validation errors

**Methodology:** 6-phase systematic analysis (Phase 1: Temporal Parameter Specification Analysis extracting 5 parameters (datetime, phenomenonTime, resultTime, executionTime, issueTime) → Phase 2: ISO 8601 Format Analysis documenting instants/intervals/durations → Phase 3: Upstream Temporal Testing Analysis of existing patterns → Phase 4: Test Scenario Design for all format variations → Phase 5: Fixture Design for query strings and responses → Phase 6: Synthesis into comprehensive temporal query testing strategy)

**Research Time:** ~180 minutes (3 hours) (February 6, 2026)

**Primary Source(s):**

- [Query Parameter Requirements](../../requirements/csapi-query-parameters.md) (temporal parameters)
- [ISO 8601 Specification](https://www.iso.org/iso-8601-date-and-time-format.html)
- [CSAPI Part 2 Specification](https://docs.ogc.org/is/23-002/23-002.html) (temporal queries)
- [OGC API - Common](https://docs.ogc.org/is/19-072/19-072.html) (temporal query patterns)

**Supporting Resources:**

- Section 8: [CSAPI Specification Test Requirements](08-csapi-specification-test-requirements.md) (temporal parameter definitions)
- Section 23: [Pagination Testing](23-pagination-testing.md) (temporal queries with pagination)
- Section 24: [Query Parameter Combination Testing](24-query-parameter-combination-testing.md) (parameter interactions)
- [RFC 3339](https://datatracker.ietf.org/doc/html/rfc3339) (ISO 8601 profile for internet timestamps)

**Document Purpose:** Defines comprehensive testing strategy for 5 CSAPI temporal parameters with ISO 8601 format variations (instants, intervals, durations, open-ended), timezone handling (UTC, offset, Z notation), temporal parameter combinations, edge cases (leap years, DST, leap seconds), and validation errors across observations and commands

---

## Executive Summary

This document defines comprehensive testing requirements for all CSAPI temporal query parameters, covering ISO 8601 format variations, timezone handling, open-ended intervals, temporal parameter combinations, and edge cases. Temporal queries are critical for observations and commands, enabling time-windowed data retrieval and real-time monitoring.

### Key Findings

**Temporal Parameters (5 total):**

- **datetime** - Generic temporal filter (OGC API - Common) for validTime property
- **phenomenonTime** - When observation was made (Part 2)
- **resultTime** - When observation result was produced (Part 2)
- **executionTime** - When command was/will be executed (Part 2)
- **issueTime** - When command was issued/submitted (Part 2)

**ISO 8601 Format Variants:**

- **Instants:** Date-only (`2024-01-15`), DateTime (`2024-01-15T12:00:00Z`), Timezone offset (`2024-01-15T12:00:00+05:00`), Fractional seconds (`2024-01-15T12:00:00.123Z`)
- **Intervals:** Closed (`2024-01-01/2024-12-31`), Open-start (`../2024-12-31`), Open-end (`2024-01-01/..`), Fully open (`../..`)
- **Durations:** ISO 8601 duration format (`P1Y`, `P1M`, `P1D`, `PT1H`, `PT30M`, etc.) - **NOT directly supported as query values** but may appear in interval representations

**Testing Priorities:**

- **CRITICAL:** Instant formats, closed intervals, open-ended intervals, timezone handling, validation errors
- **HIGH:** Date-only formats, fractional seconds, parameter combinations, pagination interactions
- **MEDIUM:** Edge cases (leap years, DST, midnight boundaries), special values (now, latest)
- **LOW:** Duration parsing (if supported), complex interval combinations

**Fixture Requirements:** ~55 fixtures

- Temporal query strings: ~25 fixtures (all ISO 8601 formats)
- Temporal response fixtures: ~15 fixtures
- Temporal error fixtures: ~10 fixtures
- Temporal edge case fixtures: ~5 fixtures

**Estimated Test Implementation:** 950-1,300 lines

- ISO 8601 instant tests: 200-250 lines (12 tests)
- ISO 8601 interval tests: 250-350 lines (15 tests)
- Open-ended interval tests: 150-200 lines (9 tests)
- Timezone handling tests: 150-200 lines (9 tests)
- Temporal parameter combination tests: 100-150 lines (6 tests)
- Temporal validation error tests: 100-150 lines (8 tests)

**Key Testing Challenges:**

1. **ISO 8601 format diversity** - Many valid representations (date-only, datetime, timezones, fractional seconds)
2. **Open-ended intervals** - Critical for "all data up to now" queries (`2024-01-01/..`)
3. **Timezone handling** - UTC, offset notation, Z notation, default behavior
4. **Temporal parameter semantics** - Each parameter has different meaning (phenomenonTime vs resultTime)
5. **Edge cases** - Leap years, DST transitions, midnight boundaries, antimeridian crossing

### Highest Rejection Risk

Temporal query testing is **HIGH RISK** because:

- **Format diversity** - Many valid ISO 8601 formats must be supported
- **Timezone complexity** - Global deployment requires correct timezone handling
- **Open-ended semantics** - `..` notation is critical for streaming and real-time scenarios
- **Parameter combinations** - Multiple temporal parameters can be combined (e.g., phenomenonTime + resultTime)
- **Edge cases** - Date/time edge cases are notoriously error-prone (leap years, DST, midnight)

**Mitigation:** Comprehensive test coverage with ~55 fixtures covering all ISO 8601 formats, timezone variations, open-ended intervals, and edge cases.

---

## 1. Temporal Parameter Inventory

### 1.1 Temporal Parameter Matrix

| Parameter          | Applies To                                        | Format                       | Special Values | Semantics                                                 | Priority     |
| ------------------ | ------------------------------------------------- | ---------------------------- | -------------- | --------------------------------------------------------- | ------------ |
| **datetime**       | Systems, Deployments, DataStreams, ControlStreams | ISO 8601 instant or interval | none           | Filters by validTime property (when description is valid) | **CRITICAL** |
| **phenomenonTime** | DataStreams, Observations                         | ISO 8601 instant or interval | none           | When observation was made (applies to FOI)                | **CRITICAL** |
| **resultTime**     | DataStreams, Observations                         | ISO 8601 instant or interval | `latest`       | When observation result was produced                      | **CRITICAL** |
| **executionTime**  | ControlStreams, Commands                          | ISO 8601 instant or interval | none           | When command was/will be executed                         | HIGH         |
| **issueTime**      | ControlStreams, Commands                          | ISO 8601 instant or interval | none           | When command was issued/submitted                         | MEDIUM       |

### 1.2 Resource-Temporal Parameter Mapping

| Resource Type      | Temporal Parameters Supported        | Primary Use Cases                                      |
| ------------------ | ------------------------------------ | ------------------------------------------------------ |
| **Systems**        | datetime                             | Filter by validTime (when system description is valid) |
| **Deployments**    | datetime                             | Filter by validTime (when deployment is active)        |
| **DataStreams**    | datetime, phenomenonTime, resultTime | Filter by validTime, observation times                 |
| **ControlStreams** | datetime, executionTime, issueTime   | Filter by validTime, command times                     |
| **Observations**   | phenomenonTime, resultTime           | Filter by observation times                            |
| **Commands**       | executionTime, issueTime             | Filter by command times                                |

### 1.3 Temporal Parameter Semantics

**datetime (OGC API - Common)**

- **Meaning:** Filters resources by validTime property (time period when resource description is valid)
- **Behavior:** Returns resources whose validTime property intersects the query value
- **Example:** `GET /systems?datetime=2024-01-15` returns systems valid on 2024-01-15

**phenomenonTime (CSAPI Part 2)**

- **Meaning:** When the observation was made (when the observed value applies to the feature of interest)
- **Behavior:** Returns observations/datastreams whose phenomenonTime intersects the query value
- **Example:** `GET /observations?phenomenonTime=2024-01-15T12:00:00Z` returns observations made at noon

**resultTime (CSAPI Part 2)**

- **Meaning:** When the observation result was produced (may differ from phenomenonTime due to processing delay)
- **Behavior:** Returns observations/datastreams whose resultTime intersects the query value
- **Special:** Supports `latest` special value to return most recent results
- **Example:** `GET /observations?resultTime=latest` returns observations with latest resultTime

**executionTime (CSAPI Part 2)**

- **Meaning:** When the command was or will be executed
- **Behavior:** Returns controlstreams/commands whose executionTime intersects the query value
- **Example:** `GET /commands?executionTime=2024-01-15T14:00:00Z/..` returns commands executed after 2pm

**issueTime (CSAPI Part 2)**

- **Meaning:** When the command was issued/submitted
- **Behavior:** Returns controlstreams/commands whose issueTime intersects the query value
- **Note:** issueTime ≤ executionTime (commands issued before or at execution)
- **Example:** `GET /commands?issueTime=2024-01-15T00:00:00Z/2024-01-15T23:59:59Z` returns commands issued on 2024-01-15

---

## 2. ISO 8601 Format Specifications

### 2.1 Instant Formats

| Format Type                          | Pattern                       | Example                       | Notes                                   | Test Priority |
| ------------------------------------ | ----------------------------- | ----------------------------- | --------------------------------------- | ------------- |
| **Date only**                        | `YYYY-MM-DD`                  | `2024-01-15`                  | Treated as start of day UTC (00:00:00Z) | **CRITICAL**  |
| **DateTime UTC**                     | `YYYY-MM-DDTHH:MM:SSZ`        | `2024-01-15T12:00:00Z`        | Z notation indicates UTC                | **CRITICAL**  |
| **DateTime with offset**             | `YYYY-MM-DDTHH:MM:SS±HH:MM`   | `2024-01-15T12:00:00+05:00`   | Timezone offset from UTC                | **CRITICAL**  |
| **DateTime with offset (short)**     | `YYYY-MM-DDTHH:MM:SS±HH`      | `2024-01-15T12:00:00+05`      | Short form offset                       | HIGH          |
| **Fractional seconds**               | `YYYY-MM-DDTHH:MM:SS.fffZ`    | `2024-01-15T12:00:00.123Z`    | Millisecond precision                   | HIGH          |
| **Fractional seconds (microsecond)** | `YYYY-MM-DDTHH:MM:SS.ffffffZ` | `2024-01-15T12:00:00.123456Z` | Microsecond precision                   | MEDIUM        |
| **Compact format (no separators)**   | `YYYYMMDDTHHMMSSZ`            | `20240115T120000Z`            | No dashes or colons                     | LOW           |

**Validation Rules:**

- MUST be valid ISO 8601 format
- Year: 0000-9999 (practical range: 1900-2100)
- Month: 01-12
- Day: 01-31 (respecting month/year)
- Hour: 00-23
- Minute: 00-59
- Second: 00-59 (60 for leap seconds - optional support)
- Timezone offset: -12:00 to +14:00

### 2.2 Interval Formats

| Format Type                    | Pattern            | Example                                     | Notes                          | Test Priority |
| ------------------------------ | ------------------ | ------------------------------------------- | ------------------------------ | ------------- |
| **Closed interval**            | `instant/instant`  | `2024-01-01/2024-12-31`                     | Both start and end specified   | **CRITICAL**  |
| **Closed interval (datetime)** | `instant/instant`  | `2024-01-01T00:00:00Z/2024-12-31T23:59:59Z` | Full datetime precision        | **CRITICAL**  |
| **Open start**                 | `../instant`       | `../2024-12-31`                             | No start (all data before end) | **CRITICAL**  |
| **Open end**                   | `instant/..`       | `2024-01-01/..`                             | No end (all data after start)  | **CRITICAL**  |
| **Fully open**                 | `../..`            | `../..`                                     | No bounds (all data)           | HIGH          |
| **Start + duration**           | `instant/duration` | `2024-01-01T00:00:00Z/P1M`                  | Start + ISO 8601 duration      | MEDIUM        |
| **Duration + end**             | `duration/instant` | `P1Y/2024-12-31T23:59:59Z`                  | ISO 8601 duration + end        | MEDIUM        |

**Validation Rules:**

- start MUST be before end (for closed intervals)
- Open-ended intervals MUST use `..` notation (double dot)
- Duration formats use ISO 8601 duration notation (P prefix)

### 2.3 Duration Formats (ISO 8601)

| Format                 | Example          | Meaning                                            | Support Level |
| ---------------------- | ---------------- | -------------------------------------------------- | ------------- |
| **Years**              | `P1Y`            | 1 year                                             | MEDIUM        |
| **Months**             | `P1M`            | 1 month                                            | MEDIUM        |
| **Weeks**              | `P1W`            | 1 week                                             | MEDIUM        |
| **Days**               | `P1D`            | 1 day                                              | MEDIUM        |
| **Hours**              | `PT1H`           | 1 hour (note: T prefix for time)                   | MEDIUM        |
| **Minutes**            | `PT30M`          | 30 minutes                                         | MEDIUM        |
| **Seconds**            | `PT45S`          | 45 seconds                                         | MEDIUM        |
| **Combined**           | `P1DT12H`        | 1 day 12 hours                                     | MEDIUM        |
| **Combined (complex)** | `P1Y2M3DT4H5M6S` | 1 year 2 months 3 days 4 hours 5 minutes 6 seconds | LOW           |

**Note:** Durations are used in interval formats (e.g., `2024-01-01/P1M`) but are **NOT supported as standalone query values** in CSAPI. They must be combined with an instant to form an interval.

### 2.4 Special Values

| Value      | Meaning            | Applies To                         | Notes                                       |
| ---------- | ------------------ | ---------------------------------- | ------------------------------------------- |
| **latest** | Most recent result | resultTime parameter only          | Returns observations with latest resultTime |
| **now**    | Current time       | None (CSAPI doesn't document this) | May be supported by implementations         |

**Important:** Unlike some OGC APIs, CSAPI Part 2 specification does NOT explicitly document `now` as a special value. Only `latest` is documented for `resultTime` parameter.

---

## 3. Timezone Handling

### 3.1 Timezone Format Variations

| Notation            | Format   | Example                     | Meaning                                 | Test Priority |
| ------------------- | -------- | --------------------------- | --------------------------------------- | ------------- |
| **Z notation**      | `Z`      | `2024-01-15T12:00:00Z`      | UTC time (Zulu time)                    | **CRITICAL**  |
| **UTC explicit**    | `+00:00` | `2024-01-15T12:00:00+00:00` | UTC time (explicit offset)              | HIGH          |
| **Positive offset** | `+HH:MM` | `2024-01-15T12:00:00+05:30` | 5 hours 30 minutes ahead of UTC (India) | **CRITICAL**  |
| **Negative offset** | `-HH:MM` | `2024-01-15T12:00:00-08:00` | 8 hours behind UTC (Pacific)            | **CRITICAL**  |
| **Short offset**    | `±HH`    | `2024-01-15T12:00:00+05`    | 5 hours offset (short form)             | MEDIUM        |
| **No timezone**     | none     | `2024-01-15T12:00:00`       | Assumed UTC per ISO 8601 default        | HIGH          |

**Timezone Offset Range:**

- Valid range: -12:00 to +14:00
- Most common: -12:00 to +12:00
- Edge cases: +12:45 (Chatham Islands), +13:00 (Tonga), +14:00 (Kiribati)

**Default Behavior:**

- ISO 8601 default: If no timezone specified, assume UTC
- CSAPI recommendation: Always specify timezone (Z or offset) for clarity

### 3.2 Timezone Conversion

**Server Behavior:**

- Server MUST accept all valid ISO 8601 timezone formats
- Server MAY convert to UTC internally
- Server SHOULD preserve client timezone in response (but not required)

**Client Behavior:**

- Client SHOULD always send timestamps in UTC (Z notation)
- Client MUST handle timezone offsets in server responses
- Client MAY convert to local timezone for display

**Example:**

```typescript
// Input (client local time: PST)
client.observations.list({
  phenomenonTime: new Date('2024-01-15T12:00:00-08:00'),
});

// Encoded as:
// ?phenomenonTime=2024-01-15T12:00:00-08:00
// or normalized to UTC: ?phenomenonTime=2024-01-15T20:00:00Z

// Server returns:
// Observations with phenomenonTime intersecting 2024-01-15T20:00:00Z UTC
```

---

## 4. Temporal Query Test Scenarios

### 4.1 Instant Format Tests (12 tests)

> ⚠️ **REVIEW NOTICE (M6): `expect(response.ok).toBe(true)` Meaningless Against Fixtures**
>
> Tests throughout Section 4 assert `expect(response.ok).toBe(true)` against mocked responses. This only confirms the mock returns `ok: true` — it tests nothing about the client. The `expect(response.requestUrl).toContain(...)` assertions in the same tests ARE client-oriented and should be retained. The table descriptions like "Returns resources on that date" describe server filtering behavior, not client behavior.
>
> **Retain:** `requestUrl` assertions that verify URL construction.
> **Remove:** `response.ok` assertions and server filtering descriptions.
> **Add:** Tests for Section 7 utility functions (`parseInstant`, `parseInterval`, `toUTC`).

**Priority:** **CRITICAL**

| Test ID       | Format                   | Example Query                          | Expected Behavior                                               | Lines |
| ------------- | ------------------------ | -------------------------------------- | --------------------------------------------------------------- | ----- |
| TEMP-INST-001 | Date only                | `datetime=2024-01-15`                  | Treated as 2024-01-15T00:00:00Z, returns resources on that date | 15    |
| TEMP-INST-002 | DateTime UTC (Z)         | `datetime=2024-01-15T12:00:00Z`        | Returns resources at exact instant                              | 15    |
| TEMP-INST-003 | DateTime UTC (explicit)  | `datetime=2024-01-15T12:00:00+00:00`   | Equivalent to Z notation                                        | 15    |
| TEMP-INST-004 | DateTime positive offset | `datetime=2024-01-15T12:00:00+05:30`   | Converts to UTC (06:30:00Z), returns resources                  | 15    |
| TEMP-INST-005 | DateTime negative offset | `datetime=2024-01-15T12:00:00-08:00`   | Converts to UTC (20:00:00Z), returns resources                  | 15    |
| TEMP-INST-006 | Fractional seconds (ms)  | `datetime=2024-01-15T12:00:00.123Z`    | Returns resources at instant with millisecond precision         | 15    |
| TEMP-INST-007 | Fractional seconds (μs)  | `datetime=2024-01-15T12:00:00.123456Z` | Returns resources at instant with microsecond precision         | 15    |
| TEMP-INST-008 | No timezone (assume UTC) | `datetime=2024-01-15T12:00:00`         | Assumed UTC per ISO 8601, returns resources at instant          | 15    |
| TEMP-INST-009 | Midnight (start of day)  | `datetime=2024-01-15T00:00:00Z`        | Returns resources at midnight                                   | 15    |
| TEMP-INST-010 | Midnight (end of day)    | `datetime=2024-01-15T23:59:59Z`        | Returns resources at end of day                                 | 15    |
| TEMP-INST-011 | Leap second              | `datetime=2024-06-30T23:59:60Z`        | Optional: May support leap seconds, or normalize to 23:59:59Z   | 15    |
| TEMP-INST-012 | Compact format           | `datetime=20240115T120000Z`            | Optional: May support no-separator format                       | 15    |

**Test Implementation (~180-240 lines, 12 tests):**

```typescript
describe('Temporal Instant Queries', () => {
  it('accepts date-only format (treated as start of day UTC)', async () => {
    const response = await client.systems.list({
      datetime: '2024-01-15',
    });

    expect(response.ok).toBe(true);
    // Verify request URL
    expect(response.requestUrl).toContain('datetime=2024-01-15');
    // Verify systems returned have validTime intersecting 2024-01-15
  });

  it('accepts datetime with Z notation (UTC)', async () => {
    const response = await client.systems.list({
      datetime: '2024-01-15T12:00:00Z',
    });

    expect(response.ok).toBe(true);
    expect(response.requestUrl).toContain('datetime=2024-01-15T12:00:00Z');
  });

  it('accepts datetime with positive timezone offset', async () => {
    const response = await client.systems.list({
      datetime: '2024-01-15T12:00:00+05:30',
    });

    expect(response.ok).toBe(true);
    // +05:30 = India Standard Time
    // 12:00:00+05:30 = 06:30:00Z
    expect(response.requestUrl).toContain(
      'datetime=2024-01-15T12:00:00%2B05:30'
    );
  });

  it('accepts datetime with negative timezone offset', async () => {
    const response = await client.systems.list({
      datetime: '2024-01-15T12:00:00-08:00',
    });

    expect(response.ok).toBe(true);
    // -08:00 = Pacific Standard Time
    // 12:00:00-08:00 = 20:00:00Z
    expect(response.requestUrl).toContain('datetime=2024-01-15T12:00:00-08:00');
  });

  it('accepts fractional seconds (milliseconds)', async () => {
    const response = await client.systems.list({
      datetime: '2024-01-15T12:00:00.123Z',
    });

    expect(response.ok).toBe(true);
    expect(response.requestUrl).toContain('datetime=2024-01-15T12:00:00.123Z');
  });

  it('accepts fractional seconds (microseconds)', async () => {
    const response = await client.systems.list({
      datetime: '2024-01-15T12:00:00.123456Z',
    });

    expect(response.ok).toBe(true);
    expect(response.requestUrl).toContain(
      'datetime=2024-01-15T12:00:00.123456Z'
    );
  });

  it('assumes UTC when timezone omitted', async () => {
    const response = await client.systems.list({
      datetime: '2024-01-15T12:00:00',
    });

    expect(response.ok).toBe(true);
    // Should be treated as 2024-01-15T12:00:00Z
    expect(response.requestUrl).toContain('datetime=2024-01-15T12:00:00');
  });

  // Similar tests for midnight boundaries, leap seconds (optional), compact format...
});
```

### 4.2 Interval Format Tests (15 tests)

**Priority:** **CRITICAL**

| Test ID       | Format                       | Example Query                                                  | Expected Behavior                                                                          | Lines |
| ------------- | ---------------------------- | -------------------------------------------------------------- | ------------------------------------------------------------------------------------------ | ----- |
| TEMP-INTV-001 | Closed interval (date)       | `datetime=2024-01-01/2024-12-31`                               | Returns resources with validTime intersecting [2024-01-01T00:00:00Z, 2024-12-31T00:00:00Z] | 15    |
| TEMP-INTV-002 | Closed interval (datetime)   | `datetime=2024-01-01T00:00:00Z/2024-12-31T23:59:59Z`           | Returns resources within full year 2024                                                    | 15    |
| TEMP-INTV-003 | Same start and end (instant) | `datetime=2024-01-15/2024-01-15`                               | Equivalent to instant query at 2024-01-15T00:00:00Z                                        | 15    |
| TEMP-INTV-004 | Single day interval          | `datetime=2024-01-15T00:00:00Z/2024-01-15T23:59:59Z`           | Returns resources within single day                                                        | 15    |
| TEMP-INTV-005 | Month interval               | `datetime=2024-01-01/2024-01-31`                               | Returns resources in January 2024                                                          | 15    |
| TEMP-INTV-006 | Year interval                | `datetime=2024-01-01/2024-12-31`                               | Returns resources in year 2024                                                             | 15    |
| TEMP-INTV-007 | Multi-year interval          | `datetime=2020-01-01/2024-12-31`                               | Returns resources in 5-year span                                                           | 15    |
| TEMP-INTV-008 | Hour interval                | `datetime=2024-01-15T12:00:00Z/2024-01-15T13:00:00Z`           | Returns resources within 1-hour window                                                     | 15    |
| TEMP-INTV-009 | Minute interval              | `datetime=2024-01-15T12:00:00Z/2024-01-15T12:01:00Z`           | Returns resources within 1-minute window                                                   | 15    |
| TEMP-INTV-010 | Second interval              | `datetime=2024-01-15T12:00:00Z/2024-01-15T12:00:01Z`           | Returns resources within 1-second window                                                   | 15    |
| TEMP-INTV-011 | Cross-timezone interval      | `datetime=2024-01-15T12:00:00+05:00/2024-01-16T12:00:00-08:00` | Handles timezone conversions correctly                                                     | 20    |
| TEMP-INTV-012 | Midnight-spanning interval   | `datetime=2024-01-15T23:00:00Z/2024-01-16T01:00:00Z`           | Crosses midnight boundary                                                                  | 15    |
| TEMP-INTV-013 | Month-boundary interval      | `datetime=2024-01-31T20:00:00Z/2024-02-01T04:00:00Z`           | Crosses month boundary                                                                     | 15    |
| TEMP-INTV-014 | Year-boundary interval       | `datetime=2024-12-31T20:00:00Z/2025-01-01T04:00:00Z`           | Crosses year boundary                                                                      | 15    |
| TEMP-INTV-015 | Fractional seconds interval  | `datetime=2024-01-15T12:00:00.000Z/2024-01-15T12:00:00.999Z`   | Sub-second interval                                                                        | 15    |

**Test Implementation (~225-300 lines, 15 tests):**

```typescript
describe('Temporal Interval Queries', () => {
  it('accepts closed interval (date-only)', async () => {
    const response = await client.systems.list({
      datetime: '2024-01-01/2024-12-31',
    });

    expect(response.ok).toBe(true);
    expect(response.requestUrl).toContain('datetime=2024-01-01%2F2024-12-31');
    // Verify systems with validTime intersecting [2024-01-01, 2024-12-31]
  });

  it('accepts closed interval (full datetime)', async () => {
    const response = await client.systems.list({
      datetime: '2024-01-01T00:00:00Z/2024-12-31T23:59:59Z',
    });

    expect(response.ok).toBe(true);
    expect(response.requestUrl).toContain(
      'datetime=2024-01-01T00:00:00Z%2F2024-12-31T23:59:59Z'
    );
  });

  it('treats same start and end as instant', async () => {
    const response = await client.systems.list({
      datetime: '2024-01-15/2024-01-15',
    });

    expect(response.ok).toBe(true);
    // Equivalent to instant at 2024-01-15T00:00:00Z
  });

  it('accepts single-day interval', async () => {
    const response = await client.systems.list({
      datetime: '2024-01-15T00:00:00Z/2024-01-15T23:59:59Z',
    });

    expect(response.ok).toBe(true);
    // Returns systems active at any point during 2024-01-15
  });

  it('accepts cross-timezone interval (converts to UTC)', async () => {
    const response = await client.systems.list({
      datetime: '2024-01-15T12:00:00+05:00/2024-01-16T12:00:00-08:00',
    });

    expect(response.ok).toBe(true);
    // Start: 12:00:00+05:00 = 07:00:00Z
    // End: 12:00:00-08:00 = 20:00:00Z (next day)
    // Interval spans ~37 hours
  });

  it('handles midnight-spanning interval', async () => {
    const response = await client.systems.list({
      datetime: '2024-01-15T23:00:00Z/2024-01-16T01:00:00Z',
    });

    expect(response.ok).toBe(true);
    // Crosses midnight 2024-01-15/2024-01-16
  });

  it('handles month-boundary interval', async () => {
    const response = await client.systems.list({
      datetime: '2024-01-31T20:00:00Z/2024-02-01T04:00:00Z',
    });

    expect(response.ok).toBe(true);
    // Crosses January/February boundary
  });

  it('handles year-boundary interval', async () => {
    const response = await client.systems.list({
      datetime: '2024-12-31T20:00:00Z/2025-01-01T04:00:00Z',
    });

    expect(response.ok).toBe(true);
    // Crosses 2024/2025 year boundary
  });

  // Similar tests for hour/minute/second intervals, fractional seconds...
});
```

### 4.3 Open-Ended Interval Tests (9 tests)

**Priority:** **CRITICAL**

| Test ID       | Format                   | Example Query                            | Expected Behavior                                   | Lines |
| ------------- | ------------------------ | ---------------------------------------- | --------------------------------------------------- | ----- |
| TEMP-OPEN-001 | Open start (date)        | `datetime=../2024-12-31`                 | Returns all resources before 2024-12-31T00:00:00Z   | 15    |
| TEMP-OPEN-002 | Open start (datetime)    | `datetime=../2024-12-31T23:59:59Z`       | Returns all resources before end of 2024            | 15    |
| TEMP-OPEN-003 | Open end (date)          | `datetime=2024-01-01/..`                 | Returns all resources after 2024-01-01T00:00:00Z    | 15    |
| TEMP-OPEN-004 | Open end (datetime)      | `datetime=2024-01-01T00:00:00Z/..`       | Returns all resources after start of 2024           | 15    |
| TEMP-OPEN-005 | Fully open               | `datetime=../..`                         | Returns all resources (no temporal filter)          | 15    |
| TEMP-OPEN-006 | Open end (recent)        | `phenomenonTime=2024-01-15T12:00:00Z/..` | Returns observations after noon on 2024-01-15       | 15    |
| TEMP-OPEN-007 | Open start (historical)  | `phenomenonTime=../2024-01-01T00:00:00Z` | Returns observations before 2024                    | 15    |
| TEMP-OPEN-008 | Open end with timezone   | `datetime=2024-01-15T12:00:00+05:00/..`  | Converts timezone, returns resources after instant  | 20    |
| TEMP-OPEN-009 | Open start with timezone | `datetime=../2024-12-31T23:59:59-08:00`  | Converts timezone, returns resources before instant | 20    |

**Test Implementation (~135-180 lines, 9 tests):**

```typescript
describe('Open-Ended Interval Queries', () => {
  it('accepts open start interval (date-only)', async () => {
    const response = await client.systems.list({
      datetime: '../2024-12-31',
    });

    expect(response.ok).toBe(true);
    expect(response.requestUrl).toContain('datetime=..%2F2024-12-31');
    // Returns all systems valid before 2024-12-31
  });

  it('accepts open start interval (full datetime)', async () => {
    const response = await client.systems.list({
      datetime: '../2024-12-31T23:59:59Z',
    });

    expect(response.ok).toBe(true);
    expect(response.requestUrl).toContain('datetime=..%2F2024-12-31T23:59:59Z');
  });

  it('accepts open end interval (date-only)', async () => {
    const response = await client.systems.list({
      datetime: '2024-01-01/..',
    });

    expect(response.ok).toBe(true);
    expect(response.requestUrl).toContain('datetime=2024-01-01%2F..');
    // Returns all systems valid after 2024-01-01
  });

  it('accepts open end interval (full datetime)', async () => {
    const response = await client.systems.list({
      datetime: '2024-01-01T00:00:00Z/..',
    });

    expect(response.ok).toBe(true);
    expect(response.requestUrl).toContain('datetime=2024-01-01T00:00:00Z%2F..');
  });

  it('accepts fully open interval (no temporal filter)', async () => {
    const response = await client.systems.list({
      datetime: '../..',
    });

    expect(response.ok).toBe(true);
    expect(response.requestUrl).toContain('datetime=..%2F..');
    // Returns all systems regardless of validTime
  });

  it('accepts open end for real-time streaming scenario', async () => {
    const response = await client.observations.list({
      phenomenonTime: '2024-01-15T12:00:00Z/..',
    });

    expect(response.ok).toBe(true);
    // Critical for "all observations after time X" streaming queries
  });

  it('handles open end with timezone conversion', async () => {
    const response = await client.systems.list({
      datetime: '2024-01-15T12:00:00+05:00/..',
    });

    expect(response.ok).toBe(true);
    // 12:00:00+05:00 = 07:00:00Z
    // Returns all systems after 07:00:00Z
  });

  // Similar tests for open start with timezone, historical queries...
});
```

### 4.4 Timezone Handling Tests (9 tests)

**Priority:** **CRITICAL**

| Test ID     | Scenario                     | Example Query                                                  | Expected Behavior                               | Lines |
| ----------- | ---------------------------- | -------------------------------------------------------------- | ----------------------------------------------- | ----- |
| TEMP-TZ-001 | Z notation (UTC)             | `datetime=2024-01-15T12:00:00Z`                                | Parsed as UTC                                   | 15    |
| TEMP-TZ-002 | Explicit UTC offset          | `datetime=2024-01-15T12:00:00+00:00`                           | Equivalent to Z notation                        | 15    |
| TEMP-TZ-003 | Positive offset (India)      | `datetime=2024-01-15T12:00:00+05:30`                           | Converts to 06:30:00Z                           | 15    |
| TEMP-TZ-004 | Negative offset (Pacific)    | `datetime=2024-01-15T12:00:00-08:00`                           | Converts to 20:00:00Z                           | 15    |
| TEMP-TZ-005 | Edge offset (Kiribati)       | `datetime=2024-01-15T12:00:00+14:00`                           | Converts to 2024-01-14T22:00:00Z (previous day) | 20    |
| TEMP-TZ-006 | Edge offset (Baker Island)   | `datetime=2024-01-15T12:00:00-12:00`                           | Converts to 2024-01-16T00:00:00Z (next day)     | 20    |
| TEMP-TZ-007 | Interval different timezones | `datetime=2024-01-15T12:00:00+05:00/2024-01-16T12:00:00-08:00` | Both convert to UTC correctly                   | 20    |
| TEMP-TZ-008 | No timezone (assume UTC)     | `datetime=2024-01-15T12:00:00`                                 | Treated as 12:00:00Z per ISO 8601               | 15    |
| TEMP-TZ-009 | Short offset notation        | `datetime=2024-01-15T12:00:00+05`                              | Equivalent to +05:00                            | 15    |

**Test Implementation (~135-180 lines, 9 tests):**

```typescript
describe('Timezone Handling', () => {
  it('parses Z notation as UTC', async () => {
    const response = await client.systems.list({
      datetime: '2024-01-15T12:00:00Z',
    });

    expect(response.ok).toBe(true);
    expect(response.requestUrl).toContain('datetime=2024-01-15T12:00:00Z');
  });

  it('treats explicit +00:00 as equivalent to Z', async () => {
    const response = await client.systems.list({
      datetime: '2024-01-15T12:00:00+00:00',
    });

    expect(response.ok).toBe(true);
    // Should be equivalent to Z notation
  });

  it('converts positive timezone offset to UTC', async () => {
    const response = await client.systems.list({
      datetime: '2024-01-15T12:00:00+05:30',
    });

    expect(response.ok).toBe(true);
    // +05:30 (India Standard Time)
    // 12:00:00+05:30 = 06:30:00Z
    expect(response.requestUrl).toContain(
      'datetime=2024-01-15T12:00:00%2B05:30'
    );
  });

  it('converts negative timezone offset to UTC', async () => {
    const response = await client.systems.list({
      datetime: '2024-01-15T12:00:00-08:00',
    });

    expect(response.ok).toBe(true);
    // -08:00 (Pacific Standard Time)
    // 12:00:00-08:00 = 20:00:00Z
    expect(response.requestUrl).toContain('datetime=2024-01-15T12:00:00-08:00');
  });

  it('handles extreme positive offset (+14:00 Kiribati)', async () => {
    const response = await client.systems.list({
      datetime: '2024-01-15T12:00:00+14:00',
    });

    expect(response.ok).toBe(true);
    // 12:00:00+14:00 = 2024-01-14T22:00:00Z (previous day!)
  });

  it('handles extreme negative offset (-12:00 Baker Island)', async () => {
    const response = await client.systems.list({
      datetime: '2024-01-15T12:00:00-12:00',
    });

    expect(response.ok).toBe(true);
    // 12:00:00-12:00 = 2024-01-16T00:00:00Z (next day!)
  });

  it('handles interval with different timezones', async () => {
    const response = await client.systems.list({
      datetime: '2024-01-15T12:00:00+05:00/2024-01-16T12:00:00-08:00',
    });

    expect(response.ok).toBe(true);
    // Start: 12:00:00+05:00 = 07:00:00Z
    // End: 12:00:00-08:00 = 20:00:00Z (next day)
    // Interval: 2024-01-15T07:00:00Z / 2024-01-16T20:00:00Z
  });

  it('assumes UTC when timezone omitted', async () => {
    const response = await client.systems.list({
      datetime: '2024-01-15T12:00:00',
    });

    expect(response.ok).toBe(true);
    // ISO 8601 default: treat as UTC
  });

  it('accepts short offset notation (+05 instead of +05:00)', async () => {
    const response = await client.systems.list({
      datetime: '2024-01-15T12:00:00+05',
    });

    expect(response.ok).toBe(true);
    // +05 is shorthand for +05:00
  });
});
```

### 4.5 Temporal Parameter Combination Tests (6 tests)

**Priority:** HIGH

| Test ID       | Combination                    | Example Query                                                   | Expected Behavior                                                     | Lines |
| ------------- | ------------------------------ | --------------------------------------------------------------- | --------------------------------------------------------------------- | ----- |
| TEMP-COMB-001 | phenomenonTime + resultTime    | `phenomenonTime=2024-01-15&resultTime=latest`                   | Filters by both parameters (AND logic)                                | 20    |
| TEMP-COMB-002 | datetime + phenomenonTime      | `datetime=2024-01-01/..&phenomenonTime=2024-01-15`              | Both applied (datetime on DataStream, phenomenonTime on observations) | 20    |
| TEMP-COMB-003 | executionTime + issueTime      | `executionTime=2024-01-15/..&issueTime=2024-01-14T00:00:00Z/..` | Both applied (issued before execution)                                | 20    |
| TEMP-COMB-004 | Temporal + spatial (bbox)      | `datetime=2024-01-15&bbox=-180,-90,180,90`                      | Both spatial and temporal filters applied                             | 15    |
| TEMP-COMB-005 | Temporal + pagination          | `phenomenonTime=2024-01-01/..&limit=100&offset=200`             | Temporal filter with pagination                                       | 15    |
| TEMP-COMB-006 | Multiple temporal (DataStream) | `datetime=2024-01-01/..&phenomenonTime=2024-01-15/..`           | Both applied to DataStream properties                                 | 20    |

**Test Implementation (~90-120 lines, 6 tests):**

```typescript
describe('Temporal Parameter Combinations', () => {
  it('combines phenomenonTime and resultTime filters', async () => {
    const response = await client.observations.list({
      phenomenonTime: '2024-01-15',
      resultTime: 'latest',
    });

    expect(response.ok).toBe(true);
    expect(response.requestUrl).toContain('phenomenonTime=2024-01-15');
    expect(response.requestUrl).toContain('resultTime=latest');
    // Returns observations made on 2024-01-15 with latest resultTime
  });

  it('combines datetime and phenomenonTime (different properties)', async () => {
    const response = await client.datastreams.list({
      datetime: '2024-01-01/..',
      phenomenonTime: '2024-01-15',
    });

    expect(response.ok).toBe(true);
    // datetime filters by validTime property
    // phenomenonTime filters by phenomenonTime property
    // Both applied (AND logic)
  });

  it('combines executionTime and issueTime', async () => {
    const response = await client.controlstreams.list({
      executionTime: '2024-01-15/..',
      issueTime: '2024-01-14T00:00:00Z/..',
    });

    expect(response.ok).toBe(true);
    // Commands executed on/after 2024-01-15
    // AND issued on/after 2024-01-14
  });

  it('combines temporal and spatial filters', async () => {
    const response = await client.systems.list({
      datetime: '2024-01-15',
      bbox: { minLon: -180, minLat: -90, maxLon: 180, maxLat: 90 },
    });

    expect(response.ok).toBe(true);
    // Returns systems valid on 2024-01-15 within bbox
  });

  it('combines temporal filter with pagination', async () => {
    const response = await client.observations.list({
      phenomenonTime: '2024-01-01/..',
      limit: 100,
      offset: 200,
    });

    expect(response.ok).toBe(true);
    // Returns observations after 2024-01-01, page 3 (offset 200, limit 100)
  });

  it('combines multiple temporal parameters on DataStream', async () => {
    const response = await client.datastreams.list({
      datetime: '2024-01-01/..',
      phenomenonTime: '2024-01-15/..',
    });

    expect(response.ok).toBe(true);
    // DataStream validTime after 2024-01-01
    // AND phenomenonTime after 2024-01-15
  });
});
```

### 4.6 Temporal Validation Error Tests (8 tests)

**Priority:** **CRITICAL**

| Test ID      | Error Type                    | Example Query                        | Expected Error                              | Lines |
| ------------ | ----------------------------- | ------------------------------------ | ------------------------------------------- | ----- |
| TEMP-ERR-001 | Invalid ISO 8601 format       | `datetime=2024-13-01`                | 400 Bad Request (invalid month)             | 15    |
| TEMP-ERR-002 | Invalid date (Feb 30)         | `datetime=2024-02-30`                | 400 Bad Request (day doesn't exist)         | 15    |
| TEMP-ERR-003 | Invalid time (hour > 23)      | `datetime=2024-01-15T25:00:00Z`      | 400 Bad Request (invalid hour)              | 15    |
| TEMP-ERR-004 | Start after end               | `datetime=2024-12-31/2024-01-01`     | 400 Bad Request (start must be before end)  | 15    |
| TEMP-ERR-005 | Invalid timezone offset       | `datetime=2024-01-15T12:00:00+15:00` | 400 Bad Request (offset > +14:00)           | 15    |
| TEMP-ERR-006 | Malformed interval (single /) | `datetime=2024-01-15/`               | 400 Bad Request (missing end)               | 15    |
| TEMP-ERR-007 | Invalid duration format       | `datetime=2024-01-01/1M`             | 400 Bad Request (duration missing P prefix) | 15    |
| TEMP-ERR-008 | Empty datetime value          | `datetime=`                          | 400 Bad Request (value required)            | 15    |

**Test Implementation (~90-120 lines, 8 tests):**

```typescript
describe('Temporal Validation Errors', () => {
  it('rejects invalid month (13)', async () => {
    await expect(
      client.systems.list({ datetime: '2024-13-01' })
    ).rejects.toThrow(/400.*invalid.*month/i);
  });

  it('rejects invalid date (Feb 30)', async () => {
    await expect(
      client.systems.list({ datetime: '2024-02-30' })
    ).rejects.toThrow(/400.*invalid.*date/i);
  });

  it('rejects invalid hour (25)', async () => {
    await expect(
      client.systems.list({ datetime: '2024-01-15T25:00:00Z' })
    ).rejects.toThrow(/400.*invalid.*hour/i);
  });

  it('rejects interval with start after end', async () => {
    await expect(
      client.systems.list({ datetime: '2024-12-31/2024-01-01' })
    ).rejects.toThrow(/400.*start.*before.*end/i);
  });

  it('rejects invalid timezone offset (+15:00)', async () => {
    await expect(
      client.systems.list({ datetime: '2024-01-15T12:00:00+15:00' })
    ).rejects.toThrow(/400.*invalid.*timezone.*offset/i);
  });

  it('rejects malformed interval (missing end)', async () => {
    await expect(
      client.systems.list({ datetime: '2024-01-15/' })
    ).rejects.toThrow(/400.*invalid.*interval/i);
  });

  it('rejects invalid duration format (missing P prefix)', async () => {
    await expect(
      client.systems.list({ datetime: '2024-01-01/1M' })
    ).rejects.toThrow(/400.*invalid.*duration/i);
  });

  it('rejects empty datetime value', async () => {
    await expect(client.systems.list({ datetime: '' })).rejects.toThrow(
      /400.*required/i
    );
  });
});
```

### 4.7 Temporal Edge Cases (8 tests)

**Priority:** MEDIUM

| Test ID       | Edge Case                         | Example Query                                                      | Expected Behavior                                           | Lines |
| ------------- | --------------------------------- | ------------------------------------------------------------------ | ----------------------------------------------------------- | ----- |
| TEMP-EDGE-001 | Leap year (Feb 29)                | `datetime=2024-02-29`                                              | Valid (2024 is leap year)                                   | 15    |
| TEMP-EDGE-002 | Non-leap year (Feb 29)            | `datetime=2023-02-29`                                              | 400 Bad Request (2023 not leap year)                        | 15    |
| TEMP-EDGE-003 | DST transition (spring forward)   | `datetime=2024-03-10T02:30:00-08:00`                               | Handles missing hour (2:00-3:00am doesn't exist in Pacific) | 20    |
| TEMP-EDGE-004 | DST transition (fall back)        | `datetime=2024-11-03T01:30:00-07:00`                               | Handles ambiguous hour (1:00-2:00am occurs twice)           | 20    |
| TEMP-EDGE-005 | Midnight (24:00:00 vs 00:00:00)   | `datetime=2024-01-15T24:00:00Z`                                    | Optional: May normalize to 2024-01-16T00:00:00Z             | 15    |
| TEMP-EDGE-006 | Antimeridian crossing (date line) | `datetime=2024-01-15T23:00:00-12:00/2024-01-16T01:00:00+14:00`     | Handles +/-12:00 timezone crossing date line                | 20    |
| TEMP-EDGE-007 | Century boundary (Y2K)            | `datetime=1999-12-31T23:59:59Z/2000-01-01T00:00:01Z`               | Crosses millennium boundary                                 | 15    |
| TEMP-EDGE-008 | Microsecond precision             | `datetime=2024-01-15T12:00:00.000001Z/2024-01-15T12:00:00.999999Z` | Handles microsecond-level precision                         | 15    |

**Test Implementation (~120-160 lines, 8 tests):**

```typescript
describe('Temporal Edge Cases', () => {
  it('accepts leap year date (Feb 29, 2024)', async () => {
    const response = await client.systems.list({
      datetime: '2024-02-29',
    });

    expect(response.ok).toBe(true);
    // 2024 is a leap year, Feb 29 is valid
  });

  it('rejects non-leap year date (Feb 29, 2023)', async () => {
    await expect(
      client.systems.list({ datetime: '2023-02-29' })
    ).rejects.toThrow(/400.*invalid.*date/i);
    // 2023 is not a leap year
  });

  it('handles DST transition (spring forward)', async () => {
    const response = await client.systems.list({
      datetime: '2024-03-10T02:30:00-08:00',
    });

    // 2:00-3:00am doesn't exist in Pacific time (spring forward)
    // Server may:
    // 1. Convert to UTC correctly (02:30-08:00 = 10:30Z)
    // 2. Reject as invalid (hour doesn't exist in that timezone)
    // Implementation-dependent behavior
  });

  it('handles DST transition (fall back)', async () => {
    const response = await client.systems.list({
      datetime: '2024-11-03T01:30:00-07:00',
    });

    // 1:00-2:00am occurs TWICE (fall back)
    // -07:00 indicates "second occurrence" (after falling back)
    // Server should handle ambiguity correctly
  });

  it('handles midnight as 24:00:00 (optional support)', async () => {
    const response = await client.systems.list({
      datetime: '2024-01-15T24:00:00Z',
    });

    // ISO 8601 allows 24:00:00 as end of day
    // Should normalize to 2024-01-16T00:00:00Z
    expect(response.ok).toBe(true);
  });

  it('handles antimeridian crossing (date line)', async () => {
    const response = await client.systems.list({
      datetime: '2024-01-15T23:00:00-12:00/2024-01-16T01:00:00+14:00',
    });

    // -12:00 and +14:00 are on opposite sides of date line
    // Start: 23:00-12:00 = 2024-01-16T11:00:00Z
    // End: 01:00+14:00 = 2024-01-15T11:00:00Z
    // Crosses date line, may require special handling
  });

  it('handles century boundary (Y2K)', async () => {
    const response = await client.systems.list({
      datetime: '1999-12-31T23:59:59Z/2000-01-01T00:00:01Z',
    });

    expect(response.ok).toBe(true);
    // Crosses millennium boundary (1999->2000)
  });

  it('handles microsecond precision', async () => {
    const response = await client.systems.list({
      datetime: '2024-01-15T12:00:00.000001Z/2024-01-15T12:00:00.999999Z',
    });

    expect(response.ok).toBe(true);
    // Sub-millisecond precision
  });
});
```

### 4.8 Special Value Tests (2 tests)

**Priority:** MEDIUM

| Test ID       | Special Value            | Example Query           | Expected Behavior                                | Lines |
| ------------- | ------------------------ | ----------------------- | ------------------------------------------------ | ----- |
| TEMP-SPEC-001 | latest (resultTime)      | `resultTime=latest`     | Returns observations with most recent resultTime | 15    |
| TEMP-SPEC-002 | latest (invalid context) | `phenomenonTime=latest` | 400 Bad Request (latest only for resultTime)     | 15    |

**Test Implementation (~30 lines, 2 tests):**

```typescript
describe('Special Temporal Values', () => {
  it('accepts "latest" for resultTime parameter', async () => {
    const response = await client.observations.list({
      resultTime: 'latest',
    });

    expect(response.ok).toBe(true);
    expect(response.requestUrl).toContain('resultTime=latest');
    // Returns observations with most recent resultTime
  });

  it('rejects "latest" for phenomenonTime parameter', async () => {
    await expect(
      client.observations.list({ phenomenonTime: 'latest' })
    ).rejects.toThrow(/400.*latest.*not.*supported.*phenomenonTime/i);
    // "latest" is only valid for resultTime
  });
});
```

### 4.9 Temporal with Pagination Tests (3 tests)

**Priority:** HIGH

| Test ID      | Scenario                    | Example Query                                       | Expected Behavior                                                | Lines |
| ------------ | --------------------------- | --------------------------------------------------- | ---------------------------------------------------------------- | ----- |
| TEMP-PAG-001 | Temporal + limit            | `phenomenonTime=2024-01-01/..&limit=100`            | Returns first 100 observations after 2024-01-01                  | 15    |
| TEMP-PAG-002 | Temporal + offset           | `phenomenonTime=2024-01-01/..&limit=100&offset=200` | Returns observations 201-300 after 2024-01-01                    | 15    |
| TEMP-PAG-003 | Temporal + pagination links | `phenomenonTime=2024-01-01/..&limit=100`            | Response includes next/prev links with temporal filter preserved | 20    |

**Test Implementation (~45-60 lines, 3 tests):**

```typescript
describe('Temporal with Pagination', () => {
  it('combines temporal filter with limit', async () => {
    const response = await client.observations.list({
      phenomenonTime: '2024-01-01/..',
      limit: 100,
    });

    expect(response.ok).toBe(true);
    expect(response.features.length).toBeLessThanOrEqual(100);
    // First 100 observations after 2024-01-01
  });

  it('combines temporal filter with offset and limit', async () => {
    const response = await client.observations.list({
      phenomenonTime: '2024-01-01/..',
      limit: 100,
      offset: 200,
    });

    expect(response.ok).toBe(true);
    expect(response.requestUrl).toContain('phenomenonTime=2024-01-01%2F..');
    expect(response.requestUrl).toContain('limit=100');
    expect(response.requestUrl).toContain('offset=200');
    // Observations 201-300 after 2024-01-01
  });

  it('preserves temporal filter in pagination links', async () => {
    const response = await client.observations.list({
      phenomenonTime: '2024-01-01/..',
      limit: 100,
    });

    expect(response.ok).toBe(true);
    // Check next link preserves phenomenonTime filter
    if (response.links) {
      const nextLink = response.links.find((l) => l.rel === 'next');
      if (nextLink) {
        expect(nextLink.href).toContain('phenomenonTime=2024-01-01');
      }
    }
  });
});
```

### 4.10 Test Scenario Summary

**Total Tests:** 72 tests  
**Total Lines:** 950-1,300 lines

| Test Category           | Test Count | Lines   | Priority     |
| ----------------------- | ---------- | ------- | ------------ |
| Instant Formats         | 12         | 180-240 | **CRITICAL** |
| Interval Formats        | 15         | 225-300 | **CRITICAL** |
| Open-Ended Intervals    | 9          | 135-180 | **CRITICAL** |
| Timezone Handling       | 9          | 135-180 | **CRITICAL** |
| Parameter Combinations  | 6          | 90-120  | HIGH         |
| Validation Errors       | 8          | 90-120  | **CRITICAL** |
| Edge Cases              | 8          | 120-160 | MEDIUM       |
| Special Values          | 2          | 30      | MEDIUM       |
| Pagination Interactions | 3          | 45-60   | HIGH         |

---

## 5. Fixture Requirements

### 5.1 Temporal Query String Fixtures (25 fixtures)

| Fixture ID                   | Format Type                | Example                                               | Notes                 |
| ---------------------------- | -------------------------- | ----------------------------------------------------- | --------------------- |
| **Instant Formats (8)**      |
| TEMP-QS-001                  | Date only                  | `2024-01-15`                                          | Start of day UTC      |
| TEMP-QS-002                  | DateTime UTC (Z)           | `2024-01-15T12:00:00Z`                                | Z notation            |
| TEMP-QS-003                  | DateTime UTC (explicit)    | `2024-01-15T12:00:00+00:00`                           | Explicit offset       |
| TEMP-QS-004                  | DateTime positive offset   | `2024-01-15T12:00:00+05:30`                           | India Standard Time   |
| TEMP-QS-005                  | DateTime negative offset   | `2024-01-15T12:00:00-08:00`                           | Pacific Standard Time |
| TEMP-QS-006                  | Fractional seconds (ms)    | `2024-01-15T12:00:00.123Z`                            | Millisecond precision |
| TEMP-QS-007                  | Fractional seconds (μs)    | `2024-01-15T12:00:00.123456Z`                         | Microsecond precision |
| TEMP-QS-008                  | No timezone                | `2024-01-15T12:00:00`                                 | Assume UTC            |
| **Interval Formats (7)**     |
| TEMP-QS-009                  | Closed interval (date)     | `2024-01-01/2024-12-31`                               | Year 2024             |
| TEMP-QS-010                  | Closed interval (datetime) | `2024-01-01T00:00:00Z/2024-12-31T23:59:59Z`           | Full precision        |
| TEMP-QS-011                  | Single day                 | `2024-01-15T00:00:00Z/2024-01-15T23:59:59Z`           | 24-hour period        |
| TEMP-QS-012                  | Hour interval              | `2024-01-15T12:00:00Z/2024-01-15T13:00:00Z`           | 1-hour window         |
| TEMP-QS-013                  | Minute interval            | `2024-01-15T12:00:00Z/2024-01-15T12:01:00Z`           | 1-minute window       |
| TEMP-QS-014                  | Cross-timezone             | `2024-01-15T12:00:00+05:00/2024-01-16T12:00:00-08:00` | Different zones       |
| TEMP-QS-015                  | Midnight-spanning          | `2024-01-15T23:00:00Z/2024-01-16T01:00:00Z`           | Crosses midnight      |
| **Open-Ended Intervals (5)** |
| TEMP-QS-016                  | Open start (date)          | `../2024-12-31`                                       | Before end            |
| TEMP-QS-017                  | Open start (datetime)      | `../2024-12-31T23:59:59Z`                             | Full precision        |
| TEMP-QS-018                  | Open end (date)            | `2024-01-01/..`                                       | After start           |
| TEMP-QS-019                  | Open end (datetime)        | `2024-01-01T00:00:00Z/..`                             | Full precision        |
| TEMP-QS-020                  | Fully open                 | `../..`                                               | No bounds             |
| **Duration Intervals (3)**   |
| TEMP-QS-021                  | Start + duration           | `2024-01-01T00:00:00Z/P1M`                            | 1 month               |
| TEMP-QS-022                  | Duration + end             | `P1Y/2024-12-31T23:59:59Z`                            | 1 year before end     |
| TEMP-QS-023                  | Complex duration           | `2024-01-01T00:00:00Z/P1DT12H`                        | 1.5 days              |
| **Edge Cases (2)**           |
| TEMP-QS-024                  | Leap year                  | `2024-02-29`                                          | Feb 29 valid          |
| TEMP-QS-025                  | Century boundary           | `1999-12-31T23:59:59Z/2000-01-01T00:00:01Z`           | Y2K                   |

### 5.2 Temporal Response Fixtures (15 fixtures)

| Fixture ID    | Resource Type | Temporal Property           | Example Value                                                                      | Notes                           |
| ------------- | ------------- | --------------------------- | ---------------------------------------------------------------------------------- | ------------------------------- |
| TEMP-RESP-001 | System        | validTime                   | `["2024-01-01T00:00:00Z", "2024-12-31T23:59:59Z"]`                                 | Valid for 2024                  |
| TEMP-RESP-002 | System        | validTime                   | `["2024-01-01T00:00:00Z", null]`                                                   | Valid from 2024 onwards         |
| TEMP-RESP-003 | System        | validTime                   | `[null, "2024-12-31T23:59:59Z"]`                                                   | Valid until end of 2024         |
| TEMP-RESP-004 | Deployment    | validTime                   | `["2024-01-15T00:00:00Z", "2024-02-15T23:59:59Z"]`                                 | 1-month deployment              |
| TEMP-RESP-005 | DataStream    | phenomenonTime              | `["2024-01-01T00:00:00Z", "2024-01-31T23:59:59Z"]`                                 | January observations            |
| TEMP-RESP-006 | DataStream    | resultTime                  | `["2024-01-01T00:00:01Z", "2024-01-31T23:59:59Z"]`                                 | Result times                    |
| TEMP-RESP-007 | Observation   | phenomenonTime              | `"2024-01-15T12:00:00Z"`                                                           | Instant                         |
| TEMP-RESP-008 | Observation   | phenomenonTime              | `["2024-01-15T12:00:00Z", "2024-01-15T13:00:00Z"]`                                 | 1-hour interval                 |
| TEMP-RESP-009 | Observation   | resultTime                  | `"2024-01-15T12:00:01Z"`                                                           | 1 second after phenomenon       |
| TEMP-RESP-010 | ControlStream | executionTime               | `["2024-01-15T00:00:00Z", "2024-01-31T23:59:59Z"]`                                 | Command execution times         |
| TEMP-RESP-011 | ControlStream | issueTime                   | `["2024-01-14T00:00:00Z", "2024-01-30T23:59:59Z"]`                                 | Command issue times             |
| TEMP-RESP-012 | Command       | executionTime               | `"2024-01-15T14:00:00Z"`                                                           | Scheduled execution             |
| TEMP-RESP-013 | Command       | issueTime                   | `"2024-01-15T12:00:00Z"`                                                           | Issued 2 hours before execution |
| TEMP-RESP-014 | Observation   | phenomenonTime + resultTime | `{"phenomenonTime": "2024-01-15T12:00:00Z", "resultTime": "2024-01-15T12:00:05Z"}` | 5-second processing delay       |
| TEMP-RESP-015 | Command       | executionTime + issueTime   | `{"executionTime": "2024-01-15T14:00:00Z", "issueTime": "2024-01-15T12:00:00Z"}`   | 2-hour lead time                |

### 5.3 Temporal Error Fixtures (10 fixtures)

| Fixture ID   | Error Type           | Example Query                        | Expected Error Message                                                |
| ------------ | -------------------- | ------------------------------------ | --------------------------------------------------------------------- |
| TEMP-ERR-001 | Invalid month        | `datetime=2024-13-01`                | "Invalid month: 13. Must be 01-12."                                   |
| TEMP-ERR-002 | Invalid date         | `datetime=2024-02-30`                | "Invalid date: 2024-02-30. February has 29 days in 2024."             |
| TEMP-ERR-003 | Invalid hour         | `datetime=2024-01-15T25:00:00Z`      | "Invalid hour: 25. Must be 00-23."                                    |
| TEMP-ERR-004 | Start after end      | `datetime=2024-12-31/2024-01-01`     | "Interval start must be before end."                                  |
| TEMP-ERR-005 | Invalid timezone     | `datetime=2024-01-15T12:00:00+15:00` | "Invalid timezone offset: +15:00. Must be between -12:00 and +14:00." |
| TEMP-ERR-006 | Malformed interval   | `datetime=2024-01-15/`               | "Invalid interval format. Expected: start/end or start/.. or ../end"  |
| TEMP-ERR-007 | Invalid duration     | `datetime=2024-01-01/1M`             | "Invalid duration format. ISO 8601 durations must start with 'P'."    |
| TEMP-ERR-008 | Empty value          | `datetime=`                          | "Parameter 'datetime' requires a value."                              |
| TEMP-ERR-009 | Non-leap year        | `datetime=2023-02-29`                | "Invalid date: 2023-02-29. 2023 is not a leap year."                  |
| TEMP-ERR-010 | latest wrong context | `phenomenonTime=latest`              | "'latest' is only supported for resultTime parameter."                |

### 5.4 Temporal Edge Case Fixtures (5 fixtures)

| Fixture ID    | Edge Case          | Example Query                                                  | Notes                     |
| ------------- | ------------------ | -------------------------------------------------------------- | ------------------------- |
| TEMP-EDGE-001 | Leap year          | `datetime=2024-02-29`                                          | Valid (2024 is leap year) |
| TEMP-EDGE-002 | DST spring forward | `datetime=2024-03-10T02:30:00-08:00`                           | Missing hour (Pacific)    |
| TEMP-EDGE-003 | DST fall back      | `datetime=2024-11-03T01:30:00-07:00`                           | Ambiguous hour (Pacific)  |
| TEMP-EDGE-004 | Midnight (24:00)   | `datetime=2024-01-15T24:00:00Z`                                | ISO 8601 allows 24:00:00  |
| TEMP-EDGE-005 | Antimeridian       | `datetime=2024-01-15T23:00:00-12:00/2024-01-16T01:00:00+14:00` | Date line crossing        |

### 5.5 Fixture Summary

**Total Fixtures:** 55 fixtures

| Fixture Category            | Count | Priority     |
| --------------------------- | ----- | ------------ |
| Temporal Query Strings      | 25    | **CRITICAL** |
| Temporal Response Fixtures  | 15    | HIGH         |
| Temporal Error Fixtures     | 10    | **CRITICAL** |
| Temporal Edge Case Fixtures | 5     | MEDIUM       |

---

## 6. Implementation Estimates

### 6.1 Test Implementation Summary

| Test Category           | Test Count | Lines per Test | Total Lines   | Priority     |
| ----------------------- | ---------- | -------------- | ------------- | ------------ |
| Instant Formats         | 12         | 15-20          | 180-240       | **CRITICAL** |
| Interval Formats        | 15         | 15-20          | 225-300       | **CRITICAL** |
| Open-Ended Intervals    | 9          | 15-20          | 135-180       | **CRITICAL** |
| Timezone Handling       | 9          | 15-20          | 135-180       | **CRITICAL** |
| Parameter Combinations  | 6          | 15-20          | 90-120        | HIGH         |
| Validation Errors       | 8          | 11-15          | 90-120        | **CRITICAL** |
| Edge Cases              | 8          | 15-20          | 120-160       | MEDIUM       |
| Special Values          | 2          | 15             | 30            | MEDIUM       |
| Pagination Interactions | 3          | 15-20          | 45-60         | HIGH         |
| **TOTAL**               | **72**     | **~15 avg**    | **950-1,300** |              |

**Test File Organization:**

```
src/ogc-api/temporal/
  temporal-instant-queries.spec.ts        (~180-240 lines, 12 tests)
  temporal-interval-queries.spec.ts       (~225-300 lines, 15 tests)
  temporal-open-intervals.spec.ts         (~135-180 lines, 9 tests)
  temporal-timezone-handling.spec.ts      (~135-180 lines, 9 tests)
  temporal-combinations.spec.ts           (~90-120 lines, 6 tests)
  temporal-validation-errors.spec.ts      (~90-120 lines, 8 tests)
  temporal-edge-cases.spec.ts             (~120-160 lines, 8 tests)
  temporal-special-values.spec.ts         (~30 lines, 2 tests)
  temporal-pagination.spec.ts             (~45-60 lines, 3 tests)

fixtures/temporal/
  query-strings/                          (25 fixture files)
  responses/                              (15 fixture files)
  errors/                                 (10 fixture files)
  edge-cases/                             (5 fixture files)
```

### 6.2 Implementation Effort Estimates

**Development Tasks:**

| Task                         | Estimated Lines     | Estimated Time  |
| ---------------------------- | ------------------- | --------------- |
| ISO 8601 instant tests       | 180-240             | 3-4 hours       |
| ISO 8601 interval tests      | 225-300             | 4-5 hours       |
| Open-ended interval tests    | 135-180             | 2-3 hours       |
| Timezone handling tests      | 135-180             | 2-3 hours       |
| Parameter combination tests  | 90-120              | 2-3 hours       |
| Validation error tests       | 90-120              | 2-3 hours       |
| Edge case tests              | 120-160             | 2-3 hours       |
| Special value tests          | 30                  | 0.5-1 hour      |
| Pagination interaction tests | 45-60               | 1-2 hours       |
| Fixture creation             | 55 files            | 6-8 hours       |
| Documentation                | 50-100              | 1-2 hours       |
| **TOTAL**                    | **950-1,300 lines** | **25-36 hours** |

**Testing Priorities:**

1. **CRITICAL (Priority 1):** 53 tests, ~810 lines, 16-22 hours

   - Instant formats (all variations)
   - Interval formats (closed and open-ended)
   - Timezone handling (Z notation, offsets, conversions)
   - Validation errors (invalid formats, invalid ranges)

2. **HIGH (Priority 2):** 9 tests, ~135 lines, 5-8 hours

   - Parameter combinations
   - Pagination interactions

3. **MEDIUM (Priority 3):** 10 tests, ~150 lines, 4-6 hours
   - Edge cases (leap years, DST, boundaries)
   - Special values

---

## 7. ISO 8601 Parsing Utilities

> ✅ **REVIEW NOTICE: Strongest Section — Genuine Client Code to Test**
>
> Section 7 defines the actual client code that Section 4 should be testing: `parseInstant()`, `parseInterval()`, `parseDuration()`, `toUTC()`, `validateISO8601()`. These are pure functions that take string input and produce typed output — ideal for unit testing with deterministic assertions. The Section 4 tests should be rewritten to exercise these functions directly rather than asserting `response.ok` against mocks.

### 7.1 Required Parsing Functions

```typescript
/**
 * Parse ISO 8601 instant (date or datetime with optional timezone)
 */
function parseInstant(value: string): Date {
  // Parse: 2024-01-15
  // Parse: 2024-01-15T12:00:00Z
  // Parse: 2024-01-15T12:00:00+05:30
  // Parse: 2024-01-15T12:00:00.123Z
  // Return: Date object in UTC
}

/**
 * Parse ISO 8601 interval (closed, open-start, open-end, fully-open)
 */
function parseInterval(value: string): { start?: Date; end?: Date } {
  // Parse: 2024-01-01/2024-12-31
  // Parse: ../2024-12-31
  // Parse: 2024-01-01/..
  // Parse: ../..
  // Return: { start?, end? }
}

/**
 * Parse ISO 8601 duration (P1Y2M3DT4H5M6S)
 */
function parseDuration(value: string): number {
  // Parse: P1Y (1 year)
  // Parse: P1M (1 month)
  // Parse: P1D (1 day)
  // Parse: PT1H (1 hour)
  // Parse: PT30M (30 minutes)
  // Parse: P1DT12H (1.5 days)
  // Return: milliseconds
}

/**
 * Convert timezone offset to UTC
 */
function toUTC(value: string): string {
  // Convert: 2024-01-15T12:00:00+05:30 → 2024-01-15T06:30:00Z
  // Convert: 2024-01-15T12:00:00-08:00 → 2024-01-15T20:00:00Z
  // Return: ISO 8601 string in UTC (Z notation)
}

/**
 * Validate ISO 8601 format
 */
function validateISO8601(value: string): { valid: boolean; error?: string } {
  // Validate month (01-12)
  // Validate day (01-31, respecting month/year)
  // Validate time (00:00:00 - 23:59:59)
  // Validate timezone offset (-12:00 to +14:00)
  // Return: { valid: true } or { valid: false, error: "..." }
}
```

### 7.2 Recommended Libraries

**Option 1: Luxon (recommended)**

- Full ISO 8601 support (instants, intervals, durations)
- Timezone handling (IANA timezones, offsets)
- Immutable DateTime objects
- ~70KB minified

**Option 2: date-fns**

- Lightweight (~20KB minified)
- Good ISO 8601 parsing (parseISO)
- Timezone support via date-fns-tz
- Less comprehensive interval support

**Option 3: Day.js**

- Very lightweight (~2KB minified)
- Basic ISO 8601 parsing
- Plugins for advanced features
- Limited interval/duration support

**Recommendation:** Use **Luxon** for comprehensive ISO 8601 support, especially for interval and duration parsing.

---

## 8. Client API Design

### 8.1 Temporal Parameter Type

```typescript
type DateTimeParameter =
  | string // ISO 8601 instant or interval string
  | Date // Single instant
  | {
      // Interval with start and/or end
      start?: Date | string;
      end?: Date | string;
    };

type ResultTimeParameter = DateTimeParameter | 'latest';
```

### 8.2 Client API Examples

**Instant Query:**

```typescript
// Date object
client.systems.list({
  datetime: new Date('2024-01-15'),
});
// Encodes to: ?datetime=2024-01-15T00:00:00.000Z

// ISO 8601 string
client.systems.list({
  datetime: '2024-01-15T12:00:00Z',
});
// Encodes to: ?datetime=2024-01-15T12:00:00Z
```

**Interval Query (Closed):**

```typescript
client.systems.list({
  datetime: {
    start: new Date('2024-01-01'),
    end: new Date('2024-12-31'),
  },
});
// Encodes to: ?datetime=2024-01-01T00:00:00.000Z/2024-12-31T00:00:00.000Z
```

**Interval Query (Open-Ended):**

```typescript
// Open end (from start onwards)
client.systems.list({
  datetime: {
    start: new Date('2024-01-01'),
    // end omitted = open-ended
  },
});
// Encodes to: ?datetime=2024-01-01T00:00:00.000Z/..

// Open start (before end)
client.systems.list({
  datetime: {
    end: new Date('2024-12-31'),
    // start omitted = open-ended
  },
});
// Encodes to: ?datetime=../2024-12-31T00:00:00.000Z

// Fully open (all data)
client.systems.list({
  datetime: {
    // both omitted = fully open
  },
});
// Encodes to: ?datetime=../..
```

**phenomenonTime Query:**

```typescript
// Latest observations
client.observations.list({
  resultTime: 'latest',
});
// Encodes to: ?resultTime=latest

// Observations after specific time
client.observations.list({
  phenomenonTime: {
    start: '2024-01-15T12:00:00Z',
  },
});
// Encodes to: ?phenomenonTime=2024-01-15T12:00:00Z/..
```

**Multiple Temporal Parameters:**

```typescript
client.observations.list({
  phenomenonTime: {
    start: '2024-01-15',
    end: '2024-01-16',
  },
  resultTime: 'latest',
});
// Encodes to: ?phenomenonTime=2024-01-15/2024-01-16&resultTime=latest
```

---

## 9. References

### 9.1 Specifications

- **OGC API - Common:** Temporal query parameter (datetime) definition
- **ISO 8601:2004:** Date and time format standard
- **RFC 3339:** ISO 8601 profile for internet protocols
- **CSAPI Part 2 Specification:** OGC 23-002 (temporal parameter definitions) — https://docs.ogc.org/is/23-002/23-002.html

### 9.2 Related Research

- **Section 24:** Query Parameter Combination Testing (temporal + other parameters)
- **Section 23:** Pagination Testing Strategy (temporal + pagination)
- **Section 8:** CSAPI Specification Test Requirements (temporal parameter specs)
- **Section 10:** SWE Common Testing Requirements (Time component)

### 9.3 Implementation References

- Query Parameter Requirements: `csapi-query-parameters.md` (datetime, phenomenonTime, resultTime, executionTime, issueTime)
- Part 2 Requirements: `csapi-part2-requirements.md` (temporal windowing)
- Data Type Requirements: `csapi-datatype-schema-requirements.md` (TimeInstant, TimePeriod types)
- Usage Scenarios: `csapi-usage-scenarios.md` (temporal query examples)

---

## 10. Appendices

### Appendix A: ISO 8601 Quick Reference

**Instant Formats:**

```
2024-01-15                         # Date only
2024-01-15T12:00:00Z               # UTC (Z notation)
2024-01-15T12:00:00+05:30          # Timezone offset
2024-01-15T12:00:00.123Z           # Fractional seconds
2024-01-15T12:00:00                # No timezone (assume UTC)
```

**Interval Formats:**

```
2024-01-01/2024-12-31              # Closed interval
../2024-12-31                      # Open start
2024-01-01/..                      # Open end
../..                              # Fully open
2024-01-01/P1M                     # Start + duration
P1Y/2024-12-31                     # Duration + end
```

**Duration Formats:**

```
P1Y                                # 1 year
P1M                                # 1 month
P1W                                # 1 week
P1D                                # 1 day
PT1H                               # 1 hour (note: T prefix)
PT30M                              # 30 minutes
PT45S                              # 45 seconds
P1DT12H                            # 1 day 12 hours
P1Y2M3DT4H5M6S                     # Complex (1y 2m 3d 4h 5m 6s)
```

### Appendix B: Timezone Offset Examples

| Location          | Timezone                         | Offset      | Example                     |
| ----------------- | -------------------------------- | ----------- | --------------------------- |
| UTC               | Universal Coordinated Time       | +00:00 or Z | `2024-01-15T12:00:00Z`      |
| New York (EST)    | Eastern Standard Time            | -05:00      | `2024-01-15T12:00:00-05:00` |
| Los Angeles (PST) | Pacific Standard Time            | -08:00      | `2024-01-15T12:00:00-08:00` |
| London (GMT)      | Greenwich Mean Time              | +00:00      | `2024-01-15T12:00:00+00:00` |
| Paris (CET)       | Central European Time            | +01:00      | `2024-01-15T12:00:00+01:00` |
| India (IST)       | India Standard Time              | +05:30      | `2024-01-15T12:00:00+05:30` |
| Tokyo (JST)       | Japan Standard Time              | +09:00      | `2024-01-15T12:00:00+09:00` |
| Sydney (AEDT)     | Australian Eastern Daylight Time | +11:00      | `2024-01-15T12:00:00+11:00` |
| Kiribati          | Line Islands Time                | +14:00      | `2024-01-15T12:00:00+14:00` |
| Baker Island      | Baker Island Time                | -12:00      | `2024-01-15T12:00:00-12:00` |

### Appendix C: Temporal Parameter Usage Matrix

| Parameter      | Part 1                  | Part 2 DataStreams         | Part 2 Observations   | Part 2 ControlStreams     | Part 2 Commands      |
| -------------- | ----------------------- | -------------------------- | --------------------- | ------------------------- | -------------------- |
| datetime       | ✅ Systems, Deployments | ✅ validTime               | ❌ Use phenomenonTime | ✅ validTime              | ❌ Use executionTime |
| phenomenonTime | ❌                      | ✅ phenomenonTime property | ✅ phenomenonTime     | ❌                        | ❌                   |
| resultTime     | ❌                      | ✅ resultTime property     | ✅ resultTime         | ❌                        | ❌                   |
| executionTime  | ❌                      | ❌                         | ❌                    | ✅ executionTime property | ✅ executionTime     |
| issueTime      | ❌                      | ❌                         | ❌                    | ✅ issueTime property     | ✅ issueTime         |

### Appendix D: Temporal Parameter Precedence

When multiple temporal parameters are specified:

1. **DataStreams:**

   - `datetime` filters by validTime
   - `phenomenonTime` filters by phenomenonTime property
   - `resultTime` filters by resultTime property
   - All applied with AND logic

2. **Observations:**

   - `phenomenonTime` filters by phenomenonTime
   - `resultTime` filters by resultTime
   - Both applied with AND logic

3. **ControlStreams:**

   - `datetime` filters by validTime
   - `executionTime` filters by executionTime property
   - `issueTime` filters by issueTime property
   - All applied with AND logic

4. **Commands:**
   - `executionTime` filters by executionTime
   - `issueTime` filters by issueTime
   - Both applied with AND logic

---

**End of Document**
