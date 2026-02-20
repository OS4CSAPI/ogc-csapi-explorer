<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { apiFetch } from '../api'
import { getSchemaUrl, getControlStreamSchemaUrl, parseSWEComponent, parseDatastreamSchemaResponse, parseControlStreamSchemaResponse } from '../csapi-bridge'
import type { AnyComponent } from '../csapi-bridge'
import ProgressSpinner from 'primevue/progressspinner'
import Message from 'primevue/message'

const props = defineProps<{
  datastreamId?: string
  controlStreamId?: string
}>()

/** Derived mode — determines which parser and URL builder to use */
const mode = computed<'datastream' | 'controlstream'>(() =>
  props.controlStreamId ? 'controlstream' : 'datastream'
)
const activeId = computed(() => props.controlStreamId || props.datastreamId || '')
const sectionTitle = computed(() => mode.value === 'controlstream' ? 'Command Schema' : 'Observation Schema')
const sectionIcon = computed(() => mode.value === 'controlstream' ? 'pi pi-sliders-h' : 'pi pi-sitemap')

const loading = ref(false)
const error = ref('')
const rawSchema = ref<any>(null)

/**
 * Typed envelope from the library's parseDatastreamSchemaResponse().
 * Contains: obsFormat, resultSchema?, recordSchema?, encoding?
 */
const parsedEnvelope = ref<{
  obsFormat: string
  resultSchema?: AnyComponent
  recordSchema?: AnyComponent
  encoding?: any
} | null>(null)

/**
 * Recursively flatten an AnyComponent into a flat list of displayable fields.
 * Each entry has: name, type, label, definition, uom.
 * Nested DataRecords / Vectors / DataArrays are expanded with dotted names.
 */
interface SchemaField {
  name: string
  type: string
  label?: string
  definition?: string
  uom?: string
  depth: number
}

function flattenComponent(component: AnyComponent, prefix: string, depth: number): SchemaField[] {
  const fields: SchemaField[] = []

  if (component.type === 'DataRecord') {
    for (const f of (component as any).fields ?? []) {
      const name = prefix ? `${prefix}.${f.name}` : f.name
      // Each field is a DataField — it has name + the component properties merged in
      const fieldType: string = f.type || 'unknown'
      fields.push({
        name,
        type: fieldType,
        label: f.label,
        definition: f.definition,
        uom: f.uom?.code || f.uom?.href || f.uom?.label,
        depth,
      })
      // Recurse if this field is itself a record/vector/array
      if (fieldType === 'DataRecord' || fieldType === 'Vector' || fieldType === 'DataArray' || fieldType === 'DataChoice') {
        try {
          const nested = parseSWEComponent(f)
          fields.push(...flattenComponent(nested, name, depth + 1))
        } catch { /* non-parseable nested — skip */ }
      }
    }
  } else if (component.type === 'Vector') {
    for (const c of (component as any).coordinates ?? []) {
      const name = prefix ? `${prefix}.${c.name}` : c.name
      fields.push({
        name,
        type: c.type || 'Quantity',
        label: c.label,
        definition: c.definition,
        uom: c.uom?.code || c.uom?.href || c.uom?.label,
        depth,
      })
    }
  } else if (component.type === 'DataArray') {
    const et = (component as any).elementType
    if (et) {
      const name = prefix ? `${prefix}[*]` : `[*]`
      fields.push({
        name,
        type: et.type || 'element',
        label: et.label,
        definition: et.definition,
        uom: et.uom?.code || et.uom?.href || et.uom?.label,
        depth,
      })
      if (et.type === 'DataRecord' || et.type === 'Vector') {
        try {
          const nested = parseSWEComponent(et)
          fields.push(...flattenComponent(nested, name, depth + 1))
        } catch { /* skip */ }
      }
    }
  } else if (component.type === 'DataChoice') {
    for (const item of (component as any).items ?? []) {
      const name = prefix ? `${prefix}|${item.name}` : item.name
      fields.push({
        name,
        type: item.type || 'unknown',
        label: item.label,
        definition: item.definition,
        uom: item.uom?.code || item.uom?.href || item.uom?.label,
        depth,
      })
    }
  } else {
    // Simple scalar component at top level
    fields.push({
      name: prefix || '(root)',
      type: component.type,
      label: (component as any).label,
      definition: (component as any).definition,
      uom: (component as any).uom?.code || (component as any).uom?.href,
      depth,
    })
  }

  return fields
}

