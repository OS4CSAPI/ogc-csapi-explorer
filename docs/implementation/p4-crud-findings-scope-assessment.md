# P4-F1 and P4-F2 — Scope Assessment

**Date:** February 19, 2026  
**Purpose:** Assess whether the two Phase 4 CRUD findings (P4-F1, P4-F2) require a Phase 6 planning effort or can be addressed as individual GitHub issues.  
**Related:** [Phase 5 Findings Coverage Analysis](p5-findings-coverage-analysis.md) | [Deferred Findings — Final Disposition](deferred-findings-final-disposition.md)

---

## Context

P4-F1 and P4-F2 were discovered during Smoke Test #19 (the first Phase 4 CRUD testing pass). They were initially categorized as "Phase 4.2" targets. Phase 4 is now complete. The question is: do these need a full planning effort (like P5 got), or can they be closed with simple GitHub issues?

---

## Key Architectural Insight

**The library is a URL builder and response parser. It does not perform HTTP fetches.**

The `CSAPIQueryBuilder` methods (`createCommand()`, `updateSystem()`, etc.) return URL strings. The consumer performs the `fetch()` call and handles the response. Both P4-F1 and P4-F2 are about HTTP behavior that happens _outside the library's current responsibility boundary_:

- P4-F1 is about what the server does after the consumer POSTs to the URL.
- P4-F2 is about what the consumer puts in the PUT request body.

This means both findings resolve to **JSDoc documentation additions** on existing methods — not new code, not new architecture, not new files.

---

## P4-F1 — Command POST Hangs

### The Finding

OSH holds the HTTP connection open on `POST /controlstreams/{id}/commands`. The server never sends a response — it appears to use a streaming/SSE pattern for real-time command status updates.

### What the Library Currently Does

`createCommand(controlStreamId)` returns a URL string: `https://example.com/collections/iot/controlStreams/{id}/commands`. That's it. The consumer does the POST.

### What Needs to Happen

- Add JSDoc warnings on `createCommand()` and `createCommands()` documenting the streaming behavior.
- Include a code example showing the recommended `AbortController` timeout pattern.
- Optionally add a `@see` reference to the P4-F1 finding.

### Effort Estimate

~15-20 lines of JSDoc changes on 2 methods. No new files. No new tests (documentation-only change).

---

## P4-F2 — PUT Rejects UID Changes

### The Finding

OSH rejects PUT requests if the `uid` in the request body doesn't byte-for-byte match the server-stored value. The error is `400 "Feature UID cannot be changed"`.

### What the Library Currently Does

`updateSystem(id)`, `updateDeployment(id)`, etc. return URL strings like `https://example.com/collections/iot/systems/{id}`. The consumer constructs and sends the PUT body.

### What Needs to Happen

- Add JSDoc warnings on all 9 `update*()` methods documenting the uid strictness.
- Document the two safe patterns: (1) preserve the original uid from the creation response, or (2) GET the resource before PUT to read the current uid.
- Include a code example showing the recommended GET-then-PUT pattern.

### Effort Estimate

~5-10 lines of JSDoc additions per method × 9 methods = ~45-90 lines total. Plus a shared `@see` reference. No new files. No new tests (documentation-only change).

---

## Verdict: Not Phase 6

Neither finding requires:

- New planning documents or ROADMAPs
- New TypeScript interfaces or model changes
- New implementation files or parsers
- New test files
- Architectural design decisions

Both findings resolve to **JSDoc documentation on existing methods** in `url_builder.ts`. They are:

- **Two separate GitHub issues** (they are unrelated concerns — connection streaming vs uid strictness)
- **~60-110 lines of JSDoc changes total** across both issues
- **No code changes** to method bodies
- **No new tests** (the methods already work correctly — they build URLs, and the URLs are correct)

If the library ever adds a higher-level "CRUD client" that wraps the URL builder with actual `fetch()` calls, these findings would become real code changes (timeout handling for P4-F1, GET-before-PUT for P4-F2). But that is a future design decision, not current scope.

---

## Action Items

| Finding | Action                                                                                       | Estimated Effort |
| ------- | -------------------------------------------------------------------------------------------- | ---------------- |
| P4-F1   | GitHub issue → JSDoc warnings on `createCommand()` / `createCommands()` with timeout example | ~15-20 lines     |
| P4-F2   | GitHub issue → JSDoc warnings on all 9 `update*()` methods with uid preservation example     | ~45-90 lines     |
