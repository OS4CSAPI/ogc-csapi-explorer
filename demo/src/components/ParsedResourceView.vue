<script setup lang="ts">
/**
 * Displays the ogc-client library's parsed/typed output for a CSAPI resource.
 *
 * For Part 1 recognized resources: shows extractCSAPIFeature() typed fields
 * (name, description, uid, featureType, validTime as Dates, geometry, links).
 * For Part 2 resources: uses typed parsers (parseDatastream, parseObservation, etc.)
 * to show structured fields with proper type conversion.
 * For unrecognized resources: shows raw field extraction.
 * Includes a type badge from getCSAPIResourceType() with 52North fallback.
 */
import { computed } from 'vue'
import {
  extractCSAPIFeature,
  getCSAPIResourceType,
  classifyResource,
  parsePart2Resource,
} from '../csapi-bridge'
import ObservationResultTable from './ObservationResultTable.vue'
import CommandStatusHistory from './CommandStatusHistory.vue'

const props = defineProps<{
  /** Raw server JSON for one resource */
  resource: any
  /** The current resource type key (e.g. 'systems', 'datastreams') */
  resourceType: string
  /** The endpoint URL this resource was fetched from (used for 52North classification fallback) */
  endpointUrl?: string
}>()

// ─── Parent datastream ID extraction ────────────────────────
/**
 * Extract the parent datastream ID from the raw observation JSON.
 * OGC Connected Systems observations carry `datastream@id` as a
 * cross-reference field in the server response.
 */
const parentDatastreamId = computed<string | null>(() => {
  if (props.resourceType !== 'observations') return null
  const raw = props.resource
  if (!raw) return null
  // Check datastream@id (standard cross-reference in API JSON)
  if (typeof raw['datastream@id'] === 'string') return raw['datastream@id']
  // Check links for a 'datastream' rel
  if (Array.isArray(raw.links)) {
    const dsLink = raw.links.find((l: any) => l.rel === 'datastream' || l.rel === 'collection')
    if (dsLink?.href) {
      // Extract ID from href like /datastreams/abc
      const match = dsLink.href.match(/datastreams\/([^/?]+)/)
      if (match) return match[1]
    }
  }
  return null
})

// ─── Parent control stream ID extraction ─────────────────────
/**
 * Extract the parent control stream ID from the raw command JSON.
 * Commands carry `controlstream@id` as a cross-reference field.
 * Needed because OSH only exposes commands nested under control streams.
 */
const parentControlStreamId = computed<string | null>(() => {
  if (props.resourceType !== 'commands') return null
  const raw = props.resource
  if (!raw) return null
  if (typeof raw['controlstream@id'] === 'string') return raw['controlstream@id']
  if (Array.isArray(raw.links)) {
    const csLink = raw.links.find((l: any) => l.rel === 'controlstream' || l.rel === 'collection')
    if (csLink?.href) {
      const match = csLink.href.match(/controlstreams\/([^/?]+)/)
      if (match) return match[1]
    }
  }
  return null
})

// ─── Library recognition ─────────────────────────────────────
const recognizedType = computed(() => {
  if (!props.resource) return null
  try {
    // Use classifyResource which tries featureType first, then falls back to URL path
    // (handles 52North's featureType:null issue)
    return classifyResource(props.resource, props.endpointUrl) ?? getCSAPIResourceType(props.resource)
  } catch {
    return null
  }
})

const typedResource = computed(() => {
  if (!props.resource || !recognizedType.value) return null
  try {
    return extractCSAPIFeature(props.resource)
  } catch {
    return null
  }
})

// ─── Part 2 typed parsing ───────────────────────────────────
const PART_2_TYPES = ['datastreams', 'observations', 'controlStreams', 'commands', 'properties']

const isPart2 = computed(() => PART_2_TYPES.includes(props.resourceType))

const parsedPart2 = computed(() => {
  if (!props.resource || !isPart2.value) return null
  return parsePart2Resource(props.resourceType, props.resource)
})

/** Label for the parser function used */
const part2ParserName = computed(() => {
  switch (props.resourceType) {
    case 'datastreams': return 'parseDatastream()'
    case 'observations': return 'parseObservation()'
    case 'controlStreams': return 'parseControlStream()'
    case 'commands': return 'parseCommand()'
    case 'properties': return 'parseProperty()'
    default: return null
  }
})

