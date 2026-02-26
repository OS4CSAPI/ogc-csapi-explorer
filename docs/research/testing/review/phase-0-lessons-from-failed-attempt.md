# Phase 0: Lessons from Failed Attempt

**Review Date:** February 12, 2026  
**Source Repository:** [OS4CSAPI/ogc-client](https://github.com/OS4CSAPI/ogc-client)  
**Purpose:** Extract specific test anti-patterns that made tests "too geared towards evaluating a server and not a client," to be used as a critical review lens in all subsequent phases.

---

## Executive Summary

A thorough examination of the failed CSAPI implementation at `OS4CSAPI/ogc-client` reveals a **fundamental architectural mismatch** between what was built and what the upstream library expects. The tests treat the client as a thin pass-through to a server, validating that _responses contain correct data_ rather than testing that _client code correctly transforms, constructs, and handles data_. This manifests in 5 distinct anti-patterns documented below, each with concrete examples from the failed repo and the client-oriented equivalent that should have been written.

The core diagnostic: **the failed tests would pass even if the client code did nothing but forward raw server responses**. That's the hallmark of server testing disguised as client testing.

---

## 1. Architectural Context: Why the Tests Went Wrong

### 1.1 The Failed Repo's Architecture

The failed attempt created **standalone client classes** (`SystemsClient`, `DeploymentsClient`, etc.) that each make HTTP requests directly:

```typescript
// Failed architecture: Each resource has its own client class
export class SystemsClient {
  readonly apiRoot: string;
  constructor(apiRoot: string) {
    this.apiRoot = apiRoot;
  }
  async list(): Promise<CSAPISystemCollection> {
    /* fetch from server */
  }
  async get(id: string): Promise<CSAPISystem> {
    /* fetch from server */
  }
}
```

### 1.2 The Upstream Architecture (What Should Be Built)

The upstream library uses a **QueryBuilder pattern** accessed through `OgcApiEndpoint`:

```typescript
// Upstream architecture: QueryBuilder accessed through endpoint factory
const endpoint = new OgcApiEndpoint('https://example.com/api');
const builder = await endpoint.edr('reservoir-api'); // factory method
const url = builder.buildAreaDownloadUrl('POLYGON(...)'); // URL construction
```

The client's job is to:

1. **Parse** service documents (capabilities, conformance, collections)
2. **Construct** URLs with correct parameters
3. **Transform** responses into typed TypeScript objects
4. **Handle** errors, edge cases, and format negotiation
5. **Validate** inputs before making requests

### 1.3 Why This Matters for Testing

When you test a client, you test **your code's logic**. You feed it known inputs (fixtures) and verify your code's outputs (parsed objects, constructed URLs, thrown errors). The failed tests skip this entirely — they feed fixtures through a thin pass-through and then check that the fixtures themselves look correct.

---

## 2. Anti-Pattern Catalog

### Anti-Pattern 1: Testing Response Content Instead of Client Behavior

**What it looks like:** Tests assert that fixture data contains expected fields rather than testing that client code correctly parses/transforms/constructs something.

**Example from failed repo** (`systems.spec.ts`):

```typescript
test('/req/geojson/system-mappings – System properties correctly mapped to GeoJSON', async () => {
  const url = getSystemsUrl(apiRoot);
  const data: any = await maybeFetchOrLoad('systems', url);
  const first = data.features[0];
  const properties = first.properties;
  expect(properties).toBeDefined();
  const hasRequiredProperties =
    properties.name !== undefined || properties.description !== undefined;
  expect(hasRequiredProperties).toBe(true);
  if (properties.name) {
    expect(typeof properties.name).toBe('string');
  }
});
```

**Why it's server-oriented:** This test loads fixture data and checks that the fixture has a `name` or `description` field of type `string`. It tests the _fixture's content_, not any client logic. If the fixture is valid, the test passes regardless of what the client code does.

**What a client-oriented test looks like** (upstream EDR pattern):

```typescript
it('can produce a EDR query builder that provides info and download urls', async () => {
  const builder = await endpoint.edr('reservoir-api');
  expect(builder.supported_queries).toEqual(
    new Set(['area', 'locations', 'cube'])
  );
  expect(Object.keys(builder.supported_parameters)).toEqual([
    'Elevation',
    'Water Temperature',
    'Air Temperature',
  ]);
});
```

**Why it's client-oriented:** This feeds a fixture (mocked as `http://local/edr/sample-data-hub`) into the `OgcApiEndpoint`, which _parses_ the fixture and _constructs_ a builder. The test asserts that the **client's parsing logic** correctly extracted `supported_queries` and `supported_parameters` from the raw fixture data. The client code is doing real work (parsing, transforming), and the test verifies that work.

---

### Anti-Pattern 2: Hybrid Fixture/Live Execution Model

**What it looks like:** Tests are designed to run against either fixtures or live servers via an environment variable toggle (`CSAPI_LIVE=true`).

**Example from failed repo** (`systems.spec.ts`):

```typescript
const apiRoot = process.env.CSAPI_API_ROOT || 'https://example.csapi.server';
const client = new SystemsClient(apiRoot);

test('GET /systems is exposed as systems resources endpoint', async () => {
  const url = getSystemsUrl(apiRoot);
  const data: any = await maybeFetchOrLoad('systems', url);
  expectFeatureCollection(data, 'System');
});
```

**Why it's server-oriented:** The `maybeFetchOrLoad` function either loads a fixture file or makes a real HTTP request to a live server. This is the architecture of a **server conformance test suite** — you point it at a server and it tells you if the server is compliant. Client tests should _never_ hit a live server because they are testing client code, not server behavior.

**What a client-oriented test looks like** (upstream WFS):

```typescript
beforeEach(() => {
  globalThis.fetchResponseFactory = () => capabilities200;
  endpoint = new WfsEndpoint('https://my.test.service/ogc/wfs?...');
});

it('returns service info', async () => {
  await endpoint.isReady();
  expect(endpoint.getServiceInfo()).toEqual({
    abstract: "Service WFS de l'IDS régionale PIGMA",
    title: "Service WFS de l'IDS régionale PIGMA",
    // ... specific parsed values
  });
});
```

**Why it's client-oriented:** The fetch is globally mocked to return a specific fixture. There is no option to hit a live server. The test creates a client, feeds it the fixture through the mock, and verifies that the client correctly parsed the XML capabilities document into a specific TypeScript object. The test is 100% deterministic and tests only client logic.

---

### Anti-Pattern 3: OGC Requirement Traceability as Test Design Driver

**What it looks like:** Tests are named after and structured around OGC specification requirement IDs (e.g., `/req/system/canonical-endpoint`), testing whether the _server_ satisfies those requirements rather than testing client-side handling.

**Example from failed repo** (`common.spec.ts`):

```typescript
test('Conformance declaration lists valid CSAPI conformance classes', async () => {
  const url = `${apiRoot}/conformance`;
  const data = await maybeFetchOrLoad('common_conformance', url);
  const conformsTo = (data as any).conformsTo;
  expect(Array.isArray(conformsTo)).toBe(true);
  expect(conformsTo.length).toBeGreaterThan(0);
  const joined = conformsTo.join(' ');
  expect(joined).toMatch(/connected-systems/i);
  expect(joined).toMatch(/ogcapi-features/i);
});
```

**Why it's server-oriented:** This test checks that a conformance document contains specific URIs. That's a server compliance check ("Does this server declare CSAPI conformance?"). The client's job regarding conformance is to _read_ the document and _set flags_ based on what it finds — e.g., `endpoint.hasConnectedSystemsApi` should resolve to `true` when specific conformance classes are present.

**What a client-oriented test looks like** (upstream endpoint.spec.ts):

```typescript
it('supports EDR', async () => {
  await expect(endpoint.hasEnvironmentalDataRetrieval).resolves.toBe(true);
});
```

**Why it's client-oriented:** This tests that the client's conformance parsing code correctly reads a fixture's conformance classes and sets the boolean property. The assertion is about client behavior (does `hasEnvironmentalDataRetrieval` return `true`?), not about the fixture content.

---

### Anti-Pattern 4: Asserting Data Shape Instead of Testing Transformation

**What it looks like:** Tests use helper functions like `expectFeatureCollection()`, `expectGeoJSONFeature()` to validate that raw data matches a shape, rather than testing that the client transforms raw data into specific typed objects.

**Example from failed repo** (`datastreams.spec.ts`):

```typescript
test('GET /datastreams is exposed as canonical Datastreams collection', async () => {
  const url = getDatastreamsUrl(apiRoot);
  const data: any = await maybeFetchOrLoad('datastreams', url);
  expectFeatureCollection(data, 'Datastream');
  expect(Array.isArray(data.features)).toBe(true);
  expect(data.features.length).toBeGreaterThan(0);
});
```

**Why it's server-oriented:** `expectFeatureCollection` checks that the loaded data has `type: 'FeatureCollection'`, the right `itemType`, and features. This validates the data, not any code. The data came straight from a fixture — no client code processed it.

**What a client-oriented test looks like** (upstream endpoint.spec.ts for collections):

```typescript
it('returns airports collection info', async () => {
  await expect(endpoint.getCollectionInfo('airports')).resolves.toStrictEqual({
    title: 'Airports',
    description: 'A centre point for all major airports including a name.',
    id: 'airports',
    itemFormats: ['text/html', 'application/vnd.ogc.fg+json', ...],
    bulkDownloadLinks: { ... },
  });
});
```

**Why it's client-oriented:** The fixture is a raw JSON service document. The client's `getCollectionInfo()` method parses it and returns a typed `OgcApiCollectionInfo` object. The test verifies the **output of client parsing**, not the raw input data.

---

### Anti-Pattern 5: Graceful Skipping Based on Fixture Content

**What it looks like:** Tests inspect fixture data to decide whether to run assertions, skipping tests when fixtures lack certain content. This is appropriate for server conformance testing (you can't know what a server supports) but inappropriate for client tests (you control the fixtures).

**Example from failed repo** (`controlstreams.spec.ts`):

```typescript
test('System-scoped control streams reference', async () => {
  const root = await maybeFetchOrLoad('controlStreams', url);
  if (!root.features?.length) {
    console.warn('[controlstreams.spec] No controlStreams features; skipping.');
    return;
  }
  const withSystem = root.features.filter((f) => {
    const p = f.properties || {};
    return (
      p.system?.id || (Array.isArray(p.systemIds) && p.systemIds.length > 0)
    );
  });
  if (!withSystem.length) {
    console.warn('[controlstreams.spec] No system linkage; skipping.');
    return;
  }
  // ... actual assertions only if data allows
});
```

**Why it's server-oriented:** This test doesn't know what it's going to find in the data. It conditionally runs based on fixture content. In a client test, _you write the fixture to exercise the exact scenario you're testing_. You never skip because the fixture "doesn't have the data" — if you need the data, you put it in the fixture.

**What a client-oriented approach looks like:**

```typescript
// You control the fixture — design it to test the specific scenario
beforeEach(() => {
  globalThis.fetchResponseFactory = (url) => {
    if (url.includes('/controlStreams')) return controlStreamsWithSystemLinks;
    // ...
  };
});

it('navigates from control stream to parent system', async () => {
  const endpoint = new OgcApiEndpoint('http://local/csapi/');
  const builder = await endpoint.csapi('my-collection');
  const url = builder.controlStreams().forSystem('sys-001').buildUrl();
  expect(url).toBe(
    'https://example.com/api/collections/my-collection/systems/sys-001/controlStreams'
  );
});
```

---

## 3. Patterns & Red Flags to Watch For During Review

These are signals that a test recommendation in the research documents may be server-oriented rather than client-oriented:

### Red Flags in Test Descriptions

| Red Flag                                  | Why It's Concerning                                      |
| ----------------------------------------- | -------------------------------------------------------- |
| "Validates that the response contains..." | Testing data content, not client behavior                |
| "Confirms the API exposes..."             | Testing server behavior, not client parsing              |
| "The endpoint SHALL..."                   | OGC requirement language — these are server requirements |
| "Hybrid fixture/live execution"           | Architecture of a server conformance suite               |
| "Skip if fixture lacks..."                | Testing unknown data instead of controlled scenarios     |
| "Confirms correct Content-Type"           | Server responsibility, not client logic                  |
| "Verifies canonical URL structure"        | May test fixture data rather than URL construction       |

### Red Flags in Test Code Patterns

| Pattern                                       | Why It's Concerning                         |
| --------------------------------------------- | ------------------------------------------- |
| `maybeFetchOrLoad()` dual-mode                | Designed for server testing portability     |
| `process.env.CSAPI_LIVE` toggle               | Client tests don't need live server support |
| `expectFeatureCollection(data)` on raw data   | Validating input data shape, not output     |
| `console.warn(...); return;` conditional skip | Fixture content shouldn't be unknown        |
| `data.features[0].properties.X !== undefined` | Checking fixture content exists             |
| Test named after `/req/X/Y` requirement       | May be testing server compliance            |

### Green Flags (Client-Oriented Indicators)

| Pattern                                               | Why It's Good                 |
| ----------------------------------------------------- | ----------------------------- |
| "Given this fixture, does our parser produce..."      | Tests transformation          |
| "Does `builder.method()` construct URL..."            | Tests URL construction logic  |
| `expect(endpoint.someProperty).resolves.toEqual(...)` | Tests client output           |
| `globalThis.fetchResponseFactory = () => fixture`     | Controlled, mocked input      |
| `expect(() => builder.bad()).toThrow()`               | Tests client validation logic |
| `expect(parsedResult).toStrictEqual({ ... })`         | Tests specific parsed output  |

---

## 4. Summary of Root Causes

| Root Cause                                                | Impact                                                                                  | Prevalence in Failed Repo          |
| --------------------------------------------------------- | --------------------------------------------------------------------------------------- | ---------------------------------- |
| Standalone client classes instead of QueryBuilder pattern | Tests can't test URL construction because there's no URL builder to test                | Architectural — affects everything |
| `maybeFetchOrLoad` dual-mode design                       | Tests are structured to validate server responses rather than client logic              | Every test file uses this          |
| OGC requirement IDs as test structure                     | Tests verify spec compliance (server responsibility) instead of client behavior         | Every test file uses this          |
| No mocking of `fetch`                                     | Client code isn't isolated; tests are integration tests against fixture-as-server       | No test uses fetch mocking         |
| Fixtures as truth source, not test input                  | Tests check "is this fixture valid?" not "does our code handle this fixture correctly?" | Majority of assertions             |

---

## 5. Implications for Research Document Review

When reviewing the 38 research findings documents in subsequent phases, each document should be evaluated against these questions:

1. **Does this document recommend testing client code behavior, or server response content?**
2. **Do code examples show assertions against client method outputs, or against raw fixture data?**
3. **Does the testing strategy assume controlled fixtures with mocked fetch, or a hybrid fixture/live model?**
4. **Are test scenarios driven by "what should our code do?" or by "what should the server provide?"**
5. **Do recommended patterns match upstream conventions (QueryBuilder + mocked fetch + parsed output assertions)?**

Any research recommendation that echoes the failed repo's patterns should be flagged as high-priority for correction.

---

## 6. Reference: Upstream Test Pattern Summary

For quick comparison during review, here is what upstream acceptance-quality tests look like:

### Unit Tests (helpers, model)

- Pure function input → output verification
- No HTTP, no fixtures needed
- Example: `DateTimeParameterToEDRString(date) → '2025-01-01T00:00:00.000Z'`
- Example: `zParameterToString({ type: 'single', level: 850 }) → '850'`

### Integration Tests (endpoint)

- `globalThis.fetchResponseFactory` mocks all HTTP responses
- Fixtures loaded as module imports, returned by the mock
- Create `OgcApiEndpoint` → call its methods → assert **parsed/constructed outputs**
- Example: `endpoint.edr('reservoir-api')` → `builder.buildAreaDownloadUrl(...)` → assert full URL string
- Example: `endpoint.getCollectionInfo('airports')` → assert specific parsed TypeScript object

### Error Tests

- Client validation tested by providing invalid inputs
- `expect(() => builder.buildAreaDownloadUrl(..., { parameter_name: ['BadParam'] })).toThrow()`
- CORS errors, HTTP errors, service exceptions all tested through mocked responses

### What's NOT Tested

- Whether the server returns valid data (that's the server's problem)
- Whether the fixture conforms to the OGC spec (that's fixture quality, not client code)
- Whether live servers work (no live server testing in upstream)
