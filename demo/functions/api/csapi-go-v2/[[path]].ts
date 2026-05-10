/**
 * Cloudflare Pages Function — reverse proxy for Connected Systems Go server (v2).
 *
 * Matches all requests to /api/csapi-go-v2/* and forwards them to
 * https://129-80-248-53.sslip.io/csapi-go-v2/*, passing through headers and bodies.
 *
 * Backend pinned to SomethingCreativeStudios/connected-systems-go @ d14d16d3.
 */

const CORS_HEADERS: Record<string, string> = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, PUT, PATCH, DELETE, OPTIONS',
  'Access-Control-Allow-Headers': 'Authorization, Content-Type, Accept',
  'Access-Control-Max-Age': '86400',
}

const UPSTREAM_HOST = '129-80-248-53.sslip.io'
const UPSTREAM_PREFIX = '/csapi-go-v2'
const PROXY_PREFIX = '/api/csapi-go-v2'

/**
 * Rewrite an upstream redirect Location header so the client stays inside
 * this proxy. Handles two known upstream defects:
 *   1. Absolute URL on the same host with the `/csapi-go-v2` prefix preserved
 *      (normal case): rewrite host+prefix to `/api/csapi-go-v2`.
 *   2. Absolute URL on the same host with the prefix STRIPPED (the
 *      `/collections/{id}/items` 307 bug): re-attach the prefix mapped to
 *      `/api/csapi-go-v2`.
 *   3. Relative path: forward as-is when it already starts with `/api/...`,
 *      otherwise prepend `/api/csapi-go-v2`.
 */
function rewriteLocation(loc: string, requestUrl: string): string | null {
  try {
    const reqOrigin = new URL(requestUrl).origin
    let target: URL
    try {
      target = new URL(loc)
    } catch {
      // Relative redirect — turn into an absolute URL we can reason about
      target = new URL(loc, requestUrl)
    }
    if (target.hostname === UPSTREAM_HOST) {
      let path = target.pathname
      if (path.startsWith(UPSTREAM_PREFIX)) {
        path = PROXY_PREFIX + path.slice(UPSTREAM_PREFIX.length)
      } else {
        // Upstream stripped its own prefix — re-attach it to keep the client on us
        path = PROXY_PREFIX + path
      }
      return reqOrigin + path + target.search + target.hash
    }
    // Different host — leave as-is (upstream is genuinely sending elsewhere)
    return loc
  } catch {
    return null
  }
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
    const target = `https://129-80-248-53.sslip.io/csapi-go-v2/${suffix}${qs}`

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

    // redirect: 'manual' so we can rewrite the Location header.
    // The csapi-go-v2 backend emits 307 redirects from /collections/{id}/items
    // to a host-root path that drops the /csapi-go-v2 prefix (upstream defect),
    // which makes any client following the redirect 404. Rewrite the Location
    // back to the proxy-relative form before returning to the client.
    const upstream = await fetch(target, {
      method: request.method,
      headers: fwdHeaders,
      body,
      redirect: 'manual',
    })

    // Forward response with CORS headers
    const responseHeaders = new Headers(upstream.headers)
    for (const [k, v] of Object.entries(CORS_HEADERS)) {
      responseHeaders.set(k, v)
    }

    // Rewrite Location header on 3xx responses so the client follows back
    // through this proxy instead of jumping to a malformed upstream URL.
    if (upstream.status >= 300 && upstream.status < 400) {
      const loc = upstream.headers.get('Location')
      if (loc) {
        const rewritten = rewriteLocation(loc, request.url)
        if (rewritten) {
          responseHeaders.set('Location', rewritten)
        }
      }
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
