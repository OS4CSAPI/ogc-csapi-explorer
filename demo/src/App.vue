<script setup lang="ts">
import ServerConnect from './components/ServerConnect.vue'
</script>

<template>
  <header class="app-header">
    <h1>CSAPI Explorer</h1>
    <p class="subtitle">Connected Systems API — Library Demo</p>
  </header>
  <main>
    <ServerConnect />
  </main>
</template>

<style scoped>
.app-header {
  text-align: center;
  padding: 1.5rem 1rem 1rem;
  border-bottom: 1px solid var(--p-surface-200, #e2e8f0);
  margin-bottom: 1.5rem;
}
.app-header h1 {
  margin: 0;
  font-size: 1.8rem;
}
.subtitle {
  margin: 0.25rem 0 0;
  color: var(--p-text-muted-color, #64748b);
  font-size: 0.95rem;
}
main {
  max-width: 960px;
  margin: 0 auto;
  padding: 0 1rem;
}
</style>
