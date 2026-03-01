<script setup lang="ts">
/**
 * Structured form for creating/editing Part 1 CSAPI resources.
 *
 * Supports: systems, deployments, procedures, samplingFeatures.
 * Builds a GeoJSON Feature body from individual fields.
 * Includes a "Raw JSON" toggle for advanced editing.
 */
import { ref, computed, watch, onBeforeUnmount, nextTick } from 'vue'
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'
import Dropdown from 'primevue/dropdown'
import InputNumber from 'primevue/inputnumber'
import Checkbox from 'primevue/checkbox'

// OpenLayers — lightweight map picker
import OlMap from 'ol/Map'
import OlView from 'ol/View'
import TileLayer from 'ol/layer/Tile'
import VectorLayer from 'ol/layer/Vector'
import VectorSource from 'ol/source/Vector'
import XYZ from 'ol/source/XYZ'
import { fromLonLat, toLonLat } from 'ol/proj'
import Feature from 'ol/Feature'
import Point from 'ol/geom/Point'
import { Style, Circle as CircleStyle, Fill, Stroke } from 'ol/style'

const props = defineProps<{
  resourceType: string
  /** Pre-populate the form from existing JSON (for update mode) */
  initialJson?: string
}>()

const emit = defineEmits<{
  (e: 'update:json', value: string): void
}>()

// ─── Form mode toggle ───────────────────────────────────────
const rawMode = ref(false)
const rawJson = ref('')

// ─── Form fields ────────────────────────────────────────────
const name = ref('')
const description = ref('')
const featureType = ref('')
const uid = ref('')
const definition = ref('')
const validTimeBegin = ref('')
const validTimeEnd = ref('')
const hasGeometry = ref(false)
const lat = ref<number | null>(null)
const lon = ref<number | null>(null)

// ─── Feature type options ───────────────────────────────────
const SYSTEM_FEATURE_TYPES = [
  { label: 'Platform (sosa:Platform)', value: 'http://www.w3.org/ns/sosa/Platform' },
  { label: 'Sensor (sosa:Sensor)', value: 'http://www.w3.org/ns/sosa/Sensor' },
  { label: 'Actuator (sosa:Actuator)', value: 'http://www.w3.org/ns/sosa/Actuator' },
  { label: 'Sampler (sosa:Sampler)', value: 'http://www.w3.org/ns/sosa/Sampler' },
]
const PROCEDURE_FEATURE_TYPES = [
  { label: 'Procedure (sosa:Procedure)', value: 'http://www.w3.org/ns/sosa/Procedure' },
  { label: 'Datasheet', value: 'http://www.w3.org/ns/ssn/systems/Datasheet' },
]
const SAMPLING_FEATURE_TYPES = [
  { label: 'Sample (sosa:Sample)', value: 'http://www.w3.org/ns/sosa/Sample' },
  { label: 'Specimen', value: 'http://www.w3.org/ns/sosa/Specimen' },
]

// Which resource types support structured forms
const STRUCTURED_TYPES = new Set(['systems', 'deployments', 'procedures', 'samplingFeatures'])
const supportsStructuredForm = computed(() => STRUCTURED_TYPES.has(props.resourceType))

const featureTypeOptions = computed(() => {
  if (props.resourceType === 'systems') return SYSTEM_FEATURE_TYPES
  if (props.resourceType === 'procedures') return PROCEDURE_FEATURE_TYPES
  if (props.resourceType === 'samplingFeatures') return SAMPLING_FEATURE_TYPES
  return []
})

const showFeatureType = computed(() => ['systems', 'procedures', 'samplingFeatures'].includes(props.resourceType))
const showUid = computed(() => props.resourceType === 'systems')
const showDefinition = computed(() => props.resourceType === 'procedures')
const showValidTime = computed(() => props.resourceType === 'deployments')
const showGeometry = computed(() => ['systems', 'samplingFeatures', 'deployments'].includes(props.resourceType))

