/**
 * Production health check — browser-side equivalent of scripts/smoke_test.py
 *
 * Checks all known resources on the OS4CSAPI server:
 * - Global endpoints (/datastreams, /systems, /deployments)
 * - 14 individual systems
 * - 3 deployments
 * - 12 critical datastream observations with staleness thresholds
 *
 * READ-ONLY: no writes to the server.
 */
import { ref, computed } from 'vue'
import { connection } from '../state'

// ── Expected resources (mirrors scripts/smoke_test.py) ──────────────

const EXPECTED_SYSTEMS: Record<string, string> = {
  '040g': 'SET Ft Huachuca',
  '0410': 'Monitoring Site Node',
  '041g': 'VHF Relay/Repeater',
  '0420': 'ODAS AZ-MA-1',
  '0490': 'ODAS AZ-MA-2',
  '049g': 'ODAS AZ-MA-3',
  '04o0': 'Localizer',
  '04og': 'ISS Position Publisher',
  '04p0': 'ISS Orbit Track Publisher',
  '04pg': 'NWS KTUS',
  '04q0': 'NWS KDMA',
  '04qg': 'NWS KFHU',
  '04r0': 'NWS KLUF',
  '04rg': 'NWS KPHX',
}

const EXPECTED_DEPLOYMENTS: Record<string, string> = {
  '040g': 'Intelligence Collection Operation',
  '048g': 'Orbital Tracking Demo',
  '04cg': 'NWS Weather Demo',
}

interface DsInfo {
  id: string
  system: string
}

const CRITICAL_DATASTREAMS: Record<string, DsInfo> = {
  'ISS Position SGP4':      { id: '04gg', system: '04og' },
  'ISS Orbit Ground Track': { id: '04h0', system: '04p0' },
  'NWS KTUS Surface Obs':   { id: '04ig', system: '04pg' },
  'NWS KDMA Surface Obs':   { id: '04j0', system: '04q0' },
  'NWS KFHU Surface Obs':   { id: '04jg', system: '04qg' },
  'NWS KLUF Surface Obs':   { id: '04k0', system: '04r0' },
  'NWS KPHX Surface Obs':   { id: '04kg', system: '04rg' },
  'AZ-MA-1 LOB':            { id: '04c0', system: '0420' },
  'AZ-MA-2 LOB':            { id: '04cg', system: '0490' },
  'AZ-MA-3 LOB':            { id: '04d0', system: '049g' },
  'UAS Location Estimate':  { id: '04l0', system: '04o0' },
  'SENREP':                 { id: '044g', system: '040g' },
}

// ── Staleness thresholds (minutes) ──
const THRESHOLDS = {
  ISS: 5,
  NWS: 480,  // 8 hours — publisher may run periodically
  SIM: 360,  // 6 hours — simulator may restart
}

// ── Types ───────────────────────────────────────────────────────────

export type CheckStatus = 'pass' | 'fail' | 'skip' | 'pending' | 'running'

export interface HealthCheck {
  name: string
  group: string
  status: CheckStatus
  detail: string
}

export interface HealthCheckState {
  checks: HealthCheck[]
  running: boolean
  elapsed: number
  timestamp: string
}

// ── Composable ──────────────────────────────────────────────────────

