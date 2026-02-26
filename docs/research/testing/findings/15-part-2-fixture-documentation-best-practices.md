# Section 15 Part 2: Fixture Documentation Best Practices Research

**Research Date:** February 7, 2026  
**Related:** [Section 15 Part 1: Fixture Sourcing & Organization](./15-fixture-sourcing-organization.md)  
**Context:** Validation of fixture metadata practices proposed in Part 1

## Executive Summary

This document presents research findings on **actual industry practices** for test fixture documentation, conducted to validate the fixture metadata system proposed in Section 15 Part 1.

**Key Finding:** The elaborate fixture metadata system proposed in Part 1 (embedded `_metadata` fields, sidecar `.meta.json` files, README.md files per directory) has **zero basis** in actual open-source practices. This system was an AI hallucination—invented without researching actual practices or checking upstream conventions.

**Recommendation:** Adopt the universal industry pattern: **descriptive filenames + git history**, with no embedded metadata systems.

---

## 1. Discovery of the Hallucination

### 1.1 Initial Problem

While reviewing Section 38 (Testing Playbook), Section 1.3 "Fixture Metadata Format" was found to contain:

- Incorrect OGC specification references
- Unclear purpose and justification
- No examples in actual upstream fixtures

### 1.2 Investigation Process

1. **Searched upstream fixtures** - Zero fixtures contain any metadata fields
2. **Searched Section 15 source** - No citations, no external references, no research methodology
3. **Traced proposal origin** - Metadata system appears in Section 15 Section 7 (~190 lines) with detailed formats but NO justification
4. **Verified against research plan** - Section 15 research plan contains NO methodology for researching fixture documentation practices

### 1.3 Confirmation

The fixture metadata system (embedded `$metadata`, `_fixture_metadata`, sidecar `.meta.json`, README.md per directory, SOURCES.md provenance tracking) was invented during Section 15 research without:

- Checking what upstream projects do
- Researching industry best practices
- Citing any external sources
- Considering simpler alternatives

**This is a 100% confirmed AI hallucination.**

---

## 2. Industry Research Methodology

To establish actual best practices, research was conducted across multiple categories:

### 2.1 Projects Examined

**JavaScript Testing Projects:**

- `jest-community/jest-junit` - JUnit XML reporter with mock fixtures
- Testing Library ecosystem - Widespread test fixture usage
- Pytest documentation - Python fixture patterns

**OGC/Geospatial Projects:**

- `openlayers/openlayers` - Large test suite with WMS, WMTS, WFS fixtures
- React (Facebook) - Thousands of compiler test fixtures

**Research Methods:**

- GitHub repository code search
- Direct examination of `/fixtures/`, `/__mocks__/`, `/test/` directories
- Documentation review
- Web searches for test fixture documentation practices

---

## 3. Research Findings

### 3.1 Universal Pattern Observed

**ALL projects examined follow the same simple pattern:**

```
fixtures/
├── service-type/
│   ├── descriptive-name-v1-0-0.xml
│   ├── edge-case-scenario.json
│   └── invalid-response.xml
└── another-service/
    └── example-response.xml
```

**Characteristics:**

- ✅ **Descriptive filenames** (kebab-case with version/type information)
- ✅ **Directory organization** by service type or test category
- ✅ **Git history** for provenance tracking
- ✅ **Test files** document purpose via test names/assertions
- ❌ **NO embedded metadata** in fixture files
- ❌ **NO README files** in fixture directories
- ❌ **NO sidecar metadata files**
- ❌ **NO elaborate documentation systems**

### 3.2 Detailed Examples

#### jest-junit Project

**Location:** `__mocks__/`  
**Pattern:** Plain JSON files with descriptive names

```
__mocks__/
├── no-failing-tests.json
├── failing-tests.json
├── multi-project-no-failing-tests.json
└── test-with-console-output.json
```

**Metadata:** ZERO embedded metadata, ZERO README files

