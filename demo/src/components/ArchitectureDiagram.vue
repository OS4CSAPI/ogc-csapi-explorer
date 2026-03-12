<script setup lang="ts">
/**
 * ArchitectureDiagram — SVG diagram showing the live demo architecture:
 *
 *   [ODAS Mic Arrays] ─ ─→ [Data Simulator] ──→ [OSH CSAPI Server] ⇄ [CSAPI Explorer] ⇄ [Analyst]
 *                           [LOB Localizer]  ⇄  [OSH CSAPI Server]
 *
 *   Bidirectional arrows:
 *     LOB Localizer ↔ Server  (GET LOBs / POST fixes)
 *     Explorer ↔ Server       (GET data / POST SENREPs)
 *     User ↔ Explorer         (views data / submits SENREPs)
 */
</script>

<template>
  <div class="arch-diagram-wrap">
    <svg viewBox="0 0 1120 370" xmlns="http://www.w3.org/2000/svg" class="arch-diagram-svg">
      <defs>
        <marker id="ad-arrow-blue" viewBox="0 0 10 7" refX="9" refY="3.5"
          markerWidth="8" markerHeight="6" orient="auto-start-reverse">
          <path d="M 0 0 L 10 3.5 L 0 7 Z" fill="#60a5fa" />
        </marker>
        <marker id="ad-arrow-green" viewBox="0 0 10 7" refX="9" refY="3.5"
          markerWidth="8" markerHeight="6" orient="auto-start-reverse">
          <path d="M 0 0 L 10 3.5 L 0 7 Z" fill="#22c55e" />
        </marker>
        <marker id="ad-arrow-amber" viewBox="0 0 10 7" refX="9" refY="3.5"
          markerWidth="8" markerHeight="6" orient="auto-start-reverse">
          <path d="M 0 0 L 10 3.5 L 0 7 Z" fill="#f59e0b" />
        </marker>
        <marker id="ad-arrow-cyan" viewBox="0 0 10 7" refX="9" refY="3.5"
          markerWidth="8" markerHeight="6" orient="auto-start-reverse">
          <path d="M 0 0 L 10 3.5 L 0 7 Z" fill="#22d3ee" />
        </marker>
        <marker id="ad-arrow-red" viewBox="0 0 10 7" refX="9" refY="3.5"
          markerWidth="8" markerHeight="6" orient="auto-start-reverse">
          <path d="M 0 0 L 10 3.5 L 0 7 Z" fill="#ef4444" />
        </marker>

        <filter id="ad-glow" x="-15%" y="-15%" width="130%" height="130%">
          <feGaussianBlur stdDeviation="2.5" result="blur" />
          <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
        </filter>
      </defs>

      <!-- ═══════════════════════════════════════════════════════════
           TITLE
           ═══════════════════════════════════════════════════════════ -->
      <text x="560" y="22" text-anchor="middle" class="ad-title">Live Technical Architecture</text>

      <!-- ═══════════════════════════════════════════════════════════
           NODE: ODAS Sensor Arrays (×3)  — far left
           ═══════════════════════════════════════════════════════════ -->
      <g class="ad-node">
        <rect x="20" y="48" width="150" height="100" rx="10"
          fill="#1e293b" stroke="#334155" stroke-width="1.5" />
        <!-- Microphone icon -->
        <g transform="translate(38, 66)">
          <rect x="4" y="0" width="12" height="20" rx="6" fill="none" stroke="#60a5fa" stroke-width="1.5" />
          <path d="M 0 16 Q 0 30, 10 30 Q 20 30, 20 16" fill="none" stroke="#60a5fa" stroke-width="1.5" />
          <line x1="10" y1="30" x2="10" y2="38" stroke="#60a5fa" stroke-width="1.5" />
          <line x1="4" y1="38" x2="16" y2="38" stroke="#60a5fa" stroke-width="1.5" />
        </g>
        <text x="95" y="88" text-anchor="middle" class="ad-node-title" fill="#e2e8f0">ODAS Mic</text>
        <text x="95" y="104" text-anchor="middle" class="ad-node-title" fill="#e2e8f0">Arrays</text>
        <text x="95" y="124" text-anchor="middle" class="ad-node-sub" fill="#94a3b8">×3 (AZ-MA-1/2/3)</text>
        <!-- Signal waves -->
        <g transform="translate(40, 62)" opacity="0.4">
          <path d="M -6 -4 Q -12 10, -6 24" fill="none" stroke="#60a5fa" stroke-width="1" />
          <path d="M -12 -8 Q -20 10, -12 28" fill="none" stroke="#60a5fa" stroke-width="1" />
        </g>
      </g>

      <!-- ═══════════════════════════════════════════════════════════
           NODE: Data Simulator (Oracle VM) — separate top box
           ═══════════════════════════════════════════════════════════ -->
      <g class="ad-node">
        <rect x="240" y="38" width="180" height="80" rx="10"
          fill="#1e293b" stroke="#f59e0b" stroke-width="1.5" />
        <!-- Gear icon -->
        <g transform="translate(260, 52)">
          <circle cx="10" cy="10" r="7" fill="none" stroke="#f59e0b" stroke-width="1.5" />
          <circle cx="10" cy="10" r="3" fill="#f59e0b" />
          <line x1="10" y1="0" x2="10" y2="3" stroke="#f59e0b" stroke-width="2" />
          <line x1="10" y1="17" x2="10" y2="20" stroke="#f59e0b" stroke-width="2" />
          <line x1="0" y1="10" x2="3" y2="10" stroke="#f59e0b" stroke-width="2" />
          <line x1="17" y1="10" x2="20" y2="10" stroke="#f59e0b" stroke-width="2" />
        </g>
        <text x="330" y="68" text-anchor="middle" class="ad-node-title" fill="#fbbf24">Data Simulator</text>
        <text x="330" y="84" text-anchor="middle" class="ad-node-sub" fill="#94a3b8">Oracle VM (systemd)</text>
      </g>

      <!-- ═══════════════════════════════════════════════════════════
           NODE: LOB Localizer — separate bottom box
           ═══════════════════════════════════════════════════════════ -->
      <g class="ad-node">
        <rect x="240" y="146" width="180" height="80" rx="10"
          fill="#1e293b" stroke="#22d3ee" stroke-width="1.5" />
        <!-- Crosshair icon -->
        <g transform="translate(260, 162)">
          <circle cx="10" cy="10" r="6" fill="none" stroke="#22d3ee" stroke-width="1.3" />
          <line x1="10" y1="1" x2="10" y2="5" stroke="#22d3ee" stroke-width="1.3" />
          <line x1="10" y1="15" x2="10" y2="19" stroke="#22d3ee" stroke-width="1.3" />
          <line x1="1" y1="10" x2="5" y2="10" stroke="#22d3ee" stroke-width="1.3" />
          <line x1="15" y1="10" x2="19" y2="10" stroke="#22d3ee" stroke-width="1.3" />
        </g>
        <text x="330" y="178" text-anchor="middle" class="ad-node-title" fill="#22d3ee">LOB Localizer</text>
        <text x="330" y="194" text-anchor="middle" class="ad-node-sub" fill="#94a3b8">Oracle VM (systemd)</text>
        <text x="330" y="210" text-anchor="middle" class="ad-node-sub-detail" fill="#94a3b8">WLS Bearing Triangulation</text>
      </g>

      <!-- ═══════════════════════════════════════════════════════════
           NODE: OSH CSAPI Server — center
           ═══════════════════════════════════════════════════════════ -->
      <g class="ad-node">
        <rect x="510" y="48" width="180" height="130" rx="10"
          fill="#0f172a" stroke="#22c55e" stroke-width="2" filter="url(#ad-glow)" />
        <!-- Server rack icon -->
        <g transform="translate(530, 68)">
          <rect x="0" y="0" width="24" height="8" rx="2" fill="none" stroke="#22c55e" stroke-width="1.3" />
          <rect x="0" y="12" width="24" height="8" rx="2" fill="none" stroke="#22c55e" stroke-width="1.3" />
          <rect x="0" y="24" width="24" height="8" rx="2" fill="none" stroke="#22c55e" stroke-width="1.3" />
          <circle cx="19" cy="4" r="1.5" fill="#22c55e" />
          <circle cx="19" cy="16" r="1.5" fill="#22c55e" />
          <circle cx="19" cy="28" r="1.5" fill="#22c55e" />
        </g>
        <text x="600" y="88" text-anchor="middle" class="ad-node-title" fill="#4ade80">OGC CSAPI</text>
        <text x="600" y="105" text-anchor="middle" class="ad-node-title" fill="#4ade80">Server</text>
        <text x="600" y="123" text-anchor="middle" class="ad-node-sub" fill="#86efac">Connected Sensors API</text>
        <text x="600" y="140" text-anchor="middle" class="ad-node-sub-detail" fill="#94a3b8">OpenSensorHub</text>
        <text x="600" y="155" text-anchor="middle" class="ad-node-sub-detail" fill="#64748b">129-80-248-53.sslip.io</text>
      </g>

      <!-- ═══════════════════════════════════════════════════════════
           NODE: CSAPI Explorer (this webapp)
           ═══════════════════════════════════════════════════════════ -->
      <g class="ad-node">
        <rect x="780" y="53" width="160" height="100" rx="10"
          fill="#1e293b" stroke="#60a5fa" stroke-width="1.5" />
        <!-- Browser icon -->
        <g transform="translate(800, 73)">
          <rect x="0" y="0" width="26" height="20" rx="3" fill="none" stroke="#60a5fa" stroke-width="1.5" />
          <line x1="0" y1="6" x2="26" y2="6" stroke="#60a5fa" stroke-width="1" />
          <circle cx="4" cy="3" r="1.2" fill="#ef4444" />
          <circle cx="9" cy="3" r="1.2" fill="#f59e0b" />
          <circle cx="14" cy="3" r="1.2" fill="#22c55e" />
        </g>
        <text x="860" y="93" text-anchor="middle" class="ad-node-title" fill="#93c5fd">CSAPI</text>
        <text x="860" y="110" text-anchor="middle" class="ad-node-title" fill="#93c5fd">Explorer</text>
        <text x="860" y="130" text-anchor="middle" class="ad-node-sub" fill="#94a3b8">This Web App</text>
      </g>

      <!-- ═══════════════════════════════════════════════════════════
           NODE: Analyst (You) — far right, person-at-desk icon
           ═══════════════════════════════════════════════════════════ -->
      <g class="ad-node">
        <rect x="1010" y="53" width="90" height="100" rx="10"
          fill="#1e293b" stroke="#a78bfa" stroke-width="1.5" />
        <!-- Person at desk (adapted from ConnectionDiagram for dark theme) -->
        <g transform="translate(1023, 60)">
          <!-- Person head -->
          <circle cx="14" cy="12" r="8" fill="#7c3aed" stroke="#a78bfa" stroke-width="1.3" />
          <!-- Person body -->
          <path d="M 4 38 Q 4 26, 14 26 Q 24 26, 24 38" fill="#6d28d9" stroke="#a78bfa" stroke-width="1" />
          <!-- Monitor -->
          <rect x="30" y="16" width="28" height="20" rx="3" fill="#1e1b4b" stroke="#a78bfa" stroke-width="1.2" />
          <rect x="33" y="19" width="22" height="14" rx="1" fill="#312e81" />
          <!-- Monitor stand -->
          <rect x="40" y="36" width="10" height="3" rx="1" fill="#6d28d9" />
          <rect x="36" y="39" width="18" height="2" rx="1" fill="#6d28d9" />
          <!-- Arm reaching to keyboard -->
          <path d="M 22 32 Q 28 34, 34 36" stroke="#a78bfa" stroke-width="1.5" fill="none" stroke-linecap="round" />
          <!-- Keyboard -->
          <rect x="32" y="42" width="22" height="4" rx="1" fill="#475569" stroke="#64748b" stroke-width="0.6" />
        </g>
        <text x="1055" y="130" text-anchor="middle" class="ad-node-sub" fill="#c4b5fd">Analyst (You)</text>
      </g>

      <!-- ═══════════════════════════════════════════════════════════
           EDGES
           ═══════════════════════════════════════════════════════════ -->

      <!-- Sensor Arrays ─ ─→ Data Simulator (dashed = "simulated") -->
      <line x1="170" y1="82" x2="238" y2="74"
        stroke="#60a5fa" stroke-width="2" stroke-dasharray="6 3"
        marker-end="url(#ad-arrow-blue)" opacity="0.6" />
      <text x="204" y="66" text-anchor="middle" class="ad-edge-label" fill="#94a3b8">simulates</text>

      <!-- Data Simulator → OSH Server (POST sensor obs) -->
      <line x1="420" y1="72" x2="508" y2="82"
        stroke="#f59e0b" stroke-width="2.5"
        marker-end="url(#ad-arrow-amber)" />
      <text x="464" y="66" text-anchor="middle" class="ad-edge-label" fill="#fbbf24">POST obs</text>

      <!-- ── LOB Localizer ⇄ OSH Server (bidirectional) ── -->
      <!-- Top: Server → LOB Localizer (GET LOBs to consume) -->
      <line x1="510" y1="162" x2="422" y2="170"
        stroke="#22c55e" stroke-width="2"
        marker-end="url(#ad-arrow-green)" />
      <text x="466" y="158" text-anchor="middle" class="ad-edge-label" fill="#86efac">GET LOBs</text>
      <!-- Bottom: LOB Localizer → Server (POST location fixes) -->
      <line x1="420" y1="190" x2="508" y2="182"
        stroke="#22d3ee" stroke-width="2"
        marker-end="url(#ad-arrow-cyan)" />
      <text x="466" y="204" text-anchor="middle" class="ad-edge-label" fill="#22d3ee">POST fixes</text>

      <!-- ── CSAPI Explorer ⇄ OSH Server (bidirectional) ── -->
      <!-- Top: Server → Explorer (GET data via CSAPI) -->
      <line x1="690" y1="90" x2="778" y2="90"
        stroke="#22c55e" stroke-width="2.5"
        marker-end="url(#ad-arrow-green)" />
      <text x="734" y="84" text-anchor="middle" class="ad-edge-label" fill="#86efac">GET data</text>
      <!-- Bottom: Explorer → Server (POST SENREPs) -->
      <line x1="780" y1="118" x2="692" y2="118"
        stroke="#ef4444" stroke-width="2"
        marker-end="url(#ad-arrow-red)" />
      <text x="734" y="132" text-anchor="middle" class="ad-edge-label" fill="#ef4444">POST SENREPs</text>

      <!-- ── Analyst ⇄ CSAPI Explorer (bidirectional) ── -->
      <!-- Top: Explorer → User (displays live data) -->
      <line x1="940" y1="90" x2="1008" y2="90"
        stroke="#60a5fa" stroke-width="2"
        marker-end="url(#ad-arrow-blue)" />
      <text x="974" y="84" text-anchor="middle" class="ad-edge-label" fill="#93c5fd">live data</text>
      <!-- Bottom: User → Explorer (submits SENREPs) -->
      <line x1="1010" y1="118" x2="942" y2="118"
        stroke="#ef4444" stroke-width="2"
        marker-end="url(#ad-arrow-red)" />
      <text x="974" y="132" text-anchor="middle" class="ad-edge-label" fill="#ef4444">SENREPs</text>

      <!-- ═══════════════════════════════════════════════════════════
           LEGEND (bottom)
           ═══════════════════════════════════════════════════════════ -->
      <g transform="translate(0, 250)">
        <text x="40" y="20" class="ad-legend-title" fill="#94a3b8">Data Flows:</text>

        <!-- Sim data -->
        <line x1="160" y1="16" x2="190" y2="16" stroke="#f59e0b" stroke-width="2" />
        <text x="196" y="20" class="ad-legend-item" fill="#cbd5e1">Simulated sensor data (LOB, SSL, SST, Health, Scene)</text>

        <!-- Loc estimates -->
        <line x1="160" y1="38" x2="190" y2="38" stroke="#22d3ee" stroke-width="2" />
        <text x="196" y="42" class="ad-legend-item" fill="#cbd5e1">Localizer fixes (WLS bearing intersection → location estimates)</text>

        <!-- CSAPI queries -->
        <line x1="160" y1="60" x2="190" y2="60" stroke="#22c55e" stroke-width="2" />
        <text x="196" y="64" class="ad-legend-item" fill="#cbd5e1">CSAPI queries (systems, datastreams, observations, deployments)</text>

        <!-- SENREP -->
        <line x1="160" y1="82" x2="190" y2="82" stroke="#ef4444" stroke-width="2" />
        <text x="196" y="86" class="ad-legend-item" fill="#cbd5e1">Analyst SENREP submissions (POST from this webapp)</text>
      </g>
    </svg>
  </div>
