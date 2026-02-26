# Phase 6: Design Decision Resolution Report

**Date:** February 24, 2026
**Status:** All decisions resolved — zero open questions remain

---

## Summary

Before the 8-plan research arc, Phase 6 had genuine uncertainty on at least 10 design questions. Each had 2–7 viable alternatives. After 285 questions across 8 plans, every decision fork has been collapsed to a single path. The implementation guide is a linear sequence of mechanical steps with no remaining judgment calls.

---

## Decision Resolution Table

| Decision                                  | Alternatives Considered                         | Resolved To                                          | Confidence Basis                                                      |
| ----------------------------------------- | ----------------------------------------------- | ---------------------------------------------------- | --------------------------------------------------------------------- |
| Export structure                          | 4-condition, types-only, simple                 | 4-condition (`types/import/browser/default`)         | 6/6 library survey (Plan 03)                                          |
| Factory vs endpoint method                | Keep method, factory, static, mixin             | `createCSAPIBuilder()` async factory                 | 4/7 dominant pattern + jahow's constraint (Plan 04, Plan 06)          |
| Coupling level                            | Levels 1–5                                      | Level 3.5 (`Pick<>` + `import type`)                 | Existing constructor precedent (Plan 05)                              |
| `scanCsapiLinks` location                 | Move to shared, keep in CSAPI, generalize       | Keep in CSAPI (factory calls it)                     | Problem self-resolves (Plan 05 → Plan 06 override)                    |
| `root`/`getCollectionDocument` visibility | Keep private + friend pattern, accessor, public | Public (1-word change each)                          | Minimum delta, both already multi-use (Plan 06)                       |
| Commit strategy                           | Squash, amend, interleave, append               | 2 appended commits (format, then architecture)       | 5+ upstream formatting-commit precedents (Plan 07, Plan 08)           |
| `sideEffects`                             | `false`, array, omit                            | `false` (array fallback documented if worker breaks) | 5/6 libraries (Plan 03)                                               |
| `typesVersions`                           | Include, skip                                   | Skip                                                 | 5/6 libraries skip; only needed for TS <4.7 (Plan 03)                 |
| Boundary enforcement                      | ESLint rule, TS project refs, CI script, none   | None (git grep verification suffices)                | jahow didn't ask for it — minimum change principle (Plan 01, Plan 05) |
| Caching                                   | Auto-cache in factory, consumer-managed, both   | No auto-cache (endpoint already caches internally)   | Minimum change principle (Plan 04, Plan 06)                           |
| Test migration                            | Move all, keep all, selective                   | 2 move, 1 remove, 3 stay                             | Per-test dependency analysis (Plan 06, Plan 08)                       |

---

## Conditional Fallbacks

The only "conditional" items are documented fallback plans for known risks, not design decisions:

| Condition                                       | Trigger                                 | Fallback                                                                          |
| ----------------------------------------------- | --------------------------------------- | --------------------------------------------------------------------------------- |
| `"sideEffects": false` breaks worker-fallback   | Tests fail after adding to package.json | Switch to `"sideEffects": ["./dist/index.js", "./dist/worker-fallback/index.js"]` |
| `getCollectionDocument` public exposure concern | jahow objects during review             | Revert to private + alternative access pattern                                    |

These are contingency responses to test results or reviewer feedback — not open design questions.

---

## Conclusion

Every fork in the decision tree has been resolved through systematic research. The implementation path forward is fully linear: create 3 files with specified content, make specific edits to 4 files, run 12 verification commands. Zero judgment calls remain between now and a completed Phase 6.
