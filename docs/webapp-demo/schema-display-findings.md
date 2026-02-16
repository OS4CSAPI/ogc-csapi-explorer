# Schema Display — Implementation Findings

> **Date**: 2026-02-16
> **Context**: While implementing GitHub Issue [#2 — feat: SWE Common schema display for datastreams](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/2), we encountered three new findings. Two are actionable library improvements; one is a server-side observation. This document follows the same structure as the [Library Findings Gap Analysis](./library-findings-gap-analysis.md).

---

## Summary

| Finding | Summary | Category | Has GitHub Issue? |
|---|---|---|---|
| **F-13** | `getDataStreamSchema()` / `getControlStreamSchema()` JSDoc conflates `f` (response format) with `obsFormat`/`cmdFormat` (schema-specific parameters) | Library — Bug / Documentation | [#16](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/16) |
| **F-14** | No library utility to parse the schema endpoint response wrapper (`{ obsFormat, resultSchema }`) | Library — Enhancement | [#17](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/17) |
| **S-8** | OSH SensorHub returns `Content-Type: auto` on schema responses | Server observation | N/A (not library-actionable) |

---

## Detailed Breakdown

---

### F-13. Schema Method JSDoc Conflates `f` with `obsFormat` / `cmdFormat`

| | |
|---|---|
| **Severity** | Medium |
| **Type** | Bug / Documentation |
| **GitHub Issue** | [#16](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/16) |
| **Affected Files** | [`src/ogc-api/csapi/url_builder.ts`](https://github.com/Sam-Bolling/ogc-client-CSAPI_2/blob/main/src/ogc-api/csapi/url_builder.ts) (L1303–1325, L1732–1757), [`url_builder.spec.ts`](https://github.com/Sam-Bolling/ogc-client-CSAPI_2/blob/main/src/ogc-api/csapi/url_builder.spec.ts) (L1644–1665, L2123–2144) |

#### Problem

The `getDataStreamSchema()` JSDoc at [`url_builder.ts` L1305](https://github.com/Sam-Bolling/ogc-client-CSAPI_2/blob/main/src/ogc-api/csapi/url_builder.ts#L1305) states:

> The `obsFormat` query parameter is **required** per Part 2, Req 11. Omitting it causes the server to return 400 Bad Request.

But the example and `@param` descriptions then tell the consumer to pass `{ f: 'application/swe+json' }`, which appends `?f=application%2Fswe%2Bjson` to the URL. These are two different query parameters:

| Parameter | Purpose | OGC Spec Reference |
|---|---|---|
| `f` | OGC API common response format negotiation (JSON vs XML vs HTML) | OGC API - Common |
| `obsFormat` | Part 2 §Req 11: specifies which observation encoding the schema describes | [OGC 23-002 §Req 11](https://docs.ogc.org/is/23-002/23-002.html#req_datastream_schema) |
| `cmdFormat` | Part 2 §Req 25: specifies which command encoding the schema describes | [OGC 23-002 §Req 25](https://docs.ogc.org/is/23-002/23-002.html#req_controlstream_schema) |

The same issue affects `getControlStreamSchema()` at [`url_builder.ts` L1735-1738](https://github.com/Sam-Bolling/ogc-client-CSAPI_2/blob/main/src/ogc-api/csapi/url_builder.ts#L1735-L1738).

#### Real-world impact

When we passed `{ f: 'application/swe+json' }` to `getDataStreamSchema()` in the demo app, the OSH SensorHub server returned:

```
400 Bad Request: { "status": 400, "message": "Unsupported format: application/swe+json" }
```

The server interpreted `f` as a response format parameter and rejected `application/swe+json` as an unsupported response format. Without the parameter, the schema loaded correctly — the server defaults to SWE JSON.

#### Root cause

The `buildQueryString()` method in `url_builder.ts` treats all options keys generically — it serializes `{ f: 'application/swe+json' }` as `?f=application%2Fswe%2Bjson`. There is no mapping from the generic `f` key to the schema-specific `obsFormat` or `cmdFormat` parameter names that the spec requires.

The test at [`url_builder.spec.ts` L1656](https://github.com/Sam-Bolling/ogc-client-CSAPI_2/blob/main/src/ogc-api/csapi/url_builder.spec.ts#L1656) is named "returns correct URL with obsFormat parameter" but actually tests `f`:

```typescript
it('returns correct URL with obsFormat parameter', () => {
  const url = makeDsBuilder().getDataStreamSchema('ds-001', { f: 'application/swe+json' });
  expect(url).toBe('https://example.com/collections/iot/datastreams/ds-001/schema?f=application%2Fswe%2Bjson');
});
```

---

### F-14. No Library Utility to Parse Schema Endpoint Response

| | |
|---|---|
| **Severity** | Medium |
| **Type** | Enhancement |
| **GitHub Issue** | [#17](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/17) |
| **Affected Module** | `src/ogc-api/csapi/formats/swecommon/` — no schema response parser exists |

#### Problem

The library provides excellent SWE Common parsing via `parseSWEComponent()`, but the schema endpoint (`/datastreams/{id}/schema`) does **not** return a raw SWE component. It returns a wrapper:

```json
{
  "obsFormat": "application/om+json",
  "resultSchema": {
    "type": "DataRecord",
    "name": "gps_data",
    "fields": [ ... ]
  }
}
```

Consumers must know to extract `.resultSchema` before calling `parseSWEComponent()`. There is no `parseSchemaResponse()` helper in the library, no `SchemaResponse` type definition, and no documentation mentioning this wrapper structure.

#### Real-world impact

In the demo app, we initially passed the entire response to `parseSWEComponent()`, which threw `SweCommonParseError` because the wrapper object doesn't have a `type` field. We had to add manual extraction logic (`data?.resultSchema ?? data`) in the demo component.

The same issue applies to control stream schemas, which return `{ cmdFormat, commandSchema }`.

#### What the library should provide

1. A `SchemaResponse` interface (for both datastream and control stream variants)
2. A `parseSchemaResponse()` function that extracts and parses the SWE component
3. Documentation noting the wrapper structure

---

### S-8. OSH SensorHub Returns `Content-Type: auto` on Schema Endpoint

| | |
|---|---|
| **Severity** | Low |
| **Type** | Server observation (not library-actionable) |
| **Server** | OSH SensorHub at `http://45.55.99.236:8080/sensorhub/api` |

#### Observation

The OSH server returns `Content-Type: auto` (a non-standard value) for schema endpoint responses. Standard-compliant values would be `application/json`, `application/swe+json`, or similar.

#### Impact

HTTP clients that check `Content-Type` to decide whether to parse as JSON (like the demo app's `apiFetch()`) fall through to text handling. The demo app works around this by attempting `JSON.parse()` on string responses in the `SweSchemaDisplay` component.

This is consistent with other OSH server quirks documented in **S-1** through **S-7** in the [upstream findings document](../upstream-findings.md).

---

## Relationship to Existing Issues

| New Finding | Related Existing Issue? | Notes |
|---|---|---|
| **F-13** | No — new discovery | JSDoc was written during Phase 2.8 but never tested against a live server's schema endpoint |
| **F-14** | Partially related to [#6 (Content-Type helper)](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/6) | Both address gaps where the library doesn't fully handle server response structure |
| **S-8** | Extends S-1–S-7 pattern | OSH server has several non-standard HTTP behaviors already documented |

---

## Actionability Summary

| Finding | Has GitHub Issue? | Actionable? | Effort | Priority |
|---|---|---|---|---|
| **F-13** | [#16](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/16) | Yes — JSDoc fix + potential API change | Low–Medium | **2** (High) |
| **F-14** | [#17](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/17) | Yes — new parser utility | Low | **3** (Medium) |
| **S-8** | N/A | No — server-side only | N/A | N/A |
