/**
 * Composable for building a rich "Deployed System Card" from CSAPI resources.
 *
 * Follows the OS4CSAPI Deployed System Card Field Mapping Spec v1.
 * A deployed-system card is composed from four sources:
 *   1. Deployment  — context, role, hierarchy, location, lifecycle
 *   2. Occupant System — identity, kind, ownership, manufacturer/model
 *   3. Procedures — how the thing works
 *   4. Datastreams — what it produces, freshness
 *
 * Only applies to deployment leaves with an occupant system (platform@link).
 */
import { ref, type Ref } from 'vue'
import { apiFetch } from '../api'
import { getSymbolForResource } from '../symbol-mapper'
import { rankCameraProcedureCandidates } from './camera-license-resolver.js'

// ─── Card model ────────────────────────────────────────────────────────────

export interface DeployedSystemCardModel {
  cardType: 'deployed-system-card'

  // Header
  title: string
  subtitle: string
  roleBadge: string
  statusBadge: string
  kindBadge: string
  thumbnail: string // URL or empty
  stanagSvg: string // data:image/svg+xml URL for STANAG symbol, or empty

  // Summary
  summarySentence: string

  // Context
  deploymentPath: string
  parentDeployment: string
  deploymentType: string
  geometrySummary: string
  validState: string

  // Occupant
  occupantName: string
  occupantUid: string
  occupantKind: string
  manufacturerModelOrVersion: string
  ownerMaintainer: string

  // Outputs & Methods
  primaryPurpose: string
  capabilities: string[]
  primaryDatastreams: DatastreamSummary[]
  latestReadings: LatestReadingSummary[]
  forecastSummaries: ForecastSummary[]
  trendSummaries: TrendSummary[]
  productLabels: string[]
  latestActivityTime: string
  latestActivityRelative: string
  lastRefreshTime: string
  lastRefreshRelative: string
  refreshCadence: string
  cadenceNote: string
  controlStreamCount: number
  primaryProcedures: ProcedureSummary[]
  methodSummary: string
  keyAssumptions: string[]

  // Freshness / Trust
  qualitySummary: string
  healthState: string
  contributingSources: string

  // Media / References
  docsLinks: DocLink[]
  mediaLinks: MediaLink[]

  // Live Camera (NDBC BuoyCAM or USGS NIMS imagery datastream)
  cameraImageUrl: string
  cameraTimestamp: string
  cameraLabel: string       // e.g. "Live BuoyCAM" or "Live Camera"
  cameraThumbUrl: string    // NIMS thumbnail URL (empty for BuoyCAM)
  cameraTimeLapseUrl: string // NIMS timelapse URL (empty for BuoyCAM)
  cameraCamId: string       // NIMS camId (empty for BuoyCAM)
  cameraLastCheckedTime: string
  cameraLastCheckedRelative: string
  cameraImageChangedTime: string
  cameraImageChangedRelative: string
  cameraUnchangedDuration: string
  cameraStalenessStatus: string
  cameraImageChanged: boolean | null
  cameraPlayerUrl: string
  cameraPageUrl: string
  cameraSourceUrl: string
  cameraAttributionText: string
  cameraLicenseUrl: string
  cameraLicenseLabel: string

  /** @deprecated Use cameraImageUrl instead */
  buoycamImageUrl: string
  /** @deprecated Use cameraTimestamp instead */
  buoycamTimestamp: string

  // Advanced IDs
  advancedDeploymentUid: string
  advancedSystemUid: string
  advancedDeploymentId: string
  advancedSystemId: string
  advancedBootstrapOwner: string
  advancedSourceOfTruth: string
}

export interface DatastreamSummary {
  id: string
  name: string
  productLabel: string
  observedProperties: string[]
  documentation: DocLink[]
}

export interface LatestReadingSummary {
  datastreamId: string
  label: string
  value: string
  unit: string
  phenomenonTime: string
  resultTime: string
  relativeTime: string
  quality: string
  freshnessState: 'current' | 'recent' | 'stale' | 'unknown'
}

export interface ForecastSummary {
  datastreamId: string
  label: string
  value: string
  unit: string
  issuedTime: string
  validTime: string
  relativeValidTime: string
  leadTimeHours: string
  forecastType: string
}

export interface TrendSummary {
  datastreamId: string
  label: string
  unit: string
  windowLabel: string
  latestValue: string
  latestRelativeTime: string
  trendLabel: string
  trendState: 'rising' | 'falling' | 'steady'
  points: number[]
  sampleCount: number
}

export interface ProcedureSummary {
  id: string
  name: string
  description: string
  uid: string
}

export interface DocLink {
  title: string
  href: string
  role: string
}

export interface MediaLink {
  title: string
  href: string
  type: string
}

const EA_HYDROLOGY_REPRESENTATIVE_IMAGE = 'https://upload.wikimedia.org/wikipedia/commons/f/f0/Environment_Agency_Morton_River_Gauge_Station_-_geograph.org.uk_-_283345.jpg'
const UK_AIR_ROADSIDE_REPRESENTATIVE_IMAGE = 'https://upload.wikimedia.org/wikipedia/commons/0/0e/Air_Quality_Monitoring_Station_-_geograph.org.uk_-_2573031.jpg'
const UK_AIR_BACKGROUND_REPRESENTATIVE_IMAGE = 'https://upload.wikimedia.org/wikipedia/commons/7/75/Air-quality_monitoring_station%2C_Dundonald_-_geograph.org.uk_-_3201697.jpg'
const BGS_SENSORTHINGS_REPRESENTATIVE_IMAGE = 'https://www.ukgeos.ac.uk/assets/img/svgs/illustrations/borehole_dimmensions.svg'
const MET_OFFICE_LAND_OBS_REPRESENTATIVE_IMAGE = 'https://upload.wikimedia.org/wikipedia/commons/thumb/5/59/Charterhall_Met_Office_Weather_Station_-_Image_%5E1_-_geograph.org.uk_-_2754908.jpg/960px-Charterhall_Met_Office_Weather_Station_-_Image_%5E1_-_geograph.org.uk_-_2754908.jpg'
const MET_OFFICE_GLOBAL_SPOT_REPRESENTATIVE_IMAGE = 'https://upload.wikimedia.org/wikipedia/commons/3/3b/Met_Office_Weather_Station_at_Lusa_-_geograph.org.uk_-_808151.jpg'
const DIGITRAFFIC_ROAD_WEATHER_REPRESENTATIVE_IMAGE = 'https://upload.wikimedia.org/wikipedia/commons/9/94/Traffic_weather_station_general_view.jpg'
const DIGITRAFFIC_MARINE_AIS_REPRESENTATIVE_IMAGE = 'https://upload.wikimedia.org/wikipedia/commons/5/51/Compact_AIS_antenna.jpg'
const DIGITRAFFIC_RAIL_REPRESENTATIVE_IMAGE = 'https://images.unsplash.com/photo-1474487548417-781cb71495f3?auto=format&fit=crop&w=1200&q=80'
const FMI_WEATHER_REPRESENTATIVE_IMAGE = 'https://upload.wikimedia.org/wikipedia/commons/2/21/S%C3%A4%C3%A4asema_Kylm%C3%A4pihlaja.jpg'
const FMI_AIR_QUALITY_REPRESENTATIVE_IMAGE = 'https://upload.wikimedia.org/wikipedia/commons/b/bd/Oksakyvetti_-_Smear_II_-asema_-_Hyyti%C3%A4l%C3%A4%2C_Juupajoki.jpg'
const SYKE_HYDROLOGY_REPRESENTATIVE_IMAGE = 'https://upload.wikimedia.org/wikipedia/commons/1/12/Crews_Lake_Water_Level_Gauge.jpg'

// ─── SML field extractors ──────────────────────────────────────────────────

function extractSmlLabel(sml: any): string {
  return sml?.label || sml?.name || ''
}

function extractSmlDescription(sml: any): string {
  return sml?.description || ''
}

function extractSmlKeywords(sml: any): string[] {
  if (!sml?.keywords) return []
  const kws: string[] = []
  for (const kw of sml.keywords) {
    if (Array.isArray(kw.keyword)) kws.push(...kw.keyword)
    else if (typeof kw === 'string') kws.push(kw)
  }
  return kws
}

function extractSmlIdentifiers(sml: any): Record<string, string> {
  const map: Record<string, string> = {}
  const ids = sml?.identifiers || sml?.identification
  if (!ids) return map
  const list = Array.isArray(ids) ? ids : [ids]
  for (const item of list) {
    // Flat format: item is {definition, label, value}
    if (item.value != null && (item.label || item.name || item.definition)) {
      const label = item.label || item.name || item.definition || ''
      map[label] = String(item.value)
      continue
    }
    // Nested format: item has identifierList/characteristicList
    const chars = item?.characteristicList || item?.identifierList
    if (Array.isArray(chars)) {
      for (const c of chars) {
        const label = c.label || c.name || c.definition || ''
        const value = c.value ?? ''
        if (label) map[label] = String(value)
      }
    }
  }
  return map
}

