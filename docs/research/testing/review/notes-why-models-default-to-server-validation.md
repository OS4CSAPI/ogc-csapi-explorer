# Why AI Models Default to Server-Oriented Testing for OGC Specs

**Date:** February 13, 2026  
**Context:** During Phase 2D issue resolution, a question arose about why multiple AI models (ChatGPT, Claude Sonnet 4.5) consistently produced server-oriented tests instead of client parser tests — and why they couldn't self-correct even during review. This document captures the analysis.

---

## The Problem

Multiple AI models, when asked to plan and implement tests for CSAPI's SensorML parser, consistently:

- Planned server conformance tests instead of parser output tests
- Implemented validation rule checklists (VAL-SML, ERR-SML) that test whether documents conform to the spec
- Told the user the tests were good
- Could not be guided toward the correct approach even during explicit review

## Why This Happens

### 1. The Specs Are Written from the Server's Perspective

OGC specifications define what a _conformant implementation_ MUST/SHOULD/MAY do. Every requirement, every conformance class, every normative statement is framed as "the server SHALL produce..." or "a valid document MUST contain..." When a model ingests that text, the gravitational pull is toward conformance testing. The spec literally hands you a checklist of validation rules. Extracting "what should a _client parser_ do with this?" requires reasoning one level removed from the text.

### 2. Validation Rules Are Easy to Enumerate; Output Models Require Design

The spec says "PhysicalSystem MUST have uniqueId conforming to URI format." That maps trivially to `expect(isValidUri(result.uniqueId)).toBe(true)`. Done — looks thorough, looks spec-aligned. But the _right_ test — `expect(result.uniqueId).toBe("urn:example:sensor")` — requires the model to first _invent_ the return type of `parseSensorML()`, which the spec doesn't define because that's an implementation decision. Models are much more comfortable translating existing text than making design decisions that aren't in the source material.

### 3. Training Data Reinforcement

OGC has entire conformance test suites (CITE/TEAM Engine). Most publicly available test code for OGC standards IS server conformance testing. Client library parser tests for OGC standards are comparatively rare in training data. So the pattern the models have seen most often for "OGC + testing" is conformance validation.

### 4. "Comprehensive" Rewards the Wrong Thing

When you ask a model to be thorough, it gets rewarded (by its training) for covering more ground. Listing 21 VAL-SML rules and 22 ERR-SML scenarios _looks_ more comprehensive than saying "define 5 core parser tests with expected output objects." The validation approach produces impressive-looking matrices and checklists. The parser approach produces shorter, more focused tests that require harder thinking about what the parser actually returns.

### 5. Review Doesn't Escape the Same Framing

When you asked models to review work that followed this pattern, they were evaluating it against the same spec-centric frame. The review question becomes "did we cover all the spec requirements?" rather than "are we testing the right thing?" The work looks rigorous — it references specific spec sections, it has requirement IDs, it covers edge cases. All the surface signals of quality are present. The architectural question ("but whose job is this?") requires stepping back from the text to think about system roles, which is a different kind of reasoning.

### 6. The Client/Server Boundary Is Implicit, Not Stated

No OGC spec says "a client parser should NOT validate incoming data." The distinction between "parse and extract" versus "parse and validate" is an architectural judgment call informed by how the upstream library works, what client libraries conventionally do, and what produces useful tests. It's not wrong knowledge — it's absent knowledge that requires inference from context (the existing codebase patterns, the library's role in the ecosystem).

## The Short Version

The specs are a validation-shaped magnet, and models followed the shape of the source material rather than reasoning about the architectural role of the code being tested. The fix wasn't more spec knowledge — it was asking a different question: "what does _our code_ do, and how do we verify it does it correctly?"

---

_These notes were captured during Phase 2D issue resolution to document a systemic pattern observed across multiple AI models working on this project._
