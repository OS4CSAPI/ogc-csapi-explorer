<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { apiFetch } from '../api'
import { getListUrl, getContentType, parseCollectionResponse } from '../csapi-bridge'
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

const props = defineProps<{
  resourceType: string
}>()

const emit = defineEmits<{
  (e: 'view', resource: any): void
  (e: 'edit', resource: any): void
}>()

// Filter state
const limit = ref(10)
const offset = ref(0)
const q = ref('')
const dtStart = ref<Date | null>(null)
const dtEnd = ref<Date | null>(null)

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
    const countPath = getListUrl(props.resourceType, countOptions)
    const acceptType = getContentType(props.resourceType)
    const countRes = await apiFetch(countPath, {
      headers: { 'Accept': acceptType },
    })
    if (!countRes.ok || !countRes.data) return null
    const parsed = parseCollectionResponse(countRes.data)
    return parsed.items.length
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
      if (datetimeParam.value) applyTemporalFilter(options, props.resourceType, datetimeParam.value)

      // Use CSAPIQueryBuilder via bridge to construct the URL
      path = getListUrl(props.resourceType, options)
    }

    // Fire total-count request in parallel (will be used if server omits numberMatched)
    const totalCountPromise = fetchTotalCount()

    const acceptType = getContentType(props.resourceType)
    const res = await apiFetch(path, {
      headers: { 'Accept': acceptType },
    })
    if (!res.ok) {
      error.value = res.error || 'Failed to fetch resources'
      return
    }

    rawResponse.value = res.data

    // Use the library's parseCollectionResponse to normalize both envelope formats
    // (FeatureCollection and items envelope) into a consistent structure
    try {
      const parsed = parseCollectionResponse(res.data)
      items.value = parsed.items as any[]
      numberReturned.value = parsed.numberReturned ?? parsed.items.length

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
}

function extractProxyPath(absoluteUrl: string): string {
  // The server returns absolute URLs like https://csa.demo.52north.org/systems?offset=10
  // We need to convert to the proxy path like /api/52north/systems?offset=10
  // For now, just strip the origin and keep the path + query
  try {
    const url = new URL(absoluteUrl)
    return url.pathname + url.search
  } catch {
    return absoluteUrl
  }
}

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

// Fetch on mount and when resource type changes
watch(() => props.resourceType, () => {
  offset.value = 0
  cursorNext.value = null
  cursorPrev.value = null
  fetchResources()
}, { immediate: true })
</script>

<template>
  <div class="resource-list">
    <!-- Filters -->
    <div class="filters">
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
    <Message v-if="error" severity="error" :closable="false" class="mt-3">{{ error }}</Message>

    <!-- Loading -->
    <div v-if="loading" class="loading">
      <ProgressSpinner style="width: 30px; height: 30px" />
      <span>Loading...</span>
    </div>

    <!-- Results info -->
    <div v-if="!loading && items.length > 0" class="results-info">
      <span>Showing {{ numberReturned ?? items.length }} results</span>
      <span v-if="numberMatched != null"> of <strong>{{ numberMatched }}</strong> total</span>
      <span v-if="paginationMode === 'offset'"> (offset: {{ offset }})</span>
    </div>

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
        :disabled="paginationMode === 'cursor' ? !cursorNext : items.length < limit"
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
