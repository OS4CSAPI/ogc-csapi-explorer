# Documentation Inventory

**Date:** February 19, 2026  
**Purpose:** Flat catalog of every document in `docs/` with one-line descriptions, organized by folder. No analysis, no recommendations — just what exists.

**Total documents:** 208 (excluding `.gitkeep` files and OpenAPI YAML specs)

---

## docs/governance/ (12 files)

| #   | File                                                                                                                                                            | Description                                                                                                           |
| --- | --------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| 1   | [AI_Collaboration_Agreement.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/governance/AI_Collaboration_Agreement.md)                         | Governing reference for human–AI development collaboration on this project                                            |
| 2   | [AI_OPERATIONAL_CONSTRAINTS.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/governance/AI_OPERATIONAL_CONSTRAINTS.md)                         | Non-negotiable operational constraints for AI to prevent architectural drift, scope creep, and standards misalignment |
| 3   | [code-review-prompt-template.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/governance/code-review-prompt-template.md)                       | Reusable prompt for AI-generated code reviews (Phase 1–2)                                                             |
| 4   | [code-review-prompt-template-phase-3.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/governance/code-review-prompt-template-phase-3.md)       | Reusable prompt for AI-generated code reviews during Phase 3                                                          |
| 5   | [issue-creation-prompt-template.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/governance/issue-creation-prompt-template.md)                 | Template for creating uniform GitHub issues for the 33 ROADMAP tasks                                                  |
| 6   | [issue-creation-prompt-template-phase-4.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/governance/issue-creation-prompt-template-phase-4.md) | Template for creating GitHub issues covering ROADMAP tasks and finding-driven issues (Phase 4, v2.0)                  |
| 7   | [known-server-quirks.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/governance/known-server-quirks.md)                                       | Reference of known behaviors, bugs, and content-negotiation quirks for the two CSAPI test servers                     |
| 8   | [phase-2-lessons-learned.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/governance/phase-2-lessons-learned.md)                               | Actionable lessons from Phase 1–2.8 code reviews, smoke tests, and fix reports                                        |
| 9   | [phase-3-lessons-learned.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/governance/phase-3-lessons-learned.md)                               | Actionable lessons from Phase 3 covering parser/format handler failure modes and server tolerance                     |
| 10  | [smoke-test-prompt-template.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/governance/smoke-test-prompt-template.md)                         | Reusable prompt for AI-driven live server smoke tests (Phase 2)                                                       |
| 11  | [smoke-test-prompt-template-phase-3.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/governance/smoke-test-prompt-template-phase-3.md)         | Reusable prompt for AI-driven smoke tests validating format handlers (Phase 3)                                        |
| 12  | [smoke-test-prompt-template-phase-4.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/governance/smoke-test-prompt-template-phase-4.md)         | Exhaustive end-to-end smoke test prompt covering full CRUD, Part 2, SensorML, cross-server (Phase 4)                  |

---

## docs/planning/ (3 active + 17 archived)

### Active

| #   | File                                                                                                                                              | Description                                                                                                   |
| --- | ------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| 13  | [contribution-goal-and-definition.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/planning/contribution-goal-and-definition.md) | Defines the contribution goal of enabling CSAPI interaction through the ogc-client unified interface          |
| 14  | [csapi-implementation-guide.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/planning/csapi-implementation-guide.md)             | Complete implementation guide for adding CSAPI support to the Camptocamp OGC Client Library (current version) |
| 15  | [ROADMAP.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/planning/ROADMAP.md)                                                   | Four-phase implementation roadmap spanning 57–84 hours across 8–11 weeks (current version)                    |

### Archive (planning/archive/)

| #   | File                                                                                                                                                            | Description                                                                      |
| --- | --------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------- |
| 16  | [component-architecture.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/planning/archive/component-architecture.md)                           | Every component needed for CSAPI support, extensions vs new code (Feb 1 version) |
| 17  | [csapi-component-architecture.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/planning/archive/csapi-component-architecture.md)               | Every component needed for CSAPI support, extensions vs new code (Feb 2 version) |
| 18  | [csapi-implementation-guide-v1.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/planning/archive/csapi-implementation-guide-v1.md)             | Implementation guide v1.0 — initial version                                      |
| 19  | [csapi-implementation-guide-v2.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/planning/archive/csapi-implementation-guide-v2.md)             | Implementation guide v2.0 — research-validated                                   |
| 20  | [csapi-implementation-guide-v3.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/planning/archive/csapi-implementation-guide-v3.md)             | Implementation guide v3.0 — implementation-ready                                 |
| 21  | [csapi-implementation-guide-v4.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/planning/archive/csapi-implementation-guide-v4.md)             | Implementation guide v4.0 — implementation-ready (revised)                       |
| 22  | [csapi-implementation-guide-v5.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/planning/archive/csapi-implementation-guide-v5.md)             | Implementation guide v5.0 — architecture-validated with real-world scenarios     |
| 23  | [csapi-implementation-guide-v6.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/planning/archive/csapi-implementation-guide-v6.md)             | Implementation guide v6.0 — complete self-contained guide                        |
| 24  | [csapi-implementation-guide-v7.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/planning/archive/csapi-implementation-guide-v7.md)             | Implementation guide v7.0 — complete with query parameters reference             |
| 25  | [FEATURE_SPEC.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/planning/archive/FEATURE_SPEC.md)                                               | Feature specification for CSAPI v1.0 client implementation                       |
| 26  | [functional-spec.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/planning/archive/functional-spec.md)                                         | Functional specification v1.0 Draft                                              |
| 27  | [hypothetical-technical-architecture.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/planning/archive/hypothetical-technical-architecture.md) | Exhaustive list of every feature that could be built based on all research       |
| 28  | [phase1-reconnaissance-report.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/planning/archive/phase1-reconnaissance-report.md)               | Reconnaissance report for restoring 18 missing sections from v1 into v6          |
| 29  | [ROADMAP-v1.0.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/planning/archive/ROADMAP-v1.0.md)                                               | Roadmap v8.0 (confusingly named): four-phase plan spanning 60–88 hours           |
| 30  | [ROADMAP-v2.0.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/planning/archive/ROADMAP-v2.0.md)                                               | Roadmap v2.0: restructured for incremental testing across four phases            |
| 31  | [technical-architecture.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/planning/archive/technical-architecture.md)                           | Simple list of everything to create, centered on CSAPIEndpoint                   |
| 32  | [vision-and-scope.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/planning/archive/vision-and-scope.md)                                       | Vision and scope document v1.0 Final                                             |

---

## docs/implementation/ (61 files)

### Phase Overviews & Assessments

| #   | File                                                                                                                                              | Description                                                                     |
| --- | ------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| 33  | [phase-0-baseline-assessment.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/implementation/phase-0-baseline-assessment.md)     | "Before" snapshot of the forked repo's inherited state                          |
| 34  | [phase-1-overview.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/implementation/phase-1-overview.md)                           | Phase 1 overview: type system, URL construction, data structure parsing         |
| 35  | [phase-1-completion-assessment.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/implementation/phase-1-completion-assessment.md) | Phase 1 completion: all 4 issues implemented, tested, committed, pushed, closed |
| 36  | [phase-2-overview.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/implementation/phase-2-overview.md)                           | Phase 2 overview: full URL-building support for every CSAPI resource type       |
| 37  | [phase-2.1-overview.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/implementation/phase-2.1-overview.md)                       | Phase 2.1: stub query builder → complete Systems API surface (12 methods)       |
| 38  | [phase-2.2-overview.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/implementation/phase-2.2-overview.md)                       | Phase 2.2: Deployments surface, live smoke test findings, DRY refactor          |
| 39  | [phase-2.3-overview.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/implementation/phase-2.3-overview.md)                       | Phase 2.3: Procedures surface plus fixes from prior findings                    |

