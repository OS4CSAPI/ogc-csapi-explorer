<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, computed } from 'vue'
import { useRouter } from 'vue-router'
import { connection, RESOURCE_TYPES } from '../state'
import { apiFetch } from '../api'
import { getListUrl, getNestedListUrl, getUpdateUrl } from '../csapi-bridge'
import { useDeployedSystemCard } from '../composables/useDeployedSystemCard'
import DeployedSystemCard from '../components/DeployedSystemCard.vue'

// OpenLayers imports
import Map from 'ol/Map'
import View from 'ol/View'
import TileLayer from 'ol/layer/Tile'
import VectorLayer from 'ol/layer/Vector'
import VectorSource from 'ol/source/Vector'
import OSM from 'ol/source/OSM'
import XYZ from 'ol/source/XYZ'
import { fromLonLat, toLonLat } from 'ol/proj'
import Feature from 'ol/Feature'
import Point from 'ol/geom/Point'
import Polygon, { circular as circularPolygon } from 'ol/geom/Polygon'
import LineString from 'ol/geom/LineString'
import { Style, Circle as CircleStyle, Fill, Stroke, Text as OlText, Icon as OlIcon, RegularShape } from 'ol/style'
import Overlay from 'ol/Overlay'
import { getSymbolForResource, getSymbolSizeForType, renderSenrepSymbol, type MilSymbolResult } from '../symbol-mapper'
import type { Coordinate } from 'ol/coordinate'
import Draw, { createBox } from 'ol/interaction/Draw'

const router = useRouter()

// Redirect if not connected
watch(
  () => connection.connected,
  (connected) => { if (!connected) router.push('/') },
  { immediate: true }
)

// --- State ---
const mapContainer = ref<HTMLDivElement>()
const popupContainer = ref<HTMLDivElement>()
let map: Map | null = null
let overlay: Overlay | null = null
let globalEnterHandler: ((e: KeyboardEvent) => void) | null = null

const loading = ref(false)
const error = ref('')
const mouseCoords = ref('')
const featureCounts = ref<Record<string, number>>({})
const selectedFeature = ref<any>(null)
const stackedFeatures = ref<any[]>([])  // multiple features at same pixel
const hasSearched = ref(false)

// Part 1 resource types that may have geometry
const SPATIAL_TYPES = RESOURCE_TYPES.filter(r => r.part === 1 && r.key !== 'properties')

// Part 2 types shown on the map (placed at parent system's location)
const PART2_MAP_TYPES = RESOURCE_TYPES.filter(r => ['datastreams', 'controlStreams'].includes(r.key))

// Synthetic entries for observation-derived layers (not real API resource types)
const OBS_TRACK_ENTRY = { key: 'observationTracks', label: 'Obs. Track', plural: 'Observation Tracks', icon: 'pi pi-directions', part: 2 as const, readOnly: true }
const OBS_POINTS_ENTRY = { key: 'observationPoints', label: 'Observation', plural: 'Observations', icon: 'pi pi-circle', part: 2 as const, readOnly: true }
const LOB_ENTRY = { key: 'bearingLines', label: 'Bearing', plural: 'Lines of Bearing', icon: 'pi pi-compass', part: 2 as const, readOnly: true }

// Detection range layer entry (not a real API resource type)
const DETECTION_RANGES_ENTRY = { key: 'detectionRanges', label: 'Det. Range', plural: 'Detection Ranges', icon: 'pi pi-circle', part: 2 as const, readOnly: true }

// Location estimate layer entry (localizer triangulation fixes)
const LOC_ESTIMATE_ENTRY = { key: 'locationEstimates', label: 'Loc. Est.', plural: 'Location Estimates', icon: 'pi pi-map-marker', part: 2 as const, readOnly: true }

// SENREP marker layer entry (human-submitted sensor reports)
const SENREP_ENTRY = { key: 'senrepMarkers', label: 'SENREP', plural: 'SENREP Reports', icon: 'pi pi-flag', part: 2 as const, readOnly: true }

// All types visible on the map
const MAP_TYPES = [...SPATIAL_TYPES, ...PART2_MAP_TYPES, OBS_POINTS_ENTRY, OBS_TRACK_ENTRY, LOB_ENTRY, DETECTION_RANGES_ENTRY, LOC_ESTIMATE_ENTRY, SENREP_ENTRY]

// Color map for resource types
const TYPE_COLORS: Record<string, string> = {
  systems: '#3b82f6',           // blue
  deployments: '#10b981',       // emerald / green
  procedures: '#f59e0b',        // amber
  samplingFeatures: '#8b5cf6',  // purple
  datastreams: '#ef4444',       // red
  controlStreams: '#f97316',    // orange
  observationTracks: '#06b6d4', // cyan
  observationPoints: '#ec4899', // pink
  bearingLines: '#f43f5e',      // rose
  detectionRanges: '#60a5fa',    // friendly blue (2525E)
  locationEstimates: '#facc15',  // gold / yellow
  senrepMarkers: '#ef4444',      // red — distinct from gold dots
}

const TYPE_LABELS: Record<string, string> = {
  systems: 'S',
  deployments: 'D',
  procedures: 'P',
  samplingFeatures: 'F',
  datastreams: 'DS',
  controlStreams: 'CS',
  observationTracks: '~',
  observationPoints: 'O',
  bearingLines: '►',
  detectionRanges: '◎',
  locationEstimates: '⊕',
  senrepMarkers: '◆',
}

// Active layer toggles
const activeLayers = ref<Record<string, boolean>>({
  systems: false,
  deployments: true,
  procedures: false,
  samplingFeatures: true,
  datastreams: false,
  controlStreams: false,
  observationTracks: true,
  observationPoints: true,
  bearingLines: true,
  detectionRanges: true,
  locationEstimates: true,
  senrepMarkers: true,
})

// ── Observation Source Toggle (per-publisher filtering) ─────────────────
const OBS_SOURCE_DEFS: Array<{ key: string; label: string; color: string; icon: string }> = [
  { key: 'src-iss',        label: 'ISS / Satellite',  color: '#a855f7', icon: '🛰️' },
  { key: 'src-nws',        label: 'NWS Weather',      color: '#60a5fa', icon: '🌤️' },
  { key: 'src-ndbc',       label: 'NDBC Buoys',       color: '#06b6d4', icon: '🌊' },
  { key: 'src-coops',      label: 'CO-OPS Tides',     color: '#14b8a6', icon: '🌊' },
  { key: 'src-metar',      label: 'Aviation METAR',   color: '#f59e0b', icon: '✈️' },
  { key: 'src-opensky',    label: 'OpenSky ADS-B',    color: '#ec4899', icon: '✈️' },
  { key: 'src-water',      label: 'USGS Water',       color: '#22d3ee', icon: '💧' },
  { key: 'src-nims',       label: 'USGS NIMS',        color: '#a78bfa', icon: '📷' },
  { key: 'src-earthquake', label: 'Earthquakes',      color: '#ef4444', icon: '🌋' },
]
const OBS_SOURCE_MAP = Object.fromEntries(OBS_SOURCE_DEFS.map(d => [d.key, d]))

/** Classify a datastream name into a source category key. */
function classifyObsSource(dsName: string): string {
  const n = dsName.toLowerCase()
  if (n.includes('sgp4') || n.includes('orbital') || n.includes('orbit')
    || (n.includes('iss') && (n.includes('position') || n.includes('track')))) return 'src-iss'
  if (n.includes('earthquake') || n.includes('seismic') || n.includes('quake')) return 'src-earthquake'
  if (n.includes('aircraft') || n.includes('adsb') || n.includes('ads-b')
    || n.includes('state vector') || n.includes('opensky')) return 'src-opensky'
  if (n.includes('nws')) return 'src-nws'
  if (n.includes('ndbc') || (n.includes('buoy') && !n.includes('cam'))) return 'src-ndbc'
  if (n.includes('co-ops') || n.includes('coops') || n.includes('tide') || n.includes('coastal')) return 'src-coops'
  if (n.includes('metar') || n.includes('awx') || n.includes('aviation')) return 'src-metar'
  if (n.includes('discharge') || n.includes('gage height')
    || n.includes('streamflow') || (n.includes('usgs') && n.includes('water'))) return 'src-water'
  if (n.includes('nims') || n.includes('station image')) return 'src-nims'
  // Generic position/location fallback — still ISS-like
  if (n.includes('position') || n.includes('location') || n.includes('gps')) return 'src-iss'
  return 'src-other'
}

// Per-source visibility + counts (dynamically populated during observation loading)
const activeObsSources = ref<Record<string, boolean>>({})
const obsSourceCounts = ref<Record<string, number>>({})

// Invisible style used to hide features when their source is toggled off
const HIDDEN_STYLE = new Style({})

// Cache: systemId → { lat, lon, alt?, datastreamName? }
const systemLocationCache: Record<string, { lat: number; lon: number; alt?: number; datastreamName?: string; phenomenonTime?: string }> = {}
// Primary (top-level) system IDs — limits per-system API calls to avoid O(N) subsystem fetches
const primarySystemIds = new Set<string>()
// Track location-related datastreams for observation track rendering
let locationDatastreamList: Array<{ id: string; name: string; systemId: string }> = []
// Localizer datastream ID — discovered dynamically from server
let localizerDatastreamId: string | null = null
// Track how many features were enriched from observations
const enrichedCounts = ref<Record<string, number>>({})

// Deployed system card composable
const { loading: dscLoading, card: dscCard, isDeployedSystemLeaf, composeCard: dscComposeCard, clearCard: dscClearCard } = useDeployedSystemCard()

// Deployment hierarchy maps — populated by enrichDeployments(), consumed by card composition
let deploymentParentMap: Record<string, string> = {}
let deploymentItemById: Record<string, any> = {}

// Bounding box filter state
const bboxFilter = ref<[number, number, number, number] | null>(null)
const drawingBbox = ref(false)

// Keyword and datetime filters
const keywordFilter = ref('')
const dtStart = ref('')
const dtEnd = ref('')
let drawInteraction: Draw | null = null
const bboxSource = new VectorSource()
const bboxLayer = new VectorLayer({
  source: bboxSource,
  style: new Style({
    stroke: new Stroke({ color: '#3b82f6', width: 2, lineDash: [6, 4] }),
    fill: new Fill({ color: 'rgba(59, 130, 246, 0)' }),
  }),
  zIndex: 20,
})

// Vector sources per type so we can toggle layers
const vectorSources: Record<string, VectorSource> = {}
const vectorLayers: Record<string, VectorLayer> = {}

// ── Live Mode (auto-refresh dynamic layers) ────────────────────────
const liveMode = ref(true)
let liveInterval: ReturnType<typeof setInterval> | null = null
const lastRefreshTime = ref('')
const LIVE_REFRESH_MS = 8000                // 8s cycle (scaled for 15-20 concurrent users)
const INITIAL_POLL_STAGGER_MS = 3000        // Random delay before first live poll (thundering herd prevention)

// ── Simulator / Reset Controls ────────────────────────────────
const SIM_API = 'https://129-80-248-53.sslip.io/simulator'
const simRunning = ref(false)
const simStarting = ref(false)
const simStopping = ref(false)
const demoResetting = ref(false)
const simMessage = ref('')
let simPollTimer: ReturnType<typeof setInterval> | null = null

async function simApiFetch(path: string, opts?: RequestInit) {
  const resp = await fetch(`${SIM_API}${path}`, {
    ...opts,
    headers: { 'Content-Type': 'application/json', ...(opts?.headers || {}) },
  })
  return resp.json()
}

async function pollSimStatus() {
  try {
    const data = await simApiFetch('/status')
    simRunning.value = !!data.running
  } catch { /* ignore */ }
}

function startSimPolling() {
  pollSimStatus()
  if (!simPollTimer) simPollTimer = setInterval(pollSimStatus, 4000)
}

function stopSimPolling() {
  if (simPollTimer) { clearInterval(simPollTimer); simPollTimer = null }
}

async function startSimulator() {
  if (simRunning.value || simStarting.value) return
  simStarting.value = true
  simMessage.value = ''
  try {
    const data = await simApiFetch('/start', {
      method: 'POST',
      body: JSON.stringify({ duration_s: 3600, interval_s: 5, speed_kmh: 12, start_offset_s: 500 }),
    })
    simMessage.value = data.message || ''
    if (data.ok) simRunning.value = true
  } catch (e: any) {
    simMessage.value = e.message || 'Failed to start simulator'
  } finally {
    simStarting.value = false
  }
}

async function stopSimulator() {
  if (!simRunning.value || simStopping.value) return
  simStopping.value = true
  simMessage.value = ''
  try {
    const data = await simApiFetch('/stop', { method: 'POST' })
    simMessage.value = data.message || 'Stopped'
    if (data.ok) simRunning.value = false
  } catch (e: any) {
    simMessage.value = e.message || 'Failed to stop simulator'
  } finally {
    simStopping.value = false
  }
}

async function fullDemoReset() {
  if (demoResetting.value) return
  if (!confirm('Full demo reset: delete ALL sim data, SENREPs, and sampling features. Continue?')) return
  demoResetting.value = true
  simMessage.value = ''
  try {
    // Stop the simulator first if it's running
    if (simRunning.value) {
      const stopData = await simApiFetch('/stop', { method: 'POST' })
      if (stopData.ok) simRunning.value = false
      // Brief pause for server to finish stopping
      await new Promise(resolve => setTimeout(resolve, 500))
    }
    const data = await simApiFetch('/reset', { method: 'POST' })
    simMessage.value = data.message || ''
    if (data.ok) {
      // Refresh the map to show cleared state
      await loadAllResources()
    }
  } catch (e: any) {
    simMessage.value = e.message || 'Failed to reset demo'
  } finally {
    demoResetting.value = false
  }
}

// ── SENREP Click-to-Report Panel State ─────────────────────────────
const senrepPanelOpen = ref(false)
const senrepSubmitting = ref(false)
const senrepSuccess = ref(false)
let nextContactSeq = 1
const operatorInitials = ref(localStorage.getItem('os4csapi-operator-initials') || '')
/** Known SENREP contact IDs (from loaded markers) that have at least one INIT — available for FUP. */
const knownSenrepContacts = ref<string[]>([])
/** Map contactId → senderId (operator initials) who created the INIT, for multi-user filtering. */
const senrepContactOwners = ref<Record<string, string>>({})
/** Contacts owned by the current operator — the only ones shown in the FUP dropdown. */
const myContacts = computed(() =>
  knownSenrepContacts.value.filter(cid => senrepContactOwners.value[cid] === operatorInitials.value)
)
const senrepForm = ref({
  contactId: '',
  classification: 'UAS',
  reportType: 'INIT',
  operatorNotes: '',
  estimatedLat: 0,
  estimatedLon: 0,
  cep50_m: 0,
  numContributingLobs: 0,
  contributingSensors: '',
  stringId: 'STRING-ALPHA',
  sourceFixObsId: '',
  sourceLobObsIds: '',
})

function generateContactId(): string {
  const d = new Date()
  const date = `${d.getFullYear()}${String(d.getMonth() + 1).padStart(2, '0')}${String(d.getDate()).padStart(2, '0')}`
  const initials = operatorInitials.value || 'XX'
  const seq = String(nextContactSeq++).padStart(3, '0')
  return `C-${date}-${initials}-${seq}`
}

function openSenrepPanel(rawData: any) {
  // Prompt for initials on first use
  if (!operatorInitials.value) {
    const initials = prompt('Enter your operator initials (2-3 characters):')
    if (initials && initials.trim().length >= 1) {
      operatorInitials.value = initials.trim().toUpperCase().slice(0, 3)
      localStorage.setItem('os4csapi-operator-initials', operatorInitials.value)
    } else {
      operatorInitials.value = 'XX'
    }
  }

  // If the panel is already open in FUP/FINAL mode, just update the position
  // fields — the operator clicked a new gold dot to supply the next location.
  if (senrepPanelOpen.value && (senrepForm.value.reportType === 'FUP' || senrepForm.value.reportType === 'FINAL')) {
    senrepForm.value.estimatedLat = rawData?.estimatedLat ?? senrepForm.value.estimatedLat
    senrepForm.value.estimatedLon = rawData?.estimatedLon ?? senrepForm.value.estimatedLon
    senrepForm.value.cep50_m = rawData?.cep50_m ?? senrepForm.value.cep50_m
    senrepForm.value.numContributingLobs = rawData?.numContributingLobs ?? senrepForm.value.numContributingLobs
    senrepForm.value.sourceFixObsId = rawData?.observationId || senrepForm.value.sourceFixObsId
    senrepSuccess.value = false
    return
  }

  // If the operator already has contacts, default to FUP for the most recent one
  // (reduces clicks for the common case of successive follow-ups)
  const hasOwnContacts = myContacts.value.length > 0
  const defaultType = hasOwnContacts ? 'FUP' : 'INIT'
  const defaultContact = hasOwnContacts
    ? (senrepForm.value.contactId && myContacts.value.includes(senrepForm.value.contactId)
        ? senrepForm.value.contactId  // keep current selection if still valid
        : myContacts.value[myContacts.value.length - 1] ?? '')  // most recent
    : generateContactId()

  senrepForm.value = {
    contactId: defaultContact,
    classification: rawData?.classification || 'UAS',
    reportType: defaultType,
    operatorNotes: '',
    estimatedLat: rawData?.estimatedLat ?? 0,
    estimatedLon: rawData?.estimatedLon ?? 0,
    cep50_m: rawData?.cep50_m ?? 0,
    numContributingLobs: rawData?.numContributingLobs ?? 0,
    contributingSensors: rawData?.contributingSensors || '',
    stringId: 'STRING-ALPHA',
    sourceFixObsId: rawData?.observationId || '',
    sourceLobObsIds: '',
  }
  senrepSuccess.value = false
  senrepPanelOpen.value = true
}

/** When the operator switches to FUP, swap the contact ID to their most recent contact.
 *  When switching back to INIT, generate a fresh contact ID. */
function onReportTypeChange() {
  if (senrepForm.value.reportType === 'FUP' || senrepForm.value.reportType === 'FINAL') {
    // Pre-select the operator's most recent contact (last in sorted list)
    const mine = myContacts.value
    senrepForm.value.contactId = mine.length ? mine[mine.length - 1] ?? senrepForm.value.contactId : senrepForm.value.contactId
  } else if (senrepForm.value.reportType === 'INIT') {
    senrepForm.value.contactId = generateContactId()
  }
}

async function submitSenrep(): Promise<void> {
  senrepSubmitting.value = true
  senrepSuccess.value = false
  try {
    const now = new Date()
    const yy = String(now.getFullYear()).slice(2)
    const mm = String(now.getMonth() + 1).padStart(2, '0')
    const dd = String(now.getDate()).padStart(2, '0')
    const hh = String(now.getUTCHours()).padStart(2, '0')
    const mi = String(now.getUTCMinutes()).padStart(2, '0')

    // Build doctrinal comments — pack contact metadata for readback
    const commentParts = [
      senrepForm.value.contactId,
      senrepForm.value.reportType || 'INIT',
      `CEP50=${senrepForm.value.cep50_m.toFixed(1)}m`,
      `LOBs=${senrepForm.value.numContributingLobs}`,
      senrepForm.value.operatorNotes || '',
      senrepForm.value.sourceFixObsId ? `fixId=${senrepForm.value.sourceFixObsId}` : '',
    ].filter(Boolean).join(' | ')

    // Map form data → doctrinal SENREP 20-field schema (matches DS 04g0)
    const obs = {
      phenomenonTime: now.toISOString(),
      resultTime: now.toISOString(),
      result: {
        timestamp: now.getTime() / 1000,
        title: senrepForm.value.contactId,                    // contact ID as report title
        senderId: operatorInitials.value || 'XX',             // operator initials
        seqNo: nextContactSeq - 1,                            // sequence number
        classification: 'U',                                  // Unclassified
        releasably: 'REL',                                    // REL for demo
        dor: `${yy}${mm}${dd}`,                               // YYMMDD
        envirOpName: 'FT-HUACHUCA',                           // exercise name
        strNo: senrepForm.value.stringId || 'AZ-STRING-ALPHA',
        detectTimeZ: `${hh}${mi}Z`,                            // HHMMZ
        qty: 1,
        tgtTyp: senrepForm.value.classification || 'UAS',     // target classification
        subTyp: senrepForm.value.reportType || 'INIT',        // report sub-type
        spd: 0,
        dirCardinal: 'UNK',
        colLengthM: 0,
        etaLat: senrepForm.value.estimatedLat,                // estimated target lat
        etaLon: senrepForm.value.estimatedLon,                // estimated target lon
        etaTimeZ: `${hh}${mi}Z`,
        comments: commentParts,
      },
    }

    const res = await apiFetch(`/datastreams/${SENREP_DS_ID}/observations`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      body: JSON.stringify(obs),
    })

    if (res.ok) {
      senrepSuccess.value = true

      // Phase 3.5: Create or update a SamplingFeature (track FOI) for this contact
      if (senrepForm.value.reportType === 'INIT') {
        try {
          await apiFetch('/samplingFeatures', {
            method: 'POST',
            headers: { 'Content-Type': 'application/geo+json', 'Accept': 'application/json' },
            body: JSON.stringify({
              type: 'Feature',
              geometry: {
                type: 'Point',
                coordinates: [senrepForm.value.estimatedLon, senrepForm.value.estimatedLat],
              },
              properties: {
                featureType: 'http://www.opengis.net/def/samplingFeatureType/OGC-OM/2.0/SF_SamplingPoint',
                uid: `urn:os4csapi:track:${senrepForm.value.contactId}`,
                name: `Track ${senrepForm.value.contactId}`,
                description: `UAS contact track created on first SENREP by ${operatorInitials.value || 'XX'}`,
              },
            }),
          })
        } catch { /* non-fatal — track FOI is optional */ }
      } else if (senrepForm.value.reportType === 'FUP' || senrepForm.value.reportType === 'FINAL') {
        // Update the existing sampling feature's location to the latest estimate
        try {
          const trackUid = `urn:os4csapi:track:${senrepForm.value.contactId}`
          // Find the sampling feature by UID — list with a limit and scan for match
          const sfListUrl = getListUrl('samplingFeatures', { limit: 200 })
          const sfListRes = await apiFetch(sfListUrl, {
            headers: { 'Accept': 'application/geo+json' },
          })
          if (sfListRes.ok && sfListRes.data) {
            const sfItems = sfListRes.data.type === 'FeatureCollection'
              ? (sfListRes.data.features || [])
              : (sfListRes.data.items || [])
            const match = sfItems.find((sf: any) => {
              const props = sf.properties || sf
              return props.uid === trackUid
            })
            if (match) {
              const sfId = match.id || match.properties?.id || match['@id']
              if (sfId) {
                const updateUrl = getUpdateUrl('samplingFeatures', sfId)
                await apiFetch(updateUrl, {
                  method: 'PUT',
                  headers: { 'Content-Type': 'application/geo+json', 'Accept': 'application/json' },
                  body: JSON.stringify({
                    type: 'Feature',
                    geometry: {
                      type: 'Point',
                      coordinates: [senrepForm.value.estimatedLon, senrepForm.value.estimatedLat],
                    },
                    properties: {
                      featureType: 'http://www.opengis.net/def/samplingFeatureType/OGC-OM/2.0/SF_SamplingPoint',
                      uid: trackUid,
                      name: `Track ${senrepForm.value.contactId}`,
                      description: `Location updated by ${senrepForm.value.reportType} SENREP from ${operatorInitials.value || 'XX'}`,
                    },
                  }),
                })
              }
            }
          }
        } catch { /* non-fatal — location update is best-effort */ }
      }

      // Refresh SENREP markers to show the new one
      // Brief delay allows server to index the new observation before query
      await new Promise(resolve => setTimeout(resolve, 500))
      await loadSenrepMarkers()
      // Also reload sampling features so the new track FOI appears
      const sfCount = await loadResourceType('samplingFeatures')
      featureCounts.value['samplingFeatures'] = sfCount

      // After INIT: switch to FUP mode for this contact (stay open for quick follow-ups)
      // After FUP/FINAL: stay in current mode with same contact (just clear success after delay)
      const submittedContact = senrepForm.value.contactId
      const submittedType = senrepForm.value.reportType
      if (submittedType === 'INIT') {
        // Transition to FUP mode — operator's next click will be a follow-up
        senrepForm.value.reportType = 'FUP'
        senrepForm.value.contactId = submittedContact
      }
      // Don't close the panel — let the operator click the next gold dot directly.
      // Just show success briefly, then clear the badge.
      setTimeout(() => {
        senrepSuccess.value = false
      }, 2000)
    } else {
      alert(`SENREP submission failed: ${res.status}`)
    }
  } catch (err: any) {
    alert(`SENREP submission error: ${err.message || err}`)
  } finally {
    senrepSubmitting.value = false
  }
}

// ── Detection Range Configuration ──────────────────────────────────
// Discovered from server: each system's "detection_capabilities" datastream
// provides min/nominal/max detection range values as observations.
// Populated by fetchDetectionRangeConfigs() before rings are drawn.
interface DetectionRing { label: string; radius_m: number }
interface DetectionRangeConfig {
  shape: string
  rings: DetectionRing[]
  confidence?: number
  basis?: string
  phenomenonTime?: string
}
const detectionRangeConfigs: Record<string, DetectionRangeConfig> = {}

// Hardcoded fallback — all three ODAS nodes share the same hardware.
// Used when the scope-leak bug buries the real observation beyond scan limits.
const DETECTION_RANGE_FALLBACK: DetectionRangeConfig = {
  shape: 'circular',
  rings: [
    { label: 'min', radius_m: 667 },
    { label: 'nominal', radius_m: 1833 },
    { label: 'max', radius_m: 3000 },
  ],
  confidence: 0.7,
  basis: 'estimated',
}
const ODAS_UIDS = [
  'urn:os4csapi:system:odas:az-ma-1',
  'urn:os4csapi:system:odas:az-ma-2',
  'urn:os4csapi:system:odas:az-ma-3',
]

// Enable/disable milsymbol rendering (toggle for A/B comparison)
const useMilSymbols = ref(true)

// ── Pre-built style caches for high-volume feature types ──
const obsPointStyle = new Style({
  image: new CircleStyle({
    radius: 4,
    fill: new Fill({ color: TYPE_COLORS['observationPoints'] || '#ec4899' }),
    stroke: new Stroke({ color: '#fff', width: 1 }),
  }),
})
const obsTrackStyle = new Style({
  stroke: new Stroke({ color: TYPE_COLORS['observationTracks'] || '#06b6d4', width: 3, lineDash: [8, 4] }),
})

// SENREP track line style — red dashed line connecting consecutive SENREPs for the same contact
const senrepTrackStyle = new Style({
  stroke: new Stroke({ color: '#ef4444', width: 2.5, lineDash: [6, 4] }),
})

// Orbit track style — solid bright line for satellite ground tracks
const orbitTrackStyle = new Style({
  stroke: new Stroke({ color: '#22d3ee', width: 2.5 }),
})
const orbitTrackGlowStyle = new Style({
  stroke: new Stroke({ color: 'rgba(34, 211, 238, 0.25)', width: 8 }),
})

// Satellite observation point style — distinct from generic obs points
const satObsPointStyle = new Style({
  image: new CircleStyle({
    radius: 3,
    fill: new Fill({ color: '#22d3ee' }),
    stroke: new Stroke({ color: '#fff', width: 0.5 }),
  }),
})

/**
 * Aircraft observation point style — rotated triangle showing heading.
 * Uses true_track_deg from ADS-B state vectors for orientation.
 */
function aircraftObsPointStyle(headingDeg: number): Style {
  return new Style({
    image: new RegularShape({
      points: 3,
      radius: 8,
      rotation: (headingDeg * Math.PI) / 180,
      fill: new Fill({ color: '#3b82f6' }),
      stroke: new Stroke({ color: '#1e3a5f', width: 1.5 }),
    }),
  })
}

/**
 * Create a per-station weather style with temperature label so stations
 * are immediately identifiable without clicking.
 */
function weatherStationStyle(stationId: string, tempC: number | null): Style {
  const label = tempC != null && !isNaN(Number(tempC))
    ? `${stationId}\n${Number(tempC).toFixed(0)}°C`
    : stationId
  return new Style({
    image: new RegularShape({
      points: 4,
      radius: 14,
      angle: Math.PI / 4,
      fill: new Fill({ color: '#0ea5e9' }),
      stroke: new Stroke({ color: '#0c4a6e', width: 2.5 }),
    }),
    text: new OlText({
      text: label,
      font: 'bold 11px sans-serif',
      offsetY: 22,
      fill: new Fill({ color: '#0c4a6e' }),
      stroke: new Stroke({ color: '#fff', width: 3 }),
      textAlign: 'center',
    }),
  })
}

/**
 * Detect whether an observation result represents a weather/surface observation
 * (NWS, METAR, etc.) by checking for temperature_c or temp_c + stationId signature fields.
 */
function isWeatherObservation(rawData: any): boolean {
  if (!rawData?.result) return false
  const r = rawData.result
  return (typeof r.temperature_c === 'number' || typeof r.temp_c === 'number')
    && typeof r.stationId === 'string'
}

/**
 * Detect whether an observation result represents an ADS-B aircraft state vector
 * by checking for icao24 + lat_deg + lon_deg signature fields.
 */
function isAircraftObservation(rawData: any): boolean {
  if (!rawData?.result) return false
  const r = rawData.result
  return typeof r.icao24 === 'string' && typeof r.lat_deg === 'number'
    && typeof r.lon_deg === 'number'
}

/** Format altitude for display: meters → feet with label */
function altFmt(m: any): string {
  if (m == null || m === 'NaN' || (typeof m === 'number' && isNaN(m))) return '—'
  const ft = Number(m) * 3.28084
  return `${Number(m).toFixed(0)} m (${ft.toFixed(0)} ft)`
}

/** Format speed for display: m/s → knots */
function spdFmt(ms: any): string {
  if (ms == null || ms === 'NaN' || (typeof ms === 'number' && isNaN(ms))) return '—'
  const kt = Number(ms) * 1.94384
  return `${Number(ms).toFixed(1)} m/s (${kt.toFixed(0)} kt)`
}

/**
 * Map weather textDescription to an emoji icon for the popup.
 */
function weatherIcon(desc: string | undefined): string {
  if (!desc) return '🌡️'
  const d = desc.toLowerCase()
  if (d.includes('thunder') || d.includes('storm')) return '⛈️'
  if (d.includes('rain') || d.includes('drizzle') || d.includes('shower')) return '🌧️'
  if (d.includes('snow') || d.includes('flurr')) return '🌨️'
  if (d.includes('fog') || d.includes('mist') || d.includes('haze')) return '🌫️'
  if (d.includes('cloud') || d.includes('overcast')) return '☁️'
  if (d.includes('partly') || d.includes('mostly sunny')) return '⛅'
  if (d.includes('fair') || d.includes('clear') || d.includes('sunny')) return '☀️'
  if (d.includes('wind')) return '💨'
  return '🌡️'
}

