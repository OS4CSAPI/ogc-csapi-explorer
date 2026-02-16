/**
 * Thin wrapper around fetch for CSAPI requests.
 * Handles auth headers, JSON parsing, and error formatting.
 */
import { connection } from './state'

export interface ApiResponse<T = any> {
  ok: boolean
  status: number
  statusText: string
  data: T | null
  error?: string
  headers: Record<string, string>
}

export async function apiFetch<T = any>(
  path: string,
  options: RequestInit = {}
): Promise<ApiResponse<T>> {
  const url = connection.baseUrl + path
  const headers: Record<string, string> = {
    ...connection.authHeaders,
    ...(options.headers as Record<string, string> || {}),
  }

  // Default Accept to JSON
  if (!headers['Accept']) {
    headers['Accept'] = 'application/json'
  }

  try {
    const response = await fetch(url, {
      ...options,
      headers,
    })

    const responseHeaders: Record<string, string> = {}
    response.headers.forEach((value, key) => {
      responseHeaders[key] = value
    })

    if (!response.ok) {
      let errorBody = ''
      try {
        errorBody = await response.text()
      } catch { /* ignore */ }
      return {
        ok: false,
        status: response.status,
        statusText: response.statusText,
        data: null,
        error: `${response.status} ${response.statusText}${errorBody ? ': ' + errorBody.substring(0, 500) : ''}`,
        headers: responseHeaders,
      }
    }

    // For DELETE or responses with no body
    const contentType = response.headers.get('content-type') || ''
    if (response.status === 204 || !contentType.includes('json')) {
      const text = await response.text()
      return {
        ok: true,
        status: response.status,
        statusText: response.statusText,
        data: (text ? text : null) as any,
        headers: responseHeaders,
      }
    }

    const data = await response.json()
    return {
      ok: true,
      status: response.status,
      statusText: response.statusText,
      data,
      headers: responseHeaders,
    }
  } catch (err: any) {
    return {
      ok: false,
      status: 0,
      statusText: 'Network Error',
      data: null,
      error: err.message || 'Network request failed',
      headers: {},
    }
  }
}

/**
 * Map resource type keys to their API path segments
 */
const RESOURCE_PATHS: Record<string, string> = {
  systems: '/systems',
  deployments: '/deployments',
  procedures: '/procedures',
  samplingFeatures: '/samplingFeatures',
  properties: '/properties',
  datastreams: '/datastreams',
  observations: '/observations',
  controlStreams: '/controlStreams',
  commands: '/commands',
}

export function getResourcePath(resourceType: string): string {
  return RESOURCE_PATHS[resourceType] || `/${resourceType}`
}

/**
 * Build query string from filter options
 */
export function buildQueryString(params: Record<string, any>): string {
  const parts: string[] = []
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === null || value === '') continue
    if (Array.isArray(value)) {
      parts.push(`${encodeURIComponent(key)}=${encodeURIComponent(value.join(','))}`)
    } else {
      parts.push(`${encodeURIComponent(key)}=${encodeURIComponent(String(value))}`)
    }
  }
  return parts.length > 0 ? '?' + parts.join('&') : ''
}