// ─── Build JSON from form fields ────────────────────────────
const builtJson = computed(() => {
  const properties: Record<string, any> = {}
  if (name.value) properties.name = name.value
  if (description.value) properties.description = description.value
  if (featureType.value && showFeatureType.value) properties.featureType = featureType.value
  if (uid.value && showUid.value) properties.uid = uid.value
  if (definition.value && showDefinition.value) properties.definition = definition.value
  if (showValidTime.value) {
    const vt: Record<string, string> = {}
    if (validTimeBegin.value) vt.begin = validTimeBegin.value
    if (validTimeEnd.value) vt.end = validTimeEnd.value
    if (Object.keys(vt).length > 0) properties.validTime = vt
  }

  let geometry: any = null
  if (hasGeometry.value && lat.value !== null && lon.value !== null) {
    geometry = {
      type: 'Point',
      coordinates: [lon.value, lat.value],
    }
  }

  return {
    type: 'Feature',
    properties,
    geometry,
  }
})

const formattedJson = computed(() => JSON.stringify(builtJson.value, null, 2))

// ─── Emit on changes ────────────────────────────────────────
watch([formattedJson, rawJson, rawMode], () => {
  emit('update:json', rawMode.value ? rawJson.value : formattedJson.value)
}, { immediate: true })

// Sync raw editor when toggling
watch(rawMode, (isRaw) => {
  if (isRaw) {
    rawJson.value = formattedJson.value
  }
})

// ─── Populate from initial JSON (update mode) ───────────────
watch(() => props.initialJson, (json) => {
  if (!json) return
  try {
    const obj = JSON.parse(json)
    // Part 1 GeoJSON Feature
    if (obj.properties) {
      name.value = obj.properties.name || ''
      description.value = obj.properties.description || ''
      featureType.value = obj.properties.featureType || ''
      uid.value = obj.properties.uid || ''
      definition.value = obj.properties.definition || ''
      if (obj.properties.validTime) {
        validTimeBegin.value = obj.properties.validTime.begin || obj.properties.validTime.start || ''
        validTimeEnd.value = obj.properties.validTime.end || ''
      }
    }
    if (obj.geometry && obj.geometry.type === 'Point' && obj.geometry.coordinates) {
      hasGeometry.value = true
      lon.value = obj.geometry.coordinates[0] ?? null
      lat.value = obj.geometry.coordinates[1] ?? null
    }
    // Also set raw JSON for toggle
    rawJson.value = json
  } catch {
    rawJson.value = json
    rawMode.value = true
  }
}, { immediate: true })

// ─── Validation ─────────────────────────────────────────────
const nameError = computed(() => !name.value ? 'Name is required' : '')
const isValid = computed(() => !!name.value)
defineExpose({ isValid })

// ─── Mini map picker ────────────────────────────────────────
const mapContainer = ref<HTMLElement | null>(null)
let miniMap: OlMap | null = null
let markerSource: VectorSource | null = null
let mapResizeObserver: ResizeObserver | null = null
const mapReady = ref(false)

const MARKER_STYLE = new Style({
  image: new CircleStyle({
    radius: 7,
    fill: new Fill({ color: '#2563eb' }),
    stroke: new Stroke({ color: '#ffffff', width: 2.5 }),
  }),
})

