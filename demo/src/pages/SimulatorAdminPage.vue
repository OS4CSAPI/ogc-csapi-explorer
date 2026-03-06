<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Message from 'primevue/message'
import Panel from 'primevue/panel'
import ProgressSpinner from 'primevue/progressspinner'
import Password from 'primevue/password'

// ── Client-side auth gate ────────────────────────────────────────────────
const AUTH_USER = 'admin'
const AUTH_PASS = 'admin'
const SESSION_KEY = 'sim-admin-auth'

const authenticated = ref(sessionStorage.getItem(SESSION_KEY) === 'true')
const loginUser = ref('')
const loginPass = ref('')
const loginError = ref('')

function attemptLogin() {
  if (loginUser.value === AUTH_USER && loginPass.value === AUTH_PASS) {
    authenticated.value = true
    sessionStorage.setItem(SESSION_KEY, 'true')
    loginError.value = ''
  } else {
    loginError.value = 'Invalid credentials'
  }
}

function logout() {
  authenticated.value = false
  sessionStorage.removeItem(SESSION_KEY)
}

// ── Simulator service URL ────────────────────────────────────────────────
// Default to Fly.io, allow override via input
const defaultUrl = 'https://os4csapi-simulator.fly.dev'
const serviceUrl = ref(defaultUrl)
const urlInput = ref(defaultUrl)

// ── Status polling ──────────────────────────────────────────────────
interface SimStatus {
  running: boolean
  tick: number
  uav_lat: number
  uav_lon: number
  detecting: string[]
  published: number
  errors: number
  detecting_ticks: number
  elapsed_s: number
  message: string
  config: {
    duration_s: number
    interval_s: number
    speed_kmh: number
    start_offset_s: number
  }
}

interface LocStatus {
  running: boolean
  cycles: number
  lobs_consumed: number
  fixes_published: number
  last_fix: {
    lat: number
    lon: number
    cep50_m: number
    residual_m: number
    n: number
    sensors: string
    classification: string
  } | null
  elapsed_s: number
  errors: number
  message: string
}

const status = ref<SimStatus | null>(null)
const locStatus = ref<LocStatus | null>(null)
const connected = ref(false)
const pollError = ref('')
const actionMessage = ref('')
const actionSeverity = ref<'success' | 'error' | 'info'>('info')
const loading = ref(false)
const locLoading = ref(false)
const clearing = ref(false)
const resetting = ref(false)

// Config form
const cfgDuration = ref('3600')
const cfgInterval = ref('5')
const cfgSpeed = ref('12')
const cfgOffset = ref('500')

let pollTimer: ReturnType<typeof setInterval> | null = null
let consecutiveFailures = 0
const DISCONNECT_THRESHOLD = 3  // Only show disconnected after N consecutive failures

// ── Helpers ──────────────────────────────────────────────────────────
async function apiFetch(path: string, opts?: RequestInit) {
  const resp = await fetch(`${serviceUrl.value}${path}`, {
    ...opts,
    headers: { 'Content-Type': 'application/json', ...(opts?.headers || {}) },
  })
  return resp.json()
}

async function pollStatus() {
  try {
    const data = await apiFetch('/status')
    status.value = data
    connected.value = true
    pollError.value = ''
    consecutiveFailures = 0
  } catch (e: any) {
    consecutiveFailures++
    pollError.value = e.message || 'Cannot reach simulator service'
    // Only mark disconnected after several consecutive failures
    // to avoid UI blink from a single dropped request
    if (consecutiveFailures >= DISCONNECT_THRESHOLD) {
      connected.value = false
    }
  }
}

async function pollLocalizerStatus() {
  try {
    const data = await apiFetch('/localizer/status')
    locStatus.value = data
  } catch { /* localizer endpoints may not exist on older builds */ }
}

function startPolling() {
  stopPolling()
  pollStatus()
  pollLocalizerStatus()
  pollTimer = setInterval(() => { pollStatus(); pollLocalizerStatus() }, 2000)
}

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

// ── Actions ──────────────────────────────────────────────────────────
async function connectService() {
  serviceUrl.value = urlInput.value.replace(/\/+$/, '')
  startPolling()
}

