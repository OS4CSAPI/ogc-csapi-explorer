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
      '/api/csapi-go': {
        target: 'https://129-80-248-53.sslip.io/csapi-go',
        changeOrigin: true,
        secure: true,
        rewrite: (path) => path.replace(/^\/api\/csapi-go/, ''),
      },
      '/api/52north': {
        target: 'https://csa.demo.52north.org',
        changeOrigin: true,
        secure: false, // their SSL cert is expired as of 2026-02-16
        rewrite: (path) => path.replace(/^\/api\/52north/, ''),
      },
      // OSH SensorHub on Oracle Cloud — primary: sslip.io, fallback: os4csapi-osh.duckdns.org
      // Production fallback is in functions/api/osh/[[path]].ts; dev proxy uses primary only.
      '/api/osh': {
        target: 'https://129-80-248-53.sslip.io/sensorhub/api',
        changeOrigin: true,
        secure: true,
        rewrite: (path) => path.replace(/^\/api\/osh/, ''),
        headers: {
          Authorization: 'Basic ' + Buffer.from('os4csapi:ogc134mm').toString('base64'),
        },
      },
      '/api/osh-do': {
        target: 'http://45.55.99.236:8080/sensorhub/api',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/osh-do/, ''),
      },
    },
  },
})
