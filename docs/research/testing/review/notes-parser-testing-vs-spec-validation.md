# Parser Testing vs. Spec Validation — Clarification Notes

**Date:** February 13, 2026  
**Context:** During Phase 2D issue resolution (C1, C2), a question arose about whether our review corrections were weakening the spec correlation in our testing. This document captures the reasoning.

---

## What We're NOT Saying

We are **not** saying "ignore the spec." The spec is the entire foundation — the parser exists _because of_ the spec. Every property it extracts, every structure type it recognizes, every nesting relationship it traverses — all of that comes from the SensorML 3.0 and CSAPI specifications. The spec knowledge is essential and fully retained.

## What We ARE Saying

The distinction is between two different jobs:

### Job 1: "Is this document a valid SensorML document?" (Server/Validator concern)

- Does `uniqueId` follow RFC 3986 URI format?
- Is `validTime.start` before `validTime.end`?
- Does this `PhysicalSystem` have all REQUIRED properties per the spec?
- Is this enum value one of the allowed values?

This is **spec conformance validation** — checking whether the _server produced correct data_. The VAL-SML and ERR-SML IDs were testing this. A client library shouldn't reject a server response because a date range is backwards or a URI has a non-standard format.

### Job 2: "Does my parser correctly transform this JSON into a useful TypeScript object?" (Client/Parser concern)

- Given a PhysicalSystem fixture with `uniqueId: "urn:example:sensor"`, does `parseSensorML()` return `{ uniqueId: "urn:example:sensor", type: "PhysicalSystem", ... }`?
- Given a 3-level nested component structure, does the parser produce the correct nested TypeScript objects?
- Given a fixture with SWE Common characteristics, are they correctly extracted into typed output?
- Given malformed JSON, does the parser throw (because it literally can't parse)?

This is what we should test. **Same spec knowledge, different question.** Instead of "is this document valid?" we ask "does my code correctly extract this document into typed output?"

## The Middle Ground — Structural Validation

There IS a natural form of validation that happens during parsing — **structural validation**:

- If the parser expects `components` to be an array and receives a string, it can't parse it into an array of component objects. That's a real parser problem.
- If the `type` field is missing, the parser can't dispatch to the right handler. That's a real parser problem.
- If circular references cause infinite recursion, that's a real parser problem.

These are legitimate parser errors and they stayed in the C2 corrections (ERR-SML-001/002, 010, 022, 030). The parser **does** need to understand the spec's structure to know what shape to expect.

What we removed is **semantic validation**: checking whether a URI follows the right format, whether a temporal range is logically valid, whether an optional-but-recommended property is present. Those are data quality questions about the server, not parser correctness questions about our code.

## Concrete Example

```typescript
// Fixture: physical-system-basic.json
{ "type": "PhysicalSystem", "uniqueId": "urn:example:weather-station", "components": [...] }

// WRONG test (spec conformance — tests the document, not the parser):
// VAL-SML-001: "PhysicalSystem MUST have uniqueId matching URI format"
expect(isValidUri(fixture.uniqueId)).toBe(true);  // ← testing the fixture, not our code

// RIGHT test (parser correctness — tests our code):
const result = parseSensorML(fixture);
expect(result.uniqueId).toBe("urn:example:weather-station");  // ← did OUR parser extract it?
expect(result.type).toBe("PhysicalSystem");
expect(result.components).toHaveLength(3);
expect(result.components[0].type).toBe("PhysicalComponent");
```

Both tests require spec knowledge. But the first tests whether the _fixture data_ is valid. The second tests whether _our parser code_ works correctly.

## What the Upstream Library Does

The existing `ogc-client` parsers (WMS, WFS, WMTS) follow this exact pattern. They parse XML capabilities documents into typed objects. They don't validate whether the server's XML conforms to the WMS spec — they extract what's there and produce a useful TypeScript model. Their tests are: "given this fixture, does parsing produce this expected output?"

## What Changed in Doc 09 (C2 Resolution)

**Preserved (spec knowledge fully retained):**

1. The **property matrices** (Section 2) — they tell us what to extract
2. The **recursive nesting strategy** (Section 4) — it tells us how deep to parse
3. The **SWE Common integration** (Section 5) — it tells us what sub-parsers to call
4. The **spec example fixtures** (Section 7) — they're the primary test inputs
5. The **test estimates and phasing** (Section 14)

**Annotated (retained as reference, reframed from test identifiers):**

- VAL-SML/ERR-SML IDs → retained as **reference** (they tell us what input shapes exist), not as test identifiers
- Enforcement levels → reframed from "parser rejects invalid documents" to "parser extracts values into typed output"
- OpenSensorHub live sourcing → removed (anti-pattern AP2, same as upstream)
- Missing piece flagged → define the TypeScript output interface first (what does `parseSensorML()` return?)

## The Bottom Line

The spec correlation is **stronger** after this change, not weaker. Before, the tests would have verified "does this JSON match the SensorML spec?" — which is the server's job and would pass or fail based on fixture data quality. After, the tests verify "does our parser correctly implement the spec by extracting all spec-defined properties into the right TypeScript fields?" — which directly tests whether we built the parser correctly.

---

_These notes were captured during Phase 2D issue resolution to address a legitimate concern about spec correlation in our testing approach._