function extractSmlClassifiers(sml: any): Record<string, string> {
  const map: Record<string, string> = {}
  const cls = sml?.classifiers || sml?.classification
  if (!cls) return map
  const list = Array.isArray(cls) ? cls : [cls]
  for (const item of list) {
    // Flat format: item is {definition, label, value}
    if (item.value != null && (item.label || item.name || item.definition)) {
      const label = item.label || item.name || item.definition || ''
      map[label] = String(item.value)
      continue
    }
    // Nested format: item has classifierList
    const chars = item?.classifierList
    if (Array.isArray(chars)) {
      for (const c of chars) {
        const label = c.label || c.name || c.definition || ''
        const value = c.value ?? ''
        if (label) map[label] = String(value)
      }
    }
  }
  return map
}

function extractSmlCapabilities(sml: any): Record<string, string> {
  const map: Record<string, string> = {}
  const caps = sml?.capabilities
  if (!caps) return map
  const list = Array.isArray(caps) ? caps : [caps]
  for (const group of list) {
    // OSH format: group has .capabilities array (nested items)
    const cList = group?.capabilities || group?.capabilityList
    if (Array.isArray(cList)) {
      for (const c of cList) {
        const label = c.label || c.name || ''
        if (c.value != null) {
          const uom = c.uom?.code || (typeof c.uom === 'string' ? c.uom : '')
          map[label] = `${c.value}${uom ? ' ' + uom : ''}`
        }
      }
      continue
    }
    // Flat single capability item
    if (group.value != null && (group.label || group.name)) {
      const label = group.label || group.name || ''
      const uom = group.uom?.code || (typeof group.uom === 'string' ? group.uom : '')
      map[label] = `${group.value}${uom ? ' ' + uom : ''}`
    }
  }
  return map
}

function extractSmlContacts(sml: any): Array<{ role: string; name: string; org: string }> {
  const contacts: Array<{ role: string; name: string; org: string }> = []
  const cList = sml?.contacts
  if (!cList) return contacts
  const list = Array.isArray(cList) ? cList : [cList]
  for (const item of list) {
    // Flat format: item is {role, organisationName, individualName, ...}
    if (item.role || item.organisationName || item.individualName) {
      contacts.push({
        role: item.role || '',
        name: item.individualName || item.name || '',
        org: item.organisationName || item.organization || '',
      })
      continue
    }
    // Nested format: item has contactList
    const members = item?.contactList
    if (Array.isArray(members)) {
      for (const c of members) {
        contacts.push({
          role: c.role || '',
          name: c.individualName || c.name || '',
          org: c.organisationName || c.organization || '',
        })
      }
    }
  }
  return contacts
}

function extractSmlDocuments(sml: any): DocLink[] {
  const docs: DocLink[] = []
  const dList = sml?.documents || sml?.documentation
  if (!dList) return docs
  const list = Array.isArray(dList) ? dList : [dList]
  for (const item of list) {
    // Flat format: item is {role, name, description, link: {href, type}}
    if (item.name || item.label || item.link || item.url) {
      docs.push({
        title: item.name || item.label || item.description || 'Document',
        href: item.link?.href || item.url || item.onlineResource?.linkage || item.linkage || '',
        role: item.role || '',
      })
      continue
    }
    // Nested format: item has documentList
    const members = item?.documentList
    if (Array.isArray(members)) {
      for (const d of members) {
        docs.push({
          title: d.name || d.label || d.description || 'Document',
          href: d.link?.href || d.url || d.onlineResource?.linkage || d.linkage || '',
          role: d.role || '',
        })
      }
    }
  }
  return docs
}

function extractSmlMedia(sml: any): MediaLink[] {
  const media: MediaLink[] = []
  // Typically in documents with role = "photo" or image MIME or link.type = image/*
  const dList = sml?.documents || sml?.documentation
  if (!dList) return media
  const list = Array.isArray(dList) ? dList : [dList]
  for (const item of list) {
    // Flat format: item is {role, name, link: {href, type}}
    const href = item.link?.href || item.url || item.onlineResource?.linkage || item.linkage || ''
    const mt = item.link?.type || item.mediaType || item.format || ''
    const nameOrRole = (item.role || '') + ' ' + (item.name || '')
    if (mt.startsWith('image/') || /photo|photograph|thumbnail|preview/i.test(nameOrRole)) {
      media.push({
        title: item.name || item.label || 'Image',
        href,
        type: mt,
      })
      continue
    }
    // Nested format: item has documentList
    const members = item?.documentList
    if (Array.isArray(members)) {
      for (const d of members) {
        const dHref = d.link?.href || d.url || d.onlineResource?.linkage || d.linkage || ''
        const dMt = d.link?.type || d.mediaType || d.format || ''
        const dNameOrRole = (d.role || '') + ' ' + (d.name || '')
        if (dMt.startsWith('image/') || /photo|photograph|thumbnail|preview/i.test(dNameOrRole)) {
          media.push({
            title: d.name || d.label || 'Image',
            href: dHref,
            type: dMt,
          })
        }
      }
    }
  }
  return media
}

function isLicenseLikeDoc(doc: DocLink): boolean {
  const hay = `${doc.title} ${doc.role} ${doc.href}`.toLowerCase()
  return /license|licence|terms|rights|copyright/.test(hay)
}

function normalizeLicenseUrl(url: string): string {
  if (!url) return ''
  try {
    const parsed = new URL(url)
    // Normalize known legacy Digitraffic path that now returns 404.
    if (parsed.hostname.endsWith('digitraffic.fi') && parsed.pathname === '/en/terms-of-use/') {
      parsed.pathname = '/en/terms-of-service/'
      return parsed.toString()
    }
  } catch {
    return url
  }
  return url
}

function representativeThumbnailForCard(
  rawData: any,
  deploymentName: string,
  systemName: string,
  keywords: string[],
): string {
  const props = rawData?.properties || rawData || {}
  const text = [
    deploymentName,
    props.name,
    props.description,
    props.uid,
    props['platform@link']?.title,
    props['platform@link']?.uid,
    systemName,
    ...keywords,
  ].filter(Boolean).join(' ').toLowerCase()

  if (text.includes('environment agency') && text.includes('hydrology')) {
    return EA_HYDROLOGY_REPRESENTATIVE_IMAGE
  }
  if (text.includes('bgs') || text.includes('sensorthings') || text.includes('ukgeos') || text.includes('hydro logger')) {
    return BGS_SENSORTHINGS_REPRESENTATIVE_IMAGE
  }
  if (text.includes('uk-air') || text.includes('uk air')) {
    if (text.includes('camden') || text.includes('roadside') || text.includes('kerbside')) {
      return UK_AIR_ROADSIDE_REPRESENTATIVE_IMAGE
    }
    return UK_AIR_BACKGROUND_REPRESENTATIVE_IMAGE
  }
  if (text.includes('global spot') || text.includes('site-specific forecast') || text.includes('forecast point')) {
    return MET_OFFICE_GLOBAL_SPOT_REPRESENTATIVE_IMAGE
  }
  if (text.includes('met office') || text.includes('weather datahub') || text.includes('land observations')) {
    return MET_OFFICE_LAND_OBS_REPRESENTATIVE_IMAGE
  }
  if (text.includes('fmi weather') || text.includes('fmiweatherobs') || (text.includes('finnish meteorological institute') && text.includes('weather'))) {
    return FMI_WEATHER_REPRESENTATIVE_IMAGE
  }
  if (text.includes('fmi air quality') || text.includes('fmiairqualityobs') || (text.includes('finnish meteorological institute') && text.includes('air quality'))) {
    return FMI_AIR_QUALITY_REPRESENTATIVE_IMAGE
  }
  if ((text.includes('digitraffic') || text.includes('fintraffic')) && (text.includes('rail') || text.includes('train'))) {
    return DIGITRAFFIC_RAIL_REPRESENTATIVE_IMAGE
  }
  if (text.includes('syke') || text.includes('hydrologiarajapinta') || text.includes('vesi.fi')) {
    return SYKE_HYDROLOGY_REPRESENTATIVE_IMAGE
  }
  if (text.includes('marine ais') || text.includes('digitrafficmarineais') || text.includes('vessel position')
    || (text.includes('digitraffic') && text.includes('marine')) || (text.includes('fintraffic') && text.includes('ais'))) {
    return DIGITRAFFIC_MARINE_AIS_REPRESENTATIVE_IMAGE
  }
  if (text.includes('digitraffic') || text.includes('fintraffic') || text.includes('road weather') || text.includes('roadweatherobs')) {
    return DIGITRAFFIC_ROAD_WEATHER_REPRESENTATIVE_IMAGE
  }
  return ''
}

