/**
 * Production health check — browser-side equivalent of scripts/smoke_test.py
 *
 * Checks all known resources on the OS4CSAPI server:
 * - Global endpoints (/datastreams, /systems, /deployments)
 * - 44 individual systems (incl. 8 USGS Water, 1 USGS Earthquake)
 * - 10 deployments (incl. USGS Water, NIMS Imagery, Seismic Monitoring)
 * - 63 critical datastream observations with staleness thresholds (incl. 5 BuoyCAM, 5 CO-OPS, 5 AWX METAR, 1 OpenSky, 16 USGS Water, 8 NIMS Imagery, 1 USGS Earthquake)
 *
 * READ-ONLY: no writes to the server.
 */
import { ref, computed } from 'vue'
import { connection } from '../state'
import { fetchWithFallback, CSAPI_BASE, CSAPI_AUTH } from './originFallback'

function getBaseUrl() {
  return connection.baseUrl || CSAPI_BASE
}

function getAuthHeaders(): Record<string, string> {
  if (connection.baseUrl && Object.keys(connection.authHeaders).length) {
    return connection.authHeaders
  }
  return { Authorization: CSAPI_AUTH }
}

// ── Expected resources (mirrors scripts/smoke_test.py) ──────────────

const EXPECTED_SYSTEMS: Record<string, string> = {
  '04j0': 'SET Ft Huachuca',
  '04jg': 'Monitoring Site Node',
  '04k0': 'VHF Relay/Repeater',
  '04kg': 'ODAS AZ-MA-1',
  '04l0': 'ODAS AZ-MA-2',
  '04lg': 'ODAS AZ-MA-3',
  '059g': 'Localizer',
  '04i0': 'ISS Position Publisher',
  '04ig': 'ISS Orbit Track Publisher',
  '040g': 'NWS KTUS',
  '0410': 'NWS KDMA',
  '041g': 'NWS KFHU',
  '0420': 'NWS KLUF',
  '042g': 'NWS KPHX',
  '0430': 'NWS KDCA',
  '043g': 'NWS KIAD',
  '0440': 'NWS KNYG',
  '044g': 'NWS KDAY',
  '0450': 'NWS KFFO',
  // NDBC buoys
  '045g': 'NDBC 44025 Long Island',
  '0460': 'NDBC 41009 Canaveral',
  '046g': 'NDBC 42036 W Tampa',
  '0470': 'NDBC 46025 Santa Monica',
  '047g': 'NDBC 46013 Bodega Bay',
  // CO-OPS tide stations
  '0480': 'CO-OPS 8518750 The Battery',
  '048g': 'CO-OPS 8723214 Virginia Key',
  '0490': 'CO-OPS 8726520 St. Petersburg',
  '049g': 'CO-OPS 9414290 San Francisco',
  '04a0': 'CO-OPS 8443970 Boston',
  // AviationWeather METAR stations
  '04ag': 'AWX KTUS Tucson Intl',
  '04b0': 'AWX KDMA Davis-Monthan',
  '04bg': 'AWX KFHU Fort Huachuca',
  '04c0': 'AWX KLUF Luke AFB',
  '04cg': 'AWX KPHX Sky Harbor',
  // OpenSky ADS-B feed
  '04d0': 'OpenSky ADS-B Feed',
  // USGS Earthquake feed
  '04dg': 'USGS Earthquake Feed',
  // USGS Water monitoring stations
  '04e0': 'USGS 09380000 Colorado River Lees Ferry',
  '04eg': 'USGS 09019850 Willow Creek Granby',
  '04f0': 'USGS 11313433 Dutch Slough',
  '04fg': 'USGS 08171000 Blanco River Wimberley',
  '04g0': 'USGS 01650800 Sligo Creek Takoma Park',
  '04gg': 'USGS 05051300 Bois De Sioux Doran',
  '04h0': 'USGS 12439500 Okanogan River Oroville',
  '04hg': 'USGS 02135000 Little Pee Dee Galivants Ferry',
}

