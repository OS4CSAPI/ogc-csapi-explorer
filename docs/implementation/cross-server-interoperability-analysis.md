# Cross-Server Interoperability Analysis

**Date:** February 14, 2026
**Milestone:** Post Phase 2.3 — second-server comparative testing
**Servers tested:** OpenSensorHub (`http://45.55.99.236:8080/sensorhub/api`), 52North (`https://csa.demo.52north.org/`)
**Purpose:** Determine what is our bug vs. upstream, whether server behaviors are consistent, and whether our code works with both implementations.

> Based on findings from:
>
> - [OpenSensorHub smoke test](live-server-smoke-test-post-phase-2.3.md)
> - [52North smoke test](live-server-smoke-test-52north.md)

---

## 1. On Us or Upstream?

| Finding                                            | Whose Bug?                | Rationale                                                                                                                                                                                                                          |
| -------------------------------------------------- | ------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **F1: Query params in href break Convention 3**    | **Ours.**                 | Our `scanCsapiLinks` doesn't strip `?f=application/json` before extracting the path segment. Works today only by luck — HTML links (no query params) happen to appear before JSON links.                                           |
| **F2: `featuresOfInterest` vs `samplingFeatures`** | **Shared.**               | The OGC spec defines `samplingFeatures` as the resource path. 52North chose `featuresOfInterest` in their collection hrefs — that's a spec deviation on their side. But our code could be more resilient by recognizing the alias. |
| **F3: No CSAPI conformance classes**               | Upstream (52North).       | They just don't advertise them.                                                                                                                                                                                                    |
| **F5: 500s and 404s**                              | Upstream (52North).       | Broken server endpoints.                                                                                                                                                                                                           |
| **Response envelope (`items` vs `features`)**      | Upstream (OpenSensorHub). | The OGC standard specifies `FeatureCollection`/`features` — 52North follows the standard. OpenSensorHub uses a non-standard `items` key.                                                                                           |

**Bottom line:** Two bugs are ours (F1, F2). The rest is server-side variation.

---

## 2. Consistent or Different Server Behaviors?

**Wildly different.** These two servers diverge on nearly every dimension:

| Dimension                         | OpenSensorHub                                  | 52North                                          | Same?  |
| --------------------------------- | ---------------------------------------------- | ------------------------------------------------ | ------ |
| Root doc resource links           | 6 links (Convention 2)                         | None                                             | ❌     |
| CSAPI conformance classes         | 20+                                            | Zero                                             | ❌     |
| Response envelope                 | `{ items: [...] }`                             | `{ type: "FeatureCollection", features: [...] }` | ❌     |
| Collection link hrefs             | Clean paths                                    | Paths with query params                          | ❌     |
| FOI naming                        | `samplingFeatures`                             | `featuresOfInterest`                             | ❌     |
| Data present                      | Yes (12 systems, 100+ obs)                     | All empty                                        | ❌     |
| Broken endpoints                  | None                                           | 3 (datastreams, FOI, controlstreams)             | ❌     |
| Auth                              | Basic auth                                     | None                                             | ❌     |
| **Collection Convention 3 links** | **`rel: "items"` with resource href**          | **`rel: "items"` with resource href**            | **✅** |
| **Resource path names**           | **`/systems`, `/deployments`, etc.**           | **`/systems`, `/deployments`, etc.**             | **✅** |
| **Query param acceptance**        | **`limit`, `offset`, `bbox`, `datetime`, `q`** | **`limit`, `offset`, `bbox`, `datetime`, `q`**   | **✅** |

The servers agree on the core resource paths and query parameters — which is what our URL builder produces. They disagree on essentially everything around discovery, response shape, and naming edges.

---

## 3. Does Our Code Work With Both Servers?

### URL Generation: Yes

