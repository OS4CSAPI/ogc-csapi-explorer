# CSAPI Explorer Smoke Test: 44/44 Full Pass Report

**Date:** February 28, 2026  
**Result:** ✅ **ALL 44 STEPS PASSED — 0 FAILED — 0 SKIPPED — 33.2 seconds**  
**Target Server:** Oracle Cloud OSH (OS4CSAPI) via Cloudflare Pages proxy  
**Deployment URL:** `https://ogc-csapi-explorer.pages.dev/smoke-test`  
**Server URL:** `https://os4csapi-osh.duckdns.org/sensorhub/api` (proxied through CF Pages Functions)

---

## Executive Summary

After an extended multi-session debugging effort spanning multiple days, the CSAPI Explorer CRUD Smoke Test achieved a **perfect 44/44 pass rate** against the Oracle Cloud OpenSensorHub deployment. This required diagnosing and fixing issues across four distinct layers: the client-side smoke test logic, the Cloudflare Pages proxy, the Oracle Cloud server build, and the upstream osh-core source code.

The journey went from **3 initial failures cascading to 41/44** → **33 pass / 2 fail / 9 skip** → **44/44 all pass**.

---

## Final Test Results

### Summary
| Metric | Value |
|--------|-------|
| Total Steps | 44 |
| Passed | 44 |
| Failed | 0 |
| Skipped | 0 |
| Total Time | 33.2s |

### Results by Resource Type
| Resource Type | Pass | Fail | Skip | Time |
|--------------|------|------|------|------|
| System | 5 | 0 | 0 | 459ms |
| Procedure | 5 | 0 | 0 | 381ms |
| Deployment | 5 | 0 | 0 | 354ms |
| Sampling Feature | 5 | 0 | 0 | 370ms |
| Subsystem | 5 | 0 | 0 | 395ms |
| Subdeployment | 5 | 0 | 0 | 434ms |
| Datastream | 5 | 0 | 0 | 576ms |
| Control Stream | 5 | 0 | 0 | 416ms |
| Observation | 3 | 0 | 0 | 217ms |
| Command | 1 | 0 | 0 | 29.6s |

### Operations Breakdown
| Operation | Count |
|-----------|-------|
| CREATE | 10 |
| READ | 9 |
| UPDATE | 8 |
| VERIFY | 8 |
| DELETE | 9 |

---

## The Journey: From Failure to Full Pass

### Phase 1: Initial Diagnosis (Starting Point: 3/44 Failures)

The smoke test was initially failing 3 out of 44 steps when run against the live Oracle Cloud OSH deployment. These 3 failures caused cascade failures across 9 dependent steps, resulting in only 32/44 passing.

**Root causes identified:**

1. **Oracle Cloud JVM Cold-Start 500 Errors** — The Oracle Cloud VM runs a free-tier ARM instance. After periods of inactivity, the first few API requests would return HTTP 500 errors as the JVM warmed up. These were transient and would resolve after 2-3 requests.

2. **Orphaned Resource UID Collisions** — Previous failed test runs left orphaned resources in the database. When subsequent test runs tried to CREATE resources with the same UIDs, the server would reject them as duplicates.

3. **Command Rejection (No Driver)** — The test server has no physical sensor driver attached, so sending commands to a ControlStream would result in rejection with messages like "No driver connected" or "Cannot reach system". This is expected behavior for a test server but was being treated as a failure.

### Phase 2: Client-Side Fixes (Commit `f4996dc`)

**Fix 1: `apiFetchWithRetry()` — Retry Logic**
```typescript
async function apiFetchWithRetry(url, options, retries = 2, delay = 800) {
  for (let attempt = 0; attempt <= retries; attempt++) {
    const res = await apiFetch(url, options);
    if (res.status !== 500 || attempt === retries) return res;
    await new Promise(r => setTimeout(r, delay));
  }
}
```
All API calls in the smoke test now retry up to 2 times on HTTP 500, with 800ms backoff. This eliminates JVM cold-start failures.