/**
 * Convert wind direction degrees to cardinal arrow.
 */
function windArrow(deg: number | undefined): string {
  if (deg == null || isNaN(Number(deg))) return ''
  const dirs = ['↓N', '↙NE', '←E', '↖SE', '↑S', '↗SW', '→W', '↘NW']
  return dirs[Math.round(Number(deg) / 45) % 8]
}

// ── Earthquake visualization helpers ─────────────────────────────────────

/**
 * Detect whether an observation result represents a USGS earthquake event
 * by checking for magnitude + eventType + depth_km signature fields.
 */
function isEarthquakeObservation(rawData: any): boolean {
  if (!rawData?.result) return false
  const r = rawData.result
  return (typeof r.magnitude === 'number' || typeof r.magnitude === 'string')
    && typeof r.eventType === 'string'
    && typeof r.depth_km === 'number'
}

/**
 * Map magnitude to a color:
 *   < 2.5  → green (micro)
 *   2.5–4.5 → yellow (light)
 *   4.5–6.0 → orange (moderate)
 *   ≥ 6.0   → red (strong+)
 */
function eqMagColor(mag: number): string {
  if (mag < 2.5) return '#22c55e'
  if (mag < 4.5) return '#eab308'
  if (mag < 6.0) return '#f97316'
  return '#ef4444'
}

/**
 * Map magnitude to a circle radius (exponential scaling like USGS map).
 * min ~4px for micro events, up to ~22px for M7+
 */
function eqMagRadius(mag: number): number {
  const clamped = Math.max(0, Math.min(mag, 9))
  return 4 + Math.pow(clamped, 1.5) * 0.8
}

/**
 * Earthquake observation point style — circle sized by magnitude,
 * colored by severity. Mimics USGS earthquake map visualization.
 */
function earthquakeObsPointStyle(mag: number): Style {
  const color = eqMagColor(mag)
  const radius = eqMagRadius(mag)
  return new Style({
    image: new CircleStyle({
      radius,
      fill: new Fill({ color: color + 'cc' }),  // slight transparency
      stroke: new Stroke({ color: '#1e293b', width: 1.5 }),
    }),
    text: mag >= 4.0 ? new OlText({
      text: `M${typeof mag === 'number' ? mag.toFixed(1) : mag}`,
      font: 'bold 10px sans-serif',
      offsetY: -(radius + 10),
      fill: new Fill({ color }),
      stroke: new Stroke({ color: '#0f172a', width: 2.5 }),
      textAlign: 'center',
    }) : undefined,
  })
}

/** Relative time label for earthquake popup — "2 min ago", "3 hr ago", etc. */
function eqTimeAgo(epochMs: number | string | undefined): string {
  if (!epochMs) return ''
  const ms = typeof epochMs === 'string' ? parseInt(epochMs, 10) : epochMs
  if (isNaN(ms)) return ''
  const diffMs = Date.now() - ms
  if (diffMs < 0) return 'just now'
  const mins = Math.floor(diffMs / 60000)
  if (mins < 1) return 'just now'
  if (mins < 60) return `${mins} min ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs} hr ago`
  const days = Math.floor(hrs / 24)
  return `${days} day${days > 1 ? 's' : ''} ago`
}

/** Magnitude description label */
function eqMagLabel(mag: number): string {
  if (mag < 2.5) return 'Micro'
  if (mag < 4.0) return 'Minor'
  if (mag < 5.0) return 'Light'
  if (mag < 6.0) return 'Moderate'
  if (mag < 7.0) return 'Strong'
  if (mag < 8.0) return 'Major'
  return 'Great'
}

/**
 * Safely format a numeric value that may be NaN, "NaN" string, null, or undefined.
 */
function wxFmt(val: any, decimals = 0, fallback = '—'): string {
  if (val == null) return fallback
  const n = Number(val)
  if (isNaN(n)) return fallback
  return n.toFixed(decimals)
}

// Bearing-line styles bucketed by quantized energy (10 buckets → max 10 style objects)
const bearingStyleCache = new Map<number, Style>()
function getCachedBearingLineStyle(energy: number): Style {
  const bucket = Math.round(Math.min(energy, 1) * 10)      // 0–10
  let s = bearingStyleCache.get(bucket)
  if (s) return s
  const hex = TYPE_COLORS['bearingLines'] || '#f43f5e'
  const r = parseInt(hex.slice(1, 3), 16)
  const g = parseInt(hex.slice(3, 5), 16)
  const b = parseInt(hex.slice(5, 7), 16)
  // Minimum opacity raised from 0.4 → 0.55 so low-energy LOBs remain visible
  // even when overlapping with detection range fills or other sensors' lines.
  const opacity = 0.55 + (bucket / 10) * 0.45
  const width = 2.5 + (bucket / 10) * 1.5
  s = new Style({ stroke: new Stroke({ color: `rgba(${r}, ${g}, ${b}, ${opacity})`, width }) })
  bearingStyleCache.set(bucket, s)
  return s
}

// Recency-based bearing-line styles: newest = bright & thick, oldest = faded & thin
// Key: 100 * ageBucket + energyBucket (composite key to cache both dimensions)
const recencyStyleCache = new Map<number, Style>()
function getRecencyBearingStyle(energy: number, recency: number): Style {
  // recency: 1.0 = newest, 0.0 = oldest in the batch
  const eBucket = Math.round(Math.min(energy, 1) * 10)
  const rBucket = Math.round(Math.min(recency, 1) * 10)
  const key = rBucket * 100 + eBucket
  let s = recencyStyleCache.get(key)
  if (s) return s
  // Newest: bright red, wide; Oldest: gray-blue, thin but still visible
  // Base opacity bumped from 0.15 → 0.35 so even the oldest LOBs remain
  // clearly visible instead of disappearing under overlapping features.
  const freshR = 244, freshG = 63,  freshB = 94   // rose #f43f5e
  const staleR = 148, staleG = 163, staleB = 184  // gray #94a3b8
  const r = Math.round(staleR + (freshR - staleR) * recency)
  const g = Math.round(staleG + (freshG - staleG) * recency)
  const b = Math.round(staleB + (freshB - staleB) * recency)
  const opacity = 0.35 + recency * 0.55
  const width = 1.5 + recency * 2
  s = new Style({ stroke: new Stroke({ color: `rgba(${r}, ${g}, ${b}, ${opacity})`, width }) })
  recencyStyleCache.set(key, s)
  return s
}

// Basemap toggle (OSM vs satellite)
const useSatellite = ref(false)
let osmLayer: TileLayer | null = null
let satLayer: TileLayer | null = null
let satRefLayer: TileLayer | null = null

function getResourceName(rawData?: any): string {
  if (!rawData) return ''
  return rawData?.properties?.name || rawData?.name || rawData?.label || ''
}

function makeNameLabel(name: string, offsetY: number): Style | null {
  if (!name) return null
  return new Style({
    text: new OlText({
      text: name,
      font: 'bold 12px sans-serif',
      fill: new Fill({ color: '#fff' }),
      stroke: new Stroke({ color: '#000', width: 4 }),
      backgroundFill: new Fill({ color: 'rgba(0, 0, 0, 0.55)' }),
      backgroundStroke: new Stroke({ color: 'rgba(255,255,255,0.3)', width: 1 }),
      padding: [2, 6, 2, 6],
      offsetY,
      textAlign: 'center',
    }),
    zIndex: 100,   // labels always render above icons so STANAG symbols don't cover them
  })
}

/** Check if a deployment has a platform@link — only these physical emplacements get STANAG symbols.
 *  Organizational deployments (ICO, R&S, SSO, SNET, Field, String) use plain circles. */
function hasPlatformLink(rawData: any): boolean {
  const props = rawData?.properties || rawData || {}
  return !!(props['platform@link']?.href)
}

function getStyle(resourceType: string, enriched = false, rawData?: any): Style | Style[] {
  const color = TYPE_COLORS[resourceType] || '#6b7280'
  const label = TYPE_LABELS[resourceType] || '?'

  // Observation tracks — return cached style
  if (resourceType === 'observationTracks') return obsTrackStyle

  // Individual observation points — return cached style
  if (resourceType === 'observationPoints') return obsPointStyle

  // Bearing lines — return cached style (energy-based version used in loadObservationLayers)
  if (resourceType === 'bearingLines') return getCachedBearingLineStyle(0.5)

  const name = getResourceName(rawData)

  // --- MIL-STD-2525 symbol rendering (only deployments with platform@link) ---
  if (useMilSymbols.value && rawData && resourceType === 'deployments' && hasPlatformLink(rawData)) {
    const sz = getSymbolSizeForType(resourceType)
    const sym = getSymbolForResource(resourceType, rawData, sz)
    if (sym) {
      const iconStyle = new Style({
        image: new OlIcon({
          src: sym.svgDataUrl,
          anchor: [sym.anchor.x / sym.size.width, sym.anchor.y / sym.size.height],
          anchorXUnits: 'fraction',
          anchorYUnits: 'fraction',
          scale: 1,
          opacity: enriched ? 0.85 : 1,
        }),
        stroke: new Stroke({ color, width: 2 }),
        fill: new Fill({ color: color + '33' }),
      })
      const nameStyle = makeNameLabel(name, sym.size.height - sym.anchor.y + 14)
      return nameStyle ? [iconStyle, nameStyle] : iconStyle
    }
  }

  // --- SENREP track sampling features: render STANAG symbol for urn:os4csapi:track:* UIDs ---
  if (useMilSymbols.value && rawData && resourceType === 'samplingFeatures') {
    const uid = rawData?.properties?.uid || rawData?.uid || ''
    if (typeof uid === 'string' && uid.startsWith('urn:os4csapi:track:')) {
      const sym = renderSenrepSymbol('UAS', 16)
      if (sym) {
        const iconStyle = new Style({
          image: new OlIcon({
            src: sym.svgDataUrl,
            anchor: [sym.anchor.x / sym.size.width, sym.anchor.y / sym.size.height],
            anchorXUnits: 'fraction',
            anchorYUnits: 'fraction',
            scale: 1,
            opacity: enriched ? 0.85 : 1,
          }),
          stroke: new Stroke({ color, width: 2 }),
          fill: new Fill({ color: color + '33' }),
        })
        const nameStyle = makeNameLabel(name, sym.size.height - sym.anchor.y + 14)
        return nameStyle ? [iconStyle, nameStyle] : iconStyle
      }
    }
  }

  // --- Fallback: colored circle with letter ---
  const isPart2 = resourceType === 'datastreams' || resourceType === 'controlStreams'
  const radius = isPart2 ? 7 : 10
  const font = isPart2 ? 'bold 8px sans-serif' : 'bold 11px sans-serif'

  const circleStyle = new Style({
    image: new CircleStyle({
      radius,
      fill: new Fill({ color }),
      stroke: new Stroke({
        color: enriched ? color : '#fff',
        width: 2,
        lineDash: enriched ? [4, 4] : undefined,
      }),
    }),
    text: new OlText({
      text: label,
      fill: new Fill({ color: '#fff' }),
      font,
      offsetY: 1,
    }),
    stroke: new Stroke({ color, width: 2 }),
    fill: new Fill({ color: color + '33' }),
  })

  const nameStyle = makeNameLabel(name, radius + 14)
  return nameStyle ? [circleStyle, nameStyle] : circleStyle
}

function getSelectedStyle(resourceType: string, rawData?: any): Style | Style[] {
  const color = TYPE_COLORS[resourceType] || '#6b7280'
  const label = TYPE_LABELS[resourceType] || '?'

  if (resourceType === 'observationTracks') {
    return new Style({
      stroke: new Stroke({ color: '#fbbf24', width: 5 }),
    })
  }

  if (resourceType === 'observationPoints') {
    return new Style({
      image: new CircleStyle({
        radius: 7,
        fill: new Fill({ color }),
        stroke: new Stroke({ color: '#fbbf24', width: 3 }),
      }),
    })
  }

  if (resourceType === 'bearingLines') {
    return new Style({
      stroke: new Stroke({ color: '#fbbf24', width: 5 }),
    })
  }

  const name = getResourceName(rawData)

  // --- MIL-STD-2525 selected: render at larger size (only deployments with platform@link) ---
  if (useMilSymbols.value && rawData && resourceType === 'deployments' && hasPlatformLink(rawData)) {
    const sym = getSymbolForResource(resourceType, rawData, 'normal')
    if (sym) {
      const iconStyle = new Style({
        image: new OlIcon({
          src: sym.svgDataUrl,
          anchor: [sym.anchor.x / sym.size.width, sym.anchor.y / sym.size.height],
          anchorXUnits: 'fraction',
          anchorYUnits: 'fraction',
          scale: 1.3,
        }),
        stroke: new Stroke({ color: '#fbbf24', width: 3 }),
        fill: new Fill({ color: color + '55' }),
      })
      const nameStyle = makeNameLabel(name, (sym.size.height - sym.anchor.y) * 1.3 + 14)
      return nameStyle ? [iconStyle, nameStyle] : iconStyle
    }
  }

  // --- SENREP track sampling features selected: larger STANAG symbol ---
  if (useMilSymbols.value && rawData && resourceType === 'samplingFeatures') {
    const uid = rawData?.properties?.uid || rawData?.uid || ''
    if (typeof uid === 'string' && uid.startsWith('urn:os4csapi:track:')) {
      const sym = renderSenrepSymbol('UAS', 20)
      if (sym) {
        const iconStyle = new Style({
          image: new OlIcon({
            src: sym.svgDataUrl,
            anchor: [sym.anchor.x / sym.size.width, sym.anchor.y / sym.size.height],
            anchorXUnits: 'fraction',
            anchorYUnits: 'fraction',
            scale: 1.3,
          }),
          stroke: new Stroke({ color: '#fbbf24', width: 3 }),
          fill: new Fill({ color: color + '55' }),
        })
        const nameStyle = makeNameLabel(name, (sym.size.height - sym.anchor.y) * 1.3 + 14)
        return nameStyle ? [iconStyle, nameStyle] : iconStyle
      }
    }
  }

  // --- Fallback: colored circle selected ---
  const isPart2 = resourceType === 'datastreams' || resourceType === 'controlStreams'
  const radius = isPart2 ? 10 : 14
  const font = isPart2 ? 'bold 10px sans-serif' : 'bold 13px sans-serif'

  const circleStyle = new Style({
    image: new CircleStyle({
      radius,
      fill: new Fill({ color }),
      stroke: new Stroke({ color: '#fbbf24', width: 3 }),
    }),
    text: new OlText({
      text: label,
      fill: new Fill({ color: '#fff' }),
      font,
      offsetY: 1,
    }),
    stroke: new Stroke({ color: '#fbbf24', width: 3 }),
    fill: new Fill({ color: color + '55' }),
  })

  const nameStyle = makeNameLabel(name, radius + 14)
  return nameStyle ? [circleStyle, nameStyle] : circleStyle
}

// --- Data Loading ---

function extractGeometry(item: any): { type: string; coordinates: any } | null {
  // GeoJSON Feature
  if (item.geometry && item.geometry.type && item.geometry.coordinates) {
    return item.geometry
  }
  // Flat object with geometry at top level
  if (item.type === 'Point' || item.type === 'Polygon' || item.type === 'LineString') {
    return { type: item.type, coordinates: item.coordinates }
  }
  return null
}

function extractName(item: any): string {
  return item.properties?.name
    || item.properties?.title
    || item.name
    || item.label
    || item.title
    || item.id
    || '(unnamed)'
}

function extractId(item: any): string {
  return item.id || item.properties?.uid || item['@id'] || ''
}

function createOlFeature(item: any, resourceType: string): Feature | null {
  const geom = extractGeometry(item)
  if (!geom) return null

  let olGeom
  try {
    if (geom.type === 'Point') {
      olGeom = new Point(fromLonLat(geom.coordinates))
    } else if (geom.type === 'Polygon') {
      olGeom = new Polygon(geom.coordinates.map((ring: number[][]) =>
        ring.map((coord: number[]) => fromLonLat(coord))
      ))
    } else if (geom.type === 'LineString') {
      olGeom = new LineString(geom.coordinates.map((coord: number[]) => fromLonLat(coord)))
    } else {
      return null
    }
  } catch {
    return null
  }

  const feature = new Feature({ geometry: olGeom })
  feature.setStyle(getStyle(resourceType, false, item))
  feature.set('resourceType', resourceType)
  feature.set('resourceId', extractId(item))
  feature.set('resourceName', extractName(item))
  feature.set('rawData', item)
  return feature
}

/** Build the common query options from all active filters */
function buildQueryOptions(extraLimit = 200): Record<string, any> {
  const opts: Record<string, any> = { limit: extraLimit, bbox: bboxFilter.value ?? undefined }
  if (keywordFilter.value.trim()) opts.q = keywordFilter.value.trim()
  if (dtStart.value || dtEnd.value) {
    const s = dtStart.value ? new Date(dtStart.value) : undefined
    const e = dtEnd.value ? new Date(dtEnd.value) : undefined
    if (s && e) opts.datetime = { start: s, end: e }
    else if (s) opts.datetime = { start: s }
    else if (e) opts.datetime = { end: e }
  }
  return opts
}

/** Like buildQueryOptions but WITHOUT bbox — for deployments, which derive geometry
 *  from subdeployments/deployed-systems and must be filtered client-side. */
function buildQueryOptionsNoBbox(extraLimit = 200): Record<string, any> {
  const opts: Record<string, any> = { limit: extraLimit }
  if (keywordFilter.value.trim()) opts.q = keywordFilter.value.trim()
  if (dtStart.value || dtEnd.value) {
    const s = dtStart.value ? new Date(dtStart.value) : undefined
    const e = dtEnd.value ? new Date(dtEnd.value) : undefined
    if (s && e) opts.datetime = { start: s, end: e }
    else if (s) opts.datetime = { start: s }
    else if (e) opts.datetime = { end: e }
  }
  return opts
}

async function loadResourceType(resourceType: string): Promise<number> {
  const source = vectorSources[resourceType]
  if (!source) return 0

  source.clear()

  try {
    // Deployments and SamplingFeatures: skip server-side bbox.
    // - Deployments derive geometry from subdeployments & deployed systems.
    // - SamplingFeatures: OSH returns empty when bbox is included in the query.
    const noBboxTypes = new Set(['deployments', 'samplingFeatures'])
    const opts = noBboxTypes.has(resourceType) ? buildQueryOptionsNoBbox() : buildQueryOptions()
    const url = getListUrl(resourceType, opts)
    // Request geo+json so servers return GeoJSON features with geometry
    const res = await apiFetch(url, {
      headers: { 'Accept': 'application/geo+json' },
    })
    if (!res.ok || !res.data) return 0

    // Parse items from either FeatureCollection or items envelope
    let items: any[] = []
    if (res.data.type === 'FeatureCollection' && Array.isArray(res.data.features)) {
      items = res.data.features
    } else if (Array.isArray(res.data.items)) {
      items = res.data.items
    } else if (Array.isArray(res.data)) {
      items = res.data
    }

    const batch: Feature[] = []
    for (const item of items) {
      // For deployments, only draw items with platform@link (physical emplacement).
      // deployedSystemUIDs and deployedSystems@link are organizational references,
      // not physical co-location indicators.
      if (resourceType === 'deployments') {
        const props = item.properties || item || {}
        if (!props['platform@link']?.href) continue
      }
      const feature = createOlFeature(item, resourceType)
      if (feature) batch.push(feature)
    }
    if (batch.length) source.addFeatures(batch)
    return batch.length
  } catch {
    return 0
  }
}

/**
 * Split a track coordinate array into segments at antimeridian (±180° lon)
 * crossings.  Prevents the ugly straight line across the entire map when
 * a satellite (or any object) crosses the date line.
 */
function splitTrackAtDateLine(coords: [number, number][]): [number, number][][] {
  if (coords.length < 2) return [coords]
  const segments: [number, number][][] = []
  let current: [number, number][] = [coords[0]]
  for (let i = 1; i < coords.length; i++) {
    const prevLon = current[current.length - 1][0]
    const curLon = coords[i][0]
    if (Math.abs(curLon - prevLon) > 180) {
      // Antimeridian crossing — finish segment and start a new one
      segments.push(current)
      current = []
    }
    current.push(coords[i])
  }
  if (current.length > 0) segments.push(current)
  return segments
}

/**
 * Extract lat/lon from an observation result object, supporting multiple
 * field naming conventions used by different servers and data models.
 */
function extractLatLonFromResult(result: any): { lat: number; lon: number; alt?: number } | null {
  if (!result || typeof result !== 'object') return null

  // Direct lat/lon (e.g., GPS location datastreams)
  if (typeof result.lat === 'number' && typeof result.lon === 'number') {
    return { lat: result.lat, lon: result.lon, alt: result.alt }
  }
  // Nested Location/location object
  if (result.Location && typeof result.Location.lat === 'number') {
    return { lat: result.Location.lat, lon: result.Location.lon, alt: result.Location.alt }
  }
  if (result.location && typeof result.location.lat === 'number') {
    return { lat: result.location.lat, lon: result.location.lon, alt: result.location.alt }
  }
  // Full-word latitude/longitude (e.g., triangulated positions, geodetic outputs)
  if (typeof result.latitude === 'number' && typeof result.longitude === 'number') {
    return { lat: result.latitude, lon: result.longitude, alt: result.altitude }
  }
  // Common GIS conventions
  if (typeof result.Latitude === 'number' && typeof result.Longitude === 'number') {
    return { lat: result.Latitude, lon: result.Longitude, alt: result.Altitude }
  }
  // Suffixed variants (e.g., ISS tracker: lat_deg, lon_deg, alt_km)
  if (typeof result.lat_deg === 'number' && typeof result.lon_deg === 'number') {
    return { lat: result.lat_deg, lon: result.lon_deg, alt: result.alt_km }
  }

  return null
}

/**
 * Extract the parent system ID from a datastream or control-stream object.
 * Handles both `system@id` (SensorHub) and `system@link.href` (Go CSAPI).
 */
function extractSystemId(resource: any): string | undefined {
  return resource['system@id']
    || resource.system?.id
    || resource['system@link']?.href?.split('/').pop()
}

/**
 * Check whether a datastream might produce observations with geographic
 * coordinates, based on its name or observedProperty definitions/labels.
 */
function isLocationRelatedDatastream(ds: any): boolean {
  const name = (ds.name || ds.outputName || '').toLowerCase()
  // Classic GPS/location keywords
  if (name.includes('gps_data') || name.includes('location') || name.includes('position')) return true
  // Bearing / detection datastreams (LOB, SST, SSL, Track Updates, Scene Summary, Classification)
  if (name.includes('lob') || name.includes('track') || name.includes('ssl')
    || name.includes('sst') || name.includes('scene') || name.includes('classification')
    || name.includes('bearing')) return true
  // Weather / surface observation datastreams (NWS, METAR, etc.)
  if (name.includes('surface') || name.includes('weather') || name.includes('metar')
    || name.includes('nws') || name.includes('awx')) return true
  // Aircraft / ADS-B surveillance datastreams (OpenSky, AISHub, etc.)
  if (name.includes('aircraft') || name.includes('adsb') || name.includes('ads-b')
    || name.includes('state vector') || name.includes('flight')) return true
  // Earthquake / seismic event datastreams (USGS, etc.)
  if (name.includes('earthquake') || name.includes('seismic') || name.includes('quake')) return true
  // NDBC buoy observations (contain lat_deg/lon_deg in result)
  if (name.includes('ndbc') || name.includes('buoy')) return true
  // CO-OPS coastal/tide observations
  if (name.includes('co-ops') || name.includes('coops') || name.includes('tide') || name.includes('coastal')) return true
  // USGS Water (discharge, gage height)
  if (name.includes('discharge') || name.includes('gage') || name.includes('streamflow')) return true
  // USGS NIMS imagery
  if (name.includes('nims') || name.includes('station image')) return true

  const rawProps = ds.observedProperties
  const props: any[] = Array.isArray(rawProps) ? rawProps : rawProps ? [rawProps] : []
  return props.some((p: any) => {
    const def = (p.definition || '').toLowerCase()
    const label = (p.label || '').toLowerCase()
    return def.includes('location') || label.includes('location')
      || def.includes('geodeticlatitude') || def.includes('latitude')
      || def.includes('longitude') || def.includes('geolocation')
      || label.includes('latitude') || label.includes('longitude')
      || def.includes('bearingtrue') || def.includes('lobrecord')
      || def.includes('trackedso') || def.includes('trackupdate')
  })
}

/**
 * Phase A: Cache system locations from already-loaded Part 1 features that
 * have geometry.  Also derive system locations from deployment geometry via
 * the `platform@link` association property.
 */
function cacheLocationsFromLoadedFeatures(): void {
  // --- Systems with direct geometry ---
  const systemSource = vectorSources['systems']
  if (systemSource) {
    for (const feature of systemSource.getFeatures()) {
      const geom = feature.getGeometry()
      const sysId = feature.get('resourceId')
      if (geom && sysId && geom.getType() === 'Point') {
        const coords = toLonLat((geom as Point).getCoordinates())
        if (!systemLocationCache[sysId]) {
          systemLocationCache[sysId] = { lat: coords[1], lon: coords[0], datastreamName: 'system geometry' }
        }
        primarySystemIds.add(sysId)
      }
    }
  }

  // --- Deployments → platform@link → system ID ---
  const deploySource = vectorSources['deployments']
  if (deploySource) {
    for (const feature of deploySource.getFeatures()) {
      const geom = feature.getGeometry()
      const raw = feature.get('rawData')
      if (!geom || !raw) continue

      // Extract deployment centroid
      let lat: number, lon: number
      if (geom.getType() === 'Point') {
        const coords = toLonLat((geom as Point).getCoordinates())
        lon = coords[0]; lat = coords[1]
      } else {
        // Polygon/LineString — use extent center
        const extent = geom.getExtent()
        const center = [(extent[0] + extent[2]) / 2, (extent[1] + extent[3]) / 2]
        const coords = toLonLat(center)
        lon = coords[0]; lat = coords[1]
      }

      // Read platform@link to find the system this deployment belongs to
      const platformLink = raw.properties?.['platform@link'] || raw['platform@link']
      if (platformLink?.href) {
        const sysId = platformLink.href.replace(/\/+$/, '').split('/').pop()
        if (sysId) {
          if (!systemLocationCache[sysId]) {
            systemLocationCache[sysId] = { lat, lon, datastreamName: 'deployment geometry' }
          }
          primarySystemIds.add(sysId)
        }
      }
    }
  }
}

/**
 * Phase B: For each system in the location cache, fetch its subsystems and
 * propagate the parent's location to children.  This enables Part 2 resources
 * attached to subsystems to inherit the deployment/platform location.
 */
async function cacheSubsystemLocations(): Promise<void> {
  const parentIds = Object.keys(systemLocationCache)
  const promises = parentIds.map(async (parentId) => {
    const parentLoc = systemLocationCache[parentId]
    try {
      const res = await apiFetch(`/systems/${parentId}/subsystems?limit=200`, {
        headers: { 'Accept': 'application/geo+json' },
      })
      if (!res.ok || !res.data) return

      let items: any[] = []
      if (res.data.type === 'FeatureCollection' && Array.isArray(res.data.features)) {
        items = res.data.features
      } else if (Array.isArray(res.data.items)) {
        items = res.data.items
      }

      for (const sub of items) {
        const subId = sub.id || sub.properties?.uid
        if (!subId) continue

        // If the subsystem has its own geometry, prefer that
        const subGeom = extractGeometry(sub)
        if (subGeom && subGeom.type === 'Point') {
          const coords = subGeom.coordinates
          systemLocationCache[subId] = { lat: coords[1], lon: coords[0], datastreamName: 'subsystem geometry' }
        } else if (!systemLocationCache[subId]) {
          systemLocationCache[subId] = { ...parentLoc, datastreamName: `inherited from parent ${parentId}` }
        }
      }
    } catch { /* skip — server may not support subsystems endpoint */ }
  })
  await Promise.all(promises)
}

/**
 * Build a cache of system locations, combining multiple strategies:
 *   A. Static geometry from loaded Part 1 features (systems + deployments)
 *   B. Subsystem location propagation from parent systems
 *   C. Observation-derived locations from datastreams with geographic data
 *
 * Also populates locationDatastreamList for observation track/point rendering.
 */
