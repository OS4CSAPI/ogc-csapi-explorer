# Section 37: Test Maintenance and Evolution Strategy

**Research Plan:** [Research Plan 37: Test Maintenance and Evolution Strategy](../research-plans/37-test-maintenance-evolution-strategy.md)

**Research Questions:** 6 core questions about keeping tests in sync with spec updates, handling upstream library changes, refactoring tests with implementation changes, test update triggers, preventing test rot, and documenting maintenance responsibilities.

**Methodology:** 6-phase systematic analysis (Phase 1: Maintenance Challenge Analysis → Phase 2: Change Detection Strategy → Phase 3: Update Process Design → Phase 4: Responsibility Assignment → Phase 5: Prevention Strategy → Phase 6: Synthesis)

**Research Time:** 50 minutes – February 6, 2026

**Primary Source(s):**

- [Lessons Learned Analysis](../../requirements/lessons-learned-analysis.md)
- Section 15 deliverable: Fixture maintenance strategy
- [Implementation Guide](../../../planning/csapi-implementation-guide.md)
- [ROADMAP](../../../planning/ROADMAP.md)

**Supporting Resources:**

- Section 35: [JSDoc Testing Documentation Standards](35-jsdoc-testing-documentation-standards.md) (maintenance documentation)
- Section 36: [Test Quality Checklist and Review Process](36-test-quality-checklist-review-process.md) (quality maintenance)
- Section 15: [Fixture Sourcing and Organization](15-fixture-sourcing-organization.md) (fixture maintenance)

**Document Purpose:** Comprehensive maintenance strategy for keeping CSAPI tests valuable, current, and maintainable as the specification evolves, upstream library changes, and implementation refactors, addressing test maintenance burden identified in lessons learned.

---

## Executive Summary

This document defines a strategy for maintaining and evolving CSAPI tests as the specification updates, upstream library changes, and implementation refactors. Based on lessons learned from the previous iteration (where test maintenance was identified as a problem), this strategy ensures tests remain valuable, current, and maintainable long-term.

> **⚠️ Review Notice (C2 fix):** The `@specification` JSDoc tag traceability system and associated tooling (`scripts/test-traceability.js`, `test:update-spec-version`) originally proposed in this document have been identified as AP3 (OGC Requirement Traceability) during Phase 2C review and removed. Structural spec-traceability infrastructure organizes tests around spec sections rather than client code behavior. The upstream codebase has zero spec-traceability infrastructure. **Sections referencing `@specification` tags have been updated to use plain `// Spec context:` comments.** Remaining instances in embedded code examples should be read as plain comments.

> **⚠️ Review Notice (H3 fix):** The original document proposed enterprise-level maintenance infrastructure disproportionate to an open-source library contribution: a RACI matrix with 5 invented roles (Test Owner, Component Maintainer, Release Manager, Tech Lead, Documentation Maintainer), monthly health checks (2–4 hours/month), 70–120 hours/year maintenance burden, custom tooling (detect-test-rot.js, validate-fixtures.js, health-report generator, fixture migration tool), GitHub Actions workflows for monthly automated health checks, Dependabot/Renovate configuration, a 9-step spec update workflow with 2–4 week timeline, and elaborate markdown templates. The contributor does not control upstream CI configuration, does not set dependency management policies, and should not propose organizational roles or 70–120 hours/year of overhead for a contribution to someone else's repository. Upstream `camptocamp/ogc-client` maintains its tests with zero documented maintenance process. These sections have been simplified to brief, practical guidelines.

### Key Maintenance Challenges

**From Lessons Learned:**

> "Test maintenance burden" - Previous iteration had unclear ownership and update processes

**Four Primary Challenge Categories:**

1. **Spec Evolution** - CSAPI specification updates with new features, changed requirements
2. **Dependency Changes** - Upstream library API changes, breaking changes
3. **Implementation Refactoring** - Code changes that invalidate test assumptions
4. **Test Rot** - Tests become outdated, trivial, or meaningless over time

### Maintenance Guidelines

**Three core practices for CSAPI test maintenance:**

1. **Update fixtures when upstream API changes** — When upstream `camptocamp/ogc-client` releases breaking changes, update test fixtures and assertions to match the new API.

2. **Keep test patterns aligned with upstream conventions** — Follow upstream's testing style. If upstream changes how it structures tests, align contributed tests accordingly.

