# Section 21: TypeScript Type Testing Strategy

> **⚠️ REVIEW NOTICE — Phase 2D Issues H4, L1 (Resolved)**
>
> This document contains excellent upstream analysis (Section 1), a correct
> tool evaluation recommending TypeScript compiler-only (Section 2), a useful
> type inventory (Section 3), and a sound compile-time vs runtime analysis
> that correctly concludes "CSAPI needs minimal runtime validation" (Section 5).
>
> **H4 — Shape-Assertion Test Template (AP4):** Section 4 (Type Test Patterns)
> and Section 6 Template 1 (`model.spec.ts`) consist of tests that construct
> objects matching TypeScript interfaces and assert the values they just set:
> `const system: System = { name: 'Sensor' }; expect(system.name).toBe('Sensor');`
> This tests nothing — the TypeScript compiler already validates the object
> literal matches the interface at compile time, and the runtime assertion
> only verifies a variable equals the value assigned on the previous line.
> See review notices at Sections 4, 6.
>
> **L1 — 6-Hour Estimate for Low-Value Tests:** Section 8 allocates ~6 hours
> to implement the shape-assertion tests that H4 identifies as zero-value.
> The document's own Section 5 analysis correctly concludes compilation-only
> testing is sufficient, but the estimate contradicts this finding.
>
> **Directly usable content:** Section 1 (upstream EDR `ZParameter` patterns),
> Section 2 (tool evaluation — TypeScript compiler only), Section 3 (type
> inventory), Section 5 (runtime vs compile-time strategy), Template 2 (type
> guard tests — if type guards are implemented), Template 3 (QueryBuilder
> integration tests — tests real behavior), Section 7 recommendations.
>
> **Key takeaway from this document's own analysis:** Types compile = types
> work. The EDR pattern (Section 1) tests _behavior_ (serialization via
> `zParameterToString`), not structure. CSAPI type tests should similarly
> test functions that consume/produce these types, not construct and re-read
> object literals.

**Research Plan:** [Research Plan 21: TypeScript Type Testing Strategy](../research-plans/21-typescript-type-testing.md)

**Research Questions:** 6 core questions about testing TypeScript interfaces compile correctly, type discrimination (union types), generic type constraints, type inference, upstream patterns for type testing, and whether compilation tests are sufficient or runtime tests needed

**Methodology:** 6-phase systematic analysis (Phase 1: Upstream Type Test Analysis of EDR model patterns → Phase 2: Type Testing Tools Research evaluating tsd/dtslint vs TypeScript compiler → Phase 3: CSAPI Type Inventory cataloging all interfaces/unions/generics → Phase 4: Type Test Pattern Design for each category → Phase 5: Runtime vs Compile-Time Strategy definition → Phase 6: Synthesis into comprehensive type testing strategy)

**Research Time:** 3.5 hours (February 8, 2026)

**Primary Source(s):**

- [TypeScript Types Analysis](../../upstream/typescript-types-analysis.md)
- [Datatype Schema Requirements](../../requirements/csapi-datatype-schema-requirements.md)
- [CSAPI Implementation Guide](../../../planning/csapi-implementation-guide.md) (Type system specification)

**Supporting Resources:**

