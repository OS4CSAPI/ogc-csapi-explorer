<script setup lang="ts">
import { ref, watch, computed, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { apiFetch } from '../api'
import { getDetailUrl, getContentType, getNestedListUrl, parseCollectionResponse } from '../csapi-bridge'
import { RELATED_RESOURCES, getResourceType, parentSystemCache, cacheParentForChildren } from '../state'
import type { RelatedResourceLink } from '../state'
import type { QueryOptions } from '@csapi/ogc-api/csapi/model'
import type { DateTimeParameter } from '@csapi/shared/models'
import { CommandStatusCodes } from '@csapi/ogc-api/csapi/model'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import DatePicker from 'primevue/datepicker'
import Select from 'primevue/select'
import Message from 'primevue/message'
import ProgressSpinner from 'primevue/progressspinner'
import SweSchemaDisplay from './SweSchemaDisplay.vue'
import ParsedResourceView from './ParsedResourceView.vue'
import DataModelDiagram from './DataModelDiagram.vue'
import SensorMLDisplay from './SensorMLDisplay.vue'

const router = useRouter()

const props = defineProps<{
  resourceType: string
  resourceId: string | null
  resource: any | null
  /** Parent type from nested navigation context (e.g., 'systems' when viewing samplingFeatures under a system) */
  nestedParentType?: string | null
  /** Parent ID from nested navigation context */
  nestedParentId?: string | null
}>()

const emit = defineEmits<{
  /** Notify parent when in-place navigation changes the viewed resource */
  (e: 'selectResource', id: string): void
}>()

const manualId = ref('')
const loading = ref(false)
const error = ref('')
const errorSeverity = ref<'error' | 'warn'>('error')
const detail = ref<any>(null)

/**
 * When the user clicks a same-type related item (e.g. subsystem),
 * store the current detail as the "in-place parent" so we can
 * render a back-link to it in parentLinks.
 */
const inPlaceParent = ref<{ id: string; name: string; resourceType: string } | null>(null)

/** Guard: when true, the next props.resourceId watcher invocation came from
 *  an in-place drill-down (viewRelatedItem) and should NOT clear inPlaceParent
 *  or re-fetch (fetchDetail was already called directly). */
let _inPlaceNavActive = false

/** SensorML metadata fetched separately for systems (keywords, identifiers, etc.) */
const smlMeta = ref<any>(null)

/** True when viewing a system — triggers SensorML metadata fetch */
const isSystem = computed(() => props.resourceType === 'systems')

/** True when viewing a datastream — triggers schema display */
const isDatastream = computed(() => props.resourceType === 'datastreams')
/** True when viewing a control stream — triggers command schema display */
const isControlStream = computed(() => props.resourceType === 'controlStreams')
/** True when viewing a procedure — triggers SensorML display */
const isProcedure = computed(() => props.resourceType === 'procedures')
const effectiveId = computed(() => detail.value?.id || props.resourceId || '')

// ========================================
// Unified inline related resource panels
// ========================================

/** All relation links for the current resource type (includes subsystems, datastreams, etc.) */
const allRelations = computed<RelatedResourceLink[]>(() => {
  return RELATED_RESOURCES[props.resourceType] || []
})

/** Per-relation reactive state: items, loading, error, expanded, filters */
interface RelationState {
  items: any[]
  loading: boolean
  error: string
  expanded: boolean
  /** Whether the filter row is visible (progressive disclosure) */
  filtersOpen: boolean
  /** Free-text keyword filter */
  q: string
  /** Temporal filter start */
  dtStart: Date | null
  /** Temporal filter end */
  dtEnd: Date | null
  /** Command status filter (commands only) */
  currentStatus: string
  /** Client-side fallback diagnostic messages (empty = server handled it) */
  clientSideFallbackDetails: string[]
}
const relationStates = reactive<Record<string, RelationState>>({})

function getRelState(relation: string): RelationState {
  if (!relationStates[relation]) {
    relationStates[relation] = {
      items: [], loading: false, error: '', expanded: true,
      filtersOpen: false, q: '', dtStart: null, dtEnd: null, currentStatus: '',
      clientSideFallbackDetails: [],
    }
  }
  return relationStates[relation]
}

/** Command status options for the dropdown */
const commandStatusOptions = CommandStatusCodes.map(s => ({ label: s, value: s }))

/**
 * Apply the temporal filter to the correct query option for the child resource type.
 * Observations & datastreams → phenomenonTime, commands → issueTime, others → datetime.
 */
function applyTemporalFilter(options: Record<string, any>, childType: string, dt: DateTimeParameter) {
  switch (childType) {
    case 'observations':
    case 'datastreams':
      options.phenomenonTime = dt
      break
    case 'commands':
      options.issueTime = dt
      break
    default:
      options.datetime = dt
      break
  }
}

/** Get the temporal param name for display in the filter hint */
function temporalParamName(childType: string): string {
  switch (childType) {
    case 'observations':
    case 'datastreams': return 'phenomenonTime'
    case 'commands': return 'issueTime'
    default: return 'datetime'
  }
}

/** Build a DateTimeParameter from a relation's date picker state */
function buildDatetimeParam(state: RelationState): DateTimeParameter | null {
  if (state.dtStart && state.dtEnd) return { start: state.dtStart, end: state.dtEnd }
  if (state.dtStart) return { start: state.dtStart }
  if (state.dtEnd) return { end: state.dtEnd }
  return null
}

/** Whether a given child type supports temporal filtering */
function supportsTemporalFilter(childType: string): boolean {
  return ['observations', 'datastreams', 'commands', 'systems', 'deployments'].includes(childType)
}

/** Whether a given child type supports command status filtering */
function supportsStatusFilter(childType: string): boolean {
  return childType === 'commands'
}

/** Whether a given child type supports text search (q) */
function supportsKeywordFilter(_childType: string): boolean {
  return true // All CSAPI collections support ?q
}

/** True if any filter is active for this relation */
function hasActiveFilters(state: RelationState, childType: string): boolean {
  if (state.q) return true
  if (state.dtStart || state.dtEnd) return true
  if (supportsStatusFilter(childType) && state.currentStatus) return true
  return false
}

/** Clear all filters for a relation and re-fetch */
function clearFilters(link: RelatedResourceLink) {
  const state = getRelState(link.relation)
  state.q = ''
  state.dtStart = null
  state.dtEnd = null
  state.currentStatus = ''
  const parentId = detail.value?.id || props.resourceId
  if (parentId) fetchRelation(link, String(parentId))
}

/**
 * Normalize an @link href to an API-relative path suitable for apiFetch().
 *
 * OSH SensorHub may return hrefs in several forms:
 *  - Absolute URL: "https://host/sensorhub/api/systems/0420"
 *  - Root-relative:  "/sensorhub/api/systems/0420"
 *  - API-relative:   "/systems/0420"
 *
 * apiFetch() prepends the proxy base URL (connection.baseUrl), so it expects
 * only the API-relative portion (e.g. "/systems/0420").  This helper strips
 * everything up to and including the "/api" segment in the path.
 */
function normalizeLinkHref(href: string, collection?: string): string {
  if (!href) return href
  // Bare ID (no slashes) — prefix with the expected collection path.
  // OSH SensorHub returns platform@link.href as "0520" instead of "/systems/0520".
  if (!href.includes('/') && collection) {
    return `/${collection}/${href}`
  }
  // Absolute URL → extract pathname
  if (href.startsWith('http')) {
    try {
      href = new URL(href).pathname
    } catch { /* keep as-is */ }
  }
  // Strip everything up to and including "/api" (e.g. "/sensorhub/api/systems/0420" → "/systems/0420")
  const apiIdx = href.indexOf('/api/')
  if (apiIdx !== -1) return href.substring(apiIdx + 4)
  // If path just starts with /api (no trailing slash), treat similarly
  if (href.startsWith('/api')) return href.substring(4)
  return href
}

/**
 * @link fallback: When the server doesn't implement a nested navigation endpoint
 * (e.g. /systems/{id}/procedures returns 400), try to resolve related resources
 * from @link fields embedded in the parent or by searching the collection.
 *
 * Supported fallbacks:
 *  - systems → procedures: follow systemKind@link href to fetch the procedure
 *  - systems → deployments: search /deployments and filter by platform@link.href
 *  - deployments → systems: follow deployedSystems@link hrefs to fetch each system
 */
async function tryLinkFallback(link: RelatedResourceLink, parentId: string): Promise<any[]> {
  const parentProps = detail.value?.properties || detail.value || {}

  // ----- System → Procedure via systemKind@link -----
  if (props.resourceType === 'systems' && link.relation === 'procedures') {
    const skLink = parentProps['systemKind@link']
    if (skLink?.href) {
      try {
        const acceptType = getContentType('procedures')
        // href may be absolute URL or root-relative — normalize to API-relative
        const path = normalizeLinkHref(skLink.href, 'procedures')
        const res = await apiFetch(path, { headers: { 'Accept': acceptType } })
        if (res.ok && res.data) {
          return [res.data]
        }
      } catch { /* fallback failed silently */ }
    }
  }

  // ----- System → Deployments via searching all deployments (incl. nested) -----
  if (props.resourceType === 'systems' && link.relation === 'deployments') {
    try {
      const acceptType = getContentType('deployments')
      const systemUrl = `systems/${parentId}`
      const systemUid = parentProps.uid || ''

      // Helpers: classify how a deployment references this system.
      // "Strong" = platform@link or deployedSystems@link (resolvable href, 1:1).
      // "Weak"   = deployedSystemUIDs (UID string, many-to-one, no direct link).
      // If any strong matches exist we return only those, avoiding duplicates
      // from parent deployments that also list the system via UIDs.
      const hasStrongLink = (dep: any): boolean => {
        const dp = dep?.properties || dep || {}
        const platformLink = dp['platform@link']
        if (platformLink?.href) {
          // Match full path ("systems/0520") or bare ID ("0520")
          if (platformLink.href.includes(systemUrl) || platformLink.href === parentId) return true
        }
        const dsLinks = dp['deployedSystems@link']
        if (Array.isArray(dsLinks) && dsLinks.some((l: any) => l?.href && (l.href.includes(systemUrl) || l.href === parentId))) return true
        return false
      }
      const hasWeakLink = (dep: any): boolean => {
        const dp = dep?.properties || dep || {}
        const dsUIDs = dp.deployedSystemUIDs || ''
        if (systemUid && dsUIDs.split(',').map((s: string) => s.trim()).includes(systemUid)) return true
        return false
      }
      const matchesSys = (dep: any): boolean => hasStrongLink(dep) || hasWeakLink(dep)

      // Recursively fetch subdeployments up to depth 5
      const fetchSubdeployments = async (depId: string, depth: number): Promise<any[]> => {
        if (depth > 8) return []
        try {
          const subRes = await apiFetch(`/deployments/${depId}/subdeployments?limit=100`, { headers: { 'Accept': acceptType } })
          if (!subRes.ok || !subRes.data) return []
          const subParsed = parseCollectionResponse(subRes.data)
          const subs = subParsed.items as any[]
          const nested: any[] = []
          for (const sub of subs) {
            const subId = sub?.id || sub?.properties?.id
            if (subId) nested.push(...await fetchSubdeployments(String(subId), depth + 1))
          }
          return [...subs, ...nested]
        } catch { return [] }
      }

      // Fetch top-level deployments + all nested
      const res = await apiFetch('/deployments?limit=100', { headers: { 'Accept': acceptType } })
      if (res.ok && res.data) {
        const parsed = parseCollectionResponse(res.data)
        const topLevel = parsed.items as any[]
        const allDeps = [...topLevel]
        for (const dep of topLevel) {
          const depId = dep?.id || dep?.properties?.id
          if (depId) allDeps.push(...await fetchSubdeployments(String(depId), 1))
        }
        const strong = allDeps.filter(hasStrongLink)
        if (strong.length > 0) return strong
        // Fall back to weak (deployedSystemUIDs) only if no strong link exists
        const matched = allDeps.filter(hasWeakLink)
        if (matched.length > 0) return matched
      }
    } catch { /* fallback failed silently */ }
  }

  // ----- Deployment → Systems via deployedSystems@link -----
  if (props.resourceType === 'deployments' && link.relation === 'systems') {
    const dsLinks = parentProps['deployedSystems@link']
    if (Array.isArray(dsLinks) && dsLinks.length > 0) {
      const items: any[] = []
      for (const l of dsLinks) {
        if (!l?.href) continue
        try {
          const path = normalizeLinkHref(l.href, 'systems')
          const acceptType = getContentType('systems')
          const res = await apiFetch(path, { headers: { 'Accept': acceptType } })
          if (res.ok && res.data) items.push(res.data)
        } catch { /* skip failed links */ }
      }
      if (items.length > 0) return items
    }
  }

  // ----- Procedure → Systems via systemKind@link reverse search -----
  if (props.resourceType === 'procedures' && link.relation === 'systems') {
    try {
      const acceptType = getContentType('systems')
      const res = await apiFetch('/systems?limit=100', { headers: { 'Accept': acceptType } })
      if (res.ok && res.data) {
        const parsed = parseCollectionResponse(res.data)
        const procUrl = `procedures/${parentId}`
        const matched = (parsed.items as any[]).filter((sys: any) => {
          const props = sys?.properties || sys || {}
          const skLink = props['systemKind@link']
          return skLink?.href && skLink.href.includes(procUrl)
        })
        if (matched.length > 0) return matched
      }
    } catch { /* fallback failed silently */ }
  }

  return []
}

/**
 * Resolve deployed systems from inline deployment properties.
 * Per OGC 23-001 Table 43, deployedSystems maps to properties/deployedSystems@link
 * (a JSON Array of links), NOT to a sub-resource endpoint.
 * Falls back to platform@link when deployedSystems@link is absent.
 */
async function resolveDeployedSystemsInline(): Promise<{ items: any[]; source: string }> {
  const parentProps = detail.value?.properties || detail.value || {}
  const acceptType = getContentType('systems')

  // 1. Try deployedSystems@link — the standard-defined inline property
  const dsLinks = parentProps['deployedSystems@link']
  if (Array.isArray(dsLinks) && dsLinks.length > 0) {
    const items: any[] = []
    for (const l of dsLinks) {
      if (!l?.href) continue
      try {
        const path = normalizeLinkHref(l.href, 'systems')
        const res = await apiFetch(path, { headers: { Accept: acceptType } })
        if (res.ok && res.data && typeof res.data === 'object') items.push(res.data)
      } catch { /* skip broken links */ }
    }
    if (items.length > 0) {
      return { items, source: `Resolved ${items.length} system(s) from inline deployedSystems@link` }
    }
  }

  // 2. Fallback: resolve platform@link
  // platform@link identifies the platform system hosting the deployment.
  // Not identical to deployedSystems per SOSA, but useful when the server
  // doesn't persist deployedSystems@link.
  const platformLink = parentProps['platform@link']
  if (platformLink?.href) {
    try {
      const path = normalizeLinkHref(platformLink.href, 'systems')
      const res = await apiFetch(path, { headers: { Accept: acceptType } })
      if (res.ok && res.data && typeof res.data === 'object') {
        return {
          items: [res.data],
          source: 'Server does not provide deployedSystems@link — resolved platform system via platform@link',
        }
      }
    } catch { /* skip */ }
  }

  // 3. Fallback: resolve from deployedSystemUIDs string property
  // When the server strips deployedSystems@link (OSH SensorHub treats it as
  // computed/read-only), a comma-separated UID string stored as a custom
  // property can be used to find systems by UID.
  const uidStr = parentProps['deployedSystemUIDs']
  if (typeof uidStr === 'string' && uidStr.length > 0) {
    const uids = uidStr.split(',').map((u: string) => u.trim()).filter(Boolean)
    if (uids.length > 0) {
      const items: any[] = []
      for (const uid of uids) {
        try {
          const searchPath = `/systems?uid=${encodeURIComponent(uid)}&limit=1`
          const res = await apiFetch(searchPath, { headers: { Accept: acceptType } })
          if (res.ok && res.data) {
            const found = res.data?.items || res.data?.features || []
            if (found.length > 0) items.push(found[0])
          }
        } catch { /* skip */ }
      }
      if (items.length > 0) {
        return {
          items,
          source: `Resolved ${items.length} system(s) from deployedSystemUIDs property`,
        }
      }
    }
  }

  return { items: [], source: '' }
}

/** Fetch a single related resource collection (with filters and client-side fallback) */
async function fetchRelation(link: RelatedResourceLink, parentId: string) {
  const state = getRelState(link.relation)
  state.loading = true
  state.error = ''
  state.items = []
  state.clientSideFallbackDetails = []

  try {
    // Build query options from current filter state
    const options: QueryOptions = { limit: 20 }
    if (state.q) options.q = state.q
    const dtParam = buildDatetimeParam(state)
    if (dtParam) applyTemporalFilter(options, link.childType, dtParam)
    if (supportsStatusFilter(link.childType) && state.currentStatus) {
      ;(options as any).currentStatus = state.currentStatus
    }

    // --- OGC 23-001 Table 43: deployedSystems is an inline property ---
    // The standard maps deployedSystems to properties/deployedSystems@link,
    // not to a sub-resource endpoint. Resolve from inline properties first.
    if (props.resourceType === 'deployments' && link.relation === 'systems' && detail.value) {
      const inlineResult = await resolveDeployedSystemsInline()
      if (inlineResult.items.length > 0) {
        state.items = inlineResult.items
        state.clientSideFallbackDetails.push(inlineResult.source)
        state.loading = false
        return
      }
    }

    const path = getNestedListUrl(props.resourceType, parentId, link.relation, options)
    const acceptType = getContentType(link.childType)
    const res = await apiFetch(path, { headers: { 'Accept': acceptType } })

    if (!res.ok) {
      if (res.status !== 404 && res.status !== 400) {
        state.error = res.error || 'Failed to fetch'
      }
      // --- @link fallback: when server returns 400 (endpoint not implemented),
      // attempt to populate the panel from @link fields in the parent resource.
      // This handles OSH SensorHub which doesn't implement /systems/{id}/procedures
      // or /systems/{id}/deployments navigation endpoints. ---
      if (res.status === 400 && detail.value) {
        const fallbackItems = await tryLinkFallback(link, parentId)
        if (fallbackItems.length > 0) {
          state.items = fallbackItems
          state.clientSideFallbackDetails.push(
            `Server returned 400 for /${link.relation} endpoint — resolved ${fallbackItems.length} item(s) via @link fields`
          )
        }
      }
      return
    }

    try {
      const parsed = parseCollectionResponse(res.data)
      let resultItems = parsed.items as any[]

      // --- Subdeployments fallback ---
      // Some servers (e.g. OSH SensorHub) return 200 with empty items for
      // /deployments/{id}/subdeployments even though subdeployments exist.
      // The server may support the collection-level `parent` query parameter
      // instead.  Try deployments?parent={id} as a fallback.
      // CAVEAT: Some servers ignore the ?parent= value entirely and return
      // ALL deployments that have any parent.  We detect this with a probe:
      // query ?parent=<nonsense>&limit=1 — if it returns items, the filter
      // is a no-op and the results are unreliable.
      if (resultItems.length === 0
          && props.resourceType === 'deployments'
          && link.relation === 'subdeployments') {
        try {
          // Probe: test if ?parent= filter actually works
          const probeAccept = getContentType('deployments')
          const probeRes = await apiFetch('/deployments?parent=__csapi_probe__&limit=1', { headers: { Accept: probeAccept } })
          const probeItems = probeRes.ok
            ? (parseCollectionResponse(probeRes.data).items as any[])
            : []
          if (probeItems.length === 0) {
            // Filter appears functional — proceed with real query
            const fallbackPath = `/deployments?parent=${encodeURIComponent(parentId)}`
            const fbAccept = getContentType('deployments')
            const fbRes = await apiFetch(fallbackPath, { headers: { Accept: fbAccept } })
            if (fbRes.ok && fbRes.data) {
              const fbParsed = parseCollectionResponse(fbRes.data)
              const fbItems = (fbParsed.items as any[]).filter((it: any) => {
                const id = it?.id || it?.properties?.id
                return id && String(id) !== String(parentId)
              })
              if (fbItems.length > 0) {
                resultItems = fbItems
                state.clientSideFallbackDetails.push(
                  `/subdeployments returned 0 — resolved ${fbItems.length} item(s) via deployments?parent=${parentId}`
                )
              }
            }
          }
        } catch { /* non-critical */ }
      }

      // --- Client-side fallback for servers that ignore query parameters ---

      // 1) Keyword filter fallback
      if (state.q && resultItems.length > 0) {
        const keyword = state.q.toLowerCase()
        const filtered = resultItems.filter((item: any) => {
          const fields = [
            item?.id,
            item?.properties?.name,
            item?.properties?.title,
            item?.properties?.description,
            item?.properties?.uniqueId,
            item?.name,
            item?.title,
            item?.description,
          ]
          return fields.some(f => typeof f === 'string' && f.toLowerCase().includes(keyword))
        })
        if (filtered.length < resultItems.length) {
          const serverCount = resultItems.length
          resultItems = filtered
          state.clientSideFallbackDetails.push(
            `q="${state.q}": server returned ${serverCount} items unfiltered — reduced to ${filtered.length} client-side`
          )
        }
      }

      // 2) Temporal filter fallback — check result times against requested range
      if (dtParam && resultItems.length > 0) {
        const paramName = temporalParamName(link.childType)
        const before = resultItems.length
        resultItems = resultItems.filter((item: any) => {
          // Try to extract the item's time from known field names
          const raw = item?.properties || item
          const timeStr = raw?.phenomenonTime || raw?.resultTime || raw?.issueTime || raw?.executionTime || raw?.validTime
          if (!timeStr) return true // Can't verify — keep item
          try {
            const itemDate = new Date(typeof timeStr === 'string' ? timeStr : timeStr.start || timeStr)
            if ((dtParam as any).start && itemDate < (dtParam as any).start) return false
            if ((dtParam as any).end && itemDate > (dtParam as any).end) return false
          } catch { return true }
          return true
        })
        if (resultItems.length < before) {
          state.clientSideFallbackDetails.push(
            `${paramName}: server returned ${before} items ignoring temporal filter — reduced to ${resultItems.length} client-side`
          )
        }
      }

      // 3) Command status filter fallback
      if (supportsStatusFilter(link.childType) && state.currentStatus && resultItems.length > 0) {
        const before = resultItems.length
        resultItems = resultItems.filter((item: any) => {
          const raw = item?.properties || item
          const status = raw?.currentStatus || raw?.statusCode
          if (!status) return true // Can't verify — keep
          return status === state.currentStatus
        })
        if (resultItems.length < before) {
          state.clientSideFallbackDetails.push(
            `currentStatus="${state.currentStatus}": server returned ${before} items unfiltered — reduced to ${resultItems.length} client-side`
          )
        }
      }

      // Filter out the current resource and its known parents from
      // self-hierarchy relations (subdeployments / subsystems).
      // Some servers return the viewed resource or its ancestors in
      // the children list.
      if (link.childType === props.resourceType && resultItems.length > 0) {
        const selfId = String(detail.value?.id || detail.value?.properties?.id || props.resourceId || '')
        // Collect parent IDs from rel="parent" links in the current resource
        const parentIds = new Set<string>()
        if (Array.isArray(detail.value?.links)) {
          for (const lnk of detail.value.links) {
            if (lnk?.rel === 'parent' && typeof lnk.href === 'string') {
              const m = lnk.href.match(/\/(systems|deployments)\/([^/?]+)/)
              if (m) parentIds.add(m[2])
            }
          }
        }
        resultItems = resultItems.filter((it: any) => {
          const itemId = String(it?.id || it?.properties?.id || '')
          if (selfId && itemId === selfId) return false   // exclude self
          if (parentIds.has(itemId)) return false          // exclude parent
          return true
        })
      }

      state.items = resultItems

      // Populate the global parent cache when fetching subsystems.
      // This allows parent breadcrumbs to survive component recreation.
      if (link.relation === 'subsystems' && link.childType === props.resourceType && resultItems.length > 0) {
        const curId = String(detail.value?.id || props.resourceId || '')
        const curName = detail.value?.properties?.name || detail.value?.name || curId
        if (curId) {
          cacheParentForChildren(
            curId,
            curName,
            resultItems.map((it: any) => ({ id: String(getItemId(it)) })).filter((it: { id: string }) => it.id && it.id !== '—'),
          )
        }
      }
    } catch {
      if (Array.isArray(res.data)) state.items = res.data
    }
  } catch {
    // Silently fail — server may not support this nested endpoint
  } finally {
    state.loading = false
  }
}

/** Fetch all related resources in parallel */
function fetchAllRelations(parentId: string) {
  // Reset all states
  for (const key of Object.keys(relationStates)) {
    delete relationStates[key]
  }
  for (const link of allRelations.value) {
    fetchRelation(link, parentId)
  }
}

function getItemId(item: any): string {
  return item?.id || item?.properties?.id || item?.['@id'] || '—'
}

function getItemName(item: any): string {
  return item?.properties?.name || item?.properties?.title || item?.name || item?.title || ''
}

/** Click a related item → navigate directly to its detail view */
function viewRelatedItem(link: RelatedResourceLink, item: any) {
  const id = getItemId(item)
  if (id === '—') return

  // Skip if clicking the resource we're already viewing (same type AND same id).
  // Different resource types can share the same server-assigned id (e.g. a system
  // and its datastream may both be "040g"), so we must also compare the type.
  const currentId = String(detail.value?.id || detail.value?.properties?.id || props.resourceId || '')
  if (id === currentId && link.childType === props.resourceType) return

  if (link.childType === props.resourceType) {
    // Same type (e.g. subsystems) — reload detail in-place.
    // Save the current detail as the in-place parent so the
    // new detail page has a back-link.
    if (detail.value) {
      const curId = detail.value?.id || detail.value?.properties?.id || props.resourceId
      const curName = detail.value?.properties?.name || detail.value?.name || String(curId)
      inPlaceParent.value = { id: String(curId), name: curName, resourceType: props.resourceType }
    }
    manualId.value = ''
    // Set guard so the watcher (triggered by the emit) doesn't clear inPlaceParent
    _inPlaceNavActive = true
    fetchDetail(id)
    // Let the parent panel know so selectedResourceId stays in sync
    emit('selectResource', id)
  } else {
    // Different type — navigate directly to that item's detail view
    router.push({
      path: `/explore/${link.childType}`,
      query: {
        parentType: props.resourceType,
        parentId: String(detail.value?.id || props.resourceId),
        relation: link.relation,
        resourceId: id,
      },
    })
  }
}

/** Navigate to full nested list for a relation */
function browseAll(link: RelatedResourceLink) {
  const id = detail.value?.id || props.resourceId
  if (!id) return
  router.push({
    path: `/explore/${link.childType}`,
    query: {
      parentType: props.resourceType,
      parentId: String(id),
      relation: link.relation,
    },
  })
}

function toggleRelation(relation: string) {
  const state = getRelState(relation)
  state.expanded = !state.expanded
}

// ========================================
// Parent navigation (observation → datastream → system, etc.)
// ========================================

interface ParentLink {
  label: string
  resourceType: string
  resourceId: string
  icon: string
  /** Friendly name of the parent (when known, e.g. from in-place navigation) */
  name?: string
}

/** Extract navigable parent references from the raw detail JSON cross-reference fields */
const parentLinks = computed<ParentLink[]>(() => {
  if (!detail.value) return []
  const links: ParentLink[] = []
  const raw = detail.value
  const seen = new Set<string>()

  // system@id (present on datastreams, controlStreams)
  if (typeof raw['system@id'] === 'string') {
    links.push({ label: 'System', resourceType: 'systems', resourceId: raw['system@id'], icon: 'pi pi-server' })
    seen.add('systems')
  } else if (raw['system@link']?.uid) {
    // Some servers use system@link with href containing the ID
    const match = raw['system@link']?.href?.match(/systems\/([^/?]+)/)
    if (match) {
      links.push({ label: 'System', resourceType: 'systems', resourceId: match[1], icon: 'pi pi-server' })
      seen.add('systems')
    }
  }

  // datastream@id (present on observations)
  if (typeof raw['datastream@id'] === 'string') {
    links.push({ label: 'Datastream', resourceType: 'datastreams', resourceId: raw['datastream@id'], icon: 'pi pi-chart-line' })
    seen.add('datastreams')
  }

  // controlstream@id (present on commands)
  if (typeof raw['controlstream@id'] === 'string') {
    links.push({ label: 'Control Stream', resourceType: 'controlStreams', resourceId: raw['controlstream@id'], icon: 'pi pi-sliders-h' })
    seen.add('controlStreams')
  }

  // command@id (present on commandStatuses — future-proofing)
  if (typeof raw['command@id'] === 'string') {
    links.push({ label: 'Command', resourceType: 'commands', resourceId: raw['command@id'], icon: 'pi pi-send' })
    seen.add('commands')
  }

  // deployment@id (present on deployed systems)
  if (typeof raw['deployment@id'] === 'string') {
    links.push({ label: 'Deployment', resourceType: 'deployments', resourceId: raw['deployment@id'], icon: 'pi pi-map' })
    seen.add('deployments')
  }

  // OGC API `links` array — look for rel="parent" (provided by servers that
  // expose subsystem/subdeployment parentage via HATEOAS links in GeoJSON).
  // Example: { "rel": "parent", "href": ".../systems/04ng?f=geojson" }
  //          { "rel": "parent", "href": ".../deployments/04cg?f=geojson" }
  if (Array.isArray(raw.links)) {
    for (const link of raw.links) {
      if (link?.rel === 'parent' && typeof link.href === 'string') {
        // Match parent system links
        const sysMatch = link.href.match(/\/systems\/([^/?]+)/)
        if (sysMatch) {
          const parentId = sysMatch[1]
          if (!seen.has('systems:' + parentId) && !seen.has('systems')) {
            links.push({ label: 'Parent System', resourceType: 'systems', resourceId: parentId, icon: 'pi pi-server' })
            seen.add('systems:' + parentId)
            // Also populate the global cache so the relationship persists
            parentSystemCache[effectiveId.value] = { id: parentId, name: link.title || parentId }
          }
        }
        // Match parent deployment links
        const depMatch = link.href.match(/\/deployments\/([^/?]+)/)
        if (depMatch) {
          const parentId = depMatch[1]
          if (!seen.has('deployments:' + parentId) && !seen.has('deployments')) {
            links.push({ label: 'Parent Deployment', resourceType: 'deployments', resourceId: parentId, icon: 'pi pi-map' })
            seen.add('deployments:' + parentId)
          }
        }
      }
    }
  }

  // Nested navigation context (e.g., sampling features under a system, procedures under a system)
  // Add if the parent type isn't already discovered from the JSON fields above.
  // Check both the bare type key (e.g. "deployments") AND the id-qualified key
  // (e.g. "deployments:0480") to avoid duplicating a parent already found via
  // rel="parent" HATEOAS links which use the id-qualified format.
  //
  // ALSO skip the nested context entirely when the resource already has
  // structural parents from its own data (rel="parent" links, @id/@link refs).
  // The nested context is merely *where the user navigated from* — e.g. a
  // deployment's systems panel — it is NOT a structural parent of the resource.
  // Showing it alongside a real parent produces a confusing double breadcrumb.
  const hasStructuralParent = links.length > 0
  if (props.nestedParentType && props.nestedParentId
      && !hasStructuralParent
      && !seen.has(props.nestedParentType)
      && !seen.has(props.nestedParentType + ':' + props.nestedParentId)) {
    const typeInfo = getResourceType(props.nestedParentType)
    if (typeInfo) {
      const isSameType = props.nestedParentType === props.resourceType
      links.push({
        label: isSameType ? `Parent ${typeInfo.label}` : typeInfo.label,
        resourceType: props.nestedParentType,
        resourceId: props.nestedParentId,
        icon: typeInfo.icon,
      })
      seen.add(props.nestedParentType + ':' + props.nestedParentId)
    }
  }

  // In-place parent: when the user drilled into a same-type child (e.g.
  // parent system → subsystem), show a back-link to the parent they came from.
  // Skip if inPlaceParent points to the current resource (self-reference guard).
  if (inPlaceParent.value
      && inPlaceParent.value.id !== effectiveId.value
      && !seen.has(inPlaceParent.value.resourceType + ':' + inPlaceParent.value.id)) {
    const typeInfo = getResourceType(inPlaceParent.value.resourceType)
    if (typeInfo) {
      links.push({
        label: `Parent ${typeInfo.label}`,
        resourceType: inPlaceParent.value.resourceType,
        resourceId: inPlaceParent.value.id,
        icon: typeInfo.icon,
        name: inPlaceParent.value.name,
      })
      seen.add(inPlaceParent.value.resourceType + ':' + inPlaceParent.value.id)
    }
  }

  // Global parent cache fallback: when viewing a system that was previously
  // seen as a subsystem, the cache provides its parent even after component
  // recreation (e.g. navigating back from a grandchild).
  if (props.resourceType === 'systems' && effectiveId.value) {
    const cached = parentSystemCache[effectiveId.value]
    if (cached && cached.id !== effectiveId.value && !seen.has('systems:' + cached.id)) {
      const typeInfo = getResourceType('systems')
      if (typeInfo) {
        links.push({
          label: `Parent ${typeInfo.label}`,
          resourceType: 'systems',
          resourceId: cached.id,
          icon: typeInfo.icon,
          name: cached.name,
        })
      }
    }
  }

  return links
})

function navigateToParent(parent: ParentLink) {
  // When the user drilled into a same-type child in-place (URL unchanged),
  // the URL already points to this parent.  A router.push would be a no-op
  // because the path+query haven't changed.  Instead, reload the parent
  // detail directly and clear the in-place state.
  if (inPlaceParent.value
      && inPlaceParent.value.id === parent.resourceId
      && inPlaceParent.value.resourceType === parent.resourceType) {
    inPlaceParent.value = null
    manualId.value = ''
    fetchDetail(parent.resourceId)
    return
  }
  router.push({
    path: `/explore/${parent.resourceType}`,
    query: { resourceId: parent.resourceId },
  })
}

/**
 * When a parent was discovered via the server's `links` array (rel="parent"),
 * the title is generic ("Parent system"). Fetch the parent detail to get its
 * real name and update the global cache so the breadcrumb shows a useful label.
 */
async function resolveParentName() {
  const curId = effectiveId.value
  if (!curId || props.resourceType !== 'systems') return
  const cached = parentSystemCache[curId]
  if (!cached) return
  // Skip if we already have a real name (not just an ID)
  if (cached.name && cached.name !== cached.id && cached.name !== 'Parent system') return
  try {
    const path = getDetailUrl('systems', cached.id)
    const acceptType = getContentType('systems')
    const res = await apiFetch(path, { headers: { Accept: acceptType } })
    if (res.ok && res.data) {
      const name = res.data?.properties?.name || res.data?.name || cached.id
      parentSystemCache[curId] = { id: cached.id, name }
    }
  } catch { /* parent name stays as ID — non-critical */ }
}

async function fetchDetail(id?: string) {
  const useId = id || manualId.value || props.resourceId
  if (!useId) return

  loading.value = true
  error.value = ''
  errorSeverity.value = 'error'
  detail.value = null

  const path = getDetailUrl(props.resourceType, useId)
  const acceptType = getContentType(props.resourceType)
  const res = await apiFetch(path, {
    headers: { 'Accept': acceptType },
  })

  if (!res.ok) {
    // If the direct fetch fails (e.g. server only serves nested resources),
    // fall back to the resource data already passed from the list
    if (res.status === 404) {
      error.value = 'This resource no longer exists on the server (HTTP 404). It appears in the listing due to a stale server index — the data shown below is cached from the list and may be outdated.'
      errorSeverity.value = 'warn'
      // Still show whatever we have from the list
      if (props.resource) {
        detail.value = props.resource
      }
    } else if (props.resource) {
      detail.value = props.resource
    } else {
      error.value = res.error || 'Failed to fetch resource'
    }
  } else {
    detail.value = res.data
  }

  // For systems, also fetch SensorML metadata (keywords, identifiers, contacts, etc.)
  smlMeta.value = null
  if (isSystem.value && detail.value) {
    const smlPath = getDetailUrl(props.resourceType, String(useId)) + '?f=sml3'
    const smlRes = await apiFetch(smlPath, {
      headers: { 'Accept': 'application/sml+json' },
    })
    if (smlRes.ok && smlRes.data) {
      smlMeta.value = smlRes.data
    }
  }

  // Auto-fetch related resources if we have a detail to show
  if (detail.value) {
    const resId = detail.value?.id || detail.value?.properties?.id
    if (resId && allRelations.value.length > 0) fetchAllRelations(String(resId))

    // Resolve parent system name from rel=parent link (async, doesn't block)
    resolveParentName()
  }
  loading.value = false
}

// Auto-fetch when a resource is selected from the list
watch(
  () => props.resourceId,
  (id) => {
    if (id) {
      if (_inPlaceNavActive) {
        // This prop change came from an in-place drill-down (viewRelatedItem
        // already called fetchDetail and set inPlaceParent) — skip.
        _inPlaceNavActive = false
        return
      }
      // External selection (list click, URL nav, etc.) — clear in-place parent
      inPlaceParent.value = null
      fetchDetail(id)
    }
  },
  { immediate: true }
)

/** Choose an icon class for a SensorML document entry based on role/type */
function docIcon(doc: any): string {
  const role = doc.role || ''
  const type = doc.link?.type || ''
  if (type.startsWith('image/') || role.includes('Photograph')) return 'pi pi-image'
  if (role.includes('Video')) return 'pi pi-video'
  if (type === 'application/pdf' || role.includes('publication')) return 'pi pi-file-pdf'
  if (role.includes('Software')) return 'pi pi-github'
  return 'pi pi-external-link'
}
</script>

<template>
  <div class="resource-detail">
    <div class="manual-fetch">
      <label>Resource ID:</label>
      <InputText v-model="manualId" :placeholder="props.resourceId || 'Enter resource ID'" class="w-md" />
      <Button label="Fetch" icon="pi pi-download" size="small" @click="fetchDetail()" :loading="loading" />
    </div>

    <div v-if="!props.resourceId && !manualId && !detail" class="empty-hint">
      <i class="pi pi-info-circle"></i>
      <p>Select a resource from the List tab, or enter an ID above to view its details.</p>
    </div>

    <div v-if="error && errorSeverity === 'warn'" class="ghost-banner">
      <i class="pi pi-exclamation-triangle"></i>
      <div>
        <strong>Ghost Resource</strong>
        <p>{{ error }}</p>
      </div>
    </div>
    <Message v-else-if="error" severity="error" :closable="false" class="mt-3">{{ error }}</Message>

    <div v-if="loading" class="loading">
      <ProgressSpinner style="width: 30px; height: 30px" />
      <span>Loading...</span>
    </div>

    <template v-if="detail">
      <!-- Resource Summary Header -->
      <div class="resource-summary" v-if="detail.properties?.name || detail.name || detail.properties?.description || detail.description">
        <h3 class="resource-name">
          {{ detail.properties?.name || detail.name || '' }}
          <span v-if="detail.properties?.featureType || detail.featureType" class="feature-type-badge">
            {{ (detail.properties?.featureType || detail.featureType || '').replace('http://www.w3.org/ns/', '').replace('sosa:', 'sosa:') }}
          </span>
        </h3>
        <p v-if="detail.properties?.description || detail.description" class="resource-description">
          {{ detail.properties?.description || detail.description }}
        </p>
        <div class="resource-meta">
          <span v-if="detail.properties?.uid || detail.uid" class="meta-item" title="Unique Identifier">
            <i class="pi pi-key"></i> {{ detail.properties?.uid || detail.uid }}
          </span>
          <span v-if="detail.properties?.assetType || detail.assetType" class="meta-item" title="Asset Type">
            <i class="pi pi-tag"></i> {{ detail.properties?.assetType || detail.assetType }}
          </span>
          <span v-if="detail.properties?.validTime" class="meta-item" title="Valid Time">
            <i class="pi pi-clock"></i>
            {{ Array.isArray(detail.properties.validTime)
              ? detail.properties.validTime[0] + ' → ' + (detail.properties.validTime[1] === '..' ? 'ongoing' : detail.properties.validTime[1])
              : detail.properties.validTime }}
          </span>
          <span v-if="detail.geometry?.type" class="meta-item" title="Geometry">
            <i class="pi pi-map-marker"></i> {{ detail.geometry.type }}
            <template v-if="detail.geometry.coordinates">
              ({{ detail.geometry.coordinates[1]?.toFixed?.(4) ?? '' }}°, {{ detail.geometry.coordinates[0]?.toFixed?.(4) ?? '' }}°)
            </template>
          </span>
        </div>
      </div>

      <!-- ═══════════════════════════════════════════════════════════
           SensorML Metadata Panels (systems only, fetched via ?f=sml3)
           ═══════════════════════════════════════════════════════════ -->
      <div v-if="smlMeta" class="sml-meta-grid">

        <!-- Keywords -->
        <div v-if="smlMeta.keywords?.length" class="sml-card">
          <div class="sml-card-header"><i class="pi pi-tags"></i> Keywords</div>
          <div class="sml-card-body sml-keywords">
            <span v-for="kw in smlMeta.keywords" :key="kw" class="sml-keyword">{{ kw }}</span>
          </div>
        </div>

        <!-- Identifiers -->
        <div v-if="smlMeta.identifiers?.length" class="sml-card">
          <div class="sml-card-header"><i class="pi pi-id-card"></i> Identifiers</div>
          <div class="sml-card-body">
            <table class="sml-table">
              <tbody>
                <tr v-for="ident in smlMeta.identifiers" :key="ident.label">
                  <td class="sml-table-label">{{ ident.label }}</td>
                  <td>{{ ident.value }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Classifiers -->
        <div v-if="smlMeta.classifiers?.length" class="sml-card">
          <div class="sml-card-header"><i class="pi pi-sitemap"></i> Classifiers</div>
          <div class="sml-card-body sml-classifiers">
            <div v-for="cls in smlMeta.classifiers" :key="cls.label" class="sml-classifier">
              <span class="sml-classifier-label">{{ cls.label }}</span>
              <span class="sml-classifier-value">{{ cls.value }}</span>
            </div>
          </div>
        </div>

        <!-- Documents (including images) -->
        <div v-if="smlMeta.documents?.length" class="sml-card sml-card-wide">
          <div class="sml-card-header"><i class="pi pi-file"></i> Documents</div>
          <div class="sml-card-body sml-documents">
            <div v-for="(doc, i) in smlMeta.documents" :key="i" class="sml-doc">
              <!-- Image preview for photographs -->
              <div v-if="doc.link?.type?.startsWith('image/')" class="sml-doc-image">
                <img :src="doc.link.href" :alt="doc.name || 'Photo'" loading="lazy" />
              </div>
              <div class="sml-doc-info">
                <a v-if="doc.link?.href" :href="doc.link.href" target="_blank" rel="noopener" class="sml-doc-link">
                  <i :class="docIcon(doc)"></i>
                  {{ doc.name || doc.link.href }}
                </a>
                <span v-else class="sml-doc-name">{{ doc.name }}</span>
                <span v-if="doc.description" class="sml-doc-desc">{{ doc.description }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Contacts -->
        <div v-if="smlMeta.contacts?.length" class="sml-card">
          <div class="sml-card-header"><i class="pi pi-users"></i> Contacts</div>
          <div class="sml-card-body">
            <div v-for="(ct, i) in smlMeta.contacts" :key="i" class="sml-contact">
              <div class="sml-contact-name">{{ ct.organisationName || ct.individualName || 'Contact' }}</div>
              <div v-if="ct.role" class="sml-contact-role">{{ ct.role.split('/').pop() }}</div>
              <a v-if="ct.contactInfo?.website" :href="ct.contactInfo.website" target="_blank" rel="noopener" class="sml-contact-web">
                <i class="pi pi-external-link"></i> {{ ct.contactInfo.website }}
              </a>
              <div v-if="ct.contactInfo?.address" class="sml-contact-addr">
                {{ [ct.contactInfo.address.city, ct.contactInfo.address.administrativeArea, ct.contactInfo.address.country].filter(Boolean).join(', ') }}
              </div>
            </div>
          </div>
        </div>

        <!-- Characteristics -->
        <div v-if="smlMeta.characteristics?.length" class="sml-card sml-card-wide">
          <div class="sml-card-header"><i class="pi pi-sliders-h"></i> Characteristics</div>
          <div class="sml-card-body">
            <div v-for="(group, gi) in smlMeta.characteristics" :key="gi" class="sml-prop-group">
              <div v-if="group.label" class="sml-prop-group-label">{{ group.label }}</div>
              <table class="sml-table">
                <tbody>
                  <tr v-for="ch in group.characteristics" :key="ch.name">
                    <td class="sml-table-label">{{ ch.label || ch.name }}</td>
                    <td>{{ ch.value }}<span v-if="ch.uom?.code" class="sml-uom"> {{ ch.uom.code }}</span></td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <!-- Capabilities -->
        <div v-if="smlMeta.capabilities?.length" class="sml-card sml-card-wide">
          <div class="sml-card-header"><i class="pi pi-chart-bar"></i> Capabilities</div>
          <div class="sml-card-body">
            <div v-for="(group, gi) in smlMeta.capabilities" :key="gi" class="sml-prop-group">
              <div v-if="group.label" class="sml-prop-group-label">{{ group.label }}</div>
              <table class="sml-table">
                <tbody>
                  <tr v-for="cap in group.capabilities" :key="cap.name">
                    <td class="sml-table-label">{{ cap.label || cap.name }}</td>
                    <td>{{ cap.value }}<span v-if="cap.uom?.code" class="sml-uom"> {{ cap.uom.code }}</span></td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

      </div>

      <!-- Parent navigation breadcrumbs -->
      <div v-if="parentLinks.length > 0" class="parent-nav">
        <i class="pi pi-arrow-up parent-nav-icon"></i>
        <span class="parent-nav-label">Parent:</span>
        <button
          v-for="parent in parentLinks"
          :key="parent.resourceType + ':' + parent.resourceId"
          class="parent-link"
          @click="navigateToParent(parent)"
        >
          <i :class="parent.icon"></i>
          {{ parent.label }}
          <template v-if="parent.name"> — {{ parent.name }}</template>
          <code>{{ parent.resourceId }}</code>
          <i class="pi pi-arrow-up-right parent-link-arrow"></i>
        </button>
      </div>

      <!-- Inline related resource panels in a grid -->
      <div v-if="allRelations.length > 0 && (detail?.id || props.resourceId)" class="relations-grid">
        <div
          v-for="link in allRelations"
          :key="link.relation"
          class="relation-card"
        >
          <div class="relation-header" @click="toggleRelation(link.relation)">
            <i :class="link.icon"></i>
            <span>{{ link.label }}</span>
            <span v-if="!getRelState(link.relation).loading" class="relation-count">{{ getRelState(link.relation).items.length }}</span>
            <ProgressSpinner v-if="getRelState(link.relation).loading" style="width: 14px; height: 14px" />
            <button
              class="filter-toggle-btn"
              :class="{ active: getRelState(link.relation).filtersOpen || hasActiveFilters(getRelState(link.relation), link.childType) }"
              @click.stop="getRelState(link.relation).filtersOpen = !getRelState(link.relation).filtersOpen"
              title="Toggle filters"
            >
              <i class="pi pi-filter"></i>
            </button>
            <i :class="['chevron', 'pi', getRelState(link.relation).expanded ? 'pi-chevron-down' : 'pi-chevron-right']" />
          </div>

          <!-- Collapsible filter row -->
          <div v-if="getRelState(link.relation).filtersOpen" class="relation-filters" @click.stop>
            <div class="relation-filter-row">
              <!-- Keyword search — available for all types -->
              <div class="rel-filter-item">
                <label>Search (q)</label>
                <InputText
                  v-model="getRelState(link.relation).q"
                  placeholder="keyword"
                  class="rel-filter-input"
                  size="small"
                />
              </div>
              <!-- Temporal filter — observations, datastreams, commands, systems, deployments -->
              <template v-if="supportsTemporalFilter(link.childType)">
                <div class="rel-filter-item">
                  <label>{{ temporalParamName(link.childType) }} start</label>
                  <DatePicker
                    v-model="getRelState(link.relation).dtStart"
                    showTime
                    hourFormat="24"
                    showIcon
                    showButtonBar
                    dateFormat="yy-mm-dd"
                    placeholder="Start"
                    class="rel-filter-dt"
                  />
                </div>
                <div class="rel-filter-item">
                  <label>{{ temporalParamName(link.childType) }} end</label>
                  <DatePicker
                    v-model="getRelState(link.relation).dtEnd"
                    showTime
                    hourFormat="24"
                    showIcon
                    showButtonBar
                    dateFormat="yy-mm-dd"
                    placeholder="End"
                    class="rel-filter-dt"
                  />
                </div>
              </template>
              <!-- Command status dropdown — commands only -->
              <div v-if="supportsStatusFilter(link.childType)" class="rel-filter-item">
                <label>currentStatus</label>
                <Select
                  v-model="getRelState(link.relation).currentStatus"
                  :options="commandStatusOptions"
                  optionLabel="label"
                  optionValue="value"
                  placeholder="Any"
                  showClear
                  class="rel-filter-select"
                />
              </div>
            </div>
            <div class="relation-filter-actions">
              <Button
                label="Apply"
                icon="pi pi-search"
                size="small"
                @click="fetchRelation(link, String(detail?.id || props.resourceId))"
                :loading="getRelState(link.relation).loading"
              />
              <Button
                v-if="hasActiveFilters(getRelState(link.relation), link.childType)"
                label="Clear"
                icon="pi pi-times"
                size="small"
                severity="secondary"
                @click="clearFilters(link)"
              />
            </div>
          </div>

          <!-- Client-side fallback warning -->
          <Message
            v-if="getRelState(link.relation).clientSideFallbackDetails.length > 0"
            severity="warn"
            :closable="false"
            class="relation-fallback-msg"
          >
            <div style="font-size: 0.72rem;">Server ignored query parameters — results corrected client-side:</div>
            <ul style="margin: 0.15rem 0 0 0; padding-left: 1rem; font-size: 0.7rem; list-style: disc;">
              <li v-for="(d, i) in getRelState(link.relation).clientSideFallbackDetails" :key="i">{{ d }}</li>
            </ul>
          </Message>

          <div v-if="getRelState(link.relation).expanded" class="relation-body">
            <div v-if="getRelState(link.relation).items.length > 0" class="relation-list">
              <div
                v-for="item in getRelState(link.relation).items"
                :key="getItemId(item)"
                class="relation-item"
                @click="viewRelatedItem(link, item)"
              >
                <code class="relation-item-id">{{ getItemId(item) }}</code>
                <span v-if="getItemName(item)" class="relation-item-name">{{ getItemName(item) }}</span>
                <i class="pi pi-arrow-right relation-arrow"></i>
              </div>
              <button
                v-if="getRelState(link.relation).items.length >= 20"
                class="browse-all-link"
                @click.stop="browseAll(link)"
              >
                Browse all →
              </button>
            </div>
            <div v-else-if="!getRelState(link.relation).loading && !getRelState(link.relation).error" class="relation-empty">
              None found
            </div>
            <div v-if="getRelState(link.relation).error" class="relation-error">
              {{ getRelState(link.relation).error }}
            </div>
          </div>
        </div>
      </div>

      <!-- Data Model diagram (open by default) -->
      <details v-if="detail?.id || props.resourceId" class="diagram-details" open>
        <summary class="diagram-summary">
          <i class="pi pi-share-alt"></i>
          Data Model — SOSA / SSN / CSAPI Relationships
        </summary>
        <DataModelDiagram
          :activeType="props.resourceType"
          :activeId="detail?.id || props.resourceId"
          :parentLinks="parentLinks.map(p => ({ resourceType: p.resourceType, resourceId: p.resourceId, name: p.name }))"
          @navigateToParent="(p: any) => navigateToParent({ label: '', resourceType: p.resourceType, resourceId: p.resourceId, icon: '', name: p.name })"
        />
      </details>

      <!-- Side-by-side layout: Raw JSON | Library Parsed Output -->
      <div class="side-by-side">
        <!-- Left panel: Raw Server Response -->
        <div class="panel raw-panel">
          <h3 class="panel-title">
            <i class="pi pi-server"></i>
            Raw Server Response
          </h3>
          <pre class="raw-json">{{ JSON.stringify(detail, null, 2) }}</pre>
        </div>

        <!-- Right panel: Library Parsed Output -->
        <div class="panel parsed-panel">
          <h3 class="panel-title">
            <i class="pi pi-cog"></i>
            Library Parsed Output
          </h3>
          <ParsedResourceView :resource="detail" :resourceType="props.resourceType" :endpointUrl="`/${props.resourceType}/${effectiveId}`" />
        </div>
      </div>

      <!-- Observation Schema (datastreams only) — full width below -->
      <SweSchemaDisplay v-if="isDatastream && effectiveId" :datastreamId="effectiveId" />

      <!-- Command Schema (control streams only) — full width below -->
      <SweSchemaDisplay v-if="isControlStream && effectiveId" :controlStreamId="effectiveId" />

      <!-- SensorML Process Description (procedures only) — full width below -->
      <SensorMLDisplay v-if="isProcedure && effectiveId" :procedureId="effectiveId" />

      <!-- Links — full width below -->
      <details v-if="detail.links?.length || detail.properties?.links?.length" class="detail-section">
        <summary>Links ({{ (detail.links || detail.properties?.links || []).length }})</summary>
        <table class="links-table">
          <thead><tr><th>Rel</th><th>Type</th><th>Href</th></tr></thead>
          <tbody>
            <tr v-for="(link, i) in (detail.links || detail.properties?.links || [])" :key="i">
              <td>{{ link.rel }}</td>
              <td>{{ link.type || '—' }}</td>
              <td class="href-cell">{{ link.href }}</td>
            </tr>
          </tbody>
        </table>
      </details>
    </template>
  </div>
</template>

<style scoped>
.resource-detail { display: flex; flex-direction: column; gap: 0.75rem; }

/* Resource Summary */
.resource-summary { background: linear-gradient(135deg, #f0fdf4, #ecfdf5); border: 1px solid #86efac; border-radius: 10px; padding: 0.85rem 1rem; }
.resource-name { margin: 0 0 0.3rem; font-size: 1.05rem; font-weight: 700; color: #14532d; display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap; }
.feature-type-badge { font-size: 0.65rem; font-weight: 600; background: #166534; color: #fff; padding: 0.1rem 0.45rem; border-radius: 999px; white-space: nowrap; }
.resource-description { margin: 0 0 0.5rem; font-size: 0.82rem; color: #374151; line-height: 1.45; }
.resource-meta { display: flex; flex-wrap: wrap; gap: 0.5rem; }
.meta-item { display: inline-flex; align-items: center; gap: 0.25rem; font-size: 0.72rem; color: #4b5563; background: #fff; border: 1px solid #d1d5db; border-radius: 6px; padding: 0.15rem 0.45rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 400px; }
.meta-item .pi { font-size: 0.65rem; color: #166534; }

/* Related resources grid */
.relations-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 0.6rem; }
.relation-card { background: #f0f9ff; border: 1px solid #bae6fd; border-radius: 8px; overflow: hidden; display: flex; flex-direction: column; }
.relation-header { display: flex; align-items: center; gap: 0.35rem; padding: 0.5rem 0.65rem; font-weight: 700; font-size: 0.8rem; color: #0369a1; cursor: pointer; user-select: none; }
.relation-header:hover { background: #e0f2fe; }
.relation-count { background: #0369a1; color: #fff; font-size: 0.65rem; font-weight: 700; min-width: 1.1rem; height: 1.1rem; line-height: 1.1rem; text-align: center; border-radius: 999px; padding: 0 0.3rem; }
.chevron { font-size: 0.65rem; color: #7dd3fc; }
.relation-body { border-top: 1px solid #bae6fd; max-height: 200px; overflow-y: auto; }
.relation-list { display: flex; flex-direction: column; }
.relation-item { display: flex; align-items: center; gap: 0.4rem; padding: 0.3rem 0.65rem; cursor: pointer; font-size: 0.8rem; border-bottom: 1px solid #e0f2fe; transition: background 0.1s; }
.relation-item:last-child { border-bottom: none; }
.relation-item:hover { background: #e0f2fe; }
.relation-item-id { background: #e0f2fe; padding: 0.05rem 0.3rem; border-radius: 3px; font-size: 0.72rem; color: #0369a1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 140px; }
.relation-item-name { color: #0c4a6e; flex: 1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; font-size: 0.78rem; }
.relation-arrow { margin-left: auto; font-size: 0.6rem; color: #38bdf8; opacity: 0; transition: opacity 0.15s; flex-shrink: 0; }
.relation-item:hover .relation-arrow { opacity: 1; }
.relation-empty { padding: 0.4rem 0.65rem; color: #7dd3fc; font-size: 0.75rem; font-style: italic; }
.relation-error { padding: 0.4rem 0.65rem; color: #dc2626; font-size: 0.75rem; }
.browse-all-link { display: block; width: 100%; padding: 0.3rem 0.65rem; border: none; background: transparent; color: #0369a1; font-size: 0.75rem; font-weight: 600; cursor: pointer; text-align: left; }
.browse-all-link:hover { background: #e0f2fe; }

/* Filter toggle button in relation header */
.filter-toggle-btn { display: inline-flex; align-items: center; justify-content: center; width: 1.3rem; height: 1.3rem; border: 1px solid #bae6fd; border-radius: 4px; background: transparent; color: #7dd3fc; font-size: 0.6rem; cursor: pointer; padding: 0; transition: all 0.15s; margin-left: auto; }
.filter-toggle-btn:hover { background: #e0f2fe; color: #0369a1; border-color: #0369a1; }
.filter-toggle-btn.active { background: #0369a1; color: #fff; border-color: #0369a1; }

/* Filter row inside relation card */
.relation-filters { border-top: 1px solid #bae6fd; background: #f0f9ff; padding: 0.45rem 0.55rem; }
.relation-filter-row { display: flex; flex-wrap: wrap; gap: 0.35rem 0.5rem; align-items: flex-end; }
.rel-filter-item { display: flex; flex-direction: column; gap: 0.1rem; min-width: 0; }
.rel-filter-item label { font-size: 0.65rem; font-weight: 600; color: #0369a1; white-space: nowrap; }
.rel-filter-input { width: 110px; font-size: 0.72rem; }
.rel-filter-dt { width: 155px; font-size: 0.72rem; }
.rel-filter-dt :deep(.p-datepicker-input) { font-size: 0.72rem; padding: 0.25rem 0.4rem; }
.rel-filter-select { width: 120px; font-size: 0.72rem; }
.rel-filter-select :deep(.p-select-label) { font-size: 0.72rem; padding: 0.25rem 0.4rem; }
.relation-filter-actions { display: flex; gap: 0.3rem; margin-top: 0.35rem; }

/* Fallback warning inside relation card */
.relation-fallback-msg { margin: 0; border-radius: 0; }
.relation-fallback-msg :deep(.p-message-text) { font-size: 0.72rem; }

/* Parent navigation bar */
.parent-nav { display: flex; align-items: center; gap: 0.5rem; padding: 0.4rem 0.65rem; background: #fefce8; border: 1px solid #fde68a; border-radius: 6px; flex-wrap: wrap; }
.parent-nav-icon { font-size: 0.8rem; color: #ca8a04; }
.parent-nav-label { font-size: 0.78rem; font-weight: 600; color: #92400e; white-space: nowrap; }
.parent-link { display: inline-flex; align-items: center; gap: 0.3rem; padding: 0.2rem 0.5rem; border: 1px solid #fde68a; border-radius: 4px; background: #fffbeb; color: #92400e; font-size: 0.78rem; font-weight: 600; cursor: pointer; transition: all 0.15s; white-space: nowrap; }
.parent-link:hover { background: #fef3c7; border-color: #f59e0b; }
.parent-link code { font-size: 0.72rem; background: rgba(0,0,0,0.05); padding: 0.05rem 0.25rem; border-radius: 2px; max-width: 160px; overflow: hidden; text-overflow: ellipsis; }
.parent-link-arrow { font-size: 0.6rem; color: #d97706; opacity: 0.6; }

.diagram-details { margin-top: 0.25rem; }
.diagram-summary { cursor: pointer; font-size: 0.8rem; font-weight: 600; color: #0369a1; display: flex; align-items: center; gap: 0.35rem; padding: 0.3rem 0; user-select: none; }
.diagram-summary:hover { color: #0284c7; }

.manual-fetch { display: flex; align-items: center; gap: 0.5rem; }
.manual-fetch label { font-weight: 600; font-size: 0.9rem; }
.w-md { width: 300px; }
.mt-3 { margin-top: 0.75rem; }
/* Ghost resource warning banner */
.ghost-banner { display: flex; align-items: flex-start; gap: 0.75rem; padding: 0.85rem 1rem; background: linear-gradient(135deg, #fef3c7, #fde68a); border: 2px solid #f59e0b; border-radius: 10px; margin-bottom: 0.5rem; }
.ghost-banner i { font-size: 1.4rem; color: #b45309; margin-top: 0.1rem; flex-shrink: 0; }
.ghost-banner strong { font-size: 0.95rem; color: #92400e; }
.ghost-banner p { margin: 0.25rem 0 0; font-size: 0.82rem; color: #78350f; line-height: 1.4; }

.empty-hint { display: flex; align-items: center; gap: 0.5rem; color: #94a3b8; padding: 1.5rem 0; }
.loading { display: flex; align-items: center; gap: 0.5rem; color: #64748b; }

/* Side-by-side layout */
.side-by-side { display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; min-height: 200px; }
@media (max-width: 900px) {
  .side-by-side { grid-template-columns: 1fr; }
}

/* ─── Mobile breakpoint ─── */
@media (max-width: 768px) {
  .relations-grid { grid-template-columns: 1fr; }
  .sml-meta-grid { grid-template-columns: 1fr; }
  .meta-item { max-width: 100%; }
  .resource-summary { padding: 0.65rem 0.75rem; }
  .resource-name { font-size: 0.95rem; }
  .parent-link { white-space: normal; }
  .parent-link code { max-width: 100px; }
  .w-md { width: 100%; }
}
.panel { border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden; display: flex; flex-direction: column; }
.panel-title { margin: 0; padding: 0.6rem 0.75rem; font-size: 0.85rem; font-weight: 700; display: flex; align-items: center; gap: 0.4rem; }
.raw-panel .panel-title { background: #f8fafc; color: #475569; border-bottom: 1px solid #e2e8f0; }
.parsed-panel .panel-title { background: #f0fdf4; color: #166534; border-bottom: 1px solid #bbf7d0; }
.raw-panel .raw-json { flex: 1; margin: 0; border-radius: 0; max-height: 600px; }
.parsed-panel > :deep(.parsed-view) { padding: 0.75rem; flex: 1; overflow-y: auto; max-height: 600px; }

.raw-json { background: #f8fafc; padding: 0.75rem; overflow-x: auto; font-size: 0.75rem; max-height: 500px; overflow-y: auto; }
.detail-section { margin-top: 0.5rem; }
.detail-section summary { cursor: pointer; font-weight: 600; font-size: 0.9rem; color: #475569; }
.links-table { width: 100%; border-collapse: collapse; font-size: 0.8rem; margin-top: 0.5rem; }
.links-table th, .links-table td { padding: 0.35rem 0.5rem; text-align: left; border-bottom: 1px solid #e2e8f0; }
.links-table th { background: #f8fafc; font-weight: 600; }
.href-cell { font-family: monospace; font-size: 0.75rem; word-break: break-all; }

/* ═══ SensorML Metadata Grid ═══ */
.sml-meta-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 0.6rem; }
.sml-card { background: #fafbff; border: 1px solid #c7d2fe; border-radius: 8px; overflow: hidden; }
.sml-card-wide { grid-column: 1 / -1; }
.sml-card-header { display: flex; align-items: center; gap: 0.35rem; padding: 0.45rem 0.65rem; font-weight: 700; font-size: 0.78rem; color: #4338ca; background: #eef2ff; border-bottom: 1px solid #c7d2fe; user-select: none; }
.sml-card-body { padding: 0.5rem 0.65rem; }

/* Keywords */
.sml-keywords { display: flex; flex-wrap: wrap; gap: 0.3rem; }
.sml-keyword { display: inline-block; font-size: 0.7rem; font-weight: 500; background: #e0e7ff; color: #3730a3; padding: 0.12rem 0.45rem; border-radius: 999px; white-space: nowrap; }

/* Classifiers */
.sml-classifiers { display: flex; flex-direction: column; gap: 0.35rem; }
.sml-classifier { display: flex; align-items: center; gap: 0.4rem; flex-wrap: wrap; }
.sml-classifier-label { font-size: 0.7rem; font-weight: 600; color: #6366f1; white-space: nowrap; }
.sml-classifier-value { font-size: 0.75rem; color: #1e1b4b; background: #e0e7ff; padding: 0.1rem 0.4rem; border-radius: 4px; }

/* Table for identifiers, characteristics, capabilities */
.sml-table { width: 100%; border-collapse: collapse; font-size: 0.75rem; }
.sml-table td { padding: 0.22rem 0.4rem; border-bottom: 1px solid #e5e7eb; }
.sml-table tr:last-child td { border-bottom: none; }
.sml-table-label { font-weight: 600; color: #4338ca; white-space: nowrap; width: 1%; }
.sml-uom { font-size: 0.65rem; color: #6366f1; margin-left: 0.2rem; }

/* Property group (characteristics / capabilities) */
.sml-prop-group { margin-bottom: 0.4rem; }
.sml-prop-group:last-child { margin-bottom: 0; }
.sml-prop-group-label { font-size: 0.7rem; font-weight: 700; color: #4338ca; margin-bottom: 0.2rem; padding-bottom: 0.15rem; border-bottom: 1px dashed #c7d2fe; }

/* Documents */
.sml-documents { display: flex; flex-direction: column; gap: 0.5rem; }
.sml-doc { display: flex; gap: 0.6rem; align-items: flex-start; }
.sml-doc-image { flex-shrink: 0; width: 120px; height: 80px; border-radius: 6px; overflow: hidden; border: 1px solid #c7d2fe; }
.sml-doc-image img { width: 100%; height: 100%; object-fit: cover; }
.sml-doc-info { display: flex; flex-direction: column; gap: 0.15rem; min-width: 0; }
.sml-doc-link { font-size: 0.78rem; font-weight: 600; color: #4338ca; text-decoration: none; display: inline-flex; align-items: center; gap: 0.3rem; }
.sml-doc-link:hover { text-decoration: underline; color: #3730a3; }
.sml-doc-name { font-size: 0.78rem; font-weight: 600; color: #1e1b4b; }
.sml-doc-desc { font-size: 0.7rem; color: #6b7280; line-height: 1.35; }

/* Contacts */
.sml-contact { padding: 0.35rem 0; border-bottom: 1px solid #e5e7eb; }
.sml-contact:last-child { border-bottom: none; }
.sml-contact-name { font-size: 0.78rem; font-weight: 700; color: #1e1b4b; }
.sml-contact-role { font-size: 0.68rem; color: #6366f1; font-weight: 500; }
.sml-contact-web { font-size: 0.7rem; color: #4338ca; text-decoration: none; display: inline-flex; align-items: center; gap: 0.2rem; }
.sml-contact-web:hover { text-decoration: underline; }
.sml-contact-addr { font-size: 0.68rem; color: #6b7280; }
</style>
