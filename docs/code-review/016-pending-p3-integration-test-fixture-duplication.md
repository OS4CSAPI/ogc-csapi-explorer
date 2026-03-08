---
status: pending
priority: p3
issue_id: "016"
tags: [code-review, dry, tests]
dependencies: []
---

# Collection Fixture Factory Redeclared in 4 Integration Test Files

## Problem Statement

Each of the 4 integration test files declares its own local `makeCollection`/`makeCSAPICollection`/`makeFullCollection` factory function that returns the same `OgcApiCollectionInfo` shape with 12 identical padding fields. These 12 fields appear 28 times across 4 files, creating a maintenance burden — adding a new required field to `OgcApiCollectionInfo` requires updating all 4 factories independently.

## Findings

| File | Function | Lines |
|---|---|---|
| `integration/discovery.spec.ts` | `makeCSAPICollection` | 37–88 |
| `integration/observation.spec.ts` | `makeCollection` | 24–59 |
| `integration/command.spec.ts` | `makeCollection` | 33–68 |
| `integration/navigation.spec.ts` | `makeFullCollection` | 48–98 |

All 4 share these 12 identical padding fields:
`itemFormats: []`, `bulkDownloadLinks: {}`, `jsonDownloadLink: ''`, `crs: []`, `itemCount: 0`, `queryables: []`, `sortables: []`, `mapTileFormats: []`, `vectorTileFormats: []`, `supportedTileMatrixSets: []`

`discovery.spec.ts` (`makeCSAPICollection`) and `navigation.spec.ts` (`makeFullCollection`) are nearly identical — both declare all 9 CSAPI resource links.

Note: `pipeline.spec.ts` does NOT have this pattern — it uses inline raw JSON fixtures.

## Origin

The entire `src/ogc-api/csapi/integration/` directory is fork-only code (absent from upstream/main). The factories were introduced in commits `1bd70b5` (Phase 4, Task 1 — Issue #31) and `66926d7` (integration test suites). 100% fork-introduced.

## Proposed Solutions

### Option A: Create a shared `_fixtures.ts` in the integration directory (Recommended)
```typescript
// src/ogc-api/csapi/integration/_fixtures.ts
import type { OgcApiCollectionInfo } from '../../model.js';

const PADDING = {
  itemFormats: [], bulkDownloadLinks: {}, jsonDownloadLink: '',
  crs: [], itemCount: 0, queryables: [], sortables: [],
  mapTileFormats: [], vectorTileFormats: [], supportedTileMatrixSets: [],
};

export const ALL_CSAPI_LINKS = [ /* 9 standard rel entries */ ];

export function makeFullCsapiCollection(
  overrides: Partial<OgcApiCollectionInfo> = {}
): OgcApiCollectionInfo {
  return { ...PADDING, links: ALL_CSAPI_LINKS, id: 'test', title: 'Test', ...overrides };
}
```

Each spec file imports from `_fixtures.ts` instead of redeclaring.
**Effort:** Small | **Risk:** None (test-only change)

## Recommended Action

Option A. Eliminates ~180 lines of boilerplate across 4 files and ensures fixture consistency.

## Technical Details

- **Affected files:** All 4 `src/ogc-api/csapi/integration/*.spec.ts`
- **New file:** `src/ogc-api/csapi/integration/_fixtures.ts`

## Acceptance Criteria

- [ ] `_fixtures.ts` created with `PADDING`, `ALL_CSAPI_LINKS`, `makeFullCsapiCollection`
- [ ] All 4 spec files import from `_fixtures.ts`
- [ ] No spec file contains its own padding object
- [ ] All integration tests pass

## Work Log

- 2026-03-05: Identified by external senior developer during code review of `clean-pr`
- 2026-03-07: Verified and filed as code-review record; confirmed no duplicate exists; confirmed fork-only
