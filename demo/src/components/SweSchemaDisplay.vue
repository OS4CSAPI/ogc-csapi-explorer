<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { apiFetch } from '../api'
import { getSchemaUrl, parseSWEComponent } from '../csapi-bridge'
import type { AnyComponent } from '../csapi-bridge'
import ProgressSpinner from 'primevue/progressspinner'
import Message from 'primevue/message'

const props = defineProps<{
  datastreamId: string
}>()

const loading = ref(false)
const error = ref('')
const rawSchema = ref<any>(null)
const parsed = ref<AnyComponent | null>(null)

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

const schemaFields = computed<SchemaField[]>(() => {
  if (!parsed.value) return []
  return flattenComponent(parsed.value, '', 0)
})

const parsedTypeLabel = computed(() => parsed.value?.type ?? null)

const obsFormat = computed(() => rawSchema.value?.obsFormat ?? null)

async function fetchSchema() {
  const url = getSchemaUrl(props.datastreamId)
  if (!url) {
    error.value = 'Schema URL not available (builder not initialized or datastreams unavailable)'
    return
  }

  loading.value = true
  error.value = ''
  rawSchema.value = null
  parsed.value = null

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

  // The schema response is typically { obsFormat, resultSchema }.
  // Extract the resultSchema for parsing; fall back to the entire response.
  const sweJson = data?.resultSchema ?? data

  // Attempt to parse with the library's SWE Common parser
  try {
    parsed.value = parseSWEComponent(sweJson)
  } catch (e: any) {
    error.value = `Schema fetched but parsing failed: ${e.message || e}`
    // Still show raw JSON even when parsing fails
  }

  loading.value = false
}

watch(() => props.datastreamId, () => {
  if (props.datastreamId) fetchSchema()
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
      <i class="pi pi-sitemap"></i>
      Observation Schema
      <span v-if="parsedTypeLabel" class="schema-type-badge">{{ parsedTypeLabel }}</span>
      <span v-if="obsFormat" class="schema-format-badge">{{ obsFormat }}</span>
    </summary>

    <div v-if="loading" class="schema-loading">
      <ProgressSpinner style="width: 24px; height: 24px" />
      <span>Loading schema...</span>
    </div>

    <Message v-if="error && !rawSchema" severity="warn" :closable="false" class="schema-error">
      {{ error }}
    </Message>

    <!-- Parsed structured view -->
    <div v-if="schemaFields.length" class="schema-parsed">
      <div v-if="error" class="schema-parse-warn">
        <i class="pi pi-exclamation-triangle"></i>
        <span>{{ error }}</span>
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
          <tr v-for="(field, i) in schemaFields" :key="i" :class="{ 'nested-row': field.depth > 0 }">
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
</style>
