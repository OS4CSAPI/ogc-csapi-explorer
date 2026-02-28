# OSH Server Property Name Divergence — Validation Report

> **Date:** 2026-02-28  
> **Related issue:** [OS4CSAPI/ogc-client-CSAPI_2#140](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/140)  
> **Commits under review:** `6650839` (paramsSchema fix), `b3c4702` (params payload change — reverted)  
> **Test servers:** Oracle Cloud OSH (`os4csapi-osh.duckdns.org`), DigitalOcean OSH (`45.55.99.236:8080`)

## Background

During CSAPI Explorer smoke test development targeting Oracle Cloud OSH (built from source) and DigitalOcean OSH (pre-built distribution), property name discrepancies were discovered between the two servers' JSON responses. An AI-assisted session created GitHub issue #140 and two commits addressing these differences, but portions of that session lost context and produced hallucinated analysis. This document records the validated findings.

## The Two Property Name Pairs

| Context | Oracle Cloud OSH | DigitalOcean OSH | OGC Spec |
|---------|-----------------|-------------------|----------|
| Control stream schema response | `paramsSchema` | `parametersSchema` | `parametersSchema` |
| Command payload / response | Untestable (no driver) | `parameters` | `parameters` |

## Live Server Test Methodology

A controlled test was executed against both servers on 2026-02-28. For each server:

1. **Created** a System (POST `/systems`, `application/geo+json`)
2. **Created** a ControlStream under the system (POST `/systems/{id}/controlstreams`, `application/json`)
3. **Read back** the control stream schema (GET `/controlstreams/{id}/schema`)
4. **Attempted** Command POST with `"parameters": {...}` payload
5. **Attempted** Command POST with `"params": {...}` payload
6. **Read back** any successfully created command
7. **Cleaned up** via cascade DELETE

## Results

### Control Stream Schema — `paramsSchema` vs `parametersSchema`

**Oracle Cloud OSH** returns:
```json
{
  "commandFormat": "application/json",
  "paramsSchema": {
    "type": "DataRecord",
    "label": "Test",
    "fields": [{ "type": "Boolean", "name": "active", "label": "Active" }]
  }
}
```

**DigitalOcean OSH** returns:
```json
{
  "commandFormat": "application/json",
  "parametersSchema": {
    "type": "DataRecord",
    "name": "test-input",
    "label": "Test",
    "fields": [{ "type": "Boolean", "name": "active", "label": "Active" }]
  }
}
```

**Verdict:** The divergence is **real and confirmed**. Oracle's build-from-source OSH uses `paramsSchema`; the pre-built distribution uses `parametersSchema`.

**Parser fix (commit `6650839`):**
```typescript
// schema-response.ts line 159
const rawParametersSchema = obj.parametersSchema ?? obj.paramsSchema;
```
This nullish coalescing fallback is **correct and necessary** for cross-server compatibility.

### Command Payload — `params` vs `parameters`

| Server | `"parameters": {...}` | `"params": {...}` |
|--------|----------------------|-------------------|
| Oracle Cloud OSH | 500 (no connected driver) | 500 (no connected driver) |
| DigitalOcean OSH | **202 Accepted** ✓ | **500 Internal Server Error** ✗ |

Oracle OSH rejects both payloads with 500 because API-created systems have no connected sensor driver to receive commands. This is expected behavior, not a property name issue.

DigitalOcean OSH **accepts `parameters` and rejects `params`**. This directly contradicts the claim made in commit `b3c4702` that `CommandBindingJson.class` bytecode uses `params`.

**Verdict:** The `params` claim was **incorrect**. The correct property name for command payloads is `parameters`. Commit `b3c4702`'s change of the smoke test payload from `parameters` → `params` has been **reverted**.

## Issue #140 Claim-by-Claim Assessment

### Claim 1: Parser misses `paramsSchema` → silent data loss
**VALID.** The original `parseControlStreamSchemaResponse()` only read `obj.parametersSchema`. Oracle OSH returns `paramsSchema`. The fix (`?? obj.paramsSchema`) is correct and already applied.

### Claim 2: Oracle uses `paramsSchema`, DO uses `parametersSchema`
**VERIFIED.** Live schema GET responses confirmed this divergence.

### Claim 3: `CommandBindingJson.class` uses `params` not `parameters`
**FALSE.** Live testing proves DigitalOcean OSH rejects `params` with 500 and accepts `parameters` with 202. The bytecode decompilation claim that led to this conclusion could not be independently verified.

### Claim 4: `parseCommand()` needs `obj.params` fallback
**NOT A BUG.** The parser correctly reads `obj.parameters` (part2.ts line 342). Since DO (the only testable command-accepting server) returns `parameters`, no fallback is needed. If Oracle's command-accepting behavior is eventually testable (with a real driver), this should be re-evaluated.

### Claim 5: Findings doc at `docs/research/phase-6/findings/osh-server-property-name-divergence.md`
**HALLUCINATED.** The file does not exist on the `upstream/phase-6` branch. The directory exists with 10 other findings files, but this one was never actually created.

### Claim 6: Discovery via `javap -c -p` bytecode decompilation
**UNVERIFIABLE.** No corroborating evidence exists (no findings doc, no bytecode output saved). The `paramsSchema` part of the discovery may still be true (server behavior confirms it), but the `params` claim is contradicted by live testing.

## Scope Consideration for Client Library

Before resolving issue #140 in the upstream `ogc-client` library, consider:

- The `paramsSchema` vs `parametersSchema` difference is an **OSH server build artifact**, not an OGC API specification variant
- A **standards-compliant client** should parse what the spec defines (`parametersSchema`)
- The fallback may be better placed in an **OSH-specific compatibility layer** rather than the generic OGC API client
- Alternatively, if multiple implementations exhibit this variation, it may warrant inclusion as defensive parsing

## Actions Taken

| Action | Commit | Status |
|--------|--------|--------|
| Added `paramsSchema` fallback in `parseControlStreamSchemaResponse()` | `6650839` | ✅ Correct, keep |
| Changed smoke test command payload `parameters` → `params` | `b3c4702` | ❌ Reverted |
| Added retry logic, Run All, Pre-Clean to smoke test | `f4996dc` | ✅ Correct, keep |
| Posted validation comment on issue #140 | — | ✅ Done |
| Created this findings document | — | ✅ Done |

## Summary

Of the property name changes made during the AI-assisted session:

- **`paramsSchema` / `parametersSchema` (schema response):** Real divergence, fix is valid
- **`params` / `parameters` (command payload):** Hallucinated divergence, fix was wrong and reverted

The root cause of command failures during smoke testing was **not** a property name issue — it was the absence of a connected sensor driver on API-created systems, which causes OSH to reject commands with 500 or 400 regardless of payload format.