3. **Fix broken tests promptly** — When tests fail (due to spec changes, dependency updates, or refactoring), fix them immediately rather than skipping or disabling.

### Spec-Informed Test Maintenance

> **⚠️ AP3 Warning:** The `@specification` JSDoc tag traceability system originally proposed here has been identified as anti-pattern AP3 (OGC Requirement Traceability). Structural spec-traceability infrastructure organizes tests around spec sections rather than client code behavior. The upstream codebase has zero spec-traceability infrastructure.

**Approach:** Use plain comments to note which spec sections informed test design

```typescript
// Spec context: OGC 23-001 §7.2.1, Table 4 defines required system properties
it('parses required system properties from response', () => {
  const result = parseSystem(fixture);
  expect(result.id).toBeDefined();
  expect(result.name).toBeDefined();
});
```

**When specs update:** Review tests whose comments reference changed sections. The spec is INPUT — it tells us what correct client behavior looks like. We test that our client code handles responses correctly, not that responses are spec-compliant.

### Maintenance Triggers

| Trigger                   | Frequency                         | Response Time  | Priority |
| ------------------------- | --------------------------------- | -------------- | -------- |
| **Spec Update**           | Per spec release (~yearly)        | Within 2 weeks | HIGH     |
| **Dependency Update**     | Per upstream release (~quarterly) | Within 1 week  | MEDIUM   |
| **Implementation Change** | Per refactoring (ad-hoc)          | Immediate      | HIGH     |
| **Test Failure**          | When detected (continuous)        | Immediate      | CRITICAL |

---

## 1. Maintenance Scenario Analysis

### 1.1 Spec Evolution Scenarios

**Scenario 1: New Feature Added to Spec**

**Example:** CSAPI v1.1.0 adds new resource type "Procedures"

**Impact:**

- **QueryBuilder:** Add getProcedures(), getProcedure(), etc. (new methods)
- **Tests:** Add new test file procedures.spec.ts (~400-600 lines)
- **Fixtures:** Create procedure fixtures (~10-15 files)
- **Documentation:** Update README with procedure examples

**Effort:** 8-12 hours

**Workflow:**

1. Review spec changes (identify new Procedures resource)
2. Implement QueryBuilder methods (8-10 new methods)
3. Write tests (40-50 tests)
4. Create fixtures (from spec examples)
5. Update documentation
6. Review and merge

**Scenario 2: Spec Requirement Changed**

**Example:** CSAPI v1.1.0 changes System.properties schema (new required field "status")

**Impact:**

- **QueryBuilder:** No changes (URL building unaffected)
- **Tests:** Update assertions to check "status" field
- **Fixtures:** Add "status" field to all system fixtures (~20 fixtures)
- **Documentation:** Update system property table

**Effort:** 3-5 hours

**Workflow:**

1. Review spec changes (identify schema change)
2. Update fixtures (add "status" field)
3. Validate fixtures (schema validation)
4. Update test assertions
5. Update documentation
6. Review and merge

**Scenario 3: Spec Feature Deprecated**

**Example:** CSAPI v2.0.0 deprecates SamplingFeature.sampledFeature field

**Impact:**

- **QueryBuilder:** Mark field as deprecated in comments
- **Tests:** Add deprecation warning tests
- **Fixtures:** Keep existing but mark as deprecated
- **Documentation:** Add deprecation notice

**Effort:** 1-2 hours

**Workflow:**

1. Review spec deprecation notice
2. Add @deprecated JSDoc tags
3. Update tests to expect deprecation warnings (if applicable)
4. Update documentation
5. Plan removal for v3.0.0
6. Review and merge

**Scenario 4: Spec Feature Removed**

**Example:** CSAPI v3.0.0 removes deprecated SamplingFeature.sampledFeature field

**Impact:**

- **QueryBuilder:** Remove deprecated field support
- **Tests:** Remove or update tests for removed field
- **Fixtures:** Remove field from all fixtures
- **Documentation:** Remove from docs

**Effort:** 2-4 hours

**Workflow:**

1. Review spec removal notice
2. Remove field from QueryBuilder (if supported)
3. Remove or update tests
4. Update fixtures
5. Update documentation
6. Review and merge

**Scenario 5: Spec Conformance Class Added**

**Example:** CSAPI v1.2.0 adds new conformance class "Advanced Filtering"

**Impact:**

