# F57 Correction Report — 52North Content Negotiation Error

**Date:** 2026-02-15  
**Triggered by:** Human collaborator observed deployment data visible in 52North HTML viewer  
**Original finding:** F57 — "52North server data has been completely removed" (Phase 3.4 smoke test)  
**Corrected finding:** Data was never lost; AI changed `Accept` header between smoke tests  
**Lessons Learned:** L13 — "AI Drift Can Fabricate Findings That Survive Re-Verification"

---

## Timeline of Events

### Phase 3.3 Smoke Test (earlier on 2026-02-15)

- Smoke test #12 fetched 52North data successfully
- 52North profile: **3 systems, 1 deployment, 1 procedure** — all confirmed present
- F50 noted: "52North default content type changed to SML" — `application/sml+json`
- Request method: PowerShell `Invoke-WebRequest` / `Invoke-RestMethod` with **no explicit Accept header**
- Server default: `application/sml+json` → SensorML data store → **data returned**

### Phase 3.4 Smoke Test (later on 2026-02-15, same day)

- Smoke test #13 reported **all 52North collections empty**
- F57 filed: "52North server data has been completely removed"
- F57 classified as: Moderate severity, Upstream ownership, "consistent with a database reset"
- F57 "independently re-verified": same conclusion
- 10 prior findings impacted (F10, F11, F15, F41, F42, F43, F44, F47, F50, F55)
- Request method: PowerShell with **`Accept: application/json` explicitly set**
- Server behavior: `application/json` → pygeoapi GeoJSON provider → **empty data**

### Human Challenge (2026-02-15)

1. Human opened `https://csa.demo.52north.org/deployments` in browser → saw deployment data
2. Human expressed concern that a code change may have caused interoperability issue
3. AI investigated, found HTML page uses `<cs-viewer>` web component → initially dismissed as browser cache
4. Human performed Ctrl+Shift+R hard refresh → data still present
5. AI tested `Accept: application/sml+json` → **all data returned immediately**
6. Root cause identified: content negotiation header change, not server data loss

---

## Root Cause Analysis

### What 52North Actually Does

52North's Connected Systems API (`connected-systems-pygeoapi`) runs two data providers side by side:

| Provider             | Content Type           | Response Shape                                                 | Data                                     |
| -------------------- | ---------------------- | -------------------------------------------------------------- | ---------------------------------------- |
| **pygeoapi GeoJSON** | `application/json`     | `{ type: "FeatureCollection", features: [...], links: [...] }` | **Empty** (no features loaded)           |
| **SensorML**         | `application/sml+json` | `{ items: [...], links: [...] }`                               | **3 systems, 1 deployment, 1 procedure** |

The `Accept` header determines which provider handles the request. With no `Accept` header, the server defaults to `application/sml+json` (the SensorML provider with data).

### What Changed Between Smoke Tests

| Aspect                | Phase 3.3 (data found)        | Phase 3.4 (data "lost")                       |
| --------------------- | ----------------------------- | --------------------------------------------- |
| Accept header         | None (server chooses default) | `application/json` (explicit)                 |
| Server default        | `application/sml+json`        | `application/sml+json`                        |
| Effective provider    | SensorML → **has data**       | GeoJSON → **empty**                           |
| Response Content-Type | `application/sml+json`        | `application/json`                            |
| Response shape        | `{ items: [...] }`            | `{ type: "FeatureCollection", features: [] }` |

The AI changed the Accept header between sessions. This was not a deliberate decision documented in the test methodology — it was an untracked drift in request construction.

### Why Re-Verification Failed

The "independent re-verification" noted in F57 was performed in the same session by the same agent using the same request pattern (`Accept: application/json`). Because the verification method was identical to the original observation, it confirmed the same wrong result.

True independent verification would have required:

- Testing with a different `Accept` header
- Testing with `?f=application/sml+json` query parameter
- Testing with no `Accept` header at all
- Checking the server's HTML viewer (which the human eventually did)

---

## Verification of Corrected State

Performed 2026-02-15 after root cause was identified:

```
Accept: application/sml+json

systems:      3 items  (PhysicalSystem, PhysicalSystem, PhysicalSystem)
deployments:  1 item   (Deployment: "Messtonne 1 - 2025 Test")
procedures:   1 item   (present)
datastreams:  400 Bad Request (content negotiation unsupported for this resource?)

Accept: application/json

systems:      0 features  (empty FeatureCollection)
deployments:  0 features  (empty FeatureCollection)
procedures:   0 features  (empty FeatureCollection)
datastreams:  500 Internal Server Error

No Accept header (server chooses default):

systems:      Content-Type: application/sml+json → 3 items (data present)
```

---

## Impact Assessment

### Documents Corrected