Every URL our 28 builder methods produce gets a 200 from both servers (for all Part 1 endpoints that aren't broken server-side). This is the core of what we've built and it's solid.

### Resource Discovery: Mostly, With Two Gaps

| Discovery Mechanism                          | OpenSensorHub           | 52North                                    |
| -------------------------------------------- | ----------------------- | ------------------------------------------ |
| Convention 1 (`ogc-cs:` prefix)              | Not used by either      | Not used by either                         |
| Convention 2 (plain rel name from root)      | ✅ Finds 6 resources    | ⚠️ No root links → finds 0                 |
| Convention 3 (items + href from collections) | ✅ Full match           | ⚠️ Finds 4/5 — misses `featuresOfInterest` |
| Conformance-based detection                  | ✅ Detects CSAPI server | ❌ Would miss this server                  |

On 52North, our discovery finds `systems`, `datastreams`, `procedures`, `deployments` from collections — but misses `featuresOfInterest` (F2) and is saved from the query-param bug (F1) only because HTML links happen to appear first.

### Verdict

Our URL builder is interoperable across both implementations. Our discovery layer has two latent bugs that should be fixed before Phase 3 response parsing work begins.

---

## 4. Recommendations

### Fix Now (Before Phase 2.4)

**1. Strip query parameters in Convention 3 parser** — One-line fix in `scanCsapiLinks()`. Change:

```js
const segment = href.replace(/\/+$/, '').split('/').pop();
```

to:

```js
const segment = href.split('?')[0].replace(/\/+$/, '').split('/').pop();
```

Low risk, high value. Prevents a real failure mode that we're currently surviving by accident (link ordering). Add a test case with `?f=application/json` in the href.

**2. Add `featuresOfInterest` as a Convention 3 alias** — `CSAPIResourceTypes` stays as `samplingFeatures` (that's the spec name and the actual endpoint path). But the Convention 3 matcher should normalize `featuresOfInterest` → `samplingFeatures` when scanning collection links. This is a 3-line addition to `scanCsapiLinks`, plus a test.

Both fixes are inside `scanCsapiLinks()` in `helpers.ts` — a function we wrote from scratch. No upstream files are touched.

### Track for Phase 3 Design (Response Parsing)

**3. Response envelope normalization** — OpenSensorHub uses `{ items: [...] }`, 52North uses `{ type: "FeatureCollection", features: [...] }`. When we build response parsing, we need a normalizer that checks for `features` first (spec-compliant), then falls back to `items`. This should be a design decision documented before Phase 3 starts.

**4. Multi-strategy server detection** — Don't rely solely on conformance classes. Our current approach (conformance check + root link scan + collection link scan) is already the right architecture. 52North proves that conformance alone would miss real CSAPI servers. Document this as an explicit design principle.

### Don't Fix (Upstream Issues)

**5. 52North's broken endpoints** (datastreams 500, controlstreams 404) — Not our problem. Don't add workarounds.

**6. 52North's missing conformance classes** — Not our problem. Our multi-strategy detection handles it.

**7. OpenSensorHub's non-standard `items` envelope** — Their deviation, but we must handle it in Phase 3 (see #3).

### Process

**8. Test against both servers going forward** — Every phase-end smoke test should hit both OpenSensorHub and 52North. Single-server testing missed both F1 and F2 across three previous smoke tests. The bugs only surfaced when we added the second implementation.

---

## 5. Upstream Impact Assessment

| Fix                        | File                                                | Who Created It?                                   | Upstream Impact                       |
| -------------------------- | --------------------------------------------------- | ------------------------------------------------- | ------------------------------------- |
| Strip query params         | `src/ogc-api/csapi/helpers.ts` → `scanCsapiLinks()` | We created this function in Phase 2.2 (Issue #34) | **Zero.** This file is 100% our code. |
| `featuresOfInterest` alias | Same function, same file                            | Same                                              | **Zero.** Same file.                  |

Both fixes are inside `scanCsapiLinks()` in `helpers.ts` — a function we wrote from scratch. We are not modifying any upstream file, upstream pattern, upstream naming, or upstream behavior. The contribution goal doc states "Zero-breaking-change integration with existing library functionality" — these changes don't touch existing library functionality at all.

The "Don't Fix" items (#5–#7) are explicitly about leaving upstream/server behaviors alone.

**Caveat:** Recommendation #3 (response envelope normalization) is a Phase 3 concern that _will_ eventually touch how we parse responses. Whether that crosses the upstream boundary depends on where response parsing lives — a design decision for later, not something proposed now.
