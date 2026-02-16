<script setup lang="ts">
import { ref, computed } from 'vue'
import { apiFetch } from '../api'
import { getDeleteUrl } from '../csapi-bridge'
import { getResourceType } from '../state'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Message from 'primevue/message'

const props = defineProps<{
  resourceType: string
  resourceId: string | null
}>()

const emit = defineEmits<{
  (e: 'deleted'): void
}>()

const rtInfo = computed(() => getResourceType(props.resourceType))
const manualId = ref('')
const loading = ref(false)
const error = ref('')
const success = ref('')
const confirmed = ref(false)

const effectiveId = computed(() => manualId.value || props.resourceId || '')

function confirmDelete() {
  error.value = ''
  success.value = ''
  if (!effectiveId.value) {
    error.value = 'Please enter or select a resource ID to delete.'
    return
  }
  confirmed.value = true
}

function cancelDelete() {
  confirmed.value = false
}

async function executeDelete() {
  error.value = ''
  success.value = ''

  if (!effectiveId.value) {
    error.value = 'No resource ID specified.'
    return
  }

  loading.value = true

  // Use CSAPIQueryBuilder via bridge to construct the DELETE URL
  const path = getDeleteUrl(props.resourceType, effectiveId.value)
  const res = await apiFetch(path, { method: 'DELETE' })

  loading.value = false
  confirmed.value = false

  if (!res.ok) {
    error.value = res.error || `Delete failed: ${res.status}`
  } else {
    success.value = `Deleted successfully! (${res.status} ${res.statusText})`
    emit('deleted')
  }
}
</script>

<template>
  <div class="resource-delete">
    <p class="hint">
      Delete a {{ rtInfo?.label || resourceType }} by ID. This action cannot be undone.
    </p>

    <div class="id-field">
      <label>Resource ID:</label>
      <InputText
        v-model="manualId"
        :placeholder="props.resourceId || 'Enter resource ID'"
        class="w-md"
      />
    </div>

    <div v-if="effectiveId" class="target-info">
      <i class="pi pi-exclamation-triangle warning-icon"></i>
      <span>Target: <code>{{ effectiveId }}</code></span>
    </div>

    <div v-if="!effectiveId" class="empty-hint">
      <i class="pi pi-info-circle"></i>
      <p>Select a resource from the List tab, or enter an ID above.</p>
    </div>

    <div v-if="effectiveId && !confirmed" class="actions">
      <Button
        label="Delete"
        icon="pi pi-trash"
        severity="danger"
        @click="confirmDelete"
      />
    </div>

    <div v-if="confirmed" class="confirm-box">
      <p class="confirm-text">
        <i class="pi pi-exclamation-triangle"></i>
        Are you sure you want to delete <code>{{ effectiveId }}</code>?
      </p>
      <div class="confirm-actions">
        <Button
          label="Yes, Delete"
          icon="pi pi-trash"
          severity="danger"
          :loading="loading"
          @click="executeDelete"
        />
        <Button
          label="Cancel"
          severity="secondary"
          @click="cancelDelete"
        />
      </div>
    </div>

    <Message v-if="error" severity="error" :closable="false" class="mt-3">{{ error }}</Message>
    <Message v-if="success" severity="success" :closable="false" class="mt-3">{{ success }}</Message>
  </div>
</template>

<style scoped>
.resource-delete { display: flex; flex-direction: column; gap: 0.75rem; }
.hint { color: #64748b; font-size: 0.9rem; margin: 0; }
.id-field { display: flex; align-items: center; gap: 0.5rem; }
.id-field label { font-weight: 600; font-size: 0.9rem; }
.w-md { width: 300px; }
.target-info { display: flex; align-items: center; gap: 0.5rem; font-size: 0.9rem; }
.target-info code { background: #fee2e2; color: #991b1b; padding: 0.15rem 0.4rem; border-radius: 3px; }
.warning-icon { color: #f59e0b; }
.empty-hint { display: flex; align-items: center; gap: 0.5rem; color: #94a3b8; padding: 1rem 0; }
.actions { display: flex; gap: 0.5rem; }
.confirm-box { background: #fef2f2; border: 1px solid #fecaca; border-radius: 6px; padding: 1rem; }
.confirm-text { margin: 0 0 0.75rem; color: #991b1b; display: flex; align-items: center; gap: 0.5rem; }
.confirm-text code { background: #fee2e2; padding: 0.15rem 0.4rem; border-radius: 3px; }
.confirm-actions { display: flex; gap: 0.5rem; }
.mt-3 { margin-top: 0.75rem; }
</style>
