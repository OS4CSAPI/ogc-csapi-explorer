<script setup lang="ts">
/**
 * LiveAnalyticsPage — Dedicated UAS / ODAS Scenario Analytics
 *
 * A standalone live analytics page inspired by Narasimha Sharma's CSAPI LiveML
 * Pipeline notebook. Auto-connects to the OS4CSAPI demo server and polls
 * observations in real-time to render:
 *
 *   Tab 1 — Live Leaflet map (sensor nodes, UAS track, LOB lines, SENREPs)
 *   Tab 2 — Live Chart.js dashboards (6-panel intelligence dashboard)
 *   Tab 3 — Live ML analysis (anomaly detection + trajectory prediction)
 *
 * This page does NOT depend on the global connection state — it manages its
 * own HTTP transport to the proxy endpoint, allowing it to work independently
 * from the main Map/Explorer pages.
 */
import { ref, reactive, onMounted, onUnmounted, nextTick, watch, computed } from 'vue'
import Button from 'primevue/button'
import Message from 'primevue/message'
import L from 'leaflet'
import { Chart, registerables } from 'chart.js'

Chart.register(...registerables)

// ════════════════════════════════════════════════════════════════════════════
//  Constants
// ════════════════════════════════════════════════════════════════════════════

const PROXY_BASE = '/api/osh'
const AUTH_HEADER = 'Basic ' + btoa('os4csapi:ogc134mm')
const POLL_INTERVAL_MS = 10_000

// Datastream IDs
const LOB_DS_IDS  = ['04c0', '04cg', '04d0']  // MA-1, MA-2, MA-3
const LOB_LABELS  = ['AZ-MA-1', 'AZ-MA-2', 'AZ-MA-3']
const LOB_COLORS  = ['#f97316', '#facc15', '#a78bfa'] // orange, yellow, purple
const SENREP_DS   = '044g'

// Sensor positions (authoritative deployment coordinates)
const SENSORS = [
  { label: 'AZ-MA-1', lat: 31.6490196, lon: -110.2758537, color: '#3b82f6' },
  { label: 'AZ-MA-2', lat: 31.6569236, lon: -110.2659979, color: '#3b82f6' },
  { label: 'AZ-MA-3', lat: 31.6637961, lon: -110.2515496, color: '#3b82f6' },
]

const MAP_CENTER: [number, number] = [31.656, -110.262]
const MAP_ZOOM = 13

// ════════════════════════════════════════════════════════════════════════════
//  Reactive state
// ════════════════════════════════════════════════════════════════════════════

const activeTab = ref<'map' | 'dashboard' | 'ml'>('map')
const status = ref<'connecting' | 'live' | 'error'>('connecting')
const statusMsg = ref('Connecting to demo server…')
const lastRefresh = ref('')
const pollCount = ref(0)

// Observation stores
interface UasFix {
  time: Date
  lat: number
  lon: number
  cep50: number
  numLobs: number
  sensors: string
  trackId: string
}

interface LobObs {
  time: Date
  dsIndex: number // 0,1,2 = MA-1,MA-2,MA-3
  bearing: number
  stdDev: number
  sensorLat: number
  sensorLon: number
}

interface Senrep {
  time: Date
  title: string
  lat: number
  lon: number
  tgtTyp: string
}

const uasFixes = reactive<UasFix[]>([])
const lobObs = reactive<LobObs[]>([])
const senreps = reactive<Senrep[]>([])

// ML results
interface AnomalyResult {
  index: number
  fix: UasFix
  speed: number
  turnRate: number
  score: number
  isAnomaly: boolean
}

interface PredictedPoint { lat: number; lon: number }

const anomalyResults = reactive<AnomalyResult[]>([])
const predictedTrajectory = reactive<PredictedPoint[]>([])

// Leaflet refs
const mapContainer = ref<HTMLDivElement | null>(null)
let leafletMap: L.Map | null = null
let tileLayer: L.TileLayer | null = null
const darkMap = ref(true)
let uasTrackLine: L.Polyline | null = null
let uasMarker: L.CircleMarker | null = null
let cepCircle: L.Circle | null = null
let lobLayerGroup: L.LayerGroup | null = null
let senrepLayerGroup: L.LayerGroup | null = null
let predictionLine: L.Polyline | null = null
let anomalyLayerGroup: L.LayerGroup | null = null

// Chart refs
const chartBearing = ref<HTMLCanvasElement | null>(null)
const chartTrack = ref<HTMLCanvasElement | null>(null)
const chartLat = ref<HTMLCanvasElement | null>(null)
const chartLon = ref<HTMLCanvasElement | null>(null)
const chartSensors = ref<HTMLCanvasElement | null>(null)
const chartStdDev = ref<HTMLCanvasElement | null>(null)

// ML chart refs
const chartMlTrack = ref<HTMLCanvasElement | null>(null)
const chartSpeed = ref<HTMLCanvasElement | null>(null)
const chartTurnRate = ref<HTMLCanvasElement | null>(null)
const chartAnomalyScore = ref<HTMLCanvasElement | null>(null)

let chartInstances: Chart[] = []

// Timer
let pollTimer: ReturnType<typeof setInterval> | null = null

// Localized datastream discovery
let localizerDsId = ''

// ════════════════════════════════════════════════════════════════════════════
//  HTTP helper
// ════════════════════════════════════════════════════════════════════════════

async function apiFetch(path: string): Promise<any> {
  const res = await fetch(PROXY_BASE + path, {
    headers: {
      'Authorization': AUTH_HEADER,
      'Accept': 'application/om+json',
    },
  })
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
  return res.json()
}

async function apiFetchJson(path: string): Promise<any> {
  const res = await fetch(PROXY_BASE + path, {
    headers: {
      'Authorization': AUTH_HEADER,
      'Accept': 'application/json',
    },
  })
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
  return res.json()
}

