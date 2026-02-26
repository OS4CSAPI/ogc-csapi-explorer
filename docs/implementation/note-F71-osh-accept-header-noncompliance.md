# Note: F71/F64 — OSH Accept Header Non-Compliance

**Date:** 2026-02-15
**Related Findings:** F64 (OSH ignores ALL Accept headers), F71 (OSH serves SML via `?f=sml3`)
**Status:** Informational — potential upstream issue for OpenSensorHub

## Summary

OSH ignores all HTTP `Accept` headers for content negotiation. The `?f=` query parameter works correctly (`?f=sml3` → `application/sml+json`, `?f=geojson` → `application/geo+json`), proving the serializers exist but are not wired to Accept header routing.

## Spec Alignment Argument

**OGC API - Common Part 1 (Core)** requires servers to support content negotiation via the HTTP `Accept` header. The `?f=` query parameter is defined as a _convenience alternative_ (for browsers, link sharing, etc.) — not a replacement. Both mechanisms are supposed to work. OSH only implementing `?f=` while ignoring `Accept` headers entirely violates:

- **HTTP/1.1 (RFC 7231 §5.3.2)** — `Accept` header is the standard content negotiation mechanism
- **OGC API - Common §7.8** — servers SHALL support content negotiation via `Accept` header
- **OGC API - Connected Systems Part 1** — inherits this requirement from Common

## Evidence

| Request                        | Expected Behavior | Actual Behavior                              |
| ------------------------------ | ----------------- | -------------------------------------------- |
| `Accept: application/sml+json` | Returns SML data  | Returns `application/json` (GeoJSON)         |
| `Accept: application/geo+json` | Returns GeoJSON   | Returns `application/json` (GeoJSON)         |
| `Accept: application/json`     | Returns JSON      | Returns `application/json` ✅ (coincidental) |
| `?f=sml3`                      | Returns SML data  | Returns `application/sml+json` ✅            |
| `?f=geojson`                   | Returns GeoJSON   | Returns `application/geo+json` ✅            |
| `?f=json`                      | Returns JSON      | Returns `application/json` ✅                |

The fact that `?f=sml3` works proves OSH _has_ the SML serializer — it just doesn't wire it to Accept header routing. This is likely a configuration or routing bug rather than a missing capability, which makes it very actionable for them.

## Recommendation

If filing an upstream issue on the OSH repo (likely `opensensorhub/osh-core` or wherever their API server lives), describe:

1. `Accept: application/sml+json` is ignored (always returns `application/json`)
2. `Accept: application/geo+json` is also ignored
3. `?f=sml3` and `?f=geojson` work correctly, proving the serializers exist
4. This makes the server non-compliant with OGC API - Common content negotiation requirements

## Impact on Our Code

For now, our code can work around this by using `?f=sml3` when targeting OSH. The integration layer (when built) may need server-specific content negotiation handling — detect OSH and use query parameters instead of Accept headers.