async function buildSystemLocationCache(): Promise<void> {
  // Clear old cache
  for (const key of Object.keys(systemLocationCache)) delete systemLocationCache[key]
  primarySystemIds.clear()
  locationDatastreamList = []

  // --- Phase A: Static geometry from loaded features ---
  cacheLocationsFromLoadedFeatures()

  // --- Phase B: Propagate to subsystems ---
  await cacheSubsystemLocations()

  // --- Phase C: Observation-derived locations (broadened filter) ---
  try {
    // Fetch datastreams from the global endpoint
    const dsRes = await apiFetch('/datastreams?limit=200')
    let allDs: any[] = []
    if (dsRes.ok && dsRes.data) {
      allDs = dsRes.data.items || dsRes.data.features || dsRes.data || []
    }

    // Also fetch datastreams for each PRIMARY system in the location cache
    // (skip subsystems — the global fetch + primary fetches cover them,
    // avoiding O(N) API calls for every subsystem which causes lag)
    const seenDsIds = new Set(allDs.map((ds: any) => ds.id))
    const systemDsResults = await Promise.all(
      Array.from(primarySystemIds).map(async (sysId) => {
        try {
          const res = await apiFetch(`/systems/${sysId}/datastreams?limit=100`)
          if (!res.ok || !res.data) return [] as any[]
          return (res.data.items || res.data.features || []) as any[]
        } catch { return [] as any[] }
      })
    )
    for (const dsList of systemDsResults) {
      for (const ds of dsList) {
        if (ds.id && !seenDsIds.has(ds.id)) {
          seenDsIds.add(ds.id)
          allDs.push(ds)
        }
      }
    }

    // Filter to location-related datastreams (broadened to catch more patterns)
    const locationDs = allDs.filter(isLocationRelatedDatastream)

    // Deduplicate by system for the location cache (one lat/lon per system)
    // but keep ALL location datastreams for observation track rendering
    const bySystem: Record<string, any> = {}
    for (const ds of locationDs) {
      const sysId = extractSystemId(ds)
      if (!sysId) continue
      // Only use observation-derived location if no static location exists
      if (systemLocationCache[sysId]) continue
      const existing = bySystem[sysId]
      if (!existing || (ds.name || '').toLowerCase().includes('location')) {
        bySystem[sysId] = ds
      }
    }

    // Save LOB + position datastreams for observation rendering.
    // LOB datastreams → bearing lines; position datastreams → orbit markers.
    locationDatastreamList = locationDs
      .filter((ds: any) => {
        const sysId = extractSystemId(ds)
        if (!sysId) return false
        const nm = (ds.name || ds.outputName || '').toLowerCase()
        const pass = nm.includes('lob') || nm.includes('bearing')
          || nm.includes('position') || nm.includes('location')
          || nm.includes('surface') || nm.includes('weather')
          || nm.includes('metar') || nm.includes('nws') || nm.includes('awx')
          || nm.includes('aircraft') || nm.includes('adsb') || nm.includes('ads-b')
          || nm.includes('state vector') || nm.includes('flight')
          // ── Sources that were missing from the secondary filter ──
          || nm.includes('earthquake') || nm.includes('seismic') || nm.includes('quake')
          || nm.includes('ndbc') || nm.includes('buoy')
          || nm.includes('co-ops') || nm.includes('coops') || nm.includes('tide') || nm.includes('coastal')
          || nm.includes('discharge') || nm.includes('gage') || nm.includes('streamflow')
          || nm.includes('nims') || nm.includes('station image')
        return pass
      })
      .map((ds: any) => ({
        id: ds.id,
        name: ds.name || ds.outputName || 'Unknown',
        systemId: extractSystemId(ds),
      }))

    // NOTE: Previously this block added ALL datastreams for systems with
    // cached locations.  That caused up to N×500 observation fetches and
    // thousands of bearing-line features, which was the #1 source of map
    // lag.  Now we only keep the location-related datastreams above.
    // If you need geographic observations from non-location datastreams,
    // add them to isLocationRelatedDatastream() instead.

    // Fetch latest observation from each location datastream in parallel.
    // Uses resultTime='latest' via the builder — OSH's default ordering is
    // oldest-first, so a bare limit=1 returns the FIRST observation, not the
    // most recent.  The builder ensures spec-compliant query serialization.
    const promises = Object.entries(bySystem).map(async ([sysId, ds]) => {
      try {
        const obsUrl = getNestedListUrl('datastreams', ds.id, 'observations', {
          resultTime: 'latest',
          limit: 1,
        } as any)
        let obsRes = await apiFetch(obsUrl, {
          headers: { 'Accept': 'application/om+json' },
        })
        // Fallback: Go CSAPI server ignores resultTime=latest.  Retry with
        // plain limit=1 (Go returns newest-first by default).
        // Fallback: Go CSAPI server ignores resultTime=latest.  Retry with
        // plain limit=1 (Go returns newest-first by default).
        if (obsRes.ok && obsRes.data && !(obsRes.data.items?.[0] || obsRes.data[0])) {
          const fallbackUrl = getNestedListUrl('datastreams', ds.id, 'observations', {
            limit: 1,
          } as any)
          obsRes = await apiFetch(fallbackUrl, {
            headers: { 'Accept': 'application/om+json' },
          })
        }
        if (!obsRes.ok || !obsRes.data) return

        const obs = obsRes.data.items?.[0] || obsRes.data[0]
        if (!obs?.result) return

        const loc = extractLatLonFromResult(obs.result)
        if (!loc) return
        systemLocationCache[sysId] = {
          lat: loc.lat, lon: loc.lon, alt: loc.alt,
          datastreamName: ds.name,
          phenomenonTime: obs.phenomenonTime,
        }
      } catch { /* observation fetch failed for one DS — continue with others */ }
    })

    await Promise.all(promises)
  } catch { /* Phase C global DS fetch failed */ }
}

/**
 * Create an OL feature from a cached location, marking it as enriched.
 */
function createEnrichedFeature(
  item: any,
  resourceType: string,
  lat: number,
  lon: number,
  enrichmentSource: string,
): Feature {
  const olFeature = new Feature({
    geometry: new Point(fromLonLat([lon, lat])),
  })
  olFeature.setStyle(getStyle(resourceType, true, item))
  olFeature.set('resourceType', resourceType)
  olFeature.set('resourceId', extractId(item))
  olFeature.set('resourceName', extractName(item))
  olFeature.set('enriched', true)
  olFeature.set('enrichmentSource', enrichmentSource)
  olFeature.set('rawData', item)
  return olFeature
}

/**
 * Enrich resources that have null geometry using the system location cache.
 * - Systems: use their own location datastream observations
 * - Deployments: use the location of their deployed systems
 * - Sampling features: try to find the system they belong to
 */
async function enrichResourcesWithLocations(): Promise<void> {
  for (const key of Object.keys(enrichedCounts.value)) delete enrichedCounts.value[key]

  // Snapshot system IDs known BEFORE deployment enrichment so we can detect
  // newly-discovered systems (e.g. ISS linked via platform@link).
  const preEnrichSystemIds = new Set(primarySystemIds)

  // --- Enrich deployments FIRST (resolves all deployment geometry + updates systemLocationCache) ---
  await enrichDeployments()

  // --- Supplementary datastream discovery for deployment-linked systems ---
  // enrichDeployments() adds systems via platform@link to primarySystemIds.
  // Systems without static geometry (e.g. ISS) are only discoverable this way.
  // Fetch their datastreams now and append location-related ones to
  // locationDatastreamList so loadObservationLayers() can render them.
  const newSystemIds = Array.from(primarySystemIds).filter(id => !preEnrichSystemIds.has(id))
  if (newSystemIds.length > 0) {
    const existingDsIds = new Set(locationDatastreamList.map(d => d.id))
    const supplementaryResults = await Promise.all(
      newSystemIds.map(async (sysId) => {
        try {
          const res = await apiFetch(`/systems/${sysId}/datastreams?limit=100`)
          if (!res.ok || !res.data) return [] as any[]
          return (res.data.items || res.data.features || []) as any[]
        } catch { return [] as any[] }
      })
    )
    for (const dsList of supplementaryResults) {
      for (const ds of dsList) {
        if (!ds.id || existingDsIds.has(ds.id)) continue
        if (!isLocationRelatedDatastream(ds)) continue
        const sysId = extractSystemId(ds)
        if (!sysId) continue
        const nm = (ds.name || ds.outputName || '').toLowerCase()
        if (nm.includes('lob') || nm.includes('bearing')
          || nm.includes('position') || nm.includes('location')
          || nm.includes('aircraft') || nm.includes('adsb') || nm.includes('ads-b')
          || nm.includes('state vector') || nm.includes('flight')
          || nm.includes('earthquake') || nm.includes('seismic') || nm.includes('quake')
          || nm.includes('ndbc') || nm.includes('buoy')
          || nm.includes('co-ops') || nm.includes('coops') || nm.includes('tide') || nm.includes('coastal')
          || nm.includes('discharge') || nm.includes('gage') || nm.includes('streamflow')
          || nm.includes('nims') || nm.includes('station image')) {
          locationDatastreamList.push({
            id: ds.id,
            name: ds.name || ds.outputName || 'Unknown',
            systemId: sysId,
          })
          existingDsIds.add(ds.id)
        }
        // Also populate systemLocationCache if not already set (for latest obs fetch)
        if (!systemLocationCache[sysId]) {
          // Will be resolved by loadObservationLayers via observation data
        }
      }
    }
  }

  // --- Enrich systems (uses updated cache with deployment locations) ---
  await enrichSystems()
  // --- Enrich sampling features ---
  await enrichSamplingFeatures()
}

async function enrichSystems(): Promise<void> {
  const source = vectorSources['systems']
  if (!source) return

  // First: reposition any existing system features whose deployment has a newer location.
  // This covers systems that have native geometry but are linked to a moved deployment.
  for (const feature of source.getFeatures()) {
    const sysId = feature.get('resourceId')
    if (!sysId) continue
    const cached = systemLocationCache[sysId]
    if (!cached || cached.datastreamName !== 'deployment geometry') continue
    // Update the feature's geometry to the deployment location
    feature.setGeometry(new Point(fromLonLat([cached.lon, cached.lat])))
    feature.set('enriched', true)
    feature.set('enrichmentSource', 'Repositioned to linked deployment location')
  }

  // Then: add features for systems that have no geometry on the map yet.
  // Re-fetch the raw items list to check which have null geometry.
  try {
    const url = getListUrl('systems', buildQueryOptions())
    const res = await apiFetch(url, {
      headers: { 'Accept': 'application/geo+json' },
    })
    if (!res.ok || !res.data) return

    let items: any[] = []
    if (res.data.type === 'FeatureCollection' && Array.isArray(res.data.features)) {
      items = res.data.features
    } else if (Array.isArray(res.data.items)) {
      items = res.data.items
    }

    // Collect IDs already on map to avoid duplicates
    const existingIds = new Set(source.getFeatures().map(f => f.get('resourceId')))

    const batch: Feature[] = []
    for (const item of items) {
      const sysId = extractId(item)
      // Skip if already on map (from loadResourceType or repositioned above)
      if (existingIds.has(sysId)) continue

      const loc = systemLocationCache[sysId]
      if (!loc) continue

      // When bbox is active, skip if enriched location falls outside
      if (bboxFilter.value) {
        const [minX, minY, maxX, maxY] = bboxFilter.value
        if (loc.lon < minX || loc.lon > maxX || loc.lat < minY || loc.lat > maxY) continue
      }

      batch.push(createEnrichedFeature(
        item, 'systems', loc.lat, loc.lon,
        `Latest observation from ${loc.datastreamName || 'location datastream'} at ${loc.phenomenonTime || 'unknown time'}`
      ))
    }
    if (batch.length) source.addFeatures(batch)
    enrichedCounts.value['systems'] = batch.length
    featureCounts.value['systems'] = (featureCounts.value['systems'] || 0) + batch.length
  } catch { /* enrichSystems failed */ }
}

async function enrichDeployments(): Promise<void> {
  const source = vectorSources['deployments']
  if (!source) return

  try {
    // Fetch WITHOUT bbox — top-level deployments often have no geometry;
    // subdeployments and deployed-system locations are resolved below,
    // then bbox is applied client-side.
    const url = getListUrl('deployments', buildQueryOptionsNoBbox())
    const res = await apiFetch(url, {
      headers: { 'Accept': 'application/geo+json' },
    })
    if (!res.ok || !res.data) return

    let items: any[] = []
    if (res.data.type === 'FeatureCollection' && Array.isArray(res.data.features)) {
      items = res.data.features
    } else if (Array.isArray(res.data.items)) {
      items = res.data.items
    }

    let enriched = 0

    // ── 1. Recursively fetch the full deployment hierarchy ──────────
    const seenIds = new Set(source.getFeatures().map(f => f.get('resourceId')))
    items.forEach(it => seenIds.add(extractId(it)))

    const childrenMap: Record<string, string[]> = {}   // parentId → [childId, ...]
    const parentMap: Record<string, string> = {}       // childId → parentId

    async function fetchSubdeployments(parentId: string, depth = 0): Promise<any[]> {
      if (depth > 8) return []
      try {
        const subRes = await apiFetch(`/deployments/${parentId}/subdeployments?limit=50`, {
          headers: { 'Accept': 'application/geo+json' },
        })
        if (!subRes.ok || !subRes.data) return []
        let subs: any[] = []
        if (subRes.data.type === 'FeatureCollection' && Array.isArray(subRes.data.features)) {
          subs = subRes.data.features
        } else if (Array.isArray(subRes.data.items)) {
          subs = subRes.data.items
        }
        const childIds: string[] = []
        const deeper: any[] = []
        for (const sub of subs) {
          const subId = extractId(sub)
          if (subId) {
            childIds.push(subId)
            parentMap[subId] = parentId
            if (!seenIds.has(subId)) {
              seenIds.add(subId)
              deeper.push(...await fetchSubdeployments(subId, depth + 1))
            }
          }
        }
        if (childIds.length > 0) childrenMap[parentId] = childIds
        return [...subs, ...deeper]
      } catch { return [] }
    }

    const allSubs: any[] = []
    await Promise.all(items.map(async (item) => {
      const parentId = extractId(item)
      if (parentId) {
        const subs = await fetchSubdeployments(parentId)
        allSubs.push(...subs)
      }
    }))

    const allItems = [...items, ...allSubs]
    const itemById: Record<string, any> = {}
    for (const it of allItems) {
      const id = extractId(it)
      if (id) itemById[id] = it
    }

    // Surface hierarchy maps for deployed-system card composition
    deploymentParentMap = { ...parentMap }
    deploymentItemById = { ...itemById }

    // ── 2. Build system UID → location lookup ──────────────────────
    // systemLocationCache is keyed by system ID, but deployments reference
    // systems by UID (deployedSystemUIDs). Build a reverse map.
    const uidToLocation: Record<string, { lon: number; lat: number }> = {}
    // Fetch all systems to build UID map
    try {
      const sysRes = await apiFetch('/systems?limit=200', {
        headers: { 'Accept': 'application/geo+json' },
      })
      if (sysRes.ok && sysRes.data) {
        const sysList = sysRes.data.features || sysRes.data.items || []
        for (const sys of sysList) {
          const sysId = extractId(sys)
          const uid = sys.properties?.uid || sys.uid || ''
          const loc = systemLocationCache[sysId]
          if (uid && loc) {
            uidToLocation[uid] = { lon: loc.lon, lat: loc.lat }
          }
          // Also try system's native geometry if not in location cache
          if (uid && !uidToLocation[uid]) {
            const geom = extractGeometry(sys)
            if (geom) {
              const pts = centroidFromGeometry(geom)
              if (pts) uidToLocation[uid] = pts
            }
          }
        }
      }
    } catch { /* proceed without UID map */ }

    // ── 3. Helper functions ────────────────────────────────────────

    /** Extract a single [lon, lat] centroid from any GeoJSON geometry */
    function centroidFromGeometry(geom: { type: string; coordinates: any }): { lon: number; lat: number } | null {
      if (geom.type === 'Point') {
        return { lon: geom.coordinates[0], lat: geom.coordinates[1] }
      }
      if (geom.type === 'LineString') {
        const coords: number[][] = geom.coordinates
        if (coords.length === 0) return null
        const avg = coords.reduce((a, c) => [a[0] + c[0], a[1] + c[1]], [0, 0])
        return { lon: avg[0] / coords.length, lat: avg[1] / coords.length }
      }
      if (geom.type === 'Polygon') {
        const ring: number[][] = geom.coordinates[0] || []
        if (ring.length === 0) return null
        const avg = ring.reduce((a, c) => [a[0] + c[0], a[1] + c[1]], [0, 0])
        return { lon: avg[0] / ring.length, lat: avg[1] / ring.length }
      }
      return null
    }

    /** Get the deployed system locations for a deployment item */
    function getDeployedSystemLocations(item: any): Array<{ lon: number; lat: number }> {
      const locs: Array<{ lon: number; lat: number }> = []
      const props = item.properties || item || {}

      // deployedSystems@link hrefs
      const dsLinks = props['deployedSystems@link'] || []
      if (Array.isArray(dsLinks)) {
        for (const dsl of dsLinks) {
          const href = dsl.system?.href || dsl.href || ''
          const sysId = href.replace(/\/+$/, '').split('/').pop()
          if (sysId) {
            const loc = systemLocationCache[sysId]
            if (loc) locs.push({ lon: loc.lon, lat: loc.lat })
          }
        }
      }

      // platform@link
      if (locs.length === 0) {
        const plat = props['platform@link']
        if (plat?.href) {
          const sysId = plat.href.replace(/\/+$/, '').split('/').pop()
          if (sysId) {
            const loc = systemLocationCache[sysId]
            if (loc) locs.push({ lon: loc.lon, lat: loc.lat })
          }
        }
      }

      // deployedSystemUIDs → use uidToLocation map
      if (locs.length === 0) {
        const uidStr = props['deployedSystemUIDs']
        if (typeof uidStr === 'string' && uidStr.length > 0) {
          for (const uid of uidStr.split(',').map(s => s.trim()).filter(Boolean)) {
            const loc = uidToLocation[uid]
            if (loc) locs.push(loc)
          }
        }
      }

      return locs
    }

    // ── 4. Bottom-up geometry resolution ───────────────────────────
    // Each deployment's representative centroid is resolved ONCE and cached.
    // Order: leaf deployments first, then walk up to parents.
    //
    // Rules:
    //   a) Native geometry exists → centroid of that geometry
    //   b) Has subdeployments or deployed systems → centroid of all those points
    //   c) No physical anchor → no geometry (organizational containers are not drawn)

    const resolvedCentroid: Record<string, { lon: number; lat: number }> = {}

    /** Resolve the representative centroid for a deployment (recursive, memoized) */
    function resolveCentroid(depId: string, visited = new Set<string>()): { lon: number; lat: number } | null {
      if (resolvedCentroid[depId]) return resolvedCentroid[depId]
      if (visited.has(depId)) return null
      visited.add(depId)

      const item = itemById[depId]
      if (!item) return null

      // a) Native geometry → use its centroid
      const nativeGeom = extractGeometry(item)
      if (nativeGeom) {
        const c = centroidFromGeometry(nativeGeom)
        if (c) { resolvedCentroid[depId] = c; return c }
      }

      // Collect points from direct subdeployments + deployed systems
      const points: Array<{ lon: number; lat: number }> = []

      // Direct subdeployment centroids
      const childIds = childrenMap[depId] || []
      for (const cid of childIds) {
        const cc = resolveCentroid(cid, new Set(visited))
        if (cc) points.push(cc)
      }

      // Deployed system locations
      points.push(...getDeployedSystemLocations(item))

      // b) Has points → compute centroid from them
      if (points.length > 0) {
        const avg = points.reduce((a, p) => ({ lon: a.lon + p.lon, lat: a.lat + p.lat }), { lon: 0, lat: 0 })
        const c = { lon: avg.lon / points.length, lat: avg.lat / points.length }
        resolvedCentroid[depId] = c
        return c
      }

      // c) No physical anchor → no geometry (organizational containers are not drawn)
      return null
    }

    // Resolve all centroids
    for (const item of allItems) {
      const id = extractId(item)
      if (id) resolveCentroid(id)
    }

    // ── 5. Build map features ──────────────────────────────────────
    const isInsideBbox = (lon: number, lat: number): boolean => {
      if (!bboxFilter.value) return true
      const [minX, minY, maxX, maxY] = bboxFilter.value
      return lon >= minX && lon <= maxX && lat >= minY && lat <= maxY
    }

    // First pass: add subdeployments with native geometry AND a system link to the map
    const existingIds = new Set(source.getFeatures().map(f => f.get('resourceId')))
    const nativeGeoBatch: Feature[] = []
    for (const sub of allSubs) {
      const subId = extractId(sub)
      if (existingIds.has(subId)) continue
      const geom = extractGeometry(sub)
      if (!geom) continue
      // Only draw if it has platform@link (physical emplacement).
      // deployedSystemUIDs and deployedSystems@link are organizational, not physical.
      const subProps = sub.properties || sub || {}
      if (!subProps['platform@link']?.href) continue
      const c = centroidFromGeometry(geom)
      if (c && bboxFilter.value && !isInsideBbox(c.lon, c.lat)) continue
      const feature = createOlFeature(sub, 'deployments')
      if (feature) {
        nativeGeoBatch.push(feature)
        existingIds.add(subId)
      }
    }
    if (nativeGeoBatch.length) source.addFeatures(nativeGeoBatch)
    featureCounts.value['deployments'] = (featureCounts.value['deployments'] || 0) + nativeGeoBatch.length

    // Second pass: derive geometry for deployments that have a direct system link
    // (platform@link, deployedSystems@link, or deployedSystemUIDs).
    // Pure organizational containers (no native geometry, no system link) are NOT drawn.
    const derivedBatch: Feature[] = []
    for (const item of allItems) {
      if (extractGeometry(item)) continue
      const depId = extractId(item)
      if (!depId) continue
      if (existingIds.has(depId)) continue

      // Only draw deployments with platform@link (physical emplacement)
      const props = item.properties || item || {}
      if (!props['platform@link']?.href) continue

      // Use the resolved centroid (from deployed system location)
      const centroid = resolvedCentroid[depId]
      if (!centroid) continue

      // Bbox filter
      if (bboxFilter.value && !isInsideBbox(centroid.lon, centroid.lat)) continue

      const olGeom = new Point(fromLonLat([centroid.lon, centroid.lat]))
      const feature = new Feature({ geometry: olGeom })
      feature.setStyle(getStyle('deployments', false, item))
      feature.set('resourceType', 'deployments')
      feature.set('resourceId', depId)
      feature.set('resourceName', extractName(item))
      feature.set('rawData', item)
      feature.set('enrichedFrom', 'Derived point from linked system location')
      derivedBatch.push(feature)
      existingIds.add(depId)
    }
    if (derivedBatch.length) source.addFeatures(derivedBatch)

    enrichedCounts.value['deployments'] = derivedBatch.length
    featureCounts.value['deployments'] = (featureCounts.value['deployments'] || 0) + derivedBatch.length

    // ── 6. Update systemLocationCache from resolved deployment centroids ───
    // Deployments with platform@link map to a specific system.
    // Now that all deployment geometry is resolved, back-fill the cache
    // so enrichSystems() places systems at their deployment's location.
    for (const item of allItems) {
      const depId = extractId(item)
      const centroid = resolvedCentroid[depId]
      if (!centroid) continue
      const plat = (item.properties || item)['platform@link']
      if (plat?.href) {
        const sysId = plat.href.replace(/\/+$/, '').split('/').pop()
        if (sysId) {
          // Always overwrite — deployment location is authoritative for deployed systems
          systemLocationCache[sysId] = { lat: centroid.lat, lon: centroid.lon, datastreamName: 'deployment geometry' }
          primarySystemIds.add(sysId)
        }
      }
    }
  } catch { /* skip */ }
}

/**
 * Discover detection-range datastreams from the server and populate
 * detectionRangeConfigs keyed by system UID.
 *
 * For each primary system, looks for a datastream whose outputName ends with
 * "_detection_capabilities", reads the latest observation, and extracts
 * min/nominal/max range values. All data comes from the CSAPI API — nothing
 * is hardcoded.
 */
async function fetchDetectionRangeConfigs(): Promise<void> {
  // Clear any stale entries
  for (const key of Object.keys(detectionRangeConfigs)) delete detectionRangeConfigs[key]

  const fetches = Array.from(primarySystemIds).map(async (sysId) => {
    try {
      // 1. Find detection_capabilities datastream
      const dsUrl = getNestedListUrl('systems', sysId, 'datastreams', { limit: 50 })
      const dsRes = await apiFetch(dsUrl)
      if (!dsRes.ok || !dsRes.data) return
      const dsList = dsRes.data.items || dsRes.data.features || []
      const capDs = dsList.find((ds: any) =>
        ds.outputName?.endsWith('_detection_capabilities')
      )
      if (!capDs) return

      // 2. Read observations and find the one with detection range data.
      //    OSH has a scope-leak bug where datastream-scoped queries return
      //    observations from sibling datastreams. Use sortBy=resultTime desc
      //    so the most recent observations (including the genuine detection
      //    capabilities obs) come first, allowing a much smaller limit.
      const obsUrl = getNestedListUrl('datastreams', capDs.id, 'observations', {
        sortBy: 'resultTime',
        sortOrder: 'desc',
        limit: 50,
      } as any)
      const obsRes = await apiFetch(obsUrl)
      if (!obsRes.ok || !obsRes.data) return
      const items = obsRes.data.items || []
      if (!items.length) return
      const rangeObs = items.find((o: any) => o.result && typeof o.result.minRange_m === 'number')
      if (!rangeObs) return
      const result = rangeObs.result

      // 3. Get system UID from the system feature
      const sysRes = await apiFetch(`/systems/${sysId}`)
      const uid = sysRes.data?.properties?.uid
      if (!uid) return

      // 4. Build config from observation data
      const rings: DetectionRing[] = []
      if (typeof result.minRange_m === 'number')     rings.push({ label: 'min', radius_m: result.minRange_m })
      if (typeof result.nominalRange_m === 'number') rings.push({ label: 'nominal', radius_m: result.nominalRange_m })
      if (typeof result.maxRange_m === 'number')     rings.push({ label: 'max', radius_m: result.maxRange_m })
      if (!rings.length) return

      detectionRangeConfigs[uid] = {
        shape: result.shape || 'circular',
        rings,
        confidence: result.confidence,
        basis: result.basis,
        phenomenonTime: items[0].phenomenonTime,
      }
    } catch { /* skip systems without detection capabilities */ }
  })
  await Promise.all(fetches)

  // Fallback: apply hardcoded detection range for ODAS nodes not found via API
  // (scope-leak can bury the real observation beyond scan limits)
  for (const uid of ODAS_UIDS) {
    if (!detectionRangeConfigs[uid]) {
      detectionRangeConfigs[uid] = { ...DETECTION_RANGE_FALLBACK }
    }
  }
}

/**
 * Build detection range ring features for deployments that link to systems
 * with detection range configurations discovered from the server.
 *
 * For each deployment emplacement with platform@link, resolve the linked
 * system's UID, look up the detection range config, and draw geodesic
 * circle polygons at the deployment's location.
 */
function buildDetectionRanges(): void {
  const source = vectorSources['detectionRanges']
  if (!source) return
  source.clear()

  const deploySource = vectorSources['deployments']
  if (!deploySource) return

  // Ring styles: solid strokes with visible fills
  // Stroke widths and fill alphas are deliberately high to remain visible on
  // retina / high-DPI mobile screens (iPhone 2-3× pixel ratio can make thin
  // strokes sub-pixel and low-alpha fills invisible).
  const ringStyles: Record<string, { dash: number[]; fillAlpha: number; strokeWidth: number }> = {
    min:     { dash: [4, 4],  fillAlpha: 0.38, strokeWidth: 3 },
    nominal: { dash: [8, 6],  fillAlpha: 0.25, strokeWidth: 2.5 },
    max:     { dash: [12, 8], fillAlpha: 0.15, strokeWidth: 2 },
  }
  const ringColor = [96, 165, 250] // #60a5fa — friendly blue

  const batch: Feature[] = []

  for (const depFeature of deploySource.getFeatures()) {
    const rawData = depFeature.get('rawData')
    if (!rawData) continue

    const props = rawData.properties || rawData || {}
    const plat = props['platform@link']
    if (!plat?.uid) continue

    const config = detectionRangeConfigs[plat.uid]
    if (!config || config.shape !== 'circular') continue

    // Get deployment location in EPSG:4326
    const geom = depFeature.getGeometry()
    if (!geom) continue
    const coords = (geom as Point).getCoordinates()
    const lonLat = toLonLat(coords)
    const lon = lonLat[0]!, lat = lonLat[1]!

    // Create a feature for each ring
    for (const ring of config.rings) {
      // circularPolygon returns a Polygon in EPSG:4326
      const circle4326 = circularPolygon([lon, lat], ring.radius_m, 64)
      // Transform to map projection (EPSG:3857)
      circle4326.transform('EPSG:4326', 'EPSG:3857')

      const feature = new Feature({ geometry: circle4326 })
      const styleDef = ringStyles[ring.label] ?? ringStyles['max']!
      feature.setStyle(new Style({
        stroke: new Stroke({
          color: `rgba(${ringColor.join(',')}, 0.8)`,
          width: styleDef.strokeWidth,
          lineDash: styleDef.dash,
        }),
        fill: new Fill({
          color: `rgba(${ringColor.join(',')}, ${styleDef.fillAlpha})`,
        }),
      }))
      feature.set('resourceType', 'detectionRanges')
      feature.set('resourceId', `${extractId(rawData)}-range-${ring.label}`)
      feature.set('resourceName', `${extractName(rawData)} — ${ring.label} (${ring.radius_m}m)`)
      feature.set('rawData', {
        properties: {
          name: `${extractName(rawData)} — ${ring.label} detection range`,
          radius_m: ring.radius_m,
          confidence: config.confidence,
          basis: config.basis,
          phenomenonTime: config.phenomenonTime,
          systemUid: plat.uid,
        }
      })

      // Add range label at the top of the circle (north)
      const labelCoord = fromLonLat([lon, lat + (ring.radius_m / 111320)]) // rough meter-to-degree
      const labelFeature = new Feature({ geometry: new Point(labelCoord) })
      labelFeature.setStyle(new Style({
        text: new OlText({
          text: `${ring.label.toUpperCase()} ${ring.radius_m}m`,
          font: '11px sans-serif',
          fill: new Fill({ color: `rgba(${ringColor.join(',')}, 0.9)` }),
          stroke: new Stroke({ color: '#fff', width: 2.5 }),
          offsetY: -6,
        }),
      }))
      labelFeature.set('resourceType', 'detectionRanges')

      batch.push(feature, labelFeature)
    }
  }

  if (batch.length) source.addFeatures(batch)
  featureCounts.value['detectionRanges'] = batch.length / 2 // each ring = polygon + label
}

// ── Location Estimate (Localizer) Layer ────────────────────────────

/** Persisted fix markers that stay on the map across poll cycles */
const persistedFixMarkers: Feature[] = []
/** Track observation IDs already rendered to avoid duplicates */
const seenFixObsIds = new Set<string>()
/** Max number of persisted fix markers to keep on the map */
const MAX_PERSISTED_FIXES = 50

/**
 * Discover the localizer datastream by searching for the fusion system's
 * "location_estimate" output.  Fully dynamic — zero hardcoded IDs.
 */
async function discoverLocalizerDatastream(): Promise<void> {
  localizerDatastreamId = null
  try {
    // Search all datastreams for the localizer output name
    const dsRes = await apiFetch('/datastreams?limit=200')
    if (!dsRes.ok || !dsRes.data) return
    const dsList = dsRes.data.items || dsRes.data.features || []
    const locDs = dsList.find((ds: any) => {
      const outputName = (ds.outputName || ds.name || '').toLowerCase()
      return outputName.includes('location_estimate')
    })
    if (locDs) {
      localizerDatastreamId = locDs.id
    }
  } catch { /* skip — localizer may not be registered */ }
}

/**
 * Location estimate styles — dynamic based on fix age.
 * Fresh fixes (< 15s) get full opacity gold; aging fixes progressively
 * fade to indicate staleness.  Hard cutoff at 60s.
 */
function getLocEstimateMarkerStyle(ageS: number): Style {
  // Opacity: 100% for < 15s, linear fade to 35% at 60s
  const opacity = ageS <= 15 ? 1.0 : Math.max(0.35, 1.0 - (ageS - 15) / (60 - 15) * 0.65)
  return new Style({
    image: new CircleStyle({
      radius: 8,
      fill: new Fill({ color: `rgba(250, 204, 21, ${opacity})` }),
      stroke: new Stroke({ color: `rgba(180, 83, 9, ${opacity})`, width: 2.5 }),
    }),
    text: new OlText({
      text: '⊕',
      font: 'bold 14px sans-serif',
      fill: new Fill({ color: `rgba(146, 64, 14, ${opacity})` }),
      offsetY: 1,
    }),
  })
}

/**
 * Fetch the latest location estimate from the localizer datastream and
 * render a position marker + CEP50 uncertainty circle on the map.
 */