function initMiniMap() {
  if (miniMap) return
  const el = mapContainer.value
  if (!el) return

  // Ensure the container is visible and has real dimensions before creating the map
  const rect = el.getBoundingClientRect()
  if (rect.width === 0 || rect.height === 0) {
    // Container isn't laid out yet — wait for ResizeObserver to fire
    if (!mapResizeObserver) {
      mapResizeObserver = new ResizeObserver(() => {
        const r = el.getBoundingClientRect()
        if (r.width > 0 && r.height > 0) {
          initMiniMap()
        }
      })
      mapResizeObserver.observe(el)
    }
    return
  }

  markerSource = new VectorSource()

  const satelliteLayer = new TileLayer({
    source: new XYZ({
      url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
      maxZoom: 19,
      attributions: 'Tiles © Esri',
    }),
  })

  const labelsLayer = new TileLayer({
    source: new XYZ({
      url: 'https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}',
      maxZoom: 19,
    }),
  })

  const markerLayer = new VectorLayer({
    source: markerSource,
    style: MARKER_STYLE,
  })

  // Center on current coords or a world-level default
  const startLon = lon.value ?? 0
  const startLat = lat.value ?? 30
  const startZoom = (lat.value !== null && lon.value !== null) ? 17 : 3

  miniMap = new OlMap({
    target: el,
    layers: [satelliteLayer, labelsLayer, markerLayer],
    view: new OlView({
      center: fromLonLat([startLon, startLat]),
      zoom: startZoom,
    }),
    controls: [],
  })

  // Keep the observer alive so OL stays in sync if the container resizes
  if (!mapResizeObserver) {
    mapResizeObserver = new ResizeObserver(() => miniMap?.updateSize())
    mapResizeObserver.observe(el)
  }

  // Place initial marker if we have coords
  if (lat.value !== null && lon.value !== null) {
    placeMarker(lon.value, lat.value)
  }

  // Click → pick new location
  miniMap.on('click', (evt) => {
    const [newLon, newLat] = toLonLat(evt.coordinate)
    lat.value = Math.round(newLat * 1e7) / 1e7
    lon.value = Math.round(newLon * 1e7) / 1e7
    placeMarker(lon.value, lat.value)
  })

  mapReady.value = true
}

function placeMarker(lng: number, latitude: number) {
  if (!markerSource) return
  markerSource.clear()
  markerSource.addFeature(
    new Feature({ geometry: new Point(fromLonLat([lng, latitude])) }),
  )
}

function destroyMiniMap() {
  if (mapResizeObserver) {
    mapResizeObserver.disconnect()
    mapResizeObserver = null
  }
  if (miniMap) {
    miniMap.setTarget(undefined)
    miniMap = null
    markerSource = null
  }
  mapReady.value = false
}

// Recreate map when the geometry section appears/disappears
watch([hasGeometry, () => showGeometry.value], async ([geo, show]) => {
  if (geo && show) {
    await nextTick()
    initMiniMap()
  } else {
    destroyMiniMap()
  }
})

// Sync marker when lat/lon fields are edited manually
watch([lat, lon], ([newLat, newLon]) => {
  if (miniMap && newLat !== null && newLon !== null) {
    placeMarker(newLon, newLat)
  }
})

onBeforeUnmount(() => destroyMiniMap())
</script>

