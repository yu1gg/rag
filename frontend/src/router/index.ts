import { createRouter, createWebHistory } from 'vue-router'

import { appTitle } from '../stores/app'

const routes = [
  {
    path: '/',
    name: 'home',
    component: () => import('../views/HomeView.vue'),
    meta: {
      title: appTitle,
    },
  },
  {
    path: '/qa',
    name: 'qa',
    component: () => import('../views/WorkspaceView.vue'),
    meta: {
      title: `${appTitle} | QA`,
      defaultMode: 'qa',
    },
  },
  {
    path: '/summary',
    name: 'summary',
    component: () => import('../views/WorkspaceView.vue'),
    meta: {
      title: `${appTitle} | Summary`,
      defaultMode: 'summary',
    },
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'not-found',
    redirect: '/',
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior() {
    return { top: 0 }
  },
})

router.afterEach((to) => {
  document.title = (to.meta.title as string) || appTitle
})

export default router
