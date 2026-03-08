<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { apiFetch } from '../api'
import { connection } from '../state'
import { getListUrl, getNestedListUrl, getContentType, parseCollectionResponse } from '../csapi-bridge'
import type { QueryOptions } from '@csapi/ogc-api/csapi/model'
import type { DateTimeParameter } from '@csapi/shared/models'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import InputNumber from 'primevue/inputnumber'
import DatePicker from 'primevue/datepicker'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Message from 'primevue/message'
import ProgressSpinner from 'primevue/progressspinner'

/**
 * Friendly guidance for resource types that some servers only expose as nested
 * sub-resources. Each entry includes a brief explanation of the server
 * limitation and a concrete navigation hint so users know where to look.
 */
const NESTED_RESOURCE_HINTS: Record<string, { explanation: string; hint: string }> = {
  commands: {
    explanation: 'This server requires commands to be accessed through their parent control stream (e.g., GET /controlstreams/{id}/commands) rather than as a standalone collection (GET /commands). This is a common server-side routing limitation — the CSAPI spec supports both patterns, but not all servers implement the top-level route.',
    hint: 'To browse commands: navigate to Control Streams → select a control stream → view its detail page to see associated commands.',
  },
  observations: {
    explanation: 'This server requires observations to be accessed through their parent datastream (e.g., GET /datastreams/{id}/observations) rather than as a standalone collection (GET /observations). Some servers only expose observations as nested resources under their datastream.',
    hint: 'To browse observations: navigate to Datastreams → select a datastream → view its detail page to see associated observations.',
  },
}

const props = defineProps<{
  resourceType: string
  parentType?: string | null
  parentId?: string | null
  parentRelation?: string | null
}>()

const emit = defineEmits<{
  (e: 'view', resource: any): void
  (e: 'edit', resource: any): void
}>()

/** Whether we're showing nested/related resources (e.g. subsystems of a system) */
const isNested = computed(() => !!(props.parentType && props.parentId && props.parentRelation))

/** Build the list URL — uses the nested builder when parent context is present */
function buildListUrl(options: QueryOptions): string {
  if (isNested.value) {
    return getNestedListUrl(props.parentType!, props.parentId!, props.parentRelation!, options)
  }
  return getListUrl(props.resourceType, options)
}

// Filter state
const limit = ref(10)
const offset = ref(0)
const q = ref('')
const sortBy = ref('')
const sortOrder = ref<'asc' | 'desc' | ''>('')
const dtStart = ref<Date | null>(null)
const dtEnd = ref<Date | null>(null)

// Reset offset when limit changes so pagination stays coherent
watch(limit, () => {
  offset.value = 0
})

/** Build OGC API datetime parameter from the two date pickers.
 *  Returns a DateTimeParameter object (Date or {start}/{end}/{start,end})
 *  that the library's formatDateTimeParameter() can serialize. */
const datetimeParam = computed((): DateTimeParameter | null => {
  if (dtStart.value && dtEnd.value) return { start: dtStart.value, end: dtEnd.value }
  if (dtStart.value) return { start: dtStart.value }
  if (dtEnd.value) return { end: dtEnd.value }
  return null
})

/** Human-readable preview of the datetime filter for the UI */
const datetimePreview = computed(() => {
  const fmt = (d: Date) => d.toISOString()
  if (dtStart.value && dtEnd.value) return `${fmt(dtStart.value)}/${fmt(dtEnd.value)}`
  if (dtStart.value) return `${fmt(dtStart.value)}/..`
  if (dtEnd.value) return `../${fmt(dtEnd.value)}`
  return ''
})

/**
 * Apply the temporal filter to the correct query option for the resource type.
 * Part 1 types (systems, deployments, etc.) use `datetime`.
 * Observations use `phenomenonTime`. Commands use `issueTime`.
 * Datastreams use `phenomenonTime`. Others fall back to `datetime`.
 */
function applyTemporalFilter(options: Record<string, any>, resourceType: string, dt: DateTimeParameter) {
  switch (resourceType) {
    case 'observations':
    case 'datastreams':
      options.phenomenonTime = dt
      break
    case 'commands':
      options.issueTime = dt
      break
    default:
      options.datetime = dt
      break
  }
}

/** Label showing which query parameter the temporal filter maps to */
const temporalParamName = computed(() => {
  switch (props.resourceType) {
    case 'observations':
    case 'datastreams': return 'phenomenonTime'
    case 'commands': return 'issueTime'
    default: return 'datetime'
  }
})

