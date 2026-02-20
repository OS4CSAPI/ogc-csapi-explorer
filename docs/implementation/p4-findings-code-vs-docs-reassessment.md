# P4 Findings: Code vs Documentation Reassessment

**Date:** February 19, 2026  
**Purpose:** Re-examine whether P4-F1 and P4-F2 warrant code changes beyond JSDoc documentation, considering the full architecture of the CSAPI client library contribution.  
**Triggered by:** Challenge to the documentation-only approach taken in Issues [#92](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/92) and [#93](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/93).

**Related documents:**
- [P4 CRUD Findings — Scope Assessment](p4-crud-findings-scope-assessment.md)
- [P5 Findings Coverage Analysis](p5-findings-coverage-analysis.md)
- [Contribution Goal and Definition](../planning/contribution-goal-and-definition.md)

---

## Context: The Library Is More Than a URL Builder

The initial scope assessment ([P4 CRUD Findings — Scope Assessment](p4-crud-findings-scope-assessment.md)) concluded that both P4 findings resolve to JSDoc-only changes because "the library is a URL builder." That framing was challenged — and rightly so.

The library already touches the write path in three places:

| Component | File | What It Does |
|-----------|------|--------------|
| `create*()`/`update*()`/`delete*()` methods | `url_builder.ts` | Returns POST/PUT/DELETE target URLs |
| `getContentTypeForResource()` | `formats/constants.ts` | Returns the correct `Content-Type` for each resource type |
| `CSAPI_CONTENT_TYPES` map | `formats/constants.ts` | Exported map of resource type → Content-Type for consumer use |

And on the read side, it goes well beyond URL construction:

| Component | File(s) | What It Does |
|-----------|---------|--------------|
| `endpoint.getCollectionItems()` | `endpoint.ts` | Builds URL + calls `fetchDocument()` + parses JSON |
| SensorML 3.0 parser | `formats/sensorml/` | Deep response parsing for system descriptions |
| SWE Common 3.0 parser | `formats/swecommon/` | Schema and encoded-values parsing |
| `isCSAPIFeature()` / `extractCSAPIFeature()` | `formats/geojson.ts` | Response classification |
| `classifyFeature()` | `formats/classification.ts` | Feature type detection from response data |

So the relevant question isn't "is this a URL builder?" — it's **"does the specific finding warrant a code change within the library's actual architecture?"**

---

## P4-F2 Reassessment: uid Strictness on Update Methods

**Finding:** OSH rejects PUT requests with `400 "Feature UID cannot be changed"` if the `uid` in the request body differs from the server-stored value.

### Could we add a `validateUpdatePayload()` function?

Considered and rejected. Here's why:

1. **Existing validators operate on URL construction inputs.** `validateLimit()` and `validateBbox()` run inside builder methods during URL construction — they validate *what goes into the URL*. A body validator would be a different class of responsibility entirely (validating what goes into the *request body*).

2. **The actual check is trivial.** It's `original.uid !== updated.uid` — one string comparison. Any TypeScript developer can do this. Wrapping it in a library function adds API surface without meaningful value.

3. **The consumer value is understanding *why* uid must match.** The non-obvious part is that OSH enforces byte-for-byte uid equality and that a 1-second timestamp difference causes rejection. JSDoc conveys this immediately at the point of use (the `update*()` method), which is exactly where the developer needs to see it.

4. **A validator would need the original resource.** The library doesn't hold state between GET and PUT — the consumer does. A validator that requires `(original, updated) => boolean` would need the consumer to pass in the original they fetched, which is redundant with just telling them to preserve the uid.

### Verdict: JSDoc is the correct approach

Issue [#92](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/92) stays as documentation-only. No code change warranted.

---

## P4-F1 Reassessment: Command POST Streaming Behavior

**Finding:** POSTing to `/controlstreams/{id}/commands` causes the connection to hang — the server holds it open indefinitely rather than returning `201 Created`.

### The deeper insight: this isn't a bug, it's the spec

The initial framing treated this as "OSH holds the connection open (a quirk)." But CSAPI Part 2 defines command endpoints as potentially streaming — the server can push command status updates back over the same connection. The "hang" is the server streaming command results in real time.

That means:
- **A timeout/AbortController workaround is the wrong *permanent* fix** — it treats a spec feature as a bug
- **JSDoc documenting the behavior is the right *immediate* fix** — consumers need to know what to expect
- **The *real* code work is proper streaming command response support** — an async iterator / ReadableStream wrapper

### What streaming support would look like

```typescript
// Hypothetical streaming-aware command API
const stream = await csapiSendCommand(builder.createCommand(csId), commandBody);
for await (const statusUpdate of stream) {
  console.log(statusUpdate.status, statusUpdate.timestamp);
}
```

This would involve:
- Research into the exact CSAPI Part 2 streaming protocol (SSE vs chunked JSON)
- A `ReadableStream` / async iterator wrapper for command responses
- Integration with the library's existing `sharedFetch` patterns (or a parallel write-path fetch utility)
- Mock streaming tests
- New interfaces for streaming status updates

### Why we're not doing this now

This is a **standalone feature** — architecturally significant and deserving its own design cycle. It would be the first time this library handles HTTP writes + streaming responses. Bolting it onto a JSDoc documentation issue would violate the "no scope expansion" constraint.

More importantly, it's **outside our contribution scope.** The [Contribution Goal](../planning/contribution-goal-and-definition.md) focuses on URL construction, response parsing, format handling, and type safety. Adding a streaming HTTP client layer would expand the library's architectural boundary beyond what was planned or agreed.

### Verdict: JSDoc now, streaming deferred indefinitely

Issue [#93](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/93) stays as documentation-only. The streaming capability is noted here for future reference but is **not in scope** for this contribution.

---

## Summary

| Finding | Code Change? | Rationale |
|---------|-------------|-----------|
| **P4-F2** (uid strictness) | No — JSDoc only | Existing validators cover URL inputs, not request bodies. The check is trivial. The value is in *understanding* the constraint, not in a wrapper function. |
| **P4-F1** (command POST streaming) | No — JSDoc only | The immediate fix (document the behavior) is JSDoc. The real code fix (streaming response support) is a standalone feature outside contribution scope. |

Both issues (#92, #93) are correctly scoped as documentation-only.

---

## Decision Record

| Decision | Date | Context |
|----------|------|---------|
| P4-F2 → JSDoc only | 2026-02-19 | Scope assessment + code-vs-docs reassessment |
| P4-F1 → JSDoc only | 2026-02-19 | Scope assessment + code-vs-docs reassessment |
| Streaming command support → out of scope | 2026-02-19 | Outside contribution boundary; deferred indefinitely |
