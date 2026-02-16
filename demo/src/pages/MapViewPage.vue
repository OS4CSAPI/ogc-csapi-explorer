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
import { fromLonLat } from 'ol/proj'
import Feature from 'ol/Feature'
import Point from 'ol/geom/Point'
import Polygon from 'ol/geom/Polygon'
import LineString from 'ol/geom/LineString'
import { Style, Circle as CircleStyle, Fill, Stroke, Text as OlText } from 'ol/style'
import Overlay from 'ol/Overlay'
import type { Coordinate } from 'ol/coordinate'

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

const loading = ref(false)
const error = ref('')
const featureCounts = ref<Record<string, number>>({})
const selectedFeature = ref<any>(null)

// Part 1 resource types that may have geometry
const SPATIAL_TYPES = RESOURCE_TYPES.filter(r => r.part === 1 && r.key !== 'properties')

// Part 2 types shown on the map (placed at parent system's location)
const PART2_MAP_TYPES = RESOURCE_TYPES.filter(r => ['datastreams', 'controlStreams'].includes(r.key))

// Synthetic entry for observation GPS tracks (not a real API resource type)
const OBS_TRACK_ENTRY = { key: 'observationTracks', label: 'Obs. Track', plural: 'Observation Tracks', icon: 'pi pi-directions', part: 2 as const, readOnly: true }

// All types visible on the map
const MAP_TYPES = [...SPATIAL_TYPES, ...PART2_MAP_TYPES, OBS_TRACK_ENTRY]

// Color map for resource types
const TYPE_COLORS: Record<string, string> = {
  systems: '#3b82f6',           // blue
  deployments: '#8b5cf6',       // purple
  procedures: '#f59e0b',        // amber
  samplingFeatures: '#10b981',  // emerald
  datastreams: '#ef4444',       // red
  controlStreams: '#f97316',    // orange
  observationTracks: '#06b6d4', // cyan
}

const TYPE_LABELS: Record<string, string> = {
  systems: 'S',
  deployments: 'D',
  procedures: 'P',
  samplingFeatures: 'F',
  datastreams: 'DS',
  controlStreams: 'CS',
  observationTracks: '~',
}

// Active layer toggles
const activeLayers = ref<Record<string, boolean>>({
  systems: true,
  deployments: true,
  procedures: true,
  samplingFeatures: true,
  datastreams: true,
  controlStreams: true,
  observationTracks: true,
})

// Cache: systemId → { lat, lon, alt?, datastreamName? }
const systemLocationCache: Record<string, { lat: number; lon: number; alt?: number; datastreamName?: string; phenomenonTime?: string }> = {}
// Track location-related datastreams for observation track rendering
let locationDatastreamList: Array<{ id: string; name: string; systemId: string }> = []
// Track how many features were enriched from observations
const enrichedCounts = ref<Record<string, number>>({})

// Vector sources per type so we can toggle layers
const vectorSources: Record<string, VectorSource> = {}
const vectorLayers: Record<string, VectorLayer> = {}

