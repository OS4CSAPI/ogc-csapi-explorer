<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { apiFetch } from '../api'
import { getDetailUrl, getContentType } from '../csapi-bridge'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Message from 'primevue/message'
import ProgressSpinner from 'primevue/progressspinner'
import SweSchemaDisplay from './SweSchemaDisplay.vue'
import ParsedResourceView from './ParsedResourceView.vue'

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

/** ID to pass to schema component — uses fetched detail ID or the prop */
const effectiveId = computed(() => detail.value?.id || props.resourceId || '')

async function fetchDetail(id?: string) {
  const useId = id || manualId.value || props.resourceId
  if (!useId) return

  loading.value = true
  error.value = ''
  detail.value = null

  // Use CSAPIQueryBuilder via bridge to construct the detail URL
  const path = getDetailUrl(props.resourceType, useId)
  const acceptType = getContentType(props.resourceType)
  const res = await apiFetch(path, {
    headers: { 'Accept': acceptType },
  })

  if (!res.ok) {
    error.value = res.error || 'Failed to fetch resource'
  } else {
    detail.value = res.data
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
          <ParsedResourceView :resource="detail" :resourceType="props.resourceType" />
        </div>
      </div>

      <!-- Observation Schema (datastreams only) — full width below -->
      <SweSchemaDisplay v-if="isDatastream && effectiveId" :datastreamId="effectiveId" />

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
.parsed-panel { }
.parsed-panel > :deep(.parsed-view) { padding: 0.75rem; flex: 1; overflow-y: auto; max-height: 600px; }

.raw-json { background: #f8fafc; padding: 0.75rem; overflow-x: auto; font-size: 0.75rem; max-height: 500px; overflow-y: auto; }
.detail-section { margin-top: 0.5rem; }
.detail-section summary { cursor: pointer; font-weight: 600; font-size: 0.9rem; color: #475569; }
.links-table { width: 100%; border-collapse: collapse; font-size: 0.8rem; margin-top: 0.5rem; }
.links-table th, .links-table td { padding: 0.35rem 0.5rem; text-align: left; border-bottom: 1px solid #e2e8f0; }
.links-table th { background: #f8fafc; font-weight: 600; }
.href-cell { font-family: monospace; font-size: 0.75rem; word-break: break-all; }
</style>
