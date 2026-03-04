<script setup lang="ts">
// Demo page — being rebuilt
</script>

<template>
  <div class="demo-page">
    <!-- Scenario Brief -->
    <div class="scenario-brief">
      <h3>Demo Scenario</h3>
      <p>You are a defence intelligence analyst assigned to create and submit sensor reports (SENREPs) whenever actionable activity has been detected by the sensors you are assigned to monitor. Your operational workflow looks like this:</p>
      <ol class="workflow-steps">
        <li>Watch and observe the displayed array of sensor detection ranges on our workstation</li>
        <li>Monitor the sensor data that is displayed as it comes in live in near-real-time</li>
        <li>Determine if the sensor data indicates the potential presence of a Unmanned Aircraft System (UAS)</li>
        <li>If the Location Estimation Process generates a location, select that location, create, and submit a SENREP</li>
      </ol>
      <p class="workstation-intro">The display below is your workstation and entry point into the live and historic mission data of your organization's enterprise data. The live technical architecture you are currently connected to looks like this:</p>
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

.workflow-steps {
  margin: 0.75rem 0;
  padding-left: 1.5rem;
  line-height: 1.8;
  color: var(--text-color, #e2e8f0);
}

.workflow-steps li {
  margin-bottom: 0.35rem;
}

.workstation-intro {
  margin-top: 0.75rem !important;
}
</style>
