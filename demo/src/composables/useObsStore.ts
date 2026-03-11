/**
 * Observation Store Monitor — counts and purges publisher observations
 *
 * Groups publisher datastreams by feed (ISS, NWS, NDBC, CO-OPS) and provides:
 * - Per-datastream observation count via CSAPI `numberMatched` (limit=0)
 * - Bulk purge: DELETE all observations in selected publisher datastreams
 *
 * Does NOT touch simulator data (LOB, UAS, SENREP) — those are managed
 * by the simulator service's /clear and /reset endpoints.
 */
import { ref, computed } from 'vue'
import { connection } from '../state'

// ── CSAPI server (fallback when connection.baseUrl is not set, e.g. admin page) ──
const CSAPI_BASE = 'https://os4csapi-osh.duckdns.org/sensorhub/api'
const CSAPI_AUTH = 'Basic b3M0Y3NhcGk6b2djMTM0bW0='

function getBaseUrl() {
  return connection.baseUrl || CSAPI_BASE
}

function getAuthHeaders(): Record<string, string> {
  if (connection.baseUrl && Object.keys(connection.authHeaders).length) {
    return connection.authHeaders
  }
  return { Authorization: CSAPI_AUTH }
}

// ── Publisher datastream registry ────────────────────────────────────

export interface DsEntry {
  id: string
  label: string
}

export interface PublisherGroup {
  name: string
  icon: string          // PrimeVue icon class
  datastreams: DsEntry[]
}

export const PUBLISHER_GROUPS: PublisherGroup[] = [
  {
    name: 'ISS',
    icon: 'pi pi-globe',
    datastreams: [
      { id: '04gg', label: 'ISS Position SGP4' },
      { id: '04h0', label: 'ISS Orbit Ground Track' },
    ],
  },
  {
    name: 'NWS',
    icon: 'pi pi-cloud',
    datastreams: [
      { id: '04qg', label: 'NWS KTUS' },
      { id: '04r0', label: 'NWS KDMA' },
      { id: '04rg', label: 'NWS KFHU' },
      { id: '04s0', label: 'NWS KLUF' },
      { id: '04sg', label: 'NWS KPHX' },
      { id: '04t0', label: 'NWS KDCA' },
      { id: '04tg', label: 'NWS KIAD' },
      { id: '04u0', label: 'NWS KNYG' },
      { id: '04ug', label: 'NWS KDAY' },
      { id: '04v0', label: 'NWS KFFO' },
    ],
  },
  {
    name: 'NDBC',
    icon: 'pi pi-compass',
    datastreams: [
      { id: '04vg', label: 'NDBC 44025 Met' },
      { id: '050g', label: 'NDBC 41009 Met' },
      { id: '051g', label: 'NDBC 42036 Met' },
      { id: '052g', label: 'NDBC 46025 Met' },
      { id: '053g', label: 'NDBC 46013 Met' },
      { id: '0500', label: 'NDBC 44025 CAM' },
      { id: '0510', label: 'NDBC 41009 CAM' },
      { id: '0520', label: 'NDBC 42036 CAM' },
      { id: '0530', label: 'NDBC 46025 CAM' },
      { id: '0540', label: 'NDBC 46013 CAM' },
    ],
  },
  {
    name: 'CO-OPS',
    icon: 'pi pi-wave-pulse',
    datastreams: [
      { id: '0570', label: 'CO-OPS 8518750 The Battery' },
      { id: '0550', label: 'CO-OPS 8723214 Virginia Key' },
      { id: '055g', label: 'CO-OPS 8726520 St. Petersburg' },
      { id: '0560', label: 'CO-OPS 9414290 San Francisco' },
      { id: '056g', label: 'CO-OPS 8443970 Boston' },
    ],
  },
  {
    name: 'AWX METAR',
    icon: 'pi pi-cloud',
    datastreams: [
      { id: '057g', label: 'AWX KTUS Tucson' },
      { id: '0580', label: 'AWX KDMA Davis-Monthan' },
      { id: '058g', label: 'AWX KFHU Ft Huachuca' },
      { id: '0590', label: 'AWX KLUF Luke AFB' },
      { id: '059g', label: 'AWX KPHX Sky Harbor' },
    ],
  },
]

// ── Types ────────────────────────────────────────────────────────────

export interface DsObsCount {
  dsId: string
  label: string
  group: string
  count: number | null  // null = not yet fetched
  error: string | null
}

// ── Composable ──────────────────────────────────────────────────────

