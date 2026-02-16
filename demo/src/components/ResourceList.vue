<script setup lang="ts">
import { ref, watch } from 'vue'
import { apiFetch, getResourcePath, buildQueryString } from '../api'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import InputNumber from 'primevue/inputnumber'
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
const bbox = ref('')
const datetime = ref('')

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
const rawResponse = ref<any>(null)

async function fetchResources(cursorUrl?: string) {
  loading.value = true
  error.value = ''
  items.value = []
  rawResponse.value = null

  try {
    let path: string
    if (cursorUrl) {
      // Cursor-based pagination: use the full link path
      path = cursorUrl
    } else {
      const params: Record<string, any> = {}
      if (limit.value) params.limit = limit.value
      if (paginationMode.value === 'offset' && offset.value > 0) params.offset = offset.value
      if (q.value) params.q = q.value
      if (bbox.value) params.bbox = bbox.value
      if (datetime.value) params.datetime = datetime.value
      path = getResourcePath(props.resourceType) + buildQueryString(params)
    }

    const res = await apiFetch(path)
    if (!res.ok) {
      error.value = res.error || 'Failed to fetch resources'
      return
    }

    rawResponse.value = res.data

    // Parse response — handle both FeatureCollection (Part 1) and items envelope (Part 2)
    const data = res.data
    if (data?.type === 'FeatureCollection' && Array.isArray(data.features)) {
      items.value = data.features
    } else if (Array.isArray(data?.items)) {
      items.value = data.items
    } else if (Array.isArray(data)) {
      items.value = data
    } else {
      items.value = []
    }

    numberMatched.value = data?.numberMatched ?? null
    numberReturned.value = data?.numberReturned ?? items.value.length

    // Extract pagination links
    cursorNext.value = null
    cursorPrev.value = null
    const links = data?.links || []
    for (const link of links) {
      if (link.rel === 'next' && link.href) {
        // Convert absolute URL to relative path through proxy
        cursorNext.value = extractProxyPath(link.href)
      }
      if (link.rel === 'prev' && link.href) {
        cursorPrev.value = extractProxyPath(link.href)
      }
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
          <label>Bbox</label>
          <InputText v-model="bbox" placeholder="minx,miny,maxx,maxy" class="w-md" />
        </div>
        <div class="filter-item">
          <label>DateTime</label>
          <InputText v-model="datetime" placeholder="2024-01-01/2024-12-31" class="w-md" />
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
      <span v-if="numberMatched != null"> of {{ numberMatched }} total</span>
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
.w-sm { width: 80px; }
.w-md { width: 180px; }
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
