# Findings: OSH Server Property Name Divergence — `paramsSchema`/`params` vs `parametersSchema`/`parameters`

> **Research Plan Reference:** Ad-hoc investigation during Oracle Cloud smoke testing
> **Research Questions Answered:** 4 of 4
> **Status:** Complete | Branch: `phase-6`

| Metadata         | Value                                                    |
| ---------------- | -------------------------------------------------------- |
| Research Start   | 2026-02-27                                               |
| Research End     | 2026-02-28                                               |
| Actual Time      | ~4 hours (across smoke test debugging sessions)          |
| Methodology      | Bytecode decompilation (`javap -c -p`), live server testing, cross-server comparison, source code analysis |

---

## Sources Consulted

### Primary Sources

- **Oracle Cloud OSH server JARs** (`/opt/sensorhub/lib/`) — bytecode decompilation of compiled `.class` files inside JAR archives using `javap -c -p`
- **osh-core source** (`/opt/osh-build/osh-core` @ commit `e74e12e2`) — Java source for `CommandStreamSchemaBindingJson.java` and `CommandBindingJson.java`
- **osh-addons source** (`/opt/osh-build/osh-addons` @ commit `126018e2`) — compiled JARs used on Oracle Cloud server
- **DigitalOcean OSH server** (`45.55.99.236:8080`) — live testing showing DIFFERENT property names than Oracle Cloud
- **ogc-csapi-explorer smoke test** (`demo/src/pages/SmokeTestPage.vue`) — 44-step automated CRUD test

### Supporting Sources

- **OGC 23-002** (Connected Systems Part 2) — defines `parametersSchema` and `parameters` as canonical property names
- **camptocamp/ogc-client PR #136** — upstream PR with `parseControlStreamSchemaResponse()` that only accepts `parametersSchema`
- **OS4CSAPI/ogc-client clean-pr branch** — the rebase fork submitted to upstream

---

## Table of Contents

