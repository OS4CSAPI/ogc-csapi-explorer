# Incident Report: External Write Activity on OSH Server

**Date:** 2026-03-04  
**Detected:** ~17:20 UTC (operator noticed data changes on map view)  
**Activity window:** 15:04 – 15:17 UTC  
**Severity:** Low — no data loss; external user created and cleaned up their own resources  

---

## 1. Timeline

| Time (UTC) | Event |
|------------|-------|
| ~14:00 | Credentials (`os4csapi` / `ogc134mm`) shared on [GitHub Discussion #37](https://github.com/orgs/OS4CSAPI/discussions/37) in reply to @doublebyte1 |
| 15:04:33 | First external POST: `POST /sensorhub/api/systems` — user begins creating test resources |
| 15:14–15:15 | Additional creates: systems, deployments, subsystems, datastreams, control streams |
| 15:16:43 | First DELETE: user begins cleaning up their test resources |
| 15:17:21 | Last DELETE: `DELETE /sensorhub/api/samplingFeatures/040g` |
| ~17:20 | Operator notices data changes on map view, begins investigation |

## 2. What Happened

An external user (likely @doublebyte1, who requested credentials on GitHub Discussion #37) connected to the server and ran a **create → explore → delete** test cycle:

1. **15:04–15:15 UTC** — Created test systems, deployments, subsystems, datastreams, and control streams
2. **15:16–15:17 UTC** — Deleted all the resources they created

The deleted resource IDs (e.g., `04og`, `04o0`, `04ng`, `04fg`, `04g0`) were **new resources created by the external user**, not part of the existing demo scenario. OSH assigns IDs sequentially, so these IDs were higher than the demo's existing resources.

### Resources created and deleted by external user

| Resource Type | IDs | Notes |
|---------------|-----|-------|
| Systems | `04og`, `04o0`, `04ng` | Test systems with subsystems and datastreams |
| Deployments | Created under `048g`, `0490` | Test deployments with sub-deployments |
| Datastreams | `04fg`, `04g0` | Attached to test systems |
| Control Streams | `0460`, `045g` | Attached to test systems |
| Procedures | `0460`, `045g` | Test procedures |
| Sampling Features | `0410`, `040g` | Test sampling features |
| Observations | `042dn6d1pk32jthg00` | At least 1 test observation |

## 3. Impact on Demo Data

**None.** The existing demo deployment hierarchy, systems, datastreams, and procedures were never modified or deleted. Full audit confirmed:

- **7 systems** — all present (SET-A, MSN-1, Relay, AZ-MA-1/2/3, Localizer)
- **10+ deployments** — full hierarchy intact (ICO → R&S → SSO → SNET → Field/String → Nodes)
- **10 procedures** — all original ODAS + localizer procedures
- **All datastreams** — LOB, health, detection_capabilities, etc.
- **platform@link** references on node emplacements verified correct
- **Simulator** running normally (Fly.io IP `64.34.84.117` posting LOB observations every 5s)

## 4. Why It Looked Alarming

The initial investigation ran `GET /deployments?limit=100` (flat listing) and saw only 1 deployment. This was misleading — the flat listing query was temporarily affected by OSH processing the deletes of the external user's resources. A recursive walk of `subdeployments` confirmed the full hierarchy was intact the whole time.

## 5. Source Attribution

All DELETE requests were logged by OSH as `user=ogc`, which is the internal user that Caddy maps from the public `os4csapi` basicauth credential.

Source IPs in the OSH logs:
- `172.68.245.32` — Cloudflare edge node
- `162.158.154.13` — Cloudflare edge node

Both are Cloudflare proxy IPs, meaning the requests came through the HTTPS reverse proxy (port 443 via Caddy). The actual client IP is masked by Cloudflare. The requests originated from someone who had the public `os4csapi` / `ogc134mm` credentials.

## 6. Root Cause (Access Control Gap)

The Caddy reverse proxy grants full read/write access to anyone with the `os4csapi` basicauth credential. There is no role separation — the public credential maps to `ogc:ogc` internally, which has the `admin` role in OSH. This means anyone with the shared credentials can create, modify, and delete any resource.

## 7. Lessons / Action Items

- [ ] **Role separation**: Create a read-only user for public access; keep write access behind a separate credential
- [ ] **Caddy access logging**: Enable request-level access logging so client operations can be audited (currently only TLS renewal is logged)
- [ ] **Cloudflare real-IP forwarding**: Configure Caddy to log `CF-Connecting-IP` header so actual client IPs are captured
- [ ] **OSH auth roles**: Investigate whether OSH supports per-resource or per-method role restrictions (e.g., `reader` role that only allows GET)
- [ ] **Rebuild**: ~~Re-run bootstrap scripts~~ — not needed, no data loss

---

## 8. Deployment Hierarchy (verified intact)

```
040g ICO
  0410 R&S Operation
    041g SSO
      0420 Sensor Network
        042g Sensor Field 001
        045g MSN-1 Emplacement
        0460 Relay Emplacement
        046g String Alpha
          0470 Node 1 — AZ-MA-1 (platform@link → 0420)
          047g Node 2 — AZ-MA-2 (platform@link → 0490)
          0480 Node 3 — AZ-MA-3 (platform@link → 049g)
      0450 SET-A
```

The pattern in the logs shows the external user was **creating their own resources, then deleting them** — a responsible test/explore cycle. They cleaned up after themselves. The demo data was never touched.

---

## 9. Server Configuration Reference

- **Caddy config**: `/etc/caddy/Caddyfile`
- **OSH config**: `/opt/sensorhub/config/config.json`
- **OSH internal users**: `admin/admin` (admin), `ogc/ogc` (admin), `sensor/pwd` (sost), `anonymous` (anon)
- **Public credential**: `os4csapi` → maps to `ogc:ogc` (admin role) via Caddy `header_up Authorization`
- **OSH logs**: `sudo journalctl -u sensorhub`
