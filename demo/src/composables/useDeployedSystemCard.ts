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
  productLabels: string[]
  latestActivityTime: string
  latestActivityRelative: string
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
  if (text.includes('uk-air') || text.includes('uk air')) {
    if (text.includes('camden') || text.includes('roadside') || text.includes('kerbside')) {
      return UK_AIR_ROADSIDE_REPRESENTATIVE_IMAGE
    }
    return UK_AIR_BACKGROUND_REPRESENTATIVE_IMAGE
  }
  return ''
}

// ─── Role/kind/status vocabulary normalization ─────────────────────────────

const ROLE_LABELS: Record<string, string> = {
  'air-quality-site': 'Air Quality Site',
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

const RESULT_METADATA_KEYS = new Set([
  'stationId', 'stationName', 'measureId', 'parameter', 'unit', 'valueType',
  'quality', 'completeness', 'sourceUrl', 'lat', 'lon', 'alt', 'latitude', 'longitude',
  'imageUrl', 'latestImageUrl', 'thumbUrl', 'mediaType', 'contentLength', 'camId',
])

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
  const unit = String(result?.unit || '').toLowerCase()
  if (parameter === 'rainfall' || valueKey.toLowerCase().includes('rainfall')) return 'Rainfall'
  if (parameter === 'flow' || valueKey.toLowerCase().includes('flow')) return 'River flow'
  if (parameter === 'level' && unit === 'maod') return 'Groundwater level'
  if (parameter === 'level' || valueKey.toLowerCase().includes('level')) return 'River level'
  return ds.productLabel || ds.name || valueKey.replace(/_/g, ' ')
}

