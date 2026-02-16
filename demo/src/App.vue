<script setup lang="ts">
import { connection } from './state'
</script>

<template>
  <header class="app-header">
    <div class="header-left">
      <h1><router-link to="/" class="title-link">CSAPI Explorer</router-link></h1>
    </div>
    <div class="header-right">
      <template v-if="connection.connected">
        <span class="connection-badge">
          <i class="pi pi-check-circle"></i>
          {{ connection.label }}
        </span>
        <router-link to="/explore/systems" class="nav-link">
          <i class="pi pi-th-large"></i> Explorer
        </router-link>
        <router-link to="/map" class="nav-link">
          <i class="pi pi-map"></i> Map
        </router-link>
      </template>
      <router-link to="/" class="nav-link">
        <i class="pi pi-link"></i> Connect
      </router-link>
    </div>
  </header>
  <router-view />
</template>

<style scoped>
.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 1.5rem;
  border-bottom: 1px solid #e2e8f0;
  background: #f8fafc;
}
.app-header h1 {
  margin: 0;
  font-size: 1.4rem;
}
.title-link {
  text-decoration: none;
  color: inherit;
}
.header-right {
  display: flex;
  align-items: center;
  gap: 1rem;
}
.connection-badge {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  color: #16a34a;
  font-size: 0.85rem;
  font-weight: 600;
}
.nav-link {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  text-decoration: none;
  color: #3b82f6;
  font-size: 0.9rem;
  font-weight: 500;
}
.nav-link:hover {
  color: #1d4ed8;
}
</style>