async function startSim() {
  loading.value = true
  actionMessage.value = ''
  try {
    const data = await apiFetch('/start', {
      method: 'POST',
      body: JSON.stringify({
        duration_s: parseInt(cfgDuration.value) || 3600,
        interval_s: parseFloat(cfgInterval.value) || 5,
        speed_kmh: parseFloat(cfgSpeed.value) || 12,
        start_offset_s: parseFloat(cfgOffset.value) || 0,
      }),
    })
    actionMessage.value = data.message
    actionSeverity.value = data.ok ? 'success' : 'error'
  } catch (e: any) {
    actionMessage.value = e.message
    actionSeverity.value = 'error'
  } finally {
    loading.value = false
  }
}

async function stopSim() {
  loading.value = true
  actionMessage.value = ''
  try {
    const data = await apiFetch('/stop', { method: 'POST' })
    actionMessage.value = data.message
    actionSeverity.value = data.ok ? 'success' : 'error'
  } catch (e: any) {
    actionMessage.value = e.message
    actionSeverity.value = 'error'
  } finally {
    loading.value = false
  }
}

async function clearObs() {
  if (!confirm('Clear all sensor/localizer data? SENREP reports will be preserved.')) return
  clearing.value = true
  actionMessage.value = ''
  try {
    const data = await apiFetch('/clear', { method: 'POST' })
    actionMessage.value = data.message
    actionSeverity.value = data.ok ? 'success' : 'error'
  } catch (e: any) {
    actionMessage.value = e.message
    actionSeverity.value = 'error'
  } finally {
    clearing.value = false
  }
}

async function resetDemo() {
  if (!confirm('Full demo reset: delete ALL sim data AND reports. Detection rings will be re-seeded on next start. Continue?')) return
  resetting.value = true
  actionMessage.value = ''
  try {
    const data = await apiFetch('/reset', { method: 'POST' })
    actionMessage.value = data.message
    actionSeverity.value = data.ok ? 'success' : 'error'
  } catch (e: any) {
    actionMessage.value = e.message
    actionSeverity.value = 'error'
  } finally {
    resetting.value = false
  }
}

// ── Localizer Actions ────────────────────────────────────────────────
async function startLocalizer() {
  locLoading.value = true
  actionMessage.value = ''
  try {
    const data = await apiFetch('/localizer/start', { method: 'POST' })
    actionMessage.value = data.message
    actionSeverity.value = data.ok ? 'success' : 'error'
  } catch (e: any) {
    actionMessage.value = e.message
    actionSeverity.value = 'error'
  } finally {
    locLoading.value = false
  }
}

async function stopLocalizer() {
  locLoading.value = true
  actionMessage.value = ''
  try {
    const data = await apiFetch('/localizer/stop', { method: 'POST' })
    actionMessage.value = data.message
    actionSeverity.value = data.ok ? 'success' : 'error'
  } catch (e: any) {
    actionMessage.value = e.message
    actionSeverity.value = 'error'
  } finally {
    locLoading.value = false
  }
}

// ── Computed ─────────────────────────────────────────────────────────
const elapsedFormatted = computed(() => {
  if (!status.value) return '—'
  const s = status.value.elapsed_s
  const m = Math.floor(s / 60)
  const sec = Math.floor(s % 60)
  return `${m}m ${sec}s`
})

const detectionRate = computed(() => {
  if (!status.value || !status.value.tick) return '—'
  return `${Math.round((status.value.detecting_ticks / status.value.tick) * 100)}%`
})

const locElapsedFormatted = computed(() => {
  if (!locStatus.value) return '—'
  const s = locStatus.value.elapsed_s
  const m = Math.floor(s / 60)
  const sec = Math.floor(s % 60)
  return `${m}m ${sec}s`
})

// ── Lifecycle ────────────────────────────────────────────────────────
onMounted(() => {
  startPolling()
})

onUnmounted(() => {
  stopPolling()
})
</script>