const EXPECTED_DEPLOYMENTS: Record<string, string> = {
  '04vg': 'Intelligence Collection Operation',
  '04t0': 'Orbital Tracking Demo',
  '040g': 'NWS Weather Demo',
  '046g': 'NDBC Buoy Demo',
  '04a0': 'CO-OPS Coastal Demo',
  '04dg': 'AWX METAR Demo',
  '04h0': 'Airspace Tracking Demo',
  '04i0': 'Seismic Monitoring Demo',
  '04j0': 'USGS Water Monitoring Demo',
  '04o0': 'USGS NIMS Imagery Demo',
}

interface DsInfo {
  id: string
  system: string
}

const CRITICAL_DATASTREAMS: Record<string, DsInfo> = {
  'ISS Position SGP4':      { id: '04sg', system: '04i0' },
  'ISS Orbit Ground Track': { id: '04t0', system: '04ig' },
  'NWS KTUS Surface Obs':   { id: '040g', system: '040g' },
  'NWS KDMA Surface Obs':   { id: '0410', system: '0410' },
  'NWS KFHU Surface Obs':   { id: '041g', system: '041g' },
  'NWS KLUF Surface Obs':   { id: '0420', system: '0420' },
  'NWS KPHX Surface Obs':   { id: '042g', system: '042g' },
  'NWS KDCA Surface Obs':   { id: '0430', system: '0430' },
  'NWS KIAD Surface Obs':   { id: '043g', system: '043g' },
  'NWS KNYG Surface Obs':   { id: '0440', system: '0440' },
  'NWS KDAY Surface Obs':   { id: '044g', system: '044g' },
  'NWS KFFO Surface Obs':   { id: '0450', system: '0450' },
  'AZ-MA-1 LOB':            { id: '04v0', system: '04kg' },
  'AZ-MA-2 LOB':            { id: '0530', system: '04l0' },
  'AZ-MA-3 LOB':            { id: '0570', system: '04lg' },
  'UAS Location Estimate':  { id: '05a0', system: '059g' },
  'SENREP':                 { id: '04tg', system: '04j0' },
  // NDBC buoys (met obs)
  'NDBC 44025 Met Obs':     { id: '045g', system: '045g' },
  'NDBC 41009 Met Obs':     { id: '046g', system: '0460' },
  'NDBC 42036 Met Obs':     { id: '047g', system: '046g' },
  'NDBC 46025 Met Obs':     { id: '048g', system: '0470' },
  'NDBC 46013 Met Obs':     { id: '049g', system: '047g' },
  // NDBC buoys (BuoyCAM)
  'NDBC 44025 BuoyCAM':     { id: '0460', system: '045g' },
  'NDBC 41009 BuoyCAM':     { id: '0470', system: '0460' },
  'NDBC 42036 BuoyCAM':     { id: '0480', system: '046g' },
  'NDBC 46025 BuoyCAM':     { id: '0490', system: '0470' },
  'NDBC 46013 BuoyCAM':     { id: '04a0', system: '047g' },
  // CO-OPS tide stations
  'CO-OPS 8518750 Coastal Obs': { id: '04ag', system: '0480' },
  'CO-OPS 8723214 Coastal Obs': { id: '04b0', system: '048g' },
  'CO-OPS 8726520 Coastal Obs': { id: '04bg', system: '0490' },
  'CO-OPS 9414290 Coastal Obs': { id: '04c0', system: '049g' },
  'CO-OPS 8443970 Coastal Obs': { id: '04cg', system: '04a0' },
  // AviationWeather METAR stations
  'AWX KTUS METAR Obs':         { id: '04d0', system: '04ag' },
  'AWX KDMA METAR Obs':         { id: '04dg', system: '04b0' },
  'AWX KFHU METAR Obs':         { id: '04e0', system: '04bg' },
  'AWX KLUF METAR Obs':         { id: '04eg', system: '04c0' },
  'AWX KPHX METAR Obs':         { id: '04f0', system: '04cg' },
  // OpenSky ADS-B feed
  'OpenSky ADS-B States':         { id: '04fg', system: '04d0' },
  // USGS Water monitoring (discharge)
  'USGS 09380000 Discharge':      { id: '04gg', system: '04e0' },
  'USGS 09019850 Discharge':      { id: '04hg', system: '04eg' },
  'USGS 11313433 Discharge':      { id: '04ig', system: '04f0' },
  'USGS 08171000 Discharge':      { id: '04jg', system: '04fg' },
  'USGS 01650800 Discharge':      { id: '04kg', system: '04g0' },
  'USGS 05051300 Discharge':      { id: '04lg', system: '04gg' },
  'USGS 12439500 Discharge':      { id: '04mg', system: '04h0' },
  'USGS 02135000 Discharge':      { id: '04ng', system: '04hg' },
  // USGS Water monitoring (gage height)
  'USGS 09380000 Gage Height':    { id: '04h0', system: '04e0' },
  'USGS 09019850 Gage Height':    { id: '04i0', system: '04eg' },
  'USGS 11313433 Gage Height':    { id: '04j0', system: '04f0' },
  'USGS 08171000 Gage Height':    { id: '04k0', system: '04fg' },
  'USGS 01650800 Gage Height':    { id: '04l0', system: '04g0' },
  'USGS 05051300 Gage Height':    { id: '04m0', system: '04gg' },
  'USGS 12439500 Gage Height':    { id: '04n0', system: '04h0' },
  'USGS 02135000 Gage Height':    { id: '04o0', system: '04hg' },
  // USGS NIMS Imagery (companion datastreams on existing water systems)
  'NIMS 09380000 Imagery':          { id: '04og', system: '04e0' },
  'NIMS 09019850 Imagery':          { id: '04p0', system: '04eg' },
  'NIMS 11313433 Imagery':          { id: '04pg', system: '04f0' },
  'NIMS 08171000 Imagery':          { id: '04q0', system: '04fg' },
  'NIMS 01650800 Imagery':          { id: '04qg', system: '04g0' },
  'NIMS 05051300 Imagery':          { id: '04r0', system: '04gg' },
  'NIMS 12439500 Imagery':          { id: '04rg', system: '04h0' },
  'NIMS 02135000 Imagery':          { id: '04s0', system: '04hg' },
  // USGS Earthquake feed
  'USGS Earthquake Events':          { id: '04g0', system: '04dg' },
}

