<script setup lang="ts">
/**
 * Renders an observation result as a structured table using the parent
 * datastream's schema. Falls back to expandable raw JSON when the schema
 * is unavailable or parsing fails.
 *
 * Features:
 * - Fetches the parent datastream schema (by datastream ID)
 * - Flattens the schema into displayable field definitions (name, type, UoM)
 * - Maps observation result values to schema fields in a table
 * - Runs validateAgainstSchema() and shows a pass/fail badge
 * - Keeps raw JSON available as expandable fallback
 *
 * @see https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/31
 */
import { ref, watch, computed } from 'vue'
import { apiFetch } from '../api'
import {
  getSchemaUrl,
  parseDatastreamSchemaResponse,
  parseSWEComponent,
  validateAgainstSchema,
} from '../csapi-bridge'
import type { AnyComponent } from '../csapi-bridge'

const props = defineProps<{
  /** The observation result value (unknown — could be object, scalar, array) */
  result: unknown
  /** The parent datastream ID — used to fetch the schema */
  datastreamId?: string | null
}>()

// ========================================
// Schema Fetching & Parsing
// ========================================

const loading = ref(false)
const schemaError = ref('')
const schema = ref<AnyComponent | null>(null)

/** Flattened schema fields for table rendering */
interface ResultField {
  /** Dotted path name (e.g., 'temperature', 'location.lat') */
  name: string
  /** SWE component type (Quantity, Text, Boolean, etc.) */
  type: string
  /** Human-readable label */
  label?: string
  /** Unit of measure */
  uom?: string
  /** Nesting depth for indentation */
  depth: number
}

/**
 * Recursively flatten an AnyComponent into displayable field definitions.
 * Mirrors the pattern used by SweSchemaDisplay.vue's flattenComponent().
 */
function flattenSchema(component: AnyComponent, prefix: string, depth: number): ResultField[] {
  const fields: ResultField[] = []

  if (component.type === 'DataRecord') {
    for (const f of (component as any).fields ?? []) {
      const name = prefix ? `${prefix}.${f.name}` : f.name
      const fieldType: string = f.type || f.component?.type || 'unknown'
      fields.push({
        name,
        type: fieldType,
        label: f.label || f.component?.label,
        uom: f.uom?.code || f.uom?.href || f.component?.uom?.code || f.component?.uom?.href,
        depth,
      })
      // Recurse into nested complex types
      if (fieldType === 'DataRecord' || fieldType === 'Vector' || fieldType === 'DataArray') {
        try {
          const nested = f.component || parseSWEComponent(f)
          fields.push(...flattenSchema(nested, name, depth + 1))
        } catch { /* skip non-parseable nested */ }
      }
    }
  } else if (component.type === 'Vector') {
    for (const c of (component as any).coordinates ?? []) {
      const name = prefix ? `${prefix}.${c.name}` : c.name
      fields.push({
        name,
        type: c.type || 'Quantity',
        label: c.label,
        uom: c.uom?.code || c.uom?.href,
        depth,
      })
    }
  } else if (component.type === 'DataArray') {
    const et = (component as any).elementType
    if (et) {
      const name = prefix ? `${prefix}[*]` : '[*]'
      fields.push({
        name,
        type: et.type || 'element',
        label: et.label,
        uom: et.uom?.code || et.uom?.href,
        depth,
      })
    }
  } else {
    // Simple scalar at top level
    fields.push({
      name: prefix || '(value)',
      type: component.type,
      label: (component as any).label,
      uom: (component as any).uom?.code || (component as any).uom?.href,
      depth,
    })
  }

  return fields
}

const schemaFields = computed<ResultField[]>(() => {
  if (!schema.value) return []
  return flattenSchema(schema.value, '', 0)
})

// ========================================
// Value Extraction
// ========================================

/**
 * Extract a value from the observation result by dotted field path.
 * Handles nested objects (e.g., 'location.lat' → result.location.lat).
 */
function getValueByPath(result: unknown, path: string): unknown {
  if (result == null) return undefined
  const parts = path.split('.')
  let current: any = result
  for (const part of parts) {
    if (current == null || typeof current !== 'object') return undefined
    current = current[part]
  }
  return current
}

/** Format a value for display */
function formatValue(value: unknown): string {
  if (value === undefined) return '—'
  if (value === null) return 'null'
  if (typeof value === 'object') return JSON.stringify(value)
  return String(value)
}

/** Check if result appears to be a structured object (not a scalar) */
const isStructuredResult = computed(() => {
  return typeof props.result === 'object' && props.result !== null && !Array.isArray(props.result)
})

// ========================================
// Validation
// ========================================

