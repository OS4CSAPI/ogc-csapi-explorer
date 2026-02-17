<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { connection } from '../state'
import { initializeBuilder, destroyBuilder } from '../csapi-bridge'
import InputText from 'primevue/inputtext'
import Password from 'primevue/password'
import Button from 'primevue/button'
import Select from 'primevue/select'
import Panel from 'primevue/panel'
import Message from 'primevue/message'
import ProgressSpinner from 'primevue/progressspinner'

const router = useRouter()

const presets = [
  { label: '52North CSA Demo', proxyPath: '/api/52north', description: 'Public demo — no auth required', externalUrl: 'https://csa.demo.52north.org' },
  { label: 'OSH SensorHub', proxyPath: '/api/osh', description: 'Requires basic auth', externalUrl: 'http://45.55.99.236:8080/sensorhub/api' },
  { label: 'Custom URL', proxyPath: '', description: 'Enter a custom server URL', externalUrl: '' },
]

const selectedPreset = ref(presets[0])
const customUrl = ref('')
const username = ref('')
const password = ref('')
const connecting = ref(false)
const error = ref('')

// Clear credentials when switching servers
watch(selectedPreset, () => {
  username.value = ''
  password.value = ''
  error.value = ''
})

// Display data (not shared — only shown on this page)
const landingPage = ref<any>(null)
const conformance = ref<string[]>([])
const collections = ref<any[]>([])

function getEffectiveUrl(): string {
  return selectedPreset.value?.proxyPath || customUrl.value
}

function getAuthHeaders(): Record<string, string> {
  if (username.value && password.value) {
    return { Authorization: 'Basic ' + btoa(`${username.value}:${password.value}`) }
  }
  return {}
}

async function connect() {
  error.value = ''
  connecting.value = true
  landingPage.value = null
  conformance.value = []
  collections.value = []

  const baseUrl = getEffectiveUrl()
  if (!baseUrl) {
    error.value = 'Please enter a server URL or select a preset.'
    connecting.value = false
    return
  }

  const headers = getAuthHeaders()

  try {
    // Landing page
    const landingRes = await fetch(baseUrl + '/', { headers })
    if (!landingRes.ok) throw new Error(`Landing page: ${landingRes.status} ${landingRes.statusText}`)
    const landingData = await landingRes.json()
    landingPage.value = landingData

    // Conformance
    try {
      const conformRes = await fetch(baseUrl + '/conformance', { headers })
      if (conformRes.ok) {
        const conformData = await conformRes.json()
        conformance.value = conformData.conformsTo || []
      }
    } catch { /* not fatal */ }

    // Collections
    try {
      const collectionsRes = await fetch(baseUrl + '/collections', { headers })
      if (collectionsRes.ok) {
        const collectionsData = await collectionsRes.json()
        collections.value = collectionsData.collections || []
      }
    } catch { /* not fatal */ }

    // Store in shared state
    connection.connected = true
    connection.label = selectedPreset.value?.label || customUrl.value
    connection.baseUrl = baseUrl
    connection.authHeaders = headers
    connection.landingPage = landingData
    connection.conformance = conformance.value
    connection.collections = collections.value

    // Initialize the CSAPIQueryBuilder from discovered links
    const csapiBuilder = initializeBuilder(landingData, collections.value)
    console.log('[CSAPI Bridge] Builder initialized. Available resources:',
      Array.from(csapiBuilder.availableResources))
  } catch (err: any) {
    error.value = err.message || 'Connection failed'
  } finally {
    connecting.value = false
  }
}

function disconnect() {
  destroyBuilder()
  connection.connected = false
  connection.label = ''
  connection.baseUrl = ''
  connection.authHeaders = {}
  connection.landingPage = null
  connection.conformance = []
  connection.collections = []
  landingPage.value = null
  conformance.value = []
  collections.value = []
  error.value = ''
}

function goToExplorer() {
  router.push('/explore/systems')
}

function csapiConformance(classes: string[]): string[] {
  return classes.filter(c =>
    c.includes('connected-systems') || c.includes('csapi') ||
    c.includes('swecommon') || c.includes('sensorml')
  )
}

function otherConformance(classes: string[]): string[] {
  return classes.filter(c =>
    !c.includes('connected-systems') && !c.includes('csapi') &&
    !c.includes('swecommon') && !c.includes('sensorml')
  )
}
</script>

