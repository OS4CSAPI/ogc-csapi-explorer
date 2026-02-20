<script setup lang="ts">
/**
 * Fetches and renders the status history for a Command resource.
 *
 * Calls `/commands/{id}/status` to retrieve status entries, parses each
 * with `tryParseCommandStatus()`, and renders a timeline-style table
 * showing the progression: PENDING → ACCEPTED → EXECUTING → COMPLETED/FAILED.
 *
 * Features:
 * - Timeline indicator with colour-coded status badges
 * - Report time, percent completion progress bar, execution time interval
 * - Status messages displayed inline
 * - Graceful handling of empty history, fetch errors, loading states
 *
 * @see https://github.com/OS4CSAPI/ogc-csapi-explorer/issues/32
 */
import { ref, watch, computed } from 'vue'
import { apiFetch } from '../api'
import { getCommandStatusUrl, tryParseCommandStatus } from '../csapi-bridge'

const props = defineProps<{
  /** The command ID whose status history to fetch */
  commandId?: string | null
}>()

// ========================================
// State
// ========================================

interface ParsedStatus {
  id: string
  reportTime: string
  statusCode: string
  percentCompletion?: number
  executionTime?: { start: Date; end?: Date }
  message?: string
}

const loading = ref(false)
const error = ref('')
const statuses = ref<ParsedStatus[]>([])
const expanded = ref(true)

// ========================================
// Status Code Styling
// ========================================

/** Ordered lifecycle phases for the timeline */
const STATUS_ORDER: Record<string, number> = {
  PENDING: 0,
  ACCEPTED: 1,
  REJECTED: 1,
  SCHEDULED: 2,
  UPDATED: 3,
  CANCELED: 3,
  EXECUTING: 4,
  FAILED: 5,
  COMPLETED: 5,
}

function statusClass(code: string): string {
  switch (code) {
    case 'COMPLETED': return 'status-completed'
    case 'EXECUTING': return 'status-executing'
    case 'ACCEPTED':
    case 'SCHEDULED': return 'status-accepted'
    case 'FAILED':
    case 'REJECTED':
    case 'CANCELED': return 'status-failed'
    case 'PENDING': return 'status-pending'
    default: return 'status-pending'
  }
}

/** Sort statuses chronologically by reportTime, then by lifecycle phase */
const sortedStatuses = computed(() => {
  return [...statuses.value].sort((a, b) => {
    const timeA = new Date(a.reportTime).getTime()
    const timeB = new Date(b.reportTime).getTime()
    if (timeA !== timeB) return timeA - timeB
    return (STATUS_ORDER[a.statusCode] ?? 99) - (STATUS_ORDER[b.statusCode] ?? 99)
  })
})

function formatDate(d: Date | undefined): string {
  if (!d) return '(ongoing / now)'
  return d instanceof Date && !isNaN(d.getTime())
    ? d.toISOString().replace('T', ' ').replace('Z', ' UTC')
    : String(d)
}

