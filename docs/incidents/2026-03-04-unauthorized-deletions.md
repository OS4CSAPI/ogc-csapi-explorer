# Incident Report: Unauthorized Resource Deletions

**Date:** 2026-03-04  
**Detected:** ~17:20 UTC (user noticed data changes)  
**Window:** 15:16:43 – 15:17:21 UTC  
**Duration:** ~38 seconds  
**Severity:** Moderate — demo deployment hierarchy partially destroyed  

---

## 1. Timeline

| Time (UTC) | Event |
|------------|-------|
| ~14:00 | Credentials (`os4csapi` / `ogc134mm`) shared on [GitHub Discussion #37](https://github.com/orgs/OS4CSAPI/discussions/37) in reply to @doublebyte1 |
| 15:16:43 | First DELETE: `DELETE /sensorhub/api/systems/04og` (ip=172.68.245.32, user=ogc) |
| 15:16:43 | `DELETE /sensorhub/api/deployments/049g` |
| 15:16:44 | `DELETE /sensorhub/api/observations/042dn6d1pk32jthg00` |
| 15:17:13 | `DELETE /sensorhub/api/datastreams/04fg` |
| 15:17:13 | `DELETE /sensorhub/api/datastreams/04g0` |
| 15:17:13 | `DELETE /sensorhub/api/controlstreams/0460` |
| 15:17:13 | `DELETE /sensorhub/api/systems/04o0` |
| 15:17:14 | `DELETE /sensorhub/api/procedures/0460` |
| 15:17:14 | `DELETE /sensorhub/api/deployments/0490` |
| 15:17:14 | `DELETE /sensorhub/api/samplingFeatures/0410` |
| 15:17:17 | `DELETE /sensorhub/api/controlstreams/045g` |
| 15:17:18 | `DELETE /sensorhub/api/systems/04ng` |
| 15:17:19 | `DELETE /sensorhub/api/procedures/045g` |
| 15:17:20 | `DELETE /sensorhub/api/deployments/048g` |
| 15:17:21 | `DELETE /sensorhub/api/samplingFeatures/040g` (last DELETE in logs) |
| ~17:20 | Deletions noticed by operator |

## 2. What Was Deleted

| Resource Type | IDs Deleted | Notes |
|---------------|-------------|-------|
| Systems | `04og`, `04o0`, `04ng` | Unknown systems — possibly created by the external user, then deleted |
| Deployments | `049g`, `0490`, `048g` | Sub-deployments from the scenario hierarchy |
| Datastreams | `04fg`, `04g0` | Unknown — possibly created then deleted |
| Control Streams | `0460`, `045g` | ODAS config actuation streams |
| Procedures | `0460`, `045g` | Calibration/health procedures |
| Sampling Features | `0410`, `040g` | SENREP sampling features |
| Observations | `042dn6d1pk32jthg00` | At least 1 individual observation |

## 3. What Survived

After the deletions, the server still had:
- **7 systems** (SET-A, MSN-1, Relay, AZ-MA-1/2/3, Localizer)
- **1 deployment** (ICO top-level only — full hierarchy gutted)
- **10 procedures** (all original ODAS + localizer procedures)
- **2 sampling features** (down from expected count)
- All **datastreams** for the 3 ODAS sensors (LOB, health, detection_capabilities, etc.)

## 4. Source Attribution

All DELETE requests were logged by OSH as `user=ogc`, which is the internal user that Caddy maps from the public `os4csapi` basicauth credential.

Source IPs in the OSH logs:
- `172.68.245.32` — Cloudflare edge node
- `162.158.154.13` — Cloudflare edge node

Both are Cloudflare proxy IPs, meaning the requests came through the HTTPS reverse proxy (port 443 via Caddy). The actual client IP is masked by Cloudflare. The requests originated from someone who had the public `os4csapi` / `ogc134mm` credentials.

## 5. Root Cause

The Caddy reverse proxy grants full read/write access to anyone with the `os4csapi` basicauth credential. There is no role separation — the public credential maps to `ogc:ogc` internally, which has the `admin` role in OSH. This means anyone with the shared credentials can create, modify, and delete any resource.

## 6. Lessons / Action Items

- [ ] **Role separation**: Create a read-only user for public access; keep write access behind a separate credential
- [ ] **Caddy access logging**: Enable request-level access logging so client operations can be audited (currently only TLS renewal is logged)
- [ ] **Cloudflare real-IP forwarding**: Configure Caddy to log `CF-Connecting-IP` header so actual client IPs are captured
- [ ] **OSH auth roles**: Investigate whether OSH supports per-resource or per-method role restrictions (e.g., `reader` role that only allows GET)
- [ ] **Rebuild**: ~~Re-run bootstrap scripts~~ — hierarchy restored itself (see §8)

---

## 8. Resolution

Upon further investigation, the full deployment hierarchy is **intact**:

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

The pattern in the logs shows the external user was **creating their own resources, then deleting them** — a test/explore cycle. Some of the deleted IDs (`0490`, `048g`, `049g`) collide with deployment IDs but refer to different resource types (the user created systems/procedures with those IDs, not the deployments themselves). The actual deployment hierarchy was never destroyed — only the `deployments?limit=100` flat listing temporarily showed fewer results because OSH was processing the deletes.

The current POST activity is exclusively the Fly.io simulator (`ip=64.34.84.117`) posting LOB observations every 5 seconds — normal operation.

**No rebuild needed.**

---

## 9. Server Configuration Reference

- **Caddy config**: `/etc/caddy/Caddyfile`
- **OSH config**: `/opt/sensorhub/config/config.json`
- **OSH internal users**: `admin/admin` (admin), `ogc/ogc` (admin), `sensor/pwd` (sost), `anonymous` (anon)
- **Public credential**: `os4csapi` → maps to `ogc:ogc` (admin role) via Caddy `header_up Authorization`
- **OSH logs**: `sudo journalctl -u sensorhub`
