<script setup lang="ts">
import { ref, computed } from 'vue'
import { apiFetch } from '../api'
import { getCreateUrl, getContentType } from '../csapi-bridge'
import { getResourceType } from '../state'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'
import Message from 'primevue/message'

const props = defineProps<{
  resourceType: string
}>()

const emit = defineEmits<{
  (e: 'created'): void
}>()

const rtInfo = computed(() => getResourceType(props.resourceType))

// For nested creation (observations → datastream, commands → controlStream)
const parentId = ref('')

const jsonBody = ref(getDefaultBody())
const loading = ref(false)
const error = ref('')
const success = ref('')
const responseData = ref<any>(null)

function getDefaultBody(): string {
  // Provide a helpful starter template based on resource type
  if (props.resourceType === 'systems') {
    return JSON.stringify({
      type: 'Feature',
      properties: {
        featureType: 'http://www.w3.org/ns/sosa/Platform',
        name: 'My Test System',
        description: 'A test system created via CSAPI Explorer',
      },
      geometry: null,
    }, null, 2)
  }
  if (props.resourceType === 'deployments') {
    return JSON.stringify({
      type: 'Feature',
      properties: {
        name: 'My Test Deployment',
        description: 'A test deployment',
        validTime: { begin: new Date().toISOString() },
      },
      geometry: null,
    }, null, 2)
  }
  if (props.resourceType === 'procedures') {
    return JSON.stringify({
      type: 'Feature',
      properties: {
        featureType: 'http://www.w3.org/ns/sosa/Procedure',
        name: 'My Test Procedure',
        description: 'A test procedure',
      },
      geometry: null,
    }, null, 2)
  }
  if (props.resourceType === 'samplingFeatures') {
    return JSON.stringify({
      type: 'Feature',
      properties: {
        featureType: 'http://www.w3.org/ns/sosa/Sample',
        name: 'My Test Sampling Feature',
        description: 'A test sampling feature',
      },
      geometry: {
        type: 'Point',
        coordinates: [0, 0],
      },
    }, null, 2)
  }
  if (props.resourceType === 'datastreams') {
    return JSON.stringify({
      name: 'My Test Datastream',
      description: 'A test datastream',
      outputName: 'test-output',
    }, null, 2)
  }
  if (props.resourceType === 'observations') {
    return JSON.stringify({
      phenomenonTime: new Date().toISOString(),
      resultTime: new Date().toISOString(),
      result: {},
    }, null, 2)
  }
  if (props.resourceType === 'controlStreams') {
    return JSON.stringify({
      name: 'My Test Control Stream',
      description: 'A test control stream',
      inputName: 'test-input',
    }, null, 2)
  }
  if (props.resourceType === 'commands') {
    return JSON.stringify({
      issueTime: new Date().toISOString(),
      parameters: {},
    }, null, 2)
  }
  return JSON.stringify({}, null, 2)
}

async function create() {
  error.value = ''
  success.value = ''
  responseData.value = null

  // Validate JSON
  let body: any
  try {
    body = JSON.parse(jsonBody.value)
  } catch (e: any) {
    error.value = 'Invalid JSON: ' + e.message
    return
  }

  loading.value = true

  // Use CSAPIQueryBuilder via bridge to construct the POST URL
  // Handles nested creation (observations → datastreams, commands → controlStreams)
  const path = getCreateUrl(
    props.resourceType,
    rtInfo.value?.createParentType ? parentId.value : undefined
  )

  // Use bridge helper for correct Content-Type (geo+json for Part 1, json for Part 2)
  const contentType = getContentType(props.resourceType)

  const res = await apiFetch(path, {
    method: 'POST',
    headers: { 'Content-Type': contentType },
    body: JSON.stringify(body),
  })

  loading.value = false

  if (!res.ok) {
    error.value = res.error || `Create failed: ${res.status}`
  } else {
    success.value = `Created successfully! (${res.status} ${res.statusText})`
    responseData.value = res.data
    // Check for Location header
    if (res.headers['location']) {
      success.value += ` — Location: ${res.headers['location']}`
    }
    emit('created')
  }
}
</script>

<template>
  <div class="resource-create">
    <p class="hint">
      Enter a JSON body for the new {{ rtInfo?.label || resourceType }}.
      The body will be POSTed to the server.
    </p>

    <!-- Parent ID for nested resources -->
    <div v-if="rtInfo?.createParentType" class="parent-field">
      <label>{{ rtInfo.createParentLabel }}:</label>
      <InputText v-model="parentId" :placeholder="`Enter ${rtInfo.createParentLabel}`" class="w-md" />
      <small class="hint">Required — {{ rtInfo.label }} is created under a {{ rtInfo.createParentLabel?.replace(' ID', '') }}</small>
    </div>

    <div class="editor-container">
      <label>Request Body (JSON):</label>
      <Textarea
        v-model="jsonBody"
        rows="16"
        class="json-editor"
        spellcheck="false"
      />
    </div>

    <div class="actions">
      <Button
        label="Create (POST)"
        icon="pi pi-plus"
        :loading="loading"
        @click="create"
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
.resource-create { display: flex; flex-direction: column; gap: 0.75rem; }
.hint { color: #64748b; font-size: 0.9rem; margin: 0; }
.parent-field { display: flex; flex-direction: column; gap: 0.25rem; }
.parent-field label { font-weight: 600; font-size: 0.9rem; }
.w-md { width: 300px; }
.editor-container { display: flex; flex-direction: column; gap: 0.25rem; }
.editor-container label { font-weight: 600; font-size: 0.9rem; }
.json-editor { font-family: 'Consolas', 'Monaco', monospace; font-size: 0.85rem; width: 100%; resize: vertical; }
.actions { display: flex; gap: 0.5rem; }
.mt-3 { margin-top: 0.75rem; }
.response-section { margin-top: 0.5rem; }
.response-section summary { cursor: pointer; font-weight: 600; font-size: 0.9rem; color: #475569; }
.raw-json { background: #f8fafc; padding: 0.75rem; border-radius: 6px; overflow-x: auto; font-size: 0.75rem; max-height: 300px; overflow-y: auto; }
</style>
