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
import Polygon from 'ol/geom/Polygon'
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

// All types visible on the map
const MAP_TYPES = [...SPATIAL_TYPES, ...PART2_MAP_TYPES, OBS_POINTS_ENTRY, OBS_TRACK_ENTRY, LOB_ENTRY]

// Color map for resource types
const TYPE_COLORS: Record<string, string> = {
  systems: '#3b82f6',           // blue
  deployments: '#8b5cf6',       // purple
  procedures: '#f59e0b',        // amber
  samplingFeatures: '#10b981',  // emerald
  datastreams: '#ef4444',       // red
  controlStreams: '#f97316',    // orange
  observationTracks: '#06b6d4', // cyan
  observationPoints: '#ec4899', // pink
  bearingLines: '#f43f5e',      // rose
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
  observationPoints: true,
  bearingLines: true,
})

// Cache: systemId → { lat, lon, alt?, datastreamName? }
const systemLocationCache: Record<string, { lat: number; lon: number; alt?: number; datastreamName?: string; phenomenonTime?: string }> = {}
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

// Enable/disable milsymbol rendering (toggle for A/B comparison)
const useMilSymbols = ref(false)

// Basemap toggle (OSM vs satellite)
const useSatellite = ref(false)
let osmLayer: TileLayer | null = null
let satLayer: TileLayer | null = null
let satRefLayer: TileLayer | null = null

function getStyle(resourceType: string, enriched = false, rawData?: any): Style {
  const color = TYPE_COLORS[resourceType] || '#6b7280'
  const label = TYPE_LABELS[resourceType] || '?'

  // Observation tracks are LineStrings — dashed line, no point marker
  if (resourceType === 'observationTracks') {
    return new Style({
      stroke: new Stroke({ color, width: 3, lineDash: [8, 4] }),
    })
  }

  // Individual observation points — tiny dots to show density without clutter
  if (resourceType === 'observationPoints') {
    return new Style({
      image: new CircleStyle({
        radius: 4,
        fill: new Fill({ color }),
        stroke: new Stroke({ color: '#fff', width: 1 }),
      }),
    })
  }

  // Bearing lines — directional lines from sensor locations
  if (resourceType === 'bearingLines') {
    return new Style({
      stroke: new Stroke({ color, width: 2.5 }),
    })
  }

  // --- MIL-STD-2525 symbol rendering ---
  if (useMilSymbols.value && rawData) {
    const sz = getSymbolSizeForType(resourceType)
    const sym = getSymbolForResource(resourceType, rawData, sz)
    if (sym) {
      return new Style({
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
    }
  }

  // --- Fallback: colored circle with letter ---
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

function getSelectedStyle(resourceType: string, rawData?: any): Style {
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

  // --- MIL-STD-2525 selected: render at larger size ---
  if (useMilSymbols.value && rawData) {
    const sym = getSymbolForResource(resourceType, rawData, 'normal')
    if (sym) {
      return new Style({
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
    }
  }

  // --- Fallback: colored circle selected ---
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

async function loadResourceType(resourceType: string): Promise<number> {
  const source = vectorSources[resourceType]
  if (!source) return 0

  source.clear()

  try {
    const url = getListUrl(resourceType, buildQueryOptions())
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
        if (sysId && !systemLocationCache[sysId]) {
          systemLocationCache[sysId] = { lat, lon, datastreamName: 'deployment geometry' }
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

    // Also fetch datastreams for each system in the location cache,
    // since subsystem datastreams may not appear at the global endpoint
    // (OSH nests them under the system hierarchy)
    const seenDsIds = new Set(allDs.map((ds: any) => ds.id))
    const cachedSystemIds = Object.keys(systemLocationCache)
    const systemDsResults = await Promise.all(
      cachedSystemIds.map(async (sysId) => {
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

    // Also include ALL datastreams for systems with cached locations,
    // so observation layers can render geographic observations from any DS
    const locationDsIds = new Set(locationDatastreamList.map(d => d.id))
    for (const ds of allDs) {
      if (locationDsIds.has(ds.id)) continue
      const sysId = ds['system@id'] || ds.system?.id
      if (sysId && systemLocationCache[sysId]) {
        locationDatastreamList.push({
          id: ds.id,
          name: ds.name || ds.outputName || 'Unknown',
          systemId: sysId,
        })
      }
    }

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

    let enriched = 0
    for (const item of items) {
      // Skip if it already has geometry (already on map)
      if (extractGeometry(item)) continue

      const sysId = extractId(item)
      const loc = systemLocationCache[sysId]
      if (!loc) continue

      // When bbox is active, skip if enriched location falls outside
      if (bboxFilter.value) {
        const [minX, minY, maxX, maxY] = bboxFilter.value
        if (loc.lon < minX || loc.lon > maxX || loc.lat < minY || loc.lat > maxY) continue
      }

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
    const url = getListUrl('deployments', buildQueryOptions())
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

          // When bbox is active, skip if enriched location falls outside
          if (bboxFilter.value) {
            const [minX, minY, maxX, maxY] = bboxFilter.value
            if (loc.lon < minX || loc.lon > maxX || loc.lat < minY || loc.lat > maxY) continue
          }

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

  source.clear()
  let count = 0
  try {
    const url = getListUrl('datastreams', buildQueryOptions())
    const res = await apiFetch(url)
    let items: any[] = (res.ok && res.data) ? (res.data.items || []) : []

    // Also fetch datastreams from systems in the location cache,
    // since subsystem datastreams may not appear at the global endpoint
    const seenIds = new Set(items.map((d: any) => d.id))
    const sysResults = await Promise.all(
      Object.keys(systemLocationCache).map(async (sysId) => {
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

  source.clear()
  let count = 0
  try {
    const url = getListUrl('controlStreams', buildQueryOptions())
    const res = await apiFetch(url)
    let items: any[] = (res.ok && res.data) ? (res.data.items || []) : []

    // Also fetch control streams from systems in the location cache
    const seenIds = new Set(items.map((d: any) => d.id))
    const sysResults = await Promise.all(
      Object.keys(systemLocationCache).map(async (sysId) => {
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
              feature.setStyle(getBearingLineStyle(b.energy))
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

  // 4. Load Part 2 resources at parent system locations + observation layers
  await Promise.all([
    loadDatastreams(),
    loadControlStreams(),
    loadObservationLayers(),
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
  for (const rt of MAP_TYPES) {
    const source = new VectorSource()
    vectorSources[rt.key] = source
    const layer = new VectorLayer({
      source,
      zIndex: rt.key === 'observationTracks' ? 5 : rt.key === 'bearingLines' ? 6 : rt.key === 'observationPoints' ? 7 : 10,
    })
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
      // Skip bbox rectangle feature
      if (!feature.get('resourceType')) return
      hit = true

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
  map.on('pointermove', (evt) => {
    const pixel = map!.getEventPixel(evt.originalEvent)
    const hit = map!.hasFeatureAtPixel(pixel)
    const target = map!.getTargetElement()
    if (target) {
      ;(target as HTMLElement).style.cursor = hit ? 'pointer' : ''
    }
    const [lon, lat] = toLonLat(evt.coordinate)
    mouseCoords.value = `${lat.toFixed(5)}°, ${lon.toFixed(5)}°`
  })

  // Map is ready — user must press Search to load data
})

onUnmounted(() => {
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
    </div>
  </div>
</template>

<style scoped>
.map-page {
  display: flex;
  height: calc(100vh - 53px);
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
</style>
