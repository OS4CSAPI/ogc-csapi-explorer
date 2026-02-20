<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { apiFetch } from '../api'
import { getDetailUrl, parseSensorML30 } from '../csapi-bridge'
import ProgressSpinner from 'primevue/progressspinner'
import Message from 'primevue/message'

const props = defineProps<{
  procedureId: string
}>()

const loading = ref(false)
const error = ref('')
const rawData = ref<any>(null)
const parseError = ref('')

// Typed result from parseSensorML30
const parsed = ref<any>(null)

async function fetchSensorML() {
  if (!props.procedureId) return

  loading.value = true
  error.value = ''
  parseError.value = ''
  rawData.value = null
  parsed.value = null

  const processTypes = ['SimpleProcess', 'AggregateProcess', 'PhysicalComponent', 'PhysicalSystem']

  // First, try fetching with Accept: application/sml+json
  const path = getDetailUrl('procedures', props.procedureId)
  let res = await apiFetch(path, {
    headers: { 'Accept': 'application/sml+json, application/json' },
  })

  if (!res.ok) {
    error.value = res.error || 'Failed to fetch SensorML description'
    loading.value = false
    return
  }

  let data = res.data
  if (typeof data === 'string') {
    try { data = JSON.parse(data) } catch { /* leave as-is */ }
  }

  // If the server returned GeoJSON instead of SensorML, look for an
  // alternate link with type=application/sml+json and follow it
  if (data && !processTypes.includes(data.type)) {
    const links = data.links || data.properties?.links || []
    const smlLink = links.find((l: any) =>
      l.type === 'application/sml+json' ||
      (l.href && (l.href.includes('f=sml3') || l.href.includes('f=sml')))
    )
    if (smlLink?.href) {
      // The link is absolute — extract the path portion after the API base
      let smlPath = smlLink.href
      // Convert absolute URL to relative path for apiFetch
      try {
        const url = new URL(smlPath)
        // Use pathname + search as the relative path, strip the API prefix
        smlPath = url.pathname + url.search
        // Strip common API prefixes — apiFetch prepends the proxy base
        const prefixes = ['/sensorhub/api', '/api']
        for (const prefix of prefixes) {
          if (smlPath.startsWith(prefix)) {
            smlPath = smlPath.slice(prefix.length)
            break
          }
        }
      } catch {
        // Not a valid URL — try using as-is
      }

      const smlRes = await apiFetch(smlPath, {
        headers: { 'Accept': 'application/sml+json, application/json' },
      })

      if (smlRes.ok) {
        data = smlRes.data
        if (typeof data === 'string') {
          try { data = JSON.parse(data) } catch { /* leave as-is */ }
        }
      }
    }
  }

  rawData.value = data

  // Only attempt SensorML parse if data has a recognizable process type
  if (data && processTypes.includes(data.type)) {
    try {
      parsed.value = parseSensorML30(data)
    } catch (e: any) {
      parseError.value = e.message || 'SensorML parse failed'
    }
  } else {
    parseError.value = 'Server did not return a SensorML process description. The procedure may not have a SensorML representation.'
  }

  loading.value = false
}

watch(() => props.procedureId, () => {
  if (props.procedureId) fetchSensorML()
}, { immediate: true })

// --- Computed display helpers ---

const processType = computed(() => parsed.value?.type ?? null)
const processLabel = computed(() => parsed.value?.label ?? null)
const uniqueId = computed(() => parsed.value?.uniqueId ?? null)
const description = computed(() => parsed.value?.description ?? null)
const definition = computed(() => parsed.value?.definition ?? null)
const keywords = computed(() => parsed.value?.keywords ?? [])
const validTime = computed(() => parsed.value?.validTime ?? null)

const identifiers = computed(() => parsed.value?.identifiers ?? [])
const classifiers = computed(() => parsed.value?.classifiers ?? [])

const capabilities = computed(() => parsed.value?.capabilities ?? [])
const characteristics = computed(() => parsed.value?.characteristics ?? [])

