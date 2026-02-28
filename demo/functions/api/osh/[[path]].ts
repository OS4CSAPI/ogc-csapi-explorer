/**
 * Cloudflare Pages Function — reverse proxy for OSH SensorHub.
 *
 * Matches all requests to /api/osh/* and forwards them to the actual
 * OSH server at http://45.55.99.236:8080/sensorhub/api/*, passing
 * through auth headers, query strings, and request bodies.
 *
 * This replaces the Vite dev-server proxy for production deployments.
 */
export const onRequest: PagesFunction = async (context) => {
  const { params, request } = context

  // Handle CORS preflight immediately — don't forward to upstream
  if (request.method === 'OPTIONS') {
    return new Response(null, {
      status: 204,
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, PUT, PATCH, DELETE, OPTIONS',
        'Access-Control-Allow-Headers': 'Authorization, Content-Type, Accept',
        'Access-Control-Max-Age': '86400',
      },
    })
  }

  const pathSegments = (params.path as string[]).join('/')
  const url = new URL(request.url)
  const target = `http://45.55.99.236:8080/sensorhub/api/${pathSegments}${url.search}`

  // Forward the original request (method, headers, body)
  const headers = new Headers(request.headers)
  // Remove host header so the upstream server sees its own host
  headers.delete('host')

  const fetchOptions: RequestInit = {
    method: request.method,
    headers,
    body: request.method !== 'GET' && request.method !== 'HEAD' ? request.body : undefined,
    // @ts-ignore — Cloudflare Workers supports duplex
    duplex: request.method !== 'GET' && request.method !== 'HEAD' ? 'half' : undefined,
  }

  try {
    const upstream = await fetch(target, fetchOptions)

    // Build response, forwarding status and body
    const responseHeaders = new Headers(upstream.headers)
    // Set CORS headers for the deployed frontend
    responseHeaders.set('Access-Control-Allow-Origin', '*')
    responseHeaders.set('Access-Control-Allow-Methods', 'GET, POST, PUT, PATCH, DELETE, OPTIONS')
    responseHeaders.set('Access-Control-Allow-Headers', 'Authorization, Content-Type, Accept')

    return new Response(upstream.body, {
      status: upstream.status,
      statusText: upstream.statusText,
      headers: responseHeaders,
    })
  } catch (err: any) {
    return new Response(JSON.stringify({ error: err.message }), {
      status: 502,
      headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' },
    })
  }
}
