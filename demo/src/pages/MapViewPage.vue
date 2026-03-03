<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, computed } from 'vue'
import { useRouter } from 'vue-router'
import { connection, RESOURCE_TYPES } from '../state'
import { apiFetch } from '../api'
import { getListUrl } from '../csapi-bridge'

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
import { Style, Circle as CircleStyle, Fill, Stroke, Text as OlText, Icon as OlIcon } from 'ol/style'
import Overlay from 'ol/Overlay'
import { getSymbolForResource, getSymbolSizeForType, type MilSymbolResult } from '../symbol-mapper'
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

// All types visible on the map
const MAP_TYPES = [...SPATIAL_TYPES, ...PART2_MAP_TYPES, OBS_POINTS_ENTRY, OBS_TRACK_ENTRY, LOB_ENTRY, DETECTION_RANGES_ENTRY]

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
})

// Cache: systemId → { lat, lon, alt?, datastreamName? }
const systemLocationCache: Record<string, { lat: number; lon: number; alt?: number; datastreamName?: string; phenomenonTime?: string }> = {}
// Primary (top-level) system IDs — limits per-system API calls to avoid O(N) subsystem fetches
const primarySystemIds = new Set<string>()
// Track location-related datastreams for observation track rendering
let locationDatastreamList: Array<{ id: string; name: string; systemId: string }> = []
// Track how many features were enriched from observations
const enrichedCounts = ref<Record<string, number>>({})

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

// ── Detection Range Configuration ──────────────────────────────────
// Client-side config: keyed by system UID.
// When the server supports custom properties, this can be replaced with
// a read from the system's `detectionRange` property.
interface DetectionRing { label: string; radius_m: number }
interface DetectionRangeConfig {
  shape: 'circular'
  rings: DetectionRing[]
  altitude?: { min_m: number; max_m: number | null; ref: string }
  confidence?: number
  basis?: string
  asOf?: string
}
const DETECTION_RANGE_CONFIGS: Record<string, DetectionRangeConfig> = {
  'urn:os4csapi:system:odas:az-ma-1': {
    shape: 'circular',
    rings: [
      { label: 'min', radius_m: 15 },
      { label: 'nominal', radius_m: 40 },
      { label: 'max', radius_m: 65 },
    ],
    altitude: { min_m: 0, max_m: null, ref: 'AGL' },
    confidence: 0.7,
    basis: 'estimated',
    asOf: '2026-03-02T18:00:00Z',
  },
  'urn:os4csapi:system:odas:az-ma-2': {
    shape: 'circular',
    rings: [
      { label: 'min', radius_m: 15 },
      { label: 'nominal', radius_m: 40 },
      { label: 'max', radius_m: 65 },
    ],
    altitude: { min_m: 0, max_m: null, ref: 'AGL' },
    confidence: 0.7,
    basis: 'estimated',
    asOf: '2026-03-02T18:00:00Z',
  },
  'urn:os4csapi:system:odas:az-ma-3': {
    shape: 'circular',
    rings: [
      { label: 'min', radius_m: 15 },
      { label: 'nominal', radius_m: 40 },
      { label: 'max', radius_m: 65 },
    ],
    altitude: { min_m: 0, max_m: null, ref: 'AGL' },
    confidence: 0.7,
    basis: 'estimated',
    asOf: '2026-03-02T18:00:00Z',
  },
}

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
  const opacity = 0.4 + (bucket / 10) * 0.6
  const width = 2 + (bucket / 10) * 2
  s = new Style({ stroke: new Stroke({ color: `rgba(${r}, ${g}, ${b}, ${opacity})`, width }) })
  bearingStyleCache.set(bucket, s)
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
    // Deployments derive geometry from subdeployments & deployed systems,
    // so skip server-side bbox (server only knows about top-level deployments
    // which typically have no geometry). Bbox is applied client-side during enrichDeployments.
    const opts = resourceType === 'deployments' ? buildQueryOptionsNoBbox() : buildQueryOptions()
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

  return null
}

/**
 * Check whether a datastream might produce observations with geographic
 * coordinates, based on its name or observedProperty definitions/labels.
 */