- **QueryBuilder:** Add advanced filter methods
- **Tests:** Add conformance class detection tests
- **Tests:** Add advanced filtering tests (~200-400 lines)
- **Fixtures:** Create advanced filtering fixtures
- **Documentation:** Document new conformance class

**Effort:** 10-16 hours

**Workflow:**

1. Review conformance class spec
2. Implement conformance detection
3. Implement advanced filter methods
4. Write tests
5. Create fixtures
6. Update documentation
7. Review and merge

### 1.2 Upstream Library Change Scenarios

**Scenario 1: Non-Breaking Dependency Update**

**Example:** ogc-client v4.2.0 → v4.3.0 (minor version, no breaking changes)

**Impact:**

- **Code:** None (compatible update)
- **Tests:** None (still pass)
- **Fixtures:** None
- **Documentation:** Update dependency version in README

**Effort:** 0.5-1 hour

**Workflow:**

1. Review upstream release notes
2. Update package.json version
3. Run npm update
4. Run full test suite (validate no breaks)
5. Update documentation
6. Review and merge

**Scenario 2: Breaking API Change in Dependency**

**Example:** ogc-client v5.0.0 renames `OgcApiEndpoint.getFeatures()` → `OgcApiEndpoint.fetchFeatures()`

**Impact:**

- **Code:** Update all calls to getFeatures() → fetchFeatures()
- **Tests:** Update test assertions and mocks
- **Fixtures:** None (API change, not data format)
- **Documentation:** Update examples

**Effort:** 4-8 hours

**Workflow:**

1. Review upstream breaking changes
2. Update package.json to v5.0.0
3. Find all getFeatures() calls (grep search)
4. Update to fetchFeatures()
5. Run tests, fix failures
6. Update documentation
7. Review and merge

**Scenario 3: Deprecated API in Dependency**

**Example:** ogc-client v4.5.0 deprecates `endpoint.getUrl()` (use `endpoint.url` property)

**Impact:**

- **Code:** Update to new API (proactive or wait for removal)
- **Tests:** Update test code
- **Fixtures:** None
- **Documentation:** None (internal change)

**Effort:** 2-4 hours

**Workflow:**

1. Review deprecation notice
2. Decide: migrate now or wait for removal
3. If migrating: find all getUrl() calls, replace with .url
4. Run tests
5. Review and merge

**Scenario 4: New Feature in Dependency**

**Example:** ogc-client v4.4.0 adds `endpoint.validateConformance()` method

**Impact:**

- **Code:** Optionally use new feature
- **Tests:** Add tests for new feature usage (if adopted)
- **Fixtures:** None
- **Documentation:** Update examples (if relevant)

**Effort:** 2-6 hours (if adopted), 0 hours (if not used)

**Workflow:**

1. Review new feature documentation
2. Decide: adopt feature or ignore
3. If adopting: implement usage
4. Write tests
5. Update documentation
6. Review and merge

### 1.3 Implementation Refactoring Scenarios

**Scenario 1: Internal Refactoring (No API Change)**

**Example:** Refactor CSAPIQueryBuilder internal URL building to use helper functions

**Impact:**

- **Code:** Refactored internals
- **Tests:** None (tests only validate public API)
- **Fixtures:** None
- **Documentation:** None

**Effort:** 0 hours (tests should still pass)

**Validation:**

- Run full test suite
- All tests should pass without changes
- If tests fail → tests were testing implementation, not behavior (fix tests)

**Scenario 2: Public API Refactoring (Breaking Change)**

**Example:** Rename `builder.getSystems()` → `builder.systems().list()` (better structure)

**Impact:**

- **Code:** Renamed methods
- **Tests:** Update all test calls
- **Fixtures:** None
- **Documentation:** Update all examples

**Effort:** 8-12 hours

**Workflow:**

1. Implement new API structure
2. Deprecate old API (keep compatibility temporarily)
3. Update all internal uses
4. Update all tests
5. Update documentation
6. Review and merge
7. Remove deprecated API in future version

**Scenario 3: Test Utility Refactoring**

**Example:** Refactor `parseAndValidateUrl()` to accept options differently

**Impact:**

- **Code:** Test utility changed
- **Tests:** Update all calls to parseAndValidateUrl() (~100+ locations)
- **Fixtures:** None
- **Documentation:** Update test utility docs

**Effort:** 4-6 hours

**Workflow:**