<template>
  <div class="connect-page">
    <div class="page-intro">
      <h2>Server Connection</h2>
      <p>Connect to a CSAPI server to explore its resources.</p>
    </div>

    <Panel header="Connection Settings">
      <div class="form-grid">
        <div class="form-row">
          <label>Server</label>
          <Select v-model="selectedPreset" :options="presets" optionLabel="label" class="w-full" />
          <small class="hint">
            {{ selectedPreset?.description }}
            <a
              v-if="selectedPreset?.externalUrl"
              :href="selectedPreset.externalUrl"
              target="_blank"
              rel="noopener noreferrer"
              class="server-link"
            >
              <i class="pi pi-external-link"></i> {{ selectedPreset.externalUrl }}
            </a>
          </small>
        </div>

        <div v-if="!selectedPreset?.proxyPath" class="form-row">
          <label>Custom URL</label>
          <InputText v-model="customUrl" placeholder="https://example.com/api" class="w-full" />
        </div>

        <div class="form-row">
          <label>Username (optional)</label>
          <InputText v-model="username" placeholder="username" class="w-full" />
        </div>

        <div class="form-row">
          <label>Password (optional)</label>
          <Password v-model="password" :feedback="false" toggleMask placeholder="password" class="w-full" />
        </div>

        <div class="form-actions">
          <Button
            v-if="!connection.connected"
            label="Connect" icon="pi pi-link" :loading="connecting"
            @click="connect"
          />
          <template v-else>
            <Button label="Open Explorer" icon="pi pi-th-large" @click="goToExplorer" />
            <Button label="Disconnect" icon="pi pi-times" severity="secondary" @click="disconnect" />
          </template>
        </div>
      </div>

      <Message v-if="error" severity="error" :closable="false" class="mt-3">{{ error }}</Message>

      <div v-if="connecting" class="connecting-spinner">
        <ProgressSpinner style="width: 40px; height: 40px" />
        <span>Connecting...</span>
      </div>
    </Panel>

    <!-- Results after connection -->
    <template v-if="connection.connected">
      <Panel header="Server Info" class="mt-4" toggleable>
        <div class="info-grid">
          <div v-if="landingPage?.title"><strong>Title:</strong> {{ landingPage.title }}</div>
          <div v-if="landingPage?.description"><strong>Description:</strong> {{ landingPage.description }}</div>
        </div>
      </Panel>

      <Panel v-if="conformance.length > 0" header="Conformance Classes" class="mt-4" toggleable>
        <div v-if="csapiConformance(conformance).length > 0">
          <h4 class="mt-0">CSAPI / SensorML / SWE Common</h4>
          <ul class="conformance-list">
            <li v-for="c in csapiConformance(conformance)" :key="c">{{ c }}</li>
          </ul>
        </div>
        <div v-if="otherConformance(conformance).length > 0">
          <h4>Other</h4>
          <ul class="conformance-list">
            <li v-for="c in otherConformance(conformance)" :key="c">{{ c }}</li>
          </ul>
        </div>
        <p class="text-muted mb-0">Total: {{ conformance.length }} conformance classes</p>
      </Panel>

      <Panel v-if="collections.length > 0" header="Collections" class="mt-4" toggleable>
        <table class="collections-table">
          <thead>
            <tr><th>ID</th><th>Title</th><th>Description</th></tr>
          </thead>
          <tbody>
            <tr v-for="col in collections" :key="col.id">
              <td><code>{{ col.id }}</code></td>
              <td>{{ col.title || '—' }}</td>
              <td>{{ col.description || '—' }}</td>
            </tr>
          </tbody>
        </table>
      </Panel>

      <Panel header="Raw Response" class="mt-4" toggleable collapsed>
        <pre class="raw-json">{{ JSON.stringify({ landingPage, conformance, collections }, null, 2) }}</pre>
      </Panel>
    </template>
  </div>
</template>

<style scoped>
.connect-page {
  max-width: 960px;
  margin: 0 auto;
  padding: 1.5rem 1rem;
}
.page-intro { margin-bottom: 1.5rem; }
.page-intro h2 { margin: 0 0 0.25rem; }
.page-intro p { margin: 0; color: #64748b; }
.form-grid { display: flex; flex-direction: column; gap: 1rem; }
.form-row { display: flex; flex-direction: column; gap: 0.25rem; }
.form-row label { font-weight: 600; font-size: 0.9rem; }
.hint { color: #64748b; font-size: 0.85rem; }
.server-link { display: inline-flex; align-items: center; gap: 0.25rem; margin-left: 0.5rem; color: #3b82f6; text-decoration: none; font-size: 0.82rem; }
.server-link:hover { text-decoration: underline; }
.server-link .pi { font-size: 0.75rem; }
.form-actions { display: flex; gap: 0.5rem; margin-top: 0.5rem; }
.w-full { width: 100%; }
.mt-0 { margin-top: 0; }
.mt-3 { margin-top: 0.75rem; }
.mt-4 { margin-top: 1rem; }
.mb-0 { margin-bottom: 0; }
.text-muted { color: #64748b; }
.connecting-spinner { display: flex; align-items: center; gap: 0.75rem; margin-top: 1rem; color: #64748b; }
.info-grid { display: flex; flex-direction: column; gap: 0.5rem; }
.conformance-list { list-style: none; padding: 0; margin: 0; }
.conformance-list li { padding: 0.25rem 0; font-size: 0.85rem; font-family: monospace; word-break: break-all; border-bottom: 1px solid #f1f5f9; }
.collections-table { width: 100%; border-collapse: collapse; font-size: 0.9rem; }
.collections-table th, .collections-table td { padding: 0.5rem 0.75rem; text-align: left; border-bottom: 1px solid #e2e8f0; }
.collections-table th { background: #f8fafc; font-weight: 600; }
.collections-table code { background: #f1f5f9; padding: 0.1rem 0.3rem; border-radius: 3px; font-size: 0.85rem; }
.raw-json { background: #f8fafc; padding: 1rem; border-radius: 6px; overflow-x: auto; font-size: 0.8rem; max-height: 400px; overflow-y: auto; margin: 0; }
</style>
