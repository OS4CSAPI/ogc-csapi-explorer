# CORS Preflight Test Results — Demo Servers

> **Date**: 2026-02-16
> **Purpose**: Pre-development validation of CORS behavior on target demo servers before scaffolding the CSAPI Explorer webapp.

---

## Why We Ran This Test

The CSAPI Explorer demo app will run in a browser at `localhost:5173` (Vite dev server) and make cross-origin requests to two live Connected Systems API servers. Browsers enforce the **Same-Origin Policy** — any request to a different domain triggers CORS enforcement. If a server doesn't return the correct `Access-Control-*` headers, the browser blocks the request entirely (the server never even sees it for preflight failures).

This matters especially for **write operations** (POST, PUT, DELETE). Simple GET requests may work with basic CORS headers, but mutations require the browser to send a **preflight OPTIONS request** first, and the server must respond with headers explicitly allowing the method, headers, and origin.

We needed to know before writing any code:
1. Will simple GET requests (resource listing, discovery) work cross-origin?
2. Will write operations (POST with `Content-Type: application/geo+json`, PUT, DELETE) pass preflight?
3. Will `Authorization` headers be allowed cross-origin (needed for OSH SensorHub)?
4. Are there any other connectivity issues (SSL, server availability)?

This determines whether the Vite dev server proxy (planned in our architecture) is a hard requirement or a nice-to-have.

---

## How We Tested

All tests were run from a Windows machine using `curl.exe` from PowerShell. No application code was written — these are raw HTTP requests simulating what a browser would do.

### Test Matrix

| Test | What It Simulates |
|------|-------------------|
| HEAD request (no Origin header) | Basic connectivity check |
| HEAD request with `Origin: http://localhost:5173` | Browser simple request — does the server return `Access-Control-Allow-Origin`? |
| OPTIONS preflight with `Access-Control-Request-Method: POST` and `Access-Control-Request-Headers: Content-Type, Authorization` | Browser preflight before a write operation with JSON body and auth header |

### Servers Tested

| Server | URL | Auth |
|--------|-----|------|
| 52North | `https://csa.demo.52north.org/` | None (public) |
| OSH SensorHub | `http://45.55.99.236:8080/sensorhub/api` | Basic auth |

---

## Results

### 52North (`https://csa.demo.52north.org/`)

#### Finding 1: SSL Certificate Expired

```
curl.exe -v "https://csa.demo.52north.org/"

* schannel: next InitializeSecurityContext failed: SEC_E_CERT_EXPIRED (0x80090328)
  - The received certificate has expired.
curl: (35) schannel: next InitializeSecurityContext failed: SEC_E_CERT_EXPIRED
```

The server's TLS certificate has expired. All subsequent tests used `-k` (insecure) to bypass this. **Browsers will refuse to connect entirely until the cert is renewed**, and the Vite proxy will need `secure: false` in its config to reach this server.

#### Finding 2: GET Requests — CORS Works

```
curl.exe -sk -H "Origin: http://localhost:5173" -I "https://csa.demo.52north.org/"

HTTP/1.1 200
Server: nginx/1.27.4
access-control-allow-origin: *
access-control-expose-headers:
vary: Origin
Content-Type: None
```

The server returns `Access-Control-Allow-Origin: *` when an `Origin` header is present. Simple GET requests would work cross-origin from a browser (ignoring the SSL issue).

#### Finding 3: Write Preflight — CORS Fails

```
curl.exe -sk -X OPTIONS \
  -H "Origin: http://localhost:5173" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type, Authorization" \
  -I "https://csa.demo.52north.org/"

HTTP/1.1 200
Server: nginx/1.27.4
allow: OPTIONS, HEAD, GET
access-control-allow-origin: *
access-control-expose-headers:
```

**Missing from the preflight response:**
- `Access-Control-Allow-Methods` — not present (browser needs this to include POST/PUT/DELETE)
- `Access-Control-Allow-Headers` — not present (browser needs this to allow `Content-Type` and `Authorization`)

The `allow` header lists only `OPTIONS, HEAD, GET` — which may also indicate the root endpoint doesn't accept POST, but the CORS headers are missing regardless. **The browser will block all write operations to this server.**

#### 52North Summary

| Capability | Status |
|------------|--------|
| Server reachable | Yes (but SSL cert expired) |
| GET with CORS | Works (`Access-Control-Allow-Origin: *`) |
| POST/PUT/DELETE preflight | **Fails** (missing `Allow-Methods` and `Allow-Headers`) |
| Verdict | **Proxy required for writes; `secure: false` required for SSL** |

---

### OSH SensorHub (`http://45.55.99.236:8080/sensorhub/api`)

#### Finding 1: No CORS Headers Without Origin

```
curl.exe -sI "http://45.55.99.236:8080/sensorhub/api"

HTTP/1.1 200 OK
Content-Type: auto
Content-Length: 0
```

