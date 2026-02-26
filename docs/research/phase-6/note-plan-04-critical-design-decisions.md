# Note: Plan 04 Contains the Critical Design Decisions

**Date:** 2026-02-23
**Context:** Analysis of which research plan involves the most important design decisions

---

## Summary

**Plan 04: Endpoint Decoupling Architecture** is the most consequential research plan — by a wide margin.

Plans 01, 02, 03, and 05 are all _informational_ — they gather facts about how things work. Plan 06 is _synthesis_ — it assembles prior findings into a checklist. None of them involve design choices.

Plan 04 is where every consequential decision lives.

---

## Critical Decisions in Plan 04

### 1. Consumer API Shape

Does a user call `CSAPIQueryBuilder.fromEndpoint(endpoint, collectionId)`, or `endpoint.csapi(collectionId)`, or `createCSAPIClient(endpoint)`? This determines the developer experience for every downstream consumer.

### 2. Coupling Direction

Does CSAPI depend on `OgcApiEndpoint` as a concrete class, or on a lightweight interface/type describing the data shape? This determines whether CSAPI can be tested and used independently.

### 3. Data Boundary

What exact data crosses from `OgcApiEndpoint` into CSAPI? Today `endpoint.ts` calls deep into CSAPI internals. The new boundary defines what's public API vs internal implementation detail.

### 4. Where Convenience Methods Live

`hasConnectedSystems` and `csapiCollections` currently live on `OgcApiEndpoint`. Do they move entirely into the CSAPI module? Do they become standalone functions? Do they stay as thin wrappers that call into CSAPI?

### 5. Test Architecture

The 6 CSAPI tests in `endpoint.spec.ts` either stay there (testing a thin delegation layer) or move to the CSAPI module's own test suite. This affects how the test fixtures are organized.

---

## Why This Matters

Every other plan feeds _into_ Plan 04, and Plan 06 simply _executes_ what Plan 04 decides. If we get Plan 04 wrong, we'll either break the public API, create a coupling that jahow rejects, or paint ourselves into a corner that requires another refactor.
