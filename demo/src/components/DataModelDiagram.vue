<script setup lang="ts">
import { computed, reactive, ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { apiFetch } from '../api'
import { getNestedListUrl, getListUrl, getDetailUrl, getContentType } from '../csapi-bridge'
import { connection, RELATED_RESOURCES, cacheParentForChildren } from '../state'

const router = useRouter()

interface ParentRef {
  resourceType: string
  resourceId: string
  /** Friendly name of the parent resource (when known) */
  name?: string
}

const props = defineProps<{
  /** The resource type currently being viewed */
  activeType: string
  /** The resource ID currently being viewed (for navigation context) */
  activeId?: string
  /** Parent references extracted from the resource JSON (e.g., observation → datastream) */
  parentLinks?: ParentRef[]
}>()

/* ──────────────────────────────────────────────────────────────────────
 * CSAPI / SOSA / SSN Data Model — Node & Edge Definitions
 *
 * This encodes the OGC Connected Systems API resource graph, which is
 * grounded in W3C/OGC SOSA/SSN ontology:
 *
 *   System  ≈  sosa:Platform / ssn:System
 *   Procedure ≈ sosa:Procedure
 *   Deployment ≈ ssn:Deployment
 *   SamplingFeature ≈ sosa:FeatureOfInterest / sam:SamplingFeature
 *   Datastream ≈ sosa:ObservationCollection (output channel)
 *   Observation ≈ sosa:Observation
 *   ControlStream ≈ (actuator command channel — CSAPI extension)
 *   Command ≈ sosa:Actuation
 *   Property ≈ ssn:Property / sosa:ObservableProperty
 * ──────────────────────────────────────────────────────────────────── */

interface ModelNode {
  id: string
  label: string
  shortLabel: string
  part: 1 | 2
  x: number
  y: number
  icon: string
  color: string
  hoverColor: string
}

interface ModelEdge {
  from: string
  to: string
  label: string
  /** Edge style hint */
  style: 'solid' | 'dashed'
  /** Plain-language tooltip shown on hover */
  tooltip: string
}

/*
 * Layout: Part 1 (Features) on the left/center, Part 2 (Observations & Commands)
 * on the right. System is the central hub reflecting its role as the primary
 * resource that ties everything together in SOSA/SSN.
 *
 * SVG viewBox is 800 x 500
 */
const nodes: ModelNode[] = [
  // Part 1 — Features
  { id: 'systems',           label: 'System',            shortLabel: 'SYS',  part: 1, x: 300, y: 200, icon: '⬡', color: '#0ea5e9', hoverColor: '#0284c7' },
  { id: 'procedures',        label: 'Procedure',         shortLabel: 'PRC',  part: 1, x: 100, y: 100, icon: '⚙', color: '#8b5cf6', hoverColor: '#7c3aed' },
  { id: 'deployments',       label: 'Deployment',        shortLabel: 'DEP',  part: 1, x: 100, y: 300, icon: '⊕', color: '#f59e0b', hoverColor: '#d97706' },
  { id: 'samplingFeatures',  label: 'Sampling Feature',  shortLabel: 'SF',   part: 1, x: 100, y: 200, icon: '◉', color: '#10b981', hoverColor: '#059669' },
  { id: 'properties',        label: 'Property',          shortLabel: 'PRP',  part: 1, x: 300, y: 30,  icon: '⊞', color: '#6b7280', hoverColor: '#4b5563' },

  // Part 2 — Observations & Commands
  { id: 'datastreams',       label: 'Datastream',        shortLabel: 'DS',   part: 2, x: 530, y: 130, icon: '≋', color: '#06b6d4', hoverColor: '#0891b2' },
  { id: 'observations',      label: 'Observation',       shortLabel: 'OBS',  part: 2, x: 700, y: 130, icon: '◈', color: '#3b82f6', hoverColor: '#2563eb' },
  { id: 'controlStreams',    label: 'Control Stream',    shortLabel: 'CS',   part: 2, x: 530, y: 300, icon: '⇶', color: '#ec4899', hoverColor: '#db2777' },
  { id: 'commands',          label: 'Command',           shortLabel: 'CMD',  part: 2, x: 700, y: 300, icon: '▶', color: '#f43f5e', hoverColor: '#e11d48' },
]

const edges: ModelEdge[] = [
  // System is central hub
  { from: 'systems',    to: 'procedures',       label: 'implements',       style: 'solid',  tooltip: 'A System implements a Procedure that describes its sensing or actuating capabilities' },
  { from: 'systems',    to: 'deployments',       label: 'deployedIn',       style: 'solid',  tooltip: 'A System is deployed as part of a Deployment that describes when/where it operates' },
  { from: 'systems',    to: 'samplingFeatures',  label: 'samples',          style: 'solid',  tooltip: 'A System samples a Sampling Feature \u2014 the real-world entity being observed' },
  { from: 'systems',    to: 'datastreams',       label: 'outputs',          style: 'solid',  tooltip: 'A System produces Datastreams that represent its continuous data outputs' },
  { from: 'systems',    to: 'controlStreams',    label: 'controls',         style: 'solid',  tooltip: 'A System exposes Control Streams that accept commands to change its behavior' },
  { from: 'systems',    to: 'systems',           label: 'subsystems',       style: 'dashed', tooltip: 'Systems can contain child sub-systems, forming a hierarchical tree' },

  // Deployment self-reference
  { from: 'deployments', to: 'deployments',      label: 'subdeployments',   style: 'dashed', tooltip: 'Deployments can contain child sub-deployments for nested deployment structures' },

  // Part 2 chains
  { from: 'datastreams',    to: 'observations',  label: 'produces',         style: 'solid',  tooltip: 'A Datastream produces individual Observations \u2014 each a timestamped measurement' },
  { from: 'controlStreams', to: 'commands',       label: 'receives',         style: 'solid',  tooltip: 'A Control Stream receives individual Commands \u2014 each a timestamped instruction' },

  // Property links
  { from: 'datastreams',    to: 'properties',    label: 'observes',         style: 'dashed', tooltip: 'A Datastream observes a Property \u2014 the physical quantity being measured' },
  { from: 'controlStreams', to: 'properties',     label: 'controls',         style: 'dashed', tooltip: 'A Control Stream controls a Property \u2014 the parameter being commanded' },
]

const NODE_RX = 12
const NODE_W = 130
const NODE_H = 52

// ─── Parent System Node (shown when viewing a subsystem) ──────────

/** Detected same-type parent link (e.g. subsystem's parent system) */
const sameTypeParent = computed(() => {
  if (!props.parentLinks?.length) return null
  return props.parentLinks.find(p => p.resourceType === props.activeType) || null
})

/** Resolved parent name — from prop or fetched */
const parentName = ref<string | null>(null)

// Fetch parent name if not provided via prop
watch(sameTypeParent, async (p) => {
  parentName.value = null
  if (!p) return
  if (p.name) { parentName.value = p.name; return }
  // Fetch the parent detail to get its name
  try {
    const path = getDetailUrl(p.resourceType, p.resourceId)
    const acceptType = getContentType(p.resourceType)
    const res = await apiFetch(path, { headers: { Accept: acceptType } })
    if (res.ok && res.data) {
      parentName.value = res.data?.properties?.name || res.data?.name || p.resourceId
    }
  } catch { /* use null — template will show ID only */ }
}, { immediate: true })

/** Parent node position — placed above-left of the System node */
const PARENT_NODE = { x: 130, y: 35, w: 160, h: 44 }

// ─── Self-Hierarchy Cluster (subsystems / subdeployments) ──────────

/** First N self-hierarchy child items fetched for the cluster display */
const selfChildItems = ref<Array<{ id: string; name: string }>>([])
/** Total count of self-hierarchy children (may exceed displayed items) */
const selfChildTotal = ref(0)
/** The relation name for the active self-hierarchy ("subsystems" or "subdeployments") */
const selfChildRelation = ref<string>('')

/** The ModelNode definition for the currently active resource type */
const activeNodeDef = computed(() => nodes.find(n => n.id === props.activeType))

/** Cluster config computed from the active node's position and self-loop edge */
const selfClusterConfig = computed(() => {
  const node = activeNodeDef.value
  if (!node || selfChildItems.value.length === 0) return null
  const selfEdge = edges.find(e => e.from === e.to && e.from === props.activeType)
  if (!selfEdge) return null
  return {
    x: Math.round(node.x - 165 / 2),
    startY: node.y + NODE_H / 2 + 65,
    chipW: 165,
    chipH: 19,
    gap: 3,
    maxShow: 6,
    color: node.color,
    icon: node.icon,
    nodeX: node.x,
    nodeY: node.y,
    relation: selfEdge.label,
  }
})

/** Dynamic SVG viewBox height — expands to fit cluster for lower-positioned nodes */
const svgViewBoxHeight = computed(() => {
  const sc = selfClusterConfig.value
  if (!sc) return 480
  const items = Math.min(selfChildItems.value.length, sc.maxShow)
  const hasOverflow = selfChildTotal.value > sc.maxShow
  const clusterBottom = sc.startY + items * (sc.chipH + sc.gap) + (hasOverflow ? 22 : 0) + 10
  return Math.max(480, clusterBottom + 20)
})

/** Find a node by id */
function findNode(id: string): ModelNode | undefined {
  return nodes.find(n => n.id === id)
}

/** Does this node have a self-referencing (hierarchy) edge? */
function hasSelfLoop(nodeId: string): boolean {
  return edges.some(e => e.from === e.to && e.from === nodeId)
}

/** Which nodes are directly connected to the active type? */
const connectedNodeIds = computed<Set<string>>(() => {
  const set = new Set<string>()
  set.add(props.activeType)
  for (const e of edges) {
    if (e.from === props.activeType) set.add(e.to)
    if (e.to === props.activeType) set.add(e.from)
  }
  // Also include parent-linked nodes
  if (props.parentLinks) {
    for (const p of props.parentLinks) set.add(p.resourceType)
  }
  return set
})

/** Does this related type have actual resources? (positive count) */
function hasResources(nodeId: string): boolean {
  const c = counts[nodeId]
  return c != null && c > 0
}

/** Is this node the actively viewed resource? */
function isActive(nodeId: string) {
  return nodeId === props.activeType
}

/** Is this node connected to the active resource (and actually has data)? */
function isConnected(nodeId: string) {
  if (nodeId === props.activeType) return true

  // Direct relation with positive count
  if (connectedNodeIds.value.has(nodeId) && hasResources(nodeId)) return true

  // Parent link: always connected if a parent reference exists for this type
  if (props.parentLinks?.some(p => p.resourceType === nodeId)) return true

  // Node has resources discovered from parent/grandparent context
  // (we only ever populate counts for structurally related nodes)
  if (hasResources(nodeId)) return true

  // Transitive: observations are reachable if datastreams > 0
  if (nodeId === 'observations' && hasResources('datastreams')) return true
  // Transitive: commands are reachable if controlStreams > 0
  if (nodeId === 'commands' && hasResources('controlStreams')) return true

  return false
}

/** Is this edge connected to the active type (and the far end has data)? */
function isEdgeActive(edge: ModelEdge) {
  // Direct edge from/to active type
  if (edge.from === props.activeType || edge.to === props.activeType) {
    const otherEnd = edge.from === props.activeType ? edge.to : edge.from
    // Parent-linked nodes are always active
    if (props.parentLinks?.some(p => p.resourceType === otherEnd)) return true
    return hasResources(otherEnd)
  }

  // Check transitive edges: datastreams→observations, controlStreams→commands
  if (edge.from === 'datastreams' && edge.to === 'observations' && hasResources('datastreams')) return true
  if (edge.from === 'controlStreams' && edge.to === 'commands' && hasResources('controlStreams')) return true

  // Parent-chain edges: if both ends are connected, light up the edge between them
  // e.g., viewing observations with parent datastream → light up systems↔datastreams edge too
  if (isConnected(edge.from) && isConnected(edge.to)) return true

  return false
}

/** Compute edge path between two nodes.
 *  For self-referencing edges, draw a loop. */
function edgePath(edge: ModelEdge): string {
  const from = findNode(edge.from)!
  const to = findNode(edge.to)!

  if (edge.from === edge.to) {
    // Self-loop: arc below the node
    const cx = from.x
    const cy = from.y + NODE_H / 2
    return `M ${cx - 20} ${cy} C ${cx - 40} ${cy + 50}, ${cx + 40} ${cy + 50}, ${cx + 20} ${cy}`
  }

  // Compute connection points on node rects
  const fx = from.x, fy = from.y
  const tx = to.x, ty = to.y

  // Direction vector
  const dx = tx - fx, dy = ty - fy
  const dist = Math.sqrt(dx * dx + dy * dy) || 1

  // Start/end at node boundary (simplified: use ellipse intersection)
  const hw = NODE_W / 2, hh = NODE_H / 2
  const sx = fx + (dx / dist) * hw * 0.9
  const sy = fy + (dy / dist) * hh * 0.9
  const ex = tx - (dx / dist) * hw * 0.9
  const ey = ty - (dy / dist) * hh * 0.9

  return `M ${sx} ${sy} L ${ex} ${ey}`
}

/** Label position for an edge */
function edgeLabelPos(edge: ModelEdge): { x: number; y: number } {
  const from = findNode(edge.from)!
  const to = findNode(edge.to)!

  if (edge.from === edge.to) {
    return { x: from.x, y: from.y + NODE_H / 2 + 40 }
  }

  return {
    x: (from.x + to.x) / 2,
    y: (from.y + to.y) / 2 - 6,
  }
}

// ─── Live Resource Counts (scoped to active resource) ─────────────

/** Map of resource-type key → count (null = loading, -1 = unavailable/error) */
const counts = reactive<Record<string, number | null>>({})
/** Grandparent references discovered by fetching parent detail JSON */
const discoveredAncestors = reactive<Record<string, ParentRef>>({})
let fetchGeneration = 0

/**
 * Extract a resource count from a collection response.
 * Prefers `numberMatched` when available; otherwise infers from items
 * and the presence of a `next` pagination link (indicating more exist).
 * Returns -1 when no useful count can be determined.
 */
function extractCount(data: any): number {
  if (data?.numberMatched != null) return data.numberMatched
  const items = data?.items ?? data?.features
  if (Array.isArray(items)) {
    const len = items.length
    // If there's a "next" link, at least one more page exists
    const hasNext = Array.isArray(data?.links) && data.links.some((l: any) => l.rel === 'next')
    return hasNext ? Math.max(len, len + 1) : len
  }
  return -1
}

/**
 * Resolve the count of deployed systems from a deployment's inline properties.
 * Per OGC 23-001 Table 43, deployedSystems maps to properties/deployedSystems@link
 * (a JSON Array of links to System resources), NOT to a sub-resource endpoint.
 * Falls back to platform@link when deployedSystems@link is absent.
 */
async function resolveDeployedSystemsCount(deploymentId: string): Promise<number> {
  try {
    const path = getDetailUrl('deployments', deploymentId)
    const acceptType = getContentType('deployments')
    const res = await apiFetch(path, { headers: { Accept: acceptType } })
    if (!res.ok) return 0
    const parentProps = res.data?.properties || res.data || {}

    // 1. Try deployedSystems@link — the standard-defined inline property
    const dsLinks = parentProps['deployedSystems@link']
    if (Array.isArray(dsLinks) && dsLinks.length > 0) {
      return dsLinks.filter((l: any) => l?.href).length
    }

    // 2. Fallback: platform@link — identifies the platform system hosting the deployment
    const platformLink = parentProps['platform@link']
    if (platformLink?.href) return 1

    // 3. Fallback: deployedSystemUIDs — comma-separated UID string
    const uidStr = parentProps['deployedSystemUIDs']
    if (typeof uidStr === 'string' && uidStr.length > 0) {
      return uidStr.split(',').filter((u: string) => u.trim()).length
    }

    return 0
  } catch { return 0 }
}

/**
 * Fetch counts of related/nested resources for the currently viewed resource.
 * Fetches direct relations, then transitive grandchild counts
 * (observations via datastreams, commands via controlStreams).
 * For leaf types with parent links, also fetches counts from parent perspective.
 */
async function fetchCounts() {
  const gen = ++fetchGeneration
  const parentType = props.activeType
  const parentId = props.activeId

  // Clear previous counts
  for (const key of Object.keys(counts)) delete counts[key]
  for (const key of Object.keys(discoveredAncestors)) delete discoveredAncestors[key]
  selfChildItems.value = []
  selfChildTotal.value = 0
  selfChildRelation.value = ''

  if (!parentId || !parentType) return

  const relations = RELATED_RESOURCES[parentType]

  // ── Direct child counts (if this type has RELATED_RESOURCES) ───
  if (relations?.length) {
    // Set connected types to loading
    for (const rel of relations) counts[rel.childType] = null

    // Fire all direct requests in parallel
    const requests = relations.map(async (rel) => {
      try {
        // For self-hierarchy relations (subsystems/subdeployments), fetch a page for chip display
        const isSelfHierarchy = rel.childType === parentType && edges.some(e => e.from === e.to && e.from === parentType && e.label === rel.relation)
        const limit = isSelfHierarchy ? 8 : 1
        const path = getNestedListUrl(parentType, parentId, rel.relation, { limit })
        const res = await apiFetch(path)
        if (gen !== fetchGeneration) return  // stale
        if (!res.ok) {
          // --- Deployed Systems fallback (OGC 23-001 Table 43) ---
          // /deployments/{id}/systems is non-standard; deployedSystems is an
          // inline property.  Fetch the deployment detail and resolve @link refs.
          if (parentType === 'deployments' && rel.relation === 'systems') {
            const inlineCount = await resolveDeployedSystemsCount(parentId)
            if (gen !== fetchGeneration) return
            counts[rel.childType] = inlineCount
            return
          }
          counts[rel.childType] = -1
          if (isSelfHierarchy) { selfChildItems.value = []; selfChildTotal.value = 0 }
          return
        }
        let count = extractCount(res.data)

        // --- Subdeployments fallback ---
        // Some servers (e.g. OSH SensorHub) return 200/{items:[]} for
        // /deployments/{id}/subdeployments but track parentage only via
        // the collection-level ?parent= query parameter.
        // CAVEAT: Some servers ignore the ?parent= value entirely and return
        // ALL deployments that have any parent.  We detect this with a probe:
        // query ?parent=<nonsense>&limit=1 — if it returns items, the filter
        // is a no-op and the results are unreliable.
        if (count === 0 && isSelfHierarchy
            && parentType === 'deployments' && rel.relation === 'subdeployments') {
          try {
            // Probe: test if ?parent= filter actually works
            const probeRes = await apiFetch('/deployments?parent=__csapi_probe__&limit=1')
            if (gen !== fetchGeneration) return
            const probeItems = probeRes.ok ? (probeRes.data?.items || probeRes.data?.features || []) : []
            if (probeItems.length > 0) {
              // Filter is broken — returns items for a nonexistent parent.
              // Cannot trust ?parent= results; fall back to scanning all
              // deployments and checking partOf@link client-side.
              const scanRes = await apiFetch('/deployments?limit=50')
              if (gen !== fetchGeneration) return
              if (scanRes.ok && scanRes.data) {
                const allDeps = scanRes.data?.items || scanRes.data?.features || []
                const children = allDeps.filter((it: any) => {
                  const partOf = it?.properties?.['partOf@link']
                  if (!partOf?.href) return false
                  const href = String(partOf.href)
                  return href.endsWith(`/${parentId}`) || href.endsWith(`/deployments/${parentId}`)
                })
                if (children.length > 0) {
                  count = children.length
                  selfChildItems.value = children.map((it: any) => ({
                    id: String(it?.id || it?.properties?.id || ''),
                    name: it?.properties?.name || it?.name || String(it?.id || ''),
                  })).filter((it: { id: string }) => it.id)
                  selfChildTotal.value = count
                  selfChildRelation.value = rel.relation
                  if (parentId && selfChildItems.value.length > 0) {
                    cacheParentForChildren(parentId, String(parentId), selfChildItems.value)
                  }
                }
              }
            } else {
              const fbPath = `/deployments?parent=${encodeURIComponent(parentId)}&limit=8`
              const fbRes = await apiFetch(fbPath)
              if (gen !== fetchGeneration) return
              if (fbRes.ok && fbRes.data) {
                const fbItems = (fbRes.data?.items || fbRes.data?.features || [])
                  .filter((it: any) => {
                    const id = it?.id || it?.properties?.id
                    return id && String(id) !== String(parentId)
                  })
                if (fbItems.length > 0) {
                  count = fbItems.length
                  if (fbRes.data?.numberMatched != null) {
                    const serverTotal = fbRes.data.numberMatched
                    count = serverTotal > count ? serverTotal : count
                    const rawLen = (fbRes.data?.items || fbRes.data?.features || []).length
                    if (rawLen > fbItems.length) count = Math.max(0, count - (rawLen - fbItems.length))
                  }
                  selfChildItems.value = fbItems.map((it: any) => ({
                    id: String(it?.id || it?.properties?.id || ''),
                    name: it?.properties?.name || it?.name || String(it?.id || ''),
                  })).filter((it: { id: string }) => it.id)
                  selfChildTotal.value = count
                  selfChildRelation.value = rel.relation
                  if (parentId && selfChildItems.value.length > 0) {
                    cacheParentForChildren(parentId, String(parentId), selfChildItems.value)
                  }
                }
              }
            }
          } catch { /* non-critical */ }
        }

        // --- Deployed Systems fallback (after 200 with 0 items) ---
        if (count === 0 && parentType === 'deployments' && rel.relation === 'systems') {
          const inlineCount = await resolveDeployedSystemsCount(parentId)
          if (gen !== fetchGeneration) return
          if (inlineCount > 0) count = inlineCount
        }

        counts[rel.childType] = count

        // Populate self-hierarchy cluster items (subsystems or subdeployments)
        // Skip if the fallback above already populated the cluster.
        if (isSelfHierarchy && selfChildItems.value.length === 0) {
          const items = res.data?.items || res.data?.features || []
          selfChildItems.value = items.map((it: any) => ({
            id: String(it?.id || it?.properties?.id || ''),
            name: it?.properties?.name || it?.name || String(it?.id || ''),
          })).filter((it: { id: string }) => it.id)
          selfChildTotal.value = extractCount(res.data)
          selfChildRelation.value = rel.relation

          // Cache parent relationship so breadcrumbs survive navigation.
          if (parentId && selfChildItems.value.length > 0) {
            cacheParentForChildren(parentId, String(parentId), selfChildItems.value)
          }
        }
      } catch {
        if (gen !== fetchGeneration) return
        counts[rel.childType] = -1
      }
    })
    await Promise.allSettled(requests)
    if (gen !== fetchGeneration) return

    // ── Transitive grandchild counts ──────────────────────────────
    const transitiveJobs: Array<{ intermediateType: string; intermediateRelation: string; grandchildType: string; grandchildRelation: string }> = []

    if (counts['datastreams'] != null && counts['datastreams'] > 0) {
      transitiveJobs.push({ intermediateType: 'datastreams', intermediateRelation: 'datastreams', grandchildType: 'observations', grandchildRelation: 'observations' })
    }
    if (counts['controlStreams'] != null && counts['controlStreams'] > 0) {
      transitiveJobs.push({ intermediateType: 'controlStreams', intermediateRelation: 'controlstreams', grandchildType: 'commands', grandchildRelation: 'commands' })
    }

    if (transitiveJobs.length) {
      for (const job of transitiveJobs) {
        counts[job.grandchildType] = null  // loading
      }

      const transitiveRequests = transitiveJobs.map(async (job) => {
        try {
          const listPath = getNestedListUrl(parentType, parentId, job.intermediateRelation, { limit: 100 })
          const listRes = await apiFetch(listPath)
          if (gen !== fetchGeneration) return
          if (!listRes.ok) { counts[job.grandchildType] = -1; return }

          const items = listRes.data?.items || listRes.data?.features || []
          const ids: string[] = items.map((item: any) => item?.id || item?.properties?.id).filter(Boolean)

          if (!ids.length) { counts[job.grandchildType] = 0; return }

          let total = 0
          const subRequests = ids.map(async (id: string) => {
            try {
              const path = getNestedListUrl(job.intermediateType, id, job.grandchildRelation, { limit: 1 })
              const res = await apiFetch(path)
              if (gen !== fetchGeneration) return 0
              if (!res.ok) return 0
              const c = extractCount(res.data)
              return c > 0 ? c : 0
            } catch { return 0 }
          })
          const results = await Promise.allSettled(subRequests)
          for (const r of results) {
            if (r.status === 'fulfilled') total += (r.value ?? 0)
          }
          if (gen !== fetchGeneration) return
          counts[job.grandchildType] = total
        } catch {
          if (gen !== fetchGeneration) return
          counts[job.grandchildType] = -1
        }
      })
      await Promise.allSettled(transitiveRequests)
    }
  }

  if (gen !== fetchGeneration) return

  // ── Parent-link counts ─────────────────────────────────────────
  // For each parent reference (e.g., observation's datastream, datastream's system),
  // fetch the parent's child relations to populate counts on sibling/ancestor nodes.
  if (props.parentLinks?.length) {
    const parentRequests = props.parentLinks.map(async (pLink) => {
      const pRelations = RELATED_RESOURCES[pLink.resourceType]
      if (!pRelations?.length) return

      // Mark parent node as having a resource (count = 1 since we know it exists)
      if (!hasResources(pLink.resourceType)) counts[pLink.resourceType] = 1

      const childRequests = pRelations.map(async (rel) => {
        // Don't overwrite counts we already fetched directly
        if (counts[rel.childType] !== undefined) return
        // Skip fetching for the active type (we know it has at least 1 — us)
        if (rel.childType === parentType) {
          counts[rel.childType] = counts[rel.childType] ?? 1
          return
        }

        counts[rel.childType] = null  // loading
        try {
          const path = getNestedListUrl(pLink.resourceType, pLink.resourceId, rel.relation, { limit: 1 })
          const res = await apiFetch(path)
          if (gen !== fetchGeneration) return
          if (!res.ok) { counts[rel.childType] = -1; return }
          counts[rel.childType] = extractCount(res.data)
        } catch {
          if (gen !== fetchGeneration) return
          counts[rel.childType] = -1
        }
      })
      await Promise.allSettled(childRequests)
    })
    await Promise.allSettled(parentRequests)

    if (gen !== fetchGeneration) return

    // ── Grandparent discovery ──────────────────────────────────────
    // Fetch each parent's detail JSON to discover its own parent references
    // (e.g., fetch datastream 083g → find system@id → mark system as count=1)
    // Then fetch that grandparent's child relations for sibling counts.
    const discoveredGrandparents: ParentRef[] = []

    const detailRequests = props.parentLinks.map(async (pLink) => {
      try {
        const path = getDetailUrl(pLink.resourceType, pLink.resourceId)
        const acceptType = getContentType(pLink.resourceType)
        const res = await apiFetch(path, { headers: { Accept: acceptType } })
        if (gen !== fetchGeneration || !res.ok) return
        const raw = res.data

        // Extract parent references from the parent's JSON (same logic as ResourceDetail)
        // Use !hasResources() so we override error (-1) and undefined counts
        if (typeof raw?.['system@id'] === 'string' && !hasResources('systems')) {
          const ref = { resourceType: 'systems', resourceId: raw['system@id'] }
          discoveredGrandparents.push(ref)
          discoveredAncestors['systems'] = ref
          counts['systems'] = 1
        }
        if (typeof raw?.['datastream@id'] === 'string' && !hasResources('datastreams')) {
          const ref = { resourceType: 'datastreams', resourceId: raw['datastream@id'] }
          discoveredGrandparents.push(ref)
          discoveredAncestors['datastreams'] = ref
          counts['datastreams'] = 1
        }
        if (typeof raw?.['controlstream@id'] === 'string' && !hasResources('controlStreams')) {
          const ref = { resourceType: 'controlStreams', resourceId: raw['controlstream@id'] }
          discoveredGrandparents.push(ref)
          discoveredAncestors['controlStreams'] = ref
          counts['controlStreams'] = 1
        }
        if (typeof raw?.['deployment@id'] === 'string' && !hasResources('deployments')) {
          const ref = { resourceType: 'deployments', resourceId: raw['deployment@id'] }
          discoveredGrandparents.push(ref)
          discoveredAncestors['deployments'] = ref
          counts['deployments'] = 1
        }
      } catch { /* ignore — best effort */ }
    })
    await Promise.allSettled(detailRequests)

    if (gen !== fetchGeneration) return

    // Fetch grandparent child relations for further sibling counts
    if (discoveredGrandparents.length) {
      const gpRequests = discoveredGrandparents.map(async (gp) => {
        const gpRelations = RELATED_RESOURCES[gp.resourceType]
        if (!gpRelations?.length) return

        const gpChildRequests = gpRelations.map(async (rel) => {
          // Skip if we already have a positive count; allow overriding errors (-1)
          if (counts[rel.childType] != null && counts[rel.childType]! >= 0) return
          counts[rel.childType] = null  // loading
          try {
            const path = getNestedListUrl(gp.resourceType, gp.resourceId, rel.relation, { limit: 1 })
            const res = await apiFetch(path)
            if (gen !== fetchGeneration) return
            if (!res.ok) { counts[rel.childType] = -1; return }
            counts[rel.childType] = extractCount(res.data)
          } catch {
            if (gen !== fetchGeneration) return
            counts[rel.childType] = -1
          }
        })
        await Promise.allSettled(gpChildRequests)
      })
      await Promise.allSettled(gpRequests)
    }
  }
}

function formatCount(n: number | null | undefined): string {
  if (n == null) return '…'         // loading
  if (n < 0) return '—'             // unavailable
  if (n >= 10000) return `${(n / 1000).toFixed(0)}k`
  if (n >= 1000) return `${(n / 1000).toFixed(1)}k`
  return String(n)
}

onMounted(() => {
  if (connection.connected && props.activeId) fetchCounts()
})

watch([() => props.activeType, () => props.activeId, () => props.parentLinks], () => {
  if (connection.connected && props.activeId) fetchCounts()
})

/** Navigate to a related resource type's list, scoped to the active resource.
 *  Matches the behavior of the related resource panels in ResourceDetail. */
function navigateToType(nodeId: string) {
  // If it's the active type, do nothing
  if (nodeId === props.activeType) return

  // Only navigate if this node is highlighted (has resources)
  if (!isConnected(nodeId)) return

  // Check if this is a parent-linked node (e.g., observation's datastream, datastream's system)
  const parentLink = props.parentLinks?.find(p => p.resourceType === nodeId)
  if (parentLink) {
    // Navigate directly to the parent resource's detail view
    router.push({
      path: `/explore/${parentLink.resourceType}`,
      query: { resourceId: parentLink.resourceId },
    })
    return
  }

  // Check if this is a discovered ancestor (grandparent, e.g., datastream's system)
  const ancestor = discoveredAncestors[nodeId]
  if (ancestor) {
    router.push({
      path: `/explore/${ancestor.resourceType}`,
      query: { resourceId: ancestor.resourceId },
    })
    return
  }

  if (!props.activeId) {
    // No active resource — just navigate to the top-level list
    router.push({ path: `/explore/${nodeId}` })
    return
  }

  // Find the RELATED_RESOURCES entry for this relation (direct child)
  const relations = RELATED_RESOURCES[props.activeType]
  const rel = relations?.find(r => r.childType === nodeId)

  if (rel) {
    // Navigate to the nested list, same as the "browse all" in ResourceDetail
    router.push({
      path: `/explore/${rel.childType}`,
      query: {
        parentType: props.activeType,
        parentId: props.activeId,
        relation: rel.relation,
      },
    })
    return
  }

  // Check if a parent has a relation to this node (sibling via parent)
  const allAncestors = [
    ...(props.parentLinks || []),
    ...Object.values(discoveredAncestors),
  ]
  for (const pLink of allAncestors) {
    const pRelations = RELATED_RESOURCES[pLink.resourceType]
    const pRel = pRelations?.find(r => r.childType === nodeId)
    if (pRel) {
      router.push({
        path: `/explore/${pRel.childType}`,
        query: {
          parentType: pLink.resourceType,
          parentId: pLink.resourceId,
          relation: pRel.relation,
        },
      })
      return
    }
  }

  // Fallback: top-level list
  router.push({ path: `/explore/${nodeId}` })
}

/** Navigate directly to the parent resource — bypasses the navigateToType guard
 *  that blocks same-type navigation (e.g. systems → systems, deployments → deployments). */
function navigateToParent() {
  if (!sameTypeParent.value) return
  router.push({
    path: `/explore/${sameTypeParent.value.resourceType}`,
    query: { resourceId: sameTypeParent.value.resourceId },
  })
}

/** Navigate into a self-hierarchy child (subsystem / subdeployment) from the cluster */
function navigateToChild(childId: string) {
  if (!props.activeId || !selfChildRelation.value) return
  router.push({
    path: `/explore/${props.activeType}`,
    query: {
      parentType: props.activeType,
      parentId: props.activeId,
      relation: selfChildRelation.value,
      resourceId: childId,
    },
  })
}

/** Browse all self-hierarchy children via the nested list */
function browseAllChildren() {
  if (!props.activeId || !selfChildRelation.value) return
  router.push({
    path: `/explore/${props.activeType}`,
    query: {
      parentType: props.activeType,
      parentId: props.activeId,
      relation: selfChildRelation.value,
    },
  })
}
</script>

<template>
  <div class="diagram-container">
    <svg
      :viewBox="'-5 -15 810 ' + svgViewBoxHeight"
      xmlns="http://www.w3.org/2000/svg"
      class="model-svg"
      :style="svgViewBoxHeight > 480 ? { maxHeight: '400px' } : {}"
    >
      <defs>
        <!-- Arrowhead marker -->
        <marker id="arrow" viewBox="0 0 10 7" refX="9" refY="3.5"
          markerWidth="8" markerHeight="6" orient="auto-start-reverse">
          <path d="M 0 0 L 10 3.5 L 0 7 Z" fill="#94a3b8" />
        </marker>
        <marker id="arrow-active" viewBox="0 0 10 7" refX="9" refY="3.5"
          markerWidth="8" markerHeight="6" orient="auto-start-reverse">
          <path d="M 0 0 L 10 3.5 L 0 7 Z" fill="#0ea5e9" />
        </marker>

        <!-- Glow filter for active node -->
        <filter id="glow" x="-30%" y="-30%" width="160%" height="160%">
          <feGaussianBlur stdDeviation="4" result="blur" />
          <feMerge>
            <feMergeNode in="blur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>

      <!-- Background partition labels -->
      <text x="180" y="415" class="partition-label">Part 1 — Features</text>
      <text x="590" y="415" class="partition-label">Part 2 — Obs &amp; Cmd</text>
      <line x1="430" y1="10" x2="430" y2="400" stroke="#e2e8f0" stroke-width="1" stroke-dasharray="6 4" />

      <!-- Edges (rendered first so nodes are on top) -->
      <g v-for="edge in edges" :key="`${edge.from}-${edge.to}-${edge.label}`">
        <title>{{ edge.tooltip }}</title>
        <path
          :d="edgePath(edge)"
          :stroke="isEdgeActive(edge) ? '#0ea5e9' : '#cbd5e1'"
          :stroke-width="isEdgeActive(edge) ? 2 : 1.2"
          :stroke-dasharray="edge.style === 'dashed' ? '5 3' : 'none'"
          fill="none"
          :marker-end="isEdgeActive(edge) ? 'url(#arrow-active)' : 'url(#arrow)'"
          :opacity="isConnected(edge.from) || isConnected(edge.to) ? 1 : 0.4"
        />
        <text
          :x="edgeLabelPos(edge).x"
          :y="edgeLabelPos(edge).y"
          class="edge-label"
          :class="{ 'edge-active': isEdgeActive(edge) }"
          text-anchor="middle"
        >{{ edge.label }}</text>
      </g>

      <!-- ══════════════════════════════════════════════════════════
           Parent Node — shown when the active resource is a child
           in a self-hierarchy (subsystem or subdeployment).
           ══════════════════════════════════════════════════════════ -->
      <template v-if="sameTypeParent && activeNodeDef">
        <!-- Hierarchical edge: parent → active node -->
        <path
          :d="`M ${PARENT_NODE.x + PARENT_NODE.w / 2} ${PARENT_NODE.y + PARENT_NODE.h / 2 + 4}
               C ${PARENT_NODE.x + PARENT_NODE.w / 2 + 40} ${PARENT_NODE.y + 80},
                 ${activeNodeDef.x - 60} ${activeNodeDef.y - 80},
                 ${activeNodeDef.x - NODE_W/2 + 10} ${activeNodeDef.y - 6}`"
          :stroke="activeNodeDef.color"
          stroke-width="2.5"
          stroke-dasharray="6 3"
          fill="none"
          marker-end="url(#arrow-active)"
          opacity="0.8"
        />
        <text
          :x="(PARENT_NODE.x + PARENT_NODE.w / 2 + activeNodeDef.x) / 2 - 30"
          :y="(PARENT_NODE.y + PARENT_NODE.h / 2 + activeNodeDef.y) / 2 - 25"
          class="edge-label edge-active"
          text-anchor="middle"
          font-size="9"
        >{{ props.activeType === 'deployments' ? 'subdeployment of' : 'subsystem of' }}</text>

        <!-- Parent node card -->
        <g class="node-group node-connected parent-node-group" @click="navigateToParent()">
          <title>Navigate to parent: {{ parentName || sameTypeParent!.resourceId }}</title>
          <!-- Shadow -->
          <rect
            :x="PARENT_NODE.x + 2" :y="PARENT_NODE.y + 2"
            :width="PARENT_NODE.w" :height="PARENT_NODE.h"
            :rx="NODE_RX" fill="rgba(0,0,0,0.06)"
          />
          <!-- Background -->
          <rect
            :x="PARENT_NODE.x" :y="PARENT_NODE.y"
            :width="PARENT_NODE.w" :height="PARENT_NODE.h"
            :rx="NODE_RX"
            fill="#f8fafc"
            :stroke="activeNodeDef.color"
            stroke-width="2"
            stroke-dasharray="4 2"
          />
          <!-- Icon -->
          <text
            :x="PARENT_NODE.x + 14" :y="PARENT_NODE.y + PARENT_NODE.h / 2"
            class="node-icon" :fill="activeNodeDef.color" dominant-baseline="central"
          >{{ activeNodeDef.icon }}</text>
          <!-- Role label -->
          <text
            :x="PARENT_NODE.x + 30" :y="PARENT_NODE.y + 14"
            class="parent-node-role" fill="#64748b" dominant-baseline="central"
          >{{ props.activeType === 'deployments' ? 'Parent Deployment' : 'Parent System' }}</text>
          <!-- Name (truncated) -->
          <text
            :x="PARENT_NODE.x + 30" :y="PARENT_NODE.y + 30"
            class="parent-node-name" fill="#334155" dominant-baseline="central"
          >{{ (parentName || sameTypeParent!.resourceId).substring(0, 22) }}{{ (parentName || sameTypeParent!.resourceId).length > 22 ? '…' : '' }}</text>
          <!-- Navigate arrow -->
          <text
            :x="PARENT_NODE.x + PARENT_NODE.w - 18" :y="PARENT_NODE.y + PARENT_NODE.h / 2"
            :fill="activeNodeDef.color" font-size="11" dominant-baseline="central"
          >↗</text>
        </g>
      </template>

      <!-- ══════════════════════════════════════════════════════════
           Self-Hierarchy Cluster — shown when the active resource
           has children of the same type (subsystems / subdeployments).
           ══════════════════════════════════════════════════════════ -->
      <template v-if="selfClusterConfig">
        <!-- Branching line from self-loop arc down to cluster -->
        <path
          :d="`M ${selfClusterConfig.nodeX} ${selfClusterConfig.nodeY + NODE_H/2 + 50}
               L ${selfClusterConfig.nodeX} ${selfClusterConfig.startY - 6}`"
          :stroke="selfClusterConfig.color"
          stroke-width="1.5"
          stroke-dasharray="4 2"
          fill="none"
          opacity="0.6"
        />

        <!-- Cluster background card -->
        <rect
          :x="selfClusterConfig.x - 6"
          :y="selfClusterConfig.startY - 8"
          :width="selfClusterConfig.chipW + 12"
          :height="Math.min(selfChildItems.length, selfClusterConfig.maxShow) * (selfClusterConfig.chipH + selfClusterConfig.gap) + (selfChildTotal > selfClusterConfig.maxShow ? 22 : 6) + 10"
          rx="8"
          fill="#f8fafc"
          stroke="#e2e8f0"
          stroke-width="1"
          opacity="0.85"
        />

        <!-- Child chips -->
        <g
          v-for="(child, idx) in selfChildItems.slice(0, selfClusterConfig.maxShow)"
          :key="child.id"
          class="subsystem-chip-group"
          @click.stop="navigateToChild(child.id)"
        >
          <title>{{ child.name }} ({{ child.id }})</title>
          <rect
            :x="selfClusterConfig.x"
            :y="selfClusterConfig.startY + idx * (selfClusterConfig.chipH + selfClusterConfig.gap)"
            :width="selfClusterConfig.chipW"
            :height="selfClusterConfig.chipH"
            rx="5"
            fill="#ffffff"
            :stroke="selfClusterConfig.color"
            stroke-width="1.2"
            class="subsystem-chip-bg"
          />
          <!-- Icon -->
          <text
            :x="selfClusterConfig.x + 10"
            :y="selfClusterConfig.startY + idx * (selfClusterConfig.chipH + selfClusterConfig.gap) + selfClusterConfig.chipH / 2"
            :fill="selfClusterConfig.color" font-size="8" dominant-baseline="central"
          >{{ selfClusterConfig.icon }}</text>
          <!-- Name (truncated) -->
          <text
            :x="selfClusterConfig.x + 22"
            :y="selfClusterConfig.startY + idx * (selfClusterConfig.chipH + selfClusterConfig.gap) + selfClusterConfig.chipH / 2"
            class="subsystem-chip-label" dominant-baseline="central"
          >{{ child.name.length > 24 ? child.name.substring(0, 24) + '…' : child.name }}</text>
          <!-- Drill-in arrow -->
          <text
            :x="selfClusterConfig.x + selfClusterConfig.chipW - 14"
            :y="selfClusterConfig.startY + idx * (selfClusterConfig.chipH + selfClusterConfig.gap) + selfClusterConfig.chipH / 2"
            fill="#38bdf8" font-size="8" dominant-baseline="central" class="chip-arrow"
          >→</text>
        </g>

        <!-- "View all N →" link when there are more -->
        <g v-if="selfChildTotal > selfClusterConfig.maxShow" class="subsystem-chip-group" @click.stop="browseAllChildren()">
          <text
            :x="selfClusterConfig.x + selfClusterConfig.chipW / 2"
            :y="selfClusterConfig.startY + selfClusterConfig.maxShow * (selfClusterConfig.chipH + selfClusterConfig.gap) + 8"
            text-anchor="middle" dominant-baseline="central"
            class="subsystem-more-link"
          >View all {{ selfChildTotal }} {{ selfClusterConfig.relation }} →</text>
        </g>
      </template>

      <!-- Nodes -->
      <g
        v-for="node in nodes"
        :key="node.id"
        class="node-group"
        :class="{
          'node-active': isActive(node.id),
          'node-connected': !isActive(node.id) && isConnected(node.id),
          'node-dimmed': !isConnected(node.id),
        }"
        @click="navigateToType(node.id)"
      >
        <!-- Stacked card effect for hierarchical (self-referencing) nodes -->
        <template v-if="hasSelfLoop(node.id)">
          <rect
            :x="node.x - NODE_W/2 + 6"
            :y="node.y - NODE_H/2 + 6"
            :width="NODE_W"
            :height="NODE_H"
            :rx="NODE_RX"
            :fill="isActive(node.id) ? node.color : '#f8fafc'"
            :stroke="isActive(node.id) ? node.color : isConnected(node.id) ? node.color : '#e2e8f0'"
            :stroke-width="0.8"
            :opacity="isActive(node.id) ? 0.4 : 0.5"
          />
          <rect
            :x="node.x - NODE_W/2 + 3"
            :y="node.y - NODE_H/2 + 3"
            :width="NODE_W"
            :height="NODE_H"
            :rx="NODE_RX"
            :fill="isActive(node.id) ? node.color : '#f8fafc'"
            :stroke="isActive(node.id) ? node.color : isConnected(node.id) ? node.color : '#e2e8f0'"
            :stroke-width="0.8"
            :opacity="isActive(node.id) ? 0.6 : 0.7"
          />
        </template>
        <!-- Shadow -->
        <rect
          :x="node.x - NODE_W/2 + 2"
          :y="node.y - NODE_H/2 + 2"
          :width="NODE_W"
          :height="NODE_H"
          :rx="NODE_RX"
          fill="rgba(0,0,0,0.08)"
        />
        <!-- Card background -->
        <rect
          :x="node.x - NODE_W/2"
          :y="node.y - NODE_H/2"
          :width="NODE_W"
          :height="NODE_H"
          :rx="NODE_RX"
          :fill="isActive(node.id) ? node.color : '#ffffff'"
          :stroke="isActive(node.id) ? node.color : isConnected(node.id) ? node.color : '#e2e8f0'"
          :stroke-width="isActive(node.id) ? 2.5 : isConnected(node.id) ? 2 : 1"
          :filter="isActive(node.id) ? 'url(#glow)' : ''"
        />
        <!-- Icon -->
        <text
          :x="node.x - NODE_W/2 + 16"
          :y="node.y + 1"
          class="node-icon"
          :fill="isActive(node.id) ? '#ffffff' : node.color"
          dominant-baseline="central"
        >{{ node.icon }}</text>
        <!-- Label -->
        <text
          :x="node.x + 6"
          :y="node.y - 4"
          class="node-label"
          :fill="isActive(node.id) ? '#ffffff' : '#334155'"
          dominant-baseline="central"
        >{{ node.label }}</text>
        <!-- Part badge -->
        <text
          :x="node.x + 6"
          :y="node.y + 14"
          class="node-part"
          :fill="isActive(node.id) ? 'rgba(255,255,255,0.7)' : '#94a3b8'"
          dominant-baseline="central"
        >Part {{ node.part }}</text>

        <!-- Count badge -->
        <g v-if="counts[node.id] !== undefined" class="count-badge-group">
          <rect
            :x="node.x + NODE_W/2 - 28"
            :y="node.y - NODE_H/2 - 7"
            :width="Math.max(22, formatCount(counts[node.id]).length * 8 + 8)"
            height="16"
            rx="8"
            :fill="counts[node.id] == null ? '#e2e8f0' : counts[node.id]! < 0 ? '#f1f5f9' : counts[node.id] === 0 ? '#f8fafc' : node.color"
            :stroke="counts[node.id] != null && counts[node.id]! > 0 ? node.color : '#cbd5e1'"
            stroke-width="1"
          />
          <text
            :x="node.x + NODE_W/2 - 28 + Math.max(22, formatCount(counts[node.id]).length * 8 + 8) / 2"
            :y="node.y - NODE_H/2 + 1"
            text-anchor="middle"
            dominant-baseline="central"
            class="count-label"
            :fill="counts[node.id] != null && counts[node.id]! > 0 ? '#ffffff' : '#94a3b8'"
          >{{ formatCount(counts[node.id]) }}</text>
        </g>
      </g>
    </svg>

    <!-- Legend -->
    <div class="legend">
      <span class="legend-item">
        <span class="legend-swatch legend-active"></span> Current resource
      </span>
      <span class="legend-item">
        <span class="legend-swatch legend-connected"></span> Directly related
      </span>
      <span class="legend-item">
        <svg width="30" height="10"><line x1="0" y1="5" x2="30" y2="5" stroke="#94a3b8" stroke-width="1.5" /></svg>
        Relationship
      </span>
      <span class="legend-item">
        <svg width="30" height="10"><line x1="0" y1="5" x2="30" y2="5" stroke="#94a3b8" stroke-width="1.5" stroke-dasharray="4 2" /></svg>
        Hierarchy / optional
      </span>
      <span class="legend-item">
        <svg width="22" height="16" viewBox="0 0 22 16">
          <rect x="4" y="4" width="14" height="10" rx="2" fill="#f8fafc" stroke="#94a3b8" stroke-width="0.8" opacity="0.5" />
          <rect x="2" y="2" width="14" height="10" rx="2" fill="#f8fafc" stroke="#94a3b8" stroke-width="0.8" opacity="0.7" />
          <rect x="0" y="0" width="14" height="10" rx="2" fill="#fff" stroke="#94a3b8" stroke-width="1" />
        </svg>
        Can nest children
      </span>
    </div>
  </div>
</template>

<style scoped>
.diagram-container {
  background: #fafbfc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 0.5rem;
  overflow: hidden;
}
.model-svg {
  width: 100%;
  height: auto;
  max-height: 360px;
}

/* Node interactivity */
.node-group {
  cursor: pointer;
  transition: opacity 0.2s;
}
.node-group:hover rect:nth-child(2) {
  filter: brightness(0.95);
}
.node-active { cursor: default; }
.node-dimmed { opacity: 0.45; cursor: default; }
.node-dimmed:hover { opacity: 0.7; }

/* Text styles */
.node-label {
  font-size: 11px;
  font-weight: 600;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}
.node-icon {
  font-size: 16px;
}
.node-part {
  font-size: 8.5px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}
/* Count badge */
.count-badge-group {
  pointer-events: none;
}
.count-label {
  font-size: 8px;
  font-weight: 700;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

.edge-label {
  font-size: 8.5px;
  fill: #94a3b8;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  font-style: italic;
}
.edge-active {
  fill: #0ea5e9;
  font-weight: 600;
}
.partition-label {
  font-size: 10px;
  fill: #cbd5e1;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  font-weight: 600;
  text-anchor: middle;
  text-transform: uppercase;
  letter-spacing: 1.5px;
}

/* Legend */
.legend {
  display: flex;
  gap: 1rem;
  justify-content: center;
  padding: 0.35rem 0 0.15rem;
  flex-wrap: wrap;
}
.legend-item {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  font-size: 0.7rem;
  color: #64748b;
}
.legend-swatch {
  width: 10px;
  height: 10px;
  border-radius: 3px;
  display: inline-block;
}
.legend-active {
  background: #0ea5e9;
  box-shadow: 0 0 4px rgba(14, 165, 233, 0.5);
}
.legend-connected {
  background: #ffffff;
  border: 2px solid #0ea5e9;
}

/* Parent node text */
.parent-node-role {
  font-size: 8px;
  font-weight: 600;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.parent-node-name {
  font-size: 10.5px;
  font-weight: 700;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}
.parent-node-group:hover rect:nth-child(2) {
  fill: #e0f2fe;
}

/* Subsystem cluster chips */
.subsystem-chip-group {
  cursor: pointer;
}
.subsystem-chip-bg {
  transition: fill 0.12s, stroke-width 0.12s;
}
.subsystem-chip-group:hover .subsystem-chip-bg {
  fill: #e0f2fe;
  stroke-width: 2;
}
.subsystem-chip-label {
  font-size: 9px;
  font-weight: 600;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  fill: #0c4a6e;
}
.chip-arrow {
  opacity: 0;
  transition: opacity 0.12s;
}
.subsystem-chip-group:hover .chip-arrow {
  opacity: 1;
}
.subsystem-more-link {
  font-size: 8.5px;
  font-weight: 700;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  fill: #0369a1;
  cursor: pointer;
}
.subsystem-more-link:hover {
  fill: #0284c7;
  text-decoration: underline;
}
</style>
