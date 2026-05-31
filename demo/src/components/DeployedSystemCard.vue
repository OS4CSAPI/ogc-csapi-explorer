<script setup lang="ts">
/**
 * DeployedSystemCard.vue — Tactical info card for deployed-system leaves.
 *
 * Redesigned per OS4CSAPI UI Feedback Pack v1.
 * Section order: Header → Summary → Outputs → Context → Occupant → Freshness → Links → Advanced
 *
 * Design goals:
 *   - Understand the system in 5 seconds
 *   - Operational, not verbose
 *   - No raw schema, no debug text, no ISO timestamps in the main view
 */
import { computed, ref, watch } from 'vue'
import type { DeployedSystemCardModel, TrendSummary } from '../composables/useDeployedSystemCard'

const showImageOverlay = ref(false)
const showBuoycamOverlay = ref(false)
const FALLBACK_THUMBNAIL = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='320' height='220' viewBox='0 0 320 220'%3E%3Crect width='320' height='220' fill='%231e3a8a'/%3E%3Ctext x='160' y='112' fill='%23eff6ff' font-size='24' text-anchor='middle' font-family='Arial,sans-serif'%3ETrain%3C/text%3E%3C/svg%3E"

const props = defineProps<{
  card: DeployedSystemCardModel
  loading?: boolean
}>()

const displayThumbnail = ref('')
const displayCameraImage = ref('')

function resetImageBindings() {
  displayThumbnail.value = props.card.thumbnail || FALLBACK_THUMBNAIL
  displayCameraImage.value = props.card.cameraThumbUrl || props.card.cameraImageUrl || ''
}

function onThumbnailError() {
  if (displayThumbnail.value !== FALLBACK_THUMBNAIL) {
    displayThumbnail.value = FALLBACK_THUMBNAIL
  }
}

function onCameraImageError() {
  if (props.card.cameraImageUrl && displayCameraImage.value !== props.card.cameraImageUrl) {
    displayCameraImage.value = props.card.cameraImageUrl
    return
  }
  if (displayCameraImage.value !== FALLBACK_THUMBNAIL) {
    displayCameraImage.value = FALLBACK_THUMBNAIL
  }
}

watch(
  () => props.card,
  () => resetImageBindings(),
  { immediate: true, deep: true },
)

const emit = defineEmits<{
  (e: 'explore'): void
  (e: 'close'): void
}>()

// Max 3 badges
const badges = computed(() => {
  const b: Array<{ label: string; cls: string }> = []
  if (props.card.roleBadge)
    b.push({ label: props.card.roleBadge, cls: 'badge-role' })
  if (props.card.statusBadge)
    b.push({ label: props.card.statusBadge, cls: statusClass(props.card.statusBadge) })
  if (props.card.kindBadge)
    b.push({ label: props.card.kindBadge, cls: 'badge-kind' })
  return b.slice(0, 3)
})

function statusClass(s: string): string {
  if (/active|healthy|online/i.test(s)) return 'badge-ok'
  if (/degraded|stale/i.test(s)) return 'badge-warn'
  if (/inactive|offline/i.test(s)) return 'badge-err'
  return 'badge-neutral'
}

// Outputs section — product labels + cadence + method
const outputLines = computed(() => {
  const lines: string[] = []
  const pl = props.card.productLabels
  if (pl.length) lines.push(...pl.slice(0, 3))
  else lines.push('No public data products')
  if (props.card.methodSummary) lines.push(props.card.methodSummary)
  return lines
})

const hasNoProducts = computed(() => props.card.productLabels.length === 0)

function readingStateClass(state: string): string {
  if (state === 'current') return 'reading-current'
  if (state === 'recent') return 'reading-recent'
  if (state === 'stale') return 'reading-stale'
  return 'reading-unknown'
}

function trendStateClass(state: TrendSummary['trendState']): string {
  if (state === 'rising') return 'trend-rising'
  if (state === 'falling') return 'trend-falling'
  return 'trend-steady'
}

function trendIcon(state: TrendSummary['trendState']): string {
  if (state === 'rising') return 'pi-arrow-up'
  if (state === 'falling') return 'pi-arrow-down'
  return 'pi-minus'
}

function formatTimestamp(value: string): string {
  if (!value) return ''
  const time = new Date(value)
  if (!Number.isFinite(time.getTime())) return value
  return time.toLocaleString()
}

