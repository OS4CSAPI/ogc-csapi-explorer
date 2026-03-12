<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { connection, type ConnectionWarning } from '../state'
import { initializeBuilder, destroyBuilder } from '../csapi-bridge'
import InputText from 'primevue/inputtext'
import Password from 'primevue/password'
import Button from 'primevue/button'
import Select from 'primevue/select'
import Panel from 'primevue/panel'
import Message from 'primevue/message'
import ProgressSpinner from 'primevue/progressspinner'
import ConnectionDiagram from '../components/ConnectionDiagram.vue'

const presets = [
  { label: 'OSH (OS4CSAPI)', proxyPath: '/api/osh', description: 'Oracle Cloud — HTTPS + basic auth', externalUrl: 'https://129-80-248-53.sslip.io/sensorhub/api', requiresAuth: true },
  { label: 'OSH SensorHub', proxyPath: '/api/osh-do', description: 'DigitalOcean — requires basic auth', externalUrl: 'http://45.55.99.236:8080/sensorhub/api', requiresAuth: true },
  { label: '52North CSA Demo', proxyPath: '/api/52north', description: 'Public demo — no auth required', externalUrl: 'https://csa.demo.52north.org', requiresAuth: false },
  { label: 'Custom URL', proxyPath: '', description: 'Enter a custom server URL', externalUrl: '', requiresAuth: false },
]

const selectedPreset = ref(presets[0])
const customUrl = ref('')
const username = ref('')
const password = ref('')
const connecting = ref(false)
const error = ref('')
const warnings = ref<ConnectionWarning[]>([])

/** Diagram state derived from connection status */
const connectionState = computed<'idle' | 'connecting' | 'connected' | 'error'>(() => {
  if (connecting.value) return 'connecting'
  if (error.value) return 'error'
  if (connection.connected) return 'connected'
  return 'idle'
})
const diagramServerLabel = computed(() => selectedPreset.value?.label || customUrl.value || '')

// Force a clean slate every time the user navigates to this page
onMounted(() => {
  if (connection.connected) disconnect()
})

// Disconnect and reset when switching servers
watch(selectedPreset, () => {
  if (connection.connected) disconnect()
  username.value = ''
  password.value = ''
  error.value = ''
})

// Display data (not shared — only shown on this page)
const landingPage = ref<any>(null)
const conformance = ref<string[]>([])
const collections = ref<any[]>([])

function getEffectiveUrl(): string {
  return selectedPreset.value?.proxyPath || customUrl.value
}

function getAuthHeaders(): Record<string, string> {
  if (username.value && password.value) {
    return { Authorization: 'Basic ' + btoa(`${username.value}:${password.value}`) }
  }
  return {}
}