function isLocationRelatedDatastream(ds: any): boolean {
  const name = (ds.name || ds.outputName || '').toLowerCase()
  // Classic GPS/location keywords
  if (name.includes('gps_data') || name.includes('location') || name.includes('position')) return true

  const props: any[] = ds.observedProperties || []
  return props.some((p: any) => {
    const def = (p.definition || '').toLowerCase()
    const label = (p.label || '').toLowerCase()
    return def.includes('location') || label.includes('location')
      || def.includes('geodeticlatitude') || def.includes('latitude')
      || def.includes('longitude') || def.includes('geolocation')
      || label.includes('latitude') || label.includes('longitude')
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
      const sysId = ds['system@id'] || ds.system?.id
      if (!sysId) continue
      // Only use observation-derived location if no static location exists
      if (systemLocationCache[sysId]) continue
      const existing = bySystem[sysId]
      if (!existing || (ds.name || '').toLowerCase().includes('location')) {
        bySystem[sysId] = ds
      }
    }

    // Save location datastreams for observation track rendering
    locationDatastreamList = locationDs
      .filter((ds: any) => ds['system@id'] || ds.system?.id)
      .map((ds: any) => ({
        id: ds.id,
        name: ds.name || ds.outputName || 'Unknown',
        systemId: ds['system@id'] || ds.system?.id,
      }))

    // NOTE: Previously this block added ALL datastreams for systems with
    // cached locations.  That caused up to N×500 observation fetches and
    // thousands of bearing-line features, which was the #1 source of map
    // lag.  Now we only keep the location-related datastreams above.
    // If you need geographic observations from non-location datastreams,
    // add them to isLocationRelatedDatastream() instead.

    // Fetch latest observation from each location datastream in parallel
    const promises = Object.entries(bySystem).map(async ([sysId, ds]) => {
      try {
        const obsRes = await apiFetch(`/datastreams/${ds.id}/observations?limit=1`, {
          headers: { 'Accept': 'application/om+json' },
        })
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
      } catch { /* skip */ }
    })

    await Promise.all(promises)
  } catch { /* cache remains empty */ }
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

  // --- Enrich deployments FIRST (resolves all deployment geometry + updates systemLocationCache) ---
  await enrichDeployments()
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
  } catch { /* skip */ }
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
 * Build detection range ring features for deployments that link to systems
 * with known detection range configurations.
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
  const ringStyles: Record<string, { dash: number[]; fillAlpha: number; strokeWidth: number }> = {
    min:     { dash: [4, 4],  fillAlpha: 0.28, strokeWidth: 2 },
    nominal: { dash: [8, 6],  fillAlpha: 0.18, strokeWidth: 1.5 },
    max:     { dash: [12, 8], fillAlpha: 0.10, strokeWidth: 1.5 },
  }
  const ringColor = [96, 165, 250] // #60a5fa — friendly blue

  const batch: Feature[] = []

  for (const depFeature of deploySource.getFeatures()) {
    const rawData = depFeature.get('rawData')
    if (!rawData) continue

    const props = rawData.properties || rawData || {}
    const plat = props['platform@link']
    if (!plat?.uid) continue

    const config = DETECTION_RANGE_CONFIGS[plat.uid]
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
          asOf: config.asOf,
          systemUid: plat.uid,
          altitude: config.altitude,
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
      const sysId = ds['system@id'] || ds.system?.id
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
      const sysId = cs['system@id'] || cs.system?.id
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
const BEARING_LINE_LENGTH_M = 1000

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
async function loadObservationLayers(): Promise<void> {
  const pointSource = vectorSources['observationPoints']
  const trackSource = vectorSources['observationTracks']
  const bearingSource = vectorSources['bearingLines']
  if (pointSource) pointSource.clear()
  if (trackSource) trackSource.clear()
  if (bearingSource) bearingSource.clear()

  let pointCount = 0
  let trackCount = 0
  let bearingCount = 0

  const promises = locationDatastreamList.map(async (dsInfo) => {
    try {
      const obsRes = await apiFetch(`/datastreams/${dsInfo.id}/observations?limit=500`, {
        headers: { 'Accept': 'application/om+json' },
      })
      if (!obsRes.ok || !obsRes.data) return

      const items = obsRes.data.items || []
      const trackCoords: [number, number][] = []

      for (const obs of items) {
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
              feature.setStyle(getStyle('observationPoints'))
              feature.set('resourceType', 'observationPoints')
              feature.set('resourceId', obs.id || `${dsInfo.id}-obs-${pointCount}`)
              feature.set('resourceName', `Obs @ ${lat.toFixed(5)}, ${lon.toFixed(5)}`)
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
              pointSource.addFeature(feature)
              pointCount++
            }
          }
        }

        // --- Bearing lines: acoustic detection directions ---
        if (bearingSource && obs.result) {
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
              feature.setStyle(getCachedBearingLineStyle(b.energy))
              feature.set('resourceType', 'bearingLines')
              feature.set('resourceId', `${dsInfo.id}-lob-${bearingCount}`)
              const label = b.classLabel
                ? `${b.classLabel} ${b.azimuth.toFixed(1)}° (conf ${(b.classConfidence ?? 0).toFixed(2)})`
                : `Bearing ${b.azimuth.toFixed(1)}° (energy ${b.energy.toFixed(2)})`
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
              bearingSource.addFeature(feature)
              bearingCount++
            }
          }
        }
      }

      // Track LineString from all parsed coordinates
      if (trackSource && trackCoords.length >= 2) {
        const lineFeature = new Feature({
          geometry: new LineString(trackCoords.map(c => fromLonLat(c))),
        })
        lineFeature.setStyle(getStyle('observationTracks'))
        lineFeature.set('resourceType', 'observationTracks')
        lineFeature.set('resourceId', dsInfo.id)
        lineFeature.set('resourceName', `Track: ${dsInfo.name}`)
        lineFeature.set('enriched', true)
        lineFeature.set('enrichmentSource', `${trackCoords.length} observations from ${dsInfo.name}`)
        lineFeature.set('rawData', { datastreamId: dsInfo.id, datastreamName: dsInfo.name, systemId: dsInfo.systemId, pointCount: trackCoords.length })
        trackSource.addFeature(lineFeature)
        trackCount++
      }
    } catch { /* skip */ }
  })

  await Promise.all(promises)
  featureCounts.value['observationPoints'] = pointCount
  featureCounts.value['observationTracks'] = trackCount
  featureCounts.value['bearingLines'] = bearingCount
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

  // 3b. Build detection range rings from deployment emplacements
  buildDetectionRanges()

  // 4. Load Part 2 resources at parent system locations + observation layers
  await Promise.all([
    loadDatastreams(),
    loadControlStreams(),
    loadObservationLayers(),
  ])

  loading.value = false

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

