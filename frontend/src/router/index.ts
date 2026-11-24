import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'Dashboard',
      component: () => import('@/views/DashboardView.vue'),
      meta: { title: 'Dashboard' },
    },
    {
      path: '/query',
      name: 'Query',
      component: () => import('@/views/QueryView.vue'),
      meta: { title: 'Query Interface' },
    },
    {
      path: '/graph',
      name: 'Graph',
      component: () => import('@/views/GraphView.vue'),
      meta: { title: 'Knowledge Graph' },
    },
    {
      path: '/papers',
      name: 'Papers',
      component: () => import('@/views/PapersView.vue'),
      meta: { title: 'Papers' },
    },
    {
      path: '/papers/:id',
      name: 'PaperDetail',
      component: () => import('@/views/PaperDetailView.vue'),
      meta: { title: 'Paper Detail' },
      props: true,
    },
    {
      path: '/citations',
      name: 'Citations',
      component: () => import('@/views/CitationsView.vue'),
      meta: { title: 'Citations' },
    },
    {
      path: '/entities',
      name: 'Entities',
      component: () => import('@/views/EntitiesView.vue'),
      meta: { title: 'Entities' },
    },
    {
      path: '/settings',
      name: 'Settings',
      component: () => import('@/views/SettingsView.vue'),
      meta: { title: 'Settings' },
    },
    {
      path: '/:pathMatch(.*)*',
      redirect: '/',
    },
  ],
})

router.beforeEach((to) => {
  document.title = `${to.meta.title ?? 'GraphRAG'} | GraphRAG`
})

export default router
