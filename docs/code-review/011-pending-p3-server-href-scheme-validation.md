---
status: pending
priority: p3
issue_id: '011'
tags: [code-review, security, defense-in-depth]
dependencies: []
---

# Server-Returned `href` Values Stored Without Scheme Validation

## Problem Statement

`scanCsapiLinks()` stores server-returned `href` values directly into the `resourceUrls` map which later becomes the base URL for all CSAPI query construction. No validation of the URL scheme is performed. A malicious or misconfigured server returning `href: "javascript:..."`, `href: "//evil.com/systems"`, or `href: "data:..."` would cause the library to construct URLs against those bases.

**Risk level is bounded** — this library constructs URLs but does not fetch them itself. The real risk is SSRF in consuming apps or XSS if URLs are rendered in links/src attributes. Defense-in-depth is appropriate.

## Findings

**File:** `src/ogc-api/csapi/helpers.ts`, **lines 147–154**

```typescript
result.set(match[1], typeof href === 'string' ? href : '');
result.set(rel, typeof href === 'string' ? href : '');
result.set(normalized, href);
```

Relative URLs are safe (they resolve against the trusted base). Absolute non-HTTP(S) URLs are not.

## Proposed Solutions

### Option A: Filter on `isTrustedHref` before storing (Recommended)

```typescript
function isTrustedHref(href: string): boolean {
  try {
    const url = new URL(href);
    return url.protocol === 'https:' || url.protocol === 'http:';
  } catch {
    return true; // relative URL — safe, resolves against trusted base
  }
}

// In scanCsapiLinks, before result.set():
if (!isTrustedHref(href)) continue;
```

**Effort:** Small | **Risk:** None

### Option B: No change — document that consumers are responsible for trusting their servers

**Effort:** Trivial | **Risk:** Low (bounded, defense-in-depth only)

## Recommended Action

Option A. Small effort, makes the library hardened against misconfigured or hostile server responses.

## Technical Details

- **Affected file:** `src/ogc-api/csapi/helpers.ts:129–171`

## Acceptance Criteria

- [ ] `scanCsapiLinks` skips hrefs with `javascript:`, `data:`, or other non-HTTP(S) schemes
- [ ] Relative hrefs are still stored (they are safe)
- [ ] Absolute `http://` and `https://` hrefs are stored as before

## Work Log

- 2026-03-05: Identified by security-sentinel agent during code review of `clean-pr`