// Pagination
const cursorNext = ref<string | null>(null)
const cursorPrev = ref<string | null>(null)
const paginationMode = ref<'offset' | 'cursor'>('offset')

// Data
const items = ref<any[]>([])
const loading = ref(false)
const error = ref('')
const numberMatched = ref<number | null>(null)
const numberReturned = ref<number | null>(null)
const totalCount = ref<number | null>(null)
const rawResponse = ref<any>(null)

/** Details about which client-side fallbacks were triggered (empty = no fallback) */
const clientSideFallbackDetails = ref<string[]>([])

/**
 * Fetch the total number of matching resources (same filters, no limit/offset).
 * Fires in parallel with the paginated request so it doesn't slow things down.
 * Only used when the server doesn't provide numberMatched in the response.
 */
async function fetchTotalCount(): Promise<number | null> {
  try {
    const countOptions: QueryOptions = { limit: 1000 }
    if (q.value) countOptions.q = q.value
    if (datetimeParam.value) applyTemporalFilter(countOptions, props.resourceType, datetimeParam.value)
    const countPath = buildListUrl(countOptions)
    const acceptType = getContentType(props.resourceType)
    const countRes = await apiFetch(countPath, {
      headers: { 'Accept': acceptType },
    })
    if (!countRes.ok || !countRes.data) return null
    const parsed = parseCollectionResponse(countRes.data)
    let countItems = parsed.items as any[]

    // Client-side keyword filter fallback for the total count too
    if (q.value && countItems.length > 0) {
      const keyword = q.value.toLowerCase()
      const filtered = countItems.filter((item: any) => {
        const fields = [
          item?.id,
          item?.properties?.name,
          item?.properties?.title,
          item?.properties?.description,
          item?.properties?.uniqueId,
          item?.name,
          item?.title,
          item?.description,
        ]
        return fields.some(f => typeof f === 'string' && f.toLowerCase().includes(keyword))
      })
      if (filtered.length < countItems.length) {
        countItems = filtered
      }
    }

    return countItems.length
  } catch {
    return null
  }
}