async function loadLocationEstimates(): Promise<void> {
  const source = vectorSources['locationEstimates']
  if (!source) return
  // Don't clear yet — wait until replacement data is ready to avoid blink

  if (!localizerDatastreamId) return

  try {
    // Helper: check if an observation is a genuine localizer fix
    const isGenuineFix = (o: any) =>
      o?.result && typeof o.result.estimatedLat === 'number' && typeof o.result.estimatedLon === 'number'

    // Step 1: Try resultTime=latest (fast path — one observation).
    const latestUrl = getNestedListUrl('datastreams', localizerDatastreamId, 'observations', {
      resultTime: 'latest',
      limit: 1,
    } as any)
    let obsRes = await apiFetch(
      latestUrl,
      { headers: { 'Accept': 'application/om+json' } },
    )
    // Fallback: Go CSAPI server ignores resultTime=latest
    if (obsRes.ok && obsRes.data && !(obsRes.data.items?.length)) {
      const fallbackUrl = getNestedListUrl('datastreams', localizerDatastreamId, 'observations', {
        limit: 1,
      } as any)
      obsRes = await apiFetch(
        fallbackUrl,
        { headers: { 'Accept': 'application/om+json' } },
      )
    }
    if (!obsRes.ok || !obsRes.data) return
    let items = obsRes.data.items || []
    let obs = items.find(isGenuineFix)

    // Step 2 (scope-leak fallback): resultTime=latest returned a leaked LOB
    // instead of a genuine localizer fix.  Use the leaked observation's
    // resultTime to build a 5-minute time window and scan for genuine fixes.
    if (!obs && items.length) {
      const leaked = items[0]
      const rt = leaked.resultTime || leaked.phenomenonTime
      if (rt) {
        const endMs = new Date(rt).getTime()
        const fallbackUrl = getNestedListUrl('datastreams', localizerDatastreamId, 'observations', {
          limit: 100,
          resultTime: { start: new Date(endMs - 300_000), end: new Date(endMs + 1_000) },
          sortBy: 'resultTime',
          sortOrder: 'desc',
        } as any)
        const fallbackRes = await apiFetch(
          fallbackUrl,
          { headers: { 'Accept': 'application/om+json' } },
        )
        if (fallbackRes.ok && fallbackRes.data) {
          const fbItems = fallbackRes.data.items || []
          // Pick the most recent genuine fix (try in order — desc sort puts newest first)
          obs = fbItems.find(isGenuineFix) || [...fbItems].reverse().find(isGenuineFix)
        }
      }
    }

    if (!obs) return

    const result = obs.result
    const lat = result.estimatedLat
    const lon = result.estimatedLon
    const cep50 = result.cep50_m
    if (typeof lat !== 'number' || typeof lon !== 'number') return

    // Staleness check: in live mode, skip if observation is older than 60 seconds.
    // Between 15–60s the marker progressively fades to indicate aging.
    const obsTime = result.timestamp ? result.timestamp * 1000 : new Date(obs.phenomenonTime || obs.resultTime).getTime()
    const ageS = (Date.now() - obsTime) / 1000
    if (liveMode.value && ageS > 60) {
      // Stale — clear ephemeral features but keep persisted markers
      clearEphemeralLocFeatures(source)
      return
    }

    const batch: Feature[] = []

    // Compute age-based opacity for progressive fade
    const fadeOpacity = liveMode.value
      ? (ageS <= 15 ? 1.0 : Math.max(0.35, 1.0 - (ageS - 15) / (60 - 15) * 0.65))
      : 1.0

    // 1. CEP50 uncertainty circle (draw first so marker is on top)
    if (typeof cep50 === 'number' && cep50 > 0) {
      const circle4326 = circularPolygon([lon, lat], cep50, 64)
      circle4326.transform('EPSG:4326', 'EPSG:3857')
      const circleFeature = new Feature({ geometry: circle4326 })
      circleFeature.setStyle(new Style({
        stroke: new Stroke({ color: `rgba(250, 204, 21, ${0.9 * fadeOpacity})`, width: 2, lineDash: [6, 4] }),
        fill: new Fill({ color: `rgba(250, 204, 21, ${0.15 * fadeOpacity})` }),
      }))
      circleFeature.set('resourceType', 'locationEstimates')
      circleFeature.set('resourceId', `loc-est-cep50`)
      circleFeature.set('resourceName', `CEP50: ${cep50.toFixed(1)}m`)
      batch.push(circleFeature)
    }

    // 2. Position marker (dynamically styled based on age in live mode)
    const obsId = obs.id || `loc-est-${obsTime}`
    const isNewFix = !seenFixObsIds.has(obsId)
    const markerFeature = new Feature({
      geometry: new Point(fromLonLat([lon, lat])),
    })
    markerFeature.setStyle(liveMode.value ? getLocEstimateMarkerStyle(ageS) : getLocEstimateMarkerStyle(0))
    markerFeature.set('resourceType', 'locationEstimates')
    markerFeature.set('resourceId', obsId)
    markerFeature.set('resourceName', `Fix: ${lat.toFixed(5)}°N, ${lon.toFixed(5)}°W`)
    markerFeature.set('isPersistedFix', true)
    markerFeature.set('rawData', {
      observationId: obs.id,
      datastreamId: localizerDatastreamId,
      phenomenonTime: obs.phenomenonTime,
      estimatedLat: lat,
      estimatedLon: lon,
      cep50_m: cep50,
      classification: result.classification,
      numContributingLobs: result.numContributingLobs,
      contributingSensors: result.contributingSensors,
      residual_m: result.residual_m,
      trackId: result.trackId,
      ageSeconds: ageS,
    })
    batch.push(markerFeature)

    // 3. Label below marker — includes fix age in live mode
    const ageLabel = liveMode.value
      ? (ageS < 10 ? '' : ` · ${Math.round(ageS)}s ago`)
      : ''
    const labelFeature = new Feature({
      geometry: new Point(fromLonLat([lon, lat])),
    })
    labelFeature.setStyle(new Style({
      text: new OlText({
        text: `${result.classification || 'UNK'} — ${result.numContributingLobs || '?'} LOBs${ageLabel}`,
        font: '11px sans-serif',
        fill: new Fill({ color: `rgba(250, 204, 21, ${fadeOpacity})` }),
        stroke: new Stroke({ color: '#000', width: 3 }),
        offsetY: 18,
      }),
    }))
    labelFeature.set('resourceType', 'locationEstimates')
    batch.push(labelFeature)

    // 4. Render contributing LOBs from the localizer observation.
    //    In live mode, these are the EXACT bearing lines used for this fix —
    //    zero temporal mismatch.  The bearing lines source is shared with
    //    loadObservationLayers() which skips LOBs in live mode to avoid
    //    duplication.
    const bearingSource = vectorSources['bearingLines']
    const lobBatch: Feature[] = []
    if (liveMode.value && bearingSource && result.contributingLobsJson) {
      try {
        const lobs: Array<{ sensorName: string; sensorLat: number; sensorLon: number; bearingTrue: number; bearingStdDev: number }> =
          JSON.parse(result.contributingLobsJson)
        for (const lob of lobs) {
          if (typeof lob.sensorLat !== 'number' || typeof lob.sensorLon !== 'number' || typeof lob.bearingTrue !== 'number') continue
          const ep = computeBearingEndpoint(lob.sensorLat, lob.sensorLon, lob.bearingTrue, BEARING_LINE_LENGTH_M)
          const feature = new Feature({
            geometry: new LineString([
              fromLonLat([lob.sensorLon, lob.sensorLat]),
              fromLonLat([ep.lon, ep.lat]),
            ]),
          })
          // Style with same fade as the location estimate marker
          feature.setStyle(getCachedBearingLineStyle(fadeOpacity))
          feature.set('resourceType', 'bearingLines')
          feature.set('resourceId', `loc-est-lob-${lob.sensorName}`)
          feature.set('resourceName', `${lob.sensorName} — ${lob.bearingTrue.toFixed(1)}°`)
          feature.set('rawData', {
            sensorName: lob.sensorName,
            sensorLat: lob.sensorLat,
            sensorLon: lob.sensorLon,
            bearingTrue: lob.bearingTrue,
            bearingStdDev: lob.bearingStdDev,
            source: 'localizer',
          })
          lobBatch.push(feature)
        }
      } catch { /* malformed JSON — skip LOB rendering */ }
    }

    // ── Persist fix markers in live mode ──
    // In live mode, accumulate position markers across poll cycles.
    // Ephemeral features (CEP circle, label) are replaced each cycle;
    // persisted fix markers stay on the map until cap is reached.
    if (liveMode.value && isNewFix) {
      seenFixObsIds.add(obsId)
      // Dim all existing persisted markers to 35% opacity
      for (const oldMarker of persistedFixMarkers) {
        oldMarker.setStyle(getLocEstimateMarkerStyle(999)) // max age → 35% opacity
      }
      // Add new marker to persisted set
      persistedFixMarkers.push(markerFeature)
      // Cap: drop oldest if over limit
      while (persistedFixMarkers.length > MAX_PERSISTED_FIXES) {
        const evicted = persistedFixMarkers.shift()!
        source.removeFeature(evicted)
        const evictedId = evicted.get('resourceId')
        if (evictedId) seenFixObsIds.delete(evictedId)
      }
    }

    // Clear ephemeral features (CEP, label) but keep persisted markers
    clearEphemeralLocFeatures(source)

    // Add ephemeral features + current marker
    source.addFeatures(batch)
    featureCounts.value['locationEstimates'] = persistedFixMarkers.length || 1

    // Swap bearing lines from localizer data (live mode only)
    if (liveMode.value && bearingSource && lobBatch.length > 0) {
      bearingSource.clear()
      bearingSource.addFeatures(lobBatch)
      featureCounts.value['bearingLines'] = lobBatch.length
    }
  } catch {
    // No data available — clear ephemeral features, keep persisted markers
    clearEphemeralLocFeatures(source)
  }
}

/**
 * Remove ephemeral location-estimate features (CEP circle, label) from the
 * source while preserving persisted fix markers.  In non-live mode or when
 * there are no persisted markers, falls back to a full clear.
 */
function clearEphemeralLocFeatures(source: VectorSource | undefined) {
  if (!source) return
  if (!liveMode.value || persistedFixMarkers.length === 0) {
    source.clear()
    featureCounts.value['locationEstimates'] = 0
    return
  }
  // Remove only features that are NOT persisted fix markers
  const toRemove = source.getFeatures().filter(f => !f.get('isPersistedFix'))
  for (const f of toRemove) source.removeFeature(f)
}

// ── SENREP DS ID (Monitoring Team A sensor reports) ────────────────
// Updated 2026-03-11 after H2 MVStore rebuild (was 044g → now NWS KDAY)
const SENREP_DS_ID = '04g0'

/**
 * SENREP marker style — red diamond
 */
const senrepMarkerStyle = new Style({
  image: new CircleStyle({
    radius: 9,
    fill: new Fill({ color: '#ef4444' }),
    stroke: new Stroke({ color: '#ffffff', width: 2 }),
    rotation: Math.PI / 4,
  }),
  text: new OlText({
    text: '◆',
    font: 'bold 16px sans-serif',
    fill: new Fill({ color: '#ef4444' }),
    stroke: new Stroke({ color: '#fff', width: 3 }),
    offsetY: 0,
  }),
})

/**
 * Fetch SENREP observations from DS 044g and render red diamond markers.
 */
async function loadSenrepMarkers(): Promise<void> {
  const source = vectorSources['senrepMarkers']
  if (!source) return
  // Don't clear yet — wait until replacement data is ready to avoid blink

  try {
    const senrepUrl = getNestedListUrl('datastreams', SENREP_DS_ID, 'observations', { limit: 50 } as any)
    const obsRes = await apiFetch(
      senrepUrl,
      { headers: { 'Accept': 'application/om+json' } },
    )
    if (!obsRes.ok || !obsRes.data) return
    // Identify SENREP observations by their doctrinal fields (etaLat/etaLon/title)
    // rather than datastream@id which OSH mislabels in per-DS queries
    const items = (obsRes.data.items || [])
      .filter((obs: any) => {
        const r = obs.result
        return r && typeof r.etaLat === 'number' && typeof r.etaLon === 'number' && r.title
      })

    if (!items.length) {
      source.clear()
      featureCounts.value['senrepMarkers'] = 0
      knownSenrepContacts.value = []
      return
    }

    // Parse all valid SENREP observations and group by contactId for track lines
    interface SenrepObs { obs: any; contactId: string; reportType: string; tgtType: string; lat: number; lon: number; time: string }
    const parsed: SenrepObs[] = []
    for (const obs of items) {
      const result = obs.result
      if (!result) continue
      const lat = result.etaLat
      const lon = result.etaLon
      if (typeof lat !== 'number' || typeof lon !== 'number') continue
      parsed.push({
        obs,
        contactId: result.title || 'SENREP',
        reportType: result.subTyp || 'INIT',
        tgtType: result.tgtTyp || 'UAS',
        lat, lon,
        time: obs.phenomenonTime || '',
      })
    }

    // Group by contactId and sort each group chronologically
    // Uses plain object instead of Map for broad runtime compatibility
    const byContact: Record<string, SenrepObs[]> = {}
    for (const s of parsed) {
      if (byContact[s.contactId]) byContact[s.contactId].push(s)
      else byContact[s.contactId] = [s]
    }
    for (const arr of Object.values(byContact)) {
      arr.sort((a, b) => (a.time < b.time ? -1 : a.time > b.time ? 1 : 0))
    }

    // Update knownSenrepContacts — contacts that have at least one INIT (available for FUP)
    // Also build senrepContactOwners map: contactId → senderId of the INIT obs
    const initContacts: string[] = []
    const owners: Record<string, string> = {}
    for (const [cid, arr] of Object.entries(byContact)) {
      const initObs = arr.find(s => s.reportType === 'INIT')
      if (cid !== 'SENREP' && initObs) {
        initContacts.push(cid)
        owners[cid] = initObs.obs.result?.senderId || ''
      }
    }
    knownSenrepContacts.value = initContacts.sort()
    senrepContactOwners.value = owners

    const batch: Feature[] = []
    for (const s of parsed) {
      // SENREP markers always use red diamond — STANAG symbol lives on the
      // sampling feature (track FOI) created by the SENREP workflow instead.
      const markerFeature = new Feature({
        geometry: new Point(fromLonLat([s.lon, s.lat])),
      })
      markerFeature.setStyle(senrepMarkerStyle)
      markerFeature.set('resourceType', 'senrepMarkers')
      markerFeature.set('resourceId', s.obs.id || `senrep-${s.contactId}`)
      markerFeature.set('resourceName', `SENREP: ${s.contactId}`)
      markerFeature.set('rawData', {
        observationId: s.obs.id,
        datastreamId: SENREP_DS_ID,
        phenomenonTime: s.time,
        contactId: s.contactId,
        classification: s.tgtType,
        reportType: s.reportType,
        estimatedLat: s.lat,
        estimatedLon: s.lon,
        senderId: s.obs.result?.senderId,
        strNo: s.obs.result?.strNo,
        comments: s.obs.result?.comments,
      })
      batch.push(markerFeature)

      // Label below marker
      const labelText = s.contactId !== 'SENREP'
        ? `${s.contactId} — ${s.reportType}`
        : s.reportType || 'SENREP'
      const labelFeature = new Feature({
        geometry: new Point(fromLonLat([s.lon, s.lat])),
      })
      labelFeature.setStyle(new Style({
        text: new OlText({
          text: labelText,
          font: '10px sans-serif',
          fill: new Fill({ color: '#ef4444' }),
          stroke: new Stroke({ color: '#000', width: 3 }),
          offsetY: 20,
        }),
      }))
      labelFeature.set('resourceType', 'senrepMarkers')
      batch.push(labelFeature)
    }

    // Draw track lines connecting consecutive SENREPs for the same contact
    for (const [cid, arr] of Object.entries(byContact)) {
      if (arr.length < 2) continue
      const coords = arr.map(s => fromLonLat([s.lon, s.lat]))
      const lineFeature = new Feature({
        geometry: new LineString(coords),
      })
      lineFeature.setStyle(senrepTrackStyle)
      lineFeature.set('resourceType', 'senrepMarkers')
      lineFeature.set('resourceId', `senrep-track-${cid}`)
      lineFeature.set('resourceName', `SENREP Track: ${cid}`)
      batch.push(lineFeature)
    }

    // Atomic swap: clear + add in one synchronous block
    source.clear()
    source.addFeatures(batch)
    featureCounts.value['senrepMarkers'] = parsed.length
  } catch {
    // No data available — clear stale features
    source.clear()
    featureCounts.value['senrepMarkers'] = 0
  }
}

async function enrichSamplingFeatures(): Promise<void> {
  const source = vectorSources['samplingFeatures']
  if (!source) return

  // For each system with a known location, fetch its sampling features
  // and enrich any that don't already have geometry on the map
  const alreadyPlottedIds = new Set(
    source.getFeatures().filter(f => f.getGeometry()).map(f => f.get('resourceId'))
  )

  // Collect enriched features from parallel fetches, then batch-add
  const sfBatch: Feature[] = []
  const promises = Object.entries(systemLocationCache).map(async ([sysId, loc]) => {
    // When bbox is active, skip systems whose location is outside the bbox
    if (bboxFilter.value) {
      const [minX, minY, maxX, maxY] = bboxFilter.value
      if (loc.lon < minX || loc.lon > maxX || loc.lat < minY || loc.lat > maxY) return
    }

    try {
      const sfRes = await apiFetch(`/systems/${sysId}/samplingFeatures?limit=100`, {
        headers: { 'Accept': 'application/geo+json' },
      })
      if (!sfRes.ok || !sfRes.data) return

      let items: any[] = []
      if (sfRes.data.type === 'FeatureCollection' && Array.isArray(sfRes.data.features)) {
        items = sfRes.data.features
      } else if (Array.isArray(sfRes.data.items)) {
        items = sfRes.data.items
      }

      for (const item of items) {
        const sfId = extractId(item)
        if (alreadyPlottedIds.has(sfId)) continue
        if (extractGeometry(item)) continue

        sfBatch.push(createEnrichedFeature(
          item, 'samplingFeatures', loc.lat, loc.lon,
          `Derived from parent system ${sysId} (${loc.datastreamName || 'location obs'})`
        ))
      }
    } catch { /* skip */ }
  })

  await Promise.all(promises)
  if (sfBatch.length) source.addFeatures(sfBatch)
  enrichedCounts.value['samplingFeatures'] = sfBatch.length
  featureCounts.value['samplingFeatures'] = (featureCounts.value['samplingFeatures'] || 0) + sfBatch.length
}

/**
 * Load Part 2 DataStreams and place them at their parent system's cached location.
 */
async function loadDatastreams(): Promise<void> {
  const source = vectorSources['datastreams']
  if (!source) return

  source.clear()
  let count = 0
  try {
    const url = getListUrl('datastreams', buildQueryOptions())
    const res = await apiFetch(url)
    let items: any[] = (res.ok && res.data) ? (res.data.items || []) : []

    // Also fetch datastreams from primary systems (skip subsystems to avoid O(N) lag)
    const seenIds = new Set(items.map((d: any) => d.id))
    const sysResults = await Promise.all(
      Array.from(primarySystemIds).map(async (sysId) => {
        try {
          const r = await apiFetch(`/systems/${sysId}/datastreams?limit=100`)
          return (r.ok && r.data) ? (r.data.items || r.data.features || []) as any[] : [] as any[]
        } catch { return [] as any[] }
      })
    )
    for (const dsList of sysResults) {
      for (const ds of dsList) {
        if (ds.id && !seenIds.has(ds.id)) {
          seenIds.add(ds.id)
          items.push(ds)
        }
      }
    }

    const dsBatch: Feature[] = []
    for (const ds of items) {
      const sysId = extractSystemId(ds)
      if (!sysId) continue
      const loc = systemLocationCache[sysId]
      if (!loc) continue

      // When bbox is active, only show datastreams whose parent system is in the bbox
      if (bboxFilter.value) {
        const [minX, minY, maxX, maxY] = bboxFilter.value
        if (loc.lon < minX || loc.lon > maxX || loc.lat < minY || loc.lat > maxY) continue
      }

      dsBatch.push(createEnrichedFeature(
        ds, 'datastreams', loc.lat, loc.lon,
        `At parent system ${sysId} (${loc.datastreamName || 'location obs'})`
      ))
    }
    if (dsBatch.length) source.addFeatures(dsBatch)
    count = dsBatch.length
  } catch { /* skip */ }
  featureCounts.value['datastreams'] = count
}

/**
 * Load Part 2 ControlStreams and place them at their parent system's cached location.
 */
async function loadControlStreams(): Promise<void> {
  const source = vectorSources['controlStreams']
  if (!source) return

  source.clear()
  let count = 0
  try {
    const url = getListUrl('controlStreams', buildQueryOptions())
    const res = await apiFetch(url)
    let items: any[] = (res.ok && res.data) ? (res.data.items || []) : []

    // Also fetch control streams from primary systems (skip subsystems to avoid O(N) lag)
    const seenIds = new Set(items.map((d: any) => d.id))
    const sysResults = await Promise.all(
      Array.from(primarySystemIds).map(async (sysId) => {
        try {
          const r = await apiFetch(`/systems/${sysId}/controlStreams?limit=100`)
          return (r.ok && r.data) ? (r.data.items || r.data.features || []) as any[] : [] as any[]
        } catch { return [] as any[] }
      })
    )
    for (const csList of sysResults) {
      for (const cs of csList) {
        if (cs.id && !seenIds.has(cs.id)) {
          seenIds.add(cs.id)
          items.push(cs)
        }
      }
    }

    const csBatch: Feature[] = []
    for (const cs of items) {
      const sysId = extractSystemId(cs)
      if (!sysId) continue
      const loc = systemLocationCache[sysId]
      if (!loc) continue

      // When bbox is active, only show controlStreams whose parent system is in the bbox
      if (bboxFilter.value) {
        const [minX, minY, maxX, maxY] = bboxFilter.value
        if (loc.lon < minX || loc.lon > maxX || loc.lat < minY || loc.lat > maxY) continue
      }

      csBatch.push(createEnrichedFeature(
        cs, 'controlStreams', loc.lat, loc.lon,
        `At parent system ${sysId} (${loc.datastreamName || 'location obs'})`
      ))
    }
    if (csBatch.length) source.addFeatures(csBatch)
    count = csBatch.length
  } catch { /* skip */ }
  featureCounts.value['controlStreams'] = count
}

// --- Bearing line helpers ---

/** Length of bearing line visualization in meters */
const BEARING_LINE_LENGTH_M = 3000

/**
 * Extract bearing/direction information from an observation result.
 * Supports both legacy (urn:x-odas:*) and v2.3 ScenarioPack formats:
 *
 * Legacy indexed formats:
 *   - LOB:  numBearings + bearing0..bearingN  { azimuth, elevation, energy, sourceId }
 *   - SSL:  numSources  + source0..sourceN    { x, y, z, energy }
 *   - SST:  numTracks   + track0..trackN      { id, tag, x, y, z, activity }
 *
 * v2.3 formats:
 *   - LOB flat:       result.bearingTrue (+ sensorLat/sensorLon)
 *   - SSL array:      result.src[]  { x, y, z, E }
 *   - SST array:      result.src[]  { id, tag, x, y, z, activity }
 *   - Track update:   result.bearingTrue + result.x/y/z + result.classLabel
 */
function extractBearings(result: any): Array<{ azimuth: number; elevation: number; energy: number; sourceId?: number; classLabel?: string; classConfidence?: number }> {
  const bearings: Array<{ azimuth: number; elevation: number; energy: number; sourceId?: number; classLabel?: string; classConfidence?: number }> = []
  if (!result || typeof result !== 'object') return bearings

  // ── Legacy LOB: bearing0..bearingN with { azimuth, elevation, energy, sourceId } ──
  if (typeof result.numBearings === 'number') {
    for (let i = 0; i < result.numBearings; i++) {
      const b = result[`bearing${i}`]
      if (b && typeof b.azimuth === 'number') {
        bearings.push({ azimuth: b.azimuth, elevation: b.elevation || 0, energy: b.energy || 0, sourceId: b.sourceId })
      }
    }
    return bearings
  }

  // ── Legacy SSL: source0..sourceN with { x, y, z, energy } ──
  if (typeof result.numSources === 'number') {
    for (let i = 0; i < result.numSources; i++) {
      const s = result[`source${i}`]
      if (s && typeof s.x === 'number' && typeof s.y === 'number') {
        const mag = Math.sqrt(s.x * s.x + s.y * s.y)
        if (mag < 0.01) continue
        const azimuth = ((Math.atan2(s.x, s.y) * 180 / Math.PI) + 360) % 360
        bearings.push({ azimuth, elevation: 0, energy: s.energy || 0 })
      }
    }
    return bearings
  }

  // ── Legacy SST: track0..trackN with { id, tag, x, y, z, activity } ──
  if (typeof result.numTracks === 'number') {
    for (let i = 0; i < result.numTracks; i++) {
      const t = result[`track${i}`]
      if (t && typeof t.x === 'number' && typeof t.y === 'number') {
        const mag = Math.sqrt(t.x * t.x + t.y * t.y)
        if (mag < 0.01) continue
        const azimuth = ((Math.atan2(t.x, t.y) * 180 / Math.PI) + 360) % 360
        bearings.push({ azimuth, elevation: 0, energy: t.activity || 0, sourceId: t.id })
      }
    }
    return bearings
  }

  // ── v2.3 Track Update (flat): bearingTrue + x/y/z + classLabel ──
  // Check this BEFORE LOB flat since track updates also have bearingTrue
  if (typeof result.bearingTrue === 'number' && typeof result.x === 'number' && typeof result.y === 'number') {
    bearings.push({
      azimuth: result.bearingTrue,
      elevation: result.elevation || 0,
      energy: result.activity || 0,
      sourceId: result.id,
      classLabel: result.classLabel,
      classConfidence: result.classConfidence,
    })
    return bearings
  }

  // ── v2.3 LOB flat: bearingTrue (+ sensorLat/sensorLon handled by caller) ──
  if (typeof result.bearingTrue === 'number') {
    bearings.push({
      azimuth: result.bearingTrue,
      elevation: 0,
      energy: 1.0, // LOB has no energy field; use full opacity
      sourceId: result.trackId,
      classLabel: result.classification, // Read from server — no fallback; sensors provide this
    })
    return bearings
  }

  // ── v2.3 SSL array: src[] with { x, y, z, E } ──
  // ── v2.3 SST array: src[] with { id, tag, x, y, z, activity } ──
  if (Array.isArray(result.src)) {
    for (const s of result.src) {
      if (s && typeof s.x === 'number' && typeof s.y === 'number') {
        const mag = Math.sqrt(s.x * s.x + s.y * s.y)
        if (mag < 0.01) continue
        // x = East, y = North → atan2(x, y) = bearing from North clockwise
        const azimuth = ((Math.atan2(s.x, s.y) * 180 / Math.PI) + 360) % 360
        bearings.push({
          azimuth,
          elevation: 0,
          energy: s.E ?? s.activity ?? 0,
          sourceId: s.id,
        })
      }
    }
    return bearings
  }

  return bearings
}

/**
 * Compute the endpoint of a bearing line given origin, azimuth, and distance.
 * Uses small-distance approximation (accurate within ~10 km).
 */
function computeBearingEndpoint(lat: number, lon: number, azimuthDeg: number, distanceM: number): { lat: number; lon: number } {
  const azRad = azimuthDeg * Math.PI / 180
  const dLat = distanceM * Math.cos(azRad) / 111320
  const dLon = distanceM * Math.sin(azRad) / (111320 * Math.cos(lat * Math.PI / 180))
  return { lat: lat + dLat, lon: lon + dLon }
}

/**
 * Style for a bearing line, with opacity and width proportional to detection energy.
 */
function getBearingLineStyle(energy: number): Style {
  const hex = TYPE_COLORS['bearingLines'] || '#f43f5e'
  const r = parseInt(hex.slice(1, 3), 16)
  const g = parseInt(hex.slice(3, 5), 16)
  const b = parseInt(hex.slice(5, 7), 16)
  const opacity = 0.4 + Math.min(energy, 1) * 0.6
  const width = 2 + Math.min(energy, 1) * 2

  return new Style({
    stroke: new Stroke({
      color: `rgba(${r}, ${g}, ${b}, ${opacity})`,
      width,
    }),
  })
}

/**
 * Load observation layers — both individual points and GPS trail tracks.
 * Fetches recent observations from all location datastreams once and builds
 * both layers from the same data to avoid duplicate API calls.
 */
