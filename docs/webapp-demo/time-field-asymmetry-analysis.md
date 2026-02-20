# Time Field Asymmetry Analysis — Part 2 Resource Types

> **Date**: 2026-02-20
> **Context**: During the implementation of [Issue #31 — Render observation results as structured tables](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/31) and the subsequent fix for the observation time display bug (commit `26546a1`), we discovered a type-level asymmetry in how time fields are represented across the six CSAPI Part 2 resource types. This document records the investigation, root cause, OGC spec rationale, and final recommendation.

---

## Summary

| Aspect | Finding |
|---|---|
| **Trigger** | Observation detail view displayed `(ongoing / now)` instead of actual ISO timestamps |
| **Root cause** | Demo app template assumed all Part 2 `phenomenonTime`/`resultTime` fields are `TimeInterval` objects |
| **Library behaviour** | Correct — the asymmetry is spec-intentional, not a bug |
| **Demo fix** | Commit [`26546a1`](https://github.com/OS4CSAPI/ogc-csapi-explorer/commit/26546a1) — runtime type check (`string` vs `TimeInterval`) |
| **Upstream action needed** | None |

---

## 1. Background

The CSAPI Part 2 specification ([OGC 23-002](https://docs.ogc.org/is/23-002/23-002.html)) defines six resource types with time-related fields. These time fields fall into two semantic categories:

- **Aggregate time extents** — a `[start, end]` pair summarizing the temporal range across all child resources in a collection. Represented in JSON as a two-element ISO 8601 string array.
- **Individual time instants** — a single ISO 8601 timestamp marking when a specific event occurred. Represented in JSON as a bare string.

The library correctly models these as different TypeScript types:

- `TimeInterval` — an object with `start: Date` and optional `end?: Date`, parsed from the two-element array via `parseValidTime()`.
- `string` — a raw ISO 8601 instant, passed through without parsing.

---

## 2. Complete Type Mapping

The table below maps every time field across all six Part 2 types, showing the OGC spec semantics, the library's TypeScript type, and the parser behaviour.

| Resource Type | Field | OGC Spec Semantics | TypeScript Type | Parser Behaviour |
|---|---|---|---|---|
| **Datastream** | `phenomenonTime` | Aggregate extent of all observation phenomenon times | `TimeInterval \| null` | `parseValidTime()` → Date objects |
| **Datastream** | `resultTime` | Aggregate extent of all observation result times | `TimeInterval \| null` | `parseValidTime()` → Date objects |
| **ControlStream** | `issueTime` | Aggregate extent of all command issue times | `TimeInterval \| null` | `parseValidTime()` → Date objects |
| **ControlStream** | `executionTime` | Aggregate extent of all command execution times | `TimeInterval \| null` | `parseValidTime()` → Date objects |
| **Observation** | `phenomenonTime` | Instant when phenomenon occurred | `string` (optional) | String pass-through |
| **Observation** | `resultTime` | Instant when result was produced | `string` (required) | String pass-through |
| **Command** | `issueTime` | Instant when command was issued | `string` (required) | String pass-through |
| **Command** | `executionTime` | Period spanning command execution | `TimeInterval` (optional) | `parseValidTime()` → Date objects |
| **CommandStatus** | `reportTime` | Instant when status was reported | `string` (required) | String pass-through |
| **CommandStatus** | `executionTime` | Period spanning command execution | `TimeInterval` (optional) | `parseValidTime()` → Date objects |

### Key observations

1. **Datastream** and **ControlStream** are collection-level metadata — all their time fields are aggregate extents (`TimeInterval`).
2. **Observation**, **Command**, and **CommandStatus** are individual events — their primary time fields are single instants (`string`).
3. **Command.executionTime** and **CommandStatus.executionTime** are the exceptions: even on individual resources, execution can span a time *range* (scheduled start → completion), so `TimeInterval` is correct.
4. There is no case where the same field name has different types on the same interface. The asymmetry is strictly *between* interfaces, reflecting their different semantic roles.

---

## 3. The Bug

### Symptom

In the observation detail view, the `phenomenonTime` and `resultTime` fields displayed `(ongoing / now)` instead of the actual ISO timestamps (e.g., `2026-02-19T14:22:03.12Z`).

### Root cause

The `ParsedResourceView.vue` template contained:

```html
<span>{{ formatDate(parsedPart2.phenomenonTime.start) }}</span>
```

This assumed `phenomenonTime` was always a `TimeInterval` object with a `.start` property. For `Observation` resources, `phenomenonTime` is a plain `string`. Accessing `.start` on a string returns `undefined`, and `formatDate(undefined)` produces the fallback text `"(ongoing / now)"`.

### Fix (commit [`26546a1`](https://github.com/OS4CSAPI/ogc-csapi-explorer/commit/26546a1))

Added runtime type detection at the render site:

```html
<!-- Observation: phenomenonTime is a plain ISO string -->
<template v-if="typeof parsedPart2.phenomenonTime === 'string'">
  <span>{{ parsedPart2.phenomenonTime }}</span>
</template>
<!-- Datastream: phenomenonTime is a TimeInterval object -->
<template v-else-if="parsedPart2.phenomenonTime?.start">
  <span>{{ formatDate(parsedPart2.phenomenonTime.start) }} → ...</span>
</template>
```

The same pattern was applied to `resultTime`.

---

## 4. Is This an Upstream Library Gap?

### Comparison with cross-reference fields

During the #31 investigation, we also noted that `Observation` does not expose the `datastream@id` cross-reference field on its interface, while the raw JSON response contains it. The `parseObservation()` JSDoc explicitly states:

> *Cross-reference fields (`datastream@id`, `samplingFeature@id`, `foi@id`) present in the raw JSON are intentionally ignored — they are not part of the `Observation` interface.*

Similarly, `parseCommand()` drops `controlstream@id`, and `parseCommandStatus()` drops `command@id`. This is a consistent design choice — cross-reference IDs are available via link relations, and the parsers strip them to keep interfaces clean.

### Verdict: No upstream issue

The time field asymmetry is **spec-correct and intentional**:

| Argument | Details |
|---|---|
| **Spec alignment** | OGC 23-002 §7.5 (Observation) defines `phenomenonTime` and `resultTime` as single instants. §7.3 (Datastream) defines them as temporal extents. The library faithfully models both. |
| **Type safety** | The `string` vs `TimeInterval` distinction prevents consumers from accidentally calling `.start` on an instant — exactly the bug we hit in the demo, which is a *consumer* error, not a library error. |
| **Consistency** | `Command.issueTime: string` and `CommandStatus.reportTime: string` follow the same instant-as-string pattern. `Command.executionTime: TimeInterval` and `CommandStatus.executionTime: TimeInterval` follow the same range-as-interval pattern. The pattern is consistent within its semantic category. |
| **Cross-reference fields** | Also intentionally omitted — a separate, already-documented design decision. |

---

## 5. Recommendations

### For the demo app

| # | Recommendation | Status |
|---|---|---|
| 1 | **Runtime type checks for all time fields** — any template rendering Part 2 time fields should check `typeof field === 'string'` before accessing `.start`/`.end`. | ✅ Done (commit `26546a1`) |
| 2 | **Consider a helper function** — a `formatTimeField(value: string \| TimeInterval \| null \| undefined): string` utility could centralize the logic and avoid repeating `typeof` checks in templates. | Deferred — low priority, current four-block pattern is clear enough. |
| 3 | **Cross-reference field extraction** — `ParsedResourceView.vue` already extracts `datastream@id` from the raw resource for `ObservationResultTable`. If more cross-references are needed in the future, consider a lightweight wrapper type. | Deferred — no current need beyond #31. |

### For the upstream library

| # | Recommendation | Status |
|---|---|---|
| 1 | **No changes needed** — the time field types correctly model the OGC spec semantics. | N/A |
| 2 | **No new issue to file** — the asymmetry is intentional, documented in JSDoc, and behaviourally correct. | N/A |
| 3 | **Documentation note** — the `parseObservation()` JSDoc already contains the "time field asymmetry" note. `parseCommand()` and `parseCommandStatus()` have equivalent notes. These are sufficient for library consumers. | Already documented |

---

## 6. Related Issues and Commits

| Reference | Description |
|---|---|
| [Issue #31](https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/31) | Render observation results as structured tables (triggered this investigation) |
| Commit [`0f5b315`](https://github.com/OS4CSAPI/ogc-csapi-explorer/commit/0f5b315) | Implemented `ObservationResultTable.vue` and integrated into `ParsedResourceView.vue` |
| Commit [`26546a1`](https://github.com/OS4CSAPI/ogc-csapi-explorer/commit/26546a1) | Fixed observation time display bug with runtime type detection |
| [Upstream issue #101](https://github.com/OS4CSAPI/ogc-client-CSAPI_2/issues/101) | DataRecord complex type parser fix (related but separate) |

---

## Appendix: OGC Spec References

- **OGC 23-002 §7.3** — Datastream Resources: `phenomenonTime` and `resultTime` are temporal extents (time period arrays).
- **OGC 23-002 §7.5** — Observation Resources: `phenomenonTime` is an instant (single value), `resultTime` is an instant.
- **OGC 23-002 §7.7** — ControlStream Resources: `issueTime` and `executionTime` are temporal extents.
- **OGC 23-002 §7.9** — Command Resources: `issueTime` is an instant, `executionTime` is a time period.
- **OGC 23-002 §7.11** — CommandStatus Resources: `reportTime` is an instant, `executionTime` is a time period.