async function fetchResources(cursorUrl?: string) {
  loading.value = true
  error.value = ''
  items.value = []
  rawResponse.value = null
  totalCount.value = null

  try {
    let path: string
    if (cursorUrl) {
      // Cursor-based pagination: use the link path directly
      path = cursorUrl
    } else {
      // Build query options using the library's typed QueryOptions interface
      const options: QueryOptions = {}
      if (limit.value) options.limit = limit.value
      if (paginationMode.value === 'offset' && offset.value > 0) options.offset = offset.value
      if (q.value) options.q = q.value
      if (sortBy.value) options.sortBy = sortBy.value
      if (sortOrder.value) options.sortOrder = sortOrder.value
      if (datetimeParam.value) applyTemporalFilter(options, props.resourceType, datetimeParam.value)

      // Use CSAPIQueryBuilder via bridge to construct the URL
      path = buildListUrl(options)
    }

    // Fire total-count request in parallel (will be used if server omits numberMatched)
    const totalCountPromise = fetchTotalCount()

    const acceptType = getContentType(props.resourceType)
    const res = await apiFetch(path, {
      headers: { 'Accept': acceptType },
    })
    if (!res.ok) {
      // Provide a friendlier, more informative message for 400 errors on
      // resource types that are typically nested (commands under controlstreams, etc.)
      if (res.status === 400) {
        if (isNested.value) {
          // Nested endpoint 400 (e.g. /deployments/{id}/systems) — likely a
          // transient server error, not a missing capability.
          error.value = `Server returned an error (400) for this nested request. This may be a temporary issue — try refreshing or navigating back and returning.\n\n` +
            `(${res.statusText || 'Bad Request'})`
        } else {
          const parentHint = NESTED_RESOURCE_HINTS[props.resourceType]
          if (parentHint) {
            error.value = `⚠️ Server limitation: ${props.resourceType} are not available as a top-level collection on this server.\n\n` +
              `${parentHint.explanation}\n\n` +
              `${parentHint.hint}\n\n` +
              `(Server response: ${res.status} ${res.statusText})`
          } else {
            error.value = `Server rejected the request (${res.status}). This resource type may not be supported by this server.`
          }
        }
      } else {
        error.value = res.error || 'Failed to fetch resources'
      }
      return
    }

    rawResponse.value = res.data

    // Use the library's parseCollectionResponse to normalize both envelope formats
    // (FeatureCollection and items envelope) into a consistent structure
    try {
      const parsed = parseCollectionResponse(res.data)
      let resultItems = parsed.items as any[]
      clientSideFallbackDetails.value = []

      // --- Client-side fallback for servers that ignore query parameters ---
      // Some servers (e.g., OSH) ignore ?q= and ?limit= entirely.
      // Detect this and apply filters locally so the UI stays correct.

      // 1) Client-side keyword filter fallback
      if (q.value && !cursorUrl && resultItems.length > 0) {
        const keyword = q.value.toLowerCase()
        const filtered = resultItems.filter((item: any) => {
          // Match against common text fields: id, name, title, description, uniqueId
          const fields = [
            item?.id,
            item?.properties?.name,
            item?.properties?.title,
            item?.properties?.description,
            item?.properties?.uniqueId,
            item?.name,
            item?.title,
            item?.description,
          ]
          return fields.some(f => typeof f === 'string' && f.toLowerCase().includes(keyword))
        })
        // Only apply if it actually reduced the set (otherwise the server may
        // have already filtered and the keyword just doesn't appear in our
        // checked fields — we don't want a false negative)
        if (filtered.length < resultItems.length) {
          const serverCount = resultItems.length
          resultItems = filtered
          clientSideFallbackDetails.value.push(
            `q="${q.value}": server returned ${serverCount} items unfiltered — reduced to ${filtered.length} client-side`
          )
        }
      }

      // 2) Client-side limit enforcement
      if (limit.value && !cursorUrl && resultItems.length > limit.value) {
        const serverCount = resultItems.length
        resultItems = resultItems.slice(0, limit.value)
        clientSideFallbackDetails.value.push(
          `limit=${limit.value}: server returned ${serverCount} items — truncated client-side`
        )
      }

      items.value = resultItems
      numberReturned.value = resultItems.length

      // Use server-provided total if available, otherwise await our parallel count
      if (parsed.numberMatched != null) {
        numberMatched.value = parsed.numberMatched
      } else {
        const counted = await totalCountPromise
        numberMatched.value = counted
      }

      // Extract pagination links from the normalized response
      cursorNext.value = null
      cursorPrev.value = null
      for (const link of parsed.links) {
        if (link.rel === 'next' && link.href) {
          cursorNext.value = extractProxyPath(link.href)
        }
        if (link.rel === 'prev' && link.href) {
          cursorPrev.value = extractProxyPath(link.href)
        }
      }
    } catch {
      // Fallback: if parseCollectionResponse fails (unexpected format),
      // try to display raw data
      if (Array.isArray(res.data)) {
        items.value = res.data
      } else {
        items.value = []
      }
      const counted = await totalCountPromise
      numberMatched.value = counted
      numberReturned.value = items.value.length
    }
  } catch (err: any) {
    error.value = err.message || 'Request failed'
  } finally {
    loading.value = false
  }

  // --- Deployments: recursively fetch subdeployments so nested ones appear ---
  // Only for top-level deployment lists (not already viewing a nested context).
  if (props.resourceType === 'deployments' && !isNested.value && items.value.length > 0) {
    await fetchNestedDeployments()
  }

  // --- Systems: recursively fetch subsystems so nested ones appear ---
  if (props.resourceType === 'systems' && !isNested.value && items.value.length > 0) {
    await fetchNestedSystems()
  }
}

/**
 * Recursively fetch subdeployments for each item in the list and append
 * nested ones that aren't already visible.  Adds a depth/indent hint so the
 * template can visually differentiate nesting levels.
 */