async function loadObservationLayers(obsLimit = 500): Promise<void> {
  const pointSource = vectorSources['observationPoints']
  const trackSource = vectorSources['observationTracks']
  const bearingSource = vectorSources['bearingLines']

  // Collect new features into pending arrays — do NOT clear sources yet.
  // Atomic swap (clear + add) happens after all API calls complete, which
  // eliminates the visible "blink" where features vanish during fetch.
  const pendingPoints: Feature[] = []
  const pendingTracks: Feature[] = []
  const pendingBearings: Feature[] = []

  const isLive = liveMode.value
  let pointCount = 0
  let trackCount = 0
  let bearingCount = 0

  // Track per-source observation counts for the source toggle UI
  const srcCounts: Record<string, number> = {}

  const promises = locationDatastreamList.map(async (dsInfo) => {
    try {
      let items: any[] = []

      // Position/track datastreams need many observations to draw a meaningful
      // ground track; LOB/bearing datastreams only need the most recent few.
      const dsNameLower = dsInfo.name.toLowerCase()
      const isPositionDs = dsNameLower.includes('position') || dsNameLower.includes('location')
        || dsNameLower.includes('gps')
      const isLobDs = dsNameLower.includes('lob') || dsNameLower.includes('bearing')
      // Detect weather/surface observation datastreams for special handling
      const isWeatherDs = dsNameLower.includes('surface') || dsNameLower.includes('weather')
        || dsNameLower.includes('metar') || dsNameLower.includes('nws') || dsNameLower.includes('awx')
        || dsNameLower.includes('ndbc') || dsNameLower.includes('buoy')
        || dsNameLower.includes('co-ops') || dsNameLower.includes('coops') || dsNameLower.includes('tide') || dsNameLower.includes('coastal')
        || dsNameLower.includes('discharge') || dsNameLower.includes('gage') || dsNameLower.includes('streamflow')
        || dsNameLower.includes('nims') || dsNameLower.includes('station image')
      // Detect aircraft / ADS-B surveillance datastreams
      const isAircraftDs = dsNameLower.includes('aircraft') || dsNameLower.includes('adsb')
        || dsNameLower.includes('ads-b') || dsNameLower.includes('state vector')
      // Detect earthquake / seismic event datastreams
      const isEarthquakeDs = dsNameLower.includes('earthquake') || dsNameLower.includes('seismic')
        || dsNameLower.includes('quake')
      // Classify into a source category for the per-source toggle
      const obsSourceKey = classifyObsSource(dsInfo.name)
      // Position/satellite DS: cap at obsLimit (default 500) to keep total
      // observation count manageable.
      // LOB DS in live mode: exactly 1 per sensor — cleanest visual, shows only
      // the very latest bearing from each MA system.
      // Weather DS: only latest observation per station (no track needed).
      // Aircraft DS: fetch up to 200 to capture the full batch (~140 aircraft).
      // Earthquake DS: fetch up to 300 to cover 24h of global events.
      // Other DS: use caller's obsLimit.
      const effectiveLimit = (isLobDs && isLive) ? 1 : isWeatherDs ? 1 : isAircraftDs ? 200 : isEarthquakeDs ? 300 : obsLimit

      // OSH returns observations oldest-first and ignores sort params, so a
      // bare limit=N always returns the N OLDEST observations.  For position/
      // satellite datastreams this is usually a rapid-fire startup burst that
      // clusters in <1° of lat/lon — invisible at global zoom.  Fix: always
      // use a time-windowed query for position DS (and for all DS in live mode)
      // to guarantee we get the RECENT, well-distributed observations.
      //
      // After fetching, we deduplicate burst observations (gap < 10s between
      // consecutive items) so only normal-cadence data remains.  This makes
      // the track immune to reconnect-induced rapid-fire bursts.
      //
      // For LOB datastreams: OSH scope-leak contaminates some DS with 80%+
      // non-LOB observations.  Fetch a larger batch so genuine LOBs survive
      // after filtering, then keep only the most recent ones so bearings
      // converge on the current target position.
      const useTimeWindow = isLive || isPositionDs || isWeatherDs || isAircraftDs || isEarthquakeDs
      if (useTimeWindow) {
        const latestUrl = getNestedListUrl('datastreams', dsInfo.id, 'observations', {
          resultTime: 'latest',
          limit: 1,
        } as any)
        let latestRes = await apiFetch(latestUrl, {
          headers: { 'Accept': 'application/om+json' },
        })
        // Fallback: Go CSAPI server ignores resultTime=latest
        if (latestRes.ok && !latestRes.data?.items?.length) {
          const fallbackUrl = getNestedListUrl('datastreams', dsInfo.id, 'observations', {
            limit: 1,
          } as any)
          latestRes = await apiFetch(fallbackUrl, {
            headers: { 'Accept': 'application/om+json' },
          })
        }
        if (!latestRes.ok || !latestRes.data?.items?.length) return
        const latestTime = latestRes.data.items[0].resultTime || latestRes.data.items[0].phenomenonTime
        if (!latestTime) return

        // Position datastreams: 4-hour window to capture multiple full orbits
        // (~92 min each → 4h ≈ 2.6 orbits).
        // LOB datastreams: 5-minute window for tight real-time view.
        // Weather datastreams: 2-hour window (obs ~hourly) to ensure latest.
        // Earthquake datastreams: 24-hour window to show all recent events.
        const windowMinutes = isPositionDs ? 240 : isWeatherDs ? 120 : isAircraftDs ? 10 : isEarthquakeDs ? 1440 : 5
        const latestMs = new Date(latestTime).getTime()
        // Fetch limit: position DS gets 2× effective to allow burst dedup
        // headroom, LOB DS needs extra to overcome OSH scope-leak contamination,
        // others use effectiveLimit.
        const fetchLimit = isPositionDs ? effectiveLimit * 2 : isLobDs ? 30 : effectiveLimit
        const windowStartDate = new Date(latestMs - windowMinutes * 60 * 1000)
        const windowEndDate = new Date(latestMs + 1000)
        const timeWindowUrl = getNestedListUrl('datastreams', dsInfo.id, 'observations', {
          resultTime: { start: windowStartDate, end: windowEndDate },
          limit: fetchLimit,
          sortBy: 'resultTime',
          sortOrder: 'asc',
        } as any)
        const obsRes = await apiFetch(
          timeWindowUrl,
          { headers: { 'Accept': 'application/om+json' } },
        )
        if (obsRes.ok && obsRes.data) {
          let allItems = obsRes.data.items || []

          // Deduplicate: discard burst observations (gap < 10s from previous).
          // Normal cadence is 30s; burst is ~70ms.  This cleanly removes
          // reconnect-induced rapid-fire clumps while keeping real data.
          if (isPositionDs && allItems.length > 1) {
            const MIN_GAP_MS = 10_000
            const filtered = [allItems[0]]
            let prevMs = new Date(allItems[0].resultTime || allItems[0].phenomenonTime || 0).getTime()
            for (let i = 1; i < allItems.length; i++) {
              const tMs = new Date(allItems[i].resultTime || allItems[i].phenomenonTime || 0).getTime()
              if (tMs - prevMs >= MIN_GAP_MS) {
                filtered.push(allItems[i])
                prevMs = tMs
              }
            }
            allItems = filtered
          }

          // LOB DS: filter out scope-leaked non-LOB observations, then keep
          // only the most recent genuine LOBs so bearings converge on the
          // current target position instead of fanning across old positions.
          if (isLobDs) {
            allItems = allItems.filter((o: any) =>
              typeof o.result?.bearingTrue === 'number' && typeof o.result?.bearingStdDev === 'number')
          }

          items = allItems.slice(-effectiveLimit)
        }
      } else {
        const plainUrl = getNestedListUrl('datastreams', dsInfo.id, 'observations', {
          limit: effectiveLimit,
        } as any)
        const obsRes = await apiFetch(plainUrl, {
          headers: { 'Accept': 'application/om+json' },
        })
        if (!obsRes.ok || !obsRes.data) return
        items = obsRes.data.items || []
      }

      // NOTE: OSH has a scope-leak bug where per-DS observation queries
      // return observations from other datastreams AND mislabel datastream@id.
      // We no longer filter by datastream@id — downstream parsing naturally
      // rejects observations with incompatible result schemas.

      const trackCoords: [number, number][] = []

      // Detect satellite/orbit datastreams for distinct styling
      const isSatDs = dsNameLower.includes('position') && (
        dsNameLower.includes('sgp4') || dsNameLower.includes('satellite')
        || dsNameLower.includes('iss') || dsNameLower.includes('orbital')
        || dsNameLower.includes('tracker')
      )

      for (let obsIdx = 0; obsIdx < items.length; obsIdx++) {
        const obs = items[obsIdx]
        // --- Observation points: results with lat/lon coordinates ---
        const loc = extractLatLonFromResult(obs.result)
        if (loc) {
          const { lat, lon, alt } = loc
          let inBbox = true
          if (bboxFilter.value) {
            const [minX, minY, maxX, maxY] = bboxFilter.value
            if (lon < minX || lon > maxX || lat < minY || lat > maxY) inBbox = false
          }
          if (inBbox) {
            trackCoords.push([lon, lat])
            if (pointSource) {
              const feature = new Feature({
                geometry: new Point(fromLonLat([lon, lat])),
              })
              // Weather stations: per-station style with station ID + temp label
              const wxStyle = isWeatherDs
                ? weatherStationStyle(obs.result?.stationId || '?', obs.result?.temperature_c ?? null)
                : null
              const acStyle = isAircraftDs
                ? aircraftObsPointStyle(typeof obs.result?.true_track_deg === 'number' ? obs.result.true_track_deg : 0)
                : null
              // Earthquake events: magnitude-scaled colored circle
              const eqMag = isEarthquakeDs && obs.result?.magnitude != null
                ? (typeof obs.result.magnitude === 'number' ? obs.result.magnitude : parseFloat(obs.result.magnitude))
                : NaN
              const eqStyle = isEarthquakeDs && !isNaN(eqMag) ? earthquakeObsPointStyle(eqMag) : null
              feature.setStyle(wxStyle || acStyle || eqStyle || (isSatDs ? satObsPointStyle : getStyle('observationPoints')))
              feature.set('resourceType', 'observationPoints')
              feature.set('resourceId', obs.id || `${dsInfo.id}-obs-${pointCount}`)
              feature.set('resourceName', isWeatherDs && obs.result?.stationName
                ? `${obs.result.stationId} — ${obs.result.stationName}`
                : isAircraftDs && obs.result?.callsign
                  ? `✈ ${obs.result.callsign.trim()} (${obs.result.icao24 || '?'})`
                  : isEarthquakeDs && obs.result?.magnitude != null
                    ? `🌋 M${typeof obs.result.magnitude === 'number' ? obs.result.magnitude.toFixed(1) : obs.result.magnitude} — ${obs.result.place || 'Unknown'}`
                    : `Obs @ ${lat.toFixed(5)}, ${lon.toFixed(5)}`)
              feature.set('enriched', true)
              feature.set('enrichmentSource', dsInfo.name)
              feature.set('rawData', {
                observationId: obs.id,
                datastreamId: dsInfo.id,
                datastreamName: dsInfo.name,
                systemId: dsInfo.systemId,
                phenomenonTime: obs.phenomenonTime,
                resultTime: obs.resultTime,
                lat, lon, alt,
                result: obs.result,
              })
              // Tag feature with source category for per-source toggle
              feature.set('obsSourceKey', obsSourceKey)
              feature.set('_origStyle', feature.getStyle())
              srcCounts[obsSourceKey] = (srcCounts[obsSourceKey] || 0) + 1
              // Auto-register new sources as visible
              if (activeObsSources.value[obsSourceKey] === undefined) {
                activeObsSources.value[obsSourceKey] = true
              }
              // Apply per-source visibility
              if (activeObsSources.value[obsSourceKey] === false) {
                feature.setStyle(HIDDEN_STYLE)
              }
              pendingPoints.push(feature)
              pointCount++
            }
          }
        }

        // --- Bearing lines: acoustic detection directions ---
        // Only extract LOBs from LOB datastreams — Track Updates duplicate the
        // bearings at slightly different angles, doubling the line count.
        const isLobDatastream = dsNameLower.includes('lob') || dsNameLower.includes('bearing')
        // Tight schema filter: genuine LOBs have both bearingTrue AND bearingStdDev.
        // This rejects scope-leak contamination (track updates, localizer, health, etc.)
        const isGenuineLob = typeof obs.result?.bearingTrue === 'number' && typeof obs.result?.bearingStdDev === 'number'
        // In LIVE MODE, LOB lines are rendered from the localizer observation
        // (loadLocationEstimates) which embeds the exact LOBs used for the fix.
        // Skip independent LOB rendering here to avoid temporal mismatch.
        if (bearingSource && isGenuineLob && isLobDatastream && !isLive) {
          // Prefer systemLocationCache; fall back to self-contained sensorLat/sensorLon (v2.3 LOB format)
          const sensorLoc = systemLocationCache[dsInfo.systemId]
            || (typeof obs.result.sensorLat === 'number' && typeof obs.result.sensorLon === 'number'
              ? { lat: obs.result.sensorLat, lon: obs.result.sensorLon }
              : null)
          if (sensorLoc) {
            const obsBearings = extractBearings(obs.result)
            for (const b of obsBearings) {
              if (b.energy < 0.1) continue
              const ep = computeBearingEndpoint(sensorLoc.lat, sensorLoc.lon, b.azimuth, BEARING_LINE_LENGTH_M)
              const feature = new Feature({
                geometry: new LineString([
                  fromLonLat([sensorLoc.lon, sensorLoc.lat]),
                  fromLonLat([ep.lon, ep.lat]),
                ]),
              })
              const bearingStyle = isLive
                ? getRecencyBearingStyle(b.energy, items.length > 1 ? (obsIdx / (items.length - 1)) : 1)
                : getCachedBearingLineStyle(b.energy)
              feature.setStyle(bearingStyle)
              feature.set('resourceType', 'bearingLines')
              feature.set('resourceId', `${dsInfo.id}-lob-${bearingCount}`)
              const label = b.classLabel
                ? `Bearing ${b.azimuth.toFixed(1)}° — Classification: ${b.classLabel}`
                : `Bearing ${b.azimuth.toFixed(1)}°`
              feature.set('resourceName', label)
              feature.set('enriched', true)
              feature.set('enrichmentSource', dsInfo.name)
              feature.set('rawData', {
                observationId: obs.id,
                datastreamId: dsInfo.id,
                datastreamName: dsInfo.name,
                systemId: dsInfo.systemId,
                phenomenonTime: obs.phenomenonTime,
                azimuth: b.azimuth,
                elevation: b.elevation,
                energy: b.energy,
                sourceId: b.sourceId,
                classLabel: b.classLabel,
                classConfidence: b.classConfidence,
                sensorLat: sensorLoc.lat,
                sensorLon: sensorLoc.lon,
              })
              pendingBearings.push(feature)
              bearingCount++
            }
          }
        }
      }

      // Track LineString from all parsed coordinates
      // Detect orbit/satellite tracks and apply distinct styling + date-line splitting
      // Skip track lines for aircraft/earthquake DS — each obs is a different entity, not a time series
      if (trackSource && trackCoords.length >= 2 && !isAircraftDs && !isEarthquakeDs) {
        // Split track at antimeridian (±180° lon) crossings to avoid ugly wrapping lines
        const segments = splitTrackAtDateLine(trackCoords)
        for (const segment of segments) {
          if (segment.length < 2) continue
          const lineFeature = new Feature({
            geometry: new LineString(segment.map(c => fromLonLat(c))),
          })
          if (isSatDs) {
            lineFeature.setStyle([orbitTrackGlowStyle, orbitTrackStyle])
          } else {
            lineFeature.setStyle(getStyle('observationTracks'))
          }
          lineFeature.set('resourceType', 'observationTracks')
          lineFeature.set('resourceId', dsInfo.id)
          lineFeature.set('resourceName', `Track: ${dsInfo.name}`)
          lineFeature.set('enriched', true)
          lineFeature.set('enrichmentSource', `${trackCoords.length} observations from ${dsInfo.name}`)
          lineFeature.set('rawData', { datastreamId: dsInfo.id, datastreamName: dsInfo.name, systemId: dsInfo.systemId, pointCount: trackCoords.length })
          // Tag track with same source category for per-source toggle
          lineFeature.set('obsSourceKey', obsSourceKey)
          lineFeature.set('_origStyle', lineFeature.getStyle())
          if (activeObsSources.value[obsSourceKey] === false) {
            lineFeature.setStyle(HIDDEN_STYLE)
          }
          pendingTracks.push(lineFeature)
          trackCount++
        }
      }

      // Snap ISS/satellite marker to the last track point so marker and track
      // are guaranteed to be at the same position (same data, no extra API call).
      if (isSatDs && trackCoords.length > 0) {
        const tip = trackCoords[trackCoords.length - 1]
        const tipCoord = fromLonLat(tip)
        systemLocationCache[dsInfo.systemId] = {
          lat: tip[1], lon: tip[0],
          datastreamName: dsInfo.name,
          phenomenonTime: items[items.length - 1]?.phenomenonTime,
        }
        const depSrc = vectorSources['deployments']
        if (depSrc) {
          for (const f of depSrc.getFeatures()) {
            const rd = f.get('rawData')
            const href = rd?.properties?.['platform@link']?.href || ''
            if (href.replace(/\/+$/, '').split('/').pop() === dsInfo.systemId) {
              f.setGeometry(new Point(tipCoord))
            }
          }
        }
        const sysSrc = vectorSources['systems']
        if (sysSrc) {
          for (const f of sysSrc.getFeatures()) {
            if (f.get('resourceId') === dsInfo.systemId) {
              f.setGeometry(new Point(tipCoord))
            }
          }
        }
      }
    } catch (e: any) { console.warn(`[Obs] DS ${dsInfo.id} (${dsInfo.name}) error:`, e?.message || e) }
  })

  await Promise.all(promises)

  // Atomic swap: clear old features and add new ones in one synchronous block.
  // This eliminates the visual blink — sources are empty for <1ms instead of seconds.
  if (pointSource) { pointSource.clear(); pointSource.addFeatures(pendingPoints) }
  if (trackSource) { trackSource.clear(); trackSource.addFeatures(pendingTracks) }
  // In live mode, LOB lines are rendered by loadLocationEstimates() from the
  // compound localizer observation — do NOT clear bearingSource here or those
  // lines will disappear every poll cycle.
  if (bearingSource && !isLive) {
    bearingSource.clear(); bearingSource.addFeatures(pendingBearings)
    featureCounts.value['bearingLines'] = bearingCount
  }
  featureCounts.value['observationPoints'] = pointCount
  featureCounts.value['observationTracks'] = trackCount

  // Update per-source observation counts for the toggle UI
  obsSourceCounts.value = srcCounts
}

async function loadAllResources() {
  loading.value = true
  error.value = ''
  hasSearched.value = true
  featureCounts.value = {}
  for (const key of Object.keys(enrichedCounts.value)) delete enrichedCounts.value[key]

  // Close any open popup and clear selection
  closePopup()

  // 1. Load Part 1 resources (systems, deployments, procedures, samplingFeatures)
  const promises = SPATIAL_TYPES.map(async (rt) => {
    const count = await loadResourceType(rt.key)
    featureCounts.value[rt.key] = count
  })
  await Promise.all(promises)

  // 2. Build system location cache (static geometry + subsystem propagation + observation data)
  await buildSystemLocationCache()

  // 3. Enrich Part 1 resource types that have null geometry
  await enrichResourcesWithLocations()

  // 3b. Discover detection range configs from server, then build rings
  await fetchDetectionRangeConfigs()
  buildDetectionRanges()

  // 3c. Discover localizer datastream for location estimate rendering
  await discoverLocalizerDatastream()

  // 4. Load Part 2 resources at parent system locations + observation layers
  await Promise.all([
    loadDatastreams(),
    loadControlStreams(),
    loadObservationLayers(500),
    loadLocationEstimates(),
    loadSenrepMarkers(),
  ])

  loading.value = false

  // Start live refresh interval if Live Mode is on by default
  // Stagger first poll to prevent thundering herd when many users load simultaneously
  if (liveMode.value) {
    const stagger = Math.random() * INITIAL_POLL_STAGGER_MS
    setTimeout(() => {
      if (!liveMode.value) return  // user may have toggled off during stagger
      lastRefreshTime.value = new Date().toLocaleTimeString()
      refreshLiveLayers()
      liveInterval = setInterval(refreshLiveLayers, LIVE_REFRESH_MS)
    }, stagger)
  }

  // Fit map to all features (merge extents directly — no intermediate VectorSource)
  let hasAnyFeatures = false
  let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity
  for (const src of Object.values(vectorSources)) {
    if (src.getFeatures().length === 0) continue
    const ext = src.getExtent()
    if (ext[0] < minX) minX = ext[0]
    if (ext[1] < minY) minY = ext[1]
    if (ext[2] > maxX) maxX = ext[2]
    if (ext[3] > maxY) maxY = ext[3]
    hasAnyFeatures = true
  }
  if (hasAnyFeatures && map) {
    map.getView().fit([minX, minY, maxX, maxY], {
      padding: [50, 50, 50, 50],
      maxZoom: 16,
      duration: 500,
    })
  }
}

// --- Bbox Filter ---

function startDrawBbox() {
  if (!map) return
  if (drawInteraction) {
    map.removeInteraction(drawInteraction)
    drawInteraction = null
  }
  bboxSource.clear()

  drawInteraction = new Draw({
    source: bboxSource,
    type: 'Circle',
    geometryFunction: createBox(),
  })

  drawInteraction.on('drawend', (evt) => {
    const geom = evt.feature.getGeometry()
    if (geom) {
      const extent = geom.getExtent()
      const min = toLonLat([extent[0], extent[1]])
      const max = toLonLat([extent[2], extent[3]])
      bboxFilter.value = [min[0], min[1], max[0], max[1]]
    }
    // Remove any inline style Draw may have set so the layer style applies
    evt.feature.setStyle(undefined)
    if (map && drawInteraction) {
      map.removeInteraction(drawInteraction)
      drawInteraction = null
    }
    drawingBbox.value = false
  })

  map.addInteraction(drawInteraction)
  drawingBbox.value = true
}

function clearBbox() {
  bboxFilter.value = null
  bboxSource.clear()
  if (map && drawInteraction) {
    map.removeInteraction(drawInteraction)
    drawInteraction = null
  }
  drawingBbox.value = false
}

function clearAllFilters() {
  keywordFilter.value = ''
  dtStart.value = ''
  dtEnd.value = ''
  clearBbox()
}

const hasAnyFilter = computed(() =>
  !!keywordFilter.value.trim() || !!dtStart.value || !!dtEnd.value || !!bboxFilter.value
)

function toggleLayer(key: string) {
  activeLayers.value[key] = !activeLayers.value[key]
  const layer = vectorLayers[key]
  if (layer) {
    layer.setVisible(activeLayers.value[key])
  }
}

/**
 * Toggle visibility of a specific observation data source (e.g. NWS, NDBC, OpenSky).
 * Iterates point and track features, hiding/restoring based on the source tag.
 */
function toggleObsSource(key: string) {
  activeObsSources.value[key] = !activeObsSources.value[key]
  const visible = activeObsSources.value[key]
  // Toggle observation points
  const pointSource = vectorSources['observationPoints']
  if (pointSource) {
    for (const f of pointSource.getFeatures()) {
      if (f.get('obsSourceKey') === key) {
        f.setStyle(visible ? f.get('_origStyle') : HIDDEN_STYLE)
      }
    }
  }
  // Toggle observation tracks
  const trackSource = vectorSources['observationTracks']
  if (trackSource) {
    for (const f of trackSource.getFeatures()) {
      if (f.get('obsSourceKey') === key) {
        f.setStyle(visible ? f.get('_origStyle') : HIDDEN_STYLE)
      }
    }
  }
}

/** Computed list of discovered sources (only those with features) for the UI. */
const discoveredObsSources = computed(() => {
  const counts = obsSourceCounts.value
  return OBS_SOURCE_DEFS.filter(d => (counts[d.key] || 0) > 0)
})

/**
 * Re-apply styles to all features on the map when the milsymbol toggle changes.
 */
function refreshAllStyles() {
  for (const [resourceType, source] of Object.entries(vectorSources)) {
    if (!source) continue
    for (const feature of source.getFeatures()) {
      const rawData = feature.get('rawData')
      const isEnriched = feature.get('enriched') || false
      feature.setStyle(getStyle(resourceType, isEnriched, rawData))
    }
  }
  // Also refresh the selected feature highlight if one is active
  if (selectedFeature.value?._olFeature) {
    const sf = selectedFeature.value
    sf._olFeature.setStyle(getSelectedStyle(sf.resourceType, sf.rawData))
  }
}

// ── Live Mode toggle ─────────────────────────────────────────────
async function refreshLiveLayers() {
  try {
    // In live mode, fetch fresh observations + update moving-system positions.
    await Promise.all([
      loadObservationLayers(500),
      loadLocationEstimates(),
      loadSenrepMarkers(),
      updateMovingSystemPositions(),
    ])
    lastRefreshTime.value = new Date().toLocaleTimeString()
  } catch { /* swallow errors during background refresh */ }
}

/**
 * Update the map positions of systems/deployments with position datastreams.
 * Queries the latest observation from each position-type location datastream
 * and moves the corresponding deployment + system features to match.
 * This uses standard CSAPI observation queries (resultTime=latest).
 */
async function updateMovingSystemPositions(): Promise<void> {
  const positionDs = locationDatastreamList.filter(ds => {
    const nm = ds.name.toLowerCase()
    if (!(nm.includes('position') || nm.includes('location') || nm.includes('gps'))) return false
    // Skip satellite/orbit datastreams — their position is already handled by
    // the snap-to-track-tip code in loadObservationLayers(). Running both in
    // parallel causes a visible blink where the marker jumps to the wrong
    // position from this separate API call before being corrected by the snap.
    if (nm.includes('sgp4') || nm.includes('satellite') || nm.includes('iss')
        || nm.includes('orbital') || nm.includes('tracker')) return false
    return true
  })
  if (positionDs.length === 0) return

  await Promise.all(positionDs.map(async (dsInfo) => {
    try {
      const posUrl = getNestedListUrl('datastreams', dsInfo.id, 'observations', {
        resultTime: 'latest',
        limit: 1,
      } as any)
      let res = await apiFetch(posUrl, {
        headers: { 'Accept': 'application/om+json' },
      })
      // Fallback: Go CSAPI server ignores resultTime=latest
      if (res.ok && !res.data?.items?.length) {
        const fallbackUrl = getNestedListUrl('datastreams', dsInfo.id, 'observations', {
          limit: 1,
        } as any)
        res = await apiFetch(fallbackUrl, {
          headers: { 'Accept': 'application/om+json' },
        })
      }
      if (!res.ok || !res.data?.items?.length) return
      const obs = res.data.items[0]
      const loc = extractLatLonFromResult(obs.result)
      if (!loc) return

      // Update the system location cache
      systemLocationCache[dsInfo.systemId] = {
        lat: loc.lat, lon: loc.lon, alt: loc.alt,
        datastreamName: dsInfo.name,
        phenomenonTime: obs.phenomenonTime,
      }

      // Move deployment features that link to this system
      const newCoord = fromLonLat([loc.lon, loc.lat])
      const depSource = vectorSources['deployments']
      if (depSource) {
        for (const feature of depSource.getFeatures()) {
          const rawData = feature.get('rawData')
          const platHref = rawData?.properties?.['platform@link']?.href || ''
          const linkedSysId = platHref.replace(/\/+$/, '').split('/').pop()
          if (linkedSysId === dsInfo.systemId) {
            feature.setGeometry(new Point(newCoord))
          }
        }
      }

      // Move system features for this system
      const sysSource = vectorSources['systems']
      if (sysSource) {
        for (const feature of sysSource.getFeatures()) {
          if (feature.get('resourceId') === dsInfo.systemId) {
            feature.setGeometry(new Point(newCoord))
          }
        }
      }
    } catch { /* skip */ }
  }))
}

function toggleLiveMode() {
  liveMode.value = !liveMode.value
  if (liveMode.value) {
    // Immediately refresh, then start interval
    refreshLiveLayers()
    liveInterval = setInterval(refreshLiveLayers, LIVE_REFRESH_MS)
  } else {
    if (liveInterval) {
      clearInterval(liveInterval)
      liveInterval = null
    }
    lastRefreshTime.value = ''
    // Clear persisted fix markers when leaving live mode
    persistedFixMarkers.length = 0
    seenFixObsIds.clear()
    const locSource = vectorSources['locationEstimates']
    if (locSource) locSource.clear()
    // Reload full history when leaving live mode
    loadObservationLayers(500)
    loadLocationEstimates()
    loadSenrepMarkers()
  }
}

function toggleBasemap() {
  if (osmLayer) osmLayer.setVisible(!useSatellite.value)
  if (satLayer) satLayer.setVisible(useSatellite.value)
  if (satRefLayer) satRefLayer.setVisible(useSatellite.value)
}

// --- Map Setup ---

onMounted(() => {
  if (!mapContainer.value || !popupContainer.value) return

  // Start polling simulator status so buttons reflect current state
  startSimPolling()

  // Create overlay for popup
  overlay = new Overlay({
    element: popupContainer.value,
    autoPan: { animation: { duration: 250 } },
  })

  // Create vector sources and layers for each map type
  // Layers with text labels get declutter: true to eliminate overlapping label renders.
  // updateWhileAnimating/Interacting: false defers re-render until pan/zoom ends.
  const labeledTypes = new Set(['systems', 'procedures', 'samplingFeatures', 'datastreams', 'controlStreams'])
  for (const rt of MAP_TYPES) {
    const source = new VectorSource()
    vectorSources[rt.key] = source
    const layerOpts: Record<string, any> = {
      source,
      zIndex: rt.key === 'detectionRanges' ? 3 : rt.key === 'observationTracks' ? 5 : rt.key === 'bearingLines' ? 6 : rt.key === 'observationPoints' ? 7 : rt.key === 'locationEstimates' ? 8 : rt.key === 'senrepMarkers' ? 9 : rt.key === 'samplingFeatures' ? 11 : 10,
      // Deployments: no declutter so STANAG symbols are never hidden by label overlap
      declutter: labeledTypes.has(rt.key),
      updateWhileAnimating: false,
      updateWhileInteracting: false,
    }
    // Bearing lines: sort by azimuth so LOBs from different sensors are interleaved
    // instead of consistently stacking one sensor on top of another.
    if (rt.key === 'bearingLines') {
      layerOpts.renderOrder = (a: Feature, b: Feature) => {
        const azA = a.get('rawData')?.azimuth ?? 0
        const azB = b.get('rawData')?.azimuth ?? 0
        return azA - azB
      }
    }
    const layer = new VectorLayer(layerOpts)
    // Respect default-off layers
    if (activeLayers.value[rt.key] === false) layer.setVisible(false)
    vectorLayers[rt.key] = layer
  }

  // Create basemap layers
  osmLayer = new TileLayer({ source: new OSM(), visible: !useSatellite.value })
  satLayer = new TileLayer({
    source: new XYZ({
      url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
      attributions: 'Tiles &copy; Esri',
      maxZoom: 19,
    }),
    visible: useSatellite.value,
  })
  // Transparent overlay: borders, roads, and place names on top of satellite
  satRefLayer = new TileLayer({
    source: new XYZ({
      url: 'https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}',
      maxZoom: 19,
    }),
    visible: useSatellite.value,
    zIndex: 1,
  })

  // Create map
  map = new Map({
    target: mapContainer.value,
    layers: [
      osmLayer,
      satLayer,
      satRefLayer,
      ...Object.values(vectorLayers),
      bboxLayer,
    ],
    overlays: [overlay],
    view: new View({
      center: fromLonLat([0, 20]),
      zoom: 2,
    }),
  })


  // Click handler for features
  map.on('singleclick', (evt) => {
    // Suppress feature clicks while drawing a bbox
    if (drawingBbox.value) return

    // Collect ALL interactive features at this pixel
    const hits: any[] = []
    map!.forEachFeatureAtPixel(evt.pixel, (feature) => {
      const rt = feature.get('resourceType')
      if (!rt) return
      if (rt === 'detectionRanges') return // static overlay — not selectable
      hits.push(feature)
    })

    if (hits.length === 0) {
      closePopup()
      return
    }

    // Toggle: if clicking the already-selected feature (and only 1 hit), deselect
    if (hits.length === 1 && selectedFeature.value?._olFeature === hits[0]) {
      closePopup()
      return
    }

    // Build stacked-feature metadata for the picker UI
    stackedFeatures.value = hits.map((f: any) => ({
      resourceType: f.get('resourceType'),
      resourceId: f.get('resourceId'),
      resourceName: f.get('resourceName'),
      _olFeature: f,
    }))

    // Always select the first feature immediately
    selectOlFeature(hits[0])
  })

  // Pointer cursor on features + coordinate display
  // Throttled to 100ms to avoid expensive hasFeatureAtPixel on every mouse move
  let pointerMoveTimer = 0
  let lastHitCheck = 0
  map.on('pointermove', (evt) => {
    // Always update coordinates cheaply
    const [lon, lat] = toLonLat(evt.coordinate)
    mouseCoords.value = `${lat.toFixed(5)}°, ${lon.toFixed(5)}°`

    // Throttle hit-detection to 100ms and skip while loading
    const now = performance.now()
    if (loading.value || now - lastHitCheck < 100) return
    if (pointerMoveTimer) return
    pointerMoveTimer = requestAnimationFrame(() => {
      pointerMoveTimer = 0
      lastHitCheck = performance.now()
      if (!map || loading.value) return
      const pixel = map.getEventPixel(evt.originalEvent)
      const hit = map.hasFeatureAtPixel(pixel)
      const target = map.getTargetElement()
      if (target) {
        ;(target as HTMLElement).style.cursor = hit ? 'pointer' : ''
      }
    })
  })

  // Map is ready — auto-load all resources immediately (filterless query)
  loadAllResources()

  // Global Enter key → execute search (unless typing in a textarea)
  function onGlobalEnter(e: KeyboardEvent) {
    if (e.key !== 'Enter') return
    const tag = (e.target as HTMLElement)?.tagName?.toLowerCase()
    if (tag === 'textarea') return
    if (loading.value) return
    loadAllResources()
  }
  window.addEventListener('keydown', onGlobalEnter)
  globalEnterHandler = onGlobalEnter
})

