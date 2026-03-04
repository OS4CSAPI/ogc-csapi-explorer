<script setup lang="ts">
// Demo page — being rebuilt
</script>

<template>
  <div class="demo-page">
    <!-- Scenario Brief -->
    <div class="scenario-brief">
      <h3>Demo Scenario</h3>
      <p>You are a defence intelligence analyst assigned to create and submit sensor reports (SENREPs) whenever actionable activity has been detected by the sensors you are assigned to monitor. Your operational workflow looks like this:</p>
    </div>
  </div>
</template>

<style scoped>
.demo-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 1.5rem;
}

.scenario-brief {
  background: var(--surface-card, #1e293b);
  border: 1px solid var(--surface-border, #334155);
  border-radius: 8px;
  padding: 1.25rem 1.5rem;
  margin-bottom: 1.5rem;
}

.scenario-brief h3 {
  margin: 0 0 0.5rem 0;
  font-size: 1.1rem;
  color: var(--primary-color, #60a5fa);
}

.scenario-brief p {
  margin: 0;
  line-height: 1.6;
  color: var(--text-color, #e2e8f0);
}
</style>
