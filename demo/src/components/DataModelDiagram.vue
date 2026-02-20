<script setup lang="ts">
import { computed, reactive, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { apiFetch } from '../api'
import { getListUrl } from '../csapi-bridge'
import { connection } from '../state'

const router = useRouter()

const props = defineProps<{
  /** The resource type currently being viewed */
  activeType: string
  /** The resource ID currently being viewed (for navigation context) */
  activeId?: string
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
  { from: 'systems',    to: 'procedures',       label: 'implements',       style: 'solid' },
  { from: 'systems',    to: 'deployments',       label: 'deployedIn',       style: 'solid' },
  { from: 'systems',    to: 'samplingFeatures',  label: 'samples',          style: 'solid' },
  { from: 'systems',    to: 'datastreams',       label: 'outputs',          style: 'solid' },
  { from: 'systems',    to: 'controlStreams',    label: 'controls',         style: 'solid' },
  { from: 'systems',    to: 'systems',           label: 'subsystems',       style: 'dashed' },

  // Deployment self-reference
  { from: 'deployments', to: 'deployments',      label: 'subdeployments',   style: 'dashed' },

  // Part 2 chains
  { from: 'datastreams',    to: 'observations',  label: 'produces',         style: 'solid' },
  { from: 'controlStreams', to: 'commands',       label: 'receives',         style: 'solid' },

  // Property links
  { from: 'datastreams',    to: 'properties',    label: 'observes',         style: 'dashed' },
  { from: 'controlStreams', to: 'properties',     label: 'controls',         style: 'dashed' },
]

const NODE_RX = 12
const NODE_W = 130
const NODE_H = 52

/** Find a node by id */
function findNode(id: string): ModelNode | undefined {
  return nodes.find(n => n.id === id)
}

/** Which nodes are directly connected to the active type? */
const connectedNodeIds = computed<Set<string>>(() => {
  const set = new Set<string>()
  set.add(props.activeType)
  for (const e of edges) {
    if (e.from === props.activeType) set.add(e.to)
    if (e.to === props.activeType) set.add(e.from)
  }
  return set
})

/** Is this node the actively viewed resource? */
function isActive(nodeId: string) {
  return nodeId === props.activeType
}

/** Is this node connected to the active resource? */
function isConnected(nodeId: string) {
  return connectedNodeIds.value.has(nodeId)
}

/** Is this edge connected to the active type? */
function isEdgeActive(edge: ModelEdge) {
  return edge.from === props.activeType || edge.to === props.activeType
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

// ─── Live Resource Counts ─────────────────────────────────────────

/** Map of resource-type key → count (null = loading, -1 = unavailable/error) */
const counts = reactive<Record<string, number | null>>({})
let fetchGeneration = 0

async function fetchCounts() {
  const gen = ++fetchGeneration
  // Reset all to loading
  for (const n of nodes) counts[n.id] = null

  // Fire all requests in parallel
  const requests = nodes.map(async (n) => {
    try {
      const path = getListUrl(n.id, { limit: 0 })
      const res = await apiFetch(path)
      if (gen !== fetchGeneration) return  // stale
      if (!res.ok) {
        counts[n.id] = -1
        return
      }
      // Try numberMatched (GeoJSON/SWE collections), then items array length
      const data = res.data
      if (data?.numberMatched != null) {
        counts[n.id] = data.numberMatched
      } else if (Array.isArray(data?.items)) {
        // If limit=0 but server still returns items array, count is the numberMatched or items length
        counts[n.id] = data.items.length
      } else if (Array.isArray(data?.features)) {
        counts[n.id] = data.features.length
      } else {
        // Server returned OK but no recognizable count — mark available but unknown
        counts[n.id] = -1
      }
    } catch {
      if (gen !== fetchGeneration) return
      counts[n.id] = -1
    }
  })
  await Promise.allSettled(requests)
}

function formatCount(n: number | null | undefined): string {
  if (n == null) return '…'         // loading
  if (n < 0) return '—'             // unavailable
  if (n >= 10000) return `${(n / 1000).toFixed(0)}k`
  if (n >= 1000) return `${(n / 1000).toFixed(1)}k`
  return String(n)
}

onMounted(() => {
  if (connection.connected) fetchCounts()
})

watch(() => connection.connected, (c) => {
  if (c) fetchCounts()
})

/** Navigate to a resource type in the explorer */
function navigateToType(nodeId: string) {
  // If it's the active type, do nothing
  if (nodeId === props.activeType) return

  // Check if this is a related resource that should be browsed as nested
  const isRelated = edges.some(
    e => (e.from === props.activeType && e.to === nodeId) ||
         (e.to === props.activeType && e.from === nodeId)
  )

  if (isRelated && props.activeId) {
    // Navigate to nested resource list under this parent
    const relation = edges.find(
      e => e.from === props.activeType && e.to === nodeId
    )
    if (relation) {
      router.push({
        path: `/explore/${nodeId}`,
        query: {
          parentType: props.activeType,
          parentId: props.activeId,
          relation: relation.label === 'subsystems' ? 'subsystems'
                  : relation.label === 'subdeployments' ? 'subdeployments'
                  : nodeId,
        },
      })
      return
    }
  }

  // Default: navigate to that resource type's list
  router.push({ path: `/explore/${nodeId}` })
}
</script>

<template>
  <div class="diagram-container">
    <svg
      viewBox="-5 -15 810 450"
      xmlns="http://www.w3.org/2000/svg"
      class="model-svg"
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
        Self/optional
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
.node-dimmed { opacity: 0.45; }
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
</style>
