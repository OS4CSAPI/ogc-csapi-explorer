# AWS Backend Infrastructure Plan

**Date:** 2026-02-21  
**Status:** Planning — no infrastructure deployed  
**Related:** [iPad App Store Feasibility](./ipad-app-store-feasibility.md)

## Problem Statement

The CSAPI Explorer webapp and potential iPad app both need to reach arbitrary CSAPI servers. Two blockers exist for production deployment:

1. **Hosted webapp** — The Vite dev proxy only exists during local development. A production build served from a static host cannot proxy requests, so CORS blocks direct calls to servers that don't send `Access-Control-Allow-Origin` headers.
2. **iPad app** — While Capacitor's native HTTP plugin bypasses CORS, a shared proxy layer provides consistency, caching, and centralized logging across both platforms.

## Proposed Architecture (MVP)

```
┌──────────────┐    ┌──────────────┐
│  Browser /   │    │  iPad App    │
│  Hosted SPA  │    │ (Capacitor)  │
└──────┬───────┘    └──────┬───────┘
       │                   │
       └───────┬───────────┘
               ▼
    ┌─────────────────────┐
    │   CloudFront CDN    │──── Static webapp (S3 origin)
    │  (custom domain)    │
    └─────────┬───────────┘
              │ /proxy/*
              ▼
    ┌─────────────────────┐
    │   API Gateway       │
    │  (REST or HTTP API) │
    └─────────┬───────────┘
              ▼
    ┌─────────────────────┐
    │   Lambda Function   │──── Forwards request to target CSAPI server
    │  (CORS proxy relay) │     Returns response with CORS headers
    └─────────────────────┘
```

### Services

| AWS Service | Purpose | Estimated Cost |
|-------------|---------|----------------|
| **S3** | Host the built webapp as static files | ~$0.25/month |
| **CloudFront** | CDN for the static site + custom domain + HTTPS | ~$1–5/month |
| **API Gateway (HTTP API)** | Route `/proxy/*` requests to the Lambda function | ~$0 at low traffic (1M free requests/month) |
| **Lambda** | CORS proxy relay — accepts target URL, forwards request, returns response with CORS headers | ~$0 at low traffic (1M free invocations/month) |
| **Route 53** | Custom domain (e.g., `csapi-explorer.org`) | ~$0.50/month per hosted zone |
| **ACM** | Free SSL certificate for the custom domain | $0 |

**Estimated total: under $10/month** for typical usage.

## CORS Proxy Lambda Design

The Lambda function is the only custom code required (~50 lines). It:

1. Accepts the target CSAPI server URL + path as query parameters (e.g., `/proxy?target=http://45.55.99.236:8080/sensorhub/api/systems`)
2. Forwards the full request (method, query params, headers, body)
3. Returns the upstream response with `Access-Control-Allow-Origin: *` and other CORS headers injected
4. Handles preflight `OPTIONS` requests automatically

### Security Controls

- **URL allowlist** (optional) — restrict proxy to known CSAPI servers to prevent open-relay abuse
- **Rate limiting** — API Gateway supports throttling per IP (e.g., 100 requests/second burst)
- **Request size limit** — API Gateway enforces 10 MB payload limit by default
- **Logging** — CloudWatch captures all invocations for monitoring

### Example Request Flow

```
GET https://csapi-explorer.org/proxy?target=http://45.55.99.236:8080/sensorhub/api/systems&limit=10

→ Lambda extracts target URL
→ Lambda fetches: GET http://45.55.99.236:8080/sensorhub/api/systems?limit=10
→ Lambda returns response body + headers + Access-Control-Allow-Origin: *
```

## Deployment Strategy

### Phase 1 — Static Hosting (Immediate)

Deploy the built webapp to S3 + CloudFront. This makes the app accessible at a public URL. CORS proxy not yet needed if users connect to servers that already support CORS.

**Alternative:** AWS Amplify Hosting can replace S3 + CloudFront with a single service that handles CI/CD (auto-deploy on push), preview environments, and custom domains. Simpler to manage but slightly less control.

### Phase 2 — CORS Proxy (When Needed)

Add the API Gateway + Lambda proxy when users need to reach servers without CORS headers (which is most CSAPI servers today).

### Phase 3 — iPad App Backend (If Pursued)

The same API Gateway endpoint serves both the webapp and the iPad app. The iPad app can optionally use Capacitor's native HTTP plugin for direct server access and fall back to the proxy for problematic servers.

## Optional Future Add-ons

| Service | Purpose | When |
|---------|---------|------|
| **DynamoDB** | Persist user connections, bookmarks, smoke test results | If user accounts are added |
| **Cognito** | Authentication (Apple Sign-In for iPad, Google, email) | If features are gated behind auth |
| **CloudWatch Alarms** | Alert on proxy errors, high latency, unusual traffic | Good practice from day 1 |
| **WAF** | Web Application Firewall — rate limiting, IP blocking, bot protection | If traffic grows or abuse occurs |
| **SQS / EventBridge** | Queue background tasks (e.g., scheduled server health checks) | If automated monitoring is added |

## Infrastructure-as-Code

Recommend defining all resources with **AWS CDK** (TypeScript) or **SAM** (Serverless Application Model) for reproducible deployments. The entire MVP stack is ~100 lines of CDK code.

## Comparison with Alternatives

| Approach | Pros | Cons |
|----------|------|------|
| **AWS (S3 + CloudFront + Lambda)** | Full control, serverless, scales to zero, cheap | More setup than managed platforms |
| **Vercel** | Zero-config for Vue/Vite, edge functions for proxy | Less control, potential vendor lock-in |
| **Netlify** | Similar to Vercel, good free tier | Proxy functions have 10s timeout (may not suit slow CSAPI servers) |
| **Cloudflare Pages + Workers** | Fast edge network, Workers for proxy, generous free tier | Different deployment model, less AWS ecosystem integration |

AWS is recommended because it provides the most flexibility for future growth (DynamoDB, Cognito, custom domains) and aligns with standard enterprise infrastructure.

## Estimated Setup Effort

| Task | Effort |
|------|--------|
| S3 bucket + CloudFront distribution + custom domain | ~2 hours |
| Lambda proxy function + API Gateway | ~2–4 hours |
| CDK/SAM infrastructure-as-code | ~2–4 hours |
| CI/CD pipeline (GitHub Actions → deploy on push) | ~1–2 hours |
| Testing + DNS propagation | ~1–2 hours |
| **Total** | **~8–14 hours** |