1. Update parseAndValidateUrl() signature
2. Find all calls (grep search)
3. Update each call with new syntax
4. Run tests, verify all pass
5. Update JSDoc documentation
6. Review and merge

**Scenario 4: Fixture Schema Update**

> **⚠️ Review Notice (M4 fix — Phase 2C):** This scenario originally proposed adding `_metadata` fields (createdDate, modifiedDate, sourceURL) to all ~280+ fixtures at 6-10 hours effort. That has been removed — fixtures are static test data files and should not carry embedded metadata (AP2 risk). This scenario now covers the realistic case of updating fixture schemas when the spec changes.

**Example:** Spec v1.2 adds new required fields to System resources

**Impact:**

- **Code:** Update type definitions
- **Tests:** Update assertions for new fields
- **Fixtures:** Update affected fixtures (resource-type scoped, not all)
- **Documentation:** Update README spec version

**Effort:** 1-4 hours (depends on scope of schema change)

**Workflow:**

1. Identify affected resource types from spec changelog
2. Update fixtures for affected resource types
3. Update type definitions and tests
4. Validate fixtures against updated schemas
5. Update README spec version
6. Review and merge

### 1.4 Test Rot Scenarios

**Scenario 1: Test Becomes Too Trivial**

**Example:** Test only checks `expect(url).toBeTruthy()` without validating structure

**Detection:**

- Quality checklist review finds trivial test
- Test passes even when code is broken

**Remediation:**

1. Identify trivial tests (manual review or automated analysis)
2. Enhance test with proper validation (use parseAndValidateUrl())
3. Validate bug detection (intentionally break code, test should fail)
4. Update test quality checklist

**Effort:** 0.5-1 hour per test

**Scenario 2: Test Tests Mocks Instead of Behavior**

**Example:** Test mocks entire API, validates mock returns expected data

**Detection:**

- Test always passes regardless of implementation
- Mock setup more complex than actual code

**Remediation:**

1. Identify over-mocked tests
2. Replace with integration tests using real fixtures
3. Validate tests catch real bugs
4. Update test patterns

**Effort:** 1-2 hours per test

**Scenario 3: Fixture Becomes Outdated**

**Example:** Fixture from CSAPI v1.0 spec, now v1.2 with schema changes

**Detection:**

- Fixture fails schema validation
- Fixture missing new required fields
- Fixture uses deprecated fields

**Remediation:**

1. Run fixture validation against current schema
2. Update fixtures to match current spec
3. Update README spec version
4. Re-validate fixtures

**Effort:** 0.5-1 hour per fixture

**Scenario 4: Test Documentation Drifts**

**Example:** Spec context comment references old spec version, test actually validates v1.2 behavior

**Detection:**

- Code review finds version mismatch in comments
- Spec section reference is outdated

**Remediation:**

1. Review spec context comments in affected test files
2. Update comments to reference current spec version
3. Verify test still validates correct client behavior
4. Update test implementation if expected behavior changed

**Effort:** 0.25-0.5 hour per test

---

## 2. Change Detection Strategy

### 2.1 Spec Version Tracking

> **⚠️ Review Notice (M4 fix — Phase 2C):** This section originally proposed tracking spec versions in 4 locations: package.json `csapi` key, test file headers, fixture `_metadata` fields, and README. The package.json `csapi` key and fixture `_metadata` system have been removed — they introduced AP2 (Hybrid Fixture/Live) risk by embedding mutable metadata into static fixture files, and adding metadata to ~280+ fixtures would be high-effort with no testing value. Test file headers were already addressed by H4/C2 (no @specification tags). README documentation is the appropriate place for spec version tracking.

**Approach:** Track spec version in README documentation for human reference

**README Documentation**

```markdown
## Specification Compliance

This implementation supports:

- **OGC 23-001** Connected Systems API - Part 1: Feature Resources (v1.0.0)
- **OGC 23-002** Connected Systems API - Part 2: Observation Data (v1.0.0)
- **OGC 23-003** Connected Systems API - Part 3: Command & Control (v1.0.0)

**Last Updated:** 2024-02-05
```

### 2.2 Dependency Version Tracking

**Approach:** Use standard npm dependency management + automated checks

**1. Package.json Dependencies**

```json
{
  "dependencies": {
    "@camptocamp/ogc-client": "^4.1.0"
  },
  "devDependencies": {
    "jest": "^29.7.0",
    "typescript": "^5.3.3"
  }
}
```