// ── Staleness thresholds (minutes) ──
const THRESHOLDS = {
  ISS: 5,
  NWS: 480,   // 8 hours — publisher may run periodically
  NDBC: 480,  // 8 hours — publisher runs hourly
  COOPS: 480, // 8 hours — publisher runs every 6 min
  AWX: 480,   // 8 hours — publisher runs every 5 min
  OPENSKY: 480, // 8 hours — publisher runs every 5 min
  USGS: 480,  // 8 hours — publisher runs every 15 min
  NIMS: 480,  // 8 hours — imagery publisher runs every 15 min
  EARTHQUAKE: 480, // 8 hours — earthquake publisher runs every 60s
  SIM: 360,   // 6 hours — simulator may restart
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
    try {
      // When connected via proxy, use that URL directly; otherwise use origin fallback
      if (connection.baseUrl) {
        const resp = await fetch(getBaseUrl() + path, {
          headers: { ...getAuthHeaders(), 'Accept': 'application/json' },
        })
        if (!resp.ok) return { status: resp.status, data: null }
        return { status: resp.status, data: await resp.json() }
      }
      // Direct-to-server with fallback across origins
      const resp = await fetchWithFallback(
        path.replace(/^\//, ''),
        { headers: { 'Accept': 'application/json' } },
        getAuthHeaders(),
      )
      if (!resp.ok) return { status: resp.status, data: null }
      return { status: resp.status, data: await resp.json() }
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
    let { status: obsStatus, data: obsData } = await apiGet(
      `/datastreams/${dsInfo.id}/observations?limit=1&resultTime=latest`
    )
    // Fallback: Go CSAPI server ignores resultTime=latest
    if (obsStatus === 200 && !(obsData?.items?.length)) {
      ({ status: obsStatus, data: obsData } = await apiGet(
        `/datastreams/${dsInfo.id}/observations?limit=1`
      ))
    }
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
    } else if (dsName.includes('CO-OPS')) {
      if (ageMin > THRESHOLDS.COOPS) {
        fail(c, `Stale — ${Math.round(ageMin)} min (max ${THRESHOLDS.COOPS})`)
      } else {
        const result = obs.result ?? {}
        const wl = result.water_level_m
        const airTemp = result.air_temp_c
        const wlStr = wl == null || (typeof wl === 'string' && wl === 'NaN') ? '—' : `${wl}m`
        const airStr = airTemp == null || (typeof airTemp === 'string' && airTemp === 'NaN') ? '—' : `${airTemp}°C`
        pass(c, `${Math.round(ageMin)} min old, wl=${wlStr} air=${airStr}`)
      }
    } else if (dsName.includes('AWX')) {
      if (ageMin > THRESHOLDS.AWX) {
        fail(c, `Stale — ${Math.round(ageMin)} min (max ${THRESHOLDS.AWX})`)
      } else {
        const result = obs.result ?? {}
        const temp = result.temp_c
        const fltCat = result.flight_category ?? '—'
        const tempStr = temp == null || (typeof temp === 'string' && temp === 'NaN') ? '—' : `${temp}°C`
        pass(c, `${Math.round(ageMin)} min old, ${tempStr} ${fltCat}`)
      }
    } else if (dsName.includes('OpenSky')) {
      if (ageMin > THRESHOLDS.OPENSKY) {
        fail(c, `Stale — ${Math.round(ageMin)} min (max ${THRESHOLDS.OPENSKY})`)
      } else {
        const result = obs.result ?? {}
        const callsign = (result.callsign ?? '?').trim()
        const alt = result.baro_altitude_m
        const altStr = alt != null && alt !== 'NaN' ? `${alt}m` : '—'
        pass(c, `${Math.round(ageMin)} min old, ${callsign} alt=${altStr}`)
      }
    } else if (dsName.includes('NIMS')) {
      if (ageMin > THRESHOLDS.NIMS) {
        fail(c, `Stale — ${Math.round(ageMin)} min (max ${THRESHOLDS.NIMS})`)
      } else {
        const result = obs.result ?? {}
        const fn = result.filename ?? '—'
        const cam = result.camId ?? '—'
        const thumb = result.thumbUrl ? '✓' : '—'
        const tl = result.timeLapseUrl ? '✓' : '—'
        pass(c, `${Math.round(ageMin)} min old, cam=${cam}, ${fn}, thumb=${thumb}, timelapse=${tl}`)
      }
    } else if (dsName.includes('Earthquake')) {
      if (ageMin > THRESHOLDS.EARTHQUAKE) {
        fail(c, `Stale — ${Math.round(ageMin)} min (max ${THRESHOLDS.EARTHQUAKE})`)
      } else {
        const result = obs.result ?? {}
        const mag = result.magnitude
        const place = result.place ?? '—'
        const magStr = mag != null && mag !== 'NaN' ? `M${mag}` : '—'
        pass(c, `${Math.round(ageMin)} min old, ${magStr} ${place}`)
      }
    } else if (dsName.includes('USGS')) {
      if (ageMin > THRESHOLDS.USGS) {
        fail(c, `Stale — ${Math.round(ageMin)} min (max ${THRESHOLDS.USGS})`)
      } else {
        const result = obs.result ?? {}
        if (dsName.includes('Discharge')) {
          const val = result.discharge_cfs
          const valStr = val != null && val !== 'NaN' ? `${val} ft³/s` : '—'
          pass(c, `${Math.round(ageMin)} min old, ${valStr}`)
        } else {
          const val = result.gage_height_ft
          const valStr = val != null && val !== 'NaN' ? `${val} ft` : '—'
          pass(c, `${Math.round(ageMin)} min old, ${valStr}`)
        }
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
        checkGlobalEndpoint('datastreams', '/datastreams', 71),
        checkGlobalEndpoint('systems', '/systems', 39),
        checkGlobalEndpoint('deployments', '/deployments', 10),
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
