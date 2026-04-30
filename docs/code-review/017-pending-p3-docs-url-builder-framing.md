---
status: pending
priority: p3
issue_id: '017'
tags: [code-review, docs, api-design]
dependencies: []
phase: 8
---

# README and Module Docs Do Not Make URL-Builder Nature Obvious

## Problem Statement

The CSAPI module is a **URL builder + response parser**, not an HTTP client.
`CSAPIQueryBuilder` returns URL strings; the consumer is responsible for every
`fetch()` call (including auth headers, timeouts, retries, and error handling).
This is a deliberate design choice that mirrors `EDRQueryBuilder`, but neither
the README, the `csapi/index.ts` module docblock, nor `createCSAPIBuilder`'s
JSDoc states it prominently.

A consumer unfamiliar with the library will look for
`builder.fetchDataStreams({ headers: { Authorization: '...' } })` and not find
it, then waste time before discovering the URL-builder pattern.

## Findings

The reviewer's worked example showed that the minimal "make one authenticated
request" path requires 5 steps and two import paths — all correct, none of it
wrong, but undocumented as a pattern:

```ts
const endpoint = new OgcApiEndpoint('https://api.example.com');
const builder = await createCSAPIBuilder(endpoint, 'weather-stations');
const url = builder.getDataStreams({ limit: 10 });
const response = await fetch(url, { headers: { Authorization: 'Bearer ...' } });
const result = parseCollectionResponse(await response.json(), parseDatastream);
```

## Proposed Solutions

### Option A: Top-of-module note + README pattern section (Recommended)

1. Add a short docblock at the top of `src/ogc-api/csapi/index.ts` explaining
   that the module returns URL strings and parsers, and that the consumer owns
   `fetch()`.
2. Add a "Connected Systems — making a request" section to the README with the
   5-step worked example, including a `headers` example for auth.
3. Cross-reference from `createCSAPIBuilder`'s JSDoc.

**Effort:** Small (docs only) | **Risk:** None

### Option B: Add an HTTP-executing wrapper

Out of scope. Would change the design and is not what the reviewer recommends.

## Ownership Assessment

100% ours — all docs in our CSAPI module and our README section.

## Triage

**Accept — Phase 8.** Docs-only fix.
