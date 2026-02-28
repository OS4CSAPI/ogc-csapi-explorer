/**
 * Cloudflare Pages Function — reverse proxy for 52North CSA Demo.
 *
 * Matches all requests to /api/52north/* and forwards them to
 * https://csa.demo.52north.org/*, passing through headers and bodies.
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
  const target = `https://csa.demo.52north.org/${pathSegments}${url.search}`

  const headers = new Headers(request.headers)
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

    const responseHeaders = new Headers(upstream.headers)
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
