---
status: upstream
priority: p1
issue_id: '001'
tags: [code-review, security, input-encoding, upstream]
dependencies: []
related: ['002']
---

# Path Traversal via Unencoded `itemId` in `getCollectionItem`

> **Upstream:** This finding affects pre-existing code authored by the camptocamp/ogc-client maintainers (Olivier Guyot, commit `ecdb8442`, 2023-02-12). The vulnerable line exists identically in `upstream/main`. This is NOT code we introduced — do not modify in our PR.

## Problem Statement

`getCollectionItem()` appends `itemId` directly to `url.pathname` without calling `encodeURIComponent`. An `itemId` containing a literal `/` (valid in OGC API item IDs) is interpreted as a path separator, enabling path traversal. A caller passing `itemId = "../other-collection/secret"` silently resolves to a different collection resource.

**Why it matters:** This is user-controlled input directly concatenated into a URL path with no encoding guard. It is a path injection vulnerability in the pre-existing `endpoint.ts` that ships to all consumers of the library.

## Findings

**File:** `src/ogc-api/endpoint.ts`, **line 551**

```typescript
// VULNERABLE:
url.pathname += `/${itemId}`;

// Example attack:
getCollectionItem('sensors', '../admin/secret');
// → url.pathname becomes /collections/sensors/items/../admin/secret
// → resolves to /collections/admin/secret
```

`encodeURIComponent` would encode `/` → `%2F`, preventing traversal.

## Ownership Verification

```
$ git blame -L 551,551 -- src/ogc-api/endpoint.ts
ecdb8442 (Olivier Guyot 2023-02-12 22:27:52 +0100 551) url.pathname += `/${itemId}`;

$ git show upstream/main:src/ogc-api/endpoint.ts | grep 'url.pathname += `/${itemId}`'
        url.pathname += `/${itemId}`;
```

The vulnerable line was authored by upstream maintainer Olivier Guyot in 2023 and exists identically in `upstream/main`. It is not in our diff.

**Conclusion:** This code is pre-existing upstream. Our CSAPI module correctly uses `encodeResourceId()` (which wraps `encodeURIComponent`) for all resource IDs — see `src/ogc-api/csapi/helpers.ts:97`.

## Assessment

The senior developer's finding is **TRUE and VERIFIED**:

1. **Vulnerability confirmed** — `url.pathname += \`/\${itemId}\`` with no encoding is a textbook path traversal vector
2. **Upstream-only** — authored by Olivier Guyot (2023-02-12), present in `upstream/main`, not in our diff
3. **Out of scope for our PR** — per governance rules, we do not modify upstream code we didn't write
4. **CSAPI is not affected** — our fork's CSAPI module uses `encodeResourceId()` consistently
5. **Tracked for awareness** — filed as an upstream tracking issue on our repo with the `upstream` label

The recommended fix (Option A: `encodeURIComponent`) is correct — one-character fix, zero regression risk. However, it must be contributed by or coordinated with the camptocamp maintainers, not bundled into our CSAPI PR.

## Proposed Solutions

### Option A: `encodeURIComponent` at the point of injection (Recommended)

```typescript
url.pathname += `/${encodeURIComponent(itemId)}`;
```

**Pros:** One-character fix, no API change, zero risk of regression, consistent with `encodeResourceId()` used in CSAPI.
**Cons:** None.
**Effort:** Small | **Risk:** None

### Option B: Validate that `itemId` contains no `/` before appending

```typescript
if (itemId.includes('/'))
  throw new EndpointError(`Invalid itemId: "${itemId}"`);
url.pathname += `/${itemId}`;
```

**Pros:** Explicit rejection of traversal attempts.
**Cons:** Breaks callers with legitimate slash-containing IDs (valid per OGC spec). Encoding is the correct solution, not rejection.
**Effort:** Small | **Risk:** Low (breaks valid use cases)

## Recommended Action

Option A — add `encodeURIComponent`. However, since this is upstream code, this should be offered as a separate upstream PR to camptocamp/ogc-client, not included in our CSAPI contribution.

## Technical Details

- **Affected file:** `src/ogc-api/endpoint.ts:551`
- **Affected method:** `getCollectionItem(collectionId, itemId)`
- **Root cause:** Direct `url.pathname +=` without `encodeURIComponent`
- **Upstream author:** Olivier Guyot (commit `ecdb8442`, 2023-02-12)
- **Note:** The CSAPI `url_builder.ts` correctly uses `encodeResourceId()` for all resource IDs

## Acceptance Criteria

- [ ] Tracked as upstream issue on our repo
- [ ] Labeled `upstream` — do NOT modify in our PR
- [ ] If/when camptocamp fixes this, sync the fix into our fork

## Work Log

- 2026-03-05: Identified by senior developer during code review of `clean-pr`
- 2026-03-07: Verified as upstream-only; filed as tracking issue with upstream label
