# Feature Specification: CSAPI Client Support

**Project:** OGC API – Connected Systems (CSAPI) v1.0 Client Implementation  
**Target Repository:** camptocamp/ogc-client  
**Status:** In Development

---

## 1. Contribution Vision

This contribution adds comprehensive client support for OGC API – Connected Systems (CSAPI) v1.0 to ogc-client, enabling developers to build applications that communicate with CSAPI-compliant servers. The implementation provides standards-based programmatic access to sensor systems, real-time observations, deployments, and dynamic data streams, eliminating the need for developers to manually implement the specification and ensuring their applications achieve interoperability with any CSAPI-compliant endpoint. By extending ogc-client's proven patterns to cover this newly published standard (July 2025), this work fills a critical gap for IoT, sensor web, and observational data applications. The contribution implements both Part 1 (Feature Resources) and Part 2 (Dynamic Data), delivering complete CSAPI client functionality that aligns with upstream conventions and reduces the development burden for standards-compliant sensor data integration.

---

## 2. Feature Overview

### 2.1 Motivation & Context

OGC API – Connected Systems (CSAPI) v1.0 was published in July 2025 as the modern successor to SOS (Sensor Observation Service). The standard defines RESTful access to sensor systems, observations, deployments, and control mechanisms. Despite its importance for IoT and sensor web applications, no TypeScript client library currently supports CSAPI. This creates a gap where developers must manually implement the specification to access CSAPI-compliant servers.

The ogc-client library already supports multiple OGC API standards (WFS, STAC, EDR). Adding CSAPI support extends this coverage to sensor and observational data, enabling developers to access all major OGC API families through a single, consistent TypeScript interface.

### 2.2 In Scope

