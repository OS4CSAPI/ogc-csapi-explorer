/**
 * Production health check — browser-side equivalent of scripts/smoke_test.py
 *
 * Checks all known resources on the OS4CSAPI server:
 * - Global endpoints (/datastreams, /systems, /deployments)
 * - 24 individual systems
 * - 4 deployments
 * - 27 critical datastream observations with staleness thresholds (incl. 5 BuoyCAM)
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
  '0520': 'NWS KTUS',
  '052g': 'NWS KDMA',
  '0530': 'NWS KFHU',
  '053g': 'NWS KLUF',
  '0540': 'NWS KPHX',
  '054g': 'NWS KDCA',
  '0550': 'NWS KIAD',
  '055g': 'NWS KNYG',
  '0560': 'NWS KDAY',
  '056g': 'NWS KFFO',
  // NDBC buoys
  '0570': 'NDBC 44025 Long Island',
  '057g': 'NDBC 41009 Canaveral',
  '0580': 'NDBC 42036 W Tampa',
  '058g': 'NDBC 46025 Santa Monica',
  '0590': 'NDBC 46013 Bodega Bay',
}

const EXPECTED_DEPLOYMENTS: Record<string, string> = {
  '040g': 'Intelligence Collection Operation',
  '048g': 'Orbital Tracking Demo',
  '04mg': 'NWS Weather Demo',
  '04sg': 'NDBC Buoy Demo',
}

interface DsInfo {
  id: string
  system: string
}

const CRITICAL_DATASTREAMS: Record<string, DsInfo> = {
  'ISS Position SGP4':      { id: '04gg', system: '04og' },
  'ISS Orbit Ground Track': { id: '04h0', system: '04p0' },
  'NWS KTUS Surface Obs':   { id: '04qg', system: '0520' },
  'NWS KDMA Surface Obs':   { id: '04r0', system: '052g' },
  'NWS KFHU Surface Obs':   { id: '04rg', system: '0530' },
  'NWS KLUF Surface Obs':   { id: '04s0', system: '053g' },
  'NWS KPHX Surface Obs':   { id: '04sg', system: '0540' },
  'NWS KDCA Surface Obs':   { id: '04t0', system: '054g' },
  'NWS KIAD Surface Obs':   { id: '04tg', system: '0550' },
  'NWS KNYG Surface Obs':   { id: '04u0', system: '055g' },
  'NWS KDAY Surface Obs':   { id: '04ug', system: '0560' },
  'NWS KFFO Surface Obs':   { id: '04v0', system: '056g' },
  'AZ-MA-1 LOB':            { id: '04c0', system: '0420' },
  'AZ-MA-2 LOB':            { id: '04cg', system: '0490' },
  'AZ-MA-3 LOB':            { id: '04d0', system: '049g' },
  'UAS Location Estimate':  { id: '04l0', system: '04o0' },
  'SENREP':                 { id: '044g', system: '040g' },
  // NDBC buoys (met obs)
  'NDBC 44025 Met Obs':     { id: '04vg', system: '0570' },
  'NDBC 41009 Met Obs':     { id: '050g', system: '057g' },
  'NDBC 42036 Met Obs':     { id: '051g', system: '0580' },
  'NDBC 46025 Met Obs':     { id: '052g', system: '058g' },
  'NDBC 46013 Met Obs':     { id: '053g', system: '0590' },
  // NDBC buoys (BuoyCAM)
  'NDBC 44025 BuoyCAM':     { id: '0500', system: '0570' },
  'NDBC 41009 BuoyCAM':     { id: '0510', system: '057g' },
  'NDBC 42036 BuoyCAM':     { id: '0520', system: '0580' },
  'NDBC 46025 BuoyCAM':     { id: '0530', system: '058g' },
  'NDBC 46013 BuoyCAM':     { id: '0540', system: '0590' },
}

// ── Staleness thresholds (minutes) ──
const THRESHOLDS = {
  ISS: 5,
  NWS: 480,  // 8 hours — publisher may run periodically
  NDBC: 480, // 8 hours — publisher runs hourly
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
    } else if (dsName.includes('NDBC')) {
      if (ageMin > THRESHOLDS.NDBC) {
        fail(c, `Stale — ${Math.round(ageMin)} min (max ${THRESHOLDS.NDBC})`)
      } else if (dsName.includes('BuoyCAM')) {
        const result = obs.result ?? {}
        const status = result.cameraStatus ?? '—'
        const sizeKb = result.contentLength ? `${Math.round(result.contentLength / 1024)} KB` : '—'
        pass(c, `${Math.round(ageMin)} min old, camera=${status}, ${sizeKb}`)
      } else {
        const result = obs.result ?? {}
        const airTemp = result.air_temp_c
        const waterTemp = result.water_temp_c
        const airStr = airTemp == null || isNaN(airTemp) ? '—' : `${airTemp}°C`
        const waterStr = waterTemp == null || isNaN(waterTemp) ? '—' : `${waterTemp}°C`
        pass(c, `${Math.round(ageMin)} min old, air=${airStr} water=${waterStr}`)
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
        checkGlobalEndpoint('datastreams', '/datastreams', 35),
        checkGlobalEndpoint('systems', '/systems', 19),
        checkGlobalEndpoint('deployments', '/deployments', 4),
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