- Section 1: [EDR Test Blueprint](01-edr-test-blueprint.md) (upstream type test patterns)
- Section 2: [Upstream Test Consistency](02-upstream-test-consistency.md) (type testing approaches)
- Section 8: [CSAPI Specification Reference](08-csapi-specification-test-requirements.md) (reclassified — spec property catalog, not test generator)
- [TypeScript Documentation](https://www.typescriptlang.org/docs/)
- [tsd Library Documentation](https://github.com/SamVerschueren/tsd)

**Document Purpose:** Defines compilation-based type testing strategy using TypeScript compiler + Jest (no specialized tools) for CSAPI's ~400 lines of type definitions across 20+ interfaces, 3 discriminated unions, and 5 type aliases, following upstream patterns with explicit type annotations and runtime validation only where needed

---

## Executive Summary

TypeScript type testing strategy for CSAPI implementation based on upstream patterns and industry standards. Upstream uses **compilation-based type testing** with explicit TypeScript annotations in Jest tests, NOT specialized tools like `tsd` or `dtslint`. This pragmatic approach provides compile-time type safety while validating runtime behavior, making it suitable for CSAPI's ~400 lines of type definitions.

### Key Findings

**Type Testing Approach:**

- ✅ **Compilation-only testing** (matches upstream)
- ✅ **Explicit type annotations** in tests (`const x: Type = ...`)
- ✅ **Jest + ts-jest + TypeScript compiler** (no specialized tools)
- ✅ **Runtime validation** for discriminated unions and serialization
- ❌ **No tsd/dtslint** (not needed for CSAPI's type complexity)

**CSAPI Type Inventory:**

- **20+ interfaces** (9 resources + helpers + collections)
- **3 discriminated unions** (minimal - mostly simple interfaces)
- **5 type aliases** (string unions for systemType, etc.)
- **~400 lines** of type definitions total
- **0 generic constraints** requiring specialized testing

**Testing Strategy:**

- **Primary:** TypeScript compilation validates type correctness
- **Secondary:** Runtime tests validate behavior (serialization, discrimination)
- **Pattern:** Explicit type annotations + Jest assertions
- **Coverage:** Interface compilation + union discrimination + optional property handling

### Recommendation

**Adopt upstream pattern:** Jest + TypeScript compiler, NO specialized type testing tools.

**Why:**

1. Upstream successfully tests complex discriminated unions (EDR ZParameter) this way
2. CSAPI types are simpler than EDR (fewer discriminated unions)
3. No tsd/dtslint in upstream dependencies (verified in package.json)
4. Industry standard for libraries without complex generic constraints
5. Zero additional dependencies or configuration

---

## Table of Contents

1. [Upstream Type Test Analysis](#1-upstream-type-test-analysis)
2. [Type Testing Tools Evaluation](#2-type-testing-tools-evaluation)
3. [CSAPI Type Inventory](#3-csapi-type-inventory)
4. [Type Test Patterns](#4-type-test-patterns)
5. [Runtime vs Compile-Time Strategy](#5-runtime-vs-compile-time-strategy)
6. [Implementation Templates](#6-implementation-templates)
7. [Recommendations](#7-recommendations)
8. [Implementation Estimates](#8-implementation-estimates)

---

## 1. Upstream Type Test Analysis

### Testing Stack

**Upstream testing tools (from package.json):**

```json
"devDependencies": {
  "@types/jest": "^29.5.11",
  "@types/node": "^20.2.5",
  "jest": "^29.7.0",
  "ts-jest": "^29.1.1",
  "typescript": "^5.9.3"
}
```

**Key findings:**

- ✅ Jest 29.7.0 + ts-jest 29.1.1 (TypeScript integration)
- ✅ TypeScript 5.9.3 (latest)
- ❌ **No tsd or dtslint** (no specialized type testing tools)
- ❌ **No expect-type** or similar

**Conclusion:** Upstream relies on TypeScript compiler + Jest for type testing.

### Type Testing Patterns Found

#### Pattern 1: Discriminated Union Testing (EDR ZParameter)

**Source:** `src/ogc-api/edr/model.spec.ts`

```typescript
describe('zParameterToString', () => {
  test('single level', () => {
    const z: ZParameter = { type: 'single', level: 850 };
    expect(zParameterToString(z)).toBe('850');
  });

  test('interval (min/max)', () => {
    const z: ZParameter = { type: 'interval', minLevel: 100, maxLevel: 550 };
    expect(zParameterToString(z)).toBe('100/550');
  });

  test('list of levels', () => {
    const z: ZParameter = { type: 'list', levels: [10, 80, 200] };
    expect(zParameterToString(z)).toBe('10,80,200');
  });

  test('repeating interval', () => {
    const z: ZParameter = {
      type: 'repeating',
      repeat: 20,
      minLevel: 100,
      step: 50,
    };
    expect(zParameterToString(z)).toBe('R20/100/50');
  });
});
```

**Pattern components:**

1. **Explicit type annotation:** `const z: ZParameter = ...`
2. **TypeScript validates at compile time:** Wrong structure won't compile
3. **Jest validates runtime behavior:** Serialization correctness
4. **All union variants tested:** Each discriminated type gets test case

**ZParameter definition:**

```typescript
export type ZParameter =
  | { type: 'single'; level: number }
  | { type: 'interval'; minLevel: number; maxLevel: number }
  | { type: 'list'; levels: number[] }
  | { type: 'repeating'; repeat: number; minLevel: number; step: number };
```

This is the **most complex discriminated union** in upstream codebase.

#### Pattern 2: DateTime Parameter Testing (EDR)

**Source:** `src/ogc-api/edr/helpers.spec.ts`

```typescript
describe('DateTimeParameterToEDRString', () => {
  const toDate = (str: string) => new Date(str);

  it('serializes a plain Date', () => {
    const result = DateTimeParameterToEDRString(toDate('2025-01-01T00:00:00Z'));
    expect(result).toBe('2025-01-01T00:00:00.000Z');
  });

  it('serializes with only start', () => {
    const result = DateTimeParameterToEDRString({
      start: toDate('2025-01-01T00:00:00Z'),
    });
    expect(result).toBe('2025-01-01T00:00:00.000Z/..');
  });

  it('serializes with start and end', () => {
    const result = DateTimeParameterToEDRString({
      start: toDate('2025-01-01T00:00:00Z'),
      end: toDate('2025-12-31T23:59:59Z'),
    });
    expect(result).toBe('2025-01-01T00:00:00.000Z/2025-12-31T23:59:59.000Z');
  });

  it('throws if passed an invalid object', () => {
    expect(() =>
      DateTimeParameterToEDRString({} as DateTimeParameter)
    ).toThrow();
  });
});
```

**Pattern components:**

1. **Union type testing:** `Date | { start: Date, end?: Date }`
2. **Each variant tested:** Plain Date, start-only, start+end
3. **Error case tested:** Invalid structure throws
4. **Type annotation implicit:** TypeScript infers from function signature

**DateTimeParameter definition (from `src/shared/models.ts`):**

```typescript
export type DateTimeParameter = Date | { start: Date; end?: Date };
```

#### Pattern 3: Interface Compilation Testing

**Observed pattern:** Interfaces tested by usage, not explicit type tests.

```typescript
// From endpoint.spec.ts
it('can produce a EDR query builder', async () => {
  const builder = await endpoint.edr('reservoir-api');

  // TypeScript validates builder has correct type
  expect(builder).toBeTruthy();
  expect(builder.supported_queries).toEqual(
    new Set(['area', 'locations', 'cube'])
  );
});
```

**Pattern components:**

1. **No explicit interface test files**
2. **Interfaces validated by usage** in integration tests
3. **TypeScript compiler ensures correctness**
4. **Runtime tests validate behavior** (properties exist, correct values)

### Type Testing Anti-Patterns NOT Found

❌ **Not found:** `expectType<T>()` from tsd  
❌ **Not found:** `expectError()` from tsd  
❌ **Not found:** Type-only test files (e.g., `types.test-d.ts`)  
❌ **Not found:** Separate type compilation test suites  
❌ **Not found:** Type guard compilation tests

**Conclusion:** Upstream uses **implicit type testing** via TypeScript compilation, not explicit type assertion libraries.

### Upstream Type Testing Summary

| Category                 | Approach                     | Tool                | Example                 |
| ------------------------ | ---------------------------- | ------------------- | ----------------------- |
| **Interfaces**           | Compilation-only             | TypeScript compiler | N/A (compiles or fails) |
| **Discriminated unions** | Explicit type + runtime test | Jest + TypeScript   | ZParameter tests        |
| **Union types**          | Runtime behavior tests       | Jest + TypeScript   | DateTimeParameter tests |
| **Type aliases**         | Compilation-only             | TypeScript compiler | N/A                     |
| **Generics**             | Not applicable               | N/A                 | No complex generics     |
| **Type guards**          | Not tested                   | N/A                 | Not found in codebase   |

**Key insight:** Upstream trusts TypeScript compiler for type correctness, uses Jest for runtime behavior validation.

---

## 2. Type Testing Tools Evaluation

### Tool 1: tsd (TypeScript Definition Testing)

**Description:** Explicit type assertion library for testing TypeScript definitions.

**Features:**

```typescript
import { expectType, expectError, expectAssignable } from 'tsd';

// Assert exact type
const system: System = { ... };
expectType<System>(system);

// Assert method return type
const url = builder.buildGetSystemsUrl();
expectType<string>(url);

// Assert compilation errors
expectError(builder.buildGetSystemsUrl({ invalidParam: true }));

// Assert type assignability
const options: SystemQueryOptions = { limit: 10 };
expectAssignable<QueryOptions>(options);
```

**Pros:**

- ✅ Explicit type assertions in tests
- ✅ Tests type inference
- ✅ Tests generic constraints
- ✅ Catches type regressions
- ✅ Popular in TypeScript libraries (5.8M weekly downloads)

**Cons:**

- ❌ Additional dependency
- ❌ Separate test execution (not Jest)
- ❌ Learning curve
- ❌ Overkill for simple types
- ❌ Not used by upstream

**When to use:**

- Complex generic type constraints
- Type inference is critical to API usability
- Library with heavy TypeScript API consumers

**CSAPI applicability:** ⚠️ **Low** - No complex generics, simple types, not upstream pattern

### Tool 2: dtslint (TypeScript Definition Linter)

**Description:** Type definition testing tool from Microsoft DefinitelyTyped.

**Features:**

```typescript
// Uses special comments for assertions
const system: System = { ... };
// $ExpectType System

const url = builder.buildGetSystemsUrl();
// $ExpectType string

// Test compilation errors
builder.buildGetSystemsUrl({ invalidParam: true });
// $ExpectError
```

**Pros:**

- ✅ Microsoft-maintained
- ✅ Used by DefinitelyTyped (@types/\*)
- ✅ Tests type definitions at scale

**Cons:**

- ❌ Designed for .d.ts files (not .ts implementation)
- ❌ Comment-based syntax (not type-safe)
- ❌ Deprecated in favor of newer tools
- ❌ Not used by upstream
- ❌ Not suited for implementation testing

**When to use:**

- Publishing standalone .d.ts files
- Contributing to DefinitelyTyped
- Legacy type definition projects

**CSAPI applicability:** ❌ **None** - Not for implementation testing, deprecated

### Tool 3: TypeScript Compiler Only

**Description:** Rely on TypeScript compiler for type checking, Jest for runtime validation.

**Features:**

```typescript
// Compilation-based type testing
describe('System interface', () => {
  it('accepts valid system object', () => {
    const system: System = {
      id: 'sys-001',
      type: 'System',
      properties: {
        name: 'Temperature Sensor',
        systemType: 'sensor',
      },
      links: [],
    };

    // TypeScript validates structure at compile time
    expect(system.properties.name).toBe('Temperature Sensor');
    expect(system.properties.systemType).toBe('sensor');
  });

  it('accepts system with optional properties', () => {
    const system: System = {
      id: 'sys-001',
      type: 'System',
      properties: {
        name: 'Sensor',
        description: 'Optional description',
        keywords: ['temp', 'sensor'],
      },
      geometry: { type: 'Point', coordinates: [0, 0] },
      links: [],
    };

    expect(system.properties.description).toBe('Optional description');
    expect(system.geometry?.type).toBe('Point');
  });
});
```

**Pros:**

- ✅ Zero additional dependencies
- ✅ Matches upstream pattern
- ✅ TypeScript compiler = authoritative type checker
- ✅ Jest provides runtime validation
- ✅ Simple, maintainable
- ✅ Fast (no separate test runner)

**Cons:**

- ❌ Can't explicitly test type inference
- ❌ Can't test "this should NOT compile" scenarios
- ❌ No explicit type assertions

**When to use:**

- Simple type systems (interfaces, unions, aliases)
- No complex generic constraints
- Following established patterns

**CSAPI applicability:** ✅ **High** - Matches upstream, simple types, zero dependencies

### Tool 4: expect-type (Lightweight Type Testing)

**Description:** Lightweight type assertion library, compile-time only.

**Features:**

```typescript
import { expectTypeOf } from 'expect-type';

// Assert type equality
expectTypeOf<System>().toMatchTypeOf<{ id: string }>();

// Assert method return types
expectTypeOf(builder.buildGetSystemsUrl).returns.toBeString();

// Assert parameter types
expectTypeOf(builder.buildGetSystemsUrl)
  .parameter(0)
  .toMatchTypeOf<SystemQueryOptions>();
```

**Pros:**

- ✅ Compile-time only (no runtime overhead)
- ✅ TypeScript-native syntax
- ✅ Lighter than tsd

**Cons:**

- ❌ Additional dependency
- ❌ Less mature than tsd
- ❌ Not used by upstream

**When to use:**

- Want type assertions without runtime overhead
- Don't need tsd's full feature set

**CSAPI applicability:** ⚠️ **Medium** - Lighter alternative to tsd, but still not upstream pattern

### Tool Comparison Matrix

| Tool                         | Complexity | Dependencies | Upstream Match | CSAPI Fit | Recommendation     |
| ---------------------------- | ---------- | ------------ | -------------- | --------- | ------------------ |
| **TypeScript compiler only** | Low        | None         | ✅ Yes         | ✅ High   | ✅ **RECOMMENDED** |
| **tsd**                      | Medium     | tsd          | ❌ No          | ⚠️ Low    | ❌ Not needed      |
| **dtslint**                  | High       | dtslint      | ❌ No          | ❌ None   | ❌ Deprecated      |
| **expect-type**              | Low        | expect-type  | ❌ No          | ⚠️ Medium | ⚠️ Optional        |

### Recommendation: TypeScript Compiler Only

**Why:**

1. ✅ **Upstream pattern:** EDR successfully tests discriminated unions this way
2. ✅ **Zero dependencies:** No additional packages required
3. ✅ **Simple types:** CSAPI has mostly interfaces and simple unions
4. ✅ **No complex generics:** No generic constraints requiring specialized testing
5. ✅ **Industry standard:** Many TypeScript libraries follow this approach

**When to reconsider:**

- CSAPI adds complex generic type constraints
- Type inference becomes critical for API usability
- Type regressions become a recurring problem

**Current verdict:** TypeScript compiler + Jest is **sufficient** for CSAPI type testing.

---

## 3. CSAPI Type Inventory

### Type Categories

Based on TypeScript types analysis document and CSAPI specification:

#### Category 1: Resource Interfaces (9 types)

**Primary resources (GeoJSON structure):**

```typescript
export interface System {
  id: string;
  type: 'System';
  properties: SystemProperties;
  geometry?: Geometry;
  links: OgcApiDocumentLink[];
}

export interface Deployment { ... }
export interface SamplingFeature { ... }
export interface Procedure { ... }
export interface Datastream { ... }
export interface Observation { ... }
export interface Control { ... }
export interface ControlStream { ... }
export interface Command { ... }
```

**Testing requirements:**

- ✅ Compilation with required properties
- ✅ Compilation with optional properties
- ✅ Correct property types
- ✅ GeoJSON structure adherence

**Complexity:** Low-Medium (simple interfaces)

#### Category 2: Helper Interfaces (6 types)

**Supporting data structures:**

```typescript
export interface TimeInterval {
  start?: Date;
  end?: Date;
}

export interface Characteristic {
  name: string;
  description?: string;
  value: number | string | boolean;
  unit?: string;
}

export interface HistoryEvent {
  time: Date;
  description: string;
}

export interface UnitOfMeasurement {
  name: string;
  symbol: string;
  definition: string;
}

export interface SystemProperties { ... }
export interface DeploymentProperties { ... }
// ... one per resource
```

**Testing requirements:**

- ✅ Compilation with required properties
- ✅ Optional property handling
- ✅ Nested property types

**Complexity:** Low (simple interfaces)

#### Category 3: Query Options Interfaces (3 types)

**API query parameters:**

```typescript
export interface QueryOptions {
  limit?: number;
  offset?: number;
  bbox?: BoundingBox;
  datetime?: DateTimeParameter;
  properties?: string[];
  sortby?: string[];
}

export interface SystemQueryOptions extends QueryOptions {
  type?: 'sensor' | 'platform' | 'actuator';
}

export interface ObservationQueryOptions extends QueryOptions {
  observedProperty?: string[];
}
```

**Testing requirements:**

- ✅ Compilation with optional parameters
- ✅ Extended interface inheritance
- ✅ Optional property handling

**Complexity:** Low (simple interfaces)

#### Category 4: Union Types (5 types)

**Type aliases and string unions:**

```typescript
// Const assertion enum
export const CSAPIResourceTypes = [
  'System',
  'Deployment',
  'SamplingFeature',
  'Procedure',
  'Datastream',
  'Observation',
  'Control',
  'ControlStream',
  'Command',
] as const;

export type CSAPIResourceType = (typeof CSAPIResourceTypes)[number];

// String unions
export type SystemType = 'sensor' | 'platform' | 'actuator';

// Link union
export type ResourceLink = string | { href: string; title?: string };

// Temporal union (reused from shared)
// export type DateTimeParameter = Date | { start: Date; end?: Date };

// Value union
export type ResultValue = number | string | boolean | object;
```

**Testing requirements:**

- ✅ Each variant compiles
- ⚠️ Runtime discrimination (if needed)
- ✅ Type narrowing (optional)

**Complexity:** Low (simple unions, not discriminated)

#### Category 5: Collection Generics (2 types)

**Generic collection types:**

```typescript
export interface Collection<T> {
  type: 'FeatureCollection';
  features: T[];
  links: OgcApiDocumentLink[];
  numberMatched?: number;
  numberReturned: number;
  timeStamp: string;
}

// Type aliases for convenience
export type SystemCollection = Collection<System>;
export type DeploymentCollection = Collection<Deployment>;
// ... one per resource
```

**Testing requirements:**

- ✅ Generic type parameter works with all resource types
- ✅ Compilation with typed arrays

**Complexity:** Low (simple generic, no constraints)

#### Category 6: Reused Types (6 types)

**From `shared/models.ts` and `ogc-api/model.ts`:**

```typescript
// Already defined, imported by CSAPI
import {
  BoundingBox,
  DateTimeParameter,
  CrsCode,
  MimeType,
  Contact,
} from '../../shared/models.js';
import { OgcApiDocumentLink } from '../model.js';
```

**Testing requirements:**

- ❌ **Not tested in CSAPI** (tested in upstream)
- ✅ Only test CSAPI usage of these types

**Complexity:** N/A (upstream responsibility)

### Type Inventory Summary

| Category                | Count  | Lines        | Complexity     | Testing Priority |
| ----------------------- | ------ | ------------ | -------------- | ---------------- |
| **Resource interfaces** | 9      | ~250         | Low-Medium     | High             |
| **Helper interfaces**   | 6      | ~60          | Low            | Medium           |
| **Query options**       | 3      | ~30          | Low            | High             |
| **Union types**         | 5      | ~20          | Low            | Low              |
| **Collection generics** | 2      | ~30          | Low            | Medium           |
| **Reused types**        | 6      | 0 (upstream) | N/A            | Low              |
| **TOTAL**               | **31** | **~390**     | **Low-Medium** |                  |

### Type Complexity Assessment

**Simple interfaces (most types):**

- System, Deployment, Procedure, etc.
- QueryOptions, TimeInterval, Characteristic
- No nested discriminated unions
- No complex generic constraints
- Optional properties only

**No complex types requiring specialized testing:**

- ❌ No higher-kinded types
- ❌ No conditional types
- ❌ No mapped types with complex transformations
- ❌ No deep type recursion
- ❌ No complex generic constraints

**Conclusion:** CSAPI type system is **simple** compared to upstream EDR (which has discriminated unions). Standard compilation-based testing is **sufficient**.

---

## 4. Type Test Patterns

> **⚠️ REVIEW NOTICE (H4 — Core Section):** The 6 patterns below are all
> shape-assertion templates (AP4). Each constructs an object matching a
> TypeScript interface and asserts the values it just set. For example,
> Pattern 1 (Interface Compilation Testing) creates `const system: System = 
{ id: 'sys-001', ... }` then asserts `expect(system.id).toBe('sys-001')`.
>
> The TypeScript compiler already validates that the object literal conforms
> to the interface at compile time — no runtime test is needed. These patterns
> should be replaced with tests of _functions that operate on these types_:
> parsers that produce them, serializers that consume them, or type guards
> that discriminate them.
>
> **What to keep as reference:** The patterns document what each type looks
> like with all properties populated, which is useful for fixture design.
> **What NOT to implement:** The `expect(obj.prop).toBe(value)` assertions.

### Pattern 1: Interface Compilation Testing

**Purpose:** Validate interface compiles with required and optional properties.

**Template:**

```typescript
describe('[InterfaceName] interface', () => {
  it('compiles with required properties only', () => {
    const obj: [InterfaceName] = {
      // All required properties
      requiredProp1: value1,
      requiredProp2: value2,
    };

    // Runtime validation
    expect(obj.requiredProp1).toBe(value1);
    expect(obj.requiredProp2).toBe(value2);
  });

  it('compiles with all properties including optional', () => {
    const obj: [InterfaceName] = {
      // Required properties
      requiredProp1: value1,
      requiredProp2: value2,
      // Optional properties
      optionalProp1: value3,
      optionalProp2: value4,
    };

    // Runtime validation
    expect(obj.optionalProp1).toBe(value3);
    expect(obj.optionalProp2).toBe(value4);
  });

  it('handles optional properties as undefined', () => {
    const obj: [InterfaceName] = {
      requiredProp1: value1,
      requiredProp2: value2,
      // Optional properties omitted
    };

    expect(obj.optionalProp1).toBeUndefined();
    expect(obj.optionalProp2).toBeUndefined();
  });
});
```

**Example: System interface:**

```typescript
describe('System interface', () => {
  it('compiles with required properties only', () => {
    const system: System = {
      id: 'sys-001',
      type: 'System',
      properties: {
        name: 'Temperature Sensor',
      },
      links: [],
    };

    expect(system.id).toBe('sys-001');
    expect(system.type).toBe('System');
    expect(system.properties.name).toBe('Temperature Sensor');
  });

  it('compiles with all properties including optional', () => {
    const system: System = {
      id: 'sys-001',
      type: 'System',
      properties: {
        name: 'Temperature Sensor',
        description: 'Measures ambient temperature',
        systemType: 'sensor',
        keywords: ['temperature', 'sensor'],
        identifier: 'urn:example:sensor:001',
      },
      geometry: {
        type: 'Point',
        coordinates: [-122.4194, 37.7749],
      },
      links: [
        { rel: 'self', href: '/systems/sys-001', type: 'application/json' },
      ],
    };

    expect(system.properties.description).toBe('Measures ambient temperature');
    expect(system.properties.systemType).toBe('sensor');
    expect(system.geometry?.type).toBe('Point');
  });

  it('handles optional geometry as undefined', () => {
    const system: System = {
      id: 'sys-001',
      type: 'System',
      properties: { name: 'Sensor' },
      links: [],
    };

    expect(system.geometry).toBeUndefined();
  });
});
```

**When to use:** All resource interfaces, helper interfaces, query options.

### Pattern 2: Union Type Variant Testing

**Purpose:** Validate each union variant compiles and behaves correctly.

**Template:**

```typescript
describe('[UnionType] union type', () => {
  it('accepts variant 1', () => {
    const value: [UnionType] = variant1Value;

    // Runtime validation
    expect(value).toBe(variant1Value); // or more complex validation
  });

  it('accepts variant 2', () => {
    const value: [UnionType] = variant2Value;

    expect(value).toBe(variant2Value);
  });

  // ... one test per variant
});
```

**Example: ResourceLink union:**

```typescript
describe('ResourceLink union type', () => {
  it('accepts string href', () => {
    const link: ResourceLink = 'https://example.com/systems/sys-001';

    expect(typeof link).toBe('string');
    expect(link).toBe('https://example.com/systems/sys-001');
  });

  it('accepts object with href and title', () => {
    const link: ResourceLink = {
      href: 'https://example.com/systems/sys-001',
      title: 'Temperature Sensor',
    };

    expect(typeof link).toBe('object');
    expect(link.href).toBe('https://example.com/systems/sys-001');
    expect(link.title).toBe('Temperature Sensor');
  });

  it('accepts object with href only', () => {
    const link: ResourceLink = {
      href: 'https://example.com/systems/sys-001',
    };

    expect(link.href).toBe('https://example.com/systems/sys-001');
    expect(link.title).toBeUndefined();
  });
});
```

**Example: SystemType string union:**

```typescript
describe('SystemType union type', () => {
  it('accepts "sensor"', () => {
    const type: SystemType = 'sensor';
    expect(type).toBe('sensor');
  });

  it('accepts "platform"', () => {
    const type: SystemType = 'platform';
    expect(type).toBe('platform');
  });

  it('accepts "actuator"', () => {
    const type: SystemType = 'actuator';
    expect(type).toBe('actuator');
  });
});
```

**When to use:** Union types (ResourceLink, SystemType, ResultValue), DateTimeParameter variants.

### Pattern 3: Generic Type Testing

**Purpose:** Validate generic types work with different type parameters.

**Template:**

```typescript
describe('[GenericType]<T> generic type', () => {
  it('works with type parameter T1', () => {
    const obj: [GenericType]<T1> = {
      // Generic properties with T1
      items: [t1Value1, t1Value2],
    };

    expect(obj.items).toHaveLength(2);
    expect(obj.items[0]).toEqual(t1Value1);
  });

  it('works with type parameter T2', () => {
    const obj: [GenericType]<T2> = {
      // Generic properties with T2
      items: [t2Value1, t2Value2],
    };

    expect(obj.items).toHaveLength(2);
    expect(obj.items[0]).toEqual(t2Value1);
  });
});
```

**Example: Collection<T> generic:**

```typescript
describe('Collection<T> generic type', () => {
  it('works with System type parameter', () => {
    const collection: Collection<System> = {
      type: 'FeatureCollection',
      features: [
        {
          id: 'sys-001',
          type: 'System',
          properties: { name: 'Sensor 1' },
          links: [],
        },
        {
          id: 'sys-002',
          type: 'System',
          properties: { name: 'Sensor 2' },
          links: [],
        },
      ],
      links: [],
      numberReturned: 2,
      timeStamp: '2024-01-01T00:00:00Z',
    };

    expect(collection.type).toBe('FeatureCollection');
    expect(collection.features).toHaveLength(2);
    expect(collection.features[0].id).toBe('sys-001');
  });

  it('works with Deployment type parameter', () => {
    const collection: Collection<Deployment> = {
      type: 'FeatureCollection',
      features: [
        {
          id: 'dep-001',
          type: 'Deployment',
          properties: { name: 'Deployment 1' },
          links: [],
        },
      ],
      links: [],
      numberReturned: 1,
      timeStamp: '2024-01-01T00:00:00Z',
    };

    expect(collection.features[0].type).toBe('Deployment');
  });

  it('works with Observation type parameter', () => {
    const collection: Collection<Observation> = {
      type: 'FeatureCollection',
      features: [
        {
          id: 'obs-001',
          type: 'Observation',
          properties: {
            phenomenonTime: new Date('2024-01-01T00:00:00Z'),
            result: 23.5,
          },
          links: [],
        },
      ],
      links: [],
      numberReturned: 1,
      timeStamp: '2024-01-01T00:00:00Z',
    };

    expect(collection.features[0].properties.result).toBe(23.5);
  });
});
```

**When to use:** Collection<T> generic (only generic in CSAPI).

### Pattern 4: Extended Interface Testing

**Purpose:** Validate interface extension (inheritance) works correctly.

**Template:**

```typescript
describe('[ExtendedInterface] extends [BaseInterface]', () => {
  it('inherits properties from base interface', () => {
    const obj: [ExtendedInterface] = {
      // Base properties
      baseProp1: value1,
      baseProp2: value2,
      // Extended properties
      extendedProp1: value3,
    };

    // Validate base properties
    expect(obj.baseProp1).toBe(value1);
    expect(obj.baseProp2).toBe(value2);
    // Validate extended properties
    expect(obj.extendedProp1).toBe(value3);
  });

  it('is assignable to base interface', () => {
    const extended: [ExtendedInterface] = {
      baseProp1: value1,
      baseProp2: value2,
      extendedProp1: value3,
    };

    // Should be assignable to base
    const base: [BaseInterface] = extended;
    expect(base.baseProp1).toBe(value1);
  });
});
```

**Example: SystemQueryOptions extends QueryOptions:**

```typescript
describe('SystemQueryOptions extends QueryOptions', () => {
  it('inherits properties from QueryOptions', () => {
    const options: SystemQueryOptions = {
      // QueryOptions properties
      limit: 10,
      offset: 20,
      bbox: [-180, -90, 180, 90],
      datetime: new Date('2024-01-01T00:00:00Z'),
      // SystemQueryOptions properties
      type: 'sensor',
    };

    // Validate base properties
    expect(options.limit).toBe(10);
    expect(options.offset).toBe(20);
    expect(options.bbox).toEqual([-180, -90, 180, 90]);
    // Validate extended properties
    expect(options.type).toBe('sensor');
  });

  it('is assignable to QueryOptions', () => {
    const systemOptions: SystemQueryOptions = {
      limit: 10,
      type: 'sensor',
    };

    // Should be assignable to base
    const baseOptions: QueryOptions = systemOptions;
    expect(baseOptions.limit).toBe(10);
  });

  it('accepts all SystemType values', () => {
    const sensor: SystemQueryOptions = { type: 'sensor' };
    const platform: SystemQueryOptions = { type: 'platform' };
    const actuator: SystemQueryOptions = { type: 'actuator' };

    expect(sensor.type).toBe('sensor');
    expect(platform.type).toBe('platform');
    expect(actuator.type).toBe('actuator');
  });
});
```

**When to use:** SystemQueryOptions, ObservationQueryOptions (interfaces extending QueryOptions).

### Pattern 5: Nested Property Testing

**Purpose:** Validate deeply nested property structures compile correctly.

**Template:**

```typescript
describe('[Interface] nested properties', () => {
  it('compiles with nested required properties', () => {
    const obj: [Interface] = {
      topLevel: {
        nested: {
          deepNested: value,
        },
      },
    };

    expect(obj.topLevel.nested.deepNested).toBe(value);
  });

  it('handles optional nested properties', () => {
    const obj: [Interface] = {
      topLevel: {
        nested: {
          // Optional deep property omitted
        },
      },
    };

    expect(obj.topLevel.nested.optionalDeep).toBeUndefined();
  });
});
```

**Example: System with nested properties:**

```typescript
describe('System nested properties', () => {
  it('compiles with nested characteristics', () => {
    const system: System = {
      id: 'sys-001',
      type: 'System',
      properties: {
        name: 'Temperature Sensor',
        characteristics: [
          {
            name: 'Range',
            value: '0-100',
            unit: '°C',
            description: 'Operating temperature range',
          },
        ],
      },
      links: [],
    };

    expect(system.properties.characteristics?.[0].name).toBe('Range');
    expect(system.properties.characteristics?.[0].value).toBe('0-100');
    expect(system.properties.characteristics?.[0].unit).toBe('°C');
  });

  it('compiles with nested geometry coordinates', () => {
    const system: System = {
      id: 'sys-001',
      type: 'System',
      properties: { name: 'Sensor' },
      geometry: {
        type: 'Point',
        coordinates: [-122.4194, 37.7749],
      },
      links: [],
    };

    expect(system.geometry?.type).toBe('Point');
    expect(system.geometry?.coordinates).toEqual([-122.4194, 37.7749]);
  });
});
```

**When to use:** Resources with nested properties (System.characteristics, Datastream.unitOfMeasurement).

### Pattern 6: Optional Property Array Testing

**Purpose:** Validate optional array properties (undefined vs empty array).

**Template:**

```typescript
describe('[Interface] optional array properties', () => {
  it('compiles with populated array', () => {
    const obj: [Interface] = {
      requiredProp: value,
      optionalArray: [item1, item2],
    };

    expect(obj.optionalArray).toHaveLength(2);
  });

  it('compiles with empty array', () => {
    const obj: [Interface] = {
      requiredProp: value,
      optionalArray: [],
    };

    expect(obj.optionalArray).toHaveLength(0);
  });

  it('compiles with undefined array', () => {
    const obj: [Interface] = {
      requiredProp: value,
      // optionalArray omitted
    };

    expect(obj.optionalArray).toBeUndefined();
  });
});
```

**Example: System with optional keywords array:**

```typescript
describe('System optional array properties', () => {
  it('compiles with populated keywords array', () => {
    const system: System = {
      id: 'sys-001',
      type: 'System',
      properties: {
        name: 'Sensor',
        keywords: ['temperature', 'sensor', 'outdoor'],
      },
      links: [],
    };

    expect(system.properties.keywords).toHaveLength(3);
    expect(system.properties.keywords?.[0]).toBe('temperature');
  });

  it('compiles with empty keywords array', () => {
    const system: System = {
      id: 'sys-001',
      type: 'System',
      properties: {
        name: 'Sensor',
        keywords: [],
      },
      links: [],
    };

    expect(system.properties.keywords).toHaveLength(0);
  });

  it('compiles with undefined keywords', () => {
    const system: System = {
      id: 'sys-001',
      type: 'System',
      properties: { name: 'Sensor' },
      links: [],
    };

    expect(system.properties.keywords).toBeUndefined();
  });
});
```

**When to use:** Resources with optional array properties (keywords, contacts, history, characteristics).

### Test Pattern Summary

| Pattern                   | Purpose                         | When to Use               | Example                  |
| ------------------------- | ------------------------------- | ------------------------- | ------------------------ |
| **Interface compilation** | Validate interface structure    | All interfaces            | System, QueryOptions     |
| **Union variant**         | Test each union case            | Union types               | ResourceLink, SystemType |
| **Generic type**          | Test with different type params | Generic types             | Collection<T>            |
| **Extended interface**    | Validate inheritance            | Extending interfaces      | SystemQueryOptions       |
| **Nested properties**     | Deep structure validation       | Complex nested objects    | System.characteristics   |
| **Optional arrays**       | Undefined vs empty arrays       | Optional array properties | System.keywords          |

---

## 5. Runtime vs Compile-Time Strategy

### Compile-Time Type Testing (Primary)

**What TypeScript compiler validates:**

- ✅ Interface structure (required properties present)
- ✅ Property types (string, number, boolean, etc.)
- ✅ Optional property handling (? operator)
- ✅ Union type variants (all valid)
- ✅ Generic type parameters (correct usage)
- ✅ Interface extension (inheritance)
- ✅ Nested property structures

**How it works:**

```typescript
// TypeScript compiler validates this at compile time
const system: System = {
  id: 'sys-001',
  type: 'System',
  properties: { name: 'Sensor' },
  links: [],
};

// TypeScript compilation ERROR (caught before runtime):
// const invalid: System = {
//   id: 123,  // ❌ Type 'number' not assignable to 'string'
//   type: 'System',
//   properties: { name: 'Sensor' },
//   links: [],
// };
```

**When to use:**

- ✅ **All type definitions** (interfaces, unions, aliases)
- ✅ **Static structure validation**
- ✅ **Type correctness**

**Limitation:** Can't validate runtime behavior (serialization, external data parsing).

### Runtime Type Validation (Secondary)

**What needs runtime validation:**

- ⚠️ **External data parsing** (JSON responses from API)
- ⚠️ **Type discrimination** (identifying resource type at runtime)
- ⚠️ **Serialization/deserialization** (e.g., Date ↔ string)
- ⚠️ **Type guards** (narrowing union types)

**When to use runtime validation:**

#### Use Case 1: External Data Parsing

**Problem:** API returns JSON, need to validate it matches type.

**Solution:** Schema validation (Zod, Joi, or custom validators).

**Example:**

```typescript
// NOT type testing - this is integration testing
describe('parseSystemResponse', () => {
  it('parses valid system JSON', () => {
    const json = {
      id: 'sys-001',
      type: 'System',
      properties: { name: 'Sensor' },
      links: [],
    };

    const system = parseSystemResponse(json);

    expect(system.id).toBe('sys-001');
    expect(system.type).toBe('System');
    expect(system.properties.name).toBe('Sensor');
  });

  it('throws on invalid system JSON', () => {
    const invalid = {
      id: 'sys-001',
      // Missing type and properties
    };

    expect(() => parseSystemResponse(invalid)).toThrow();
  });
});
```

**This is NOT type testing** - it's **integration testing** (tested elsewhere).

#### Use Case 2: Type Guards

**Problem:** Need to narrow union types at runtime.

**Solution:** Type guard functions (optional for CSAPI).

**Example:**

```typescript
// Type guard definition
export function isSystem(resource: any): resource is System {
  return (
    resource &&
    typeof resource === 'object' &&
    resource.type === 'System' &&
    typeof resource.id === 'string'
  );
}

// Type guard tests (if implemented)
describe('isSystem type guard', () => {
  it('returns true for valid System', () => {
    const system: System = {
      id: 'sys-001',
      type: 'System',
      properties: { name: 'Sensor' },
      links: [],
    };

    expect(isSystem(system)).toBe(true);
  });

  it('returns false for Deployment', () => {
    const deployment: Deployment = {
      id: 'dep-001',
      type: 'Deployment',
      properties: { name: 'Deploy' },
      links: [],
    };

    expect(isSystem(deployment)).toBe(false);
  });

  it('returns false for invalid object', () => {
    expect(isSystem({})).toBe(false);
    expect(isSystem(null)).toBe(false);
    expect(isSystem('string')).toBe(false);
  });
});
```

**Decision for CSAPI:** Type guards are **optional** (only if needed for mixed response types).

#### Use Case 3: Serialization Helpers

**Problem:** Need to serialize/deserialize complex types (e.g., Date ↔ string).

**Solution:** Test serialization functions (like upstream DateTimeParameterToEDRString).

**Example:**

```typescript
// Serialization helper (if needed)
export function serializeDateTimeParameter(dt: DateTimeParameter): string {
  if (dt instanceof Date) {
    return dt.toISOString();
  } else if (dt.start && dt.end) {
    return `${dt.start.toISOString()}/${dt.end.toISOString()}`;
  } else if (dt.start) {
    return `${dt.start.toISOString()}/..`;
  } else {
    throw new Error('Invalid DateTimeParameter');
  }
}

// Serialization tests
describe('serializeDateTimeParameter', () => {
  it('serializes plain Date', () => {
    const date = new Date('2024-01-01T00:00:00Z');
    expect(serializeDateTimeParameter(date)).toBe('2024-01-01T00:00:00.000Z');
  });

  it('serializes start-only interval', () => {
    const interval = { start: new Date('2024-01-01T00:00:00Z') };
    expect(serializeDateTimeParameter(interval)).toBe(
      '2024-01-01T00:00:00.000Z/..'
    );
  });

  it('serializes start/end interval', () => {
    const interval = {
      start: new Date('2024-01-01T00:00:00Z'),
      end: new Date('2024-12-31T23:59:59Z'),
    };
    expect(serializeDateTimeParameter(interval)).toBe(
      '2024-01-01T00:00:00.000Z/2024-12-31T23:59:59.000Z'
    );
  });
});
```

**Decision for CSAPI:** Only if custom serialization is needed (DateTimeParameter reused from shared).

### Strategy Decision Matrix

| Scenario                  | Compile-Time | Runtime            | Testing Location         |
| ------------------------- | ------------ | ------------------ | ------------------------ |
| **Interface structure**   | ✅ Yes       | ❌ No              | Type tests (compilation) |
| **Property types**        | ✅ Yes       | ❌ No              | Type tests (compilation) |
| **Optional properties**   | ✅ Yes       | ❌ No              | Type tests (compilation) |
| **Union variants**        | ✅ Yes       | ❌ No              | Type tests (compilation) |
| **Generic types**         | ✅ Yes       | ❌ No              | Type tests (compilation) |
| **External data parsing** | ❌ No        | ✅ Yes             | Integration tests        |
| **Type guards**           | ❌ No        | ✅ Yes (optional)  | Type guard tests         |
| **Serialization**         | ❌ No        | ✅ Yes (if needed) | Helper tests             |

### CSAPI Runtime Validation Assessment

**Required runtime validation:**

- ❌ **None** - CSAPI uses standard types (no custom serialization)
- ❌ **No type guards** needed (response type known from endpoint)
- ❌ **No custom parsing** (JSON.parse handles standard types)

**Optional runtime validation:**

- ⚠️ **Type guards** (only if mixed response types become common)
- ⚠️ **Schema validation** (only if external data validation required)

**Conclusion:** CSAPI needs **minimal runtime validation** - primarily compile-time type testing.

---

## 6. Implementation Templates

### Template 1: Resource Interface Test File

> **⚠️ REVIEW NOTICE (H4 — Core Template):** This ~250-line `model.spec.ts`
> template consists entirely of shape-assertion tests. Every test constructs
> an object literal with an explicit type annotation, then asserts each
> property equals the value assigned on the previous line. For example:
>
> ```typescript
> const system: System = { id: 'sys-001', ... };
> expect(system.id).toBe('sys-001'); // tests nothing
> ```
>
> The TypeScript compiler already validates that `{ id: 'sys-001', ... }`
> conforms to the `System` interface. The runtime assertion adds zero value.
>
> **Do NOT implement this template.** Instead, test functions that consume
> or produce these types: parser output verification, QueryBuilder parameter
> handling, type guard discrimination. The document's own Section 5 correctly
> concludes "CSAPI needs minimal runtime validation."
>
> Templates 2 (type guards) and 3 (QueryBuilder integration) below are
> directly usable — they test actual runtime behavior.

**File:** `src/ogc-api/csapi/model.spec.ts`

```typescript
import {
  System,
  Deployment,
  SamplingFeature,
  Procedure,
  Datastream,
  Observation,
  ControlStream,
  Command,
  SystemQueryOptions,
  ObservationQueryOptions,
  Collection,
  TimeInterval,
  ResourceLink,
} from './model.js';

describe('CSAPI Type Definitions', () => {
  //═══════════════════════════════════════════════════════════
  // Resource Interfaces
  //═══════════════════════════════════════════════════════════

  describe('System interface', () => {
    it('compiles with required properties only', () => {
      const system: System = {
        id: 'sys-001',
        type: 'System',
        properties: {
          name: 'Temperature Sensor',
        },
        links: [],
      };

      expect(system.id).toBe('sys-001');
      expect(system.type).toBe('System');
      expect(system.properties.name).toBe('Temperature Sensor');
    });

    it('compiles with all optional properties', () => {
      const system: System = {
        id: 'sys-001',
        type: 'System',
        properties: {
          name: 'Temperature Sensor',
          description: 'Measures ambient temperature',
          systemType: 'sensor',
          keywords: ['temperature', 'sensor'],
          identifier: 'urn:example:sensor:001',
          characteristics: [
            {
              name: 'Range',
              value: '0-100',
              unit: '°C',
            },
          ],
        },
        geometry: {
          type: 'Point',
          coordinates: [-122.4194, 37.7749],
        },
        links: [
          { rel: 'self', href: '/systems/sys-001', type: 'application/json' },
        ],
      };

      expect(system.properties.description).toBe(
        'Measures ambient temperature'
      );
      expect(system.properties.systemType).toBe('sensor');
      expect(system.geometry?.type).toBe('Point');
    });

    it('handles optional geometry as undefined', () => {
      const system: System = {
        id: 'sys-001',
        type: 'System',
        properties: { name: 'Sensor' },
        links: [],
      };

      expect(system.geometry).toBeUndefined();
    });
  });

  describe('Deployment interface', () => {
    it('compiles with required properties', () => {
      const deployment: Deployment = {
        id: 'dep-001',
        type: 'Deployment',
        properties: {
          name: 'Coastal Deployment',
        },
        links: [],
      };

      expect(deployment.id).toBe('dep-001');
      expect(deployment.type).toBe('Deployment');
    });

    it('compiles with optional deployed systems', () => {
      const deployment: Deployment = {
        id: 'dep-001',
        type: 'Deployment',
        properties: {
          name: 'Deployment',
          deployedSystems: [
            'sys-001',
            { href: '/systems/sys-002', title: 'Sensor 2' },
          ],
        },
        links: [],
      };

      expect(deployment.properties.deployedSystems).toHaveLength(2);
    });
  });

  describe('Observation interface', () => {
    it('compiles with numeric result', () => {
      const observation: Observation = {
        id: 'obs-001',
        type: 'Observation',
        properties: {
          phenomenonTime: new Date('2024-01-01T00:00:00Z'),
          result: 23.5,
        },
        links: [],
      };

      expect(observation.properties.result).toBe(23.5);
    });

    it('compiles with string result', () => {
      const observation: Observation = {
        id: 'obs-002',
        type: 'Observation',
        properties: {
          phenomenonTime: new Date('2024-01-01T00:00:00Z'),
          result: 'clear',
        },
        links: [],
      };

      expect(observation.properties.result).toBe('clear');
    });
  });

  // ... Similar tests for Procedure, Datastream, SamplingFeature, Control, ControlStream, Command
  //
  // ⚠️ A1 FINDING C1-M2: The following 5 resource interfaces were previously
  // represented only by this placeholder comment. Explicit shape examples are
  // now provided below for fixture design reference. Per the H4 review notice
  // above, do NOT implement the expect() assertions — they are AP4. The
  // TypeScript compiler validates shape conformance at compile time.
  //

  describe('Procedure interface', () => {
    it('compiles with required properties only', () => {
      const procedure: Procedure = {
        id: 'proc-001',
        type: 'Procedure',
        properties: {
          name: 'Temperature Measurement Method',
        },
        links: [],
      };

      expect(procedure.id).toBe('proc-001');
      expect(procedure.type).toBe('Procedure');
    });

    it('compiles with all optional properties', () => {
      const procedure: Procedure = {
        id: 'proc-001',
        type: 'Procedure',
        properties: {
          name: 'Temperature Measurement Method',
          description: 'Standard thermometer reading procedure',
          procedureType: 'urn:ogc:def:procedure:OGC::measurement',
          identifier: 'urn:example:procedure:temp-measure',
        },
        links: [
          {
            rel: 'self',
            href: '/procedures/proc-001',
            type: 'application/json',
          },
        ],
      };

      expect(procedure.properties.description).toBe(
        'Standard thermometer reading procedure'
      );
      expect(procedure.properties.procedureType).toBe(
        'urn:ogc:def:procedure:OGC::measurement'
      );
    });
  });

  describe('SamplingFeature interface', () => {
    it('compiles with required properties only', () => {
      const sf: SamplingFeature = {
        id: 'sf-001',
        type: 'SamplingFeature',
        properties: {
          name: 'Weather Station Site',
          sampledFeature: 'urn:example:feature:atmosphere',
        },
        geometry: {
          type: 'Point',
          coordinates: [-122.4194, 37.7749],
        },
        links: [],
      };

      expect(sf.id).toBe('sf-001');
      expect(sf.properties.sampledFeature).toBe(
        'urn:example:feature:atmosphere'
      );
    });

    it('compiles with polygon geometry', () => {
      const sf: SamplingFeature = {
        id: 'sf-002',
        type: 'SamplingFeature',
        properties: {
          name: 'Forest Monitoring Plot',
          sampledFeature: 'urn:example:feature:forest',
          description: '100m x 100m monitoring plot',
        },
        geometry: {
          type: 'Polygon',
          coordinates: [
            [
              [-122.42, 37.77],
              [-122.41, 37.77],
              [-122.41, 37.78],
              [-122.42, 37.78],
              [-122.42, 37.77],
            ],
          ],
        },
        links: [],
      };

      expect(sf.geometry.type).toBe('Polygon');
    });
  });

  describe('Datastream interface', () => {
    it('compiles with required properties only', () => {
      const ds: Datastream = {
        id: 'ds-001',
        type: 'DataStream',
        properties: {
          name: 'Temperature Readings',
          observedProperty: 'urn:ogc:def:property:OGC::Temperature',
        },
        links: [],
      };

      expect(ds.id).toBe('ds-001');
      expect(ds.type).toBe('DataStream');
    });

    it('compiles with schema and format options', () => {
      const ds: Datastream = {
        id: 'ds-001',
        type: 'DataStream',
        properties: {
          name: 'Temperature Readings',
          observedProperty: 'urn:ogc:def:property:OGC::Temperature',
          description: 'Ambient temperature from station sensor',
          observationFormat: 'application/swe+json',
          resultSchema: {
            type: 'DataRecord',
            fields: [
              { name: 'time', type: 'Time' },
              { name: 'temperature', type: 'Quantity', uom: { code: 'Cel' } },
            ],
          },
        },
        links: [
          { rel: 'observations', href: '/datastreams/ds-001/observations' },
        ],
      };

      expect(ds.properties.observationFormat).toBe('application/swe+json');
      expect(ds.properties.resultSchema?.type).toBe('DataRecord');
    });
  });

  describe('ControlStream interface', () => {
    it('compiles with required properties only', () => {
      const cs: ControlStream = {
        id: 'cs-001',
        type: 'ControlStream',
        properties: {
          name: 'Valve Control Channel',
          controlledProperty: 'urn:ogc:def:property:OGC::ValvePosition',
        },
        links: [],
      };

      expect(cs.id).toBe('cs-001');
      expect(cs.type).toBe('ControlStream');
    });

    it('compiles with parameter schema', () => {
      const cs: ControlStream = {
        id: 'cs-001',
        type: 'ControlStream',
        properties: {
          name: 'Valve Control Channel',
          controlledProperty: 'urn:ogc:def:property:OGC::ValvePosition',
          description: 'Controls main intake valve',
          commandFormat: 'application/swe+json',
          parameterSchema: {
            type: 'DataRecord',
            fields: [
              { name: 'position', type: 'Quantity', uom: { code: '%' } },
            ],
          },
        },
        links: [{ rel: 'commands', href: '/controlstreams/cs-001/commands' }],
      };

      expect(cs.properties.commandFormat).toBe('application/swe+json');
      expect(cs.properties.parameterSchema?.type).toBe('DataRecord');
    });
  });

  describe('Command interface', () => {
    it('compiles with required properties only', () => {
      const cmd: Command = {
        id: 'cmd-001',
        type: 'Command',
        properties: {
          issueTime: new Date('2024-06-15T10:00:00Z'),
          parameters: { position: 75 },
        },
        links: [],
      };

      expect(cmd.id).toBe('cmd-001');
      expect(cmd.type).toBe('Command');
    });

    it('compiles with status and execution time', () => {
      const cmd: Command = {
        id: 'cmd-001',
        type: 'Command',
        properties: {
          issueTime: new Date('2024-06-15T10:00:00Z'),
          executionTime: new Date('2024-06-15T10:00:05Z'),
          parameters: { position: 75, speed: 'slow' },
          status: 'COMPLETED',
        },
        links: [
          { rel: 'status', href: '/commands/cmd-001/status' },
          { rel: 'result', href: '/commands/cmd-001/result' },
        ],
      };

      expect(cmd.properties.status).toBe('COMPLETED');
      expect(cmd.properties.executionTime).toBeInstanceOf(Date);
    });

    it('compiles with pending async command', () => {
      const cmd: Command = {
        id: 'cmd-002',
        type: 'Command',
        properties: {
          issueTime: new Date('2024-06-15T10:00:00Z'),
          parameters: { position: 100 },
          status: 'PENDING',
        },
        links: [{ rel: 'status', href: '/commands/cmd-002/status' }],
      };

      expect(cmd.properties.status).toBe('PENDING');
      expect(cmd.properties.executionTime).toBeUndefined();
    });
  });

  //═══════════════════════════════════════════════════════════
  // Query Options
  //═══════════════════════════════════════════════════════════

  describe('QueryOptions interface', () => {
    it('compiles with all optional parameters', () => {
      const options: QueryOptions = {
        limit: 10,
        offset: 20,
        bbox: [-180, -90, 180, 90],
        datetime: new Date('2024-01-01T00:00:00Z'),
        properties: ['name', 'description'],
        sortby: ['name', '-updated'],
      };

      expect(options.limit).toBe(10);
      expect(options.bbox).toEqual([-180, -90, 180, 90]);
    });

    it('compiles with subset of parameters', () => {
      const options: QueryOptions = {
        limit: 10,
      };

      expect(options.limit).toBe(10);
      expect(options.offset).toBeUndefined();
    });
  });

  describe('SystemQueryOptions extends QueryOptions', () => {
    it('inherits QueryOptions properties', () => {
      const options: SystemQueryOptions = {
        limit: 10,
        type: 'sensor',
      };

      expect(options.limit).toBe(10);
      expect(options.type).toBe('sensor');
    });

    it('is assignable to QueryOptions', () => {
      const systemOptions: SystemQueryOptions = {
        limit: 10,
        type: 'sensor',
      };

      const baseOptions: QueryOptions = systemOptions;
      expect(baseOptions.limit).toBe(10);
    });
  });

  //═══════════════════════════════════════════════════════════
  // Union Types
  //═══════════════════════════════════════════════════════════

  describe('ResourceLink union type', () => {
    it('accepts string href', () => {
      const link: ResourceLink = 'https://example.com/systems/sys-001';

      expect(typeof link).toBe('string');
    });

    it('accepts object with href', () => {
      const link: ResourceLink = {
        href: 'https://example.com/systems/sys-001',
        title: 'Temperature Sensor',
      };

      expect(link.href).toBe('https://example.com/systems/sys-001');
    });
  });

  //═══════════════════════════════════════════════════════════
  // Generic Types
  //═══════════════════════════════════════════════════════════

  describe('Collection<T> generic type', () => {
    it('works with System type parameter', () => {
      const collection: Collection<System> = {
        type: 'FeatureCollection',
        features: [
          {
            id: 'sys-001',
            type: 'System',
            properties: { name: 'Sensor 1' },
            links: [],
          },
        ],
        links: [],
        numberReturned: 1,
        timeStamp: '2024-01-01T00:00:00Z',
      };

      expect(collection.features[0].type).toBe('System');
    });

    it('works with Deployment type parameter', () => {
      const collection: Collection<Deployment> = {
        type: 'FeatureCollection',
        features: [
          {
            id: 'dep-001',
            type: 'Deployment',
            properties: { name: 'Deploy 1' },
            links: [],
          },
        ],
        links: [],
        numberReturned: 1,
        timeStamp: '2024-01-01T00:00:00Z',
      };

      expect(collection.features[0].type).toBe('Deployment');
    });
  });

  //═══════════════════════════════════════════════════════════
  // Helper Types
  //═══════════════════════════════════════════════════════════

  describe('TimeInterval interface', () => {
    it('compiles with both start and end', () => {
      const interval: TimeInterval = {
        start: new Date('2024-01-01T00:00:00Z'),
        end: new Date('2024-12-31T23:59:59Z'),
      };

      expect(interval.start).toBeInstanceOf(Date);
      expect(interval.end).toBeInstanceOf(Date);
    });

    it('compiles with start only', () => {
      const interval: TimeInterval = {
        start: new Date('2024-01-01T00:00:00Z'),
      };

      expect(interval.start).toBeInstanceOf(Date);
      expect(interval.end).toBeUndefined();
    });

    it('compiles with empty object', () => {
      const interval: TimeInterval = {};

      expect(interval.start).toBeUndefined();
      expect(interval.end).toBeUndefined();
    });
  });
});
```

**Test count:** ~30-40 tests (3-5 per resource, 2-3 per helper type)

**Estimated size:** ~400-500 lines

### Template 2: Type Guard Test File (Optional)

**File:** `src/ogc-api/csapi/guards.spec.ts`

```typescript
import {
  isSystem,
  isDeployment,
  isObservation,
  // ... other guards
} from './guards.js';
import type { System, Deployment, Observation } from './model.js';

describe('Type Guards', () => {
  describe('isSystem', () => {
    it('returns true for valid System', () => {
      const system: System = {
        id: 'sys-001',
        type: 'System',
        properties: { name: 'Sensor' },
        links: [],
      };

      expect(isSystem(system)).toBe(true);
    });

    it('returns false for Deployment', () => {
      const deployment: Deployment = {
        id: 'dep-001',
        type: 'Deployment',
        properties: { name: 'Deploy' },
        links: [],
      };

      expect(isSystem(deployment)).toBe(false);
    });

    it('returns false for invalid objects', () => {
      expect(isSystem({})).toBe(false);
      expect(isSystem(null)).toBe(false);
      expect(isSystem('string')).toBe(false);
      expect(isSystem({ type: 'System' })).toBe(false); // Missing id
    });
  });

  // Similar tests for other guards
});
```

**Decision:** Only implement if type guards are needed (optional for CSAPI).

### Template 3: Integration with Existing Tests

**Location:** Add type tests to existing QueryBuilder test files.

**Example:** `src/ogc-api/csapi/systems-builder.spec.ts`

```typescript
describe('SystemsQueryBuilder', () => {
  // Existing URL construction tests...

  describe('type safety', () => {
    it('accepts valid SystemQueryOptions', () => {
      const builder = new SystemsQueryBuilder('https://example.com');

      const options: SystemQueryOptions = {
        limit: 10,
        type: 'sensor',
      };

      const url = builder.buildGetSystemsUrl(options);
      expect(url).toContain('limit=10');
      expect(url).toContain('type=sensor');
    });

    it('accepts base QueryOptions', () => {
      const builder = new SystemsQueryBuilder('https://example.com');

      const options: QueryOptions = {
        limit: 10,
        offset: 20,
      };

      const url = builder.buildGetSystemsUrl(options);
      expect(url).toContain('limit=10');
    });
  });
});
```

**Integration approach:** Add type safety test suites to existing QueryBuilder test files.

---

## 7. Recommendations

### Primary Recommendation: TypeScript Compiler Only

**Adopt upstream pattern:** Jest + TypeScript compiler, NO specialized type testing tools.

**Implementation steps:**

1. **Create type test file:** `src/ogc-api/csapi/model.spec.ts`

   - Test all resource interfaces (System, Deployment, etc.)
   - Test query options interfaces
   - Test union types (ResourceLink, SystemType)
   - Test generic types (Collection<T>)
   - Test helper types (TimeInterval, Characteristic)

2. **Add type safety tests to QueryBuilder tests:**

   - Test SystemQueryOptions in systems-builder.spec.ts
   - Test ObservationQueryOptions in observations-builder.spec.ts
   - Validate type annotations compile correctly

3. **No type guards needed initially:**

   - Response type known from endpoint
   - No mixed resource type responses
   - Can add later if needed

4. **No custom serialization tests needed:**
   - Reuse DateTimeParameter from shared
   - Standard JSON serialization
   - No complex type transformations

**Effort estimate:** ~4-6 hours (see Section 8)

### Optional Enhancement: Type Guards

**Add if needed for:**

- Mixed resource type responses
- Runtime type discrimination
- Dynamic response parsing

**Implementation:**

```typescript
// File: src/ogc-api/csapi/guards.ts
export function isSystem(resource: any): resource is System {
  return (
    resource &&
    typeof resource === 'object' &&
    resource.type === 'System' &&
    typeof resource.id === 'string'
  );
}

// File: src/ogc-api/csapi/guards.spec.ts
describe('isSystem', () => {
  it('returns true for valid System', () => { ... });
  it('returns false for Deployment', () => { ... });
});
```

**Effort estimate:** +2-3 hours (if implemented)

### Not Recommended: Specialized Type Testing Tools

**Do NOT add:**

- ❌ tsd
- ❌ dtslint
- ❌ expect-type

**Rationale:**

1. Not used by upstream
2. CSAPI types are simple (no complex generics)
3. Additional dependencies and configuration
4. Learning curve for maintainers
5. TypeScript compiler already provides type checking

**Reconsider if:**

- CSAPI adds complex generic type constraints
- Type inference becomes critical for API usability
- Type regressions become recurring problem

### Testing Strategy Summary

| Type Category           | Testing Approach      | Tool              | Location       |
| ----------------------- | --------------------- | ----------------- | -------------- |
| **Resource interfaces** | Compilation + runtime | TypeScript + Jest | model.spec.ts  |
| **Query options**       | Compilation + runtime | TypeScript + Jest | model.spec.ts  |
| **Union types**         | Compilation + runtime | TypeScript + Jest | model.spec.ts  |
| **Generic types**       | Compilation + runtime | TypeScript + Jest | model.spec.ts  |
| **Helper types**        | Compilation + runtime | TypeScript + Jest | model.spec.ts  |
| **Type guards**         | Runtime (optional)    | Jest              | guards.spec.ts |

---

## 8. Implementation Estimates

> **⚠️ REVIEW NOTICE (L1):** The estimates below allocate ~6 hours to
> implement the shape-assertion `model.spec.ts` template that H4 identifies
> as zero-value. The document's own Section 5 correctly concludes that
> compilation-only testing is sufficient for CSAPI's simple type system.
>
> **Revised estimate:** If no `model.spec.ts` shape assertions are written,
> the real effort is:
>
> - **Compile-time validation:** 0 hours (types compile = types work, verified
>   by existing `tsc` in CI)
> - **Type guard tests** (if guards are implemented): ~1 hour
> - **QueryBuilder integration tests** (Template 3): ~2 hours
> - **Total: ~1-3 hours** depending on whether type guards are needed,
>   saving 3-5 hours vs the original estimate.

### Type Test Implementation Breakdown

#### Task 1: Create model.spec.ts

**Subtasks:**

1. Set up test file structure (5 minutes)
2. Write resource interface tests (9 resources × 15 minutes = 135 minutes)
   - System, Deployment, SamplingFeature, Procedure, Datastream, Observation, ControlStream, Command
   - Required properties test
   - Optional properties test
   - Optional undefined test
3. Write query options tests (3 interfaces × 10 minutes = 30 minutes)
   - QueryOptions, SystemQueryOptions, ObservationQueryOptions
4. Write union type tests (5 unions × 5 minutes = 25 minutes)
   - ResourceLink, SystemType, ResultValue, CSAPIResourceType
5. Write generic type tests (Collection<T>, 2 variants × 5 minutes = 10 minutes)
6. Write helper type tests (6 helpers × 5 minutes = 30 minutes)
   - TimeInterval, Characteristic, HistoryEvent, UnitOfMeasurement, etc.

**Total:** ~4 hours (240 minutes)

**Lines of code:** ~400-500 lines

#### Task 2: Integrate Type Tests with QueryBuilder Tests

**Subtasks:**

1. Add type safety suite to systems-builder.spec.ts (15 minutes)
2. Add type safety suite to deployments-builder.spec.ts (15 minutes)
3. Add type safety suite to observations-builder.spec.ts (15 minutes)
4. Add type safety suite to other builders (6 × 10 minutes = 60 minutes)

**Total:** ~2 hours (105 minutes)

**Lines of code:** ~100-150 lines (20-25 per builder)

#### Task 3: Optional Type Guards (If Needed)

**Subtasks:**

1. Create guards.ts (9 guards × 5 minutes = 45 minutes)
2. Create guards.spec.ts (9 guards × 10 minutes = 90 minutes)

**Total:** ~2.5 hours (135 minutes)

**Lines of code:** ~200-250 lines

### Total Implementation Estimate

**Required tasks:**

- Task 1: model.spec.ts = 4 hours
- Task 2: QueryBuilder integration = 2 hours
- **TOTAL: 6 hours**

**Optional tasks:**

- Task 3: Type guards = +2.5 hours
- **TOTAL WITH GUARDS: 8.5 hours**

### Maintenance Estimate

**Per new resource type:**

- Interface tests: 15 minutes
- QueryBuilder integration: 10 minutes
- Type guard (optional): 15 minutes

**Per new helper type:**

- Interface tests: 5 minutes

**Per new query option:**

- Interface tests: 10 minutes

### Timeline

**Phase 1: Core type tests** (6 hours)

- Day 1: model.spec.ts resource interfaces (4 hours)
- Day 2: model.spec.ts helpers + QueryBuilder integration (2 hours)

**Phase 2: Optional guards** (2.5 hours, if needed)

- Day 3: Type guards implementation and tests (2.5 hours)

**Total:** 1-2 days of focused work

---

## Conclusion

### Key Findings

1. **Upstream uses compilation-based type testing:** No tsd/dtslint found
2. **Discriminated unions tested with explicit type annotations:** EDR ZParameter pattern
3. **CSAPI types are simpler than EDR:** Fewer discriminated unions, no complex generics
4. **TypeScript compiler is sufficient:** No need for specialized tools
5. **Runtime validation minimal:** No custom serialization, reuse shared types

### Recommended Approach

**Primary strategy:**

- ✅ Jest + TypeScript compiler (upstream pattern)
- ✅ Explicit type annotations in tests
- ✅ Compilation validates type correctness
- ✅ Runtime tests validate behavior
- ✅ One test file: model.spec.ts (~400-500 lines)

**Optional enhancements:**

- ⚠️ Type guards (only if mixed responses)
- ⚠️ Custom serialization tests (only if needed)

**Not recommended:**

- ❌ tsd or dtslint (not needed for CSAPI)

### Implementation Priority

**High priority:**

- Resource interface tests (System, Deployment, etc.)
- Query options tests (SystemQueryOptions, etc.)

**Medium priority:**

- Generic type tests (Collection<T>)
- Helper type tests (TimeInterval, etc.)

**Low priority:**

- Union type tests (simple string unions)
- Type guards (optional, only if needed)

### Success Criteria

✅ All CSAPI type definitions have compilation tests  
✅ All resource interfaces tested (9 resources)  
✅ All query options tested (3 interfaces)  
✅ Generic Collection<T> tested with 2+ type parameters  
✅ Pattern matches upstream (EDR model.spec.ts)  
✅ Zero additional dependencies  
✅ Tests execute in <1 second

---

**Research Complete:** 2026-02-08 — Review notices added (Phase 2D issues H4, L1)  
**Next Steps:** Create model.spec.ts and integrate type tests with QueryBuilder tests.
