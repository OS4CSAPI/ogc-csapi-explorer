# Section 35: JSDoc Testing Documentation Standards

**Research Plan:** [Research Plan 35: JSDoc Testing Documentation Standards](../research-plans/35-jsdoc-testing-documentation-standards.md)

**Research Questions:** 6 core questions about JSDoc comments needed in test files, documenting test intent/behavior, fixture provenance, coverage gaps, examples, and upstream documentation patterns.

**Methodology:** 6-phase systematic analysis (Phase 1: Upstream Documentation Analysis → Phase 2: JSDoc Tag Analysis → Phase 3: Documentation Level Design → Phase 4: Template Design → Phase 5: Documentation Standards → Phase 6: Synthesis)

**Research Time:** 60 minutes – February 6, 2026

**Primary Source(s):**

- [Implementation Guide](../../../planning/csapi-implementation-guide.md)
- Section 1-2 deliverables: Upstream test documentation patterns
- [TypeDoc documentation standards](https://typedoc.org/)
- [JSDoc specification](https://jsdoc.app/)

**Supporting Resources:**

- Section 19: [Test Organization and File Structure](19-test-organization-file-structure.md) (test file patterns)
- Section 34: [Test Utility and Helper Design](34-test-utility-helper-design.md) (utility documentation)

**Document Purpose:** Lightweight JSDoc guidelines for CSAPI test files, aligned with upstream's near-zero documentation approach and focused on the few places JSDoc genuinely adds value.

---

## Executive Summary

> **⚠️ Review Notice (H4 fix — Phase 2C):** This document originally proposed 12 JSDoc tag types, 12 templates, 4 custom tags (`@specification`, `@fixture`, `@coverage`, `@scenario`), and ~2,000 lines of documentation infrastructure for a test suite estimated at ~5,000 lines. This contradicted its own upstream analysis showing 0.3% documentation density (1 JSDoc block in 8,200+ test lines). The document has been rewritten to align recommendations with upstream's proven minimalist approach: JSDoc for exported test helpers, descriptive test names, and optional brief comments for complex setup.

> **⚠️ Review Notice (C2 fix — Phase 2C):** The `@specification` JSDoc tag was originally recommended throughout this document but has been identified as AP3 (OGC Requirement Traceability). Structural `@specification` tags create spec-traceability infrastructure that organizes tests around spec sections rather than client code behavior. Use plain `// Spec context:` comments instead when noting which spec section informed a test.

**Upstream reality:** 28 test files, ~8,200 lines, 1 JSDoc block, ~25 inline comments. Tests are self-documenting through clear naming and structure. The few comments that exist explain "why" not "what."

**CSAPI approach:** Follow upstream's lead. Three rules:

1. **JSDoc for exported test helper functions** — `@param`, `@returns`, `@example`, `@throws`
2. **Descriptive `describe`/`it` block names** — already upstream practice, no JSDoc needed
3. **Optional brief comments for complex setup** — explain "why" not "what," plain comments only

---

## 1. Upstream Documentation Analysis

### 1.1 Upstream Test Documentation Inventory

**Analysis of 7 Upstream Test Suites:**

| Test Suite  | Files  | Total Lines | JSDoc Blocks | Inline Comments | Documentation Density |
| ----------- | ------ | ----------- | ------------ | --------------- | --------------------- |
| **WFS**     | 7      | ~1,500      | 0            | ~5              | 0.3%                  |
| **WMS**     | 4      | ~800        | 1            | ~3              | 0.5%                  |
| **WMTS**    | 3      | ~600        | 0            | ~2              | 0.3%                  |
| **TMS**     | 2      | ~400        | 0            | ~1              | 0.3%                  |
| **STAC**    | 3      | ~800        | 0            | ~4              | 0.5%                  |
| **OGC-API** | 5      | ~3,500      | 0            | ~8              | 0.2%                  |
| **Shared**  | 4      | ~600        | 0            | ~2              | 0.3%                  |
| **TOTAL**   | **28** | **~8,200**  | **1**        | **~25**         | **0.3%**              |

**Key Finding:** Upstream has **NEAR-ZERO formal documentation** in test files (0.3% documentation density).

### 1.2 Upstream Documentation Patterns

**Pattern 1: No File-Level Documentation**

All 28 upstream test files have **NO** `@fileoverview`, `@module`, or file-level JSDoc comments. Files start directly with imports and test setup.

**Example from ogc-api/endpoint.spec.ts:**

```typescript
import OgcApiEndpoint from './endpoint.js';
import { readFile, stat } from 'fs/promises';
import * as path from 'path';

const FIXTURES_ROOT = path.join(__dirname, '../../fixtures/ogc-api');

beforeAll(() => {
  // Setup fetch mock...
});

describe('OgcApiEndpoint', () => {
  // Tests...
});
```

**Pattern 2: No Test Case Documentation**

Tests are self-documenting through naming and structure:

```typescript
describe('#info', () => {
  it('should return endpoint information', async () => {
    const info = await endpoint.info;
    expect(info).toHaveProperty('title');
    expect(info).toHaveProperty('description');
  });

  it('should throw error if info endpoint fails', async () => {
    // Test implementation...
  });
});
```

**Pattern 3: Minimal Inline Comments (Purpose-Driven)**

The **few comments** that exist explain **WHY** not **WHAT**:

```typescript
// Example 1: Explain non-obvious behavior
// if we're on the root path (e.g. /sample-data/), only answer if there's a trailing slash
// this is made to mimic the behavior of a webapp deployed on http://host.com/webapp/,
// where querying http://host.com/webapp would return a 404
if (url.pathname.split('/').length === 2 && !url.pathname.endsWith('/')) {
  return { ok: false, status: 404 };
}

// Example 2: Explain purpose of cleanup
// this will exhaust all microtasks, effectively preventing rejected promises from leaking between tests
await jest.runAllTimersAsync();

// Example 3: Clarify test focus
// For now we test that the method handles the case properly
it('should handle missing search endpoint', async () => {
  // Test implementation...
});
```

**Pattern 4: One JSDoc Block Found (Exception)**

Found **1 JSDoc block** in WMS capabilities test (409 lines into file):

```typescript
/**
 * @param {string} capabilitiesUrl
 */
function parseCapabilitiesUrl(capabilitiesUrl: string) {
  // Implementation...
}
```

This is the **ONLY** formal JSDoc in 8,200+ lines of test code.

### 1.3 Implications for CSAPI

**Upstream Demonstrates:**

1. ✅ **Tests CAN be self-documenting** through clear naming and structure
2. ✅ **Minimal documentation works** for straightforward test suites
3. ✅ **Comments focus on "why"** not "what" when they exist
4. ✅ **No file-level boilerplate** reduces maintenance burden

**CSAPI Context:**

- CSAPI has more complex specs than upstream's WMS/WFS/WMTS, but this does not change the documentation approach — it changes test _design_, not test _comments_
- Spec complexity is handled by descriptive test names and clear test structure, not by JSDoc tags
- Fixture provenance (where test data came from) can be noted in a brief comment if non-obvious

**Conclusion:** Follow upstream's approach. JSDoc only for exported test helper functions. Tests are self-documenting through naming and structure.

---

## 2. Documentation Guidelines

### 2.1 Where JSDoc Is Required: Exported Test Helper Functions

The **only** place JSDoc is required is on exported functions in test utility modules (e.g., `test-utils/`). These are reusable functions consumed by multiple test files, so callers benefit from parameter documentation.

**Required tags:** `@param`, `@returns`
**Recommended tags:** `@example`, `@throws`
**Optional tags:** `@deprecated`, `@see`

**Example:**

````typescript
/**
 * Parse URL and validate expected components
 *
 * @param url - URL string to parse
 * @param expected - Expected URL components to validate
 * @param expected.pathname - Expected pathname
 * @param expected.query - Expected query parameters
 * @returns Parsed URL components
 * @throws {Error} If URL parsing fails
 *
 * @example
 * ```typescript
 * parseAndValidateUrl('https://api.example.com/systems?limit=10', {
 *   pathname: '/systems',
 *   query: { limit: '10' }
 * });
 * ```
 */
export function parseAndValidateUrl(
  url: string,
  expected: { pathname?: string; query?: Record<string, string> }
): ParsedURL {
  // Implementation...
}
````

### 2.2 Where JSDoc Is Not Needed: Test Files

Following upstream practice, test files (`*.spec.ts`) should **not** have:

- `@fileoverview` blocks — upstream has zero across 28 test files
- `@module` tags — adds no value for test files
- JSDoc on `describe` blocks — the name is the documentation
- JSDoc on `it` blocks — the test name describes intent
- Custom tags (`@fixture`, `@coverage`, `@scenario`) — these create documentation infrastructure that must be maintained but doesn't improve test quality

**Self-documenting test example (upstream pattern):**

```typescript
import {
  createTestQueryBuilder,
  parseAndValidateUrl,
} from '../test-utils/index.js';

describe('CSAPIQueryBuilder - Systems', () => {
  let builder: CSAPIQueryBuilder;

  beforeEach(async () => {
    builder = await createTestQueryBuilder({ conformance: ['systems'] });
  });

  describe('getSystems()', () => {
    it('should construct systems collection URL', async () => {
      const url = builder.getSystems();
      parseAndValidateUrl(url, { pathname: '/systems', query: { f: 'json' } });
    });

    it('should include limit parameter', async () => {
      const url = builder.getSystems({ limit: 10 });
      expectQueryParam(url, 'limit', '10');
    });

    it('should include bbox parameter', async () => {
      const url = builder.getSystems({ bbox: [0, 0, 1, 1] });
      expectQueryParam(url, 'bbox', '0,0,1,1');
    });
  });
});
```

No JSDoc needed — test names explain intent, helper functions are documented at their definition site.

### 2.3 When Plain Comments Are Appropriate

Brief inline comments are appropriate in the same situations upstream uses them — to explain **why**, not **what**:

```typescript
// Open interval: unbounded start per RFC 3339 §5.6
it('should handle open datetime interval', async () => {
  const url = builder.getSystems({ datetime: '../2024-12-31T23:59:59Z' });
  expectQueryParam(url, 'datetime', '../2024-12-31T23:59:59Z');
});
```

```typescript
// Spec context: OGC 23-001 §7.2.1 Table 4 defines required system properties
it('should parse all required system properties from response', async () => {
  // ...
});
```

```typescript
// Exhaust microtasks to prevent rejected promise leaks between tests
await jest.runAllTimersAsync();
```

**Use a comment when:**

- Non-obvious behavior needs a one-line explanation
- A spec section informed the test design (use `// Spec context:` prefix)
- Setup/teardown logic has a subtle purpose

**Don't use a comment when:**

- The test name already explains intent
- The assertion is self-evident from the code
- You're describing what the code does rather than why

---

## 3. Anti-Patterns to Avoid

### 3.1 Redundant Documentation

```typescript
// ❌ Bad: JSDoc repeats the test name
/**
 * This test tests that getSystems returns a valid URL.
 */
it('should return valid URL', async () => { ... });

// ✅ Good: No JSDoc needed — test name is sufficient
it('should return valid URL', async () => { ... });
```

### 3.2 Implementation Documentation

```typescript
// ❌ Bad: Describes HOW test works
/**
 * Mocks fetch to return system collection JSON, calls builder.getSystems(),
 * then parses the URL with parseAndValidateUrl helper.
 */
it('should construct systems URL', async () => { ... });

// ✅ Good: Test name explains intent, code shows implementation
it('should construct systems URL', async () => { ... });
```

### 3.3 Over-Documentation

```typescript
// ❌ Bad: Excessive metadata on test files
/**
 * @fileoverview Tests for parseAndValidateUrl utility function
 * @module tests/test-utils/url
 * @author John Doe
 * @since v1.0.0
 * @version 2.1.3
 * @coverage URL parsing and validation
 * @see test-utils.ts
 */

// ✅ Good: No file-level JSDoc (upstream has zero)
import { parseAndValidateUrl } from '../test-utils.js';
describe('parseAndValidateUrl', () => { ... });
```

### 3.4 Custom Tag Proliferation

```typescript
// ❌ Bad: Custom tags create maintenance burden with no tooling support
/**
 * @specification OGC 23-001 §7.2
 * @fixture fixtures/csapi/systems/system-123.json
 * @coverage System CRUD operations
 * @scenario User queries systems with bbox filter
 */
it('should filter systems by bbox', async () => { ... });

// ✅ Good: One-line comment if context is non-obvious
// Spec context: OGC 23-001 §7.2.3 defines spatial filtering for systems
it('should filter systems by bbox', async () => { ... });
```

---

## 4. Summary

| Context                                   | Approach                                        |
| ----------------------------------------- | ----------------------------------------------- |
| **Exported test helpers** (`test-utils/`) | JSDoc with `@param`, `@returns`, `@example`     |
| **Test files** (`*.spec.ts`)              | No JSDoc — self-documenting via naming          |
| **Non-obvious behavior**                  | Brief `//` comment explaining "why"             |
| **Spec context**                          | `// Spec context: OGC 23-001 §X.Y` when helpful |
| **Complex setup**                         | Brief `//` comment on the non-obvious line      |
| **File-level docs**                       | Not needed (upstream has zero)                  |
| **Custom JSDoc tags**                     | Not recommended                                 |

**Upstream evidence:** 28 test files, ~8,200 lines, 1 JSDoc block (on a helper function), ~25 inline comments. This approach works for a production library with 7 protocol implementations. CSAPI should follow the same pattern.

---

## 5. References

### 5.1 Related Research Documents

- **Section 19:** Test Organization and File Structure (test file patterns)
- **Section 34:** Test Utility and Helper Design (utility documentation standards)
- **Section 1-2:** Upstream Analysis (upstream documentation patterns)

### 5.2 Specification References

- **OGC 23-001:** Connected Systems API Part 1 - Feature Resources
- **OGC 23-002:** Connected Systems API Part 2 - Observation Data
- **OGC 23-003:** Connected Systems API Part 3 - Command & Control

### 5.3 Tool Documentation

- **JSDoc:** https://jsdoc.app/
- **Jest:** https://jestjs.io/

### 5.4 Implementation Guide

- [docs/planning/csapi-implementation-guide.md](../../../planning/csapi-implementation-guide.md) - Documentation standards for source code

---

**END OF DOCUMENT**
