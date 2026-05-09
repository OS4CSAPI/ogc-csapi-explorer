/**
 * Cloudflare Pages Function — reverse proxy for the 52°North
 * connected-systems-pygeoapi server deployed on Oracle Cloud (Phase 9).
 *
 * Matches all requests to /api/csapi-pygeoapi/* and forwards them to
 * https://129-80-248-53.sslip.io/csapi-pygeoapi/*, passing through headers
 * and bodies. No authentication is required by the upstream server.
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
    const target = `https://129-80-248-53.sslip.io/csapi-pygeoapi/${suffix}${qs}`

    // Only forward specific headers
    const fwdHeaders = new Headers()
    fwdHeaders.set('Host', '129-80-248-53.sslip.io')
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
