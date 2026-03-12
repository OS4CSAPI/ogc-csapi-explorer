/**
 * Origin fallback — tries multiple hostnames for the OSH SensorHub API.
 *
 * Both hostnames point to the same Oracle Cloud VM (129.80.248.53) via
 * different wildcard-DNS providers:
 *   1. sslip.io  — IP encoded in hostname, no account needed
 *   2. DuckDNS   — classic dynamic-DNS subdomain
 *
 * The first successful response wins. Network/DNS errors trigger the
 * next origin; HTTP errors (4xx/5xx) are returned immediately since the
 * server was reachable.
 */

const ORIGINS = [
  'https://129-80-248-53.sslip.io/sensorhub/api',
  'https://os4csapi-osh.duckdns.org/sensorhub/api',
]

const CSAPI_AUTH = 'Basic b3M0Y3NhcGk6b2djMTM0bW0='    // os4csapi:ogc134mm

/**
 * Fetch with automatic origin fallback.
 *
 * @param path   - API path after /sensorhub/api/ (e.g. "systems?limit=10")
 * @param init   - Optional RequestInit overrides (method, headers, body, etc.)
 * @param authHeaders - Optional auth headers; defaults to CSAPI basic auth
 * @returns The first successful Response, or throws if ALL origins fail.
 */
export async function fetchWithFallback(
  path: string,
  init?: RequestInit,
  authHeaders?: Record<string, string>,
): Promise<Response> {
  const auth = authHeaders ?? { Authorization: CSAPI_AUTH }
  let lastError: unknown = null

  for (const origin of ORIGINS) {
    const url = `${origin}/${path}`
    try {
      const resp = await fetch(url, {
        ...init,
        headers: { ...auth, ...((init?.headers as Record<string, string>) ?? {}) },
      })
      // Server reachable — return immediately (even if 4xx/5xx)
      return resp
    } catch (err) {
      // Network/DNS error — try next origin
      lastError = err
    }
  }

  throw new Error(
    `All OSH origins unreachable: ${lastError instanceof Error ? lastError.message : String(lastError)}`,
  )
}

/** Default base URL (first origin). Used where a static URL string is needed. */
export const CSAPI_BASE = ORIGINS[0]

/** Default auth header value. */
export { CSAPI_AUTH }