function sparklinePoints(points: number[]): string {
  if (points.length < 2) return ''
  const min = Math.min(...points)
  const max = Math.max(...points)
  const span = max - min || 1
  return points.map((value, index) => {
    const x = points.length === 1 ? 50 : (index / (points.length - 1)) * 100
    const y = 28 - ((value - min) / span) * 24
    return `${x.toFixed(1)},${y.toFixed(1)}`
  }).join(' ')
}

// Context — compact breadcrumb
const contextLines = computed(() => {
  const parts: string[] = []
  if (props.card.deploymentPath) {
    // Split path and take the last 3 segments for compactness
    const segs = props.card.deploymentPath.split(/\s*[›→>]\s*/).filter(Boolean)
    parts.push(...segs.slice(-3))
  } else if (props.card.parentDeployment) {
    parts.push(props.card.parentDeployment)
  }
  if (props.card.deploymentType) parts.push(props.card.deploymentType)
  return parts
})

const hasOccupant = computed(() =>
  props.card.occupantName && props.card.occupantName !== 'Unknown Occupant'
)

// Links — max 3
const visibleLinks = computed(() => props.card.docsLinks.slice(0, 3))

// Freshness
const freshLabel = computed(() => {
  if (props.card.latestActivityRelative && props.card.latestActivityRelative !== 'No recent activity') {
    return `Updated ${props.card.latestActivityRelative}`
  }
  return 'No recent activity'
})

const freshActive = computed(() =>
  props.card.latestActivityRelative && props.card.latestActivityRelative !== 'No recent activity'
)

const refreshRows = computed(() => {
  const rows: Array<{ label: string; value: string; title: string }> = []
  const lastRefreshTime = props.card.lastRefreshTime || props.card.latestActivityTime
  const lastRefreshRelative = props.card.lastRefreshRelative || props.card.latestActivityRelative
  if (lastRefreshTime) {
    rows.push({
      label: 'Last refresh',
      value: lastRefreshRelative ? `${lastRefreshRelative} (${formatTimestamp(lastRefreshTime)})` : formatTimestamp(lastRefreshTime),
      title: lastRefreshTime,
    })
  }
  const cadence = props.card.refreshCadence || props.card.cadenceNote.replace(/^Cadence:\s*/i, '')
  if (cadence) {
    rows.push({ label: 'Refresh rate', value: cadence, title: cadence })
  }
  return rows
})

const cadenceClarifier = computed(() => {
  const searchable = [
    props.card.title,
    props.card.subtitle,
    props.card.occupantName,
    props.card.occupantUid,
    props.card.advancedSystemUid,
    props.card.primaryPurpose,
    ...props.card.productLabels,
  ].join(' ')
  if (/opensky|ads-?b|state vector/i.test(searchable)) {
    return 'Periodic ADS-B state vectors; not streaming.'
  }
  return ''
})

const trustLine = computed(() => {
  const parts: string[] = []
  if (props.card.healthState) parts.push(props.card.healthState)
  if (props.card.qualitySummary) parts.push(props.card.qualitySummary)
  return parts.join(' · ') || ''
})
</script>

