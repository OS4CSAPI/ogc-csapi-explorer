<script setup lang="ts">
import { ref, reactive } from 'vue'
import InputText from 'primevue/inputtext'
import Password from 'primevue/password'
import Button from 'primevue/button'
import Select from 'primevue/select'
import Panel from 'primevue/panel'
import Message from 'primevue/message'
import ProgressSpinner from 'primevue/progressspinner'

// Preset server configs
const presets = [
  {
    label: '52North CSA Demo',
    proxyPath: '/api/52north',
    description: 'Public demo — no auth required',
  },
  {
    label: 'OSH SensorHub',
    proxyPath: '/api/osh',
    description: 'Requires basic auth',
  },
  {
    label: 'Custom URL',
    proxyPath: '',
    description: 'Enter a custom server URL',
  },
]

const selectedPreset = ref(presets[0])
const customUrl = ref('')
const username = ref('')
const password = ref('')
const connecting = ref(false)
const error = ref('')

// Connection result
const connectionResult = reactive({
  connected: false,
  landingPage: null as any,
  conformance: [] as string[],
  collections: [] as any[],
  raw: null as any,
})

function getEffectiveUrl(): string {
  if (selectedPreset.value.proxyPath) {
    return selectedPreset.value.proxyPath
  }
  return customUrl.value
}

function getAuthHeaders(): Record<string, string> {
  if (username.value && password.value) {
    const encoded = btoa(`${username.value}:${password.value}`)
    return { Authorization: `Basic ${encoded}` }
  }
  return {}
}

async function connect() {
  error.value = ''
  connecting.value = true
  connectionResult.connected = false
  connectionResult.landingPage = null
  connectionResult.conformance = []
  connectionResult.collections = []
  connectionResult.raw = null

  const baseUrl = getEffectiveUrl()
  if (!baseUrl) {
    error.value = 'Please enter a server URL or select a preset.'
    connecting.value = false
    return
  }

  const headers = getAuthHeaders()

  try {
    // Step 1: Fetch landing page
    const landingRes = await fetch(baseUrl + '/', { headers })
    if (!landingRes.ok) {
      throw new Error(`Landing page: ${landingRes.status} ${landingRes.statusText}`)
    }
    const landingData = await landingRes.json()
    connectionResult.landingPage = landingData

    // Step 2: Fetch conformance
    try {
      const conformRes = await fetch(baseUrl + '/conformance', { headers })
      if (conformRes.ok) {
        const conformData = await conformRes.json()
        connectionResult.conformance = conformData.conformsTo || []
      }
    } catch {
      // conformance endpoint may not exist — not fatal
    }

    // Step 3: Fetch collections
    try {
      const collectionsRes = await fetch(baseUrl + '/collections', { headers })
      if (collectionsRes.ok) {
        const collectionsData = await collectionsRes.json()
        connectionResult.collections = collectionsData.collections || []
      }
    } catch {
      // collections may not exist — not fatal
    }

    connectionResult.connected = true
    connectionResult.raw = {
      landingPage: landingData,
      conformance: connectionResult.conformance,
      collections: connectionResult.collections,
    }
  } catch (err: any) {
    error.value = err.message || 'Connection failed'
  } finally {
    connecting.value = false
  }
}

function disconnect() {
  connectionResult.connected = false
  connectionResult.landingPage = null
  connectionResult.conformance = []
  connectionResult.collections = []
  connectionResult.raw = null
  error.value = ''
}

// Helpers for display
function csapiConformance(classes: string[]): string[] {
  return classes.filter(
    (c) =>
      c.includes('connected-systems') ||
      c.includes('csapi') ||
      c.includes('swecommon') ||
      c.includes('sensorml')
  )
}

function otherConformance(classes: string[]): string[] {
  return classes.filter(
    (c) =>
      !c.includes('connected-systems') &&
      !c.includes('csapi') &&
      !c.includes('swecommon') &&
      !c.includes('sensorml')
  )
}
</script>

