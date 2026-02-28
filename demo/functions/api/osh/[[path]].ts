/**
 * Cloudflare Pages Function — reverse proxy for OSH SensorHub.
 *
 * Matches all requests to /api/osh/* and forwards them to the actual
 * OSH server at http://45.55.99.236:8080/sensorhub/api/*, passing
 * through auth headers, query strings, and request bodies.
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
    const target = `http://45.55.99.236:8080/sensorhub/api/${suffix}${qs}`

    // Forward headers (strip host so upstream sees its own)
    const headers = new Headers(request.headers)
    headers.delete('host')

    // Read body as ArrayBuffer for non-GET/HEAD to avoid streaming issues
    let body: ArrayBuffer | null = null
    if (request.method !== 'GET' && request.method !== 'HEAD') {
      body = await request.arrayBuffer()
    }

    const upstream = await fetch(target, {
      method: request.method,
      headers,
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
