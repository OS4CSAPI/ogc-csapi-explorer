import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@csapi': path.resolve(__dirname, '../src'),
      // Library source imports @rgrove/parse-xml transitively (via shared/errors.ts).
      // Resolve from root node_modules since lib deps are installed there.
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
