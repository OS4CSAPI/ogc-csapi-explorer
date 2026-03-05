<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { connection } from './state'
import os4csapiIcon from './assets/os4csapi-logo.svg'

const router = useRouter()
const route = useRoute()
const mobileMenuOpen = ref(false)
const showNav = computed(() => connection.connected || route.name === 'demo' || route.name === 'community')

// Close mobile menu on any route change
watch(() => route.fullPath, () => { mobileMenuOpen.value = false })

function mobileNav(to: string) {
  mobileMenuOpen.value = false
  router.push(to)
}
</script>

<template>
  <header class="app-header">
    <div class="header-left">
      <router-link to="/" class="title-link">
        <img :src="os4csapiIcon" alt="OS4CSAPI" class="header-logo" />
        <h1>CSAPI Explorer</h1>
      </router-link>
    </div>
    <!-- Desktop nav -->
    <div class="header-right header-desktop">
      <template v-if="showNav">
        <span class="connection-badge">
          <i class="pi pi-check-circle"></i>
          {{ connection.label }}
        </span>
        <router-link to="/smoke-test" class="nav-link">
          <i class="pi pi-bolt"></i> Smoke Test
        </router-link>
        <router-link to="/demo" class="nav-link">
          <i class="pi pi-desktop"></i> Demo
        </router-link>
        <router-link to="/explore/deployments" class="nav-link">
          <i class="pi pi-th-large"></i> Explorer
        </router-link>
        <router-link to="/map" class="nav-link">
          <i class="pi pi-map"></i> Map
        </router-link>
        <router-link to="/admin/simulator" class="nav-link">
          <i class="pi pi-cog"></i> Simulator
        </router-link>
      </template>
      <router-link to="/community" class="nav-link">
        <i class="pi pi-users"></i> Community
      </router-link>
      <router-link to="/" class="nav-link">
        <i class="pi pi-link"></i> Connect
      </router-link>
      <a href="https://github.com/OS4CSAPI" target="_blank" rel="noopener noreferrer" class="nav-link">
        <i class="pi pi-github"></i> GitHub
      </a>
    </div>
    <!-- Mobile hamburger -->
    <button class="hamburger" @click="mobileMenuOpen = !mobileMenuOpen" aria-label="Toggle menu">
      <i :class="mobileMenuOpen ? 'pi pi-times' : 'pi pi-bars'"></i>
    </button>
    <!-- Mobile dropdown -->
    <Teleport to="body">
      <div v-if="mobileMenuOpen" class="mobile-menu-backdrop" @click="mobileMenuOpen = false"></div>
      <nav v-if="mobileMenuOpen" class="mobile-menu">
        <template v-if="showNav">
          <span class="connection-badge" style="justify-content: center">
            <i class="pi pi-check-circle"></i>
            {{ connection.label }}
          </span>
          <button class="mobile-menu-link" @click="mobileNav('/smoke-test')">
            <i class="pi pi-bolt"></i> Smoke Test
          </button>
          <button class="mobile-menu-link" @click="mobileNav('/explore/deployments')">
            <i class="pi pi-th-large"></i> Explorer
          </button>
          <button class="mobile-menu-link" @click="mobileNav('/map')">
            <i class="pi pi-map"></i> Map
          </button>
          <button class="mobile-menu-link" @click="mobileNav('/admin/simulator')">
            <i class="pi pi-cog"></i> Simulator
          </button>
        </template>
        <button class="mobile-menu-link" @click="mobileNav('/community')">
          <i class="pi pi-users"></i> Community
        </button>
        <button class="mobile-menu-link" @click="mobileNav('/')">
          <i class="pi pi-link"></i> Connect
        </button>
        <a href="https://github.com/OS4CSAPI" target="_blank" rel="noopener noreferrer" class="mobile-menu-link" @click="mobileMenuOpen = false">
          <i class="pi pi-github"></i> GitHub
        </a>
      </nav>
    </Teleport>
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
.nav-link-disabled {
  color: #94a3b8;
  cursor: not-allowed;
}
.app-main {
  flex: 1;
  overflow: auto;
  min-height: 0;
}

/* ─── Hamburger button (hidden on desktop) ─── */
.hamburger {
  display: none;
  align-items: center;
  justify-content: center;
  width: 38px;
  height: 38px;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  background: #fff;
  color: #334155;
  font-size: 1.15rem;
  cursor: pointer;
  flex-shrink: 0;
}

/* ─── Mobile dropdown menu ─── */
.mobile-menu-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.25);
  z-index: 999;
}
.mobile-menu {
  position: fixed;
  top: 53px;
  left: 0;
  right: 0;
  background: #fff;
  border-bottom: 1px solid #e2e8f0;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  display: flex;
  flex-direction: column;
  padding: 0.5rem 0;
  z-index: 1000;
}
.mobile-menu-link {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.7rem 1.25rem;
  font-size: 0.95rem;
  font-weight: 500;
  color: #3b82f6;
  text-decoration: none;
  background: none;
  border: none;
  cursor: pointer;
  width: 100%;
  text-align: left;
}
.mobile-menu-link:hover {
  background: #f1f5f9;
}

/* ─── Mobile breakpoint ─── */
@media (max-width: 768px) {
  .app-header {
    padding: 0.5rem 0.75rem;
    flex-shrink: 0;
  }
  .app-header h1 {
    font-size: 1.1rem;
  }
  .header-logo {
    height: 28px;
  }
  .header-desktop {
    display: none;
  }
  .hamburger {
    display: flex;
  }
  .app-main {
    flex: 1;
    overflow: auto;
    min-height: 0;
    -webkit-overflow-scrolling: touch;
  }
}
</style>