| Document                                   | Change                                                                    |
| ------------------------------------------ | ------------------------------------------------------------------------- |
| Phase 3.4 smoke test — F57                 | Struck through original finding, added correction note                    |
| Phase 3.4 smoke test — 52N Server Profile  | Struck through "data loss" warning, added correction note                 |
| Phase 3.4 smoke test — Summary             | Struck through "cannot verify" conclusions, added correction note         |
| Phase 3.4 smoke test — Verdict             | Struck through data loss narrative, added correction note                 |
| Phase 3.5 code review — Smoke Test section | Added correction header noting F57 was incorrect                          |
| Phase 3 Lessons Learned                    | Added L13: "AI Drift Can Fabricate Findings That Survive Re-Verification" |

### Findings Affected by F57 Correction

These findings were marked as "cannot verify" or "reversed" based on F57. Their actual status should be re-evaluated in the next smoke test:

| Finding                            | F57-Based Status | Actual Status                                                                                                   |
| ---------------------------------- | ---------------- | --------------------------------------------------------------------------------------------------------------- |
| F10 (52N has real data)            | "Reversed"       | **Still true** — data present via `application/sml+json`                                                        |
| F11 (52N uses SensorML format)     | "Changed"        | **Still true** — SML is the default and data-bearing format                                                     |
| F15 (52N adds third system)        | "Reversed"       | **Still true** — 3 systems present                                                                              |
| F41 (null featureType)             | "Cannot verify"  | **Should be re-verifiable** via SML responses                                                                   |
| F42 (null validTime)               | "Cannot verify"  | **Should be re-verifiable** via SML responses                                                                   |
| F43 (Procedures misclassified)     | "Cannot verify"  | **Should be re-verifiable** via SML responses                                                                   |
| F44 (CURIE + full URI forms)       | "Cannot verify"  | **Should be re-verifiable** via SML responses                                                                   |
| F47 (GeoJSON `@link` notation)     | "Cannot verify"  | **Requires GeoJSON format** — may still need `application/geo+json` Accept header test                          |
| F50 (default content type changed) | "Changed"        | **Nuanced** — default is still `application/sml+json`, but `application/json` goes to a separate empty provider |
| F55 (F42 no longer blocking)       | "Cannot verify"  | **Should be re-verifiable**                                                                                     |

### Important Caveat: GeoJSON vs SensorML Response Shapes

The correction reveals that F41, F42, F43, F44, and F47 were originally observed in **GeoJSON responses** (`application/json` or `application/geo+json`), not SensorML responses. Accessing the data via `application/sml+json` gives a different response shape (`items` array with SensorML objects, not `features` array with GeoJSON FeatureCollection). Re-verifying these GeoJSON-specific findings will require testing with `Accept: application/geo+json` to see if 52North's GeoJSON provider returns data in that format. If 52North only serves GeoJSON from the empty provider, then GeoJSON-specific findings may genuinely be unverifiable for 52North — but for a different reason than "data loss."

---

## Implications for Our Work

### Immediate

1. **52North dual-server testing is restored.** We are back to two-server validation capability — OSH for systems/samplingFeatures, 52North for systems/deployments/procedures.

2. **The next smoke test must use correct content negotiation.** All 52North requests should either use no `Accept` header (server default) or explicitly use `Accept: application/sml+json` for data-bearing responses.

3. **Response shape differs by content type.** `application/sml+json` returns `{ items: [...] }` while `application/json` returns `{ type: "FeatureCollection", features: [...] }`. Our response parser (future Phase 3/4 work) must handle both shapes.

### Architectural

4. **The `items` vs `features` envelope variation is confirmed with a real-world cause.** F3 and F45 already documented this variation, but now we know it's not just a server convention difference — it's a **content-type-driven routing difference within a single server**. The same server returns different envelope shapes depending on the content type.

5. **Content negotiation is more critical than we assumed.** L9 was written as a forward-looking concern for the response parser. This incident proves it's also a concern for smoke test methodology — and by extension, for any code that makes HTTP requests to these servers.

### Process

6. **AI smoke test methodology needs a content-negotiation checklist.** Every smoke test should test at least 3 Accept headers (`none`, `application/json`, `application/sml+json`) and document which was used for each observation. Header choice should never change silently between smoke tests.

7. **"Upstream" attribution requires ruling out our own changes first.** The instinct to blame the server was wrong. The corrective action is: when something that worked before stops working, diff our own behavior first.

---

## Lessons for AI-Human Collaboration

This incident demonstrated the value of human oversight in AI-assisted development:

1. **The human noticed what the AI missed.** The AI had high confidence in F57 — it survived re-verification, was documented with evidence, and was cited across multiple documents. The human noticed a single data point (the HTML viewer showed data) that contradicted the entire narrative.

2. **The human pushed past the AI's initial dismissal.** When the AI attributed the HTML data to browser caching, the human tested that hypothesis (Ctrl+Shift+R) and rejected it. This forced a deeper investigation.

3. **The AI's confidence was inversely correlated with correctness.** F57 was one of the most thoroughly-documented findings in the smoke test series. It had more evidence bullets, more impact analysis, and more dependent findings than any other finding. But it was wrong from the first observation.