function formatDuration(start: Date, end?: Date): string {
  if (!end) return ''
  const ms = end.getTime() - start.getTime()
  if (ms < 1000) return `${ms}ms`
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`
  return `${(ms / 60000).toFixed(1)}min`
}

// ========================================
// Fetch Logic
// ========================================

async function fetchStatusHistory() {
  const id = props.commandId
  if (!id) return

  loading.value = true
  error.value = ''
  statuses.value = []

  try {
    const url = getCommandStatusUrl(id)
    if (!url) {
      error.value = 'Could not build status URL'
      loading.value = false
      return
    }

    const res = await apiFetch(url, {
      headers: { 'Accept': 'application/json' },
    })

    if (!res.ok) {
      error.value = `Status fetch failed: ${res.error || res.statusText}`
      loading.value = false
      return
    }

    let data = res.data
    if (typeof data === 'string') {
      try { data = JSON.parse(data) } catch { /* leave as string */ }
    }

    // Response is either an array of statuses or an object with .items array
    let items: unknown[] = []
    if (Array.isArray(data)) {
      items = data
    } else if (data && typeof data === 'object') {
      const obj = data as Record<string, unknown>
      if (Array.isArray(obj.items)) {
        items = obj.items
      } else {
        // Single status object — wrap in array
        items = [data]
      }
    }

    const parsed: ParsedStatus[] = []
    for (const item of items) {
      const s = tryParseCommandStatus(item)
      if (s) {
        parsed.push(s as ParsedStatus)
      }
    }

    statuses.value = parsed
  } catch (err: any) {
    error.value = `Fetch error: ${err.message || err}`
  } finally {
    loading.value = false
  }
}

// Fetch when commandId changes
watch(
  () => props.commandId,
  (id) => { if (id) fetchStatusHistory() },
  { immediate: true }
)
</script>

<template>
  <div class="cmd-status-history">
    <div class="history-header" @click="expanded = !expanded">
      <span class="history-title">
        <i class="pi pi-history"></i>
        Status History
        <span v-if="sortedStatuses.length" class="count-badge">{{ sortedStatuses.length }}</span>
      </span>
      <span v-if="loading" class="loading-hint">Loading…</span>
      <i :class="expanded ? 'pi pi-chevron-up' : 'pi pi-chevron-down'" class="toggle-icon"></i>
    </div>

    <div v-if="expanded" class="history-body">
      <!-- Error state -->
      <div v-if="error" class="status-error">
        <i class="pi pi-exclamation-circle"></i> {{ error }}
      </div>

      <!-- Loading state -->
      <div v-else-if="loading" class="status-loading">
        <i class="pi pi-spin pi-spinner"></i> Fetching status history…
      </div>

      <!-- Empty state -->
      <div v-else-if="sortedStatuses.length === 0" class="status-empty">
        <i class="pi pi-info-circle"></i> No status entries found
      </div>

      <!-- Timeline table -->
      <div v-else class="timeline">
        <div
          v-for="(status, i) in sortedStatuses"
          :key="status.id || i"
          class="timeline-entry"
        >
          <!-- Timeline connector -->
          <div class="timeline-rail">
            <div :class="['timeline-dot', statusClass(status.statusCode)]"></div>
            <div v-if="i < sortedStatuses.length - 1" class="timeline-line"></div>
          </div>

          <!-- Content -->
          <div class="timeline-content">
            <div class="status-row-header">
              <span :class="['status-code-badge', statusClass(status.statusCode)]">
                {{ status.statusCode }}
              </span>
              <code class="report-time">{{ status.reportTime }}</code>
              <span
                v-if="status.percentCompletion !== undefined"
                class="percent-badge"
              >
                {{ status.percentCompletion }}%
              </span>
            </div>

            <!-- Progress bar -->
            <div
              v-if="status.percentCompletion !== undefined && status.percentCompletion < 100"
              class="progress-wrapper"
            >
              <div class="progress-bar">
                <div
                  class="progress-fill"
                  :style="{ width: status.percentCompletion + '%' }"
                ></div>
              </div>
            </div>

            <!-- Execution time -->
            <div v-if="status.executionTime" class="exec-time">
              <span class="exec-label">Execution:</span>
              <code>{{ formatDate(status.executionTime.start) }}</code>
              <span v-if="status.executionTime.end">
                → <code>{{ formatDate(status.executionTime.end) }}</code>
                <span class="duration-hint">{{ formatDuration(status.executionTime.start, status.executionTime.end) }}</span>
              </span>
            </div>

            <!-- Message -->
            <div v-if="status.message" class="status-message">
              <i class="pi pi-comment"></i> {{ status.message }}
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.cmd-status-history {
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  overflow: hidden;
  margin-top: 0.25rem;
}

.history-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.4rem 0.6rem;
  background: #f8fafc;
  cursor: pointer;
  user-select: none;
  border-bottom: 1px solid #e2e8f0;
}
.history-header:hover { background: #f1f5f9; }
.history-title {
  font-size: 0.8rem;
  font-weight: 700;
  color: #334155;
  display: flex;
  align-items: center;
  gap: 0.35rem;
  flex: 1;
}
.count-badge {
  font-size: 0.68rem;
  background: #dbeafe;
  color: #1e40af;
  padding: 0.05rem 0.35rem;
  border-radius: 8px;
  font-weight: 700;
}
.loading-hint { font-size: 0.72rem; color: #94a3b8; font-style: italic; }
.toggle-icon { font-size: 0.72rem; color: #94a3b8; }

.history-body { padding: 0.5rem 0.6rem; }

.status-error {
  font-size: 0.78rem;
  color: #dc2626;
  display: flex;
  align-items: center;
  gap: 0.3rem;
}
.status-loading {
  font-size: 0.78rem;
  color: #64748b;
  display: flex;
  align-items: center;
  gap: 0.3rem;
}
.status-empty {
  font-size: 0.78rem;
  color: #94a3b8;
  display: flex;
  align-items: center;
  gap: 0.3rem;
  font-style: italic;
}

/* ── Timeline ────────────────────────── */
.timeline { display: flex; flex-direction: column; }
.timeline-entry { display: flex; gap: 0.6rem; min-height: 2.5rem; }

.timeline-rail {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 16px;
  flex-shrink: 0;
}
.timeline-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  border: 2px solid #cbd5e1;
  background: #fff;
  flex-shrink: 0;
  margin-top: 4px;
}
.timeline-line {
  width: 2px;
  flex: 1;
  background: #e2e8f0;
  margin: 2px 0;
}

/* Status dot colours */
.timeline-dot.status-completed { border-color: #16a34a; background: #dcfce7; }
.timeline-dot.status-executing { border-color: #2563eb; background: #dbeafe; }
.timeline-dot.status-accepted { border-color: #ca8a04; background: #fef9c3; }
.timeline-dot.status-failed { border-color: #dc2626; background: #fee2e2; }
.timeline-dot.status-pending { border-color: #94a3b8; background: #f1f5f9; }

.timeline-content {
  flex: 1;
  padding-bottom: 0.6rem;
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.status-row-header {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  flex-wrap: wrap;
}

.status-code-badge {
  font-size: 0.72rem;
  font-weight: 700;
  padding: 0.1rem 0.4rem;
  border-radius: 4px;
  white-space: nowrap;
}
.status-code-badge.status-completed { background: #dcfce7; color: #166534; }
.status-code-badge.status-executing { background: #dbeafe; color: #1e40af; }
.status-code-badge.status-accepted { background: #fef9c3; color: #854d0e; }
.status-code-badge.status-failed { background: #fee2e2; color: #991b1b; }
.status-code-badge.status-pending { background: #f1f5f9; color: #64748b; }

.report-time { font-size: 0.72rem; color: #64748b; }
.percent-badge {
  font-size: 0.68rem;
  background: #ede9fe;
  color: #7c3aed;
  padding: 0.05rem 0.3rem;
  border-radius: 3px;
  font-weight: 700;
}

/* ── Progress bar ──────────────────── */
.progress-wrapper { max-width: 200px; }
.progress-bar {
  height: 4px;
  background: #e2e8f0;
  border-radius: 2px;
  overflow: hidden;
}
.progress-fill {
  height: 100%;
  background: #7c3aed;
  border-radius: 2px;
  transition: width 0.3s ease;
}

/* ── Execution time ────────────────── */
.exec-time {
  font-size: 0.72rem;
  color: #475569;
  display: flex;
  align-items: center;
  gap: 0.3rem;
  flex-wrap: wrap;
}
.exec-label { font-weight: 600; color: #64748b; }
.exec-time code { font-size: 0.7rem; background: #f1f5f9; padding: 0.05rem 0.2rem; border-radius: 2px; }
.duration-hint { font-size: 0.65rem; color: #94a3b8; margin-left: 0.2rem; }

/* ── Message ───────────────────────── */
.status-message {
  font-size: 0.74rem;
  color: #475569;
  display: flex;
  align-items: flex-start;
  gap: 0.25rem;
  padding: 0.2rem 0.35rem;
  background: #f8fafc;
  border-radius: 3px;
  border-left: 2px solid #cbd5e1;
}
</style>