**2. Automated Dependency Updates**

**Tools:**

- **Dependabot:** GitHub automated dependency PR creation
- **Renovate:** Alternative with more configuration options

**Configuration (.github/dependabot.yml):**

```yaml
version: 2
updates:
  - package-ecosystem: 'npm'
    directory: '/'
    schedule:
      interval: 'weekly'
    open-pull-requests-limit: 5
    reviewers:
      - 'maintainer-username'
    labels:
      - 'dependencies'
      - 'automated'
```

**3. Breaking Change Detection**

**Process:**

1. Dependabot creates PR for dependency update
2. CI runs full test suite
3. If tests fail → breaking change detected
4. Manual review required
5. Update code and tests
6. Re-run tests
7. Merge when passing

### 2.3 Spec-Aware Test Maintenance

> **⚠️ AP3 Warning:** The `@specification` JSDoc tag traceability system and automated tooling (`scripts/test-traceability.js`) originally proposed in this section have been removed. They constitute anti-pattern AP3 — organizing tests around spec sections rather than client code behavior. The upstream codebase has zero spec-traceability infrastructure.

**Approach:** Use spec awareness as context for maintenance decisions, not as structural infrastructure.

**When a spec updates:**

1. Review spec changelog for changed sections
2. Identify which client behaviors the changes affect (URL patterns, response structures, error conditions)
3. Search test files for comments referencing those spec sections: `grep -r "Spec context:.*§7.2" src/`
4. Review and update affected tests to match new expected client behavior
5. Update fixtures if response structures changed
6. Run test suite
7. Review and merge

**Key principle:** Spec changes trigger test updates because they change what _correct client behavior_ looks like — not because we need to maintain spec-coverage metrics.

### 2.4 Automated Change Detection

**1. Continuous Integration Checks**

**GitHub Actions Workflow (.github/workflows/test.yml):**

```yaml
name: Test Suite
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '20'
      - run: npm ci
      - run: npm test
      - run: npm run test:coverage
      - name: Check coverage thresholds
        run: |
          # Fail if coverage drops below targets
          # Statement: 85%, Branch: 80%
      - name: Detect flaky tests
        run: npm test -- --runInBand --maxWorkers=1 --repeat=5
```

**2. Scheduled Test Health Checks**

**Monthly Health Check Workflow (.github/workflows/test-health.yml):**

```yaml
name: Monthly Test Health Check
on:
  schedule:
    - cron: '0 0 1 * *' # First day of each month
jobs:
  health-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
      - run: npm ci
      - run: npm test
      - name: Generate test health report
        run: |
          # Run traceability tool
          # Check for outdated fixtures
          # Check for trivial tests
          # Generate report
      - name: Create issue if problems found
        run: |
          # Create GitHub issue with findings
          # Assign to maintainer
```

**3. Fixture Validation Checks**

**Script: `scripts/validate-fixtures.js`**

```javascript
// Validate all fixtures against current schemas
function validateFixtures() {
  // Load all fixtures
  // Validate against JSON schemas
  // Check metadata completeness
  // Check spec version consistency
  // Report errors
}
```

**Usage:**

```bash
# Validate all fixtures
npm run fixtures:validate

# Validate fixtures for specific resource
npm run fixtures:validate -- --resource systems

# Update fixture metadata
npm run fixtures:update-metadata
```

### 2.5 Manual Review Triggers

> **⚠️ H3 fix:** The original monthly review checklist template (30+ checkbox items covering spec compliance, dependency health, test quality, fixture health, documentation, and technical debt) has been replaced with a brief checklist appropriate for an open-source contribution. Monthly formal reviews with named reviewers and dated reports are not appropriate — simply review tests when they break or when upstream changes.

**When to review tests:**

- A dependency update breaks something
- A new spec version is published
- Tests start failing after an upstream merge
- You notice a test that doesn't actually validate anything

---

## 3. Test Update Workflows

> **⚠️ H3 fix:** The original 9-step spec update workflow (with ASCII art flowchart, 2–4 week timeline, 16–32 hours estimate, and named roles at each stage) and separate dependency/refactoring/retirement workflows with 5–7 steps each have been replaced with brief practical guidance. Upstream `camptocamp/ogc-client` has no documented update workflow.

### 3.1 When Specs Update

