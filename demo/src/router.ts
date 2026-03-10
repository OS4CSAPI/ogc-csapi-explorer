import { createRouter, createWebHistory } from 'vue-router'
import ServerConnectPage from './pages/ServerConnectPage.vue'
import ResourceExplorerPage from './pages/ResourceExplorerPage.vue'
import MapViewPage from './pages/MapViewPage.vue'
import SmokeTestPage from './pages/SmokeTestPage.vue'
import DemoPage from './pages/DemoPage.vue'
import SimulatorAdminPage from './pages/SimulatorAdminPage.vue'
import CommunityShowcasePage from './pages/CommunityShowcasePage.vue'
import LiveAnalyticsPage from './pages/LiveAnalyticsPage.vue'

const routes = [
  {
    path: '/',
    name: 'connect',
    component: ServerConnectPage,
  },
  {
    path: '/explore/:resourceType?',
    name: 'explore',
    component: ResourceExplorerPage,
    props: true,
  },
  {
    path: '/map',
    name: 'map',
    component: MapViewPage,
  },
  {
    path: '/smoke-test',
    name: 'smoke-test',
    component: SmokeTestPage,
  },
  {
    path: '/demo',
    name: 'demo',
    component: DemoPage,
  },
  {
    path: '/admin',
    name: 'admin',
    component: SimulatorAdminPage,
  },
  {
    path: '/community',
    name: 'community',
    component: CommunityShowcasePage,
  },
  {
    path: '/analytics',
    name: 'analytics',
    component: LiveAnalyticsPage,
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
