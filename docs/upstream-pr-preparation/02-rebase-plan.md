# Rebase Plan — Clean PR to `camptocamp/ogc-client`

**Date:** 2026-02-21  
**Source (archive):** `OS4CSAPI/ogc-client-CSAPI_2` branch `main` @ `2a71289`  
**Target (clean fork):** `OS4CSAPI/ogc-client` branch `main` @ `53a6449` (synced with upstream)  
**Upstream:** `camptocamp/ogc-client` branch `main` @ `53a6449`

---

## Overview

This plan reconstructs the CSAPI contribution as **13 clean commits** on a fresh
fork of the upstream repository. Each commit is self-contained, logically grouped,
and builds on the previous one. The dependency graph has been validated — imports
flow strictly downward through the commit sequence.

**Total contribution:** 61 new files + 6 modified upstream files = **67 files**  
**Total new lines:** ~29,768 insertions, 225 deletions (excluding docs)

---

## Files Explicitly Excluded

| File/Folder                               | Reason                                                        |
| ----------------------------------------- | ------------------------------------------------------------- |
| `docs/**` (371 files)                     | Internal exploratory documentation — not relevant to upstream |
| `.github/ISSUE_TEMPLATE/general-task.yml` | Our project workflow artifact                                 |
| `app/package-lock.json`                   | Lockfile churn (223 deleted lines, not meaningful)            |

These are permanently preserved in `ogc-client-CSAPI_2` (the archive repo).

---

## Files That Modify Existing Upstream Code

These files already exist in the upstream — our commits add CSAPI-related code to them:

| File                           | Lines Changed | Nature of Change                               |
| ------------------------------ | ------------- | ---------------------------------------------- |
| `.gitignore`                   | +2 lines      | Add `.vscode` and `test-output*.txt`           |
| `src/shared/mime-type.ts`      | +64 lines     | Add SML/SWE JSON/text/CSV media-type detectors |
| `src/shared/mime-type.spec.ts` | +111 lines    | Tests for above                                |
| `src/ogc-api/info.ts`          | +31 lines     | Add CSAPI conformance class constants          |
| `src/ogc-api/endpoint.ts`      | +135 lines    | Add `csapi()`, `csapiCollections`, `hasCSAPI`  |
| `src/ogc-api/endpoint.spec.ts` | +53 lines     | Tests for CSAPI endpoint integration           |
| `src/index.ts`                 | +184 lines    | Re-export CSAPI types and builders             |

---

## Commit Sequence

### Commit 1 — `feat(csapi): add CSAPI type definitions and model interfaces`

**~1,107 lines** | Foundation layer — all type definitions the rest of the codebase depends on.

| File                              | Lines | Description                                                                                                                                                  |
| --------------------------------- | ----- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `src/ogc-api/csapi/model.ts`      | 730   | Core interfaces: `System`, `Deployment`, `Procedure`, `DataStream`, `Observation`, `ControlStream`, `Command`, query option types, `CSAPIResourceTypes` enum |
| `src/ogc-api/csapi/model.spec.ts` | 377   | Type contract tests verifying all interfaces                                                                                                                 |

**Imports from upstream only:** `../../shared/models.js`, `../model.js`, `geojson`  
**Depended on by:** All subsequent commits

---

### Commit 2 — `feat(csapi): add URL builder with CRUD query support`

**~5,169 lines** | The workhorse — constructs all CSAPI endpoint URLs with query parameters.

| File                                    | Lines | Description                                                                                                                                                          |
| --------------------------------------- | ----- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `src/ogc-api/csapi/url_builder.ts`      | 2,307 | `CSAPIQueryBuilder` class: 50+ methods for systems, deployments, procedures, sampling features, datastreams, observations, control streams, commands, command status |
| `src/ogc-api/csapi/url_builder.spec.ts` | 2,862 | Comprehensive tests for all URL builder methods                                                                                                                      |

**Imports:** `./model.js`, `../../shared/errors.js`  
**Depended on by:** Commit 3 (command-routing), Commit 11 (endpoint integration)

---

### Commit 3 — `feat(csapi): add helper utilities and command routing`