</template>

<style scoped>
.arch-diagram-wrap {
  width: 100%;
  margin: 1rem 0;
}
.arch-diagram-svg {
  width: 100%;
  max-width: 960px;
  height: auto;
  display: block;
  margin: 0 auto;
}

.ad-node { cursor: default; }

.ad-title {
  font-size: 14px;
  font-weight: 700;
  fill: #cbd5e1;
  font-family: system-ui, -apple-system, sans-serif;
  letter-spacing: 0.03em;
}
.ad-node-title {
  font-size: 13px;
  font-weight: 700;
  font-family: system-ui, -apple-system, sans-serif;
}
.ad-node-sub {
  font-size: 9.5px;
  font-weight: 500;
  font-family: system-ui, -apple-system, sans-serif;
}
.ad-node-sub-title {
  font-size: 11px;
  font-weight: 600;
  font-family: system-ui, -apple-system, sans-serif;
}
.ad-node-sub-detail {
  font-size: 9px;
  font-weight: 400;
  font-family: system-ui, -apple-system, sans-serif;
}
.ad-edge-label {
  font-size: 9px;
  font-weight: 600;
  font-family: system-ui, -apple-system, sans-serif;
}
.ad-legend-title {
  font-size: 10px;
  font-weight: 700;
  font-family: system-ui, -apple-system, sans-serif;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
.ad-legend-item {
  font-size: 10px;
  font-weight: 400;
  font-family: system-ui, -apple-system, sans-serif;
}
</style>