**Fix 2: `preClean()` — Orphan Purge**
A "Pre-Clean" button was added to the toolbar that queries all resource types and deletes any existing resources before the test begins. This prevents UID collisions from previous failed runs.

**Fix 3: `runAllSteps()` — Automated Execution**
A "Run All" button was added that automatically executes all 44 steps in sequence after the initial "Begin Test" setup, eliminating the need to manually click through each step.

**Fix 4: Timestamped UIDs**
All resource UIDs now include `Date.now()` suffixes (e.g., `urn:test:system:smoke-1740789012345`) to prevent collisions even without pre-cleaning.

**Fix 5: Broadened Command Skip Handling**
The command CREATE step now gracefully handles multiple rejection patterns:
```typescript
if (/no driver|cannot reach|not connected|unavailable|unable to forward/i.test(body))
```
These are treated as expected "skip" results rather than failures.

### Phase 3: UI Improvements (Commit `40e7a31`)

**Warm Up Button**
Added a "Warm Up" button that pings the server 6 times and signals readiness when 2 consecutive responses come back in under 1.5 seconds. This ensures the JVM is warm before testing begins.

**Toolbar Reorder**
The toolbar was reorganized for logical workflow:
```
Pre-Clean | Warm Up | [divider] | Begin Test | Run All | Reset
```

**DELETE Badge Restyle**
DELETE operation badges were restyled from red to purple to distinguish them from failure indicators.

### Phase 4: First Live Test Run (Result: 33/44 pass, 2 fail, 9 skip)

Running against the DigitalOcean OSH server via `https://ogc-csapi-explorer.pages.dev/smoke-test`, two failures remained:

**Failure 1: SamplingFeature CREATE → HTTP 500**
The DigitalOcean server's `/samplingFeatures` endpoint was completely broken — even a bare GET request returned 500. This is a server-side bug, not a client issue.

**Failure 2: ControlStream CREATE → HTTP 500**
The smoke test was sending `paramsSchema` in the ControlStream creation payload, but the DO server expected `parametersSchema`. The servers had divergent property names.

### Phase 5: Schema Property Name Detective Work

This was the most technically interesting part of the investigation.

**The Discovery:**
- **DigitalOcean server** accepts ONLY `parametersSchema` (returns 500 on `paramsSchema`)
- **Oracle Cloud server** accepts ONLY `paramsSchema` (returns 500 on `parametersSchema`)
- Both servers run OpenSensorHub, ostensibly from the same source code

**The Question:** Why would two servers from the same codebase have mutually exclusive property names?

**Auto-Detect Fix (Commit `b30ff98`):**
As an immediate workaround, the smoke test was updated with auto-detection logic:
```typescript
const detectedSchemaKey = ref<string>('');

async function detectSchemaKey() {
  // Try parametersSchema first (newer standard)
  const res1 = await tryCreate('parametersSchema');
  if (res1.ok) { detectedSchemaKey.value = 'parametersSchema'; return; }
  // Fall back to paramsSchema (older)
  const res2 = await tryCreate('paramsSchema');
  if (res2.ok) { detectedSchemaKey.value = 'paramsSchema'; return; }
}
```
The SamplingFeature server-side 500 was also handled with a graceful skip.

### Phase 6: The SSH Investigation — Root Cause Found

The user challenged why the servers were different, noting that the Oracle server had been installed that same day. An SSH investigation into the Oracle Cloud VM (`129.80.248.53`) revealed the definitive answer.

**Oracle Cloud VM Forensics:**

```
SSH: ubuntu@129.80.248.53
Build dir: /opt/osh-build (cloned from opensensorhub/osh-node-dev-template @ f8f2085)
osh-core submodule: commit e74e12e2c (tag: v2.0-beta1-2211-ge74e12e2c)
Date of deployed commit: April 7, 2025
```

**Source Code Evidence:**

File: `CommandStreamSchemaBindingJson.java`
- Line 92: `if ("paramsSchema".equals(prop))` — reads `paramsSchema`
- Line 144: `writer.name("paramsSchema");` — writes `paramsSchema`
- **No occurrence of `parametersSchema` anywhere in the deployed source**

