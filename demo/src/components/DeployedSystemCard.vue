<script setup lang="ts">
/**
 * DeployedSystemCard.vue
 *
 * Rich details card for deployment resources that represent deployed-system leaves.
 * Follows the OS4CSAPI Deployed System Card Field Mapping Spec v1.
 *
 * Card sections:
 *   1. Header — title, subtitle, role/status/kind badges
 *   2. Summary — one-sentence operational summary
 *   3. Context — deployment path, type, geometry
 *   4. Occupant — system identity, kind, manufacturer/model, owner
 *   5. Outputs & Methods — datastreams, procedures, capabilities
 *   6. Freshness / Trust — latest activity, quality
 *   7. Media / References — docs, links
 *   8. Advanced IDs — collapsed by default
 */
import { computed } from 'vue'
import type { DeployedSystemCardModel } from '../composables/useDeployedSystemCard'

const props = defineProps<{
  card: DeployedSystemCardModel
  loading?: boolean
}>()

const emit = defineEmits<{
  (e: 'explore'): void
  (e: 'close'): void
}>()

// Badges to show (filter out empty ones)
const badges = computed(() => {
  const b: Array<{ label: string; color: string; icon?: string }> = []
  if (props.card.roleBadge) {
    b.push({ label: props.card.roleBadge, color: '#3b82f6' })
  }
  if (props.card.statusBadge) {
    const statusColor = /active|healthy|online/i.test(props.card.statusBadge) ? '#22c55e'
      : /degraded|stale/i.test(props.card.statusBadge) ? '#f59e0b'
      : /inactive|offline/i.test(props.card.statusBadge) ? '#ef4444'
      : '#64748b'
    b.push({ label: props.card.statusBadge, color: statusColor })
  }
  if (props.card.kindBadge) {
    b.push({ label: props.card.kindBadge, color: '#8b5cf6' })
  }
  return b
})

const hasContext = computed(() =>
  props.card.deploymentPath || props.card.deploymentType || props.card.geometrySummary
)

const hasOccupant = computed(() =>
  props.card.occupantName && props.card.occupantName !== 'Unknown Occupant'
)

const hasOutputs = computed(() =>
  props.card.primaryDatastreams.length > 0 ||
  props.card.primaryProcedures.length > 0 ||
  props.card.capabilities.length > 0
)

const hasFreshness = computed(() =>
  props.card.latestActivityRelative || props.card.qualitySummary || props.card.healthState
)

const hasDocs = computed(() =>
  props.card.docsLinks.length > 0 || props.card.mediaLinks.length > 0
)
</script>