async function fetchNestedDeployments() {
  const seenIds = new Set(items.value.map((it: any) => it?.id || it?.properties?.id))
  const acceptType = getContentType('deployments')
  // Cap the total number of nested items to prevent runaway expansion on
  // servers with very wide/deep hierarchies.
  const MAX_NESTED = 200
  let nestedCount = 0

  async function fetchSubs(parentId: string, depth: number): Promise<any[]> {
    if (depth > 8 || nestedCount >= MAX_NESTED) return []
    try {
      const res = await apiFetch(`/deployments/${parentId}/subdeployments?limit=50`, {
        headers: { Accept: acceptType },
      })
      if (!res.ok || !res.data) return []
      const parsed = parseCollectionResponse(res.data)
      const subs = parsed.items as any[]
      const results: any[] = []
      for (const sub of subs) {
        if (nestedCount >= MAX_NESTED) break
        const subId = sub?.id || sub?.properties?.id
        if (!subId || seenIds.has(subId)) continue
        seenIds.add(subId)
        nestedCount++
        // Tag with nesting depth for display
        sub._nestingDepth = depth
        results.push(sub)
        results.push(...await fetchSubs(subId, depth + 1))
      }
      return results
    } catch { return [] }
  }

  // Interleave nested items immediately after each parent so hierarchy
  // reads top-down even when there are multiple top-level deployments.
  const topLevel = [...items.value]
  const interleaved: any[] = []
  for (const item of topLevel) {
    interleaved.push(item)
    const id = item?.id || item?.properties?.id
    if (id) interleaved.push(...await fetchSubs(id, 1))
  }
  if (interleaved.length > topLevel.length) {
    items.value = interleaved
    // Update counts to reflect the full hierarchy
    numberReturned.value = items.value.length
    numberMatched.value = items.value.length
  }
}

/**
 * Recursively fetch subsystems for each item in the list and interleave
 * nested ones directly after their parent.  Mirrors fetchNestedDeployments.
 */
async function fetchNestedSystems() {
  const seenIds = new Set(items.value.map((it: any) => it?.id || it?.properties?.id))
  const acceptType = getContentType('systems')
  const MAX_NESTED = 200
  let nestedCount = 0

  async function fetchSubs(parentId: string, depth: number): Promise<any[]> {
    if (depth > 5 || nestedCount >= MAX_NESTED) return []
    try {
      const res = await apiFetch(`/systems/${parentId}/subsystems?limit=50`, {
        headers: { Accept: acceptType },
      })
      if (!res.ok || !res.data) return []
      const parsed = parseCollectionResponse(res.data)
      const subs = parsed.items as any[]
      const results: any[] = []
      for (const sub of subs) {
        if (nestedCount >= MAX_NESTED) break
        const subId = sub?.id || sub?.properties?.id
        if (!subId || seenIds.has(subId)) continue
        seenIds.add(subId)
        nestedCount++
        sub._nestingDepth = depth
        results.push(sub)
        results.push(...await fetchSubs(subId, depth + 1))
      }
      return results
    } catch { return [] }
  }

  const topLevel = [...items.value]
  const interleaved: any[] = []
  for (const item of topLevel) {
    interleaved.push(item)
    const id = item?.id || item?.properties?.id
    if (id) interleaved.push(...await fetchSubs(id, 1))
  }
  if (interleaved.length > topLevel.length) {
    items.value = interleaved
    numberReturned.value = items.value.length
    numberMatched.value = items.value.length
  }
}

function extractProxyPath(absoluteUrl: string): string {
  // The server returns absolute URLs like https://os4csapi-osh.duckdns.org/sensorhub/api/systems?offset=10
  // connection.baseUrl is like https://os4csapi-osh.duckdns.org/sensorhub/api (via proxy or direct)
  // We need to strip the origin AND the base path prefix, keeping only the
  // resource path + query (e.g., /systems?offset=10) that apiFetch can use.
  try {
    const url = new URL(absoluteUrl)
    const fullPath = url.pathname + url.search

    // Try to strip the server's base path prefix to avoid double-pathing
    // e.g., /sensorhub/api/systems → /systems
    if (connection.baseUrl) {
      try {
        const base = new URL(connection.baseUrl)
        if (fullPath.startsWith(base.pathname)) {
          return fullPath.substring(base.pathname.length) || '/'
        }
      } catch { /* ignore */ }
    }
    return fullPath
  } catch {
    return absoluteUrl
  }
}

/** True when there are more results beyond the current page */
const hasMoreResults = computed(() => {
  // If server told us total count, use that
  if (numberMatched.value != null) {
    return offset.value + (numberReturned.value ?? items.value.length) < numberMatched.value
  }
  // Fallback: if we got exactly `limit` items, there may be more
  return items.value.length >= limit.value
})

function refresh() {
  cursorNext.value = null
  cursorPrev.value = null
  fetchResources()
}

function nextPage() {
  if (paginationMode.value === 'cursor' && cursorNext.value) {
    fetchResources(cursorNext.value)
  } else {
    offset.value += limit.value
    fetchResources()
  }
}

function prevPage() {
  if (paginationMode.value === 'cursor' && cursorPrev.value) {
    fetchResources(cursorPrev.value)
  } else {
    offset.value = Math.max(0, offset.value - limit.value)
    fetchResources()
  }
}

