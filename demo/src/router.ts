import { createRouter, createWebHistory } from 'vue-router'
import ServerConnectPage from './pages/ServerConnectPage.vue'
import ResourceExplorerPage from './pages/ResourceExplorerPage.vue'

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
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