// ─── ValidTime formatting ───────────────────────────────────
function formatDate(d: Date | undefined): string {
  if (!d) return '(ongoing / now)'
  return d.toISOString()
}

// ─── Geometry summary ───────────────────────────────────────
function geometrySummary(geom: any): string {
  if (!geom) return 'null'
  if (geom.type === 'Point' && Array.isArray(geom.coordinates)) {
    const [lon, lat] = geom.coordinates
    return `Point [${lat}, ${lon}]`
  }
  return `${geom.type} (${JSON.stringify(geom.coordinates).slice(0, 60)}…)`
}
</script>

<template>
  <div class="parsed-view">
    <!-- Recognition badge -->
    <div v-if="recognizedType" class="badge recognized">
      <i class="pi pi-check-circle"></i>
      <span><strong>{{ recognizedType }}</strong> — recognized by <code>getCSAPIResourceType()</code></span>
    </div>
    <div v-else-if="parsedPart2" class="badge part2-recognized">
      <i class="pi pi-check-circle"></i>
      <span><strong>{{ resourceType }}</strong> — parsed by <code>{{ part2ParserName }}</code></span>
    </div>
    <div v-else class="badge unrecognized">
      <i class="pi pi-info-circle"></i>
      <span>Not recognized by <code>getCSAPIResourceType()</code> — {{ isPart2 ? 'Part 2 resource (no GeoJSON feature)' : 'missing or unknown featureType' }}</span>
    </div>

    <!-- Part 1: Typed fields from extractCSAPIFeature() -->
    <div v-if="typedResource" class="typed-fields">
      <h4 class="section-title">
        <code>extractCSAPIFeature()</code> output
      </h4>

      <table class="field-table">
        <tbody>
          <tr>
            <td class="field-label">id</td>
            <td><code>{{ typedResource.id }}</code></td>
            <td class="field-type">string</td>
          </tr>
          <tr>
            <td class="field-label">type</td>
            <td>{{ typedResource.type }}</td>
            <td class="field-type">literal</td>
          </tr>
          <tr>
            <td class="field-label">properties.name</td>
            <td>{{ typedResource.properties?.name || '—' }}</td>
            <td class="field-type">string</td>
          </tr>
          <tr v-if="typedResource.properties?.description">
            <td class="field-label">properties.description</td>
            <td>{{ typedResource.properties.description }}</td>
            <td class="field-type">string</td>
          </tr>
          <tr>
            <td class="field-label">properties.featureType</td>
            <td><code>{{ typedResource.properties?.featureType || '—' }}</code></td>
            <td class="field-type">string (URI)</td>
          </tr>
          <tr>
            <td class="field-label">properties.uid</td>
            <td><code>{{ typedResource.properties?.uid || '—' }}</code></td>
            <td class="field-type">string (URN)</td>
          </tr>
          <tr v-if="(typedResource.properties as any)?.assetType">
            <td class="field-label">properties.assetType</td>
            <td>{{ (typedResource.properties as any).assetType }}</td>
            <td class="field-type">enum</td>
          </tr>
          <tr v-if="(typedResource.properties as any)?.validTime">
            <td class="field-label">properties.validTime.start</td>
            <td class="date-value">
              <code>{{ formatDate((typedResource.properties as any).validTime.start) }}</code>
              <span class="converted-badge">Date object</span>
            </td>
            <td class="field-type">Date</td>
          </tr>
          <tr v-if="(typedResource.properties as any)?.validTime">
            <td class="field-label">properties.validTime.end</td>
            <td class="date-value">
              <code>{{ formatDate((typedResource.properties as any).validTime.end) }}</code>
              <span class="converted-badge">Date object</span>
            </td>
            <td class="field-type">Date | undefined</td>
          </tr>
          <tr>
            <td class="field-label">geometry</td>
            <td>{{ geometrySummary(typedResource.geometry) }}</td>
            <td class="field-type">Geometry | null</td>
          </tr>
          <tr>
            <td class="field-label">links</td>
            <td>{{ typedResource.links?.length || 0 }} link(s)</td>
            <td class="field-type">ResourceLink[]</td>
          </tr>
        </tbody>
      </table>

      <!-- Links detail -->
      <details v-if="typedResource.links?.length" class="links-section">
        <summary>Parsed links ({{ typedResource.links.length }})</summary>
        <table class="links-table">
          <thead><tr><th>rel</th><th>type</th><th>href</th><th>title</th></tr></thead>
          <tbody>
            <tr v-for="(link, i) in typedResource.links" :key="i">
              <td><code>{{ link.rel }}</code></td>
              <td>{{ link.type || '—' }}</td>
              <td class="href-cell">{{ link.href }}</td>
              <td>{{ link.title || '—' }}</td>
            </tr>
          </tbody>
        </table>
      </details>
    </div>

    <!-- Part 2: Typed fields from library parsers -->
    <div v-else-if="parsedPart2" class="typed-fields">
      <h4 class="section-title">
        <code>{{ part2ParserName }}</code> output
      </h4>

      <table class="field-table">
        <tbody>
          <tr v-if="parsedPart2.id">
            <td class="field-label">id</td>
            <td><code>{{ parsedPart2.id }}</code></td>
            <td class="field-type">string</td>
          </tr>
          <tr v-if="parsedPart2.name">
            <td class="field-label">name</td>
            <td>{{ parsedPart2.name }}</td>
            <td class="field-type">string</td>
          </tr>
          <tr v-if="parsedPart2.description">
            <td class="field-label">description</td>
            <td>{{ parsedPart2.description }}</td>
            <td class="field-type">string</td>
          </tr>
          <!-- Datastream-specific fields -->
          <tr v-if="parsedPart2.outputName">
            <td class="field-label">outputName</td>
            <td><code>{{ parsedPart2.outputName }}</code></td>
            <td class="field-type">string</td>
          </tr>
          <tr v-if="parsedPart2.observedProperties?.length">
            <td class="field-label">observedProperties</td>
            <td><code>{{ parsedPart2.observedProperties.join(', ') }}</code></td>
            <td class="field-type">string[]</td>
          </tr>
          <tr v-if="parsedPart2.resultType !== undefined">
            <td class="field-label">resultType</td>
            <td><code>{{ parsedPart2.resultType ?? 'null' }}</code></td>
            <td class="field-type">enum | null</td>
          </tr>
          <tr v-if="parsedPart2.live !== undefined">
            <td class="field-label">live</td>
            <td>
              <span :class="parsedPart2.live ? 'live-badge live' : 'live-badge'">
                {{ parsedPart2.live ? 'LIVE' : 'false' }}
              </span>
            </td>
            <td class="field-type">boolean | null</td>
          </tr>
          <tr v-if="parsedPart2.formats?.length">
            <td class="field-label">formats</td>
            <td><code>{{ parsedPart2.formats.join(', ') }}</code></td>
            <td class="field-type">string[]</td>
          </tr>
          <!-- Datastream type classification -->
          <tr v-if="parsedPart2.type">
            <td class="field-label">type</td>
            <td>
              <span class="type-badge">{{ parsedPart2.type }}</span>
            </td>
            <td class="field-type">'status' | 'observation'</td>
          </tr>
          <!-- ControlStream-specific fields -->
          <tr v-if="parsedPart2.inputName">
            <td class="field-label">inputName</td>
            <td><code>{{ parsedPart2.inputName }}</code></td>
            <td class="field-type">string</td>
          </tr>
          <tr v-if="parsedPart2.controlledProperties?.length">
            <td class="field-label">controlledProperties</td>
            <td><code>{{ parsedPart2.controlledProperties.join(', ') }}</code></td>
            <td class="field-type">string[]</td>
          </tr>
          <tr v-if="parsedPart2.async !== undefined">
            <td class="field-label">async</td>
            <td>
              <span :class="parsedPart2.async ? 'async-badge async-true' : 'async-badge'">
                {{ parsedPart2.async ? 'ASYNC' : 'sync' }}
              </span>
            </td>
            <td class="field-type">boolean</td>
          </tr>
          <!-- Observation-specific fields (plain ISO strings, NOT TimeInterval) -->
          <tr v-if="parsedPart2.phenomenonTime && typeof parsedPart2.phenomenonTime === 'string'">
            <td class="field-label">phenomenonTime</td>
            <td class="date-value">
              <code>{{ parsedPart2.phenomenonTime }}</code>
              <span class="converted-badge">string (ISO)</span>
            </td>
            <td class="field-type">string</td>
          </tr>
          <!-- Datastream-level phenomenonTime (TimeInterval extent) -->
          <tr v-else-if="parsedPart2.phenomenonTime && parsedPart2.phenomenonTime.start">
            <td class="field-label">phenomenonTime</td>
            <td class="date-value">
              <code>{{ formatDate(parsedPart2.phenomenonTime.start) }}</code>
              <span v-if="parsedPart2.phenomenonTime.end"> → <code>{{ formatDate(parsedPart2.phenomenonTime.end) }}</code></span>
              <span class="converted-badge">TimeInterval</span>
            </td>
            <td class="field-type">TimeInterval</td>
          </tr>
          <!-- Observation resultTime (plain ISO string) -->
          <tr v-if="parsedPart2.resultTime && typeof parsedPart2.resultTime === 'string'">
            <td class="field-label">resultTime</td>
            <td class="date-value">
              <code>{{ parsedPart2.resultTime }}</code>
              <span class="converted-badge">string (ISO)</span>
            </td>
            <td class="field-type">string</td>
          </tr>
          <!-- Datastream-level resultTime (TimeInterval extent) -->
          <tr v-else-if="parsedPart2.resultTime && parsedPart2.resultTime.start">
            <td class="field-label">resultTime</td>
            <td class="date-value">
              <code>{{ formatDate(parsedPart2.resultTime.start) }}</code>
              <span v-if="parsedPart2.resultTime.end"> → <code>{{ formatDate(parsedPart2.resultTime.end) }}</code></span>
              <span class="converted-badge">TimeInterval</span>
            </td>
            <td class="field-type">TimeInterval</td>
          </tr>
          <tr v-if="parsedPart2.result !== undefined">
            <td class="field-label">result</td>
            <td colspan="2">
              <ObservationResultTable
                :result="parsedPart2.result"
                :datastreamId="parentDatastreamId"
              />
            </td>
          </tr>
          <!-- Command-specific fields -->
          <tr v-if="parsedPart2.issueTime">
            <td class="field-label">issueTime</td>
            <td class="date-value">
              <code>{{ parsedPart2.issueTime }}</code>
              <span class="converted-badge">string (ISO)</span>
            </td>
            <td class="field-type">string</td>
          </tr>
          <tr v-if="parsedPart2.executionTime">
            <td class="field-label">executionTime</td>
            <td class="date-value">
              <code>{{ formatDate(parsedPart2.executionTime.start) }}</code>
              <span v-if="parsedPart2.executionTime.end"> → <code>{{ formatDate(parsedPart2.executionTime.end) }}</code></span>
              <span class="converted-badge">TimeInterval</span>
            </td>
            <td class="field-type">TimeInterval</td>
          </tr>
          <tr v-if="parsedPart2.currentStatus">
            <td class="field-label">currentStatus</td>
            <td>
              <span class="status-badge">{{ parsedPart2.currentStatus }}</span>
            </td>
            <td class="field-type">CommandStatusCode</td>
          </tr>
          <tr v-if="parsedPart2.sender">
            <td class="field-label">sender</td>
            <td><code>{{ parsedPart2.sender }}</code></td>
            <td class="field-type">string</td>
          </tr>
          <tr v-if="parsedPart2.parameters !== undefined">
            <td class="field-label">parameters</td>
            <td><code>{{ typeof parsedPart2.parameters === 'object' ? JSON.stringify(parsedPart2.parameters).slice(0, 200) : parsedPart2.parameters }}</code></td>
            <td class="field-type">{{ typeof parsedPart2.parameters }}</td>
          </tr>
          <!-- Command status history panel -->
          <tr v-if="resourceType === 'commands' && parsedPart2.id">
            <td class="field-label">statusHistory</td>
            <td colspan="2">
              <CommandStatusHistory :commandId="parsedPart2.id" :controlStreamId="parentControlStreamId" />
            </td>
          </tr>
          <!-- Property-specific fields -->
          <tr v-if="parsedPart2.definition">
            <td class="field-label">definition</td>
            <td><code>{{ parsedPart2.definition }}</code></td>
            <td class="field-type">string (URI)</td>
          </tr>
          <tr v-if="parsedPart2.label">
            <td class="field-label">label</td>
            <td>{{ parsedPart2.label }}</td>
            <td class="field-type">string</td>
          </tr>
          <tr v-if="parsedPart2.uniqueId">
            <td class="field-label">uniqueId</td>
            <td><code>{{ parsedPart2.uniqueId }}</code></td>
            <td class="field-type">string (URI)</td>
          </tr>
          <tr v-if="parsedPart2.baseProperty">
            <td class="field-label">baseProperty</td>
            <td><code>{{ parsedPart2.baseProperty }}</code></td>
            <td class="field-type">string (URI)</td>
          </tr>
          <tr v-if="parsedPart2.objectType">
            <td class="field-label">objectType</td>
            <td><code>{{ parsedPart2.objectType }}</code></td>
            <td class="field-type">string (URI)</td>
          </tr>
          <tr v-if="parsedPart2.statistic">
            <td class="field-label">statistic</td>
            <td><code>{{ parsedPart2.statistic }}</code></td>
            <td class="field-type">string (URI)</td>
          </tr>
          <!-- ValidTime (shared across types) -->
          <tr v-if="parsedPart2.validTime">
            <td class="field-label">validTime.start</td>
            <td class="date-value">
              <code>{{ formatDate(parsedPart2.validTime.start) }}</code>
              <span class="converted-badge">Date object</span>
            </td>
            <td class="field-type">Date</td>
          </tr>
          <tr v-if="parsedPart2.validTime">
            <td class="field-label">validTime.end</td>
            <td class="date-value">
              <code>{{ formatDate(parsedPart2.validTime.end) }}</code>
              <span class="converted-badge">Date object</span>
            </td>
            <td class="field-type">Date | undefined</td>
          </tr>
          <tr v-if="parsedPart2.links?.length">
            <td class="field-label">links</td>
            <td>{{ parsedPart2.links.length }} link(s)</td>
            <td class="field-type">ResourceLink[]</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Part 2 / unrecognized: show flat field extraction -->
    <div v-else class="flat-fields">
      <h4 class="section-title">Extracted fields (raw)</h4>
      <table class="field-table">
        <tbody>
          <tr v-if="resource.id">
            <td class="field-label">id</td>
            <td><code>{{ resource.id }}</code></td>
            <td class="field-type">string</td>
          </tr>
          <tr v-if="resource.name">
            <td class="field-label">name</td>
            <td>{{ resource.name }}</td>
            <td class="field-type">string</td>
          </tr>
          <tr v-if="resource.description">
            <td class="field-label">description</td>
            <td>{{ resource.description }}</td>
            <td class="field-type">string</td>
          </tr>
          <!-- Part 2 specific fields -->
          <tr v-if="resource.outputName">
            <td class="field-label">outputName</td>
            <td><code>{{ resource.outputName }}</code></td>
            <td class="field-type">string</td>
          </tr>
          <tr v-if="resource.inputName">
            <td class="field-label">inputName</td>
            <td><code>{{ resource.inputName }}</code></td>
            <td class="field-type">string</td>
          </tr>
          <tr v-if="resource.phenomenonTime">
            <td class="field-label">phenomenonTime</td>
            <td><code>{{ resource.phenomenonTime }}</code></td>
            <td class="field-type">string (ISO)</td>
          </tr>
          <tr v-if="resource.resultTime">
            <td class="field-label">resultTime</td>
            <td><code>{{ resource.resultTime }}</code></td>
            <td class="field-type">string (ISO)</td>
          </tr>
          <tr v-if="resource.issueTime">
            <td class="field-label">issueTime</td>
            <td><code>{{ resource.issueTime }}</code></td>
            <td class="field-type">string (ISO)</td>
          </tr>
          <tr v-if="resource.result !== undefined">
            <td class="field-label">result</td>
            <td><code>{{ typeof resource.result === 'object' ? JSON.stringify(resource.result).slice(0, 100) : resource.result }}</code></td>
            <td class="field-type">{{ typeof resource.result }}</td>
          </tr>
          <tr v-if="resource.parameters !== undefined">
            <td class="field-label">parameters</td>
            <td><code>{{ typeof resource.parameters === 'object' ? JSON.stringify(resource.parameters).slice(0, 100) : resource.parameters }}</code></td>
            <td class="field-type">{{ typeof resource.parameters }}</td>
          </tr>
          <!-- GeoJSON properties fallback -->
          <tr v-if="resource.properties?.name">
            <td class="field-label">properties.name</td>
            <td>{{ resource.properties.name }}</td>
            <td class="field-type">string</td>
          </tr>
          <tr v-if="resource.properties?.description">
            <td class="field-label">properties.description</td>
            <td>{{ resource.properties.description }}</td>
            <td class="field-type">string</td>
          </tr>
          <tr v-if="resource.properties?.featureType">
            <td class="field-label">properties.featureType</td>
            <td><code>{{ resource.properties.featureType }}</code></td>
            <td class="field-type">string (URI)</td>
          </tr>
          <tr v-if="resource.properties?.validTime">
            <td class="field-label">properties.validTime</td>
            <td><code>{{ JSON.stringify(resource.properties.validTime) }}</code></td>
            <td class="field-type">raw (not converted)</td>
          </tr>
          <tr v-if="resource.geometry !== undefined">
            <td class="field-label">geometry</td>
            <td>{{ geometrySummary(resource.geometry) }}</td>
            <td class="field-type">raw GeoJSON</td>
          </tr>
          <tr v-if="resource.links?.length">
            <td class="field-label">links</td>
            <td>{{ resource.links.length }} link(s)</td>
            <td class="field-type">array</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.parsed-view { display: flex; flex-direction: column; gap: 0.75rem; }