**Core Implementation (following PR #114 EDR pattern):**

- URL building pattern: Library provides URL strings, users handle `fetch()`
- `endpoint.csapi(collectionId)` navigator pattern
- Per-collection navigator instances with caching

**Resource Coverage (9 CSAPI resource types):**

_Part 1: Feature Resources_

- Systems (12 methods: CRUD + history + subsystems)
- Procedures (8 methods: CRUD + history)
- Deployments (8 methods: CRUD + history)
- Sampling Features (8 methods: CRUD + history)
- Properties (6 methods: CRUD)

_Part 2: Dynamic Data_

- Datastreams (11 methods: CRUD + observations + schema)
- Observations (9 methods: Read/create + time filtering)
- Control Streams (8 methods: CRUD + timing)
- Commands (8 methods: CRUD + status)

**Query Support:**

- All CSAPI query parameters: bbox, datetime, limit, offset, filters
- Pagination support (offset-based)
- Format negotiation (GeoJSON and SensorML via Accept headers)
- Proper URL encoding and parameter handling

**Testing & Quality:**

- Client-oriented tests (real-world usage scenarios)
- Unit tests for all URL builder methods
- Integration tests for endpoint conformance
- Parser and validator test coverage
- Target: 85%+ overall test coverage
- OGC-conformant test fixtures

**Integration:**

- Extend `OgcApiEndpoint` following upstream patterns
- Conformance class detection
- Collection-level capability checking
- TypeScript interfaces for all query options

### 2.3 Testing Strategy - Ensuring Meaningful Coverage

**Context:** Previous iterations received feedback that tests were too trivial and didn't deeply validate functionality. This section defines what constitutes appropriate, meaningful testing for a TypeScript URL-building client library implementing CSAPI.

**What "Meaningful Tests" Look Like for This Project:**

**1. URL Builder Tests (Unit Level)**

- ✅ **GOOD:** Verify complete URL structure including base path, resource path, and query string
- ✅ **GOOD:** Test all query parameter combinations with real values from the spec
- ✅ **GOOD:** Validate proper URL encoding (spaces, special characters, arrays)
- ✅ **GOOD:** Test edge cases (empty params, null values, boundary conditions)
- ❌ **TRIVIAL:** Just checking that method returns a string

**Example of meaningful test:**

```typescript
// GOOD - Validates complete URL structure and encoding
expect(
  navigator.getSystemsUrl({
    bbox: [-180, -90, 180, 90],
    datetime: '2024-01-01T00:00:00Z/..',
    limit: 10,
  })
).toBe(
  'https://api.example.com/systems?bbox=-180,-90,180,90&datetime=2024-01-01T00:00:00Z/..&limit=10'
);

// TRIVIAL - Doesn't validate anything meaningful
expect(typeof navigator.getSystemsUrl()).toBe('string');
```

**2. Integration Tests (Endpoint Level)**

- ✅ **GOOD:** Test endpoint conformance detection from real CSAPI landing page fixtures
- ✅ **GOOD:** Verify collection capability checking (does collection X support resource Y?)
- ✅ **GOOD:** Test navigator caching and instance reuse
- ✅ **GOOD:** Validate error handling for non-CSAPI endpoints
- ❌ **TRIVIAL:** Only testing that methods exist

**3. Parser/Validator Tests (Format Handling)**

- ✅ **GOOD:** Test with real GeoJSON features from CSAPI spec examples
- ✅ **GOOD:** Test with real SensorML 3.0 documents (SimpleProcess, AggregateProcess, PhysicalSystem)
- ✅ **GOOD:** Test with real SWE Common 3.0 data components (DataArray, DataRecord, Quantity, etc.)
- ✅ **GOOD:** Validate that parsers detect malformed data
- ✅ **GOOD:** Test property extraction from nested structures
- ❌ **TRIVIAL:** Only testing with minimal/empty objects

**4. Format Negotiation Tests**

- ✅ **GOOD:** Verify Accept headers are set correctly for GeoJSON vs SensorML
- ✅ **GOOD:** Test Content-Type detection for different response formats
- ✅ **GOOD:** Validate that format parameter propagates through URL building
- ❌ **TRIVIAL:** Just checking that header exists

**5. Standards Compliance Tests**

- ✅ **GOOD:** Validate query parameters match CSAPI spec exactly
- ✅ **GOOD:** Test datetime/bbox formats follow OGC API Common patterns
- ✅ **GOOD:** Verify conformance class URIs are correct
- ✅ **GOOD:** Test that generated URLs match OpenAPI spec examples
- ❌ **TRIVIAL:** Not checking against actual spec requirements

**What We're NOT Testing (Because Users Handle It):**

- ❌ Network requests (no fetch/axios in library)
- ❌ Authentication/authorization (user's responsibility)
- ❌ Retry logic or error handling for HTTP failures
- ❌ Full server round-trips (that's what CSAPI-Live-Testing repo was for)

**Coverage Targets:**

- **Overall:** 85%+ statement coverage
- **Critical paths:** 95%+ (URL builders, parsers, validators)
- **Edge cases:** Explicit tests for null, undefined, empty arrays, boundary values
- **Real data:** Use fixtures from actual CSAPI servers and spec examples

**Reference Point:**
Study [PR #114 (EDR implementation)](https://github.com/camptocamp/ogc-client/pull/114) test suite to understand upstream expectations for test depth and quality.

**Validation:**
Before claiming tests are "complete," ask:

1. Do tests use real data from the CSAPI spec?
2. Do they validate complete behavior, not just existence?
3. Would they catch actual bugs in URL construction or parsing?
4. Do they test the spec-defined edge cases?

### 2.4 Out of Scope

**Explicitly excluded (defer or not applicable):**

- HTTP execution (users control fetch, auth, retries)
- Response parsing into domain objects (users handle JSON)
- Client-side validation of payloads before POST/PUT
- Server-side pagination cursor support (CSAPI uses offset-based)
- Advanced SWE Common encoding/decoding beyond format negotiation
- WebSocket subscriptions (CSAPI doesn't define this)
- Non-CSAPI OGC standards (separate concerns)

**Deferred to future work:**

- System Events resource (Part 3, not yet published)
- System History detailed query support (if spec evolves)
- Performance benchmarking suite
- Browser-specific optimizations

### 2.5 Upstream Alignment & Constraints

**Non-Negotiable Principles:**

**Minimal Impact on Existing Code:**

- Modify existing upstream files **only when absolutely necessary** for CSAPI integration
- Do NOT refactor, optimize, or "improve" existing upstream code
- Do NOT fix existing upstream test failures or issues unrelated to CSAPI
- Do NOT change existing patterns, conventions, or architectural choices
- Preserve all existing functionality - zero regressions

**Additive-Only Approach:**

- New functionality lives in isolated `src/ogc-api/csapi/` directory
- Changes to shared files (`endpoint.ts`, `info.ts`, `index.ts`) limited to:
  - Adding CSAPI conformance checking
  - Adding `csapi()` method to endpoint
  - Exporting CSAPI types
- Each modification to existing files must be justified as essential for CSAPI functionality

**Diff Discipline:**

- Every line changed in an existing file must directly support CSAPI integration
- Prefer duplication over refactoring shared code
- Follow existing code style exactly (no formatting changes)
- Avoid "while we're here" improvements

**Rationale:** Maintainers must review changes efficiently. Mixing CSAPI addition with unrelated changes creates review burden, increases merge conflict risk, and reduces approval likelihood.

### 2.6 Code Volume Considerations

**Context:** Previous implementation (second iteration) resulted in ~2x the size of the entire upstream codebase. This raised concerns about contribution proportionality and maintainability.

**Risk:** A disproportionately large contribution may:

- Overwhelm maintainers during review
- Suggest over-engineering or unnecessary complexity
- Create long-term maintenance burden
- Reduce likelihood of acceptance

**Mitigation Strategy:**

**1. Understand What Drives Code Volume:**

- [ ] **9 resource types** - CSAPI has more resource types than other OGC APIs
- [ ] **Dual formats** - GeoJSON + SensorML support doubles some code
- [ ] **Complex schemas** - SWE Common data components, SensorML structures
- [ ] **Comprehensive tests** - 85%+ coverage target means significant test code
- [ ] **TypeScript interfaces** - Full type safety requires extensive type definitions

**2. Justify vs Eliminate:**

- **Necessary complexity:** If CSAPI genuinely requires more code due to standard scope, document why
- **Over-engineering:** Identify and eliminate unnecessary abstractions, utilities, or features
- **Comparison:** Compare code volume to PR #114 (EDR) proportionally - EDR has fewer resources, so some size difference is expected
- **Test vs Implementation ratio:** Verify test code isn't artificially inflating size

**3. Pre-Submission Analysis:**
Before submitting PR, perform code volume audit:

- [ ] Total lines of implementation code (exclude tests, fixtures, comments)
- [ ] Compare to PR #114 on per-resource basis (EDR has X resources, CSAPI has 9)
- [ ] Identify any bloat: duplicated code, unused utilities, over-abstraction
- [ ] Prepare justification for volume if significantly larger than expected

**4. Communication Strategy:**
If volume remains high after optimization:

- Document in PR description why CSAPI requires more code
- Highlight that CSAPI Part 1 + Part 2 = ~2x the scope of typical OGC API
- Show per-resource code is comparable to EDR
- Emphasize test coverage quality, not just quantity
- Offer to phase contribution if needed (Part 1 first, Part 2 later)

**5. Red Lines:**

- **Absolute maximum:** If implementation exceeds upstream size, must have compelling justification
- **Comparison to EDR:** CSAPI code should be proportional (9 resources vs EDR's resource count)
- **Tests:** Test code can be large if meaningful, but should be reviewed for bloat

**Success Metric:** Maintainer doesn't question contribution size, or questions are easily answered with clear justification.

### 2.7 Standards & Specifications

**Primary:**

- [OGC API – Connected Systems Part 1: Feature Resources (23-001) v1.0](https://docs.ogc.org/is/23-001/23-001.html)
  - [OpenAPI Specification](../research/ogcapi-connectedsystems-1.bundled.oas31.yaml) (local reference)
- [OGC API – Connected Systems Part 2: Dynamic Data (23-002) v1.0](https://docs.ogc.org/is/23-002/23-002.html)
  - [OpenAPI Specification](../research/ogcapi-connectedsystems-2.bundled.oas31.yaml) (local reference)

**Supporting:**

- [OGC SWE Common Data Model (23-000) v3.0](https://docs.ogc.org/is/23-000/23-000.html) - Data component structure
- [OGC SensorML (24-014) v3.0](https://docs.ogc.org/is/24-014/24-014.html) - System description format
- [GeoJSON (RFC 7946)](https://tools.ietf.org/html/rfc7946) - Alternative feature encoding

**Reference Implementation:**

- [PR #114 (EDR implementation)](https://github.com/camptocamp/ogc-client/pull/114) - Direct pattern template for architecture

**Previous Work:**

- Upstream request: [camptocamp/ogc-client#118](https://github.com/camptocamp/ogc-client/issues/118) - Original issue requesting CSAPI support
- Exploratory repo: [OS4CSAPI/ogc-client-homework](https://github.com/OS4CSAPI/ogc-client-homework) (257 commits - learning phase)
- Second iteration: [OS4CSAPI/ogc-client-CSAPI](https://github.com/OS4CSAPI/ogc-client-CSAPI) (refined implementation - Phases 1-5 ~90% complete)
- Meta/planning repo: [OS4CSAPI/os4csapi-meta](https://github.com/OS4CSAPI/os4csapi-meta) (issue tracking and planning for second iteration)
- Live testing repo: [Sam-Bolling/CSAPI-Live-Testing](https://github.com/Sam-Bolling/CSAPI-Live-Testing) (live server integration testing against OSH deployment)
- Cleaned repo: [OS4CSAPI/ogc-client](https://github.com/OS4CSAPI/ogc-client) (14 commits - rebased)
- Draft PR: [camptocamp/ogc-client#131](https://github.com/camptocamp/ogc-client/pull/131)

**CSAPI Ecosystem - Related Implementations:**

_Client Applications:_

- [osh-viewer](https://github.com/Botts-Innovative-Research/osh-viewer) - JavaScript webapp CSAPI client
- [oscar-viewer](https://github.com/Botts-Innovative-Research/oscar-viewer) - TypeScript webapp CSAPI client

_Client Libraries:_

- [OWSLib](https://github.com/geopython/OWSLib) - Python library for OGC web services (including CSAPI)
- [OSHConnect-Python](https://github.com/Botts-Innovative-Research/OSHConnect-Python) - Python client for CSAPI
- [ConnectedSystemsAPI-CPP](https://github.com/Botts-Innovative-Research/ConnectedSystemsAPI-CPP) - C++ CSAPI library

_Server Implementations:_

- [OpenSensorHub](https://github.com/opensensorhub) - Reference CSAPI server implementation
- [52°North OGC API Connected Systems](https://52north.org/software/software-components/ogc-api-connected-systems/) - Alternative CSAPI server

### 2.8 Success Criteria

**Complete when:**

- ✅ URL builder methods exist for all 70+ CRUD operations across 9 resources
- ✅ Both GeoJSON and SensorML format negotiation supported via Accept headers
- ✅ All query parameters from spec supported with proper encoding
- ✅ Pagination (offset-based) fully functional
- ✅ 85%+ test coverage with client-oriented tests
- ✅ Integration tests validate conformance checking
- ✅ TypeScript interfaces provide full type safety
- ✅ JSDoc documentation for all public methods
- ✅ Usage examples demonstrate common workflows
- ✅ Upstream Vue demo app works with CSAPI integration (no regressions)
- ✅ Upstream maintainers approve PR for merge

---

## 3. Technical Design

_[To be completed]_

---
