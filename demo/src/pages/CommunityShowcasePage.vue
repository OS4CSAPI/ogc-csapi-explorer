<script setup lang="ts">
import { ref } from 'vue'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Password from 'primevue/password'
import Panel from 'primevue/panel'
import Message from 'primevue/message'

// ── Client-side auth gate (same pattern as SimulatorAdminPage) ───────────
const AUTH_USER = 'admin'
const AUTH_PASS = 'admin'
const SESSION_KEY = 'community-auth'

const authenticated = ref(sessionStorage.getItem(SESSION_KEY) === 'true')
const loginUser = ref('')
const loginPass = ref('')
const loginError = ref('')

function attemptLogin() {
  if (loginUser.value === AUTH_USER && loginPass.value === AUTH_PASS) {
    authenticated.value = true
    sessionStorage.setItem(SESSION_KEY, 'true')
    loginError.value = ''
  } else {
    loginError.value = 'Invalid credentials'
  }
}

function logout() {
  authenticated.value = false
  sessionStorage.removeItem(SESSION_KEY)
}

const activeTab = ref<'map' | 'dashboard' | 'ml'>('map')
</script>

<template>
  <div class="showcase-page">
    <!-- Header -->
    <div class="showcase-header">
      <h2><i class="pi pi-users"></i> Community Showcase</h2>
      <p class="subtitle">Third-party projects built on top of the live CSAPI server</p>
    </div>

    <!-- Auth gate -->
    <div v-if="!authenticated" class="login-gate">
      <Panel header="Authentication Required" class="login-panel">
        <p class="login-desc">This page is restricted while we await permission to publicly showcase community contributions. Enter admin credentials to preview.</p>
        <div class="login-form">
          <div class="login-field">
            <label for="comm-user">Username</label>
            <InputText id="comm-user" v-model="loginUser" placeholder="Username" @keyup.enter="attemptLogin" />
          </div>
          <div class="login-field">
            <label for="comm-pass">Password</label>
            <Password id="comm-pass" v-model="loginPass" placeholder="Password" :feedback="false" toggleMask @keyup.enter="attemptLogin" />
          </div>
          <Message v-if="loginError" severity="error" :closable="false" class="mt-2">{{ loginError }}</Message>
          <Button label="Sign In" icon="pi pi-sign-in" @click="attemptLogin" class="mt-3 login-btn" />
        </div>
      </Panel>
    </div>

    <!-- Authenticated content -->
    <template v-else>

    <div class="auth-toolbar">
      <Button label="Sign Out" icon="pi pi-sign-out" severity="secondary" size="small" text @click="logout" />
    </div>

    <!-- Featured Project -->
    <div class="project-card">
      <div class="project-banner">
        <div class="project-title-row">
          <div>
            <h3>CSAPI LiveML Pipeline</h3>
            <p class="author">by <strong>Narasimha Sharma Narayanam</strong> &mdash; Founder, Aganitha Space</p>
          </div>
          <a
            href="https://github.com/OS4CSAPI"
            target="_blank"
            rel="noopener noreferrer"
            class="github-link"
          >
            <i class="pi pi-github"></i> View on GitHub
          </a>
        </div>
      </div>

      <div class="project-description">
        <p>
          After the OGC 134th Member Meeting, Narasimha discovered the public CSAPI demo server and
          built a full ML-powered intelligence pipeline entirely in a Google Colab notebook. Using only
          standard HTTP requests against the CSAPI endpoints, the pipeline:
        </p>
        <ul class="feature-list">
          <li><strong>Auto-discovers</strong> all systems, datastreams, and deployments via the API</li>
          <li><strong>Collects</strong> live LOB bearings, UAS location estimates, and SENREPs into CSV datasets</li>
          <li><strong>Visualizes</strong> sensor networks and UAS tracks on interactive Folium maps</li>
          <li><strong>Engineers ML features</strong> &mdash; speed, heading, turn rate, sensor count &mdash; from raw observation data</li>
          <li><strong>Detects anomalies</strong> using scikit-learn's Isolation Forest on live UAS tracking data</li>
          <li><strong>Predicts trajectory</strong> by extrapolating fix positions to estimate the next 5 UAS waypoints</li>
        </ul>
        <p class="interop-note">
          <i class="pi pi-check-circle"></i>
          This project validates the interoperability of the OGC Connected Systems API &mdash; a third party
          was able to build a complete ISR analysis pipeline with <em>zero custom integration code</em>,
          using only standard CSAPI endpoints and public credentials. The artifacts below are point-in-time
          snapshots from a single pipeline run.
        </p>
      </div>

      <!-- Tab bar -->
      <div class="tab-bar">
        <button
          :class="['tab-btn', { active: activeTab === 'map' }]"
          @click="activeTab = 'map'"
        >
          <i class="pi pi-map"></i> Sensor Map
        </button>
        <button
          :class="['tab-btn', { active: activeTab === 'dashboard' }]"
          @click="activeTab = 'dashboard'"
        >
          <i class="pi pi-chart-bar"></i> Intelligence Dashboard
        </button>
        <button
          :class="['tab-btn', { active: activeTab === 'ml' }]"
          @click="activeTab = 'ml'"
        >
          <i class="pi pi-sliders-h"></i> ML Analysis
        </button>
      </div>

      <!-- Tab content -->
      <div class="tab-content">
        <!-- Interactive Map -->
        <div v-if="activeTab === 'map'" class="tab-panel">
          <div class="panel-header">
            <h4>Sensor Network &amp; UAS Track (Snapshot)</h4>
            <p>Point-in-time Folium map captured from a single pipeline run. Shows sensor nodes (blue), UAS position history (red), LOB bearing lines (orange), and filed SENREPs. The map is pannable and zoomable, but the data is static &mdash; not polling the server.</p>
          </div>
          <div class="map-container">
            <iframe
              src="/csapi_live_map.html"
              class="map-iframe"
              title="CSAPI Live Map"
            ></iframe>
          </div>
        </div>

        <!-- Intelligence Dashboard -->
        <div v-if="activeTab === 'dashboard'" class="tab-panel">
          <div class="panel-header">
            <h4>6-Panel Intelligence Dashboard (Snapshot)</h4>
            <p>Static image from a single pipeline run. Shows UAS flight track with time-progression colorbar, LOB bearings from all 3 sensors over time, bearing uncertainty (std dev), latitude &amp; longitude time series, and contributing-sensors count per fix.</p>
          </div>
          <div class="dashboard-container">
            <img
              src="/csapi_dashboard.png"
              alt="CSAPI Intelligence Dashboard"
              class="dashboard-img"
            />
          </div>
        </div>

        <!-- ML Analysis -->
        <div v-if="activeTab === 'ml'" class="tab-panel">
          <div class="panel-header">
            <h4>Anomaly Detection &amp; Trajectory Prediction (Snapshot)</h4>
            <p>Static image from a single pipeline run. Isolation Forest anomaly detection on speed, turn rate, and sensor count features. Green dots are normal fixes; red X markers are anomalies. Purple dashed line shows predicted future trajectory.</p>
          </div>
          <div class="dashboard-container">
            <img
              src="/csapi_ml_dashboard.png"
              alt="CSAPI ML Analysis Dashboard"
              class="dashboard-img"
            />
          </div>
        </div>
      </div>

      <!-- Tech stack -->
      <div class="tech-stack">
        <h4>Technology Stack</h4>
        <div class="tech-badges">
          <span class="badge">Python</span>
          <span class="badge">Google Colab</span>
          <span class="badge">Folium</span>
          <span class="badge">Matplotlib</span>
          <span class="badge">scikit-learn</span>
          <span class="badge">Pandas</span>
          <span class="badge">OGC CSAPI</span>
          <span class="badge">SensorThings</span>
        </div>
      </div>
    </div>

    </template><!-- /v-else -->
  </div>
