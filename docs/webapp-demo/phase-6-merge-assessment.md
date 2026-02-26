# Phase 6 Upstream Merge Assessment

**Date:** February 26, 2026  
**Upstream PR:** [camptocamp/ogc-client#136](https://github.com/camptocamp/ogc-client/pull/136)  
**Upstream branch:** `OS4CSAPI/ogc-client-CSAPI_2` → `phase-6`  
**Explorer commit:** `8f74d60` (merged into `main`)

## Summary

The Phase 6 upstream refactoring (84 commits, 58 src/ files changed, +3,667/−1,642 lines) was merged into the explorer repository with **zero breakage**. Only 1 trivial merge conflict was encountered.

## What Phase 6 Changed

Phase 6 was a major architectural refactoring requested by the upstream maintainer (`jahow`) to decouple CSAPI from the core library:

| Change | Detail |
|---|---|
| Root `src/index.ts` | Removed ~186 CSAPI export lines |
| New `src/ogc-api/csapi/index.ts` | Created barrel file re-exporting 171 public symbols |
| New `src/ogc-api/csapi/factory.ts` | `createCSAPIBuilder()` async factory replacing `endpoint.csapi()` |
| `src/ogc-api/endpoint.ts` | Removed `csapi()` method and CSAPI imports; added `hasConnectedSystems`/`csapiCollections` with zero CSAPI imports |
| `package.json` | Added `./csapi` sub-path export, `"sideEffects": false` |

The goal: anyone using `@camptocamp/ogc-client` without Connected Systems gets zero CSAPI code in their bundle. CSAPI is now opt-in via `@camptocamp/ogc-client/csapi`.

## Why It Didn't Affect the Explorer

The demo app imports via deep paths using the `@csapi` Vite alias (which resolves to `src/`):

```ts
import { CSAPIQueryBuilder } from '@csapi/ogc-api/csapi/url_builder';
import { CSAPIResourceTypes } from '@csapi/ogc-api/csapi/types';
// ... 14 deep import paths total
```

Phase 6 changed the **public entry points** (barrel files, export surfaces), not the **internal module structure**. The internal files that the explorer imports from (`url_builder.ts`, `types.ts`, `helpers.ts`, `parser.ts`, etc.) were not renamed or relocated. All 14 demo import paths remained valid after the merge.

## Merge Results

| Gate | Result |
|---|---|
| Merge conflicts | 1 (trivial — import path rename in `url_builder.ts`) |
| Demo import paths verified | 14/14 pass |
| CSAPI test suites | 30/30 pass |
| CSAPI individual tests | 1,294/1,294 pass |
| Full test suites | 56/61 pass (5 pre-existing non-CSAPI failures) |
| Vite compilation | Clean, zero errors |
| App loads in browser | Confirmed |

## Conflict Resolution

The single conflict was in `src/ogc-api/csapi/url_builder.ts`:

- **Ours:** Import formatting differences (cosmetic)
- **Theirs:** Import path changed from `endpoint-error.js` to `errors.js` (module rename)
- **Resolution:** Accepted upstream (`git checkout --theirs`) — upstream is canonical for library source

## Merge Strategy

A throwaway branch (`test-phase6-merge`) was created from `main` to safely test the merge before committing. After all verification gates passed, it was fast-forwarded into `main` and pushed. The test branch was then deleted.

## Conclusion

The Phase 6 refactoring was well-designed — it was a packaging/export reshuffling at the boundary, not a rewrite of internals. The upstream maintainer's requirements (decouple from `index.ts`, no CSAPI imports outside `csapi/` directory) were all additive/structural changes that did not affect the internal module paths the explorer depends on.
