---
status: upstream
priority: p1
issue_id: "002"
tags: [code-review, security, input-encoding, upstream]
dependencies: []
related: ["001"]
---

# Query Parameter Injection via `encodeURI` in `getCollectionItemsUrl`

> **Upstream:** This finding affects pre-existing code authored by the camptocamp/ogc-client maintainers (Olivia, commit `d587336c`, 2025-08-04). The vulnerable line exists identically in `upstream/main`. This is NOT code we introduced — do not modify in our PR.

## Problem Statement

`getCollectionItemsUrl()` appends a caller-supplied `query` string using `encodeURI`, which does NOT encode `&`, `=`, `?`, or `#`. A caller can inject additional query parameters (e.g. `"limit=9999"`) that override server-set pagination parameters, or corrupt the URL entirely with `#fragment`. The JSDoc says "will be URL-encoded if necessary" — this is a false promise.

**Why it matters:** Parameter injection can silently override pagination limits (e.g. `limit=9999` fetching unbounded data), expose unexpected query parameters to the server, or corrupt URLs in ways that are invisible to callers.

## Findings

**File:** `src/ogc-api/endpoint.ts`, **line 651**

```typescript
// VULNERABLE:
if (options.query !== undefined)
  url.search += (url.search ? '&' : '') + encodeURI(options.query);

// Attack 1 — override pagination:
getCollectionItemsUrl('sensors', { query: 'name=foo&limit=99999' })
// → &name=foo&limit=99999 appended — limit=99999 overrides the 10-item limit set earlier

// Attack 2 — URL corruption:
getCollectionItemsUrl('sensors', { query: '#anything' })
// → # treated as fragment boundary, rest of URL ignored by server
```

`encodeURI` encodes spaces and non-ASCII but leaves `&`, `=`, `?`, `#`, `;` intact.

## Ownership Verification

```
$ git blame -L 651,651 -- src/ogc-api/endpoint.ts
d587336c (Olivia 2025-08-04 11:52:52 +0200 651) url.search += (url.search ? '&' : '') + encodeURI(options.query);

$ git show upstream/main:src/ogc-api/endpoint.ts | grep 'encodeURI(options.query)'
          url.search += (url.search ? '&' : '') + encodeURI(options.query);
```

The vulnerable line was authored by upstream contributor Olivia in 2025 and exists identically in `upstream/main`. It is not in our diff.

**Conclusion:** This code is pre-existing upstream.

## Assessment

The senior developer's finding is **TRUE and VERIFIED**:

1. **Vulnerability confirmed** — `encodeURI` does not encode `&`, `=`, `?`, `#`, enabling parameter injection and URL corruption
2. **Upstream-only** — authored by Olivia (2025-08-04), present in `upstream/main`, not in our diff
3. **Out of scope for our PR** — per governance rules, we do not modify upstream code we didn't write
4. **CSAPI is not affected** — our fork's CSAPI URL builder uses typed query parameter construction via `buildQueryString()` which encodes each parameter value individually
5. **Tracked for awareness** — filed as an upstream tracking issue on our repo with the `upstream` label

The recommended fix (Option A: `URLSearchParams`) is correct — properly encodes each value, prevents injection. However, it must be contributed by or coordinated with the camptocamp maintainers, not bundled into our CSAPI PR.

## Proposed Solutions

### Option A: Parse `query` as key=value pairs via `URLSearchParams` (Recommended)
```typescript
if (options.query !== undefined) {
  for (const [k, v] of new URLSearchParams(options.query)) {
    url.searchParams.append(k, v);
  }
}
```
**Pros:** Properly encodes each value; prevents injection of extra `&k=v` pairs; clear intent.
**Cons:** Breaking change if callers pass pre-encoded strings or raw filter syntax (e.g. CQL).
**Effort:** Small | **Risk:** Low (may break callers relying on pass-through behaviour)

### Option B: Document `query` as a deliberate escape hatch
Add explicit security warning to JSDoc that `query` is not sanitized.
**Pros:** No code change, honest documentation.
**Cons:** Leaves the injection vector open.
**Effort:** Trivial | **Risk:** High (vulnerability remains open)

## Recommended Action

Option A — parse via `URLSearchParams`. However, since this is upstream code, this should be offered as a separate upstream PR to camptocamp/ogc-client, not included in our CSAPI contribution.

## Technical Details

- **Affected file:** `src/ogc-api/endpoint.ts:651`
- **Affected method:** `getCollectionItemsUrl(collectionId, options)`
- **Root cause:** `encodeURI` does not encode structural URL characters (`&`, `=`, `#`)
- **Upstream author:** Olivia (commit `d587336c`, 2025-08-04)
- **Note:** The CSAPI `url_builder.ts` uses typed query construction via `buildQueryString()` which is not affected

## Acceptance Criteria

- [ ] Tracked as upstream issue on our repo
- [ ] Labeled `upstream` — do NOT modify in our PR
- [ ] If/when camptocamp fixes this, sync the fix into our fork

## Work Log

- 2026-03-05: Identified by senior developer during code review of `clean-pr`
- 2026-03-07: Verified as upstream-only; filed as tracking issue with upstream label