1. Read the spec changelog to identify changes that affect client behavior
2. Update implementation code for any changed behavior
3. Update test fixtures if response schemas changed
4. Update test assertions to match new expected behavior
5. Update spec context comments in affected tests
6. Submit PR with all changes together

### 3.2 When Dependencies Update

1. Run tests after updating the dependency
2. If tests pass, merge the update
3. If tests fail, fix the test or implementation code to match the new API
4. For breaking changes, update fixtures and assertions as needed

### 3.3 When Refactoring Implementation

- **Internal refactoring (private methods):** Tests should still pass — if they don't, the tests are too tightly coupled to implementation details
- **Public API changes:** Update tests to use the new API. If the old API is deprecated, add tests for the new API and mark old tests for removal.

### 3.4 When Retiring Tests

Remove tests when:

- The feature they test has been removed from the codebase
- They duplicate other tests without adding value
- They test implementation details that no longer exist

---

## 4. Maintenance Responsibilities

> **⚠️ H3 fix:** The original RACI matrix with 5 invented roles (Test Owner, Component Maintainer, Release Manager, Tech Lead, Documentation Maintainer), role assignment tables, 6-month ownership timelines, and detailed per-role responsibility lists have been removed. These roles do not exist in upstream `camptocamp/ogc-client`. This is a contribution to someone else's repository — the upstream maintainer decides who reviews and merges PRs.

**Ownership model:** The developer who writes tests is responsible for keeping them working. When submitting a PR to upstream, the contributor is responsible for:

1. All tests pass before PR submission
2. Tests are updated when implementation changes
3. Fixtures are updated when upstream API changes
4. Responding to maintainer feedback on test quality

---

## 5. Test Rot Prevention Strategy

### 5.1 Test Rot Indicators

**Definition:** Test rot occurs when tests become outdated, trivial, or no longer provide value.

**Indicators:**

| Indicator                 | Description                                 | Detection Method                    | Severity |
| ------------------------- | ------------------------------------------- | ----------------------------------- | -------- |
| **Always Passes**         | Test passes even when code is broken        | Intentional breakage validation     | HIGH     |
| **Tests Mocks**           | Test validates mock behavior, not real code | Code review, mock complexity > code | HIGH     |
| **No Assertions**         | Test has setup but minimal/no validation    | Grep for tests with no `expect()`   | CRITICAL |
| **Trivial Checks**        | Only checks `.toBeTruthy()` without depth   | Grep for shallow assertions         | HIGH     |
| **Outdated Fixtures**     | Fixtures from old spec version              | Fixture metadata check              | MEDIUM   |
| **Outdated Spec Context** | Spec context comments reference old version | Manual review                       | LOW      |
| **Coverage Drop**         | Coverage decreases over time                | Coverage trend monitoring           | MEDIUM   |
| **Flaky Tests**           | Tests fail intermittently                   | CI failure tracking                 | HIGH     |
| **Slow Tests**            | Test execution time increases               | Performance monitoring              | LOW      |
| **Documentation Drift**   | Test docs don't match behavior              | Manual review                       | LOW      |

**How to detect test rot (no custom tooling required):**

- Search for tests with no `expect()` calls
- Search for tests that only use `toBeTruthy()` or `toBeDefined()`
- Intentionally break code and verify tests fail
- Review coverage reports for declining trends

### 5.2 Prevention

> **⚠️ H3 fix:** The original §5.2–5.6 included a monthly health check procedure (automated + manual, 1.5–2.5 hours/month), a custom `scripts/detect-test-rot.js` tool, a quality metrics dashboard auto-generated by CI, a deprecation warning system with 3-6 month timelines, a technical debt tracking system with GitHub issue labels/templates/prioritization tiers, and separate Pre-Commit/PR Review/Post-Merge checklists. This infrastructure is disproportionate for a contribution to an upstream library. Simplified to a brief prevention checklist.

**Keep tests valuable by:**

1. Writing meaningful assertions from the start (not `toBeTruthy()`)
2. Testing behavior, not implementation details
3. Using real fixtures, not invented data
4. Fixing broken tests immediately rather than skipping them
5. Removing tests when the feature they test no longer exists

---

## 6. Test Evolution Documentation

> **⚠️ H3 fix:** The original §6 included a detailed test changelog template (`tests/CHANGELOG.md`), a spec version history document (`tests/SPEC-VERSIONS.md`), migration guides with per-field before/after examples and effort estimates, and an auto-generated test inventory by component and spec section. This level of documentation infrastructure is not practical for a contribution to an upstream library that has no test changelog or migration guides.

