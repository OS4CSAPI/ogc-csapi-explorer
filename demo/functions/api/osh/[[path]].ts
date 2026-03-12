/**
 * Cloudflare Pages Function — reverse proxy for OSH SensorHub.
 *
 * Matches all requests to /api/osh/* and forwards them to the actual
 * OSH server on Oracle Cloud (Caddy reverse proxy with basic auth +
 * auto-HTTPS), passing through query strings and request bodies.
 *
 * Uses a primary/fallback hostname pattern so the proxy survives a
 * DNS outage on either wildcard-DNS provider:
 *   1. sslip.io  — IP encoded in hostname, no account needed
 *   2. DuckDNS   — classic dynamic-DNS subdomain
 *
 * The client must send valid Basic auth credentials (os4csapi:ogc134mm)
 * in the Authorization header. The proxy validates them before forwarding
 * to the upstream Caddy server.
 *
 * This replaces the Vite dev-server proxy for production deployments.
 */

// ── Origin hostnames (try in order) ─────────────────────────────────
const ORIGINS = [
  'https://129-80-248-53.sslip.io',      // primary — IP-based wildcard DNS
  'https://os4csapi-osh.duckdns.org',     // fallback — dynamic DNS
]

// Accepted client credentials — any of these will be allowed through the proxy.
// The proxy always forwards UPSTREAM_AUTH to Caddy regardless of which credential the client used.
const VALID_CREDENTIALS: string[] = [
  'Basic ' + btoa('os4csapi:ogc134mm'),
  'Basic ' + btoa('wstp:vienna'),
]
const UPSTREAM_AUTH = 'Basic ' + btoa('os4csapi:ogc134mm')

const CORS_HEADERS: Record<string, string> = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, PUT, PATCH, DELETE, OPTIONS',
  'Access-Control-Allow-Headers': 'Authorization, Content-Type, Accept',
  'Access-Control-Max-Age': '86400',
}

export const onRequest: PagesFunction = async (context) => {
  try {
    const { params, request } = context

    // Handle CORS preflight immediately
    if (request.method === 'OPTIONS') {
      return new Response(null, { status: 204, headers: CORS_HEADERS })
    }

    // --- Validate client credentials ---
    const clientAuth = request.headers.get('Authorization') || ''
    if (!VALID_CREDENTIALS.includes(clientAuth)) {
      return new Response(
        JSON.stringify({ error: 'Unauthorized — invalid or missing credentials.' }),
        {
          status: 401,
          headers: {
            'Content-Type': 'application/json',
            'WWW-Authenticate': 'Basic realm="OSH SensorHub"',
            ...CORS_HEADERS,
          },
        },
      )
    }

    // Build path suffix + query string (shared across attempts)
    const raw = params.path
    const suffix = Array.isArray(raw) ? raw.join('/') : (raw || '')
    const qs = new URL(request.url).search

    // Forward headers (shared across attempts)
    const fwdHeaders = new Headers()
    fwdHeaders.set('Authorization', UPSTREAM_AUTH)
    const ct = request.headers.get('Content-Type')
    if (ct) fwdHeaders.set('Content-Type', ct)
    const accept = request.headers.get('Accept')
    if (accept) fwdHeaders.set('Accept', accept)

    // Read body once (shared across attempts — only for mutating requests)
    let body: ArrayBuffer | null = null
    if (request.method !== 'GET' && request.method !== 'HEAD') {
      body = await request.arrayBuffer()
    }

    // --- Try each origin in order; fall through on network errors ---
    let lastError: any = null
    for (const origin of ORIGINS) {
      const target = `${origin}/sensorhub/api/${suffix}${qs}`
      try {
        const upstream = await fetch(target, {
          method: request.method,
          headers: fwdHeaders,
          body,
        })

        // Forward response with CORS headers
        const responseHeaders = new Headers(upstream.headers)
        for (const [k, v] of Object.entries(CORS_HEADERS)) {
          responseHeaders.set(k, v)
        }
        responseHeaders.set('X-Origin-Used', origin)

        return new Response(upstream.body, {
          status: upstream.status,
          statusText: upstream.statusText,
          headers: responseHeaders,
        })
      } catch (err) {
        // Network/DNS error — try next origin
        lastError = err
      }
    }

    // All origins failed
    return new Response(
      JSON.stringify({
        error: `All origins unreachable: ${String(lastError?.message || lastError)}`,
        origins: ORIGINS,
      }),
      { status: 502, headers: { 'Content-Type': 'application/json', ...CORS_HEADERS } },
    )
  } catch (err: any) {
    return new Response(
      JSON.stringify({ error: String(err?.message || err), stack: String(err?.stack || '') }),
      { status: 502, headers: { 'Content-Type': 'application/json', ...CORS_HEADERS } },
    )
  }
}