<template>
  <div class="admin-page">
    <h2><i class="pi pi-cog"></i> Simulator Admin</h2>

    <!-- Auth gate -->
    <div v-if="!authenticated" class="login-gate">
      <Panel header="Authentication Required" class="login-panel">
        <p class="login-desc">Enter credentials to access the simulator admin console.</p>
        <div class="login-form">
          <div class="login-field">
            <label for="login-user">Username</label>
            <InputText id="login-user" v-model="loginUser" placeholder="Username" @keyup.enter="attemptLogin" />
          </div>
          <div class="login-field">
            <label for="login-pass">Password</label>
            <Password id="login-pass" v-model="loginPass" placeholder="Password" :feedback="false" toggleMask @keyup.enter="attemptLogin" />
          </div>
          <Message v-if="loginError" severity="error" :closable="false" class="mt-2">{{ loginError }}</Message>
          <Button label="Sign In" icon="pi pi-sign-in" @click="attemptLogin" class="mt-3 login-btn" />
        </div>
      </Panel>
    </div>

    <!-- Authenticated content -->
    <template v-else>

    <div class="admin-toolbar">
      <Button label="Sign Out" icon="pi pi-sign-out" severity="secondary" size="small" text @click="logout" />
    </div>

    <!-- Service URL -->
    <Panel header="Service Connection" class="mb-4">
      <div class="url-row">
        <InputText v-model="urlInput" placeholder="Simulator service URL" class="url-input" />
        <Button label="Connect" icon="pi pi-link" @click="connectService" size="small" />
      </div>
      <div class="connection-status mt-2">
        <span v-if="connected" class="status-badge status-connected">
          <i class="pi pi-check-circle"></i> Connected
        </span>
        <span v-else class="status-badge status-disconnected">
          <i class="pi pi-times-circle"></i> {{ pollError || 'Disconnected' }}
        </span>
      </div>
    </Panel>

    <!-- Action message -->
    <Message v-if="actionMessage" :severity="actionSeverity" :closable="true" @close="actionMessage = ''" class="mb-4">
      {{ actionMessage }}
    </Message>

    <!-- Simulation Status -->
    <Panel header="Simulation Status" class="mb-4">
      <div v-if="!connected" class="placeholder-text">
        Not connected to simulator service
      </div>
      <div v-else-if="!status" class="placeholder-text">
        <ProgressSpinner style="width: 24px; height: 24px" /> Loading…
      </div>
      <div v-else class="status-grid">
        <div class="stat-card" :class="status.running ? 'stat-running' : 'stat-stopped'">
          <div class="stat-label">State</div>
          <div class="stat-value">
            <span class="state-dot" :class="status.running ? 'dot-green' : 'dot-gray'"></span>
            {{ status.running ? 'RUNNING' : (status.message || 'IDLE') }}
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Tick</div>
          <div class="stat-value">{{ status.tick }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Elapsed</div>
          <div class="stat-value">{{ elapsedFormatted }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Published</div>
          <div class="stat-value">{{ status.published }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Errors</div>
          <div class="stat-value" :class="status.errors > 0 ? 'text-error' : ''">{{ status.errors }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Detection Rate</div>
          <div class="stat-value">{{ detectionRate }}</div>
        </div>
        <div class="stat-card stat-wide">
          <div class="stat-label">UAV Position</div>
          <div class="stat-value">{{ status.uav_lat.toFixed(6) }}, {{ status.uav_lon.toFixed(6) }}</div>
        </div>
        <div class="stat-card stat-wide">
          <div class="stat-label">Detecting Nodes</div>
          <div class="stat-value">
            <span v-if="status.detecting.length">
              <span v-for="n in status.detecting" :key="n" class="node-badge">{{ n }}</span>
            </span>
            <span v-else class="text-muted">None</span>
          </div>
        </div>
      </div>
    </Panel>

    <!-- Controls -->
    <Panel header="Controls" class="mb-4">
      <div class="config-grid">
        <div class="config-field">
          <label>Duration (s)</label>
          <InputText v-model="cfgDuration" type="number" size="small" />
        </div>
        <div class="config-field">
          <label>Interval (s)</label>
          <InputText v-model="cfgInterval" type="number" size="small" />
        </div>
        <div class="config-field">
          <label>Speed (km/h)</label>
          <InputText v-model="cfgSpeed" type="number" size="small" />
        </div>
        <div class="config-field">
          <label>Start Offset (s)</label>
          <InputText v-model="cfgOffset" type="number" size="small" />
        </div>
      </div>

      <div class="action-row mt-3">
        <Button
          label="Start Simulation"
          icon="pi pi-play"
          severity="success"
          :loading="loading"
          :disabled="!connected || (status?.running ?? false)"
          @click="startSim"
        />
        <Button
          label="Stop Simulation"
          icon="pi pi-stop"
          severity="danger"
          :loading="loading"
          :disabled="!connected || !(status?.running ?? false)"
          @click="stopSim"
        />
        <Button
          label="Clear Sim Data"
          icon="pi pi-trash"
          severity="warn"
          :loading="clearing"
          :disabled="!connected || (status?.running ?? false) || (locStatus?.running ?? false)"
          @click="clearObs"
        />
        <Button
          label="Full Demo Reset"
          icon="pi pi-refresh"
          severity="danger"
          :loading="resetting"
          :disabled="!connected || (status?.running ?? false) || (locStatus?.running ?? false)"
          @click="resetDemo"
        />
      </div>
    </Panel>

    <!-- Localizer Status -->
    <Panel header="LOB Localizer" class="mb-4">
      <div v-if="!connected" class="placeholder-text">
        Not connected to simulator service
      </div>
      <div v-else-if="!locStatus" class="placeholder-text">
        <ProgressSpinner style="width: 24px; height: 24px" /> Loading…
      </div>
      <div v-else>
        <div class="status-grid">
          <div class="stat-card" :class="locStatus.running ? 'stat-running' : 'stat-stopped'">
            <div class="stat-label">State</div>
            <div class="stat-value">
              <span class="state-dot" :class="locStatus.running ? 'dot-gold' : 'dot-gray'"></span>
              {{ locStatus.running ? 'RUNNING' : 'IDLE' }}
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-label">Cycles</div>
            <div class="stat-value">{{ locStatus.cycles }}</div>
          </div>
          <div class="stat-card">
            <div class="stat-label">Elapsed</div>
            <div class="stat-value">{{ locElapsedFormatted }}</div>
          </div>
          <div class="stat-card">
            <div class="stat-label">LOBs Consumed</div>
            <div class="stat-value">{{ locStatus.lobs_consumed }}</div>
          </div>
          <div class="stat-card">
            <div class="stat-label">Fixes Published</div>
            <div class="stat-value loc-fixes">{{ locStatus.fixes_published }}</div>
          </div>
          <div class="stat-card">
            <div class="stat-label">Errors</div>
            <div class="stat-value" :class="locStatus.errors > 0 ? 'text-error' : ''">{{ locStatus.errors }}</div>
          </div>
        </div>

        <!-- Last fix detail -->
        <div v-if="locStatus.last_fix" class="loc-fix-detail mt-3">
          <div class="stat-label" style="margin-bottom: 0.5rem">Latest Fix</div>
          <div class="status-grid">
            <div class="stat-card stat-wide">
              <div class="stat-label">Position</div>
              <div class="stat-value">{{ locStatus.last_fix.lat.toFixed(6) }}, {{ locStatus.last_fix.lon.toFixed(6) }}</div>
            </div>
            <div class="stat-card">
              <div class="stat-label">CEP50</div>
              <div class="stat-value">{{ locStatus.last_fix.cep50_m.toFixed(0) }} m</div>
            </div>
            <div class="stat-card">
              <div class="stat-label">Residual</div>
              <div class="stat-value">{{ locStatus.last_fix.residual_m.toFixed(1) }} m</div>
            </div>
            <div class="stat-card">
              <div class="stat-label">LOBs Used</div>
              <div class="stat-value">{{ locStatus.last_fix.n }}</div>
            </div>
            <div class="stat-card">
              <div class="stat-label">Classification</div>
              <div class="stat-value loc-class">{{ locStatus.last_fix.classification }}</div>
            </div>
            <div class="stat-card stat-wide">
              <div class="stat-label">Sensors</div>
              <div class="stat-value">
                <span v-for="s in locStatus.last_fix.sensors.split(',')" :key="s" class="node-badge node-badge-gold">{{ s }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Localizer controls -->
        <div class="action-row mt-3">
          <Button
            label="Start Localizer"
            icon="pi pi-play"
            severity="success"
            :loading="locLoading"
            :disabled="!connected || (locStatus?.running ?? false)"
            @click="startLocalizer"
          />
          <Button
            label="Stop Localizer"
            icon="pi pi-stop"
            severity="danger"
            :loading="locLoading"
            :disabled="!connected || !(locStatus?.running ?? false)"
            @click="stopLocalizer"
          />
        </div>
      </div>
    </Panel>

    <!-- Help -->
    <Panel header="Deployment" toggleable :collapsed="true">
      <div class="help-text">
        <p>The simulator service runs as a container on <strong>Fly.io</strong>.</p>
        <h4>Deploy / Update</h4>
        <pre>cd simulator
flyctl deploy</pre>
        <h4>Logs</h4>
        <pre>flyctl logs --app os4csapi-simulator</pre>
        <h4>Architecture</h4>
        <ul>
          <li>FastAPI + Uvicorn inside a Python 3.12 container</li>
          <li>Simulation runs in a background thread (not async)</li>
          <li>LOB Localizer runs in a separate background thread</li>
          <li>WLS bearing-intersection algorithm with CEP50 estimate</li>
          <li>Machine auto-suspends when idle (Fly.io free tier)</li>
          <li>Wakes on first HTTP request (~2s cold start)</li>
        </ul>
      </div>
    </Panel>

    </template><!-- v-else (authenticated) -->
  </div>
</template>

<style scoped>
.admin-page {
  max-width: 900px;
  margin: 0 auto;
  padding: 1.5rem 1rem;
}

.admin-page h2 {
  margin: 0 0 1.5rem;
  font-size: 1.6rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.mb-4 {
  margin-bottom: 1.25rem;
}

.mt-2 {
  margin-top: 0.5rem;
}

.mt-3 {
  margin-top: 0.75rem;
}

/* URL row */
.url-row {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.url-input {
  flex: 1;
  font-family: monospace;
  font-size: 0.85rem;
}

/* Connection badge */
.connection-status {
  font-size: 0.85rem;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.2rem 0.6rem;
  border-radius: 6px;
  font-weight: 600;
}

.status-connected {
  background: #dcfce7;
  color: #166534;
}

.status-disconnected {
  background: #fee2e2;
  color: #991b1b;
}

/* Status grid */
.status-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 0.75rem;
}

.stat-card {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 0.75rem;
}

.stat-wide {
  grid-column: span 2;
}

.stat-running {
  border-color: #86efac;
  background: #f0fdf4;
}

.stat-stopped {
  border-color: #e2e8f0;
}

.stat-label {
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #64748b;
  margin-bottom: 0.25rem;
}

.stat-value {
  font-size: 1.1rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.state-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  display: inline-block;
}

.dot-green {
  background: #22c55e;
  box-shadow: 0 0 6px #22c55e80;
}

.dot-gray {
  background: #94a3b8;
}

.text-error {
  color: #dc2626;
}

.text-muted {
  color: #94a3b8;
  font-weight: 400;
}

.node-badge {
  display: inline-block;
  background: #dbeafe;
  color: #1e40af;
  padding: 0.1rem 0.5rem;
  border-radius: 4px;
  font-size: 0.8rem;
  font-weight: 600;
  margin-right: 0.3rem;
}

.node-badge-gold {
  background: #fef3c7;
  color: #92400e;
}

/* Localizer specifics */
.dot-gold {
  background: #f59e0b;
  box-shadow: 0 0 6px #f59e0b80;
}

.loc-fixes {
  color: #b45309;
}

.loc-class {
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.loc-fix-detail {
  border-top: 1px solid #e2e8f0;
  padding-top: 0.75rem;
}

/* Config form */
.config-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 0.75rem;
}

.config-field label {
  display: block;
  font-size: 0.75rem;
  font-weight: 600;
  color: #475569;
  margin-bottom: 0.25rem;
}

.config-field :deep(input) {
  width: 100%;
}

/* Action buttons */
.action-row {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
}

/* Help */
.help-text {
  font-size: 0.9rem;
  line-height: 1.6;
}

.help-text pre {
  background: #1e293b;
  color: #e2e8f0;
  padding: 0.75rem 1rem;
  border-radius: 6px;
  overflow-x: auto;
  font-size: 0.8rem;
}

.help-text ul {
  padding-left: 1.25rem;
}

.placeholder-text {
  color: #94a3b8;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

/* Responsive */
@media (max-width: 600px) {
  .status-grid {
    grid-template-columns: 1fr 1fr;
  }
  .stat-wide {
    grid-column: span 2;
  }
  .config-grid {
    grid-template-columns: 1fr 1fr;
  }
  .action-row {
    flex-direction: column;
  }
  .action-row .p-button {
    width: 100%;
  }
}

.login-gate {
  display: flex;
  justify-content: center;
  margin-top: 2rem;
}

.login-panel {
  max-width: 400px;
  width: 100%;
}

.login-desc {
  color: var(--text-color-secondary);
  margin-bottom: 1rem;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.login-field {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.login-field label {
  font-weight: 600;
  font-size: 0.875rem;
}

.login-field .p-inputtext,
.login-field .p-password {
  width: 100%;
}

.login-btn {
  width: 100%;
}

.admin-toolbar {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 0.5rem;
}
</style>
