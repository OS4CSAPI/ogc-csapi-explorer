---
status: upstream
priority: p2
issue_id: "006"
tags: [code-review, security, credential-leakage]
dependencies: []
---

# Full `error` Object Logged via `console.error` — May Expose API Keys in URLs

## Problem Statement

`getCollectionItemsUrl()` logs the full `error` object (not just `error.message`). Network errors from the Fetch API routinely include the full request URL in the error object's properties. If the `OgcApiEndpoint` is initialized with a URL containing an API key query parameter (e.g. `?apiKey=sk_live_...`), that key is logged to the browser console and any centralized logging system that captures console output.

## Findings

**File:** `src/ogc-api/endpoint.ts`, **line 656**
```typescript
.catch((error) => {
  console.error('Error fetching collection items URL:', error);  // ← full object, not .message
  throw error;
});
```

Contrast with the consistent (safer) pattern in the same file at **lines 701, 746**:
```typescript
.catch((error) => {
  console.error('Error fetching collection tileset URL:', error.message);  // ← .message only
  throw error;
});
```

The inconsistency itself is a signal — one handler was updated and the other was not.

## Proposed Solutions

### Option A: Log `error.message` only (Recommended)
```typescript
.catch((error) => {
  console.error('Error fetching collection items URL:', error.message);
  throw error;
});
```
**Pros:** One-word fix; consistent with lines 701/746; eliminates URL exposure in logs.
**Effort:** Trivial | **Risk:** None

### Option B: Remove `console.error` entirely (callers receive the thrown error)
```typescript
.catch((error) => {
  throw error;
});
```
**Pros:** Libraries generally should not log to console at all — the consuming app can log what it needs.
**Cons:** Removes a convenience log that may help debugging during development.
**Effort:** Trivial | **Risk:** None

## Recommended Action

Option A — log `error.message` only, matching the existing pattern on lines 701/746.

## Technical Details

- **Affected file:** `src/ogc-api/endpoint.ts:656`
- **One-character fix:** Change `error` → `error.message`

## Acceptance Criteria

- [ ] `console.error` at `endpoint.ts:656` logs `error.message`, not the full `error` object
- [ ] Pattern is consistent with lines 701 and 746
- [ ] No behavioral change — error is still re-thrown

## Ownership Assessment

**Ownership: UPSTREAM (camptocamp/ogc-client)** — Both the buggy line 656 (commit `6ff1fff`, Ronit Jadhav, 2024-04-05) and the correct lines 701/746 (commit `f1d10993`, ronitjadhav, 2024-04-27) are upstream camptocamp code present on `upstream/main`. Our fork never touched these lines. This is a pre-existing inconsistency, not something introduced by our CSAPI contribution. If pursued, it should be filed as a one-line PR or issue on camptocamp/ogc-client, not addressed in our working branch.

## Work Log

- 2026-03-05: Identified by security-sentinel agent during code review of `clean-pr`
- 2026-03-06: Filed to docs/code-review/; not tracked as GitHub issue (upstream ownership)