**The Rename Commit:**

```
git diff e74e12e2c origin/master -- .../CommandStreamSchemaBindingJson.java

-  if ("paramsSchema".equals(prop))
+  if ("parametersSchema".equals(prop))

-  writer.name("paramsSchema");
+  writer.name("parametersSchema");
```

**Commit:** `5f59b5b69` — *"[CSAPI] Update JSON property names for control streams and commands (#318). Closes #272"*  
**Date:** October 22, 2025  
**Location:** `opensensorhub/osh-core` repository

**Timeline:**
| Date | Event |
|------|-------|
| Apr 7, 2025 | osh-core commit `e74e12e2c` — uses `paramsSchema` |
| Oct 22, 2025 | PR #318 merged — renames to `parametersSchema` |
| Feb 28, 2026 | Oracle VM built from template pinning `e74e12e2c` (6 months stale) |

The `osh-node-dev-template` repository pinned its osh-core submodule to `e74e12e2c`, which **predated** the rename by 6 months. The DigitalOcean server was built from a newer version that included the rename. This was not an installation error — the build template itself pointed to the older submodule.

### Phase 7: The Server Rebuild — Oracle Cloud Updated

Rather than relying on the auto-detect workaround, the Oracle server was rebuilt from the latest osh-core master.

**Steps performed:**

1. **Updated osh-core submodule:**
   ```bash
   cd /opt/osh-build/include/osh-core
   sudo git checkout origin/master  # e74e12e2c → 482891d6c (+94 commits)
   ```

2. **Cleaned build caches:**
   ```bash
   sudo find /opt/osh-build/include/osh-core -type d -name build -exec rm -rf {} +
   sudo rm -rf /opt/osh-build/include/osh-core/.gradle
   ```

3. **Full rebuild from source:**
   ```bash
   cd /opt/osh-build
   sudo ./gradlew installDist --no-daemon --console=plain
   # BUILD SUCCESSFUL — 49 tasks, full GWT widgetset recompilation
   ```

4. **Verified rename in compiled JAR:**
   ```bash
   strings sensorhub-service-consys-2.0-beta2.jar | grep parametersSchema
   # Output: parametersSchema  ✅
   ```

5. **Deployed and restarted:**
   ```bash
   sudo systemctl stop sensorhub
   sudo cp -r /opt/sensorhub/lib /opt/sensorhub/lib.bak  # backup
   sudo rm /opt/sensorhub/lib/*.jar
   sudo cp /opt/osh-build/build/install/osh-node/lib/*.jar /opt/sensorhub/lib/  # 78 JARs
   sudo systemctl start sensorhub
   ```

6. **Verified server health:**
   ```bash
   curl -s -u ogc:ogc http://localhost:8181/sensorhub/api | grep title
   # "title": "Connected Systems API Service"  ✅
   ```

**Result:** Oracle server now runs osh-core @ `482891d6c` (latest master) with `parametersSchema` — matching the DigitalOcean server exactly.

### Phase 8: The Final Run — 44/44 PASS ✅

With the Oracle server rebuilt and all client-side fixes in place, the smoke test was executed one final time:

**Pre-Clean → Warm Up → Run All**

```
✅ CRUD Smoke Test — Stop 44/44 — 44 pass
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        44          44           0           0        33.2s
   TOTAL STEPS    PASSED      FAILED      SKIPPED   TOTAL TIME
```

**Every single resource type passed every single operation:**
- System: CREATE ✅ READ ✅ UPDATE ✅ VERIFY ✅ DELETE ✅
- Procedure: CREATE ✅ READ ✅ UPDATE ✅ VERIFY ✅ DELETE ✅
- Deployment: CREATE ✅ READ ✅ UPDATE ✅ VERIFY ✅ DELETE ✅
- Sampling Feature: CREATE ✅ READ ✅ UPDATE ✅ VERIFY ✅ DELETE ✅
- Subsystem: CREATE ✅ READ ✅ UPDATE ✅ VERIFY ✅ DELETE ✅
- Subdeployment: CREATE ✅ READ ✅ UPDATE ✅ VERIFY ✅ DELETE ✅
- Datastream: CREATE ✅ READ ✅ UPDATE ✅ VERIFY ✅ DELETE ✅
- Control Stream: CREATE ✅ READ ✅ UPDATE ✅ VERIFY ✅ DELETE ✅
- Observation: CREATE ✅ READ ✅ DELETE ✅
- Command: CREATE ✅