**~1,037 lines** | Shared utility functions and command dispatch logic.

| File                                        | Lines | Description                                                                           |
| ------------------------------------------- | ----- | ------------------------------------------------------------------------------------- |
| `src/ogc-api/csapi/helpers.ts`              | 200   | `encodeResourceId()`, `scanCsapiLinks()`, resource-type utilities, date/time handling |
| `src/ogc-api/csapi/helpers.spec.ts`         | 463   | Tests for all helper functions                                                        |
| `src/ogc-api/csapi/command-routing.ts`      | 144   | Routes command requests through the correct control-stream → command path             |
| `src/ogc-api/csapi/command-routing.spec.ts` | 230   | Tests for command routing                                                             |

**Imports:** `./model.js`, `./url_builder.js`, `./helpers.js`  
**Depended on by:** Commit 11 (endpoint uses `scanCsapiLinks`)

---

### Commit 4 — `feat(csapi): add GeoJSON Part 1 format parsers`

**~2,014 lines** | Extracts typed resources from GeoJSON feature collections (Part 1 standard).

| File                                               | Lines | Description                                                                   |
| -------------------------------------------------- | ----- | ----------------------------------------------------------------------------- |
| `src/ogc-api/csapi/formats/constants.ts`           | 292   | Resource-type link relation constants, media types                            |
| `src/ogc-api/csapi/formats/constants.spec.ts`      | 166   | Tests for constants                                                           |
| `src/ogc-api/csapi/formats/property.ts`            | 57    | Property extraction from GeoJSON features                                     |
| `src/ogc-api/csapi/formats/property.spec.ts`       | 114   | Tests for property extraction                                                 |
| `src/ogc-api/csapi/formats/classification.ts`      | 118   | Classifier extraction (taxonomy terms)                                        |
| `src/ogc-api/csapi/formats/classification.spec.ts` | 168   | Tests for classification                                                      |
| `src/ogc-api/csapi/formats/geojson.ts`             | 467   | `parseResourceRef()`, `parseValidTime()`, GeoJSON → typed resource extraction |
| `src/ogc-api/csapi/formats/geojson.spec.ts`        | 632   | Tests for GeoJSON parsing                                                     |

**Imports:** `../model.js`, `geojson`  
**Depended on by:** Commit 7 (`part2.ts` imports `parseValidTime` from `geojson.js`)

---

### Commit 5 — `feat(csapi): add SWE Common data model parsers`

**~6,373 lines** | Parses SWE Common JSON encoding — observation/command result schemas.

| File                                                      | Lines | Description                                                                |
| --------------------------------------------------------- | ----- | -------------------------------------------------------------------------- |
| `src/ogc-api/csapi/formats/swecommon/types.ts`            | 669   | SWE Common type interfaces (`DataRecord`, `DataArray`, scalar/range types) |
| `src/ogc-api/csapi/formats/swecommon/types.spec.ts`       | 375   | Tests for SWE types                                                        |
| `src/ogc-api/csapi/formats/swecommon/_helpers.ts`         | 78    | Internal parser helpers                                                    |
| `src/ogc-api/csapi/formats/swecommon/components.ts`       | 747   | Scalar/range/boolean/text/category component parsers                       |
| `src/ogc-api/csapi/formats/swecommon/components.spec.ts`  | 600   | Tests for component parsing                                                |
| `src/ogc-api/csapi/formats/swecommon/data-record.ts`      | 225   | DataRecord parser                                                          |
| `src/ogc-api/csapi/formats/swecommon/data-record.spec.ts` | 343   | Tests for DataRecord                                                       |
| `src/ogc-api/csapi/formats/swecommon/data-array.ts`       | 526   | DataArray parser with encoding support                                     |
| `src/ogc-api/csapi/formats/swecommon/data-array.spec.ts`  | 580   | Tests for DataArray                                                        |
| `src/ogc-api/csapi/formats/swecommon/parser.ts`           | 1,307 | Top-level SWE Common parser dispatch                                       |
| `src/ogc-api/csapi/formats/swecommon/parser.spec.ts`      | 621   | Tests for parser                                                           |
| `src/ogc-api/csapi/formats/swecommon/index.ts`            | 135   | Module barrel export                                                       |
| `src/ogc-api/csapi/formats/swecommon/index.spec.ts`       | 167   | Tests for exports                                                          |

