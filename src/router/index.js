import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import { notePageView } from '../lib/humanBeacon.js'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView,
    },
    {
      path: '/wait-times',
      name: 'waitTimes',
      component: () => import('../views/WaitTimesView.vue'),
    },
    {
      path: '/swim-lessons',
      name: 'swimLessons',
      component: () => import('../views/SwimLessonsView.vue'),
    },
    {
      path: '/registration',
      name: 'registration',
      component: () => import('../views/RegistrationView.vue'),
    },
    {
      path: '/guides/fever',
      name: 'feverGuide',
      component: () => import('../views/FeverGuideView.vue'),
    },
    {
      path: '/admin/update',
      name: 'adminHomepageUpdate',
      component: () => import('../views/AdminHomepageUpdateView.vue'),
    },
  ],
})

// Count route views per session for the human-visit beacon: a second page
// view within one session is a human signal (see src/lib/humanBeacon.js).
router.afterEach(() => {
  notePageView()
})

export default router
