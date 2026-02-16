<script setup lang="ts">
/**
 * Displays the ogc-client library's parsed/typed output for a CSAPI resource.
 *
 * For Part 1 recognized resources: shows extractCSAPIFeature() typed fields
 * (name, description, uid, featureType, validTime as Dates, geometry, links).
 * For unrecognized resources: shows parseCollectionResponse metadata if applicable.
 * Includes a type badge from getCSAPIResourceType().
 */
import { computed } from 'vue'
import {
  extractCSAPIFeature,
  getCSAPIResourceType,
} from '../csapi-bridge'

const props = defineProps<{
  /** Raw server JSON for one resource */
  resource: any
  /** The current resource type key (e.g. 'systems', 'datastreams') */
  resourceType: string
}>()

// ─── Library recognition ─────────────────────────────────────
const recognizedType = computed(() => {
  if (!props.resource) return null
  try {
    return getCSAPIResourceType(props.resource)
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

// ─── Part 2 / flat resource fields ──────────────────────────
const isPart2 = computed(() =>
  ['datastreams', 'observations', 'controlStreams', 'commands', 'properties'].includes(props.resourceType)
)

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
.unrecognized { background: #fefce8; border: 1px solid #fef08a; color: #854d0e; }
.unrecognized i { color: #ca8a04; }

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