function toggleBasemap() {
  if (osmLayer) osmLayer.setVisible(!useSatellite.value)
  if (satLayer) satLayer.setVisible(useSatellite.value)
  if (satRefLayer) satRefLayer.setVisible(useSatellite.value)
}

// --- Map Setup ---

onMounted(() => {
  if (!mapContainer.value || !popupContainer.value) return

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
    const layer = new VectorLayer({
      source,
      zIndex: rt.key === 'detectionRanges' ? 3 : rt.key === 'observationTracks' ? 5 : rt.key === 'bearingLines' ? 6 : rt.key === 'observationPoints' ? 7 : 10,
      // Deployments: no declutter so STANAG symbols are never hidden by label overlap
      declutter: labeledTypes.has(rt.key),
      updateWhileAnimating: false,
      updateWhileInteracting: false,
    })
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

    let hit = false
    map!.forEachFeatureAtPixel(evt.pixel, (feature) => {
      if (hit) return // only handle first
      // Skip bbox rectangle feature and non-interactive overlays
      const rt = feature.get('resourceType')
      if (!rt) return
      if (rt === 'detectionRanges') return // static overlay — not selectable
      hit = true

      // Toggle: if clicking the already-selected feature, deselect it
      if (selectedFeature.value?._olFeature === feature) {
        closePopup()
        return
      }

      const resourceType = feature.get('resourceType')
      const rawData = feature.get('rawData')
      const isEnriched = feature.get('enriched') || false
      const enrichmentSource = feature.get('enrichmentSource') || ''

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
    })

    if (!hit) {
      // Clicked empty space — close popup and deselect
      closePopup()
    }
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

  // Map is ready — user must press Search to load data

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

      <!-- Detail panel when a feature is selected -->
      <div v-if="selectedFeature" class="detail-panel">
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
        </div>
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
            <div v-if="mobilePanel === 'detail' && selectedFeature" class="tak-sheet-body">
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
              <button class="tak-explore-btn" @click="goToDetail">
                <i class="pi pi-external-link"></i> View in Explorer
              </button>
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
  font-size: 0.75rem;
  color: #64748b;
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
</style>