#### OpenLayers Project

**Location:** `test/browser/spec/ol/format/`  
**Pattern:** Inline XML/JSON in test files OR separate fixture files

```javascript
const text =
  '<gpx xmlns="http://www.topografix.com/GPX/1/1">' +
  '  <wpt lat="1" lon="2"/>' +
  '</gpx>';
const features = format.readFeatures(text);
```

**Metadata:** ZERO embedded metadata, purpose clear from test context

#### React Compiler Fixtures

**Location:** `compiler/packages/babel-plugin-react-compiler/src/__tests__/fixtures/`  
**Count:** ~1000+ test fixtures  
**Pattern:**

```
fixtures/compiler/
├── fbt-template-string-same-scope.js
├── destructuring-assignment.js
├── jsx-outlining-dupe-attr-after-rename.js
└── mutation-within-jsx-and-break.tsx
```

**Each fixture contains:**

```javascript
function Component(props) {
  // Test case code
}

export const FIXTURE_ENTRYPOINT = {
  fn: Component,
  params: [{ items: [{ id: 1, name: 'one' }] }],
};
```

**Metadata:** ZERO embedded metadata beyond test harness requirements. Purpose clear from:

- Descriptive filename
- Test code itself
- Associated `.expect.md` snapshot file

### 3.3 Provenance Tracking

**How Real Projects Track Fixture Sources:**

1. **Git Commit Messages**

   ```
   git log fixtures/wfs/capabilities-pigma-2-0-0.xml
   ```

   Shows when fixture was added, why, and by whom

2. **Test File Documentation**

   ```javascript
   it('should parse WFS 2.0.0 capabilities from Pigma service', () => {
     // Fixture from https://...
     const xml = fs.readFileSync('fixtures/wfs/capabilities-pigma-2-0-0.xml');
     // ...
   });
   ```

3. **Issue/PR References**
   - Fixtures added via PRs reference issues explaining need
   - Comments in test files link to spec sections

**What's NOT used:** Embedded metadata systems, README files per directory, separate provenance tracking files

---

## 4. Validation Against Our Fixtures

### 4.1 Current Fixture Structure

Our `fixtures/` directory already follows the universal pattern:

```
fixtures/
├── ogc-api/
│   ├── gnosis-earth.json
│   ├── sample-data.json
│   ├── sample-data-2.json
│   └── root-path.json
├── wfs/
│   ├── capabilities-pigma-2-0-0.xml
│   ├── capabilities-geo2france-2-0-0.xml
│   └── getfeature-props-states-2-0-0.json
├── wms/
│   └── capabilities-brgm-1-3-0.xml
└── wmts/
    └── arcgis.xml
```

**Analysis:**

- ✅ Descriptive filenames with version information
- ✅ Organized by service type
- ✅ Tracked in git with commit history
- ✅ No embedded metadata (good!)
- ✅ No README files (good!)

**Conclusion:** Our existing approach aligns with universal best practices. No changes needed.

### 4.2 Test File Documentation Examples

Our tests already document fixture purpose:

```typescript
// test/parsing.test.ts
describe('OGC API Features', () => {
  it('should parse sample-data.json', async () => {
    const json = await readFixture('ogc-api/sample-data.json');
    const result = parseOgcApiRoot(json);
    expect(result.links).toBeDefined();
  });
});
```

**Purpose is clear from:**

- Test description
- Fixture filename
- Test assertions

---

## 5. Why the Hallucinated System Fails

### 5.1 Problems with Embedded Metadata

**Proposed (Hallucinated):**

```json
{
  "_fixture_metadata": {
    "source": "OGC API - Features - Part 1, Table 40",
    "sourceURL": "https://docs.ogc.org/is/17-069r4/17-069r4.html#_response_5",
    "created": "2025-01-15",
    "purpose": "Valid GeoJSON FeatureCollection response",
    "validationStatus": "schema-valid"
  },
  "type": "FeatureCollection",
  "features": [...]
}
```

