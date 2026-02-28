/**
 * Cloudflare Pages Function — reverse proxy for the original OSH SensorHub
 * on DigitalOcean (45.55.99.236:8080).
 *
 * Matches all requests to /api/osh-do/* and forwards them to the actual
 * OSH server, passing through auth headers, query strings, and request bodies.
 *
 * Uses nip.io hostname because Cloudflare Workers block fetch() to raw
 * IP addresses (Error 1003). 45.55.99.236.nip.io resolves to the same IP.
 *
 * This replaces the Vite dev-server proxy for production deployments.
 */

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

    // Build target URL — params.path may be undefined, string, or string[]
    const raw = params.path
    const suffix = Array.isArray(raw) ? raw.join('/') : (raw || '')
    const qs = new URL(request.url).search
    const target = `http://45.55.99.236.nip.io:8080/sensorhub/api/${suffix}${qs}`

    // Forward auth + safe headers from the client
    const fwdHeaders = new Headers()
    const auth = request.headers.get('Authorization')
    if (auth) fwdHeaders.set('Authorization', auth)
    const ct = request.headers.get('Content-Type')
    if (ct) fwdHeaders.set('Content-Type', ct)
    const accept = request.headers.get('Accept')
    if (accept) fwdHeaders.set('Accept', accept)

    // Read body as ArrayBuffer for non-GET/HEAD to avoid streaming issues
    let body: ArrayBuffer | null = null
    if (request.method !== 'GET' && request.method !== 'HEAD') {
      body = await request.arrayBuffer()
    }

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

    return new Response(upstream.body, {
      status: upstream.status,
      statusText: upstream.statusText,
      headers: responseHeaders,
    })
  } catch (err: any) {
    return new Response(
      JSON.stringify({ error: String(err?.message || err), stack: String(err?.stack || '') }),
      { status: 502, headers: { 'Content-Type': 'application/json', ...CORS_HEADERS } },
    )
  }
}