<template>
  <div class="dsc" :class="{ 'dsc--loading': loading }">
    <!-- ═══ Loading overlay ═══ -->
    <div v-if="loading" class="dsc-loading">
      <i class="pi pi-spin pi-spinner"></i>
      <span>Loading system details…</span>
    </div>

    <!-- ═══ 1. HEADER ═══ -->
    <div class="dsc-header">
      <div class="dsc-header-top">
        <div class="dsc-icon-area">
          <img v-if="card.thumbnail" :src="card.thumbnail" class="dsc-thumbnail" alt="" />
          <div v-else class="dsc-icon-placeholder">
            <i class="pi pi-map"></i>
          </div>
        </div>
        <div class="dsc-title-area">
          <div class="dsc-title">{{ card.title }}</div>
          <div v-if="card.subtitle" class="dsc-subtitle">{{ card.subtitle }}</div>
        </div>
      </div>
      <div v-if="badges.length" class="dsc-badges">
        <span
          v-for="(badge, i) in badges"
          :key="i"
          class="dsc-badge"
          :style="{ backgroundColor: badge.color + '18', color: badge.color, borderColor: badge.color + '40' }"
        >
          {{ badge.label }}
        </span>
      </div>
    </div>

    <!-- ═══ 2. SUMMARY ═══ -->
    <p v-if="card.summarySentence" class="dsc-summary">
      {{ card.summarySentence }}
    </p>

    <!-- ═══ 3. CONTEXT ═══ -->
    <div v-if="hasContext" class="dsc-section">
      <div class="dsc-section-label">
        <i class="pi pi-sitemap"></i> Context
      </div>
      <div v-if="card.deploymentPath" class="dsc-field">
        <span class="dsc-field-label">Path</span>
        <span class="dsc-path">{{ card.deploymentPath }}</span>
      </div>
      <div v-if="card.deploymentType" class="dsc-field">
        <span class="dsc-field-label">Type</span>
        <span class="dsc-chip dsc-chip--muted">{{ card.deploymentType }}</span>
      </div>
      <div v-if="card.geometrySummary" class="dsc-field">
        <span class="dsc-field-label">Geometry</span>
        {{ card.geometrySummary }}
      </div>
    </div>

    <!-- ═══ 4. OCCUPANT ═══ -->
    <div v-if="hasOccupant" class="dsc-section">
      <div class="dsc-section-label">
        <i class="pi pi-server"></i> Occupant System
      </div>
      <div class="dsc-field">
        <span class="dsc-field-label">Name</span>
        {{ card.occupantName }}
      </div>
      <div v-if="card.occupantKind && card.occupantKind !== 'Unknown Kind'" class="dsc-field">
        <span class="dsc-field-label">Kind</span>
        {{ card.occupantKind }}
      </div>
      <div v-if="card.manufacturerModelOrVersion" class="dsc-field">
        <span class="dsc-field-label">Model / Version</span>
        {{ card.manufacturerModelOrVersion }}
      </div>
      <div v-if="card.ownerMaintainer" class="dsc-field">
        <span class="dsc-field-label">Owner</span>
        {{ card.ownerMaintainer }}
      </div>
    </div>

    <!-- ═══ 5. OUTPUTS & METHODS ═══ -->
    <div v-if="hasOutputs || card.primaryPurpose" class="dsc-section">
      <div class="dsc-section-label">
        <i class="pi pi-chart-line"></i> Outputs & Methods
      </div>

      <!-- Purpose -->
      <div v-if="card.primaryPurpose && card.primaryPurpose !== 'Purpose not documented'" class="dsc-field">
        <span class="dsc-field-label">Purpose</span>
        {{ card.primaryPurpose }}
      </div>

      <!-- Capabilities -->
      <div v-if="card.capabilities.length" class="dsc-field">
        <span class="dsc-field-label">Capabilities</span>
        <div class="dsc-chips">
          <span v-for="cap in card.capabilities" :key="cap" class="dsc-chip">
            {{ cap }}
          </span>
        </div>
      </div>

      <!-- Datastreams -->
      <div v-if="card.primaryDatastreams.length" class="dsc-field">
        <span class="dsc-field-label">Data Products</span>
        <div class="dsc-ds-list">
          <div v-for="ds in card.primaryDatastreams" :key="ds.id" class="dsc-ds-item">
            <i class="pi pi-chart-line dsc-ds-icon"></i>
            <div class="dsc-ds-info">
              <div class="dsc-ds-name">{{ ds.name }}</div>
              <div v-if="ds.observedProperties.length" class="dsc-ds-props">
                {{ ds.observedProperties.slice(0, 4).join(', ') }}
                <span v-if="ds.observedProperties.length > 4" class="dsc-muted">
                  +{{ ds.observedProperties.length - 4 }} more
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div v-else class="dsc-empty">No public data products</div>

      <!-- Procedures -->
      <div v-if="card.primaryProcedures.length" class="dsc-field">
        <span class="dsc-field-label">Methods</span>
        <div v-for="proc in card.primaryProcedures" :key="proc.id" class="dsc-proc-item">
          <i class="pi pi-cog dsc-proc-icon"></i>
          <div>
            <div class="dsc-proc-name">{{ proc.name }}</div>
            <div v-if="proc.description" class="dsc-proc-desc">{{ proc.description }}</div>
          </div>
        </div>
      </div>

      <!-- Control streams -->
      <div v-if="card.controlStreamCount > 0" class="dsc-field">
        <span class="dsc-field-label">Control Streams</span>
        <span class="dsc-chip dsc-chip--muted">{{ card.controlStreamCount }} available</span>
      </div>
    </div>

    <!-- ═══ 6. FRESHNESS / TRUST ═══ -->
    <div v-if="hasFreshness" class="dsc-section">
      <div class="dsc-section-label">
        <i class="pi pi-clock"></i> Freshness
      </div>
      <div class="dsc-freshness-row">
        <div v-if="card.latestActivityRelative" class="dsc-field">
          <span class="dsc-field-label">Last Activity</span>
          <span class="dsc-freshness-value">
            {{ card.latestActivityRelative }}
            <span v-if="card.latestActivityTime" class="dsc-muted"> · {{ card.latestActivityTime }}</span>
          </span>
        </div>
        <div v-if="card.qualitySummary" class="dsc-field">
          <span class="dsc-field-label">Quality</span>
          {{ card.qualitySummary }}
        </div>
        <div v-if="card.healthState" class="dsc-field">
          <span class="dsc-field-label">Health</span>
          {{ card.healthState }}
        </div>
        <div v-if="card.contributingSources" class="dsc-field">
          <span class="dsc-field-label">Sources</span>
          {{ card.contributingSources }}
        </div>
      </div>
    </div>

    <!-- ═══ 7. MEDIA / REFERENCES ═══ -->
    <div v-if="hasDocs" class="dsc-section">
      <div class="dsc-section-label">
        <i class="pi pi-link"></i> References
      </div>
      <div v-for="doc in card.docsLinks" :key="doc.href" class="dsc-doc-link">
        <a v-if="doc.href" :href="doc.href" target="_blank" rel="noopener">
          <i class="pi pi-external-link"></i> {{ doc.title }}
        </a>
        <span v-else>{{ doc.title }}</span>
        <span v-if="doc.role" class="dsc-muted"> · {{ doc.role }}</span>
      </div>
      <div v-if="card.mediaLinks.length" class="dsc-media-row">
        <a
          v-for="ml in card.mediaLinks"
          :key="ml.href"
          :href="ml.href"
          target="_blank"
          rel="noopener"
          class="dsc-media-thumb"
        >
          <img :src="ml.href" :alt="ml.title" />
        </a>
      </div>
    </div>

    <!-- ═══ ACTION BUTTONS ═══ -->
    <div class="dsc-actions">
      <button class="dsc-btn dsc-btn--primary" @click="emit('explore')">
        <i class="pi pi-external-link"></i> View in Explorer
      </button>
    </div>

    <!-- ═══ 8. ADVANCED IDs (collapsed) ═══ -->
    <details class="dsc-advanced">
      <summary>Advanced IDs</summary>
      <div class="dsc-advanced-body">
        <div v-if="card.advancedDeploymentId" class="dsc-adv-field">
          <span class="dsc-adv-label">Deployment ID</span>
          <code>{{ card.advancedDeploymentId }}</code>
        </div>
        <div v-if="card.advancedDeploymentUid" class="dsc-adv-field">
          <span class="dsc-adv-label">Deployment UID</span>
          <code>{{ card.advancedDeploymentUid }}</code>
        </div>
        <div v-if="card.advancedSystemId" class="dsc-adv-field">
          <span class="dsc-adv-label">System ID</span>
          <code>{{ card.advancedSystemId }}</code>
        </div>
        <div v-if="card.advancedSystemUid" class="dsc-adv-field">
          <span class="dsc-adv-label">System UID</span>
          <code>{{ card.advancedSystemUid }}</code>
        </div>
        <div v-if="card.advancedBootstrapOwner" class="dsc-adv-field">
          <span class="dsc-adv-label">Bootstrap Owner</span>
          <code>{{ card.advancedBootstrapOwner }}</code>
        </div>
        <div v-if="card.advancedSourceOfTruth" class="dsc-adv-field">
          <span class="dsc-adv-label">Source of Truth</span>
          <code>{{ card.advancedSourceOfTruth }}</code>
        </div>
      </div>
    </details>
  </div>
