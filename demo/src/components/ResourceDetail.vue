<script setup lang="ts">
import { ref, watch, computed, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { apiFetch } from '../api'
import { getDetailUrl, getContentType, getNestedListUrl, parseCollectionResponse } from '../csapi-bridge'
import { RELATED_RESOURCES } from '../state'
import type { RelatedResourceLink } from '../state'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Message from 'primevue/message'
import ProgressSpinner from 'primevue/progressspinner'
import SweSchemaDisplay from './SweSchemaDisplay.vue'
import ParsedResourceView from './ParsedResourceView.vue'
import DataModelDiagram from './DataModelDiagram.vue'
import SensorMLDisplay from './SensorMLDisplay.vue'

const router = useRouter()

const props = defineProps<{
  resourceType: string
  resourceId: string | null
  resource: any | null
}>()

const manualId = ref('')
const loading = ref(false)
const error = ref('')
const detail = ref<any>(null)

/** True when viewing a datastream — triggers schema display */
const isDatastream = computed(() => props.resourceType === 'datastreams')
/** True when viewing a procedure — triggers SensorML display */
const isProcedure = computed(() => props.resourceType === 'procedures')
const effectiveId = computed(() => detail.value?.id || props.resourceId || '')

// ========================================
// Unified inline related resource panels
// ========================================

/** All relation links for the current resource type (includes subsystems, datastreams, etc.) */
const allRelations = computed<RelatedResourceLink[]>(() => {
  return RELATED_RESOURCES[props.resourceType] || []
})

/** Per-relation reactive state: items, loading, error, expanded */
interface RelationState {
  items: any[]
  loading: boolean
  error: string
  expanded: boolean
}
const relationStates = reactive<Record<string, RelationState>>({})

function getRelState(relation: string): RelationState {
  if (!relationStates[relation]) {
    relationStates[relation] = { items: [], loading: false, error: '', expanded: true }
  }
  return relationStates[relation]
}

/** Fetch a single related resource collection */
async function fetchRelation(link: RelatedResourceLink, parentId: string) {
  const state = getRelState(link.relation)
  state.loading = true
  state.error = ''
  state.items = []

  try {
    const path = getNestedListUrl(props.resourceType, parentId, link.relation, { limit: 20 })
    const acceptType = getContentType(link.childType)
    const res = await apiFetch(path, { headers: { 'Accept': acceptType } })

    if (!res.ok) {
      if (res.status !== 404 && res.status !== 400) {
        state.error = res.error || 'Failed to fetch'
      }
      return
    }

    try {
      const parsed = parseCollectionResponse(res.data)
      state.items = parsed.items as any[]
    } catch {
      if (Array.isArray(res.data)) state.items = res.data
    }
  } catch {
    // Silently fail — server may not support this nested endpoint
  } finally {
    state.loading = false
  }
}

/** Fetch all related resources in parallel */
function fetchAllRelations(parentId: string) {
  // Reset all states
  for (const key of Object.keys(relationStates)) {
    delete relationStates[key]
  }
  for (const link of allRelations.value) {
    fetchRelation(link, parentId)
  }
}

function getItemId(item: any): string {
  return item?.id || item?.properties?.id || item?.['@id'] || '—'
}

function getItemName(item: any): string {
  return item?.properties?.name || item?.properties?.title || item?.name || item?.title || ''
}

/** Click a related item → load its detail (if same type) or navigate */
function viewRelatedItem(link: RelatedResourceLink, item: any) {
  const id = getItemId(item)
  if (id === '—') return

  if (link.childType === props.resourceType) {
    // Same type (e.g. subsystems) — reload detail in-place
    manualId.value = ''
    fetchDetail(id)
  } else {
    // Different type — navigate to that type's explorer with the item selected
    router.push({
      path: `/explore/${link.childType}`,
      query: {
        parentType: props.resourceType,
        parentId: String(detail.value?.id || props.resourceId),
        relation: link.relation,
      },
    })
  }
}

/** Navigate to full nested list for a relation */
function browseAll(link: RelatedResourceLink) {
  const id = detail.value?.id || props.resourceId
  if (!id) return
  router.push({
    path: `/explore/${link.childType}`,
    query: {
      parentType: props.resourceType,
      parentId: String(id),
      relation: link.relation,
    },
  })
}

function toggleRelation(relation: string) {
  const state = getRelState(relation)
  state.expanded = !state.expanded
}

async function fetchDetail(id?: string) {
  const useId = id || manualId.value || props.resourceId
  if (!useId) return

  loading.value = true
  error.value = ''
  detail.value = null

  const path = getDetailUrl(props.resourceType, useId)
  const acceptType = getContentType(props.resourceType)
  const res = await apiFetch(path, {
    headers: { 'Accept': acceptType },
  })

  if (!res.ok) {
    // If the direct fetch fails (e.g. server only serves nested resources),
    // fall back to the resource data already passed from the list
    if (props.resource) {
      detail.value = props.resource
    } else {
      error.value = res.error || 'Failed to fetch resource'
    }
  } else {
    detail.value = res.data
  }

  // Auto-fetch related resources if we have a detail to show
  if (detail.value) {
    const resId = detail.value?.id || detail.value?.properties?.id
    if (resId && allRelations.value.length > 0) fetchAllRelations(String(resId))
  }
  loading.value = false
}

// Auto-fetch when a resource is selected from the list
watch(
  () => props.resourceId,
  (id) => {
    if (id) fetchDetail(id)
  },
  { immediate: true }
)
</script>

<template>
  <div class="resource-detail">
    <div class="manual-fetch">
      <label>Resource ID:</label>
      <InputText v-model="manualId" :placeholder="props.resourceId || 'Enter resource ID'" class="w-md" />
      <Button label="Fetch" icon="pi pi-download" size="small" @click="fetchDetail()" :loading="loading" />
    </div>

    <div v-if="!props.resourceId && !manualId && !detail" class="empty-hint">
      <i class="pi pi-info-circle"></i>
      <p>Select a resource from the List tab, or enter an ID above to view its details.</p>
    </div>

    <Message v-if="error" severity="error" :closable="false" class="mt-3">{{ error }}</Message>

    <div v-if="loading" class="loading">
      <ProgressSpinner style="width: 30px; height: 30px" />
      <span>Loading...</span>
    </div>

    <template v-if="detail">
      <!-- Inline related resource panels in a grid -->
      <div v-if="allRelations.length > 0 && (detail?.id || props.resourceId)" class="relations-grid">
        <div
          v-for="link in allRelations"
          :key="link.relation"
          class="relation-card"
        >
          <div class="relation-header" @click="toggleRelation(link.relation)">
            <i :class="link.icon"></i>
            <span>{{ link.label }}</span>
            <span v-if="!getRelState(link.relation).loading" class="relation-count">{{ getRelState(link.relation).items.length }}</span>
            <ProgressSpinner v-if="getRelState(link.relation).loading" style="width: 14px; height: 14px" />
            <i :class="['chevron', 'pi', getRelState(link.relation).expanded ? 'pi-chevron-down' : 'pi-chevron-right']" />
          </div>
          <div v-if="getRelState(link.relation).expanded" class="relation-body">
            <div v-if="getRelState(link.relation).items.length > 0" class="relation-list">
              <div
                v-for="item in getRelState(link.relation).items"
                :key="getItemId(item)"
                class="relation-item"
                @click="viewRelatedItem(link, item)"
              >
                <code class="relation-item-id">{{ getItemId(item) }}</code>
                <span v-if="getItemName(item)" class="relation-item-name">{{ getItemName(item) }}</span>
                <i class="pi pi-arrow-right relation-arrow"></i>
              </div>
              <button
                v-if="getRelState(link.relation).items.length >= 20"
                class="browse-all-link"
                @click.stop="browseAll(link)"
              >
                Browse all →
              </button>
            </div>
            <div v-else-if="!getRelState(link.relation).loading && !getRelState(link.relation).error" class="relation-empty">
              None found
            </div>
            <div v-if="getRelState(link.relation).error" class="relation-error">
              {{ getRelState(link.relation).error }}
            </div>
          </div>
        </div>
      </div>

      <!-- Data Model diagram (collapsed by default) -->
      <details v-if="allRelations.length > 0 && (detail?.id || props.resourceId)" class="diagram-details">
        <summary class="diagram-summary">
          <i class="pi pi-share-alt"></i>
          Data Model — SOSA / SSN / CSAPI Relationships
        </summary>
        <DataModelDiagram :activeType="props.resourceType" :activeId="detail?.id || props.resourceId" />
      </details>

      <!-- Side-by-side layout: Raw JSON | Library Parsed Output -->
      <div class="side-by-side">
        <!-- Left panel: Raw Server Response -->
        <div class="panel raw-panel">
          <h3 class="panel-title">
            <i class="pi pi-server"></i>
            Raw Server Response
          </h3>
          <pre class="raw-json">{{ JSON.stringify(detail, null, 2) }}</pre>
        </div>

        <!-- Right panel: Library Parsed Output -->
        <div class="panel parsed-panel">
          <h3 class="panel-title">
            <i class="pi pi-cog"></i>
            Library Parsed Output
          </h3>
          <ParsedResourceView :resource="detail" :resourceType="props.resourceType" :endpointUrl="`/${props.resourceType}/${effectiveId}`" />
        </div>
      </div>

      <!-- Observation Schema (datastreams only) — full width below -->
      <SweSchemaDisplay v-if="isDatastream && effectiveId" :datastreamId="effectiveId" />

      <!-- SensorML Process Description (procedures only) — full width below -->
      <SensorMLDisplay v-if="isProcedure && effectiveId" :procedureId="effectiveId" />

      <!-- Links — full width below -->
      <details v-if="detail.links?.length || detail.properties?.links?.length" class="detail-section">
        <summary>Links ({{ (detail.links || detail.properties?.links || []).length }})</summary>
        <table class="links-table">
          <thead><tr><th>Rel</th><th>Type</th><th>Href</th></tr></thead>
          <tbody>
            <tr v-for="(link, i) in (detail.links || detail.properties?.links || [])" :key="i">
              <td>{{ link.rel }}</td>
              <td>{{ link.type || '—' }}</td>
              <td class="href-cell">{{ link.href }}</td>
            </tr>
          </tbody>
        </table>
      </details>
    </template>
  </div>
</template>

<style scoped>
.resource-detail { display: flex; flex-direction: column; gap: 0.75rem; }

/* Related resources grid */
.relations-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 0.6rem; }
.relation-card { background: #f0f9ff; border: 1px solid #bae6fd; border-radius: 8px; overflow: hidden; display: flex; flex-direction: column; }
.relation-header { display: flex; align-items: center; gap: 0.35rem; padding: 0.5rem 0.65rem; font-weight: 700; font-size: 0.8rem; color: #0369a1; cursor: pointer; user-select: none; }
.relation-header:hover { background: #e0f2fe; }
.relation-count { background: #0369a1; color: #fff; font-size: 0.65rem; font-weight: 700; min-width: 1.1rem; height: 1.1rem; line-height: 1.1rem; text-align: center; border-radius: 999px; padding: 0 0.3rem; }
.chevron { margin-left: auto; font-size: 0.65rem; color: #7dd3fc; }
.relation-body { border-top: 1px solid #bae6fd; max-height: 200px; overflow-y: auto; }
.relation-list { display: flex; flex-direction: column; }
.relation-item { display: flex; align-items: center; gap: 0.4rem; padding: 0.3rem 0.65rem; cursor: pointer; font-size: 0.8rem; border-bottom: 1px solid #e0f2fe; transition: background 0.1s; }
.relation-item:last-child { border-bottom: none; }
.relation-item:hover { background: #e0f2fe; }
.relation-item-id { background: #e0f2fe; padding: 0.05rem 0.3rem; border-radius: 3px; font-size: 0.72rem; color: #0369a1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 140px; }
.relation-item-name { color: #0c4a6e; flex: 1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; font-size: 0.78rem; }
.relation-arrow { margin-left: auto; font-size: 0.6rem; color: #38bdf8; opacity: 0; transition: opacity 0.15s; flex-shrink: 0; }
.relation-item:hover .relation-arrow { opacity: 1; }
.relation-empty { padding: 0.4rem 0.65rem; color: #7dd3fc; font-size: 0.75rem; font-style: italic; }
.relation-error { padding: 0.4rem 0.65rem; color: #dc2626; font-size: 0.75rem; }
.browse-all-link { display: block; width: 100%; padding: 0.3rem 0.65rem; border: none; background: transparent; color: #0369a1; font-size: 0.75rem; font-weight: 600; cursor: pointer; text-align: left; }
.browse-all-link:hover { background: #e0f2fe; }

.diagram-details { margin-top: 0.25rem; }
.diagram-summary { cursor: pointer; font-size: 0.8rem; font-weight: 600; color: #0369a1; display: flex; align-items: center; gap: 0.35rem; padding: 0.3rem 0; user-select: none; }
.diagram-summary:hover { color: #0284c7; }

.manual-fetch { display: flex; align-items: center; gap: 0.5rem; }
.manual-fetch label { font-weight: 600; font-size: 0.9rem; }
.w-md { width: 300px; }
.mt-3 { margin-top: 0.75rem; }
.empty-hint { display: flex; align-items: center; gap: 0.5rem; color: #94a3b8; padding: 1.5rem 0; }
.loading { display: flex; align-items: center; gap: 0.5rem; color: #64748b; }

/* Side-by-side layout */
.side-by-side { display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; min-height: 200px; }
@media (max-width: 900px) {
  .side-by-side { grid-template-columns: 1fr; }
}
.panel { border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden; display: flex; flex-direction: column; }
.panel-title { margin: 0; padding: 0.6rem 0.75rem; font-size: 0.85rem; font-weight: 700; display: flex; align-items: center; gap: 0.4rem; }
.raw-panel .panel-title { background: #f8fafc; color: #475569; border-bottom: 1px solid #e2e8f0; }
.parsed-panel .panel-title { background: #f0fdf4; color: #166534; border-bottom: 1px solid #bbf7d0; }
.raw-panel .raw-json { flex: 1; margin: 0; border-radius: 0; max-height: 600px; }
.parsed-panel > :deep(.parsed-view) { padding: 0.75rem; flex: 1; overflow-y: auto; max-height: 600px; }

.raw-json { background: #f8fafc; padding: 0.75rem; overflow-x: auto; font-size: 0.75rem; max-height: 500px; overflow-y: auto; }
.detail-section { margin-top: 0.5rem; }
.detail-section summary { cursor: pointer; font-weight: 600; font-size: 0.9rem; color: #475569; }
.links-table { width: 100%; border-collapse: collapse; font-size: 0.8rem; margin-top: 0.5rem; }
.links-table th, .links-table td { padding: 0.35rem 0.5rem; text-align: left; border-bottom: 1px solid #e2e8f0; }
.links-table th { background: #f8fafc; font-weight: 600; }
.href-cell { font-family: monospace; font-size: 0.75rem; word-break: break-all; }
</style>