<template>
  <!-- Image lightbox overlay -->
  <Teleport to="body">
    <div v-if="showImageOverlay" class="dsc-lightbox" @click="showImageOverlay = false">
      <div class="dsc-lightbox-inner" @click.stop>
        <img :src="displayThumbnail" alt="" class="dsc-lightbox-img" @error="onThumbnailError" />
        <button class="dsc-lightbox-close" @click="showImageOverlay = false" title="Close">
          <i class="pi pi-times"></i>
        </button>
      </div>
    </div>
    <div v-if="showBuoycamOverlay" class="dsc-lightbox" @click="showBuoycamOverlay = false">
      <div class="dsc-lightbox-inner" @click.stop>
        <img :src="displayCameraImage || card.cameraImageUrl" alt="Camera" class="dsc-lightbox-img" @error="onCameraImageError" />
        <button class="dsc-lightbox-close" @click="showBuoycamOverlay = false" title="Close">
          <i class="pi pi-times"></i>
        </button>
      </div>
    </div>
  </Teleport>

  <div class="dsc" :class="{ 'dsc--loading': loading }">
    <!-- Loading spinner -->
    <div v-if="loading" class="dsc-loader">
      <i class="pi pi-spin pi-spinner"></i> Loading…
    </div>

    <!-- ── 1. HEADER ── -->
    <header class="dsc-hdr">
      <div class="dsc-hdr-row">
        <div class="dsc-icon-group">
          <div class="dsc-icon" :class="{ 'dsc-icon--clickable': !!displayThumbnail }" @click="displayThumbnail && (showImageOverlay = true)">
            <img v-if="displayThumbnail" :src="displayThumbnail" alt="" title="Click to enlarge" @error="onThumbnailError" />
            <i v-else class="pi pi-map"></i>
          </div>
          <img v-if="card.stanagSvg" :src="card.stanagSvg" class="dsc-stanag" alt="STANAG" title="MIL-STD-2525 Symbol" />
        </div>
        <div class="dsc-hdr-text">
          <h2 class="dsc-title">{{ card.title }}</h2>
          <p v-if="card.subtitle" class="dsc-sub">{{ card.subtitle }}</p>
        </div>
        <button class="dsc-close" @click="emit('close')" title="Close">
          <i class="pi pi-times"></i>
        </button>
      </div>
      <div v-if="badges.length" class="dsc-badges">
        <span v-for="(b, i) in badges" :key="i" class="dsc-badge" :class="b.cls">
          {{ b.label }}
        </span>
      </div>
    </header>

    <!-- ── 2. SUMMARY ── -->
    <p v-if="card.summarySentence" class="dsc-summary">
      {{ card.summarySentence }}
    </p>

    <!-- ── 2b. LIVE CAMERA IMAGE (BuoyCAM / NIMS) ── -->
    <section v-if="card.cameraImageUrl" class="dsc-sec dsc-buoycam">
      <h3 class="dsc-sec-hd"><i class="pi pi-camera"></i> {{ card.cameraLabel || 'Live Camera' }}</h3>
      <div class="dsc-buoycam-frame" @click="showBuoycamOverlay = true" title="Click to enlarge">
        <img :src="displayCameraImage || card.cameraImageUrl" alt="Camera" class="dsc-buoycam-img" @error="onCameraImageError" />
      </div>
      <div class="dsc-buoycam-meta">
        <div v-if="card.cameraTimestamp" class="dsc-buoycam-time">
          <i class="pi pi-clock"></i>
          {{ new Date(card.cameraTimestamp).toLocaleString() }}
        </div>
        <div v-if="card.cameraCamId" class="dsc-buoycam-camid">
          📹 {{ card.cameraCamId }}
        </div>
      </div>
      <a
        v-if="card.cameraTimeLapseUrl"
        :href="card.cameraTimeLapseUrl"
        target="_blank"
        rel="noopener"
        class="dsc-timelapse-link"
      >
        <i class="pi pi-play-circle"></i> View Timelapse
      </a>
    </section>

    <!-- ── 3. OUTPUTS ── -->
    <section class="dsc-sec">
      <h3 class="dsc-sec-hd"><i class="pi pi-chart-line"></i> Outputs</h3>
      <ul class="dsc-output-list">
        <li
          v-for="(line, i) in outputLines"
          :key="i"
          class="dsc-output-item"
          :class="{ 'dsc-output-empty': hasNoProducts && i === 0 }"
        >
          {{ line }}
        </li>
      </ul>
    </section>

    <!-- ── 4. FORECASTS ── -->
    <section v-if="card.forecastSummaries.length" class="dsc-sec dsc-forecasts">
      <h3 class="dsc-sec-hd"><i class="pi pi-calendar-clock"></i> Forecast</h3>
      <div class="dsc-forecast-list">
        <div
          v-for="forecast in card.forecastSummaries"
          :key="forecast.datastreamId"
          class="dsc-forecast-item"
        >
          <div class="dsc-forecast-main">
            <span class="dsc-forecast-label">{{ forecast.label }}</span>
            <span class="dsc-forecast-value">
              {{ forecast.value }}
            </span>
          </div>
          <div class="dsc-forecast-meta">
            <span v-if="forecast.validTime" :title="forecast.validTime">
              Valid {{ forecast.relativeValidTime }}
            </span>
            <span v-if="forecast.leadTimeHours" class="dsc-forecast-lead">
              Lead {{ forecast.leadTimeHours }}
            </span>
            <span v-if="forecast.issuedTime" :title="forecast.issuedTime">
              Issued {{ formatTimestamp(forecast.issuedTime) }}
            </span>
          </div>
        </div>
      </div>
    </section>

    <!-- ── 4b. LATEST READINGS ── -->
    <section v-if="card.latestReadings.length" class="dsc-sec">
      <h3 class="dsc-sec-hd"><i class="pi pi-bolt"></i> Latest readings</h3>
      <div class="dsc-reading-list">
        <div
          v-for="reading in card.latestReadings"
          :key="reading.datastreamId"
          class="dsc-reading-item"
        >
          <div class="dsc-reading-main">
            <span class="dsc-reading-label">{{ reading.label }}</span>
            <span class="dsc-reading-value">
              {{ reading.value }}{{ reading.unit ? ' ' + reading.unit : '' }}
            </span>
          </div>
          <div class="dsc-reading-meta">
            <span v-if="reading.relativeTime" :title="reading.phenomenonTime">
              {{ reading.relativeTime }}
            </span>
            <span
              class="dsc-reading-state"
              :class="readingStateClass(reading.freshnessState)"
            >
              {{ reading.freshnessState }}
            </span>
            <span v-if="reading.quality">{{ reading.quality }}</span>
          </div>
        </div>
      </div>
    </section>

    <!-- ── 4c. RECENT TRENDS ── -->
    <section v-if="card.trendSummaries.length" class="dsc-sec dsc-trends">
      <h3 class="dsc-sec-hd"><i class="pi pi-chart-line"></i> Recent trend</h3>
      <div class="dsc-trend-list">
        <div
          v-for="trend in card.trendSummaries"
          :key="trend.datastreamId"
          class="dsc-trend-item"
        >
          <div class="dsc-trend-top">
            <div class="dsc-trend-name">
              <span class="dsc-trend-label">{{ trend.label }}</span>
              <span class="dsc-trend-window">{{ trend.windowLabel }} · {{ trend.sampleCount }} samples</span>
            </div>
            <span class="dsc-trend-badge" :class="trendStateClass(trend.trendState)">
              <i class="pi" :class="trendIcon(trend.trendState)"></i>
              {{ trend.trendLabel }}
            </span>
          </div>
          <div class="dsc-trend-body">
            <svg class="dsc-spark" viewBox="0 0 100 32" preserveAspectRatio="none" aria-hidden="true">
              <polyline :points="sparklinePoints(trend.points)" />
            </svg>
            <div class="dsc-trend-value">
              <strong>{{ trend.latestValue }}{{ trend.unit ? ' ' + trend.unit : '' }}</strong>
              <span v-if="trend.latestRelativeTime">{{ trend.latestRelativeTime }}</span>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ── 5. CONTEXT ── -->
    <section v-if="contextLines.length" class="dsc-sec">
      <h3 class="dsc-sec-hd"><i class="pi pi-sitemap"></i> Context</h3>
      <div class="dsc-breadcrumb">
        <span v-for="(seg, i) in contextLines" :key="i">
          <span v-if="i > 0" class="dsc-sep">›</span>
          {{ seg }}
        </span>
      </div>
    </section>

    <!-- ── 6. OCCUPANT ── -->
    <section v-if="hasOccupant" class="dsc-sec">
      <h3 class="dsc-sec-hd"><i class="pi pi-server"></i> Occupant</h3>
      <div class="dsc-kv">
        <span class="dsc-k">Name</span>
        <span class="dsc-v">{{ card.occupantName }}</span>
      </div>
      <div v-if="card.occupantKind && card.occupantKind !== 'Unknown Kind'" class="dsc-kv">
        <span class="dsc-k">Kind</span>
        <span class="dsc-v">{{ card.occupantKind }}</span>
      </div>
      <div v-if="card.manufacturerModelOrVersion" class="dsc-kv">
        <span class="dsc-k">Model / Version</span>
        <span class="dsc-v">{{ card.manufacturerModelOrVersion }}</span>
      </div>
      <div v-if="card.ownerMaintainer" class="dsc-kv">
        <span class="dsc-k">Owner</span>
        <span class="dsc-v">{{ card.ownerMaintainer }}</span>
      </div>
    </section>

    <!-- ── 7. FRESHNESS ── -->
    <section class="dsc-sec dsc-fresh">
      <div class="dsc-fresh-row">
        <span class="dsc-fresh-label" :class="{ 'dsc-fresh-active': freshActive }">
          <i class="pi" :class="freshActive ? 'pi-check-circle' : 'pi-clock'"></i>
          {{ freshLabel }}
        </span>
        <span v-if="trustLine" class="dsc-trust">{{ trustLine }}</span>
      </div>
      <div v-if="refreshRows.length" class="dsc-refresh-grid">
        <div v-for="row in refreshRows" :key="row.label" class="dsc-refresh-row">
          <span class="dsc-refresh-k">{{ row.label }}</span>
          <span class="dsc-refresh-v" :title="row.title">{{ row.value }}</span>
        </div>
      </div>
      <p v-if="cadenceClarifier" class="dsc-refresh-note">{{ cadenceClarifier }}</p>
    </section>

    <!-- ── 8. LINKS ── -->
    <section class="dsc-sec dsc-links">
      <button class="dsc-action" @click="emit('explore')">
        <i class="pi pi-external-link"></i> View in Explorer
      </button>
      <a
        v-for="doc in visibleLinks"
        :key="doc.href"
        :href="doc.href"
        target="_blank"
        rel="noopener"
        class="dsc-doc"
      >
        <i class="pi pi-file"></i> {{ doc.title }}
      </a>
    </section>

    <!-- ── 9. ADVANCED IDs (collapsed) ── -->
    <details class="dsc-adv">
      <summary>Advanced IDs</summary>
      <div class="dsc-adv-body">
        <div v-if="card.advancedDeploymentId" class="dsc-adv-row">
          <span>Deployment ID</span><code>{{ card.advancedDeploymentId }}</code>
        </div>
        <div v-if="card.advancedDeploymentUid" class="dsc-adv-row">
          <span>Deployment UID</span><code>{{ card.advancedDeploymentUid }}</code>
        </div>
        <div v-if="card.advancedSystemId" class="dsc-adv-row">
          <span>System ID</span><code>{{ card.advancedSystemId }}</code>
        </div>
        <div v-if="card.advancedSystemUid" class="dsc-adv-row">
          <span>System UID</span><code>{{ card.advancedSystemUid }}</code>
        </div>
        <div v-if="card.advancedBootstrapOwner" class="dsc-adv-row">
          <span>Bootstrap Owner</span><code>{{ card.advancedBootstrapOwner }}</code>
        </div>
        <div v-if="card.advancedSourceOfTruth" class="dsc-adv-row">
          <span>Source of Truth</span><code>{{ card.advancedSourceOfTruth }}</code>
        </div>
        <div v-if="card.latestActivityTime" class="dsc-adv-row">
          <span>Exact Time</span><code>{{ card.latestActivityTime }}</code>
        </div>
      </div>
    </details>
  </div>