**When making significant test changes, document them in commit messages and PR descriptions.** This is standard open-source practice and provides adequate traceability through git history.

---

## 7. Maintenance Tooling

> **⚠️ H3 fix:** The original §7 proposed 7+ custom tools (rot detection tool, fixture validation tool, health report generator, spec version updater, fixture migration tool, test metrics web dashboard) with 33.5–46.5 hours of development effort, plus GitHub Actions workflows (monthly health check cron job, Dependabot/Renovate configuration). The contributor does not control upstream CI/CD configuration. These tools have been removed. Use standard tooling that already exists in the project.

**Available tooling (no custom scripts needed):**

- `npm test` — run the test suite
- `npm run test:coverage` — generate coverage report
- `grep` — find tests referencing specific spec sections or patterns
- Git history — track when and why tests changed

---

## 8. Key Recommendations

> **⚠️ H3 fix:** The original §8 (Implementation Estimates) with 33.5–46.5 hours of tooling development and 84–184 hours/year annual maintenance burden has been removed. The original §9 (Key Recommendations) recommended implementing a traceability tool, monthly health checks, component maintainer assignments, Dependabot configuration, and tracking 8 success metrics with monthly/quarterly/annual reviews. These have been simplified to practical guidance.

**Essential practices:**

1. Keep tests passing — fix failures immediately
2. Update fixtures when spec or API changes
3. Follow upstream conventions — match their testing style
4. Write meaningful assertions — not just `toBeTruthy()`
5. Remove obsolete tests — don't maintain dead code

**Avoid over-engineering:**

- No custom maintenance tools for a library contribution
- No monthly formal health checks — just fix issues when you see them
- No RACI matrices or invented roles — standard PR review is sufficient
- No multi-week update workflows — just update, test, and submit a PR

2. ✅ Set up monthly health checks (prevent rot)
3. ✅ Assign component maintainers (clear ownership)
4. ✅ Track spec version in tests and fixtures (enable updates)
5. ✅ Configure Dependabot (automate dependency PRs)

## **SHOULD (Highly Recommended):**

## 9. Summary

> **⚠️ H3 fix:** The original summary (§10) repeated the enterprise infrastructure: "Four Maintenance Pillars" (RACI matrix, monthly health checks, automated rot detection, traceability tool), 5 invented roles, 120–184 hours/year effort, and multi-week workflows. Simplified below.

**Test maintenance for CSAPI contribution to `camptocamp/ogc-client`:**

1. **Fix broken tests immediately** — don't let failures accumulate
2. **Update fixtures when APIs change** — keep test data current
3. **Follow upstream conventions** — match their testing style
4. **Remove obsolete tests** — don't maintain dead code
5. **Use spec as input** — spec informs what correct client behavior looks like

**What this unblocks:**

- Tests remain valuable as the project evolves
- Clear path to update tests when spec or upstream changes
- Low maintenance overhead appropriate for a library contribution

---

## 10. References

### 10.1 Related Research Sections

- **Section 15:** Fixture Sourcing and Organization (fixture maintenance procedures)
- **Section 35:** JSDoc Testing Documentation Standards (spec context comments, test documentation)
- **Section 36:** Test Quality Checklist and Review Process (quality standards, rot indicators)

### 10.2 External References

- **Lessons Learned Analysis:** [docs/research/requirements/lessons-learned-analysis.md](../../requirements/lessons-learned-analysis.md)
- **CSAPI Implementation Guide:** [docs/planning/csapi-implementation-guide.md](../../../planning/csapi-implementation-guide.md)
- **ROADMAP:** [docs/planning/ROADMAP.md](../../../planning/ROADMAP.md)

### 10.3 Specifications

- **OGC 23-001:** Connected Systems API - Part 1: Feature Resources
- **OGC 23-002:** Connected Systems API - Part 2: Observation Data
- **OGC 23-003:** Connected Systems API - Part 3: Command & Control

### 10.4 Tools and Frameworks

- **Jest:** Testing framework (coverage)
- **GitHub Actions:** CI/CD workflows (upstream-controlled)

---

**Document Status:** ✅ COMPLETE  
**Review Status:** H3 fix applied — enterprise infrastructure simplified  
**Next Steps:** Follow the three core maintenance guidelines when contributing tests
