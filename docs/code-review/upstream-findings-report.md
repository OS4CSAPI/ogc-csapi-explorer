# Upstream Security Findings — Out of Scope Assessment

**Date:** 2026-03-07
**Reviewer:** GitHub Copilot (Claude Opus 4.6)
**Source:** Senior developer code review of `clean-pr` (upstream draft PR #136)

---

## Summary

Four findings (001, 002, 005, 006) from the senior developer's code review target pre-existing code in `src/ogc-api/endpoint.ts` — code authored by camptocamp/ogc-client maintainers that we did not write and did not modify. All four findings are **TRUE and VERIFIED** but **out of scope** for our CSAPI PR.

- **001, 002** — P1-Critical security vulnerabilities (path traversal, query injection)
- **005, 006** — P2 security/quality issues (HTTP scheme enforcement, credential leakage in logs)

**Verdict: Do not fix in our PR. Do not create GitHub issues. Track via MD files only.**

---

## Finding 001 — Path Traversal via Unencoded `itemId`

**MD file:** [001-upstream-p1-path-traversal-item-id.md](001-upstream-p1-path-traversal-item-id.md)

| Field | Value |
|-------|-------|
| **Severity** | P1-Critical |
| **File** | `src/ogc-api/endpoint.ts:551` |
| **Upstream author** | Olivier Guyot (commit `ecdb8442`, 2023-02-12) |
| **Exists in `upstream/main`** | Yes — identical line |
| **In our diff** | No |
| **CSAPI affected** | No — CSAPI uses `encodeResourceId()` |

**Assessment:** The finding is correct. `url.pathname += \`/\${itemId}\`` without `encodeURIComponent` is a textbook path traversal vector. However, this line was written by the upstream maintainer in 2023, exists identically in `upstream/main`, and is not part of our contribution. Our CSAPI module is not affected because it uses `encodeResourceId()` (which wraps `encodeURIComponent`) for all resource IDs.

**Out of scope because:**
- We did not author this code
- It is not in our diff to `clean-pr`
- Modifying upstream code we didn't write violates our governance rules
- Our CSAPI code is independently protected

---

## Finding 002 — Query Parameter Injection via `encodeURI`

**MD file:** [002-upstream-p1-query-param-injection.md](002-upstream-p1-query-param-injection.md)

| Field | Value |
|-------|-------|
| **Severity** | P1-Critical |
| **File** | `src/ogc-api/endpoint.ts:651` |
| **Upstream author** | Olivia (commit `d587336c`, 2025-08-04) |
| **Exists in `upstream/main`** | Yes — identical line |
| **In our diff** | No |
| **CSAPI affected** | No — CSAPI uses typed `buildQueryString()` |

**Assessment:** The finding is correct. `encodeURI(options.query)` does not encode `&`, `=`, `?`, or `#`, enabling parameter injection and URL corruption. However, this line was authored by an upstream contributor in 2025, exists identically in `upstream/main`, and is not part of our contribution. Our CSAPI URL builder uses typed query parameter construction via `buildQueryString()` which individually encodes each parameter value — not affected.

**Out of scope because:**
- We did not author this code
- It is not in our diff to `clean-pr`
- Modifying upstream code we didn't write violates our governance rules
- Our CSAPI code is independently protected

---

## Finding 005 — `OgcApiEndpoint` Accepts `http://` Without Warning

**MD file:** [005-pending-p2-http-no-enforcement.md](005-pending-p2-http-no-enforcement.md)

| Field | Value |
|-------|-------|
| **Severity** | P2 |
| **File** | `src/ogc-api/endpoint.ts:148` |
| **Upstream author** | camptocamp — constructor exists on `upstream/main` |
| **Exists in `upstream/main`** | Yes — identical constructor |
| **In our diff** | No |
| **CSAPI affected** | Indirectly — inherits scheme from caller |

**Assessment:** The finding is correct. The `OgcApiEndpoint` constructor accepts any URL scheme including `http://` with no validation or warning. All downstream URL construction inherits the insecure scheme, enabling mixed-content blocks in browsers and credential exposure over cleartext. However, this constructor is upstream code we did not author or modify. The recommended fix (a `console.warn` on non-localhost HTTP) would be a valuable contribution but should be offered as a separate upstream PR.

**Out of scope because:**
- We did not author this code
- It is not in our diff to `clean-pr`
- Modifying upstream code we didn't write violates our governance rules

---

## Finding 006 — Full `error` Object Logged via `console.error` — May Expose API Keys

**MD file:** [006-pending-p2-error-object-logged.md](006-pending-p2-error-object-logged.md)

| Field | Value |
|-------|-------|
| **Severity** | P2 |
| **File** | `src/ogc-api/endpoint.ts:656` |
| **Upstream author** | Ronit Jadhav (commit `6ff1fff`, 2024-04-05) |
| **Exists in `upstream/main`** | Yes — identical line |
| **In our diff** | No |
| **CSAPI affected** | No — CSAPI methods use different error handling |

**Assessment:** The finding is correct. `getCollectionItemsUrl()` logs the full `error` object (not just `error.message`), which can expose API keys embedded in URLs. The same file has the correct pattern (`.message` only) at lines 701 and 746, confirming this is a pre-existing inconsistency — one handler was updated and the other was not. Both the buggy line (Ronit Jadhav, 2024) and the correct lines (ronitjadhav, 2024) are upstream commits. A one-character fix (`error` → `error.message`) should be offered as a trivial upstream PR or issue.

**Out of scope because:**
- We did not author this code
- It is not in our diff to `clean-pr`
- Pre-existing inconsistency between upstream contributors' handlers

---

## Recommendation

All four vulnerabilities are real and should eventually be fixed in the upstream camptocamp/ogc-client repository. If we choose to contribute fixes, they should be offered as **separate upstream PRs** — not bundled into our CSAPI contribution. For now, the MD files in `docs/code-review/` serve as our awareness record.
