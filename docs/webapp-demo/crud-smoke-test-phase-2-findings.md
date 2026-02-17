# CRUD Smoke Test Phase 2 Findings — controlStream Integration

> **Date**: 2026-02-16
> **Context**: During CRUD smoke testing of Part 2 resources (datastreams, controlStreams, observations, commands) against OSH SensorHub (`http://45.55.99.236:8080/sensorhub/api`), three additional findings were identified. One is a **library bug** (F-17) and two are **server observations** (S-10, S-11). These extend the existing findings documented in [`library-findings-gap-analysis.md`](./library-findings-gap-analysis.md) and [`server-observations-gap-analysis.md`](./server-observations-gap-analysis.md).

---

## Summary

| ID | Category | Summary | Severity | Actionable? |
|---|---|---|---|---|
| **F-17** | Library bug | `buildResourceUrl` fallback produces camelCase `controlStreams` in URL path | High | Yes — [GitHub Issue #20](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/20) |
| **S-10** | Server observation | OSH controlStream CREATE requires `commandFormat` + `parametersSchema` (non-standard field names) | Medium | No — server quirk |
| **S-11** | Server observation | OSH enforces strict lowercase `controlstreams` URL path segment | Medium | No — server enforcement of spec |
| **S-12** | Server observation | OSH controlStream PUT requires `schema` but crashes (500) when CREATE-format field names are used | High | No — server Catch-22 bug |
| **S-13** | Server observation | OSH observations and commands are immutable — PUT returns 500, only CREATE/READ/DELETE supported | Medium | No — server design decision |
| **S-14** | Server observation | OSH commands use async dispatch — POST returns 202 (not 201), no Location header or persisted resource | Medium | No — server design decision |

---

## Detailed Breakdown

---

### F-17. `buildResourceUrl` Fallback Produces camelCase URL Path for `controlStreams`

| | |
|---|---|
| **Severity** | High |
| **GitHub Issue** | [#20](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/20) |
| **Status** | Issue created |
| **Affected File** | [`src/ogc-api/csapi/url_builder.ts`](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/src/ogc-api/csapi/url_builder.ts) (L199–L215) |

#### What's broken

The `CSAPIResourceTypes` array in [`model.ts`](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/src/ogc-api/csapi/model.ts#L30-L41) defines `'controlStreams'` as the internal key (camelCase). When `buildResourceUrl()` constructs a URL without a pre-populated `resourceUrls_` entry for this type, the fallback path is:

```typescript
const resourceBase = topLevelUrl
  ? topLevelUrl.replace(/\/+$/, '')
  : `${this.baseUrl}/${resourceType}`;
//                      ^^^^^^^^^^^^^^ — uses 'controlStreams' directly
```

This produces URLs like:

```
GET  /controlStreams/cs-001        ← camelCase — REJECTED by OSH
PUT  /controlStreams/cs-001        ← camelCase — REJECTED by OSH
DELETE /controlStreams/cs-001      ← camelCase — REJECTED by OSH
```

The OGC Connected Systems API spec uses lowercase `/controlstreams` in all examples and endpoint definitions.

#### Internal inconsistency

The library already uses the **correct lowercase** path in its nested sub-path methods:

```typescript
// url_builder.ts:465 — CORRECT lowercase sub-path
getSystemControlStreams(id: string, options?: QueryOptions): string {
  this.assertResourceAvailable('systems');
  return this.buildResourceUrl('systems', id, 'controlstreams', options);
  //                                           ^^^^^^^^^^^^^^ lowercase ✓
}
```

But the top-level methods pass the camelCase key directly to `buildResourceUrl`:

```typescript
// url_builder.ts:1642–1644 — passes camelCase key
getControlStreams(options?: ControlStreamQueryOptions): string {
  this.assertResourceAvailable('controlStreams');
  return this.buildResourceUrl('controlStreams', undefined, undefined, options);
  //                            ^^^^^^^^^^^^^^ camelCase — becomes URL path
}

// url_builder.ts:1664–1665
getControlStream(id: string, options?: QueryOptions): string {
  this.assertResourceAvailable('controlStreams');
  return this.buildResourceUrl('controlStreams', id, undefined, options);
  //                            ^^^^^^^^^^^^^^ camelCase — becomes URL path
}
```

The same inconsistency applies to `createControlStream()`, `updateControlStream()`, and `deleteControlStream()`.

#### Evidence from live testing

```
GET /api/osh/controlStreams/0410
→ 400 Bad Request
→ { "status": 400, "message": "Invalid resource name: 'controlStreams'" }

GET /api/osh/controlstreams/0410
→ 200 OK (after fix)
```

#### Root cause

The `CSAPIResourceTypes` constant uses `'controlStreams'` (camelCase) as the canonical key, and `buildResourceUrl()` uses this key directly in the URL path when no `resourceUrls_` map entry provides an override. This conflates internal type keys with URL path segments.

The `samplingFeatures` type has the same structural pattern (camelCase key), but the OGC spec actually does use `/samplingFeatures` (camelCase) for that resource — so it works. `controlStreams` is the only resource type where the OGC spec path (`/controlstreams`) differs from the internal key (`controlStreams`).

#### Proposed fix

Add a `RESOURCE_PATH_OVERRIDES` map that normalizes the internal type key to its correct OGC API URL path segment:

```typescript
/** Maps internal resource type keys to their OGC API URL path segments. */
const RESOURCE_PATH_OVERRIDES: Record<string, string> = {
  controlStreams: 'controlstreams',
};

function toUrlPathSegment(resourceType: string): string {
  return RESOURCE_PATH_OVERRIDES[resourceType] ?? resourceType;
}
```

Apply this in `buildResourceUrl()`:

```diff
  const resourceBase = topLevelUrl
    ? topLevelUrl.replace(/\/+$/, '')
-   : `${this.baseUrl}/${resourceType}`;
+   : `${this.baseUrl}/${toUrlPathSegment(resourceType)}`;
```

#### Demo app workaround

Applied in [`demo/src/csapi-bridge.ts`](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/demo/src/csapi-bridge.ts) at commit [`6f2d854`](https://github.com/OS4CSAPI/ogc-csapi-explorer/commit/6f2d854). The bridge module adds a `toUrlPath()` mapping that converts `controlStreams` → `controlstreams` in all fallback URL paths, and injects the lowercase path into the builder's `resourceUrls` map during initialization.

#### Impact on consumers

Any consumer using `CSAPIQueryBuilder` without pre-populating the `resourceUrls_` map with a lowercase `/controlstreams` entry will generate URLs that OSH SensorHub (and likely other strict servers) reject with 400. This affects `getControlStream()`, `getControlStreams()`, `updateControlStream()`, `deleteControlStream()`, `createControlStream()`, and `getControlStreamSchema()`.

---

### S-10. OSH SensorHub: controlStream CREATE Requires Non-Standard Field Names

| | |
|---|---|
| **Severity** | Medium |
| **Server** | OSH SensorHub |
| **Endpoint** | `POST /systems/{id}/controlstreams` |
| **Discovered In** | CRUD smoke test — controlStream CREATE step |

#### What happens

OSH returns `500 Internal Server Error` when the controlStream creation payload uses the field names from the OGC spec's schema response format. The server expects different field names in the **create request body** than what the **schema response endpoint** returns.

#### Evidence

**Payload that fails (500):**

```json
{
  "name": "Smoke Test Control Stream",
  "schema": {
    "cmdFormat": "application/swe+json",
    "recordSchema": {
      "type": "DataRecord",
      "fields": [
        { "type": "Text", "name": "action", "label": "Control Action" }
      ]
    }
  }
}
```

**Payload that succeeds (201):**

```json
{
  "name": "Smoke Test Control Stream",
  "schema": {
    "commandFormat": "application/swe+json",
    "parametersSchema": {
      "type": "DataRecord",
      "fields": [
        { "type": "Text", "name": "action", "label": "Control Action" }
      ]
    }
  }
}
```

#### Field name discrepancy

| Context | Format field | Schema field |
|---|---|---|
| **Schema GET response** (`/controlstreams/{id}/schema`) | `cmdFormat` | `commandSchema` |
| **Create request body** (OSH expects) | `commandFormat` | `parametersSchema` |
| **OGC spec examples** | `commandFormat` | `parametersSchema` |

The field names OSH expects in the create body (`commandFormat`, `parametersSchema`) actually match the OGC spec's create examples. However, the schema *response* endpoint uses different field names (`cmdFormat`, `commandSchema`), which creates confusion for consumers who inspect existing control streams and then try to replicate their structure in a create payload.

#### Impact on consumers

A consumer building a create payload by examining existing control stream schemas (a natural reverse-engineering workflow) will use the wrong field names and get 500 errors. The `500 Internal Server Error` response (not 400) provides no diagnostic message about the field name mismatch, making this especially hard to debug.

#### Workaround applied in demo app

Changed the controlStream creation payload to use `commandFormat` + `parametersSchema` at commit [`0cdeabe`](https://github.com/OS4CSAPI/ogc-csapi-explorer/commit/0cdeabe).

#### Related

- S-9 — Also involves schema format field name confusion (`obsFormat` values for datastreams)
- [#6 — CSAPI_CONTENT_TYPES helper map](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/6) — Should document create vs. response field names

---

### S-11. OSH SensorHub: Strict Lowercase `controlstreams` URL Path Enforcement

| | |
|---|---|
| **Severity** | Medium |
| **Server** | OSH SensorHub |
| **Endpoint** | All `/controlstreams/*` endpoints |
| **Discovered In** | CRUD smoke test — controlStream READ step |

#### What happens

OSH performs case-sensitive matching on URL path segments. The path `/controlStreams/{id}` (camelCase, matching the internal resource type key) is rejected with `400 Bad Request`:

```
GET /controlStreams/0410
→ 400 { "status": 400, "message": "Invalid resource name: 'controlStreams'" }

GET /controlstreams/0410
→ 200 OK
```

#### Why this is notable

Most URL path segments in the OGC Connected Systems API happen to be all-lowercase already (`systems`, `deployments`, `procedures`, `datastreams`, `observations`, `commands`). The `controlStreams` resource type is unique in having a camelCase internal name while the OGC spec path is all lowercase (`/controlstreams`).

The `samplingFeatures` type also has a camelCase name, but OSH accepts `/samplingFeatures` (camelCase) in URLs — which is consistent with the OGC spec for that resource type. Only `controlStreams` → `controlstreams` has a mismatch between name and path.

This case-sensitive behavior contrasts with many HTTP servers that perform case-insensitive path matching. Servers that enforce case sensitivity expose any client library that conflates internal type keys with URL path segments.

#### All affected operations

| Operation | camelCase URL (rejected) | Lowercase URL (accepted) |
|---|---|---|
| LIST | `GET /controlStreams` | `GET /controlstreams` |
| READ | `GET /controlStreams/{id}` | `GET /controlstreams/{id}` |
| CREATE | `POST /controlStreams` | `POST /controlstreams` |
| UPDATE | `PUT /controlStreams/{id}` | `PUT /controlstreams/{id}` |
| DELETE | `DELETE /controlStreams/{id}` | `DELETE /controlstreams/{id}` |
| SCHEMA | `GET /controlStreams/{id}/schema` | `GET /controlstreams/{id}/schema` |

#### Impact on consumers

Any client library or consumer that uses the camelCase type key `controlStreams` directly in URL paths will fail on strict servers like OSH. This is the triggering condition for F-17 above.

#### Workaround applied in demo app

The `toUrlPath()` mapping in [`demo/src/csapi-bridge.ts`](https://github.com/OS4CSAPI/ogc-csapi-explorer/blob/main/demo/src/csapi-bridge.ts) converts `controlStreams` → `controlstreams` in all URL paths, and the builder's `resourceUrls` map is initialized with the lowercase path. Commit [`6f2d854`](https://github.com/OS4CSAPI/ogc-csapi-explorer/commit/6f2d854).

#### Related

- F-17 — Library bug that exposed this server behavior
- [#14 — Improve resource discovery for non-standard link structures](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/14) — Discovery should provide correct URL paths rather than relying on type keys

---

### S-12. OSH SensorHub: controlStream PUT Requires `schema` but Crashes When CREATE-Format Field Names Are Used

| | |
|---|---|
| **Severity** | High |
| **Server** | OSH SensorHub |
| **Endpoint** | `PUT /controlstreams/{id}` |
| **Discovered In** | CRUD smoke test — controlStream UPDATE step |

#### What happens

OSH's controlStream PUT handler has a Catch-22:

| Payload | Response | Message |
|---|---|---|
| **Without** `schema` block | `400 Bad Request` | `"Invalid payload: Missing property: schema"` |
| **With** `schema` using CREATE field names (`commandFormat` + `parametersSchema`) | `500 Internal Server Error` | `"Internal server error"` |
| **With** `schema` from GET response (fetch-then-merge) | `204 No Content` | **Success** (workaround) |

The server *requires* the `schema` property on PUT but *crashes* when it receives the schema field names that the POST (create) handler accepts.

#### Evidence

**Without schema (400):**

```
PUT /controlstreams/042g
Content-Type: application/json

{ "name": "Smoke Test controlStreams (updated)", "inputName": "smoke-test-input" }

→ 400 { "status": 400, "message": "Invalid payload: Missing property: schema" }
```

**With CREATE-format schema (500):**

```
PUT /controlstreams/0420
Content-Type: application/json

{
  "name": "Smoke Test controlStreams (updated)",
  "inputName": "smoke-test-input",
  "schema": {
    "commandFormat": "application/swe+json",
    "parametersSchema": { "type": "DataRecord", "fields": [...] }
  }
}

→ 500 { "status": 500, "message": "Internal server error" }
```

#### Why it's a Catch-22

The field names OSH accepts on **CREATE** (`commandFormat` + `parametersSchema`) differ from what its **PUT handler** can parse. The PUT handler likely expects the GET response format, which may use different field names. This means a client cannot construct a valid PUT payload from scratch — it must fetch the existing resource and merge changes into the server's own representation.

#### Contrast with datastreams

The equivalent datastream PUT (`PUT /datastreams/{id}`) handles schema without issue. This bug is specific to the controlStream update code path in OSH, suggesting the two PUT handlers had different implementation approaches.

#### Workaround applied in demo app

Fetch the current control stream state via GET, then merge updated fields (name, inputName) while preserving the server's original `schema` block unchanged:

```typescript
// Fetch current state — its schema block uses the server's own format
const readResp = await apiFetch(readUrl, { method: 'GET' })
const merged = { ...readResp.data, name: 'updated name', inputName: 'smoke-test-input' }
// PUT the merged object — schema preserved from server exactly
await apiFetch(updateUrl, { method: 'PUT', body: JSON.stringify(merged) })
```

Committed at [`fc58638`](https://github.com/OS4CSAPI/ogc-csapi-explorer/commit/fc58638) (initial without-schema attempt), then refined with fetch-then-merge approach.

#### Related

- S-10 — CREATE field names (`commandFormat` + `parametersSchema`) differ from schema response field names
- S-9 — Similar obsFormat/cmdFormat field name confusion for datastreams

---

### S-13. OSH SensorHub: Observations and Commands Are Immutable — No UPDATE (PUT) Support

| | |
|---|---|
| **Severity** | Medium |
| **Server** | OSH SensorHub |
| **Endpoints** | `PUT /datastreams/{id}/observations/{id}`, `PUT /controlstreams/{id}/commands/{id}` |
| **Discovered In** | CRUD smoke test — observation UPDATE step |

#### What happens

OSH returns `500 Internal Server Error` when attempting to PUT (update) an observation or command resource. This occurs regardless of payload content — even a fetch-then-merge approach (which works for controlStreams per S-12) still produces 500.

This indicates that observations and commands are **append-only** resources on OSH: they can be created, read, and deleted, but not modified after creation.

#### Evidence

**Observation UPDATE (500):**

```
PUT /datastreams/{dsId}/observations/{obsId}
Content-Type: application/json

{ ...merged payload from GET response with updated fields... }

→ 500 { "status": 500, "message": "Internal server error" }
```

The same 500 occurs whether the payload is:
- A minimal update (just changed fields)
- A full fetch-then-merge (GET current state, merge changes, PUT back)
- The exact GET response body echoed back unchanged

#### Why this is expected

Observations and commands represent **recorded events** — sensor measurements and actuator commands that occurred at specific points in time. In many sensor network architectures, these records are treated as immutable facts:

- **Observations** are sensor readings. Modifying a historical measurement would undermine data integrity and traceability.
- **Commands** are actuator instructions. Once issued and potentially executed, modifying the record would create an inconsistent audit trail.

This design aligns with the time-series / event-sourcing philosophy common in IoT and sensor web platforms. The OGC Connected Systems API spec does define PUT for these resources, but individual server implementations may choose not to support it.

#### Contrast with parent resources

| Resource Type | CREATE | READ | UPDATE (PUT) | DELETE |
|---|---|---|---|---|
| **datastreams** | ✅ 201 | ✅ 200 | ✅ 204 | ✅ 204 |
| **controlStreams** | ✅ 201 | ✅ 200 | ✅ 204 (with fetch-merge) | ✅ 204 |
| **observations** | ✅ 201 | ✅ 200 | ❌ 500 | ✅ 204 |
| **commands** | ✅ 201 | ✅ 200 | ❌ 500 | ✅ 204 |

Parent resources (datastreams, controlStreams) support full CRUD. Child resources (observations, commands) support only CRD — Create, Read, Delete.

#### Impact on consumers

Clients implementing generic CRUD workflows need to be aware that observations and commands may not support PUT on all servers. A robust client should either:
1. Probe the server's capabilities (e.g., check Allow headers on OPTIONS) before attempting PUT
2. Handle 500/405 responses gracefully and skip UPDATE operations for these resource types
3. Document which resource types support full CRUD vs. CRD only

#### Workaround applied in demo app

Changed the smoke test step builder to use `CRD_OPS` (CREATE, READ, DELETE — 3 operations) instead of `CRUD_OPS` (5 operations including UPDATE and VERIFY) for observation and command resource types. This reduced total test steps from 40 to 34.

```typescript
const CRD_OPS: OpType[] = ['CREATE', 'READ', 'DELETE']

// Phase 2b — child resources: CRD only (no UPDATE — immutable on OSH)
for (const rt of ['observations', 'commands'] as CSAPIResourceType[]) {
  steps.push(...CRD_OPS.map(op => ({ resourceType: rt, op })))
}
```

Committed at [`12a7640`](https://github.com/OS4CSAPI/ogc-csapi-explorer/commit/12a7640).

#### Related

- S-12 — controlStream PUT also has issues (Catch-22), but has a working fetch-then-merge workaround
- S-10 — Field name confusion affects both CREATE and UPDATE paths for controlStreams

---

### S-14. OSH SensorHub: Commands Use Async Dispatch — POST Returns 202, No Persisted Resource

| | |
|---|---|
| **Severity** | Medium |
| **Server** | OSH SensorHub |
| **Endpoint** | `POST /controlstreams/{id}/commands` |
| **Discovered In** | CRUD smoke test — command CREATE step |

#### What happens

OSH handles command creation as an **asynchronous dispatch** operation rather than standard resource creation. Instead of persisting the command and returning `201 Created` with a `Location` header (as the OGC CSAPI spec defines for resource creation), OSH dispatches the command to the target actuator and waits for acknowledgment.

If no actuator is listening (or acknowledgment times out), the server returns:

```
POST /controlstreams/0450/commands
Content-Type: application/json

{ "issueTime": "2026-02-17T00:17:39.351Z", "parameters": { "active": true } }

→ 202 Accepted (after ~29.6s timeout)
→ {
    "status": 202,
    "message": "Command accepted but request timed out before command was acknowledged by receiving system"
  }
```

#### Key differences from standard resource creation

| Aspect | Standard CREATE (201) | Command Dispatch (202) |
|---|---|---|
| **Status code** | `201 Created` | `202 Accepted` |
| **Location header** | Present (URL of new resource) | Absent |
| **Response time** | Fast (~70-150ms) | Slow (~29s, waits for actuator) |
| **Resource persisted?** | Yes — GET/DELETE available | No — fire-and-forget |
| **Response body** | Resource representation or empty | Status message |

#### Why the delay

The 29.6-second response time is caused by OSH waiting for a real actuator to acknowledge receipt of the command. Since the smoke test's control stream is synthetic (no real actuator connected), the server waits until its internal timeout before returning 202.

#### Impact on consumers

Clients implementing command workflows need to handle:

1. **202 vs. 201**: The response is success (2xx) but not creation. Standard `fetch` treats `response.ok` as true for both, but the semantics differ.
2. **No resource ID**: Without a `Location` header, there's no command resource to READ, UPDATE, or DELETE. Subsequent CRUD operations will have no target.
3. **Long timeouts**: The ~30-second wait may exceed client-side timeout settings, causing false failures.
4. **No read-back**: Commands cannot be verified via GET after dispatch — the fire-and-forget model means the client only knows the command was *accepted*, not *executed*.

#### Contrast with observations

| Resource | POST Response | Persisted? | READ/DELETE? |
|---|---|---|---|
| **Observations** | `201 Created` + `Location` header | Yes | Yes |
| **Commands** | `202 Accepted` (no `Location`) | No | No |

Both are child resources of Part 2 parents, but they have fundamentally different persistence models:
- **Observations** are recorded measurements — persisted as time-series data, readable and deletable.
- **Commands** are dispatched instructions — forwarded to actuators, not stored as queryable resources.

#### OGC spec alignment

The OGC Connected Systems API Part 2 spec defines `POST /commands` as returning `201 Created` with a `Location` header for the new command resource. OSH's 202 behavior deviates from this, treating commands as transient dispatches rather than persistent resources. This is a valid server implementation choice but differs from the spec's resource-oriented model.

#### Workaround applied in demo app

Reduced command steps to CREATE-only (1 operation). Since no resource ID is returned, READ and DELETE steps are not applicable.

```typescript
const CREATE_ONLY_OPS: OpType[] = ['CREATE']  // Commands — async dispatch, 202 with no persisted ID

// Phase 2b-2: Commands — async dispatch only
for (const key of PART2_CHILD_TYPES_CREATE_ONLY) {
  steps.push(...CREATE_ONLY_OPS.map(op => ({ resourceType: key, op })))
}
```

Committed at [`c6118bb`](https://github.com/OS4CSAPI/ogc-csapi-explorer/commit/c6118bb).

#### Related

- S-13 — Observations/commands immutable (no PUT). S-14 goes further: commands aren't even persisted resources.
- S-8 — Server capability differences (OSH vs. 52North)

---

## Cross-Reference with Prior Findings

| New Finding | Related Prior Finding | Relationship |
|---|---|---|
| F-17 (URL casing) | [F-1/F-2 (#5)](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/5) | Same area: URL builder generates wrong URLs for controlStream operations |
| F-17 (URL casing) | [F-11 (#14)](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/14) | Resource discovery should provide normalized URLs |
| S-10 (field names) | S-9 (obsFormat) | Both involve create payload field name confusion |
| S-10 (field names) | [#6 (content types)](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/6) | Content type and format field documentation |
| S-11 (case sensitivity) | F-17 (URL casing) | Server behavior that triggers the library bug |
| S-12 (PUT schema Catch-22) | S-10 (CREATE field names) | Server uses different field names for POST vs. PUT |
| S-12 (PUT schema Catch-22) | S-9 (obsFormat) | Broader pattern of schema field name confusion |
| S-13 (immutable obs/cmds) | S-12 (PUT schema Catch-22) | Both involve PUT failures on Part 2 resources; different root causes |
| S-13 (immutable obs/cmds) | S-8 (OSH read-write vs. 52North read-only) | Server capability differences affecting write operations |
| S-14 (async command dispatch) | S-13 (immutable obs/cmds) | Both involve non-standard write behavior for child resources |
| S-14 (async command dispatch) | S-8 (OSH read-write vs. 52North read-only) | Server capability differences affecting write operations |

---

## Commits Implementing Workarounds

| Commit | Fix |
|---|---|
| [`0cdeabe`](https://github.com/OS4CSAPI/ogc-csapi-explorer/commit/0cdeabe) | ControlStream schema field names (`commandFormat` + `parametersSchema`) |
| [`6f2d854`](https://github.com/OS4CSAPI/ogc-csapi-explorer/commit/6f2d854) | URL path normalization (`controlStreams` → `controlstreams`) |
| [`fc58638`](https://github.com/OS4CSAPI/ogc-csapi-explorer/commit/fc58638) | ControlStream UPDATE: omit schema (initial attempt) |
| [`78fec79`](https://github.com/OS4CSAPI/ogc-csapi-explorer/commit/78fec79) | ControlStream UPDATE: fetch-then-merge with schema sub-resource |
| [`0f07c5c`](https://github.com/OS4CSAPI/ogc-csapi-explorer/commit/0f07c5c) | ControlStream UPDATE: fetch schema from `/controlstreams/{id}/schema` |
| [`406aba8`](https://github.com/OS4CSAPI/ogc-csapi-explorer/commit/406aba8) | Observation UPDATE: fetch-then-merge attempt (unsuccessful) |
| [`12a7640`](https://github.com/OS4CSAPI/ogc-csapi-explorer/commit/12a7640) | Observations/commands: CRD only — removed UPDATE steps (immutable on OSH) |
| [`b415a1e`](https://github.com/OS4CSAPI/ogc-csapi-explorer/commit/b415a1e) | Command payload: `parameters` (not `params`) per OGC CSAPI spec |
| [`c6118bb`](https://github.com/OS4CSAPI/ogc-csapi-explorer/commit/c6118bb) | Commands: CREATE-only — async dispatch (202), no persisted resource |