// ════════════════════════════════════════════════════════════════════════════
//  Data fetching
// ════════════════════════════════════════════════════════════════════════════

async function discoverLocalizerDs(): Promise<void> {
  const data = await apiFetchJson('/datastreams?limit=200')
  const dsList = data.items || data.features || []
  const loc = dsList.find((ds: any) => {
    const nm = (ds.outputName || ds.name || '').toLowerCase()
    return nm.includes('location_estimate')
  })
  if (loc) localizerDsId = loc.id
}

async function fetchUasFixes(): Promise<void> {
  if (!localizerDsId) return

  // Fetch larger window for track history
  const data = await apiFetch(`/datastreams/${localizerDsId}/observations?limit=200`)
  const items = (data.items || []).filter((o: any) =>
    o?.result && typeof o.result.estimatedLat === 'number' && typeof o.result.estimatedLon === 'number'
  )

  // Deduplicate by time
  const existingTimes = new Set(uasFixes.map(f => f.time.getTime()))
  for (const obs of items) {
    const t = new Date(obs.resultTime || obs.phenomenonTime)
    if (existingTimes.has(t.getTime())) continue
    const r = obs.result
    uasFixes.push({
      time: t,
      lat: r.estimatedLat,
      lon: r.estimatedLon,
      cep50: r.cep50_m || 0,
      numLobs: r.numContributingLobs || 0,
      sensors: r.contributingSensors || '',
      trackId: r.trackId || '',
    })
  }

  // Sort by time
  uasFixes.sort((a, b) => a.time.getTime() - b.time.getTime())
}

async function fetchLobs(): Promise<void> {
  for (let i = 0; i < LOB_DS_IDS.length; i++) {
    try {
      const data = await apiFetch(`/datastreams/${LOB_DS_IDS[i]}/observations?limit=200`)
      const items = (data.items || []).filter((o: any) =>
        o?.result && typeof o.result.bearingTrue === 'number'
      )

      const existingKeys = new Set(lobObs
        .filter(l => l.dsIndex === i)
        .map(l => l.time.getTime())
      )

      for (const obs of items) {
        const t = new Date(obs.resultTime || obs.phenomenonTime)
        if (existingKeys.has(t.getTime())) continue
        const r = obs.result
        lobObs.push({
          time: t,
          dsIndex: i,
          bearing: r.bearingTrue,
          stdDev: r.bearingStdDev || 0,
          sensorLat: r.sensorLat ?? SENSORS[i].lat,
          sensorLon: r.sensorLon ?? SENSORS[i].lon,
        })
      }
    } catch { /* skip individual sensor failures */ }
  }

  lobObs.sort((a, b) => a.time.getTime() - b.time.getTime())
}

async function fetchSenreps(): Promise<void> {
  try {
    const data = await apiFetch(`/datastreams/${SENREP_DS}/observations?limit=50`)
    const items = (data.items || []).filter((o: any) =>
      o?.result && typeof o.result.etaLat === 'number' && typeof o.result.etaLon === 'number' && o.result.title
    )

    const existingTitles = new Set(senreps.map(s => s.title))
    for (const obs of items) {
      const r = obs.result
      if (existingTitles.has(r.title)) continue
      senreps.push({
        time: new Date(obs.resultTime || obs.phenomenonTime),
        title: r.title,
        lat: r.etaLat,
        lon: r.etaLon,
        tgtTyp: r.tgtTyp || 'UNK',
      })
    }
  } catch { /* skip */ }
}

// ════════════════════════════════════════════════════════════════════════════
//  ML — Anomaly Detection + Trajectory Prediction
// ════════════════════════════════════════════════════════════════════════════