// ─── Role/kind/status vocabulary normalization ─────────────────────────────

const ROLE_LABELS: Record<string, string> = {
  'air-quality-site': 'Air Quality Site',
  'groundwater-telemetry-site': 'Groundwater Telemetry Site',
  'weather-observation-site': 'Weather Observation Site',
  'sensor-node': 'Sensor Node',
  'acoustic-sensor-node': 'Acoustic Sensor Node',
  'localizer': 'Localizer',
  'fusion-agent': 'Fusion Agent',
  'set': 'Sensor Exploitation Team',
  'relay': 'Communications Relay',
  'monitoring-site': 'Monitoring Site',
  'orbit-feed': 'Orbit Feed',
  'feed-leaf': 'Feed Leaf',
  'sensor-leaf': 'Sensor Leaf',
  'support-leaf': 'Support Leaf',
  'role-leaf': 'Role Leaf',
}

const KIND_LABELS: Record<string, string> = {
  'physical': 'Physical Device',
  'physicalDevice': 'Physical Device',
  'physical-device': 'Physical Device',
  'software': 'Software Agent',
  'softwareAgent': 'Software Agent',
  'software-agent': 'Software Agent',
  'software-fusion-agent': 'Software Fusion Agent',
  'human': 'Human Team',
  'humanTeam': 'Human Team',
  'human-team': 'Human Team',
  'support': 'Support System',
  'supportSystem': 'Support System',
  'support-system': 'Support System',
  'communications-relay': 'Communications Relay',
}

