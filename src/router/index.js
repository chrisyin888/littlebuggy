import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView,
    },
    {
      path: '/admin/update',
      name: 'adminHomepageUpdate',
      component: () => import('../views/AdminHomepageUpdateView.vue'),
    },
  ],
})

export default router