function computeML(): void {
  anomalyResults.length = 0
  predictedTrajectory.length = 0

  if (uasFixes.length < 3) return

  // Feature engineering: speed, heading, turn rate per fix
  const features: { speed: number; heading: number; turnRate: number; sensorCount: number }[] = []

  for (let i = 0; i < uasFixes.length; i++) {
    if (i === 0) {
      features.push({ speed: 0, heading: 0, turnRate: 0, sensorCount: uasFixes[i].numLobs })
      continue
    }
    const prev = uasFixes[i - 1]
    const curr = uasFixes[i]
    const dt = (curr.time.getTime() - prev.time.getTime()) / 1000 // seconds
    if (dt <= 0) {
      features.push({ speed: 0, heading: 0, turnRate: 0, sensorCount: curr.numLobs })
      continue
    }

    // Haversine distance
    const dLat = (curr.lat - prev.lat) * Math.PI / 180
    const dLon = (curr.lon - prev.lon) * Math.PI / 180
    const a = Math.sin(dLat / 2) ** 2 +
              Math.cos(prev.lat * Math.PI / 180) * Math.cos(curr.lat * Math.PI / 180) *
              Math.sin(dLon / 2) ** 2
    const dist = 6371000 * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))
    const speed = dist / dt // m/s

    // Heading
    const y = Math.sin(dLon) * Math.cos(curr.lat * Math.PI / 180)
    const x = Math.cos(prev.lat * Math.PI / 180) * Math.sin(curr.lat * Math.PI / 180) -
              Math.sin(prev.lat * Math.PI / 180) * Math.cos(curr.lat * Math.PI / 180) * Math.cos(dLon)
    const heading = (Math.atan2(y, x) * 180 / Math.PI + 360) % 360

    const prevHeading = i >= 2 ? features[i - 1].heading : heading
    let dh = heading - prevHeading
    if (dh > 180) dh -= 360
    if (dh < -180) dh += 360
    const turnRate = Math.abs(dh / dt)

    features.push({ speed, heading, turnRate, sensorCount: curr.numLobs })
  }

  // Z-score anomaly detection (simpler + more transparent than Isolation Forest)
  const speeds = features.map(f => f.speed)
  const turns = features.map(f => f.turnRate)
  const sensorCounts = features.map(f => f.sensorCount)

  function zScores(arr: number[]): number[] {
    const mean = arr.reduce((s, v) => s + v, 0) / arr.length
    const std = Math.sqrt(arr.reduce((s, v) => s + (v - mean) ** 2, 0) / arr.length) || 1
    return arr.map(v => Math.abs((v - mean) / std))
  }

  const zSpeed = zScores(speeds)
  const zTurn = zScores(turns)
  const zSensor = zScores(sensorCounts)

  for (let i = 0; i < uasFixes.length; i++) {
    // Composite anomaly score (max of z-scores across features)
    const score = Math.max(zSpeed[i], zTurn[i], zSensor[i])
    anomalyResults.push({
      index: i,
      fix: uasFixes[i],
      speed: features[i].speed,
      turnRate: features[i].turnRate,
      score,
      isAnomaly: score > 2.0, // threshold: 2 standard deviations
    })
  }

  // Trajectory prediction: linear extrapolation from last 5 fixes
  const lastN = uasFixes.slice(-Math.min(5, uasFixes.length))
  if (lastN.length >= 2) {
    // Fit linear regression on lat and lon vs time
    const t0 = lastN[0].time.getTime()
    const xs = lastN.map(f => (f.time.getTime() - t0) / 1000)
    const lats = lastN.map(f => f.lat)
    const lons = lastN.map(f => f.lon)

    function linReg(x: number[], y: number[]): { slope: number; intercept: number } {
      const n = x.length
      const sx = x.reduce((a, b) => a + b, 0)
      const sy = y.reduce((a, b) => a + b, 0)
      const sxx = x.reduce((a, b) => a + b * b, 0)
      const sxy = x.reduce((a, b, i) => a + b * y[i], 0)
      const slope = (n * sxy - sx * sy) / (n * sxx - sx * sx || 1)
      const intercept = (sy - slope * sx) / n
      return { slope, intercept }
    }

    const latReg = linReg(xs, lats)
    const lonReg = linReg(xs, lons)

    // Predict 5 future points, each 10 seconds ahead
    const lastT = xs[xs.length - 1]
    for (let step = 1; step <= 5; step++) {
      const futureT = lastT + step * 10
      predictedTrajectory.push({
        lat: latReg.intercept + latReg.slope * futureT,
        lon: lonReg.intercept + lonReg.slope * futureT,
      })
    }
  }
}

// ════════════════════════════════════════════════════════════════════════════
//  Leaflet map
// ════════════════════════════════════════════════════════════════════════════

const TILE_DARK = 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png'
const TILE_LIGHT = 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png'
const ATTR_DARK = '&copy; <a href="https://carto.com/">CARTO</a>'
const ATTR_LIGHT = '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'

function initMap(): void {
  if (!mapContainer.value || leafletMap) return

  leafletMap = L.map(mapContainer.value, {
    center: MAP_CENTER,
    zoom: MAP_ZOOM,
    zoomControl: true,
  })

  tileLayer = L.tileLayer(TILE_DARK, {
    attribution: ATTR_DARK,
    maxZoom: 19,
  }).addTo(leafletMap)

  // Sensor nodes
  for (const s of SENSORS) {
    L.circleMarker([s.lat, s.lon], {
      radius: 8,
      fillColor: s.color,
      color: '#fff',
      weight: 2,
      fillOpacity: 0.9,
    })
      .bindTooltip(s.label, { permanent: true, direction: 'top', offset: [0, -10], className: 'sensor-tooltip' })
      .addTo(leafletMap)
  }

  // Layer groups
  lobLayerGroup = L.layerGroup().addTo(leafletMap)
  senrepLayerGroup = L.layerGroup().addTo(leafletMap)
  anomalyLayerGroup = L.layerGroup().addTo(leafletMap)

  // UAS track polyline
  uasTrackLine = L.polyline([], { color: '#ef4444', weight: 2, opacity: 0.8 }).addTo(leafletMap)
  predictionLine = L.polyline([], { color: '#a855f7', weight: 2, dashArray: '8 6', opacity: 0.7 }).addTo(leafletMap)
}

function toggleMapStyle(): void {
  if (!leafletMap || !tileLayer) return
  darkMap.value = !darkMap.value
  leafletMap.removeLayer(tileLayer)
  tileLayer = L.tileLayer(
    darkMap.value ? TILE_DARK : TILE_LIGHT,
    { attribution: darkMap.value ? ATTR_DARK : ATTR_LIGHT, maxZoom: 19 },
  ).addTo(leafletMap)
}

