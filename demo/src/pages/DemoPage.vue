<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { connection } from '../state'
import { apiFetch } from '../api'

// ── Types ──────────────────────────────────────────────────────────
interface SensorArray {
  id: string
  serverId: string
  label: string
  lat: number
  lon: number
  subsystemCount: number | null
  datastreamCount: number | null
  controlStreamCount: number | null
  datastreams: DatastreamInfo[]
  health: HealthSnapshot | null
}

interface DatastreamInfo {
  id: string
  name: string
  dsType: string
  obsCount: number | null
  latestObs: any | null
  latestTime: string | null
}

interface HealthSnapshot {
  cpuLoad: number
  memUsedMB: number
  tempC: number
  latencyMs: number
  uptimeS: number
}

interface SceneSummary {
  trackCount: number
  activityLevel: number
}

interface SenrepEntry {
  id: string
  contactId: string
  operator: string
  classification: string
  reportType: string
  lat: number
  lon: number
  strNo: string
  comments: string
  time: string
}

interface TrackEntry {
  id: string
  uid: string
  name: string
  description: string
  lon: number
  lat: number
}

// ── Known sensor array IDs ──────────────────────────────────────────
const SENSOR_ARRAYS = [
  { id: 'AZ-MA-1', serverId: '04ng', label: 'AZ-MA-1 — Sensor Array 1', lat: 31.5550, lon: -110.3510 },
  { id: 'AZ-MA-2', serverId: '04o0', label: 'AZ-MA-2 — Sensor Array 2', lat: 31.5570, lon: -110.3480 },
  { id: 'AZ-MA-3', serverId: '04og', label: 'AZ-MA-3 — Sensor Array 3', lat: 31.5540, lon: -110.3450 },
]

const NETWORK = { serverId: '04n0', label: 'AZ-MA-NET — Network Fused' }

// ── v2.5 doctrine systems ───────────────────────────────────────────
const STRING_PROCESSOR = { serverId: '05f0', label: 'AZ-STRPROC-ALPHA — String Processor' }
const MONITORING_TEAM = { serverId: '05eg', label: 'AZ-MON-TEAM-A — Monitoring Team' }

// ── Datastream type classification ──────────────────────────────────
const DS_TYPE_MAP: Record<string, string> = {
  lob: '🎯 LOB',
  ssl: '📡 SSL',
  sst: '🔗 SST',
  track_update: '🏷️ Track',
  triangulated_position: '📍 Triangulated',
  classification_probs: '🤖 Classification',
  health: '💚 Health',
  scene_summary: '📊 Scene',
  track_state: '🛤️ Track State',
  predicted_position: '🔮 Predicted Pos',
  senrep: '📋 SENREP',
}

function classifyDatastream(name: string): string {
  const lower = name.toLowerCase()
  if (lower.includes('lob') || lower.includes('line_of_bearing')) return 'lob'
  if (lower.includes('ssl') || lower.includes('sound_source_loc')) return 'ssl'
  if (lower.includes('sst') || lower.includes('sound_source_track')) return 'sst'
  if (lower.includes('track_update') || lower.includes('track update')) return 'track_update'
  if (lower.includes('triangulat')) return 'triangulated_position'
  if (lower.includes('classif')) return 'classification_probs'
  if (lower.includes('health')) return 'health'
  if (lower.includes('scene') || lower.includes('summary')) return 'scene_summary'
  if (lower.includes('track_state') || lower.includes('track state')) return 'track_state'
  if (lower.includes('predicted') || lower.includes('prediction')) return 'predicted_position'
  if (lower.includes('senrep') || lower.includes('sensor report')) return 'senrep'
  return 'unknown'
}

// ── Reactive state ──────────────────────────────────────────────────
const sensors = ref<SensorArray[]>([])
const networkDatastreams = ref<DatastreamInfo[]>([])
const stringProcDatastreams = ref<DatastreamInfo[]>([])
const monitoringDatastreams = ref<DatastreamInfo[]>([])
const sceneSummary = ref<SceneSummary | null>(null)
const loading = ref(false)
const lastRefresh = ref<string | null>(null)
const autoRefresh = ref(false)
const refreshInterval = ref<number | null>(null)
const totalObsCount = ref(0)
const senrepReports = ref<SenrepEntry[]>([])
const senrepCount = ref(0)
const activeTracks = ref<TrackEntry[]>([])
const error = ref<string | null>(null)