</template>

<style scoped>
/* ═══ Root ═══ */
.dsc {
  font-size: 0.84rem;
  color: #1e293b;
  line-height: 1.45;
  position: relative;
}

.dsc--loading {
  opacity: 0.6;
  pointer-events: none;
}

.dsc-loading {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0;
  color: #64748b;
  font-size: 0.82rem;
}

/* ═══ Header ═══ */
.dsc-header {
  margin-bottom: 0.5rem;
}

.dsc-header-top {
  display: flex;
  gap: 0.6rem;
  align-items: flex-start;
}

.dsc-icon-area {
  flex-shrink: 0;
  width: 36px;
  height: 36px;
}

.dsc-thumbnail {
  width: 36px;
  height: 36px;
  border-radius: 6px;
  object-fit: cover;
}

.dsc-icon-placeholder {
  width: 36px;
  height: 36px;
  background: #dbeafe;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #3b82f6;
  font-size: 1rem;
}

.dsc-title-area {
  flex: 1;
  min-width: 0;
}

.dsc-title {
  font-weight: 700;
  font-size: 0.95rem;
  color: #0f172a;
  line-height: 1.2;
}

.dsc-subtitle {
  font-size: 0.82rem;
  color: #64748b;
  margin-top: 1px;
}

/* ═══ Badges ═══ */
.dsc-badges {
  display: flex;
  flex-wrap: wrap;
  gap: 0.3rem;
  margin-top: 0.4rem;
}

