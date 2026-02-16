/**
 * Thin wrapper around fetch for CSAPI requests.
 * Handles auth headers, JSON parsing, and error formatting.
 *
 * URL construction is handled by csapi-bridge.ts (which uses the library's
 * CSAPIQueryBuilder). This module just handles the HTTP transport layer.
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

/**
 * Fetch a CSAPI resource. The path should be a relative path produced by
 * the CSAPIQueryBuilder (e.g., `/systems?limit=10`). The proxy base URL
 * from the connection state is automatically prepended.
 */
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