</template>

<style scoped>
/* ═══ Root ═══ */
.dsc {
  font-family: system-ui, -apple-system, sans-serif;
  font-size: 0.84rem;
  color: #1e293b;
  line-height: 1.45;
  position: relative;
  padding: 0;
}
.dsc--loading { opacity: 0.5; pointer-events: none; }
.dsc-loader {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.4rem 0;
  color: #64748b;
  font-size: 0.82rem;
}

/* ═══ Header ═══ */
.dsc-hdr { margin-bottom: 0.35rem; }
.dsc-hdr-row {
  display: flex;
  gap: 0.55rem;
  align-items: center;
}
.dsc-icon-group {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 0.35rem;
}
.dsc-icon {
  flex-shrink: 0;
  width: 72px; height: 72px;
  background: #dbeafe;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #3b82f6;
  font-size: 1.15rem;
  overflow: hidden;
}
.dsc-icon--clickable {
  cursor: pointer;
  transition: box-shadow 0.15s;
}
.dsc-icon--clickable:hover {
  box-shadow: 0 0 0 2px #3b82f6;
}
.dsc-icon img {
  width: 100%; height: 100%;
  object-fit: cover;
}

/* Lightbox overlay */
.dsc-lightbox {
  position: fixed;
  inset: 0;
  z-index: 10000;
  background: rgba(0,0,0,0.70);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}