---

## Architecture Overview

### System Topology
```
┌──────────────────────────────────────────────────────────┐
│  Browser: https://ogc-csapi-explorer.pages.dev/smoke-test │
│  (Vue 3 SPA on Cloudflare Pages)                          │
└────────────────────┬─────────────────────────────────────┘
                     │ HTTPS
                     ▼
┌──────────────────────────────────────────────────────────┐
│  Cloudflare Pages Functions (Reverse Proxy)               │
│  /api/osh/*   → https://os4csapi-osh.duckdns.org/...     │
│  /api/osh-do/* → http://45.55.99.236:8080/...            │
└────────────────────┬─────────────────────────────────────┘
                     │ HTTPS (via Caddy)
                     ▼
┌──────────────────────────────────────────────────────────┐
│  Oracle Cloud VM (129.80.248.53)                          │
│  Caddy reverse proxy → SensorHub on port 8181             │
│  osh-core @ 482891d6c (latest master)                     │
│  sensorhub-service-consys-2.0-beta2.jar                   │
│  Java 17 (OpenJDK 17.0.18)                                │
│  Ubuntu, ARM64 (free tier)                                │
└──────────────────────────────────────────────────────────┘
```

### Key Files Modified
| File | Purpose |
|------|---------|
| `demo/src/pages/SmokeTestPage.vue` | Main smoke test page (~2052 lines) |
| `demo/functions/api/[...path].ts` | CF Pages proxy function |
| `src/ogc-api/csapi/formats/schema-response.ts` | Schema response parser (dual-name fallback) |
| `demo/src/csapi-bridge.ts` | CSAPI bridge utilities |

### Commits (Chronological)
| Commit | Description |
|--------|-------------|
| `f4996dc` | Retry logic, pre-clean, run-all, timestamped UIDs, command skip handling |
| `9a082a5` | Reverted `params` → `parameters` in command payload (corrected hallucinated fix) |
| `40e7a31` | Warm Up button, toolbar reorder, DELETE badge restyle |
| `b30ff98` | Auto-detect schema key, SamplingFeature graceful skip |

---

## Bugs Found & Reported

### 1. osh-core Property Name Divergence (PR #318 / Issue #272)
- **What:** `paramsSchema` was renamed to `parametersSchema` in osh-core PR #318 (Oct 2025), but the `osh-node-dev-template` still pins a pre-rename submodule
- **Impact:** Any server built from the template uses the old name; pre-built distributions use the new name
- **Status:** Fixed by rebuilding Oracle server from latest master
- **Upstream:** Already tracked as opensensorhub/osh-core#272 (closed by PR #318)

### 2. DigitalOcean SamplingFeature Endpoint Broken
- **What:** `GET /samplingFeatures` returns HTTP 500 on the DO server
- **Impact:** SamplingFeature CRUD operations fail server-side
- **Status:** Handled with graceful skip in smoke test; server-side fix needed

### 3. Issue #140 Validation
- **What:** GitHub issue #140 on `OS4CSAPI/ogc-client-CSAPI_2` contained claims about property name divergence
- **Validated Claims:** `paramsSchema` → `parametersSchema` fix in `schema-response.ts` (CORRECT)
- **Invalidated Claims:** `params` → `parameters` in command payloads (FALSE — DO rejects `params`, accepts `parameters`; the server was already correct)
- **Status:** Validation comment posted on issue #140

---

## Lessons Learned

