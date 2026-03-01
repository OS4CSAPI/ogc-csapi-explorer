<script setup lang="ts">
/**
 * ConnectionDiagram — visual SVG diagram showing the connection chain:
 *
 *   [User] ——→ [CSAPI Explorer] ----→ [CSAPI Server]
 *
 * States:
 *   idle       — User→Webapp solid, Webapp→Server greyed out (dashed)
 *   connecting — User→Webapp solid, Webapp→Server animated pulse
 *   connected  — all green solid lines
 *   error      — User→Webapp solid, Webapp→Server red, server has red dotted border
 */
defineProps<{
  /** Connection state: 'idle' | 'connecting' | 'connected' | 'error' */
  state: 'idle' | 'connecting' | 'connected' | 'error'
  /** Server label shown under the CSAPI Server box */
  serverLabel?: string
}>()
</script>

<template>
  <div class="conn-diagram-wrap">
    <svg viewBox="0 0 680 150" xmlns="http://www.w3.org/2000/svg" class="conn-diagram-svg">
      <defs>
        <!-- Arrowhead: default grey -->
        <marker id="cd-arrow-grey" viewBox="0 0 10 7" refX="9" refY="3.5"
          markerWidth="8" markerHeight="6" orient="auto-start-reverse">
          <path d="M 0 0 L 10 3.5 L 0 7 Z" fill="#94a3b8" />
        </marker>
        <!-- Arrowhead: green -->
        <marker id="cd-arrow-green" viewBox="0 0 10 7" refX="9" refY="3.5"
          markerWidth="8" markerHeight="6" orient="auto-start-reverse">
          <path d="M 0 0 L 10 3.5 L 0 7 Z" fill="#22c55e" />
        </marker>
        <!-- Arrowhead: red -->
        <marker id="cd-arrow-red" viewBox="0 0 10 7" refX="9" refY="3.5"
          markerWidth="8" markerHeight="6" orient="auto-start-reverse">
          <path d="M 0 0 L 10 3.5 L 0 7 Z" fill="#ef4444" />
        </marker>

        <!-- Glow for connected state -->
        <filter id="cd-glow-green" x="-20%" y="-20%" width="140%" height="140%">
          <feGaussianBlur stdDeviation="3" result="blur" />
          <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
        </filter>
        <!-- Error glow -->
        <filter id="cd-glow-red" x="-20%" y="-20%" width="140%" height="140%">
          <feGaussianBlur stdDeviation="3" result="blur" />
          <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
        </filter>
      </defs>

      <!-- ═══════════════════════════════════════════════════════
           EDGE 1:  User ——→ CSAPI Explorer Webapp
           Always solid — the user is always "connected" to the webapp.
           Green when connected, default blue/grey otherwise.
           ═══════════════════════════════════════════════════════ -->
      <line
        x1="120" y1="62" x2="218" y2="62"
        stroke="#22c55e"
        stroke-width="2.5"
        marker-end="url(#cd-arrow-green)"
      />

      <!-- ═══════════════════════════════════════════════════════
           EDGE 2:  CSAPI Explorer ----→ CSAPI Server
           Varies by state.
           ═══════════════════════════════════════════════════════ -->
      <!-- idle: greyed-out dashed -->
      <line
        v-if="state === 'idle'"
        x1="450" y1="62" x2="528" y2="62"
        stroke="#cbd5e1" stroke-width="1.5" stroke-dasharray="6 4"
        marker-end="url(#cd-arrow-grey)"
        opacity="0.5"
      />
      <!-- connecting: animated pulse -->
      <line
        v-if="state === 'connecting'"
        x1="450" y1="62" x2="528" y2="62"
        stroke="#f59e0b" stroke-width="2" stroke-dasharray="6 4"
        marker-end="url(#cd-arrow-grey)"
        class="cd-pulse"
      />
      <!-- connected: solid green -->
      <line
        v-if="state === 'connected'"
        x1="450" y1="62" x2="528" y2="62"
        stroke="#22c55e" stroke-width="2.5"
        marker-end="url(#cd-arrow-green)"
      />
      <!-- error: solid red -->
      <line
        v-if="state === 'error'"
        x1="450" y1="62" x2="528" y2="62"
        stroke="#ef4444" stroke-width="2.5"
        marker-end="url(#cd-arrow-red)"
      />

      <!-- ═══════════════════════════════════════════════════════
           NODE 1:  User (person at computer icon + label)
           ═══════════════════════════════════════════════════════ -->
      <g class="cd-node">
        <!-- User icon group — stylized person at desk -->
        <g transform="translate(30, 22)">
          <!-- Desk / Monitor -->
          <rect x="28" y="20" width="34" height="26" rx="3" fill="#b0c4de" stroke="#7a96b8" stroke-width="1.5" />
          <rect x="32" y="23" width="26" height="17" rx="1" fill="#dbeafe" />
          <!-- Monitor stand -->
          <rect x="41" y="46" width="12" height="4" rx="1" fill="#7a96b8" />
          <rect x="36" y="50" width="22" height="3" rx="1" fill="#7a96b8" />
          <!-- Person head -->
          <circle cx="14" cy="14" r="9" fill="#87b1d6" stroke="#5a8ab5" stroke-width="1.5" />
          <!-- Person body -->
          <path d="M 2 42 Q 2 28, 14 28 Q 26 28, 26 42" fill="#5a9fd4" stroke="#4080b0" stroke-width="1" />
          <!-- Person arm reaching to keyboard -->
          <path d="M 22 34 Q 30 36, 36 40" stroke="#4080b0" stroke-width="2" fill="none" stroke-linecap="round" />
          <!-- Keyboard -->
          <rect x="32" y="54" width="26" height="5" rx="1" fill="#94a3b8" stroke="#64748b" stroke-width="0.8" />
        </g>
        <!-- Label -->
        <text x="60" y="100" text-anchor="middle" class="cd-label">User</text>
      </g>

      <!-- ═══════════════════════════════════════════════════════
           NODE 2:  CSAPI Explorer Webapp
           ═══════════════════════════════════════════════════════ -->
      <g class="cd-node">
        <rect
          x="220" y="30" width="228" height="64" rx="12"
          :fill="state === 'connected' ? '#f0fdf4' : '#f8fafc'"
          :stroke="state === 'connected' ? '#22c55e' : '#94a3b8'"
          :stroke-width="state === 'connected' ? 2 : 1.5"
          :filter="state === 'connected' ? 'url(#cd-glow-green)' : 'none'"
        />
        <!-- Browser icon -->
        <g transform="translate(240, 47)">
          <rect x="0" y="0" width="24" height="18" rx="3" fill="none" stroke="#64748b" stroke-width="1.5" />
          <line x1="0" y1="5" x2="24" y2="5" stroke="#64748b" stroke-width="1" />
          <circle cx="4" cy="2.5" r="1" fill="#ef4444" />
          <circle cx="8" cy="2.5" r="1" fill="#f59e0b" />
          <circle cx="12" cy="2.5" r="1" fill="#22c55e" />
        </g>
        <text x="334" y="58" text-anchor="middle" class="cd-node-title"
          :fill="state === 'connected' ? '#15803d' : '#334155'"
        >CSAPI Explorer</text>
        <text x="334" y="78" text-anchor="middle" class="cd-node-subtitle">Web Application</text>
      </g>

      <!-- ═══════════════════════════════════════════════════════
           NODE 3:  CSAPI Server
           ═══════════════════════════════════════════════════════ -->
      <g class="cd-node">
        <!-- Main rect — red dotted border on error -->
        <rect
          x="530" y="30" width="140" height="64" rx="12"
          :fill="state === 'connected' ? '#f0fdf4' : state === 'error' ? '#fef2f2' : '#f8fafc'"
          :stroke="state === 'connected' ? '#22c55e' : state === 'error' ? '#ef4444' : '#cbd5e1'"
          :stroke-width="state === 'connected' ? 2 : state === 'error' ? 2.5 : 1.5"
          :stroke-dasharray="state === 'error' ? '6 3' : state === 'idle' ? '4 3' : 'none'"
          :filter="state === 'connected' ? 'url(#cd-glow-green)' : state === 'error' ? 'url(#cd-glow-red)' : 'none'"
          :opacity="state === 'idle' ? 0.5 : 1"
        />
        <!-- Server icon -->
        <g transform="translate(548, 44)" :opacity="state === 'idle' ? 0.4 : 1">
          <rect x="0" y="0" width="22" height="7" rx="2" fill="none"
            :stroke="state === 'error' ? '#ef4444' : state === 'connected' ? '#22c55e' : '#94a3b8'" stroke-width="1.3" />
          <rect x="0" y="10" width="22" height="7" rx="2" fill="none"
            :stroke="state === 'error' ? '#ef4444' : state === 'connected' ? '#22c55e' : '#94a3b8'" stroke-width="1.3" />
          <rect x="0" y="20" width="22" height="7" rx="2" fill="none"
            :stroke="state === 'error' ? '#ef4444' : state === 'connected' ? '#22c55e' : '#94a3b8'" stroke-width="1.3" />
          <!-- LED dots -->
          <circle cx="17" cy="3.5" r="1.5"
            :fill="state === 'connected' ? '#22c55e' : state === 'error' ? '#ef4444' : '#94a3b8'" />
          <circle cx="17" cy="13.5" r="1.5"
            :fill="state === 'connected' ? '#22c55e' : state === 'error' ? '#ef4444' : '#94a3b8'" />
          <circle cx="17" cy="23.5" r="1.5"
            :fill="state === 'connected' ? '#22c55e' : state === 'error' ? '#ef4444' : '#94a3b8'" />
        </g>
        <text x="600" y="58" text-anchor="middle" class="cd-node-title"
          :fill="state === 'connected' ? '#15803d' : state === 'error' ? '#dc2626' : '#64748b'"
          :opacity="state === 'idle' ? 0.5 : 1"
        >CSAPI</text>
        <text x="600" y="78" text-anchor="middle" class="cd-node-subtitle"
          :opacity="state === 'idle' ? 0.5 : 1"
          :fill="state === 'error' ? '#dc2626' : undefined"
        >Server</text>
      </g>

      <!-- Server label (below the box, when provided) -->
      <text
        v-if="serverLabel && state !== 'idle'"
        x="600" y="115"
        text-anchor="middle"
        class="cd-server-label"
        :fill="state === 'error' ? '#dc2626' : state === 'connected' ? '#15803d' : '#64748b'"
      >{{ serverLabel }}</text>

      <!-- Status text below the connecting line -->
      <text
        v-if="state === 'connecting'"
        x="490" y="82"
        text-anchor="middle"
        class="cd-status-text cd-pulse"
        fill="#f59e0b"
      >connecting…</text>
      <text
        v-if="state === 'connected'"
        x="490" y="82"
        text-anchor="middle"
        class="cd-status-text"
        fill="#22c55e"
      >connected</text>
      <text
        v-if="state === 'error'"
        x="490" y="82"
        text-anchor="middle"
        class="cd-status-text"
        fill="#ef4444"
      >failed</text>
    </svg>
  </div>