const SENREP_DS_ID = '044g'

const isConnectedToOSH = computed(() => {
  return connection.connected && connection.baseUrl.includes('/api/osh')
})

// ── Fetch helpers ───────────────────────────────────────────────────
async function fetchJson(path: string): Promise<any> {
  const res = await apiFetch(path)
  if (!res.ok) throw new Error(res.error || `HTTP ${res.status}`)
  return res.data
}

async function fetchDatastreamsForSystem(systemId: string): Promise<DatastreamInfo[]> {
  try {
    const data = await fetchJson(`/systems/${systemId}/datastreams?limit=50`)
    const items = data?.items || []
    return items.map((ds: any) => ({
      id: ds.id || ds['@id'] || '',
      name: ds.name || ds.label || ds.id || '',
      dsType: classifyDatastream(ds.name || ds.label || ''),
      obsCount: null,
      latestObs: null,
      latestTime: null,
    }))
  } catch {
    return []
  }
}

async function fetchLatestObs(dsId: string): Promise<{ obs: any; count: number } | null> {
  try {
    const data = await fetchJson(`/datastreams/${dsId}/observations?limit=1&resultTime=latest`)
    const items = data?.items || []
    const count = typeof data?.numberMatched === 'number' ? data.numberMatched : (items.length || 0)
    return { obs: items[0] || null, count }
  } catch {
    return null
  }
}

async function fetchControlStreamCount(systemId: string): Promise<number> {
  try {
    const data = await fetchJson(`/systems/${systemId}/controlstreams?limit=1`)
    return typeof data?.numberMatched === 'number' ? data.numberMatched : (data?.items?.length || 0)
  } catch {
    return 0
  }
}

async function fetchSubsystemCount(systemId: string): Promise<number> {
  try {
    const data = await fetchJson(`/systems/${systemId}/subsystems?limit=1`)
    return typeof data?.numberMatched === 'number' ? data.numberMatched : (data?.items?.length || 0)
  } catch {
    return 0
  }
}