**Imports:** Self-contained module (no cross-format dependencies)  
**Depended on by:** Commit 8 (`schema-response.ts` imports `parseSWEComponent`, `parseEncoding`)

---

### Commit 6 — `feat(csapi): add SensorML procedure description parsers`

**~5,787 lines** | Parses `application/sml+json` procedure descriptions (PhysicalSystem, SimpleProcess, AggregateProcess).

| File                                                           | Lines | Description                        |
| -------------------------------------------------------------- | ----- | ---------------------------------- |
| `src/ogc-api/csapi/formats/sensorml/types.ts`                  | 863   | SensorML type interfaces           |
| `src/ogc-api/csapi/formats/sensorml/types.spec.ts`             | 369   | Tests for SensorML types           |
| `src/ogc-api/csapi/formats/sensorml/_helpers.ts`               | 258   | Internal SensorML parser helpers   |
| `src/ogc-api/csapi/formats/sensorml/errors.ts`                 | 40    | SensorML-specific error classes    |
| `src/ogc-api/csapi/formats/sensorml/physical-system.ts`        | 622   | PhysicalSystem parser              |
| `src/ogc-api/csapi/formats/sensorml/physical-system.spec.ts`   | 1,145 | Tests for PhysicalSystem           |
| `src/ogc-api/csapi/formats/sensorml/simple-process.ts`         | 135   | SimpleProcess parser               |
| `src/ogc-api/csapi/formats/sensorml/simple-process.spec.ts`    | 438   | Tests for SimpleProcess            |
| `src/ogc-api/csapi/formats/sensorml/aggregate-process.ts`      | 240   | AggregateProcess parser            |
| `src/ogc-api/csapi/formats/sensorml/aggregate-process.spec.ts` | 720   | Tests for AggregateProcess         |
| `src/ogc-api/csapi/formats/sensorml/parser.ts`                 | 410   | Top-level SensorML parser dispatch |
| `src/ogc-api/csapi/formats/sensorml/parser.spec.ts`            | 343   | Tests for parser                   |
| `src/ogc-api/csapi/formats/sensorml/index.ts`                  | 122   | Module barrel export               |
| `src/ogc-api/csapi/formats/sensorml/index.spec.ts`             | 82    | Tests for exports                  |

**Imports:** Self-contained module (no cross-format dependencies)  
**Depended on by:** Commit 8 (format index re-exports SensorML)

---

### Commit 7 — `feat(csapi): add Part 2 dynamic data format handlers`

**~1,424 lines** | Parses Part 2 resources: observations, commands, command status.

| File                                      | Lines | Description                               |
| ----------------------------------------- | ----- | ----------------------------------------- |
| `src/ogc-api/csapi/formats/part2.ts`      | 497   | Observation/Command/CommandStatus parsers |
| `src/ogc-api/csapi/formats/part2.spec.ts` | 927   | Comprehensive Part 2 tests                |

**Imports:** `./geojson.js` (uses `parseValidTime`)  
**Depended on by:** Commit 8 (format index re-exports Part 2)

---

### Commit 8 — `feat(csapi): add format pipeline — response, schema-response, and index`

**~1,403 lines** | Wires all format parsers into a unified pipeline.

| File                                                | Lines | Description                                             |
| --------------------------------------------------- | ----- | ------------------------------------------------------- |
| `src/ogc-api/csapi/formats/response.ts`             | 115   | Response wrapper for parsed CSAPI responses             |
| `src/ogc-api/csapi/formats/response.spec.ts`        | 193   | Tests for response handling                             |
| `src/ogc-api/csapi/formats/schema-response.ts`      | 165   | Schema-response parser (SWE Common observation schemas) |
| `src/ogc-api/csapi/formats/schema-response.spec.ts` | 336   | Tests for schema-response                               |
| `src/ogc-api/csapi/formats/index.ts`                | 298   | Format module barrel — re-exports all format parsers    |
| `src/ogc-api/csapi/formats/index.spec.ts`           | 296   | Tests for module exports and pipeline                   |