onUnmounted(() => {
  stopSimPolling()
  if (liveInterval) {
    clearInterval(liveInterval)
    liveInterval = null
  }
  if (globalEnterHandler) {
    window.removeEventListener('keydown', globalEnterHandler)
    globalEnterHandler = null
  }

  if (map) {
    if (drawInteraction) map.removeInteraction(drawInteraction)
    map.setTarget(undefined)
    map = null
  }
})

function closePopup() {
  overlay?.setPosition(undefined)
  if (selectedFeature.value?._olFeature) {
    const prevType = selectedFeature.value.resourceType
    const prevEnriched = selectedFeature.value.enriched || false
    selectedFeature.value._olFeature.setStyle(getStyle(prevType, prevEnriched, selectedFeature.value.rawData))
  }
  selectedFeature.value = null
  stackedFeatures.value = []
  dscClearCard()
}

/**
 * Select a specific OL feature (from click or from stacked-feature picker).
 */
function selectOlFeature(feature: any) {
  const resourceType = feature.get('resourceType')
  const rawData = feature.get('rawData')
  const isEnriched = feature.get('enriched') || false
  const enrichmentSource = feature.get('enrichmentSource') || ''

  // ── Quick FUP update: clicking a gold dot while the SENREP panel is
  //    open in FUP/FINAL mode updates the form position directly.
  //    The operator can then just click Submit — no popup interaction.
  if (senrepPanelOpen.value
      && (senrepForm.value.reportType === 'FUP' || senrepForm.value.reportType === 'FINAL')
      && resourceType === 'locationEstimates'
      && rawData) {
    senrepForm.value.estimatedLat = rawData.estimatedLat ?? senrepForm.value.estimatedLat
    senrepForm.value.estimatedLon = rawData.estimatedLon ?? senrepForm.value.estimatedLon
    senrepForm.value.cep50_m = rawData.cep50_m ?? senrepForm.value.cep50_m
    senrepForm.value.numContributingLobs = rawData.numContributingLobs ?? senrepForm.value.numContributingLobs
    senrepForm.value.sourceFixObsId = rawData.observationId || senrepForm.value.sourceFixObsId
    senrepSuccess.value = false
    // Still show the popup so the operator can see what they clicked,
    // but the form is already updated — just click Submit.
  }

  // Reset previous selection style
  if (selectedFeature.value?._olFeature) {
    const prevType = selectedFeature.value.resourceType
    const prevEnriched = selectedFeature.value.enriched || false
    selectedFeature.value._olFeature.setStyle(getStyle(prevType, prevEnriched, selectedFeature.value.rawData))
  }

  // Highlight new selection
  ;(feature as Feature).setStyle(getSelectedStyle(resourceType, rawData))

  selectedFeature.value = {
    resourceType,
    resourceId: feature.get('resourceId'),
    resourceName: feature.get('resourceName'),
    rawData,
    enriched: isEnriched,
    enrichmentSource,
    _olFeature: feature,
  }

  // Compose deployed-system card if this is a deployment leaf
  if (isDeployedSystemLeaf(selectedFeature.value)) {
    dscComposeCard(selectedFeature.value, deploymentParentMap, deploymentItemById)
  } else {
    dscClearCard()
  }

  // Position popup
  const geom = (feature as Feature).getGeometry()
  if (geom) {
    let coord: Coordinate
    if (geom.getType() === 'Point') {
      coord = (geom as Point).getCoordinates()
    } else {
      coord = (geom as any).getInteriorPoint?.()?.getCoordinates?.() || (geom as any).getFirstCoordinate()
    }
    overlay?.setPosition(coord)
  }
}

/**
 * Pick a stacked feature by index (from the UI picker).
 */
function pickStackedFeature(idx: number) {
  const feat = stackedFeatures.value[idx]
  if (feat) selectOlFeature(feat._olFeature)
}

function goToDetail() {
  if (selectedFeature.value) {
    // Synthetic map types → navigate to the closest real resource type
    const typeMap: Record<string, string> = {
      observationPoints: 'observations',
      observationTracks: 'datastreams',
    }
    const resourceType = typeMap[selectedFeature.value.resourceType] || selectedFeature.value.resourceType
    router.push(`/explore/${resourceType}`)
  }
}

const totalFeatures = computed(() =>
  Object.values(featureCounts.value).reduce((sum, n) => sum + n, 0)
)

const creatingTest = ref(false)
const testCreated = ref(false)

async function createTestFeature() {
  creatingTest.value = true
  try {
    const timestamp = Date.now().toString(36)
    const payload = {
      type: 'Feature',
      properties: {
        uid: `urn:csapi-explorer:test:map-system-${timestamp}`,
        featureType: 'http://www.w3.org/ns/sosa/Platform',
        name: 'CSAPI Explorer — Map Test System',
        description: 'Test system created by CSAPI Explorer to demonstrate the map view. Safe to delete.',
      },
      geometry: {
        type: 'Point',
        coordinates: [-77.0369, 38.9072], // Washington DC
      },
    }

    const res = await apiFetch('/systems', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/geo+json',
      },
      body: JSON.stringify(payload),
    })

    if (res.ok) {
      testCreated.value = true
      // Reload to pick up the new feature
      await loadAllResources()
    } else {
      error.value = `Create failed: ${res.error || res.status}`
    }
  } catch (e: any) {
    error.value = e.message
  } finally {
    creatingTest.value = false
  }
}

// ─── TAK-style mobile panel ───
const mobilePanel = ref<'layers' | 'filters' | 'detail' | null>(null)

function toggleMobilePanel(panel: 'layers' | 'filters') {
  mobilePanel.value = mobilePanel.value === panel ? null : panel
}

function closeMobilePanel() {
  if (mobilePanel.value === 'detail' && window.innerWidth <= 768) {
    selectedFeature.value = null
    if (overlay) overlay.setPosition(undefined)
  }
  mobilePanel.value = null
}

function mobileSearch() {
  closeMobilePanel()
  loadAllResources()
}

function mobileStartBbox() {
  closeMobilePanel()
  startDrawBbox()
}

// Auto-show detail on mobile when feature selected
watch(selectedFeature, (feat) => {
  if (feat && window.innerWidth <= 768) {
    mobilePanel.value = 'detail'
  }
})
</script>