function updateMap(): void {
  if (!leafletMap) return

  // UAS track
  if (uasTrackLine && uasFixes.length) {
    const coords: [number, number][] = uasFixes.map(f => [f.lat, f.lon])
    uasTrackLine.setLatLngs(coords)

    // Latest fix marker
    const latest = uasFixes[uasFixes.length - 1]
    if (uasMarker) leafletMap.removeLayer(uasMarker)
    uasMarker = L.circleMarker([latest.lat, latest.lon], {
      radius: 7,
      fillColor: '#ef4444',
      color: '#fff',
      weight: 2,
      fillOpacity: 1,
    })
      .bindTooltip(`UAS: ${latest.lat.toFixed(4)}, ${latest.lon.toFixed(4)}<br>CEP50: ${latest.cep50.toFixed(0)}m`, { direction: 'top' })
      .addTo(leafletMap)

    // CEP50 circle
    if (cepCircle) leafletMap.removeLayer(cepCircle)
    if (latest.cep50 > 0) {
      cepCircle = L.circle([latest.lat, latest.lon], {
        radius: latest.cep50,
        color: '#ef4444',
        fillColor: '#ef4444',
        fillOpacity: 0.08,
        weight: 1,
        dashArray: '4 4',
      }).addTo(leafletMap)
    }
  }

  // LOB lines
  if (lobLayerGroup) {
    lobLayerGroup.clearLayers()
    // Show latest LOB per sensor
    for (let i = 0; i < LOB_DS_IDS.length; i++) {
      const sensorLobs = lobObs.filter(l => l.dsIndex === i)
      if (!sensorLobs.length) continue
      const latest = sensorLobs[sensorLobs.length - 1]
      const range = 5000 // 5km visual range
      const bearingRad = latest.bearing * Math.PI / 180
      const endLat = latest.sensorLat + (range / 111320) * Math.cos(bearingRad)
      const endLon = latest.sensorLon + (range / (111320 * Math.cos(latest.sensorLat * Math.PI / 180))) * Math.sin(bearingRad)

      L.polyline(
        [[latest.sensorLat, latest.sensorLon], [endLat, endLon]],
        { color: LOB_COLORS[i], weight: 2, opacity: 0.7, dashArray: '6 4' },
      )
        .bindTooltip(`${LOB_LABELS[i]}: ${latest.bearing.toFixed(1)}°`, { sticky: true })
        .addTo(lobLayerGroup)
    }
  }

  // SENREPs
  if (senrepLayerGroup) {
    senrepLayerGroup.clearLayers()
    for (const s of senreps) {
      L.marker([s.lat, s.lon], {
        icon: L.divIcon({
          className: 'senrep-icon',
          html: '<div style="width:12px;height:12px;background:#dc2626;transform:rotate(45deg);border:1px solid #fff;"></div>',
          iconSize: [12, 12],
          iconAnchor: [6, 6],
        }),
      })
        .bindTooltip(`SENREP: ${s.title}<br>${s.tgtTyp}`, { direction: 'top' })
        .addTo(senrepLayerGroup)
    }
  }

  // Prediction line
  if (predictionLine && predictedTrajectory.length && uasFixes.length) {
    const last = uasFixes[uasFixes.length - 1]
    const coords: [number, number][] = [
      [last.lat, last.lon],
      ...predictedTrajectory.map(p => [p.lat, p.lon] as [number, number]),
    ]
    predictionLine.setLatLngs(coords)
  }

  // Anomaly markers
  if (anomalyLayerGroup) {
    anomalyLayerGroup.clearLayers()
    for (const a of anomalyResults) {
      if (!a.isAnomaly) continue
      L.circleMarker([a.fix.lat, a.fix.lon], {
        radius: 10,
        fillColor: 'transparent',
        color: '#ef4444',
        weight: 3,
        opacity: 0.9,
      })
        .bindTooltip(`Anomaly: score=${a.score.toFixed(2)}<br>speed=${a.speed.toFixed(1)} m/s`, { direction: 'top' })
        .addTo(anomalyLayerGroup)

      // X marker
      const s = 0.00015
      L.polyline([[a.fix.lat - s, a.fix.lon - s], [a.fix.lat + s, a.fix.lon + s]], { color: '#ef4444', weight: 2 }).addTo(anomalyLayerGroup)
      L.polyline([[a.fix.lat + s, a.fix.lon - s], [a.fix.lat - s, a.fix.lon + s]], { color: '#ef4444', weight: 2 }).addTo(anomalyLayerGroup)
    }
  }
}

// ════════════════════════════════════════════════════════════════════════════
//  Chart.js — Dashboard
// ════════════════════════════════════════════════════════════════════════════

const CHART_FONT_COLOR = '#94a3b8'
const CHART_GRID_COLOR = 'rgba(148,163,184,0.15)'

function chartDefaults(): any {
  return {
    responsive: true,
    maintainAspectRatio: false,
    animation: { duration: 300 },
    plugins: { legend: { labels: { color: CHART_FONT_COLOR } } },
    scales: {
      x: { ticks: { color: CHART_FONT_COLOR, maxTicksLimit: 8 }, grid: { color: CHART_GRID_COLOR } },
      y: { ticks: { color: CHART_FONT_COLOR }, grid: { color: CHART_GRID_COLOR } },
    },
  }
}

function timeLabels(arr: { time: Date }[]): string[] {
  return arr.map(f => f.time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }))
}

function destroyCharts(): void {
  chartInstances.forEach(c => c.destroy())
  chartInstances = []
}

