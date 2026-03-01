<script setup lang="ts">
import { connection } from './state'
import os4csapiIcon from './assets/os4csapi-logo.svg'
</script>

<template>
  <header class="app-header">
    <div class="header-left">
      <router-link to="/" class="title-link">
        <img :src="os4csapiIcon" alt="OS4CSAPI" class="header-logo" />
        <h1>CSAPI Explorer</h1>
      </router-link>
    </div>
    <div class="header-right">
      <template v-if="connection.connected">
        <span class="connection-badge">
          <i class="pi pi-check-circle"></i>
          {{ connection.label }}
        </span>
        <router-link to="/smoke-test" class="nav-link">
          <i class="pi pi-bolt"></i> Smoke Test
        </router-link>
        <router-link to="/demo" class="nav-link">
          <i class="pi pi-play"></i> Demo
        </router-link>
        <router-link to="/explore/deployments" class="nav-link">
          <i class="pi pi-th-large"></i> Explorer
        </router-link>
        <router-link to="/map" class="nav-link">
          <i class="pi pi-map"></i> Map
        </router-link>
      </template>
      <router-link to="/" class="nav-link">
        <i class="pi pi-link"></i> Connect
      </router-link>
      <a href="https://github.com/OS4CSAPI" target="_blank" rel="noopener noreferrer" class="nav-link">
        <i class="pi pi-github"></i> GitHub
      </a>
    </div>
  </header>
  <main class="app-main">
    <router-view />
  </main>
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
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.header-logo {
  height: 36px;
  width: auto;
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
.app-main {
  flex: 1;
  overflow: auto;
  min-height: 0;
}
</style>
