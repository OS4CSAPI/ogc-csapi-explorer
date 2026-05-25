import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  optimizeDeps: {
    exclude: ['milsymbol'],
  },
  resolve: {
    alias: {
      '@csapi': path.resolve(__dirname, '../src'),
      // The library's shared/xml-utils.ts imports @rgrove/parse-xml at runtime,
      // but the demo only uses CSAPI (JSON-only) so XML parsing is never called.
      // Point at a local stub so the build succeeds without the real package.
      '@rgrove/parse-xml': path.resolve(__dirname, 'src/stubs/parse-xml.ts'),
    },
  },
  server: {
    proxy: {
      '/api/csapi-go-v2': {
        target: 'https://129-80-248-53.sslip.io/csapi-go-v2',
        changeOrigin: true,
        secure: true,
        rewrite: (path) => path.replace(/^\/api\/csapi-go-v2/, ''),
        // The csapi-go-v2 backend emits 307 redirects from
        // /collections/{id}/items to a host-root path that drops the
        // /csapi-go-v2 prefix (upstream defect — observed 2026-05-09).
        // Without this rewrite, the browser follows the bad Location and
        // 404s. Re-attach our proxy prefix so the redirect stays inside the
        // proxy chain.
        configure: (proxy) => {
          proxy.on('proxyRes', (proxyRes) => {
            const status = proxyRes.statusCode || 0
            if (status < 300 || status >= 400) return
            const loc = proxyRes.headers['location']
            if (typeof loc !== 'string' || !loc) return
            try {
              const u = new URL(loc, 'https://129-80-248-53.sslip.io')
              if (u.hostname !== '129-80-248-53.sslip.io') return
              let p = u.pathname
              if (p.startsWith('/csapi-go-v2')) {
                p = '/api/csapi-go-v2' + p.slice('/csapi-go-v2'.length)
              } else {
                p = '/api/csapi-go-v2' + p
              }
              proxyRes.headers['location'] = p + u.search + u.hash
            } catch {
              /* leave Location unchanged on parse failure */
            }
          })
        },
      },
      // 52North connected-systems-pygeoapi on Oracle (Phase 9 live deploy).
      // No auth required. Documented in docs/research/phase-9 of ogc-client-CSAPI_2.
      '/api/csapi-pygeoapi': {
        target: 'https://129-80-248-53.sslip.io/csapi-pygeoapi',
        changeOrigin: true,
        secure: true,
        rewrite: (path) => path.replace(/^\/api\/csapi-pygeoapi/, ''),
      },
      '/api/52north': {
        target: 'https://csa.demo.52north.org',
        changeOrigin: true,
        secure: false, // their SSL cert is expired as of 2026-02-16
        rewrite: (path) => path.replace(/^\/api\/52north/, ''),
      },
      // OSH SensorHub on Oracle Cloud — primary: sslip.io, fallback: os4csapi-osh.duckdns.org.
      // No auth required. Production fallback is in functions/api/osh/[[path]].ts;
      // dev proxy uses primary only.
      '/api/osh': {
        target: 'https://129-80-248-53.sslip.io/sensorhub/api',
        changeOrigin: true,
        secure: true,
        rewrite: (path) => path.replace(/^\/api\/osh/, ''),
      },
      '/api/osh-do': {
        target: 'http://45.55.99.236:8080/sensorhub/api',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/osh-do/, ''),
      },
    },
  },
})