const inputs = computed(() => parsed.value?.inputs ?? [])
const outputs = computed(() => parsed.value?.outputs ?? [])
const parameters = computed(() => parsed.value?.parameters ?? [])

const contacts = computed(() => parsed.value?.contacts ?? [])
const documents = computed(() => parsed.value?.documents ?? [])
const history = computed(() => parsed.value?.history ?? [])

// Physical process fields
const position = computed(() => parsed.value?.position ?? null)
const attachedTo = computed(() => parsed.value?.attachedTo ?? null)
const localReferenceFrames = computed(() => parsed.value?.localReferenceFrames ?? [])

// Aggregate / PhysicalSystem fields
const components = computed(() => parsed.value?.components ?? [])
const connections = computed(() => parsed.value?.connections ?? [])

// SimpleProcess / PhysicalComponent fields
const method = computed(() => parsed.value?.method ?? null)

const modes = computed(() => parsed.value?.modes ?? [])
const configuration = computed(() => parsed.value?.configuration ?? null)
const featuresOfInterest = computed(() => parsed.value?.featuresOfInterest ?? [])
const typeOf = computed(() => parsed.value?.typeOf ?? null)

/** True when there's at least some parsed content to show */
const hasParsedContent = computed(() => !!parsed.value)

/** Format a TimePeriod for display */
function formatTime(tp: any): string {
  if (!tp) return '—'
  if (typeof tp === 'string') return tp
  if (Array.isArray(tp)) return tp.join(' / ')
  return JSON.stringify(tp)
}

/** Shorten a URI for display */
function shortenUri(uri: string): string {
  if (!uri) return ''
  try {
    const parts = new URL(uri).pathname.split('/').filter(Boolean)
    return parts.length > 2 ? '…/' + parts.slice(-2).join('/') : uri
  } catch {
    return uri.length > 60 ? '…' + uri.slice(-55) : uri
  }
}

/** Get a contact's display name */
function contactName(c: any): string {
  if (c.individualName) return c.individualName
  if (c.organisationName) return c.organisationName
  if (c.title) return c.title
  if (c.href) return shortenUri(c.href)
  return '(unnamed contact)'
}

/** Get component display info */
function componentInfo(c: any): { name: string, type: string, label: string } {
  return {
    name: c.name || '—',
    type: c.type || '—',
    label: c.label || c.title || '',
  }
}

/** Format IOComponentChoice for display */
function ioInfo(io: any): { name: string, type: string, label: string, definition: string } {
  return {
    name: io.name || '—',
    type: io.type || '—',
    label: io.label || '',
    definition: io.definition || '',
  }
}
</script>