// ── Main refresh ────────────────────────────────────────────────────
async function refresh() {
  if (!isConnectedToOSH.value) {
    error.value = 'Not connected to OSH server. Connect to the OSH endpoint first.'
    return
  }
  loading.value = true
  error.value = null
  let obsTotal = 0

  try {
    // Fetch all sensor arrays in parallel
    const sensorResults = await Promise.all(
      SENSOR_ARRAYS.map(async (sa) => {
        const [datastreams, subsystemCount, controlStreamCount] = await Promise.all([
          fetchDatastreamsForSystem(sa.serverId),
          fetchSubsystemCount(sa.serverId),
          fetchControlStreamCount(sa.serverId),
        ])

        // Fetch latest obs for each datastream in parallel
        await Promise.all(
          datastreams.map(async (ds) => {
            const result = await fetchLatestObs(ds.id)
            if (result) {
              ds.obsCount = result.count
              obsTotal += result.count
              ds.latestObs = result.obs
              ds.latestTime = result.obs?.resultTime || result.obs?.phenomenonTime || null
            }
          })
        )

        // Extract health from the health datastream
        const healthDs = datastreams.find((d) => d.dsType === 'health')
        let health: HealthSnapshot | null = null
        if (healthDs?.latestObs?.result) {
          const r = healthDs.latestObs.result
          health = {
            cpuLoad: r.cpuLoad ?? 0,
            memUsedMB: r.memUsedMB ?? 0,
            tempC: r.tempC ?? 0,
            latencyMs: r.latencyMs ?? 0,
            uptimeS: r.uptimeS ?? 0,
          }
        }

        return {
          id: sa.id,
          serverId: sa.serverId,
          label: sa.label,
          lat: sa.lat,
          lon: sa.lon,
          subsystemCount,
          datastreamCount: datastreams.length,
          controlStreamCount,
          datastreams,
          health,
        } as SensorArray
      })
    )
    sensors.value = sensorResults

    // Fetch network-level datastreams
    const netDs = await fetchDatastreamsForSystem(NETWORK.serverId)
    await Promise.all(
      netDs.map(async (ds) => {
        const result = await fetchLatestObs(ds.id)
        if (result) {
          ds.obsCount = result.count
          obsTotal += result.count
          ds.latestObs = result.obs
          ds.latestTime = result.obs?.resultTime || result.obs?.phenomenonTime || null
        }
      })
    )
    networkDatastreams.value = netDs

    // Extract scene summary from network
    const sceneDs = netDs.find((d) => d.dsType === 'scene_summary')
    if (sceneDs?.latestObs?.result) {
      sceneSummary.value = {
        trackCount: sceneDs.latestObs.result.trackCount ?? 0,
        activityLevel: sceneDs.latestObs.result.activityLevel ?? 0,
      }
    }

    // Fetch String Processor datastreams
    const spDs = await fetchDatastreamsForSystem(STRING_PROCESSOR.serverId)
    await Promise.all(
      spDs.map(async (ds) => {
        const result = await fetchLatestObs(ds.id)
        if (result) {
          ds.obsCount = result.count
          obsTotal += result.count
          ds.latestObs = result.obs
          ds.latestTime = result.obs?.resultTime || result.obs?.phenomenonTime || null
        }
      })
    )
    stringProcDatastreams.value = spDs

    // Fetch Monitoring Team datastreams
    const monDs = await fetchDatastreamsForSystem(MONITORING_TEAM.serverId)
    await Promise.all(
      monDs.map(async (ds) => {
        const result = await fetchLatestObs(ds.id)
        if (result) {
          ds.obsCount = result.count
          obsTotal += result.count
          ds.latestObs = result.obs
          ds.latestTime = result.obs?.resultTime || result.obs?.phenomenonTime || null
        }
      })
    )
    monitoringDatastreams.value = monDs

    // Fetch SENREP reports from DS 044g
    try {
      const senrepData = await fetchJson(`/datastreams/${SENREP_DS_ID}/observations?limit=50`)
      const senrepItems = (senrepData?.items || [])
        .filter((obs: any) => !obs['datastream@id'] || obs['datastream@id'] === SENREP_DS_ID)
      senrepCount.value = senrepItems.length
      senrepReports.value = senrepItems
        .map((obs: any) => {
          const r = obs.result || {}
          return {
            id: obs.id || '',
            contactId: r.title || '—',
            operator: r.senderId || '—',
            classification: r.tgtTyp || '—',
            reportType: r.subTyp || 'INIT',
            lat: r.etaLat ?? 0,
            lon: r.etaLon ?? 0,
            strNo: r.strNo || '—',
            comments: r.comments || '',
            time: obs.resultTime || obs.phenomenonTime || '',
          } as SenrepEntry
        })
        .sort((a: SenrepEntry, b: SenrepEntry) => new Date(b.time).getTime() - new Date(a.time).getTime())
    } catch { /* SENREP DS may not exist */ }

    // Fetch active tracks (SamplingFeatures created on first SENREP)
    try {
      const sfData = await fetchJson('/samplingFeatures?limit=50')
      const sfItems = (sfData?.items || sfData?.features || [])
        .filter((sf: any) => {
          const uid = sf.properties?.uid || sf.uid || ''
          return uid.startsWith('urn:os4csapi:track:C-')
        })
      activeTracks.value = sfItems.map((sf: any) => {
        const props = sf.properties || {}
        const coords = sf.geometry?.coordinates || [0, 0]
        return {
          id: sf.id || props.id || '',
          uid: props.uid || '',
          name: props.name || props.uid || '—',
          description: props.description || '',
          lon: coords[0] ?? 0,
          lat: coords[1] ?? 0,
        } as TrackEntry
      })
    } catch { /* SamplingFeatures may not exist */ }

    totalObsCount.value = obsTotal
    lastRefresh.value = new Date().toLocaleTimeString()
  } catch (err: any) {
    error.value = err.message || 'Unknown error'
  } finally {
    loading.value = false
  }
}