**Imports:** `./swecommon/parser.js`, `./swecommon/data-array.js`, `../model.js`  
**Depended on by:** Commit 12 (main library exports format types)

---

### Commit 9 — `test(csapi): add CSAPI test fixtures`

**~126 lines** | JSON fixture files for unit and integration tests.

| File                                                                  | Lines | Description                                 |
| --------------------------------------------------------------------- | ----- | ------------------------------------------- |
| `fixtures/ogc-api/csapi/sample-data-hub.json`                         | 30    | Root API document with CSAPI link relations |
| `fixtures/ogc-api/csapi/sample-data-hub/conformance.json`             | 11    | Conformance classes including CSAPI         |
| `fixtures/ogc-api/csapi/sample-data-hub/collections.json`             | 54    | Collection list with CSAPI links            |
| `fixtures/ogc-api/csapi/sample-data-hub/collections/iot-sensors.json` | 31    | Single collection with CSAPI links          |

**No code imports — test data only.**

---

### Commit 10 — `test(csapi): add integration test suites`

**~1,728 lines** | End-to-end integration tests exercising the full CSAPI stack.

| File                                                | Lines | Description                  |
| --------------------------------------------------- | ----- | ---------------------------- |
| `src/ogc-api/csapi/integration/discovery.spec.ts`   | 339   | Discovery flow tests         |
| `src/ogc-api/csapi/integration/navigation.spec.ts`  | 428   | Navigation between resources |
| `src/ogc-api/csapi/integration/observation.spec.ts` | 322   | Observation CRUD flows       |
| `src/ogc-api/csapi/integration/command.spec.ts`     | 359   | Command routing flows        |
| `src/ogc-api/csapi/integration/pipeline.spec.ts`    | 280   | Format pipeline integration  |

**Imports:** Full CSAPI module stack  
**Depended on by:** Nothing — leaf tests

---

### Commit 11 — `feat(csapi): integrate CSAPI detection into OgcApiEndpoint`

**~396 lines changed in upstream files** | Wires CSAPI into the existing library entry points.

| File                           | Lines Changed | Description                                                                                                     |
| ------------------------------ | ------------- | --------------------------------------------------------------------------------------------------------------- |
| `src/shared/mime-type.ts`      | +64           | `isMimeTypeSmlJson()`, `isMimeTypeSweJson()`, `isMimeTypeSweText()`, `isMimeTypeSweCsv()`, `isMimeTypeOmJson()` |
| `src/shared/mime-type.spec.ts` | +111          | Tests for all new mime-type detectors                                                                           |
| `src/ogc-api/info.ts`          | +31           | CSAPI conformance class URI constants                                                                           |
| `src/ogc-api/endpoint.ts`      | +135          | `csapi()` method, `csapiCollections` getter, `hasCSAPI` check, private CSAPI builder cache                      |
| `src/ogc-api/endpoint.spec.ts` | +53           | Tests for CSAPI endpoint integration                                                                            |

**This is the only commit that modifies existing upstream files (other than index and gitignore).**

---

### Commit 12 — `feat(csapi): export CSAPI from main library index`

**~184 lines changed** | Makes CSAPI available to library consumers.

| File           | Lines Changed | Description                                              |
| -------------- | ------------- | -------------------------------------------------------- |
| `src/index.ts` | +184          | Re-exports all CSAPI types, builders, and format parsers |

---

### Commit 13 — `chore: add .vscode and test-output to .gitignore`

**~2 lines changed** | Minor housekeeping.

| File         | Lines Changed | Description                                   |
| ------------ | ------------- | --------------------------------------------- |
| `.gitignore` | +2            | Add `.vscode` and `test-output*.txt` patterns |

---

## Commit Summary

