<script setup lang="ts">
import { computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { connection, RESOURCE_TYPES } from '../state'
import ResourcePanel from '../components/ResourcePanel.vue'

const router = useRouter()

const props = defineProps<{
  resourceType?: string
}>()

const activeType = computed(() => props.resourceType || 'systems')

// Redirect to connect page if not connected
watch(
  () => connection.connected,
  (connected) => {
    if (!connected) router.push('/')
  },
  { immediate: true }
)

function selectType(key: string) {
  router.push(`/explore/${key}`)
}
</script>

<template>
  <div v-if="connection.connected" class="explorer-layout">
    <!-- Sidebar -->
    <aside class="sidebar">
      <div class="sidebar-header">
        <span class="sidebar-title">Resource Types</span>
      </div>
      <div class="sidebar-section">
        <div class="section-label">Part 1 — Features</div>
        <button
          v-for="rt in RESOURCE_TYPES.filter(r => r.part === 1)"
          :key="rt.key"
          :class="['sidebar-item', { active: activeType === rt.key }]"
          @click="selectType(rt.key)"
        >
          <i :class="rt.icon"></i>
          <span>{{ rt.plural }}</span>
          <span v-if="rt.readOnly" class="badge-readonly">R/O</span>
        </button>
      </div>
      <div class="sidebar-section">
        <div class="section-label">Part 2 — Observations & Commands</div>
        <button
          v-for="rt in RESOURCE_TYPES.filter(r => r.part === 2)"
          :key="rt.key"
          :class="['sidebar-item', { active: activeType === rt.key }]"
          @click="selectType(rt.key)"
        >
          <i :class="rt.icon"></i>
          <span>{{ rt.plural }}</span>
        </button>
      </div>
    </aside>

    <!-- Main Content -->
    <main class="explorer-main">
      <ResourcePanel :resource-type="activeType" :key="activeType" />
    </main>
  </div>
</template>

<style scoped>
.explorer-layout {
  display: flex;
  height: calc(100vh - 53px); /* subtract header height */
}

.sidebar {
  width: 240px;
  min-width: 240px;
  background: #f8fafc;
  border-right: 1px solid #e2e8f0;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  padding: 1rem 1rem 0.5rem;
}

.sidebar-title {
  font-weight: 700;
  font-size: 0.85rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #64748b;
}

.sidebar-section {
  padding: 0.25rem 0;
}

.section-label {
  padding: 0.5rem 1rem 0.25rem;
  font-size: 0.75rem;
  font-weight: 600;
  color: #94a3b8;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

.sidebar-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  width: 100%;
  padding: 0.5rem 1rem;
  border: none;
  background: transparent;
  cursor: pointer;
  font-size: 0.9rem;
  color: #334155;
  text-align: left;
  transition: background 0.15s;
}

.sidebar-item:hover {
  background: #e2e8f0;
}

.sidebar-item.active {
  background: #3b82f6;
  color: white;
}

.sidebar-item i {
  font-size: 1rem;
  width: 1.2rem;
  text-align: center;
}

.badge-readonly {
  margin-left: auto;
  font-size: 0.65rem;
  background: #f1f5f9;
  color: #64748b;
  padding: 0.1rem 0.35rem;
  border-radius: 3px;
  font-weight: 600;
}

.sidebar-item.active .badge-readonly {
  background: rgba(255, 255, 255, 0.2);
  color: rgba(255, 255, 255, 0.8);
}

.explorer-main {
  flex: 1;
  overflow-y: auto;
  padding: 1.5rem;
}
</style>