<template>
  <div v-if="connection.connected" class="map-page">
    <!-- Sidebar legend/controls -->
    <aside class="map-sidebar">
      <div class="sidebar-header">
        <span class="sidebar-title">Map Layers</span>
      </div>

      <div class="layer-controls">
        <div class="layer-section-label">Part 1 — Features</div>
        <button
          v-for="rt in SPATIAL_TYPES"
          :key="rt.key"
          :class="['layer-toggle', { inactive: !activeLayers[rt.key] }]"
          @click="toggleLayer(rt.key)"
        >
          <span class="layer-dot" :style="{ backgroundColor: TYPE_COLORS[rt.key] }"></span>
          <span class="layer-label">{{ rt.plural }}</span>
          <span class="layer-count">{{ featureCounts[rt.key] ?? '—' }}</span>
        </button>

        <div class="layer-section-label" style="margin-top: 0.5rem;">Part 2 — Dynamic Data</div>
        <button
          v-for="rt in [...PART2_MAP_TYPES, OBS_POINTS_ENTRY, OBS_TRACK_ENTRY, LOB_ENTRY]"
          :key="rt.key"
          :class="['layer-toggle', { inactive: !activeLayers[rt.key] }]"
          @click="toggleLayer(rt.key)"
        >
          <span class="layer-dot" :style="{ backgroundColor: TYPE_COLORS[rt.key] }"></span>
          <span class="layer-label">{{ rt.plural }}</span>
          <span class="layer-count">{{ featureCounts[rt.key] ?? '—' }}</span>
        </button>

        <div class="layer-section-label" style="margin-top: 0.5rem;">Overlays</div>
        <button
          :class="['layer-toggle', { inactive: !activeLayers['detectionRanges'] }]"
          @click="toggleLayer('detectionRanges')"
        >
          <span class="layer-dot" :style="{ backgroundColor: TYPE_COLORS['detectionRanges'] }"></span>
          <span class="layer-label">Detection Ranges</span>
          <span class="layer-count">{{ featureCounts['detectionRanges'] ?? '—' }}</span>
        </button>
        <button
          :class="['layer-toggle', { inactive: !activeLayers['locationEstimates'] }]"
          @click="toggleLayer('locationEstimates')"
        >
          <span class="layer-dot" :style="{ backgroundColor: TYPE_COLORS['locationEstimates'] }"></span>
          <span class="layer-label">Location Estimates</span>
          <span class="layer-count">{{ featureCounts['locationEstimates'] ?? '—' }}</span>
        </button>
        <button
          :class="['layer-toggle', { inactive: !activeLayers['senrepMarkers'] }]"
          @click="toggleLayer('senrepMarkers')"
        >
          <span class="layer-dot" :style="{ backgroundColor: TYPE_COLORS['senrepMarkers'] }"></span>
          <span class="layer-label">SENREP Reports</span>
          <span class="layer-count">{{ featureCounts['senrepMarkers'] ?? '—' }}</span>
        </button>
      </div>

      <!-- Data Sources (per-publisher observation toggle) -->
      <div v-if="discoveredObsSources.length > 0" class="source-controls">
        <div class="layer-section-label" style="margin-top: 0.5rem;">Data Sources</div>
        <button
          v-for="src in discoveredObsSources"
          :key="src.key"
          :class="['source-toggle', { inactive: activeObsSources[src.key] === false }]"
          @click="toggleObsSource(src.key)"
        >
          <span class="source-icon">{{ src.icon }}</span>
          <span class="source-dot" :style="{ backgroundColor: src.color }"></span>
          <span class="source-label">{{ src.label }}</span>
          <span class="source-count">{{ obsSourceCounts[src.key] ?? 0 }}</span>
        </button>
      </div>

      <!-- Enrichment info -->
      <div v-if="Object.values(enrichedCounts).some(c => c > 0)" class="enrichment-info">
        <span class="enriched-indicator"></span>
        <span class="enrichment-text">
          {{ Object.values(enrichedCounts).reduce((s, n) => s + n, 0) }} locations derived from observations
        </span>
      </div>

      <!-- Basemap toggle -->
      <div class="milsymbol-toggle">
        <label class="milsymbol-label">
          <input type="checkbox" v-model="useSatellite" @change="toggleBasemap" />
          <span>Satellite + Labels</span>
        </label>
      </div>

      <!-- Live Mode toggle -->
      <div class="milsymbol-toggle">
        <label class="milsymbol-label">
          <input type="checkbox" :checked="liveMode" @change="toggleLiveMode" />
          <span :style="liveMode ? { color: '#22c55e', fontWeight: 600 } : {}">Live Mode</span>
          <span v-if="liveMode" style="margin-left: 0.4rem; font-size: 0.7rem; color: #9ca3af;">
            {{ lastRefreshTime || '...' }}
          </span>
        </label>
      </div>

      <!-- MIL-STD-2525 symbol toggle -->
      <div class="milsymbol-toggle">
        <label class="milsymbol-label">
          <input type="checkbox" v-model="useMilSymbols" @change="refreshAllStyles" />
          <span>MIL-STD-2525 Symbols</span>
        </label>
      </div>

      <div class="sidebar-status">
        <template v-if="loading">
          <i class="pi pi-spin pi-spinner"></i> Loading resources...
        </template>
        <template v-else>
          {{ totalFeatures }} features on map
        </template>
      </div>

      <!-- Filters section -->
      <div class="filter-section">
        <div class="filter-section-label">
          <i class="pi pi-filter"></i> Filters
          <button v-if="hasAnyFilter" class="clear-all-btn" @click="clearAllFilters" :disabled="loading" title="Clear all filters">
            <i class="pi pi-times"></i> Clear all
          </button>
        </div>

        <!-- Keyword filter -->
        <div class="filter-item">
          <label class="filter-label">Keyword (q)</label>
          <input
            v-model="keywordFilter"
            type="text"
            placeholder="e.g. acoustic, camera"
            class="filter-input"
            @keyup.enter="loadAllResources"
          />
        </div>

        <!-- Temporal filter -->
        <div class="filter-item">
          <label class="filter-label">Date/time start</label>
          <input
            v-model="dtStart"
            type="datetime-local"
            class="filter-input"
          />
        </div>
        <div class="filter-item">
          <label class="filter-label">Date/time end</label>
          <input
            v-model="dtEnd"
            type="datetime-local"
            class="filter-input"
          />
        </div>

        <!-- Bbox spatial filter -->
        <div class="filter-item">
          <label class="filter-label">Spatial (bbox)</label>
          <div class="bbox-controls">
            <button
              :class="['bbox-draw-btn', { active: drawingBbox }]"
              @click="drawingBbox ? clearBbox() : startDrawBbox()"
              :disabled="loading"
            >
              <i :class="drawingBbox ? 'pi pi-times' : 'pi pi-stop'"></i>
              {{ drawingBbox ? 'Cancel' : 'Draw Bbox' }}
            </button>
            <template v-if="bboxFilter">
              <div class="bbox-active">
                <i class="pi pi-check-circle" style="color: #10b981;"></i>
                <span class="bbox-label">Bbox set</span>
                <button class="bbox-clear" @click="clearBbox" :disabled="loading" title="Clear bbox">
                  <i class="pi pi-times"></i>
                </button>
              </div>
              <div class="bbox-coords">
                {{ bboxFilter[0].toFixed(3) }}, {{ bboxFilter[1].toFixed(3) }} &rarr;
                {{ bboxFilter[2].toFixed(3) }}, {{ bboxFilter[3].toFixed(3) }}
              </div>
            </template>
          </div>
        </div>
      </div>

      <!-- Primary Search button -->
      <button class="search-btn" @click="loadAllResources" :disabled="loading">
        <i :class="loading ? 'pi pi-spin pi-spinner' : 'pi pi-search'"></i>
        {{ hasSearched ? 'Search Again' : 'Search' }}
      </button>

      <!-- Empty state message -->
      <div v-if="!loading && hasSearched && totalFeatures === 0" class="empty-state">
        <i class="pi pi-map-marker" style="font-size: 1.5rem; color: #94a3b8;"></i>
        <p><strong>No features with geometry found</strong></p>
        <p class="empty-detail">
          The server's resources currently have <code>null</code> geometry. 
          This is common for demo servers where sensor locations haven't been configured.
        </p>
        <p class="empty-detail">
          You can create a test system with a location to see the map in action:
        </p>
        <button
          class="create-test-btn"
          @click="createTestFeature"
          :disabled="creatingTest"
        >
          <i :class="creatingTest ? 'pi pi-spin pi-spinner' : 'pi pi-map-marker'"></i>
          {{ creatingTest ? 'Creating...' : 'Create Test System (Washington DC)' }}
        </button>
        <p v-if="testCreated" class="test-created-msg">
          <i class="pi pi-check-circle"></i> Test system created! It should appear on the map.
        </p>
        <p v-if="error" class="error-msg">
          <i class="pi pi-exclamation-triangle"></i> {{ error }}
        </p>
      </div>

      <!-- Weather observation detail panel (NWS / METAR) -->
      <div v-if="selectedFeature && !dscCard && !isDeployedSystemLeaf(selectedFeature) && isWeatherObservation(selectedFeature.rawData)" class="detail-panel weather-detail-panel">
        <div class="detail-header">
          <span class="detail-type-badge" style="background-color: #0ea5e9;">◆</span>
          <strong>{{ selectedFeature.rawData.result.stationName || selectedFeature.resourceName }}</strong>
        </div>
        <div class="weather-station-id">{{ selectedFeature.rawData.result.stationId }}</div>
        <div class="weather-hero">
          <span class="weather-hero-icon">{{ weatherIcon(selectedFeature.rawData.result.textDescription) }}</span>
          <div class="weather-hero-temp">
            {{ wxFmt(selectedFeature.rawData.result.temperature_c ?? selectedFeature.rawData.result.temp_c, 1) }}°C
            <span class="weather-hero-temp-f">({{ wxFmt((selectedFeature.rawData.result.temperature_c ?? selectedFeature.rawData.result.temp_c) * 9 / 5 + 32, 1) }}°F)</span>
          </div>
          <div class="weather-hero-desc">{{ selectedFeature.rawData.result.textDescription || selectedFeature.rawData.result.flight_category || 'N/A' }}</div>
        </div>
        <div class="weather-fields">
          <div class="weather-field">
            <span class="weather-field-label">💧 Humidity</span>
            <span>{{ wxFmt(selectedFeature.rawData.result.humidity_pct) }}%</span>
          </div>
          <div class="weather-field">
            <span class="weather-field-label">🌡️ Dewpoint</span>
            <span>{{ wxFmt(selectedFeature.rawData.result.dewpoint_c ?? selectedFeature.rawData.result.dewp_c, 1) }}°C</span>
          </div>
          <div class="weather-field">
            <span class="weather-field-label">💨 Wind</span>
            <span>{{ wxFmt(selectedFeature.rawData.result.wind_speed_kmh ?? (selectedFeature.rawData.result.wind_speed_kt ? selectedFeature.rawData.result.wind_speed_kt * 1.852 : undefined)) }} km/h {{ windArrow(selectedFeature.rawData.result.wind_direction_deg ?? selectedFeature.rawData.result.wind_dir_deg) }}</span>
          </div>
          <div v-if="wxFmt(selectedFeature.rawData.result.wind_gust_kmh) !== '—'" class="weather-field">
            <span class="weather-field-label">💨 Gusts</span>
            <span>{{ wxFmt(selectedFeature.rawData.result.wind_gust_kmh) }} km/h</span>
          </div>
          <div class="weather-field">
            <span class="weather-field-label">📊 Pressure</span>
            <span>{{ wxFmt(selectedFeature.rawData.result.barometric_pressure_pa ? selectedFeature.rawData.result.barometric_pressure_pa / 100 : selectedFeature.rawData.result.slp_hpa, 1) }} hPa</span>
          </div>
          <div class="weather-field">
            <span class="weather-field-label">👁️ Visibility</span>
            <span>{{ wxFmt(selectedFeature.rawData.result.visibility_m ? selectedFeature.rawData.result.visibility_m / 1000 : (selectedFeature.rawData.result.visibility_sm ? selectedFeature.rawData.result.visibility_sm * 1.609 : undefined), 1) }} km</span>
          </div>
          <div class="weather-field">
            <span class="weather-field-label">⛰️ Elevation</span>
            <span>{{ wxFmt(selectedFeature.rawData.result.elev_m) }} m</span>
          </div>
        </div>
        <div v-if="selectedFeature.rawData.phenomenonTime" class="weather-time">
          <i class="pi pi-clock"></i> {{ selectedFeature.rawData.phenomenonTime }}
        </div>
        <details v-if="selectedFeature.rawData.result.rawMessage" class="weather-metar-details">
          <summary>Raw METAR</summary>
          <pre class="weather-metar-pre">{{ selectedFeature.rawData.result.rawMessage }}</pre>
        </details>
        <button class="detail-link-btn" @click="goToDetail">
          <i class="pi pi-external-link"></i> View in Explorer
        </button>
      </div>

      <!-- Aircraft observation detail panel (ADS-B / OpenSky) -->
      <div v-if="selectedFeature && !dscCard && !isDeployedSystemLeaf(selectedFeature) && isAircraftObservation(selectedFeature.rawData)" class="detail-panel aircraft-detail-panel">
        <div class="detail-header">
          <span class="detail-type-badge" style="background-color: #3b82f6;">✈</span>
          <strong>{{ selectedFeature.rawData.result.callsign?.trim() || selectedFeature.rawData.result.icao24 }}</strong>
        </div>
        <div class="aircraft-icao">ICAO24: {{ selectedFeature.rawData.result.icao24 }}</div>
        <div class="aircraft-hero">
          <div class="aircraft-hero-heading">
            <span class="aircraft-heading-arrow" :style="{ transform: `rotate(${selectedFeature.rawData.result.true_track_deg || 0}deg)` }">▲</span>
            <span>{{ typeof selectedFeature.rawData.result.true_track_deg === 'number' ? selectedFeature.rawData.result.true_track_deg.toFixed(1) + '°' : '—' }}</span>
          </div>
          <div class="aircraft-hero-alt">
            {{ altFmt(selectedFeature.rawData.result.baro_altitude_m) }}
          </div>
          <div class="aircraft-hero-status">
            {{ selectedFeature.rawData.result.on_ground === 'true' || selectedFeature.rawData.result.on_ground === true ? '🛬 On Ground' : '✈️ Airborne' }}
          </div>
        </div>
        <div class="aircraft-fields">
          <div class="aircraft-field">
            <span class="aircraft-field-label">🏎️ Speed</span>
            <span>{{ spdFmt(selectedFeature.rawData.result.velocity_ms) }}</span>
          </div>
          <div class="aircraft-field">
            <span class="aircraft-field-label">📐 Heading</span>
            <span>{{ typeof selectedFeature.rawData.result.true_track_deg === 'number' ? selectedFeature.rawData.result.true_track_deg.toFixed(1) + '°' : '—' }}</span>
          </div>
          <div class="aircraft-field">
            <span class="aircraft-field-label">⬆️ Baro Alt</span>
            <span>{{ altFmt(selectedFeature.rawData.result.baro_altitude_m) }}</span>
          </div>
          <div class="aircraft-field">
            <span class="aircraft-field-label">🌍 Geo Alt</span>
            <span>{{ altFmt(selectedFeature.rawData.result.geo_altitude_m) }}</span>
          </div>
          <div class="aircraft-field">
            <span class="aircraft-field-label">↕️ Vert Rate</span>
            <span>{{ selectedFeature.rawData.result.vertical_rate_ms != null && selectedFeature.rawData.result.vertical_rate_ms !== 'NaN' ? Number(selectedFeature.rawData.result.vertical_rate_ms).toFixed(1) + ' m/s' : '—' }}</span>
          </div>
          <div class="aircraft-field">
            <span class="aircraft-field-label">🌐 Country</span>
            <span>{{ selectedFeature.rawData.result.origin_country || '—' }}</span>
          </div>
          <div v-if="selectedFeature.rawData.result.squawk" class="aircraft-field">
            <span class="aircraft-field-label">📟 Squawk</span>
            <span>{{ selectedFeature.rawData.result.squawk }}</span>
          </div>
          <div class="aircraft-field">
            <span class="aircraft-field-label">📡 Source</span>
            <span>{{ selectedFeature.rawData.result.position_source || 'ADS-B' }}</span>
          </div>
        </div>
        <div class="aircraft-how-it-works">
          <details>
            <summary>How is this data collected?</summary>
            <p>
              Aircraft with Mode S transponders continuously broadcast their GPS position,
              altitude, speed, and heading on 1090 MHz via ADS-B (Automatic Dependent
              Surveillance–Broadcast). The OpenSky Network collects these broadcasts using
              ~30,000 crowd-sourced ground receivers worldwide. This system queries the
              OpenSky REST API every 5 minutes for all aircraft over southern Arizona.
            </p>
          </details>
        </div>
        <div v-if="selectedFeature.rawData.phenomenonTime" class="aircraft-time">
          <i class="pi pi-clock"></i> {{ selectedFeature.rawData.phenomenonTime }}
        </div>
        <button class="detail-link-btn" @click="goToDetail">
          <i class="pi pi-external-link"></i> View in Explorer
        </button>
      </div>

      <!-- Detail panel when a feature is selected (non-deployment features only) -->
      <div v-if="selectedFeature && !dscCard && !isDeployedSystemLeaf(selectedFeature) && !isWeatherObservation(selectedFeature.rawData) && !isAircraftObservation(selectedFeature.rawData)" class="detail-panel">
        <template>
        <div class="detail-header">
          <span class="detail-type-badge" :style="{ backgroundColor: TYPE_COLORS[selectedFeature.resourceType] }">
            {{ TYPE_LABELS[selectedFeature.resourceType] }}
          </span>
          <strong>{{ selectedFeature.resourceName }}</strong>
        </div>
        <div class="detail-field">
          <span class="field-label">Type:</span>
          {{ MAP_TYPES.find(r => r.key === selectedFeature.resourceType)?.label }}
        </div>
        <div v-if="selectedFeature.enriched" class="enrichment-banner">
          <i class="pi pi-info-circle"></i>
          <span>Location derived from observation data</span>
          <small v-if="selectedFeature.enrichmentSource">{{ selectedFeature.enrichmentSource }}</small>
        </div>
        <div class="detail-field">
          <span class="field-label">ID:</span>
          <code>{{ selectedFeature.resourceId }}</code>
        </div>
        <!-- Observation-specific fields -->
        <div v-if="selectedFeature.rawData?.phenomenonTime" class="detail-field">
          <span class="field-label">Time:</span>
          {{ selectedFeature.rawData.phenomenonTime }}
        </div>
        <div v-if="selectedFeature.rawData?.lat != null" class="detail-field">
          <span class="field-label">Location:</span>
          {{ selectedFeature.rawData.lat.toFixed(6) }}°, {{ selectedFeature.rawData.lon.toFixed(6) }}°
          <span v-if="selectedFeature.rawData.alt != null" style="color: #64748b;">
            ({{ selectedFeature.rawData.alt.toFixed(1) }}m)
          </span>
        </div>
        <div v-if="selectedFeature.rawData?.datastreamName" class="detail-field">
          <span class="field-label">Datastream:</span>
          {{ selectedFeature.rawData.datastreamName }}
        </div>
        <div v-if="selectedFeature.rawData?.properties?.description || selectedFeature.rawData?.description" class="detail-field">
          <span class="field-label">Description:</span>
          {{ selectedFeature.rawData?.properties?.description || selectedFeature.rawData?.description }}
        </div>
        <div v-if="selectedFeature.rawData?.properties?.uid || selectedFeature.rawData?.uniqueId" class="detail-field">
          <span class="field-label">UID:</span>
          <code class="uid">{{ selectedFeature.rawData?.properties?.uid || selectedFeature.rawData?.uniqueId }}</code>
        </div>
        <button class="detail-link-btn" @click="goToDetail">
          <i class="pi pi-external-link"></i> View in Explorer
        </button>
        <details class="raw-json">
          <summary>Raw JSON</summary>
          <pre>{{ JSON.stringify(selectedFeature.rawData, null, 2) }}</pre>
        </details>
        </template>
      </div>
    </aside>

    <!-- Map -->
    <div class="map-area">
      <div ref="mapContainer" class="map-container"></div>
      <div v-if="mouseCoords" class="coord-display">{{ mouseCoords }}</div>

      <!-- Popup overlay (attached to OL overlay, positioned on map) -->
      <div ref="popupContainer" class="ol-popup">
        <a href="#" class="ol-popup-closer" @click.prevent="closePopup"></a>
        <div v-if="selectedFeature" class="popup-content">
          <span class="popup-badge" :style="{ backgroundColor: TYPE_COLORS[selectedFeature.resourceType] }">
            {{ TYPE_LABELS[selectedFeature.resourceType] }}
          </span>
          <strong>{{ selectedFeature.resourceName }}</strong>
          <div v-if="selectedFeature.rawData?.phenomenonTime" class="popup-id">{{ selectedFeature.rawData.phenomenonTime }}</div>
          <div v-else class="popup-id">{{ selectedFeature.resourceId }}</div>
          <!-- Stacked-feature picker — shown when multiple features share the same pixel -->
          <div v-if="stackedFeatures.length > 1" class="stacked-picker">
            <div class="stacked-label">{{ stackedFeatures.length }} features here:</div>
            <button
              v-for="(sf, i) in stackedFeatures"
              :key="sf.resourceId"
              class="stacked-btn"
              :class="{ 'stacked-btn--active': selectedFeature?.resourceId === sf.resourceId }"
              @click.stop="pickStackedFeature(i)"
            >
              {{ sf.resourceName || sf.resourceId }}
            </button>
          </div>
          <!-- SENREP popup extra info -->
          <template v-if="selectedFeature.resourceType === 'senrepMarkers' && selectedFeature.rawData">
            <div class="popup-senrep-detail">
              <div>{{ selectedFeature.rawData.classification }} — {{ selectedFeature.rawData.reportType || 'INIT' }}</div>
              <div>{{ selectedFeature.rawData.estimatedLat?.toFixed(5) }}°N, {{ selectedFeature.rawData.estimatedLon?.toFixed(5) }}°W</div>
              <div v-if="selectedFeature.rawData.senderId">Operator: {{ selectedFeature.rawData.senderId }}</div>
              <div v-if="selectedFeature.rawData.comments">{{ selectedFeature.rawData.comments }}</div>
            </div>
          </template>
          <!-- Weather observation popup (NWS / METAR) -->
          <template v-if="isWeatherObservation(selectedFeature.rawData)">
            <div class="popup-weather-detail">
              <div class="popup-weather-conditions">
                <span class="popup-weather-icon">{{ weatherIcon(selectedFeature.rawData.result.textDescription) }}</span>
                <span class="popup-weather-desc">{{ selectedFeature.rawData.result.textDescription || selectedFeature.rawData.result.flight_category || 'N/A' }}</span>
              </div>
              <div class="popup-weather-temp">
                {{ wxFmt(selectedFeature.rawData.result.temperature_c ?? selectedFeature.rawData.result.temp_c, 1) }}°C
                <span class="popup-weather-temp-f">({{ wxFmt((selectedFeature.rawData.result.temperature_c ?? selectedFeature.rawData.result.temp_c) * 9 / 5 + 32, 1) }}°F)</span>
              </div>
              <div class="popup-weather-grid">
                <span title="Wind">💨 {{ wxFmt(selectedFeature.rawData.result.wind_speed_kmh ?? (selectedFeature.rawData.result.wind_speed_kt ? selectedFeature.rawData.result.wind_speed_kt * 1.852 : undefined)) }} km/h {{ windArrow(selectedFeature.rawData.result.wind_direction_deg ?? selectedFeature.rawData.result.wind_dir_deg) }}</span>
                <span title="Humidity">💧 {{ wxFmt(selectedFeature.rawData.result.humidity_pct) }}%</span>
              </div>
              <div v-if="selectedFeature.rawData.result.rawMessage" class="popup-weather-metar">
                {{ selectedFeature.rawData.result.rawMessage }}
              </div>
            </div>
          </template>
          <!-- Aircraft observation popup (ADS-B / OpenSky) -->
          <template v-if="isAircraftObservation(selectedFeature.rawData)">
            <div class="popup-aircraft-detail">
              <div class="popup-aircraft-id">
                {{ selectedFeature.rawData.result.callsign?.trim() || selectedFeature.rawData.result.icao24 }}
                <span class="popup-aircraft-country">{{ selectedFeature.rawData.result.origin_country }}</span>
              </div>
              <div class="popup-aircraft-grid">
                <span title="Altitude">⬆️ {{ altFmt(selectedFeature.rawData.result.baro_altitude_m) }}</span>
                <span title="Speed">🏎️ {{ spdFmt(selectedFeature.rawData.result.velocity_ms) }}</span>
                <span title="Heading">📐 {{ typeof selectedFeature.rawData.result.true_track_deg === 'number' ? selectedFeature.rawData.result.true_track_deg.toFixed(1) + '°' : '—' }}</span>
                <span title="Status">{{ selectedFeature.rawData.result.on_ground === 'true' || selectedFeature.rawData.result.on_ground === true ? '🛬 Ground' : '✈️ Airborne' }}</span>
              </div>
            </div>
          </template>
          <!-- Earthquake observation popup (USGS) -->
          <template v-if="isEarthquakeObservation(selectedFeature.rawData)">
            <div class="popup-earthquake-detail">
              <div class="popup-eq-header">
                <span
                  class="popup-eq-mag-badge"
                  :style="{ backgroundColor: eqMagColor(Number(selectedFeature.rawData.result.magnitude) || 0) }"
                >
                  M{{ typeof selectedFeature.rawData.result.magnitude === 'number' ? selectedFeature.rawData.result.magnitude.toFixed(1) : selectedFeature.rawData.result.magnitude }}
                </span>
                <span class="popup-eq-severity">
                  {{ eqMagLabel(Number(selectedFeature.rawData.result.magnitude) || 0) }}
                  <span v-if="selectedFeature.rawData.result.magType" class="popup-eq-magtype">({{ selectedFeature.rawData.result.magType }})</span>
                </span>
              </div>
              <div class="popup-eq-place">📍 {{ selectedFeature.rawData.result.place || 'Unknown location' }}</div>
              <div class="popup-eq-grid">
                <span title="Depth">⬇️ {{ typeof selectedFeature.rawData.result.depth_km === 'number' ? selectedFeature.rawData.result.depth_km.toFixed(1) + ' km' : '—' }}</span>
                <span title="Status">{{ selectedFeature.rawData.result.status === 'reviewed' ? '✅ Reviewed' : '🤖 Automatic' }}</span>
                <span v-if="selectedFeature.rawData.result.eventTime" title="Time">🕐 {{ eqTimeAgo(selectedFeature.rawData.result.eventTime) }}</span>
              </div>
              <a
                v-if="selectedFeature.rawData.result.detailUrl"
                :href="selectedFeature.rawData.result.detailUrl.replace('/fdsnws/event/1/query?eventid=', '/earthquakes/eventpage/')"
                target="_blank"
                rel="noopener"
                class="popup-eq-usgs-link"
              >
                🌐 View on USGS
              </a>
            </div>
          </template>
          <!-- BuoyCAM / NIMS image observation popup -->
          <template v-if="selectedFeature.rawData?.result?.mediaType?.startsWith('image/') && selectedFeature.rawData?.result?.imageUrl">
            <div class="popup-buoycam-detail">
              <a :href="selectedFeature.rawData.result.imageUrl" target="_blank" rel="noopener" title="Open full image">
                <img :src="selectedFeature.rawData.result.thumbUrl || selectedFeature.rawData.result.imageUrl" alt="Camera" class="popup-buoycam-img" loading="lazy" />
              </a>
              <div class="popup-buoycam-meta">
                📷 {{ selectedFeature.rawData.result.cameraStatus || selectedFeature.rawData.result.camId || 'ok' }}
                · {{ Math.round((selectedFeature.rawData.result.contentLength || 0) / 1024) || '' }} {{ selectedFeature.rawData.result.contentLength ? 'KB' : '' }}
              </div>
              <a
                v-if="selectedFeature.rawData.result.timeLapseUrl"
                :href="selectedFeature.rawData.result.timeLapseUrl"
                target="_blank"
                rel="noopener"
                class="popup-timelapse-link"
              >
                ▶ Timelapse
              </a>
            </div>
          </template>
          <!-- "Submit SENREP" button on gold dot popup -->
          <button
            v-if="selectedFeature.resourceType === 'locationEstimates' && selectedFeature.rawData"
            class="senrep-popup-btn"
            @click="openSenrepPanel(selectedFeature.rawData); closePopup()"
          >
            <i class="pi pi-flag"></i> Submit SENREP
          </button>
        </div>
      </div>

      <!-- ═══ Deployed System Card — floating right-side panel ═══ -->
      <transition name="dsc-slide">
        <div v-if="selectedFeature && (dscCard || (dscLoading && isDeployedSystemLeaf(selectedFeature)))" class="dsc-float-panel">
          <div class="dsc-float-header">
            <span class="dsc-float-title">
              <i class="pi pi-id-card" style="color: #3b82f6;"></i> Deployed System
            </span>
            <button class="dsc-float-close" @click="closePopup" title="Close">
              <i class="pi pi-times"></i>
            </button>
          </div>
          <div class="dsc-float-body">
            <div v-if="dscLoading && !dscCard" class="dsc-inline-loading">
              <i class="pi pi-spin pi-spinner"></i>
              <span>Loading system details…</span>
            </div>
            <DeployedSystemCard
              v-if="dscCard"
              :card="dscCard"
              :loading="dscLoading"
              @explore="goToDetail"
              @close="closePopup"
            />
          </div>
        </div>
      </transition>

      <!-- ═══ SENREP Slide-out Panel ═══ -->
      <transition name="senrep-slide">
        <div v-if="senrepPanelOpen" class="senrep-panel">
          <div class="senrep-panel-header">
            <span class="senrep-panel-title">
              <i class="pi pi-flag" style="color: #ef4444;"></i> Submit SENREP
            </span>
            <button class="senrep-panel-close" @click="senrepPanelOpen = false">
              <i class="pi pi-times"></i>
            </button>
          </div>
          <div class="senrep-panel-body">
            <!-- Operator initials -->
            <label class="senrep-label">Operator</label>
            <input v-model="operatorInitials" class="senrep-input" maxlength="3" placeholder="XX"
              @change="localStorage.setItem('os4csapi-operator-initials', operatorInitials)" />

            <!-- Contact ID -->
            <label class="senrep-label">Contact ID</label>
            <input v-model="senrepForm.contactId" class="senrep-input" />

            <!-- Classification -->
            <label class="senrep-label">Classification</label>
            <select v-model="senrepForm.classification" class="senrep-input">
              <option>UAS</option>
              <option>rotary-wing</option>
              <option>fixed-wing</option>
              <option>unknown</option>
            </select>

            <!-- Report type -->
            <label class="senrep-label">Report Type</label>
            <select v-model="senrepForm.reportType" class="senrep-input" @change="onReportTypeChange">
              <option value="INIT">INIT — Initial Report</option>
              <option value="FUP" :disabled="!myContacts.length">FUP — Follow-Up</option>
              <option value="FINAL" :disabled="!myContacts.length">FINAL — Close Contact</option>
            </select>

            <!-- Contact ID picker (FUP / FINAL only — filtered to this operator's contacts) -->
            <template v-if="senrepForm.reportType === 'FUP' || senrepForm.reportType === 'FINAL'">
              <label class="senrep-label">Follow-up Contact</label>
              <select v-model="senrepForm.contactId" class="senrep-input">
                <option v-for="cid in myContacts" :key="cid" :value="cid">{{ cid }}</option>
              </select>
            </template>

            <!-- Read-only fields from gold dot -->
            <label class="senrep-label">Position (from fix)</label>
            <div class="senrep-readonly">
              {{ senrepForm.estimatedLat.toFixed(5) }}°N, {{ senrepForm.estimatedLon.toFixed(5) }}°W
            </div>

            <label class="senrep-label">CEP50</label>
            <div class="senrep-readonly">{{ senrepForm.cep50_m.toFixed(1) }}m</div>

            <label class="senrep-label">Contributing LOBs</label>
            <div class="senrep-readonly">{{ senrepForm.numContributingLobs }}</div>

            <!-- Operator notes -->
            <label class="senrep-label">Operator Notes</label>
            <textarea v-model="senrepForm.operatorNotes" class="senrep-textarea" rows="3" placeholder="Optional notes..."></textarea>

            <!-- Submit button -->
            <button class="senrep-submit-btn" :disabled="senrepSubmitting" @click="submitSenrep">
              <i :class="senrepSubmitting ? 'pi pi-spin pi-spinner' : 'pi pi-send'"></i>
              {{ senrepSubmitting ? 'Submitting...' : 'Submit Report' }}
            </button>
            <div v-if="senrepSuccess" class="senrep-success">
              <i class="pi pi-check-circle"></i> SENREP submitted successfully!
            </div>

            <!-- Provenance (collapsed) -->
            <details class="senrep-provenance">
              <summary>Provenance</summary>
              <div class="senrep-readonly" style="font-size: 0.7rem;">
                Source Fix: {{ senrepForm.sourceFixObsId || '—' }}<br/>
                DS: {{ SENREP_DS_ID }}
              </div>
            </details>
          </div>
        </div>
      </transition>

      <!-- ═══ Simulator / Reset floating controls ═══ -->
      <div class="sim-control-bar">
        <button
          v-if="!simRunning"
          class="sim-btn sim-btn--start"
          :disabled="simStarting"
          @click="startSimulator"
          title="Start data simulator"
        >
          <i :class="simStarting ? 'pi pi-spin pi-spinner' : 'pi pi-play'"></i>
          {{ simStarting ? 'Starting…' : 'Start Simulator' }}
        </button>
        <span v-else class="sim-msg">Simulation started</span>
        <button
          v-if="!simRunning"
          class="sim-btn sim-btn--reset"
          :disabled="demoResetting"
          @click="fullDemoReset"
          title="Full demo reset"
        >
          <i :class="demoResetting ? 'pi pi-spin pi-spinner' : 'pi pi-refresh'"></i>
          {{ demoResetting ? 'Resetting…' : 'Full Reset' }}
        </button>
        <span v-if="simMessage" class="sim-msg">{{ simMessage }}</span>
      </div>

      <!-- ═══ TAK-style mobile controls (hidden on desktop via CSS) ═══ -->
      <div class="tak-overlay">
        <!-- Top-left status -->
        <div class="tak-status" v-if="loading || hasSearched">
          <template v-if="loading">
            <i class="pi pi-spin pi-spinner"></i> LOADING…
          </template>
          <template v-else>{{ totalFeatures }} FEATURES</template>
        </div>

        <!-- Right-side FABs -->
        <div class="tak-fab-group">
          <!-- Sim controls (mobile only) -->
          <button v-if="!simRunning" class="tak-fab tak-fab--sim-start"
            :disabled="simStarting" @click="startSimulator" title="Start Simulator">
            <i :class="simStarting ? 'pi pi-spin pi-spinner' : 'pi pi-play'"></i>
          </button>
          <button v-if="!simRunning" class="tak-fab tak-fab--reset"
            :disabled="demoResetting" @click="fullDemoReset" title="Full Reset">
            <i :class="demoResetting ? 'pi pi-spin pi-spinner' : 'pi pi-refresh'"></i>
          </button>
          <span v-if="simRunning" class="tak-fab tak-fab--sim-running" title="Simulation Running">SIM</span>
          <button class="tak-fab" :class="{ active: mobilePanel === 'layers' }"
            @click="toggleMobilePanel('layers')" title="Layers">
            <i class="pi pi-images"></i>
          </button>
          <button class="tak-fab" :class="{ active: mobilePanel === 'filters' }"
            @click="toggleMobilePanel('filters')" title="Filters">
            <i class="pi pi-filter"></i>
          </button>
          <button class="tak-fab" @click="mobileSearch" :disabled="loading" title="Search">
            <i :class="loading ? 'pi pi-spin pi-spinner' : 'pi pi-search'"></i>
          </button>
          <button class="tak-fab" @click="useSatellite = !useSatellite; toggleBasemap()" title="Basemap">
            <i class="pi pi-globe"></i>
          </button>
          <button class="tak-fab" @click="useMilSymbols = !useMilSymbols; refreshAllStyles()" title="Symbols">
            <i class="pi pi-shield"></i>
          </button>
          <button class="tak-fab" :class="{ 'tak-fab--live': liveMode }" @click="toggleLiveMode" title="Live Mode">
            <i class="pi pi-bolt"></i>
          </button>
          <button class="tak-fab tak-fab--senrep" :class="{ active: senrepPanelOpen }" @click="openSenrepPanel(null); closeMobilePanel()" title="SENREP">
            <i class="pi pi-flag"></i>
          </button>
        </div>
      </div>

      <!-- TAK bottom sheet -->
      <transition name="tak-slide">
        <div v-if="mobilePanel" class="tak-backdrop" @click.self="closeMobilePanel">
          <div class="tak-sheet" :class="'tak-sheet--' + mobilePanel">
            <div class="tak-sheet-handle" @click="closeMobilePanel"></div>
            <div class="tak-sheet-header">
              <span class="tak-sheet-title">
                {{ mobilePanel === 'layers' ? 'LAYERS' : mobilePanel === 'filters' ? 'FILTERS' : 'DETAIL' }}
              </span>
              <button class="tak-sheet-close" @click="closeMobilePanel">
                <i class="pi pi-times"></i>
              </button>
            </div>

            <!-- Layers content -->
            <div v-if="mobilePanel === 'layers'" class="tak-sheet-body">
              <div class="tak-layer-grid">
                <button v-for="rt in MAP_TYPES" :key="rt.key"
                  :class="['tak-layer-chip', { inactive: !activeLayers[rt.key] }]"
                  @click="toggleLayer(rt.key)">
                  <span class="tak-layer-dot" :style="{ backgroundColor: TYPE_COLORS[rt.key] }"></span>
                  <span class="tak-layer-name">{{ rt.label }}</span>
                  <span class="tak-layer-count">{{ featureCounts[rt.key] ?? '—' }}</span>
                </button>
              </div>
              <div v-if="Object.values(enrichedCounts).some(c => c > 0)" class="tak-enrichment">
                {{ Object.values(enrichedCounts).reduce((s, n) => s + n, 0) }} locations from observations
              </div>
              <!-- Mobile Data Sources -->
              <div v-if="discoveredObsSources.length > 0" class="tak-source-section">
                <div class="tak-source-heading">Data Sources</div>
                <div class="tak-layer-grid">
                  <button v-for="src in discoveredObsSources" :key="src.key"
                    :class="['tak-layer-chip', { inactive: activeObsSources[src.key] === false }]"
                    @click="toggleObsSource(src.key)">
                    <span class="tak-source-icon">{{ src.icon }}</span>
                    <span class="tak-layer-name">{{ src.label }}</span>
                    <span class="tak-layer-count">{{ obsSourceCounts[src.key] ?? 0 }}</span>
                  </button>
                </div>
              </div>
              <div class="tak-live-row">
                <button :class="['tak-live-btn', { active: liveMode }]" @click="toggleLiveMode">
                  <i class="pi pi-bolt"></i>
                  {{ liveMode ? 'LIVE' : 'Live Mode' }}
                </button>
                <span v-if="liveMode" class="tak-live-ts">{{ lastRefreshTime || '...' }}</span>
              </div>
            </div>

            <!-- Filters content -->
            <div v-if="mobilePanel === 'filters'" class="tak-sheet-body">
              <div class="tak-filter-row">
                <label>Keyword</label>
                <input v-model="keywordFilter" type="text" placeholder="e.g. acoustic" class="tak-input"
                  @keyup.enter="mobileSearch" />
              </div>
              <div class="tak-filter-row tak-filter-dates">
                <div>
                  <label>Start</label>
                  <input v-model="dtStart" type="datetime-local" class="tak-input" />
                </div>
                <div>
                  <label>End</label>
                  <input v-model="dtEnd" type="datetime-local" class="tak-input" />
                </div>
              </div>
              <div class="tak-filter-row">
                <label>Spatial</label>
                <div class="tak-bbox-row">
                  <button class="tak-bbox-btn" :class="{ active: drawingBbox }"
                    @click="drawingBbox ? clearBbox() : mobileStartBbox()">
                    <i :class="drawingBbox ? 'pi pi-times' : 'pi pi-stop'"></i>
                    {{ drawingBbox ? 'Cancel' : 'Draw Bbox' }}
                  </button>
                  <span v-if="bboxFilter" class="tak-bbox-set">
                    <i class="pi pi-check-circle"></i> Set
                    <button class="tak-bbox-clear" @click="clearBbox"><i class="pi pi-times"></i></button>
                  </span>
                </div>
                <div v-if="bboxFilter" class="tak-bbox-coords">
                  {{ bboxFilter[0].toFixed(3) }},{{ bboxFilter[1].toFixed(3) }} &rarr;
                  {{ bboxFilter[2].toFixed(3) }},{{ bboxFilter[3].toFixed(3) }}
                </div>
              </div>
              <button v-if="hasAnyFilter" class="tak-clear-all" @click="clearAllFilters">
                <i class="pi pi-times"></i> Clear All Filters
              </button>
              <button class="tak-search-btn" @click="mobileSearch" :disabled="loading">
                <i :class="loading ? 'pi pi-spin pi-spinner' : 'pi pi-search'"></i>
                {{ hasSearched ? 'Search Again' : 'Search' }}
              </button>
            </div>

            <!-- Detail content -->
            <div v-if="mobilePanel === 'detail' && selectedFeature && dscCard" class="tak-sheet-body">
              <DeployedSystemCard
                :card="dscCard"
                :loading="dscLoading"
                @explore="goToDetail"
                @close="closePopup"
              />
            </div>
            <!-- Weather observation mobile detail -->
            <div v-else-if="mobilePanel === 'detail' && selectedFeature && isWeatherObservation(selectedFeature.rawData)" class="tak-sheet-body">
              <div class="tak-detail-header">
                <span class="tak-detail-badge" style="background-color: #0ea5e9;">◆</span>
                <strong>{{ selectedFeature.rawData.result.stationName || selectedFeature.resourceName }}</strong>
              </div>
              <div class="weather-station-id" style="margin: 0.2rem 0 0.5rem;">{{ selectedFeature.rawData.result.stationId }}</div>
              <div class="weather-hero" style="margin-bottom: 0.5rem;">
                <span class="weather-hero-icon">{{ weatherIcon(selectedFeature.rawData.result.textDescription) }}</span>
                <div class="weather-hero-temp">
                  {{ wxFmt(selectedFeature.rawData.result.temperature_c, 1) }}°C
                  <span class="weather-hero-temp-f">({{ wxFmt(selectedFeature.rawData.result.temperature_c * 9 / 5 + 32, 1) }}°F)</span>
                </div>
                <div class="weather-hero-desc">{{ selectedFeature.rawData.result.textDescription || 'N/A' }}</div>
              </div>
              <div class="weather-fields">
                <div class="weather-field">
                  <span class="weather-field-label">💧 Humidity</span>
                  <span>{{ wxFmt(selectedFeature.rawData.result.humidity_pct) }}%</span>
                </div>
                <div class="weather-field">
                  <span class="weather-field-label">💨 Wind</span>
                  <span>{{ wxFmt(selectedFeature.rawData.result.wind_speed_kmh) }} km/h {{ windArrow(selectedFeature.rawData.result.wind_direction_deg) }}</span>
                </div>
                <div class="weather-field">
                  <span class="weather-field-label">📊 Pressure</span>
                  <span>{{ wxFmt(selectedFeature.rawData.result.barometric_pressure_pa / 100, 1) }} hPa</span>
                </div>
                <div class="weather-field">
                  <span class="weather-field-label">👁️ Visibility</span>
                  <span>{{ wxFmt(selectedFeature.rawData.result.visibility_m / 1000, 1) }} km</span>
                </div>
              </div>
              <div v-if="selectedFeature.rawData.phenomenonTime" class="weather-time" style="margin-top: 0.5rem;">
                <i class="pi pi-clock"></i> {{ selectedFeature.rawData.phenomenonTime }}
              </div>
              <button class="tak-explore-btn" @click="goToDetail">
                <i class="pi pi-external-link"></i> View in Explorer
              </button>
            </div>
            <div v-else-if="mobilePanel === 'detail' && selectedFeature" class="tak-sheet-body">
              <div v-if="dscLoading && isDeployedSystemLeaf(selectedFeature)" class="dsc-inline-loading">
                <i class="pi pi-spin pi-spinner"></i>
                <span>Loading deployed system details…</span>
              </div>
              <template v-else>
              <div class="tak-detail-header">
                <span class="tak-detail-badge" :style="{ backgroundColor: TYPE_COLORS[selectedFeature.resourceType] }">
                  {{ TYPE_LABELS[selectedFeature.resourceType] }}
                </span>
                <strong>{{ selectedFeature.resourceName }}</strong>
              </div>
              <div class="tak-detail-fields">
                <div class="tak-detail-field">
                  <span class="tak-field-label">Type</span>
                  {{ MAP_TYPES.find(r => r.key === selectedFeature.resourceType)?.label }}
                </div>
                <div class="tak-detail-field">
                  <span class="tak-field-label">ID</span>
                  <code>{{ selectedFeature.resourceId }}</code>
                </div>
                <div v-if="selectedFeature.rawData?.phenomenonTime" class="tak-detail-field">
                  <span class="tak-field-label">Time</span>
                  {{ selectedFeature.rawData.phenomenonTime }}
                </div>
                <div v-if="selectedFeature.rawData?.lat != null" class="tak-detail-field">
                  <span class="tak-field-label">Location</span>
                  {{ selectedFeature.rawData.lat.toFixed(6) }}°, {{ selectedFeature.rawData.lon.toFixed(6) }}°
                  <span v-if="selectedFeature.rawData?.alt != null"> ({{ selectedFeature.rawData.alt.toFixed(1) }}m)</span>
                </div>
                <div v-if="selectedFeature.rawData?.properties?.uid || selectedFeature.rawData?.uniqueId" class="tak-detail-field">
                  <span class="tak-field-label">UID</span>
                  <code class="tak-uid">{{ selectedFeature.rawData?.properties?.uid || selectedFeature.rawData?.uniqueId }}</code>
                </div>
                <div v-if="selectedFeature.enriched" class="tak-enrichment-note">
                  <i class="pi pi-info-circle"></i> Location from observation data
                </div>
              </div>
              <button
                v-if="selectedFeature.resourceType === 'locationEstimates' && selectedFeature.rawData"
                class="tak-explore-btn tak-senrep-btn"
                @click="openSenrepPanel(selectedFeature.rawData); closeMobilePanel()"
              >
                <i class="pi pi-flag"></i> Submit SENREP
              </button>
              <button class="tak-explore-btn" @click="goToDetail">
                <i class="pi pi-external-link"></i> View in Explorer
              </button>
              </template>
            </div>
          </div>
        </div>
      </transition>
    </div>
  </div>
</template>

<style scoped>
.map-page {
  display: flex;
  height: 100%;
  overflow: hidden;
}

.map-sidebar {
  width: 280px;
  min-width: 280px;
  background: #f8fafc;
  border-right: 1px solid #e2e8f0;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
}

.sidebar-header {
  padding: 1rem 1rem 0.5rem;
}

.sidebar-title {
  font-weight: 700;
  font-size: 0.85rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #64748b;
}

.layer-controls {
  padding: 0.25rem 0.5rem;
}

.layer-section-label {
  font-size: 0.7rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: #94a3b8;
  padding: 0.35rem 0.75rem 0.15rem;
}

.layer-toggle {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  width: 100%;
  padding: 0.5rem 0.75rem;
  border: none;
  background: transparent;
  cursor: pointer;
  border-radius: 6px;
  font-size: 0.85rem;
  transition: background 0.15s;
}

.layer-toggle:hover {
  background: #e2e8f0;
}

.layer-toggle.inactive {
  opacity: 0.4;
}

.layer-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  flex-shrink: 0;
  border: 2px solid #fff;
  box-shadow: 0 0 0 1px rgba(0,0,0,0.15);
}

.layer-label {
  flex: 1;
  text-align: left;
}

.layer-count {
  font-size: 0.8rem;
  color: #64748b;
  font-weight: 600;
  min-width: 1.5rem;
  text-align: right;
}

/* ── Data Source Toggle (per-publisher) ─────────────────────────── */
.source-controls {
  padding: 0.25rem 0.5rem;
  border-top: 1px solid #e2e8f0;
}

.source-toggle {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  width: 100%;
  padding: 0.35rem 0.75rem;
  border: none;
  background: transparent;
  cursor: pointer;
  border-radius: 6px;
  font-size: 0.8rem;
  transition: background 0.15s, opacity 0.2s;
}

.source-toggle:hover {
  background: #e2e8f0;
}

.source-toggle.inactive {
  opacity: 0.3;
}

.source-icon {
  font-size: 0.9rem;
  line-height: 1;
  width: 1.1rem;
  text-align: center;
}

.source-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.source-label {
  flex: 1;
  text-align: left;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.source-count {
  font-size: 0.75rem;
  color: #94a3b8;
  font-weight: 600;
  min-width: 1.5rem;
  text-align: right;
}

.sidebar-status {
  padding: 0.75rem 1rem;
  font-size: 0.8rem;
  color: #64748b;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.milsymbol-toggle {
  padding: 0.5rem 1rem;
  border-top: 1px solid #e2e8f0;
}

.milsymbol-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.82rem;
  color: #334155;
  cursor: pointer;
  user-select: none;
}

.milsymbol-label input[type="checkbox"] {
  accent-color: #3b82f6;
  width: 15px;
  height: 15px;
  cursor: pointer;
}

.search-btn {
  margin: 0.5rem 0.75rem 0.75rem;
  padding: 0.6rem 1rem;
  border: none;
  background: #3b82f6;
  color: #fff;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.4rem;
}

.search-btn:hover {
  background: #2563eb;
}

.search-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.filter-section {
  margin: 0.5rem 0.75rem;
  padding: 0.5rem;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
}

.filter-section-label {
  font-size: 0.78rem;
  font-weight: 600;
  color: #475569;
  margin-bottom: 0.5rem;
  display: flex;
  align-items: center;
  gap: 0.35rem;
}

.clear-all-btn {
  margin-left: auto;
  background: none;
  border: none;
  font-size: 0.7rem;
  color: #ef4444;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.2rem;
  padding: 0.15rem 0.3rem;
  border-radius: 4px;
}

.clear-all-btn:hover {
  background: #fee2e2;
}

.filter-item {
  margin-bottom: 0.4rem;
}

.filter-label {
  display: block;
  font-size: 0.7rem;
  color: #64748b;
  margin-bottom: 0.15rem;
}

.filter-input {
  width: 100%;
  box-sizing: border-box;
  padding: 0.3rem 0.45rem;
  border: 1px solid #cbd5e1;
  border-radius: 4px;
  font-size: 0.78rem;
  color: #1e293b;
  background: #fff;
}

.filter-input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.15);
}

.empty-state {
  margin: 0.75rem;
  padding: 1rem;
  background: #fffbeb;
  border: 1px solid #fde68a;
  border-radius: 8px;
  text-align: center;
  font-size: 0.85rem;
  color: #92400e;
}

.empty-state p {
  margin: 0.4rem 0;
}

.empty-detail {
  font-size: 0.8rem;
  color: #78716c;
}

.empty-detail code {
  background: #fef3c7;
  padding: 0.1rem 0.3rem;
  border-radius: 3px;
  font-size: 0.75rem;
}

.create-test-btn {
  margin-top: 0.5rem;
  padding: 0.5rem 1rem;
  border: 1px solid #3b82f6;
  background: #3b82f6;
  color: #fff;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.85rem;
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
}

.create-test-btn:hover {
  background: #2563eb;
}

.create-test-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.test-created-msg {
  color: #16a34a;
  font-weight: 600;
}

.error-msg {
  color: #dc2626;
  font-weight: 600;
}

.enrichment-info {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin: 0.25rem 0.75rem 0.5rem;
  padding: 0.4rem 0.6rem;
  background: #f0f9ff;
  border: 1px dashed #93c5fd;
  border-radius: 6px;
  font-size: 0.75rem;
  color: #1e40af;
}

.enriched-indicator {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  border: 2px dashed #3b82f6;
  flex-shrink: 0;
}

.enrichment-text {
  flex: 1;
}

.enrichment-banner {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
  padding: 0.4rem 0.6rem;
  margin-bottom: 0.5rem;
  background: #f0f9ff;
  border: 1px dashed #93c5fd;
  border-radius: 6px;
  font-size: 0.75rem;
  color: #1e40af;
}

.enrichment-banner small {
  color: #64748b;
  font-size: 0.7rem;
}

.detail-panel {
  margin: 0.5rem 0.75rem;
  padding: 0.75rem;
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 0.85rem;
}

.dsc-inline-loading {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 0;
  color: #64748b;
  font-size: 0.82rem;
}

.detail-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}

.detail-type-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  color: #fff;
  font-size: 0.7rem;
  font-weight: 700;
  flex-shrink: 0;
}

.detail-field {
  margin-bottom: 0.35rem;
  color: #334155;
  line-height: 1.4;
}

.field-label {
  font-weight: 600;
  color: #64748b;
}

.detail-field code {
  font-size: 0.8rem;
  background: #f1f5f9;
  padding: 0.1rem 0.3rem;
  border-radius: 3px;
}

.detail-field code.uid {
  word-break: break-all;
}

.detail-link-btn {
  margin-top: 0.5rem;
  width: 100%;
  padding: 0.4rem;
  border: 1px solid #3b82f6;
  background: transparent;
  color: #3b82f6;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.8rem;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.35rem;
}

.detail-link-btn:hover {
  background: #eff6ff;
}

.raw-json {
  margin-top: 0.5rem;
}

.raw-json summary {
  cursor: pointer;
  font-size: 0.8rem;
  color: #64748b;
}

.raw-json pre {
  max-height: 200px;
  overflow: auto;
  font-size: 0.75rem;
  background: #f1f5f9;
  padding: 0.5rem;
  border-radius: 4px;
  margin-top: 0.35rem;
}

.map-area {
  flex: 1;
  position: relative;
}

.map-container {
  width: 100%;
  height: 100%;
}

.coord-display {
  position: absolute;
  bottom: 6px;
  left: 6px;
  background: rgba(0, 0, 0, 0.55);
  color: #fff;
  font-family: monospace;
  font-size: 0.78rem;
  padding: 3px 8px;
  border-radius: 4px;
  pointer-events: none;
  z-index: 10;
  user-select: none;
}

