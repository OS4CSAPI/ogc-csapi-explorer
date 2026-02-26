# Phase 6: Work Assessment and Strategy

**Date:** 2026-02-23
**Context:** Maintainer feedback on PR #136 — architectural refactoring required for upstream acceptance
**Branch:** `phase-6` (from `main`)

---

## Work Breakdown

The remaining work breaks into three tiers.

### Tier 1: Mechanical (1–2 days)

Straightforward changes, no design decisions needed:

- **Prettier formatting** — run `prettier --write` on our 62 files. Zero-thought transformation.
- **Remove CSAPI exports from `src/index.ts`** — delete the 184 lines we added. Consumers will import from the new entry point instead.
- **Move MIME type functions** out of `src/shared/mime-type.ts` back into the CSAPI module (e.g., into `formats/constants.ts` where related constants already live). Remove the tests from `mime-type.spec.ts` and put them in the corresponding CSAPI test file.
- **Move `checkHasConnectedSystems`** out of `src/ogc-api/info.ts` into the CSAPI module. It just checks conformance URIs — it can live in `helpers.ts` or a new `conformance.ts`.

After Tier 1, our upstream file modifications shrink from 5 files to essentially **zero** (or maybe just `.gitignore`). That's a dramatically cleaner footprint and exactly what jahow wants.

### Tier 2: Architecture (2–4 days) — the hard part

This is the central design question: **if `endpoint.ts` can't import CSAPI code, how do consumers access CSAPI functionality?**

Right now the flow is:

```
endpoint.csapi('collection') → CSAPIQueryBuilder
```

The endpoint reaches into the CSAPI module to create the query builder. That has to be inverted — the CSAPI module needs to reach into the endpoint instead.

**The likely new pattern:**

```ts
import { OgcApiEndpoint } from '@camptocamp/ogc-client';
import { CSAPIQueryBuilder } from '@camptocamp/ogc-client/csapi';

const endpoint = new OgcApiEndpoint('https://api.example.org');
// CSAPI module uses the endpoint's PUBLIC API to get what it needs
const csapi = await CSAPIQueryBuilder.fromEndpoint(endpoint, 'collection-id');
```

Or a helper function:

```ts
import { csapi } from '@camptocamp/ogc-client/csapi';
const qb = await csapi(endpoint, 'collection-id');
```

This works because `CSAPIQueryBuilder` already receives its constructor arguments (base URL, available resources, resource URLs) — it doesn't care where they came from. We just need to extract that setup logic from `endpoint.ts` and move it into a factory function inside the CSAPI module that reads the endpoint's existing public properties (`allCollections`, `conformanceClasses`, etc.).

This also requires:

- A new `src/ogc-api/csapi/index.ts` barrel file as the public entry point
- An addition to `package.json`'s `"exports"` field mapping `"./csapi"` to the right dist path
- Possibly build config adjustments (though the esbuild command already compiles all `.ts` files individually, so this might just work)
- Updating the PR description's usage example

### Tier 3: Verification (1–2 days)

- All 1,285 CSAPI tests still pass
- All upstream tests pass (zero regressions)
- Full CI pipeline goes green (all 5 steps)
- The separate entry point actually works from a consumer's perspective
- Clean rebase onto upstream base

---

## Strategic Timing

jahow said _"I'm going to review the changes to the existing code and give you a more thorough feedback."_ This review hasn't arrived yet. He's going to look at our modifications to `endpoint.ts`, `info.ts`, and `mime-type.ts` — which are exactly the files we'll be refactoring.

**Recommendation:** Wait for his detailed review before implementing. Reasons:

1. His review may contain additional constraints or preferences that affect the design. Starting now risks having to redo work.
2. His review might explicitly say "move all of this into the CSAPI module" — confirming our plan and giving us a clear mandate.
3. He may have opinions on the entry point pattern (`./csapi` vs `./ogc-api/csapi` vs something else) or the factory function approach.
4. Responding to his architecture comment now (the draft response we prepared) opens the door for him to clarify before we build.

### What we CAN do right now

- Post the response to jahow (gets the dialogue going)
- Research how the build system handles multiple entry points
- Research how EDR (PR #114) integrated — since jahow pointed to it as a reference, understanding where it deviates from what he wants for CSAPI is valuable
- Plan the specific file-level changes
- Draft the new `package.json` exports configuration

### What we should NOT do yet

- Start coding the refactor
- Fix formatting (it'll just need redoing after the refactor anyway)

---

## Overall Assessment

This is a solid 1–2 weeks of focused work, but it's well-scoped. The good news is that 95% of the CSAPI module internals don't change at all — it's purely the integration surface (how the module connects to the rest of ogc-client) and the packaging (how consumers import it). The 1,285 tests, the parsers, the URL builder, the format pipeline — all of that stays exactly as-is.

The risk is low, the path is clear, and jahow's feedback is actually improving the architecture. A self-contained module with its own entry point is cleaner than what we had before.