function getDisplayId(item: any): string {
  return item?.id || item?.properties?.id || item?.['@id'] || '—'
}

function getDisplayTitle(item: any): string {
  return item?.properties?.name || item?.properties?.title || item?.name || item?.title || item?.properties?.description?.substring(0, 60) || '—'
}

function getDisplayType(item: any): string {
  return item?.type || item?.properties?.featureType || ''
}

// Fetch on mount and when resource type or parent context changes
watch(
  () => [props.resourceType, props.parentType, props.parentId, props.parentRelation],
  () => {
    offset.value = 0
    cursorNext.value = null
    cursorPrev.value = null
    fetchResources()
  },
  { immediate: true }
)
</script>

<template>
  <div class="resource-list">
    <!-- Filters -->
    <div class="filters" @keydown.enter="refresh">
      <div class="filter-row">
        <div class="filter-item">
          <label>Limit</label>
          <InputNumber v-model="limit" :min="1" :max="1000" class="w-sm" />
        </div>
        <div class="filter-item">
          <label>Search (q)</label>
          <InputText v-model="q" placeholder="free text search" class="w-md" />
        </div>
        <div class="filter-item">
          <label>Sort by</label>
          <InputText v-model="sortBy" placeholder="e.g. resultTime" class="w-md" />
        </div>
        <div class="filter-item">
          <label>Order</label>
          <Button
            :label="sortOrder || 'default'"
            size="small"
            severity="secondary"
            @click="sortOrder = sortOrder === 'asc' ? 'desc' : sortOrder === 'desc' ? '' : 'asc'"
            style="min-width: 70px"
          />
        </div>
        <div class="filter-item">
          <label>Start date/time</label>
          <DatePicker
            v-model="dtStart"
            showTime
            hourFormat="24"
            showIcon
            showButtonBar
            dateFormat="yy-mm-dd"
            placeholder="Start"
            class="w-dt"
          />
        </div>
        <div class="filter-item">
          <label>End date/time</label>
          <DatePicker
            v-model="dtEnd"
            showTime
            hourFormat="24"
            showIcon
            showButtonBar
            dateFormat="yy-mm-dd"
            placeholder="End"
            class="w-dt"
          />
        </div>
        <div v-if="datetimePreview" class="filter-item datetime-preview">
          <label>{{ temporalParamName }}</label>
          <code class="dt-value">{{ datetimePreview }}</code>
        </div>
      </div>
      <div class="filter-actions">
        <Button label="Fetch" icon="pi pi-search" size="small" @click="refresh" :loading="loading" />
        <div class="pagination-toggle">
          <label>Pagination:</label>
          <Button
            :label="paginationMode === 'offset' ? 'Offset' : 'Cursor'"
            size="small"
            severity="secondary"
            @click="paginationMode = paginationMode === 'offset' ? 'cursor' : 'offset'"
          />
        </div>
      </div>
    </div>

    <!-- Error -->
    <Message v-if="error" :severity="error.startsWith('⚠️ Server limitation') ? 'warn' : 'error'" :closable="false" class="mt-3">
      <span style="white-space: pre-line">{{ error }}</span>
    </Message>

    <!-- Loading -->
    <div v-if="loading" class="loading">
      <ProgressSpinner style="width: 30px; height: 30px" />
      <span>Loading...</span>
    </div>

    <!-- Results info -->
    <div v-if="!loading && items.length > 0" class="results-info">
      <span>Showing {{ numberReturned ?? items.length }} results</span>
      <span v-if="numberMatched != null"> of <strong>{{ numberMatched }}</strong> total</span>
      <span v-if="items.some((it: any) => it._nestingDepth)"> (incl. {{ props.resourceType === 'systems' ? 'subsystems' : 'subdeployments' }})</span>
      <span v-else-if="paginationMode === 'offset'"> (offset: {{ offset }})</span>
    </div>

    <!-- Client-side fallback warning -->
    <Message v-if="!loading && clientSideFallbackDetails.length" severity="warn" :closable="false" class="mt-2">
      <div>Server ignored query parameters — results corrected client-side:</div>
      <ul class="mt-1 mb-0 pl-4" style="list-style: disc;">
        <li v-for="(detail, i) in clientSideFallbackDetails" :key="i">{{ detail }}</li>
      </ul>
    </Message>

    <!-- Data Table -->
    <DataTable
      v-if="!loading && items.length > 0"
      :value="items"
      stripedRows
      size="small"
      class="mt-2"
    >
      <Column header="ID" style="min-width: 120px">
        <template #body="{ data }">
          <code class="id-cell">{{ getDisplayId(data) }}</code>
        </template>
      </Column>
      <Column header="Name / Title" style="min-width: 200px">
        <template #body="{ data }">
          <span v-if="data._nestingDepth" :style="{ paddingLeft: (data._nestingDepth * 16) + 'px', opacity: 0.5 }">└─</span>
          {{ getDisplayTitle(data) }}
        </template>
      </Column>
      <Column header="Type" style="min-width: 100px">
        <template #body="{ data }">
          <span class="type-cell">{{ getDisplayType(data) }}</span>
        </template>
      </Column>
      <Column header="Actions" style="width: 160px">
        <template #body="{ data }">
          <div class="action-buttons">
            <Button icon="pi pi-eye" size="small" severity="info" text @click="emit('view', data)" title="View detail" />
            <Button icon="pi pi-pencil" size="small" severity="warning" text @click="emit('edit', data)" title="Edit" />
          </div>
        </template>
      </Column>
    </DataTable>

    <!-- Empty state -->
    <div v-if="!loading && !error && items.length === 0 && rawResponse !== null" class="empty-state">
      <i class="pi pi-inbox"></i>
      <p>No resources found.</p>
    </div>

    <!-- Pagination controls -->
    <div v-if="!loading && items.length > 0" class="pagination">
      <Button
        label="Previous"
        icon="pi pi-arrow-left"
        size="small"
        severity="secondary"
        :disabled="paginationMode === 'offset' ? offset === 0 : !cursorPrev"
        @click="prevPage"
      />
      <Button
        label="Next"
        icon="pi pi-arrow-right"
        iconPos="right"
        size="small"
        severity="secondary"
        :disabled="paginationMode === 'cursor' ? !cursorNext : !hasMoreResults"
        @click="nextPage"
      />
    </div>

    <!-- Raw response toggle -->
    <details v-if="rawResponse" class="raw-section">
      <summary>Raw Response</summary>
      <pre class="raw-json">{{ JSON.stringify(rawResponse, null, 2) }}</pre>
    </details>
  </div>