<template>
  <div class="server-connect">
    <!-- Connection Form -->
    <Panel header="Server Connection">
      <div class="form-grid">
        <div class="form-row">
          <label>Server</label>
          <Select
            v-model="selectedPreset"
            :options="presets"
            optionLabel="label"
            placeholder="Select a server"
            class="w-full"
          />
          <small class="hint">{{ selectedPreset?.description }}</small>
        </div>

        <div v-if="!selectedPreset?.proxyPath" class="form-row">
          <label>Custom URL</label>
          <InputText
            v-model="customUrl"
            placeholder="https://example.com/api"
            class="w-full"
          />
        </div>

        <div class="form-row">
          <label>Username (optional)</label>
          <InputText v-model="username" placeholder="username" class="w-full" />
        </div>

        <div class="form-row">
          <label>Password (optional)</label>
          <Password
            v-model="password"
            :feedback="false"
            toggleMask
            placeholder="password"
            class="w-full"
          />
        </div>

        <div class="form-actions">
          <Button
            v-if="!connectionResult.connected"
            label="Connect"
            icon="pi pi-link"
            :loading="connecting"
            @click="connect"
          />
          <Button
            v-else
            label="Disconnect"
            icon="pi pi-times"
            severity="secondary"
            @click="disconnect"
          />
        </div>
      </div>

      <Message v-if="error" severity="error" :closable="false" class="mt-3">
        {{ error }}
      </Message>

      <div v-if="connecting" class="connecting-spinner">
        <ProgressSpinner style="width: 40px; height: 40px" />
        <span>Connecting...</span>
      </div>
    </Panel>

    <!-- Results -->
    <template v-if="connectionResult.connected">
      <!-- Landing Page Info -->
      <Panel header="Server Info" class="mt-4" toggleable>
        <div class="info-grid">
          <div v-if="connectionResult.landingPage?.title">
            <strong>Title:</strong> {{ connectionResult.landingPage.title }}
          </div>
          <div v-if="connectionResult.landingPage?.description">
            <strong>Description:</strong>
            {{ connectionResult.landingPage.description }}
          </div>
        </div>
      </Panel>

      <!-- Conformance Classes -->
      <Panel
        v-if="connectionResult.conformance.length > 0"
        header="Conformance Classes"
        class="mt-4"
        toggleable
      >
        <div v-if="csapiConformance(connectionResult.conformance).length > 0">
          <h4 style="margin-top: 0">CSAPI / SensorML / SWE Common</h4>
          <ul class="conformance-list">
            <li
              v-for="c in csapiConformance(connectionResult.conformance)"
              :key="c"
            >
              {{ c }}
            </li>
          </ul>
        </div>
        <div v-if="otherConformance(connectionResult.conformance).length > 0">
          <h4>Other</h4>
          <ul class="conformance-list">
            <li
              v-for="c in otherConformance(connectionResult.conformance)"
              :key="c"
            >
              {{ c }}
            </li>
          </ul>
        </div>
        <p style="margin-bottom: 0; color: #64748b">
          Total: {{ connectionResult.conformance.length }} conformance classes
        </p>
      </Panel>

      <!-- Collections -->
      <Panel
        v-if="connectionResult.collections.length > 0"
        header="Collections"
        class="mt-4"
        toggleable
      >
        <table class="collections-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Title</th>
              <th>Description</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="col in connectionResult.collections"
              :key="col.id"
            >
              <td><code>{{ col.id }}</code></td>
              <td>{{ col.title || '—' }}</td>
              <td>{{ col.description || '—' }}</td>
            </tr>
          </tbody>
        </table>
      </Panel>

      <!-- Raw JSON -->
      <Panel header="Raw Response" class="mt-4" toggleable collapsed>
        <pre class="raw-json">{{ JSON.stringify(connectionResult.raw, null, 2) }}</pre>
      </Panel>
    </template>
  </div>
</template>

<style scoped>
.server-connect {
  padding-bottom: 2rem;
}

.form-grid {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.form-row {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.form-row label {
  font-weight: 600;
  font-size: 0.9rem;
}

.hint {
  color: #64748b;
  font-size: 0.85rem;
}

.form-actions {
  margin-top: 0.5rem;
}

.w-full {
  width: 100%;
}

.mt-3 {
  margin-top: 0.75rem;
}

.mt-4 {
  margin-top: 1rem;
}

.connecting-spinner {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-top: 1rem;
  color: #64748b;
}

.info-grid {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.conformance-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.conformance-list li {
  padding: 0.25rem 0;
  font-size: 0.85rem;
  font-family: monospace;
  word-break: break-all;
  border-bottom: 1px solid #f1f5f9;
}

.collections-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.9rem;
}

.collections-table th,
.collections-table td {
  padding: 0.5rem 0.75rem;
  text-align: left;
  border-bottom: 1px solid #e2e8f0;
}

.collections-table th {
  background: #f8fafc;
  font-weight: 600;
}

.collections-table code {
  background: #f1f5f9;
  padding: 0.1rem 0.3rem;
  border-radius: 3px;
  font-size: 0.85rem;
}

.raw-json {
  background: #f8fafc;
  padding: 1rem;
  border-radius: 6px;
  overflow-x: auto;
  font-size: 0.8rem;
  max-height: 400px;
  overflow-y: auto;
  margin: 0;
}
</style>