// ── Auto-refresh toggle ─────────────────────────────────────────────
function toggleAutoRefresh() {
  autoRefresh.value = !autoRefresh.value
  if (autoRefresh.value) {
    refresh()
    refreshInterval.value = window.setInterval(refresh, 5000)
  } else if (refreshInterval.value) {
    clearInterval(refreshInterval.value)
    refreshInterval.value = null
  }
}

// ── Lifecycle ───────────────────────────────────────────────────────
onMounted(() => {
  if (isConnectedToOSH.value) refresh()
})

onUnmounted(() => {
  if (refreshInterval.value) clearInterval(refreshInterval.value)
})

// ── Helpers ─────────────────────────────────────────────────────────
function dsTypeLabel(type: string): string {
  return DS_TYPE_MAP[type] || type
}

function formatTime(t: string | null): string {
  if (!t) return '—'
  try { return new Date(t).toLocaleTimeString() } catch { return t }
}

function formatUptime(seconds: number): string {
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  return `${h}h ${m}m`
}

function activityColor(level: number): string {
  if (level >= 0.7) return '#ef4444'
  if (level >= 0.4) return '#f59e0b'
  return '#22c55e'
}
</script>

<template>
  <div class="demo-page">
    <!-- Scenario Brief -->
    <div class="scenario-brief">
      <h3>Demo Scenario</h3>
      <p>You are a defence intelligence analyst assigned to create and submit sensor reports (SENREPs) whenever actionable activity has been detected by the sensors you are assigned to monitor. Your operational workflow looks like this:</p>
    </div>

    <!-- Header -->
    <div class="demo-header">
      <div class="demo-title">
        <h2><i class="pi pi-desktop"></i> ODAS C-UAS Acoustic Demo Monitor</h2>
        <p class="subtitle">Real-time monitoring of the Ft. Huachuca acoustic sensor array simulation</p>
      </div>
      <div class="demo-controls">
        <button class="btn btn-primary" @click="refresh" :disabled="loading || !isConnectedToOSH">
          <i class="pi" :class="loading ? 'pi-spin pi-spinner' : 'pi-refresh'"></i>
          {{ loading ? 'Refreshing…' : 'Refresh' }}
        </button>
        <button
          class="btn"
          :class="autoRefresh ? 'btn-danger' : 'btn-success'"
          @click="toggleAutoRefresh"
          :disabled="!isConnectedToOSH"
        >
          <i class="pi" :class="autoRefresh ? 'pi-pause' : 'pi-play'"></i>
          {{ autoRefresh ? 'Stop Auto' : 'Auto (5s)' }}
        </button>
        <span v-if="lastRefresh" class="last-refresh">Last: {{ lastRefresh }}</span>
      </div>
    </div>

    <!-- Not connected warning -->
    <div v-if="!isConnectedToOSH" class="alert alert-warn">
      <i class="pi pi-exclamation-triangle"></i>
      Connect to the <strong>OSH</strong> server first (os4csapi-osh.duckdns.org).
      Go to <router-link to="/">Connect</router-link> and select the OSH endpoint.
    </div>

    <!-- Error -->
    <div v-if="error" class="alert alert-error">
      <i class="pi pi-times-circle"></i> {{ error }}
    </div>

    <!-- Summary Cards -->
    <div v-if="isConnectedToOSH && !error" class="summary-grid">
      <div class="summary-card">
        <div class="card-icon"><i class="pi pi-server"></i></div>
        <div class="card-body">
          <div class="card-value">{{ sensors.length }}</div>
          <div class="card-label">Sensor Arrays</div>
        </div>
      </div>
      <div class="summary-card">
        <div class="card-icon"><i class="pi pi-eye"></i></div>
        <div class="card-body">
          <div class="card-value">{{ totalObsCount.toLocaleString() }}</div>
          <div class="card-label">Total Observations</div>
        </div>
      </div>
      <div class="summary-card">
        <div class="card-icon" :style="{ color: sceneSummary ? activityColor(sceneSummary.activityLevel) : '#94a3b8' }">
          <i class="pi pi-chart-bar"></i>
        </div>
        <div class="card-body">
          <div class="card-value">{{ sceneSummary?.trackCount ?? '—' }}</div>
          <div class="card-label">Active Tracks</div>
        </div>
      </div>
      <div class="summary-card">
        <div class="card-icon" :style="{ color: sceneSummary ? activityColor(sceneSummary.activityLevel) : '#94a3b8' }">
          <i class="pi pi-bolt"></i>
        </div>
        <div class="card-body">
          <div class="card-value">{{ sceneSummary ? (sceneSummary.activityLevel * 100).toFixed(0) + '%' : '—' }}</div>
          <div class="card-label">Activity Level</div>
        </div>
      </div>
      <div class="summary-card senrep-card">
        <div class="card-icon" style="color: #ef4444;"><i class="pi pi-flag"></i></div>
        <div class="card-body">
          <div class="card-value">{{ senrepCount }}</div>
          <div class="card-label">SENREP Reports</div>
        </div>
      </div>
    </div>

    <!-- Sensor Array Cards -->
    <div v-if="sensors.length" class="sensor-section">
      <h3>Sensor Arrays</h3>
      <div class="sensor-grid">
        <div v-for="sensor in sensors" :key="sensor.id" class="sensor-card">
          <div class="sensor-header">
            <h4>{{ sensor.id }}</h4>
            <span class="sensor-coords">{{ sensor.lat.toFixed(4) }}°N, {{ Math.abs(sensor.lon).toFixed(4) }}°W</span>
          </div>

          <!-- Health bar -->
          <div v-if="sensor.health" class="health-bar">
            <div class="health-item">
              <span class="health-label">CPU</span>
              <div class="health-meter">
                <div class="health-fill" :style="{ width: sensor.health.cpuLoad + '%', background: sensor.health.cpuLoad > 80 ? '#ef4444' : '#22c55e' }"></div>
              </div>
              <span class="health-val">{{ sensor.health.cpuLoad.toFixed(0) }}%</span>
            </div>
            <div class="health-item">
              <span class="health-label">Mem</span>
              <span class="health-val">{{ sensor.health.memUsedMB.toFixed(0) }} MB</span>
            </div>
            <div class="health-item">
              <span class="health-label">Temp</span>
              <span class="health-val" :style="{ color: sensor.health.tempC > 70 ? '#ef4444' : 'inherit' }">{{ sensor.health.tempC.toFixed(1) }}°C</span>
            </div>
            <div class="health-item">
              <span class="health-label">Uptime</span>
              <span class="health-val">{{ formatUptime(sensor.health.uptimeS) }}</span>
            </div>
          </div>

          <!-- Resource counts -->
          <div class="resource-counts">
            <span class="count-badge" title="Subsystems"><i class="pi pi-sitemap"></i> {{ sensor.subsystemCount ?? '…' }}</span>
            <span class="count-badge" title="Datastreams"><i class="pi pi-chart-line"></i> {{ sensor.datastreamCount ?? '…' }}</span>
            <span class="count-badge" title="Control Streams"><i class="pi pi-sliders-h"></i> {{ sensor.controlStreamCount ?? '…' }}</span>
          </div>

          <!-- Datastream table -->
          <table class="ds-table" v-if="sensor.datastreams.length">
            <thead>
              <tr>
                <th>Datastream</th>
                <th>Obs</th>
                <th>Latest</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="ds in sensor.datastreams" :key="ds.id">
                <td><span class="ds-type-badge">{{ dsTypeLabel(ds.dsType) }}</span></td>
                <td class="num">{{ ds.obsCount?.toLocaleString() ?? '…' }}</td>
                <td class="time">{{ formatTime(ds.latestTime) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- Network Fused Section -->
    <div v-if="networkDatastreams.length" class="sensor-section">
      <h3><i class="pi pi-globe"></i> Network Fused (AZ-MA-NET)</h3>
      <table class="ds-table ds-table-wide">
        <thead>
          <tr>
            <th>Datastream</th>
            <th>Type</th>
            <th>Obs</th>
            <th>Latest</th>
            <th>Preview</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="ds in networkDatastreams" :key="ds.id">
            <td>{{ ds.name }}</td>
            <td><span class="ds-type-badge">{{ dsTypeLabel(ds.dsType) }}</span></td>
            <td class="num">{{ ds.obsCount?.toLocaleString() ?? '…' }}</td>
            <td class="time">{{ formatTime(ds.latestTime) }}</td>
            <td class="preview">
              <template v-if="ds.latestObs?.result">
                <code>{{ JSON.stringify(ds.latestObs.result).substring(0, 80) }}{{ JSON.stringify(ds.latestObs.result).length > 80 ? '…' : '' }}</code>
              </template>
              <template v-else>—</template>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- String Processor Section (v2.5) -->
    <div v-if="stringProcDatastreams.length" class="sensor-section">
      <h3><i class="pi pi-cog"></i> String Processor (AZ-STRPROC-ALPHA)</h3>
      <p class="section-desc">Derived track state and predicted positions from LOB triangulation chain</p>
      <table class="ds-table ds-table-wide">
        <thead>
          <tr>
            <th>Datastream</th>
            <th>Type</th>
            <th>Obs</th>
            <th>Latest</th>
            <th>Preview</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="ds in stringProcDatastreams" :key="ds.id">
            <td>{{ ds.name }}</td>
            <td><span class="ds-type-badge">{{ dsTypeLabel(ds.dsType) }}</span></td>
            <td class="num">{{ ds.obsCount?.toLocaleString() ?? '…' }}</td>
            <td class="time">{{ formatTime(ds.latestTime) }}</td>
            <td class="preview">
              <template v-if="ds.latestObs?.result">
                <code>{{ JSON.stringify(ds.latestObs.result).substring(0, 80) }}{{ JSON.stringify(ds.latestObs.result).length > 80 ? '…' : '' }}</code>
              </template>
              <template v-else>—</template>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Monitoring Team Section (v2.5) -->
    <div v-if="monitoringDatastreams.length" class="sensor-section">
      <h3><i class="pi pi-users"></i> Monitoring Team (AZ-MON-TEAM-A)</h3>
      <p class="section-desc">Doctrine-aligned SENREP sensor reports from human monitoring operators</p>
      <table class="ds-table ds-table-wide">
        <thead>
          <tr>
            <th>Datastream</th>
            <th>Type</th>
            <th>Obs</th>
            <th>Latest</th>
            <th>Preview</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="ds in monitoringDatastreams" :key="ds.id">
            <td>{{ ds.name }}</td>
            <td><span class="ds-type-badge">{{ dsTypeLabel(ds.dsType) }}</span></td>
            <td class="num">{{ ds.obsCount?.toLocaleString() ?? '…' }}</td>
            <td class="time">{{ formatTime(ds.latestTime) }}</td>
            <td class="preview">
              <template v-if="ds.latestObs?.result">
                <code>{{ JSON.stringify(ds.latestObs.result).substring(0, 80) }}{{ JSON.stringify(ds.latestObs.result).length > 80 ? '…' : '' }}</code>
              </template>
              <template v-else>—</template>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Active Tracks (from SamplingFeatures) -->
    <div v-if="activeTracks.length" class="sensor-section">
      <h3><i class="pi pi-map-marker" style="color: #facc15;"></i> Active Tracks</h3>
      <p class="section-desc">SamplingFeatures created when operators submit their first SENREP for a contact</p>
      <div class="track-list">
        <div v-for="track in activeTracks" :key="track.id" class="track-row">
          <div class="track-icon">⌖</div>
          <div class="track-body">
            <div class="track-name">{{ track.name }}</div>
            <div class="track-detail">
              {{ track.lat.toFixed(4) }}°N, {{ Math.abs(track.lon).toFixed(4) }}°W
              <span v-if="track.description" class="track-desc">— {{ track.description }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- SENREP Report Timeline -->
    <div v-if="senrepReports.length" class="sensor-section">
      <h3><i class="pi pi-flag" style="color: #ef4444;"></i> SENREP Report Feed</h3>
      <p class="section-desc">Sensor reports submitted by monitoring operators — newest first</p>
      <div class="senrep-timeline">
        <div v-for="report in senrepReports" :key="report.id" class="senrep-row">
          <div class="senrep-row-icon">◆</div>
          <div class="senrep-row-body">
            <div class="senrep-row-header">
              <span class="senrep-contact">{{ report.contactId }}</span>
              <span class="senrep-type-badge" :class="'senrep-type--' + report.reportType.toLowerCase()">{{ report.reportType }}</span>
              <span class="senrep-time">{{ formatTime(report.time) }}</span>
            </div>
            <div class="senrep-row-detail">
              <span><strong>{{ report.classification }}</strong></span>
              <span class="senrep-sep">·</span>
              <span>{{ report.lat.toFixed(4) }}°N, {{ Math.abs(report.lon).toFixed(4) }}°W</span>
              <span class="senrep-sep">·</span>
              <span>Operator: <strong>{{ report.operator }}</strong></span>
              <span class="senrep-sep">·</span>
              <span>{{ report.strNo }}</span>
            </div>
            <div v-if="report.comments" class="senrep-row-comments">{{ report.comments }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Loading skeleton -->
    <div v-if="loading && !sensors.length" class="loading-skeleton">
      <div class="skeleton-card" v-for="i in 3" :key="i"></div>
    </div>
  </div>
</template>

<style scoped>
.demo-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 1.5rem;
}

.scenario-brief {
  background: var(--surface-card, #1e293b);
  border: 1px solid var(--surface-border, #334155);
  border-radius: 8px;
  padding: 1.25rem 1.5rem;
  margin-bottom: 1.5rem;
}

.scenario-brief h3 {
  margin: 0 0 0.5rem 0;
  font-size: 1.1rem;
  color: var(--primary-color, #60a5fa);
}

.scenario-brief p {
  margin: 0;
  line-height: 1.6;
  color: var(--text-color, #e2e8f0);
}

.demo-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
  gap: 1rem;
}
.demo-title h2 {
  margin: 0;
  font-size: 1.4rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.subtitle {
  color: #64748b;
  margin: 0.25rem 0 0;
  font-size: 0.9rem;
}
.demo-controls {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.last-refresh {
  font-size: 0.8rem;
  color: #94a3b8;
}

.btn {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.85rem;
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  transition: opacity 0.15s;
}
.btn:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-primary { background: #3b82f6; color: #fff; }
.btn-primary:hover:not(:disabled) { background: #2563eb; }
.btn-success { background: #22c55e; color: #fff; }
.btn-success:hover:not(:disabled) { background: #16a34a; }
.btn-danger { background: #ef4444; color: #fff; }
.btn-danger:hover:not(:disabled) { background: #dc2626; }

.alert {
  padding: 0.75rem 1rem;
  border-radius: 8px;
  margin-bottom: 1.5rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.alert a { color: inherit; font-weight: 600; }
.alert-warn { background: #fef3c7; color: #92400e; border: 1px solid #fbbf24; }
.alert-error { background: #fee2e2; color: #991b1b; border: 1px solid #fca5a5; }

.summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}
.summary-card {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 1rem 1.25rem;
  display: flex;
  align-items: center;
  gap: 1rem;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.card-icon { font-size: 1.6rem; color: #3b82f6; }
.card-value { font-size: 1.6rem; font-weight: 700; line-height: 1; }
.card-label { font-size: 0.8rem; color: #64748b; margin-top: 0.15rem; }

.sensor-section { margin-bottom: 2rem; }
.sensor-section h3 {
  margin: 0 0 1rem;
  font-size: 1.1rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.section-desc {
  color: #64748b;
  font-size: 0.85rem;
  margin: -0.5rem 0 1rem;
}
.sensor-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(340px, 1fr));
  gap: 1rem;
}

.sensor-card {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 1rem 1.25rem;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.sensor-header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 0.75rem;
}
.sensor-header h4 { margin: 0; font-size: 1rem; }
.sensor-coords { font-size: 0.75rem; color: #94a3b8; font-family: monospace; }

.health-bar {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
  padding: 0.5rem 0;
  border-top: 1px solid #f1f5f9;
  border-bottom: 1px solid #f1f5f9;
  margin-bottom: 0.75rem;
}
.health-item { display: flex; align-items: center; gap: 0.35rem; font-size: 0.75rem; }
.health-label { color: #64748b; font-weight: 500; min-width: 2.5rem; }
.health-meter { width: 50px; height: 6px; background: #e2e8f0; border-radius: 3px; overflow: hidden; }
.health-fill { height: 100%; border-radius: 3px; transition: width 0.3s ease; }
.health-val { font-family: monospace; font-weight: 600; font-size: 0.75rem; }

.resource-counts { display: flex; gap: 0.75rem; margin-bottom: 0.75rem; }
.count-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  font-size: 0.8rem;
  padding: 0.2rem 0.5rem;
  background: #f1f5f9;
  border-radius: 4px;
  color: #475569;
}

.ds-table { width: 100%; border-collapse: collapse; font-size: 0.8rem; }
.ds-table th {
  text-align: left;
  font-weight: 600;
  color: #64748b;
  padding: 0.35rem 0.5rem;
  border-bottom: 1px solid #e2e8f0;
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}
.ds-table td { padding: 0.35rem 0.5rem; border-bottom: 1px solid #f1f5f9; }
.ds-table .num { text-align: right; font-family: monospace; font-weight: 600; }
.ds-table .time { color: #64748b; font-family: monospace; font-size: 0.75rem; }
.ds-table .preview code { font-size: 0.7rem; color: #64748b; word-break: break-all; }
.ds-table-wide {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  overflow: hidden;
}
.ds-table-wide th, .ds-table-wide td { padding: 0.5rem 0.75rem; }
.ds-type-badge { display: inline-block; font-size: 0.75rem; white-space: nowrap; }

.loading-skeleton {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(340px, 1fr));
  gap: 1rem;
}
.skeleton-card {
  height: 250px;
  background: linear-gradient(90deg, #f1f5f9 25%, #e2e8f0 50%, #f1f5f9 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  border-radius: 10px;
}
@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

/* SENREP card highlight */
.senrep-card { border-left: 3px solid #ef4444; }

/* Active Tracks list */
.track-list {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  overflow: hidden;
}
.track-row {
  display: flex;
  gap: 0.75rem;
  padding: 0.6rem 1rem;
  border-bottom: 1px solid #f1f5f9;
  align-items: center;
}
.track-row:last-child { border-bottom: none; }
.track-row:hover { background: #f8fafc; }
.track-icon {
  color: #facc15;
  font-size: 1.1rem;
  font-weight: 700;
  flex-shrink: 0;
}
.track-body { flex: 1; min-width: 0; }
.track-name { font-weight: 700; font-size: 0.9rem; color: #1e293b; }
.track-detail { font-size: 0.8rem; color: #475569; margin-top: 0.1rem; }
.track-desc { color: #64748b; font-style: italic; }

/* SENREP Timeline */
.senrep-timeline {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  overflow: hidden;
}
.senrep-row {
  display: flex;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  border-bottom: 1px solid #f1f5f9;
  align-items: flex-start;
}
.senrep-row:last-child { border-bottom: none; }
.senrep-row:hover { background: #f8fafc; }
.senrep-row-icon {
  color: #ef4444;
  font-size: 1rem;
  line-height: 1.4;
  flex-shrink: 0;
}
.senrep-row-body { flex: 1; min-width: 0; }
.senrep-row-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}
.senrep-contact {
  font-weight: 700;
  font-size: 0.9rem;
  color: #1e293b;
}
.senrep-type-badge {
  font-size: 0.7rem;
  font-weight: 600;
  padding: 0.1rem 0.45rem;
  border-radius: 4px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
.senrep-type--init { background: #dbeafe; color: #1e40af; }
.senrep-type--update { background: #fef3c7; color: #92400e; }
.senrep-type--final { background: #fee2e2; color: #991b1b; }
.senrep-time {
  font-size: 0.75rem;
  color: #94a3b8;
  font-family: monospace;
  margin-left: auto;
}
.senrep-row-detail {
  font-size: 0.8rem;
  color: #475569;
  margin-top: 0.2rem;
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem;
  align-items: center;
}
.senrep-sep { color: #cbd5e1; }
.senrep-row-comments {
  font-size: 0.75rem;
  color: #64748b;
  margin-top: 0.25rem;
  font-style: italic;
}
</style>