### 1. Submodule Pinning Creates Silent Drift
The root cause of the entire property name divergence was a git submodule pinned to a 6-month-old commit. The template repo looked correct, the build succeeded, the server ran — but it was silently using outdated JSON property names. This is a systemic risk with submodule-based build systems.

### 2. Live Testing Reveals What Unit Tests Cannot
The property name divergence was invisible to unit tests (which test against the same build) and to local development (which uses mocks). Only live cross-server testing revealed the mismatch.

### 3. Retry Logic Is Essential for Cloud Deployments
Free-tier cloud VMs have JVM cold-start latency. Any test suite that hits a cloud-deployed Java service needs retry logic with backoff, or it will produce false failures.

### 4. Pre-Clean Is Critical for Idempotent Tests
CRUD smoke tests are inherently stateful. Without cleaning up resources from failed runs, subsequent runs will fail on duplicate UIDs. The pre-clean pattern should be standard for any stateful integration test.

### 5. Validate AI-Generated Issue Claims
Issue #140 contained a claim that was validated as FALSE (the `params` → `parameters` rename). AI-assisted issue filing requires human verification of each claim.

---

## Server Configuration Reference

### Oracle Cloud OSH
| Property | Value |
|----------|-------|
| IP | 129.80.248.53 |
| SSH User | ubuntu |
| SSH Key | `~/.ssh/oracle-osh.pem` |
| SensorHub Port | 8181 |
| Public URL | `https://os4csapi-osh.duckdns.org/sensorhub/api` |
| Credentials | `os4csapi:ogc134mm` (public), `ogc:ogc` (direct) |
| Build Dir | `/opt/osh-build` |
| Install Dir | `/opt/sensorhub` |
| Service | `sensorhub.service` (systemd) |
| Java | OpenJDK 17.0.18 (ARM64) |
| osh-core | `482891d6c` (latest master as of Feb 28, 2026) |
| Reverse Proxy | Caddy |