/** Fields from the resultSchema (JSON observation format) */
const resultSchemaFields = computed<SchemaField[]>(() => {
  if (!parsedEnvelope.value?.resultSchema) return []
  return flattenComponent(parsedEnvelope.value.resultSchema, '', 0)
})

/** Fields from the recordSchema (SWE Common observation format) */
const recordSchemaFields = computed<SchemaField[]>(() => {
  if (!parsedEnvelope.value?.recordSchema) return []
  return flattenComponent(parsedEnvelope.value.recordSchema, '', 0)
})

/** Backward-compatible: first available schema fields for single-schema display */
const schemaFields = computed<SchemaField[]>(() => {
  return resultSchemaFields.value.length ? resultSchemaFields.value : recordSchemaFields.value
})

const hasResultSchema = computed(() => resultSchemaFields.value.length > 0)
const hasRecordSchema = computed(() => recordSchemaFields.value.length > 0)
const hasBothSchemas = computed(() => hasResultSchema.value && hasRecordSchema.value)

const resultSchemaTypeLabel = computed(() => parsedEnvelope.value?.resultSchema?.type ?? null)
const recordSchemaTypeLabel = computed(() => parsedEnvelope.value?.recordSchema?.type ?? null)

const obsFormat = computed(() => parsedEnvelope.value?.obsFormat || null)
/** commandFormat is present only for control stream schemas */
const commandFormat = computed(() => (parsedEnvelope.value as any)?.commandFormat || null)
/** Show obsFormat or commandFormat depending on mode */
const formatBadge = computed(() => commandFormat.value || obsFormat.value || null)
const encoding = computed(() => parsedEnvelope.value?.encoding ?? null)

async function fetchSchema() {
  const url = mode.value === 'controlstream'
    ? getControlStreamSchemaUrl(activeId.value)
    : getSchemaUrl(activeId.value)
  if (!url) {
    error.value = `Schema URL not available (builder not initialized or ${mode.value === 'controlstream' ? 'controlStreams' : 'datastreams'} unavailable)`
    return
  }

  loading.value = true
  error.value = ''
  rawSchema.value = null
  parsedEnvelope.value = null

  const res = await apiFetch(url, {
    headers: { 'Accept': 'application/swe+json, application/json' },
  })

  if (!res.ok) {
    error.value = res.error || 'Failed to fetch schema'
    loading.value = false
    return
  }

  // apiFetch may return a string if Content-Type is not json (e.g. OSH returns "auto")
  let data = res.data
  if (typeof data === 'string') {
    try { data = JSON.parse(data) } catch { /* leave as string — will fail gracefully */ }
  }

  rawSchema.value = data

  // Use the library's schema response parser appropriate for the mode.
  // Datastream: parseDatastreamSchemaResponse() → { obsFormat, resultSchema, recordSchema, encoding }
  // ControlStream: parseControlStreamSchemaResponse() → { commandFormat, parametersSchema, encoding }
  try {
    if (mode.value === 'controlstream') {
      const envelope = parseControlStreamSchemaResponse(data)
      if (envelope.parametersSchema) {
        // Map parametersSchema into resultSchema slot for unified rendering
        parsedEnvelope.value = {
          obsFormat: '',
          resultSchema: envelope.parametersSchema,
          encoding: envelope.encoding,
          ...({ commandFormat: envelope.commandFormat } as any),
        }
      } else {
        // Bare SWE component fallback
        const component = parseSWEComponent(data)
        parsedEnvelope.value = { obsFormat: '', resultSchema: component }
      }
    } else {
      const envelope = parseDatastreamSchemaResponse(data)
      if (envelope.resultSchema || envelope.recordSchema) {
        parsedEnvelope.value = envelope
      } else {
        const component = parseSWEComponent(data)
        parsedEnvelope.value = { obsFormat: '', resultSchema: component }
      }
    }
  } catch (outerErr: any) {
    // Parser failed — try bare SWE component fallback
    try {
      const component = parseSWEComponent(data)
      parsedEnvelope.value = { obsFormat: '', resultSchema: component }
    } catch (innerErr: any) {
      error.value = `Schema fetched but parsing failed: ${innerErr.message || innerErr}`
      // Still show raw JSON even when parsing fails
    }
  }

  loading.value = false
}