export function useHealthCheck() {
  const checks = ref<HealthCheck[]>([])
  const running = ref(false)
  const elapsed = ref(0)
  const timestamp = ref('')

  const summary = computed(() => {
    const passed = checks.value.filter(c => c.status === 'pass').length
    const failed = checks.value.filter(c => c.status === 'fail').length
    const skipped = checks.value.filter(c => c.status === 'skip').length
    const total = checks.value.length
    return { passed, failed, skipped, total }
  })

  const overallStatus = computed(() => {
    if (running.value) return 'running'
    if (checks.value.length === 0) return 'idle'
    return summary.value.failed > 0 ? 'fail' : 'pass'
  })

  // ── API helper ──
  async function apiGet(path: string): Promise<{ status: number; data: any }> {
    const url = connection.baseUrl + path
    try {
      const resp = await fetch(url, {
        headers: {
          ...connection.authHeaders,
          'Accept': 'application/json',
        },
      })
      if (!resp.ok) return { status: resp.status, data: null }
      const data = await resp.json()
      return { status: resp.status, data }
    } catch (e: any) {
      return { status: 0, data: e.message }
    }
  }

  function obsAgeMinutes(resultTime: string): number {
    const dt = new Date(resultTime)
    return (Date.now() - dt.getTime()) / 60000
  }

  function addCheck(group: string, name: string): HealthCheck {
    const check: HealthCheck = { name, group, status: 'pending', detail: '' }
    checks.value.push(check)
    return check
  }

  function pass(check: HealthCheck, detail: string) {
    check.status = 'pass'
    check.detail = detail
  }

  function fail(check: HealthCheck, detail: string) {
    check.status = 'fail'
    check.detail = detail
  }

  function _skip(check: HealthCheck, detail: string) {
    check.status = 'skip'
    check.detail = detail
  }

  // ── Individual checks ──

  async function checkGlobalEndpoint(endpoint: string, label: string, minCount: number) {
    const c = addCheck('Global Endpoints', label)
    c.status = 'running'
    const { status, data } = await apiGet(`/${endpoint}?limit=200`)
    if (status !== 200) { fail(c, `HTTP ${status}`); return }
    const count = data?.items?.length ?? 0
    if (count < minCount) {
      fail(c, `Only ${count} (expected ≥ ${minCount})`)
    } else {
      pass(c, `${count} found`)
    }
  }

  async function checkSystem(id: string, expectedName: string) {
    const c = addCheck('Systems', `${expectedName}`)
    c.status = 'running'
    const { status, data } = await apiGet(`/systems/${id}`)
    if (status !== 200) { fail(c, `HTTP ${status}`); return }
    pass(c, data?.properties?.name ?? 'exists')
  }

  async function checkDeployment(id: string, expectedName: string) {
    const c = addCheck('Deployments', `${expectedName}`)
    c.status = 'running'
    const { status, data } = await apiGet(`/deployments/${id}`)
    if (status !== 200) { fail(c, `HTTP ${status}`); return }
    pass(c, data?.properties?.name ?? 'exists')
  }

  async function checkDatastreamObs(dsName: string, dsInfo: DsInfo) {
    const c = addCheck('Observations', dsName)
    c.status = 'running'

    // Check DS exists
    const { status: dsStatus } = await apiGet(`/datastreams/${dsInfo.id}`)
    if (dsStatus !== 200) { fail(c, `DS not found (HTTP ${dsStatus})`); return }

    // Fetch latest obs
    const { status: obsStatus, data: obsData } = await apiGet(
      `/datastreams/${dsInfo.id}/observations?limit=1&resultTime=latest`
    )
    if (obsStatus !== 200) { fail(c, `Obs query HTTP ${obsStatus}`); return }

    const items = obsData?.items ?? []
    if (items.length === 0) { fail(c, 'No observations'); return }

    const obs = items[0]
    const rt = obs.resultTime ?? ''
    const ageMin = rt ? obsAgeMinutes(rt) : Infinity

    if (dsName.includes('ISS')) {
      if (ageMin > THRESHOLDS.ISS) {
        fail(c, `Stale — ${Math.round(ageMin)} min (max ${THRESHOLDS.ISS})`)
      } else {
        pass(c, `${ageMin.toFixed(1)} min old`)
      }
    } else if (dsName.includes('NWS')) {
      if (ageMin > THRESHOLDS.NWS) {
        fail(c, `Stale — ${Math.round(ageMin)} min (max ${THRESHOLDS.NWS})`)
      } else {
        const result = obs.result ?? {}
        const temp = result.temperature_c
        const tempStr = temp == null || isNaN(temp) ? '—' : `${temp}°C`
        pass(c, `${Math.round(ageMin)} min old, ${tempStr}`)
      }
    } else {
      if (ageMin > THRESHOLDS.SIM) {
        fail(c, `Stale — ${Math.round(ageMin)} min (max ${THRESHOLDS.SIM})`)
      } else {
        pass(c, `${ageMin.toFixed(1)} min old`)
      }
    }
  }

  // ── Run all ──

  async function runAll() {
    checks.value = []
    running.value = true
    elapsed.value = 0
    timestamp.value = new Date().toISOString()
    const t0 = performance.now()

    try {
      // Global endpoints (parallel)
      await Promise.all([
        checkGlobalEndpoint('datastreams', '/datastreams', 30),
        checkGlobalEndpoint('systems', '/systems', 14),
        checkGlobalEndpoint('deployments', '/deployments', 3),
      ])

      // Systems (parallel)
      await Promise.all(
        Object.entries(EXPECTED_SYSTEMS).map(([id, name]) => checkSystem(id, name))
      )

      // Deployments (parallel)
      await Promise.all(
        Object.entries(EXPECTED_DEPLOYMENTS).map(([id, name]) => checkDeployment(id, name))
      )

      // Critical datastream observations (parallel)
      await Promise.all(
        Object.entries(CRITICAL_DATASTREAMS).map(([name, info]) => checkDatastreamObs(name, info))
      )
    } finally {
      elapsed.value = Math.round(performance.now() - t0)
      running.value = false
    }
  }

  return {
    checks,
    running,
    elapsed,
    timestamp,
    summary,
    overallStatus,
    runAll,
  }
}
