# Note: Additional Research Plans and Constraint Scoping for Plan 04

**Date:** 2026-02-23
**Context:** Analysis of gaps in the Phase 6 research strategy, specifically around external knowledge gathering and constraint enforcement

---

## Part 1: The Need for Additional External Research Plans

### The Gap

In the testing research phase, we followed a deliberate pattern: **gather authoritative external knowledge first, then synthesize into design decisions**. Specifically:

- **Section 3** (TypeScript Testing Best Practices) went to industry libraries (axios, @octokit/rest, AWS SDK) _before_ Section 6 defined "meaningful vs trivial" and Section 7 defined e2e scope
- **Section 8** (CSAPI Spec Requirements) went to the OGC specifications themselves _before_ Section 12 designed the QueryBuilder testing strategy
- **Section 9** (SensorML) went to the spec + real-world OpenSensorHub data _before_ designing parser test strategies
- **Section 32** (Real-World Servers) went to live OpenSensorHub and 52°North servers _before_ designing compatibility tests

The pattern: **authoritative external knowledge → synthesis into internal design decisions**

Plan 04 (Endpoint Decoupling Architecture) as originally written skips this entirely. It goes straight to "design the factory/adapter pattern" without first researching how proven libraries solve the exact same problem. That's the equivalent of jumping to Section 12 (QueryBuilder testing strategy) without doing Section 3 (industry best practices) first.

### Three Candidate Additions

#### 1. TypeScript Sub-Module API Design Patterns (Industry Case Studies) — ESSENTIAL

This is the most critical gap. Our core design question — _does CSAPI take an `OgcApiEndpoint` instance, or extracted data primitives?_ — has been answered many times by major TypeScript libraries. We've never looked at any of them.

**What to study:**

- How does `@aws-sdk/lib-storage` consume `@aws-sdk/client-s3`? Does it take the S3Client as a constructor parameter, or config primitives?
- How does `@octokit/plugin-rest-endpoint-methods` compose with `@octokit/core`? Plugin/mixin pattern vs wrapper pattern
- How does `@angular/cdk/testing` relate to `@angular/core`? Does it import concrete classes, interfaces, or injection tokens?
- How do `date-fns`, `lodash-es`, or `rxjs/operators` expose stateless utility APIs vs stateful module APIs?
- How does `zod` handle its ecosystem extensions (`zod-to-json-schema`, `@anatine/zod-openapi`) — do they depend on zod's concrete class or an interface?

**What design decisions this informs:**