watch(() => activeId.value, () => {
  if (activeId.value) fetchSchema()
}, { immediate: true })

/** Shorten a definition URI for display — show last 1-2 path segments */
function shortenUri(uri: string): string {
  try {
    const parts = new URL(uri).pathname.split('/').filter(Boolean)
    return parts.length > 2 ? '…/' + parts.slice(-2).join('/') : uri
  } catch {
    // Not a valid URL — just truncate
    return uri.length > 50 ? '…' + uri.slice(-45) : uri
  }
}
</script>

<template>
  <details class="schema-section" open>
    <summary>
      <i :class="sectionIcon"></i>
      {{ sectionTitle }}
      <span v-if="!hasBothSchemas && (resultSchemaTypeLabel || recordSchemaTypeLabel)" class="schema-type-badge">{{ resultSchemaTypeLabel || recordSchemaTypeLabel }}</span>
      <span v-if="formatBadge" class="schema-format-badge">{{ formatBadge }}</span>
    </summary>

    <div v-if="loading" class="schema-loading">
      <ProgressSpinner style="width: 24px; height: 24px" />
      <span>Loading schema...</span>
    </div>

    <Message v-if="error && !rawSchema" severity="warn" :closable="false" class="schema-error">
      {{ error }}
    </Message>

    <!-- Parse warning (raw data available but parsing had issues) -->
    <div v-if="error && rawSchema" class="schema-parse-warn">
      <i class="pi pi-exclamation-triangle"></i>
      <span>{{ error }}</span>
    </div>

    <!-- Result Schema (JSON observation format) -->
    <div v-if="hasResultSchema" class="schema-parsed">
      <div v-if="hasBothSchemas" class="schema-section-label">
        <i class="pi pi-table"></i> Result Schema
        <span v-if="resultSchemaTypeLabel" class="schema-type-badge">{{ resultSchemaTypeLabel }}</span>
      </div>
      <table class="schema-table">
        <thead>
          <tr>
            <th>Field</th>
            <th>Type</th>
            <th>Label</th>
            <th>UoM</th>
            <th>Definition</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(field, i) in resultSchemaFields" :key="'r-' + i" :class="{ 'nested-row': field.depth > 0 }">
            <td>
              <span :style="{ paddingLeft: field.depth * 16 + 'px' }">
                <code>{{ field.name }}</code>
              </span>
            </td>
            <td><span class="type-chip">{{ field.type }}</span></td>
            <td>{{ field.label || '—' }}</td>
            <td><code v-if="field.uom">{{ field.uom }}</code><span v-else>—</span></td>
            <td class="definition-cell">
              <a v-if="field.definition" :href="field.definition" target="_blank" rel="noopener" :title="field.definition">
                {{ shortenUri(field.definition) }}
              </a>
              <span v-else>—</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Record Schema (SWE Common observation format) -->
    <div v-if="hasRecordSchema" class="schema-parsed">
      <div class="schema-section-label">
        <i class="pi pi-table"></i> Record Schema
        <span v-if="recordSchemaTypeLabel" class="schema-type-badge">{{ recordSchemaTypeLabel }}</span>
      </div>
      <table class="schema-table">
        <thead>
          <tr>
            <th>Field</th>
            <th>Type</th>
            <th>Label</th>
            <th>UoM</th>
            <th>Definition</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(field, i) in recordSchemaFields" :key="'s-' + i" :class="{ 'nested-row': field.depth > 0 }">
            <td>
              <span :style="{ paddingLeft: field.depth * 16 + 'px' }">
                <code>{{ field.name }}</code>
              </span>
            </td>
            <td><span class="type-chip">{{ field.type }}</span></td>
            <td>{{ field.label || '—' }}</td>
            <td><code v-if="field.uom">{{ field.uom }}</code><span v-else>—</span></td>
            <td class="definition-cell">
              <a v-if="field.definition" :href="field.definition" target="_blank" rel="noopener" :title="field.definition">
                {{ shortenUri(field.definition) }}
              </a>
              <span v-else>—</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Encoding section -->
    <details v-if="encoding" class="schema-encoding-section" open>
      <summary class="schema-section-label">
        <i class="pi pi-code"></i> Encoding
        <span class="encoding-type-badge">{{ encoding.type }}</span>
      </summary>
      <div class="encoding-details">
        <!-- TextEncoding -->
        <template v-if="encoding.type === 'TextEncoding'">
          <div class="encoding-field"><span class="encoding-key">Token Separator:</span> <code>{{ JSON.stringify(encoding.tokenSeparator) }}</code></div>
          <div class="encoding-field"><span class="encoding-key">Block Separator:</span> <code>{{ JSON.stringify(encoding.blockSeparator) }}</code></div>
          <div v-if="encoding.decimalSeparator" class="encoding-field"><span class="encoding-key">Decimal Separator:</span> <code>{{ encoding.decimalSeparator }}</code></div>
          <div v-if="encoding.collapseWhiteSpaces !== undefined" class="encoding-field"><span class="encoding-key">Collapse Whitespace:</span> {{ encoding.collapseWhiteSpaces ? 'Yes' : 'No' }}</div>
        </template>
        <!-- JSONEncoding -->
        <template v-else-if="encoding.type === 'JSONEncoding'">
          <div v-if="encoding.recordsAsArrays !== undefined" class="encoding-field"><span class="encoding-key">Records as Arrays:</span> {{ encoding.recordsAsArrays ? 'Yes' : 'No' }}</div>
          <div v-if="encoding.vectorsAsArrays !== undefined" class="encoding-field"><span class="encoding-key">Vectors as Arrays:</span> {{ encoding.vectorsAsArrays ? 'Yes' : 'No' }}</div>
          <div v-if="encoding.recordsAsArrays === undefined && encoding.vectorsAsArrays === undefined" class="encoding-field"><em>Default JSON encoding (no custom options)</em></div>
        </template>
        <!-- BinaryEncoding -->
        <template v-else-if="encoding.type === 'BinaryEncoding'">
          <div class="encoding-field"><span class="encoding-key">Byte Order:</span> {{ encoding.byteOrder }}</div>
          <div class="encoding-field"><span class="encoding-key">Byte Encoding:</span> {{ encoding.byteEncoding }}</div>
          <div v-if="encoding.byteLength" class="encoding-field"><span class="encoding-key">Byte Length:</span> {{ encoding.byteLength }}</div>
          <div v-if="encoding.members?.length" class="encoding-members">
            <div class="encoding-key" style="margin-bottom: 0.25rem;">Members ({{ encoding.members.length }}):</div>
            <table class="encoding-members-table">
              <thead>
                <tr>
                  <th>Type</th>
                  <th>Ref</th>
                  <th>Data Type</th>
                  <th>Byte Length</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(member, mi) in encoding.members" :key="mi">
                  <td><span class="member-type-chip">{{ member.type }}</span></td>
                  <td><code>{{ member.ref }}</code></td>
                  <td>
                    <code v-if="member.dataType">{{ shortenUri(member.dataType) }}</code>
                    <span v-else-if="member.compression">{{ member.compression }}</span>
                    <span v-else>—</span>
                  </td>
                  <td>{{ member.byteLength ?? '—' }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </template>
        <!-- XMLEncoding -->
        <template v-else-if="encoding.type === 'XMLEncoding'">
          <div v-if="encoding.namespace" class="encoding-field"><span class="encoding-key">Namespace:</span> <code>{{ encoding.namespace }}</code></div>
          <div v-else class="encoding-field"><em>Default XML encoding</em></div>
        </template>
      </div>
    </details>

    <!-- Raw schema JSON (always shown if available) -->
    <details v-if="rawSchema" class="schema-raw-section">
      <summary>Raw Schema JSON</summary>
      <pre class="schema-raw-json">{{ JSON.stringify(rawSchema, null, 2) }}</pre>
    </details>
  </details>
</template>

<style scoped>
.schema-section {
  margin-top: 0.5rem;
}
.schema-section > summary {
  cursor: pointer;
  font-weight: 600;
  font-size: 0.9rem;
  color: #475569;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.schema-type-badge {
  background: #dbeafe;
  color: #1e40af;
  padding: 0.1rem 0.5rem;
  border-radius: 10px;
  font-size: 0.75rem;
  font-weight: 500;
}
.schema-format-badge {
  background: #fef3c7;
  color: #92400e;
  padding: 0.1rem 0.5rem;
  border-radius: 10px;
  font-size: 0.7rem;
  font-weight: 400;
  font-family: monospace;
}
.schema-loading {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #64748b;
  padding: 0.5rem 0;
}
.schema-error {
  margin-top: 0.5rem;
}
.schema-parse-warn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #b45309;
  font-size: 0.8rem;
  padding: 0.3rem 0;
}
.schema-parsed {
  margin-top: 0.5rem;
}
.schema-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.8rem;
  margin-top: 0.25rem;
}
.schema-table th,
.schema-table td {
  padding: 0.4rem 0.5rem;
  text-align: left;
  border-bottom: 1px solid #e2e8f0;
}
.schema-table th {
  background: #f8fafc;
  font-weight: 600;
  color: #475569;
}
.schema-table code {
  background: #f1f5f9;
  padding: 0.1rem 0.3rem;
  border-radius: 3px;
  font-size: 0.78rem;
}
.nested-row {
  background: #fafbfd;
}
.type-chip {
  display: inline-block;
  background: #f0fdf4;
  color: #166534;
  padding: 0.1rem 0.4rem;
  border-radius: 8px;
  font-size: 0.75rem;
  font-weight: 500;
}
.definition-cell {
  font-size: 0.75rem;
  max-width: 220px;
  word-break: break-all;
}
.definition-cell a {
  color: #2563eb;
  text-decoration: none;
}
.definition-cell a:hover {
  text-decoration: underline;
}
.schema-raw-section {
  margin-top: 0.5rem;
}
.schema-raw-section summary {
  cursor: pointer;
  font-weight: 600;
  font-size: 0.85rem;
  color: #64748b;
}
.schema-raw-json {
  background: #f8fafc;
  padding: 0.75rem;
  border-radius: 6px;
  overflow-x: auto;
  font-size: 0.72rem;
  max-height: 350px;
  overflow-y: auto;
  margin-top: 0.25rem;
}
.schema-section-label {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-weight: 600;
  font-size: 0.82rem;
  color: #475569;
  margin: 0.75rem 0 0.25rem 0;
}
.encoding-type-badge {
  background: #e0e7ff;
  color: #3730a3;
  padding: 0.1rem 0.5rem;
  border-radius: 10px;
  font-size: 0.72rem;
  font-weight: 500;
  font-family: monospace;
}
.schema-encoding-section {
  margin-top: 0.75rem;
}
.schema-encoding-section > summary {
  cursor: pointer;
}
.encoding-details {
  padding: 0.5rem 0 0.5rem 1.25rem;
}
.encoding-field {
  font-size: 0.82rem;
  color: #334155;
  padding: 0.15rem 0;
}
.encoding-key {
  font-weight: 600;
  color: #475569;
}
.encoding-details code {
  background: #f1f5f9;
  padding: 0.1rem 0.3rem;
  border-radius: 3px;
  font-size: 0.78rem;
}
.encoding-members {
  margin-top: 0.35rem;
}
.encoding-members-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.78rem;
  margin-top: 0.15rem;
}
.encoding-members-table th,
.encoding-members-table td {
  padding: 0.3rem 0.5rem;
  text-align: left;
  border-bottom: 1px solid #e2e8f0;
}
.encoding-members-table th {
  background: #f8fafc;
  font-weight: 600;
  color: #475569;
  font-size: 0.72rem;
}
.encoding-members-table code {
  background: #f1f5f9;
  padding: 0.1rem 0.3rem;
  border-radius: 3px;
  font-size: 0.75rem;
}
.member-type-chip {
  display: inline-block;
  background: #ede9fe;
  color: #5b21b6;
  padding: 0.1rem 0.35rem;
  border-radius: 8px;
  font-size: 0.7rem;
  font-weight: 500;
}
</style>