4. **Known lessons are not automatically applied.** L9 (Content Negotiation Cannot Be Assumed) existed before F57 was written. The AI wrote L9, reviewed code against it, and then violated it. Awareness of a principle does not guarantee its application, especially when the AI is operating in a different mode (smoke testing vs code review).

---

## What This Means — Plain-Language Summary

### For the 52North Server

52North is **fine** — nothing was ever lost. What we discovered is that it runs a **dual-backend architecture**:

- **`application/sml+json`** (default) → Routes to the SensorML data store → **3 systems, 1 deployment, 1 procedure** — all present, never changed
- **`application/json`** → Routes to a separate pygeoapi GeoJSON provider → **empty** (no features loaded into this provider)

This is actually a valuable interoperability finding. The same server serves different data (and different response envelope shapes — `items` vs `features`) depending on the `Accept` header. It's not a bug per se, but it means clients that hard-code `Accept: application/json` will see an empty server even though data exists.

### For Our Work

**Good news:**

- **52North dual-server testing is restored.** We're back to two live servers for validation (OSH + 52North). The 10 findings that were marked "cannot verify" because of F57 are all potentially re-verifiable now.
- **No code was affected.** F57 was a documentation-only finding — it never caused code changes. The parser, type system, and tests are all clean.
- **Our SensorML parser already handles `application/sml+json`.** The `SimpleProcess` parser and format detection we built in Issue #19 target exactly the format that 52North's data-bearing provider returns.

**Important forward-looking considerations:**

- **Future smoke tests must document which `Accept` header was used** for every request. Header choice should never change silently between test runs.
- **The response parser will need to handle both envelope shapes** — `{ items: [...] }` from SML responses and `{ type: "FeatureCollection", features: [...] }` from GeoJSON responses — even from the same server.
- **Content negotiation (L9) is now proven critical for both code and testing methodology.** We wrote L9 as a parser concern, but this incident shows it's equally important for how we observe server behavior.

### For AI-Human Collaboration

This was a process failure on the AI's part. The AI changed the request pattern between smoke tests without tracking it, filed a confident finding based on the wrong data, "verified" it using the same wrong method, and initially dismissed the human's correct observation as browser caching. The finding survived because re-verification was performed in the same context that produced the error.

The detection path — the human noticing the HTML viewer had data, doing a hard refresh to rule out cache, and pushing the investigation — is exactly the kind of human oversight that keeps AI-assisted work honest. L13 captures this going forward.

---

## Prior Art: This Was Already Known

After the correction was complete, a review of [OS4CSAPI Discussion #2 — Sprint Goal #2 Feedback](https://github.com/orgs/OS4CSAPI/discussions/2) (October 2025, Code Sprint 26) revealed that this exact content negotiation behavior was **already documented four months before our smoke test encountered it**.

SpeckiJ (Jan Speckamp, 52North implementer) wrote on October 27, 2025:

> _"Sorry for the confusion, i forgot to explain that I actually tested it using the url: `https://csa.demo.52north.org/?f=application/geo%2Bjson` — Which hardcodes the feature-type to geojson - this bypasses the Content-Type parsing of pygeoapi which does not really handle our mimetypes well. **Specifically our implementation does not really deal well with the `Accept` Header containing multiple different keys in the case that they are all valid, but content is only available in some types.**"_

That last sentence describes exactly what we discovered: 52North has content available in `application/sml+json` but not in `application/json`, and the `Accept` header routes to different providers.

### Corroborating Evidence from the Discussion

| Discussion observation (Oct 2025)                                            | Our F57 experience (Feb 2026)                                                  |
| ---------------------------------------------------------------------------- | ------------------------------------------------------------------------------ |
| QGIS expects `application/json` / GeoJSON FeatureCollection                  | Our Phase 3.4 smoke test used `Accept: application/json`                       |
| QGIS saw empty or broken collections                                         | We saw empty FeatureCollections                                                |
| SpeckiJ workaround: `?f=application/geo%2Bjson` bypasses content negotiation | We found `Accept: application/sml+json` bypasses the empty GeoJSON provider    |
| "content is only available in some types"                                    | Exactly — SML provider has data, GeoJSON provider is empty                     |
| The example deployment shown is "Messtonne 1 - 2025 Test"                    | That's the same deployment we found when we tested with `application/sml+json` |

The discussion also reveals additional context:

- **All responses from the API are expected as `json` and `GeoJSON FeatureCollection`** by generic OGC API Features clients like QGIS
- **QGIS does not do handling/setting of response formats** (via `f` parameter), just assumes valid response types
- This is a **known limitation of 52North's pygeoapi integration**, not a server reset or database wipe
- SpeckiJ noted he would "try to develop a fix during this week" — but as of February 2026, the dual-backend behavior persists

### What This Means

If the AI had checked the organization's own discussion forum before attributing empty responses to "data loss," F57 would never have been filed. The information was available and documented by the server implementer himself. This reinforces L13 further — the AI didn't just drift on HTTP headers, it also failed to consult available context about known server behavior before reaching for the most dramatic explanation ("the database was wiped").