function normalizeLabel(value: string, vocab: Record<string, string>): string {
  if (!value) return ''
  const lower = value.toLowerCase().replace(/[_ ]/g, '-')
  if (vocab[lower]) return vocab[lower]
  if (vocab[value]) return vocab[value]
  // Title-case fallback
  return value.replace(/[-_]/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}

// ─── Relative time formatter ───────────────────────────────────────────────

function relativeTime(isoString: string): string {
  if (!isoString) return ''
  try {
    const then = new Date(isoString).getTime()
    const now = Date.now()
    const diffMs = now - then
    if (diffMs < 0) return 'in the future'
    const secs = Math.floor(diffMs / 1000)
    if (secs < 60) return `${secs}s ago`
    const mins = Math.floor(secs / 60)
    if (mins < 60) return `${mins}m ago`
    const hrs = Math.floor(mins / 60)
    if (hrs < 24) return `${hrs}h ago`
    const days = Math.floor(hrs / 24)
    return `${days}d ago`
  } catch {
    return ''
  }
}

function formatDurationSeconds(value: unknown): string {
  const seconds = typeof value === 'number' ? value : Number(value)
  if (!Number.isFinite(seconds) || seconds < 0) return ''
  if (seconds < 60) return `${Math.floor(seconds)}s`
  const mins = Math.floor(seconds / 60)
  if (mins < 60) return `${mins}m`
  const hrs = Math.floor(mins / 60)
  const remMins = mins % 60
  if (hrs < 24) return remMins ? `${hrs}h ${remMins}m` : `${hrs}h`
  const days = Math.floor(hrs / 24)
  const remHours = hrs % 24
  return remHours ? `${days}d ${remHours}h` : `${days}d`
}

function metadataValue(map: Record<string, string>, labels: string[]): string {
  const wanted = labels.map(label => label.toLowerCase().replace(/[^a-z0-9]/g, ''))
  for (const [label, value] of Object.entries(map)) {
    const normalized = label.toLowerCase().replace(/[^a-z0-9]/g, '')
    if (wanted.includes(normalized)) return value
  }
  return ''
}

function formatCadenceValue(value: string): string {
  const trimmed = value.trim()
  if (!trimmed) return ''

  const match = trimmed.match(/^(\d+(?:\.\d+)?)\s*(s|sec|secs|second|seconds)$/i)
  if (!match) return trimmed

  const seconds = Number(match[1])
  if (!Number.isFinite(seconds) || seconds <= 0) return trimmed
  const secondsLabel = Number.isInteger(seconds) ? String(seconds) : String(Number(seconds.toPrecision(3)))
  if (seconds < 60) return `Every ${secondsLabel}s`
  if (seconds % 3600 === 0) {
    const hours = seconds / 3600
    const hoursLabel = Number.isInteger(hours) ? String(hours) : String(Number(hours.toPrecision(3)))
    return `Every ${hoursLabel}h (${secondsLabel}s)`
  }
  if (seconds % 60 === 0) {
    const minutes = seconds / 60
    const minutesLabel = Number.isInteger(minutes) ? String(minutes) : String(Number(minutes.toPrecision(3)))
    return `Every ${minutesLabel}m (${secondsLabel}s)`
  }
  return `Every ${secondsLabel}s`
}

function relativeForecastTime(isoString: string): string {
  if (!isoString) return ''
  const then = new Date(isoString).getTime()
  if (!Number.isFinite(then)) return isoString
  const diffMs = then - Date.now()
  const absMs = Math.abs(diffMs)
  const mins = Math.floor(absMs / 60000)
  if (mins < 1) return diffMs >= 0 ? 'now' : 'just now'
  if (mins < 60) return diffMs >= 0 ? `in ${mins}m` : `${mins}m ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return diffMs >= 0 ? `in ${hrs}h` : `${hrs}h ago`
  const days = Math.floor(hrs / 24)
  return diffMs >= 0 ? `in ${days}d` : `${days}d ago`
}

function observationItems(data: any): any[] {
  const items = data?.items || data || []
  return Array.isArray(items) ? items : []
}

function newestObservation(items: any[]): any | null {
  return items
    .filter(Boolean)
    .sort((a, b) => {
      const aTime = new Date(a.resultTime || a.phenomenonTime || '').getTime()
      const bTime = new Date(b.resultTime || b.phenomenonTime || '').getTime()
      return (Number.isFinite(bTime) ? bTime : 0) - (Number.isFinite(aTime) ? aTime : 0)
    })[0] || null
}

async function fetchLatestObservation(datastreamId: string): Promise<any | null> {
  const latestRes = await apiFetch(
    `/datastreams/${datastreamId}/observations?resultTime=latest&limit=20`,
    { headers: { 'Accept': 'application/json' } },
  )
  if (latestRes.ok && latestRes.data) {
    const items = observationItems(latestRes.data)
    const latest = newestObservation(items)
    if (latest) return latest
  }

  const fallbackRes = await apiFetch(
    `/datastreams/${datastreamId}/observations?limit=1`,
    { headers: { 'Accept': 'application/json' } },
  )
  if (!fallbackRes.ok || !fallbackRes.data) return null
  return newestObservation(observationItems(fallbackRes.data))
}

async function fetchRecentObservations(datastreamId: string, limit: number, windowHours: number): Promise<any[]> {
  const latest = await fetchLatestObservation(datastreamId)
  const anchorTime = latest?.resultTime || latest?.phenomenonTime
  if (!anchorTime) return latest ? [latest] : []

  const anchorMs = new Date(anchorTime).getTime()
  if (!Number.isFinite(anchorMs)) return latest ? [latest] : []

  const start = encodeURIComponent(new Date(anchorMs - windowHours * 60 * 60 * 1000).toISOString())
  const end = encodeURIComponent(new Date(anchorMs + 1000).toISOString())
  const windowRes = await apiFetch(
    `/datastreams/${datastreamId}/observations?resultTime=${start}%2F${end}&limit=${limit}&sortBy=resultTime&sortOrder=asc`,
    { headers: { 'Accept': 'application/json' } },
  )
  if (!windowRes.ok || !windowRes.data) return latest ? [latest] : []
  const items = observationItems(windowRes.data)
  return items.length > 0 ? items : (latest ? [latest] : [])
}

function readingFreshnessState(isoString: string): LatestReadingSummary['freshnessState'] {
  if (!isoString) return 'unknown'
  const then = new Date(isoString).getTime()
  if (!Number.isFinite(then)) return 'unknown'
  const ageMs = Date.now() - then
  if (ageMs < 0) return 'current'
  if (ageMs <= 60 * 60 * 1000) return 'current'
  if (ageMs <= 24 * 60 * 60 * 1000) return 'recent'
  return 'stale'
}

function isCameraDatastreamName(name: string): boolean {
  return /buoycam|buoy[\s_-]?cam|weather[\s_-]?cam|weather\s+camera|camera|webcam|cam.*image|nims.*image|station.*image/i.test(name)
}

function isForecastDatastream(ds: DatastreamSummary): boolean {
  const text = [ds.name, ds.productLabel, ...ds.observedProperties].filter(Boolean).join(' ')
  return /forecast|global spot|site[-\s]?specific/i.test(text)
}

async function fetchCameraProcedureLicense(
  cameraDs: DatastreamSummary,
  sourceHintText: string,
): Promise<{ licenseDoc: DocLink | null; sourceName: string }> {
  const listRes = await apiFetch('/procedures?limit=200', {
    headers: { 'Accept': 'application/json' },
  })
  if (!listRes.ok || !listRes.data) return { licenseDoc: null, sourceName: '' }

  const procedureItems = Array.isArray(listRes.data.items) ? listRes.data.items : []
  const scored = rankCameraProcedureCandidates(
    cameraDs.name,
    cameraDs.productLabel,
    sourceHintText,
    procedureItems,
  )

  for (const candidate of scored) {
    const smlRes = await apiFetch(`/procedures/${candidate.id}?f=application/sml%2Bjson`, {
      headers: { 'Accept': 'application/sml+json' },
    })
    if (!smlRes.ok || !smlRes.data) continue
    const src = smlRes.data?.type === 'Feature' ? (smlRes.data?.properties || {}) : (smlRes.data || {})
    const docs = extractSmlDocuments(src)
    const licenseDoc = docs.find(isLicenseLikeDoc) || null
    if (!licenseDoc) continue
    const procContacts = extractSmlContacts(src)
    const operatorContact = procContacts.find(c => /operator|owner|provider/i.test(c.role || ''))
    const sourceName = operatorContact?.org || operatorContact?.name || ''
    return { licenseDoc, sourceName }
  }

  return { licenseDoc: null, sourceName: '' }
}

const RESULT_METADATA_KEYS = new Set([
  'stationId', 'stationName', 'measureId', 'parameter', 'unit', 'valueType',
  'quality', 'completeness', 'sourceUrl', 'lat', 'lon', 'alt', 'latitude', 'longitude',
  'lat_deg', 'lon_deg',
  'locationId', 'geohash',
  'forecastType', 'issuedTime', 'validTime', 'leadTimeHours',
  'imageUrl', 'latestImageUrl', 'thumbUrl', 'mediaType', 'contentLength', 'camId',
  'cameraId', 'cameraTitle', 'locationName', 'posterUrl', 'playerUrl', 'pageUrl',
  'sourceType', 'live', 'httpStatus', 'etag', 'lastModified', 'sourceLastModifiedTime',
  'imageSha256', 'imageChanged', 'firstSeenTime', 'lastSeenTime', 'lastChangedTime',
  'unchangedPollCount', 'stalenessStatus', 'sourceAgeSeconds',
  'thingId', 'sourceThingId', 'sourceDatastreamId', 'observedProperty', 'sourceObservationId', 'publishFlag',
])

const VALUE_PRIORITY_KEYS = [
  'value',
  'air_temperature_c', 'air_temp_c', 'temperature_c',
  'water_temperature_c', 'water_temp_c',
  'river_level_m', 'groundwater_level_m', 'water_level_m',
  'water_level_cm',
  'river_flow_m3s', 'flow_m3s', 'discharge_m3s',
  'speed_kmh',
  'rainfall_mm',
  'wind_speed_ms', 'wind_gust_ms',
  'precipitation_probability_pct', 'weather_code',
  'pressure_hpa', 'mean_sea_level_pressure_hpa',
  'relative_humidity_pct',
  'conductivity_us_cm', 'conductivity_uS_cm',
]

const SOURCE_VALUE_PRIORITY_KEYS: Array<{ pattern: RegExp; keys: string[] }> = [
  {
    pattern: /ndbc|buoy/i,
    keys: [
      'wind_speed_ms', 'wind_gust_ms', 'pressure_hpa',
      'air_temp_c', 'air_temperature_c', 'water_temp_c', 'water_temperature_c', 'wave_height_m',
    ],
  },
  {
    pattern: /met office|weather datahub|land observations/i,
    keys: [
      'air_temperature_c', 'mean_sea_level_pressure_hpa', 'wind_speed_ms',
      'wind_gust_ms', 'relative_humidity_pct', 'pressure_tendency_code', 'visibility_m',
    ],
  },
  {
    pattern: /environment agency|ea hydrology|river|rainfall|groundwater/i,
    keys: ['value', 'river_level_m', 'river_flow_m3s', 'flow_m3s', 'rainfall_mm', 'groundwater_level_m'],
  },
  {
    pattern: /syke|hydrologiarajapinta|vesi\.fi|sykedischarge|sykewaterlevel/i,
    keys: ['water_level_cm', 'discharge_m3s', 'value'],
  },
  {
    pattern: /digitraffic|fintraffic|rail|train/i,
    keys: ['speed_kmh', 'value'],
  },
  {
    pattern: /uk-air|uk air|air quality|nitrogen dioxide|ozone|particulate/i,
    keys: ['value', 'no2_ugm3', 'no2_ug_m3', 'o3_ugm3', 'o3_ug_m3', 'pm10_ugm3', 'pm10_ug_m3', 'pm25_ugm3', 'pm25_ug_m3'],
  },
  {
    pattern: /bgs|sensorthings|ukgeos|hydro logger|conductivity|water level maod/i,
    keys: ['water_level_maod_m', 'water_level_m', 'water_temperature_c', 'water_temp_c', 'conductivity_us_cm', 'conductivity_uS_cm'],
  },
]

function formatObservationValue(value: unknown, unit: string): string {
  if (typeof value === 'number') {
    if (value === 0 && /mm/i.test(unit)) return '0.0'
    if (Number.isInteger(value)) return String(value)
    return String(Number(value.toPrecision(4)))
  }
  if (typeof value === 'string') return value
  return String(value ?? '')
}

function labelForReading(ds: DatastreamSummary, result: any, valueKey: string): string {
  const parameter = String(result?.parameter || '').toLowerCase()
  const observedProperty = String(result?.observedProperty || '').toLowerCase()
  const unit = String(result?.unit || '').toLowerCase()
  if (valueKey === 'air_temperature_c' || valueKey === 'air_temp_c' || valueKey === 'temperature_c') return 'Air Temperature'
  if (valueKey === 'relative_humidity_pct') return 'Relative Humidity'
  if (valueKey === 'mean_sea_level_pressure_hpa' || valueKey === 'pressure_hpa') return 'Mean Sea Level Pressure'
  if (valueKey === 'visibility_m' || valueKey === 'visibility_nmi') return 'Visibility'
  if (valueKey === 'weather_code') return 'Weather Code'
  if (valueKey === 'wind_direction_deg') return 'Wind Direction'
  if (valueKey === 'wind_speed_ms') return 'Wind Speed'
  if (valueKey === 'wind_gust_ms') return 'Wind Gust'
  if (valueKey === 'speed_kmh') return 'Train Speed'
  if (valueKey === 'precipitation_probability_pct') return 'Precipitation Probability'
  if (valueKey === 'pressure_tendency_code' || valueKey === 'pressure_tendency_hpa') return 'Pressure Tendency'
  if (valueKey === 'water_temp_c' || valueKey === 'water_temperature_c') return 'Water Temperature'
  if (valueKey === 'wave_height_m') return 'Wave Height'
  if (observedProperty.includes('water level maod') || valueKey.toLowerCase().includes('maod')) return 'Water Level maOD'
  if (observedProperty.includes('water temperature')) return 'Water Temperature'
  if (observedProperty.includes('conductivity')) return 'Conductivity'
  if (parameter === 'rainfall' || valueKey.toLowerCase().includes('rainfall')) return 'Rainfall'
  if (valueKey.toLowerCase().includes('water_level_cm')) return 'Water Level'
  if (parameter === 'flow' || valueKey.toLowerCase().includes('flow')) return 'River flow'
  if (parameter === 'level' && unit === 'maod') return 'Groundwater level'
  if (parameter === 'level' || valueKey.toLowerCase().includes('level')) return 'River level'
  return ds.productLabel || ds.name || valueKey.replace(/_/g, ' ')
}

function summarizeForecast(ds: DatastreamSummary, obs: any): ForecastSummary | null {
  const result = obs?.result || {}
  if (!result || typeof result !== 'object') return null

  const validTime = result.validTime || obs.phenomenonTime || ''
  if (!validTime) return null

  const entries = Object.entries(result).filter(([key, value]) =>
    !RESULT_METADATA_KEYS.has(key)
    && value !== null
    && value !== undefined
    && (typeof value === 'number' || (typeof value === 'string' && value.trim() && value.trim().toLowerCase() !== 'nan'))
  )
  const valueEntry = chooseValueEntry(entries, ds, result)
  if (!valueEntry) return null

  const [valueKey, value] = valueEntry
  const unit = unitForValueKey(valueKey, result)
  const rawLeadTime = result.leadTimeHours
  const leadTimeHours = typeof rawLeadTime === 'number'
    ? `${rawLeadTime}h`
    : rawLeadTime && String(rawLeadTime).trim().toLowerCase() !== 'nan'
      ? String(rawLeadTime)
      : ''

  return {
    datastreamId: ds.id,
    label: labelForReading(ds, result, valueKey),
    value: formatObservationValue(value, unit),
    unit,
    issuedTime: result.issuedTime || obs.resultTime || '',
    validTime,
    relativeValidTime: relativeForecastTime(validTime),
    leadTimeHours,
    forecastType: result.forecastType || 'Forecast',
  }
}

async function fetchForecastSummary(ds: DatastreamSummary): Promise<ForecastSummary | null> {
  try {
    const items = await fetchRecentObservations(ds.id, 96, 48)
    if (items.length === 0) return null
    const now = Date.now()
    const forecasts = items
      .map(obs => summarizeForecast(ds, obs))
      .filter((summary): summary is ForecastSummary => !!summary)
      .sort((a, b) => {
        const aTime = new Date(a.validTime).getTime()
        const bTime = new Date(b.validTime).getTime()
        const aFuture = Number.isFinite(aTime) && aTime >= now
        const bFuture = Number.isFinite(bTime) && bTime >= now
        if (aFuture !== bFuture) return aFuture ? -1 : 1
        return Math.abs(aTime - now) - Math.abs(bTime - now)
      })
    return forecasts[0] || null
  } catch {
    return null
  }
}

function unitForValueKey(valueKey: string, result: any): string {
  if (result?.unit) return result.unit
  if (/_pct$/.test(valueKey)) return '%'
  if (/_hpa$/.test(valueKey)) return 'hPa'
  if (/_c$/.test(valueKey)) return 'C'
  if (/_ms$/.test(valueKey)) return 'm/s'
  if (/_kmh$/.test(valueKey)) return 'km/h'
  if (/_m3s$/.test(valueKey)) return 'm3/s'
  if (/_cm$/.test(valueKey)) return 'cm'
  if (/_mm$/.test(valueKey)) return 'mm'
  if (/_m$/.test(valueKey)) return 'm'
  if (/_nmi$/.test(valueKey)) return 'nmi'
  if (/_deg$/.test(valueKey)) return 'deg'
  if (/_ugm3$/.test(valueKey) || /_ug_m3$/.test(valueKey)) return 'ug/m3'
  if (/conductivity/i.test(valueKey)) return 'uS/cm'
  return ''
}

function valuePriorityKeysFor(ds: DatastreamSummary, result: any): string[] {
  const text = [
    ds.name,
    ds.productLabel,
    ...ds.observedProperties,
    result?.parameter,
    result?.observedProperty,
  ].filter(Boolean).join(' ')
  const sourceSpecific = SOURCE_VALUE_PRIORITY_KEYS.find(priority => priority.pattern.test(text))?.keys || []
  return [...sourceSpecific, ...VALUE_PRIORITY_KEYS]
}

function chooseValueEntry(
  entries: Array<[string, unknown]>,
  ds: DatastreamSummary,
  result: any,
): [string, unknown] | undefined {
  for (const key of valuePriorityKeysFor(ds, result)) {
    const found = entries.find(([entryKey]) => entryKey === key)
    if (found) return found
  }
  return entries.find(([, value]) => typeof value === 'number') || entries[0]
}

function extractNumericObservationValue(ds: DatastreamSummary, obs: any): {
  value: number
  valueKey: string
  unit: string
  label: string
  time: string
} | null {
  const result = obs?.result || {}
  if (!result || typeof result !== 'object') return null
  const entries = Object.entries(result).filter(([key, value]) =>
    !RESULT_METADATA_KEYS.has(key)
    && typeof value === 'number'
    && Number.isFinite(value)
  )
  const valueEntry = chooseValueEntry(entries, ds, result)
  if (!valueEntry) return null
  const [valueKey, value] = valueEntry
  const unit = unitForValueKey(valueKey, result)
  const time = obs.phenomenonTime || obs.resultTime || ''
  if (!time) return null
  return {
    value: value as number,
    valueKey,
    unit,
    label: labelForReading(ds, result, valueKey),
    time,
  }
}

function summarizeLatestReading(ds: DatastreamSummary, obs: any): LatestReadingSummary | null {
  const result = obs?.result || {}
  if (!result || typeof result !== 'object') return null

  const entries = Object.entries(result).filter(([key, value]) =>
    !RESULT_METADATA_KEYS.has(key)
    && value !== null
    && value !== undefined
    && (typeof value === 'number' || (typeof value === 'string' && value.trim() && value.trim().toLowerCase() !== 'nan'))
  )
  const valueEntry = chooseValueEntry(entries, ds, result)
  if (!valueEntry) return null

  const [valueKey, value] = valueEntry
  const unit = unitForValueKey(valueKey, result)
  const phenomenonTime = obs.phenomenonTime || obs.resultTime || ''
  const resultTime = obs.resultTime || ''

  return {
    datastreamId: ds.id,
    label: labelForReading(ds, result, valueKey),
    value: formatObservationValue(value, unit),
    unit,
    phenomenonTime,
    resultTime,
    relativeTime: phenomenonTime ? relativeTime(phenomenonTime) : '',
    quality: result.quality || '',
    freshnessState: readingFreshnessState(phenomenonTime),
  }
}

async function fetchLatestReading(ds: DatastreamSummary): Promise<LatestReadingSummary | null> {
  try {
    const latest = await fetchLatestObservation(ds.id)
    return latest ? summarizeLatestReading(ds, latest) : null
  } catch {
    return null
  }
}

function trendWindowLabel(firstTime: string, lastTime: string): string {
  const first = new Date(firstTime).getTime()
  const last = new Date(lastTime).getTime()
  if (!Number.isFinite(first) || !Number.isFinite(last) || last <= first) return 'Recent trend'
  const hours = Math.max(1, Math.round((last - first) / (60 * 60 * 1000)))
  if (hours >= 48) return `Last ${Math.round(hours / 24)}d`
  return `Last ${hours}h`
}

async function fetchTrendSummary(ds: DatastreamSummary): Promise<TrendSummary | null> {
  try {
    if (isCameraDatastreamName(ds.name)) return null
    const items = await fetchRecentObservations(ds.id, 48, 48)
    if (items.length < 2) return null

    const samples = items
      .map(obs => extractNumericObservationValue(ds, obs))
      .filter((sample): sample is NonNullable<typeof sample> => !!sample)
      .sort((a, b) => new Date(a.time).getTime() - new Date(b.time).getTime())

    if (samples.length < 2) return null

    const first = samples[0]!
    const latest = samples[samples.length - 1]!
    const values = samples.map(sample => sample.value)
    const minValue = Math.min(...values)
    const maxValue = Math.max(...values)
    const range = maxValue - minValue
    const delta = latest.value - first.value
    const epsilon = Math.max(Math.abs(latest.value) * 0.005, range * 0.08, 0.0001)
    const trendState: TrendSummary['trendState'] = Math.abs(delta) <= epsilon
      ? 'steady'
      : delta > 0 ? 'rising' : 'falling'
    const trendLabel = trendState === 'steady'
      ? 'Steady'
      : trendState === 'rising' ? 'Rising' : 'Falling'

    return {
      datastreamId: ds.id,
      label: latest.label,
      unit: latest.unit,
      windowLabel: trendWindowLabel(first.time, latest.time),
      latestValue: formatObservationValue(latest.value, latest.unit),
      latestRelativeTime: relativeTime(latest.time),
      trendLabel,
      trendState,
      points: values,
      sampleCount: samples.length,
    }
  } catch {
    return null
  }
}

// ─── Geometry summary ──────────────────────────────────────────────────────

function summarizeGeometry(item: any): string {
  const geom = item?.geometry
  if (!geom) return 'No geometry'
  if (geom.type === 'Point') {
    const [lon, lat] = geom.coordinates
    return `Point (${lat.toFixed(4)}°, ${lon.toFixed(4)}°)`
  }
  if (geom.type === 'Polygon') return 'Area / polygon'
  if (geom.type === 'LineString') return 'Line / track'
  return geom.type || 'Unknown geometry'
}

// ─── Deployment hierarchy helpers ──────────────────────────────────────────

/**
 * Build a deployment path breadcrumb by walking the hierarchy.
 * We use a two-strategy approach:
 *  1. Walk parent links from the enrichDeployments parentMap if available
 *  2. Fall back to fetching parent from the API
 */
async function buildDeploymentPath(
  deploymentId: string,
  deploymentName: string,
  itemById: Record<string, any>,
  parentMap: Record<string, string>,
): Promise<string> {
  const path: string[] = []
  let currentId = deploymentId
  let depth = 0

  while (currentId && depth < 10) {
    const parentId = parentMap[currentId]
    if (!parentId) break
    const parentItem = itemById[parentId]
    const parentName = parentItem
      ? (parentItem.properties?.name || parentItem.name || parentId)
      : parentId
    path.unshift(parentName)
    currentId = parentId
    depth++
  }

  path.push(deploymentName)
  return path.join(' > ')
}

// ─── Composition logic ────────────────────────────────────────────────────

function inferRoleFromContext(
  deploymentProps: any,
  systemSml: any,
  systemKeywords: string[],
  classifiers: Record<string, string>,
): string {
  // Try classifiers first (keys may be label text like "System Kind" or definition-based like "SensorType")
  const roleFromClassifier = classifiers['System Role'] || classifiers['Role Type']
    || classifiers['sensorType'] || classifiers['systemType']
    || classifiers['role'] || classifiers['Role']
    || classifiers['System Kind'] || ''
  if (roleFromClassifier) return roleFromClassifier

  // Try keywords
  const kwStr = systemKeywords.join(' ').toLowerCase()
  const contextText = `${kwStr} ${deploymentProps?.name || ''} ${deploymentProps?.description || ''}`.toLowerCase()
  if (/bgs|british geological survey|sensorthings|ukgeos|geothermal|groundwater|hydro logger/.test(contextText)) {
    return 'Groundwater Telemetry Site'
  }
  if (/uk[- ]air|air quality|air pollution|pollutant|\bno2\b|\bpm10\b|pm2\.5|ozone/.test(contextText)) {
    return 'Air Quality Site'
  }
  if (/met office|weather datahub|land observations|weather observation|weather station/.test(contextText)) {
    return 'Weather Observation Site'
  }
  if (kwStr.includes('acoustic') && kwStr.includes('sensor')) return 'Acoustic Sensor Node'
  if (kwStr.includes('localizer') || kwStr.includes('fusion')) return 'Software Fusion Agent'
  if (kwStr.includes('relay') || kwStr.includes('communications')) return 'Communications Relay'
  if (kwStr.includes('monitoring') || kwStr.includes('dissemination')) return 'Monitoring Site'
  if (kwStr.includes('senrep') || kwStr.includes('human') || kwStr.includes('team')) return 'Sensor Exploitation Team'
  if (kwStr.includes('orbit') || kwStr.includes('satellite') || kwStr.includes('iss')) return 'Orbit Feed'

  // Try description
  const desc = (extractSmlDescription(systemSml) || deploymentProps?.description || '').toLowerCase()
  if (/bgs|british geological survey|sensorthings|ukgeos|geothermal|groundwater|hydro logger/.test(desc)) {
    return 'Groundwater Telemetry Site'
  }
  if (/uk[- ]air|air quality|air pollution|pollutant|\bno2\b|\bpm10\b|pm2\.5|ozone/.test(desc)) {
    return 'Air Quality Site'
  }
  if (/met office|weather datahub|land observations|weather observation|weather station/.test(desc)) {
    return 'Weather Observation Site'
  }
  if (desc.includes('acoustic') || desc.includes('microphone')) return 'Sensor Node'
  if (desc.includes('localiz') || desc.includes('triangulat') || desc.includes('fusion')) return 'Fusion Agent'
  if (desc.includes('relay') || desc.includes('repeater')) return 'Communications Relay'
  if (desc.includes('monitoring')) return 'Monitoring Site'
  if (desc.includes('exploitation') || desc.includes('senrep')) return 'Sensor Exploitation Team'

  return ''
}

function inferKindFromContext(
  classifiers: Record<string, string>,
  keywords: string[],
  _identifiers: Record<string, string>,
): string {
  // Check classifiers (keys may be label text like "System Kind" or definition-based)
  const kindCls = classifiers['System Kind'] || classifiers['intendedApplication']
    || classifiers['systemKind'] || classifiers['Kind'] || ''
  if (kindCls) return kindCls

  const kwStr = keywords.join(' ').toLowerCase()
  if (kwStr.includes('physical') || kwStr.includes('hardware') || kwStr.includes('device')) return 'Physical Device'
  if (kwStr.includes('software') || kwStr.includes('algorithm') || kwStr.includes('fusion')) return 'Software Agent'
  if (kwStr.includes('human') || kwStr.includes('team')) return 'Human Team'
  if (kwStr.includes('relay') || kwStr.includes('support')) return 'Support System'

  return ''
}

function buildSummarySentence(
  role: string,
  parentName: string,
  purpose: string,
): string {
  if (!role && !parentName && !purpose) return ''

  // Use the description/purpose directly if it's concise enough
  if (purpose && purpose.length <= 180) {
    return purpose.endsWith('.') ? purpose : purpose + '.'
  }
  // Truncate long purpose
  if (purpose) {
    const truncated = purpose.substring(0, 175).replace(/\s\S*$/, '') + '…'
    return truncated
  }

  const roleStr = role || 'Deployed system'
  if (parentName) {
    return `${roleStr} under ${parentName}.`
  }
  return `${roleStr}.`
}

function inferPurpose(
  capabilities: Record<string, string>,
  keywords: string[],
  desc: string,
  _role: string,
): string {
  // Prefer description — use first sentence only
  if (desc) {
    const firstSentence = desc.split(/(?<=[.!?])\s/)[0] || desc
    const truncated =
      firstSentence.length > 150
        ? firstSentence.substring(0, 147).replace(/\s\S*$/, '') + '…'
        : firstSentence
    return truncated
  }

  // Summarise capabilities as operational text
  const capKeys = Object.keys(capabilities)
  if (capKeys.length > 0) {
    const capParts: string[] = []
    for (const key of capKeys.slice(0, 3)) {
      capParts.push(`${key}: ${capabilities[key]}`)
    }
    return capParts.join(' · ')
  }

  // Fall back to keywords
  if (keywords.length > 0) {
    return keywords.slice(0, 4).join(', ')
  }

  return ''
}

// ─── Main composable ──────────────────────────────────────────────────────

export function useDeployedSystemCard() {
  const loading = ref(false)
  const card: Ref<DeployedSystemCardModel | null> = ref(null)
  const error = ref('')

  /**
   * Determine if a selected feature should use the deployed-system card.
   */
  function isDeployedSystemLeaf(feature: any): boolean {
    if (!feature) return false
    if (feature.resourceType !== 'deployments') return false
    const props = feature.rawData?.properties || feature.rawData || {}
    return !!props['platform@link']?.href
  }

  /**
   * Compose the card model from the deployment rawData.
   * Fetches occupant system, datastreams, and procedures.
   */
  async function composeCard(
    feature: any,
    parentMap: Record<string, string>,
    itemById: Record<string, any>,
  ): Promise<void> {
    if (!isDeployedSystemLeaf(feature)) {
      card.value = null
      return
    }

    loading.value = true
    error.value = ''

    try {
      const rawData = feature.rawData
      const props = rawData?.properties || rawData || {}
      const deploymentId = feature.resourceId
      const deploymentName = feature.resourceName || props.name || 'Unnamed Deployed System'
      const deploymentUid = props.uid || ''
      const deploymentDesc = props.description || ''

      // ── Resolve occupant system ──────────────────────────────────
      const platformLink = props['platform@link']
      let systemId = ''
      let systemJson: any = null
      let systemSml: any = null

      if (platformLink?.href) {
        // Extract system ID from href: "/systems/04o0" → "04o0"
        systemId = platformLink.href.replace(/\/+$/, '').split('/').pop() || ''

        // Fetch system geo+json (basic identity)
        const [geoRes, smlRes] = await Promise.all([
          apiFetch(`/systems/${systemId}`, {
            headers: { 'Accept': 'application/geo+json' },
          }),
          apiFetch(`/systems/${systemId}?f=application/sml%2Bjson`, {
            headers: { 'Accept': 'application/sml+json' },
          }),
        ])

        if (geoRes.ok && geoRes.data) {
          systemJson = geoRes.data
        }
        if (smlRes.ok && smlRes.data) {
          systemSml = smlRes.data
        }
      }

      const systemProps = systemJson?.properties || systemJson || {}
      const systemName = systemProps.name || systemProps.title || platformLink?.title || ''
      const systemUid = systemProps.uid || platformLink?.uid || ''
      const systemDesc = systemProps.description || ''

      // Extract SML details
      // Normalize: Go v2 returns SML as a GeoJSON Feature (type='Feature', fields in .properties)
      // OSH returns SML with fields at top level (type='PhysicalSystem' etc.)
      const smlSource = systemSml?.type === 'Feature' ? (systemSml?.properties || {}) : (systemSml || {})
      const _smlLabel = extractSmlLabel(smlSource) // used for future enrichment
      void _smlLabel
      const smlDesc = extractSmlDescription(smlSource)
      const keywords = extractSmlKeywords(smlSource)
      const identifiers = extractSmlIdentifiers(smlSource)
      const classifiers = extractSmlClassifiers(smlSource)
      const capabilities = extractSmlCapabilities(smlSource)
      const contacts = extractSmlContacts(smlSource)
      const smlDocs = extractSmlDocuments(smlSource)
      const smlMedia = extractSmlMedia(smlSource)

      // ── Resolve datastreams ──────────────────────────────────────
      const datastreams: DatastreamSummary[] = []
      if (systemId) {
        try {
          const dsRes = await apiFetch(`/systems/${systemId}/datastreams?limit=10`, {
            headers: { 'Accept': 'application/json' },
          })
          if (dsRes.ok && dsRes.data) {
            const dsList = dsRes.data.items || dsRes.data || []
            for (const ds of (Array.isArray(dsList) ? dsList : [])) {
              const obsProps = ds.observedProperties || []
              datastreams.push({
                id: ds.id || '',
                name: ds.name || ds.outputName || '',
                productLabel: ds.name || ds.outputName || '',
                observedProperties: obsProps.map((p: any) =>
                  typeof p === 'string' ? p : (p.label || p.name || p.definition || '')
                ),
                documentation: Array.isArray(ds.documentation)
                  ? ds.documentation
                    .map((doc: any) => ({
                      title: doc?.title || doc?.name || '',
                      href: doc?.href || doc?.url || doc?.link?.href || '',
                      role: doc?.rel || doc?.role || '',
                    }))
                    .filter((doc: DocLink) => !!doc.href)
                  : [],
              })
            }
          }
        } catch { /* datastream fetch optional */ }
      }

      // ── Resolve procedures ───────────────────────────────────────
      const procedures: ProcedureSummary[] = []
      // Optional nested procedure discovery is intentionally skipped here.
      // Some live OSH deployments return 400 for /systems/{id}/procedures;
      // the card already has enough method/context from SensorML and docs.

      // ── Resolve latest observation summaries ─────────────────────
      const forecastDatastreams = datastreams.filter(ds => isForecastDatastream(ds))
      const observationDatastreams = datastreams.filter(ds => !isForecastDatastream(ds))
      const forecastSummaries = (await Promise.all(
        forecastDatastreams.slice(0, 3).map(ds => fetchForecastSummary(ds)),
      )).filter((forecast): forecast is ForecastSummary => !!forecast)
      const latestReadings = (await Promise.all(
        observationDatastreams.slice(0, 3).map(ds => fetchLatestReading(ds)),
      )).filter((reading): reading is LatestReadingSummary => !!reading)
      const trendSummaries = (await Promise.all(
        observationDatastreams
          .filter(ds => !isCameraDatastreamName(ds.name))
          .slice(0, 3)
          .map(ds => fetchTrendSummary(ds)),
      )).filter((trend): trend is TrendSummary => !!trend)
      const latestTime = latestReadings
        .map(reading => reading.phenomenonTime || reading.resultTime)
        .filter(Boolean)
        .sort((a, b) => new Date(b).getTime() - new Date(a).getTime())[0] || ''
      const lastRefreshTime = latestReadings
        .map(reading => reading.resultTime || reading.phenomenonTime)
        .filter(Boolean)
        .sort((a, b) => new Date(b).getTime() - new Date(a).getTime())[0] || ''

      const staleReadingCount = latestReadings.filter(reading => reading.freshnessState === 'stale').length
      const qualityValues = Array.from(new Set(latestReadings.map(reading => reading.quality).filter(Boolean)))

      // ── Resolve live camera image (BuoyCAM or NIMS) ──────────────
      let cameraImageUrl = ''
      let cameraTimestamp = ''
      let cameraLabel = ''
      let cameraThumbUrl = ''
      let cameraTimeLapseUrl = ''
      let cameraCamId = ''
      let cameraLastCheckedTime = ''
      let cameraLastCheckedRelative = ''
      let cameraImageChangedTime = ''
      let cameraImageChangedRelative = ''
      let cameraUnchangedDuration = ''
      let cameraStalenessStatus = ''
      let cameraImageChanged: boolean | null = null
      let cameraPlayerUrl = ''
      let cameraPageUrl = ''
      let cameraSourceUrl = ''
      let cameraAttributionText = ''
      let cameraLicenseUrl = ''
      let cameraLicenseLabel = ''
      const cameraDs = datastreams.find(ds => isCameraDatastreamName(ds.name))
      if (cameraDs) {
        const isBuoyCAM = /buoycam|buoy[\s_-]?cam/i.test(cameraDs.name)
        const isWeathercam = /weather[\s_-]?cam|weather\s+camera|digitraffic.*cam/i.test(cameraDs.name)
        cameraLabel = isBuoyCAM ? 'Live BuoyCAM' : isWeathercam ? 'Live Weathercam' : 'Live Camera'
        try {
          const obs = await fetchLatestObservation(cameraDs.id)
          const result = obs?.result || {}
          if ((result.imageUrl || result.latestImageUrl) && typeof result.mediaType === 'string' && result.mediaType.startsWith('image/')) {
            // Prefer imageUrl when it is an absolute URL; fall back to latestImageUrl
            // when imageUrl is a relative path (BUOYCAM_CACHE_BASE_URL not configured).
            cameraImageUrl = result.imageUrl?.startsWith('http') ? result.imageUrl : (result.latestImageUrl || result.imageUrl || '')
            cameraTimestamp = obs?.phenomenonTime || obs?.resultTime || ''
            // NIMS-specific fields
            cameraThumbUrl = result.thumbUrl || ''
            cameraTimeLapseUrl = result.timeLapseUrl || ''
            cameraCamId = result.camId || ''
            cameraLastCheckedTime = result.lastSeenTime || obs?.resultTime || obs?.phenomenonTime || ''
            cameraLastCheckedRelative = cameraLastCheckedTime ? relativeTime(cameraLastCheckedTime) : ''
            cameraImageChangedTime = result.lastChangedTime || obs?.phenomenonTime || obs?.resultTime || ''
            cameraImageChangedRelative = cameraImageChangedTime ? relativeTime(cameraImageChangedTime) : ''
            cameraTimestamp = cameraImageChangedTime || cameraTimestamp
            cameraUnchangedDuration = formatDurationSeconds(result.sourceAgeSeconds)
            cameraStalenessStatus = result.stalenessStatus || ''
            cameraImageChanged = typeof result.imageChanged === 'boolean' ? result.imageChanged : null
            cameraPlayerUrl = result.playerUrl || ''
            cameraPageUrl = result.pageUrl || ''
            cameraSourceUrl = result.sourceUrl || ''

            // SensorML/metadata-first: resolve license docs from datastream or system docs.
            const dsLicenseDoc = cameraDs.documentation.find(isLicenseLikeDoc)
            const smlLicenseDoc = smlDocs.find(isLicenseLikeDoc)
            const licenseDoc = dsLicenseDoc || smlLicenseDoc
            cameraLicenseUrl = normalizeLicenseUrl(licenseDoc?.href || '')
            cameraLicenseLabel = licenseDoc?.title || 'License terms'

            const operatorContact = contacts.find(c => /operator|owner|provider/i.test(c.role || ''))
            const operatorName = operatorContact?.org || operatorContact?.name || ''
            if (operatorName) {
              cameraAttributionText = `Source: ${operatorName}`
            } else if (cameraLicenseUrl) {
              cameraAttributionText = 'Source/license metadata from SensorML/CSAPI'
            }

            if (!cameraLicenseUrl) {
              const procedureMeta = await fetchCameraProcedureLicense(
                cameraDs,
                `${cameraSourceUrl} ${cameraPageUrl}`,
              )
              if (procedureMeta.licenseDoc) {
                cameraLicenseUrl = normalizeLicenseUrl(procedureMeta.licenseDoc.href)
                cameraLicenseLabel = procedureMeta.licenseDoc.title || 'License terms'
                if (!cameraAttributionText && procedureMeta.sourceName) {
                  cameraAttributionText = `Source: ${procedureMeta.sourceName}`
                }
                if (!cameraAttributionText) {
                  cameraAttributionText = 'Source/license metadata from SensorML/CSAPI'
                }
              }
            }
          }
        } catch { /* camera fetch optional */ }
      }
      // Backwards-compat aliases
      const buoycamImageUrl = cameraImageUrl
      const buoycamTimestamp = cameraTimestamp

      // ── Resolve control streams count ────────────────────────────
      let controlCount = 0
      if (systemId) {
        try {
          const csRes = await apiFetch(`/systems/${systemId}/controlstreams?limit=1`, {
            headers: { 'Accept': 'application/json' },
          })
          if (csRes.ok && csRes.data) {
            // csRes.data may have numberMatched or numberReturned or items
            controlCount = csRes.data.numberMatched ?? csRes.data.numberReturned ?? (csRes.data.items?.length || 0)
          }
        } catch { /* optional */ }
      }

      // ── Build parent deployment path ─────────────────────────────
      const deploymentPath = await buildDeploymentPath(
        deploymentId,
        deploymentName,
        itemById,
        parentMap,
      )

      const parentId = parentMap[deploymentId]
      const parentItem = parentId ? itemById[parentId] : null
      const parentDeploymentName = parentItem
        ? (parentItem.properties?.name || parentItem.name || parentId)
        : ''

      // ── Infer role, kind, status ─────────────────────────────────
      const inferredRole = inferRoleFromContext(props, systemSml, keywords, classifiers)
      const inferredKind = inferKindFromContext(classifiers, keywords, identifiers)
      const status = props.status || systemProps.status || identifiers['Status'] || 'Active Demo'

      // ── Infer purpose ────────────────────────────────────────────
      const purpose = inferPurpose(capabilities, keywords, smlDesc || systemDesc || deploymentDesc, inferredRole)

      // ── Owner / manufacturer ─────────────────────────────────────
      const ownerContact = contacts.find(c => /owner/i.test(c.role))
      const owner = ownerContact?.org || ownerContact?.name
        || identifiers['Owner'] || identifiers['owner']
        || ''

      const manufacturer = identifiers['Manufacturer'] || identifiers['manufacturer'] || ''
      const model = identifiers['Model'] || identifiers['model'] || ''
      const version = identifiers['Software Version'] || identifiers['softwareVersion']
        || identifiers['version'] || identifiers['Version'] || ''
      const mfgLine = manufacturer && model
        ? `${manufacturer} ${model}`
        : manufacturer || model || (version ? `v${version}` : '')

      // ── Product labels ───────────────────────────────────────────
      const productLabels = datastreams
        .map(ds => ds.productLabel || ds.name)
        .filter(Boolean)
        .slice(0, 3)

      // ── Cadence note ─────────────────────────────────────────────
      // Infer cadence from capabilities or keywords
      let cadenceNote = ''
      let refreshCadence = ''
      const cadenceCap = metadataValue(capabilities, [
        'Publish Interval',
        'Update Interval',
        'Update Rate',
        'Refresh Rate',
        'Refresh Interval',
        'Sampling Rate',
        'Reporting Rate',
        'Cadence',
      ])
      if (cadenceCap) {
        refreshCadence = formatCadenceValue(cadenceCap)
        cadenceNote = `Cadence: ${refreshCadence}`
      } else if (keywords.some(k => /event[- ]?driven/i.test(k)) || smlDesc?.toLowerCase().includes('event-driven')) {
        refreshCadence = 'Event-driven'
        cadenceNote = 'Event-driven'
      } else if (keywords.some(k => /real[- ]?time/i.test(k))) {
        refreshCadence = 'Near-real-time'
        cadenceNote = 'Near-real-time'
      }

      // ── Method summary ───────────────────────────────────────────
      let methodSummary = ''
      if (procedures.length > 0) {
        methodSummary = procedures[0]!.name || procedures[0]!.description || ''
        if (methodSummary && methodSummary.length > 40) {
          methodSummary = methodSummary.substring(0, 37) + '…'
        }
        if (methodSummary) methodSummary = `Method: ${methodSummary}`
      }

      // ── STANAG symbol ──────────────────────────────────────────────
      const stanagResult = getSymbolForResource('deployments', rawData, 'normal')
      const stanagSvg = stanagResult?.svgDataUrl || ''
      const representativeThumbnail = representativeThumbnailForCard(rawData, deploymentName, systemName, keywords)

      // ── Capabilities chips ───────────────────────────────────────
      const capChips: string[] = []
      for (const [label, val] of Object.entries(capabilities)) {
        capChips.push(`${label}: ${val}`)
      }

      // ── Build card model ─────────────────────────────────────────
      card.value = {
        cardType: 'deployed-system-card',

        // Header
        title: deploymentName,
        subtitle: systemName !== deploymentName ? systemName : (normalizeLabel(inferredRole, ROLE_LABELS) || ''),
        roleBadge: normalizeLabel(inferredRole, ROLE_LABELS) || 'Deployed System',
        statusBadge: normalizeLabel(status, {}) || 'Unknown Status',
        kindBadge: normalizeLabel(inferredKind, KIND_LABELS) || '',
        thumbnail: representativeThumbnail || (smlMedia.length > 0 ? smlMedia[0]!.href : ''),
        stanagSvg,

        // Summary
        summarySentence: buildSummarySentence(
          normalizeLabel(inferredRole, ROLE_LABELS),
          parentDeploymentName,
          purpose,
        ),

        // Context
        deploymentPath,
        parentDeployment: parentDeploymentName,
        deploymentType: classifiers['deploymentType'] || classifiers['intendedApplication'] || '',
        geometrySummary: summarizeGeometry(rawData),
        validState: status,

        // Occupant
        occupantName: systemName || 'Unknown Occupant',
        occupantUid: systemUid,
        occupantKind: normalizeLabel(inferredKind, KIND_LABELS) || 'Unknown Kind',
        manufacturerModelOrVersion: mfgLine,
        ownerMaintainer: owner,

        // Outputs & Methods
        primaryPurpose: purpose || 'Purpose not documented',
        capabilities: capChips.slice(0, 3),
        primaryDatastreams: datastreams.slice(0, 3),
        latestReadings,
        forecastSummaries,
        trendSummaries,
        productLabels,
        latestActivityTime: latestTime || '',
        latestActivityRelative: latestTime ? relativeTime(latestTime) : 'No recent activity',
        lastRefreshTime,
        lastRefreshRelative: lastRefreshTime ? relativeTime(lastRefreshTime) : '',
        refreshCadence,
        cadenceNote,
        controlStreamCount: controlCount,
        primaryProcedures: procedures.slice(0, 2),
        methodSummary,
        keyAssumptions: [],

        // Freshness / Trust
        qualitySummary: qualityValues.slice(0, 2).join(', '),
        healthState: staleReadingCount ? `${staleReadingCount} stale reading${staleReadingCount === 1 ? '' : 's'}` : '',
        contributingSources: '',

        // Media / References
        docsLinks: smlDocs.filter(d => !smlMedia.some(m => m.href === d.href)),
        mediaLinks: smlMedia.slice(1), // first one is thumbnail

        // Live Camera
        cameraImageUrl,
        cameraTimestamp,
        cameraLabel,
        cameraThumbUrl,
        cameraTimeLapseUrl,
        cameraCamId,
        cameraLastCheckedTime,
        cameraLastCheckedRelative,
        cameraImageChangedTime,
        cameraImageChangedRelative,
        cameraUnchangedDuration,
        cameraStalenessStatus,
        cameraImageChanged,
        cameraPlayerUrl,
        cameraPageUrl,
        cameraSourceUrl,
        cameraAttributionText,
        cameraLicenseUrl,
        cameraLicenseLabel,
        buoycamImageUrl,
        buoycamTimestamp,

        // Advanced IDs
        advancedDeploymentUid: deploymentUid,
        advancedSystemUid: systemUid,
        advancedDeploymentId: deploymentId,
        advancedSystemId: systemId,
        advancedBootstrapOwner: identifiers['Bootstrap Owner'] || identifiers['bootstrapOwner'] || '',
        advancedSourceOfTruth: identifiers['Source of Truth'] || identifiers['sourceOfTruth'] || '',
      }
    } catch (e: any) {
      error.value = e?.message || 'Failed to compose card'
      card.value = null
    } finally {
      loading.value = false
    }
  }

  /**
   * Clear the card state.
   */
  function clearCard() {
    card.value = null
    error.value = ''
  }

  return {
    loading,
    card,
    error,
    isDeployedSystemLeaf,
    composeCard,
    clearCard,
  }
}