function getStyle(resourceType: string, enriched = false): Style {
  const color = TYPE_COLORS[resourceType] || '#6b7280'
  const label = TYPE_LABELS[resourceType] || '?'

  // Observation tracks are LineStrings — dashed line, no point marker
  if (resourceType === 'observationTracks') {
    return new Style({
      stroke: new Stroke({ color, width: 3, lineDash: [8, 4] }),
    })
  }

  // Part 2 associated types use smaller markers to reduce clutter at shared locations
  const isPart2 = resourceType === 'datastreams' || resourceType === 'controlStreams'
  const radius = isPart2 ? 7 : 10
  const font = isPart2 ? 'bold 8px sans-serif' : 'bold 11px sans-serif'

  return new Style({
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
}

function getSelectedStyle(resourceType: string): Style {
  const color = TYPE_COLORS[resourceType] || '#6b7280'
  const label = TYPE_LABELS[resourceType] || '?'

  if (resourceType === 'observationTracks') {
    return new Style({
      stroke: new Stroke({ color: '#fbbf24', width: 5 }),
    })
  }

  const isPart2 = resourceType === 'datastreams' || resourceType === 'controlStreams'
  const radius = isPart2 ? 10 : 14
  const font = isPart2 ? 'bold 10px sans-serif' : 'bold 13px sans-serif'

  return new Style({
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
  feature.setStyle(getStyle(resourceType))
  feature.set('resourceType', resourceType)
  feature.set('resourceId', extractId(item))
  feature.set('resourceName', extractName(item))
  feature.set('rawData', item)
  return feature
}

async function loadResourceType(resourceType: string): Promise<number> {
  const source = vectorSources[resourceType]
  if (!source) return 0

  source.clear()

  try {
    const url = getListUrl(resourceType, { limit: 200 })
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

    let count = 0
    for (const item of items) {
      const feature = createOlFeature(item, resourceType)
      if (feature) {
        source.addFeature(feature)
        count++
      }
    }
    return count
  } catch {
    return 0
  }
}

/**
 * Build a cache of system locations from their location/GPS datastreams.
 * For each system that has a location datastream, fetches the latest observation
 * and caches the lat/lon so we can use it to enrich any resource linked to that system.
 */
async function buildSystemLocationCache(): Promise<void> {
  // Clear old cache
  for (const key of Object.keys(systemLocationCache)) delete systemLocationCache[key]
  locationDatastreamList = []

  try {
    // Fetch all datastreams
    const dsRes = await apiFetch('/datastreams?limit=200')
    if (!dsRes.ok || !dsRes.data) return

    const allDs = dsRes.data.items || dsRes.data.features || dsRes.data || []
    // Filter to location-related datastreams
    const locationDs = allDs.filter((ds: any) => {
      const name = (ds.name || ds.outputName || '').toLowerCase()
      const hasLocationProp = ds.observedProperties?.some((p: any) =>
        (p.definition || '').includes('Location') || (p.label || '').toLowerCase().includes('location')
      )
      return hasLocationProp || name.includes('gps_data') || name.includes('location')
    })

    // Deduplicate by system — keep only one datastream per system (prefer "Location" in name)
    const bySystem: Record<string, any> = {}
    for (const ds of locationDs) {
      const sysId = ds['system@id'] || ds.system?.id
      if (!sysId) continue
      const existing = bySystem[sysId]
      if (!existing || (ds.name || '').toLowerCase().includes('location')) {
        bySystem[sysId] = ds
      }
    }

    // Save all location datastream info for observation track rendering
    locationDatastreamList = Object.entries(bySystem).map(([sysId, ds]) => ({
      id: ds.id,
      name: ds.name || ds.outputName || 'Unknown',
      systemId: sysId,
    }))

    // Fetch latest observation from each location datastream in parallel
    const promises = Object.entries(bySystem).map(async ([sysId, ds]) => {
      try {
        const obsRes = await apiFetch(`/datastreams/${ds.id}/observations?limit=1`, {
          headers: { 'Accept': 'application/om+json' },
        })
        if (!obsRes.ok || !obsRes.data) return

        const obs = obsRes.data.items?.[0] || obsRes.data[0]
        if (!obs?.result) return

        // Extract lat/lon from various result shapes
        let lat: number | undefined
        let lon: number | undefined
        let alt: number | undefined
        const result = obs.result
        if (typeof result.lat === 'number' && typeof result.lon === 'number') {
          lat = result.lat; lon = result.lon; alt = result.alt
        } else if (result.Location && typeof result.Location.lat === 'number') {
          lat = result.Location.lat; lon = result.Location.lon; alt = result.Location.alt
        } else if (result.location && typeof result.location.lat === 'number') {
          lat = result.location.lat; lon = result.location.lon; alt = result.location.alt
        }
        if (lat == null || lon == null) return

        systemLocationCache[sysId] = {
          lat, lon, alt,
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
  olFeature.setStyle(getStyle(resourceType, true))
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

  // --- Enrich systems ---
  await enrichSystems()
  // --- Enrich deployments ---
  await enrichDeployments()
  // --- Enrich sampling features ---
  await enrichSamplingFeatures()
}

async function enrichSystems(): Promise<void> {
  const source = vectorSources['systems']
  if (!source) return

  // We need to know which systems were loaded but have no geometry on the map.
  // Re-fetch the raw items list to check which have null geometry.
  try {
    const url = getListUrl('systems', { limit: 200 })
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
    for (const item of items) {
      // Skip if it already has geometry (already on map)
      if (extractGeometry(item)) continue

      const sysId = extractId(item)
      const loc = systemLocationCache[sysId]
      if (!loc) continue

      const feature = createEnrichedFeature(
        item, 'systems', loc.lat, loc.lon,
        `Latest observation from ${loc.datastreamName || 'location datastream'} at ${loc.phenomenonTime || 'unknown time'}`
      )
      source.addFeature(feature)
      enriched++
    }
    enrichedCounts.value['systems'] = enriched
    featureCounts.value['systems'] = (featureCounts.value['systems'] || 0) + enriched
  } catch { /* skip */ }
}

async function enrichDeployments(): Promise<void> {
  const source = vectorSources['deployments']
  if (!source) return

  try {
    const url = getListUrl('deployments', { limit: 200 })
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
    for (const item of items) {
      if (extractGeometry(item)) continue

      // Try to find a deployed system with a known location
      const deployedSystems = item.properties?.['deployedSystems@link'] || item['deployedSystems@link'] || []
      for (const dsl of deployedSystems) {
        const sysHref = dsl.system?.href || dsl.href || ''
        // Extract system ID from href (last path segment)
        const sysId = sysHref.split('/').pop()
        if (sysId && systemLocationCache[sysId]) {
          const loc = systemLocationCache[sysId]
          const feature = createEnrichedFeature(
            item, 'deployments', loc.lat, loc.lon,
            `Derived from deployed system ${sysId} (${loc.datastreamName || 'location obs'})`
          )
          source.addFeature(feature)
          enriched++
          break // one location per deployment is enough
        }
      }
    }
    enrichedCounts.value['deployments'] = enriched
    featureCounts.value['deployments'] = (featureCounts.value['deployments'] || 0) + enriched
  } catch { /* skip */ }
}

async function enrichSamplingFeatures(): Promise<void> {
  const source = vectorSources['samplingFeatures']
  if (!source) return

  // For each system with a known location, fetch its sampling features
  // and enrich any that don't already have geometry on the map
  const alreadyPlottedIds = new Set(
    source.getFeatures().filter(f => f.getGeometry()).map(f => f.get('resourceId'))
  )

  let enriched = 0
  const promises = Object.entries(systemLocationCache).map(async ([sysId, loc]) => {
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
        // Skip if this feature already has geometry on the map
        if (alreadyPlottedIds.has(sfId)) continue
        // Skip if feature has its own geometry
        if (extractGeometry(item)) continue

        const feature = createEnrichedFeature(
          item, 'samplingFeatures', loc.lat, loc.lon,
          `Derived from parent system ${sysId} (${loc.datastreamName || 'location obs'})`
        )
        source.addFeature(feature)
        enriched++
      }
    } catch { /* skip */ }
  })

  await Promise.all(promises)
  enrichedCounts.value['samplingFeatures'] = enriched
  featureCounts.value['samplingFeatures'] = (featureCounts.value['samplingFeatures'] || 0) + enriched
}

/**
 * Load Part 2 DataStreams and place them at their parent system's cached location.
 */
async function loadDatastreams(): Promise<void> {
  const source = vectorSources['datastreams']
  if (!source) return

  let count = 0
  try {
    const res = await apiFetch('/datastreams?limit=200')
    if (!res.ok || !res.data) return

    const items = res.data.items || []
    for (const ds of items) {
      const sysId = ds['system@id'] || ds.system?.id
      if (!sysId) continue
      const loc = systemLocationCache[sysId]
      if (!loc) continue

      const feature = createEnrichedFeature(
        ds, 'datastreams', loc.lat, loc.lon,
        `At parent system ${sysId} (${loc.datastreamName || 'location obs'})`
      )
      source.addFeature(feature)
      count++
    }
  } catch { /* skip */ }
  featureCounts.value['datastreams'] = count
}

/**
 * Load Part 2 ControlStreams and place them at their parent system's cached location.
 */
async function loadControlStreams(): Promise<void> {
  const source = vectorSources['controlStreams']
  if (!source) return

  let count = 0
  try {
    const res = await apiFetch('/controlstreams?limit=200')
    if (!res.ok || !res.data) return

    const items = res.data.items || []
    for (const cs of items) {
      const sysId = cs['system@id'] || cs.system?.id
      if (!sysId) continue
      const loc = systemLocationCache[sysId]
      if (!loc) continue

      const feature = createEnrichedFeature(
        cs, 'controlStreams', loc.lat, loc.lon,
        `At parent system ${sysId} (${loc.datastreamName || 'location obs'})`
      )
      source.addFeature(feature)
      count++
    }
  } catch { /* skip */ }
  featureCounts.value['controlStreams'] = count
}

/**
 * Load observation tracks — GPS trail LineStrings from location datastreams.
 * Fetches recent observations and plots them as a path on the map.
 */
async function loadObservationTracks(): Promise<void> {
  const source = vectorSources['observationTracks']
  if (!source) return

  let count = 0
  const promises = locationDatastreamList.map(async (dsInfo) => {
    try {
      const obsRes = await apiFetch(`/datastreams/${dsInfo.id}/observations?limit=50`, {
        headers: { 'Accept': 'application/om+json' },
      })
      if (!obsRes.ok || !obsRes.data) return

      const items = obsRes.data.items || []
      const coords: [number, number][] = []
      for (const obs of items) {
        const result = obs.result
        let lat: number | undefined, lon: number | undefined
        if (typeof result?.lat === 'number' && typeof result?.lon === 'number') {
          lat = result.lat; lon = result.lon
        } else if (result?.location?.lat != null) {
          lat = result.location.lat; lon = result.location.lon
        } else if (result?.Location?.lat != null) {
          lat = result.Location.lat; lon = result.Location.lon
        }
        if (lat != null && lon != null) {
          coords.push([lon, lat])
        }
      }

      if (coords.length >= 2) {
        const lineFeature = new Feature({
          geometry: new LineString(coords.map(c => fromLonLat(c))),
        })
        lineFeature.setStyle(getStyle('observationTracks'))
        lineFeature.set('resourceType', 'observationTracks')
        lineFeature.set('resourceId', dsInfo.id)
        lineFeature.set('resourceName', `Track: ${dsInfo.name}`)
        lineFeature.set('enriched', true)
        lineFeature.set('enrichmentSource', `${coords.length} observations from ${dsInfo.name}`)
        lineFeature.set('rawData', { datastreamId: dsInfo.id, datastreamName: dsInfo.name, systemId: dsInfo.systemId, pointCount: coords.length })
        source.addFeature(lineFeature)
        count++
      }
    } catch { /* skip */ }
  })

  await Promise.all(promises)
  featureCounts.value['observationTracks'] = count
}

async function loadAllResources() {
  loading.value = true
  error.value = ''
  featureCounts.value = {}
  for (const key of Object.keys(enrichedCounts.value)) delete enrichedCounts.value[key]

  // 1. Load Part 1 resources (systems, deployments, procedures, samplingFeatures)
  const promises = SPATIAL_TYPES.map(async (rt) => {
    const count = await loadResourceType(rt.key)
    featureCounts.value[rt.key] = count
  })
  await Promise.all(promises)

  // 2. Build system location cache from observation data
  await buildSystemLocationCache()

  // 3. Enrich Part 1 resource types that have null geometry
  await enrichResourcesWithLocations()

  // 4. Load Part 2 resources at parent system locations + observation tracks
  await Promise.all([
    loadDatastreams(),
    loadControlStreams(),
    loadObservationTracks(),
  ])

  loading.value = false

  // Fit map to features if any exist
  const allFeatures: Feature[] = []
  for (const src of Object.values(vectorSources)) {
    allFeatures.push(...src.getFeatures())
  }
  if (allFeatures.length > 0 && map) {
    const combinedSource = new VectorSource({ features: allFeatures })
    const ext = combinedSource.getExtent()
    if (ext) map.getView().fit(ext, {
      padding: [50, 50, 50, 50],
      maxZoom: 16,
      duration: 500,
    })
  }
}

function toggleLayer(key: string) {
  activeLayers.value[key] = !activeLayers.value[key]
  const layer = vectorLayers[key]
  if (layer) {
    layer.setVisible(activeLayers.value[key])
  }
}

// --- Map Setup ---

onMounted(() => {
  if (!mapContainer.value || !popupContainer.value) return

  // Create overlay for popup
  overlay = new Overlay({
    element: popupContainer.value,
    autoPan: { animation: { duration: 250 } },
    positioning: 'bottom-center',
    offset: [0, -10],
  })

  // Create vector sources and layers for each map type
  for (const rt of MAP_TYPES) {
    const source = new VectorSource()
    vectorSources[rt.key] = source
    const layer = new VectorLayer({
      source,
      zIndex: rt.key === 'observationTracks' ? 5 : 10,
    })
    vectorLayers[rt.key] = layer
  }

  // Create map
  map = new Map({
    target: mapContainer.value,
    layers: [
      new TileLayer({ source: new OSM() }),
      ...Object.values(vectorLayers),
    ],
    overlays: [overlay],
    view: new View({
      center: fromLonLat([0, 20]),
      zoom: 2,
    }),
  })

  // Click handler for features
  map.on('singleclick', (evt) => {
    let hit = false
    map!.forEachFeatureAtPixel(evt.pixel, (feature) => {
      if (hit) return // only handle first
      hit = true

      const resourceType = feature.get('resourceType')
      const rawData = feature.get('rawData')
      const isEnriched = feature.get('enriched') || false
      const enrichmentSource = feature.get('enrichmentSource') || ''

      // Reset previous selection style
      if (selectedFeature.value?._olFeature) {
        const prevType = selectedFeature.value.resourceType
        const prevEnriched = selectedFeature.value.enriched || false
        selectedFeature.value._olFeature.setStyle(getStyle(prevType, prevEnriched))
      }

      // Highlight new selection
      ;(feature as Feature).setStyle(getSelectedStyle(resourceType))

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

  // Pointer cursor on features
  map.on('pointermove', (evt) => {
    const pixel = map!.getEventPixel(evt.originalEvent)
    const hit = map!.hasFeatureAtPixel(pixel)
    const target = map!.getTargetElement()
    if (target) {
      ;(target as HTMLElement).style.cursor = hit ? 'pointer' : ''
    }
  })

  // Load data
  loadAllResources()
})

onUnmounted(() => {
  if (map) {
    map.setTarget(undefined)
    map = null
  }
})

function closePopup() {
  overlay?.setPosition(undefined)
  if (selectedFeature.value?._olFeature) {
    const prevType = selectedFeature.value.resourceType
    const prevEnriched = selectedFeature.value.enriched || false
    selectedFeature.value._olFeature.setStyle(getStyle(prevType, prevEnriched))
  }
  selectedFeature.value = null
}

function goToDetail() {
  if (selectedFeature.value) {
    router.push(`/explore/${selectedFeature.value.resourceType}`)
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
          v-for="rt in [...PART2_MAP_TYPES, OBS_TRACK_ENTRY]"
          :key="rt.key"
          :class="['layer-toggle', { inactive: !activeLayers[rt.key] }]"
          @click="toggleLayer(rt.key)"
        >
          <span class="layer-dot" :style="{ backgroundColor: TYPE_COLORS[rt.key] }"></span>
          <span class="layer-label">{{ rt.plural }}</span>
          <span class="layer-count">{{ featureCounts[rt.key] ?? '—' }}</span>
        </button>
      </div>

      <!-- Enrichment info -->
      <div v-if="Object.values(enrichedCounts).some(c => c > 0)" class="enrichment-info">
        <span class="enriched-indicator"></span>
        <span class="enrichment-text">
          {{ Object.values(enrichedCounts).reduce((s, n) => s + n, 0) }} locations derived from observations
        </span>
      </div>

      <div class="sidebar-status">
        <template v-if="loading">
          <i class="pi pi-spin pi-spinner"></i> Loading resources...
        </template>
        <template v-else>
          {{ totalFeatures }} features on map
        </template>
      </div>

      <button class="refresh-btn" @click="loadAllResources" :disabled="loading">
        <i class="pi pi-refresh"></i> Reload
      </button>

      <!-- Empty state message -->
      <div v-if="!loading && totalFeatures === 0" class="empty-state">
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

      <!-- Popup overlay (attached to OL overlay, positioned on map) -->
      <div ref="popupContainer" class="ol-popup">
        <a href="#" class="ol-popup-closer" @click.prevent="closePopup"></a>
        <div v-if="selectedFeature" class="popup-content">
          <span class="popup-badge" :style="{ backgroundColor: TYPE_COLORS[selectedFeature.resourceType] }">
            {{ MAP_TYPES.find(r => r.key === selectedFeature.resourceType)?.label }}
          </span>
          <strong>{{ selectedFeature.resourceName }}</strong>
          <div class="popup-id">{{ selectedFeature.resourceId }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.map-page {
  display: flex;
  height: calc(100vh - 53px);
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

.refresh-btn {
  margin: 0 0.75rem 0.75rem;
  padding: 0.5rem;
  border: 1px solid #e2e8f0;
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

.refresh-btn:hover {
  background: #eff6ff;
}

.refresh-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
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

/* OpenLayers popup */
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
</style>
