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
      // The library's shared/xml-utils.ts imports @rgrove/parse-xml at runtime.
      // Since demo only uses CSAPI (JSON-only), this is never executed, but the
      // bundler still needs to resolve it. Point it at the root node_modules.
      '@rgrove/parse-xml': path.resolve(__dirname, '../node_modules/@rgrove/parse-xml'),
    },
  },
  server: {
    proxy: {
      '/api/52north': {
        target: 'https://csa.demo.52north.org',
        changeOrigin: true,
        secure: false, // their SSL cert is expired as of 2026-02-16
        rewrite: (path) => path.replace(/^\/api\/52north/, ''),
      },
      '/api/osh': {
        target: 'http://45.55.99.236:8080/sensorhub/api',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/osh/, ''),
      },
    },
  },
})
