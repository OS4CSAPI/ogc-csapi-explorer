import { createRouter, createWebHistory } from 'vue-router'
import ServerConnectPage from './pages/ServerConnectPage.vue'
import ResourceExplorerPage from './pages/ResourceExplorerPage.vue'
import MapViewPage from './pages/MapViewPage.vue'

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
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
