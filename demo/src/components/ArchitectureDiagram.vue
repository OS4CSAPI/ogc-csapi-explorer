<script setup lang="ts">
/**
 * ArchitectureDiagram — SVG diagram showing the live demo architecture:
 *
 *   ┌─────────────┐     ┌──────────────┐     ┌──────────────────┐     ┌──────────┐
 *   │ ODAS Sensor  │────→│    Data       │────→│   OSH CSAPI      │←───│  CSAPI   │←── [Analyst]
 *   │ Arrays (×3)  │     │  Simulator    │     │    Server        │     │ Explorer │
 *   └─────────────┘     │              │     │                  │     └──────────┘
 *                        │  LOB         │────→│                  │
 *                        │  Localizer   │     │                  │
 *                        └──────────────┘     └──────────────────┘
 */
</script>

<template>
  <div class="arch-diagram-wrap">
    <svg viewBox="0 0 960 320" xmlns="http://www.w3.org/2000/svg" class="arch-diagram-svg">
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

        <filter id="ad-glow" x="-15%" y="-15%" width="130%" height="130%">
          <feGaussianBlur stdDeviation="2.5" result="blur" />
          <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
        </filter>
      </defs>

      <!-- ═══════════════════════════════════════════════════════════
           ROW LABELS (top)
           ═══════════════════════════════════════════════════════════ -->
      <text x="480" y="20" text-anchor="middle" class="ad-title">Live Technical Architecture</text>

      <!-- ═══════════════════════════════════════════════════════════
           NODE: ODAS Sensor Arrays (×3)  — left column
           ═══════════════════════════════════════════════════════════ -->
      <g class="ad-node">
        <rect x="20" y="60" width="160" height="100" rx="10"
          fill="#1e293b" stroke="#334155" stroke-width="1.5" />
        <!-- Microphone icon -->
        <g transform="translate(40, 80)">
          <!-- Mic body -->
          <rect x="4" y="0" width="12" height="20" rx="6" fill="none" stroke="#60a5fa" stroke-width="1.5" />
          <!-- Mic stand arc -->
          <path d="M 0 16 Q 0 30, 10 30 Q 20 30, 20 16" fill="none" stroke="#60a5fa" stroke-width="1.5" />
          <!-- Stand -->
          <line x1="10" y1="30" x2="10" y2="38" stroke="#60a5fa" stroke-width="1.5" />
          <line x1="4" y1="38" x2="16" y2="38" stroke="#60a5fa" stroke-width="1.5" />
        </g>
        <text x="100" y="98" text-anchor="middle" class="ad-node-title" fill="#e2e8f0">ODAS Mic</text>
        <text x="100" y="115" text-anchor="middle" class="ad-node-title" fill="#e2e8f0">Arrays</text>
        <text x="100" y="135" text-anchor="middle" class="ad-node-sub" fill="#94a3b8">×3 (AZ-MA-1/2/3)</text>

        <!-- Signal waves emanating -->
        <g transform="translate(42, 76)" opacity="0.4">
          <path d="M -6 -4 Q -12 10, -6 24" fill="none" stroke="#60a5fa" stroke-width="1" />
          <path d="M -12 -8 Q -20 10, -12 28" fill="none" stroke="#60a5fa" stroke-width="1" />
        </g>
      </g>

      <!-- ═══════════════════════════════════════════════════════════
           NODE: Data Simulator (Fly.io)
           ═══════════════════════════════════════════════════════════ -->
      <g class="ad-node">
        <rect x="240" y="45" width="190" height="130" rx="10"
          fill="#1e293b" stroke="#f59e0b" stroke-width="1.5" />
        <!-- Gear icon for simulator -->
        <g transform="translate(264, 62)">
          <circle cx="10" cy="10" r="7" fill="none" stroke="#f59e0b" stroke-width="1.5" />
          <circle cx="10" cy="10" r="3" fill="#f59e0b" />
          <!-- Gear teeth -->
          <line x1="10" y1="0" x2="10" y2="3" stroke="#f59e0b" stroke-width="2" />
          <line x1="10" y1="17" x2="10" y2="20" stroke="#f59e0b" stroke-width="2" />
          <line x1="0" y1="10" x2="3" y2="10" stroke="#f59e0b" stroke-width="2" />
          <line x1="17" y1="10" x2="20" y2="10" stroke="#f59e0b" stroke-width="2" />
        </g>
        <text x="335" y="72" text-anchor="middle" class="ad-node-title" fill="#fbbf24">Data</text>
        <text x="335" y="89" text-anchor="middle" class="ad-node-title" fill="#fbbf24">Simulator</text>
        <text x="335" y="106" text-anchor="middle" class="ad-node-sub" fill="#94a3b8">Fly.io Container</text>

        <!-- Separator line -->
        <line x1="252" y1="116" x2="418" y2="116" stroke="#334155" stroke-width="1" />

        <!-- LOB Localizer sub-section -->
        <g transform="translate(264, 126)">
          <!-- Crosshair icon -->
          <circle cx="10" cy="10" r="6" fill="none" stroke="#22d3ee" stroke-width="1.3" />
          <line x1="10" y1="1" x2="10" y2="5" stroke="#22d3ee" stroke-width="1.3" />
          <line x1="10" y1="15" x2="10" y2="19" stroke="#22d3ee" stroke-width="1.3" />
          <line x1="1" y1="10" x2="5" y2="10" stroke="#22d3ee" stroke-width="1.3" />
          <line x1="15" y1="10" x2="19" y2="10" stroke="#22d3ee" stroke-width="1.3" />
        </g>
        <text x="335" y="140" text-anchor="middle" class="ad-node-sub-title" fill="#22d3ee">LOB Localizer</text>
        <text x="335" y="155" text-anchor="middle" class="ad-node-sub-detail" fill="#94a3b8">WLS Triangulation</text>
      </g>

      <!-- ═══════════════════════════════════════════════════════════
           NODE: OSH CSAPI Server
           ═══════════════════════════════════════════════════════════ -->
      <g class="ad-node">
        <rect x="500" y="50" width="180" height="120" rx="10"
          fill="#0f172a" stroke="#22c55e" stroke-width="2" filter="url(#ad-glow)" />
        <!-- Server rack icon -->
        <g transform="translate(520, 72)">
          <rect x="0" y="0" width="24" height="8" rx="2" fill="none" stroke="#22c55e" stroke-width="1.3" />
          <rect x="0" y="12" width="24" height="8" rx="2" fill="none" stroke="#22c55e" stroke-width="1.3" />
          <rect x="0" y="24" width="24" height="8" rx="2" fill="none" stroke="#22c55e" stroke-width="1.3" />
          <circle cx="19" cy="4" r="1.5" fill="#22c55e" />
          <circle cx="19" cy="16" r="1.5" fill="#22c55e" />
          <circle cx="19" cy="28" r="1.5" fill="#22c55e" />
        </g>
        <text x="590" y="90" text-anchor="middle" class="ad-node-title" fill="#4ade80">OSH CSAPI</text>
        <text x="590" y="107" text-anchor="middle" class="ad-node-title" fill="#4ade80">Server</text>
        <text x="590" y="125" text-anchor="middle" class="ad-node-sub" fill="#86efac">Connected Sensors API</text>
        <text x="590" y="142" text-anchor="middle" class="ad-node-sub-detail" fill="#94a3b8">os4csapi-osh.duckdns.org</text>
      </g>

      <!-- ═══════════════════════════════════════════════════════════
           NODE: CSAPI Explorer (this webapp)
           ═══════════════════════════════════════════════════════════ -->
      <g class="ad-node">
        <rect x="750" y="60" width="180" height="100" rx="10"
          fill="#1e293b" stroke="#60a5fa" stroke-width="1.5" />
        <!-- Browser icon -->
        <g transform="translate(770, 80)">
          <rect x="0" y="0" width="26" height="20" rx="3" fill="none" stroke="#60a5fa" stroke-width="1.5" />
          <line x1="0" y1="6" x2="26" y2="6" stroke="#60a5fa" stroke-width="1" />
          <circle cx="4" cy="3" r="1.2" fill="#ef4444" />
          <circle cx="9" cy="3" r="1.2" fill="#f59e0b" />
          <circle cx="14" cy="3" r="1.2" fill="#22c55e" />
        </g>
        <text x="840" y="98" text-anchor="middle" class="ad-node-title" fill="#93c5fd">CSAPI</text>
        <text x="840" y="115" text-anchor="middle" class="ad-node-title" fill="#93c5fd">Explorer</text>
        <text x="840" y="135" text-anchor="middle" class="ad-node-sub" fill="#94a3b8">This Web App</text>
      </g>

      <!-- ═══════════════════════════════════════════════════════════
           NODE: Analyst (You) — far right
           ═══════════════════════════════════════════════════════════ -->

      <!-- ═══════════════════════════════════════════════════════════
           EDGES
           ═══════════════════════════════════════════════════════════ -->

      <!-- Sensor Arrays → Data Simulator (simulated sensor data) -->
      <line x1="180" y1="100" x2="238" y2="90"
        stroke="#60a5fa" stroke-width="2" stroke-dasharray="6 3"
        marker-end="url(#ad-arrow-blue)" opacity="0.7" />
      <text x="209" y="82" text-anchor="middle" class="ad-edge-label" fill="#94a3b8">simulates</text>

      <!-- Data Simulator → OSH Server (POST observations: LOB, SSL, SST, health, scene) -->
      <line x1="430" y1="90" x2="498" y2="90"
        stroke="#f59e0b" stroke-width="2.5"
        marker-end="url(#ad-arrow-amber)" />
      <text x="464" y="82" text-anchor="middle" class="ad-edge-label" fill="#fbbf24">POST obs</text>

      <!-- LOB Localizer → OSH Server (POST location estimates) -->
      <line x1="430" y1="140" x2="498" y2="120"
        stroke="#22d3ee" stroke-width="2"
        marker-end="url(#ad-arrow-cyan)" />
      <text x="464" y="146" text-anchor="middle" class="ad-edge-label" fill="#22d3ee">POST fixes</text>

      <!-- CSAPI Explorer ← OSH Server (GET via CSAPI) -->
      <line x1="680" y1="107" x2="748" y2="107"
        stroke="#22c55e" stroke-width="2.5"
        marker-end="url(#ad-arrow-green)" />
      <text x="714" y="100" text-anchor="middle" class="ad-edge-label" fill="#86efac">GET / CSAPI</text>

      <!-- ═══════════════════════════════════════════════════════════
           DATA FLOW LABELS (bottom)
           ═══════════════════════════════════════════════════════════ -->
      <g transform="translate(0, 200)">
        <!-- Legend row -->
        <text x="40" y="20" class="ad-legend-title" fill="#94a3b8">Data Flows:</text>

        <!-- Sim data -->
        <line x1="140" y1="16" x2="170" y2="16" stroke="#f59e0b" stroke-width="2" />
        <text x="176" y="20" class="ad-legend-item" fill="#cbd5e1">Simulated sensor data (LOB, SSL, SST, Health, Scene)</text>

        <!-- Loc estimates -->
        <line x1="140" y1="38" x2="170" y2="38" stroke="#22d3ee" stroke-width="2" />
        <text x="176" y="42" class="ad-legend-item" fill="#cbd5e1">Localizer fixes (WLS bearing intersection → location estimates)</text>

        <!-- CSAPI queries -->
        <line x1="140" y1="60" x2="170" y2="60" stroke="#22c55e" stroke-width="2" />
        <text x="176" y="64" class="ad-legend-item" fill="#cbd5e1">CSAPI queries (systems, datastreams, observations, deployments)</text>

        <!-- SENREP -->
        <line x1="140" y1="82" x2="170" y2="82" stroke="#ef4444" stroke-width="2" />
        <text x="176" y="86" class="ad-legend-item" fill="#cbd5e1">Analyst SENREP submissions (POST from this webapp)</text>
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
  max-width: 860px;
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