</template>

<style scoped>
.showcase-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 1.5rem;
}

.showcase-header {
  margin-bottom: 1.5rem;
}

/* Auth gate */
.login-gate {
  display: flex;
  justify-content: center;
  margin-top: 2rem;
}

.login-panel {
  max-width: 400px;
  width: 100%;
}

.login-desc {
  color: var(--text-color-secondary);
  margin-bottom: 1rem;
  line-height: 1.5;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.login-field {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.login-field label {
  font-weight: 600;
  font-size: 0.875rem;
}

.login-field .p-inputtext,
.login-field .p-password {
  width: 100%;
}

.login-btn {
  width: 100%;
}

.auth-toolbar {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 0.5rem;
}

.showcase-header h2 {
  margin: 0 0 0.25rem 0;
  font-size: 1.5rem;
  color: var(--primary-color, #60a5fa);
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.subtitle {
  margin: 0;
  color: var(--text-color-secondary, #94a3b8);
  font-size: 0.95rem;
}

.project-card {
  background: var(--surface-card, #1e293b);
  border: 1px solid var(--surface-border, #334155);
  border-radius: 12px;
  overflow: hidden;
}

.project-banner {
  background: linear-gradient(135deg, #1e3a5f 0%, #0f172a 100%);
  padding: 1.5rem;
  border-bottom: 1px solid var(--surface-border, #334155);
}

.project-title-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  flex-wrap: wrap;
  gap: 1rem;
}

.project-title-row h3 {
  margin: 0;
  font-size: 1.3rem;
  color: #ffffff;
}

.author {
  margin: 0.25rem 0 0 0;
  color: #94a3b8;
  font-size: 0.9rem;
}

.github-link {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.4rem 0.8rem;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 6px;
  color: #e2e8f0;
  text-decoration: none;
  font-size: 0.85rem;
  transition: background 0.2s;
}

.github-link:hover {
  background: rgba(255, 255, 255, 0.2);
}

.project-description {
  padding: 1.25rem 1.5rem;
  color: var(--text-color, #e2e8f0);
  line-height: 1.7;
}

.project-description p {
  margin: 0 0 0.75rem 0;
}

.feature-list {
  margin: 0.5rem 0 1rem 0;
  padding-left: 1.5rem;
}

.feature-list li {
  margin-bottom: 0.35rem;
  line-height: 1.6;
}

.interop-note {
  background: rgba(34, 197, 94, 0.1);
  border: 1px solid rgba(34, 197, 94, 0.25);
  border-radius: 8px;
  padding: 0.75rem 1rem;
  color: #86efac;
  font-size: 0.9rem;
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
}

.interop-note i {
  margin-top: 0.15rem;
  color: #22c55e;
}

/* Tabs */
.tab-bar {
  display: flex;
  border-top: 1px solid var(--surface-border, #334155);
  border-bottom: 1px solid var(--surface-border, #334155);
  background: rgba(0, 0, 0, 0.2);
}

.tab-btn {
  flex: 1;
  padding: 0.75rem 1rem;
  background: none;
  border: none;
  border-bottom: 3px solid transparent;
  color: var(--text-color-secondary, #94a3b8);
  font-size: 0.9rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.4rem;
  transition: all 0.2s;
}

.tab-btn:hover {
  color: var(--text-color, #e2e8f0);
  background: rgba(255, 255, 255, 0.03);
}

.tab-btn.active {
  color: var(--primary-color, #60a5fa);
  border-bottom-color: var(--primary-color, #60a5fa);
  background: rgba(96, 165, 250, 0.05);
}

.tab-content {
  padding: 1.25rem 1.5rem;
}

.panel-header {
  margin-bottom: 1rem;
}

.panel-header h4 {
  margin: 0 0 0.35rem 0;
  color: var(--primary-color, #60a5fa);
  font-size: 1rem;
}

.panel-header p {
  margin: 0;
  color: var(--text-color-secondary, #94a3b8);
  font-size: 0.85rem;
  line-height: 1.5;
}

.map-container {
  border: 1px solid var(--surface-border, #334155);
  border-radius: 8px;
  overflow: hidden;
}

.map-iframe {
  width: 100%;
  height: 500px;
  border: none;
}

.dashboard-container {
  border: 1px solid var(--surface-border, #334155);
  border-radius: 8px;
  overflow: hidden;
  background: #0d1117;
}

.dashboard-img {
  width: 100%;
  height: auto;
  display: block;
}

/* Tech stack badges */
.tech-stack {
  padding: 1rem 1.5rem;
  border-top: 1px solid var(--surface-border, #334155);
}

.tech-stack h4 {
  margin: 0 0 0.5rem 0;
  color: var(--text-color-secondary, #94a3b8);
  font-size: 0.85rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.tech-badges {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
}

.badge {
  padding: 0.25rem 0.6rem;
  background: rgba(96, 165, 250, 0.12);
  border: 1px solid rgba(96, 165, 250, 0.25);
  border-radius: 12px;
  color: #93c5fd;
  font-size: 0.8rem;
}

/* Responsive */
@media (max-width: 768px) {
  .tab-btn {
    font-size: 0.8rem;
    padding: 0.6rem 0.5rem;
  }

  .map-iframe {
    height: 350px;
  }

  .project-title-row {
    flex-direction: column;
  }
}
</style>