| #   | Message                                                                   | New Files | Modified Files | ~Lines     |
| --- | ------------------------------------------------------------------------- | --------- | -------------- | ---------- |
| 1   | `feat(csapi): add CSAPI type definitions and model interfaces`            | 2         | 0              | 1,107      |
| 2   | `feat(csapi): add URL builder with CRUD query support`                    | 2         | 0              | 5,169      |
| 3   | `feat(csapi): add helper utilities and command routing`                   | 4         | 0              | 1,037      |
| 4   | `feat(csapi): add GeoJSON Part 1 format parsers`                          | 8         | 0              | 2,014      |
| 5   | `feat(csapi): add SWE Common data model parsers`                          | 14        | 0              | 6,373      |
| 6   | `feat(csapi): add SensorML procedure description parsers`                 | 14        | 0              | 5,787      |
| 7   | `feat(csapi): add Part 2 dynamic data format handlers`                    | 2         | 0              | 1,424      |
| 8   | `feat(csapi): add format pipeline — response, schema-response, and index` | 6         | 0              | 1,403      |
| 9   | `test(csapi): add CSAPI test fixtures`                                    | 4         | 0              | 126        |
| 10  | `test(csapi): add integration test suites`                                | 5         | 0              | 1,728      |
| 11  | `feat(csapi): integrate CSAPI detection into OgcApiEndpoint`              | 0         | 5              | 394        |
| 12  | `feat(csapi): export CSAPI from main library index`                       | 0         | 1              | 184        |
| 13  | `chore: add .vscode and test-output to .gitignore`                        | 0         | 1              | 2          |
|     | **TOTAL**                                                                 | **61**    | **7**          | **26,748** |

---

## Dependency Graph

```
Commit 1: model.ts (types)
    ├── Commit 2: url_builder.ts (imports model)
    │     └── Commit 3: helpers.ts, command-routing.ts (imports model + url_builder)
    ├── Commit 4: formats/geojson.ts, constants.ts, property.ts, classification.ts (imports model)
    │     └── Commit 7: formats/part2.ts (imports geojson)
    ├── Commit 5: formats/swecommon/* (self-contained)
    │     └── Commit 8: formats/schema-response.ts, response.ts, index.ts (imports swecommon + model)
    ├── Commit 6: formats/sensorml/* (self-contained)
    ├── Commit 9: fixtures (data only — no code deps)
    ├── Commit 10: integration tests (imports full stack)
    ├── Commit 11: endpoint.ts, info.ts, mime-type.ts (imports url_builder + helpers)
    ├── Commit 12: src/index.ts (re-exports everything)
    └── Commit 13: .gitignore (no deps)
```

---

## Execution Procedure

### Prerequisites

1. Clone `OS4CSAPI/ogc-client` locally (the fresh fork)
2. Have `ogc-client-CSAPI_2` available as the source

### For Each Commit (1–13):

```bash
# 1. Copy the files listed for that commit from ogc-client-CSAPI_2 → ogc-client
#    Preserving exact directory structure
# 2. Stage the files
git add <files>
# 3. Commit with the specified message
git commit -m "<commit message>"
# 4. Verify: run tsc (should have 0 errors through commit 12)
npx tsc --noEmit
# 5. Verify: run tests for the affected suite
npx jest --testPathPattern="csapi"
```

### After All Commits:

```bash
# Full verification
npx tsc --noEmit           # 0 errors
npx jest                   # All tests pass
git log --oneline          # 13 clean commits on top of upstream
git push origin main       # Push to OS4CSAPI/ogc-client
```

### Then:

- Open PR from `OS4CSAPI/ogc-client:main` → `camptocamp/ogc-client:main`
- Write PR description referencing OGC API - Connected Systems standard
- Request review from maintainers

---

## Notes

- Commits 1–10 are **purely additive** — they create new files in `src/ogc-api/csapi/` and `fixtures/ogc-api/csapi/`. They cannot break existing upstream code.
- Commit 11 is the **only one that touches upstream source files** (endpoint, info, mime-type). This is the commit reviewers will scrutinize most carefully.
- Commit 12 modifies `src/index.ts` to expose CSAPI — also modifies upstream, but is a simple additive re-export.
- Commit 13 is trivially small housekeeping.
- TypeScript compilation may not be clean until Commit 11–12 when the integration wiring is in place. Individual commits are locally self-consistent within the `csapi/` subtree.