.dsc-lightbox-inner {
  position: relative;
  cursor: default;
  width: min(760px, 90vw);
  max-height: 90vh;
  display: flex;
  align-items: center;
  justify-content: center;
}
.dsc-lightbox-img {
  display: block;
  width: 100%;
  max-width: 100%;
  max-height: 85vh;
  border-radius: 10px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.5);
  object-fit: contain;
  background: #fff;
}
.dsc-lightbox-close {
  position: absolute;
  top: -12px;
  right: -12px;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #fff;
  border: none;
  box-shadow: 0 2px 8px rgba(0,0,0,0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 0.9rem;
  color: #334155;
}
.dsc-lightbox-close:hover {
  background: #f1f5f9;
}
.dsc-stanag {
  width: 64px;
  height: 64px;
  object-fit: contain;
  flex-shrink: 0;
}
.dsc-hdr-text { flex: 1; min-width: 0; }
.dsc-title {
  font-size: 1.02rem;
  font-weight: 700;
  color: #0f172a;
  line-height: 1.2;
  margin: 0;
}
.dsc-sub {
  font-size: 0.8rem;
  color: #64748b;
  margin: 1px 0 0;
}
.dsc-close {
  flex-shrink: 0;
  background: none;
  border: none;
  cursor: pointer;
  color: #94a3b8;
  font-size: 0.85rem;
  padding: 0.2rem;
  border-radius: 4px;
}
.dsc-close:hover { color: #475569; background: #f1f5f9; }

/* ═══ Badges ═══ */
.dsc-badges {
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem;
  margin-top: 0.35rem;
}
.dsc-badge {
  font-size: 0.68rem;
  font-weight: 600;
  padding: 0.12rem 0.45rem;
  border-radius: 999px;
  border: 1px solid;
  white-space: nowrap;
  letter-spacing: 0.02em;
  text-transform: uppercase;
}
.badge-role { background: #eff6ff; color: #2563eb; border-color: #93c5fd; }
.badge-ok   { background: #f0fdf4; color: #16a34a; border-color: #86efac; }
.badge-warn { background: #fffbeb; color: #d97706; border-color: #fcd34d; }
.badge-err  { background: #fef2f2; color: #dc2626; border-color: #fca5a5; }
.badge-neutral { background: #f8fafc; color: #64748b; border-color: #cbd5e1; }
.badge-kind { background: #faf5ff; color: #7c3aed; border-color: #c4b5fd; }

/* ═══ Summary ═══ */
.dsc-summary {
  margin: 0.3rem 0 0.5rem;
  padding: 0.4rem 0.55rem;
  background: #f0f9ff;
  border-left: 3px solid #3b82f6;
  border-radius: 0 6px 6px 0;
  font-size: 0.82rem;
  color: #1e40af;
  line-height: 1.45;
}

/* ═══ Sections ═══ */
.dsc-sec {
  margin-bottom: 0.45rem;
  padding-bottom: 0.4rem;
  border-bottom: 1px solid #f1f5f9;
}
.dsc-sec:last-of-type { border-bottom: none; }
.dsc-sec-hd {
  font-size: 0.68rem;
  font-weight: 700;
  color: #94a3b8;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  margin: 0 0 0.25rem;
  display: flex;
  align-items: center;
  gap: 0.3rem;
}
.dsc-sec-hd i { font-size: 0.68rem; }

/* ═══ Outputs ═══ */
.dsc-output-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
}
.dsc-output-item {
  font-size: 0.82rem;
  padding: 0.22rem 0.5rem;
  background: #f8fafc;
  border: 1px solid #f1f5f9;
  border-radius: 5px;
  color: #1e293b;
  font-weight: 500;
}
.dsc-output-item:first-child {
  font-weight: 600;
  background: #eff6ff;
  border-color: #dbeafe;
  color: #1e40af;
}
.dsc-output-empty {
  color: #94a3b8 !important;
  font-style: italic;
  font-weight: 400 !important;
  background: #fafafa !important;
  border-color: #f1f5f9 !important;
}

/* ═══ Latest Readings ═══ */
.dsc-forecast-list {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}
.dsc-forecast-item {
  padding: 0.4rem 0.5rem;
  background: #f0f9ff;
  border: 1px solid #bae6fd;
  border-radius: 6px;
}
.dsc-forecast-main {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 0.5rem;
}
.dsc-forecast-label {
  min-width: 0;
  color: #075985;
  font-size: 0.8rem;
  font-weight: 700;
}
.dsc-forecast-value {
  flex-shrink: 0;
  color: #0c4a6e;
  font-size: 0.9rem;
  font-weight: 800;
}
.dsc-forecast-meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.3rem;
  margin-top: 0.15rem;
  color: #0369a1;
  font-size: 0.7rem;
}
.dsc-forecast-lead {
  padding: 0.05rem 0.32rem;
  border-radius: 999px;
  border: 1px solid #7dd3fc;
  background: #e0f2fe;
  color: #075985;
  font-size: 0.62rem;
  font-weight: 700;
  line-height: 1.4;
  text-transform: uppercase;
}
.dsc-reading-list {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}
.dsc-reading-item {
  padding: 0.35rem 0.5rem;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
}
.dsc-reading-main {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 0.5rem;
}
.dsc-reading-label {
  min-width: 0;
  color: #334155;
  font-size: 0.8rem;
  font-weight: 600;
}
.dsc-reading-value {
  flex-shrink: 0;
  color: #0f172a;
  font-size: 0.9rem;
  font-weight: 700;
}
.dsc-reading-meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.3rem;
  margin-top: 0.15rem;
  color: #64748b;
  font-size: 0.7rem;
}
.dsc-reading-state {
  padding: 0.05rem 0.32rem;
  border-radius: 999px;
  border: 1px solid;
  font-size: 0.62rem;
  font-weight: 700;
  line-height: 1.4;
  text-transform: uppercase;
}
.reading-current { background: #f0fdf4; color: #16a34a; border-color: #bbf7d0; }
.reading-recent { background: #eff6ff; color: #2563eb; border-color: #bfdbfe; }
.reading-stale { background: #fffbeb; color: #d97706; border-color: #fde68a; }
.reading-unknown { background: #f8fafc; color: #64748b; border-color: #cbd5e1; }

/* ═══ Recent Trends ═══ */
.dsc-trend-list {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}
.dsc-trend-item {
  padding: 0.4rem 0.5rem;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
}
.dsc-trend-top {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 0.5rem;
}
.dsc-trend-name {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 0.05rem;
}
.dsc-trend-label {
  color: #334155;
  font-size: 0.8rem;
  font-weight: 700;
}
.dsc-trend-window {
  color: #64748b;
  font-size: 0.68rem;
}
.dsc-trend-badge {
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  gap: 0.22rem;
  padding: 0.1rem 0.38rem;
  border-radius: 999px;
  border: 1px solid;
  font-size: 0.64rem;
  font-weight: 700;
  text-transform: uppercase;
}
.dsc-trend-badge i { font-size: 0.62rem; }
.trend-rising { background: #fef2f2; color: #dc2626; border-color: #fecaca; }
.trend-falling { background: #eff6ff; color: #2563eb; border-color: #bfdbfe; }
.trend-steady { background: #f0fdf4; color: #16a34a; border-color: #bbf7d0; }
.dsc-trend-body {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 0.55rem;
  align-items: center;
  margin-top: 0.25rem;
}
.dsc-spark {
  width: 100%;
  height: 32px;
  display: block;
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 5px;
}
.dsc-spark polyline {
  fill: none;
  stroke: #2563eb;
  stroke-width: 2.5;
  vector-effect: non-scaling-stroke;
  stroke-linecap: round;
  stroke-linejoin: round;
}
.dsc-trend-value {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  min-width: 4.7rem;
  color: #64748b;
  font-size: 0.68rem;
  line-height: 1.25;
}
.dsc-trend-value strong {
  color: #0f172a;
  font-size: 0.82rem;
  white-space: nowrap;
}

/* ═══ Context ═══ */
.dsc-breadcrumb {
  font-size: 0.8rem;
  color: #475569;
}
.dsc-sep {
  color: #cbd5e1;
  margin: 0 0.25rem;
}

/* ═══ Occupant KV ═══ */
.dsc-kv {
  display: flex;
  gap: 0.4rem;
  margin-bottom: 0.15rem;
  font-size: 0.8rem;
}
.dsc-k {
  flex-shrink: 0;
  width: 90px;
  color: #64748b;
  font-weight: 600;
  font-size: 0.75rem;
}
.dsc-v {
  color: #1e293b;
  min-width: 0;
  word-break: break-word;
}

/* ═══ Freshness ═══ */
.dsc-fresh {
  padding: 0.35rem 0;
  border-bottom: none;
}
.dsc-fresh-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}
.dsc-fresh-label {
  font-size: 0.8rem;
  color: #64748b;
  display: flex;
  align-items: center;
  gap: 0.25rem;
}
.dsc-fresh-label i { font-size: 0.75rem; }
.dsc-fresh-active { color: #16a34a; font-weight: 600; }
.dsc-trust {
  font-size: 0.75rem;
  color: #94a3b8;
}
.dsc-refresh-grid {
  display: grid;
  gap: 0.2rem;
  margin-top: 0.3rem;
}
.dsc-refresh-row {
  display: grid;
  grid-template-columns: 88px minmax(0, 1fr);
  gap: 0.4rem;
  align-items: baseline;
  font-size: 0.76rem;
}
.dsc-refresh-k {
  color: #64748b;
  font-weight: 700;
}
.dsc-refresh-v {
  min-width: 0;
  color: #1e293b;
  overflow-wrap: anywhere;
}
.dsc-refresh-note {
  margin: 0.25rem 0 0;
  color: #64748b;
  font-size: 0.72rem;
  line-height: 1.25;
}

/* ═══ Links ═══ */
.dsc-links {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
  border-bottom: none;
}
.dsc-action {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.35rem;
  padding: 0.4rem 0.6rem;
  border: 1px solid #3b82f6;
  border-radius: 6px;
  background: transparent;
  color: #3b82f6;
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.12s;
}
.dsc-action:hover { background: #eff6ff; }
.dsc-doc {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.78rem;
  color: #3b82f6;
  text-decoration: none;
  padding: 0.15rem 0;
}
.dsc-doc:hover { text-decoration: underline; }
.dsc-doc i { font-size: 0.72rem; }

/* ═══ Advanced ═══ */
.dsc-adv {
  margin-top: 0.35rem;
}
.dsc-adv summary {
  cursor: pointer;
  font-size: 0.75rem;
  color: #94a3b8;
  user-select: none;
}
.dsc-adv summary:hover { color: #64748b; }
.dsc-adv-body {
  margin-top: 0.25rem;
  padding: 0.35rem 0.4rem;
  background: #f8fafc;
  border-radius: 6px;
  border: 1px solid #f1f5f9;
}
.dsc-adv-row {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 0.15rem;
  font-size: 0.72rem;
  gap: 0.4rem;
}
.dsc-adv-row span {
  color: #94a3b8;
  font-weight: 600;
  flex-shrink: 0;
}
.dsc-adv-row code {
  font-size: 0.7rem;
  background: #f1f5f9;
  padding: 0.08rem 0.2rem;
  border-radius: 3px;
  word-break: break-all;
  color: #334155;
  text-align: right;
}

/* ═══ BuoyCAM Section ═══ */
.dsc-buoycam {
  background: #0f172a;
  border-radius: 8px;
  padding: 0.6rem !important;
  margin-top: 0.4rem;
}
.dsc-buoycam .dsc-sec-hd {
  color: #e2e8f0;
  margin-bottom: 0.45rem;
}
.dsc-buoycam .dsc-sec-hd i {
  color: #38bdf8;
}
.dsc-buoycam-frame {
  cursor: pointer;
  border-radius: 6px;
  overflow: hidden;
  transition: box-shadow 0.15s;
  line-height: 0;
}
.dsc-buoycam-frame:hover {
  box-shadow: 0 0 0 2px #38bdf8;
}
.dsc-buoycam-img {
  width: 100%;
  height: auto;
  object-fit: cover;
  max-height: 200px;
  display: block;
}
.dsc-buoycam-time {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  color: #94a3b8;
  font-size: 0.72rem;
  margin-top: 0.35rem;
}
.dsc-buoycam-time i { font-size: 0.72rem; }
.dsc-buoycam-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.3rem;
  margin-top: 0.35rem;
}
.dsc-buoycam-camid {
  color: #94a3b8;
  font-size: 0.72rem;
}
.dsc-timelapse-link {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  margin-top: 0.45rem;
  padding: 0.3rem 0.6rem;
  background: rgba(56, 189, 248, 0.15);
  color: #38bdf8;
  border: 1px solid rgba(56, 189, 248, 0.3);
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 600;
  text-decoration: none;
  transition: background 0.15s, border-color 0.15s;
}
.dsc-timelapse-link:hover {
  background: rgba(56, 189, 248, 0.25);
  border-color: #38bdf8;
}
.dsc-timelapse-link i { font-size: 0.8rem; }
</style>