### Code Reviews

| #   | File                                                                                                                                | Description                                                                                      |
| --- | ----------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| 40  | [phase-1-code-review.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/implementation/phase-1-code-review.md)       | Code review for all Phase 1 deliverables (Issues #1–#4)                                          |
| 41  | [phase-1-fix-report.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/implementation/phase-1-fix-report.md)         | Fix report for findings F1 and F5 from Phase 1 code review                                       |
| 42  | [phase-2.2-code-review.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/implementation/phase-2.2-code-review.md)   | Issues #5, #6, #34, #35 (Systems, Deployments, live-server fixes)                                |
| 43  | [phase-2.3-code-review.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/implementation/phase-2.3-code-review.md)   | Issue #7: 8 Procedures methods                                                                   |
| 44  | [phase-2.4-code-review.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/implementation/phase-2.4-code-review.md)   | Issue #8 (SamplingFeatures) and Issue #39 (Convention 3 link detection)                          |
| 45  | [phase-2.5-code-review.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/implementation/phase-2.5-code-review.md)   | Issue #40 (open code review findings) and Issue #9 (Properties)                                  |
| 46  | [phase-2.6-code-review.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/implementation/phase-2.6-code-review.md)   | Issue #41 (gap findings fix) and Issue #10 (DataStreams — first Part 2)                          |
| 47  | [phase-2.7-code-review.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/implementation/phase-2.7-code-review.md)   | Issue #43 (resultTime=latest type fix) and Issue #11 (Observations)                              |
| 48  | [phase-2.8-code-review.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/implementation/phase-2.8-code-review.md)   | Issue #12: 8 Control Streams methods                                                             |
| 49  | [phase-2.9-code-review.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/implementation/phase-2.9-code-review.md)   | Issue #13: Commands methods (final Phase 2 resource type)                                        |
| 50  | [phase-3.1-code-review.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/implementation/phase-3.1-code-review.md)   | Issue #14 (GeoJSON Handler Extensions) and Issue #46 (Commands backfill)                         |
| 51  | [phase-3.2-code-review.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/implementation/phase-3.2-code-review.md)   | SensorML vocabulary, format detector extensions, validator extensions (Issues #49, #15, #16)     |
| 52  | [phase-3.3-code-review.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/implementation/phase-3.3-code-review.md)   | Validator removal and SWE Common type definitions (Issues #52, #17)                              |
| 53  | [phase-3.4-code-review.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/implementation/phase-3.4-code-review.md)   | SensorML 3.0 type definitions (Issue #18)                                                        |
| 54  | [phase-3.5-code-review.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/implementation/phase-3.5-code-review.md)   | SensorML SimpleProcess sub-parser (Issue #19)                                                    |
| 55  | [phase-3.6-code-review.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/implementation/phase-3.6-code-review.md)   | AggregateProcess sub-parser and validation sweep (Issue #20)                                     |
| 56  | [phase-3.7-code-review.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/implementation/phase-3.7-code-review.md)   | SensorML PhysicalSystem & PhysicalComponent sub-parsers (Issue #21)                              |
| 57  | [phase-3.8-code-review.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/implementation/phase-3.8-code-review.md)   | SensorML main parser, SensorMLParseError extraction, barrel file (Issues #22, #23, #53)          |
| 58  | [phase-3.9-code-review.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/implementation/phase-3.9-code-review.md)   | SWE Common simple components parser (Issue #24)                                                  |
| 59  | [phase-3.10-code-review.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/implementation/phase-3.10-code-review.md) | DataRecord parser and SensorML helper consolidation (Issues #25, #54)                            |
| 60  | [phase-3.11-code-review.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/implementation/phase-3.11-code-review.md) | DataArray parser and `satisfies` cast cleanup (Issues #26, #55)                                  |
| 61  | [phase-3.12-code-review.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/implementation/phase-3.12-code-review.md) | Main parser, barrel files, constants, response parser, classification (Issues #27–#30, #36, #50) |
| 62  | [phase-3.13-code-review.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/implementation/phase-3.13-code-review.md) | Nested create methods, Content-Type constants, JSDoc, bug fixes (Issues #57–#69)                 |
| 63  | [phase-3.14-code-review.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/implementation/phase-3.14-code-review.md) | Quick-fix batch and `as unknown as T` cast elimination (Issues #70–#74)                          |
| 64  | [phase-3.15-code-review.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/implementation/phase-3.15-code-review.md) | data-record.ts cast elimination and parseAssociationAttributeGroup DRY extraction (Issue #75)    |
| 65  | [phase-3.16-code-review.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/implementation/phase-3.16-code-review.md) | parseAssociationAttributeGroup self-validation fix (Phase 3.15 F4)                               |
| 66  | [phase-3.17-code-review.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/implementation/phase-3.17-code-review.md) | SSN namespace recognition and Deployment validTime made optional (Issues #76, #77)               |

### Smoke Test Reports (19 total)

| #   | File                                                                                                                                                                | Description                                                                            |
| --- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| 67  | [live-server-smoke-test-post-phase-2.1.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/implementation/live-server-smoke-test-post-phase-2.1.md)   | ST#1: First live test validating Phase 1 + 2.1 against OpenSensorHub                   |
| 68  | [live-server-retest-post-issues-34-35.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/implementation/live-server-retest-post-issues-34-35.md)     | ST#2: Re-test verifying Issues #34/#35 resolve critical F1/F2 findings                 |
| 69  | [live-server-smoke-test-post-phase-2.2.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/implementation/live-server-smoke-test-post-phase-2.2.md)   | ST#3: Validates Phase 2.2 fixes against OpenSensorHub                                  |
| 70  | [live-server-smoke-test-post-phase-2.3.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/implementation/live-server-smoke-test-post-phase-2.3.md)   | ST#4: Validates all 28 builder methods with 8 new Procedures methods                   |
| 71  | [live-server-smoke-test-post-phase-2.4.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/implementation/live-server-smoke-test-post-phase-2.4.md)   | ST#5: Validates 36 methods against two servers (OSH + 52North), 8 new SamplingFeatures |
| 72  | [live-server-smoke-test-post-phase-2.5.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/implementation/live-server-smoke-test-post-phase-2.5.md)   | ST#6: Validates 6 new Properties methods and regression checks                         |
| 73  | [live-server-smoke-test-post-phase-2.6.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/implementation/live-server-smoke-test-post-phase-2.6.md)   | ST#7: Validates 11 new DataStreams methods (first Part 2) across both servers          |
| 74  | [live-server-smoke-test-post-phase-2.7.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/implementation/live-server-smoke-test-post-phase-2.7.md)   | ST#8: Validates 8 Observations methods, resultTime=latest fix, 61 total methods        |
| 75  | [live-server-smoke-test-post-phase-2.8.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/implementation/live-server-smoke-test-post-phase-2.8.md)   | ST#9: Validates 8 ControlStreams methods across all 69 methods                         |
| 76  | [live-server-smoke-test-post-phase-2.9.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/implementation/live-server-smoke-test-post-phase-2.9.md)   | ST#10: Validates 10 Commands methods and 3 backfill tests                              |
| 77  | [live-server-smoke-test-52north.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/implementation/live-server-smoke-test-52north.md)                 | ST#11: Cross-implementation test against 52North pygeoapi demo server                  |
| 78  | [live-server-smoke-test-post-phase-3.1.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/implementation/live-server-smoke-test-post-phase-3.1.md)   | ST#12: GeoJSON handler functions against real server responses                         |
| 79  | [live-server-smoke-test-post-phase-3.2.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/implementation/live-server-smoke-test-post-phase-3.2.md)   | ST#13: GeoJSON handler improvements, format detector, validator extensions             |
| 80  | [live-server-smoke-test-post-phase-3.3.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/implementation/live-server-smoke-test-post-phase-3.3.md)   | ST#14: Extraction success after validator removal                                      |
| 81  | [live-server-smoke-test-post-phase-3.4.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/implementation/live-server-smoke-test-post-phase-3.4.md)   | ST#15: SensorML type alignment against real server data                                |
| 82  | [live-server-smoke-test-post-phase-3.5.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/implementation/live-server-smoke-test-post-phase-3.5.md)   | ST#16: SimpleProcess parser with corrected Accept headers                              |
| 83  | [live-server-smoke-test-post-phase-3.7.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/implementation/live-server-smoke-test-post-phase-3.7.md)   | ST#17: All four SensorML sub-parsers against live data                                 |
| 84  | [live-server-smoke-test-post-phase-3.11.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/implementation/live-server-smoke-test-post-phase-3.11.md) | ST#18: SWE Common parsers and satisfies migration validation                           |
| 85  | [live-server-smoke-test-post-phase-3.12.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/implementation/live-server-smoke-test-post-phase-3.12.md) | ST#18b: Response envelope parser, classification fallback, format constants            |
| 86  | [live-server-smoke-test-post-phase-3.16.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/implementation/live-server-smoke-test-post-phase-3.16.md) | ST#18c: Issues #57–#75 validation, 1,159 passing tests, 25 suites                      |
| 87  | [live-server-smoke-test-post-phase-4.1.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/implementation/live-server-smoke-test-post-phase-4.1.md)   | ST#19: Full CRUD testing, 1,525 passed, 5 failed (pre-existing), 53 suites             |

### Design Notes & Special Reports

| #   | File                                                                                                                                                                              | Description                                                                          |
| --- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------ |
| 88  | [cross-server-interoperability-analysis.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/implementation/cross-server-interoperability-analysis.md)               | Comparative testing of OSH and 52North to distinguish client bugs from server issues |
| 89  | [design-notes-validation-extraction-decoupling.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/implementation/design-notes-validation-extraction-decoupling.md) | Decision to remove feature-level validators from scope (triggered by F49)            |
| 90  | [f57-content-negotiation-correction.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/implementation/f57-content-negotiation-correction.md)                       | Correction of false finding F57 (AI-changed Accept header between tests)             |
| 91  | [note-crud-smoke-test-readiness.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/implementation/note-crud-smoke-test-readiness.md)                               | Assessment of when CRUD operations can be added to smoke tests                       |
| 92  | [note-F71-osh-accept-header-noncompliance.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/implementation/note-F71-osh-accept-header-noncompliance.md)           | OSH ignores all HTTP Accept headers, only supports `?f=` query parameter             |
| 93  | [phase-3-smoke-test-rationale.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/implementation/phase-3-smoke-test-rationale.md)                                   | Decision rationale for continuing live smoke testing into Phase 3                    |
| 94  | [server-quirks-reference.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/implementation/server-quirks-reference.md)                                             | Complete server quirks reference compiled from 18 smoke tests, all findings F1–F90   |

---

## docs/research/ (root level — 1 file + 2 specs)

| #   | File                                                                                                                                                                          | Description                                                      |
| --- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------- |
| 95  | [references.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/references.md)                                                                         | Annotated bibliography of key resources for CSAPI implementation |
| —   | [ogcapi-connectedsystems-1.bundled.oas31.yaml](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/standards/ogcapi-connectedsystems-1.bundled.oas31.yaml) | Part 1 OpenAPI 3.1 spec (bundled)                                |
| —   | [ogcapi-connectedsystems-2.bundled.oas31.yaml](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/standards/ogcapi-connectedsystems-2.bundled.oas31.yaml) | Part 2 OpenAPI 3.1 spec (bundled)                                |

---

## docs/research/requirements/ (23 files)

| #   | File                                                                                                                                                               | Description                                                                             |
| --- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------- |
| 96  | [requirements-research-strategy.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/requirements/requirements-research-strategy.md)         | Systematic research-first methodology for identifying all functional requirements       |
| 97  | [contribution-definition.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/requirements/contribution-definition.md)                       | Complete implementation scope covering Part 1 + Part 2 resources and format abstraction |
| 98  | [csapi-part1-requirements.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/requirements/csapi-part1-requirements.md)                     | Requirements analysis of Part 1: Feature Resources (OGC 23-001)                         |
| 99  | [csapi-part2-requirements.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/requirements/csapi-part2-requirements.md)                     | Requirements analysis of Part 2: Dynamic Data (OGC 23-002)                              |
| 100 | [csapi-conformance-capabilities.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/requirements/csapi-conformance-capabilities.md)         | All conformance classes, detection mechanisms, and capability discovery patterns        |
| 101 | [csapi-crud-operations.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/requirements/csapi-crud-operations.md)                           | All CRUD operations, HTTP method mappings, and client implementation needs              |
| 102 | [csapi-datatype-schema-requirements.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/requirements/csapi-datatype-schema-requirements.md) | Type system requirements and scope from OpenAPI schemas                                 |
| 103 | [csapi-format-requirements.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/requirements/csapi-format-requirements.md)                   | Comprehensive format requirements analysis (Section 3)                                  |
| 104 | [csapi-format-requirements-3.1.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/requirements/csapi-format-requirements-3.1.md)           | Common format requirements and content negotiation mechanisms                           |
| 105 | [csapi-gap-analysis.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/requirements/csapi-gap-analysis.md)                                 | Gaps, errors, and lessons from first implementation attempt                             |
| 106 | [csapi-query-parameters.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/requirements/csapi-query-parameters.md)                         | All query parameters including encoding rules, validation, and client needs             |
| 107 | [csapi-subresource-navigation.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/requirements/csapi-subresource-navigation.md)             | All sub-resource navigation patterns and nesting hierarchy                              |
| 108 | [csapi-usage-scenarios.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/requirements/csapi-usage-scenarios.md)                           | Real-world usage scenario requirements and priorities                                   |
| 109 | [csapi-52north-analysis.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/requirements/csapi-52north-analysis.md)                         | 52North Python CSAPI server analyzed for multi-server compatibility                     |
| 110 | [csapi-cpp-analysis.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/requirements/csapi-cpp-analysis.md)                                 | ConnectedSystemsAPI-CPP C++ client analyzed for TypeScript design insights              |
| 111 | [csapi-opensensorhub-analysis.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/requirements/csapi-opensensorhub-analysis.md)             | OpenSensorHub server-side CSAPI analyzed for client design                              |
| 112 | [csapi-oscarviewer-analysis.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/requirements/csapi-oscarviewer-analysis.md)                 | oscar-viewer TypeScript React CSAPI client patterns analyzed                            |
| 113 | [csapi-oshconnect-python-analysis.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/requirements/csapi-oshconnect-python-analysis.md)     | OSHConnect-Python CSAPI client compared to OWSLib                                       |
| 114 | [OSHConnect-Python-Analysis.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/requirements/OSHConnect-Python-Analysis.md)                 | OSHConnect-Python client research for TypeScript design                                 |
| 115 | [csapi-oshviewer-analysis.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/requirements/csapi-oshviewer-analysis.md)                     | osh-viewer Vue.js CSAPI client patterns analyzed                                        |
| 116 | [csapi-owslib-analysis.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/requirements/csapi-owslib-analysis.md)                           | OWSLib Python CSAPI implementation analyzed for TypeScript design                       |
| 117 | [lessons-learned-analysis.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/requirements/lessons-learned-analysis.md)                     | What worked, what didn't from previous attempts (third iteration)                       |
| 118 | [upstream-expectations.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/requirements/upstream-expectations.md)                           | Upstream camptocamp/ogc-client expectations for new API implementations                 |

---

## docs/research/upstream/ (11 files + 1 archive)

| #   | File                                                                                                                                                                               | Description                                                                    |
| --- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------ |
| 119 | [architecture-patterns-analysis.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/upstream/architecture-patterns-analysis.md)                             | Consistent architectural patterns in ogc-client for adding new OGC API support |
| 120 | [code-reuse-analysis.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/upstream/code-reuse-analysis.md)                                                   | When to reuse upstream utilities vs duplicate for CSAPI                        |
| 121 | [csapi-architecture-analysis.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/upstream/csapi-architecture-analysis.md)                                   | Architectural choices for 9 CSAPI resource types within ogc-client patterns    |
| 122 | [error-handling-analysis.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/upstream/error-handling-analysis.md)                                           | Error handling patterns to guide CSAPI error strategy                          |
| 123 | [file-organization-analysis.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/upstream/file-organization-analysis.md)                                     | File organization patterns to guide CSAPI structure                            |
| 124 | [format-negotiation-analysis.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/upstream/format-negotiation-analysis.md)                                   | Format negotiation patterns (GeoJSON, JSON-FG, SensorML)                       |
| 125 | [integration-analysis.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/upstream/integration-analysis.md)                                                 | Exact code changes required to integrate CSAPI into OgcApiEndpoint             |
| 126 | [pr114-analysis.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/upstream/pr114-analysis.md)                                                             | PR #114 (EDR) as direct blueprint for CSAPI implementation                     |
| 127 | [querybuilder-pattern-analysis.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/upstream/querybuilder-pattern-analysis.md)                               | QueryBuilder pattern for API-specific query operations                         |
| 128 | [typescript-types-analysis.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/upstream/typescript-types-analysis.md)                                       | TypeScript type organization for CSAPI's 9 resource types                      |
| 129 | [url-building-analysis.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/upstream/url-building-analysis.md)                                               | URL building patterns for 9 resource types with nested paths                   |
| 130 | [archive/csapi-architecture-analysis-original.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/upstream/archive/csapi-architecture-analysis-original.md) | Architecture decisions for 9 CSAPI types without bloat (original version)      |

---

## docs/research/design/ (1 + 8 component folders)

| #   | File                                                                                                                   | Description                                                         |
| --- | ---------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------- |
| 131 | [design-sequence.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/design/design-sequence.md) | Optimal order for designing each CSAPI component to minimize rework |

### design/collections-reader/

| #   | File                                                                                                                                                                        | Description                                                         |
| --- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------- |
| 132 | [collections-reader-research-plan.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/design/collections-reader/collections-reader-research-plan.md) | Design research plan for Collections Reader (Phase 1, Component #3) |
| 133 | [collections-reader-analysis.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/design/collections-reader/collections-reader-analysis.md)           | Complete analysis and blueprint for collection filtering            |

### design/conformance-reader/

| #   | File                                                                                                                                                                        | Description                                                         |
| --- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------- |
| 134 | [conformance-reader-research-plan.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/design/conformance-reader/conformance-reader-research-plan.md) | Design research plan for Conformance Reader (Phase 1, Component #2) |
| 135 | [conformance-reader-analysis.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/design/conformance-reader/conformance-reader-analysis.md)           | Complete analysis and blueprint for conformance detection           |

### design/ogcapiendpoint-integration/

| #   | File                                                                                                                                                                                                | Description                                                                 |
| --- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------- |
| 136 | [ogcapiendpoint-integration-research-plan.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/design/ogcapiendpoint-integration/ogcapiendpoint-integration-research-plan.md) | Design research plan for OgcApiEndpoint integration (Phase 1, Component #1) |
| 137 | [ogcapiendpoint-integration-analysis.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/design/ogcapiendpoint-integration/ogcapiendpoint-integration-analysis.md)           | Complete analysis report for OgcApiEndpoint integration                     |

### design/csapiquerybuilder/ (2 archive + 22 research plans + 11 findings + 4 results)

#### Architecture Decision Research Plans

| #   | File                                                                                                                                                                                           | Description                                                                |
| --- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------- |
| 138 | [01-pr114-edr-pattern.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/design/csapiquerybuilder/architecture-decision/01-pr114-edr-pattern.md)                       | Does upstream mandate a single QueryBuilder class via the PR #114 pattern? |
| 139 | [02-querybuilder-pattern.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/design/csapiquerybuilder/architecture-decision/02-querybuilder-pattern.md)                 | Does the QueryBuilder pattern inherently require a single class?           |
| 140 | [03-csapi-architecture-decisions.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/design/csapiquerybuilder/architecture-decision/03-csapi-architecture-decisions.md) | Are existing CSAPI architecture decisions still valid?                     |
| 141 | [04-architecture-patterns.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/design/csapiquerybuilder/architecture-decision/04-architecture-patterns.md)               | ogc-client pattern survey — single-class vs multi-class preference?        |
| 142 | [05-owslib-pattern.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/design/csapiquerybuilder/architecture-decision/05-owslib-pattern.md)                             | OWSLib's class-per-resource architecture compared                          |
| 143 | [06-oshconnect-detailed.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/design/csapiquerybuilder/architecture-decision/06-oshconnect-detailed.md)                   | OSHConnect-Python stateful builder pattern detailed analysis               |
| 144 | [07-oshconnect-summary.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/design/csapiquerybuilder/architecture-decision/07-oshconnect-summary.md)                     | OSHConnect-Python key takeaways for architecture decisions                 |
| 145 | [08-oscar-viewer.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/design/csapiquerybuilder/architecture-decision/08-oscar-viewer.md)                                 | oscar-viewer TypeScript patterns for CSAPI organization                    |
| 146 | [09-osh-viewer.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/design/csapiquerybuilder/architecture-decision/09-osh-viewer.md)                                     | osh-viewer Vue.js client patterns for CSAPI organization                   |
| 147 | [10-upstream-expectations.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/design/csapiquerybuilder/architecture-decision/10-upstream-expectations.md)               | camptocamp/ogc-client expectations for class patterns                      |
| 148 | [11-integration-requirements.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/design/csapiquerybuilder/architecture-decision/11-integration-requirements.md)         | Class structure impact on integration code complexity                      |
| 149 | [12-file-organization.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/design/csapiquerybuilder/architecture-decision/12-file-organization.md)                       | Single-class vs multi-class file organization impacts                      |
| 150 | [13-typescript-types.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/design/csapiquerybuilder/architecture-decision/13-typescript-types.md)                         | Class structure impact on TypeScript type safety                           |
| 151 | [14-usage-scenarios.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/design/csapiquerybuilder/architecture-decision/14-usage-scenarios.md)                           | Common usage scenarios — single vs multi-class preference                  |
| 152 | [15-query-parameters.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/design/csapiquerybuilder/architecture-decision/15-query-parameters.md)                         | Query parameter complexity — class organization impacts                    |
| 153 | [16-subresource-navigation.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/design/csapiquerybuilder/architecture-decision/16-subresource-navigation.md)             | Nested resource patterns — class organization impacts                      |
| 154 | [17-part1-scope.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/design/csapiquerybuilder/architecture-decision/17-part1-scope.md)                                   | Part 1 scope (5 types, 70+ operations) — single-class feasible?            |
| 155 | [18-part2-scope.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/design/csapiquerybuilder/architecture-decision/18-part2-scope.md)                                   | Part 2 dynamic data complexity — architecture impact                       |
| 156 | [19-lessons-learned.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/design/csapiquerybuilder/architecture-decision/19-lessons-learned.md)                           | Architectural lessons from previous attempts                               |
| 157 | [20-gap-analysis.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/design/csapiquerybuilder/architecture-decision/20-gap-analysis.md)                                 | Gaps from first attempt related to architecture decisions                  |
| 158 | [21-part1-openapi.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/design/csapiquerybuilder/architecture-decision/21-part1-openapi.md)                               | Part 1 OpenAPI endpoint organization for class structure                   |
| 159 | [22-part2-openapi.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/design/csapiquerybuilder/architecture-decision/22-part2-openapi.md)                               | Part 2 OpenAPI dynamic resource organization boundaries                    |

#### Findings (completed research)

| #   | File                                                                                                                                                                                                                      | Description                                     |
| --- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------- |
| 160 | [01-pr114-edr-pattern-findings.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/design/csapiquerybuilder/architecture-decision/findings/01-pr114-edr-pattern-findings.md)                       | PR #114 EDR pattern analysis results            |
| 161 | [02-querybuilder-pattern-findings.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/design/csapiquerybuilder/architecture-decision/findings/02-querybuilder-pattern-findings.md)                 | QueryBuilder pattern core concepts results      |
| 162 | [03-csapi-architecture-decisions-findings.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/design/csapiquerybuilder/architecture-decision/findings/03-csapi-architecture-decisions-findings.md) | Existing architecture decision validity results |
| 163 | [04-architecture-patterns-findings.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/design/csapiquerybuilder/architecture-decision/findings/04-architecture-patterns-findings.md)               | ogc-client architectural patterns results       |
| 164 | [10-upstream-expectations-findings.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/design/csapiquerybuilder/architecture-decision/findings/10-upstream-expectations-findings.md)               | Upstream expectations results                   |
| 165 | [11-integration-requirements-findings.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/design/csapiquerybuilder/architecture-decision/findings/11-integration-requirements-findings.md)         | Integration code complexity results             |
| 166 | [12-file-organization-findings.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/design/csapiquerybuilder/architecture-decision/findings/12-file-organization-findings.md)                       | File organization implications results          |
| 167 | [13-typescript-types-findings.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/design/csapiquerybuilder/architecture-decision/findings/13-typescript-types-findings.md)                         | TypeScript type organization results            |
| 168 | [14-usage-scenarios-findings.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/design/csapiquerybuilder/architecture-decision/findings/14-usage-scenarios-findings.md)                           | Usage scenario analysis results                 |
| 169 | [15-query-parameters-findings.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/design/csapiquerybuilder/architecture-decision/findings/15-query-parameters-findings.md)                         | Query parameter complexity results              |
| 170 | [16-subresource-navigation-findings.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/design/csapiquerybuilder/architecture-decision/findings/16-subresource-navigation-findings.md)             | Nested resource patterns results                |

#### Architecture Decision Results

| #   | File                                                                                                                                                                                                           | Description                                                 |
| --- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------- |
| 171 | [DECISION-part1-structure.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/design/csapiquerybuilder/architecture-decision/results/DECISION-part1-structure.md)                       | Final decision on CSAPIQueryBuilder structural design       |
| 172 | [DECISION-part2-implementation.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/design/csapiquerybuilder/architecture-decision/results/DECISION-part2-implementation.md)             | Final decision on CSAPIQueryBuilder implementation details  |
| 173 | [DECISION-part3-validation.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/design/csapiquerybuilder/architecture-decision/results/DECISION-part3-validation.md)                     | Final decision on CSAPIQueryBuilder architecture validation |
| 174 | [LESSONS-LEARNED-multi-class-failure.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/design/csapiquerybuilder/architecture-decision/results/LESSONS-LEARNED-multi-class-failure.md) | Post-mortem: why multi-class architecture failed twice      |

#### Archive

| #   | File                                                                                                                                                                             | Description                                                                    |
| --- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------ |
| 175 | [csapiquerybuilder-analysis.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/design/csapiquerybuilder/archive/csapiquerybuilder-analysis.md)           | Component analysis from Session 1 foundation research                          |
| 176 | [csapiquerybuilder-research-plan.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/design/csapiquerybuilder/archive/csapiquerybuilder-research-plan.md) | Original research plan (single class, ~10k-14k lines, EDRQueryBuilder pattern) |

### Empty design folders (scaffolded, no content)

- design/api-documentation/
- design/background-processing/
- design/format-detector/
- design/geojson-handler/
- design/sensorml-handler/
- design/swe-common-handler/
- design/test-coverage/
- design/validator/

---

## docs/research/strategy/ (1 file)

| #   | File                                                                                                                                       | Description                                                                  |
| --- | ------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------- |
| 177 | [design-strategy-research.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/strategy/design-strategy-research.md) | Architectural design strategy research to complete before any implementation |

---

## docs/research/testing/ (38 research plans + 38 findings + 12 reviews + 1 strategy)

### Strategy

| #   | File                                                                                                                                        | Description                                                            |
| --- | ------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------- |
| 178 | [testing-strategy-research.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/testing/testing-strategy-research.md) | Comprehensive research plan for production-quality CSAPI test coverage |

### Research Plans (research-plans/)

| #   | File                                                                                                                                                                                             | Description                                                    |
| --- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------- |
| 179 | [01-pr114-blueprint-analysis.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/testing/research-plans/01-pr114-blueprint-analysis.md)                                   | Analyze PR #114 as blueprint for CSAPI test patterns           |
| 180 | [02-upstream-test-consistency.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/testing/research-plans/02-upstream-test-consistency.md)                                 | Survey existing upstream test patterns for consistency         |
| 181 | [03-typescript-testing-standards.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/testing/research-plans/03-typescript-testing-standards.md)                           | TypeScript client library testing best practices               |
| 182 | [04-implementation-guide-testing-requirements.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/testing/research-plans/04-implementation-guide-testing-requirements.md) | Testing requirements from the CSAPI implementation guide       |
| 183 | [05-roadmap-testing-integration.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/testing/research-plans/05-roadmap-testing-integration.md)                             | When to write tests across 34 roadmap tasks                    |
| 184 | [06-meaningful-vs-trivial-definition.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/testing/research-plans/06-meaningful-vs-trivial-definition.md)                   | Quality criteria distinguishing meaningful from trivial tests  |
| 185 | [07-end-to-end-testing-scope.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/testing/research-plans/07-end-to-end-testing-scope.md)                                   | End-to-end testing scope and boundaries                        |
| 186 | [08-csapi-specification-test-requirements.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/testing/research-plans/08-csapi-specification-test-requirements.md)         | CSAPI spec-derived test requirements (~4,800 lines)            |
| 187 | [09-sensorml-testing-requirements.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/testing/research-plans/09-sensorml-testing-requirements.md)                         | SensorML 3.0 format parsing test requirements                  |
| 188 | [10-swe-common-testing-requirements.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/testing/research-plans/10-swe-common-testing-requirements.md)                     | SWE Common 3.0 format parsing test requirements                |
| 189 | [11-geojson-csapi-testing-requirements.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/testing/research-plans/11-geojson-csapi-testing-requirements.md)               | GeoJSON CSAPI extensions test requirements                     |
| 190 | [12-querybuilder-testing-strategy.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/testing/research-plans/12-querybuilder-testing-strategy.md)                         | URL construction testing for ~70-80 methods across 9 types     |
| 191 | [13-resource-method-testing-patterns.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/testing/research-plans/13-resource-method-testing-patterns.md)                   | CRUD testing patterns for 9 CSAPI resource types               |
| 192 | [14-integration-test-workflow-design.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/testing/research-plans/14-integration-test-workflow-design.md)                   | Integration test workflows (26 scenarios)                      |
| 193 | [15-fixture-sourcing-organization.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/testing/research-plans/15-fixture-sourcing-organization.md)                         | Sourcing and organizing ~280 test fixtures                     |
| 194 | [16-worker-extensions-testing.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/testing/research-plans/16-worker-extensions-testing.md)                                 | Worker testing strategy (out of scope — reference only)        |
| 195 | [17-coverage-targets-metrics.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/testing/research-plans/17-coverage-targets-metrics.md)                                   | Code coverage targets and metrics thresholds                   |
| 196 | [18-error-condition-testing.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/testing/research-plans/18-error-condition-testing.md)                                     | Error conditions and edge cases strategy                       |
| 197 | [19-test-organization-file-structure.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/testing/research-plans/19-test-organization-file-structure.md)                   | Test file organization and directory structure conventions     |
| 198 | [20-test-to-code-ratio-validation.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/testing/research-plans/20-test-to-code-ratio-validation.md)                         | Test-to-code ratio validation (outline only)                   |
| 199 | [21-typescript-type-testing.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/testing/research-plans/21-typescript-type-testing.md)                                     | TypeScript type definition testing strategy                    |
| 200 | [22-conformance-capability-testing.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/testing/research-plans/22-conformance-capability-testing.md)                       | Conformance classes and capability detection testing           |
| 201 | [23-pagination-testing.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/testing/research-plans/23-pagination-testing.md)                                               | Pagination testing across CSAPI resources (53 scenarios)       |
| 202 | [24-query-parameter-combination-testing.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/testing/research-plans/24-query-parameter-combination-testing.md)             | Query parameter combinations (120 scenarios)                   |
| 203 | [25-format-negotiation-testing.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/testing/research-plans/25-format-negotiation-testing.md)                               | Content type and format negotiation testing                    |
| 204 | [26-subresource-navigation-testing.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/testing/research-plans/26-subresource-navigation-testing.md)                       | Sub-resource navigation and link traversal (16 relationships)  |
| 205 | [27-schema-driven-validation-testing.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/testing/research-plans/27-schema-driven-validation-testing.md)                   | Schema-driven response validation (66 tests)                   |
| 206 | [28-temporal-query-testing.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/testing/research-plans/28-temporal-query-testing.md)                                       | Temporal query testing (outline only)                          |
| 207 | [29-spatial-query-testing.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/testing/research-plans/29-spatial-query-testing.md)                                         | Spatial/bbox query parameters (43 tests)                       |
| 208 | [30-bulk-operations-testing.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/testing/research-plans/30-bulk-operations-testing.md)                                     | Bulk/batch operations (28 tests)                               |
| 209 | [31-command-lifecycle-testing.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/testing/research-plans/31-command-lifecycle-testing.md)                                 | Command send/status/result lifecycle (42 tests)                |
| 210 | [32-real-world-server-compatibility-testing.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/testing/research-plans/32-real-world-server-compatibility-testing.md)     | Real-world server compatibility (~65% flagged as anti-pattern) |
| 211 | [33-performance-efficiency-testing.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/testing/research-plans/33-performance-efficiency-testing.md)                       | Performance testing (out of scope with rationale)              |
| 212 | [34-test-utility-helper-design.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/testing/research-plans/34-test-utility-helper-design.md)                               | Shared test utility functions (~50 helpers)                    |
| 213 | [35-jsdoc-testing-documentation-standards.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/testing/research-plans/35-jsdoc-testing-documentation-standards.md)         | JSDoc documentation standards for test files                   |
| 214 | [36-test-quality-checklist-review-process.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/testing/research-plans/36-test-quality-checklist-review-process.md)         | Quality checklist and review process                           |
| 215 | [37-test-maintenance-evolution-strategy.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/testing/research-plans/37-test-maintenance-evolution-strategy.md)             | Long-term maintenance and evolution strategy                   |
| 216 | [38-testing-playbook-synthesis.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/testing/research-plans/38-testing-playbook-synthesis.md)                               | Final synthesis consolidating all 37 prior research plans      |

### Findings (findings/)

| #   | File                                                                                                                                                                                           | Description                                                                |
| --- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------- |
| 217 | [01-edr-test-blueprint.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/testing/findings/01-edr-test-blueprint.md)                                                   | PR #114 test patterns, coverage, assertions, fixtures extracted            |
| 218 | [02-upstream-test-consistency.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/testing/findings/02-upstream-test-consistency.md)                                     | Consistency matrix across all 6 existing OGC implementations               |
| 219 | [03-typescript-testing-standards.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/testing/findings/03-typescript-testing-standards.md)                               | TypeScript testing best practices for coverage, mocking, type testing      |
| 220 | [04-implementation-guide-testing-requirements.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/testing/findings/04-implementation-guide-testing-requirements.md)     | Test structure, coverage targets, format parser requirements extracted     |
| 221 | [05-roadmap-testing-integration.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/testing/findings/05-roadmap-testing-integration.md)                                 | Incremental testing workflow, checkpoints, test debt prevention            |
| 222 | [06-meaningful-vs-trivial-definition.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/testing/findings/06-meaningful-vs-trivial-definition.md)                       | Quality guide with assertion depth criteria and side-by-side comparisons   |
| 223 | [07-end-to-end-testing-scope.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/testing/findings/07-end-to-end-testing-scope.md)                                       | E2E scope: Discovery, Observation, Command workflows with effort estimates |
| 224 | [08-csapi-specification-test-requirements.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/testing/findings/08-csapi-specification-test-requirements.md)             | Resource types, endpoints, query parameters, conformance classes cataloged |
| 225 | [09-sensorml-testing-requirements.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/testing/findings/09-sensorml-testing-requirements.md)                             | SensorML parser testing reclassified from validator to parser focus        |
| 226 | [10-swe-common-testing-requirements.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/testing/findings/10-swe-common-testing-requirements.md)                         | SWE Common parser testing with binary encoding content                     |
| 227 | [11-geojson-csapi-testing-requirements.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/testing/findings/11-geojson-csapi-testing-requirements.md)                   | GeoJSON property extraction, type ID, validTime, association links         |
| 228 | [12-querybuilder-testing-strategy.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/testing/findings/12-querybuilder-testing-strategy.md)                             | URL construction testing with validation depth analysis                    |
| 229 | [13-resource-method-testing-patterns.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/testing/findings/13-resource-method-testing-patterns.md)                       | Universal describe block templates and shared utilities                    |
| 230 | [14-integration-test-workflow-design.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/testing/findings/14-integration-test-workflow-design.md)                       | Multi-step Discovery, Observation, Command, Cross-resource workflows       |
| 231 | [15-fixture-sourcing-organization.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/testing/findings/15-fixture-sourcing-organization.md)                             | Directory hierarchies, naming conventions, provenance docs                 |
| 232 | [15-part-2-fixture-documentation-best-practices.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/testing/findings/15-part-2-fixture-documentation-best-practices.md) | Industry best practices validating the fixture metadata system             |
| 233 | [16-worker-extensions-testing.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/testing/findings/16-worker-extensions-testing.md)                                     | Worker testing OFF; no JSON API in ogc-client uses workers                 |
| 234 | [17-coverage-targets-and-metrics.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/testing/findings/17-coverage-targets-and-metrics.md)                               | Component-specific thresholds and Jest configuration                       |
| 235 | [18-error-condition-testing-strategy.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/testing/findings/18-error-condition-testing-strategy.md)                       | Client-side errors, binary parsing edges, network failures                 |
| 236 | [19-test-organization-file-structure.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/testing/findings/19-test-organization-file-structure.md)                       | File naming, describe/it structure, utilities, fixture layout              |
| 237 | [20-test-to-code-ratio-validation.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/testing/findings/20-test-to-code-ratio-validation.md)                             | Ratios validated against upstream EDR/WFS/WMS/WMTS/STAC                    |
| 238 | [21-typescript-type-testing-strategy.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/testing/findings/21-typescript-type-testing-strategy.md)                       | Compiler-only validation with type inventory                               |
| 239 | [22-conformance-capability-testing.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/testing/findings/22-conformance-capability-testing.md)                           | Conformance class detection, hasConnectedSystems, graceful degradation     |
| 240 | [23-pagination-testing.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/testing/findings/23-pagination-testing.md)                                                   | URL construction with cursor/offset and link parsing                       |
| 241 | [24-query-parameter-combination-testing.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/testing/findings/24-query-parameter-combination-testing.md)                 | ~60 scenarios with server validation tests flagged for removal             |
| 242 | [25-format-negotiation-testing.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/testing/findings/25-format-negotiation-testing.md)                                   | `f=` parameter, format constants, client pre-validation                    |
| 243 | [26-subresource-navigation-testing.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/testing/findings/26-subresource-navigation-testing.md)                           | 16 parent-child relationships, bidirectional navigation                    |
| 244 | [27-schema-driven-validation-testing.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/testing/findings/27-schema-driven-validation-testing.md)                       | Observation/command validation; server tests flagged for review            |
| 245 | [28-temporal-query-testing.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/testing/findings/28-temporal-query-testing.md)                                           | ISO 8601, timezone handling, parseInstant/parseInterval/parseDuration      |
| 246 | [29-spatial-query-testing.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/testing/findings/29-spatial-query-testing.md)                                             | bbox encoding, coordinate validation, antimeridian handling                |
| 247 | [30-bulk-operations-testing.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/testing/findings/30-bulk-operations-testing.md)                                         | Auto-chunking, fallback-to-sequential, BulkCreateResult, progress          |
| 248 | [31-command-lifecycle-testing.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/testing/findings/31-command-lifecycle-testing.md)                                     | Lifecycle states, transition rules, sync vs async, polling                 |
| 249 | [32-real-world-server-compatibility-testing.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/testing/findings/32-real-world-server-compatibility-testing.md)         | ~65% flagged as anti-pattern; conformance detection sections usable        |
| 250 | [33-performance-efficiency-testing.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/testing/findings/33-performance-efficiency-testing.md)                           | Parser benchmarks, large datasets, memory, regressions                     |
| 251 | [34-test-utility-helper-design.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/testing/findings/34-test-utility-helper-design.md)                                   | URL validation, fixture loading, assertion/mocking/setup helpers           |
| 252 | [35-jsdoc-testing-documentation-standards.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/testing/findings/35-jsdoc-testing-documentation-standards.md)             | Test intent, fixture provenance, coverage gaps, upstream patterns          |
| 253 | [36-test-quality-checklist-review-process.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/testing/findings/36-test-quality-checklist-review-process.md)             | Meaningful, useful, deep test validation with sign-off workflow            |
| 254 | [37-test-maintenance-evolution-strategy.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/testing/findings/37-test-maintenance-evolution-strategy.md)                 | Spec updates, upstream changes, test rot prevention                        |
| 255 | [38-testing-playbook-synthesis.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/testing/findings/38-testing-playbook-synthesis.md)                                   | Comprehensive playbook: workflows, patterns, progress tracking             |

### Reviews (review/)

| #   | File                                                                                                                                                                                       | Description                                                                |
| --- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------- |
| 256 | [notes-parser-testing-vs-spec-validation.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/testing/review/notes-parser-testing-vs-spec-validation.md)             | Parser tests verify client extraction, not server compliance               |
| 257 | [notes-why-models-default-to-server-validation.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/testing/review/notes-why-models-default-to-server-validation.md) | Why AI models produce server-oriented tests instead of client parser tests |
| 258 | [phase-0-lessons-from-failed-attempt.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/testing/review/phase-0-lessons-from-failed-attempt.md)                     | Anti-patterns from prior failed testing attempt (review lens)              |
| 259 | [phase-1-foundation-validation.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/testing/review/phase-1-foundation-validation.md)                                 | Foundation research plans (Sections 1-7) reviewed, 5 quality layers        |
| 260 | [phase-2a-fixtures-category.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/testing/review/phase-2a-fixtures-category.md)                                       | Fixture sourcing and organization deep dive                                |
| 261 | [phase-2b-testing-patterns-category.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/testing/review/phase-2b-testing-patterns-category.md)                       | Testing patterns category review (5 documents)                             |
| 262 | [phase-2c-standards-quality-category.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/testing/review/phase-2c-standards-quality-category.md)                     | Standards and quality category review (6 documents)                        |
| 263 | [phase-2d-csapi-specific-testing-category.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/testing/review/phase-2d-csapi-specific-testing-category.md)           | CSAPI-specific testing requirements review (6 documents)                   |
| 264 | [phase-2e-advanced-scenarios-category.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/testing/review/phase-2e-advanced-scenarios-category.md)                   | Advanced testing scenarios review (12 documents)                           |
| 265 | [phase-2f-integration-workflow-category.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/testing/review/phase-2f-integration-workflow-category.md)               | Integration and workflow review (4 documents)                              |
| 266 | [phase-3-synthesis-validation.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/testing/review/phase-3-synthesis-validation.md)                                   | Testing playbook synthesis review (Doc 38, 3,410 lines)                    |
| 267 | [phase-4-cross-cutting-review.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/testing/review/phase-4-cross-cutting-review.md)                                   | Meta-review: corpus-wide consistency across 38 findings + 12 reviews       |
| 268 | [verified-conformance-uris.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/testing/review/verified-conformance-uris.md)                                         | Authoritative CSAPI conformance class URIs from OGC published standards    |

### Archive

| #   | File                                                                                                                                                      | Description                               |
| --- | --------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------- |
| 269 | [testing-strategy-research-v1.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/testing/archive/testing-strategy-research-v1.md) | Testing strategy research v1 (superseded) |

---

## docs/research/pre-implementation-alignment/ (3 plans + 5 findings + 5 prompts)

### Research Plans

| #   | File                                                                                                                                                                                                                                               | Description                                                   |
| --- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------- |
| 270 | [A1-research-plan-test-research-vs-implementation-guide.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/pre-implementation-alignment/A1-research-plan-test-research-vs-implementation-guide.md)                         | Bidirectional alignment: Test Research ↔ Implementation Guide |
| 271 | [A2-research-plan-roadmap-vs-implementation-guide-and-test-research.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/pre-implementation-alignment/A2-research-plan-roadmap-vs-implementation-guide-and-test-research.md) | ROADMAP ↔ Implementation Guide + Test Research alignment      |
| 272 | [A3-research-plan-contribution-goal-vs-implementation-guide.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/pre-implementation-alignment/A3-research-plan-contribution-goal-vs-implementation-guide.md)                 | Contribution Goal ↔ Implementation Guide alignment            |

### Findings

| #   | File                                                                                                                                                                                                                                          | Description                                                      |
| --- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------- |
| 273 | [A1-pass-1-forward-checks.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/pre-implementation-alignment/findings/A1-pass-1-forward-checks.md)                                                                       | Implementation Guide → Test Research forward alignment findings  |
| 274 | [A1-pass-2-reverse-checks.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/pre-implementation-alignment/findings/A1-pass-2-reverse-checks.md)                                                                       | Test Research → Implementation Guide reverse alignment findings  |
| 275 | [A1-test-research-vs-implementation-guide-report.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/pre-implementation-alignment/findings/A1-test-research-vs-implementation-guide-report.md)                         | Final bidirectional alignment report                             |
| 276 | [A2-roadmap-vs-implementation-guide-and-test-research-report.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/pre-implementation-alignment/findings/A2-roadmap-vs-implementation-guide-and-test-research-report.md) | ROADMAP v3.0 vs Implementation Guide + test research (12 checks) |
| 277 | [A3-contribution-goal-vs-implementation-guide-report.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/pre-implementation-alignment/findings/A3-contribution-goal-vs-implementation-guide-report.md)                 | Contribution Goal v1.0 vs Implementation Guide v7.0 (8 checks)   |

### Prompts

| #   | File                                                                                                                                                             | Description                                    |
| --- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------- |
| 278 | [A1-execution-prompt.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/pre-implementation-alignment/prompts/A1-execution-prompt.md)     | 3-pass execution prompt for A1 research plan   |
| 279 | [A2-execution-prompt.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/pre-implementation-alignment/prompts/A2-execution-prompt.md)     | Single execution prompt for A2 alignment       |
| 280 | [A2-execution-prompt-1.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/pre-implementation-alignment/prompts/A2-execution-prompt-1.md) | A2 prompt 1/2: structural alignment checks 1–7 |
| 281 | [A2-execution-prompt-2.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/pre-implementation-alignment/prompts/A2-execution-prompt-2.md) | A2 prompt 2/2: qualitative/audit checks 8–12   |
| 282 | [A3-execution-prompt.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/pre-implementation-alignment/prompts/A3-execution-prompt.md)     | Execution prompt for A3 alignment              |

---

## docs/research/phase-5/ (2 files — this phase)

| #   | File                                                                                                                                    | Description                                                              |
| --- | --------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------ |
| 283 | [parsing-coverage-audit.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/phase-5/parsing-coverage-audit.md)   | Full inventory of model interfaces vs parse functions, identifies 9 gaps |
| 284 | [documentation-inventory.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/research/phase-5/documentation-inventory.md) | This file — flat catalog of all 306 documents in docs/                   |

---

## docs/testing/ (1 guide + 19 demo-app findings)

| #   | File                                                                                                         | Description                                                |
| --- | ------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------- |
| 285 | [fixtures-guide.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/testing/fixtures-guide.md) | Guide to test data fixtures following upstream methodology |

### Demo App Findings (testing/demo-app-findings/)

| #   | File                                                                                                                                                                                                 | Description                                                         |
| --- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------- |
| 286 | [issue-5-nested-create-methods.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/testing/demo-app-findings/issue-5-nested-create-methods.md)                                         | `createDataStream()` URL bugs and missing nested create methods     |
| 287 | [issue-6-content-type-helper.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/testing/demo-app-findings/issue-6-content-type-helper.md)                                             | `CSAPI_CONTENT_TYPES` helper map for content negotiation            |
| 288 | [issue-7-unit-tests.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/testing/demo-app-findings/issue-7-unit-tests.md)                                                               | Unit tests for nested create methods and Content-Type map           |
| 289 | [issue-8-jsdoc-documentation.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/testing/demo-app-findings/issue-8-jsdoc-documentation.md)                                             | JSDoc for `extractCSAPIFeature()` limitations                       |
| 290 | [issue-9-accept-header-default.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/testing/demo-app-findings/issue-9-accept-header-default.md)                                         | Default to `Accept: application/geo+json` for Part 1                |
| 291 | [issue-10-endpoint-root-error-type.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/testing/demo-app-findings/issue-10-endpoint-root-error-type.md)                                 | endpoint.ts root getter should throw `EndpointError` not `Error`    |
| 292 | [issue-11-generic-crud-methods.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/testing/demo-app-findings/issue-11-generic-crud-methods.md)                                         | Generic CRUD methods for dynamic-type consumers                     |
| 293 | [issue-12-constructor-parameter-narrowing.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/testing/demo-app-findings/issue-12-constructor-parameter-narrowing.md)                   | Narrow `CSAPIQueryBuilder` constructor to required fields only      |
| 294 | [issue-13-type-guard-functions-for-union-narrowing.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/testing/demo-app-findings/issue-13-type-guard-functions-for-union-narrowing.md) | Type guards for `extractCSAPIFeature()` union narrowing             |
| 295 | [issue-14-resource-discovery-non-standard-links.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/testing/demo-app-findings/issue-14-resource-discovery-non-standard-links.md)       | Handle servers with non-standard link structures                    |
| 296 | [issue-15-parse-location-header.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/testing/demo-app-findings/issue-15-parse-location-header.md)                                       | `parseLocationHeader()` utility for 201 responses                   |
| 297 | [issue-16-schema-jsdoc-parameter-confusion.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/testing/demo-app-findings/issue-16-schema-jsdoc-parameter-confusion.md)                 | Schema method JSDoc `f` vs `obsFormat`/`cmdFormat` naming           |
| 298 | [issue-17-schema-response-parser.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/testing/demo-app-findings/issue-17-schema-response-parser.md)                                     | Schema response parser utility for datastream/controlstream schemas |
| 299 | [issue-18-empty-body-201-response.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/testing/demo-app-findings/issue-18-empty-body-201-response.md)                                   | Handle empty-body 201 Created without crashing                      |
| 300 | [issue-19-uid-requirement-in-put-payloads.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/testing/demo-app-findings/issue-19-uid-requirement-in-put-payloads.md)                   | Document/enforce uid requirement in PUT updates                     |
| 301 | [issue-20-controlstream-url-path-casing.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/testing/demo-app-findings/issue-20-controlstream-url-path-casing.md)                       | Fix `buildResourceUrl()` lowercase fallback for controlStreams      |
| 302 | [issue-21-mapview-manual-url-construction.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/testing/demo-app-findings/issue-21-mapview-manual-url-construction.md)                   | Replace manual URL construction with CSAPIQueryBuilder              |
| 303 | [issue-22-relationship-based-filter-systemid.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/testing/demo-app-findings/issue-22-relationship-based-filter-systemid.md)             | systemId dropdown filter on Datastreams list                        |
| 304 | [issue-26-procedure-sensorml-jsdoc-crossrefs.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/testing/demo-app-findings/issue-26-procedure-sensorml-jsdoc-crossrefs.md)             | JSDoc cross-references between Procedure and SensorML types         |

---

## docs/webapp-demo/ (2 files)

| #   | File                                                                                                                       | Description                                                        |
| --- | -------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------ |
| 305 | [demo-app-assessment.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/webapp-demo/demo-app-assessment.md) | Assessment of the CSAPI demo webapp, identifying "HTTP Client" gap |
| 306 | [session-handoff.md](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/blob/main/docs/webapp-demo/session-handoff.md)         | Session handoff for continuing demo app work in a new workspace    |

---

## Summary by Category

| Category                                                         | Count   |
| ---------------------------------------------------------------- | ------- |
| Governance (templates, constraints, lessons)                     | 12      |
| Planning (active)                                                | 3       |
| Planning (archive)                                               | 17      |
| Implementation (overviews, reviews, smoke tests, notes)          | 61      |
| Research — Requirements                                          | 23      |
| Research — Upstream patterns                                     | 12      |
| Research — Design (component blueprints, architecture decisions) | 47      |
| Research — Testing (strategy, plans, findings, reviews)          | 90      |
| Research — Pre-implementation alignment                          | 13      |
| Research — Phase 5 (current)                                     | 2       |
| Research — Other (references, strategy)                          | 2       |
| Testing (fixtures guide + demo app findings)                     | 20      |
| Webapp demo                                                      | 2       |
| **Total**                                                        | **306** |