No CORS headers when no `Origin` is sent. This is normal — the server only includes CORS headers when it sees an `Origin` header (standard behavior).

#### Finding 2: GET Requests — Full CORS Support

```
curl.exe -s -H "Origin: http://localhost:5173" -I "http://45.55.99.236:8080/sensorhub/api"

HTTP/1.1 200 OK
Access-Control-Allow-Origin: http://localhost:5173
Vary: Origin
Access-Control-Allow-Credentials: true
Access-Control-Expose-Headers: location,link
Content-Type: auto
```

The server mirrors the requesting origin (not a wildcard `*`), supports credentials, and exposes `location` and `link` headers. This is textbook correct CORS.

#### Finding 3: Write Preflight — Full CORS Support

```
curl.exe -s -X OPTIONS \
  -H "Origin: http://localhost:5173" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type, Authorization" \
  -I "http://45.55.99.236:8080/sensorhub/api"

HTTP/1.1 200 OK
Access-Control-Allow-Origin: http://localhost:5173
Access-Control-Allow-Credentials: true
Access-Control-Max-Age: 1800
Access-Control-Allow-Methods: GET,POST,PUT,DELETE,PATCH,OPTIONS
Access-Control-Allow-Headers: origin,content-type,accept,authorization
Allow: GET, HEAD, POST, PUT, DELETE, TRACE, OPTIONS
```

Every CORS header needed for full CRUD is present:
- `Allow-Methods` includes all HTTP methods we need
- `Allow-Headers` includes `content-type` and `authorization`
- `Allow-Credentials: true` means we can send Basic auth cross-origin
- `Max-Age: 1800` means preflight results are cached for 30 minutes (reduces request overhead)

#### OSH SensorHub Summary

| Capability | Status |
|------------|--------|
| Server reachable | Yes |
| GET with CORS | Works (mirrors origin, supports credentials) |
| POST/PUT/DELETE preflight | **Works** (all methods, headers, and credentials allowed) |
| Verdict | **No proxy technically required — direct cross-origin works** |

---

## Consolidated Findings

| | 52North | OSH SensorHub |
|---|---------|---------------|
| SSL | Expired cert | N/A (HTTP) |
| GET CORS | Works | Works |
| Write CORS preflight | Fails | Works |
| Auth header allowed | No (not in preflight) | Yes |
| Proxy required? | **Yes** (writes + SSL) | No (but recommended for uniformity) |

---

## Recommendations

1. **Keep the Vite proxy in the architecture.** It's required for 52North and gives us a uniform approach for both servers. Removing it for OSH only would mean two different request patterns in the app code.

2. **Add `secure: false` to the 52North proxy config.** Their SSL cert is expired. Without this flag, the Vite proxy's server-side fetch will also reject the connection.

3. **The proxy config should look like:**
   ```js
   server: {
     proxy: {
       '/api/52north': {
         target: 'https://csa.demo.52north.org',
         changeOrigin: true,
         secure: false, // expired SSL cert
         rewrite: (path) => path.replace(/^\/api\/52north/, ''),
       },
       '/api/osh': {
         target: 'http://45.55.99.236:8080/sensorhub/api',
         changeOrigin: true,
         rewrite: (path) => path.replace(/^\/api\/osh/, ''),
       },
     },
   }
   ```

4. **OSH as a fallback.** If the proxy causes issues during development, we can temporarily bypass it for OSH and make direct cross-origin requests. This gives us a working CRUD demo even if proxy configuration takes troubleshooting.

5. **Monitor 52North SSL.** If they renew their cert, we can remove `secure: false`. If the server stays down or unreliable, OSH becomes our primary demo target.

---

## Raw Test Commands (Reproducible)

```powershell
# 52North — basic connectivity (will fail due to expired SSL)
curl.exe -v "https://csa.demo.52north.org/"

# 52North — bypass SSL, check headers
curl.exe -skI "https://csa.demo.52north.org/"

# 52North — CORS on GET
curl.exe -sk -H "Origin: http://localhost:5173" -I "https://csa.demo.52north.org/"

# 52North — CORS preflight for writes
curl.exe -sk -X OPTIONS -H "Origin: http://localhost:5173" -H "Access-Control-Request-Method: POST" -H "Access-Control-Request-Headers: Content-Type, Authorization" -I "https://csa.demo.52north.org/"

# OSH — basic connectivity
curl.exe -sI "http://45.55.99.236:8080/sensorhub/api"

# OSH — CORS on GET
curl.exe -s -H "Origin: http://localhost:5173" -I "http://45.55.99.236:8080/sensorhub/api"

# OSH — CORS preflight for writes
curl.exe -s -X OPTIONS -H "Origin: http://localhost:5173" -H "Access-Control-Request-Method: POST" -H "Access-Control-Request-Headers: Content-Type, Authorization" -I "http://45.55.99.236:8080/sensorhub/api"
```
