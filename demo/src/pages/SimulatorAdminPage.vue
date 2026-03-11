<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Message from 'primevue/message'
import Panel from 'primevue/panel'
import ProgressSpinner from 'primevue/progressspinner'
import Password from 'primevue/password'
import { useHealthCheck } from '../composables/useHealthCheck'
import { useObsStore } from '../composables/useObsStore'

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
// Default to Oracle VM (behind Caddy reverse proxy)
const defaultUrl = 'https://os4csapi-osh.duckdns.org/simulator'
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

const status = ref<SimStatus | null>(null)
const connected = ref(false)
const pollError = ref('')
const actionMessage = ref('')
const actionSeverity = ref<'success' | 'error' | 'info'>('info')
const loading = ref(false)
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

function startPolling() {
  stopPolling()
  pollStatus()
  pollTimer = setInterval(() => { pollStatus() }, 2000)
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

// ── Health Check ─────────────────────────────────────────────────────
const {
  checks: hcChecks,
  running: hcRunning,
  elapsed: hcElapsed,
  timestamp: hcTimestamp,
  summary: hcSummary,
  overallStatus: hcStatus,
  runAll: hcRunAll,
} = useHealthCheck()

const hcGrouped = computed(() => {
  const groups: Record<string, typeof hcChecks.value> = {}
  for (const c of hcChecks.value) {
    if (!groups[c.group]) groups[c.group] = []
    groups[c.group].push(c)
  }
  return groups
})

// ── Observation Store ────────────────────────────────────────────────
const {
  counts: obsCounts,
  fetching: obsFetching,
  purging: obsPurging,
  purgeLog: obsPurgeLog,
  lastFetched: obsLastFetched,
  totalObs,
  groupTotals,
  fetchCounts: obsFetchCounts,
  purgeAll: obsPurgeAll,
  PUBLISHER_GROUPS,
} = useObsStore()

const showPurgeConfirm = ref(false)

function confirmPurge() {
  showPurgeConfirm.value = true
}

async function executePurge() {
  showPurgeConfirm.value = false
  await obsPurgeAll()
}

function getCountEntry(dsId: string) {
  return obsCounts.value.find(c => c.dsId === dsId) ?? null
}

function formatCount(dsId: string): string {
  const entry = getCountEntry(dsId)
  if (!entry) return '—'
  if (entry.error) return entry.error
  if (entry.count === null) return '…'
  return entry.count.toLocaleString()
}

// ── Health Check Console (terminal-style output) ────────────────────
const consoleOutput = computed(() => {
  if (!hcChecks.value.length) return ''
  const lines: string[] = []
  lines.push('=' .repeat(60))
  lines.push('  OS4CSAPI Production Health Check')
  if (hcTimestamp.value) {
    lines.push(`  ${hcTimestamp.value}`)
  }
  lines.push('=' .repeat(60))
  lines.push('')
  for (const [groupName, checks] of Object.entries(hcGrouped.value)) {
    lines.push(`  ── ${groupName} ──`)
    for (const c of checks) {
      const icon = c.status === 'pass' ? '✅' : c.status === 'fail' ? '❌' : '⏭️'
      const detail = c.detail ? `  —  ${c.detail}` : ''
      lines.push(`  ${icon}  ${c.name}${detail}`)
    }
    lines.push('')
  }
  lines.push('-'.repeat(60))
  const s = hcSummary.value
  if (s.failed > 0) {
    lines.push('  ❌  HEALTH CHECK FAILED')
  } else {
    lines.push('  ✅  HEALTH CHECK PASSED')
  }
  lines.push(`  ${s.passed} passed, ${s.failed} failed, ${s.skipped} skipped  (${s.total} total, ${hcElapsed.value}ms)`)
  lines.push('-'.repeat(60))
  return lines.join('\n')
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
    <h2><i class="pi pi-cog"></i> Admin</h2>

    <!-- Auth gate -->
    <div v-if="!authenticated" class="login-gate">
      <Panel header="Authentication Required" class="login-panel">
        <p class="login-desc">Enter credentials to access the admin console.</p>
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
          :disabled="!connected || (status?.running ?? false)"
          @click="clearObs"
        />
        <Button
          label="Full Demo Reset"
          icon="pi pi-refresh"
          severity="danger"
          :loading="resetting"
          :disabled="!connected || (status?.running ?? false)"
          @click="resetDemo"
        />
      </div>
    </Panel>

    <!-- Observation Store -->
    <Panel header="Observation Store" class="mb-4">
      <div class="obs-toolbar">
        <Button
          label="Fetch Counts"
          icon="pi pi-database"
          severity="info"
          :loading="obsFetching"
          @click="obsFetchCounts"
        />
        <Button
          label="Purge All Publisher Obs"
          icon="pi pi-trash"
          severity="danger"
          :loading="obsPurging"
          :disabled="obsFetching || obsPurging"
          @click="confirmPurge"
        />
        <span v-if="obsLastFetched && !obsFetching" class="obs-meta">
          Last fetched {{ obsLastFetched }} &mdash; {{ totalObs.toLocaleString() }} total
        </span>
      </div>

      <!-- Purge Confirmation -->
      <div v-if="showPurgeConfirm" class="purge-confirm mt-2">
        <Message severity="warn" :closable="false">
          <strong>Confirm Purge:</strong> This will permanently delete ALL observations from
          {{ PUBLISHER_GROUPS.reduce((n, g) => n + g.datastreams.length, 0) }} publisher datastreams
          (ISS, NWS, NDBC, CO-OPS). Simulator data is not affected.
        </Message>
        <div class="purge-actions mt-2">
          <Button label="Yes, Purge Everything" icon="pi pi-exclamation-triangle" severity="danger" @click="executePurge" />
          <Button label="Cancel" severity="secondary" text @click="showPurgeConfirm = false" />
        </div>
      </div>

      <!-- Group counts grid -->
      <div v-if="obsCounts.length && !obsFetching" class="obs-groups mt-2">
        <div v-for="group in PUBLISHER_GROUPS" :key="group.name" class="obs-group-card">
          <div class="obs-group-header">
            <i :class="group.icon"></i>
            <span class="obs-group-name">{{ group.name }}</span>
            <span class="obs-group-total">{{ (groupTotals[group.name] ?? 0).toLocaleString() }}</span>
          </div>
          <div class="obs-ds-list">
            <div
              v-for="ds in group.datastreams"
              :key="ds.id"
              class="obs-ds-row"
            >
              <span class="obs-ds-label">{{ ds.label }}</span>
              <span class="obs-ds-count" :class="getCountEntry(ds.id)?.error ? 'obs-ds-error' : ''">
                {{ formatCount(ds.id) }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Running spinner -->
      <div v-if="obsFetching" class="hc-running mt-2">
        <ProgressSpinner style="width: 20px; height: 20px" /> Fetching observation counts…
      </div>

      <!-- Purge log -->
      <div v-if="obsPurgeLog.length" class="console-terminal mt-2">
        <pre class="console-pre">{{ obsPurgeLog.join('\n') }}</pre>
      </div>

      <!-- No data yet -->
      <div v-if="!obsCounts.length && !obsFetching && !obsPurgeLog.length" class="placeholder-text mt-2">
        Click "Fetch Counts" to query observation counts for all publisher datastreams.
      </div>
    </Panel>

    <!-- Production Health Check -->
    <Panel header="Production Health Check" class="mb-4">
      <div class="hc-toolbar">
        <Button
          label="Run Health Check"
          icon="pi pi-play"
          severity="info"
          :loading="hcRunning"
          @click="hcRunAll"
        />
        <span v-if="hcTimestamp && !hcRunning" class="hc-meta">
          {{ hcSummary.total }} checks in {{ hcElapsed }}ms
        </span>
      </div>

      <!-- Overall status badge -->
      <div v-if="hcChecks.length && !hcRunning" class="hc-overall mt-2">
        <span class="hc-badge" :class="hcStatus === 'pass' ? 'hc-pass' : 'hc-fail'">
          <i :class="hcStatus === 'pass' ? 'pi pi-check-circle' : 'pi pi-times-circle'"></i>
          {{ hcStatus === 'pass' ? 'ALL CHECKS PASSED' : `${hcSummary.failed} FAILED` }}
          <span class="hc-counts">
            {{ hcSummary.passed }} passed, {{ hcSummary.failed }} failed, {{ hcSummary.skipped }} skipped
          </span>
        </span>
      </div>

      <!-- Running spinner -->
      <div v-if="hcRunning" class="hc-running mt-2">
        <ProgressSpinner style="width: 20px; height: 20px" /> Running checks…
      </div>

      <!-- Console output (terminal-style) -->
      <div v-if="consoleOutput" class="console-terminal mt-2">
        <pre class="console-pre">{{ consoleOutput }}</pre>
      </div>

      <!-- Placeholder when no results yet -->
      <div v-if="!hcChecks.length && !hcRunning" class="placeholder-text mt-2">
        Click "Run Health Check" to verify all {{ Object.keys(hcGrouped).length || '' }} server resources.
      </div>
    </Panel>

    <!-- Help -->
    <Panel header="Deployment" toggleable :collapsed="true">
      <div class="help-text">
        <p>The simulator runs on the <strong>Oracle VM</strong> behind Caddy reverse proxy.</p>
        <h4>Update Code</h4>
        <pre>scp simulator/main.py simulator/engine.py ubuntu@129.80.248.53:/home/ubuntu/simulator/
ssh ubuntu@129.80.248.53 "sudo systemctl restart simulator"</pre>
        <h4>Logs</h4>
        <pre>ssh ubuntu@129.80.248.53 "sudo journalctl -u simulator -f"</pre>
        <h4>Architecture</h4>
        <ul>
          <li>FastAPI + Uvicorn on Oracle VM (systemd service)</li>
          <li>Caddy reverse proxy: <code>/simulator/*</code> → <code>localhost:8000</code></li>
          <li>Simulation runs in a background thread (not async)</li>
          <li>LOB Localizer runs as a separate standalone service</li>
          <li>WLS bearing-intersection algorithm with CEP50 estimate</li>
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

/* ── Health Check ────────────────────────────────────────────── */
.hc-toolbar {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.hc-meta {
  font-size: 0.8rem;
  color: #64748b;
}

.hc-overall {
  margin-bottom: 0.5rem;
}

.hc-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.35rem 0.8rem;
  border-radius: 6px;
  font-weight: 700;
  font-size: 0.85rem;
}

.hc-pass {
  background: #dcfce7;
  color: #166534;
}

.hc-fail {
  background: #fee2e2;
  color: #991b1b;
}

.hc-counts {
  font-weight: 400;
  margin-left: 0.5rem;
  opacity: 0.8;
}

.hc-running {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #64748b;
  font-size: 0.85rem;
}

/* ── Console Terminal ──────────────────────────────────────── */
.console-terminal {
  background: #0d1117;
  border: 1px solid #30363d;
  border-radius: 8px;
  overflow: auto;
  max-height: 520px;
}

.console-pre {
  color: #c9d1d9;
  font-family: 'Cascadia Code', 'Fira Code', 'JetBrains Mono', 'Consolas', monospace;
  font-size: 0.82rem;
  line-height: 1.5;
  padding: 1rem 1.25rem;
  margin: 0;
  white-space: pre;
  overflow-x: auto;
}

/* ── Observation Store ────────────────────────────────────── */
.obs-toolbar {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.obs-meta {
  font-size: 0.8rem;
  color: #64748b;
}

.obs-groups {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 0.75rem;
}

.obs-group-card {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  overflow: hidden;
}

.obs-group-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.6rem 0.75rem;
  background: #f1f5f9;
  border-bottom: 1px solid #e2e8f0;
  font-weight: 700;
  font-size: 0.85rem;
}

.obs-group-name {
  flex: 1;
}

.obs-group-total {
  font-family: 'Cascadia Code', 'Consolas', monospace;
  font-size: 0.9rem;
  color: #0369a1;
}

.obs-ds-list {
  padding: 0.25rem 0;
}

.obs-ds-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.2rem 0.75rem;
  font-size: 0.8rem;
}

.obs-ds-row:hover {
  background: #e2e8f0;
}

.obs-ds-label {
  color: #475569;
}

.obs-ds-count {
  font-family: 'Cascadia Code', 'Consolas', monospace;
  font-weight: 600;
  color: #334155;
  min-width: 4rem;
  text-align: right;
}

.obs-ds-error {
  color: #dc2626;
  font-weight: 400;
  font-family: inherit;
}

.purge-confirm {
  border-left: 3px solid #f59e0b;
  padding-left: 0.5rem;
}

.purge-actions {
  display: flex;
  gap: 0.5rem;
}
</style>