function renderDashboard(): void {
  destroyCharts()
  if (!uasFixes.length) return

  const labels = timeLabels(uasFixes)

  // 1. Flight Track (scatter — lat vs lon)
  if (chartTrack.value) {
    chartInstances.push(new Chart(chartTrack.value, {
      type: 'scatter',
      data: {
        datasets: [{
          label: 'UAS Track',
          data: uasFixes.map(f => ({ x: f.lon, y: f.lat })),
          backgroundColor: uasFixes.map((_, i) => {
            const t = i / (uasFixes.length - 1 || 1)
            return `rgba(${Math.round(239 * (1 - t) + 96 * t)}, ${Math.round(68 * (1 - t) + 165 * t)}, ${Math.round(68 * (1 - t) + 250 * t)}, 0.8)`
          }),
          pointRadius: 5,
        }],
      },
      options: {
        ...chartDefaults(),
        plugins: {
          ...chartDefaults().plugins,
          title: { display: true, text: 'UAS Flight Track', color: CHART_FONT_COLOR },
        },
        scales: {
          x: { title: { display: true, text: 'Longitude', color: CHART_FONT_COLOR }, ticks: { color: CHART_FONT_COLOR }, grid: { color: CHART_GRID_COLOR } },
          y: { title: { display: true, text: 'Latitude', color: CHART_FONT_COLOR }, ticks: { color: CHART_FONT_COLOR }, grid: { color: CHART_GRID_COLOR } },
        },
      },
    }))
  }

  // 2. LOB Bearings over time (one series per sensor)
  if (chartBearing.value) {
    const datasets = LOB_DS_IDS.map((_, i) => {
      const sensorLobs = lobObs.filter(l => l.dsIndex === i)
      return {
        label: LOB_LABELS[i],
        data: sensorLobs.map(l => ({ x: l.time.getTime(), y: l.bearing })),
        borderColor: LOB_COLORS[i],
        backgroundColor: LOB_COLORS[i],
        pointRadius: 3,
        showLine: true,
        tension: 0.1,
      }
    })
    chartInstances.push(new Chart(chartBearing.value, {
      type: 'scatter',
      data: { datasets },
      options: {
        ...chartDefaults(),
        plugins: {
          ...chartDefaults().plugins,
          title: { display: true, text: 'LOB Bearings Over Time', color: CHART_FONT_COLOR },
        },
        scales: {
          x: {
            type: 'linear',
            title: { display: true, text: 'Time', color: CHART_FONT_COLOR },
            ticks: {
              color: CHART_FONT_COLOR,
              callback: (v: any) => new Date(v).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
            },
            grid: { color: CHART_GRID_COLOR },
          },
          y: {
            title: { display: true, text: 'Bearing (°)', color: CHART_FONT_COLOR },
            ticks: { color: CHART_FONT_COLOR },
            grid: { color: CHART_GRID_COLOR },
          },
        },
      },
    }))
  }

  // 3. Bearing StdDev over time
  if (chartStdDev.value) {
    const datasets = LOB_DS_IDS.map((_, i) => {
      const sensorLobs = lobObs.filter(l => l.dsIndex === i)
      return {
        label: LOB_LABELS[i],
        data: sensorLobs.map(l => ({ x: l.time.getTime(), y: l.stdDev })),
        borderColor: LOB_COLORS[i],
        backgroundColor: LOB_COLORS[i],
        pointRadius: 3,
        showLine: true,
        tension: 0.1,
      }
    })
    chartInstances.push(new Chart(chartStdDev.value, {
      type: 'scatter',
      data: { datasets },
      options: {
        ...chartDefaults(),
        plugins: {
          ...chartDefaults().plugins,
          title: { display: true, text: 'Bearing Uncertainty (σ)', color: CHART_FONT_COLOR },
        },
        scales: {
          x: {
            type: 'linear',
            title: { display: true, text: 'Time', color: CHART_FONT_COLOR },
            ticks: {
              color: CHART_FONT_COLOR,
              callback: (v: any) => new Date(v).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
            },
            grid: { color: CHART_GRID_COLOR },
          },
          y: {
            title: { display: true, text: 'StdDev (°)', color: CHART_FONT_COLOR },
            ticks: { color: CHART_FONT_COLOR },
            grid: { color: CHART_GRID_COLOR },
          },
        },
      },
    }))
  }

  // 4. Latitude time series
  if (chartLat.value) {
    chartInstances.push(new Chart(chartLat.value, {
      type: 'line',
      data: {
        labels,
        datasets: [{
          label: 'Latitude',
          data: uasFixes.map(f => f.lat),
          borderColor: '#60a5fa',
          backgroundColor: 'rgba(96,165,250,0.1)',
          fill: true,
          tension: 0.2,
          pointRadius: 3,
        }],
      },
      options: {
        ...chartDefaults(),
        plugins: {
          ...chartDefaults().plugins,
          title: { display: true, text: 'Latitude Time Series', color: CHART_FONT_COLOR },
        },
      },
    }))
  }

  // 5. Longitude time series
  if (chartLon.value) {
    chartInstances.push(new Chart(chartLon.value, {
      type: 'line',
      data: {
        labels,
        datasets: [{
          label: 'Longitude',
          data: uasFixes.map(f => f.lon),
          borderColor: '#f97316',
          backgroundColor: 'rgba(249,115,22,0.1)',
          fill: true,
          tension: 0.2,
          pointRadius: 3,
        }],
      },
      options: {
        ...chartDefaults(),
        plugins: {
          ...chartDefaults().plugins,
          title: { display: true, text: 'Longitude Time Series', color: CHART_FONT_COLOR },
        },
      },
    }))
  }

  // 6. Sensor count per fix
  if (chartSensors.value) {
    chartInstances.push(new Chart(chartSensors.value, {
      type: 'bar',
      data: {
        labels,
        datasets: [{
          label: 'Contributing Sensors',
          data: uasFixes.map(f => f.numLobs),
          backgroundColor: 'rgba(34,197,94,0.6)',
          borderColor: '#22c55e',
          borderWidth: 1,
        }],
      },
      options: {
        ...chartDefaults(),
        plugins: {
          ...chartDefaults().plugins,
          title: { display: true, text: 'Contributing Sensors per Fix', color: CHART_FONT_COLOR },
        },
        scales: {
          ...chartDefaults().scales,
          y: { ...chartDefaults().scales.y, beginAtZero: true, max: 4 },
        },
      },
    }))
  }
}