- Consumer API shape (the #1 most visible decision)
- Whether to accept `OgcApiEndpoint` as a concrete class vs an interface/type
- How to share types between root and sub-module without creating circular deps
- Whether factory function, static method, constructor injection, or plugin pattern is the industry norm

**Without this**, we'd be designing the consumer API from instinct, with no evidence that it matches what TypeScript developers expect.

#### 2. Module Decoupling Patterns in TypeScript (Architectural Patterns) — ESSENTIAL

This is the second critical gap. Plan 04 asks us to "design the factory/adapter pattern" — but we've never studied what adapter patterns, dependency inversion, and module decoupling actually look like _in TypeScript specifically_. TypeScript's structural typing makes this different from Java/C# where the patterns originated.

**What to study:**

- Adapter pattern in TypeScript — concrete examples, not just the Gang of Four diagram
- Dependency inversion with TypeScript's structural typing (duck-typed interfaces as implicit contracts vs explicit interface declarations)
- How TypeScript projects define module boundaries (barrel files, explicit public APIs, `@internal` tags)
- Real case studies of library refactorings where a tightly-coupled module was decoupled after the fact (this is exactly our situation — CSAPI was integrated, now we're extracting it)
- The tradeoffs between coupling level options: `OgcApiEndpoint` (concrete class) → `OgcApiEndpointLike` (interface) → `{baseUrl, conformance, collections}` (data record) → individual function parameters

**What design decisions this informs:**

- Coupling direction (the #1 riskiest architectural decision — if jahow rejects it, we start over)
- Data boundary definition
- Whether to use explicit interfaces, structural typing, or parameter objects
- How loose is "loose enough" for a module that lives _in the same repo_ as its dependency

**Without this**, we'd be applying textbook SOLID principles without understanding how they translate to TypeScript's type system and module resolution.

#### 3. OGC API Building Block Architecture and Client Library Precedents (Standards Context + Case Studies) — JUDGMENT CALL

This is less clearly essential but could provide important framing. The question is: does the OGC standards architecture itself imply anything about how the client module should be structured?

**What to study:**

- OGC API "building block" architecture — how do Features, EDR, Processes, Records compose? Is CSAPI an "extension" of Features or a peer standard?
- How does `owslib` (Python, the most mature OGC client library) structure optional OGC API modules?
- How does OpenLayers handle optional OGC sources that depend on shared OGC infrastructure?
- Are there any other CSAPI client implementations (even partial) we can learn from?

**What design decisions this informs:**

- Whether the separation should reflect the standards hierarchy (CSAPI extending OGC API Common → OGC API Features → CSAPI)
- Whether our module boundary aligns with or deviates from how other OGC clients are structured
- Standards-based justification for the design we choose (useful in the PR discussion with jahow)

**The case for including it**: Provides a justification layer beyond "this is good TypeScript practice" — we can say "this also aligns with how OGC standards compose." jahow knows OGC well; speaking his language matters.

**The case against**: Might not change any code. The separation is already mandated. The OGC client library ecosystem is small enough that we might not find rich examples.

### Recommendation

**Add plans 1 and 2 as required prerequisites to the Endpoint Decoupling Architecture plan. Plan 3 is optional but worth considering.**

The revised execution order mirrors the testing research structure: internal analysis first (like Sections 1–2 in testing), external knowledge gathering second (like Section 3), then design synthesis (like Sections 6–7). The design plan now has _five_ prior plans feeding into it instead of just three — the same depth of preparation that made the testing research so effective.

---

## Part 2: Constraint Scoping — jahow's Non-Negotiable Requirements

### The Problem

The research plans as written don't tightly enough enforce jahow's constraints. Some research questions explore territory that's already closed, risking wasted effort or designs that violate hard rules.

### jahow's Non-Negotiable Constraints

These are **boundary conditions** — not design options:

1. CSAPI must **not** be exported from the root `index.ts`
2. CSAPI must be importable via `@camptocamp/ogc-client/csapi`
3. Nothing outside `src/ogc-api/csapi/` should import from the CSAPI module
4. Nothing in the core module should depend on CSAPI code (one-way dependency: CSAPI → core, never core → CSAPI)

### What These Constraints Close Off

- **Plugin/mixin patterns** where the host module imports the plugin (violates constraint 4)
- **Decorator or monkey-patching patterns** where CSAPI adds methods to `OgcApiEndpoint` (violates constraints 3 and 4)
- **Shared barrel exports** (violates constraint 3)
- **`endpoint.csapi()` remaining as-is** on the endpoint class (violates constraint 4 — endpoint would import CSAPI code)

### What's Actually Still Open

- Does the consumer call `new CSAPIClient(endpoint)` — passing an `OgcApiEndpoint` instance in?
- Or `CSAPIClient.fromEndpoint(endpoint)` — static factory?
- Or `createCSAPIClient({baseUrl, conformance})` — accepting extracted primitives?
- Does CSAPI depend on `OgcApiEndpoint` as a concrete class, or only on a type/interface describing its shape?
- Where does `hasConnectedSystems` live? It can't stay on `OgcApiEndpoint` if that means importing CSAPI code — but it _could_ stay there if it only checks conformance URIs (no CSAPI import needed)
- How are shared types (like `OgcApiCollectionInfo`) referenced — does CSAPI import them from the core module's public API?

### Action

The research strategy must be updated to:

1. State jahow's four constraints as a formal **Boundary Conditions** section
2. Scope every research question to "given these constraints, what is the best pattern for X"
3. Explicitly exclude closed design options from each research plan
