<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { getResourceType } from '../state'
import Tabs from 'primevue/tabs'
import TabList from 'primevue/tablist'
import Tab from 'primevue/tab'
import TabPanels from 'primevue/tabpanels'
import TabPanel from 'primevue/tabpanel'
import ResourceList from './ResourceList.vue'
import ResourceDetail from './ResourceDetail.vue'
import ResourceCreate from './ResourceCreate.vue'
import ResourceUpdate from './ResourceUpdate.vue'
import ResourceDelete from './ResourceDelete.vue'

const props = defineProps<{
  resourceType: string
  parentType?: string | null
  parentId?: string | null
  parentRelation?: string | null
  initialResourceId?: string | null
}>()

const rtInfo = computed(() => getResourceType(props.resourceType))
const activeTab = ref(0)
const selectedResourceId = ref<string | null>(null)
const selectedResource = ref<any>(null)

// Auto-select a resource and show its Detail tab when navigated with a direct resourceId
watch(
  () => props.initialResourceId,
  (id) => {
    if (id) {
      selectedResourceId.value = id
      selectedResource.value = null // will be fetched by ResourceDetail
      activeTab.value = 1
    }
  },
  { immediate: true }
)

function viewDetail(resource: any) {
  // Extract ID from GeoJSON feature or flat object
  const id = resource?.id || resource?.properties?.id || resource?.['@id'] || ''
  selectedResourceId.value = String(id)
  selectedResource.value = resource
  activeTab.value = 1 // switch to Detail tab
}

/** Sync selectedResourceId when ResourceDetail navigates in-place (e.g. subsystem drill-down) */
function onSelectResource(id: string) {
  selectedResourceId.value = id
  selectedResource.value = null // will be fetched by ResourceDetail
}

function editResource(resource: any) {
  const id = resource?.id || resource?.properties?.id || resource?.['@id'] || ''
  selectedResourceId.value = String(id)
  selectedResource.value = resource
  activeTab.value = 3 // switch to Update tab
}

function onCreated() {
  activeTab.value = 0 // go back to list to see the new resource
}

function onUpdated() {
  activeTab.value = 0
}

function onDeleted() {
  selectedResourceId.value = null
  selectedResource.value = null
  activeTab.value = 0
}
</script>

<template>
  <div v-if="rtInfo" class="resource-panel">
    <div class="panel-header">
      <i :class="rtInfo.icon" class="panel-icon"></i>
      <h2>{{ rtInfo.plural }}</h2>
      <span v-if="rtInfo.readOnly" class="readonly-badge">Read Only</span>
      <span class="part-badge">Part {{ rtInfo.part }}</span>
    </div>

    <Tabs :value="activeTab" @update:value="(v: any) => activeTab = v">
      <TabList>
        <Tab :value="0">List</Tab>
        <Tab :value="1">Detail</Tab>
        <Tab v-if="!rtInfo?.readOnly" :value="2">Create</Tab>
        <Tab v-if="!rtInfo?.readOnly" :value="3">Update</Tab>
        <Tab v-if="!rtInfo?.readOnly" :value="4">Delete</Tab>
      </TabList>
      <TabPanels>
        <TabPanel :value="0">
          <ResourceList
            :resource-type="resourceType"
            :parent-type="parentType"
            :parent-id="parentId"
            :parent-relation="parentRelation"
            @view="viewDetail"
            @edit="editResource"
          />
        </TabPanel>

        <TabPanel :value="1">
          <ResourceDetail
            :resource-type="resourceType"
            :resource-id="selectedResourceId"
            :resource="selectedResource"
            :nested-parent-type="parentType"
            :nested-parent-id="parentId"
            @selectResource="onSelectResource"
          />
        </TabPanel>

        <TabPanel v-if="!rtInfo?.readOnly" :value="2">
          <ResourceCreate
            :resource-type="resourceType"
            @created="onCreated"
          />
        </TabPanel>

        <TabPanel v-if="!rtInfo?.readOnly" :value="3">
          <ResourceUpdate
            :resource-type="resourceType"
            :resource-id="selectedResourceId"
            :resource="selectedResource"
            @updated="onUpdated"
          />
        </TabPanel>

        <TabPanel v-if="!rtInfo?.readOnly" :value="4">
          <ResourceDelete
            :resource-type="resourceType"
            :resource-id="selectedResourceId"
            @deleted="onDeleted"
          />
        </TabPanel>
      </TabPanels>
    </Tabs>
  </div>
</template>

<style scoped>
.resource-panel {
  max-width: 100%;
}

.panel-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.panel-header h2 {
  margin: 0;
  font-size: 1.4rem;
}

.panel-icon {
  font-size: 1.3rem;
  color: #3b82f6;
}

.readonly-badge {
  font-size: 0.7rem;
  background: #fef3c7;
  color: #92400e;
  padding: 0.15rem 0.5rem;
  border-radius: 4px;
  font-weight: 600;
}

.part-badge {
  font-size: 0.7rem;
  background: #e0e7ff;
  color: #3730a3;
  padding: 0.15rem 0.5rem;
  border-radius: 4px;
  font-weight: 600;
}
</style>