<template>
  <div v-if="supportsStructuredForm" class="structured-form">
    <!-- Mode toggle -->
    <div class="mode-toggle">
      <label class="toggle-label">
        <Checkbox v-model="rawMode" :binary="true" />
        <span>Raw JSON editor</span>
      </label>
    </div>

    <!-- Structured fields -->
    <div v-if="!rawMode" class="form-fields">
      <div class="form-field" :class="{ 'has-error': nameError }">
        <label>Name <span class="required">*</span></label>
        <InputText v-model="name" placeholder="Resource name" class="field-input" />
        <small v-if="nameError" class="field-error">{{ nameError }}</small>
      </div>

      <div class="form-field">
        <label>Description</label>
        <Textarea v-model="description" rows="2" placeholder="Optional description" class="field-input" />
      </div>

      <div v-if="showFeatureType" class="form-field">
        <label>Feature Type</label>
        <Dropdown
          v-model="featureType"
          :options="featureTypeOptions"
          optionLabel="label"
          optionValue="value"
          placeholder="Select feature type"
          class="field-input"
          :editable="true"
        />
      </div>

      <div v-if="showUid" class="form-field">
        <label>UID</label>
        <InputText v-model="uid" placeholder="Unique identifier (URN)" class="field-input" />
      </div>

      <div v-if="showDefinition" class="form-field">
        <label>Definition</label>
        <InputText v-model="definition" placeholder="Procedure definition URI" class="field-input" />
      </div>

      <div v-if="showValidTime" class="form-field">
        <label>Valid Time — Begin</label>
        <InputText v-model="validTimeBegin" :placeholder="new Date().toISOString()" class="field-input" />
      </div>
      <div v-if="showValidTime" class="form-field">
        <label>Valid Time — End</label>
        <InputText v-model="validTimeEnd" placeholder="(leave empty for ongoing)" class="field-input" />
      </div>

      <div v-if="showGeometry" class="form-field">
        <label class="toggle-label">
          <Checkbox v-model="hasGeometry" :binary="true" />
          <span>Include Point geometry</span>
        </label>
      </div>
      <div v-if="showGeometry && hasGeometry" class="form-row">
        <div class="form-field half">
          <label>Latitude</label>
          <InputNumber v-model="lat" :minFractionDigits="1" :maxFractionDigits="8" :min="-90" :max="90" placeholder="0.0" class="field-input" />
        </div>
        <div class="form-field half">
          <label>Longitude</label>
          <InputNumber v-model="lon" :minFractionDigits="1" :maxFractionDigits="8" :min="-180" :max="180" placeholder="0.0" class="field-input" />
        </div>
      </div>

      <!-- Mini map picker for point geometry -->
      <div v-if="showGeometry && hasGeometry" class="map-picker-container">
        <label class="map-picker-label">Click the map to set location</label>
        <div ref="mapContainer" class="map-picker"></div>
      </div>

      <!-- JSON preview -->
      <details class="json-preview-section">
        <summary>JSON Preview</summary>
        <pre class="json-preview">{{ formattedJson }}</pre>
      </details>
    </div>

    <!-- Raw JSON editor -->
    <div v-else class="editor-container">
      <label>Request Body (JSON):</label>
      <Textarea
        v-model="rawJson"
        rows="16"
        class="json-editor"
        spellcheck="false"
      />
    </div>
  </div>
</template>

<style scoped>
.structured-form { display: flex; flex-direction: column; gap: 0.75rem; }
.mode-toggle { display: flex; align-items: center; }
.toggle-label { display: flex; align-items: center; gap: 0.5rem; font-size: 0.9rem; color: #475569; cursor: pointer; }
.form-fields { display: flex; flex-direction: column; gap: 0.75rem; }
.form-field { display: flex; flex-direction: column; gap: 0.25rem; }
.form-field label { font-weight: 600; font-size: 0.85rem; color: #475569; }
.required { color: #dc2626; }
.field-input { width: 100%; }
.field-error { color: #dc2626; font-size: 0.78rem; }
.has-error :deep(.p-inputtext) { border-color: #dc2626; }
.form-row { display: flex; gap: 0.75rem; }
.form-field.half { flex: 1; }
.json-preview-section { margin-top: 0.25rem; }
.json-preview-section summary { cursor: pointer; font-weight: 600; font-size: 0.85rem; color: #64748b; }
.json-preview { background: #f8fafc; padding: 0.75rem; border-radius: 6px; overflow-x: auto; font-size: 0.75rem; max-height: 300px; overflow-y: auto; margin-top: 0.25rem; }
.editor-container { display: flex; flex-direction: column; gap: 0.25rem; }
.editor-container label { font-weight: 600; font-size: 0.9rem; }
.json-editor { font-family: 'Consolas', 'Monaco', monospace; font-size: 0.85rem; width: 100%; resize: vertical; }
.map-picker-container { display: flex; flex-direction: column; gap: 0.25rem; }
.map-picker-label { font-weight: 600; font-size: 0.85rem; color: #64748b; }
.map-picker { width: 100%; height: 260px; border-radius: 8px; border: 1px solid #cbd5e1; position: relative; cursor: crosshair; }
.map-picker :deep(.ol-viewport) { border-radius: 8px; }
</style>