async function connect() {
  error.value = ''
  connecting.value = true
  landingPage.value = null
  conformance.value = []
  collections.value = []
  warnings.value = []

  const baseUrl = getEffectiveUrl()
  if (!baseUrl) {
    error.value = 'Please enter a server URL or select a preset.'
    connecting.value = false
    return
  }

  if (selectedPreset.value?.requiresAuth && (!username.value || !password.value)) {
    error.value = 'This server requires authentication. Please enter a username and password.'
    connecting.value = false
    return
  }

  const headers = getAuthHeaders()

  try {
    // Landing page
    const landingRes = await fetch(baseUrl + '/', { headers })
    if (!landingRes.ok) throw new Error(`Landing page: ${landingRes.status} ${landingRes.statusText}`)
    const landingData = await landingRes.json()
    landingPage.value = landingData

    // Conformance
    let conformanceFetchFailed = false
    try {
      const conformRes = await fetch(baseUrl + '/conformance', { headers })
      if (conformRes.ok) {
        const conformData = await conformRes.json()
        conformance.value = conformData.conformsTo || []
      } else {
        conformanceFetchFailed = true
      }
    } catch {
      conformanceFetchFailed = true
    }

    // Collections
    try {
      const collectionsRes = await fetch(baseUrl + '/collections', { headers })
      if (collectionsRes.ok) {
        const collectionsData = await collectionsRes.json()
        collections.value = collectionsData.collections || []
      }
    } catch { /* not fatal */ }

    // --- Credential verification ---
    // The landing page may be public (returns 200 regardless of credentials),
    // so verify credentials against an actual CSAPI resource endpoint.
    if (username.value && password.value) {
      try {
        const authCheckRes = await fetch(baseUrl + '/systems?limit=1', { headers })
        if (authCheckRes.status === 401 || authCheckRes.status === 403) {
          throw new Error(
            'Authentication failed — the server rejected the provided credentials. '
            + 'Please check your username and password.'
          )
        }
      } catch (authErr: any) {
        // Re-throw auth failures; swallow network/404 errors (endpoint may not exist)
        if (authErr.message?.includes('Authentication failed')) throw authErr
      }
    }

    // --- Dynamic warning detection ---
    const detectedWarnings: ConnectionWarning[] = []

    // 0. Transport security: HTTP vs HTTPS, SSL certificate, and CORS
    // Determine the actual external URL (not the proxy path)
    const actualExternalUrl = selectedPreset.value?.externalUrl || customUrl.value
    const isProxied = !!selectedPreset.value?.proxyPath

    if (actualExternalUrl && actualExternalUrl.startsWith('http://')) {
      detectedWarnings.push({
        severity: 'warn',
        summary: 'Unencrypted HTTP connection',
        detail: `The server URL (${actualExternalUrl}) uses plain HTTP. `
          + 'All traffic — including authentication credentials — is transmitted without '
          + 'encryption and can be intercepted. A production deployment should use HTTPS.',
      })
    } else if (actualExternalUrl && actualExternalUrl.startsWith('https://')) {
      detectedWarnings.push({
        severity: 'success',
        summary: 'HTTPS connection',
        detail: 'The server uses HTTPS — traffic is encrypted.',
      })
    }

    // For proxied connections, probe the external URL to detect SSL and CORS issues.
    // The dev proxy (changeOrigin + secure:false) hides both problems from the browser.
    if (isProxied && actualExternalUrl) {
      let sslOk = false

      // Detect mixed-content situation: page served over HTTPS, external URL is HTTP.
      // Browsers block these requests entirely — probing is impossible.
      const isMixedContent =
        window.location.protocol === 'https:' && actualExternalUrl.startsWith('http://')

      // SSL check: no-cors mode still requires a valid TLS handshake.
      // If this fails, the cert is bad (expired, self-signed, etc.).
      if (isMixedContent) {
        // Can't probe — browser blocks mixed content before any network request.
        // Still allow CORS checks below by setting sslOk = true (it's irrelevant for HTTP).
        sslOk = true
        detectedWarnings.push({
          severity: 'info',
          summary: 'Mixed-content limitation',
          detail: `The external server at ${actualExternalUrl} uses HTTP but this app is served `
            + 'over HTTPS. Browsers block direct HTTP requests from HTTPS pages (mixed content), '
            + 'so SSL and CORS could not be probed directly. The app connects through a proxy '
            + 'that bypasses this limitation.',
        })
      } else {
        try {
          const controller = new AbortController()
          const timeout = setTimeout(() => controller.abort(), 5000)
          await fetch(actualExternalUrl, { mode: 'no-cors', signal: controller.signal })
          clearTimeout(timeout)
          sslOk = true
          if (actualExternalUrl.startsWith('https://')) {
            detectedWarnings.push({
              severity: 'success',
              summary: 'SSL certificate valid',
              detail: 'The server\'s HTTPS certificate was validated successfully by the browser.',
            })
          }
        } catch {
          if (actualExternalUrl.startsWith('https://')) {
            detectedWarnings.push({
              severity: 'warn',
              summary: 'SSL certificate issue',
              detail: `The server's HTTPS certificate at ${actualExternalUrl} could not be validated `
                + 'by the browser. The app connected through a development proxy that bypasses SSL '
                + 'validation, but a direct browser connection would fail. The certificate may be '
                + 'expired, self-signed, or misconfigured. CORS support could not be verified '
                + 'because the SSL handshake failed first.',
            })
          }
        }
      }

      // CORS check: if SSL passed (or the server is HTTP), test with mode: 'cors'.
      // A no-cors success + cors failure = the server doesn't send CORS headers.
      // For auth-required servers, a bare GET returns 401 — if the 401 lacks CORS
      // headers the browser throws a network error indistinguishable from "no CORS".
      // So we also try an OPTIONS preflight (which CORS filters handle without auth)
      // and accept any readable response (even 401) as proof of CORS support.
      if (sslOk) {
        let corsDetected = false
        // Strategy 1: plain cors GET — works for public endpoints
        try {
          const controller = new AbortController()
          const timeout = setTimeout(() => controller.abort(), 5000)
          const resp = await fetch(actualExternalUrl, { mode: 'cors', signal: controller.signal })
          clearTimeout(timeout)
          // Any readable response (even 401/403) means CORS headers were present
          corsDetected = true
          void resp
        } catch { /* CORS or network error */ }

        // Strategy 2: OPTIONS preflight — CORS filters typically respond without auth
        if (!corsDetected) {
          try {
            const controller = new AbortController()
            const timeout = setTimeout(() => controller.abort(), 5000)
            const resp = await fetch(actualExternalUrl, {
              method: 'OPTIONS',
              mode: 'cors',
              headers: { 'Access-Control-Request-Method': 'GET' },
              signal: controller.signal,
            })
            clearTimeout(timeout)
            corsDetected = true
            void resp
          } catch { /* CORS or network error */ }
        }

        if (corsDetected) {
          detectedWarnings.push({
            severity: 'success',
            summary: 'CORS headers present',
            detail: `The server at ${actualExternalUrl} includes CORS headers, allowing direct browser access from other origins.`,
          })
        } else {
          detectedWarnings.push({
            severity: 'warn',
            summary: 'CORS headers not provided',
            detail: `The server at ${actualExternalUrl} does not include CORS `
              + '(Cross-Origin Resource Sharing) headers in its responses. A browser-based '
              + 'application on a different origin would be blocked from accessing this API. '
              + 'This app connects through a development proxy that bypasses CORS, '
              + 'but a production web application would need the server to send '
              + 'Access-Control-Allow-Origin headers or use a backend proxy.',
          })
        }
      }
    }

    // 1. Conformance endpoint
    if (conformanceFetchFailed) {
      detectedWarnings.push({
        severity: 'warn',
        summary: 'Conformance endpoint unavailable',
        detail: 'The /conformance endpoint returned an error or could not be reached. '
          + 'The app cannot determine which API capabilities this server supports. '
          + 'The ogc-client library\'s OgcApiEndpoint class would be unable to discover server features.',
      })
    } else if (conformance.value.length === 0) {
      detectedWarnings.push({
        severity: 'warn',
        summary: 'No conformance classes declared',
        detail: 'The server\'s /conformance endpoint returned an empty list. '
          + 'Without conformance declarations, the ogc-client library\'s OgcApiEndpoint class '
          + 'would report no capabilities for this server.',
      })
    } else if (csapiConformance(conformance.value).length === 0) {
      detectedWarnings.push({
        severity: 'warn',
        summary: 'No CSAPI conformance classes',
        detail: `This server declares ${conformance.value.length} conformance class(es), `
          + 'but none relate to the OGC Connected Systems API (Part 1 or Part 2), SensorML, '
          + 'or SWE Common. The ogc-client library\'s OgcApiEndpoint class would report '
          + 'no CSAPI capabilities for this server.',
      })
    } else {
      const csapiCount = csapiConformance(conformance.value).length
      detectedWarnings.push({
        severity: 'success',
        summary: `${csapiCount} CSAPI conformance class${csapiCount !== 1 ? 'es' : ''}`,
        detail: `The server declares ${csapiCount} Connected Systems API / SensorML / SWE Common `
          + `conformance class${csapiCount !== 1 ? 'es' : ''} out of ${conformance.value.length} total.`,
      })
    }

    // 2. Collections link relation
    // The ogc-client library expects link rel "data" or the full OGC URI
    // "http://www.opengis.net/def/rel/ogc/1.0/data" in the root landing page
    // to discover the collections URL. Some servers (e.g. OSH) use rel "collections"
    // instead, which causes the library's collectionsUrl to resolve to null.
    const rootLinks: Array<{ rel?: string; href?: string }> = landingData?.links || []
    const hasDataRel = rootLinks.some((l: any) =>
      l.rel === 'data' || l.rel === 'http://www.opengis.net/def/rel/ogc/1.0/data'
    )
    const hasCollectionsRel = rootLinks.some((l: any) => l.rel === 'collections')
    if (!hasDataRel && hasCollectionsRel) {
      detectedWarnings.push({
        severity: 'warn',
        summary: 'Non-standard collections link relation',
        detail: 'The server\'s landing page advertises its collections endpoint using link rel '
          + '"collections" instead of the OGC API Common-specified "data" relation. '
          + 'The ogc-client library\'s OgcApiEndpoint class would fail to discover the '
          + 'collections URL, causing csapiCollections to return an empty array even though '
          + 'the server fully implements the Connected Systems API.',
      })
    } else if (!hasDataRel && !hasCollectionsRel) {
      detectedWarnings.push({
        severity: 'warn',
        summary: 'No collections link in landing page',
        detail: 'The server\'s landing page does not contain a link with rel "data" or '
          + '"collections" pointing to the collections endpoint. The ogc-client library\'s '
          + 'OgcApiEndpoint class would be unable to discover available collections.',
      })
    } else {
      detectedWarnings.push({
        severity: 'success',
        summary: 'Standard collections link relation',
        detail: 'The server\'s landing page provides a link with the OGC API Common-specified "data" '
          + 'relation, enabling the ogc-client library to discover collections correctly.',
      })
    }

    // 3. CSAPI resource link discovery
    const initResult = initializeBuilder(landingData, collections.value)
    if (initResult.usedFallback) {
      detectedWarnings.push({
        severity: 'warn',
        summary: 'CSAPI resource links not advertised',
        detail: 'No Connected Systems API resource links were found in the server\'s '
          + 'landing page or collection links. The app is assuming all 9 standard CSAPI '
          + 'resource types are available at their default paths. Some types may not '
          + 'actually be supported by this server.',
      })
    } else {
      detectedWarnings.push({
        severity: 'success',
        summary: `${initResult.discoveredTypes.length} CSAPI resource types discovered`,
        detail: `The server advertises ${initResult.discoveredTypes.length} Connected Systems API `
          + `resource type${initResult.discoveredTypes.length !== 1 ? 's' : ''} via landing page `
          + `or collection links: ${initResult.discoveredTypes.join(', ')}.`,
      })
    }

    // Store in shared state
    connection.connected = true
    connection.label = selectedPreset.value?.label || customUrl.value
    connection.baseUrl = baseUrl
    connection.authHeaders = headers
    connection.landingPage = landingData
    connection.conformance = conformance.value
    connection.collections = collections.value
    connection.warnings = detectedWarnings
    warnings.value = detectedWarnings

    console.log('[CSAPI Bridge] Builder initialized. Available resources:',
      Array.from(initResult.builder.availableResources))
    if (detectedWarnings.length > 0) {
      console.warn('[Connect] Detected warnings:', detectedWarnings.map(w => w.summary))
    }
  } catch (err: any) {
    error.value = err.message || 'Connection failed'
  } finally {
    connecting.value = false
  }
}