<template>
  <details class="sensorml-section" open>
    <summary>
      <i class="pi pi-microchip"></i>
      SensorML Process Description
      <span v-if="processType" class="sml-type-badge">{{ processType }}</span>
    </summary>

    <div v-if="loading" class="sml-loading">
      <ProgressSpinner style="width: 24px; height: 24px" />
      <span>Loading SensorML...</span>
    </div>

    <Message v-if="error" severity="warn" :closable="false" class="sml-msg">
      {{ error }}
    </Message>

    <Message v-if="parseError && rawData" severity="info" :closable="false" class="sml-msg">
      {{ parseError }}
    </Message>

    <template v-if="hasParsedContent">
      <!-- Identity -->
      <div class="sml-card">
        <div class="sml-card-header">
          <i class="pi pi-id-card"></i> Identity
        </div>
        <table class="sml-table">
          <tbody>
            <tr><td class="sml-key">Type</td><td><span class="sml-chip">{{ processType }}</span></td></tr>
            <tr><td class="sml-key">Label</td><td>{{ processLabel }}</td></tr>
            <tr><td class="sml-key">Unique ID</td><td class="sml-mono">{{ uniqueId }}</td></tr>
            <tr v-if="description"><td class="sml-key">Description</td><td>{{ description }}</td></tr>
            <tr v-if="definition"><td class="sml-key">Definition</td><td><a :href="definition" target="_blank" class="sml-link">{{ shortenUri(definition) }}</a></td></tr>
            <tr v-if="validTime"><td class="sml-key">Valid Time</td><td>{{ formatTime(validTime) }}</td></tr>
            <tr v-if="typeOf"><td class="sml-key">Type Of</td><td><a :href="typeOf.href" target="_blank" class="sml-link">{{ typeOf.title || shortenUri(typeOf.href) }}</a></td></tr>
          </tbody>
        </table>
        <div v-if="keywords.length > 0" class="sml-keywords">
          <span v-for="kw in keywords" :key="kw" class="sml-keyword">{{ kw }}</span>
        </div>
      </div>

      <!-- Identifiers -->
      <div v-if="identifiers.length > 0" class="sml-card">
        <div class="sml-card-header">
          <i class="pi pi-tag"></i> Identifiers ({{ identifiers.length }})
        </div>
        <table class="sml-table">
          <thead><tr><th>Label</th><th>Value</th><th>Definition</th></tr></thead>
          <tbody>
            <tr v-for="(t, i) in identifiers" :key="i">
              <td>{{ t.label }}</td>
              <td class="sml-mono">{{ t.value }}</td>
              <td><a v-if="t.definition" :href="t.definition" target="_blank" class="sml-link">{{ shortenUri(t.definition) }}</a></td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Classifiers -->
      <div v-if="classifiers.length > 0" class="sml-card">
        <div class="sml-card-header">
          <i class="pi pi-tags"></i> Classifiers ({{ classifiers.length }})
        </div>
        <table class="sml-table">
          <thead><tr><th>Label</th><th>Value</th><th>Definition</th></tr></thead>
          <tbody>
            <tr v-for="(t, i) in classifiers" :key="i">
              <td>{{ t.label }}</td>
              <td class="sml-mono">{{ t.value }}</td>
              <td><a v-if="t.definition" :href="t.definition" target="_blank" class="sml-link">{{ shortenUri(t.definition) }}</a></td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Capabilities -->
      <div v-if="capabilities.length > 0" class="sml-card">
        <div class="sml-card-header">
          <i class="pi pi-bolt"></i> Capabilities ({{ capabilities.length }} groups)
        </div>
        <div v-for="(capList, ci) in capabilities" :key="ci" class="sml-subgroup">
          <div v-if="capList.label || capList.definition" class="sml-subgroup-header">
            {{ capList.label || '' }}
            <a v-if="capList.definition" :href="capList.definition" target="_blank" class="sml-link sml-link-small">{{ shortenUri(capList.definition) }}</a>
          </div>
          <table class="sml-table">
            <thead><tr><th>Name</th><th>Type</th><th>Value</th><th>UoM</th><th>Definition</th></tr></thead>
            <tbody>
              <tr v-for="(prop, pi) in capList.capabilities" :key="pi">
                <td>{{ prop.name }}</td>
                <td><span class="sml-chip-sm">{{ prop.type }}</span></td>
                <td class="sml-mono">{{ (prop as any).value ?? '—' }}</td>
                <td>{{ (prop as any).uom?.code || (prop as any).uom?.href || '—' }}</td>
                <td><a v-if="(prop as any).definition" :href="(prop as any).definition" target="_blank" class="sml-link">{{ shortenUri((prop as any).definition) }}</a></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Characteristics -->
      <div v-if="characteristics.length > 0" class="sml-card">
        <div class="sml-card-header">
          <i class="pi pi-sliders-h"></i> Characteristics ({{ characteristics.length }} groups)
        </div>
        <div v-for="(charList, ci) in characteristics" :key="ci" class="sml-subgroup">
          <div v-if="charList.label || charList.definition" class="sml-subgroup-header">
            {{ charList.label || '' }}
            <a v-if="charList.definition" :href="charList.definition" target="_blank" class="sml-link sml-link-small">{{ shortenUri(charList.definition) }}</a>
          </div>
          <table class="sml-table">
            <thead><tr><th>Name</th><th>Type</th><th>Value</th><th>UoM</th><th>Definition</th></tr></thead>
            <tbody>
              <tr v-for="(prop, pi) in charList.characteristics" :key="pi">
                <td>{{ prop.name }}</td>
                <td><span class="sml-chip-sm">{{ prop.type }}</span></td>
                <td class="sml-mono">{{ (prop as any).value ?? '—' }}</td>
                <td>{{ (prop as any).uom?.code || (prop as any).uom?.href || '—' }}</td>
                <td><a v-if="(prop as any).definition" :href="(prop as any).definition" target="_blank" class="sml-link">{{ shortenUri((prop as any).definition) }}</a></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Inputs -->
      <div v-if="inputs.length > 0" class="sml-card">
        <div class="sml-card-header">
          <i class="pi pi-sign-in"></i> Inputs ({{ inputs.length }})
        </div>
        <table class="sml-table">
          <thead><tr><th>Name</th><th>Type</th><th>Label</th><th>Definition</th></tr></thead>
          <tbody>
            <tr v-for="(io, i) in inputs" :key="i">
              <td>{{ ioInfo(io).name }}</td>
              <td><span class="sml-chip-sm">{{ ioInfo(io).type }}</span></td>
              <td>{{ ioInfo(io).label }}</td>
              <td><a v-if="ioInfo(io).definition" :href="ioInfo(io).definition" target="_blank" class="sml-link">{{ shortenUri(ioInfo(io).definition) }}</a></td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Outputs -->
      <div v-if="outputs.length > 0" class="sml-card">
        <div class="sml-card-header">
          <i class="pi pi-sign-out"></i> Outputs ({{ outputs.length }})
        </div>
        <table class="sml-table">
          <thead><tr><th>Name</th><th>Type</th><th>Label</th><th>Definition</th></tr></thead>
          <tbody>
            <tr v-for="(io, i) in outputs" :key="i">
              <td>{{ ioInfo(io).name }}</td>
              <td><span class="sml-chip-sm">{{ ioInfo(io).type }}</span></td>
              <td>{{ ioInfo(io).label }}</td>
              <td><a v-if="ioInfo(io).definition" :href="ioInfo(io).definition" target="_blank" class="sml-link">{{ shortenUri(ioInfo(io).definition) }}</a></td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Parameters -->
      <div v-if="parameters.length > 0" class="sml-card">
        <div class="sml-card-header">
          <i class="pi pi-cog"></i> Parameters ({{ parameters.length }})
        </div>
        <table class="sml-table">
          <thead><tr><th>Name</th><th>Type</th><th>Label</th><th>Definition</th></tr></thead>
          <tbody>
            <tr v-for="(io, i) in parameters" :key="i">
              <td>{{ ioInfo(io).name }}</td>
              <td><span class="sml-chip-sm">{{ ioInfo(io).type }}</span></td>
              <td>{{ ioInfo(io).label }}</td>
              <td><a v-if="ioInfo(io).definition" :href="ioInfo(io).definition" target="_blank" class="sml-link">{{ shortenUri(ioInfo(io).definition) }}</a></td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Components (AggregateProcess / PhysicalSystem) -->
      <div v-if="components.length > 0" class="sml-card">
        <div class="sml-card-header">
          <i class="pi pi-th-large"></i> Components ({{ components.length }})
        </div>
        <table class="sml-table">
          <thead><tr><th>Name</th><th>Type</th><th>Label</th></tr></thead>
          <tbody>
            <tr v-for="(c, i) in components" :key="i">
              <td>{{ componentInfo(c).name }}</td>
              <td><span class="sml-chip-sm">{{ componentInfo(c).type }}</span></td>
              <td>{{ componentInfo(c).label }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Connections (AggregateProcess / PhysicalSystem) -->
      <div v-if="connections.length > 0" class="sml-card">
        <div class="sml-card-header">
          <i class="pi pi-arrow-right-arrow-left"></i> Connections ({{ connections.length }})
        </div>
        <table class="sml-table">
          <thead><tr><th>Source</th><th></th><th>Destination</th></tr></thead>
          <tbody>
            <tr v-for="(conn, i) in connections" :key="i">
              <td class="sml-mono">{{ conn.source }}</td>
              <td style="text-align:center; color:#94a3b8;">→</td>
              <td class="sml-mono">{{ conn.destination }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Method (SimpleProcess / PhysicalComponent) -->
      <div v-if="method" class="sml-card">
        <div class="sml-card-header">
          <i class="pi pi-code"></i> Process Method
        </div>
        <p v-if="method.description" class="sml-method-desc">{{ method.description }}</p>
        <pre v-if="method.algorithm" class="sml-raw">{{ JSON.stringify(method.algorithm, null, 2) }}</pre>
      </div>

      <!-- Position (PhysicalComponent / PhysicalSystem) -->
      <div v-if="position" class="sml-card">
        <div class="sml-card-header">
          <i class="pi pi-map-marker"></i> Position
        </div>
        <div v-if="typeof position === 'string'" class="sml-position-text">{{ position }}</div>
        <div v-else-if="position.type === 'Point'" class="sml-position-text">
          GeoJSON Point: {{ position.coordinates.join(', ') }}
        </div>
        <div v-else-if="position.position" class="sml-position-text">
          Pose — Position: {{ position.position?.coordinates?.join(', ') || '—' }}
          <span v-if="position.angles"> | Orientation: yaw={{ position.angles.yaw }}, pitch={{ position.angles.pitch }}, roll={{ position.angles.roll }}</span>
        </div>
        <pre v-else class="sml-raw">{{ JSON.stringify(position, null, 2) }}</pre>
      </div>

      <!-- Attached To (Physical processes) -->
      <div v-if="attachedTo" class="sml-card">
        <div class="sml-card-header">
          <i class="pi pi-link"></i> Attached To
        </div>
        <a :href="attachedTo.href" target="_blank" class="sml-link">{{ attachedTo.title || shortenUri(attachedTo.href) }}</a>
      </div>

      <!-- Local Reference Frames -->
      <div v-if="localReferenceFrames.length > 0" class="sml-card">
        <div class="sml-card-header">
          <i class="pi pi-compass"></i> Local Reference Frames ({{ localReferenceFrames.length }})
        </div>
        <div v-for="(frame, fi) in localReferenceFrames" :key="fi" class="sml-subgroup">
          <div class="sml-subgroup-header">{{ frame.label || `Frame ${fi + 1}` }}</div>
          <p v-if="frame.origin" class="sml-frame-origin">Origin: {{ frame.origin }}</p>
          <table class="sml-table" v-if="frame.axes?.length">
            <thead><tr><th>Axis</th><th>Description</th></tr></thead>
            <tbody>
              <tr v-for="(axis, ai) in frame.axes" :key="ai">
                <td class="sml-mono">{{ axis.name }}</td>
                <td>{{ axis.description }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Contacts -->
      <div v-if="contacts.length > 0" class="sml-card">
        <div class="sml-card-header">
          <i class="pi pi-users"></i> Contacts ({{ contacts.length }})
        </div>
        <div v-for="(c, i) in contacts" :key="i" class="sml-contact">
          <span class="sml-contact-name">{{ contactName(c) }}</span>
          <span v-if="c.role" class="sml-chip-sm">{{ shortenUri(c.role) }}</span>
          <span v-if="c.positionName" class="sml-contact-pos">{{ c.positionName }}</span>
        </div>
      </div>

      <!-- Documents -->
      <div v-if="documents.length > 0" class="sml-card">
        <div class="sml-card-header">
          <i class="pi pi-file"></i> Documentation ({{ documents.length }})
        </div>
        <div v-for="(doc, i) in documents" :key="i" class="sml-doc">
          <a v-if="doc.link?.href" :href="doc.link.href" target="_blank" class="sml-link">{{ doc.name || shortenUri(doc.link.href) }}</a>
          <span v-else>{{ doc.name }}</span>
          <span v-if="doc.description" class="sml-doc-desc">— {{ doc.description }}</span>
        </div>
      </div>

      <!-- History / Events -->
      <div v-if="history.length > 0" class="sml-card">
        <div class="sml-card-header">
          <i class="pi pi-history"></i> History ({{ history.length }} events)
        </div>
        <table class="sml-table">
          <thead><tr><th>Label</th><th>Time</th><th>Type</th></tr></thead>
          <tbody>
            <tr v-for="(evt, i) in history" :key="i">
              <td>{{ evt.label }}</td>
              <td>{{ formatTime(evt.time) }}</td>
              <td><a v-if="evt.definition" :href="evt.definition" target="_blank" class="sml-link">{{ shortenUri(evt.definition) }}</a><span v-else>—</span></td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Modes -->
      <div v-if="modes.length > 0" class="sml-card">
        <div class="sml-card-header">
          <i class="pi pi-sliders-v"></i> Operating Modes ({{ modes.length }})
        </div>
        <div v-for="(mode, i) in modes" :key="i" class="sml-mode">
          <span class="sml-chip-sm">{{ mode.label }}</span>
          <span v-if="mode.description" class="sml-mode-desc">{{ mode.description }}</span>
        </div>
      </div>

      <!-- Configuration / Settings -->
      <div v-if="configuration" class="sml-card">
        <div class="sml-card-header">
          <i class="pi pi-wrench"></i> Configuration
        </div>
        <pre class="sml-raw">{{ JSON.stringify(configuration, null, 2) }}</pre>
      </div>

      <!-- Features of Interest -->
      <div v-if="featuresOfInterest.length > 0" class="sml-card">
        <div class="sml-card-header">
          <i class="pi pi-globe"></i> Features of Interest ({{ featuresOfInterest.length }})
        </div>
        <div v-for="(foi, i) in featuresOfInterest" :key="i" class="sml-foi">
          <a v-if="foi.href" :href="foi.href" target="_blank" class="sml-link">{{ foi.title || shortenUri(foi.href) }}</a>
          <span v-else>{{ foi.title || '(unnamed)' }}</span>
        </div>
      </div>
    </template>

    <!-- Raw JSON fallback -->
    <details v-if="rawData" class="sml-raw-section">
      <summary>Raw SensorML JSON</summary>
      <pre class="sml-raw">{{ JSON.stringify(rawData, null, 2) }}</pre>
    </details>
  </details>
</template>

<style scoped>
.sensorml-section {
  margin-top: 0.75rem;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  overflow: hidden;
}
.sensorml-section > summary {
  cursor: pointer;
  font-weight: 700;
  font-size: 0.9rem;
  padding: 0.65rem 0.85rem;
  background: #fdf4ff;
  color: #7e22ce;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  border-bottom: 1px solid #f0abfc;
  user-select: none;
}
.sml-type-badge {
  background: #a855f7;
  color: #fff;
  font-size: 0.7rem;
  font-weight: 700;
  padding: 0.1rem 0.5rem;
  border-radius: 999px;
}

.sml-loading {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem;
  color: #64748b;
  font-size: 0.85rem;
}
.sml-msg {
  margin: 0.5rem 0.75rem;
}

/* Cards */
.sml-card {
  margin: 0.5rem 0.75rem;
  border: 1px solid #e9d5ff;
  border-radius: 6px;
  overflow: hidden;
}
.sml-card-header {
  background: #faf5ff;
  padding: 0.4rem 0.65rem;
  font-weight: 700;
  font-size: 0.8rem;
  color: #6b21a8;
  display: flex;
  align-items: center;
  gap: 0.35rem;
  border-bottom: 1px solid #e9d5ff;
}

/* Tables */
.sml-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.78rem;
}
.sml-table th {
  background: #faf5ff;
  padding: 0.3rem 0.5rem;
  text-align: left;
  font-weight: 600;
  color: #7e22ce;
  font-size: 0.72rem;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}
.sml-table td {
  padding: 0.3rem 0.5rem;
  border-top: 1px solid #f3e8ff;
  color: #334155;
}
.sml-key {
  font-weight: 600;
  color: #6b21a8;
  white-space: nowrap;
  width: 110px;
}
.sml-mono {
  font-family: 'Cascadia Code', 'Fira Code', monospace;
  font-size: 0.74rem;
  word-break: break-all;
}

/* Chips */
.sml-chip {
  display: inline-block;
  background: #a855f7;
  color: #fff;
  font-size: 0.72rem;
  font-weight: 700;
  padding: 0.1rem 0.5rem;
  border-radius: 4px;
}
.sml-chip-sm {
  display: inline-block;
  background: #e9d5ff;
  color: #6b21a8;
  font-size: 0.68rem;
  font-weight: 600;
  padding: 0.05rem 0.35rem;
  border-radius: 3px;
}

/* Keywords */
.sml-keywords {
  padding: 0.35rem 0.5rem;
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem;
  border-top: 1px solid #f3e8ff;
}
.sml-keyword {
  background: #f3e8ff;
  color: #7e22ce;
  font-size: 0.7rem;
  padding: 0.1rem 0.4rem;
  border-radius: 999px;
}

/* Links */
.sml-link {
  color: #7c3aed;
  text-decoration: none;
  font-size: 0.78rem;
}
.sml-link:hover {
  text-decoration: underline;
}
.sml-link-small {
  font-size: 0.7rem;
  margin-left: 0.3rem;
}

/* Subgroups */
.sml-subgroup {
  border-top: 1px solid #f3e8ff;
}
.sml-subgroup:first-child {
  border-top: none;
}
.sml-subgroup-header {
  padding: 0.3rem 0.5rem;
  font-weight: 600;
  font-size: 0.76rem;
  color: #7e22ce;
  background: #faf5ff;
}

/* Contacts */
.sml-contact {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.35rem 0.65rem;
  border-top: 1px solid #f3e8ff;
  font-size: 0.8rem;
}
.sml-contact:first-child { border-top: none; }
.sml-contact-name { font-weight: 600; color: #334155; }
.sml-contact-pos { color: #94a3b8; font-size: 0.75rem; }

/* Docs */
.sml-doc {
  padding: 0.3rem 0.65rem;
  border-top: 1px solid #f3e8ff;
  font-size: 0.8rem;
}
.sml-doc:first-child { border-top: none; }
.sml-doc-desc { color: #64748b; font-size: 0.75rem; }

/* Modes */
.sml-mode {
  padding: 0.3rem 0.65rem;
  display: flex;
  align-items: center;
  gap: 0.4rem;
  border-top: 1px solid #f3e8ff;
  font-size: 0.8rem;
}
.sml-mode:first-child { border-top: none; }
.sml-mode-desc { color: #64748b; font-size: 0.75rem; }

/* Features of Interest */
.sml-foi {
  padding: 0.3rem 0.65rem;
  border-top: 1px solid #f3e8ff;
  font-size: 0.8rem;
}
.sml-foi:first-child { border-top: none; }

/* Position */
.sml-position-text { padding: 0.4rem 0.65rem; font-size: 0.8rem; color: #334155; }

/* Method */
.sml-method-desc { padding: 0.4rem 0.65rem; font-size: 0.8rem; color: #334155; margin: 0; }

/* Frame origin */
.sml-frame-origin { padding: 0.3rem 0.5rem; font-size: 0.78rem; color: #64748b; margin: 0; }

/* Raw JSON */
.sml-raw-section {
  margin: 0.5rem 0.75rem;
}
.sml-raw-section summary {
  cursor: pointer;
  font-size: 0.78rem;
  font-weight: 600;
  color: #64748b;
  padding: 0.25rem 0;
}
.sml-raw {
  background: #f8fafc;
  padding: 0.5rem;
  font-size: 0.72rem;
  max-height: 400px;
  overflow: auto;
  border-radius: 4px;
  border: 1px solid #e2e8f0;
  margin: 0.25rem 0;
}
</style>