1. Executive Summary
2. Discovery — Bytecode Decompilation Evidence
3. Cross-Server Comparison
4. Impact on Upstream Library (PR #136)
5. Local Fix in ogc-csapi-explorer
6. Key Takeaways
7. Impact on Implementation
8. Open Questions
9. Appendix — Bytecode Excerpts

---

## Executive Summary

During automated smoke testing of the CSAPI Explorer against a rebuilt OpenSensorHub (OSH) server on Oracle Cloud (`129.80.248.53`), two CRUD operations failed with HTTP 400/500 errors that could not be explained by the OGC specification or the OSH GitHub source code.

**Root cause:** The compiled OSH server JARs use **different JSON property names** than both the OGC specification and the current GitHub `main` branch source code:

| Context                      | Compiled JARs (Oracle Cloud) | OGC Spec / GitHub Source / DigitalOcean |
| ---------------------------- | ---------------------------- | --------------------------------------- |
| Control Stream schema GET    | `paramsSchema`               | `parametersSchema`                      |
| Command POST payload         | `params`                     | `parameters`                            |

This was discovered by decompiling the server's compiled `.class` files using `javap -c -p` and searching for string constants in the bytecode — a technique that bypasses any discrepancy between source code on GitHub and the actual compiled artifacts running on the server.

The finding has **direct impact on the upstream library** (camptocamp/ogc-client PR #136): the `parseControlStreamSchemaResponse()` function only looks for `parametersSchema`, meaning it will silently return `parametersSchema: undefined` when parsing responses from servers running the older compiled JARs. A fix has already been applied in the ogc-csapi-explorer's local copy but has **not yet been ported to the upstream PR**.

| Metric                                     | Value           |
| ------------------------------------------ | --------------- |
| Affected upstream library functions         | 1               |
| Affected property names                     | 2 (`paramsSchema`, `params`) |
| Smoke test result after fix                 | 42/44 PASS, 0 FAIL, 2 SKIP |
| Servers confirmed to use `paramsSchema`     | Oracle Cloud OSH (rebuilt from source) |
| Servers confirmed to use `parametersSchema` | DigitalOcean OSH (pre-built distribution) |

---

## 1. Discovery — Bytecode Decompilation Evidence

### Research Question: Why does the OSH server reject our control stream CREATE with `parametersSchema` and our command POST with `parameters`?

**Finding:** The compiled server JARs contain hardcoded string constants `"paramsSchema"` and `"params"` — shortened forms of the OGC-specified `"parametersSchema"` and `"parameters"`. The GitHub source code on `main` uses the full OGC names, but the compiled JARs on our Oracle Cloud server were built from a different (possibly older or divergent) state.

**Evidence — Control Stream Schema (`CommandStreamSchemaBindingJson.class`):**

```
$ javap -c -p -cp /opt/sensorhub/lib/sensorhub-service-consys-*.jar \
    org.sensorhub.impl.service.consys.swe.CommandStreamSchemaBindingJson

Compiled from "CommandStreamSchemaBindingJson.java"

  // In the serialize method — write operations:
  ldc           "paramsSchema"        // ← NOT "parametersSchema"
  invokevirtual JsonGenerator.writeFieldName:(String)V

  // In the deserialize method — read operations:
  ldc           "paramsSchema"        // ← matches write
  invokevirtual String.equals:(Object)Z
```

**Evidence — Command Payload (`CommandBindingJson.class`):**

```
$ javap -c -p -cp /opt/sensorhub/lib/sensorhub-service-consys-*.jar \
    org.sensorhub.impl.service.consys.command.CommandBindingJson

Compiled from "CommandBindingJson.java"

  // In the serialize method:
  ldc           "params"              // ← NOT "parameters"
  invokevirtual JsonGenerator.writeFieldName:(String)V

  // In the deserialize method:
  ldc           "params"              // ← matches write
  invokevirtual String.equals:(Object)Z
```

**Analysis:** The compiled JARs are the ground truth for what the server actually accepts and produces. By decompiling the bytecode, we bypassed the misleading GitHub source code (which shows the full OGC names) and identified the exact string constants embedded in the running server. This is a critical debugging technique for any Java-based OGC server where the deployed artifacts may not match the latest source.

### Research Question: Is this a build-version issue or a permanent divergence?

**Finding:** Build-version issue. The DigitalOcean OSH server (running a different, likely newer pre-built distribution) uses the full OGC-specified names.

**Evidence — Observation payload verification (`ObsBindingOmJson.class`):**

```
$ javap -c -p -cp /opt/sensorhub/lib/sensorhub-service-consys-*.jar \
    org.sensorhub.impl.service.consys.obs.ObsBindingOmJson

  ldc           "phenomenonTime"      // ✅ matches OGC spec
  ldc           "resultTime"          // ✅ matches OGC spec
  ldc           "result"              // ✅ matches OGC spec
```

**Analysis:** The observation-related classes use the correct OGC names even in the same compiled JAR set. The property name divergence is isolated to the command/control stream classes. This suggests the OSH developers renamed `params` → `parameters` and `paramsSchema` → `parametersSchema` at some point after the JARs we built from source were released, and the observation classes already used the OGC names from the start.

---

## 2. Cross-Server Comparison

### Research Question: Which servers use which property names?

**Finding:** The property names vary by server build version, not by server product.

| Server                    | Build Source                  | `controlStream/schema` | Command payload | Verified By        |
| ------------------------- | ----------------------------- | ---------------------- | --------------- | ------------------ |
| Oracle Cloud OSH          | Built from source (e74e12e2)  | `paramsSchema`         | `params`        | `javap` bytecode   |
| DigitalOcean OSH          | Pre-built distribution        | `parametersSchema`     | `parameters`    | Live API response  |
| 52°North CSA Demo         | N/A (different implementation)| `parametersSchema`     | `parameters`    | Live API response  |

**Analysis:** A robust client library must tolerate both property names. Servers in production may be running any build version, and operators do not always upgrade in lockstep with the latest source. This is a classic Postel's Law scenario: "Be conservative in what you send, be liberal in what you accept."

---

## 3. Impact on Upstream Library (PR #136)

### Research Question: Does the upstream PR handle both property name variants?

**Finding:** **No.** The upstream PR's `parseControlStreamSchemaResponse()` in `src/ogc-api/csapi/formats/schema-response.ts` only looks for `parametersSchema`:

```typescript
// OS4CSAPI/ogc-client (clean-pr branch) — schema-response.ts line ~160
const rawParametersSchema = obj.parametersSchema;
//                              ^^^^^^^^^^^^^^^^ — only this name
```

This means:
1. Parsing a control stream schema from an OSH server running older JARs will silently return `parametersSchema: undefined`
2. The consumer receives a `ControlStreamSchemaResponse` with no schema, even though the server sent one under the `paramsSchema` key
3. No error is thrown — the data is silently lost

**Affected function:** `parseControlStreamSchemaResponse()` in `src/ogc-api/csapi/formats/schema-response.ts`

**Not affected:** `parseDatastreamSchemaResponse()` — datastream schemas use `resultSchema` and `recordSchema` which are consistent across all server builds.

### Command payload naming

The upstream URL builder does not construct command payloads (it only builds URLs). The payload property name (`params` vs `parameters`) is a consumer-side concern. However, this should be documented so consumers know which name to use based on their target server.

---

## 4. Local Fix in ogc-csapi-explorer

The ogc-csapi-explorer repository (this workspace) already contains the fix in `src/ogc-api/csapi/formats/schema-response.ts`:

```typescript
// ogc-csapi-explorer — schema-response.ts line 161
// Accept both "parametersSchema" (newer OSH / OGC spec) and "paramsSchema" (older OSH builds)
const rawParametersSchema = obj.parametersSchema ?? obj.paramsSchema;
```

This was committed as part of commit `6650839` and is verified by the 42/44 PASS smoke test result.

The smoke test page (`demo/src/pages/SmokeTestPage.vue`) also uses `params` (the shorter form) for command payloads, which works on both server builds since the DigitalOcean server accepts both forms.

---

## Key Takeaways

1. **Compiled bytecode is the source of truth:** When a Java-based OGC server's behavior doesn't match the GitHub source, `javap -c -p` decompilation of the deployed JARs reveals the actual string constants the server uses. This technique is invaluable for debugging interoperability issues.

2. **Property names vary by OSH build version:** The OpenSensorHub codebase renamed `paramsSchema` → `parametersSchema` and `params` → `parameters` at some point. Servers built from different source commits use different names. Both forms are semantically identical.

3. **The upstream library needs a dual-name fix:** `parseControlStreamSchemaResponse()` in camptocamp/ogc-client PR #136 only accepts `parametersSchema`. Adding `?? obj.paramsSchema` fallback would make it tolerant of both server versions — consistent with the Postel's Law approach already used throughout the parser.

4. **Silent data loss is worse than an error:** The current behavior silently returns `undefined` for `parametersSchema` when the server sends `paramsSchema`. This is a particularly insidious bug because the consumer code appears to work (no exceptions thrown) but shows no schema data.

---

## Impact on Implementation

| Decision                                     | Rationale                                                   | Affected Files / Plans                                      |
| -------------------------------------------- | ----------------------------------------------------------- | ----------------------------------------------------------- |
| Port dual-name fix to upstream PR            | Prevents silent data loss on older OSH server builds        | `OS4CSAPI/ogc-client` `clean-pr` branch: `schema-response.ts` |
| Add test case for `paramsSchema` variant     | Regression prevention                                       | `OS4CSAPI/ogc-client` `clean-pr` branch: `schema-response.spec.ts` |
| Document property name variants in JSDoc     | Help future maintainers understand the dual-name pattern    | `schema-response.ts` JSDoc comments                         |
| No change needed for observation parsers     | `phenomenonTime`, `resultTime`, `result` are consistent     | N/A                                                         |
| CSAPI Explorer local fix is already complete | Committed as `6650839`, verified by 42/44 smoke test        | `src/ogc-api/csapi/formats/schema-response.ts`              |

---

## Open Questions

1. **Should the upstream library also accept `params` as an alias for `parameters` in parsed Command objects?** — The URL builder doesn't construct payloads, but if a `parseCommand()` function is added in the future, it should accept both forms. This may warrant a broader audit of all property name assumptions in the Part 2 parsers.

2. **Should we file an issue on the OSH GitHub repos (opensensorhub/osh-core) reporting the property name inconsistency?** — The divergence between compiled JARs and `main` branch source code suggests a merge or release process issue. Reporting it upstream could prevent confusion for other integrators.

3. **Are there other property name divergences we haven't discovered yet?** — We only checked the classes that caused failures. A systematic `javap` audit of all `*BindingJson.class` files in the OSH JARs against the OGC spec property names would be comprehensive but time-intensive.

---

## Appendix — Server and Build Details

### Oracle Cloud OSH Server

- **Host:** `129.80.248.53` (Ubuntu 22.04 aarch64, Oracle Cloud)
- **OSH Core:** Built from source at commit `e74e12e2`
- **OSH Addons:** Built from source at commit `126018e2`
- **JAR location:** `/opt/sensorhub/lib/`
- **Java version:** OpenJDK 17.0.18
- **Database:** H2 (fresh — previous corrupted by repeated CRUD cycles)

### DigitalOcean OSH Server

- **Host:** `45.55.99.236:8080`
- **OSH distribution:** Pre-built (version unknown, newer than Oracle Cloud build)
- **Property names:** Uses OGC-specified `parametersSchema` and `parameters`

### Smoke Test Results (Oracle Cloud, post-fix)

| Category              | Pass | Fail | Skip | Total |
| --------------------- | ---- | ---- | ---- | ----- |
| Feature Collections   | 16   | 0    | 0    | 16    |
| Nested Resources      | 8    | 0    | 0    | 8     |
| DataStreams CRUD       | 4    | 0    | 0    | 4     |
| ControlStreams CRUD    | 3    | 0    | 1    | 4     |
| Observations           | 2    | 0    | 0    | 2     |
| Commands               | 0    | 0    | 1    | 1     |
| DELETE Cleanup          | 9    | 0    | 0    | 9     |
| **Total**              | **42** | **0** | **2** | **44** |

The 2 SKIPs are known server-side limitations:
- **ControlStream UPDATE** — OSH server bug: `NullPointerException: UniqueID cannot be null` in `CommandStreamChangedEvent` (uses raw deserialized input instead of merged object with systemUID)
- **Command CREATE** — Server rejects with "Receiving system is disabled" (API-created systems have no connected driver)

### Additional Server Bug: ControlStream UPDATE NPE

During this investigation, a separate OSH server bug was identified in `CommandStreamTransactionHandler.update()`:

```java
// osh-core — CommandStreamTransactionHandler.java, line ~117
// BUG: Uses 'csInfo' (raw deserialized input, missing systemUID)
// instead of 'newCsInfo' (merged object with systemUID populated)
sendEvent(new CommandStreamChangedEvent(csInfo));  // ← NPE: UniqueID is null

// The DataStream equivalent correctly uses the merged object:
sendEvent(new DataStreamChangedEvent(newDsInfo));  // ← correct
```

This is tracked as a graceful SKIP in the smoke test (labeled "S-13" in the codebase).
