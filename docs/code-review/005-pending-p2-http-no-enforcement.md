---
status: upstream
priority: p2
issue_id: "005"
tags: [code-review, security, https-enforcement]
dependencies: []
---

# `OgcApiEndpoint` Constructor Accepts `http://` Without Warning

## Problem Statement

`OgcApiEndpoint` accepts any URL scheme including `http://` with no validation. All downstream CSAPI URL construction inherits the insecure scheme. Browser consumers making `http://` requests trigger mixed-content blocks. Servers that use token-based authentication via query parameters (common with OGC servers) will expose credentials over cleartext. There is no upgrade logic anywhere in the chain.

## Findings

**File:** `src/ogc-api/endpoint.ts`, **line 148**
```typescript
constructor(private baseUrl: string) {}
```

No scheme check. No warning. All 30+ methods that call `fetchDocument`, `fetchLink`, `fetchRoot` use the stored `baseUrl` directly.

## Proposed Solutions

### Option A: `console.warn` on non-localhost `http://` (Recommended for library)
```typescript
constructor(private baseUrl: string) {
  try {
    const parsed = new URL(baseUrl);
    if (
      parsed.protocol === 'http:' &&
      parsed.hostname !== 'localhost' &&
      parsed.hostname !== '127.0.0.1' &&
      !parsed.hostname.startsWith('[::1]')
    ) {
      console.warn(
        `[ogc-client] Insecure URL: "${baseUrl}". Use https:// to protect data in transit.`
      );
    }
  } catch {
    // Invalid URL — will fail at first network call, not our responsibility to throw here
  }
}
```
**Pros:** Warns consumers without breaking existing callers; allows HTTP for localhost dev/test; non-breaking.
**Effort:** Small | **Risk:** None

### Option B: Throw `EndpointError` on non-localhost `http://`
Same check as Option A but throws instead of warning.
**Pros:** Enforces HTTPS for all non-local use.
**Cons:** Breaking change for consumers currently using HTTP endpoints (government/enterprise OGC servers often still serve HTTP).
**Effort:** Small | **Risk:** Breaking for some consumers

### Option C: No change, document the requirement in JSDoc
```typescript
/**
 * @param baseUrl - The OGC API endpoint URL. Must use https:// for non-localhost URLs
 *   to prevent credential exposure and mixed-content issues in browsers.
 */
constructor(private baseUrl: string) {}
```
**Effort:** Trivial | **Risk:** None (but doesn't protect consumers)

## Recommended Action

Option A — warn on non-localhost HTTP. Libraries should be defensive without being breaking. The warning will surface in developer consoles and CI logs, prompting migration to HTTPS.

## Technical Details

- **Affected file:** `src/ogc-api/endpoint.ts:148`
- **Scope:** All `OgcApiEndpoint` instances, all protocol methods

## Acceptance Criteria

- [ ] `new OgcApiEndpoint('http://remote.example.com')` emits a `console.warn`
- [ ] `new OgcApiEndpoint('http://localhost:8080')` does NOT warn
- [ ] `new OgcApiEndpoint('https://example.com')` does NOT warn
- [ ] Existing tests pass

## Ownership Assessment

**Ownership: UPSTREAM (camptocamp/ogc-client)** — `src/ogc-api/endpoint.ts` exists on `upstream/main` and is not within the `csapi/` isolation boundary. This finding cannot be addressed in our CSAPI PR (#136). If pursued, it should be filed as a feature request on camptocamp/ogc-client, not as a fix in our working branch.

## Work Log

- 2026-03-05: Identified by security-sentinel agent during code review of `clean-pr`
- 2026-03-06: Filed to docs/code-review/; not tracked as GitHub issue (upstream ownership)