### DigitalOcean OSH
| Property | Value |
|----------|-------|
| IP | 45.55.99.236 |
| Port | 8080 |
| Public URL | `http://45.55.99.236:8080/sensorhub/api` |
| Credentials | `admin:admin` |
| Build | Pre-built distribution (includes PR #318 rename) |

---

## Appendix A: The 44 Test Steps

| # | Resource Type | Operation | Status |
|---|--------------|-----------|--------|
| 1 | System | CREATE | ✅ PASS |
| 2 | System | READ | ✅ PASS |
| 3 | System | UPDATE | ✅ PASS |
| 4 | System | VERIFY | ✅ PASS |
| 5 | Procedure | CREATE | ✅ PASS |
| 6 | Procedure | READ | ✅ PASS |
| 7 | Procedure | UPDATE | ✅ PASS |
| 8 | Procedure | VERIFY | ✅ PASS |
| 9 | Deployment | CREATE | ✅ PASS |
| 10 | Deployment | READ | ✅ PASS |
| 11 | Deployment | UPDATE | ✅ PASS |
| 12 | Deployment | VERIFY | ✅ PASS |
| 13 | Sampling Feature | CREATE | ✅ PASS |
| 14 | Sampling Feature | READ | ✅ PASS |
| 15 | Sampling Feature | UPDATE | ✅ PASS |
| 16 | Sampling Feature | VERIFY | ✅ PASS |
| 17 | Subsystem | CREATE | ✅ PASS |
| 18 | Subsystem | READ | ✅ PASS |
| 19 | Subsystem | UPDATE | ✅ PASS |
| 20 | Subsystem | VERIFY | ✅ PASS |
| 21 | Subdeployment | CREATE | ✅ PASS |
| 22 | Subdeployment | READ | ✅ PASS |
| 23 | Subdeployment | UPDATE | ✅ PASS |
| 24 | Subdeployment | VERIFY | ✅ PASS |
| 25 | Datastream | CREATE | ✅ PASS |
| 26 | Datastream | READ | ✅ PASS |
| 27 | Datastream | UPDATE | ✅ PASS |
| 28 | Datastream | VERIFY | ✅ PASS |
| 29 | Control Stream | CREATE | ✅ PASS |
| 30 | Control Stream | READ | ✅ PASS |
| 31 | Control Stream | UPDATE | ✅ PASS |
| 32 | Control Stream | VERIFY | ✅ PASS |
| 33 | Observation | CREATE | ✅ PASS |
| 34 | Observation | READ | ✅ PASS |
| 35 | Command | CREATE | ✅ PASS |
| 36 | Datastream | DELETE | ✅ PASS |
| 37 | Control Stream | DELETE | ✅ PASS |
| 38 | System | DELETE | ✅ PASS |
| 39 | Procedure | DELETE | ✅ PASS |
| 40 | Deployment | DELETE | ✅ PASS |
| 41 | Sampling Feature | DELETE | ✅ PASS |
| 42 | Observation | DELETE | ✅ PASS |
| 43 | Subdeployment | DELETE | ✅ PASS |
| 44 | Subsystem | DELETE | ✅ PASS |

---

## Appendix B: Key Code — `apiFetchWithRetry()`

```typescript
/**
 * Wrapper around apiFetch that retries on HTTP 500 errors.
 * Handles JVM cold-start transient failures on Oracle Cloud.
 */
async function apiFetchWithRetry(
  url: string,
  options: RequestInit,
  retries = 2,
  delay = 800
): Promise<Response> {
  for (let attempt = 0; attempt <= retries; attempt++) {
    const res = await apiFetch(url, options);
    if (res.status !== 500 || attempt === retries) return res;
    console.warn(`Retry ${attempt + 1}/${retries} after 500 from ${url}`);
    await new Promise(r => setTimeout(r, delay));
  }
  // Unreachable, but TypeScript needs it
  return apiFetch(url, options);
}
```

## Appendix C: Key Code — Schema Key Auto-Detection

```typescript
/**
 * Detects whether the server uses 'parametersSchema' (post-PR#318)
 * or 'paramsSchema' (pre-PR#318). Caches the result for the session.
 */
const detectedSchemaKey = ref<string>('');

function makeControlStreamPayload(): object {
  const schemaKey = detectedSchemaKey.value || 'parametersSchema';
  return {
    name: `Test ControlStream ${Date.now()}`,
    inputName: 'test-command-input',
    schema: {
      commandFormat: 'application/json',
      [schemaKey]: {
        type: 'DataRecord',
        label: 'Test Command Parameters',
        fields: [/* ... */]
      }
    }
  };
}
```

## Appendix D: Oracle Server Rebuild Commands

```bash
# 1. Update osh-core submodule to latest master
cd /opt/osh-build/include/osh-core
sudo git fetch origin
sudo git checkout origin/master
# e74e12e2c (Apr 2025) → 482891d6c (Feb 2026, +94 commits)

# 2. Clean all build caches
sudo find /opt/osh-build/include/osh-core -type d -name build -exec rm -rf {} +
sudo rm -rf /opt/osh-build/include/osh-core/.gradle

# 3. Full rebuild
cd /opt/osh-build
sudo ./gradlew installDist --no-daemon --console=plain
# BUILD SUCCESSFUL — 49 tasks

# 4. Verify rename in compiled JAR
strings build/install/osh-node/lib/sensorhub-service-consys-2.0-beta2.jar | grep parametersSchema
# Output: parametersSchema ✅

# 5. Stop service, deploy, restart
sudo systemctl stop sensorhub
sudo cp -r /opt/sensorhub/lib /opt/sensorhub/lib.bak
sudo rm /opt/sensorhub/lib/*.jar
sudo cp /opt/osh-build/build/install/osh-node/lib/*.jar /opt/sensorhub/lib/
sudo cp -r /opt/osh-build/build/install/osh-node/web/* /opt/sensorhub/web/
sudo systemctl start sensorhub

# 6. Verify
curl -s -u ogc:ogc http://localhost:8181/sensorhub/api | grep title
# "title": "Connected Systems API Service" ✅
```

---

*Report generated February 28, 2026. All 44 CRUD smoke test steps passing against live Oracle Cloud OSH deployment.*
