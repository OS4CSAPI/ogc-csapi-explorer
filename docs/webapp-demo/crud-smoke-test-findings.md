# CRUD Smoke Test Findings — Additional Library Issues

> **Date**: 2026-02-16
> **Context**: During CRUD smoke test development and live testing against OSH SensorHub (`http://45.55.99.236:8080/sensorhub/api`), two new library-level findings were identified that were **not** previously captured in the [library findings gap analysis](./library-findings-gap-analysis.md) (F-1 through F-12) or existing GitHub issues #5–#17.

---

## Summary

| ID | Finding | Severity | GitHub Issue | Affected Area |
|---|---|---|---|---|
| **F-15** | `apiFetch()` / library crashes on 201 Created with empty response body | High | [#18](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/18) | HTTP response handling |
| **F-16** | PUT/UPDATE requires `uid` field — server returns 400 "Missing feature UID" | Medium | [#19](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/19) | CRUD write operations |

> **Numbering note**: F-13 and F-14 were assigned to findings documented in issues [#16](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/16) and [#17](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/17). These new findings continue from F-15.

---

## Detailed Breakdown of Each Finding

### F-15. Library Crashes on 201 Created with Empty Response Body

| | |
|---|---|
| **Severity** | High |
| **GitHub Issue** | [#18](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/18) |
| **Status** | Issue created; workaround applied in demo app |
| **Affected Area** | Any HTTP response handling layer (library or consumer `fetch()` wrapper) |

#### What happens

When a POST request creates a resource successfully, OGC API servers return HTTP `201 Created` with:
- A `Location` header containing the URL of the new resource (e.g., `Location: /sensorhub/api/systems/045g`)
- An **empty response body** (content-length: 0)

The standard JavaScript `response.json()` method throws when called on an empty body:

```
Failed to execute 'json' on 'Response': Unexpected end of JSON input
```

This crashes the CRUD operation even though it succeeded. The resource is created on the server, but the client sees a failure.

#### How it was discovered

During live CRUD smoke testing against OSH SensorHub. The smoke test executed `POST /systems` and received `201 Created` with a valid `Location` header but no body. The demo app's `apiFetch()` wrapper attempted to parse the empty body as JSON and threw.

#### Evidence

Screenshot from smoke test showing:
- **Request**: `POST /systems` with valid GeoJSON Feature payload
- **Response status**: `0 Network Error` (the error thrown before status could be captured)
- **Error**: `Failed to execute 'json' on 'Response': Unexpected end of JSON input`

The resource was actually created successfully on the server — confirmed by manual `GET /systems/{id}` and subsequent `DELETE` cleanup.

#### Why it's critical

This affects **every POST operation** against OSH SensorHub. All four Part 1 resource types (systems, procedures, deployments, samplingFeatures) return empty-body 201 responses. Any library consumer performing create operations will hit this crash.

#### Root cause

The response handling code only had an empty-body guard for `204 No Content`:

```typescript
// Only handles 204
if (response.status === 204) {
  return { ok: true, status: 204, data: null };
}

// Falls through to JSON.parse for 201
const contentType = response.headers.get('content-type') || '';
if (contentType.includes('json')) {
  data = await response.json();  // ← CRASHES on empty body
}
```

#### Workaround applied in demo app

Fixed `demo/src/api.ts` to check for empty body regardless of status code:

```typescript
// Handle responses with no body (204, 201 with empty body, etc.)
const contentLength = response.headers.get('content-length');
if (response.status === 204 || contentLength === '0') {
  return { ok: true, status: response.status, data: null, headers: responseHeaders };
}

// Also guard against empty text before JSON.parse
const text = await response.text();
if (!text || !text.trim()) {
  return { ok: true, status: response.status, data: null, headers: responseHeaders };
}
data = JSON.parse(text);
```

Committed at [`f3dd4ee`](https://github.com/OS4CSAPI/ogc-csapi-explorer/commit/f3dd4ee).

#### Recommendation for library

Any internal HTTP helper or documented fetch pattern in the ogc-client library should:
1. Check `content-length: 0` before attempting body parsing
2. Use `response.text()` + guarded `JSON.parse()` instead of `response.json()` for resilience
3. For 201 responses, extract the resource ID from the `Location` header (see also [#15 — parseLocationHeader()](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/15))

#### Related issues

- [#15 — Add parseLocationHeader() utility](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/15) — Complementary: parses the Location header that 201 responses provide *instead of* a body

---

### F-16. PUT/UPDATE Requires `uid` Field — Server Returns 400 "Missing feature UID"

| | |
|---|---|
| **Severity** | Medium |
| **GitHub Issue** | [#19](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/19) |
| **Status** | Issue created; workaround applied in demo app |
| **Affected Area** | CRUD update operations for Part 1 resources |

#### What happens

When updating a Part 1 resource (system, procedure, deployment, samplingFeature) via `PUT /systems/{id}`, OSH SensorHub requires the `uid` field in the request body's `properties` object. If `uid` is omitted, the server returns:

```json
{
  "status": 400,
  "message": "Invalid payload: Missing feature UID"
}
```

This is not immediately obvious because:
1. The `uid` is a **server-assigned unique identifier** generated during CREATE
2. The OGC spec treats `uid` as an immutable identifier — it shouldn't need to be re-sent on UPDATE
3. The CREATE response returns the `uid` only indirectly (it's in the original payload sent by the client, and the `Location` header returns the server's internal ID, not the UID)

#### How it was discovered

During live CRUD smoke testing against OSH SensorHub. The smoke test:
1. Created a system with `uid: "urn:csapi-explorer:smoke-test:systems:1771280090991"` → `201 Created`
2. Read it back → `200 OK`
3. Sent UPDATE with the same payload but without `uid` (since `uid` was intentionally omitted for updates to avoid accidentally changing it) → `400 "Missing feature UID"`

#### Evidence

Screenshot from smoke test showing:
- **Request**: `PUT /systems/0460` with GeoJSON Feature payload (no `uid` in properties)
- **Response**: `400 Bad Request` — `"Invalid payload: Missing feature UID"`

#### Why it matters

A library consumer following a natural pattern — "fetch resource, modify some fields, PUT it back" — may strip or omit `uid` thinking it's immutable metadata. The server silently rejects the update. The library's CRUD helpers or documentation should make clear that **all** properties, including `uid`, must be preserved on updates.

#### Workaround applied in demo app

The smoke test now stores the `uid` from the CREATE payload and includes it in all subsequent UPDATE payloads:

```typescript
const createdUids = reactive<Record<string, string>>({})

// On CREATE: store the uid
if (payload?.properties?.uid) createdUids[step.resourceType] = payload.properties.uid

// On UPDATE: reuse it
const uid = phase === 'create'
  ? `urn:csapi-explorer:smoke-test:${type}:${Date.now()}`
  : createdUids[type]  // Reuse original UID — OSH requires it
```

Committed at [`d671f96`](https://github.com/OS4CSAPI/ogc-csapi-explorer/commit/d671f96).

#### Recommendation for library

1. **Document the requirement**: Any CRUD update helper or example code should explicitly note that `uid` must be preserved in PUT payloads
2. **Consider a "merge update" pattern**: A library-level update helper could fetch the current resource, merge caller-provided changes, and ensure required fields like `uid` are preserved
3. **Add to Content-Type / payload guidance**: This pairs with [#6 — CSAPI_CONTENT_TYPES helper](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/6) — payload structure requirements should be documented alongside content-type requirements

#### Related issues

- [#6 — Add CSAPI_CONTENT_TYPES helper map](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/6) — Content-Type and payload structure documentation
- [#5 — Fix createDataStream() URL generation + add missing nested create methods](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/5) — Related CRUD write operation improvements

---

## Server-Side Observation

### S-8. OSH SensorHub: Rejects `Accept: application/geo+json` on POST

During smoke testing, POST requests with `Accept: application/geo+json` header caused network-level failures on OSH SensorHub. The same request with `Accept: application/json` (or no explicit Accept header) succeeded with `201 Created`.

This is consistent with the server returning an empty body on 201 — the `Accept` header is irrelevant when there's no response body, but the server may be validating it against its supported response formats before processing the request.

**Impact on library**: Issue [#9 — Default to Accept: application/geo+json for Part 1 resource requests](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/9) should note that this default should apply to **GET requests only**, not POST/PUT/DELETE operations where the response is typically empty or status-only.

---

## Relationship to Existing Findings

These findings extend the original [library findings gap analysis](./library-findings-gap-analysis.md) and the [conformance bypass architecture notes](./conformance-bypass-architecture-notes.md):

| Document | Findings | Focus |
|---|---|---|
| [Library findings gap analysis](./library-findings-gap-analysis.md) | F-1 through F-12, S-1 through S-7 | Initial integration testing |
| [Conformance bypass architecture notes](./conformance-bypass-architecture-notes.md) | Architectural finding | Demo app bypasses OgcApiEndpoint entirely |
| **This document** | F-15, F-16, S-8 | Live CRUD smoke testing |

All findings are tracked in the [GitHub issues list](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues).