interface ValidationState {
  valid: boolean
  errors: Array<{ path: string; message: string; code: string }>
  ran: boolean
}

const validation = ref<ValidationState>({ valid: true, errors: [], ran: false })

function runValidation() {
  if (!schema.value || props.result === undefined) return
  try {
    const result = validateAgainstSchema(props.result, schema.value)
    validation.value = { valid: result.valid, errors: result.errors, ran: true }
  } catch {
    validation.value = { valid: false, errors: [{ path: '', message: 'Validation threw an error', code: 'INTERNAL' }], ran: true }
  }
}

// ========================================
// Schema Fetching
// ========================================

async function fetchSchema() {
  if (!props.datastreamId) {
    schemaError.value = 'No datastream ID available'
    return
  }

  const url = getSchemaUrl(props.datastreamId)
  if (!url) {
    schemaError.value = 'Could not construct schema URL'
    return
  }

  loading.value = true
  schemaError.value = ''
  schema.value = null
  validation.value = { valid: true, errors: [], ran: false }

  try {
    const res = await apiFetch(url, {
      headers: { 'Accept': 'application/swe+json, application/json' },
    })

    if (!res.ok) {
      schemaError.value = `Schema fetch failed: ${res.error || res.statusText}`
      loading.value = false
      return
    }

    let data = res.data
    if (typeof data === 'string') {
      try { data = JSON.parse(data) } catch { /* leave as string */ }
    }

    // Parse schema envelope → extract resultSchema
    try {
      const envelope = parseDatastreamSchemaResponse(data)
      schema.value = envelope.resultSchema ?? envelope.recordSchema ?? null
    } catch {
      // Fallback: try parsing as a bare SWE component
      try {
        schema.value = parseSWEComponent(data)
      } catch (innerErr: any) {
        schemaError.value = `Schema parse failed: ${innerErr.message || innerErr}`
      }
    }

    // Auto-validate once schema is available
    if (schema.value && props.result !== undefined) {
      runValidation()
    }
  } catch (err: any) {
    schemaError.value = `Fetch error: ${err.message || err}`
  } finally {
    loading.value = false
  }
}

// Fetch schema when datastream ID changes
watch(
  () => props.datastreamId,
  (id) => { if (id) fetchSchema() },
  { immediate: true }
)

// ========================================
// Raw JSON fallback
// ========================================

const rawJson = computed(() => {
  if (props.result === undefined) return 'undefined'
  return JSON.stringify(props.result, null, 2)
})

const rawJsonTruncated = computed(() => {
  const full = typeof props.result === 'object' ? JSON.stringify(props.result) : String(props.result ?? '')
  return full.length > 200 ? full.slice(0, 200) + '…' : full
})
</script>

<template>
  <div class="obs-result-table">
    <!-- Schema-aware structured table -->
    <div v-if="schemaFields.length > 0 && isStructuredResult" class="result-structured">
      <div class="result-header">
        <span class="result-title">
          <i class="pi pi-table"></i> Observation Result
        </span>
        <!-- Validation badge -->
        <span v-if="validation.ran" :class="['validation-badge', validation.valid ? 'valid' : 'invalid']">
          <i :class="validation.valid ? 'pi pi-check-circle' : 'pi pi-exclamation-triangle'"></i>
          {{ validation.valid ? 'Valid' : `${validation.errors.length} error(s)` }}
        </span>
        <span v-if="loading" class="schema-loading-hint">Loading schema…</span>
      </div>

      <table class="result-table">
        <thead>
          <tr>
            <th>Field</th>
            <th>Value</th>
            <th>Type</th>
            <th>UoM</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(field, i) in schemaFields" :key="i" :class="{ 'nested-row': field.depth > 0 }">
            <td class="field-name">
              <span :style="{ paddingLeft: field.depth * 16 + 'px' }">
                <code>{{ field.name }}</code>
                <span v-if="field.label" class="field-label-hint">{{ field.label }}</span>
              </span>
            </td>
            <td class="field-value">
              <code>{{ formatValue(getValueByPath(result, field.name)) }}</code>
            </td>
            <td><span class="type-chip">{{ field.type }}</span></td>
            <td>
              <code v-if="field.uom" class="uom-code">{{ field.uom }}</code>
              <span v-else class="dim">—</span>
            </td>
          </tr>
        </tbody>
      </table>

      <!-- Validation errors detail -->
      <details v-if="validation.ran && !validation.valid" class="validation-errors">
        <summary>
          <i class="pi pi-exclamation-triangle"></i>
          Validation errors ({{ validation.errors.length }})
        </summary>
        <ul>
          <li v-for="(err, i) in validation.errors" :key="i">
            <code>{{ err.path || '(root)' }}</code>: {{ err.message }}
            <span class="error-code">[{{ err.code }}]</span>
          </li>
        </ul>
      </details>
    </div>

    <!-- No schema available — show inline truncated value -->
    <div v-else-if="!loading && !schemaFields.length" class="result-fallback">
      <code class="result-raw-inline">{{ rawJsonTruncated }}</code>
      <span v-if="schemaError" class="schema-hint">
        <i class="pi pi-info-circle"></i> {{ schemaError }}
      </span>
    </div>

    <!-- Loading state -->
    <div v-else-if="loading" class="result-fallback">
      <code class="result-raw-inline">{{ rawJsonTruncated }}</code>
      <span class="schema-loading-hint">Loading schema…</span>
    </div>

    <!-- Raw JSON expandable fallback (always available when structured) -->
    <details v-if="schemaFields.length > 0 && isStructuredResult" class="raw-fallback">
      <summary>Raw JSON</summary>
      <pre class="raw-json-block">{{ rawJson }}</pre>
    </details>
  </div>