</template>

<style scoped>
.resource-list { display: flex; flex-direction: column; gap: 0.5rem; }
.filters { background: #f8fafc; padding: 0.75rem; border-radius: 6px; border: 1px solid #e2e8f0; }
.filter-row { display: flex; flex-wrap: wrap; gap: 0.75rem; margin-bottom: 0.5rem; }
.filter-item { display: flex; flex-direction: column; gap: 0.15rem; }
.filter-item label { font-size: 0.75rem; font-weight: 600; color: #64748b; }
.w-sm { width: 90px; }
.w-sm :deep(.p-inputnumber-input) { width: 90px; }
.w-md { width: 180px; }
.w-dt { width: 210px; }
.w-dt :deep(.p-datepicker-input) { font-size: 0.8rem; }
.datetime-preview { justify-content: center; }
.dt-value { font-size: 0.7rem; color: #475569; background: #e2e8f0; padding: 0.2rem 0.4rem; border-radius: 3px; max-width: 320px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.filter-actions { display: flex; align-items: center; gap: 1rem; }
.pagination-toggle { display: flex; align-items: center; gap: 0.5rem; font-size: 0.85rem; color: #64748b; }
.mt-2 { margin-top: 0.5rem; }
.mt-3 { margin-top: 0.75rem; }
.loading { display: flex; align-items: center; gap: 0.5rem; padding: 1rem 0; color: #64748b; }
.results-info { font-size: 0.85rem; color: #64748b; padding-top: 0.5rem; }
.id-cell { background: #f1f5f9; padding: 0.1rem 0.3rem; border-radius: 3px; font-size: 0.8rem; }
.type-cell { font-size: 0.8rem; color: #64748b; }
.action-buttons { display: flex; gap: 0.25rem; }
.empty-state { text-align: center; padding: 2rem; color: #94a3b8; }
.empty-state i { font-size: 2rem; }
.pagination { display: flex; gap: 0.5rem; padding-top: 0.75rem; }
.raw-section { margin-top: 1rem; }
.raw-section summary { cursor: pointer; font-size: 0.85rem; color: #64748b; }
.raw-json { background: #f8fafc; padding: 0.75rem; border-radius: 6px; overflow-x: auto; font-size: 0.75rem; max-height: 300px; overflow-y: auto; }
</style>