export function useObsStore() {
  const counts = ref<DsObsCount[]>([])
  const fetching = ref(false)
  const purging = ref(false)
  const purgeLog = ref<string[]>([])
  const lastFetched = ref('')

  // Derived
  const totalObs = computed(() =>
    counts.value.reduce((sum, d) => sum + (d.count ?? 0), 0)
  )

  const groupTotals = computed(() => {
    const m: Record<string, number> = {}
    for (const d of counts.value) {
      m[d.group] = (m[d.group] ?? 0) + (d.count ?? 0)
    }
    return m
  })

  // ── API helpers ──

  async function apiFetch(path: string, method = 'GET'): Promise<{ ok: boolean; status: number; data: any }> {
    const url = getBaseUrl() + path
    try {
      const resp = await fetch(url, {
        method,
        headers: {
          ...getAuthHeaders(),
          'Accept': 'application/json',
        },
      })
      if (!resp.ok) return { ok: false, status: resp.status, data: null }
      // DELETE may return 204 with no body
      if (resp.status === 204 || resp.headers.get('content-length') === '0') {
        return { ok: true, status: resp.status, data: null }
      }
      const data = await resp.json()
      return { ok: true, status: resp.status, data }
    } catch (e: any) {
      return { ok: false, status: 0, data: e.message }
    }
  }

  // ── Fetch observation counts ──

  async function fetchCounts() {
    fetching.value = true
    counts.value = []

    // Build initial entries
    for (const group of PUBLISHER_GROUPS) {
      for (const ds of group.datastreams) {
        counts.value.push({
          dsId: ds.id,
          label: ds.label,
          group: group.name,
          count: null,
          error: null,
        })
      }
    }

    // Fetch in parallel (batched to avoid overwhelming server)
    // OSH SensorHub does not support numberMatched, so we fetch with a large
    // limit and count items.  If a "next" link is present, more obs exist.
    const COUNT_LIMIT = 10000
    const batchSize = 4
    for (let i = 0; i < counts.value.length; i += batchSize) {
      const batch = counts.value.slice(i, i + batchSize)
      await Promise.all(
        batch.map(async (entry) => {
          const { ok, data } = await apiFetch(
            `/datastreams/${entry.dsId}/observations?limit=${COUNT_LIMIT}`
          )
          if (ok && data) {
            const items = data.items ?? []
            const links = data.links ?? []
            const hasNext = links.some((l: any) => l.rel === 'next')
            // If numberMatched is present, prefer it; otherwise count items
            if (typeof data.numberMatched === 'number' && data.numberMatched > 0) {
              entry.count = data.numberMatched
            } else {
              entry.count = items.length
            }
            // Flag overflow: more obs exist beyond our limit
            if (hasNext && entry.count === COUNT_LIMIT) {
              entry.error = `${COUNT_LIMIT.toLocaleString()}+`
            } else {
              entry.error = null
            }
          } else {
            entry.count = null
            entry.error = typeof data === 'string' ? data : `HTTP error`
          }
        })
      )
    }

    lastFetched.value = new Date().toLocaleTimeString()
    fetching.value = false
  }

  // ── Purge observations ──

  /** Core purge logic — deletes all obs from the given datastreams */
  async function purgeDatastreams(targets: DsEntry[], label: string) {
    purging.value = true
    purgeLog.value = []
    let totalDeleted = 0

    purgeLog.value.push(`── Purging: ${label} (${targets.length} datastream${targets.length > 1 ? 's' : ''}) ──`)
    purgeLog.value.push('')

    for (const ds of targets) {
      purgeLog.value.push(`Purging ${ds.label} (${ds.id})…`)

      // Attempt collection delete: DELETE /datastreams/{id}/observations
      const { ok, status } = await apiFetch(
        `/datastreams/${ds.id}/observations`,
        'DELETE'
      )

      if (ok || status === 204) {
        const entry = counts.value.find(c => c.dsId === ds.id)
        const n = entry?.count ?? '?'
        purgeLog.value.push(`  ✅ ${ds.label}: deleted ${n} observations`)
        if (entry) {
          totalDeleted += entry.count ?? 0
          entry.count = 0
          entry.error = null
        }
      } else if (status === 405) {
        // Server doesn't support bulk delete — fall back to iterative
        purgeLog.value.push(`  ⚠️ ${ds.label}: bulk delete not supported, deleting individually…`)
        let deleted = 0
        let hasMore = true
        while (hasMore) {
          const { ok: listOk, data } = await apiFetch(
            `/datastreams/${ds.id}/observations?limit=100`
          )
          if (!listOk || !data?.items?.length) {
            hasMore = false
            break
          }
          for (const obs of data.items) {
            const obsId = obs.id ?? obs['@id']
            if (!obsId) continue
            await apiFetch(`/observations/${obsId}`, 'DELETE')
            deleted++
          }
          if (data.items.length < 100) hasMore = false
        }
        purgeLog.value.push(`  ✅ ${ds.label}: deleted ${deleted} observations (individually)`)
        totalDeleted += deleted
        const entry = counts.value.find(c => c.dsId === ds.id)
        if (entry) { entry.count = 0; entry.error = null }
      } else {
        purgeLog.value.push(`  ❌ ${ds.label}: failed (HTTP ${status})`)
      }
    }

    purgeLog.value.push('')
    purgeLog.value.push(`Done — ${totalDeleted.toLocaleString()} total observations purged`)
    purging.value = false
  }

  /** Purge all publisher observations */
  async function purgeAll() {
    const allDs = PUBLISHER_GROUPS.flatMap(g => g.datastreams)
    await purgeDatastreams(allDs, 'All Publishers')
  }

  /** Purge all observations for a single publisher group (e.g. 'ISS') */
  async function purgeGroup(groupName: string) {
    const group = PUBLISHER_GROUPS.find(g => g.name === groupName)
    if (!group) return
    await purgeDatastreams(group.datastreams, group.name)
  }

  /** Purge observations for a single datastream by ID */
  async function purgeDatastream(dsId: string) {
    // Find the DS entry across all groups
    for (const group of PUBLISHER_GROUPS) {
      const ds = group.datastreams.find(d => d.id === dsId)
      if (ds) {
        await purgeDatastreams([ds], ds.label)
        return
      }
    }
  }

  return {
    counts,
    fetching,
    purging,
    purgeLog,
    lastFetched,
    totalObs,
    groupTotals,
    fetchCounts,
    purgeAll,
    purgeGroup,
    purgeDatastream,
    PUBLISHER_GROUPS,
  }
}
