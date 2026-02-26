# Section 33: Performance and Efficiency Testing Strategy

**Research Plan:** [Research Plan 33: Performance and Efficiency Testing](../research-plans/33-performance-efficiency-testing.md)

**Research Questions:** 6 core questions about performance benchmarks, parser performance, large datasets, memory usage, Worker performance, and performance regression tests.

**Methodology:** 6-phase systematic analysis (Phase 1: Performance Requirements Analysis → Phase 2: Benchmark Scenario Design → Phase 3: Upstream Performance Testing Analysis → Phase 4: Measurement Strategy Design → Phase 5: Test Infrastructure Design → Phase 6: Synthesis)

**Research Time:** 90 minutes – February 6, 2026

**Primary Source(s):**

- [Implementation Guide](../../../planning/csapi-implementation-guide.md)
- [SWE Common 3.0 Specification](https://docs.ogc.org/is/24-014/24-014.html)
- Section 16: Worker testing strategy
- Section 10: SWE Common testing specification

**Supporting Resources:**

- Section 30: [Bulk Operations Testing](30-bulk-operations-testing.md) (large batch performance)
- Section 23: [Pagination Testing](23-pagination-testing.md) (large collection performance)
- Browser performance APIs (Performance API, Memory API)

**Document Purpose:** Performance testing strategy specification for parsers and large datasets (REFERENCE ONLY - performance testing is NOT in scope for this project, matching upstream's zero-performance-test approach).

---

# ⚠️ PERFORMANCE TESTING IS NOT IN SCOPE ⚠️

## IMPORTANT DECISION: NO PERFORMANCE TESTING WILL BE IMPLEMENTED

**This document is for REFERENCE ONLY.**

**FIRM RULE:** Performance testing will **NOT** be implemented for this project.

**Rationale:**

- Upstream `ogc-client` has **ZERO** performance tests
- We are matching upstream's testing approach
- Performance testing adds significant complexity (46-64 hours estimated effort)
- Performance testing requires specialized infrastructure (baseline tracking, statistical analysis, profiling)
- Functional correctness is the priority - performance is secondary
- If performance issues arise in production, they can be addressed reactively

**What This Means:**

- ❌ NO parser performance benchmarks will be created
- ❌ NO memory usage tests will be implemented
- ❌ NO Worker performance tests will be created
- ❌ NO API performance tests will be implemented
- ❌ NO performance regression detection in CI/CD
- ❌ NO baseline establishment or tracking
- ❌ NO statistical performance analysis utilities

**This Research Document:**
This document contains the research findings on what performance testing _would_ look like if it were in scope. It is preserved for:

1. Future reference if performance testing becomes necessary
2. Documentation of the decision-making process
3. Understanding what was deliberately excluded from scope

**Do NOT implement anything from this document. Performance testing is explicitly OUT OF SCOPE.**

---

## Executive Summary (REFERENCE ONLY - NOT TO BE IMPLEMENTED)

This document defines what comprehensive performance and efficiency testing requirements _would be_ for the CSAPI client library, with focus on parser performance (especially Binary SWE Common), large dataset handling, Worker thread efficiency, and memory management.

**REMINDER: This is research only. None of these tests will be implemented.**

### Key Findings

**Performance-Critical Components (5):**

1. **SWE Common Parsers** (JSON, Text, Binary) - Handle high-volume observation data
2. **Worker Thread Operations** - Offload heavy parsing from main thread
3. **API Client Methods** - User-visible response times
4. **Pagination/Streaming** - Large collection traversal
5. **Memory Management** - Prevent browser crashes with large datasets

**Performance Requirements:**

| Component                          | Target    | Measurement   | Priority     |
| ---------------------------------- | --------- | ------------- | ------------ |
| **Parser Performance**             |
| Parse 100 observations (JSON)      | < 10ms    | p95 latency   | **CRITICAL** |
| Parse 100 observations (Binary)    | < 5ms     | p95 latency   | **CRITICAL** |
| Parse 1000 observations (JSON)     | < 100ms   | p95 latency   | **CRITICAL** |
| Parse 1000 observations (Binary)   | < 50ms    | p95 latency   | **CRITICAL** |
| Parse 10000 observations (Binary)  | < 500ms   | p95 latency   | HIGH         |
| **Worker Performance**             |
| Worker message overhead            | < 5ms     | p95 latency   | HIGH         |
| Background parsing vs main thread  | 2x faster | throughput    | HIGH         |
| **API Performance**                |
| Get collection list                | < 200ms   | p95 latency   | HIGH         |
| Get single resource                | < 100ms   | p95 latency   | HIGH         |
| Get paginated resources (50 items) | < 300ms   | p95 latency   | MEDIUM       |
| **Memory Efficiency**              |
| Parse 1000 observations            | < 10MB    | heap increase | **CRITICAL** |
| Parse 10000 observations           | < 100MB   | heap increase | HIGH         |
| Parse 100000 observations          | < 500MB   | heap increase | MEDIUM       |
| **Throughput**                     |
| Observations/second (Binary)       | > 10,000  | ops/sec       | HIGH         |
| Observations/second (JSON)         | > 5,000   | ops/sec       | MEDIUM       |

**Binary Encoding Performance Advantage:**

- **Expected:** 2x faster than JSON for equivalent data
- **Reason:** No text parsing, compact binary representation, optimized data types
- **Use Case:** High-frequency sensors (>10 Hz), large observation batches

**Testing Approach:**

- **Benchmark Suites:** Dedicated performance test suites (not unit tests)
- **Statistical Analysis:** 100 iterations, report p50/p95/p99 percentiles
- **Baseline Establishment:** Initial implementation serves as baseline
- **Regression Detection:** Alert if performance degrades >10% from baseline
- **Profiling:** Use browser Profiler API to identify hotspots

**Fixture Requirements:** ~50 performance fixtures

- Small datasets: 10, 50, 100 observations (baseline)
- Medium datasets: 500, 1000 observations (typical production)
- Large datasets: 5000, 10000 observations (stress testing)
- Very large datasets: 50000, 100000 observations (extreme stress)
- All 3 encodings: JSON, Text, Binary for each size

**Estimated Test Implementation:** 600-900 lines

- Parser performance benchmarks: 200-300 lines (12-15 tests)
- Worker performance benchmarks: 100-150 lines (6-8 tests)
- Memory usage tests: 100-150 lines (6-8 tests)
- Pagination performance tests: 80-120 lines (4-6 tests)
- API performance tests: 120-180 lines (8-10 tests)

**Key Testing Challenges:**

1. **Environment consistency** - Performance varies across browsers, CPUs, memory
2. **Statistical significance** - Need multiple iterations to reduce variance
3. **Fixture generation** - Large datasets expensive to create
4. **Worker overhead** - Message passing adds latency vs main thread
5. **Memory measurement** - Chrome-specific Memory API

### Highest Rejection Risk

Parser performance testing is **MEDIUM RISK** because:

- **Binary encoding complexity** - Most performance-critical, most complex parsing
- **Measurement variability** - Performance varies by environment (browser, CPU, memory)
- **Statistical rigor** - Need proper benchmarking methodology (not simple assertions)
- **Regression tracking** - Requires baseline establishment and continuous monitoring

**Mitigation:** Comprehensive benchmark suite with multiple dataset sizes, statistical analysis (p95/p99), regression detection with >10% threshold, profiling to identify hotspots.

---

## 1. Performance Requirements by Component

### 1.1 Parser Performance Requirements

**Priority:** **CRITICAL**

**Rationale:** Parsers are the most performance-critical components because they:

- Handle high-volume observation data (1000+ observations per request)
- Run frequently (every observation query)
- Block user interface if too slow
- Scale with dataset size (O(n) complexity)

**Target Metrics:**

| Dataset Size           | Encoding | Target (p95) | Measurement | Priority     |
| ---------------------- | -------- | ------------ | ----------- | ------------ |
| **10 observations**    |
|                        | JSON     | < 2ms        | parse time  | HIGH         |
|                        | Text     | < 2ms        | parse time  | HIGH         |
|                        | Binary   | < 1ms        | parse time  | HIGH         |
| **100 observations**   |
|                        | JSON     | < 10ms       | parse time  | **CRITICAL** |
|                        | Text     | < 8ms        | parse time  | **CRITICAL** |
|                        | Binary   | < 5ms        | parse time  | **CRITICAL** |
| **1000 observations**  |
|                        | JSON     | < 100ms      | parse time  | **CRITICAL** |
|                        | Text     | < 80ms       | parse time  | **CRITICAL** |
|                        | Binary   | < 50ms       | parse time  | **CRITICAL** |
| **5000 observations**  |
|                        | JSON     | < 500ms      | parse time  | HIGH         |
|                        | Text     | < 400ms      | parse time  | HIGH         |
|                        | Binary   | < 250ms      | parse time  | HIGH         |
| **10000 observations** |
|                        | JSON     | < 1000ms     | parse time  | MEDIUM       |
|                        | Text     | < 800ms      | parse time  | MEDIUM       |
|                        | Binary   | < 500ms      | parse time  | HIGH         |

**Binary Encoding Advantage:**

- **Expected speedup:** 2x faster than JSON
- **Reason:** No text parsing overhead, compact binary format, optimized data types
- **Use cases:** High-frequency sensors (>10 Hz), large observation batches (>1000 items), real-time streaming

**Complex Schema Performance:**

```typescript
// Simple schema (3 fields)
DataRecord {
  fields: [
    { name: 'time', type: 'Time' },
    { name: 'temp', type: 'Quantity' },
    { name: 'humidity', type: 'Quantity' }
  ]
}
// Expected: Base performance targets

// Complex schema (15+ fields, nested DataRecords)
DataRecord {
  fields: [
    { name: 'time', type: 'Time' },
    { name: 'sensor', type: 'DataRecord' { fields: [...] } },
    { name: 'location', type: 'Vector' },
    // ... 12 more fields
  ]
}
// Expected: ~1.5x slower than simple schema
```

---

### 1.2 Worker Performance Requirements

**Priority:** HIGH

**Rationale:** Worker threads offload heavy parsing from main thread to maintain responsive UI.

**Target Metrics:**

| Operation                  | Target (p95) | Measurement | Priority   |
| -------------------------- | ------------ | ----------- | ---------- |
| **Message Overhead**       |
| Worker message round-trip  | < 5ms        | latency     | HIGH       |
| Data serialization (1KB)   | < 1ms        | time        | MEDIUM     |
| Data serialization (100KB) | < 10ms       | time        | MEDIUM     |
| Data serialization (1MB)   | < 50ms       | time        | LOW        |
| **Background Parsing**     |
| 100 observations (Worker)  | < 15ms       | total time  | HIGH       |
| 100 observations (Main)    | < 10ms       | total time  | (baseline) |
| 1000 observations (Worker) | < 120ms      | total time  | HIGH       |
| 1000 observations (Main)   | < 100ms      | total time  | (baseline) |
| **Throughput**             |
| Observations/sec (Worker)  | > 8,000      | ops/sec     | HIGH       |
| Observations/sec (Main)    | > 10,000     | ops/sec     | (baseline) |

**Worker vs Main Thread Tradeoffs:**

**When Worker is Faster:**

- Large datasets (>500 observations) where parsing time >> message overhead
- Complex schemas requiring heavy computation
- Main thread is busy with UI updates

**When Main Thread is Faster:**

- Small datasets (<100 observations) where message overhead > parsing time
- Simple schemas with minimal computation
- Main thread is idle

**Measurement Approach:**

```typescript
// Worker total time
const start = performance.now();
const result = await workerClient.parseSWEResult(data, schema);
const workerTime = performance.now() - start;

// Main thread total time
const start2 = performance.now();
const result2 = parseSWEResult(data, schema);
const mainTime = performance.now() - start2;

// Overhead
const overhead = workerTime - mainTime;
```

---

### 1.3 API Performance Requirements

**Priority:** HIGH

**Rationale:** API calls are user-visible and affect perceived application responsiveness.

**Target Metrics:**

| Operation                       | Target (p95) | Measurement | Priority     |
| ------------------------------- | ------------ | ----------- | ------------ |
| **Collection Operations**       |
| List systems                    | < 200ms      | total time  | HIGH         |
| List deployments                | < 200ms      | total time  | HIGH         |
| List datastreams                | < 200ms      | total time  | HIGH         |
| **Single Resource Operations**  |
| Get system by ID                | < 100ms      | total time  | HIGH         |
| Get deployment by ID            | < 100ms      | total time  | HIGH         |
| Get datastream by ID            | < 100ms      | total time  | HIGH         |
| **Paginated Operations**        |
| Get 10 items                    | < 150ms      | total time  | HIGH         |
| Get 50 items                    | < 300ms      | total time  | HIGH         |
| Get 100 items                   | < 500ms      | total time  | MEDIUM       |
| **Observation Queries**         |
| Get 100 observations            | < 200ms      | total time  | **CRITICAL** |
| Get 1000 observations           | < 800ms      | total time  | HIGH         |
| Get 10000 observations          | < 5000ms     | total time  | MEDIUM       |
| **Relationship Navigation**     |
| System → DataStreams            | < 250ms      | total time  | HIGH         |
| DataStream → Observations (100) | < 300ms      | total time  | HIGH         |
| Deployment → Systems            | < 200ms      | total time  | MEDIUM       |

**Total Time Breakdown:**

```
Total Time = Network Latency + Server Processing + Parsing Time

Example (Get 100 observations):
- Network latency: ~50-100ms (varies by connection)
- Server processing: ~20-50ms (varies by server)
- Client parsing: <10ms (target - JSON) or <5ms (target - Binary)
- Total: ~80-160ms (well under 200ms target)
```

**Performance Budget:**

- **Network latency:** Not controlled by client (50-150ms typical)
- **Server processing:** Not controlled by client (20-100ms typical)
- **Client parsing:** **Controlled by client** - must be <10% of total time

---

### 1.4 Memory Usage Requirements

**Priority:** **CRITICAL**

**Rationale:** Excessive memory usage causes:

- Browser crashes (especially mobile)
- Garbage collection pauses (UI freezes)
- Slow performance due to swapping
- Out-of-memory errors on large datasets

**Target Metrics:**

| Dataset Size            | Max Heap Increase | Measurement | Priority     |
| ----------------------- | ----------------- | ----------- | ------------ |
| **10 observations**     | < 100KB           | heap delta  | MEDIUM       |
| **100 observations**    | < 1MB             | heap delta  | HIGH         |
| **1000 observations**   | < 10MB            | heap delta  | **CRITICAL** |
| **10000 observations**  | < 100MB           | heap delta  | HIGH         |
| **100000 observations** | < 500MB           | heap delta  | MEDIUM       |

**Memory Efficiency Targets:**

- **Per observation overhead:** < 10KB/observation (JSON)
- **Per observation overhead:** < 5KB/observation (Binary)
- **Peak memory:** < 2x final data size (temporary parsing overhead)
- **Garbage collection:** < 10% of total parsing time

**Memory Measurement (Chrome only):**

```typescript
// Measure heap size before
const before = (performance as any).memory.usedJSHeapSize;

// Parse data
const result = parseSWEResult(data, schema);

// Force garbage collection (requires --expose-gc flag)
if (global.gc) global.gc();

// Measure heap size after
const after = (performance as any).memory.usedJSHeapSize;

// Memory increase
const memoryIncrease = after - before;
```

**Memory Leak Detection:**

- Parse large dataset multiple times
- Check if heap size grows linearly (leak) or plateaus (no leak)
- Expected: Heap size plateaus after 2-3 iterations (GC cleans up)

---

### 1.5 Pagination Performance Requirements

**Priority:** MEDIUM

**Rationale:** Large collections require efficient pagination to avoid loading entire dataset.

**Target Metrics:**

| Operation                        | Target (p95) | Measurement | Priority |
| -------------------------------- | ------------ | ----------- | -------- |
| **First Page**                   |
| Get page 1 (10 items)            | < 200ms      | total time  | HIGH     |
| Get page 1 (50 items)            | < 300ms      | total time  | HIGH     |
| Get page 1 (100 items)           | < 500ms      | total time  | MEDIUM   |
| **Subsequent Pages**             |
| Get page 2-10 (offset)           | < 300ms      | total time  | MEDIUM   |
| Get page 2-10 (cursor)           | < 250ms      | total time  | HIGH     |
| **Large Offsets**                |
| Get page 100 (offset 1000)       | < 500ms      | total time  | LOW      |
| Get via cursor (any page)        | < 250ms      | total time  | HIGH     |
| **Full Traversal**               |
| Paginate 1000 items (10 pages)   | < 3000ms     | total time  | MEDIUM   |
| Paginate 10000 items (100 pages) | < 30s        | total time  | LOW      |

**Cursor vs Offset Performance:**

- **Cursor:** Constant time (O(1)) - use for Part 2 (Observations, Commands)
- **Offset:** Linear time (O(n)) - acceptable for Part 1 (Systems, Deployments)

---

## 2. Benchmark Scenario Design

### 2.1 Parser Performance Benchmarks

**Test Suite:** `performance/parser-benchmarks.spec.ts`

**Benchmark Structure:**

```typescript
describe('SWE Common Parser Performance', () => {
  describe('JSON Encoding Performance', () => {
    it('should parse 10 observations in <2ms (p95)', async () => {
      const fixture = load('observations-10-json.json');
      const iterations = 100;
      const times: number[] = [];

      for (let i = 0; i < iterations; i++) {
        const start = performance.now();
        const result = parseJSONObservations(fixture, schema);
        const end = performance.now();
        times.push(end - start);
      }

      const stats = calculateStats(times);

      console.log(
        `JSON 10 obs: ${stats.p50}ms (p50), ${stats.p95}ms (p95), ${stats.p99}ms (p99)`
      );

      expect(stats.p95).toBeLessThan(2);
      expect(result.observations.length).toBe(10);
    });

    it('should parse 100 observations in <10ms (p95)', async () => {
      // Similar structure
      expect(stats.p95).toBeLessThan(10);
    });

    it('should parse 1000 observations in <100ms (p95)', async () => {
      expect(stats.p95).toBeLessThan(100);
    });

    it('should parse 10000 observations in <1000ms (p95)', async () => {
      expect(stats.p95).toBeLessThan(1000);
    });
  });

  describe('Binary Encoding Performance', () => {
    it('should parse 10 observations in <1ms (p95)', async () => {
      const fixture = load('observations-10-binary.bin');
      // ... benchmark
      expect(stats.p95).toBeLessThan(1);
    });

    it('should parse 100 observations in <5ms (p95)', async () => {
      expect(stats.p95).toBeLessThan(5);
    });

    it('should parse 1000 observations in <50ms (p95)', async () => {
      expect(stats.p95).toBeLessThan(50);
    });

    it('should parse 10000 observations in <500ms (p95)', async () => {
      expect(stats.p95).toBeLessThan(500);
    });
  });

  describe('Binary vs JSON Performance Comparison', () => {
    it('should parse Binary 2x faster than JSON (1000 observations)', async () => {
      const jsonFixture = load('observations-1000-json.json');
      const binaryFixture = load('observations-1000-binary.bin');

      const jsonStats = benchmarkParsing(
        () => parseJSONObservations(jsonFixture, schema),
        100
      );
      const binaryStats = benchmarkParsing(
        () => parseBinaryObservations(binaryFixture, schema),
        100
      );

      const speedup = jsonStats.p50 / binaryStats.p50;

      console.log(`Binary speedup: ${speedup}x faster than JSON`);

      expect(speedup).toBeGreaterThanOrEqual(1.8); // At least 1.8x faster
      expect(speedup).toBeLessThanOrEqual(2.5); // At most 2.5x faster (realistic range)
    });
  });

  describe('Complex Schema Performance', () => {
    it('should parse nested DataRecord in <150ms (1000 observations, p95)', async () => {
      const fixture = load('observations-1000-complex-schema-json.json');
      const complexSchema = load('complex-schema.json');

      // ... benchmark

      expect(stats.p95).toBeLessThan(150); // ~1.5x slower than simple schema
    });
  });
});
```

**Statistical Analysis Utilities:**

```typescript
function calculateStats(times: number[]): PerformanceStats {
  const sorted = times.sort((a, b) => a - b);

  return {
    min: sorted[0],
    max: sorted[sorted.length - 1],
    mean: sorted.reduce((a, b) => a + b) / sorted.length,
    median: sorted[Math.floor(sorted.length / 2)],
    p50: sorted[Math.floor(sorted.length * 0.5)],
    p95: sorted[Math.floor(sorted.length * 0.95)],
    p99: sorted[Math.floor(sorted.length * 0.99)],
    stddev: calculateStdDev(sorted),
  };
}

function benchmarkParsing(
  parseFn: () => any,
  iterations: number = 100
): PerformanceStats {
  const times: number[] = [];

  for (let i = 0; i < iterations; i++) {
    const start = performance.now();
    parseFn();
    const end = performance.now();
    times.push(end - start);
  }

  return calculateStats(times);
}
```

---

### 2.2 Worker Performance Benchmarks

**Test Suite:** `performance/worker-benchmarks.spec.ts`

**Benchmark Structure:**

```typescript
describe('Worker Performance', () => {
  describe('Message Overhead', () => {
    it('should have <5ms message overhead (p95)', async () => {
      const iterations = 100;
      const times: number[] = [];

      for (let i = 0; i < iterations; i++) {
        const start = performance.now();

        // Simple echo message (no parsing, just overhead)
        await workerClient.sendMessage({ type: 'ECHO', data: 'test' });

        const end = performance.now();
        times.push(end - start);
      }

      const stats = calculateStats(times);

      console.log(`Worker message overhead: ${stats.p95}ms (p95)`);

      expect(stats.p95).toBeLessThan(5);
    });
  });

  describe('Background Parsing vs Main Thread', () => {
    it('should parse 1000 observations in Worker (total time < 120ms, p95)', async () => {
      const fixture = load('observations-1000-json.json');
      const iterations = 50;

      const workerStats = benchmarkParsing(async () => {
        await workerClient.parseSWEResult(fixture, schema);
      }, iterations);

      console.log(`Worker parse 1000 obs: ${workerStats.p95}ms (p95)`);

      expect(workerStats.p95).toBeLessThan(120); // Includes message overhead
    });

    it('should compare Worker vs Main thread performance', async () => {
      const fixture = load('observations-1000-json.json');

      // Main thread benchmark
      const mainStats = benchmarkParsing(() => {
        parseSWEResult(fixture, schema);
      }, 50);

      // Worker thread benchmark
      const workerStats = benchmarkParsing(async () => {
        await workerClient.parseSWEResult(fixture, schema);
      }, 50);

      const overhead = workerStats.p50 - mainStats.p50;

      console.log(`Worker overhead: ${overhead}ms`);
      console.log(`Main: ${mainStats.p50}ms, Worker: ${workerStats.p50}ms`);

      // Worker has overhead but still acceptable
      expect(overhead).toBeLessThan(20); // <20ms overhead for 1000 observations
    });
  });

  describe('Throughput', () => {
    it('should achieve >8000 observations/sec in Worker', async () => {
      const fixture = load('observations-1000-json.json');
      const iterations = 10;
      const totalObservations = 1000 * iterations;

      const start = performance.now();

      for (let i = 0; i < iterations; i++) {
        await workerClient.parseSWEResult(fixture, schema);
      }

      const end = performance.now();
      const totalTime = (end - start) / 1000; // Convert to seconds
      const throughput = totalObservations / totalTime;

      console.log(`Worker throughput: ${throughput.toFixed(0)} obs/sec`);

      expect(throughput).toBeGreaterThan(8000);
    });
  });
});
```

---

### 2.3 Memory Usage Benchmarks

**Test Suite:** `performance/memory-benchmarks.spec.ts`

**Note:** Memory measurement requires Chrome with `--expose-gc` flag.

**Benchmark Structure:**

```typescript
describe('Memory Usage', () => {
  beforeEach(() => {
    // Force garbage collection before each test
    if (global.gc) global.gc();
  });

  describe('Observation Parsing Memory', () => {
    it('should use <1MB memory for 100 observations', () => {
      const fixture = load('observations-100-json.json');

      const memoryBefore = (performance as any).memory.usedJSHeapSize;

      const result = parseSWEResult(fixture, schema);

      // Force GC to get accurate measurement
      if (global.gc) global.gc();

      const memoryAfter = (performance as any).memory.usedJSHeapSize;
      const memoryIncrease = (memoryAfter - memoryBefore) / 1024 / 1024; // MB

      console.log(`Memory increase (100 obs): ${memoryIncrease.toFixed(2)} MB`);

      expect(memoryIncrease).toBeLessThan(1);
      expect(result.observations.length).toBe(100);
    });

    it('should use <10MB memory for 1000 observations', () => {
      const fixture = load('observations-1000-json.json');

      // ... similar measurement

      expect(memoryIncrease).toBeLessThan(10);
    });

    it('should use <100MB memory for 10000 observations', () => {
      expect(memoryIncrease).toBeLessThan(100);
    });
  });

  describe('Memory Leak Detection', () => {
    it('should not leak memory on repeated parsing', () => {
      const fixture = load('observations-1000-json.json');
      const iterations = 10;
      const memorySnapshots: number[] = [];

      for (let i = 0; i < iterations; i++) {
        const result = parseSWEResult(fixture, schema);

        // Force GC
        if (global.gc) global.gc();

        const memory = (performance as any).memory.usedJSHeapSize;
        memorySnapshots.push(memory);
      }

      // Check if memory growth is linear (leak) or plateaus (no leak)
      const firstThree = memorySnapshots.slice(0, 3);
      const lastThree = memorySnapshots.slice(-3);

      const firstAvg = firstThree.reduce((a, b) => a + b) / firstThree.length;
      const lastAvg = lastThree.reduce((a, b) => a + b) / lastThree.length;

      const growth = (lastAvg - firstAvg) / firstAvg;

      console.log(
        `Memory growth over ${iterations} iterations: ${(growth * 100).toFixed(
          1
        )}%`
      );

      // Memory should not grow more than 20% (allows for GC variability)
      expect(growth).toBeLessThan(0.2);
    });
  });

  describe('Peak Memory Usage', () => {
    it('should have peak memory <2x final data size', () => {
      const fixture = load('observations-1000-json.json');

      let peakMemory = 0;
      let baselineMemory = (performance as any).memory.usedJSHeapSize;

      // Monitor memory during parsing
      const interval = setInterval(() => {
        const current = (performance as any).memory.usedJSHeapSize;
        if (current > peakMemory) peakMemory = current;
      }, 1); // Sample every 1ms

      const result = parseSWEResult(fixture, schema);

      clearInterval(interval);

      if (global.gc) global.gc();

      const finalMemory = (performance as any).memory.usedJSHeapSize;
      const peakIncrease = (peakMemory - baselineMemory) / 1024 / 1024;
      const finalIncrease = (finalMemory - baselineMemory) / 1024 / 1024;

      const ratio = peakIncrease / finalIncrease;

      console.log(`Peak memory: ${peakIncrease.toFixed(2)} MB`);
      console.log(`Final memory: ${finalIncrease.toFixed(2)} MB`);
      console.log(`Ratio: ${ratio.toFixed(2)}x`);

      expect(ratio).toBeLessThan(2);
    });
  });
});
```

---

### 2.4 API Performance Benchmarks

**Test Suite:** `performance/api-benchmarks.spec.ts`

**Benchmark Structure:**

```typescript
describe('API Performance', () => {
  let client: CSAPIClient;
  let mockServer: MockCSAPIServer;

  beforeEach(() => {
    // Use mock server with realistic latency
    mockServer = new MockCSAPIServer({
      latency: 50, // 50ms network latency
    });
    client = new CSAPIClient(mockServer.url);
  });

  describe('Collection Operations', () => {
    it('should list systems in <200ms (p95)', async () => {
      const iterations = 50;

      const stats = await benchmarkAsync(async () => {
        await client.systems.list({ limit: 10 });
      }, iterations);

      console.log(`List systems: ${stats.p95}ms (p95)`);

      expect(stats.p95).toBeLessThan(200);
    });

    it('should get system by ID in <100ms (p95)', async () => {
      const stats = await benchmarkAsync(async () => {
        await client.systems.get('sys-123');
      }, 50);

      expect(stats.p95).toBeLessThan(100);
    });
  });

  describe('Observation Queries', () => {
    it('should get 100 observations in <200ms (p95)', async () => {
      mockServer.setObservations('ds-123', 100); // Setup mock

      const stats = await benchmarkAsync(async () => {
        await client.datastreams.observations('ds-123').list({ limit: 100 });
      }, 50);

      console.log(`Get 100 observations: ${stats.p95}ms (p95)`);

      expect(stats.p95).toBeLessThan(200);
    });

    it('should get 1000 observations in <800ms (p95)', async () => {
      mockServer.setObservations('ds-123', 1000);

      const stats = await benchmarkAsync(async () => {
        await client.datastreams.observations('ds-123').list({ limit: 1000 });
      }, 20); // Fewer iterations for large datasets

      expect(stats.p95).toBeLessThan(800);
    });
  });

  describe('Pagination Performance', () => {
    it('should paginate 1000 items in <3000ms', async () => {
      mockServer.setSystems(1000); // 1000 systems

      const start = performance.now();

      let totalItems = 0;
      const generator = client.systems.listPaginated({ limit: 100 });

      for await (const system of generator) {
        totalItems++;
      }

      const end = performance.now();
      const totalTime = end - start;

      console.log(`Paginated 1000 items in ${totalTime.toFixed(0)}ms`);

      expect(totalItems).toBe(1000);
      expect(totalTime).toBeLessThan(3000);
    });
  });
});
```

---

### 2.5 Pagination Performance Benchmarks

**Test Suite:** `performance/pagination-benchmarks.spec.ts`

**Benchmark Structure:**

```typescript
describe('Pagination Performance', () => {
  describe('Offset-Based Pagination', () => {
    it('should fetch first page (10 items) in <200ms (p95)', async () => {
      const stats = await benchmarkAsync(async () => {
        await client.systems.list({ limit: 10, offset: 0 });
      }, 50);

      expect(stats.p95).toBeLessThan(200);
    });

    it('should fetch page 100 (offset 1000) in <500ms (p95)', async () => {
      // Large offset may be slower
      const stats = await benchmarkAsync(async () => {
        await client.systems.list({ limit: 10, offset: 1000 });
      }, 20);

      expect(stats.p95).toBeLessThan(500);
    });
  });

  describe('Cursor-Based Pagination', () => {
    it('should fetch first page via cursor in <250ms (p95)', async () => {
      const stats = await benchmarkAsync(async () => {
        await client.observations.list({ limit: 100 });
      }, 50);

      expect(stats.p95).toBeLessThan(250);
    });

    it('should fetch subsequent pages via cursor in <250ms (p95)', async () => {
      // First page to get cursor
      const page1 = await client.observations.list({ limit: 100 });
      const cursor = extractCursor(page1.links);

      const stats = await benchmarkAsync(async () => {
        await client.observations.list({ limit: 100, cursor });
      }, 50);

      expect(stats.p95).toBeLessThan(250);
    });
  });

  describe('Full Collection Traversal', () => {
    it('should traverse 1000 items in <3000ms', async () => {
      mockServer.setObservations('ds-123', 1000);

      const start = performance.now();

      let count = 0;
      const generator = client.datastreams
        .observations('ds-123')
        .listPaginated({ limit: 100 });

      for await (const obs of generator) {
        count++;
      }

      const end = performance.now();
      const totalTime = end - start;

      console.log(`Traversed 1000 observations in ${totalTime.toFixed(0)}ms`);

      expect(count).toBe(1000);
      expect(totalTime).toBeLessThan(3000);
    });
  });
});
```

---

## 3. Upstream Performance Testing Analysis

### 3.1 Upstream Performance Tests

**Finding:** No explicit performance tests in upstream `ogc-client` codebase.

**Evidence:**

- Searched `src/**/*.spec.ts` for performance-related keywords (performance.mark, performance.measure, benchmark, throughput, latency)
- Found only `jest.useFakeTimers()` for timeout testing (not performance)
- No dedicated benchmark suites

**Implications:**

1. **CSAPI must define performance testing from scratch** - no reusable patterns
2. **Performance is tested implicitly** through functional tests (if they pass, performance is acceptable)
3. **Upstream approach is pragmatic** - avoid performance testing complexity unless needed

### 3.2 Upstream Performance Characteristics

**WMS/WFS/WMTS Parsing Performance:**

- XML parsing (~1-10KB documents) is fast enough not to require explicit testing
- Typical parse times: <5ms for capabilities documents
- No large dataset scenarios (unlike CSAPI observations)

**STAC/Features API:**

- JSON parsing for collections (~10-100 items) is fast
- No binary encoding requirements
- No high-volume data scenarios

**CSAPI Performance Requirements are Unique:**

- **Large datasets:** 1000+ observations per request (vs 10-100 items in STAC)
- **Binary encoding:** Performance-critical binary parsing (not in other OGC APIs)
- **Real-time data:** High-frequency sensors (>10 Hz) require efficient parsing
- **Worker threads:** Heavy parsing workload justifies Worker performance testing

### 3.3 Performance Testing Best Practices

**Industry Standards:**

1. **Statistical Rigor:**

   - Run benchmarks 50-100 iterations
   - Report percentiles (p50, p95, p99) not just mean
   - Eliminate outliers (warmup iterations)

2. **Baseline Establishment:**

   - Initial implementation serves as baseline
   - Track performance over time
   - Alert on regressions >10% from baseline

3. **Environment Consistency:**

   - Run on same hardware
   - Close other applications
   - Disable background processes
   - Use consistent browser version

4. **Fixture Realism:**

   - Use realistic dataset sizes (not just tiny examples)
   - Use realistic schemas (not overly simplified)
   - Use realistic data distributions (not all zeros)

5. **Profiling:**
   - Use browser Profiler API to identify hotspots
   - Optimize based on profiling data (not guesses)
   - Profile both CPU and memory

**Performance Testing Tools:**

**Browser Performance API:**

```typescript
const start = performance.now();
// ... operation
const end = performance.now();
const duration = end - start;
```

**Chrome Memory API:**

```typescript
const memory = (performance as any).memory;
console.log('Used heap size:', memory.usedJSHeapSize / 1024 / 1024, 'MB');
console.log('Total heap size:', memory.totalJSHeapSize / 1024 / 1024, 'MB');
```

**Chrome Profiler API:**

```typescript
console.profile('parseSWEResult');
parseSWEResult(data, schema);
console.profileEnd('parseSWEResult');
// View profile in Chrome DevTools
```

**Benchmark.js (External Library):**

```typescript
import Benchmark from 'benchmark';

const suite = new Benchmark.Suite();

suite
  .add('JSON parsing', () => {
    parseJSONObservations(data, schema);
  })
  .add('Binary parsing', () => {
    parseBinaryObservations(data, schema);
  })
  .on('cycle', (event) => {
    console.log(String(event.target));
  })
  .on('complete', function () {
    console.log('Fastest is ' + this.filter('fastest').map('name'));
  })
  .run({ async: true });
```

---

## 4. Measurement Strategy Design

### 4.1 Performance Metrics

**Primary Metrics:**

| Metric           | Definition                           | Unit              | Use Case                             |
| ---------------- | ------------------------------------ | ----------------- | ------------------------------------ |
| **Latency**      | Time to complete single operation    | milliseconds (ms) | Response time, user experience       |
| **Throughput**   | Operations per unit time             | ops/sec           | High-volume processing capacity      |
| **Memory Usage** | Heap size increase                   | megabytes (MB)    | Resource consumption, leak detection |
| **CPU Time**     | Processing time (excluding I/O wait) | milliseconds (ms) | Computational efficiency             |

**Secondary Metrics:**

| Metric               | Definition                          | Unit              | Use Case               |
| -------------------- | ----------------------------------- | ----------------- | ---------------------- |
| **Peak Memory**      | Maximum heap size during operation  | megabytes (MB)    | Memory spike detection |
| **GC Time**          | Garbage collection duration         | milliseconds (ms) | Pause impact on UI     |
| **Message Overhead** | Worker message round-trip time      | milliseconds (ms) | Worker efficiency      |
| **Parsing Ratio**    | Binary parse time / JSON parse time | ratio             | Encoding efficiency    |

### 4.2 Statistical Analysis

**Percentile Reporting:**

| Percentile       | Meaning                  | Use Case                                               |
| ---------------- | ------------------------ | ------------------------------------------------------ |
| **p50 (median)** | 50% of operations faster | Typical performance                                    |
| **p95**          | 95% of operations faster | Performance SLA (5% outliers allowed)                  |
| **p99**          | 99% of operations faster | Worst-case performance (excluding 1% extreme outliers) |
| **max**          | Slowest operation        | Extreme worst case                                     |

**Why p95 is Primary Metric:**

- **Realistic:** Allows for occasional slow operations (network blips, GC pauses)
- **Actionable:** If p95 exceeds target, investigate why 5% of operations are slow
- **Not overly pessimistic:** p99/max can be extreme outliers not representative of typical performance

**Statistical Functions:**

```typescript
interface PerformanceStats {
  min: number;
  max: number;
  mean: number;
  median: number;
  p50: number;
  p95: number;
  p99: number;
  stddev: number;
}

function calculateStats(times: number[]): PerformanceStats {
  const sorted = times.sort((a, b) => a - b);
  const n = sorted.length;

  const sum = sorted.reduce((a, b) => a + b, 0);
  const mean = sum / n;

  const variance =
    sorted.reduce((acc, val) => acc + Math.pow(val - mean, 2), 0) / n;
  const stddev = Math.sqrt(variance);

  return {
    min: sorted[0],
    max: sorted[n - 1],
    mean,
    median: sorted[Math.floor(n / 2)],
    p50: sorted[Math.floor(n * 0.5)],
    p95: sorted[Math.floor(n * 0.95)],
    p99: sorted[Math.floor(n * 0.99)],
    stddev,
  };
}
```

### 4.3 Baseline Establishment

**Initial Baseline:**

1. Run all performance benchmarks on initial implementation
2. Record p95 latency for each scenario
3. Store baseline metrics in `performance/baseline.json`

**Baseline File Format:**

```json
{
  "version": "1.0.0",
  "date": "2026-02-06",
  "environment": {
    "browser": "Chrome 130",
    "os": "Windows 11",
    "cpu": "Intel i7-12700K",
    "memory": "32GB"
  },
  "benchmarks": {
    "parse-json-100-obs": {
      "p50": 7.2,
      "p95": 9.8,
      "p99": 12.1,
      "unit": "ms"
    },
    "parse-binary-100-obs": {
      "p50": 3.5,
      "p95": 4.8,
      "p99": 6.2,
      "unit": "ms"
    },
    "parse-json-1000-obs": {
      "p50": 72.1,
      "p95": 89.5,
      "p99": 105.3,
      "unit": "ms"
    },
    "parse-binary-1000-obs": {
      "p50": 36.8,
      "p95": 45.2,
      "p99": 58.1,
      "unit": "ms"
    }
  }
}
```

### 4.4 Regression Detection

**Regression Threshold:** 10% slower than baseline

**Regression Detection Algorithm:**

```typescript
function detectRegression(
  current: PerformanceStats,
  baseline: PerformanceStats,
  threshold: number = 0.1 // 10%
): boolean {
  const regression = (current.p95 - baseline.p95) / baseline.p95;

  if (regression > threshold) {
    console.error(`Performance regression detected!`);
    console.error(`  Baseline p95: ${baseline.p95}ms`);
    console.error(`  Current p95: ${current.p95}ms`);
    console.error(`  Regression: ${(regression * 100).toFixed(1)}%`);
    return true;
  }

  if (regression < -threshold) {
    console.log(`Performance improvement!`);
    console.log(`  Baseline p95: ${baseline.p95}ms`);
    console.log(`  Current p95: ${current.p95}ms`);
    console.log(`  Improvement: ${(Math.abs(regression) * 100).toFixed(1)}%`);
  }

  return false;
}
```

**CI/CD Integration:**

```yaml
# .github/workflows/performance.yml
name: Performance Tests

on:
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 2 * * *' # Daily at 2 AM

jobs:
  performance:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
      - run: npm ci
      - run: npm run test:performance
      - name: Compare with baseline
        run: npm run performance:compare
      - name: Fail if regression
        if: steps.compare.outputs.regression == 'true'
        run: exit 1
```

### 4.5 Profiling Strategy

**When to Profile:**

- Performance benchmark fails (exceeds target)
- Performance regression detected (>10% slower)
- Implementing performance-critical feature (parsers, Workers)

**Profiling Tools:**

**Chrome DevTools Profiler:**

```typescript
// Start profiling
console.profile('parseSWEResult');

// Run operation
parseSWEResult(data, schema);

// Stop profiling
console.profileEnd('parseSWEResult');

// View profile in Chrome DevTools → Performance tab
```

**performance.mark() / performance.measure():**

```typescript
// Mark start
performance.mark('parse-start');

// ... parsing logic

// Mark end
performance.mark('parse-end');

// Measure duration
performance.measure('parse-duration', 'parse-start', 'parse-end');

// Get measurement
const measure = performance.getEntriesByName('parse-duration')[0];
console.log(`Parse duration: ${measure.duration}ms`);
```

**Custom Instrumentation:**

```typescript
class PerformanceProfiler {
  private marks: Map<string, number> = new Map();

  start(label: string) {
    this.marks.set(label, performance.now());
  }

  end(label: string): number {
    const start = this.marks.get(label);
    if (!start) throw new Error(`No start mark for ${label}`);

    const duration = performance.now() - start;
    this.marks.delete(label);

    return duration;
  }

  async measure<T>(label: string, fn: () => T | Promise<T>): Promise<T> {
    this.start(label);
    const result = await fn();
    const duration = this.end(label);

    console.log(`${label}: ${duration.toFixed(2)}ms`);

    return result;
  }
}

// Usage
const profiler = new PerformanceProfiler();

await profiler.measure('parse-observations', () => {
  return parseSWEResult(data, schema);
});
```

---

## 5. Test Infrastructure Design

### 5.1 Performance Test Execution Environment

**Test Suite Location:**

```
test/
  performance/
    parser-benchmarks.spec.ts      # Parser performance
    worker-benchmarks.spec.ts      # Worker performance
    memory-benchmarks.spec.ts      # Memory usage
    api-benchmarks.spec.ts         # API performance
    pagination-benchmarks.spec.ts  # Pagination performance
    utils/
      stats.ts                     # Statistical analysis
      benchmark.ts                 # Benchmark utilities
      profiler.ts                  # Profiling utilities
    baseline.json                  # Baseline metrics
```

**Test Configuration:**

```javascript
// jest.performance.config.js
module.exports = {
  displayName: 'performance',
  testMatch: ['**/performance/**/*.spec.ts'],
  testEnvironment: 'jsdom',
  testTimeout: 60000, // 60 seconds (longer for benchmarks)

  // Disable parallel execution (performance tests need consistent environment)
  maxWorkers: 1,

  // Disable test randomization
  randomize: false,

  // Run performance tests only when explicitly requested
  // npm run test:performance
};
```

**Package.json Scripts:**

```json
{
  "scripts": {
    "test:performance": "jest --config jest.performance.config.js",
    "test:performance:baseline": "jest --config jest.performance.config.js && npm run performance:save-baseline",
    "performance:save-baseline": "node scripts/save-performance-baseline.js",
    "performance:compare": "node scripts/compare-performance.js"
  }
}
```

### 5.2 Test Data Generation

**Fixture Generator:**

```typescript
// scripts/generate-performance-fixtures.ts

interface FixtureConfig {
  observationCount: number;
  encoding: 'json' | 'text' | 'binary';
  schema: DataStreamSchema;
  outputPath: string;
}

async function generatePerformanceFixtures() {
  const schema = createSimpleSchema(); // 3 fields: time, temp, humidity

  const configs: FixtureConfig[] = [
    // JSON fixtures
    {
      observationCount: 10,
      encoding: 'json',
      schema,
      outputPath: 'fixtures/performance/observations-10-json.json',
    },
    {
      observationCount: 100,
      encoding: 'json',
      schema,
      outputPath: 'fixtures/performance/observations-100-json.json',
    },
    {
      observationCount: 1000,
      encoding: 'json',
      schema,
      outputPath: 'fixtures/performance/observations-1000-json.json',
    },
    {
      observationCount: 10000,
      encoding: 'json',
      schema,
      outputPath: 'fixtures/performance/observations-10000-json.json',
    },

    // Binary fixtures
    {
      observationCount: 10,
      encoding: 'binary',
      schema,
      outputPath: 'fixtures/performance/observations-10-binary.bin',
    },
    {
      observationCount: 100,
      encoding: 'binary',
      schema,
      outputPath: 'fixtures/performance/observations-100-binary.bin',
    },
    {
      observationCount: 1000,
      encoding: 'binary',
      schema,
      outputPath: 'fixtures/performance/observations-1000-binary.bin',
    },
    {
      observationCount: 10000,
      encoding: 'binary',
      schema,
      outputPath: 'fixtures/performance/observations-10000-binary.bin',
    },

    // Text fixtures
    {
      observationCount: 10,
      encoding: 'text',
      schema,
      outputPath: 'fixtures/performance/observations-10-text.csv',
    },
    {
      observationCount: 100,
      encoding: 'text',
      schema,
      outputPath: 'fixtures/performance/observations-100-text.csv',
    },
    {
      observationCount: 1000,
      encoding: 'text',
      schema,
      outputPath: 'fixtures/performance/observations-1000-text.csv',
    },
    {
      observationCount: 10000,
      encoding: 'text',
      schema,
      outputPath: 'fixtures/performance/observations-10000-text.csv',
    },
  ];

  for (const config of configs) {
    console.log(
      `Generating ${config.observationCount} observations (${config.encoding})...`
    );

    const observations = generateObservations(
      config.observationCount,
      config.schema
    );
    const encoded = encodeObservations(
      observations,
      config.encoding,
      config.schema
    );

    await fs.writeFile(config.outputPath, encoded);

    console.log(
      `  Written to ${config.outputPath} (${(encoded.length / 1024).toFixed(
        1
      )} KB)`
    );
  }
}

function generateObservations(
  count: number,
  schema: DataStreamSchema
): Observation[] {
  const observations: Observation[] = [];
  const startTime = new Date('2024-01-01T00:00:00Z').getTime();

  for (let i = 0; i < count; i++) {
    observations.push({
      phenomenonTime: new Date(startTime + i * 60000).toISOString(), // 1 min intervals
      result: {
        time: startTime + i * 60000,
        temp: 20 + Math.random() * 10, // 20-30°C
        humidity: 50 + Math.random() * 30, // 50-80%
      },
    });
  }

  return observations;
}
```

**Run Fixture Generation:**

```bash
npm run generate:performance-fixtures
```

### 5.3 Result Collection and Analysis

**Performance Report:**

```typescript
interface PerformanceReport {
  timestamp: string;
  environment: {
    browser: string;
    os: string;
    cpu: string;
    memory: string;
  };
  benchmarks: {
    [name: string]: {
      iterations: number;
      stats: PerformanceStats;
      target: number;
      passed: boolean;
      regression: boolean;
    };
  };
}

async function generatePerformanceReport(): Promise<PerformanceReport> {
  const report: PerformanceReport = {
    timestamp: new Date().toISOString(),
    environment: {
      browser: navigator.userAgent,
      os: navigator.platform,
      cpu: navigator.hardwareConcurrency + ' cores',
      memory: (navigator.deviceMemory || 'unknown') + ' GB',
    },
    benchmarks: {},
  };

  // Run all benchmarks
  const benchmarks = [
    { name: 'parse-json-100-obs', fn: () => parseJSON100, target: 10 },
    { name: 'parse-binary-100-obs', fn: () => parseBinary100, target: 5 },
    // ... more benchmarks
  ];

  for (const benchmark of benchmarks) {
    const stats = await runBenchmark(benchmark.fn, 100);
    const baseline = loadBaseline(benchmark.name);

    report.benchmarks[benchmark.name] = {
      iterations: 100,
      stats,
      target: benchmark.target,
      passed: stats.p95 < benchmark.target,
      regression: baseline ? detectRegression(stats, baseline) : false,
    };
  }

  return report;
}
```

**Report Output:**

```
Performance Test Report
=======================
Date: 2026-02-06T10:30:00Z
Environment: Chrome 130, Windows 11, 8 cores, 32GB

Benchmarks:
-----------
✅ parse-json-100-obs
   p50: 7.2ms | p95: 9.8ms | p99: 12.1ms
   Target: <10ms (p95)
   Status: PASSED

✅ parse-binary-100-obs
   p50: 3.5ms | p95: 4.8ms | p99: 6.2ms
   Target: <5ms (p95)
   Status: PASSED

✅ parse-json-1000-obs
   p50: 72.1ms | p95: 89.5ms | p99: 105.3ms
   Target: <100ms (p95)
   Status: PASSED

❌ parse-json-10000-obs
   p50: 820.3ms | p95: 1050.2ms | p99: 1210.5ms
   Target: <1000ms (p95)
   Status: FAILED (regression: +8.2% from baseline)

Summary:
--------
✅ 12 benchmarks passed
❌ 1 benchmark failed
⚠️ 1 regression detected
```

### 5.4 Regression Tracking

**Baseline Storage:**

```json
{
  "version": "1.0.0",
  "date": "2026-02-06",
  "git_commit": "abc123def456",
  "environment": {
    "browser": "Chrome 130",
    "os": "Windows 11"
  },
  "benchmarks": {
    "parse-json-100-obs": {
      "p95": 9.8,
      "unit": "ms"
    },
    "parse-binary-100-obs": {
      "p95": 4.8,
      "unit": "ms"
    }
  }
}
```

**Update Baseline Script:**

```typescript
// scripts/save-performance-baseline.ts

async function saveBaseline() {
  const report = await generatePerformanceReport();

  const baseline = {
    version: require('../package.json').version,
    date: new Date().toISOString(),
    git_commit: execSync('git rev-parse HEAD').toString().trim(),
    environment: report.environment,
    benchmarks: Object.fromEntries(
      Object.entries(report.benchmarks).map(([name, result]) => [
        name,
        { p95: result.stats.p95, unit: 'ms' },
      ])
    ),
  };

  await fs.writeFile(
    'test/performance/baseline.json',
    JSON.stringify(baseline, null, 2)
  );

  console.log('✅ Baseline saved to test/performance/baseline.json');
}
```

### 5.5 Performance Test Isolation

**Isolation Requirements:**

1. **No Parallel Execution:**

   - Performance tests must run sequentially (maxWorkers: 1)
   - Parallel tests compete for CPU/memory resources

2. **Environment Consistency:**

   - Close other applications
   - Disable background processes (e.g., antivirus, indexing)
   - Use dedicated CI runner for performance tests

3. **Warmup Iterations:**

   - First 10% of iterations discarded (JIT compilation, cache warmup)
   - Only measure steady-state performance

4. **Garbage Collection:**
   - Force GC before each test (if `--expose-gc` flag available)
   - Prevents GC pauses during measurement

**Warmup Implementation:**

```typescript
async function benchmarkWithWarmup<T>(
  fn: () => T | Promise<T>,
  iterations: number = 100,
  warmupPercent: number = 0.1
): Promise<PerformanceStats> {
  const warmupIterations = Math.floor(iterations * warmupPercent);
  const measureIterations = iterations - warmupIterations;

  // Warmup (discard results)
  for (let i = 0; i < warmupIterations; i++) {
    await fn();
  }

  // Force GC after warmup
  if (global.gc) global.gc();

  // Measure
  const times: number[] = [];
  for (let i = 0; i < measureIterations; i++) {
    const start = performance.now();
    await fn();
    const end = performance.now();
    times.push(end - start);
  }

  return calculateStats(times);
}
```

---

## 6. Performance Test Implementation Estimates

### 6.1 Test Implementation Summary

| Test Category               | Test Count   | Lines per Test | Total Lines     | Priority     | Fixtures Needed                |
| --------------------------- | ------------ | -------------- | --------------- | ------------ | ------------------------------ |
| **Parser Performance**      |
| JSON encoding benchmarks    | 4            | 30-40          | 120-160         | **CRITICAL** | 4 (10, 100, 1K, 10K obs)       |
| Text encoding benchmarks    | 4            | 30-40          | 120-160         | HIGH         | 4 (10, 100, 1K, 10K obs)       |
| Binary encoding benchmarks  | 4            | 30-40          | 120-160         | **CRITICAL** | 4 (10, 100, 1K, 10K obs)       |
| Binary vs JSON comparison   | 2            | 40-50          | 80-100          | HIGH         | 2 (100, 1K obs both encodings) |
| Complex schema benchmarks   | 2            | 40-50          | 80-100          | MEDIUM       | 2 (complex schemas)            |
| **Subtotal Parser**         | **16**       | **~35 avg**    | **520-680**     |              | **16 fixtures**                |
| **Worker Performance**      |
| Message overhead tests      | 2            | 30-40          | 60-80           | HIGH         | 0 (simple echo messages)       |
| Background parsing tests    | 3            | 40-50          | 120-150         | HIGH         | 3 (100, 1K, 10K obs)           |
| Worker vs Main comparison   | 2            | 40-50          | 80-100          | HIGH         | 2 (1K, 10K obs)                |
| Throughput tests            | 2            | 30-40          | 60-80           | MEDIUM       | 2 (1K obs batches)             |
| **Subtotal Worker**         | **9**        | **~37 avg**    | **320-410**     |              | **7 fixtures**                 |
| **Memory Usage**            |
| Parsing memory tests        | 4            | 35-45          | 140-180         | **CRITICAL** | 4 (100, 1K, 10K, 100K obs)     |
| Memory leak detection       | 2            | 40-50          | 80-100          | HIGH         | 2 (1K obs)                     |
| Peak memory tests           | 2            | 40-50          | 80-100          | MEDIUM       | 2 (1K, 10K obs)                |
| **Subtotal Memory**         | **8**        | **~40 avg**    | **300-380**     |              | **8 fixtures**                 |
| **API Performance**         |
| Collection operations       | 4            | 30-35          | 120-140         | HIGH         | 4 (mock server responses)      |
| Single resource operations  | 3            | 25-30          | 75-90           | MEDIUM       | 3 (mock server responses)      |
| Observation queries         | 3            | 35-45          | 105-135         | HIGH         | 3 (100, 1K, 10K obs)           |
| Relationship navigation     | 2            | 30-40          | 60-80           | MEDIUM       | 2 (mock server responses)      |
| **Subtotal API**            | **12**       | **~32 avg**    | **360-445**     |              | **12 fixtures**                |
| **Pagination Performance**  |
| Offset pagination tests     | 3            | 30-40          | 90-120          | MEDIUM       | 3 (page sizes)                 |
| Cursor pagination tests     | 3            | 30-40          | 90-120          | HIGH         | 3 (page sizes)                 |
| Full traversal tests        | 2            | 40-50          | 80-100          | MEDIUM       | 2 (1K, 10K items)              |
| **Subtotal Pagination**     | **8**        | **~35 avg**    | **260-340**     |              | **8 fixtures**                 |
| **Infrastructure**          |
| Statistical utilities       | 1 file       | 150-200        | 150-200         | **CRITICAL** | 0                              |
| Benchmark utilities         | 1 file       | 100-150        | 100-150         | **CRITICAL** | 0                              |
| Profiler utilities          | 1 file       | 80-120         | 80-120          | MEDIUM       | 0                              |
| Fixture generators          | 1 file       | 200-300        | 200-300         | HIGH         | 0                              |
| **Subtotal Infrastructure** | **4 files**  |                | **530-770**     |              | **0 fixtures**                 |
| **TOTAL**                   | **53 tests** | **~35 avg**    | **2,290-3,025** |              | **51 fixtures**                |

### 6.2 Infrastructure Implementation

| Component                      | Lines         | Priority     | Estimated Time  |
| ------------------------------ | ------------- | ------------ | --------------- |
| Statistical analysis utilities | 150-200       | **CRITICAL** | 2-3 hours       |
| Benchmark utilities            | 100-150       | **CRITICAL** | 2-3 hours       |
| Profiler utilities             | 80-120        | MEDIUM       | 1-2 hours       |
| Fixture generators             | 200-300       | HIGH         | 3-4 hours       |
| Baseline management scripts    | 100-150       | HIGH         | 2-3 hours       |
| Performance report generator   | 150-200       | MEDIUM       | 2-3 hours       |
| **Infrastructure Total**       | **780-1,120** |              | **12-18 hours** |

### 6.3 Fixture Requirements

| Fixture Category                         | Count   | Size Range        | Priority     |
| ---------------------------------------- | ------- | ----------------- | ------------ |
| **Observation Fixtures**                 |
| JSON (10 obs)                            | 1       | ~2 KB             | HIGH         |
| JSON (100 obs)                           | 1       | ~20 KB            | **CRITICAL** |
| JSON (1000 obs)                          | 1       | ~200 KB           | **CRITICAL** |
| JSON (10000 obs)                         | 1       | ~2 MB             | HIGH         |
| Binary (10 obs)                          | 1       | ~0.5 KB           | HIGH         |
| Binary (100 obs)                         | 1       | ~5 KB             | **CRITICAL** |
| Binary (1000 obs)                        | 1       | ~50 KB            | **CRITICAL** |
| Binary (10000 obs)                       | 1       | ~500 KB           | HIGH         |
| Text (10 obs)                            | 1       | ~0.8 KB           | MEDIUM       |
| Text (100 obs)                           | 1       | ~8 KB             | HIGH         |
| Text (1000 obs)                          | 1       | ~80 KB            | HIGH         |
| Text (10000 obs)                         | 1       | ~800 KB           | MEDIUM       |
| **Schema Fixtures**                      |
| Simple schema (3 fields)                 | 1       | ~1 KB             | **CRITICAL** |
| Complex schema (15+ fields)              | 1       | ~5 KB             | MEDIUM       |
| Nested schema (DataRecord in DataRecord) | 1       | ~3 KB             | MEDIUM       |
| **Mock Server Fixtures**                 |
| Systems collection                       | 5       | ~10-100 KB        | HIGH         |
| Observations collection                  | 5       | ~20-200 KB        | HIGH         |
| **TOTAL**                                | **~25** | **~3.5 MB total** |              |

### 6.4 Total Implementation Effort

| Component                    | Lines                 | Priority          | Estimated Time  |
| ---------------------------- | --------------------- | ----------------- | --------------- |
| Parser performance tests     | 520-680               | **CRITICAL**      | 10-14 hours     |
| Worker performance tests     | 320-410               | HIGH              | 6-8 hours       |
| Memory usage tests           | 300-380               | **CRITICAL**      | 6-8 hours       |
| API performance tests        | 360-445               | HIGH              | 7-9 hours       |
| Pagination performance tests | 260-340               | MEDIUM            | 5-7 hours       |
| Infrastructure               | 780-1,120             | **CRITICAL/HIGH** | 12-18 hours     |
| **TOTAL**                    | **2,540-3,375 lines** |                   | **46-64 hours** |

**Total Implementation Effort:** ~2-3 weeks (1 developer)

---

## 7. Testing Priorities

### Priority 1: CRITICAL (Must Have)

**What:** Parser performance (JSON/Binary), memory usage tests, statistical utilities

**Why:** Parsers are most performance-critical, memory leaks cause browser crashes

**Tests:** 28 tests, ~970-1,260 lines

**Deliverables:**

- JSON encoding parser benchmarks (4 tests, 120-160 lines)
- Binary encoding parser benchmarks (4 tests, 120-160 lines)
- Memory usage tests (8 tests, 300-380 lines)
- Statistical analysis utilities (150-200 lines)
- Benchmark utilities (100-150 lines)
- Fixture generators (200-300 lines)

### Priority 2: HIGH (Should Have)

**What:** Worker performance, API performance, pagination tests, baseline management

**Why:** Worker efficiency affects UI responsiveness, API calls are user-visible

**Tests:** 29 tests, ~940-1,195 lines

**Deliverables:**

- Worker performance tests (9 tests, 320-410 lines)
- API performance tests (12 tests, 360-445 lines)
- Cursor pagination tests (3 tests, 90-120 lines)
- Baseline management scripts (100-150 lines)
- Performance report generator (150-200 lines)

### Priority 3: MEDIUM (Nice to Have)

**What:** Complex schema benchmarks, offset pagination, profiling utilities

**Why:** Edge cases and advanced scenarios, less frequently used

**Tests:** 12 tests, ~420-570 lines

**Deliverables:**

- Complex schema benchmarks (2 tests, 80-100 lines)
- Offset pagination tests (3 tests, 90-120 lines)
- Peak memory tests (2 tests, 80-100 lines)
- Profiler utilities (80-120 lines)

---

## 8. Key Testing Challenges and Mitigations

### Challenge 1: Environment Variability

**Problem:** Performance varies across browsers, CPUs, memory, operating systems.

**Impact:** Benchmarks not reproducible across environments.

**Mitigation:**

- Establish baseline on single reference environment
- Document environment (browser, OS, CPU, memory) in baseline
- Run performance tests on dedicated CI runner (consistent environment)
- Report percentiles (p95) instead of absolute values (more robust to variability)
- Use performance ratios (Binary/JSON speedup) instead of absolute times

### Challenge 2: Statistical Significance

**Problem:** Single-run performance measurements are unreliable (variance due to GC, CPU throttling, background processes).

**Impact:** False positives/negatives in regression detection.

**Mitigation:**

- Run benchmarks 50-100 iterations
- Report p95/p99 percentiles (not just mean)
- Discard warmup iterations (first 10%)
- Force GC before each test (if available)
- Use >10% regression threshold (not overly sensitive)

### Challenge 3: Large Fixture Generation

**Problem:** Generating large fixtures (10,000+ observations) is time-consuming and expensive.

**Impact:** Fixture generation slows down development, fixtures too large for version control.

**Mitigation:**

- Generate fixtures programmatically (scripts, not manual)
- Store only small fixtures in Git (10, 100, 1000 obs)
- Generate large fixtures (10,000+) on-demand during tests
- Use compression for large binary fixtures
- Document fixture generation process

### Challenge 4: Worker Message Overhead

**Problem:** Worker message passing adds latency (5-20ms) that can negate parsing speedup for small datasets.

**Impact:** Worker may be slower than main thread for small datasets.

**Mitigation:**

- Measure total time (parsing + message overhead)
- Document when Worker is faster vs slower
- Provide guidance on when to use Worker (dataset size threshold)
- Test both Worker and main thread performance

### Challenge 5: Memory Measurement Limitations

**Problem:** Memory API only available in Chrome, requires `--expose-gc` flag.

**Impact:** Memory tests can't run in all browsers, limited CI environment support.

**Mitigation:**

- Mark memory tests as Chrome-only (skip in other browsers)
- Document `--expose-gc` requirement for memory tests
- Provide alternative memory leak detection (heap snapshots)
- Run memory tests manually (not in CI)

---

## 9. Performance Test Execution Strategy

### 9.1 When to Run Performance Tests

**During Development:**

- **Unit tests:** Always (fast, every commit)
- **Performance tests:** Occasionally (slow, when optimizing)

**In CI/CD:**

- **Pull Requests:** No (too slow, environment variability)
- **Nightly Builds:** Yes (consistent environment, baseline comparison)
- **Release Candidates:** Yes (validate no regressions before release)

**Manual:**

- **Before optimizations:** Establish baseline
- **After optimizations:** Verify improvements
- **Performance regression investigation:** Identify hotspots

### 9.2 Test Execution Commands

```bash
# Run all performance tests
npm run test:performance

# Run specific performance suite
npm run test:performance -- parser-benchmarks
npm run test:performance -- worker-benchmarks
npm run test:performance -- memory-benchmarks

# Establish new baseline
npm run test:performance:baseline

# Compare current performance with baseline
npm run test:performance && npm run performance:compare

# Run with profiling (Chrome DevTools)
npm run test:performance:profile
```

### 9.3 CI/CD Integration

```yaml
# .github/workflows/nightly-performance.yml
name: Nightly Performance Tests

on:
  schedule:
    - cron: '0 2 * * *' # Daily at 2 AM UTC

jobs:
  performance:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Setup Node
        uses: actions/setup-node@v3
        with:
          node-version: '20'

      - name: Install dependencies
        run: npm ci

      - name: Generate performance fixtures
        run: npm run generate:performance-fixtures

      - name: Run performance tests
        run: npm run test:performance

      - name: Compare with baseline
        id: compare
        run: npm run performance:compare
        continue-on-error: true

      - name: Upload performance report
        uses: actions/upload-artifact@v3
        with:
          name: performance-report
          path: test/performance/report.json

      - name: Comment on regression
        if: steps.compare.outputs.regression == 'true'
        uses: actions/github-script@v6
        with:
          script: |
            github.rest.issues.create({
              owner: context.repo.owner,
              repo: context.repo.repo,
              title: '⚠️ Performance Regression Detected',
              body: 'Nightly performance tests detected a regression. See attached report for details.',
              labels: ['performance', 'regression']
            });
```

---

## 10. References

### 10.1 Related Research Documents

- **Section 10:** SWE Common Testing Requirements (parser testing foundation)
- **Section 16:** Worker Extensions Testing (Worker performance context)
- **Section 23:** Pagination Testing (large collection traversal performance)
- **Section 30:** Bulk Operations Testing (large batch performance)

### 10.2 Performance Testing Resources

**Browser APIs:**

- [Performance API (MDN)](https://developer.mozilla.org/en-US/docs/Web/API/Performance)
- [Performance Timing API (MDN)](https://developer.mozilla.org/en-US/docs/Web/API/Performance/timing)
- [Memory API (Chrome)](https://developer.chrome.com/docs/devtools/memory-problems/)

**Performance Testing Best Practices:**

- [Web Performance Best Practices (web.dev)](https://web.dev/performance/)
- [JavaScript Performance (MDN)](https://developer.mozilla.org/en-US/docs/Web/Performance)
- [Benchmarking JavaScript](https://calendar.perfplanet.com/2022/benchmarking-javascript/)

**Statistical Analysis:**

- [Percentile Metrics](https://blog.cloudflare.com/a-tour-inside-cloudflares-latency-tools/)
- [Performance Percentiles Explained](https://www.circonus.com/2018/11/the-problem-with-percentiles/)

---

## 11. Summary and Next Steps

### Research Summary

**Performance Requirements Defined:**

- Parser performance targets (JSON, Text, Binary) for 10-10,000 observations
- Worker performance targets (message overhead, throughput)
- API performance targets (collections, observations, pagination)
- Memory usage targets (1000-100,000 observations)

**Benchmark Scenarios Designed:**

- 16 parser performance benchmarks (JSON/Text/Binary, various sizes)
- 9 Worker performance benchmarks (overhead, background parsing, throughput)
- 8 memory usage benchmarks (parsing memory, leak detection, peak memory)
- 12 API performance benchmarks (collections, single resources, observations)
- 8 pagination performance benchmarks (offset, cursor, traversal)

**Measurement Strategy:**

- Statistical analysis (p50, p95, p99 percentiles)
- Baseline establishment and regression detection (>10% threshold)
- Profiling utilities (performance.mark, Chrome DevTools)
- Environment consistency (dedicated CI runner, single-worker execution)

**Test Infrastructure:**

- 53 performance tests (~2,290-3,025 lines)
- 4 infrastructure files (~780-1,120 lines)
- 51 performance fixtures (~3.5 MB total)
- Baseline management and performance reporting

**Total Estimated Effort:** 46-64 hours (2-3 weeks, 1 developer)

### Next Steps

**Immediate (Priority 1 - CRITICAL):**

1. Implement statistical analysis utilities (150-200 lines)
2. Implement benchmark utilities (100-150 lines)
3. Generate performance fixtures (25 fixtures, 3.5 MB)
4. Implement parser performance benchmarks (520-680 lines, 16 tests)
5. Implement memory usage tests (300-380 lines, 8 tests)

**Short-Term (Priority 2 - HIGH):** 6. Implement Worker performance benchmarks (320-410 lines, 9 tests) 7. Implement API performance benchmarks (360-445 lines, 12 tests) 8. Implement baseline management scripts (100-150 lines) 9. Set up CI/CD performance testing (nightly builds)

**Long-Term (Priority 3 - MEDIUM):** 10. Implement complex schema benchmarks (80-100 lines, 2 tests) 11. Implement pagination performance tests (260-340 lines, 8 tests) 12. Implement profiling utilities (80-120 lines) 13. Optimize based on profiling results

**Documentation:** 14. Update Implementation Guide with performance testing strategy 15. Document performance targets and baseline establishment process 16. Create performance testing runbook for developers

---

**END OF DOCUMENT**