function renderMlCharts(): void {
  // Destroy only ML charts (last 4 in array? No, just maintain separately)
  // Simpler: destroy all and re-render when tab switches
  destroyCharts()
  if (!anomalyResults.length) return

  const labels = anomalyResults.map(a => a.fix.time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }))
  const normal = anomalyResults.filter(a => !a.isAnomaly)
  const anomalies = anomalyResults.filter(a => a.isAnomaly)

  // 1. ML Track with anomalies
  if (chartMlTrack.value) {
    chartInstances.push(new Chart(chartMlTrack.value, {
      type: 'scatter',
      data: {
        datasets: [
          {
            label: 'Normal',
            data: normal.map(a => ({ x: a.fix.lon, y: a.fix.lat })),
            backgroundColor: '#22c55e',
            pointRadius: 5,
          },
          {
            label: 'Anomaly',
            data: anomalies.map(a => ({ x: a.fix.lon, y: a.fix.lat })),
            backgroundColor: '#ef4444',
            pointRadius: 8,
            pointStyle: 'crossRot',
          },
          ...(predictedTrajectory.length ? [{
            label: 'Predicted',
            data: predictedTrajectory.map(p => ({ x: p.lon, y: p.lat })),
            borderColor: '#a855f7',
            backgroundColor: '#a855f7',
            pointRadius: 6,
            pointStyle: 'triangle',
            showLine: true,
            borderDash: [6, 4],
          }] : []),
        ],
      },
      options: {
        ...chartDefaults(),
        plugins: {
          ...chartDefaults().plugins,
          title: { display: true, text: 'Anomaly Detection — Track View', color: CHART_FONT_COLOR },
        },
        scales: {
          x: { title: { display: true, text: 'Longitude', color: CHART_FONT_COLOR }, ticks: { color: CHART_FONT_COLOR }, grid: { color: CHART_GRID_COLOR } },
          y: { title: { display: true, text: 'Latitude', color: CHART_FONT_COLOR }, ticks: { color: CHART_FONT_COLOR }, grid: { color: CHART_GRID_COLOR } },
        },
      },
    }))
  }

  // 2. Speed over time
  if (chartSpeed.value) {
    chartInstances.push(new Chart(chartSpeed.value, {
      type: 'line',
      data: {
        labels,
        datasets: [{
          label: 'Speed (m/s)',
          data: anomalyResults.map(a => a.speed),
          borderColor: '#60a5fa',
          backgroundColor: 'rgba(96,165,250,0.1)',
          fill: true,
          tension: 0.2,
          pointRadius: anomalyResults.map(a => a.isAnomaly ? 8 : 3),
          pointBackgroundColor: anomalyResults.map(a => a.isAnomaly ? '#ef4444' : '#60a5fa'),
          pointStyle: anomalyResults.map(a => a.isAnomaly ? 'crossRot' : 'circle'),
        }],
      },
      options: {
        ...chartDefaults(),
        plugins: {
          ...chartDefaults().plugins,
          title: { display: true, text: 'Speed Over Time', color: CHART_FONT_COLOR },
        },
      },
    }))
  }

  // 3. Turn rate over time
  if (chartTurnRate.value) {
    chartInstances.push(new Chart(chartTurnRate.value, {
      type: 'line',
      data: {
        labels,
        datasets: [{
          label: 'Turn Rate (°/s)',
          data: anomalyResults.map(a => a.turnRate),
          borderColor: '#f97316',
          backgroundColor: 'rgba(249,115,22,0.1)',
          fill: true,
          tension: 0.2,
          pointRadius: anomalyResults.map(a => a.isAnomaly ? 8 : 3),
          pointBackgroundColor: anomalyResults.map(a => a.isAnomaly ? '#ef4444' : '#f97316'),
          pointStyle: anomalyResults.map(a => a.isAnomaly ? 'crossRot' : 'circle'),
        }],
      },
      options: {
        ...chartDefaults(),
        plugins: {
          ...chartDefaults().plugins,
          title: { display: true, text: 'Turn Rate Over Time', color: CHART_FONT_COLOR },
        },
      },
    }))
  }

  // 4. Anomaly score
  if (chartAnomalyScore.value) {
    chartInstances.push(new Chart(chartAnomalyScore.value, {
      type: 'bar',
      data: {
        labels,
        datasets: [{
          label: 'Anomaly Score',
          data: anomalyResults.map(a => a.score),
          backgroundColor: anomalyResults.map(a => a.isAnomaly ? 'rgba(239,68,68,0.7)' : 'rgba(34,197,94,0.5)'),
          borderColor: anomalyResults.map(a => a.isAnomaly ? '#ef4444' : '#22c55e'),
          borderWidth: 1,
        }],
      },
      options: {
        ...chartDefaults(),
        plugins: {
          ...chartDefaults().plugins,
          title: { display: true, text: 'Anomaly Score (threshold = 2σ)', color: CHART_FONT_COLOR },
          annotation: undefined,
        },
        scales: {
          ...chartDefaults().scales,
          y: { ...chartDefaults().scales.y, beginAtZero: true },
        },
      },
    }))
  }
}

// ════════════════════════════════════════════════════════════════════════════
//  Poll cycle
// ════════════════════════════════════════════════════════════════════════════

async function poll(): Promise<void> {
  try {
    await Promise.all([fetchUasFixes(), fetchLobs(), fetchSenreps()])
    computeML()
    updateMap()

    // Only re-render charts if we're on that tab (expensive)
    if (activeTab.value === 'dashboard') renderDashboard()
    if (activeTab.value === 'ml') renderMlCharts()

    pollCount.value++
    lastRefresh.value = new Date().toLocaleTimeString()
    if (status.value !== 'live') {
      status.value = 'live'
      statusMsg.value = 'Live'
    }
  } catch (err: any) {
    status.value = 'error'
    statusMsg.value = `Error: ${err.message || err}`
  }
}

// Re-render charts when switching tabs
watch(activeTab, async (tab) => {
  await nextTick()
  if (tab === 'map') {
    if (!leafletMap) initMap()
    else leafletMap.invalidateSize()
    updateMap()
  } else if (tab === 'dashboard') {
    renderDashboard()
  } else if (tab === 'ml') {
    renderMlCharts()
  }
})

// Stats
const fixCount = computed(() => uasFixes.length)
const lobCount = computed(() => lobObs.length)
const senrepCount = computed(() => senreps.length)
const anomalyCount = computed(() => anomalyResults.filter(a => a.isAnomaly).length)

// ════════════════════════════════════════════════════════════════════════════
//  Lifecycle
// ════════════════════════════════════════════════════════════════════════════

onMounted(async () => {
  try {
    await discoverLocalizerDs()
    await nextTick()
    initMap()
    await poll()
    pollTimer = setInterval(poll, POLL_INTERVAL_MS)
  } catch (err: any) {
    status.value = 'error'
    statusMsg.value = `Failed to connect: ${err.message || err}`
  }
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
  destroyCharts()
  if (leafletMap) {
    leafletMap.remove()
    leafletMap = null
  }
})
</script>