</template>

<style scoped>
.obs-result-table { display: flex; flex-direction: column; gap: 0.5rem; }

.result-header { display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.25rem; flex-wrap: wrap; }
.result-title { font-size: 0.8rem; font-weight: 700; color: #334155; display: flex; align-items: center; gap: 0.3rem; }

.validation-badge { font-size: 0.72rem; padding: 0.15rem 0.5rem; border-radius: 4px; font-weight: 700; display: inline-flex; align-items: center; gap: 0.25rem; }
.validation-badge.valid { background: #dcfce7; color: #166534; }
.validation-badge.invalid { background: #fee2e2; color: #991b1b; }

.schema-loading-hint { font-size: 0.72rem; color: #94a3b8; font-style: italic; }

.result-table { width: 100%; border-collapse: collapse; font-size: 0.8rem; }
.result-table th { padding: 0.3rem 0.5rem; text-align: left; background: #f8fafc; font-size: 0.72rem; font-weight: 700; color: #64748b; border-bottom: 2px solid #e2e8f0; white-space: nowrap; }
.result-table td { padding: 0.3rem 0.5rem; border-bottom: 1px solid #f1f5f9; vertical-align: top; }

.field-name { white-space: nowrap; }
.field-name code { font-size: 0.76rem; font-weight: 600; color: #475569; }
.field-label-hint { font-size: 0.68rem; color: #94a3b8; margin-left: 0.3rem; font-style: italic; }
.field-value code { font-size: 0.76rem; background: #f1f5f9; padding: 0.1rem 0.3rem; border-radius: 3px; word-break: break-all; }
.type-chip { font-size: 0.7rem; background: #ede9fe; color: #7c3aed; padding: 0.1rem 0.35rem; border-radius: 3px; font-weight: 600; white-space: nowrap; }
.uom-code { font-size: 0.72rem; background: #dbeafe; color: #1e40af; padding: 0.05rem 0.25rem; border-radius: 3px; }
.dim { color: #cbd5e1; font-size: 0.75rem; }

.nested-row { background: #fafbfd; }
.nested-row .field-name code { color: #64748b; }

.validation-errors { margin-top: 0.25rem; font-size: 0.78rem; }
.validation-errors summary { cursor: pointer; font-weight: 600; color: #991b1b; display: flex; align-items: center; gap: 0.3rem; font-size: 0.78rem; }
.validation-errors ul { margin: 0.25rem 0; padding-left: 1.25rem; }
.validation-errors li { margin-bottom: 0.15rem; color: #7f1d1d; }
.validation-errors code { font-size: 0.72rem; background: #fee2e2; padding: 0.05rem 0.25rem; border-radius: 2px; }
.error-code { font-size: 0.65rem; color: #a8a29e; margin-left: 0.3rem; }

.result-fallback { display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap; }
.result-raw-inline { font-size: 0.78rem; background: #f1f5f9; padding: 0.1rem 0.3rem; border-radius: 3px; word-break: break-all; max-width: 100%; }
.schema-hint { font-size: 0.68rem; color: #94a3b8; display: flex; align-items: center; gap: 0.2rem; }

.raw-fallback { margin-top: 0.15rem; }
.raw-fallback summary { cursor: pointer; font-size: 0.72rem; color: #94a3b8; font-weight: 600; }
.raw-json-block { font-size: 0.72rem; background: #f8fafc; padding: 0.5rem; border-radius: 4px; max-height: 200px; overflow: auto; margin: 0.25rem 0 0; }
</style>
