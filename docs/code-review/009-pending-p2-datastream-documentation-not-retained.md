---
status: pending
priority: p2
issue_id: '009'
tags: [code-review, csapi, metadata, sensorml]
dependencies: []
---

# Datastream Documentation Metadata Is Not Retained On Current Server

## Problem Statement

For the current live CSAPI deployment, license metadata placed on datastream `documentation` is not durable. During bootstrap create, helper logs confirm `documentation` is stripped before POST, and a direct datastream PUT with `documentation` returns HTTP 500. As a result, clients cannot rely on datastream metadata for license/terms links.

## Findings

1. Bootstrap run output on Oracle showed:

```text
[WARN] Stripped datastream field(s) ['uid', 'documentation'] before POST for digitrafficWeatherCamImage
```

2. Live API readback after bootstrap:

```text
GET /datastreams/07m02 -> no documentation field present
```

3. Direct update probe:

```text
PUT /datastreams/07m02 with documentation -> HTTP 500 Internal server error
```

4. Procedure SensorML remains durable and contains license docs:

```text
GET /procedures/04k0?f=application/sml+json
documents: Digitraffic Terms of Use -> https://www.digitraffic.fi/en/terms-of-service/
```

## Impact

- License/attribution links cannot be treated as datastream-native metadata on this server.
- Clients need a SensorML-aware fallback to procedure metadata for legal attribution display.

## Ownership Assessment

Likely server/API behavior in deployed CSAPI implementation (not a frontend-only defect). Bootstrap helper behavior already strips unsupported datastream fields to avoid strict-server create failures.

## Recommended Action

1. Server-side: accept and persist datastream `documentation` (or return explicit 4xx with validation details).
2. Client-side (current mitigation): resolve license metadata from procedure SensorML when datastream docs are absent.
3. Keep a regression test around procedure ranking/selection so fallback behavior does not regress.

## Reproduction

1. Create datastream with `documentation` in body.
2. Read datastream back and confirm docs missing.
3. Attempt PUT to add `documentation`; observe HTTP 500.

## Work Log

- 2026-06-04: Observed on live endpoint `https://129-80-248-53.sslip.io/sensorhub/api` during Digitraffic weathercam refresh.
- 2026-06-04: Explorer updated to use procedure SensorML docs as canonical fallback for license links.