<template>
  <div class="analytics-page">
    <!-- Header -->
    <div class="analytics-header">
      <div class="header-top">
        <div>
          <h2><i class="pi pi-chart-line"></i> UAS / ODAS Live Demo</h2>
          <p class="subtitle">
            Real-time intelligence pipeline — Arizona sensor array
            <span class="attribution">Inspired by <a href="https://github.com/nsnarayanam" target="_blank">Narasimha Sharma</a>'s <a href="https://github.com/orgs/OS4CSAPI/discussions/37" target="_blank">CSAPI LiveML notebook</a></span>
          </p>
        </div>
        <div class="status-bar">
          <span :class="['status-badge', status]">
            <i :class="status === 'live' ? 'pi pi-circle-fill' : status === 'connecting' ? 'pi pi-spin pi-spinner' : 'pi pi-exclamation-triangle'"></i>
            {{ statusMsg }}
          </span>
          <span v-if="lastRefresh" class="refresh-time">Last: {{ lastRefresh }}</span>
        </div>
      </div>

      <!-- Stats bar -->
      <div class="stats-bar">
        <div class="stat"><span class="stat-value">{{ fixCount }}</span><span class="stat-label">UAS Fixes</span></div>
        <div class="stat"><span class="stat-value">{{ lobCount }}</span><span class="stat-label">LOB Obs</span></div>
        <div class="stat"><span class="stat-value">{{ senrepCount }}</span><span class="stat-label">SENREPs</span></div>
        <div class="stat anomaly"><span class="stat-value">{{ anomalyCount }}</span><span class="stat-label">Anomalies</span></div>
        <div class="stat"><span class="stat-value">{{ pollCount }}</span><span class="stat-label">Polls</span></div>
      </div>
    </div>

    <!-- Tab bar -->
    <div class="tab-bar">
      <button :class="['tab-btn', { active: activeTab === 'map' }]" @click="activeTab = 'map'">
        <i class="pi pi-map"></i> Live Map
      </button>
      <button :class="['tab-btn', { active: activeTab === 'dashboard' }]" @click="activeTab = 'dashboard'">
        <i class="pi pi-chart-bar"></i> Dashboard
      </button>
      <button :class="['tab-btn', { active: activeTab === 'ml' }]" @click="activeTab = 'ml'">
        <i class="pi pi-sliders-h"></i> ML Analysis
      </button>
    </div>

    <!-- Tab content -->
    <div class="tab-content">
      <!-- Live Map -->
      <div v-show="activeTab === 'map'" class="tab-panel">
        <div ref="mapContainer" class="leaflet-map-container"></div>
        <div class="map-legend">
          <button class="map-style-toggle" @click="toggleMapStyle" :title="darkMap ? 'Switch to light map' : 'Switch to dark map'">
            <i :class="darkMap ? 'pi pi-sun' : 'pi pi-moon'"></i>
            {{ darkMap ? 'Light' : 'Dark' }}
          </button>
          <span class="legend-sep"></span>
          <span class="legend-item"><span class="legend-dot" style="background:#3b82f6"></span> Sensor Node</span>
          <span class="legend-item"><span class="legend-dot" style="background:#ef4444"></span> UAS Track</span>
          <span class="legend-item"><span class="legend-line" style="border-color:#f97316"></span> LOB Bearing</span>
          <span class="legend-item"><span class="legend-diamond"></span> SENREP</span>
          <span class="legend-item"><span class="legend-line" style="border-color:#a855f7;border-style:dashed"></span> Predicted</span>
          <span class="legend-item"><span class="legend-x"></span> Anomaly</span>
        </div>
      </div>

      <!-- Dashboard -->
      <div v-show="activeTab === 'dashboard'" class="tab-panel">
        <div v-if="!uasFixes.length" class="empty-state">
          <i class="pi pi-spin pi-spinner" style="font-size:2rem"></i>
          <p>Waiting for observation data…</p>
        </div>
        <div v-else class="chart-grid">
          <div class="chart-cell"><canvas ref="chartTrack"></canvas></div>
          <div class="chart-cell"><canvas ref="chartBearing"></canvas></div>
          <div class="chart-cell"><canvas ref="chartStdDev"></canvas></div>
          <div class="chart-cell"><canvas ref="chartLat"></canvas></div>
          <div class="chart-cell"><canvas ref="chartLon"></canvas></div>
          <div class="chart-cell"><canvas ref="chartSensors"></canvas></div>
        </div>
      </div>

      <!-- ML Analysis -->
      <div v-show="activeTab === 'ml'" class="tab-panel">
        <div v-if="anomalyResults.length < 3" class="empty-state">
          <i class="pi pi-spin pi-spinner" style="font-size:2rem"></i>
          <p>Need ≥ 3 UAS fixes for ML analysis…</p>
        </div>
        <div v-else>
          <Message severity="info" :closable="false" class="ml-info">
            Z-score anomaly detection on speed, turn rate, and sensor count. Fixes with a composite score &gt; 2σ are flagged.
            Trajectory prediction uses linear extrapolation from the last 5 fixes.
          </Message>
          <div class="chart-grid">
            <div class="chart-cell"><canvas ref="chartMlTrack"></canvas></div>
            <div class="chart-cell"><canvas ref="chartSpeed"></canvas></div>
            <div class="chart-cell"><canvas ref="chartTurnRate"></canvas></div>
            <div class="chart-cell"><canvas ref="chartAnomalyScore"></canvas></div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Leaflet CSS import */
@import 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css';

.analytics-page {
  max-width: 1400px;
  margin: 0 auto;
  padding: 1rem;
}

.analytics-header {
  margin-bottom: 0.75rem;
}

