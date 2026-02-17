# Commands as Nested Resources: OSH Server Design Choice Analysis

## 1. The Observation

When clicking **Commands** in the Explorer sidebar, OSH SensorHub returns a `400 Bad Request` with `"Invalid resource name: 'commands'"`. This is the **only** resource type out of the nine CSAPI types that fails at the top level. All other eight — systems, deployments, procedures, sampling features, properties, datastreams, observations, and control streams — respond with `200 OK`.

Yet commands do exist on this server. There are **273 commands** distributed across 3 of the 18 control streams, including drone flight control commands with latitude/longitude/altitude parameters, completion statuses, and timestamps. They are only accessible via nested URLs like `/controlstreams/{id}/commands`.

This raises questions about the server's design choice, the spec's requirements, and the practical impact on users and client applications.

---

## 2. What the Server Advertises

### Landing Page Links

The OSH landing page (`/api/`) advertises these resource links:

| rel | Endpoint |
|---|---|
| `systems` | `/systems` |
| `deployments` | `/deployments` |
| `procedures` | `/procedures` |
| `samplingFeatures` | `/samplingFeatures` |
| `datastreams` | `/datastreams` |
| `observations` | `/observations` |

Notably absent: **`controlstreams`**, **`commands`**, and **`properties`** — yet `/controlstreams` and `/properties` both return `200 OK` when hit directly. The landing page under-reports what the server actually supports.

### Conformance Classes

OSH declares 33 conformance classes. The relevant Part 2 classes are:

- `ogcapi-connectedsystems-2/1.0/conf/datastream` — governs datastreams **and** observations
- `ogcapi-connectedsystems-2/1.0/conf/controlstream` — governs control streams **and** commands

There are no separate `observation` or `command` conformance classes. Observations and commands are **sub-resources** of their parent stream types in the spec's conformance model. Claiming the `controlstream` conformance class implies support for commands as nested resources — but it says nothing about top-level `/commands` access.

---

## 3. What the Spec Says

### The Nesting Model

OGC API — Connected Systems Part 2 defines a hierarchical resource model:

```
System
├── Datastreams
│   └── Observations          ← nested under parent datastream
└── Control Streams
    └── Commands              ← nested under parent control stream
```

The **normative** access pattern for commands is:

```
GET /controlstreams/{csId}/commands
GET /controlstreams/{csId}/commands/{cmdId}
POST /controlstreams/{csId}/commands
```

### Top-Level Shortcuts

The spec also defines **optional** top-level collection endpoints as convenience shortcuts:

```
GET /observations             ← cross-cutting view across all datastreams
GET /commands                 ← cross-cutting view across all control streams
```

These top-level endpoints are not required for conformance. They exist as a convenience for clients that need to search across parent boundaries — for example, "find all commands issued in the last hour regardless of which control stream they belong to."

### The Asymmetry on OSH

OSH implements the top-level shortcut for `/observations` but **not** for `/commands`:

| Resource | Nested | Top-Level | Landing Page |
|---|---|---|---|
| Observations | `/datastreams/{id}/observations` ✅ | `/observations` ✅ | Advertised ✅ |
| Commands | `/controlstreams/{id}/commands` ✅ | `/commands` ❌ (400) | Not advertised |

Both are architecturally equivalent in the spec — commands are to control streams what observations are to datastreams. The asymmetry is an OSH implementation choice, not a spec requirement.

---

## 4. Could They Have Done It?

**Yes.** The `/observations` endpoint already demonstrates that OSH has the architecture to aggregate nested resources at the top level. Implementing `/commands` would follow the same pattern: iterate across control streams, merge their command collections, apply query parameters (filtering, pagination), and return a unified response.

### Why They Probably Didn't

Several factors may explain the omission:

1. **Lower demand**: Observations are the primary read-heavy resource — monitoring dashboards, analytics pipelines, and map visualizations all query observations constantly. Commands are write-heavy (issued, then occasionally reviewed) and much less frequently queried in bulk.

2. **Development priority**: The OSH team may have prioritized the observation path because it serves the majority of sensor web use cases. Command review is a less common workflow.

3. **Data volume asymmetry**: This server has ~1000+ observations but only 273 commands. The cost-benefit of a top-level aggregation endpoint is lower for commands.

4. **Spec maturity**: The CSAPI Part 2 spec was published relatively recently. Implementations may roll out features incrementally, with observations first and commands later.

---

## 5. The User Impact

### What Users Can't Do Today

Without a top-level `/commands` endpoint, users of the Explorer (or any client) cannot:

1. **Search across all commands at once** — e.g., "show me all commands issued today" requires iterating through every control stream manually.

2. **Apply cross-cutting filters** — temporal filters, status filters (`currentStatus=COMPLETED`), or free-text search across all commands are impossible through a single query.

3. **Review command history holistically** — an operator wanting to audit "what commands were sent to any system in the last 24 hours?" must know which control streams exist and query each one individually.

4. **Discover commands without knowing the hierarchy** — a new user exploring the API must first find systems, then their control streams, then query each control stream's commands. There's no single entry point.

### What Users Can Do

Commands are fully accessible via the nested path. The workflow is:

1. Browse control streams at `/controlstreams` (works at top level, returns 18)
2. Pick a control stream (e.g., "FCU Field Drone CubePilot - Location Control")
3. Follow its `commands` link to `/controlstreams/{id}/commands`
4. Browse, filter, and paginate commands within that stream

This works but requires knowing the parent-child structure and navigating it manually.

### Concrete Example: Drone Command Review

On this OSH server, control stream `0o10` ("FCU Field Drone CubePilot - Location Control") contains **263 commands** — drone flight commands with location vectors, hover parameters, and completion statuses:

```json
{
  "id": "0o1qr7kupc33cgmqj0",
  "controlstream@id": "0o10",
  "issueTime": "2026-01-14T12:42:21.910351Z",
  "sender": "urn:osh:process:datasink:commandstream#drone",
  "currentStatus": "COMPLETED",
  "parameters": {
    "locationVectorLLA": {
      "Latitude": 24.1806,
      "Longitude": 120.6492,
      "AltitudeAGL": 105.0
    },
    "returnToStart": false,
    "hoverSeconds": 0
  }
}
```

An operator wanting to review all drone commands sent during a specific time window must know to look at control stream `0o10` specifically. If there were multiple drone systems with different control streams, the operator would need to query each one separately.

With a top-level `/commands` endpoint, the same review would be a single query:
```
GET /commands?issueTime=2026-01-14T12:00:00Z/2026-01-14T14:00:00Z
```

---

## 6. Semantic Pros and Cons of the Design Choice

### Arguments For Nested-Only Commands

| Argument | Explanation |
|---|---|
| **Cleaner resource semantics** | Commands inherently belong to a control stream. Top-level access obscures this relationship. |
| **Simpler server implementation** | No need to build a cross-stream aggregation layer with filtering, pagination, and access control. |
| **Fewer ambiguous queries** | Querying `/commands` without specifying a control stream could return a confusing mix of commands from unrelated systems (drone waypoints mixed with HVAC setpoints). |
| **Security scoping** | Access control is naturally scoped to the control stream. A top-level endpoint would need to enforce per-stream permissions across aggregated results. |
| **Consistent with write path** | You POST commands to a specific control stream. Making reads also stream-scoped keeps the mental model consistent. |

### Arguments For Top-Level Commands

| Argument | Explanation |
|---|---|
| **Discoverability** | New users expect all 9 resource types to be browseable from the top level. A 400 error is confusing. |
| **Auditability** | Reviewing command history across all systems is a legitimate operational use case (compliance, incident review). |
| **Consistency with observations** | If `/observations` exists at the top level, users reasonably expect `/commands` to behave the same way. The asymmetry is surprising. |
| **Client simplicity** | Client libraries and UIs can treat all resource types uniformly. Special-casing commands adds complexity. |
| **Cross-system correlation** | "What commands were issued during this anomaly window?" requires cross-stream temporal queries. |
| **OGC API design philosophy** | The OGC API family favors flat, browseable resource collections. Top-level endpoints align with this philosophy. |

### The Consistency Problem

The strongest argument for top-level `/commands` is **consistency**. OSH treats observations and commands as architecturally equivalent in every other way:

- Both are nested under a parent stream (datastream/control stream)
- Both have temporal properties (`phenomenonTime`/`resultTime` vs `issueTime`/`executionTime`)
- Both support filtering by time, status, and other properties
- Both parent streams are available at the top level

Yet observations get top-level access and commands don't. This creates an inconsistency that surprises users and requires special handling in client code.

---

## 7. How Our Demo Handles This

### Before (Raw Error)

The Explorer showed a red error banner with the raw HTTP response:
```
400 Bad Request: {"status":400,"message":"Invalid resource name: 'commands'"}
```

This was confusing — it looked like a bug in the app rather than a server limitation.

### After (Friendly Warning)

The Explorer now shows a yellow warning (commit `f5e56bc`):
```
This server does not support listing commands as a top-level resource.
Commands are nested under individual control streams. Try viewing a
control stream's detail page to browse its commands.
(Server returned: 400 Bad Request)
```

The severity is `warn` (yellow) rather than `error` (red) to communicate that this is a server capability limitation, not a failure.

### Architecture Note

The client library's `CSAPIQueryBuilder` builds valid URLs for all 9 resource types including `/commands`. The 400 comes from OSH, not from the library. The library correctly models the spec; the server partially implements it.

---

## 8. Recommendations

### For the OSH Server Team

1. **Implement `/commands` at the top level** — it's architecturally identical to the already-implemented `/observations` shortcut. The spec provides for it, and the server already has the aggregation pattern from observations.

2. **Advertise all supported endpoints in the landing page** — `/controlstreams` and `/properties` work but aren't listed in the landing page links. Clients relying on HATEOAS discovery (which is the OGC API design philosophy) won't find them.

3. **If `/commands` won't be implemented**, return `404 Not Found` instead of `400 Bad Request`. A 404 means "this endpoint doesn't exist" (accurate), while 400 means "your request was malformed" (misleading — the request was valid per the spec).

### For Client Library Developers

1. **Don't assume all 9 resource types are available at the top level.** Check the server's landing page links and conformance classes to determine availability.

2. **Provide a fallback for nested-only resources.** If `/commands` fails, the library could automatically fall back to iterating `/controlstreams` and aggregating their commands — though this is expensive and doesn't support server-side filtering.

3. **Surface the distinction to users.** UIs should indicate when a resource type is only available as a nested sub-resource, with guidance on how to access it.

### For the OGC Specification

1. **Clarify whether top-level shortcuts are normative or optional.** The current spec is ambiguous about whether claiming `controlstream` conformance implies top-level `/commands` access.

2. **Consider a discovery mechanism.** The landing page links partially serve this purpose, but a more explicit capability declaration (e.g., a capabilities document listing which resource types support top-level collection access) would help clients negotiate gracefully.

---

## 9. Data Summary

| Metric | Value |
|---|---|
| Total control streams | 18 |
| Control streams with commands | 3 |
| Total commands (nested) | 273 |
| Commands at top level | 0 (400 error) |
| Largest command collection | 263 (drone location control) |
| Conformance class | `controlstream` (implies command sub-resource support) |
| Landing page advertises commands | No |
| Landing page advertises controlstreams | No |
