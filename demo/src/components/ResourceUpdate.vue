<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { apiFetch, getResourcePath } from '../api'
import { getResourceType } from '../state'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'
import Message from 'primevue/message'

const props = defineProps<{
  resourceType: string
  resourceId: string | null
  resource: any | null
}>()

const emit = defineEmits<{
  (e: 'updated'): void
}>()

const rtInfo = computed(() => getResourceType(props.resourceType))
const manualId = ref('')
const jsonBody = ref('')
const loading = ref(false)
const error = ref('')
const success = ref('')
const responseData = ref<any>(null)

// When a resource is selected (from list or detail), populate the editor
watch(
  () => props.resource,
  (resource) => {
    if (resource) {
      jsonBody.value = JSON.stringify(resource, null, 2)
    }
  },
  { immediate: true }
)

const effectiveId = computed(() => manualId.value || props.resourceId || '')

async function update() {
  error.value = ''
  success.value = ''
  responseData.value = null

  if (!effectiveId.value) {
    error.value = 'Please enter or select a resource ID to update.'
    return
  }

  let body: any
  try {
    body = JSON.parse(jsonBody.value)
  } catch (e: any) {
    error.value = 'Invalid JSON: ' + e.message
    return
  }

  loading.value = true

  const path = `${getResourcePath(props.resourceType)}/${effectiveId.value}`

  const contentType = (props.resourceType === 'systems' || props.resourceType === 'deployments' ||
    props.resourceType === 'procedures' || props.resourceType === 'samplingFeatures')
    ? 'application/geo+json'
    : 'application/json'

  const res = await apiFetch(path, {
    method: 'PUT',
    headers: { 'Content-Type': contentType },
    body: JSON.stringify(body),
  })

  loading.value = false

  if (!res.ok) {
    error.value = res.error || `Update failed: ${res.status}`
  } else {
    success.value = `Updated successfully! (${res.status} ${res.statusText})`
    responseData.value = res.data
    emit('updated')
  }
}
</script>

<template>
  <div class="resource-update">
    <p class="hint">
      Edit the JSON body and PUT it to update the {{ rtInfo?.label || resourceType }}.
      Select a resource from the List tab or enter an ID.
    </p>

    <div class="id-field">
      <label>Resource ID:</label>
      <InputText
        v-model="manualId"
        :placeholder="props.resourceId || 'Enter resource ID'"
        class="w-md"
      />
      <span v-if="effectiveId" class="id-display">Updating: <code>{{ effectiveId }}</code></span>
    </div>

    <div v-if="!jsonBody && !effectiveId" class="empty-hint">
      <i class="pi pi-info-circle"></i>
      <p>Click the edit (pencil) icon on a resource in the List tab to load it here.</p>
    </div>

    <div v-if="jsonBody" class="editor-container">
      <label>Request Body (JSON):</label>
      <Textarea
        v-model="jsonBody"
        rows="16"
        class="json-editor"
        spellcheck="false"
      />
    </div>

    <div v-if="jsonBody || effectiveId" class="actions">
      <Button
        label="Update (PUT)"
        icon="pi pi-save"
        :loading="loading"
        @click="update"
        :disabled="!effectiveId"
      />
    </div>

    <Message v-if="error" severity="error" :closable="false" class="mt-3">{{ error }}</Message>
    <Message v-if="success" severity="success" :closable="false" class="mt-3">{{ success }}</Message>

    <details v-if="responseData" class="response-section">
      <summary>Response Body</summary>
      <pre class="raw-json">{{ JSON.stringify(responseData, null, 2) }}</pre>
    </details>
  </div>
</template>

<style scoped>
.resource-update { display: flex; flex-direction: column; gap: 0.75rem; }
.hint { color: #64748b; font-size: 0.9rem; margin: 0; }
.id-field { display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap; }
.id-field label { font-weight: 600; font-size: 0.9rem; }
.w-md { width: 300px; }
.id-display { font-size: 0.85rem; color: #475569; }
.id-display code { background: #e2e8f0; padding: 0.1rem 0.3rem; border-radius: 3px; }
.empty-hint { display: flex; align-items: center; gap: 0.5rem; color: #94a3b8; padding: 1rem 0; }
.editor-container { display: flex; flex-direction: column; gap: 0.25rem; }
.editor-container label { font-weight: 600; font-size: 0.9rem; }
.json-editor { font-family: 'Consolas', 'Monaco', monospace; font-size: 0.85rem; width: 100%; resize: vertical; }
.actions { display: flex; gap: 0.5rem; }
.mt-3 { margin-top: 0.75rem; }
.response-section { margin-top: 0.5rem; }
.response-section summary { cursor: pointer; font-weight: 600; font-size: 0.9rem; color: #475569; }
.raw-json { background: #f8fafc; padding: 0.75rem; border-radius: 6px; overflow-x: auto; font-size: 0.75rem; max-height: 300px; overflow-y: auto; }
</style>