.header-top {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.analytics-header h2 {
  margin: 0;
  font-size: 1.4rem;
  color: var(--primary-color, #60a5fa);
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.subtitle {
  margin: 0.2rem 0 0 0;
  color: var(--text-color-secondary, #94a3b8);
  font-size: 0.85rem;
}

.attribution {
  opacity: 0.7;
  font-size: 0.8rem;
}

.attribution a {
  color: var(--primary-color, #60a5fa);
  text-decoration: none;
}

.attribution a:hover {
  text-decoration: underline;
}

.status-bar {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  padding: 0.25rem 0.6rem;
  border-radius: 12px;
  font-size: 0.8rem;
  font-weight: 600;
}

.status-badge.live {
  background: rgba(34, 197, 94, 0.15);
  color: #22c55e;
}

.status-badge.connecting {
  background: rgba(96, 165, 250, 0.15);
  color: #60a5fa;
}

.status-badge.error {
  background: rgba(239, 68, 68, 0.15);
  color: #ef4444;
}

.status-badge .pi-circle-fill {
  font-size: 0.5rem;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

.refresh-time {
  color: var(--text-color-secondary, #94a3b8);
  font-size: 0.75rem;
}

/* Stats bar */
.stats-bar {
  display: flex;
  gap: 0.5rem;
  margin-top: 0.5rem;
  flex-wrap: wrap;
}

.stat {
  display: flex;
  align-items: baseline;
  gap: 0.3rem;
  padding: 0.25rem 0.6rem;
  background: var(--surface-card, #1e293b);
  border: 1px solid var(--surface-border, #334155);
  border-radius: 8px;
  font-size: 0.8rem;
}

.stat-value {
  font-weight: 700;
  color: var(--primary-color, #60a5fa);
  font-variant-numeric: tabular-nums;
}

.stat.anomaly .stat-value {
  color: #ef4444;
}

.stat-label {
  color: var(--text-color-secondary, #94a3b8);
}

/* Tabs */
.tab-bar {
  display: flex;
  border: 1px solid var(--surface-border, #334155);
  border-radius: 8px 8px 0 0;
  overflow: hidden;
  background: rgba(0, 0, 0, 0.2);
}

.tab-btn {
  flex: 1;
  padding: 0.65rem 1rem;
  background: none;
  border: none;
  border-bottom: 3px solid transparent;
  color: var(--text-color-secondary, #94a3b8);
  font-size: 0.9rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.4rem;
  transition: all 0.2s;
}

.tab-btn:hover {
  color: var(--text-color, #e2e8f0);
  background: rgba(255, 255, 255, 0.03);
}

.tab-btn.active {
  color: var(--primary-color, #60a5fa);
  border-bottom-color: var(--primary-color, #60a5fa);
  background: rgba(96, 165, 250, 0.05);
}

.tab-content {
  border: 1px solid var(--surface-border, #334155);
  border-top: none;
  border-radius: 0 0 8px 8px;
  background: var(--surface-card, #1e293b);
  min-height: 500px;
}

.tab-panel {
  padding: 0;
}

/* Leaflet map */
.leaflet-map-container {
  width: 100%;
  height: 550px;
  background: #0d1117;
}

.map-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  padding: 0.5rem 1rem;
  background: rgba(0, 0, 0, 0.3);
  font-size: 0.75rem;
  color: var(--text-color-secondary, #94a3b8);
  align-items: center;
}

.map-style-toggle {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  padding: 0.2rem 0.5rem;
  border-radius: 6px;
  border: 1px solid var(--surface-border, #334155);
  background: rgba(255, 255, 255, 0.08);
  color: var(--text-color-secondary, #94a3b8);
  font-size: 0.75rem;
  cursor: pointer;
  transition: all 0.2s;
}

.map-style-toggle:hover {
  background: rgba(255, 255, 255, 0.15);
  color: var(--text-color, #e2e8f0);
}

.legend-sep {
  width: 1px;
  height: 14px;
  background: var(--surface-border, #334155);
}

.legend-item {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
}

.legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  display: inline-block;
}

.legend-line {
  width: 16px;
  height: 0;
  border-top: 2px solid;
  display: inline-block;
}

.legend-diamond {
  width: 8px;
  height: 8px;
  background: #dc2626;
  transform: rotate(45deg);
  display: inline-block;
  border: 1px solid #fff;
}

.legend-x {
  display: inline-block;
  width: 12px;
  height: 12px;
  position: relative;
}

.legend-x::before,
.legend-x::after {
  content: '';
  position: absolute;
  width: 14px;
  height: 2px;
  background: #ef4444;
  top: 50%;
  left: -1px;
}

.legend-x::before { transform: rotate(45deg); }
.legend-x::after { transform: rotate(-45deg); }

/* Chart grid */
.chart-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.75rem;
  padding: 1rem;
}

.chart-cell {
  background: rgba(0, 0, 0, 0.2);
  border: 1px solid var(--surface-border, #334155);
  border-radius: 8px;
  padding: 0.5rem;
  height: 280px;
  position: relative;
}

.chart-cell canvas {
  width: 100% !important;
  height: 100% !important;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 400px;
  color: var(--text-color-secondary, #94a3b8);
  gap: 0.75rem;
}

.ml-info {
  margin: 0.75rem 1rem 0 1rem;
}

/* Responsive */
@media (max-width: 900px) {
  .chart-grid {
    grid-template-columns: 1fr;
  }

  .header-top {
    flex-direction: column;
  }

  .leaflet-map-container {
    height: 400px;
  }
}

/* Leaflet tooltip styling */
:deep(.sensor-tooltip) {
  background: rgba(30, 41, 59, 0.9);
  border: 1px solid rgba(96, 165, 250, 0.4);
  color: #e2e8f0;
  font-size: 0.75rem;
  font-weight: 600;
  padding: 2px 6px;
}
</style>