function disconnect() {
  destroyBuilder()
  connection.connected = false
  connection.label = ''
  connection.baseUrl = ''
  connection.authHeaders = {}
  connection.landingPage = null
  connection.conformance = []
  connection.collections = []
  connection.warnings = []
  landingPage.value = null
  conformance.value = []
  collections.value = []
  warnings.value = []
  error.value = ''
}

function csapiConformance(classes: string[]): string[] {
  return classes.filter(c =>
    c.includes('connected-systems') || c.includes('csapi') ||
    c.includes('swecommon') || c.includes('sensorml')
  )
}

function otherConformance(classes: string[]): string[] {
  return classes.filter(c =>
    !c.includes('connected-systems') && !c.includes('csapi') &&
    !c.includes('swecommon') && !c.includes('sensorml')
  )
}
</script>

<template>
  <div class="connect-page">
    <p class="intro-text">
      <strong>CSAPI Explorer</strong> is a lightweight client application designed to explore
      <a href="https://www.ogc.org/standards/ogc-api-connected-systems/" target="_blank" rel="noopener noreferrer">OGC API - Connected Systems (OGC CSAPI)</a>
      compliant servers. The GitHub for the CSAPI Explorer webapp is
      <a href="https://github.com/OS4CSAPI/ogc-csapi-explorer" target="_blank" rel="noopener noreferrer">here</a>
      and it is largely based on the OGC CSAPI Typescript Client Library
      <a href="https://github.com/OS4CSAPI/ogc-client" target="_blank" rel="noopener noreferrer">here</a>
      (currently under review for contribution to the Camp-To-Camp OGC Client library
      <a href="https://github.com/camptocamp/ogc-client/pull/136" target="_blank" rel="noopener noreferrer">camptocamp/ogc-client#136</a>).
      To be added to the growing
      <a href="https://github.com/OS4CSAPI" target="_blank" rel="noopener noreferrer">OS4CSAPI</a> community,
      please <strong>@Sam-Bolling</strong> in a comment.
      You are welcomed and encouraged to leave feedback
      <a href="https://github.com/orgs/OS4CSAPI/discussions/37" target="_blank" rel="noopener noreferrer">here</a>.
    </p>

    <ConnectionDiagram :state="connectionState" :serverLabel="diagramServerLabel" />

    <Panel header="Server Connection">
      <div class="form-grid">
        <div class="form-row">
          <label>Server</label>
          <Select v-model="selectedPreset" :options="presets" optionLabel="label" class="w-full" />
          <small class="hint">
            {{ selectedPreset?.description }}
            <a
              v-if="selectedPreset?.externalUrl"
              :href="selectedPreset.externalUrl"
              target="_blank"
              rel="noopener noreferrer"
              class="server-link"
            >
              <i class="pi pi-external-link"></i> {{ selectedPreset.externalUrl }}
            </a>
          </small>
        </div>

        <div v-if="!selectedPreset?.proxyPath" class="form-row">
          <label>Custom URL</label>
          <InputText v-model="customUrl" placeholder="https://example.com/api" class="w-full" @keyup.enter="connect" />
        </div>

        <div class="auth-row">
          <div class="form-row">
            <label>Username</label>
            <InputText v-model="username" :placeholder="selectedPreset?.requiresAuth ? 'required' : 'optional'" class="w-full" autocapitalize="none" @keyup.enter="connect" />
          </div>
          <div class="form-row">
            <label>Password</label>
            <Password v-model="password" :feedback="false" toggleMask :placeholder="selectedPreset?.requiresAuth ? 'required' : 'optional'" class="w-full" @keyup.enter="connect" />
          </div>
        </div>

        <div class="form-actions">
          <Button
            v-if="!connection.connected"
            label="Connect" icon="pi pi-link" :loading="connecting"
            @click="connect"
          />
          <Button
            v-else
            label="Disconnect" icon="pi pi-times" severity="secondary" @click="disconnect"
          />
        </div>
      </div>

      <Message v-if="error" severity="error" :closable="false" class="mt-3">{{ error }}</Message>

      <div v-if="connecting" class="connecting-spinner">
        <ProgressSpinner style="width: 32px; height: 32px" />
        <span>Connecting...</span>
      </div>
    </Panel>

    <!-- Results after connection -->
    <template v-if="connection.connected">
      <Panel header="Server Info" class="mt-4" toggleable>
        <div class="info-grid">
          <div v-if="landingPage?.title"><strong>Title:</strong> {{ landingPage.title }}</div>
          <div v-if="landingPage?.description"><strong>Description:</strong> {{ landingPage.description }}</div>
        </div>
      </Panel>

      <Panel header="Connection Diagnostics" class="mt-4" toggleable>
        <div class="warnings-list">
          <Message
            v-for="(w, i) in warnings"
            :key="i"
            :severity="w.severity"
            :closable="false"
            class="warning-message"
          >
            <div>
              <strong>{{ w.summary }}</strong>
              <p class="warning-detail">{{ w.detail }}</p>
            </div>
          </Message>
        </div>
        <p class="text-muted mb-0">Green items passed standard OGC API checks. Amber items indicate where the app had to bypass or work around expected behavior.</p>
      </Panel>

      <Panel v-if="conformance.length > 0" header="Conformance Classes" class="mt-4" toggleable>
        <div v-if="csapiConformance(conformance).length > 0">
          <h4 class="mt-0">CSAPI / SensorML / SWE Common</h4>
          <ul class="conformance-list">
            <li v-for="c in csapiConformance(conformance)" :key="c">{{ c }}</li>
          </ul>
        </div>
        <div v-if="otherConformance(conformance).length > 0">
          <h4>Other</h4>
          <ul class="conformance-list">
            <li v-for="c in otherConformance(conformance)" :key="c">{{ c }}</li>
          </ul>
        </div>
        <p class="text-muted mb-0">Total: {{ conformance.length }} conformance classes</p>
      </Panel>

      <Panel v-if="collections.length > 0" header="Collections" class="mt-4" toggleable>
        <table class="collections-table">
          <thead>
            <tr><th>ID</th><th>Title</th><th>Description</th></tr>
          </thead>
          <tbody>
            <tr v-for="col in collections" :key="col.id">
              <td><code>{{ col.id }}</code></td>
              <td>{{ col.title || '—' }}</td>
              <td>{{ col.description || '—' }}</td>
            </tr>
          </tbody>
        </table>
      </Panel>

      <Panel header="Raw Response" class="mt-4" toggleable collapsed>
        <pre class="raw-json">{{ JSON.stringify({ landingPage, conformance, collections }, null, 2) }}</pre>
      </Panel>
    </template>
  </div>
</template>

<style scoped>
.connect-page {
  max-width: 640px;
  margin: 2rem auto;
  padding: 0 1rem;
}
.intro-text {
  font-size: 0.88rem;
  line-height: 1.6;
  color: #475569;
  margin: 0 0 0.5rem;
}
.intro-text a {
  color: #3b82f6;
  text-decoration: none;
}
.intro-text a:hover {
  text-decoration: underline;
}
.form-grid { display: flex; flex-direction: column; gap: 0.75rem; }
.form-row { display: flex; flex-direction: column; gap: 0.2rem; }
.form-row label { font-weight: 600; font-size: 0.85rem; }
.auth-row { display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; }
@media (max-width: 768px) {
  .auth-row { grid-template-columns: 1fr; }
  .connect-page { margin: 1rem auto; }
}
.hint { color: #64748b; font-size: 0.85rem; }
.server-link { display: inline-flex; align-items: center; gap: 0.25rem; margin-left: 0.5rem; color: #3b82f6; text-decoration: none; font-size: 0.82rem; }
.server-link:hover { text-decoration: underline; }
.server-link .pi { font-size: 0.75rem; }
.form-actions { display: flex; gap: 0.5rem; }
.w-full { width: 100%; }
.mt-0 { margin-top: 0; }
.mt-3 { margin-top: 0.75rem; }
.mt-4 { margin-top: 1rem; }
.mb-0 { margin-bottom: 0; }
.text-muted { color: #64748b; }
.connecting-spinner { display: flex; align-items: center; gap: 0.75rem; margin-top: 1rem; color: #64748b; }
.info-grid { display: flex; flex-direction: column; gap: 0.5rem; }
.conformance-list { list-style: none; padding: 0; margin: 0; }
.conformance-list li { padding: 0.25rem 0; font-size: 0.85rem; font-family: monospace; word-break: break-all; border-bottom: 1px solid #f1f5f9; }
.collections-table { width: 100%; border-collapse: collapse; font-size: 0.9rem; }
.collections-table th, .collections-table td { padding: 0.5rem 0.75rem; text-align: left; border-bottom: 1px solid #e2e8f0; }
.collections-table th { background: #f8fafc; font-weight: 600; }
.collections-table code { background: #f1f5f9; padding: 0.1rem 0.3rem; border-radius: 3px; font-size: 0.85rem; }
.raw-json { background: #f8fafc; padding: 1rem; border-radius: 6px; overflow-x: auto; font-size: 0.8rem; max-height: 400px; overflow-y: auto; margin: 0; }
.warnings-list { display: flex; flex-direction: column; gap: 0.5rem; margin-bottom: 0.75rem; }
.warning-message { margin: 0; }
.warning-detail { margin: 0.25rem 0 0; font-size: 0.85rem; opacity: 0.9; line-height: 1.4; }
</style>