.dsc-badge {
  display: inline-flex;
  align-items: center;
  font-size: 0.72rem;
  font-weight: 600;
  padding: 0.15rem 0.45rem;
  border-radius: 999px;
  border: 1px solid;
  white-space: nowrap;
  letter-spacing: 0.01em;
}

/* ═══ Summary ═══ */
.dsc-summary {
  margin: 0.4rem 0 0.6rem;
  padding: 0.45rem 0.55rem;
  background: #f0f9ff;
  border-left: 3px solid #3b82f6;
  border-radius: 0 6px 6px 0;
  font-size: 0.82rem;
  color: #1e40af;
  line-height: 1.45;
}

/* ═══ Sections ═══ */
.dsc-section {
  margin-bottom: 0.6rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid #f1f5f9;
}

.dsc-section:last-of-type {
  border-bottom: none;
}

.dsc-section-label {
  font-size: 0.72rem;
  font-weight: 700;
  color: #94a3b8;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  margin-bottom: 0.35rem;
  display: flex;
  align-items: center;
  gap: 0.3rem;
}

.dsc-section-label i {
  font-size: 0.72rem;
}

/* ═══ Fields ═══ */
.dsc-field {
  margin-bottom: 0.3rem;
}

.dsc-field-label {
  font-size: 0.75rem;
  font-weight: 600;
  color: #64748b;
  display: block;
  margin-bottom: 0.05rem;
}

.dsc-path {
  font-size: 0.78rem;
  color: #475569;
  word-break: break-word;
}

.dsc-muted {
  color: #94a3b8;
  font-size: 0.78rem;
}

.dsc-empty {
  font-size: 0.8rem;
  color: #94a3b8;
  font-style: italic;
  margin: 0.2rem 0;
}

/* ═══ Chips ═══ */
.dsc-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem;
  margin-top: 0.15rem;
}

.dsc-chip {
  display: inline-flex;
  align-items: center;
  font-size: 0.72rem;
  padding: 0.15rem 0.4rem;
  border-radius: 4px;
  background: #eff6ff;
  color: #1e40af;
  border: 1px solid #bfdbfe;
  white-space: nowrap;
}