.badge { display: flex; align-items: center; gap: 0.5rem; padding: 0.5rem 0.75rem; border-radius: 6px; font-size: 0.85rem; }
.badge code { font-size: 0.78rem; background: rgba(0,0,0,0.06); padding: 0.1rem 0.3rem; border-radius: 3px; }
.recognized { background: #f0fdf4; border: 1px solid #bbf7d0; color: #166534; }
.recognized i { color: #16a34a; }
.part2-recognized { background: #eff6ff; border: 1px solid #bfdbfe; color: #1e40af; }
.part2-recognized i { color: #3b82f6; }
.unrecognized { background: #fefce8; border: 1px solid #fef08a; color: #854d0e; }
.unrecognized i { color: #ca8a04; }

.live-badge { font-size: 0.75rem; padding: 0.15rem 0.4rem; border-radius: 4px; font-weight: 700; background: #f1f5f9; color: #64748b; }
.live-badge.live { background: #dcfce7; color: #166534; animation: pulse-live 2s ease-in-out infinite; }
@keyframes pulse-live { 0%, 100% { opacity: 1; } 50% { opacity: 0.7; } }
.status-badge { font-size: 0.78rem; padding: 0.15rem 0.4rem; border-radius: 4px; font-weight: 600; background: #e0e7ff; color: #3730a3; }
.type-badge { font-size: 0.75rem; padding: 0.15rem 0.4rem; border-radius: 4px; font-weight: 600; background: #fef3c7; color: #92400e; }
.async-badge { font-size: 0.75rem; padding: 0.15rem 0.4rem; border-radius: 4px; font-weight: 700; background: #f1f5f9; color: #64748b; }
.async-badge.async-true { background: #dbeafe; color: #1e40af; }

.section-title { font-size: 0.85rem; margin: 0; color: #334155; font-weight: 600; }
.section-title code { font-size: 0.78rem; color: #7c3aed; background: #ede9fe; padding: 0.1rem 0.4rem; border-radius: 3px; }

.field-table { width: 100%; border-collapse: collapse; font-size: 0.82rem; }
.field-table td { padding: 0.35rem 0.5rem; border-bottom: 1px solid #f1f5f9; vertical-align: top; }
.field-label { font-weight: 600; color: #475569; white-space: nowrap; min-width: 160px; font-family: 'Consolas', 'Monaco', monospace; font-size: 0.78rem; }
.field-type { color: #94a3b8; font-size: 0.75rem; font-style: italic; white-space: nowrap; text-align: right; }
.field-table code { font-size: 0.78rem; background: #f1f5f9; padding: 0.1rem 0.3rem; border-radius: 3px; word-break: break-all; }

.date-value { display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap; }
.converted-badge { font-size: 0.7rem; background: #dbeafe; color: #1e40af; padding: 0.1rem 0.35rem; border-radius: 3px; font-weight: 600; }

.links-section { margin-top: 0.25rem; }
.links-section summary { cursor: pointer; font-weight: 600; font-size: 0.82rem; color: #64748b; }
.links-table { width: 100%; border-collapse: collapse; font-size: 0.78rem; margin-top: 0.25rem; }
.links-table th, .links-table td { padding: 0.3rem 0.4rem; text-align: left; border-bottom: 1px solid #f1f5f9; }
.links-table th { background: #f8fafc; font-weight: 600; font-size: 0.75rem; color: #64748b; }
.links-table code { font-size: 0.75rem; }
.href-cell { font-family: monospace; font-size: 0.72rem; word-break: break-all; max-width: 250px; }
</style>
