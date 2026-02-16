<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { apiFetch } from '../api'
import { getDetailUrl, extractCSAPIFeature, getCSAPIResourceType } from '../csapi-bridge'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Message from 'primevue/message'
import ProgressSpinner from 'primevue/progressspinner'
import SweSchemaDisplay from './SweSchemaDisplay.vue'

const props = defineProps<{
  resourceType: string
  resourceId: string | null
  resource: any | null
}>()
const manualId = ref('')
const loading = ref(false)
const error = ref('')
const detail = ref<any>(null)

// Use the library's extractCSAPIFeature for typed display when applicable
const typedResource = computed(() => {
  if (!detail.value) return null
  try {
    // Only works for Part 1 GeoJSON resources with recognized featureType
    if (getCSAPIResourceType(detail.value)) {
      return extractCSAPIFeature(detail.value)
    }
  } catch { /* Not a recognized CSAPI feature — show raw */ }
  return null
})

const recognizedType = computed(() => {
  if (!detail.value) return null
  return getCSAPIResourceType(detail.value)
})

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
  const res = await apiFetch(path)

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
      <!-- Library recognition badge -->
      <div v-if="recognizedType" class="recognition-badge">
        <i class="pi pi-check-circle"></i>
        <span>Recognized by library as: <strong>{{ recognizedType }}</strong></span>
      </div>

      <!-- Summary fields -->
      <div class="detail-summary">
        <div v-if="detail.id" class="field">
          <span class="field-label">ID:</span>
          <code>{{ detail.id }}</code>
        </div>
        <div v-if="detail.type" class="field">
          <span class="field-label">Type:</span>
          <span>{{ detail.type }}</span>
        </div>
        <!-- Typed properties from extractCSAPIFeature -->
        <template v-if="typedResource">
          <div v-if="typedResource.properties?.name" class="field">
            <span class="field-label">Name:</span>
            <span>{{ typedResource.properties.name }}</span>
          </div>
          <div v-if="typedResource.properties?.description" class="field">
            <span class="field-label">Description:</span>
            <span>{{ typedResource.properties.description }}</span>
          </div>
          <div v-if="typedResource.properties?.featureType" class="field">
            <span class="field-label">Feature Type:</span>
            <span>{{ typedResource.properties.featureType }}</span>
          </div>
          <div v-if="typedResource.properties?.uid" class="field">
            <span class="field-label">UID:</span>
            <code>{{ typedResource.properties.uid }}</code>
          </div>
          <div v-if="(typedResource.properties as any)?.validTime" class="field">
            <span class="field-label">Valid Time:</span>
            <span>{{ (typedResource.properties as any).validTime.start.toISOString() }}{{ (typedResource.properties as any).validTime.end ? ' – ' + (typedResource.properties as any).validTime.end.toISOString() : ' – (ongoing)' }}</span>
          </div>
        </template>
        <!-- Fallback: raw property display for non-GeoJSON resources -->
        <template v-else>
          <div v-if="detail.properties?.name" class="field">
            <span class="field-label">Name:</span>
            <span>{{ detail.properties.name }}</span>
          </div>
          <div v-if="detail.properties?.description" class="field">
            <span class="field-label">Description:</span>
            <span>{{ detail.properties.description }}</span>
          </div>
          <div v-if="detail.properties?.featureType" class="field">
            <span class="field-label">Feature Type:</span>
            <span>{{ detail.properties.featureType }}</span>
          </div>
          <div v-if="detail.properties?.validTime" class="field">
            <span class="field-label">Valid Time:</span>
            <span>{{ JSON.stringify(detail.properties.validTime) }}</span>
          </div>
          <!-- Part 2 flat objects -->
          <div v-if="detail.name && !detail.properties" class="field">
            <span class="field-label">Name:</span>
            <span>{{ detail.name }}</span>
          </div>
          <div v-if="detail.description && !detail.properties" class="field">
            <span class="field-label">Description:</span>
            <span>{{ detail.description }}</span>
          </div>
        </template>
      </div>

      <!-- Observation Schema (datastreams only) -->
      <SweSchemaDisplay v-if="isDatastream && effectiveId" :datastreamId="effectiveId" />

      <!-- Links -->
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

      <!-- Full JSON -->
      <details class="detail-section" open>
        <summary>Full JSON</summary>
        <pre class="raw-json">{{ JSON.stringify(detail, null, 2) }}</pre>
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
.recognition-badge { display: flex; align-items: center; gap: 0.5rem; background: #f0fdf4; border: 1px solid #bbf7d0; padding: 0.5rem 0.75rem; border-radius: 6px; font-size: 0.85rem; color: #166534; }
.recognition-badge i { color: #16a34a; }
.detail-summary { background: #f8fafc; padding: 1rem; border-radius: 6px; border: 1px solid #e2e8f0; display: flex; flex-direction: column; gap: 0.4rem; }
.field { display: flex; gap: 0.5rem; font-size: 0.9rem; }
.field-label { font-weight: 600; min-width: 110px; color: #475569; }
.field code { background: #e2e8f0; padding: 0.1rem 0.3rem; border-radius: 3px; font-size: 0.85rem; }
.detail-section { margin-top: 0.5rem; }
.detail-section summary { cursor: pointer; font-weight: 600; font-size: 0.9rem; color: #475569; }
.links-table { width: 100%; border-collapse: collapse; font-size: 0.8rem; margin-top: 0.5rem; }
.links-table th, .links-table td { padding: 0.35rem 0.5rem; text-align: left; border-bottom: 1px solid #e2e8f0; }
.links-table th { background: #f8fafc; font-weight: 600; }
.href-cell { font-family: monospace; font-size: 0.75rem; word-break: break-all; }
.raw-json { background: #f8fafc; padding: 0.75rem; border-radius: 6px; overflow-x: auto; font-size: 0.75rem; max-height: 500px; overflow-y: auto; margin-top: 0.5rem; }
</style>