</template>

<style scoped>
.conn-diagram-wrap {
  width: 100%;
  margin: 0.5rem 0 1rem;
}
.conn-diagram-svg {
  width: 100%;
  max-width: 580px;
  height: auto;
  display: block;
  margin: 0 auto;
}

/* Node styles */
.cd-node { cursor: default; }
.cd-label {
  font-size: 13px;
  font-weight: 600;
  fill: #475569;
  font-family: system-ui, -apple-system, sans-serif;
}
.cd-node-title {
  font-size: 14px;
  font-weight: 700;
  font-family: system-ui, -apple-system, sans-serif;
}
.cd-node-subtitle {
  font-size: 10.5px;
  font-weight: 400;
  fill: #94a3b8;
  font-family: system-ui, -apple-system, sans-serif;
}
.cd-server-label {
  font-size: 9.5px;
  font-weight: 500;
  font-family: system-ui, -apple-system, sans-serif;
}
.cd-status-text {
  font-size: 9.5px;
  font-weight: 600;
  font-family: system-ui, -apple-system, sans-serif;
}

/* Connecting pulse animation */
.cd-pulse {
  animation: cd-pulse-anim 1.2s ease-in-out infinite;
}
@keyframes cd-pulse-anim {
  0%, 100% { opacity: 0.4; }
  50% { opacity: 1; }
}
</style>