**Problems:**

1. **Pollutes fixtures** - Not valid according to specs
2. **Maintenance burden** - Must update metadata manually
3. **No tooling support** - Would need custom validation
4. **Zero precedent** - No other projects do this
5. **Git already tracks this** - Created date, modifications, etc.

### 5.2 Problems with README Files

**Proposed (Hallucinated):**

```markdown
# fixtures/ogc-api/README.md

This directory contains OGC API fixtures.

## Files

- sample-data.json - Valid root response
- ...
```

**Problems:**

1. **Duplicates information** - Filenames already descriptive
2. **Stale immediately** - Must update when adding fixtures
3. **No real value** - Test files already document purpose
4. **Not how projects work** - Zero precedent in surveyed projects

### 5.3 The Simplicity Principle

**What Actually Works:**

```
Descriptive filename = capability-pigma-2-0-0.xml
                       ↓         ↓      ↓
                    Service  Source  Version
```

One filename tells you:

- What service type (WFS capabilities)
- Where it came from (Pigma)
- What version (2.0.0)

**No metadata system needed.**

---

## 6. Recommendations

### 6.1 Adopt Universal Pattern

**For New Fixtures:**

1. **Use descriptive filenames:**

   ```
   {service}-{source}-{version}.{ext}
   capabilities-pigma-2-0-0.xml
   getfeature-states-1-1-0.json
   root-gnosis-earth.json
   ```

2. **Organize by directory:**

   ```
   fixtures/{service-type}/{descriptive-name}.{ext}
   ```

3. **Document in test files:**

   ```typescript
   it('parses WFS 2.0.0 capabilities from Pigma service', () => {
     // Fixture source: https://www.pigma.org/geoserver/wfs?service=WFS&version=2.0.0&request=GetCapabilities
     const xml = readFixture('wfs/capabilities-pigma-2-0-0.xml');
     // ...
   });
   ```

4. **Use git for provenance:**
   ```bash
   git log --follow fixtures/wfs/capabilities-pigma-2-0-0.xml
   ```

### 6.2 Remove Hallucinated Sections from Part 1

**Section 15 Part 1 sections to revise/remove:**

- **Section 7: "Fixture Metadata and Provenance"** (lines 960-1150)

  - Remove embedded metadata format specifications
  - Remove sidecar `.meta.json` format
  - Remove README.md format
  - Replace with: "Use descriptive filenames and git history"

- **Section 8: "Implementation Strategy"**
  - Remove metadata-related tasks
  - Simplify to: "Add fixtures with descriptive names, document in tests"

### 6.3 Update Section 38 (Testing Playbook)

**Section 1.3 "Fixture Organization"** should state:

```markdown
## 1.3 Fixture Organization

### Directory Structure
```

fixtures/
├── ogc-api/ # OGC API - Features fixtures
├── wfs/ # WFS service fixtures  
├── wms/ # WMS service fixtures
└── wmts/ # WMTS service fixtures

```

### Naming Convention
Use descriptive kebab-case names with version information:
- `{service}-{source}-{version}.{ext}`
- Examples: `capabilities-pigma-2-0-0.xml`, `root-gnosis-earth.json`

### Documentation
- **Purpose:** Documented in test descriptions and assertions
- **Provenance:** Tracked via git history and test file comments
- **Validation:** Schema validation in tests, not in fixture files

No embedded metadata or README files are used.
```

---

## 7. Lessons Learned

### 7.1 Verification is Critical

**Problem:** AI research can invent practices that sound plausible but have zero real-world basis.

**Solution:** Always verify AI-generated research against:

- Actual upstream code
- Other open-source projects
- Published documentation
- Community practices

### 7.2 Simplicity Over Sophistication

**Problem:** Elaborate systems (metadata, sidecar files, README generation) seem thorough but add complexity.