/* OpenLayers popup — positioned above the feature with arrow pointing down */
.ol-popup {
  position: absolute;
  background: white;
  padding: 10px 14px;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  min-width: 160px;
  max-width: 280px;
  font-size: 0.85rem;
  bottom: 12px;
  transform: translateX(-50%);
  white-space: normal;
}

.ol-popup:after, .ol-popup:before {
  top: 100%;
  border: solid transparent;
  content: " ";
  height: 0;
  width: 0;
  position: absolute;
  pointer-events: none;
}

.ol-popup:after {
  border-top-color: white;
  border-width: 8px;
  left: 50%;
  margin-left: -8px;
}

.ol-popup:before {
  border-top-color: #e2e8f0;
  border-width: 9px;
  left: 50%;
  margin-left: -9px;
}

.ol-popup-closer {
  text-decoration: none;
  position: absolute;
  top: 4px;
  right: 8px;
  font-size: 1.1rem;
  color: #94a3b8;
}

.ol-popup-closer:after {
  content: "✕";
}

.ol-popup-closer:hover {
  color: #334155;
}

.popup-content {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.popup-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  color: #fff;
  font-size: 0.65rem;
  font-weight: 700;
  margin-bottom: 0.1rem;
}

.popup-id {
  font-size: 0.78rem;
  color: #475569;
}

/* Stacked-feature picker */
.stacked-picker {
  margin-top: 0.35rem;
  padding-top: 0.35rem;
  border-top: 1px solid #e2e8f0;
}
.stacked-label {
  font-size: 0.7rem;
  color: #94a3b8;
  margin-bottom: 0.2rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
.stacked-btn {
  display: block;
  width: 100%;
  text-align: left;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 4px;
  padding: 0.25rem 0.4rem;
  margin-bottom: 0.15rem;
  font-size: 0.78rem;
  color: #1e293b;
  cursor: pointer;
  transition: background 0.1s;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.stacked-btn:hover { background: #eff6ff; border-color: #93c5fd; }
.stacked-btn--active {
  background: #dbeafe;
  border-color: #3b82f6;
  color: #1e40af;
  font-weight: 600;
}

.bbox-controls {
  margin: 0 0.75rem 0.75rem;
}

.bbox-draw-btn {
  width: 100%;
  padding: 0.5rem;
  border: 1px dashed #3b82f6;
  background: #fff;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.85rem;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.35rem;
  color: #3b82f6;
}

.bbox-draw-btn:hover {
  background: #eff6ff;
}

.bbox-draw-btn.active {
  background: #dbeafe;
  border-style: solid;
  color: #1d4ed8;
}

.bbox-draw-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.bbox-active {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  margin-top: 0.4rem;
  padding: 0.35rem 0.5rem;
  background: #eff6ff;
  border: 1px solid #93c5fd;
  border-radius: 6px;
  font-size: 0.8rem;
  color: #1d4ed8;
}

.bbox-label {
  flex: 1;
  font-weight: 600;
}

.bbox-clear {
  background: none;
  border: none;
  color: #64748b;
  cursor: pointer;
  padding: 0.15rem;
  border-radius: 3px;
  font-size: 0.75rem;
}

.bbox-clear:hover {
  color: #dc2626;
  background: #fee2e2;
}

.bbox-coords {
  font-size: 0.7rem;
  color: #64748b;
  padding: 0.2rem 0.5rem;
  font-family: monospace;
}

/* ─── TAK-style mobile overlay (hidden on desktop) ─── */
.tak-overlay,
.tak-backdrop {
  display: none;
}

@media (max-width: 768px) {
  .map-page {
    flex-direction: column;
    height: calc(100vh - 53px);
    height: calc(100dvh - 53px);
    overflow: hidden;
  }

  /* Hide desktop sidebar — replaced by TAK overlays */
  .map-sidebar {
    display: none !important;
  }

  /* Hide desktop deployed-system card panel — mobile uses bottom drawer */
  .dsc-float-panel {
    display: none !important;
  }

  .map-area {
    flex: 1;
    min-height: 0;
    position: relative;
  }

  /* Hide OL popup on mobile — detail goes to bottom sheet */
  .ol-popup {
    display: none !important;
  }

  /* ─── Coordinate display — TAK styling ─── */
  .coord-display {
    background: rgba(15, 23, 42, 0.82) !important;
    border: 1px solid rgba(100, 116, 139, 0.35);
    color: #94d6a4 !important;
    font-family: 'Courier New', monospace;
    font-size: 0.72rem !important;
    padding: 4px 10px !important;
    border-radius: 3px !important;
    z-index: 50 !important;
  }

  /* ─── TAK overlay container ─── */
  .tak-overlay {
    display: block;
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    pointer-events: none;
    z-index: 100;
  }

  /* ─── Status pill — top-left ─── */
  .tak-status {
    position: absolute;
    top: 10px;
    left: 10px;
    padding: 5px 12px;
    background: rgba(15, 23, 42, 0.82);
    color: #94d6a4;
    font-family: 'Courier New', monospace;
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    border-radius: 3px;
    border: 1px solid rgba(100, 116, 139, 0.35);
    pointer-events: auto;
    display: flex;
    align-items: center;
    gap: 6px;
  }

  /* ─── Floating action buttons — right edge ─── */
  .tak-fab-group {
    position: absolute;
    top: 10px;
    right: 10px;
    display: flex;
    flex-direction: column;
    gap: 8px;
    pointer-events: auto;
  }

  .tak-fab {
    width: 44px;
    height: 44px;
    border-radius: 4px;
    border: 1px solid rgba(100, 116, 139, 0.5);
    background: rgba(15, 23, 42, 0.85);
    color: #e2e8f0;
    font-size: 1.1rem;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.45);
    transition: background 0.15s, border-color 0.15s;
    -webkit-tap-highlight-color: transparent;
  }

  .tak-fab:active {
    background: rgba(30, 41, 59, 0.95);
  }

  .tak-fab.active {
    background: rgba(16, 185, 129, 0.25);
    border-color: #10b981;
    color: #10b981;
  }

  .tak-fab:disabled {
    opacity: 0.4;
  }

  /* ─── Bottom sheet backdrop ─── */
  .tak-backdrop {
    display: block;
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    z-index: 200;
    pointer-events: auto;
  }

  /* ─── Bottom sheet panel ─── */
  .tak-sheet {
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    max-height: 55vh;
    background: rgba(15, 23, 42, 0.94);
    border-top: 1px solid rgba(100, 116, 139, 0.4);
    border-radius: 10px 10px 0 0;
    display: flex;
    flex-direction: column;
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    box-shadow: 0 -4px 24px rgba(0, 0, 0, 0.55);
  }

  .tak-sheet--detail {
    max-height: 42vh;
  }

  .tak-sheet-handle {
    width: 36px;
    height: 4px;
    background: rgba(148, 163, 184, 0.45);
    border-radius: 2px;
    margin: 8px auto 4px;
    cursor: pointer;
  }

  .tak-sheet-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 4px 16px 8px;
    border-bottom: 1px solid rgba(100, 116, 139, 0.25);
  }

  .tak-sheet-title {
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.14em;
    color: #10b981;
    font-family: 'Courier New', monospace;
  }

  .tak-sheet-close {
    background: none;
    border: none;
    color: #94a3b8;
    font-size: 1.05rem;
    padding: 6px;
    cursor: pointer;
    -webkit-tap-highlight-color: transparent;
  }

  .tak-sheet-body {
    padding: 12px 16px 24px;
    overflow-y: auto;
    -webkit-overflow-scrolling: touch;
  }

  /* ─── Layers grid ─── */
  .tak-layer-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 6px;
  }

  .tak-layer-chip {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 10px 10px;
    background: rgba(30, 41, 59, 0.7);
    border: 1px solid rgba(100, 116, 139, 0.3);
    border-radius: 4px;
    color: #e2e8f0;
    font-size: 0.76rem;
    cursor: pointer;
    -webkit-tap-highlight-color: transparent;
    transition: opacity 0.15s;
  }

  .tak-layer-chip.inactive {
    opacity: 0.3;
  }

  .tak-layer-dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    flex-shrink: 0;
    border: 1px solid rgba(255, 255, 255, 0.25);
  }

  .tak-layer-name {
    flex: 1;
    text-align: left;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .tak-layer-count {
    font-size: 0.68rem;
    color: #94a3b8;
    font-weight: 600;
    font-family: 'Courier New', monospace;
  }

  .tak-enrichment {
    margin-top: 10px;
    padding: 6px 10px;
    background: rgba(59, 130, 246, 0.1);
    border: 1px dashed rgba(59, 130, 246, 0.3);
    border-radius: 4px;
    font-size: 0.72rem;
    color: #93c5fd;
    text-align: center;
  }

  .tak-source-section {
    margin-top: 10px;
    padding-top: 8px;
    border-top: 1px solid rgba(255, 255, 255, 0.08);
  }

  .tak-source-heading {
    font-size: 0.65rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: #94a3b8;
    padding: 0 4px 4px;
  }

  .tak-source-icon {
    font-size: 0.85rem;
    line-height: 1;
    width: 1.1rem;
    text-align: center;
  }

  /* ─── Live Mode (mobile) ─── */
  .tak-live-row {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-top: 12px;
  }
  .tak-live-btn {
    display: flex;
    align-items: center;
    gap: 5px;
    padding: 6px 14px;
    border-radius: 6px;
    border: 1px solid rgba(255, 255, 255, 0.15);
    background: rgba(255, 255, 255, 0.06);
    color: #cbd5e1;
    font-size: 0.75rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
  }
  .tak-live-btn.active {
    background: rgba(34, 197, 94, 0.2);
    border-color: rgba(34, 197, 94, 0.5);
    color: #22c55e;
    animation: tak-live-pulse 2s ease-in-out infinite;
  }
  .tak-live-ts {
    font-size: 0.65rem;
    color: #9ca3af;
    font-family: 'Courier New', monospace;
  }
  .tak-fab--live {
    background: rgba(34, 197, 94, 0.25) !important;
    border-color: rgba(34, 197, 94, 0.6) !important;
    color: #22c55e !important;
    animation: tak-live-pulse 2s ease-in-out infinite;
  }
  @keyframes tak-live-pulse {
    0%, 100% { box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.4); }
    50% { box-shadow: 0 0 8px 3px rgba(34, 197, 94, 0.2); }
  }

  /* ─── Sim FABs (mobile) ─── */
  .tak-fab--sim-start {
    background: rgba(34, 197, 94, 0.25) !important;
    border-color: rgba(34, 197, 94, 0.6) !important;
    color: #22c55e !important;
  }
  .tak-fab--reset {
    background: rgba(239, 68, 68, 0.25) !important;
    border-color: rgba(239, 68, 68, 0.6) !important;
    color: #ef4444 !important;
  }
  .tak-fab--senrep {
    background: rgba(239, 68, 68, 0.25) !important;
    border-color: rgba(239, 68, 68, 0.6) !important;
    color: #ef4444 !important;
  }
  .tak-fab--senrep.active {
    background: rgba(239, 68, 68, 0.45) !important;
    border-color: rgba(239, 68, 68, 0.9) !important;
    color: #fff !important;
  }
  .tak-senrep-btn {
    background: rgba(239, 68, 68, 0.2) !important;
    border: 1px solid rgba(239, 68, 68, 0.5) !important;
    color: #ef4444 !important;
  }
  .tak-fab--sim-running {
    background: rgba(34, 197, 94, 0.15) !important;
    border-color: rgba(34, 197, 94, 0.4) !important;
    color: #22c55e !important;
    font-size: 0.55rem;
    pointer-events: none;
    animation: tak-live-pulse 2s ease-in-out infinite;
  }

  /* ─── Filters ─── */
  .tak-filter-row {
    margin-bottom: 12px;
  }

  .tak-filter-row label {
    display: block;
    font-size: 0.66rem;
    font-weight: 700;
    color: #94a3b8;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-bottom: 4px;
  }

  .tak-input {
    width: 100%;
    box-sizing: border-box;
    padding: 9px 10px;
    background: rgba(30, 41, 59, 0.8);
    border: 1px solid rgba(100, 116, 139, 0.4);
    border-radius: 3px;
    color: #e2e8f0;
    font-size: 0.82rem;
    font-family: inherit;
  }

  .tak-input:focus {
    outline: none;
    border-color: #10b981;
    box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.2);
  }

  .tak-input::placeholder {
    color: #64748b;
  }

  /* datetime-local color-scheme for dark inputs */
  .tak-input[type="datetime-local"] {
    color-scheme: dark;
  }

  .tak-filter-dates {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
  }

  .tak-bbox-row {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .tak-bbox-btn {
    flex: 1;
    padding: 9px;
    background: rgba(30, 41, 59, 0.8);
    border: 1px dashed rgba(59, 130, 246, 0.5);
    border-radius: 3px;
    color: #93c5fd;
    font-size: 0.82rem;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    -webkit-tap-highlight-color: transparent;
  }

  .tak-bbox-btn.active {
    background: rgba(59, 130, 246, 0.15);
    border-style: solid;
    color: #60a5fa;
  }

  .tak-bbox-set {
    display: flex;
    align-items: center;
    gap: 4px;
    color: #10b981;
    font-size: 0.78rem;
    font-weight: 600;
  }

  .tak-bbox-clear {
    background: none;
    border: none;
    color: #94a3b8;
    cursor: pointer;
    padding: 2px;
    font-size: 0.72rem;
    -webkit-tap-highlight-color: transparent;
  }

  .tak-bbox-coords {
    margin-top: 4px;
    font-size: 0.66rem;
    color: #64748b;
    font-family: 'Courier New', monospace;
  }

  .tak-clear-all {
    width: 100%;
    padding: 7px;
    background: rgba(239, 68, 68, 0.1);
    border: 1px solid rgba(239, 68, 68, 0.3);
    border-radius: 3px;
    color: #fca5a5;
    font-size: 0.78rem;
    cursor: pointer;
    margin-bottom: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 4px;
    -webkit-tap-highlight-color: transparent;
  }

  .tak-search-btn {
    width: 100%;
    padding: 12px;
    background: #10b981;
    border: none;
    border-radius: 4px;
    color: #fff;
    font-size: 0.88rem;
    font-weight: 700;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    letter-spacing: 0.04em;
    -webkit-tap-highlight-color: transparent;
  }

  .tak-search-btn:active {
    background: #059669;
  }

  .tak-search-btn:disabled {
    opacity: 0.5;
  }

  /* ─── Detail sheet ─── */
  .tak-detail-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 12px;
  }

  .tak-detail-badge {
    width: 28px;
    height: 28px;
    border-radius: 4px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #fff;
    font-size: 0.72rem;
    font-weight: 700;
    flex-shrink: 0;
  }

  .tak-detail-header strong {
    color: #e2e8f0;
    font-size: 0.92rem;
  }

  .tak-detail-fields {
    display: grid;
    gap: 8px;
  }

  .tak-detail-field {
    font-size: 0.8rem;
    color: #cbd5e1;
    line-height: 1.4;
  }

  .tak-field-label {
    font-weight: 700;
    color: #64748b;
    font-size: 0.66rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    display: block;
  }

  .tak-detail-field code {
    font-size: 0.74rem;
    background: rgba(30, 41, 59, 0.6);
    padding: 2px 6px;
    border-radius: 2px;
    color: #94d6a4;
  }

  .tak-uid {
    word-break: break-all;
  }

  .tak-enrichment-note {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 6px 10px;
    background: rgba(59, 130, 246, 0.1);
    border: 1px dashed rgba(59, 130, 246, 0.3);
    border-radius: 4px;
    font-size: 0.72rem;
    color: #93c5fd;
  }

  .tak-explore-btn {
    margin-top: 14px;
    width: 100%;
    padding: 11px;
    background: transparent;
    border: 1px solid #10b981;
    border-radius: 4px;
    color: #10b981;
    font-size: 0.84rem;
    font-weight: 600;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    -webkit-tap-highlight-color: transparent;
  }

  .tak-explore-btn:active {
    background: rgba(16, 185, 129, 0.15);
  }

  /* ─── Slide-up transition ─── */
  .tak-slide-enter-active,
  .tak-slide-leave-active {
    transition: opacity 0.2s ease;
  }

  .tak-slide-enter-active .tak-sheet,
  .tak-slide-leave-active .tak-sheet {
    transition: transform 0.28s cubic-bezier(0.32, 0.72, 0, 1);
  }

  .tak-slide-enter-from,
  .tak-slide-leave-to {
    opacity: 0;
  }

  .tak-slide-enter-from .tak-sheet,
  .tak-slide-leave-to .tak-sheet {
    transform: translateY(100%);
  }
}

/* ═══ SENREP Panel Styles ═══ */
.senrep-popup-btn {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  margin-top: 0.4rem;
  padding: 0.3rem 0.6rem;
  background: #ef4444;
  color: #fff;
  border: none;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s;
}
.senrep-popup-btn:hover { background: #dc2626; }

.popup-senrep-detail {
  font-size: 0.78rem;
  color: #334155;
  margin-top: 0.3rem;
  line-height: 1.5;
}

/* ═══ Weather Observation Popup & Detail Styles ═══ */
.popup-weather-detail {
  margin-top: 0.3rem;
  font-size: 0.78rem;
  color: #334155;
  line-height: 1.5;
}
.popup-weather-conditions {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  font-weight: 600;
}
.popup-weather-icon { font-size: 1.2rem; }
.popup-weather-desc { color: #475569; }
.popup-weather-temp {
  font-size: 1.1rem;
  font-weight: 700;
  color: #0ea5e9;
  margin: 0.15rem 0;
}
.popup-weather-temp-f {
  font-weight: 400;
  font-size: 0.78rem;
  color: #64748b;
}
.popup-weather-grid {
  display: flex;
  gap: 0.6rem;
  font-size: 0.72rem;
  color: #475569;
}
.popup-weather-metar {
  font-family: 'Fira Code', 'Cascadia Code', monospace;
  font-size: 0.65rem;
  color: #64748b;
  margin-top: 0.3rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 250px;
}

/* Camera popup image (BuoyCAM / NIMS) */
.popup-buoycam-detail { margin-top: 0.35rem; text-align: center; }
.popup-buoycam-img { max-width: 240px; max-height: 160px; border-radius: 4px; object-fit: contain; border: 1px solid #cbd5e1; cursor: pointer; transition: transform 0.15s; }
.popup-buoycam-img:hover { transform: scale(1.03); }
.popup-buoycam-meta { font-size: 0.68rem; color: #64748b; margin-top: 0.2rem; }
.popup-timelapse-link {
  display: inline-block;
  margin-top: 0.25rem;
  padding: 0.15rem 0.5rem;
  font-size: 0.68rem;
  font-weight: 600;
  color: #0ea5e9;
  background: rgba(14, 165, 233, 0.08);
  border: 1px solid rgba(14, 165, 233, 0.25);
  border-radius: 4px;
  text-decoration: none;
  transition: background 0.15s;
}
.popup-timelapse-link:hover { background: rgba(14, 165, 233, 0.18); }

/* ═══ Earthquake Observation Popup Styles ═══ */
.popup-earthquake-detail {
  margin-top: 0.35rem;
  font-size: 0.78rem;
  color: #334155;
  line-height: 1.5;
}
.popup-eq-header {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  margin-bottom: 0.2rem;
}
.popup-eq-mag-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 2.2rem;
  padding: 0.15rem 0.35rem;
  border-radius: 6px;
  color: #fff;
  font-weight: 800;
  font-size: 0.9rem;
  text-shadow: 0 1px 2px rgba(0,0,0,0.3);
  letter-spacing: -0.02em;
}
.popup-eq-severity {
  font-weight: 600;
  color: #475569;
  font-size: 0.8rem;
}
.popup-eq-magtype {
  font-weight: 400;
  color: #94a3b8;
  font-size: 0.7rem;
}
.popup-eq-place {
  font-size: 0.78rem;
  color: #334155;
  margin-bottom: 0.2rem;
}
.popup-eq-grid {
  display: flex;
  gap: 0.6rem;
  font-size: 0.72rem;
  color: #475569;
  flex-wrap: wrap;
}
.popup-eq-usgs-link {
  display: inline-block;
  margin-top: 0.3rem;
  padding: 0.2rem 0.5rem;
  font-size: 0.7rem;
  font-weight: 600;
  color: #3b82f6;
  background: rgba(59, 130, 246, 0.08);
  border: 1px solid rgba(59, 130, 246, 0.25);
  border-radius: 4px;
  text-decoration: none;
  transition: background 0.15s;
}
.popup-eq-usgs-link:hover { background: rgba(59, 130, 246, 0.18); }

/* Sidebar weather detail panel */
.weather-detail-panel {
  border-left: 3px solid #0ea5e9;
}
.weather-station-id {
  font-size: 0.72rem;
  color: #64748b;
  font-family: 'Fira Code', 'Cascadia Code', monospace;
  letter-spacing: 0.04em;
}
.weather-hero {
  text-align: center;
  padding: 0.5rem 0;
  border-bottom: 1px solid #e2e8f0;
  margin-bottom: 0.5rem;
}
.weather-hero-icon { font-size: 2rem; }
.weather-hero-temp {
  font-size: 1.5rem;
  font-weight: 700;
  color: #0ea5e9;
  margin: 0.2rem 0;
}
.weather-hero-temp-f {
  font-weight: 400;
  font-size: 0.85rem;
  color: #64748b;
}
.weather-hero-desc {
  font-size: 0.85rem;
  color: #475569;
  font-weight: 500;
}
.weather-fields {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.4rem;
}
.weather-field {
  display: flex;
  flex-direction: column;
  font-size: 0.78rem;
  padding: 0.3rem 0;
}
.weather-field-label {
  font-size: 0.68rem;
  color: #64748b;
  font-weight: 600;
}
.weather-time {
  font-size: 0.72rem;
  color: #94a3b8;
  margin-top: 0.5rem;
}
.weather-time .pi { font-size: 0.7rem; }
.weather-metar-details {
  margin-top: 0.5rem;
}
.weather-metar-details summary {
  font-size: 0.72rem;
  color: #64748b;
  cursor: pointer;
}
.weather-metar-pre {
  font-family: 'Fira Code', 'Cascadia Code', monospace;
  font-size: 0.68rem;
  color: #334155;
  background: #f1f5f9;
  padding: 0.4rem;
  border-radius: 4px;
  white-space: pre-wrap;
  word-break: break-all;
  margin-top: 0.3rem;
}

/* ═══ Aircraft Observation Popup & Detail Styles ═══ */
.popup-aircraft-detail {
  margin-top: 0.3rem;
  font-size: 0.78rem;
  color: #334155;
  line-height: 1.5;
}
.popup-aircraft-id {
  font-weight: 700;
  font-size: 0.9rem;
  color: #1e3a5f;
}
.popup-aircraft-country {
  font-weight: 400;
  font-size: 0.72rem;
  color: #64748b;
  margin-left: 0.3rem;
}
.popup-aircraft-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.3rem 0.6rem;
  font-size: 0.72rem;
  color: #475569;
  margin-top: 0.2rem;
}

/* Sidebar aircraft detail panel */
.aircraft-detail-panel {
  border-left: 3px solid #3b82f6;
}
.aircraft-icao {
  font-size: 0.72rem;
  color: #64748b;
  font-family: 'Fira Code', 'Cascadia Code', monospace;
  letter-spacing: 0.04em;
}
.aircraft-hero {
  text-align: center;
  padding: 0.5rem 0;
  border-bottom: 1px solid #e2e8f0;
  margin-bottom: 0.5rem;
}
.aircraft-hero-heading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.3rem;
  font-size: 1.3rem;
  font-weight: 700;
  color: #3b82f6;
}
.aircraft-heading-arrow {
  display: inline-block;
  font-size: 1.5rem;
  transition: transform 0.3s;
  color: #3b82f6;
}
.aircraft-hero-alt {
  font-size: 1.1rem;
  font-weight: 600;
  color: #1e3a5f;
  margin: 0.2rem 0;
}
.aircraft-hero-status {
  font-size: 0.85rem;
  color: #475569;
  font-weight: 500;
}
.aircraft-fields {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.4rem;
}
.aircraft-field {
  display: flex;
  flex-direction: column;
  font-size: 0.78rem;
  padding: 0.3rem 0;
}
.aircraft-field-label {
  font-size: 0.68rem;
  color: #64748b;
  font-weight: 600;
}
.aircraft-how-it-works {
  margin-top: 0.6rem;
  border-top: 1px solid #e2e8f0;
  padding-top: 0.4rem;
}
.aircraft-how-it-works summary {
  font-size: 0.72rem;
  color: #3b82f6;
  cursor: pointer;
  font-weight: 600;
}
.aircraft-how-it-works p {
  font-size: 0.72rem;
  color: #475569;
  line-height: 1.5;
  margin: 0.3rem 0 0;
}
.aircraft-time {
  font-size: 0.72rem;
  color: #94a3b8;
  margin-top: 0.5rem;
}
.aircraft-time .pi { font-size: 0.7rem; }

/* ═══ Deployed System Card — floating right-side panel ═══ */
.dsc-float-panel {
  position: absolute;
  top: 0;
  right: 0;
  width: 400px;
  max-width: 90vw;
  height: 100%;
  background: #ffffff;
  border-left: 2px solid #3b82f6;
  z-index: 90;
  display: flex;
  flex-direction: column;
  box-shadow: -4px 0 20px rgba(0, 0, 0, 0.18);
}
.dsc-float-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 1rem;
  background: #1e293b;
  color: #f1f5f9;
  border-bottom: 1px solid #334155;
}
.dsc-float-title {
  font-weight: 600;
  font-size: 0.9rem;
  display: flex;
  align-items: center;
  gap: 0.4rem;
}
.dsc-float-close {
  background: none;
  border: none;
  color: #94a3b8;
  cursor: pointer;
  font-size: 1rem;
  padding: 0.25rem;
}
.dsc-float-close:hover { color: #f1f5f9; }
.dsc-float-body {
  flex: 1;
  overflow-y: auto;
  padding: 0.75rem;
}

/* Slide transition for the deployed system card */
.dsc-slide-enter-active,
.dsc-slide-leave-active {
  transition: transform 0.25s ease;
}
.dsc-slide-enter-from,
.dsc-slide-leave-to {
  transform: translateX(100%);
}

.senrep-panel {
  position: absolute;
  top: 0;
  right: 0;
  width: 320px;
  height: 100%;
  background: #1e293b;
  border-left: 2px solid #ef4444;
  z-index: 100;
  display: flex;
  flex-direction: column;
  box-shadow: -4px 0 20px rgba(0, 0, 0, 0.4);
}
@media (max-width: 768px) {
  .senrep-panel {
    top: auto;
    bottom: 0;
    left: 0;
    right: 0;
    width: 100%;
    height: 60vh;
    border-left: none;
    border-top: 2px solid #ef4444;
    border-radius: 16px 16px 0 0;
    z-index: 1100;
    box-shadow: 0 -4px 20px rgba(0, 0, 0, 0.5);
  }
}
.senrep-panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 1rem;
  background: #0f172a;
  border-bottom: 1px solid #334155;
}
.senrep-panel-title {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-weight: 700;
  font-size: 0.9rem;
  color: #f1f5f9;
}
.senrep-panel-close {
  background: none;
  border: none;
  color: #94a3b8;
  cursor: pointer;
  font-size: 1rem;
}
.senrep-panel-close:hover { color: #f1f5f9; }

.senrep-panel-body {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}
.senrep-label {
  font-size: 0.7rem;
  font-weight: 600;
  color: #94a3b8;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-top: 0.4rem;
}
.senrep-input, .senrep-textarea {
  background: #0f172a;
  border: 1px solid #334155;
  color: #e2e8f0;
  padding: 0.4rem 0.6rem;
  border-radius: 4px;
  font-size: 0.8rem;
  font-family: inherit;
}
.senrep-input:focus, .senrep-textarea:focus {
  outline: none;
  border-color: #ef4444;
}
.senrep-readonly {
  font-size: 0.8rem;
  color: #cbd5e1;
  background: #0f172a;
  padding: 0.3rem 0.6rem;
  border-radius: 4px;
  border: 1px solid transparent;
}
.senrep-submit-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.4rem;
  margin-top: 0.8rem;
  padding: 0.6rem 1rem;
  background: #ef4444;
  color: #fff;
  border: none;
  border-radius: 6px;
  font-size: 0.85rem;
  font-weight: 700;
  cursor: pointer;
  transition: background 0.15s;
}
.senrep-submit-btn:hover:not(:disabled) { background: #dc2626; }
.senrep-submit-btn:disabled { opacity: 0.6; cursor: not-allowed; }
.senrep-success {
  text-align: center;
  color: #22c55e;
  font-weight: 600;
  font-size: 0.85rem;
  margin-top: 0.4rem;
}
.senrep-provenance {
  margin-top: 0.8rem;
  color: #64748b;
  font-size: 0.75rem;
}
.senrep-provenance summary {
  cursor: pointer;
  font-weight: 600;
}

/* Slide transition */
.senrep-slide-enter-active,
.senrep-slide-leave-active {
  transition: transform 0.25s ease;
}
.senrep-slide-enter-from,
.senrep-slide-leave-to {
  transform: translateX(100%);
}

/* ── Simulator / Reset Control Bar ────────────────────────────────────── */
.sim-control-bar {
  position: absolute;
  bottom: 18px;
  left: 0;
  right: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  z-index: 1000;
  pointer-events: none;
}
.sim-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 18px;
  border: none;
  border-radius: 8px;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s, opacity 0.2s, box-shadow 0.2s;
  box-shadow: 0 2px 8px rgba(0,0,0,0.25);
  color: #fff;
  pointer-events: auto;
}
.sim-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}
.sim-btn--start {
  background: #16a34a;
}
.sim-btn--start:not(:disabled):hover {
  background: #15803d;
  box-shadow: 0 2px 12px rgba(22,163,74,0.4);
}
.sim-btn--stop {
  background: #d97706;
}
.sim-btn--stop:not(:disabled):hover {
  background: #b45309;
  box-shadow: 0 2px 12px rgba(217,119,6,0.4);
}
.sim-btn--reset {
  background: #dc2626;
}
.sim-btn--reset:not(:disabled):hover {
  background: #b91c1c;
  box-shadow: 0 2px 12px rgba(220,38,38,0.4);
}
.sim-msg {
  font-size: 0.75rem;
  color: #f1f5f9;
  background: rgba(0,0,0,0.5);
  padding: 4px 10px;
  border-radius: 6px;
  max-width: 260px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Mobile: hide desktop sim bar — controls are in TAK FAB group */
@media (max-width: 768px) {
  .sim-control-bar {
    display: none !important;
  }
  .sim-btn {
    font-size: 0.8rem;
    padding: 7px 14px;
  }
}
</style>