.dsc-chip--muted {
  background: #f1f5f9;
  color: #64748b;
  border-color: #e2e8f0;
}

/* ═══ Datastream list ═══ */
.dsc-ds-list {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
  margin-top: 0.2rem;
}

.dsc-ds-item {
  display: flex;
  gap: 0.4rem;
  align-items: flex-start;
  padding: 0.3rem 0.4rem;
  background: #fafbfc;
  border: 1px solid #f1f5f9;
  border-radius: 6px;
}

.dsc-ds-icon {
  color: #3b82f6;
  font-size: 0.75rem;
  margin-top: 0.15rem;
  flex-shrink: 0;
}

.dsc-ds-info {
  min-width: 0;
}

.dsc-ds-name {
  font-weight: 600;
  font-size: 0.8rem;
  color: #1e293b;
}

.dsc-ds-props {
  font-size: 0.74rem;
  color: #64748b;
  margin-top: 0.05rem;
  word-break: break-word;
}

/* ═══ Procedure list ═══ */
.dsc-proc-item {
  display: flex;
  gap: 0.4rem;
  align-items: flex-start;
  margin-bottom: 0.25rem;
}

.dsc-proc-icon {
  color: #8b5cf6;
  font-size: 0.75rem;
  margin-top: 0.15rem;
  flex-shrink: 0;
}

.dsc-proc-name {
  font-weight: 600;
  font-size: 0.8rem;
  color: #1e293b;
}

.dsc-proc-desc {
  font-size: 0.74rem;
  color: #64748b;
  margin-top: 0.05rem;
}

/* ═══ Freshness ═══ */
.dsc-freshness-row {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
}

.dsc-freshness-value {
  font-weight: 600;
  color: #0f172a;
}

/* ═══ Docs / Media ═══ */
.dsc-doc-link {
  margin-bottom: 0.2rem;
  font-size: 0.8rem;
}

.dsc-doc-link a {
  color: #3b82f6;
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
}

.dsc-doc-link a:hover {
  text-decoration: underline;
}

.dsc-media-row {
  display: flex;
  gap: 0.3rem;
  margin-top: 0.3rem;
  flex-wrap: wrap;
}

.dsc-media-thumb img {
  width: 48px;
  height: 48px;
  object-fit: cover;
  border-radius: 4px;
  border: 1px solid #e2e8f0;
}

/* ═══ Action buttons ═══ */
.dsc-actions {
  margin-top: 0.6rem;
  display: flex;
  gap: 0.4rem;
}

.dsc-btn {
  flex: 1;
  padding: 0.4rem 0.5rem;
  border-radius: 6px;
  font-size: 0.8rem;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.3rem;
  transition: background 0.15s, color 0.15s;
  border: 1px solid transparent;
}

.dsc-btn--primary {
  background: transparent;
  color: #3b82f6;
  border-color: #3b82f6;
}

.dsc-btn--primary:hover {
  background: #eff6ff;
}

/* ═══ Advanced IDs ═══ */
.dsc-advanced {
  margin-top: 0.5rem;
}

.dsc-advanced summary {
  cursor: pointer;
  font-size: 0.78rem;
  color: #94a3b8;
  user-select: none;
}

.dsc-advanced summary:hover {
  color: #64748b;
}

.dsc-advanced-body {
  margin-top: 0.3rem;
  padding: 0.4rem;
  background: #f8fafc;
  border-radius: 6px;
  border: 1px solid #f1f5f9;
}

.dsc-adv-field {
  margin-bottom: 0.2rem;
  font-size: 0.76rem;
}

.dsc-adv-label {
  font-weight: 600;
  color: #94a3b8;
  font-size: 0.72rem;
  display: block;
}

.dsc-adv-field code {
  font-size: 0.74rem;
  background: #f1f5f9;
  padding: 0.1rem 0.25rem;
  border-radius: 3px;
  word-break: break-all;
  color: #334155;
}
</style>