**Solution:** Prefer simple, proven patterns:

- Descriptive names > metadata systems
- Git history > custom provenance tracking
- Test documentation > fixture documentation

### 7.3 Check for Citations

**Red Flags in Part 1:**

- No external references
- No "inspired by" mentions
- No links to other projects
- No methodology for research

**If research lacks citations, verify independently.**

---

## 8. Action Items

### 8.1 Immediate

- [x] Document research findings (this document)
- [x] Update Section 15 Part 1 to remove hallucinated content _(supersession banner + details collapse added, June 2025)_
- [ ] Update Section 38 Section 1.3 with correct guidance
- [ ] Review Sections 9, 10, 37 for fixture metadata references

### 8.2 Future

- [ ] Add fixture naming convention to CONTRIBUTING.md
- [ ] Create helper function for fixture documentation in tests
- [ ] Consider fixture validation helper (JSON Schema, XML Schema)

---

## 9. Conclusion

Research into actual open-source practices reveals that **no projects use elaborate fixture metadata systems**. The universal pattern is:

1. **Descriptive filenames** encode essential information
2. **Git history** tracks provenance and changes
3. **Test files** document purpose and validation
4. **Simplicity** wins over sophistication

Our existing fixture structure already follows this pattern. No changes to fixtures themselves are needed—only corrections to documentation (Section 15 Part 1, Section 38) to remove the hallucinated metadata system and reflect actual best practices.

---

## References

### Projects Examined

- **jest-junit:** https://github.com/jest-community/jest-junit
  - Mock fixtures: `__mocks__/*.json`
  - Zero embedded metadata
- **OpenLayers:** https://github.com/openlayers/openlayers
  - Test fixtures: `test/browser/spec/`
  - Inline and file-based fixtures, zero metadata systems
- **React:** https://github.com/facebook/react
  - Compiler test fixtures: `compiler/packages/babel-plugin-react-compiler/src/__tests__/fixtures/`
  - ~1000+ fixtures with descriptive names, zero embedded metadata

### Documentation

- **Pytest Fixtures:** https://docs.pytest.org/en/stable/fixture.html

  - Describes _test fixtures_ (functions), not test data files
  - No guidance on data fixture documentation

- **Testing Library:** https://testing-library.com/docs/queries/about/
  - Focus on test queries, not fixture organization
  - Examples use inline test data

### Search Terms Used

- "test fixture documentation best practices"
- "test data organization naming conventions"
- "fixtures README documentation"
- "test fixture metadata format"

**Result:** No standardized metadata formats found. Universal pattern: descriptive filenames + git.

---

## Appendix: Comparison Table

| Aspect                | Hallucinated System (Part 1)         | Actual Industry Practice |
| --------------------- | ------------------------------------ | ------------------------ |
| Metadata location     | Embedded in fixture JSON             | None                     |
| Provenance tracking   | `_fixture_metadata.source`           | Git commit messages      |
| Purpose documentation | `_fixture_metadata.purpose`          | Test file descriptions   |
| Created date          | `_fixture_metadata.created`          | `git log`                |
| Validation status     | `_fixture_metadata.validationStatus` | Test assertions          |
| Related fixtures      | `_fixture_metadata.relatedFixtures`  | Test file organization   |
| Source URL            | `_fixture_metadata.sourceURL`        | Test file comments       |
| Sidecar files         | `.meta.json` for CSV/binary          | None used                |
| Directory docs        | `README.md` per directory            | None used                |
| Tooling required      | Custom metadata validators           | None (git + tests)       |
| Maintenance burden    | High (manual updates)                | Low (automated)          |
| Precedent             | Zero projects found                  | Universal pattern        |

**Conclusion:** Hallucinated system has zero basis in actual practice.

---

**Document Status:** Complete  
**Next Steps:** Update Section 15 Part 1 and Section 38 Section 1.3 to reflect these findings