function summarizeLatestReading(ds: DatastreamSummary, obs: any): LatestReadingSummary | null {
  const result = obs?.result || {}
  if (!result || typeof result !== 'object') return null

  const entries = Object.entries(result).filter(([key, value]) =>
    !RESULT_METADATA_KEYS.has(key)
    && value !== null
    && value !== undefined
    && (typeof value === 'number' || typeof value === 'string')
  )
  const valueEntry = entries.find(([, value]) => typeof value === 'number') || entries[0]
  if (!valueEntry) return null

  const [valueKey, value] = valueEntry
  const unit = result.unit || ''
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
    let latestRes = await apiFetch(
      `/datastreams/${ds.id}/observations?limit=1&resultTime=latest`,
      { headers: { 'Accept': 'application/json' } },
    )
    if (latestRes.ok && latestRes.data && !(latestRes.data.items?.length || (Array.isArray(latestRes.data) && latestRes.data.length))) {
      latestRes = await apiFetch(
        `/datastreams/${ds.id}/observations?limit=1`,
        { headers: { 'Accept': 'application/json' } },
      )
    }
    if (!latestRes.ok || !latestRes.data) return null
    const items = latestRes.data.items || latestRes.data || []
    if (!Array.isArray(items) || items.length === 0) return null
    return summarizeLatestReading(ds, items[0])
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
  if (/uk[- ]air|air quality|air pollution|pollutant|\bno2\b|\bpm10\b|pm2\.5|ozone/.test(contextText)) {
    return 'Air Quality Site'
  }
  if (kwStr.includes('acoustic') && kwStr.includes('sensor')) return 'Acoustic Sensor Node'
  if (kwStr.includes('localizer') || kwStr.includes('fusion')) return 'Software Fusion Agent'
  if (kwStr.includes('relay') || kwStr.includes('communications')) return 'Communications Relay'
  if (kwStr.includes('monitoring') || kwStr.includes('dissemination')) return 'Monitoring Site'
  if (kwStr.includes('senrep') || kwStr.includes('human') || kwStr.includes('team')) return 'Sensor Exploitation Team'
  if (kwStr.includes('orbit') || kwStr.includes('satellite') || kwStr.includes('iss')) return 'Orbit Feed'

  // Try description
  const desc = (extractSmlDescription(systemSml) || deploymentProps?.description || '').toLowerCase()
  if (/uk[- ]air|air quality|air pollution|pollutant|\bno2\b|\bpm10\b|pm2\.5|ozone/.test(desc)) {
    return 'Air Quality Site'
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
              })
            }
          }
        } catch { /* datastream fetch optional */ }
      }

      // ── Resolve procedures ───────────────────────────────────────
      const procedures: ProcedureSummary[] = []
      if (systemId) {
        try {
          const procRes = await apiFetch(`/systems/${systemId}/procedures?limit=5`, {
            headers: { 'Accept': 'application/json' },
          })
          if (procRes.ok && procRes.data) {
            const procList = procRes.data.items || procRes.data || []
            for (const p of (Array.isArray(procList) ? procList : [])) {
              procedures.push({
                id: p.id || '',
                name: p.name || p.label || '',
                description: p.description || '',
                uid: p.uid || p.properties?.uid || '',
              })
            }
          }
        } catch { /* procedure fetch optional */ }
      }

      // ── Resolve latest observation summaries ─────────────────────
      const latestReadings = (await Promise.all(
        datastreams.slice(0, 3).map(ds => fetchLatestReading(ds)),
      )).filter((reading): reading is LatestReadingSummary => !!reading)
      const latestTime = latestReadings
        .map(reading => reading.phenomenonTime || reading.resultTime)
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
      const cameraDs = datastreams.find(ds =>
        /buoycam|buoy[\s_-]?cam|camera|nims.*image|station.*image/i.test(ds.name)
      )
      if (cameraDs) {
        const isBuoyCAM = /buoycam|buoy[\s_-]?cam/i.test(cameraDs.name)
        cameraLabel = isBuoyCAM ? 'Live BuoyCAM' : 'Live Camera'
        try {
          let camRes = await apiFetch(
            `/datastreams/${cameraDs.id}/observations?limit=1&resultTime=latest`,
            { headers: { 'Accept': 'application/json' } },
          )
          // Fallback: Go CSAPI server ignores resultTime=latest
          if (camRes.ok && camRes.data && !(camRes.data.items?.length || (Array.isArray(camRes.data) && camRes.data.length))) {
            camRes = await apiFetch(
              `/datastreams/${cameraDs.id}/observations?limit=1`,
              { headers: { 'Accept': 'application/json' } },
            )
          }
          if (camRes.ok && camRes.data) {
            const camItems = camRes.data.items || camRes.data || []
            if (Array.isArray(camItems) && camItems.length > 0) {
              const obs = camItems[0]
              const result = obs.result || {}
              if ((result.imageUrl || result.latestImageUrl) && typeof result.mediaType === 'string' && result.mediaType.startsWith('image/')) {
                // Prefer imageUrl when it is an absolute URL; fall back to latestImageUrl
                // when imageUrl is a relative path (BUOYCAM_CACHE_BASE_URL not configured).
                cameraImageUrl = result.imageUrl?.startsWith('http') ? result.imageUrl : (result.latestImageUrl || result.imageUrl || '')
                cameraTimestamp = obs.phenomenonTime || obs.resultTime || ''
                // NIMS-specific fields
                cameraThumbUrl = result.thumbUrl || ''
                cameraTimeLapseUrl = result.timeLapseUrl || ''
                cameraCamId = result.camId || ''
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
      const cadenceCap = capabilities['Update Rate'] || capabilities['updateRate']
        || capabilities['Sampling Rate'] || capabilities['samplingRate']
        || capabilities['Reporting Rate'] || capabilities['reportingRate'] || ''
      if (cadenceCap) {
        cadenceNote = `Cadence: ${cadenceCap}`
      } else if (keywords.some(k => /event[- ]?driven/i.test(k)) || smlDesc?.toLowerCase().includes('event-driven')) {
        cadenceNote = 'Event-driven'
      } else if (keywords.some(k => /real[- ]?time/i.test(k))) {
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
        thumbnail: smlMedia.length > 0 ? smlMedia[0]!.href : representativeThumbnail,
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
        productLabels,
        latestActivityTime: latestTime || '',
        latestActivityRelative: latestTime ? relativeTime(latestTime) : 'No recent activity',
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
